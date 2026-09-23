from pathlib import Path
import sys,json,hashlib,time,gc
sys.dont_write_bytecode=True
R=Path(r'P:\AI\Codex\projects\black-rock-shooter-hd-ui-fonts');sys.path.insert(0,str(R/'tools'))
import numpy as np,torch
from PIL import Image,ImageDraw,ImageFont
from local_sr import load_model,infer_rgb,MODEL,MODEL_SHA,MODEL_URL
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text('utf8'))
O=R/'workspace/local-sr/field-foliage006-priors';P=R/'outputs/field-foliage006';Q=R/'qa/field_foliage006_priors.json';assert not Q.exists();O.mkdir(exist_ok=True)
mattepath=R/'qa/field_foliage006_matte.json';m=read(mattepath);old={x['group_id']:x for x in m['files'] if x['id'].endswith('-photo-matte')};models=read(R/'workspace/local-sr/models/models.json')['records']
sw=next(x for x in models if 'classicalSR' in x['name']);an={'name':MODEL.name,'path':str(MODEL),'sha256':MODEL_SHA,'source_url':MODEL_URL}
rep={'schema':'brs-field-foliage006-alternative-priors/v1','matte_report':str(mattepath),'matte_report_sha256':sha(mattepath),'changed_variable':'Same authored-RGB input and protected source alpha; replace WDN/Photo prior with classical SwinIR or Anime6B.','actual_RGB_passes':0,'new_unique_originals':0,'external_calls':0,'alpha_neural_passes':0,'files':[],'pages':[],'runtime_verified':False,'release_eligible':False}
def save():Q.write_text(json.dumps(rep,ensure_ascii=False,indent=2,allow_nan=False),'utf8')
for tag,modelinfo in [('swinir',sw),('anime6b',an)]:
 model=load_model(Path(modelinfo['path']),modelinfo['sha256'])
 for p in m['inputs']:
  gid=p['group_id'];s=Image.open(p['source']).convert('RGBA');assert sha(p['input'])==p['input_sha256'] and sha(p['alpha'])==p['alpha_sha256'];t=time.monotonic()
  full=infer_rgb(model,Image.open(p['input']));fp=O/(gid+'-'+tag+'-native4x-full.png');full.save(fp);native=full.crop((32,32,(s.width+8)*4,(s.height+8)*4));npth=O/(gid+'-'+tag+'-native4x.png');native.save(npth);out=native.resize((s.width*8,s.height*8),Image.Resampling.LANCZOS).convert('RGBA');out.putalpha(Image.open(p['alpha']));op=O/(gid+'-'+tag+'-8x.png');out.save(op)
  rep['files'].append({**p,'id':gid+'-'+tag,'model':modelinfo,'native_full':str(fp),'native_full_sha256':sha(fp),'native':str(npth),'native_sha256':sha(npth),'output':str(op),'output_sha256':sha(op),'seconds':time.monotonic()-t,'review_status':'pending'});rep['actual_RGB_passes']+=1;save();print('INFERRED',gid,tag,flush=True)
 del model;gc.collect();torch.cuda.empty_cache()
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',15)
for z in rep['files']:
 gid=z['group_id'];boxes=[('whole',None),('native',(20,0,60,40) if gid=='FM0290' else (28,20,68,60))]
 if gid=='FM0314':boxes.append(('trunks',(28,80,68,120)))
 for tag,box in boxes:
  can=Image.new('RGB',(1050,810),'#25313c');d=ImageDraw.Draw(can)
  for row,(matte,mlabel) in enumerate([('#18222c','어두운 배경'),('#dedede','밝은 배경')]):
   for col,(path,title) in enumerate([(z['source'],'원본 · 단순 확대'),(old[gid]['output'],'로컬 Photo · 원본 RGB'),(z['output'],z['id'])]):
    im=Image.open(path).convert('RGBA')
    if box:im=im.crop(box if col==0 else tuple(t*8 for t in box))
    scale=min(320/im.width,340/im.height);im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST if col==0 else Image.Resampling.LANCZOS);bg=Image.new('RGBA',im.size,matte);bg.alpha_composite(im);d.text((col*350+8,row*405+8),title,font=font,fill='white');d.text((col*350+8,row*405+30),mlabel,font=font,fill='#c7d1da');can.paste(bg.convert('RGB'),(col*350+(350-bg.width)//2,row*405+58+(340-bg.height)//2))
  pp=P/(z['id']+'-'+tag+'.png');can.save(pp);rep['pages'].append({'path':str(pp),'sha256':sha(pp),'output_id':z['id'],'source_box':box,'review_status':'pending'})
save();print(json.dumps({'passes':rep['actual_RGB_passes'],'pages':len(rep['pages'])}),flush=True)
