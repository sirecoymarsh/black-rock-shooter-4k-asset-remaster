"""Export decoded PGR mesh skin/bind data from immutable local bundle snapshots."""
from pathlib import Path
import json,sys,hashlib
ROOT=Path(r'P:\AI\Codex\projects\black-rock-shooter-hd-retexture')
sys.path.insert(0,str(ROOT/'workspace/tooldeps/unitypy'))
from UnityPy.helpers.MeshHelper import MeshHandler
import UnityPy
import numpy as np
R=ROOT/'workspace/pgr_reference';OUT=ROOT/'workspace/model_port'
keys=json.loads((R/'pgrstudio_Keys.json').read_text())
UnityPy.set_assetbundle_decrypt_key(bytes.fromhex(next(x['Key'] for x in keys if x['Name']=='PGR CN/JP/TW')))
manifest=json.loads((R/'extraction_manifest.json').read_text('utf-8'))
def load(suffix):
    rec=next(x for x in manifest['selected'] if x['bundle_name'].endswith(suffix));b=Path(rec['snapshot']).read_bytes()
    assert hashlib.sha256(b).hexdigest()==rec['sha256']
    return UnityPy.load(b),rec
prefab,pr=load('charaterprefab/r2blackrockmd010011.prefab.ab')
meshes,mr=load('body/r2blackrockmd010011/vc.ab')
objects={o.path_id:o for o in prefab.objects}
names={i:o.read().m_Name for i,o in objects.items() if o.type.name=='GameObject'}
transforms={i:o.read() for i,o in objects.items() if o.type.name=='Transform'}
renderers={o.read().m_Mesh.m_PathID:o.read() for o in prefab.objects if o.type.name=='SkinnedMeshRenderer'}
C=np.array([[-1,0,0,0],[0,0,1,0],[0,-1,0,0],[0,0,0,1]],dtype=float)
parts=[]
for o in meshes.objects:
    if o.type.name!='Mesh':continue
    d=o.read()
    if d.m_Name.startswith('E3'):continue
    h=MeshHandler(d);h.process();rend=renderers[o.path_id]
    assert len(d.m_BindPose)==len(rend.m_Bones)
    bones=[]
    for i,(bp,ref) in enumerate(zip(d.m_BindPose,rend.m_Bones)):
        t=transforms[ref.m_PathID]
        ib=np.array([[getattr(bp,f'e{r}{c}') for c in range(4)] for r in range(4)])
        ib=C@ib@np.linalg.inv(C);rest=np.linalg.inv(ib)
        bones.append(dict(index=i,name=names[t.m_GameObject.m_PathID],path_id=ref.m_PathID,inverse_bind=ib.T.reshape(-1).tolist(),position=rest[:3,3].tolist()))
    pos=np.array(h.m_Vertices)@C[:3,:3].T;nor=np.array(h.m_Normals)[:,:3]@C[:3,:3].T
    indices=[n for triangles in h.get_triangles() for tri in triangles for n in reversed(tri)]
    assert h.m_BoneIndices is not None and h.m_BoneWeights is not None
    assert len(h.m_BoneWeights)==len(pos)
    weights=np.array(h.m_BoneWeights);assert abs(weights.sum(axis=1)-1).max()<.001
    joints=np.array(h.m_BoneIndices);assert joints.max()<len(bones)
    part=dict(name=d.m_Name.removesuffix('VC'),positions=pos.reshape(-1).tolist(),normals=nor.reshape(-1).tolist(),uvs=[u for uv in h.m_UV0 for u in uv],indices=indices,weights=weights.tolist(),joints=joints.tolist(),bones=bones)
    parts.append(part)
    print(part['name'],len(pos),len(indices)//3, 'bones',len(bones),'bounds',np.stack([pos.min(axis=0),pos.max(axis=0)]).round(3).tolist())
    if 'Face' in part['name']:print('HEAD',bones)
    if 'Body' in part['name']:
        print('BODY CORE',[(b['name'],[round(x,3) for x in b['position']]) for b in bones if b['name'].startswith('Bip')])
(OUT/'pgr_skin_source.json').write_text(json.dumps(dict(parts=parts,source_bundles=[{'snapshot':x['snapshot'],'sha256':x['sha256']} for x in [pr,mr]]),separators=(',',':')),encoding='utf-8')
