"""Codex visual decisions, source/output proof, and a bounded exact-key QA pack."""
import sys,json,hashlib,shutil
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np
sys.stdout.reconfigure(encoding='utf8')
R=Path(r'P:\AI\Codex\projects\black-rock-shooter-hd-ui-fonts')
C=Path(r'C:\Users\CadriacLord\Documents\Codex\2026-09-22\brs-hd-ui-fonts')
if (R/'qa/local_sr_soft_review_v4.json').exists():
    raise SystemExit('Historical LOCAL-SR-003 builder: newer soft-review v4 decisions exist. Preserve the current catalog; do not overwrite it with this earlier batch.')
def read(n):return json.loads((R/n).read_text('utf8'))
def write(n,v):(R/n).write_text(json.dumps(v,ensure_ascii=False,indent=2),'utf8')
def sha(b):return hashlib.sha256(b).hexdigest()
cat=read('qa/battle_sr_catalog.json');groups={g['group_id']:g for g in cat['groups']}
bydigest={g['rgba_sha256']:g['group_id'] for g in cat['groups']}
opaque=read('qa/local_sr_stage01_materials_v1.json');road=read('qa/local_sr_road_paint_rework_v2.json')
alpha=read('qa/local_sr_stage01_alpha_v1.json');rework=read('qa/local_sr_stage01_alpha_rework_v2.json')
selected={};processed=set();verified=[]
def check(row):
    src=Image.open(row['source']).convert('RGBA');assert sha(src.tobytes())==row['source_rgba_sha256']
    p=Path(row['output']);assert sha(p.read_bytes())==row['output_sha256']
    im=Image.open(p).convert('RGBA');assert im.size==(src.width*8,src.height*8)
    for a,h in [('native','native_sha256'),('alpha_native','alpha_native_sha256'),('rgb_native','rgb_native_sha256')]:
        if a in row:assert sha(Path(row[a]).read_bytes())==row[h]
    if src.getchannel('A').getextrema()==(255,255):assert im.getchannel('A').getextrema()==(255,255)
    else:
        lin=np.asarray(src.getchannel('A').resize(im.size,Image.Resampling.BILINEAR));av=np.asarray(im.getchannel('A'))
        assert not np.any(av[lin==0])
    verified.append({'group_id':row['group_id'],'file':str(p),'sha256':row['output_sha256']})
    return src,im
def choose(gid,row,report,reason):
    selected[gid]={'source_report':report,'source_rgba_sha256':groups[gid]['rgba_sha256'],
        'output':row['output'],'output_sha256':row['output_sha256'],'reason':reason,
        'status':'static_candidate_for_consumer_and_game_review','runtime_verified':False,'release_eligible':False}
half={23,31,32,34,35,38,40,43,44,54}
holds={'BM036':'White markings may contain tiny text/signs. Separate protected-region review required.',
       'BM056':'32px window partitions need cross-check against related source material before accepting inferred divisions.'}
for row in opaque['files']:
    check(row);gid=row['group_id'];processed.add(gid);num=int(gid[2:]);dn=row['denoise_strength']
    if gid in holds:
        status='held';reason=holds[gid]
        if gid=='BM036':row['classification']='ambiguous white markings; protected-region review required'
    elif gid in ['BM004','BM005','BM028']:status='superseded';reason='Road paint gained raised bright rims; replaced by paint-aware rework.'
    else:
        pick=.5 if num in half else 0.;status='selected_for_game_review' if dn==pick else 'not_selected'
        reason='Middle denoise reduces excess grain in smooth/rough material while retaining major shapes.' if pick else 'Weak denoise retains original material grain and architectural divisions better.'
        if status=='selected_for_game_review':choose(gid,row,'qa/local_sr_stage01_materials_v1.json',reason)
    row['visual_review']={'reviewer':'Codex internal','status':status,'reason':reason,'evidence':'outputs/stage01-material-review/review-01..10.png'}
for row in road['files']:
    src,im=check(row);gid=row['group_id'];processed.add(gid)
    m=Image.open(row['paint_mask']).resize(im.size,Image.Resampling.NEAREST)
    mask=np.asarray(m)>0;expected=np.asarray(src.resize(im.size,Image.Resampling.NEAREST))
    assert np.array_equal(np.asarray(im)[mask],expected[mask])
    reason='Raised highlight removed; flat source paint width, location and RGB restored exactly. Neural asphalt remains.'
    row['visual_review']={'reviewer':'Codex internal','status':'selected_for_game_review','reason':reason,'evidence':road['comparison']}
    choose(gid,row,'qa/local_sr_road_paint_rework_v2.json',reason)
for row in alpha['files']:
    check(row);gid=row['group_id'];processed.add(gid)
    if gid in ['BM001','BM026','BM045']:
        status='selected_for_game_review' if row['alpha_model_id']=='general-wdn' else 'not_selected'
        reason='Source cutout and solid parts retained; visible contour improved in static matte comparison.'
        if status=='selected_for_game_review':choose(gid,row,'qa/local_sr_stage01_alpha_v1.json',reason)
    else:
        status='rejected_rework_required'
        reason={'BM007':'Faint branches disappear.','BM055':'Faint branches disappear.','BM058':'Faint branches disappear.',
                'BM027':'Soft cloud becomes faceted; source softness is not retained.',
                'BM039':'Diagonal edge becomes wavy; reconstruct linear marking geometry.',
                'BM057':'Foliage becomes excessively glossy and fibrous.'}[gid]
    row['visual_review']={'reviewer':'Codex internal','status':status,'reason':reason,'evidence':'outputs/local_sr_alpha_trial_01..03.png'}
for row in rework['files']:
    check(row);gid=row['group_id'];processed.add(gid)
    if 'neural_weight' in row:
        pick=row['neural_weight']==.35
        status='selected_for_game_review' if pick else ('not_advanced_by_faint_line_check' if row['neural_weight']==.5 else 'not_selected')
        reason='35% neural alpha with positive source coverage restores weak branches and source mean opacity; residual threshold losses are recorded, not declared zero.'
        if pick:choose(gid,row,'qa/local_sr_stage01_alpha_rework_v2.json',reason)
        evidence='outputs/local_sr_alpha_rework_cracks.png; 0.5 weight screened by retention metrics, not depicted in this sheet'
    else:
        status='rejected_rework_required';reason='Changing RGB model alone did not correct cloud facets or glossy foliage; further alpha/RGB joint reconstruction required.'
        evidence='outputs/local_sr_alpha_rework_soft.png'
    row['visual_review']={'reviewer':'Codex internal','status':status,'reason':reason,'evidence':evidence}

# Bring earlier reviewed candidates into one ledger without counting repeated model runs as new originals.
old=read('qa/local_sr_battle_material_trial.json')
for row in old['files']:
    gid=bydigest[row['source_rgba_sha256']];processed.add(gid)
    if gid in ['BM009','BM010'] and row['model']=='general-wdn':
        row['group_id']=gid;check(row);choose(gid,row,'qa/local_sr_battle_material_trial.json','Earlier WDN static review candidate; runtime pending.')
early=read('qa/local_sr_battle_material_rework_v2.json')
for row in early['files']:
    gid=bydigest[row['source_rgba_sha256']]
    if row['denoise_strength']==.5:
        row['group_id']=gid;check(row);choose(gid,row,'qa/local_sr_battle_material_rework_v2.json','Earlier midpoint denoise/color rework candidate; runtime pending.')
for gid in ['BM036','BM019']:
    groups[gid]['classification']='ambiguous markings; protected-region review required'
    groups[gid]['classification_review']='Codex internal; corrected after enlarged SR comparison'

for gid,g in groups.items():
    g['local_sr_attempted']=gid in processed
    g['candidate']=selected.get(gid)
    g['runtime_verified']=g['release_eligible']=False
summary={'battle_groups_total':len(groups),'battle_groups_locally_processed':len(processed),
         'battle_static_candidates':len(selected),'battle_processed_without_accepted_candidate':len(processed-set(selected)),
         'battle_groups_not_yet_processed':len(groups)-len(processed),
         'title_originals_locally_processed':1,'all_unique_originals_locally_processed':len(processed)+1,
         'new_unique_originals_this_batch':47,'checked_output_records':len(verified),
         'source_table_entries':416,'source_decoded_entries':410,'source_format_unresolved':6,
         'all_game_complete':False,'runtime_verified':False}
cat['processing_summary']=summary
write('qa/battle_sr_catalog.json',cat)
for name,obj in [('local_sr_stage01_materials_v1',opaque),('local_sr_road_paint_rework_v2',road),('local_sr_stage01_alpha_v1',alpha),('local_sr_stage01_alpha_rework_v2',rework)]:
    write('qa/'+name+'.json',obj)
write('qa/local_sr_stage01_verification.json',{'summary':summary,'checked_records':verified,'selected':selected,'limitations':['Static review only.','Equal source pixels do not establish scene/UV consumer.','No user installation or final ZIP.']})

# Only full-RGBA observed keys may enter the isolated review pack.
pack=R/'workspace/local-sr/stage01-review-pack/PSP/TEXTURES/NPUH10126';(pack/'materials').mkdir(parents=True,exist_ok=True)
bindings={};proof=[]
for b in read('qa/battle_map_runtime_links.json')['bindings']:
    gid=bydigest[b['source_rgba_sha256']]
    if gid not in selected:continue
    assert b['logical_full_image_match'] and b['size']==[groups[gid]['width'],groups[gid]['height']]
    for m in b['matches']:
        found=False
        for path in m['paths']:
            p=Path(path)
            if not p.exists():continue
            observed=Image.open(p).convert('RGBA')
            assert observed.size==tuple(b['size']) and sha(observed.tobytes())==b['source_rgba_sha256']
            found=True;break
        assert found
        key=m['key'];value=f'materials/{gid}.png'
        assert key not in bindings or bindings[key]==value
        bindings[key]=value;shutil.copyfile(selected[gid]['output'],pack/value)
        assert sha((pack/value).read_bytes())==selected[gid]['output_sha256']
        proof.append({'key':key,'group_id':gid,'source_path':path,'rgba_sha256':b['source_rgba_sha256'],'replacement_sha256':selected[gid]['output_sha256']})
title=R/'workspace/local-sr/title-review-pack/PSP/TEXTURES/NPUH10126/title/title-metal-local-sr.png'
assert sha(title.read_bytes())=='9bfc5e1abb745a408ca66c8f15ee6a809564e3ebb2f1099e508b2672896916d8'
(pack/'title').mkdir(exist_ok=True);shutil.copyfile(title,pack/'title/title-metal-local-sr.png')
bindings['0000000086ba34d7c28b381c']='title/title-metal-local-sr.png'
ini='[options]\nversion = 1\nhash = xxh64\nignoreAddress = true\nreduceHash = false\n\n[hashes]\n'+''.join(f'{k} = {v}\n' for k,v in sorted(bindings.items()))
(pack/'textures.ini').write_text(ini,'utf8')
write('qa/local_sr_stage01_review_pack.json',{'path':str(pack),'keys':bindings,'battle_binding_evidence':proof,'runtime_verified':False,'installed':False,'release_eligible':False})

# A compact user-facing comparison of selected architecture at unchanged aspect ratios.
font=ImageFont.truetype(r'C:\Windows\Fonts\malgun.ttf',22)
sheet=Image.new('RGB',(1060,1450),'#293440');d=ImageDraw.Draw(sheet)
d.text((14,8),'원본 단순 확대',font=font,fill='white');d.text((544,8),'로컬 AI 처리 · 검수 후보',font=font,fill='white')
for i,gid in enumerate(['BM012','BM013','BM047','BM052']):
    src=Image.open(groups[gid]['representative']['png']).convert('RGB');out=Image.open(selected[gid]['output']).convert('RGB')
    size=(304,304);y=54+i*345
    for col,im in enumerate([src,out]):
        x=col*530+14;d.text((x,y),f'{gid} · {src.width}×{src.height} → {out.width}×{out.height}',font=font,fill='white')
        sheet.paste(im.resize(size,Image.Resampling.NEAREST if col==0 else Image.Resampling.LANCZOS),(x,y+34))
dst=C/'outputs/로컬_업스케일_1지역_건물_검수.png';sheet.save(dst)
for a,b in [('local_sr_road_paint_rework.png','로컬_업스케일_도로_재작업.png'),('local_sr_alpha_rework_cracks.png','로컬_업스케일_균열_재작업.png')]:
    shutil.copyfile(R/'outputs'/a,C/'outputs'/b)
    assert sha((R/'outputs'/a).read_bytes())==sha((C/'outputs'/b).read_bytes())
note=f'''# 로컬 업스케일 진행

- 실제 로컬 GPU로 처리한 고유 원본: **{summary['all_unique_originals_locally_processed']}종**(타이틀1 + 전투재질{len(processed)}). 이번 배치에서47종 추가.
- 원본의 AI4배 처리 후8배 출력 크기로 맞췄습니다. 재처리 조건과 중복 파일을 고유 원본 수에 더하지 않았습니다.
- 전투재질{len(selected)}종은 정적 검수 후보입니다. 실제 게임의 반복 경계·배치·축소 표시 검증은 남았습니다.
- 도로: 밝게 부풀었던 선을 원래 색·두께·위치로 복원하고 아스팔트는 로컬 모델로 재처리했습니다.
- 균열: 사라진 약한 선을 줄이고 원본의 전체 불투명도를 보존하는 보정을 적용했습니다. 후보이며 모든 선의 게임 표시가 검증된 것은 아닙니다.
- 구름·나무·대각선 표시는 미채택으로 남겨 재작업합니다. 작은 표식과 저해상도 창문 구획도 확인이 필요합니다.
- 전투맵 전체 추출은416항목 중410항목, 픽셀 중복을 제외하면283종입니다. 이 수치는 게임 전체 자산 총수가 아닙니다.
- 별도 시험팩은 관측 원본과 완전히 일치하는{len(bindings)}개 키만 포함합니다. 사용자 게임에 설치하지 않았습니다.
- 전체 지역, 적·오브젝트·이펙트, 한글 폰트·조준 고정의 실제 표시 검증 및 최종 설치 ZIP은 미완료입니다.
'''
(C/'outputs/로컬_업스케일_진행.md').write_text(note,'utf8')
marker='## 2026-09-23 — LOCAL-SR-003: 1지역 재질47종 추가 처리와 재작업'
progress=R/'PROGRESS.md';text=progress.read_text('utf8')
if marker not in text:
    text+='\n\n'+marker+f'''

- 이전 목표 턴은 progress: LOCAL-SR-002의 검수 판정·출력·별도ISO 실행 관측·종료 증거가 추가되어 다음 행동이 바뀌었다. 진행 불가 상태가 아님.
- 전투 원본410항목을 크기+RGBA SHA256으로283그룹(BM001..BM283)에 묶음. 1지역 고유58그룹의 원본 확대4페이지 직접 검토/분류. qa/battle_sr_catalog.json. 그룹은 동일 소비자/해시라는 뜻이 아님.
- 신규 불투명38그룹에 WDN/DNI0.5 실제 로컬 추론76후보, 비교10페이지 직접 검수. tools/batch_stage01_sr.py. BM036 작은 흰 표식은 문자 가능성을 발견해 보류로 정정, BM056 창 구획은 관련원본 대조 보류.
- BM003/004/005/028 도로의 밝은 입체 테두리를 발견. 원본 페인트 팔레트 마스크를 분리해 이웃 원본 RGB로 바탕을 준비하고 배경만 로컬 WDN으로 재추론. 선의 색·두께·위치는 원본8배와 RGBA 동일. 4재작업 후보 직접 확인. qa/local_sr_road_paint_rework_v2.json.
- 투명9그룹 실제 RGB/알파 추론18후보. 단색 균열3그룹은 RGB를 무의미하게 모델에 넣지 않고 색을 유지하며 알파를 추론. Bilinear-source 밖 완전투명/내부 완전불투명 보호. 모델만 쓴 균열은 약한 선 소실, 구름은 각진 덩어리, 나무는 과한 광택으로 미채택.
- 균열3그룹:35/50/65% neural alpha 혼합·원본 평균알파 복원9후처리. 새 GPU추론으로 세지 않음.35%가 약한 선을 더 유지하여 게임 검수 후보. source alpha>=16→축소alpha<8 잔여는BM007=3/BM055=1/BM058=0이며 완전보존 주장 금지. qa/local_sr_stage01_alpha_rework_v2.json.
- 구름/나무는 anime6B/photo 추가 RGB4조건 실제 로컬 재추론도 미채택. RGB모델 변경만으로는 해결되지 않음. 다음은 cloud 알파·RGB 공동 필터링/부드러운 밀도 보존, tree의 잎·줄기 영역별 질감 강도 재작업. BM039 대각선은 선형 기하를 재구성해야 함. GPT 협력 허용은 유지, 이번 배치 이미지 업로드 없음.
- 누계 실제 로컬 고유 원본{summary['all_unique_originals_locally_processed']}종(타이틀1+전투{len(processed)}), 이번 신규47종. 전투 정적후보{len(selected)}, 처리했으나 채택보류{summary['battle_processed_without_accepted_candidate']}, 전투그룹 미처리{summary['battle_groups_not_yet_processed']}. 전체게임 완료/전체4K 승인 아님.
- 출력{len(verified)}레코드의 원본RGBA·PNG해시·8배크기·보호알파/페인트 검사. qa/local_sr_stage01_verification.json은 이미지 직접검수 판정과 분리한다.
- stage01-review-pack은 관측 전체RGBA를 현파일로 재대조한 정확키와 기존 타이틀키, 총{len(bindings)}키만 포함. qa/local_sr_stage01_review_pack.json. 미설치/런타임 미검증. 매핑 없는 후보를 와일드카드로 넣지 않음.
- C outputs: 로컬_업스케일_1지역_건물_검수.png, 로컬_업스케일_도로_재작업.png, 로컬_업스케일_균열_재작업.png, 로컬_업스케일_진행.md. Windows입력/에뮬실행 없음.
- 다음: 위 미달6그룹 및 미처리 문자/표식5그룹 계속재작업; 관측과 소비UV 확보 및 실제게임 비교; 2~6지역/EX·진엔딩, FLD·적·이펙트·컷신 범위 확장. PTMD flag5의6항목, Orbit v4/LOCK ON 소비, 최종 설치·제거ZIP 미완료. 전체 목표 active.
'''
    progress.write_text(text,'utf8')
print(json.dumps({'summary':summary,'qa_pack_keys':len(bindings),'candidate_ids':sorted(selected)},ensure_ascii=False))
