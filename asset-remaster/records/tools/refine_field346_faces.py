"""Keep straight measured faces and their bevel shade instead of blurred cylinders."""
import json,hashlib
from pathlib import Path
import numpy as np,cv2
from scipy.ndimage import gaussian_filter,gaussian_filter1d
from scipy.interpolate import PchipInterpolator
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];Q=R/'qa/field_geometry004_faces_v3.json';assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
two=json.loads((R/'qa/field_geometry004_refined.json').read_text('utf8'));v=next(v for v in two['files'] if v['group_id']=='FM0346');one=json.loads((R/'qa/field_geometry004_trials.json').read_text('utf8'));v1=next(v for v in one['files'] if v['group_id']=='FM0346')
s=np.asarray(Image.open(v['source']).convert('RGBA'));p=np.asarray(Image.open(v['parent']).convert('RGBA'));base=np.load(v1['base_planes'])['rgb'].copy();phase=np.array(v['recipe']['source_phase_rgb'],np.float32)
profiles={'bright':phase[:,:2].mean(1),'shaded':phase[:,2:5].mean(1),'shadow':phase[:,5]}
classes=np.zeros((256,256),np.uint8);classes[:128]=1
for x0 in range(0,32,6):
 for label,a,b,key in [(2,x0,min(x0+2,32),'bright'),(3,x0+2,min(x0+5,32),'shaded'),(4,x0+5,min(x0+6,32),'shadow')]:
  if a>=32:continue
  pr=gaussian_filter1d(profiles[key],.5,axis=0,mode='nearest');base[128:,a*8:b*8]=cv2.resize(pr[:,None,:],((b-a)*8,128),interpolation=cv2.INTER_LINEAR);classes[128:,a*8:b*8]=label
assert np.all(classes>0)
grain=p[:,:,:3].astype('float32')-gaussian_filter(p[:,:,:3].astype('float32'),(2,2,0),mode='nearest');out=p.copy();out[:,:,:3]=np.rint(np.clip(base+np.clip(grain*.4,-2,2),0,255)).astype('uint8');out[:,:,3]=255
O=R/'workspace/local-sr/field-geometry004';ident='FM0346-source-faces-bevel-v3';op=O/(ident+'-8x.png');bp=O/(ident+'-base.npz');mp=O/(ident+'-classes.png');Image.fromarray(out).save(op);np.savez_compressed(bp,rgb=base);Image.fromarray(classes).save(mp)
row={**{k:v[k] for k in ['group_id','source','source_ptm','source_ptm_sha256','source_rgba_sha256','parent','parent_sha256']},'id':ident,'output':str(op),'output_sha256':sha(op),'base_planes':str(bp),'base_planes_sha256':sha(bp),'region_classmap':str(mp),'region_classmap_sha256':sha(mp),'source_phase_rgb':phase.tolist(),'source_profiles_rgb':{k:a.tolist() for k,a in profiles.items()},'phase_regions':{'bright':[0,2],'shaded':[2,5],'shadow':[5,6]},'period_source':6,'lower_source_y':16,'profile_smoothing_sigma_source_y':.5,'grain_sigma_output':2,'grain_gain':.4,'grain_bound':2,'method':'Source6-pixel repeat divided into2-pixel bright face,3-pixel shaded face and1-pixel darker bevel, original vertical illumination, bounded local WDN grain. No black gaps or new neural inference.','runtime_verified':False,'release_eligible':False}
can=Image.new('RGB',(930,302),'#26333f');d=ImageDraw.Draw(can);font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17)
for j,(im,title) in enumerate([(Image.fromarray(s).resize((256,256),Image.Resampling.NEAREST),'원본 · 단순 확대'),(Image.open(v['output']),'곡면 보간 · 이전 수정'),(Image.fromarray(out),'직선 면·홈 음영 구분')]):d.text((j*310+6,5),'FM0346 '+title,font=font,fill='white');can.paste(im.convert('RGB'),(j*310+6,38))
pp=R/'outputs/field-geometry004/FM0346-whole-v3.png';can.save(pp)
# Compare ornamental center traces with weighted original highlight centers.
cv=next(z for z in one['files'] if z['group_id']=='FM0347');cs=np.asarray(Image.open(cv['source']).convert('RGB'));cl=cs.mean(2);diagnostics=[]
for curve in cv['curve_centers']:
 fit=PchipInterpolator(curve['source_y'],curve['source_x'],extrapolate=True)
 for y in [18,20,22,25,27,29]:
  pred=float(fit(y+.5));lo=max(0,int(np.floor(pred-2)));hi=min(64,int(np.ceil(pred+2))+1);xx=np.arange(lo,hi)+.5;weight=np.maximum(cl[y,lo:hi]-np.median(cl[y])-3,0)
  if weight.sum()>0:
   observed=float(np.average(xx,weights=weight));diagnostics.append({'repeat':curve['repeat'],'direction':curve['direction'],'source_y':y,'predicted_x_at_pixel_center':pred,'source_highlight_centroid_x':observed,'difference_source_px':pred-observed,'weight':float(weight.sum())})
diff=[abs(z['difference_source_px']) for z in diagnostics]
Q.write_text(json.dumps({'schema':'brs-source-repeat-refinement/v3','parent_report_sha256':sha(R/'qa/field_geometry004_refined.json'),'files':[row],'pages':[{'path':str(pp),'sha256':sha(pp),'review_status':'pending'}],'FM0347_curve_diagnostics':{'samples':diagnostics,'absolute_error_median_source_px':float(np.median(diff)),'absolute_error_p95_source_px':float(np.percentile(diff,95)),'limit':'Weighted highlight centers at six rows per curve, not exact source geometry or runtime proof. Aliased shading and crossing support affect centroids.'},'new_neural_passes':0,'external_calls':0},ensure_ascii=False,indent=2),'utf8')
print(json.dumps({'output':str(op),'curve_samples':len(diagnostics),'curve_centroid_median_error':float(np.median(diff)),'curve_centroid_p95_error':float(np.percentile(diff,95))}))
