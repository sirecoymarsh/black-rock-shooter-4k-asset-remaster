import json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np
R=Path(__file__).resolve().parents[1];r=json.loads((R/'qa/field_sr001_inference.json').read_text('utf8'));rows={v['id']:v for v in r['files']};O=R/'outputs/field-sr001'
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18);rec=[]
boxes={55:(0,27,64,64),71:(0,35,64,60),72:(0,42,64,61),78:(35,44,53,57),84:(5,0,59,53),117:(0,0,128,64),119:(0,0,64,64)}
for n,box in boxes.items():
 gid=f'FM{n:04d}';v=rows[gid+'-wdn'];s=Image.open(v['source']).convert('RGBA');w=(box[2]-box[0])*8;h=(box[3]-box[1])*8;canvas=Image.new('RGB',(w*3+24,h+56),'#25313c');d=ImageDraw.Draw(canvas)
 for i,(path,title) in enumerate([(v['source'],'원본 8배 · 비교용'),(v['output'],'로컬 WDN'),(rows[gid+'-photo']['output'],'로컬 Photo')]):
  im=Image.open(path).convert('RGB').crop(box if i==0 else tuple(b*8 for b in box))
  if i==0:im=im.resize((w,h),Image.Resampling.NEAREST)
  d.text((i*(w+8)+4,4),gid+' '+title,font=font,fill='white');canvas.paste(im,(i*(w+8)+4,38))
 p=O/f'detail-{gid}.png';canvas.save(p);rec.append({'group_id':gid,'box_source':box,'scale':8,'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'review_status':'pending'})
(R/'qa/field_sr001_details.json').write_text(json.dumps({'pages':rec},ensure_ascii=False,indent=2),'utf8')
for gid,axis,lo,hi in [('FM0072','x',46,51),('FM0084','y',15,49),('FM0071','x',43,48),('FM0078','y',42,48)]:
 src=np.asarray(Image.open(rows[gid+'-wdn']['source']).convert('RGB'),float).mean(2)
 profile=src[lo:hi].mean(0) if axis=='x' else src[:,lo:hi].mean(1)
 print(gid,axis,' '.join(f'{i}:{v:.0f}' for i,v in enumerate(profile)))
