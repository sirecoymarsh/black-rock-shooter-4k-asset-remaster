"""Neural asphalt reconstruction, source-bound flat paint; no invented bevels."""
import sys,json,time
from pathlib import Path
import numpy as np,torch
from scipy.ndimage import distance_transform_edt
from PIL import Image,ImageDraw,ImageFont
import local_sr as sr
sys.stdout.reconfigure(encoding='utf8')
R=Path(__file__).resolve().parents[1];O=R/'workspace/local-sr/stage01-road-paint-v2';O.mkdir(parents=True,exist_ok=True)
cat=json.loads((R/'qa/battle_sr_catalog.json').read_text('utf8'));groups={g['group_id']:g for g in cat['groups']}
model_rec=next(m for m in json.loads((R/'workspace/local-sr/models/models.json').read_text('utf8'))['records'] if m['name']=='realesr-general-wdn-x4v3.pth')
model=sr.load_model(Path(model_rec['path']),model_rec['sha256'])
prior=json.loads((R/'qa/local_sr_stage01_materials_v1.json').read_text('utf8'))
old={r['group_id']:r['output'] for r in prior['files'] if r['denoise_strength']==0}
old['BM003']=str(R/'workspace/local-sr/battle-material-trial-v1/002-general-wdn-8x.png')
rows=[];font=ImageFont.truetype(r'C:\Windows\Fonts\malgun.ttf',20)
sheet=Image.new('RGB',(1536,4*370+45),'#293440');draw=ImageDraw.Draw(sheet)
for c,title in enumerate(['원본 단순 확대','첫 로컬 처리 · 선이 부푼 상태','재작업 · 평평한 도로 표시 복원']):draw.text((c*512+12,6),title,font=font,fill='white')
for k,gid in enumerate(['BM003','BM004','BM005','BM028']):
    group=groups[gid];src=Image.open(group['representative']['png']).convert('RGBA');a=np.asarray(src)
    assert sr.sha(src.tobytes())==group['rgba_sha256']
    # Source palette/positions inspected: only white and yellow road paint meet this threshold.
    paint=a[:,:,0]>=120
    if gid in ['BM003','BM028']:paint[:,187:]=False
    assert paint.any() and not paint.all()
    near=distance_transform_edt(paint,return_distances=False,return_indices=True)
    rgb=a[:,:,:3].copy();rgb[paint]=rgb[near[0][paint],near[1][paint]]
    assert np.array_equal(rgb[~paint],a[:,:,:3][~paint])
    clean=Image.fromarray(rgb);clean_path=O/f'{gid}-paint-removed.png';clean.save(clean_path)
    mp=O/f'{gid}-paint-mask.png';Image.fromarray(paint.astype(np.uint8)*255).save(mp)
    start=time.monotonic();native=sr.infer_rgb(model,clean)
    npth=O/f'{gid}-asphalt-neural4x.png';native.save(npth)
    n=np.asarray(native,dtype=np.float32);drift=rgb.mean(axis=(0,1))-n.mean(axis=(0,1))
    fixed=Image.fromarray(np.rint(np.clip(n+drift,0,255)).astype(np.uint8))
    out=np.asarray(fixed.resize((src.width*8,src.height*8),Image.Resampling.LANCZOS)).copy()
    mask8=np.repeat(np.repeat(paint,8,axis=0),8,axis=1)
    original8=np.repeat(np.repeat(a[:,:,:3],8,axis=0),8,axis=1)
    out[mask8]=original8[mask8]
    im=Image.fromarray(out);im.putalpha(255);p=O/f'{gid}-paint-aware-8x.png';im.save(p)
    assert np.array_equal(np.asarray(im)[:,:,:3][mask8],original8[mask8])
    row={'group_id':gid,'source_id':group['representative']['id'],'source':group['representative']['png'],
         'source_rgba_sha256':group['rgba_sha256'],'pixel_equivalent_members':group['members'],
         'model':model_rec,'device':torch.cuda.get_device_name(0),'precision':'float32','native_neural_scale':4,
         'post_scale':'Lanczos 2x for neural background. Source paint mask and colors reconstructed exactly at 8x.',
         'paint_mask':str(mp),'paint_pixels':int(paint.sum()),'clean_plate':str(clean_path),
         'clean_plate_method':'Nearest non-paint original RGB. All non-paint source pixels unchanged before inference.',
         'native':str(npth),'native_sha256':sr.sha(npth.read_bytes()),'mean_color_offset_rgb':drift.tolist(),
         'output':str(p),'output_sha256':sr.sha(p.read_bytes()),'output_size':list(im.size),
         'paint_geometry_and_color_exact':True,'local_inference':True,'image_upload':False,
         'metrics':sr.roundtrip_metrics(src,im),'seconds':time.monotonic()-start,
         'visual_review':'pending','runtime_verified':False,'release_eligible':False}
    rows.append(row)
    ims=[src.convert('RGB'),Image.open(old[gid]).convert('RGB'),im.convert('RGB')]
    s=min(488/src.width,308/src.height,8);size=(round(src.width*s),round(src.height*s))
    for c,v in enumerate(ims):
        x=c*512+12;y=45+k*370;draw.text((x,y+2),gid,font=font,fill='white')
        sheet.paste(v.resize(size,Image.Resampling.NEAREST if c==0 else Image.Resampling.LANCZOS),(x,y+36))
    print('REWORKED',gid,flush=True)
proof=R/'outputs/local_sr_road_paint_rework.png';sheet.save(proof)
report={'schema':'brs-road-paint-rework/v2','files':rows,'comparison':str(proof),'runtime_verified':False,'release_eligible':False}
(R/'qa/local_sr_road_paint_rework_v2.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
