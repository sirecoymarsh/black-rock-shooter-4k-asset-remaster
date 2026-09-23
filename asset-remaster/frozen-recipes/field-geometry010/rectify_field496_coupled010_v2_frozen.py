"""One coupled2D displacement field for adjoining facade edges, not serial strip warps."""
from pathlib import Path
import json,hashlib,shutil
import numpy as np,cv2
from scipy.ndimage import gaussian_filter,gaussian_filter1d,median_filter,map_coordinates
from PIL import Image,ImageDraw,ImageFont

def build(s,p):
 rgb=p[:,:,:3].astype('float32');h,w=rgb.shape[:2];yy,xx=np.mgrid[0:h,0:w].astype('float32');sourcey=(np.arange(h)+.5)/8;gray=gaussian_filter(rgb.mean(2),(1.25,9),mode='nearest');anchors=[0,18,28.5,30.5,39.5,43,60,63.5,67,128];modes={28.5:'min',30.5:'max',39.5:'min',63.5:'max'};curves=[];records=[]
 for y in anchors:
  if y not in modes:curve=np.full(w,y,dtype='float32')
  else:
   lo=max(0,int((y-1.35)*8));hi=min(h,int((y+1.35)*8)+1);region=gray[lo:hi];indices=np.argmin(region,axis=0) if modes[y]=='min' else np.argmax(region,axis=0);curve=(lo+indices+.5).astype('float32')/8;curve=gaussian_filter1d(median_filter(curve,size=25,mode='nearest'),12,mode='nearest');records.append({'kind':'horizontal_anchor','source_y':y,'detector':modes[y],'parent_y_minmax':[float(curve.min()),float(curve.max())]})
  curves.append(curve)
 curves=np.asarray(curves);assert np.all(np.diff(curves,axis=0)>0);mapy=np.empty((h,w),np.float32)
 for x in range(w):mapy[:,x]=np.interp(sourcey,anchors,curves[:,x])*8-.5
 base=cv2.remap(rgb,xx,mapy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE);smooth=gaussian_filter(base.mean(2),1.25,mode='nearest')
 # Shared vertices are intersections of the same source line equations.
 left=lambda y:145.2+(y-101)*8.44/27
 right=lambda y:190.75-(y-100)*8.25/28
 corners=[[left(100.5),100.5],[right(100.5),100.5],[right(127),127],[left(127),127]]
 lines=[('upper-left',[57.5,40.5],[57.5,63.5],'min'),('upper-right',[182.5,40.5],[182.5,63.5],'min'),('recess',[117.5,64.5],[117.5,94.5],'min'),('lower-left',[9.5,96.5],[9.5,128.],'min'),('plate-left',corners[0],[left(128),128.],'min'),('plate-right',[right(94),94.],[right(128),128.],'min'),('plate-top',corners[0],corners[1],'max'),('plate-bottom',corners[3],corners[2],'max'),('lower-horizontal',[196.,107.5],[256.,107.5],'min'),('lower-thin',[226.5,109.],[226.5,128.],'min'),('lower-dark',[242.5,109.],[242.5,128.],'min')]
 Axx=np.zeros((h,w),np.float32);Axy=Axx.copy();Ayy=Axx.copy();bx=Axx.copy();by=Axx.copy();support=Axx.copy();frozen={'horizontal_mapy':mapy,'horizontal_parent_anchors':curves};x=(xx+.5)/8;y=(yy+.5)/8
 for name,start,end,polarity in lines:
  a=np.asarray(start);b=np.asarray(end);vec=b-a;length=float(np.linalg.norm(vec));tan=vec/length;normal=np.array([-tan[1],tan[0]]);along=(x-a[0])*tan[0]+(y-a[1])*tan[1];dist=(x-a[0])*normal[0]+(y-a[1])*normal[1];pos=np.linspace(0,length,max(16,round(length*4)));ds=np.linspace(-1.5,1.5,49);points=a[None,None,:]+pos[:,None,None]*tan[None,None,:]+ds[None,:,None]*normal[None,None,:];samples=cv2.remap(smooth,(points[:,:,0]*8-.5).astype('float32'),(points[:,:,1]*8-.5).astype('float32'),cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE);idx=np.argmin(samples,1) if polarity=='min' else np.argmax(samples,1);offset=ds[idx]
  # Estimate near a corner from nearby edge interiors, never chase its isolated grain peak.
  interior=(pos>=2)&(pos<=length-2)
  if interior.sum()>=3:offset=np.interp(pos,pos[interior],offset[interior])
  offset=gaussian_filter1d(median_filter(offset,size=9,mode='nearest'),4,mode='nearest');delta=np.interp(along,pos,offset)
  cross=np.clip((4-abs(dist))/3,0,1);ends=np.minimum(np.clip((along+2)/2,0,1),np.clip((length+2-along)/2,0,1));weight=(cross*cross*(3-2*cross)*ends*ends*(3-2*ends)).astype('float32')
  Axx+=weight*normal[0]**2;Axy+=weight*normal[0]*normal[1];Ayy+=weight*normal[1]**2;bx+=weight*normal[0]*delta;by+=weight*normal[1]*delta;support=np.maximum(support,weight)
  frozen[name+'-offset']=offset;records.append({'kind':'coupled_segment','name':name,'source_start':start,'source_end':end,'detector':polarity,'sample_along_source':pos.tolist(),'parent_normal_offset_source':offset.tolist(),'normal_offset_range':[float(offset.min()),float(offset.max())],'support_halfwidth_source':4,'core_halfwidth_source':1,'end_extension_source':2,'endpoint_offset_estimate':'interpolated from edge interior excluding2source px','median_cross_contrast':float(np.median(samples.max(1)-samples.min(1)))})
 ridge=.03;Axx+=ridge;Ayy+=ridge;det=Axx*Ayy-Axy*Axy;assert np.all(det>0);dx=(Ayy*bx-Axy*by)/det;dy=(Axx*by-Axy*bx)/det;
 # Integrate a smooth stationary velocity; small positive steps avoid fold-over.
 boundary=np.minimum(np.minimum(xx,w-1-xx),np.minimum(yy,h-1-yy));fade=np.clip(boundary/16,0,1);fade=fade*fade*(3-2*fade);vx=gaussian_filter(dx,3,mode='nearest')*fade*8;vy=gaussian_filter(dy,3,mode='nearest')*fade*8;steps=7;fx=vx/(2**steps);fy=vy/(2**steps)
 for iteration in range(steps):
  coords=np.array([yy+fy,xx+fx]);nx=fx+map_coordinates(fx,coords,order=1,mode='nearest',prefilter=False);ny=fy+map_coordinates(fy,coords,order=1,mode='nearest',prefilter=False);fx,fy=nx,ny
 mx=xx+fx;my=yy+fy

 # Positive Jacobian prevents fold-over of the shared corner neighborhood.
 dxdy,dxdx=np.gradient(mx);dydy,dydx=np.gradient(my);jac=dxdx*dydy-dxdy*dydx;assert np.isfinite(jac).all() and float(jac.min())>0
 final=cv2.remap(base,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE);out=np.dstack([np.rint(np.clip(final,0,255)).astype('uint8'),p[:,:,3]]);mask=(abs(fx)+abs(fy)>0)|(abs(mapy-yy)>1e-4);assert np.array_equal(out[~mask],p[~mask]);frozen.update(coupled_mapx=mx,coupled_mapy=my,coupled_support=support,coupled_jacobian=jac,velocity_x=vx,velocity_y=vy,integrated_displacement_x=fx,integrated_displacement_y=fy)
 summary={'ridge':ridge,'velocity_smoothing_native_px':3,'integration_squarings':steps,'boundary_fade_native_px':16,'source_plate_corners':corners,'right_edge_source_extension_to_y94_preserved':True,'coupled_map_jacobian_min':float(jac.min()),'nonpositive_jacobian_pixels':int((jac<=0).sum()),'max_displacement_source_px':float(np.hypot(fx,fy).max()/8),'corner_semantics':'Left upper corner and each adjoining edge are mapped simultaneously. The right sloping feature continues above the top edge in the source and is not cut off to invent a closed undamaged trapezoid.'}
 return out,mask,frozen,records,summary

def main():
 R=Path(__file__).resolve().parents[1];O=R/'workspace/local-sr/field-geometry010';P=R/'outputs/field-geometry010';Q=R/'qa/field_geometry010_facade496_v2.json';assert not Q.exists();O.mkdir(exist_ok=True);P.mkdir(exist_ok=True)
 def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
 prior=json.loads((R/'qa/field_geometry008_facade496_v2.json').read_text('utf8'));s=np.asarray(Image.open(prior['source']).convert('RGBA'));p=np.asarray(Image.open(prior['parent']).convert('RGBA'));old=np.asarray(Image.open(prior['output']).convert('RGBA'));out,mask,maps,records,summary=build(s,p);op=O/'FM0496-coupled-edges-v2-8x.png';Image.fromarray(out).save(op);mp=O/'FM0496-coupled-edges-v2-mask.png';Image.fromarray(mask.astype('uint8')*255).save(mp);fp=O/'FM0496-coupled-edges-v2-maps.npz';np.savez_compressed(fp,**maps);program=O/'rectify_field496_coupled010_v2_frozen.py';shutil.copy2(__file__,program)
 elems=['<svg xmlns="http://www.w3.org/2000/svg" width="2048" height="1024" viewBox="0 0 256 128">']
 for z in records:
  coords=[0,z['source_y'],256,z['source_y']] if z['kind']=='horizontal_anchor' else z['source_start']+z['source_end'];x1,y1,x2,y2=coords;elems.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="white" stroke-width=".1"/>')
 elems.append('</svg>');vp=O/'FM0496-coupled-edges-v2-guide.svg';vp.write_text(''.join(elems),'utf8');font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',15);pages=[]
 for tag,box in [('whole',None),('cornice',(44,12,84,52)),('recess',(98,52,138,92)),('plate-all',(136,88,204,128)),('left-plate',(136,88,176,128)),('right-plate',(168,88,208,128)),('right-joints',(216,88,256,128))]:
  can=Image.new('RGB',(1400,410),'#25313c');d=ImageDraw.Draw(can)
  for col,(a,title) in enumerate([(s,'원본 · 단순 확대'),(p,'로컬 Photo'),(old,'이전 개별 보정 · 보류'),(out,'접힘 방지·모서리 통합 v2')]):
   im=Image.fromarray(a)
   if box:im=im.crop(box if col==0 else tuple(t*8 for t in box))
   scale=min(320/im.width,340/im.height);pic=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST if col==0 else Image.Resampling.LANCZOS);d.text((col*350+8,8),'FM0496 '+title,font=font,fill='white');can.paste(pic.convert('RGB'),(col*350+(350-pic.width)//2,48+(340-pic.height)//2))
  pp=P/f'FM0496-coupled-v2-{tag}.png';can.save(pp);pages.append({'path':str(pp),'sha256':sha(pp),'source_box':box,'review_status':'pending'})
 report={**{k:prior[k] for k in ['group_id','source','source_ptm','source_ptm_sha256','source_rgba_sha256','parent','parent_sha256']},'schema':'brs-coupled-facade010/v2','id':'FM0496-coupled-edges-v2','previous_goal_turn_classification':'progress: geometry009 resolved3 checker holds,9 derivative outputs and source-design evidence verified.','catalog_before_sha256':sha(R/'qa/field_sr_catalog.json'),'geometry_contract_before_sha256':sha(R/'qa/architectural_geometry_contract.json'),'previous_rejected_output':prior['output'],'previous_rejected_output_sha256':prior['output_sha256'],'output':str(op),'output_sha256':sha(op),'mask':str(mp),'mask_sha256':sha(mp),'maps':str(fp),'maps_sha256':sha(fp),'vector':str(vp),'vector_sha256':sha(vp),'reconstruction_program':str(program),'reconstruction_program_sha256':sha(program),'anchors':records,'coupling_diagnostics':summary,'method':'Source horizontal bands and a single joint2D least-squares field integrated as smooth stationary velocity for all11 segments; shared source corner vertices and preserved sloping continuation. Existing Photo material remapped, no painting or new neural inference.','new_local_passes':0,'new_external_calls':0,'pages':pages,'runtime_verified':False,'release_eligible':False};Q.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8');print(json.dumps(summary),flush=True)
if __name__=='__main__':main()
