from pathlib import Path
import sys,json,hashlib
sys.dont_write_bytecode=True
import numpy as np
from scipy.ndimage import distance_transform_edt
from PIL import Image,ImageDraw,ImageFont
R=Path(r'P:\AI\Codex\projects\black-rock-shooter-hd-ui-fonts');O=R/'workspace/local-sr/field-foliage006-authored';P=R/'outputs/field-foliage006';Q=R/'qa/field_foliage006_tree_adaptation.json';assert not Q.exists();O.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text('utf8'))
z=next(v for v in read(R/'qa/field_foliage006_gpt_raw.json')['files'] if v['group_id']=='FM0314');local=read(R/'qa/field_foliage006_local.json');p=next(v for v in local['prepared_sources'] if v['group_id']=='FM0314');parent=next(v for v in local['files'] if v['id']=='FM0314-photo')
s=Image.open(z['source']).convert('RGBA');a=Image.open(z['raw_generated_image']).convert('RGBA');size=(s.width*8,s.height*8);base=np.array(a.resize(size,Image.Resampling.LANCZOS));source=np.array(s.resize(size,Image.Resampling.NEAREST));alpha=np.array(Image.open(p['alpha']));good=base[:,:,3]>=128;idx=distance_transform_edt(~good,return_distances=False,return_indices=True);rgb=base[:,:,:3].copy();rgb[~good]=rgb[idx[0][~good],idx[1][~good]]
rep={'schema':'brs-field-foliage006-tree-adaptation/v1','group_id':'FM0314','source':z['source'],'source_rgba_sha256':p['source_rgba_sha256'],'raw':z['raw_generated_image'],'raw_sha256':sha(z['raw_generated_image']),'source_alpha':p['alpha'],'source_alpha_sha256':sha(p['alpha']),'ground_source_rows':[125,128],'ground_method':'Nearest8 source RGBA rows125..127 restored exactly. Source bottom edge stays opaque and at its original UV boundary. Other pixels are unchanged from the declared variant.','files':[],'pages':[],'runtime_verified':False,'release_eligible':False}
for tag in ['drawn-alpha','source-alpha']:
 out=base.copy()
 if tag=='source-alpha':out[:,:,:3]=rgb;out[:,:,3]=alpha
 out[125*8:]=source[125*8:]
 op=O/('FM0314-GPT-'+tag+'-ground-v1-8x.png');Image.fromarray(out).save(op)
 assert np.array_equal(out[125*8:],source[125*8:])
 small=np.array(Image.fromarray(out[:,:,3]).resize(s.size,Image.Resampling.BOX));aa=np.array(s)[:,:,3];mask=small>=128;src=aa>=128
 rep['files'].append({'id':'FM0314-GPT-'+tag+'-ground-v1','output':str(op),'output_sha256':sha(op),'alpha_policy':tag,'alpha_mass_ratio':float(out[:,:,3].mean()/aa.mean()),'source_scale_alpha_IoU':float((mask&src).sum()/(mask|src).sum()),'ground_source_RGBA_exact':True,'review_status':'pending'})
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',15)
for tag,box in [('whole',None),('canopy',(28,20,68,60)),('ground',(32,96,72,128))]:
 can=Image.new('RGB',(1050,810),'#25313c');d=ImageDraw.Draw(can)
 for row,(matte,mlabel) in enumerate([('#18222c','어두운 배경'),('#dedede','밝은 배경')]):
  for col,(path,title) in enumerate([(z['source'],'원본 · 단순 확대'),(rep['files'][0]['output'],'재작화 윤곽 + 원본 지면'),(rep['files'][1]['output'],'원본 투명도 + 원본 지면')]):
   im=Image.open(path).convert('RGBA')
   if box:im=im.crop(box if col==0 else tuple(t*8 for t in box))
   scale=min(320/im.width,340/im.height);im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST if col==0 else Image.Resampling.LANCZOS);bg=Image.new('RGBA',im.size,matte);bg.alpha_composite(im);d.text((col*350+8,row*405+8),title,font=font,fill='white');d.text((col*350+8,row*405+30),mlabel,font=font,fill='#c7d1da');can.paste(bg.convert('RGB'),(col*350+(350-bg.width)//2,row*405+58+(340-bg.height)//2))
 pp=P/('FM0314-GPT-alpha-ground-'+tag+'.png');can.save(pp);rep['pages'].append({'path':str(pp),'sha256':sha(pp),'source_box':box,'review_status':'pending'})
Q.write_text(json.dumps(rep,ensure_ascii=False,indent=2),'utf8');print(json.dumps(rep['files']))
