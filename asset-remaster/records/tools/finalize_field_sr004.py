"""Verify frozen inference/derived recipes and record source-faithful static choices."""
import copy,hashlib,json,shutil,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np,cv2
from scipy.ndimage import gaussian_filter,gaussian_filter1d
from PIL import Image,ImageFilter,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];C=Path(r'C:\Users\CadriacLord\Documents\Codex\2026-09-22\brs-hd-ui-fonts');Q=R/'qa/field_sr004_review.json';assert not Q.exists()
def read(p):return json.loads(Path(p).read_text('utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2),'utf8')
def arr(p):return np.asarray(Image.open(p).convert('RGBA'))
last=read(R/'qa/field_geometry002_review.json');names=['field_source_review03.json','field_sr004_inference.json','field_sr004_rework.json','field_sr004_planes.json','field_sr004_plane282_v2.json','field_geometry003_hybrid.json'];reports={n:read(R/'qa'/n) for n in names}
source,base,rew,planes,p2,hybrid=[reports[n] for n in names];cp=R/'qa/field_sr_catalog.json';gp=R/'qa/architectural_geometry_contract.json';cat=read(cp);before=copy.deepcopy(cat);contract=read(gp)
assert sha(cp)==last['catalog_after_sha256']==base['source_catalog_sha256_before'];assert sha(gp)==last['geometry_contract_after_sha256']
assert base['source_review_sha256']==sha(R/'qa/field_source_review03.json');assert rew['initial_inference_sha256']==planes['parent_inference_sha256']==sha(R/'qa/field_sr004_inference.json');assert p2['previous_report_sha256']==sha(R/'qa/field_sr004_planes.json')
for rel,h in last['protected_file_hashes'].items():assert sha(R/rel)==h
pack=R/'workspace/local-sr/observed-review-pack-v2/PSP/TEXTURES/NPUH10126';packhash={str(p.relative_to(pack)):sha(p) for p in pack.rglob('*') if p.is_file()};assert packhash==last['pack_hashes']
classified=set()
for rel,h in {**source['prior_classifications_sha256'],'qa/field_source_review03.json':sha(R/'qa/field_source_review03.json')}.items():
 assert sha(R/rel)==h;d=read(R/rel)
 for v in d['files']:
  assert v['group_id'] not in classified and v['classification'];classified.add(v['group_id'])
assert len(classified)==216
for v in source['files']:
 assert sha(v['source_ptm'])==v['source_ptm_sha256'];assert hashlib.sha256(arr(v['source']).tobytes()).hexdigest()==v['source_rgba_sha256'];assert v['source_review']=='directly_inspected_by_Codex_internal'
pick={276:'photo',277:'wdn',280:'wdn',286:'wdn',297:'photo',302:'photo',304:'wdn',306:'photo',307:'photo',313:'photo',315:'wdn',322:'photo'}
selected={f'FM{k:04d}':f'FM{k:04d}-{v}' for k,v in pick.items()};selected.update(FM0282='FM0282-source-fixed-planes-v2',FM0356='FM0356-source-fixed-planes')
holds={
 'FM0275':'Vent ribs have wavy modeled edges; lower faceted islands also need source-line anchors. Preserve original straight ribs and intentional facets before accepting material.',
 'FM0303':'Initial WDN adds dense crack networks; Photo/general soften and round stone clumps. WDN065 reduces some extra lines but still emphasizes a fine fissure network. Original large cracks are real; keep held for restrained reconstruction rather than repeat smoothing.',
 'FM0305':'Original concentric wood curves are meaningful. Photo/general carve thick dark grooves; WDN conditions blur/coalesce central and lower rings. Ring continuity/topology remains unresolved after four local conditions.',
 'FM0328':'Local WDN material is the better trial, but straight facets and curved metal sections coexist. Source vertex/segment anchors are not yet established; do not accept bowed facet edges from material review alone.',
 'FM0329':'Photo reduces noisy material, but panel seams/junctions and angular islands need source-anchored geometry review. Consumer/character association remains unresolved; no automatic exclusion.',
 'FM0330':'WDN is less embellished, but long diagonal plates and corner intersections need source-defined straight segments; material review alone does not pass the geometry gate.',
 'FM0332':'Photo invents pseudo-lettering on the tiny right strip. Its original graphic identity is unresolved; WDN also needs protected strip and panel-edge reconstruction.',
 'FM0333':'Photo material is restrained, but shaft and flat panel profiles still need source anchors. Intentional tapered/rounded surfaces must not be indiscriminately squared.',
 'FM0334':'Both models bow the source folded-panel diagonals and round their junctions. Requires original facet vertices and straight segments, preserving the intentional V shape.',
 'FM0336':'Additional local conditions still exaggerate road cracks and alter fine central-stripe edges. Existing source cracks are real; preserve the source line and restrain surrounding fissure contrast.',
 'FM0337':'Repeated bright posts require source-defined bands/count/spacing. Local models add prominent cracks across posts. Profile peak counts vary with shading and are not physical post counts.',
 'FM0338':'Damaged brick joints and irregular holes coexist. Both models reinterpret brick widths/joints; explicit source rows and intact segments are needed without straightening intentional damage.',
 'FM0345':'Source center seam includes an intentional stepped diagonal bend. Local models round its two corners; WDN also turns surface shading into grooves. Reconstruct the original polyline.',
 'FM0346':'Photo changes broad pale fluted faces into thin bars against black gaps. WDN also needs original repeated profile geometry. Brightness peaks do not establish physical column counts.',
 'FM0347':'Both models turn the original curved/oval lattice into angular diamonds. Source arches must be preserved together with straight horizontal moldings.',
 'FM0363':'Source profile reveals a real center seam at x30 and highlighted/dark outer rim. Initial material-only classification is incomplete. WDN makes seam ragged; Photo/general make it too emphatic and outer edges need anchors. Hold for source-structured panel reconstruction.'}
assert len(selected)==14 and len(holds)==16 and set(selected)|set(holds)==set(base['group_ids']) and not set(selected)&set(holds)
reasons={
 'FM0276':'Photo retains broad orange/green/pale blotches without WDN lattice-like microcracks; no rectilinear construction identified in original whole/native views.',
 'FM0277':'WDN retains finer green-gray coarse grain; Photo turns it into rounded clumps. Organic source pattern, not architecture.',
 'FM0280':'WDN keeps restrained layered gray stone; Photo produces deeper glossy relief. Intentional irregular source transitions retained.',
 'FM0282':'Two original vertical supports x7..8 and61..64 fixed for all64 source rows. Source colors smoothed within strips; WDN dark material retained outside correction bands. v1 stretched-row grain rejected; v2 uses nearby spatial local material.',
 'FM0286':'WDN adds less object-like interpretation to ambiguous shaded gray material than Photo. Actual consumer/material identity remains unknown.',
 'FM0297':'Photo preserves a soft cloud bank; WDN adds dark scratch-like strokes along upper cloud edge. No rigid structural lines identified.',
 'FM0302':'Photo chosen consistently with FM0306/FM0322 to preserve broad blue-green swirls and avoid WDN diagonal streaks. Related appearance is not proof of shared animation/state consumer.',
 'FM0304':'WDN retains fine broad striations without Photo deep grooves; source material identity remains ambiguous, with no architectural grid identified.',
 'FM0306':'Photo keeps the broad dark-blue/green swirl arrangement; consistent treatment with FM0302/FM0322, without assuming consumer/state linkage.',
 'FM0307':'Photo avoids the fine spiderweb cracks introduced by WDN while retaining original broad pale streaks.',
 'FM0313':'Photo keeps bright source patches clearer; WDN adds fine branching dark cracks into them.',
 'FM0315':'WDN retains fine green surface grain; Photo overly smooths it. No architectural corner requirement identified.',
 'FM0322':'Photo preserves broad blue-green swirls with restrained detail; style matched to FM0302/FM0306 without asserting animation/state equivalence.',
 'FM0356':'Original uniform band [0,4,128,18] restored exactly to RGB115/93/74; source row colors blend into local Photo rubble at y25..33, below33 unchanged. Source image partition only, not a proven scene horizon.'}
hold190='Constrained reuse of old GPT masonry grain at strengths.45/±8 and.75/±12 preserves fixed planes and protected corners, but both still look pasted/rounded at cornice joints. Grain alone does not fix the source profile/joint interpretation. Keep held; next repair must change plane-profile/corner shading construction, not repeat a material-strength sweep.'
allrows={};checked=[];modelhashes={}
for v in base['files']+rew['files']:
 s=Image.open(v['source']).convert('RGBA');o=Image.open(v['output']).convert('RGBA');assert hashlib.sha256(s.tobytes()).hexdigest()==v['source_rgba_sha256'];assert sha(v['source_ptm'])==v['source_ptm_sha256'];m=v['model'];modelhashes.setdefault(m['path'],sha(m['path']));assert modelhashes[m['path']]==m['sha256']
 for k in ['input','native','output']:assert sha(v[k])==v[k+'_sha256']
 expected=s.convert('RGB').filter(ImageFilter.GaussianBlur(v['input_gaussian_sigma_source_px']));assert np.array_equal(np.asarray(expected),np.asarray(Image.open(v['input'])))
 native=Image.open(v['native']).convert('RGB');assert native.size==(s.width*4,s.height*4) and o.size==(s.width*8,s.height*8)
 assert np.array_equal(np.asarray(native.resize(o.size,Image.Resampling.LANCZOS).convert('RGBA')),np.asarray(o));assert o.getchannel('A').getextrema()==(255,255)
 allrows[v['id']]=v;checked.append({'id':v['id'],'group_id':v['group_id'],'path':v['output'],'sha256':v['output_sha256'],'source_model_input_native_output_hashes_verified':True,'input_prefilter_and_Lanczos_postprocess_exact':True,'neural_inference_repeated_for_validation':False,'native_scale':4,'final_scale':8,'opaque255':True,'decision':'static_candidate' if selected.get(v['group_id'])==v['id'] else 'held' if v['group_id'] in holds else 'not_selected','reason':holds.get(v['group_id'],reasons.get(v['group_id'])),'runtime_verified':False,'release_eligible':False})
for report,version in [(planes,1),(p2,2)]:
 for v in report['files']:
  gid=v['group_id'];s=arr(v['source']);p=arr(v['parent']);out=arr(v['output']);rebuilt=p.copy();mask=np.zeros(out.shape[:2],bool);h,w=s.shape[:2]
  for k in ['source_ptm','parent','output','mask','vector']:assert sha(v[k])==v[k+'_sha256']
  assert hashlib.sha256(s.tobytes()).hexdigest()==v['source_rgba_sha256'];assert out.shape==(h*8,w*8,4)
  rects=list(ET.parse(v['vector']).getroot().iter('{http://www.w3.org/2000/svg}rect'));assert rects and all(not any(k in t.attrib for k in ['rx','ry','transform']) for t in rects)
  if gid=='FM0356':
   profile=np.median(s[:,:,:3].astype('float32'),axis=1);assert np.array_equal(profile,np.asarray(v['source_row_profile_rgb']));material=cv2.resize(profile[:,None,:],(w*8,h*8),interpolation=cv2.INTER_LINEAR);material[32:144]=[115,93,74];weight=np.clip((264-(np.arange(h*8)+.5))/64,0,1).astype('float32')[:,None,None];rebuilt[:,:,:3]=np.rint(np.clip(material*weight+p[:,:,:3].astype('float32')*(1-weight),0,255)).astype('uint8');mask[:264]=True;assert np.all(out[32:144,:,:3]==[115,93,74])
  elif version==1:
   a,b=40,80;t=np.linspace(0,1,b-a,dtype='float32')[None,:,None];rebuilt[:,a:b,:3]=np.rint(p[:,a,:3].astype('float32')[:,None,:]*(1-t)+p[:,b-1,:3].astype('float32')[:,None,:]*t).astype('uint8');mask[:,a:b]=True;rebuilt[:,472:488,:3]=p[:,472,:3][:,None,:];mask[:,472:]=True
   for a,b in [(7,8),(61,64)]:
    profile=gaussian_filter1d(s[:,a:b,:3].astype('float32'),.65,axis=0,mode='nearest');assert np.array_equal(profile,np.asarray(v['saved_source_profiles'][str(a)]))
    for j in range(b-a):rebuilt[:,(a+j)*8:(a+j+1)*8,:3]=np.rint(cv2.resize(profile[:,j:j+1,:],(1,512),interpolation=cv2.INTER_LINEAR)).astype('uint8')
  else:
   for a,b,c,d in v['material_transfers_output_x']:
    patch=p[:,c:d,:3].astype('float32');weight=np.minimum((np.arange(b-a)+.5)/4,1)
    if b<512:weight=np.minimum(weight,(b-a-np.arange(b-a)-.5)/4)
    rebuilt[:,a:b,:3]=np.rint(patch*weight[None,:,None]+p[:,a:b,:3]*(1-weight[None,:,None])).astype('uint8');mask[:,a:b]=True
   for a,b in [(7,8),(61,64)]:
    profile=gaussian_filter1d(s[:,a:b,:3].mean(1).astype('float32'),1.2,axis=0,mode='nearest');assert np.array_equal(profile,np.asarray(v['averaged_source_profiles'][str(a)]));rebuilt[:,a*8:b*8,:3]=np.rint(cv2.resize(profile[:,None,:],(1,512),interpolation=cv2.INTER_LINEAR)).astype('uint8')
  assert np.array_equal(out,rebuilt) and np.array_equal(mask,np.asarray(Image.open(v['mask']))>0);assert np.array_equal(out[~mask],p[~mask]) and np.all(out[:,:,3]==255)
  if gid=='FM0282':
   exp=np.zeros((512,512),bool);exp[:,56:64]=True;exp[:,488:]=True;assert np.array_equal(out[:,:,:3].mean(2)>80,exp)
  allrows[v['id']]=v;chosen=selected.get(gid)==v['id'];checked.append({'id':v['id'],'group_id':gid,'path':v['output'],'sha256':v['output_sha256'],'source_parent_vector_mask_output_hashes_verified':True,'rgba_reproduced_from_saved_recipe':True,'outside_mask_parent_rgba_exact':True,'opaque255':True,'decision':'static_candidate' if chosen else 'not_selected','reason':reasons[gid] if chosen else 'First fixed-line material stretched one value across each row, leaving ladder-like grain beside the line; v2 corrects it.','runtime_verified':False,'release_eligible':False})
for v in hybrid['files']:
 s=arr(v['source']);p=arr(v['parent']);g=arr(v['generated_material']);out=arr(v['output']);assert hashlib.sha256(s.tobytes()).hexdigest()==v['source_rgba_sha256']
 for k in ['source_ptm','parent','generated_material','mask','output']:assert sha(v[k])==v[k+'_sha256']
 assert sha(R/v['generated_report'])==v['generated_report_sha256'];mask=np.zeros(out.shape[:2],bool)
 for a,b,c,d in v['masonry_rectangles']:mask[b*8:d*8,a*8:c*8]=True
 for a,b,c,d in v['protected_corner_rectangles']:mask[b*8:d*8,a*8:c*8]=False
 grain=g[:,:,:3].astype('float32')-gaussian_filter(g[:,:,:3].astype('float32'),(6,6,0),mode='nearest');rebuild=p.copy();material=np.rint(np.clip(p[:,:,:3].astype('float32')+np.clip(grain*v['grain_strength'],-v['grain_RGB_bound'],v['grain_RGB_bound']),0,255)).astype('uint8');rebuild[:,:,:3][mask]=material[mask]
 assert np.array_equal(out,rebuild) and np.array_equal(mask,np.asarray(Image.open(v['mask']))>0) and np.array_equal(out[~mask],p[~mask]);assert out.shape==(1024,512,4) and np.all(out[:,:,3]==255)
 checked.append({'id':v['id'],'group_id':'FM0190','path':v['output'],'sha256':v['output_sha256'],'source_parents_mask_output_hashes_verified':True,'rgba_reproduced_from_saved_recipe':True,'outside_mask_parent_rgba_exact':True,'decision':'held','reason':hold190,'new_external_calls':0,'reuses_existing_external_material':True,'runtime_verified':False,'release_eligible':False})
assert len(checked)==73 and base['actual_local_rgb_inference_passes']==60 and rew['actual_local_rgb_passes']==8
pages=[]
for name,report in reports.items():
 for v in report.get('pages',[])+report.get('initial_native_crop_pages',[]):
  assert sha(v['path'])==v['sha256'];pages.append({**v,'review_status':'directly_inspected_by_Codex_internal','evidence_report':name})
assert len(pages)==49
for v in cat['groups']:
 gid=v['group_id']
 if gid in selected or gid in holds:
  assert not v['local_sr_attempted'] and v['battle_pixel_equivalent_group'] is None;v['local_sr_attempted']=True
  if gid in selected:
   f=allrows[selected[gid]];v.update(status='static_candidate',hold_reason=None,candidate={'id':f['id'],'path':f['output'],'sha256':f['output_sha256'],'review':'qa/field_sr004_review.json','method':f.get('method','Local RGB4x +Lanczos2x, opaque alpha255'),'geometry_review':reasons[gid],'runtime_verified':False,'release_eligible':False})
  else:v.update(status='held',hold_reason=holds[gid],candidate=None)
 elif gid=='FM0190':assert v['status']=='held';v['hold_reason']=hold190
for a,b in zip(before['groups'],cat['groups']):
 if a['group_id'] not in set(base['group_ids'])|{'FM0190'}:assert a==b
assert sum(v['local_sr_attempted'] for v in cat['groups'])==125;assert sum(bool(v['candidate']) for v in cat['groups'])==86;assert sum(v['status']=='held' for v in cat['groups'])==39
stats=cat['processing_summary'];stats.update(field_novel_sources_classified=216,field_neural_originals=125,field_static_candidates=86,field_holds=39,field_groups_not_processed_in_field_context=451,remaining_novel_unprocessed=226,latest_review='qa/field_sr004_review.json')
contract['field_sr004_review']={'review':'qa/field_sr004_review.json','new_static_candidates':selected,'new_holds':holds,'source_interpretation_correction':planes['source_diagnostics']['FM0363']['interpretation'],'geometry_reconstructions':['FM0282','FM0356'],'local_retry_rejected_hypotheses':['Stronger input blur alone did not solve FM0303/0305/0336/0363 material/geometry interpretation.','A matching brightness peak count would not prove repeated physical columns or source topology.'],'scope':'Originals, whole layouts and native crops inspected. Source-coordinate support/flat-band checks do not prove runtime consumer/UV behavior.'}
contract['geometry_review003']={'review':'qa/field_sr004_review.json','remaining_hold':{'FM0190':hold190},'new_external_calls':0,'existing_external_material_reused':True,'new_neural_passes':0}
backup=R/'qa/backups/before-field-sr004-review';backup.mkdir(exist_ok=False)
for p in [cp,gp]:shutil.copy2(p,backup/p.name)
write(cp,cat);write(gp,contract)
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17);can=Image.new('RGB',(900,620),'#26333f');draw=ImageDraw.Draw(can)
for j,(gid,tag,box,label) in enumerate([('FM0282','wdn',(0,16,32,48),'판넬 세로선'),('FM0356','photo',(40,16,72,48),'배경의 평평한 띠')]):
 f=allrows[selected[gid]];src=Image.open(f['source']).convert('RGBA').crop(box).resize((256,256),Image.Resampling.NEAREST);parent=Image.open(next(v['output'] for v in base['files'] if v['id']==gid+'-'+tag)).convert('RGBA').crop(tuple(t*8 for t in box));fixed=Image.open(f['output']).convert('RGBA').crop(tuple(t*8 for t in box))
 for k,(im,title) in enumerate(zip([src,parent,fixed],['원본 · 단순 확대','로컬 AI 처리','원본 구조로 수정'])):draw.text((k*300+8,j*310+5),label+' / '+title,font=font,fill='white');can.paste(im.convert('RGB'),(k*300+8,j*310+38))
preview=R/'outputs/field-sr004/선과_평평한_면_수정_비교.png';can.save(preview);localpreview=C/'outputs/선과_평평한_면_수정_비교.png';shutil.copy2(preview,localpreview)
review={'schema':'brs-field-sr-review/v4','batch':'FIELD-SR-004 + FIELD-GEOMETRY-003','previous_goal_turn_classification':'progress: FIELD-GEOMETRY-002 resolvedFM0189 and rejected wholeFM0190 external repaint.','this_goal_turn_classification':'progress:72 new source classifications,30 new local originals,68 real RGB passes,14 static candidates,16 new holds,2 accepted source-plane protections and constrained old-GPT-material hypothesis rejected.','new_neural_unique_originals':30,'actual_local_rgb_inference_passes':68,'actual_alpha_passes':0,'native_neural_scale':4,'post_scale':'Lanczos2x','external_generative_calls':0,'image_upload':False,'derived_outputs':5,'checked_outputs':checked,'new_static_candidates':selected,'new_holds':holds,'prior_hold_updated':{'FM0190':hold190},'source_classification_corrections':{'FM0363':planes['source_diagnostics']['FM0363']['interpretation']},'source_and_comparison_pages':pages,'source_pages_directly_inspected':8,'comparison_pages_directly_inspected':41,'source_reports_sha256':{str((R/'qa'/n).relative_to(R)):sha(R/'qa'/n) for n in names},'catalog_before_sha256':base['source_catalog_sha256_before'],'catalog_after_sha256':sha(cp),'geometry_contract_before_sha256':last['geometry_contract_after_sha256'],'geometry_contract_after_sha256':sha(gp),'other545_field_groups_unchanged':True,'previous72_field_candidates_unchanged':True,'field_processing_summary':stats,'unique_neural_originals_title_battle_novel_field':382,'unique_count_basis':'Title1 +battle256 +novel field125; local retries and source-plane/GPT-material derivatives do not add unique neural originals.','protected_file_hashes':last['protected_file_hashes'],'pack_hashes':packhash,'preview':{'path':str(localpreview),'project_path':str(preview),'sha256':sha(preview)},'limits':['Source reports remain immutable; this review owns final visual status. Their original pending inference markers are historical, not a competing current decision.','All68 inputs and saved-native postprocessing reproduce exactly; GPU inference was not rerun just to claim bitwise determinism.','All5 derived recipes reproduce RGBA exactly. Source-fixed geometry and bounded masks are independent of visual acceptability; FM0190 hybrids still fail.','FM0328/329/330/333 material trials remain held pending source-facet/shaft geometry; consumer or character identity is not inferred from pixels.','FM0302/306/322 share visual motif but runtime/state linkage is unknown.','Historical57 field and241 battle candidates still need geometry-applicability review. These are static candidates, not a finished texture pack.','No new PPSSPP key, install, emulator launch, gameplay verification or final ZIP.'],'runtime_verified':False,'release_eligible':False,'all_game_complete':False,'next_action':'Reconstruct source bands/corners for heldFM0337/0346 and curved latticeFM0347; finish protected grids29/113 and perspective facades37/38. Continue novel field226, battle43 unresolved, source formats/other character-enemy-FX/cutscene coverage. FM0190 requires a changed plane-profile/joint premise, not another grain-strength retry.','scripts':{n:sha(R/'tools'/n) for n in ['prepare_field_sources03.py','field_sr004.py','inspect_rework_field_sr004.py','hybrid_field190_masonry003.py','protect_field_sr004_planes.py','refine_field282_material.py','finalize_field_sr004.py']}}
for rel,h in last['protected_file_hashes'].items():assert sha(R/rel)==h
assert {str(p.relative_to(pack)):sha(p) for p in pack.rglob('*') if p.is_file()}==packhash
write(Q,review)
with (R/'PROGRESS.md').open('a',encoding='utf8') as f:f.write('''

## 2026-09-23 — FIELD-SR-004 / 원본 선·면 보호 및 다음 배경 묶음
- 이번 goal turn은 progress. 신규 source72종/8페이지 직접 분류하여 누계216. 불투명30종 WDN/Photo60 RGB추론 +FM0303/0305/0336/0363 WDN.65/general.35 재작업8 = 실제 로컬68회. 새 원본30종, 새 외부 호출/업로드0. 로컬native4x 후Lanczos2x임을 구분.
- 전체15·native10·재작업4 페이지 직접 검수. FM0303 과도한 미세균열,0305 나이테 흐림/과장,0336 균열/세로선,0363 중앙선 해석은 네 조건 모두 최종 채택하지 않음. 0363원본 자체x30 어두운 선과 외곽 테두리 확인; 기존 자연재질 분류의 한계는 최종 review에서 정정하고 해시로 묶인 원본분류 기록은 유지.
- 원본 좌표 직접 보호3파생: FM0282세로선x7..8/61..64 고정, v1은 주변 재질을 행별로 늘여 가로 줄무늬가 생겨 제외. v2 인접 로컬 재질 조각+4px 접합으로 수정 후 채택. threshold80 밝은 지지영역 모든 행 동일. FM0356 원본RGB115/93/74 평면[0,4,128,18] 그대로, y25..33 로컬Photo에 연결,33아래RGBA동일. 두 최종 후보; 새 AI추론 아님. 비교6페이지 직접 검수.
- FM0190 과거 GPT생성 재질 고주파만 고정cornice안 strength.45/±8,.75/±12 2파생/6페이지 모두검수. mask밖·darkcorner·glassRGBA 그대로여도 cornice접합의 붙임판/둥근느낌 해결안됨. 둘 보류. 재질grain만으로 해결한다는 가설 제외, 다음은 원본 면 단면/접합음영 해석 변경 필요. 새 외부호출0이며 기존 외부재질 재사용을 전부로컬이라 부르지 않음.
- 신규14 후보: Photo276/297/302/306/307/313/322, WDN277/280/286/304/315, 직접보호282v2/356. 신규16 보류:275/303/305/328/329/330/332/333/334/336/337/338/345/346/347/363. 기계atlas328/329/330/333은 재질이 나아도 facet/shaft 원본선anchor미확정이라보류. 332작은무늬가 가짜글자로 바뀜. 347원래곡선을마름모로바꾸지않음. 346명암면이검은틈/가는막대로해석되는오류. 밝기profile peaks는 실제기둥개수증거아님.
- 전체73출력 =68로컬+직접면3+기존GPT재질2. 원본PTM/RGBA,model/input/native/output/부모/vector/mask SHA 및입력/저장native후처리/5파생RGBA재현 확인. 소스8+비교41=49페이지 직접검수. authoritative qa/field_sr004_review.json. raw추론report의pending은이최종review로판정; 바인딩해시유지를위해raw기록불변.
- 현재field125neural/86정적후보/39보류/novel미처리226. source분류216/351. title1+battle256+field125=고유neural382. 기존72후보,다른545fieldgroup,전투241후보17보류26미처리,20key팩/보호파일보존. 과거57field/241battlegeometry적용여부대기. 설치/실게임검수/최종ZIP 미완료, 전체목표active.
- 다음 FM0337/0346원본반복띠·0347곡선격자,29/113격자·37/38원근건물,잔여field226·전투43와기타캐릭터적효과컷신범위. FM0190grain강도반복중단. GUI복구증거없으므로검은캡처반복/컴퓨터유즈실행없음. 사용자비교 outputs/선과_평평한_면_수정_비교.png.
''')
with (C/'outputs/로컬_업스케일_진행.md').open('a',encoding='utf8') as f:f.write('''

## 배경 30종 추가 검수와 원본 선·면 수정 — FIELD-SR-004
- 30종을 로컬 모델로 비교하고 문제 4종을 재처리했습니다. 실제 로컬 추론68회, 새 외부 생성0회입니다.
- 14종을 파일 검수 후보로 남겼고 16종은 구조·무늬·균열 과장 문제로 보류했습니다. 판넬 세로선과 배경의 평평한 띠 2종은 원본 좌표로 직접 수정했습니다.
- 현재 필드86종 후보/39종 보류/226종 미처리입니다. 전투43종과 나머지 대상 조사, 실제 게임 적용 검수 및 최종 배포도 남았습니다. 전체 완료율·완료 시각은 아직 확정하지 않았습니다.
''')
print(json.dumps({'checked_outputs':len(checked),'pages_directly_inspected':len(pages),'new_candidates':len(selected),'new_holds':len(holds),'local_rgb_passes':68,'field_summary':stats,'user_preview':str(localpreview)},ensure_ascii=False))
