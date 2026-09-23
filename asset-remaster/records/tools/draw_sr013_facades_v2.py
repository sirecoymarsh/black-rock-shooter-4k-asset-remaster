"""Source-measured facade drawing; no invented window count or neural passes."""
import json,hashlib,subprocess
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];O=R/'workspace/manual-redraw/sr013-facades-v2';Q=R/'qa/local_sr013_facades_v2.json'
if Q.exists():raise SystemExit('Existing attempt: use another revision.')
O.mkdir(parents=True,exist_ok=True)
cat=json.loads((R/'qa/battle_sr_catalog.json').read_text('utf8'));g=next(g for g in cat['groups'] if g['group_id']=='BM087');assert g['candidate'] is None
old=json.loads((R/'qa/local_sr012_inference.json').read_text('utf8'));par=next(r for r in old['files'] if r['group_id']=='BM087' and r['model_id']=='wdn');src=Image.open(par['source']).convert('RGBA');parent=Image.open(par['output']).convert('RGBA');a=np.asarray(src)
def sha(b):return hashlib.sha256(b).hexdigest()
assert sha(src.tobytes())==g['rgba_sha256']==par['source_rgba_sha256'];assert sha(Path(par['output']).read_bytes())==par['output_sha256']
# Explicitly observed dark row runs. These are source marks, not proof of real architectural window counts.
facades=[
 {'id':'A','box':[0,0,10,48],'rows':[[5,6],[9,11],[14,15],[19,21],[24,25],[28,30],[33,34],[37,39],[42,44]]},
 {'id':'B','box':[10,13,22,43],'rows':[[17,18],[20,22],[24,26],[28,30],[32,34],[35,37],[39,41]]},
 {'id':'C','box':[32,16,43,56],'rows':[[20,22],[24,25],[28,30],[33,34],[37,39],[41,42],[45,47],[49,51],[53,55]]},
 {'id':'D','box':[43,2,57,46],'rows':[[7,8],[11,13],[16,18],[21,23],[26,27],[30,32],[35,37],[39,41],[44,46]]},
 {'id':'E','box':[57,18,73,53],'rows':[[23,25],[28,30],[32,34],[37,39],[42,44],[47,49],[51,53]]},
 {'id':'F','box':[73,0,89,44],'rows':[[5,6],[9,11],[14,15],[19,21],[24,25],[28,30],[33,34],[37,39],[42,44]]},
 {'id':'G','box':[85,5,95,50],'rows':[[9,10],[13,14],[17,19],[23,24],[27,29],[32,34],[36,38],[41,43],[45,47],[49,50]]},
 {'id':'H','box':[95,20,107,57],'rows':[[24,26],[29,30],[33,35],[39,40],[43,44],[48,49],[52,54],[56,57]]},
 {'id':'I','box':[107,13,118,57],'rows':[[19,21],[24,25],[28,30],[34,35],[38,40],[43,44],[47,48],[52,54],[56,57]]},
 {'id':'J','box':[118,0,128,48],'rows':[[5,6],[9,11],[14,15],[19,21],[24,25],[28,30],[33,34],[37,39],[42,44]]},
]
def col(v):return '#'+''.join(f'{int(x):02x}' for x in np.rint(np.clip(v,0,255)))
node='C:/Users/CadriacLord/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe';renderer="require('C:/Users/CadriacLord/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp')(process.argv[1]).png().toFile(process.argv[2]).catch(e=>{process.stderr.write(String(e));process.exitCode=1;})"
files=[]
for variant,inset,source_mix in [('bands',.04,.3),('source-facade',.04,.6)]:
    defs=[];body=[];masks=Image.new('L',parent.size);md=ImageDraw.Draw(masks);rows_total=0;cells=0
    for f in facades:
        x0,y0,x1,y1=f['box'];wid=x1-x0;rows=f['rows'];dark={y for b,e in rows for y in range(b,e)}
        # Drawing wall colors from lighter source rows avoids the denoiser's newly invented vertical ribs.
        ys=[y for y in range(y0,y1) if y not in dark];wall=np.array([np.percentile(a[y,x0+1:max(x0+2,x1-1),:3],70,axis=0) for y in ys]);wall_y=np.arange(y0,y1);colors=np.column_stack([np.interp(wall_y,ys,wall[:,c]) for c in range(3)])
        stops=''.join(f'<stop offset="{(y-y0)/max(1,y1-y0-1):.5f}" stop-color="{col(colors[y-y0])}"/>' for y in wall_y)
        defs.append(f'<linearGradient id="wall{f["id"]}" x1="0" y1="0" x2="0" y2="1">{stops}</linearGradient>')
        body.append(f'<rect x="{x0}" y="{y0}" width="{wid}" height="{y1-y0}" fill="url(#wall{f["id"]})"/>')
        # Source edge columns are retained as shaded edge strips, with no added bright frame.
        for x in [x0,x1-1]:
            stops=''.join(f'<stop offset="{(y-y0)/max(1,y1-y0-1):.5f}" stop-color="{col(a[y,x,:3])}"/>' for y in range(y0,y1,2))
            ident=f'edge{f["id"]}{x}';defs.append(f'<linearGradient id="{ident}" x1="0" y1="0" x2="0" y2="1">{stops}</linearGradient>');body.append(f'<rect x="{x}" y="{y0}" width="1" height="{y1-y0}" fill="url(#{ident})"/>')
        for b,e in rows:
            rows_total+=1
            samples=[(x,a[b:e,x,:3].mean(0)) for x in range(x0+1,x1-1)];rid=f'row{f["id"]}{b}'
            stops=''.join(f'<stop offset="{(x-x0-1)/max(1,wid-3):.5f}" stop-color="{col(rgb)}"/>' for x,rgb in samples)
            defs.append(f'<linearGradient id="{rid}" x1="0" y1="0" x2="1" y2="0">{stops}</linearGradient>')
            body.append(f'<rect x="{x0+1}" y="{b+inset:.3f}" width="{wid-2}" height="{e-b-2*inset:.3f}" fill="url(#{rid})"/>');cells+=len(samples)
        # Fade only the lower facade transition; all marked high contrast rows are fully shown above it.
        for y in range(y0*8,y1*8):
            w=round(255*min(1,(y1*8-y)/32));md.line([(x0*8,y),(x1*8-1,y)],fill=w)
    # Small alternating roof marks are design-protected, including their irregular original phase.
    protected_box=[74,1,89,4]
    for y in range(1,4):
        for x in range(74,89):body.append(f'<rect x="{x}" y="{y}" width="1" height="1" fill="{col(a[y,x,:3])}"/>')
    svg='<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 128 128"><defs>'+''.join(defs)+'</defs>'+''.join(body)+'</svg>';vp=O/f'BM087-{variant}.svg';vp.write_text(svg,'utf8');rp=O/f'BM087-{variant}-render.png';subprocess.run([node,'-e',renderer,str(vp),str(rp)],check=True)
    render=Image.open(rp).convert('RGBA');va=np.asarray(parent).copy();paint=np.asarray(render).copy();original_rgb=np.asarray(src.convert('RGB').resize(parent.size,Image.Resampling.BICUBIC),dtype=float);color=np.asarray(paint[:,:,:3],dtype=float)*(1-source_mix)+original_rgb*source_mix;mask=np.asarray(masks,dtype=float)/255.;mask*=np.asarray(parent.getchannel('A'))>0;va[:,:,:3]=np.rint(color*mask[:,:,None]+va[:,:,:3]*(1-mask[:,:,None])).astype('uint8')
    nn=np.asarray(src.resize(parent.size,Image.Resampling.NEAREST));x0,y0,x1,y1=protected_box;va[y0*8:y1*8,x0*8:x1*8,:3]=nn[y0*8:y1*8,x0*8:x1*8,:3];mp=O/f'BM087-{variant}-mask.png';masks.save(mp);out=Image.fromarray(va);p=O/f'BM087-{variant}-8x.png';out.save(p);assert out.getchannel('A').tobytes()==parent.getchannel('A').tobytes()
    files.append({'id':'BM087-'+variant,'group_id':'BM087','source':par['source'],'source_rgba_sha256':g['rgba_sha256'],'parent':par['output'],'parent_sha256':par['output_sha256'],'alpha_parent':par['output'],'alpha_parent_sha256':par['output_sha256'],'vector':str(vp),'vector_sha256':sha(vp.read_bytes()),'render':str(rp),'render_sha256':sha(rp.read_bytes()),'mask':str(mp),'mask_sha256':sha(mp.read_bytes()),'output':str(p),'output_sha256':sha(p.read_bytes()),'output_size':list(out.size),'method':'Codex-authored continuous facade row bands without invented per-pixel mullions and source-sampled wall gradients; source color blend; local WDN retained below mask; exact roof-mark restoration','facades':facades,'drawn_row_runs':rows_total,'row_color_samples':cells,'inset_source_pixels':inset,'source_color_mix':source_mix,'protected_source_box':protected_box,'alpha_exact_to_parent':True,'new_neural_passes':0,'visual_review':'pending','runtime_verified':False,'release_eligible':False})
    print('DRAWN',variant,rows_total,cells,flush=True)
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18);pages=[]
for label,box in [('left',(0,0,64,64)),('right',(64,0,128,64)),('whole',(0,0,128,128))]:
    ims=[(src,'원본 단순 확대'),(parent,'초기 로컬 AI')]+[(Image.open(f['output']).convert('RGBA'),f['id']) for f in files];wh=(512,512);s=Image.new('RGB',(1064,1150),'#293440');d=ImageDraw.Draw(s)
    for i,(im,title) in enumerate(ims):
        x=i%2*532+8;y=i//2*575+8;d.text((x,y),title,font=font,fill='white');v=im.crop(box if i==0 else tuple(z*8 for z in box)).resize(wh,Image.Resampling.NEAREST if i==0 else Image.Resampling.LANCZOS);bg=Image.new('RGB',wh,'#72808b');bg.paste(v,(0,0),v);s.paste(bg,(x,y+34))
    p=R/f'outputs/sr013_facade_v2_{label}.png';s.save(p);pages.append(str(p))
Q.write_text(json.dumps({'schema':'brs-sr013-facades-v2/v1','files':files,'comparison_sheets':pages,'new_neural_passes':0,'image_upload':False,'runtime_verified':False,'release_eligible':False,'limitation':'Rows and cells trace observable low-resolution marks; they do not establish the number or true appearance of architectural windows.'},ensure_ascii=False,indent=2),'utf8')
