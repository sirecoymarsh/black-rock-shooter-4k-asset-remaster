import json,hashlib,shutil,ast
from pathlib import Path
from PIL import Image
import numpy as np
R=Path('P:/AI/Codex/projects/black-rock-shooter-hd-ui-fonts');C=Path('C:/Users/CadriacLord/Documents/Codex/2026-09-22/brs-hd-ui-fonts')
def read(n):return json.loads((R/n).read_text('utf-8-sig'))
def write(n,v):(R/n).write_text(json.dumps(v,ensure_ascii=False,indent=2),'utf8')
for fn in ['rework_soft_alpha_v3.py','rework_linear_and_foliage.py','prepare_soft_review.py','finalize_soft_review.py','finalize_stage01_sr.py']:
    ast.parse((R/'tools'/fn).read_text('utf8'))
cat=read('qa/battle_sr_catalog.json');summary=cat['processing_summary']
summary['new_unique_originals_LOCAL_SR_003']=summary.pop('new_unique_originals_this_batch',47)
summary['checked_output_records_LOCAL_SR_003']=summary.pop('checked_output_records',115)
summary['checked_output_records_latest_rework']=12
write('qa/battle_sr_catalog.json',cat);sr=read('qa/local_sr_soft_review_v4.json');sr['processing_summary']=summary;write('qa/local_sr_soft_review_v4.json',sr)
sessions=[]
for sid,backend,observation in [('UIF-Q005-title-baseline','VULKAN','Dark/black window captures; original GE records show INFORMATION UI. One guest Start press was completed/released.'),('UIF-Q006-title-baseline','DIRECT3D11','Window screenshots remained black. No guest button or Windows activation.'),('UIF-Q007-title-baseline','VULKAN','Returned exact QA window id70304. Foreground activation attempt failed with GetCursorPos access denied 0x80070005 before a new screenshot.')]:
    meta=read(f'workspace/sessions/{sid}/session.json');assert meta.get('stopped_utc') and meta.get('previous_routing_restored')
    sessions.append({'session':sid,'backend':backend,'metadata':meta,'observation':observation,'runtime_texture_acceptance':False})
proof=[]
for name,sid in [('q005-vulkan-capture.png','UIF-Q005-title-baseline'),('q006-direct3d-capture.png','UIF-Q006-title-baseline')]:
    source=C/'work'/name;dest=R/f'workspace/sessions/{sid}/captures'/name;shutil.copyfile(source,dest);im=Image.open(dest).convert('RGB');a=np.asarray(im)
    proof.append({'path':str(dest),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'size':list(im.size),'nonzero_rgb_values':int(np.count_nonzero(a))})
runtime={'schema':'brs-runtime-observation/v2','sessions':sessions,'screenshots':proof,'fixed_iso_sha256':'525b5d2b7d8f4723be25b026e72b69d07d30c2cf84d8a48235577ca3728fc92a','window_capture':'Computer Use @oai/sky, returned exact QA executable window only. No launch through Computer Use.','windows_activation_attempt':{'session':'UIF-Q007-title-baseline','result':'GetCursorPos failed: access denied (0x80070005)','focus_change_confirmed':False,'mouse_or_keyboard_input_sent':False},'desktop_lock_state':'unconfirmed; user clarification pending','guest_input':{'session':'UIF-Q005-title-baseline','api':'input.buttons.press','button':'start','duration':2,'release_response_confirmed':True,'record':'workspace/sessions/UIF-Q005-title-baseline/captures/boot-start.json'},'emucap_route':{'bootstrap':'PSP supported; listener47800; no managed emulator generation launched','plan':'adapter binary unavailable; bridge available; headless binary not installed','launch_attempted':False},'source_reference':'https://github.com/hrydgard/ppsspp/blob/v1.20.4/Core/ConfigValues.h','candidate_session_launched':False,'runtime_verified':False,'next':'Once desktop access is available, start a new explicit-ISO baseline/candidate pair. Do not repeat black screenshots or CPU-stepping GPU downloads as acceptance evidence.'}
write('qa/runtime_observation_local_sr004.json',runtime)
note='''# 로컬 업스케일 진행

- 실제 로컬 GPU로 처리한 고유 원본은 **54종**입니다. 타이틀 1종과 전투 재질 53종이며, 같은 원본의 재추론은 중복으로 세지 않습니다.
- 전투 재질 **50종이 정적 검수 후보**입니다. 처리 후 보류된 원본은 BM019/BM036/BM056 3종이고, 전투 중복 제거 목록에서 미처리 원본은 230종입니다.
- 이번에는 구름·나무 2종에 로컬 RGB/알파 추론 24회를 실행해 8개 조건을 비교했습니다. 구름은 각진 얼룩, 나무는 광택을 줄였습니다.
- 대각선 표식은 원본에서 선의 경계를 측정해 복원하고 기존 로컬 추론 RGB를 사용했습니다. 이 후처리를 새 AI 추론으로 세지 않습니다.
- 새 결과 12개는 원본·출력 해시, 크기, 투명도 또는 구역별 보호 조건을 확인했습니다. 밝고 어두운 배경과 2배 축소 표시도 직접 보았습니다.
- 검수 게임은 ISO 경로를 직접 지정해 실행했습니다. 화면 캡처가 검게 나왔고, 창 표시 요청에 Windows 접근 거부가 발생했습니다. 실제 게임 적용·표시 검증은 미완료입니다. 별도 검수 프로세스를 종료하고 검수 경로 설정을 복구했습니다.
- 시험 팩의 정확한 관측 키는 2개입니다. 새 후보의 키를 추측해 넣지 않았고 사용자 게임에 설치하지 않았습니다.
- 전체 지역 1~6/EX·진엔딩, 적·오브젝트·이펙트·컷신, 미관측 해시, 한글 폰트·조준 고정 표시 검증, 최종 설치·제거 ZIP은 남아 있습니다.
'''
(C/'outputs/로컬_업스케일_진행.md').write_text(note,'utf8')
progress=R/'PROGRESS.md';body=progress.read_text('utf8');marker='## 2026-09-23 — LOCAL-SR-004: 구름·나무·직선 재작업 / 화면 접근 진단'
if marker not in body:
    body+='\n\n'+marker+'''

- 직전 설명 응답은 기존 Fate 실행 기록을 확인한 정정으로 제작 진척은 없었다. 이번 턴은 새 추론·검수·후보 승격 및 실제 화면 접근 오류의 분리로 progress. 전체 목표 active, 완료/blocked 아님.
- 사용자 지시대로 모든 에뮬 실행은 고정 exe+ISO CLI. Start-Title-QA에 명시 세션명/검수창 표시/백엔드 선택, 시작 실패시 경로 복구 추가. Stop은 세션명 제한과 기존 exe/PID/UTC 생성시각 검사 유지.
- Q005(Vulkan)/Q006(D3D11)는 반환된 정확 QA 창을 읽었지만 검정/암전 캡처. Q005 game.status는 NPUH10126 v1.01, original GE100레코드/5텍스처/18draw의 INFORMATION 화면이며 title 소비 증거 아님. Q005 guest Start2프레임 1회 응답·해제 확인. 키보드/마우스 주입 없음.
- Q007은 사용자의 ‘CU로 실행하지 말고 ISO로 실행’ 지시를 유지한 별도 CLI 실행 후 반환된 창의 표시/활성화를 시도. GetCursorPos access denied0x80070005로 실패. 이전 Esc를 영구적 검수 금지로 해석하지 않았으나, 현재 Windows 접근 오류 뒤 UI 입력 중단. 잠금 여부는 미확정, 비동기 확인 질문 중. user desktop/계정/보안 설정 조작 없음. Q005/006/007은 각각 정확 PID+생성시각 확인 후 종료, QA routing 복구. qa/runtime_observation_local_sr004.json.
- emucap bootstrap/launch_plan: PSP 기능은 있으나 headless adapter binary 미설치, bridge는 존재. 별도 managed game launch 없음. 기존 도구의 지원 부족을 로컬 모델 부재와 혼동하지 않음.
- BM027/BM057: premultiplied RGBA Gaussian 사전 필터 → 로컬 WDN/photo RGB+alpha 추론, 조건8개/실제24pass. tree는 x=48 경계로 foliage/bark 분리. 원본 평균 opacity/가중 RGB 평균 복원 및 원본 완전 투명/불투명 범위 제약. qa/local_sr_soft_alpha_v3.json.
- Cloud BM027 photo sigma1.0은 각진 덩어리 감소, source alpha mass0.99923. 다른 후보의 각짐/과도한 흐림 확인 후 어두운/밝은 matte와2배 표시 검수해 후보로 승격. 원래 투명 블렌딩 방식/게임 소비는 미확인.
- Tree BM057 photo sigma0.4 foliage의 고주파 RGB잔차60%로 광택 완화, 기존 WDN의 bark x>=384와 합성. alpha 및 각각의 atlas 구역이 부모 파일과 정확 일치. 35%는 지나치게 부드러워 미채택. 새 추론과 후처리/합성을 구분. bark가 식물의 같은 소비자라는 주장 없음.
- BM039은 source alpha>=128 연결 띠6개의 관측 좌우 경계에 직선 적합. 전부 잘린 가장자리2개는 보이는 경계+다른띠의 중앙 폭으로 바깥쪽을 추정했다는 기록 유지. 최대 잔차1.2975원본픽셀, source mask IoU0.9597. 원본 바이트 동일 형태라는 주장 금지. 기존 실제 neural RGB+분석적 alpha를 결합, 새 AI추론0. 정적 비교에서 휘어진 가장자리 개선, 반복 경계/소비UV는 미검증.
- 출력12개와 native/input/parent 파일 SHA, 8배 크기, 투명도 또는 명시 geometry 예외, tree 영역 동일성 검증. qa/local_sr_soft_review_v4.json. 2배 검수표 하단 잘림은 높이1300으로 수정.
- 고유 원본 누계54 유지; battle static candidates47→50, 처리 후 보류3(BM019/BM036/BM056), battle미처리230. title+BM023 exact2key reviewpack unchanged; 새 후보 관측키 없음/사용자 설치 없음/최종ZIP 없음. 이전 finalize_stage01_sr.py가 최신 후보를47개로 되돌리지 않도록 역사적 빌더 재실행 차단.
- C outputs/로컬_업스케일_구름_나무_표식_재작업.png, 로컬_업스케일_투명도_검수.png, 로컬_업스케일_진행.md. 화면 접근 오류 때문에 Explorer 표시 대신 Codex 파일 미리보기.
- 다음: 화면 접근 가능시 새 baseline/candidate를 ISO로 직접 실행하고 title/Orbit v4/LOCK ON 실제 비교. 대기 중에도 BM019/036의 작은 표식 보호, BM056 창문 구획 대조, 미처리 BM006/022/024/030/041 및2~6지역·FLD/적/이펙트/컷신 작업 지속. 6개 flag5 특수높이 디코드와 전체 경로 인벤토리, 최종ZIP 미완료.
'''
progress.write_text(body,'utf8')
print(json.dumps({'runtime_sessions_closed':len(sessions),'proof_images':proof,'static_candidates':summary['battle_static_candidates'],'selected_checks':len(sr['checked_outputs'])}))
