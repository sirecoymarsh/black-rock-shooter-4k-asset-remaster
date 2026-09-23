"""Bounded INSM reader and geometry round-trip audit for local BRS assets.

Format leads: chrrox/Noesis BRS reader preserved in https://guramori.tistory.com/380;
BRS-PSP-Research-Initiative INSM notes. All interpretations are validated against
the local revision. Does not execute downloaded scripts or modify game inputs.
"""
from pathlib import Path
import base64, collections, gzip, hashlib, json, math, struct, sys

ROOT = Path(r'P:\AI\Codex\projects\black-rock-shooter-hd-retexture')
ARCH = Path(r'P:\AI\Codex\work_archive\2026-07-25\new-chat-2\work')
OUT = ROOT / 'workspace/model_port'

def sha(b): return hashlib.sha256(b).hexdigest()
def align(n, a): return (n+a-1)//a*a

def layout(vt):
    uv, col, norm, pos, wt = vt&3, vt>>2&7, vt>>5&3, vt>>7&3, vt>>9&3
    nw, morph, idx, through = (vt>>14&7)+1, (vt>>18&7)+1, vt>>11&3, vt>>23&1
    assert pos == 3 and wt == 3 and norm == 1 and uv == 2
    assert morph == 1 and idx == 0 and through == 0 and col in (0,6)
    o=0; fields={}
    for name, count, sz in [('weight',nw,4),('uv',2,2),('color',1,2 if col else 0),('normal',3,1),('position',3,4)]:
        if not sz: continue
        o=align(o,sz);fields[name]=o;o+=count*sz
    return {'fields':fields,'stride':align(o,4),'weights':nw,'color_type':col}

def decode(name, raw=None, texture_paths=None):
    source=ARCH/'full_extracted/PSP_GAME/USRDIR/GAMEDATA/FLD/FCHR'/f'{name}.BIN'
    raw=source.read_bytes() if raw is None else raw; sc=gzip.decompress(raw)
    # SC section 1 offset + its 16-byte descriptor; independently check magic.
    start=struct.unpack_from('<I',sc,8)[0]+16
    assert sc[:2]==b'SC' and sc[start:start+4]==b'INSM'
    end=struct.unpack_from('<I',sc,12)[0]
    assert start<end<=len(sc)
    b=sc[start:end]; h=struct.unpack_from('<8BI10I',b,4)
    _,tc,mc,_,bc,gc,_,_,dc,ma,da,ba,ga,mga,ta,va,ds,bs,ta2=h
    assert ta==ta2 and da-ma==mc*36 and ba-da==dc*8 and ga-ba==bc*32
    materials=[struct.unpack_from('<4B8I',b,ma+i*36) for i in range(mc)]
    states=[]
    for material in materials:
        o=material[4];state={}
        while True:
            word=struct.unpack_from('<I',b,o)[0];o+=4
            if word>>24==0x0b:break
            assert o<=va+ds
            state[f'{word>>24:02x}']=word&0xffffff
        states.append(state)
    draws=[struct.unpack_from('<4BI',b,da+i*8) for i in range(dc)]
    ends=[x[4] for x in draws[1:]]+[materials[0][4]]
    bones=[]
    for i in range(bc):
        off=ba+i*32; flags,ident,parent,next_=struct.unpack_from('<4b',b,off)
        pos=struct.unpack_from('<3f',b,off+4);quat=struct.unpack_from('<4f',b,off+16)
        assert parent<i or parent==-1
        assert abs(sum(x*x for x in quat)-1)<1e-4
        bones.append(dict(index=i,flags=flags,semantic_id=ident,parent=parent,next=next_,position=pos,quaternion=quat))
    groups=[]
    for i in range(gc):
        n,j,ptr,dest=struct.unpack_from('<HHII',b,ga+12*i)
        assert 0<=j<bc and ptr+n*4<=va and dest+64<=mga
        groups.append(dict(index=i,transform_index=j,patch_offsets=struct.unpack_from('<'+'I'*n,b,ptr),matrix_offset=dest,inverse_bind=struct.unpack_from('<16f',b,dest)))
    refs=sorted((r,g['transform_index']) for g in groups for r in g['patch_offsets'])
    assert len(refs)==len(set(r for r,j in refs))==sum(d[1] for d in draws)
    ri=0;last_ref=-56
    parts=[]; record_offsets={}; layouts=collections.Counter(); command_types=collections.Counter(); vertex_ranges=[]
    rebuilt=bytearray(b)
    for di,(d,end) in enumerate(zip(draws,ends)):
        flags,nw,mat,unk,cmd=d; assert 0<=mat<mc and cmd>=va
        palette_refs=refs[ri:ri+nw];ri+=nw
        extra=(52 if flags&1 else 0)+(8 if flags&4 else 0)+(16 if flags&8 else 0)
        assert flags&~13==0
        assert palette_refs[0][0]-last_ref==68+extra
        assert all(v[0]-u[0]==56 for u,v in zip(palette_refs,palette_refs[1:]))
        last_ref=palette_refs[-1][0]
        palette=[j for r,j in palette_refs]
        origin,cull=struct.unpack_from('<II',b,cmd)
        assert (end-cmd-12)%16==0 and origin==0x14000000 and cull in (0x1d000000,0x1d000001),(di,end-cmd,origin,cull)
        strips=[];positions=[];normals=[];uvs=[];colors=[];weights=[];indices=[];locs=[]
        for so in range(cmd+8,end-4,16):
            typ,base,addr,prim=struct.unpack_from('<4I',b,so)
            assert typ>>24==0x12 and base>>24==0x10 and addr>>24==1 and prim>>24==4
            assert base&0xffffff==0
            vt=typ&0xffffff;l=layout(vt);assert l['weights']==nw
            count=prim&0xffff; primitive=prim>>16&7;assert primitive in (3,4)
            vp=cmd+(addr&0xffffff);assert 0<=vp and vp+l['stride']*count<=ta
            vertex_ranges.append((vp,vp+l['stride']*count)); command_types[primitive]+=1
            first=len(positions)//3
            for vi in range(count):
                off=vp+vi*l['stride'];f=l['fields'];p=struct.unpack_from('<3f',b,off+f['position'])
                n=struct.unpack_from('<3b',b,off+f['normal']);u=struct.unpack_from('<2H',b,off+f['uv'])
                w=struct.unpack_from('<'+'f'*nw,b,off)
                assert all(math.isfinite(x) and abs(x)<1000 for x in p)
                assert all(-1e-6<=x<=1.00001 for x in w) and abs(sum(w)-1)<2e-4
                positions.extend(p);normals.extend(x/128 for x in n);uvs.extend(x/32768 for x in u);weights.append(w);locs.append(off)
                c=struct.unpack_from('<H',b,off+f['color'])[0] if l['color_type'] else 0xffff
                colors.extend(((c>>(i*4))&15)/15 for i in range(4))
                struct.pack_into('<3f',rebuilt,off+f['position'],*p)
                record_offsets[off]=dict(offset=off,stride=l['stride'],position_offset=off+f['position'],normal_offset=off+f['normal'],uv_offset=off+f['uv'],weights=nw)
            if primitive==4:
                for k in range(count-2):
                    tri=[first+k,first+k+1,first+k+2]
                    if k%2:tri[0],tri[1]=tri[1],tri[0]
                    indices.extend(tri)
            else:
                assert count%3==0
                indices.extend(range(first,first+count))
            layouts[f'{vt:06x}/{l["stride"]}']+=count
            strips.append(dict(command_offset=so,vertex_offset=vp,count=count,vtype=vt,stride=l['stride'],primitive=primitive))
        assert struct.unpack_from('<I',b,end-4)[0]>>24==0x0b
        parts.append(dict(name=f'PSP_draw_{di:03d}',draw=di,material=mat,texture_index=materials[mat][1],material_state=states[mat],flags=flags,cull=bool(cull&1),weights_per_vertex=nw,bone_palette=palette,positions=positions,normals=normals,uvs=uvs,colors=colors,weights=weights,indices=indices,vertex_offsets=locs,strips=strips))
    assert last_ref+60==bs
    assert bytes(rebuilt)==b,'unchanged geometry round trip altered bytes'
    textures=[]
    for i in range(tc):
        p=Path(texture_paths[i]) if texture_paths is not None else ROOT/f'workspace/stella_hd/variants/{name}_{i:02d}.png';assert p.exists()
        textures.append('data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode())
    for part in parts:part['texture']=textures[part['texture_index']]
    report=dict(name=name,source=str(source),source_sha256=sha(raw),sc_sha256=sha(sc),insm_offset=start,insm_length=len(b),counts=dict(textures=tc,materials=mc,bones=bc,matrix_groups=gc,draws=dc,submitted_vertices=sum(len(p['positions'])//3 for p in parts),triangles=sum(len(p['indices'])//3 for p in parts),unique_vertex_records=len(record_offsets)),header=h,material_states=states,vertex_layouts=dict(layouts),primitives=dict(command_types),unchanged_geometry_roundtrip_sha256=sha(bytes(rebuilt)),unchanged_geometry_roundtrip_exact=True,roundtrip_scope='All decoded position floats repacked into a copy; exact INSM bytes unchanged. Not a complete serializer/runtime test.',bone_palette_layout_verified=True,bone_palette_layout_scope='Sorted patch offsets partition into draw weight counts; all within/between-draw strides and scratch allocation size match. Runtime animation not yet checked.',bone_mapping_verified=False,animation_verified=False,game_installed=False,bones=bones,matrix_groups=groups)
    return parts,report,record_offsets

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    models=[];reports=[]
    for name,label in [('FCHR_P_BRS00','PSP 노멀 슈트'),('FCHR_P_BRS02','PSP 부스터 유닛')]:
        parts,report,records=decode(name)
        (OUT/f'{name}_geometry.json').write_text(json.dumps(parts,separators=(',',':')),encoding='utf-8')
        (OUT/f'{name}_structure.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        (OUT/f'{name}_vertex_records.json').write_text(json.dumps(list(records.values()),indent=2),encoding='utf-8')
        reports.append(report)
        models.append(dict(name=label,id=name,meshes=[{k:p[k] for k in ['name','draw','material','material_state','texture_index','flags','cull','positions','normals','uvs','colors','indices','texture']} for p in parts]))
        print(json.dumps({k:report[k] for k in ['name','counts','vertex_layouts','primitives','unchanged_geometry_roundtrip_exact']}))
    (OUT/'psp_models.json').write_text(json.dumps(models,separators=(',',':')),encoding='utf-8')

if __name__=='__main__':main()
