"""Compare alternate local models and restrained rubble reconstruction."""
import json,gc,time
from pathlib import Path
import numpy as np,torch
from scipy.ndimage import gaussian_filter,distance_transform_edt
from PIL import Image,ImageDraw,ImageFont
import local_sr as sr
R=Path(__file__).resolve().parents[1];Q=R/'qa/local_sr012_rework.json';O=R/'workspace/local-sr/sr012-rework'
if Q.exists() or (R/'qa/local_sr012_review.json').exists():raise SystemExit('Do not overwrite completed attempts; create a new revision.')
O.mkdir(exist_ok=True)
old=json.loads((R/'qa/local_sr012_inference.json').read_text('utf8'));parents={r['group_id']:r for r in old['files'] if r['model_id']=='wdn'}
ms={m['name']:m for m in json.loads((R/'workspace/local-sr/models/models.json').read_text('utf8'))['records']}
anime={'name':sr.MODEL.name,'path':str(sr.MODEL),'sha256':sr.MODEL_SHA,'source_url':sr.MODEL_URL,'bytes':sr.MODEL.stat().st_size,'reused_read_only_from':'Fate/EXTRA HD project'}
report={'schema':'brs-sr012-rework/v1','files':[],'local_inference':True,'image_upload':False,'runtime_verified':False,'release_eligible':False}
def save():Q.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
def guide(src,sigma):
    a=np.asarray(src,dtype=np.float32);w=a[:,:,3:4]/255.;cov=gaussian_filter(w,(sigma,sigma,0),mode='nearest') if sigma else w;rgb=gaussian_filter(a[:,:,:3]*w,(sigma,sigma,0),mode='nearest') if sigma else a[:,:,:3]*w;rgb=rgb/np.maximum(cov,1e-6);vis=cov[:,:,0]>1e-6
    if not vis.all():
        near=distance_transform_edt(~vis,return_distances=False,return_indices=True);rgb[~vis]=rgb[near[0][~vis],near[1][~vis]]
    return Image.fromarray(np.rint(np.clip(rgb,0,255)).astype('uint8'))
for mid,model_info,ids,sigma in [('anime-raw',anime,['BM087','BM110'],0.),('general-raw',ms['realesr-general-x4v3.pth'],['BM087','BM110'],0.),('wdn-filtered',ms['realesr-general-wdn-x4v3.pth'],['BM115'],.75)]:
    model=sr.load_model(Path(model_info['path']),model_info['sha256'])
    for gid in ids:
        parent=parents[gid];src=Image.open(parent['source']).convert('RGBA');assert sr.sha(src.tobytes())==parent['source_rgba_sha256'];assert sr.sha(Path(parent['output']).read_bytes())==parent['output_sha256'];prior=Image.open(parent['output']).convert('RGBA');out=Image.new('RGBA',prior.size);parts=[];t=time.monotonic()
        for pi,part in enumerate(parent['parts']):
            box=part['source_box'];tile=src.crop(box);inp=guide(tile,sigma);ip=O/f'{gid}-{mid}-p{pi}-input.png';inp.save(ip);native=sr.infer_rgb(model,inp);npth=O/f'{gid}-{mid}-p{pi}-native4x.png';native.save(npth);wh=(tile.width*8,tile.height*8);rgb=np.asarray(native.resize(wh,Image.Resampling.LANCZOS),dtype=np.float32);alpha=prior.getchannel('A').crop(tuple(v*8 for v in box));a=np.asarray(alpha,dtype=np.float32)[:,:,None]/255.;orig=np.asarray(tile,dtype=np.float32);w=orig[:,:,3:4]/255.;offset=(orig[:,:,:3]*w).sum((0,1))/w.sum()-(rgb*a).sum((0,1))/a.sum();im=Image.fromarray(np.rint(np.clip(rgb+offset,0,255)).astype('uint8')).convert('RGBA');im.putalpha(alpha);out.paste(im,(box[0]*8,box[1]*8));parts.append({'source_box':box,'input':str(ip),'input_sha256':sr.sha(ip.read_bytes()),'native':str(npth),'native_sha256':sr.sha(npth.read_bytes()),'weighted_mean_rgb_offset':offset.tolist()})
        p=O/f'{gid}-{mid}.png';out.save(p);assert out.getchannel('A').tobytes()==prior.getchannel('A').tobytes()
        record={'id':f'{gid}-{mid}','group_id':gid,'source':parent['source'],'source_rgba_sha256':parent['source_rgba_sha256'],'model':model_info,'prefilter_sigma':sigma,'parts':parts,'alpha_parent':parent['output'],'alpha_parent_sha256':parent['output_sha256'],'output':str(p),'output_sha256':sr.sha(p.read_bytes()),'output_size':list(out.size),'new_neural_passes':len(parts),'method':'Local RGB4x inference on isolated source panels; source weighted mean restored, existing alpha retained, Lanczos2x','native_neural_scale':4,'seconds':time.monotonic()-t,'visual_review':'pending','runtime_verified':False,'release_eligible':False}
        report['files'].append(record);save();print('INFERRED',record['id'],len(parts),flush=True)
        if gid=='BM115':
            for tag,base in [('guided',prior),('filtered-guided',out)]:
                v=np.asarray(base,dtype=np.float32);a=v[:,:,3:4]/255.;low=gaussian_filter(v[:,:,:3]*a,(6.,6.,0),mode='nearest')/np.maximum(gaussian_filter(a,(6.,6.,0),mode='nearest'),1e-6);target=np.asarray(guide(src,.25).resize(base.size,Image.Resampling.BILINEAR),dtype=np.float32);weight=.45;rgb=target+weight*(v[:,:,:3]-low);colors=np.asarray(src)[:,:,:3][np.asarray(src)[:,:,3]>0];rgb=np.minimum(np.maximum(rgb,colors.min(0)),colors.max(0));im=Image.fromarray(np.rint(np.clip(rgb,0,255)).astype('uint8')).convert('RGBA');im.putalpha(prior.getchannel('A'));op=O/f'{gid}-{tag}.png';im.save(op);bp=parent['output'] if tag=='guided' else str(p)
                report['files'].append({'id':gid+'-'+tag,'group_id':gid,'source':parent['source'],'source_rgba_sha256':parent['source_rgba_sha256'],'model':model_info,'alpha_parent':parent['output'],'alpha_parent_sha256':parent['output_sha256'],'parent':bp,'parent_sha256':sr.sha(Path(bp).read_bytes()),'output':str(op),'output_sha256':sr.sha(op.read_bytes()),'output_size':list(im.size),'new_neural_passes':0,'detail_weight':weight,'method':'Source color guidance plus weighted neural high-frequency residual; no new model pass','visual_review':'pending','runtime_verified':False,'release_eligible':False});save()
    del model;gc.collect();torch.cuda.empty_cache()
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18);pages=[]
for gid in ['BM087','BM110','BM115']:
    src=Image.open(parents[gid]['source']).convert('RGBA');ims=[(src,'원본 단순 확대'),(Image.open(parents[gid]['output']).convert('RGBA'),'이전 WDN')]+[(Image.open(r['output']).convert('RGBA'),r['id']) for r in report['files'] if r['group_id']==gid]
    box=(0,0,64,64) if gid=='BM087' else (0,0,64,32) if gid=='BM110' else (64,0,128,64);wh=((box[2]-box[0])*8,(box[3]-box[1])*8);s=Image.new('RGB',(1596,2*(wh[1]+58)),'#293440');d=ImageDraw.Draw(s)
    for i,(im,label) in enumerate(ims):
        x=i%3*532+8;y=i//3*(wh[1]+58)+8;d.text((x,y),label,font=font,fill='white');crop=im.crop(box if i==0 else tuple(v*8 for v in box)).resize(wh,Image.Resampling.NEAREST if i==0 else Image.Resampling.LANCZOS);bg=Image.new('RGB',wh,'#72808b');bg.paste(crop,(0,0),crop);s.paste(bg,(x,y+34))
    p=R/f'outputs/sr012_rework_{gid}.png';s.save(p);pages.append(str(p))
report['comparison_sheets']=pages;report['new_neural_passes']=sum(r['new_neural_passes'] for r in report['files']);save();print(json.dumps({'outputs':len(report['files']),'passes':report['new_neural_passes']}),flush=True)
