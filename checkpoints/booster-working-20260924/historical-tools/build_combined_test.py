"""Freeze existing BRS work into a separate playable test bundle; no asset generation."""
from pathlib import Path
import configparser, hashlib, json, re, shutil, time
from PIL import Image

R = Path('P:/AI/Codex/projects/black-rock-shooter-hd-ui-fonts')
G = Path('P:/AI/Codex/projects/black-rock-shooter-hd-retexture')
C = Path(__file__).resolve().parents[1]
OUT = G / 'release' / ('combined-test-' + time.strftime('%Y%m%d-%H%M%S'))
BASE = G / 'workspace/sessions/S-20260922-151804-baseline-d7d8b6'
ISO = G / 'workspace/model_port/candidate_v1/BRS_pgr_candidate.iso'
EXE = G / 'workspace/runtime/ppsspp-1.20.4/PPSSPPWindows64.exe'

def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(4*1024*1024), b''): h.update(b)
    return h.hexdigest()

def cfg(p):
    c = configparser.ConfigParser(interpolation=None, strict=True)
    c.optionxform = str
    c.read(p, encoding='utf-8-sig')
    return c

def read(p): return json.loads(p.read_text('utf-8-sig'))
def write(p, j): p.write_text(json.dumps(j, ensure_ascii=False, indent=2), 'utf8')
def copy_verified(src, dst, expected=None):
    actual = sha(src)
    if expected: assert actual == expected, str(src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    assert sha(dst) == actual, str(dst)
    return actual

assert sha(ISO) == 'ffd94390d4f0703a5ba4c2fe66e15cf576215ffaabf588a2a0574cdb7398dd42'
assert sha(EXE) == '27d3edbb06dc623dab60877d3e3a975aef4034c7d4fac464e92fd4998864d2ec'
OUT.mkdir(parents=True, exist_ok=False)
pack = OUT / 'memstick/PSP/TEXTURES/NPUH10126'
pack.mkdir(parents=True)
bindings, evidence, staged, by_rgba = {}, [], {}, {}

def bind(key, src, rel, proof):
    assert re.fullmatch('[0-9a-f]{24}', key) and key.startswith('00000000')
    digest = sha(src)
    if key in bindings:
        assert sha(pack / bindings[key]) == digest, ('conflicting key', key)
        return
    copy_verified(src, pack / rel, digest)
    bindings[key] = rel
    evidence.append(dict(key=key, file=rel, sha256=digest, proof=proof))

ui = R / 'workspace/build-v4/PSP/TEXTURES/NPUH10126'
ui_ini = cfg(ui / 'textures.ini')
assert len(ui_ini['hashes']) == 539
for k, v in ui_ini['hashes'].items(): bind(k, ui / v, 'ui-font-v4/' + v, 'existing UI/font v4 exact-key pack')

for name in ['battle_sr_catalog.json', 'field_sr_catalog.json']:
    for g in read(R / 'qa' / name)['groups']:
        c = g.get('candidate')
        if not c: continue
        src = Path(c.get('output') or c['path'])
        digest = c.get('output_sha256') or c['sha256']
        gid = g['group_id']
        assert sha(src) == digest
        with Image.open(src) as im: size = list(im.size)
        staged[gid] = dict(group_id=gid, source_rgba_sha256=g['rgba_sha256'], source=str(src), sha256=digest, size=size, keys=[])
        copy_verified(src, OUT / 'saved-candidates' / (gid+'.png'), digest)
        by_rgba.setdefault(g['rgba_sha256'], []).append(gid)
assert len(staged) == 354

# Re-read real captured source textures. Accept a key only on exact decoded
# full-image RGBA + dimensions identity, with xxh64/non-reduced capture settings.
dump_count = 0
for root in [R / 'workspace/sessions', G / 'workspace/sessions']:
    for folder in root.glob('*/memstick/PSP/TEXTURES/NPUH10126/new'):
        ini_path = folder.parent / 'textures.ini'
        if not ini_path.is_file(): continue
        opt = cfg(ini_path)['options']
        if opt.get('hash', '').lower() != 'xxh64' or opt.get('reduceHash', 'false').lower() != 'false': continue
        for p in sorted(folder.glob('*.png')):
            if not re.fullmatch('[0-9a-fA-F]{24}', p.stem): continue
            with Image.open(p) as image:
                im = image.convert('RGBA')
                digest = hashlib.sha256(im.tobytes()).hexdigest()
                size = im.size
            dump_count += 1
            gids = by_rgba.get(digest, [])
            if not gids: continue
            # If equivalent records disagree on the chosen artwork, avoid a new binding.
            if len({staged[g]['sha256'] for g in gids}) != 1: continue
            gid = gids[0]; c = staged[gid]
            assert c['size'] == [size[0]*8, size[1]*8], gid
            key = '00000000' + p.stem.lower()[8:]
            bind(key, Path(c['source']), 'materials/'+gid+'.png', dict(observed_png=str(p), observed_png_sha256=sha(p), source_rgba_sha256=digest, source_size=list(size), capture_options=str(ini_path)))
            for g in gids:
                if key not in staged[g]['keys']: staged[g]['keys'].append(key)

observed = R / 'workspace/local-sr/observed-review-pack-v2/PSP/TEXTURES/NPUH10126'
for key, rel in cfg(observed / 'textures.ini')['hashes'].items():
    if key not in bindings: bind(key, observed / rel, 'observed-v2/'+rel, 'existing verified-source-key observed v2 pack')

texture_text = '[options]\nversion = 1\nhash = xxh64\nignoreAddress = true\nreduceHash = false\n\n[hashes]\n'
texture_text += ''.join(k+' = '+v+'\n' for k,v in sorted(bindings.items()))
(pack / 'textures.ini').write_text(texture_text, 'utf8')
assert dict(cfg(pack/'textures.ini')['hashes']) == bindings
for e in evidence: assert sha(pack/e['file']) == e['sha256']

runtime = OUT / 'runtime'; runtime.mkdir()
exe_hash = copy_verified(EXE, runtime/'PPSSPPBRS4KTest.exe')
shutil.copytree(EXE.parent / 'assets', runtime / 'assets')
(runtime/'installed.txt').write_text(str(OUT/'memstick')+'\n','utf8')
iso_hash = copy_verified(ISO, OUT/'BRS_4K_combined_test.iso')
system = OUT/'memstick/PSP/SYSTEM'; system.mkdir(parents=True)
copy_verified(BASE/'memstick/PSP/SYSTEM/controls.ini',system/'controls.ini')
shutil.copytree(BASE/'memstick/PSP/SAVEDATA',OUT/'memstick/PSP/SAVEDATA')
config = cfg(BASE/'memstick/PSP/SYSTEM/ppsspp.ini')
changes = {
 'General': {'WindowX':'80','WindowY':'80','WindowWidth':'1440','WindowHeight':'870','RemoteISOPort':'49324','RemoteDebuggerOnStartup':'True','RemoteDebuggerLocal':'True','FullScreen':'False','AutoLoadSaveState':'0','PauseOnLostFocus':'False','PauseWhenMinimized':'False','CurrentDirectory':str(OUT)},
 'Graphics': {'ReplaceTextures':'True','SaveNewTextures':'True','InternalResolution':'8','FullScreen':'False'},
 'Sound': {'Enable':'True','GameVolume':'75'},
}
for section, values in changes.items():
    for key, value in values.items(): config[section][key] = value
with (system/'ppsspp.ini').open('w',encoding='utf8') as f: config.write(f)

launcher = r'''$ErrorActionPreference='Stop'
$root=$PSScriptRoot
$exe=Join-Path $root 'runtime\PPSSPPBRS4KTest.exe'
$iso=Join-Path $root 'BRS_4K_combined_test.iso'
$manifest=Get-Content -LiteralPath (Join-Path $root 'build-manifest.json') -Raw | ConvertFrom-Json
if((Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant() -ne $manifest.executable_sha256){throw 'Emulator hash mismatch'}
if((Get-FileHash -LiteralPath $iso -Algorithm SHA256).Hash.ToLowerInvariant() -ne $manifest.iso_sha256){throw 'ISO hash mismatch'}
if(Get-CimInstance Win32_Process | Where-Object {$_.ExecutablePath -eq $exe}){throw 'This build is already running'}
if(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object {$_.LocalPort -eq 49324}){throw 'Port 49324 is already in use'}
[IO.File]::WriteAllText((Join-Path $root 'runtime\installed.txt'),(Join-Path $root 'memstick')+"`n",[Text.UTF8Encoding]::new($false))
$p=Start-Process -FilePath $exe -WorkingDirectory (Join-Path $root 'runtime') -ArgumentList @(('"'+$iso+'"'),'--windowed') -WindowStyle Normal -PassThru
@{pid=$p.Id;executable=$exe;iso=$iso;port=49324;launched=(Get-Date).ToString('o');savestate_loaded=$false} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $root 'launch-session.json') -Encoding utf8
Write-Output ('BRS combined build launched: '+$p.Id)
'''
(OUT/'Launch-BRS-4K.ps1').write_text(launcher,'utf-8-sig')
(OUT/'게임 실행.cmd').write_text('@echo off\r\npowershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Launch-BRS-4K.ps1"\r\n','ascii')
manifest = dict(schema='brs-combined-test/v1',path=str(OUT),status='test_build_not_final_release',iso_source=str(ISO),iso_sha256=iso_hash,executable_sha256=exe_hash,game='NPUH10126',ui_font_keys=539,total_keys=len(bindings),environment_title_keys=len(bindings)-539,saved_candidates=len(staged),mapped_candidate_count=sum(bool(x['keys']) for x in staged.values()),unmapped_candidate_count=sum(not x['keys'] for x in staged.values()),dump_files_checked=dump_count,candidates=list(staged.values()),bindings=evidence,settings=changes,savedata_source=str(BASE/'memstick/PSP/SAVEDATA'),savestate_autoload=False,model='PGR candidate, Booster Unit only; actual display/movement unverified',excluded='Four unreviewed FIELD-FOLIAGE-008 candidates; old-model body replacement; source ISO and originals are untouched',runtime_verified=False)
write(OUT/'build-manifest.json',manifest)
summary={k:manifest[k] for k in ['path','iso_sha256','total_keys','ui_font_keys','environment_title_keys','saved_candidates','mapped_candidate_count','unmapped_candidate_count','dump_files_checked']}
write(C/'outputs/combined-build-latest.json',summary)
readme = f'''BLACK ROCK SHOOTER — 4K 애셋 리마스터 통합 시험본

실행: 게임 실행.cmd
한글 패치 ISO + PGR 모델 후보(Booster Unit) + 한글 UI/폰트 v4 + 관측키 연결 배경/타이틀.
활성 교체 키: {len(bindings)} (UI/폰트539, 배경/타이틀{len(bindings)-539}).
제작 후보354종을 saved-candidates에 동결 보존. 그중 {summary['mapped_candidate_count']}종만 현재 게임 관측키와 연결되었습니다.
미연결 {summary['unmapped_candidate_count']}종은 보존용이며 게임에는 아직 표시되지 않습니다.
최신 미검수 식물4종은 제외. 모든 애셋/모델의 실게임 품질 검수 완료나 최종 배포본을 뜻하지 않습니다.
별도 세이브 사본 사용. 원본 세이브/ISO/다른 게임 에뮬레이터는 변경하지 않습니다.
8배 내부 렌더링, 소리 활성화/75. 오래된 모델이 RAM에 남는 것을 피하도록 구형 강제 세이브는 자동 로드하지 않습니다.
'''
(OUT/'읽어주세요.txt').write_text(readme,'utf-8-sig')
shutil.copy2(__file__,OUT/'build_combined_test.py')
print(json.dumps(summary,ensure_ascii=False))
