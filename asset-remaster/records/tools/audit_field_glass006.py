from pathlib import Path
import json,hashlib
import numpy as np,cv2
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];Q=R/'qa/field_geometry006_source_audit.json';assert not Q.exists();O=R/'workspace/local-sr/field-geometry006';V=R/'outputs/field-geometry006';O.mkdir(exist_ok=False);V.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
prev=json.loads((R/'qa/field_geometry005_review.json').read_text('utf8'));assert sha(R/'qa/field_sr_catalog.json')==prev['catalog_after_sha256'];assert sha(R/'qa/architectural_geometry_contract.json')==prev['geometry_contract_after_sha256'];src=json.loads((R/'qa/field_source_review03.json').read_text('utf8'));v29=json.loads((R/'qa/field_geometry005_trials.json').read_text('utf8'))['files'][0];font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',19);rows=[];pages=[]
for gid in ['FM0029','FM0358','FM0359','FM0364']:
 v=v29 if gid=='FM0029' else next(v for v in src['files'] if v['group_id']==gid);im=Image.open(v['source']).convert('RGBA');s=np.array(im);h,w=s.shape[:2];assert hashlib.sha256(s.tobytes()).hexdigest()==v['source_rgba_sha256'];assert sha(v['source_ptm'])==v['source_ptm_sha256'];colors,counts=np.unique(s.reshape(-1,4),axis=0,return_counts=True);alpha=s[:,:,3];components={}
 for threshold in [1,128,255]:
  c,hier=cv2.findContours(np.pad((alpha>=threshold).astype('uint8'),1),cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE);components[str(threshold)]={'contours':len(c),'enclosed_holes':int(sum(z[3]>=0 for z in hier[0])) if hier is not None else 0}
 scale=8;ww,hh=w*scale,h*scale;can=Image.new('RGB',(ww*2+24,hh+64),'#26333f');dr=ImageDraw.Draw(can)
 for j,bg in enumerate(['#252d35','#d4d5d7']):
  dr.text((j*(ww+12)+4,5),gid+' 원본 · '+('어두운 배경' if j==0 else '밝은 배경'),font=font,fill='white');mat=Image.new('RGBA',(ww,hh),bg);mat.alpha_composite(im.resize((ww,hh),Image.Resampling.NEAREST));can.paste(mat.convert('RGB'),(j*(ww+12)+4,42))
 pp=V/(gid+'-source-dual-matte.png');can.save(pp);pages.append({'path':str(pp),'sha256':sha(pp),'kind':'source_nearest8x_dual_matte','review_status':'pending'})
 # Numbered source coordinate plate for constructing rectilinear faces.
 big=Image.new('RGB',(ww+40,hh+54),'#26333f');dd=ImageDraw.Draw(big);mat=Image.new('RGBA',(ww,hh),'#c0c0c0');mat.alpha_composite(im.resize((ww,hh),Image.Resampling.NEAREST));big.paste(mat.convert('RGB'),(32,30))
 for x in range(0,w,8):dd.text((32+x*8,6),str(x),font=font,fill='white');dd.line((32+x*8,30,32+x*8,30+hh),fill='#3377aa',width=1)
 for y in range(0,h,8):dd.text((0,30+y*8),str(y),font=font,fill='white');dd.line((32,30+y*8,32+ww,30+y*8),fill='#3377aa',width=1)
 pp=V/(gid+'-source-coordinates.png');big.save(pp);pages.append({'path':str(pp),'sha256':sha(pp),'kind':'source_coordinates','review_status':'pending'})
 rows.append({**{k:v[k] for k in ['group_id','source','source_ptm','source_ptm_sha256','source_rgba_sha256']},'size':[w,h],'palette':[{'RGBA':a.tolist(),'pixels':int(n)} for a,n in zip(colors,counts)],'alpha_histogram':{str(int(k)):int(n) for k,n in zip(*np.unique(alpha,return_counts=True))},'alpha_topology':components,'source_note':v.get('source_visual_note','Painted machinery/window/panel atlas, source alpha only in grille.')})
Q.write_text(json.dumps({'schema':'brs-source-broken-glass-audit/v1','previous_goal_turn_classification':'progress: FIELD-GEOMETRY-005 resolved the FM0113 support, made a source-constrained FM0029 glass trial and recorded material-aware direct authoring.','catalog_before_sha256':sha(R/'qa/field_sr_catalog.json'),'geometry_contract_before_sha256':sha(R/'qa/architectural_geometry_contract.json'),'files':rows,'pages':pages,'new_inference_calls':0,'runtime_verified':False},ensure_ascii=False,indent=2),'utf8');print(json.dumps([{k:v[k] for k in ['group_id','size','alpha_histogram','alpha_topology']} for v in rows]))
