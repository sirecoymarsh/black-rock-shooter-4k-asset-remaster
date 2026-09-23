"""Compare measured local models after rejecting over-smoothed metal detail."""
import sys, json, time, gc
from pathlib import Path
import torch, spandrel, numpy as np
from PIL import Image, ImageDraw, ImageFont
import local_sr as sr

sys.stdout.reconfigure(encoding='utf8')
torch.set_num_threads(4)
R = Path(__file__).resolve().parents[1]
O = R/'workspace/local-sr/title-trial-v2'
O.mkdir(parents=True, exist_ok=True)
manifest = json.loads((R/'workspace/local-sr/models/models.json').read_text('utf8'))
models = {x['name']:x for x in manifest['records']}
source = R/'workspace/source/ui_expanded/title.vol/001_if_title.zzz/000.png'
im = Image.open(source).convert('RGBA')
assert sr.sha(im.tobytes()) == 'ded2fa74a3a2753eb35c15b3b373b36cbb76fe264ce12a6c82915982f5553e42'
src = im.crop((0,0,480,272)).convert('RGB')
records = []
images = [('source-nearest',src.resize((1920,1088),Image.Resampling.NEAREST))]
prev = Image.open(R/'workspace/local-sr/title-trial-v1/title-active-neural-4x.png').convert('RGB')
images.append(('anime6B-default-REJECTED',prev))

def read_weight(name):
    rec=models[name];p=Path(rec['path']);assert sr.sha(p.read_bytes()) == rec['sha256']
    d=torch.load(p,map_location='cpu',weights_only=True)
    return d.get('params_ema',d.get('params',d))

def run(name, weights, sources, exposure=1):
    model=spandrel.ModelLoader().load_from_state_dict(weights).cuda().eval()
    assert model.scale==4
    original=np.asarray(src)
    if exposure!=1:
        assert float(original.max())*exposure<=255.00001, 'No exposure clipping allowed'
    prep=Image.fromarray(np.rint(original.astype(np.float32)*exposure).astype(np.uint8))
    start=time.monotonic();native=sr.infer_rgb(model,prep)
    if exposure!=1:native=Image.fromarray(np.rint(np.asarray(native,dtype=np.float32)/exposure).astype(np.uint8))
    p=O/(name+'-neural-4x.png');native.save(p)
    out=native.resize((3840,2176),Image.Resampling.LANCZOS);out.save(O/(name+'-active-8x.png'))
    record={'id':name,'model_sources':sources,'exposure_before':exposure,'exposure_after':1/exposure,
            'native_size':list(native.size),'output_size':list(out.size),'output':str(O/(name+'-active-8x.png')),
            'output_sha256':sr.sha((O/(name+'-active-8x.png')).read_bytes()),
            'metrics':sr.roundtrip_metrics(src,out),'elapsed_seconds':time.monotonic()-start,
            'visual_review':'pending','runtime_verified':False,'release_eligible':False}
    records.append(record);images.append((name,native));print(json.dumps(record),flush=True)
    del model;gc.collect();torch.cuda.empty_cache()

g=read_weight('realesr-general-x4v3.pth');w=read_weight('realesr-general-wdn-x4v3.pth')
assert g.keys()==w.keys()
for dn in [0.0,0.5,1.0]:
    weights={k:dn*g[k]+(1-dn)*w[k] for k in g}
    run('general-dn'+str(dn),weights,[{**models[n],'weight':v} for n,v in [('realesr-general-x4v3.pth',dn),('realesr-general-wdn-x4v3.pth',1-dn)]])
run('photo-x4plus',read_weight('RealESRGAN_x4plus.pth'),[models['RealESRGAN_x4plus.pth']])
assert sr.sha(sr.MODEL.read_bytes())==sr.MODEL_SHA
state=torch.load(sr.MODEL,map_location='cpu',weights_only=True)
gain=min(3.0,255.0/float(np.asarray(src).max()))
run('anime6B-exposure',state.get('params_ema',state),[{'path':str(sr.MODEL),'sha256':sr.MODEL_SHA}],gain)

font=ImageFont.truetype(r'C:\Windows\Fonts\malgun.ttf',20)
box=(140,125,340,270)
for page in range(0,len(images),3):
    group=images[page:page+3];sheet=Image.new('RGB',(820*len(group),1230),'#293440');d=ImageDraw.Draw(sheet)
    for col,(name,pic) in enumerate(group):
        x=10+820*col;d.text((x,8),name,font=font,fill='white')
        crop=pic.crop(tuple(v*4 for v in box))
        sheet.paste(crop,(x,44))
        light=Image.fromarray(np.minimum(np.asarray(crop,dtype=np.uint16)*3,255).astype(np.uint8))
        sheet.paste(light,(x,640))
    d.text((10,1200),'위: 실제 밝기 / 아래: 양쪽 동일 3배 밝기, 검수 전 후보',font=font,fill='white')
    sheet.save(R/f'outputs/local_sr_title_models_v2_{page//3+1}.png')
report={'schema':'brs-local-sr-comparison/v2','input':str(source),'input_rgba_sha256':sr.sha(im.tobytes()),
        'device':torch.cuda.get_device_name(0),'torch':torch.__version__,'spandrel':spandrel.__version__,
        'color_order':'RGB','precision':'float32','neural_scale':4,'post_scale':'Lanczos 2x',
        'reason':'Default anime6B removed source metal texture and over-emphasized rivet highlights; compare alternatives.',
        'files':records,'external_generation':False,'release_eligible':False}
(R/'qa/local_sr_title_models_v2.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
print('Local model comparison complete',flush=True)
