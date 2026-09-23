import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads((R/p).read_text('utf8'))
q=read('qa/local_sr009_inference.json');retry=read('qa/local_sr009_rework.json');cat=read('qa/battle_sr_catalog.json');groups={g['group_id']:g for g in cat['groups']}
wdn=[136,137,140,141,142,143,153,154,155,183,196,199]
photo=[132,135,138,171,197,198]
choices={f'BM{i:03d}':('wdn' if i in wdn else 'photo') for i in wdn+photo}
selected={gid:next(r for r in q['files'] if r['group_id']==gid and r['model_id']==mid) for gid,mid in choices.items()}
for gid in ['BM139','BM146','BM172','BM195']:selected[gid]=next(r for r in retry['files'] if r['id']==gid+'-filtered-guided')
assert len(selected)==22
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17);pages=[];directory=R/'outputs/sr009-mattes';directory.mkdir(exist_ok=True)
items=sorted(selected.items())
for start in range(0,len(items),3):
 batch=items[start:start+3];s=Image.new('RGB',(1320,len(batch)*330+42),'#293440');d=ImageDraw.Draw(s)
 for j,label in enumerate(['원본 · 어두운 배경','후보 · 어두운 배경','원본 · 밝은 배경','후보 · 밝은 배경']):d.text((j*330+10,8),label,font=font,fill='white')
 for i,(gid,row) in enumerate(batch):
  src=Image.open(row['source']).convert('RGBA');out=Image.open(row['output']).convert('RGBA');scale=min(310/src.width,265/src.height,4);wh=(round(src.width*scale),round(src.height*scale))
  for j,im in enumerate([src,out,src,out]):
   x=j*330+10;y=i*330+45;d.text((x,y),f'{gid} 표시 {scale:.2f}배',font=font,fill='white');v=im.resize(wh,Image.Resampling.NEAREST if j%2==0 else Image.Resampling.LANCZOS);bg=Image.new('RGB',wh,'#111111' if j<2 else '#eeeeee');bg.paste(v,(0,0),v);s.paste(bg,(x,y+30))
 p=directory/f'matte-{start//3+1:02d}.png';s.save(p);pages.append(str(p))
row=selected['BM136'];src=Image.open(row['source']).convert('RGBA');out=Image.open(row['output']).convert('RGBA');s=Image.new('RGB',(1060,760),'#293440');d=ImageDraw.Draw(s)
for i,box in enumerate([(32,0,96,64),(224,32,288,96)]):
 for j,im in enumerate([src.crop(box),out.crop(tuple(v*8 for v in box))]):
  x=j*530+10;y=i*380+10;d.text((x,y),f'BM136 {box} '+('원본' if j==0 else '후보'),font=font,fill='white');im=im.resize((320,320),Image.Resampling.NEAREST if j==0 else Image.Resampling.LANCZOS);bg=Image.new('RGB',im.size,'#eeeeee');bg.paste(im,(0,0),im);s.paste(bg,(x,y+34))
p=directory/'BM136-detail.png';s.save(p);pages.append(str(p))
record={'schema':'brs-sr009-proposed-review/v1','selected':{g:{'output':r['output'],'output_sha256':r['output_sha256'],'model_id':r.get('model_id'),'id':r.get('id')} for g,r in selected.items()},'holds':['BM145','BM147'],'matte_pages':pages,'review_state':'pending final matte inspection','runtime_verified':False}
(R/'qa/local_sr009_proposed_review.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),'utf8')
src=Image.open(groups['BM189']['representative']['png']).convert('RGB');s=Image.new('RGB',(1060,575),'#293440');d=ImageDraw.Draw(s)
for j,(pic,label) in enumerate([(src,'BM189 원본 · 단순 확대'),(ImageOps.autocontrast(src.convert('L')).convert('RGB'),'진단용 대비 조정 · 원본 판독 보조')]):d.text((j*530+10,8),label,font=font,fill='white');s.paste(pic.resize((512,512),Image.Resampling.NEAREST),(j*530+10,42))
s.save(R/'outputs/BM189_source_inspection.png')
print(json.dumps({'choices':len(selected),'matte_pages':len(pages),'loss_records':[(r['group_id'],r['model_id'],r['alpha_metrics']) for r in q['files'] if r['alpha_metrics']['source_ge16_reduced_below8']>0]}),flush=True)
