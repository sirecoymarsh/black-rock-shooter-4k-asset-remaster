"""A different local reconstruction model for held textures; no external image calls."""
import sys,json,time
from pathlib import Path
import numpy as np,torch
from scipy.ndimage import gaussian_filter,distance_transform_edt
from PIL import Image,ImageDraw,ImageFont
import local_sr as sr
sys.stdout.reconfigure(encoding='utf8');torch.set_num_threads(4)
R=Path(__file__).resolve().parents[1];O=R/'workspace/local-sr/swinir-held-v1';O.mkdir(parents=True,exist_ok=True);Q=R/'qa/local_sr_swinir_held_v1.json'
cat=json.loads((R/'qa/battle_sr_catalog.json').read_text('utf8'));groups={g['group_id']:g for g in cat['groups']};old=json.loads((R/'qa/local_sr_observed_v1.json').read_text('utf8'));parents={r['group_id']:r for r in old['files'] if r['model_id']=='wdn'}
for fn in ['local_sr_stage02_materials_v1','local_sr_stage01_materials_v1']:
    for row in json.loads((R/'qa'/f'{fn}.json').read_text('utf8'))['files']:
        if row.get('denoise_strength')==0:parents[row['group_id']]=row
ids=['BM130','BM156','BM159','BM162','BM163','BM164','BM165','BM082','BM056','BM114']
rec=next(r for r in json.loads((R/'workspace/local-sr/models/models.json').read_text('utf8'))['records'] if r['name']=='001_classicalSR_DF2K_s64w8_SwinIR-M_x4.pth');model=sr.load_model(Path(rec['path']),rec['sha256'])
report=json.loads(Q.read_text('utf8')) if Q.exists() else {'schema':'brs-swinir-held/v1','group_ids':ids,'model':rec,'device':torch.cuda.get_device_name(0),'files':[],'local_inference':True,'image_upload':False,'runtime_verified':False,'release_eligible':False};done={(r['group_id'],r['prefilter_sigma']):r for r in report['files']}
def save():Q.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
for sigma in [0.,.35]:
    for gid in ids:
        if (gid,sigma) in done:
            row=done[(gid,sigma)];assert sr.sha(Path(row['output']).read_bytes())==row['output_sha256'];continue
        g=groups[gid];src=Image.open(g['representative']['png']).convert('RGBA');assert sr.sha(src.tobytes())==g['rgba_sha256'];parent=parents[gid];assert sr.sha(Path(parent['output']).read_bytes())==parent['output_sha256'];alpha=Image.open(parent['output']).convert('RGBA').getchannel('A');out=Image.new('RGBA',alpha.size)
        boxes=[(0,y,256,y+32) for y in range(0,128,32)] if gid=='BM130' else [(0,0,src.width,src.height)];parts=[];t=time.monotonic()
        for i,box in enumerate(boxes):
            a=np.asarray(src.crop(box),dtype=np.float32);w=a[:,:,3:4]/255.;cov=gaussian_filter(w,(sigma,sigma,0),mode='nearest') if sigma else w;pre=gaussian_filter(a[:,:,:3]*w,(sigma,sigma,0),mode='nearest') if sigma else a[:,:,:3]*w;rgb=pre/np.maximum(cov,1e-6);vis=cov[:,:,0]>1e-6
            if not vis.all():
                near=distance_transform_edt(~vis,return_distances=False,return_indices=True);rgb[~vis]=rgb[near[0][~vis],near[1][~vis]]
            inp=Image.fromarray(np.rint(np.clip(rgb,0,255)).astype('uint8'));tag=f'{gid}-sigma{sigma}-p{i}';ip=O/f'{tag}-input.png';inp.save(ip);native=sr.infer_rgb(model,inp);npth=O/f'{tag}-native4x.png';native.save(npth)
            im=native.resize((inp.width*8,inp.height*8),Image.Resampling.LANCZOS);im.putalpha(alpha.crop(tuple(v*8 for v in box)));out.paste(im,(box[0]*8,box[1]*8));parts.append({'source_box':box,'input':str(ip),'input_sha256':sr.sha(ip.read_bytes()),'native':str(npth),'native_sha256':sr.sha(npth.read_bytes())})
        assert out.getchannel('A').tobytes()==alpha.tobytes();p=O/f'{gid}-sigma{sigma}-rgba8x.png';out.save(p)
        row={'group_id':gid,'source':g['representative']['png'],'source_rgba_sha256':g['rgba_sha256'],'model':rec,'prefilter_sigma':sigma,'precision':'float32','native_neural_scale':4,'post_scale':'Lanczos2x','parts':parts,'new_neural_passes':len(parts),'alpha_parent':parent['output'],'alpha_parent_sha256':parent['output_sha256'],'alpha_exact_to_parent':True,'output':str(p),'output_sha256':sr.sha(p.read_bytes()),'output_size':list(out.size),'seconds':time.monotonic()-t,'metrics':sr.roundtrip_metrics(src,out),'visual_review':'pending','runtime_verified':False,'release_eligible':False};report['files'].append(row);done[(gid,sigma)]=row;save();print('INFERRED',gid,sigma,flush=True)
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17);pages=[]
for gid in ids:
    src=Image.open(groups[gid]['representative']['png']).convert('RGBA');ims=[src,Image.open(parents[gid]['output']).convert('RGBA')]+[Image.open(done[(gid,s)]['output']).convert('RGBA') for s in [0.,.35]];labels=['원본 단순 확대','이전 Real-ESRGAN','SwinIR · 원본 입력','SwinIR · 약한 사전 필터'];wh=(480,round(480*src.height/src.width));s=Image.new('RGB',(1000,2*(wh[1]+65)),'#293440');d=ImageDraw.Draw(s)
    for i,(im,t) in enumerate(zip(ims,labels)):
        x=i%2*500+10;y=i//2*(wh[1]+65);d.text((x,y+7),gid+' '+t,font=font,fill='white');v=im.resize(wh,Image.Resampling.NEAREST if i==0 else Image.Resampling.LANCZOS);bg=Image.new('RGB',wh,'#72808b');bg.paste(v,(0,0),v);s.paste(bg,(x,y+42))
    p=R/f'outputs/local_sr_swinir_{gid}.png';s.save(p);pages.append(str(p))
report['comparison_sheets']=pages;report['new_neural_passes']=sum(r['new_neural_passes'] for r in report['files']);save();print(json.dumps({'outputs':len(report['files']),'neural_passes':report['new_neural_passes']}),flush=True)
