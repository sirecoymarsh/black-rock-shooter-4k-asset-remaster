import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1]
audit=json.loads((R/'qa/ui_source_audit.json').read_text(encoding='utf-8'))
rows=[];font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',20)
for i in [19,20,21,23,24,25,26]:
 a=audit['assets'][i];old=Image.open(Path(a['source']).with_suffix('.png')).convert('RGBA');new=Image.open(R/f'workspace/ui_candidates_v3/UI-{i:02d}_8x.png').convert('RGBA').crop((0,0,old.width*8,old.height*8))
 old=old.resize((old.width*4,old.height*4),Image.Resampling.NEAREST);new=new.resize(old.size,Image.Resampling.LANCZOS)
 row=Image.new('RGB',(2100,old.height+45),'#243449');d=ImageDraw.Draw(row);d.text((10,5),f'UI-{i:02d} 원본 / 현재 후보',font=font,fill='white');row.paste(old,(10,40),old);row.paste(new,(1060,40),new);rows.append(row)
sheet=Image.new('RGB',(2100,sum(r.height for r in rows)),'#243449');y=0
for row in rows:sheet.paste(row,(0,y));y+=row.height
sheet.save(R/'qa/hud_before_geometry_review.png')
