"""Trace the source's fifteen material-color planes instead of inventing metallic texture."""
import json,hashlib,subprocess
from pathlib import Path
import numpy as np,cv2
from scipy.ndimage import distance_transform_edt
from skimage.measure import find_contours
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];O=R/'workspace/manual-redraw/sr013-rubble';Q=R/'qa/local_sr013_rubble.json'
if Q.exists():raise SystemExit('Existing attempt; use a new revision.')
O.mkdir(parents=True,exist_ok=True)
q=json.loads((R/'qa/local_sr012_inference.json').read_text('utf8'));r=next(r for r in q['files'] if r['group_id']=='BM115' and r['model_id']=='wdn');src=Image.open(r['source']).convert('RGBA');parent=Image.open(r['output']).convert('RGBA');a=np.asarray(src);visible=a[:,:,3]>0
def sha(b):return hashlib.sha256(b).hexdigest()
assert sha(src.tobytes())==r['source_rgba_sha256'];assert sha(Path(r['output']).read_bytes())==r['output_sha256']
palette,counts=np.unique(a[visible,:3],axis=0,return_counts=True);assert len(palette)==15
filled=a[:,:,:3].copy();near=distance_transform_edt(~visible,return_distances=False,return_indices=True);filled[~visible]=filled[near[0][~visible],near[1][~visible]];base=Image.fromarray(filled).resize(parent.size,Image.Resampling.BICUBIC).convert('RGBA');base.putalpha(255)
node='C:/Users/CadriacLord/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe';renderer="require('C:/Users/CadriacLord/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp')(process.argv[1]).png().toFile(process.argv[2]).catch(e=>{process.stderr.write(String(e));process.exitCode=1;})"
def curve(points,rounding):
    points=np.asarray(points,float)
    if np.allclose(points[0],points[-1]):points=points[:-1]
    if len(points)<3:return ''
    ins=[];outs=[]
    for i,p in enumerate(points):
        prev=points[i-1];nxt=points[(i+1)%len(points)];d1=np.linalg.norm(prev-p);d2=np.linalg.norm(nxt-p);ins.append(p+(prev-p)*min(.4,rounding/max(d1,1e-9)));outs.append(p+(nxt-p)*min(.4,rounding/max(d2,1e-9)))
    chunks=[f'M{ins[0][0]:.4f},{ins[0][1]:.4f}']
    for i,p in enumerate(points):
        if i:chunks.append(f'L{ins[i][0]:.4f},{ins[i][1]:.4f}')
        chunks.append(f'Q{p[0]:.4f},{p[1]:.4f} {outs[i][0]:.4f},{outs[i][1]:.4f}')
    chunks.append('Z');return ' '.join(chunks)
files=[]
for name,epsilon,rounding,mix in [('planes',.15,.10,.15),('painted',.32,.22,.3)]:
    paths=[];stats=[]
    for color,count in zip(palette,counts):
        mask=np.all(a[:,:,:3]==color,2)&visible;contours=find_contours(np.pad(mask.astype('uint8'),1),.5,fully_connected='high');subpaths=[];vertices=0
        for ct in contours:
            points=ct[:,::-1]-.5;approx=cv2.approxPolyDP(points.astype(np.float32),epsilon,True).reshape(-1,2)
            if len(approx)<3:approx=points
            path=curve(approx,rounding)
            if path:subpaths.append(path);vertices+=len(approx)
        col='#'+''.join(f'{v:02x}' for v in color);paths.append(f'<path d="{" ".join(subpaths)}" fill="{col}" fill-rule="evenodd"/>');stats.append({'rgb':color.tolist(),'source_pixels':int(count),'contours':len(subpaths),'vertices':vertices})
    svg='<svg xmlns="http://www.w3.org/2000/svg" width="2048" height="512" viewBox="0 0 256 64">'+''.join(paths)+'</svg>';vp=O/f'BM115-{name}.svg';vp.write_text(svg,'utf8');rp=O/f'BM115-{name}-render.png';subprocess.run([node,'-e',renderer,str(vp),str(rp)],check=True);render=Image.open(rp).convert('RGBA');composite=Image.alpha_composite(base,render);paint=np.asarray(composite).astype(float);source=np.asarray(base).astype(float);paint[:,:,:3]=(1-mix)*paint[:,:,:3]+mix*source[:,:,:3];out=Image.fromarray(np.rint(np.clip(paint,0,255)).astype('uint8'));out.putalpha(parent.getchannel('A'));p=O/f'BM115-{name}-8x.png';out.save(p)
    assert out.getchannel('A').tobytes()==parent.getchannel('A').tobytes();files.append({'id':'BM115-'+name,'group_id':'BM115','source':r['source'],'source_rgba_sha256':r['source_rgba_sha256'],'parent':r['output'],'parent_sha256':r['output_sha256'],'alpha_parent':r['output'],'alpha_parent_sha256':r['output_sha256'],'vector':str(vp),'vector_sha256':sha(vp.read_bytes()),'render':str(rp),'render_sha256':sha(rp.read_bytes()),'output':str(p),'output_sha256':sha(p.read_bytes()),'output_size':list(out.size),'method':'Codex-directed fifteen source-color plane contours, bounded polygon simplification and quadratic corner strokes, composited over source color guide; only alpha is retained from local WDN','palette':stats,'contour_epsilon_source_px':epsilon,'corner_rounding_source_px':rounding,'source_guide_mix':mix,'new_neural_passes':0,'visual_review':'pending','runtime_verified':False,'release_eligible':False});print('DRAWN',name,sum(s['contours'] for s in stats),flush=True)
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18);pages=[]
for label,box in [('whole',(0,0,256,64)),('left',(0,0,64,64)),('middle',(64,0,128,64)),('right',(128,0,256,64))]:
    ims=[(src,'원본 단순 확대'),(parent,'초기 로컬 AI')]+[(Image.open(f['output']).convert('RGBA'),f['id']) for f in files];w=1024 if label=='whole' else 512;h=round(w*(box[3]-box[1])/(box[2]-box[0]));rh=h+60;s=Image.new('RGB',((w+20)*2,rh*2),'#293440');d=ImageDraw.Draw(s)
    for i,(im,title) in enumerate(ims):
        x=i%2*(w+20)+8;y=i//2*rh+8;d.text((x,y),title,font=font,fill='white');v=im.crop(box if i==0 else tuple(z*8 for z in box)).resize((w,h),Image.Resampling.NEAREST if i==0 else Image.Resampling.LANCZOS);bg=Image.new('RGB',v.size,'#72808b');bg.paste(v,(0,0),v);s.paste(bg,(x,y+34))
    p=R/f'outputs/sr013_rubble_{label}.png';s.save(p);pages.append(str(p))
Q.write_text(json.dumps({'schema':'brs-sr013-rubble/v1','files':files,'comparison_sheets':pages,'new_neural_passes':0,'image_upload':False,'runtime_verified':False,'release_eligible':False,'authorship':'Codex internal material treatment and tracing parameters; boundaries derived computationally from source palette, not hand-painted freeform artwork.'},ensure_ascii=False,indent=2),'utf8')
