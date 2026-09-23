from pathlib import Path
import json,hashlib
import numpy as np
from scipy.ndimage import gaussian_filter
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];Q=R/'qa/field_sr005_geometry502_v2.json';assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
old=json.loads((R/'qa/field_sr005_geometry502.json').read_text('utf8'));s=np.asarray(Image.open(old['source']).convert('RGBA'));p=np.asarray(Image.open(old['parent']).convert('RGBA'));out=p.copy();m=np.asarray(Image.open(old['mask']).convert('RGBA'))[:,:,3]>0
grain=p[:,:,:3].astype('float32')-gaussian_filter(p[:,:,:3].astype('float32'),(1.25,1.25,0),mode='nearest');grain=np.clip(grain*.25,-1,1)
# Medians remove AI waviness in the transverse section; linear interpolation
# between original texel centers avoids the v1 staircase of flat face shades.
profiles={'top':np.median(s[:6,2:126,:3],axis=1).tolist(),'bottom':np.median(s[29:,2:126,:3],axis=1).tolist(),'left':np.median(s[5:30,:3,:3],axis=0).tolist(),'right':np.median(s[5:30,125:,:3],axis=0).tolist()}
for key,a,b,origin in [('top',0,40,0),('bottom',240,256,29)]:
 ys=(np.arange(a,b)+.5)/8;profile=np.asarray(profiles[key]);vals=np.stack([np.interp(ys,np.arange(origin,origin+len(profile))+.5,profile[:,c]) for c in range(3)],1);out[a:b,:,:3]=np.rint(np.clip(vals[:,None,:]+grain[a:b],0,255)).astype('uint8')
for key,a,b,origin in [('left',0,16,0),('right',1008,1024,125)]:
 xs=(np.arange(a,b)+.5)/8;profile=np.asarray(profiles[key]);vals=np.stack([np.interp(xs,np.arange(origin,origin+len(profile))+.5,profile[:,c]) for c in range(3)],1);out[40:240,a:b,:3]=np.rint(np.clip(vals[None,:,:]+grain[40:240,a:b],0,255)).astype('uint8')
assert np.array_equal(out[~m],p[~m]);assert np.array_equal(out[:,:,3],p[:,:,3]);op=R/'workspace/local-sr/field-sr005/FM0502-source-fixed-border-v2-8x.png';Image.fromarray(out).save(op)
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17);pages=[]
for tag,box in [('whole',(0,0,128,32)),('native',(44,0,76,32)),('corner',(0,0,32,32))]:
 can=Image.new('RGB',(1050,390),'#25313c');d=ImageDraw.Draw(can)
 for col,(a,title) in enumerate([(s,'원본 · 단순 확대'),(p,'로컬 Photo'),(out,'직선·띠 음영 수정 v2')]):
  im=Image.fromarray(a).crop(box if col==0 else tuple(t*8 for t in box));scale=min(320/im.width,320/im.height) if tag=='whole' else 8 if col==0 else 1;pic=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST if col==0 else Image.Resampling.LANCZOS);d.text((col*350+8,8),'FM0502 '+title,font=font,fill='white');can.paste(pic.convert('RGB'),(col*350+(350-pic.width)//2,45+(320-pic.height)//2))
 pp=R/f'outputs/field-sr005/FM0502-fixed-v2-{tag}.png';can.save(pp);pages.append({'path':str(pp),'sha256':sha(pp),'source_box':box,'review_status':'pending_final_review'})
data={**old,'id':'FM0502-source-fixed-border-v2','output':str(op),'output_sha256':sha(op),'previous_geometry_report_sha256':sha(R/'qa/field_sr005_geometry502.json'),'method':'Source texel-center median cross-section interpolated along fixed straight border planes, with bounded local high-frequency grain. No additional neural inference.','source_profiles_rgb':profiles,'grain_sigma_output_px':1.25,'grain_gain':.25,'grain_bound_RGB':1,'pages':pages};Q.write_text(json.dumps(data,ensure_ascii=False,indent=2),'utf8');print('Saved v2 and3 pages.')
