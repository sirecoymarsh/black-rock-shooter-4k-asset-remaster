import hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1]
Q=R/'qa/local_sr_stage0506_source_review.json'
if Q.exists():raise SystemExit('Existing source review; inspect it instead of overwriting.')
cat=json.loads((R/'qa/battle_sr_catalog.json').read_text('utf8'))
groups=[g for g in cat['groups'] if 200<=int(g['group_id'][2:])<=283]
assert len(groups)==84 and not any(g.get('local_sr_attempted') for g in groups)
O=R/'outputs/sr010-sources';O.mkdir(exist_ok=True)
f=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17);pages=[]
for start in range(0,len(groups),9):
    batch=groups[start:start+9];s=Image.new('RGB',(1200,1140),'#293440');d=ImageDraw.Draw(s)
    for i,g in enumerate(batch):
        im=Image.open(g['representative']['png']).convert('RGBA')
        assert hashlib.sha256(im.tobytes()).hexdigest()==g['rgba_sha256']
        x=i%3*400+10;y=i//3*380+6
        d.text((x,y),f"{g['group_id']} {im.width}×{im.height} 알파 {im.getchannel('A').getextrema()}\n원본 단순 확대",font=f,fill='white')
        scale=min(380/im.width,310/im.height,8);size=(round(im.width*scale),round(im.height*scale))
        im=im.resize(size,Image.Resampling.NEAREST);bg=Image.new('RGB',size,'#7d858f');bg.paste(im,(0,0),im);s.paste(bg,(x,y+52))
    p=O/f'source-{start//9+1:02d}.png';s.save(p)
    pages.append({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'groups':[g['group_id'] for g in batch]})
report={'schema':'brs-source-review/v1','group_ids':[g['group_id'] for g in groups],'pages':pages,'visual_review':'pending','excluded_from_project':[]}
Q.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
print(json.dumps({'groups':len(groups),'pages':len(pages)}))
