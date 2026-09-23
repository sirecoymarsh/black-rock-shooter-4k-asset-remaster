"""Persist reviewed 24-source batch and verify the final copied QA launch preparation."""
import json,hashlib,shutil
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];C=Path('C:/Users/CadriacLord/Documents/Codex/2026-09-22/brs-hd-ui-fonts')
def read(p):return json.loads((R/p).read_text('utf8'))
def write(p,v):(R/p).write_text(json.dumps(v,ensure_ascii=False,indent=2),'utf8')
def sha(b):return hashlib.sha256(b).hexdigest()
def checkfile(p,h):assert sha(Path(p).read_bytes())==h,p
if (R/'qa/local_sr008_review.json').exists():raise SystemExit('Finalized; use a new version.')
cat=read('qa/battle_sr_catalog.json');groups={g['group_id']:g for g in cat['groups']}
prior={gid:json.loads(json.dumps(g.get('candidate'))) for gid,g in groups.items() if g.get('candidate')};assert len(prior)==114
q=read('qa/local_sr008_inference.json');retry=read('qa/local_sr008_grid_rework.json');classification=read('qa/local_sr_stage0304_source_review.json')
choices={f'BM{i:03d}':0. for i in [129,133,144,169,170,173,174,176,178,179,181,182,185,188,190,191,194]}
choices.update({f'BM{i:03d}':.5 for i in [177,180,184,186,192]})
reasons={
 'BM129':'WDN retains subtle horizontal snow bands and grain; medium denoise smears these bands more.',
 'BM133':'WDN retains the branching crack and surrounding granular snow texture.',
 'BM144':'WDN retains panel divisions, recesses and the cross vent; slight inferred wear requires runtime review.',
 'BM169':'WDN preserves broad rocky masses and fissures without the stronger smoothing of the other condition.',
 'BM170':'WDN keeps the low-contrast mottled surface texture.',
 'BM173':'WDN retains the six circles, luminous strip, broken opening and panel arrangement.',
 'BM174':'WDN retains vents, access panels and wall divisions.',
 'BM175':'All five tested conditions fail: WDN turns the checker mesh into coarse chevrons; photo removes the mesh. Consumer/mesh reconstruction still required.',
 'BM176':'WDN retains horizontal folds and metallic grain.',
 'BM177':'Medium denoise retains curved mechanical panels with less exaggerated surface grain.',
 'BM178':'WDN retains the control-panel arrangement and surrounding panels.',
 'BM179':'WDN preserves three gauge-like shapes and the square access panel.',
 'BM180':'Medium denoise preserves the slot, curved ridge and circular fastener with fewer artificial scratches.',
 'BM181':'WDN retains the four corner fasteners and surface texture.',
 'BM182':'WDN retains the curved mechanical panel and rougher color variant.',
 'BM184':'Medium denoise keeps vertical bars straighter and reduces spurious marks.',
 'BM185':'WDN retains grilles and stacked controls; tiny panel semantics and consumer scaling remain unverified.',
 'BM186':'Medium denoise preserves the panel layout with fewer invented surface cracks.',
 'BM187':'WDN with input sigma0.5 reduces exaggerated grille edges while keeping the vent rows and cross; static candidate only.',
 'BM188':'WDN keeps the four dark squares and surrounding frame geometry.',
 'BM190':'WDN preserves the door mechanism and top grille.',
 'BM191':'WDN retains broad horizontal folds and the inset upper panel.',
 'BM192':'Medium denoise retains the inset rectangles and slot contours with fewer artificial cracks.',
 'BM194':'WDN retains the soft directional streaks of the green surface.'}
checked=[];models=set();selected={}
for report,name in [(q,'qa/local_sr008_inference.json'),(retry,'qa/local_sr008_grid_rework.json')]:
 for row in report['files']:
  gid=row['group_id'];g=groups[gid];src=Image.open(row['source']).convert('RGBA');assert sha(src.tobytes())==row['source_rgba_sha256']==g['rgba_sha256']
  assert src.size==(g['width'],g['height']) and src.getchannel('A').getextrema()==(255,255)
  for key in ['input','native','output']:
   if key in row:checkfile(row[key],row[key+'_sha256'])
  native=Image.open(row['native']);out=Image.open(row['output']).convert('RGBA')
  assert native.size==(src.width*4,src.height*4) and out.size==(src.width*8,src.height*8)==tuple(row['output_size'])
  assert out.getchannel('A').getextrema()==(255,255)
  for m in row.get('model_sources',[row.get('model')]):
   pair=(m['path'],m['sha256'])
   if pair not in models:checkfile(*pair);models.add(pair)
  pick=(report is q and choices.get(gid)==row['denoise_strength']) or (report is retry and row['id']=='BM187-wdn-filter05')
  reason=reasons[gid]
  if not pick and gid!='BM175':reason='Alternate condition not selected after source comparison. '+reason
  evidence=report['comparison_sheets']
  row['visual_review']={'reviewer':'Codex internal','status':'selected_for_game_review' if pick else 'held_rework_required' if gid=='BM175' else 'not_selected','reason':reason,'evidence':evidence}
  checked.append({'group_id':gid,'output':row['output'],'output_sha256':row['output_sha256'],'model_and_native_sha_verified':True,'source_rgba_sha256_verified':True,'size_8x_and_opaque_alpha_verified':True})
  if pick:selected[gid]={'source_report':name,'source_rgba_sha256':g['rgba_sha256'],'output':row['output'],'output_sha256':row['output_sha256'],'reason':reason,'status':'static_candidate_for_consumer_and_game_review','runtime_verified':False,'release_eligible':False}
assert len(checked)==54 and len(selected)==23 and len(q['group_ids'])==24
for row in classification['classifications']:
 g=groups[row['group_id']];g['classification']=row['classification'];g['classification_reason']=row['reason'];g['classification_review']='Codex internal: stage03-04-pending-01..06 source sheets'
for gid in q['group_ids']:
 g=groups[gid];assert not g.get('local_sr_attempted');g['local_sr_attempted']=True;g['candidate']=selected.get(gid)
 if gid not in selected:g['review_hold_reason']=reasons[gid]
for gid,candidate in prior.items():assert groups[gid]['candidate']==candidate
summary=cat['processing_summary'];pcount=sum(bool(g.get('local_sr_attempted')) for g in groups.values());ccount=sum(bool(g.get('candidate')) for g in groups.values());assert pcount==147 and ccount==137
summary.update({'battle_groups_locally_processed':pcount,'battle_static_candidates':ccount,'battle_processed_without_accepted_candidate':pcount-ccount,'battle_groups_not_yet_processed':len(groups)-pcount,'all_unique_originals_locally_processed':pcount+1,'latest_rework':'qa/local_sr008_review.json','new_unique_originals_latest_rework':24,'checked_output_records_latest_rework':54,'new_unique_originals_LOCAL_SR_008':24,'neural_passes_LOCAL_SR_008':54})
pack=read('qa/local_sr_observed_review_pack_v2.json');before_ini=sha((Path(pack['path'])/'textures.ini').read_bytes());assert before_ini==pack['textures_ini_sha256']
mapped={g['group_id'] for g in groups.values() if any(b['source_rgba_sha256']==g['rgba_sha256'] and b['size']==[g['width'],g['height']] for b in read('qa/battle_map_runtime_links.json')['bindings'])}
assert not set(q['group_ids'])&mapped,'Newly observed groups must be connected separately before claiming the pack unchanged.'
preflight=json.loads((C/'work/qa_latest_pack_preflight.json').read_text('utf-8-sig'));assert preflight['verify_only'] and not preflight['emulator_started'] and not preflight['routing_changed'] and preflight['pack_verification']['keys']==20
launcher=R/'tools/Start-Title-QA.ps1';backup=R/'tools/Start-Title-QA.before-sr008.ps1';assert not backup.exists();shutil.copyfile(launcher,backup);shutil.copyfile(C/'work/Start-Title-QA.ps1',launcher)
checkfile(launcher,sha((C/'work/Start-Title-QA.ps1').read_bytes()));preflight['verified_script_sha256']=sha(launcher.read_bytes());preflight['prior_script_backup']=str(backup);write('qa/local_sr008_launch_preflight.json',preflight)
report={'schema':'brs-local-sr-review/v8','batch':'LOCAL-SR-008','selected':selected,'new_holds':{'BM175':reasons['BM175']},'checked_outputs':checked,'new_unique_originals':24,'new_actual_local_neural_passes':54,'prior_candidates_preserved':114,'source_reviewed_groups':50,'deferred_source_groups':[g for g in classification['group_ids'] if g not in q['group_ids']],'processing_summary':summary,'pack_unchanged_keys':20,'new_sources_observed_keys':0,'runtime_verified':False,'release_eligible':False}
for name,obj in [('qa/local_sr008_inference.json',q),('qa/local_sr008_grid_rework.json',retry),('qa/battle_sr_catalog.json',cat),('qa/local_sr008_review.json',report)]:write(name,obj)
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',21);sheet=Image.new('RGB',(1080,1560),'#293440');d=ImageDraw.Draw(sheet)
for j,label in enumerate(['원본 단순 확대','로컬 AI 처리 · 게임 검수 전']):d.text((j*540+12,10),label,font=font,fill='white')
for i,gid in enumerate(['BM133','BM144','BM188','BM190']):
 src=Image.open(groups[gid]['representative']['png']).convert('RGB');out=Image.open(selected[gid]['output']).convert('RGB');scale=min(510/src.width,310/src.height,8);wh=(round(src.width*scale),round(src.height*scale))
 for j,im in enumerate([src,out]):
  x=j*540+12;y=55+i*375;d.text((x,y),gid,font=font,fill='white');sheet.paste(im.resize(wh,Image.Resampling.NEAREST if j==0 else Image.Resampling.LANCZOS),(x,y+34))
sheet.save(R/'outputs/local_sr008_selected.png');shutil.copyfile(R/'outputs/local_sr008_selected.png',C/'outputs/로컬_업스케일_3·4지역_검수.png')
note=f'''# 로컬 업스케일 진행 — LOCAL-SR-008

- 실제 로컬 GPU 추론을 거친 고유 원본 **148종**: 타이틀1 + 전투재질147.
- 전투재질 정적 검수 후보 **137종**, 처리 후 보류 **10종**, 미처리 **136종/283종**. 전투맵 집계이며 게임 전체 완료율은 아닙니다.
- 보류 재작업4종을 후보로 반영했고, 3·4지역 새 원본24종의 두 설정 및 재작업을 합친54출력을 직접 비교해23종을 후보로 골랐습니다. 작은 환기구1종은 재작업 후에도 무늬가 바뀌거나 지워져 보류했습니다.
- SwinIR20출력은 이번 자산에서 테두리·무늬·형상이 부자연스러워 미채택입니다. GPT BM162 대안1회도 원본 빈틈과 실루엣을 바꿔 미채택입니다. GPT 시도는 외부 이미지 편집이며 나머지 보고된 추론은 로컬 RTX5080입니다.
- 실제 AI 복원4배 후 보간2배로 최종8배 크기입니다. 모든 픽셀을 AI로8배 복원했다고 표현하지 않습니다.
- 검수팩은 **20개 정확한 관측키**(타이틀1+재질19)입니다. 이번 새24종은 관측키가 없어 임의 연결하지 않았습니다.
- 검수팩: {pack['path']}
- 실행 준비 절차는 위20키팩을 기본으로 지정하고 파일 해시를 검사하도록 수정했습니다. exe/ISO/20개PNG 검증은 통과했으며, 검증 전용 실행으로 에뮬 시작·설치경로 변경은 없었습니다.
- 실제 교체 표시, Orbit 한글 폰트와 LOCK ON, 지역1~6/EX/진엔딩 전체 경로 검증은 남았습니다. Windows 검수창 접근 오류의 해소는 아직 확인되지 않았습니다. 최종 배포 ZIP은 없습니다.
- 다음: 3·4지역의 투명 철골·폐허·효과와 문자26종, 기존 보류10종 및 나머지 지역/필드/적/이펙트/컷신 처리와 소비 확인. 특수 PTMD6건도 미해결입니다.
'''
(C/'outputs/로컬_업스케일_진행.md').write_text(note,'utf8')
with (R/'PROGRESS.md').open('a',encoding='utf8') as f:f.write('''

## 2026-09-23 — LOCAL-SR-008: 3·4지역 신규24종과 최신검수팩 실행준비

- stage03/04미처리50종의원본6페이지를모두직접검토. 불투명재질24종을WDN/dn0.5 두설정48actualpass. 6페이지비교후BM175/187격자변형확인→WDN사전필터0.5/photo/photo사전필터0.5 추가6actualpass,2페이지직접검수. 총24신규원본/54출력/54로컬추론,외부전송없음.
- 선택23: WDN BM129/133/144/169/170/173/174/176/178/179/181/182/185/188/190/191/194; dn0.5 BM177/180/184/186/192; filteredWDN BM187. BM175는WDN에서체커메시가굵은지그재그로변하고photo에서메시소실하여전조건보류. 후보는추정재질을포함하며원본HD복원확정/실제게임통과아님.
-54출력 원본RGBA·모델·native·입력·최종파일해시/4배native·8배출력/알파255검사통과. 기존114후보정확보존. 누계고유원본148(전투147+타이틀1),전투후보137/보류10/미처리136/283. source범위416항목410디코드6특수형식미해결. 게임전체분모아님.
-50원본전체분류: 다음26종에는얇은철골·분할폐허·효과알파·BM189큰문자/엠블럼·BM193평탄strip·BM199softdark등포함. 범위제외없음. qa/local_sr_stage0304_source_review.json에개별분류. BM189의문자미확정,의미번역없음.
-새24그룹은현재관측RGBA/key연결0이므로20key observed-review-pack-v2 변경없음. 새모델결과를추측키로설치하지않았다.
-Start-Title-QA.ps1의candidate기본을observed-review-pack-v2로변경,명시적v1/v2선택+VerifyOnly추가. INI/키별PNG/SHA/파일모집단검사와복사후재검사,메타데이터에검사결과기록. 이전script는tools/Start-Title-QA.before-sr008.ps1. 구문검사및VerifyOnly로exe/ISO/20PNG/INI일치통과,실제Start-Process경로는이번에실행하지않았음. qa/local_sr008_launch_preflight.json. Get-CimInstance/OS화면접근문제는별개이며해결주장없음.
-사용자진행.md와3·4지역검수.png갱신. 에뮬/사용자게임입력·설치없음. 다음은26투명/문자/효과및나머지지역,OS접근가능시고정exe+ISO CLI 실게임/20key팩/Orbit/LOCKON검증. 전체목표active;최종ZIP미완료.
''')
print(json.dumps({'new_selected':len(selected),'hold':['BM175'],'summary':summary,'checked_outputs':len(checked),'launch_preflight':'passed without launch'},ensure_ascii=False))
