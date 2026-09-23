"""Persist local inference evidence, decisions, and an honest continuation checkpoint."""
import sys,json,hashlib,collections,datetime,io
from pathlib import Path
import numpy as np
from PIL import Image
from ptmd_expanded import decode

sys.stdout.reconfigure(encoding='utf8')
R=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads((R/p).read_text('utf8'))
def write(p,data):(R/p).write_text(json.dumps(data,ensure_ascii=False,indent=2),'utf8')

# The expanded decoder must preserve every already verified source, not just new maps.
ui=read('qa/ui_inventory_expanded.json');regression=[]
for t in ui['textures']:
    if t['magic']!='50544d44':continue
    im,proof=decode(Path(t['source']).read_bytes())
    assert sha(im.tobytes())==t['rgba_sha256'] and proof['roundtrip_exact'],t['id']
    regression.append(t['id'])

trial=read('qa/local_sr_title_trial_v1.json')
trial['visual_review']='rejected: over-smoothed metal surface, distorted rivet shading/highlights. Independently confirmed.'
write('qa/local_sr_title_trial_v1.json',trial)
comparison=read('qa/local_sr_title_models_v2.json')
decisions={
    'general-dn0.0':'selected for isolated game verification: preserves grain, long scratches and rivet body/shading better; true detail vs palette dithering remains uncertain',
    'general-dn0.5':'not selected: more surface grain removed than dn0.0',
    'general-dn1.0':'rejected for this metal background: excessive smoothing',
    'photo-x4plus':'not selected: stronger reinterpretation of scratch and rivet edges',
    'anime6B-exposure':'rejected for this metal background: smooth planes and irregular rivet facets remain'}
for rec in comparison['files']:rec['visual_review']=decisions[rec['id']]
comparison['independent_review']='Read-only agent confirmed general-dn0.0 as first game-verification candidate; not final acceptance.'
write('qa/local_sr_title_models_v2.json',comparison)

materials=read('qa/local_sr_battle_material_trial.json')
materials['scope']='Six opaque material comparisons: five without identified lettering; tex018 dark markings are text/damage ambiguous and unapproved. STOP lettering and alpha assets remain pending in full scope.'
materials['independent_review']='Read-only comparison: 002/008/009 WDN are static candidates; 001/017 need texture/color rework; 018 meaning unresolved.'
for rec in materials['files']:
    rec['visual_review']=('provisional game/tiling review candidate; inspect inferred fine texture and source marks'
                          if rec['model']=='general-wdn' else 'not selected: over-smoothing or cartoon-like surface/edge simplification')
    if rec['model']=='general-wdn' and rec['asset_id'].endswith(('tex001','tex017')):
        rec['visual_review']='rework required: too much inferred fine relief/fibrous grain and cooler color; compare intermediate denoise or less generative restoration before adoption'
    if rec['asset_id'].endswith('tex018'):
        rec['visual_review']='hold: text/damage ambiguity in source marks; not approved as generic texture'
        rec['unresolved']='Native box [45,54,85,82): dark marks may be damage or lettering; no semantic interpretation accepted.'
write('qa/local_sr_battle_material_trial.json',materials)

checked=[]
for rec in [trial,*comparison['files'],*materials['files'],read('qa/local_sr_title_stage.json')]:
    path=Path(rec['output']);data=path.read_bytes();assert sha(data)==rec['output_sha256'],path
    im=Image.open(io.BytesIO(data));im.verify()
    checked.append({'path':str(path),'sha256':sha(data)})

# Full-image pixel equality is stronger than a logical crop; still not material/UV proof.
observed=read('qa/ui_expanded_links.json');by_pixels=collections.defaultdict(list)
for rec in observed['observed_records']:
    by_pixels[(tuple(rec['size']),rec['rgba_sha256'])].append({k:rec[k] for k in ['key','paths','png_sha256','rgba_sha256','size']})
maps=read('qa/battle_map_inventory.json');bindings=[];formats=collections.Counter();matched_formats=collections.Counter()
for tex in maps['textures']:
    if 'png' not in tex:continue
    fmt=(tex['mode'],tex.get('palette_code'));formats[str(fmt)]+=1
    matches=by_pixels.get(((tex['width'],tex['height']),tex['rgba_sha256']),[])
    if matches:
        matched_formats[str(fmt)]+=1
        bindings.append({'asset_id':tex['id'],'logical_full_image_match':True,'source_rgba_sha256':tex['rgba_sha256'],
                         'size':[tex['width'],tex['height']],'matches':matches,
                         'consumer_scene_uv':'Not established by pixel equality','replacement_runtime_verified':False})
maplinks={'schema':'brs-battle-map-runtime-links/v1','iso_sha256':maps['iso_sha256'],
          'decoded_count':maps['summary']['decoded'],'matched_asset_count':len(bindings),
          'format_counts':dict(formats),'matched_format_counts':dict(matched_formats),'bindings':bindings,
          'release_eligible':False,'scope':'Observed full texture pixels compared to extracted source; no replacement or full stage coverage claim.'}
write('qa/battle_map_runtime_links.json',maplinks)
summary={'schema':'brs-local-sr-batch-verification/v1','date':datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'old_ui_ptmd_regression_count':len(regression),'old_ui_rgba_and_roundtrip_pass':True,
         'output_files_verified':checked,'unique_originals_processed_locally':7,
         'title_neural_variants':6,'battle_material_neural_variants':12,
         'maps':maps['summary'],'map_pixel_links':maplinks['matched_asset_count'],
         'matched_palette_formats':dict(matched_formats),'installed':False,'runtime_verified':False,'full_goal_complete':False}
write('qa/local_sr_batch_verification.json',summary)
marker='## 2026-09-23 — LOCAL-SR-001: 실제 로컬 추론 및 재작업'
progress=R/'PROGRESS.md';old=progress.read_text('utf8')
if marker not in old:
    note=f'''

{marker}

- 최신 사용자 지시: 로컬 업스케일 → Codex 품질 검수 → 미달이면 재작업. 로컬로 해결하기 어렵다고 확인된 경우 GPT 협력도 허용. 이 배치에서는 모든 이미지 추론을 로컬 GPU에서 실행했다.
- 앞선 설명 정정: v4의 한글은 고해상도 재렌더링이지만 비문자 원본 영역은 nearest 8배 보존이었다. 이를 AI 업스케일 완료로 계산하지 않는다. 외부 imagegen 타이틀1672×941 시안은 미채택·미설치, 실제4K 완료가 아니다.
- Forge/models에 파일이 없다는 관찰로 전체 로컬 모델 부재를 단정한 것은 오류. Fate/EXTRA 프로젝트의 공식 RealESRGAN_x4plus_anime_6B.pth를 발견하여 해시 f872d837d3c90ed2e05227bed711af5671a6fd1c9f7d7e91c911a61f155e99da 검증, 읽기 전용 재사용. RTX5080 / torch2.7.0+cu128 / spandrel0.3.4 / FP32 RGB. Fate 프로젝트는 변경하지 않았다.
- 이전 사용량 한도 승인 검사 실패는 이번 실행에서 재현되지 않았다. 허용된 P 프로젝트 쓰기로 실제 산출물을 생성했다. 미실행 계획을 추론 성공으로 기록하지 않음.

### 완료한 실제 추론과 품질 판정
- 타이틀 원본 /000:480×272 활성 영역을 anime6B로 실제4배 추론 후 Lanczos2배(3840×2176). 첫 결과는 표면 무늬 소실·리벳 하이라이트 과장으로 미채택. qa/local_sr_title_trial_v1.json.
- 재작업5조건: general DNI0/0.5/1, photo-x4plus, anime6B 노출전처리. 필요한 비교모델은 공식 release에서 프로젝트 workspace/local-sr/models로 다운로드, 출처·크기·SHA256·LICENSE 기록. 첫6B까지 총6조건 모두 실제 로컬 추론이다.
- general-dn0.0(weak denoise)을 게임 검수 후보로 선택. 독립 읽기 검토도 같은 판단. 미세결에는 팔레트 디더링의 재해석이 섞였을 수 있으며 최종 품질·런타임 통과 아님. qa/local_sr_title_models_v2.json.
- 관측키0000000086ba34d7c28b381c에만 연결한 별도 title-review-pack 준비. 실제 관측512×512의 패딩·전체알파·활성영역밖 픽셀은 nearest 기준과 완전 일치. 출력4096×4096. 원래 가로선y192, 세로 어두운 띠 유지. qa/local_sr_title_stage.json. 설치/게임 실행 없음.
- 첫 전투맵의6종(001흙/002도로/008아치창/009건물외벽/017잔해/018무너진건물)을 general-WDN 및 anime6B 두 모델로 처리한12후보. 일반모델이 표면결·형상을 더 유지, anime6B는 평탄화/만화적 단순화로 미선택. /018어두운 자국의 의미 미확정. STOP문구005와 알파자산은 이 비교에서만 보류, 전체범위에서 제외하지 않는다. qa/local_sr_battle_material_trial.json.
- 실제 로컬 처리 원본은 총7종(타이틀1+전투재질6). neural4배 후Lanczos2배이며 native8배AI·전게임4K 완료 주장은 금지. 후보들의 SHA/PNG검증 완료: qa/local_sr_batch_verification.json.

### 추출·연결 및 기존 보고서 보충
- UI 확장443이미지(439PTMD+4PNG),84루트,39SDO를 추출/원본바이트 roundtrip 확인. qa/ui_inventory_expanded.json. 이는 전체 게임 모집단이 아니다. 기존439PTMD의 RGBA·roundtrip은 새 디코더로 재검사 통과.
- tools/link_expanded_ui.py 실행:6832관측키 스캔,152논리자산의 일치 후보. 단색·작은 조각은 수천 개 키와 일치하므로 이 수치를 소비자 식별 완료나 정식매핑 수로 쓰지 않는다. title배경은 고유 일치. qa/ui_expanded_links.json.
- 부모 rgba hash는 SHA256(big-endian w,h+RGBA), 이 프로젝트는 SHA256(RGBA), 크기별도. 기존 같은키 해시 차이는 이 계약 차이이며 이미지충돌의 증거가 아니었다.
- 전투맵 BTL/MAP24루트,STCM44컨테이너의 텍스처 테이블416항목 확보.410디코드,6개는 flag5/높이1·4 특수형식으로 미해결. 헤더6..7을 텍스처수 일부로 잘못 해석하지 않으며 보존. 텍스처0개 컨테이너도 유효하게 집계. qa/battle_map_inventory.json.
- RGB565/RGBA5551 indexed palette코드0/16 지원을 추가하여 palette·인덱스·swizzle bytes의 exact roundtrip 확인. 실제 전체픽셀 관측 연결은 {{maplinks['matched_asset_count']}}개. 새 색상형식 runtime일치 근거는 qa/battle_map_runtime_links.json의 matched_format_counts 참조.

### 다음 실행 단계 / 전체 범위 유지
1. 타이틀 general-WDN 후보의 실제게임 합성·축소/움직임·리벳 밝기 검증. 사용자 게임에 입력하지 않으며 에뮬 실행 시 항상 exe+고정ISO CLI. 컴퓨터 유즈로 실행하지 않는다.
2. 전투재질6종 독립 검수 결과 기록, 반복 경계·UV·알파/조각별 소비 확인 후 배치 확대. 조각 아틀라스·문자·알파전용 효과는 구역/소비구조에 맞춰 별도 처리.
3. STCM flag5 미해결6항목을 원본·관측덤프·엔진 소비로 해석, 미지원으로 영구 제외하지 않음. FLD/오브젝트/적/이펙트/컷신 추출 확대, 주인공PGR/연결모델은 부모 소유 제외 유지.
4. Orbit본문·UI v4 실제게임 검수, 조준고정 UI22 실제 소비, 미관측캐시, 지역1~6/EX/진엔딩 커버리지, 설치/제거 가능한 최종ZIP 모두 남음. 전체 목표 active.
'''.replace("{maplinks['matched_asset_count']}",str(maplinks['matched_asset_count']))
    progress.write_text(old+note,'utf8')
review_marker='### LOCAL-SR-001 독립 전투재질 검토 반영'
old=progress.read_text('utf8')
if review_marker not in old:
    progress.write_text(old+'\n\n'+review_marker+'\n- 002도로/008아치창/009외벽: general-WDN 정적 후보. 001흙/017잔해: 미세 요철·섬유 모양 과장과 차가운 색으로 재작업 필요. 018: 원본[45,54,85,82)의 어두운 표식이 글자인지 손상인지 미확정하여 채택보류.\n- 이전 6종을 모두 nontext로 표현한 manifest를 정정. 비교6종 중5종만 식별된 글자 없음,018은 ambiguous로 유지. 이 결과를 전체배경 승인이나 게임/UV 통과로 쓰지 않는다. 다음 GPU 작업은001/017의 중간 노이즈 강도 및 보수적 복원 비교부터.\n','utf8')
print(json.dumps({k:v for k,v in summary.items() if k!='output_files_verified'},ensure_ascii=False),flush=True)
