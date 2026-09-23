"""Twenty source-reviewed materials: local RGB comparisons, source-owned alpha."""
from pathlib import Path
import sys,json,hashlib,time,gc
sys.dont_write_bytecode=True
import torch
from PIL import Image,ImageFilter,ImageDraw,ImageFont
from local_sr import load_model,infer_rgb,roundtrip_metrics
R=Path(__file__).resolve().parents[1]
Q=R/'qa/field_sr005_inference.json';S=R/'qa/field_source_review04.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text('utf8'))
def write(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2),'utf8')
s=read(S);ids=s['selected_for_local_comparison'];assert len(ids)==20
rows={v['group_id']:v for v in s['files']};cat=read(R/'qa/field_sr_catalog.json')
groups={v['group_id']:v for v in cat['groups']}
assert all(not groups[g]['local_sr_attempted'] and groups[g]['status']=='not_processed_in_field_context' for g in ids)
O=R/'workspace/local-sr/field-sr005';P=R/'outputs/field-sr005';O.mkdir(exist_ok=True);P.mkdir(exist_ok=True)
rep=read(Q) if Q.exists() else {'schema':'brs-field-local-sr/v5','batch':'FIELD-SR-005','source_review':str(S),'source_review_sha256':sha(S),'source_catalog_sha256_before':sha(R/'qa/field_sr_catalog.json'),'geometry_contract_sha256_before':sha(R/'qa/architectural_geometry_contract.json'),'group_ids':ids,'unique_originals':20,'actual_local_rgb_inference_passes':0,'actual_alpha_passes':0,'external_calls':0,'image_upload':False,'native_neural_scale':4,'final_scale':8,'post_scale':'Lanczos2x','device':torch.cuda.get_device_name(0),'torch':torch.__version__,'files':[],'pages':[],'runtime_verified':False,'release_eligible':False}
assert rep['source_review_sha256']==sha(S) and rep['group_ids']==ids
done={v['id']:v for v in rep['files']};models=read(R/'workspace/local-sr/models/models.json')['records']
choices=[('wdn','realesr-general-wdn-x4v3.pth'),('photo','RealESRGAN_x4plus.pth')]
for tag,name in choices:
 rec=next(m for m in models if m['name']==name);model=load_model(Path(rec['path']),rec['sha256'])
 for gid in ids:
  if gid+'-'+tag in done:
   assert sha(done[gid+'-'+tag]['output'])==done[gid+'-'+tag]['output_sha256'];continue
  start=time.monotonic();v=rows[gid];src=Image.open(v['source']).convert('RGBA')
  assert hashlib.sha256(src.tobytes()).hexdigest()==v['source_rgba_sha256'] and sha(v['source_ptm'])==v['source_ptm_sha256']
  assert src.getchannel('A').getextrema()[0]>=225
  sigma=.35 if v['classification'] in ['opaque_natural','nearopaque_natural'] else .25
  inp=src.convert('RGB').filter(ImageFilter.GaussianBlur(sigma));ip=O/f'{gid}-{tag}-input.png';inp.save(ip)
  native=infer_rgb(model,inp);npth=O/f'{gid}-{tag}-native4x.png';native.save(npth)
  out=native.resize((src.width*8,src.height*8),Image.Resampling.LANCZOS).convert('RGBA')
  alpha=src.getchannel('A').resize(out.size,Image.Resampling.BILINEAR);out.putalpha(alpha)
  op=O/f'{gid}-{tag}-8x.png';out.save(op)
  row={**{k:v[k] for k in ['group_id','representative','source','source_ptm','source_ptm_sha256','source_rgba_sha256','classification']},'id':gid+'-'+tag,'model':rec,'input':str(ip),'input_sha256':sha(ip),'input_gaussian_sigma_source_px':sigma,'native':str(npth),'native_sha256':sha(npth),'output':str(op),'output_sha256':sha(op),'output_size':list(out.size),'alpha':'source_bilinear8x' if alpha.getextrema()[0]<255 else 'opaque255','source_alpha_extrema':list(src.getchannel('A').getextrema()),'actual_local_rgb_inference_passes':1,'source_scale_metrics':roundtrip_metrics(src,out),'seconds':time.monotonic()-start,'visual_review':'pending_final_review','runtime_verified':False,'release_eligible':False}
  rep['files'].append(row);done[row['id']]=row;rep['actual_local_rgb_inference_passes']+=1;write(Q,rep);print('INFERRED',gid,tag,flush=True)
 del model;gc.collect();torch.cuda.empty_cache()
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17);rep['pages']=[]
for k in range(0,len(ids),2):
 can=Image.new('RGB',(1050,760),'#25313c');d=ImageDraw.Draw(can);batch=ids[k:k+2]
 for j,gid in enumerate(batch):
  v=rows[gid];ims=[Image.open(v['source']).convert('RGBA')]+[Image.open(done[gid+'-'+tag]['output']).convert('RGBA') for tag,_ in choices]
  for c,(im,label) in enumerate(zip(ims,['원본 · 단순 확대','로컬 WDN','로컬 Photo'])):
   x=c*350;y=j*380;d.text((x+8,y+8),gid+' '+label,font=font,fill='white');sc=min(320/im.width,320/im.height);wh=(round(im.width*sc),round(im.height*sc));pic=im.resize(wh,Image.Resampling.NEAREST if c==0 else Image.Resampling.LANCZOS)
   mat=Image.new('RGB',wh,'#444950');mat.paste(pic,(0,0),pic);can.paste(mat,(x+(350-wh[0])//2,y+38+(320-wh[1])//2))
 path=P/f'review-{k//2+1:02d}.png';can.save(path);rep['pages'].append({'path':str(path),'sha256':sha(path),'group_ids':batch,'review_status':'pending_final_review'})
write(Q,rep);print(json.dumps({'originals':20,'passes':rep['actual_local_rgb_inference_passes'],'pages':len(rep['pages'])}),flush=True)
