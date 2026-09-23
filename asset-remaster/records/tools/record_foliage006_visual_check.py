from pathlib import Path
import json, hashlib
from datetime import datetime, timezone

R = Path(r'P:\AI\Codex\projects\black-rock-shooter-hd-ui-fonts')
raw_path = R / 'qa/field_foliage006_local.json'
out_path = R / 'qa/field_foliage006_visual_check.json'
assert not out_path.exists(), 'Do not overwrite an existing review.'
def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()
raw = json.loads(raw_path.read_text('utf8'))
assert raw['actual_local_RGB_passes'] == 18
assert len(raw['files']) == 18 and len(raw['pages']) == 18
for item in raw['files']:
    for key in ('input', 'alpha', 'native_full', 'native', 'output'):
        assert sha(item[key]) == item[key + '_sha256']
for item in raw['pages']:
    assert sha(item['path']) == item['sha256']

notes = {
    'FM0290': 'Both local models soften thin leaves/tips into rounded waxy or melted blobs; no selection.',
    'FM0301': 'Broad radial leaf identity remains, but waxy surfaces and weak leaf structure require another treatment; no selection.',
    'FM0312': 'WDN flattens canopy material; Photo adds conspicuous pale granular structures. Source foliage character is not reliably restored; no selection.',
    'FM0314': 'Both models reinterpret pale canopy areas as flat cracked planes; whole-image trunks also flatten. Reject these material interpretations.',
    'FM0316': 'Canopy detail is more plausible than the dark variant, but pale patches and block-like trunks need source comparison and an alternative preprocessing trial before selection.',
    'FM0317': 'Similar to FM0316: canopy grain alone does not establish acceptable tree structure; broad flattened trunk regions remain. No selection.',
    'FM0318': 'WDN resembles a soft continuous mottled surface; Photo introduces coarse pale speckling. Neither demonstrates convincing source-faithful foliage.',
    'FM0320': 'WDN has fuzzy compact-mass appearance; Photo has stone-like granular/cracked detail. Neither selected.',
    'FM0325': 'Pale canopy becomes cracked flat planes in both models, with block-like trunks. Reject these material interpretations.'
}
assert set(notes) == {x['group_id'] for x in raw['prepared_sources']}
current = {'FM0314-local-native.png', 'FM0316-local-whole.png', 'FM0316-local-native.png',
           'FM0317-local-whole.png', 'FM0317-local-native.png', 'FM0318-local-whole.png',
           'FM0318-local-native.png', 'FM0320-local-whole.png', 'FM0320-local-native.png',
           'FM0325-local-whole.png', 'FM0325-local-native.png'}
report = {
    'schema': 'brs-field-foliage006-interim-visual-check/v1',
    'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
    'local_report': str(raw_path), 'local_report_sha256': sha(raw_path),
    'actual_local_RGB_passes_so_far': 18,
    'new_local_unique_originals_in_raw_report': 9,
    'selected_outputs': [], 'catalog_finalized': False,
    'inspection': [{'group_id': gid, 'decision': 'needs_rework', 'finding': note}
                   for gid, note in notes.items()],
    'pages': [{**p, 'review_status': 'directly_visually_inspected',
               'inspection_turn': 'current' if Path(p['path']).name in current else 'prior_continuation'}
              for p in raw['pages']],
    'validation': 'All 18 saved input/alpha/native-full/native/output hashes and all 18 comparison-page hashes match the raw inference record. Alpha topology checks are recorded in the raw report; not independently replayed in this status turn. Geometry checks do not establish material quality or runtime behavior.',
    'changed_hypothesis': 'Nearest-opaque RGB fill before inference removes alpha/background separation from the model input. This may contribute to continuous-surface interpretations. This is an untested hypothesis, not an established cause.',
    'next_executable_step': 'Compare representative FM0290 and FM0314 using original authored source RGB/matte instead of nearest-opaque hidden-RGB fill, with the same WDN/Photo models. Keep source alpha protected separately, inspect leaf tips, canopy and trunks on both mattes. If material identity remains poor, change local prior or use an explicit source-guided repaint; do not repeat grain-strength tuning.',
    'confirmed_catalog_counts_unchanged': {
        'battle_unique': 284, 'novel_field_unique': 351,
        'battle_candidates': 241, 'field_candidates': 108,
        'battle_any_method': 258, 'field_any_method': 153,
        'candidate_fraction_known_battle_and_novel_field': 349/635,
        'processed_fraction_known_battle_and_novel_field': 411/635,
        'scope': 'Known battle and novel field textures only; excludes title and unresolved whole-game populations. Nine unfinished foliage sources are not added to the finalized catalog yet.'
    },
    'runtime_verified': False, 'installed': False, 'release_eligible': False
}
out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False), 'utf8')
note = '''

## 2026-09-23 — FIELD-FOLIAGE-006 / 로컬18출력 중간 시각검수
- 사용자 퍼센트 질문: 확정된 battle284+novel field351=635종에서 정적후보349(약55%), 한번 이상 처리411(약65%). 전체 게임 완료율이 아니며 설치/실게임 검수 미완료.
- foliage9종 로컬RGB18회는 이미 완료. 이전 직접검수7페이지에 이번11페이지를 더해 원본/WDN/Photo 양배경 비교18페이지 전부 직접검수. 저장input/alpha/native-full/native/output와 비교페이지hash 전부 raw기록과 일치.
- 신규 선정0. 314/325의 수관이 갈라진 평면으로 바뀌고, 290/301의 잎은 둥글고 왁스 같음. 312/318/320도 연속 얼룩/돌 같은 과장 입자로 보임. 316/317은 상대적으로 나으나 줄기의 평평한 블록 해석이 남아 보류. alpha 연결/구멍 수 검사가 재질 품질의 합격 근거는 아님.
- qa/field_foliage006_visual_check.json에 9종 판정/18페이지 검수와 다음 가설 기록. raw local report는 불변. catalog 미확정이므로 field108후보/45보류/198미처리 등 최종 집계 그대로; 이 9종을 최종집계에 중복 추가하지 않음.
- 다음 실행: 290/314 대표원본에서 nearest-opaque hidden-RGB 채움 대신 원본 RGB/matte를 모델에 제공하는 변경가설을 같은 WDN/Photo로 비교. 원본 alpha 별도 보호, 잎끝/수관/줄기와 밝고 어두운 배경 확인. 전처리가 원인이라는 확정 아님. 그래도 미달이면 다른 local prior 또는 source-guided 직접재작화로 전환. 전체목표 active, 에뮬실행/설치/새키 변경 없음.
'''
with (R/'PROGRESS.md').open('a', encoding='utf8', newline='') as f:
    f.write(note)
print(json.dumps({'interim_review': str(out_path), 'inspected_pages': 18, 'new_candidates': 0, 'catalog_changed': False}))
