"""Measure native source raster checker edges against generated candidates."""
import json,hashlib
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter1d
from PIL import Image
R=Path(__file__).resolve().parents[1];Q=R/'qa/local_sr015_edge_audit.json'
if Q.exists():raise SystemExit('Existing audit')
rep=json.loads((R/'qa/local_sr015_gpt_floor.json').read_text('utf8'));row=rep['files'][1];src=Image.open(row['source']).convert('RGB');a=np.asarray(src,dtype=float).mean(2)
g=np.asarray(Image.open(row['output']).convert('RGB'),float).mean(2);factor=g.shape[0]/a.shape[0]
old=json.loads((R/'qa/local_sr014_reconstruction.json').read_text('utf8'));patches=next(r for r in old['files'] if r['group_id']=='BM201')['patches']
def edge(v,scale,axis,other,expected,sign):
 # A three-source-pixel perpendicular strip; use median to limit isolated grain.
 center=int(round((other+.5)*scale-.5));lo=max(0,center-round(scale));hi=min(v.shape[1-axis],center+round(scale)+1)
 strip=np.median(v[lo:hi,:],axis=0) if axis==0 else np.median(v[:,lo:hi],axis=1)
 sm=gaussian_filter1d(strip,max(.4,scale*.35),mode='nearest');grad=np.gradient(sm)*sign
 coords=(np.arange(len(grad))+.5)/scale
 valid=(coords>=expected-2.5)&(coords<=expected+2.5)
 ids=np.flatnonzero(valid);peak=ids[np.argmax(grad[valid])]
 local=valid&(abs(coords-coords[peak])<=.75);weights=np.maximum(grad[local],0)
 if weights.sum()<1e-6:return None
 return float((coords[local]*weights).sum()/weights.sum()),float(grad[peak]*scale)
out=[]
for p in patches:
 cells={(c['column'],c['row']):c for c in p['cells'] if c['source_samples']>=25};samples=[]
 for ij,c in cells.items():
  x0,y0,x1,y1=c['source_bounds'];cx=int((x0+x1)/2);cy=int((y0+y1)/2);mean=float(a[cy-1:cy+2,cx-1:cx+2].mean())
  for axis,key in [(0,(ij[0]+1,ij[1])),(1,(ij[0],ij[1]+1))]:
   if key not in cells:continue
   n=cells[key];nx0,ny0,nx1,ny1=n['source_bounds'];nx=int((nx0+nx1)/2);ny=int((ny0+ny1)/2);delta=float(a[ny-1:ny+2,nx-1:nx+2].mean())-mean
   if abs(delta)<20:continue
   expected=x1 if axis==0 else y1;other=cy if axis==0 else cx;sign=np.sign(delta)
   se=edge(a,1,axis,other,expected,sign);ge=edge(g,factor,axis,other,expected,sign)
   if se is None or ge is None or se[1]<10 or ge[1]<10:continue
   samples.append({'axis':'x' if axis==0 else 'y','pair':[ij,key],'perpendicular_source_coordinate':other,'source_raster_edge':se[0],'generated_edge_source_units':ge[0],'offset_source_pixels':ge[0]-se[0],'source_peak_gradient':se[1],'generated_peak_gradient':ge[1]})
 fit={}
 for axis in ['x','y']:
  rows=[s for s in samples if s['axis']==axis];x=np.array([s['source_raster_edge'] for s in rows]);y=np.array([s['generated_edge_source_units'] for s in rows]);keep=np.ones(len(x),bool)
  if len(x)<4:continue
  for _ in range(3):
   coef=np.polyfit(x[keep],y[keep],1);res=y-np.polyval(coef,x);keep=np.abs(res)<max(.65,2.5*np.median(np.abs(res)))
  fit[axis]={'source_to_generated_scale':float(coef[0]),'source_to_generated_offset':float(coef[1]),'samples':len(x),'fit_inliers':int(keep.sum()),'median_abs_offset_source_pixels':float(np.median(np.abs(y-x))),'p95_abs_offset_source_pixels':float(np.quantile(np.abs(y-x),.95)),'fit_p95_abs_residual_source_pixels':float(np.quantile(np.abs(res[keep]),.95))}
 out.append({'patch':p['id'],'fits':fit,'samples':samples})
Q.write_text(json.dumps({'schema':'brs-sr015-edge-audit/v1','source':row['source'],'source_rgba_sha256':row['source_rgba_sha256'],'candidate':row['output'],'candidate_sha256':row['output_sha256'],'patches':out,'limits':['Measures visible source raster transitions only; original continuous HD edges remain unknown.','Strong source contrasts >=20/255, 3-source-pixel perpendicular medians, +/-2.5-source-pixel search. Not every edge or occluded cell is measured.','Measured geometric offsets do not establish UV/runtime consumer correctness.'],'runtime_verified':False},ensure_ascii=False,indent=2),'utf8')
print(json.dumps({p['patch']:p['fits'] for p in out}))
