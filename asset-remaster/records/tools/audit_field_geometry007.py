from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];Q=R/'qa/field_geometry007_source_audit.json';assert not Q.exists();P=R/'outputs/field-geometry007';P.mkdir(exist_ok=True);O=R/'workspace/local-sr/field-geometry007';O.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
src=json.loads((R/'qa/field_source_review04.json').read_text('utf8'));files=[];pages=[];font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',12)
for gid,box in [('FM0495',(0,0,64,64)),('FM0496',(0,0,256,128)),('FM0533',(0,104,32,128))]:
 v=next(z for z in src['files'] if z['group_id']==gid);im=Image.open(v['source']).convert('RGBA');a=np.array(im);assert hashlib.sha256(im.tobytes()).hexdigest()==v['source_rgba_sha256'];assert sha(v['source_ptm'])==v['source_ptm_sha256'];files.append(v)
 step=12 if gid=='FM0495' else 4 if gid=='FM0496' else 24;pic=im.crop(box).resize(((box[2]-box[0])*step,(box[3]-box[1])*step),Image.Resampling.NEAREST);can=Image.new('RGB',(pic.width+44,pic.height+44),'#25313c');can.paste(pic,(36,36));d=ImageDraw.Draw(can);stride=4 if gid=='FM0495' else 8 if gid=='FM0496' else 1
 for x in range(box[0],box[2],stride):d.text((36+(x-box[0])*step,16),str(x),font=font,fill='white');d.line((36+(x-box[0])*step,36,36+(x-box[0])*step,36+pic.height),fill='#6d747a',width=1)
 for y in range(box[1],box[3],stride):d.text((3,36+(y-box[1])*step),str(y),font=font,fill='white');d.line((36,36+(y-box[1])*step,36+pic.width,36+(y-box[1])*step),fill='#6d747a',width=1)
 path=P/f'{gid}-source-coordinate.png';can.save(path);pages.append({'path':str(path),'sha256':sha(path),'group_id':gid,'box':box,'review_status':'pending'})
 if gid=='FM0533':
  print('533 lower grayscale/color indices');colors=sorted(im.getcolors(999999),key=lambda z:z[1]);print(colors)
 if gid=='FM0495':
  gray=a[:,:,:3].mean(2);print('495 darkest y within course neighborhoods per x=8,24,40,56')
  for lo,hi in [(0,7),(7,15),(15,25),(25,35),(35,44),(44,53),(53,62)]:print(lo,hi,[(x,int(lo+np.argmin(gray[lo:hi,x]))) for x in [8,24,40,56]])
report={'schema':'brs-geometry007-source-audit/v1','previous_goal_turn_classification':'progress: SR005 completed135 source classifications,20 local originals,7 static candidates and13 holds with42 real local passes.','files':files,'pages':pages,'catalog_before_sha256':sha(R/'qa/field_sr_catalog.json'),'geometry_contract_before_sha256':sha(R/'qa/architectural_geometry_contract.json'),'runtime_verified':False,'release_eligible':False};Q.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8');print('3 sources audited.')
