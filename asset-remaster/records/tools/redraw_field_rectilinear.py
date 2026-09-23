"""Keep source-axis mechanical geometry exact; add bounded local material only inside it."""
import json,hashlib,subprocess
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];Q=R/'qa/field_sr003_rectilinear.json';assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
base=json.loads((R/'qa/field_sr003_inference.json').read_text('utf8'));O=R/'workspace/local-sr/field-sr003-rectilinear';O.mkdir(exist_ok=False)
node='C:/Users/CadriacLord/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe';sharp='C:/Users/CadriacLord/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp'
render=O/'render.cjs';render.write_text("const sharp=require("+json.dumps(sharp)+"); sharp(process.argv[2]).png().toFile(process.argv[3]).catch(e=>{console.error(e);process.exit(1)});",'utf8')
files=[];pages=[];font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17)
for gid,mid in [('FM0045','wdn'),('FM0120','photo')]:
 v=next(v for v in base['files'] if v['id']==gid+'-'+mid);src=Image.open(v['source']).convert('RGBA');parent=Image.open(v['output']).convert('RGBA');s=np.asarray(src);p=np.asarray(parent);assert src.size==(32,32)
 # Authored edit boundary: complete mechanical atlas, or left mechanical strip plus lower horizontal bands.
 source_mask=np.ones((32,32),bool) if gid=='FM0045' else np.indices((32,32))[1]<16
 if gid=='FM0120':source_mask[20:,:]=True
 # Compile exact source color spans as SVG rectangles, merging identical adjacent rows.
 active={};rects=[]
 for y in range(33):
  runs=[]
  if y<32:
   x=0
   while x<32:
    if not source_mask[y,x]:x+=1;continue
    x0=x;color=tuple(int(z) for z in s[y,x]);x+=1
    while x<32 and source_mask[y,x] and tuple(s[y,x])==color:x+=1
    runs.append((x0,x,color))
  keys=set(runs)
  for key,y0 in list(active.items()):
   if key not in keys:rects.append((key[0],y0,key[1]-key[0],y-y0,key[2]));del active[key]
  for key in runs:active.setdefault(key,y)
 xml=['<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 32 32" shape-rendering="crispEdges">']
 for x,y,w,h,color in rects:
  if color[3]:xml.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="rgb({color[0]},{color[1]},{color[2]})" fill-opacity="{color[3]/255:.9f}"/>')
 xml.append('</svg>');svg=O/f'{gid}-source-geometry.svg';svg.write_text('\n'.join(xml),'utf8');rp=O/f'{gid}-source-geometry.png';subprocess.run([node,str(render),str(svg),str(rp)],check=True,capture_output=True)
 geom=np.asarray(Image.open(rp).convert('RGBA'));mask=np.repeat(np.repeat(source_mask,8,0),8,1);nn=np.repeat(np.repeat(s,8,0),8,1);visible=mask&(nn[:,:,3]>0)
 assert np.array_equal(geom[:,:,3][mask],nn[:,:,3][mask]);assert np.array_equal(geom[:,:,:3][visible],nn[:,:,:3][visible])
 # Only small local high-frequency material survives; it cannot move any color-class edge.
 high=p[:,:,:3].astype(np.float32)-gaussian_filter(p[:,:,:3].astype(np.float32),(8,8,0),mode='nearest');texture=np.clip(high*.25,-4,4)
 result=p.copy();rgb=np.rint(np.clip(nn[:,:,:3].astype(np.float32)+texture,0,255)).astype('uint8');result[:,:,:3][visible]=rgb[visible];result[:,:,3][mask]=nn[:,:,3][mask];result[:,:,:3][mask&~visible]=nn[:,:,:3][mask&~visible]
 palette=np.unique(s[:,:,:3][s[:,:,3]>0],axis=0).astype(np.int16)
 # Calculate safely in int32 to avoid uint8/int16 square overflow.
 outclasses=np.argmin(((result[:,:,:3][visible,None].astype(np.int32)-palette[None].astype(np.int32))**2).sum(2),axis=1)
 sourceclasses=np.argmin(((nn[:,:,:3][visible,None].astype(np.int32)-palette[None].astype(np.int32))**2).sum(2),axis=1);assert np.array_equal(outclasses,sourceclasses)
 assert np.array_equal(result[~mask],p[~mask]);assert np.array_equal(result[:,:,3][mask],nn[:,:,3][mask]);assert np.max(abs(result[:,:,:3][visible].astype(int)-nn[:,:,:3][visible].astype(int)))<=4
 out=Image.fromarray(result,'RGBA');op=O/f'{gid}-source-rectilinear-local-material-8x.png';out.save(op);mp=O/f'{gid}-edit-mask.png';Image.fromarray(mask.astype('uint8')*255).save(mp)
 row={'id':gid+'-source-rectilinear-local-material','group_id':gid,'method':'Source-coordinate axis-aligned SVG color regions, exact source alpha and palette classes; existing local high-frequency material bounded to +/-4 RGB.','source':v['source'],'source_ptm':v['source_ptm'],'source_ptm_sha256':v['source_ptm_sha256'],'source_rgba_sha256':v['source_rgba_sha256'],'parent':v['output'],'parent_sha256':v['output_sha256'],'vector':str(svg),'vector_sha256':sha(svg),'render':str(rp),'render_sha256':sha(rp),'mask':str(mp),'mask_sha256':sha(mp),'output':str(op),'output_sha256':sha(op),'source_edit_rule':'complete32x32 mechanical atlas' if gid=='FM0045' else 'x<16 or y>=20; organic upper-right wall remains parent','source_rectangles':[[x,y,w,h,list(c)] for x,y,w,h,c in rects],'source_color_class_exact_in_mask':True,'source_nearest_alpha_exact_in_mask':True,'outside_mask_rgba_exact_to_parent':True,'rgb_delta_from_source_max':4,'new_neural_passes':0,'visual_review':'pending','runtime_verified':False,'release_eligible':False};files.append(row)
 canvas=Image.new('RGB',(840,620),'#27323b');d=ImageDraw.Draw(canvas)
 for j,(im,title) in enumerate(zip([src.resize((256,256),Image.Resampling.NEAREST),parent,out],['원본 · 단순 확대','초기 로컬','직선·직각 고정'])):
  x=j*280;d.text((x+8,8),gid+' '+title,font=font,fill='white')
  for k,bg in enumerate(['#242b33','#d4d5d7']):
   matte=Image.new('RGB',(256,256),bg);matte.paste(im,(0,0),im);canvas.paste(matte,(x+8,38+k*280))
 path=R/f'outputs/field-sr003/rectilinear-{gid}.png';canvas.save(path);pages.append({'group_id':gid,'path':str(path),'sha256':sha(path),'review_status':'pending'})
rep={'schema':'brs-field-rectilinear-reconstruction/v1','basis':'User explicitly requires intended right angles and straight lines to remain exact, since generation bends them.','new_unique_originals':0,'new_neural_passes':0,'files':files,'pages':pages,'limits':['Geometric source reconstruction is not newly recovered HD detail. Protected geometry has source-nearest color classes and alpha, while bounded neural texture supplies subtle intra-region material.','Source pixel color steps and original damage are intentionally retained; no unsupported smoothing of structural edges.','FM0120 organic upper-right wall is outside the edit mask.','SVG rectangles have no rounded corners; all stored edges are axis-aligned. This only proves the declared edit region.'],'runtime_verified':False,'release_eligible':False}
Q.write_text(json.dumps(rep,ensure_ascii=False,indent=2),'utf8');print(json.dumps({'geometry_outputs':len(files),'new_neural_passes':0,'pages':[p['path'] for p in pages]}))
