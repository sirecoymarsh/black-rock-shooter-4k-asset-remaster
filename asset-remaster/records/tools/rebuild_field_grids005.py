"""Protected alpha lattice and source-line grid/stand reconstruction trials."""
import json,hashlib,subprocess,shutil
from pathlib import Path
import numpy as np,cv2
from scipy.ndimage import gaussian_filter,distance_transform_edt,label
from skimage.measure import find_contours
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];Q=R/'qa/field_geometry005_trials.json';assert not Q.exists()
O=R/'workspace/local-sr/field-geometry005';O.mkdir(exist_ok=False);V=R/'outputs/field-geometry005';V.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
inference=json.loads((R/'qa/field_sr003_inference.json').read_text('utf8'));prior=json.loads((R/'qa/field_geometry004_review.json').read_text('utf8'));assert sha(R/'qa/field_sr_catalog.json')==prior['catalog_after_sha256']
node='C:/Users/CadriacLord/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe';render=O/'render.cjs';shutil.copy2(R/'workspace/local-sr/field-sr003-rectilinear/render.cjs',render)
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17);files=[];pages=[]
for gid in ['FM0029','FM0113']:
 v=next(v for v in inference['files'] if v['id']==gid+'-wdn');s=np.asarray(Image.open(v['source']).convert('RGBA'));p=np.asarray(Image.open(v['output']).convert('RGBA'));h,w=s.shape[:2];nn=np.repeat(np.repeat(s,8,0),8,1);out=p.copy();mask=np.zeros(p.shape[:2],bool);meta={};vectors=[]
 if gid=='FM0029':
  boxes=[[32,0,55,20],[55,0,92,20],[92,12,121,59]];grain=p[:,:,:3].astype('float32')-gaussian_filter(p[:,:,:3].astype('float32'),(3,3,0),mode='nearest')
  # Merge identical horizontal palette runs vertically into exact rectangles.
  # The lattice's alpha phase is intentional source data, not a mesh inference.
  rects=[]
  for box in boxes:
   x0,y0,x1,y1=box;active={}
   for y in range(y0,y1+1):
    current={}
    if y<y1:
     x=x0
     while x<x1:
      color=tuple(int(a) for a in s[y,x]);end=x+1
      while end<x1 and np.array_equal(s[y,end],s[y,x]):end+=1
      key=(x,end,color);current[key]=active.get(key,y);x=end
    for key,start in active.items():
     if key not in current:
      a,c,color=key;rects.append({'box':[a,start,c,y],'rgba':list(color)})
    active=current
   a,b,c,d=[t*8 for t in box];mask[b:d,a:c]=True;material=nn[b:d,a:c,:3].astype('float32');detail=3*np.tanh(grain[b:d,a:c]*.35/3);out[b:d,a:c,:3]=np.rint(np.clip(material+detail,0,255)).astype('uint8');out[b:d,a:c,3]=nn[b:d,a:c,3];out[b:d,a:c,:3][out[b:d,a:c,3]==0]=0
  for j,z in enumerate(rects):
   x0,y0,x1,y1=z['box'];red,green,blue,alpha=z['rgba'];vectors.append(f'<rect id="r{j}" x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" fill="rgb({red},{green},{blue})" fill-opacity="{alpha/255}"/>')
  assert np.array_equal(out[:,:,3][mask],nn[:,:,3][mask]);meta={'editable_source_boxes':boxes,'palette_rectangles':rects,'source_alpha_in_mask':'exact nearest8x','grain_sigma_output':3,'grain_gain':.35,'grain_soft_bound':3,'method':'Exact original palette rectangles and alpha phase in three rectilinear atlas regions, bounded existing local WDN grain. Outside regions keeps parent; whole atlas remains pending review.','scope_limit':'Does not repair the other window/door frames, diagonal trim, top-left mechanism or lower illustrated/broken-glass regions.'}
 else:
  # Upper grid x0..15: six source dark-column locations and six horizontal rows.
  # Material interpretation remains tied to source colors; fade interruptions
  # are retained in each narrow row/column profile.
  xb=[2,4,7,10,13,15];yb=[1,6,12,18,24,29];base=p[:,:,:3].astype('float32').copy();regions=[];coverage=np.zeros((256,128),np.uint8)
  for y0,y1 in zip([0,1,2,6,7,12,13,18,19,24,25,29,30],[1,2,6,7,12,13,18,19,24,25,29,30,32]):
   for x0,x1 in zip([0,2,3,4,5,7,8,10,11,13,14,15],[2,3,4,5,7,8,10,11,13,14,15,16]):
    a,b,c,d=[t*8 for t in [x0,y0,x1,y1]];patch=s[y0:y1,x0:x1,:3].astype('float32');mat=cv2.resize(gaussian_filter(patch,(.65,.35,0),mode='nearest'),(c-a,d-b),interpolation=cv2.INTER_CUBIC);base[b:d,a:c]=mat;coverage[b:d,a:c]+=1;regions.append({'box':[x0,y0,x1,y1],'kind':'source seam' if x0 in xb or y0 in yb else 'pane'});vectors.append(f'<rect x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" fill="none" stroke="red" stroke-width=".05"/>')
  assert np.all(coverage==1);grain=p[:,:,:3].astype('float32')-gaussian_filter(p[:,:,:3].astype('float32'),(3,3,0),mode='nearest');base[:256,:128]+=2*np.tanh(grain[:256,:128]*.4/2);out[:256,:128,:3]=np.rint(np.clip(base[:256,:128],0,255)).astype('uint8');out[:256,:128,3]=255;mask[:256,:128]=True
  # Closed source contours, including four holes, simplified into straight
  # segments. Full source alpha topology is preserved, pixel equality is audited.
  source_mask=(s[:,:,3]>0).astype(float);source_mask[:32]=0;polygons=[]
  for contour in find_contours(np.pad(source_mask,1),.5,fully_connected='high'):
   points=(contour[:,::-1]-.5).astype('float32');poly=cv2.approxPolyDP(points,.8,True).reshape(-1,2);polygons.append(poly.tolist())
  pathdata=' '.join('M '+' L '.join(f'{x},{y}' for x,y in poly)+' Z' for poly in polygons);alpha_svg=O/'FM0113-stand-alpha-v1.svg';alpha_svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="256" height="512" viewBox="0 0 32 64"><path d="'+pathdata+'" fill="white" fill-rule="evenodd"/></svg>','utf8');alpha_render=O/'FM0113-stand-alpha-v1.png';subprocess.run([node,str(render),str(alpha_svg),str(alpha_render)],check=True,capture_output=True);a=np.asarray(Image.open(alpha_render).convert('RGBA'))[:,:,3]
  # Source RGB is recovered with alpha-aware low-frequency filtering. Local
  # fine material is bounded, so it cannot supply invented major cracks.
  alpha=s[:,:,3].astype('float32')/255;covered=gaussian_filter(alpha,.7,mode='nearest');rgb=gaussian_filter(s[:,:,:3].astype('float32')*alpha[:,:,None],(.7,.7,0),mode='nearest')/np.maximum(covered[:,:,None],1e-6);valid=covered>1e-6;near=distance_transform_edt(~valid,return_distances=False,return_indices=True);rgb[~valid]=rgb[near[0][~valid],near[1][~valid]];smooth=cv2.resize(rgb,(256,512),interpolation=cv2.INTER_CUBIC);out[256:,:,:3]=np.rint(np.clip(smooth[256:]+4*np.tanh(grain[256:]*.5/4),0,255)).astype('uint8');out[256:,:,3]=a[256:];mask[256:]=True
  # Keep fully transparent RGB at the corresponding parent's extended color;
  # only visible geometry/color is reconstructed here.
  sample=a[260::8,4::8]>=128;src=s[32:,:,3]>=128;diff=int(np.count_nonzero(sample!=src));inter=np.count_nonzero(sample&src);union=np.count_nonzero(sample|src)
  meta={'grid_vertical_source_columns':xb,'grid_horizontal_source_rows':yb,'upper_grid_regions':regions,'lower_contours_source':polygons,'alpha_vector':str(alpha_svg),'alpha_vector_sha256':sha(alpha_svg),'alpha_render':str(alpha_render),'alpha_render_sha256':sha(alpha_render),'alpha_simplification_epsilon_source':.8,'lower_source_alpha_center_mismatches':diff,'lower_source_alpha_center_IoU':inter/union,'lower_alpha_mass_ratio':float(a[256:].sum()/(s[32:,:,3].sum()*64)),'grain_sigma_output':3,'method':'Source fixed grid rectangles and simplified straight lower stand contours, alpha-aware source low-frequency color plus restrained existing local WDN grain.','scope_limit':'Upper right x16..31/y0..31 remains parent. Contour geometry preserves structure with new antialiasing; source alpha byte identity is not claimed.'}
  basepath=O/'FM0113-grid-stand-base-v1.npz';np.savez_compressed(basepath,grid_rgb=base,stand_smooth_rgb=smooth);meta.update(base_planes=str(basepath),base_planes_sha256=sha(basepath))
 assert np.array_equal(out[~mask],p[~mask]);op=O/(gid+'-source-grid-v1-8x.png');mp=O/(gid+'-source-grid-v1-mask.png');sp=O/(gid+'-source-grid-v1.svg');Image.fromarray(out).save(op);Image.fromarray(mask.astype('uint8')*255).save(mp);sp.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w*8}" height="{h*8}" viewBox="0 0 {w} {h}">'+''.join(vectors)+'</svg>','utf8')
 files.append({**{k:v[k] for k in ['group_id','source','source_ptm','source_ptm_sha256','source_rgba_sha256']},'id':gid+'-source-grid-v1','parent':v['output'],'parent_sha256':v['output_sha256'],'output':str(op),'output_sha256':sha(op),'mask':str(mp),'mask_sha256':sha(mp),'vector':str(sp),'vector_sha256':sha(sp),**meta,'outside_mask_parent_rgba_exact':True,'new_neural_passes':0,'runtime_verified':False,'release_eligible':False,'visual_review':'pending'})
 boxes=[('whole',(0,0,w,h))]
 if gid=='FM0029':boxes.extend([('grille',(30,0,57,23)),('cabinet',(54,0,94,20)),('yellow',(92,28,121,59))])
 else:boxes.extend([('upper',(0,0,32,32)),('stand',(0,32,32,64))])
 for name,box in boxes:
  ww,hh=(box[2]-box[0])*8,(box[3]-box[1])*8;scale=min(1,640/ww,512/hh) if name=='whole' else 1;sw,sh=round(ww*scale),round(hh*scale);cw=max(310,sw+16);can=Image.new('RGB',(cw*3,(sh+42)*2),'#26333f');draw=ImageDraw.Draw(can);ims=[Image.fromarray(s).crop(box).resize((ww,hh),Image.Resampling.NEAREST),Image.fromarray(p).crop(tuple(t*8 for t in box)),Image.fromarray(out).crop(tuple(t*8 for t in box))]
  for j,(im,title) in enumerate(zip(ims,['원본 · 단순 확대','로컬 WDN','원본 격자·외곽 수정'])):
   im=im.resize((sw,sh),Image.Resampling.NEAREST if j==0 else Image.Resampling.LANCZOS)
   for k,bg in enumerate(['#252d35','#d4d5d7']):
    draw.text((j*cw+6,k*(sh+42)+4),gid+' '+title,font=font,fill='white');matte=Image.new('RGB',(sw,sh),bg);matte.paste(im,(0,0),im);can.paste(matte,(j*cw+6,k*(sh+42)+34))
  pp=V/(gid+'-'+name+'-v1.png');can.save(pp);pages.append({'path':str(pp),'sha256':sha(pp),'source_box':list(box),'review_status':'pending'})
Q.write_text(json.dumps({'schema':'brs-source-grid-reconstruction/v1','previous_goal_turn_classification':'progress: FIELD-GEOMETRY-004 resolved three held structural/material groups with10 verified outputs.','catalog_before_sha256':sha(R/'qa/field_sr_catalog.json'),'geometry_contract_before_sha256':sha(R/'qa/architectural_geometry_contract.json'),'files':files,'pages':pages,'render_script':str(render),'render_script_sha256':sha(render),'new_neural_passes':0,'external_calls':0,'runtime_verified':False,'release_eligible':False},ensure_ascii=False,indent=2),'utf8')
print(json.dumps({'outputs':2,'pages':len(pages),'FM0113_alpha_center_mismatches':files[1]['lower_source_alpha_center_mismatches'],'FM0113_alpha_center_IoU':files[1]['lower_source_alpha_center_IoU']}))
