"""Freeze a bounded architectural geometry audit from current source/candidate state."""
import json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];Q=R/'qa/field_geometry001_sources.json';assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads((R/p).read_text('utf8'))
cat=read('qa/field_sr_catalog.json');groups={g['group_id']:g for g in cat['groups']};source={g['group_id']:g for k in [1,2] for g in read(f'qa/field_source_review{k:02d}.json')['files']};trial=read('qa/field_sr003_inference.json')
ids=['FM0029','FM0113','FM0037','FM0038','FM0189','FM0190','FM0257','FM0258'];P=R/'outputs/field-geometry001';P.mkdir(exist_ok=False);font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17);files=[];pages=[]
for gid in ids:
 v=source[gid];g=groups[gid];s=Image.open(v['source']).convert('RGBA');assert hashlib.sha256(s.tobytes()).hexdigest()==v['source_rgba_sha256'];assert sha(v['source_ptm'])==v['source_ptm_sha256']
 if g['candidate']:parent=g['candidate']['path'];ph=g['candidate']['sha256'];pid=g['candidate']['id']
 else:
  b=next(r for r in trial['files'] if r['group_id']==gid and r['model_id']==('photo' if gid in ['FM0037','FM0038'] else 'wdn'));parent=b['output'];ph=b['output_sha256'];pid=b['id']
 assert sha(parent)==ph;p=Image.open(parent).convert('RGBA');assert p.size==(s.width*8,s.height*8)
 entry={**{k:v[k] for k in ['group_id','source','source_ptm','source_ptm_sha256','source_rgba_sha256','classification','source_visual_note']},'size':list(s.size),'parent':parent,'parent_sha256':ph,'parent_id':pid,'catalog_status_before':g['status'],'candidate_before':g['candidate']};files.append(entry)
 wh=p.size;cw=wh[0]+24;canvas=Image.new('RGB',(cw*2,wh[1]+50),'#26333f');d=ImageDraw.Draw(canvas)
 for j,(im,title) in enumerate([(s.resize(wh,Image.Resampling.NEAREST),'원본 · 단순 확대'),(p,'기존 로컬 후보')]):
  x=j*cw;d.text((x+8,7),gid+' '+title,font=font,fill='white');bg=Image.new('RGB',wh,'#a8adb2');bg.paste(im,(0,0),im);canvas.paste(bg,(x+8,38))
 path=P/f'audit-{gid}.png';canvas.save(path);pages.append({'group_id':gid,'path':str(path),'sha256':sha(path),'review_status':'pending'})
 if gid in ['FM0029','FM0113']:
  box=(30,0,57,23) if gid=='FM0029' else (0,0,18,32);scale=22;crop=s.crop(box).resize(((box[2]-box[0])*scale,(box[3]-box[1])*scale),Image.Resampling.NEAREST);out=Image.new('RGB',(crop.width+50,crop.height+50),'#a8adb2');out.paste(crop,(40,40),crop);d=ImageDraw.Draw(out)
  for x in range(box[0],box[2]):
   xx=40+(x-box[0])*scale;d.line((xx,40,xx,40+crop.height),fill='#777777');d.text((xx,3),str(x),font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',11),fill='black')
  for y in range(box[1],box[3]):
   yy=40+(y-box[1])*scale;d.line((40,yy,40+crop.width,yy),fill='#777777');d.text((3,yy),str(y),font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',13),fill='black')
  pp=P/f'source-coordinates-{gid}.png';out.save(pp);pages.append({'group_id':gid,'path':str(pp),'sha256':sha(pp),'source_box':list(box),'review_status':'pending','diagnostic':'Coordinate overlay only, not a game asset.'})
rep={'schema':'brs-field-geometry-source-audit/v1','previous_goal_turn_classification':'progress: FIELD-SR-00327 originals,102local passes,12 static candidates,15 holds; straight-line geometry contract recorded.','catalog_sha256_before':sha(R/'qa/field_sr_catalog.json'),'geometry_contract_sha256_before':sha(R/'qa/architectural_geometry_contract.json'),'files':files,'pages':pages,'new_neural_passes':0,'runtime_verified':False,'release_eligible':False};Q.write_text(json.dumps(rep,ensure_ascii=False,indent=2),'utf8');print(json.dumps({'sources':len(files),'pages':len(pages),'report':str(Q)}))
