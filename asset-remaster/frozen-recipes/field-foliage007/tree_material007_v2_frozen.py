import numpy as np, cv2
from PIL import Image, ImageFilter
from scipy.ndimage import gaussian_filter,distance_transform_edt

# Authored source coordinates. Each node is (x,y,half-width), in decoded source pixels.
TRACKS=[
 {'name':'central_trunk','nodes':[(52.5,82,4.0),(53.6,94,4.3),(55.1,105,4.8),(55.7,116,5.2),(58,124.5,5.0)]},
 {'name':'central_right_arm','nodes':[(68.0,78.0,2.8),(63.2,86.0,3.4),(59.2,94.0,4.0),(55.3,102.0,4.7)]},
 {'name':'fork_stem','nodes':[(85,88,1.0),(83,95,2.0),(80.8,103,2.0),(79.2,114,1.9),(78.7,124.5,1.9)]},
 {'name':'fork_right_arm','nodes':[(95,94,0.8),(91,97,1.1),(87.3,101,1.35),(82,105,1.4),(80,109,1.4)]},
 {'name':'right_trunk','nodes':[(104.1,87,1.6),(102.3,96,2.4),(101.3,106,3.0),(101,117,3.4),(101,124.5,3.0)]},
 {'name':'far_right_trunk','nodes':[(126.2,97,1.0),(124.4,106,1.5),(124,116,1.6),(124,124.5,1.4)]}
]
CANOPY_BOTTOM=[(0,87),(8,96),(18,103),(26,89),(35,84),(45,85),(55,84),(65,88),(76,83),(87,81),(97,85),(110,90),(128,86)]
BARK_BOX=(516,865,564,1185)

def material_field(rgb,sigma):
 return rgb-gaussian_filter(rgb,(sigma,sigma,0),mode='reflect')

def source_extended(source):
 rgb=source[:,:,:3].copy();m=source[:,:,3]>0
 idx=distance_transform_edt(~m,return_distances=False,return_indices=True)
 rgb[~m]=rgb[idx[0][~m],idx[1][~m]]
 return rgb

def tracks_maps(shape):
 h,w=shape;yy,xx=np.mgrid[:h,:w];xx=(xx+.5)/8;yy=(yy+.5)/8
 results=[]
 for track in TRACKS:
  nodes=np.array(track['nodes'],float);best=np.full((h,w),1e20);u=np.zeros((h,w));v=np.zeros((h,w));inside=np.zeros((h,w));lengths=np.linalg.norm(np.diff(nodes[:,:2],axis=0),axis=1);total=lengths.sum();offset=0.
  for i,(a,b) in enumerate(zip(nodes[:-1],nodes[1:])):
   vector=b[:2]-a[:2];length=lengths[i];tx,ty=vector/length;dx=xx-a[0];dy=yy-a[1];t=np.clip((dx*tx+dy*ty)/length,0,1);cx=a[0]+t*vector[0];cy=a[1]+t*vector[1];dist=np.sqrt((xx-cx)**2+(yy-cy)**2);half=a[2]+t*(b[2]-a[2]);score=dist-half;choose=score<best;best[choose]=score[choose];cross=(xx-cx)*(-ty)+(yy-cy)*tx;u[choose]=(cross/((half+3)*2)+.5)[choose];v[choose]=((offset+t*length)/total)[choose];offset+=length
  coverage=np.clip(.5-best*8,0,1);coverage[yy>=125]=0
  results.append({'name':track['name'],'coverage':coverage,'score':best,'u':np.clip(u,0,1),'v':np.clip(v,0,1)})
 return results

def build(source,parent,donor):
 h,w=parent.shape[:2];assert source.shape[:2]==(128,128) and (h,w)==(1024,1024)
 donor_rgb=np.asarray(Image.fromarray(donor).resize((w,h),Image.Resampling.LANCZOS))[:,:,:3].astype(float)
 source_rgb=source_extended(source);base=np.asarray(Image.fromarray(source_rgb).filter(ImageFilter.GaussianBlur(.45)).resize((w,h),Image.Resampling.BICUBIC)).astype(float)
 leafgrain=np.clip(material_field(donor_rgb,12)*.85,-30,30)
 yy,xx=np.mgrid[:h,:w];xsource=(xx+.5)/8;ysource=(yy+.5)/8;lower=np.interp(xsource[0],[p[0] for p in CANOPY_BOTTOM],[p[1] for p in CANOPY_BOTTOM]);canopy=np.clip((lower[None,:]-ysource)/2+.5,0,1)
 out=parent.copy();rgb=parent[:,:,:3].astype(float);leaf=np.clip(base+leafgrain,0,255)
 crop=np.asarray(Image.fromarray(donor).crop(BARK_BOX).convert('RGB')).astype(float);barkgrain=np.clip(material_field(crop,8)*.8,-24,24);layers=tracks_maps((h,w));coverage=canopy.copy()
 # The source color classes gate bark; authored axes orient grain but do not invent trunk edges.
 woodclass=(source[:,:,:3].mean(2)>=45).astype(float)
 woodclass=cv2.resize(gaussian_filter(woodclass,.45),(w,h),interpolation=cv2.INTER_LINEAR)
 background_grain=np.clip(material_field(parent[:,:,:3].astype(float),2)*.3,-3,3)
 expanded=[np.clip((3-layer['score'])/2,0,1)*np.clip(125-ysource,0,1) for layer in layers]
 all_envelopes=np.maximum.reduce(expanded)
 rgb=rgb*(1-all_envelopes[:,:,None])+(base+background_grain)*all_envelopes[:,:,None]
 for layer in layers:
  envelope=np.clip((3-layer['score'])/2,0,1)*np.clip(125-ysource,0,1);mask=envelope*woodclass;u=layer['u']*(crop.shape[1]-1);v=layer['v']*(crop.shape[0]-1);grain=cv2.remap(barkgrain.astype('float32'),u.astype('float32'),v.astype('float32'),cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT_101);wood=np.clip(base+grain,0,255);rgb=rgb*(1-mask[:,:,None])+wood*mask[:,:,None];coverage=np.maximum(coverage,envelope)
 # Canopy lies in front of wood and hides the material-mask caps.
 rgb=rgb*(1-canopy[:,:,None])+leaf*canopy[:,:,None]
 out[:,:,:3]=np.rint(rgb).astype('uint8')
 # Preserve source-supported foliage outline, with only a small leaf-scale edge variation.
 fg=source[:,:,3]>0;signed=(distance_transform_edt(fg)-distance_transform_edt(~fg))*.5;distance=cv2.resize(signed,(w,h),interpolation=cv2.INTER_LINEAR)*8
 variation=np.clip(leafgrain.mean(2)/20,-1,1)*1.5*canopy
 alpha=np.rint(np.clip(distance+variation+.5,0,1)*255).astype('uint8')
 # Below canopy, reuse the already verified source-alpha parent exactly.
 alpha[canopy==0]=parent[:,:,3][canopy==0]
 # Keep the decoded source's diagonal foreground junctions connected.
 for y,x in zip(*np.where(fg[:-1,:-1] & fg[1:,1:] & ~fg[:-1,1:] & ~fg[1:,:-1])):
  by=(y+1)*8;bx=(x+1)*8;alpha[by-1,bx-1]=alpha[by,bx]=255
 for y,x in zip(*np.where(~fg[:-1,:-1] & ~fg[1:,1:] & fg[:-1,1:] & fg[1:,:-1])):
  by=(y+1)*8;bx=(x+1)*8;alpha[by-1,bx]=alpha[by,bx-1]=255
 out[:,:,3]=alpha
 return out,coverage,layers,{'canopy_bottom':CANOPY_BOTTOM,'tracks':TRACKS,'bark_box_in_GPT_raw':BARK_BOX,'source_RGB_filter_sigma':.45,'source_wood_luma_threshold':45,'source_wood_mask_sigma':.45,'wood_envelope_beyond_authored_halfwidth_source_px':3,'background_grain_clip':3,'canopy_composited_after_wood':True,'leaf_grain_sigma_output':12,'leaf_grain_gain':.85,'leaf_grain_clip':30,'bark_grain_sigma_raw':8,'bark_grain_gain':.8,'bark_grain_clip':24,'leaf_edge_variation_max_output_pixels':1.5,'source_center_alpha_exact':bool(np.array_equal(alpha[4::8,4::8],source[:,:,3])),'alpha_mass_ratio':float(alpha.mean()/source[:,:,3].mean())}
