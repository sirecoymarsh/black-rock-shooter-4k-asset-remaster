"""Read-only UI UV extraction from PPSSPP v1.20.4 GE frame records.

Uses original PSP texture bytes, not the replacement GPU texture. Only through-mode
vertices are interpreted. Unsupported formats are counted, never guessed.
"""
import sys,json,struct,hashlib,collections
from pathlib import Path
import numpy as np
from PIL import Image
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
R=Path(__file__).resolve().parents[1];D=Path(sys.argv[1]);meta=json.loads((D/'commands.json').read_text());data=(D/'pushbuf.bin').read_bytes()
regs=[0]*256;vertices=b'';indices=b'';texture=None;clut=bytearray(1024);draws=[];errors=collections.Counter();formats=collections.Counter();textures={};texcache={}
def sha(b):return hashlib.sha256(b).hexdigest()
def words(b):return struct.unpack('<'+'I'*(len(b)//4),b)
def palette(b,fmt):
 if fmt==3:return np.frombuffer(b,dtype=np.uint8).reshape(-1,4)
 v=np.frombuffer(b,dtype='<u2').astype(np.uint32)
 if fmt==0:r=(v&31)*255//31;g=((v>>5)&63)*255//63;b=((v>>11)&31)*255//31;a=np.full(len(v),255)
 elif fmt==1:r=(v&31)*255//31;g=((v>>5)&31)*255//31;b=((v>>10)&31)*255//31;a=(v>>15)*255
 elif fmt==2:r=(v&15)*17;g=((v>>4)&15)*17;b=((v>>8)&15)*17;a=(v>>12)*17
 else:raise ValueError('Unsupported palette')
 return np.stack([r,g,b,a],1).astype(np.uint8)
def get_texture():
 if texture is None:raise ValueError('Missing texture')
 raw,framebuf=texture;fmt=regs[0xc3]&15;w=1<<(regs[0xb8]&15);h=1<<((regs[0xb8]>>8)&15);bufw=regs[0xa8]&0x7ff
 if framebuf:_,bufw,_,_=struct.unpack_from('<IIII',raw);raw=raw[16:]
 if fmt not in range(6):raise ValueError('Unsupported texture format '+str(fmt))
 if not bufw or w>bufw:raise ValueError('Unsupported short stride')
 size=bufw*h*[16,16,16,32,4,8][fmt]//8
 if len(raw)<size:raise ValueError('Short texture')
 key=(sha(raw[:size]),fmt,w,h,bufw,regs[0xc2]&1,regs[0xc5],sha(clut))
 if key in texcache:return texcache[key]
 stride=size//h;a=np.frombuffer(raw[:size],dtype=np.uint8)
 if regs[0xc2]&1:
  if h%8 or stride%16:raise ValueError('Unsupported swizzle geometry')
  a=a.reshape(h//8,stride//16,8,16).transpose(0,2,1,3).reshape(h,stride)
 else:a=a.reshape(h,stride)
 if fmt==4:
  ix=np.empty((h,bufw),np.uint8);ix[:,0::2]=a&15;ix[:,1::2]=a>>4
 elif fmt==5:ix=a
 if fmt in (4,5):
  cf=regs[0xc5];ix=((ix.astype(np.uint32)>>((cf>>2)&31))&((cf>>8)&255))|(((cf>>16)&31)<<4)
  pal=palette(clut,cf&3);rgba=pal[ix][:,:w]
 else:rgba=palette(a.tobytes(),fmt).reshape(h,bufw,4)[:,:w]
 digest=sha(rgba.tobytes());dest=D/'textures'/f'{digest}.png';dest.parent.mkdir(exist_ok=True)
 if digest not in textures:
  Image.fromarray(rgba).save(dest);textures[digest]={'width':w,'height':h,'format':fmt,'bufw':bufw,'file':str(dest),'rgba_sha256':digest}
 texcache[key]=digest;return digest
def vertex_layout(vt):
 tc=vt&3;col=(vt>>2)&7;nrm=(vt>>5)&3;pos=(vt>>7)&3;wt=(vt>>9)&3
 if wt or (vt>>18)&7:raise ValueError('Weighted/morphed 2D vertex')
 size=0;alignmax=1;layout={}
 for key,t,count,cs in [('uv',tc,2,False),('color',col,1,True),('normal',nrm,3,False),('pos',pos,3,False)]:
  if not t:continue
  unit=({4:2,5:2,6:2,7:4}[t] if cs else [0,1,2,4][t]);size=(size+unit-1)//unit*unit;layout[key]=(size,t);size+=unit*count;alignmax=max(alignmax,unit)
 return (size+alignmax-1)//alignmax*alignmax,layout
def draw(op,ci):
 vt=regs[0x12];formats[hex(vt)]+=1
 if (vt>>9)&3 or (vt>>18)&7:return
 if regs[0xc0]&3:return  # Only direct UV mapping; exclude generated coordinates.
 if not regs[0x1e]&1 or not vt&3:return
 try:
  tex=get_texture();stride,layout=vertex_layout(vt);count=op&65535;itype=(vt>>11)&3
  ids=struct.unpack_from('<'+[None,'B','H','I'][itype]*count,indices) if itype else range(count)
  pts=[]
  for i in ids:
   base=i*stride;uo,ut=layout['uv'];po,pt=layout['pos']
   uv=struct.unpack_from('<'+[None,'BB','HH','ff'][ut],vertices,base+uo)
   if not vt&0x800000:
    den=[None,128,32768,1][ut]
    su,sv,ou,ov=[struct.unpack('<f',struct.pack('<I',regs[k]<<8))[0] for k in [0x48,0x49,0x4a,0x4b]]
    uv=((uv[0]/den*su+ou)*textures[tex]['width'],(uv[1]/den*sv+ov)*textures[tex]['height'])
   pos=struct.unpack_from('<'+[None,'bbB','hhH','fff'][pt],vertices,base+po)
   pts.append([*uv,*pos])
  assert all(all(np.isfinite(p)) for p in pts)
  draws.append({'command':ci,'primitive':(op>>16)&7,'vtype':hex(vt),'texture':tex,'vertices':pts,'uv_bounds':[min(p[0] for p in pts),min(p[1] for p in pts),max(p[0] for p in pts),max(p[1] for p in pts)],'xy_bounds':[min(p[2] for p in pts),min(p[3] for p in pts),max(p[2] for p in pts),max(p[3] for p in pts)]})
 except (ValueError,IndexError,KeyError,struct.error,AssertionError) as e:errors[str(e)]+=1
ranges=[(0,2),(0x10,0x10),(0x12,0x28),(0x2c,0x33),(0x36,0x38),(0x42,0x4d),(0x50,0x51),(0x53,0x58),(0x5b,0xb5),(0xb8,0xc3),(0xc5,0xd0),(0xd2,0xe9),(0xeb,0xec),(0xee,0xee),(0xf0,0xf6),(0xf8,0xf9)]
for ci,c in enumerate(meta['commands']):
 b=data[c['ptr']:c['ptr']+c['sz']];t=c['type']
 if t==0:
  vals=words(b);p=17
  for lo,hi in ranges:
   for reg in range(lo,hi+1):
    op=vals[p];p+=1;assert op>>24==reg;regs[reg]=op&0xffffff
 elif t==1:
  for op in words(b):
   reg=op>>24;regs[reg]=op&0xffffff
   if reg==4:draw(op,ci)
 elif t==2:vertices=b
 elif t==3:indices=b
 elif t==4:clut[:len(b)]=b
 elif t in (16,24):texture=(b,t==24)
# Exact logical RGBA links to fixed ISO assets; padding is never inferred as art.
audit=json.loads((R/'qa/ui_source_audit.json').read_text(encoding='utf-8'))
for digest,tex in textures.items():
 im=Image.open(tex['file']).convert('RGBA');matches=[]
 for a in audit['assets']:
  if im.size!=(a['padded_width'],a['padded_height']):continue
  source=Image.open(Path(a['source']).with_suffix('.png')).convert('RGBA')
  if im.crop((0,0,*source.size)).tobytes()==source.tobytes():matches.append(a['id'])
 tex['ui_assets']=matches
report={'source':meta['source'],'source_sha256':meta['source_sha256'],'decode_errors':dict(errors),'vertex_formats':dict(formats),'textures':textures,'draws':draws,'scope':'Direct-UV, unweighted, unmorphed primitives. Non-through UVs include scale/offset and texture-size conversion. XYZ values are unprojected; no GPU replacement-byte claim.'}
(D/'ui_consumers.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'draws':len(draws),'textures':len(textures),'errors':dict(errors),'formats':dict(formats),'mapped':{k:v['ui_assets'] for k,v in textures.items() if v['ui_assets']}}))
