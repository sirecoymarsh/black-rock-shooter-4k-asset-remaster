"""Persist Codex visual review; no asset changes or runtime acceptance."""
import hashlib
import json
import shutil
from pathlib import Path
from PIL import Image

R = Path(r'P:\AI\Codex\projects\black-rock-shooter-hd-ui-fonts')
C = Path(r'C:\Users\CadriacLord\Documents\Codex\2026-09-22\brs-hd-ui-fonts')
p = R / 'qa/local_sr_battle_material_rework_v2.json'
report = json.loads(p.read_text('utf8'))
verified = []
for row in report['files']:
    src = Image.open(row['source']).convert('RGBA')
    assert hashlib.sha256(src.tobytes()).hexdigest() == row['source_rgba_sha256']
    for key, hashkey in [('native_unadjusted', 'native_unadjusted_sha256'), ('output', 'output_sha256')]:
        data = Path(row[key]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == row[hashkey]
    im = Image.open(row['output']).convert('RGBA')
    assert im.size == (src.width * 8, src.height * 8)
    assert im.getchannel('A').getextrema() == (255, 255)
    dn = row['denoise_strength']
    row['visual_review'] = {
        'reviewer': 'Codex internal',
        'status': 'selected_for_game_review' if dn == .5 else 'not_selected',
        'reason': {
            .25: 'Warmer color is closer to source, but excessive fine surface relief remains comparatively strong.',
            .5: 'Best balance among reviewed variants: reduced fine relief with major light/dark shapes retained. Inferred detail remains; game-scale review is required.',
            .75: 'Stronger denoising softens fine structures and merges small material variations more than the middle setting.',
        }[dn],
        'scope': 'Static source and model comparison sheets only; no UV, repetition, mip or runtime acceptance.',
    }
    row['tiling_verified'] = row['runtime_verified'] = row['release_eligible'] = False
    verified.append({'asset_id': row['asset_id'], 'dn': dn, 'sha256': row['output_sha256']})
report['review_complete'] = True
report['selected_denoise_strength'] = .5
report['verification'] = {'outputs_checked': len(verified), 'records': verified}
p.write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf8')
for n, name in [(1, '로컬_업스케일_흙_재작업비교.png'), (17, '로컬_업스케일_잔해_재작업비교.png')]:
    src = R / f'outputs/local_sr_material_rework_{n:03d}.png'
    dest = C / 'outputs' / name
    shutil.copyfile(src, dest)
    assert hashlib.sha256(src.read_bytes()).digest() == hashlib.sha256(dest.read_bytes()).digest()
marker = '## 2026-09-23 — LOCAL-SR-002: 흙·잔해 중간 강도 재작업 검토'
progress = R / 'PROGRESS.md'
old = progress.read_text('utf8')
if marker not in old:
    old += '\n\n' + marker + '''

- 원본 tex001/017 각각 DNI0.25/0.5/0.75 총6조건 실제 RTX5080 FP32 추론. native4배 후 원본 평균RGB 오프셋을 명시 적용하고 Lanczos2배 출력. 보정 전 neural4x 파일도 보존. tools/rework_battle_materials.py, qa/local_sr_battle_material_rework_v2.json.
- Codex가 두 비교표를 직접 검수. 두 자산 모두0.5를 게임 검수 후보로 선택:0.25의 과한 세밀 요철을 줄이고0.75의 뭉개짐은 덜함. 질감은 모델의 추정이며 원본 고해상도 복원 확정이 아님. 색 평균·축소오차 수치를 품질 승인으로 쓰지 않음.
- 6개 후보의 원본RGBA 해시·출력파일 해시·8배 크기·불투명알파 확인. UV/반복/게임표시/배포 검증은 미완료. 실제 로컬 처리 고유 원본은 여전히7종; 재추론 조건을 새 원본 수로 더하지 않음.
- 사용자용 사본: C 작업폴더 outputs/로컬_업스케일_흙_재작업비교.png 및 로컬_업스케일_잔해_재작업비교.png. 원본과 SHA256 일치. 설치하지 않음.
- PPSSPP1.20.4 공식 GPUBufferSubscriber.cpp/Stepping.cpp 확인: 웹소켓 GPU버퍼 요청의 CPU 정지 조건만으로는 GE 정지 작업 실행을 보장하지 않음. 기존 CPU stepping Could not download output 경로는 반복하지 않음. 별도 QA를 ISO 명시 CLI로 실행하고 입력 없는 창 캡처 경로 검증을 진행.
- Fate/EXTRA qa/realesrgan-all.json 재확인: 로컬 anime6B, RTX5080,121개 파일, 모델 SHA256 일치. 앞선 로컬 모델 부재 발언은 Forge만 본 잘못된 단정이라는 정정 유지.
- 다음: 타이틀 실제 교체/합성 관측 → 전투재질 UV와 반복 소비 확인 → 처리 범위 확대. Orbit v4·LOCK ON·전체 지역/EX/진엔딩·최종ZIP 미완료, 목표 active.
'''
    progress.write_text(old, 'utf8')
print(json.dumps({'verified': len(verified), 'selected': .5, 'runtime_verified': False}))
