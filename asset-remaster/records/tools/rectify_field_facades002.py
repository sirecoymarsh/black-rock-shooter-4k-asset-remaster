"""Rectify existing local material using source boundary positions; no new inference."""
import hashlib,json
from pathlib import Path
import numpy as np,cv2
from scipy.ndimage import gaussian_filter,gaussian_filter1d
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];O=R/'workspace/local-sr/field-geometry002';V=R/'outputs/field-geometry002';Q=R/'qa/field_geometry002_rectification.json';assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
old=json.loads((R/'qa/field_geometry002_trials.json').read_text('utf8'));files=[];pages=[];font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17)
for v in old['files']:
 gid=v['group_id'];s=Image.open(v['source']).convert('RGBA');p=np.asarray(Image.open(v['parent']).convert('RGBA'));h,w=p.shape[:2];yy,xx=np.mgrid[:h,:w].astype('float32');mx=xx.copy();lum=gaussian_filter(p[:,:,:3].mean(2),(1.5,1.5));dx=np.gradient(lum,axis=1);vertical=[]
 bands=[(9,43),(54,88),(103,128)] if gid=='FM0189' else [(12,46),(57,91),(103,124)]
 for bi,(y0,y1) in enumerate(bands):
  nodes=[(5,-1),(31,1),(33,-1),(61,1)] if gid=='FM0189' and bi<2 else ([(5,-1),(29,1),(37,-1),(61,1)] if bi<2 else [(9,-1),(56,1)])
  target=[0];traces=[np.zeros((y1-y0)*8,np.float32)]
  for x,sign in nodes:
   nominal=x*8-.5;cand=np.arange(int(round(nominal))-6,int(round(nominal))+7)
   raw=cand[(dx[y0*8:y1*8,cand]*sign).argmax(1)].astype('float32')
   # Corners contain horizontal edges; use established interior side edges through the corners.
   margin=16;raw[:margin]=np.median(raw[margin:margin+16]);raw[-margin:]=np.median(raw[-margin-16:-margin])
   trace=gaussian_filter1d(raw,5,mode='nearest');target.append(nominal);traces.append(trace)
   vertical.append({'source_y_range':[y0,y1],'source_boundary_x':x,'gradient_sign':sign,'target_output_x':nominal,'search_radius_output':6,'source_position_authority':'Fixed source-coordinate pane boundary; local gradient chooses material coordinates only.','parent_trace_output_x':trace.tolist(),'displacement_range_output':[float((trace-nominal).min()),float((trace-nominal).max())]})
  target.append(w-1);traces.append(np.full((y1-y0)*8,w-1,np.float32));traces=np.stack(traces)
  assert np.all(np.diff(traces,axis=0)>0)
  for j,y in enumerate(range(y0*8,y1*8)):mx[y]=np.interp(np.arange(w),target,traces[:,j])
 ximage=cv2.remap(p,mx,yy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
 # Target anchors distinguish actual aperture edges, molding peaks/troughs and shutter ridges.
 if gid=='FM0189':
  anchors=[(3.5,'peak'),(9,'fall'),(43,'rise'),(47.5,'trough'),(48.5,'peak'),(54,'fall'),(88,'rise'),(92.5,'trough'),(96.5,'peak'),(98.5,'trough'),(100.5,'peak'),(103,'fall'),(107.5,'peak'),(110.5,'peak'),(113.5,'peak'),(116.5,'peak'),(120.5,'peak'),(123.5,'peak'),(126.5,'peak')]
 else:
  anchors=[(1.5,'peak'),(4.5,'trough'),(6.5,'peak'),(10.5,'trough'),(12,'fall'),(29,'fall'),(46,'rise'),(50.5,'trough'),(51.5,'peak'),(53.5,'peak'),(57,'fall'),(74,'fall'),(91,'rise'),(95.5,'trough'),(96.5,'peak'),(98.5,'trough'),(100.5,'peak'),(103,'fall'),(124,'rise'),(126.5,'peak')]
 l=gaussian_filter(ximage[:,:,:3].mean(2),(1.3,2));dy=np.gradient(l,axis=0);targets=[0];traces=[np.zeros(w,np.float32)];horizontal=[]
 for sy,kind in anchors:
  nominal=sy*8-.5;radius=3 if any(abs(sy-t)<1.6 for t,k in anchors if t!=sy) else 6
  cand=np.arange(max(0,int(round(nominal))-radius),min(h,int(round(nominal))+radius+1))
  value=l[cand] if kind in ['peak','trough'] else dy[cand]
  sign=1 if kind in ['peak','rise'] else -1
  raw=cand[(value*sign).argmax(0)].astype('float32')
  # Strong aperture/molding evidence lies away from upright piers and corner shading.
  valid=np.zeros(w,bool)
  spans=[(12,27),(38,53)] if sy>=103 else ([(8,28),(36,57)] if gid=='FM0189' else [(8,25),(40,57)])
  for a,b in spans:valid[a*8:b*8]=True
  raw=np.interp(np.arange(w),np.flatnonzero(valid),raw[valid]).astype('float32');trace=gaussian_filter1d(raw,6,mode='nearest')
  horizontal.append({'source_y':sy,'kind':kind,'target_output_y':nominal,'search_radius_output':radius,'valid_source_x_spans':spans,'parent_after_x_trace_output_y':trace.tolist(),'displacement_range_output':[float((trace-nominal).min()),float((trace-nominal).max())]});targets.append(nominal);traces.append(trace)
 targets.append(h-1);traces.append(np.full(w,h-1,np.float32));traces=np.stack(traces)
 assert np.all(np.diff(traces,axis=0)>0)
 my=yy.copy()
 for x in range(w):my[:,x]=np.interp(np.arange(h),targets,traces[:,x])
 out=cv2.remap(ximage,xx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE);assert np.all(out[:,:,3]==255)
 maps=O/f'{gid}-rectification-v2-maps.npz';np.savez_compressed(maps,map_x=mx,map_y=my)
 op=O/f'{gid}-local-material-source-lines-v2-8x.png';Image.fromarray(out,'RGBA').save(op)
 mask=np.any(out!=p,axis=2);mp=O/f'{gid}-rectification-v2-changed.png';Image.fromarray(mask.astype('uint8')*255).save(mp)
 files.append({**{k:v[k] for k in ['group_id','source','source_ptm','source_ptm_sha256','source_rgba_sha256','parent','parent_sha256','parent_id']},'id':gid+'-local-material-source-lines-v2','output':str(op),'output_sha256':sha(op),'maps':str(maps),'maps_sha256':sha(maps),'changed_mask':str(mp),'changed_mask_sha256':sha(mp),'vertical_anchors':vertical,'horizontal_anchors':horizontal,'method':'Source-coordinate boundary anchors with locally measured material traces; sequential bilinear X/Y remap of existing local RGB.','new_local_passes':0,'external_calls':0,'visual_review':'pending','runtime_verified':False,'release_eligible':False})
 for kind,box in [('whole',(0,0,64,128)),('upper',(0,0,64,57)),('lower',(0,88,64,128))]:
  cw=(box[2]-box[0])*8;ch=(box[3]-box[1])*8;canvas=Image.new('RGB',((cw+16)*3,ch+42),'#26333f');d=ImageDraw.Draw(canvas)
  ims=[s.crop(box).resize((cw,ch),Image.Resampling.NEAREST),Image.fromarray(p,'RGBA').crop(tuple(t*8 for t in box)),Image.fromarray(out,'RGBA').crop(tuple(t*8 for t in box))]
  for j,(im,title) in enumerate(zip(ims,['원본 · 단순 확대','기존 로컬 · 보류','기존 재질 · 경계 보정 v2'])):d.text((j*(cw+16)+6,5),gid+' '+title,font=font,fill='white');canvas.paste(im.convert('RGB'),(j*(cw+16)+6,36))
  path=V/f'{gid}-{kind}-v2.png';canvas.save(path);pages.append({'group_id':gid,'path':str(path),'sha256':sha(path),'source_box':box,'review_status':'pending'})
Q.write_text(json.dumps({'schema':'brs-facade-rectification/v2','basis':'v1 source-profile planes passed rectangle partition checks but visibly lost metallic/brick material and created blurred bands; rejected. v2 retains the entire local material and remaps measured edges onto fixed source anchors.','files':files,'pages':pages,'new_local_passes':0,'external_calls':0,'limits':['Local gradient traces locate material and do not establish source geometry; fixed declared anchors come from source review.','Two bilinear warps may soften fine grain and do not guarantee every unmeasured edge/corner. Native visual review and corner diagnostics remain required.','No new detail recovery, consumer or runtime proof.'],'runtime_verified':False,'release_eligible':False},ensure_ascii=False,indent=2),'utf8')
print(json.dumps({'outputs':2,'pages':6,'new_local_passes':0}))
