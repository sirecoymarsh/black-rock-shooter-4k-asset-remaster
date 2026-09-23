"""Source-coordinate SVG for the 4x4 grille which both local models erase."""
import json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import subprocess
R=Path(__file__).resolve().parents[1];Q=R/'qa/field_sr001_grid.json';assert not Q.exists()
rep=json.loads((R/'qa/field_sr001_inference.json').read_text('utf8'));row=next(v for v in rep['files'] if v['id']=='FM0078-photo');src=Image.open(row['source']).convert('RGBA');a=np.asarray(src);par=Image.open(row['output']).convert('RGBA');out=par.copy();O=Path(row['output']).parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgb(v):return '#'+''.join(f'{int(x):02x}' for x in v[:3])
# Coordinates measured on the original. This represents source-observed dark cells,
# not an assertion about physical holes or true HD bevel widths.
box=(40,45,50,56);parts=['<svg xmlns="http://www.w3.org/2000/svg" width="80" height="88" viewBox="40 45 10 11">','<defs><linearGradient id="base" x1="0" y1="0" x2="0" y2="1"><stop stop-color="'+rgb(a[45,45])+'"/><stop offset="1" stop-color="'+rgb(a[54,45])+'"/></linearGradient></defs>','<rect x="40" y="45" width="10" height="11" fill="url(#base)"/>'];cells=[]
for j,y in enumerate([47,49,51,53]):
 for i,x in enumerate([42,44,46,48]):
  base=rgb(a[y,x]);highlight=rgb(a[y,x-1]);bottom=rgb(a[y+1,x]);parts += [f'<rect x="{x-.25}" y="{y-.3}" width="1.15" height="1.2" rx=".06" fill="{base}"/>',f'<path d="M{x-.4},{y+1.03}V{y-.45}H{x+1.03}" fill="none" stroke="{highlight}" stroke-width=".26"/>',f'<path d="M{x-.2},{y+1.12}H{x+1.12}" fill="none" stroke="{bottom}" stroke-width=".22"/>'];cells.append({'column':i,'row':j,'source_center':[x,y],'source_rgba':a[y,x].tolist(),'rect':[x-.25,y-.3,1.15,1.2]})
parts += [f'<path d="M40.3,45.3V55.65H49.5" fill="none" stroke="{rgb(a[50,40])}" stroke-width=".6"/>',f'<path d="M40.3,45.3H49.55V55.65" fill="none" stroke="{rgb(a[50,49])}" stroke-width=".55"/>','</svg>']
vp=O/'FM0078-grid-source-layout.svg';vp.write_text(''.join(parts),'utf8');rp=O/'FM0078-grid-render.png'
deps=Path('C:/Users/CadriacLord/.cache/codex-runtimes/codex-primary-runtime/dependencies/node')
code='const sharp=require('+json.dumps(str(deps/'node_modules/sharp'))+');sharp(process.argv[1]).png().toFile(process.argv[2]).catch(e=>{console.error(e);process.exit(1)});'
subprocess.run([str(deps/'bin/node.exe'),'-e',code,str(vp),str(rp)],check=True)
plate=Image.open(rp).convert('RGBA');assert plate.size==(80,88);out.paste(plate,(box[0]*8,box[1]*8));op=O/'FM0078-photo-source-grid-8x.png';out.save(op)
mask=Image.new('L',out.size,0);ImageDraw.Draw(mask).rectangle((box[0]*8,box[1]*8,box[2]*8-1,box[3]*8-1),fill=255);mp=O/'FM0078-grid-mask.png';mask.save(mp)
assert np.array_equal(np.asarray(out)[np.asarray(mask)==0],np.asarray(par)[np.asarray(mask)==0])
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',19);w=440;h=440;canvas=Image.new('RGB',(1350,1000),'#25313c');d=ImageDraw.Draw(canvas)
for i,(im,title) in enumerate([(src,'원본 · 단순 확대'),(par,'로컬 · 가로선 소실'),(out,'직접 재구성 · 원본 4×4 배열')]):
 x=i*450+5;d.text((x,8),title,font=font,fill='white');crop=im.crop((36,42,54,60) if i==0 else (288,336,432,480)).resize((w,h),Image.Resampling.NEAREST if i==0 else Image.Resampling.LANCZOS);canvas.paste(crop.convert('RGB'),(x,42));canvas.paste(im.convert('RGB').resize((w,h),Image.Resampling.NEAREST if i==0 else Image.Resampling.LANCZOS),(x,515))
p=R/'outputs/field-sr001/grid-FM0078.png';canvas.save(p)
record={'schema':'brs-source-grid-redraw/v1','id':'FM0078-photo-source-grid','group_id':'FM0078','source':row['source'],'source_ptm':row['source_ptm'],'source_ptm_sha256':row['source_ptm_sha256'],'source_rgba_sha256':row['source_rgba_sha256'],'parent':str(row['output']),'parent_sha256':sha(row['output']),'vector':str(vp),'vector_sha256':sha(vp),'render':str(rp),'render_sha256':sha(rp),'mask':str(mp),'mask_sha256':sha(mp),'output':str(op),'output_sha256':sha(op),'output_size':list(out.size),'source_box':box,'authored_cells':cells,'source_grid_rows':4,'source_grid_columns':4,'new_local_neural_passes':0,'new_external_generative_calls':0,'outside_mask_rgba_exact':True,'method':'Codex-authored SVG geometry from 16 source dark-cell centers; local Photo parent outside rectangular grille. New bevel geometry is interpretation, not recovered true HD.','comparison':str(p),'comparison_sha256':sha(p),'visual_review':'pending','runtime_verified':False,'release_eligible':False}
Q.write_text(json.dumps(record,ensure_ascii=False,indent=2),'utf8');print('Saved 16-cell source-derived SVG and comparison.')
