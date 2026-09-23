"""Deterministic rendering of the identified Orbit font, never new glyph design."""
import hashlib,struct,math
from pathlib import Path
from functools import lru_cache
from PIL import Image,ImageDraw,ImageFont,ImageFilter
R=Path(__file__).resolve().parents[1]
FONT=R/'workspace/source/font/orbit/Orbit-Regular.ttf'
FONT_SHA='5d0206fb0a9e3eeac51aff8d4a6dbb7613d63fc435f1a51f96dc35cefb5f9f87'
assert hashlib.sha256(FONT.read_bytes()).hexdigest()==FONT_SHA
PROFILE={'font':'Orbit Regular','font_sha256':FONT_SHA,'source_commit':'95122395c6d1fda07aebdf36f566a75678bc3bdd','license':'SIL OFL 1.1','author':'Sooun Cho, JAMO','source_url':'https://github.com/JAMO-TYPEFACE/Orbit','intent':'Straight diagonal Hangul strokes and uniform stroke construction echo the fixed-ISO UI; not a claim of an exact original typeface match.','ui_space_advance_em':0.45,'ui_ink_expansion':'square max filter, radius round(font_size*0.015), minimum 1 output pixel','body_origin_8x':[8,-33],'body_size_8x':112,'body_ink_expansion':0,'runtime_status':'unverified candidate'}

@lru_cache(None)
def font(size):return ImageFont.truetype(str(FONT),size)

@lru_cache(None)
def coverage():
 data=FONT.read_bytes();tables={}
 for n in range(struct.unpack_from('>H',data,4)[0]):
  tag,_,offset,length=struct.unpack_from('>4sIII',data,12+16*n);tables[tag]=data[offset:offset+length]
 cm=tables[b'cmap'];result=set()
 for n in range(struct.unpack_from('>H',cm,2)[0]):
  platform,encoding,offset=struct.unpack_from('>HHI',cm,4+8*n)
  if not(platform==0 or (platform==3 and encoding in (1,10))):continue
  fmt=struct.unpack_from('>H',cm,offset)[0]
  if fmt==12:
   for k in range(struct.unpack_from('>I',cm,offset+12)[0]):
    a,b,g=struct.unpack_from('>III',cm,offset+16+12*k);result.update(range(a+(g==0),b+1))
  elif fmt==4:
   count=struct.unpack_from('>H',cm,offset+6)[0]//2
   for k in range(count):
    end=struct.unpack_from('>H',cm,offset+14+2*k)[0];start=struct.unpack_from('>H',cm,offset+16+2*count+2*k)[0]
    delta=struct.unpack_from('>h',cm,offset+16+4*count+2*k)[0];addr=offset+16+6*count+2*k;r=struct.unpack_from('>H',cm,addr)[0]
    for code in range(start,end+1):
     gid=(code+delta)&65535 if not r else struct.unpack_from('>H',cm,addr+r+2*(code-start))[0]
     if r and gid:gid=(gid+delta)&65535
     if gid:result.add(code)
 return result

def require_chars(text):
 missing=sorted(set(c for c in text if not c.isspace() and ord(c) not in coverage()))
 assert not missing,('missing glyphs',missing)

def text_ink(text,size,spacing=0):
 require_chars(text);f=font(size);radius=max(1,round(size*.015));parts=[];x=y=0
 for char in text:
  if char=='\n':x=0;y+=size+spacing;continue
  if char==' ':x+=size*.45;continue
  b=f.getbbox(char);parts.append((char,x,y,b));x+=f.getlength(char)
 assert parts
 left=math.floor(min(x+b[0] for _,x,y,b in parts))-radius
 top=math.floor(min(y+b[1] for _,x,y,b in parts))-radius
 right=math.ceil(max(x+b[2] for _,x,y,b in parts))+radius
 bottom=math.ceil(max(y+b[3] for _,x,y,b in parts))+radius
 guard=8;mask=Image.new('L',(right-left+2*guard,bottom-top+2*guard));draw=ImageDraw.Draw(mask)
 for char,x,y,b in parts:draw.text((x-left+guard,y-top+guard),char,font=f,fill=255)
 mask=mask.filter(ImageFilter.MaxFilter(2*radius+1));box=mask.getbbox()
 assert box and box[0]>=guard and box[1]>=guard and box[2]<=mask.width-guard and box[3]<=mask.height-guard
 return mask.crop((guard,guard,mask.width-guard,mask.height-guard))

def make_text(text,w,h,maximum,minimum=5,fill=(255,255,255,255),align='left',valign='center',spacing=0,stroke_width=0,stroke_fill=None,edge_margin=0,**kw):
 assert stroke_width==0,('unimplemented distinct outline layer',text)
 margin=edge_margin*8;mw=w-2*margin;mh=h-2*margin
 for size in range(maximum*8,max(12,minimum*8)-1,-1):
  mask=text_ink(text,size,spacing*8)
  if mask.width<=mw and mask.height<=mh:break
 else:raise ValueError(('text cannot fit',text,w,h))
 x=margin+(mw-mask.width if align=='right' else (mw-mask.width)//2 if align=='center' else 0)
 y=margin+(mh-mask.height if valign=='bottom' else (mh-mask.height)//2 if valign=='center' else 0)
 if fill[3]!=255:mask=mask.point(lambda a:round(a*fill[3]/255))
 tile=Image.new('RGBA',(w,h),(*fill[:3],0));tile.putalpha(Image.new('L',(w,h)));ink=Image.new('RGBA',mask.size,(*fill[:3],255));ink.putalpha(mask);tile.alpha_composite(ink,(x,y))
 return tile,size

def body_glyph(char):
 require_chars(char);g=8;mask=Image.new('L',(120+2*g,120+2*g))
 ImageDraw.Draw(mask).text((8+g,-33+g),char,font=font(112),fill=255)
 box=mask.getbbox()
 assert box and box[0]>=g and box[1]>=g and box[2]<=120+g and box[3]<=120+g,('body clipping',char,box)
 mask=mask.crop((g,g,120+g,120+g));result=Image.new('RGBA',mask.size,'white');result.putalpha(mask);return result

