from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];Q=R/'qa/field_sr005_native_review.json';assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
rep=json.loads((R/'qa/field_sr005_inference.json').read_text('utf8'));rows={v['id']:v for v in rep['files']}
boxes={391:[12,42,52,82],396:[12,20,52,60],407:[50,16,90,56],424:[16,0,48,32],456:[12,12,52,52],465:[12,12,52,52],466:[12,12,52,52],473:[0,0,32,32],476:[44,40,84,80],480:[12,12,52,52],486:[12,12,52,52],494:[12,12,52,52],495:[12,12,52,52],496:[44,12,84,52],499:[44,44,84,84],502:[44,0,76,32],506:[12,12,52,52],518:[8,72,48,112],525:[40,40,80,80],533:[0,96,32,128]}
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17);pages=[];ids=rep['group_ids']
for k in range(0,len(ids),2):
 can=Image.new('RGB',(1050,760),'#25313c');d=ImageDraw.Draw(can)
 for j,gid in enumerate(ids[k:k+2]):
  v=rows[gid+'-wdn'];box=boxes[int(gid[2:])];outbox=tuple(n*8 for n in box)
  src=Image.open(v['source']).convert('RGBA').crop(box);ims=[src.resize((src.width*8,src.height*8),Image.Resampling.NEAREST)]+[Image.open(rows[gid+'-'+t]['output']).convert('RGBA').crop(outbox) for t in ['wdn','photo']]
  for c,(im,label) in enumerate(zip(ims,['원본 · 단순 확대','로컬 WDN · 출력 원크기','로컬 Photo · 출력 원크기'])):
   x=c*350;y=j*380;d.text((x+8,y+8),gid+' '+label,font=font,fill='white');d.text((x+8,y+33),str(box),font=font,fill='#bac7d3');mat=Image.new('RGB',im.size,'#444950');mat.paste(im,(0,0),im);can.paste(mat,(x+(350-im.width)//2,y+58))
 path=R/f'outputs/field-sr005/native-{k//2+1:02d}.png';can.save(path);pages.append({'path':str(path),'sha256':sha(path),'group_ids':ids[k:k+2],'source_boxes':{g:boxes[int(g[2:])] for g in ids[k:k+2]},'output_display_scale':1,'review_status':'pending_final_review'})
Q.write_text(json.dumps({'schema':'brs-field-native-comparison/v1','inference_report_sha256':sha(R/'qa/field_sr005_inference.json'),'pages':pages},indent=2,ensure_ascii=False),'utf8');print('Native comparison pages:',len(pages))
