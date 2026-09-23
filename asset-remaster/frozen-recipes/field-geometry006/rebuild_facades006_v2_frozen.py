"""Source-anchored facades with sharp original damage and material-only GPT use."""
from pathlib import Path
import json,hashlib,subprocess,shutil
import numpy as np,cv2
from scipy.ndimage import gaussian_filter,distance_transform_edt
from skimage.measure import find_contours
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];O=R/'workspace/local-sr/field-geometry006';V=R/'outputs/field-geometry006';Q=R/'qa/field_geometry006_facades_v2.json';assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def arr(p):return np.array(Image.open(p).convert('RGBA'))
audit=json.loads((R/'qa/field_geometry006_source_audit.json').read_text('utf8'));node='C:/Users/CadriacLord/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe';render=O/'render.cjs';shutil.copy2(R/'workspace/local-sr/field-geometry005/render.cjs',render);font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18)
spec={
 'FM0358':{'gray':[8,11,12],'panes':[[3,5,21,25],[22,5,40,25],[44,5,67,25],[68,5,90,25],[94,5,109,25],[110,5,125,25],[3,42,19,56],[20,42,36,56],[49,42,66,63],[67,42,85,63],[99,42,111,56],[112,42,125,56]],'tx_top':[0,3,21,22,40,44,67,68,90,94,109,110,125,128],'gx_top':[0,3.05,18.4,19.7,35.7,41.6,61.9,63.9,84.2,89.6,105,106.3,124.2,128],'tx_bottom':[0,3,19,20,36,49,66,67,85,99,111,112,125,128],'gx_bottom':[0,3.1,18.5,19.8,35.7,45,61.3,65.6,81.2,89.8,105.9,108.5,124.2,128],'ty':[0,4,5,25,26,32,35,41,42,56,57,63,64],'gy':[0,3.5,4.8,24.0,25.3,31.3,35,37.8,38.7,54.2,55.3,60.2,64]},
 'FM0359':{'gray':[9,11,13],'panes':[[9,9,19,26],[21,9,32,26],[44,9,62,26],[64,9,82,26],[94,9,106,26],[108,9,119,26],[9,41,19,58],[21,41,32,58],[44,41,62,58],[64,41,82,58],[94,41,106,58],[108,41,119,58]],'tx_top':[0,9,19,21,32,44,62,64,82,94,106,108,119,128],'gx_top':[0,8.2,18.8,21.3,31.9,45,62.1,65.4,81,95.2,105.9,108.8,119.7,128],'ty':[0,8,9,26,27,29,31,39,41,58,60,64],'gy':[0,7,8.5,25.3,27,28,32,38.5,40,57.2,59.5,64]},
 'FM0364':{'gray':[9,10,11,12,13,14,15],'panes':[[6,5,19,23],[26,5,40,23],[44,5,65,23],[70,5,90,23],[94,5,106,23],[112,5,122,23],[6,42,36,59],[49,42,66,63],[68,42,85,63],[99,42,122,59]],'tx_top':[0,6,19,26,40,44,65,70,90,94,106,112,122,128],'gx_top':[0,6.35,17,25.35,36.4,42.85,60.2,67.35,85.7,91.45,102.4,111.3,121.6,128],'tx_bottom':[0,6,36,49,66,68,85,99,122,128],'gx_bottom':[0,5.8,35.85,50.65,61.6,66.3,78.0,92.7,121.9,128],'ty':[0,4,5,23,24,30,32,38,41,42,59,60,63,64],'gy':[0,4.25,5.2,20.8,23,28.7,30.2,34,36.3,37.5,53.4,56,59.7,64]}}
spec['FM0364']['panes']=[[6,4,20,23],[25,4,40,23],[44,4,65,23],[70,5,90,23],[94,5,106,23],[112,4,122,23],[5,42,36,59],[49,42,66,63],[68,42,85,63],[99,42,122,59]]
glasspath=R/'workspace/gpt-trials/FM0359-v1/generated-raw.png';glassraw=arr(glasspath);gh,gw=glassraw.shape[:2];glassbox=[46,45,49,52];ga,gb,gc,gd=[round(t*z) for t,z in zip(glassbox,[gw/128,gh/64,gw/128,gh/64])];glass=glassraw[gb:gd,ga:gc,:3].astype('float32');glassalpha=glassraw[gb:gd,ga:gc,3];assert np.all(glassalpha==255)
donorpreview=O/'glass-material-donor-v2.png';Image.fromarray(glass.astype('uint8')).resize((240,560),Image.Resampling.NEAREST).save(donorpreview)
files=[];pages=[]
for gid,z in spec.items():
 v=next(v for v in audit['files'] if v['group_id']==gid);s=arr(v['source']);gp=R/'workspace/gpt-trials'/(gid+'-v1')/'generated-raw.png';g=arr(gp);gh,gw=g.shape[:2];h,w=s.shape[:2];palette,inv=np.unique(s.reshape(-1,4),axis=0,return_inverse=True);labels=inv.reshape(h,w);graymask=np.isin(labels,z['gray']);colorgray=graymask&(s[:,:,3]>0)
 # Two story maps avoid translating different lower group positions as if the
 # atlas were a single projective photograph.
 xx=(np.arange(1024)+.5)/8;yy=(np.arange(512)+.5)/8;mx0=np.interp(xx,z['tx_top'],z['gx_top'])*gw/128-.5;mx1=np.interp(xx,z.get('tx_bottom',z['tx_top']),z.get('gx_bottom',z['gx_top']))*gw/128-.5;my=np.interp(yy,z['ty'],z['gy'])*gh/64-.5;mapx=np.broadcast_to(mx0,(512,1024)).copy();mapx[280:]=mx1;mapy=np.broadcast_to(my[:,None],(512,1024));rgb=cv2.remap(g[:,:,:3].astype('float32'),mapx.astype('float32'),mapy.astype('float32'),cv2.INTER_CUBIC);panemask=np.zeros((512,1024),bool)
 for box in z['panes']:
  a,b,c,d=[t*8 for t in box];panemask[b:d,a:c]=True
 # Wall-only normalization avoids transparent black/checker affecting exposure.
 wallmask=~panemask;swall=(~graymask)&(s[:,:,3]>0);target=s[:,:,:3][swall].mean(0);gain=target/np.maximum(rgb[wallmask].mean(0),1);rgb*=gain
 # Original holes become straight-segment vector cuts. Small holes are retained
 # rather than discarded as noise; original source alpha topology is tested.
 polys=[]
 for c in find_contours(np.pad((s[:,:,3]>0).astype(float),1),.5,fully_connected='high'):
  points=(c[:,::-1]-.5).astype('float32');poly=cv2.approxPolyDP(points,.40,True).reshape(-1,2)
  if len(poly)<3:poly=points
  polys.append(poly.tolist())
 path=' '.join('M '+' L '.join(f'{x},{y}' for x,y in p)+' Z' for p in polys);vp=O/(gid+'-source-alpha-v2.svg');vp.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="512" viewBox="0 0 128 64"><path d="'+path+'" fill="white" fill-rule="evenodd"/></svg>','utf8');ap=O/(gid+'-source-alpha-v2.png');subprocess.run([node,str(render),str(vp),str(ap)],check=True,capture_output=True);alpha=arr(ap)[:,:,3]
 # Exact source frame footprints, invariant bevel profiles. The generated door
 # handles lie on these repainted supports and cannot enter the result.
 frame_regions=[];glass_regions=[]
 for pi,box in enumerate(z['panes']):
  x0,y0,x1,y1=box;a,b,c,d=[t*8 for t in box];pad=8;outer=[max(0,a-pad),max(0,b-pad),min(1024,c+pad),min(512,d+pad)];aa,bb,cc,dd=outer
  source_ring=s[max(0,y0-1):min(h,y1+1),max(0,x0-1):min(w,x1+1),:3];valid_ring=np.ones(source_ring.shape[:2],bool);valid_ring[1:-1,1:-1]=False;frame_color=np.clip(np.median(source_ring[valid_ring],axis=0),8,115)
  # Source shadow/construction edge plus one narrow illuminated inner bevel.
  strips=[([aa,bb,cc,b],'horizontal'),([aa,d,cc,dd],'horizontal'),([aa,b,a,d],'vertical'),([c,b,cc,d],'vertical')]
  for sb,axis in strips:
   u,t,e,f=sb
   if e<=u or f<=t:continue
   length=f-t if axis=='horizontal' else e-u;prof=np.linspace(.42,1.3,length)[:,None]*frame_color[None,:];mat=np.broadcast_to(prof[:,None,:],(f-t,e-u,3)) if axis=='horizontal' else np.broadcast_to(prof[None,:,:],(f-t,e-u,3));rgb[t:f,u:e]=mat;frame_regions.append({'box_output':sb,'axis':axis,'base_RGB':frame_color.tolist()})
  # Rebuild glass using only a clean opaque material donor. No generated hole,
  # checker pattern, colored alpha fringe or handle is used as pane content.
  patch=cv2.resize(glass,(c-a,d-b),interpolation=cv2.INTER_CUBIC);fine=patch-gaussian_filter(patch,(1.2,1.2,0),mode='nearest');orig=s[y0:y1,x0:x1,:3][colorgray[y0:y1,x0:x1]];mean=orig.mean(0) if len(orig) else np.array([173,173,173]);gray=mean+2*np.tanh(fine*.25/2);gray+=np.linspace(-3,3,c-a)[None,:,None]+np.linspace(5,-5,d-b)[:,None,None]
  # Source secondary tone planes remain visible without repeating pixel blocks.
  light=np.mean(s[y0:y1,x0:x1,:3],axis=2);covered=colorgray[y0:y1,x0:x1];valid=np.where(covered,light,mean.mean());shade=cv2.resize(gaussian_filter(valid.astype('float32'),.7,mode='nearest'),(c-a,d-b),interpolation=cv2.INTER_CUBIC)-mean.mean();gray+=shade[:,:,None]*.40
  rgb[b:d,a:c]=gray;glass_regions.append({'source_box':box,'base_source_RGB':mean.tolist()})
 # Thin edge facets on retained glass only, along source fracture contours.
 sourceglass=np.repeat(np.repeat(graymask,8,0),8,1);solid=alpha>=128;inside=distance_transform_edt(solid);edge=sourceglass&solid&(inside<=2);rgb[edge]+=np.array([16,18,20]);out=np.concatenate([np.rint(np.clip(rgb,0,255)).astype('uint8'),alpha[:,:,None]],axis=2)
 # Invisible RGB dilation avoids colored fringes when the game samples alpha.
 ni=distance_transform_edt(~solid,return_distances=False,return_indices=True);out[~solid,:3]=out[ni[0][~solid],ni[1][~solid],:3]
 op=O/(gid+'-source-frame-glass-v2-8x.png');Image.fromarray(out).save(op);npz=O/(gid+'-source-frame-glass-v2-base.npz');np.savez_compressed(npz,rgb=out[:,:,:3],alpha=alpha,mapx=mapx.astype('float32'),mapy=mapy.astype('float32'))
 sample=alpha[4::8,4::8]>=128;original=s[:,:,3]>=128;diff=int(np.count_nonzero(sample!=original));inter=np.count_nonzero(sample&original);union=np.count_nonzero(sample|original)
 def holes(binary):
  _,hier=cv2.findContours(np.pad(binary.astype('uint8'),1),cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE);return int(sum(a[3]>=0 for a in hier[0]))
 rec={**{k:v[k] for k in ['group_id','source','source_ptm','source_ptm_sha256','source_rgba_sha256']},'id':gid+'-source-frame-glass-v2','output':str(op),'output_sha256':sha(op),'gpt_raw':str(gp),'gpt_raw_sha256':sha(gp),'gpt_raw_size':[gw,gh],'gpt_prompt':str(gp.parent/'prompt.txt'),'gpt_prompt_sha256':sha(gp.parent/'prompt.txt'),'geometry_vector':str(vp),'geometry_vector_sha256':sha(vp),'alpha_render':str(ap),'alpha_render_sha256':sha(ap),'base_planes':str(npz),'base_planes_sha256':sha(npz),'glass_donor':str(glasspath),'glass_donor_sha256':sha(glasspath),'glass_donor_box_source_coordinates':glassbox,'glass_donor_alpha255':True,'source_mapping':z,'source_alpha_polygons':polys,'frame_regions':frame_regions,'glass_regions':glass_regions,'wall_RGB_gain':gain.tolist(),'source_alpha_center_mismatches':diff,'source_alpha_center_IoU':float(inter/union),'alpha_mass_ratio':float(alpha.sum()/(s[:,:,3].sum()*64)),'enclosed_holes_source':holes(original),'enclosed_holes_output':holes(solid),'method':'Original alpha damage traced as straight polygons; source-position rectangular metal frames and glass planes; GPT wall material reprojected by story and clean opaque glass material reused from FM0359.','new_local_inference_passes':0,'new_external_calls':0,'runtime_verified':False,'release_eligible':False,'visual_review':'pending'};files.append(rec)
 for name,box in [('whole',[0,0,128,64]),('upper-left',[0,0,44,30]),('lower-center',[43,38,88,64])]:
  x0,y0,x1,y1=box;ww,hh=(x1-x0)*8,(y1-y0)*8;scale=min(1,640/ww,512/hh);sw,sh=round(ww*scale),round(hh*scale);cw=max(380,sw+16);can=Image.new('RGB',(cw*2,(sh+44)*2),'#26333f');dr=ImageDraw.Draw(can)
  for j,(im,title) in enumerate([(Image.fromarray(s).crop(box).resize((ww,hh),Image.Resampling.NEAREST),'원본 · 단순 확대'),(Image.fromarray(out).crop(tuple(t*8 for t in box)),'원본 창틀 · 파손 윤곽 + 재질')]):
   im=im.resize((sw,sh),Image.Resampling.NEAREST if j==0 else Image.Resampling.LANCZOS)
   for k,bg in enumerate(['#252d35','#d4d5d7']):
    dr.text((j*cw+6,k*(sh+44)+4),gid+' '+title,font=font,fill='white');m=Image.new('RGB',(sw,sh),bg);m.paste(im,(0,0),im);can.paste(m,(j*cw+6,k*(sh+44)+35))
  pp=V/(gid+'-'+name+'-v2.png');can.save(pp);pages.append({'path':str(pp),'sha256':sha(pp),'source_box':box,'review_status':'pending'})
Q.write_text(json.dumps({'schema':'brs-source-frame-broken-glass/v1','source_audit_sha256':sha(R/'qa/field_geometry006_source_audit.json'),'files':files,'pages':pages,'glass_donor_preview':str(donorpreview),'material_refinement':'Large material crack pattern removed by fine residual extraction; mild planar glass reflection and source-bound fracture edge facets. FM0364 top fragments included in pane rectangles.','new_local_inference_passes':0,'external_generative_calls':0,'reuses_external_generations':3,'tool':'built-in image_gen; model ID not exposed','runtime_verified':False,'release_eligible':False},ensure_ascii=False,indent=2),'utf8');print(json.dumps([{k:v[k] for k in ['group_id','source_alpha_center_mismatches','source_alpha_center_IoU','alpha_mass_ratio','enclosed_holes_source','enclosed_holes_output']} for v in files]))
