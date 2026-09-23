import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1]
sel={'BM087':('qa/local_sr013_facades_v2.json','BM087-bands'),'BM115':('qa/local_sr013_rubble_tone.json','BM115-tone-0.80')};font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18);pages=[]
for gid,(report,ident) in sel.items():
    r=next(r for r in json.loads((R/report).read_text('utf8'))['files'] if r['id']==ident);src=Image.open(r['source']).convert('RGBA');out=Image.open(r['output']).convert('RGBA');scale=min(4,500/src.width);wh=(round(src.width*scale),round(src.height*scale));s=Image.new('RGB',(2080,wh[1]+65),'#293440');d=ImageDraw.Draw(s)
    for j,(im,bg,title) in enumerate([(src,'#111111','원본 · 어두운 배경'),(out,'#111111','재작업 · 어두운 배경'),(src,'#eeeeee','원본 · 밝은 배경'),(out,'#eeeeee','재작업 · 밝은 배경')]):
        x=j*520+8;d.text((x,8),gid+' '+title,font=font,fill='white');im=im.resize(wh,Image.Resampling.NEAREST if j%2==0 else Image.Resampling.LANCZOS);base=Image.new('RGB',wh,bg);base.paste(im,(0,0),im);s.paste(base,(x,42))
    p=R/f'outputs/sr013_final_{gid}_mattes.png';s.save(p);pages.append(str(p))
    if gid=='BM115':
        box=(126,15,162,45);s=Image.new('RGB',(940,590),'#293440');d=ImageDraw.Draw(s)
        for i,bg in enumerate(['#111111','#eeeeee']):
            for j,im in enumerate([src,out]):
                x=j*470+8;y=i*295+8;d.text((x,y),'중앙 얇은 연결부 · '+('원본' if j==0 else '재작업'),font=font,fill='white');im=im.crop(box if j==0 else tuple(v*8 for v in box)).resize((288,240),Image.Resampling.NEAREST if j==0 else Image.Resampling.LANCZOS);base=Image.new('RGB',im.size,bg);base.paste(im,(0,0),im);s.paste(base,(x,y+35))
        p=R/'outputs/sr013_final_BM115_connector.png';s.save(p);pages.append(str(p))
(R/'qa/local_sr013_proposed_review.json').write_text(json.dumps({'selected':sel,'matte_pages':pages,'review_status':'pending final matte review','runtime_verified':False},ensure_ascii=False,indent=2),'utf8');print('Prepared final matte and connector comparison pages.')
