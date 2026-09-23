"""Source-reviewed stage 3/4 opaque materials, actual CUDA SR in two conditions."""
import sys,json,time,gc
from pathlib import Path
import numpy as np,torch,spandrel
from PIL import Image,ImageDraw,ImageFont
import local_sr as sr
sys.stdout.reconfigure(encoding='utf8');torch.set_num_threads(4)
R=Path(__file__).resolve().parents[1]
O=R/'workspace/local-sr/stage0304-materials-v1';Q=R/'qa/local_sr008_inference.json'
if (R/'qa/local_sr008_review.json').exists():raise SystemExit('Finalized; create a new batch instead of overwriting reviewed evidence.')
O.mkdir(parents=True,exist_ok=True)
cat=json.loads((R/'qa/battle_sr_catalog.json').read_text('utf8'));groups={g['group_id']:g for g in cat['groups']}
ids=[129,133,144,169,170,173,174,175,176,177,178,179,180,181,182,184,185,186,187,188,190,191,192,194]
chosen=[groups[f'BM{i:03d}'] for i in ids]
source_review=json.loads((R/'qa/local_sr_stage0304_source_review.json').read_text('utf8'))
classified=[]
for gid in source_review['group_ids']:
 g=groups[gid]
 if int(gid[2:]) in ids:category='opaque material for local SR comparison';reason='Metal/stone/snow/water surface reviewed in source sheets; no legible wording identified. Panel details require comparison after inference.'
 elif gid=='BM189':category='lettered/emblem surface; reconstruction pending';reason='Large dark sign-like glyphs must be identified and protected; generic SR could alter their strokes.'
 elif gid=='BM199':category='soft dark effect; alpha/blend consumer pending';reason='Soft low-contrast gradient must not gain material grain; investigate consumer and compare a restrained treatment.'
 elif gid=='BM193':category='tiny flat strip/palette-like asset; consumer pending';reason='8x8 flat bands should not acquire invented texture; determine actual use before treatment.'
 else:category='alpha/atlas for separate treatment';reason='Cutout silhouette, thin rods, split panels or soft opacity require alpha-aware inference and explicit region checks.'
 classified.append({'group_id':gid,'classification':category,'reason':reason,'source_rgba_sha256':g['rgba_sha256']})
source_review.update({'visual_review':'Codex internal: all six source pages inspected','classifications':classified,'opaque_batch':f'qa/{Q.name}','excluded_from_project':[]})
(R/'qa/local_sr_stage0304_source_review.json').write_text(json.dumps(source_review,ensure_ascii=False,indent=2),'utf8')
mr={r['name']:r for r in json.loads((R/'workspace/local-sr/models/models.json').read_text('utf8'))['records']}
def weights(name):
 r=mr[name];assert sr.sha(Path(r['path']).read_bytes())==r['sha256'];w=torch.load(r['path'],map_location='cpu',weights_only=True);return w.get('params_ema',w.get('params',w))
wg=weights('realesr-general-x4v3.pth');ww=weights('realesr-general-wdn-x4v3.pth');assert wg.keys()==ww.keys() and torch.cuda.is_available()
report=json.loads(Q.read_text('utf8')) if Q.exists() else {'schema':'brs-sr008-inference/v1','group_ids':[g['group_id'] for g in chosen],'source_review':'qa/local_sr_stage0304_source_review.json','iso_sha256':cat['iso_sha256'],'device':torch.cuda.get_device_name(0),'torch':torch.__version__,'spandrel':spandrel.__version__,'local_inference':True,'image_upload':False,'files':[],'runtime_verified':False,'release_eligible':False}
assert report['group_ids']==[g['group_id'] for g in chosen]
done={(r['group_id'],r['denoise_strength']):r for r in report['files']}
for dn in [0.,.5]:
 model=spandrel.ModelLoader().load_from_state_dict({k:dn*wg[k]+(1-dn)*ww[k] for k in wg}).cuda().eval();assert model.scale==4
 for g in chosen:
  gid=g['group_id'];src=Image.open(g['representative']['png']).convert('RGBA');assert src.getchannel('A').getextrema()==(255,255) and sr.sha(src.tobytes())==g['rgba_sha256']
  if (gid,dn) in done:
   row=done[(gid,dn)];assert row['source_rgba_sha256']==g['rgba_sha256'] and sr.sha(Path(row['output']).read_bytes())==row['output_sha256'];continue
  assert not g.get('local_sr_attempted'),gid
  start=time.monotonic();native=sr.infer_rgb(model,src);npth=O/f'{gid}-dn{dn}-neural4x.png';native.save(npth)
  a=np.asarray(native,dtype=np.float32);offset=np.asarray(src.convert('RGB'),dtype=np.float32).mean((0,1))-a.mean((0,1));out=Image.fromarray(np.rint(np.clip(a+offset,0,255)).astype('uint8')).resize((src.width*8,src.height*8),Image.Resampling.LANCZOS);out.putalpha(255);p=O/f'{gid}-dn{dn}-8x.png';out.save(p)
  row={'group_id':gid,'source':g['representative']['png'],'source_rgba_sha256':g['rgba_sha256'],'denoise_strength':dn,'model_sources':[mr[n] for n in ['realesr-general-x4v3.pth','realesr-general-wdn-x4v3.pth']],'model_weights':[dn,1-dn],'precision':'float32','native_neural_scale':4,'post_scale':'Lanczos2x','native':str(npth),'native_sha256':sr.sha(npth.read_bytes()),'output':str(p),'output_sha256':sr.sha(p.read_bytes()),'output_size':list(out.size),'mean_color_offset_rgb':offset.tolist(),'source_scale_metrics':sr.roundtrip_metrics(src,out),'alpha':'Opaque255 exact','edge_context':'Full source image; tile-wrap/atlas consumers unverified','seconds':time.monotonic()-start,'visual_review':'pending','runtime_verified':False,'release_eligible':False}
  report['files'].append(row);done[(gid,dn)]=row;Q.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8');print('INFERRED',gid,dn,flush=True)
 del model;gc.collect();torch.cuda.empty_cache()
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',19);sdir=R/'outputs/sr008-review';sdir.mkdir(exist_ok=True);pages=[]
for start in range(0,len(chosen),4):
 batch=chosen[start:start+4];sheet=Image.new('RGB',(1536,len(batch)*370+45),'#293440');d=ImageDraw.Draw(sheet)
 for col,t in enumerate(['원본 단순 확대','로컬 WDN','로컬 중간 노이즈 제거']):d.text((col*512+10,6),t,font=font,fill='white')
 for i,g in enumerate(batch):
  src=Image.open(g['representative']['png']).convert('RGB');s=min(488/src.width,310/src.height,8);wh=(round(src.width*s),round(src.height*s))
  ims=[src]+[Image.open(done[(g['group_id'],dn)]['output']).convert('RGB') for dn in [0.,.5]]
  for j,im in enumerate(ims):
   x=j*512+10;y=45+i*370;d.text((x,y),f"{g['group_id']} {src.width}×{src.height}",font=font,fill='white');sheet.paste(im.resize(wh,Image.Resampling.NEAREST if j==0 else Image.Resampling.LANCZOS),(x,y+34))
 p=sdir/f'review-{start//4+1:02d}.png';sheet.save(p);pages.append(str(p))
report['comparison_sheets']=pages;report['actual_new_neural_passes']=len(report['files']);Q.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
print(json.dumps({'originals':len(chosen),'outputs':len(report['files']),'pages':len(pages)}),flush=True)
