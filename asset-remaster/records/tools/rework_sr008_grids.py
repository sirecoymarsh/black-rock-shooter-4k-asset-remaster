import sys,json,time,gc
from pathlib import Path
import numpy as np,torch
from PIL import Image,ImageDraw,ImageFont,ImageFilter
import local_sr as sr
sys.stdout.reconfigure(encoding='utf8')
R=Path(__file__).resolve().parents[1];O=R/'workspace/local-sr/sr008-grid-rework';O.mkdir(parents=True,exist_ok=True)
if (R/'qa/local_sr008_review.json').exists():raise SystemExit('Finalized; use a new version.')
cat=json.loads((R/'qa/battle_sr_catalog.json').read_text('utf8'));groups={g['group_id']:g for g in cat['groups']}
models={m['name']:m for m in json.loads((R/'workspace/local-sr/models/models.json').read_text('utf8'))['records']}
report={'schema':'brs-sr008-grid-rework/v1','files':[],'local_inference':True,'image_upload':False,'runtime_verified':False,'release_eligible':False}
for name,sigma,tag in [('realesr-general-wdn-x4v3.pth',.5,'wdn-filter05'),('RealESRGAN_x4plus.pth',0.,'photo'),('RealESRGAN_x4plus.pth',.5,'photo-filter05')]:
 m=models[name];model=sr.load_model(Path(m['path']),m['sha256'])
 for gid in ['BM175','BM187']:
  g=groups[gid];src=Image.open(g['representative']['png']).convert('RGBA');assert sr.sha(src.tobytes())==g['rgba_sha256']
  inp=src.convert('RGB').filter(ImageFilter.GaussianBlur(sigma)) if sigma else src.convert('RGB');ip=O/f'{gid}-{tag}-input.png';inp.save(ip)
  t=time.monotonic();native=sr.infer_rgb(model,inp);npth=O/f'{gid}-{tag}-native4x.png';native.save(npth)
  a=np.asarray(native,dtype=np.float32);offset=np.asarray(src.convert('RGB'),dtype=np.float32).mean((0,1))-a.mean((0,1));out=Image.fromarray(np.rint(np.clip(a+offset,0,255)).astype('uint8')).resize((src.width*8,src.height*8),Image.Resampling.LANCZOS);out.putalpha(255);p=O/f'{gid}-{tag}-8x.png';out.save(p)
  report['files'].append({'id':gid+'-'+tag,'group_id':gid,'model':m,'source':g['representative']['png'],'source_rgba_sha256':g['rgba_sha256'],'prefilter_sigma':sigma,'input':str(ip),'input_sha256':sr.sha(ip.read_bytes()),'native':str(npth),'native_sha256':sr.sha(npth.read_bytes()),'output':str(p),'output_sha256':sr.sha(p.read_bytes()),'output_size':list(out.size),'native_neural_scale':4,'post_scale':'Lanczos2x','mean_rgb_offset':offset.tolist(),'seconds':time.monotonic()-t,'visual_review':'pending','runtime_verified':False,'release_eligible':False});print('INFERRED',gid,tag,flush=True)
 del model;gc.collect();torch.cuda.empty_cache()
q=json.loads((R/'qa/local_sr008_inference.json').read_text('utf8'));font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18);pages=[]
for gid in ['BM175','BM187']:
 src=Image.open(groups[gid]['representative']['png']).convert('RGBA');old=next(r for r in q['files'] if r['group_id']==gid and r['denoise_strength']==0)
 ims=[(src,'원본'),(Image.open(old['output']).convert('RGBA'),'이전 WDN')]+[(Image.open(r['output']).convert('RGBA'),r['id']) for r in report['files'] if r['group_id']==gid]
 s=Image.new('RGB',(1560,1100),'#293440');d=ImageDraw.Draw(s)
 for i,(im,label) in enumerate(ims):
  x=(i%3)*520+10;y=(i//3)*550+10;d.text((x,y),label,font=font,fill='white');scale=min(500/src.width,490/src.height,8);wh=(round(src.width*scale),round(src.height*scale));s.paste(im.convert('RGB').resize(wh,Image.Resampling.NEAREST if i==0 else Image.Resampling.LANCZOS),(x,y+30))
 p=R/f'outputs/sr008_grid_{gid}.png';s.save(p);pages.append(str(p))
report['comparison_sheets']=pages;report['actual_new_neural_passes']=6;(R/'qa/local_sr008_grid_rework.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
print('DONE',flush=True)
