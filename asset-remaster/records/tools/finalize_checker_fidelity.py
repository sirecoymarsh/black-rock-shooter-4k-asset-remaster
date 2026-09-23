"""Finalize checker-only review; unrelated SR012 inference remains pending."""
import copy,hashlib,json,shutil
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];C=Path('C:/Users/CadriacLord/Documents/Codex/2026-09-22/brs-hd-ui-fonts')
FINAL=R/'qa/checker_fidelity_review_v1.json'
if FINAL.exists():raise SystemExit('Already reviewed; use a new revision.')
def read(p):return json.loads((R/p).read_text('utf8'))
def sha(b):return hashlib.sha256(b).hexdigest()
def check(p,h):assert sha(Path(p).read_bytes())==h,str(p)
def write(p,v):(R/p).write_text(json.dumps(v,ensure_ascii=False,indent=2),'utf8')
cat=read('qa/battle_sr_catalog.json');before=copy.deepcopy(cat);groups={g['group_id']:g for g in cat['groups']}
assert sum(bool(g.get('candidate')) for g in groups.values())==229 and groups['BM221']['candidate'] is None
q=read('qa/checker_fidelity_v1.json');retry=read('qa/checker_frame_rework_v1.json');contract=read('qa/checker_design_contract.json');source=read('qa/local_sr012_sources.json')
selected_ids={'BM200-cell-preserved','BM269-cell-preserved','BM221-wdn-guided-0.60'}
selected={};checks=[];modelpairs=set();neural=0
for report_name,rep in [('qa/checker_fidelity_v1.json',q),('qa/checker_frame_rework_v1.json',retry)]:
    for row in rep['files']:
        gid=row['group_id'];g=groups[gid];src=Image.open(row['source']).convert('RGBA');assert sha(src.tobytes())==row['source_rgba_sha256']==g['rgba_sha256']
        check(g['representative']['source'],g['representative']['source_sha256']);check(row['output'],row['output_sha256']);out=Image.open(row['output']).convert('RGBA');assert out.size==(src.width*8,src.height*8)==tuple(row['output_size'])
        for key in ['input','native','cleanplate','mask','parent']:
            if key in row:check(row[key],row[key+'_sha256'])
        if 'model' in row:
            m=row['model'];pair=(m['path'],m['sha256'])
            if pair not in modelpairs:check(*pair);modelpairs.add(pair)
            assert Image.open(row['native']).size==(src.width*4,src.height*4) and Image.open(row['input']).size==src.size
        a=np.asarray(src);b=np.asarray(out)
        if gid=='BM221':
            mask=np.all(a==[98,125,103,255],2)|np.all(a==[218,177,186,255],2);assert int(mask.sum())==614
            assert np.array_equal(np.asarray(Image.open(row['mask']).convert('L'))>0,mask)
            m8=np.repeat(np.repeat(mask,8,0),8,1);nn=np.asarray(src.resize(out.size,Image.Resampling.NEAREST));assert np.array_equal(b[m8],nn[m8])
            reference=np.asarray(src.getchannel('A').resize(out.size,Image.Resampling.BILINEAR));assert np.array_equal(b[:,:,3][~m8],reference[~m8])
            evidence={'protected_source_pixels':614,'protected_output_pixels':int(m8.sum()),'protected_rgba_exact_to_source_nearest8x':True,'nonprotected_alpha_exact_to_source_bilinear8x':True,'checker_neural_inference':False}
        else:
            pitch=row['cell_pitch_source'];yy,xx=np.indices(a.shape[:2]);parity=((xx//pitch+yy//pitch)%2).astype(np.uint8)
            cls=(a[:,:,0]>=70).astype(np.uint8) if gid=='BM200' else (a[:,:,0]!=255).astype(np.uint8)
            pred=(b[:,:,0]>=70).astype(np.uint8) if gid=='BM200' else (b[:,:,0]!=255).astype(np.uint8)
            assert np.array_equal(cls,parity) and np.array_equal(pred,np.repeat(np.repeat(parity,8,0),8,1))
            assert out.getchannel('A').tobytes()==src.getchannel('A').resize(out.size,Image.Resampling.NEAREST).tobytes()
            for cell in row['cells']:
                sp=np.asarray(src.crop(tuple(cell['source_box'])));op=np.asarray(out.crop(tuple(cell['output_box'])));assert np.all(op.min((0,1))>=sp.min((0,1))) and np.all(op.max((0,1))<=sp.max((0,1)))
            evidence={'cell_pitch_source':pitch,'cell_count':len(row['cells']),'cell_boundary_phase_and_class_exact':True,'alpha_exact_to_source_nearest8x':True,'shading_within_each_source_cell_gamut':True,'checker_neural_inference':False}
        assert row['new_neural_passes']==int('native' in row);neural+=row['new_neural_passes']
        chosen=row['id'] in selected_ids
        reason=('Cell boundaries/count/colors retained on dark and light mattes; only shading within cells is interpolated.' if gid!='BM221' else 'Exact authored checker layer is sharp; 0.60 frame residual retains clearer frame edges than 0.35 while reducing speculative depth relative to unguided frame.')
        row['visual_review']={'reviewer':'Codex internal','status':'selected_for_game_review' if chosen else 'not_selected','reason':reason if chosen else 'Alternate not selected. '+reason}
        checks.append({'id':row['id'],'output_sha256':row['output_sha256'],'source_model_parent_mask_and_output_verified':True,**evidence})
        if chosen:selected[gid]={'source_report':report_name,'source_rgba_sha256':g['rgba_sha256'],'output':row['output'],'output_sha256':row['output_sha256'],'method':row['method'],'reason':reason,'status':'static_candidate_for_consumer_and_game_review','runtime_verified':False,'release_eligible':False}
assert len(checks)==6 and neural==2 and len(selected)==3
floor_notes={
 'BM201':{'decision':'held_rework_required','reason':'Whole-source comparison shows newly sharpened triangular fractures through checker cells and changed patch boundaries. Protect the grid and original damage masks before accepting the material.'},
 'BM209':{'decision':'held_rework_required','reason':'Upper patches and horizontal checker strip acquire folded/slit-like cell interpretations. Separate grid design from surrounding damage and material.'},
 'BM244':{'decision':'held_rework_required','reason':'Several checker patches acquire faceted/folded shading and altered internal boundaries. Requires source-guided checker and clipping masks.'},
 'BM226':{'decision':'retained_static_candidate_pending_geometric_audit','reason':'Whole-source comparison retains the diagonal checker rows and phase visibly. No mesh substitution or blur seen; precise cell/UV audit and runtime remain unverified.'}}
revoked={}
for gid,note in floor_notes.items():
    g=groups[gid];g['checker_design_review']={**note,'reviewer':'Codex internal','evidence':str(R/f'outputs/checker_audit_{gid}.png'),'runtime_verified':False}
    if note['decision']=='held_rework_required':
        revoked[gid]=g['candidate'];g.setdefault('superseded_candidates',[]).append({'candidate':g['candidate'],'reason':note['reason']});g['candidate']=None;g['review_hold_reason']=note['reason']
for gid,c in selected.items():
    groups[gid]['candidate']=c;groups[gid].pop('review_hold_reason',None)
    if gid in {'BM200','BM269'}:groups[gid]['geometry_processed']=True;groups[gid]['processing_method']='deterministic_checker_cells';assert not groups[gid]['local_sr_attempted']
    else:groups[gid]['checker_design_protected']=True
untouched=set(groups)-set(selected)-set(floor_notes)
for g in before['groups']:
    if g['group_id'] in untouched:assert groups[g['group_id']]==g
local=sum(bool(g.get('local_sr_attempted')) for g in groups.values());geom=sum(bool(g.get('geometry_processed')) and not g.get('local_sr_attempted') for g in groups.values());processed=local+geom;candidates=sum(bool(g.get('candidate')) for g in groups.values())
assert (local,geom,processed,candidates)==(244,2,246,229)
summary=cat['processing_summary'];summary.update(battle_static_candidates=candidates,battle_processed_without_accepted_candidate=processed-candidates,battle_groups_processed_any_method=processed,battle_geometry_only_groups_processed=geom,battle_groups_never_locally_inferred=284-local,battle_groups_not_yet_processed=284-processed,latest_rework='qa/checker_fidelity_review_v1.json',new_unique_originals_latest_rework=0,checked_output_records_latest_rework=6,neural_passes_CHECKER_001=2)
summary['counter_contract']='Locally processed counts mean actual neural inference. Processed-any-method also includes explicitly recorded deterministic geometry. Static candidate/held/unprocessed counts use all methods.'
neural_sources={f'BM{i:03d}' for i in [62,63,65,74,79,87,101,110,111,115,116,118]};semantic={f'BM{i:03d}' for i in [22,24,41,80,85,95,96,106,109,112,113,120,121,189]}
source['review_status']='All five pages directly inspected by Codex internal; classified before SR012 inference and checker work.'
source['classification']={g:('neural material/alpha comparison prepared; pending result review' if g in neural_sources else 'text/emblem or ambiguous small marks: source protection/reconstruction needed' if g in semantic else 'checker design protected separately' if g in {'BM200','BM269'} else 'flat/lookup use needs consumer analysis; no invented texture' if g in {'BM193','BM229','BM231','BM284'} else 'sparse star positions and density require protection' if g=='BM259' else 'hazard stripe geometry requires protection' if g=='BM067' else 'luminous line/path geometry and glow need separate treatment') for g in source['group_ids']}
contract['completed_static_design_checks']=['BM200','BM221','BM269'];contract['review_queue']=['BM175','BM201','BM209','BM226','BM244'];contract['completed_checks_runtime_verified']=False
evidence_paths=q['comparison_sheets']+retry['comparison_sheets']+[str(R/f'outputs/checker_audit_{g}.png') for g in floor_notes]
evidence=[{'path':p,'sha256':sha(Path(p).read_bytes()),'reviewer':'Codex internal'} for p in evidence_paths]
pack=read('qa/local_sr_observed_review_pack_v2.json');packdir=Path(pack['path']);check(packdir/'textures.ini',pack['textures_ini_sha256']);assert len(pack['keys'])==20
packhashes={str(p.relative_to(packdir)):sha(p.read_bytes()) for p in packdir.rglob('*') if p.is_file()}
for b in pack['battle_binding_evidence']:check(packdir/pack['keys'][b['key']],b['output_sha256'])
report={'schema':'brs-checker-fidelity-review/v1','selected':selected,'revoked_floor_candidates':revoked,'floor_review':floor_notes,'checks':checks,'new_actual_neural_passes':2,'new_neurally_processed_originals':0,'new_geometry_only_originals':2,'processing_summary':copy.deepcopy(summary),'review_evidence':evidence,'runtime_verified':False,'release_eligible':False,'image_upload':False,'pack_unchanged_keys':20,'pack_hashes':packhashes,'limitations':['Exact checker preservation is nearest-neighbor restoration of authored pixel geometry, not an AI restoration of unknown high-resolution detail.','BM200/BM269 shading is ordinary per-cell interpolation; no neural inference claimed.','BM221 mask clipping retains source pixel stair-steps; improving clipping must not alter checker cells.','Checks establish static design fidelity, not native UV/tiling/game behavior.','SR012 24 outputs/46 passes remain unreviewed and unmerged.'],'scripts':{p:sha((R/'tools'/p).read_bytes()) for p in ['checker_fidelity_v1.py','refine_checker_frame.py','prepare_checker_floor_audit.py','finalize_checker_fidelity.py']}}
report['scripts']['repair_checker_shading_quantization.py']=sha((R/'tools/repair_checker_shading_quantization.py').read_bytes())
# Clear user-facing comparison, with a separate full-silhouette strip.
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18);src=Image.open(groups['BM221']['representative']['png']).convert('RGBA');old=Image.open(q['revoked_candidate']['output']).convert('RGBA');new=Image.open(selected['BM221']['output']).convert('RGBA')
s=Image.new('RGB',(1140,1110),'#293440');d=ImageDraw.Draw(s)
for j,(im,label) in enumerate([(src,'원본 · 체크무늬 기준'),(old,'이전 후보 · 흐림으로 제외'),(new,'수정 후보 · 체크무늬 정확 보존')]):
    x=j*380+10;d.text((x,10),label,font=font,fill='white')
    crop=im.crop((0,32,32,96) if j==0 else (0,256,256,768)).resize((256,512),Image.Resampling.NEAREST if j==0 else Image.Resampling.LANCZOS);bg=Image.new('RGB',crop.size,'#eeeeee');bg.paste(crop,(0,0),crop);s.paste(bg,(x,50))
    full=im.crop((0,0,32,128) if j==0 else (0,0,256,1024)).resize((128,512),Image.Resampling.NEAREST if j==0 else Image.Resampling.LANCZOS);bg=Image.new('RGB',full.size,'#111111');bg.paste(full,(0,0),full);s.paste(bg,(x,585))
userpath=R/'outputs/checker_design_corrected.png';s.save(userpath);shutil.copyfile(userpath,C/'outputs/체크판_디자인_보존_비교.png')
backup=R/'qa/backups/before-checker-finalize';backup.mkdir(parents=True,exist_ok=False)
oldreview=read('qa/local_sr011_review.json');oldreview.setdefault('superseded_selections',{})['BM221']={'superseded_by':'qa/checker_fidelity_review_v1.json','reason':'User checker-design fidelity clarification; old soft candidate revoked.'}
tosave=[('qa/battle_sr_catalog.json',cat),('qa/checker_fidelity_v1.json',q),('qa/checker_frame_rework_v1.json',retry),('qa/checker_design_contract.json',contract),('qa/local_sr012_sources.json',source),('qa/local_sr011_review.json',oldreview)]
for name,_ in tosave:shutil.copyfile(R/name,backup/Path(name).name)
for name,v in tosave:write(name,v)
FINAL.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
write('qa/checker_floor_audit_review.json',{'floor_review':floor_notes,'review_evidence':[e for e in evidence if 'checker_audit_' in e['path']],'runtime_verified':False})
(C/'outputs/로컬_업스케일_진행.md').write_text('''# 로컬 업스케일 진행 — 체크판 디자인 보존 재작업

- 체크판을 게임의 핵심 디자인으로 별도 보호합니다. 칸이 금속망이나 접힌 조각으로 변하거나 흐려진 결과는 채택하지 않습니다.
- BM221 체크 장식: 기존 흐린 후보를 취소했습니다. 원본 체크 색·위치를 별도 층으로 정확히 보존하고, 체크를 제거한 주변 재질에만 로컬 모델 2회 추론을 수행했습니다. 프레임 후처리 후 다시 검수했습니다.
- BM200/BM269 바닥 체크: 2×2칸과 4×4칸의 경계를 정확하게 유지하고, 각 칸 안의 명암만 보간했습니다. 이 2종은 AI 처리로 세지 않습니다.
- 기존 바닥 BM201/BM209/BM244는 체크칸의 변형 가능성을 확인해 후보에서 보류로 돌렸습니다. BM226은 대각선 체크가 보이지만 정밀한 칸·UV 검증은 남았습니다.
- 확정 기록 기준 실제 로컬 GPU 추론 고유 원본은 245종(타이틀1+전투244), 도형 처리 전용 2종입니다. 전투 정적 후보229/처리 후 보류17/미처리38종입니다. 전체 게임 완료율이 아닙니다.
- 별도 SR012의 신규12종은 로컬 추론24결과/46회가 끝났지만 아직 검수·위 수치 통합 전입니다.
- 필드 v2는 SC422개/STCM151개를 검증했고 텍스처1630건 중1616건을 해독했습니다. 기존576종 그룹 ID를 보존했습니다. 추가 텍스처는 없으며 SC209건·특수텍스처14건·미분류구획833건이 남았습니다.
- 기존20키 검수팩 미설치·변경 없음. 실제 게임 표시, Orbit 한글 폰트·LOCK ON, 전 지역·EX/진엔딩·필드·적·효과·컷신 및 최종 ZIP 검증이 남았습니다.
- 다음: 체크 바닥3종과BM175의 원본 격자/손상 마스크 복원, SR01212종 검수·재작업·통합, 필드 특수 구획 해독을 이어갑니다.
''','utf8')
with (R/'PROGRESS.md').open('a',encoding='utf8') as f:f.write('''

### CHECKER-001 정적 검수와 기존 바닥 후보 재검토
- BM221정확핑크/그린614source픽셀=39296output픽셀RGBA완전일치. 체크제거입력으로WDN/photo2실제RGBpass,프레임sourceguide .35/.60후처리2. .60선택:칸선명함유지하면서과한프레임입체감감소. BM20016px pitch4칸/BM2698px pitch16칸의전체클래스·경계·phase·alpha정확일치,칸별명암범위보존. 두기하출력은AI카운트0. 6출력해시/크기/모델·input/native/parent/mask검사,두배경직접검수. qa/checker_fidelity_review_v1.json.
- BM201/209/244원본2배전체비교에서체크칸내삼각균열·접힘·경계해석을발견,기존후보취소하고원본격자/손상보호재작업으로환원. BM226대각체크는메시화/흐림없어정적후보유지하되정밀칸·UV검증미완료. qa/checker_floor_audit_review.json. BM175기존보류유지.
- 후보229/보류17/미처리38(전투284분모),실제추론244+기하전용2=전투처리246. neural-only카운트는244/타이틀포함245유지;도형출력을AI로세지않음. 처리집계계약명시. 기존20키팩해시보존/미설치/런타임미검증. SR011역사보고서BM221superseded표시.
- Field v2정정:79미지원count경로에허용범위를넓혔지만새검증SC는59개(363→422),추가텍스처0.총SC631레코드중209실패/STCM151검증/1630텍스처·1616해독·576고유보존,833미분류. 원본field inventory v1보존. 신뢰안되는스파스offset/SSCRvariant강제허용안함.
- LOCAL-SR-012기존미처리40원본5페이지직접분류저장. 신규12종24출력46pass은GPU정상종료,검수미완료로카탈로그미통합. 다음첫단계outputs/sr012-review/review-01..04직접검토. field v2도exit0,현재실행프로세스없음.
- Coutputs/체크판_디자인_보존_비교.png 및진행.md갱신. 사용자핵심디자인지적으로검수기준실제강화;전체목표active이며런타임/최종ZIP미완료.\n''')
assert packhashes=={str(p.relative_to(packdir)):sha(p.read_bytes()) for p in packdir.rglob('*') if p.is_file()}
assert read('qa/battle_sr_catalog.json')==cat
print(json.dumps({'selected':list(selected),'revoked_floors':list(revoked),'neural_originals_total':245,'geometry_only':2,'battle_candidates':candidates,'battle_held':processed-candidates,'battle_unprocessed':284-processed},ensure_ascii=False))
