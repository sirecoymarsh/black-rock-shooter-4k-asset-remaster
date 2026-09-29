"""Build the mandatory title SDO companion into a separate, hash-bound ISO."""
from pathlib import Path
import hashlib,json,shutil,sys,os
import numpy as np
sys.stdout.reconfigure(encoding='utf8')
R=Path(__file__).resolve().parents[1];G=R.parent/'black-rock-shooter-hd-retexture'
sys.path.insert(0,r'P:\AI\Codex\work_archive\2026-07-25\new-chat-2\work\patch_pipeline')
from brs_patch import Iso9660
O=R/'workspace/ui-title-ko-002';src=G/'release/combined-test-20260924-001005/BRS_4K_combined_test.iso'
dest=O/'BRS_UI_title_v2.iso';temp=O/'BRS_UI_title_v2.building.iso'
expected='b162f45f10622992a4fd068b8414008cd7f455c7c9b203c1c610554d43de9b21'
target='PSP_GAME/USRDIR/GAMEDATA/TITLE.VOL'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()
assert sha(src)==expected
m=json.loads((O/'manifest.json').read_text('utf8'));v=m['volume_patch'];payload=Path(v['output']).read_bytes()
assert hashlib.sha256(payload).hexdigest()==v['output_sha256']
with Iso9660(src) as a:
    entry=a.get(target);assert a.hash_entry(entry)==v['source_sha256']
    assert len(payload)<entry.size
    allow=[(entry.extent*2048,entry.extent*2048+((entry.size+2047)//2048)*2048),(entry.record_offset+10,entry.record_offset+18)]
    if temp.exists():raise FileExistsError(temp)
    shutil.copyfile(src,temp)
    with Iso9660(temp,True) as iso:
        change=iso.patch_entry(iso.get(target),payload,'allocation');iso.finish_volume()
    with Iso9660(temp) as b:
        assert b.read_entry(b.get(target))==payload
        assert len(a.entries)==len(b.entries)
        for x,y in zip(a.entries,b.entries):
            assert x.path==y.path and x.flags==y.flags and x.extent==y.extent
            if x.path!=target:assert x.size==y.size
    # Verify every physical byte outside TITLE's allocation and its size fields.
    changed=0;offset=0
    with src.open('rb') as fa,temp.open('rb') as fb:
        while True:
            ba=fa.read(4*1024*1024);bb=fb.read(4*1024*1024);assert len(ba)==len(bb)
            if not ba:break
            diff=np.frombuffer(ba,dtype=np.uint8)!=np.frombuffer(bb,dtype=np.uint8)
            changed+=int(diff.sum())
            for lo,hi in allow:
                x=max(0,lo-offset);y=min(len(ba),hi-offset)
                if y>x:diff[x:y]=False
            assert not diff.any(),offset
            offset+=len(ba)
os.replace(temp,dest)
report=dict(schema='brs-title-companion-iso/v1',source=str(src),source_sha256=expected,
    output=str(dest),output_sha256=sha(dest),size=dest.stat().st_size,changed_file=target,change=change,
    allowed_physical_ranges=allow,changed_byte_count=changed,unrelated_physical_bytes_exact=True,
    required_texture_pack=m['pack'],requires_title_pngs=True,runtime_verified=False,live_installation_performed=False)
(O/'iso-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(report,ensure_ascii=False))
