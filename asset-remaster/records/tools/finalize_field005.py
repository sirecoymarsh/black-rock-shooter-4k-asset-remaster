"""Bounded geometry/material QA and honest whole-atlas versus region decisions."""
from pathlib import Path
import json,hashlib,copy,shutil,xml.etree.ElementTree as ET
import numpy as np,cv2
from PIL import Image
R=Path(__file__).resolve().parents[1];C=Path(r'C:\Users\CadriacLord\Documents\Codex\2026-09-22\brs-hd-ui-fonts');Q=R/'qa/field_geometry005_review.json';assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text('utf8'))
def arr(p):return np.asarray(Image.open(p).convert('RGBA'))
def write(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2),'utf8')
prev=read(R/'qa/field_geometry004_review.json');names=['field_geometry005_trials.json','field_geometry005_authored.json','field_geometry005_material_v3.json'];reports=[read(R/'qa'/n) for n in names];one,two,three=reports;cp=R/'qa/field_sr_catalog.json';gp=R/'qa/architectural_geometry_contract.json';cat=read(cp);before=copy.deepcopy(cat);contract=read(gp)
assert sha(cp)==prev['catalog_after_sha256']==one['catalog_before_sha256'];assert sha(gp)==prev['geometry_contract_after_sha256']==one['geometry_contract_before_sha256'];assert two['parent_report_sha256']==sha(R/'qa'/names[0]);assert three['parent_report_sha256']==sha(R/'qa'/names[1])
for rel,h in prev['protected_file_hashes'].items():assert sha(R/rel)==h
pack=R/'workspace/local-sr/observed-review-pack-v2/PSP/TEXTURES/NPUH10126';packhash={str(p.relative_to(pack)):sha(p) for p in pack.rglob('*') if p.is_file()};assert packhash==prev['pack_hashes']
checked=[];allrows={}
for ver,report in enumerate(reports,1):
 for v in report['files']:
  s=arr(v['source']);o=arr(v['output']);p=arr(v['parent']);h,w=s.shape[:2];assert hashlib.sha256(s.tobytes()).hexdigest()==v['source_rgba_sha256'];assert o.shape==(h*8,w*8,4)
  for key in ['source_ptm','parent','output','mask','vector','base_planes','alpha_vector','alpha_render','previous','gpt_raw','gpt_prompt','geometry_vector']:
   if key in v:assert sha(v[key])==v[key+'_sha256'],(v['id'],key)
  mask=np.asarray(Image.open(v['mask']))>0
  if ver==1:assert np.array_equal(o[~mask],p[~mask])
  elif v['group_id']=='FM0029' and ver==2:assert np.array_equal(o[~mask],arr(v['previous'])[~mask]);assert np.array_equal(o[:,:,3],arr(v['previous'])[:,:,3])
  elif ver==3:assert np.array_equal(o[~mask],p[~mask]);assert np.array_equal(o[:,:,3],p[:,:,3])
  if ver==1 and v['group_id']=='FM0029':assert np.array_equal(o[:,:,3][mask],np.repeat(np.repeat(s[:,:,3],8,0),8,1)[mask])
  if ver==2 and v['group_id']=='FM0113':
   frozen=np.load(v['base_planes']);assert np.array_equal(frozen['rgb'],o[:,:,:3]);assert np.array_equal(frozen['alpha'],o[:,:,3])
  if ver==3 and v['group_id']=='FM0113':assert np.array_equal(o[256:],p[256:])
  decision='static_candidate' if v['id']=='FM0113-authored-v3' else 'partial_glass_preview_whole_held' if v['id']=='FM0029-authored-v3' else 'superseded_not_selected'
  checked.append({'id':v['id'],'path':v['output'],'sha256':v['output_sha256'],'decision':decision,'source_and_lineage_hashes_verified':True,'8x_dimensions_verified':True,'protected_region_checks_verified':True,'runtime_verified':False,'release_eligible':False});allrows[v['id']]=v
for v in two['files']:
 g=arr(v['gpt_raw']);assert [g.shape[1],g.shape[0]]==v['gpt_actual_size'];checked.append({'id':v['group_id']+'-GPT-raw','path':v['gpt_raw'],'sha256':v['gpt_raw_sha256'],'decision':'not_selected_whole_generated_layout','reason':'Generated atlas shifts source positions. FM0029 additionally contains an unrelated miniature inset at top left, entirely outside adopted glass masks. Only constrained derivatives are considered.','prompt':v['gpt_prompt'],'prompt_sha256':v['gpt_prompt_sha256'],'actual_size':v['gpt_actual_size']})
assert len(checked)==8
# Output properties independent of the declared polygon metadata.
v113=allrows['FM0113-authored-v3'];support=allrows['FM0113-authored-v2'];o=arr(v113['output']);s=arr(v113['source']);a=o[:,:,3];assert np.all(a[:256]==255);assert np.all(a[272:288,80:176]==0);assert np.all(a[264:272,80:176]==255)
def holes(binary):
 _,hier=cv2.findContours(np.pad(binary.astype('uint8'),1),cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE);return int(sum(z[3]>=0 for z in hier[0]))
assert holes(a[256:]>=128)==holes(s[32:,:,3]>=128)==4
sample=a[260::8,4::8]>=128;src=s[32:,:,3]>=128;diff=int(np.count_nonzero(sample!=src));iou=np.count_nonzero(sample&src)/np.count_nonzero(sample|src);assert diff==22 and abs(iou-support['lower_source_alpha_center_IoU'])<1e-12
svg=ET.parse(support['geometry_vector']).getroot();paths=list(svg.iter('{http://www.w3.org/2000/svg}path'));assert len(paths)==1 and not any(c in paths[0].attrib['d'] for c in 'CQAScqast')
profile=np.rint(np.array(v113['fixed_seam_profile_RGB'])).astype('uint8');hrows=np.ones(240,bool)
for z in v113['seams']:
 if z['axis']=='horizontal':hrows[z['output_span'][0]:z['output_span'][1]]=False
for z in v113['seams']:
 l,r=z['output_span']
 if z['axis']=='vertical':assert np.all(o[:240,l:r,:3][hrows]==profile[None,:,:])
 else:assert np.all(o[l:r,:128,:3]==profile[:,None,:])
diagnostics={'rectangular_top_slot_alpha_zero_source_box':[10,34,22,36],'upper_slot_edge_horizontal_and_solid':True,'lower_enclosed_holes_source':4,'lower_enclosed_holes_output':4,'source_alpha_center_mismatches':diff,'source_alpha_center_IoU':float(iou),'alpha_mass_ratio':support['lower_alpha_mass_ratio'],'contour_uses_straight_segments_only':True,'grid_uninterrupted_seam_profiles_invariant':True,'correction':'The authored-v2 raw report field lower_holes_count_at_threshold128=6 incorrectly counted disconnected background regions minus one. Padded contour hierarchy establishes FOUR enclosed holes in source and output. Raw report retained for hash lineage.','scope_limit':'These tests verify declared image geometry and topology, not native mesh/UV, game material identity, alpha-test behavior or runtime appearance.'}
pages=[]
for ri,report in enumerate(reports):
 for v in report['pages']:
  assert sha(v['path'])==v['sha256'];name=Path(v['path']).name
  seen=(ri==0 and '-whole-' in name) or ri==1 or (ri==2 and name not in ['FM0113-detail-authored-v3.png','FM0029-upper-authored-v3.png'])
  pages.append({**v,'review_status':'directly_inspected_by_Codex_internal' if seen else 'redundant_after_whole_rejection_or_unchanged_region','report':names[ri]})
reason='Original top slot is rectangular and horizontal; support silhouette uses straight legs and X-braces with four enclosed voids, source dark-to-worn illumination and new directional wood grain. Grid fixed at source texel centers and wall repainted as concrete/plaster. Geometry v1 rejected for skewed slot/incorrect contour; v2 upper material was flat; v3 improves material. Material attribution is an explicit artistic interpretation.'
for v in cat['groups']:
 if v['group_id']=='FM0113':
  assert v['status']=='held' and v['candidate'] is None;v.update(status='static_candidate',hold_reason=None,candidate={'id':v113['id'],'path':v113['output'],'sha256':v113['output_sha256'],'review':'qa/field_geometry005_review.json','method':v113['method'],'geometry_review':reason,'runtime_verified':False,'release_eligible':False})
 elif v['group_id']=='FM0029':
  assert v['status']=='held' and v['candidate'] is None;v['hold_reason']='Source grille phase and three rectilinear regions reconstructed; broken glass redrawn by built-in GPT and source-masked/tone-matched. Whole atlas remains held: frames, lower panels and other unreviewed local geometry need direct construction; exact fracture correspondence is not established.'
for a,b in zip(before['groups'],cat['groups']):
 if a['group_id'] not in ['FM0113','FM0029']:assert a==b
stats=cat['processing_summary'];stats.update(field_static_candidates=90,field_holds=35,latest_review='qa/field_geometry005_review.json');assert sum(bool(v['candidate']) for v in cat['groups'])==90;assert sum(v['status']=='held' for v in cat['groups'])==35
contract['geometry_review005']={'review':'qa/field_geometry005_review.json','resolved_holds':{'FM0113':v113['id']},'partial_glass_preview':{'FM0029':allrows['FM0029-authored-v3']['output']},'runtime_verified':False,'release_eligible':False}
contract['user_direct_repaint_and_material_policy']={'instructions':['깨진 창문은 직접 그릴 것; 로컬 자동복원 반복을 중단.','도구 애셋의 원래 직선 구조와 콘셉트에 맞춰 재작화.','목재·돌·콘크리트 등 재질이 드러나게 표현.'],'rules':['Record immutable source anchors before redrawing frames, tools and structural props. Generated material may not alter straight construction edges or rectangular openings.','Broken glass retains dark voids and original damage regions with sharp fracture facets. Preserve intentional chamfers/curves; do not force broken edges into right angles.','Wood grain follows member direction; stone uses faceted planes/broken corners; concrete uses restrained mineral grain. Keep source color family and aging, without invented deep cracks or noise on straight silhouettes.','When the source cannot establish material identity, record the chosen material as artistic interpretation, not recovered metadata.'],'known_broken_window_direct_authoring_queue':['FM0029','FM0358','FM0359','FM0364'],'other_structured_holds_require_source_anchored_review':True,'source_report':'qa/field_sr004_review.json'}
contract['current_batch_geometry_holds'].pop('FM0113',None);contract['current_batch_geometry_holds']['FM0029']=next(v['hold_reason'] for v in cat['groups'] if v['group_id']=='FM0029')
backup=R/'qa/backups/before-field-geometry005-review';backup.mkdir(exist_ok=False)
for p in [cp,gp]:shutil.copy2(p,backup/p.name)
write(cp,cat);write(gp,contract)
previews=[]
for source,name in [('FM0113-whole-authored-v3.png','받침대_직선과_재질_수정_비교.png'),('FM0029-detail-authored-v3.png','깨진_유리_재작화_부분_비교.png')]:
 pp=R/'outputs/field-geometry005'/source;dst=C/'outputs'/name;shutil.copy2(pp,dst);previews.append({'path':str(dst),'project_path':str(pp),'sha256':sha(pp)})
review={'schema':'brs-field-geometry-material-final-review/v1','batch':'FIELD-GEOMETRY-005','this_goal_turn_classification':'progress: tool-frame geometry corrected; one held whole asset becomes static candidate; broken-glass region redraw remains part of held atlas. User material-specific art direction recorded.','selected':{'FM0113':'FM0113-authored-v3'},'selection_reason':reason,'partial_region_only':{'FM0029':'FM0029-authored-v3; glass-only preview, whole atlas held'},'checked_outputs':checked,'new_neural_unique_originals':0,'new_local_inference_passes':0,'external_generative_calls':2,'gpt_tool':'built-in image_gen; model identifier not exposed','geometry_diagnostics':diagnostics,'pages':pages,'pages_directly_inspected_count':sum(p['review_status']=='directly_inspected_by_Codex_internal' for p in pages),'gpt_raws_directly_inspected':2,'source_reports_sha256':{str((R/'qa'/n).relative_to(R)):sha(R/'qa'/n) for n in names},'catalog_before_sha256':one['catalog_before_sha256'],'catalog_after_sha256':sha(cp),'geometry_contract_before_sha256':one['geometry_contract_before_sha256'],'geometry_contract_after_sha256':sha(gp),'other574_field_groups_unchanged':True,'previous89_field_candidates_unchanged':True,'field_processing_summary':stats,'unique_neural_originals_title_battle_novel_field':382,'protected_file_hashes':prev['protected_file_hashes'],'pack_hashes':packhash,'previews':previews,'runtime_verified':False,'release_eligible':False,'all_game_complete':False,'limits':['FM0113 material identity is interpreted. Its22 source alpha-center differences and+0.6073% alpha mass are reported, not called pixel-exact.','Source-position grid supports and four enclosed support holes are checked; actual game UV/consumer and alpha testing remain unverified.','FM0029 glass redrawing changes microfracture shapes and still needs source/concept/runtime review together with unrepaired frames and panels.','Whole GPT outputs not adopted: layout differences; FM0029 accidental inset excluded by source glass masks.','Historical57 field and241 battle material candidates still await geometry-applicability review.','No new observed key, game installation, emulator launch or final release ZIP.'],'next_action':'Finish FM0029 straight frame/panel construction around redrawn glass, then direct-author known broken-window358/359/364. Continue structured holds37/38 etc and remainingfield226/battle43/other game populations.','scripts':{n:sha(R/'tools'/n) for n in ['rebuild_field_grids005.py','author_field005.py','refine_material_field005.py','finalize_field005.py']}}
for rel,h in prev['protected_file_hashes'].items():assert sha(R/rel)==h
assert {str(p.relative_to(pack)):sha(p) for p in pack.rglob('*') if p.is_file()}==packhash
write(Q,review)
with (R/'PROGRESS.md').open('a',encoding='utf8') as f:f.write('''

## 2026-09-23 — FIELD-GEOMETRY-005 / 받침대·깨진 유리·재질별 재작화
- 사용자 지시 추가: 깨진 창문은 직접 재작화, 도구/구조물의 직선 유지, 목재·돌·콘크리트 재질 구분. qa/architectural_geometry_contract.json에 기록. 358/359/364는 직접 재작화 대기이며 작업완료 아님.
- FM0029 v1 격자/캐비닛/노란판3영역 source palette rectangles +기존WDN잔질감. 격자alpha위상 sourceNN정확. 나머지frame미수정이라 wholeheld. FM0113 v1 RDP외곽은 slot기울어짐/두께왜곡으로 불채택.
- built-in image_gen 2회 실제수행: FM0113 raw887x1774,FM0029 raw1774x887. 각 workspace/gpt-trials/<ID>-v1/prompt.txt와raw보존. 전체생성안은위치변화로불채택; FM0029왼위미니그림도불채택영역. 새local추론/새고유원본0.
- FM0113 직접source좌표직선polygon과직사각slot,4닫힌구멍. 새목재grain은면안에투영하고원본상단어두움/하단마모색조유지. 목재·콘크리트해석은설계방향이지native재질확정아님. v2상단재질너무평평하여v3고정seam/bevel+재투영pane/concrete로변경. v3정적후보채택.
- FM0113 sourcealpha center22불일치,IoU.9538784,mass+0.60728%, source/output모두닫힌구멍4. raw v2 lower_holes_count=6은외부배경분리영역을포함한잘못된수치이며finalreview에서hierarchy4로정정. source픽셀동일주장안함. 직선path/slot직사각alpha/수직수평seam불변검사.
- FM0029 GPT유리6영역만sourceglassmask내재투영,frame/나머지palette영역/alpha보호. v2너무밝은유리는v3sourcegray평균에맞춰낮춤. 유리부분미리보기이며frame/하단판넬/파손세부대응미완으로wholeheld유지.
- 파생6+GPTraw2=8출력 lineage/크기/보호영역검사. 전체19비교페이지중12직접검수+raw2직접검수;미사용7은실패whole후중복또는변경없는영역. 원본/PTM·catalog/contract·보호팩해시검증. 최종 qa/field_geometry005_review.json. 원본/기존89후보/다른574fieldgroup/20key팩바이트보존.
- 현재field125neural/90정적후보/35보류/novel미처리226. 고유neural382유지,전투241후보17보류26미처리. 전체목표active,설치/실게임/최종ZIP미완료.
- 다음29창틀·하단판넬과358/359/364깨진창직접재작화,37/38원근구조등structured보류,남은field226/전투43/기타캐릭터적효과컷신진행. GUI복구증거없어컴퓨터유즈실행/검은캡처반복없음.
''')
with (C/'outputs/로컬_업스케일_진행.md').open('a',encoding='utf8') as f:f.write('''

## 받침대와 깨진 유리 재작화 — FIELD-GEOMETRY-005
- 받침대의 수평 구멍과 곧은 다리/X지지대를 다시 그리고 목재 결을 적용했습니다. 벽은 콘크리트 입자감으로 수정했습니다. 파일 검수 후보이며 실게임 적용은 아직입니다.
- 깨진 유리는 날카로운 조각으로 재작화하고 밝기를 원본에 맞췄습니다. 주변 창틀/하단판넬은 추가 수정이 남아 전체 이미지는 보류입니다.
- 내장 GPT 이미지 편집2회와직접원본좌표구조수정을사용했습니다. 새로컬추론0회,필드후보90/보류35/미처리226입니다.
''')
print(json.dumps({'checked_outputs':len(checked),'viewed_pages':review['pages_directly_inspected_count'],'pages_total':len(pages),'selected':review['selected'],'field_summary':stats,'runtime_verified':False}))
