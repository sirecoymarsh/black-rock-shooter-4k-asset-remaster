"""Reviewed second-region opaque surfaces, two actual local neural conditions."""
import sys,json,time,gc
from pathlib import Path
import numpy as np,torch,spandrel
from PIL import Image,ImageDraw,ImageFont
import local_sr as sr
sys.stdout.reconfigure(encoding='utf8');torch.set_num_threads(4)
R=Path(__file__).resolve().parents[1];O=R/'workspace/local-sr/stage02-materials-v1';O.mkdir(parents=True,exist_ok=True);Q=R/'qa/local_sr_stage02_materials_v1.json'
if (R/'qa/local_sr_stage02_review_v3.json').exists():
    raise SystemExit('This batch is finalized. Preserve reviewed classifications and candidates; use a new version for further work.')
cat=json.loads((R/'qa/battle_sr_catalog.json').read_text('utf8'))
special={80:'illustrated poster with banner/footer lettering',85:'RED CHERRY outlined lettering',89:'crosswalk paint, flat geometry protection',91:'BUS painted lettering',95:'advertisement lettering',96:'coffee advertisement with lettering',106:'traffic signal/street signs atlas',109:'cursive shop sign',112:'police vehicle lettering atlas',113:'taxi vehicle lettering atlas',120:'VIRGINIA BEER outlined sign',121:'faded outlined lettering',126:'straight road arrow',127:'turn road arrow'}
stage=[g for g in cat['groups'] if any('stg02_' in k for k in g['members']) and not g.get('local_sr_attempted')]
chosen=[];deferred={}
for g in stage:
    n=int(g['group_id'][2:]);desc=special.get(n)
    if desc:deferred[g['group_id']]=desc
    elif g['representative']['alpha_min']!=255:deferred[g['group_id']]='Source alpha requires coverage/contour review; not excluded from project.'
    else:chosen.append(g)
    g['classification']='protected semantic/geometry or alpha surface' if g['group_id'] in deferred else 'opaque surface, no lettering identified in enlarged source'
    g['classification_review']='Codex internal; qa/battle-source-catalog/stage02-01..06.png'
    if g['group_id'] in deferred:g['classification_reason']=deferred[g['group_id']]
(R/'qa/battle_sr_catalog.json').write_text(json.dumps(cat,ensure_ascii=False,indent=2),'utf8')
mr={r['name']:r for r in json.loads((R/'workspace/local-sr/models/models.json').read_text('utf8'))['records']}
def weights(name):
    r=mr[name];p=Path(r['path']);assert sr.sha(p.read_bytes())==r['sha256'];d=torch.load(p,map_location='cpu',weights_only=True);return d.get('params_ema',d.get('params',d))
wg=weights('realesr-general-x4v3.pth');ww=weights('realesr-general-wdn-x4v3.pth');assert wg.keys()==ww.keys() and torch.cuda.is_available()
report=json.loads(Q.read_text('utf8')) if Q.exists() else {'schema':'brs-stage02-materials/v1','iso_sha256':cat['iso_sha256'],'device':torch.cuda.get_device_name(0),'torch':torch.__version__,'spandrel':spandrel.__version__,'local_inference':True,'image_upload':False,'files':[],'chosen_groups':[g['group_id'] for g in chosen],'deferred_groups':deferred,'runtime_verified':False,'release_eligible':False}
assert report['chosen_groups']==[g['group_id'] for g in chosen]
done={(r['group_id'],r['denoise_strength']):r for r in report['files']}
for dn in [0.,.5]:
    model=spandrel.ModelLoader().load_from_state_dict({k:dn*wg[k]+(1-dn)*ww[k] for k in wg}).cuda().eval();assert model.scale==4
    for g in chosen:
        gid=g['group_id'];src=Image.open(g['representative']['png']).convert('RGBA');assert src.getchannel('A').getextrema()==(255,255) and sr.sha(src.tobytes())==g['rgba_sha256']
        if (gid,dn) in done:
            r=done[(gid,dn)];assert r['source_rgba_sha256']==g['rgba_sha256'] and sr.sha(Path(r['output']).read_bytes())==r['output_sha256'];continue
        start=time.monotonic();native=sr.infer_rgb(model,src);npth=O/f'{gid}-dn{dn}-neural4x.png';native.save(npth)
        a=np.asarray(native,dtype=np.float32);offset=np.asarray(src.convert('RGB'),dtype=np.float32).mean((0,1))-a.mean((0,1));a=np.clip(a+offset,0,255);out=Image.fromarray(np.rint(a).astype('uint8')).resize((src.width*8,src.height*8),Image.Resampling.LANCZOS);out.putalpha(255);p=O/f'{gid}-dn{dn}-8x.png';out.save(p)
        r={'group_id':gid,'source':g['representative']['png'],'source_id':g['representative']['id'],'source_rgba_sha256':g['rgba_sha256'],'denoise_strength':dn,'model_sources':[mr[n] for n in ['realesr-general-x4v3.pth','realesr-general-wdn-x4v3.pth']],'model_weights':[dn,1-dn],'precision':'float32','native_neural_scale':4,'post_scale':'Lanczos 2x','native':str(npth),'native_sha256':sr.sha(npth.read_bytes()),'output':str(p),'output_sha256':sr.sha(p.read_bytes()),'output_size':list(out.size),'mean_color_offset_rgb':offset.tolist(),'source_scale_metrics':sr.roundtrip_metrics(src,out),'alpha':'Opaque255 exact','edge_context':'Full source image, no tile-wrap/atlas-split assumptions','seconds':time.monotonic()-start,'visual_review':'pending','runtime_verified':False,'release_eligible':False}
        report['files'].append(r);done[(gid,dn)]=r;Q.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8');print('INFERRED',gid,dn,flush=True)
    del model;gc.collect();torch.cuda.empty_cache()
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',19);sdir=R/'outputs/stage02-material-review';sdir.mkdir(exist_ok=True);pages=[]
for start in range(0,len(chosen),4):
    batch=chosen[start:start+4];sheet=Image.new('RGB',(1536,len(batch)*370+45),'#293440');d=ImageDraw.Draw(sheet)
    for col,text in enumerate(['원본 단순 확대','로컬 WDN','로컬 중간 노이즈 제거']):d.text((col*512+10,6),text,font=font,fill='white')
    for i,g in enumerate(batch):
        src=Image.open(g['representative']['png']).convert('RGB');size=(round(src.width*min(488/src.width,310/src.height,8)),round(src.height*min(488/src.width,310/src.height,8)))
        ims=[src]+[Image.open(done[(g['group_id'],dn)]['output']).convert('RGB') for dn in [0.,.5]]
        for j,im in enumerate(ims):
            x=j*512+10;y=45+i*370;d.text((x,y),f"{g['group_id']} {src.width}×{src.height}",font=font,fill='white');sheet.paste(im.resize(size,Image.Resampling.NEAREST if j==0 else Image.Resampling.LANCZOS),(x,y+34))
    p=sdir/f'review-{start//4+1:02d}.png';sheet.save(p);pages.append(str(p))
report['comparison_sheets']=pages;Q.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8');print(json.dumps({'groups':len(chosen),'outputs':len(report['files']),'pages':len(pages),'deferred':deferred}),flush=True)
