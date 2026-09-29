"""Independent persisted-pixel, source binding, protected-geometry and SDO QA."""
from pathlib import Path
import sys,json,hashlib,configparser,ast
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];W=R/'workspace/ui-remaining-ko-001';O=R/'outputs/ui-remaining-ko-001';S=8
sys.stdout.reconfigure(encoding='utf8')
def read(p):return json.loads(p.read_text('utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sb(b):return tuple(int(v*S) for v in b)
m=read(W/'manifest.json');inv=read(R/'qa/ui_inventory_expanded.json');assets={};checks=[]
# This reviewer uses affine UV sampling, not the builder's box/rotation path.
tree=ast.parse((R/'tools/review_title_ko_002.py').read_text('utf8'))
fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='compose')
exec(compile(ast.Module(body=[fn],type_ignores=[]),'<independent affine SDO sampler>','exec'))
for r in m['records']:
 images={}
 for role,f in r['files'].items():
  p=Path(f['path']);assert sha(p)==f['sha256'];images[role]=Image.open(p).copy()
 original=np.array(images['before']);final=np.array(images['candidate']);mask=np.array(images['mask'])>0
 assert np.array_equal(original[~mask],final[~mask]),r['id']
 merged=images['clean'].copy();merged.alpha_composite(images['layer']);assert merged.tobytes()==images['candidate'].tobytes()
 logical_h=r['logical_size'][1]*S;assert np.array_equal(original[logical_h:],final[logical_h:])
 assert sha(W/'pack/PSP/TEXTURES/NPUH10126'/r['replacement'])==r['output_sha256']
 assert sha(Path(r['binding']['parent']))==r['binding']['parent_sha256']
 for label in r['labels']:
  if label.get('color_mask'):
   a=np.array(images['clean'].crop(sb(label['box'])));rgb=a[:,:,:3].astype(int);assert not ((rgb.max(2)-rgb.min(2)>30)&(a[:,:,3]>0)).any()
  elif label.get('blue_plate'):
   a=np.array(images['clean'].crop(sb(label['box'])));assert (a[:,:,0]==34).all()
  else:
   a=np.array(images['clean'].crop(sb(label['box'])));expected=label.get('clean',[255,255,255,0]);assert (a==expected).all(),(r['id'],label['source'])
 images['size']=[images['candidate'].width//S,images['candidate'].height//S];assets[r['id']]=images
 checks.append({'asset':r['id'],'outside_ownership_rgba':'exact','padding':'exact','clean_plus_layer':'exact','bindings':len(r['binding']['keys']),'observed_bindings':len(r['binding']['observed'])})

protected={'MUI-01':[[0,0,91,46],[96,46,103,51],[117,0,128,13]],'RUI-007':[[0,0,20,152]],
 'RUI-008':[[0,0,64,10],[0,17,64,32]],'RUI-009':[[0,0,128,37],[39,37,77,38],[85,37,128,56]],
 'MUI-28':[[0,0,44,48]],'BUI-002':[[88,0,128,17],[67,28,78,38]],'BUI-003':[[0,0,24,11],[30,0,32,11],[0,17,9,22]]}
for aid,boxes in protected.items():
 for box in boxes:
  a=assets[aid];assert a['source'].crop(sb(box)).tobytes()==a['candidate'].crop(sb(box)).tobytes(),(aid,box)
  checks.append({'asset':aid,'protected_box':box,'rgba_exact':True})

def sdo(ident):return next(c for c in inv['containers'] if c['id']==ident)['sdo']['records']
families=[
 ('도전 과제 제목','if::menu::if_rec_info.gz::001',{5:'MUI-27',6:'MUI-28'},[53,54,55,56,57,58,59,105,106,107,108]),
 ('전투 결과 제목','system.vol::007_if_btlsys.lpk::006::000',{1:'BUI-002'},[37,38,39,40]),
 ('레벨 상승','system.vol::007_if_btlsys.lpk::006::000',{1:'BUI-002'},[8,9,6]),
 ('획득 아이템','system.vol::007_if_btlsys.lpk::006::000',{0:'BUI-001'},[21]),
 ('도전 과제 메뉴','system.vol::005_if_rsdsys.lpk::019::000',{5:'RUI-010'},[58,61,62,66]),
 ('도전 과제 해금','system.vol::005_if_rsdsys.lpk::021::000',{1:'RUI-012'},[16,30]),
 ('도전 과제 완료','system.vol::005_if_rsdsys.lpk::021::000',{1:'RUI-012'},[31,32]),
]
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18);pages=[]
for n,(title,sid,slots,ids) in enumerate(families):
 records=[sdo(sid)[i] for i in ids]
 xy=[(r['layout_xywh'][0]+min(v[2] for v in r['vertices']),r['layout_xywh'][1]+min(v[3] for v in r['vertices'])) for r in records]
 left=min(x for x,y in xy);top=min(y for x,y in xy)
 right=max(x+r['layout_xywh'][2] for (x,y),r in zip(xy,records));bottom=max(y+r['layout_xywh'][3] for (x,y),r in zip(xy,records))
 images=[]
 for role in ['source','candidate']:
  canvas=Image.new('RGBA',(int((right-left)*S),int((bottom-top)*S)),(255,255,255,0))
  for (x,y),rec in zip(xy,records):
   a=assets[slots[rec['texture_slot']]];tile=compose(a[role],rec,a['size']);canvas.alpha_composite(tile,(int((x-left)*S),int((y-top)*S)))
  images.append(canvas)
 if title=='도전 과제 제목':
  # Repeated L/E and removed N/G/S consumers must be empty, not Korean fragments.
  for i in [57,58,59,105,106,107,108]:
   rec=sdo(sid)[i];a=assets[slots[rec['texture_slot']]];assert not compose(a['candidate'],rec,a['size']).getchannel('A').getbbox(),i
  checks.append({'family':title,'repeated_letter_aliases_empty':True,'sdo_unchanged':True})
 if title=='전투 결과 제목':
  rec=sdo(sid)[39];assert not compose(assets['BUI-002']['candidate'],rec,[128,64]).getchannel('A').getbbox()
  checks.append({'family':title,'plural_S_alias_empty':True})
 factor=min(1,1000/images[0].width);size=(round(images[0].width*factor),round(images[0].height*factor))
 out=Image.new('RGB',(size[0]+24,size[1]*2+85),'#344659');d=ImageDraw.Draw(out)
 d.text((8,2),title+' · 소비자 정적 조립 / 실제 게임 캡처 아님',font=font,fill='white')
 for j,im in enumerate(images):out.paste(im.resize(size),(8,35+j*(size[1]+30)),im.resize(size))
 path=O/f'consumer-{n+1}.png';out.save(path);pages.append({'path':str(path),'sha256':sha(path)})
report={'schema':'brs-remaining-ko-review/v1','manifest_sha256':sha(W/'manifest.json'),'static_status':'PASS','checks':checks,'consumer_proofs':pages,'visual_status':'pending direct inspection','runtime_verified':False,'live_installation_performed':False}
(R/'qa/ui_remaining_ko_001_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
print(json.dumps({'static':'PASS','checks':len(checks),'consumer_proofs':len(pages)}))
