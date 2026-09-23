import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

R = Path(__file__).resolve().parents[1]
q = json.loads((R/'qa/local_sr009_inference.json').read_text('utf8'))
r = json.loads((R/'qa/local_sr009_bm196_rework.json').read_text('utf8'))
old = next(x for x in q['files'] if x['group_id']=='BM196' and x['model_id']=='wdn')
new = next(x for x in r['files'] if x['id']=='BM196-filtered-guided')
s = Image.new('RGB', (1596,1160), '#293440')
d = ImageDraw.Draw(s)
f = ImageFont.truetype('C:/Windows/Fonts/malgun.ttf', 19)
for i, bg in enumerate(['#111111','#eeeeee']):
    for j, (p,label) in enumerate([(old['source'],'원본 단순 확대'),(old['output'],'초기 결과 · 미채택'),(new['output'],'로컬 재처리 + 원본 명암 반영')]):
        im=Image.open(p).convert('RGBA').resize((512,512),Image.Resampling.NEAREST if j==0 else Image.Resampling.LANCZOS)
        plate=Image.new('RGB', im.size, bg);plate.paste(im,(0,0),im)
        x=j*532+10;y=i*580+8
        d.text((x,y),label,font=f,fill='white');s.paste(plate,(x,y+36))
p=R/'outputs/sr009-mattes/BM196-rework-mattes.png';s.save(p)
print(p)
