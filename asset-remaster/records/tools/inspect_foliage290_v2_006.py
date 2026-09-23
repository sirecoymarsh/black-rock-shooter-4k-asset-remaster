from pathlib import Path
import sys,json,hashlib,shutil
sys.dont_write_bytecode=True
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(r'P:\AI\Codex\projects\black-rock-shooter-hd-ui-fonts');Q=R/'qa/field_foliage006_weed_v2.json';assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text('utf8'))
o=R/'workspace/gpt-trials/FM0290-foliage-v2';p=read(R/'workspace/gpt-trials/FM0290-foliage-v1/provenance.json');generated=Path(r'P:\AI\Codex\generated_images\01a0c802-c7cf-7f71-a268-2f12b1fd7bd3\exec-c90c07b8-2aaf-4fbf-b5e9-dd14df68193a.png');raw=o/'generated-raw.png';assert not raw.exists();shutil.copy2(generated,raw)
s=Image.open(p['source']).convert('RGBA');im=Image.open(raw).convert('RGBA');out=im.resize((s.width*8,s.height*8),Image.Resampling.LANCZOS);op=R/'workspace/local-sr/field-foliage006-authored/FM0290-GPT-density-v2-8x.png';out.save(op)
source=np.asarray(s);a=np.asarray(out);small=np.asarray(out.getchannel('A').resize(s.size,Image.Resampling.BOX));mask=small>=128;sm=source[:,:,3]>=128
def weightmean(arr):
 aa=arr[:,:,3].astype(float)/255
 return (arr[:,:,:3]*aa[:,:,None]).sum((0,1))/aa.sum()
zones={}
for label,y0,y1 in [('upper',0,21),('middle',21,43),('lower',43,64)]:
 zones[label]={'source_alpha_mean':float(source[y0:y1,:,3].mean()),'v1_alpha_mean':float(np.asarray(Image.open(p['raw_generated_image']).getchannel('A').resize((512,512),Image.Resampling.LANCZOS))[y0*8:y1*8].mean()),'v2_alpha_mean':float(a[y0*8:y1*8,:,3].mean())}
rec={'schema':'brs-field-foliage006-weed-v2/v1','id':'FM0290-GPT-density-v2','group_id':'FM0290','source':p['source'],'source_rgba_sha256':p['source_rgba_sha256'],'references':[{'path':p['raw_generated_image'],'sha256':sha(p['raw_generated_image']),'role':'edit target; v1 too sparse'},{'path':p['reference'],'sha256':sha(p['reference']),'role':'source layout and density'}],'prompt':str(o/'prompt.txt'),'prompt_sha256':sha(o/'prompt.txt'),'tool':'built-in image_gen','model_id':'not exposed','actual_external_calls_this_revision':1,'raw_store':str(generated),'raw':str(raw),'raw_sha256':sha(raw),'raw_size':list(im.size),'output':str(op),'output_sha256':sha(op),'output_size':list(out.size),'method':'Source-guided GPT foliage repaint v2, Lanczos resampled to original8x. Generated alpha retained through RGBA resize. No replacement with fixed source alpha.','alpha_diagnostics':{'mass_ratio':float(a[:,:,3].mean()/source[:,:,3].mean()),'source_scale_IoU_at128':float((mask&sm).sum()/(mask|sm).sum()),'source_scale_disagreements_at128':int((mask!=sm).sum()),'zones':zones},'alpha_weighted_RGB_mean':{'source':weightmean(source).tolist(),'output':weightmean(a).tolist()},'review_status':'pending','runtime_verified':False,'release_eligible':False,'pages':[]}
(o/'provenance.json').write_text(json.dumps(rec,ensure_ascii=False,indent=2),'utf8')
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',15);old=next(v for v in read(R/'qa/field_foliage006_local.json')['files'] if v['id']=='FM0290-photo')
for tag,box in [('whole',None),('tips',(20,0,60,40)),('lower',(12,32,52,64))]:
 can=Image.new('RGB',(1400,810),'#25313c');d=ImageDraw.Draw(can)
 for row,(matte,mlabel) in enumerate([('#18222c','어두운 배경'),('#dedede','밝은 배경')]):
  for col,(path,title) in enumerate([(p['source'],'원본 · 단순 확대'),(old['output'],'로컬 Photo'),(p['raw_generated_image'],'GPT 1차'),(str(op),'GPT 밀도 수정')]):
   pic=Image.open(path).convert('RGBA')
   if box:
    xs=pic.width/s.width;ys=pic.height/s.height;pic=pic.crop(tuple(round(t*(xs if i%2==0 else ys)) for i,t in enumerate(box)))
   scale=min(320/pic.width,340/pic.height);pic=pic.resize((round(pic.width*scale),round(pic.height*scale)),Image.Resampling.NEAREST if col==0 else Image.Resampling.LANCZOS);bg=Image.new('RGBA',pic.size,matte);bg.alpha_composite(pic);d.text((col*350+8,row*405+8),title,font=font,fill='white');d.text((col*350+8,row*405+30),mlabel,font=font,fill='#c7d1da');can.paste(bg.convert('RGB'),(col*350+(350-bg.width)//2,row*405+58+(340-bg.height)//2))
  pp=R/'outputs/field-foliage006'/('FM0290-GPT-v2-'+tag+'.png')
 can.save(pp);rec['pages'].append({'path':str(pp),'sha256':sha(pp),'source_box':box,'review_status':'pending'})
Q.write_text(json.dumps(rec,ensure_ascii=False,indent=2),'utf8');print(json.dumps({'alpha':rec['alpha_diagnostics'],'mean':rec['alpha_weighted_RGB_mean']}))
