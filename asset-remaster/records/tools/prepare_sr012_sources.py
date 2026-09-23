import hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1]
cat=json.loads((R/'qa/battle_sr_catalog.json').read_text('utf8'))
groups=[g for g in cat['groups'] if not g.get('local_sr_attempted')]
assert len(groups)==40
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18)
directory=R/'outputs/sr012-sources';directory.mkdir(exist_ok=True);pages=[]
for start in range(0,len(groups),8):
    batch=groups[start:start+8];sheet=Image.new('RGB',(1240,1440),'#293440');d=ImageDraw.Draw(sheet)
    for k,g in enumerate(batch):
        src=Image.open(g['representative']['png']).convert('RGBA');assert hashlib.sha256(src.tobytes()).hexdigest()==g['rgba_sha256']
        x=k%2*620+10;y=k//2*360+8;a=src.getchannel('A').getextrema();d.text((x,y),f"{g['group_id']} {src.width}×{src.height} alpha {a}",font=font,fill='white')
        scale=min(596/src.width,300/src.height,8);wh=(round(src.width*scale),round(src.height*scale));v=src.resize(wh,Image.Resampling.NEAREST);bg=Image.new('RGB',wh,'#72808b');bg.paste(v,(0,0),v);sheet.paste(bg,(x,y+34))
    p=directory/f'source-{start//8+1:02d}.png';sheet.save(p);pages.append(str(p))
record={'schema':'brs-sr012-source-review/v1','group_ids':[g['group_id'] for g in groups],'pages':pages,'review_status':'pending direct source classification','runtime_verified':False}
(R/'qa/local_sr012_sources.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),'utf8')
print(json.dumps({'sources':len(groups),'pages':pages}))
