"""Read-only PGR BRS reference extraction; all outputs stay in this project's ignored workspace."""
import sys,json,re,hashlib,collections
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8');sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'workspace/tooldeps/unitypy'))
import msgpack,UnityPy
OUT=ROOT/'workspace/pgr_reference';SRC=Path(r'Y:\Punishing Gray Raven Game\PGR_Data\StreamingAssets')
keys=json.loads((OUT/'pgrstudio_Keys.json').read_text());UnityPy.set_assetbundle_decrypt_key(bytes.fromhex(next(k['Key'] for k in keys if k['Name']=='PGR CN/JP/TW')))
index=msgpack.unpackb((OUT/'resource_matrix_index_index.bin').read_bytes(),raw=False,strict_map_key=False)[0]
all_matches={k:v for k,v in index.items() if re.search('blackrock|heiyan|brs',k,re.I)}
(OUT/'index_matches.json').write_text(json.dumps(all_matches,ensure_ascii=False,indent=2),encoding='utf-8')
select=[k for k in all_matches if k.startswith('assets/product/role/body/') or '/role/weaponres/' in k or '/role/charaterprefab/' in k or k=='assets/product/texture/image/uibrsactivity.ab']
results=[]
for name in select:
 key,hash1,size=index[name];p=SRC/'resource/matrix'/key
 rec={'bundle_name':name,'source':str(p),'index_sha1':hash1,'index_size':size}
 if not p.exists():rec['error']='missing';results.append(rec);continue
 st=p.stat();b=p.read_bytes();en=p.stat()
 if (st.st_size,st.st_mtime_ns)!=(en.st_size,en.st_mtime_ns):rec['error']='changed_during_read';results.append(rec);continue
 rec.update(size=len(b),sha256=hashlib.sha256(b).hexdigest(),sha1=hashlib.sha1(b).hexdigest(),mtime_ns=st.st_mtime_ns)
 snap=OUT/'snapshots'/key;snap.write_bytes(b);rec['snapshot']=str(snap)
 env=UnityPy.load(b);rec['types']=dict(collections.Counter(o.type.name for o in env.objects));rec['objects']=[];rec['containers']=list(env.container)
 folder=OUT/'extracted'/name.removeprefix('assets/product/').removesuffix('.ab');folder.mkdir(parents=True,exist_ok=True)
 for o in env.objects:
  if o.type.name not in ['Mesh','Texture2D','Material','SkinnedMeshRenderer','Animator','Avatar']:continue
  it={'path_id':o.path_id,'type':o.type.name,'name':o.peek_name()}
  try:
   d=o.read();safe=re.sub(r'[^\w.-]','_',getattr(d,'m_Name',None) or str(o.path_id))
   if o.type.name=='Texture2D':
    it.update(width=d.m_Width,height=d.m_Height,format=str(d.m_TextureFormat),mip_count=d.m_MipCount)
    dest=folder/(safe+'.png');d.image.save(dest);it['export']=str(dest)
   elif o.type.name=='Mesh':
    it.update(vertices=d.m_VertexData.m_VertexCount,submeshes=[{'indices':s.indexCount,'topology':s.topology} for s in d.m_SubMeshes],bind_pose_count=len(d.m_BindPose or []),blend_shape_count=len(d.m_Shapes.channels) if d.m_Shapes else 0)
    dest=folder/(safe+'.obj');dest.write_text(d.export(),encoding='utf-8');it['export']=str(dest)
   elif o.type.name=='Material':
    it['properties']=o.read_typetree();(folder/(safe+'.material.json')).write_text(json.dumps(it['properties'],ensure_ascii=False,indent=2),encoding='utf-8')
   elif o.type.name=='SkinnedMeshRenderer':
    it.update(bones=len(d.m_Bones or []),mesh_path_id=d.m_Mesh.m_PathID,mesh_file_id=d.m_Mesh.m_FileID)
  except Exception as e:it['error']=f'{type(e).__name__}: {e}'
  rec['objects'].append(it)
 results.append(rec)
 print(name,rec['types'])
 for it in rec['objects']:
  print({k:v for k,v in it.items() if k not in ['properties','export']})
(OUT/'extraction_manifest.json').write_text(json.dumps({'unitypy_version':UnityPy.__version__,'source_root':str(SRC),'bundle_name_match_count':len(all_matches),'selected':results},ensure_ascii=False,indent=2),encoding='utf-8')
