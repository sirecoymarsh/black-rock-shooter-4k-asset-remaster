from pathlib import Path
import sys,json,hashlib
sys.dont_write_bytecode=True
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(r'P:\AI\Codex\projects\black-rock-shooter-hd-ui-fonts');P=R/'outputs/field-foliage007';O=R/'workspace/local-sr/field-foliage007';Q=R/'qa/field_foliage007_source_audit.json';assert not Q.exists();P.mkdir(exist_ok=True);O.mkdir(exist_ok=True)
def read(p):return json.loads(Path(p).read_text('utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
local=read(R/'qa/field_foliage006_local.json');prev=read(R/'qa/field_foliage006_review.json');assert sha(R/'qa/field_sr_catalog.json')==prev['catalog_after_sha256'];assert sha(R/'qa/architectural_geometry_contract.json')==prev['geometry_contract_after_sha256'];preps={p['group_id']:p for p in local['prepared_sources']};gids=['FM0314','FM0316','FM0317','FM0325'];font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',16)
rep={'schema':'brs-field-foliage007-source-audit/v1','previous_goal_turn_classification':'progress: foliage006 reviewed9 new originals and selected source-density weed290; tree314 still held with specified source-geometry next action','catalog_before_sha256':sha(R/'qa/field_sr_catalog.json'),'geometry_contract_before_sha256':sha(R/'qa/architectural_geometry_contract.json'),'files':[],'pages':[],'source_relationships':[],'new_local_passes':0,'new_external_calls':0}
arrays={}
for gid in gids:
 p=preps[gid];s=Image.open(p['source']).convert('RGBA');a=np.asarray(s);arrays[gid]=a;assert hashlib.sha256(a.tobytes()).hexdigest()==p['source_rgba_sha256'] and sha(p['source_ptm'])==p['source_ptm_sha256'];rep['files'].append({k:p[k] for k in ['group_id','source','source_ptm','source_ptm_sha256','source_rgba_sha256']})
 im=s.resize((1024,1024),Image.Resampling.NEAREST);bg=Image.new('RGBA',im.size,'#18222c');bg.alpha_composite(im);pp=P/(gid+'-source-full.png');bg.convert('RGB').save(pp);rep['pages'].append({'path':str(pp),'sha256':sha(pp),'group_id':gid,'kind':'source-full','review_status':'pending'})
 if gid!='FM0314':continue
 for tag,box in [('lower',(0,64,128,128)),('left',(0,72,64,128)),('right',(64,72,128,128))]:
  x0,y0,x1,y1=box;scale=8 if tag=='lower' else 12;can=Image.new('RGB',((x1-x0)*scale+60,(y1-y0)*scale+50),'#25313c');pic=s.crop(box).resize(((x1-x0)*scale,(y1-y0)*scale),Image.Resampling.NEAREST);bg=Image.new('RGBA',pic.size,'#18222c');bg.alpha_composite(pic);can.paste(bg.convert('RGB'),(50,40));d=ImageDraw.Draw(can)
  for x in range(x0,x1+1,4):
   px=50+(x-x0)*scale;d.line((px,40,px,can.height-10),fill='#50606c' if x%8==0 else '#35444f',width=1);d.text((px-9,12),str(x),font=font,fill='white')
  for y in range(y0,y1+1,4):
   py=40+(y-y0)*scale;d.line((50,py,can.width-10,py),fill='#50606c' if y%8==0 else '#35444f',width=1);d.text((8,py-8),str(y),font=font,fill='white')
  pp=P/(gid+'-source-coordinate-'+tag+'.png');can.save(pp);rep['pages'].append({'path':str(pp),'sha256':sha(pp),'group_id':gid,'kind':'coordinate-'+tag,'source_box':box,'review_status':'pending'})
base=arrays['FM0314']
for gid in ['FM0316','FM0317','FM0325']:
 a=arrays[gid];common=(base[:,:,3]>0)&(a[:,:,3]>0);delta=a[:,:,:3].astype(int)-base[:,:,:3];same=np.all(delta==0,2);gray0=base[:,:,:3].mean(2);gray1=a[:,:,:3].mean(2);pairs=np.column_stack([gray0[common],gray1[common]]);A=np.column_stack([pairs[:,0],np.ones(len(pairs))]);coeff=np.linalg.lstsq(A,pairs[:,1],rcond=None)[0];res=pairs[:,1]-A@coeff
 rep['source_relationships'].append({'base':'FM0314','other':gid,'common_opaque_source_pixels':int(common.sum()),'equal_RGB_fraction_common_opaque':float(same[common].mean()),'whole_RGB_equal_fraction':float(same.mean()),'gray_affine_coefficients':coeff.tolist(),'gray_affine_residual_RMS':float(np.sqrt(np.mean(res*res))),'limit':'Pixel/color relationship only; does not prove same in-game consumer or permit automatic geometry reuse.'})
write=lambda p,v:Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2),'utf8');write(Q,rep);print(json.dumps({'pages':len(rep['pages']),'relationships':rep['source_relationships']}))
