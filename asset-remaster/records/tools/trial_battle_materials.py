"""Local SR comparisons on opaque stage-one materials; tex018 markings unresolved."""
import sys,json,time,gc
from pathlib import Path
import numpy as np,torch,spandrel
from PIL import Image,ImageDraw,ImageFont
import local_sr as sr

sys.stdout.reconfigure(encoding='utf8');torch.set_num_threads(4)
R=Path(__file__).resolve().parents[1]
inv=json.loads((R/'qa/battle_map_inventory.json').read_text('utf8'))
chosen={1:'흙·자갈',2:'도로·보도',8:'아치형 창',9:'건물 외벽',17:'잔해',18:'무너진 건물'}
items=[t for t in inv['textures'] if t['container']=='map_b_stg01_01.vol/001_map_b_stg01_01.bin' and t['index'] in chosen]
assert len(items)==len(chosen) and all(t.get('opaque_fraction')==1 for t in items)
models=json.loads((R/'workspace/local-sr/models/models.json').read_text('utf8'))['records']
general=next(m for m in models if m['name']=='realesr-general-wdn-x4v3.pth')
O=R/'workspace/local-sr/battle-material-trial-v1';O.mkdir(parents=True,exist_ok=True)
records=[]
for model_id,path,digest in [('general-wdn',Path(general['path']),general['sha256']),('anime6B',sr.MODEL,sr.MODEL_SHA)]:
    model=sr.load_model(path,digest)
    for t in items:
        src=Image.open(t['png']).convert('RGBA');assert sr.sha(src.tobytes())==t['rgba_sha256']
        start=time.monotonic();native=sr.infer_rgb(model,src)
        p=O/f"{t['index']:03d}-{model_id}-native4x.png";native.save(p)
        out=native.resize((src.width*8,src.height*8),Image.Resampling.LANCZOS);out.putalpha(255)
        q=O/f"{t['index']:03d}-{model_id}-8x.png";out.save(q)
        records.append({'asset_id':t['id'],'source':t['png'],'source_rgba_sha256':t['rgba_sha256'],
                        'model':model_id,'model_sha256':digest,'native_scale':4,'post_scale':'Lanczos 2x',
                        'output':str(q),'output_sha256':sr.sha(q.read_bytes()),'output_size':list(out.size),
                        'metrics':sr.roundtrip_metrics(src,out),'seconds':time.monotonic()-start,
                        'alpha':'Opaque255 preserved','edge_context':'Full image inference, no periodic assumption',
                        'uv_tiling_verified':False,'runtime_verified':False,'visual_review':'pending','release_eligible':False})
        print('LOCAL_SR',t['index'],model_id,flush=True)
    del model;gc.collect();torch.cuda.empty_cache()
font=ImageFont.truetype(r'C:\Windows\Fonts\malgun.ttf',20)
for t in items:
    src=Image.open(t['png']).convert('RGB')
    ims=[src.resize((src.width*8,src.height*8),Image.Resampling.NEAREST)]+[Image.open(O/f"{t['index']:03d}-{m}-8x.png").convert('RGB') for m in ['general-wdn','anime6B']]
    labels=['원본 단순 확대','일반 모델 · 약한 노이즈 제거','애니메이션 모델']
    w=min(900,src.width*8);h=round(w*src.height/src.width)
    sheet=Image.new('RGB',(3*(w+16),h+74),'#293440');d=ImageDraw.Draw(sheet)
    for col,(im,label) in enumerate(zip(ims,labels)):
        x=col*(w+16)+8;d.text((x,6),label,font=font,fill='white')
        sheet.paste(im.resize((w,h),Image.Resampling.LANCZOS),(x,38))
    d.text((8,h+42),chosen[t['index']]+' · 원본 위치 유지 / 반복 타일·게임 표시 검증 전',font=font,fill='white')
    sheet.save(R/f"outputs/local_sr_material_{t['index']:03d}.png")
(R/'qa/local_sr_battle_material_trial.json').write_text(json.dumps({'schema':'brs-local-material-trial/v1',
    'iso_sha256':inv['iso_sha256'],'device':torch.cuda.get_device_name(0),'files':records,
    'scope':'Six opaque material comparisons: five without identified lettering; tex018 dark markings are text/damage ambiguous and unapproved. STOP lettering and alpha assets remain pending in full scope.',
    'runtime_verified':False,'release_eligible':False},ensure_ascii=False,indent=2),'utf8')
print('Complete',len(records),flush=True)
