from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];Q=R/'qa/field_sr005_alpha_review.json';assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
b=json.loads((R/'qa/field_sr005_inference.json').read_text('utf8'));rows={v['id']:v for v in b['files']};font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17);pages=[]
for gid in ['FM0480','FM0494','FM0506']:
 v=rows[gid+'-wdn'];ims=[Image.open(v['source']).convert('RGBA')]+[Image.open(rows[gid+'-'+t]['output']).convert('RGBA') for t in ['wdn','photo']];can=Image.new('RGB',(900,630),'#25313c');d=ImageDraw.Draw(can)
 for r,matte in enumerate(['#202830','#dedede']):
  for c,(im,title) in enumerate(zip(ims,['원본 · 단순 확대','로컬 WDN','로컬 Photo'])):
   pic=im.resize((256,256),Image.Resampling.NEAREST if c==0 else Image.Resampling.LANCZOS);mat=Image.new('RGB',pic.size,matte);mat.paste(pic,(0,0),pic);d.text((c*300+8,r*315+8),gid+' '+title,font=font,fill='white');can.paste(mat,(c*300+20,r*315+43))
 pp=R/f'outputs/field-sr005/{gid}-dual-matte.png';can.save(pp);pages.append({'path':str(pp),'sha256':sha(pp),'group_id':gid,'review_status':'pending_final_review','mattes':['#202830','#dedede']})
Q.write_text(json.dumps({'schema':'brs-nearopaque-matte-review/v1','inference_report_sha256':sha(R/'qa/field_sr005_inference.json'),'pages':pages},ensure_ascii=False,indent=2),'utf8');print('3 dual-matte comparisons saved.')
