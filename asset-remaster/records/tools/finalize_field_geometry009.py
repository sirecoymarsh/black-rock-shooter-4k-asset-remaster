from pathlib import Path
import json,hashlib,shutil,copy,sys,importlib.util,xml.etree.ElementTree as ET
sys.dont_write_bytecode=True
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];C=Path(r'C:\Users\CadriacLord\Documents\Codex\2026-09-22\brs-hd-ui-fonts');Q=R/'qa/field_geometry009_review.json';assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text('utf8'))
def write(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False),'utf8')
def arr(p):return np.asarray(Image.open(p).convert('RGBA'))
last=read(R/'qa/field_geometry008_review.json');cp=R/'qa/field_sr_catalog.json';gp=R/'qa/architectural_geometry_contract.json';cat=read(cp);before=copy.deepcopy(cat);contract=read(gp)
assert sha(cp)==last['catalog_after_sha256'] and sha(gp)==last['geometry_contract_after_sha256']
for rel,h in last['protected_file_hashes'].items():assert sha(R/rel)==h
pack=R/'workspace/local-sr/observed-review-pack-v2/PSP/TEXTURES/NPUH10126';packhash={str(p.relative_to(pack)):sha(p) for p in pack.rglob('*') if p.is_file()};assert packhash==last['pack_hashes']
old=[g['candidate'] for g in cat['groups'] if g['candidate']];assert len(old)==104
for z in old:assert sha(z['path'])==z['sha256']
audits={v:read(R/'qa'/n) for v,n in [(1,'field_geometry009_lattice_audit.json'),(2,'field_geometry009_lattice_audit_v2.json')]}
for audit in audits.values():
 assert audit['catalog_before_sha256']==sha(cp) and audit['geometry_contract_before_sha256']==sha(gp)
 for z in audit['source_records']:
  assert sha(z['source_ptm'])==z['source_ptm_sha256'] and hashlib.sha256(arr(z['source']).tobytes()).hexdigest()==z['source_rgba_sha256'];assert sha(z['overlay'])==z['overlay_sha256']
names=['field_geometry009_reconstruction_v1.json','field_geometry009_reconstruction_v2.json','field_geometry009_reconstruction_v3.json','field_geometry009_checker394_v3.json'];reports={n:read(R/'qa'/n) for n in names};checked=[];pages=[];selected={};diagnostics={}
for ni,(name,rep) in enumerate(reports.items()):
 assert sha(rep['reconstruction_program'])==rep['reconstruction_program_sha256'];anum=1 if ni==0 else 2;ap=R/'qa'/('field_geometry009_lattice_audit.json' if anum==1 else 'field_geometry009_lattice_audit_v2.json');assert rep['lattice_audit_sha256']==sha(ap)
 spec=importlib.util.spec_from_file_location('frozen_checker009_'+str(ni),rep['reconstruction_program']);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 for z in rep['files']:
  for k in ['source_ptm','parent','output','mask','maps','vector']:assert sha(z[k])==z[k+'_sha256']
  s=arr(z['source']);p=arr(z['parent']);out=arr(z['output']);assert hashlib.sha256(s.tobytes()).hexdigest()==z['source_rgba_sha256'];h,w=s.shape[:2]
  patches=z.get('applied_lattice_patches',next(v for v in audits[anum]['source_records'] if v['group_id']==z['lattice_source_group'])['patches'])
  expected,union,maps,recs,vectors=mod.build(s,p,patches,z['coordinate_scale']);assert np.array_equal(expected,out) and recs==z['recipe'];f=np.load(z['maps']);assert np.array_equal(union,f['union'])
  for k,a in maps.items():assert np.isfinite(a).all() and np.array_equal(a,f[k])
  assert np.array_equal(np.asarray(Image.open(z['mask'])),np.rint(union*255).astype('uint8'));assert np.array_equal(out[union==0],p[union==0]) and np.all(out[:,:,3]==255) and out.shape==(h*8,w*8,4)
  root=ET.parse(z['vector']).getroot();groups=list(root.iter('{http://www.w3.org/2000/svg}g'));clips=list(root.iter('{http://www.w3.org/2000/svg}clipPath'));assert len(groups)==len(recs)==len(clips)
  for group,clip,rec in zip(groups,clips,recs):
   element=list(clip)[0];points=np.array([[float(q) for q in t.split(',')] for t in element.attrib['points'].split()]);assert np.array_equal(points,np.asarray(rec['source_clip_polygon']))
   polys=list(group);assert len(polys)==len(rec['cells'])
   for el,cell in zip(polys,rec['cells']):
    points=np.array([[float(q) for q in t.split(',')] for t in el.attrib['points'].split()]);assert np.array_equal(points,np.asarray(cell['source_quad']));edges=np.roll(points,-1,0)-points;assert abs(np.cross(edges[0],edges[2]))<1e-10 and abs(np.cross(edges[1],edges[3]))<1e-10
   M=np.asarray(rec['lattice_matrix']);assert np.linalg.det(M)>0
  chosen=(ni==2 and z['group_id'] in ['FM0430','FM0444']) or ni==3
  reason='Source geometry/phase restored with original patch colors and restrained local grain; final treatment includes upper-right checker fragments.' if chosen else 'First reconstruction:394 material too soft;430/444 small-grid orientation initialization wrong.' if ni==0 else 'Intermediate geometry:394 retained a tiny nonorthogonal fit term;430/444 upper-right treatment omitted surviving checker fragments.'
  checked.append({'id':z['id'],'path':z['output'],'sha256':z['output_sha256'],'decision':'static_candidate' if chosen else 'not_selected','reason':reason,'source_parent_vector_mask_maps_program_output_hashes_verified':True,'RGBA_recipe_reproduced':True,'outside_treatment_parent_RGBA_exact':True,'alpha_source_nearest8x_exact':True,'runtime_verified':False,'release_eligible':False})
  if chosen:
   selected[z['group_id']]=z;y,x=np.mgrid[0:h,0:w];x=x+.5;y=y+.5;items=[]
   for a in recs:
    M=np.array(a['lattice_matrix']);c=np.array(a['source_center']);phase=np.array(a['lattice_phase']);u=M[0,0]*(x-c[0])+M[0,1]*(y-c[1])+phase[0];v=M[1,0]*(x-c[0])+M[1,1]*(y-c[1])+phase[1];valid=(maps[a['name']+'-weight'][4::8,4::8]>.99)&(abs(u-np.round(u))<.33)&(abs(v-np.round(v))<.33);wave=np.where((np.round(u).astype(int)+np.round(v).astype(int))%2==0,1.,-1.);X=np.column_stack([np.ones(valid.sum()),x[valid]-c[0],y[valid]-c[1],wave[valid]]);result={}
    for label,path in [('source',z['source']),('local_WDN',z['parent']),('final',z['output'])]:
     a0=np.asarray(Image.open(path).convert('RGB').resize((w,h),Image.Resampling.LANCZOS)).mean(2);coef=np.linalg.lstsq(X,a0[valid],rcond=None)[0];result[label]=float(coef[3])
    assert valid.sum()>15 and result['source']*result['final']>0;ratio=result['final']/result['source'];assert .7<ratio<1.2
    items.append({'patch':a['name'],'source_pixel_centers_tested':int(valid.sum()),'checker_coefficient_RGB_mean':result,'output_to_source_coefficient_ratio':ratio,'phase_polarity_preserved':True})
   if z['group_id']=='FM0394':
    M=np.array(recs[0]['lattice_matrix']);assert M[0,1]==M[1,0]==0
    for cell in recs[0]['cells']:
     a=np.array(cell['source_quad']);assert a[0,1]==a[1,1] and a[1,0]==a[2,0] and a[2,1]==a[3,1] and a[3,0]==a[0,0]
   diagnostics[z['group_id']]={'patches':items,'straight_affine_cell_edges':True,'all_cell_axes_exact_horizontal_vertical':z['group_id']=='FM0394','limit':'Source-center checker coefficients support phase/contrast on measured interiors. They do not certify exact fragment-cell counts, every damaged edge or high-resolution ground truth. Source remapping keeps cell-level tone; faint444 retains70-90% source contrast instead of approximately half under WDN.'}
 for pp in rep['pages']:
  assert sha(pp['path'])==pp['sha256'];pages.append({**pp,'review_status':'directly_inspected_by_Codex_internal','report':name})
assert len(checked)==9 and len(selected)==3 and len(pages)==26
for anum,audit in audits.items():
 for z in audit['source_records']:
  duplicate=anum==2 and z['group_id']=='FM0394';previous=next(v for v in audits[1]['source_records'] if v['group_id']==z['group_id'])
  if duplicate:assert z['overlay_sha256']==previous['overlay_sha256']
  pages.append({'path':z['overlay'],'sha256':z['overlay_sha256'],'review_status':'not_reopened_identical_to_inspected_v1' if duplicate else 'directly_inspected_by_Codex_internal'})
for gid in ['FM0394','FM0430']:
 pp=C/'work'/(gid+'-geometry009-coordinates.png');dst=R/'outputs/field-geometry009'/pp.name;shutil.copy2(pp,dst);pages.append({'path':str(dst),'sha256':sha(dst),'review_status':'directly_inspected_by_Codex_internal'})
for gid in selected:
 pp=R/'outputs/field-geometry008'/(gid+'-source.png');pages.append({'path':str(pp),'sha256':sha(pp),'review_status':'directly_inspected_by_Codex_internal','reused_source_page':True})
assert len(pages)==35 and sum(p['review_status']=='directly_inspected_by_Codex_internal' for p in pages)==34
for g in cat['groups']:
 gid=g['group_id']
 if gid in selected:
  assert g['status']=='held' and g['local_sr_attempted'];v=selected[gid];g.update(status='static_candidate',hold_reason=None,candidate={'id':v['id'],'path':v['output'],'sha256':v['output_sha256'],'review':'qa/field_geometry009_review.json','method':v['method'],'geometry_review':'Source-fitted checker cell boundaries; phase/contrast separately checked against each source; source RGB material and restrained reused local grain. Exact90-degree grid for394.','runtime_verified':False,'release_eligible':False})
for a,b in zip(before['groups'],cat['groups']):
 if a['group_id'] not in selected:assert a==b
stats=cat['processing_summary'];stats.update(field_static_candidates=107,field_holds=46,latest_review='qa/field_geometry009_review.json')
assert sum(bool(g['candidate']) for g in cat['groups'])==107 and sum(g['status']=='held' for g in cat['groups'])==46 and sum(g['local_sr_attempted'] for g in cat['groups'])==149
for gid in selected:contract['current_batch_geometry_holds'].pop(gid,None)
contract['geometry_review009']={'review':'qa/field_geometry009_review.json','static_candidates':{k:v['id'] for k,v in selected.items()},'field_checker_review':'qa/field_checker_design_review009.json','source_interpretation_correction':'430/444 fragments have slanted/torn outer boundaries; their internal checker axes are close to horizontal/vertical. First tilted-grid initialization was wrong and rejected.','new_local_passes':0,'new_external_calls':0,'new_unique_originals':0,'runtime_verified':False,'release_eligible':False}
checker={'schema':'brs-field-checker-design-review009/v1','parent_contract':'qa/checker_design_contract.json','parent_contract_sha256':sha(R/'qa/checker_design_contract.json'),'previous_field_checker_review':'qa/field_checker_design_review008.json','selected':{k:v['id'] for k,v in selected.items()},'geometry_diagnostics':diagnostics,'source_painting_policy':'Checker shape/phase is authored from source-intensity lattice evidence. RGB is interpolated inside original cells, using clipped local high-frequency material only. Treatment contours blend around retained source fragmentation; no new complete checker sheet is invented.','SVG_limit':'The SVG contains geometry guides with alternating diagnostic fills. Final colors and bright/dark phase come from each source RGBA, not the diagnostic SVG fills.','source_and_consumer_limit':'444 half-scale430 geometry was checked against444 source phase/contrast and every visible fragment. Shared appearance does not establish shared consumer semantics.','runtime_verified':False,'release_eligible':False}
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17);can=Image.new('RGB',(1050,1200),'#25313c');dr=ImageDraw.Draw(can)
for row,gid in enumerate(['FM0394','FM0430','FM0444']):
 v=selected[gid]
 for col,(path,label) in enumerate([(v['source'],'원본 · 단순 확대'),(v['parent'],'로컬 AI 비교'),(v['output'],'체크 구조·재질 수정')]):
  im=Image.open(path).convert('RGB').resize((320,320),Image.Resampling.NEAREST if col==0 else Image.Resampling.LANCZOS);dr.text((col*350+10,row*400+10),gid+' '+label,font=font,fill='white');can.paste(im,(col*350+15,row*400+50))
preview=R/'outputs/field-geometry009/장식_체크_3종_복원_비교.png';can.save(preview);localpreview=C/'outputs'/preview.name;shutil.copy2(preview,localpreview)
backup=R/'qa/backups/before-field-geometry009-review';backup.mkdir(exist_ok=False)
for p in [cp,gp]:shutil.copy2(p,backup/p.name)
write(cp,cat);write(gp,contract);chp=R/'qa/field_checker_design_review009.json';write(chp,checker)
report={'schema':'brs-field-geometry009-final-review/v1','batch':'FIELD-GEOMETRY-009','previous_goal_turn_classification':'progress: geometry008 five new originals/two checker candidates; final recipes and review records completed.','this_goal_turn_classification':'progress: source checker fits corrected,9 geometry/material derivatives checked and3 held checker originals become static candidates.','selected':{k:v['id'] for k,v in selected.items()},'checked_outputs':checked,'geometry_diagnostics':diagnostics,'new_local_neural_unique_originals':0,'new_geometry_only_unique_originals':0,'new_direct_GPT_only_unique_originals':0,'new_local_inference_passes':0,'external_generative_calls':0,'source_reports_sha256':{str((R/'qa'/n).relative_to(R)):sha(R/'qa'/n) for n in names+['field_geometry009_lattice_audit.json','field_geometry009_lattice_audit_v2.json']},'source_and_comparison_pages':pages,'pages_directly_inspected':34,'catalog_before_sha256':last['catalog_after_sha256'],'catalog_after_sha256':sha(cp),'geometry_contract_before_sha256':last['geometry_contract_after_sha256'],'geometry_contract_after_sha256':sha(gp),'field_checker_design_review_sha256':sha(chp),'other573_field_groups_unchanged':True,'previous104_field_candidates_unchanged':True,'field_processing_summary':stats,'unique_local_neural_originals_title_battle_novel_field':406,'processed_originals_title_battle_novel_field_all_routes':412,'all_routes_count_basis':{'title':1,'battle':258,'novel_field':153},'protected_file_hashes':last['protected_file_hashes'],'pack_hashes':packhash,'preview':{'path':str(localpreview),'project_path':str(preview),'sha256':sha(preview),'review_status':'pending_direct_inspection'},'source_interpretation_corrections':['First430/444 grid used fragment silhouette angle as internal grid angle. Source peak centers and second fit show near-axis-aligned checker; first orientation discarded.','Initial upper-right treatment failed to cover intact left/up checker fragments; v3 expands treatment over source-supported fragments.','Large394 initial near-orthogonal affine fit had tiny nonzero cross terms. Final sets cross terms exactly zero for horizontal/vertical lines and90-degree cell corners.'],'tips_consulted':['references/tips/general/whole-canvas-rendering-preserved-cross-tile-effects.md','references/tips/general/equal-raw-bytes-can-have-different-consumer-semantics.md'],'runtime_verified':False,'release_eligible':False,'all_game_complete':False,'limits':['Source geometry is a bounded affine reconstruction from low-resolution evidence, not native high-resolution ground truth. Do not claim exact original fragment-cell counts from the treatment polygon.','Source RGB is independently remapped within each cell; chip/dirt tone remains an interpretation at subpixel edges. Materials use previously generated local detail, with no new neural inference this turn.','444 source-scale core checker contrast ratios are approximately.78-.84; better retained than prior WDN, but not exact source contrast.','Historical57 field/241 battle candidates need geometry-applicability checks;46 field holds/198 novel unprocessed,43 battle issues and other game populations remain.','No new runtime key, installation, emulator launch, gameplay proof or release ZIP. GUI remains unavailable; no successful Explorer claim.'],'next_action':'Resolve496 coupled plate corner and adjoining edges; continue masonry456/465/466/473 and machinery29/391/396/407, perspective37/38 and remaining198 field originals, battle and other game populations.','scripts':{n:sha(R/'tools'/n) for n in ['fit_checker_geometry009.py','fit_checker_geometry009_v2.py','rebuild_checker_geometry009.py','rebuild_checker_geometry009_v2.py','rebuild_checker_geometry009_v3.py','rebuild_checker394_geometry009_v3.py','finalize_field_geometry009.py']}}
for rel,h in last['protected_file_hashes'].items():assert sha(R/rel)==h
assert {str(p.relative_to(pack)):sha(p) for p in pack.rglob('*') if p.is_file()}==packhash
write(Q,report)
note='''

## 2026-09-23 — FIELD-GEOMETRY-009 / 장식 체크3종 복원
- 이전008 progress. 이번3기존held source검토/9재구성출력으로progress. 신규원본·로컬추론·외부생성0. 전체목표active.
- 394 큰격자 source강도에bounded affinefit. v1 재질너무부드러움→v2 source칸내RGB+WDN잔질감σ6/gain.85/±9, v3 아주작은off-axis항0으로고정해 정확한수평수직·90도. v3정적후보. 원본칸별색/먼지유지하며 AI베벨·과장균열제외.
- 430/444 v1은찢긴조각외곽기울기를내부격자로오인해잘못기울임. 원본밝은칸peak초기값으로v2수정:각격자는거의축정렬. v2상단우측처리범위가왼/윗쪽온전한체크조각누락→v3확장. 4조각전체확대검수후두v3정적후보.
- 444는430의halfscale geometry를별도원본색으로재구성. 외형유사성이소비자동일증거아님. 원본별core격자계수9영역모두부호유지,최종/source비.70..1.20검사. 444네영역실제.78..84로WDN의대략절반보존보다개선되나정확한source대비아님.
- 9출력source/PTM/parent/vector/mask/maps/frozenprogram/output해시·RGBArecipe재현·mask밖parent정확·alpha255보존. source/좌표/격자overlay/비교35페이지중34직접검수,394auditv2는본v1과동일hash라중복열기생략. 기하guideSVG의흑백은진단용이며최종색/위상은원본RGB에서옴. 처리polygon에걸친cell목록은전체원본파손칸수의증거아님.
- field107정적후보/46보류/198novel미처리. local149/directGPT-only3/geometry-only1/전체153원본그대로,전게임현재조사범위local406/allroutes412유지. 기존104후보/다른573fieldgroup/보호5파일/팩22파일불변. qa/field_geometry009_review.json authoritative.
- 전체게임완료·설치·실게임·최종ZIP미완료. 다음496모서리와양인접선통합,456/465/466/473줄눈·29/391/396/407기계·37/38원근구조·잔여field198/battle43/나머지캐릭터적효과컷신. GUI복구증거없어에뮬/검은캡처반복안함. outputs/field-geometry009/장식_체크_3종_복원_비교.png.
'''
for p in [R/'PROGRESS.md',C/'outputs/로컬_업스케일_진행.md']:
 with p.open('a',encoding='utf8') as f:f.write(note)
print(json.dumps({'review':str(Q),'selected':report['selected'],'field_candidates':107,'field_holds':46,'field_novel_unprocessed':198},ensure_ascii=False))
