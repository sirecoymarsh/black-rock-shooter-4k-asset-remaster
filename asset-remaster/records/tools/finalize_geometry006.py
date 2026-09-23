"""Verify source geometry/topology, record material-only external use and update
the catalog without miscounting direct GPT-only originals as local inference."""
from pathlib import Path
import json,hashlib,copy,shutil,xml.etree.ElementTree as ET
import numpy as np,cv2
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];C=Path(r'C:\Users\CadriacLord\Documents\Codex\2026-09-22\brs-hd-ui-fonts');Q=R/'qa/field_geometry006_review.json';assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text('utf8'))
def arr(p):return np.asarray(Image.open(p).convert('RGBA'))
def write(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2),'utf8')
prev=read(R/'qa/field_geometry005_review.json');names=['field_geometry006_source_audit.json','field_geometry006_facades_v1.json','field_geometry006_facades_v2.json','field_geometry006_atlas29_v1.json','field_geometry006_atlas29_v2.json'];reports={n:read(R/'qa'/n) for n in names};audit,f1,f2,a1,a2=[reports[n] for n in names];cp=R/'qa/field_sr_catalog.json';gp=R/'qa/architectural_geometry_contract.json';cat=read(cp);before=copy.deepcopy(cat);contract=read(gp)
assert sha(cp)==prev['catalog_after_sha256']==audit['catalog_before_sha256'];assert sha(gp)==prev['geometry_contract_after_sha256']==audit['geometry_contract_before_sha256'];assert f1['source_audit_sha256']==sha(R/'qa'/names[0]);assert f2['parent_report_sha256']==sha(R/'qa'/names[1]);assert a2['parent_report_sha256']==sha(R/'qa'/names[3])
for rel,h in prev['protected_file_hashes'].items():assert sha(R/rel)==h
pack=R/'workspace/local-sr/observed-review-pack-v2/PSP/TEXTURES/NPUH10126';packhash={str(p.relative_to(pack)):sha(p) for p in pack.rglob('*') if p.is_file()};assert packhash==prev['pack_hashes']
for report in [f2,a2]:assert sha(report['reconstruction_program'])==report['reconstruction_program_sha256']
checked=[];diagnostics={};pick={};pages=[]
def topology(binary):
 _,hier=cv2.findContours(np.pad(binary.astype('uint8'),1),cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE);return int(sum(v[3]>=0 for v in hier[0]))
for ver,report in [(1,f1),(2,f2)]:
 for v in report['files']:
  gid=v['group_id'];s=arr(v['source']);o=arr(v['output']);assert o.shape==(512,1024,4);assert hashlib.sha256(s.tobytes()).hexdigest()==v['source_rgba_sha256']
  for key in ['source_ptm','output','gpt_raw','gpt_prompt','geometry_vector','alpha_render','base_planes','glass_donor']:assert sha(v[key])==v[key+'_sha256']
  original=s[:,:,3]>=128;alpha=o[:,:,3];assert np.array_equal(alpha,arr(v['alpha_render'])[:,:,3]);frozen=np.load(v['base_planes']);assert np.array_equal(o[:,:,:3],frozen['rgb']) and np.array_equal(alpha,frozen['alpha']);assert frozen['mapx'].shape==frozen['mapy'].shape==(512,1024);assert np.all(np.diff(frozen['mapx'],axis=1)>=0);assert np.all(np.diff(frozen['mapy'],axis=0)>=0)
  vector=ET.parse(v['geometry_vector']).getroot();paths=list(vector.iter('{http://www.w3.org/2000/svg}path'));assert len(paths)==1 and paths[0].attrib['fill-rule']=='evenodd';assert not any(c in paths[0].attrib['d'] for c in 'CQAScqast')
  sample=alpha[4::8,4::8]>=128;diff=int(np.count_nonzero(sample!=original));iou=np.count_nonzero(sample&original)/np.count_nonzero(sample|original);assert diff==v['source_alpha_center_mismatches'];assert topology(original)==topology(alpha>=128)==v['enclosed_holes_source']==v['enclosed_holes_output']
  # Pixel-center phase is explicitly recorded. Symmetric four-sample diagnostic
  # does not replace the prior point-sample result or claim game alpha behavior.
  centered=(alpha[3::8,3::8].astype(float)+alpha[3::8,4::8]+alpha[4::8,3::8]+alpha[4::8,4::8])/4;centereddiff=int(np.count_nonzero((centered>=128)!=original))
  # Frame writer replay with source-coordinate rectangles and constant
  # transverse bevels. Geometry edges are audited independently of pane RGB.
  region_class=np.zeros(alpha.shape,np.int32)
  for j,z in enumerate(v['frame_regions'],1):
   a,b,c,d=z['box_output'];assert 0<=a<c<=1024 and 0<=b<d<=512;region_class[b:d,a:c]=j
  for z in v['glass_regions']:
   a,b,c,d=[t*8 for t in z['source_box']];region_class[b:d,a:c]=0
  tested=0
  for j,z in enumerate(v['frame_regions'],1):
   a,b,c,d=z['box_output'];n=d-b if z['axis']=='horizontal' else c-a;profile=np.linspace(.42,1.3,n)[:,None]*np.array(z['base_RGB'])[None,:];expected=np.broadcast_to(profile[:,None,:],(d-b,c-a,3)) if z['axis']=='horizontal' else np.broadcast_to(profile[None,:,:],(d-b,c-a,3));m=(region_class[b:d,a:c]==j)&(alpha[b:d,a:c]>=128)
   # Fracture bevels can touch a source glass pixel at a frame boundary. Exclude
   # only the 2-output-pixel neighborhood where that last writer is declared.
   dist=cv2.distanceTransform((alpha>=128).astype('uint8'),cv2.DIST_L2,cv2.DIST_MASK_PRECISE);m&=dist[b:d,a:c]>2.01
   if m.any():assert np.array_equal(o[b:d,a:c,:3][m],np.rint(np.clip(expected,0,255)).astype('uint8')[m]),(gid,j);tested+=int(m.sum())
  checked.append({'id':v['id'],'path':v['output'],'sha256':v['output_sha256'],'decision':'static_candidate' if ver==2 else 'superseded_not_selected','source_and_lineage_hashes_verified':True,'alpha_matches_saved_vector_render':True,'RGB_matches_frozen_material_planes':True,'frame_bevel_recipe_pixels_verified':tested,'runtime_verified':False,'release_eligible':False})
  if ver==2:
   pick[gid]=v;diagnostics[gid]={'source_holes':topology(original),'output_holes':topology(alpha>=128),'point_sample_source_center_mismatches':diff,'point_sample_IoU':float(iou),'symmetric_four_sample_center_mismatches':centereddiff,'point_sample_definition':'Output pixel at(8*x+4,8*y+4), whose pixel center is +.0625 source pixels beyond the ideal source texel center; retained for comparability.','alpha_mass_ratio':v['alpha_mass_ratio'],'straight_segment_contours':True,'source_pane_rectangles':v['source_mapping']['panes'],'frame_recipe_pixels_verified':tested,'limit':'Source topology/anchors and decoded image geometry, not complete game alpha-test, UV or consumer proof.'}
for report in [a1,a2]:
 v=report['file'];s=arr(v['source']);p=arr(v['parent']);o=arr(v['output']);assert hashlib.sha256(s.tobytes()).hexdigest()==v['source_rgba_sha256'];assert o.shape==(512,1024,4)
 for key in ['source_ptm','parent','output','mask','vector','render','generated_material']:assert sha(v[key])==v[key+'_sha256']
 mask=np.asarray(Image.open(v['mask']))>0;assert np.array_equal(o[~mask],p[~mask]);assert np.array_equal(o[:,:,3],p[:,:,3]);root=ET.parse(v['vector']).getroot();polys=list(root.iter('{http://www.w3.org/2000/svg}polygon'));assert len(polys)==len(v['shapes'])==86
 for z,pv in zip(v['shapes'],polys):assert np.array_equal(np.array([[float(t) for t in q.split(',')] for q in pv.attrib['points'].split()]),np.array(z['points']))
 checked.append({'id':v['id'],'path':v['output'],'sha256':v['output_sha256'],'decision':'partial_frame_panel_preview_whole_held' if report is a2 else 'superseded_not_selected','source_and_lineage_hashes_verified':True,'outside_mask_parent_RGBA_exact':True,'alpha_parent_exact':True,'polygon_manifest_matches_SVG':True,'runtime_verified':False,'release_eligible':False})
for v in f2['files']:
 raw=arr(v['gpt_raw']);assert [raw.shape[1],raw.shape[0]]==v['gpt_raw_size'];checked.append({'id':v['group_id']+'-GPT-raw','path':v['gpt_raw'],'sha256':v['gpt_raw_sha256'],'decision':'not_selected_whole','prompt':v['gpt_prompt'],'prompt_sha256':v['gpt_prompt_sha256'],'reason':'Generated positions/holes differ; FM0359 painted checker in openings, FM0364 colored edge fringe,358/364 invented handles. These are excluded by source alpha/glass planes and authored frame supports. Material donors are separate.'})
assert len(checked)==11
for n,report in reports.items():
 for p in report.get('pages',[]):
  assert sha(p['path'])==p['sha256'];seen=not (n==names[0] and Path(p['path']).name=='FM0029-source-dual-matte.png');pages.append({**p,'review_status':'directly_inspected_by_Codex_internal' if seen else 'redundant_source_already_inspected_on_coordinate_plate','report':n})
assert len(pages)==34 and sum(p['review_status']=='directly_inspected_by_Codex_internal' for p in pages)==33
hold29='Lower window frames/panels source-reconstructed in geometry006 v2 with source dark rims, cream trim, gold chamfers and sloped panel. Repainted glass retained. Whole atlas still held: top-left mechanism/remaining upper fragments and cross-region material/corner-style consistency are not yet demonstrated under direct-authoring criteria.'
for v in cat['groups']:
 gid=v['group_id']
 if gid in pick:
  assert v['status']=='not_processed_in_field_context' and not v['local_sr_attempted'] and v['candidate'] is None;z=pick[gid];v.update(status='static_candidate',hold_reason=None,direct_gpt_attempted=True,processing_route='source_geometry_with_direct_GPT_material',candidate={'id':z['id'],'path':z['output'],'sha256':z['output_sha256'],'review':'qa/field_geometry006_review.json','method':z['method'],'geometry_review':'Source rectangular panes/metal supports and original transparent damage topology, source-colored glass with fine generated material, story-aligned concrete. Not the unconstrained whole GPT image.','runtime_verified':False,'release_eligible':False})
 elif gid=='FM0029':assert v['status']=='held';v['hold_reason']=hold29
for a,b in zip(before['groups'],cat['groups']):
 if a['group_id'] not in set(pick)|{'FM0029'}:assert a==b
stats=cat['processing_summary'];stats.update(field_static_candidates=93,field_holds=35,remaining_novel_unprocessed=223,field_groups_not_processed_in_field_context=448,field_direct_gpt_only_originals=3,field_processed_novel_originals_all_routes=128,latest_review='qa/field_geometry006_review.json',counting_note='Legacy field_neural_originals=125 counts originals that received local neural SR;3 new direct-GPT-only originals are separate. All processed novel originals=125+3=128. Do not count direct GPT as local inference.')
assert sum(bool(v['candidate']) for v in cat['groups'])==93;assert sum(v['status']=='held' for v in cat['groups'])==35;assert sum(v['local_sr_attempted'] for v in cat['groups'])==125;assert sum(v['status']=='not_processed_in_field_context' for v in cat['groups'])==448
contract['geometry_review006']={'review':'qa/field_geometry006_review.json','direct_broken_window_static_candidates':{k:v['id'] for k,v in pick.items()},'partial_atlas29':a2['file']['id'],'source_alpha_hole_counts':{k:v['source_holes'] for k,v in diagnostics.items()},'raw_GPT_whole_images_not_selected':True,'new_local_passes':0,'new_external_calls':3,'runtime_verified':False,'release_eligible':False};contract['current_batch_geometry_holds']['FM0029']=hold29;contract['user_direct_repaint_and_material_policy']['known_broken_window_direct_authoring_queue']=['FM0029'];contract['user_direct_repaint_and_material_policy']['known_broken_window_static_candidates_pending_runtime']=['FM0358','FM0359','FM0364']
backup=R/'qa/backups/before-field-geometry006-review';backup.mkdir(exist_ok=False)
for p in [cp,gp]:shutil.copy2(p,backup/p.name)
write(cp,cat);write(gp,contract)
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18);can=Image.new('RGB',(1080,900),'#26333f');draw=ImageDraw.Draw(can)
for row,gid in enumerate(['FM0358','FM0359','FM0364']):
 v=pick[gid]
 for col,(p,title) in enumerate([(v['source'],'원본 · 단순 확대'),(v['output'],'직선 창틀 · 유리 파손 · 재질 수정')]):
  im=Image.open(p).convert('RGBA').resize((512,256),Image.Resampling.NEAREST if col==0 else Image.Resampling.LANCZOS);mat=Image.new('RGB',(512,256),'#39424b');mat.paste(im,(0,0),im);draw.text((col*540+8,row*300+5),gid+' '+title,font=font,fill='white');can.paste(mat,(col*540+8,row*300+36))
preview=R/'outputs/field-geometry006/깨진_창문_3종_수정_비교.png';can.save(preview);previews=[]
for pp,name in [(preview,preview.name),(R/'outputs/field-geometry006/FM0029-whole-v2.png','갈색_창틀과_패널_수정_비교.png')]:
 dst=C/'outputs'/name;shutil.copy2(pp,dst);previews.append({'path':str(dst),'project_path':str(pp),'sha256':sha(pp)})
review={'schema':'brs-field-direct-glass-final-review/v1','batch':'FIELD-GEOMETRY-006','previous_goal_turn_classification':audit['previous_goal_turn_classification'],'this_goal_turn_classification':'progress:3 previously unprocessed damaged facades reconstructed using direct GPT material and source geometry; FM0029 frame/panel geometry advanced, whole atlas still held.','selected':{k:v['id'] for k,v in pick.items()},'partial_only':{'FM0029':a2['file']['id']},'checked_outputs':checked,'new_local_neural_unique_originals':0,'new_direct_GPT_only_unique_originals':3,'new_local_inference_passes':0,'external_generative_calls':3,'external_mode':'built-in image_gen; model identifier not exposed','geometry_diagnostics':diagnostics,'pages':pages,'pages_directly_inspected_count':33,'gpt_raws_directly_inspected':3,'glass_donor_directly_inspected':True,'source_reports_sha256':{str((R/'qa'/n).relative_to(R)):sha(R/'qa'/n) for n in names},'catalog_before_sha256':audit['catalog_before_sha256'],'catalog_after_sha256':sha(cp),'geometry_contract_before_sha256':audit['geometry_contract_before_sha256'],'geometry_contract_after_sha256':sha(gp),'other572_field_groups_unchanged':True,'previous90_field_candidates_unchanged':True,'field_processing_summary':stats,'unique_local_neural_originals_title_battle_novel_field':382,'unique_processed_originals_including_direct_GPT_only_title_battle_novel_field':385,'protected_file_hashes':prev['protected_file_hashes'],'pack_hashes':packhash,'previews':previews,'runtime_verified':False,'release_eligible':False,'all_game_complete':False,'limits':['The3 facades are static candidates; game alpha-test/UV/render behavior is unverified.','Source-alpha point samples differ at4/2/2 pixels; mass grows~.136%-.215% with contour antialiasing. No byte-exact alpha claim. Both point/symmetric center diagnostics are recorded.','Clean donor glass is shared from FM0359; own generated facade concrete is story-reprojected. Source damage geometry is authored, not inferred from generated holes.','FM0029 corrected frame coordinates do not prove full mechanical fragment identity or consistent material/corner style; whole atlas held.','No new local model passes, observed keys, emulator launch, installed assets or final release ZIP.','Historical57 field/241 battle geometry-applicability review and other whole-game populations remain unfinished.'],'next_action':'Review source-fixed improvements against overall concept and original material cues; finish FM0029 remaining mechanical/upper regions and consistent frame material/corners. Continue perspective facades37/38 and remainingfield223/battle43, other game-source populations. Runtime work only on evidence of GUI recovery; never Computer Use emulator launch.','scripts':{n:sha(R/'tools'/n) for n in ['audit_field_glass006.py','rebuild_facades006.py','refine_facades006.py','rebuild_atlas29_006.py','refine_atlas29_006.py','finalize_geometry006.py']}}
for rel,h in prev['protected_file_hashes'].items():assert sha(R/rel)==h
assert {str(p.relative_to(pack)):sha(p) for p in pack.rglob('*') if p.is_file()}==packhash
write(Q,review)
with (R/'PROGRESS.md').open('a',encoding='utf8') as f:f.write('''

## 2026-09-23 — FIELD-GEOMETRY-006 / 깨진 창문3종·갈색 틀/패널
- 이전005는progress. 이번은신규직접GPT전용원본3종과FM0029틀·판넬2안으로progress. 전체목표active. 사용자직접깨진유리/직선/재질기준유지,로컬추론0/GPT외부생성3회.
- 358/359/364 각각built-in image_gen 1774x887. 지시문/원본 workspace/gpt-trials/FM0358-v1,FM0359-v1,FM0364-v1. 생성전체는변경된창문/구멍위치,359체크무늬,364색프린지,358/364신규손잡이로불채택. source좌표창틀/직선polygon파손alpha로다시구성하여해당부분제외. 깨끗한359유리재질donor공유,각건물본인GPT콘크리트재질story별재투영.
- source128x64→1024x512,창12/12/10개직사각영역. 원본alpha닫힌구멍13/15/20개모두보존. singlepointcenter4/2/2픽셀불일치,IoU.9992846/.9996932/.9996785,alpha총량+0.1696/+0.1353/+0.2152%. sourcecenter샘플위상(+.0625)와4점대칭샘플도기록;실게임alpha-test보증아님.
- facadesv1 유리에큰donor균열/잔무늬와364상단fragment범위문제. v2는고주파잔질감+작은평면반사·절단면강조,364원본palettecomponent범위포함. 세v2정적후보. source파손을새일반구멍으로대체하지않음. 원본창틀직각/불변bevelRGB·alpha/render/base·mapping단조성검증.
- FM0029 lower창틀/패널86sourcepolygon직접작성. 원래금색chamfer와우하단기울기유지,생성볼트제거. v1색테두리두꺼워v2원본darkrim/얇은coloredbevel분리,작은원본plate고정부팔레트복원. 기존tone유리를innerpolygon안에유지,외부mask/alpha불변. 상단기계/잔여영역과재질·cornerstyle통일검토미완으로wholeheld유지.
- 총11검사출력=facade6+atlas2+GPTraw3. 원본PTM/RGBA·부모/GPTprompt/raw/donor/vector/render/base/output SHA검사. source/비교34페이지중33직접검수,raw3+donor1직접검수. 최종 qa/field_geometry006_review.json. 원본/기존90후보/다른572fieldgroup/20key팩보존.
- 현재field93정적후보/35보류/미처리223. 로컬neural125 +신규directGPT-only3 =전체처리128;catalog기존field_neural_originals는로컬추론125로유지하고별도필드로구분. source분류216유지. title+battle+field로컬고유382,외부전용포함전체처리385. 전투241후보17보류26미처리. 전체게임완료율아님.
- 다음29상단기계/일관된프레임재질·corner검토,37/38원근구조와field223/전투43/다른게임원본범위. 설치/실게임/최종ZIP미완료,새키/에뮬실행없음. GUI복구증거없어검은캡처반복안함. outputs/깨진_창문_3종_수정_비교.png 및갈색틀비교보관.
''')
with (C/'outputs/로컬_업스케일_진행.md').open('a',encoding='utf8') as f:f.write('''

## 깨진 창문3종·갈색 창틀 수정 — FIELD-GEOMETRY-006
- 깨진 창문3종을 새로 재작화하고 원본 창틀/투명구멍에맞췄습니다. 내장GPT이미지편집3회,새로컬추론0회입니다. 파일검수후보이며게임적용은아직입니다.
- 갈색창문이미지도창틀·하단패널을직접수정했습니다. 상단기계부품과전체재질/모서리통일검토가남아전체이미지는계속보류합니다.
- 필드후보93/보류35/미처리223. 처리128종중로컬추론125종과직접GPT전용3종을구분합니다. 실게임검수/최종배포는미완료입니다.
''')
print(json.dumps({'checked_outputs':len(checked),'selected':review['selected'],'pages_viewed':33,'field_summary':stats,'alpha_diagnostics':diagnostics}))
