"""Hash-bound PPSSPP 64 MiB test build. Preserve the PGR model bytes exactly."""
from pathlib import Path
import hashlib,json,struct,sys,shutil
from capstone import Cs,CS_ARCH_MIPS,CS_MODE_MIPS32,CS_MODE_LITTLE_ENDIAN
G=Path('P:/AI/Codex/projects/black-rock-shooter-hd-retexture')
B=G/'release/combined-test-20260924-001005'
D=G/'workspace/model_port/diagnostics/combined-20260924'
A=Path('P:/AI/Codex/work_archive/2026-07-25/new-chat-2/work')
sys.path.insert(0,str(A/'patch_pipeline'))
from brs_patch import Iso9660
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4194304),b''):h.update(b)
    return h.hexdigest()
def sfo_read(b):
    magic,version,keys,data,count=struct.unpack_from('<5I',b)
    assert magic==0x46535000 and version==0x101
    rows=[]
    for i in range(count):
        key,fmt,length,maximum,offset=struct.unpack_from('<HHIII',b,20+16*i)
        name=b[keys+key:b.index(0,keys+key)].decode('ascii')
        rows.append((name,fmt,length,maximum,b[data+offset:data+offset+maximum]))
    return rows
def sfo_large_memory(b):
    rows=sfo_read(b);old={r[0]:r[1:] for r in rows}
    rows=[r for r in rows if r[0]!='MEMSIZE']+[('MEMSIZE',0x404,4,4,struct.pack('<I',1))]
    rows.sort(key=lambda r:r[0]);keys=bytearray();data=bytearray();entries=bytearray()
    for name,fmt,length,maximum,value in rows:
        data.extend(b'\0'*((-len(data))%4))
        entries+=struct.pack('<HHIII',len(keys),fmt,length,maximum,len(data))
        keys+=name.encode()+b'\0';data+=value
    ko=20+len(entries);do=(ko+len(keys)+3)//4*4
    out=struct.pack('<5I',0x46535000,0x101,ko,do,len(rows))+entries+keys+b'\0'*(do-ko-len(keys))+data
    new={r[0]:r[1:] for r in sfo_read(out)}
    assert all(new[k]==v for k,v in old.items() if k!='MEMSIZE')
    assert new['MEMSIZE'][-1]==struct.pack('<I',1)
    return out

source=D/'BRS_combined_model_loader_fix.iso'
assert sha(source)=='b76505a511ae02cfac9440acc9743f8430466bd89c90aa0fe02b178c1567e3d9'
elf_source=B/'memstick/PSP/SYSTEM/DUMP/NPUH10126_EBOOT.BIN'
original=elf_source.read_bytes();elf=bytearray(original)
h=struct.unpack_from('<16sHHIIIIIHHHHHH',elf)
assert h[0][:7]==b'\x7fELF\x01\x01\x01' and h[1:4]==(0xffa0,8,1)
segments=[struct.unpack_from('<8I',elf,h[5]+i*h[9]) for i in range(h[10])]
def offset(address):
    relative=address-0x08804000
    hits=[p[1]+relative-p[2] for p in segments if p[0]==1 and p[2]<=relative<p[2]+p[4]]
    assert len(hits)==1
    return hits[0]
changes=[
    (0x08804100,0x3c040030,0x3c040078,'Shared load arena: 3 MiB to 7.5 MiB; existing first 1.5 MiB preserved'),
    (0x0884086c,0x00a08025,0x3c100060,'Model heap constructor: size 6 MiB; caller base remains arena + 1.5 MiB'),
    (0x08969638,0x01480000,0x01c80000,'Main heap backing: 20.5 MiB to 28.5 MiB within declared 64 MiB RAM'),
    (0x08974c98,0x00005400,0x00007400,'SDK C heap reservation in KiB: 21 MiB to 29 MiB; preserves original 0.5 MiB headroom'),
]
md=Cs(CS_ARCH_MIPS,CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN)
report_changes=[];allowed=set()
for address,old,new,why in changes:
    at=offset(address);assert struct.unpack_from('<I',elf,at)[0]==old,(hex(address),elf[at:at+4].hex())
    struct.pack_into('<I',elf,at,new);allowed.update(range(at,at+4))
    row=dict(address=hex(address),file_offset=at,before=hex(old),after=hex(new),reason=why)
    if address<0x08900000:
        row['before_instruction']=[f'{i.mnemonic} {i.op_str}' for i in md.disasm(struct.pack('<I',old),address)]
        row['after_instruction']=[f'{i.mnemonic} {i.op_str}' for i in md.disasm(struct.pack('<I',new),address)]
        assert len(row['before_instruction'])==len(row['after_instruction'])==1
    report_changes.append(row)
assert all(i in allowed for i,(a,b) in enumerate(zip(original,elf)) if a!=b)
assert len(elf)==len(original)
output=D/'BRS_combined_model_memory_fix_v2.iso'
assert not output.exists()
with Iso9660(source) as src:
    model_path='PSP_GAME/USRDIR/GAMEDATA/FLD/FCHR/FCHR_P_BRS02.BIN'
    model=src.read_entry(src.get(model_path))
    assert hashlib.sha256(model).hexdigest()=='d711234f6c86f771c9730eefbfc0b0e2621a8e88a26c3f9a2833f2b95203a597'
    sfo=sfo_large_memory(src.read_entry(src.get('PSP_GAME/PARAM.SFO')))
    shutil.copyfile(source,output)
    with Iso9660(output,True) as dst:
        edits=[dst.patch_entry(dst.get('PSP_GAME/SYSDIR/EBOOT.BIN'),bytes(elf),'relocate'),dst.patch_entry(dst.get('PSP_GAME/PARAM.SFO'),bytes(sfo),'relocate')]
        dst.finish_volume()
    with Iso9660(output) as dst:
        assert dst.read_entry(dst.get(model_path))==model
        assert dst.read_entry(dst.get('PSP_GAME/SYSDIR/EBOOT.BIN'))==elf
        assert dst.read_entry(dst.get('PSP_GAME/PARAM.SFO'))==sfo
        for a,b in zip(src.entries,dst.entries):
            assert a.path==b.path and a.flags==b.flags
            if a.path not in ('PSP_GAME/SYSDIR/EBOOT.BIN','PSP_GAME/PARAM.SFO'):assert (a.extent,a.size)==(b.extent,b.size)
(D/'EBOOT_model_memory_fix_v2.BIN').write_bytes(elf)
report=dict(status='static_validated_runtime_pending',source=str(source),source_sha256=sha(source),output=str(output),output_sha256=sha(output),elf_source_sha256=hashlib.sha256(original).hexdigest(),elf_output_sha256=hashlib.sha256(elf).hexdigest(),changes=report_changes,iso_edits=edits,model_byte_exact=True,model_sha256=hashlib.sha256(model).hexdigest(),other_iso_files_preserved=True,requires_64mb_memory=True,runtime_verified=False)
(D/'model-memory-fix-v2-build.json').write_text(json.dumps(report,indent=2),'utf8')
print(json.dumps(report))
