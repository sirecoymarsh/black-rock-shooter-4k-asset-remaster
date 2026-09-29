"""Source contour reconstruction with protected orthogonal corners."""
import json,math,hashlib
import numpy as np
import cv2
from PIL import Image
from skimage.measure import find_contours,approximate_polygon
from scipy.ndimage import distance_transform_edt

def outline(binary,force_orthogonal=False):
 doubled=np.repeat(np.repeat(binary.astype(float),2,axis=0),2,axis=1)
 paths=[]
 for c in find_contours(np.pad(doubled,1),.5,fully_connected='high'):
  p=c[:-1].copy();nxt=np.roll(p,-1,axis=0)
  dv=nxt-p;incoming=p-np.roll(p,1,axis=0);outgoing=np.roll(p,-2,axis=0)-nxt
  diag=np.all(np.abs(dv)==.5,axis=1)
  hv=diag & (incoming[:,0]==0) & (outgoing[:,1]==0)
  vh=diag & (incoming[:,1]==0) & (outgoing[:,0]==0)
  p[hv,1]=nxt[hv,1];p[vh,0]=nxt[vh,0]
  p=(p[~np.roll(hv|vh,1)]-.5)/2
  # Remove exactly collinear vertices, without moving any corner.
  u=p-np.roll(p,1,axis=0);v=np.roll(p,-1,axis=0)-p
  cross=u[:,0]*v[:,1]-u[:,1]*v[:,0]
  p=p[np.abs(cross)>1e-8]
  if len(p)<3:continue
  lo=p.min(axis=0);hi=p.max(axis=0);center=(lo+hi)/2
  radii=np.linalg.norm(p-center,axis=1);mean=radii.mean()
  if not force_orthogonal and len(p)>=12 and mean>2 and radii.std()/mean<.065 and abs((hi-lo)[0]-(hi-lo)[1])<=1:
   # Area fixes the circle radius; the source bounding center is retained.
   area=abs(cv2.contourArea(p[:,::-1].astype('float32')))
   radius=math.sqrt(area/math.pi);angles=np.linspace(0,2*math.pi,192,endpoint=False)
   p=np.column_stack((center[0]+radius*np.sin(angles),center[1]+radius*np.cos(angles)))
  elif not force_orthogonal and len(p)>4:
   u=p-np.roll(p,1,axis=0);v=np.roll(p,-1,axis=0)-p
   lengths=np.maximum(np.linalg.norm(u,axis=1),np.linalg.norm(v,axis=1))
   # A run of >=2 source pixels establishes an authored axis. Its corner is
   # immutable; only one-pixel staircase chains between anchors are fitted.
   anchors=np.flatnonzero(lengths>=2)
   if len(anchors)>=2:
    pieces=[]
    for j,start in enumerate(anchors):
     end=anchors[(j+1)%len(anchors)]
     seq=p[start:end+1] if end>start else np.concatenate((p[start:],p[:end+1]))
     pieces.extend(approximate_polygon(seq,tolerance=.72)[:-1])
    p=np.array(pieces)
   else:
    p=approximate_polygon(np.concatenate((p,p[:1])),tolerance=.55)[:-1]
  paths.append(p[:,::-1].round(5).tolist())
 return paths

def rebuild(src,folder,scale=8):
 rgba=np.asarray(src,dtype=np.float32);alpha=rgba[:,:,3]
 factor=scale*3;size=(src.width*scale,src.height*scale)
 orth=folder.name in {'cell-4','cell-12','cell-14','cell-15','cell-16','cell-17','cell-18','cell-26','cell-31','cell-32','cell-33','cell-34','cell-56','frame-original'} or any(x in folder.parts for x in ['ICO-036','ICO-061'])
 fields=[alpha]+[rgba[:,:,c]*alpha/255 for c in range(3)]
 channels=[];records=[]
 for channel,field in enumerate(fields):
  values=np.unique(field);peak=float(field.max())
  levels=values[values>0] if len(values)<=32 else np.linspace(peak/32,peak,32)
  high=np.zeros((src.height*factor,src.width*factor),np.float32);previous=0.
  for value in levels:
   paths=outline(field>=(previous+float(value))/2,orth)
   if paths:cv2.fillPoly(high,[np.rint(np.array(p)*factor).astype('int32') for p in paths],float(value))
   records.append(dict(channel=channel,value=float(value),paths=paths));previous=float(value)
  channels.append(np.clip(np.array(Image.fromarray(high,'F').resize(size,Image.Resampling.LANCZOS)),0,255))
 al=channels[0];out=np.zeros((*al.shape,4),np.uint8);out[:,:,3]=np.rint(al)
 for c in range(3):out[:,:,c]=np.rint(np.clip(channels[c+1]*255/np.maximum(al,.001),0,255))
 matte=np.array(src.resize(size,Image.Resampling.NEAREST));out[al<.5,:3]=matte[al<.5,:3]
 (folder/'layered-contours.json').write_text(json.dumps(dict(source_rgba_sha256=hashlib.sha256(src.tobytes()).hexdigest(),protected_axis_runs_native_px=2,staircase_tolerance=.72,force_orthogonal=orth,layers=records),separators=(',',':')),'utf8')
 return Image.fromarray(out)
