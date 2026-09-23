import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1]
q=json.loads((R/'qa/local_sr011_bm221_rework.json').read_text('utf8'))
row=next(r for r in q['files'] if r['id']=='BM221-filtered-guided')
src=Image.open(row['source']).convert('RGBA');out=Image.open(row['output']).convert('RGBA')
s=Image.new('RGB',(1320,1300),'#293440');d=ImageDraw.Draw(s);font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17)
for i,box in enumerate([(0,0,32,160),(0,32,32,96)]):
    scale=3 if i==0 else 8;wh=((box[2]-box[0])*scale,(box[3]-box[1])*scale)
    for j,im in enumerate([src.crop(box),out.crop(tuple(v*8 for v in box)),src.crop(box),out.crop(tuple(v*8 for v in box))]):
        x=j*330+10;y=i*650+10;d.text((x,y),('원본' if j%2==0 else 'BM221 재작업')+f' · {scale}배',font=font,fill='white');im=im.resize(wh,Image.Resampling.NEAREST if j%2==0 else Image.Resampling.LANCZOS);bg=Image.new('RGB',wh,'#111111' if j<2 else '#eeeeee');bg.paste(im,(0,0),im);s.paste(bg,(x,y+35))
p=R/'outputs/sr011-mattes/BM221-rework-mattes.png';s.save(p)
print(str(p))
