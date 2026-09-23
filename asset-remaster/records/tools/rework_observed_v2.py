"""Reduce invented material structure while retaining real local neural detail."""
import sys,json,time
from pathlib import Path
import numpy as np,torch
from scipy.ndimage import gaussian_filter,distance_transform_edt
from PIL import Image,ImageDraw,ImageFont
import local_sr as sr
sys.stdout.reconfigure(encoding='utf8');torch.set_num_threads(4)
R=Path(__file__).resolve().parents[1];O=R/'workspace/local-sr/observed-rework-v2';O.mkdir(parents=True,exist_ok=True);Q=R/'qa/local_sr_observed_rework_v2.json'
cat=json.loads((R/'qa/battle_sr_catalog.json').read_text('utf8'));groups={g['group_id']:g for g in cat['groups']}
old=json.loads((R/'qa/local_sr_observed_v1.json').read_text('utf8'));parents={r['group_id']:r for r in old['files'] if r['model_id']=='wdn'}
ids=['BM130','BM156','BM159','BM162','BM163','BM164','BM165'];rec=next(r for r in json.loads((R/'workspace/local-sr/models/models.json').read_text('utf8'))['records'] if r['name']=='realesr-general-wdn-x4v3.pth')
report=json.loads(Q.read_text('utf8')) if Q.exists() else {'schema':'brs-observed-rework/v2','group_ids':ids,'device':torch.cuda.get_device_name(0),'files':[],'runtime_verified':False,'release_eligible':False,'image_upload':False}
done={r['id']:r for r in report['files']}
def save():Q.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
def guide(src,sigma):
    a=np.asarray(src,dtype=np.float32);w=a[:,:,3:4]/255.;cov=gaussian_filter(w,(sigma,sigma,0),mode='nearest');rgb=gaussian_filter(a[:,:,:3]*w,(sigma,sigma,0),mode='nearest')/np.maximum(cov,1e-6);vis=cov[:,:,0]>1e-6
    if not vis.all():
        near=distance_transform_edt(~vis,return_distances=False,return_indices=True);rgb[~vis]=rgb[near[0][~vis],near[1][~vis]]
    return Image.fromarray(np.rint(np.clip(rgb,0,255)).astype('uint8'))
def add(key,gid,im,details):
    p=O/f'{key}.png';im.save(p);r={'id':key,'group_id':gid,'source':groups[gid]['representative']['png'],'source_rgba_sha256':groups[gid]['rgba_sha256'],'output':str(p),'output_sha256':sr.sha(p.read_bytes()),'output_size':list(im.size),'visual_review':'pending','runtime_verified':False,'release_eligible':False,**details};report['files'].append(r);done[key]=r;save();print('CREATED',key,flush=True);return r
model=sr.load_model(Path(rec['path']),rec['sha256'])
for gid in ids:
    src=Image.open(groups[gid]['representative']['png']).convert('RGBA');assert sr.sha(src.tobytes())==groups[gid]['rgba_sha256'];parent=parents[gid];assert sr.sha(Path(parent['output']).read_bytes())==parent['output_sha256'];previous=Image.open(parent['output']).convert('RGBA')
    boxes=[(0,y,256,y+32) for y in range(0,128,32)] if gid=='BM130' else [(0,0,src.width,src.height)]
    freshkey=gid+'-prefilter075';fresh=done.get(freshkey)
    if fresh:assert sr.sha(Path(fresh['output']).read_bytes())==fresh['output_sha256']
    else:
        out=Image.new('RGBA',previous.size);records=[];t=time.monotonic()
        for i,box in enumerate(boxes):
            part=src.crop(box);inp=guide(part,.75);ip=O/f'{freshkey}-part{i}-input.png';inp.save(ip);native=sr.infer_rgb(model,inp);npth=O/f'{freshkey}-part{i}-native4x.png';native.save(npth)
            n=np.asarray(native,dtype=float);offset=np.asarray(inp,dtype=float).mean((0,1))-n.mean((0,1));im=Image.fromarray(np.rint(np.clip(n+offset,0,255)).astype('uint8')).resize((part.width*8,part.height*8),Image.Resampling.LANCZOS);im.putalpha(previous.getchannel('A').crop(tuple(v*8 for v in box)));out.paste(im,(box[0]*8,box[1]*8))
            records.append({'source_box':box,'input':str(ip),'input_sha256':sr.sha(ip.read_bytes()),'native':str(npth),'native_sha256':sr.sha(npth.read_bytes()),'mean_rgb_offset':offset.tolist()})
        fresh=add(freshkey,gid,out,{'method':'Premultiplied source RGB prefilter sigma0.75 then actual WDN4x, Lanczos2x, earlier alpha exact.','model':rec,'native_neural_scale':4,'parts':records,'new_neural_passes':len(boxes),'seconds':time.monotonic()-t,'alpha_parent':parent['output'],'alpha_parent_sha256':parent['output_sha256']})
    for tag,base_row,weight in [('guided055',parent,.55),('guided080',parent,.8),('prefilter075-guided065',fresh,.65)]:
        key=gid+'-'+tag
        if key in done:assert sr.sha(Path(done[key]['output']).read_bytes())==done[key]['output_sha256'];continue
        base=Image.open(base_row['output']).convert('RGBA');v=np.asarray(base,dtype=np.float32);out=v.copy()
        for box in boxes:
            x0,y0,x1,y1=[i*8 for i in box];part=v[y0:y1,x0:x1];a=part[:,:,3:4]/255.;low=gaussian_filter(part[:,:,:3]*a,(6.,6.,0),mode='nearest')/np.maximum(gaussian_filter(a,(6.,6.,0),mode='nearest'),1e-6)
            target=np.asarray(guide(src.crop(box),.5).resize((x1-x0,y1-y0),Image.Resampling.BILINEAR),dtype=np.float32)
            corrected=target+weight*(part[:,:,:3]-low)
            visible=np.asarray(src.crop(box));colors=visible[:,:,:3][visible[:,:,3]>0];corrected=np.minimum(np.maximum(corrected,colors.min(0)),colors.max(0))
            out[y0:y1,x0:x1,:3]=corrected
        im=Image.fromarray(np.rint(np.clip(out,0,255)).astype('uint8'));assert im.getchannel('A').tobytes()==previous.getchannel('A').tobytes()
        add(key,gid,im,{'method':'Source premultiplied sigma0.5 RGB guide at8x plus weighted alpha-normalized neural high-frequency residual (sigma6 output pixels); clamp each channel to source visible range. Original source split boxes isolated. All alpha byte-identical to previous WDN candidate.','parent':base_row['output'],'parent_sha256':base_row['output_sha256'],'alpha_parent':parent['output'],'alpha_parent_sha256':parent['output_sha256'],'detail_weight':weight,'source_boxes':boxes,'new_neural_passes':0})
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17);pages=[]
for gid in ids:
    src=Image.open(groups[gid]['representative']['png']).convert('RGBA');ims=[src,Image.open(parents[gid]['output'])]+[Image.open(done[gid+'-'+tag]['output']) for tag in ['guided055','guided080','prefilter075','prefilter075-guided065']];labels=['원본 단순 확대','이전 WDN','원본 색 + 질감55%','원본 색 + 질감80%','사전 필터 후 재추론','재추론 + 원본 색·질감65%']
    wh=(480,round(480*src.height/src.width));height=wh[1]+63;s=Image.new('RGB',(1500,height*2),'#293440');d=ImageDraw.Draw(s)
    for i,(im,label) in enumerate(zip(ims,labels)):
        x=i%3*500+10;y=i//3*height;d.text((x,y+8),gid+' '+label,font=font,fill='white');im=im.convert('RGBA').resize(wh,Image.Resampling.NEAREST if i==0 else Image.Resampling.LANCZOS);bg=Image.new('RGB',wh,'#72808b');bg.paste(im,(0,0),im);s.paste(bg,(x,y+42))
    p=R/f'outputs/local_sr_observed_rework_{gid}.png';s.save(p);pages.append(str(p))
report['comparison_sheets']=pages;report['new_neural_passes']=sum(r['new_neural_passes'] for r in report['files']);save();print(json.dumps({'outputs':len(report['files']),'new_neural_passes':report['new_neural_passes']}),flush=True)
