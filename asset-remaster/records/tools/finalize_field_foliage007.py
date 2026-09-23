from pathlib import Path
import sys,json,hashlib,copy,shutil
sys.dont_write_bytecode=True
R=Path(r'P:\AI\Codex\projects\black-rock-shooter-hd-ui-fonts')
C=Path(r'C:\Users\CadriacLord\Documents\Codex\2026-09-22\brs-hd-ui-fonts')
Q=R/'qa/field_foliage007_review.json'
assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text('utf8'))
def write(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False),'utf8')
vp=C/'work/field_foliage007_validation.json';v=read(vp)
last=read(R/'qa/field_foliage006_review.json')
cp=R/'qa/field_sr_catalog.json';gp=R/'qa/architectural_geometry_contract.json'
assert sha(cp)==v['catalog_before_sha256']==last['catalog_after_sha256']
assert sha(gp)==v['geometry_contract_before_sha256']==last['geometry_contract_after_sha256']
cat=read(cp);before=copy.deepcopy(cat);contract=read(gp)
for rel,h in v['source_reports_sha256'].items():assert sha(R/rel)==h
for rel,h in v['protected_file_hashes'].items():assert sha(R/rel)==h
pack=R/'workspace/local-sr/observed-review-pack-v2/PSP/TEXTURES/NPUH10126'
assert {str(p.relative_to(pack)):sha(p) for p in pack.rglob('*') if p.is_file()}==v['pack_hashes']
for g in cat['groups']:
    if g['candidate']:assert sha(g['candidate']['path'])==g['candidate']['sha256']
for p in v['checked_outputs']:assert sha(p['path'])==p['sha256']
for p in v['source_and_comparison_pages']:assert sha(p['path'])==p['sha256']
selected={p['group_id']:p for p in v['checked_outputs'] if p['id'].endswith('v4')}
assert set(selected)=={'FM0314','FM0316','FM0317','FM0325'}
method='Original-coordinate canopy and material-class-gated trunk reconstruction; existing local Photo parent and previously generated GPT leaf/bark material reused with native-scale affine grain. Own source palette and alpha; no new neural/GPT inference.'
for g in cat['groups']:
    gid=g['group_id']
    if gid not in selected:continue
    p=selected[gid]
    assert g['status']=='held' and g['candidate'] is None and g['local_sr_attempted']
    g.update(status='static_candidate',hold_reason=None,candidate={'id':p['id'],'path':p['path'],'sha256':p['sha256'],'review':'qa/field_foliage007_review.json','method':method,'geometry_review':'Own source color classes gate bark and original coordinates orient six material tracks. Source-center alpha exact; small canopy edge variation changes fine components and holes. Below-canopy alpha, protected lower-left and bottom three source rows are exactly the local parent. Not exact RGB geometry/topology or runtime proof.','runtime_verified':False,'release_eligible':False})
for a,b in zip(before['groups'],cat['groups']):
    if a['group_id'] not in selected:assert a==b
stats=cat['processing_summary']
stats.update(field_static_candidates=113,field_holds=49,latest_review='qa/field_foliage007_review.json',counting_note='158 locally inferred originals +3 direct-GPT-only +1 geometry-only =162 processed novel field originals. Four existing tree holds become candidates using existing materials; no new originals or inference calls. Static candidate113, held49, novel unprocessed189.')
assert sum(bool(g['candidate']) for g in cat['groups'])==113
assert sum(g['status']=='held' for g in cat['groups'])==49
assert sum(g['local_sr_attempted'] for g in cat['groups'])==158
assert sum(g['status']=='not_processed_in_field_context' for g in cat['groups'])==414
assert stats['remaining_novel_unprocessed']==189 and stats['field_processed_novel_originals_all_routes']==162
for gid in selected:contract['current_batch_geometry_holds'].pop(gid,None)
contract['field_foliage007_review']={'review':'qa/field_foliage007_review.json','resolved_holds':{gid:p['id'] for gid,p in selected.items()},'method':method,'source_geometry_limits':'Six source-coordinate tracks are material orientation controls, not a total tree count. Own decoded RGB/material gate determines coverage. Source-center alpha preserved, but fine canopy topology changes; this does not relax architectural holes or checker geometry rules.','source_palette_variant_check':'FM0316/FM0317 have19 material-class differences versus314 in jointly opaque lower source pixels;FM0325 has0. Each output uses its own source RGB and mask. Shared runtime consumers are not established.','new_local_passes':0,'new_external_calls':0,'new_unique_originals':0,'runtime_verified':False,'release_eligible':False}
reasons={
    'FM0314-source-material-v1':'Narrow material strip, missing central right arm and material caps; not selected.',
    'FM0314-source-material-v2':'Per-segment donor stretching produced obvious striped/chevron bands and seams; not selected.',
    'FM0314-source-material-v3':'Affine native-scale bark and weighted junctions fix bands; superseded byv4 to avoid undefined transparent donor RGB and support each source palette.'}
checked=copy.deepcopy(v['checked_outputs'])
for p in checked:
    if p['group_id'] in selected and p['id']==selected[p['group_id']]['id']:
        p['decision']='static_candidate'
        p['reason']='Source palettes/clipping reviewed individually on dark/light mattes. Leaves read as leaves, bark follows source-controlled trunk regions, previous stretched grain bands are absent. Fine-edge alpha differences are recorded and remain unverified in game.'
    else:p.update(decision='not_selected',reason=reasons[p['id']])
preview_source=R/'outputs/field-foliage007/FM0325-source-material-v4-whole.png'
preview=R/'outputs/field-foliage007/나무_잎과_껍질_재질_수정.png'
shutil.copy2(preview_source,preview)
local_preview=C/'outputs'/preview.name;shutil.copy2(preview,local_preview)
assert sha(preview)==sha(preview_source)==sha(local_preview)
validation=R/'qa/field_foliage007_validation.json';assert not validation.exists();shutil.copy2(vp,validation)
script_names=['audit_tree_geometry007.py','tree_material007.py','build_tree_material007.py','build_tree_material007_v2.py','build_tree_material007_v3.py','build_tree_material007_v4.py','validate_tree_material007.py','finalize_field_foliage007.py']
scripts=[]
for name in script_names:
    src=C/'work'/name;dest=R/'tools'/name;shutil.copy2(src,dest);assert sha(src)==sha(dest)
    scripts.append({'path':str(dest),'sha256':sha(dest)})
backup=R/'qa/backups/before-field-foliage007-review';backup.mkdir(exist_ok=False)
for p in [cp,gp]:shutil.copy2(p,backup/p.name)
write(cp,cat);write(gp,contract)
report={'schema':'brs-field-foliage007-final-review/v1','batch':'FIELD-FOLIAGE-007','previous_goal_turn_classification':'progress: nine foliage originals compared via actual local inference and GPT redraw; one weed candidate selected, tree material donor identified but geometry held','this_goal_turn_classification':'progress: original tree material regions inspected, seven reconstructions replayed; four existing holds resolved into static candidates','new_local_neural_unique_originals':0,'actual_local_RGB_passes':0,'actual_alpha_neural_passes':0,'external_generative_calls':0,'new_direct_GPT_only_unique_originals':0,'new_geometry_only_unique_originals':0,'method':method,'checked_outputs':checked,'resolved_holds':{gid:p['id'] for gid,p in selected.items()},'new_holds':{},'source_reports_sha256':v['source_reports_sha256'],'validation':{'path':str(validation),'sha256':sha(validation)},'GPT_provenance':{'path':v['GPT_provenance_path'],'sha256':v['GPT_provenance_sha256'],'call_performed_in_batch':'FIELD-FOLIAGE-006','new_call_in_this_batch':False},'source_and_comparison_pages':v['source_and_comparison_pages'],'pages_total':45,'pages_directly_inspected':41,'material_donor_crop_pages_directly_inspected':2,'source_wood_classes':v['source_wood_classes'],'source_wood_class_limit_correction':v['classification_limit_correction'],'catalog_before_sha256':v['catalog_before_sha256'],'catalog_after_sha256':sha(cp),'geometry_contract_before_sha256':v['geometry_contract_before_sha256'],'geometry_contract_after_sha256':sha(gp),'other572_field_groups_unchanged':True,'previous109_field_candidates_unchanged':True,'field_processing_summary':stats,'unique_local_neural_originals_title_battle_novel_field':415,'processed_originals_title_battle_novel_field_all_routes':421,'all_routes_count_basis':{'title':1,'battle':258,'novel_field':162},'known_battle_plus_novel_field_progress':{'denominator':635,'static_candidates':354,'static_candidate_percent':354/635*100,'processed_at_least_once':420,'processed_percent':420/635*100,'is_entire_game_completion_percent':False},'protected_file_hashes':v['protected_file_hashes'],'pack_hashes':v['pack_hashes'],'scripts':scripts,'preview':{'path':str(local_preview),'project_path':str(preview),'sha256':sha(preview),'review_status':'directly_inspected_exact_copy_of_FM0325_v4_whole'},'runtime_verified':False,'release_eligible':False,'all_game_complete':False,'limits':[
    'Leaf/bark material is reused from one previously generated GPT image. This batch performs no new local neural/GPT inference and is not described as purely local neural upscaling.',
    'All seven historical/final reconstructions reproduce their saved RGBA exactly using hash-bound frozen programs. The current helper isv4; old builders import its module name and must not be rerun as historical recipes. Replay the frozen helper identified by each attempt report.',
    'V4 source-center alpha is exact at8x phase4; total alpha mass differs by at most0.075percent. BOX source-scale masks disagree at7/11/10/9 pixels. This does not mean full-resolution alpha or topology is exact.',
    'Fine canopy edge variation changes foreground components/holes. At alpha128 components lacking an opaque source-center sample are11..14 per image, at most6 output pixels each. Components containing source samples can also split. These are accepted as static fine-edge differences after visual review; game alpha testing remains unverified.',
    'Each source palette, clipping mask and lower backdrop is used independently. Six material axes orient grain; they do not prove a total tree count, shared consumer or every RGB edge being geometrically exact.',
    'Bark placement changes color/shading inside source-controlled regions; original-source filtering and material blending do not constitute high-resolution ground truth.',
    'Lower-left source rectangle0,108..28,128 and bottom source rows125..127 remain exactly the local parent. Below-canopy alpha is exact parent; no claim that all lower background RGB outside these controls is original-pixel-identical.',
    '41 of45 source/comparison pages directly inspected; four redundantv2 pages skipped after trunk detail revealed material bands. Two material-bank crop pages inspected separately.',
    'Remaining field49 holds and189 novel unprocessed; battle43 unresolved; historical geometry applicability, character/enemy/UI/effect/cutscene and unsupported source populations remain.635 is only the currently classified battle plus novel-field population.',
    'No new texture key, emulator launch, installation, game verification or release ZIP. Native GUI unavailable; Explorer opening not claimed.'
],'next_action':'Continue remaining foliage holdsFM0301,FM0312,FM0318,FM0320 with own-source material interpretation, then architectural/mechanical holds and189 unprocessed novel field originals. Preserve source geometry and use local-first plus inspected direct repair as appropriate; continue battle43 and other whole-game scope.'}
for rel,h in v['protected_file_hashes'].items():assert sha(R/rel)==h
assert {str(p.relative_to(pack)):sha(p) for p in pack.rglob('*') if p.is_file()}==v['pack_hashes']
write(Q,report)
note='''

## 2026-09-23 — FIELD-FOLIAGE-007 / 나무4종 원본 구조·잎과 나무껍질
- 기존314/316/317/325 보류4종을 원본별 색·alpha·잘림·하단 배경으로 재구성. 새고유원본/로컬추론/GPT호출0. 이전006 실제 GPT314 재질과 각 로컬Photo를 사용하므로 순수로컬 AI 확대라고 표시하지 않음.
- 원본 좌표 수관경계와6재질방향 track, 본인source색분류로 나무껍질 범위 제한. v1 좁은재질띠/branch누락, v2 분할좌표늘림의 줄무늬 실패. v3 native donor-scale affine+분기 weighted blend로 해결; v4 본인palette대비/threshold,투명donor RGB배제·검증leafbank로 가장자리재질 보완. 최종v4 네종 정적후보.
- 316/317 source분류 공통하단19픽셀씩314와상이,325는0. 각자마스크사용하며 소비자동일/원본전체동일 주장안함. 7출력 frozenrecipe RGBA재현·원본/PTM/부모/model/GPTraw/prompt/reference/vector/mask/outputhash 검증. source/비교45페이지중41직접검수,v2실패후중복4미검수;donor crop2별도검수.
- source센터alpha8배phase4정확,총alpha질량비.9994263/.9996350/.9999956/.9992547. BOX원본규모IoU.999303/.999010/.998973/.999097이며7/11/10/9샘플상이. 미세edgevariation으로alpha128분리조각/구멍수는원본과다름;source센터없는작은조각최대6출력픽셀,source센터포함구성도분리가능. static수용/실게임alpha-test미검증,완전topology보존주장안함.
- 수관아래alpha,원본좌하단(0,108)-(28,128),마지막3source행RGBA는부모정확. 재질방향6개는총나무개수의증거아님. qa/field_foliage007_review.json authoritative;다른572fieldgroup·기존109후보·보호5파일·20key팩22파일불변.
- field113정적후보/49보류/189novel미처리. local158+GPT-only3+geometry-only1=162처리유지,전체조사범위local415/allroutes421유지. 확정battle284+novelfield351=635에서354후보55.75%,한번이상420처리66.14%. 전체게임완료율아님. 설치/실게임/최종ZIP미완료,전체목표active.
- 다음foliage301/312/318/320 원본별재질수정,기존기계/건축보류·field189/battle43·인물/적/효과/컷신및미지원원본. GUI복구증거없어에뮬실행/검은화면반복없음. outputs/field-foliage007/나무_잎과_껍질_재질_수정.png.
'''
for p in [R/'PROGRESS.md',C/'outputs/로컬_업스케일_진행.md']:
    with p.open('a',encoding='utf8') as f:f.write(note)
print(json.dumps({'review':str(Q),'selected':list(selected),'field_candidates':113,'field_holds':49,'known_scope_candidate_percent':354/635*100,'known_scope_processed_percent':420/635*100,'preview':str(preview)},ensure_ascii=False))
