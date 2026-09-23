"""Use same-cell luminance-filtered donors; semantic rim exclusion is not proven."""
import json,hashlib
from pathlib import Path
import numpy as np
from scipy.ndimage import distance_transform_edt,gaussian_filter
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];Q=R/'qa/local_sr015_small_texture_v3.json'
if Q.exists():raise SystemExit('Existing v3')
r=json.loads((R/'qa/local_sr015_small_repair.json').read_text('utf8'))['files'][0];O=Path(r['output']).parent
par=Image.open(r['parent']).convert('RGBA');src=Image.open(r['source']).convert('RGBA');a=np.asarray(src);p=np.asarray(par);mask=np.asarray(Image.open(r['mask']).convert('L'),float)/255.;hard=mask>0;fill=p[:,:,:3].copy();donors=[]
def sha(b):return hashlib.sha256(b).hexdigest()
for cell in r['checker_cell_fills']:
 x0,y0,x1,y1=cell['generated_source_unit_bounds'];xa,xb,ya,yb=round(x0*8),round(x1*8),round(y0*8),round(y1*8);m=hard[ya:yb,xa:xb];v=p[ya:yb,xa:xb,:3].astype(float);lum=v.mean(2);h,w=m.shape;light=(cell['column']+cell['row'])%2==0
 valid=~m;valid[:5]=False;valid[-5:]=False;valid[:,:5]=False;valid[:,-5:]=False
 values=lum[valid];cut=float(np.quantile(values,.65 if light else .45));valid&=(lum>=max(cut,45)) if light else (lum<=min(cut+5,45))
 assert valid.any();near=distance_transform_edt(~valid,return_distances=False,return_indices=True)
 sample=v[near[0],near[1]];low=gaussian_filter(sample,(10,10,0),mode='nearest')
 grain=v-gaussian_filter(v,(3,3,0),mode='nearest');detail=grain[near[0],near[1]]
 material=np.clip(low+.65*detail,0,255);sub=v.copy();sub[m]=material[m];fill[ya:yb,xa:xb]=np.rint(sub).astype('uint8')
 donors.append({'cell':cell,'expected_role':'light' if light else 'dark','luminance_donor_cut':cut,'valid_donors':int(valid.sum()),'edited_output_pixels':int(m.sum()),'donor_cell_restriction_verified':True,'luminance_role_filter_applied':True,'rim_exclusion_proven':False})
dark=np.asarray(Image.open(r['source_fragment_mask']))>0;cov=np.asarray(Image.fromarray(dark.astype('uint8')*255).resize(par.size,Image.Resampling.BICUBIC),float)/255.;cov=np.clip((cov-.12)/.76,0,1)
near=distance_transform_edt(~dark,return_distances=False,return_indices=True);dc=np.asarray(Image.fromarray(a[near[0],near[1],:3]).resize(par.size,Image.Resampling.BILINEAR),float)
paint=fill*(1-cov[:,:,None])+dc*cov[:,:,None];out=p.copy();out[:,:,:3]=np.rint(np.clip(paint*mask[:,:,None]+p[:,:,:3]*(1-mask[:,:,None]),0,255)).astype('uint8');assert np.array_equal(out[~hard],p[~hard])
im=Image.fromarray(out);op=O/'BM201-small-source-texture-v3.png';im.save(op);up=O/'BM201-small-matching-role-underlay.png';Image.fromarray(fill).save(up)
row={**{k:r[k] for k in ['group_id','source','source_rgba_sha256','parent','parent_sha256','mask','mask_sha256','source_fragment_mask','source_fragment_mask_sha256','source_fragment_pixels','source_observed_crack_corridor']},'id':'BM201-small-source-texture-v3','underlay':str(up),'underlay_sha256':sha(up.read_bytes()),'donor_cells':donors,'source_dark_strength':1.0,'output':str(op),'output_sha256':sha(op.read_bytes()),'output_size':list(im.size),'method':'Matching light/dark same-cell donors yield an interpolated material field plus fine texture; original source dark fragments restored. No neural inference.','new_neural_passes':0,'new_generative_calls':0,'visual_review':'pending','runtime_verified':False,'release_eligible':False}
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18);box=(194,197,249,253);w=512;h=round(w*56/55);rh=h+55;s=Image.new('RGB',(1064,rh*2),'#293440');d=ImageDraw.Draw(s)
ims=[(src,'원본 단순 확대'),(par,'재작화 · 균열 과장'),(Image.open(O/'BM201-small-source-texture-v2.png'),'v2 · 재질 조각이 보임'),(im,'v3 · 같은 색 칸의 재질로 복원')]
for i,(pic,t) in enumerate(ims):
 x=i%2*532+8;y=i//2*rh+8;d.text((x,y),t,font=font,fill='white');pic=pic.crop(box if i==0 else tuple(z*8 for z in box)).resize((w,h),Image.Resampling.NEAREST if i==0 else Image.Resampling.LANCZOS);s.paste(pic.convert('RGB'),(x,y+32))
page=R/'outputs/sr015-BM201-small-texture-v3.png';s.save(page)
Q.write_text(json.dumps({'schema':'brs-sr015-small-texture/v3','files':[row],'comparison_sheets':[str(page)],'new_neural_passes':0,'new_generative_calls':0,'runtime_verified':False,'release_eligible':False},ensure_ascii=False,indent=2),'utf8');print('Saved matching-role material repair v3.')
