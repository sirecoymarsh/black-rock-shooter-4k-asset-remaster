"""Remove invented button bevels; draw the connected original grayscale lattice."""
import json,hashlib,subprocess
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];Q=R/'qa/field_sr001_grid_v2.json';assert not Q.exists()
r=json.loads((R/'qa/field_sr001_grid.json').read_text('utf8'));O=Path(r['output']).parent;s=Image.open(r['source']).convert('RGBA');a=np.asarray(s);p=Image.open(r['parent']).convert('RGBA');box=(40,45,50,56)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgb(v):return '#'+''.join(f'{int(x):02x}' for x in v[:3])
parts=['<svg xmlns="http://www.w3.org/2000/svg" width="80" height="88" viewBox="40 45 10 11">']
# Source colors supply frame pixels. The interior lattice has connected bars,
# exactly four square dark cells per row, without per-cell raised rims.
for y in range(45,56):
 for x in range(40,50):
  parts.append(f'<rect x="{x}" y="{y}" width="1" height="1" fill="{rgb(a[y,x])}"/>')
parts.append('</svg>');vp=O/'FM0078-grid-source-lattice-v2.svg';vp.write_text(''.join(parts),'utf8');rp=O/'FM0078-grid-source-lattice-v2.png';deps=Path('C:/Users/CadriacLord/.cache/codex-runtimes/codex-primary-runtime/dependencies/node');code='const sharp=require('+json.dumps(str(deps/'node_modules/sharp'))+');sharp(process.argv[1]).png().toFile(process.argv[2]).catch(e=>{console.error(e);process.exit(1)});';subprocess.run([str(deps/'bin/node.exe'),'-e',code,str(vp),str(rp)],check=True)
plate=Image.open(rp).convert('RGBA');out=p.copy();out.paste(plate,(320,360));op=O/'FM0078-photo-protected-source-lattice-8x.png';out.save(op);expected=s.crop(box).resize(plate.size,Image.Resampling.NEAREST);assert np.array_equal(np.asarray(plate),np.asarray(expected));mask=np.asarray(Image.open(r['mask']))>0;assert np.array_equal(np.asarray(out)[~mask],np.asarray(p)[~mask])
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',19);canvas=Image.new('RGB',(1350,1000),'#25313c');d=ImageDraw.Draw(canvas)
for i,(im,title) in enumerate([(s,'원본 · 단순 확대'),(p,'로컬 · 가로선 소실'),(out,'원본 격자 보호 · 재질만 AI')]):
 x=i*450+5;d.text((x,8),title,font=font,fill='white');crop=im.crop((36,42,54,60) if i==0 else (288,336,432,480)).resize((440,440),Image.Resampling.NEAREST if i==0 else Image.Resampling.LANCZOS);canvas.paste(crop.convert('RGB'),(x,42));canvas.paste(im.convert('RGB').resize((440,440),Image.Resampling.NEAREST if i==0 else Image.Resampling.LANCZOS),(x,515))
page=R/'outputs/field-sr001/grid-FM0078-v2.png';canvas.save(page)
r.update(id='FM0078-photo-protected-source-lattice',vector=str(vp),vector_sha256=sha(vp),render=str(rp),render_sha256=sha(rp),output=str(op),output_sha256=sha(op),comparison=str(page),comparison_sha256=sha(page),method='Exact source-lattice protection, expressed as SVG pixel rectangles. This region is nearest-neighbor reproduction, NOT new high-resolution detail or hand-painted artistic restoration; Photo neural material retained outside.',protected_source_pixels=110,protected_output_pixels=7040,protected_region_exact_source_nearest=True,authored_cells=None,visual_review='pending')
Q.write_text(json.dumps(r,ensure_ascii=False,indent=2),'utf8');print('Saved v2 exact-source fallback; no invented bevels or new inference.')
