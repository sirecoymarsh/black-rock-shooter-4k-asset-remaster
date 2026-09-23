"""Compare source-derived alpha interpolants; distinguish point samples from reduction."""
import json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];Q=R/'qa/field_sr003_alpha_rework.json';assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
rep=json.loads((R/'qa/field_sr003_inference.json').read_text('utf8'));v=next(v for v in rep['files'] if v['id']=='FM0087-wdn');src=Image.open(v['source']).convert('RGBA');parent=Image.open(v['output']).convert('RGBA');s=np.asarray(src.getchannel('A'));ref=np.asarray(Image.open(v['reference_alpha']));O=R/'workspace/local-sr/field-sr003-rework';files=[]
def metrics(im):
 a=np.asarray(im.getchannel('A'));down=np.asarray(im.getchannel('A').resize(src.size,Image.Resampling.LANCZOS));center=(a[3::8,3::8].astype(float)+a[3::8,4::8]+a[4::8,3::8]+a[4::8,4::8])/4
 result={'alpha_mass_ratio':float(a.mean()/s.mean()),'texel_center_mae':float(abs(center-s).mean()),'texel_center_max_abs_error':float(abs(center-s).max()),'source_ge16_reduced_below8':int(((s>=16)&(down<8)).sum()),'point_ious':{},'reduction_ious':{}}
 for t in [8,16,32,64,128,192,240]:
  gt=s>=t
  for key,data in [('point_ious',center),('reduction_ious',down)]:
   pred=data>=t;union=(gt|pred).sum();result[key][str(t)]=float((gt&pred).sum()/union) if union else 1.
 return result
baselines={'original_local_source_bilinear':metrics(parent),'source_alpha_nearest_control':metrics(Image.merge('RGBA',(*parent.split()[:3],src.getchannel('A').resize(parent.size,Image.Resampling.NEAREST))))}
for name,method in [('bicubic',Image.Resampling.BICUBIC),('lanczos',Image.Resampling.LANCZOS)]:
 alpha=np.clip(np.asarray(src.getchannel('A').resize(parent.size,method)),0,int(s.max())).copy();alpha[ref==0]=0;alpha[ref==255]=255;im=parent.copy();im.putalpha(Image.fromarray(alpha));p=O/f'FM0087-wdn-source-{name}-alpha-8x.png';im.save(p)
 files.append({'id':'FM0087-wdn-source-'+name+'-alpha','group_id':'FM0087','method':name,'source':v['source'],'source_ptm':v['source_ptm'],'source_ptm_sha256':v['source_ptm_sha256'],'source_rgba_sha256':v['source_rgba_sha256'],'parent':v['output'],'parent_sha256':v['output_sha256'],'reference_alpha':v['reference_alpha'],'reference_alpha_sha256':v['reference_alpha_sha256'],'output':str(p),'output_sha256':sha(p),'output_size':list(im.size),'alpha_method':'Source '+name+'8x with source max254 clamp, source-bilinear zero255 support; RGB byte-exact parent','metrics':metrics(im),'actual_local_inference_passes':0,'visual_review':'pending','runtime_verified':False,'release_eligible':False})
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17);pages=[]
for label,box in [('whole',(0,0,128,128)),('detail',(0,0,64,64))]:
 ims=[src.crop(box).resize(((box[2]-box[0])*8,(box[3]-box[1])*8),Image.Resampling.NEAREST),parent.crop(tuple(x*8 for x in box))]+[Image.open(f['output']).convert('RGBA').crop(tuple(x*8 for x in box)) for f in files]
 scale=.5 if label=='whole' else 1;wh=(round(ims[0].width*scale),round(ims[0].height*scale));cw=wh[0]+20;ch=wh[1]+36;canvas=Image.new('RGB',(cw*2,ch*4),'#26333f');d=ImageDraw.Draw(canvas)
 for i,(im,title) in enumerate(zip(ims,['원본 · 단순 확대','초기 bilinear 알파','원본 bicubic 알파','원본 Lanczos 알파'])):
  im=im.resize(wh,Image.Resampling.NEAREST if i==0 else Image.Resampling.LANCZOS)
  for j,bg in enumerate(['#242b33','#d4d5d7']):
   x=j*cw;y=i*ch;d.text((x+6,y+5),'FM0087 '+title,font=font,fill='white');matte=Image.new('RGB',wh,bg);matte.paste(im,(0,0),im);canvas.paste(matte,(x+6,y+30))
 p=R/f'outputs/field-sr003/FM0087-alpha-{label}.png';canvas.save(p);pages.append({'path':str(p),'sha256':sha(p),'source_box':list(box),'review_status':'pending'})
result={'schema':'brs-field-alpha-repair/v1','new_unique_originals':0,'new_neural_passes':0,'image_upload':False,'baselines':baselines,'files':files,'pages':pages,'limits':['Downsampled threshold IoU is not a direct simulation of native bilinear sampling or alpha-test behavior. Nearest baseline isolates this measurement limitation.','Source texel centers are bilinear samples of high-resolution alpha at pixel coordinates8*i+3.5; this is still only a discrete diagnostic.','Consumer sampler, alpha test and true high-resolution outline remain unverified.'],'runtime_verified':False,'release_eligible':False}
Q.write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf8');print(json.dumps({'baselines':baselines,'variants':{f['method']:f['metrics'] for f in files}}))
