"""Local retries for overly interpreted grain, cracks and fabric-like surface detail."""
import sys,json,time,gc
from pathlib import Path
import numpy as np,torch
from scipy.ndimage import gaussian_filter
from PIL import Image,ImageDraw,ImageFont
import local_sr as sr
sys.stdout.reconfigure(encoding='utf8');torch.set_num_threads(4)
R=Path(__file__).resolve().parents[1];Q=R/'qa/local_sr010_anime_retry.json'
if Q.exists() or (R/'qa/local_sr010_review.json').exists():raise SystemExit('Existing evidence; inspect before repeating.')
O=R/'workspace/local-sr/sr010-anime-retry';O.mkdir(parents=True,exist_ok=True)
old=json.loads((R/'qa/local_sr010_inference.json').read_text('utf8'))
parents={r['group_id']:r for r in old['files'] if r['denoise_strength']==0.}
ids=['BM254','BM256']
models={m['name']:m for m in json.loads((R/'workspace/local-sr/models/models.json').read_text('utf8'))['records']}
models['RealESRGAN_x4plus_anime_6B.pth']={'name':sr.MODEL.name,'path':str(sr.MODEL),'sha256':sr.MODEL_SHA,'source_url':sr.MODEL_URL}
report={'schema':'brs-sr010-rework/v1','group_ids':ids,'files':[],'local_inference':True,'image_upload':False,'runtime_verified':False,'release_eligible':False}
for tag,name,sigma in [('anime0','RealESRGAN_x4plus_anime_6B.pth',0.),('anime04','RealESRGAN_x4plus_anime_6B.pth',.4)]:
    m=models[name];model=sr.load_model(Path(m['path']),m['sha256'])
    for gid in ids:
        parent=parents[gid];src=Image.open(parent['source']).convert('RGBA')
        assert sr.sha(src.tobytes())==parent['source_rgba_sha256']
        out=Image.new('RGBA',(src.width*8,src.height*8));parts=[];t=time.monotonic()
        for pi,oldpart in enumerate(parent['parts']):
            box=oldpart['source_box'];part=src.crop(box).convert('RGB');v=np.asarray(part,dtype=np.float32)
            inp=Image.fromarray(np.rint(np.clip(gaussian_filter(v,(sigma,sigma,0),mode='nearest'),0,255)).astype('uint8'))
            ip=O/f'{gid}-{tag}-p{pi}-input.png';inp.save(ip)
            native=sr.infer_rgb(model,inp);npth=O/f'{gid}-{tag}-p{pi}-native4x.png';native.save(npth)
            nv=np.asarray(native,dtype=np.float32);offset=v.mean((0,1))-nv.mean((0,1))
            enlarged=Image.fromarray(np.rint(np.clip(nv+offset,0,255)).astype('uint8')).resize((part.width*8,part.height*8),Image.Resampling.LANCZOS).convert('RGBA');enlarged.putalpha(255)
            out.paste(enlarged,(box[0]*8,box[1]*8))
            parts.append({'source_box':box,'input':str(ip),'input_sha256':sr.sha(ip.read_bytes()),'native':str(npth),'native_sha256':sr.sha(npth.read_bytes()),'mean_color_offset_rgb':offset.tolist()})
        p=O/f'{gid}-{tag}.png';out.save(p)
        report['files'].append({'id':gid+'-'+tag,'group_id':gid,'source':parent['source'],'source_rgba_sha256':parent['source_rgba_sha256'],'model':m,'prefilter_sigma':sigma,'parts':parts,'new_neural_passes':len(parts),'native_neural_scale':4,'post_scale':'Lanczos2x','method':'Local filtered-source RGB inference, original per-panel RGB mean restored','output':str(p),'output_sha256':sr.sha(p.read_bytes()),'output_size':list(out.size),'seconds':time.monotonic()-t,'alpha':'Opaque255 exact','visual_review':'pending','runtime_verified':False,'release_eligible':False})
        Q.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8');print('REWORKED',gid,tag,flush=True)
    del model;gc.collect();torch.cuda.empty_cache()
f=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18);pages=[]
for gid in ids:
    parent=parents[gid];src=Image.open(parent['source']).convert('RGBA')
    ims=[(src,'원본 단순 확대'),(Image.open(parent['output']),'초기 WDN')]+[(Image.open(r['output']),r['id']) for r in report['files'] if r['group_id']==gid]
    s=Image.new('RGB',(1560,1120),'#293440');d=ImageDraw.Draw(s);scale=min(500/src.width,485/src.height,8);wh=(round(src.width*scale),round(src.height*scale))
    for i,(im,label) in enumerate(ims):
        x=i%3*520+10;y=i//3*560+10;d.text((x,y),label,font=f,fill='white');s.paste(im.convert('RGB').resize(wh,Image.Resampling.NEAREST if i==0 else Image.Resampling.LANCZOS),(x,y+34))
    p=R/f'outputs/sr010-anime-{gid}.png';s.save(p);pages.append(str(p))
report['comparison_sheets']=pages;report['new_neural_passes']=sum(r['new_neural_passes'] for r in report['files']);Q.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
print(json.dumps({'outputs':len(report['files']),'passes':report['new_neural_passes']}),flush=True)

