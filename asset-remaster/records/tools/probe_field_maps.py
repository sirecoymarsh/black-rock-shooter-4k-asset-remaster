"""Read-only fixed-ISO field map survey, with no magic-scan texture acceptance."""
import sys,json,gzip,hashlib,collections,re
from pathlib import Path
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1]
A=Path('P:/AI/Codex/work_archive/2026-07-25/new-chat-2/work')
sys.path.insert(0,str(A/'patch_pipeline'))
from brs_patch import Iso9660
Q=R/'qa/field_map_format_probe.json'
if Q.exists():raise SystemExit('Existing evidence; inspect it instead.')
identity=json.loads((R/'qa/source_identity.json').read_text('utf8'))['iso']
with Path(identity['path']).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==identity['sha256']
rows=[]
with Iso9660(Path(identity['path']),writable=False) as iso:
    entries=[e for k,e in iso.by_path.items() if '/gamedata/fld/map/' in k and not e.is_dir]
    for e in entries:
        raw=iso._read_at(e.extent*2048,e.size)
        data=gzip.decompress(raw) if raw[:2]==b'\x1f\x8b' else raw
        rows.append({'iso_path':e.path,'iso_extent':e.extent,'source_size':len(raw),'source_sha256':hashlib.sha256(raw).hexdigest(),'transform':'gzip' if raw[:2]==b'\x1f\x8b' else 'none','decoded_size':len(data),'decoded_sha256':hashlib.sha256(data).hexdigest(),'magic':data[:4].hex(),'header64':data[:64].hex(),'unbound_magic_hits':{m.decode():[x.start() for x in re.finditer(m,data)] for m in [b'STCM',b'PTMD',b'RTDP',b'LPK\x00']},'texture_tables_verified':False,'runtime_verified':False})
report={'schema':'brs-field-map-probe/v1','iso':identity,'root_count':len(rows),'decoded_magic_counts':dict(collections.Counter(r['magic'] for r in rows)),'roots':rows,'meaning':'Gzip integrity and exact ISO bytes only. Embedded magic hits are investigation leads, not accepted textures or verified consumers.','all_game_complete':False}
Q.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
print(json.dumps({'roots':len(rows),'magic_counts':report['decoded_magic_counts'],'examples':rows[:3]},ensure_ascii=False))
