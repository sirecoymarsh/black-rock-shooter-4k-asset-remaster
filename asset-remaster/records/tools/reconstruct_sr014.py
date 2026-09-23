"""Source-constrained mesh holes and per-cell floor paint; no generative inference."""
import json,hashlib,math
from pathlib import Path
import numpy as np,cv2
from scipy.ndimage import gaussian_filter,distance_transform_edt
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];O=R/'workspace/manual-redraw/sr014';O.mkdir(parents=True,exist_ok=True)
Q=R/'qa/local_sr014_reconstruction.json'
if Q.exists():raise SystemExit('Existing trial. Use a new revision.')
def read(p):return json.loads((R/p).read_text('utf8'))
def sha(b):return hashlib.sha256(b).hexdigest()
def rgb(p):return Image.open(p).convert('RGB')
def save(im,name):
 p=O/name;im.save(p);return str(p),sha(p.read_bytes())
def field(a,mask,sigma):
 v=gaussian_filter(a*mask[:,:,None],(sigma,sigma,0),mode='nearest')/np.maximum(gaussian_filter(mask.astype(float),sigma,mode='nearest')[:,:,None],1e-8)
 near=distance_transform_edt(~mask,return_distances=False,return_indices=True)
 v[~mask]=v[near[0][~mask],near[1][~mask]]
 return v
cat=read('qa/battle_sr_catalog.json');groups={g['group_id']:g for g in cat['groups']};files=[]
g=groups['BM175'];src=rgb(g['representative']['png']);a=np.asarray(src,dtype=float);par=next(f for f in read('qa/local_sr008_grid_rework.json')['files'] if f['id']=='BM175-photo');parent=Image.open(par['output']).convert('RGBA')
assert sha(Path(par['output']).read_bytes())==par['output_sha256']
for threshold in [.72,.82]:
 out=np.asarray(parent).copy();mask_all=np.zeros(a.shape[:2],np.uint8);panels=[]
 for box in [(4,2,28,13),(4,34,28,45)]:
  x0,y0,x1,y1=box;v=a[y0:y1,x0:x1];lum=v.mean(2);base=gaussian_filter(lum,(1.1,1.1),mode='reflect');ratio=lum/np.maximum(base,1)
  holes=ratio<threshold;nr,labels,stats,centers=cv2.connectedComponentsWithStats(holes.astype('uint8'),8)
  # Continuous source-derived level set: subpixel curves follow source contrast. No hole locations are invented.
  hi=cv2.resize(ratio,None,fx=8,fy=8,interpolation=cv2.INTER_CUBIC)
  cov=np.clip((threshold-hi)/.10+.5,0,1)
  light=field(v,~holes,1.2);dark=field(v,holes,1.1)
  li=cv2.resize(light,None,fx=8,fy=8,interpolation=cv2.INTER_CUBIC);da=cv2.resize(dark,None,fx=8,fy=8,interpolation=cv2.INTER_CUBIC)
  result=li*(1-cov[:,:,None])+da*cov[:,:,None]
  out[y0*8:y1*8,x0*8:x1*8,:3]=np.rint(np.clip(result,0,255)).astype('uint8');mask_all[y0:y1,x0:x1]=255
  hs=save(Image.fromarray(holes.astype('uint8')*255),f'BM175-{threshold:.2f}-holes-{y0}.png')
  hh=save(Image.fromarray(np.rint(cov*255).astype('uint8')),f'BM175-{threshold:.2f}-coverage-{y0}.png')
  highcc=cv2.connectedComponentsWithStats((cov>=.5).astype('uint8'),8)
  sample=np.asarray(Image.fromarray((cov*255).astype('uint8')).resize((x1-x0,y1-y0),Image.Resampling.NEAREST))>=128
  panels.append({'box':box,'threshold':threshold,'source_hole_mask':hs[0],'source_hole_mask_sha256':hs[1],'coverage':hh[0],'coverage_sha256':hh[1],'source_components':nr-1,'output_components':highcc[0]-1,'source_sample_class_mismatches':int((sample!=holes).sum()),'source_component_centroids':centers[1:].tolist()})
 im=Image.fromarray(out);op,oh=save(im,f'BM175-holes-{threshold:.2f}-8x.png');mp,mh=save(Image.fromarray(mask_all),'BM175-panel-mask.png')
 files.append({'id':f'BM175-holes-{threshold:.2f}','group_id':'BM175','source':g['representative']['png'],'source_rgba_sha256':g['rgba_sha256'],'parent':par['output'],'parent_sha256':par['output_sha256'],'output':op,'output_sha256':oh,'output_size':list(im.size),'mask':mp,'mask_sha256':mh,'panels':panels,'method':'Codex-directed source contrast contours and independently interpolated hole/mesh shading; local Photo frame retained. This is computational shape reconstruction, not freehand painting.','new_neural_passes':0,'new_generative_calls':0,'visual_review':'pending','runtime_verified':False,'release_eligible':False})

# Observed patch footprints, grid boundaries, and existing cracks are authored separately.
# The polygons are a source-informed tracing, not verified native material/UV boundaries.
patches=[
 {'id':'upper','polygon':[(56,52),(65,41),(76,33),(85,31),(89,22),(104,28),(114,21),(123,29),(139,24),(148,31),(144,39),(127,45),(128,62),(113,75),(105,73),(94,68),(85,77),(71,71),(61,73),(54,64)],'xs':[55.5,65.5,75.8,86.2,96.5,106.5,116.8,126.8,137,147.3],'ys':[20.6,30.8,41,51.1,61.1,71.3,81.5],'cracks':[[(68,45),(77,50),(88,54),(96,60)],[(79,52),(95,52),(104,50),(116,50),(127,58)]]},
 {'id':'right','polygon':[(181,37),(191,33),(196,30),(209,26),(219,24),(225,34),(228,45),(229,62),(223,75),(225,85),(218,96),(211,100),(210,108),(215,114),(207,125),(204,130),(188,134),(184,143),(164,148),(153,146),(154,133),(153,117),(154,103),(154,91),(164,81),(166,72),(176,63),(177,54),(175,48)],'xs':[153.5,163.6,173.8,184.1,194.4,204.6,214.8,225,235.2],'ys':[25.8,36,46.2,56.4,66.6,76.8,87,97.2,107.4,117.6,127.8,138,148.2],'cracks':[[(183,74),(190,82),(194,89),(198,96),(196,107),(199,117),(195,129)],[(198,97),(206,94),(215,91),(223,89)]]},
 {'id':'left','polygon':[(14,130),(23,119),(36,119),(46,112),(54,105),(63,103),(69,115),(68,122),(59,132),(64,135),(67,146),(62,151),(68,155),(65,164),(64,173),(54,175),(50,183),(38,182),(30,190),(28,183),(18,185),(22,176),(26,167),(29,160),(24,154),(21,145)],'xs':[14,24.2,34.4,44.6,54.8,65,75.2],'ys':[102,112.2,122.4,132.6,142.8,153,163.2,173.4,183.6,193.8],'cracks':[[(27,163),(37,157),(47,153),(50,149),(50,140),(55,132),(60,127),(68,122)]]},
 {'id':'bottom','polygon':[(18,216),(38,217),(48,222),(58,216),(76,217),(82,210),(85,201),(90,196),(103,199),(108,197),(117,205),(119,213),(118,221),(119,231),(115,236),(111,238),(110,245),(95,246),(86,242),(80,245),(76,250),(61,254),(51,250),(39,252),(35,242),(24,241),(23,233)],'xs':[14.5,24.7,34.9,45.1,55.3,65.5,75.7,85.9,96.1,106.3,116.5,126.7],'ys':[194.5,204.7,214.9,225.1,235.3,245.5,255.7],'cracks':[[(88,201),(95,207),(99,213),(96,217),(91,224),(98,229),(103,236)]]},
 {'id':'small','polygon':[(208,209),(214,205),(218,207),(224,200),(232,206),(235,214),(234,225),(238,231),(230,238),(225,243),(220,241),(216,248),(211,244),(212,238),(205,233),(205,223)],'xs':[204.5,214.7,224.9,235.1,245.3],'ys':[205.5,215.7,225.9,236.1,246.3],'cracks':[]}
]
g=groups['BM201'];src=rgb(g['representative']['png']);a=np.asarray(src,dtype=float);par=g['superseded_candidates'][-1]['candidate'];parent=Image.open(par['output']).convert('RGBA');W,H=parent.size
assert sha(Path(par['output']).read_bytes())==par['output_sha256']
for sigma in [.6,1.1]:
 out=np.asarray(parent).copy();mask_union=np.zeros((H,W),float);infos=[];vectors=[]
 for patch in patches:
  mask=Image.new('L',src.size);ImageDraw.Draw(mask).polygon(patch['polygon'],fill=255);mask=np.asarray(mask)>0
  # Use signed distance for a narrow clipping edge, and keep all original cracks as their own layer.
  dist=distance_transform_edt(mask)-distance_transform_edt(~mask)
  clip=np.clip(cv2.resize(dist.astype('float32'),(W,H),interpolation=cv2.INTER_LINEAR)/.8+.5,0,1)
  crease_roi=Image.new('L',src.size);cd=ImageDraw.Draw(crease_roi)
  for line in patch['cracks']:cd.line(line,fill=255,width=6)
  crease=(np.asarray(crease_roi)>0)&mask&(a[:,:,0]<=34)
  cratio=cv2.resize(crease.astype('float32'),(W,H),interpolation=cv2.INTER_CUBIC)
  ccov=np.clip((cratio-.4)*5+.5,0,1)
  panel=np.zeros((H,W,3),float);covered=np.zeros((H,W),bool);cells=[]
  for j,(y0,y1) in enumerate(zip(patch['ys'],patch['ys'][1:])):
   for i,(x0,x1) in enumerate(zip(patch['xs'],patch['xs'][1:])):
    xa=max(0,math.ceil(x0-.5));xb=min(src.width,math.ceil(x1-.5));ya=max(0,math.ceil(y0-.5));yb=min(src.height,math.ceil(y1-.5))
    cm=np.zeros(mask.shape,bool);cm[ya:yb,xa:xb]=True;cm&=mask&~crease
    if cm.sum()<3:continue
    # Color is measured from this one source cell only; smoothing never crosses into the opposite checker cell.
    inside=cm.copy();inside[ya,:]=False;inside[:,xa]=False;inside[max(ya,yb-1),:]=False;inside[:,max(xa,xb-1)]=False
    if inside.sum()<3:inside=cm
    nearest=distance_transform_edt(~inside,return_distances=False,return_indices=True)
    fill=a[nearest[0],nearest[1]];smooth=gaussian_filter(fill,(sigma,sigma,0),mode='nearest')
    hx0=max(0,round(x0*8));hx1=min(W,round(x1*8));hy0=max(0,round(y0*8));hy1=min(H,round(y1*8))
    sy,sx=np.indices((hy1-hy0,hx1-hx0),dtype=np.float32);sx=(sx+hx0+.5)/8-.5;sy=(sy+hy0+.5)/8-.5
    vals=cv2.remap(smooth.astype('float32'),sx,sy,cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
    panel[hy0:hy1,hx0:hx1]=vals;covered[hy0:hy1,hx0:hx1]=True
    med=np.median(a[inside],axis=0);cells.append({'column':i,'row':j,'source_bounds':[x0,y0,x1,y1],'source_samples':int(inside.sum()),'median_rgb':med.tolist()})
    vectors.append(f'<rect x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" fill="rgb({int(med[0])},{int(med[1])},{int(med[2])})"/>')
  crgb=cv2.resize(a,(W,H),interpolation=cv2.INTER_CUBIC)
  panel=panel*(1-ccov[:,:,None])+crgb*ccov[:,:,None]
  effective=clip*covered;out[:,:,:3]=np.rint(np.clip(panel*effective[:,:,None]+out[:,:,:3]*(1-effective[:,:,None]),0,255)).astype('uint8');mask_union=np.maximum(mask_union,effective)
  mp,mh=save(Image.fromarray(mask.astype('uint8')*255),f'BM201-{patch["id"]}-source-mask.png');cp,ch=save(Image.fromarray(crease.astype('uint8')*255),f'BM201-{patch["id"]}-source-cracks.png')
  infos.append({**patch,'mask':mp,'mask_sha256':mh,'crack_mask':cp,'crack_mask_sha256':ch,'cells':cells,'crack_source_pixels':int(crease.sum())})
 im=Image.fromarray(out);op,oh=save(im,f'BM201-cells-sigma{sigma:.1f}-8x.png');mp,mh=save(Image.fromarray(np.rint(mask_union*255).astype('uint8')),f'BM201-cells-sigma{sigma:.1f}-mask8x.png')
 svg='<svg xmlns="http://www.w3.org/2000/svg" width="2048" height="2048" viewBox="0 0 256 256">'+''.join(vectors)+'</svg>';vp=O/f'BM201-cells-sigma{sigma:.1f}-layout.svg';vp.write_text(svg,'utf8')
 files.append({'id':f'BM201-cells-{sigma:.1f}','group_id':'BM201','source':g['representative']['png'],'source_rgba_sha256':g['rgba_sha256'],'parent':par['output'],'parent_sha256':par['output_sha256'],'output':op,'output_sha256':oh,'output_size':list(im.size),'mask':mp,'mask_sha256':mh,'vector_layout':str(vp),'vector_layout_sha256':sha(vp.read_bytes()),'patches':infos,'cell_shading_sigma':sigma,'method':'Codex-authored patch footprints and measured checker boundaries; independently sampled cell colors and narrow source crack contours over prior local material. Layout SVG is geometric provenance, not the textured final render.','new_neural_passes':0,'new_generative_calls':0,'visual_review':'pending','runtime_verified':False,'release_eligible':False})
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17);pages=[]
for gid,boxes in [('BM175',[(0,0,32,64),(3,1,29,15)]),('BM201',[(0,0,256,256),(148,20,237,155),(50,20,149,80),(15,105,75,194),(10,195,125,256)])]:
 rows=[r for r in files if r['group_id']==gid];src=Image.open(rows[0]['source']).convert('RGBA');parent=Image.open(rows[0]['parent']).convert('RGBA')
 for k,box in enumerate(boxes):
  w=512 if gid=='BM201' else 300;h=round(w*(box[3]-box[1])/(box[2]-box[0]));cw=w+20;rh=h+50;s=Image.new('RGB',(cw*2,rh*2),'#293440');d=ImageDraw.Draw(s)
  ims=[(src,'원본 단순 확대'),(parent,'기존 로컬 AI')]+[(Image.open(r['output']).convert('RGBA'),r['id']) for r in rows]
  for i,(im,title) in enumerate(ims):
   x=i%2*cw+8;y=i//2*rh+6;d.text((x,y),title,font=font,fill='white');im=im.crop(box if i==0 else tuple(z*8 for z in box)).resize((w,h),Image.Resampling.NEAREST if i==0 else Image.Resampling.LANCZOS);s.paste(im.convert('RGB'),(x,y+30))
  p=R/f'outputs/sr014-{gid}-compare{k}.png';s.save(p);pages.append(str(p))
Q.write_text(json.dumps({'schema':'brs-sr014-reconstruction/v1','files':files,'comparison_sheets':pages,'new_neural_passes':0,'new_generative_calls':0,'runtime_verified':False,'release_eligible':False,'review_status':'pending'},ensure_ascii=False,indent=2),'utf8')
print(json.dumps({'outputs':len(files),'mesh_panels':files[0]['panels'],'floor_cells':[len(p['cells']) for p in files[2]['patches']]},ensure_ascii=False))
