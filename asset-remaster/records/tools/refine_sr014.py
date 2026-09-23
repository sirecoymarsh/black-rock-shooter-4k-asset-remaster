"""Second source-driven reconstruction after rejecting rounded holes and flat pasted floor."""
import json,hashlib,math
from pathlib import Path
import numpy as np,cv2
from scipy.ndimage import gaussian_filter,distance_transform_edt
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];O=R/'workspace/manual-redraw/sr014-v2';O.mkdir(parents=True,exist_ok=True);Q=R/'qa/local_sr014_refinement.json'
if Q.exists():raise SystemExit('Existing revision')
old=json.loads((R/'qa/local_sr014_reconstruction.json').read_text('utf8'))
def sha(b):return hashlib.sha256(b).hexdigest()
def save(im,name):
 p=O/name;im.save(p);return str(p),sha(p.read_bytes())
def shade(v,mask,sigma):
 near=distance_transform_edt(~mask,return_distances=False,return_indices=True);filled=v[near[0],near[1]];return gaussian_filter(filled,(sigma,sigma,0),mode='nearest')
files=[]
r=old['files'][0];src=Image.open(r['source']).convert('RGBA');a=np.asarray(src)[:,:,:3].astype(float);parent=Image.open(r['parent']).convert('RGBA')
for name,radius in [('angular',.47),('fine',.37)]:
 out=np.asarray(parent).copy();panels=[];paths=[]
 for p in r['panels']:
  x0,y0,x1,y1=p['box'];holes=np.asarray(Image.open(p['source_hole_mask']))>0;v=a[y0:y1,x0:x1];nr,lab,stats,centers=cv2.connectedComponentsWithStats(holes.astype('uint8'),8)
  mh=Image.new('L',((x1-x0)*32,(y1-y0)*32));draw=ImageDraw.Draw(mh);polygons=[]
  for k in range(1,nr):
   ys,xs=np.nonzero(lab==k);pts=[]
   for x,y in zip(xs,ys):pts.extend([(x+.5-radius,y+.5),(x+.5,y+.5-radius),(x+.5+radius,y+.5),(x+.5,y+.5+radius)])
   poly=cv2.convexHull(np.array(pts,dtype='float32')).reshape(-1,2);draw.polygon([tuple(z*32 for z in q) for q in poly],fill=255)
   polygons.append({'component_id':k,'source_pixels':int((lab==k).sum()),'local_vertices':poly.tolist()})
   path='M '+' L '.join(f'{x+x0:.4f},{y+y0:.4f}' for x,y in poly)+' Z';paths.append(f'<path d="{path}" fill="#202427"/>')
  mh=mh.resize(((x1-x0)*8,(y1-y0)*8),Image.Resampling.LANCZOS);cov=np.asarray(mh,dtype=float)/255
  light=cv2.resize(shade(v,~holes,.35),None,fx=8,fy=8,interpolation=cv2.INTER_CUBIC);dark=cv2.resize(shade(v,holes,.5),None,fx=8,fy=8,interpolation=cv2.INTER_CUBIC)
  # Original upper/lower illumination and bright interwoven crossings are kept in each separate material field.
  result=light*(1-cov[:,:,None])+dark*cov[:,:,None]
  out[y0*8:y1*8,x0*8:x1*8,:3]=np.rint(np.clip(result,0,255)).astype('uint8')
  cp,ch=save(mh,f'BM175-{name}-holes-{y0}-coverage8x.png');actual=cv2.connectedComponents((cov>=.5).astype('uint8'),8)[0]-1
  centers_visible=[]
  for poly in polygons:
   ys,xs=np.nonzero(lab==poly['component_id']);centers_visible.append(bool(any(cov[int(y*8+4),int(x*8+4)]>=.5 for x,y in zip(xs,ys))))
  panels.append({**p,'coverage':cp,'coverage_sha256':ch,'source_components':nr-1,'output_components':actual,'all_source_components_represented':all(centers_visible),'polygons':polygons})
 im=Image.fromarray(out);op,oh=save(im,f'BM175-{name}-8x.png');vp=O/f'BM175-{name}-hole-geometry.svg';vp.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="256" height="512" viewBox="0 0 32 64">'+''.join(paths)+'</svg>','utf8')
 files.append({**{k:r[k] for k in ['group_id','source','source_rgba_sha256','parent','parent_sha256','mask','mask_sha256']},'id':'BM175-'+name,'output':op,'output_sha256':oh,'output_size':list(im.size),'vector_layout':str(vp),'vector_layout_sha256':sha(vp.read_bytes()),'panels':panels,'method':'Source component masks converted to compact angular polygons; independent source metal and hole shading. Codex-directed computational tracing, with prior Photo outer frame.','new_neural_passes':0,'new_generative_calls':0,'visual_review':'pending','runtime_verified':False,'release_eligible':False})

r=next(r for r in old['files'] if r['id']=='BM201-cells-0.6');src=Image.open(r['source']).convert('RGBA');a=np.asarray(src)[:,:,:3].astype(float);parent=Image.open(r['parent']).convert('RGBA');pa=np.asarray(parent);W,H=parent.size
base=np.asarray(Image.open(r['output']))[:,:,:3].astype(float)
# Remove broad invented folds from the checker interior while retaining only fine local surface variation.
detail=pa[:,:,:3].astype(float)-gaussian_filter(pa[:,:,:3].astype(float),(2.4,2.4,0),mode='nearest')
for name,weight in [('material',.30),('quiet',.12)]:
 out=pa.copy();union=np.zeros((H,W),float);infos=[]
 for patch in r['patches']:
  mask=np.asarray(Image.open(patch['mask']))>0;dist=distance_transform_edt(mask)
  highdist=cv2.resize(dist.astype('float32'),(W,H),interpolation=cv2.INTER_LINEAR)
  clip=np.clip((highdist-1.6)/1.4,0,1)
  # Keep the existing source-observed large crack's immediate edge treatment, not the newly drawn speckled crack mask.
  crease=np.asarray(Image.open(patch['crack_mask']))>0
  keep=distance_transform_edt(~crease)
  nearcrack=cv2.resize(keep.astype('float32'),(W,H),interpolation=cv2.INTER_LINEAR)
  clip*=np.clip((nearcrack-1.2)/1.4,0,1)
  paint=base.copy();covered=np.zeros((H,W),bool)
  for cell in patch['cells']:
   x0,y0,x1,y1=cell['source_bounds'];xa=max(0,round(x0*8));xb=min(W,round(x1*8));ya=max(0,round(y0*8));yb=min(H,round(y1*8))
   med=np.array(cell['median_rgb']);paint[ya:yb,xa:xb]=.6*med+.4*base[ya:yb,xa:xb]+weight*detail[ya:yb,xa:xb]
   covered[ya:yb,xa:xb]=True
  clip*=covered
  out[:,:,:3]=np.rint(np.clip(paint*clip[:,:,None]+out[:,:,:3]*(1-clip[:,:,None]),0,255)).astype('uint8');union=np.maximum(union,clip)
  infos.append({'id':patch['id'],'protected_crack_source_pixels':int(crease.sum()),'full_repaint_output_pixels':int((clip>=1).sum())})
 im=Image.fromarray(out);op,oh=save(im,f'BM201-{name}-8x.png');mp,mhs=save(Image.fromarray(np.rint(union*255).astype('uint8')),f'BM201-{name}-effective-mask8x.png')
 files.append({**{k:r[k] for k in ['group_id','source','source_rgba_sha256','parent','parent_sha256','vector_layout','vector_layout_sha256','patches']},'id':'BM201-'+name,'structure_parent':r['output'],'structure_parent_sha256':r['output_sha256'],'output':op,'output_sha256':oh,'output_size':list(im.size),'mask':mp,'mask_sha256':mhs,'fine_material_weight':weight,'patch_interior_checks':infos,'method':'Source-positioned cells with stable sampled color and restrained local fine material; prior local damage edges retained within narrow source crack/boundary bands.','new_neural_passes':0,'new_generative_calls':0,'visual_review':'pending','runtime_verified':False,'release_eligible':False})
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17);pages=[]
for gid,boxes in [('BM175',[(0,0,32,64),(3,1,29,15)]),('BM201',[(0,0,256,256),(148,20,237,155),(50,20,149,80),(15,105,75,194),(10,195,125,256)])]:
 rows=[r for r in files if r['group_id']==gid];src=Image.open(rows[0]['source']).convert('RGBA');parent=Image.open(rows[0]['parent']).convert('RGBA')
 for k,box in enumerate(boxes):
  w=512 if gid=='BM201' else 300;h=round(w*(box[3]-box[1])/(box[2]-box[0]));cw=w+20;rh=h+50;s=Image.new('RGB',(cw*2,rh*2),'#293440');d=ImageDraw.Draw(s)
  ims=[(src,'원본 단순 확대'),(parent,'기존 로컬 AI')]+[(Image.open(r['output']).convert('RGBA'),r['id']) for r in rows]
  for i,(im,title) in enumerate(ims):
   x=i%2*cw+8;y=i//2*rh+6;d.text((x,y),title,font=font,fill='white');im=im.crop(box if i==0 else tuple(z*8 for z in box)).resize((w,h),Image.Resampling.NEAREST if i==0 else Image.Resampling.LANCZOS);s.paste(im.convert('RGB'),(x,y+30))
  p=R/f'outputs/sr014-v2-{gid}-compare{k}.png';s.save(p);pages.append(str(p))
Q.write_text(json.dumps({'schema':'brs-sr014-refinement/v2','files':files,'comparison_sheets':pages,'new_neural_passes':0,'new_generative_calls':0,'runtime_verified':False,'release_eligible':False,'review_status':'pending'},ensure_ascii=False,indent=2),'utf8')
print(json.dumps({'outputs':4,'mesh_components':[(r['id'],[(p['source_components'],p['output_components'],p['all_source_components_represented']) for p in r['panels']]) for r in files if r['group_id']=='BM175']},ensure_ascii=False))
