"""Verify saved inference/geometry recipes and publish the bounded008 review."""
from pathlib import Path
import sys,json,hashlib,copy,shutil,importlib.util,xml.etree.ElementTree as ET
sys.dont_write_bytecode=True
import numpy as np
from PIL import Image,ImageFilter,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1]
C=Path(r'C:\Users\CadriacLord\Documents\Codex\2026-09-22\brs-hd-ui-fonts')
Q=R/'qa/field_geometry008_review.json'
assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text('utf8'))
def write(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False),'utf8')
def arr(p,mode='RGBA'):return np.asarray(Image.open(p).convert(mode))
def source(v):
 assert sha(v['source_ptm'])==v['source_ptm_sha256']
 s=arr(v['source']);assert hashlib.sha256(s.tobytes()).hexdigest()==v['source_rgba_sha256'];return s
def hashes(v,keys):
 for k in keys:assert sha(v[k])==v[k+'_sha256'],(v.get('id'),k)
last=read(R/'qa/field_geometry007_review.json')
names=['field_geometry008_source_audit.json','field_geometry008_local.json','field_geometry008_checker489.json','field_geometry008_facade496_v1.json','field_geometry008_facade496_v2.json']
reports={n:read(R/'qa'/n) for n in names};audit,local,gold,f1,f2=[reports[n] for n in names]
cp=R/'qa/field_sr_catalog.json';gp=R/'qa/architectural_geometry_contract.json'
cat=read(cp);before=copy.deepcopy(cat);contract=read(gp)
assert sha(cp)==last['catalog_after_sha256']==audit['catalog_before_sha256']
assert sha(gp)==last['geometry_contract_after_sha256']==audit['geometry_contract_before_sha256']
assert sha(R/'qa/checker_design_contract.json')==audit['checker_contract_sha256']
for rel,h in last['protected_file_hashes'].items():assert sha(R/rel)==h
pack=R/'workspace/local-sr/observed-review-pack-v2/PSP/TEXTURES/NPUH10126'
packhash={str(p.relative_to(pack)):sha(p) for p in pack.rglob('*') if p.is_file()}
assert packhash==last['pack_hashes'] and len(packhash)==22
oldcandidates=[g['candidate'] for g in cat['groups'] if g['candidate']]
assert len(oldcandidates)==102
for v in oldcandidates:assert sha(v['path'])==v['sha256']
for v in audit['files']:source(v)
for rep in [local,gold,f1,f2]:assert rep['source_audit_sha256']==sha(R/'qa'/names[0])
assert f2['previous_report_sha256']==sha(R/'qa/field_geometry008_facade496_v1.json')
assert local['actual_local_RGB_passes']==14 and len(local['completed_components'])==14
assert local['new_neural_unique_originals']==4 and local['alpha_passes']==0 and local['external_calls']==0
components={v['id']:v for v in local['completed_components']};seen=set();checked=[];means=[]
reasons={
 'FM0394':'Both local models bevel flat checker cells and warp corner/border geometry. Rebuild the source checker separately from surrounding damage.',
 'FM0430':'WDN rounds checker cells; Photo introduces net-like connections and overinterprets the surface. Four source checker patches, including the clipped lower-right patch, need protected reconstruction.',
 'FM0444':'Both models partly replace faint checker patches with mesh/scratches. Preserve the original four visible patches and their faded colors.',
 'FM0496':'v1 source row sections flatten stone into shade bands. v2 retains material and improves horizontal bands but creates a triangular pinch/fold at the lower-left plate corner. Held: coupled corner/edge reconstruction is required; independent strip warps and added grain are not sufficient.'}
for v in local['files']:
 s=source(v);src=Image.fromarray(s);h,w=s.shape[:2];hashes(v,['native','output']);assert sha(v['model']['path'])==v['model']['sha256']
 expected=Image.new('RGBA',(w*8,h*8));nativewhole=Image.new('RGB',(w*4,h*4));coverage=np.zeros((h,w),np.uint8)
 for z in v['components']:
  origin=components[z['id']];assert all(z[k]==val for k,val in origin.items());seen.add(z['id']);hashes(z,['input','native_full']);assert z['model']==v['model'] and z['actual_RGB_passes']==1
  x0,y0,x1,y1=z['source_box'];patch=src.crop(z['source_box']).convert('RGB');pad=z['reflect_padding_source_px'];sigma=z['prefilter_sigma_source'];pre=np.asarray(patch.filter(ImageFilter.GaussianBlur(sigma)))
  assert (pad,sigma)==((8,.35) if v['group_id']=='FM0498' else (0,.25))
  inp=np.pad(pre,((pad,pad),(pad,pad),(0,0)),mode='reflect') if pad else pre
  assert np.array_equal(inp,arr(z['input'],'RGB'))
  nf=Image.open(z['native_full']).convert('RGB');assert nf.size==((patch.width+2*pad)*4,(patch.height+2*pad)*4)
  native=nf.crop((pad*4,pad*4,(pad+patch.width)*4,(pad+patch.height)*4));piece=native.resize((patch.width*8,patch.height*8),Image.Resampling.LANCZOS)
  if v['group_id']=='FM0498':
   a=np.asarray(piece).astype('float32');target=np.asarray(patch).mean((0,1));offset=target-a.mean((0,1));assert offset.tolist()==z['mean_RGB_offset_after_resize'] and target.tolist()==z['source_mean_RGB']
   piece=Image.fromarray(np.rint(np.clip(a+offset,0,255)).astype('uint8'));outmean=np.asarray(piece).mean((0,1));assert outmean.tolist()==z['output_mean_RGB']
   means.append({'id':z['id'],'source_mean_RGB':target.tolist(),'output_mean_RGB':outmean.tolist(),'max_mean_error_RGB':float(abs(target-outmean).max())})
  nativewhole.paste(native,(x0*4,y0*4));expected.paste(piece.convert('RGBA'),(x0*8,y0*8));coverage[y0:y1,x0:x1]+=1
 assert np.all(coverage==1) and np.array_equal(np.asarray(expected),arr(v['output'])) and np.array_equal(np.asarray(nativewhole),arr(v['native'],'RGB'))
 chosen=v['id']=='FM0498-wdn'
 reason='Four source cells reconstructed independently, straight source cross boundary retained; WDN stone grain selected.' if chosen else 'Photo invents dark brick/step-like internal structures.' if v['group_id']=='FM0498' else reasons[v['group_id']]
 checked.append({'id':v['id'],'path':v['output'],'sha256':v['output_sha256'],'decision':'static_candidate' if chosen else 'not_selected','reason':reason,'source_model_input_native_output_hashes_verified':True,'saved_native_postprocess_RGBA_reproduced':True,'full_source_cell_coverage_once':True,'runtime_verified':False,'release_eligible':False})
assert seen==set(components) and len(checked)==8 and sum(v['actual_RGB_passes'] for v in local['files'])==14
assert max(m['max_mean_error_RGB'] for m in means if m['id'].startswith('FM0498-wdn'))<.5

s=source(gold);hashes(gold,['output','vector','mask']);assert s.shape==(32,32,4)
out=arr(gold['output']);reconstructed=np.zeros((256,256,4),np.uint8);coverage=np.zeros((32,32),np.uint8);goldmask=np.zeros((256,256),bool)
rects=list(ET.parse(gold['vector']).getroot().iter('{http://www.w3.org/2000/svg}rect'));assert len(rects)==8 and len(gold['cells'])==16
rectindex=0
for cell in gold['cells']:
 x,y=cell['column'],cell['row'];box=[x*8,y*8,(x+1)*8,(y+1)*8];assert box==cell['source_box'];a=s[y*8:(y+1)*8,x*8:(x+1)*8]
 if (x+y)%2==0:
  assert cell['kind']=='solid_gold' and np.all(a==[255,209,105,255]);piece=np.full((64,64,4),[255,209,105,255],np.uint8);goldmask[y*64:(y+1)*64,x*64:(x+1)*64]=True
  el=rects[rectindex];rectindex+=1;assert [float(el.attrib[t]) for t in ['x','y','width','height']]==[x*8,y*8,8,8]
 else:
  assert cell['kind']=='translucent_red_gradient' and np.all(a[:,:,3]==64);rgb=np.asarray(Image.fromarray(a[:,:,:3]).resize((64,64),Image.Resampling.BILINEAR));piece=np.dstack([rgb,np.full((64,64),64,np.uint8)])
 reconstructed[y*64:(y+1)*64,x*64:(x+1)*64]=piece;coverage[y*8:(y+1)*8,x*8:(x+1)*8]+=1
assert np.array_equal(out,reconstructed) and np.all(coverage==1)
assert np.array_equal(out[:,:,3],np.repeat(np.repeat(s[:,:,3],8,0),8,1))
assert np.array_equal(arr(gold['mask'])[:,:,3]==255,goldmask) and goldmask.sum()==32768
checked.append({'id':gold['id'],'path':gold['output'],'sha256':gold['output_sha256'],'decision':'static_candidate','reason':'Source4x4 checker: exact gold RGB/alpha and grid; red gradient interpolated within each cell without crossing boundaries. No neural inference.','source_vector_mask_output_hashes_verified':True,'source_recipe_RGBA_reproduced':True,'source_alpha_nearest8x_exact':True,'runtime_verified':False,'release_eligible':False})

for num,v in [(1,f1),(2,f2)]:
 s=source(v);keys=['parent','output','mask','vector','reconstruction_program']+(['frozen_planes'] if num==1 else ['maps']);hashes(v,keys)
 p=arr(v['parent']);out=arr(v['output']);spec=importlib.util.spec_from_file_location('frozen_geometry008_'+str(num),v['reconstruction_program']);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);rebuilt=module.build(s,p);assert np.array_equal(rebuilt[0],out)
 mask=arr(v['mask'],'L')==255;assert np.array_equal(rebuilt[1],mask) and np.array_equal(out[~mask],p[~mask]) and np.all(out[:,:,3]==255) and out.shape==(s.shape[0]*8,s.shape[1]*8,4)
 frozen=np.load(v['frozen_planes'] if num==1 else v['maps']);records=rebuilt[3];assert records==(v['regions'] if num==1 else v['anchors'])
 if num==1:
  assert np.array_equal(frozen['classes'],rebuilt[2]);data=rebuilt[4];xml=ET.parse(v['vector']).getroot();rs=list(xml.iter('{http://www.w3.org/2000/svg}rect'));ls=list(xml.iter('{http://www.w3.org/2000/svg}line'));assert len(rs)==3 and len(ls)==11
  for el,z in zip(rs,records[:3]):
   y0,y1=z['source_y_range'];assert [float(el.attrib[t]) for t in ['x','y','width','height']]==[0,y0,256,y1-y0]
  for el,z in zip(ls,records[3:]):assert [float(el.attrib[t]) for t in ['x1','y1','x2','y2']]==z['source_start']+z['source_end']
 else:
  data=rebuilt[2];assert np.all(np.diff(data['horizontal_parent_anchors'],axis=0)>0);ls=list(ET.parse(v['vector']).getroot().iter('{http://www.w3.org/2000/svg}line'));assert len(ls)==15
  for el,z in zip(ls,records):
   coords=[0,z['source_y'],256,z['source_y']] if z['kind']=='horizontal_anchor' else z['source_start']+z['source_end'];assert [float(el.attrib[t]) for t in ['x1','y1','x2','y2']]==coords
 for k,a in data.items():assert np.isfinite(a).all() and np.array_equal(frozen[k],a)
 checked.append({'id':v['id'],'path':v['output'],'sha256':v['output_sha256'],'decision':'not_selected','reason':v.get('v1_rejected_reason',reasons['FM0496']) if num==1 else reasons['FM0496'],'source_parent_vector_mask_frozen_program_output_hashes_verified':True,'frozen_recipe_RGBA_reproduced':True,'outside_mask_parent_RGBA_exact':True,'runtime_verified':False,'release_eligible':False})
assert len(checked)==11 and sum(v['decision']=='static_candidate' for v in checked)==2
pages=[]
for name,rep in reports.items():
 for v in rep['pages']:
  assert sha(v['path'])==v['sha256'];skip=name=='field_geometry008_facade496_v1.json' and any(tag in Path(v['path']).stem for tag in ['left-plate','right-plate','right-joints'])
  pages.append({**v,'review_status':'not_inspected_redundant_after_whole_material_failure' if skip else 'directly_inspected_by_Codex_internal','evidence_report':name})
extra=R/'outputs/field-geometry008/FM0496-lower-source-coordinate.png';assert extra.exists();pages.append({'path':str(extra),'sha256':sha(extra),'review_status':'directly_inspected_by_Codex_internal','purpose':'Source lower plate/joint coordinates.'})
assert len(pages)==28 and sum(v['review_status']=='directly_inspected_by_Codex_internal' for v in pages)==25

selected={'FM0498':next(v for v in local['files'] if v['id']=='FM0498-wdn'),'FM0489':gold}
for g in cat['groups']:
 gid=g['group_id']
 if gid in ['FM0394','FM0430','FM0444','FM0498']:
  assert not g['local_sr_attempted'] and g['status']=='not_processed_in_field_context';g['local_sr_attempted']=True
 if gid in selected:
  v=selected[gid];g.update(status='static_candidate',hold_reason=None,candidate={'id':v['id'],'path':v['output'],'sha256':v['output_sha256'],'review':'qa/field_geometry008_review.json','method':v['method'],'runtime_verified':False,'release_eligible':False})
  if gid=='FM0489':g.update(geometry_processed=True,processing_route='deterministic_checker_cells')
 elif gid in reasons:g.update(status='held',hold_reason=reasons[gid])
changed=set(reasons)|set(selected)
for a,b in zip(before['groups'],cat['groups']):
 if a['group_id'] not in changed:assert a==b
assert len(changed)==6
stats=cat['processing_summary'];stats.update(field_neural_originals=149,field_static_candidates=104,field_holds=49,field_groups_not_processed_in_field_context=423,remaining_novel_unprocessed=198,field_direct_gpt_only_originals=3,field_geometry_only_originals=1,field_processed_novel_originals_all_routes=153,latest_review='qa/field_geometry008_review.json',counting_note='Cumulative novel field processing:149 locally inferred +3 direct-GPT-only +1 deterministic-geometry-only =153 originals. Repeated inference, retries and geometry derivatives of already processed originals do not add unique originals. Static candidates and holds include all routes.')
assert sum(bool(g['candidate']) for g in cat['groups'])==104 and sum(g['status']=='held' for g in cat['groups'])==49 and sum(g['local_sr_attempted'] for g in cat['groups'])==149
assert sum(g['status']=='not_processed_in_field_context' for g in cat['groups'])==423
battle=read(R/'qa/battle_sr_catalog.json')['processing_summary'];assert battle['battle_groups_locally_processed']==256 and battle['battle_groups_processed_any_method']==258 and battle['battle_geometry_only_groups_processed']==2
for gid,reason in reasons.items():contract['current_batch_geometry_holds'][gid]=reason
contract['geometry_review008']={'review':'qa/field_geometry008_review.json','static_candidates':{k:v['id'] for k,v in selected.items()},'new_holds':['FM0394','FM0430','FM0444'],'existing_hold_reworked_not_resolved':'FM0496','field_checker_review':'qa/field_checker_design_review008.json','new_local_inference_passes':14,'new_local_unique_originals':4,'new_geometry_only_unique_originals':1,'new_external_calls':0,'runtime_verified':False,'release_eligible':False}
checker={'schema':'brs-field-checker-design-review008/v1','parent_contract':'qa/checker_design_contract.json','parent_contract_sha256':audit['checker_contract_sha256'],'protected_parent_unchanged':True,'accepted_static':{'FM0498':'2x2 source cell locations/phase preserved through isolated local inference; WDN material chosen. Native4x + per-cell Lanczos2x, with RGB mean recenter.','FM0489':'4x4 source rectangular cells, exact gold255/209/105/255; original red cells alpha64 retained with per-cell bilinear gradients. Deterministic geometry, not AI.'},'held':{k:reasons[k] for k in ['FM0394','FM0430','FM0444']},'source_interpretation_corrections':['FM0430 has four visible checker patches including the clipped lower-right patch, rather than three. FM0444 also has four visible patches; similarity does not prove shared consumers.','FM0489 source cells are gold and translucent dark red. The earlier gray visual label depended on display matte.'],'material_cell_mean_diagnostics':means,'limits':'Geometry/alpha and material comparison are offline checks, not evidence of exact high-resolution ground truth, game UV consumers or runtime alpha-test behavior.','runtime_verified':False,'release_eligible':False}

# A compact review artifact, not a game texture edit.
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18);small=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',15);can=Image.new('RGB',(720,805),'#25313c');d=ImageDraw.Draw(can)
for row,(gid,title,note) in enumerate([('FM0498','돌 재질 · 큰 체크','칸별 로컬 AI 처리 · 경계 고정'),('FM0489','금색 체크 · 원본 투명도','원본 도형 직접 재구성 · AI 처리 없음')]):
 v=selected[gid];basey=row*400;d.text((18,basey+12),title,font=font,fill='white');d.text((18,basey+41),note,font=small,fill='#ccd6de')
 for col,(path,label) in enumerate([(v['source'],'원본 · 단순 확대'),(v['output'],'수정 후보')]):
  im=Image.open(path).convert('RGBA').resize((304,304),Image.Resampling.NEAREST if col==0 or gid=='FM0489' else Image.Resampling.LANCZOS);bg=Image.new('RGBA',im.size,'#202830');bg.alpha_composite(im);x=18+col*354;d.text((x,basey+70),label,font=small,fill='white');can.paste(bg.convert('RGB'),(x,basey+96))
preview=R/'outputs/field-geometry008/체크_경계와_재질_수정.png';can.save(preview);localpreview=C/'outputs'/preview.name;shutil.copy2(preview,localpreview)
review={'schema':'brs-field-geometry008-final-review/v1','batch':'FIELD-GEOMETRY-008','previous_goal_turn_classification':audit['previous_goal_turn_classification'],'this_goal_turn_classification':'progress: five new originals processed, two static checker candidates; three new checker holds; two existing-facade corrections rejected.','selected':{k:v['id'] for k,v in selected.items()},'new_holds':['FM0394','FM0430','FM0444'],'existing_hold_unresolved':'FM0496','checked_outputs':checked,'new_local_neural_unique_originals':4,'new_geometry_only_unique_originals':1,'new_direct_GPT_only_unique_originals':0,'new_local_inference_passes':14,'alpha_neural_passes':0,'external_generative_calls':0,'source_reports_sha256':{str((R/'qa'/n).relative_to(R)):sha(R/'qa'/n) for n in names},'source_and_comparison_pages':pages,'pages_directly_inspected':25,'raw489_output_also_directly_inspected':True,'catalog_before_sha256':sha(cp),'geometry_contract_before_sha256':sha(gp),'other570_field_groups_unchanged':True,'previous102_field_candidates_unchanged':True,'field_processing_summary':stats,'unique_local_neural_originals_title_battle_novel_field':406,'processed_originals_title_battle_novel_field_all_routes':412,'all_routes_count_basis':{'title':1,'battle':258,'novel_field':153},'counting_correction':'Earlier405 including direct GPT was local402 +directGPT3 and omitted two historical battle geometry-only originals BM200/BM269. Actual prior all-routes total was407. This batch adds five field originals, not seven.','protected_file_hashes':last['protected_file_hashes'],'pack_hashes':packhash,'preview':{'path':str(localpreview),'project_path':str(preview),'sha256':sha(preview),'review_status':'pending_direct_inspection'},'runtime_verified':False,'release_eligible':False,'all_game_complete':False,'limits':['FM0394/0430/0444 local material does not preserve the checker design; all six trials remain unselected.','FM0496 v1/v2 recipes reproduce correctly, but visual defects remain. Reproducibility is not visual acceptance. Corner intersections need a coupled reconstruction.','FM0498 WDN per-cell mean RGB differs from source by less than0.5 per channel after rounding/clipping; it is not exact RGB preservation.','FM0489 is direct deterministic reconstruction with bilinear interpolation confined to red cells; it is not a neural upscale.','Historical57 field/241 battle candidates still need geometry-applicability review. Field49 holds/198 novel unprocessed, battle43 unresolved and other game populations remain.','No installation, PPSSPP launch, gameplay verification, new texture keys or release ZIP. Native GUI remains unavailable; no successful Explorer/visible preview claim.'],'next_action':'Reconstruct held checker layouts394/430/444 from source; treat496 corners jointly with adjoining edges. Continue remaining structured props/masonry/field originals, battle issues and game populations. Runtime integration remains a later gate.','scripts':{n:sha(R/'tools'/n) for n in ['audit_field_geometry008.py','local_field_checker008.py','rebuild_field489_008.py','rebuild_field496_008.py','rectify_field496_008_v2.py','finalize_field_geometry008.py']}}
backup=R/'qa/backups/before-field-geometry008-review';backup.mkdir(exist_ok=False)
for p in [cp,gp]:shutil.copy2(p,backup/p.name)
write(cp,cat);write(gp,contract);write(R/'qa/field_checker_design_review008.json',checker)
review.update(catalog_after_sha256=sha(cp),geometry_contract_after_sha256=sha(gp),field_checker_design_review_sha256=sha(R/'qa/field_checker_design_review008.json'))
for rel,h in last['protected_file_hashes'].items():assert sha(R/rel)==h
assert {str(p.relative_to(pack)):sha(p) for p in pack.rglob('*') if p.is_file()}==packhash
write(Q,review)
note='''

## 2026-09-23 — FIELD-GEOMETRY-008 / 체크 경계·색·투명도와 건물 모서리
- 이전007 progress. 이번 신규5원본 중 로컬4종/실제RGB추론14회, 직접geometry-only1종. 외부생성0/alpha추론0. 전체목표active.
- 394/430/444 두 로컬모델6출력 모두 보류: 평면 체크가 볼록한 타일·그물·흠집으로 변형됨. 430원본 체크는 잘린우하단포함4영역으로 이전3영역기록정정. 444도4영역, 동일소비자증거아님.
- 498 4칸 각각 Gaussian.35/reflect8source padding→실제local4x→crop→칸별Lanczos2x→원본RGB평균보정. WDN 채택, Photo 내부벽돌/단차형태과해불채택. 경계/위상 정확, 평균RGB채널오차0.5미만이며RGB완전동일은아님.
- 489 4x4 직접원본도형. 금색RGBA255/209/105/255 정확, 붉은칸은 원본alpha64/칸별bilinear. alpha원본NN8x정확, goldmask32768픽셀,16칸1회coverage. 회색이라는 이전표시는배경합성영향이라정정. 새AI아닌직접geometry-only1종.
- 496 v1 원본median단면3띠/11선은 재질을평평한음영띠로바꿔실패. v2 원본anchor로기존Photo좌표보정은재질보존/가로선개선됐으나하단왼모서리에새삼각꺾임. 둘불채택/기존held유지. 다음은교차모서리·양인접선을함께맞추며 grain추가/독립띠warp반복안함.
- 출력11(로컬8+4891+4962) source/model/input/native/output/vector/mask/frozenprogram해시와저장recipeRGBA재현. source/비교28페이지중25직접검수, v1실패후중복하단3미검수. raw489별도직접검수. qa/field_geometry008_review.json authoritative. 보호5파일/관측팩22파일/기존102후보/다른570fieldgroup불변.
- field104정적후보/49보류/198novel미처리. local149+directGPT-only3+geometry-only1=153처리, field문맥미처리423에는battle동일225포함. 전체고유local406. 모든방식title1+battle258+novelfield153=412. 이전405는역사적battlegeometry-only2(BM200/BM269)누락한합계였으며이번신규는5종이지7종이아님.
- 설치/실게임검수/최종ZIP미완료,전체완료율미산정. 잔여field·battle43·인물/적/효과/컷신및미지원원본계속. GUI복구증거없어컴퓨터유즈실행/검은캡처반복없음. 사용자이번묶음마무리ETA15~30분안내,전체ETA확답안함.
- 다음394/430/444체크sourcegeometry,496corner연결구조및기존29/37/38·masonry구조보류와잔여field198. outputs/field-geometry008/체크_경계와_재질_수정.png.
'''
with (R/'PROGRESS.md').open('a',encoding='utf8') as f:f.write(note)
with (C/'outputs/로컬_업스케일_진행.md').open('a',encoding='utf8') as f:f.write(note)
print(json.dumps({'review':str(Q),'selected':review['selected'],'field':stats,'local_unique':406,'all_routes_unique':412,'preview':str(preview)},ensure_ascii=False))
