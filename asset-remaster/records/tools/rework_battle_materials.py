"""Rework tex001/017: measured denoise interpolation and source mean-color preservation."""
import sys,json,gc,time
from pathlib import Path
import numpy as np,torch,spandrel
from PIL import Image,ImageDraw,ImageFont
import local_sr as sr

sys.stdout.reconfigure(encoding='utf8');torch.set_num_threads(4)
R=Path(__file__).resolve().parents[1];O=R/'workspace/local-sr/battle-material-rework-v2';O.mkdir(parents=True,exist_ok=True)
catalog=json.loads((R/'workspace/local-sr/models/models.json').read_text('utf8'))['records']
models={m['name']:m for m in catalog}
def state(name):
    r=models[name];p=Path(r['path']);assert sr.sha(p.read_bytes())==r['sha256']
    d=torch.load(p,map_location='cpu',weights_only=True);return d.get('params_ema',d.get('params',d))
g=state('realesr-general-x4v3.pth');w=state('realesr-general-wdn-x4v3.pth');assert g.keys()==w.keys()
inv=json.loads((R/'qa/battle_map_inventory.json').read_text('utf8'))
items=[t for t in inv['textures'] if t['container']=='map_b_stg01_01.vol/001_map_b_stg01_01.bin' and t['index'] in [1,17]]
records=[];pictures={t['index']:[] for t in items}
for dn in [.25,.5,.75]:
    model=spandrel.ModelLoader().load_from_state_dict({k:dn*g[k]+(1-dn)*w[k] for k in g}).cuda().eval()
    for t in items:
        src=Image.open(t['png']).convert('RGBA');assert sr.sha(src.tobytes())==t['rgba_sha256']
        assert src.getchannel('A').getextrema()==(255,255)
        start=time.monotonic();native=sr.infer_rgb(model,src)
        raw_path=O/f"{t['index']:03d}-dn{dn}-neural4x.png";native.save(raw_path)
        a=np.asarray(native,dtype=np.float32);target=np.asarray(src.convert('RGB'),dtype=np.float32).mean(axis=(0,1))
        drift=target-a.mean(axis=(0,1));corrected=a+drift
        clipped=float(((corrected<0)|(corrected>255)).mean())
        native_fixed=Image.fromarray(np.rint(np.clip(corrected,0,255)).astype(np.uint8))
        out=native_fixed.resize((src.width*8,src.height*8),Image.Resampling.LANCZOS);out.putalpha(255)
        p=O/f"{t['index']:03d}-dn{dn}-mean-color-8x.png";out.save(p)
        rec={'asset_id':t['id'],'source':t['png'],'source_rgba_sha256':t['rgba_sha256'],'denoise_strength':dn,
             'model_sources':[models[n] for n in ['realesr-general-x4v3.pth','realesr-general-wdn-x4v3.pth']],
             'model_weights':[dn,1-dn],'precision':'float32','native_neural_scale':4,'post_scale':'Lanczos 2x',
             'mean_color_offset_rgb':drift.tolist(),'color_offset_clipped_fraction':clipped,
             'native_unadjusted':str(raw_path),'native_unadjusted_sha256':sr.sha(raw_path.read_bytes()),
             'output':str(p),'output_sha256':sr.sha(p.read_bytes()),'output_size':list(out.size),
             'metrics':sr.roundtrip_metrics(src,out),'elapsed_seconds':time.monotonic()-start,
             'visual_review':'pending','tiling_verified':False,'runtime_verified':False,'release_eligible':False}
        records.append(rec);pictures[t['index']].append((f'DNI {dn} · 원본 평균색 보정',out.convert('RGB')))
        print(json.dumps({k:rec[k] for k in ['asset_id','denoise_strength','mean_color_offset_rgb','color_offset_clipped_fraction','metrics']}),flush=True)
    del model;gc.collect();torch.cuda.empty_cache()
font=ImageFont.truetype(r'C:\Windows\Fonts\malgun.ttf',22)
for t in items:
    src=Image.open(t['png']).convert('RGB');old=Image.open(R/f"workspace/local-sr/battle-material-trial-v1/{t['index']:03d}-general-wdn-8x.png").convert('RGB')
    cols=[('원본 단순 확대',src.resize((src.width*8,src.height*8),Image.Resampling.NEAREST)),('이전 WDN · 재작업 대상',old),*pictures[t['index']]]
    sheet=Image.new('RGB',(1800,1290),'#293440');d=ImageDraw.Draw(sheet)
    for n,(label,im) in enumerate(cols):
        x=n%3*600+10;y=n//3*630;d.text((x,y+8),label,font=font,fill='white')
        sheet.paste(im.resize((580,580),Image.Resampling.LANCZOS),(x,y+44))
    d.text((1220,840),'동일한 원본 · 로컬 모델 재처리\n원본 평균 RGB 유지\n반복 경계·게임 표시 검증 전',font=font,fill='white')
    sheet.save(R/f"outputs/local_sr_material_rework_{t['index']:03d}.png")
report={'schema':'brs-material-rework/v2','device':torch.cuda.get_device_name(0),'files':records,
        'reason':'Prior WDN had over-inferred fine relief/fibers and cooler color. Compare intermediate denoise plus explicit source mean RGB correction.',
        'local_inference':True,'image_upload':False,'runtime_verified':False,'release_eligible':False}
(R/'qa/local_sr_battle_material_rework_v2.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
print('REWORK COMPLETE',len(records),flush=True)
