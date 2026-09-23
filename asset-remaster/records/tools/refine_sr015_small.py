"""Replace smeared inpainting with same-cell texture donors; preserve source dark cores."""
import json,hashlib
from pathlib import Path
import numpy as np
from scipy.ndimage import distance_transform_edt
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];Q=R/'qa/local_sr015_small_texture.json'
if Q.exists():raise SystemExit('Existing texture repair')
r=json.loads((R/'qa/local_sr015_small_repair.json').read_text('utf8'))['files'][0];O=Path(r['output']).parent
par=Image.open(r['parent']).convert('RGBA');src=Image.open(r['source']).convert('RGBA');a=np.asarray(src);p=np.asarray(par);mask=np.asarray(Image.open(r['mask']).convert('L'),float)/255.;hard=mask>0;fill=p[:,:,:3].copy();donors=[]
def sha(b):return hashlib.sha256(b).hexdigest()
for cell in r['checker_cell_fills']:
 x0,y0,x1,y1=cell['generated_source_unit_bounds'];xa,xb,ya,yb=round(x0*8),round(x1*8),round(y0*8),round(y1*8);m=hard[ya:yb,xa:xb];v=p[ya:yb,xa:xb,:3];h,w=m.shape;yy,xx=np.indices((h,w));valid=~m;valid[:3]=False;valid[-3:]=False;valid[:,:3]=False;valid[:,-3:]=False
 assert valid.any();near=distance_transform_edt(~valid,return_distances=False,return_indices=True);dy,dx=near[0].copy(),near[1].copy();done=np.zeros(m.shape,bool)
 # Prefer a translated material sample from the same scanline and checker cell, avoiding an artificial smooth fill.
 for shift in [round(w*.45),-round(w*.45),round(w*.3),-round(w*.3)]:
  cand=xx+shift;safe=(cand>=3)&(cand<w-3);clipped=np.clip(cand,0,w-1);ok=m&~done&safe&valid[yy,clipped];dx[ok]=clipped[ok];dy[ok]=yy[ok];done|=ok
 out=v.copy();out[m]=v[dy[m],dx[m]];fill[ya:yb,xa:xb]=out
 donors.append({'cell':cell,'translated_scanline_donors':int(done.sum()),'nearest_same_cell_donors':int((m&~done).sum()),'outside_cell_donors':0})
dark=np.asarray(Image.open(r['source_fragment_mask']))>0;coverage=Image.fromarray(dark.astype('uint8')*255).resize(par.size,Image.Resampling.BICUBIC);cov=np.clip((np.asarray(coverage,float)/255.-.12)/.76,0,1)
near=distance_transform_edt(~dark,return_distances=False,return_indices=True);colors=a[near[0],near[1],:3];dc=np.asarray(Image.fromarray(colors).resize(par.size,Image.Resampling.BILINEAR),float)
paint=fill*(1-cov[:,:,None])+dc*cov[:,:,None];out=p.copy();out[:,:,:3]=np.rint(np.clip(paint*mask[:,:,None]+p[:,:,:3]*(1-mask[:,:,None]),0,255)).astype('uint8');assert np.array_equal(out[~hard],p[~hard])
im=Image.fromarray(out);op=O/'BM201-small-source-texture-v2.png';im.save(op);up=O/'BM201-small-same-cell-underlay.png';Image.fromarray(fill).save(up)
row={**{k:r[k] for k in ['group_id','source','source_rgba_sha256','parent','parent_sha256','mask','mask_sha256','source_fragment_mask','source_fragment_mask_sha256','source_fragment_pixels','source_observed_crack_corridor']},'id':'BM201-small-source-texture-v2','underlay':str(up),'underlay_sha256':sha(up.read_bytes()),'donor_cells':donors,'source_dark_strength':1.0,'output':str(op),'output_sha256':sha(op.read_bytes()),'output_size':list(im.size),'method':'Texture donors restricted to each measured generated checker cell replace the enlarged crack; source dark core coverage restored. No neural inference.','new_neural_passes':0,'new_generative_calls':0,'visual_review':'pending','runtime_verified':False,'release_eligible':False}
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18);pages=[]
for k,box in enumerate([(194,197,249,253),(0,0,256,256)]):
 w=512;h=round(w*(box[3]-box[1])/(box[2]-box[0]));rh=h+55;s=Image.new('RGB',(1064,rh*2),'#293440');d=ImageDraw.Draw(s)
 ims=[(src,'원본 단순 확대'),(par,'전체 재작화 · 균열 과장'),(Image.open(r['output']),'첫 보정 · 재질 번짐으로 제외'),(im,'칸별 재질 복원 · 원본 파손 흔적')]
 for i,(pic,t) in enumerate(ims):
  x=i%2*532+8;y=i//2*rh+8;d.text((x,y),t,font=font,fill='white');pic=pic.crop(box if i==0 else tuple(z*8 for z in box)).resize((w,h),Image.Resampling.NEAREST if i==0 else Image.Resampling.LANCZOS);s.paste(pic.convert('RGB'),(x,y+32))
 pp=R/f'outputs/sr015-BM201-small-texture-{k}.png';s.save(pp);pages.append(str(pp))
Q.write_text(json.dumps({'schema':'brs-sr015-small-texture/v2','files':[row],'comparison_sheets':pages,'new_neural_passes':0,'new_generative_calls':0,'runtime_verified':False,'release_eligible':False},ensure_ascii=False,indent=2),'utf8');print('Saved texture-preserving small-crack repair.')
