"""Local source-mask super resolution; no semantic image generation."""
import json,hashlib
import numpy as np
import cv2
from PIL import Image
from scipy.ndimage import distance_transform_edt
import local_sr as sr
from icon_geometry import rebuild
MODEL=None

def render(src,folder):
 global MODEL
 if MODEL is None:MODEL=sr.load_model()
 rgba=np.array(src);alpha=rgba[:,:,3];rgb=rgba[:,:,:3].copy()
 peak=int(alpha.max());values=np.unique(alpha)
 if len(values)<=32:levels=values[values>0]
 else:levels=np.unique(np.r_[np.linspace(peak/24,peak,24).round(),[v for v in [40,120,249] if v<peak]])
 high=np.zeros((src.height*4,src.width*4),np.uint8);previous=0.;seen={}
 for value in levels:
  mask=((alpha.astype(float)>=(previous+float(value))/2)*255).astype('uint8')
  key=hashlib.sha256(mask.tobytes()).hexdigest()
  if key not in seen:
   padded=np.pad(mask,8,mode='edge')
   pred=np.array(sr.infer_rgb(MODEL,Image.fromarray(padded).convert('RGB')))[32:-32,32:-32,0]
   seen[key]=pred>=128
  high[seen[key]]=round(float(value));previous=float(value)
 if (alpha>0).any():
  inds=distance_transform_edt(alpha==0,return_distances=False,return_indices=True)
  rgb[alpha==0]=rgb[inds[0][alpha==0],inds[1][alpha==0]]
 if np.max(np.ptp(rgb.reshape(-1,3).astype(int),axis=0))<=5:
  color=tuple(np.median(rgb.reshape(-1,3),axis=0).astype(int));out=Image.new('RGBA',(src.width*4,src.height*4),(*color,255))
 else:
  padded=np.pad(rgb,((8,8),(8,8),(0,0)),mode='edge')
  nr=np.asarray(sr.infer_rgb(MODEL,Image.fromarray(padded)),dtype=np.float32)[32:-32,32:-32]
  error=rgb.astype(np.float32)-cv2.resize(nr,src.size,interpolation=cv2.INTER_AREA)
  nr=np.clip(nr+.5*cv2.resize(error,(src.width*4,src.height*4),interpolation=cv2.INTER_CUBIC),0,255)
  # Flat UI colors come only from the source palette. SR may infer curves,
  # but must not turn muted green/pink into a new saturated neon color.
  colors,counts=np.unique(rgba[:,:,:3][alpha>0],axis=0,return_counts=True)
  palette=colors[np.argsort(counts)[-32:]].astype(np.float32)
  flat=nr.reshape(-1,3);mapped=np.empty_like(flat)
  for start in range(0,len(flat),8192):
   block=flat[start:start+8192];idx=np.argmin(((block[:,None]-palette[None])**2).sum(axis=2),axis=1);mapped[start:start+8192]=palette[idx]
  out=Image.fromarray(mapped.reshape(nr.shape).astype('uint8')).convert('RGBA')
 bounds=src.getchannel('A').getbbox()
 if bounds:
  x,y,x1,y1=[v*4 for v in bounds];bounded=np.zeros_like(high);bounded[y:y1,x:x1]=high[y:y1,x:x1];high=bounded
 out.putalpha(Image.fromarray(high));out.save(folder/'local-binary4x.png')
 (folder/'local-provenance.json').write_text(json.dumps(dict(**sr.provenance(),method='binary source-mask inference at original alpha levels; original color projection',mask_inferences=len(seen),source_rgba_sha256=hashlib.sha256(src.tobytes()).hexdigest()),ensure_ascii=False,indent=2),'utf8')
 return out.resize((src.width*8,src.height*8),Image.Resampling.LANCZOS)
