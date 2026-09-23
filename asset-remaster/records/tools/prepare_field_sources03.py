import json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];O=R/'outputs/field-source-review03';Q=R/'qa/field_source_review03.json';assert not Q.exists();O.mkdir(parents=True,exist_ok=False)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
inv=json.loads((R/'qa/field_map_inventory_v2.json').read_text('utf8'));tex={t['id']:t for t in inv['textures']};priors=[R/f'qa/field_source_review0{i}.json' for i in (1,2)];done={v['group_id'] for p in priors for v in json.loads(p.read_text('utf8'))['files']};groups=[g for g in inv['groups'] if not g['battle_pixel_equivalent_group'] and g['group_id'] not in done][:72]
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',16);small=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',13);rows=[];pages=[]
for k in range(0,len(groups),9):
 batch=groups[k:k+9];sheet=Image.new('RGB',(900,1020),'#293440');d=ImageDraw.Draw(sheet)
 for j,g in enumerate(batch):
  t=tex[g['representative']];im=Image.open(t['png']).convert('RGBA');assert hashlib.sha256(im.tobytes()).hexdigest()==g['rgba_sha256']==t['rgba_sha256'];assert sha(t['source'])==t['source_sha256'];x=j%3*300+10;y=j//3*340+10
  d.text((x,y),f'{g["group_id"]} {im.width}×{im.height} alpha {t["alpha_min"]}–{t["alpha_max"]}',font=font,fill='white');d.text((x,y+22),g['representative'].split('/')[0],font=small,fill='#ccd7de');sc=min(280/im.width,270/im.height);wh=(round(im.width*sc),round(im.height*sc));pic=im.resize(wh,Image.Resampling.NEAREST);bg=Image.new('RGB',(280,270),'#72808b');bg.paste(pic,((280-wh[0])//2,(270-wh[1])//2),pic);sheet.paste(bg,(x,y+48))
  rows.append({'group_id':g['group_id'],'representative':g['representative'],'source':t['png'],'source_ptm':t['source'],'source_ptm_sha256':t['source_sha256'],'source_rgba_sha256':g['rgba_sha256'],'size':list(im.size),'alpha_min':t['alpha_min'],'alpha_max':t['alpha_max'],'classification':'pending','page':k//9+1})
 p=O/f'source-{k//9+1:02d}.png';sheet.save(p);pages.append({'path':str(p),'sha256':sha(p),'group_ids':[g['group_id'] for g in batch],'review_status':'pending'})
Q.write_text(json.dumps({'schema':'brs-field-source-review/v3','scope':'Next72 unclassified field-only pixel groups; source appearance is not consumer/UV/exclusion proof.','source_inventory':'qa/field_map_inventory_v2.json','source_inventory_sha256':sha(R/'qa/field_map_inventory_v2.json'),'prior_classifications_sha256':{str(p.relative_to(R)):sha(p) for p in priors},'files':rows,'pages':pages,'new_neural_passes':0,'runtime_verified':False,'all_game_complete':False},ensure_ascii=False,indent=2),'utf8');print('Prepared',len(rows),'sources',len(pages),'pages')
