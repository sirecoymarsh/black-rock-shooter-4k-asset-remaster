"""Reject reviewed geometric experiments without changing the accepted candidate set."""
import json,hashlib,copy,shutil
from pathlib import Path
import numpy as np,cv2
from PIL import Image
R=Path(__file__).resolve().parents[1];C=Path('C:/Users/CadriacLord/Documents/Codex/2026-09-22/brs-hd-ui-fonts');F=R/'qa/local_sr014_review.json'
if F.exists():raise SystemExit('Review already recorded.')
def read(p):return json.loads((R/p).read_text('utf8'))
def sha(b):return hashlib.sha256(b).hexdigest()
def check(p,h):assert sha(Path(p).read_bytes())==h,str(p)
def image(p):return Image.open(p).convert('RGBA')
cat=read('qa/battle_sr_catalog.json');groups={g['group_id']:g for g in cat['groups']}
assert sum(bool(g.get('candidate')) for g in groups.values())==241
assert not groups['BM175']['candidate'] and not groups['BM201']['candidate']
names=['qa/local_sr014_reconstruction.json','qa/local_sr014_refinement.json'];reports=[(p,read(p)) for p in names]
protected_paths=['qa/battle_sr_catalog.json','qa/checker_design_contract.json','qa/checker_fidelity_review_v1.json','qa/field_map_inventory_v2.json','tools/Start-Title-QA.ps1']
protected={p:sha((R/p).read_bytes()) for p in protected_paths}
pack=read('qa/local_sr_observed_review_pack_v2.json');pp=Path(pack['path']);check(pp/'textures.ini',pack['textures_ini_sha256']);assert len(pack['keys'])==20
packhashes={str(p.relative_to(pp)):sha(p.read_bytes()) for p in pp.rglob('*') if p.is_file()}
checks=[];corrections=[]
for name,rep in reports:
 for row in rep['files']:
  gid=row['group_id'];src=image(row['source']);out=image(row['output']);a=np.asarray(src);b=np.asarray(out)
  assert sha(src.tobytes())==row['source_rgba_sha256']==groups[gid]['rgba_sha256'];g=groups[gid]['representative'];check(g['source'],g['source_sha256'])
  for key in ['output','parent','structure_parent','mask','vector_layout']:
   if key in row:check(row[key],row[key+'_sha256'])
  assert out.size==(src.width*8,src.height*8)==tuple(row['output_size']) and np.all(b[:,:,3]==255)
  assert row['new_neural_passes']==row['new_generative_calls']==0
  m=Image.open(row['mask']).convert('L');m=m.resize(out.size,Image.Resampling.NEAREST) if m.size!=out.size else m
  outside=np.asarray(m)==0;parent=np.asarray(image(row['parent']));outside_delta=int(np.abs(b.astype(int)-parent.astype(int))[outside].max()) if outside.any() else 0
  assert outside_delta<=1
  mesh=[]
  for p in row.get('panels',[]):
   check(p['source_hole_mask'],p['source_hole_mask_sha256']);check(p['coverage'],p['coverage_sha256'])
   low=np.asarray(Image.open(p['source_hole_mask']))>0;coverage=Image.open(p['coverage']).convert('L');hi=np.asarray(coverage)>=128
   nc=int(cv2.connectedComponents(low.astype('uint8'),8)[0]-1);nh=int(cv2.connectedComponents(hi.astype('uint8'),8)[0]-1)
   sample=np.asarray(coverage.resize((low.shape[1],low.shape[0]),Image.Resampling.NEAREST))>=128;bad=int((sample!=low).sum())
   assert nc==p['source_components'] and nh==p['output_components']
   if name.endswith('refinement.json'):
    old_bad=p['source_sample_class_mismatches']
    p['source_sample_class_mismatches']=bad
    if old_bad!=bad:corrections.append({'id':row['id'],'panel':p['box'],'field':'source_sample_class_mismatches','inherited_prior_value':old_bad,'measured_value':bad})
    assert nc==nh and p['all_source_components_represented']
   else:
    # v1 records used a float coverage truncated to uint8 before saving; the final saved rounded image is authoritative for this review.
    p['saved_coverage_source_sample_class_mismatches']=bad
   mesh.append({'source_components':nc,'output_components':nh,'saved_source_sample_class_mismatches':bad})
  for p in row.get('patches',[]):
   for key in ['mask','crack_mask']:check(p[key],p[key+'_sha256'])
  if gid=='BM175':
   reason='Rounded level-set version splits source dark components and resembles scattered round holes.' if 'holes-' in row['id'] else 'Angular version retains source dark component count, but appears as clean slots in a smooth plate; this does not establish the original mesh/material design.'
  else:
   reason='Independent cell fill produces pasted planar patches and speckled crack edges.' if 'cells-' in row['id'] else 'Narrow retained local edge bands overlap the newly aligned cells, leaving horizontal bands/double boundaries. Material/quiet variants do not pass source fidelity review.'
  row['visual_review']={'reviewer':'Codex internal','status':'rejected','reason':reason,'runtime_verified':False}
  checks.append({'id':row['id'],'source_ptm_rgba_output_parent_mask_vector_hashes_verified':True,'size8x_verified':True,'alpha255_verified':True,'outside_quantized_edit_mask_max_channel_delta':outside_delta,'mesh':mesh,'decision':'rejected'})
 assert rep['new_neural_passes']==rep['new_generative_calls']==0
 rep['review_status']='Rejected after visual inspection; no candidates installed or accepted. See qa/local_sr014_review.json.'
assert len(checks)==8

# Independent source/candidate sample contrast diagnostic. This is not an all-cell or native UV proof.
contrast=[]
for row in reports[1][1]['files']:
 if row['group_id']!='BM201':continue
 src=image(row['source']);a=np.asarray(src.convert('RGB'),float).mean(2)
 images={'initial_local':image(row['parent']),'reconstruction':image(row['output'])}
 reduced={k:np.asarray(v.convert('RGB').resize(src.size,Image.Resampling.LANCZOS),float).mean(2) for k,v in images.items()}
 for p in row['patches']:
  vals={}
  for c in p['cells']:
   if c['source_samples']<25:continue
   x0,y0,x1,y1=c['source_bounds'];x=int((x0+x1)/2);y=int((y0+y1)/2)
   vals[(c['column'],c['row'])]={'source':float(a[y-1:y+2,x-1:x+2].mean()),**{k:float(v[y-1:y+2,x-1:x+2].mean()) for k,v in reduced.items()}}
  pairs=[]
  for xy,v in vals.items():
   for other in [(xy[0]+1,xy[1]),(xy[0],xy[1]+1)]:
    if other not in vals:continue
    u=vals[other];delta=u['source']-v['source']
    if abs(delta)<10:continue
    pairs.append({'from':xy,'to':other,'source_difference':delta,**{k+'_difference':u[k]-v[k] for k in reduced}})
  contrast.append({'id':row['id'],'patch':p['id'],'source_stable_sample_cells':len(vals),'sample_pairs':len(pairs),'opposite_sign_vs_source':{k:[v for v in pairs if v[k+'_difference']*v['source_difference']<=0] for k in reduced},'interpretation':'3x3 source-positioned center means, limited to cells with >=25 assigned source samples and source adjacent difference >=10/255. Partial edges and damaged cells may not represent checker phase.'})

inspected=['outputs/sr014-BM175-compare1.png']+[f'outputs/sr014-BM201-compare{k}.png' for k in [0,1,2]]+[f'outputs/sr014-v2-BM175-compare{k}.png' for k in [0,1]]+[f'outputs/sr014-v2-BM201-compare{k}.png' for k in range(5)]
source_inspected=['BM175-p0','BM201-p0','BM201-p1','BM201-p2','BM201-p3','BM201-p4','BM209-p0','BM209-p2','BM244-p3']
evidence=inspected+[f'outputs/sr014-source/{n}.png' for n in source_inspected]
report={'schema':'brs-local-sr-review/v14','batch':'LOCAL-SR-014','previous_goal_turn_classification':'progress: SR013 accepted two static redraw candidates with preserved catalog and provenance','checked_outputs':checks,'accepted_candidates':{},'still_held':['BM175','BM201'],'new_unique_originals':0,'new_actual_local_neural_passes':0,'external_generative_calls':0,'metadata_corrections':corrections,'source_contrast_diagnostics':contrast,'review_evidence':[{'path':str(R/p),'sha256':sha((R/p).read_bytes()),'reviewer':'Codex internal','status':'directly_inspected'} for p in evidence],'comparison_pages_generated':14,'comparison_pages_inspected':11,'source_pages_generated':15,'source_pages_inspected':9,'processing_summary_unchanged':cat['processing_summary'],'protected_file_hashes':protected,'pack_hashes':packhashes,'runtime_verified':False,'release_eligible':False,'findings':['BM175 source pattern has repeating small diagonal dark groups; reconstructed count alone does not prove its physical material design.','V1 mesh changes 36/35 source dark groups into 50/50 high-resolution groups. V2 preserves 36/35 but looks like a slotted plate. Both rejected.','BM201 source already contains broad cracks. The initial audit must not treat all triangular damage as invented; actual new deformation and original damage must be distinguished.','BM201 isolated cell paint leaves artificial flatness; blending back local crack/rim bands produces visible overlap strips. Do not keep stacking local overlays.','BM201 source/candidate sample contrasts show remaining opposite signs near the top damaged rim, and are insufficient to prove exact checker phase.','BM209/BM244/BM226 inspected source/current audit images only; not reconstructed or completed this batch.'],'next_action':['Replace the overlapping floor repair with a single coherent source-derived surface for the entire patch, with grid and damage represented in the same coordinate system.','For BM175 obtain consumer/material reference if available before choosing between wire mesh and perforated/slotted plate; retain original dark groups as the objective positional evidence.','Continue remaining checker audit and full-game inventory/processing. Existing static candidates do not establish runtime or complete-game coverage.'],'scripts':{p:sha((R/'tools'/p).read_bytes()) for p in ['inspect_sr014_checkers.py','reconstruct_sr014.py','refine_sr014.py','review_sr014.py']}}
backup=R/'qa/backups/before-sr014-review';backup.mkdir(parents=True,exist_ok=False)
for name,_ in reports:shutil.copyfile(R/name,backup/Path(name).name)
for name,rep in reports:(R/name).write_text(json.dumps(rep,ensure_ascii=False,indent=2),'utf8')
F.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
with (R/'PROGRESS.md').open('a',encoding='utf8') as f:f.write('''

## 2026-09-23 — LOCAL-SR-014: 체크 바닥·철망 재구성 실패 판정과 원인 기록
- 이전 goal turn SR013은 후보2종을 실제기록한 progress. 이번은 원본측정/재구성8출력/직접검수 및 실패원인·다음변경근거를 남긴 progress이며, 후보 추가는0이다. qa/local_sr014_review.json.
- BM175 source dark그룹 분리와 독립명암 v1두안: 상/하36/35그룹이 highres50/50으로분리되고 둥근점무늬로 보여거부. v2각진SVG두안:36/35그룹·모든원본그룹표현 확인했으나 매끈한판에슬롯을낸디자인으로바뀌어거부. source dark그룹은실제구멍수확정이아님. 메쉬/타공판의실제소비자료필요.
- BM2015원본patch의좌표·checker경계·원래균열을분리하여224개부분cell영역을2명암설정으로그림. 실제완전한칸224개라는뜻아님. 평평한붙임판/얼룩진균열로v1두안거부. v2 source색+local미세재질/좁은균열경계유지두안도grid와parent경계겹침의가로띠발견으로거부. 다음은겹쳐붙이기를중단하고patch전체를한좌표계의일관된surface로재구성.
- 실제원본확대에서일부큰삼각균열은원래존재함확인; 모든삼각파손을모델이만든것으로일괄판정하지않음. 원본파손과추가변형분리필요. strongadjacent3x3표본254쌍중원본과부호다른2쌍이윗손상경계에남음; 전체칸phase/geometry증거로쓰지않음. 초기local대비도별도기록.
- 원본확대15페이지중9개·비교14페이지중11개직접검수. 8출력 PTM/RGBA/source/parent/structure/mask/SVG/output SHA·8배·alpha255검사. v2 panel metadata의이전sample오차값이상속된것을현재저장coverage재측정으로정정,이전값별도기록.
- 실제신규local추론0/GPT외부생성0/신규원본0. 이전모델출력활용과수치/SVG재구성을AI추론으로세지않음. 기존카탈로그241후보/17보류/26미처리,20key팩,checker계약,fieldv2,Start-Title-QA해시보존;설치/에뮬실행/런타임검증없음. BM175/BM201계속보류.
- BM209/BM244/BM226는원본/기존비교재검토만했고재구성완료주장없음. 다음checkerpatch단일surface,소비자확인자료,전체field/적/효과/컷신및남은26원본계속. 전체목표active;외부화면접근문제는전체오프라인작업의막힘이아님.
''')
with (C/'outputs/로컬_업스케일_진행.md').open('a',encoding='utf8') as f:f.write('''

## 추가 검수 — LOCAL-SR-014
- 철망과 체크 바닥을 직접 재구성한8안을 검사했으나 이번에는 모두 보류했습니다. 철망은 구멍 수가 맞아도 원본과 다른 타공판처럼 보였고, 바닥에는 수정한 칸과 기존 경계가 겹치는 띠가 남았습니다.
- 원본에도 큰 균열이 있어 이를 전부 모델 오류로 취급하지 않도록 기준을 구체화했습니다. 다음 바닥 수정은 겹쳐 붙이는 방식 대신 전체 무늬와 파손을 한 번에 맞추는 방식으로 진행해야 합니다.
- 이번 새 로컬 추론/GPT 외부 생성은0회이며, 기존 결과를 바탕으로 도형과 색을 다시 구성했습니다. 후보 수는241, 보류17, 미처리26으로 그대로입니다. 실제 게임 검증 전입니다.
''')
assert all(sha((R/p).read_bytes())==h for p,h in protected.items())
assert packhashes=={str(p.relative_to(pp)):sha(p.read_bytes()) for p in pp.rglob('*') if p.is_file()}
print(json.dumps({'checked_outputs':8,'accepted':0,'held':['BM175','BM201'],'catalog_unchanged':True,'metadata_corrections':corrections,'comparison_pages_directly_inspected':11},ensure_ascii=False))
