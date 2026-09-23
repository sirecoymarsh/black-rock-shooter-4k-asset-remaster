import sys,json,collections,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
R=Path(r'P:\AI\Codex\projects\black-rock-shooter-hd-ui-fonts');sys.path.insert(0,str(R/'tools'))
from brs_font_pipeline import parse_font_layout,cell_bytes,decoded_cell_image
l,p=parse_font_layout((R/'workspace/source/font/font.lpk').read_bytes())
lookup=collections.defaultdict(list)
for i in range(l.glyph_count):
 im=decoded_cell_image(cell_bytes(p,l,i),l.palette_rgba).getchannel('A')
 if im.getbbox():lookup[im.tobytes()].append(i)
dirs=[Path(r'P:\AI\Codex\projects\black-rock-shooter-hd-retexture\workspace\sessions')/s/'memstick/PSP/TEXTURES/NPUH10126/new' for s in ['S-20260922-145156-354b41','S-20260922-151804-baseline-d7d8b6','S-20260922-152906-preview-60de48']]
files={f.name:f for d in dirs for f in d.glob('*851096b*.png')}
print('caches',len(files))
for f in list(files.values())[:6]:
 im=Image.open(f).convert('RGBA');a=im.getchannel('A');results=[]
 for offy in range(2):
  for offx in range(2):
   hits=[];nonblank=0
   for y in range(offy,im.height-14,16):
    for x in range(offx,im.width-14,16):
     b=a.crop((x,y,x+15,y+15));nonblank+=bool(b.getbbox());match=lookup.get(b.tobytes())
     if match:hits.append((x,y,match))
   results.append((offx,offy,len(hits),nonblank,hits[:3]))
 print(f.name,im.size,results)