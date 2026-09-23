"""Connected source lattice; no invented individual hole bevels or outer plate."""
import json,hashlib,subprocess
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];Q=R/'qa/field_grid003.json';assert not Q.exists()
r=json.loads((R/'qa/field_sr001_grid.json').read_text('utf8'));O=Path(r['output']).parent;s=Image.open(r['source']).convert('RGBA');a=np.asarray(s);p=Image.open(r['parent']).convert('RGBA');box=(41,46,50,55)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgb(v):return '#'+''.join(f'{int(x):02x}' for x in v[:3])
defs=[];parts=[]
# Sixteen source-observed dark cells. Flat cells preserve the low-res cue rather
# than inventing a separate raised rim around each one.
cells=[]
for j,y in enumerate([47,49,51,53]):
 for i,x in enumerate([42,44,46,48]):
  parts.append(f'<rect x="{x}" y="{y}" width="1" height="1" fill="{rgb(a[y,x])}"/>');cells.append({'column':i,'row':j,'source_pixel':[x,y],'source_rgba':a[y,x].tolist(),'rect':[x,y,1,1]})
# Connected vertical/horizontal bars. Interpolate color only along each bar,
# using source sample colors; widths, openings and intersections stay fixed.
bars=[]
for x in [41,43,45,47,49]:
 stops=[(0,a[46,x]),*((((y+.5-46)/9),a[y,x]) for y in [47,49,51,53]),(1,a[54,x])];key=f'v{x}';defs.append(f'<linearGradient id="{key}" gradientUnits="userSpaceOnUse" x1="{x}" y1="46" x2="{x}" y2="55">'+''.join(f'<stop offset="{t}" stop-color="{rgb(c)}"/>' for t,c in stops)+'</linearGradient>');parts.append(f'<rect x="{x}" y="46" width="1" height="9" fill="url(#{key})"/>');bars.append({'axis':'vertical','source_bounds':[x,46,x+1,55],'stops':[[t,[int(z) for z in c]] for t,c in stops]})
for y in [46,48,50,52,54]:
 stops=[(0,a[y,41]),*((((x+.5-41)/9),a[y,x]) for x in [41,43,45,47,49]),(1,a[y,49])];key=f'h{y}';defs.append(f'<linearGradient id="{key}" gradientUnits="userSpaceOnUse" x1="41" y1="{y}" x2="50" y2="{y}">'+''.join(f'<stop offset="{t}" stop-color="{rgb(c)}"/>' for t,c in stops)+'</linearGradient>');parts.append(f'<rect x="41" y="{y}" width="9" height="1" fill="url(#{key})"/>');bars.append({'axis':'horizontal','source_bounds':[41,y,50,y+1],'stops':[[t,[int(z) for z in c]] for t,c in stops]})
svg='<svg xmlns="http://www.w3.org/2000/svg" width="72" height="72" viewBox="41 46 9 9"><defs>'+''.join(defs)+'</defs>'+''.join(parts)+'</svg>';vp=O/'FM0078-connected-grid-v3.svg';vp.write_text(svg,'utf8');rp=O/'FM0078-connected-grid-v3.png';deps=Path('C:/Users/CadriacLord/.cache/codex-runtimes/codex-primary-runtime/dependencies/node');code='const sharp=require('+json.dumps(str(deps/'node_modules/sharp'))+');sharp(process.argv[1]).png().toFile(process.argv[2]).catch(e=>{console.error(e);process.exit(1)});';subprocess.run([str(deps/'bin/node.exe'),'-e',code,str(vp),str(rp)],check=True)
plate=Image.open(rp).convert('RGBA');assert plate.size==(72,72) and plate.getchannel('A').getextrema()==(255,255);out=p.copy();out.paste(plate,(328,368));op=O/'FM0078-photo-connected-grid-v3-8x.png';out.save(op);mask=Image.new('L',out.size,0);ImageDraw.Draw(mask).rectangle((328,368,399,439),fill=255);mp=O/'FM0078-connected-grid-v3-mask.png';mask.save(mp);assert np.array_equal(np.asarray(out)[np.asarray(mask)==0],np.asarray(p)[np.asarray(mask)==0])
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',19);canvas=Image.new('RGB',(1350,1000),'#25313c');d=ImageDraw.Draw(canvas)
for i,(im,title) in enumerate([(s,'원본 · 단순 확대'),(p,'로컬 · 가로선 소실'),(out,'직접 구성 · 연결된 격자')]):
 x=i*450+5;d.text((x,8),title,font=font,fill='white');crop=im.crop((36,42,54,60) if i==0 else (288,336,432,480)).resize((440,440),Image.Resampling.NEAREST if i==0 else Image.Resampling.LANCZOS);canvas.paste(crop.convert('RGB'),(x,42));canvas.paste(im.convert('RGB').resize((440,440),Image.Resampling.NEAREST if i==0 else Image.Resampling.LANCZOS),(x,515))
page=R/'outputs/field-sr001/grid-FM0078-v3.png';canvas.save(page)
rec={**{k:r[k] for k in ['group_id','source','source_ptm','source_ptm_sha256','source_rgba_sha256','parent','parent_sha256']},'schema':'brs-source-connected-lattice/v3','id':'FM0078-photo-connected-grid-v3','vector':str(vp),'vector_sha256':sha(vp),'render':str(rp),'render_sha256':sha(rp),'mask':str(mp),'mask_sha256':sha(mp),'output':str(op),'output_sha256':sha(op),'output_size':list(out.size),'source_box':box,'cells':cells,'bars':bars,'outside_mask_rgba_exact':True,'method':'Codex-authored vector lattice with source-fixed 16 square dark cells and five connected bars per axis; interpolate source color along bars only. No additional bevel/outer frame. This is geometry reconstruction, not neural inference or invented high-frequency detail.','new_local_neural_passes':0,'new_external_generative_calls':0,'comparison':str(page),'comparison_sha256':sha(page),'visual_review':'pending','runtime_verified':False,'release_eligible':False}
Q.write_text(json.dumps(rec,ensure_ascii=False,indent=2),'utf8');print('Saved connected source lattice v3.')
