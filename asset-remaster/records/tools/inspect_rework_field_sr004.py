import sys,json,hashlib,time,gc
from pathlib import Path
sys.dont_write_bytecode=True
import torch,numpy as np
from PIL import Image,ImageFilter,ImageDraw,ImageFont
from local_sr import load_model,infer_rgb,roundtrip_metrics
sys.stdout.reconfigure(encoding='utf8')
R=Path(__file__).resolve().parents[1];Q=R/'qa/field_sr004_rework.json';assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
base=json.loads((R/'qa/field_sr004_inference.json').read_text('utf8'));rows={v['group_id']:v for v in base['files'] if v['id'].endswith('-wdn')};P=R/'outputs/field-sr004';O=R/'workspace/local-sr/field-sr004';font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17)
boxes={275:[40,8,72,40],276:[16,16,48,48],277:[16,16,48,48],280:[16,16,48,48],282:[0,16,32,48],286:[0,0,32,32],297:[16,16,48,48],302:[16,16,48,48],303:[16,16,48,48],304:[24,24,56,56],305:[16,16,48,48],306:[16,16,48,48],307:[16,48,48,80],313:[16,16,48,48],315:[16,16,48,48],322:[16,16,48,48],328:[64,0,96,32],329:[16,16,48,48],330:[32,32,64,64],332:[96,16,128,48],333:[80,32,112,64],334:[16,16,48,48],336:[48,20,80,52],337:[40,4,72,36],338:[48,16,80,48],345:[0,16,32,48],346:[0,0,32,32],347:[16,0,48,32],356:[40,16,72,48],363:[16,16,48,48]}
pages=[];ids=base['group_ids']
for k in range(0,len(ids),3):
 batch=ids[k:k+3];canvas=Image.new('RGB',(840,len(batch)*305),'#26333f');d=ImageDraw.Draw(canvas)
 for j,gid in enumerate(batch):
  box=boxes[int(gid[2:])];src=Image.open(rows[gid]['source']).convert('RGBA');ims=[src.crop(box).resize((256,256),Image.Resampling.NEAREST)]+[Image.open(next(v['output'] for v in base['files'] if v['id']==gid+'-'+tag)).convert('RGBA').crop(tuple(t*8 for t in box)) for tag in ['wdn','photo']]
  for c,(im,title) in enumerate(zip(ims,['원본 · 단순 확대','로컬 WDN · 실제 배율','로컬 Photo · 실제 배율'])):d.text((c*280+6,j*305+4),gid+' '+title,font=font,fill='white');canvas.paste(im.convert('RGB'),(c*280+6,j*305+34))
 path=P/f'native-crop-{k//3+1:02d}.png';canvas.save(path);pages.append({'path':str(path),'sha256':sha(path),'group_ids':batch,'source_boxes':{gid:boxes[int(gid[2:])] for gid in batch},'review_status':'pending'})
rep={'schema':'brs-field-sr004-rework/v1','basis':'Source blur/dither became extra cracks or overly deep ring/panel relief in initial comparisons; compare stronger WDN prefilter and a distinct local general model.','initial_inference_sha256':sha(R/'qa/field_sr004_inference.json'),'initial_native_crop_pages':pages,'files':[],'pages':[],'new_unique_originals':0,'actual_local_rgb_passes':0,'external_calls':0,'image_upload':False,'runtime_verified':False,'release_eligible':False};Q.write_text(json.dumps(rep,ensure_ascii=False,indent=2),'utf8')
models=json.loads((R/'workspace/local-sr/models/models.json').read_text('utf8'))['records']
for tag,name,sigma in [('wdn065','realesr-general-wdn-x4v3.pth',.65),('general035','realesr-general-x4v3.pth',.35)]:
 rec=next(m for m in models if m['name']==name);model=load_model(Path(rec['path']),rec['sha256'])
 for n in [303,305,336,363]:
  gid=f'FM{n:04d}';v=rows[gid];src=Image.open(v['source']).convert('RGBA');inp=src.convert('RGB').filter(ImageFilter.GaussianBlur(sigma));ip=O/f'{gid}-{tag}-input.png';inp.save(ip);native=infer_rgb(model,inp);npth=O/f'{gid}-{tag}-native4x.png';native.save(npth);out=native.resize((src.width*8,src.height*8),Image.Resampling.LANCZOS).convert('RGBA');op=O/f'{gid}-{tag}-8x.png';out.save(op)
  rep['files'].append({**{k:v[k] for k in ['group_id','source','source_ptm','source_ptm_sha256','source_rgba_sha256','classification']},'id':gid+'-'+tag,'model':rec,'input':str(ip),'input_sha256':sha(ip),'input_gaussian_sigma_source_px':sigma,'native':str(npth),'native_sha256':sha(npth),'output':str(op),'output_sha256':sha(op),'output_size':list(out.size),'actual_local_rgb_passes':1,'source_scale_metrics':roundtrip_metrics(src,out),'visual_review':'pending','runtime_verified':False,'release_eligible':False});rep['actual_local_rgb_passes']+=1;Q.write_text(json.dumps(rep,ensure_ascii=False,indent=2),'utf8');print('REWORK',gid,tag,flush=True)
 del model;gc.collect();torch.cuda.empty_cache()
for n in [303,305,336,363]:
 gid=f'FM{n:04d}';src=Image.open(rows[gid]['source']).convert('RGBA');canvas=Image.new('RGB',(1050,730),'#25313c');d=ImageDraw.Draw(canvas);ims=[src]+[Image.open(next(v['output'] for v in rep['files'] if v['id']==gid+'-'+tag)).convert('RGBA') for tag in ['wdn065','general035']]
 for c,(im,title) in enumerate(zip(ims,['원본 · 단순 확대','로컬 WDN · 보정 강도0.65','로컬 General · 보정0.35'])):
  d.text((c*350+6,5),gid+' '+title,font=font,fill='white');sc=min(320/im.width,320/im.height);wh=(round(im.width*sc),round(im.height*sc));pic=im.resize(wh,Image.Resampling.NEAREST if c==0 else Image.Resampling.LANCZOS);canvas.paste(pic.convert('RGB'),(c*350+6,40));box=boxes[n];crop=src.crop(box).resize((256,256),Image.Resampling.NEAREST) if c==0 else im.crop(tuple(t*8 for t in box));canvas.paste(crop.convert('RGB'),(c*350+6,420))
 path=P/f'rework-{gid}.png';canvas.save(path);rep['pages'].append({'path':str(path),'sha256':sha(path),'group_id':gid,'source_crop':boxes[n],'review_status':'pending'})
Q.write_text(json.dumps(rep,ensure_ascii=False,indent=2),'utf8');print(json.dumps({'native_crop_pages':len(pages),'rework_passes':8,'rework_pages':4}),flush=True)
