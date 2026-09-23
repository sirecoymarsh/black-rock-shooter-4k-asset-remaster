"""Read-only reconstruction of failed SC slices; does not broaden the decoder."""
import collections,hashlib,json,struct
from pathlib import Path
R=Path(__file__).resolve().parents[1]
q=json.loads((R/'qa/field_map_inventory.json').read_text('utf8'))
containers={c['id']:c for c in q['containers']};rootbytes={}
def sha(b):return hashlib.sha256(b).hexdigest()
for r in q['roots']:
    b=Path(r['decoded_source']).read_bytes();assert sha(b)==r['decoded_sha256']
    rootbytes[Path(r['iso_path']).name.lower()]=b
def get(c):
    origin=c['origin']
    if 'parent' not in origin:b=rootbytes[c['id']]
    else:
        p=get(containers[origin['parent']]);b=p[origin['offset']:origin['offset']+origin['size']]
    assert len(b)==c['size'] and sha(b)==c['sha256']
    return b
rows=[]
for c in q['containers']:
    if c['table_verified']:continue
    b=get(c);n=struct.unpack_from('<H',b,2)[0]
    row={'id':c['id'],'source_sha256':sha(b),'size':len(b),'count_candidate':n,'header_hex':b[:80].hex()}
    if n>64:
        row.update(diagnosis='SC prefix overlaps an unclassified signature; not a proven SC offset table',signature=b[:4].decode('ascii',errors='replace'))
    else:
        end=4+4*(n+1);header=(end+15)&~15;offsets=list(struct.unpack_from('<'+str(n+1)+'I',b,4))
        row.update(expected_aligned_header=header,offsets=offsets,first_offset=offsets[0],last_offset=offsets[-1],trailing_bytes=len(b)-offsets[-1],monotonic=offsets==sorted(offsets),zero_header_padding=not any(b[end:header]))
        row['trailing_all_zero']=0<=offsets[-1]<=len(b) and not any(b[offsets[-1]:])
        row['diagnosis']='unsupported count' if n not in (8,16,32) else 'first offset differs from assumed aligned header' if offsets[0]!=header else 'last offset differs from parent-bounded size' if offsets[-1]!=len(b) else 'other table constraint'
    rows.append(row)
report={'schema':'brs-field-sc-failure-diagnostics/v1','source_inventory_sha256':sha((R/'qa/field_map_inventory.json').read_bytes()),'root_hashes_verified':len(rootbytes),'failed_container_slice_hashes_verified':len(rows),'failure_kinds':dict(collections.Counter(f['kind'] for f in q['failures'])),'container_counts':dict(collections.Counter(c['type']+('_verified' if c['table_verified'] else '_unverified') for c in q['containers'])),'diagnosis_counts':dict(collections.Counter(r['diagnosis'] for r in rows)),'rows':rows,'new_textures_decoded':0,'scope':'Diagnostics only; unsupported variants remain unresolved and no assets are promoted.'}
(R/'qa/field_map_sc_diagnostics.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
print(json.dumps({k:v for k,v in report.items() if k!='rows'},ensure_ascii=False))
print(json.dumps(rows[:5],ensure_ascii=False))
