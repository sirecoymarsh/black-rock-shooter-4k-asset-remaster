"""Reduce an over-interpreted small crack using source dark coverage, one local edit."""
import json,hashlib
from pathlib import Path
import numpy as np,cv2
from scipy.ndimage import distance_transform_edt,gaussian_filter
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];Q=R/'qa/local_sr015_small_repair.json';O=R/'workspace/gpt-trials/BM201-v1'
if Q.exists():raise SystemExit('Existing repair')
q=json.loads((R/'qa/local_sr015_gpt_floor.json').read_text('utf8'));r=q['files'][1];src=Image.open(r['source']).convert('RGBA');par=Image.open(r['output']).convert('RGBA');a=np.asarray(src);b=np.asarray(par);W,H=par.size
def sha(x):return hashlib.sha256(x).hexdigest()
def save(im,n):
 p=O/n;im.save(p);return str(p),sha(p.read_bytes())
assert sha(Path(r['output']).read_bytes())==r['output_sha256']
line=[(212.0,210.5),(212.0,214.0),(213.7,218.0),(215.1,221.0),(214.4,226.0),(213.4,229.0),(211.5,232.0),(213.0,234.5),(214.5,238.0),(216.0,241.0),(218.5,244.0)]
edit=Image.new('L',par.size);d=ImageDraw.Draw(edit);d.line([(round(x*8),round(y*8)) for x,y in line],fill=255,width=round(3.5*8),joint='curve')
for x,y in line:d.ellipse((x*8-14,y*8-14,x*8+14,y*8+14),fill=255)
mask=np.asarray(edit)>0
# Clip edit to an independently observed floor interior; do not touch the enclosing plate rim.
poly=[(211.5,210),(216,208),(220,209),(224,211),(225,216),(225,222),(224,229),(224,238),(221,244),(218,246),(213,241),(209,237),(207,231),(207,223),(208,218)]
roi=Image.new('L',par.size);ImageDraw.Draw(roi).polygon([(x*8,y*8) for x,y in poly],fill=255);mask&=np.asarray(roi)>0
soft=np.clip(distance_transform_edt(mask)/2.,0,1)
mp,mh=save(Image.fromarray(np.rint(soft*255).astype('uint8')),'BM201-small-edit-mask8x.png')
# Checker boundaries measured from this coherent repaint (native-source units). Local fills never borrow across them.
xs=[204.95,215.50,225.35,235.55];ys=[206.75,217.02,227.24,237.50,247.75]
filled=b[:,:,:3].copy();cells=[]
for j,(y0,y1) in enumerate(zip(ys,ys[1:])):
 for i,(x0,x1) in enumerate(zip(xs,xs[1:])):
  xa,xb,ya,yb=round(x0*8),round(x1*8),round(y0*8),round(y1*8);sub=b[ya:yb,xa:xb,:3].copy();sm=mask[ya:yb,xa:xb]
  if not sm.any():continue
  # The one-cell crop is reflected before inpainting, preserving the corresponding tile's color at its edge.
  pad=24;v=cv2.copyMakeBorder(sub,pad,pad,pad,pad,cv2.BORDER_REFLECT_101);mm=cv2.copyMakeBorder(sm.astype('uint8')*255,pad,pad,pad,pad,cv2.BORDER_REFLECT_101)
  healed=cv2.inpaint(v,mm,12,cv2.INPAINT_TELEA)[pad:-pad,pad:-pad]
  filled[ya:yb,xa:xb]=healed;cells.append({'column':i,'row':j,'generated_source_unit_bounds':[x0,y0,x1,y1],'edited_output_pixels':int(sm.sum())})
fillp,fillh=save(Image.fromarray(filled),'BM201-small-healed-underlay.png')
# Preserve actual source dark fragments; do not interpret every dark checker tile as a crack.
source_roi=Image.new('L',src.size);ImageDraw.Draw(source_roi).line(line,fill=255,width=3)
dark=(a[:,:,0]<=21)&(np.asarray(source_roi)>0)
dp,dh=save(Image.fromarray(dark.astype('uint8')*255),'BM201-small-source-dark-fragments.png')
coverage=Image.fromarray(dark.astype('uint8')*255).resize(par.size,Image.Resampling.BICUBIC)
cov=np.asarray(coverage,dtype=float)/255.;cov=np.clip((cov-.12)/.76,0,1)
source_nearest=np.asarray(Image.fromarray(a[:,:,:3]).resize(par.size,Image.Resampling.NEAREST))
near=distance_transform_edt(~dark,return_distances=False,return_indices=True);dark_colors=a[near[0],near[1],:3]
dark8=np.asarray(Image.fromarray(dark_colors).resize(par.size,Image.Resampling.BILINEAR),float)
files=[]
for strength in [1.,.7]:
 c=cov*strength;paint=filled.astype(float)*(1-c[:,:,None])+dark8*c[:,:,None];out=b.copy();out[:,:,:3]=np.rint(np.clip(paint*soft[:,:,None]+b[:,:,:3]*(1-soft[:,:,None]),0,255)).astype('uint8')
 im=Image.fromarray(out);op,oh=save(im,f'BM201-small-source-crack-{strength:.1f}.png');assert np.array_equal(out[~mask],b[~mask])
 files.append({'id':f'BM201-small-source-crack-{strength:.1f}','group_id':'BM201','source':r['source'],'source_rgba_sha256':r['source_rgba_sha256'],'parent':r['output'],'parent_sha256':r['output_sha256'],'mask':mp,'mask_sha256':mh,'underlay':fillp,'underlay_sha256':fillh,'source_fragment_mask':dp,'source_fragment_mask_sha256':dh,'source_fragment_pixels':int(dark.sum()),'source_dark_strength':strength,'source_observed_crack_corridor':line,'checker_cell_fills':cells,'output':op,'output_sha256':oh,'output_size':list(im.size),'method':'Within-cell local inpainting for over-emphasized generated crack, followed by source dark-fragment restoration; original repaint exact outside the authored edit mask.','new_neural_passes':0,'new_generative_calls':0,'visual_review':'pending','runtime_verified':False,'release_eligible':False})
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18);pages=[]
for k,box in enumerate([(194,197,249,253),(0,0,256,256)]):
 w=512;h=round(w*(box[3]-box[1])/(box[2]-box[0]));rh=h+55;s=Image.new('RGB',(1064,rh*2),'#293440');d=ImageDraw.Draw(s)
 ims=[(src,'원본 단순 확대'),(par,'전체 재작화 · 균열이 과장됨')]+[(Image.open(f['output']),f['id']) for f in files]
 for i,(im,t) in enumerate(ims):
  x=i%2*532+8;y=i//2*rh+8;d.text((x,y),t,font=font,fill='white');im=im.crop(box if i==0 else tuple(z*8 for z in box)).resize((w,h),Image.Resampling.NEAREST if i==0 else Image.Resampling.LANCZOS);s.paste(im.convert('RGB'),(x,y+32))
 p=R/f'outputs/sr015-BM201-small-repair-{k}.png';s.save(p);pages.append(str(p))
Q.write_text(json.dumps({'schema':'brs-sr015-small-crack-repair/v1','files':files,'comparison_sheets':pages,'new_neural_passes':0,'new_generative_calls':0,'runtime_verified':False,'release_eligible':False},ensure_ascii=False,indent=2),'utf8')
print(json.dumps({'outputs':2,'source_dark_fragments':int(dark.sum()),'edited_pixels':int(mask.sum())}))
