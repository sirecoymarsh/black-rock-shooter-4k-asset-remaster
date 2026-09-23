import sys,re,gzip,struct,json,hashlib
from pathlib import Path
from PIL import Image
sys.dont_write_bytecode=True
ROOT=Path(r'P:\AI\Codex\projects\black-rock-shooter-hd-retexture');A=Path(r'P:\AI\Codex\work_archive\2026-07-25\new-chat-2\work');sys.path.insert(0,str(A/'ui_graphics_pipeline'));from ptmd_codec import decode_ptmd,unswizzle_psp,PtmdTexture
out=ROOT/'workspace/stella_hd/source';out.mkdir(parents=True,exist_ok=True);records=[]
for name in ['FCHR_P_BRS00.BIN','FCHR_P_BRS02.BIN']:
 p=A/'full_extracted/PSP_GAME/USRDIR/GAMEDATA/FLD/FCHR'/name;b=gzip.decompress(p.read_bytes())
 for i,m in enumerate(re.finditer(b'PTMD',b)):
  off=m.start();head=b[off:off+16];paloff=struct.unpack_from('<I',head,12)[0];mode=head[8];code=head[9];print(name,i,hex(off),head.hex())
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
   (out/f'{p.stem}_{i:02d}.ptmd').write_bytes(data)
   png=out/f'{p.stem}_{i:02d}.png';Image.frombytes('RGBA',(t.width,t.height),t.rgba_bytes).save(png);rec={'source':str(p),'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'offset':off,'ptmd_sha256':hashlib.sha256(data).hexdigest(),'width':t.width,'height':t.height,'png':str(png),'rgba_sha256':hashlib.sha256(t.rgba_bytes).hexdigest()};records.append(rec);print('OK',t.width,t.height)
  except Exception as e:print(type(e).__name__,e)
(out/'source_manifest.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
