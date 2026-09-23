"""Source-anchored geometric planes and traced ornamental curves with local grain."""
import json,hashlib
from pathlib import Path
import numpy as np,cv2
from scipy.ndimage import gaussian_filter,gaussian_filter1d
from scipy.interpolate import PchipInterpolator
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];Q=R/'qa/field_geometry004_trials.json';assert not Q.exists()
O=R/'workspace/local-sr/field-geometry004';V=R/'outputs/field-geometry004';font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
audit=json.loads((R/'qa/field_geometry004_source_audit.json').read_text('utf8'));inference=json.loads((R/'qa/field_sr004_inference.json').read_text('utf8'));files=[];pages=[]
for v in audit['files']:
 gid=v['group_id'];m=next(v for v in inference['files'] if v['id']==gid+'-wdn');s=np.asarray(Image.open(v['source']).convert('RGBA'));p=np.asarray(Image.open(m['output']).convert('RGBA'));h,w=s.shape[:2];base=np.zeros(p.shape[:2]+(3,),np.float32);classes=np.zeros(p.shape[:2],np.uint16);coverage=np.zeros(p.shape[:2],np.uint8);regions=[];vectors=[]
 def region(name,box,mode='surface',sigma=(1.0,.5,0)):
  x0,y0,x1,y1=box;a,b,c,d=[z*8 for z in box];src=s[y0:y1,x0:x1,:3].astype('float32')
  if mode=='surface':material=cv2.resize(gaussian_filter(src,sigma,mode='nearest'),(c-a,d-b),interpolation=cv2.INTER_CUBIC)
  elif mode=='horizontal':
   profile=gaussian_filter1d(np.median(src,axis=1),.5,axis=0,mode='nearest');material=cv2.resize(profile[:,None,:],(c-a,d-b),interpolation=cv2.INTER_LINEAR)
  elif mode=='vertical':
   profile=gaussian_filter1d(np.median(src,axis=1),.75,axis=0,mode='nearest');material=cv2.resize(profile[:,None,:],(c-a,d-b),interpolation=cv2.INTER_LINEAR)
  base[b:d,a:c]=material;classes[b:d,a:c]=len(regions)+1;coverage[b:d,a:c]+=1;regions.append({'name':name,'source_box':box,'mode':mode,'surface_sigma_source':list(sigma) if mode=='surface' else None});vectors.append(f'<rect id="r{len(regions)}" x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" fill="none" stroke="red" stroke-width=".05"/>')
 if gid=='FM0337':
  region('continuous left bright face',[0,0,6,64]);region('continuous left shadow face',[6,0,9,64])
  region('upper recess',[9,0,128,4],'horizontal')
  starts=v['bright_vertical_source_spans'][1:];cursor=9
  for x0,x1 in starts:
   region('recess',[cursor,4,x0,46]);region('bright upright',[x0,4,x1,46]);cursor=x1
  region('right recess',[cursor,4,128,46])
  for y0,y1 in v['horizontal_bands_y'][1:]:region('lower horizontal face',[9,y0,128,y1],'horizontal')
  grain_gain=.45;grain_bound=4;extra={'declared_bright_spans':v['bright_vertical_source_spans'],'scope':'Source straight face partitions; softly filtered original low-frequency shading and bounded local WDN fine grain. Weathering is not claimed pixel-identical.'}
 elif gid=='FM0346':
  region('lintel profile',[0,0,32,16],'horizontal')
  cursor=0
  for x0,x1 in v['bright_vertical_spans']:
   if cursor<x0:region('shaded flute face',[cursor,16,x0,32],'vertical')
   region('bright flute face',[x0,16,x1,32],'vertical');cursor=x1
  grain_gain=.35;grain_bound=2;extra={'declared_bright_spans':v['bright_vertical_spans'],'repeat_period_source':6,'scope':'Six bright bands at period6 and pale shaded faces. Does not equate them with six independent physical columns.'}
 else:
  region('upper molding light',[0,0,64,1],'horizontal');region('upper molding face',[0,1,64,2],'horizontal')
  for x0,x1 in [(0,1),(31,32),(63,64)]:region('upper vertical divider',[x0,2,x1,15],'vertical')
  for x0,x1 in [(1,31),(32,63)]:region('upper panel',[x0,2,x1,15],'surface',(1.0,1.0,0))
  region('middle molding light',[0,15,64,16],'horizontal');region('middle molding shadow',[0,16,64,17],'horizontal');region('lower edge',[0,31,64,32],'horizontal');region('ornament background',[0,17,64,31],'horizontal')
  # Authored curve centers follow original left/right arm samples; they are not
  # unconstrained model edges or an assertion that the source contains full ellipses.
  ys=np.array([17,18,19,20,21,22,23.5,25,26,27,28,29,30.5],float)
  xs=np.array([1.0,2.6,4.0,5.1,6.2,7.25,8.5,9.75,10.9,12.0,13.25,14.2,15.7],float)
  yy=(np.arange(17*8,31*8)+.5)/8;xx=(np.arange(w*8)+.5)/8
  a=PchipInterpolator(ys,xs,extrapolate=True)(yy);dist=np.full((len(yy),w*8),999.,np.float32);curves=[]
  for k in range(4):
   for sense in [1,-1]:
    cx=(a if sense==1 else 17-a)+15*k;dist=np.minimum(dist,np.abs(xx[None,:]-cx[:,None]));curves.append({'repeat':k,'direction':sense,'source_y':ys.tolist(),'source_x':((xs if sense==1 else 17-xs)+15*k).tolist()})
    pts=' '.join(f'{x:.4f},{y:.4f}' for x,y in zip(cx,yy));vectors.append(f'<polyline points="{pts}" fill="none" stroke="lime" stroke-width="1.5"/>')
  lum=s[17:31,:,:3].mean(2);highlight=np.array([s[y,:,:3][np.argsort(lum[y-17])[-8:]].mean(0) for y in range(17,31)],np.float32)
  high=cv2.resize(highlight[:,None,:],(w*8,len(yy)),interpolation=cv2.INTER_LINEAR)
  weight=np.exp(-.5*(dist/.75)**2)[:,:,None];base[136:248]=base[136:248]*(1-weight)+high*weight
  extra={'curve_centers':curves,'curve_width_sigma_source':.75,'curve_highlight_profile_rgb':highlight.tolist(),'source_interpretation':'Four broad waists made by eight crossing curved arms. Exact trace is an authored interpolation of visible source centers; full ellipses or recovered native detail are not claimed.'};grain_gain=.20;grain_bound=1.5
 assert np.all(coverage==1)
 grain=p[:,:,:3].astype('float32')-gaussian_filter(p[:,:,:3].astype('float32'),(3,3,0),mode='nearest');out=np.empty_like(p);out[:,:,:3]=np.rint(np.clip(base+np.clip(grain*grain_gain,-grain_bound,grain_bound),0,255)).astype('uint8');out[:,:,3]=255
 ident=gid+'-source-planes-local-grain';op=O/(ident+'-8x.png');bp=O/(ident+'-base.npz');mp=O/(ident+'-regions.png');sp=O/(ident+'.svg')
 Image.fromarray(out).save(op);np.savez_compressed(bp,rgb=base);Image.fromarray(classes).save(mp);sp.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}">'+''.join(vectors)+'</svg>','utf8')
 files.append({**{k:v[k] for k in ['group_id','source','source_ptm','source_ptm_sha256','source_rgba_sha256']},'id':ident,'parent':m['output'],'parent_sha256':m['output_sha256'],'parent_model':m['model']['name'],'source_audit_sha256':sha(R/'qa/field_geometry004_source_audit.json'),'output':str(op),'output_sha256':sha(op),'base_planes':str(bp),'base_planes_sha256':sha(bp),'region_classmap':str(mp),'region_classmap_sha256':sha(mp),'vector':str(sp),'vector_sha256':sha(sp),'regions':regions,'grain_sigma_output':3,'grain_gain':grain_gain,'grain_bound':grain_bound,'method':'Authored source-coordinate planes/curves plus source shading and restrained high-frequency material from existing local WDN result. No new neural inference.',**extra,'new_neural_passes':0,'runtime_verified':False,'release_eligible':False,'visual_review':'pending'})
 boxes=[('whole',(0,0,w,h)),('detail',(40,0,72,32) if gid=='FM0337' else ((0,0,32,32) if gid=='FM0346' else (16,0,48,32)))]
 for label,box in boxes:
  cw,ch=(box[2]-box[0])*8,(box[3]-box[1])*8;scale=min(1,640/cw,512/ch) if label=='whole' else 1;sw,sh=round(cw*scale),round(ch*scale);col=max(310,sw+16);can=Image.new('RGB',(col*3,sh+46),'#26333f');d=ImageDraw.Draw(can)
  ims=[Image.fromarray(s).crop(box).resize((cw,ch),Image.Resampling.NEAREST),Image.fromarray(p).crop(tuple(t*8 for t in box)),Image.fromarray(out).crop(tuple(t*8 for t in box))]
  for j,(im,title) in enumerate(zip(ims,['원본 · 단순 확대','로컬 WDN','원본 구조 · 로컬 재질'])):d.text((j*col+6,5),gid+' '+title,font=font,fill='white');can.paste(im.resize((sw,sh),Image.Resampling.NEAREST if j==0 else Image.Resampling.LANCZOS).convert('RGB'),(j*col+6,38))
  pp=V/(gid+'-'+label+'-v1.png');can.save(pp);pages.append({'path':str(pp),'sha256':sha(pp),'source_box':list(box),'review_status':'pending'})
Q.write_text(json.dumps({'schema':'brs-source-repeat-reconstruction/v1','files':files,'pages':pages,'new_neural_passes':0,'external_calls':0,'limits':['Local texture grain is retained only at bounded amplitude; geometry/shading are authored from the source.','Source-face interpretation and visual quality require separate inspection. Region coverage and straight rectangles alone do not prove a good reconstruction.'],'runtime_verified':False,'release_eligible':False},ensure_ascii=False,indent=2),'utf8')
print('Saved3 source-geometry trials and6 whole/detail comparison pages.')
