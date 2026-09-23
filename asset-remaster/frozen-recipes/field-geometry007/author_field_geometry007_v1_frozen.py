"""Source-owned masonry joints and thin ornament, using existing local RGB only."""
from pathlib import Path
import json,hashlib,subprocess
import numpy as np,cv2
from scipy.ndimage import gaussian_filter,gaussian_filter1d
from skimage.measure import find_contours
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];O=R/'workspace/local-sr/field-geometry007';P=R/'outputs/field-geometry007';Q=R/'qa/field_geometry007_authored_v1.json';assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text('utf8'))
def arr(p):return np.asarray(Image.open(p).convert('RGBA'))
audit=read(R/'qa/field_geometry007_source_audit.json');sources={v['group_id']:v for v in audit['files']};base=read(R/'qa/field_sr005_inference.json');parents={v['id']:v for v in base['files']};files=[];pages=[]
def render(svg,path):
 vp=path.with_suffix('.svg');vp.write_text(svg,'utf8');subprocess.run([r'C:\Users\CadriacLord\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe',str(R/'workspace/local-sr/field-geometry006/render.cjs'),str(vp),str(path)],check=True);return vp
def save(gid,rgb,svg,renderpath,recipe,extra):
 v=sources[gid];parent=parents[gid+'-photo'];s=arr(v['source']);out=np.dstack([np.clip(np.rint(rgb),0,255).astype('uint8'),np.full(rgb.shape[:2],255,'uint8')]);op=O/f'{gid}-authored-v1-8x.png';Image.fromarray(out).save(op);frozen=O/f'{gid}-authored-v1-planes.npz';np.savez_compressed(frozen,**extra)
 z={**{k:v[k] for k in ['group_id','source','source_ptm','source_ptm_sha256','source_rgba_sha256']},'id':gid+'-authored-v1','parent':parent['output'],'parent_sha256':parent['output_sha256'],'vector':str(svg),'vector_sha256':sha(svg),'render':str(renderpath),'render_sha256':sha(renderpath),'frozen_planes':str(frozen),'frozen_planes_sha256':sha(frozen),'output':str(op),'output_sha256':sha(op),'output_size':[out.shape[1],out.shape[0]],'recipe':recipe,'method':'Direct source geometry with existing local Photo material; zero new neural inference and zero external generation.','runtime_verified':False,'release_eligible':False};files.append(z);return z
# FM0495: seven course lines and observed irregularly-spaced vertical joints.
gid='FM0495';s=arr(sources[gid]['source']);p=arr(parents[gid+'-photo']['output']);ys=[0,3.5,11.75,20.75,30.5,40.5,49.5,58.5,64];vertical=[[],[18.5,32.5,59.5],[4.5,24.5,56.5],[16.5,43.5],[1.5,31.5,57.5],[15.5,41.5],[3.5,27.5,51.5],[16.5,41.5]]
rgb=np.zeros((512,512,3),np.float32);coverage=np.zeros((512,512),np.uint8);regions=[];lines=[];mapx=np.zeros((512,512),np.float32);mapy=np.zeros((512,512),np.float32)
for row,(y0,y1,xs) in enumerate(zip(ys[:-1],ys[1:],vertical)):
 for x0,x1 in zip([0]+xs,xs+[64]):
  ax,bx=round(x0*8),round(x1*8);ay,by=round(y0*8),round(y1*8);margin=min(1.15,(x1-x0)/5,(y1-y0)/5);mx=np.linspace((x0+margin)*8-.5,(x1-margin)*8-.5,bx-ax,dtype=np.float32);my=np.linspace((y0+margin)*8-.5,(y1-margin)*8-.5,by-ay,dtype=np.float32);xx,yy=np.meshgrid(mx,my);patch=cv2.remap(p[:,:,:3],xx,yy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE).astype('float32')
  sx0,sx1=max(0,int(np.ceil(x0+.7))),min(64,int(np.floor(x1-.7))+1);sy0,sy1=max(0,int(np.ceil(y0+.7))),min(64,int(np.floor(y1-.7))+1);target=s[sy0:sy1,sx0:sx1,:3].astype(float).mean((0,1));patch+=target-patch.mean((0,1));rgb[ay:by,ax:bx]=patch;coverage[ay:by,ax:bx]+=1;mapx[ay:by,ax:bx]=xx;mapy[ay:by,ax:bx]=yy;regions.append({'source_box':[x0,y0,x1,y1],'output_box':[ax,ay,bx,by],'donor_margin_source':margin,'source_mean_rgb':target.tolist()})
 for x in xs:lines.append({'points':[[x,y0],[x,y1]],'axis':'vertical','width':.55,'core_rgb':[130,133,131]})
for y in ys[1:-1]:
 target=np.median(s[int(y),:,:3],axis=0);color=np.rint(np.clip(target-(205-target)*.24,75,195)).astype(int).tolist();lines.append({'points':[[0,y],[64,y]],'axis':'horizontal','width':.68,'core_rgb':color})
assert np.all(coverage==1)
elements=[]
for z in lines:
 (x1,y1),(x2,y2)=z['points'];col=z['core_rgb'];color=f'rgb({col[0]},{col[1]},{col[2]})';elements.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="1.15" opacity=".28"/>');elements.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{z["width"]}"/>')
rp=O/f'{gid}-mortar-v1-render.png';vp=render('<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 64 64">'+''.join(elements)+'</svg>',rp);layer=arr(rp);a=layer[:,:,3:4]/255.;base_rgb=rgb.copy();rgb=rgb*(1-a)+layer[:,:,:3]*a
save(gid,rgb,vp,rp,{'course_y_source':ys[1:-1],'vertical_joints_by_row':vertical,'lines':lines,'regions':regions,'material':'Per-source-brick local donor inset1.15px max, source-mean color; raster overlay is the source-defined straight mortar.'},{'base_rgb':base_rgb,'coverage':coverage,'mapx':mapx,'mapy':mapy})
# FM0533: separate the warm material from a source-estimated white ornament.
gid='FM0533';s=arr(sources[gid]['source']);p=arr(parents[gid+'-photo']['output']);sub=s[104:,:,:3].astype(float);start=np.median(s[104:109,:,:3],axis=0);end=np.median(s[126:128,:,:3],axis=0);start=gaussian_filter1d(start,.7,axis=0,mode='nearest');end=gaussian_filter1d(end,.7,axis=0,mode='nearest');t=np.linspace(0,1,24)[:,None,None];clean=start[None,:,:]*(1-t)+end[None,:,:]*t
chroma=clean[:,:,0]-clean[:,:,2];alpha=np.clip(1-(sub[:,:,0]-sub[:,:,2])/np.maximum(chroma,1),0,1);alpha[alpha<.28]=0;field=cv2.resize(alpha.astype('float32'),(256,192),interpolation=cv2.INTER_CUBIC);field=gaussian_filter(field,1.35,mode='nearest');paths=[]
for contour in find_contours(np.pad(field,4),.48):
 xy=np.stack([(contour[:,1]-4+.5)/8,(contour[:,0]-4+.5)/8+104],1);xy=cv2.approxPolyDP(xy.astype('float32').reshape(-1,1,2),.08,True)[:,0,:]
 if len(xy)<4:continue
 # Smooth closed source contours, preserving their observed asymmetry.
 commands=[f'M {xy[0,0]:.5f} {xy[0,1]:.5f}']
 for i in range(len(xy)):
  p0,p1,p2,p3=xy[(i-1)%len(xy)],xy[i],xy[(i+1)%len(xy)],xy[(i+2)%len(xy)];c1=p1+(p2-p0)/6;c2=p2-(p3-p1)/6;commands.append(f'C {c1[0]:.5f} {c1[1]:.5f} {c2[0]:.5f} {c2[1]:.5f} {p2[0]:.5f} {p2[1]:.5f}')
 commands.append('Z');paths.append(' '.join(commands))
svg='<svg xmlns="http://www.w3.org/2000/svg" width="256" height="1024" viewBox="0 0 32 128"><defs><clipPath id="motif"><rect x="0" y="110" width="32" height="14"/></clipPath></defs><path clip-path="url(#motif)" fill="rgb(244,237,232)" fill-rule="evenodd" d="'+' '.join(paths)+'"/><rect x="0" y="109" width="32" height="1" fill="rgb(244,237,232)"/><rect x="0" y="124" width="32" height="1" fill="white"/></svg>'
rp=O/f'{gid}-ornament-v1-render.png';vp=render(svg,rp);layer=arr(rp);underlay=p[:,:,:3].astype('float32').copy();rgbclean=cv2.resize(clean.astype('float32'),(256,192),interpolation=cv2.INTER_LINEAR);donor=p[640:832,:,:3].astype('float32');grain=np.clip((donor-gaussian_filter(donor,(4,4,0),mode='nearest'))*.25,-1,1);rgbclean+=grain;blend=np.clip((np.arange(192)+.5)/32,0,1).astype('float32')[:,None,None];underlay[832:]=underlay[832:]*(1-blend)+rgbclean*blend;a=layer[:,:,3:4]/255.;rgb=underlay*(1-a)+layer[:,:,:3]*a
save(gid,rgb,vp,rp,{'source_background_rows_top':[104,109],'source_background_rows_bottom':[126,128],'source_chroma_opacity_threshold':.48,'opacity_prefilter_output_sigma':1.35,'curves':'Source-estimated coverage contours simplified0.08source px then closed Catmull-Rom cubic segments; no mirror symmetry imposed.','straight_bars_xywh':[[0,109,32,1],[0,124,32,1]],'motif_clip_xywh':[0,110,32,14],'upper_parent_RGBA_exact_until_source_y':104,'new_material':'Existing Photo donor y80..104 high-frequency±1 on interpolated source warm-color background; no external generation.'},{'base_rgb':underlay,'source_estimated_opacity':alpha,'source_clean_background':clean,'vector_coverage':layer[:,:,3]})
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17)
for z in files:
 gid=z['group_id'];ims=[Image.open(z['source']).convert('RGBA'),Image.open(z['parent']).convert('RGBA'),Image.open(z['output']).convert('RGBA')]
 boxes=[('whole',None),('native',(12,12,52,52) if gid=='FM0495' else (0,96,32,128))]
 for tag,box in boxes:
  can=Image.new('RGB',(1050,410),'#25313c');d=ImageDraw.Draw(can)
  for col,(im,label) in enumerate(zip(ims,['원본 · 단순 확대','로컬 Photo','원본 구조·무늬 재구성 v1'])):
   if box:im=im.crop(box if col==0 else tuple(t*8 for t in box));scale=8 if col==0 else 1
   else:scale=min(320/im.width,340/im.height)
   pic=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST if col==0 else Image.Resampling.LANCZOS);d.text((col*350+6,8),gid+' '+label,font=font,fill='white');can.paste(pic.convert('RGB'),(col*350+(350-pic.width)//2,48+(340-pic.height)//2))
  pp=P/f'{gid}-v1-{tag}.png';can.save(pp);pages.append({'path':str(pp),'sha256':sha(pp),'group_id':gid,'source_box':box,'review_status':'pending'})
program=O/'author_field_geometry007_v1_frozen.py';program.write_bytes(Path(__file__).read_bytes());report={'schema':'brs-source-geometry-material/v1','source_audit_sha256':sha(R/'qa/field_geometry007_source_audit.json'),'reconstruction_program':str(program),'reconstruction_program_sha256':sha(program),'files':files,'pages':pages,'new_local_inference_passes':0,'new_external_calls':0};Q.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8');print('2 authored outputs /4 comparisons saved.')
