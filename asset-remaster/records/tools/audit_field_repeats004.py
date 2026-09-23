import json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];Q=R/'qa/field_geometry004_source_audit.json';assert not Q.exists()
O=R/'outputs/field-geometry004';O.mkdir(exist_ok=False);W=R/'workspace/local-sr/field-geometry004';W.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
base=json.loads((R/'qa/field_sr004_inference.json').read_text('utf8'));files=[];pages=[];font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',13)
for gid in ['FM0337','FM0346','FM0347']:
 v=next(v for v in base['files'] if v['id']==gid+'-wdn');im=Image.open(v['source']).convert('RGBA');s=np.asarray(im);factor=8 if im.width==128 else 16
 canvas=Image.new('RGB',(im.width*factor+56,im.height*factor+52),'#25323e');d=ImageDraw.Draw(canvas);canvas.paste(im.resize((im.width*factor,im.height*factor),Image.Resampling.NEAREST).convert('RGB'),(40,32));d.text((4,3),gid+' SOURCE pixel coordinates',font=font,fill='white')
 for x in range(0,im.width,4):d.text((40+x*factor,17),str(x),font=font,fill='white')
 for y in range(0,im.height,2):d.text((8,32+y*factor),str(y),font=font,fill='white')
 p=O/(gid+'-source-coordinates.png');canvas.save(p);pages.append({'path':str(p),'sha256':sha(p),'group_id':gid,'review_status':'pending'})
 row={k:v[k] for k in ['group_id','source','source_ptm','source_ptm_sha256','source_rgba_sha256']}
 row.update(source_size=list(im.size),source_row_mean_rgb=s[:,:,:3].mean(1).tolist())
 if gid=='FM0337':
  row.update(bright_vertical_source_spans=[[0,6],[13,19],[25,31],[38,44],[51,57],[65,71],[78,84],[92,98],[105,111],[118,124]],repeated_upright_y=[4,46],horizontal_bands_y=[[0,4],[46,47],[47,50],[50,59],[59,62],[62,64]],left_strip_x=[0,9],interpretation='Ten bright vertical source spans, first clipped at left texture edge. Not ten independently confirmed 3D posts. Left strip x0..8 continues down past horizontal lower bands; physical consumer unknown.')
 elif gid=='FM0346':row.update(repeat_source_period=6,bright_vertical_spans=[[0,2],[6,8],[12,14],[18,20],[24,26],[30,32]],repeat_y=[16,32],horizontal_lintel_y=[0,16],interpretation='Six bright two-pixel bands at period6, first/last clipped by texture boundaries. Intervening four-pixel shaded faces are pale, not black holes; this is a repeat profile, not six proven physical columns.')
 else:row.update(horizontal_molding_rows=[0,1,15,16,31],upper_vertical_rows=[2,15],upper_vertical_columns=[0,31,63],lower_ornament_box=[0,17,64,31],interpretation='Four X-shaped waists across the lower row near x8.5/23.5/38.5/53.5. Source transitions need traced curves; prior oval terminology is descriptive, not established complete ellipses. Preserve opening/closing positions and upper straight molds.')
 files.append(row)
Q.write_text(json.dumps({'schema':'brs-source-repeat-audit/v1','previous_goal_turn_classification':'progress: FIELD-SR-004 classified72 and selected14/30 local originals with source-plane corrections.','catalog_before_sha256':sha(R/'qa/field_sr_catalog.json'),'geometry_contract_before_sha256':sha(R/'qa/architectural_geometry_contract.json'),'files':files,'pages':pages,'new_neural_passes':0,'runtime_verified':False,'release_eligible':False},ensure_ascii=False,indent=2),'utf8')
print('Prepared source-coordinate boards for3 held groups.')
