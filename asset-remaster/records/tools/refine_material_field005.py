"""Use source-bounded material faces instead of uniformly filled grid cells."""
from pathlib import Path
import json,hashlib
import numpy as np,cv2
from scipy.ndimage import gaussian_filter
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];O=R/'workspace/local-sr/field-geometry005';V=R/'outputs/field-geometry005';Q=R/'qa/field_geometry005_material_v3.json';assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def arr(p):return np.asarray(Image.open(p).convert('RGBA'))
report=json.loads((R/'qa/field_geometry005_authored.json').read_text('utf8'));files=[];pages=[];font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17)
for v in report['files']:
 gid=v['group_id'];s=arr(v['source']);p=arr(v['output']);out=p.copy();g=arr(v['gpt_raw']);gh,gw=g.shape[:2];h,w=s.shape[:2];meta={};mask=np.zeros(p.shape[:2],bool)
 if gid=='FM0113':
  # Generated line centers are mapped to the original line centers. Flat metal
  # strips are then rendered with one invariant transverse bevel profile each.
  tx=np.array([0,2.5,4.5,7.5,10.5,13.5,15.5,16]);gx=np.array([0,3.85,7.5,11.15,14.85,18.5,21.25,21.45]);ty=np.array([0,1.5,6.5,12.5,18.5,24.5,29.5,30]);gy=np.array([0,.36,6.38,12.48,18.72,24.77,30.28,30.78]);xx=(np.arange(128)+.5)/8;yy=(np.arange(240)+.5)/8;mx=np.interp(xx,tx,gx)*gw/32-.5;my=np.interp(yy,ty,gy)*gh/64-.5;mapx,mapy=np.meshgrid(mx,my);rgb=cv2.remap(g[:,:,:3].astype('float32'),mapx.astype('float32'),mapy.astype('float32'),cv2.INTER_CUBIC)
  source_mean=s[:30,:16,:3].mean((0,1));gain=source_mean/rgb.mean((0,1));rgb*=gain
  # Half source-pixel metal divider with a narrow authored bevel. Identical
  # transverse profile along each uninterrupted segment prevents edge bowing.
  profile=np.array([87,62,60,73],np.float32)[:,None]*np.array([[1,.965,.92]],np.float32);seams=[]
  for x in tx[1:-1]:
   a=int(round(x*8))-2;rgb[:,a:a+4]=profile[None,:,:];seams.append({'axis':'vertical','center_source':float(x),'output_span':[a,a+4]})
  for y in ty[1:-1]:
   b=int(round(y*8))-2;rgb[b:b+4]=profile[:,None,:];seams.append({'axis':'horizontal','center_source':float(y),'output_span':[b,b+4]})
  out[:240,:128,:3]=np.rint(np.clip(rgb,0,255)).astype('uint8')
  # Whole source wall plane: retain new mineral surface and broad source-like
  # diagonal shadow, normalized to source mean, not a cloudy Gaussian underlay.
  donor=[21.6,0,32,30.78];a,b,c,d=[round(t*z) for t,z in zip(donor,[gw/32,gh/64,gw/32,gh/64])];wall=cv2.resize(g[b:d,a:c,:3].astype('float32'),(128,256),interpolation=cv2.INTER_CUBIC);wg=s[:32,16:,:3].mean((0,1))/wall.mean((0,1));out[:256,128:,:3]=np.rint(np.clip(wall*wg,0,255)).astype('uint8');mask[:256]=True
  meta={'method':'Source-position grid dividers with fixed transverse metal bevels, reprojected generated pane material; concrete wall plane with source-mean color normalization. Lower authored wood support from v2 unchanged.','grid_target_x':tx.tolist(),'grid_generated_x':gx.tolist(),'grid_target_y':ty.tolist(),'grid_generated_y':gy.tolist(),'grid_RGB_gain':gain.tolist(),'fixed_seam_profile_RGB':profile.tolist(),'seams':seams,'wall_donor_box_in_32x64_coordinates':donor,'wall_RGB_gain':wg.tolist(),'lower_support_RGBA_parent_exact':True,'alpha_parent_exact':True,'scope_limit':'Source line locations and rectilinear construction preserved; source fade/dither is interpreted. Wood/concrete material is art direction, not proven native metadata.'}
 else:
  palette=np.unique(s.reshape(-1,4),axis=0);gray=np.zeros((h,w),bool)
  for i in [3,4,7,9,12,13]:gray|=np.all(s==palette[i],axis=2)
  parentmask=np.asarray(Image.open(v['mask']))>0;records=[]
  for z in v['panes']:
   x0,y0,x1,y1=z['source_box'];a,b,c,d=[t*8 for t in z['source_box']];region=out[b:d,a:c,:3].astype('float32');gm=(region.mean(2)>62)&parentmask[b:d,a:c];original=s[y0:y1,x0:x1,:3][gray[y0:y1,x0:x1]];target=original.mean((0,1)) if original.ndim==3 else original.mean(0)
   # Soft selection avoids an artificial brightness threshold seam.
   current=region[gm].mean(0);base=np.array([52,36,32]);gain=np.clip((target-base)/np.maximum(current-base,1),.45,1);corrected=base+(region-base)*gain;mix=np.clip((region.mean(2)-48)/20,0,1)[:,:,None];edit=parentmask[b:d,a:c];new=np.rint(np.clip(region*(1-mix)+corrected*mix,0,255)).astype('uint8');out[b:d,a:c,:3][edit]=new[edit];mask[b:d,a:c]|=edit;records.append({'pane':z['id'],'original_gray_mean_RGB':target.tolist(),'current_gray_mean_RGB':current.tolist(),'RGB_gain_from_dark_floor':gain.tolist()})
  meta={'method':'Angular GPT glass constrained to source pane mask, with source gray-palette mean matching to reduce overbright silver reflections.','pane_tone_records':records,'outside_mask_parent_rgba_exact':True,'alpha_parent_exact':True,'scope_limit':'Glass-only candidate, not whole atlas acceptance; intact frame geometry still requires repair.'}
 assert np.array_equal(out[~mask],p[~mask]);assert np.array_equal(out[:,:,3],p[:,:,3]);op=O/(gid+'-authored-v3-8x.png');mp=O/(gid+'-authored-v3-mask.png');Image.fromarray(out).save(op);Image.fromarray(mask.astype('uint8')*255).save(mp);rec={'id':gid+'-authored-v3','group_id':gid,'source':v['source'],'source_ptm':v['source_ptm'],'source_ptm_sha256':v['source_ptm_sha256'],'source_rgba_sha256':v['source_rgba_sha256'],'parent':v['output'],'parent_sha256':sha(v['output']),'output':str(op),'output_sha256':sha(op),'mask':str(mp),'mask_sha256':sha(mp),**meta,'runtime_verified':False,'release_eligible':False};files.append(rec)
 for name,box in [('whole',[0,0,w,h]),('detail',[0,32,32,64] if gid=='FM0113' else [26,21,64,45]),('upper',[0,0,32,32] if gid=='FM0113' else [0,21,92,45])]:
  a,b,c,d=box;ww,hh=(c-a)*8,(d-b)*8;scale=min(1,640/ww,512/hh);sw,sh=round(ww*scale),round(hh*scale);cw=max(310,sw+16);can=Image.new('RGB',(cw*3,(sh+44)*2),'#26333f');draw=ImageDraw.Draw(can);ims=[Image.fromarray(s).crop(box).resize((ww,hh),Image.Resampling.NEAREST),Image.open(v['parent']).convert('RGBA').crop(tuple(t*8 for t in box)),Image.fromarray(out).crop(tuple(t*8 for t in box))]
  for j,(im,title) in enumerate(zip(ims,['원본 · 단순 확대','기존 로컬','직선 구조 · 재질 재작화'])):
   im=im.resize((sw,sh),Image.Resampling.NEAREST if j==0 else Image.Resampling.LANCZOS)
   for k,bg in enumerate(['#252d35','#d4d5d7']):
    draw.text((j*cw+6,k*(sh+44)+4),gid+' '+title,font=font,fill='white');m=Image.new('RGB',(sw,sh),bg);m.paste(im,(0,0),im);can.paste(m,(j*cw+6,k*(sh+44)+35))
  pp=V/(gid+'-'+name+'-authored-v3.png');can.save(pp);pages.append({'path':str(pp),'sha256':sha(pp),'source_box':box,'review_status':'pending'})
Q.write_text(json.dumps({'schema':'brs-authored-material-refinement/v1','parent_report_sha256':sha(R/'qa/field_geometry005_authored.json'),'files':files,'pages':pages,'new_local_inference_passes':0,'new_external_calls':0,'runtime_verified':False,'release_eligible':False},ensure_ascii=False,indent=2),'utf8');print(json.dumps({'outputs':len(files),'pages':len(pages)}))
