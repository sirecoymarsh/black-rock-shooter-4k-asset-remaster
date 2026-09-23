"""Original binary topology, antialiased silhouette and opaque diagonal junctions."""
import numpy as np,cv2
from scipy.ndimage import distance_transform_edt,label
def topology(mask):
 _,n=label(mask,np.ones((3,3),int));z,k=label(~mask,[[0,1,0],[1,1,1],[0,1,0]]);edge=set(np.r_[z[0],z[-1],z[:,0],z[:,-1]]);return {'foreground_8_components':int(n),'background_4_enclosed_holes':sum(i not in edge for i in range(1,k+1))}
def make_alpha(alpha):
 assert set(np.unique(alpha))<={0,255};h,w=alpha.shape;mask=alpha>0;signed=(distance_transform_edt(mask)-distance_transform_edt(~mask))*.5;sd=cv2.resize(signed.astype('float32'),(w*8,h*8),interpolation=cv2.INTER_LINEAR);base=np.rint(np.clip(sd*8+.5,0,1)*255).astype('uint8');out=base.copy();junctions=[]
 for y in range(h-1):
  for x in range(w-1):
   tl,tr,bl,br=bool(mask[y,x]),bool(mask[y,x+1]),bool(mask[y+1,x]),bool(mask[y+1,x+1]);by=(y+1)*8;bx=(x+1)*8
   if tl and br and not tr and not bl:points=[(by-1,bx-1),(by,bx)]
   elif tr and bl and not tl and not br:points=[(by-1,bx),(by,bx-1)]
   else:continue
   for py,px in points:out[py,px]=255
   junctions.append({'source_quad_top_left':[x,y],'opaque_output_yx':[list(v) for v in points]})
 assert np.array_equal(out[4::8,4::8],alpha)
 return out,base,junctions
def prepare_rgb(rgba):
 mask=rgba[:,:,3]>0;_,indices=distance_transform_edt(~mask,return_indices=True);out=rgba[:,:,:3].copy();out[~mask]=out[indices[0][~mask],indices[1][~mask]];return out
