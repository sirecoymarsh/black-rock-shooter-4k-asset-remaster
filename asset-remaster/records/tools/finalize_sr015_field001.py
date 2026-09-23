"""Finalize inspected trials, verify provenance, preserve installed/review packs."""
import json,hashlib,shutil
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy.signal import find_peaks
R=Path(__file__).resolve().parents[1];C=Path('C:/Users/CadriacLord/Documents/Codex/2026-09-22/brs-hd-ui-fonts')
assert not (R/'qa/local_sr015_review.json').exists() and not (R/'qa/field_sr001_review.json').exists()
def read(p):return json.loads((R/p).read_text('utf8'))
def save(p,v):(R/p).write_text(json.dumps(v,ensure_ascii=False,indent=2),'utf8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def img(p):return Image.open(p).convert('RGBA')
def raw(im):return hashlib.sha256(im.tobytes()).hexdigest()
def check(p,h):assert sha(p)==h,str(p)
previous=read('qa/local_sr014_review.json');protected=previous['protected_file_hashes'];pack=Path(read('qa/local_sr_observed_review_pack_v2.json')['path'])
for p,h in protected.items():check(R/p,h)
assert previous['pack_hashes']=={str(p.relative_to(pack)):sha(p) for p in pack.rglob('*') if p.is_file()}
cat=read('qa/battle_sr_catalog.json');bm=next(g for g in cat['groups'] if g['group_id']=='BM201');assert not bm['candidate']
backup=R/'qa/backups/before-sr015-field001-review';backup.mkdir(parents=True,exist_ok=False)
names=['local_sr015_gpt_floor.json','local_sr015_small_repair.json','local_sr015_small_texture.json','local_sr015_small_texture_v3.json']
reports={n:read('qa/'+n) for n in names};floor=reports[names[0]];checks=[]
for n,rep in reports.items():
 shutil.copyfile(R/'qa'/n,backup/n)
 for v in rep['files']:
  s=img(v['source']);o=img(v['output']);assert raw(s)==v['source_rgba_sha256']==bm['rgba_sha256'];check(bm['representative']['source'],bm['representative']['source_sha256'])
  for k in ['generated','parent','mask','underlay','source_fragment_mask','output']:
   if k in v:check(v[k],v[k+'_sha256'])
  assert o.size==(s.width*8,s.height*8)==tuple(v['output_size']) and o.getchannel('A').getextrema()==(255,255)
  outside=None
  if 'mask' in v:
   m=np.asarray(Image.open(v['mask']).convert('L'))>0;b=np.asarray(img(v['parent']));a=np.asarray(o);outside=int(np.max(np.abs(a.astype(int)-b.astype(int))[~m]));assert outside==0
  if n==names[0]:status='held';reason='Sampled checker phase and edges improve, but wear/crack interpretation is stronger than the source, especially the small bottom-right patch. Source already has dark crack fragments; do not erase legitimate source damage.'
  elif n==names[1]:status='rejected';reason='Inpainted narrow crack corridor leaves blurry fills/halos; seven strong source pixels do not establish the full original crack.'
  else:status='rejected';reason='Same-cell material restoration still leaves visible patches or blur. Luminance filters do not prove enclosing-rim exclusion.'
  if n==names[3]:
   for d in v['donor_cells']:
    d.pop('no_other_cell_or_enclosing_rim_donors',None);d.update(donor_cell_restriction_verified=True,luminance_role_filter_applied=True,rim_exclusion_proven=False)
  v['visual_review']={'reviewer':'Codex internal','status':status,'reason':reason};checks.append({'id':v['id'],'decision':status,'source_ptm_rgba_and_output_parent_mask_hashes_verified':True,'size8x_alpha255_verified':True,'outside_mask_max_rgba_difference':outside})
 rep['review_status']='Finalized; no accepted BM201 replacement. See local_sr015_review.json.';save('qa/'+n,rep)
assert len(checks)==6
check(floor['prompt_file'],floor['prompt_sha256']);check(floor['raw_generated']['path'],floor['raw_generated']['sha256']);assert img(floor['raw_generated']['path']).size==(1254,1254)
contrast=[];patches=next(v for v in read('qa/local_sr014_reconstruction.json')['files'] if v['id']=='BM201-cells-0.6')['patches']
for v in floor['files']:
 s=img(v['source']);a=np.asarray(s.convert('RGB'),float).mean(2);b=np.asarray(img(v['output']).convert('RGB').resize(s.size,Image.Resampling.LANCZOS),float).mean(2)
 for p in patches:
  vals={}
  for c in p['cells']:
   if c['source_samples']<25:continue
   x0,y0,x1,y1=c['source_bounds'];x=int((x0+x1)/2);y=int((y0+y1)/2);vals[(c['column'],c['row'])]=(float(a[y-1:y+2,x-1:x+2].mean()),float(b[y-1:y+2,x-1:x+2].mean()))
  n=bad=0
  for xy,pair in vals.items():
   for z in [(xy[0]+1,xy[1]),(xy[0],xy[1]+1)]:
    if z not in vals:continue
    ds=vals[z][0]-pair[0];do=vals[z][1]-pair[1]
    if abs(ds)>=10:n+=1;bad+=int(ds*do<=0)
  contrast.append({'id':v['id'],'patch':p['id'],'strong_adjacent_pairs':n,'sign_reversals':bad})
for v in floor['files']:
 assert sum(d['strong_adjacent_pairs'] for d in contrast if d['id']==v['id'])==254
 assert sum(d['sign_reversals'] for d in contrast if d['id']==v['id'])==0
edge=read('qa/local_sr015_edge_audit.json');check(edge['candidate'],edge['candidate_sha256']);assert raw(img(edge['source']))==edge['source_rgba_sha256'];assert sum(len(p['samples']) for p in edge['patches'])==207
evidence=[f'outputs/sr015-BM201-initial-{n}.png' for n in range(6)]+[f'outputs/sr015-BM201-small-repair-{n}.png' for n in range(2)]+['outputs/sr015-BM201-small-texture-0.png','outputs/sr015-BM201-small-texture-v3.png','outputs/sr015-small-coordinates.png']
sr15={'schema':'brs-local-sr-review/v15','batch':'LOCAL-SR-015','checked_outputs':checks,'new_actual_local_neural_passes':0,'external_generative_calls':1,'external_tool':'built-in image_gen; model identifier not exposed','image_upload':True,'new_unique_originals':0,'derived_outputs':6,'accepted_candidates':{},'held':['BM201'],'source_adjacent_contrast':contrast,'contrast_limit':'3x3 source-coordinate center averages from cells with >=25 source samples; difference >=10. Not all-cell geometry, exact HD detail, or native UV proof.','edge_samples':207,'edge_audit_path':'qa/local_sr015_edge_audit.json','edge_audit_sha256':sha(R/'qa/local_sr015_edge_audit.json'),'edge_fit_applied':False,'metadata_correction':'v3 rim-exclusion claim removed; same-cell sampling and luminance filtering do not prove semantic rim exclusion.','review_evidence':[{'path':str(R/p),'sha256':sha(R/p),'directly_inspected':True} for p in evidence],'comparison_pages_inspected':10,'coordinate_pages_inspected':1,'uninspected_comparison_pages':['outputs/sr015-BM201-small-texture-1.png'],'prompt_file':floor['prompt_file'],'prompt_sha256':floor['prompt_sha256'],'generated_actual_size':[1254,1254],'final_canvas_size':[2048,2048],'final_resize':'Lanczos; not native AI8x','protected_file_hashes':protected,'pack_hashes':previous['pack_hashes'],'runtime_verified':False,'release_eligible':False,'next_step':'Keep BM201 held; reassess coherent material/damage reconstruction rather than stacking additional narrow inpaint overlays. Continue independent full-game source scope.'}
save('qa/local_sr015_review.json',sr15)
# Correct the reproducible script's overclaim as well; preserve the original.
for path in [R/'tools/refine_sr015_small_v3.py',C/'work/refine_sr015_small_v3.py']:
 text=path.read_text('utf8');old="'no_other_cell_or_enclosing_rim_donors':True"
 if old in text:
  if path.parent==R/'tools':shutil.copyfile(path,backup/path.name)
  path.write_text(text.replace(old,"'donor_cell_restriction_verified':True,'luminance_role_filter_applied':True,'rim_exclusion_proven':False").replace('Use only matching light/dark tile donors; exclude enclosing rim from sampled material.','Use same-cell luminance-filtered donors; semantic rim exclusion is not proven.'),'utf8')

# Independently validate all new field inference outputs and decide static candidates.
rep=read('qa/field_sr001_inference.json');shutil.copyfile(R/'qa/field_sr001_inference.json',backup/'field_sr001_inference.json');inv=read('qa/field_map_inventory_v2.json');source={v['group_id']:v for v in read('qa/field_source_review01.json')['files']}
pick={36:'photo',40:'wdn',48:'wdn',49:'wdn',52:'wdn',53:'photo',56:'wdn',57:'wdn',61:'wdn',62:'wdn',63:'photo',71:'photo',72:'photo',73:'photo',74:'photo',75:'photo',76:'photo',77:'photo',79:'photo',80:'photo',81:'photo',83:'wdn',84:'photo',118:'wdn'}
hold={55:'Both infer brick seams not securely recoverable from the original; source row/cell geometry unresolved.',78:'Both erase horizontal lattice bars. Manual v1 adds button-like bevels; exact-source fallback v2 preserves all pixels but is not a completed HD redraw.',117:'Both invent or strengthen crack networks and streaks across pale stone.',119:'Source has a fine diagonal/repeated dark pattern. WDN turns it into granular material; Photo erases it. Consumer/material identity needs review.'}
accepted={f'FM{n:04d}':f'FM{n:04d}-{t}' for n,t in pick.items()};hold={f'FM{n:04d}':v for n,v in hold.items()};checks=[]
assert len(accepted)==24 and len(hold)==4
for v in rep['files']:
 s=img(v['source']);o=img(v['output']);assert raw(s)==v['source_rgba_sha256']==source[v['group_id']]['source_rgba_sha256'];check(v['source_ptm'],v['source_ptm_sha256']);check(v['model']['path'],v['model']['sha256'])
 for k in ['input','native','output']:check(v[k],v[k+'_sha256'])
 native=Image.open(v['native']).convert('RGB');assert native.size==(s.width*4,s.height*4);assert o.size==(s.width*8,s.height*8)==tuple(v['output_size']);assert o.getchannel('A').getextrema()==(255,255)
 rebuilt=native.resize(o.size,Image.Resampling.LANCZOS).convert('RGBA');assert np.array_equal(np.asarray(o),np.asarray(rebuilt))
 gid=v['group_id'];status='selected_static_candidate' if accepted.get(gid)==v['id'] else ('held' if gid in hold else 'not_selected')
 reason=hold.get(gid,'Selected against source for material/line balance; model detail is interpretive, not recovered true HD.' if status=='selected_static_candidate' else 'Alternative model not selected after direct comparison.')
 v['visual_review']={'reviewer':'Codex internal','status':status,'reason':reason};checks.append({'id':v['id'],'source_ptm_rgba_model_input_native_output_hashes_verified':True,'native4x_final8x_verified':True,'opaque255_verified':True,'post_resize_exact':True,'decision':status})
for p in rep['pages']:check(p['path'],p['sha256']);p['review_status']='directly_inspected_by_Codex_internal'
assert rep['actual_local_rgb_inference_passes']==sum(v['actual_local_rgb_inference_passes'] for v in rep['files'])==56
details=read('qa/field_sr001_details.json')
for p in details['pages']:check(p['path'],p['sha256']);p['review_status']='directly_inspected_by_Codex_internal'
save('qa/field_sr001_details.json',details)
gridchecks=[]
for n in ['qa/field_sr001_grid.json','qa/field_sr001_grid_v2.json']:
 v=read(n);shutil.copyfile(R/n,backup/Path(n).name)
 for k in ['parent','vector','render','mask','output','comparison']:check(v[k],v[k+'_sha256'])
 s=img(v['source']);o=img(v['output']);p=img(v['parent']);mask=np.asarray(Image.open(v['mask']))>0;assert raw(s)==v['source_rgba_sha256'] and np.array_equal(np.asarray(o)[~mask],np.asarray(p)[~mask])
 isv2=n.endswith('v2.json');v['visual_review']={'reviewer':'Codex internal','status':'fallback_only_not_HD_candidate' if isv2 else 'rejected','reason':'Exact protected source pixels; hard transition/pixel-sized cells remain. Keep as faithful fallback, not finished hand-drawn HD.' if isv2 else 'Separate raised rims resemble sixteen buttons and create an obvious patch; source calls for connected lattice.'}
 if isv2:
  box=tuple(v['source_box']);p1=s.crop(box).resize(((box[2]-box[0])*8,(box[3]-box[1])*8),Image.Resampling.NEAREST);p2=o.crop(tuple(x*8 for x in box));assert np.array_equal(np.asarray(p1),np.asarray(p2));assert v['protected_output_pixels']==7040
 gridchecks.append({'id':v['id'],'hashes_verified':True,'outside_mask_exact':True,'protected_source_nearest_exact':isv2,'decision':v['visual_review']['status']});save(n,v)
# Measured repeated-line diagnostics, limited to sampled interior sections.
profiles=[];rows={v['id']:v for v in rep['files']}
for gid,axis,lo,hi,extent in [('FM0072','x',46,51,64),('FM0084','y',15,49,53)]:
 data={}
 for tag in ['source','photo']:
  v=rows[gid+'-photo'];im=img(v['source'] if tag=='source' else v['output']);a=np.asarray(im.convert('RGB'),float).mean(2);scale=1 if tag=='source' else 8
  prof=a[lo*scale:hi*scale,:extent*scale].mean(0) if axis=='x' else a[:extent*scale,lo*scale:hi*scale].mean(1)
  peaks,prop=find_peaks(-prof,distance=3*scale,prominence=20);data[tag]={'interior_dark_troughs':len(peaks),'positions_source_units':[(float(p)+.5)/scale for p in peaks]}
 data['group_id']=gid;data['sampling']={'axis':axis,'perpendicular_band':[lo,hi],'extent':extent,'prominence_0_255':20,'minimum_distance_source_px':3};data['count_match']=data['source']['interior_dark_troughs']==data['photo']['interior_dark_troughs'];profiles.append(data)
 assert data['count_match'],data
save('qa/field_sr001_inference.json',rep)
fieldgroups=[]
for g in inv['groups']:
 gid=g['group_id'];v=rows.get(accepted.get(gid,''));fieldgroups.append({'group_id':gid,'width':g['width'],'height':g['height'],'rgba_sha256':g['rgba_sha256'],'representative':g['representative'],'battle_pixel_equivalent_group':g.get('battle_pixel_equivalent_group'),'local_sr_attempted':gid in accepted or gid in hold,'candidate':None if not v else {'id':v['id'],'path':v['output'],'sha256':v['output_sha256'],'review':'qa/field_sr001_review.json','runtime_verified':False,'release_eligible':False},'status':'static_candidate' if v else ('held' if gid in hold else 'not_processed_in_field_context'),'hold_reason':hold.get(gid)})
fieldcat={'schema':'brs-field-sr-catalog/v1','source_inventory':'qa/field_map_inventory_v2.json','source_inventory_sha256':sha(R/'qa/field_map_inventory_v2.json'),'group_equivalence':'Exact dimensions/RGBA only; does not establish consumer, UV, exclusions or PPSSPP key. Battle-equivalent groups have not been assigned field candidates.','groups':fieldgroups,'processing_summary':{'field_unique_groups':576,'battle_pixel_equivalent_groups':225,'field_novel_groups':351,'field_novel_sources_classified':72,'field_neural_originals':28,'field_static_candidates':24,'field_holds':4,'field_groups_not_processed_in_field_context':548,'remaining_novel_unprocessed':323},'runtime_verified':False,'release_eligible':False};save('qa/field_sr_catalog.json',fieldcat)
fieldreview={'schema':'brs-field-review/v1','batch':'FIELD-SR-001','source_pages_directly_inspected':8,'source_originals_classified':72,'new_neural_unique_originals':28,'actual_local_rgb_inference_passes':56,'external_generative_calls':0,'image_upload':False,'local_outputs':56,'direct_svg_or_protected_source_outputs':2,'checked_outputs':checks,'grid_checks':gridchecks,'selected_static_candidates':accepted,'held':hold,'comparison_pages_directly_inspected':14,'native8x_detail_pages_directly_inspected':7,'manual_grid_pages_directly_inspected':2,'geometry_diagnostics':profiles,'geometry_diagnostic_limits':'Sampled line count only. Does not prove every edge, material interpretation, native UV, consumer exclusion, or runtime layout.','processing_summary':fieldcat['processing_summary'],'prior_battle_summary_unchanged':cat['processing_summary'],'unique_neural_originals_title_battle_novel_field':285,'unique_count_basis':'Title1 + battle256 + new field28; geometry-only battle2 are excluded from neural count. Not whole-game coverage.','protected_file_hashes':protected,'pack_hashes':previous['pack_hashes'],'runtime_verified':False,'release_eligible':False,'remaining':['Finish FM0055/0078/0117/0119 and remaining novel field323; classify further source pages.','Battle holds17 and not-processed26 remain, as do enemy/effects/cutscene lanes and decoder gaps.','Native consumer/UV and PPSSPP key mapping; installed runtime title/Orbit/LOCK ON/full regions and final packaging remain.'],'next_action':'Reconstruct FM0078 connected lattice using source-positioned bars with coherent surrounding frame (not separate button bevels); source-exact v2 is fallback only. Continue further field source classification.'};save('qa/field_sr001_review.json',fieldreview)
for p,h in protected.items():check(R/p,h)
assert previous['pack_hashes']=={str(p.relative_to(pack)):sha(p) for p in pack.rglob('*') if p.is_file()}
with (R/'PROGRESS.md').open('a',encoding='utf8') as f:f.write('''

## 2026-09-23 — LOCAL-SR-015 / FIELD-SR-001
- 이전 SR014는 실패8안의 검수·원인 기록으로 progress. 이번은 BM201 외부재작화1회 검수와 필드72원본 분류/신규28원본56실제 local GPU pass/24정적후보를 추가한 progress. 전체목표active.
- BM201 built-in image_gen 1회 실제1254²→Lanczos2048². 원본과254인접대조쌍 부호역전0,207경계표본 측정. 표본/원본해상도 수준의 검사이며 전체칸·HD형상·nativeUV 보존 증거가 아님. 정확prompt workspace/gpt-trials/BM201-v1/prompt.txt.
- BM201 raw/tone2안과 작은균열수정4안=6출력, 신규local추론0/신규원본0. 실제원본에도 어두운균열 조각이 존재하나 생성안은 이를 과장. 좁은보정은 번짐/패치 흔적이 남아 모두채택안함. BM201계속보류. 10비교페이지+1좌표페이지직접검수. v3의rim제외보장 주장을 제거하고같은칸/밝기필터라는측정가능한사실만기록. qa/local_sr015_review.json.
- 필드 v2 총576그룹 중 전투와픽셀동일225를제외한351의첫72 원본8페이지전체분류. 글자5/캐릭터포스터1/가는alpha/창틀/도로atlas 등을 분리. 포스터는주인공연결제외검사보류. source review분류가소비자/UV/범위제외증거는아님.
- opaque28종 WDN/Photo 각28, 실제RGB56pass. input sigma.25/.35, native4x+Lanczos2x 최종8x. 새외부업로드0. 14전체비교+7실제8x crop직접검수. 24정적후보: FM0036/0040/0048/0049/0052/0053/0056/0057/0061/0062/0063/0071/0072/0073/0074/0075/0076/0077/0079/0080/0081/0083/0084/0118.
- 보류4: FM0055벽돌선 재해석,FM0078격자 가로선소실,FM0117균열망과장,FM0119반복패턴 재질변경. FM0078 직접SVG16칸v1도버튼같은새테두리로거부. v2는원본110px→7040px정확보호층;이는격자부분단순확대이며HD재작화로세지않음. 후보미채택/충실한fallback으로만보관. qa/field_sr001_grid*.json.
- 56추론출력 source PTM/RGBA·model/input/native/output SHA·4x/8x·alpha255·native출력에서Lanczos재현검사. SVG2출력/hash/mask밖정확 및v2원본격자RGBA정확. FM0072/0084 표본단면반복선개수일치; 전체형상/UV증거로확대해석안함. qa/field_sr001_review.json 및새 qa/field_sr_catalog.json.
- 전투241후보/17보류/26미처리 유지. 필드신규28처리/24후보/4보류,novel미처리323. 타이틀1+전투256+field28=neural고유285;geometry-only2별도. 전체게임분모/완료율아님. 기존20key시험팩·checker계약·fieldv2·Start-Title-QA해시완전보존. 설치/에뮬실행/런타임검증없음.
- 다음 FM0078원본연결격자/프레임을일관되게재구성(개별버튼테두리금지),field추가원본분류/미처리323,전투26/보류17 및적/효과/컷신·SC해독미완료계속. GUI접근복구증거없어검은화면캡처반복안함. 최종ZIP미완료.
''')
with (C/'outputs/로컬_업스케일_진행.md').open('a',encoding='utf8') as f:f.write('''

## 필드 배경 첫 검수 — FIELD-SR-001
- 새 필드 원본72개를 분류하고, 28개를 로컬 두 모델로 처리했습니다. 실제 추론56회, 24개는 정적후보이며 4개는 재작업이 필요합니다.
- 작은 격자는 로컬 모델이 가로선을 지웠습니다. 직접 그린16칸도 테두리가 버튼처럼 보여 채택하지 않았습니다. 원본 무늬를 정확히 보존한 대안은 따로 보관했으며, 격자부분은 단순확대이므로 HD복원완료라고 부르지 않습니다.
- 체크 바닥 BM201도 계속 보류입니다. built-in image_gen 외부재작화1회와 파생6출력을 검사했지만 균열과 재질 문제가 남았습니다. 이 작업은 로컬추론으로 세지 않습니다.
- 이번 통과는 파일 비교검수이며 실제 게임 검증/설치/최종배포는 아직입니다. 기록: P:/AI/Codex/projects/black-rock-shooter-hd-ui-fonts/qa/field_sr001_review.json.
''')
# A compact user-facing example of selected materials, not the unaccepted lattice.
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',20);sub=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',16);canvas=Image.new('RGB',(1056,752),'#202c38');d=ImageDraw.Draw(canvas)
for j,(gid,label) in enumerate([('FM0075','금속 지지대'),('FM0049','바닥과 경계선')]):
 v=rows[accepted[gid]];s=img(v['source']);im=img(v['output']);y=j*366
 for i,(pic,t) in enumerate([(s,'원본 · 단순 확대'),(im,'로컬 AI · 정적 검수 통과')]):
  x=i*528;d.text((x+12,y+8),label+' / '+t,font=font,fill='white');pic=pic.resize((320,320),Image.Resampling.NEAREST if i==0 else Image.Resampling.LANCZOS);canvas.paste(pic.convert('RGB'),(x+104,y+40))
d.text((12,732),'실제 게임 적용 전 비교입니다.',font=sub,fill='#bed0dd');op=C/'outputs/필드_배경_로컬_검수.png';canvas.save(op)
print(json.dumps({'sr015_outputs':6,'sr015_accepted':0,'field_local_passes':56,'field_static_candidates':24,'field_holds':4,'field_line_diagnostics':profiles,'catalog_and_pack_preserved':True,'preview':str(op)},ensure_ascii=False))
