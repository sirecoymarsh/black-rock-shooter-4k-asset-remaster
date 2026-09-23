import sys, json, hashlib, shutil, collections, gzip
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
sys.dont_write_bytecode=True
sys.stdout.reconfigure(encoding='utf-8')
R=Path(r'P:\AI\Codex\projects\black-rock-shooter-hd-ui-fonts')
P=Path(r'P:\AI\Codex\projects\black-rock-shooter-hd-retexture')
A=Path(r'P:\AI\Codex\work_archive\2026-07-25\new-chat-2\work')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''): h.update(b)
 return h.hexdigest()
def js(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
E=json.loads((P/'qa/evidence/environment.json').read_text(encoding='utf-8-sig'))
assert sha(Path(E['iso']['path']))==E['iso']['sha256']
S=R/'workspace/source';S.mkdir(parents=True,exist_ok=True)
manifest=[]
for rel in ['PROJECT.md','PROGRESS.md','qa/evidence/environment.json','qa/evidence/inventory_summary.json','workspace/inventory/baseline_mapping_audit.json','workspace/inventory/assets.json','workspace/inventory/observations.json','workspace/inventory/crosswalk.json','qa/coverage.json']:
 src=P/rel;dst=S/'parent_records'/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst);manifest.append({'source':str(src),'snapshot':str(dst),'sha256':sha(dst)})
sys.path.insert(0,str(A/'patch_pipeline'))
from brs_patch import Iso9660,Rtdp
with Iso9660(Path(E['iso']['path']),writable=False) as iso:
 v=iso.by_path['psp_game/usrdir/gamedata/system.vol'];raw=iso._read_at(v.extent*2048,v.size);vol=Rtdp(raw)
 for item in vol.items:
  if item.name.lower() in ['font.lpk','ucs2jis.bin','ascii.ptm']:
   enc=vol.payload(item);data=bytes(v^0x55 for v in enc)
   dest=S/'font'/item.name.lower();dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
   manifest.append({'iso_path':'psp_game/usrdir/gamedata/system.vol','entry':item.name,'raw_sha256':hashlib.sha256(enc).hexdigest(),'decoded_sha256':sha(dest),'size':len(data),'output':str(dest)})
F=A/'release_build/runtime_fix_iso_20260823_test_v2/font_final'
for name in ['glyph_alias_map.json','glyph_alias_map_bscr_cjk.json']:
 shutil.copyfile(F/name,S/'font'/name)
assert (S/'font/font.lpk').read_bytes()==(F/'font.lpk').read_bytes()
assert (S/'font/ucs2jis.bin').read_bytes()==(F/'ucs2jis.bin').read_bytes()
for rel in ['font_pipeline/brs_font_pipeline.py','ui_graphics_pipeline/ptmd_codec.py']:
 shutil.copyfile(A/rel,R/'tools'/Path(rel).name)
js(R/'qa/source_identity.json',{'iso':E['iso'],'sources':manifest,'font_matches_final_build':True})
D=P/'workspace/sessions/S-20260922-145156-354b41/memstick/PSP/TEXTURES/NPUH10126/new'
files=sorted(D.glob('*.png'));groups=collections.defaultdict(list)
for f in files:
 im=Image.open(f);groups[(im.size,f.stem[8:16])].append(f)
print('GROUPS',[(k,len(v)) for k,v in sorted(groups.items(),key=lambda x:-len(x[1]))[:20]])
selected=[]
for k,v in sorted(groups.items(),key=lambda x:-len(x[1]))[:24]:
 selected.extend(v[:2])
sheet=Image.new('RGB',(6*270,((len(selected)+5)//6)*315),'#202c3d');draw=ImageDraw.Draw(sheet)
for i,f in enumerate(selected):
 x=i%6*270;y=i//6*315;im=Image.open(f).convert('RGBA');im.thumbnail((256,280),Image.Resampling.NEAREST);sheet.paste(im,(x+6,y+28),im);draw.text((x+6,y+5),f.stem[8:],fill='white')
sheet.save(R/'qa/source_contact.png')
js(R/'qa/dump_groups.json',[{'size':k[0],'clut_dimension':k[1],'count':len(v),'example':str(v[0])} for k,v in sorted(groups.items(),key=lambda x:-len(x[1]))])
print('FONT ISO MATCH; source snapshots complete')