"""Fit bounded scroll offsets/width to source coverage, without mirroring it."""
from pathlib import Path
import json,hashlib,re,subprocess,time
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import cKDTree
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];O=R/'workspace/local-sr/field-geometry007';P=R/'outputs/field-geometry007';Q=R/'qa/field_geometry007_ornament533_v3.json';assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text('utf8'))
def arr(p):return np.asarray(Image.open(p).convert('RGBA'))
v=next(z for z in read(R/'qa/field_geometry007_authored_v2.json')['files'] if z['group_id']=='FM0533');s=arr(v['source']);p=arr(v['parent']);frozen=np.load(v['frozen_planes']);under=frozen['base_rgb'];origpaths=v['recipe']['hand_paths'];curves=[]
for path in origpaths:
 nums=np.array([float(t) for t in re.findall(r'-?\d+(?:\.\d+)?',path)]).reshape(-1,2);pts=[];start=nums[0]
 for j in range(1,len(nums),3):
  c1,c2,end=nums[j:j+3];t=np.linspace(0,1,96)[:,None];pts.append((1-t)**3*start+3*(1-t)**2*t*c1+3*(1-t)*t*t*c2+t**3*end);start=end
 curves.append(np.concatenate(pts))
# Inferred opacity is a source fitting target, not native engine transparency.
bg=np.asarray(Image.fromarray(np.rint(under).astype('uint8')).resize((32,128),Image.Resampling.BILINEAR)).astype(float)[110:124];white=np.array([244.,237.,232.]);ss=s[110:124,:,:3].astype(float);direction=white-bg;target=np.clip(np.sum((ss-bg)*direction,2)/np.maximum(np.sum(direction*direction,2),1),0,1)
factor=4;yy,xx=np.mgrid[0:14*factor,0:32*factor];points=np.c_[((xx+.5)/factor).ravel(),(110+(yy+.5)/factor).ravel()]
def predict(par):
 d=np.full(len(points),100.)
 for j,c in enumerate(curves):d=np.minimum(d,cKDTree(c+par[j*2:j*2+2]).query(points,workers=1)[0])
 high=np.clip((par[-1]/2+.16-d)/.32,0,1).reshape(14*factor,32*factor);return high.reshape(14,factor,32,factor).mean((1,3))
def objective(par):return np.r_[(predict(par)-target).ravel(),par[:8]*.10,(par[-1]-1.7)*.025]
initial=np.r_[np.zeros(8),1.7];start=time.monotonic();fit=least_squares(objective,initial,bounds=(np.r_[np.full(8,-.85),1.25],np.r_[np.full(8,.85),2.35]),max_nfev=35,ftol=1e-6,xtol=1e-6,gtol=1e-6);par=fit.x;print('Fit',par.tolist(),'evaluations',fit.nfev,flush=True)
paths=[]
for j,path in enumerate(origpaths):
 nums=np.array([float(t) for t in re.findall(r'-?\d+(?:\.\d+)?',path)]).reshape(-1,2)+par[j*2:j*2+2];d=f'M {nums[0,0]:.6f} {nums[0,1]:.6f}'
 for k in range(1,len(nums),3):d+=' C '+' '.join(f'{z:.6f}' for z in nums[k:k+3].ravel())
 paths.append(d)
svg='<svg xmlns="http://www.w3.org/2000/svg" width="256" height="1024" viewBox="0 0 32 128"><defs><clipPath id="motif"><rect x="0" y="110" width="32" height="14"/></clipPath></defs><g clip-path="url(#motif)" fill="none" stroke="rgb(244,237,232)" stroke-width="'+f'{par[-1]:.6f}'+'" stroke-linecap="round" stroke-linejoin="round">'+''.join('<path d="'+d+'"/>' for d in paths)+'</g><rect x="0" y="109" width="32" height="1" fill="rgb(244,237,232)"/><rect x="0" y="124" width="32" height="1" fill="white"/></svg>'
vp=O/'FM0533-source-fit-v3.svg';rp=O/'FM0533-source-fit-v3-render.png';vp.write_text(svg,'utf8');subprocess.run([r'C:\Users\CadriacLord\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe',str(R/'workspace/local-sr/field-geometry006/render.cjs'),str(vp),str(rp)],check=True);layer=arr(rp);alpha=layer[:,:,3:4]/255.;rgb=np.rint(np.clip(under*(1-alpha)+layer[:,:,:3]*alpha,0,255)).astype('uint8');out=np.dstack([rgb,p[:,:,3]]);assert np.array_equal(out[:832],p[:832]);op=O/'FM0533-source-fit-v3-8x.png';Image.fromarray(out).save(op)
metrics={};sourcewhite=(s[109:125,:,0].astype(int)-s[109:125,:,2].astype(int))<27
for label,path in [('localPhoto',v['parent']),('v2_manual_thin',v['output']),('v3_source_fit',op)]:
 small=np.asarray(Image.open(path).convert('RGB').resize((32,128),Image.Resampling.LANCZOS)).astype(float);whitearea=(small[109:125,:,0]-small[109:125,:,2])<27;metrics[label]={'source_white_class_count':int(sourcewhite.sum()),'output_white_class_count':int(whitearea.sum()),'white_class_IoU':float(np.count_nonzero(sourcewhite&whitearea)/np.count_nonzero(sourcewhite|whitearea)),'RGB_MAE_ornament_native_source_scale':float(np.abs(small[109:125]-s[109:125,:,:3]).mean())}
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17);pages=[]
for tag,box in [('whole',None),('native',(0,96,32,128))]:
 can=Image.new('RGB',(1050,410),'#25313c');d=ImageDraw.Draw(can)
 for col,(path,title) in enumerate([(v['source'],'원본 · 단순 확대'),(v['parent'],'로컬 Photo'),(op,'원본 곡선·폭 대응 v3')]):
  im=Image.open(path).convert('RGBA')
  if box:im=im.crop(box if col==0 else tuple(t*8 for t in box));scale=8 if col==0 else 1
  else:scale=min(320/im.width,340/im.height)
  pic=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST if col==0 else Image.Resampling.LANCZOS);d.text((col*350+8,8),'FM0533 '+title,font=font,fill='white');can.paste(pic.convert('RGB'),(col*350+(350-pic.width)//2,48+(340-pic.height)//2))
 pp=P/f'FM0533-v3-{tag}.png';can.save(pp);pages.append({'path':str(pp),'sha256':sha(pp),'source_box':box,'review_status':'pending'})
z={**v,'id':'FM0533-source-fit-v3','output':str(op),'output_sha256':sha(op),'vector':str(vp),'vector_sha256':sha(vp),'render':str(rp),'render_sha256':sha(rp),'previous_report_sha256':sha(R/'qa/field_geometry007_authored_v2.json'),'recipe':{**v['recipe'],'hand_paths':paths,'stroke_width_source':float(f'{par[-1]:.6f}'),'curve_offsets_source_px':par[:8].reshape(4,2).tolist(),'fitting':'Bounded independent translations±.85source px per each of4 manually authored curves, shared width1.25..2.35; source RGB-implied coverage fit. Source asymmetry retained. This is geometry fitting, not neural inference.','v2_rejected_reason':'Manual width1.25 source px lost too much of the original white footprint; global thinness is not an acceptance criterion.'},'source_scale_diagnostics':metrics,'fit_evaluations':fit.nfev,'fit_seconds':time.monotonic()-start,'local_inference_passes':0,'external_calls':0,'pages':pages};Q.write_text(json.dumps(z,ensure_ascii=False,indent=2),'utf8');print(json.dumps(metrics),flush=True)
