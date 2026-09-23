"""Independently reconstruct source alpha and saved-native postprocessing."""
import json,hashlib
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter,distance_transform_edt,label
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];Q=R/'qa/field_sr003_audit.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check(p,h):assert sha(p)==h,p
def img(p):return Image.open(p).convert('RGBA')
rep=json.loads((R/'qa/field_sr003_inference.json').read_text('utf8'));assert len(rep['files'])==54 and len(rep['pages'])==9
for p,h in rep['source_reviews'].items():check(R/p,h)
check(R/'qa/field_sr_catalog.json',rep['source_catalog_sha256_before'])
old=json.loads((R/'qa/field_sr002_review.json').read_text('utf8'))
for p,h in old['protected_file_hashes'].items():check(R/p,h)
pack=Path(json.loads((R/'qa/local_sr_observed_review_pack_v2.json').read_text('utf8'))['path'])
assert old['pack_hashes']=={str(p.relative_to(pack)):sha(p) for p in pack.rglob('*') if p.is_file()}
checks=[];cached=set()
for v in rep['files']:
 src=img(v['source']);out=img(v['output']);check(v['source_ptm'],v['source_ptm_sha256']);assert hashlib.sha256(src.tobytes()).hexdigest()==v['source_rgba_sha256']
 if v['model']['path'] not in cached:check(v['model']['path'],v['model']['sha256']);cached.add(v['model']['path'])
 for k in ['output','reference_alpha']:check(v[k],v[k+'_sha256'])
 assert out.size==(src.width*8,src.height*8)==tuple(v['output_size'])
 rebuilt=Image.new('RGBA',out.size);ref=Image.new('L',out.size);coverage=np.zeros((src.height,src.width),np.uint8)
 for part in v['parts']:
  box=tuple(part['source_box']);x0,y0,x1,y1=box;coverage[y0:y1,x0:x1]+=1;s=src.crop(box);wh=(s.width*8,s.height*8);sigma=v['input_gaussian_sigma_source_px']
  ar=np.asarray(s,dtype=np.float32)/255.;a=ar[:,:,3];cov=gaussian_filter(a,sigma,mode='nearest');premul=gaussian_filter(ar[:,:,:3]*a[:,:,None],(sigma,sigma,0),mode='nearest');rgb=premul/np.maximum(cov[:,:,None],1e-6);vis=cov>1e-6
  if not vis.all():
   near=distance_transform_edt(~vis,return_distances=False,return_indices=True);rgb[~vis]=rgb[near[0][~vis],near[1][~vis]]
  assert np.array_equal(np.rint(np.clip(rgb,0,1)*255).astype('uint8'),np.asarray(Image.open(part['input_rgb'])))
  assert np.array_equal(np.rint(np.clip(cov,0,1)*255).astype('uint8'),np.asarray(Image.open(part['input_alpha'])))
  for k in ['input_rgb','input_alpha','rgb_native']+(['alpha_native'] if 'alpha_native' in part else []):check(part[k],part[k+'_sha256'])
  n=Image.open(part['rgb_native']).convert('RGB');assert n.size==(s.width*4,s.height*4);rgb=np.asarray(n.resize(wh,Image.Resampling.LANCZOS),dtype=np.float32)
  linim=s.getchannel('A').resize(wh,Image.Resampling.BILINEAR);lin=np.asarray(linim,dtype=np.float32);av=lin.copy();weight=v['alpha_neural_weight']
  if weight:
   an=Image.open(part['alpha_native']).convert('L');assert an.size==n.size;av=weight*np.asarray(an.resize(wh,Image.Resampling.LANCZOS),dtype=np.float32)+(1-weight)*lin
   for _ in range(5):
    av=np.clip(av*(np.asarray(s.getchannel('A')).mean()/max(av.mean(),1e-6)),0,255);av[lin==0]=0;av[lin==255]=255
  original=np.asarray(s,dtype=np.float32);oa=original[:,:,3:4]/255.;wa=av[:,:,None]/255.;offset=(original[:,:,:3]*oa).sum((0,1))/oa.sum()-(rgb*wa).sum((0,1))/wa.sum();assert np.allclose(offset,part['weighted_mean_rgb_offset'],atol=1e-6)
  im=Image.fromarray(np.rint(np.clip(rgb+offset,0,255)).astype('uint8'));im.putalpha(Image.fromarray(np.rint(av).astype('uint8')));rebuilt.paste(im,(x0*8,y0*8));ref.paste(linim,(x0*8,y0*8))
 assert (coverage==1).all() and np.array_equal(np.asarray(rebuilt),np.asarray(out));assert np.array_equal(np.asarray(ref),np.asarray(Image.open(v['reference_alpha'])))
 a=np.asarray(out.getchannel('A'));lin=np.asarray(ref);orig=np.asarray(src.getchannel('A'));down=np.asarray(out.getchannel('A').resize(src.size,Image.Resampling.LANCZOS));assert np.all(a[lin==0]==0) and np.all(a[lin==255]==255)
 metrics={'mass_ratio':float(a.mean()/orig.mean()),'source_ge16_reduced_below8':int(((orig>=16)&(down<8)).sum()),'source_ge8_reduced_below4':int(((orig>=8)&(down<4)).sum()),'source_bilinear_byte_exact':bool(np.array_equal(a,lin)),'threshold_ious':{}}
 components={}
 for t in [8,16,32,64,128,192,240]:
  gt=orig>=t;pred=down>=t;union=(gt|pred).sum();metrics['threshold_ious'][str(t)]=float((gt&pred).sum()/union) if union else 1.;components[str(t)]=[int(label(gt,np.ones((3,3)))[1]),int(label(pred,np.ones((3,3)))[1])]
 assert metrics==v['alpha_metrics'];checks.append({'id':v['id'],'source_ptm_rgba_model_input_native_output_hashes_verified':True,'inputs_reproduced_exact':True,'native4x_final8x_verified':True,'whole_output_postprocessing_reproduced_exact':True,'panel_partition_exact':True,'source_bilinear_alpha_reproduced_exact':True,'zero255_support_verified':True,'alpha_metrics':metrics,'source_and_reduced_output_components':components})
 assert v['actual_rgb_passes']==len(v['parts']) and v['actual_alpha_passes']==sum('alpha_native' in p for p in v['parts'])
for p in rep['pages']:check(p['path'],p['sha256'])
boxes={29:(28,0,56,28),87:(0,0,64,64),113:(0,0,32,32),123:(0,0,32,64),145:(44,0,78,54),157:(8,0,56,64),164:(0,0,64,32),254:(0,0,64,64),255:(64,0,128,64),263:(0,0,64,64),264:(128,0,192,64),272:(240,8,304,72)}
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17);pages=[]
for number,box in boxes.items():
 gid=f'FM{number:04d}';vs=[v for v in rep['files'] if v['group_id']==gid];src=img(vs[0]['source']);ims=[src.crop(box).resize(((box[2]-box[0])*8,(box[3]-box[1])*8),Image.Resampling.NEAREST)]+[img(next(v for v in vs if v['model_id']==mid)['output']).crop(tuple(x*8 for x in box)) for mid in ['wdn','photo']]
 w,h=ims[0].size;cw=max(w+16,250);canvas=Image.new('RGB',(cw*3,2*(h+22)+40),'#27323b');d=ImageDraw.Draw(canvas)
 for j,(im,name) in enumerate(zip(ims,['원본 · 단순 확대','로컬 WDN','로컬 Photo'])):
  x=j*cw;d.text((x+6,6),gid+' '+name,font=font,fill='white')
  for k,bg in enumerate(['#242b33','#d4d5d7']):
   matte=Image.new('RGB',im.size,bg);matte.paste(im,(0,0),im);canvas.paste(matte,(x+6,38+k*(h+22)))
 p=R/f'outputs/field-sr003/detail-{gid}.png';canvas.save(p);pages.append({'group_id':gid,'source_box':list(box),'path':str(p),'sha256':sha(p),'display':'native output8x and source nearest8x; two mattes','review_status':'pending'})
result={'schema':'brs-field-alpha-audit/v1','batch':'FIELD-SR-003','checked_outputs':checks,'actual_rgb_passes':sum(v['actual_rgb_passes'] for v in rep['files']),'actual_alpha_passes':sum(v['actual_alpha_passes'] for v in rep['files']),'actual_local_inference_passes':sum(v['actual_local_inference_passes'] for v in rep['files']),'protected_file_hashes':old['protected_file_hashes'],'pack_hashes':old['pack_hashes'],'detail_pages':pages,'limits':['Alpha component counts at thresholds are diagnostics, not proof of topology, UV consumers or correct runtime alpha test.','Source-bilinear-alpha-only lanes do not claim neural silhouette reconstruction.','All output reproduction checks verify saved-native postprocessing, not rerun determinism or true recovered high-resolution detail.'],'runtime_verified':False,'release_eligible':False}
Q.write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf8')
print(json.dumps({'outputs_verified':len(checks),'passes':result['actual_local_inference_passes'],'weak_alpha_losses':[v['id'] for v in checks if v['alpha_metrics']['source_ge16_reduced_below8'] or v['alpha_metrics']['source_ge8_reduced_below4']],'source_alpha_exact_outputs':sum(v['alpha_metrics']['source_bilinear_byte_exact'] for v in checks),'details':len(pages)}))
