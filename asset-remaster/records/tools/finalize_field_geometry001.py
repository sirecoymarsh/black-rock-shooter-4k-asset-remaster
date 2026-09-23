"""Verify saved reconstructions and record bounded architectural geometry review."""
import copy, hashlib, json, shutil, xml.etree.ElementTree as ET
from pathlib import Path
import cv2
import numpy as np
from scipy.ndimage import gaussian_filter, label
from PIL import Image

R = Path(__file__).resolve().parents[1]
C = Path(r'C:\Users\CadriacLord\Documents\Codex\2026-09-22\brs-hd-ui-fonts')
Q = R / 'qa/field_geometry001_review.json'
assert not Q.exists()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text('utf8'))
def rgba(p): return np.asarray(Image.open(p).convert('RGBA'))
def write(p, d): Path(p).write_text(json.dumps(d, ensure_ascii=False, indent=2), 'utf8')

sourcepath = R / 'qa/field_geometry001_sources.json'
sources = read(sourcepath)
catpath = R / 'qa/field_sr_catalog.json'
contractpath = R / 'qa/architectural_geometry_contract.json'
assert sha(catpath) == sources['catalog_sha256_before']
assert sha(contractpath) == sources['geometry_contract_sha256_before']
cat = read(catpath); before = copy.deepcopy(cat); contract = read(contractpath)
previous = read(R / 'qa/field_sr003_review.json')
for rel, digest in previous['protected_file_hashes'].items(): assert sha(R / rel) == digest, rel
pack = R / 'workspace/local-sr/observed-review-pack-v2/PSP/TEXTURES/NPUH10126'
packhashes = {str(p.relative_to(pack)): sha(p) for p in pack.rglob('*') if p.is_file()}
assert packhashes == previous['pack_hashes']
for v in sources['files']:
    assert sha(v['source_ptm']) == v['source_ptm_sha256']
    assert hashlib.sha256(rgba(v['source']).tobytes()).hexdigest() == v['source_rgba_sha256']
    assert sha(v['parent']) == v['parent_sha256']

reports = [read(R / f'qa/field_windows00{i}.json') for i in (1, 2, 3)]
checked = []; pages = []
for p in sources['pages']:
    assert sha(p['path']) == p['sha256']
    pages.append({**p, 'review_status': 'directly_inspected', 'scope': 'source audit'})
for version, report in enumerate(reports, 1):
    for p in report['pages']:
        assert sha(p['path']) == p['sha256']
        pages.append({**p, 'review_status': 'directly_inspected', 'scope': f'window v{version} whole/crop'})
    for v in report['files']:
        for field in ('source_ptm', 'parent', 'vector', 'render', 'mask', 'classes', 'frame_mask', 'geometry_parent', 'output'):
            if field in v: assert sha(v[field]) == v[field + '_sha256'], (v['id'], field)
        s = rgba(v['source']); p = rgba(v['parent']); out = rgba(v['output'])
        assert hashlib.sha256(s.tobytes()).hexdigest() == v['source_rgba_sha256']
        assert out.shape == (s.shape[0] * 8, s.shape[1] * 8, 4)
        mask = np.asarray(Image.open(v['mask'])) > 0
        classes = np.asarray(Image.open(v['classes']))
        expected_mask = np.zeros(mask.shape, bool); expected_classes = np.zeros(mask.shape, np.uint8)
        x0, y0, x1, y1 = v['plan']['outer']; expected_mask[y0*8:y1*8, x0*8:x1*8] = True
        for index, (a, b, c, d) in enumerate(v['plan']['panes'], 1): expected_classes[b*8:d*8, a*8:c*8] = index
        assert np.array_equal(mask, expected_mask) and np.array_equal(classes, expected_classes)
        frame = mask & (classes == 0)
        assert np.array_equal(out[~mask], p[~mask]) and np.all(out[:, :, 3] == 255)
        binary = out[y0*8:y1*8, x0*8:x1*8, :3].mean(2) < 108
        assert np.array_equal(binary, classes[y0*8:y1*8, x0*8:x1*8] > 0)
        assert label(binary, np.ones((3,3)))[1] == len(v['plan']['panes'])
        coverage = np.zeros(mask.shape, np.uint8)
        root = ET.parse(v['vector']).getroot()
        assert all('transform' not in node.attrib for node in root.iter())
        for rect in root.iter('{http://www.w3.org/2000/svg}rect'):
            assert not any(k in rect.attrib for k in ('rx', 'ry'))
            a, b, w, h = [int(rect.attrib[k]) for k in ('x', 'y', 'width', 'height')]
            coverage[b*8:(b+h)*8, a*8:(a+w)*8] += 1
        assert np.array_equal(coverage, frame.astype(np.uint8))
        rebuilt = p.copy()
        if version == 1:
            rendered = rgba(v['render']); assert np.array_equal(rendered[:,:,3] > 0, frame)
            high = p[:,:,:3].astype(np.float32) - gaussian_filter(p[:,:,:3].astype(np.float32), (8,8,0), mode='nearest')
            colors = np.rint(np.clip(rendered[:,:,:3].astype(np.float32) + np.clip(high * .2, -3, 3), v['plan']['frame_floor'], 253)).astype('uint8')
            rebuilt[:,:,:3][frame] = colors[frame]
        else:
            assert np.array_equal(np.asarray(Image.open(v['frame_mask'])) > 0, frame)
            for bar in v['frame_bars']:
                assert sha(bar['map']) == bar['map_sha256']
                maps = np.load(bar['map']); a, b, c, d = bar['output_box']
                material = cv2.remap(p[:,:,:3], maps['map_x'], maps['map_y'], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
                rebuilt[b:d,a:c,:3] = np.clip(material, v['plan']['frame_floor'], 253).astype('uint8')
        rebuilt[:,:,:3][classes > 0] = np.minimum(p[:,:,:3][classes > 0], v['plan']['glass_max_rgb'])
        rebuilt[:,:,3][mask] = 255
        if version == 3:
            assert np.array_equal(rebuilt, rgba(v['geometry_parent']))
            pad = v['glass_inner_padding_output_px']; assert pad == 8
            for a, b, c, d in v['plan']['panes']:
                inner = p[b*8:d*8, a*8:c*8, :3][pad:-pad,pad:-pad]
                fill = cv2.copyMakeBorder(inner, pad, pad, pad, pad, cv2.BORDER_REPLICATE)
                rebuilt[b*8:d*8,a*8:c*8,:3] = np.minimum(fill, v['plan']['glass_max_rgb'])
            assert np.array_equal(out[classes == 0], rgba(v['geometry_parent'])[classes == 0])
        assert np.array_equal(rebuilt, out), v['id']
        decisions = {1: ('rejected', 'Frame colors look like flat newly pasted strips.'), 2: ('superseded', 'Exact rectangle classes still contain rounded bright remnants inside glass edges.'), 3: ('static_candidate', 'Straight source-anchored frames and six rectangular openings; aged local material retained, old curved glass-edge remnants removed.')}
        status, reason = decisions[version]
        checked.append({'id': v['id'], 'group_id': v['group_id'], 'path': v['output'], 'sha256': v['output_sha256'], 'decision': status, 'reason': reason, 'source_ptm_rgba_and_lineage_hashes_verified': True, 'saved_recipe_reproduces_rgba_exactly': True, 'axis_aligned_vector_and_exact_frame_coverage': True, 'declared_pane_class_exact_threshold108': True, 'pane_count': len(v['plan']['panes']), 'outside_mask_parent_rgba_exact': True, 'runtime_verified': False, 'release_eligible': False})

holds = {
 'FM0189': 'Source-audit whole image shows bowed central mullions and uneven horizontal frame/header edges. Earlier material acceptance is revoked under the straight-line gate; source-anchored frame/shutter reconstruction remains required. Visual finding, not a claimed complete geometric measurement.',
 'FM0190': 'Source-audit whole image shows uneven window frame/sill edges and altered brick-column alignment. Earlier material acceptance is revoked; source-defined straight frame and horizontal band geometry is required. Original surface weathering is not itself a defect.'
}
audit_notes = {
 'FM0029': 'Grille source x32..54/y0..19 has alternating opaque/transparent phases; crossing rows5/10/15 invert ordinary row phase. Do not replace it with continuous bars. Right lower yellow window has4 columns by2 rows; upper transom has3. No repair this batch.',
 'FM0113': 'Upper grid horizontal dark rows1/6/12/18/24/29 and lower diagonal X braces require source anchors. Do not equate threshold-derived columns with physical bar count. No repair this batch.',
 'FM0037': 'Preserve perspective slopes of roof and side-face windows; locally bowed edges need anchored quadrilaterals. No repair this batch.',
 'FM0038': 'Multiple facades and cornices include perspective slopes; local sill/column waviness needs anchored straight segments. No repair this batch.',
 **holds
}
changed = {'FM0257', 'FM0258', *holds}
selected = {v['group_id']: v for v in reports[2]['files']}
for g in cat['groups']:
    gid = g['group_id']
    if gid in changed:
        g.setdefault('candidate_history', []).append({'candidate': copy.deepcopy(g['candidate']), 'superseded_by_review': 'qa/field_geometry001_review.json', 'reason': holds.get(gid, 'Source-anchored window reconstruction selected.')})
    if gid in holds:
        g['candidate'] = None; g['status'] = 'held'; g['hold_reason'] = holds[gid]
    elif gid in selected:
        v = selected[gid]
        g['candidate'] = {'id': v['id'], 'path': v['output'], 'sha256': v['output_sha256'], 'review': 'qa/field_geometry001_review.json', 'method': v['method'], 'runtime_verified': False, 'release_eligible': False}
        g['geometry_review_scope'] = 'Declared pane/frame rectangles only; source1px glass-edge material extrapolation, unchanged exterior local pixels, no UV/runtime proof.'
for old, new in zip(before['groups'], cat['groups']):
    if old['group_id'] not in changed: assert old == new
stats = cat['processing_summary']
stats['field_static_candidates'] = sum(g['candidate'] is not None for g in cat['groups'])
stats['field_holds'] = sum(g['status'] == 'held' for g in cat['groups'])
stats['latest_review'] = 'qa/field_geometry001_review.json'
assert (stats['field_static_candidates'], stats['field_holds'], stats['field_neural_originals'], stats['remaining_novel_unprocessed']) == (71, 24, 95, 256)
key = 'historical_field_candidates_pending_geometry_applicability_review'
assert len(contract[key]) == 61
contract[key] = [gid for gid in contract[key] if gid not in changed]
assert len(contract[key]) == 57
contract['geometry_review001'] = {'review': 'qa/field_geometry001_review.json', 'selected_reconstructions': {gid: v['id'] for gid, v in selected.items()}, 'scope': 'Six pane rectangles and12 frame bars. Other facade material remains the historical local output; no full-game/UV/runtime proof.', 'historical_candidates_revoked': holds, 'existing_holds_audited_without_repair': {k:v for k,v in audit_notes.items() if k not in holds}}

backup = R / 'qa/backups/before-field-geometry001-review'; backup.mkdir(parents=True, exist_ok=False)
for p in (catpath, contractpath): shutil.copy2(p, backup / p.name)
write(catpath, cat); write(contractpath, contract)
for rel, digest in previous['protected_file_hashes'].items(): assert sha(R / rel) == digest
assert {str(p.relative_to(pack)): sha(p) for p in pack.rglob('*') if p.is_file()} == packhashes
preview = C / 'outputs/창틀_직선_직각_수정_비교.png'
ims = [Image.open(R / f'outputs/field-geometry001/windows-v3-{gid}-windows.png').convert('RGB') for gid in selected]
canvas = Image.new('RGB', (max(i.width for i in ims), sum(i.height for i in ims) + 16), '#26333f')
y = 0
for im in ims: canvas.paste(im, (0,y)); y += im.height + 16
canvas.save(preview)
review = {'schema': 'brs-field-geometry-review/v1', 'batch': 'FIELD-GEOMETRY-001', 'previous_goal_turn_classification': sources['previous_goal_turn_classification'], 'new_neural_unique_originals': 0, 'new_local_inference_passes': 0, 'external_generative_calls': 0, 'derived_outputs': 6, 'source_groups_audited': 8, 'checked_outputs': checked, 'pages_directly_inspected': pages, 'audit_findings': audit_notes, 'selected_replacements': {k:v['id'] for k,v in selected.items()}, 'historical_candidates_revoked': holds, 'source_reports_sha256': {str(p.relative_to(R)): sha(p) for p in [sourcepath, *[R/f'qa/field_windows00{i}.json' for i in (1,2,3)]]}, 'catalog_before_sha256': sources['catalog_sha256_before'], 'catalog_after_sha256': sha(catpath), 'geometry_contract_before_sha256': sources['geometry_contract_sha256_before'], 'geometry_contract_after_sha256': sha(contractpath), 'field_processing_summary': stats, 'unique_neural_originals_title_battle_novel_field': 352, 'protected_file_hashes': previous['protected_file_hashes'], 'pack_hashes': packhashes, 'other572_field_groups_unchanged': True, 'preview': {'path': str(preview), 'sha256': sha(preview)}, 'limits': ['FM0258 equal10-source-pixel openings use bright bar peaks9/20/31/42/53 as11px pitch; low-resolution bevel texels are interpreted, not copied byte-exactly.', 'Glass edge padding extends existing local interior color by1source pixel. No newly recovered detail or new neural inference is claimed.', 'Threshold/connected-component checks prove the declared masks only; direct visual review found the v2 curved residue despite passing those checks.', 'Only static source/frame review. Unknown consumer UV/repeat, observed texture keys and actual game rendering remain open.'], 'next_action': 'Source-anchor FM0189/0190 facade frames and horizontal bands; continue FM0029/0113 grille and FM0037/0038 perspective geometry. Remaining field256 originals, battle43 unresolved, other game asset inventories and runtime verification remain.', 'runtime_verified': False, 'release_eligible': False, 'all_game_complete': False, 'scripts': {p.name: sha(p) for p in [R/'tools/prepare_field_geometry001.py', R/'tools/redraw_field_windows001.py', R/'tools/redraw_field_windows002.py', R/'tools/refine_field_window_glass.py', Path(__file__)]}}
write(Q, review)
with (R/'PROGRESS.md').open('a',encoding='utf8') as f:
    f.write('\n\n## 2026-09-23 — FIELD-GEOMETRY-001 / 원본 직선·직각 재검수\n- 이전 FIELD-SR-003는 progress. 이번은8원본 audit와창틀2종 직접수정/6파생출력 검증 및기존2후보철회로 progress. 신규원본/로컬추론/외부생성0, 전체목표active.\n- FM0257/0258 창틀 v1은붙임판 같은재질로제외. v2는원본좌표·2/4직사각창·12막대가맞아도유리안쪽둥근밝은잔재가남아대체. v3는기존로컬유리안쪽재질을1source픽셀연장해잔재제거,선택. 세로pitch8/11source px,FM0258밝은bar9/20/31/42/53근거4동일10px개구부해석;source RGBA정확복원아님.\n- 전체6결과 원본PTM/RGBA·부모·SVG/render/map/mask/classes/output SHA,8배크기/alpha255/mask밖RGBA정확/축정렬rect·12bar coverage 및저장recipe로RGBA재현검증. 클래스검사만으로시각충실도주장안함. source10페이지+whole/crop12페이지직접검수. qa/field_geometry001_review.json.\n- FM0189/0190 기존재질후보는창틀/수평경계휨으로철회,원본anchor재작업보류. FM0029교차행alpha위상/오른쪽하단4x2창·상단3칸,FM0113상단grid/하단Xbrace,FM0037/0038원근구조audit만완료;재작업완료아님.\n- 현재field95neural/71정적후보/24보류/novel256미처리. 과거field geometry적용여부대기57, battle241동일. title1+battle256+field95=실제neural고유352. catalog변경4그룹외572동일,보호원본/전투카탈로그/20key팩바이트보존.\n- 사용자비교 outputs/창틀_직선_직각_수정_비교.png. 설치/에뮬실행/실게임검증/최종ZIP미완료. 다음189/190창틀/가로띠anchor재구성,29/113격자와37/38원근구조,잔여field/적/효과/컷신계속.\n')
with (C/'outputs/로컬_업스케일_진행.md').open('a',encoding='utf8') as f:
    f.write('\n\n## 창틀의 직선·직각 수정 — FIELD-GEOMETRY-001\n- 창틀2종의 원본 창6칸과 간격을 기준으로 직접 수정했습니다. 기존 로컬 재질은 살리고, 모서리 안쪽에 남은 둥근 테두리까지 고친 세 번째 안을 정적 후보로 골랐습니다. 새 AI 추론은0회입니다.\n- 기존 건물 후보2종도 선이 휘어 재작업 대상으로 돌렸습니다. 수정본 밖의 그림 보존과 원본 좌표·저장된 수정 과정의 재현을 확인했습니다.\n- 현재 필드 후보71종/보류24종/미처리256종입니다. 전투43종 미해결과 캐릭터·적·효과, 게임 적용 검수·최종 배포도 남았습니다. 이번 결과는 파일 비교 검수이며 게임에서 확인한 완료본은 아닙니다.\n')
print(json.dumps({'review': str(Q), 'checked_outputs': len(checked), 'pages_inspected': len(pages), 'field_summary': stats, 'preview': str(preview)},ensure_ascii=False))
