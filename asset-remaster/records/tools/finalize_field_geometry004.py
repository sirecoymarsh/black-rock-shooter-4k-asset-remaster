"""Verify all recipes, structural diagnostics, and adopt three inspected repairs."""
import copy,json,hashlib,shutil,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np,cv2
from scipy.ndimage import gaussian_filter,gaussian_filter1d
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];C=Path(r'C:\Users\CadriacLord\Documents\Codex\2026-09-22\brs-hd-ui-fonts');Q=R/'qa/field_geometry004_review.json';assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text('utf8'))
def arr(p):return np.asarray(Image.open(p).convert('RGBA'))
def write(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2),'utf8')
names=['field_geometry004_source_audit.json','field_geometry004_trials.json','field_geometry004_refined.json','field_geometry004_faces_v3.json','field_geometry004_gpt_and_alignment.json'];reports={n:read(R/'qa'/n) for n in names};audit,one,two,three,last=[reports[n] for n in names];previous=read(R/'qa/field_sr004_review.json');cp=R/'qa/field_sr_catalog.json';gp=R/'qa/architectural_geometry_contract.json';cat=read(cp);before=copy.deepcopy(cat);contract=read(gp)
assert sha(cp)==previous['catalog_after_sha256']==audit['catalog_before_sha256'];assert sha(gp)==previous['geometry_contract_after_sha256']==audit['geometry_contract_before_sha256']
for rel,h in previous['protected_file_hashes'].items():assert sha(R/rel)==h
pack=R/'workspace/local-sr/observed-review-pack-v2/PSP/TEXTURES/NPUH10126';packhash={str(p.relative_to(pack)):sha(p) for p in pack.rglob('*') if p.is_file()};assert packhash==previous['pack_hashes']
assert two['parent_report_sha256']==sha(R/'qa/field_geometry004_trials.json');assert three['parent_report_sha256']==sha(R/'qa/field_geometry004_refined.json')
for n,h in last['parent_reports_sha256'].items():assert sha(R/'qa'/n)==h
pick={'FM0337':'FM0337-source-planes-gpt-material-v3','FM0346':'FM0346-source-faces-bevel-v3','FM0347':'FM0347-pixel-center-curves-v3'}
reasons={'FM0337':'Original ten bright source spans and lower horizontal faces are fixed; GPT material projected from region interiors, with source mean colors and smoothed row/column lighting restored. Prior local-material trials smeared or overemphasized coarse grain. Generated whole image alone is not adopted.','FM0346':'Six period6 bright spans retain pale shaded faces and a narrow darker bevel. v1 flattened the flute, v2 cubic interpolation softened it; v3 separates2-pixel bright/3-pixel shaded/1-pixel bevel supports with original vertical illumination and restrained existing WDN grain.','FM0347':'Original straight upper dividers/moldings remain fixed; eight authored curved arms retain four waists. v1 was too soft; v2 improved stroke but treated pixel indices as coordinates. v3 shifts source trace x/y by.5 and uses a narrow beveled profile. No full-ellipse or exact source-pixel-identity claim.'}
checked=[];allrows={}
for version,report in [(1,one),(2,two),(3,three),(4,last)]:
 for v in report['files']:
  gid=v['group_id'];s=arr(v['source']);p=arr(v['parent']);o=arr(v['output']);h,w=s.shape[:2];assert hashlib.sha256(s.tobytes()).hexdigest()==v['source_rgba_sha256']
  for k in ['source_ptm','parent','output','base_planes','region_classmap','vector','previous']:
   if k in v:assert sha(v[k])==v[k+'_sha256'],(v['id'],k)
  assert o.shape==(h*8,w*8,4) and np.all(o[:,:,3]==255)
  if 'vector' in v:
   rects=list(ET.parse(v['vector']).getroot().iter('{http://www.w3.org/2000/svg}rect'));assert len(rects)==len(v['regions']);coverage=np.zeros(o.shape[:2],np.uint8);classmap=np.zeros(o.shape[:2],np.uint16)
   for j,(z,rect) in enumerate(zip(v['regions'],rects),1):
    x0,y0,x1,y1=z['source_box'];assert [float(rect.attrib[k]) for k in ['x','y','width','height']]==[x0,y0,x1-x0,y1-y0];assert not any(k in rect.attrib for k in ['rx','ry','transform']);coverage[y0*8:y1*8,x0*8:x1*8]+=1;classmap[y0*8:y1*8,x0*8:x1*8]=j
   assert np.all(coverage==1) and np.array_equal(classmap,np.asarray(Image.open(v['region_classmap'])))
  rebuild=p.copy()
  if version==1:
   base=np.load(v['base_planes'])['rgb'];grain=p[:,:,:3].astype('float32')-gaussian_filter(p[:,:,:3].astype('float32'),(v['grain_sigma_output'],v['grain_sigma_output'],0),mode='nearest');rebuild[:,:,:3]=np.rint(np.clip(base+np.clip(grain*v['grain_gain'],-v['grain_bound'],v['grain_bound']),0,255)).astype('uint8')
  elif version==2:
   base=np.load(v['base_planes'])['rgb'];rc=v['recipe']
   if gid=='FM0337':
    material=np.zeros_like(base)
    for z in rc['regions']:
     a,b,c,d=[t*8 for t in z['source_box']];px,py=z['parent_interior_output_trim_xy'];patch=p[b+py:d-py or None,a+px:c-px or None,:3].astype('float32');patch=cv2.resize(patch,(c-a,d-b),interpolation=cv2.INTER_CUBIC);fine=patch-gaussian_filter(patch,(12,12,0),mode='nearest');material[b:d,a:c]=np.clip(fine*.75,-10,10)
    rebuild[:,:,:3]=np.rint(np.clip(base+material,0,255)).astype('uint8')
   else:
    sg=rc['grain_sigma_output'];grain=p[:,:,:3].astype('float32')-gaussian_filter(p[:,:,:3].astype('float32'),(sg,sg,0),mode='nearest');rebuild[:,:,:3]=np.rint(np.clip(base+np.clip(grain*rc['grain_gain'],-rc['grain_bound'],rc['grain_bound']),0,255)).astype('uint8')
  elif version==3:
   base=np.load(v['base_planes'])['rgb'];phase=np.array(v['source_phase_rgb'],np.float32);pr={'bright':phase[:,:2].mean(1),'shaded':phase[:,2:5].mean(1),'shadow':phase[:,5]};classes=np.ones(o.shape[:2],np.uint8)
   for x0 in range(0,32,6):
    for label,a,b,key in [(2,x0,min(x0+2,32),'bright'),(3,x0+2,min(x0+5,32),'shaded'),(4,x0+5,min(x0+6,32),'shadow')]:
     if a>=32:continue
     assert np.array_equal(pr[key],np.array(v['source_profiles_rgb'][key],np.float32));expected=cv2.resize(gaussian_filter1d(pr[key],.5,axis=0,mode='nearest')[:,None,:],((b-a)*8,128),interpolation=cv2.INTER_LINEAR);assert np.array_equal(base[128:,a*8:b*8],expected);classes[128:,a*8:b*8]=label
   assert np.array_equal(classes,np.asarray(Image.open(v['region_classmap'])));grain=p[:,:,:3].astype('float32')-gaussian_filter(p[:,:,:3].astype('float32'),(2,2,0),mode='nearest');rebuild[:,:,:3]=np.rint(np.clip(base+np.clip(grain*.4,-2,2),0,255)).astype('uint8')
  elif gid=='FM0337':
   rc=v['recipe'];g=arr(rc['generated_material']);assert sha(rc['generated_material'])==rc['generated_material_sha256'];coverage=np.zeros(o.shape[:2],np.uint8)
   for z in rc['regions']:
    x0,y0,x1,y1=z['source_box'];a,b,c,d=[t*8 for t in z['source_box']];px,py=z['generated_interior_trim_output_xy'];mat=cv2.resize(g[b+py:d-py or None,a+px:c-px or None,:3].astype('float32'),(c-a,d-b),interpolation=cv2.INTER_CUBIC);sp=s[y0:y1,x0:x1,:3].astype('float32');target=sp.mean((0,1));gain=target/np.maximum(mat.mean((0,1)),1);row=gaussian_filter1d(sp.mean(1),2,axis=0,mode='nearest');col=gaussian_filter1d(sp.mean(0),2,axis=0,mode='nearest')
    assert np.array_equal(target,np.array(z['target_source_mean_rgb'],np.float32));assert np.array_equal(gain,np.array(z['generated_RGB_gain'],np.float32));assert np.array_equal(row,np.array(z['source_row_shading_rgb'],np.float32)) and np.array_equal(col,np.array(z['source_column_shading_rgb'],np.float32));shade=cv2.resize(row[:,None,:]+col[None,:,:]-2*target,(c-a,d-b),interpolation=cv2.INTER_LINEAR);rebuild[b:d,a:c,:3]=np.rint(np.clip(mat*gain+shade,0,255)).astype('uint8');coverage[b:d,a:c]+=1
   assert np.all(coverage==1)
  else:
   rc=v['recipe'];assert sha(rc['base_planes'])==rc['base_planes_sha256'];base=np.load(rc['base_planes'])['rgb'];grain=p[:,:,:3].astype('float32')-gaussian_filter(p[:,:,:3].astype('float32'),(5,5,0),mode='nearest');rebuild[:,:,:3]=np.rint(np.clip(base+np.clip(grain*.3,-2,2),0,255)).astype('uint8')
   original=next(z for z in one['files'] if z['group_id']==gid)
   for a,b in zip(original['curve_centers'],rc['curve_centers']):assert np.array_equal(np.array(a['source_x'])+.5,b['source_x']) and np.array_equal(np.array(a['source_y'])+.5,b['source_y'])
  rebuild[:,:,3]=255;assert np.array_equal(rebuild,o),v['id']
  chosen=pick[gid]==v['id'];checked.append({'id':v['id'],'group_id':gid,'path':v['output'],'sha256':v['output_sha256'],'decision':'static_candidate' if chosen else 'superseded_not_selected','reason':reasons[gid],'source_and_lineage_hashes_verified':True,'rgba_from_saved_base_or_region_recipe_exact':True,'opaque255':True,'runtime_verified':False,'release_eligible':False});allrows[v['id']]=v
gpt=last['gpt']
for k in ['raw','resized_output','prompt']:assert sha(gpt[k])==gpt[k+'_sha256']
for v in gpt['references']:assert sha(v['path'])==v['sha256']
raw=Image.open(gpt['raw']).convert('RGBA');assert list(raw.size)==[1774,887];assert np.array_equal(np.asarray(raw.resize((1024,512),Image.Resampling.LANCZOS)),arr(gpt['resized_output']))
checked.append({'id':'FM0337-gpt-whole-trial','path':gpt['resized_output'],'sha256':gpt['resized_output_sha256'],'decision':'not_selected','reason':'Whole repaint changes source region colors and does not itself bind all source edges; only source-constrained material derivative is selected.','raw_prompt_reference_hashes_verified':True,'Lanczos_recipe_exact':True,'runtime_verified':False,'release_eligible':False});assert len(checked)==10
# Independent output edge diagnostics, bounded to a neighborhood of each original
# anchor. They do not replace inspection or claim global geometry recovery.
def edges(o,axis,positions,span,directions):
 lum=o[:,:,:3].mean(2);traces=[]
 for pos,sign in zip(positions,directions):
  derivative=np.diff(lum,axis=axis)*sign;expected=pos*8;low=max(0,expected-9);high=min(derivative.shape[axis],expected+8)
  window=derivative[span[0]*8:span[1]*8,low:high] if axis==1 else derivative[low:high,span[0]*8:span[1]*8]
  ix=np.argmax(window,axis=axis)+low+1;errors=(ix-expected)/8
  traces.append({'source_anchor':pos,'direction':sign,'sample_count':len(errors),'median_absolute_error_source_px':float(np.median(np.abs(errors))),'p95_absolute_error_source_px':float(np.percentile(np.abs(errors),95)),'max_absolute_error_source_px':float(np.abs(errors).max())})
 return traces
v337=allrows[pick['FM0337']];o337=arr(v337['output']);spans=next(v for v in audit['files'] if v['group_id']=='FM0337')['bright_vertical_source_spans'];xs=[];signs=[]
for a,b in spans:
 if a>0:xs.append(a);signs.append(1)
 xs.append(b);signs.append(-1)
diagnostics={'FM0337':{'vertical_edges':edges(o337,1,xs,[5,45],signs),'horizontal_lower_edges':edges(o337,0,[47,50,59,62],[10,127],[1,-1,1,-1]),'limit':'Dominant signed grayscale gradient within +/-1 source pixel of declared boundary, excluding plane junctions. Not a full UV/render proof.'},'FM0346':{'phase_spans_source':[[0,2],[6,8],[12,14],[18,20],[24,26],[30,32]],'face_phase_widths_source':[2,3,1],'period_source':6,'grain_RGB_bound':2,'class_support_identical_for_all_lower_rows':len(np.unique(np.asarray(Image.open(allrows[pick['FM0346']]['region_classmap']))[128:],axis=0))==1,'limit':'Six bright texture spans, not independently proven six 3D columns.'},'FM0347':allrows[pick['FM0347']]['recipe']['source_curve_diagnostics']}
pages=[]
for n,report in reports.items():
 for v in report.get('pages',[]):
  assert sha(v['path'])==v['sha256'];inspected=not (n=='field_geometry004_trials.json' and '-detail-' in v['path']);pages.append({**v,'review_status':'directly_inspected_by_Codex_internal' if inspected else 'not_needed_after_whole_image_rejection','report':n})
assert len(pages)==19 and sum(v['review_status']=='directly_inspected_by_Codex_internal' for v in pages)==16
for v in cat['groups']:
 gid=v['group_id']
 if gid in pick:
  assert v['status']=='held' and v['candidate'] is None and v['local_sr_attempted'];chosen=allrows[pick[gid]];v.update(status='static_candidate',hold_reason=None,candidate={'id':chosen['id'],'path':chosen['output'],'sha256':chosen['output_sha256'],'review':'qa/field_geometry004_review.json','method':chosen.get('method','Source-fixed planes with generated material' if gid=='FM0337' else 'Pixel-center-aligned authored curves plus existing local material'),'geometry_review':reasons[gid],'runtime_verified':False,'release_eligible':False})
for a,b in zip(before['groups'],cat['groups']):
 if a['group_id'] not in pick:assert a==b
stats=cat['processing_summary'];stats.update(field_static_candidates=sum(bool(v['candidate']) for v in cat['groups']),field_holds=sum(v['status']=='held' for v in cat['groups']),latest_review='qa/field_geometry004_review.json');assert (stats['field_static_candidates'],stats['field_holds'],stats['field_neural_originals'],stats['remaining_novel_unprocessed'])==(89,36,125,226)
contract['geometry_review004']={'review':'qa/field_geometry004_review.json','resolved_holds':pick,'scope':reasons,'source_interpretation_correction':'FM0347 was previously described as oval/curved lattice. The established source motif is four waists made by crossing arms; do not assert complete ellipses. Pixel-index trace samples are converted to pixel centers by+.5 in both axes.','external_material':'FM0337 uses one new built-in image_gen edit followed by source-plane/color projection. Other two use previous local WDN material.','runtime_verified':False,'release_eligible':False}
backup=R/'qa/backups/before-field-geometry004-review';backup.mkdir(exist_ok=False)
for p in [cp,gp]:shutil.copy2(p,backup/p.name)
write(cp,cat);write(gp,contract)
# Compact source/local/final proof sheet; all crops are shown at their true8x pixels.
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17);can=Image.new('RGB',(930,930),'#26333f');draw=ImageDraw.Draw(can)
for j,(gid,box,label) in enumerate([('FM0337',(40,0,72,32),'콘크리트 반복 면'),('FM0346',(0,0,32,32),'기둥 면과 홈'),('FM0347',(16,0,48,32),'장식 격자')]):
 v=allrows[pick[gid]];sourceim=Image.open(v['source']).convert('RGBA').crop(box).resize((256,256),Image.Resampling.NEAREST);parent=Image.open(v['parent']).convert('RGBA').crop(tuple(t*8 for t in box));out=Image.open(v['output']).convert('RGBA').crop(tuple(t*8 for t in box))
 for k,(im,title) in enumerate(zip([sourceim,parent,out],['원본 · 단순 확대','초기 로컬','원본 구조로 수정'])):draw.text((k*310+6,j*310+5),label+' / '+title,font=font,fill='white');can.paste(im.convert('RGB'),(k*310+6,j*310+38))
preview=R/'outputs/field-geometry004/기둥과_장식격자_수정_비교.png';can.save(preview);localpreview=C/'outputs/기둥과_장식격자_수정_비교.png';shutil.copy2(preview,localpreview)
review={'schema':'brs-source-repeat-final-review/v1','batch':'FIELD-GEOMETRY-004','previous_goal_turn_classification':'progress: FIELD-SR-004 processed30 new originals, selected14 and classified72.','this_goal_turn_classification':'progress: three held source-geometry/material defects resolved,10 output recipes verified, one external material comparison incorporated only after source-plane/color projection.','selected':pick,'selection_scope':reasons,'new_neural_unique_originals':0,'new_local_inference_passes':0,'external_generative_calls':1,'checked_outputs':checked,'source_reports_sha256':{str((R/'qa'/n).relative_to(R)):sha(R/'qa'/n) for n in names},'pages':pages,'pages_directly_inspected_count':16,'gpt_raw_directly_inspected':True,'geometry_diagnostics':diagnostics,'catalog_before_sha256':audit['catalog_before_sha256'],'catalog_after_sha256':sha(cp),'geometry_contract_before_sha256':audit['geometry_contract_before_sha256'],'geometry_contract_after_sha256':sha(gp),'other573_field_groups_unchanged':True,'previous86_field_candidates_unchanged':True,'field_processing_summary':stats,'unique_neural_originals_title_battle_novel_field':382,'protected_file_hashes':previous['protected_file_hashes'],'pack_hashes':packhash,'preview':{'path':str(localpreview),'project_path':str(preview),'sha256':sha(preview)},'gpt_prompt':gpt['prompt'],'gpt_actual_raw_size':[1774,887],'gpt_tool':'built-in image_gen; model identifier not exposed','runtime_verified':False,'release_eligible':False,'all_game_complete':False,'limits':['These three are static source/material candidates. The game consumer, UV seams, lighting and in-game scale remain unverified.','Structured reconstructions retain source geometry and interpreted shading, not every source dither pixel.','FM0347 revised sample-center diagnostic excludes the neighboring crossing arm; its numbers are not directly interchangeable with the earlier unsplit centroid diagnostic.','Final output replay uses frozen base planes where recorded; geometry maps/regions and sampled actual-output edges are checked separately.','Historical57 field and241 battle material candidates still need geometry-applicability review; no final geometry-wide acceptance claim.','No new observed PPSSPP key, install, emulator launch or final distribution package.'],'next_action':'Continue source-anchored held rail/lattice29/113, perspective facades37/38 and current structured holds. Complete remaining field226, battle43 and other source populations; FM0190 needs changed joint/plane-profile interpretation.','scripts':{n:sha(R/'tools'/n) for n in ['audit_field_repeats004.py','rebuild_field_repeats004.py','refine_field_repeats004.py','refine_field346_faces.py','constrain_field337_gpt_and_align347.py','finalize_field_geometry004.py']}}
for rel,h in previous['protected_file_hashes'].items():assert sha(R/rel)==h
assert {str(p.relative_to(pack)):sha(p) for p in pack.rglob('*') if p.is_file()}==packhash
write(Q,review)
with (R/'PROGRESS.md').open('a',encoding='utf8') as f:f.write('''

## 2026-09-23 — FIELD-GEOMETRY-004 / 반복 기둥·장식 격자 보류3종 수정
- 이전FIELD-SR-004는progress. 이번은 원본좌표3종audit,10출력검증과FM0337/0346/0347 보류해결로progress. 신규local추론/새고유원본0, built-in image_gen 외부편집1회. 전체목표active.
- 337 source밝은span10개(왼끝포함), y4..46기둥면과하단47..50/59..62띠, 왼x0..9연속면 분리. 실제3D기둥10개주장아님. v1질감번짐, v2local interior grain강조가거친얼룩으로보여제외. GPT정확지시문 workspace/gpt-trials/FM0337-v1/prompt.txt, actual1774x887→1024x512Lanczos. 원본/geometryv1두참조,modelID미노출. 전체GPT그림은색/좌표보장안되므로불채택. 각source평면안쪽재질만재투영하고원본평균RGB와완만한행/열조명복원한v3채택. 전부로컬결과라고하지않음.
- 346 source6px주기/밝은2px띠6개,나머지는blackhole아닌회색면. v1옆면평평함,v2cubic보간흐림으로제외. v3 밝은2/음영3/어두운bevel1source px로구분하고source세로조명+기존WDNgrain±2로수정,채택. 공간기둥수확정아님.
- 347 상단source수평행0/1/15/16/31과세로x0/31/63고정,하단4waist/8곡선팔작성. 이전oval표현은완전타원증거아님을정정. v1너무흐림,v2stroke개선후pixelindex를좌표로쓴오프셋확인. v3각trace x/y+.5픽셀중심변환. 인접교차팔영향을분리한48source highlight중심표본 median오차.2/p95.4source px;전체geometry/runtime증거아님. v3채택.
- 원본PTM/RGBA·부모·vector/classmap/base/output/GPTraw/prompt/reference SHA,축정렬rect·전면1회coverage·저장base/recipe로RGBA재현·8배/alpha255확인.337출력signed edge주변오차추가측정(제한된anchor근방이며global증거아님). 비교/source19페이지중16직접검수,초기실패v1detail3미사용+GPTraw직접검수. qa/field_geometry004_review.json.
- field125neural/89정적후보/36보류/novel226미처리. 기존86후보와다른573fieldgroup,전투241후보17보류26미처리,관측20key팩/보호원본 보존. 고유neural382유지. historical57field/241battlegeometry적용여부대기. 설치/실제게임/최종ZIP미완료.
- 다음29/113격자·37/38원근선·나머지structured보류와잔여field226/전투43/캐릭터적효과컷신조사. FM0190grain강도반복은중단한상태이며면단면/접합해석변경필요. 사용자비교 outputs/기둥과_장식격자_수정_비교.png.
''')
with (C/'outputs/로컬_업스케일_진행.md').open('a',encoding='utf8') as f:f.write('''

## 반복 기둥·장식 격자 3종 수정 — FIELD-GEOMETRY-004
- 보류3종을 원본 구조로 수정해 파일 검수 후보로 전환했습니다. 콘크리트1종은 내장 GPT 이미지 편집1회로 만든 재질을 원본 위치·색에 맞췄고, 나머지2종은 기존 로컬 재질을 사용했습니다. 새로운 로컬 추론은0회입니다.
- 현재 필드 후보89종/보류36종/미처리226종입니다. 실제 게임 적용 검수와 최종 배포는 아직 완료되지 않았습니다.
''')
print(json.dumps({'checked_outputs':len(checked),'selected':pick,'field_summary':stats,'gpt_calls':1,'vertical_edge_p95_max':max(v['p95_absolute_error_source_px'] for v in diagnostics['FM0337']['vertical_edges']),'horizontal_edge_p95_max':max(v['p95_absolute_error_source_px'] for v in diagnostics['FM0337']['horizontal_lower_edges'])}))
