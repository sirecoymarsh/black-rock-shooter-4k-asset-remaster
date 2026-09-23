"""First actual local SR candidate, with explicit neural-vs-resampling provenance."""
import sys, json, time
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import local_sr as sr

sys.stdout.reconfigure(encoding='utf8')
R = Path(__file__).resolve().parents[1]
O = R / 'workspace/local-sr/title-trial-v1'
O.mkdir(parents=True, exist_ok=True)
inv = json.loads((R / 'qa/ui_inventory_expanded.json').read_text('utf8'))
t = next(t for t in inv['textures'] if t['id'] == 'title.vol::001_if_title.zzz::000')
src_path = Path(t['png'])
src = Image.open(src_path).convert('RGBA')
assert sr.sha(src.tobytes()) == t['rgba_sha256']
assert src.size == (512,280)
assert src.getchannel('A').getbbox() == (0,0,480,272)
assert np.asarray(src.getchannel('A'))[:272,:480].min() == 255
active = src.crop((0,0,480,272)).convert('RGB')
start = time.monotonic()
model = sr.load_model()
print('Running local model', sr.provenance(), flush=True)
native = sr.infer_rgb(model, active)
native.save(O / 'title-active-neural-4x.png')
up = native.resize((3840,2176), Image.Resampling.LANCZOS)
up.save(O / 'title-active-8x.png')
logical = src.resize((4096,2240), Image.Resampling.NEAREST)
logical.paste(up.convert('RGBA'), (0,0))
assert logical.getchannel('A').tobytes() == src.getchannel('A').resize(logical.size, Image.Resampling.NEAREST).tobytes()
logical.save(O / 'title-logical-8x.png')

# Comparative images use equal-sized crops. A second view raises display brightness
# on both sides equally because this asset is deliberately very dark in-game.
font = ImageFont.truetype(r'C:\Windows\Fonts\malgun.ttf', 22)
sheet = Image.new('RGB', (1500,1110), '#27303b')
d = ImageDraw.Draw(sheet)
for col,label in enumerate(['원본 단순 확대', '로컬 AI 4배 복원 → 8배 출력']):
    d.text((14+750*col,10),label,font=font,fill='white')
for row,box in enumerate([(150,140,330,265),(215,25,280,90)]):
    target = (720,500) if row == 0 else (500,500)
    for col,im in enumerate([active.crop(box).resize(target, Image.Resampling.NEAREST),
                             up.crop(tuple(v*8 for v in box)).resize(target, Image.Resampling.LANCZOS)]):
        sheet.paste(im,(14+col*750,52+row*530))
sheet.save(R / 'outputs/local_sr_title_comparison_v1.png')
boost = np.asarray(sheet).copy()
for row in range(2):
    for col in range(2):
        x=14+col*750;y=52+row*530;w=720 if row==0 else 500
        boost[y:y+500,x:x+w] = np.minimum(boost[y:y+500,x:x+w].astype(np.uint16)*3,255).astype(np.uint8)
bright = Image.fromarray(boost)
ImageDraw.Draw(bright).text((14,1070),'검수용: 양쪽 밝기를 동일하게 3배 표시 (실제 텍스처는 원래 밝기)',font=font,fill='white')
bright.save(R / 'outputs/local_sr_title_inspection_v1.png')
record = {'schema':'brs-local-sr-trial/v1','asset_id':t['id'],'input_png':str(src_path),
          'input_png_sha256':sr.sha(src_path.read_bytes()),'input_rgba_sha256':t['rgba_sha256'],
          'iso_sha256':inv['iso_sha256'],'active_source_box':[0,0,480,272],
          'logical_output_size':list(logical.size),'active_output_size':list(up.size),
          'method':sr.provenance(),'alpha':'Exact nearest expansion; original opaque active rectangle and transparent padding retained.',
          'output':str(O / 'title-logical-8x.png'),'output_sha256':sr.sha((O / 'title-logical-8x.png').read_bytes()),
          'output_rgba_sha256':sr.sha(logical.tobytes()),'metrics':sr.roundtrip_metrics(active,up),
          'elapsed_seconds':time.monotonic()-start,'visual_review':'pending','runtime_verified':False,
          'release_eligible':False,'scope':'One title background only; not full-game upscaling or native 8x AI.'}
(R / 'qa/local_sr_title_trial_v1.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),'utf8')
print(json.dumps(record,ensure_ascii=False),flush=True)
