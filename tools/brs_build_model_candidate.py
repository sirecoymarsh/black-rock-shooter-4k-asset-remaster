"""Serialize a bounded PSP INSM candidate from decoded mesh/bone records.

Keeps SC scripts/animations, all bones, original optional-draw groups and original
weapon draws. Model construction is a development PoC until runtime verified.
"""
from pathlib import Path
import json,sys,gzip,struct,hashlib,collections,math
ROOT=Path(r'P:\AI\Codex\projects\black-rock-shooter-hd-retexture')
ARCH=Path(r'P:\AI\Codex\work_archive\2026-07-25\new-chat-2\work')
sys.path.insert(0,str(ROOT/'tools'));sys.path.insert(0,str(ARCH/'ui_graphics_pipeline'))
from brs_model_port import decode,align
from ptmd_codec import PtmdTexture,encode_ptmd,decode_ptmd
from PIL import Image
OUT=ROOT/'workspace/model_port';CAND=OUT/'candidate_v1'

def original_texture_blocks(b,h):
    blocks=[];pos=h[14]
    for i in range(h[1]):
        assert b[pos:pos+4]==b'PTMD'
        count=16 if b[pos+8]==4 else 256;sz=4 if b[pos+9]==48 else 2
        end=pos+struct.unpack_from('<I',b,pos+12)[0]+count*sz
        blocks.append(b[pos:end]);pos=align(end,16)
    assert pos==len(b)
    return blocks

def fallback_texture(path):
    # Game-format encoding only. Full original PGR PNG is retained for HD loading.
    image=Image.open(path).convert('RGBA').resize((256,256),Image.Resampling.LANCZOS)
    q=image.quantize(colors=256,method=Image.Quantize.FASTOCTREE,dither=Image.Dither.NONE)
    rgba=q.convert('RGBA').tobytes();ids=q.tobytes();pal=[(0,0,0,0)]*256
    for i,k in enumerate(ids):pal[k]=tuple(rgba[4*i:4*i+4])
    header=b'PTMD'+bytes([2,1,0,0x81,5,0x30,0,0])+struct.pack('<I',65552)
    tex=PtmdTexture(header,256,256,5,48,65552,ids,tuple(pal));encoded=encode_ptmd(tex)
    assert decode_ptmd(encoded).rgba_bytes==rgba
    return encoded

def source_draws(parts):
    out=[]
    for p in parts:
        verts=[]
        pos=p['positions'];nor=p['normals'];uv=p['uvs'];colors=p['colors']
        for i in p['indices']:
            verts.append((pos[3*i:3*i+3],nor[3*i:3*i+3],uv[2*i:2*i+2],p['weights'][i],colors[4*i:4*i+4]))
        out.append(dict(material=p['material'],flags=p['flags'],palette=p['bone_palette'],cull=p['cull'],verts=verts,label=p['name']))
    return out

def pgr_draws(candidate,start_material):
    result=[];triangle_counts=[]
    for pi,p in enumerate(candidate['meshes']):
        palette=set();tris=[];batches=[]
        def flush():
            nonlocal palette,tris
            if tris:batches.append((sorted(palette),tris))
            palette=set();tris=[]
        for off in range(0,len(p['indices']),3):
            tri=p['indices'][off:off+3]
            needed={j for vi in tri for j,w in zip(p['joints'][vi],p['weights'][vi]) if w>1e-7}
            assert len(needed)<=8,('triangle exceeds PSP bone palette',p['name'],off,len(needed))
            if len(needed|palette)>8 or len(tris)>=5000:flush()
            palette|=needed;tris.append(tri)
        flush()
        for bi,(palette,tris) in enumerate(batches):
            verts=[]
            for tri in tris:
                for i in tri:
                    weights=collections.defaultdict(float)
                    for joint,weight in zip(p['joints'][i],p['weights'][i]):
                        if weight>1e-7:weights[joint]+=weight
                    w=[weights[j] for j in palette]
                    assert abs(sum(w)-1)<1e-5
                    u,v=p['uvs'][2*i:2*i+2]
                    verts.append((p['positions'][3*i:3*i+3],p['normals'][3*i:3*i+3],[u,1-v],w,[1,1,1,1]))
            result.append(dict(material=start_material+pi,flags=12 if bi==0 else 0,palette=palette,cull=False,verts=verts,label=f'{p["name"]}_{bi}'))
        triangle_counts.append(dict(part=p['name'],triangles=len(p['indices'])//3,batches=len(batches)))
    return result,triangle_counts

def serialize(old,h,draws,textures,original_materials):
    mats=[bytearray(x) for x in original_materials]
    for ti in range(h[1],len(textures)):
        m=bytearray(mats[0]);m[1]=ti;mats.append(m)
    assert len(mats)<256 and len(textures)<256
    # Scratch layout independently matched across both original costumes.
    refs=collections.defaultdict(list);last=-56
    for d in draws:
        flags=d['flags'];extra=(52 if flags&1 else 0)+(8 if flags&4 else 0)+(16 if flags&8 else 0)
        last+=68+extra
        for i,j in enumerate(d['palette']):
            if i:last+=56
            refs[j].append(last)
    scratch_size=last+60
    ma=56;da=ma+len(mats)*36;ba=da+len(draws)*8;ga=ba+h[4]*32
    ref_base=ga+len(refs)*12;va=ref_base+sum(map(len,refs.values()))*4
    # Separate command byte ranges from vertex ranges; pointers emitted after placement.
    command_info=[];pos=va
    for d in draws:
        chunks=[d['verts'][i:i+15000] for i in range(0,len(d['verts']),15000)]
        assert chunks and all(len(x)%3==0 for x in chunks)
        command_info.append((pos,chunks));pos+=12+16*len(chunks)
    material_commands=[]
    for i in range(len(mats)):
        source_i=i if i<len(original_materials) else 0
        old_pos=struct.unpack_from('<I',original_materials[source_i],4)[0];words=[]
        while True:
            word=struct.unpack_from('<I',old,old_pos)[0];old_pos+=4;words.append(word)
            if word>>24==0xb:break
        if i>=len(original_materials):
            # PGR Hair material declares _Cutoff=0.1. Its diffuse alpha peaks
            # below 0.5, so the PSP default >=128 would discard every texel.
            is_hair=(i-len(original_materials))==4
            is_eye=(i-len(original_materials))==0
            words=[(0xdbff1a07 if is_hair and word>>24==0xdb else
                    0xdbff2607 if is_eye and word>>24==0xdb else word) for word in words]
        material_commands.append((pos,struct.pack('<'+'I'*len(words),*words)));pos+=4*len(words)
    vertex_base=align(pos,4);vertices=bytearray();gpu_chunks=[]
    for d,(cmd,chunks) in zip(draws,command_info):
        nw=len(d['palette']);has_color=any(any(c!=1 for c in v[4]) for v in d['verts']);vt=0x7a2+((nw-1)<<14)+(0x18 if has_color else 0)
        entries=[]
        for chunk in chunks:
            start=vertex_base+len(vertices)
            for p,n,uv,w,c in chunk:
                assert len(w)==nw and abs(sum(w)-1)<1e-5
                data=bytearray(struct.pack('<'+'f'*nw,*w))
                data+=struct.pack('<HH',*(round(float(x)*32768)&0xffff for x in uv))
                if has_color:data+=struct.pack('<H',sum(max(0,min(15,round(x*15)))<<(4*i) for i,x in enumerate(c)))
                data+=struct.pack('<bbb',*(max(-128,min(127,round(x*128))) for x in n))
                data+=b'\0'*((-len(data))%4);data+=struct.pack('<3f',*p);vertices+=data
            entries.append((vt,start,len(chunk)))
        gpu_chunks.append(entries)
    matrix_base=align(vertex_base+len(vertices),16)
    old_matrix_base=min(g['matrix_offset']-64*g['transform_index'] for g in PSP['matrix_groups'])
    matrix_data=old[old_matrix_base:h[13]];assert len(matrix_data)==46*64
    mga=matrix_base+len(matrix_data);group_data=old[h[13]:h[14]];assert len(group_data)==h[6]*16
    # Original optional-draw groups still address identical first draws/scratch slots.
    ta=mga+len(group_data)
    buf=bytearray(ta);buf[0:4]=b'INSM'
    nh=list(h);nh[1]=len(textures);nh[2]=len(mats);nh[5]=len(refs);nh[8]=len(draws)
    nh[9:]=[ma,da,ba,ga,mga,ta,va,vertex_base-va,scratch_size,ta]
    struct.pack_into('<8BI10I',buf,4,*nh)
    for i,(m,(cmd,words)) in enumerate(zip(mats,material_commands)):
        struct.pack_into('<I',m,4,cmd);buf[ma+i*36:ma+(i+1)*36]=m;buf[cmd:cmd+len(words)]=words
    buf[ba:ga]=old[h[11]:h[12]]
    at=ref_base
    for i,(joint,offsets) in enumerate(sorted(refs.items())):
        struct.pack_into('<HHII',buf,ga+i*12,len(offsets),joint,at,matrix_base+joint*64)
        struct.pack_into('<'+'I'*len(offsets),buf,at,*offsets);at+=len(offsets)*4
    assert at==va
    for i,(d,(cmd,chunks),entries) in enumerate(zip(draws,command_info,gpu_chunks)):
        struct.pack_into('<4BI',buf,da+8*i,d['flags'],len(d['palette']),d['material'],0,cmd)
        struct.pack_into('<II',buf,cmd,0x14000000,0x1d000000|int(d['cull']))
        for j,(vt,vertex,count) in enumerate(entries):
            relative=vertex-cmd;assert 0<=relative<0x1000000
            struct.pack_into('<4I',buf,cmd+8+16*j,0x12000000|vt,0x10000000,0x01000000|relative,0x04030000|count)
        struct.pack_into('<I',buf,cmd+8+16*len(entries),0x0b000000)
    buf[vertex_base:vertex_base+len(vertices)]=vertices
    buf[matrix_base:mga]=matrix_data;buf[mga:ta]=group_data
    for tex in textures:buf+=tex;buf+=b'\0'*((-len(buf))%16)
    return bytes(buf),dict(header=nh,size=len(buf),scratch_size=scratch_size,draws=len(draws),vertex_bytes=len(vertices))

def sc_replace(sc,start,end,new):
    delta=len(new)-(end-start);assert delta%16==0
    out=bytearray(sc[:start]+new+sc[end:]);count=struct.unpack_from('<H',sc,2)[0]
    for i in range(count+1):
        at=4+i*4;v=struct.unpack_from('<I',sc,at)[0]
        if v>=end:struct.pack_into('<I',out,at,v+delta)
    block=start-16;assert sc[block:block+4]==b'SC\1\0'
    struct.pack_into('<I',out,block+8,len(new)+16)
    assert bytes(out[start+len(new):])==sc[end:]
    check=bytearray(out[:start]);check[4:4+(count+1)*4]=sc[4:4+(count+1)*4];check[block+8:block+12]=sc[block+8:block+12]
    assert bytes(check)==sc[:start]
    return bytes(out)

def main():
    global PSP
    CAND.mkdir(parents=True,exist_ok=True)
    parts,PSP,_=decode('FCHR_P_BRS02');raw=Path(PSP['source']).read_bytes();sc=gzip.decompress(raw);start=PSP['insm_offset'];end=start+PSP['insm_length'];old=sc[start:end];h=PSP['header']
    materials=[old[h[9]+36*i:h[9]+36*(i+1)] for i in range(h[2])];textures=original_texture_blocks(old,h)
    orig=source_draws(parts)
    # Before adding PGR, prove a complete model rewrite preserves decoded content.
    rebuilt,base_info=serialize(old,h,orig,textures,materials);re_sc=sc_replace(sc,start,end,rebuilt);re_raw=gzip.compress(re_sc,compresslevel=9,mtime=0)
    check,report,_=decode('FCHR_P_BRS02',raw=re_raw)
    assert [p['bone_palette'] for p in check]==[p['bone_palette'] for p in parts]
    max_position_error=max(abs(x-y) for a,o in zip(check,orig) for x,y in zip(a['positions'],[c for v in o['verts'] for c in v[0]]))
    assert max_position_error==0
    assert all([list(w) for w in c['weights']]==[list(v[3]) for v in o['verts']] for c,o in zip(check,orig))
    assert original_texture_blocks(rebuilt,report['header'])==textures
    (CAND/'original_reencoded.BIN').write_bytes(re_raw)
    candidate=json.loads((OUT/'pgr_on_psp_skin.json').read_text());added,counts=pgr_draws(candidate,h[2])
    for i,(p,d) in enumerate(zip(parts,orig)):
        if p['texture_index']<5:
            nw=len(d['palette']);dummy=([0,0,0],[0,0,1],[0,0],[1.0]+[0.0]*(nw-1),[1,1,1,1]);d['verts']=[dummy,dummy,dummy]
    for p in candidate['meshes']:textures.append(fallback_texture(p['texture_path']))
    new,info=serialize(old,h,orig+added,textures,materials);newsc=sc_replace(sc,start,end,new);newraw=gzip.compress(newsc,compresslevel=9,mtime=0)
    texture_paths=[str(ROOT/f'workspace/stella_hd/variants/FCHR_P_BRS02_{i:02d}.png') for i in range(h[1])]+[p['texture_path'] for p in candidate['meshes']]
    # Inspect the actual game-format texture output, not only source PNGs.
    fallback_paths=[]
    for i,encoded in enumerate(textures):
        if i<h[1]:
            fallback_paths.append(texture_paths[i]);continue
        tex=decode_ptmd(encoded);tex_path=CAND/f'texture_{i:02d}.png'
        Image.frombytes('RGBA',(tex.width,tex.height),tex.rgba_bytes).save(tex_path)
        fallback_paths.append(str(tex_path))
    decoded,validated,_=decode('FCHR_P_BRS02',raw=newraw,texture_paths=fallback_paths)
    assert len(decoded)==len(orig)+len(added)
    assert len(newraw)>0 and sum(len(d['indices'])//3 for d in decoded[len(orig):])==18863
    path=CAND/'FCHR_P_BRS02_pgr_candidate.BIN';path.write_bytes(newraw)
    (CAND/'candidate_decoded_geometry.json').write_text(json.dumps(decoded,separators=(',',':')),encoding='utf-8')
    (CAND/'texture_sources.json').write_text(json.dumps(texture_paths,indent=2),encoding='utf-8')
    report=dict(scope='Full INSM+SC development candidate, not game verified',original_reencode=base_info,original_reencode_positions_exact=True,original_reencode_weights_exact=True,original_reencode_textures_exact=True,script_animation_suffix_exact=True,candidate=info,candidate_compressed_size=len(newraw),candidate_sha256=hashlib.sha256(newraw).hexdigest(),parts=counts,game_installed=False,limitations=['PGR facial blendshapes not transplanted','Original alternate hand meshes disabled; weapon meshes preserved','Accessory skin collapsed to available PSP joints; motion and clipping unverified','Memory budget and loader growth unverified'])
    (CAND/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
