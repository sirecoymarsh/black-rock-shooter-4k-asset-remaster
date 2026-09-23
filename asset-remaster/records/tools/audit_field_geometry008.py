from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];Q=R/'qa/field_geometry008_source_audit.json';assert not Q.exists();P=R/'outputs/field-geometry008';P.mkdir(exist_ok=True);O=R/'workspace/local-sr/field-geometry008';O.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
d=json.loads((R/'qa/field_source_review04.json').read_text('utf8'));ids=['FM0394','FM0430','FM0444','FM0489','FM0498','FM0496'];files=[];pages=[];font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18)
for gid in ids:
 v=next(z for z in d['files'] if z['group_id']==gid);im=Image.open(v['source']).convert('RGBA');assert hashlib.sha256(im.tobytes()).hexdigest()==v['source_rgba_sha256'];assert sha(v['source_ptm'])==v['source_ptm_sha256'];files.append(v)
 scale=512/max(im.size);pic=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST);can=Image.new('RGB',(552,570),'#25313c');dr=ImageDraw.Draw(can);dr.text((18,8),gid+' 원본 · 단순 확대',font=font,fill='white');bg=Image.new('RGB',pic.size,'#414951');bg.paste(pic,(0,0),pic);can.paste(bg,((552-pic.width)//2,44));pp=P/f'{gid}-source.png';can.save(pp);pages.append({'path':str(pp),'sha256':sha(pp),'group_id':gid,'review_status':'pending'})
 if gid=='FM0489':
  a=np.array(im);print('489 totalRGBA',np.unique(a.reshape(-1,4),axis=0,return_counts=True));print('489 cells',[[np.unique(a[y:y+8,x:x+8].reshape(-1,4),axis=0).tolist() for x in range(0,32,8)] for y in range(0,32,8)])
 if gid=='FM0498':
  a=np.array(im);print('498 means',[(x,y,a[y:y+64,x:x+64,:3].mean((0,1)).tolist()) for y in [0,64] for x in [0,64]])
q={'schema':'brs-geometry008-source-audit/v1','previous_goal_turn_classification':'progress: geometry007 source geometry/material repaired495/533 with6 derivatives, two holds resolved and source interpretation limitations recorded.','files':files,'pages':pages,'catalog_before_sha256':sha(R/'qa/field_sr_catalog.json'),'geometry_contract_before_sha256':sha(R/'qa/architectural_geometry_contract.json'),'checker_contract_sha256':sha(R/'qa/checker_design_contract.json'),'runtime_verified':False,'release_eligible':False};Q.write_text(json.dumps(q,ensure_ascii=False,indent=2),'utf8')
