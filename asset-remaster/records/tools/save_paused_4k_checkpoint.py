from pathlib import Path
import json,hashlib,shutil,datetime
from PIL import Image
R=Path(r'P:\AI\Codex\projects\black-rock-shooter-hd-ui-fonts')
G=Path(r'P:\AI\Codex\projects\black-rock-shooter-hd-retexture')
C=Path(r'C:\Users\CadriacLord\Documents\Codex\2026-09-22\brs-hd-ui-fonts')
S=G/'asset-remaster';assert not S.exists()
def read(p):return json.loads(Path(p).read_text('utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False),'utf8')
last=read(R/'qa/field_foliage007_review.json');cat=read(R/'qa/field_sr_catalog.json');battle=read(R/'qa/battle_sr_catalog.json')
assert sha(R/'qa/field_sr_catalog.json')==last['catalog_after_sha256']
assert sha(R/'qa/architectural_geometry_contract.json')==last['geometry_contract_after_sha256']
raw=read(R/'qa/field_foliage008_gpt_raw.json');pending=read(R/'qa/field_foliage008_material_v1.json')
assert len(raw['files'])==3 and len(pending['files'])==4 and len(pending['pages'])==12
for p in raw['files']:
    assert sha(p['raw_generated_image'])==p['raw_sha256']
    for k in ['prompt','reference']:assert sha(p[k])==p[k+'_sha256']
for p in pending['files']:assert sha(p['output'])==p['output_sha256'] and p['review_status']=='pending'
for p in pending['pages']:assert sha(p['path'])==p['sha256'] and p['review_status']=='pending'
for rel,h in last['protected_file_hashes'].items():assert sha(R/rel)==h
script_names=['prepare_foliage008.py','inspect_foliage008_raw.py','foliage_material008.py','build_foliage_material008.py','save_paused_4k_checkpoint.py']
for name in script_names:shutil.copy2(C/'work'/name,R/'tools'/name)
prompt_dir=R/'docs/field-foliage008';prompt_dir.mkdir(parents=True,exist_ok=True)
for gid in ['FM0301','FM0312','FM0320']:shutil.copy2(C/'work'/(gid+'-foliage008-prompt.txt'),prompt_dir/(gid+'-prompt.txt'))
checkpoint={'schema':'brs-4k-asset-remaster-paused/v1','project_title':'BLACK★ROCK SHOOTER THE GAME — 4K 애셋 리마스터','status':'paused_by_user','reason':'User requested pause due to remaining Codex allowance; save work and organize in Git for later resumption.','asset_work_running':False,'latest_completed_batch':'FIELD-FOLIAGE-007','authoritative_review':'qa/field_foliage007_review.json','active_unfinished_batch':'FIELD-FOLIAGE-008','confirmed_counts':last['known_battle_plus_novel_field_progress'],'field_processing_summary':last['field_processing_summary'],'current_batch':{'actual_GPT_calls':3,'actual_new_local_calls':0,'new_unique_originals':0,'raw_GPT':[{k:p[k] for k in ['group_id','raw_generated_image','raw_sha256','prompt','prompt_sha256']} for p in raw['files']],'pending_candidates':[{k:p[k] for k in ['group_id','id','output','output_sha256','review_status']} for p in pending['files']],'unreviewed_comparison_pages':[p['path'] for p in pending['pages']],'raw_comparison_pages_directly_inspected':8,'latest_material_candidates_directly_inspected':0,'counts_updated_for_this_batch':False},'next_step':'After explicit user resume, inspect all12 FIELD-FOLIAGE-008 material-v1 whole/detail/edge pages on both mattes; compare source silhouettes/leaf structure/palette. Do not treat generated files or matching total alpha as accepted. Then perform frozen recipe/integrity checks and finalize selected/held catalog entries. No new inference has started.','remaining_full_scope':'Field49 holds and189 novel unprocessed; battle43 unresolved; historical geometry applicability, characters/enemies/UI/effects/cutscenes/unsupported source populations, exact consumer mapping, actual-game verification and final packaging remain.','runtime_constraint':'No Computer Use emulator launch. Native GUI unavailable at pause; do not repeat black capture attempts without new recovery evidence. Exact QA exe+ISO only if runtime work resumes.','git_repository':str(G),'local_full_working_artifacts':str(R),'rendering_resolution_note':'4K Asset Remaster is the user-requested project name. Current assets retain their actual4x/8x/native sizes; not all PNGs are4096px.','runtime_verified':False,'release_eligible':False,'all_game_complete':False}
write(R/'qa/paused_checkpoint_20260923.json',checkpoint)
pause_note='''

## 2026-09-23 — 사용자 요청 일시정지 / 4K 애셋 리마스터 Git 체크포인트
- 사용자 한도 사유로 재작화 목표paused. 신규애셋생성/추론/후보선정중단. 마지막완료FIELD-FOLIAGE-007 집계유지(known635중354정적후보/420처리;field113후보49보류189미처리).
- FIELD-FOLIAGE-008 GPT실제3회(301/312/320),색조·밀도보정파생4종(301/312/318/320)저장. raw비교8페이지는직접검수; 최신material-v1비교12페이지/후보4종은시각검수전이며catalog에반영하지않음. 최신작업프로세스는정상종료.
- qa/paused_checkpoint_20260923.json에해시/지시문/출력/재개단계보존. 다음은사용자가재개한뒤12비교페이지검수→필요한수정과frozenrecipe검증→후보/보류반영. alpha총량일치만으로합격처리하지않음.
- 기존black-rock-shooter-hd-retexture Git저장소에asset-remaster 체크포인트로정리. 원본ISO/무가공추출/모델가중치/에뮬레이터/세이브는기존로컬에보존하며Git에포함하지않음. 프로젝트명4K애셋리마스터;현PNG전체가4096해상도라는의미아님.
'''
for p in [R/'PROGRESS.md',C/'outputs/로컬_업스케일_진행.md']:
    with p.open('a',encoding='utf8') as f:f.write(pause_note)

S.mkdir();items=[]
def copy_asset(src,relative,kind):
    src=Path(src);dest=S/relative;assert src.is_file()
    dest.parent.mkdir(parents=True,exist_ok=True);assert not dest.exists();shutil.copy2(src,dest);h=sha(src);assert sha(dest)==h
    rec={'path':str(dest.relative_to(G)).replace('\\','/'),'source_path':str(src),'sha256':h,'bytes':src.stat().st_size,'kind':kind}
    if src.suffix.lower()=='.png':
        with Image.open(src) as im:rec['actual_pixel_size']=list(im.size)
    items.append(rec)
text_ext={'.py','.ps1','.js','.mjs','.cjs','.json','.md','.txt','.csv','.tsv','.html','.svg','.ini','.toml','.yml','.yaml','.xml','.bat','.cmd','.cpp','.h'}
for name in ['tools','docs','qa']:
    for p in (R/name).rglob('*'):
        if p.is_file() and p.suffix.lower() in text_ext and '__pycache__' not in p.parts:
            copy_asset(p,Path('records')/p.relative_to(R),'code_and_evidence')
copy_asset(R/'PROGRESS.md','records/PROGRESS.md','progress')
counts={}
for lane,catalog in [('field',cat),('battle',battle)]:
    selected=[p for p in catalog['groups'] if p.get('candidate')];counts[lane]=len(selected)
    for p in selected:
        candidate=p['candidate'];path=candidate.get('path',candidate.get('output'));h=candidate.get('sha256',candidate.get('output_sha256'));assert path and h and sha(path)==h
        copy_asset(path,Path('assets/static-candidates')/lane/(p['group_id']+'.png'),'static_candidate_not_runtime_verified')
assert counts=={'field':113,'battle':241}
for name,source in [('observed-review-v2',R/'workspace/local-sr/observed-review-pack-v2'),('ui-font-v4',R/'workspace/build-v4')]:
    for p in source.rglob('*'):
        if p.is_file() and p.suffix.lower() in {'.png','.ini','.txt','.md','.json'}:
            copy_asset(p,Path('packs-not-installed')/name/p.relative_to(source),'uninstalled_review_pack')
for p in (R/'workspace/gpt-trials').rglob('*'):
    if p.is_file() and p.name in {'generated-raw.png','prompt.txt','provenance.json'}:
        copy_asset(p,Path('generated-materials')/p.relative_to(R/'workspace/gpt-trials'),'preserved_GPT_material_and_prompt')
for p in pending['files']:
    copy_asset(p['output'],Path('assets/pending-review/field-foliage008')/Path(p['output']).name,'pending_visual_review_not_selected')
for p in (R/'workspace/local-sr').rglob('*'):
    if p.is_file() and p.suffix.lower() in {'.py','.svg','.npz','.npy'} and 'models' not in p.parts and '__pycache__' not in p.parts:
        copy_asset(p,Path('frozen-recipes')/p.relative_to(R/'workspace/local-sr'),'frozen_recipe_or_geometry')
for p in (R/'outputs/field-foliage008').glob('*.png'):
    copy_asset(p,Path('previews/field-foliage008')/p.name,'comparison_with_review_state_in_manifest')
copy_asset(R/'outputs/field-foliage007/나무_잎과_껍질_재질_수정.png','previews/tree-material-comparison.png','reviewed_comparison')
resume='''# 재개 안내

현재 사용자 요청으로 **일시정지**한 개발 체크포인트입니다. 배포판이나 게임 내 검증 완료 팩이 아닙니다.

1. 마지막 확정 기록은 `records/qa/field_foliage007_review.json`입니다.
2. 최신 작업 상태는 `records/qa/paused_checkpoint_20260923.json`입니다.
3. `assets/pending-review/field-foliage008/`의4개PNG는 아직 시각검수하지 않았습니다. `previews/field-foliage008/`의 `material-v1` 전체/세부/가장자리12장을 검사하는 것이 다음 단계입니다.
4. 확인 후 원본 구조/색/alpha 검증 및 frozen recipe 재현을 수행하고, 통과한 경우에만 후보catalog를 갱신합니다.
5. 현재 full local workspace는 `P:/AI/Codex/projects/black-rock-shooter-hd-ui-fonts`입니다. 원본과 과거 실패·재작업 파일도 그곳에 보존되어 있습니다.

이 Git 스냅샷은354개전투·필드정적후보, 미설치관측팩/폰트UI팩, 최신미검수4종, GPT원본/지시문, 작업기록/검수JSON/스크립트/고정recipe를 포함합니다. 원본ISO·무가공게임추출·모델가중치·에뮬레이터·세이브·대량이전시도이미지는Git에넣지않고로컬작업공간에보존합니다. 일부과거기록과스크립트는원래로컬절대경로를참조하므로새환경에서그대로실행하면안됩니다. `snapshot-manifest.json`에Git사본과원래파일의경로·SHA-256을대응시켰습니다.

프로젝트명은사용자지정 **4K 애셋 리마스터**입니다. 현재PNG는원본4배/8배및개별해상도를유지하며모든파일이4096픽셀인것은아닙니다. 실제크기는매니페스트에기록했습니다.

실제게임검수·설치·최종ZIP은미완료입니다. 컴퓨터유즈로에뮬레이터를실행하지말라는지시를유지합니다. 전체목표는완료처리하지말고사용자의명시적재개후계속합니다.
'''
(S/'RESUME.md').write_text(resume,'utf8')
manifest={'schema':'brs-4k-asset-remaster-git-snapshot/v1','status':'paused_development_checkpoint','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'static_candidate_counts':counts,'pending_unreviewed_candidates':4,'tracked_payload_files':len(items),'tracked_payload_bytes':sum(p['bytes'] for p in items),'files':items,'runtime_verified':False,'release_eligible':False}
write(S/'snapshot-manifest.json',manifest)
readme=G/'README.md';old=readme.read_text('utf8');old=old.replace('# BLACK★ROCK SHOOTER THE GAME HD Retexture','# BLACK★ROCK SHOOTER THE GAME — 4K 애셋 리마스터',1)
readme.write_text(old+'''

## 4K 애셋 리마스터 — 저장된 개발 체크포인트

사용자 요청으로 작업을 일시정지했습니다. [재개 안내](asset-remaster/RESUME.md)와 [파일·해시 목록](asset-remaster/snapshot-manifest.json)을 기준으로 이어갑니다.

- 확인된 전투·고유 필드635종 중 정적검수후보354종(55.75%), 한번이상처리420종(66.14%). 전체게임완료율이 아닙니다.
- 최신 식물 보정4종은 **미검수** 상태로 따로 보존했습니다.
- UI/폰트팩 및관측팩은미설치·실게임검증전입니다.
- `4K 애셋 리마스터`는 프로젝트명이며 현재모든PNG가4096픽셀이라는뜻은아닙니다. 실제크기는매니페스트에표시합니다.
- 원본ISO/무가공추출/모델/에뮬레이터/세이브는Git에서제외하고기존로컬작업공간에보존합니다.
''','utf8')
with (G/'PROGRESS.md').open('a',encoding='utf8') as f:f.write(pause_note+'\n- 통합 Git 체크포인트: asset-remaster/RESUME.md 및 snapshot-manifest.json.\n')
ignore=G/'.gitignore';txt=ignore.read_text('utf8');txt=txt.replace('# Game-derived texture dumps and generated replacements stay local','# Original working dumps stay local; selected generated assets are archived in asset-remaster/')
txt+='\n# Credentials and local environment\n.env\n.env.*\n!.env.example\n*.pem\n*.key\n'
ignore.write_text(txt,'utf8')
print(json.dumps({'repo':str(G),'snapshot':str(S),'files':len(items),'MiB':sum(p['bytes'] for p in items)/1024**2,'candidates':counts,'pending':4,'largest_MiB':max(p['bytes'] for p in items)/1024**2},ensure_ascii=False))
