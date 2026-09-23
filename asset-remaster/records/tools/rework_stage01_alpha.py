"""Review-driven local rework: protect faint cracks and compare soft-material RGB models."""
import sys,json,gc
from pathlib import Path
import numpy as np,torch
from scipy.ndimage import distance_transform_edt
from PIL import Image,ImageDraw,ImageFont
import local_sr as sr
sys.stdout.reconfigure(encoding='utf8')
R=Path(__file__).resolve().parents[1];O=R/'workspace/local-sr/stage01-alpha-rework-v2';O.mkdir(parents=True,exist_ok=True)
trial=json.loads((R/'qa/local_sr_stage01_alpha_v1.json').read_text('utf8'))
base={r['group_id']:r for r in trial['files'] if r['alpha_model_id']=='general-wdn'}
rows=[];font=ImageFont.truetype(r'C:\Windows\Fonts\malgun.ttf',20)
def metrics(src,im):
    a=np.asarray(src.getchannel('A'));b=np.asarray(im.getchannel('A').resize(src.size,Image.Resampling.LANCZOS))
    return {'alpha_mass_ratio':float(np.asarray(im.getchannel('A')).mean()/a.mean()),
            'source_pixels_ge16_reduced_below8':int(((a>=16)&(b<8)).sum()),
            'alpha_source_mae':float(np.abs(a.astype(float)-b).mean())}
for gid in ['BM007','BM055','BM058']:
    b=base[gid];src=Image.open(b['source']).convert('RGBA');raw=Image.open(b['output']).convert('RGBA')
    a=np.asarray(raw.getchannel('A'),dtype=np.float32);lin=np.asarray(src.getchannel('A').resize(raw.size,Image.Resampling.BILINEAR),dtype=np.float32)
    for mix in [.35,.5,.65]:
        v=mix*a+(1-mix)*lin
        # Retain global source opacity without making the background nontransparent.
        for _ in range(3):v=np.clip(v*(np.asarray(src.getchannel('A')).mean()/v.mean()),0,255)
        v[lin==0]=0;im=raw.copy();im.putalpha(Image.fromarray(np.rint(v).astype(np.uint8)))
        p=O/f'{gid}-neural{mix}-coverage-8x.png';im.save(p)
        row={'group_id':gid,'source':b['source'],'source_rgba_sha256':b['source_rgba_sha256'],
             'parent_neural_output':b['output'],'parent_sha256':b['output_sha256'],
             'method':'Mix neural alpha with positive bilinear source coverage, then restore source mean opacity; same constant visible RGB.',
             'neural_weight':mix,'postprocessing_only':True,'new_neural_inference':False,
             'output':str(p),'output_sha256':sr.sha(p.read_bytes()),'metrics':metrics(src,im),
             'visual_review':'pending','runtime_verified':False,'release_eligible':False}
        rows.append(row);print(json.dumps({'id':gid,'mix':mix,'metrics':row['metrics']}),flush=True)

models=json.loads((R/'workspace/local-sr/models/models.json').read_text('utf8'))['records']
photo=next(m for m in models if m['name']=='RealESRGAN_x4plus.pth')
for mid,path,digest in [('anime6B',sr.MODEL,sr.MODEL_SHA),('photo',Path(photo['path']),photo['sha256'])]:
    model=sr.load_model(path,digest)
    for gid in ['BM027','BM057']:
        b=base[gid];src=Image.open(b['source']).convert('RGBA');a=np.asarray(src);vis=a[:,:,3]>0;rgb=a[:,:,:3].copy()
        if not vis.all():
            near=distance_transform_edt(~vis,return_distances=False,return_indices=True)
            rgb[~vis]=rgb[near[0][~vis],near[1][~vis]]
        native=sr.infer_rgb(model,Image.fromarray(rgb));npth=O/f'{gid}-{mid}-rgb4x.png';native.save(npth)
        out=native.resize((src.width*8,src.height*8),Image.Resampling.LANCZOS)
        # Hold alpha fixed across RGB comparisons so RGB quality can be judged in isolation.
        out.putalpha(Image.open(b['output']).getchannel('A'))
        p=O/f'{gid}-{mid}-rgba8x.png';out.save(p)
        row={'group_id':gid,'source':b['source'],'source_rgba_sha256':b['source_rgba_sha256'],'model':mid,
             'model_path':str(path),'model_sha256':digest,'device':torch.cuda.get_device_name(0),
             'native':str(npth),'native_sha256':sr.sha(npth.read_bytes()),'native_neural_scale':4,'post_scale':'Lanczos 2x',
             'alpha_parent':b['output'],'alpha_parent_sha256':b['output_sha256'],'alpha_unchanged_from_general_trial':True,
             'output':str(p),'output_sha256':sr.sha(p.read_bytes()),'metrics':sr.roundtrip_metrics(src,out),
             'local_inference':True,'new_neural_inference':True,'image_upload':False,
             'visual_review':'pending','runtime_verified':False,'release_eligible':False}
        rows.append(row);print('RGB_REWORK',gid,mid,flush=True)
    del model;gc.collect();torch.cuda.empty_cache()

def composite(im,size,bgcolor):
    v=im.resize(size,Image.Resampling.LANCZOS);bg=Image.new('RGB',size,bgcolor);bg.paste(v,(0,0),v);return bg
for kind,ids in [('cracks',['BM007','BM055','BM058']),('soft',['BM027','BM057'])]:
    sheet=Image.new('RGB',(1600,len(ids)*620+44),'#293440');d=ImageDraw.Draw(sheet)
    labels=['원본 단순 확대','이전 일반 모델','재작업 · 원본 선 보존','재작업 · 모델 비중 높임'] if kind=='cracks' else ['원본 단순 확대','이전 일반 모델','애니 모델로 재작업','사진 모델로 재작업']
    for n,label in enumerate(labels):d.text((n*400+8,6),label,font=font,fill='white')
    for i,gid in enumerate(ids):
        src=Image.open(base[gid]['source']).convert('RGBA')
        paths=[base[gid]['output']]
        paths+= [str(O/f'{gid}-neural{mix}-coverage-8x.png') for mix in [.35,.65]] if kind=='cracks' else [str(O/f'{gid}-{m}-rgba8x.png') for m in ['anime6B','photo']]
        ims=[src]+[Image.open(p).convert('RGBA') for p in paths]
        for n,im in enumerate(ims):
            x=n*400+8;y=44+i*620;d.text((x,y),gid,font=font,fill='white')
            s=min(384/src.width,552/src.height,8);size=(round(src.width*s),round(src.height*s))
            if n==0:im=src.resize(size,Image.Resampling.NEAREST)
            sheet.paste(composite(im,size,'#a7b4bc' if kind=='soft' else '#d8d2c4'),(x,y+34))
    sheet.save(R/f'outputs/local_sr_alpha_rework_{kind}.png')
(R/'qa/local_sr_stage01_alpha_rework_v2.json').write_text(json.dumps({'schema':'brs-alpha-rework/v2','files':rows,
    'reason':'Sparse cracks lost faint branches; cloud RGB became faceted and tree foliage overly glossy.',
    'runtime_verified':False,'release_eligible':False},ensure_ascii=False,indent=2),'utf8')
