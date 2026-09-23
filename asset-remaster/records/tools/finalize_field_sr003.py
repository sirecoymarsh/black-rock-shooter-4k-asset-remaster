"""Finalize inspected field-alpha results under the new straight-line geometry gate."""
import json,hashlib,shutil,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter,distance_transform_edt
from PIL import Image
R=Path(__file__).resolve().parents[1];C=Path('C:/Users/CadriacLord/Documents/Codex/2026-09-22/brs-hd-ui-fonts');Q=R/'qa/field_sr003_review.json';assert not Q.exists()
def read(p):return json.loads((R/p).read_text('utf8'))
def save(p,v):(R/p).write_text(json.dumps(v,ensure_ascii=False,indent=2),'utf8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check(p,h):assert sha(p)==h,str(p)
def img(p):return Image.open(p).convert('RGBA')
base=read('qa/field_sr003_inference.json');audit=read('qa/field_sr003_audit.json');rew=read('qa/field_sr003_rework.json');ar=read('qa/field_sr003_alpha_rework.json');v1=read('qa/field_sr003_rectilinear.json');v2=read('qa/field_sr003_rectilinear_v2.json');cat=read('qa/field_sr_catalog.json');battle=read('qa/battle_sr_catalog.json')
check(R/'qa/field_sr_catalog.json',base['source_catalog_sha256_before'])
for p,h in audit['protected_file_hashes'].items():check(R/p,h)
pack=Path(read('qa/local_sr_observed_review_pack_v2.json')['path']);assert audit['pack_hashes']=={str(p.relative_to(pack)):sha(p) for p in pack.rglob('*') if p.is_file()}
old_candidates={g['group_id']:g['candidate'] for g in cat['groups'] if g['candidate']};assert len(old_candidates)==61
backup=R/'qa/backups/before-field-sr003-review';backup.mkdir(parents=True,exist_ok=False)
names=['field_sr_catalog.json','field_sr003_inference.json','field_sr003_audit.json','field_sr003_rework.json','field_sr003_alpha_rework.json','field_sr003_rectilinear.json','field_sr003_rectilinear_v2.json']
for name in names:shutil.copyfile(R/'qa'/name,backup/name)
pick={60:'wdn',123:'wdn',124:'wdn',157:'photo',254:'photo',255:'photo',256:'photo',260:'wdn',263:'wdn',264:'photo'}
accepted={f'FM{n:04d}':f'FM{n:04d}-{mid}' for n,mid in pick.items()}
accepted.update({f['group_id']:f['id'] for f in v2['files']});assert len(accepted)==12
holds={
'FM0029':'Thin grille crossing rows become beaded/rounded in both models. Source alternating gap phase needs direct rectilinear reconstruction.',
'FM0037':'Window-frame and roof line/corner geometry needs source-anchored straightening before acceptance under the new user gate.',
'FM0038':'Window and cornice edges have local warping; source perspective must be retained while straight architectural segments are reconstructed.',
'FM0047':'Upper rectangular fixture and straight post are not yet demonstrated to retain their corner and line geometry; curved arm itself is intentional.',
'FM0059':'Distant street/building geometry remains a material trial; required straight structural segments have not been anchored/checked.',
'FM0087':'Initial bilinear alpha loses peak strength; cubic/Lanczos alternatives add alpha mass and reduce1/4 weak samples below8. No accepted alpha replacement. Reduction IoU is not direct runtime alpha-test evidence; point and nearest-control diagnostics are retained.',
'FM0113':'Fine window-grid line spacing and corner geometry are not preserved with sufficient confidence; source-based reconstruction required. No physical bar count asserted.',
'FM0115':'Four local conditions convert flat/faded source regions into peeled/deep/outlined planes, or blur them. Requires source geometry and restrained material reconstruction.',
'FM0116':'Windows and horizontal facade boundaries require anchored straightening under the new architectural gate.',
'FM0121':'Four local conditions exaggerate small facade color transitions into cracks or ink contours; strong filtering merely blurs. Held for authored geometry.',
'FM0122':'Repeated window grid and small right-side graphic remain altered/ambiguous under all four local conditions; preserve geometry and graphic identity.',
'FM0145':'Triangular handle legs/base and panel seam geometry need direct straight-line reconstruction; generated edge wobble cannot be accepted as material detail.',
'FM0164':'Four plate strips need source-fixed horizontal/vertical edges before architectural acceptance; material quality alone is insufficient.',
'FM0268':'Door/frame and rectilinear panel seams need source-defined geometry; nearopaque alpha is preserved but does not prove RGB edge fidelity.',
'FM0272':'Facade seams and a small yellow graphic need protected geometry/artwork handling. Generated surface changes its relief; original graphic identity is unresolved.'}
assert len(holds)==15 and set(accepted)|set(holds)==set(base['group_ids']) and not set(accepted)&set(holds)
reasons={
'FM0060':'Organic foliage; WDN avoids stronger Photo highlights. Source-bilinear alpha remains exact; no architectural right-angle requirement identified.',
'FM0123':'Ornate lamp curves are intentional; straight stems remain in the source-derived alpha positions. WDN avoids extra Photo ink-like edges. Whole/two-matte and native top crop inspected.',
'FM0124':'Cloth pennant, horizontal seam and two pointed ends remain visually coherent; no new architectural corners introduced. Static visual candidate only.',
'FM0157':'Photo avoids WDN crack texture. Repeated ladder/plate positions and original chipped alpha are source-fixed; straight segments were compared on both mattes and native crop.',
'FM0254':'Source two-row partition and broken/faceted spire contours retained; Photo suppresses WDN crack exaggeration. Intentional broken slopes are not forced to90 degrees.',
'FM0255':'Source two-row partition, broken arch and visible support beam slope retained in inspected whole/native views; source damage is not treated as accidental generated curvature.',
'FM0256':'Snow/rock forms and existing thin broken pillars retained; Photo is less dither-like than WDN. This is not a claim of recovered unseen architectural detail.',
'FM0260':'Soft organic cloud/snow-bank silhouette; WDN keeps subdued source contrast and no artificial sharp architecture.',
'FM0263':'Thin broken structural outline uses exact source-bilinear alpha; intentional arcs and fractures remain. WDN material selected after source and native thin-line review.',
'FM0264':'Broken arch/beam outline uses exact source-bilinear alpha; Photo avoids WDN oversized flat facets. Source damage/perspective are retained, not forcibly squared.',
'FM0045':'Authored planar v2 fixes structural rectangles, four square black-rail corners and exact source alpha; v1 pixel-color mosaic rejected as too blocky.',
'FM0120':'Authored planar v2 fixes left panel frames and lower horizontal bands; upper-right organic plaster retains local Photo. v1 pixel-color mosaic rejected as too blocky.'}
checked=list(audit['checked_outputs']);allrows={v['id']:v for v in base['files']}
assert len(checked)==54
for v in base['files']:
 check(v['output'],v['output_sha256']);assert v['actual_local_inference_passes']==v['actual_rgb_passes']+v['actual_alpha_passes']
for v in rew['files']:
 src=img(v['source']);parent=img(v['alpha_parent']);out=img(v['output']);assert hashlib.sha256(src.tobytes()).hexdigest()==v['source_rgba_sha256'];check(v['source_ptm'],v['source_ptm_sha256']);check(v['model']['path'],v['model']['sha256'])
 for k in ['input','native','alpha_parent','output']:check(v[k],v[k+'_sha256'])
 a=np.asarray(src,dtype=np.float32)/255.;alpha=a[:,:,3];sig=v['input_gaussian_sigma_source_px'];cov=gaussian_filter(alpha,sig,mode='nearest');rgb=gaussian_filter(a[:,:,:3]*alpha[:,:,None],(sig,sig,0),mode='nearest')/np.maximum(cov[:,:,None],1e-6);vis=cov>1e-6
 if not vis.all():
  near=distance_transform_edt(~vis,return_distances=False,return_indices=True);rgb[~vis]=rgb[near[0][~vis],near[1][~vis]]
 assert np.array_equal(np.rint(np.clip(rgb,0,1)*255).astype('uint8'),np.asarray(Image.open(v['input'])))
 native=Image.open(v['native']).convert('RGB');assert native.size==(src.width*4,src.height*4) and out.size==(src.width*8,src.height*8);rgb=np.asarray(native.resize(out.size,Image.Resampling.LANCZOS),dtype=np.float32);rebuild=np.rint(np.clip(rgb+np.array(v['weighted_mean_rgb_offset'],dtype=np.float32),0,255)).astype('uint8');assert np.array_equal(rebuild,np.asarray(out)[:,:,:3]);assert np.array_equal(np.asarray(out)[:,:,3],np.asarray(parent)[:,:,3]);checked.append({'id':v['id'],'source_model_input_native_parent_output_hashes_verified':True,'input_and_rgb_postprocessing_reproduced_exact':True,'parent_alpha_byte_exact':True,'decision':'held'});allrows[v['id']]=v
for v in ar['files']:
 s=img(v['source']);parent=img(v['parent']);o=img(v['output']);ref=np.asarray(Image.open(v['reference_alpha']));assert hashlib.sha256(s.tobytes()).hexdigest()==v['source_rgba_sha256']
 for k in ['source_ptm','parent','reference_alpha','output']:check(v[k],v[k+'_sha256'])
 method=Image.Resampling.BICUBIC if v['method']=='bicubic' else Image.Resampling.LANCZOS;a=np.clip(np.asarray(s.getchannel('A').resize(o.size,method)),0,254).copy();a[ref==0]=0;a[ref==255]=255;assert np.array_equal(a,np.asarray(o)[:,:,3]) and np.array_equal(np.asarray(o)[:,:,:3],np.asarray(parent)[:,:,:3]);assert o.size==(s.width*8,s.height*8);checked.append({'id':v['id'],'hashes_size_rgb_parent_exact_verified':True,'alpha_reproduced_exact':True,'decision':'held'});allrows[v['id']]=v
for version,report in [(1,v1),(2,v2)]:
 for v in report['files']:
  s=img(v['source']);p=np.asarray(img(v['parent']));o=np.asarray(img(v['output']));g=np.asarray(img(v['render']));mask=np.asarray(Image.open(v['mask']))>0;nn=np.repeat(np.repeat(np.asarray(s),8,0),8,1);visible=mask&(nn[:,:,3]>0)
  for k in ['source_ptm','parent','vector','render','mask','output']:check(v[k],v[k+'_sha256'])
  assert hashlib.sha256(s.tobytes()).hexdigest()==v['source_rgba_sha256'];assert o.shape==(256,256,4) and np.array_equal(o[~mask],p[~mask]);assert np.array_equal(o[:,:,3][mask],nn[:,:,3][mask]) and np.array_equal(g[:,:,3][mask],nn[:,:,3][mask])
  tree=ET.parse(v['vector']);rectangles=tree.findall('.//{http://www.w3.org/2000/svg}rect');assert rectangles and all(not any(k in rect.attrib for k in ['rx','ry','transform']) for rect in rectangles)
  high=p[:,:,:3].astype(np.float32)-gaussian_filter(p[:,:,:3].astype(np.float32),(8,8,0),mode='nearest');tex=np.clip(high*.25,-4,4);basis=nn if version==1 else g;rebuilt=p.copy();rebuilt[:,:,:3][visible]=np.rint(np.clip(basis[:,:,:3].astype(np.float32)+tex,0,255)).astype('uint8')[visible];rebuilt[:,:,3][mask]=nn[:,:,3][mask];rebuilt[:,:,:3][mask&~visible]=nn[:,:,:3][mask&~visible]
  if version==2:
   x0,y0,x1,y1=v['black_rail_source_box'];rebuilt[y0*8:y1*8,x0*8:x1*8,:3]=0;assert np.all(o[y0*8:y1*8,x0*8:x1*8,:3]==0)
  assert np.array_equal(rebuilt,o);checked.append({'id':v['id'],'source_parent_vector_render_mask_output_hashes_verified':True,'output_reproduced_exact':True,'source_alpha_exact_in_declared_mask':True,'outside_mask_parent_exact':True,'svg_rectangles_axis_aligned_without_corner_radius':True,'decision':'selected_static_candidate' if version==2 else 'not_selected_blocky'});allrows[v['id']]=v
assert len(checked)==66
reports=[('qa/field_sr003_inference.json',base),('qa/field_sr003_rework.json',rew),('qa/field_sr003_alpha_rework.json',ar),('qa/field_sr003_rectilinear.json',v1),('qa/field_sr003_rectilinear_v2.json',v2)]
evidence=[]
for path,report in reports:
 for v in report['files']:
  gid=v['group_id'];status='selected_static_candidate' if accepted.get(gid)==v['id'] else 'held' if gid in holds else 'not_selected';reason=holds.get(gid,reasons[gid] if gid in reasons else 'Alternative not selected.')
  if path.endswith('rectilinear.json'):status='not_selected';reason='Source-color pixel mosaic remains blocky; superseded by authored planar v2.'
  v['visual_review']={'reviewer':'Codex internal','status':status,'reason':reason}
 for p in report['pages']:check(p['path'],p['sha256']);p['review_status']='directly_inspected_by_Codex_internal';evidence.append(p)
 save(path,report)
for p in audit['detail_pages']:check(p['path'],p['sha256']);p['review_status']='directly_inspected_by_Codex_internal';evidence.append(p)
save('qa/field_sr003_audit.json',audit);assert len(evidence)==30
sourcepages=[]
for i in range(1,4):
 p=R/f'outputs/field-sr003/source-{i:02d}.png';sourcepages.append({'path':str(p),'sha256':sha(p),'directly_inspected':True})
for g in cat['groups']:
 gid=g['group_id']
 if gid in accepted:
  assert not g['local_sr_attempted'];v=allrows[accepted[gid]];g.update(local_sr_attempted=True,status='static_candidate',hold_reason=None,candidate={'id':v['id'],'path':v['output'],'sha256':v['output_sha256'],'review':'qa/field_sr003_review.json','method':v.get('method','Local RGB neural4x +Lanczos2x, source-bound alpha'),'geometry_review':reasons[gid],'runtime_verified':False,'release_eligible':False})
 elif gid in holds:
  assert not g['local_sr_attempted'];g.update(local_sr_attempted=True,status='held',hold_reason=holds[gid],candidate=None)
assert all(next(g for g in cat['groups'] if g['group_id']==gid)['candidate']==c for gid,c in old_candidates.items())
assert sum(bool(g['candidate']) for g in cat['groups'])==73 and sum(g['status']=='held' for g in cat['groups'])==22 and sum(g['local_sr_attempted'] for g in cat['groups'])==95
cat['processing_summary'].update(field_neural_originals=95,field_static_candidates=73,field_holds=22,field_groups_not_processed_in_field_context=481,remaining_novel_unprocessed=256,latest_review='qa/field_sr003_review.json')
contract={'schema':'brs-architectural-geometry-contract/v1','user_instruction':'건물이나 배경을 판정할때 직각이어야 하는건 직각으로. 생성형은 직선을 뭉개는 경향이 있기 때문에','principles':['Intended source straight lines must remain straight; intended right-angle corners must remain right-angle corners. Sharpness/material attractiveness cannot offset bowed lines, rounded construction corners or changed grid spacing.','Record source anchors/segments/rectangular regions before accepting architectural repaint. Preserve perspective slopes and intentional arcs/fractures; do not force all image angles to90 degrees.','Use source-coordinate vector/geometry layers for structure and confine generated texture to interiors when a model changes boundaries. Separate source shading/dither from actual structural boundaries.','Review whole layout and native-resolution corners/line segments on both mattes for alpha assets; record count/spacing, positional alignment and alpha/consumer limits.','Candidate files made before this user instruction require a geometry applicability review. Historical material QA counts are retained but are not final geometry acceptance.'],'current_batch_geometry_holds':holds,'current_batch_static_candidates':accepted,'historical_field_candidates_pending_geometry_applicability_review':sorted(old_candidates),'historical_battle_candidates_pending_geometry_applicability_review':[g['group_id'] for g in battle['groups'] if g.get('selected') or g.get('candidate')],'runtime_verified':False,'release_eligible':False}
assert len(contract['historical_battle_candidates_pending_geometry_applicability_review'])==241
save('qa/architectural_geometry_contract.json',contract);cat['architectural_geometry_contract']='qa/architectural_geometry_contract.json';save('qa/field_sr_catalog.json',cat)
review={'schema':'brs-field-alpha-review/v1','batch':'FIELD-SR-003','previous_goal_turn_classification':'progress: field40 new neural originals/36 new static candidates and prior FM0078 geometry hold resolved.','new_neural_unique_originals':27,'actual_local_rgb_passes':64,'actual_local_alpha_passes':38,'actual_local_inference_passes':102,'external_generative_calls':0,'image_upload':False,'checked_outputs':checked,'new_field_static_candidates':accepted,'new_holds':holds,'new_geometry_reconstructions_selected':['FM0045','FM0120'],'geometry_contract':'qa/architectural_geometry_contract.json','geometry_contract_sha256':sha(R/'qa/architectural_geometry_contract.json'),'source_pages_directly_inspected':sourcepages,'comparison_pages_directly_inspected':30,'review_evidence':[{'path':p['path'],'sha256':p['sha256'],'directly_inspected':True} for p in evidence],'field_processing_summary':cat['processing_summary'],'unique_neural_originals_title_battle_novel_field':352,'unique_count_basis':'Title1 +battle256 +novel field95; vector and alpha postprocessing are not additional neural originals.','protected_file_hashes':audit['protected_file_hashes'],'pack_hashes':audit['pack_hashes'],'previous61_field_candidates_preserved':True,'limits':['Initial54 outputs reproduce exactly from saved native inference and per-panel processing; actual calls58 RGB+38 alpha. Rework6 RGB calls bring total102.','Alpha source-bilinear20 outputs are exact. Initial weak>=16 to reduced<8 and>=8 to reduced<4 tests show0 losses, but FM0087 peak strength/reduction threshold disagreement requires hold.','FM0087 nearest-control reduction IoU128 is only.7558, versus original-bilinear.5: reduction is not direct consumer alpha-test simulation. Texel-center samples and cubic/Lanczos controls are separate diagnostics.','Direct planar geometry fixes declared regions; source-nearest alpha is intentional, not a claim of new AI contour detail. Source small intra-plane lighting flecks are interpreted, not pixel-exact.','12 selections are static source/material/geometry candidates only. Existing61 field and prior battle candidates require applicability checks against the newly explicit straight-line gate.','No new PPSSPP key, game installation, emulator launch or runtime verification.'],'runtime_verified':False,'release_eligible':False,'all_game_complete':False,'remaining':['Novel field256 unprocessed +22 holds; existing61 field candidates need new geometry-policy applicability review.','Battle26 unprocessed +17 holds; historical candidates need new geometry-policy applicability review.','Remaining field formats/character/enemy/effects/cutscene source coverage; full game runtime/Orbit/LOCK ON and final distributable.'],'next_action':'Apply straight-line gate to prior architectural field candidates using source anchors; prioritize FM0029/0113 grids and facade37/38/116, then field unprocessed source inventory. Do not repeatedly retry local smoothers on115/121/122 without a changed geometry premise.'}
assert base['actual_local_inference_passes']==96 and rew['actual_local_inference_passes']==6
scripts=['field_sr003.py','audit_field_sr003.py','rework_field_sr003.py','repair_field087_alpha.py','redraw_field_rectilinear.py','redraw_field_rectilinear_v2.py','finalize_field_sr003.py'];review['scripts']={p:sha(R/'tools'/p) for p in scripts};save('qa/field_sr003_review.json',review)
for p,h in audit['protected_file_hashes'].items():check(R/p,h)
assert audit['pack_hashes']=={str(p.relative_to(pack)):sha(p) for p in pack.rglob('*') if p.is_file()}
with (R/'PROGRESS.md').open('a',encoding='utf8') as f:f.write('''

## 2026-09-23 — FIELD-SR-003 / 직선·직각 판정 반영
- 이전 FIELD-SR-002는 신규40/36후보와격자수정으로 progress. 이번도 투명field27신규원본/102실제local추론/66출력검증/12정적후보 및 직선·직각 계약을추가한 progress. 전체목표 active.
- 원본3페이지 재확인 후 WDN/Photo54결과: RGB58+alpha38=96pass. FM0254/0255 눈에보이는두행격리(소비자/UV증거아님). 가는8종과nearopaque2종20출력은 source-bilinear alpha정확; 나머지는20%neural/80%source와0/255support/평균보정. 새외부업로드0.
- 비교9페이지+native상세12페이지 모두검토. FM0115/0121/0122 추가WDNσ.65와Fate animeσ.35 6RGBpass/6결과 모두불채택: 강한선/입체화 또는단순흐림. 새원본누계27 그대로.
- 초기약alpha검사손실0만으로전체보존주장불가. FM0087 bilinear축소128IoU.5 확인; sourceNN대조도.7558이므로이측정은runtimealpha-test증거아님. texel-center128IoU.97647/240IoU0, bicubic/Lanczos보정2출력은center개선하지만mass+4.95%/+8.42%, 약점1/4개손실. 두배경전체/상세검수후모두보류. 새로운추론0.
- 사용자 ‘직각이어야 하는건 직각’ 반영. 원본직선·직각/칸간격/원근선 보호, 생성재질로구조변형덮기금지. qa/architectural_geometry_contract.json. 원근/의도된아치/파손은무조건90도로왜곡하지않음. 기존61field후보와battle후보는신규geometry적용대상판정대기; 이전material후보숫자만으로최종geometry통과주장금지.
- FM0045/0120 직접SVG v1은원본색픽셀블록이남아탈락. v2 구조rect와면의linear gradient분리+local고주파±4 RGB만안쪽활용. 원본alpha정확/편집mask밖parent정확/blackrail14x2 source사각검증/모든SVG rect축정렬·roundedcorner없음. 두v2정적후보; 직접도형출력을새AI복원으로세지않음. v1/v2총4페이지검수.
- 새12후보: FM0045/0120 planar v2, WDN FM0060/0123/0124/0260/0263, Photo FM0157/0254/0255/0256/0264. 새15보류: FM0029/0037/0038/0047/0059/0087/0113/0115/0116/0121/0122/0145/0164/0268/0272. 각실패/추가geometry조건은최종보고서에기록. 작은그래픽272와격자29/113보호필요.
- 전체66출력=초기54+local재작업6+alpha후처리2+SVGv1/v2 4. 원본PTM/RGBA·model/input/native/parent/output·vector/render/mask SHA/크기·저장native후처리재현검증. 검수30페이지+source3. qa/field_sr003_review.json.
- 현재field95neural/73정적후보/22보류/novel미처리256, 소비문맥미처리481. title1+battle256+field95=neural고유352. battle241후보/17보류/26미처리와20key팩/원본inventory보존. 설치/에뮬실행/실게임/최종ZIP미완료.
- 다음 기존건물후보의원본직선anchor검수와29/113격자·37/38/116창틀직접재구성, field잔여256 및적/효과/컷신범위계속. GUI복구증거없어검은화면캡처/재실행반복없음.
''')
with (C/'outputs/로컬_업스케일_진행.md').open('a',encoding='utf8') as f:f.write('''

## 필드 투명 배경과 직선·직각 검수 — FIELD-SR-003
- 27종을 로컬 처리해 12종을 정적 후보로 남겼고, 15종은 구조·그림·투명도 문제로 보류했습니다. 실제 로컬 추론102회, 외부생성0회입니다.
- 기둥/창틀2종은 원본 좌표로 직접 구성했습니다. 첫 픽셀블록 시안은 제외하고, 구조와 면의 명암을 분리한 두 번째 안을 골랐습니다. 새 AI 상세복원이라고 세지 않습니다.
- 직선·직각을 흐트러뜨린 결과는 통과시키지 않습니다. 이전 건물 후보도 이 기준의 적용 여부부터 다시 검토합니다.
- 현재 전투43종 미해결, 새 필드256종 미처리와22종 보류입니다. 캐릭터·적·효과 및 실제 게임 적용 검수와 최종 배포도 남았습니다. 완료 시각은 아직 확정할 수 없습니다.
''')
preview=C/'outputs/직선_직각_재구성_비교.png';shutil.copyfile(v2['pages'][1]['path'],preview);check(preview,v2['pages'][1]['sha256'])
print(json.dumps({'checked_outputs':66,'local_inference_passes':102,'new_candidates':12,'new_holds':15,'field_summary':cat['processing_summary'],'battle_geometry_queue_count':len(contract['historical_battle_candidates_pending_geometry_applicability_review']),'user_preview':str(preview)},ensure_ascii=False))
