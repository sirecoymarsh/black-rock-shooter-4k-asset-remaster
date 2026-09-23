"""Commit directly reviewed retries, verify lineage, and build an uninstalled QA pack."""
import json, hashlib, shutil, re
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

R=Path(__file__).resolve().parents[1]
C=Path('C:/Users/CadriacLord/Documents/Codex/2026-09-22/brs-hd-ui-fonts')
def read(p): return json.loads((R/p).read_text('utf8'))
def write(p,obj): (R/p).write_text(json.dumps(obj,ensure_ascii=False,indent=2),'utf8')
def sha(b): return hashlib.sha256(b).hexdigest()
def checkfile(p,h): assert sha(Path(p).read_bytes())==h,p
final=R/'qa/local_sr007_review.json'
if final.exists(): raise SystemExit('LOCAL-SR-007 is finalized; use a new version for subsequent work.')
cat=read('qa/battle_sr_catalog.json');groups={g['group_id']:g for g in cat['groups']}
prior={gid:json.loads(json.dumps(g['candidate'])) for gid,g in groups.items() if g.get('candidate')}
assert len(prior)==110 and sum(bool(g.get('local_sr_attempted')) for g in groups.values())==123
rework=read('qa/local_sr_observed_rework_v2.json');swin=read('qa/local_sr_swinir_held_v1.json')
choices={gid:gid+'-prefilter075-guided065' for gid in ['BM130','BM159','BM164','BM165']}
reasons={
 'BM130':'Prefiltered neural retry reduces invented zigzag grooves; source-guided color retains the cliff bands. Softer fine detail remains a game-review limitation.',
 'BM159':'Filtered inference with source-guided color reduces the overly busy yellow microtexture; broad patches and prior alpha are retained.',
 'BM164':'Filtered inference with source-guided color reduces glossy folded blobs while retaining the scattered green clusters; selected only for game review.',
 'BM165':'Same treatment reduces stone-like highlights in the gray variant; selected only for game review.',
 'BM156':'Tree crown retains flat/glossy planes or becomes too blurred; trunk and branch appearance still need a different treatment.',
 'BM162':'All local retries remain rock-like/glossy or lose too much foliage detail. GPT alternative also changes coverage and is rejected.',
 'BM163':'Leaf strips still read as knotted tubes; filtering and source guidance do not recover credible leaf structure.'}
swin_reasons={
 'BM130':'Classical SR emphasizes dither into dots and thin etched contours rather than restoring cliff texture.',
 'BM156':'Bright rims, dots and flat patches distort crown and trunk detail.',
 'BM159':'Flat yellow islands and dark cutouts retain grid-like artifacts.',
 'BM162':'White rims and pooled highlights give foliage a glossy cellular appearance.',
 'BM163':'Black/yellow rims and repeated tubular shapes do not resolve the leaf geometry.',
 'BM164':'Curled glossy patches and ringing replace leaf detail.',
 'BM165':'Gray leaf fragments become bright hard-edged curled patches.',
 'BM082':'Frame stripes, hub outline and blade highlights gain severe ringing and hard invented outlines.',
 'BM056':'Vertical window mullions bend and merge with dark openings.',
 'BM114':'Dither is emphasized as isolated dots and thin outlines; surface geometry is not improved.'}
checked=[];models=set();selected={}
for report,report_name in [(rework,'qa/local_sr_observed_rework_v2.json'),(swin,'qa/local_sr_swinir_held_v1.json')]:
 for row in report['files']:
  gid=row['group_id'];g=groups[gid];src=Image.open(row['source']).convert('RGBA')
  assert src.size==(g['width'],g['height']) and sha(src.tobytes())==row['source_rgba_sha256']==g['rgba_sha256']
  checkfile(row['output'],row['output_sha256']);out=Image.open(row['output']).convert('RGBA')
  assert out.size==(src.width*8,src.height*8)==tuple(row['output_size'])
  for key in ['parent','alpha_parent']:
   if key in row:checkfile(row[key],row[key+'_sha256'])
  ap=Image.open(row['alpha_parent']).convert('RGBA');assert out.getchannel('A').tobytes()==ap.getchannel('A').tobytes()
  lin=np.asarray(src.getchannel('A').resize(out.size,Image.Resampling.BILINEAR));a=np.asarray(out.getchannel('A'))
  assert not np.any(a[lin==0]) and np.all(a[lin==255]==255)
  if 'model' in row:
   m=row['model'];pair=(m['path'],m['sha256'])
   if pair not in models:checkfile(*pair);models.add(pair)
  for part in row.get('parts',[]):
   for key in ['input','native']:checkfile(part[key],part[key+'_sha256'])
  pick=report is rework and choices.get(gid)==row['id']
  reason=swin_reasons[gid] if report is swin else reasons[gid]
  if report is rework and gid in choices and not pick:reason='Not selected: residual-only alternatives retain invented detail; un-guided filtered alternatives are softer. '+reason
  evidence=[str(R/f'outputs/local_sr_swinir_{gid}.png')] if report is swin else [str(R/f'outputs/local_sr_observed_rework_{gid}.png')]
  if pick:evidence.append(str(R/f'outputs/local_sr007_matte_{gid}.png'))
  row['visual_review']={'reviewer':'Codex internal','status':'selected_for_game_review' if pick else 'rejected_condition' if report is swin else 'not_selected' if gid in choices else 'held_rework_required','reason':reason,'evidence':evidence}
  checked.append({'group_id':gid,'output':row['output'],'sha256':row['output_sha256'],'lineage_and_model_verified':True,'alpha_exact_to_parent':True,'empty_and_solid_support_verified':True})
  if pick:
   selected[gid]={'source_report':report_name,'source_rgba_sha256':g['rgba_sha256'],'output':row['output'],'output_sha256':row['output_sha256'],'reason':reason,'status':'static_candidate_for_consumer_and_game_review','runtime_verified':False,'release_eligible':False}
   g['candidate']=selected[gid];g.pop('review_hold_reason',None)
  elif report is rework and gid not in choices:g['review_hold_reason']=reason
assert len(checked)==48 and len(selected)==4
assert rework['new_neural_passes']==10 and swin['new_neural_passes']==26
for gid,cand in prior.items():assert groups[gid]['candidate']==cand

gpt=read('qa/gpt_bm162_trial_v1.json');checkfile(gpt['project_copy'],gpt['output_sha256'])
assert sha(Image.open(gpt['source']).convert('RGBA').tobytes())==gpt['source_rgba_sha256']
gpt['visual_review']={'reviewer':'Codex internal','status':'rejected','reason':'Generated foliage fills source gaps, repeats leaf motifs and changes coverage. Alpha mass is about 29.24% higher; 1254-square output also misses the requested 1024-square canvas. Do not adopt or force-fit by copying only source alpha.','evidence':'outputs/gpt_bm162_compare_v1.png'}
gpt['release_eligible']=False
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18)
sheet=Image.open(R/'outputs/gpt_bm162_compare_v1.png');d=ImageDraw.Draw(sheet);d.rectangle((1024,0,1535,44),fill='#293440');d.text((1034,10),'GPT 대안 · 원형 변경으로 미채택',font=font,fill='white');sheet.save(R/'outputs/gpt_bm162_compare_v1.png')

pack=R/'workspace/local-sr/observed-review-pack-v2/PSP/TEXTURES/NPUH10126'
assert not pack.exists(),'Versioned pack already exists; inspect before replacing.'
(pack/'materials').mkdir(parents=True);(pack/'title').mkdir()
by_identity={(g['width'],g['height'],g['rgba_sha256']):gid for gid,g in groups.items()}
bindings={};proof=[]
for b in read('qa/battle_map_runtime_links.json')['bindings']:
 gid=by_identity[(*b['size'],b['source_rgba_sha256'])];cand=groups[gid].get('candidate')
 if not cand:continue
 assert b['logical_full_image_match']
 for m in b['matches']:
  observed=next((Path(p) for p in m['paths'] if Path(p).is_file()),None);assert observed
  im=Image.open(observed).convert('RGBA');assert im.size==tuple(b['size']) and sha(im.tobytes())==b['source_rgba_sha256']
  key=m['key'];value=f'materials/{gid}.png';assert re.fullmatch(r'00000000[0-9a-f]{16}',key)
  assert key not in bindings or bindings[key]==value
  checkfile(cand['output'],cand['output_sha256']);shutil.copyfile(cand['output'],pack/value);checkfile(pack/value,cand['output_sha256'])
  bindings[key]=value;proof.append({'key':key,'group_id':gid,'asset_id':b['asset_id'],'observed_source_png':str(observed),'observed_source_png_sha256':sha(observed.read_bytes()),'observed_rgba_sha256':b['source_rgba_sha256'],'output_sha256':cand['output_sha256'],'consumer_scene_uv':'unverified','replacement_runtime_verified':False})
oldpack=read('qa/local_sr_observed_review_pack_v1.json');tk='0000000086ba34d7c28b381c';title=Path(oldpack['path'])/oldpack['keys'][tk]
checkfile(title,'9bfc5e1abb745a408ca66c8f15ee6a809564e3ebb2f1099e508b2672896916d8');bindings[tk]=oldpack['keys'][tk];shutil.copyfile(title,pack/bindings[tk])
assert len(bindings)==20 and {p['group_id'] for p in proof}-{p['group_id'] for p in oldpack['battle_binding_evidence']}==set(choices)
for key,value in oldpack['keys'].items():assert bindings[key]==value and (pack/value).read_bytes()==(Path(oldpack['path'])/value).read_bytes()
ini='[options]\nversion = 1\nhash = xxh64\nignoreAddress = true\nreduceHash = false\n\n[hashes]\n'+''.join(f'{k} = {v}\n' for k,v in sorted(bindings.items()))
(pack/'textures.ini').write_text(ini,'utf8')
actual={k:v for k,v in re.findall(r'^(00000000[0-9a-f]{16}) = (.+)$',(pack/'textures.ini').read_text('utf8'),re.M)};assert actual==bindings
assert {p.relative_to(pack).as_posix() for p in pack.rglob('*.png')}==set(bindings.values())
(pack/'README.txt').write_text('BRS NPUH10126 LOCAL-SR-007 isolated QA pack\n20 exact observed keys: title +19 materials.\nUninstalled; game rendering/UV/blend modes unverified.\nOrbit/UI v4 remain separate. Not a final release.\n','utf8')
pack_report={'schema':'brs-observed-review-pack/v2','path':str(pack),'keys':bindings,'battle_binding_evidence':proof,'textures_ini_sha256':sha((pack/'textures.ini').read_bytes()),'unique_battle_groups':19,'all_keys':20,'new_keys_this_batch':4,'prior_key_count':16,'all_prior_files_exact':True,'installed':False,'runtime_verified':False,'release_eligible':False}
summary=cat['processing_summary'];summary.update({'battle_static_candidates':114,'battle_processed_without_accepted_candidate':9,'latest_rework':'qa/local_sr007_review.json','new_unique_originals_latest_rework':0,'checked_output_records_latest_rework':48,'new_unique_originals_LOCAL_SR_007':0,'neural_passes_LOCAL_SR_007':36,'review_pack_exact_keys':20})
assert sum(bool(g.get('candidate')) for g in groups.values())==114
report={'schema':'brs-local-sr-review/v7','batch':'LOCAL-SR-007','previous_goal_turn':'progress: local rework, GPT diagnostic rejection evidence, official SwinIR inference completed; review was pending','selected':selected,'checked_outputs':checked,'actual_new_local_neural_passes':36,'local_output_records':48,'new_unique_originals':0,'swinir_outputs_rejected':20,'external_gpt_trials':1,'external_gpt_trials_adopted':0,'remaining_holds':[gid for gid,g in groups.items() if g.get('local_sr_attempted') and not g.get('candidate')],'processing_summary':summary,'qa_pack_report':'qa/local_sr_observed_review_pack_v2.json','runtime_verified':False,'release_eligible':False,'superseded_scale_evidence':['outputs/local_sr_observed_rework_scale_01.png','outputs/local_sr_observed_rework_scale_02.png'],'scale_evidence_correction':'Older page overlapped BM130 black/light views and capped its scale. Use local_sr007_matte_BM*.png: exact 1x black/2x light, no overlap.'}
for name,obj in [('qa/local_sr_observed_rework_v2.json',rework),('qa/local_sr_swinir_held_v1.json',swin),('qa/gpt_bm162_trial_v1.json',gpt),('qa/local_sr_observed_review_pack_v2.json',pack_report),('qa/battle_sr_catalog.json',cat),('qa/local_sr007_review.json',report)]:write(name,obj)
progress=R/'PROGRESS.md'
with progress.open('a',encoding='utf8') as f:f.write('''

## 2026-09-23 — LOCAL-SR-007: 보류 재작업 판정 및 관측키20개 시험팩

- 이전 목표턴은 progress: WDN7종 재작업28출력/실제10pass와 SwinIR10종20출력/실제26pass가 완료된 상태. 이번 계속작업에서 모든17개 비교표와 선택4종의 정확1배검정/2배밝은matte를 직접검수하고 판정을 확정했다. 고유원본은 추가하지 않았다.
- BM130/159/164/165 prefilter075-guided065를 게임검수 후보로 선정. 절벽 지그재그홈/잎 광택 완화, 원본색 가이드+neural residual. 원본알파 그대로가 아니라 이전WDN의35%neural/65%source-bilinear 알파에 byte-exact. BM156/162/163은 평면적인가지·돌질감·관모양잎 문제로 계속보류.
- SwinIR20조건은 dither테두리/반짝임/휘는창틀/평면무늬로 전부미채택. 공식모델001_classicalSR_DF2K_s64w8_SwinIR-M_x4.pth SHA4e78e33f22c1aa8a773db0cf4a7381bae97c2362c717f155439ebc690cbd9215, Apache2.0 출처/라이선스 models.json 유지.48출력의원본·모델·입력·native·부모·최종해시/8배크기/알파support 재검증. 실제36로컬pass; 후처리파생물을추가추론으로세지않는다.
- GPT BM162 1회는 외부builtin image_gen 편집이었다. 실제모델ID비공개. 1254×1254 출력,알파mass1.2924/IoU0.7711/원본빈영역침범33356픽셀 및 반복잎/빈틈손실로미채택. qa/gpt_bm162_trial_v1.json와workspace/gpt-trials/BM162-v1/prompt.txt. 전체작업을외부전송없음이라고표현하지않는다.
- catalog 후보110→114,보류13→9,고유원본누계124(전투123+타이틀1),미처리160/283. 기존110후보/기존시험팩16키파일정확보존. 전체원본RGBA/크기확인후4키추가한 observed-review-pack-v2는20키(19battle+title),미설치/실제교체표시미검증/최종ZIP아님. Orbit/UI는별도.
- 이전 scale_01의BM130두matte겹침과2배표기의축소상한을발견,검수근거에서대체. local_sr007_matte_BM130/159/164/165.png는정확1배와2배이며미리보기표시배율은뷰어에따름.
- 런타임Windows접근불가조건의외부변화증거없어검은화면캡처반복/사용자입력없음. 에뮬재실행없음. 다음: stage03/04미처리50종원본검토및처리,9보류와특수PTMD6건계속해결;OS접근가능시고정exe+ISO CLI로20key팩/Orbit/LOCKON표시검증. 전체지역1~6/EX/진엔딩·다른자산·최종ZIP미완료,목표active.
''')
shutil.copyfile(R/'outputs/local_sr007_matte_BM130.png',C/'outputs/로컬_업스케일_절벽_재작업.png')
print(json.dumps({'selected':list(selected),'summary':summary,'pack':str(pack),'verified_outputs':len(checked)},ensure_ascii=False))
