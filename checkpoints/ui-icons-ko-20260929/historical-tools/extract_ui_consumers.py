"""Freeze fixed-ISO UI containers and decode their bounded SDO display lists."""
import sys,json,gzip,hashlib,struct,collections
from pathlib import Path
from PIL import Image
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
R=Path(__file__).resolve().parents[1];A=Path(r'P:\AI\Codex\work_archive\2026-07-25\new-chat-2\work');sys.path.insert(0,str(A/'patch_pipeline'))
from brs_patch import Iso9660,Rtdp,Lpk
from ptmd_codec import decode_ptmd
def sha(b):return hashlib.sha256(b).hexdigest()
def parse_sdo(b):
 assert b[:4]==b'SDOa';n,texcount=struct.unpack_from('<HH',b,4);assert 8+n*16<=len(b);rows=[]
 ptrs=[struct.unpack_from('<I',b,8+i*16+12)[0] for i in range(n)];limits=sorted(set([p for p in ptrs if p]+[len(b)]))
 for i in range(n):
  kind,tex,x,y,w,h,p=struct.unpack_from('<HHhhhhI',b,8+i*16);r={'id':i,'kind':kind,'texture_slot':tex,'layout_xywh':[x,y,w,h],'offset':p}
  if not p:r['empty']=True;rows.append(r);continue
  end=next(v for v in limits if v>p);assert p>=8+n*16 and end<=len(b)
  # SDOa stores a PSP display list followed by its relative-address vertex data.
  ops=[];q=p
  while q+4<=end:
   op=struct.unpack_from('<I',b,q)[0];ops.append(op);q+=4
   if op>>24==0x0b:break
  vt=next((v&0xffffff for v in ops if v>>24==0x12),None);vp=next((v&0xffffff for v in ops if v>>24==1),None);prim=next((v&0xffffff for v in ops if v>>24==4),None)
  r.update(vtype=hex(vt) if vt is not None else None,ops=[hex(v) for v in ops])
  if vt in (0x19c,0x180):
   r['untextured']=True;r['classification']='No texture-coordinate component in vertex format';rows.append(r);continue
  if vt not in (0x183,0x19f) or vp is None or prim is None:r['unresolved']='Unsupported display-list format';rows.append(r);continue
  stride=20 if vt==0x183 else 24;count=prim&65535;assert p+vp>=q and p+vp+stride*count<=end
  vertices=[]
  for j in range(count):
   a=p+vp+j*stride;u,v=struct.unpack_from('<ff',b,a);xyz=struct.unpack_from('<fff',b,a+(8 if vt==0x183 else 12));vertices.append([u,v,*xyz])
  r.update(primitive=(prim>>16)&7,vertices=vertices,vertex_bytes_sha256=sha(b[p+vp:p+vp+stride*count]),uv_normalized=[min(v[0] for v in vertices),min(v[1] for v in vertices),max(v[0] for v in vertices),max(v[1] for v in vertices)])
  rows.append(r)
 return {'record_count':n,'texture_slot_count':texcount,'records':rows}
audit=json.loads((R/'qa/ui_source_audit.json').read_text(encoding='utf-8'));archives=sorted(set('/'.join(a['relative'].split('/')[:2]) for a in audit['assets']));records=[]
iso_path=A/'release_build/runtime_fix_iso_20260823_test_v2/BRS_Korean_v1.0.iso'
with Iso9660(iso_path,writable=False) as iso:
 def get(k):e=iso.by_path[k.lower()];return iso._read_at(e.extent*2048,e.size)
 vol=Rtdp(get('PSP_GAME/USRDIR/GAMEDATA/SYSTEM.VOL'))
 for archive in archives:
  domain,name=archive.split('/')
  if domain=='MENU':raw=gzip.decompress(get('PSP_GAME/USRDIR/GAMEDATA/IF/MENU/'+name+'.GZ'))
  else:item=next(i for i in vol.items if i.name.lower()==name.lower()+'.lpk');raw=bytes(v^0x55 for v in vol.payload(item))
  lpk=Lpk(raw);dest=R/'workspace/source/ui_containers'/archive;dest.mkdir(parents=True,exist_ok=True);rec={'archive':archive,'lpk_sha256':sha(raw),'members':[]}
  for item in lpk.items:
   b=lpk.payload(item);magic=b[:4];fn=f'{item.index:03d}_'+('PTMD.ptm' if magic==b'PTMD' else 'SDOa.sdo' if magic==b'SDOa' else 'other.bin');p=dest/fn;p.write_bytes(b);r={'index':item.index,'magic':magic.hex(),'sha256':sha(b),'path':str(p),'size':len(b)}
   if magic==b'SDOa':r['sdo']=parse_sdo(b)
   elif magic==b'PTMD':
    try:
     t=decode_ptmd(b);Image.frombytes('RGBA',(t.width,t.height),t.rgba_bytes).save(p.with_suffix('.png'));r.update(width=t.width,height=t.height,padded_width=1<<(t.width-1).bit_length(),padded_height=1<<(t.height-1).bit_length())
    except ValueError as e:r['unresolved']=str(e)
   rec['members'].append(r)
  records.append(rec)
report={'schema':'brs-ui-sdo/v1','iso_sha256':audit['iso_sha256'],'records':records,'texture_slot_binding':'Unresolved initially; texture slot numbering is not assumed to equal LPK PTMD ordering. Bind using source dimensions, UV samples and runtime texture/vertex byte equality.'}
(R/'qa/ui_consumers_static.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'archives':len(records),'ptmd':sum(m['magic']=='50544d44' for r in records for m in r['members']),'sdo':sum('sdo' in m for r in records for m in r['members']),'sprites':sum(m['sdo']['record_count'] for r in records for m in r['members'] if 'sdo' in m),'unresolved':sum(bool(s.get('unresolved')) for r in records for m in r['members'] if 'sdo' in m for s in m['sdo']['records'])}))
