import sys,json,hashlib,time
from pathlib import Path
sys.dont_write_bytecode=True
import torch,numpy as np
from PIL import Image,ImageFilter,ImageDraw,ImageFont
from local_sr import load_model,infer_rgb,MODEL,MODEL_SHA,roundtrip_metrics
R=Path(__file__).resolve().parents[1];Q=R/'qa/field_sr002_rework.json';assert not Q.exists();r=json.loads((R/'qa/field_sr002_inference.json').read_text('utf8'));rows={v['id']:v for v in r['files']};O=R/'workspace/local-sr/field-sr002';models=json.loads((R/'workspace/local-sr/models/models.json').read_text('utf8'))['records'];wdn=next(m for m in models if m['name']=='realesr-general-wdn-x4v3.pth');configs=[('wdn065',wdn,.65),('anime035',{'name':MODEL.name,'path':str(MODEL),'sha256':MODEL_SHA},.35)];files=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
for tag,modelrec,sigma in configs:
 model=load_model(Path(modelrec['path']),modelrec['sha256'])
 for gid in ['FM0160','FM0188']:
  v=rows[gid+'-wdn'];s=Image.open(v['source']).convert('RGBA');inp=s.convert('RGB').filter(ImageFilter.GaussianBlur(sigma));ip=O/f'{gid}-{tag}-input.png';inp.save(ip);native=infer_rgb(model,inp);npth=O/f'{gid}-{tag}-native4x.png';native.save(npth);out=native.resize((s.width*8,s.height*8),Image.Resampling.LANCZOS).convert('RGBA');op=O/f'{gid}-{tag}-8x.png';out.save(op);files.append({**{k:v[k] for k in ['group_id','source','source_ptm','source_ptm_sha256','source_rgba_sha256']},'id':gid+'-'+tag,'model':modelrec,'input':str(ip),'input_sha256':sha(ip),'input_gaussian_sigma_source_px':sigma,'native':str(npth),'native_sha256':sha(npth),'output':str(op),'output_sha256':sha(op),'output_size':list(out.size),'actual_local_rgb_inference_passes':1,'source_scale_metrics':roundtrip_metrics(s,out),'visual_review':'pending','runtime_verified':False,'release_eligible':False})
 del model;torch.cuda.empty_cache()
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17);pages=[]
for gid in ['FM0160','FM0188']:
 images=[(rows[gid+'-wdn']['source'],'원본 · 단순 확대'),(rows[gid+'-wdn']['output'],'초기 WDN · 균열'),*[(next(v['output'] for v in files if v['id']==gid+'-'+t),t) for t,_,_ in configs]];src=Image.open(images[0][0]);w=512;h=round(w*src.height/src.width);ch=h+40;canvas=Image.new('RGB',(1048,ch*2),'#25313c');d=ImageDraw.Draw(canvas)
 for i,(p,label) in enumerate(images):
  x=i%2*524+4;y=i//2*ch;d.text((x,y+4),gid+' '+label,font=font,fill='white');im=Image.open(p).convert('RGB').resize((w,h),Image.Resampling.NEAREST if i==0 else Image.Resampling.LANCZOS);canvas.paste(im,(x,y+32))
 p=R/'outputs/field-sr002'/f'rework-{gid}.png';canvas.save(p);pages.append({'path':str(p),'sha256':sha(p),'group_id':gid,'review_status':'pending'})
Q.write_text(json.dumps({'schema':'brs-field-rework/v2','files':files,'actual_local_rgb_inference_passes':4,'new_unique_originals':0,'external_calls':0,'image_upload':False,'pages':pages,'runtime_verified':False},ensure_ascii=False,indent=2),'utf8');print('Four rework passes complete.')
