"""Consolidate actual visual decisions, reproducibility and protected-file checks."""
from pathlib import Path
import json,hashlib,copy,shutil,xml.etree.ElementTree as ET
import numpy as np,cv2
from scipy.ndimage import gaussian_filter,gaussian_filter1d
from PIL import Image,ImageFilter,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];C=Path(r'C:\Users\CadriacLord\Documents\Codex\2026-09-22\brs-hd-ui-fonts');Q=R/'qa/field_sr005_review.json';assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text('utf8'))
def write(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2),'utf8')
def arr(p):return np.asarray(Image.open(p).convert('RGBA'))
last=read(R/'qa/field_geometry006_review.json');names=['field_source_review04.json','field_sr005_inference.json','field_sr005_native_review.json','field_sr005_rework.json','field_sr005_geometry502.json','field_sr005_geometry502_v2.json','field_sr005_alpha_review.json'];reports={n:read(R/'qa'/n) for n in names};src,base,native,rew,g1,g2,matte=[reports[n] for n in names]
cp=R/'qa/field_sr_catalog.json';gp=R/'qa/architectural_geometry_contract.json';cat=read(cp);before=copy.deepcopy(cat);contract=read(gp)
assert sha(cp)==last['catalog_after_sha256']==base['source_catalog_sha256_before']==src['catalog_before_sha256'];assert sha(gp)==last['geometry_contract_after_sha256']==base['geometry_contract_sha256_before']
assert base['source_review_sha256']==sha(R/'qa/field_source_review04.json');assert all(r['inference_report_sha256']==sha(R/'qa/field_sr005_inference.json') for r in [native,matte]);assert rew['base_report_sha256']==sha(R/'qa/field_sr005_inference.json');assert g2['previous_geometry_report_sha256']==sha(R/'qa/field_sr005_geometry502.json')
for rel,h in last['protected_file_hashes'].items():assert sha(R/rel)==h
pack=R/'workspace/local-sr/observed-review-pack-v2/PSP/TEXTURES/NPUH10126';packhash={str(p.relative_to(pack)):sha(p) for p in pack.rglob('*') if p.is_file()};assert packhash==last['pack_hashes']
for v in before['groups']:
 if v['candidate']:assert sha(v['candidate']['path'])==v['candidate']['sha256']
# Full decoded-novel source routing, explicitly not a whole-game denominator.
routed=set()
for n in ['field_source_review01.json','field_source_review02.json','field_source_review03.json','field_source_review04.json']:
 d=read(R/'qa'/n)
 for v in d['files']:
  assert v['group_id'] not in routed;routed.add(v['group_id']);assert sha(v['source_ptm'])==v['source_ptm_sha256'];assert hashlib.sha256(arr(v['source']).tobytes()).hexdigest()==v['source_rgba_sha256']
assert len(routed)==351;assert len(src['files'])==135;assert all(v['source_review']=='directly_inspected_by_Codex_internal' for v in src['files'])
chosen={424:'photo',480:'wdn',486:'wdn',494:'wdn',499:'wdn',506:'wdn'};selected={f'FM{k:04d}':f'FM{k:04d}-{v}' for k,v in chosen.items()};selected['FM0502']=g2['id']
holds={
 'FM0391':'Faceted plate atlas, not free folded material. Long diagonal edges and acute tips remain subtly bowed/rounded. Source segment anchors and small holes/seams need protected reconstruction.',
 'FM0396':'Angular metal/plate atlas. Native crops show softened corners and curved bevel paths; reconstruct intended straight segments while preserving source intentional arcs.',
 'FM0407':'Panel facets and stepped inset seams need source-anchored construction. A sharper Photo edge alone does not establish corner/segment fidelity.',
 'FM0456':'Weathered masonry: Photo clarifies blocks but source joint paths and chipped boundaries need separation; WDN makes stronger granular cracks. No source-defined joint geometry accepted yet.',
 'FM0465':'Photo invents/emphasizes thin continuous mortar strokes while WDN obscures them. Separate original block joints from dirt and fractures before direct geometry treatment.',
 'FM0466':'Low-contrast masonry cues are present; prior natural-only routing was too broad. Photo turns faint transitions into dark long joints/cracks; WDN retains grain but does not establish joint geometry.',
 'FM0473':'Source shows brick courses behind broad diagonal fracture/vein-like features, not only a random veined material. Models impose differing block-joint and crack detail; preserve both source layout and broken parts.',
 'FM0476':'Mixed masonry/edge and coarse aggregate atlas, not one homogeneous striated material. Upper courses/edge require source boundaries; lower aggregate textures differ strongly between priors.',
 'FM0495':'Regular block masonry. Mortar paths still bow and intersections shift at native scale; source joint anchors/straight segments must be authored before acceptance.',
 'FM0496':'Long cornice bands and slab joints need source fixed cross-sections/anchors. Both local priors round the band edges and introduce uneven surface profiles.',
 'FM0518':'Grayscale shading/region atlas needs consumer-aware ramp treatment. Local models smooth some contours but add strong material-like surfaces and line detail; preserve source region boundaries and tonal function.',
 'FM0525':'Repeating carpet/ornamental motifs and narrow border markings change between priors. Anime retry flattens surface and redraws motif interiors; no model output accepted. Direct motif reconstruction required.',
 'FM0533':'Salmon drapery/panel shading is usable only as a future donor. Both Photo and Anime thicken the original white curled ornament; WDN blurs it. Needs source-defined thin scroll curves/border without imposing symmetry.'}
assert len(holds)==13 and len(selected)==7 and set(selected)|set(holds)==set(base['group_ids'])
reasons={
 'FM0424':'Photo retains the coarse irregular pitted stone/masonry surface and broad dark patch arrangement with less fine scratching than WDN. No precise rigid joint grid established in this crop; chipped edges remain intentionally irregular.',
 'FM0480':'WDN keeps a finer cracked mineral surface than Photo, which widens and deepens fissures. Original nearopaque alpha is resized separately; no neural alpha inference.',
 'FM0486':'WDN retains finer original crack-network appearance than Photo with less exaggerated rough relief. Similar appearance to480/506 does not establish shared consumer or equivalence.',
 'FM0494':'WDN preserves softer pale veins and granular gray base; Photo hardens veins into white strokes. Nearopaque source alpha is independent of RGB inference.',
 'FM0499':'WDN preserves soft mottled/cloud-like gray color shapes without adding strong new cracks or a rigid material identity. Photo makes several shape boundaries harder.',
 'FM0502':'Fixed source strip/corner regions and median source color cross-sections keep border lines straight; interpolation removes v1 flat step bands. Local Photo interior remains unchanged, including weathered patch. Source surface interpretation remains visual, not native material metadata.',
 'FM0506':'WDN preserves finer gray crack appearance with less deep black separation than Photo. Original nearopaque alpha is resized separately; not assumed equivalent to480/486.'}
corrections={
 'FM0391':'Source routing should be protected faceted mechanical atlas rather than generic folded material.',
 'FM0396':'Source routing should be protected angular plate/mechanical atlas rather than generic folded material.',
 'FM0466':'Low-contrast masonry lines visible on close review; revise natural-only routing to structured weathered masonry.',
 'FM0473':'Brick courses and large diagonal damaged features coexist; do not route as only irregular natural veins.',
 'FM0476':'Upper masonry and lower coarse aggregate are separate regions; original natural-striation routing is insufficient.',
 'FM0518':'Treat broad grayscale fields as protected shading/region atlas with unknown consumer, not generic material grain.'}
checked=[];allrows={};modelhashes={};alpha_diagnostics={}
for v in base['files']+rew['files']:
 s=Image.open(v['source']).convert('RGBA');o=Image.open(v['output']).convert('RGBA');assert hashlib.sha256(s.tobytes()).hexdigest()==v['source_rgba_sha256'];assert sha(v['source_ptm'])==v['source_ptm_sha256']
 model=v['model'];modelhashes.setdefault(model['path'],sha(model['path']));assert modelhashes[model['path']]==model['sha256']
 for key in ['input','native','output']:assert sha(v[key])==v[key+'_sha256']
 inp=s.convert('RGB').filter(ImageFilter.GaussianBlur(v['input_gaussian_sigma_source_px']));assert np.array_equal(np.asarray(inp),np.asarray(Image.open(v['input'])))
 n=Image.open(v['native']).convert('RGB');assert n.size==(s.width*4,s.height*4) and o.size==(s.width*8,s.height*8)
 expected=n.resize(o.size,Image.Resampling.LANCZOS).convert('RGBA');alpha=s.getchannel('A').resize(o.size,Image.Resampling.BILINEAR);expected.putalpha(alpha);assert np.array_equal(np.asarray(expected),np.asarray(o))
 if s.getchannel('A').getextrema()[0]<255:
  aa=np.asarray(alpha);sa=np.asarray(s.getchannel('A'));alpha_diagnostics[v['group_id']]={'source_extrema':list(s.getchannel('A').getextrema()),'output_extrema':list(alpha.getextrema()),'source_alpha_mean':float(sa.mean()),'output_alpha_mean':float(aa.mean()),'mean_ratio':float(aa.mean()/sa.mean()),'exact_recipe':'Source alpha BILINEAR8x; RGB neural only','game_alpha_behavior_verified':False}
 allrows[v['id']]=v;checked.append({'id':v['id'],'group_id':v['group_id'],'path':v['output'],'sha256':v['output_sha256'],'source_model_input_native_output_hashes_verified':True,'saved_input_prefilter_and_native_postprocess_exact':True,'inference_repeated_for_validation':False,'alpha_recipe_verified':True,'decision':'static_candidate' if selected.get(v['group_id'])==v['id'] else 'held' if v['group_id'] in holds else 'not_selected','reason':holds.get(v['group_id'],reasons.get(v['group_id'])),'runtime_verified':False,'release_eligible':False})
geometry_diagnostics={}
for version,v in [(1,g1),(2,g2)]:
 s=arr(v['source']);p=arr(v['parent']);o=arr(v['output']);rebuilt=p.copy();mask=np.asarray(Image.open(v['mask']).convert('RGBA'))[:,:,3]>0
 for key in ['source_ptm','parent','output','vector','mask']:assert sha(v[key])==v[key+'_sha256']
 assert hashlib.sha256(s.tobytes()).hexdigest()==v['source_rgba_sha256'];assert o.shape==(256,1024,4);rects=list(ET.parse(v['vector']).getroot().iter('{http://www.w3.org/2000/svg}rect'));assert len(rects)==4
 expectedmask=np.zeros((256,1024),bool)
 for element,(x,y,w,h) in zip(rects,v['rectangles_xywh_source']):
  assert [float(element.attrib[t]) for t in ['x','y','width','height']]==[x,y,w,h];assert not any(t in element.attrib for t in ['rx','ry','transform']);expectedmask[y*8:(y+h)*8,x*8:(x+w)*8]=True
 assert np.array_equal(mask,expectedmask)
 if version==1:
  for profile,y0 in [(gaussian_filter1d(s[:5,:,:3].astype('float32'),.6,axis=1,mode='nearest'),0),(gaussian_filter1d(s[30:,:,:3].astype('float32'),.6,axis=1,mode='nearest'),30)]:
   for j,row in enumerate(profile):rebuilt[(y0+j)*8:(y0+j+1)*8,:,:3]=np.rint(cv2.resize(row[None,:,:],(1024,1),interpolation=cv2.INTER_LINEAR)[0]).astype('uint8')[None,:,:]
  for profile,x0 in [(gaussian_filter1d(s[:,0:2,:3].astype('float32'),.6,axis=0,mode='nearest'),0),(gaussian_filter1d(s[:,126:128,:3].astype('float32'),.6,axis=0,mode='nearest'),126)]:
   for j in range(2):rebuilt[40:240,(x0+j)*8:(x0+j+1)*8,:3]=np.rint(cv2.resize(profile[:,j:j+1,:],(1,256),interpolation=cv2.INTER_LINEAR)[40:240,0,:]).astype('uint8')[:,None,:]
 else:
  grain=np.clip((p[:,:,:3].astype('float32')-gaussian_filter(p[:,:,:3].astype('float32'),(1.25,1.25,0),mode='nearest'))*.25,-1,1)
  profiles={'top':np.median(s[:6,2:126,:3],axis=1).tolist(),'bottom':np.median(s[29:,2:126,:3],axis=1).tolist(),'left':np.median(s[5:30,:3,:3],axis=0).tolist(),'right':np.median(s[5:30,125:,:3],axis=0).tolist()};assert profiles==v['source_profiles_rgb']
  for key,a,b,origin in [('top',0,40,0),('bottom',240,256,29)]:
   profile=np.array(profiles[key]);ys=(np.arange(a,b)+.5)/8;vals=np.stack([np.interp(ys,np.arange(origin,origin+len(profile))+.5,profile[:,c]) for c in range(3)],1);rebuilt[a:b,:,:3]=np.rint(np.clip(vals[:,None,:]+grain[a:b],0,255)).astype('uint8')
  for key,a,b,origin in [('left',0,16,0),('right',1008,1024,125)]:
   profile=np.array(profiles[key]);xs=(np.arange(a,b)+.5)/8;vals=np.stack([np.interp(xs,np.arange(origin,origin+len(profile))+.5,profile[:,c]) for c in range(3)],1);rebuilt[40:240,a:b,:3]=np.rint(np.clip(vals[None,:,:]+grain[40:240,a:b],0,255)).astype('uint8')
  # Along any protected straight strip, only the declared bounded grain varies.
  spreads={'top_RGB_max_spread_along_x':int(np.ptp(o[:40,:,:3].astype(int),axis=1).max()),'bottom_RGB_max_spread_along_x':int(np.ptp(o[240:,:,:3].astype(int),axis=1).max()),'left_RGB_max_spread_along_y':int(np.ptp(o[40:240,:16,:3].astype(int),axis=0).max()),'right_RGB_max_spread_along_y':int(np.ptp(o[40:240,1008:,:3].astype(int),axis=0).max())};assert max(spreads.values())<=2;geometry_diagnostics={'rectangles_xywh_source':v['rectangles_xywh_source'],'protected_pixels':int(mask.sum()),'cross_section_spreads':spreads,'limit':'Fixed decoded-image border section; no proof of native UV seams or full consumer geometry.'}
 assert np.array_equal(o,rebuilt);assert np.array_equal(o[~mask],p[~mask]);assert np.array_equal(o[:,:,3],p[:,:,3]);allrows[v['id']]=v
 checked.append({'id':v['id'],'group_id':'FM0502','path':v['output'],'sha256':v['output_sha256'],'source_parent_vector_mask_output_hashes_verified':True,'rgba_reproduced_from_source_recipe':True,'outside_mask_parent_RGBA_exact':True,'alpha_parent_exact':True,'decision':'static_candidate' if version==2 else 'not_selected','reason':reasons['FM0502'] if version==2 else 'v1 straight strips were visible flat shade blocks; v2 interpolates the source transverse section.','runtime_verified':False,'release_eligible':False})
assert len(checked)==44 and base['actual_local_rgb_inference_passes']==40 and rew['actual_local_rgb_inference_passes']==2
pages=[]
for name,report in reports.items():
 for v in report.get('pages',[]):
  assert sha(v['path'])==v['sha256'];pages.append({**v,'review_status':'directly_inspected_by_Codex_internal','evidence_report':name})
coordinate=R/'outputs/field-sr005/FM0533-source-coordinate.png';pages.append({'path':str(coordinate),'sha256':sha(coordinate),'review_status':'directly_inspected_by_Codex_internal','kind':'source_coordinate_plate'})
assert len(pages)==47
for g in cat['groups']:
 gid=g['group_id']
 if gid not in selected and gid not in holds:continue
 assert not g['local_sr_attempted'] and g['battle_pixel_equivalent_group'] is None and g['status']=='not_processed_in_field_context';g['local_sr_attempted']=True
 if gid in selected:
  v=allrows[selected[gid]];g.update(status='static_candidate',hold_reason=None,candidate={'id':v['id'],'path':v['output'],'sha256':v['output_sha256'],'review':'qa/field_sr005_review.json','method':v.get('method','Local RGB4x +Lanczos2x; source alpha BILINEAR8x independent'),'geometry_review':reasons[gid],'runtime_verified':False,'release_eligible':False})
 else:g.update(status='held',hold_reason=holds[gid],candidate=None)
for a,b in zip(before['groups'],cat['groups']):
 if a['group_id'] not in set(base['group_ids']):assert a==b
assert sum(g['local_sr_attempted'] for g in cat['groups'])==145;assert sum(bool(g['candidate']) for g in cat['groups'])==100;assert sum(g['status']=='held' for g in cat['groups'])==48;assert sum(g['status']=='not_processed_in_field_context' for g in cat['groups'])==428
stats=cat['processing_summary'];stats.update(field_novel_sources_classified=351,field_neural_originals=145,field_static_candidates=100,field_holds=48,field_groups_not_processed_in_field_context=428,remaining_novel_unprocessed=203,field_direct_gpt_only_originals=3,field_processed_novel_originals_all_routes=148,latest_review='qa/field_sr005_review.json',counting_note='Legacy field_neural_originals counts145 originals with actual local inference; direct-GPT-only3 are separate. All processed novel148=145+3. New batch20 originals and42 real RGB calls; retries/geometry derivatives do not add unique originals.')
contract['field_sr005_review']={'review':'qa/field_sr005_review.json','new_static_candidates':selected,'new_holds':holds,'source_routing_corrections':corrections,'geometry_reconstruction':'FM0502 source fixed border v2; v1 shade blocks rejected','pattern_retry':'Local anime6B tested525/533; both rejected. Change to source-owned ornament curves/motifs instead of another blind prior sweep.','alpha_policy':'Nearopaque480/494/506 exact source BILINEAR8x alpha, no neural alpha. Runtime alpha behavior unknown.','new_local_passes':42,'new_external_calls':0,'runtime_verified':False,'release_eligible':False};contract['current_batch_geometry_holds'].update(holds)
backup=R/'qa/backups/before-field-sr005-review';backup.mkdir(exist_ok=False)
for p in [cp,gp]:shutil.copy2(p,backup/p.name)
write(cp,cat);write(gp,contract)
# Compact user artifact uses one mineral material and the native border crop.
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18);can=Image.new('RGB',(900,660),'#25313c');draw=ImageDraw.Draw(can)
for row,(gid,box,label) in enumerate([('FM0480',(12,12,44,44),'균열이 있는 석재'),('FM0502',(44,0,76,32),'패널의 직선 테두리')]):
 v=allrows[selected[gid]];source=Image.open(v['source']).convert('RGBA').crop(box).resize((256,256),Image.Resampling.NEAREST);bad=next(z for z in base['files'] if z['id']==gid+'-photo');ims=[source,Image.open(bad['output']).convert('RGBA').crop(tuple(x*8 for x in box)),Image.open(v['output']).convert('RGBA').crop(tuple(x*8 for x in box))]
 for col,(im,title) in enumerate(zip(ims,['원본 · 단순 확대','로컬 Photo 비교','선택 후보'])):
  draw.text((col*300+9,row*330+8),label,font=font,fill='white');draw.text((col*300+9,row*330+34),title,font=font,fill='#d4dce4');bg=Image.new('RGB',im.size,'#414951');bg.paste(im,(0,0),im);can.paste(bg,(col*300+20,row*330+67))
preview=R/'outputs/field-sr005/재질과_직선_검수_비교.png';can.save(preview);localpreview=C/'outputs'/preview.name;shutil.copy2(preview,localpreview)
review={'schema':'brs-field-sr-review/v5','batch':'FIELD-SR-005','previous_goal_turn_classification':'progress: geometry006 added3 direct-GPT-only field candidates and advanced atlas29; whole29 still held.','this_goal_turn_classification':'progress: remaining135 novel sources classified,20 new local originals/42 actual RGB calls reviewed,7 static candidates and13 holds, source border502 corrected.','new_neural_unique_originals':20,'actual_local_rgb_inference_passes':42,'actual_alpha_passes':0,'external_generative_calls':0,'image_upload':False,'native_neural_scale':4,'final_scale':8,'post_scale':'Lanczos2x','checked_outputs':checked,'new_static_candidates':selected,'new_holds':holds,'selection_reasons':reasons,'source_routing_corrections':corrections,'alpha_diagnostics':alpha_diagnostics,'geometry_diagnostics':geometry_diagnostics,'source_and_comparison_pages':pages,'source_pages_directly_inspected':15,'additional_source_coordinate_pages':1,'comparison_pages_directly_inspected':31,'source_reports_sha256':{str((R/'qa'/n).relative_to(R)):sha(R/'qa'/n) for n in names},'catalog_before_sha256':base['source_catalog_sha256_before'],'catalog_after_sha256':sha(cp),'geometry_contract_before_sha256':base['geometry_contract_sha256_before'],'geometry_contract_after_sha256':sha(gp),'other556_field_groups_unchanged':True,'previous93_field_candidates_unchanged':True,'field_processing_summary':stats,'unique_local_neural_originals_title_battle_novel_field':402,'unique_processed_originals_including_direct_GPT_only_title_battle_novel_field':405,'protected_file_hashes':last['protected_file_hashes'],'pack_hashes':packhash,'preview':{'path':str(localpreview),'project_path':str(preview),'sha256':sha(preview)},'runtime_verified':False,'release_eligible':False,'all_game_complete':False,'limits':['351 source classifications complete only the decoded novel field routing population;225 battle-pixel-equivalent field groups, undecoded assets, consumers and other game populations remain separate.','Some initial appearance labels were too broad; final routing corrections are explicit here, while source-linked inference reports remain immutable.','42 actual local RGB calls:40 WDN/Photo plus2 anime6B pattern retries. Both pattern retries rejected. No external generation this batch.','All saved input/native postprocessing and2 geometry recipes reproduce exactly; CUDA inference was not unnecessarily repeated.','Alpha on3 nearopaque textures matches source bilinear8x exactly; it is not byte-exact source texels or game alpha-test evidence.','Static candidates only. Historical57 field/241 battle geometry-applicability checks,48 current field holds,203 novel unprocessed and43 battle unresolved remain.','No installation, new observed PPSSPP keys, emulator launch, actual-game verification or final release ZIP.'],'next_action':'Prioritize source-defined masonry joints456/465/466/473/495 and straight cornice496, thin ornament533 and motifs525; finish atlas29 and perspective facades37/38. Continue remaining203 novel field and43 battle plus other game populations. Keep direct-GPT glass policy and material-vs-geometry separation. Runtime only when GUI recovery is evidenced, never Computer Use launch.','scripts':{n:sha(R/'tools'/n) for n in ['prepare_field_sources04.py','classify_field_sources04.py','field_sr005.py','inspect_field_sr005.py','rework_field_sr005.py','protect_field502.py','refine_field502.py','inspect_field_sr005_alpha.py','finalize_field_sr005.py']}}
for rel,h in last['protected_file_hashes'].items():assert sha(R/rel)==h
assert {str(p.relative_to(pack)):sha(p) for p in pack.rglob('*') if p.is_file()}==packhash
write(Q,review)
with (R/'PROGRESS.md').open('a',encoding='utf8') as f:f.write('''

## 2026-09-23 — FIELD-SR-005 / 남은 원본 분류·재질과 직선 검수
- 이전geometry006은progress. 이번도신규20로컬원본/7정적후보로progress,전체목표active. 남은135source/15페이지직접분류하여decoded novel field351 routing완료. 전체게임분모나225battle픽셀동일소비자검증완료아님.
- WDN/Photo20종40실제RGBpass,525/533 Anime6B.25추가2pass 모두불채택. 총42실제local RGB추론/새외부0. native4x후Lanczos2x. nearopaque480/494/506alpha는sourceBILINEAR8x정확별도,alpha추론0.
- 처음 folded/material로넓게분류한391/396은각진부품atlas,466은희미한masonry,473은벽돌+대각파손,476은masonry/aggregate혼합,518은grayscale shading/region으로최종review정정. 원본분류/추론의바인딩해시기록은불변.
- 신규7후보: Photo424,WDN480/486/494/499/506,502직접border v2. 신규13보류391/396/407/456/465/466/473/476/495/496/518/525/533. 흐린원본단서를줄눈/장식으로임의강조한결과나더선명하지만휘는부품선은불채택.
- 502source top/bottom/side4rect mask로띠구조보호. v1rowshade가평평한블록이라불채택;v2원본texelcenter median단면선형보간+localhighfreq±1 RGB만사용. mask밖/alpha부모정확,모든선길이방향RGB변동최대2,두recipe RGBA재현. 원본색/띠단면검사이지UV/실게임증거아님.
- 전체44출력=42local+geometry2. source351PTM/RGBA,3model/input/native/output,vector/mask/parent/replaySHA검사. source15+좌표1+비교31=47페이지직접검수. 3nearopaque는양배경검수/원본alpha별도보존,source/outputalpha평균차기록. 최종qa/field_sr005_review.json.
- 현재field100정적후보/48보류/novel203미처리,local145+directGPT-only3=148처리. 소비문맥미처리428에는battle픽셀동일225포함. title1+battle256+novelfield145=402고유local,외부전용포함405. 기존93후보/다른556fieldgroup/전투241후보17보류26미처리/20key팩과원본보호파일보존.
- 사용자완료시간질문에는아직상당한작업/직접수정과실게임검수잔여를설명,전체완료율·ETA확답안함. 설치/실게임/최종ZIP미완료,GUI복구증거없어에뮬실행/검은캡처반복없음.
- 다음새보류masonry줄눈/496cornice/533얇은scroll/525motif 직접구성,29/37/38등기존구조보류,field203/전투43/기타인물적효과컷신/미지원원본범위. outputs/field-sr005/재질과_직선_검수_비교.png.
''')
with (C/'outputs/로컬_업스케일_진행.md').open('a',encoding='utf8') as f:f.write('''

## 배경20종 추가 검수 — FIELD-SR-005
- 로컬모델실제추론42회와직접테두리수정2안검수. 7종을파일검수후보로남기고13종은줄눈·부품·장식형태문제로보류했습니다. 이번묶음새외부생성0회입니다.
- 현재필드후보100종,재작업보류48종,미처리203종입니다. 전투43종과다른게임대상조사,실게임검수·최종배포도남아있습니다. 전체완료시각은아직확정할수없습니다.
- 원본분류351종완료는현재해독된신규필드범위의분류완료이며전체게임완성이아닙니다. 패널테두리는원본위치·명암으로재구성했고재질표면은로컬결과를보존했습니다.
''')
print(json.dumps({'checked_outputs':44,'new_candidates':7,'new_holds':13,'local_RGB_passes':42,'pages_directly_inspected':47,'field_summary':stats,'alpha':alpha_diagnostics,'geometry':geometry_diagnostics,'preview':str(localpreview)},ensure_ascii=False))
