import json,hashlib
from pathlib import Path
import numpy as np,cv2
from scipy.signal import find_peaks
from scipy.ndimage import gaussian_filter1d
from PIL import Image
R=Path(__file__).resolve().parents[1];Q=R/'qa/field_sr002_geometry_audit.json';assert not Q.exists();rep=json.loads((R/'qa/field_sr002_inference.json').read_text('utf8'));rows={v['id']:v for v in rep['files']};d=json.loads((R/'qa/field_sr002_details.json').read_text('utf8'))
def raw(im):return hashlib.sha256(im.convert('RGBA').tobytes()).hexdigest()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def components(mask,minsize):
 n,l,st,_=cv2.connectedComponentsWithStats(mask.astype('uint8'),8);valid=[i for i in range(1,n) if st[i,cv2.CC_STAT_AREA]>=minsize];return [{'pixels':int(st[i,4]),'box':[int(x) for x in st[i,:4]]} for i in valid]
diag=[]
for v in d['line_diagnostics']:
 if v['group_id'] not in ['FM0147','FM0161']:continue
 z={'group_id':v['group_id'],'source_common_sigma_px':.5,'counts_by_prominence':{},'interpretation':'One common source-coordinate smoothing scale suppresses source dithering; sensitivity is reported at every threshold. These are profile extrema, not physical slat counts.'}
 for tag,w in v['values'].items():
  a=np.asarray(w['profile_0_255']);sc=1 if tag=='source' else 8;filtered=gaussian_filter1d(a,.5*sc);z['counts_by_prominence'][tag]={str(p):len(find_peaks(-filtered,prominence=p,distance=3*sc)[0]) for p in [6,10,14,18,24]}
 diag.append(z)
hazards=[]
for gid,tag in [('FM0137','wdn'),('FM0148','photo'),('FM0149','photo'),('FM0152','photo')]:
 v=rows[gid+'-'+tag];s=Image.open(v['source']).convert('RGBA');o=Image.open(v['output']).convert('RGBA');arrays=[np.asarray(im.convert('RGB'),float) for im in [s,o]];masks=[(a[:,:,0]>70)&(a[:,:,1]>70)&(a[:,:,0]>a[:,:,2]*1.7)&(a[:,:,1]>a[:,:,2]*1.7) for a in arrays];cs=components(masks[0],4);co=components(masks[1],256);down=np.asarray(Image.fromarray(masks[1].astype('uint8')*255).resize(s.size,Image.Resampling.BOX))>=128;union=np.logical_or(masks[0],down).sum();iou=float(np.logical_and(masks[0],down).sum()/union);means=[a[m].mean(0).tolist() for a,m in zip(arrays,masks)]
 hazards.append({'id':v['id'],'threshold':'R,G>70 and R,G>1.7B','source_yellow_regions_ge4px':cs,'output_yellow_regions_ge256px':co,'region_count_match':len(cs)==len(co),'source_vs_downsample_yellow_IoU':iou,'mean_rgb_yellow_source_output':means,'interpretation':'Yellow connected regions only; edge AA and thresholding affect boundaries. Not exact full-colored geometry/phase or native UV proof.'})
grid=json.loads((R/'qa/field_grid003.json').read_text('utf8'));s=Image.open(grid['source']).convert('RGBA');o=Image.open(grid['output']).convert('RGBA');p=Image.open(grid['parent']).convert('RGBA');assert raw(s)==grid['source_rgba_sha256'];assert sha(grid['parent'])==grid['parent_sha256']
for k in ['source_ptm','vector','render','mask','output','comparison']:assert sha(grid[k])==grid[k+'_sha256']
box=tuple(grid['source_box']);a=np.asarray(s.crop(box));b=np.asarray(o.crop(tuple(x*8 for x in box)));lo=a[:,:,:3].mean(2)<95;hi=b[:,:,:3].mean(2)<95;want=np.repeat(np.repeat(lo,8,axis=0),8,axis=1);assert np.array_equal(want,hi);assert len(components(lo,1))==len(components(hi,1))==16
core=[]
for c in grid['cells']:
 x,y=c['source_pixel'];region=np.asarray(o)[y*8:(y+1)*8,x*8:(x+1)*8];assert np.all(region==np.asarray(c['source_rgba']));core.append({'source_pixel':[x,y],'rgba_exact_output_pixels':64})
mask=np.asarray(Image.open(grid['mask']))>0;assert np.array_equal(np.asarray(o)[~mask],np.asarray(p)[~mask]);assert o.getchannel('A').getextrema()==(255,255);assert len(grid['bars'])==10
gcheck={'id':grid['id'],'source_grid_components':16,'output_grid_components':16,'dark_class_threshold_mean_RGB':95,'complete_class_mask_equal_source_nearest':True,'dark_cell_core_rgb_exact':core,'bar_count_per_axis':5,'bar_positions_source_fixed':True,'outside_edit_mask_rgba_exact':True,'opaque255':True,'edit_pixels':int(mask.sum()),'source_ptm_rgba_parent_svg_mask_output_hashes_verified':True,'interpretation':'Geometric source reconstruction with source-colored bar gradients. No new neural inference or recovered fine raster detail. Material/frame outside patch remains the previously inspected Photo output.'}
report={'schema':'brs-field-geometry-audit/v2','line_threshold_sensitivity':diag,'hazard_regions':hazards,'connected_grid_check':gcheck,'runtime_verified':False};Q.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8');print(json.dumps({'profiles':diag,'hazards':[{'id':v['id'],'source_regions':len(v['source_yellow_regions_ge4px']),'output_regions':len(v['output_yellow_regions_ge256px']),'IoU':v['source_vs_downsample_yellow_IoU']} for v in hazards],'grid':gcheck['source_grid_components']},ensure_ascii=False))
