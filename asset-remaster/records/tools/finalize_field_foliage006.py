from pathlib import Path
import sys,json,hashlib,copy,shutil,importlib.util
sys.dont_write_bytecode=True
import numpy as np
from scipy.ndimage import label,find_objects,distance_transform_edt
from PIL import Image,ImageDraw,ImageFont
R=Path(r'P:\AI\Codex\projects\black-rock-shooter-hd-ui-fonts');C=Path(r'C:\Users\CadriacLord\Documents\Codex\2026-09-22\brs-hd-ui-fonts');Q=R/'qa/field_foliage006_review.json';assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text('utf8'))
def write(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False),'utf8')
def arr(p):return np.asarray(Image.open(p).convert('RGBA'))
last=read(R/'qa/field_geometry010_review.json');cp=R/'qa/field_sr_catalog.json';gp=R/'qa/architectural_geometry_contract.json';assert sha(cp)==last['catalog_after_sha256'] and sha(gp)==last['geometry_contract_after_sha256'];cat=read(cp);before=copy.deepcopy(cat);contract=read(gp)
for rel,h in last['protected_file_hashes'].items():assert sha(R/rel)==h
pack=R/'workspace/local-sr/observed-review-pack-v2/PSP/TEXTURES/NPUH10126';packhash={str(p.relative_to(pack)):sha(p) for p in pack.rglob('*') if p.is_file()};assert packhash==last['pack_hashes']
old=[g['candidate'] for g in cat['groups'] if g['candidate']];assert len(old)==108
for c in old:assert sha(c['path'])==c['sha256']
names=['field_foliage006_source_audit.json','field_foliage006_local.json','field_foliage006_visual_check.json','field_foliage006_matte.json','field_foliage006_priors.json','field_foliage006_local_validation.json','field_foliage006_gpt_raw.json','field_foliage006_tree_adaptation.json','field_foliage006_weed_v2.json','field_foliage006_weed_shape.json'];rs={n:read(R/'qa'/n) for n in names};audit,base,interim,matte,priors,val,gpt,tree,v2,shape=[rs[n] for n in names]
for rel,h in val['reports_sha256'].items():assert sha(R/rel)==h
assert val['actual_RGB_passes']==26 and val['new_local_unique_originals']==9
gids={p['group_id'] for p in base['prepared_sources']};assert len(gids)==9
for p in base['prepared_sources']:
 assert sha(p['source_ptm'])==p['source_ptm_sha256'] and hashlib.sha256(arr(p['source']).tobytes()).hexdigest()==p['source_rgba_sha256']
for v in val['checked_outputs']:assert sha(v['path'])==v['sha256']
checked=list(val['checked_outputs'])
for p in gpt['files']:
 for k in ['reference','prompt']:assert sha(p[k])==p[k+'_sha256']
 assert sha(p['raw_generated_image'])==p['raw_sha256'];assert Image.open(p['raw_generated_image']).size==tuple(p['raw_size'])
 checked.append({'id':p['group_id']+'-GPT-raw-v1','path':p['raw_generated_image'],'sha256':p['raw_sha256'],'decision':'not_selected','reason':'FM0290 too sparse; FM0314 material improves but changes trunk alignment and lower background.','runtime_verified':False})
for k in ['raw','prompt','output','program']:
 if k in v2:assert sha(v2[k])==v2[k+'_sha256']
for p in v2['references']:assert sha(p['path'])==p['sha256']
assert np.array_equal(arr(v2['output']),np.asarray(Image.open(v2['raw']).convert('RGBA').resize((512,512),Image.Resampling.LANCZOS)))
checked += [{'id':'FM0290-GPT-raw-v2','path':v2['raw'],'sha256':v2['raw_sha256'],'decision':'not_selected','reason':'Density correction overshoots source total alpha by18.58percent.'},{'id':v2['id'],'path':v2['output'],'sha256':v2['output_sha256'],'decision':'not_selected','reason':'Resized v2 remains too dense.'}]
assert sha(tree['raw'])==tree['raw_sha256'] and sha(tree['source_alpha'])==tree['source_alpha_sha256'];s=Image.open(tree['source']).convert('RGBA');size=(s.width*8,s.height*8);bb=np.array(Image.open(tree['raw']).convert('RGBA').resize(size,Image.Resampling.LANCZOS));src=np.array(s.resize(size,Image.Resampling.NEAREST));good=bb[:,:,3]>=128;indices=distance_transform_edt(~good,return_distances=False,return_indices=True);rgb=bb[:,:,:3].copy();rgb[~good]=rgb[indices[0][~good],indices[1][~good]]
for p in tree['files']:
 assert sha(p['output'])==p['output_sha256'];ex=bb.copy()
 if p['alpha_policy']=='source-alpha':ex[:,:,:3]=rgb;ex[:,:,3]=np.asarray(Image.open(tree['source_alpha']))
 ex[1000:]=src[1000:];assert np.array_equal(ex,arr(p['output']))
 checked.append({'id':p['id'],'path':p['output'],'sha256':p['output_sha256'],'decision':'held','reason':'Ground restored numerically but produces a pixel-stepped strip; generated trunk geometry/lower backdrop still differs. Fixed source alpha also visibly clips leaves into the original coarse shape.','RGBA_recipe_reproduced':True})
for k in ['output','program']:assert sha(shape[k])==shape[k+'_sha256']
for p in shape['parents']:assert sha(p['path'])==p['sha256']
spec=importlib.util.spec_from_file_location('foliage006_shape_final_replay',shape['program']);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);expected,diag=mod.build(arr(shape['source']),*[arr(p['path']) for p in shape['parents']]);out=arr(shape['output']);assert np.array_equal(expected,out);assert abs(diag['alpha_mass_ratio']-1)<1e-5
for key,value in diag.items():assert value==shape['diagnostics'][key]
source=arr(shape['source']);assert hashlib.sha256(source.tobytes()).hexdigest()==shape['source_rgba_sha256'];alpha=out[:,:,3];sm=source[:,:,3]>=128;small=np.asarray(Image.fromarray(alpha).resize((64,64),Image.Resampling.BOX));om=small>=128
tips=[]
for p in shape['tip_landmarks']:
 x0,y0,x1,y1=p['source_box'];rec=copy.deepcopy(p)
 for tag,m in [('source',sm),('output',om)]:
  ys,xs=np.where(m[y0:y1,x0:x1]);top=int(ys.min());assert p[tag]=={'top_y':y0+top,'top_two_rows_x_mean':float(x0+xs[ys<=top+1].mean())}
 assert p['top_y_shift_source_px']==0 and abs(p['top_x_shift_source_px'])<=.100001;tips.append(rec)
components={}
for t in [1,64,128,192,254]:
 labels,n=label(alpha>=t,np.ones((3,3),int));counts=np.bincount(labels.ravel())[1:];boxes=find_objects(labels);components[str(t)]=[{'pixels':int(counts[i]),'bbox_yx':[[b.start,b.stop] for b in box],'touches_bottom':bool((labels[-1]==i+1).any())} for i,box in enumerate(boxes)]
assert len(components['128'])==2 and all(p['touches_bottom'] for p in components['128'])
zones={str([a,b]):{'source_alpha_mean':float(source[a:b,:,3].mean()),'candidate_alpha_mean':float(alpha[a*8:b*8].mean())} for a,b in [(0,21),(21,43),(43,64)]}
checked.append({'id':shape['id'],'path':shape['output'],'sha256':shape['output_sha256'],'decision':'static_candidate','reason':'Distinct tapered leaves and slender stems replace local melted blobs. Signed-distance shape interpolation restores source total coverage, while four prominent source tip landmarks remain aligned. Fine leaves, holes and alpha are newly drawn and are not pixel-exact source topology.','RGBA_recipe_reproduced':True,'runtime_verified':False,'release_eligible':False});assert len(checked)==33
pages=[]
for p in audit.get('pages',[]):
 assert sha(p['path'])==p['sha256'];pages.append({**p,'review_status':'directly_inspected_by_Codex_internal'})
pages+=val['pages']
for rep in [gpt,tree,v2,shape]:
 for p in rep['pages']:
  assert sha(p['path'])==p['sha256'];pages.append({**p,'review_status':'directly_inspected_by_Codex_internal'})
holds={p['group_id']:p['finding'] for p in interim['inspection'] if p['group_id']!='FM0290'}
holds['FM0314']='Local canopy becomes cracked planes. GPT improves leaf and bark material but moves/changes trunk and lower backdrop geometry; both ground adaptations retain mismatches. Need source-defined trunk silhouettes/branch junctions and intact lower background, then transfer generated materials only within those regions.'
for g in cat['groups']:
 gid=g['group_id']
 if gid not in gids:continue
 assert not g['local_sr_attempted'] and g['battle_pixel_equivalent_group'] is None and g['status']=='not_processed_in_field_context';g['local_sr_attempted']=True
 if gid=='FM0290':g.update(status='static_candidate',hold_reason=None,candidate={'id':shape['id'],'path':shape['output'],'sha256':shape['output_sha256'],'review':'qa/field_foliage006_review.json','method':shape['method'],'geometry_review':'Four prominent tip positions checked; total alpha mass restored, but individual leaf contours and hole topology are repainted, not source-exact. Both components at alpha128 reach the bottom edge. Runtime behavior unverified.','runtime_verified':False,'release_eligible':False})
 else:g.update(status='held',hold_reason=holds[gid],candidate=None)
for a,b in zip(before['groups'],cat['groups']):
 if a['group_id'] not in gids:assert a==b
stats=cat['processing_summary'];stats.update(field_neural_originals=158,field_static_candidates=109,field_holds=53,field_groups_not_processed_in_field_context=414,remaining_novel_unprocessed=189,field_processed_novel_originals_all_routes=162,latest_review='qa/field_foliage006_review.json',counting_note='158 locally inferred originals +3 direct-GPT-only +1 geometry-only =162 processed novel field originals. GPT foliage290/314 overlap the local9 and do not add unique originals again. Static candidate109, held53. Local retries and geometry derivatives are not new originals.')
assert sum(g['local_sr_attempted'] for g in cat['groups'])==158 and sum(bool(g['candidate']) for g in cat['groups'])==109 and sum(g['status']=='held' for g in cat['groups'])==53 and sum(g['status']=='not_processed_in_field_context' for g in cat['groups'])==414
contract['field_foliage006_review']={'review':'qa/field_foliage006_review.json','new_static_candidates':{'FM0290':shape['id']},'new_holds':holds,'new_local_passes':26,'new_external_calls':3,'alpha_distinction':'All26 rejected local trials use separately reconstructed source alpha with verified source topology. The selected natural-plant repaint instead uses newly drawn fine-leaf alpha, source total mass and4 tip controls. It does not claim source holes, pixel topology or runtime alpha testing preserved. Architectural apertures/checker alpha rules are not waived.','runtime_verified':False,'release_eligible':False};contract['current_batch_geometry_holds'].update(holds)
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',16);canvas=Image.new('RGB',(1050,810),'#25313c');draw=ImageDraw.Draw(canvas);oldphoto=next(p for p in base['files'] if p['id']=='FM0290-photo')
for row,(matte,mlabel) in enumerate([('#18222c','어두운 배경'),('#dedede','밝은 배경')]):
 for col,(path,title) in enumerate([(shape['source'],'원본 · 단순 확대'),(oldphoto['output'],'로컬 비교'),(shape['output'],'재작화·밀도 조정 후보')]):
  im=Image.open(path).convert('RGBA').resize((320,320),Image.Resampling.NEAREST if col==0 else Image.Resampling.LANCZOS);bg=Image.new('RGBA',im.size,matte);bg.alpha_composite(im);draw.text((col*350+8,row*405+8),title,font=font,fill='white');draw.text((col*350+8,row*405+32),mlabel,font=font,fill='#c7d1da');canvas.paste(bg.convert('RGB'),(col*350+15,row*405+68))
preview=R/'outputs/field-foliage006/풀_재작화와_밀도_수정.png';canvas.save(preview);localpreview=C/'outputs'/preview.name;shutil.copy2(preview,localpreview)
backup=R/'qa/backups/before-field-foliage006-review';backup.mkdir(exist_ok=False)
for p in [cp,gp]:shutil.copy2(p,backup/p.name)
write(cp,cat);write(gp,contract)
report={'schema':'brs-field-foliage006-final-review/v1','batch':'FIELD-FOLIAGE-006','previous_goal_turn_classification':'progress: completed base visual review and ruled out accepting melted/stone-like foliage; recorded changed preprocessing hypothesis','this_goal_turn_classification':'progress: authored-RGB and alternative-prior experiments,26 local outputs verified;3 actual GPT calls;1 source-density contour reconstruction becomes a static candidate;8 remain held with explicit changed next actions','new_local_neural_unique_originals':9,'actual_local_RGB_passes':26,'actual_alpha_neural_passes':0,'external_generative_calls':3,'new_direct_GPT_only_unique_originals':0,'new_geometry_only_unique_originals':0,'checked_outputs':checked,'new_static_candidates':{'FM0290':shape['id']},'new_holds':holds,'source_reports_sha256':{str((R/'qa'/n).relative_to(R)):sha(R/'qa'/n) for n in names},'source_and_comparison_pages':pages,'pages_directly_inspected':sum(p['review_status']=='directly_inspected_by_Codex_internal' for p in pages),'raw_GPT_images_directly_inspected':3,'candidate_alpha_diagnostics':{**shape['diagnostics'],'components_by_threshold':components,'zone_coverage':zones,'tip_landmarks':tips},'catalog_before_sha256':last['catalog_after_sha256'],'catalog_after_sha256':sha(cp),'geometry_contract_before_sha256':last['geometry_contract_after_sha256'],'geometry_contract_after_sha256':sha(gp),'other567_field_groups_unchanged':True,'previous108_field_candidates_unchanged':True,'field_processing_summary':stats,'unique_local_neural_originals_title_battle_novel_field':415,'processed_originals_title_battle_novel_field_all_routes':421,'all_routes_count_basis':{'title':1,'battle':258,'novel_field':162},'protected_file_hashes':last['protected_file_hashes'],'pack_hashes':packhash,'preview':{'path':str(localpreview),'project_path':str(preview),'sha256':sha(preview),'review_status':'pending_direct_inspection'},'runtime_verified':False,'release_eligible':False,'all_game_complete':False,'limits':['Original-RGB matte changed edges but did not fix material identity. SwinIR adds grid/ringing; Anime6B flattens materials. All26 local attempts are unselected.','GPT290v1 is15.76percent too sparse;v2 is18.58percent too dense. Neither whole draft is selected. The authored third version interpolates actual contours, not semitransparent ghost compositing, to match original total alpha. RGB comes from both paintings.','Selected290 alpha mass ratio0.99999929; source-scale IoU0.866327 and289 of4096 coarse mask samples differ. Fine leaves/holes are repainted. This is not high-resolution ground truth, original topology or exact original density in every subregion.','Four selected tip regions have0 vertical and maximum0.1source-pixel horizontal centroid change. This checks those controls only, not every stem. At threshold128 both foreground components reach bottom; at higher thresholds tiny fragments can separate. Runtime alpha behavior remains unverified.','Tree314 material donor is useful but whole result is held because trunk placement and lower background change. Restoring source alpha crudely clips leaves; ground-strip copy creates pixel steps. Next is source-defined tree/background regions, not another blind grain or alpha-strength sweep.','Current field53 holds/189 novel unprocessed, battle43 unresolved, historical geometry applicability checks, other character/enemy/UI/effect/cutscene and unsupported source populations remain.','No new PPSSPP texture key, installation, emulator launch, actual-game verification or release ZIP. GUI unavailable; Explorer not claimed opened.'],'next_action':'Trace source-defined314 major trunk silhouettes, forks and baked lower background. Use the existing generated bark/foliage only in the matching material regions. Consider that method for related316/317/325 only after own-source confirmation. Continue broad-leaf301/canopies312/318/320 and all remaining game scope.'}
for rel,h in last['protected_file_hashes'].items():assert sha(R/rel)==h
assert {str(p.relative_to(pack)):sha(p) for p in pack.rglob('*') if p.is_file()}==packhash
write(Q,report)
note='''

## 2026-09-23 — FIELD-FOLIAGE-006 / 식물9종·재작화와 밀도 조정
- 이전 중간검수 turn은 progress. 이번 원본 RGB/matte 비교4회와 SwinIR/Anime6B4회 추가, 기존18회 포함 실제 로컬RGB26회/신규9원본. 로컬26출력은 잎 뭉개짐·돌/평면 해석·ringing 등으로 모두 불채택. 입력/모델/native/crop/resize/원본alpha9recipe 재현 검사.
- built-in image_gen 실제3회: FM0290 2안,FM0314 1안. prompt/raw/reference 해시와 원본을 workspace/gpt-trials에 보존. 290 첫안alpha질량 원본의.84236, 둘째1.18580이라 둘다통째로불채택. 두그림의 signed-distance 윤곽을 직접조정한v3는 질량비.99999929/4주요끝 y변화0,x최대.1source px. 양배경 전체/잎끝/하단 직접검수후 정적후보1종.
- 290v3의세부잎·구멍·alpha는새재작화이며원본pixel/topology동일아님. source-scale maskIoU.866327/289샘플상이. alpha128에서2덩어리모두하단접촉,높은threshold에작은분리조각. 이는실게임alpha-test증거아님. 버려진로컬26의sourcealpha보존검사와선택GPT파생alpha를혼동하지않음.
- 314재작화는잎/나무껍질재질개선됐으나줄기위치/하단배경변경. 원본지면3행복원2안은pixel단차,sourcealpha재적용은잎을둔한덩어리로잘라불채택. 314포함나머지8종보류. 다음원본줄기/분기/하단배경영역정의후재질만대응영역으로전사;추가무작정model/grain강도반복안함.
- 전체33출력 lineage/recipe검증,새후보290v3/보류8. qa/field_foliage006_review.json authoritative. 기존108후보/다른567group/보호5파일/20key팩22파일불변. raw기록은변경안함.
- 현재field158local+3directGPT-only+1geometry-only=162처리,109정적후보/53보류/189novel미처리. context미처리414에는battle동일225포함. 전게임현재조사범위local415/allroutes421. GPT3회는local9와겹치므로고유원본추가안함. 설치/실게임/전체게임완료/최종ZIP미완료,전체목표active.
'''
for path in [R/'PROGRESS.md',C/'outputs/로컬_업스케일_진행.md']:
 with path.open('a',encoding='utf8') as f:f.write(note)
print(json.dumps({'review':str(Q),'outputs':len(checked),'pages':len(pages),'directly_seen':report['pages_directly_inspected'],'field_candidates':109,'field_holds':53,'remaining_novel':189,'preview':str(preview)}))
