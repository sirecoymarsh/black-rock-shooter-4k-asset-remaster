"""Source-coordinate rectangular windows with existing local material constrained inside."""
import json,hashlib,subprocess
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter,label
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];Q=R/'qa/field_windows001.json';assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
sources=json.loads((R/'qa/field_geometry001_sources.json').read_text('utf8'));O=R/'workspace/local-sr/field-geometry001';O.mkdir(exist_ok=False)
node='C:/Users/CadriacLord/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe';sharp='C:/Users/CadriacLord/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp';render=O/'render.cjs';render.write_text('const sharp=require('+json.dumps(sharp)+');sharp(process.argv[2]).png().toFile(process.argv[3]).catch(e=>{console.error(e);process.exit(1)});','utf8')
plans={
'FM0257':{'outer':[23,9,40,20],'panes':[[24,10,31,19],[32,10,39,19]],'glass_max_rgb':64,'frame_floor':112,'bevel_width':1},
'FM0258':{'outer':[9,18,54,31],'panes':[[11,19,20,30],[21,19,31,30],[32,19,42,30],[43,19,52,30]],'glass_max_rgb':100,'frame_floor':116,'bevel_width':1}}
files=[];pages=[];font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17)
for gid,plan in plans.items():
 v=next(v for v in sources['files'] if v['group_id']==gid);src=Image.open(v['source']).convert('RGBA');parent=Image.open(v['parent']).convert('RGBA');s=np.asarray(src);p=np.asarray(parent);assert hashlib.sha256(s.tobytes()).hexdigest()==v['source_rgba_sha256'];assert sha(v['parent'])==v['parent_sha256'];scale=8;x0,y0,x1,y1=plan['outer'];w,h=src.size
 # Complete frame rectangle with exact rectangular openings. No generative boundary pixels survive.
 source_frame=np.zeros((h,w),bool);source_frame[y0:y1,x0:x1]=True;source_glass=np.zeros((h,w),np.uint8)
 for index,(a,b,c,d) in enumerate(plan['panes'],1):source_frame[b:d,a:c]=False;source_glass[b:d,a:c]=index
 # Smooth source frame color along its length. An explicit cross-face gradient gives a square bevel.
 frame_rgb=np.asarray(src.convert('RGB'),dtype=np.float32);weighted=gaussian_filter(frame_rgb*source_frame[:,:,None],(.7,.7,0),mode='nearest');weight=gaussian_filter(source_frame.astype(np.float32),.7,mode='nearest');color=np.clip(weighted/np.maximum(weight[:,:,None],1e-6),plan['frame_floor'],250)
 defs=[];shapes=[];regions=[];sid=0
 for y in range(y0,y1):
  x=x0
  while x<x1:
   if not source_frame[y,x]:x+=1;continue
   start=x;x+=1
   while x<x1 and source_frame[y,x]:x+=1
   values=color[y,start:x];stops=[]
   for j,c in enumerate(values):
    pos=0 if len(values)==1 else j/(len(values)-1);stops.append(f'<stop offset="{pos:.8f}" stop-color="rgb({int(round(c[0]))},{int(round(c[1]))},{int(round(c[2]))})"/>')
   defs.append(f'<linearGradient id="g{sid}" x1="0" y1="0" x2="1" y2="0">'+''.join(stops)+'</linearGradient>');shapes.append(f'<rect x="{start}" y="{y}" width="{x-start}" height="1" fill="url(#g{sid})"/>');regions.append([start,y,x-start,1]);sid+=1
 svg=O/f'{gid}-frame-geometry-v1.svg';svg.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w*8}" height="{h*8}" viewBox="0 0 {w} {h}" shape-rendering="crispEdges"><defs>'+''.join(defs)+'</defs>'+''.join(shapes)+'</svg>','utf8');rp=O/f'{gid}-frame-geometry-v1.png';subprocess.run([node,str(render),str(svg),str(rp)],check=True,capture_output=True);g=np.asarray(Image.open(rp).convert('RGBA'));frame=np.repeat(np.repeat(source_frame,8,0),8,1);glass=np.repeat(np.repeat(source_glass,8,0),8,1);assert np.array_equal(g[:,:,3]>0,frame)
 mask=frame|(glass>0);out=p.copy();high=p[:,:,:3].astype(np.float32)-gaussian_filter(p[:,:,:3].astype(np.float32),(8,8,0),mode='nearest');texture=np.clip(high*.2,-3,3);framecolor=np.rint(np.clip(g[:,:,:3].astype(np.float32)+texture,plan['frame_floor'],253)).astype('uint8');out[:,:,:3][frame]=framecolor[frame]
 # Keep local glass material at its source coordinates but remove leaked frame highlights.
 out[:,:,:3][glass>0]=np.minimum(p[:,:,:3][glass>0],plan['glass_max_rgb']);out[:,:,3][mask]=255
 assert np.array_equal(out[~mask],p[~mask]);assert np.all(out[:,:,3]==255);assert np.all(out[:,:,:3][frame]>=plan['frame_floor']);assert np.all(out[:,:,:3][glass>0]<=plan['glass_max_rgb'])
 roi=out[y0*8:y1*8,x0*8:x1*8,:3].mean(2)<108;expected=(glass[y0*8:y1*8,x0*8:x1*8]>0);assert np.array_equal(roi,expected);assert label(roi,np.ones((3,3)))[1]==len(plan['panes'])
 op=O/f'{gid}-straight-windows-v1-8x.png';Image.fromarray(out,'RGBA').save(op);mp=O/f'{gid}-straight-windows-mask.png';Image.fromarray(mask.astype('uint8')*255).save(mp);cp=O/f'{gid}-window-classes.png';Image.fromarray(glass).save(cp)
 row={**v,'id':gid+'-straight-windows-v1','method':'Source-coordinate rectangular panes/frame; source-smoothed frame colors; bounded local frame grain and clipped existing local glass material.','plan':plan,'vector':str(svg),'vector_sha256':sha(svg),'render':str(rp),'render_sha256':sha(rp),'mask':str(mp),'mask_sha256':sha(mp),'classes':str(cp),'classes_sha256':sha(cp),'output':str(op),'output_sha256':sha(op),'output_size':[w*8,h*8],'rectangles':regions,'geometry_checks':{'frame_mask_exact_to_plan':True,'dark_class_threshold108_exact_to_pane_rectangles':True,'separate_panes':len(plan['panes']),'outside_mask_parent_rgba_exact':True,'opaque255':True},'new_neural_passes':0,'visual_review':'pending','runtime_verified':False,'release_eligible':False};files.append(row)
 for kind,box in [('whole',(0,0,w,h)),('windows',(max(0,x0-2),max(0,y0-2),min(w,x1+2),min(h,y1+2)))]:
  outim=Image.fromarray(out,'RGBA');ims=[src.crop(box).resize(((box[2]-box[0])*8,(box[3]-box[1])*8),Image.Resampling.NEAREST),parent.crop(tuple(t*8 for t in box)),outim.crop(tuple(t*8 for t in box))];ww,hh=ims[0].size;cw=max(ww+18,270);canvas=Image.new('RGB',(cw*3,hh+48),'#26333f');d=ImageDraw.Draw(canvas)
  for j,(im,title) in enumerate(zip(ims,['원본 · 단순 확대','기존 로컬','창틀 직선·직각 고정'])):d.text((j*cw+6,8),gid+' '+title,font=font,fill='white');canvas.paste(im.convert('RGB'),(j*cw+6,38))
  path=R/f'outputs/field-geometry001/windows-{gid}-{kind}.png';canvas.save(path);pages.append({'group_id':gid,'path':str(path),'sha256':sha(path),'source_box':list(box),'review_status':'pending'})
rep={'schema':'brs-straight-field-windows/v1','files':files,'pages':pages,'new_neural_passes':0,'external_calls':0,'image_upload':False,'limits':['Source anchors define axis-aligned openings; light/dark edge pixels in the low-resolution source include weathering and sampling, so source color byte identity is not claimed.','Source-smoothed frame lightness and clipped local glass prevent generated edge pixels from reintroducing curvature, but actual texture appearance still requires direct visual review.','Unknown consumer/UV/repeat behavior and runtime remain unverified.'],'runtime_verified':False,'release_eligible':False};Q.write_text(json.dumps(rep,ensure_ascii=False,indent=2),'utf8');print(json.dumps({'outputs':len(files),'panes':sum(len(p['panes']) for p in plans.values()),'pages':len(pages)}))
