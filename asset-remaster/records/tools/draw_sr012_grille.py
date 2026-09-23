"""Codex-authored vector redraw from measured source line coordinates."""
import json,hashlib,shutil,subprocess
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];O=R/'workspace/manual-redraw/sr012';O.mkdir(parents=True,exist_ok=True)
Q=R/'qa/local_sr012_manual_grille.json'
if Q.exists():raise SystemExit('Existing redraw; use a new revision.')
q=json.loads((R/'qa/local_sr012_inference.json').read_text('utf8'));r=next(r for r in q['files'] if r['group_id']=='BM110' and r['model_id']=='wdn');src=Image.open(r['source']).convert('RGBA');a=np.asarray(src)
def sha(b):return hashlib.sha256(b).hexdigest()
assert sha(src.tobytes())==r['source_rgba_sha256']
def col(x,y):return '#'+''.join(f'{v:02x}' for v in a[y,x,:3])
defs=['<clipPath id="grille"><rect x="0" y="0" width="32" height="32"/></clipPath>',
 '<linearGradient id="ring" x1="0" y1="1" x2="1" y2="0"><stop offset="0" stop-color="#7d8989"/><stop offset=".3" stop-color="#505958"/><stop offset=".5" stop-color="#414848"/><stop offset=".72" stop-color="#6c7877"/><stop offset="1" stop-color="#99a7a4"/></linearGradient>',
 '<linearGradient id="washer" x1="0" y1="1" x2="1" y2="0"><stop offset="0" stop-color="#677570"/><stop offset=".5" stop-color="#687970"/><stop offset="1" stop-color="#a8b7a7"/></linearGradient>']
body=['<g clip-path="url(#grille)">',f'<path d="M4 3H32V29H4L3 28V4Z" fill="{col(4,4)}"/>',f'<path d="M3.45 4V27.6L4.2 28.45H32" fill="none" stroke="{col(3,5)}" stroke-width=".75"/>',f'<path d="M5.5 26.5V5.5H32" fill="none" stroke="{col(5,5)}" stroke-width=".95"/>',f'<path d="M4.25 4.3H32M4.5 27.1H32" fill="none" stroke="{col(6,4)}" stroke-width=".65"/>',f'<rect x="6" y="6" width="26" height="20" fill="{col(8,7)}"/>']
horizontal=[8,10,12,14,17,19,21,23,25];vertical=[9,15,21,27]
# Color varies along the measured lines; all runs remain straight and continuous.
for y in horizontal:
    stops=''.join(f'<stop offset="{(x-7)/24:.4f}" stop-color="{col(x,y)}"/>' for x in [7,10,14,18,22,26,31])
    defs.append(f'<linearGradient id="h{y}" x1="0" y1="0" x2="1" y2="0">{stops}</linearGradient>')
    body.append(f'<rect x="7" y="{y+.1}" width="25" height=".8" fill="url(#h{y})"/>')
for x in vertical:
    stops=''.join(f'<stop offset="{(y-7)/18:.4f}" stop-color="{col(x,y)}"/>' for y in [7,9,11,13,16,18,20,22,24,25])
    defs.append(f'<linearGradient id="v{x}" x1="0" y1="0" x2="0" y2="1">{stops}</linearGradient>')
    body.append(f'<rect x="{x+.12}" y="7" width=".76" height="18" fill="url(#v{x})"/>')
for x in [11,17,23,29]:body.append(f'<rect x="{x}" y="15.1" width="3" height=".8" fill="{col(x+1,15)}"/>')
body+=['</g>',
 '<circle cx="48" cy="16" r="13" fill="#090e0b"/>',
 '<circle cx="48" cy="16" r="12.7" fill="none" stroke="url(#ring)" stroke-width=".75"/>',
 '<circle cx="48" cy="16" r="10.8" fill="none" stroke="url(#ring)" stroke-width="1.3"/>',
 '<circle cx="48" cy="16" r="8.2" fill="url(#ring)"/>',
 '<path d="M48 9.65L54.35 16L48 22.35L41.65 16Z" fill="#030805"/>',
 '<path d="M46.1 4.2H49.9V7.5H46.1ZM46.1 24.5H49.9V27.8H46.1ZM36.2 14.1H39.5V17.9H36.2ZM56.5 14.1H59.8V17.9H56.5Z" fill="#040907"/>',
 '<path d="M47.2 5.25H48.8V8.65H47.2ZM47.2 23.35H48.8V26.75H47.2ZM37.25 15.2H40.65V16.8H37.25ZM55.35 15.2H58.75V16.8H55.35Z" fill="#3e4943"/>',
 '<path d="M48 12.05C50.2 11.75 52.2 13.8 51.9 16C51.8 18.25 49.45 19.4 47.65 19.05C45.25 18.85 43.9 17.2 44.2 15.15C44.45 13.35 45.75 12.2 48 12.05Z" fill="url(#washer)"/>',
 '<path d="M47 14H49V15H50V16H49V17H47V16H46V15H47Z" fill="#020703"/>',
 '<ellipse cx="46.55" cy="17.55" rx=".65" ry=".58" fill="#060c07"/>',
 '<ellipse cx="49.4" cy="17.7" rx=".62" ry=".56" fill="#060c07"/>']
svg='<svg xmlns="http://www.w3.org/2000/svg" width="512" height="256" viewBox="0 0 64 32"><defs>'+''.join(defs)+'</defs>'+''.join(body)+'</svg>'
vp=O/'BM110-codex-vector-v1.svg';vp.write_text(svg,'utf8');raw=O/'BM110-codex-vector-v1-render.png'
node='C:/Users/CadriacLord/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
renderer="require('C:/Users/CadriacLord/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp')(process.argv[1]).png().toFile(process.argv[2]).catch(e=>{process.stderr.write(String(e));process.exitCode=1;})"
subprocess.run([node,'-e',renderer,str(vp),str(raw)],check=True);im=Image.open(raw).convert('RGBA');assert im.size==(512,256)
# The painted material is original vector work. Preserve the known source alpha boundary separately.
pixels=np.asarray(im).copy();alpha=src.getchannel('A').resize(im.size,Image.Resampling.BILINEAR);visible=pixels[:,:,3]>0
from scipy.ndimage import distance_transform_edt
near=distance_transform_edt(~visible,return_distances=False,return_indices=True);pixels[~visible,:3]=pixels[near[0][~visible],near[1][~visible],:3];final=Image.fromarray(pixels);final.putalpha(alpha);p=O/'BM110-codex-vector-v1.png';final.save(p)
generated=Path('P:/AI/Codex/generated_images/01a0c802-c7cf-7f71-a268-2f12b1fd7bd3/exec-6d6b0a99-fada-4e56-8dbb-011f77874d34.png');gp=O/'BM110-gpt-redraw-rejected.png';shutil.copyfile(generated,gp);gim=Image.open(gp).convert('RGBA');ga=np.asarray(gim.getchannel('A'));gd=gim.resize(src.size,Image.Resampling.LANCZOS);gda=np.asarray(gd.getchannel('A'));gt=a[:,:,3]>=128;pr=gda>=128
gpt={'method':'built-in image_gen reference edit','source_reference':r['source'],'source_rgba_sha256':r['source_rgba_sha256'],'output':str(gp),'output_sha256':sha(gp.read_bytes()),'output_size':list(gim.size),'image_upload':True,'decision':'rejected','reason':'Grille slat count/spacing and vertical divisions differ; oversized cardinal supports and redesigned circular center; object placement does not match original atlas.','alpha_extrema':[int(ga.min()),int(ga.max())],'downsample_alpha128_iou':float((gt&pr).sum()/(gt|pr).sum()),'runtime_verified':False,'release_eligible':False}
record={'id':'BM110-codex-vector-v1','group_id':'BM110','source':r['source'],'source_rgba_sha256':r['source_rgba_sha256'],'output':str(p),'output_sha256':sha(p.read_bytes()),'output_size':list(final.size),'vector':str(vp),'vector_sha256':sha(vp.read_bytes()),'raw_render':str(raw),'raw_render_sha256':sha(raw.read_bytes()),'method':'Codex internal authored SVG from measured original coordinates and sampled palette; rendered 8x; source bilinear alpha applied separately','new_neural_passes':0,'new_generative_calls':0,'alpha_method':'exact source bilinear8x','horizontal_slat_source_rows':horizontal,'vertical_slat_source_columns':vertical,'interrupted_source_row15_segments':[[x,15,x+3,16] for x in [11,17,23,29]],'circular_center_source_xy':[48,16],'circular_redraw_note':'Explicit source-informed manual interpretation; true lost HD detail is unknown.','visual_review':'pending','runtime_verified':False,'release_eligible':False}
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18);s=Image.new('RGB',(1596,660),'#293440');d=ImageDraw.Draw(s)
for i,color in enumerate(['#111111','#eeeeee']):
    for j,(image,label) in enumerate([(src,'원본 단순 확대'),(Image.open(r['output']).convert('RGBA'),'초기 로컬 AI'),(final,'직접 그린 벡터 후보')]):
        x=j*532+8;y=i*330+8;d.text((x,y),label,font=font,fill='white');v=image.resize((512,256),Image.Resampling.NEAREST if j==0 else Image.Resampling.LANCZOS);bg=Image.new('RGB',v.size,color);bg.paste(v,(0,0),v);s.paste(bg,(x,y+34))
sheet=R/'outputs/sr012_manual_BM110.png';s.save(sheet)
Q.write_text(json.dumps({'schema':'brs-sr012-manual-grille/v1','files':[record],'gpt_attempt':gpt,'comparison_sheets':[str(sheet)],'new_neural_passes':0,'new_generative_calls':1,'runtime_verified':False,'release_eligible':False},ensure_ascii=False,indent=2),'utf8');print(json.dumps({'output':str(p),'gpt_rejected':gpt['output_size'],'manual_review':'pending'}))
