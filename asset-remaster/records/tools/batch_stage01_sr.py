"""First-region material SR, with explicit source classification and resumable proof."""
import sys, json, time, gc
from pathlib import Path
import numpy as np, torch, spandrel
from PIL import Image, ImageDraw, ImageFont
import local_sr as sr

sys.stdout.reconfigure(encoding='utf8');torch.set_num_threads(4)
R=Path(__file__).resolve().parents[1]
O=R/'workspace/local-sr/stage01-materials-v1';O.mkdir(parents=True,exist_ok=True)
Q=R/'qa/local_sr_stage01_materials_v1.json'
catalog=json.loads((R/'qa/battle_sr_catalog.json').read_text('utf8'))
byid={g['group_id']:g for g in catalog['groups']}
alpha={1:'cutout building',7:'crack decal',26:'railings',27:'cloud layer',39:'diagonal marking',45:'broken panels',55:'crack decal',57:'tree plus trunk atlas',58:'crack decals'}
special={6:'STOP road lettering',19:'ambiguous dark damage/marking',22:'illustrated poster and lettering',24:'mechanical atlas with possible tiny signs',30:'STOP road lettering atlas',41:'weathered graphic/signage'}
atlases={20,21,29,49}
rough={2,18,23,54}
existing={2,3,9,10,18} # Prior inspected opaque candidates; no redundant inference.
for n in range(1,59):
    g=byid[f'BM{n:03d}']
    if n in alpha:
        g.update(classification='alpha-aware rework required',reason=alpha[n])
    elif n in special:
        g.update(classification='protected text/ambiguous region; separate rework',reason=special[n])
    else:
        g.update(classification='opaque material' if n not in atlases else 'opaque window-strip atlas',
                 reason='No lettering identified in source sheet; original geometry retained, consumer proof pending.')
    g['classification_review']='Codex internal; qa/battle-source-catalog/stage01-01..04.png'
(R/'qa/battle_sr_catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2),'utf8')
chosen=[byid[f'BM{n:03d}'] for n in range(1,59) if n not in alpha and n not in special and n not in existing]
models=json.loads((R/'workspace/local-sr/models/models.json').read_text('utf8'))['records']
mr={r['name']:r for r in models}
def weights(name):
    p=Path(mr[name]['path']);assert sr.sha(p.read_bytes())==mr[name]['sha256']
    d=torch.load(p,map_location='cpu',weights_only=True)
    return d.get('params_ema',d.get('params',d))
wg=weights('realesr-general-x4v3.pth');ww=weights('realesr-general-wdn-x4v3.pth')
assert wg.keys()==ww.keys() and torch.cuda.is_available()
report=json.loads(Q.read_text('utf8')) if Q.exists() else {
    'schema':'brs-stage01-materials/v1','iso_sha256':catalog['iso_sha256'],
    'device':torch.cuda.get_device_name(0),'torch':torch.__version__,'spandrel':spandrel.__version__,
    'local_inference':True,'image_upload':False,'files':[],
    'group_count':len(chosen),'existing_reviewed_groups':[f'BM{n:03d}' for n in sorted(existing)],
    'deferred_groups':{f'BM{n:03d}':v for n,v in (alpha|special).items()},
    'full_scope_note':'Deferred assets remain in scope. This is neither the full game nor a release.',
    'runtime_verified':False,'release_eligible':False}
done={(r['group_id'],r['denoise_strength']):r for r in report['files']}
for dn in [0.,.5]:
    model=spandrel.ModelLoader().load_from_state_dict({k:dn*wg[k]+(1-dn)*ww[k] for k in wg}).cuda().eval()
    assert model.scale==4
    for group in chosen:
        gid=group['group_id'];t=group['representative'];src=Image.open(t['png']).convert('RGBA')
        assert src.getchannel('A').getextrema()==(255,255)
        assert sr.sha(src.tobytes())==group['rgba_sha256']
        old=done.get((gid,dn))
        if old:
            assert old['source_rgba_sha256']==group['rgba_sha256']
            assert sr.sha(Path(old['output']).read_bytes())==old['output_sha256']
            continue
        start=time.monotonic();native=sr.infer_rgb(model,src)
        p=O/f'{gid}-dn{dn}-neural4x.png';native.save(p)
        a=np.asarray(native,dtype=np.float32);target=np.asarray(src.convert('RGB'),dtype=np.float32).mean(axis=(0,1))
        offset=target-a.mean(axis=(0,1));fixed=a+offset
        clipped=float(((fixed<0)|(fixed>255)).mean())
        fixed_im=Image.fromarray(np.rint(np.clip(fixed,0,255)).astype(np.uint8))
        out=fixed_im.resize((src.width*8,src.height*8),Image.Resampling.LANCZOS);out.putalpha(255)
        q=O/f'{gid}-dn{dn}-color-8x.png';out.save(q)
        row={'group_id':gid,'source_id':t['id'],'source':t['png'],'source_rgba_sha256':group['rgba_sha256'],
             'pixel_equivalent_members':group['members'],'classification':group['classification'],
             'denoise_strength':dn,'model_sources':[mr[n] for n in ['realesr-general-x4v3.pth','realesr-general-wdn-x4v3.pth']],
             'model_weights':[dn,1-dn],'precision':'float32','native_neural_scale':4,'post_scale':'Lanczos 2x',
             'native':str(p),'native_sha256':sr.sha(p.read_bytes()),'output':str(q),'output_sha256':sr.sha(q.read_bytes()),
             'source_size':list(src.size),'output_size':list(out.size),'alpha':'Opaque255 preserved exactly',
             'mean_color_offset_rgb':offset.tolist(),'color_clipped_fraction':clipped,'metrics':sr.roundtrip_metrics(src,out),
             'edge_context':'Full image. No periodic extension, seam or UV assumptions.',
             'seconds':time.monotonic()-start,'visual_review':'pending','runtime_verified':False,'release_eligible':False}
        report['files'].append(row);done[(gid,dn)]=row
        Q.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
        print(f'INFERRED {gid} dn={dn}',flush=True)
    del model;gc.collect();torch.cuda.empty_cache()

font=ImageFont.truetype(r'C:\Windows\Fonts\malgun.ttf',20)
sheetdir=R/'outputs/stage01-material-review';sheetdir.mkdir(exist_ok=True)
sheets=[]
for start in range(0,len(chosen),4):
    batch=chosen[start:start+4];sheet=Image.new('RGB',(1536,len(batch)*370+45),'#293440');d=ImageDraw.Draw(sheet)
    for col,label in enumerate(['원본 단순 확대','로컬 모델 · 약한 노이즈 제거','로컬 모델 · 중간 노이즈 제거']):
        d.text((col*512+12,6),label,font=font,fill='white')
    for n,group in enumerate(batch):
        gid=group['group_id'];src=Image.open(group['representative']['png']).convert('RGB')
        ims=[src,Image.open(done[(gid,0.)]['output']).convert('RGB'),Image.open(done[(gid,.5)]['output']).convert('RGB')]
        scale=min(488/src.width,308/src.height,8);size=(round(src.width*scale),round(src.height*scale))
        for col,im in enumerate(ims):
            x=col*512+12;y=45+n*370
            d.text((x,y+2),f'{gid} · {src.width}×{src.height} → {src.width*8}×{src.height*8}',font=font,fill='white')
            sheet.paste(im.resize(size,Image.Resampling.NEAREST if col==0 else Image.Resampling.LANCZOS),(x,y+36))
    p=sheetdir/f'review-{start//4+1:02d}.png';sheet.save(p);sheets.append(str(p))
report['comparison_sheets']=sheets
Q.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
print(json.dumps({'inferred_original_groups':len(chosen),'outputs':len(report['files']),'sheets':len(sheets)}),flush=True)
