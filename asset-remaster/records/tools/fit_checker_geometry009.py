"""Fit bounded affine checker lattices to original source samples; audit only."""
from pathlib import Path
import json,hashlib
import numpy as np,cv2
from scipy.optimize import least_squares
from scipy.ndimage import distance_transform_edt
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];O=R/'workspace/local-sr/field-geometry009';P=R/'outputs/field-geometry009';Q=R/'qa/field_geometry009_lattice_audit.json'
O.mkdir(exist_ok=True);P.mkdir(exist_ok=True);assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
sources=json.loads((R/'qa/field_geometry008_source_audit.json').read_text('utf8'))['files']
# Polygons bound visibly surviving design, not inferred full undamaged sheets.
specs={
 'FM0394':[{'name':'large','poly':[[65,22],[72,14],[80,14],[86,24],[86,43],[92,56],[98,51],[103,51],[109,42],[116,42],[117,34],[128,34],[128,128],[14,128],[14,89],[19,76],[22,66],[28,57],[29,52],[36,45],[42,40],[47,34],[52,28],[55,24]],'center':[72,25],'vx':[10.25,0],'vy':[0,10.25]}],
 'FM0430':[
  {'name':'middle','poly':[[58,60],[66,61],[71,66],[72,77],[68,85],[66,93],[64,101],[60,106],[55,107],[52,104],[51,97],[54,88],[55,80],[56,72]],'center':[62,66],'vx':[4.1,1.0],'vy':[-.6,4.1]},
  {'name':'left','poly':[[22,39],[26,41],[28,44],[30,51],[30,57],[28,62],[24,66],[22,64],[21,59],[17,53],[17,48],[18,43]],'center':[21,46],'vx':[3.7,-1.6],'vy':[1.3,3.7]},
  {'name':'upper-right','poly':[[121,10],[127,13],[128,19],[127,24],[118,28],[114,31],[106,34],[101,32],[100,28],[103,23],[111,20],[115,15]],'center':[118,19],'vx':[3.5,-1.7],'vy':[1.7,3.5]},
  {'name':'lower-right','poly':[[98,112],[102,115],[104,120],[105,125],[105,128],[93,128],[93,123],[93,118]],'center':[98,123],'vx':[3.7,-1.6],'vy':[1.3,3.7]}]}
records=[];font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',15)
for gid,patches in specs.items():
 src=next(z for z in sources if z['group_id']==gid);im=Image.open(src['source']).convert('RGBA');a=np.asarray(im);gray=a[:,:,:3].mean(2);h,w=gray.shape;yy,xx=np.mgrid[0:h,0:w];xx=xx+.5;yy=yy+.5;whole=Image.new('RGBA',(w*8,h*8));dr=ImageDraw.Draw(whole);recs=[]
 assert sha(src['source_ptm'])==src['source_ptm_sha256'] and hashlib.sha256(a.tobytes()).hexdigest()==src['source_rgba_sha256']
 for spec in patches:
  mask=np.zeros((h,w),np.uint8);cv2.fillPoly(mask,[np.rint(np.array(spec['poly'])*16).astype('int32')],1,shift=4);dist=distance_transform_edt(mask);valid=dist>2 if gid=='FM0394' else dist>1.5
  dx=xx[valid]-spec['center'][0];dy=yy[valid]-spec['center'][1];target=gray[valid];basis=np.array([spec['vx'],spec['vy']]).T;inv=np.linalg.inv(basis);matrix=np.column_stack([np.ones(len(dx)),dx,dy]);init=np.r_[inv.ravel(),0.,0.];bounds=np.array([.012,.008,.008,.012,.35,.35]) if gid=='FM0394' else np.array([.045,.065,.065,.045,.6,.6])
  offsets=[((x+.5)/4-.5,(y+.5)/4-.5) for y in range(4) for x in range(4)]
  def pattern(v,x=dx,y=dy):
   result=np.zeros_like(x,dtype=float)
   for ox,oy in offsets:
    u=v[0]*(x+ox)+v[1]*(y+oy)+v[4];vv=v[2]*(x+ox)+v[3]*(y+oy)+v[5];result+=np.tanh(4*np.cos(np.pi*u))*np.tanh(4*np.cos(np.pi*vv))
   return result/16
  def residual(v,ret=False):
   wave=pattern(v);design=np.column_stack([matrix,wave]);coef=np.linalg.lstsq(design,target,rcond=None)[0];error=design@coef-target
   return (coef,wave,error) if ret else error
  trials=[]
  for phase in [(0,0),(.2,0),(0,.2),(-.2,-.2)]:
   start=init.copy();start[4:]=phase;fit=least_squares(residual,start,bounds=(init-bounds,init+bounds),loss='soft_l1',f_scale=8,max_nfev=120);coef,wave,err=residual(fit.x,True);trials.append((float(np.mean(np.minimum(err*err,35*35))),fit,coef,wave,err))
  _,fit,coef,wave,err=min(trials,key=lambda z:z[0]);m=fit.x;aff=np.array([[m[0],m[1]],[m[2],m[3]]]);b=np.array(spec['center']);phase=m[4:];invfit=np.linalg.inv(aff);uv=np.array(spec['poly'])@aff.T-b@aff.T+phase
  segments=[]
  for axis in [0,1]:
   for boundary in np.arange(np.floor(uv[:,axis].min()-.5)+.5,np.ceil(uv[:,axis].max()+.5),1):
    low=np.floor(uv[:,1-axis].min())-2;high=np.ceil(uv[:,1-axis].max())+2;ends=np.array([[boundary,low],[boundary,high]]) if axis==0 else np.array([[low,boundary],[high,boundary]]);points=(ends-phase)@invfit.T+b;segments.append(points.tolist())
    dr.line([tuple(p*8) for p in points],fill=(255,210,45,190),width=1)
  dr.polygon([tuple(np.array(p)*8) for p in spec['poly']],outline=(50,220,235,255),width=2)
  recs.append({**spec,'source_lattice_parameters':m.tolist(),'fitted_basis':invfit.tolist(),'fitted_color_plane_amplitude':coef.tolist(),'fit_pixel_count':int(valid.sum()),'source_fit_MAE':float(abs(err).mean()),'source_fit_RMSE':float(np.sqrt((err*err).mean())),'source_wave_correlation':float(np.corrcoef(wave,target-matrix@coef[:3])[0,1]),'boundary_segments':segments,'bounds_delta':bounds.tolist(),'note':'Bounded source-intensity fit is supporting evidence; clipping polygon and design geometry still require direct visual review.'})
  print(gid,spec['name'],'MAE',round(abs(err).mean(),2),'amplitude',round(coef[3],2),'basis',np.round(invfit,3).tolist(),flush=True)
 base=im.resize((w*8,h*8),Image.Resampling.NEAREST);base.alpha_composite(whole);pp=P/(gid+'-lattice-audit.png');base.convert('RGB').save(pp);records.append({**src,'patches':recs,'overlay':str(pp),'overlay_sha256':sha(pp)})
out={'schema':'brs-checker-source-lattice-audit009/v1','previous_turn':'progress:008 five new originals/two checker candidates, source and recipe checks completed.','source_records':records,'review_status':'pending','catalog_before_sha256':sha(R/'qa/field_sr_catalog.json'),'geometry_contract_before_sha256':sha(R/'qa/architectural_geometry_contract.json'),'script_sha256':sha(__file__),'new_neural_passes':0,'new_external_calls':0};Q.write_text(json.dumps(out,ensure_ascii=False,indent=2),'utf8')
