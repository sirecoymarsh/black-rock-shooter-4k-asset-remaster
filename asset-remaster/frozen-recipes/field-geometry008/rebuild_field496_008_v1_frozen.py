"""Straight source cross-sections for cornices, joints and a sloping plate."""
from pathlib import Path
import json,hashlib,shutil
import numpy as np,cv2
from scipy.ndimage import gaussian_filter
from PIL import Image,ImageDraw,ImageFont

def build(s,p):
 s=s[:,:,:3].astype('float32');parent=p[:,:,:3].astype('float32');h,w=parent.shape[:2];rgb=parent.copy();mask=np.zeros((h,w),bool);classes=np.zeros((h,w),np.uint8);record=[];frozen={};fine=np.clip((parent-gaussian_filter(parent,(3,3,0),mode='nearest'))*.4,-3,3)
 # Together, not independently shifted lines: preserve the source band section.
 for idx,(y0,y1) in enumerate([(0,3),(20,42),(62,96)],1):
  profile=np.median(s,axis=1);ys=(np.arange(y0*8,y1*8)+.5)/8;vals=np.stack([np.interp(ys,np.arange(s.shape[0])+.5,profile[:,c]) for c in range(3)],1);rgb[y0*8:y1*8]=vals[:,None,:]+fine[y0*8:y1*8];mask[y0*8:y1*8]=True;classes[y0*8:y1*8]=idx;record.append({'kind':'horizontal_source_section','source_y_range':[y0,y1],'source_row_profile_rgb':profile.tolist(),'fine_grain_bound_RGB':3});frozen[f'section{idx}']=vals
 # Source-core coordinates. Sloping rails retain their source slope, not90deg.
 lines=[('upper-joint-left',[57.5,40.5],[57.5,63.5],3.),('upper-joint-right',[182.5,40.5],[182.5,63.5],3.),('recess-joint',[117.5,64.5],[117.5,94.5],3.),('lower-left-rail',[9.5,95.5],[9.5,128.0],3.),('plate-left',[145.2,101.],[153.64,128.],3.5),('plate-right',[190.75,100.],[182.5,128.],3.5),('plate-top',[146.5,100.5],[190.,100.5],3.),('plate-bottom',[154.,127.],[183.,127.],3.),('lower-horizontal',[196.,107.5],[256.,107.5],3.),('lower-joint-thin',[226.5,108.5],[226.5,128.],2.5),('lower-joint-dark',[242.5,108.5],[242.5,128.],3.)]
 yy,xx=np.mgrid[0:h,0:w].astype('float32');xx=(xx+.5)/8;yy=(yy+.5)/8
 for index,(name,start,end,half) in enumerate(lines,4):
  a=np.array(start);b=np.array(end);vec=b-a;length=float(np.linalg.norm(vec));tangent=vec/length;normal=np.array([-tangent[1],tangent[0]]);along=(xx-a[0])*tangent[0]+(yy-a[1])*tangent[1];dist=(xx-a[0])*normal[0]+(yy-a[1])*normal[1];inside=(along>=0)&(along<=length)&(abs(dist)<=half);t=np.linspace(.18,.82,31);ds=np.linspace(-half,half,57);points=a[None,None,:]+t[:,None,None]*vec[None,None,:]+ds[None,:,None]*normal[None,None,:];sample=cv2.remap(s,(points[:,:,0]-.5).astype('float32'),(points[:,:,1]-.5).astype('float32'),cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE);profile=np.median(sample,axis=0);baseline=profile[0][None,:]*(1-(ds+half)/(2*half))[:,None]+profile[-1][None,:]*((ds+half)/(2*half))[:,None];relief=profile-baseline
  fy=a[1]+along*tangent[1];fx=a[0]+along*tangent[0];left=cv2.remap(rgb,((fx-half*normal[0])*8-.5).astype('float32'),((fy-half*normal[1])*8-.5).astype('float32'),cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE);right=cv2.remap(rgb,((fx+half*normal[0])*8-.5).astype('float32'),((fy+half*normal[1])*8-.5).astype('float32'),cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE);u=np.clip((dist+half)/(2*half),0,1)[:,:,None];clean=left*(1-u)+right*u;delta=np.stack([np.interp(dist,ds,relief[:,c]) for c in range(3)],2);target=clean+delta+fine*.5;weight=(np.clip((half-abs(dist))/.55,0,1)*np.clip(along/.5,0,1)*np.clip((length-along)/.5,0,1))[:,:,None];new=rgb*(1-weight)+target*weight;rgb[inside]=new[inside];mask|=inside;classes[inside]=index
  record.append({'kind':'source_relief_segment','name':name,'source_start':start,'source_end':end,'half_width_source':half,'cross_offsets_source':ds.tolist(),'source_cross_profile_rgb':profile.tolist(),'source_relief_delta_rgb':relief.tolist(),'end_cap_blend_source':.5,'edge_blend_source':.55,'material':'Existing surface sampled on both flanks to erase model-warped edge, then source median transverse relief on a fixed straight segment.'})
  frozen[name+'-profile']=profile
 assert np.isfinite(rgb).all();out=np.dstack([np.rint(np.clip(rgb,0,255)).astype('uint8'),p[:,:,3]]);assert np.array_equal(out[~mask],p[~mask]);return out,mask,classes,record,frozen

def main():
 R=Path(__file__).resolve().parents[1];Q=R/'qa/field_geometry008_facade496_v1.json';assert not Q.exists();O=R/'workspace/local-sr/field-geometry008';P=R/'outputs/field-geometry008'
 def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
 audit=json.loads((R/'qa/field_geometry008_source_audit.json').read_text('utf8'));v=next(z for z in audit['files'] if z['group_id']=='FM0496');base=json.loads((R/'qa/field_sr005_inference.json').read_text('utf8'));parent=next(z for z in base['files'] if z['id']=='FM0496-photo');s=np.asarray(Image.open(v['source']).convert('RGBA'));p=np.asarray(Image.open(parent['output']).convert('RGBA'));out,mask,classes,records,frozen=build(s,p);op=O/'FM0496-source-cross-sections-v1-8x.png';Image.fromarray(out).save(op);mp=O/'FM0496-source-cross-sections-v1-mask.png';Image.fromarray(mask.astype('uint8')*255).save(mp);npth=O/'FM0496-source-cross-sections-v1-planes.npz';np.savez_compressed(npth,classes=classes,**frozen)
 svg=['<svg xmlns="http://www.w3.org/2000/svg" width="2048" height="1024" viewBox="0 0 256 128">']
 for z in records:
  if z['kind']=='horizontal_source_section':y0,y1=z['source_y_range'];svg.append(f'<rect x="0" y="{y0}" width="256" height="{y1-y0}" fill="white"/>')
  else:(x1,y1),(x2,y2)=z['source_start'],z['source_end'];svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="white" stroke-width="{2*z["half_width_source"]}"/>')
 svg.append('</svg>');vp=O/'FM0496-source-cross-sections-v1.svg';vp.write_text(''.join(svg),'utf8');program=O/'rebuild_field496_008_v1_frozen.py';shutil.copy2(Path(__file__),program);font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17);pages=[]
 boxes=[('whole',None),('cornice',(44,12,84,52)),('recess',(98,52,138,92)),('left-plate',(136,88,176,128)),('right-plate',(168,88,208,128)),('right-joints',(216,88,256,128))]
 for tag,box in boxes:
  can=Image.new('RGB',(1050,410),'#25313c');d=ImageDraw.Draw(can)
  for col,(a,title) in enumerate([(s,'원본 · 단순 확대'),(p,'로컬 Photo'),(out,'직선·원본 단면 재구성 v1')]):
   im=Image.fromarray(a)
   if box:im=im.crop(box if col==0 else tuple(t*8 for t in box));sc=8 if col==0 else 1
   else:sc=min(320/im.width,340/im.height)
   pic=im.resize((round(im.width*sc),round(im.height*sc)),Image.Resampling.NEAREST if col==0 else Image.Resampling.LANCZOS);d.text((col*350+8,8),'FM0496 '+title,font=font,fill='white');can.paste(pic.convert('RGB'),(col*350+(350-pic.width)//2,48+(340-pic.height)//2))
  pp=P/f'FM0496-v1-{tag}.png';can.save(pp);pages.append({'path':str(pp),'sha256':sha(pp),'source_box':box,'review_status':'pending'})
 data={**{k:v[k] for k in ['group_id','source','source_ptm','source_ptm_sha256','source_rgba_sha256']},'id':'FM0496-source-cross-sections-v1','source_audit_sha256':sha(R/'qa/field_geometry008_source_audit.json'),'parent':parent['output'],'parent_sha256':parent['output_sha256'],'output':str(op),'output_sha256':sha(op),'mask':str(mp),'mask_sha256':sha(mp),'vector':str(vp),'vector_sha256':sha(vp),'frozen_planes':str(npth),'frozen_planes_sha256':sha(npth),'reconstruction_program':str(program),'reconstruction_program_sha256':sha(program),'regions':records,'method':'Existing local Photo material plus source median profiles on3 horizontal bands and11 source-line segments; original sloping frame retained.','new_local_passes':0,'new_external_calls':0,'pages':pages,'runtime_verified':False,'release_eligible':False};Q.write_text(json.dumps(data,ensure_ascii=False,indent=2),'utf8');print('496 source profiles /6 review pages saved.')
if __name__=='__main__':main()
