import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];a=json.loads((R/'qa/ui_source_audit.json').read_text(encoding='utf-8'))['assets'];rows=[];f=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',20)
for i in [0,1,12,13,15,16]:
 im=Image.open(Path(a[i]['source']).with_suffix('.png')).convert('RGBA')
 if i==15:im=im.crop((0,84,128,144))
 im=im.resize((im.width*6,im.height*6),Image.Resampling.NEAREST);row=Image.new('RGB',(1600,im.height+35),'#596270');ImageDraw.Draw(row).text((8,3),f'UI-{i:02d}',font=f,fill='white');row.paste(im,(8,32),im);rows.append(row)
out=Image.new('RGB',(1600,sum(r.height for r in rows)),'#596270');y=0
for row in rows:out.paste(row,(0,y));y+=row.height
out.save(R/'qa/menu_source_cells.png')
