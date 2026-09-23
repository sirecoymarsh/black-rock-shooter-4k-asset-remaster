"""Walk bounded SC sections and STCM texture tables in the fixed ISO's FLD/MAP roots."""
import sys,json,gzip,hashlib,struct,re,collections
from pathlib import Path
import numpy as np
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf8')
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,'P:/AI/Codex/work_archive/2026-07-25/new-chat-2/work/patch_pipeline')
from brs_patch import Iso9660
from ptmd_expanded import decode
Q=R/'qa/field_map_inventory_v2.json'
previous=json.loads((R/'qa/field_map_inventory.json').read_text('utf8'))
previous_textures={t['id']:t for t in previous['textures']}
previous_groups={(g['width'],g['height'],g['rgba_sha256']):g for g in previous['groups']}
if Q.exists():raise SystemExit('Existing inventory; create a new revision.')
O=R/'workspace/source/field_maps';O.mkdir(parents=True,exist_ok=True)
probe=json.loads((R/'qa/field_map_format_probe.json').read_text('utf8'))
roots=[];containers=[];textures=[];other=[];failures=[];sc_counts=collections.Counter()
def sha(b):return hashlib.sha256(b).hexdigest()
def texture(data,rel,origin):
    p=O/(rel+'.ptm');p.parent.mkdir(parents=True,exist_ok=True);
    if p.exists():assert p.read_bytes()==data,str(p)
    else:p.write_bytes(data)
    row={'id':rel,'origin':origin,'source':str(p),'source_sha256':sha(data),'size':len(data),'consumer_status':'SC/STCM table-bound source only; material/scene/UV and protagonist exclusions not yet resolved','runtime_verified':False,'release_eligible':False}
    try:
        im,details=decode(data);png=p.with_suffix('.png')
        if png.exists():
            from PIL import Image
            old=Image.open(png).convert('RGBA');assert old.size==im.size and old.tobytes()==im.tobytes(),str(png)
        else:im.save(png)
        a=np.asarray(im.getchannel('A'))
        row.update(details,png=str(png),width=im.width,height=im.height,rgba_sha256=sha(im.tobytes()),alpha_min=int(a.min()),alpha_max=int(a.max()),opaque_fraction=float((a==255).mean()),status='decoded source; visual classification and consumer review pending')
    except (ValueError,AssertionError,struct.error) as exc:
        row.update(status='decode failed',error=str(exc));failures.append({'id':rel,'kind':'texture_decode','error':str(exc)})
    textures.append(row)
def visit(b,rel,origin,depth=0):
    assert depth<=10
    if b[:2]==b'SC' and len(b)>=4 and b[:4]!=b'SCMP':
        rec={'id':rel,'origin':origin,'magic':b[:4].hex(),'size':len(b),'sha256':sha(b),'type':'SC','table_verified':False}
        try:
            count=struct.unpack_from('<H',b,2)[0];assert 1<=count<=32,('unverified SC count',count)
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
for root in previous['roots']:
    b=Path(root['decoded_source']).read_bytes();assert sha(b)==root['decoded_sha256']
    rel=Path(root['iso_path']).name.lower();roots.append(root)
    visit(b,rel,{'iso_path':root['iso_path'],'source_sha256':root['source_sha256'],'decoded_sha256':sha(b),'transform':'gzip; verified prior decoded root'})
    print('FIELD-V2',rel,'textures',len(textures),flush=True)
unique={};next_group=len(previous_groups)+1;battle=json.loads((R/'qa/battle_sr_catalog.json').read_text('utf8'))
bg={(g['width'],g['height'],g['rgba_sha256']):g['group_id'] for g in battle['groups']}
for row in textures:
    if 'png' not in row:continue
    key=(row['width'],row['height'],row['rgba_sha256'])
    if key not in unique:
        group_id=previous_groups[key]['group_id'] if key in previous_groups else f'FM{next_group:04d}'
        if key not in previous_groups:next_group+=1
        unique[key]={'group_id':group_id,'width':key[0],'height':key[1],'rgba_sha256':key[2],'representative':row['id'],'members':[],'battle_pixel_equivalent_group':bg.get(key),'equivalence_limitation':'Exact dimensions/RGBA only; not shared UV, material, scene or replacement-key proof.','local_sr_attempted':False,'candidate':None,'runtime_verified':False,'release_eligible':False}
    unique[key]['members'].append(row['id'])
for t in textures:
    if t['id'] in previous_textures:
        old=previous_textures[t['id']];assert t['source_sha256']==old['source_sha256'] and t.get('rgba_sha256')==old.get('rgba_sha256')
assert set(previous_textures)<=set(t['id'] for t in textures)
assert set(previous_groups)<=set(unique)
summary={'field_map_roots':len(roots),'sc_containers':sum(c['type']=='SC' for c in containers),'stcm_containers':sum(c['type']=='STCM' for c in containers),'table_bound_textures':len(textures),'decoded':sum('png' in t for t in textures),'unique_rgba_groups':len(unique),'groups_equal_to_battle_pixels':sum(bool(g['battle_pixel_equivalent_group']) for g in unique.values()),'unclassified_leaves':len(other),'failures':len(failures)}
report={'schema':'brs-field-map-inventory/v2','iso':probe['iso'],'scope':'All fixed-ISO FLD/MAP roots; source decoding only. Not all game assets and not accepted remasters.','summary':summary,'roots':roots,'containers':containers,'previous_inventory_sha256':sha((R/'qa/field_map_inventory.json').read_bytes()),'prior_texture_records_preserved':len(previous_textures),'prior_group_ids_preserved':len(previous_groups),'verified_containers':dict(collections.Counter(c['type'] for c in containers if c['table_verified'])),'sc_slot_count_population':dict(sc_counts),'textures':textures,'groups':list(unique.values()),'unclassified_leaves':other,'failures':failures,'parser_source_sha256':sha(Path(__file__).read_bytes()),'ptmd_decoder_source_sha256':sha((R/'tools/ptmd_expanded.py').read_bytes()),'runtime_verified':False,'all_game_complete':False}
Q.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8');print(json.dumps(summary),flush=True)
for f in failures[:12]:print(f,flush=True)
