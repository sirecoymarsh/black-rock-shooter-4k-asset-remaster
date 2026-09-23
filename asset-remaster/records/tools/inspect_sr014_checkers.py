import json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];O=R/'outputs/sr014-source';O.mkdir(exist_ok=True)
cat=json.loads((R/'qa/battle_sr_catalog.json').read_text('utf8'));groups={g['group_id']:g for g in cat['groups']}
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',15)
boxes={'BM175':[(0,0,32,32),(0,32,32,64)],'BM201':[(30,12,152,85),(148,20,237,155),(10,92,85,198),(5,192,130,256),(194,197,249,253)],'BM209':[(7,3,116,50),(135,22,248,56),(0,58,256,81)],'BM244':[(6,13,57,55),(187,19,256,73),(23,67,66,139),(89,109,148,213),(170,194,214,256)]}
for gid,parts in boxes.items():
 src=Image.open(groups[gid]['representative']['png']).convert('RGB');a=np.asarray(src)
 for i,box in enumerate(parts):
  scale=20 if gid=='BM175' else 6;wh=((box[2]-box[0])*scale,(box[3]-box[1])*scale);s=Image.new('RGB',(wh[0]+55,wh[1]+55),'#293440');d=ImageDraw.Draw(s);s.paste(src.crop(box).resize(wh,Image.Resampling.NEAREST),(45,45))
  step=2 if gid=='BM175' else 10
  for x in range((box[0]+step-1)//step*step,box[2],step):d.text((45+(x-box[0])*scale,20),str(x),font=font,fill='white')
  for y in range((box[1]+step-1)//step*step,box[3],step):d.text((4,45+(y-box[1])*scale),str(y),font=font,fill='white')
  d.text((5,0),f'{gid} p{i} source {box}',font=font,fill='white');s.save(O/f'{gid}-p{i}.png')
 if gid=='BM175':
  print('BM175 R values')
  for y in list(range(1,17))+list(range(33,49)): print(y,','.join(map(str,a[y,:,0].tolist())))
print('Source inspection sheets:',len(list(O.glob('*.png'))))
