"""Record inspected source roles and compare two local models; no installation."""
import sys,json,hashlib,time
from pathlib import Path
sys.dont_write_bytecode=True
import numpy as np
import torch
from PIL import Image,ImageFilter,ImageDraw,ImageFont
from local_sr import load_model,infer_rgb,roundtrip_metrics
R=Path(__file__).resolve().parents[1]
Q=R/'qa/field_sr001_inference.json'
assert not Q.exists(),'Do not overwrite completed inference.'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def raw(im):return hashlib.sha256(im.convert('RGBA').tobytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),'utf8')
classes={
'illustration_identity_hold':[2],
'text_protected':[32,34,54,89,90],
'flat_geometry':[33,44,50,64,65,66,67,68,69,70,106],
'opaque_material':[36,40,48,49,52,53,55,56,57,61,62,63,83,117,118],
'structured_material':[25,71,72,73,74,75,76,77,78,79,80,81,84,119],
'architecture':[39,41,42,43,58,86],
'atlas_partition_geometry':[51,85,114],
'alpha_geometry':[29,37,38,45,113,120,124],
'thin_alpha':[46,47,87,123],
'alpha_distant_architecture':[59,115,116,121,122],
'alpha_foliage':[60]}
notes={2:'Woman-face poster with lettering; character/protagonist relationship unresolved.',25:'Horizontal slat count and straight frame.',29:'Vehicle mechanical atlas, panel partitions and alpha.',32:'Facade with faded sign and windows; protect lettering.',33:'Flat pump/display blocks; avoid invented texture.',34:'GAS STATION/24H sign; preserve source text.',36:'Wall with lower contrasting horizontal rail.',37:'Building corner; window structure and silhouette.',38:'Facade row and roof silhouettes.',39:'Vertical facade bays and windows.',40:'Wall with narrow base trim.',41:'Facade windows of multiple sizes.',42:'Repeated window rows and door.',43:'Brick facade, window rows and garage doors.',44:'Four paving cells; cross boundary.',45:'Rectilinear post/rail atlas.',46:'Fence uprights and fine rails.',47:'Curved post/arm with small pale rectangles.',48:'Brown paving with pale line on left.',49:'Brown paving and vertical curb boundary.',50:'Four green-gray paving cells.',51:'Road atlas with yellow stripe and paving grids; native UV not verified.',52:'Gray-green paving material.',53:'Right-angle curb and asphalt corner.',54:'STOP road letters and white bar.',55:'Hedge above plinth and brick; horizontal divisions.',56:'Ground with narrow dark green upper strip.',57:'Dark gravel/asphalt-like material.',58:'Ornate paired facade windows and lower openings.',59:'Distant street and tree silhouette.',60:'Sparse foliage; preserve weak alpha branches.',61:'Bright vertical bark/rough trunk-like material; avoid metallic shine.',62:'Rough brick horizontal courses; preserve seams.',63:'Gravel/rough rock; avoid invented deep fractures.',64:'Three vertical framed sections with crossbar.',65:'Double entry door and paired handles.',66:'Barred window; preserve bar count.',67:'Four-pane window.',68:'Four-pane window variant.',69:'Paired tall window/door frames.',70:'Wide short paired window.',71:'Purple wall strips and lower diamond braces.',72:'Two upper recesses and lower vent slots.',73:'Central ladder/recess with paired side boxes.',74:'Three broad vertical ribs.',75:'Large X brace in frame.',76:'Tall stacked panel atlas; source partitions not native UV proof.',77:'Upper-left grille and raised strip.',78:'Stacked ribs and lower round panels/holes.',79:'Double recessed panel.',80:'Tall pipe/groove and vertical seams.',81:'Beige horizontal industrial wall/tubes.',83:'Blue-gray mottled surface; material identity unresolved.',84:'Upper vent and lower large panel; preserve slats.',85:'Facade grid/braces beside road stripe; protect partitions.',86:'Arched-window facade; preserve tracery and count.',87:'Sparse branching cracks/vines; alpha max254.',89:'Vehicle atlas with lettering and checker stripe; protect both.',90:'Vehicle atlas with stripes/windows and possible text.',106:'Framed dark double doors and pale handles.',113:'Building panel and lower X-brace cutout.',114:'Road atlas with multiple markings and paving grids.',115:'Distant low-angle facade around sky.',116:'Street-canyon facades and opening.',117:'Two courses of rectangular stone blocks.',118:'Horizontal stone ledge and shadow.',119:'Green rough framed panel with rails and orange strip.',120:'Post/wall/stripe flat atlas.',121:'Small distant street opening.',122:'Teal-gray skyline and windows.',123:'Two ornate streetlamps with very thin posts.',124:'Fabric/banner silhouette and pointed lower shapes.'}
selected=[36,40,48,49,52,53,55,56,57,61,62,63,*range(71,82),83,84,117,118,119]
ids=[f'FM{n:04d}' for n in selected]
sfile=R/'qa/field_source_review01.json';s=json.loads(sfile.read_text('utf8'))
assert sha(R/s['source_inventory'])==s['source_inventory_sha256']
lookup={f'FM{n:04d}':k for k,ns in classes.items() for n in ns}
assert len(lookup)==72 and set(lookup)=={v['group_id'] for v in s['files']}
for v in s['files']:
 gid=v['group_id'];im=Image.open(v['source']).convert('RGBA')
 assert raw(im)==v['source_rgba_sha256'] and sha(v['source_ptm'])==v['source_ptm_sha256']
 v.update(classification=lookup[gid],source_visual_note=notes[int(gid[2:])],source_review='directly_inspected_by_Codex_internal',selected_for_field_sr001=gid in ids)
for page in s['pages']:
 assert sha(page['path'])==page['sha256'];page['review_status']='directly_inspected_by_Codex_internal'
s['classification_summary']={k:len(ns) for k,ns in classes.items()}
s['selected_for_first_local_comparison']=ids
backup=R/'qa/backups/before-field-source01-classification';backup.mkdir(parents=True,exist_ok=False)
(backup/sfile.name).write_bytes(sfile.read_bytes());save(sfile,s)
rows={v['group_id']:v for v in s['files']};O=R/'workspace/local-sr/field-sr001';O.mkdir(parents=True,exist_ok=False)
models=json.loads((R/'workspace/local-sr/models/models.json').read_text('utf8'))['records']
choices=[('wdn','realesr-general-wdn-x4v3.pth'),('photo','RealESRGAN_x4plus.pth')]
rep={'schema':'brs-field-local-sr/v1','batch':'FIELD-SR-001','source_review':str(sfile),'source_review_sha256':sha(sfile),'unique_originals':len(ids),'actual_local_rgb_inference_passes':0,'external_calls':0,'image_upload':False,'native_neural_scale':4,'final_scale':8,'post_scale':'Lanczos2x','device':torch.cuda.get_device_name(0),'torch':torch.__version__,'files':[],'pages':[],'runtime_verified':False,'release_eligible':False}
for tag,name in choices:
 rec=next(m for m in models if m['name']==name);model=load_model(Path(rec['path']),rec['sha256'])
 for gid in ids:
  st=time.monotonic();v=rows[gid];src=Image.open(v['source']).convert('RGBA');assert src.getchannel('A').getextrema()==(255,255)
  sigma=.25 if v['classification']=='structured_material' else .35
  inp=src.convert('RGB').filter(ImageFilter.GaussianBlur(sigma));ip=O/f'{gid}-{tag}-input.png';inp.save(ip)
  native=infer_rgb(model,inp);npth=O/f'{gid}-{tag}-native4x.png';native.save(npth)
  out=native.resize((src.width*8,src.height*8),Image.Resampling.LANCZOS).convert('RGBA');op=O/f'{gid}-{tag}-8x.png';out.save(op)
  rep['files'].append({**{k:v[k] for k in ['group_id','representative','source','source_ptm','source_ptm_sha256','source_rgba_sha256','classification']},'id':gid+'-'+tag,'model':rec,'input':str(ip),'input_sha256':sha(ip),'input_gaussian_sigma_source_px':sigma,'native':str(npth),'native_sha256':sha(npth),'output':str(op),'output_sha256':sha(op),'output_size':list(out.size),'alpha':'opaque255','actual_local_rgb_inference_passes':1,'source_scale_metrics':roundtrip_metrics(src,out),'seconds':time.monotonic()-st,'visual_review':'pending','runtime_verified':False,'release_eligible':False})
  rep['actual_local_rgb_inference_passes']+=1;save(Q,rep)
 del model;torch.cuda.empty_cache();print(tag,len(ids),'completed',flush=True)
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17);small=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',14)
P=R/'outputs/field-sr001';P.mkdir(exist_ok=False)
for k in range(0,len(ids),2):
 canvas=Image.new('RGB',(1050,760),'#25313c');d=ImageDraw.Draw(canvas);pageids=ids[k:k+2]
 for j,gid in enumerate(pageids):
  v=rows[gid];ims=[Image.open(v['source']).convert('RGBA')]+[Image.open(next(r['output'] for r in rep['files'] if r['id']==gid+'-'+tag)).convert('RGBA') for tag,_ in choices]
  for c,(im,label) in enumerate(zip(ims,['원본 · 단순 확대','로컬 WDN','로컬 Photo'])):
   x=c*350;y=j*380;d.text((x+8,y+8),gid+' '+label,font=font,fill='white');scale=min(320/im.width,320/im.height);size=(round(im.width*scale),round(im.height*scale));im=im.resize(size,Image.Resampling.NEAREST if c==0 else Image.Resampling.LANCZOS);canvas.paste(im.convert('RGB'),(x+(350-size[0])//2,y+38+(320-size[1])//2))
  d.text((8,y+358),v['classification']+' | '+str(v['size']),font=small,fill='#b6c8da')
 p=P/f'review-{k//2+1:02d}.png';canvas.save(p);rep['pages'].append({'path':str(p),'sha256':sha(p),'group_ids':pageids,'review_status':'pending'})
save(Q,rep);print(json.dumps({'originals':len(ids),'passes':rep['actual_local_rgb_inference_passes'],'pages':len(rep['pages'])}))
