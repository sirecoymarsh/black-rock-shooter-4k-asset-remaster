"""Finalize inspected redraw candidates; preserve historical inference counts."""
import copy, hashlib, json, shutil, xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np, cv2
from scipy.ndimage import distance_transform_edt
from PIL import Image, ImageDraw, ImageFont

R=Path(__file__).resolve().parents[1]
C=Path('C:/Users/CadriacLord/Documents/Codex/2026-09-22/brs-hd-ui-fonts')
FINAL='qa/local_sr013_review.json'
if (R/FINAL).exists(): raise SystemExit('Already finalized; use a new review revision.')
def read(p): return json.loads((R/p).read_text('utf8'))
def sha(b): return hashlib.sha256(b).hexdigest()
def check(p,h): assert sha(Path(p).read_bytes())==h, str(p)
def rgba(p): return Image.open(p).convert('RGBA')
def write(p,obj):
    p=R/p; t=p.with_suffix(p.suffix+'.staging')
    t.write_text(json.dumps(obj,ensure_ascii=False,indent=2),'utf8');t.replace(p)

cat=read('qa/battle_sr_catalog.json');before=copy.deepcopy(cat)
groups={g['group_id']:g for g in cat['groups']}
assert len(groups)==284 and sum(bool(g.get('candidate')) for g in groups.values())==239
ids={'BM087','BM115'}
assert all(groups[g]['local_sr_attempted'] and not groups[g].get('candidate') for g in ids)
names=['facades','facades_v2','rubble','gpt_rubble','rubble_tone','rubble_edge']
reports=[('qa/local_sr013_'+n+'.json',read('qa/local_sr013_'+n+'.json')) for n in names]
choice={'BM087':'BM087-bands','BM115':'BM115-tone080-edge2'}
reasons={
 'BM087-bands':'Source-positioned continuous facade bands restore the missing horizontal structure without adding per-pixel window dividers. Exact source roof marks retained. This is a source-informed drawing, not proof of original architectural window count.',
 'BM115-tone080-edge2':'Registered GPT repaint removes foil-like local material, with broad source color correction. Edge contrast 2 reduces bright-matte blur while retaining the source-bilinear half-coverage contour and thin connector. Static game-review candidate; internal painted planes remain an interpretation.',
 'BM087-measured':'Rejected: individual source-pixel rectangles introduce artificial barcode/window dividers.',
 'BM087-soft-material':'Rejected: per-pixel dividers remain artificial even with more source color.',
 'BM087-source-facade':'Not selected: stronger source blend makes facade bands mottled and softer than the bands variant.',
 'BM115-planes':'Rejected: palette tracing enlarges quantization speckles into diamond/maze motifs and flat material.',
 'BM115-painted':'Rejected: tracing source quantization still produces maze-like decorative marks.',
 'BM115-gpt-registered':'Intermediate: registered composition is usable as repaint input, but needs broad source tones and narrower alpha transition.',
 'BM115-gpt-source-colors':'Rejected: fine source-color guide produces blurry blotches over the painted planes.',
 'BM115-tone-0.55':'Not selected: weaker broad color correction is farther from the source blue/gray/ochre balance.',
 'BM115-tone-0.80':'Intermediate selected as RGB parent: broad tones are closer to source; alpha edge still visibly too broad on light matte.',
 'BM115-tone080-edge4':'Not selected: harder transition accentuates the low-resolution contour more than edge2.'}
pack=read('qa/local_sr_observed_review_pack_v2.json');pp=Path(pack['path'])
check(pp/'textures.ini',pack['textures_ini_sha256']);assert len(pack['keys'])==20
packhashes={str(p.relative_to(pp)):sha(p.read_bytes()) for p in pp.rglob('*') if p.is_file()}
for b in pack['battle_binding_evidence']:check(pp/pack['keys'][b['key']],b['output_sha256'])
protected_names=['qa/checker_design_contract.json','qa/checker_fidelity_review_v1.json','qa/field_map_inventory_v2.json','tools/Start-Title-QA.ps1']
protected={p:sha((R/p).read_bytes()) for p in protected_names}
initial=read('qa/local_sr012_inference.json')
initial_rows={r['group_id']:r for r in initial['files'] if r['group_id'] in ids and r['model_id']=='wdn'}
for row in initial_rows.values():
    check(row['output'],row['output_sha256']);check(row['model']['path'],row['model']['sha256'])

checked=[];selected={};rows={};facade_proof={}
for name,rep in reports:
    assert rep['new_neural_passes']==0
    for row in rep['files']:
        gid=row['group_id'];ident=row['id'];rows[ident]=row;src=rgba(row['source']);out=rgba(row['output'])
        assert sha(src.tobytes())==row['source_rgba_sha256']==groups[gid]['rgba_sha256']
        g=groups[gid]['representative'];check(g['source'],g['source_sha256'])
        assert Path(row['source'])==Path(g['png'])
        for key in ['output','parent','alpha_parent','vector','render','mask','generated']:
            if key in row:check(row[key],row[key+'_sha256'])
        assert out.size==(src.width*8,src.height*8)==tuple(row['output_size'])
        assert row['new_neural_passes']==0 and row.get('new_generative_calls',0)==0
        oa=np.asarray(out);sa=np.asarray(src);lin=np.asarray(src.getchannel('A').resize(out.size,Image.Resampling.BILINEAR))
        if 'alpha_parent' in row:
            parent=np.asarray(rgba(row['alpha_parent']))
            assert np.array_equal(oa[:,:,3],parent[:,:,3])
            alpha={'exact_to_initial_wdn_alpha':True,'exact_to_source_bilinear_alpha':False}
        elif 'alpha_strength' in row:
            expected=np.rint(np.clip((lin.astype(float)-127.5)*row['alpha_strength']+127.5,0,255)).astype('uint8')
            assert np.array_equal(expected,oa[:,:,3]);assert np.array_equal(oa[:,:,:3],np.asarray(rgba(row['parent']))[:,:,:3])
            down=np.asarray(out.getchannel('A').resize(src.size,Image.Resampling.LANCZOS));gt=sa[:,:,3]>=128;pred=down>=128
            metrics={'source_ge16_reduced_below8':int(((sa[:,:,3]>=16)&(down<8)).sum()),'source_threshold128_iou':float((gt&pred).sum()/(gt|pred).sum()),'mass_ratio':float(expected.mean()/sa[:,:,3].mean()),'source_bilinear_half_coverage_exact':bool(np.array_equal(expected>=128,lin>=128)),'components_alpha128':int(cv2.connectedComponents((expected>=128).astype('uint8'),8)[0]-1),'outside_source_bilinear_support':int((expected[lin==0]>0).sum()),'opaque_support_preserved':bool(np.all(expected[lin==255]==255))}
            assert metrics==row['alpha_metrics']
            alpha={'exact_to_source_bilinear_alpha':False,'formula_reconstructed':True,'RGB_exact_to_parent':True,**metrics}
        else:
            assert np.array_equal(oa[:,:,3],lin)
            alpha={'exact_to_source_bilinear_alpha':True}
        assert np.all(oa[:,:,3][lin==0]==0) and np.all(oa[:,:,3][lin==255]==255)
        if gid=='BM087':
            x0,y0,x1,y1=row['protected_source_box'];nn=np.asarray(src.resize(out.size,Image.Resampling.NEAREST))
            assert np.array_equal(oa[y0*8:y1*8,x0*8:x1*8,:3],nn[y0*8:y1*8,x0*8:x1*8,:3])
            mask=np.asarray(Image.open(row['mask']).convert('L'))>0
            assert np.array_equal(oa[~mask],np.asarray(rgba(row['parent']))[~mask])
            if ident=='BM087-bands':
                rects=ET.parse(row['vector']).getroot().findall('.//{http://www.w3.org/2000/svg}rect')
                bands={e.get('fill'):e for e in rects if e.get('fill','').startswith('url(#row')}
                assert len(bands)==sum(len(f['rows']) for f in row['facades'])==86
                for f in row['facades']:
                    bx0,by0,bx1,by1=f['box']
                    for b,e in f['rows']:
                        el=bands[f'url(#row{f["id"]}{b})']
                        assert abs(float(el.get('y'))-b-row['inset_source_pixels'])<1e-9
                        assert float(el.get('x'))==bx0+1 and float(el.get('width'))==bx1-bx0-2
                facade_proof={'row_bands':86,'row_color_samples':868,'architectural_window_count_verified':False,'protected_source_box':[x0,y0,x1,y1],'protected_output_rgb_pixels':(x1-x0)*(y1-y0)*64,'outside_edit_mask_exact_to_local_parent':True,'alpha_exact_to_local_parent':True}
        pick=choice[gid]==ident
        row['visual_review']={'reviewer':'Codex internal','status':'selected_for_game_review' if pick else 'not_selected','reason':reasons[ident],'runtime_verified':False}
        checked.append({'id':ident,'source_ptm_rgba_parent_vector_render_mask_output_hashes_verified':True,'size8x_verified':True,'alpha':alpha,'new_actual_neural_passes':0})
        if pick:selected[gid]={'source_report':name,'id':ident,'source_rgba_sha256':groups[gid]['rgba_sha256'],'output':row['output'],'output_sha256':row['output_sha256'],'reason':reasons[ident],'authorship':'Codex-authored SVG facade over prior local material' if gid=='BM087' else 'External built-in image_gen repaint with Codex registration, source tone and alpha correction','status':'static_candidate_for_consumer_and_game_review','runtime_verified':False,'release_eligible':False}
assert len(checked)==12 and len(selected)==2
assert sum(r.get('new_generative_calls',0) for _,r in reports)==1

# Re-evaluate the actual generated support, before source alpha is imposed.
gpt=reports[3][1];raw=gpt['raw_generated'];check(raw['output'],raw['sha256'])
assert rgba(raw['output']).size==tuple(raw['size'])==(2172,724)
original_generated=Path('P:/AI/Codex/generated_images/01a0c802-c7cf-7f71-a268-2f12b1fd7bd3/exec-66f23cc6-d3c3-4c7f-9176-735ecca36444.png')
check(original_generated,raw['sha256'])
row=rows['BM115-gpt-registered'];src=rgba(row['source']);sa=np.asarray(src);gen=np.asarray(rgba(raw['output']))
ns,sl,ss,sc=cv2.connectedComponentsWithStats((sa[:,:,3]>0).astype('uint8'),8)
ng,gl,gs,gc=cv2.connectedComponentsWithStats((gen[:,:,3]>=128).astype('uint8'),8)
assert ns==4
yy,xx=np.indices((src.height*8,src.width*8),dtype=np.float32);sx=(xx+.5)/8;sy=(yy+.5)/8
recomputed=[]
for part in row['parts']:
    sm=sl==part['source_component_id'];gm=np.isin(gl,part['generated_component_ids'])
    ys,xs=np.nonzero(sm);gy,gx=np.nonzero(gm)
    sb=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]
    gb=[int(gx.min()),int(gy.min()),int(gx.max()+1),int(gy.max()+1)]
    assert sb==part['source_box'] and gb==part['generated_box']
    x0,y0,x1,y1=sb;gx0,gy0,gx1,gy1=gb;mask=gm[gy0:gy1,gx0:gx1]
    mx=(sx-x0)*(gx1-gx0)/(x1-x0)-.5;my=(sy-y0)*(gy1-gy0)/(y1-y0)-.5
    ga=cv2.remap((mask*255).astype('uint8'),mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,borderValue=0)
    low=np.asarray(Image.fromarray(ga).resize(src.size,Image.Resampling.LANCZOS))>=128
    outside=np.ones(src.size[::-1],bool);outside[y0:y1,x0:x1]=False;low[outside]=False
    missing=sm&~low;dist=distance_transform_edt(~low)
    calc={'raw_registered_alpha128_iou':float((sm&low).sum()/(sm|low).sum()),'source_visible_pixels_without_generated_alpha128':int(missing.sum()),'missing_fraction':float(missing.sum()/sm.sum()),'maximum_source_pixel_distance_for_fill':float(dist[missing].max()) if missing.any() else 0.,'source_component_pixels':int(sm.sum())}
    assert all(abs(calc[k]-part[k])<1e-12 for k in calc)
    recomputed.append({**part,'recomputed_from_raw_pixels':True})
assert sum(p['source_visible_pixels_without_generated_alpha128'] for p in recomputed)==326
assert sum(p['source_component_pixels'] for p in recomputed)==8031
prompt=R/'workspace/gpt-trials/BM115-v1/prompt.txt';assert prompt.exists()
gpt['prompt_file']=str(prompt);gpt['prompt_sha256']=sha(prompt.read_bytes())
gpt['reference_image']=row['source'];gpt['requested_generation_count']=1
gpt['raw_generated']['decision']='Raw output rejected for direct use; selected derived output is registered, tone-corrected and alpha-adjusted.'

mapped={g['group_id'] for g in groups.values() if any(b['source_rgba_sha256']==g['rgba_sha256'] and b['size']==[g['width'],g['height']] for b in read('qa/battle_map_runtime_links.json')['bindings'])}
assert not ids&mapped
for gid in ids:
    groups[gid]['resolved_holds']=groups[gid].get('resolved_holds',[])+[{'reason':groups[gid].pop('review_hold_reason'),'resolved_by':FINAL,'status':'static candidate only; runtime unverified'}]
    groups[gid]['candidate']=selected[gid]
groups['BM087']['manual_geometry_reconstruction']=True
groups['BM115']['external_repaint_candidate']=True
for old in before['groups']:
    if old['group_id'] not in ids:assert groups[old['group_id']]==old
assert cat['source_decode_failures']==before['source_decode_failures']
local=sum(bool(g.get('local_sr_attempted')) for g in groups.values())
geom=sum(bool(g.get('geometry_processed')) and not g.get('local_sr_attempted') for g in groups.values())
accepted=sum(bool(g.get('candidate')) for g in groups.values());assert (local,geom,accepted)==(256,2,241)
summary=cat['processing_summary'];summary.update(battle_static_candidates=241,battle_processed_without_accepted_candidate=17,latest_rework=FINAL,new_unique_originals_latest_rework=0,checked_output_records_latest_rework=12,new_unique_originals_LOCAL_SR_013=0,neural_passes_LOCAL_SR_013=0,generative_calls_LOCAL_SR_013=1,manual_reconstructed_groups_LOCAL_SR_013=1)
prior=read('qa/local_sr012_review.json')
prior['resolved_holds']={gid:{'resolved_by':FINAL,'candidate_id':choice[gid],'runtime_verified':False} for gid in ids}
proposed=read('qa/local_sr013_proposed_review.json')
proposed['superseded_selected']=copy.deepcopy(proposed['selected'])
proposed['selected']={gid:[r['source_report'],r['id']] for gid,r in selected.items()}
proposed['review_status']='Facade mattes inspected; rubble initial matte softness corrected with edge2 and directly compared on light/dark mattes.'
proposed['final_rubble_matte_pages']=reports[-1][1]['comparison_sheets']

# Compact original / initial local / selected proof, retaining honest method labels.
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',21)
small=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17)
sheet=Image.new('RGB',(1560,1050),'#263440');d=ImageDraw.Draw(sheet)
d.text((14,10),'원본 디자인을 기준으로 다시 그린 후보 · 실제 게임 검수 전',font=font,fill='white')
panels=[('BM087',(0,0,128,128),55,500,'건물 무늬 직접 재구성'),('BM115',(0,0,256,64),615,125,'GPT 재질 재작화 + 직접 보정'),('BM115',(126,15,162,45),800,200,'중앙 연결부 · 밝은 배경')]
for gid,box,top,h,label in panels:
    ims=[rgba(groups[gid]['representative']['png']),rgba(initial_rows[gid]['output']),rgba(selected[gid]['output'])]
    labels=['원본 단순 확대','초기 로컬 AI',label]
    for j,(im,title) in enumerate(zip(ims,labels)):
        x=12+j*520;d.text((x,top),title,font=small,fill='white')
        im=im.crop(box if j==0 else tuple(z*8 for z in box));w=500 if top!=800 else 240
        im=im.resize((w,h),Image.Resampling.NEAREST if j==0 else Image.Resampling.LANCZOS)
        bg=Image.new('RGB',im.size,'#eeeeee' if top==800 else '#72808b');bg.paste(im,(0,0),im);sheet.paste(bg,(x,top+30))
pic=R/'outputs/sr013_final_comparison.png';sheet.save(pic)
evidence=sorted(set([str(pic)]+sum((rep.get('comparison_sheets',[]) for _,rep in reports),[])+proposed['matte_pages']))
report={'schema':'brs-local-sr-review/v13','batch':'LOCAL-SR-013','selected':selected,'checked_outputs':checked,'new_unique_originals':0,'new_actual_local_neural_passes':0,'external_generative_calls':1,'external_image_upload':True,'generator':'built-in image_gen; model identifier not exposed','prompt_file':str(prompt),'prompt_sha256':sha(prompt.read_bytes()),'raw_generated':raw,'registration_parts':recomputed,'registration_missing_source_pixels_before_fill':326,'registration_source_pixels':8031,'facade_geometry_checks':facade_proof,'prior_candidates_preserved':239,'processing_summary':copy.deepcopy(summary),'review_evidence':[{'path':p,'sha256':sha(Path(p).read_bytes()),'reviewer':'Codex internal','status':'prepared_for_final_inspection' if p==str(pic) else 'directly_inspected'} for p in evidence],'pack_unchanged_keys':20,'pack_hashes':packhashes,'protected_file_hashes':protected,'new_sources_observed_keys':0,'runtime_verified':False,'release_eligible':False,'limitations':['Facade bands are a source-informed drawing, not recovery of unknown HD window counts.','Rubble material planes are generated interpretations; restored alpha does not prove matching internal planes.','326/8031 source-visible pixels lacked threshold128 generated support after bbox registration and received nearest visible RGB.','Selected rubble alpha has the same source-bilinear threshold128 contour and zero/255 support; bytes are not identical. Alpha mass is about 1.8 percent above source.','Local inference count this batch is zero; one external generation and twelve derived outputs are recorded separately.','284 groups cover battle maps only. Whole-game inventory, native UV/material consumers, actual replacement display, fonts/UI and release remain unfinished.'],'scripts':{p:sha((R/'tools'/p).read_bytes()) for p in ['draw_sr013_facades.py','draw_sr013_facades_v2.py','draw_sr013_rubble.py','register_sr013_rubble.py','tone_sr013_rubble.py','edge_sr013_rubble.py','finalize_sr013.py']}}

backup=R/'qa/backups/before-sr013-finalize';backup.mkdir(parents=True,exist_ok=False)
save_reports=reports+[('qa/local_sr013_proposed_review.json',proposed),('qa/local_sr012_review.json',prior),('qa/battle_sr_catalog.json',cat)]
for name,_ in save_reports:shutil.copyfile(R/name,backup/Path(name).name)
shutil.copyfile(R/'PROGRESS.md',backup/'PROGRESS.md')
shutil.copyfile(C/'outputs/로컬_업스케일_진행.md',backup/'user-progress.md')
for name,obj in save_reports:write(name,obj)
write(FINAL,report)
shutil.copyfile(pic,C/'outputs/직접_재작업_건물과_잔해_비교.png')
(C/'outputs/로컬_업스케일_진행.md').write_text('''# 업스케일 진행 — LOCAL-SR-013 / 직접 재작업

- 보류했던 건물(BM087)과 잔해(BM115)를 재작업하여 게임 검수 후보로 기록했습니다. 이번 새 로컬 추론은0회, GPT 이미지 편집은1회, 직접 그린 결과와 보정 결과는12개입니다.
- 건물의 가로 무늬86구간은 원본 위치를 기준으로 도형으로 다시 그렸습니다. 개별 픽셀을 창틀로 해석했던 첫 안은 제외했습니다. 지붕 작은 체크무늬의 원본45픽셀(8배 출력2880픽셀)은 RGB가 정확히 같습니다. 실제 창문 개수를 복원했다는 뜻은 아닙니다.
- 잔해는 직접 윤곽을 따는 안도 무늬가 부자연스러워 제외했습니다. GPT 재작화1회를 거쳐 원본3구역에 위치를 맞추고 원본 계열 색과 얇은 연결부를 보정했습니다. GPT 처리1회는 외부 이미지 처리입니다.
- 잔해의 생성 재질이 원본의 모든 면과 일치하는지는 미확정입니다. 생성물이 빠뜨린 원본326/8031픽셀 영역에는 가까운 재질색을 채웠습니다. 최종 투명도는 원본 bilinear 확대와 절반 농도 윤곽이 같지만 수치 전체가 같지는 않으며 평균 투명도 합은 약1.8% 증가했습니다.
- 누계 실제 로컬 추론 고유원본257종(타이틀1+전투256), 도형 전용2종. 전투284종 중 정적 후보241/보류17/미처리26입니다. 전체 게임 완료율이 아닙니다.
- 기존20키 검수팩은 변경/설치하지 않았고 이번2종의 정확한 관측키도 없습니다. 실제 게임 표시·UV·한글 폰트·LOCK ON 검증과 전체 필드/적/효과/컷신 및 최종 ZIP은 남았습니다.
- 다음: 체크 바닥 BM175/201/209/244 재작업 및 BM226 정밀 검사, 미처리26종과 필드576종 분류/형식 해독. 에뮬은 고정exe+ISO 직접 지정으로 실행하는 원칙을 유지합니다.
''','utf8')
with (R/'PROGRESS.md').open('a',encoding='utf8') as f:f.write('''

## 2026-09-23 — LOCAL-SR-013: 건물 직접 재구성과 잔해 재작화
- 이전 goal turn LOCAL-SR-012는 progress. 사용자 직접 그리기 지시에 따라 보류 BM087/BM115를 재작업했다. 신규 원본0/새 local inference0/GPT external edit1/파생12출력. alpha/color/vector 후처리를 새 추론으로 세지 않음.
- BM087 facade v1 두안은 개별픽셀에 창틀을 만들어 barcode처럼 보이므로 제외. v2 연속 가로86구간과 원본색 gradient 작성, bands .30 선택(.60은 얼룩/흐림). 지붕[74,1,89,4] 원본45→출력2880 RGB정확보호, SVG row좌표/86개·mask밖WDN정확·alpha WDN정확검사. 실제 창문개수 복원주장없음.
- BM115 원본15색 contour tracing2안은1431윤곽의 양자화가 diamond/maze로 드러나 제외. built-in image_gen 1외부편집2172x724, raw 직접적용거부. 원본alpha3component에 축정렬bbox등록,색조.8+edge2를 정적후보선택. 외부모델ID비공개. 정확prompt workspace/gpt-trials/BM115-v1/prompt.txt.
- 등록시 generated alpha128가 빠진 원본326/8031px(부분81/82/163),최대원본거리2.2361px색채움. raw등록IoU .9320567/.8707865/.8864162 재계산. 복원alpha를생성재질면일치증거로쓰지않음. RGB tone.8부모정확, sourcebilinear halfcoverage/zero255support정확,edge2 alpha128component3,약alpha손실0/축소128IoU .9966542/mass1.0179848. alpha byte-exact주장금지.
- 모든12원본PTM/RGBA·부모·SVG/render/mask/generated/output해시/8배크기검사. 건물전체/좌우/양matte 및 잔해각재작업전체/좌중우/연결부양matte 직접검수. qa/local_sr013_review.json. 기존239후보/다른그룹/특수미해독3건/체크계약/fieldv2/Start-Title-QA/20key팩 보존.
- 전투후보241/보류17/미처리26,neural256+geometry-only2;타이틀포함실제neural원본257유지. SR012역사카운트유지하고 resolved_holds만추가. 이번2종관측키0,설치/에뮬실행/런타임검증없음. GUI복구증거없어검은화면캡처반복없음.
- 사용자출력 Coutputs/직접_재작업_건물과_잔해_비교.png 및진행.md. 다음 체크175201209244 재작업/226정밀검수,남은26원본,field576분류/미지원SC구획,적/효과/컷신확장. 전체목표active,실게임·폰트·LOCK ON·최종ZIP미완료.
''')
assert packhashes=={str(p.relative_to(pp)):sha(p.read_bytes()) for p in pp.rglob('*') if p.is_file()}
assert all(sha((R/p).read_bytes())==h for p,h in protected.items())
assert read('qa/battle_sr_catalog.json')==cat
print(json.dumps({'checked_outputs':12,'selected':choice,'static_candidates':241,'holds':17,'unprocessed':26,'local_passes_this_batch':0,'external_generations':1,'runtime_verified':False},ensure_ascii=False))
