"""Walk bounded SC sections and STCM texture tables in the fixed ISO's FLD/MAP roots."""
import sys,json,gzip,hashlib,struct,re,collections
from pathlib import Path
import numpy as np
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf8')
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,'P:/AI/Codex/work_archive/2026-07-25/new-chat-2/work/patch_pipeline')
from brs_patch import Iso9660
from ptmd_expanded import decode
Q=R/'qa/field_map_inventory.json'
if Q.exists():raise SystemExit('Existing inventory; create a new revision.')
O=R/'workspace/source/field_maps';O.mkdir(parents=True,exist_ok=True)
probe=json.loads((R/'qa/field_map_format_probe.json').read_text('utf8'))
roots=[];containers=[];textures=[];other=[];failures=[];sc_counts=collections.Counter()
def sha(b):return hashlib.sha256(b).hexdigest()
def texture(data,rel,origin):
    p=O/(rel+'.ptm');p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    row={'id':rel,'origin':origin,'source':str(p),'source_sha256':sha(data),'size':len(data),'consumer_status':'SC/STCM table-bound source only; material/scene/UV and protagonist exclusions not yet resolved','runtime_verified':False,'release_eligible':False}
    try:
        im,details=decode(data);png=p.with_suffix('.png');im.save(png);a=np.asarray(im.getchannel('A'))
        row.update(details,png=str(png),width=im.width,height=im.height,rgba_sha256=sha(im.tobytes()),alpha_min=int(a.min()),alpha_max=int(a.max()),opaque_fraction=float((a==255).mean()),status='decoded source; visual classification and consumer review pending')
    except (ValueError,AssertionError,struct.error) as exc:
        row.update(status='decode failed',error=str(exc));failures.append({'id':rel,'kind':'texture_decode','error':str(exc)})
    textures.append(row)
def visit(b,rel,origin,depth=0):
    assert depth<=10
    if b[:2]==b'SC' and len(b)>=4:
        rec={'id':rel,'origin':origin,'magic':b[:4].hex(),'size':len(b),'sha256':sha(b),'type':'SC','table_verified':False}
        try:
            count=struct.unpack_from('<H',b,2)[0];assert count in (8,16,32),('unverified SC count',count)
            end=4+4*(count+1);header=(end+15)&~15
            offsets=list(struct.unpack_from('<'+str(count+1)+'I',b,4))
            assert offsets[0]==header and offsets[-1]==len(b)
            assert offsets==sorted(offsets) and all(header<=v<=len(b) for v in offsets)
            assert not any(b[end:header]),'Nonzero SC header padding'
            parts=[b[a:z] for a,z in zip(offsets,offsets[1:])]
            assert b[:header]+b''.join(parts)==b
            rec.update(slot_count=count,offsets=offsets,table_verified=True,partition_exact=True,empty_slots=[i for i,p in enumerate(parts) if not p]);containers.append(rec);sc_counts[count]+=1
            for i,p in enumerate(parts):
                if p:visit(p,rel+f'/sc{i:02d}',{'parent':rel,'slot':i,'offset':offsets[i],'size':len(p)},depth+1)
        except (ValueError,AssertionError,struct.error) as exc:
            rec['error']=str(exc)
            if not rec['table_verified']:containers.append(rec)
            failures.append({'id':rel,'kind':'SC_table','error':str(exc)})
    elif b[:4]==b'STCM':
        rec={'id':rel,'origin':origin,'magic':'5354434d','size':len(b),'sha256':sha(b),'type':'STCM','table_verified':False}
        try:
            assert len(b)>=0x30 and b[4]==1
            count=b[5];assert struct.unpack_from('<I',b,16)[0]==0x30+4*count
            offsets=list(struct.unpack_from('<'+str(count)+'I',b,0x30))
            assert offsets==sorted(set(offsets))
            if offsets:assert offsets[0]==struct.unpack_from('<I',b,28)[0]
            assert offsets==[m.start() for m in re.finditer(b'PTMD',b)],'Unbound texture signature or inconsistent table'
            assert all(0x30+count*4<=v<len(b) for v in offsets)
            rec.update(texture_count=count,texture_offsets=offsets,table_verified=True);containers.append(rec)
            for i,start in enumerate(offsets):
                finish=offsets[i+1] if i+1<count else len(b)
                texture(b[start:finish],rel+f'/tex{i:03d}',{'parent':rel,'table_index':i,'offset':start,'size':finish-start})
        except (ValueError,AssertionError,struct.error) as exc:
            rec['error']=str(exc)
            if not rec['table_verified']:containers.append(rec)
            failures.append({'id':rel,'kind':'STCM_table','error':str(exc)})
    elif b[:4]==b'PTMD':texture(b,rel,origin)
    else:other.append({'id':rel,'origin':origin,'magic':b[:4].hex(),'size':len(b),'sha256':sha(b),'status':'Table-bounded non-SC/non-STCM/non-PTMD leaf; not excluded from game scope'})
with Iso9660(Path(probe['iso']['path']),writable=False) as iso:
    found=[e for k,e in iso.by_path.items() if '/gamedata/fld/map/' in k and not e.is_dir]
    assert {e.path for e in found}=={r['iso_path'] for r in probe['roots']}
    for root in probe['roots']:
        e=iso.by_path[root['iso_path'].lower()];raw=iso._read_at(e.extent*2048,e.size)
        assert sha(raw)==root['source_sha256'];b=gzip.decompress(raw);assert sha(b)==root['decoded_sha256']
        rel=Path(e.path).name.lower();p=O/rel/'source.sc';p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
        roots.append({**root,'decoded_source':str(p)})
        visit(b,rel,{'iso_path':e.path,'source_sha256':sha(raw),'decoded_sha256':sha(b),'transform':'gzip'})
        print('FIELD',rel,'textures',len(textures),flush=True)
unique={};battle=json.loads((R/'qa/battle_sr_catalog.json').read_text('utf8'))
bg={(g['width'],g['height'],g['rgba_sha256']):g['group_id'] for g in battle['groups']}
for row in textures:
    if 'png' not in row:continue
    key=(row['width'],row['height'],row['rgba_sha256'])
    if key not in unique:unique[key]={'group_id':f'FM{len(unique)+1:04d}','width':key[0],'height':key[1],'rgba_sha256':key[2],'representative':row['id'],'members':[],'battle_pixel_equivalent_group':bg.get(key),'equivalence_limitation':'Exact dimensions/RGBA only; not shared UV, material, scene or replacement-key proof.','local_sr_attempted':False,'candidate':None,'runtime_verified':False,'release_eligible':False}
    unique[key]['members'].append(row['id'])
summary={'field_map_roots':len(roots),'sc_containers':sum(c['type']=='SC' for c in containers),'stcm_containers':sum(c['type']=='STCM' for c in containers),'table_bound_textures':len(textures),'decoded':sum('png' in t for t in textures),'unique_rgba_groups':len(unique),'groups_equal_to_battle_pixels':sum(bool(g['battle_pixel_equivalent_group']) for g in unique.values()),'unclassified_leaves':len(other),'failures':len(failures)}
report={'schema':'brs-field-map-inventory/v1','iso':probe['iso'],'scope':'All fixed-ISO FLD/MAP roots; source decoding only. Not all game assets and not accepted remasters.','summary':summary,'roots':roots,'containers':containers,'sc_slot_count_population':dict(sc_counts),'textures':textures,'groups':list(unique.values()),'unclassified_leaves':other,'failures':failures,'parser_source_sha256':sha(Path(__file__).read_bytes()),'ptmd_decoder_source_sha256':sha((R/'tools/ptmd_expanded.py').read_bytes()),'runtime_verified':False,'all_game_complete':False}
Q.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8');print(json.dumps(summary),flush=True)
for f in failures[:12]:print(f,flush=True)
