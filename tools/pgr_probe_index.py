import sys,json,hashlib,re
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8');sys.dont_write_bytecode=True
ROOT=Path(r'P:\AI\Codex\projects\black-rock-shooter-hd-retexture')
sys.path.insert(0,str(ROOT/'workspace/tooldeps/unitypy'))
import UnityPy
keys=json.loads((ROOT/'workspace/pgr_reference/pgrstudio_Keys.json').read_text())
UnityPy.set_assetbundle_decrypt_key(bytes.fromhex(next(k['Key'] for k in keys if k['Name']=='PGR CN/JP/TW')))
out=ROOT/'workspace/pgr_reference';(out/'snapshots').mkdir(exist_ok=True)
for rel in ['resource/matrix/index','document/matrix/index']:
 p=Path(r'Y:\Punishing Gray Raven Game\PGR_Data\StreamingAssets')/rel
 if not p.exists():continue
 st=p.stat();b=p.read_bytes();end=p.stat();assert(st.st_size,st.st_mtime_ns)==(end.st_size,end.st_mtime_ns),'updating'
 n=rel.replace('/','_');(out/'snapshots'/n).write_bytes(b)
 print('FILE',rel,len(b),hashlib.sha256(b).hexdigest())
 env=UnityPy.load(b)
 for obj in env.objects:
  print('OBJ',obj.type.name,obj.path_id,obj.peek_name())
  if obj.type.name=='TextAsset':
   a=obj.read();data=a.m_Script.encode('utf-8','surrogateescape');(out/(n+'_'+re.sub(r'[^\w.-]','_',a.m_Name)+'.bin')).write_bytes(data);print('TEXT',len(data),repr(data[:250]))
  elif obj.type.name=='AssetBundle':
   d=obj.read();print('CONTAINER',list(env.container)[:8])
