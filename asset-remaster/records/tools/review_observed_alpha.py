import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1]
q=json.loads((R/'qa/local_sr_observed_v1.json').read_text('utf8'));rows={(r['group_id'],r['model_id']):r for r in q['files']}
selected={'BM131':'wdn','BM148':'photo','BM149':'photo','BM158':'wdn','BM166':'photo','BM167':'photo','BM168':'wdn'}
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17)
items=list(selected.items())
for start in range(0,len(items),3):
    batch=items[start:start+3];s=Image.new('RGB',(1536,len(batch)*385+45),'#293440');d=ImageDraw.Draw(s)
    for j,t in enumerate(['원본 · 검정 배경','후보 · 검정 배경','원본 · 밝은 배경','후보 · 밝은 배경']):d.text((j*384+10,5),t,font=font,fill='white')
    for i,(gid,mid) in enumerate(batch):
        row=rows[(gid,mid)];src=Image.open(row['source']).convert('RGBA');out=Image.open(row['output']).convert('RGBA');factor=min(366/src.width,325/src.height,8);wh=(round(src.width*factor),round(src.height*factor))
        for j,im in enumerate([src,out,src,out]):
            im=im.resize(wh,Image.Resampling.NEAREST if j%2==0 else Image.Resampling.LANCZOS);bg=Image.new('RGB',wh,'#080808' if j<2 else '#eeeeee');bg.paste(im,(0,0),im);x=j*384+8;y=45+i*385;d.text((x,y),gid+' '+mid,font=font,fill='white');s.paste(bg,(x,y+30))
    s.save(R/f'outputs/local_sr_observed_matte_{start//3+1:02d}.png')
print('Made three source/candidate alpha comparison pages.')
