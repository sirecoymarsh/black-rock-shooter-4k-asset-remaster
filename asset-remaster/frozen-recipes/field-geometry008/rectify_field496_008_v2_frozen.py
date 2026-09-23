"""Source-anchored coordinate correction while retaining full local stone material."""
from pathlib import Path
import json,hashlib,shutil
import numpy as np,cv2
from scipy.ndimage import gaussian_filter,gaussian_filter1d,median_filter
from PIL import Image,ImageDraw,ImageFont

def build(s,p):
 rgb=p[:,:,:3].astype('float32');h,w=rgb.shape[:2];yy,xx=np.mgrid[0:h,0:w].astype('float32');sourcey=(np.arange(h)+.5)/8;gray=gaussian_filter(rgb.mean(2),(1.25,9),mode='nearest');anchors=[0,18,28.5,30.5,39.5,43,60,63.5,67,128];mode={28.5:'min',30.5:'max',39.5:'min',63.5:'max'};curves=[];records=[]
 for y in anchors:
  if y not in mode:curve=np.full(w,y,dtype='float32')
  else:
   lo=max(0,int((y-1.35)*8));hi=min(h,int((y+1.35)*8)+1);region=gray[lo:hi];indices=np.argmin(region,axis=0) if mode[y]=='min' else np.argmax(region,axis=0);curve=(lo+indices+.5).astype('float32')/8;curve=gaussian_filter1d(median_filter(curve,size=25,mode='nearest'),12,mode='nearest');records.append({'kind':'horizontal_anchor','source_y':y,'detector':mode[y],'parent_y_minmax':[float(curve.min()),float(curve.max())],'parent_y_median':float(np.median(curve)),'search_radius_source':1.35})
  curves.append(curve)
 curves=np.asarray(curves);assert np.all(np.diff(curves,axis=0)>0);mapy=np.empty((h,w),np.float32)
 for x in range(w):mapy[:,x]=np.interp(sourcey,anchors,curves[:,x])*8-.5
 base=cv2.remap(rgb,xx,mapy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE);maps={'horizontal_mapy':mapy,'horizontal_parent_anchors':curves};last=base.copy();mask=np.abs(mapy-yy)>1e-4
 lines=[('upper-left',[57.5,40.5],[57.5,63.5],'min'),('upper-right',[182.5,40.5],[182.5,63.5],'min'),('recess',[117.5,64.5],[117.5,94.5],'min'),('lower-left',[9.5,96.5],[9.5,128.],'min'),('plate-left',[145.2,101.],[153.64,128.],'min'),('plate-right',[190.75,100.],[182.5,128.],'min'),('plate-top',[148.,100.5],[187.,100.5],'max'),('plate-bottom',[156.,127.],[181.,127.],'max'),('lower-horizontal',[196.,107.5],[256.,107.5],'min'),('lower-thin',[226.5,109.],[226.5,128.],'min'),('lower-dark',[242.5,109.],[242.5,128.],'min')]
 for name,start,end,polarity in lines:
  a=np.asarray(start);b=np.asarray(end);v=b-a;length=float(np.linalg.norm(v));tan=v/length;normal=np.array([-tan[1],tan[0]]);along=((xx+.5)/8-a[0])*tan[0]+((yy+.5)/8-a[1])*tan[1];dist=((xx+.5)/8-a[0])*normal[0]+((yy+.5)/8-a[1])*normal[1];pos=np.linspace(0,length,max(16,round(length*4)));ds=np.linspace(-1.5,1.5,49);samplepoints=a[None,None,:]+pos[:,None,None]*tan[None,None,:]+ds[None,:,None]*normal[None,None,:];smooth=gaussian_filter(last.mean(2),1.25,mode='nearest');samples=cv2.remap(smooth,(samplepoints[:,:,0]*8-.5).astype('float32'),(samplepoints[:,:,1]*8-.5).astype('float32'),cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE);idx=np.argmin(samples,1) if polarity=='min' else np.argmax(samples,1);offset=ds[idx];offset=gaussian_filter1d(median_filter(offset,size=9,mode='nearest'),4,mode='nearest');delta=np.interp(along,pos,offset);weight=np.clip((3.-abs(dist))/1.1,0,1)*np.clip(along/.6,0,1)*np.clip((length-along)/.6,0,1);mx=(xx+delta*weight*normal[0]*8).astype('float32');my=(yy+delta*weight*normal[1]*8).astype('float32');new=cv2.remap(last,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE);affected=weight>0;last[affected]=new[affected];mask|=affected;maps[name+'-offset']=offset;records.append({'kind':'source_segment_anchor','name':name,'source_start':start,'source_end':end,'detector':polarity,'sample_along_source':pos.tolist(),'parent_normal_offset_source':offset.tolist(),'normal_offset_range':[float(offset.min()),float(offset.max())],'median_cross_contrast':float(np.median(samples.max(1)-samples.min(1))),'support_halfwidth_source':3.,'material':'Coordinate remap only; no painted row profile, shade bands or invented grain.'})
 out=np.dstack([np.rint(np.clip(last,0,255)).astype('uint8'),p[:,:,3]]);assert np.array_equal(out[~mask],p[~mask]);assert np.isfinite(last).all();return out,mask,maps,records

def main():
 R=Path(__file__).resolve().parents[1];O=R/'workspace/local-sr/field-geometry008';P=R/'outputs/field-geometry008';Q=R/'qa/field_geometry008_facade496_v2.json';assert not Q.exists()
 def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
 prior=json.loads((R/'qa/field_geometry008_facade496_v1.json').read_text('utf8'));s=np.asarray(Image.open(prior['source']).convert('RGBA'));p=np.asarray(Image.open(prior['parent']).convert('RGBA'));out,mask,maps,records=build(s,p);op=O/'FM0496-source-anchored-material-v2-8x.png';Image.fromarray(out).save(op);mp=O/'FM0496-source-anchored-material-v2-mask.png';Image.fromarray(mask.astype('uint8')*255).save(mp);npth=O/'FM0496-source-anchored-material-v2-maps.npz';np.savez_compressed(npth,**maps);program=O/'rectify_field496_008_v2_frozen.py';shutil.copy2(Path(__file__),program)
 # Editable guide lists desired source lines, not painted image content.
 elems=['<svg xmlns="http://www.w3.org/2000/svg" width="2048" height="1024" viewBox="0 0 256 128">']
 for z in records:
  if z['kind']=='horizontal_anchor':x1,y1,x2,y2=0,z['source_y'],256,z['source_y']
  else:(x1,y1),(x2,y2)=z['source_start'],z['source_end']
  elems.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="white" stroke-width=".1"/>')
 vp=O/'FM0496-source-anchored-material-v2-guide.svg';vp.write_text(''.join(elems)+'</svg>','utf8');font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17);pages=[]
 for tag,box in [('whole',None),('cornice',(44,12,84,52)),('recess',(98,52,138,92)),('left-plate',(136,88,176,128)),('right-plate',(168,88,208,128)),('right-joints',(216,88,256,128))]:
  can=Image.new('RGB',(1050,410),'#25313c');d=ImageDraw.Draw(can)
  for col,(a,title) in enumerate([(s,'원본 · 단순 확대'),(p,'로컬 Photo'),(out,'원본 선 고정·재질 유지 v2')]):
   im=Image.fromarray(a)
   if box:im=im.crop(box if col==0 else tuple(t*8 for t in box));sc=8 if col==0 else 1
   else:sc=min(320/im.width,340/im.height)
   pic=im.resize((round(im.width*sc),round(im.height*sc)),Image.Resampling.NEAREST if col==0 else Image.Resampling.LANCZOS);d.text((col*350+8,8),'FM0496 '+title,font=font,fill='white');can.paste(pic.convert('RGB'),(col*350+(350-pic.width)//2,48+(340-pic.height)//2))
  pp=P/f'FM0496-v2-{tag}.png';can.save(pp);pages.append({'path':str(pp),'sha256':sha(pp),'source_box':box,'review_status':'pending'})
 report={**{k:prior[k] for k in ['group_id','source','source_ptm','source_ptm_sha256','source_rgba_sha256','source_audit_sha256','parent','parent_sha256']},'id':'FM0496-source-anchored-material-v2','previous_report_sha256':sha(R/'qa/field_geometry008_facade496_v1.json'),'output':str(op),'output_sha256':sha(op),'mask':str(mp),'mask_sha256':sha(mp),'maps':str(npth),'maps_sha256':sha(npth),'vector':str(vp),'vector_sha256':sha(vp),'reconstruction_program':str(program),'reconstruction_program_sha256':sha(program),'anchors':records,'method':'Source line targets with bounded local coordinate remapping of existing Photo RGB. Full material retained; no constant row painting.','v1_rejected_reason':'Median-row painting lost broad stone variation, created visible flat shade bands and made bevels look soft; changing grain strength alone is not the fix.','new_local_passes':0,'new_external_calls':0,'pages':pages,'runtime_verified':False,'release_eligible':False};Q.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8');print('496 coordinate remap v2 /6 pages saved.')
if __name__=='__main__':main()
