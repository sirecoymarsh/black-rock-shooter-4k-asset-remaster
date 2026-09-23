"""Fixed-ISO inventory of IF, resident UI, title and memory-card containers."""
import sys,json,gzip,zlib,hashlib,struct,collections,ast,math
from pathlib import Path
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf8')
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];A=Path(r'P:\AI\Codex\work_archive\2026-07-25\new-chat-2\work')
sys.path.insert(0,str(A/'patch_pipeline'));from brs_patch import Iso9660,Rtdp,Lpk
from ptmd_expanded import decode
# Load just the existing pure parser definition; importing its script would
# overwrite the original 10-container report. Its exact source hash is recorded.
source=(R/'tools/extract_ui_consumers.py').read_text('utf8');tree=ast.parse(source)
pure=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='parse_sdo')
exec(compile(ast.Module(body=[pure],type_ignores=[]),'<verified parse_sdo>','exec'))
def sha(b):return hashlib.sha256(b).hexdigest()
iso_path=A/'release_build/runtime_fix_iso_20260823_test_v2/BRS_Korean_v1.0.iso'
identity=json.loads((R/'qa/source_identity.json').read_text('utf8'))
with iso_path.open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==identity['iso']['sha256']
root=R/'workspace/source/ui_expanded';root.mkdir(parents=True,exist_ok=True)
textures=[];containers=[];unresolved=[];other=collections.Counter();iso_rows=[]
legacy=json.loads((R/'qa/ui_source_audit.json').read_text('utf8'))['assets'];old_ids=collections.defaultdict(list)
for a in legacy:old_ids[a['iso_ptmd_sha256']].append(a['id'])
known=[b'LPK\0',b'PTMD',b'SDOa',b'RTDP',b'CZAA',b'\x1f\x8b',b'\x89PNG']
def recognized(b):return any(b.startswith(k) for k in known)

def visit(raw,rel,origin,depth=0):
 assert depth<10
 transforms=[];data=raw
 if data[:2]==b'\x1f\x8b':data=gzip.decompress(data);transforms.append('gzip')
 if data[:4]==b'CZAA':
  expected=struct.unpack_from('<I',data,4)[0];data=zlib.decompress(data[16:]);assert len(data)==expected;transforms.append('CZAA +16 / zlib')
 path=root/rel;rec={'id':rel.replace('/','::'),'relative':rel,'origin':origin,'source_sha256':sha(raw),'decoded_sha256':sha(data),'size':len(data),'transforms':transforms,'magic':data[:4].hex()}
 if data[:4]==b'LPK\0':
  path.mkdir(parents=True,exist_ok=True);(path/'container.lpk').write_bytes(data);lpk=Lpk(data);rec['member_count']=len(lpk.items);containers.append(rec)
  for it in lpk.items:visit(lpk.payload(it),rel+f'/{it.index:03d}',{'container':rec['id'],'index':it.index,'offset':it.offset},depth+1)
 elif data[:4]==b'RTDP':
  path.mkdir(parents=True,exist_ok=True);(path/'container.vol').write_bytes(data);vol=Rtdp(data);rec['member_count']=len(vol.items);containers.append(rec)
  for it in vol.items:
   b=vol.payload(it);plain=bytes(x^0x55 for x in b)
   if recognized(b):child=b;xor=False
   elif recognized(plain):child=plain;xor=True
   else:other['RTDP-unclassified:'+plain[:4].hex()]+=1;unresolved.append({'container':rec['id'],'index':it.index,'name':it.name,'size':len(b),'classification':'Non-UI binary or unparsed embedded container; not excluded from whole-game scope'});continue
   visit(child,rel+f'/{it.index:03d}_'+it.name,{'container':rec['id'],'index':it.index,'name':it.name,'xor55':xor,'encoded_sha256':sha(b)},depth+1)
 elif data[:4]==b'PTMD':
  path.parent.mkdir(parents=True,exist_ok=True);ptm=Path(str(path)+'.ptm');ptm.write_bytes(data);rec['source']=str(ptm);rec['prior_ui_ids']=old_ids.get(sha(data),[]);rec['status']='unresolved';rec['runtime_matches']=[];rec['consumer_status']='unverified'
  try:
   im,details=decode(data);dest=ptm.with_suffix('.png');im.save(dest);a=np.array(im.getchannel('A'));rec.update(details,width=im.width,height=im.height,padded_width=1<<(im.width-1).bit_length(),padded_height=1<<(im.height-1).bit_length(),rgba_sha256=sha(im.tobytes()),png=str(dest),alpha_min=int(a.min()),alpha_max=int(a.max()),status='decoded; visible-surface review pending')
  except (ValueError,AssertionError) as exc:rec['error']=str(exc)
  textures.append(rec)
 elif data[:4]==b'SDOa':
  path.parent.mkdir(parents=True,exist_ok=True);p=Path(str(path)+'.sdo');p.write_bytes(data);rec['source']=str(p)
  try:rec['sdo']=parse_sdo(data)
  except (ValueError,AssertionError,StopIteration) as exc:rec['error']=str(exc)
  containers.append(rec)
 elif data.startswith(b'\x89PNG'):
  path.parent.mkdir(parents=True,exist_ok=True);p=Path(str(path)+'.png');p.write_bytes(data);im=Image.open(p).convert('RGBA');rec.update(source=str(p),png=str(p),width=im.width,height=im.height,rgba_sha256=sha(im.tobytes()),status='Native PNG; not an emulator texture binding');textures.append(rec)
 else:
  other[data[:4].hex()]+=1;unresolved.append({'id':rec['id'],'magic':data[:4].hex(),'size':len(data),'classification':'Non-PTMD leaf or unsupported embedded container; not excluded from whole-game scope'})

with Iso9660(iso_path,writable=False) as iso:
 selected=[]
 for key,e in iso.by_path.items():
  if e.is_dir:continue
  head=iso._read_at(e.extent*2048,min(16,e.size));iso_rows.append({'path':e.path,'size':e.size,'magic':head[:4].hex()})
  if '/gamedata/if/' in key or key in ['psp_game/usrdir/gamedata/system.vol','psp_game/usrdir/gamedata/title.vol','psp_game/usrdir/gamedata/mc.vol']:selected.append((key,e))
 for key,e in selected:
  rel=key.split('/gamedata/',1)[1];visit(iso._read_at(e.extent*2048,e.size),rel,{'iso_path':e.path,'extent':e.extent})

report={'schema':'brs-expanded-ui-inventory/v1','iso_sha256':identity['iso']['sha256'],'scope':'All IF files plus SYSTEM.VOL, TITLE.VOL, MC.VOL; not all game texture containers','root_file_count':len(selected),'texture_count':len(textures),'ptmd_count':sum(t['magic']=='50544d44' for t in textures),'decode_failures':[t['id'] for t in textures if 'error' in t],'parse_sdo_source_sha256':sha(source.encode()),'textures':textures,'containers':containers,'unclassified_leaves':unresolved,'other_magics':dict(other),'complete_game_file_inventory':iso_rows}
(R/'qa/ui_inventory_expanded.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
# Separate sheets so all texture labels remain readable. A sheet is source evidence.
font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',15)
groups=collections.defaultdict(list)
for t in textures:
 if 'png' not in t:continue
 rel=t['relative'];group='resident' if 'if_rsdsys' in rel else 'title' if rel.startswith('title') else 'tutorial' if rel.startswith('if/pict') else 'minimap' if rel.startswith('if/evt') else 'remaining'
 groups[group].append(t)
for group,items in groups.items():
 for start in range(0,len(items),24):
  batch=items[start:start+24];sheet=Image.new('RGB',(1600,math.ceil(len(batch)/4)*340),'#293747');d=ImageDraw.Draw(sheet)
  for n,t in enumerate(batch):
   x=n%4*400;y=n//4*340;d.text((x+6,y+4),t['relative'][-45:],font=font,fill='white');d.text((x+6,y+25),f"{t['width']}x{t['height']} / {t.get('mode','PNG')}",font=font,fill='#adcbeb');im=Image.open(t['png']).convert('RGBA');im.thumbnail((385,280),Image.Resampling.NEAREST);sheet.paste(im,(x+6,y+52),im)
  sheet.save(R/f'qa/ui_inventory_{group}_{start//24+1}.png')
print(json.dumps({k:report[k] for k in ['root_file_count','texture_count','ptmd_count','decode_failures']}));print('SDO',sum('sdo' in c for c in containers),'unclassified',len(unresolved))
