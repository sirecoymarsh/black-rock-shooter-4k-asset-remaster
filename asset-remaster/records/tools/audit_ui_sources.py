import sys,json,gzip,hashlib,collections,shutil
from pathlib import Path
from PIL import Image
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
R=Path(__file__).resolve().parents[1];A=Path(r'P:\AI\Codex\work_archive\2026-07-25\new-chat-2\work');P=Path(r'P:\AI\Codex\projects\black-rock-shooter-hd-retexture')
sys.path.insert(0,str(A/'patch_pipeline'))
from brs_patch import Iso9660,Rtdp,Lpk
from ptmd_codec import decode_ptmd
report=json.loads((A/'ui_graphics_pipeline/hd_ui_pack_report.json').read_text(encoding='utf-8'));assets=[];source=R/'workspace/source/ui';source.mkdir(parents=True,exist_ok=True)
def h(b):return hashlib.sha256(b).hexdigest()
iso_path=A/'release_build/runtime_fix_iso_20260823_test_v2/BRS_Korean_v1.0.iso'
with Iso9660(iso_path,writable=False) as iso:
 def get(k):e=iso.by_path[k.lower()];return iso._read_at(e.extent*2048,e.size)
 volume=Rtdp(get('PSP_GAME/USRDIR/GAMEDATA/SYSTEM.VOL'))
 for row in report['assets']:
  domain,archive,file=row['relative'].split('/');index=int(file[:3]);info=dict(row)
  if domain=='MENU':raw=get('PSP_GAME/USRDIR/GAMEDATA/IF/MENU/'+archive+'.GZ');lpk=Lpk(gzip.decompress(raw))
  else:item=next(i for i in volume.items if i.name.lower()==archive.lower()+'.lpk');lpk=Lpk(bytes(v^0x55 for v in volume.payload(item)))
  data=lpk.payload(lpk.items[index]);dest=source/row['relative'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);tex=decode_ptmd(data);native=Image.frombytes('RGBA',(tex.width,tex.height),tex.rgba_bytes);native.save(dest.with_suffix('.png'))
  old=(A/'ui_graphics_pipeline/root_patched_ptmd'/row['relative']).read_bytes();original=(A/'lpk'/row['relative']).read_bytes()
  info.update({'id':f"UI-{row['index']:02d}",'iso_ptmd_sha256':h(data),'matches_old_korean_ptmd':data==old,'matches_original_english_ptmd':data==original,'logical_rgba_sha256':h(tex.rgba_bytes),'logical_size':native.size,'source':str(dest),'matches':[]})
  assets.append(info)
# Inspect only declared families, using source decoded pixels rather than quick-hash guesses.
families=collections.defaultdict(list)
for a in assets:families[a['cache_low']].append(a)
files={}
for root in [P,R]:
 for sess in (root/'workspace/sessions').iterdir():
  metaf=sess/'session.json'
  if not metaf.is_file():continue
  meta=json.loads(metaf.read_text(encoding='utf-8-sig'))
  if meta.get('iso_sha256')!='525b5d2b7d8f4723be25b026e72b69d07d30c2cf84d8a48235577ca3728fc92a':continue
  for f in (sess/'memstick/PSP/TEXTURES/NPUH10126/new').glob('*.png'):
   if len(f.stem)==24 and f.stem.startswith('00000000') and f.stem[8:16] in families:files[f.name]=f
unmatched=[]
for name,f in sorted(files.items()):
 im=Image.open(f).convert('RGBA');matches=[]
 for a in families[f.stem[8:16]]:
  w,hh=a['logical_size']
  if im.size!=(a['padded_width'],a['padded_height']):continue
  if h(im.crop((0,0,w,hh)).tobytes())==a['logical_rgba_sha256']:
   a['matches'].append({'key':f.stem,'path':str(f),'full_rgba_sha256':h(im.tobytes()),'logical_match':True});matches.append(a['id'])
 if not matches:unmatched.append({'key':f.stem,'path':str(f),'families':[a['id'] for a in families[f.stem[8:16]]]})
result={'schema':'brs-ui-iso-audit/v1','iso_sha256':'525b5d2b7d8f4723be25b026e72b69d07d30c2cf84d8a48235577ca3728fc92a','assets':assets,'unmatched_dumps':unmatched,'mapping_rule':'Current xxh64 observations only, decoded full logical source pixel identity, preserve dump padding separately; no quick hash migration or palette-only wildcard.'}
(R/'qa/ui_source_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
for a in assets:print(a['id'],a['relative'],'oldko',a['matches_old_korean_ptmd'],'english',a['matches_original_english_ptmd'],'matches',len(a['matches']))
print('unmatched',len(unmatched))