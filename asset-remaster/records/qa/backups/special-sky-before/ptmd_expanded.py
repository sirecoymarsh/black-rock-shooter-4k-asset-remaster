"""Decode indexed UI and bounded direct-color PTMD without altering source bytes."""
import struct
import numpy as np
from PIL import Image
from ptmd_codec import decode_ptmd,encode_ptmd,unswizzle_psp,swizzle_psp

def decode(data):
 assert data[:4]==b'PTMD' and len(data)>=16
 w=1<<(data[7]>>4);h=data[6]|((data[7]&15)<<8);mode=data[8];swizzled=data[5]
 assert swizzled in (0,1),('swizzle flag',swizzled)
 if mode in (4,5):
  assert swizzled==1,('unhandled linear indexed texture',mode)
  if data[9] in (0,16):
   assert data[4]==2 and data[10:12]==b'\0\0'
   stride=w//2 if mode==4 else w;count=16 if mode==4 else 256
   paloff=struct.unpack_from('<I',data,12)[0]
   assert paloff==16+stride*h and len(data)==paloff+2*count
   linear=unswizzle_psp(data[16:paloff],stride,h)
   indexes=bytes(v for b in linear for v in (b&15,b>>4)) if mode==4 else linear
   assert len(indexes)==w*h
   packed=bytes(indexes[i]|(indexes[i+1]<<4) for i in range(0,len(indexes),2)) if mode==4 else indexes
   assert data[16:paloff]==swizzle_psp(packed,stride,h)
   # Reuse the direct decoder's exact 16-bit pack-back check for palette entries.
   hdr=b'PTMD'+bytes([2,0,1,(4 if count==16 else 8)<<4,data[9]>>4,0,0,0])+struct.pack('<I',16+2*count)
   palette,proof=decode(hdr+data[paloff:]);assert proof['roundtrip_exact']
   colors=np.asarray(palette).reshape(count,4)
   rgba=colors[np.frombuffer(indexes,np.uint8)].reshape(h,w,4)
   return Image.fromarray(rgba),{'mode':mode,'swizzled':True,'palette_code':data[9],'roundtrip_exact':True,'color_expansion':'bit replication; runtime dump match is checked separately'}
  t=decode_ptmd(data);assert encode_ptmd(t)==data
  return Image.frombytes('RGBA',(w,h),t.rgba_bytes),{'mode':mode,'swizzled':bool(swizzled),'palette_code':t.palette_code,'roundtrip_exact':True}
 assert mode in (0,1,2,3),('unsupported mode',mode)
 stride=w*(4 if mode==3 else 2);end=16+stride*h
 assert len(data)==end and struct.unpack_from('<I',data,12)[0]==end,('direct texture length',len(data),end)
 assert data[9:12]==b'\0\0\0'
 linear=unswizzle_psp(data[16:],stride,h) if swizzled else data[16:]
 if mode==3:rgba=np.frombuffer(linear,np.uint8).reshape(h,w,4).copy();encoded=rgba.tobytes()
 else:
  bits=np.frombuffer(linear,'<u2').astype(np.uint32)
  def five(x):return (x<<3)|(x>>2)
  if mode==0:
   a=bits&31;b=(bits>>5)&63;c=(bits>>11)&31
   rgba=np.stack([five(a),(b<<2)|(b>>4),five(c),np.full(len(bits),255)],1).astype(np.uint8)
   r=rgba.astype(np.uint16);back=(r[:,0]>>3)|((r[:,1]>>2)<<5)|((r[:,2]>>3)<<11)
  elif mode==1:
   rgba=np.stack([five(bits&31),five((bits>>5)&31),five((bits>>10)&31),(bits>>15)*255],1).astype(np.uint8)
   r=rgba.astype(np.uint16);back=(r[:,0]>>3)|((r[:,1]>>3)<<5)|((r[:,2]>>3)<<10)|((r[:,3]>>7)<<15)
  else:
   rgba=np.stack([(bits&15)*17,((bits>>4)&15)*17,((bits>>8)&15)*17,(bits>>12)*17],1).astype(np.uint8)
   r=rgba.astype(np.uint16);back=(r[:,0]//17)|((r[:,1]//17)<<4)|((r[:,2]//17)<<8)|((r[:,3]//17)<<12)
  encoded=back.astype('<u2').tobytes();rgba=rgba.reshape(h,w,4)
 assert encoded==linear
 assert data[:16]+(swizzle_psp(encoded,stride,h) if swizzled else encoded)==data
 return Image.fromarray(rgba),{'mode':mode,'swizzled':bool(swizzled),'palette_code':None,'roundtrip_exact':True,'color_expansion':'bit replication; runtime dump match is checked separately'}
