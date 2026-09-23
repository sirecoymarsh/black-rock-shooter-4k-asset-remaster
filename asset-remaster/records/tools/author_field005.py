"""Source-bound construction geometry with explicitly external painted material."""
from pathlib import Path
import json,hashlib,subprocess,shutil
import numpy as np,cv2
from scipy.ndimage import gaussian_filter,distance_transform_edt,label
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];O=R/'workspace/local-sr/field-geometry005';V=R/'outputs/field-geometry005';Q=R/'qa/field_geometry005_authored.json'
assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def arr(p):return np.asarray(Image.open(p).convert('RGBA'))
def save(p,a):Image.fromarray(a).save(p)
def write(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2),'utf8')
old=json.loads((R/'qa/field_geometry005_trials.json').read_text('utf8'));files=[];pages=[]
node='C:/Users/CadriacLord/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe';renderer=O/'render.cjs'
def render(svg,name,w,h):
 p=O/(name+'.svg');p.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w*8}" height="{h*8}" viewBox="0 0 {w} {h}">'+svg+'</svg>','utf8');q=O/(name+'.png');subprocess.run([node,str(renderer),str(p),str(q)],check=True,capture_output=True);return p,q,arr(q)
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17)
def page(gid,s,p,out,box,name):
 a,b,c,d=box;ww,hh=(c-a)*8,(d-b)*8;scale=min(1,640/ww,512/hh);sw,sh=round(ww*scale),round(hh*scale);cw=max(310,sw+16);can=Image.new('RGB',(cw*3,(sh+44)*2),'#26333f');draw=ImageDraw.Draw(can)
 ims=[Image.fromarray(s).crop(box).resize((ww,hh),Image.Resampling.NEAREST),Image.fromarray(p).crop(tuple(x*8 for x in box)),Image.fromarray(out).crop(tuple(x*8 for x in box))]
 for j,(im,title) in enumerate(zip(ims,['원본 · 단순 확대','기존 로컬','원본 구조 + 재작화'])):
  im=im.resize((sw,sh),Image.Resampling.NEAREST if j==0 else Image.Resampling.LANCZOS)
  for k,bg in enumerate(['#252d35','#d4d5d7']):
   draw.text((j*cw+6,k*(sh+44)+4),gid+' '+title,font=font,fill='white');mat=Image.new('RGB',(sw,sh),bg);mat.paste(im,(0,0),im);can.paste(mat,(j*cw+6,k*(sh+44)+35))
 pp=V/(gid+'-'+name+'-authored-v2.png');can.save(pp);pages.append({'path':str(pp),'sha256':sha(pp),'source_box':box,'review_status':'pending'})
for gid in ['FM0113','FM0029']:
 v=next(v for v in old['files'] if v['group_id']==gid);s=arr(v['source']);p=arr(v['parent']);previous=arr(v['output']);h,w=s.shape[:2];gp=R/'workspace/gpt-trials'/(gid+'-v1')/'generated-raw.png';g=arr(gp);gh,gw=g.shape[:2];out=previous.copy();meta={};mask=np.zeros(out.shape[:2],bool)
 if gid=='FM0113':
  # Deliberate straight contours. The top slot is an exact rectangle; no RDP.
  outer=[[7,32],[25,32],[26,33],[26,36],[27,36],[27,37],[26,37],[26,38],[25.625,38],[32.125,64],[27,64],[16,49],[5,64],[-.125,64],[6.375,38],[6,38],[6,37],[5,37],[5,36],[6,36],[6,33]]
  holes=[[[10,34],[22,34],[22,36],[10,36]],[[10.5,38],[21.5,38],[16,44]],[[9,40.5],[14.5,45.7],[5.8,56.5]],[[23,40.5],[17.5,45.7],[26.2,56.5]]]
  path=' '.join('M '+' L '.join(f'{x},{y}' for x,y in poly)+' Z' for poly in [outer]+holes)
  vp,ap,am=render('<path d="'+path+'" fill="white" fill-rule="evenodd"/>','FM0113-authored-support-alpha-v2',w,h);alpha=am[:,:,3].copy();alpha[:256]=255
  # Alpha-aware source illumination, separate from the new wood grain.
  sa=s[:,:,3].astype('float32')/255;den=gaussian_filter(sa,1.2,mode='nearest');sc=gaussian_filter(s[:,:,:3].astype('float32')*sa[:,:,None],(1.2,1.2,0),mode='nearest')/np.maximum(den[:,:,None],1e-6);valid=den>1e-5;ni=distance_transform_edt(~valid,return_distances=False,return_indices=True);sc[~valid]=sc[ni[0][~valid],ni[1][~valid]];base=cv2.resize(sc,(256,512),interpolation=cv2.INTER_CUBIC)
  rgb=base.copy();gen=g[:,:,:3].astype('float32');planes=[];coverage=np.zeros((512,256),np.uint8)
  def wood(name,target,donor):
   nonlocal_dummy=None
   src=np.float32(donor)*[gw/32,gh/64];dst=np.float32(target)*8;H=cv2.getPerspectiveTransform(src.astype('float32'),dst.astype('float32'));mat=cv2.warpPerspective(gen,H,(256,512),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE);pm=np.zeros((512,256),np.uint8);cv2.fillConvexPoly(pm,np.rint(dst*16).astype('int32'),1,shift=4);m=pm>0
   # Reuse material only: source illumination keeps the dark top and worn base.
   fine=mat-gaussian_filter(mat,(9,9,0),mode='nearest');rgb[m]=base[m]+12*np.tanh(fine[m]*.9/12);coverage[m]+=1;planes.append({'id':name,'target_quad_source':target,'generated_donor_quad_in_32x64_coordinates':donor})
  donor=[[6.45,36],[8.65,36],[3.95,60.4],[1.6,61.7]]
  wood('left-leg',[[6.375,38],[9.6,38],[5,64],[-.125,64]],donor)
  wood('right-leg',[[22.4,38],[25.625,38],[32.125,64],[27,64]],[[23.35,36],[25.55,36],[30.4,61.7],[28.05,60.4]])
  wood('back-rising-brace',[[21,38],[25,38],[4.1,64],[-1,64]],donor)
  wood('front-falling-brace',[[7,38],[11,38],[33,64],[27.9,64]],donor)
  wood('horizontal-cap',[[5,32],[27,32],[27,38],[5,38]],[[5.8,31.4],[26,31.4],[26,35],[5.8,35]])
  # Mild finite-width edge bevel within a mathematically straight outline.
  edge=distance_transform_edt(alpha>=128);shade=np.minimum(edge/2,1);rgb[256:]*=(.90+.10*shade[256:,:,None])
  # Wall: generated mineral grain only, with source shading including the dark
  # diagonal source patch. No invented brick joints/crack network is retained.
  wall=g[int(gh*.005):int(gh*.475),int(gw*.68):int(gw*.995),:3].astype('float32');wall=cv2.resize(wall,(128,256),interpolation=cv2.INTER_CUBIC);grain=wall-gaussian_filter(wall,(7,7,0),mode='nearest');wallbase=cv2.resize(gaussian_filter(s[:32,16:,:3].astype('float32'),(.8,.8,0),mode='nearest'),(128,256),interpolation=cv2.INTER_CUBIC);rgb[:256,128:]=wallbase+6*np.tanh(grain*.7/6)
  # Each original window bay receives texture independently, leaving construction
  # seams at declared original texel centers. Physical bar count is not asserted.
  xb=[0,2.5,4.5,7.5,10.5,13.5,15.5,16];yb=[0,1.5,6.5,12.5,18.5,24.5,29.5,30,32]
  glass=g[int(gh*.05):int(gh*.085),int(gw*.14):int(gw*.19),:3].astype('float32');grids=[]
  for a,c in zip(xb,xb[1:]):
   for b,d in zip(yb,yb[1:]):
    aa,bb,cc,dd=[round(x*8) for x in [a,b,c,d]];sp=s[int(b):max(int(b)+1,int(np.ceil(d))),int(a):max(int(a)+1,int(np.ceil(c))),:3].astype('float32');col=sp.mean((0,1));mat=cv2.resize(glass,(cc-aa,dd-bb),interpolation=cv2.INTER_CUBIC);fine=mat-gaussian_filter(mat,(4,4,0),mode='nearest');rgb[bb:dd,aa:cc]=col+5*np.tanh(fine*.6/5);grids.append([a,b,c,d])
  seams=[]
  for axis,values,start,end in [('v',[2.5,4.5,7.5,10.5,13.5,15.5],.8,30),('h',[1.5,6.5,12.5,18.5,24.5,29.5],0,16)]:
   for pos in values:
    box=[pos-.35,start,pos+.35,end] if axis=='v' else [start,pos-.35,end,pos+.35];aa,bb,cc,dd=[round(x*8) for x in box];rgb[bb:dd,aa:cc]=[67,63,58]
    if axis=='v':rgb[bb:dd,aa:aa+1]=[88,83,76]
    else:rgb[bb:bb+1,aa:cc]=[88,83,76]
    seams.append({'axis':axis,'position':pos,'box':box})
  rgb[240:256,:128]=cv2.resize(gaussian_filter(s[30:32,:16,:3].astype('float32'),(.2,1,0),mode='nearest'),(128,16),interpolation=cv2.INTER_LINEAR)
  out[:,:,:3]=np.rint(np.clip(rgb,0,255)).astype('uint8');out[:,:,3]=alpha;mask[:]=True
  # RGB dilation only under alpha=0 keeps hidden edge colors nonblack.
  valid=alpha>0;ni=distance_transform_edt(~valid,return_distances=False,return_indices=True);out[~valid,:3]=out[ni[0][~valid],ni[1][~valid],:3]
  src=s[32:,:,3]>0;sample=alpha[260::8,4::8]>=128;diff=int(np.count_nonzero(src!=sample));inter=np.count_nonzero(src&sample);union=np.count_nonzero(src|sample)
  basepath=O/'FM0113-authored-material-base-v2.npz';np.savez_compressed(basepath,rgb=out[:,:,:3],alpha=alpha)
  meta={'method':'Explicit straight source geometry, rectangular slot and triangular voids; original illumination with constrained externally generated wood/mineral material.','geometry_vector':str(vp),'geometry_vector_sha256':sha(vp),'alpha_render':str(ap),'alpha_render_sha256':sha(ap),'outer_source_polygon':outer,'holes_source_polygons':holes,'material_planes':planes,'seams':seams,'source_grid_cell_regions':grids,'base_planes':str(basepath),'base_planes_sha256':sha(basepath),'lower_source_alpha_center_mismatches':diff,'lower_source_alpha_center_IoU':inter/union,'lower_alpha_mass_ratio':float(alpha[256:].sum()/(s[32:,:,3].sum()*64)),'lower_holes_count_at_threshold128':int(label(alpha[256:]<128)[1]-1),'material_interpretation':'Timber support and concrete/plaster wall inferred as art direction from construction and user request; not independently proven native material metadata.','limitation':'Straight construction is authored from source anchors, not exact source alpha identity. Upper grid/source shading is interpreted; generated whole layout is not adopted.'}
 else:
  # Only opaque glass interiors. All window frames, palette lattice and other
  # atlas surfaces are protected against unrelated changes in the GPT output.
  panes=[('left-clipped',[0,23,8,42],[0,23.2,7.6,41.4]),('small-left',[13,25,22,41],[12.9,24.6,22,41.3]),('large-left',[29,23,41,42],[29.2,23.3,41.5,41.5]),('large-right',[48,23,60,42],[48.7,23.3,60.5,41.5]),('narrow',[64,23,72,64],[65.0,23.3,72.7,63.8]),('small-right',[78,32,88,42],[79.5,32.5,89.1,41.5])]
  records=[];sx=gw/128;sy=gh/64
  # Source pixels colored brown/cream/gold are frame, not glass.
  palette=np.unique(s.reshape(-1,4),axis=0);allow=np.zeros((h,w),bool)
  for i in [2,3,4,7,9,12,13]:allow|=np.all(s==palette[i],axis=2)
  for name,box,donor in panes:
   x0,y0,x1,y1=box;a,b,c,d=[t*8 for t in box];ga,gb,gc,gd=donor;patch=np.asarray(Image.fromarray(g).crop((round(ga*sx),round(gb*sy),round(gc*sx),round(gd*sy))).resize((c-a,d-b),Image.Resampling.LANCZOS)).copy();edit=np.repeat(np.repeat(allow[y0:y1,x0:x1],8,0),8,1);patch[:,:,3]=255
   # Match the original dark-brown interior floor while retaining angular gray
   # shards. Contrast added by the generator is explicitly inspected afterwards.
   lum=patch[:,:,:3].mean(2);dark=(lum<70)&edit
   if dark.any():offset=np.array([52,36,32])-np.median(patch[:,:,:3][dark],axis=0)
   else:offset=np.zeros(3)
   patch[:,:,:3]=np.rint(np.clip(patch[:,:,:3].astype(float)+offset,0,255)).astype('uint8');out[b:d,a:c][edit]=patch[edit];mask[b:d,a:c]|=edit;records.append({'id':name,'source_box':box,'generated_donor_box_in_128x64_coordinates':donor,'RGB_dark_floor_offset':offset.tolist()})
  assert np.array_equal(out[~mask],previous[~mask]);assert np.array_equal(out[:,:,3],previous[:,:,3]);meta={'method':'Built-in GPT redraw, six glass interiors reprojected into source palette-defined opaque glass masks, original source-grid parent elsewhere.','panes':records,'outside_mask_parent_rgba_exact':True,'parent_for_mask':v['output'],'parent_for_mask_sha256':sha(v['output']),'alpha_parent_exact':True,'limitation':'Glass-only trial. Frames and other atlas regions still carry unapproved prior local geometry; whole atlas remains held. Generated shard placement must be compared to source, not assumed exact.'}
 op=O/(gid+'-authored-v2-8x.png');mp=O/(gid+'-authored-v2-mask.png');save(op,out);save(mp,mask.astype('uint8')*255)
 rec={k:v[k] for k in ['group_id','source','source_ptm','source_ptm_sha256','source_rgba_sha256','parent','parent_sha256']};rec.update(id=gid+'-authored-v2',output=str(op),output_sha256=sha(op),mask=str(mp),mask_sha256=sha(mp),previous=v['output'],previous_sha256=sha(v['output']),gpt_raw=str(gp),gpt_raw_sha256=sha(gp),gpt_actual_size=[gw,gh],gpt_prompt=str(gp.parent/'prompt.txt'),gpt_prompt_sha256=sha(gp.parent/'prompt.txt'),**meta,new_neural_passes=0,new_external_calls=1,runtime_verified=False,release_eligible=False,visual_review='pending');files.append(rec)
 page(gid,s,p,out,[0,0,w,h],'whole');page(gid,s,p,out,[0,32,32,64] if gid=='FM0113' else [0,21,92,45],'detail');page(gid,s,p,out,[0,0,32,32] if gid=='FM0113' else [26,21,64,45],'upper' if gid=='FM0113' else 'glass')
write(Q,{'schema':'brs-authored-material-geometry/v1','parent_report_sha256':sha(R/'qa/field_geometry005_trials.json'),'files':files,'pages':pages,'new_local_inference_passes':0,'external_generative_calls':2,'tool':'built-in image_gen, model identifier not exposed','runtime_verified':False,'release_eligible':False})
print(json.dumps({'outputs':len(files),'pages':len(pages),'support_alpha_mismatches':files[0]['lower_source_alpha_center_mismatches'],'support_alpha_IoU':files[0]['lower_source_alpha_center_IoU']}))
