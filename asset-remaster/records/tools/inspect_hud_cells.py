import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];a=json.loads((R/'qa/ui_source_audit.json').read_text(encoding='utf-8'));d=json.loads((R/'qa/ui_consumers_static.json').read_text(encoding='utf-8'))
f=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18);rows=[]
for i,b in [(19,(150,34,235,48)),(20,(46,40,64,120)),(21,(0,0,256,48)),(23,(98,0,128,104)),(24,(0,0,128,24)),(25,(0,0,128,32)),(26,(0,0,256,32))]:
 im=Image.open(Path(a['assets'][i]['source']).with_suffix('.png')).convert('RGBA').crop(b)
 if i in (20,23):im=im.rotate(90,expand=True)
 im=im.resize((im.width*8,im.height*8),Image.Resampling.NEAREST);r=Image.new('RGB',(max(1200,im.width+20),im.height+32),'#243449');ImageDraw.Draw(r).text((10,5),f'UI-{i:02d} {b}',font=f,fill='white');r.paste(im,(10,30),im);rows.append(r)
out=Image.new('RGB',(max(r.width for r in rows),sum(r.height for r in rows)),'#243449');y=0
for r in rows:out.paste(r,(0,y));y+=r.height
out.save(R/'qa/hud_source_cells.png')
for archive,member,ids in [('SYSTEM/if_btlsys',0,[4,19,20,27,28,30,31,32,33,38]),('SYSTEM/if_fldsys',12,[17,19,20,32,33,52,53,54,55,56,57]),('SYSTEM/if_fldsys',23,[2,3,5]),('SYSTEM/if_fldsys',26,[28,37])]:
 ar=next(x for x in d['records'] if x['archive']==archive);m=next(x for x in ar['members'] if x['index']==member)
 print(archive,member)
 for i in ids:print(json.dumps(m['sdo']['records'][i]))
