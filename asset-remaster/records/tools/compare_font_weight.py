import sys,json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageFont,ImageDraw
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
R=Path(__file__).resolve().parents[1]
from brs_font_pipeline import parse_font_layout,cell_bytes,decoded_cell_image
s=R/'workspace/source/font';l,p=parse_font_layout((s/'font.lpk').read_bytes());rows=json.loads((s/'glyph_alias_map.json').read_text(encoding='utf-8'))['aliases'];f=ImageFont.truetype(r'C:\Windows\Fonts\NotoSansKR-VF.ttf',112)
weights=[100,300,310,315,320,325,330,350];results=[];rasters={}
for weight in weights:
 f.set_variation_by_axes([weight]);oldsum=newsum=0;err=[];clipped=[]
 for row in rows:
  char=row['character'];a=Image.new('L',(152,152));ImageDraw.Draw(a).text((24,8),char,font=f,fill=255);crop=a.crop((16,16,136,136));outside=np.array(a);outside[16:136,16:136]=0
  if outside.any():clipped.append(char)
  old=np.array(decoded_cell_image(cell_bytes(p,l,row['font_index']),l.palette_rgba).getchannel('A')).astype(float);new=np.array(crop.resize((15,15),Image.Resampling.BOX)).astype(float)
  oldsum+=old.sum();newsum+=new.sum();err.append(abs(new-old).mean());rasters[weight,char]=crop
 results.append({'weight':weight,'glyph_count':len(rows),'integrated_alpha_ratio_to_native':newsum/oldsum,'native_downsample_mae':float(np.mean(err)),'clipped':clipped})
print(json.dumps(results,ensure_ascii=False))
(R/'qa/font_weight_comparison.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
samples='읽값밖꽃뿔쐐괜왜뛰'.strip();samples=''.join(c for c in samples if (100,c) in rasters)
# Use glyphs from the actual repertoire only; captions describe comparison and do not change game wording.
if len(samples)<8:samples+=''.join(row['character'] for row in rows[:8-len(samples)])
cols=len(samples);sheet=Image.new('RGB',(210+cols*128,6*150),'#172237');d=ImageDraw.Draw(sheet);label=ImageFont.truetype(r'C:\Windows\Fonts\malgun.ttf',24)
for y,weight in enumerate(['native',100,300,315,320,330]):
 d.text((12,y*150+45),'원본 확대' if weight=='native' else f'굵기 {weight}',font=label,fill='white')
 for x,c in enumerate(samples):
  if weight=='native':row=next(r for r in rows if r['character']==c);a=decoded_cell_image(cell_bytes(p,l,row['font_index']),l.palette_rgba).getchannel('A').resize((120,120),Image.Resampling.NEAREST)
  else:a=rasters[weight,c]
  im=Image.new('RGBA',a.size,'white');im.putalpha(a);sheet.paste(im,(210+x*128,y*150+15),im)
sheet.save(R/'outputs/font_weight_comparison.png')