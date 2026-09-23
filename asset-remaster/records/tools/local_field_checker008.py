"""Local comparisons for ornamental checks; cell-isolated inference for FM0498."""
from pathlib import Path
import sys,json,hashlib,gc,time
sys.dont_write_bytecode=True
import numpy as np,torch
from PIL import Image,ImageFilter,ImageDraw,ImageFont
from local_sr import load_model,infer_rgb,roundtrip_metrics
R=Path(__file__).resolve().parents[1];O=R/'workspace/local-sr/field-geometry008';P=R/'outputs/field-geometry008';Q=R/'qa/field_geometry008_local.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text('utf8'))
def write(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2),'utf8')
audit=read(R/'qa/field_geometry008_source_audit.json');sources={v['group_id']:v for v in audit['files']};ids=['FM0394','FM0430','FM0444','FM0498'];models=read(R/'workspace/local-sr/models/models.json')['records'];choices=[('wdn','realesr-general-wdn-x4v3.pth'),('photo','RealESRGAN_x4plus.pth')]
rep=read(Q) if Q.exists() else {'schema':'brs-checker-local-comparison/v1','source_audit_sha256':sha(R/'qa/field_geometry008_source_audit.json'),'source_catalog_sha256_before':sha(R/'qa/field_sr_catalog.json'),'group_ids':ids,'new_neural_unique_originals':4,'actual_local_RGB_passes':0,'alpha_passes':0,'external_calls':0,'files':[],'completed_components':[],'pages':[],'runtime_verified':False,'release_eligible':False};assert rep['source_audit_sha256']==sha(R/'qa/field_geometry008_source_audit.json');done={v['id']:v for v in rep['files']};cdone={v['id']:v for v in rep['completed_components']}
for tag,name in choices:
 modelinfo=next(z for z in models if z['name']==name);model=load_model(Path(modelinfo['path']),modelinfo['sha256'])
 for gid in ids:
  id=gid+'-'+tag
  if id in done:assert sha(done[id]['output'])==done[id]['output_sha256'];continue
  v=sources[gid];src=Image.open(v['source']).convert('RGBA');assert src.getchannel('A').getextrema()==(255,255);assert sha(v['source_ptm'])==v['source_ptm_sha256'];assert hashlib.sha256(src.tobytes()).hexdigest()==v['source_rgba_sha256'];start=time.monotonic();components=[]
  boxes=[[0,0,src.width,src.height]] if gid!='FM0498' else [[x,y,x+64,y+64] for y in [0,64] for x in [0,64]]
  whole_native=Image.new('RGB',(src.width*4,src.height*4));whole=Image.new('RGBA',(src.width*8,src.height*8))
  for index,box in enumerate(boxes):
   cid=id+f'-cell{index}';patch=src.crop(box).convert('RGB');pad=8 if gid=='FM0498' else 0;sigma=.35 if gid=='FM0498' else .25
   if cid in cdone:
    comp=cdone[cid];assert sha(comp['native_full'])==comp['native_full_sha256'];nativefull=Image.open(comp['native_full']).convert('RGB')
   else:
    pre=patch.filter(ImageFilter.GaussianBlur(sigma));inp=Image.fromarray(np.pad(np.asarray(pre),((pad,pad),(pad,pad),(0,0)),mode='reflect')) if pad else pre;ip=O/f'{cid}-input.png';inp.save(ip);nativefull=infer_rgb(model,inp);npth=O/f'{cid}-native4x-full.png';nativefull.save(npth);comp={'id':cid,'source_box':box,'model':modelinfo,'input':str(ip),'input_sha256':sha(ip),'prefilter_sigma_source':sigma,'reflect_padding_source_px':pad,'native_full':str(npth),'native_full_sha256':sha(npth),'actual_RGB_passes':1};rep['completed_components'].append(comp);cdone[cid]=comp;rep['actual_local_RGB_passes']+=1;write(Q,rep);print('INFERRED',cid,flush=True)
   native=nativefull.crop((pad*4,pad*4,(pad+patch.width)*4,(pad+patch.height)*4));piece=native.resize((patch.width*8,patch.height*8),Image.Resampling.LANCZOS)
   if gid=='FM0498':
    a=np.asarray(piece).astype('float32');target=np.asarray(patch).mean((0,1));offset=target-a.mean((0,1));piece=Image.fromarray(np.rint(np.clip(a+offset,0,255)).astype('uint8'));comp={**comp,'mean_RGB_offset_after_resize':offset.tolist(),'source_mean_RGB':target.tolist(),'output_mean_RGB':np.asarray(piece).mean((0,1)).tolist()}
   whole_native.paste(native,(box[0]*4,box[1]*4));whole.paste(piece.convert('RGBA'),(box[0]*8,box[1]*8));components.append(comp)
  nativepath=O/f'{id}-native4x.png';whole_native.save(nativepath);op=O/f'{id}-8x.png';whole.save(op);row={**{k:v[k] for k in ['group_id','source','source_ptm','source_ptm_sha256','source_rgba_sha256']},'id':id,'model':modelinfo,'components':components,'native':str(nativepath),'native_sha256':sha(nativepath),'output':str(op),'output_sha256':sha(op),'output_size':list(whole.size),'actual_RGB_passes':len(boxes),'source_scale_metrics':roundtrip_metrics(src,whole),'method':'Independent4 cells, reflect-padded local4x, Lanczos2x per cell and source mean RGB recenter, exact source cell boundaries.' if gid=='FM0498' else 'Whole RGB local4x then Lanczos2x trial; checker design still requires source review.','seconds':time.monotonic()-start,'visual_review':'pending','runtime_verified':False,'release_eligible':False};rep['files'].append(row);done[id]=row;write(Q,rep)
 del model;gc.collect();torch.cuda.empty_cache()
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17);rep['pages']=[]
for gid in ids:
 for tag,box in [('whole',None),('native',{'FM0394':(40,20,80,60),'FM0430':(48,58,88,98),'FM0444':(18,22,58,62),'FM0498':(44,44,84,84)}[gid])]:
  can=Image.new('RGB',(1050,410),'#25313c');d=ImageDraw.Draw(can)
  for col,(path,label) in enumerate([(sources[gid]['source'],'원본 · 단순 확대'),(done[gid+'-wdn']['output'],'로컬 WDN'),(done[gid+'-photo']['output'],'로컬 Photo')]):
   im=Image.open(path).convert('RGBA')
   if box:im=im.crop(box if col==0 else tuple(t*8 for t in box));scale=8 if col==0 else 1
   else:scale=min(320/im.width,340/im.height)
   pic=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST if col==0 else Image.Resampling.LANCZOS);d.text((col*350+8,8),gid+' '+label,font=font,fill='white');can.paste(pic.convert('RGB'),(col*350+(350-pic.width)//2,48+(340-pic.height)//2))
  pp=P/f'{gid}-local-{tag}.png';can.save(pp);rep['pages'].append({'path':str(pp),'sha256':sha(pp),'group_id':gid,'source_box':box,'review_status':'pending'})
write(Q,rep);print(json.dumps({'unique_originals':4,'actual_RGB_passes':rep['actual_local_RGB_passes'],'composite_outputs':8,'pages':8}),flush=True)
