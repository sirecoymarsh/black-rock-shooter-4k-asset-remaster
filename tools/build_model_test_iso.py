from pathlib import Path
import sys,hashlib,shutil,json
ROOT=Path(r'P:\AI\Codex\projects\black-rock-shooter-hd-retexture')
ARCH=Path(r'P:\AI\Codex\work_archive\2026-07-25\new-chat-2\work')
sys.path.insert(0,str(ARCH/'patch_pipeline'))
from brs_patch import Iso9660
source=ARCH/'release_build/runtime_fix_iso_20260823_test_v2/BRS_Korean_v1.0.iso'
expected='525b5d2b7d8f4723be25b026e72b69d07d30c2cf84d8a48235577ca3728fc92a'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert sha(source)==expected
entry_path='PSP_GAME/USRDIR/GAMEDATA/FLD/FCHR/FCHR_P_BRS02.BIN'
out=ROOT/'workspace/model_port/candidate_v1';reports=[]
with Iso9660(source) as source_iso:
 old=source_iso.read_entry(source_iso.get(entry_path))
 assert old==(ARCH/'full_extracted'/entry_path).read_bytes()
 original_entries=[(e.path,e.size,e.flags) for e in source_iso.entries]
 for name,payload_name in [('BRS_model_reencoded.iso','original_reencoded.BIN'),('BRS_pgr_candidate.iso','FCHR_P_BRS02_pgr_candidate.BIN')]:
  dest=out/name;payload=(out/payload_name).read_bytes()
  if dest.exists():raise FileExistsError(dest)
  shutil.copyfile(source,dest)
  with Iso9660(dest,True) as iso:
   change=iso.patch_entry(iso.get(entry_path),payload,'relocate');iso.finish_volume()
  with Iso9660(dest) as check:
   assert check.read_entry(check.get(entry_path))==payload
   # Every other ISO file extent and contents remains from the source copy.
   for a,b in zip(source_iso.entries,check.entries):
    assert a.path==b.path and a.flags==b.flags
    if a.path!=entry_path:assert a.size==b.size and a.extent==b.extent
  reports.append(dict(path=str(dest),sha256=sha(dest),source_sha256=expected,change=change))
(out/'iso_validation.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
print(json.dumps(reports,indent=2))
