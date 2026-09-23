"""Source-owned masonry joints and thin ornament, using existing local RGB only."""
from pathlib import Path
import json,hashlib,subprocess
import numpy as np,cv2
from scipy.ndimage import gaussian_filter,gaussian_filter1d
from skimage.measure import find_contours
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];O=R/'workspace/local-sr/field-geometry007';P=R/'outputs/field-geometry007';Q=R/'qa/field_geometry007_authored_v3.json';assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text('utf8'))
def arr(p):return np.asarray(Image.open(p).convert('RGBA'))
audit=read(R/'qa/field_geometry007_source_audit.json');sources={v['group_id']:v for v in audit['files']};base=read(R/'qa/field_sr005_inference.json');parents={v['id']:v for v in base['files']};files=[];pages=[]
def render(svg,path):
 vp=path.with_suffix('.svg');vp.write_text(svg,'utf8');subprocess.run([r'C:\Users\CadriacLord\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe',str(R/'workspace/local-sr/field-geometry006/render.cjs'),str(vp),str(path)],check=True);return vp
def save(gid,rgb,svg,renderpath,recipe,extra):
 v=sources[gid];parent=parents[gid+'-photo'];s=arr(v['source']);assert np.isfinite(rgb).all();out=np.dstack([np.clip(np.rint(rgb),0,255).astype('uint8'),np.full(rgb.shape[:2],255,'uint8')]);op=O/f'{gid}-authored-v3-8x.png';Image.fromarray(out).save(op);frozen=O/f'{gid}-authored-v3-planes.npz';np.savez_compressed(frozen,**extra)
 z={**{k:v[k] for k in ['group_id','source','source_ptm','source_ptm_sha256','source_rgba_sha256']},'id':gid+'-authored-v3','parent':parent['output'],'parent_sha256':parent['output_sha256'],'vector':str(svg),'vector_sha256':sha(svg),'render':str(renderpath),'render_sha256':sha(renderpath),'frozen_planes':str(frozen),'frozen_planes_sha256':sha(frozen),'output':str(op),'output_sha256':sha(op),'output_size':[out.shape[1],out.shape[0]],'recipe':recipe,'method':'Direct source geometry with existing local Photo material; zero new neural inference and zero external generation.','runtime_verified':False,'release_eligible':False};files.append(z);return z
# FM0495: seven course lines and observed irregularly-spaced vertical joints.
gid='FM0495';s=arr(sources[gid]['source']);p=arr(parents[gid+'-photo']['output']);ys=[0,3.5,11.75,20.75,30.5,40.5,49.5,58.5,64];vertical=[[],[19.5,32.5,60.0],[3.5,56.0],[16.5,43.5],[1.5,28.5,55.5],[15.5,41.5],[3.5,26.5,51.5],[20.5,39.5,60.0]]
rgb=np.zeros((512,512,3),np.float32);coverage=np.zeros((512,512),np.uint8);regions=[];lines=[];mapx=np.zeros((512,512),np.float32);mapy=np.zeros((512,512),np.float32)
for row,(y0,y1,xs) in enumerate(zip(ys[:-1],ys[1:],vertical)):
 for x0,x1 in zip([0]+xs,xs+[64]):
  ax,bx=round(x0*8),round(x1*8);ay,by=round(y0*8),round(y1*8);margin=min(2.2,(x1-x0)/4,(y1-y0)/4);mx=np.linspace((x0+margin)*8-.5,(x1-margin)*8-.5,bx-ax,dtype=np.float32);my=np.linspace((y0+margin)*8-.5,(y1-margin)*8-.5,by-ay,dtype=np.float32);xx,yy=np.meshgrid(mx,my);patch=cv2.remap(p[:,:,:3],xx,yy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE).astype('float32')
  sx0=max(0,int(np.ceil(x0+.35)));sx1=min(64,max(sx0+1,int(np.floor(x1-.35))+1));sy0=max(0,int(np.ceil(y0+.35)));sy1=min(64,max(sy0+1,int(np.floor(y1-.35))+1));target=s[sy0:sy1,sx0:sx1,:3].astype(float).mean((0,1));assert np.isfinite(target).all();patch+=target-patch.mean((0,1));rgb[ay:by,ax:bx]=patch;coverage[ay:by,ax:bx]+=1;mapx[ay:by,ax:bx]=xx;mapy[ay:by,ax:bx]=yy;regions.append({'source_box':[x0,y0,x1,y1],'output_box':[ax,ay,bx,by],'donor_margin_source':margin,'source_mean_rgb':target.tolist()})
 for x in xs:lines.append({'points':[[x,y0],[x,y1]],'axis':'vertical','width':.35,'core_rgb':[103,106,104]})
for y in ys[1:-1]:
 target=np.median(s[int(y),:,:3],axis=0);color=np.rint(np.clip(target-43,65,155)).astype(int).tolist();lines.append({'points':[[0,y],[64,y]],'axis':'horizontal','width':.4,'core_rgb':color})
assert np.all(coverage==1)
damage=np.zeros((64,64),np.float32)
for x0,y0,x1,y1 in [(26,34,31,40),(13,45,18,50)]:damage[y0:y1,x0:x1]=(s[y0:y1,x0:x1,:3].mean(2)<135).astype('float32')
damage=cv2.resize(gaussian_filter(damage,.3), (512,512),interpolation=cv2.INTER_LINEAR);rgb=rgb*(1-damage[:,:,None])+p[:,:,:3]*damage[:,:,None]

elements=[]
for z in lines:
 (x1,y1),(x2,y2)=z['points'];col=z['core_rgb'];color=f'rgb({col[0]},{col[1]},{col[2]})';elements.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width=".95" opacity=".15"/>');elements.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{z["width"]}"/>')
rp=O/f'{gid}-mortar-v3-render.png';vp=render('<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 64 64">'+''.join(elements)+'</svg>',rp);layer=arr(rp);a=layer[:,:,3:4]/255.;base_rgb=rgb.copy();grout_grain=np.clip((p[:,:,:3].astype('float32')-gaussian_filter(p[:,:,:3].astype('float32'),(1.25,1.25,0),mode='nearest'))*.4,-6,6);rgb=rgb*(1-a)+np.clip(layer[:,:,:3]+grout_grain,0,255)*a
save(gid,rgb,vp,rp,{'course_y_source':ys[1:-1],'vertical_joints_by_row':vertical,'lines':lines,'regions':regions,'source_anchor_revision':'Strong source-column troughs locate18 vertical seam segments; the weak sloping interior line in row12..20 is retained as material, not inserted as a new structural joint. v1/v2 had incorrect several x positions and bottom-row seam count.','source_damage_windows':[[26,34,31,40],[13,45,18,50]],'material':'Per-source-brick local donor inset2.2px max, source-mean color; raster overlay is the source-defined straight mortar.'},{'base_rgb':base_rgb,'coverage':coverage,'mapx':mapx,'mapy':mapy,'grout_grain':grout_grain,'source_damage_mask':damage})
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17)
for z in files:
 gid=z['group_id'];ims=[Image.open(z['source']).convert('RGBA'),Image.open(z['parent']).convert('RGBA'),Image.open(z['output']).convert('RGBA')]
 boxes=[('whole',None),('native',(12,12,52,52) if gid=='FM0495' else (0,96,32,128))]
 for tag,box in boxes:
  can=Image.new('RGB',(1050,410),'#25313c');d=ImageDraw.Draw(can)
  for col,(im,label) in enumerate(zip(ims,['원본 · 단순 확대','로컬 Photo','원본 구조·무늬 재구성 v3'])):
   if box:im=im.crop(box if col==0 else tuple(t*8 for t in box));scale=8 if col==0 else 1
   else:scale=min(320/im.width,340/im.height)
   pic=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST if col==0 else Image.Resampling.LANCZOS);d.text((col*350+6,8),gid+' '+label,font=font,fill='white');can.paste(pic.convert('RGB'),(col*350+(350-pic.width)//2,48+(340-pic.height)//2))
  pp=P/f'{gid}-v3-{tag}.png';can.save(pp);pages.append({'path':str(pp),'sha256':sha(pp),'group_id':gid,'source_box':box,'review_status':'pending'})
program=O/'author_field_geometry007_v3_frozen.py';program.write_bytes(Path(__file__).read_bytes());report={'schema':'brs-source-geometry-material/v3','source_audit_sha256':sha(R/'qa/field_geometry007_source_audit.json'),'reconstruction_program':str(program),'reconstruction_program_sha256':sha(program),'files':files,'pages':pages,'new_local_inference_passes':0,'new_external_calls':0,'v1_rejected_reason':'Masonry v1 empty narrow-border color ROI caused nonfinite data and a black edge; source interior crop also left doubled joints, and ornament automated coverage made thick white blobs. v3 fixes source ROI, donor inset, thinner textured joints and replaces ornamental contours with authored centerlines.'};Q.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False),'utf8');print('Masonry v3 /2 comparisons saved.')

