"""Verify observed-key candidates and assemble an isolated, uninstalled QA pack."""
import sys,json,hashlib,shutil
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
sys.stdout.reconfigure(encoding='utf8')
R=Path(__file__).resolve().parents[1];C=Path('C:/Users/CadriacLord/Documents/Codex/2026-09-22/brs-hd-ui-fonts')
def sha(b):return hashlib.sha256(b).hexdigest()
def read(n):return json.loads((R/n).read_text('utf8'))
def write(n,x):(R/n).write_text(json.dumps(x,ensure_ascii=False,indent=2),'utf8')
q=read('qa/local_sr_observed_v1.json');cat=read('qa/battle_sr_catalog.json');groups={g['group_id']:g for g in cat['groups']};prior={gid:json.loads(json.dumps(g.get('candidate'))) for gid,g in groups.items() if g.get('candidate')}
choices={'BM131':'wdn','BM134':'wdn','BM148':'photo','BM149':'photo','BM150':'wdn','BM151':'wdn','BM152':'wdn','BM157':'wdn','BM158':'wdn','BM160':'wdn','BM161':'wdn','BM166':'photo','BM167':'photo','BM168':'wdn'}
holds={'BM130':'Both models invent strongly segmented/zigzag cliff grooves; source macro structure needs a better controlled retry.','BM156':'Foliage has glossy hard patches and branches acquire planar edges; separate foliage/trunk detail strength before selection.','BM159':'Yellow mottled layer becomes too vivid and highly detailed; preserve local color/coverage before choosing a candidate.','BM162':'Foliage acquires bright rock-like highlights; reduce invented contrast.','BM163':'Leaf strips become glossy knotted tubes; local prefilter/material treatment needs revision.','BM164':'Scattered leaves become glossy blob shapes; source color and leaf silhouette need closer reconstruction.','BM165':'Gray leaf variant shows the same glossy blobby detail problem as BM164.'}
checked=[];selected={};verified_models=set()
for row in q['files']:
    gid=row['group_id'];src=Image.open(row['source']).convert('RGBA');g=groups[gid];assert sha(src.tobytes())==row['source_rgba_sha256']==g['rgba_sha256'];assert src.size==(g['width'],g['height'])
    out=Path(row['output']);assert sha(out.read_bytes())==row['output_sha256'];im=Image.open(out).convert('RGBA');assert im.size==(src.width*8,src.height*8)
    m=row['model'];mk=(m['path'],m['sha256'])
    if mk not in verified_models:assert sha(Path(mk[0]).read_bytes())==mk[1];verified_models.add(mk)
    for part in row['parts']:
        for key in ['input_rgb','input_alpha','rgb_native','alpha_native']:
            if key in part:assert sha(Path(part[key]).read_bytes())==part[key+'_sha256']
    actual=np.asarray(im);lin=np.asarray(src.getchannel('A').resize(im.size,Image.Resampling.BILINEAR));assert not np.any(actual[:,:,3][lin==0]);assert np.all(actual[:,:,3][lin==255]==255)
    aa=np.asarray(src.getchannel('A'));red=np.asarray(im.getchannel('A').resize(src.size,Image.Resampling.LANCZOS));lost=int(((aa>=16)&(red<8)).sum());assert lost==row['alpha_metrics']['source_ge16_reduced_below8']==0
    checked.append({'group_id':gid,'model_id':row['model_id'],'output':row['output'],'sha256':row['output_sha256'],'size':list(im.size),'source_and_model_sha_verified':True,'empty_and_solid_support_verified':True,'source_ge16_reduced_below8':lost})
    pick=choices.get(gid)==row['model_id'];reason=holds.get(gid,'Selected after source/model comparisons; major structure retained. Source full-RGBA/key identity is verified separately; this is not final scene/UV/tile-wrap approval.' if pick else 'Alternate condition loses more grain/detail or adds sharper highlights than the selected condition.')
    if gid in ['BM131','BM148','BM149','BM158','BM166','BM167','BM168'] and pick:reason+=' Black and light matte comparisons reviewed; native blend mode/alpha testing remains unverified.'
    row['visual_review']={'reviewer':'Codex internal','status':'selected_for_game_review' if pick else 'held_rework_required' if gid in holds else 'not_selected','reason':reason,'evidence':q['comparison_sheets']+([f'outputs/local_sr_observed_matte_{i:02d}.png' for i in range(1,4)] if gid in choices and src.getchannel('A').getextrema()!=(255,255) else [])}
    g['local_sr_attempted']=True;g['classification']='Observed-key source; opaque material' if src.getchannel('A').getextrema()==(255,255) else 'Observed-key source; RGBA material/cutout';g['classification_review']='Codex internal; observed-pending-01..04 and observed_compare_01..07'
    if pick:
        candidate={'source_report':'qa/local_sr_observed_v1.json','source_rgba_sha256':g['rgba_sha256'],'output':row['output'],'output_sha256':row['output_sha256'],'reason':reason,'status':'static_candidate_for_consumer_and_game_review','runtime_verified':False,'release_eligible':False};selected[gid]=candidate;g['candidate']=candidate
    elif gid in holds:g['candidate']=None;g['review_hold_reason']=holds[gid]
assert len(selected)==14 and len(checked)==42 and len(q['group_ids'])==21 and q['new_neural_passes']==86
for gid,candidate in prior.items():
    if gid not in q['group_ids']:assert groups[gid]['candidate']==candidate

pack=R/'workspace/local-sr/observed-review-pack-v1/PSP/TEXTURES/NPUH10126';(pack/'materials').mkdir(parents=True,exist_ok=True);(pack/'title').mkdir(exist_ok=True)
byhash={g['rgba_sha256']:gid for gid,g in groups.items()};bindings={};proof=[]
for binding in read('qa/battle_map_runtime_links.json')['bindings']:
    gid=byhash[binding['source_rgba_sha256']];candidate=groups[gid].get('candidate')
    if not candidate:continue
    assert binding['logical_full_image_match'] and binding['size']==[groups[gid]['width'],groups[gid]['height']]
    for match in binding['matches']:
        observed_path=next((Path(p) for p in match['paths'] if Path(p).is_file()),None);assert observed_path is not None
        observed=Image.open(observed_path).convert('RGBA');assert observed.size==tuple(binding['size']) and sha(observed.tobytes())==binding['source_rgba_sha256']
        key=match['key'];value=f'materials/{gid}.png';assert len(key)==24 and key.startswith('00000000');assert key not in bindings or bindings[key]==value
        bindings[key]=value;shutil.copyfile(candidate['output'],pack/value);assert sha((pack/value).read_bytes())==candidate['output_sha256']
        proof.append({'key':key,'group_id':gid,'asset_id':binding['asset_id'],'observed_source_png':str(observed_path),'observed_source_png_sha256':sha(observed_path.read_bytes()),'observed_rgba_sha256':binding['source_rgba_sha256'],'output_sha256':candidate['output_sha256'],'consumer_scene_uv':'unverified','replacement_runtime_verified':False})
oldpack=read('qa/local_sr_stage01_review_pack.json');titlekey='0000000086ba34d7c28b381c';title=Path(oldpack['path'])/oldpack['keys'][titlekey];assert sha(title.read_bytes())=='9bfc5e1abb745a408ca66c8f15ee6a809564e3ebb2f1099e508b2672896916d8';shutil.copyfile(title,pack/'title/title-metal-local-sr.png');bindings[titlekey]='title/title-metal-local-sr.png'
assert len(bindings)==16 and {p['group_id'] for p in proof}==set(choices)|{'BM023'}
ini='[options]\nversion = 1\nhash = xxh64\nignoreAddress = true\nreduceHash = false\n\n[hashes]\n'+''.join(f'{k} = {v}\n' for k,v in sorted(bindings.items()));(pack/'textures.ini').write_text(ini,'utf8')
# Read the final disk INI and every destination to establish what the QA copy actually contains.
actual_bindings={line.split(' = ')[0]:line.split(' = ')[1] for line in (pack/'textures.ini').read_text('utf8').splitlines() if len(line.split(' = ')[0])==24 and ' = ' in line};assert actual_bindings==bindings
expected_pngs=set(bindings.values());actual_pngs={p.relative_to(pack).as_posix() for p in pack.rglob('*.png')};assert actual_pngs==expected_pngs
pack_report={'schema':'brs-observed-review-pack/v1','path':str(pack),'keys':bindings,'battle_binding_evidence':proof,'textures_ini_sha256':sha((pack/'textures.ini').read_bytes()),'unique_battle_groups':15,'all_keys':16,'new_keys_this_batch':14,'prior_key_count':2,'installed':False,'runtime_verified':False,'release_eligible':False,'limitations':['Full observed source RGBA/key matches; replacement loading and final game rendering still unverified.','Only title plus selected mapped materials; Orbit/UI v4 are separate.','Not a final installer/release ZIP.']};write('qa/local_sr_observed_review_pack_v1.json',pack_report)
(pack/'README.txt').write_text('BRS NPUH10126 LOCAL-SR-006 isolated QA pack\n16 exact observed keys: title +15 materials.\nNo user installation performed. Static candidates only.\nReplacement loading, game UV/alpha/tile behavior, and gameplay transitions remain unverified.\nOrbit font/UI v4 are separate. This is not the final release.\n','utf8')
summary=cat['processing_summary'];pcount=sum(bool(g.get('local_sr_attempted')) for g in groups.values());ccount=sum(bool(g.get('candidate')) for g in groups.values());assert pcount==123 and ccount==110
summary.update({'battle_groups_locally_processed':pcount,'battle_static_candidates':ccount,'battle_processed_without_accepted_candidate':pcount-ccount,'battle_groups_not_yet_processed':len(groups)-pcount,'all_unique_originals_locally_processed':pcount+1,'latest_rework':'qa/local_sr_observed_review_v1.json','new_unique_originals_latest_rework':21,'checked_output_records_latest_rework':42,'new_unique_originals_LOCAL_SR_006':21,'neural_passes_LOCAL_SR_006':86,'review_pack_exact_keys':16,'all_game_complete':False,'runtime_verified':False})
report={'schema':'brs-observed-review/v1','batch':'LOCAL-SR-006','selected':selected,'checked_outputs':checked,'new_unique_originals':21,'new_neural_passes':86,'new_holds':holds,'processing_summary':summary,'qa_pack_report':'qa/local_sr_observed_review_pack_v1.json','runtime_verified':False,'release_eligible':False}
write('qa/local_sr_observed_v1.json',q);write('qa/battle_sr_catalog.json',cat);write('qa/local_sr_observed_review_v1.json',report)

font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',20);s=Image.new('RGB',(1060,1460),'#293440');d=ImageDraw.Draw(s)
for j,t in enumerate(['원본 단순 확대','로컬 AI 처리 · 게임 검수 전']):d.text((j*530+14,8),t,font=font,fill='white')
for i,gid in enumerate(['BM150','BM151','BM161','BM149']):
    src=Image.open(groups[gid]['representative']['png']).convert('RGBA');out=Image.open(selected[gid]['output']).convert('RGBA');scale=min(490/src.width,290/src.height,8);wh=(round(src.width*scale),round(src.height*scale))
    for j,im in enumerate([src,out]):
        x=j*530+14;y=48+i*350;d.text((x,y),gid,font=font,fill='white');v=im.resize(wh,Image.Resampling.NEAREST if j==0 else Image.Resampling.LANCZOS);bg=Image.new('RGB',wh,'#72808b');bg.paste(v,(0,0),v);s.paste(bg,(x,y+32))
dest=C/'outputs/로컬_업스케일_관측재질_검수.png';s.save(dest);shutil.copyfile(dest,R/'outputs/local_sr_observed_selected.png')
note=C/'outputs/로컬_업스케일_진행.md';note.write_text(f'''# 로컬 업스케일 진행 — LOCAL-SR-006

- 실제 로컬 GPU 추론을 거친 고유 원본: **124종**(타이틀1 + 전투재질123).
- 전투재질 **110종은 정적 검수 후보**입니다. 처리 후 보류13종, 전투맵283종 중 미처리160종입니다. 게임 전체 자산의 총수나 전체 완료율은 아닙니다.
- 이번 이어진 작업에서 원본21종을 추가로 두 모델로 처리했습니다.42개 출력/실제86추론을 비교하고14종을 후보로 선택했습니다. 투명 후보7종은 검정·밝은 배경에서도 원본과 대조했습니다.
- 절벽·나무·일부 잎/노란 무늬7종은 질감·색·형상이 과장돼 미채택입니다. 기존6종과 함께 계속 재작업합니다.
- 별도 시험팩을 **정확한 관측키2개→16개**로 확장했습니다. 실제 게임에서 추출했던 원본 전체RGBA와 파일을 재대조해 연결했으며, 새 교체 이미지의 실제 게임 표시 검증은 남아 있습니다.
- 시험팩 경로: {pack}
- 사용자 게임에 설치하지 않았습니다. 한글 폰트/UI v4는 별도이며 최종 배포 ZIP도 아직 없습니다.
- STOP·BUS·화살표·도로 페인트7종과 직선 보호2영역은 원본 픽셀 형태를 보존한 중간 후보입니다. 해당 부분까지 새 고해상도 그림으로 완성했다고 주장하지 않습니다.
- 남은 작업: 보류13종 재작업, 미처리 전투맵160종과 다른 지역/FLD/적/이펙트/컷신, 특수 PTMD6건, 한글 폰트·조준 고정 및 전체 경로의 실제 화면 검수, 최종 설치·제거 ZIP.
- Windows 검수창 접근 오류는 해결 확인 전입니다. 잠금 여부 확인 질문은 답변 대기 중이며 사용자 게임 입력이나 보안 설정 변경은 하지 않았습니다.
''','utf8')
marker='## 2026-09-23 — LOCAL-SR-006: 관측키21종 처리와 정확키16개 시험팩'
progress=R/'PROGRESS.md';text=progress.read_text('utf8')
if marker not in text:
    text+='\n\n'+marker+f'''

- LOCAL-SR-005 직후 동일목표턴에서 의미있는 계속작업. 원본관측키가있는미처리21종 원본4페이지를 직접검토하고 WDN/photo 두모델42후보,실제86pass. BM130은4개32px높이띠,BM149는2개128px높이영역을분리추론. premultiplied RGB/alpha사전필터와35%neural/65%sourcebilinear알파혼합,원본평균opacity및가중RGB평균복원.
- 7개비교페이지전체직접검수. 선택14: WDN BM131/134/150/151/152/157/158/160/161/168,photo BM148/149/166/167. 투명선택7종은검정/밝은matte3페이지도확인. 이는게임의blend mode/alpha test/UV/반복경계승인이아님.
- 보류7: BM130절벽의지그재그홈,156나무의광택/평면적인가지,159노란무늬의과한색/세부,162~165잎의광택/관모양/덩어리화. 기존6보류와합쳐13. 초기양조건이실패한종은원본국소색상/질감강도와잎형상재작업대상,범위제외아님.
-42출력의원본전체RGBA/모델/input/native/output SHA,8배크기,투명0/불투명255support검사통과. sourcealpha>=16이축소alpha<8로사라진픽셀0은이특정임계검사만을뜻함. 모든원본형태동일/모든잔가지게임표시보존주장금지. qa/local_sr_observed_review_v1.json.
- 고유원본누계124(타이틀1+전투123),전투후보110,보류13,미처리160/283. 총게임분모아님. 이전96후보정확보존. 이번신규원본21,추론86회,후보14. session92111정상exit0.
- 관측원본전체RGBA와키를현재디스크파일로재검증하고선정14그룹을연결. 기존BM023+타이틀포함16exactkey/15battle그룹팩: workspace/local-sr/observed-review-pack-v1/PSP/TEXTURES/NPUH10126. ini xxh64/ignoreAddress true/reduceHash false,최종ini읽기및모든PNG목록/해시검증. qa/local_sr_observed_review_pack_v1.json. 미설치/교체런타임미검증/최종ZIP아님. Orbit/UI v4 별도. 기존stage01팩/Start-Title-QA의기본팩경로는유지되어새팩시험시명시적으로연결해야함.
- batch_stage02_opaque.py에005최종검수파일존재시분류쓰기전에중단하는보호추가. 새후보/문자분류가과거batch재실행으로훼손되지않게함.
- C outputs/로컬_업스케일_관측재질_검수.png와진행.md갱신. Windows접근오류미해결확인으로Explorer대신Codex미리보기,외부이미지전송/에뮬실행없음.
- 다음: 13보류의국소색/형상재작업(특히이미관측키가있는7종)및stage1/2미처리문자/알파,남은지역/자산확장. OS접근가능시새16key팩과Orbit/UI후보를구분해고정ISO CLI실행→실제로드/표시/알파·UV·상태전환증거. 전체목표active,완료/blocked아님.
'''
    progress.write_text(text,'utf8')
print(json.dumps({'summary':summary,'pack':str(pack),'keys':len(bindings),'new_selected':sorted(selected),'new_holds':sorted(holds),'comparison':str(dest)},ensure_ascii=False))
