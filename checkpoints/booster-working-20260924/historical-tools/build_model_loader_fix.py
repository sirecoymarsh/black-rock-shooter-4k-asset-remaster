"""Synchronize the existing PGR model with SYSTEM.VOL's RVLS and install data."""
from pathlib import Path
import sys,hashlib,struct,shutil,json,gzip
G=Path('P:/AI/Codex/projects/black-rock-shooter-hd-retexture')
A=Path('P:/AI/Codex/work_archive/2026-07-25/new-chat-2/work')
D=G/'workspace/model_port/diagnostics/combined-20260924'
SOURCE=G/'release/combined-test-20260924-001005/BRS_4K_combined_test.iso'
DEST=D/'BRS_combined_model_loader_fix.iso'
sys.path.insert(0,str(A/'patch_pipeline'))
from brs_patch import Iso9660,Rtdp
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(4194304),b''):h.update(block)
    return h.hexdigest()
assert sha(SOURCE)=='ffd94390d4f0703a5ba4c2fe66e15cf576215ffaabf588a2a0574cdb7398dd42'
assert not DEST.exists()
model_path='PSP_GAME/USRDIR/GAMEDATA/FLD/FCHR/FCHR_P_BRS02.BIN'
system_path='PSP_GAME/USRDIR/GAMEDATA/SYSTEM.VOL'
install_path='PSP_GAME/INSDIR/INSTDAT.VLD'
with Iso9660(SOURCE) as iso:
    model=iso.read_entry(iso.get(model_path))
    assert hashlib.sha256(model).hexdigest()=='d711234f6c86f771c9730eefbfc0b0e2621a8e88a26c3f9a2833f2b95203a597'
    original_system=iso.read_entry(iso.get(system_path));vol=Rtdp(original_system)
    item=next(x for x in vol.items if x.name=='instdat.vls')
    old_index=bytes(x^0x55 for x in vol.payload(item));index=bytearray(old_index)
    assert index[:4]==b'RVLS'
    count=struct.unpack_from('<I',index,8)[0]
    matching=[32+60*i for i in range(count) if index[32+60*i:64+60*i].split(b'\0')[0]==b'FCHR_P_BRS02.BIN']
    assert len(matching)==1
    at=matching[0];old_digest=bytes(index[at+32:at+52]);old_size,old_offset=struct.unpack_from('<II',index,at+52)
    vld=bytearray(iso.read_entry(iso.get(install_path)))
    assert struct.unpack_from('<I',index,12)[0]==len(index)+len(vld)
    old_model=bytes(v^old_digest[i%20] for i,v in enumerate(vld[old_offset:old_offset+old_size]))
    assert hashlib.sha1(old_model).digest()==old_digest
    assert old_model==(A/'full_extracted'/model_path).read_bytes()
    assert old_size==322859 and len(model)==727157
    # Append exactly one new encoded payload. All old install payloads stay byte-exact.
    new_offset=(len(vld)+15)//16*16;vld.extend(b'\0'*(new_offset-len(vld)))
    digest=hashlib.sha1(model).digest();vld.extend(bytes(v^digest[i%20] for i,v in enumerate(model)))
    vld.extend(b'\0'*((-len(vld))%16))
    index[at+32:at+52]=digest;struct.pack_into('<II',index,at+52,len(model),new_offset)
    struct.pack_into('<I',index,12,len(index)+len(vld))
    allowed=set(range(12,16))|set(range(at+32,at+60))
    assert all(i in allowed for i,(a,b) in enumerate(zip(old_index,index)) if a!=b)
    # Preserve every RTDP offset and byte outside the existing RVLS payload.
    system=bytearray(original_system);payload_offset=vol.data_offset+item.relative_offset
    system[payload_offset:payload_offset+item.size]=bytes(x^0x55 for x in index)
    check=Rtdp(bytes(system));assert len(system)==len(original_system)
    for other in vol.items:
        if other.index!=item.index:assert vol.payload(other)==check.payload(check.items[other.index])
    vld_path=D/'INSTDAT_model_loader_fix.VLD';vld_path.write_bytes(vld)
    (D/'SYSTEM_model_loader_fix.VOL').write_bytes(system)
    shutil.copyfile(SOURCE,DEST)
    with Iso9660(DEST,True) as out:
        system_change=out.patch_entry(out.get(system_path),bytes(system),'relocate')
        install_change=out.patch_entry(out.get(install_path),bytes(vld),'relocate')
        out.finish_volume()
    with Iso9660(DEST) as out:
        assert out.read_entry(out.get(model_path))==model
        assert out.read_entry(out.get(system_path))==system
        assert out.read_entry(out.get(install_path))==vld
        assert bytes(v^digest[i%20] for i,v in enumerate(vld[new_offset:new_offset+len(model)]))==model
        for src,dst in zip(iso.entries,out.entries):
            assert src.path==dst.path and src.flags==dst.flags
            if src.path not in (system_path,install_path):assert (src.extent,src.size)==(dst.extent,dst.size)
    report=dict(status='metadata_consistency_fixed_runtime_retest_pending',source=str(SOURCE),source_sha256=sha(SOURCE),output=str(DEST),output_sha256=sha(DEST),model_geometry_unchanged=True,model_sha256=hashlib.sha256(model).hexdigest(),model_decompressed_sha256=hashlib.sha256(gzip.decompress(model)).hexdigest(),rvls_record_offset=at,old_compressed_size=old_size,new_compressed_size=len(model),old_install_offset=old_offset,new_install_offset=new_offset,system_change=system_change,install_change=install_change,other_files_preserved=True,runtime_verified=False)
    (D/'model-loader-fix-build.json').write_text(json.dumps(report,indent=2),'utf8')
    print(json.dumps(report))
