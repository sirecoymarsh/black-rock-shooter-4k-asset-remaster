"""Exercise the game's captured MIPS gzip routine in an isolated Unicorn VM."""
from pathlib import Path
import gzip, hashlib, json, struct, sys, time

G=Path('P:/AI/Codex/projects/black-rock-shooter-hd-retexture')
D=G/'workspace/model_port/diagnostics'
B=G/'release/combined-test-20260924-001005'
A=Path('P:/AI/Codex/work_archive/2026-07-25/new-chat-2/work')
sys.path.insert(0,str(D/'tools'))
from unicorn import Uc, UcError, UC_ARCH_MIPS, UC_MODE_MIPS32, UC_MODE_LITTLE_ENDIAN, UC_HOOK_MEM_INVALID,UC_HOOK_CODE
from collections import deque
from unicorn.mips_const import UC_MIPS_REG_0
from unicorn.mips_const import UC_MIPS_REG_A0,UC_MIPS_REG_A1,UC_MIPS_REG_A2,UC_MIPS_REG_A3,UC_MIPS_REG_SP,UC_MIPS_REG_RA,UC_MIPS_REG_PC,UC_MIPS_REG_V0

ram=bytearray((B/'captures/current-model-ram.bin').read_bytes())
code=json.loads((B/'captures/inflater-instructions.json').read_text())
restored=0
for line in code['lines']:
    if line.get('encoding') is None: continue
    at=line['address']-0x08000000
    struct.pack_into('<I',ram,at,line['encoding']);restored+=1
    if line.get('macroEncoding') is not None:
        assert line['addressSize']==8
        assert line['macroEncoding'][0]==line['encoding']
        struct.pack_into('<I',ram,at+4,line['macroEncoding'][1]);restored+=1

cases=[A/'full_extracted/PSP_GAME/USRDIR/GAMEDATA/FLD/FCHR/FCHR_P_BRS02.BIN',G/'workspace/model_port/candidate_v1/original_reencoded.BIN',G/'workspace/model_port/candidate_v1/FCHR_P_BRS02_pgr_candidate.BIN',D/'combined-20260924/FCHR_P_BRS02_same_model_fixed_deflate.BIN']
results=[]
for path in cases:
    raw=path.read_bytes();expected=gzip.decompress(raw)
    uc=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN)
    from unicorn.mips_const import UC_CPU_MIPS32_24KF
    uc.ctl_set_cpu_model(UC_CPU_MIPS32_24KF)
    uc.mem_map(0x08000000,0x02000000);uc.mem_write(0x08000000,bytes(ram))
    dest=0x09000000;source=0x09800000;stack=0x09fff000
    uc.mem_write(source,raw);uc.mem_write(dest,b'\xcd'*(len(expected)+256))
    for reg,value in [(UC_MIPS_REG_A0,dest),(UC_MIPS_REG_A1,len(expected)),(UC_MIPS_REG_A2,source),(UC_MIPS_REG_A3,0),(UC_MIPS_REG_SP,stack),(UC_MIPS_REG_RA,0x08001000)]:uc.reg_write(reg,value)
    invalid=[]
    def on_invalid(uc,access,address,size,value,data):
        invalid.append(dict(access=access,address=hex(address),size=size,pc=hex(uc.reg_read(UC_MIPS_REG_PC))))
        return False
    uc.hook_add(UC_HOOK_MEM_INVALID,on_invalid)
    tail=deque(maxlen=12)
    def special(uc,address,size,line):
        tail.append(hex(address));word=line['encoding'];rs=(word>>21)&31;rt=(word>>16)&31;rd=(word>>11)&31
        if line['name'] in ('clz','clo'):
            value=uc.reg_read(UC_MIPS_REG_0+rs)&0xffffffff
            if line['name']=='clo':value^=0xffffffff
            result=32-value.bit_length()
        elif line['name']=='bitrev':
            value=uc.reg_read(UC_MIPS_REG_0+rt)&0xffffffff
            result=int(f'{value:032b}'[::-1],2)
        elif line['name'] in ('min','max'):
            left=uc.reg_read(UC_MIPS_REG_0+rs)&0xffffffff;right=uc.reg_read(UC_MIPS_REG_0+rt)&0xffffffff
            if left&0x80000000:left-=0x100000000
            if right&0x80000000:right-=0x100000000
            result=(min(left,right) if line['name']=='min' else max(left,right))&0xffffffff
        else:raise AssertionError(line)
        uc.reg_write(UC_MIPS_REG_0+rd,result)
    for line in code['lines']:
        if line['name'] in ('clz','clo','bitrev','min','max'):
            # Keep native branch-delay handling by executing a NOP after the
            # exact register operation in the hook. Never patch the real game.
            uc.mem_write(line['address'],b'\0'*4)
            uc.hook_add(UC_HOOK_CODE,special,line,begin=line['address'],end=line['address'])
    start=time.monotonic();error=None
    try: uc.emu_start(0x08960b18,0x08001000,timeout=15000000,count=150000000)
    except UcError as e:error=str(e)
    output=bytes(uc.mem_read(dest,len(expected)))
    row=dict(file=str(path),bytes=len(raw),expected_bytes=len(expected),returned=uc.reg_read(UC_MIPS_REG_V0),pc=hex(uc.reg_read(UC_MIPS_REG_PC)),elapsed=time.monotonic()-start,error=error,invalid=invalid,exact_output=output==expected,output_sha256=hashlib.sha256(output).hexdigest(),expected_sha256=hashlib.sha256(expected).hexdigest())
    row['last_instructions']=list(tail)
    results.append(row);print(json.dumps(row),flush=True)
(D/'combined-20260924/inflater-offline-test.json').write_text(json.dumps(dict(restored_instruction_count=restored,results=results,scope='Offline original MIPS inflater with isolated buffers; does not prove game allocation or rendered model'),indent=2),'utf8')
