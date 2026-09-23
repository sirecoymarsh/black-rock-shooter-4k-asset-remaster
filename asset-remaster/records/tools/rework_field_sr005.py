"""A different local prior for two authored ornamental patterns; no external call."""
from pathlib import Path
import sys,json,hashlib,time
sys.dont_write_bytecode=True
from PIL import Image,ImageFilter,ImageDraw,ImageFont
from local_sr import load_model,infer_rgb,roundtrip_metrics,MODEL,MODEL_SHA
R=Path(__file__).resolve().parents[1];Q=R/'qa/field_sr005_rework.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text('utf8'))
def write(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2),'utf8')
b=read(R/'qa/field_sr005_inference.json');base={v['id']:v for v in b['files']};O=R/'workspace/local-sr/field-sr005'
rep=read(Q) if Q.exists() else {'schema':'brs-field-local-pattern-rework/v1','base_report_sha256':sha(R/'qa/field_sr005_inference.json'),'hypothesis':'A local anime line-art prior may preserve thin designed curls and repeat motifs better than the two photo priors; acceptance still requires source comparison.','actual_local_rgb_inference_passes':0,'actual_alpha_passes':0,'external_calls':0,'files':[],'pages':[],'runtime_verified':False,'release_eligible':False}
model=load_model(MODEL,MODEL_SHA);done={v['id']:v for v in rep['files']}
for gid in ['FM0525','FM0533']:
 id=gid+'-anime025'
 if id in done:assert sha(done[id]['output'])==done[id]['output_sha256'];continue
 start=time.monotonic();v=base[gid+'-photo'];s=Image.open(v['source']).convert('RGBA');inp=s.convert('RGB').filter(ImageFilter.GaussianBlur(.25));ip=O/f'{id}-input.png';inp.save(ip);n=infer_rgb(model,inp);npth=O/f'{id}-native4x.png';n.save(npth);o=n.resize((s.width*8,s.height*8),Image.Resampling.LANCZOS).convert('RGBA');op=O/f'{id}-8x.png';o.save(op)
 z={**{k:v[k] for k in ['group_id','source','source_ptm','source_ptm_sha256','source_rgba_sha256','classification']},'id':id,'model':{'name':MODEL.name,'path':str(MODEL),'sha256':MODEL_SHA},'input':str(ip),'input_sha256':sha(ip),'input_gaussian_sigma_source_px':.25,'native':str(npth),'native_sha256':sha(npth),'output':str(op),'output_sha256':sha(op),'output_size':list(o.size),'alpha':'opaque255','actual_local_rgb_inference_passes':1,'source_scale_metrics':roundtrip_metrics(s,o),'seconds':time.monotonic()-start,'visual_review':'pending_final_review','runtime_verified':False,'release_eligible':False};rep['files'].append(z);done[id]=z;rep['actual_local_rgb_inference_passes']+=1;write(Q,rep);print(id,flush=True)
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17);rep['pages']=[]
for gid,box in [('FM0525',(40,40,80,80)),('FM0533',(0,96,32,128))]:
 v=done[gid+'-anime025'];ims=[Image.open(v['source']).convert('RGBA'),Image.open(base[gid+'-photo']['output']).convert('RGBA'),Image.open(v['output']).convert('RGBA')];can=Image.new('RGB',(1050,760),'#25313c');d=ImageDraw.Draw(can)
 for col,(im,label) in enumerate(zip(ims,['원본 · 단순 확대','로컬 Photo','로컬 Anime6B 재시도'])):
  d.text((col*350+8,8),gid+' '+label,font=font,fill='white');sc=min(320/im.width,320/im.height);wh=(round(im.width*sc),round(im.height*sc));pic=im.resize(wh,Image.Resampling.NEAREST if col==0 else Image.Resampling.LANCZOS);can.paste(pic.convert('RGB'),(col*350+(350-wh[0])//2,38+(320-wh[1])//2))
  crop=im.crop(box if col==0 else tuple(z*8 for z in box));crop=crop.resize((crop.width*8,crop.height*8),Image.Resampling.NEAREST) if col==0 else crop;d.text((col*350+8,388),str(box)+' / 출력 원크기',font=font,fill='white');can.paste(crop.convert('RGB'),(col*350+(350-crop.width)//2,428))
 pp=R/f'outputs/field-sr005/{gid}-pattern-rework.png';can.save(pp);rep['pages'].append({'path':str(pp),'sha256':sha(pp),'group_id':gid,'source_box':box,'review_status':'pending_final_review'})
write(Q,rep)
