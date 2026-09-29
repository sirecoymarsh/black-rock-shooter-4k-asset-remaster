"""Freeze reviewed UI batch; export UI-only overlay without touching live packs."""
from pathlib import Path
import sys,json,hashlib,subprocess,configparser,shutil,html
R=Path(__file__).resolve().parents[1];W=R/'workspace/ui-remaining-ko-001';O=R/'outputs/ui-remaining-ko-001'
sys.stdout.reconfigure(encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text('utf8'))
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2),'utf8')
def cfg(p):
 c=configparser.ConfigParser(interpolation=None);c.optionxform=str;c.read(p,encoding='utf-8-sig');return c
before={p:sha(p) for p in W.rglob('*') if p.is_file() and 'ui-overlay' not in p.parts}
for script in ['build_remaining_ko_001.py','review_remaining_ko_001.py']:
 subprocess.run([sys.executable,str(R/'tools'/script)],check=True)
changed=[str(p) for p,h in before.items() if sha(p)!=h];assert not changed,changed
m=read(W/'manifest.json');review=read(R/'qa/ui_remaining_ko_001_review.json');assert review['static_status']=='PASS'
pack=W/'pack/PSP/TEXTURES/NPUH10126';current=cfg(pack/'textures.ini');base=cfg(Path(m['baseline'])/'textures.ini')
affected={k for r in m['records'] for k in r['binding']['keys']};untouched=0
for k,rel in base['hashes'].items():
 if k in affected:continue
 assert current['hashes'][k]==rel and sha(pack/rel)==sha(Path(m['baseline'])/rel);untouched+=1
assert set(current['hashes'])==set(base['hashes'])|affected
legacy={r['id']:r for r in read(R/'qa/ui_build_v4.json')['records']}
for r in m['records']:
 if r['id'].startswith('UI-'):
  assert sha(Path(legacy[r['id']]['candidate']))==legacy[r['id']]['candidate_sha256']
  from PIL import Image
  old=Image.open(legacy[r['id']]['candidate']).convert('RGBA');new=Image.open(r['files']['candidate']['path']).convert('RGBA');width,height=r['logical_size']
  assert old.crop((0,0,width*8,height*8)).tobytes()==new.crop((0,0,width*8,height*8)).tobytes()

observed=sum(bool(r['binding']['observed']) for r in m['records']);calculated=len(m['records'])-observed
accept={'schema':'brs-remaining-ko-acceptance/v1','translator_model':'Codex internal','reviewer':'active Codex internal model','reviewed_on':'2026-09-29','manifest_sha256':sha(W/'manifest.json'),'static_review_sha256':sha(R/'qa/ui_remaining_ko_001_review.json'),'asset_families':len(m['records']),'semantic_entries':m['semantic_entry_count'],'static_status':'PASS','visual_status':'PASS','visual_scope':'Full atlas comparisons and seven affine SDO assemblies. Atlas fragments are judged in their assembled state.','proofs':[{'path':str(p),'sha256':sha(p)} for p in sorted(O.glob('*-atlas.png'))]+review['consumer_proofs'],'determinism':{'status':'PASS','compared_files':len(before),'changed_files':changed},'unaffected_baseline_bindings_verified':untouched,'observed_binding_families':observed,'calculated_unobserved_binding_families':calculated,'runtime_verified':False,'live_installation_performed':False,'runtime_limitations':['Unobserved contiguous-source keys require in-game matching; enclosing-LPK padding is a recorded hypothesis.','UI-22 has exact calculated maxSeenV hashes only from 350 through 512 rows, covering every edited glyph.','Title v2 requires its companion ISO. Other combined packs must receive only the UI delta.'],'protected_latin':['Actual L/R/START/SELECT button labels','A/B/C grades, numeric digits and standard units','Brand logos/copyright and character identifiers'],'remaining_outside_this_batch':['Original tutorial screenshots: 61 assets / 31 unique images with embedded English or Japanese, audited separately; inclusion question sent to user.','Native save-dialog art and any unparsed runtime-only surface are not included in this acceptance.']}
write(R/'qa/ui_remaining_ko_001_acceptance.json',accept)
write(W/'translation-map.json',{'translator_model':'Codex internal','entries':[l for r in m['records'] for l in r['labels']]})

# Export cumulative UI delta from the successful checkpoint, preserving the
# separate background task's new bindings during a future merge.
checkpoint=R.parent/'black-rock-shooter-hd-retexture/checkpoints/booster-working-20260924/PSP/TEXTURES/NPUH10126'
frozen=cfg(checkpoint/'textures.ini');delta={k:v for k,v in current['hashes'].items() if k not in frozen['hashes'] or v!=frozen['hashes'][k]}
overlay=W/'ui-overlay/PSP/TEXTURES/NPUH10126';overlay.mkdir(parents=True,exist_ok=True)
for rel in set(delta.values()):
 dst=overlay/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(pack/rel,dst)
(overlay/'textures-fragment.ini').write_text('[hashes]\n'+''.join(k+' = '+v+'\n' for k,v in sorted(delta.items())),'utf8')
write(W/'ui-overlay/manifest.json',{'translator_model':'Codex internal','bindings':delta,'unique_pngs':len(set(delta.values())),'files':[{'path':rel,'sha256':sha(overlay/rel)} for rel in sorted(set(delta.values()))],'required_title_iso':m['required_companion_iso'],'installation_performed':False,'instruction':'Merge these hash entries into the latest combined textures.ini. Do not replace another task\'s newer complete INI with the old baseline.'})

sections=['<!doctype html><html lang="ko"><meta charset="utf-8"><title>BRS 한국어 UI 비교</title><style>body{background:#19232e;color:#ecf1f7;font:18px sans-serif;max-width:1500px;margin:32px auto;padding:12px}img{max-width:100%;display:block;margin:12px 0 30px}a{color:#8dc9ff}section{border-top:1px solid #536274;padding-top:20px}p{line-height:1.6}</style><h1>한국어 UI 추가 검수</h1><p>23개 애셋 묶음 · 문구 53개 한국어화·수정. 원본에 맞춘 글자 높이와 굵기로 메뉴, 전투 결과, 상태 아이콘, 보조 문구를 제작했습니다.</p><p><strong>정적·시각 검수 완료. 실제 게임 적용·플레이 검수는 아직 하지 않았습니다.</strong> 일부 매핑은 관측 대신 원본 바이트로 계산했으므로 실게임 확인이 필요합니다.</p>']
for p in sorted(O.glob('consumer-*.png')):sections.append('<section><img src="'+html.escape(p.name)+'" alt="소비자 조립 비교"></section>')
sections.append('<h2>전체 애셋 비교</h2><p>조각난 글자는 위의 소비자 조립 비교를 기준으로 확인합니다.</p>')
for p in sorted(O.glob('*-atlas.png')):sections.append('<section><h3>'+html.escape(p.stem)+'</h3><img loading="lazy" src="'+html.escape(p.name)+'"></section>')
(O/'index.html').write_text('\n'.join(sections),'utf8')
(O/'README.md').write_text(f'# 한국어 UI 추가 묶음\n\n23개 애셋 묶음과 문구 53개를 한국어화·수정했습니다. 원본처럼 충분한 글자 높이와 굵기를 유지하고, 영문 그림자·공유 복수형 조각까지 정리했습니다. `index.html`에서 비교를 볼 수 있습니다.\n\n- 정적 검증 {len(review["checks"])}검사 PASS; 재빌드 {len(before)}파일 동일.\n- 관측 키가 있는 묶음 {observed}개 / 계산 키만 있는 묶음 {calculated}개. 계산 키의 실제 게임 매칭은 미검증입니다.\n- 누적 시험 팩: `{pack}`.\n- 최신 배경 팩에 병합할 UI 전용 델타: `{W / "ui-overlay"}` ({len(delta)}키, {len(set(delta.values()))}PNG).\n- 타이틀 v2는 `{m["required_companion_iso"]}`와 함께 사용해야 합니다.\n- 성공 ISO·라이브 팩·다른 채팅의 배경 파일은 변경하지 않았습니다.\n\n원본 튜토리얼 캡처 61장(고유 31장)의 영문·일문과 네이티브 저장 아이콘은 별도 감사에 기록했으며 이번 23개 묶음의 완료 판정에 포함하지 않습니다.\n','utf8')
p=R/'PROGRESS.md';text=p.read_text('utf8');marker='## 현재 상태 — 2026-09-29, 타이틀 v2 및 잔여 영문 UI'
text=text.replace(marker,'## 이전 상태 — 타이틀 v2 및 잔여 영문 감사',1)
status=f'## 현재 상태 — 2026-09-29, 추가 UI 23개 묶음 정적 완료\n\n- 최신 사용자 요청: HD 팩의 남은 영문 UI 모두 한국어화. 사용자가 승인한 굵고 큰 원본 계승 스타일 유지.\n- 추가 완료: `workspace/ui-remaining-ko-001`의 23애셋 묶음, 문구 53개. 안정 ID MUI-01/05/16/19/27/28, RUI-007..012, BUI-001..003 및 기존 미관측 UI-00/12/13/21/22/23/24/26 활성 후보.\n- 정적 {len(review["checks"])}검사와 시각 검수 PASS, 재빌드 {len(before)}파일 동일. 최종 근거 `qa/ui_remaining_ko_001_acceptance.json`. 실게임 적용/검수 미수행.\n- 누적 시험 팩 900키. 이 중 UI-22의 163개는 350..512행까지의 maxSeenV 길이를 원본 바이트로 계산한 정확 키 후보이며, 163개 독립 애셋이 아님. 관측된 매핑 묶음 {observed}개, 계산만 된 매핑 {calculated}개를 구분.\n- **최신 배경 작업과 병합할 때 전체 INI를 덮어쓰지 말 것.** `workspace/ui-remaining-ko-001/ui-overlay`의 UI 전용 {len(delta)}키/{len(set(delta.values()))}PNG만 병합. 타이틀 v2 동봉 ISO 필수 조건 유지.\n- 사용자 비교표 `outputs/ui-remaining-ko-001/index.html`. 성공/라이브 ISO와 팩은 변경하지 않음.\n- 원본 튜토리얼의 flag 0 직접색 텍스처가 실제로는 타일 순서임을 시각적으로 확인. `outputs/ui-tutorial-audit` 67장 중 UI 포함 61장, 고유 31장(나머지6은 배경/삽화). 바이트왕복/시각복원까지만 확인; 관측 키 일치0. 아직 번역하거나 적용하지 않았다. 포함 여부를 사용자에게 async 질문했고 답변 대기.\n- 다음: 질문 답변에 따라 튜토리얼 범위 확정. 포함 시 고유 31장별 문구/마스크/배경 복원 지도를 작성하고 한국어화. 메뉴만 선택 시 추가 UI 묶음을 전달하고 중간 게임 조작 없이 종료. 네이티브 저장 아이콘의 NEW DATA/SYSTEM DATA는 별도 자산이며 현재 HD 매핑 밖.\n\n'
p.write_text(text.replace('# 진행 기록\n\n','# 진행 기록\n\n'+status,1),'utf8')
print(json.dumps({'acceptance':'PASS','assets':23,'semantic_entries':53,'deterministic_files':len(before),'observed_families':observed,'calculated_families':calculated,'overlay_keys':len(delta),'overlay_pngs':len(set(delta.values()))}))
