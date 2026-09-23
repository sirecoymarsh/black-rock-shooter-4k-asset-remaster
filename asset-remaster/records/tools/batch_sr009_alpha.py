"""Region 3/4 alpha-aware local SR with recorded, isolated source panels."""
import sys,json,time,gc
from pathlib import Path
import numpy as np,torch
from scipy.ndimage import gaussian_filter,distance_transform_edt
from PIL import Image,ImageDraw,ImageFont
import local_sr as sr
sys.stdout.reconfigure(encoding='utf8');torch.set_num_threads(4)
R=Path(__file__).resolve().parents[1];O=R/'workspace/local-sr/stage0304-alpha-v1';Q=R/'qa/local_sr009_inference.json'
if (R/'qa/local_sr009_review.json').exists():raise SystemExit('Reviewed batch; use a new version.')
O.mkdir(parents=True,exist_ok=True)
cat=json.loads((R/'qa/battle_sr_catalog.json').read_text('utf8'));groups={g['group_id']:g for g in cat['groups']}
ids=[f'BM{i:03d}' for i in [132,135,136,137,138,139,140,141,142,143,145,146,147,153,154,155,171,172,183,195,196,197,198,199]]
soft={'BM195','BM196','BM197','BM198','BM199'}
split={
 'BM137':[(0,0,64,32),(0,32,32,64),(32,32,64,64)],
 'BM140':[(0,0,128,64),(0,64,128,128)],
 'BM141':[(0,0,128,64),(0,64,128,128)],
 'BM142':[(0,0,64,64),(64,0,128,64)]}
models={m['name']:m for m in json.loads((R/'workspace/local-sr/models/models.json').read_text('utf8'))['records']}
report=json.loads(Q.read_text('utf8')) if Q.exists() else {'schema':'brs-sr009-alpha/v1','group_ids':ids,'device':torch.cuda.get_device_name(0),'torch':torch.__version__,'local_inference':True,'image_upload':False,'files':[],'runtime_verified':False,'release_eligible':False,'panel_basis':'Visible separated rows/quadrants in source; processing separation is not proof of native UV consumers.'}
assert report['group_ids']==ids
done={(r['group_id'],r['model_id']):r for r in report['files']}
def save():Q.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
def prefilter(src,sigma):
 a=np.asarray(src,dtype=np.float32)/255.;alpha=a[:,:,3]
 coverage=gaussian_filter(alpha,sigma,mode='nearest') if sigma else alpha.copy()
 premul=gaussian_filter(a[:,:,:3]*alpha[:,:,None],(sigma,sigma,0),mode='nearest') if sigma else a[:,:,:3]*alpha[:,:,None]
 rgb=premul/np.maximum(coverage[:,:,None],1e-6);vis=coverage>1e-6
 if not vis.all():
  assert vis.any();near=distance_transform_edt(~vis,return_distances=False,return_indices=True);rgb[~vis]=rgb[near[0][~vis],near[1][~vis]]
 return Image.fromarray(np.rint(np.clip(rgb,0,1)*255).astype('uint8')),Image.fromarray(np.rint(np.clip(coverage,0,1)*255).astype('uint8'))
for mid,name in [('wdn','realesr-general-wdn-x4v3.pth'),('photo','RealESRGAN_x4plus.pth')]:
 rec=models[name];model=sr.load_model(Path(rec['path']),rec['sha256'])
 for gid in ids:
  g=groups[gid];src=Image.open(g['representative']['png']).convert('RGBA');assert sr.sha(src.tobytes())==g['rgba_sha256'] and src.size==(g['width'],g['height'])
  if (gid,mid) in done:
   row=done[(gid,mid)];assert row['source_rgba_sha256']==g['rgba_sha256'] and sr.sha(Path(row['output']).read_bytes())==row['output_sha256'];continue
  assert not g.get('local_sr_attempted'),gid
  opaque=src.getchannel('A').getextrema()==(255,255);sigma=(.75 if mid=='wdn' else 1.) if gid in soft else .35
  weight=.2 if gid in soft else .35;boxes=split.get(gid,[(0,0,src.width,src.height)])
  cover=np.zeros((src.height,src.width),np.uint8)
  for x0,y0,x1,y1 in boxes:cover[y0:y1,x0:x1]+=1
  assert (cover==1).all(),'Source boxes must partition the complete image exactly once.'
  t=time.monotonic();out=Image.new('RGBA',(src.width*8,src.height*8));reference=Image.new('L',out.size);parts=[];passes=0
  for pi,box in enumerate(boxes):
   part=src.crop(box);inp,alpha=prefilter(part,sigma);tag=f'{gid}-{mid}-p{pi}';ip=O/f'{tag}-rgb-input.png';ap=O/f'{tag}-alpha-input.png';inp.save(ip);alpha.save(ap)
   native=sr.infer_rgb(model,inp);passes+=1;npth=O/f'{tag}-rgb4x.png';native.save(npth);wh=(part.width*8,part.height*8);rgb=np.asarray(native.resize(wh,Image.Resampling.LANCZOS),dtype=np.float32)
   linim=part.getchannel('A').resize(wh,Image.Resampling.BILINEAR);lin=np.asarray(linim,dtype=np.float32)
   p={'source_box':list(box),'input_rgb':str(ip),'input_rgb_sha256':sr.sha(ip.read_bytes()),'input_alpha':str(ap),'input_alpha_sha256':sr.sha(ap.read_bytes()),'rgb_native':str(npth),'rgb_native_sha256':sr.sha(npth.read_bytes())}
   if opaque:av=np.full((wh[1],wh[0]),255,np.float32)
   else:
    an=sr.infer_rgb(model,alpha.convert('RGB')).convert('L');passes+=1;anp=O/f'{tag}-alpha4x.png';an.save(anp);p.update({'alpha_native':str(anp),'alpha_native_sha256':sr.sha(anp.read_bytes())})
    av=weight*np.asarray(an.resize(wh,Image.Resampling.LANCZOS),dtype=np.float32)+(1-weight)*lin
    for _ in range(5):
     av=np.clip(av*(np.asarray(part.getchannel('A')).mean()/max(av.mean(),1e-6)),0,255);av[lin==0]=0;av[lin==255]=255
   original=np.asarray(part,dtype=np.float32);oa=original[:,:,3:4]/255.;wa=av[:,:,None]/255.;assert oa.sum()>0 and wa.sum()>0
   offset=(original[:,:,:3]*oa).sum((0,1))/oa.sum()-(rgb*wa).sum((0,1))/wa.sum();im=Image.fromarray(np.rint(np.clip(rgb+offset,0,255)).astype('uint8'));im.putalpha(Image.fromarray(np.rint(av).astype('uint8')))
   out.paste(im,(box[0]*8,box[1]*8));reference.paste(linim,(box[0]*8,box[1]*8));p['weighted_mean_rgb_offset']=offset.tolist();parts.append(p)
  p=O/f'{gid}-{mid}-rgba8x.png';out.save(p);a=np.asarray(out.getchannel('A'));lin=np.asarray(reference);assert not np.any(a[lin==0]);assert np.all(a[lin==255]==255)
  refp=O/f'{gid}-{mid}-panel-bilinear-alpha.png';reference.save(refp);orig=np.asarray(src.getchannel('A'));down=np.asarray(out.getchannel('A').resize(src.size,Image.Resampling.LANCZOS));gt=orig>=128;pred=down>=128;union=(gt|pred).sum()
  row={'group_id':gid,'source':g['representative']['png'],'source_rgba_sha256':g['rgba_sha256'],'model_id':mid,'model':rec,'prefilter_sigma':sigma,'parts':parts,'new_neural_passes':passes,'native_neural_scale':4,'post_scale':'Lanczos2x','precision':'float32','alpha_method':'Opaque255 exact' if opaque else f'{weight:.2f} neural alpha + {1-weight:.2f} source bilinear, per-panel mean restored and zero/255 support constrained','reference_alpha':str(refp),'reference_alpha_sha256':sr.sha(refp.read_bytes()),'output':str(p),'output_sha256':sr.sha(p.read_bytes()),'output_size':list(out.size),'seconds':time.monotonic()-t,'alpha_metrics':{'mass_ratio':float(a.mean()/orig.mean()),'source_threshold128_iou':float((gt&pred).sum()/union) if union else 1.,'source_ge16_reduced_below8':int(((orig>=16)&(down<8)).sum()),'outside_panel_bilinear_support':0},'visual_review':'pending','runtime_verified':False,'release_eligible':False}
  report['files'].append(row);done[(gid,mid)]=row;save();print('INFERRED',gid,mid,'passes',passes,flush=True)
 del model;gc.collect();torch.cuda.empty_cache()
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18);pages=[];directory=R/'outputs/sr009-review';directory.mkdir(exist_ok=True)
for start in range(0,len(ids),3):
 batch=ids[start:start+3];sheet=Image.new('RGB',(1536,len(batch)*410+45),'#293440');d=ImageDraw.Draw(sheet)
 for j,t in enumerate(['원본 단순 확대','로컬 WDN','로컬 Photo']):d.text((j*512+10,6),t,font=font,fill='white')
 for i,gid in enumerate(batch):
  src=Image.open(groups[gid]['representative']['png']).convert('RGBA');ims=[src]+[Image.open(done[(gid,mid)]['output']).convert('RGBA') for mid in ['wdn','photo']];s=min(488/src.width,345/src.height,8);wh=(round(src.width*s),round(src.height*s))
  for j,im in enumerate(ims):
   x=j*512+10;y=45+i*410;d.text((x,y),gid,font=font,fill='white');v=im.resize(wh,Image.Resampling.NEAREST if j==0 else Image.Resampling.LANCZOS);bg=Image.new('RGB',wh,'#72808b');bg.paste(v,(0,0),v);sheet.paste(bg,(x,y+30))
 p=directory/f'review-{start//3+1:02d}.png';sheet.save(p);pages.append(str(p))
report['comparison_sheets']=pages;report['new_neural_passes']=sum(r['new_neural_passes'] for r in report['files']);save();print(json.dumps({'originals':len(ids),'outputs':len(report['files']),'passes':report['new_neural_passes'],'pages':len(pages)}),flush=True)
