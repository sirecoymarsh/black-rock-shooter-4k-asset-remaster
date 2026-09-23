from pathlib import Path
import json,hashlib,copy,shutil,xml.etree.ElementTree as ET
import numpy as np,cv2
from scipy.ndimage import gaussian_filter,gaussian_filter1d
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];C=Path(r'C:\Users\CadriacLord\Documents\Codex\2026-09-22\brs-hd-ui-fonts');Q=R/'qa/field_geometry007_review.json';assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text('utf8'))
def write(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False),'utf8')
def arr(p):return np.asarray(Image.open(p).convert('RGBA'))
last=read(R/'qa/field_sr005_review.json');names=['field_geometry007_source_audit.json','field_geometry007_authored_v1.json','field_geometry007_authored_v2.json','field_geometry007_authored_v3.json','field_geometry007_ornament533_v3.json'];reports={n:read(R/'qa'/n) for n in names};audit,v1,v2,v3,o3=[reports[n] for n in names];cp=R/'qa/field_sr_catalog.json';gp=R/'qa/architectural_geometry_contract.json';cat=read(cp);before=copy.deepcopy(cat);contract=read(gp)
assert sha(cp)==last['catalog_after_sha256']==audit['catalog_before_sha256'];assert sha(gp)==last['geometry_contract_after_sha256']==audit['geometry_contract_before_sha256']
for rel,h in last['protected_file_hashes'].items():assert sha(R/rel)==h
pack=R/'workspace/local-sr/observed-review-pack-v2/PSP/TEXTURES/NPUH10126';packhash={str(p.relative_to(pack)):sha(p) for p in pack.rglob('*') if p.is_file()};assert packhash==last['pack_hashes']
for g in before['groups']:
 if g['candidate']:assert sha(g['candidate']['path'])==g['candidate']['sha256']
for v in audit['files']:
 assert sha(v['source_ptm'])==v['source_ptm_sha256'];assert hashlib.sha256(arr(v['source']).tobytes()).hexdigest()==v['source_rgba_sha256']
for report in [v1,v2,v3]:assert sha(report['reconstruction_program'])==report['reconstruction_program_sha256'];assert report['source_audit_sha256']==sha(R/'qa/field_geometry007_source_audit.json')
assert o3['previous_report_sha256']==sha(R/'qa/field_geometry007_authored_v2.json')
selected={'FM0495':v3['files'][0],'FM0533':o3};checked=[];diagnostics={};rejected={
 'FM0495-authored-v1':'Invalid material data from an empty narrow-border source ROI, plus wrong source joint anchors and flat broad grout. Never eligible.',
 'FM0495-authored-v2':'Finite color data, but some manually placed vertical joints were several source pixels off and bottom-row seam layout was wrong. v3 uses source trough evidence; counters/axis alignment alone did not establish correctness.',
 'FM0533-authored-v1':'Estimated opacity contour turned the ornament into thick lumps and bulging junctions.',
 'FM0533-authored-v2':'Four smooth manual curves were too thin and lost source white coverage; width1.25 was rejected after source comparison.'}
for version,report in [(1,v1),(2,v2),(3,v3),(3,{'files':[o3]})]:
 for v in report['files']:
  gid=v['group_id'];s=arr(v['source']);p=arr(v['parent']);out=arr(v['output']);layer=arr(v['render']);f=np.load(v['frozen_planes']);base=f['base_rgb'];assert hashlib.sha256(s.tobytes()).hexdigest()==v['source_rgba_sha256']
  for key in ['source_ptm','parent','output','vector','render','frozen_planes']:assert sha(v[key])==v[key+'_sha256']
  assert out.shape==(s.shape[0]*8,s.shape[1]*8,4) and np.all(out[:,:,3]==255);xml=ET.parse(v['vector']).getroot();record={'id':v['id'],'path':v['output'],'sha256':v['output_sha256'],'source_parent_vector_render_frozen_output_hashes_verified':True,'runtime_verified':False,'release_eligible':False}
  if gid=='FM0495' and version==1:
   nonfinite=int((~np.isfinite(base)).sum());assert nonfinite>0;record.update(decision='rejected_invalid',nonfinite_frozen_RGB_values=nonfinite,reason=rejected[v['id']]);checked.append(record);continue
  assert np.isfinite(base).all()
  if gid=='FM0495':
   coverage=np.zeros((512,512),np.uint8);rebuild=np.zeros((512,512,3),np.float32)
   for z in v['recipe']['regions']:
    x0,y0,x1,y1=z['source_box'];ax,ay,bx,by=z['output_box'];m=z['donor_margin_source'];mx=np.linspace((x0+m)*8-.5,(x1-m)*8-.5,bx-ax,dtype=np.float32);my=np.linspace((y0+m)*8-.5,(y1-m)*8-.5,by-ay,dtype=np.float32);xx,yy=np.meshgrid(mx,my);assert np.array_equal(f['mapx'][ay:by,ax:bx],xx);assert np.array_equal(f['mapy'][ay:by,ax:bx],yy)
    patch=cv2.remap(p[:,:,:3],xx,yy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE).astype('float32');patch+=np.asarray(z['source_mean_rgb'])-patch.mean((0,1));rebuild[ay:by,ax:bx]=patch;coverage[ay:by,ax:bx]+=1
   assert np.all(coverage==1) and np.array_equal(coverage,f['coverage'])
   if version==3:
    d=np.zeros((64,64),np.float32)
    for x0,y0,x1,y1 in v['recipe']['source_damage_windows']:d[y0:y1,x0:x1]=(s[y0:y1,x0:x1,:3].mean(2)<135).astype('float32')
    d=cv2.resize(gaussian_filter(d,.3),(512,512),interpolation=cv2.INTER_LINEAR);assert np.array_equal(d,f['source_damage_mask']);rebuild=rebuild*(1-d[:,:,None])+p[:,:,:3]*d[:,:,None]
   assert np.array_equal(rebuild,base)
   grain=np.clip((p[:,:,:3].astype('float32')-gaussian_filter(p[:,:,:3].astype('float32'),(1.25,1.25,0),mode='nearest'))*.4,-6,6);assert np.array_equal(grain,f['grout_grain']);a=layer[:,:,3:4]/255.;expected=np.rint(np.clip(base*(1-a)+np.clip(layer[:,:,:3]+grain,0,255)*a,0,255)).astype('uint8');assert np.array_equal(expected,out[:,:,:3])
   segments=v['recipe']['lines'];xml_lines=list(xml.iter('{http://www.w3.org/2000/svg}line'));assert len(xml_lines)==len(segments)*2
   for i,z in enumerate(segments):
    (x1,y1),(x2,y2)=z['points'];assert x1==x2 or y1==y2
    for element in xml_lines[i*2:i*2+2]:assert [float(element.attrib[t]) for t in ['x1','y1','x2','y2']]==[x1,y1,x2,y2]
   if version==3:
    gray=s[:,:,:3].mean(2);og=out[:,:,:3].mean(2);anchors=[]
    for z in segments:
     (x0,y0),(x1,y1)=z['points']
     if z['axis']=='vertical':
      a0,b0=int(np.ceil(y0+.5)),int(np.floor(y1-.5));profile=gray[a0:b0].mean(0);lo=max(0,int(np.floor(x0))-2);hi=min(64,int(np.ceil(x0))+3);observed=lo+int(np.argmin(profile[lo:hi]))+.5;source_error=abs(observed-x0)
      a1,b1=int((y0+1)*8),int((y1-1)*8);pr=np.median(og[a1:b1],axis=0);left=max(0,int((x0-.7)*8));right=min(512,int((x0+.7)*8)+1);outpos=(left+int(np.argmin(pr[left:right]))+.5)/8;output_error=abs(outpos-x0)
     else:
      profile=np.median(gray,axis=1);lo=max(0,int(np.floor(y0))-1);hi=min(64,int(np.ceil(y0))+2);observed=lo+int(np.argmin(profile[lo:hi]))+.5;source_error=abs(observed-y0)
      pr=np.median(og,axis=1);top=max(0,int((y0-.7)*8));bottom=min(512,int((y0+.7)*8)+1);outpos=(top+int(np.argmin(pr[top:bottom]))+.5)/8;output_error=abs(outpos-y0)
     anchors.append({'axis':z['axis'],'source_segment':z['points'],'source_local_trough_center':float(observed),'source_anchor_error_px':float(source_error),'output_local_trough_center':float(outpos),'output_anchor_error_source_px':float(output_error)})
    assert len(anchors)==25;assert max(z['source_anchor_error_px'] for z in anchors)<=.5;assert max(z['output_anchor_error_source_px'] for z in anchors)<=.2
    diagnostics[gid]={'horizontal_courses':7,'vertical_segments':18,'source_brick_material_regions':len(v['recipe']['regions']),'anchors':anchors,'source_anchor_max_error_px':max(z['source_anchor_error_px'] for z in anchors),'output_anchor_max_error_source_px':max(z['output_anchor_error_source_px'] for z in anchors),'weak_sloped_interior_line_row12_20':'Preserved as local material; not counted as a new authored structural joint.','damage_windows_source':v['recipe']['source_damage_windows'],'limit':'Observed seam segments and fixed decoded texture anchors; not a count of physical blocks or a proof of UV/tile behavior.'}
   record.update(geometry_and_material_recipe_RGBA_reproduced=True,source_rectangles_full_coverage_once=True)
  else:
   start=gaussian_filter1d(np.median(s[104:109,:,:3],axis=0),.7,axis=0,mode='nearest');end=gaussian_filter1d(np.median(s[126:128,:,:3],axis=0),.7,axis=0,mode='nearest');t=np.linspace(0,1,24)[:,None,None];clean=start[None,:,:]*(1-t)+end[None,:,:]*t;assert np.array_equal(clean,f['source_clean_background']);bg=p[:,:,:3].astype('float32').copy();clean8=cv2.resize(clean.astype('float32'),(256,192),interpolation=cv2.INTER_LINEAR);donor=p[640:832,:,:3].astype('float32');grain=np.clip((donor-gaussian_filter(donor,(4,4,0),mode='nearest'))*.25,-1,1);clean8+=grain;blend=np.clip((np.arange(192)+.5)/32,0,1).astype('float32')[:,None,None];bg[832:]=bg[832:]*(1-blend)+clean8*blend;assert np.array_equal(base,bg)
   a=layer[:,:,3:4]/255.;expected=np.rint(np.clip(base*(1-a)+layer[:,:,:3]*a,0,255)).astype('uint8');assert np.array_equal(expected,out[:,:,:3]);assert np.array_equal(out[:832],p[:832]);rects=list(xml.iter('{http://www.w3.org/2000/svg}rect'));assert len(rects)==3
   for element,box in zip(rects,[[0,110,32,14],[0,109,32,1],[0,124,32,1]]):assert [float(element.attrib[t]) for t in ['x','y','width','height']]==box
   if version>=2:
    paths=list(xml.iter('{http://www.w3.org/2000/svg}path'));assert len(paths)==4 and [el.attrib['d'] for el in paths]==v['recipe']['hand_paths']
   if v['id']==o3['id']:
    group=next(xml.iter('{http://www.w3.org/2000/svg}g'));assert float(group.attrib['stroke-width'])==v['recipe']['stroke_width_source'];assert max(abs(t) for pair in v['recipe']['curve_offsets_source_px'] for t in pair)<=.85
    metrics={};sourceclass=(s[109:125,:,0].astype(int)-s[109:125,:,2].astype(int))<27
    for label,path in [('localPhoto',v['parent']),('v2_manual_thin',next(z for z in v2['files'] if z['group_id']=='FM0533')['output']),('v3_source_fit',v['output'])]:
     small=np.asarray(Image.open(path).convert('RGB').resize((32,128),Image.Resampling.LANCZOS)).astype(float);wc=(small[109:125,:,0]-small[109:125,:,2])<27;metrics[label]={'source_white_class_count':int(sourceclass.sum()),'output_white_class_count':int(wc.sum()),'white_class_IoU':float(np.count_nonzero(sourceclass&wc)/np.count_nonzero(sourceclass|wc)),'RGB_MAE_ornament_native_source_scale':float(np.abs(small[109:125]-s[109:125,:,:3]).mean())}
    assert metrics==v['source_scale_diagnostics'];diagnostics[gid]={'manual_curve_count':4,'source_fitted_width':v['recipe']['stroke_width_source'],'curve_offsets_source_px':v['recipe']['curve_offsets_source_px'],'straight_bars':[[0,109,32,1],[0,124,32,1]],'upper104_source_rows_parent_RGBA_exact':True,'source_scale_metrics':metrics,'interpretation_correction':'The original broad claim that localPhoto has too much total white is not supported: this diagnostic counts203 Photo vs259 source-class pixels. v2 was too thin. v3 is a smooth vector redraw with225; its .710 classIoU is below Photo .784, so it is not more pixel-exact reconstruction. Static selection is for controlled smooth curves with the same paired-scroll concept, and retains this measured limitation.','limit':'The near-white RGB class is a diagnostic affected by source palette/antialiasing, not native alpha or proof of exact original high-resolution ornament.'}
   record.update(material_background_and_composite_RGBA_reproduced=True,upper_parent_RGBA_exact_until_source_y104=True)
  chosen=selected.get(gid,{}).get('id')==v['id'];record.update(decision='static_candidate' if chosen else 'not_selected',reason='Source-aligned straight courses/segments with worn local stone inside source regions.' if chosen and gid=='FM0495' else 'Four smooth source-fitted scrolls preserve the paired ornament and source-fixed horizontal borders; pixel-footprint limits are recorded.' if chosen else rejected[v['id']]);checked.append(record)
assert len(checked)==6 and sum(z['decision']=='static_candidate' for z in checked)==2
pages=[]
for name,report in reports.items():
 for p in report.get('pages',[]):assert sha(p['path'])==p['sha256'];pages.append({**p,'review_status':'directly_inspected_by_Codex_internal','evidence_report':name})
assert len(pages)==15
for g in cat['groups']:
 if g['group_id'] in selected:
  gid=g['group_id'];assert g['status']=='held' and g['local_sr_attempted'];v=selected[gid];g.update(status='static_candidate',hold_reason=None,candidate={'id':v['id'],'path':v['output'],'sha256':v['output_sha256'],'review':'qa/field_geometry007_review.json','method':v['method'],'geometry_review':'Source7 course/18 seam anchors; local material and source damage regions.' if gid=='FM0495' else 'Manual4 cubic scroll centerlines, source coverage-fitted offsets/width1.967692, fixed two horizontal borders. Not pixel-exact; footprint comparison in final report.','runtime_verified':False,'release_eligible':False})
for a,b in zip(before['groups'],cat['groups']):
 if a['group_id'] not in selected:assert a==b
stats=cat['processing_summary'];stats.update(field_static_candidates=102,field_holds=46,latest_review='qa/field_geometry007_review.json')
assert sum(bool(g['candidate']) for g in cat['groups'])==102 and sum(g['status']=='held' for g in cat['groups'])==46;assert sum(g['local_sr_attempted'] for g in cat['groups'])==145
for gid in selected:contract['current_batch_geometry_holds'].pop(gid,None)
contract['geometry_review007']={'review':'qa/field_geometry007_review.json','static_candidates':{k:v['id'] for k,v in selected.items()},'audited_unmodified_hold':'FM0496 source bands/joints mapped for next step; no full reconstruction claimed.','source_interpretation_corrections':['Masonry v1/v2 joint anchors were inaccurate despite axis-aligned checks; v3 fixes positions using source troughs.','Near-white footprint count does not support global excess-white claim for Photo533; v2 manual thin version is rejected. v3 redraw prioritizes smooth curves while retaining lower pixel overlap than Photo as a limitation.'],'new_local_inference_passes':0,'new_external_calls':0,'runtime_verified':False,'release_eligible':False}
backup=R/'qa/backups/before-field-geometry007-review';backup.mkdir(exist_ok=False)
for p in [cp,gp]:shutil.copy2(p,backup/p.name)
write(cp,cat);write(gp,contract)
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17);can=Image.new('RGB',(1050,770),'#25313c');d=ImageDraw.Draw(can)
for row,(gid,box,label) in enumerate([('FM0495',(12,12,52,52),'벽돌 이음선과 표면'),('FM0533',(0,96,32,128),'장식 곡선과 천의 음영')]):
 v=selected[gid]
 for col,(path,title) in enumerate([(v['source'],'원본 · 단순 확대'),(v['parent'],'로컬 Photo 비교'),(v['output'],'원본 구조·곡선 재구성')]):
  im=Image.open(path).convert('RGBA').crop(box if col==0 else tuple(t*8 for t in box))
  if col==0:im=im.resize((im.width*8,im.height*8),Image.Resampling.NEAREST)
  d.text((col*350+8,row*385+8),label,font=font,fill='white');d.text((col*350+8,row*385+33),title,font=font,fill='#d4dce4');can.paste(im.convert('RGB'),(col*350+(350-im.width)//2,row*385+60))
preview=R/'outputs/field-geometry007/벽돌_줄눈과_장식_곡선_수정.png';can.save(preview);localpreview=C/'outputs'/preview.name;shutil.copy2(preview,localpreview)
review={'schema':'brs-source-geometry007-final-review/v1','batch':'FIELD-GEOMETRY-007','previous_goal_turn_classification':audit['previous_goal_turn_classification'],'this_goal_turn_classification':'progress: source audits3, six geometry/material derivatives reviewed, source joint interpretation corrected and two former holds become static candidates; FM0496 remains held.','selected':{k:v['id'] for k,v in selected.items()},'audited_only':['FM0496'],'checked_outputs':checked,'geometry_diagnostics':diagnostics,'new_local_neural_unique_originals':0,'new_direct_GPT_only_unique_originals':0,'new_local_inference_passes':0,'external_generative_calls':0,'source_reports_sha256':{str((R/'qa'/n).relative_to(R)):sha(R/'qa'/n) for n in names},'source_and_comparison_pages':pages,'pages_directly_inspected':15,'catalog_before_sha256':audit['catalog_before_sha256'],'catalog_after_sha256':sha(cp),'geometry_contract_before_sha256':audit['geometry_contract_before_sha256'],'geometry_contract_after_sha256':sha(gp),'other574_field_groups_unchanged':True,'previous100_field_candidates_unchanged':True,'field_processing_summary':stats,'unique_local_neural_originals_title_battle_novel_field':402,'unique_processed_originals_including_direct_GPT_only_title_battle_novel_field':405,'protected_file_hashes':last['protected_file_hashes'],'pack_hashes':packhash,'preview':{'path':str(localpreview),'project_path':str(preview),'sha256':sha(preview)},'runtime_verified':False,'release_eligible':False,'all_game_complete':False,'limits':['FM0495 v1 contained nonfinite frozen RGB from an empty source ROI and is rejected, not claimed as a valid render. All other5 derivatives have finite data and verified source/material compositing recipes.','Masonry source trough checks cover7 course lines/18 authored seam segments; the faint sloped interior line is retained as material. This is not a physical brick/UV count.','FM0533 v3 is a clean vector interpretation of the same paired-scroll design; its near-white-class IoU .710 is lower than localPhoto .784. It cannot be called exact source reconstruction. Manual thin v2 is rejected.','FM0496 only audited; source bands, block seams and lower sloped panel still require reconstruction.','No new local model call, external generation, PPSSPP key, installation, emulator launch, gameplay verification or release ZIP.','Historical57 field/241 battle geometry-applicability review,46 current field holds,203 novel unprocessed,43 battle unresolved and other game-source populations remain.'],'next_action':'Reconstruct FM0496 source cornice/band/plate geometry; repair structured masonry456/465/466/473 without guessing seam positions; finish motifs525 and atlas29, perspective facades37/38. Continue all remaining target populations and eventual real-game verification.','scripts':{n:sha(R/'tools'/n) for n in ['audit_field_geometry007.py','author_field_geometry007.py','author_field_geometry007_v2.py','author_field495_v3.py','fit_field533_curves.py','finalize_field_geometry007.py']}}
for rel,h in last['protected_file_hashes'].items():assert sha(R/rel)==h
assert {str(p.relative_to(pack)):sha(p) for p in pack.rglob('*') if p.is_file()}==packhash;write(Q,review)
with (R/'PROGRESS.md').open('a',encoding='utf8') as f:f.write('''

## 2026-09-23 — FIELD-GEOMETRY-007 / 벽돌 이음선·장식 곡선
- 이전SR005는progress. 이번3sourceaudit/6파생검토/495·533보류2종정적후보로progress,전체목표active. 새local/GPT/고유원본0. 496은source구조audit만,wholeheld유지.
- 495 v1 좁은좌측원본ROI가비어nonfinite RGB/검은edge발생하여무효. v2 숫자는유효하나손으로잡은여러joint좌표가틀림. 원본row별darkprofile대조로v3 x위치/하단seam개수수정.7가로course·18세로segment,약한row12..20내부사선은새structuraljoint로세지않고재질로유지. source trough오차최대.5px,outputanchor최대.2px이하검사. source중앙/하단파손2영역보존.
- 495 원본구역별Photo재질안쪽재투영+원본평균색/직선mortar,26영역1회coverage. thinmortar고주파±6이shape를바꾸지않음. v1/v2출력그대로보존하며실패이유명시,최종v3만후보.
- 533 v1 source-chroma contour는뭉친흰덩어리,v2수동곡선1.25px는너무얇아불채택. v3수동4cubic곡선에각±.85source px범위위치보정과공유폭fitting→1.967692px. 좌우동일복제아님. sourcey109/124직선border,상단104행Photo RGBA정확,하단은원본salmoncleanplate+기존Photo잔질감.
- 원본whiteclass259,Photo203,v2 150,v3 225;classIoU .784/.543/.710,RGBMAE9.98/15.39/11.80. Photo전체white가과다라는해석은정정. v3는같은pairedscroll을깨끗한벡터곡선으로재작화한정적후보이며Photo보다pixeloverlap높다고주장안함. 원본고해상도정답/alpha증거아님.
- source3+비교12=15페이지직접검수. 전체6파생중v1masonry1무효,나머지5finite/원본·부모·SVG/render/base/recipe RGBA재현/alpha255검사. 최종qa/field_geometry007_review.json. 기존100후보/다른574fieldgroup/전투·20key팩보호파일불변.
- field102후보/46보류/203미처리,local145+directGPT3=148처리그대로. 고유local402/외부전용포함405. 설치/실게임/최종ZIP미완료;GUI복구증거없어실행/검은캡처반복없음.
- 다음496cornice·blockjoint·하단기울기판구조,456/465/466/473줄눈은원본좌표확인후구성,525motif·29·37/38기존보류/전체잔여원본범위계속. outputs/field-geometry007/벽돌_줄눈과_장식_곡선_수정.png.
''')
with (C/'outputs/로컬_업스케일_진행.md').open('a',encoding='utf8') as f:f.write('''

## 벽돌 이음선·장식 곡선 직접 수정 — FIELD-GEOMETRY-007
- 보류했던2종을원본좌표와무늬에맞춰다시구성해파일검수후보로남겼습니다. 벽돌줄눈위치를원본에대조했고,장식은4곡선과두가로띠로정리했습니다. 기존로컬재질을활용했으며새로컬추론·외부생성은없습니다.
- 장식은원본고해상도를정확히복원한것이아닌같은콘셉트의곡선재작화입니다. 원본픽셀겹침은로컬Photo보다낮은부분이있어검수기록에남겼습니다.
- 현재필드후보102종/보류46종/미처리203종. 실게임검수와최종배포는미완료입니다.
''')
print(json.dumps({'selected':review['selected'],'checked_outputs':6,'source_and_comparison_pages':15,'field_summary':stats,'geometry_diagnostics':diagnostics},ensure_ascii=False))
