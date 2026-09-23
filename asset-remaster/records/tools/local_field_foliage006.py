from pathlib import Path
import sys,json,hashlib,time,shutil,gc
sys.dont_write_bytecode=True
import numpy as np,torch
from PIL import Image,ImageFilter,ImageDraw,ImageFont
from local_sr import load_model,infer_rgb
from foliage_alpha006 import make_alpha,prepare_rgb,topology
R=Path(__file__).resolve().parents[1];O=R/'workspace/local-sr/field-foliage006';P=R/'outputs/field-foliage006';Q=R/'qa/field_foliage006_local.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text('utf8'))
def write(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False),'utf8')
audit=read(R/'qa/field_foliage006_source_audit.json');models=read(R/'workspace/local-sr/models/models.json')['records'];program=O/'foliage_alpha006_frozen.py'
if not program.exists():shutil.copy2(R/'tools/foliage_alpha006.py',program)
assert sha(program)==sha(R/'tools/foliage_alpha006.py')
rep=read(Q) if Q.exists() else {'schema':'brs-field-foliage006-local/v1','source_audit_sha256':sha(R/'qa/field_foliage006_source_audit.json'),'alpha_program':str(program),'alpha_program_sha256':sha(program),'prepared_sources':[],'files':[],'actual_local_RGB_passes':0,'new_local_unique_originals':9,'alpha_neural_passes':0,'external_calls':0,'pages':[],'runtime_verified':False,'release_eligible':False};assert rep['source_audit_sha256']==sha(R/'qa/field_foliage006_source_audit.json');prepared={v['group_id']:v for v in rep['prepared_sources']};done={v['id']:v for v in rep['files']}
for v in audit['files']:
 gid=v['group_id'];src=Image.open(v['source']).convert('RGBA');a=np.asarray(src);assert sha(v['source_ptm'])==v['source_ptm_sha256'] and hashlib.sha256(a.tobytes()).hexdigest()==v['source_rgba_sha256']
 if gid in prepared:
  for k in ['input','alpha','alpha_unrepaired']:assert sha(prepared[gid][k])==prepared[gid][k+'_sha256']
  continue
 alpha,base,junctions=make_alpha(a[:,:,3]);wanted=topology(a[:,:,3]>0);thresholds=sorted({1,255}|{int(t)+1 for t in np.unique(alpha) if 0<int(t)<255});observed={str(t):topology(alpha>=t) for t in thresholds};assert all(z==wanted for z in observed.values());assert np.array_equal(alpha[4::8,4::8],a[:,:,3])
 raw=prepare_rgb(a);pre=Image.fromarray(raw).filter(ImageFilter.GaussianBlur(.25));pad=8;inp=Image.fromarray(np.pad(np.asarray(pre),((pad,pad),(pad,pad),(0,0)),mode='reflect'));ip=O/(gid+'-input.png');inp.save(ip);ap=O/(gid+'-source-alpha8x.png');Image.fromarray(alpha).save(ap);bp=O/(gid+'-alpha-before-junction-fix.png');Image.fromarray(base).save(bp)
 p={**{k:v[k] for k in ['group_id','source','source_ptm','source_ptm_sha256','source_rgba_sha256']},'input':str(ip),'input_sha256':sha(ip),'alpha':str(ap),'alpha_sha256':sha(ap),'alpha_unrepaired':str(bp),'alpha_unrepaired_sha256':sha(bp),'prefilter_sigma_source':.25,'reflect_padding_source_px':8,'alpha_method':'Source binary signed-distance interpolation with1output-pixel antialias width; two source-foreground corner pixels per diagonal junction restored to255. Original pixel-center alpha and foreground8/background4 topology checked at every distinct output alpha threshold.','diagonal_junctions':junctions,'source_topology':wanted,'threshold_topology':observed,'all_integer_alpha_thresholds_1_to255_covered':True,'alpha_mass_ratio':float(alpha.sum()/64/a[:,:,3].sum()),'alpha_source_centers_exact':True,'hidden_RGB_method':'Nearest original opaque-pixel RGB extended into transparent pixels before local inference; visible source RGB is not replaced by this fill.'};rep['prepared_sources'].append(p);prepared[gid]=p;write(Q,rep);print('ALPHA',gid,'thresholds',len(thresholds),'junctions',len(junctions),flush=True)
for tag,name in [('wdn','realesr-general-wdn-x4v3.pth'),('photo','RealESRGAN_x4plus.pth')]:
 modelinfo=next(m for m in models if m['name']==name);model=load_model(Path(modelinfo['path']),modelinfo['sha256'])
 for v in audit['files']:
  gid=v['group_id'];id=gid+'-'+tag
  if id in done:
   assert sha(done[id]['output'])==done[id]['output_sha256'];continue
  prep=prepared[gid];src=Image.open(v['source']).convert('RGBA');start=time.monotonic();inp=Image.open(prep['input']).convert('RGB');full=infer_rgb(model,inp);fp=O/(id+'-native4x-full.png');full.save(fp);native=full.crop((32,32,(src.width+8)*4,(src.height+8)*4));npth=O/(id+'-native4x.png');native.save(npth);rgb=native.resize((src.width*8,src.height*8),Image.Resampling.LANCZOS);out=rgb.convert('RGBA');out.putalpha(Image.open(prep['alpha']));op=O/(id+'-8x.png');out.save(op)
  a=np.asarray(src);b=np.asarray(out);visible=a[:,:,3]>0;small=np.asarray(rgb.resize(src.size,Image.Resampling.LANCZOS));delta=small[:,:,:3].astype(float)-a[:,:,:3];metrics={'visible_source_RGB_MAE':float(abs(delta[visible]).mean()),'visible_source_mean_shift_RGB':delta[visible].mean(0).tolist(),'interpretation':'Only a source-scale color consistency diagnostic; not visual acceptance, restored ground truth or runtime alpha evidence.'}
  z={**{k:v[k] for k in ['group_id','source','source_ptm','source_ptm_sha256','source_rgba_sha256']},'id':id,'model':modelinfo,'prepared_source':gid,'input':prep['input'],'input_sha256':prep['input_sha256'],'alpha':prep['alpha'],'alpha_sha256':prep['alpha_sha256'],'native_full':str(fp),'native_full_sha256':sha(fp),'native':str(npth),'native_sha256':sha(npth),'output':str(op),'output_sha256':sha(op),'output_size':list(out.size),'actual_RGB_passes':1,'seconds':time.monotonic()-start,'source_scale_metrics':metrics,'method':'Nearest-opaque RGB extension, Gaussian.25source, reflect8pad; real localRGB4x, crop, Lanczos2x. Original-derived topology-preserving alpha combined separately; no neural alpha.','visual_review':'pending','runtime_verified':False,'release_eligible':False};rep['files'].append(z);rep['actual_local_RGB_passes']+=1;done[id]=z;write(Q,rep);print('INFERRED',id,flush=True)
 del model;gc.collect();torch.cuda.empty_cache()
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',16);rep['pages']=[]
boxes={'FM0290':(20,0,60,40),'FM0301':(12,12,52,52),'FM0312':(72,16,112,56),'FM0314':(28,20,68,60),'FM0316':(28,20,68,60),'FM0317':(28,20,68,60),'FM0318':(72,16,112,56),'FM0320':(20,4,60,44),'FM0325':(28,20,68,60)}
for v in audit['files']:
 gid=v['group_id']
 for tag,box in [('whole',None),('native',boxes[gid])]:
  can=Image.new('RGB',(1050,810),'#25313c');d=ImageDraw.Draw(can)
  for row,(matte,mlabel) in enumerate([('#18222c','어두운 배경'),('#dedede','밝은 배경')]):
   for col,(path,title) in enumerate([(v['source'],'원본 · 단순 확대'),(done[gid+'-wdn']['output'],'로컬 WDN'),(done[gid+'-photo']['output'],'로컬 Photo')]):
    im=Image.open(path).convert('RGBA')
    if box:im=im.crop(box if col==0 else tuple(t*8 for t in box))
    scale=min(320/im.width,340/im.height);im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST if col==0 else Image.Resampling.LANCZOS);bg=Image.new('RGBA',im.size,matte);bg.alpha_composite(im);d.text((col*350+8,row*405+8),gid+' '+title,font=font,fill='white');d.text((col*350+8,row*405+30),mlabel,font=font,fill='#c7d1da');can.paste(bg.convert('RGB'),(col*350+(350-bg.width)//2,row*405+58+(340-bg.height)//2))
  pp=P/(gid+'-local-'+tag+'.png');can.save(pp);rep['pages'].append({'path':str(pp),'sha256':sha(pp),'group_id':gid,'source_box':box,'mattes':['#18222c','#dedede'],'review_status':'pending'})
write(Q,rep);print(json.dumps({'actual_RGB_passes':rep['actual_local_RGB_passes'],'outputs':len(rep['files']),'dual_matte_pages':len(rep['pages'])}),flush=True)
