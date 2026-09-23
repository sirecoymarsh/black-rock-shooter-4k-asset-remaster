"""Register external material once; constrain it to source planes and fix curve coordinates."""
import json,hashlib,shutil
from pathlib import Path
import numpy as np,cv2
from scipy.ndimage import gaussian_filter,gaussian_filter1d
from scipy.interpolate import PchipInterpolator
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];Q=R/'qa/field_geometry004_gpt_and_alignment.json';assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
one=json.loads((R/'qa/field_geometry004_trials.json').read_text('utf8'));two=json.loads((R/'qa/field_geometry004_refined.json').read_text('utf8'));O=R/'workspace/local-sr/field-geometry004';V=R/'outputs/field-geometry004';files=[];pages=[];font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17)
G=R/'workspace/gpt-trials/FM0337-v1';rawsource=Path(r'P:\AI\Codex\generated_images\01a0c802-c7cf-7f71-a268-2f12b1fd7bd3\exec-afa2ea6e-719e-4306-a100-218a75d6db28.png');raw=G/'generated-raw.png';assert not raw.exists();shutil.copy2(rawsource,raw);rawim=Image.open(raw).convert('RGBA');scaled=rawim.resize((1024,512),Image.Resampling.LANCZOS);scaledpath=G/'FM0337-gpt-material-trial-8x.png';scaled.save(scaledpath)
for gid in ['FM0337','FM0347']:
 v=next(v for v in one['files'] if v['group_id']==gid);v2=next(z for z in two['files'] if z['group_id']==gid);s=np.asarray(Image.open(v['source']).convert('RGBA'));p=np.asarray(Image.open(v['parent']).convert('RGBA'));h,w=s.shape[:2];recipe={}
 if gid=='FM0337':
  gen=np.asarray(scaled);out=p.copy();regions=[];coverage=np.zeros(p.shape[:2],np.uint8)
  for region in v['regions']:
   x0,y0,x1,y1=region['source_box'];a,b,c,d=[t*8 for t in region['source_box']];px=min(4,max(0,(c-a-8)//2));py=min(4,max(0,(d-b-8)//2));material=cv2.resize(gen[b+py:d-py or None,a+px:c-px or None,:3].astype('float32'),(c-a,d-b),interpolation=cv2.INTER_CUBIC)
   sp=s[y0:y1,x0:x1,:3].astype('float32');target=sp.mean((0,1));gain=target/np.maximum(material.mean((0,1)),1)
   row=gaussian_filter1d(sp.mean(1),2,axis=0,mode='nearest');col=gaussian_filter1d(sp.mean(0),2,axis=0,mode='nearest');shade=row[:,None,:]+col[None,:,:]-2*target;shade=cv2.resize(shade,(c-a,d-b),interpolation=cv2.INTER_LINEAR)
   patch=material*gain+shade;out[b:d,a:c,:3]=np.rint(np.clip(patch,0,255)).astype('uint8');coverage[b:d,a:c]+=1
   regions.append({'source_box':region['source_box'],'name':region['name'],'generated_interior_trim_output_xy':[px,py],'target_source_mean_rgb':target.tolist(),'generated_RGB_gain':gain.tolist(),'source_row_shading_rgb':row.tolist(),'source_column_shading_rgb':col.tolist()})
  assert np.all(coverage==1);out[:,:,3]=255;ident='FM0337-source-planes-gpt-material-v3';recipe={'regions':regions,'source_shading_sigma':2,'generated_material':str(scaledpath),'generated_material_sha256':sha(scaledpath),'formula':'resize generated plane interior cubic; match its channel means to source plane; add smoothed source row+column variation minus2*source mean; round/clip.','geometry_scope':'Original rectangles partition every output pixel once; generated boundaries are discarded by interior projection.','material_provenance':'Built-in image_gen external material, one call. Prior local WDN geometric edit was supplied as target; not an all-local result.'}
  references=[{'role':'edit target fixed geometry','path':v['output'],'sha256':v['output_sha256']},{'role':'immutable original color/layout reference','path':v['source'],'sha256':sha(v['source'])}]
  gpt={'raw':str(raw),'raw_sha256':sha(raw),'original_generated_path':str(rawsource),'actual_raw_size':list(rawim.size),'resized_output':str(scaledpath),'resized_output_sha256':sha(scaledpath),'resized_size':[1024,512],'resize':'Pillow Lanczos','prompt':str(G/'prompt.txt'),'prompt_sha256':sha(G/'prompt.txt'),'references':references,'tool':'built-in image_gen','model_identifier':'not exposed by tool','external_calls':1,'whole_generated_image_decision':'held pending exact source-plane/color correction; generated image alone is not adopted','runtime_verified':False,'release_eligible':False}
 else:
  base=np.load(v2['base_planes'])['rgb'].copy();by=np.median(s[17:31,:,:3],axis=1).astype('float32');back=cv2.resize(by[:,None,:],(512,112),interpolation=cv2.INTER_LINEAR);yy=(np.arange(136,248)+.5)/8;xx=(np.arange(512)+.5)/8;closest=np.full((112,512),999.,np.float32);signed=np.zeros_like(closest);curves=[];samples=[]
  lum=s[:,:,:3].mean(2)
  for oldc in v['curve_centers']:
   c={**oldc,'source_x':(np.array(oldc['source_x'])+.5).tolist(),'source_y':(np.array(oldc['source_y'])+.5).tolist()};curves.append(c);fit=PchipInterpolator(c['source_y'],c['source_x'],extrapolate=True);cx=fit(yy);dd=xx[None,:]-cx[:,None];take=np.abs(dd)<closest;closest[take]=np.abs(dd)[take];signed[take]=dd[take]
   for y in [18,20,22,25,27,29]:
    pred=float(fit(y+.5));lo=max(0,int(np.floor(pred-2)));hi=min(64,int(np.ceil(pred+2))+1);sx=np.arange(lo,hi)+.5;mid=9+15*c['repeat'];weights=np.maximum(lum[y,lo:hi]-np.median(lum[y])-3,0);weights[(sx>=mid) if pred<mid else (sx<mid)]=0
    if weights.sum():
     obs=float(np.average(sx,weights=weights));samples.append({'repeat':c['repeat'],'direction':c['direction'],'source_row':y,'predicted_x':pred,'weighted_source_center_x':obs,'difference_source_px':pred-obs,'neighboring_arm_excluded_at_x':mid})
  high=cv2.resize(np.array(v['curve_highlight_profile_rgb'],np.float32)[:,None,:],(512,112),interpolation=cv2.INTER_LINEAR);weight=np.clip((1.05-closest)/.25,0,1)[:,:,None];bevel=np.clip(.88+.12*signed/.8,.72,1.0)[:,:,None];base[136:248]=back*(1-weight)+high*bevel*weight;grain=p[:,:,:3].astype('float32')-gaussian_filter(p[:,:,:3].astype('float32'),(5,5,0),mode='nearest');out=p.copy();out[:,:,:3]=np.rint(np.clip(base+np.clip(grain*.3,-2,2),0,255)).astype('uint8');out[:,:,3]=255
  err=np.abs([z['difference_source_px'] for z in samples]);ident='FM0347-pixel-center-curves-v3';bp=O/(ident+'-base.npz');np.savez_compressed(bp,rgb=base)
  recipe={'curve_centers':curves,'coordinate_correction':'Original traced samples were recorded as pixel indices; add.5 to both x/y to render at pixel centers. All earlier trace records remain unchanged.','stroke_outer_halfwidth_source':1.05,'stroke_edge_transition_source':.25,'bevel_equation':'clip(.88+.12*signed/.8,.72,1)','grain_sigma_output':5,'grain_gain':.3,'grain_bound':2,'base_planes':str(bp),'base_planes_sha256':sha(bp),'source_curve_diagnostics':{'samples':samples,'median_absolute_error_source_px':float(np.median(err)),'p95_absolute_error_source_px':float(np.percentile(err,95)),'limit':'Sampled original highlight centers with adjacent crossing arm excluded. Trace/center agreement is not proof of consumer geometry or every edge.'}}
 op=O/(ident+'-8x.png');Image.fromarray(out).save(op);files.append({**{k:v[k] for k in ['group_id','source','source_ptm','source_ptm_sha256','source_rgba_sha256','parent','parent_sha256','region_classmap','region_classmap_sha256']},'id':ident,'output':str(op),'output_sha256':sha(op),'recipe':recipe,'new_neural_passes':0,'runtime_verified':False,'release_eligible':False,'visual_review':'pending'})
 for label,box in [('whole',(0,0,w,h)),('detail',(40,0,72,32) if gid=='FM0337' else (16,0,48,32))]:
  ims=[Image.fromarray(s).crop(box).resize(((box[2]-box[0])*8,(box[3]-box[1])*8),Image.Resampling.NEAREST),Image.open(v2['output']).convert('RGBA').crop(tuple(t*8 for t in box))]
  titles=['원본 · 단순 확대','직전 수정']
  if gid=='FM0337':ims.append(scaled.crop(tuple(t*8 for t in box)));titles.append('GPT 재질 시안')
  ims.append(Image.fromarray(out).crop(tuple(t*8 for t in box)));titles.append('원본 구조·색 보정' if gid=='FM0337' else '곡선 픽셀 중심 정렬')
  cw,ch=ims[0].size;scale=min(1,512/cw,512/ch) if label=='whole' else 1;sw,sh=round(cw*scale),round(ch*scale);col=max(310,sw+16);can=Image.new('RGB',(col*len(ims),sh+46),'#26333f');d=ImageDraw.Draw(can)
  for j,(im,title) in enumerate(zip(ims,titles)):d.text((j*col+6,5),gid+' '+title,font=font,fill='white');can.paste(im.resize((sw,sh),Image.Resampling.NEAREST if j==0 else Image.Resampling.LANCZOS).convert('RGB'),(j*col+6,38))
  pp=V/(gid+'-'+label+'-v3.png');can.save(pp);pages.append({'path':str(pp),'sha256':sha(pp),'source_box':list(box),'review_status':'pending'})
Q.write_text(json.dumps({'schema':'brs-source-constrained-external-material-and-alignment/v1','parent_reports_sha256':{n:sha(R/'qa'/n) for n in ['field_geometry004_trials.json','field_geometry004_refined.json']},'files':files,'pages':pages,'gpt':gpt,'new_neural_passes':0,'external_calls':1,'runtime_verified':False,'release_eligible':False},ensure_ascii=False,indent=2),'utf8')
print(json.dumps({'derived':2,'external_calls':1,'gpt_actual_size':list(rawim.size),'curve_diagnostics':{k:v for k,v in files[1]['recipe']['source_curve_diagnostics'].items() if k!='samples'}}))
