"""One bounded alternative for flat distant architecture that local models extruded."""
import sys,json,time,hashlib,gc
from pathlib import Path
import numpy as np,torch
from scipy.ndimage import gaussian_filter,distance_transform_edt
from PIL import Image,ImageDraw,ImageFont
from local_sr import load_model,infer_rgb,MODEL,MODEL_SHA
sys.stdout.reconfigure(encoding='utf8');sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1];Q=R/'qa/field_sr003_rework.json';assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save():Q.write_text(json.dumps(rep,ensure_ascii=False,indent=2),'utf8')
base=json.loads((R/'qa/field_sr003_inference.json').read_text('utf8'));models=json.loads((R/'workspace/local-sr/models/models.json').read_text('utf8'))['records'];ids=['FM0115','FM0121','FM0122'];O=R/'workspace/local-sr/field-sr003-rework';O.mkdir(exist_ok=False)
choices=[('wdn065',.65,next(m for m in models if m['name']=='realesr-general-wdn-x4v3.pth')),('anime035',.35,{'path':str(MODEL),'sha256':MODEL_SHA,'name':MODEL.name})]
rep={'schema':'brs-field-alpha-rework/v1','batch':'FIELD-SR-003','basis':'Both initial local outputs exaggerated flat distant architecture boundaries as peeling/deep edges. Compare more prefiltering and Fate anime model, preserving initial Photo alpha exactly.','new_unique_originals':0,'image_upload':False,'external_calls':0,'files':[],'pages':[],'actual_local_inference_passes':0,'runtime_verified':False,'release_eligible':False}
for tag,sigma,rec in choices:
 model=load_model(Path(rec['path']),rec['sha256'])
 for gid in ids:
  start=time.monotonic();v=next(v for v in base['files'] if v['group_id']==gid and v['model_id']=='photo');src=Image.open(v['source']).convert('RGBA');parent=Image.open(v['output']).convert('RGBA');a=np.asarray(src,dtype=np.float32)/255.;alpha=a[:,:,3];cov=gaussian_filter(alpha,sigma,mode='nearest');rgb=gaussian_filter(a[:,:,:3]*alpha[:,:,None],(sigma,sigma,0),mode='nearest')/np.maximum(cov[:,:,None],1e-6);vis=cov>1e-6
  if not vis.all():
   near=distance_transform_edt(~vis,return_distances=False,return_indices=True);rgb[~vis]=rgb[near[0][~vis],near[1][~vis]]
  inp=Image.fromarray(np.rint(np.clip(rgb,0,1)*255).astype('uint8'));ip=O/f'{gid}-{tag}-input.png';inp.save(ip);native=infer_rgb(model,inp);npth=O/f'{gid}-{tag}-native4x.png';native.save(npth);rgb=np.asarray(native.resize(parent.size,Image.Resampling.LANCZOS),dtype=np.float32);pa=np.asarray(parent.getchannel('A'));oa=np.asarray(src,dtype=np.float32);ow=oa[:,:,3:4]/255.;pw=pa[:,:,None].astype(np.float32)/255.;offset=(oa[:,:,:3]*ow).sum((0,1))/ow.sum()-(rgb*pw).sum((0,1))/pw.sum();out=Image.fromarray(np.rint(np.clip(rgb+offset,0,255)).astype('uint8'));out.putalpha(parent.getchannel('A'));op=O/f'{gid}-{tag}-8x.png';out.save(op)
  rep['files'].append({**{k:v[k] for k in ['group_id','representative','source','source_ptm','source_ptm_sha256','source_rgba_sha256','classification']},'id':gid+'-'+tag,'model':rec,'input':str(ip),'input_sha256':sha(ip),'input_gaussian_sigma_source_px':sigma,'native':str(npth),'native_sha256':sha(npth),'alpha_parent':v['output'],'alpha_parent_sha256':v['output_sha256'],'alpha_method':'byte-exact initial Photo alpha; no new alpha inference','weighted_mean_rgb_offset':offset.tolist(),'output':str(op),'output_sha256':sha(op),'output_size':list(out.size),'actual_local_inference_passes':1,'seconds':time.monotonic()-start,'visual_review':'pending','runtime_verified':False,'release_eligible':False});rep['actual_local_inference_passes']+=1;save()
 del model;gc.collect();torch.cuda.empty_cache();print(tag,'completed',flush=True)
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17)
for gid in ids:
 v=next(v for v in base['files'] if v['group_id']==gid and v['model_id']=='photo');src=Image.open(v['source']).convert('RGBA');ims=[src,Image.open(v['output']).convert('RGBA')]+[Image.open(next(v for v in rep['files'] if v['id']==gid+'-'+tag)['output']).convert('RGBA') for tag,_,_ in choices]
 scale=min(496/src.width,496/src.height,8);wh=(round(src.width*scale),round(src.height*scale));ch=wh[1]+44;canvas=Image.new('RGB',(1040,ch*4),'#27323b');d=ImageDraw.Draw(canvas)
 for i,(im,label) in enumerate(zip(ims,['원본 · 단순 확대','초기 Photo','WDN 입력 잡음 완화','Fate anime 모델'])):
  for j,bg in enumerate(['#242b33','#d4d5d7']):
   x=j*520;y=i*ch;d.text((x+8,y+7),gid+' '+label,font=font,fill='white');pic=im.resize(wh,Image.Resampling.NEAREST if i==0 else Image.Resampling.LANCZOS);matte=Image.new('RGB',wh,bg);matte.paste(pic,(0,0),pic);canvas.paste(matte,(x+8,y+35))
 p=R/f'outputs/field-sr003/rework-{gid}.png';canvas.save(p);rep['pages'].append({'group_id':gid,'path':str(p),'sha256':sha(p),'review_status':'pending'})
save();print(json.dumps({'new_originals':0,'new_rgb_passes':6,'new_outputs':6,'pages':3}))
