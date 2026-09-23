import json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];O=R/'outputs/field-source-review01';O.mkdir(parents=True,exist_ok=True);Q=R/'qa/field_source_review01.json'
if Q.exists():raise SystemExit('Existing source pages; do not replace reviewed evidence.')
q=json.loads((R/'qa/field_map_inventory_v2.json').read_text('utf8'));tex={t['id']:t for t in q['textures']};groups=[g for g in q['groups'] if not g['battle_pixel_equivalent_group']][:72]
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',16);small=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',13);rows=[];pages=[]
def sha(b):return hashlib.sha256(b).hexdigest()
for pi in range(0,len(groups),9):
 batch=groups[pi:pi+9];sheet=Image.new('RGB',(900,1020),'#293440');d=ImageDraw.Draw(sheet)
 for j,g in enumerate(batch):
  t=tex[g['representative']];im=Image.open(t['png']).convert('RGBA');assert sha(im.tobytes())==g['rgba_sha256']==t['rgba_sha256'];assert sha(Path(t['source']).read_bytes())==t['source_sha256'];x=j%3*300+10;y=j//3*340+10
  d.text((x,y),f'{g["group_id"]} {im.width}×{im.height} alpha {t["alpha_min"]}–{t["alpha_max"]}',font=font,fill='white');d.text((x,y+22),g['representative'].split('/')[0],font=small,fill='#ccd7de')
  scale=min(280/im.width,270/im.height);wh=(max(1,round(im.width*scale)),max(1,round(im.height*scale)));pic=im.resize(wh,Image.Resampling.NEAREST)
  bg=Image.new('RGB',(280,270),'#72808b');bg.paste(pic,((280-wh[0])//2,(270-wh[1])//2),pic);sheet.paste(bg,(x,y+48))
  rows.append({'group_id':g['group_id'],'representative':g['representative'],'source':t['png'],'source_ptm':t['source'],'source_ptm_sha256':t['source_sha256'],'source_rgba_sha256':g['rgba_sha256'],'size':list(im.size),'alpha_min':t['alpha_min'],'alpha_max':t['alpha_max'],'classification':'pending','page':pi//9+1})
 p=O/f'source-{pi//9+1:02}.png';sheet.save(p);pages.append({'path':str(p),'sha256':sha(p.read_bytes()),'group_ids':[g['group_id'] for g in batch],'review_status':'pending'})
Q.write_text(json.dumps({'schema':'brs-field-source-review/v1','scope':'First72 of351 field groups whose dimensions/RGBA are not identical to battle groups; source review only.','source_inventory':'qa/field_map_inventory_v2.json','source_inventory_sha256':sha((R/'qa/field_map_inventory_v2.json').read_bytes()),'files':rows,'pages':pages,'new_neural_passes':0,'runtime_verified':False,'protagonist_exclusion_status':'No source or runtime modifications; character-like or ambiguous items must be held for consumer/exclusion review.','all_game_complete':False},ensure_ascii=False,indent=2),'utf8');print('Prepared72 field originals in8 pages.')
