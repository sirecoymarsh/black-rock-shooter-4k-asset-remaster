"""Authored source-coordinate facade planes with bounded existing local material."""
import hashlib, json, subprocess
from pathlib import Path
import numpy as np
import cv2
from scipy.ndimage import gaussian_filter
from PIL import Image, ImageDraw, ImageFont

R=Path(__file__).resolve().parents[1]
O=R/'workspace/local-sr/field-geometry002'; O.mkdir(exist_ok=False)
V=R/'outputs/field-geometry002'; V.mkdir(exist_ok=False)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def savejson(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),'utf8')
sources=json.loads((R/'qa/field_geometry001_sources.json').read_text('utf8'))
catalog=R/'qa/field_sr_catalog.json'; contract=R/'qa/architectural_geometry_contract.json'
node='C:/Users/CadriacLord/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
sharp='C:/Users/CadriacLord/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp'
render=O/'render.cjs'; render.write_text('const sharp=require('+json.dumps(sharp)+');sharp(process.argv[2]).png().toFile(process.argv[3]).catch(e=>{console.error(e);process.exit(1)});','utf8')
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17)
files=[]; pages=[]
for v in sources['files']:
 gid=v['group_id']
 if gid not in ['FM0189','FM0190']:continue
 src=Image.open(v['source']).convert('RGBA');parent=Image.open(v['parent']).convert('RGBA');s=np.asarray(src);p=np.asarray(parent)
 assert sha(v['source_ptm'])==v['source_ptm_sha256'] and sha(v['parent'])==v['parent_sha256']
 assert hashlib.sha256(s.tobytes()).hexdigest()==v['source_rgba_sha256']
 regions=[]
 def region(name,box,kind,**extra):regions.append({'name':name,'box':list(box),'kind':kind,**extra})
 if gid=='FM0189':
  region('left exterior molding',(0,0,3,128),'vertical',grain=2)
  region('right exterior pier',(62,0,64,128),'vertical',grain=2)
  for index,(y0,y1) in enumerate([(0,9),(43,54),(88,103)]):region(f'continuous horizontal molding {index}',(3,y0,62,y1),'horizontal',grain=3,profile_sample_x=[4,60])
  for index,(y0,y1) in enumerate([(9,43),(54,88)]):
   region(f'left frame {index}',(3,y0,5,y1),'vertical',grain=2)
   region(f'central narrow frame {index}',(31,y0,33,y1),'vertical',grain=2)
   region(f'right shaded edge {index}',(61,y0,62,y1),'vertical',grain=2)
   region(f'left glass {index}',(5,y0,31,y1),'glass',glass_ceiling=180)
   region(f'right glass {index}',(33,y0,61,y1),'glass',glass_ceiling=180)
  region('lower left jamb',(3,103,9,128),'surface',grain=3)
  region('lower right jamb',(56,103,62,128),'surface',grain=3)
  region('lower left shutter',(9,103,32,128),'shutter',grain=2)
  region('lower center seam',(32,103,33,128),'horizontal',grain=1)
  region('lower right shutter',(33,103,56,128),'shutter',grain=2)
 else:
  for index,(y0,y1) in enumerate([(0,12),(46,57),(91,103),(124,128)]):region(f'horizontal cornice {index}',(0,y0,64,y1),'horizontal',grain=5,profile_sample_x=[5,59])
  for index,(y0,y1,divider) in enumerate([(12,46,29),(57,91,74)]):
   region(f'left brick edge {index}',(0,y0,4,y1),'surface',grain=5)
   region(f'left light frame {index}',(4,y0,5,y1),'vertical',grain=3)
   region(f'central brick pier {index}',(29,y0,36,y1),'surface',grain=5)
   region(f'right light frame {index}',(36,y0,37,y1),'vertical',grain=3)
   region(f'right brick edge {index}',(61,y0,64,y1),'surface',grain=5)
   for side,a,c in [('left',5,29),('right',37,61)]:
    region(f'{side} upper glass {index}',(a,y0,c,divider),'glass',glass_ceiling=115)
    region(f'{side} lower glass {index}',(a,divider,c,y1),'glass',glass_ceiling=115)
  region('lower left pier',(0,103,9,124),'surface',grain=5)
  region('lower right pier',(56,103,64,124),'surface',grain=5)
  region('lower opening',(9,103,56,124),'glass',glass_ceiling=90)
 coverage=np.zeros(p.shape[:2],np.uint8);classmap=np.zeros(p.shape[:2],np.uint8);defs=[];rects=[]
 base=np.zeros_like(p);base[:,:,3]=255
 for i,z in enumerate(regions,1):
  x0,y0,x1,y1=z['box'];box=tuple(t*8 for t in z['box']);a,b,c,d=box
  coverage[b:d,a:c]+=1;classmap[b:d,a:c]=i
  if z['kind'] in ['horizontal','vertical']:
   patch=s[y0:y1,x0:x1,:3].astype(np.float32)
   if 'profile_sample_x' in z:xx0,xx1=z['profile_sample_x'];patch=s[y0:y1,xx0:xx1,:3].astype(np.float32)
   axis=1 if z['kind']=='horizontal' else 0
   profile=np.median(patch,axis=axis);z['profile_rgb']=profile.tolist();n=len(profile)
   stops=[]
   for j,color in enumerate(profile):stops.append(f'<stop offset="{(j+.5)/n:.9f}" stop-color="rgb({int(color[0])},{int(color[1])},{int(color[2])})"/>')
   direction='x1="0" x2="0" y1="0" y2="1"' if z['kind']=='horizontal' else 'x1="0" x2="1" y1="0" y2="0"'
   defs.append(f'<linearGradient id="g{i}" {direction}>'+''.join(stops)+'</linearGradient>')
   rects.append(f'<rect x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" fill="url(#g{i})"/>')
  else:
   rects.append(f'<rect x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" fill="black"/>')
 assert np.all(coverage==1)
 svg=O/f'{gid}-facade-planes-v1.svg';svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="512" height="1024" viewBox="0 0 64 128" shape-rendering="crispEdges"><defs>'+''.join(defs)+'</defs>'+''.join(rects)+'</svg>','utf8')
 rp=O/f'{gid}-facade-planes-v1.png';subprocess.run([node,str(render),str(svg),str(rp)],check=True,capture_output=True)
 base=np.asarray(Image.open(rp).convert('RGBA')).copy();assert np.all(base[:,:,3]==255)
 grain=p[:,:,:3].astype(np.float32)-gaussian_filter(p[:,:,:3].astype(np.float32),(8,8,0),mode='nearest')
 for i,z in enumerate(regions,1):
  x0,y0,x1,y1=z['box'];a,b,c,d=[t*8 for t in z['box']];kind=z['kind']
  if kind=='glass':
   # Interior samples provide color only, fixed rectangles define all boundaries.
   crop=p[b:d,a:c,:3];pad=8;inner=crop[pad:-pad,pad:-pad]
   material=cv2.copyMakeBorder(inner,pad,pad,pad,pad,cv2.BORDER_REPLICATE)
   base[b:d,a:c,:3]=np.minimum(material,z['glass_ceiling']);z['interior_edge_extension_output_px']=pad
  else:
   if kind=='surface':
    low=gaussian_filter(s[y0:y1,x0:x1,:3].astype(np.float32),(.55,.55,0),mode='nearest')
    material=cv2.resize(low,(c-a,d-b),interpolation=cv2.INTER_CUBIC);z['source_surface_smoothing_sigma']=.55
   elif kind=='shutter':
    patch=s[y0:y1,x0:x1,:3].astype(np.float32)
    rows=np.median(patch,axis=1);cols=np.median(patch,axis=0);column_gain=cols/np.maximum(cols.mean(axis=0),1)
    low=rows[:,None,:]*column_gain[None,:,:];material=cv2.resize(low,(c-a,d-b),interpolation=cv2.INTER_LINEAR)
    z['row_profile_rgb']=rows.tolist();z['column_gain']=column_gain.tolist()
   else:material=base[b:d,a:c,:3].astype(np.float32)
   amount=z['grain'];base[b:d,a:c,:3]=np.rint(np.clip(material+np.clip(grain[b:d,a:c]*.25,-amount,amount),0,255)).astype('uint8')
 out=O/f'{gid}-source-planes-local-material-v1-8x.png';Image.fromarray(base,'RGBA').save(out)
 cp=O/f'{gid}-regions-v1.png';Image.fromarray(classmap).save(cp)
 row={**v,'id':gid+'-source-planes-local-material-v1','regions':regions,'region_classmap':str(cp),'region_classmap_sha256':sha(cp),'vector':str(svg),'vector_sha256':sha(svg),'render':str(rp),'render_sha256':sha(rp),'output':str(out),'output_sha256':sha(out),'method':'Source-anchored complete rectangle partition; source-profile vector molding and frames, bounded existing local high-frequency material, existing local glass interiors.','output_size':[512,1024],'coverage_once_every_pixel':True,'new_local_passes':0,'external_calls':0,'visual_review':'pending','runtime_verified':False,'release_eligible':False};files.append(row)
 for kind,box in [('whole',(0,0,64,128)),('upper',(0,0,64,57)),('lower',(0,88,64,128))]:
  w=(box[2]-box[0])*8;h=(box[3]-box[1])*8;canvas=Image.new('RGB',((w+16)*3,h+42),'#26333f');draw=ImageDraw.Draw(canvas)
  ims=[src.crop(box).resize((w,h),Image.Resampling.NEAREST),parent.crop(tuple(x*8 for x in box)),Image.fromarray(base,'RGBA').crop(tuple(x*8 for x in box))]
  for j,(im,title) in enumerate(zip(ims,['원본 · 단순 확대','기존 로컬 · 보류','원본 구조 고정 · v1'])):draw.text((j*(w+16)+6,5),gid+' '+title,font=font,fill='white');canvas.paste(im.convert('RGB'),(j*(w+16)+6,36))
  path=V/f'{gid}-{kind}-v1.png';canvas.save(path);pages.append({'group_id':gid,'path':str(path),'sha256':sha(path),'source_box':box,'review_status':'pending'})
savejson(R/'qa/field_geometry002_trials.json',{'schema':'brs-facade-geometry-trials/v1','previous_goal_turn_classification':'progress: FIELD-GEOMETRY-001 replaced two window candidates, revoked two geometrically defective candidates and verified six outputs.','catalog_before_sha256':sha(catalog),'geometry_contract_before_sha256':sha(contract),'files':files,'pages':pages,'new_neural_unique_originals':0,'new_local_passes':0,'external_calls':0,'limits':['Source grain/dither is separated from authored structure; source RGB byte identity is not claimed.','Local glass edge extension by1source pixel is material extrapolation, not recovery of detail.','Brick pier material is source-smoothed color plus bounded existing local grain to avoid generated deep mortar absent from source.','Window glass horizontal change at source y29/74 is retained as a split material rectangle, not claimed to be additional physical panes.','Consumer UV/repeat, observed replacement keys and actual game appearance remain unverified.'],'runtime_verified':False,'release_eligible':False})
print(json.dumps({'outputs':len(files),'pages':len(pages),'new_local_passes':0}))
