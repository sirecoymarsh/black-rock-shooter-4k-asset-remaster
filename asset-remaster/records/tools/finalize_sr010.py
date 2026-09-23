"""Persist source-reviewed region 5/6 trials and retained rework requirements."""
import copy,hashlib,json,shutil
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1]
C=Path('C:/Users/CadriacLord/Documents/Codex/2026-09-22/brs-hd-ui-fonts')
FINAL='qa/local_sr010_review.json'
if (R/FINAL).exists():raise SystemExit('Already finalized; create a new revision.')
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads((R/p).read_text('utf8'))
def check(p,h):assert sha(Path(p).read_bytes())==h,str(p)
def write(p,v):
    p=R/p;t=p.with_suffix(p.suffix+'.staging');t.write_text(json.dumps(v,ensure_ascii=False,indent=2),'utf8');t.replace(p)
cat=read('qa/battle_sr_catalog.json');groups={g['group_id']:g for g in cat['groups']}
prior={g:copy.deepcopy(v['candidate']) for g,v in groups.items() if v.get('candidate')}
assert len(prior)==159 and len(groups)==284
before_special=copy.deepcopy(cat['source_decode_failures']);before_sky=copy.deepcopy(groups['BM284'])
source=read('qa/local_sr_stage0506_source_review.json')
q=read('qa/local_sr010_inference.json');retry=read('qa/local_sr010_rework.json');anime=read('qa/local_sr010_anime_retry.json')
assert len(q['files'])==62 and len(retry['files'])==20 and len(anime['files'])==4
assert len(q['group_ids'])==31 and not any(groups[g].get('local_sr_attempted') for g in q['group_ids'])
medium={203,212,213,215,218,232,238,241,243,267}
wdn={201,202,209,210,211,226,227,236,237,239,240,244,251,253,279,281}
initial={f'BM{i:03d}':(.5 if i in medium else 0.) for i in medium|wdn}
rework_choices={'BM233':'BM233-wdn08','BM255':'BM255-wdn05','BM268':'BM268-photo035'}
holds={'BM254','BM256'}
assert set(initial)|set(rework_choices)|holds==set(q['group_ids'])
reasons={
 'BM201':'WDN keeps the checker patch placement and major broken floor shapes; invented microtexture remains subject to actual game review.',
 'BM202':'WDN retains the lamp rectangle, wall bands and central inset with less grid-like texture than the medium setting.',
 'BM203':'Medium setting keeps the narrow vertical panel and corner piece with less exaggerated roughness.',
 'BM209':'WDN retains the checker strip and exposed patches without the additional patterned grain of the medium setting.',
 'BM210':'WDN keeps the low-contrast panel divisions; the medium setting adds conspicuous checker-like grain.',
 'BM211':'WDN retains the broad stone-block pattern and crossbands.',
 'BM212':'Medium setting retains the large angular fragments and pale edges with less fine wear.',
 'BM213':'Medium setting retains the diagonal overlapping plates and dark seams.',
 'BM215':'Medium setting retains the broken horizontal strip and thin panel lines on opaque black backing.',
 'BM218':'Medium setting retains the atlas layout, narrow grille lines and white corner. Consumers and UV sampling remain unverified.',
 'BM226':'WDN chosen after whole-sheet and two enlarged crop comparisons; the top panels, narrow vent and checker-floor placement remain visible. This does not verify native UVs.',
 'BM227':'WDN retains broad fractures and dark central gap with more restrained surface grain.',
 'BM232':'Medium setting retains straight window rows and broken pane remnants. No lettering was inferred from the high-contrast fragments.',
 'BM233':'Input sigma0.8 WDN reduces the exaggerated fine mesh/fan texture of initial trials. This softer candidate retains the pale center and rust-colored edge masses; true original HD detail is not known.',
 'BM236':'WDN retains the muted green bands and foreground rubble; medium setting adds patterned grain in the flat upper field.',
 'BM237':'WDN retains fine stone grain and the main pale-slab cracks without the stronger smoothing of the other setting.',
 'BM238':'Medium setting keeps two window rows and main pane remnants with less surface pitting.',
 'BM239':'WDN retains the broken wall/window layout and vertical division. Fine crack interpretations still need game-scale review.',
 'BM240':'WDN retains broad debris shapes and rough ground grain.',
 'BM241':'Medium setting retains thin pale outlines and geometric panels on black backing.',
 'BM243':'Medium setting retains angular fragments and the narrow separate post.',
 'BM244':'WDN retains checker patches and the broad dark floor layout.',
 'BM251':'WDN retains clustered major cracks with less strongly emphasized dark network than the medium setting.',
 'BM253':'WDN retains directional pale cracks with less exaggerated bright contrast.',
 'BM254':'Initial and Photo trials invent pronounced crack networks; sigma0.8 and source-guided variants blur or retain coarse source blocks. Anime6B adds hatching and dark outlines. All eight conditions remain held for another material-aware reconstruction.',
 'BM255':'Input sigma0.5 WDN retains the tiny rough-material masses while slightly reducing harsh grain. Photo exaggerates holes; sigma0.8/source-guided alternatives are too soft or blocky.',
 'BM256':'Initial, filtered and Photo trials add excessive branching cracks around the column/panel regions. Guided output retains blockiness; Anime6B adds black outlined/hatching style. All eight conditions held; preserve column tracks and identify the upper motif before a new treatment.',
 'BM267':'Medium setting retains silver-edged geometric panels and the thin right-hand strip.',
 'BM268':'Photo with input sigma0.35 retains long vertical golden grain better than the cloth-like WDN output; guided/strong filtering were too coarse or soft. Material identity is not asserted.',
 'BM279':'WDN retains separate dark and pale rock halves with less dark branching than the medium setting; the exact source half boundary was isolated during inference.',
 'BM281':'WDN retains long pale slab divisions and the broken dark recess.'}
assert set(reasons)==set(q['group_ids'])
checked=[];selected={};models=set();all_passes=0
reports=[('qa/local_sr010_inference.json',q),('qa/local_sr010_rework.json',retry),('qa/local_sr010_anime_retry.json',anime)]
for name,report in reports:
    total=0
    for row in report['files']:
        gid=row['group_id'];g=groups[gid];src=Image.open(row['source']).convert('RGBA')
        assert src.size==(g['width'],g['height']) and sha(src.tobytes())==g['rgba_sha256']==row['source_rgba_sha256']
        assert src.getchannel('A').getextrema()==(255,255)
        check(g['representative']['source'],g['representative']['source_sha256'])
        for m in row.get('model_sources',[row.get('model')]):
            pair=(m['path'],m['sha256'])
            if pair not in models:check(*pair);models.add(pair)
        check(row['output'],row['output_sha256']);out=Image.open(row['output']).convert('RGBA')
        assert out.size==(src.width*8,src.height*8)==tuple(row['output_size'])
        assert out.getchannel('A').getextrema()==(255,255)
        coverage=np.zeros((src.height,src.width),np.uint8);passes=0
        for part in row['parts']:
            x0,y0,x1,y1=part['source_box'];assert 0<=x0<x1<=src.width and 0<=y0<y1<=src.height
            coverage[y0:y1,x0:x1]+=1;small=(x1-x0,y1-y0)
            if 'native' in part:
                for key in ['input','native']:check(part[key],part[key+'_sha256'])
                assert Image.open(part['input']).size==small
                assert Image.open(part['native']).size==(small[0]*4,small[1]*4)
                if report is q:assert Image.open(part['input']).convert('RGB').tobytes()==src.crop((x0,y0,x1,y1)).convert('RGB').tobytes()
                passes+=1
        assert np.all(coverage==1) and passes==row['new_neural_passes']
        if 'parent' in row:check(row['parent'],row['parent_sha256'])
        total+=passes
        pick=(report is q and initial.get(gid)==row['denoise_strength']) or (report is retry and row.get('id')==rework_choices.get(gid))
        why=reasons[gid] if pick or gid in holds else 'Alternative not selected. '+reasons[gid]
        evidence=list(report['comparison_sheets'])
        if gid=='BM226':evidence.append(str(R/'outputs/sr010-BM226-detail.png'))
        row['visual_review']={'reviewer':'Codex internal','status':'selected_for_game_review' if pick else 'held_rework_required' if gid in holds else 'not_selected','reason':why,'evidence':evidence}
        checked.append({'group_id':gid,'output':row['output'],'output_sha256':row['output_sha256'],'source_ptm_and_rgba_verified':True,'model_input_native_parent_hashes_verified':True,'source_panels_partition_exactly_once':True,'native4x_final8x_verified':True,'opaque255_exact':True,'new_neural_passes':passes})
        if pick:
            assert gid not in selected
            selected[gid]={'source_report':name,'source_rgba_sha256':g['rgba_sha256'],'output':row['output'],'output_sha256':row['output_sha256'],'reason':reasons[gid],'status':'static_candidate_for_consumer_and_game_review','runtime_verified':False,'release_eligible':False}
    assert total==report['new_neural_passes'];all_passes+=total
assert len(checked)==86 and all_passes==104 and len(selected)==29
assert len(source['classifications'])==84 and 'all directly inspected' in source['visual_review']
for row in source['classifications']:
    gid=row['group_id'];g=groups[gid];assert g['rgba_sha256']==row['source_rgba_sha256']
    g.update(classification=row['classification'],classification_reason=row['reason'],classification_review='Codex internal: sr010 source-01..10 directly inspected')
for gid in q['group_ids']:
    groups[gid]['local_sr_attempted']=True;groups[gid]['candidate']=selected.get(gid)
    if gid in holds:groups[gid]['review_hold_reason']=reasons[gid]
for gid,v in prior.items():assert groups[gid]['candidate']==v
assert cat['source_decode_failures']==before_special and groups['BM284']==before_sky
pcount=sum(bool(g.get('local_sr_attempted')) for g in groups.values());ccount=sum(bool(g.get('candidate')) for g in groups.values())
assert pcount==202 and ccount==188
summary=cat['processing_summary'];summary.update(battle_groups_locally_processed=pcount,battle_static_candidates=ccount,battle_processed_without_accepted_candidate=pcount-ccount,battle_groups_not_yet_processed=len(groups)-pcount,all_unique_originals_locally_processed=pcount+1,latest_rework=FINAL,new_unique_originals_latest_rework=31,checked_output_records_latest_rework=86,new_unique_originals_LOCAL_SR_010=31,neural_passes_LOCAL_SR_010=104)
bindings=read('qa/battle_map_runtime_links.json')['bindings']
mapped={g['group_id'] for g in groups.values() if any(b['source_rgba_sha256']==g['rgba_sha256'] and b['size']==[g['width'],g['height']] for b in bindings)}
assert not set(q['group_ids'])&mapped
pack=read('qa/local_sr_observed_review_pack_v2.json');pp=Path(pack['path']);check(pp/'textures.ini',pack['textures_ini_sha256'])
assert len(pack['keys'])==20
population={str(p.relative_to(pp)):sha(p.read_bytes()) for p in pp.rglob('*') if p.is_file()}
evidence=sorted(set(sum((p['comparison_sheets'] for _,p in reports),[])+[str(R/'outputs/sr010-BM226-detail.png')]))
for p in source['pages']:check(p['path'],p['sha256'])
field=read('qa/field_map_format_probe.json');assert field['root_count']==88 and field['decoded_magic_counts']=={'53431000':88}
report={'schema':'brs-local-sr-review/v10','batch':'LOCAL-SR-010','selected':selected,'new_holds':{g:reasons[g] for g in sorted(holds)},'checked_outputs':checked,'new_unique_originals':31,'new_actual_local_neural_passes':104,'prior_candidates_preserved':159,'processing_summary':copy.deepcopy(summary),'review_evidence':[{'path':p,'sha256':sha(Path(p).read_bytes())} for p in evidence],'source_reviewed_groups':84,'remaining_stage0506_groups':[g for g in source['group_ids'] if g not in q['group_ids']],'field_map_probe':'qa/field_map_format_probe.json','field_probe_limitation':'88 gzip roots share SC 10 00 magic. Embedded texture hits are unbound leads; no new field texture acceptance.','new_sources_observed_keys':0,'pack_unchanged_keys':20,'pack_file_hashes':population,'runtime_verified':False,'release_eligible':False,'local_inference':True,'image_upload_this_batch':False,'scripts':{p:sha((R/'tools'/p).read_bytes()) for p in ['prepare_sr010_sources.py','batch_sr010_opaque.py','rework_sr010_materials.py','rework_sr010_anime.py','probe_field_maps.py','finalize_sr010.py']}}
f=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',20);s=Image.new('RGB',(1080,1640),'#293440');d=ImageDraw.Draw(s)
for j,label in enumerate(['원본 단순 확대','로컬 AI 처리 · 게임 검수 전']):d.text((j*540+10,8),label,font=f,fill='white')
for i,gid in enumerate(['BM201','BM238','BM268','BM281']):
    src=Image.open(groups[gid]['representative']['png']).convert('RGB');out=Image.open(selected[gid]['output']).convert('RGB');scale=min(510/src.width,320/src.height,8);wh=(round(src.width*scale),round(src.height*scale))
    for j,im in enumerate([src,out]):
        x=j*540+10;y=50+i*395;d.text((x,y),gid+f' · 표시 {scale:.2f}배',font=f,fill='white');s.paste(im.resize(wh,Image.Resampling.NEAREST if j==0 else Image.Resampling.LANCZOS),(x,y+35))
s.save(R/'outputs/local_sr010_selected.png');shutil.copyfile(R/'outputs/local_sr010_selected.png',C/'outputs/로컬_업스케일_5·6지역_검수.png')
backup=R/'qa/backups/before-sr010-finalize';backup.mkdir(parents=True,exist_ok=False)
to_save=[*reports,('qa/battle_sr_catalog.json',cat)]
for name,_ in to_save:shutil.copyfile(R/name,backup/Path(name).name)
for name,obj in to_save:write(name,obj)
write(FINAL,report)
note=f'''# 로컬 업스케일 진행 — LOCAL-SR-010

- 실제 로컬 GPU 추론을 거친 고유 원본 **203종**: 타이틀 1 + 전투재질 202.
- 전투맵 284종 중 정적 검수 후보 **188종**, 처리 후 보류 **14종**, 미처리 **82종**입니다. 게임 전체 완료율은 아닙니다.
- 5·6지역 원본 84종을 직접 확인했습니다. 그중 신규 31종의 초기 비교·재작업·추가 모델 시험을 합쳐 **86개 결과·실제 로컬 추론 104회**를 검사하고 29종을 게임 검수 후보로 골랐습니다.
- 과한 결이 생긴 5종을 재작업했습니다. 3종은 질감 강도/방향을 개선한 후보를 선정했고, 균열이 과장되는 2종은 애니메이션 모델까지 비교했으나 보류했습니다. 해당 모델은 이번 재질을 검은 선·해칭으로 바꾸어 미채택입니다.
- AI 본래 처리 배율은 4배, 이후 보간 2배로 최종 8배 크기입니다. 이번 작업은 로컬 RTX 5080에서 진행했고 외부 이미지 업로드는 없습니다.
- 기존 정확한 관측키 20개 검수팩은 유지합니다. 신규 31종은 관측키가 아직 연결되지 않았습니다. {pack['path']}
- 필드맵 88개의 압축을 확인했고 SC 컨테이너 구조를 조사하기 시작했습니다. 내부 이미지의 테이블 연결과 해독은 아직 검증되지 않았습니다.
- 실제 교체 표시, Orbit 한글 폰트와 LOCK ON, 전체 지역·필드·적·효과·컷신 검증은 남았습니다. Windows 검수창 접근 오류 해소는 확인되지 않았고 최종 배포 ZIP은 없습니다.
- 다음: 남은 투명 철골·사슬·발광 문양 53종(5·6지역), 이전 지역 미처리 및 보류 14종, 필드맵 SC 구조와 다른 자산을 이어갑니다. 화면 접근이 가능해지면 고정 에뮬에 ISO를 직접 지정해 게임 검수를 진행합니다.
'''
(C/'outputs/로컬_업스케일_진행.md').write_text(note,'utf8')
with (R/'PROGRESS.md').open('a',encoding='utf8') as f:
    f.write('''

## 2026-09-23 — LOCAL-SR-010: 5·6지역31종과 필드맵 형식 조사

- 이전 목표턴은 progress: LOCAL-SR-009 24신규원본/120pass/22후보 및 특수하늘3건의 정확한 해독을 반영했다. 이번 턴도 실제 신규추론과재작업/분류갱신을 완료하여 progress. 전체목표 active.
- 원본84종의10페이지전체직접검토. opaque31종 WDN/DNI0.5 62출력/70actualpass. BM256은4개눈에보이는구역, BM279는좌우2구역을격리. source partition은nativeUV증거아님. 나머지53종은사슬·가느다란골격·발광선·단색/별무리등으로분류,범위제외없음.
- 초기11페이지비교→BM233/254/255/256/268 과한메시·갈라짐·천질감발견,입력sigma.5/.8 WDN과photo.35 15추론출력/24actualpass 및source-guided5후처리,5재작업페이지검수.254/256 추가anime6B두설정4출력/10pass도검은해칭과굵은균열로미채택.총86결과/실제104로컬pass,외부업로드없음.
- 29후보: WDN BM201/202/209/210/211/226/227/236/237/239/240/244/251/253/279/281, DNI0.5 BM203/212/213/215/218/232/238/241/243/267, 재작업BM233-wdn08/BM255-wdn05/BM268-photo035. BM226 top/floor2crop도직접확인. BM254/256은각8조건모두보류,원본윤곽과재질을더보존하는재작업필요.
- 86출력의원본PTM/RGBA·모델·input/native/parent/output SHA,source분할완전성,4x/8x크기와opaque255검사통과. 기존159후보/BM284/미해독3항목보존. 전투202처리/188후보/14보류/82미처리,고유원본누계203(타이틀1포함). qa/local_sr010_review.json. 전체게임완료율아님.
- 신규31종관측키0,기존20키시험팩변경/설치없음. Windows화면접근오류외부변화증거없어에뮬재실행/검은화면반복없음. 런타임및최종ZIP미완료.
- 고정ISO를재해시하고FLD/MAP88개를읽기전용gzip검사,모두magic53431000(SC10)이며내부STCM/PTMD후보위치기록. qa/field_map_format_probe.json. magic스캔은텍스처테이블/소비증거가아니며새field텍스처승인없음. 다음SC헤더및STCM포인터테이블연결을해독한다.
- 출력 로컬_업스케일_5·6지역_검수.png/진행.md 갱신. GUI접근불가로Codex미리보기사용. 다음5·6지역잔여53알파/도형종·기존미처리/14보류·FLD/적/효과/컷신계속,실행은고정exe+ISO CLI 원칙유지.
''')
assert read('qa/battle_sr_catalog.json')==cat and read(FINAL)==report
assert population=={str(p.relative_to(pp)):sha(p.read_bytes()) for p in pp.rglob('*') if p.is_file()}
print(json.dumps({'new_candidates':29,'new_holds':sorted(holds),'outputs':len(checked),'actual_local_passes':all_passes,'summary':summary},ensure_ascii=False))
