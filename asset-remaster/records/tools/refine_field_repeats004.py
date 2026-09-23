"""Improve material without relaxing fixed original structural coordinates."""
import json,hashlib
from pathlib import Path
import numpy as np,cv2
from scipy.ndimage import gaussian_filter,gaussian_filter1d
from scipy.interpolate import PchipInterpolator
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];Q=R/'qa/field_geometry004_refined.json';assert not Q.exists()
O=R/'workspace/local-sr/field-geometry004';V=R/'outputs/field-geometry004';font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
old=json.loads((R/'qa/field_geometry004_trials.json').read_text('utf8'));files=[];pages=[]
for v in old['files']:
 gid=v['group_id'];s=np.asarray(Image.open(v['source']).convert('RGBA'));p=np.asarray(Image.open(v['parent']).convert('RGBA'));prev=np.asarray(Image.open(v['output']).convert('RGBA'));h,w=s.shape[:2];base=np.load(v['base_planes'])['rgb'].copy();out=p.copy();details={}
 if gid=='FM0337':
  material=np.zeros_like(base);details['regions']=[]
  for z in v['regions']:
   x0,y0,x1,y1=z['source_box'];a,b,c,d=[q*8 for q in z['source_box']];src=s[y0:y1,x0:x1,:3].astype('float32');base[b:d,a:c]=cv2.resize(gaussian_filter(src,(1.2,.8,0),mode='nearest'),(c-a,d-b),interpolation=cv2.INTER_CUBIC)
   px=min(8,max(0,(c-a-8)//2));py=min(4,max(0,(d-b-8)//2));patch=p[b+py:d-py or None,a+px:c-px or None,:3].astype('float32');patch=cv2.resize(patch,(c-a,d-b),interpolation=cv2.INTER_CUBIC)
   fine=patch-gaussian_filter(patch,(12,12,0),mode='nearest');material[b:d,a:c]=np.clip(fine*.75,-10,10)
   details['regions'].append({'source_box':z['source_box'],'parent_interior_output_trim_xy':[px,py]})
  out[:,:,:3]=np.rint(np.clip(base+material,0,255)).astype('uint8');details.update(source_sigma=[1.2,.8,0],material_sigma_output=12,material_gain=.75,material_RGB_bound=10)
 elif gid=='FM0346':
  # Pooled periodic cross section keeps broad pale faces and the actual six-pixel
  # repeat. Interpolation is across the flute's shaded face, not along its edge.
  lower=s[16:32,:,:3].astype('float32');phase=np.array([np.median(lower[:,k::6,:],axis=1) for k in range(6)]).transpose(1,0,2)
  xs=(np.arange(w*8)+.5)/8-.5;ys=(np.arange(16*8)+.5)/8-.5
  tiled=np.tile(phase,(1,7,1));mx=np.broadcast_to((xs+6).astype('float32'),(128,256));my=np.broadcast_to(ys[:,None].astype('float32'),(128,256));base[128:]=cv2.remap(tiled,mx,my,cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
  grain=p[:,:,:3].astype('float32')-gaussian_filter(p[:,:,:3].astype('float32'),(8,8,0),mode='nearest');out[:,:,:3]=np.rint(np.clip(base+np.clip(grain*.65,-4,4),0,255)).astype('uint8')
  details.update(source_phase_rgb=phase.tolist(),period_source=6,lower_source_y=16,interpolation='cv2 cubic with periodic source phase, clamped vertical boundary',grain_sigma_output=8,grain_gain=.65,grain_bound=4)
 else:
  # Recreate the same traced centers with a narrow beveled profile. A broad
  # Gaussian line was too soft, even when its center positions were correct.
  by=np.median(s[17:31,:,:3],axis=1).astype('float32');back=cv2.resize(by[:,None,:],(512,112),interpolation=cv2.INTER_LINEAR);yy=(np.arange(136,248)+.5)/8;xx=(np.arange(512)+.5)/8
  closest=np.full((112,512),999.,np.float32);signed=np.zeros_like(closest)
  for c in v['curve_centers']:
   cx=PchipInterpolator(c['source_y'],c['source_x'],extrapolate=True)(yy);dd=xx[None,:]-cx[:,None];take=np.abs(dd)<closest;closest[take]=np.abs(dd)[take];signed[take]=dd[take]
  high=cv2.resize(np.array(v['curve_highlight_profile_rgb'],np.float32)[:,None,:],(512,112),interpolation=cv2.INTER_LINEAR)
  coverage=np.clip((1.05-closest)/.25,0,1)[:,:,None];bevel=np.clip(.88+.12*signed/.8,.72,1.0)[:,:,None]
  brace=high*bevel;base[136:248]=back*(1-coverage)+brace*coverage
  grain=p[:,:,:3].astype('float32')-gaussian_filter(p[:,:,:3].astype('float32'),(5,5,0),mode='nearest');out[:,:,:3]=np.rint(np.clip(base+np.clip(grain*.30,-2,2),0,255)).astype('uint8');details.update(curve_centers=v['curve_centers'],curve_highlight_profile_rgb=v['curve_highlight_profile_rgb'],stroke_outer_halfwidth_source=1.05,stroke_edge_transition_source=.25,bevel_equation='clip(.88+.12*signed/.8,.72,1)',grain_sigma_output=5,grain_gain=.30,grain_bound=2)
 out[:,:,3]=255;ident=gid+'-source-planes-refined-v2';op=O/(ident+'-8x.png');bp=O/(ident+'-base.npz');Image.fromarray(out).save(op);np.savez_compressed(bp,rgb=base)
 files.append({**{k:v[k] for k in ['group_id','source','source_ptm','source_ptm_sha256','source_rgba_sha256','parent','parent_sha256','vector','vector_sha256','region_classmap','region_classmap_sha256','regions']},'id':ident,'previous':v['output'],'previous_sha256':v['output_sha256'],'output':str(op),'output_sha256':sha(op),'base_planes':str(bp),'base_planes_sha256':sha(bp),'recipe':details,'method':'Source-fixed structure with revised material/profile: spatial local interior grain for337, source periodic bevel shading for346, narrow beveled source curves for347. No new neural inference.','new_neural_passes':0,'visual_review':'pending','runtime_verified':False,'release_eligible':False})
 boxes=[('whole',(0,0,w,h))]
 if gid!='FM0346':boxes.append(('detail',(40,0,72,32) if gid=='FM0337' else (16,0,48,32)))
 for label,box in boxes:
  cw,ch=(box[2]-box[0])*8,(box[3]-box[1])*8;scale=min(1,640/cw,512/ch) if label=='whole' else 1;sw,sh=round(cw*scale),round(ch*scale);col=max(310,sw+16);can=Image.new('RGB',(col*3,sh+46),'#26333f');d=ImageDraw.Draw(can)
  ims=[Image.fromarray(s).crop(box).resize((cw,ch),Image.Resampling.NEAREST),Image.fromarray(prev).crop(tuple(t*8 for t in box)),Image.fromarray(out).crop(tuple(t*8 for t in box))]
  for j,(im,title) in enumerate(zip(ims,['원본 · 단순 확대','구조 고정 · 첫 수정','구조 유지 · 재질 수정'])):d.text((j*col+6,5),gid+' '+title,font=font,fill='white');can.paste(im.resize((sw,sh),Image.Resampling.NEAREST if j==0 else Image.Resampling.LANCZOS).convert('RGB'),(j*col+6,38))
  pp=V/(gid+'-'+label+'-v2.png');can.save(pp);pages.append({'path':str(pp),'sha256':sha(pp),'source_box':list(box),'review_status':'pending'})
Q.write_text(json.dumps({'schema':'brs-source-repeat-reconstruction/v2','basis':'First fixed geometry trials make337 material too diffuse,346 flute faces too flat, and347 curves too soft. Keep source coordinates while correcting each distinct material defect.','parent_report_sha256':sha(R/'qa/field_geometry004_trials.json'),'files':files,'pages':pages,'new_neural_passes':0,'external_calls':0,'runtime_verified':False,'release_eligible':False},ensure_ascii=False,indent=2),'utf8')
print('Saved3 refined candidates and5 comparison pages.')
