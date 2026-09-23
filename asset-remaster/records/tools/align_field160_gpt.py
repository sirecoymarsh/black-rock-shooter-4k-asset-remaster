"""Register the two central edges of the repaint to measured source edges."""
import json,hashlib
from pathlib import Path
import cv2,numpy as np
from scipy.ndimage import gaussian_filter,gaussian_filter1d
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];Q=R/'qa/field_sr002_gpt_registered.json';assert not Q.exists();r=json.loads((R/'qa/field_sr002_gpt_material.json').read_text('utf8'));v=r['files'][0];src=Image.open(v['source']).convert('RGBA');par=Image.open(v['output']).convert('RGBA');O=Path(v['output']).parent;dg=r['edge_diagnostics'][0]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
ys=np.arange(2,62)+.5;output_y=(np.arange(512)+.5)/8;source_edges=gaussian_filter1d(np.asarray(dg['source_edge_positions']),1,axis=0);gen_edges=gaussian_filter1d(np.asarray(dg['output_edge_positions']),1,axis=0);target=np.column_stack([np.interp(output_y,ys,source_edges[:,j]) for j in range(2)]);parent=np.column_stack([np.interp(output_y,ys,gen_edges[:,j]) for j in range(2)]);xs=(np.arange(512)+.5)/8;mx=np.empty((512,512),np.float32)
for y in range(512):mx[y]=(np.interp(xs,[0,*target[y],64],[0,*parent[y],64])*8-.5).astype(np.float32)
my=np.repeat(np.arange(512,dtype=np.float32)[:,None],512,axis=1);warped=cv2.remap(np.asarray(par)[:,:,:3],mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE);up=O/'FM0160-gpt-registered-before-tone.png';Image.fromarray(warped).save(up)
a=np.asarray(src.convert('RGB'),float);b=warped.astype(float);sl=Image.fromarray(np.rint(gaussian_filter(a,(2,2,0))).astype('uint8')).resize((512,512),Image.Resampling.BICUBIC);delta=np.asarray(sl,float)-gaussian_filter(b,(16,16,0));out=Image.fromarray(np.rint(np.clip(b+.65*delta,0,255)).astype('uint8')).convert('RGBA');op=O/'FM0160-gpt-registered-tone065-8x.png';out.save(op);mapfile=O/'FM0160-registration-map.npz';np.savez_compressed(mapfile,map_x=mx,map_y=my)
def edges(im):
 sc=im.width/64;z=gaussian_filter(np.asarray(im.convert('RGB'),float).mean(2),(sc,.45*sc));g=np.gradient(z,axis=1);ret=[]
 for y in range(2,62):
  yy=round((y+.5)*sc-.5);rr=[]
  for lo,hi,sign in [(23,32,-1),(31,41,1)]:
   left=round(lo*sc);p=g[yy,left:round(hi*sc)]*sign;k=int(np.argmax(p));rr.append((left+k+.5)/sc)
  ret.append(rr)
 return np.asarray(ret)
after=edges(out);diff=np.abs(after-np.asarray(dg['source_edge_positions']));diag={'median_abs_offset_source_px':np.median(diff,axis=0).tolist(),'p95_abs_offset_source_px':np.quantile(diff,.95,axis=0).tolist(),'output_edge_positions':after.tolist(),'source_edge_positions':dg['source_edge_positions'],'sampled_rows':dg['sampled_rows'],'registration_control_sigma_source_px':1,'limit':'Measured 60 smoothed rows and two selected edges. Original source resolution bounds exact geometry; no native UV or complete texture-layout proof.'}
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18);canvas=Image.new('RGB',(1560,560),'#25313c');d=ImageDraw.Draw(canvas)
for i,(im,label) in enumerate([(src,'원본 · 단순 확대'),(Image.open(v['output']),'초기 재작화 · 경계 차이'),(out,'재작화 · 원본 경계/명암 보정')]):
 x=i*520+4;d.text((x,4),label,font=font,fill='white');im=im.convert('RGB').resize((512,512),Image.Resampling.NEAREST if i==0 else Image.Resampling.LANCZOS);canvas.paste(im,(x,36))
page=R/'outputs/field-sr002/FM0160-gpt-registered.png';canvas.save(page);rec={**{k:v[k] for k in ['group_id','source','source_ptm','source_ptm_sha256','source_rgba_sha256','generated','generated_sha256']},'schema':'brs-field-material-registration/v1','id':'FM0160-gpt-registered-tone065','parent':v['output'],'parent_sha256':sha(v['output']),'registration_map':str(mapfile),'registration_map_sha256':sha(mapfile),'before_tone':str(up),'before_tone_sha256':sha(up),'output':str(op),'output_sha256':sha(op),'output_size':list(out.size),'method':'Piecewise horizontal source-edge registration, preserving outside endpoints, followed by source low-frequency tone .65 at sigma2source; no further inference.','new_local_neural_passes':0,'new_external_generative_calls':0,'edge_diagnostics':diag,'comparison':str(page),'comparison_sha256':sha(page),'visual_review':'pending','runtime_verified':False,'release_eligible':False};Q.write_text(json.dumps(rec,ensure_ascii=False,indent=2),'utf8');print(json.dumps(diag['p95_abs_offset_source_px']))
