from pathlib import Path
import json,hashlib,subprocess
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];O=R/'workspace/local-sr/field-geometry008';P=R/'outputs/field-geometry008';Q=R/'qa/field_geometry008_checker489.json';assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
audit=json.loads((R/'qa/field_geometry008_source_audit.json').read_text('utf8'));v=next(z for z in audit['files'] if z['group_id']=='FM0489');s=Image.open(v['source']).convert('RGBA');a=np.asarray(s);assert s.size==(32,32);out=Image.new('RGBA',(256,256));cells=[];elements=[]
for y in range(4):
 for x in range(4):
  box=[x*8,y*8,(x+1)*8,(y+1)*8];patch=s.crop(box);gold=(x+y)%2==0
  if gold:
   assert np.all(np.asarray(patch)==[255,209,105,255]);piece=Image.new('RGBA',(64,64),(255,209,105,255));elements.append(f'<rect x="{x*8}" y="{y*8}" width="8" height="8" fill="white"/>')
  else:
   assert patch.getchannel('A').getextrema()==(64,64);piece=patch.convert('RGB').resize((64,64),Image.Resampling.BILINEAR).convert('RGBA');piece.putalpha(64)
  out.paste(piece,(x*64,y*64));cells.append({'column':x,'row':y,'source_box':box,'kind':'solid_gold' if gold else 'translucent_red_gradient','alpha':255 if gold else 64})
vp=O/'FM0489-checker-gold-mask.svg';vp.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 32 32">'+''.join(elements)+'</svg>','utf8');mp=O/'FM0489-checker-gold-mask.png';subprocess.run([r'C:\Users\CadriacLord\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe',str(R/'workspace/local-sr/field-geometry006/render.cjs'),str(vp),str(mp)],check=True);goldmask=np.asarray(Image.open(mp).convert('RGBA'))[:,:,3]==255;oa=np.asarray(out);assert np.array_equal(oa[:,:,3],np.asarray(s.getchannel('A').resize((256,256),Image.Resampling.NEAREST)));assert np.array_equal(goldmask,oa[:,:,3]==255);assert int(goldmask.sum())==32768
op=O/'FM0489-source-checker-geometry-8x.png';out.save(op);font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17);can=Image.new('RGB',(600,630),'#25313c');d=ImageDraw.Draw(can)
for row,matte in enumerate(['#202830','#dedede']):
 for col,(im,title) in enumerate([(s.resize((256,256),Image.Resampling.NEAREST),'원본 · 단순 확대'),(out,'원본 격자·색·투명도 보존')]):
  bg=Image.new('RGB',im.size,matte);bg.paste(im,(0,0),im);d.text((col*300+8,row*315+8),'FM0489 '+title,font=font,fill='white');can.paste(bg,(col*300+20,row*315+43))
pp=P/'FM0489-geometry-dual-matte.png';can.save(pp)
data={**{k:v[k] for k in ['group_id','source','source_ptm','source_ptm_sha256','source_rgba_sha256']},'id':'FM0489-source-checker-geometry','output':str(op),'output_sha256':sha(op),'vector':str(vp),'vector_sha256':sha(vp),'mask':str(mp),'mask_sha256':sha(mp),'source_audit_sha256':sha(R/'qa/field_geometry008_source_audit.json'),'cells':cells,'method':'Direct4x4 source rectangle reconstruction; gold RGB exact, red gradients bilinear within each source cell, alpha64/255 exact source nearest8x. This is authored deterministic geometry, not neural upscale.','source_interpretation_correction':'The apparent gray cells are actually dark red RGB with alpha64; prior yellow/gray visual label depended on the background. Preserve actual source RGBA.','new_neural_unique_originals':0,'new_geometry_only_unique_originals':1,'new_local_passes':0,'new_external_calls':0,'pages':[{'path':str(pp),'sha256':sha(pp),'review_status':'pending','mattes':['#202830','#dedede']}],'runtime_verified':False,'release_eligible':False};Q.write_text(json.dumps(data,ensure_ascii=False,indent=2),'utf8');print('Source checker geometry and dual-matte comparison saved.')
