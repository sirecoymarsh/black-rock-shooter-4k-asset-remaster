"""Render exact-size matte checks and the next unprocessed source population."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

R = Path(__file__).resolve().parents[1]
q = json.loads((R/'qa/local_sr_observed_rework_v2.json').read_text('utf8'))
rows = {r['id']: r for r in q['files']}
old = json.loads((R/'qa/local_sr_observed_v1.json').read_text('utf8'))
parents = {r['group_id']: r for r in old['files'] if r['model_id']=='wdn'}
font = ImageFont.truetype('C:/Windows/Fonts/malgun.ttf', 18)
for gid in ['BM130','BM159','BM164','BM165']:
    row = rows[gid+'-prefilter075-guided065']
    src = Image.open(row['source']).convert('RGBA')
    ims = [src, Image.open(parents[gid]['output']).convert('RGBA'), Image.open(row['output']).convert('RGBA')]
    cw = max(300, src.width*2+24)
    s = Image.new('RGB', (cw*3,src.height*3+150), '#293440')
    d = ImageDraw.Draw(s)
    for j,im in enumerate(ims):
        x = j*cw+10
        d.text((x,8),gid+' '+['원본','이전 로컬','재작업 후보'][j],font=font,fill='white')
        for factor, y, color in [(1,65,'#111111'),(2,src.height+115,'#eeeeee')]:
            wh = (src.width*factor,src.height*factor)
            d.text((x,y-26),f'원본 대비 {factor}배 표시',font=font,fill='white')
            v = im.resize(wh,Image.Resampling.NEAREST if j==0 else Image.Resampling.LANCZOS)
            bg = Image.new('RGB',wh,color); bg.paste(v,(0,0),v); s.paste(bg,(x,y))
    s.save(R/f'outputs/local_sr007_matte_{gid}.png')

cat=json.loads((R/'qa/battle_sr_catalog.json').read_text('utf8'))
todo=[g for g in cat['groups'] if not g.get('local_sr_attempted') and any('stg03_' in m or 'stg04_' in m for m in g['members'])]
pages=[]
for start in range(0,len(todo),9):
    batch=todo[start:start+9];s=Image.new('RGB',(900,900),'#293440');d=ImageDraw.Draw(s)
    for i,g in enumerate(batch):
        x=(i%3)*300+10;y=(i//3)*300+10
        d.text((x,y),f"{g['group_id']} {g['width']}×{g['height']} A{g['representative']['alpha_min']}",font=font,fill='white')
        src=Image.open(g['representative']['png']).convert('RGBA');scale=min(280/src.width,250/src.height,6);wh=(round(src.width*scale),round(src.height*scale))
        src=src.resize(wh,Image.Resampling.NEAREST);bg=Image.new('RGB',wh,'#72808b');bg.paste(src,(0,0),src);s.paste(bg,(x,y+32))
    p=R/f'qa/battle-source-catalog/stage03-04-pending-{start//9+1:02d}.png';s.save(p);pages.append(str(p))
(R/'qa/local_sr_stage0304_source_review.json').write_text(json.dumps({'group_ids':[g['group_id'] for g in todo],'source_pages':pages,'visual_review':'pending','runtime_verified':False},ensure_ascii=False,indent=2),'utf8')
print(json.dumps({'source_groups':len(todo),'source_pages':len(pages),'matte_pages':4}))
