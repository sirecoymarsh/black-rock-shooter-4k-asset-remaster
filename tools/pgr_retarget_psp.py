"""Prototype PGR geometry/skin adaptation to PSP bind space, not a release rig.
Accessory bones are explicitly collapsed to available PSP chains. Preserve source.
"""
import json,sys,gzip,struct,math,base64,hashlib
from pathlib import Path
ROOT=Path(r'P:\AI\Codex\projects\black-rock-shooter-hd-retexture')
sys.path.insert(0,str(ROOT/'workspace/tooldeps/imageqa'))
import numpy as np
OUT=ROOT/'workspace/model_port';R=ROOT/'workspace/pgr_reference'

def main():
    src=json.loads((OUT/'pgr_skin_source.json').read_text());psp=json.loads((OUT/'FCHR_P_BRS02_structure.json').read_text())
    sc=gzip.decompress(Path(psp['source']).read_bytes());b=sc[psp['insm_offset']:psp['insm_offset']+psp['insm_length']]
    matrix_base=min(g['matrix_offset']-64*g['transform_index'] for g in psp['matrix_groups'])
    inverse=[np.array(struct.unpack_from('<16f',b,matrix_base+64*i)).reshape(4,4).T for i in range(46)]+[np.eye(4)]
    rest=[np.linalg.inv(m) for m in inverse]
    named={bone['name']:bone for p in src['parts'] for bone in p['bones']}
    scale=86.0
    sy=np.array([0,named['Bip001LFoot']['position'][1],named['BoneLCalfTwist']['position'][1],named['Bip001Pelvis']['position'][1],named['Bip001Spine2']['position'][1],named['Bip001Neck']['position'][1],named['Bip001Head']['position'][1],1.8])
    ty=np.array([0,rest[40][1,3],rest[39][1,3],rest[0][1,3],rest[2][1,3],rest[3][1,3],rest[4][1,3],rest[4][1,3]+(1.8-sy[-2])*scale])
    assert np.all(np.diff(sy)>0) and np.all(np.diff(ty)>0)
    head_z=rest[4][2,3]-named['Bip001Head']['position'][2]*scale
    def warp(v):
        p=np.array(v,dtype=float).copy();p[...,0]*=scale;p[...,2]=p[...,2]*scale+head_z;p[...,1]=np.interp(p[...,1],sy,ty);return p
    arms={}
    for side,j in [('L',18),('R',23)]:
        a=warp(named[f'Bip001{side}UpperArm']['position']);h=warp(named[f'Bip001{side}Hand']['position']);target=rest[j][:3,3];dest=rest[j+2][:3,3]
        u=h[:2]-a[:2];v=dest[:2]-target[:2];theta=math.atan2(v[1],v[0])-math.atan2(u[1],u[0]);k=np.linalg.norm(v)/np.linalg.norm(u)
        mat=np.eye(3);mat[:2,:2]=[[math.cos(theta)*k,-math.sin(theta)*k],[math.sin(theta)*k,math.cos(theta)*k]]
        arms[side]=(a,target,mat)
    def target_bone(bone):
        n=bone['name'];left='L' in n.removeprefix('Bip001');side=0 if left else 1
        if n=='Bip001Pelvis':return 0,'pelvis'
        if n=='Bip001Spine':return 1,'lower spine'
        if n in ('Bip001Spine1','Bip001Spine2'):return 2,'upper spine collapse'
        if n=='Bip001Neck':return 3,'neck'
        if n=='Bip001Head':return 4,'head'
        if 'Clavicle' in n:return [17,22][side],'shoulder/repair collapse'
        if 'UpperArm' in n:return [18,23][side],'upper arm/twist collapse'
        if 'ForeArm' in n or 'Elbow' in n:return [19,24][side],'forearm/twist collapse'
        if 'Hand' in n:return [20,25][side],'hand'
        if 'Finger' in n:return [21,27][side],'fingers collapsed to PSP hand end'
        if 'Thigh' in n or 'RepairPelvis' in n:return [38,42][side],'thigh/repair collapse'
        if 'Calf' in n or 'knee' in n:return [39,43][side],'calf/knee collapse'
        if 'Foot' in n:return [40,44][side],'ankle'
        if 'Toe' in n:return [41,45][side],'toe'
        if n.startswith('HairBone'):
            if n.startswith('HairBoneF'):return 4,'front hair follows head'
            chain=[7,8,9,10] if bone['position'][0]>=0 else [11,12,13]
            depth=max(0,min(.999,(1.53-bone['position'][1])/.82))
            return chain[int(depth*len(chain))],'hair chain by height and side'
        if n.startswith('CloakBone'):
            if 'M' in n or n.endswith('00'):return 29,'coat root'
            return (30 if bone['position'][0]>=0 else 31),'coat side; original PGR cloth dynamics not preserved'
        if n.startswith(('Oppein','Zipper','Bow')):return 2,'torso accessory collapse'
        if n.startswith('Streamer'):return 0,'waist streamer collapse'
        raise ValueError('Unmapped PGR bone '+n)
    converted=[];rules=[]
    for part in src['parts']:
        p=np.array(part['positions']).reshape(-1,3);normal=np.array(part['normals']).reshape(-1,3);weights=np.array(part['weights']);joints=np.array(part['joints'])
        fitted=warp(p)
        slope=np.diff(ty)/np.diff(sy);segments=np.clip(np.searchsorted(sy,p[:,1],side='right')-1,0,len(slope)-1)
        normal=normal/np.stack([np.full(len(p),scale),slope[segments],np.full(len(p),scale)],axis=1)
        mapping=[]
        for bone in part['bones']:
            target,reason=target_bone(bone);mapping.append(target);rules.append(dict(part=part['name'],source=bone['name'],psp_bone=target,rule=reason))
        # Fit arm rest pose using only source arm influences; torso/coat stay on vertical landmark fit.
        for side in ['L','R']:
            mask=np.array([any(k in x['name'] for k in [side+'UpperArm',side+'ForeArm',side+'Hand',side+'Finger','ElbowBone'+side]) for x in part['bones']])
            influence=(mask[joints]*weights).sum(axis=1)
            a,t,m=arms[side];transformed=(fitted-a)@m.T+t
            fitted=fitted*(1-influence[:,None])+transformed*influence[:,None]
            inv=np.linalg.inv(m);transformed_n=normal@inv
            normal=normal*(1-influence[:,None])+transformed_n*influence[:,None]
        normal/=np.maximum(np.linalg.norm(normal,axis=1,keepdims=True),1e-12)
        mapped=np.array(mapping)[joints];jw=[];ww=[]
        for js,ws in zip(mapped,weights):
            acc={}
            for j,w in zip(js,ws):
                if w>1e-7:acc[int(j)]=acc.get(int(j),0)+float(w)
            ordered=sorted(acc.items(),key=lambda x:(-x[1],x[0]));total=sum(w for j,w in ordered)
            assert 1<=len(ordered)<=4 and abs(total-1)<.001
            jw.append([j for j,w in ordered]+[0]*(4-len(ordered)));ww.append([w/total for j,w in ordered]+[0]*(4-len(ordered)))
        suffix=part['name'].removeprefix('R2BlackrockMd010011');texname='Eyes' if suffix=='Eye' else suffix
        tex=R/f'extracted/role/body/r2blackrockmd010011/R2BlackrockMd010011{texname}.png';assert tex.exists()
        converted.append(dict(name=part['name'],positions=fitted.reshape(-1).tolist(),normals=normal.reshape(-1).tolist(),uvs=part['uvs'],indices=part['indices'],joints=jw,weights=ww,texture_path=str(tex),texture='data:image/png;base64,'+base64.b64encode(tex.read_bytes()).decode()))
    candidate=dict(name='퍼니싱 얼굴·의상 · PSP 뼈대 변환 후보',id='PGR_PSP_RIG_CANDIDATE',meshes=converted,bones=[dict(index=i,parent=psp['bones'][i]['parent'],inverse_bind=inverse[i].T.reshape(-1).tolist(),rest_matrix=rest[i].T.reshape(-1).tolist()) for i in range(47)])
    (OUT/'pgr_on_psp_skin.json').write_text(json.dumps(candidate,separators=(',',':')),encoding='utf-8')
    report=dict(scope='Offline prototype skin remapping; not installed or runtime verified',source_skin_sha256=hashlib.sha256((OUT/'pgr_skin_source.json').read_bytes()).hexdigest(),psp_sha256=psp['source_sha256'],landmarks_source_y=sy.tolist(),landmarks_target_y=ty.tolist(),bone_rules=rules,vertices=sum(len(p['positions'])//3 for p in converted),triangles=sum(len(p['indices'])//3 for p in converted),psp_bones=47,limitations=['PGR fingers/cloth/twist/hair chains collapsed to PSP bones','Original PGR facial blendshapes not transplanted','Rest fit and animation deformation require visual/game verification'],game_installed=False)
    (OUT/'retarget_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['scope','vertices','triangles','psp_bones','game_installed']},ensure_ascii=False))

if __name__=='__main__':main()
