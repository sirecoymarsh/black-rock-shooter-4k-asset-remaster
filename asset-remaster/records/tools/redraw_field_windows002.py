"""Rectify existing local frame material onto exact source-defined straight bars."""
import json,hashlib
from pathlib import Path
import numpy as np,cv2
from scipy.ndimage import gaussian_filter1d,label
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];Q=R/'qa/field_windows002.json';assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
old=json.loads((R/'qa/field_windows001.json').read_text('utf8'));O=R/'workspace/local-sr/field-geometry001';files=[];pages=[];font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17)
for v in old['files']:
 gid=v['group_id'];src=Image.open(v['source']).convert('RGBA');parent=Image.open(v['parent']).convert('RGBA');p=np.asarray(parent);out=p.copy();plan=dict(v['plan']);x0,y0,x1,y1=plan['outer']
 if gid=='FM0258':plan['panes']=[[10,19,20,30],[21,19,31,30],[32,19,42,30],[43,19,53,30]]
 width,height=src.size;classes=np.zeros((height*8,width*8),np.uint8);mask=np.zeros(classes.shape,bool);mask[y0*8:y1*8,x0*8:x1*8]=True
 for index,(a,b,c,d) in enumerate(plan['panes'],1):classes[b*8:d*8,a*8:c*8]=index
 frame=mask&(classes==0);bar_records=[];coverage=np.zeros(classes.shape,np.uint8);lum=p[:,:,:3].astype(np.float32).mean(2)
 # One-source-pixel bar pitch is directly visible: 23/31/39 or9/20/31/42/53.
 vertical=[x0]+[b[2] for b in plan['panes']];vertical=sorted(set(vertical));horizontal=[y0,y1-1]
 for direction,positions in [('vertical',vertical),('horizontal',horizontal)]:
  for position in positions:
   nominal=position*8+3.5
   if direction=='vertical':
    ys=np.arange((y0+1)*8,(y1-1)*8);target_x=np.arange(position*8,(position+1)*8);candidates=np.arange(int(round(nominal))-5,int(round(nominal))+6);profile=lum[ys[:,None],candidates[None,:]];smooth=gaussian_filter1d(profile,1,axis=1,mode='nearest');ridge=candidates[smooth.argmax(1)].astype(np.float32);ridge=gaussian_filter1d(ridge,4,mode='nearest');mx=np.broadcast_to((target_x-nominal)[None,:],(len(ys),8)).astype(np.float32)+ridge[:,None];my=np.broadcast_to(ys[:,None],mx.shape).astype(np.float32);box=[position*8,int(ys[0]),(position+1)*8,int(ys[-1]+1)]
   else:
    xs=np.arange(x0*8,x1*8);target_y=np.arange(position*8,(position+1)*8);candidates=np.arange(int(round(nominal))-5,int(round(nominal))+6);profile=lum[candidates[:,None],xs[None,:]];smooth=gaussian_filter1d(profile,1,axis=0,mode='nearest');ridge=candidates[smooth.argmax(0)].astype(np.float32);ridge=gaussian_filter1d(ridge,4,mode='nearest');my=np.broadcast_to((target_y-nominal)[:,None],(8,len(xs))).astype(np.float32)+ridge[None,:];mx=np.broadcast_to(xs[None,:],my.shape).astype(np.float32);box=[int(xs[0]),position*8,int(xs[-1]+1),(position+1)*8]
   color=cv2.remap(p[:,:,:3],mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE);color=np.clip(color,plan['frame_floor'],253).astype('uint8');a,b,c,d=box;out[b:d,a:c,:3]=color;coverage[b:d,a:c]+=1
   tag=f'{gid}-{direction}-{position}';mapfile=O/f'{tag}-map-v2.npz';np.savez_compressed(mapfile,map_x=mx,map_y=my);bar_records.append({'direction':direction,'source_position':position,'source_nominal_center':position+.5,'output_box':box,'ridge_search_output_radius':5,'ridge_search_rule':'Mean RGB smoothed sigma1 across width, argmax, sigma4 along length; a material sampling rule, not proof of original edge positions.','map':str(mapfile),'map_sha256':sha(mapfile),'ridge_offset_range_output_px':[float((ridge-nominal).min()),float((ridge-nominal).max())]})
 assert np.all(coverage[frame]==1) and not np.any(coverage[classes>0]);out[:,:,:3][classes>0]=np.minimum(p[:,:,:3][classes>0],plan['glass_max_rgb']);out[:,:,3][mask]=255;assert np.array_equal(out[~mask],p[~mask]);assert np.all(out[:,:,3]==255)
 roi=out[y0*8:y1*8,x0*8:x1*8,:3].mean(2)<108;expected=classes[y0*8:y1*8,x0*8:x1*8]>0;assert np.array_equal(roi,expected);assert label(roi,np.ones((3,3)))[1]==len(plan['panes'])
 svg=O/f'{gid}-frame-geometry-v2.svg';rects=[]
 for x in vertical:rects.append([x,y0+1,1,y1-y0-2])
 for y in horizontal:rects.append([x0,y,x1-x0,1])
 svg.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width*8}" height="{height*8}" viewBox="0 0 {width} {height}" shape-rendering="crispEdges">'+''.join(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="white"/>' for x,y,w,h in rects)+'</svg>','utf8')
 op=O/f'{gid}-straight-windows-local-frame-v2-8x.png';Image.fromarray(out,'RGBA').save(op);mp=O/f'{gid}-straight-windows-mask-v2.png';Image.fromarray(mask.astype('uint8')*255).save(mp);cp=O/f'{gid}-window-classes-v2.png';Image.fromarray(classes).save(cp);fp=O/f'{gid}-frame-mask-v2.png';Image.fromarray(frame.astype('uint8')*255).save(fp)
 row={**{k:v[k] for k in ['group_id','source','source_ptm','source_ptm_sha256','source_rgba_sha256','parent','parent_sha256','parent_id','candidate_before']},'id':gid+'-straight-windows-local-frame-v2','method':'Source-axis rectangular frame; existing local frame material sampled onto straight bars; existing glass constrained to exact pane interiors.','plan':plan,'frame_bars':bar_records,'vector':str(svg),'vector_sha256':sha(svg),'mask':str(mp),'mask_sha256':sha(mp),'classes':str(cp),'classes_sha256':sha(cp),'frame_mask':str(fp),'frame_mask_sha256':sha(fp),'output':str(op),'output_sha256':sha(op),'output_size':[width*8,height*8],'geometry_checks':{'dark_class_threshold108_exact_to_pane_rectangles':True,'separate_panes':len(plan['panes']),'vertical_bar_source_positions':vertical,'horizontal_bar_source_positions':horizontal,'source_frame_pitch':8 if gid=='FM0257' else 11,'coverage_once_per_frame_pixel':True,'outside_mask_parent_rgba_exact':True,'opaque255':True},'new_neural_passes':0,'visual_review':'pending','runtime_verified':False,'release_eligible':False};files.append(row)
 for kind,box in [('whole',(0,0,width,height)),('windows',(max(0,x0-2),max(0,y0-2),min(width,x1+2),min(height,y1+2)))]:
  outim=Image.fromarray(out,'RGBA');ims=[src.crop(box).resize(((box[2]-box[0])*8,(box[3]-box[1])*8),Image.Resampling.NEAREST),parent.crop(tuple(t*8 for t in box)),outim.crop(tuple(t*8 for t in box))];ww,hh=ims[0].size;cw=max(ww+18,270);canvas=Image.new('RGB',(cw*3,hh+48),'#26333f');d=ImageDraw.Draw(canvas)
  for j,(im,title) in enumerate(zip(ims,['원본 · 단순 확대','기존 로컬','직선 고정 · 기존 재질'])):d.text((j*cw+6,8),gid+' '+title,font=font,fill='white');canvas.paste(im.convert('RGB'),(j*cw+6,38))
  path=R/f'outputs/field-geometry001/windows-v2-{gid}-{kind}.png';canvas.save(path);pages.append({'group_id':gid,'path':str(path),'sha256':sha(path),'source_box':list(box),'review_status':'pending'})
rep={'schema':'brs-straight-field-windows/v2','basis':'v1 source-derived frame colors looked like new flat pasted strips. v2 reuses the actual aged local frame material and fixes all frame positions independently of it.','files':files,'pages':pages,'new_neural_passes':0,'external_calls':0,'image_upload':False,'limits':['FM0258 frame peak coordinates9,20,31,42,53 establish11-source-pixel pitch. Edge gray texels are interpreted as bevel/sampling, giving four equal10-pixel openings rather than9/10/10/9 strong-dark cores.','Exact source color/lighting is not claimed; the geometry masks, high-contrast class and bar coordinates are exact to the declared source interpretation.','Ridge search only selects existing material; it is not geometry evidence. Consumer UV and runtime remain unverified.'],'runtime_verified':False,'release_eligible':False};Q.write_text(json.dumps(rep,ensure_ascii=False,indent=2),'utf8');print(json.dumps({'outputs':len(files),'rectified_bars':sum(len(v['frame_bars']) for v in files),'pages':len(pages)}))
