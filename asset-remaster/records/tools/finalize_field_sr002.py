"""Verify inspected outputs, promote static candidates and retain unresolved scope."""
import json,hashlib,shutil
from pathlib import Path
import numpy as np,cv2
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];C=Path('C:/Users/CadriacLord/Documents/Codex/2026-09-22/brs-hd-ui-fonts');Q=R/'qa/field_sr002_review.json';assert not Q.exists()
def read(p):return json.loads((R/p).read_text('utf8'))
def save(p,v):(R/p).write_text(json.dumps(v,ensure_ascii=False,indent=2),'utf8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def img(p):return Image.open(p).convert('RGBA')
def check(p,h):assert sha(p)==h,str(p)
oldreview=read('qa/field_sr001_review.json');protected=oldreview['protected_file_hashes'];pack=Path(read('qa/local_sr_observed_review_pack_v2.json')['path'])
for p,h in protected.items():check(R/p,h)
assert oldreview['pack_hashes']=={str(p.relative_to(pack)):sha(p) for p in pack.rglob('*') if p.is_file()}
cat=read('qa/field_sr_catalog.json');oldgroups={g['group_id']:g for g in cat['groups']};assert sum(bool(g['candidate']) for g in cat['groups'])==24 and sum(g['status']=='held' for g in cat['groups'])==4
backup=R/'qa/backups/before-field-sr002-review';backup.mkdir(parents=True,exist_ok=False)
for name in ['field_sr_catalog.json','field_sr001_review.json','field_sr002_inference.json','field_sr002_rework.json','field_sr002_gpt_material.json','field_sr002_gpt_registered.json','field_grid003.json']:shutil.copyfile(R/'qa'/name,backup/name)
pick={125:'photo',126:'photo',127:'wdn',128:'wdn',129:'photo',130:'wdn',133:'photo',135:'photo',136:'photo',139:'wdn',142:'wdn',143:'wdn',144:'photo',146:'wdn',147:'wdn',148:'photo',149:'photo',150:'wdn',151:'wdn',152:'photo',153:'wdn',154:'photo',156:'wdn',161:'wdn',163:'photo',168:'photo',178:'wdn',189:'photo',190:'wdn',253:'wdn',257:'wdn',258:'wdn',259:'photo',265:'wdn',270:'wdn'}
accepted={f'FM{n:04d}':f'FM{n:04d}-{t}' for n,t in pick.items()};accepted['FM0160']='FM0160-gpt-registered-tone065'
holds={'FM0132':'Fixed sample has15 source dark troughs versus14 in both models; repeated board/slat detail is ambiguous and needs source-specific reconstruction. A profile count alone is not a physical plank count.','FM0137':'Yellow-region count remains7 but thresholded coverage IoU is .821596; original dither and edge coverage are not sufficiently resolved to certify the stripe shape. Preserve as hold for protected hazard repaint.','FM0167':'Fine diagonal/diamond patch looks smeared in WDN and becomes dense embossed mesh in Photo. Whole atlas withheld pending pattern reconstruction.','FM0188':'Faint source marks are emphasized as cracks in all four local trials; need restrained material reconstruction. Not every source mark is invented.'}
assert len(accepted)==36 and len(holds)==4
rep=read('qa/field_sr002_inference.json');rew=read('qa/field_sr002_rework.json');checked=[];rows={}
for name,report in [('qa/field_sr002_inference.json',rep),('qa/field_sr002_rework.json',rew)]:
 for v in report['files']:
  s=img(v['source']);o=img(v['output']);assert hashlib.sha256(s.tobytes()).hexdigest()==v['source_rgba_sha256'];check(v['source_ptm'],v['source_ptm_sha256']);check(v['model']['path'],v['model']['sha256'])
  for k in ['input','native','output']:check(v[k],v[k+'_sha256'])
  native=Image.open(v['native']).convert('RGB');assert native.size==(s.width*4,s.height*4) and o.size==(s.width*8,s.height*8)==tuple(v['output_size']);assert o.getchannel('A').getextrema()==(255,255);assert np.array_equal(np.asarray(o),np.asarray(native.resize(o.size,Image.Resampling.LANCZOS).convert('RGBA')))
  gid=v['group_id'];status='selected_static_candidate' if accepted.get(gid)==v['id'] else ('held' if gid in holds else 'not_selected')
  reason=holds.get(gid,'Compared with source and alternative model; static material/layout candidate only.' if status=='selected_static_candidate' else 'Alternative not selected after comparison.')
  if gid=='FM0160':reason='Existing faint source marks are amplified by local trials. Registered external repaint selected instead; not a claim that every crack was invented.'
  v['visual_review']={'reviewer':'Codex internal','status':status,'reason':reason};checked.append({'id':v['id'],'source_ptm_rgba_model_input_native_output_hashes_verified':True,'native4x_final8x_and_Lanczos_reproduction_verified':True,'opaque255':True,'decision':status});rows[v['id']]=v
 for p in report['pages']:check(p['path'],p['sha256']);p['review_status']='directly_inspected_by_Codex_internal'
 save(name,report)
assert len(checked)==84 and rep['actual_local_rgb_inference_passes']+rew['actual_local_rgb_inference_passes']==84
details=read('qa/field_sr002_details.json')
for p in details['pages']:check(p['path'],p['sha256']);p['review_status']='directly_inspected_by_Codex_internal'
save('qa/field_sr002_details.json',details)
grid=read('qa/field_grid003.json');audit=read('qa/field_sr002_geometry_audit.json')
for k in ['source_ptm','parent','vector','render','mask','output','comparison']:check(grid[k],grid[k+'_sha256'])
s=img(grid['source']);o=img(grid['output']);mask=np.asarray(Image.open(grid['mask']))>0;assert hashlib.sha256(s.tobytes()).hexdigest()==grid['source_rgba_sha256'];assert np.array_equal(np.asarray(o)[~mask],np.asarray(img(grid['parent']))[~mask]);assert o.getchannel('A').getextrema()==(255,255)
box=tuple(grid['source_box']);lo=np.asarray(s.crop(box))[:,:,:3].mean(2)<95;hi=np.asarray(o.crop(tuple(x*8 for x in box)))[:,:,:3].mean(2)<95;assert np.array_equal(np.repeat(np.repeat(lo,8,axis=0),8,axis=1),hi);assert cv2.connectedComponents(lo.astype('uint8'),8)[0]-1==cv2.connectedComponents(hi.astype('uint8'),8)[0]-1==16
for c in grid['cells']:
 x,y=c['source_pixel'];assert np.all(np.asarray(o)[y*8:(y+1)*8,x*8:(x+1)*8]==c['source_rgba'])
grid['visual_review']={'reviewer':'Codex internal','status':'selected_static_candidate','reason':'Connected source-fixed lattice restores16 dark cells without separate raised button rims. Source-colored bar gradients keep sharp openings; existing frame remains parent. Geometric reconstruction, not newly recovered high-frequency material.'};save('qa/field_grid003.json',grid);rows[grid['id']]=grid
checked.append({'id':grid['id'],'source_ptm_rgba_parent_svg_mask_output_hashes_verified':True,'dark_components_source_output':[16,16],'full_dark_class_mask_source_nearest_exact':True,'dark_core_rgba_exact_output_pixels':1024,'outside_mask_rgba_exact':True,'edit_pixels':5184,'decision':'selected_static_candidate'})
gpt=read('qa/field_sr002_gpt_material.json');reg=read('qa/field_sr002_gpt_registered.json');check(gpt['raw_generated'],gpt['raw_generated_sha256']);check(gpt['prompt'],gpt['prompt_sha256']);assert img(gpt['raw_generated']).size==tuple(gpt['actual_generated_size'])==(1254,1254)
for v in gpt['files']:
 s=img(v['source']);o=img(v['output']);assert hashlib.sha256(s.tobytes()).hexdigest()==v['source_rgba_sha256'];check(v['source_ptm'],v['source_ptm_sha256']);check(v['generated'],v['generated_sha256']);check(v['output'],v['output_sha256']);assert o.size==(512,512) and o.getchannel('A').getextrema()==(255,255);v['visual_review']={'reviewer':'Codex internal','status':'superseded','reason':'Useful subdued material, but center-right edge differs from source (p95 1.1875 source px). Superseded by registered version.'};checked.append({'id':v['id'],'hashes_size_alpha_verified':True,'decision':'superseded'})
for k in ['source_ptm','generated','parent','registration_map','before_tone','output','comparison']:check(reg[k],reg[k+'_sha256'])
o=img(reg['output']);s=img(reg['source']);assert hashlib.sha256(s.tobytes()).hexdigest()==reg['source_rgba_sha256'];assert o.size==(s.width*8,s.height*8) and o.getchannel('A').getextrema()==(255,255)
mapping=np.load(reg['registration_map']);mx,my=mapping['map_x'],mapping['map_y'];assert mx.shape==my.shape==(512,512) and np.isfinite(mx).all() and np.isfinite(my).all();rebuild=cv2.remap(np.asarray(img(reg['parent']))[:,:,:3],mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE);assert np.array_equal(rebuild,np.asarray(Image.open(reg['before_tone']).convert('RGB')));assert max(reg['edge_diagnostics']['p95_abs_offset_source_px'])<=.3125
reg['visual_review']={'reviewer':'Codex internal','status':'selected_static_candidate','reason':'Subdued material retains faint marks, with source-measured center-edge shape restored and low-frequency palette matching. 60-row edge diagnostic is partial evidence; true HD, UV and runtime not proven.'};save('qa/field_sr002_gpt_material.json',gpt);save('qa/field_sr002_gpt_registered.json',reg);rows[reg['id']]=reg;checked.append({'id':reg['id'],'source_ptm_rgba_generated_parent_map_underlay_output_hashes_verified':True,'registration_reproduced_exact':True,'opaque255_size8x_verified':True,'edge_p95_source_px':reg['edge_diagnostics']['p95_abs_offset_source_px'],'decision':'selected_static_candidate'})
assert len(checked)==88
old_candidates={g['group_id']:g['candidate'] for g in cat['groups'] if g['candidate']};newids=set(accepted)|set(holds);assert len(newids)==40 and all(not oldgroups[g]['local_sr_attempted'] for g in newids)
adopt={**accepted,'FM0078':grid['id']}
for g in cat['groups']:
 gid=g['group_id']
 if gid in adopt:
  v=rows[adopt[gid]];g.update(local_sr_attempted=True,status='static_candidate',hold_reason=None,candidate={'id':v['id'],'path':v['output'],'sha256':v['output_sha256'],'review':'qa/field_sr002_review.json','method':v.get('method','Local RGB neural4x, Lanczos2x'),'runtime_verified':False,'release_eligible':False})
 elif gid in holds:g.update(local_sr_attempted=True,status='held',hold_reason=holds[gid],candidate=None)
assert all(oldgroups[gid]['candidate']==value for gid,value in old_candidates.items())
assert sum(bool(g['candidate']) for g in cat['groups'])==61 and sum(g['status']=='held' for g in cat['groups'])==7 and sum(g['local_sr_attempted'] for g in cat['groups'])==68
cat['processing_summary'].update(field_novel_sources_classified=144,field_neural_originals=68,field_static_candidates=61,field_holds=7,field_groups_not_processed_in_field_context=508,remaining_novel_unprocessed=283,latest_review='qa/field_sr002_review.json');save('qa/field_sr_catalog.json',cat)
oldreview.setdefault('resolved_holds',{})['FM0078']={'review':'qa/field_sr002_review.json','candidate':grid['id'],'scope':'static geometry repair only; runtime false'};save('qa/field_sr001_review.json',oldreview)
evidence=[*rep['pages'],*details['pages'],*rew['pages'],{'path':grid['comparison'],'sha256':grid['comparison_sha256']},{'path':gpt['comparison'],'sha256':gpt['comparison_sha256']},{'path':reg['comparison'],'sha256':reg['comparison_sha256']}]
assert len(evidence)==36
review={'schema':'brs-field-review/v2','batch':'FIELD-SR-002 / GRID-003','previous_goal_turn_classification':'progress: field72 classified,28 neural originals/24 static candidates; SR015 six outputs reviewed and held.','source_pages_directly_inspected':8,'new_source_originals_classified':72,'total_field_novel_sources_classified':144,'new_neural_unique_originals':40,'actual_local_rgb_inference_passes':84,'external_generative_calls':1,'image_upload':True,'external_tool':'built-in image_gen; model identifier not exposed','external_prompt':gpt['prompt'],'external_prompt_sha256':gpt['prompt_sha256'],'external_actual_size':[1254,1254],'external_final_size':[512,512],'external_final_resampling':'Lanczos downsample plus registered edges and source-tone correction; not native AI8x','checked_outputs':checked,'new_field_static_candidates':accepted,'resolved_prior_holds':{'FM0078':grid['id']},'new_holds':holds,'comparison_pages_directly_inspected':36,'review_evidence':[{'path':v['path'],'sha256':v['sha256'],'directly_inspected':True} for v in evidence],'geometry_audit':'qa/field_sr002_geometry_audit.json','geometry_audit_sha256':sha(R/'qa/field_sr002_geometry_audit.json'),'diagnostic_limits':['Dark troughs are sample extrema, not physical bar counts; fixed-sample and threshold-sensitivity results are both retained.','FM0147 common sigma.5 source-unit profiles have8 strong troughs for prominence10..18 in source and both models; raw low-threshold counts include dithering.','FM0161 source and outputs show alternating dark and bright rungs, but extrema vary by threshold. Full geometric equivalence not asserted.','FM0078 complete threshold95 dark mask and16 dark-cell colors are source-exact; bar gradients are an authored interpretation.','FM0160 source already contains faint lines. The issue was contrast amplification. Registered 60-row edge p95 .3125/.0625 source px is not full UV/runtime proof.','Only inspected source-visible partitions are known; native consumers, exclusion relationships and replacement keys are not established by image quality.'],'field_processing_summary':cat['processing_summary'],'unique_neural_originals_title_battle_novel_field':325,'unique_count_basis':'Title1 + battle256 + novel field68; battle geometry-only2 excluded; prior FM0078/GPT FM0160 not extra originals.','protected_file_hashes':protected,'pack_hashes':oldreview['pack_hashes'],'previous24_field_candidates_preserved':True,'runtime_verified':False,'release_eligible':False,'all_game_complete':False,'remaining':['Battle43 unresolved groups:17 holds and26 unprocessed.','Novel field283 unprocessed and7 holds; classified144/351.','Remaining character/enemy/effect/cutscene source reachability, unsupported SC/PTMD structures, and protagonist exclusion matching.','Gameplay title/Orbit/LOCK ON/full regions/EX/true-ending runtime verification, replacement-key collection, installation/removal and final ZIP.'],'next_action':'Process previously classified alpha and protected atlas field lanes, then remaining source pages. Resolve hazard FM0137 and mesh FM0167 with source-defined geometry; reconstruct subtle FM0188 marks without intensification. No emulator launch without new screen-access evidence; fixed exe+ISO CLI only.'}
scripts=['prepare_field_sources02.py','field_sr002.py','redraw_field_grid003.py','inspect_field_sr002.py','rework_field_sr002.py','audit_field_sr002.py','prepare_field160_gpt.py','align_field160_gpt.py','finalize_field_sr002.py'];review['scripts']={n:sha(R/'tools'/n) for n in scripts};save('qa/field_sr002_review.json',review)
for p,h in protected.items():check(R/p,h)
assert oldreview['pack_hashes']=={str(p.relative_to(pack)):sha(p) for p in pack.rglob('*') if p.is_file()}
with (R/'PROGRESS.md').open('a',encoding='utf8') as f:f.write('''

## 2026-09-23 — FIELD-SR-002 / GRID-003
- 이전goal턴SR015/field001은실제분류72/추론28/정적후보24와실패검수기록으로progress. 이번도source72신규분류/40신규neural원본/84actual local pass/외부생성1/신규필드36후보+기존격자1해결로progress. 전체목표active.
- field source02의다음72개8페이지직접분류,누계144/351novel. 글자·포스터/인물·alpha·shader ramp·미세격자는별도분류,범위제외없음. 불투명40종WDN/Photo80pass, FM0160/0188에WDNσ.65와Fate anime6Bσ.35로4추가pass. 최초local80+재작업4=84출력/실제84pass.
- 20비교+11native8x crop+2재작업페이지직접검수. source geometry diagnostics 고정임계결과보존. FM0128 source/WDN8 versusPhoto10trough;FM0129source/Photo4 vsWDN5;FM0142source/WDN31 vsPhoto30;FM0153/0265표본12/7동일. 이는물리막대개수전체증거아님. FM0147공통σ.5후prominence10..18에서모두8강한trough,FM0161은threshold민감도전체기록하고완전형상보존주장안함.
- 보류4: FM0132반복가로선해석(표본15vs14),FM0137노란7연결영역은같으나축소classIoU .821596로경계/dither해석불확실,FM0167미세대각pattern왜곡,FM0188원래희미한선의균열강조. FM0148/0149/0152yellow연결영역5/8/13개각원본동일,IoU .99258/.96336/.98663. 연결영역이실제줄개수/전체UV증거는아님.
- FM0078연결격자 직접SVG v3 채택: 5가로/5세로막대,16square darkcell,source색bar gradient. 원본class threshold95 전체mask와출력정확일치/16components/16darkcore1024outputRGBA정확/mask밖parentRGBA정확;5184outputpx수정. 새로운AI상세복원이아닌sourcegeometry구성. v1버튼같은테두리와v2원본NNfallback은미채택그대로보존.
- FM0160원본에도희미한대각선/짧은균열이있음재확인,모든균열을AI발명으로일괄판정하지않음. 로컬4조건은강조가심함. built-in image_gen 1외부편집actual1254²(request1024²)→Lanczos512². 초기rightedge p95원본1.1875px차이;source60행edge기준수평등록+σ2명암.65보정후p95 .3125/.0625px. 재작화2초안+등록1출력중등록안정적채택. 정확prompt workspace/gpt-trials/FM0160-v1/prompt.txt. modelID미노출. source대표edge측정이며전체geometry/nativeUV/게임증거아님.
- 총88파생출력=local84+직접SVG1+GPT파생3. 원본PTM/RGBA·model/input/native/output·SVG/render/mask·generated/prompt/map/underlay해시,4x/8x/alpha255와localLanczos재현·GPT등록재현검사. 검수36페이지와source8페이지를보고서에연결. qa/field_sr002_review.json.
- 현재필드68neural처리/61정적후보/7보류/novel미처리283,전체576field중해당소비문맥미처리508(전투픽셀동일225포함). 이전필드24후보바이트/기존전투241후보17보류26미처리/20key팩/checker/fieldv2/Startscript완전보존. 타이틀1+전투256+field68=neural고유325;전체게임분모아님.
- 사용자‘얼마나남았어’에전투43/추가field미처리283와미완료적·캐릭터·효과·런타임·최종팩범위를설명. 전체게임자산총수미확정으로전체완료율/정확시간미제시. 도구화면오류복구증거없어에뮬재실행없음,설치/런타임/최종ZIP미완료.
- 다음: 기존분류alpha/미세격자·복합atlas보호및필드잔여283원본,FM0137경고띠·FM0167격자·FM0188재질직접수정,전투43/적/효과/컷신/미지원SC진행. 보류7에는FM0055/0117/0119도포함. source분류는소비자/UV/주인공제외증거아님.
''')
with (C/'outputs/로컬_업스케일_진행.md').open('a',encoding='utf8') as f:f.write('''

## 필드 배경 두 번째 검수 — FIELD-SR-002
- 새 필드40종을처리해36종을정적후보로남겼습니다. 로컬84회추론과외부재작화1회를사용했고,경고띠·반복목재선·격자판·균열재질4종은계속보류했습니다.
- 기존작은격자는연결된가로/세로막대로직접구성해16칸의배열과색을복원했습니다. 새AI상세복원으로세지않습니다. 회색재질은GPT재작화후원본경계와명암에맞춘안을선택했습니다.
- 현재전투43종미해결,새필드283종미처리와7종보류입니다. 필드누계61종정적후보이며전체게임완료율이아닙니다. 캐릭터·적·효과·실게임검증·최종배포도남습니다.
- 실제게임에설치하거나검증한결과는아직아닙니다. 자세한검수기록: P:/AI/Codex/projects/black-rock-shooter-hd-ui-fonts/qa/field_sr002_review.json.
''')
# Show a concise source/local/repaired grid example to the user, preserving labels.
out=C/'outputs/격자_직접_복원_비교.png';shutil.copyfile(grid['comparison'],out)
print(json.dumps({'local_passes':84,'external_calls':1,'checked_outputs':88,'new_field_candidates':36,'prior_hold_resolved':'FM0078','field_candidates_total':61,'field_holds_total':7,'field_novel_unprocessed':283,'previous24_preserved':True,'protected_pack_preserved':True,'user_preview':str(out)},ensure_ascii=False))
