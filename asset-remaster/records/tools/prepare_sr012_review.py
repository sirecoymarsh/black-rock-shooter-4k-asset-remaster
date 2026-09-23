"""Prepare full alpha mattes and native-size detail views, not auto-approval."""
import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1]
q=json.loads((R/'qa/local_sr012_inference.json').read_text('utf8'))
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17)
O=R/'outputs/sr012-mattes';O.mkdir(exist_ok=True)
choices={g:('photo' if g in {'BM062','BM063','BM074','BM101','BM116','BM118'} else 'wdn') for g in q['group_ids']}
rows={(r['group_id'],r['model_id']):r for r in q['files']}
pages=[];details=[]
for start in range(0,len(q['group_ids']),3):
    batch=q['group_ids'][start:start+3];s=Image.new('RGB',(1320,len(batch)*340+42),'#293440');d=ImageDraw.Draw(s)
    for j,t in enumerate(['원본 · 어두운 배경','임시 후보 · 어두운 배경','원본 · 밝은 배경','임시 후보 · 밝은 배경']):d.text((j*330+8,8),t,font=font,fill='white')
    for i,g in enumerate(batch):
        r=rows[(g,choices[g])];src=Image.open(r['source']).convert('RGBA');out=Image.open(r['output']).convert('RGBA');sc=min(310/src.width,275/src.height,4);wh=(round(src.width*sc),round(src.height*sc))
        for j,im in enumerate([src,out,src,out]):
            x=j*330+8;y=i*340+45;d.text((x,y),g+' '+choices[g],font=font,fill='white');v=im.resize(wh,Image.Resampling.NEAREST if j%2==0 else Image.Resampling.LANCZOS);bg=Image.new('RGB',wh,'#111111' if j<2 else '#eeeeee');bg.paste(v,(0,0),v);s.paste(bg,(x,y+30))
    p=O/f'matte-{start//3+1:02d}.png';s.save(p);pages.append(str(p))
for g in ['BM065','BM074','BM079','BM087','BM110','BM115']:
    src=Image.open(rows[(g,'wdn')]['source']).convert('RGBA');box=(0,0,min(src.width,64),min(src.height,64))
    if g=='BM065':box=(0,28,src.width,92)
    if g=='BM087':box=(0,0,64,48)
    if g=='BM115':box=(64,0,128,src.height)
    wh=((box[2]-box[0])*8,(box[3]-box[1])*8);cw=max(280,wh[0]+20);rh=wh[1]+55;s=Image.new('RGB',(cw*3,rh*2),'#293440');d=ImageDraw.Draw(s)
    ims=[src.crop(box)]+[Image.open(rows[(g,m)]['output']).convert('RGBA').crop(tuple(v*8 for v in box)) for m in ['wdn','photo']]
    for i,c in enumerate(['#111111','#eeeeee']):
        for j,im in enumerate(ims):
            x=j*cw+8;y=i*rh+8;d.text((x,y),g+' '+['원본 8배','WDN','Photo'][j],font=font,fill='white');v=im.resize(wh,Image.Resampling.NEAREST if j==0 else Image.Resampling.LANCZOS);bg=Image.new('RGB',wh,c);bg.paste(v,(0,0),v);s.paste(bg,(x,y+32))
    p=O/f'{g}-detail.png';s.save(p);details.append(str(p))
report={'schema':'brs-sr012-proposed-review/v1','choices':choices,'matte_pages':pages,'detail_pages':details,'review_status':'pending direct review','runtime_verified':False}
(R/'qa/local_sr012_proposed_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
print(json.dumps({'pages':len(pages),'detail':len(details),'source_sizes':{g:list(Image.open(rows[(g,'wdn')]['source']).size) for g in q['group_ids']}}))
