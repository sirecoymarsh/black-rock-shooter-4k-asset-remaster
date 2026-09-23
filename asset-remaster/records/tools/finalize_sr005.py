"""Freeze reviewed LOCAL-SR-005 decisions; preserve all earlier candidates."""
import sys,json,hashlib,shutil
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
sys.stdout.reconfigure(encoding='utf8')
R=Path(__file__).resolve().parents[1];C=Path('C:/Users/CadriacLord/Documents/Codex/2026-09-22/brs-hd-ui-fonts')
def sha(b):return hashlib.sha256(b).hexdigest()
def read(n):return json.loads((R/n).read_text('utf8'))
def write(n,x):(R/n).write_text(json.dumps(x,ensure_ascii=False,indent=2),'utf8')
cat=read('qa/battle_sr_catalog.json');groups={g['group_id']:g for g in cat['groups']};before={gid:json.loads(json.dumps(g.get('candidate'))) for gid,g in groups.items() if g.get('candidate')}
reports={n:read('qa/'+n+'.json') for n in ['local_sr_stage02_materials_v1','local_sr_stage02_rework_v2','local_sr_stage02_refine_v3']}
review_path='qa/local_sr_stage02_review_v3.json';previous_review=read(review_path) if (R/review_path).exists() else None
old_processed=set(previous_review['prior_processed_groups']) if previous_review else {gid for gid,g in groups.items() if g.get('local_sr_attempted')}
selected={};checked=[];processed=set();verified_models=set()
def verify(row):
    gid=row['group_id'];processed.add(gid);src=Image.open(row['source']).convert('RGBA');assert src.size==(groups[gid]['width'],groups[gid]['height']) and sha(src.tobytes())==row['source_rgba_sha256']==groups[gid]['rgba_sha256']
    p=Path(row['output']);assert sha(p.read_bytes())==row['output_sha256'];im=Image.open(p).convert('RGBA');assert im.size==(src.width*8,src.height*8) and im.getchannel('A').getextrema()==(255,255)
    for key in ['native','input','parent','paint_mask','protected_mask','blend_weight']:
        if key in row:assert sha(Path(row[key]).read_bytes())==row[key+'_sha256']
    for model in row.get('model_sources',[]) + ([row['model']] if 'model' in row else []):
        k=(model['path'],model['sha256'].lower())
        if k not in verified_models:assert sha(Path(k[0]).read_bytes())==k[1];verified_models.add(k)
    orig=np.asarray(src.resize(im.size,Image.Resampling.NEAREST));a=np.asarray(im)
    for key in ['paint_mask','protected_mask']:
        if key in row:
            mask=np.asarray(Image.open(row[key]).resize(im.size,Image.Resampling.NEAREST))>0;assert np.array_equal(a[mask],orig[mask])
            if key=='protected_mask':assert np.array_equal(a[~mask],np.asarray(Image.open(row['parent']).convert('RGBA'))[~mask])
    if 'blend_weight' in row:
        yy,xx=np.mgrid[:im.height,:im.width];rad=np.sqrt(((xx+.5)/8-32)**2+((yy+.5)/8-32)**2);assert np.array_equal(a[rad>=4.75],np.asarray(Image.open(row['parent']).convert('RGBA'))[rad>=4.75])
    checked.append({'id':row.get('id',gid+'-dn'+str(row['denoise_strength']) if 'denoise_strength' in row else gid),'group_id':gid,'output':str(p),'sha256':row['output_sha256'],'size':list(im.size),'protected_pixels_verified':any(k in row for k in ['paint_mask','protected_mask']),'runtime_verified':False})
def decide(row,report,status,reason,evidence):
    row['visual_review']={'reviewer':'Codex internal','status':status,'reason':reason,'evidence':evidence}
    if status=='selected_for_game_review':
        gid=row['group_id'];selected[gid]={'source_report':'qa/'+report+'.json','source_rgba_sha256':groups[gid]['rgba_sha256'],'output':row['output'],'output_sha256':row['output_sha256'],'reason':reason,'status':'static_candidate_for_consumer_and_game_review','runtime_verified':False,'release_eligible':False}
half={'BM070','BM071','BM077','BM086','BM092','BM097','BM105','BM119','BM122'}
holds={'BM076':'Flat blue/white frame corner became rounded; source-protected rework required.','BM082':'Hub became an overly regular rhombus and blade-tip interpretation differs from the low-resolution source. Source-center interpolation is softer but does not resolve the whole fan.','BM083':'Yellow straight striped panel became black curved hooks.','BM090':'Road paint became brighter/raised.','BM114':'Dark surface gains grid/crack structures; sigma0.7 reduces them but loses surrounding detail. Material/consumer interpretation remains unresolved.','BM124':'Source review missed lettering on two signs. Enlarged neural output revealed the issue; exact wording is not established and must not be invented.'}
for row in reports['local_sr_stage02_materials_v1']['files']:
    verify(row);gid=row['group_id'];reason=holds.get(gid)
    if reason:status='rework_required'
    else:
        status='selected_for_game_review' if row['denoise_strength']==(.5 if gid in half else 0.) else 'not_selected'
        reason='Middle denoise reduces excess grain while retaining the visible structure.' if gid in half else 'Weak denoise retains material texture and major structure in static comparison.'
    decide(row,'local_sr_stage02_materials_v1',status,reason,reports['local_sr_stage02_materials_v1']['comparison_sheets'])
for row in reports['local_sr_stage02_rework_v2']['files']:
    verify(row);gid=row['group_id']
    if 'paint_mask' in row:
        pick=gid not in ['BM030','BM089'];status='selected_for_game_review' if pick else 'superseded'
        reason='Original paint RGB and pixel-cell shape kept exactly; asphalt received actual local neural inference. Lettering/paint itself still needs any desired high-resolution redraw and game-scale review.' if pick else 'Neural asphalt introduced pronounced cracks; later source prefilter retry is selected.'
    elif 'protected_mask' in row:status='selected_for_game_review';reason='Straight source panel restored exactly; all remaining pixels equal the recorded neural parent. Protected geometry is source enlargement, not a new high-resolution reconstruction.'
    else:status='rework_required';reason=holds[gid]
    decide(row,'local_sr_stage02_rework_v2',status,reason,reports['local_sr_stage02_rework_v2']['comparison_sheets'])
for row in reports['local_sr_stage02_refine_v3']['files']:
    verify(row);gid=row['group_id']
    pick=(gid=='BM030' and row.get('model_id')=='wdn') or (gid=='BM089' and row.get('model_id')=='photo')
    reason='Source prefilter removes hallucinated large cracks; remaining asphalt texture and exact source paint reviewed side by side. Source paint remains pixel-cell enlarged, not newly redrawn.' if pick else holds['BM082'] if gid=='BM082' else 'Alternate retry is either excessively smooth or retains stripe-like artifacts; other condition selected.'
    decide(row,'local_sr_stage02_refine_v3','selected_for_game_review' if pick else 'rework_required' if gid=='BM082' else 'not_selected',reason,reports['local_sr_stage02_refine_v3']['comparison_sheets'])
assert len(processed)==49 and len(selected)==46 and len(checked)==105
for gid in processed:groups[gid]['local_sr_attempted']=True
for gid,candidate in selected.items():groups[gid]['candidate']=candidate
for gid in ['BM082','BM114','BM124']:
    assert not before.get(gid);groups[gid]['candidate']=None;groups[gid]['review_hold_reason']=holds[gid]
groups['BM124']['classification']='protected lettering on background signs; source wording unresolved';groups['BM124']['classification_review']='Codex internal; corrected after enlarged output inspection in LOCAL-SR-005'
for gid in ['BM006','BM030','BM089','BM090','BM091','BM126','BM127']:groups[gid]['classification']='paint-aware neural background with exact source geometry protection'
for gid,old in before.items():
    if gid not in processed:assert groups[gid]['candidate']==old
summary=cat['processing_summary'];pcount=sum(bool(g.get('local_sr_attempted')) for g in groups.values());ccount=sum(bool(g.get('candidate')) for g in groups.values())
summary.update({'battle_groups_locally_processed':pcount,'battle_static_candidates':ccount,'battle_processed_without_accepted_candidate':pcount-ccount,'battle_groups_not_yet_processed':len(groups)-pcount,'all_unique_originals_locally_processed':pcount+summary['title_originals_locally_processed'],'latest_rework':review_path,'new_unique_originals_latest_rework':len(processed-old_processed),'checked_output_records_latest_rework':len(checked),'new_unique_originals_LOCAL_SR_005':49,'neural_passes_LOCAL_SR_005':102,'all_game_complete':False,'runtime_verified':False})
assert pcount==102 and ccount==96 and len(processed-old_processed)==49
report={'schema':'brs-stage02-review/v3','batch':'LOCAL-SR-005','reviewer':'Codex internal','prior_processed_groups':sorted(old_processed),'processed_groups':sorted(processed),'selected':selected,'checked_outputs':checked,'processing_summary':summary,'remaining_processed_holds':[gid for gid,g in groups.items() if g.get('local_sr_attempted') and not g.get('candidate')],'new_neural_passes':102,'new_unique_originals':49,'limitations':['Static comparison only; no runtime, UV, tile-wrap or moving material acceptance.','Seven paint surfaces and two geometric regions retain explicitly source-enlarged pixels; do not claim all areas were AI upscaled or fully redrawn.','BM082/114/124 remain open, as do prior BM019/036/056.','No new exact observed key among this batch; review pack remains title+BM023 (2 keys).','No user installation or release ZIP.']}
for name,obj in reports.items():write('qa/'+name+'.json',obj)
write(review_path,report);write('qa/battle_sr_catalog.json',cat)

# Future work prioritizes already-observed source keys to improve installable coverage.
bindings=read('qa/battle_map_runtime_links.json')['bindings'];byhash={g['rgba_sha256']:gid for gid,g in groups.items()};mapped=sorted({byhash[b['source_rgba_sha256']] for b in bindings})
unprocessed=[gid for gid in mapped if not groups[gid].get('local_sr_attempted')]
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',19)
for start in range(0,len(unprocessed),6):
    page=Image.new('RGB',(1536,1040),'#293440');d=ImageDraw.Draw(page)
    for i,gid in enumerate(unprocessed[start:start+6]):
        g=groups[gid];im=Image.open(g['representative']['png']).convert('RGBA');scale=min(480/im.width,440/im.height,8);wh=(round(im.width*scale),round(im.height*scale));im=im.resize(wh,Image.Resampling.NEAREST);bg=Image.new('RGB',wh,'#72808b');bg.paste(im,(0,0),im);x=(i%3)*512+10;y=(i//3)*520+10;d.text((x,y),f'{gid} {g["width"]}x{g["height"]} alpha{g["representative"]["alpha_min"]}',font=font,fill='white');page.paste(bg,(x,y+35))
    page.save(R/f'qa/battle-source-catalog/observed-pending-{start//6+1:02d}.png')
write('qa/local_sr_observed_pending.json',{'groups':unprocessed,'count':len(unprocessed),'reason':'Full observed RGBA/key proof exists; replacement and runtime still pending.'})

sheet=Image.new('RGB',(1060,1270),'#293440');d=ImageDraw.Draw(sheet)
for j,t in enumerate(['원본 단순 확대','로컬 AI 처리 · 게임 검수 전']):d.text((j*530+14,8),t,font=font,fill='white')
for i,gid in enumerate(['BM070','BM078','BM098','BM119']):
    src=Image.open(groups[gid]['representative']['png']);out=Image.open(groups[gid]['candidate']['output']);wh=(round(src.width*min(480/src.width,250/src.height,8)),round(src.height*min(480/src.width,250/src.height,8)))
    for j,im in enumerate([src,out]):x=j*530+14;y=48+i*300;d.text((x,y),gid,font=font,fill='white');sheet.paste(im.convert('RGB').resize(wh,Image.Resampling.NEAREST if j==0 else Image.Resampling.LANCZOS),(x,y+30))
sheet.save(C/'outputs/로컬_업스케일_2지역_검수.png');shutil.copyfile(C/'outputs/로컬_업스케일_2지역_검수.png',R/'outputs/local_sr_stage02_selected.png')
shutil.copyfile(R/'outputs/local_sr005_geometry.png',C/'outputs/로컬_업스케일_직선_재작업.png')
shutil.copyfile(R/'outputs/local_sr005_refine_BM030.png',C/'outputs/로컬_업스케일_STOP_재작업.png')
note=C/'outputs/로컬_업스케일_진행.md'
note.write_text(f'''# 로컬 업스케일 진행 — LOCAL-SR-005

- 실제 로컬 GPU 추론을 거친 고유 원본: **{pcount+1}종**(타이틀1 + 전투재질{pcount}). 이번 배치49종 추가, 처리 조건과 재작업을 원본 수에 중복 합산하지 않았습니다.
- 전투재질 **{ccount}종은 정적 검수 후보**입니다. 처리 후 보류6종, 전투맵283종 중 미처리181종입니다. 이 분모는 게임 전체 자산 수가 아닙니다.
- 2지역 불투명43종을 두 로컬 조건으로 처리한86개 결과와 추가 재작업19개를 직접 비교했습니다. 총 실제 추론102회이며 나머지3개는 기존 추론 결과의 부분 보정입니다.
- 도로 바탕은 실제 AI 처리입니다. STOP·BUS·화살표·페인트7종과 직선 보호2영역은 원본의 픽셀 형태를 보존했습니다. 그 보호 부분까지 새 고해상도 그림으로 완성했다는 뜻은 아닙니다.
- 환풍기, 어두운 표면, 글자 포함 배경은 재시도 뒤에도 보류했습니다. 이전 작은 표식·창문 관련3종도 남아 있습니다.
- 실제 관측 원본과 매칭되는 추가21종을 다음 처리 대상으로 확인했습니다. 이번 배치에는 새 관측키가 없어 기존 별도 시험팩은2키 그대로입니다.
- 실제 게임 화면 검수, 한글 폰트·조준 고정, 나머지 지역/적/이펙트/컷신 및 최종 설치 ZIP은 미완료입니다. 최근 Windows 화면 접근 오류는 해결 확인 전입니다.
''','utf8')
progress=R/'PROGRESS.md';text=progress.read_text('utf8');marker='## 2026-09-23 — LOCAL-SR-005: 2지역 재질 / 원본 표식 보호 재작업'
if marker not in text:
    text+='\n\n'+marker+f'''

- 직전 사용자 질문 응답은 Fate 로컬 모델 파일과121개 실제 실행기록의 해시 확인 정정으로, 제작 진척은 없었다. 이어진 이번 목표 턴은 미통합86출력의 검수 반영,16추가 neural pass,3후처리 및 카탈로그 갱신으로 progress. 전체 목표 active.
- 1지역 잔여8종 및2지역70종 원본 시트 직접 확인. 2지역 불투명43고유 원본에 WDN/DNI0.5 총86추론 결과,11비교 페이지 검수. BM070/071/077/086/092/097/105/119/122는0.5, 나머지 일반 후보는WDN. 초기6보류 중076/083/090은 부분 재작업으로 정적 후보,082/114/124는 여전히보류.
- BM006/030/089/090/091/126/127: 원본 팔레트에서 페인트 마스크, 이웃 배경으로 cleanplate, 실제WDN 추론. 페인트RGB/모양은nearest8x와 정확일치. BM090 도로범위x37..187, 바깥 포장석을 페인트로 오인하지 않음. 글자/화살표 자체HD새그림 완료 주장 금지.
- BM030/089의 최초 바탕에는 원본에 없는 굵은 균열/띠가 나타나 재추론4조건.030은WDN+sigma0.65,089는photo+sigma0.4 선택. 각 표식은 그대로 보호. BM076은 청백색 프레임 마스크+1cell 경계,083은[51,8,64,16]영역 원본복원. 주변은부모neural결과와 동일. 새neuralpass로 세지 않음.
- BM082 WDN 사전필터/photo/anime6B 세 조건도 중심의마름모화/날개끝 해석 차이를 해소하지 못함. 원본중심(32,32)radius4/.75feather Lanczos보정은 부드럽지만 전체형상 근거 부족으로 미채택. BM114sigma0.4/.7도 질감 왜곡 또는 과도한 부드러움으로 보류. BM124는 원본검토에서 못본 간판문자를 확대결과에서 발견해 분류정정, 문구추정 채택 없음.
- 검증: 원본전체RGBA, 실제모델SHA,105출력/native/input/parent/maskSHA,8배크기,불투명255,페인트/보호영역 동일성과부모밖범위 검사. qa/local_sr_stage02_review_v3.json. 시각검수와기계검사를 구분.
- 실제고유원본54→103(타이틀1+전투102),전투정적후보50→96,보류6(BM019/036/056/082/114/124),미처리181/283. 기존50후보 보존. 이번실제추론102pass(86+12+4),후처리3,신규원본49. 사용자설치/최종ZIP/게임검증 없음.
- 새후보와battle_map_runtime_links대조: 이번49그룹에는추가관측키없음, title+BM023기존2키팩유지. 대신원본관측RGBA/키가확보된미처리21종(BM130/131/134/148..등)을 qa/local_sr_observed_pending.json과원본4페이지로 다음우선순위 지정. 지도전체UV·재질소비는여전히미확인.
- Windows화면접근확인질문은미응답. 이번턴Get-CimInstance도접근거부,일반Get-Process에python/PPSSPP없음; 검수창재실행/사용자입력/보안우회 없음. 로컬추론39353은정상종료,추가refine도exit0. 새로운외부이미지전송없음.
- Coutputs: 로컬_업스케일_2지역_검수.png,로컬_업스케일_직선_재작업.png,로컬_업스케일_STOP_재작업.png,로컬_업스케일_진행.md. GUI불가이므로Codex미리보기 사용.
- 다음: 관측키21종원본검수→로컬추론→선정품정확키시험팩확장; 남은1/2지역문자·알파·보류6재작업;3~6지역/FLD/적/이펙트/컷신과6특수높이PTMD조사. 화면접근가능해지면명시ISO CLI로실제title/Orbit/LOCK ON 및지역소비검증. 전체목표 active.
'''
    progress.write_text(text,'utf8')
print(json.dumps({'summary':summary,'holds':report['remaining_processed_holds'],'observed_pending':unprocessed,'checked_outputs':len(checked)},ensure_ascii=False))
