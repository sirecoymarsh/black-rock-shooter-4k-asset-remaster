import sys,re,gzip,struct,json,hashlib
from pathlib import Path
from collections import defaultdict
from PIL import Image,ImageDraw,ImageFont
sys.dont_write_bytecode=True
R=Path(r'P:\AI\Codex\projects\black-rock-shooter-hd-retexture'); A=Path(r'P:\AI\Codex\work_archive\2026-07-25\new-chat-2\work')
sys.path.insert(0,str(A/'ui_graphics_pipeline'));sys.path.insert(0,str(A/'patch_pipeline'))
from ptmd_codec import decode_ptmd,unswizzle_psp,PtmdTexture
from brs_patch import Iso9660
out=R/'workspace/stella_hd/variants';out.mkdir(exist_ok=True);records=[];errors=[];iso_checks=[]
env=json.loads((R/'qa/evidence/environment.json').read_text(encoding='utf-8-sig'))
source_dir=A/'full_extracted/PSP_GAME/USRDIR/GAMEDATA/FLD/FCHR'
with Iso9660(Path(env['iso']['path']),writable=False) as iso:
 for p in sorted(source_dir.glob('FCHR_P_BRS*.BIN')):
  raw=p.read_bytes();rel='PSP_GAME/USRDIR/GAMEDATA/FLD/FCHR/'+p.name; entry=iso.by_path[rel.lower()]; check=iso._read_at(entry.extent*2048,entry.size)
  assert check==raw,rel
  iso_checks.append({'file':p.name,'sha256':hashlib.sha256(raw).hexdigest(),'current_iso_byte_match':True})
  b=gzip.decompress(raw)
  for i,m in enumerate(re.finditer(b'PTMD',b)):
   off=m.start();head=b[off:off+16];paloff=struct.unpack_from('<I',head,12)[0];mode=head[8];code=head[9]
   try:
    count=16 if mode==4 else 256;ps=4 if code==48 else 2;data=b[off:off+paloff+count*ps]
    if code in (0,16):
     w=1<<(head[7]>>4);h=head[6]|((head[7]&15)<<8);row=w//2 if mode==4 else w;assert paloff==16+row*h
     linear=unswizzle_psp(data[16:paloff],row,h);idx=bytes(c for v in linear for c in (v&15,v>>4)) if mode==4 else linear;pal=[]
     for v in struct.unpack('<'+'H'*count,data[paloff:]):
      if code==0:pal.append(((v&31)*255//31,((v>>5)&63)*255//63,((v>>11)&31)*255//31,255))
      else:pal.append(((v&31)*255//31,((v>>5)&31)*255//31,((v>>10)&31)*255//31,255 if v&32768 else 0))
     t=PtmdTexture(head,w,h,mode,code,paloff,idx,tuple(pal))
    else:t=decode_ptmd(data)
    png=out/f'{p.stem}_{i:02d}.png';Image.frombytes('RGBA',(t.width,t.height),t.rgba_bytes).save(png)
    (out/f'{p.stem}_{i:02d}.ptmd').write_bytes(data)
    records.append({'file':p.name,'index':i,'offset':off,'png':png.name,'width':t.width,'height':t.height,'rgba_sha256':hashlib.sha256(t.rgba_bytes).hexdigest(),'ptmd_sha256':hashlib.sha256(data).hexdigest()})
   except Exception as e:errors.append({'file':p.name,'index':i,'error':str(e)})
by_hash=defaultdict(list)
for r in records:by_hash[r['rgba_sha256']].append(r['png'])
dump=R/'workspace/sessions/S-20260922-145156-354b41/memstick/PSP/TEXTURES/NPUH10126/new'
observed=[];bodydumps=[];files=list(dump.glob('*.png'))
for p in files:
 try:
  im=Image.open(p).convert('RGBA'); sha=hashlib.sha256(im.tobytes()).hexdigest()
  if sha in by_hash:observed.append({'dump':p.name,'matches':by_hash[sha],'rgba_sha256':sha,'size':im.size})
  if im.size==(256,256):bodydumps.append(p)
 except Exception:pass
font=ImageFont.truetype(r'C:\Windows\Fonts\malgun.ttf',16)
bodies=[out/r['png'] for r in records if r['index']==0]
for name,items in [('source_bodies.png',bodies),('runtime_256.png',bodydumps)]:
 sheet=Image.new('RGB',(4*290,((len(items)+3)//4)*320),'#182333');d=ImageDraw.Draw(sheet)
 for i,p in enumerate(items):
  x=(i%4)*290;y=(i//4)*320;d.text((x+8,y+8),p.stem,font=font,fill='white');im=Image.open(p).convert('RGBA');im.thumbnail((270,270));sheet.paste(im.convert('RGB'),(x+8,y+40))
 sheet.save(out/name)
report={'iso_checks':iso_checks,'records':records,'errors':errors,'runtime_dump_file_count':len(files),'runtime_exact_matches':observed}
(out/'inventory.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'variants':len(iso_checks),'textures':len(records),'errors':errors,'observed_matches':observed},ensure_ascii=False,indent=2))
