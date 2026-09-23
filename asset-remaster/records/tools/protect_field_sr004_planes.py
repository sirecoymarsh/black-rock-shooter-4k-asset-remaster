"""Source-anchored deterministic geometry protection over frozen local material."""
import hashlib,json
from pathlib import Path
import numpy as np,cv2
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];Q=R/'qa/field_sr004_planes.json';assert not Q.exists()
O=R/'workspace/local-sr/field-sr004';V=R/'outputs/field-sr004'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def arr(p):return np.asarray(Image.open(p).convert('RGBA'))
base=json.loads((R/'qa/field_sr004_inference.json').read_text('utf8'));rows={v['id']:v for v in base['files']}
files=[];pages=[];diagnostics={};font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17)
for gid,tag in [('FM0282','wdn'),('FM0356','photo')]:
 v=rows[gid+'-'+tag];s=arr(v['source']);p=arr(v['output']);h,w=s.shape[:2];out=p.copy();mask=np.zeros(p.shape[:2],bool);meta={}
 if gid=='FM0282':
  # Source bright support is exactly x7 and x61..63 for every source row.
  support=s[:,:,:3].mean(2)>80;expected=np.zeros((h,w),bool);expected[:,7]=True;expected[:,61:64]=True;assert np.array_equal(support,expected)
  a,b=40,80;left=p[:,a,:3].astype('float32');right=p[:,b-1,:3].astype('float32');t=np.linspace(0,1,b-a,dtype='float32')[None,:,None]
  out[:,a:b,:3]=np.rint(left[:,None,:]*(1-t)+right[:,None,:]*t).astype('uint8');mask[:,a:b]=True
  out[:,59*8:61*8,:3]=p[:,59*8,:3][:,None,:];mask[:,59*8:]=True
  profiles={}
  for x0,x1 in [(7,8),(61,64)]:
   patch=gaussian_filter1d(s[:,x0:x1,:3].astype('float32'),.65,axis=0,mode='nearest');material=np.empty((h*8,(x1-x0)*8,3),np.float32)
   for j in range(x1-x0):material[:,j*8:(j+1)*8]=cv2.resize(patch[:,j:j+1,:],(1,h*8),interpolation=cv2.INTER_LINEAR)
   out[:,x0*8:x1*8,:3]=np.rint(material).astype('uint8');profiles[str(x0)]=patch.tolist()
  e=np.repeat(np.repeat(expected,8,axis=0),8,axis=1);assert np.array_equal(out[:,:,:3].mean(2)>80,e)
  meta={'method':'Fixed source straight supports x7..8 and61..64, source vertical color profiles; existing WDN dark panel retained outside two correction bands. No new neural inference.','source_bright_boxes':[[7,0,8,64],[61,0,64,64]],'editable_source_boxes':[[5,0,10,64],[59,0,64,64]],'source_column_smoothing_sigma':.65,'saved_source_profiles':profiles,'diagnostic':{'threshold_mean_RGB':80,'source_bright_columns':[7,61,62,63],'output_bright_columns':[56,57,58,59,60,61,62,63]+list(range(488,512)),'same_support_every_row':True,'limit':'Declared two vertical supports only; consumer/UV seams and tiling remain unverified.'}}
  svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect id="fine-line" x="7" y="0" width="1" height="64"/><rect id="right-edge" x="61" y="0" width="3" height="64"/></svg>'
 else:
  # Original rows4..17 have one uniform RGB value across the complete width.
  assert np.all(s[4:18,:,:3]==[115,93,74])
  profile=np.median(s[:,:,:3].astype('float32'),axis=1);material=cv2.resize(profile[:,None,:],(w*8,h*8),interpolation=cv2.INTER_LINEAR)
  material[4*8:18*8,:,:]=[115,93,74]
  weights=np.clip((33*8-(np.arange(h*8)+.5))/(8*8),0,1).astype('float32')[:,None,None]
  out[:,:,:3]=np.rint(np.clip(material*weights+p[:,:,:3].astype('float32')*(1-weights),0,255)).astype('uint8');mask[:33*8]=True
  assert np.all(out[32:144,:,:3]==[115,93,74]);assert np.array_equal(out[264:],p[264:])
  meta={'method':'Source row-color profile protects original horizontal band; exact uniform rows4..17. Blend into frozen local Photo rubble from source y25..33; below33 unchanged. No new neural inference.','editable_source_boxes':[[0,0,128,33]],'source_row_profile_rgb':profile.tolist(),'uniform_source_box':[0,4,128,18],'uniform_rgb':[115,93,74],'blend_source_y':[25,33],'diagnostic':{'uniform_band_exact_source_color':True,'uniform_band_output_height':112,'lower_rubble_parent_rgba_exact_below_source_y':33,'limit':'Image partition and flat color verified; does not establish atlas consumers or an actual horizon.'}}
  svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 64"><rect id="original-uniform-band" x="0" y="4" width="128" height="14" fill="#735d4a"/></svg>'
 assert np.array_equal(out[~mask],p[~mask]) and np.all(out[:,:,3]==255)
 ident=gid+'-source-fixed-planes';op=O/(ident+'-8x.png');mp=O/(ident+'-mask.png');sp=O/(ident+'.svg')
 Image.fromarray(out).save(op);Image.fromarray(mask.astype('uint8')*255).save(mp);sp.write_text(svg,'utf8')
 files.append({**{k:v[k] for k in ['group_id','source','source_ptm','source_ptm_sha256','source_rgba_sha256']},'id':ident,'parent':v['output'],'parent_sha256':v['output_sha256'],'parent_model':v['model']['name'],'output':str(op),'output_sha256':sha(op),'mask':str(mp),'mask_sha256':sha(mp),'vector':str(sp),'vector_sha256':sha(sp),**meta,'outside_mask_parent_exact':True,'actual_new_local_passes':0,'visual_review':'pending','runtime_verified':False,'release_eligible':False})
 boxes=[('whole',(0,0,w,h)),('native',(0,16,32,48) if gid=='FM0282' else (40,16,72,48))]
 for label,box in boxes:
  cw,ch=(box[2]-box[0])*8,(box[3]-box[1])*8;scale=min(1,512/cw,512/ch) if label=='whole' else 1;sw,sh=round(cw*scale),round(ch*scale);col=max(300,sw+16);can=Image.new('RGB',(col*3,sh+46),'#26333f');d=ImageDraw.Draw(can)
  ims=[Image.fromarray(s).crop(box).resize((cw,ch),Image.Resampling.NEAREST),Image.fromarray(p).crop(tuple(t*8 for t in box)),Image.fromarray(out).crop(tuple(t*8 for t in box))]
  for j,(im,title) in enumerate(zip(ims,['원본 · 단순 확대','로컬 '+tag,'원본 좌표로 선·면 고정'])):
   d.text((j*col+6,5),gid+' '+title,font=font,fill='white');pic=im.resize((sw,sh),Image.Resampling.NEAREST if j==0 else Image.Resampling.LANCZOS);can.paste(pic.convert('RGB'),(j*col+6,38))
  pp=V/(gid+'-fixed-'+label+'.png');can.save(pp);pages.append({'path':str(pp),'sha256':sha(pp),'source_box':list(box),'review_status':'pending'})
for gid in ['FM0337','FM0346','FM0363']:
 v=rows[gid+'-wdn'];s=arr(v['source']);span=(4,36) if gid=='FM0337' else ((16,32) if gid=='FM0346' else (8,56));prof=s[span[0]:span[1],:,:3].mean((0,2));models={}
 for tag in ['wdn','photo']:
  o=arr(rows[gid+'-'+tag]['output']);pr=o[span[0]*8:span[1]*8,:,:3].mean((0,2));models[tag]={'profile_output':pr.tolist(),'brightness_peaks_source_x':((find_peaks(gaussian_filter1d(pr,1.2),prominence=5,distance=16)[0]+.5)/8-.5).tolist()}
 diagnostics[gid]={'source_rgba_sha256':v['source_rgba_sha256'],'source_y_span':list(span),'source_mean_profile':prof.tolist(),'source_brightness_peaks_x':find_peaks(gaussian_filter1d(prof,.15),prominence=5,distance=2)[0].tolist(),'local_profiles':models,'limit':'Brightness-profile diagnostic only, not physical column count. No visual acceptance follows from a peak match.'}
diagnostics['FM0363']['interpretation']='Source already has a dark seam at x30 (mean80.2 vs neighboring86.7 and84.9), and highlighted/dark outer rim. Revise material-only assumption in review, retaining original classified source report unchanged. Generated seam exaggeration/edge warp remains unresolved.'
Q.write_text(json.dumps({'schema':'brs-field-sr004-source-planes/v1','parent_inference_sha256':sha(R/'qa/field_sr004_inference.json'),'files':files,'pages':pages,'source_diagnostics':diagnostics,'new_neural_passes':0,'external_calls':0,'runtime_verified':False,'release_eligible':False},ensure_ascii=False,indent=2),'utf8')
print(json.dumps({'derived_outputs':len(files),'pages':len(pages),'diagnostic_groups':list(diagnostics)}))
