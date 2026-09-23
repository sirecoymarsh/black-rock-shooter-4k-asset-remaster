from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];q=json.loads((R/'qa/local_sr015_gpt_floor.json').read_text('utf8'));r=q['files'][1]
box=(202,200,242,249);scale=16;wh=(640,784);s=Image.new('RGB',(1390,850),'#293440');d=ImageDraw.Draw(s);font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',16)
for j,p in enumerate([r['source'],r['output']]):
 im=Image.open(p);im=im.crop(box if j==0 else tuple(z*8 for z in box)).resize(wh,Image.Resampling.NEAREST if j==0 else Image.Resampling.LANCZOS);off=45+j*695;s.paste(im.convert('RGB'),(off,45));d.text((off,0),'원본' if j==0 else '재작화',font=font,fill='white')
 for x in range(205,242,5):d.text((off+(x-box[0])*scale,20),str(x),font=font,fill='white')
 for y in range(200,249,5):d.text((off-40,45+(y-box[1])*scale),str(y),font=font,fill='white')
s.save(R/'outputs/sr015-small-coordinates.png')
