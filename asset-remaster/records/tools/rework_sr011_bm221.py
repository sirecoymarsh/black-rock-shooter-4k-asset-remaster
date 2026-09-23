"""Source-guided neural retries for observed material/geometry failures."""
import json,time,sys
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter,distance_transform_edt
from PIL import Image,ImageDraw,ImageFont
import local_sr as sr
sys.stdout.reconfigure(encoding='utf8')
R=Path(__file__).resolve().parents[1];O=R/'workspace/local-sr/sr011-bm221-rework';O.mkdir(parents=True,exist_ok=True)
if (R/'qa/local_sr011_review.json').exists():raise SystemExit('Finalized; use a new version.')
old=json.loads((R/'qa/local_sr011_inference.json').read_text('utf8'));parents={r['group_id']:r for r in old['files'] if r['model_id']=='wdn'}
model_info=parents['BM221']['model'];model=sr.load_model(Path(model_info['path']),model_info['sha256'])
ids=['BM221'];report={'schema':'brs-sr011-rework/v1','group_ids':ids,'files':[],'local_inference':True,'image_upload':False,'runtime_verified':False,'release_eligible':False}
def guide(src,sigma):
 a=np.asarray(src,dtype=np.float32);w=a[:,:,3:4]/255.;cov=gaussian_filter(w,(sigma,sigma,0),mode='nearest');rgb=gaussian_filter(a[:,:,:3]*w,(sigma,sigma,0),mode='nearest')/np.maximum(cov,1e-6);vis=cov[:,:,0]>1e-6
 if not vis.all():
  near=distance_transform_edt(~vis,return_distances=False,return_indices=True);rgb[~vis]=rgb[near[0][~vis],near[1][~vis]]
 return Image.fromarray(np.rint(np.clip(rgb,0,255)).astype('uint8'))
for gid in ids:
 parent=parents[gid];src=Image.open(parent['source']).convert('RGBA');assert sr.sha(src.tobytes())==parent['source_rgba_sha256'];assert sr.sha(Path(parent['output']).read_bytes())==parent['output_sha256'];prior=Image.open(parent['output']).convert('RGBA')
 sigma=.75 if gid=='BM221' else .75;inp=guide(src,sigma);ip=O/f'{gid}-filtered-input.png';inp.save(ip);t=time.monotonic();native=sr.infer_rgb(model,inp);npth=O/f'{gid}-filtered-native4x.png';native.save(npth);fresh=native.resize(prior.size,Image.Resampling.LANCZOS).convert('RGBA');fresh.putalpha(prior.getchannel('A'))
 variants=[('filtered',fresh,None),('guided',prior,.2 if gid=='BM221' else .45),('filtered-guided',fresh,.2 if gid=='BM221' else .45)]
 for tag,base,weight in variants:
  basep=Path(parent['output']) if tag=='guided' else O/f'{gid}-filtered.png'
  if weight is None:out=fresh
  else:
   v=np.asarray(base,dtype=np.float32);a=v[:,:,3:4]/255.;low=gaussian_filter(v[:,:,:3]*a,(6.,6.,0),mode='nearest')/np.maximum(gaussian_filter(a,(6.,6.,0),mode='nearest'),1e-6)
   target=np.asarray(guide(src,.5 if gid=='BM221' else .25).resize(base.size,Image.Resampling.BILINEAR),dtype=np.float32)
   corrected=target+weight*(v[:,:,:3]-low);colors=np.asarray(src)[:,:,:3][np.asarray(src)[:,:,3]>0];corrected=np.minimum(np.maximum(corrected,colors.min(0)),colors.max(0));out=Image.fromarray(np.rint(np.clip(corrected,0,255)).astype('uint8')).convert('RGBA');out.putalpha(prior.getchannel('A'))
  p=O/f'{gid}-{tag}.png';out.save(p);assert out.getchannel('A').tobytes()==prior.getchannel('A').tobytes()
  record={'id':gid+'-'+tag,'group_id':gid,'source':parent['source'],'source_rgba_sha256':parent['source_rgba_sha256'],'model':model_info,'prefilter_sigma':sigma if tag!='guided' else parent['prefilter_sigma'],'alpha_parent':parent['output'],'alpha_parent_sha256':parent['output_sha256'],'output':str(p),'output_sha256':sr.sha(p.read_bytes()),'output_size':list(out.size),'new_neural_passes':1 if tag=='filtered' else 0,'native_neural_scale':4,'post_scale':'Lanczos2x','method':'actual filtered source neural RGB4x with existing alpha' if tag=='filtered' else 'Source premultiplied color guide plus weighted alpha-normalized neural high-frequency residual; alpha exact to original trial','detail_weight':weight,'visual_review':'pending','runtime_verified':False,'release_eligible':False}
  if tag=='filtered':record.update(input=str(ip),input_sha256=sr.sha(ip.read_bytes()),native=str(npth),native_sha256=sr.sha(npth.read_bytes()),seconds=time.monotonic()-t)
  else:record.update(parent=str(basep),parent_sha256=sr.sha(basep.read_bytes()))
  report['files'].append(record)
 print('REWORKED',gid,flush=True)
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18);pages=[]
for gid in ids:
 src=Image.open(parents[gid]['source']).convert('RGBA');ims=[(src,'원본 단순 확대'),(Image.open(parents[gid]['output']).convert('RGBA'),'이전 WDN')]+[(Image.open(r['output']).convert('RGBA'),r['id']) for r in report['files'] if r['group_id']==gid]
 s=Image.new('RGB',(1560,1090),'#293440');d=ImageDraw.Draw(s)
 for i,(im,label) in enumerate(ims):
  x=i%3*520+10;y=i//3*545+10;d.text((x,y),label,font=font,fill='white');scale=min(500/src.width,485/src.height,8);wh=(round(src.width*scale),round(src.height*scale));im=im.resize(wh,Image.Resampling.NEAREST if i==0 else Image.Resampling.LANCZOS);bg=Image.new('RGB',wh,'#72808b');bg.paste(im,(0,0),im);s.paste(bg,(x,y+34))
 p=R/f'outputs/sr011_bm221_rework_{gid}.png';s.save(p);pages.append(str(p))
report['comparison_sheets']=pages;report['new_neural_passes']=1;(R/'qa/local_sr011_bm221_rework.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
print(json.dumps({'outputs':3,'new_neural_passes':1}),flush=True)


