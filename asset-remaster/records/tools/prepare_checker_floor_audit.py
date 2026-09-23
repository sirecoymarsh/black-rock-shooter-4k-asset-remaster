import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];cat=json.loads((R/'qa/battle_sr_catalog.json').read_text('utf8'));groups={g['group_id']:g for g in cat['groups']}
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18);pages=[]
for gid in ['BM201','BM209','BM226','BM244']:
    g=groups[gid];src=Image.open(g['representative']['png']).convert('RGBA');out=Image.open(g['candidate']['output']).convert('RGBA');wh=(src.width*2,src.height*2);s=Image.new('RGB',(1060,wh[1]+60),'#293440');d=ImageDraw.Draw(s)
    for j,im in enumerate([src,out]):
        x=j*530+10;d.text((x,10),gid+(' 원본 2배' if j==0 else ' 기존 후보 · 체크판 재검수'),font=font,fill='white');im=im.resize(wh,Image.Resampling.NEAREST if j==0 else Image.Resampling.LANCZOS);s.paste(im,(x,42))
    p=R/f'outputs/checker_audit_{gid}.png';s.save(p);pages.append(str(p))
(R/'qa/checker_floor_audit_pending.json').write_text(json.dumps({'pages':pages,'review_state':'pending','group_ids':['BM201','BM209','BM226','BM244']},ensure_ascii=False,indent=2),'utf8')
print('4 floor audit comparisons prepared')
