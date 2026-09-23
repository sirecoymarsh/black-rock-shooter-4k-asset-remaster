"""Record directly inspected local and authored candidates with explicit rejected work."""
import copy,json,hashlib,shutil,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];C=Path('C:/Users/CadriacLord/Documents/Codex/2026-09-22/brs-hd-ui-fonts');FINAL='qa/local_sr012_review.json'
if (R/FINAL).exists():raise SystemExit('Reviewed already; create a new revision.')
def read(p):return json.loads((R/p).read_text('utf8'))
def sha(b):return hashlib.sha256(b).hexdigest()
def check(p,h):assert sha(Path(p).read_bytes())==h,str(p)
def write(p,v):
    path=R/p;tmp=path.with_suffix(path.suffix+'.staging');tmp.write_text(json.dumps(v,ensure_ascii=False,indent=2),'utf8');tmp.replace(path)
cat=read('qa/battle_sr_catalog.json');before=copy.deepcopy(cat);groups={g['group_id']:g for g in cat['groups']};assert len(groups)==284 and sum(bool(g.get('candidate')) for g in groups.values())==229
names=['qa/local_sr012_inference.json','qa/local_sr012_rework.json','qa/local_sr012_structure.json','qa/local_sr012_manual_grille.json','qa/local_sr012_manual_hybrid.json','qa/local_sr012_manual_shaded.json','qa/local_sr012_smoke_alpha.json'];reports=[(n,read(n)) for n in names];q=reports[0][1];proposed=read('qa/local_sr012_proposed_review.json');ids=q['group_ids'];assert len(ids)==12 and not any(groups[g]['local_sr_attempted'] for g in ids)
choice={g:f'{g}-{proposed["choices"][g]}' for g in ids if g not in {'BM087','BM110','BM115'}};choice['BM110']='BM110-codex-grid-and-fastener-v3';choice['BM111']='BM111-wdn-source-bicubic-alpha'
holds={'BM087':'All four local model conditions lose/merge original small windows; source-structure retries recover source marks but remain too soft. Direct facade redraw is required.','BM115':'Initial results add strong metallic sheen and granular edges; filtered and source-guided retries trade that for excessive softness. Direct source-faithful material redraw is required.'}
reasons={
 'BM062':'Photo keeps thin ruined beams and blue source masses with less rough surface grain. Full views on both mattes inspected.',
 'BM063':'Photo keeps thin scaffold projections and rubble silhouette, with restrained material detail. Both mattes inspected.',
 'BM065':'WDN keeps diamond lattice spacing, crossed braces and thin bars. Full atlas and native 8x lattice detail inspected on both mattes.',
 'BM074':'Photo keeps two very thin horizontal strips and separated lower plate; detail views on both mattes retain the strips.',
 'BM079':'WDN retains four vertical members and their open gaps. Added surface relief is an inference; source spacing and matte visibility checked.',
 'BM101':'Photo keeps three window columns and original horizontal divisions with calmer surfaces. Original bilinear alpha used without alpha inference.',
 'BM110':'Codex-authored straight grid restores nine full horizontal slats, four vertical slats and the four source row-15 segments. Authored central cross and two holes replace the changed model center. Surrounding frame/rings retain local WDN material, and center broad shading comes from the source. Static candidate only; full geometry/UV/runtime remains unverified.',
 'BM111':'WDN RGB with source bicubic alpha retains faint peripheral particles lost in the original WDN/Photo trials. The tested weak-alpha loss count is zero, while threshold128 IoU remains below one; no all-particle geometry claim.',
 'BM116':'Photo retains two paired window rows and the lower panel, with cleaner glass than WDN. Source bilinear alpha verified.',
 'BM118':'Photo retains paired window rows and dark lower panel with less grain. Source bilinear alpha verified.'}
assert set(choice)==set(reasons) and set(choice)|set(holds)==set(ids)
checked=[];selected={};models=set();initial={};passes=0;allrows={}
for name,rep in reports:
    count=0
    for row in rep['files']:
        gid=row['group_id'];g=groups[gid];ident=row.get('id',gid+'-'+row.get('model_id','unknown'));allrows[ident]=row;src=Image.open(row['source']).convert('RGBA');assert sha(src.tobytes())==row['source_rgba_sha256']==g['rgba_sha256'];check(g['representative']['source'],g['representative']['source_sha256']);check(row['output'],row['output_sha256']);out=Image.open(row['output']).convert('RGBA');assert out.size==(src.width*8,src.height*8)==tuple(row['output_size'])
        if 'model' in row:
            m=row['model'];key=(m['path'],m['sha256'])
            if key not in models:check(*key);models.add(key)
        for key in ['parent','alpha_parent','manual_parent','vector','mask','raw_render']:
            if key in row:check(row[key],row[key+'_sha256'])
        actual=0;partproof=[];cover=np.zeros((src.height,src.width),np.uint8);ref=Image.new('L',out.size)
        for part in row.get('parts',[]):
            x0,y0,x1,y1=part['source_box'];assert 0<=x0<x1<=src.width and 0<=y0<y1<=src.height;cover[y0:y1,x0:x1]+=1;wh=(x1-x0,y1-y0)
            for key in ['input_rgb','input_alpha','rgb_native','alpha_native','input','native']:
                if key not in part:continue
                check(part[key],part[key+'_sha256']);im=Image.open(part[key]);scale=4 if 'native' in key else 1;assert im.size==(wh[0]*scale,wh[1]*scale);actual+=int('native' in key)
            ref.paste(src.crop((x0,y0,x1,y1)).getchannel('A').resize((wh[0]*8,wh[1]*8),Image.Resampling.BILINEAR),(x0*8,y0*8));partproof.append(part['source_box'])
        if row.get('parts'):assert np.all(cover==1)
        if rep is q:
            check(row['reference_alpha'],row['reference_alpha_sha256']);assert ref.tobytes()==Image.open(row['reference_alpha']).convert('L').tobytes();a=np.asarray(out.getchannel('A'));lin=np.asarray(ref);original=np.asarray(src.getchannel('A'));down=np.asarray(out.getchannel('A').resize(src.size,Image.Resampling.LANCZOS));assert np.all(a[lin==0]==0) and np.all(a[lin==255]==255);gt=original>=128;pred=down>=128;union=(gt|pred).sum();metric={'mass_ratio':float(a.mean()/original.mean()),'source_threshold128_iou':float((gt&pred).sum()/union) if union else 1.,'source_ge16_reduced_below8':int(((original>=16)&(down<8)).sum()),'outside_panel_bilinear_support':0}
            for k,v in metric.items():assert abs(v-row['alpha_metrics'][k])<1e-12,(gid,k)
            assert metric['source_ge16_reduced_below8']==(5 if gid=='BM111' else 0)
            if gid=='BM111':assert choice[gid]!=ident
            if gid in {'BM101','BM116','BM118'}:assert out.getchannel('A').tobytes()==ref.tobytes()
            alpha={'panel_bilinear_reconstructed':True,'zero_and_255_support_verified':True,**metric};initial[(gid,row['model_id'])]=row
        elif 'alpha_kernel' in row:
            par=np.asarray(Image.open(row['parent']).convert('RGBA'));assert np.array_equal(np.asarray(out)[:,:,:3],par[:,:,:3]);kernel={'bicubic':Image.Resampling.BICUBIC,'lanczos':Image.Resampling.LANCZOS}[row['alpha_kernel']];lin=np.asarray(src.getchannel('A').resize(out.size,Image.Resampling.BILINEAR));expect=np.asarray(src.getchannel('A').resize(out.size,kernel)).copy();expect[lin==0]=0;expect[lin==255]=255;assert np.array_equal(expect,np.asarray(out.getchannel('A')))
            orig=np.asarray(src.getchannel('A'));down=np.asarray(out.getchannel('A').resize(src.size,Image.Resampling.LANCZOS));gt=orig>=128;pred=down>=128;metrics={'source_ge16_reduced_below8':int(((orig>=16)&(down<8)).sum()),'source_threshold128_iou':float((gt&pred).sum()/(gt|pred).sum()),'mass_ratio':float(expect.mean()/orig.mean()),'outside_source_bilinear_support':int((expect[lin==0]>0).sum())};assert metrics==row['alpha_metrics']
            if choice[gid]==ident:assert metrics['source_ge16_reduced_below8']==0
            alpha={'source_alpha_kernel_reconstructed':True,'RGB_exact_to_local_parent':True,**metrics}
        elif 'alpha_parent' in row:
            assert row['alpha_parent']==initial[(gid,'wdn')]['output'];assert out.getchannel('A').tobytes()==Image.open(row['alpha_parent']).convert('RGBA').getchannel('A').tobytes();alpha={'exact_to_initial_wdn_alpha':True}
        else:
            assert ident=='BM110-codex-vector-v1';assert out.getchannel('A').tobytes()==src.getchannel('A').resize(out.size,Image.Resampling.BILINEAR).tobytes();alpha={'exact_to_source_bilinear8x':True}
        assert actual==row['new_neural_passes'];count+=actual;pick=choice.get(gid)==ident
        reason=reasons.get(gid,holds.get(gid));row['visual_review']={'reviewer':'Codex internal','status':'selected_for_game_review' if pick else 'not_selected','reason':reason if pick else 'Not selected. '+reason,'runtime_verified':False}
        if ident=='BM110-codex-vector-v1':row['visual_review']['reason']='Full-vector material is too flat and source-alpha reapplication produces colored edge specks. Replaced by vector grid/center over the local material.'
        if ident=='BM110-codex-grid-and-fastener-v2':row['visual_review']['reason']='Geometry is retained but center metal is flat. Superseded by source-shaded v3.'
        checked.append({'id':ident,'source_ptm_rgba_and_output_hash_verified':True,'model_parent_vector_mask_hashes_verified':True,'size8x_verified':True,'part_coverage':partproof,'alpha':alpha,'actual_neural_passes':actual})
        if pick:selected[gid]={'source_report':name,'id':ident,'source_rgba_sha256':g['rgba_sha256'],'output':row['output'],'output_sha256':row['output_sha256'],'reason':reason,'status':'static_candidate_for_consumer_and_game_review','runtime_verified':False,'release_eligible':False}
    assert count==rep['new_neural_passes'];passes+=count
assert len(checked)==41 and passes==53 and len(selected)==10
# Inspect concrete vector geometry and the final pixels, not just declared metadata.
v=allrows['BM110-codex-vector-v1'];root=ET.parse(v['vector']).getroot();rects=root.findall('.//{http://www.w3.org/2000/svg}rect');hs=[e for e in rects if e.get('fill','').startswith('url(#h')];vs=[e for e in rects if e.get('fill','').startswith('url(#v')];assert len(hs)==9 and len(vs)==4
source=np.asarray(Image.open(v['source']).convert('RGBA'));horizontal=[8,10,12,14,17,19,21,23,25];vertical=[9,15,21,27]
assert [int(round(float(e.get('y'))-.1)) for e in hs]==horizontal;assert [int(round(float(e.get('x'))-.12)) for e in vs]==vertical
for y in horizontal:assert np.median(source[y,16:21,:3])>np.median(source[7,16:21,:3])
for x in vertical:assert source[13,x,:3].mean()>source[13,x+1,:3].mean()
final=allrows['BM110-codex-grid-and-fastener-v3'];f=np.asarray(Image.open(final['output']).convert('RGBA'));raw=np.asarray(Image.open(v['raw_render']).convert('RGBA'));assert np.array_equal(f[48:208,48:256,:3],raw[48:208,48:256,:3])
prev=np.asarray(Image.open(final['parent']).convert('RGBA'));metal=np.asarray(Image.open(final['mask']).convert('L'))>0;assert np.array_equal(f[~metal],prev[~metal]);initial_wdn=np.asarray(Image.open(initial[('BM110','wdn')]['output']).convert('RGBA'));m2=allrows['BM110-codex-grid-and-fastener-v2'];mask=np.asarray(Image.open(m2['mask']).convert('L'))>0;assert np.array_equal(f[~mask],initial_wdn[~mask])
gpt=reports[3][1]['gpt_attempt'];check(gpt['output'],gpt['output_sha256']);assert gpt['decision']=='rejected' and Image.open(gpt['output']).size==tuple(gpt['output_size'])
mapped={g['group_id'] for g in groups.values() if any(b['source_rgba_sha256']==g['rgba_sha256'] and b['size']==[g['width'],g['height']] for b in read('qa/battle_map_runtime_links.json')['bindings'])};assert not set(ids)&mapped
pack=read('qa/local_sr_observed_review_pack_v2.json');pp=Path(pack['path']);check(pp/'textures.ini',pack['textures_ini_sha256']);assert len(pack['keys'])==20;packhashes={str(p.relative_to(pp)):sha(p.read_bytes()) for p in pp.rglob('*') if p.is_file()}
for b in pack['battle_binding_evidence']:check(pp/pack['keys'][b['key']],b['output_sha256'])
for gid in ids:
    groups[gid]['local_sr_attempted']=True;groups[gid]['candidate']=selected.get(gid)
    if gid in holds:groups[gid]['review_hold_reason']=holds[gid]
groups['BM110']['manual_geometry_reconstruction']=True
for old in before['groups']:
    if old['group_id'] not in ids:assert groups[old['group_id']]==old
assert cat['source_decode_failures']==before['source_decode_failures']
local=sum(bool(g.get('local_sr_attempted')) for g in groups.values());geom=sum(bool(g.get('geometry_processed')) and not g.get('local_sr_attempted') for g in groups.values());accepted=sum(bool(g.get('candidate')) for g in groups.values());assert (local,geom,accepted)==(256,2,239)
summary=cat['processing_summary'];summary.update(battle_groups_locally_processed=local,all_unique_originals_locally_processed=local+1,battle_groups_processed_any_method=local+geom,battle_static_candidates=accepted,battle_processed_without_accepted_candidate=local+geom-accepted,battle_groups_not_yet_processed=284-local-geom,battle_groups_never_locally_inferred=284-local,latest_rework=FINAL,new_unique_originals_latest_rework=12,checked_output_records_latest_rework=41,new_unique_originals_LOCAL_SR_012=12,neural_passes_LOCAL_SR_012=53,generative_calls_LOCAL_SR_012=1,manual_reconstructed_groups_LOCAL_SR_012=1)
proposed['final_selected']={g:r['id'] for g,r in selected.items()};proposed['holds']=holds;proposed['review_status']='All model, alpha matte, detail, structural retry and manual comparison pages directly inspected. Two groups still need direct redraw. Runtime unverified.';proposed['superseded_matte_choices']={'BM087':'held after detail review','BM110':'local WDN replaced by authored grid/fastener v3','BM115':'held after all retries','BM111':'initial WDN loses five faint source samples; replaced by source bicubic alpha'}
evidence=sorted(set(sum((rep['comparison_sheets'] for _,rep in reports),[])+proposed['matte_pages']+proposed['detail_pages']+[str(R/'outputs/sr012_BM087_facade_source.png')]))
report={'schema':'brs-local-sr-review/v12','batch':'LOCAL-SR-012','selected':selected,'new_holds':holds,'checked_outputs':checked,'new_unique_originals':12,'new_actual_local_neural_passes':53,'external_generative_calls':1,'gpt_attempt':gpt,'manual_authorship':'Codex internal','manual_geometry_checks':{'horizontal_source_rows':horizontal,'vertical_source_columns':vertical,'source_line_evidence_verified':True,'final_grid_rgb_exact_to_authored_render':True,'outside_manual_edit_mask_exact_to_local_parent':True,'original_alpha_bytes_exact':False},'prior_candidates_preserved':229,'processing_summary':copy.deepcopy(summary),'review_evidence':[{'path':p,'sha256':sha(Path(p).read_bytes()),'reviewer':'Codex internal'} for p in evidence],'new_sources_observed_keys':0,'pack_unchanged_keys':20,'pack_hashes':packhashes,'runtime_verified':False,'release_eligible':False,'limitations':['Static candidates still require native UV and actual game display checks.','Only original source-bilinear zero/255 alpha support is constrained for neural-alpha outputs; single-threshold loss checks do not prove all geometry.','Manual grid/center is an explicit source-informed reconstruction, not recovered unknown original HD artwork.','BM087 small windows and BM115 rubble remain held for direct redraw; their local attempts were not accepted.','Full-vector v1 was rejected for flat material and edge specks; chosen v3 keeps local outer material.','284 is the battle-map denominator only. Field, enemy, effects and whole-game verification remain unfinished.'],'scripts':{p:sha((R/'tools'/p).read_bytes()) for p in ['batch_sr012_alpha.py','prepare_sr012_review.py','rework_sr012.py','structure_sr012.py','draw_sr012_grille.py','hybrid_sr012_grille.py','shade_sr012_fastener.py','repair_sr012_smoke_alpha.py','finalize_sr012.py']}}
backup=R/'qa/backups/before-sr012-finalize';backup.mkdir(parents=True,exist_ok=False)
save_reports=reports+[('qa/local_sr012_proposed_review.json',proposed),('qa/battle_sr_catalog.json',cat)]
for name,_ in save_reports:shutil.copyfile(R/name,backup/Path(name).name)
for name,obj in save_reports:write(name,obj)
write(FINAL,report)
userpic=C/'outputs/직접_재구성_환기구_비교.png';shutil.copyfile(R/'outputs/sr012_manual_shaded_BM110.png',userpic)
(C/'outputs/로컬_업스케일_진행.md').write_text('''# 로컬 업스케일 진행 — LOCAL-SR-012 / 직접 재구성

- 신규 원본12종의 로컬 처리와 재작업을 검수했습니다. 로컬 GPU 추론53회, 로컬/직접 그린 결과41개를 검사했습니다. 10종을 정적 후보로 추가했고 작은 창이 있는 건물(BM087)과 잔해(BM115)는 직접 재작업 대상으로 남겼습니다.
- 환기구(BM110)는 로컬 모델4조건에서 선 변형을 확인했습니다. GPT 이미지 편집1회도 선 개수·원형 중심부·배치가 달라 제외했습니다. 이1회는 외부 이미지 처리이며 로컬 추론으로 세지 않습니다.
- 원본 좌표의 가로선9개·세로선4개·중간 짧은선4개와 중심부 십자 홈/작은 구멍2개를 Codex가 도형으로 다시 그렸습니다. 바깥 금속 재질은 로컬 결과를 사용하고 원본 명암을 중심부에 적용한 v3를 정적 후보로 기록했습니다.
- 누계 실제 로컬 추론 고유 원본257종(타이틀1+전투256), 도형 처리 전용2종. 전투284종 중 정적 후보239/처리 후 보류19/미처리26입니다. 전체 게임 완료율이 아닙니다.
- 체크판 디자인 보존 기준 유지. BM200/221/269는 칸·색·위치 보호, BM175/201/209/244 재작업 및 BM226 정밀 검사가 남았습니다.
- 필드맵은 이전 부분 추출 상태(576종)이며 이번에 완료로 바뀐 부분은 없습니다. 전체 지역·EX/진엔딩·적·효과·컷신, Orbit 한글 폰트·LOCK ON, 실제 게임 표시와 최종 ZIP 검증은 남았습니다.
- 기존20키 검수팩은 바이트 변경/설치하지 않았습니다. 이번12종의 정확한 관측키는 아직 없으며 실제 게임 확인 전입니다.
- 다음: BM087 창 무늬와 BM115 잔해 직접 재구성, 체크 바닥·철망 보류작 재작업, 필드의 미지원 구획 해독과 전체 범위 확장. 에뮬 실행은 고정exe+ISO 직접 지정 원칙을 유지합니다.
''','utf8')
with (R/'PROGRESS.md').open('a',encoding='utf8') as f:f.write('''

## 2026-09-23 — LOCAL-SR-012: 신규12종 검수 및 환기구 직접 재구성
- 이전 goal turn은 CHECKER-001 후보/보류 갱신으로 progress. 이번 시작 시 최신 PROGRESS/카탈로그/실제 SR012 출력을 재확인했다.
- 신규12종 초기24출력/46pass, 4모델비교 페이지+4밝고어두운 matte페이지+6상세 crop 직접검수. BM087 창소실·BM110격자휨/중심변형·BM115과도광택 발견. 추가 anime/general raw 4결과6pass와 BM115 filtered1pass+guided2후처리. 구조guide5추가후처리. 총 로컬53pass.
- 사용자 지시 ‘로컬이 영 별로면 네가 직접 그리도록’ 반영. imagegen built-in BM110 1외부편집(1774x887)도 선개수/중심부/배치변경으로 불채택; alpha128 축소IoU .8425656. 원본/생성파일/해시 qa/local_sr012_manual_grille.json. 외부처리를 로컬로 세지 않음.
- Codex 직접 SVG BM110 v1: source y8/10/12/14/17/19/21/23/25 가로9개, x9/15/21/27 세로4개 및 y15 x11/17/23/29 짧은선4개. 중심 십자홈·하단2구멍 재구성. 전체v1 재질평면/edge색점으로제외, local외곽+직접격자/중심v2 후 원본명암v3 선택. SVG자체개수/좌표·원본row/col증거·최종gridRGB완전일치·mask밖초기WDN완전일치·alpha부모일치검사. true HD 복원주장안함.
- 41출력 원본PTM/RGBA·모델/input/native/parent/vector/mask/output 해시 및4x/8x크기/분할coverage 검증. 초기alpha metrics재계산에서BM111두모델약알파5점손실발견. source bicubic/Lanczos alpha2후처리비교후bicubic선택(약알파손실0/IoU .88047/질량+0.1558%). 초기실패값보존. zero255support검증; BM101116118 sourcebilinear alpha정확일치. 전체형상·UV·게임증거아님.
- 선택10: Photo BM062/063/074/101/116/118; WDN BM065/079; WDN RGB+source bicubic alpha BM111; 직접재구성v3 BM110. BM087와BM115는 모든trial품질미달로보류, 직접재작업필요. qa/local_sr012_review.json. 기존229후보/나머지모든그룹/특수3건보존.
- 누계실제neural원본257(타이틀1+BM256),geometry-only2별도. BM후보239/보류19/미처리26,처리258. 신규12관측키0,기존20키검수팩바이트보존/미설치/런타임미검증. Coutputs/직접_재구성_환기구_비교.png 와진행.md갱신. 전체목표active.
- 다음: BM087원본 facade 128x76 확대(outputs/sr012_BM087_facade_source.png) 기준창무늬 직접재구성, BM115잔해재작업. 체크 BM175/201/209/244 및 BM226정밀audit, fieldv2 미지원구획 해독/576원본분류, 적/효과/컷신 확장. GUI접근복구증거없어재실행/검은화면루프없음.
''')
assert packhashes=={str(p.relative_to(pp)):sha(p.read_bytes()) for p in pp.rglob('*') if p.is_file()};assert read('qa/battle_sr_catalog.json')==cat
print(json.dumps({'checked':len(checked),'local_passes':passes,'gpt_calls':1,'selected':list(selected),'held':list(holds),'candidates':239,'total_neural_originals':257},ensure_ascii=False))
