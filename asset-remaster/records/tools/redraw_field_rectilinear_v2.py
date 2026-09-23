"""Authored planar panels, not a palette-pixel mosaic; straight source-defined edges."""
import json,hashlib,subprocess
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];Q=R/'qa/field_sr003_rectilinear_v2.json';assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
base=json.loads((R/'qa/field_sr003_inference.json').read_text('utf8'));v1=json.loads((R/'qa/field_sr003_rectilinear.json').read_text('utf8'));O=R/'workspace/local-sr/field-sr003-rectilinear';node='C:/Users/CadriacLord/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe';render=O/'render.cjs';files=[];pages=[];font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17)
for gid,mid,offset in [('FM0045','wdn',0),('FM0120','photo',-10)]:
 v=next(v for v in base['files'] if v['id']==gid+'-'+mid);previous=next(f for f in v1['files'] if f['group_id']==gid);src=Image.open(v['source']).convert('RGBA');parent=Image.open(v['output']).convert('RGBA');s=np.asarray(src);p=np.asarray(parent);mask=np.asarray(Image.open(previous['mask']))>0;nn=np.repeat(np.repeat(s,8,0),8,1)
 defs=[];shapes=[];regions=[]
 def rect(name,box,left,right=None):
  x,y,w,h=box;left=np.array(left);right=left if right is None else np.array(right);idx=len(regions);regions.append({'name':name,'box_xywh':box,'left_rgb':left.tolist(),'right_rgb':right.tolist(),'edge_kind':'source-axis rectangle; no corner radius'})
  defs.append(f'<linearGradient id="g{idx}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="rgb({left[0]},{left[1]},{left[2]})"/><stop offset="1" stop-color="rgb({right[0]},{right[1]},{right[2]})"/></linearGradient>')
  shapes.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#g{idx})"/>')
 def panel(x,y,width,height):
  rect('frame',[x,y,width,height],[182,183,179],[201,201,195])
  rect('brown face',[x+1,y+1,4,height-1],[82,49,16],[105,68,26])
  rect('gray face',[x+6,y+1,2,height-1],[153,153,147],[172,172,166])
  if width>9:rect('beige face',[x+9,y+1,width-10,height-1],[112,100,75],[134,119,89])
 if gid=='FM0045':
  rect('left narrow brown face',[4,0,1,32],[66,39,12],[72,42,13]);rect('left dark face',[5,0,1,32],[34,18,6],[43,24,9]);rect('left gray plane',[6,0,3,32],[150,150,144],[169,169,162]);rect('left bright edge',[9,0,1,32],[210,210,209],[219,219,218])
  rect('crossbar upper face',[0,14,10,1],[121,107,81],[215,215,214]);rect('crossbar front face',[0,15,10,1],[87,78,67],[160,160,154]);rect('crossbar lower face',[0,16,10,1],[66,39,12],[149,93,35])
 panel(11+offset,0,9,16);panel(11+offset,16,14,16)
 for y,h in [(3,1),(12,2),(15,1),(29,1),(31,1)]:
  width=9 if y<16 else 14;x=11+offset
  rect('cross rail face',[x,y,width,h],[87,78,67],[77,69,58]);rect('cross rail dark brown',[x+1,y,4,h],[34,18,6],[42,23,8]);rect('cross rail gray',[x+6,y,2,h],[67,60,52],[79,71,61])
 rect('black horizontal band',[11+offset,19,14,2],[0,0,0]);rect('brown band lower highlight',[12+offset,21,4,1],[122,76,28],[131,81,29]);rect('beige band lower highlight',[20+offset,21,4,1],[141,124,93],[150,132,98])
 if gid=='FM0120':
  # Horizontal consumer-unknown material bands retain original row extents. Organic upper wall remains parent.
  for y0,y1 in [(20,22),(22,23),(23,25),(25,26),(26,27),(27,29),(29,30),(30,31),(31,32)]:
   left=np.rint(np.mean(s[y0:y1,16:24,:3],axis=(0,1))).astype(int);right=np.rint(np.mean(s[y0:y1,24:32,:3],axis=(0,1))).astype(int);rect('lower horizontal wall band',[16,y0,16,y1-y0],left.tolist(),right.tolist())
 xml='<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 32 32" shape-rendering="crispEdges"><defs>'+''.join(defs)+'</defs>'+''.join(shapes)+'</svg>';svg=O/f'{gid}-planar-geometry-v2.svg';svg.write_text(xml,'utf8');rp=O/f'{gid}-planar-geometry-v2.png';subprocess.run([node,str(render),str(svg),str(rp)],check=True,capture_output=True);g=np.asarray(Image.open(rp).convert('RGBA'));assert np.array_equal(g[:,:,3][mask],nn[:,:,3][mask])
 visible=mask&(nn[:,:,3]>0);high=p[:,:,:3].astype(np.float32)-gaussian_filter(p[:,:,:3].astype(np.float32),(8,8,0),mode='nearest');texture=np.clip(high*.25,-4,4);out=p.copy();rgb=np.rint(np.clip(g[:,:,:3].astype(np.float32)+texture,0,255)).astype('uint8');out[:,:,:3][visible]=rgb[visible];out[:,:,3][mask]=nn[:,:,3][mask];out[:,:,:3][mask&~visible]=nn[:,:,:3][mask&~visible]
 # Source black rail rectangle has exact full width, two-source-pixel height and four square corners.
 bx=11+offset;out[19*8:21*8,bx*8:(bx+14)*8,:3]=0;assert np.all(out[19*8:21*8,bx*8:(bx+14)*8,:3]==0);assert np.array_equal(out[~mask],p[~mask]);assert np.array_equal(out[:,:,3][mask],nn[:,:,3][mask])
 im=Image.fromarray(out,'RGBA');op=O/f'{gid}-planar-geometry-local-material-v2-8x.png';im.save(op)
 row={**{k:previous[k] for k in ['group_id','source','source_ptm','source_ptm_sha256','source_rgba_sha256','parent','parent_sha256','mask','mask_sha256','source_edit_rule']},'id':gid+'-planar-geometry-local-material-v2','method':'Authored rectangular planes and linear face shading at measured source coordinates; bounded existing local high-frequency material inside; exact source alpha in protected region.','vector':str(svg),'vector_sha256':sha(svg),'render':str(rp),'render_sha256':sha(rp),'output':str(op),'output_sha256':sha(op),'regions':regions,'black_rail_source_box':[bx,19,bx+14,21],'outside_mask_rgba_exact_to_parent':True,'source_nearest_alpha_exact_in_mask':True,'new_neural_passes':0,'visual_review':'pending','runtime_verified':False,'release_eligible':False};files.append(row)
 canvas=Image.new('RGB',(840,620),'#27323b');d=ImageDraw.Draw(canvas)
 for j,(pic,title) in enumerate(zip([src.resize((256,256),Image.Resampling.NEAREST),parent,im],['원본 · 단순 확대','초기 로컬','직선·직각 재구성 v2'])):
  x=j*280;d.text((x+7,8),gid+' '+title,font=font,fill='white')
  for k,bg in enumerate(['#242b33','#d4d5d7']):
   matte=Image.new('RGB',(256,256),bg);matte.paste(pic,(0,0),pic);canvas.paste(matte,(x+8,38+k*280))
 path=R/f'outputs/field-sr003/rectilinear-v2-{gid}.png';canvas.save(path);pages.append({'group_id':gid,'path':str(path),'sha256':sha(path),'review_status':'pending'})
result={'schema':'brs-field-rectilinear-reconstruction/v2','basis':'v1 retained all source color pixels and looked blocky; v2 separates structural planes from incidental source shading.','files':files,'pages':pages,'new_neural_passes':0,'limits':['Structural boxes and source alpha are fixed; small original lighting flecks inside planes are interpreted as shading, not reproduced pixel-for-pixel.','FM0120 lower horizontal bands use source row-average face colors; unknown consumer and material meaning remain runtime requirements.','Neither vector output is counted as new AI inference or recovered native8x detail.'],'runtime_verified':False,'release_eligible':False};Q.write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf8');print(json.dumps({'outputs':len(files),'new_neural_passes':0,'pages':[p['path'] for p in pages]}))
