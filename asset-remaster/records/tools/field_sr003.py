"""Source-bound alpha field comparisons. RGB and alpha calls are counted separately."""
import sys,json,hashlib,time,gc
from pathlib import Path
import numpy as np,torch
from scipy.ndimage import gaussian_filter,distance_transform_edt
from PIL import Image,ImageDraw,ImageFont
from local_sr import load_model,infer_rgb
sys.dont_write_bytecode=True
sys.stdout.reconfigure(encoding='utf8')
R=Path(__file__).resolve().parents[1]
Q=R/'qa/field_sr003_inference.json'; O=R/'workspace/local-sr/field-sr003'; P=R/'outputs/field-sr003'
ids=[f'FM{x:04d}' for x in [29,37,38,45,47,59,60,87,113,115,116,120,121,122,123,124,145,157,164,254,255,256,260,263,264,268,272]]
thin={f'FM{x:04d}' for x in [47,59,60,87,123,157,263,264]}
nearopaque={'FM0268','FM0272'}
split={g:[(0,0,128,64),(0,64,128,128)] for g in ['FM0254','FM0255']}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads((R/p).read_text('utf8'))
def save():Q.write_text(json.dumps(rep,ensure_ascii=False,indent=2),'utf8')
reviews=['qa/field_source_review01.json','qa/field_source_review02.json']
rows={v['group_id']:v for p in reviews for v in read(p)['files']}
cat=read('qa/field_sr_catalog.json'); groups={g['group_id']:g for g in cat['groups']}
assert len(ids)==27 and all(not groups[g]['local_sr_attempted'] for g in ids)
assert not (R/'qa/field_sr003_review.json').exists()
for gid in ids:
 v=rows[gid]; src=Image.open(v['source']).convert('RGBA')
 assert hashlib.sha256(src.tobytes()).hexdigest()==v['source_rgba_sha256'];assert sha(v['source_ptm'])==v['source_ptm_sha256']
 assert v['source_review']=='directly_inspected_by_Codex_internal' and not groups[gid]['battle_pixel_equivalent_group']
O.mkdir(parents=True,exist_ok=True);P.mkdir(parents=True,exist_ok=True)
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17)
def composite(im,size,bg,resample):
 v=im.resize(size,resample);out=Image.new('RGB',size,bg);out.paste(v,(0,0),v);return out
if '--prepare' in sys.argv:
 for start in range(0,len(ids),9):
  canvas=Image.new('RGB',(1200,1020),'#26333f');d=ImageDraw.Draw(canvas)
  for j,gid in enumerate(ids[start:start+9]):
   im=Image.open(rows[gid]['source']).convert('RGBA');x=(j%3)*400;y=(j//3)*340;d.text((x+8,y+8),f'{gid} {im.width}x{im.height}',font=font,fill='white')
   sc=min(375/im.width,290/im.height,8);size=(round(im.width*sc),round(im.height*sc));canvas.paste(composite(im,size,'#83909c',Image.Resampling.NEAREST),(x+10,y+37))
  p=P/f'source-{start//9+1:02d}.png';canvas.save(p);print(p)
 raise SystemExit(0)
if Q.exists():
 rep=read('qa/field_sr003_inference.json');assert rep['group_ids']==ids
else:
 rep={'schema':'brs-field-local-alpha-sr/v1','batch':'FIELD-SR-003','group_ids':ids,'unique_originals':27,'source_reviews':{p:sha(R/p) for p in reviews},'source_catalog_sha256_before':sha(R/'qa/field_sr_catalog.json'),'device':torch.cuda.get_device_name(0),'torch':torch.__version__,'external_calls':0,'image_upload':False,'native_neural_scale':4,'final_scale':8,'post_scale':'Lanczos2x','panel_basis':'FM0254/0255 visible two-row source partition, not native UV evidence.','files':[],'pages':[],'runtime_verified':False,'release_eligible':False}
done={(v['group_id'],v['model_id']):v for v in rep['files']}
def prefilter(src,sigma):
 a=np.asarray(src,dtype=np.float32)/255.;alpha=a[:,:,3];cov=gaussian_filter(alpha,sigma,mode='nearest')
 premul=gaussian_filter(a[:,:,:3]*alpha[:,:,None],(sigma,sigma,0),mode='nearest');rgb=premul/np.maximum(cov[:,:,None],1e-6);vis=cov>1e-6
 if not vis.all():
  assert vis.any();near=distance_transform_edt(~vis,return_distances=False,return_indices=True);rgb[~vis]=rgb[near[0][~vis],near[1][~vis]]
 return Image.fromarray(np.rint(np.clip(rgb,0,1)*255).astype('uint8')),Image.fromarray(np.rint(np.clip(cov,0,1)*255).astype('uint8'))
models=read('workspace/local-sr/models/models.json')['records']
for mid,name in [('wdn','realesr-general-wdn-x4v3.pth'),('photo','RealESRGAN_x4plus.pth')]:
 rec=next(m for m in models if m['name']==name);model=load_model(Path(rec['path']),rec['sha256'])
 for gid in ids:
  if (gid,mid) in done:
   assert sha(done[(gid,mid)]['output'])==done[(gid,mid)]['output_sha256'];continue
  t=time.monotonic();v=rows[gid];src=Image.open(v['source']).convert('RGBA');sigma=.25 if gid in thin else .6 if gid=='FM0260' else .35
  weight=0. if gid in thin|nearopaque else .2
  boxes=split.get(gid,[(0,0,src.width,src.height)]);coverage=np.zeros((src.height,src.width),np.uint8)
  out=Image.new('RGBA',(src.width*8,src.height*8));ref=Image.new('L',out.size);parts=[];rgbpasses=0;apasses=0
  for pi,box in enumerate(boxes):
   x0,y0,x1,y1=box;coverage[y0:y1,x0:x1]+=1;part=src.crop(box);inp,alpha=prefilter(part,sigma);wh=(part.width*8,part.height*8);tag=f'{gid}-{mid}-p{pi}'
   ip=O/f'{tag}-rgb-input.png';ap=O/f'{tag}-alpha-input.png';inp.save(ip);alpha.save(ap)
   native=infer_rgb(model,inp);rgbpasses+=1;npth=O/f'{tag}-rgb4x.png';native.save(npth);rgb=np.asarray(native.resize(wh,Image.Resampling.LANCZOS),dtype=np.float32)
   linim=part.getchannel('A').resize(wh,Image.Resampling.BILINEAR);lin=np.asarray(linim,dtype=np.float32);av=lin.copy()
   p={'source_box':list(box),'input_rgb':str(ip),'input_rgb_sha256':sha(ip),'input_alpha':str(ap),'input_alpha_sha256':sha(ap),'rgb_native':str(npth),'rgb_native_sha256':sha(npth)}
   if weight:
    an=infer_rgb(model,alpha.convert('RGB')).convert('L');apasses+=1;anp=O/f'{tag}-alpha4x.png';an.save(anp);p.update(alpha_native=str(anp),alpha_native_sha256=sha(anp))
    av=weight*np.asarray(an.resize(wh,Image.Resampling.LANCZOS),dtype=np.float32)+(1-weight)*lin
    for _ in range(5):
     av=np.clip(av*(np.asarray(part.getchannel('A')).mean()/max(av.mean(),1e-6)),0,255);av[lin==0]=0;av[lin==255]=255
   a=np.asarray(part,dtype=np.float32);oa=a[:,:,3:4]/255.;wa=av[:,:,None]/255.;offset=(a[:,:,:3]*oa).sum((0,1))/oa.sum()-(rgb*wa).sum((0,1))/wa.sum()
   im=Image.fromarray(np.rint(np.clip(rgb+offset,0,255)).astype('uint8'));im.putalpha(Image.fromarray(np.rint(av).astype('uint8')));out.paste(im,(x0*8,y0*8));ref.paste(linim,(x0*8,y0*8));p['weighted_mean_rgb_offset']=offset.tolist();parts.append(p)
  assert (coverage==1).all();op=O/f'{gid}-{mid}-8x.png';rp=O/f'{gid}-{mid}-source-alpha8x.png';out.save(op);ref.save(rp)
  a=np.asarray(out.getchannel('A'));lin=np.asarray(ref);orig=np.asarray(src.getchannel('A'));down=np.asarray(out.getchannel('A').resize(src.size,Image.Resampling.LANCZOS));assert np.all(a[lin==0]==0) and np.all(a[lin==255]==255)
  metrics={'mass_ratio':float(a.mean()/orig.mean()),'source_ge16_reduced_below8':int(((orig>=16)&(down<8)).sum()),'source_ge8_reduced_below4':int(((orig>=8)&(down<4)).sum()),'source_bilinear_byte_exact':bool(np.array_equal(a,lin)),'threshold_ious':{}}
  for threshold in [8,16,32,64,128,192,240]:
   gt=orig>=threshold;pred=down>=threshold;union=(gt|pred).sum();metrics['threshold_ious'][str(threshold)]=float((gt&pred).sum()/union) if union else 1.
  row={**{k:v[k] for k in ['group_id','representative','source','source_ptm','source_ptm_sha256','source_rgba_sha256','classification']},'id':gid+'-'+mid,'model_id':mid,'model':rec,'input_gaussian_sigma_source_px':sigma,'alpha_neural_weight':weight,'alpha_method':'source bilinear only' if not weight else '0.2 neural +0.8 source bilinear; five per-panel mean restorations and zero/255 support constraints','parts':parts,'actual_rgb_passes':rgbpasses,'actual_alpha_passes':apasses,'actual_local_inference_passes':rgbpasses+apasses,'reference_alpha':str(rp),'reference_alpha_sha256':sha(rp),'output':str(op),'output_sha256':sha(op),'output_size':list(out.size),'alpha_metrics':metrics,'seconds':time.monotonic()-t,'visual_review':'pending','runtime_verified':False,'release_eligible':False}
  rep['files'].append(row);done[(gid,mid)]=row;save();print('INFERRED',gid,mid,rgbpasses+apasses,flush=True)
 del model;gc.collect();torch.cuda.empty_cache()
for start in range(0,len(ids),3):
 batch=ids[start:start+3];canvas=Image.new('RGB',(1536,len(batch)*570),'#26333f');d=ImageDraw.Draw(canvas)
 for i,gid in enumerate(batch):
  src=Image.open(rows[gid]['source']).convert('RGBA');ims=[src]+[Image.open(done[(gid,m)]['output']).convert('RGBA') for m in ['wdn','photo']]
  sc=min(485/src.width,248/src.height,8);wh=(round(src.width*sc),round(src.height*sc))
  for j,(im,label) in enumerate(zip(ims,['원본 · 단순 확대','로컬 WDN','로컬 Photo'])):
   x=j*512;y=i*570;d.text((x+8,y+6),gid+' '+label,font=font,fill='white')
   for bi,bg in enumerate(['#242b33','#d4d5d7']):canvas.paste(composite(im,wh,bg,Image.Resampling.NEAREST if j==0 else Image.Resampling.LANCZOS),(x+10,y+35+bi*264))
 path=P/f'review-{start//3+1:02d}.png';canvas.save(path);rep['pages'].append({'path':str(path),'sha256':sha(path),'group_ids':batch,'review_status':'pending'})
rep.update(actual_rgb_passes=sum(v['actual_rgb_passes'] for v in rep['files']),actual_alpha_passes=sum(v['actual_alpha_passes'] for v in rep['files']),actual_local_inference_passes=sum(v['actual_local_inference_passes'] for v in rep['files']))
save();print(json.dumps({'originals':len(ids),'outputs':len(rep['files']),'passes':rep['actual_local_inference_passes'],'pages':len(rep['pages'])}),flush=True)
