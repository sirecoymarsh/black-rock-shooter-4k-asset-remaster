"""Actual local RGB/coverage SR trials, preserving source-empty and solid regions."""
import sys,json,gc,time
from pathlib import Path
import numpy as np,torch
from scipy.ndimage import distance_transform_edt
from PIL import Image,ImageDraw,ImageFont
import local_sr as sr
sys.stdout.reconfigure(encoding='utf8')
R=Path(__file__).resolve().parents[1];O=R/'workspace/local-sr/stage01-alpha-v1';O.mkdir(parents=True,exist_ok=True)
cat=json.loads((R/'qa/battle_sr_catalog.json').read_text('utf8'))
ids=['BM001','BM007','BM026','BM027','BM039','BM045','BM055','BM057','BM058']
groups={g['group_id']:g for g in cat['groups'] if g['group_id'] in ids}
models=json.loads((R/'workspace/local-sr/models/models.json').read_text('utf8'))['records']
general=next(m for m in models if m['name']=='realesr-general-wdn-x4v3.pth')
general_model=sr.load_model(Path(general['path']),general['sha256'])
base={};records=[]
for gid in ids:
    g=groups[gid];src=Image.open(g['representative']['png']).convert('RGBA');a=np.asarray(src);visible=a[:,:,3]>0
    assert sr.sha(src.tobytes())==g['rgba_sha256']
    unique=np.unique(a[:,:,:3][visible],axis=0)
    if len(unique)==1:
        rgb4=Image.new('RGB',(src.width*4,src.height*4),tuple(map(int,unique[0])))
        method='Single visible RGB retained; detail is in alpha, so no pointless RGB model inference.'
    else:
        rgb=a[:,:,:3].copy()
        if not visible.all():
            near=distance_transform_edt(~visible,return_distances=False,return_indices=True)
            rgb[~visible]=rgb[near[0][~visible],near[1][~visible]]
        rgb4=sr.infer_rgb(general_model,Image.fromarray(rgb));method='Local general-WDN RGB4x with nearest-visible color bleed into source-transparent pixels.'
    rgbp=O/f'{gid}-rgb4x.png';rgb4.save(rgbp)
    base[gid]={'src':src,'rgb4':rgb4,'rgb_path':str(rgbp),'rgb_sha256':sr.sha(rgbp.read_bytes()),'rgb_method':method}
for mid,model,desc in [('general-wdn',general_model,general),('anime6B',None,{'name':sr.MODEL.name,'path':str(sr.MODEL),'sha256':sr.MODEL_SHA,'source_url':sr.MODEL_URL})]:
    if model is None:model=sr.load_model(Path(desc['path']),desc['sha256'])
    for gid in ids:
        start=time.monotonic();g=groups[gid];b=base[gid];src=b['src'];alpha=src.getchannel('A')
        raw4=sr.infer_rgb(model,alpha.convert('RGB'));rawp=O/f'{gid}-{mid}-alpha4x.png';raw4.save(rawp)
        alpha8=raw4.resize((src.width*8,src.height*8),Image.Resampling.LANCZOS).convert('L')
        lin=np.asarray(alpha.resize(alpha8.size,Image.Resampling.BILINEAR));av=np.asarray(alpha8).copy()
        # These are mathematical source-mask invariants, not visual approval.
        av[lin==0]=0;av[lin==255]=255
        out=b['rgb4'].resize(alpha8.size,Image.Resampling.LANCZOS);out.putalpha(Image.fromarray(av))
        p=O/f'{gid}-{mid}-rgba8x.png';out.save(p)
        reduced=np.asarray(out.getchannel('A').resize(src.size,Image.Resampling.LANCZOS));orig=np.asarray(alpha)
        gt=orig>=128;pred=reduced>=128;union=(gt|pred).sum()
        disappearing=int(((orig>=16)&(reduced<8)).sum())
        row={'group_id':gid,'source_id':g['representative']['id'],'source':g['representative']['png'],
             'source_rgba_sha256':g['rgba_sha256'],'pixel_equivalent_members':g['members'],
             'alpha_model':desc,'rgb_model':general,'rgb_method':b['rgb_method'],'rgb_native':b['rgb_path'],'rgb_native_sha256':b['rgb_sha256'],
             'alpha_model_id':mid,'alpha_native':str(rawp),'alpha_native_sha256':sr.sha(rawp.read_bytes()),
             'precision':'float32','device':torch.cuda.get_device_name(0),'native_neural_scale':4,'post_scale':'Lanczos 2x',
             'alpha_constraints':'Bilinear-source alpha0 remains0 and alpha255 remains255; intermediate coverage uses neural prediction.',
             'output':str(p),'output_sha256':sr.sha(p.read_bytes()),'output_size':list(out.size),
             'alpha_metrics':{'mean_source':float(orig.mean()),'mean_output':float(av.mean()),
                              'mass_ratio':float(av.mean()/orig.mean()),'source_scale_mae':float(np.abs(reduced.astype(float)-orig).mean()),
                              'threshold128_iou':float((gt&pred).sum()/union) if union else 1.,
                              'source_pixels_ge16_reduced_below8':disappearing,
                              'forbidden_alpha_outside_bilinear_support':int((av[lin==0]!=0).sum())},
             'seconds':time.monotonic()-start,'local_inference':True,'image_upload':False,
             'visual_review':'pending','runtime_verified':False,'release_eligible':False}
        records.append(row);print(json.dumps({'id':gid,'model':mid,'alpha_metrics':row['alpha_metrics']}),flush=True)
    if mid=='anime6B':del model
del general_model;gc.collect();torch.cuda.empty_cache()
font=ImageFont.truetype(r'C:\Windows\Fonts\malgun.ttf',19)
pages=[]
for start in range(0,len(ids),3):
    selected=ids[start:start+3];sheet=Image.new('RGB',(1536,len(selected)*430+45),'#293440');d=ImageDraw.Draw(sheet)
    for col,label in enumerate(['원본 단순 확대','알파 복원 · 일반 모델','알파 복원 · 애니 모델']):d.text((col*512+12,6),label,font=font,fill='white')
    for n,gid in enumerate(selected):
        src=base[gid]['src'];ims=[src]+[Image.open(O/f'{gid}-{mid}-rgba8x.png').convert('RGBA') for mid in ['general-wdn','anime6B']]
        scale=min(488/src.width,350/src.height,8);size=(round(src.width*scale),round(src.height*scale))
        for col,im in enumerate(ims):
            x=col*512+12;y=45+n*430;d.text((x,y+2),gid,font=font,fill='white')
            v=im.resize(size,Image.Resampling.NEAREST if col==0 else Image.Resampling.LANCZOS)
            bg=Image.new('RGB',size,'#c5c5bd')
            for ix in range(0,size[0],24):
                for iy in range(0,size[1],24):
                    if (ix//24+iy//24)%2==0:ImageDraw.Draw(bg).rectangle((ix,iy,ix+23,iy+23),fill='#65716d')
            bg.paste(v,(0,0),v);sheet.paste(bg,(x,y+35))
    p=R/f'outputs/local_sr_alpha_trial_{start//3+1:02d}.png';sheet.save(p);pages.append(str(p))
report={'schema':'brs-alpha-trial/v1','files':records,'comparison_sheets':pages,'original_groups':len(ids),
        'scope':'First-region alpha assets, local SR trials. Original channel semantics preserved; no runtime acceptance.',
        'runtime_verified':False,'release_eligible':False}
(R/'qa/local_sr_stage01_alpha_v1.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
