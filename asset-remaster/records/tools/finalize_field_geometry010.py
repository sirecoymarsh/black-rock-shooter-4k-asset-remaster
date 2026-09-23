from pathlib import Path
import sys,json,hashlib,copy,shutil,importlib.util,xml.etree.ElementTree as ET,collections
sys.dont_write_bytecode=True
import numpy as np,cv2
from scipy.ndimage import gaussian_filter,map_coordinates
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];C=Path(r'C:\Users\CadriacLord\Documents\Codex\2026-09-22\brs-hd-ui-fonts');Q=R/'qa/field_geometry010_review.json';assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text('utf8'))
def write(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False),'utf8')
def arr(p):return np.asarray(Image.open(p).convert('RGBA'))
last=read(R/'qa/field_geometry009_review.json');cp=R/'qa/field_sr_catalog.json';gp=R/'qa/architectural_geometry_contract.json';cat=read(cp);before=copy.deepcopy(cat);contract=read(gp)
assert sha(cp)==last['catalog_after_sha256'] and sha(gp)==last['geometry_contract_after_sha256']
for rel,h in last['protected_file_hashes'].items():assert sha(R/rel)==h
pack=R/'workspace/local-sr/observed-review-pack-v2/PSP/TEXTURES/NPUH10126';packhash={str(p.relative_to(pack)):sha(p) for p in pack.rglob('*') if p.is_file()};assert packhash==last['pack_hashes']
old=[g['candidate'] for g in cat['groups'] if g['candidate']];assert len(old)==107
for z in old:assert sha(z['path'])==z['sha256']
reports=[read(R/'qa'/f'field_geometry010_facade496_v{i}.json') for i in [1,2]];checked=[];pages=[];line_checks=[]
for version,v in enumerate(reports,1):
 assert v['catalog_before_sha256']==sha(cp) and v['geometry_contract_before_sha256']==sha(gp)
 for k in ['source_ptm','parent','previous_rejected_output','output','mask','maps','vector','reconstruction_program']:assert sha(v[k])==v[k+'_sha256']
 s=arr(v['source']);p=arr(v['parent']);out=arr(v['output']);assert hashlib.sha256(s.tobytes()).hexdigest()==v['source_rgba_sha256'];spec=importlib.util.spec_from_file_location('frozen_facade010_'+str(version),v['reconstruction_program']);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);expected,mask,maps,records,summary=mod.build(s,p)
 assert np.array_equal(expected,out) and records==v['anchors'] and summary==v['coupling_diagnostics'];assert out.shape==(s.shape[0]*8,s.shape[1]*8,4) and np.all(out[:,:,3]==255) and np.array_equal(out[~mask],p[~mask]);assert np.array_equal(np.asarray(Image.open(v['mask'])),mask.astype('uint8')*255)
 f=np.load(v['maps'])
 for k,a in maps.items():assert np.isfinite(a).all() and np.array_equal(f[k],a)
 assert np.all(np.diff(maps['horizontal_parent_anchors'],axis=0)>0)
 elems=list(ET.parse(v['vector']).getroot().iter('{http://www.w3.org/2000/svg}line'));assert len(elems)==len(records)==15
 for el,z in zip(elems,records):
  coords=[0,z['source_y'],256,z['source_y']] if z['kind']=='horizontal_anchor' else z['source_start']+z['source_end'];assert [float(el.attrib[t]) for t in ['x1','y1','x2','y2']]==coords
 corners=summary['source_plate_corners'];lines={z['name']:z for z in records if z['kind']=='coupled_segment'};assert lines['plate-left']['source_start']==lines['plate-top']['source_start']==corners[0]
 assert lines['plate-top']['source_end']==corners[1] and lines['plate-bottom']['source_start']==corners[3] and lines['plate-bottom']['source_end']==corners[2]
 right=lines['plate-right'];assert right['source_start'][1]==94
 for corner in [corners[1],corners[2]]:assert abs(np.cross(np.asarray(right['source_end'])-right['source_start'],np.asarray(corner)-right['source_start']))<1e-10
 if version==1:assert summary['nonpositive_jacobian_pixels']==1376 and summary['coupled_map_jacobian_min']<0
 else:
  assert summary['nonpositive_jacobian_pixels']==0 and summary['coupled_map_jacobian_min']>.33
  mx=maps['coupled_mapx'];my=maps['coupled_mapy'];fy=map_coordinates(maps['horizontal_mapy'],[my,mx],order=1,mode='nearest',prefilter=False);a,b=np.gradient(mx);c,d=np.gradient(fy);jac=b*c-a*d;assert np.isfinite(jac).all() and np.all(jac>0)
  combined={'raster_grid_Jacobian_min':float(jac.min()),'nonpositive_raster_grid_Jacobian_pixels':int((jac<=0).sum()),'coupled_coordinate_bounds_xy':[float(mx.min()),float(my.min()),float(mx.max()),float(my.max())],'limit':'Finite-grid derivative check of the composed map; not a proof of every continuous subpixel point or in-game UV topology.'}
  gray={k:gaussian_filter(np.asarray(Image.open(v[k]).convert('RGB')).mean(2),1.25) for k in ['parent','output']}
  for name,line in lines.items():
   start=np.array(line['source_start']);end=np.array(line['source_end']);vec=end-start;length=np.linalg.norm(vec);t=vec/length;n=np.array([-t[1],t[0]]);pos=np.linspace(3,length-3,max(3,int(length*2)));ds=np.linspace(-1.5,1.5,121);pts=start[None,None,:]+pos[:,None,None]*t+ds[None,:,None]*n;vals={}
   for k,im in gray.items():
    sm=cv2.remap(im.astype('float32'),(pts[:,:,0]*8-.5).astype('float32'),(pts[:,:,1]*8-.5).astype('float32'),cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE);idx=np.argmin(sm,axis=1) if line['detector']=='min' else np.argmax(sm,axis=1);offs=ds[idx];vals[k]={'mean_source_px':float(offs.mean()),'RMS_source_px':float(np.sqrt(np.mean(offs**2))),'std_source_px':float(offs.std()),'max_abs_source_px':float(abs(offs).max())}
   assert vals['output']['RMS_source_px']<vals['parent']['RMS_source_px'];line_checks.append({'name':name,'samples':len(pos),'exclude_endpoints_source_px':3,'offset_measurements':vals,'RMS_improved':True})
  assert len(line_checks)==11
 checked.append({'id':v['id'],'path':v['output'],'sha256':v['output_sha256'],'decision':'rejected_invalid_coordinate_fold' if version==1 else 'static_candidate','reason':'Coupled linear displacement still folded1376 raster-grid pixels; rejected even though a corner looked visually better.' if version==1 else 'Smooth integrated coupled correction removes the former corner pinch; zero raster-grid folds and all11 sampled edge-location RMS values improve while retaining material and source sloping continuation.','source_parent_program_vector_mask_maps_output_hashes_verified':True,'frozen_recipe_RGBA_reproduced':True,'outside_mask_parent_RGBA_exact':True,'coupling_diagnostics':summary,'runtime_verified':False,'release_eligible':False})
 for pp in v['pages']:
  assert sha(pp['path'])==pp['sha256'];seen=version==2 or any(Path(pp['path']).stem.endswith('-'+tag) for tag in ['whole','left-plate','right-plate']);pages.append({**pp,'review_status':'directly_inspected_by_Codex_internal' if seen else 'not_inspected_after_coordinate_fold_failure'})
for name in ['FM0496-source.png','FM0496-lower-source-coordinate.png','FM0496-v2-left-plate.png','FM0496-v2-right-plate.png']:
 pp=R/'outputs/field-geometry008'/name;pages.append({'path':str(pp),'sha256':sha(pp),'review_status':'directly_inspected_by_Codex_internal','reused_source_or_failure_reference':True})
assert len(pages)==18 and sum(p['review_status']=='directly_inspected_by_Codex_internal' for p in pages)==14
chosen=reports[1];group=next(g for g in cat['groups'] if g['group_id']=='FM0496');assert group['status']=='held' and group['local_sr_attempted'];group.update(status='static_candidate',hold_reason=None,candidate={'id':chosen['id'],'path':chosen['output'],'sha256':chosen['output_sha256'],'review':'qa/field_geometry010_review.json','method':chosen['method'],'geometry_review':'Coupled corner/edge source controls, original right sloping continuation retained; positive finite-grid Jacobian throughout composed map, all11 sampled source-guide RMS offsets improved.','runtime_verified':False,'release_eligible':False})
for a,b in zip(before['groups'],cat['groups']):
 if a['group_id']!='FM0496':assert a==b
stats=cat['processing_summary'];stats.update(field_static_candidates=108,field_holds=45,latest_review='qa/field_geometry010_review.json');assert sum(bool(g['candidate']) for g in cat['groups'])==108 and sum(g['status']=='held' for g in cat['groups'])==45 and sum(g['local_sr_attempted'] for g in cat['groups'])==149
contract['current_batch_geometry_holds'].pop('FM0496',None);contract['geometry_review010']={'review':'qa/field_geometry010_review.json','static_candidate':{'FM0496':chosen['id']},'rejected':'FM0496-coupled-edges-v1:1376 nonpositive raster Jacobian pixels.','source_interpretation':'Source right sloping edge continues above the plate top; do not close/cap it into an undamaged trapezoid. Shared left corner target joins top and side.','new_local_passes':0,'new_external_calls':0,'new_unique_originals':0,'runtime_verified':False,'release_eligible':False}
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',16);canvas=Image.new('RGB',(1050,1020),'#25313c');dr=ImageDraw.Draw(canvas)
for row,(box,y0,label) in enumerate([(None,0,'건물 패널 전체'),((44,12,84,52),250,'수평 띠와 줄눈'),((136,88,176,128),630,'판의 모서리와 재질')]):
 for col,(path,title) in enumerate([(chosen['source'],'원본 · 단순 확대'),(chosen['parent'],'로컬 Photo'),(chosen['output'],'모서리·직선 수정')]):
  im=Image.open(path).convert('RGB')
  if box:im=im.crop(box if col==0 else tuple(t*8 for t in box))
  scale=min(320/im.width,320/im.height);pic=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST if col==0 else Image.Resampling.LANCZOS);dr.text((col*350+8,y0+8),label,font=font,fill='white');dr.text((col*350+8,y0+32),title,font=font,fill='#d0d9e2');canvas.paste(pic,(col*350+(350-pic.width)//2,y0+60))
preview=R/'outputs/field-geometry010/건물_패널_모서리_수정.png';canvas.save(preview);localpreview=C/'outputs'/preview.name;shutil.copy2(preview,localpreview)
# Preserve a compact source-backed routing list for the remaining actual scope.
source_rows={};source_reports={}
for pth in sorted((R/'qa').glob('field_source_review0*.json')):
 source_reports[str(pth.relative_to(R))]=sha(pth)
 for r in read(pth).get('files',[]):source_rows[r['group_id']]=r
pending=[g for g in cat['groups'] if g['status']=='not_processed_in_field_context' and not g['battle_pixel_equivalent_group']];assert len(pending)==198;routes=[{'group_id':g['group_id'],'classification':source_rows[g['group_id']]['classification'],'source_visual_note':source_rows[g['group_id']].get('source_visual_note'),'size':[g['width'],g['height']]} for g in pending];routing={'schema':'brs-pending-field-routing010/v1','source_reports_sha256':source_reports,'novel_unprocessed':198,'classification_counts':dict(collections.Counter(r['classification'] for r in routes)),'groups':routes,'next_bounded_batch':[r['group_id'] for r in routes if r['classification']=='alpha_foliage'],'next_method':'Local RGB comparison with separately source-preserved alpha; inspect thin stems, holes and faint support against both dark/light mattes. Do not infer alpha with the RGB model or treat illustration/sign identity as generic material.'};rp=R/'qa/field_pending_routing010.json';write(rp,routing)
backup=R/'qa/backups/before-field-geometry010-review';backup.mkdir(exist_ok=False)
for pth in [cp,gp]:shutil.copy2(pth,backup/pth.name)
write(cp,cat);write(gp,contract)
report={'schema':'brs-field-geometry010-final-review/v1','batch':'FIELD-GEOMETRY-010','previous_goal_turn_classification':chosen['previous_goal_turn_classification'],'this_goal_turn_classification':'progress: coupled facade corner reconstruction; invalid folding trial rejected, integrated correction verified and one hold resolved. Remaining198 field routes recorded for a bounded alpha-foliage batch.','selected':{'FM0496':chosen['id']},'checked_outputs':checked,'geometry_diagnostics':{'composed_map':combined,'line_checks':line_checks,'measurement_limit':'Source-guide offset from local grayscale extrema, evaluated away from endpoints; grain and source ambiguity affect measured residual. Not a claim of perfectly straight every-pixel material boundaries or native high-resolution ground truth.'},'new_local_neural_unique_originals':0,'new_geometry_only_unique_originals':0,'new_direct_GPT_only_unique_originals':0,'new_local_inference_passes':0,'external_generative_calls':0,'source_reports_sha256':{f'qa/field_geometry010_facade496_v{i}.json':sha(R/'qa'/f'field_geometry010_facade496_v{i}.json') for i in [1,2]},'source_and_comparison_pages':pages,'pages_directly_inspected':14,'catalog_before_sha256':last['catalog_after_sha256'],'catalog_after_sha256':sha(cp),'geometry_contract_before_sha256':last['geometry_contract_after_sha256'],'geometry_contract_after_sha256':sha(gp),'other575_field_groups_unchanged':True,'previous107_field_candidates_unchanged':True,'field_processing_summary':stats,'unique_local_neural_originals_title_battle_novel_field':406,'processed_originals_title_battle_novel_field_all_routes':412,'all_routes_count_basis':{'title':1,'battle':258,'novel_field':153},'protected_file_hashes':last['protected_file_hashes'],'pack_hashes':packhash,'pending_routing':{'path':str(rp),'sha256':sha(rp)},'preview':{'path':str(localpreview),'project_path':str(preview),'sha256':sha(preview),'review_status':'pending_direct_inspection'},'runtime_verified':False,'release_eligible':False,'all_game_complete':False,'limits':['The rejected v1 has finite reproducible data but1376 locally reversed coordinate samples. Its better-looking corner did not justify acceptance.','v2 composed finite-grid Jacobian minimum.33748, zero nonpositive pixels; maximum integrated movement1.39323source px. No formal continuous or runtime UV proof claimed.','All11 sampled guide RMS values improve; residuals include source/material roughness and reach.380source px on the lower-left rail. Geometry controls do not guarantee perfectly straight every-pixel grayscale thresholds.','Original Photo material is resampled; source RGB values are not claimed unchanged inside the affected region. Alpha255 and mask-exterior parent bytes are exact.','Field45 holds/198 novel unprocessed,43 battle issues, historical57field/241battle geometry-applicability checks and other source populations remain.','No new neural/GPT call, texture key, installation, emulator launch, gameplay proof or release ZIP. GUI unavailable, no successful Explorer claim.'],'next_action':'Run the9 source-classified alpha-foliage originals as a bounded local RGB comparison batch with explicit alpha preservation and dual-matte/thin-support checks. Continue all remaining architecture/mechanical/identity/FX populations; source pixels and GUI/runtime limitations do not narrow the original goal.','scripts':{n:sha(R/'tools'/n) for n in ['rectify_field496_coupled010.py','rectify_field496_coupled010_v2.py','finalize_field_geometry010.py']}}
for rel,h in last['protected_file_hashes'].items():assert sha(R/rel)==h
assert {str(p.relative_to(pack)):sha(p) for p in pack.rglob('*') if p.is_file()}==packhash
write(Q,report)
note='''

## 2026-09-23 — FIELD-GEOMETRY-010 / 건물 패널 모서리 통합 보정
- 이전009 progress. 이번기존496보류1종해결과잔여198route정리로progress. 새로컬추론·GPT·고유원본0. 전체목표active.
- 008개별strip보정은왼모서리삼각pinch,median단면은재질평탄화로불채택했던것. 이번원본11segment/sharedcorner를하나의2D최소제곱변위로해석. v1 외관은나아도Jacobian<=0픽셀1376/min-1.65168이라불채택.
- v2같은field를nativeσ3부드러운velocity로바꾸고경계16pxfade/7회scaling-squaring 적분. 합성map전체finite-gridJacobian최소.33748/접힘0,최대이동1.39323source px. 물리연속공간/실게임증거아님. 기존Photo재질좌표만이동하며painted단면안씀.
- 원본오른사선은판윗변보다위sourcey94까지이어짐. 완전닫힌정상trapezoid로자르지않고연장유지. 왼상단모서리/인접선sharedtarget로함께보정. 7비교페이지전체직접검수후v2정적후보.
- 11선내부(endpoint3source px제외)grayscale극값sourceguide RMS모두감소. upper-left.129→.054,recess.102→.052,plate-left.478→.277,plate-right.358→.200,plate-top.359→.293,plate-bottom.772→.305,lower-left.960→.380source px. 미세재질/원본모호성잔여이며모든RGBpixel완벽직선주장안함.
- 두출력source/PTM/parent/previousfailure/vector/mask/maps/frozenprogram/output해시·RGBArecipe재현·mask밖parentRGBA정확·alpha255. 전체18source/비교중14직접검수,수치fold실패v1중복4미검수. qa/field_geometry010_review.json authoritative.
- field108후보/45보류/198novel미처리. local149/directGPT-only3/geometry-only1/전체153그대로. 전체조사범위local406/allroutes412. 기존107후보/다른575fieldgroup/보호5파일/팩22파일불변.
- 남은198은alphaornament17/alphamechanical16/flatgeometry14/identitytext11/architecture10/alphafoliage9등구조·투명도·원화보호대상. qa/field_pending_routing010.json에전체ID/classification보존. 다음9alphafoliage로컬RGB비교+원본alpha별도/양배경/줄기·구멍검수,나머지45보류/198원본·battle43·기타게임범위계속.
- 설치/실게임/최종ZIP미완료,GUI복구증거없어에뮬/검은캡처반복없음. outputs/field-geometry010/건물_패널_모서리_수정.png.
'''
for pth in [R/'PROGRESS.md',C/'outputs/로컬_업스케일_진행.md']:
 with pth.open('a',encoding='utf8') as f:f.write(note)
print(json.dumps({'selected':report['selected'],'field_candidates':108,'field_holds':45,'novel_unprocessed':198,'next_alpha_foliage_ids':routing['next_bounded_batch']},ensure_ascii=False))
