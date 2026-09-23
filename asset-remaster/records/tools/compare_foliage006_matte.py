from pathlib import Path
import sys, json, hashlib, time, gc
sys.dont_write_bytecode = True
R = Path(r'P:\AI\Codex\projects\black-rock-shooter-hd-ui-fonts')
sys.path.insert(0, str(R/'tools'))
import numpy as np, torch
from PIL import Image, ImageFilter, ImageDraw, ImageFont
from local_sr import load_model, infer_rgb
O=R/'workspace/local-sr/field-foliage006-matte'; P=R/'outputs/field-foliage006'; Q=R/'qa/field_foliage006_matte.json'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text('utf8'))
def save(): Q.write_text(json.dumps(rep,ensure_ascii=False,indent=2,allow_nan=False),'utf8')
assert not Q.exists()
O.mkdir(parents=True,exist_ok=True)
rawpath=R/'qa/field_foliage006_local.json';raw=read(rawpath)
prepared={p['group_id']:p for p in raw['prepared_sources']}
old={p['id']:p for p in raw['files']}
models=read(R/'workspace/local-sr/models/models.json')['records']
gids=['FM0290','FM0314']
rep={'schema':'brs-field-foliage006-matte-ablation/v1','prior_report':str(rawpath),'prior_report_sha256':sha(rawpath),'previous_turn':'progress: inspected the remaining11 comparison pages and recorded all9 as needing rework','changed_variable':'Use original authored RGB including hidden RGB instead of nearest-opaque hidden-RGB extension. Gaussian.25, padding, models, native4x/8x resampling and alpha remain identical.','files':[],'inputs':[],'pages':[],'actual_RGB_passes':0,'new_unique_originals':0,'alpha_neural_passes':0,'external_calls':0,'runtime_verified':False,'release_eligible':False}
for gid in gids:
 p=prepared[gid];s=Image.open(p['source']).convert('RGBA');a=np.asarray(s)
 assert hashlib.sha256(a.tobytes()).hexdigest()==p['source_rgba_sha256'] and sha(p['source_ptm'])==p['source_ptm_sha256']
 pre=s.convert('RGB').filter(ImageFilter.GaussianBlur(.25));inp=Image.fromarray(np.pad(np.asarray(pre),((8,8),(8,8),(0,0)),mode='reflect'))
 ip=O/(gid+'-authored-matte-input.png');inp.save(ip)
 rep['inputs'].append({'group_id':gid,'source':p['source'],'source_rgba_sha256':p['source_rgba_sha256'],'input':str(ip),'input_sha256':sha(ip),'alpha':p['alpha'],'alpha_sha256':p['alpha_sha256']})
save()
for tag,name in [('wdn','realesr-general-wdn-x4v3.pth'),('photo','RealESRGAN_x4plus.pth')]:
 m=next(m for m in models if m['name']==name);model=load_model(Path(m['path']),m['sha256'])
 for p in rep['inputs']:
  gid=p['group_id'];s=Image.open(p['source']).convert('RGBA');t=time.monotonic();full=infer_rgb(model,Image.open(p['input']));fp=O/(gid+'-'+tag+'-matte-native4x-full.png');full.save(fp)
  native=full.crop((32,32,(s.width+8)*4,(s.height+8)*4));npth=O/(gid+'-'+tag+'-matte-native4x.png');native.save(npth)
  rgb=native.resize((s.width*8,s.height*8),Image.Resampling.LANCZOS);out=rgb.convert('RGBA');out.putalpha(Image.open(p['alpha']));op=O/(gid+'-'+tag+'-matte-8x.png');out.save(op)
  assert sha(p['alpha'])==p['alpha_sha256'];assert np.array_equal(np.asarray(out)[:,:,3],np.asarray(Image.open(p['alpha'])))
  delta=np.asarray(rgb.resize(s.size,Image.Resampling.LANCZOS)).astype(float)-np.asarray(s)[:,:,:3];visible=np.asarray(s)[:,:,3]>0
  z={**p,'id':gid+'-'+tag+'-matte','model':m,'native_full':str(fp),'native_full_sha256':sha(fp),'native':str(npth),'native_sha256':sha(npth),'output':str(op),'output_sha256':sha(op),'output_size':list(out.size),'seconds':time.monotonic()-t,'source_visible_RGB_MAE':float(abs(delta[visible]).mean()),'metrics_limitation':'Consistency only, not visual quality','prior_id':gid+'-'+tag,'prior_output':old[gid+'-'+tag]['output'],'prior_output_sha256':old[gid+'-'+tag]['output_sha256'],'review_status':'pending'}
  rep['files'].append(z);rep['actual_RGB_passes']+=1;save();print('INFERRED',z['id'],flush=True)
 del model;gc.collect();torch.cuda.empty_cache()
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',15)
for z in rep['files']:
 gid=z['group_id'];boxes=[('whole',None),('native',(20,0,60,40) if gid=='FM0290' else (28,20,68,60))]
 if gid=='FM0314':boxes.append(('trunks',(28,80,68,120)))
 for tag,box in boxes:
  can=Image.new('RGB',(1050,810),'#25313c');d=ImageDraw.Draw(can)
  for row,(matte,mlabel) in enumerate([('#18222c','어두운 배경'),('#dedede','밝은 배경')]):
   for col,(path,title) in enumerate([(z['source'],'원본 · 단순 확대'),(z['prior_output'],'이전 · 투명부 색 확장'),(z['output'],'변경 · 원본 RGB 유지')]):
    im=Image.open(path).convert('RGBA')
    if box:im=im.crop(box if col==0 else tuple(t*8 for t in box))
    scale=min(320/im.width,340/im.height);im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST if col==0 else Image.Resampling.LANCZOS)
    bg=Image.new('RGBA',im.size,matte);bg.alpha_composite(im)
    d.text((col*350+8,row*405+8),z['id']+' '+title,font=font,fill='white');d.text((col*350+8,row*405+30),mlabel,font=font,fill='#c7d1da');can.paste(bg.convert('RGB'),(col*350+(350-bg.width)//2,row*405+58+(340-bg.height)//2))
  pp=P/(z['id']+'-'+tag+'.png');can.save(pp);rep['pages'].append({'path':str(pp),'sha256':sha(pp),'output_id':z['id'],'source_box':box,'review_status':'pending'})
save();print(json.dumps({'passes':rep['actual_RGB_passes'],'pages':len(rep['pages'])}),flush=True)
