"""Verify saved facade recipes and adopt only the visually accepted metal facade."""
import copy,hashlib,json,shutil,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np,cv2
from PIL import Image
from scipy.ndimage import gaussian_filter,gaussian_filter1d
from scipy.signal import find_peaks
R=Path(__file__).resolve().parents[1];C=Path(r'C:\Users\CadriacLord\Documents\Codex\2026-09-22\brs-hd-ui-fonts');Q=R/'qa/field_geometry002_review.json';assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text('utf8'))
def arr(p):return np.asarray(Image.open(p).convert('RGBA'))
def write(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2),'utf8')
paths=[R/'qa'/n for n in ['field_geometry002_trials.json','field_geometry002_rectification.json','field_geometry002_planes_v3.json','field_geometry002_bevels_v4.json']]
reports=[read(p) for p in paths];one,two,three,four=reports;last=read(R/'qa/field_geometry001_review.json')
catpath=R/'qa/field_sr_catalog.json';contractpath=R/'qa/architectural_geometry_contract.json';cat=read(catpath);before=copy.deepcopy(cat);contract=read(contractpath)
assert sha(catpath)==one['catalog_before_sha256']==last['catalog_after_sha256']
assert sha(contractpath)==one['geometry_contract_before_sha256']==last['geometry_contract_after_sha256']
for rel,h in last['protected_file_hashes'].items():assert sha(R/rel)==h
pack=R/'workspace/local-sr/observed-review-pack-v2/PSP/TEXTURES/NPUH10126';packhashes={str(p.relative_to(pack)):sha(p) for p in pack.rglob('*') if p.is_file()};assert packhashes==last['pack_hashes']
checked=[];pages=[]
for version,report in enumerate(reports,1):
 for page in report['pages']:
  assert sha(page['path'])==page['sha256']
  inspected=version>=3 or '-whole-' in page['path']
  pages.append({**page,'review_status':'directly_inspected' if inspected else 'not_needed_after_whole_image_rejection'})
 for v in report['files']:
  gid=v['group_id'];source=arr(v['source']);p=arr(v['parent']);out=arr(v['output'])
  assert source.shape==(128,64,4) and out.shape==(1024,512,4)
  assert hashlib.sha256(source.tobytes()).hexdigest()==v['source_rgba_sha256']
  for key in ['source_ptm','parent','output','region_classmap','vector','render','maps','changed_mask','material_parent','profiles','geometry_parent','mask']:
   if key in v:assert sha(v[key])==v[key+'_sha256'],(v['id'],key)
  assert np.all(out[:,:,3]==255)
  v1=next(z for z in one['files'] if z['group_id']==gid)
  if version==1:
   rebuilt=arr(v['render']).copy();coverage=np.zeros(out.shape[:2],np.uint8);classes=np.zeros(out.shape[:2],np.uint8)
   rects=list(ET.parse(v['vector']).getroot().iter('{http://www.w3.org/2000/svg}rect'));assert len(rects)==len(v['regions'])
   grain=p[:,:,:3].astype('float32')-gaussian_filter(p[:,:,:3].astype('float32'),(8,8,0),mode='nearest')
   for i,(z,rect) in enumerate(zip(v['regions'],rects),1):
    x0,y0,x1,y1=z['box'];a,b,c,d=[t*8 for t in z['box']];kind=z['kind'];coverage[b:d,a:c]+=1;classes[b:d,a:c]=i
    assert not any(k in rect.attrib for k in ['rx','ry','transform'])
    assert [int(rect.attrib[k]) for k in ['x','y','width','height']]==[x0,y0,x1-x0,y1-y0]
    if kind=='glass':
     pad=8;inner=p[b:d,a:c,:3][pad:-pad,pad:-pad];rebuilt[b:d,a:c,:3]=np.minimum(cv2.copyMakeBorder(inner,pad,pad,pad,pad,cv2.BORDER_REPLICATE),z['glass_ceiling']);continue
    if kind=='surface':material=cv2.resize(gaussian_filter(source[y0:y1,x0:x1,:3].astype('float32'),(.55,.55,0),mode='nearest'),(c-a,d-b),interpolation=cv2.INTER_CUBIC)
    elif kind=='shutter':
     patch=source[y0:y1,x0:x1,:3].astype('float32');rows=np.median(patch,axis=1);cols=np.median(patch,axis=0);gain=cols/np.maximum(cols.mean(0),1)
     assert np.array_equal(rows,np.asarray(z['row_profile_rgb'])) and np.array_equal(gain,np.asarray(z['column_gain']))
     material=cv2.resize(rows[:,None,:]*gain[None,:,:],(c-a,d-b),interpolation=cv2.INTER_LINEAR)
    else:
     xx0,xx1=z.get('profile_sample_x',[x0,x1]);patch=source[y0:y1,xx0:xx1,:3].astype('float32');profile=np.median(patch,axis=1 if kind=='horizontal' else 0)
     assert np.array_equal(profile,np.asarray(z['profile_rgb']));material=rebuilt[b:d,a:c,:3].astype('float32')
    rebuilt[b:d,a:c,:3]=np.rint(np.clip(material+np.clip(grain[b:d,a:c]*.25,-z['grain'],z['grain']),0,255)).astype('uint8')
   assert np.all(coverage==1) and np.array_equal(classes,np.asarray(Image.open(v['region_classmap'])))
  elif version==2:
   maps=np.load(v['maps']);mx=maps['map_x'];my=maps['map_y'];yy,xx=np.mgrid[:1024,:512].astype('float32')
   assert np.all(np.isfinite(mx)) and np.all(np.isfinite(my));assert np.all(np.diff(mx,axis=1)>0) and np.all(np.diff(my,axis=0)>0)
   rebuilt=cv2.remap(cv2.remap(p,mx,yy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE),xx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
   assert np.array_equal(np.any(rebuilt!=p,axis=2),np.asarray(Image.open(v['changed_mask']))>0)
  elif version==3:
   local=arr(v['material_parent']);rebuilt=local.copy();profiles=np.load(v['profiles']);grain=local[:,:,:3].astype('float32')-gaussian_filter(local[:,:,:3].astype('float32'),(4,4,0),mode='nearest')
   for z,base in zip(v['regions'],v1['regions']):
    assert z['box']==base['box'] and z['kind']==base['kind'];a,b,c,d=[t*8 for t in z['box']];patch=local[b:d,a:c,:3].astype('float32');kind=z['kind']
    if kind=='glass':pad=z['edge_extension_output_px'];material=np.minimum(cv2.copyMakeBorder(patch[pad:-pad,pad:-pad],pad,pad,pad,pad,cv2.BORDER_REFLECT_101),z['glass_ceiling'])
    elif kind in ['horizontal','vertical']:
     if kind=='horizontal':lo,hi=base.get('profile_sample_x',[z['box'][0],z['box'][2]]);profile=np.median(local[b:d,lo*8:hi*8,:3].astype('float32'),axis=1);material=np.broadcast_to(profile[:,None,:],patch.shape).copy()
     else:sample=patch[16:-16] if d-b>40 else patch;profile=np.median(sample,axis=0);material=np.broadcast_to(profile[None,:,:],patch.shape).copy()
     assert np.array_equal(profile,profiles[z['profile_key']]);material+=np.clip(grain[b:d,a:c]*z['grain_gain'],-z['grain_strength'],z['grain_strength'])
    elif kind=='shutter':
     profile=np.median(patch,axis=1);cols=np.median(patch,axis=0);gain=cols/np.maximum(cols.mean(0),1);gain=cv2.GaussianBlur(gain[None,:,:],(0,0),sigmaX=6,sigmaY=0)[0]
     assert np.array_equal(profile,profiles[z['profile_key']]) and np.array_equal(gain,profiles[z['gain_key']]);material=profile[:,None,:]*gain[None,:,:]+np.clip(grain[b:d,a:c]*.5,-2,2)
    else:material=patch.copy()
    rebuilt[b:d,a:c,:3]=np.rint(np.clip(material,0,255)).astype('uint8')
  else:
   parent=arr(v['geometry_parent']);rebuilt=parent.copy();mask=np.zeros(parent.shape[:2],bool);grain=parent[:,:,:3].astype('float32')-gaussian_filter(parent[:,:,:3].astype('float32'),(4,4,0),mode='nearest')
   for z in v['bevels']:
    x0,y0,x1,y1=z['box'];a,b,c,d=[t*8 for t in z['box']];patch=source[y0:y1,x0:x1,:3].astype('float32');assert np.array_equal(patch,np.asarray(z['source_rgb_columns']));material=np.empty((d-b,c-a,3),np.float32)
    for x in range(x1-x0):material[:,x*8:(x+1)*8,:]=cv2.resize(patch[:,x,:][:,None,:],(1,d-b),interpolation=cv2.INTER_LINEAR)
    rebuilt[b:d,a:c,:3]=np.rint(np.clip(material+np.clip(grain[b:d,a:c]*.4,-2,2),0,255)).astype('uint8');mask[b:d,a:c]=True
   assert np.array_equal(mask,np.asarray(Image.open(v['mask']))>0) and np.array_equal(out[~mask],parent[~mask])
  assert np.array_equal(rebuilt,out),v['id']
  status='static_candidate' if version==4 and gid=='FM0189' else ('superseded' if version==3 and gid=='FM0189' else 'held')
  reasons={1:'Low-resolution source profiles produce blurred/pasted molding and lose local material.',2:'Unconstrained local-gradient rectification leaves bowed corners and creates steps where the X warp starts/ends.',3:'FM0189 gray side face became as bright as white frame, doubling apparent frame width; FM0190 cornice material/joints still look pasted.',4:'FM0189 restores narrow white core, gray side face, straight profiles and source shutter spacing; FM0190 material integration and corner shading interpretation remain unresolved.'}
  checked.append({'id':v['id'],'path':v['output'],'sha256':v['output_sha256'],'decision':status,'reason':reasons[version],'source_and_lineage_hashes_verified':True,'rgba_reproduced_from_saved_recipe':True,'size':[512,1024],'opaque255':True,'runtime_verified':False,'release_eligible':False})

gpath=R/'qa/field_geometry002_gpt190.json';gpt=read(gpath)
for key in ['raw','resized_output','prompt']:assert sha(gpt[key])==gpt[key+'_sha256']
for v in gpt['references']:assert sha(v['path'])==v['sha256']
assert list(Image.open(gpt['raw']).size)==[887,1774]
assert np.array_equal(np.asarray(Image.open(gpt['raw']).convert('RGBA').resize((512,1024),Image.Resampling.LANCZOS)),arr(gpt['resized_output']))
for page in gpt['pages']:assert sha(page['path'])==page['sha256'];pages.append({**page,'review_status':'directly_inspected'})
checked.append({'id':'FM0190-gpt-material-trial','path':gpt['resized_output'],'sha256':gpt['resized_output_sha256'],'decision':'held','reason':gpt['reason'],'actual_raw_size':[887,1774],'saved_Lanczos_recipe_exact':True,'runtime_verified':False,'release_eligible':False})
chosen=next(v for v in four['files'] if v['group_id']=='FM0189');s=arr(chosen['source']);o=arr(chosen['output']);lum=o[:,:,:3].mean(2);vertical=[];horizontal=[];ribs=[]
for y0,y1 in [(9,43),(54,88)]:
 for x0,x1 in [(3,5),(31,33)]:
  bits=lum[y0*8:y1*8,x0*8:x1*8]>200;distinct=len(np.unique(np.packbits(bits,axis=1),axis=0));assert distinct==1
  vertical.append({'source_box':[x0,y0,x1,y1],'threshold_mean_RGB':200,'distinct_row_patterns':distinct,'bright_output_columns_relative':np.flatnonzero(bits.all(0)).tolist(),'limit':'7-pixel visible white core within8-pixel source-column support; remaining pixel is an edge transition, not exact source-nearest color.'})
for y0 in [43,88]:
 bits=lum[y0*8:(y0+2)*8,5*8:59*8]>200
 horizontal.append({'source_y':y0,'source_x_span':[5,59],'threshold':200,'all_bright_relative_rows':np.flatnonzero(bits.all(1)).tolist(),'any_bright_relative_rows':np.flatnonzero(bits.any(1)).tolist(),'distinct_column_patterns':len(np.unique(bits.T,axis=0)),'limit':'Bounded grain changes one edge row at this threshold; source plane geometry remains fixed. No pixel-perfect source color/threshold claim.'})
for a,b in [(13,29),(37,52)]:
 sp=gaussian_filter1d(s[103:128,a:b,:3].mean((1,2)),.35);op=gaussian_filter1d(o[824:1024,a*8:b*8,:3].mean((1,2)),2.8)
 for prom in [3,5,8,10]:
  si=find_peaks(sp,prominence=prom,distance=2)[0]+103;oi=(find_peaks(op,prominence=prom,distance=16)[0]+.5)/8+102.5
  ribs.append({'source_x_span':[a,b],'prominence':prom,'source_profile_peaks_y':si.tolist(),'output_profile_peaks_in_source_y':oi.tolist(),'limit':'Brightness-profile maxima, not independently established physical shutter slat count. Higher thresholds differ because contrast changes.'})

hold='Fixed source planes improve geometry, but FM0190 cornices look pasted/smoother than the brick piers and source dark corner bevels need coherent joint shading. GPT trial1 is overtextured in glass and masonry. Keep held; evaluate constrained use of generated masonry material only, with source corner patches and unchanged glass.'
for v in cat['groups']:
 if v['group_id']=='FM0189':
  assert v['status']=='held' and v['candidate'] is None;v['status']='static_candidate';v['hold_reason']=None
  v['candidate']={'id':chosen['id'],'path':chosen['output'],'sha256':chosen['output_sha256'],'review':'qa/field_geometry002_review.json','method':chosen['method'],'runtime_verified':False,'release_eligible':False};v['geometry_review_scope']='Fixed facade planes, four windows, narrow bright-frame/gray-bevel separation and shutter profile diagnostics. Existing local glass/material interpretation and consumer UV/runtime remain unverified.'
 elif v['group_id']=='FM0190':assert v['status']=='held';v['hold_reason']=hold
for a,b in zip(before['groups'],cat['groups']):
 if a['group_id'] not in ['FM0189','FM0190']:assert a==b
stats=cat['processing_summary'];stats['field_static_candidates']=sum(v['candidate'] is not None for v in cat['groups']);stats['field_holds']=sum(v['status']=='held' for v in cat['groups']);stats['latest_review']='qa/field_geometry002_review.json';assert (stats['field_static_candidates'],stats['field_holds'],stats['field_neural_originals'],stats['remaining_novel_unprocessed'])==(72,23,95,256)
contract['geometry_review002']={'review':'qa/field_geometry002_review.json','resolved_historical_hold':{'FM0189':chosen['id']},'remaining_hold':{'FM0190':hold},'source_correction':gpt['source_correction'],'limits':['Source-plane geometry is exact to declared interpretation, not full RGB/source pixel identity.','Measured straight bright cores, brightness-peak spacing and stored render recipes do not prove consumer/UV/runtime appearance.']}
backup=R/'qa/backups/before-field-geometry002-review';backup.mkdir(parents=True,exist_ok=False)
for p in [catpath,contractpath]:shutil.copy2(p,backup/p.name)
write(catpath,cat);write(contractpath,contract)
preview=C/'outputs/건물_창틀과_셔터_수정_비교.png';shutil.copy2(R/'outputs/field-geometry002/FM0189-whole-v4.png',preview)
review={'schema':'brs-field-geometry-review/v2','batch':'FIELD-GEOMETRY-002','previous_goal_turn_classification':'progress: two source-anchored window replacements, two candidate revocations and six verified outputs in FIELD-GEOMETRY-001.','new_neural_unique_originals':0,'new_local_inference_passes':0,'external_generative_calls':1,'derived_outputs':9,'checked_outputs':checked,'pages':pages,'pages_directly_inspected_count':sum(p['review_status']=='directly_inspected' for p in pages),'selected':{'FM0189':chosen['id']},'remaining_hold':{'FM0190':hold},'geometry_diagnostics':{'vertical_white_cores':vertical,'horizontal_sill_threshold_patterns':horizontal,'shutter_profile_threshold_sensitivity':ribs},'gpt_trial_report':str(gpath),'gpt_trial_report_sha256':sha(gpath),'gpt_limits':gpt['source_correction'],'source_reports_sha256':{str(p.relative_to(R)):sha(p) for p in paths},'catalog_before_sha256':one['catalog_before_sha256'],'catalog_after_sha256':sha(catpath),'geometry_contract_before_sha256':one['geometry_contract_before_sha256'],'geometry_contract_after_sha256':sha(contractpath),'other574_field_groups_unchanged':True,'field_processing_summary':stats,'unique_neural_originals_title_battle_novel_field':352,'protected_file_hashes':last['protected_file_hashes'],'pack_hashes':packhashes,'preview':{'path':str(preview),'sha256':sha(preview)},'runtime_verified':False,'release_eligible':False,'all_game_complete':False,'next_action':'FM0190 constrained generated masonry material trial on fixed source header planes, source corner patches and unchanged glass; continue held grille/perspective facades and remaining field256/battle43/other game populations.','scripts':{p.name:sha(p) for p in [R/'tools'/n for n in ['redraw_field_facades002.py','rectify_field_facades002.py','constrain_field_facades002.py','restore_facade_bevels002.py','review_field190_gpt001.py','finalize_field_geometry002.py']]}}
for rel,h in last['protected_file_hashes'].items():assert sha(R/rel)==h
assert {str(p.relative_to(pack)):sha(p) for p in pack.rglob('*') if p.is_file()}==packhashes
write(Q,review)
with (R/'PROGRESS.md').open('a',encoding='utf8') as f:
 f.write('\n\n## 2026-09-23 — FIELD-GEOMETRY-002 / 건물 면·창틀 음영·셔터 수정\n- 이전 geometry001은progress. 이번은보류2종의4단계직접수정8출력+GPT외부재작화1회/Lanczos1출력 검증과FM0189 보류해결로progress. 신규local추론0/신규원본0,전체목표active.\n- v1 source프로필은blurred붙임판 재질이라제외. v2 기존로컬 경계추적으로펴기는corner휘어짐/구간시작끝단차가남아제외. v3 고정면+local단면프로필에서189 source회색측면x31이흰색250수준으로변해창틀폭이2배로보임확인. v4원본gray/shadow독립세로면복원후189선택. 190은가로띠재질/접합부의일관성부족으로계속보류.\n- 189화이트core4세로구간 threshold200 각행패턴동일,논리1source픽셀폭8output중7밝은core+1edge-transition. sourceRGBA/NN완전동일주장없음. 가로sill은grain때문에threshold200 edge1행차이존재기록. shutter두span prominence3/5 source/output8밝기peak이며위치근사일치;8/10threshold개수달라짐전부보존. 물리slat8개증거아님.\n- built-in image_gen 190 1외부편집 actual887x1774→512x1024Lanczos. 유리/석재거친요철과장이남아전체채택안함. 8창경계표본p95오차.1875~.4375source px;전체geometry/runtime증거아님. 원본에도darkcorner/bevel있으므로전부생성오류로지우지않음. 정확prompt workspace/gpt-trials/FM0190-v1/prompt.txt.\n- 9파생결과 sourcePTM/RGBA·parent/vector/render/map/profile/mask/output/GPTprompt/raw SHA,8배/alpha255·region1회coverage·좌표map단조성·모든저장recipe RGBA재현검증. 비교27페이지중19직접검수(초기탈락v1/v2는전체2씩만). qa/field_geometry002_review.json.\n- 현재field95neural/72후보/23보류/novel256미처리,unique neural352유지. 다른574field그룹/전투241후보17보류26미처리/20key팩/보호파일보존. 설치/에뮬/게임검증/최종ZIP미완료.\n- 다음190 GPT석재재질만고정가로면안에제한적활용·원본cornerpatch보호·유리유지,29/113격자37/38원근면및잔여256/전투43/기타캐릭터적효과컷신범위. 사용자비교outputs/건물_창틀과_셔터_수정_비교.png.\n')
with (C/'outputs/로컬_업스케일_진행.md').open('a',encoding='utf8') as f:
 f.write('\n\n## 건물 창틀·셔터 추가 수정 — FIELD-GEOMETRY-002\n- 금속 창틀 건물1종을 파일 검수 후보로 되돌렸습니다. 원본 회색 옆면이 흰 창틀로 바뀌어 두꺼워 보이던 문제를 고치고 직선과 셔터 간격을 확인했습니다.\n- 벽돌 건물1종은 재질과 창틀 접합부가 아직 부족해 보류합니다. GPT 외부 편집1회도 유리까지 거친 질감이 강해 전체 채택하지 않았습니다. 새 로컬 추론은0회이며 기존 로컬 재질을 활용한 직접 수정입니다.\n- 현재 필드 후보72종/보류23종/미처리256종입니다. 전투43종 미해결과 나머지 캐릭터·적·효과, 게임 검수·최종 배포도 남았습니다.\n')
print(json.dumps({'checked_outputs':len(checked),'pages_inspected':review['pages_directly_inspected_count'],'selected':'FM0189','held':'FM0190','field_summary':stats,'external_calls':1}))
