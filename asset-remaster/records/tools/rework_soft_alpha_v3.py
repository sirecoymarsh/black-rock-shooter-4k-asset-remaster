"""Local neural rework of cloud and foliage, with source-coupled RGBA prefiltering."""
import sys,json,time,gc
from pathlib import Path
import numpy as np,torch
from scipy.ndimage import gaussian_filter,distance_transform_edt
from PIL import Image,ImageDraw,ImageFont
import local_sr as sr
sys.stdout.reconfigure(encoding='utf8')
R=Path(__file__).resolve().parents[1];O=R/'workspace/local-sr/soft-alpha-v3';O.mkdir(parents=True,exist_ok=True)
cat=json.loads((R/'qa/battle_sr_catalog.json').read_text('utf8'));groups={g['group_id']:g for g in cat['groups']}
prev=json.loads((R/'qa/local_sr_stage01_alpha_v1.json').read_text('utf8'))
old={r['group_id']:r for r in prev['files'] if r['alpha_model_id']=='general-wdn'}
models=json.loads((R/'workspace/local-sr/models/models.json').read_text('utf8'))['records']
rows=[]

def prefilter(src,radius):
    a=np.asarray(src,dtype=np.float32)/255.;cov=a[:,:,3]
    blur=gaussian_filter(cov,radius,mode='nearest')
    rgb=gaussian_filter(a[:,:,:3]*cov[:,:,None],(radius,radius,0),mode='nearest')/np.maximum(blur[:,:,None],1e-6)
    vis=blur>1e-6
    if not vis.all():
        near=distance_transform_edt(~vis,return_distances=False,return_indices=True)
        rgb[~vis]=rgb[near[0][~vis],near[1][~vis]]
    return Image.fromarray(np.rint(np.clip(rgb,0,1)*255).astype('uint8')),Image.fromarray(np.rint(blur*255).astype('uint8'))

for mid,name in [('wdn','realesr-general-wdn-x4v3.pth'),('photo','RealESRGAN_x4plus.pth')]:
    rec=next(m for m in models if m['name']==name);model=sr.load_model(Path(rec['path']),rec['sha256'])
    for gid in ['BM027','BM057']:
        g=groups[gid];src=Image.open(g['representative']['png']).convert('RGBA');assert sr.sha(src.tobytes())==g['rgba_sha256']
        # Tree is an atlas: foliage and bark are inferred separately across the source x=48 seam.
        parts=[(0,0,48,64),(48,0,64,64)] if gid=='BM057' else [(0,0,src.width,src.height)]
        for rad in ([.6,1.] if gid=='BM027' else [.4,.7]):
            tag=f'{gid}-{mid}-sigma{rad}';start=time.monotonic();size=(src.width*8,src.height*8)
            out=Image.new('RGBA',size);native_records=[]
            for pi,box in enumerate(parts):
                part=src.crop(box);radius=rad if pi==0 else .15
                rgb,alpha=prefilter(part,radius)
                rgbp=O/f'{tag}-part{pi}-input-rgb.png';ap=O/f'{tag}-part{pi}-input-alpha.png';rgb.save(rgbp);alpha.save(ap)
                native=sr.infer_rgb(model,rgb);na=sr.infer_rgb(model,alpha.convert('RGB')).convert('L')
                npth=O/f'{tag}-part{pi}-rgb4x.png';naph=O/f'{tag}-part{pi}-alpha4x.png';native.save(npth);na.save(naph)
                ps=(part.width*8,part.height*8);im=native.resize(ps,Image.Resampling.LANCZOS)
                predicted=np.asarray(na.resize(ps,Image.Resampling.LANCZOS),dtype=np.float32)
                smoothed=np.asarray(alpha.resize(ps,Image.Resampling.BILINEAR),dtype=np.float32)
                av=.5*predicted+.5*smoothed
                for _ in range(5):av=np.clip(av*(np.asarray(part.getchannel('A')).mean()/max(av.mean(),1e-6)),0,255)
                lin=np.asarray(part.getchannel('A').resize(ps,Image.Resampling.BILINEAR))
                av[lin==0]=0;av[lin==255]=255
                # Preserve average alpha-weighted color, not every newly inferred highlight.
                rgbv=np.asarray(im,dtype=np.float32);orig=np.asarray(part,dtype=np.float32);oa=orig[:,:,3:4]/255.;wa=av[:,:,None]/255.
                shift=(orig[:,:,:3]*oa).sum((0,1))/oa.sum()-(rgbv*wa).sum((0,1))/wa.sum()
                rgbv=np.clip(rgbv+shift,0,255);im=Image.fromarray(np.rint(rgbv).astype('uint8'));im.putalpha(Image.fromarray(np.rint(av).astype('uint8')))
                out.paste(im,(box[0]*8,box[1]*8))
                native_records.append({'source_box':box,'prefilter_sigma':radius,'input_rgb':str(rgbp),'input_rgb_sha256':sr.sha(rgbp.read_bytes()),'input_alpha':str(ap),'input_alpha_sha256':sr.sha(ap.read_bytes()),'rgb_native':str(npth),'rgb_native_sha256':sr.sha(npth.read_bytes()),'alpha_native':str(naph),'alpha_native_sha256':sr.sha(naph.read_bytes()),'weighted_rgb_mean_correction':shift.tolist()})
            p=O/f'{tag}-rgba8x.png';out.save(p)
            orig=np.asarray(src);actual=np.asarray(out);lin=np.asarray(src.getchannel('A').resize(size,Image.Resampling.BILINEAR))
            assert not np.any(actual[:,:,3][lin==0])
            row={'group_id':gid,'source':g['representative']['png'],'source_rgba_sha256':g['rgba_sha256'],'model':rec,'model_id':mid,'prefilter_sigma':rad,'parts':native_records,'output':str(p),'output_sha256':sr.sha(p.read_bytes()),'output_size':list(out.size),'native_neural_scale':4,'post_scale':'Lanczos 2x','alpha_method':'50% actual neural coverage, 50% bilinear prefiltered coverage; source mean opacity restoration; source empty and solid support constraints.','prefilter_method':'Gaussian premultiplied RGBA filtering before RGB/alpha local inference; atlas parts isolated.','alpha_mass_ratio':float(actual[:,:,3].mean()/orig[:,:,3].mean()),'roundtrip':sr.roundtrip_metrics(src,out),'device':torch.cuda.get_device_name(0),'torch':torch.__version__,'precision':'float32','local_inference':True,'image_upload':False,'new_inference_passes':2*len(parts),'seconds':time.monotonic()-start,'visual_review':'pending','runtime_verified':False,'release_eligible':False}
            rows.append(row);print(json.dumps({'id':tag,'seconds':row['seconds'],'alpha_mass':row['alpha_mass_ratio']}),flush=True)
    del model;gc.collect();torch.cuda.empty_cache()
font=ImageFont.truetype(r'C:\Windows\Fonts\malgun.ttf',18)
for gid in ['BM027','BM057']:
    src=Image.open(groups[gid]['representative']['png']).convert('RGBA');trials=[r for r in rows if r['group_id']==gid]
    ims=[src,Image.open(old[gid]['output']).convert('RGBA')]+[Image.open(r['output']).convert('RGBA') for r in trials]
    labels=['원본 단순 확대','이전 · 미채택']+[f"{r['model_id']} · 사전 필터 {r['prefilter_sigma']}" for r in trials]
    w=512;h=256 if gid=='BM027' else 512;sheet=Image.new('RGB',(3*(w+16),2*(h+75)),'#293440');d=ImageDraw.Draw(sheet)
    for n,(im,label) in enumerate(zip(ims,labels)):
        x=n%3*(w+16)+8;y=n//3*(h+75);d.text((x,y+8),gid+' '+label,font=font,fill='white')
        v=im.resize((w,h),Image.Resampling.NEAREST if n==0 else Image.Resampling.LANCZOS)
        bg=Image.new('RGB',(w,h),'#a7b4bc');bg.paste(v,(0,0),v);sheet.paste(bg,(x,y+42))
    sheet.save(R/f'outputs/local_sr_{gid}_soft_v3.png')
(R/'qa/local_sr_soft_alpha_v3.json').write_text(json.dumps({'schema':'brs-soft-alpha-rework/v3','files':rows,'unique_originals':2,'new_originals':0,'new_neural_inference_passes':sum(r['new_inference_passes'] for r in rows),'runtime_verified':False,'release_eligible':False},ensure_ascii=False,indent=2),'utf8')
