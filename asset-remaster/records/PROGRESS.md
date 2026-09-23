# 진행 기록

## 2026-09-22 — 독립 작업 초기화 / 조사 진행

- 작업 폴더: P:\AI\Codex\projects\black-rock-shooter-hd-ui-fonts
- 부모 프로젝트 및 실행 중 사용자 게임 변경 없음. 부모 기록은 workspace/source/parent_records에 읽기 전용 기준 사본으로 수집.
- 고정 ISO SHA-256 직접 일치. SYSTEM.VOL에서 XOR55 복호화한 font.lpk 및 ucs2jis.bin이 지정 v1.0.1 font_final과 바이트 완전 일치.
- 폰트: 15×15/4bpp, 3354개 슬롯, 한국어 주입 919글자. 동적 128×128/256×128 캐시를 덤프에서 식별 중.
- 기존 27 UI는 기존 제작물이며 새 HD 제작이나 현재 판본 검증 완료로 계산하지 않음.

| 안정 ID | 범위 | 상태 |
|---|---|---|
| FONT-KO-919 | 기존 한국어 글리프의 벡터 기반 8배 재렌더링 | 소스·룩업 확인, 제작 전 |
| FONT-CACHE | 실제 캐시의 글리프 슬롯 재구성 및 정확한 xxh64 매핑 | 분석 중 |
| UI-00..26 | 기존 메뉴/시스템 UI 재검증 | 대기 |
| HUD-EXT | 아이콘·전투 HUD 추가 제작 | 대기 |
| WORLD/ENEMY/FX/CUT | 배경·오브젝트·적·이펙트·컷신 | 미착수 |

다음 단계: 글리프 셀과 캐시 픽셀을 전수 대조 → 위치를 유지한 재렌더링 → 별도 세션 및 시험 팩 → GPU 소비와 전후 화면 검증.
최신 제한: Debug Stats가 꺼진 replacer 0은 미적용 증거가 아님. GE 정지 후 읽기, 끝나면 Resume. 부모 부스터 텍스처의 적용 증거를 이 작업에 전용하지 않음.

## 2026-09-22 — 첫 폰트 제작 묶음 / 사용자 Esc 중단 체크포인트

### 완료
- FONT-KO-919: 기존 한국어 919글자 모두 14px 재렌더링 결과가 고정 ISO의 4bpp 글리프와 바이트 완전 일치. 같은 글꼴을 112px로 다시 래스터화한 8배 원본 아틀라스 제작.
- FONT-CACHE: 현재 판본 세션에서 관측한 정확한 xxh64 캐시 454개를 8배로 재구성. 원본 셀과 RGBA 완전 일치한 글리프만 교체. 실제 포함된 한국어 글리프는 415종이며 전체 919종 런타임 확인을 뜻하지 않음.
- 원본 보호 영역과 한 픽셀 셀 간격 보존, 글리프 클리핑, 해시 충돌 검사 통과. 거절 캐시 0.
- 산출물: outputs/korean_919_glyphs_8x.png, outputs/font_before_after.png, workspace/build/PSP/TEXTURES/NPUH10126/font/*.png, textures.ini.
- 상세 검증: qa/font_build.json, qa/source_identity.json. 재현 도구: tools/survey.py, tools/build_fonts.py.
- 별도 실행기와 복사 세이브, 무음 포트49321 세션 UIF-S001-baseline 준비. 게임 ID/판본 API 확인. 부모 게임에 대한 변경 없음.

### 미완료 및 중요한 품질 관찰
- 실제 GPU 교체·전후 게임 화면 확인 미실시. 현재 출력은 오프라인 후보이며 설치용 최종 ZIP 아님.
- 원래 Noto Sans KR 가변 폰트 기본 굵기는100(Thin). 14px 힌팅에 비해 112px 직접 렌더링 획이 얇아짐. 처음100글자 알파 면적 비율0.545. 기본 후보의 얇은 획을 완료 품질로 채택하지 않음.
- 굵기200/250/300/350/400 비교 프로브의 알파면적 비율0.697/0.775/0.849/1.149/1.279. 다음에는 300~330 광학 굵기를 전체919글자에서 비교하고 동일 원점·폭을 유지하며 읽기성을 결정할 것. 현재 파일은 weight100 초안 그대로 보존.
- 동적 캐시는 미관측 조합에서 원본 폰트로 돌아감. 광범위 와일드카드 금지. 454개를 전체 폰트 지원으로 표현하지 않음.
- 기존 UI27·HUD·아이콘·배경·적·오브젝트·이펙트·컷신 확장은 미착수.
- 사용자가 Windows Computer Use 도중 물리 Esc를 눌러 중단. 이후 UI 입력 중지. 탐색기 표시도 하지 않음.

### 다음 실행 단계
1. tools/build_fonts.py의 고해상도 글꼴 광학 굵기를 300~330 후보로 비교. 저해상도 기준 검증은 기존 weight100으로 유지. 샘플 시트 및 전체919글자 클리핑 재확인.
2. 독립 실행기 프로세스 상태를 다시 확인. 숨김으로 실행한 PID54152는 이 작업의 경로를 검사한 뒤 종료했음. sky.launch_app으로 표시 시도 중 Esc 중단이므로 새 인스턴스 존재 여부는 재확인 필요.
3. UIF-S001-baseline 복사 세이브를 별도 실행기에서 사용해 메뉴를 읽고 게임 프레임 확보. 사용자 게임은 변경하지 말 것.
4. 완성 후보를 새 독립 preview 세션에 복사 후 실제 GE 정지 위치에서 GPU 이미지 일치 및 알파·좌표·메뉴/대사 표시 확인. 반드시 GE Resume.
5. 기존UI27의 현재판본 정확한 RGBA 매핑을 전수 대조하고 미확인 광범위 와일드카드는 제외. 설치·제거 가능한 검증된 시험ZIP 제작.

## 사용자 정정 — 검증 경로 자체의 로딩 멈춤
- 사용자: "그게 게임이 로딩 안되고 멈춘 경로였어".
- 이전 Esc는 정상 게임 검증을 중지한 것으로 해석할 수 없음. 사용자가 설명한 해당 경로는 로딩 불가/멈춤 경로. game.status의 판본·paused=false는 정상 화면이나 진행의 증거가 아님.
- 첫 대응: 실패 세션UIF-S001 로그·빠른저장 보존. 새 UIF-S002에서 같은 ISO/설정의 새 부팅과 물려받은 state 재개를 분리 비교. 폰트/HD팩 미적용 기준 상태부터 검증.

## 최신 정정 및 직접 ISO 실행 완료
- 사용자 추가 설명: 게임 자체가 로딩 중 멈춘 것이 아니라 ISO 없이 에뮬레이터 파일 탐색 화면만 열렸던 것. 위 "로딩 불가/멈춤 경로" 해석은 철회한다.
- 원인: hidden 실행기의 화면 표시를 시도하며 sky.launch_app에 실행기 경로만 전달했다. 이는 ISO가 로드된 창을 보장하지 않으며 파일 탐색 초기 화면을 열었다.
- 사용자 지시: 컴퓨터 유즈로 열지 말고 게임 경로를 직접 지정해 실행.
- 컴퓨터 유즈 없이 실행 파일에 고정 ISO 절대경로와 --windowed를 전달해 직접 실행했다. 새 부팅이며 빠른 저장을 자동 불러오지 않음.
- 독립 UIF-S002-coldboot / PID67548 / port49321. API game.status=NPUH10126, version1.01, paused=false. OS 창 제목도 PPSSPP v1.20.4 - NPUH10126 : BLACK★ROCK SHOOTER THE GAME, Responding=True. 실제 게임 자산 덤프가 계속 생성됨. 단순 파일 탐색 화면과 구분되는 게임 로딩 확인.
- 증거: workspace/sessions/UIF-S002-coldboot/process.json, captures/direct-iso-launch.json, memstick/PSP/SYSTEM/DUMP/log.txt.
- 실행 중 프레임 API는 Neither CPU or GPU is stepping으로 거절되었으며 조작·일시정지하지 않음. 화면 검증은 별도 미완료.
- 재발 방지: tools/Launch-Game.ps1에 ISO/실행기 해시 확인과 ISO 직접 실행, 중복 실행 방지 구현.
- 이 실행은 텍스처 교체가 꺼진 기준 게임이다. HD 폰트/기존UI 적용 완료를 뜻하지 않는다. 현재 게임 조작·설정·오디오 변경 없이 유지.

## 2026-09-22 — 폰트 실제 화면 / UI 소비 좌표 재구성 / 조준 고정 수정

### 완료된 묶음
- FONT-KO-919 v2: 원본 919글자 재현 검사를 유지하며 8배 벡터 재렌더링 굵기를325로 조정. 원본 대비 통합 알파면적 비율1.000270. 919종 클리핑 없음. qa/font_weight_comparison.json.
- FONT-CACHE v2: 관측 캐시522개, 포함 한글415종. 출력 workspace/build-v2/PSP/TEXTURES/NPUH10126/font. 미관측 캐시·전체919글자 런타임 지원은 미완료.
- UIF-Q001 baseline vs UIF-Q002 preview: 같은 ISO와 복사 state(e993964c...)를 CLI로 직접 실행. 컴퓨터 유즈로 실행하지 않음. 전투 결과의 리페어 200/500에서 한국어 폰트 변화가 보임. outputs/font_runtime_before_after.png / qa/font_runtime_comparison.json.
- GE frame record에서 원본 font cache RGBA가 정확히 00000000851096b0aaf18fc7(source SHA ffc975489d213434893455f497e92e0016159d5cf0b4ef4442e82820a8ca6460)와 일치. 이 캐시를 소비하는4개 draw 기록 확보. workspace/ge/battle-results/ui_consumers.json. 높은 해상도 GPU texture 자체를 바이트 대조했다는 뜻은 아님.
- plus 아이콘과 수량 표시는 스크린샷 ROI 픽셀 동일. 숫자 글리프는 원본 모양을 유지하나 교체 텍스처의 샘플링 변화로 화면 픽셀 차이가 있음. 모든 비한글 글자를 고화질화했다는 주장은 금지.
- 별도 QA 실행은 종료된 상태이며 기록 마지막은 Vulkan shader/pipeline 저장. 종료 원인은 추정하지 않음. 사용자 실행기 PID67548은 별도 유지 확인. 사용자의 파일 탐색 초기 화면 문제는 ISO CLI 실행으로 해결된 별개 사안임.

### UI v3
- 기존 UI27의19개 자산은 현재 ISO 관측값에 대응(17개 정확한 해시). 나머지 UI-00/12/13/21/22/23/24/26 런타임 해시 미확보. 현재 후보는 배포 대상 아님.
- 고정 ISO의 관련10개 UI 컨테이너에서 PTMD120개, SDO16개, 표시 기록1070개를 추출. qa/ui_consumers_static.json. 전체 게임 UI 모집단은 아직 아니며 다른 컨테이너 확장 필요.
- 기존 이미지의 넓은 사각형을 지우는 방식이 실제 UV와 달랐음. SDO display list를 해석해 분할 제목과 회전 문구의 실제 source UV 및 화면 위치를 재구성.
- 수정 안정 ID: UI-02/04/06/07/09/10/11/14/17/18/22 (11개). workspace/ui_candidates_v3 및 workspace/build-v3/PSP/TEXTURES/NPUH10126/ui, qa/ui_build_v3.json.
- CUSTOMIZE와 OPTIONS 제목을 각각의 글자 슬롯에 분할 재삽입. 중복 O와 겹치는 글자 좌표를 처리. INFORMATION은 실제 두 조각과1px 간격을 고려하여 임무/정보를 조립.
- UI-11/14의 세로 원문을 회전해 읽은 결과 USE / KEY ITEMS / EQUIP. 이전 초안의 MISC/ITEMS 해석을 폐기하고 사용 / 중요 아이템 / 장비로 교정. translator_model: Codex internal. 대사 재번역 없음.
- 사용자가 조준 고정 오류를 지적: LOCK ON 원문은 y297..301인데 첫 지우기 범위가 y301을 제외해 하단이 남았음. y303 exclusive까지 지워 수정, 오른쪽 삼각형과 실제 하단 테두리(y304)는 보존. 같은 경계 문제였던 임무 목록/회전 카테고리/SHOOT도 원본 픽셀 범위로 교정.
- 최종 후보 27개 클리핑·외부영역 RGBA 검사, 별도 지정한 아이콘/테두리32영역 원본 동일, 기존 글자9영역 완전 지우기 범위 검사 통과. 최종 비교표에서 잔여 글자 제거 및 조립 제목 가독성 직접 확인. UI 런타임 수용 검사는 아직 미완료.
- 증거: outputs/lock_on_before_after.png, outputs/ui_v3_geometry_proof.png, qa/ui_v3_protected_regions.json. 빌더 tools/build_ui_v3.py, ui_geometry_v3.py, review_ui_v3.py. v2 후보와 원본은 보존.

### 현재 미완료 / 다음 실행 단계
1. 원본 SDO의 no-UV 형식0x19c(357개),0x180(1개)는 텍스처 없는 도형이다. extract_ui_consumers.py에서 분류 코드를 반영했으나 기존 보고서의358개 unresolved 표시를 갱신해야 함. 소비 좌표 없는 텍스처로 간주하지 말 것.
2. 남은 UI16개 초안에도 분할/반복/회전 소비 오류가 있을 수 있음. SDO에 맞춰 UI-00/01/03/05/08/12/13/15/16/19/20/21/23/24/25/26을 검토. UI9/18 방식으로 조립 검증. 현재 UI22 해시가 없으므로 화면 수정 완료로 보고하지 말 것.
3. 관련120개 텍스처 및 다른 메뉴·시스템 컨테이너로 인벤토리 확장. 본격 HUD/아이콘/배경/적/오브젝트/이펙트/컷신 제작과 지역1~6/EX/진엔딩 소비 확인 미완료. 주인공 PGR/연결 텍스처는 부모 작업 제외 범위를 유지.
4. 실제 화면 QA 시 항상 직접 ISO 경로를 전달. 사용자 게임을 재시작/조작하지 않고 별도 검증 대상만 사용. CPU stepping GPU 다운로드는 동일한 Could not download output 실패이므로 반복하지 말고 GE 정지 또는 다른 검증 경로를 마련. gpu.record.dump는 실행 중 기록 확보 성공.
5. 충분한 런타임·상태변형 검증 후 설치/제거 가능한 시험 ZIP 작성. 최종 ZIP 아직 없음. 전체4K 목표 active 유지.

## 2026-09-22 — UI v3 독립 검토 / 원시 연결값 도출

- 읽기 전용 검토자가 확인한 UI-06 헤더 바탕 (10,7,5,255), 글자 (229,229,229,255), EXIT 글자 (78,78,78,252)를 복구. UI-09 소비 셀 사이 원문 그림자20픽셀도 별도 지우기 범위로 제거.
- tools/ui_geometry_v3.py, review_ui_v3.py에 반영. 전체27개 후보 재빌드, 보호32영역 동일성, 측정된 원문/그림자12영역 지우기, UI06 색상 및 UI09 gutter 투명성 검사 통과. 전체11자산의 모든 잔여를 자동 검증했다는 뜻은 아님. 최종 증명 시트 직접 확인.
- extract_ui_consumers.py 보고서 갱신:10컨테이너/PTMD120/SDO16/1070표시기록, 미지원0. 기존358건은 no-UV 도형으로 분류됨.
- UI22 LOCK ON 하단 잔여가 제거되고 테두리/삼각형/사격 버튼은 동일함을 독립 확인. 단, SDO멤버7의 record20은 SHOOT,25는 □이며 LOCK ON UV영역(y294..305)의 소비 기록은 두 SDO에서 발견되지 않음. 동적 소비/별도 경로 확인 필요. 런타임 완료 주장 금지.
- 현재 사용자 게임 PID67548은 ISO 인수가 명시된 채 실행 중. game.status에서 NPUH10126 v1.01/paused=false 확인. 상태/입력/설정 변경 없음, 추가 에뮬 실행 없음.
- 새 tools/probe_ui_raw_hashes.py는 고정 ISO LPK 안의 PTMD+16 주소부터 power-of-two 높이까지 연속된 원시 바이트를 PPSSPP1.20.4 방식(xx h64 seedBACD7814 하위32비트)으로 해시. 18자산/18매핑/15고유키가 관측값과 일치. 이18매핑의 전체 RGBA도 실제 덤프와 동일(패딩 포함). 팔레트로 계산한 하위 캐시키27개도 기존값과 일치. qa/ui_raw_hash_probe.json.
- UI18만 전체 높이 범위가 LPK 밖을 넘음: 두 관측 키의 가변 패딩을 추측하지 말 것. 기존 관측 기반 빌드 유지.
- UI22 전체높이512 조건의 도출 키:000000009881822fdf95c383. workspace/ui22-static-review/{textures.ini,ui22.png,original-full.png,README.txt}에 독립 시험본 준비. 원본의 연속 바이트 패딩을 복원하고 논리영역에 v3글자 수정 적용. 미설치/미관측이며 최대V에 따른 축소해시 경우를 지원한다고 주장하지 않음.
- 새 도출키를 실제 관측 매핑(19자산/17고유키)에 섞지 않았음. 기존 build-v3의 미관측 UI8개 상태 유지. 최초 실제 UI22 소비 장면에서 원본 전체 RGBA·키·좌표를 대조한 후에만 정식 바인딩으로 승격할 것.
- 다음 단계: UI22 실제 소비 경로/장면 확인, 나머지 legacy UI16개의 SDO와 문자·아이콘 경계 검토. 전체4K 목표의 배경/적/오브젝트/이펙트/컷신/지역1~6·EX·진엔딩 범위는 여전히 미완료. 활성 목표 유지.


## 2026-09-22 — 남은 UI 배치 / 원본 디자인 계승 폰트 후보 v4

### UI v3 추가 완료
- 14개 추가 자산의 원문·실제 SDO 표시 좌표를 수정. 총25개 자산 geometry 수정, UI05/08은 검토 후 기존 위치 유지. 전체27개 후보 클리핑·수정 영역 밖 RGBA 검사 통과.
- 추가14개에서 보호52영역·원문 잉크50영역 검증 통과. 앞선32/12와 합쳐 지정 보호84영역, 측정 원문62영역. 아이템 제목의 E/M 사이 (43,112) 그림자1픽셀까지 제거. 독립 읽기 검토에서 추가 확정 결함 없음.
- 주요 교정: 스테이지3/4 순서·후지수해/샌프란시스코 전체 이름, 갤러리 slash 페이지 구분자·화살표, 아이템 분할 제목, UI19의 잘못된 DMG_RANK 해석(실제로 OK/__ /R/HP/%), 정보 회전 방향, 임무 결과 원형 테두리, BEGIN MISSION 전체 문구 소비. 대사 재번역 없음. translator_model: Codex internal.
- UI13 갤러리 제목은 반복되는 L 슬롯을 비워 원래 제목 영역 오른쪽에 배치. 원래 시작점과 동일하다는 주장은 금지. 동적 등장 애니메이션 확인 필요.
- 결과: qa/ui_remaining_review.json, outputs/ui_menu_geometry_final.png, ui_hud_geometry_final.png.

### 사용자 새 지시 및 v4 글꼴 후보
- 사용자: "한글 폰트도 가능하면 원본의 디자인을 계승한걸로 만들어". 원본의 직선·대각선 획과 일정한 획 굵기를 참고. 기존 Noto의 곡선형 한글을 그대로 확대하는 방향에서 수정.
- 식별된 established font Orbit Regular (Sooun Cho, JAMO), upstream commit 95122395c6d1fda07aebdf36f566a75678bc3bdd, SHA256 5d0206fb0a9e3eeac51aff8d4a6dbb7613d63fc435f1a51f96dc35cefb5f9f87, SIL OFL1.1. 입력 font와 LICENSE는 workspace/source/font/orbit에 보존. Gugi는 비교만 했으며 단절된 획·둥근 단말이 원본과 덜 어울려 빌드에 사용하지 않음.
- 실제 원작 글꼴의 한글 확장판이라는 주장은 하지 않음. Orbit의 기존 글자꼴에 재현 가능한 렌더링·자간·굵기 설정을 적용한 디자인 계승 후보. 새로운 TTF를 만들거나 OS에 설치하지 않았음.
- UI: 원래 소비 좌표·색상·회전·분할 조립을 그대로 유지. 공간 문자만0.45em, 작은 UI에서 사각 MaxFilter radius round(size*0.015) 적용. 각 문구의 문자표 지원·잉크 경계 확인. UI19 라틴 상태 약어는 원본 픽셀 유지로 되돌림(고화질 신규 영문 제작 주장 금지).
- v4 UI27개 제작, geometry 수정24개/유지 검토3개(05/08/19), 관측19개 자산/정확17키 유지. 81개 지정 보호영역(기존UI19 네 구역 대신 아틀라스 전체 한 구역 검사), 측정 원문59영역 모두 통과. 27개 후보 수정 범위 밖 RGBA·클리핑 검사 통과.
- 본문: 같은919개 기존 글리프 매핑과15x15셀, 16px 캐시 간격 유지. 8배112px 렌더링 원점(8,-33), 획 보강 없음. 초기1픽셀 보강판은 통합 알파면적1.505배로 과해 폐기; 현재 무보강판은1.164795배. 이는 가독성·미감 승인 수치가 아님.
- 본문 후보919종 클리핑 없음. 기존 확인522캐시만 정확히 재구성, 포함 한글415종. 캐시의 비한글·숫자·문장부호·오른쪽/하단 간격은 원본 nearest 확대와 RGBA 동일. 미관측 캐시는 원본으로 돌아감. 전체919종 런타임 소비 증거는 아직 없음.
- 통합 후보: workspace/build-v4/PSP/TEXTURES/NPUH10126 (폰트522키 + UI17키). 별도 설치·실행 안 함. UI22 등 미관측8개 자산은 정식 매핑에 추가하지 않음. 기존 ui22-static-review는 v3 실험본이며 v4폰트 적용본으로 혼동하지 말 것.
- 제작 코드: tools/font_heritage.py, prepare_heritage_build.py, build_ui_v4.py, build_fonts_v4.py, preview_heritage.py. qa/font_build_v4.json, ui_build_v4.json, ui_v4_protected_regions.json, ui_remaining_review_v4.json. 비교: outputs/font_heritage_design.png, font_heritage_body.png, lock_on_heritage.png.
- v4의 UI와 본문 모두 실제 게임 화면 검증 전. 이전 Noto v2의 리페어 결과 화면 적용 증거는 Orbit에 승계하지 않음. 본문 비교표는 설명용 고정 격자 한글 조립이며 원본 게임 대사·문장부호 전체 표시 증명이 아님.

### 현재 실행·조율 및 다음 단계
- 부모 작업이 독립 PPSSPPModelPort/port49219로 UI 검증 중이라는 메시지를 받음. 이 작업은 입력을 보내지 않음. 사용자 창을 새로 열거나 다시 시작하지 않았음.
- 사용자 게임 진행 화면에서 로드로 가는 방법 질문: Esc로PPSSPP메뉴, 빠른 저장은Load state, 게임 내 저장은타이틀의불러오기 경로로 안내. 실제 로드/재시작은 실행하지 않음.
- 다음: 최종 v4독립 캐시 검토 결과 기록 → 입력 조율 후 별도 QA에서 직접 ISO+복사state CLI 실행으로 새 글꼴 가독성·동적 제목 소비 확인. 컴퓨터 유즈로 에뮬을 실행하지 말라는 사용자 지시 유지.
- 전체4K 활성 목표 계속. 27개/관련10컨테이너는 전체 게임의UI 인벤토리가 아님. if_rsdsys(전투 결과) 등 추가 UI, 배경/오브젝트/적/이펙트/컷신 및 지역1~6/EX/진엔딩 소비 검증은 남음. 부모 PGR/모델/주인공 연결 텍스처 범위 제외 유지. 최종 배포ZIP 없음.


### v4 최종 독립 읽기 검토 결과
- /root/review_ui_v3: UI27개 파일 해시, 보호81영역 RGBA 일치. 폰트522캐시 파일/RGBA 해시와 한글30,964셀, 비한글·간격의 원본 보존 확인. 919글자 아틀라스 셀 해시·대응·클리핑 일치, 관측415종. 최종 Orbit본문 무보강/알파1.164795 확인. 추가 확정 결함 없음.
- 이것은 정적 검증이며 UI22 동적 LOCK ON 소비, 미관측캐시, 실제게임최종표시 증거를 추가하지 않음.
- 부모 작업은 이후 Esc로 Windows 입력을 중단한 상태임을 확인. 이 작업도 별도 Windows 입력/게임 재시작 없이 비교파일만 Codex 패널에 표시 요청(queued). 탐색기 창은 새로 열지 않음.
- 사용자용 사본은 C 작업 폴더 outputs의 원본디자인_한글폰트_비교.png, 대사용_한글폰트_비교.png, 메뉴_UI_수정비교.png, 전투_UI_수정비교.png, 조준고정_수정비교.png.


## 2026-09-23 — LOCAL-SR-001: 실제 로컬 추론 및 재작업

- 최신 사용자 지시: 로컬 업스케일 → Codex 품질 검수 → 미달이면 재작업. 로컬로 해결하기 어렵다고 확인된 경우 GPT 협력도 허용. 이 배치에서는 모든 이미지 추론을 로컬 GPU에서 실행했다.
- 앞선 설명 정정: v4의 한글은 고해상도 재렌더링이지만 비문자 원본 영역은 nearest 8배 보존이었다. 이를 AI 업스케일 완료로 계산하지 않는다. 외부 imagegen 타이틀1672×941 시안은 미채택·미설치, 실제4K 완료가 아니다.
- Forge/models에 파일이 없다는 관찰로 전체 로컬 모델 부재를 단정한 것은 오류. Fate/EXTRA 프로젝트의 공식 RealESRGAN_x4plus_anime_6B.pth를 발견하여 해시 f872d837d3c90ed2e05227bed711af5671a6fd1c9f7d7e91c911a61f155e99da 검증, 읽기 전용 재사용. RTX5080 / torch2.7.0+cu128 / spandrel0.3.4 / FP32 RGB. Fate 프로젝트는 변경하지 않았다.
- 이전 사용량 한도 승인 검사 실패는 이번 실행에서 재현되지 않았다. 허용된 P 프로젝트 쓰기로 실제 산출물을 생성했다. 미실행 계획을 추론 성공으로 기록하지 않음.

### 완료한 실제 추론과 품질 판정
- 타이틀 원본 /000:480×272 활성 영역을 anime6B로 실제4배 추론 후 Lanczos2배(3840×2176). 첫 결과는 표면 무늬 소실·리벳 하이라이트 과장으로 미채택. qa/local_sr_title_trial_v1.json.
- 재작업5조건: general DNI0/0.5/1, photo-x4plus, anime6B 노출전처리. 필요한 비교모델은 공식 release에서 프로젝트 workspace/local-sr/models로 다운로드, 출처·크기·SHA256·LICENSE 기록. 첫6B까지 총6조건 모두 실제 로컬 추론이다.
- general-dn0.0(weak denoise)을 게임 검수 후보로 선택. 독립 읽기 검토도 같은 판단. 미세결에는 팔레트 디더링의 재해석이 섞였을 수 있으며 최종 품질·런타임 통과 아님. qa/local_sr_title_models_v2.json.
- 관측키0000000086ba34d7c28b381c에만 연결한 별도 title-review-pack 준비. 실제 관측512×512의 패딩·전체알파·활성영역밖 픽셀은 nearest 기준과 완전 일치. 출력4096×4096. 원래 가로선y192, 세로 어두운 띠 유지. qa/local_sr_title_stage.json. 설치/게임 실행 없음.
- 첫 전투맵의6종(001흙/002도로/008아치창/009건물외벽/017잔해/018무너진건물)을 general-WDN 및 anime6B 두 모델로 처리한12후보. 일반모델이 표면결·형상을 더 유지, anime6B는 평탄화/만화적 단순화로 미선택. /018어두운 자국의 의미 미확정. STOP문구005와 알파자산은 이 비교에서만 보류, 전체범위에서 제외하지 않는다. qa/local_sr_battle_material_trial.json.
- 실제 로컬 처리 원본은 총7종(타이틀1+전투재질6). neural4배 후Lanczos2배이며 native8배AI·전게임4K 완료 주장은 금지. 후보들의 SHA/PNG검증 완료: qa/local_sr_batch_verification.json.

### 추출·연결 및 기존 보고서 보충
- UI 확장443이미지(439PTMD+4PNG),84루트,39SDO를 추출/원본바이트 roundtrip 확인. qa/ui_inventory_expanded.json. 이는 전체 게임 모집단이 아니다. 기존439PTMD의 RGBA·roundtrip은 새 디코더로 재검사 통과.
- tools/link_expanded_ui.py 실행:6832관측키 스캔,152논리자산의 일치 후보. 단색·작은 조각은 수천 개 키와 일치하므로 이 수치를 소비자 식별 완료나 정식매핑 수로 쓰지 않는다. title배경은 고유 일치. qa/ui_expanded_links.json.
- 부모 rgba hash는 SHA256(big-endian w,h+RGBA), 이 프로젝트는 SHA256(RGBA), 크기별도. 기존 같은키 해시 차이는 이 계약 차이이며 이미지충돌의 증거가 아니었다.
- 전투맵 BTL/MAP24루트,STCM44컨테이너의 텍스처 테이블416항목 확보.410디코드,6개는 flag5/높이1·4 특수형식으로 미해결. 헤더6..7을 텍스처수 일부로 잘못 해석하지 않으며 보존. 텍스처0개 컨테이너도 유효하게 집계. qa/battle_map_inventory.json.
- RGB565/RGBA5551 indexed palette코드0/16 지원을 추가하여 palette·인덱스·swizzle bytes의 exact roundtrip 확인. 실제 전체픽셀 관측 연결은 30개. 새 색상형식 runtime일치 근거는 qa/battle_map_runtime_links.json의 matched_format_counts 참조.

### 다음 실행 단계 / 전체 범위 유지
1. 타이틀 general-WDN 후보의 실제게임 합성·축소/움직임·리벳 밝기 검증. 사용자 게임에 입력하지 않으며 에뮬 실행 시 항상 exe+고정ISO CLI. 컴퓨터 유즈로 실행하지 않는다.
2. 전투재질6종 독립 검수 결과 기록, 반복 경계·UV·알파/조각별 소비 확인 후 배치 확대. 조각 아틀라스·문자·알파전용 효과는 구역/소비구조에 맞춰 별도 처리.
3. STCM flag5 미해결6항목을 원본·관측덤프·엔진 소비로 해석, 미지원으로 영구 제외하지 않음. FLD/오브젝트/적/이펙트/컷신 추출 확대, 주인공PGR/연결모델은 부모 소유 제외 유지.
4. Orbit본문·UI v4 실제게임 검수, 조준고정 UI22 실제 소비, 미관측캐시, 지역1~6/EX/진엔딩 커버리지, 설치/제거 가능한 최종ZIP 모두 남음. 전체 목표 active.


### LOCAL-SR-001 독립 전투재질 검토 반영
- 002도로/008아치창/009외벽: general-WDN 정적 후보. 001흙/017잔해: 미세 요철·섬유 모양 과장과 차가운 색으로 재작업 필요. 018: 원본[45,54,85,82)의 어두운 표식이 글자인지 손상인지 미확정하여 채택보류.
- 이전 6종을 모두 nontext로 표현한 manifest를 정정. 비교6종 중5종만 식별된 글자 없음,018은 ambiguous로 유지. 이 결과를 전체배경 승인이나 게임/UV 통과로 쓰지 않는다. 다음 GPU 작업은001/017의 중간 노이즈 강도 및 보수적 복원 비교부터.


## 2026-09-23 — LOCAL-SR-002: 흙·잔해 중간 강도 재작업 검토

- 원본 tex001/017 각각 DNI0.25/0.5/0.75 총6조건 실제 RTX5080 FP32 추론. native4배 후 원본 평균RGB 오프셋을 명시 적용하고 Lanczos2배 출력. 보정 전 neural4x 파일도 보존. tools/rework_battle_materials.py, qa/local_sr_battle_material_rework_v2.json.
- Codex가 두 비교표를 직접 검수. 두 자산 모두0.5를 게임 검수 후보로 선택:0.25의 과한 세밀 요철을 줄이고0.75의 뭉개짐은 덜함. 질감은 모델의 추정이며 원본 고해상도 복원 확정이 아님. 색 평균·축소오차 수치를 품질 승인으로 쓰지 않음.
- 6개 후보의 원본RGBA 해시·출력파일 해시·8배 크기·불투명알파 확인. UV/반복/게임표시/배포 검증은 미완료. 실제 로컬 처리 고유 원본은 여전히7종; 재추론 조건을 새 원본 수로 더하지 않음.
- 사용자용 사본: C 작업폴더 outputs/로컬_업스케일_흙_재작업비교.png 및 로컬_업스케일_잔해_재작업비교.png. 원본과 SHA256 일치. 설치하지 않음.
- PPSSPP1.20.4 공식 GPUBufferSubscriber.cpp/Stepping.cpp 확인: 웹소켓 GPU버퍼 요청의 CPU 정지 조건만으로는 GE 정지 작업 실행을 보장하지 않음. 기존 CPU stepping Could not download output 경로는 반복하지 않음. 별도 QA를 ISO 명시 CLI로 실행하고 입력 없는 창 캡처 경로 검증을 진행.
- Fate/EXTRA qa/realesrgan-all.json 재확인: 로컬 anime6B, RTX5080,121개 파일, 모델 SHA256 일치. 앞선 로컬 모델 부재 발언은 Forge만 본 잘못된 단정이라는 정정 유지.
- 다음: 타이틀 실제 교체/합성 관측 → 전투재질 UV와 반복 소비 확인 → 처리 범위 확대. Orbit v4·LOCK ON·전체 지역/EX/진엔딩·최종ZIP 미완료, 목표 active.

### LOCAL-SR-002 별도 콜드부팅 관측
- UIF-Q003-title-baseline: 고정 ISO/PPSSPP 해시 확인 후 exe+ISO 명시 CLI, WindowStyle Hidden으로 시작. 사용자 저장파일/상태 복사 없음, 교체텍스처 꺼짐. PID31696 및 생성시각을 session.json에 기록.
- game.status에서 NPUH10126 v1.01, BLACK★ROCK SHOOTER THE GAME, paused=false 확인. 탐색기/게임목록 상태로 실행된 것이 아님.
- Computer Use는 list_windows/list_apps 읽기만 수행했고 해당 숨김 창을 반환하지 않았다. 클릭·키보드·포커스 이동·활성화 없음. 화면 캡처 증거는 미확보.
- 실행 중 gpu.record.dump 성공. 10,940바이트 v6 GE 원본 기록, 100레코드/18direct-UV draw/5텍스처/파싱오류0. workspace/ge/title-baseline 및 세션 captures 보존. 기존 UI27과 일치0, 타이틀배경 소비는 확인되지 않았다. 콜드부팅 안내 화면 가능성이 있으나 전체 합성화면 미관측으로 확정하지 않는다.
- raw GE의 원본 텍스처를 교체 GPU 최종표시 증거로 쓰지 않는다. 후보 Q004는 아직 시작하지 않음. 현재 baseline 프로세스는 기록된 exe/PID/생성시각 일치 후 종료했고 previous-installed.txt로 QA 경로 복구. 사용자 게임/세이브/설정 변경 없음.
- 종료 스크립트의 첫 생성시각 비교는 ConvertFrom-Json의 DateTime 변환으로 문자열 대조에 실패해 중단됨. 경로/명시ISO/정확한 UTC ticks를 재확인하고 날짜 비교를 ticks 기반으로 수정한 뒤 종료.
- 다음 실행: 부팅 안내 화면의 최종 프레임을 관측할 지원 경로 확보 후 명시적인 별도QA guest 입력으로 타이틀 도달, 후보와 비교. 숨김 창 목록 재시도나 CPU stepping GPU다운로드 실패를 반복하지 않는다.


## 2026-09-23 — LOCAL-SR-003: 1지역 재질47종 추가 처리와 재작업

- 이전 목표 턴은 progress: LOCAL-SR-002의 검수 판정·출력·별도ISO 실행 관측·종료 증거가 추가되어 다음 행동이 바뀌었다. 진행 불가 상태가 아님.
- 전투 원본410항목을 크기+RGBA SHA256으로283그룹(BM001..BM283)에 묶음. 1지역 고유58그룹의 원본 확대4페이지 직접 검토/분류. qa/battle_sr_catalog.json. 그룹은 동일 소비자/해시라는 뜻이 아님.
- 신규 불투명38그룹에 WDN/DNI0.5 실제 로컬 추론76후보, 비교10페이지 직접 검수. tools/batch_stage01_sr.py. BM036 작은 흰 표식은 문자 가능성을 발견해 보류로 정정, BM056 창 구획은 관련원본 대조 보류.
- BM003/004/005/028 도로의 밝은 입체 테두리를 발견. 원본 페인트 팔레트 마스크를 분리해 이웃 원본 RGB로 바탕을 준비하고 배경만 로컬 WDN으로 재추론. 선의 색·두께·위치는 원본8배와 RGBA 동일. 4재작업 후보 직접 확인. qa/local_sr_road_paint_rework_v2.json.
- 투명9그룹 실제 RGB/알파 추론18후보. 단색 균열3그룹은 RGB를 무의미하게 모델에 넣지 않고 색을 유지하며 알파를 추론. Bilinear-source 밖 완전투명/내부 완전불투명 보호. 모델만 쓴 균열은 약한 선 소실, 구름은 각진 덩어리, 나무는 과한 광택으로 미채택.
- 균열3그룹:35/50/65% neural alpha 혼합·원본 평균알파 복원9후처리. 새 GPU추론으로 세지 않음.35%가 약한 선을 더 유지하여 게임 검수 후보. source alpha>=16→축소alpha<8 잔여는BM007=3/BM055=1/BM058=0이며 완전보존 주장 금지. qa/local_sr_stage01_alpha_rework_v2.json.
- 구름/나무는 anime6B/photo 추가 RGB4조건 실제 로컬 재추론도 미채택. RGB모델 변경만으로는 해결되지 않음. 다음은 cloud 알파·RGB 공동 필터링/부드러운 밀도 보존, tree의 잎·줄기 영역별 질감 강도 재작업. BM039 대각선은 선형 기하를 재구성해야 함. GPT 협력 허용은 유지, 이번 배치 이미지 업로드 없음.
- 누계 실제 로컬 고유 원본54종(타이틀1+전투53), 이번 신규47종. 전투 정적후보47, 처리했으나 채택보류6, 전투그룹 미처리230. 전체게임 완료/전체4K 승인 아님.
- 출력115레코드의 원본RGBA·PNG해시·8배크기·보호알파/페인트 검사. qa/local_sr_stage01_verification.json은 이미지 직접검수 판정과 분리한다.
- stage01-review-pack은 관측 전체RGBA를 현파일로 재대조한 정확키와 기존 타이틀키, 총2키만 포함. qa/local_sr_stage01_review_pack.json. 미설치/런타임 미검증. 매핑 없는 후보를 와일드카드로 넣지 않음.
- C outputs: 로컬_업스케일_1지역_건물_검수.png, 로컬_업스케일_도로_재작업.png, 로컬_업스케일_균열_재작업.png, 로컬_업스케일_진행.md. Windows입력/에뮬실행 없음.
- 다음: 위 미달6그룹 및 미처리 문자/표식5그룹 계속재작업; 관측과 소비UV 확보 및 실제게임 비교; 2~6지역/EX·진엔딩, FLD·적·이펙트·컷신 범위 확장. PTMD flag5의6항목, Orbit v4/LOCK ON 소비, 최종 설치·제거ZIP 미완료. 전체 목표 active.


## 2026-09-23 — LOCAL-SR-004: 구름·나무·직선 재작업 / 화면 접근 진단

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


## 2026-09-23 — LOCAL-SR-005: 2지역 재질 / 원본 표식 보호 재작업

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


## 2026-09-23 — LOCAL-SR-006: 관측키21종 처리와 정확키16개 시험팩

- LOCAL-SR-005 직후 동일목표턴에서 의미있는 계속작업. 원본관측키가있는미처리21종 원본4페이지를 직접검토하고 WDN/photo 두모델42후보,실제86pass. BM130은4개32px높이띠,BM149는2개128px높이영역을분리추론. premultiplied RGB/alpha사전필터와35%neural/65%sourcebilinear알파혼합,원본평균opacity및가중RGB평균복원.
- 7개비교페이지전체직접검수. 선택14: WDN BM131/134/150/151/152/157/158/160/161/168,photo BM148/149/166/167. 투명선택7종은검정/밝은matte3페이지도확인. 이는게임의blend mode/alpha test/UV/반복경계승인이아님.
- 보류7: BM130절벽의지그재그홈,156나무의광택/평면적인가지,159노란무늬의과한색/세부,162~165잎의광택/관모양/덩어리화. 기존6보류와합쳐13. 초기양조건이실패한종은원본국소색상/질감강도와잎형상재작업대상,범위제외아님.
-42출력의원본전체RGBA/모델/input/native/output SHA,8배크기,투명0/불투명255support검사통과. sourcealpha>=16이축소alpha<8로사라진픽셀0은이특정임계검사만을뜻함. 모든원본형태동일/모든잔가지게임표시보존주장금지. qa/local_sr_observed_review_v1.json.
- 고유원본누계124(타이틀1+전투123),전투후보110,보류13,미처리160/283. 총게임분모아님. 이전96후보정확보존. 이번신규원본21,추론86회,후보14. session92111정상exit0.
- 관측원본전체RGBA와키를현재디스크파일로재검증하고선정14그룹을연결. 기존BM023+타이틀포함16exactkey/15battle그룹팩: workspace/local-sr/observed-review-pack-v1/PSP/TEXTURES/NPUH10126. ini xxh64/ignoreAddress true/reduceHash false,최종ini읽기및모든PNG목록/해시검증. qa/local_sr_observed_review_pack_v1.json. 미설치/교체런타임미검증/최종ZIP아님. Orbit/UI v4 별도. 기존stage01팩/Start-Title-QA의기본팩경로는유지되어새팩시험시명시적으로연결해야함.
- batch_stage02_opaque.py에005최종검수파일존재시분류쓰기전에중단하는보호추가. 새후보/문자분류가과거batch재실행으로훼손되지않게함.
- C outputs/로컬_업스케일_관측재질_검수.png와진행.md갱신. Windows접근오류미해결확인으로Explorer대신Codex미리보기,외부이미지전송/에뮬실행없음.
- 다음: 13보류의국소색/형상재작업(특히이미관측키가있는7종)및stage1/2미처리문자/알파,남은지역/자산확장. OS접근가능시새16key팩과Orbit/UI후보를구분해고정ISO CLI실행→실제로드/표시/알파·UV·상태전환증거. 전체목표active,완료/blocked아님.


## 2026-09-23 — LOCAL-SR-007: 보류 재작업 판정 및 관측키20개 시험팩

- 이전 목표턴은 progress: WDN7종 재작업28출력/실제10pass와 SwinIR10종20출력/실제26pass가 완료된 상태. 이번 계속작업에서 모든17개 비교표와 선택4종의 정확1배검정/2배밝은matte를 직접검수하고 판정을 확정했다. 고유원본은 추가하지 않았다.
- BM130/159/164/165 prefilter075-guided065를 게임검수 후보로 선정. 절벽 지그재그홈/잎 광택 완화, 원본색 가이드+neural residual. 원본알파 그대로가 아니라 이전WDN의35%neural/65%source-bilinear 알파에 byte-exact. BM156/162/163은 평면적인가지·돌질감·관모양잎 문제로 계속보류.
- SwinIR20조건은 dither테두리/반짝임/휘는창틀/평면무늬로 전부미채택. 공식모델001_classicalSR_DF2K_s64w8_SwinIR-M_x4.pth SHA4e78e33f22c1aa8a773db0cf4a7381bae97c2362c717f155439ebc690cbd9215, Apache2.0 출처/라이선스 models.json 유지.48출력의원본·모델·입력·native·부모·최종해시/8배크기/알파support 재검증. 실제36로컬pass; 후처리파생물을추가추론으로세지않는다.
- GPT BM162 1회는 외부builtin image_gen 편집이었다. 실제모델ID비공개. 1254×1254 출력,알파mass1.2924/IoU0.7711/원본빈영역침범33356픽셀 및 반복잎/빈틈손실로미채택. qa/gpt_bm162_trial_v1.json와workspace/gpt-trials/BM162-v1/prompt.txt. 전체작업을외부전송없음이라고표현하지않는다.
- catalog 후보110→114,보류13→9,고유원본누계124(전투123+타이틀1),미처리160/283. 기존110후보/기존시험팩16키파일정확보존. 전체원본RGBA/크기확인후4키추가한 observed-review-pack-v2는20키(19battle+title),미설치/실제교체표시미검증/최종ZIP아님. Orbit/UI는별도.
- 이전 scale_01의BM130두matte겹침과2배표기의축소상한을발견,검수근거에서대체. local_sr007_matte_BM130/159/164/165.png는정확1배와2배이며미리보기표시배율은뷰어에따름.
- 런타임Windows접근불가조건의외부변화증거없어검은화면캡처반복/사용자입력없음. 에뮬재실행없음. 다음: stage03/04미처리50종원본검토및처리,9보류와특수PTMD6건계속해결;OS접근가능시고정exe+ISO CLI로20key팩/Orbit/LOCKON표시검증. 전체지역1~6/EX/진엔딩·다른자산·최종ZIP미완료,목표active.


## 2026-09-23 — LOCAL-SR-008: 3·4지역 신규24종과 최신검수팩 실행준비

- stage03/04미처리50종의원본6페이지를모두직접검토. 불투명재질24종을WDN/dn0.5 두설정48actualpass. 6페이지비교후BM175/187격자변형확인→WDN사전필터0.5/photo/photo사전필터0.5 추가6actualpass,2페이지직접검수. 총24신규원본/54출력/54로컬추론,외부전송없음.
- 선택23: WDN BM129/133/144/169/170/173/174/176/178/179/181/182/185/188/190/191/194; dn0.5 BM177/180/184/186/192; filteredWDN BM187. BM175는WDN에서체커메시가굵은지그재그로변하고photo에서메시소실하여전조건보류. 후보는추정재질을포함하며원본HD복원확정/실제게임통과아님.
-54출력 원본RGBA·모델·native·입력·최종파일해시/4배native·8배출력/알파255검사통과. 기존114후보정확보존. 누계고유원본148(전투147+타이틀1),전투후보137/보류10/미처리136/283. source범위416항목410디코드6특수형식미해결. 게임전체분모아님.
-50원본전체분류: 다음26종에는얇은철골·분할폐허·효과알파·BM189큰문자/엠블럼·BM193평탄strip·BM199softdark등포함. 범위제외없음. qa/local_sr_stage0304_source_review.json에개별분류. BM189의문자미확정,의미번역없음.
-새24그룹은현재관측RGBA/key연결0이므로20key observed-review-pack-v2 변경없음. 새모델결과를추측키로설치하지않았다.
-Start-Title-QA.ps1의candidate기본을observed-review-pack-v2로변경,명시적v1/v2선택+VerifyOnly추가. INI/키별PNG/SHA/파일모집단검사와복사후재검사,메타데이터에검사결과기록. 이전script는tools/Start-Title-QA.before-sr008.ps1. 구문검사및VerifyOnly로exe/ISO/20PNG/INI일치통과,실제Start-Process경로는이번에실행하지않았음. qa/local_sr008_launch_preflight.json. Get-CimInstance/OS화면접근문제는별개이며해결주장없음.
-사용자진행.md와3·4지역검수.png갱신. 에뮬/사용자게임입력·설치없음. 다음은26투명/문자/효과및나머지지역,OS접근가능시고정exe+ISO CLI 실게임/20key팩/Orbit/LOCKON검증. 전체목표active;최종ZIP미완료.
- 최종 저장본 실행준비 스크립트의 VerifyOnly 재검사도 통과: 20키/20PNG, installed.txt 전후 SHA BFA2DF0ABDDF92B279798FCA47C545DCC73367CF5D06840075AA7741DA59C7DE 동일, 세션 디렉터리 모집단 불변, 에뮬 시작 없음. qa/local_sr008_launch_final_verification.json. 최종 3·4지역 비교표를 직접 확인함.


## 2026-09-23 — PTMD-SKY-001: 특수하늘3건의 정확한 원본 배열 확인

- 기존미해독6건을같은ISO의6832관측기록과크기별대조. 256×4의하늘T4 3항목은동일payload이며 linear/low-nibble-first 해석이관측키000000009c3edae9ca6a6a87의전체RGBA와정확히일치. block16×height해석은불일치. 가설이갈리는픽셀증거를확보했다.
- ptmd_expanded.decode에이payloadSHA f266ad36e0bf4af9b3f03ea6c96385aa8f384fa0db9c80e2b771a5a1bc5f0649만허용하는분기추가. flag5전체가linear라는규칙은미확정. 16×1의남은3건및변조된knownpayload는거부검사통과. 410battle+439UI 기존전체849항목의source/RGBA/roundtrip 회귀검사통과.
- 테이블416항목중410→413디코드,특수미해독6→3. 기존283그룹/후보내용정확보존하고고유색상띠BM284추가(미추론). battle_rgba/key연결30→33source항목;3개동일컨테이너각각의장면소비증거는아님. 284개는여전히전투맵고유분모이며게임전체분모아님.
- 원본PTM/ISO변경없고새decodedPNG3개만추가. qa/ptmd_special_sky_verification.json에관측원본경로/해시/대안가설/849검사내역. 이전decoder/3개인벤토리는qa/backups/special-sky-before. outputs/special_sky_layout.png.
- 하늘은짧은gradient/lookup일가능성이있어관측소비구조확인전새질감생성/자동교체하지않음. 새교체런타임/최종배포검증없음. 남은16×1색띠3항목의flag/배열소비는미해결.


## 2026-09-23 — LOCAL-SR-009: 3·4지역 투명재질24종 검수와 효과 재작업

- 24신규원본 WDN/photo 48출력, 실제114 RGB/alpha pass. 얇은 철골·폐허·격자와 soft effect를 분리하고, BM137/140/141/142는 보이는 구역별 추론. 원본 알파 bilinear와 neural을 혼합, 완전투명/불투명 경계와 평균 명암 보호. 구역 분할은 native UV 증거가 아님.
- 초기비교8페이지·5종재작업5페이지·matte8페이지와BM136상세2crop을 직접검수. BM139/146/172/195 filtered-guided 채택. BM196은 밝은matte에서초기WDN의갈라진무늬를확인해추가1RGB pass/3출력, 재작업비교와양배경확인후filtered-guided로변경. 초기matte-07의BM196은대체됨.
- 총66출력/실제120로컬pass. 22정적후보 선택: WDN BM136/137/140/141/142/143/153/154/155/183/199, photo BM132/135/138/171/197/198, filtered-guided BM139/146/172/195/196. BM145 작은검정·노랑그림의입체화와중앙chip변형, BM147 작은흑백엠블럼변형은보류. 의미나문구를추측하여채택하지않음.
- 모든원본PTM/RGBA·모델·입력·native·parent·출력SHA/8배크기검사. 분할별bilinear알파를재구성해기록과일치, 완전투명0/불투명255support확인. sourcealpha>=16→축소alpha<8 손실0은특정임계검사에한함. 재작업18출력알파는초기WDN과byte-exact이며원본과동일하다는뜻아님. qa/local_sr009_review.json.
- 기존137후보와BM284그룹·미해독3건보존. 전투171처리/159후보/12보류/113미처리,고유원본누계172(타이틀1포함),284는전투맵고유분모. 새24종관측키0이므로20키팩변경/설치없음. 전체목표active,런타임/최종ZIP미완료.
- BM189 원본과진단용대비표를검토: 왼쪽의반복된어두운표식과오른쪽뾰족한엠블럼형태이나정확한문구/역할미확정. 번역없음. 다음 BM189보호·BM193/BM284색띠소비확인,나머지지역·필드·적·효과·컷신범위확장및12보류재작업.
- 사용자Fate질문은모델파일SHA와qa/realesrgan-all.json 121레코드/RTX5080/native4x+Lanczos최종8x로확인. 로컬모델부재라는과거설명을정정. 이번009는외부업로드없음,에뮬실행없음. Windows화면접근문제외부변화증거없어검은창캡처반복안함.
- 사용자출력: 로컬_업스케일_투명재질_검수.png, 로컬_업스케일_효과_재작업.png, 로컬_업스케일_진행.md. GUI접근불가로파일미리보기사용.


## 2026-09-23 — LOCAL-SR-010: 5·6지역31종과 필드맵 형식 조사

- 이전 목표턴은 progress: LOCAL-SR-009 24신규원본/120pass/22후보 및 특수하늘3건의 정확한 해독을 반영했다. 이번 턴도 실제 신규추론과재작업/분류갱신을 완료하여 progress. 전체목표 active.
- 원본84종의10페이지전체직접검토. opaque31종 WDN/DNI0.5 62출력/70actualpass. BM256은4개눈에보이는구역, BM279는좌우2구역을격리. source partition은nativeUV증거아님. 나머지53종은사슬·가느다란골격·발광선·단색/별무리등으로분류,범위제외없음.
- 초기11페이지비교→BM233/254/255/256/268 과한메시·갈라짐·천질감발견,입력sigma.5/.8 WDN과photo.35 15추론출력/24actualpass 및source-guided5후처리,5재작업페이지검수.254/256 추가anime6B두설정4출력/10pass도검은해칭과굵은균열로미채택.총86결과/실제104로컬pass,외부업로드없음.
- 29후보: WDN BM201/202/209/210/211/226/227/236/237/239/240/244/251/253/279/281, DNI0.5 BM203/212/213/215/218/232/238/241/243/267, 재작업BM233-wdn08/BM255-wdn05/BM268-photo035. BM226 top/floor2crop도직접확인. BM254/256은각8조건모두보류,원본윤곽과재질을더보존하는재작업필요.
- 86출력의원본PTM/RGBA·모델·input/native/parent/output SHA,source분할완전성,4x/8x크기와opaque255검사통과. 기존159후보/BM284/미해독3항목보존. 전투202처리/188후보/14보류/82미처리,고유원본누계203(타이틀1포함). qa/local_sr010_review.json. 전체게임완료율아님.
- 신규31종관측키0,기존20키시험팩변경/설치없음. Windows화면접근오류외부변화증거없어에뮬재실행/검은화면반복없음. 런타임및최종ZIP미완료.
- 고정ISO를재해시하고FLD/MAP88개를읽기전용gzip검사,모두magic53431000(SC10)이며내부STCM/PTMD후보위치기록. qa/field_map_format_probe.json. magic스캔은텍스처테이블/소비증거가아니며새field텍스처승인없음. 다음SC헤더및STCM포인터테이블연결을해독한다.
- 출력 로컬_업스케일_5·6지역_검수.png/진행.md 갱신. GUI접근불가로Codex미리보기사용. 다음5·6지역잔여53알파/도형종·기존미처리/14보류·FLD/적/효과/컷신계속,실행은고정exe+ISO CLI 원칙유지.


## 2026-09-23 — LOCAL-SR-011: 5·6지역 투명재질42종과 필드맵 부분 추출

- 신규42종 WDN/photo 84출력/실제180 RGB·alpha pass. BM220/250/261은보이는두행을격리,soft4종과thin8종은neural-alpha20%,나머지35%와source-bilinear혼합. zero/255support·평균RGB/alpha보정. native4x+Lanczos2x이며nativeAI8x아님.
- 초기14페이지와matte14페이지·8개8x상세crop직접검토. BM262파편광택/BM264균열/BM277거친밀도에추가3RGB pass·9출력. BM221상세에서체크무늬가금속망으로변한것을확인해추가1pass·3출력,최종두배경/3x·8x검토.4종filtered-guided선택. 후처리8개는새추론으로세지않음. 총96출력/184실제pass/42정적후보. BM221초기matte04Photo는최종재작업으로대체.
- 모든원본PTM·RGBA/모델/input/native/parent/output SHA·4x/8x크기·분할coverage검증. 분할별bilinearalpha재구성일치,zero/solid영역보존,alpha>=16→축소<8손실0. 단일임계검사로전체형상/블렌딩보존주장안함. BM224Photo는원본max115에없는128threshold픽셀생성으로미채택,WDN선택. BM282/283 alphaIoU<1그대로기록. qa/local_sr011_review.json.
- 기존188후보/skyBM284/미해독3건보존. 전투244처리/230후보/14보류/40미처리,타이틀포함고유245. 새42종관측키0,기존20키시험팩바이트보존/미설치. 런타임·최종ZIP미완료,전체목표active. 에뮬실행/새외부업로드없음.
- FLD/MAP88gzip루트원본해시/SC·STCM포인터경계검사. SC363/STCM151개테이블검증,텍스처1630건중1616해독·roundtrip,576고유FM그룹.225그룹은BM크기+RGBA동일일뿐소비자/UV/키동일증거아님. 새필드HD처리0. qa/field_map_inventory.json.557 SC레코드에는실패194개가포함되므로557검증완료주장금지.
- field실패208건=SC분류/테이블194+PTMD14.14는128x4 flag4한건/16x1 flag5열세건. 미분류leaf808개. 194실패의bounded slice를원본88루트해시와재대조: firstoffset가정차88,미지원count79,lastoffset크기차22,SCMP서명겹침5. qa/field_map_sc_diagnostics.json. 첫offset52/56/60이지만SSCR은48부터인variant와zero/sparseoffsetvariant확인;단순header허용완화로강제추출안함.
- 사용자Fate질문: RealESRGAN_x4plus_anime_6B/RTX5080/121기록/native4x+Lanczos최종8x확인. 이전모델부재설명오류정정. Coutputs/로컬_업스케일_투명재질_재작업.png 및진행.md갱신. GUI접근불가로Codex미리보기사용.
- 다음: 남은BM40/보류14,field미지원variant해독과576원본분류·주인공연결제외대조,FLD/적/효과/컷신확장. 접근복구증거확보시고정exe+ISO CLI실게임title/Orbit/LOCK ON·지역검수.


### 체크판 디자인 보존 기준 강화 — 사용자 지적 반영
- 체크판은게임핵심디자인이며blur로왜곡을가리는것을채택하지않는다. BM221기존filtered-guided후보취소/원본파일보존,현재전투정적후보229/보류15. qa/checker_design_contract.json. BM175/200/201/209/221/226/244/269재검수대상.
- BM221원본핑크/그린614픽셀은정확RGBA보호층으로분리,체크를제거한바탕에만WDN/Photo2pass. BM200은2x2칸/BM269는4x4칸위치·색군·alpha고정,칸내명암만bilinear확대. 이두건은AI추론으로세지않음. qa/checker_fidelity_v1.json 시각검수대기/미통합.
- 병행SR012신규12원본24결과46pass완료/미검수·미통합. Field v2는79소형SC확장,기존1630텍스처·576FM그룹보존,새텍스처0. 작은묶음내새미지원구획이추가발견되어실패223/미분류833. 전체목표active.


### CHECKER-001 정적 검수와 기존 바닥 후보 재검토
- BM221정확핑크/그린614source픽셀=39296output픽셀RGBA완전일치. 체크제거입력으로WDN/photo2실제RGBpass,프레임sourceguide .35/.60후처리2. .60선택:칸선명함유지하면서과한프레임입체감감소. BM20016px pitch4칸/BM2698px pitch16칸의전체클래스·경계·phase·alpha정확일치,칸별명암범위보존. 두기하출력은AI카운트0. 6출력해시/크기/모델·input/native/parent/mask검사,두배경직접검수. qa/checker_fidelity_review_v1.json.
- BM201/209/244원본2배전체비교에서체크칸내삼각균열·접힘·경계해석을발견,기존후보취소하고원본격자/손상보호재작업으로환원. BM226대각체크는메시화/흐림없어정적후보유지하되정밀칸·UV검증미완료. qa/checker_floor_audit_review.json. BM175기존보류유지.
- 후보229/보류17/미처리38(전투284분모),실제추론244+기하전용2=전투처리246. neural-only카운트는244/타이틀포함245유지;도형출력을AI로세지않음. 처리집계계약명시. 기존20키팩해시보존/미설치/런타임미검증. SR011역사보고서BM221superseded표시.
- Field v2정정:79미지원count경로에허용범위를넓혔지만새검증SC는59개(363→422),추가텍스처0.총SC631레코드중209실패/STCM151검증/1630텍스처·1616해독·576고유보존,833미분류. 원본field inventory v1보존. 신뢰안되는스파스offset/SSCRvariant강제허용안함.
- LOCAL-SR-012기존미처리40원본5페이지직접분류저장. 신규12종24출력46pass은GPU정상종료,검수미완료로카탈로그미통합. 다음첫단계outputs/sr012-review/review-01..04직접검토. field v2도exit0,현재실행프로세스없음.
- Coutputs/체크판_디자인_보존_비교.png 및진행.md갱신. 사용자핵심디자인지적으로검수기준실제강화;전체목표active이며런타임/최종ZIP미완료.


## 2026-09-23 — LOCAL-SR-012: 신규12종 검수 및 환기구 직접 재구성
- 이전 goal turn은 CHECKER-001 후보/보류 갱신으로 progress. 이번 시작 시 최신 PROGRESS/카탈로그/실제 SR012 출력을 재확인했다.
- 신규12종 초기24출력/46pass, 4모델비교 페이지+4밝고어두운 matte페이지+6상세 crop 직접검수. BM087 창소실·BM110격자휨/중심변형·BM115과도광택 발견. 추가 anime/general raw 4결과6pass와 BM115 filtered1pass+guided2후처리. 구조guide5추가후처리. 총 로컬53pass.
- 사용자 지시 ‘로컬이 영 별로면 네가 직접 그리도록’ 반영. imagegen built-in BM110 1외부편집(1774x887)도 선개수/중심부/배치변경으로 불채택; alpha128 축소IoU .8425656. 원본/생성파일/해시 qa/local_sr012_manual_grille.json. 외부처리를 로컬로 세지 않음.
- Codex 직접 SVG BM110 v1: source y8/10/12/14/17/19/21/23/25 가로9개, x9/15/21/27 세로4개 및 y15 x11/17/23/29 짧은선4개. 중심 십자홈·하단2구멍 재구성. 전체v1 재질평면/edge색점으로제외, local외곽+직접격자/중심v2 후 원본명암v3 선택. SVG자체개수/좌표·원본row/col증거·최종gridRGB완전일치·mask밖초기WDN완전일치·alpha부모일치검사. true HD 복원주장안함.
- 41출력 원본PTM/RGBA·모델/input/native/parent/vector/mask/output 해시 및4x/8x크기/분할coverage 검증. 초기alpha metrics재계산에서BM111두모델약알파5점손실발견. source bicubic/Lanczos alpha2후처리비교후bicubic선택(약알파손실0/IoU .88047/질량+0.1558%). 초기실패값보존. zero255support검증; BM101116118 sourcebilinear alpha정확일치. 전체형상·UV·게임증거아님.
- 선택10: Photo BM062/063/074/101/116/118; WDN BM065/079; WDN RGB+source bicubic alpha BM111; 직접재구성v3 BM110. BM087와BM115는 모든trial품질미달로보류, 직접재작업필요. qa/local_sr012_review.json. 기존229후보/나머지모든그룹/특수3건보존.
- 누계실제neural원본257(타이틀1+BM256),geometry-only2별도. BM후보239/보류19/미처리26,처리258. 신규12관측키0,기존20키검수팩바이트보존/미설치/런타임미검증. Coutputs/직접_재구성_환기구_비교.png 와진행.md갱신. 전체목표active.
- 다음: BM087원본 facade 128x76 확대(outputs/sr012_BM087_facade_source.png) 기준창무늬 직접재구성, BM115잔해재작업. 체크 BM175/201/209/244 및 BM226정밀audit, fieldv2 미지원구획 해독/576원본분류, 적/효과/컷신 확장. GUI접근복구증거없어재실행/검은화면루프없음.


## 2026-09-23 — LOCAL-SR-013: 건물 직접 재구성과 잔해 재작화
- 이전 goal turn LOCAL-SR-012는 progress. 사용자 직접 그리기 지시에 따라 보류 BM087/BM115를 재작업했다. 신규 원본0/새 local inference0/GPT external edit1/파생12출력. alpha/color/vector 후처리를 새 추론으로 세지 않음.
- BM087 facade v1 두안은 개별픽셀에 창틀을 만들어 barcode처럼 보이므로 제외. v2 연속 가로86구간과 원본색 gradient 작성, bands .30 선택(.60은 얼룩/흐림). 지붕[74,1,89,4] 원본45→출력2880 RGB정확보호, SVG row좌표/86개·mask밖WDN정확·alpha WDN정확검사. 실제 창문개수 복원주장없음.
- BM115 원본15색 contour tracing2안은1431윤곽의 양자화가 diamond/maze로 드러나 제외. built-in image_gen 1외부편집2172x724, raw 직접적용거부. 원본alpha3component에 축정렬bbox등록,색조.8+edge2를 정적후보선택. 외부모델ID비공개. 정확prompt workspace/gpt-trials/BM115-v1/prompt.txt.
- 등록시 generated alpha128가 빠진 원본326/8031px(부분81/82/163),최대원본거리2.2361px색채움. raw등록IoU .9320567/.8707865/.8864162 재계산. 복원alpha를생성재질면일치증거로쓰지않음. RGB tone.8부모정확, sourcebilinear halfcoverage/zero255support정확,edge2 alpha128component3,약alpha손실0/축소128IoU .9966542/mass1.0179848. alpha byte-exact주장금지.
- 모든12원본PTM/RGBA·부모·SVG/render/mask/generated/output해시/8배크기검사. 건물전체/좌우/양matte 및 잔해각재작업전체/좌중우/연결부양matte 직접검수. qa/local_sr013_review.json. 기존239후보/다른그룹/특수미해독3건/체크계약/fieldv2/Start-Title-QA/20key팩 보존.
- 전투후보241/보류17/미처리26,neural256+geometry-only2;타이틀포함실제neural원본257유지. SR012역사카운트유지하고 resolved_holds만추가. 이번2종관측키0,설치/에뮬실행/런타임검증없음. GUI복구증거없어검은화면캡처반복없음.
- 사용자출력 Coutputs/직접_재작업_건물과_잔해_비교.png 및진행.md. 다음 체크175201209244 재작업/226정밀검수,남은26원본,field576분류/미지원SC구획,적/효과/컷신확장. 전체목표active,실게임·폰트·LOCK ON·최종ZIP미완료.
- 최종 사용자 3열 비교표도 직접검수 완료: 원본/초기로컬/선택후보 라벨·crop 일치,건물체크·가로무늬·잔해연결부 확인. 실제게임미검증 상태 유지.


## 2026-09-23 — LOCAL-SR-014: 체크 바닥·철망 재구성 실패 판정과 원인 기록
- 이전 goal turn SR013은 후보2종을 실제기록한 progress. 이번은 원본측정/재구성8출력/직접검수 및 실패원인·다음변경근거를 남긴 progress이며, 후보 추가는0이다. qa/local_sr014_review.json.
- BM175 source dark그룹 분리와 독립명암 v1두안: 상/하36/35그룹이 highres50/50으로분리되고 둥근점무늬로 보여거부. v2각진SVG두안:36/35그룹·모든원본그룹표현 확인했으나 매끈한판에슬롯을낸디자인으로바뀌어거부. source dark그룹은실제구멍수확정이아님. 메쉬/타공판의실제소비자료필요.
- BM2015원본patch의좌표·checker경계·원래균열을분리하여224개부분cell영역을2명암설정으로그림. 실제완전한칸224개라는뜻아님. 평평한붙임판/얼룩진균열로v1두안거부. v2 source색+local미세재질/좁은균열경계유지두안도grid와parent경계겹침의가로띠발견으로거부. 다음은겹쳐붙이기를중단하고patch전체를한좌표계의일관된surface로재구성.
- 실제원본확대에서일부큰삼각균열은원래존재함확인; 모든삼각파손을모델이만든것으로일괄판정하지않음. 원본파손과추가변형분리필요. strongadjacent3x3표본254쌍중원본과부호다른2쌍이윗손상경계에남음; 전체칸phase/geometry증거로쓰지않음. 초기local대비도별도기록.
- 원본확대15페이지중9개·비교14페이지중11개직접검수. 8출력 PTM/RGBA/source/parent/structure/mask/SVG/output SHA·8배·alpha255검사. v2 panel metadata의이전sample오차값이상속된것을현재저장coverage재측정으로정정,이전값별도기록.
- 실제신규local추론0/GPT외부생성0/신규원본0. 이전모델출력활용과수치/SVG재구성을AI추론으로세지않음. 기존카탈로그241후보/17보류/26미처리,20key팩,checker계약,fieldv2,Start-Title-QA해시보존;설치/에뮬실행/런타임검증없음. BM175/BM201계속보류.
- BM209/BM244/BM226는원본/기존비교재검토만했고재구성완료주장없음. 다음checkerpatch단일surface,소비자확인자료,전체field/적/효과/컷신및남은26원본계속. 전체목표active;외부화면접근문제는전체오프라인작업의막힘이아님.


## 2026-09-23 — LOCAL-SR-015 / FIELD-SR-001
- 이전 SR014는 실패8안의 검수·원인 기록으로 progress. 이번은 BM201 외부재작화1회 검수와 필드72원본 분류/신규28원본56실제 local GPU pass/24정적후보를 추가한 progress. 전체목표active.
- BM201 built-in image_gen 1회 실제1254²→Lanczos2048². 원본과254인접대조쌍 부호역전0,207경계표본 측정. 표본/원본해상도 수준의 검사이며 전체칸·HD형상·nativeUV 보존 증거가 아님. 정확prompt workspace/gpt-trials/BM201-v1/prompt.txt.
- BM201 raw/tone2안과 작은균열수정4안=6출력, 신규local추론0/신규원본0. 실제원본에도 어두운균열 조각이 존재하나 생성안은 이를 과장. 좁은보정은 번짐/패치 흔적이 남아 모두채택안함. BM201계속보류. 10비교페이지+1좌표페이지직접검수. v3의rim제외보장 주장을 제거하고같은칸/밝기필터라는측정가능한사실만기록. qa/local_sr015_review.json.
- 필드 v2 총576그룹 중 전투와픽셀동일225를제외한351의첫72 원본8페이지전체분류. 글자5/캐릭터포스터1/가는alpha/창틀/도로atlas 등을 분리. 포스터는주인공연결제외검사보류. source review분류가소비자/UV/범위제외증거는아님.
- opaque28종 WDN/Photo 각28, 실제RGB56pass. input sigma.25/.35, native4x+Lanczos2x 최종8x. 새외부업로드0. 14전체비교+7실제8x crop직접검수. 24정적후보: FM0036/0040/0048/0049/0052/0053/0056/0057/0061/0062/0063/0071/0072/0073/0074/0075/0076/0077/0079/0080/0081/0083/0084/0118.
- 보류4: FM0055벽돌선 재해석,FM0078격자 가로선소실,FM0117균열망과장,FM0119반복패턴 재질변경. FM0078 직접SVG16칸v1도버튼같은새테두리로거부. v2는원본110px→7040px정확보호층;이는격자부분단순확대이며HD재작화로세지않음. 후보미채택/충실한fallback으로만보관. qa/field_sr001_grid*.json.
- 56추론출력 source PTM/RGBA·model/input/native/output SHA·4x/8x·alpha255·native출력에서Lanczos재현검사. SVG2출력/hash/mask밖정확 및v2원본격자RGBA정확. FM0072/0084 표본단면반복선개수일치; 전체형상/UV증거로확대해석안함. qa/field_sr001_review.json 및새 qa/field_sr_catalog.json.
- 전투241후보/17보류/26미처리 유지. 필드신규28처리/24후보/4보류,novel미처리323. 타이틀1+전투256+field28=neural고유285;geometry-only2별도. 전체게임분모/완료율아님. 기존20key시험팩·checker계약·fieldv2·Start-Title-QA해시완전보존. 설치/에뮬실행/런타임검증없음.
- 다음 FM0078원본연결격자/프레임을일관되게재구성(개별버튼테두리금지),field추가원본분류/미처리323,전투26/보류17 및적/효과/컷신·SC해독미완료계속. GUI접근복구증거없어검은화면캡처반복안함. 최종ZIP미완료.


## 2026-09-23 — FIELD-SR-002 / GRID-003
- 이전goal턴SR015/field001은실제분류72/추론28/정적후보24와실패검수기록으로progress. 이번도source72신규분류/40신규neural원본/84actual local pass/외부생성1/신규필드36후보+기존격자1해결로progress. 전체목표active.
- field source02의다음72개8페이지직접분류,누계144/351novel. 글자·포스터/인물·alpha·shader ramp·미세격자는별도분류,범위제외없음. 불투명40종WDN/Photo80pass, FM0160/0188에WDNσ.65와Fate anime6Bσ.35로4추가pass. 최초local80+재작업4=84출력/실제84pass.
- 20비교+11native8x crop+2재작업페이지직접검수. source geometry diagnostics 고정임계결과보존. FM0128 source/WDN8 versusPhoto10trough;FM0129source/Photo4 vsWDN5;FM0142source/WDN31 vsPhoto30;FM0153/0265표본12/7동일. 이는물리막대개수전체증거아님. FM0147공통σ.5후prominence10..18에서모두8강한trough,FM0161은threshold민감도전체기록하고완전형상보존주장안함.
- 보류4: FM0132반복가로선해석(표본15vs14),FM0137노란7연결영역은같으나축소classIoU .821596로경계/dither해석불확실,FM0167미세대각pattern왜곡,FM0188원래희미한선의균열강조. FM0148/0149/0152yellow연결영역5/8/13개각원본동일,IoU .99258/.96336/.98663. 연결영역이실제줄개수/전체UV증거는아님.
- FM0078연결격자 직접SVG v3 채택: 5가로/5세로막대,16square darkcell,source색bar gradient. 원본class threshold95 전체mask와출력정확일치/16components/16darkcore1024outputRGBA정확/mask밖parentRGBA정확;5184outputpx수정. 새로운AI상세복원이아닌sourcegeometry구성. v1버튼같은테두리와v2원본NNfallback은미채택그대로보존.
- FM0160원본에도희미한대각선/짧은균열이있음재확인,모든균열을AI발명으로일괄판정하지않음. 로컬4조건은강조가심함. built-in image_gen 1외부편집actual1254²(request1024²)→Lanczos512². 초기rightedge p95원본1.1875px차이;source60행edge기준수평등록+σ2명암.65보정후p95 .3125/.0625px. 재작화2초안+등록1출력중등록안정적채택. 정확prompt workspace/gpt-trials/FM0160-v1/prompt.txt. modelID미노출. source대표edge측정이며전체geometry/nativeUV/게임증거아님.
- 총88파생출력=local84+직접SVG1+GPT파생3. 원본PTM/RGBA·model/input/native/output·SVG/render/mask·generated/prompt/map/underlay해시,4x/8x/alpha255와localLanczos재현·GPT등록재현검사. 검수36페이지와source8페이지를보고서에연결. qa/field_sr002_review.json.
- 현재필드68neural처리/61정적후보/7보류/novel미처리283,전체576field중해당소비문맥미처리508(전투픽셀동일225포함). 이전필드24후보바이트/기존전투241후보17보류26미처리/20key팩/checker/fieldv2/Startscript완전보존. 타이틀1+전투256+field68=neural고유325;전체게임분모아님.
- 사용자‘얼마나남았어’에전투43/추가field미처리283와미완료적·캐릭터·효과·런타임·최종팩범위를설명. 전체게임자산총수미확정으로전체완료율/정확시간미제시. 도구화면오류복구증거없어에뮬재실행없음,설치/런타임/최종ZIP미완료.
- 다음: 기존분류alpha/미세격자·복합atlas보호및필드잔여283원본,FM0137경고띠·FM0167격자·FM0188재질직접수정,전투43/적/효과/컷신/미지원SC진행. 보류7에는FM0055/0117/0119도포함. source분류는소비자/UV/주인공제외증거아님.


## 2026-09-23 — FIELD-SR-003 / 직선·직각 판정 반영
- 이전 FIELD-SR-002는 신규40/36후보와격자수정으로 progress. 이번도 투명field27신규원본/102실제local추론/66출력검증/12정적후보 및 직선·직각 계약을추가한 progress. 전체목표 active.
- 원본3페이지 재확인 후 WDN/Photo54결과: RGB58+alpha38=96pass. FM0254/0255 눈에보이는두행격리(소비자/UV증거아님). 가는8종과nearopaque2종20출력은 source-bilinear alpha정확; 나머지는20%neural/80%source와0/255support/평균보정. 새외부업로드0.
- 비교9페이지+native상세12페이지 모두검토. FM0115/0121/0122 추가WDNσ.65와Fate animeσ.35 6RGBpass/6결과 모두불채택: 강한선/입체화 또는단순흐림. 새원본누계27 그대로.
- 초기약alpha검사손실0만으로전체보존주장불가. FM0087 bilinear축소128IoU.5 확인; sourceNN대조도.7558이므로이측정은runtimealpha-test증거아님. texel-center128IoU.97647/240IoU0, bicubic/Lanczos보정2출력은center개선하지만mass+4.95%/+8.42%, 약점1/4개손실. 두배경전체/상세검수후모두보류. 새로운추론0.
- 사용자 ‘직각이어야 하는건 직각’ 반영. 원본직선·직각/칸간격/원근선 보호, 생성재질로구조변형덮기금지. qa/architectural_geometry_contract.json. 원근/의도된아치/파손은무조건90도로왜곡하지않음. 기존61field후보와battle후보는신규geometry적용대상판정대기; 이전material후보숫자만으로최종geometry통과주장금지.
- FM0045/0120 직접SVG v1은원본색픽셀블록이남아탈락. v2 구조rect와면의linear gradient분리+local고주파±4 RGB만안쪽활용. 원본alpha정확/편집mask밖parent정확/blackrail14x2 source사각검증/모든SVG rect축정렬·roundedcorner없음. 두v2정적후보; 직접도형출력을새AI복원으로세지않음. v1/v2총4페이지검수.
- 새12후보: FM0045/0120 planar v2, WDN FM0060/0123/0124/0260/0263, Photo FM0157/0254/0255/0256/0264. 새15보류: FM0029/0037/0038/0047/0059/0087/0113/0115/0116/0121/0122/0145/0164/0268/0272. 각실패/추가geometry조건은최종보고서에기록. 작은그래픽272와격자29/113보호필요.
- 전체66출력=초기54+local재작업6+alpha후처리2+SVGv1/v2 4. 원본PTM/RGBA·model/input/native/parent/output·vector/render/mask SHA/크기·저장native후처리재현검증. 검수30페이지+source3. qa/field_sr003_review.json.
- 현재field95neural/73정적후보/22보류/novel미처리256, 소비문맥미처리481. title1+battle256+field95=neural고유352. battle241후보/17보류/26미처리와20key팩/원본inventory보존. 설치/에뮬실행/실게임/최종ZIP미완료.
- 다음 기존건물후보의원본직선anchor검수와29/113격자·37/38/116창틀직접재구성, field잔여256 및적/효과/컷신범위계속. GUI복구증거없어검은화면캡처/재실행반복없음.


## 2026-09-23 — FIELD-GEOMETRY-001 / 원본 직선·직각 재검수
- 이전 FIELD-SR-003는 progress. 이번은8원본 audit와창틀2종 직접수정/6파생출력 검증 및기존2후보철회로 progress. 신규원본/로컬추론/외부생성0, 전체목표active.
- FM0257/0258 창틀 v1은붙임판 같은재질로제외. v2는원본좌표·2/4직사각창·12막대가맞아도유리안쪽둥근밝은잔재가남아대체. v3는기존로컬유리안쪽재질을1source픽셀연장해잔재제거,선택. 세로pitch8/11source px,FM0258밝은bar9/20/31/42/53근거4동일10px개구부해석;source RGBA정확복원아님.
- 전체6결과 원본PTM/RGBA·부모·SVG/render/map/mask/classes/output SHA,8배크기/alpha255/mask밖RGBA정확/축정렬rect·12bar coverage 및저장recipe로RGBA재현검증. 클래스검사만으로시각충실도주장안함. source10페이지+whole/crop12페이지직접검수. qa/field_geometry001_review.json.
- FM0189/0190 기존재질후보는창틀/수평경계휨으로철회,원본anchor재작업보류. FM0029교차행alpha위상/오른쪽하단4x2창·상단3칸,FM0113상단grid/하단Xbrace,FM0037/0038원근구조audit만완료;재작업완료아님.
- 현재field95neural/71정적후보/24보류/novel256미처리. 과거field geometry적용여부대기57, battle241동일. title1+battle256+field95=실제neural고유352. catalog변경4그룹외572동일,보호원본/전투카탈로그/20key팩바이트보존.
- 사용자비교 outputs/창틀_직선_직각_수정_비교.png. 설치/에뮬실행/실게임검증/최종ZIP미완료. 다음189/190창틀/가로띠anchor재구성,29/113격자와37/38원근구조,잔여field/적/효과/컷신계속.


## 2026-09-23 — FIELD-GEOMETRY-002 / 건물 면·창틀 음영·셔터 수정
- 이전 geometry001은progress. 이번은보류2종의4단계직접수정8출력+GPT외부재작화1회/Lanczos1출력 검증과FM0189 보류해결로progress. 신규local추론0/신규원본0,전체목표active.
- v1 source프로필은blurred붙임판 재질이라제외. v2 기존로컬 경계추적으로펴기는corner휘어짐/구간시작끝단차가남아제외. v3 고정면+local단면프로필에서189 source회색측면x31이흰색250수준으로변해창틀폭이2배로보임확인. v4원본gray/shadow독립세로면복원후189선택. 190은가로띠재질/접합부의일관성부족으로계속보류.
- 189화이트core4세로구간 threshold200 각행패턴동일,논리1source픽셀폭8output중7밝은core+1edge-transition. sourceRGBA/NN완전동일주장없음. 가로sill은grain때문에threshold200 edge1행차이존재기록. shutter두span prominence3/5 source/output8밝기peak이며위치근사일치;8/10threshold개수달라짐전부보존. 물리slat8개증거아님.
- built-in image_gen 190 1외부편집 actual887x1774→512x1024Lanczos. 유리/석재거친요철과장이남아전체채택안함. 8창경계표본p95오차.1875~.4375source px;전체geometry/runtime증거아님. 원본에도darkcorner/bevel있으므로전부생성오류로지우지않음. 정확prompt workspace/gpt-trials/FM0190-v1/prompt.txt.
- 9파생결과 sourcePTM/RGBA·parent/vector/render/map/profile/mask/output/GPTprompt/raw SHA,8배/alpha255·region1회coverage·좌표map단조성·모든저장recipe RGBA재현검증. 비교27페이지중19직접검수(초기탈락v1/v2는전체2씩만). qa/field_geometry002_review.json.
- 현재field95neural/72후보/23보류/novel256미처리,unique neural352유지. 다른574field그룹/전투241후보17보류26미처리/20key팩/보호파일보존. 설치/에뮬/게임검증/최종ZIP미완료.
- 다음190 GPT석재재질만고정가로면안에제한적활용·원본cornerpatch보호·유리유지,29/113격자37/38원근면및잔여256/전투43/기타캐릭터적효과컷신범위. 사용자비교outputs/건물_창틀과_셔터_수정_비교.png.


## 2026-09-23 — FIELD-SR-004 / 원본 선·면 보호 및 다음 배경 묶음
- 이번 goal turn은 progress. 신규 source72종/8페이지 직접 분류하여 누계216. 불투명30종 WDN/Photo60 RGB추론 +FM0303/0305/0336/0363 WDN.65/general.35 재작업8 = 실제 로컬68회. 새 원본30종, 새 외부 호출/업로드0. 로컬native4x 후Lanczos2x임을 구분.
- 전체15·native10·재작업4 페이지 직접 검수. FM0303 과도한 미세균열,0305 나이테 흐림/과장,0336 균열/세로선,0363 중앙선 해석은 네 조건 모두 최종 채택하지 않음. 0363원본 자체x30 어두운 선과 외곽 테두리 확인; 기존 자연재질 분류의 한계는 최종 review에서 정정하고 해시로 묶인 원본분류 기록은 유지.
- 원본 좌표 직접 보호3파생: FM0282세로선x7..8/61..64 고정, v1은 주변 재질을 행별로 늘여 가로 줄무늬가 생겨 제외. v2 인접 로컬 재질 조각+4px 접합으로 수정 후 채택. threshold80 밝은 지지영역 모든 행 동일. FM0356 원본RGB115/93/74 평면[0,4,128,18] 그대로, y25..33 로컬Photo에 연결,33아래RGBA동일. 두 최종 후보; 새 AI추론 아님. 비교6페이지 직접 검수.
- FM0190 과거 GPT생성 재질 고주파만 고정cornice안 strength.45/±8,.75/±12 2파생/6페이지 모두검수. mask밖·darkcorner·glassRGBA 그대로여도 cornice접합의 붙임판/둥근느낌 해결안됨. 둘 보류. 재질grain만으로 해결한다는 가설 제외, 다음은 원본 면 단면/접합음영 해석 변경 필요. 새 외부호출0이며 기존 외부재질 재사용을 전부로컬이라 부르지 않음.
- 신규14 후보: Photo276/297/302/306/307/313/322, WDN277/280/286/304/315, 직접보호282v2/356. 신규16 보류:275/303/305/328/329/330/332/333/334/336/337/338/345/346/347/363. 기계atlas328/329/330/333은 재질이 나아도 facet/shaft 원본선anchor미확정이라보류. 332작은무늬가 가짜글자로 바뀜. 347원래곡선을마름모로바꾸지않음. 346명암면이검은틈/가는막대로해석되는오류. 밝기profile peaks는 실제기둥개수증거아님.
- 전체73출력 =68로컬+직접면3+기존GPT재질2. 원본PTM/RGBA,model/input/native/output/부모/vector/mask SHA 및입력/저장native후처리/5파생RGBA재현 확인. 소스8+비교41=49페이지 직접검수. authoritative qa/field_sr004_review.json. raw추론report의pending은이최종review로판정; 바인딩해시유지를위해raw기록불변.
- 현재field125neural/86정적후보/39보류/novel미처리226. source분류216/351. title1+battle256+field125=고유neural382. 기존72후보,다른545fieldgroup,전투241후보17보류26미처리,20key팩/보호파일보존. 과거57field/241battlegeometry적용여부대기. 설치/실게임검수/최종ZIP 미완료, 전체목표active.
- 다음 FM0337/0346원본반복띠·0347곡선격자,29/113격자·37/38원근건물,잔여field226·전투43와기타캐릭터적효과컷신범위. FM0190grain강도반복중단. GUI복구증거없으므로검은캡처반복/컴퓨터유즈실행없음. 사용자비교 outputs/선과_평평한_면_수정_비교.png.


## 2026-09-23 — FIELD-GEOMETRY-004 / 반복 기둥·장식 격자 보류3종 수정
- 이전FIELD-SR-004는progress. 이번은 원본좌표3종audit,10출력검증과FM0337/0346/0347 보류해결로progress. 신규local추론/새고유원본0, built-in image_gen 외부편집1회. 전체목표active.
- 337 source밝은span10개(왼끝포함), y4..46기둥면과하단47..50/59..62띠, 왼x0..9연속면 분리. 실제3D기둥10개주장아님. v1질감번짐, v2local interior grain강조가거친얼룩으로보여제외. GPT정확지시문 workspace/gpt-trials/FM0337-v1/prompt.txt, actual1774x887→1024x512Lanczos. 원본/geometryv1두참조,modelID미노출. 전체GPT그림은색/좌표보장안되므로불채택. 각source평면안쪽재질만재투영하고원본평균RGB와완만한행/열조명복원한v3채택. 전부로컬결과라고하지않음.
- 346 source6px주기/밝은2px띠6개,나머지는blackhole아닌회색면. v1옆면평평함,v2cubic보간흐림으로제외. v3 밝은2/음영3/어두운bevel1source px로구분하고source세로조명+기존WDNgrain±2로수정,채택. 공간기둥수확정아님.
- 347 상단source수평행0/1/15/16/31과세로x0/31/63고정,하단4waist/8곡선팔작성. 이전oval표현은완전타원증거아님을정정. v1너무흐림,v2stroke개선후pixelindex를좌표로쓴오프셋확인. v3각trace x/y+.5픽셀중심변환. 인접교차팔영향을분리한48source highlight중심표본 median오차.2/p95.4source px;전체geometry/runtime증거아님. v3채택.
- 원본PTM/RGBA·부모·vector/classmap/base/output/GPTraw/prompt/reference SHA,축정렬rect·전면1회coverage·저장base/recipe로RGBA재현·8배/alpha255확인.337출력signed edge주변오차추가측정(제한된anchor근방이며global증거아님). 비교/source19페이지중16직접검수,초기실패v1detail3미사용+GPTraw직접검수. qa/field_geometry004_review.json.
- field125neural/89정적후보/36보류/novel226미처리. 기존86후보와다른573fieldgroup,전투241후보17보류26미처리,관측20key팩/보호원본 보존. 고유neural382유지. historical57field/241battlegeometry적용여부대기. 설치/실제게임/최종ZIP미완료.
- 다음29/113격자·37/38원근선·나머지structured보류와잔여field226/전투43/캐릭터적효과컷신조사. FM0190grain강도반복은중단한상태이며면단면/접합해석변경필요. 사용자비교 outputs/기둥과_장식격자_수정_비교.png.


## 2026-09-23 — FIELD-GEOMETRY-005 / 받침대·깨진 유리·재질별 재작화
- 사용자 지시 추가: 깨진 창문은 직접 재작화, 도구/구조물의 직선 유지, 목재·돌·콘크리트 재질 구분. qa/architectural_geometry_contract.json에 기록. 358/359/364는 직접 재작화 대기이며 작업완료 아님.
- FM0029 v1 격자/캐비닛/노란판3영역 source palette rectangles +기존WDN잔질감. 격자alpha위상 sourceNN정확. 나머지frame미수정이라 wholeheld. FM0113 v1 RDP외곽은 slot기울어짐/두께왜곡으로 불채택.
- built-in image_gen 2회 실제수행: FM0113 raw887x1774,FM0029 raw1774x887. 각 workspace/gpt-trials/<ID>-v1/prompt.txt와raw보존. 전체생성안은위치변화로불채택; FM0029왼위미니그림도불채택영역. 새local추론/새고유원본0.
- FM0113 직접source좌표직선polygon과직사각slot,4닫힌구멍. 새목재grain은면안에투영하고원본상단어두움/하단마모색조유지. 목재·콘크리트해석은설계방향이지native재질확정아님. v2상단재질너무평평하여v3고정seam/bevel+재투영pane/concrete로변경. v3정적후보채택.
- FM0113 sourcealpha center22불일치,IoU.9538784,mass+0.60728%, source/output모두닫힌구멍4. raw v2 lower_holes_count=6은외부배경분리영역을포함한잘못된수치이며finalreview에서hierarchy4로정정. source픽셀동일주장안함. 직선path/slot직사각alpha/수직수평seam불변검사.
- FM0029 GPT유리6영역만sourceglassmask내재투영,frame/나머지palette영역/alpha보호. v2너무밝은유리는v3sourcegray평균에맞춰낮춤. 유리부분미리보기이며frame/하단판넬/파손세부대응미완으로wholeheld유지.
- 파생6+GPTraw2=8출력 lineage/크기/보호영역검사. 전체19비교페이지중12직접검수+raw2직접검수;미사용7은실패whole후중복또는변경없는영역. 원본/PTM·catalog/contract·보호팩해시검증. 최종 qa/field_geometry005_review.json. 원본/기존89후보/다른574fieldgroup/20key팩바이트보존.
- 현재field125neural/90정적후보/35보류/novel미처리226. 고유neural382유지,전투241후보17보류26미처리. 전체목표active,설치/실게임/최종ZIP미완료.
- 다음29창틀·하단판넬과358/359/364깨진창직접재작화,37/38원근구조등structured보류,남은field226/전투43/기타캐릭터적효과컷신진행. GUI복구증거없어컴퓨터유즈실행/검은캡처반복없음.


## 2026-09-23 — FIELD-GEOMETRY-006 / 깨진 창문3종·갈색 틀/패널
- 이전005는progress. 이번은신규직접GPT전용원본3종과FM0029틀·판넬2안으로progress. 전체목표active. 사용자직접깨진유리/직선/재질기준유지,로컬추론0/GPT외부생성3회.
- 358/359/364 각각built-in image_gen 1774x887. 지시문/원본 workspace/gpt-trials/FM0358-v1,FM0359-v1,FM0364-v1. 생성전체는변경된창문/구멍위치,359체크무늬,364색프린지,358/364신규손잡이로불채택. source좌표창틀/직선polygon파손alpha로다시구성하여해당부분제외. 깨끗한359유리재질donor공유,각건물본인GPT콘크리트재질story별재투영.
- source128x64→1024x512,창12/12/10개직사각영역. 원본alpha닫힌구멍13/15/20개모두보존. singlepointcenter4/2/2픽셀불일치,IoU.9992846/.9996932/.9996785,alpha총량+0.1696/+0.1353/+0.2152%. sourcecenter샘플위상(+.0625)와4점대칭샘플도기록;실게임alpha-test보증아님.
- facadesv1 유리에큰donor균열/잔무늬와364상단fragment범위문제. v2는고주파잔질감+작은평면반사·절단면강조,364원본palettecomponent범위포함. 세v2정적후보. source파손을새일반구멍으로대체하지않음. 원본창틀직각/불변bevelRGB·alpha/render/base·mapping단조성검증.
- FM0029 lower창틀/패널86sourcepolygon직접작성. 원래금색chamfer와우하단기울기유지,생성볼트제거. v1색테두리두꺼워v2원본darkrim/얇은coloredbevel분리,작은원본plate고정부팔레트복원. 기존tone유리를innerpolygon안에유지,외부mask/alpha불변. 상단기계/잔여영역과재질·cornerstyle통일검토미완으로wholeheld유지.
- 총11검사출력=facade6+atlas2+GPTraw3. 원본PTM/RGBA·부모/GPTprompt/raw/donor/vector/render/base/output SHA검사. source/비교34페이지중33직접검수,raw3+donor1직접검수. 최종 qa/field_geometry006_review.json. 원본/기존90후보/다른572fieldgroup/20key팩보존.
- 현재field93정적후보/35보류/미처리223. 로컬neural125 +신규directGPT-only3 =전체처리128;catalog기존field_neural_originals는로컬추론125로유지하고별도필드로구분. source분류216유지. title+battle+field로컬고유382,외부전용포함전체처리385. 전투241후보17보류26미처리. 전체게임완료율아님.
- 다음29상단기계/일관된프레임재질·corner검토,37/38원근구조와field223/전투43/다른게임원본범위. 설치/실게임/최종ZIP미완료,새키/에뮬실행없음. GUI복구증거없어검은캡처반복안함. outputs/깨진_창문_3종_수정_비교.png 및갈색틀비교보관.


## 2026-09-23 — FIELD-SR-005 / 남은 원본 분류·재질과 직선 검수
- 이전geometry006은progress. 이번도신규20로컬원본/7정적후보로progress,전체목표active. 남은135source/15페이지직접분류하여decoded novel field351 routing완료. 전체게임분모나225battle픽셀동일소비자검증완료아님.
- WDN/Photo20종40실제RGBpass,525/533 Anime6B.25추가2pass 모두불채택. 총42실제local RGB추론/새외부0. native4x후Lanczos2x. nearopaque480/494/506alpha는sourceBILINEAR8x정확별도,alpha추론0.
- 처음 folded/material로넓게분류한391/396은각진부품atlas,466은희미한masonry,473은벽돌+대각파손,476은masonry/aggregate혼합,518은grayscale shading/region으로최종review정정. 원본분류/추론의바인딩해시기록은불변.
- 신규7후보: Photo424,WDN480/486/494/499/506,502직접border v2. 신규13보류391/396/407/456/465/466/473/476/495/496/518/525/533. 흐린원본단서를줄눈/장식으로임의강조한결과나더선명하지만휘는부품선은불채택.
- 502source top/bottom/side4rect mask로띠구조보호. v1rowshade가평평한블록이라불채택;v2원본texelcenter median단면선형보간+localhighfreq±1 RGB만사용. mask밖/alpha부모정확,모든선길이방향RGB변동최대2,두recipe RGBA재현. 원본색/띠단면검사이지UV/실게임증거아님.
- 전체44출력=42local+geometry2. source351PTM/RGBA,3model/input/native/output,vector/mask/parent/replaySHA검사. source15+좌표1+비교31=47페이지직접검수. 3nearopaque는양배경검수/원본alpha별도보존,source/outputalpha평균차기록. 최종qa/field_sr005_review.json.
- 현재field100정적후보/48보류/novel203미처리,local145+directGPT-only3=148처리. 소비문맥미처리428에는battle픽셀동일225포함. title1+battle256+novelfield145=402고유local,외부전용포함405. 기존93후보/다른556fieldgroup/전투241후보17보류26미처리/20key팩과원본보호파일보존.
- 사용자완료시간질문에는아직상당한작업/직접수정과실게임검수잔여를설명,전체완료율·ETA확답안함. 설치/실게임/최종ZIP미완료,GUI복구증거없어에뮬실행/검은캡처반복없음.
- 다음새보류masonry줄눈/496cornice/533얇은scroll/525motif 직접구성,29/37/38등기존구조보류,field203/전투43/기타인물적효과컷신/미지원원본범위. outputs/field-sr005/재질과_직선_검수_비교.png.


## 2026-09-23 — FIELD-GEOMETRY-007 / 벽돌 이음선·장식 곡선
- 이전SR005는progress. 이번3sourceaudit/6파생검토/495·533보류2종정적후보로progress,전체목표active. 새local/GPT/고유원본0. 496은source구조audit만,wholeheld유지.
- 495 v1 좁은좌측원본ROI가비어nonfinite RGB/검은edge발생하여무효. v2 숫자는유효하나손으로잡은여러joint좌표가틀림. 원본row별darkprofile대조로v3 x위치/하단seam개수수정.7가로course·18세로segment,약한row12..20내부사선은새structuraljoint로세지않고재질로유지. source trough오차최대.5px,outputanchor최대.2px이하검사. source중앙/하단파손2영역보존.
- 495 원본구역별Photo재질안쪽재투영+원본평균색/직선mortar,26영역1회coverage. thinmortar고주파±6이shape를바꾸지않음. v1/v2출력그대로보존하며실패이유명시,최종v3만후보.
- 533 v1 source-chroma contour는뭉친흰덩어리,v2수동곡선1.25px는너무얇아불채택. v3수동4cubic곡선에각±.85source px범위위치보정과공유폭fitting→1.967692px. 좌우동일복제아님. sourcey109/124직선border,상단104행Photo RGBA정확,하단은원본salmoncleanplate+기존Photo잔질감.
- 원본whiteclass259,Photo203,v2 150,v3 225;classIoU .784/.543/.710,RGBMAE9.98/15.39/11.80. Photo전체white가과다라는해석은정정. v3는같은pairedscroll을깨끗한벡터곡선으로재작화한정적후보이며Photo보다pixeloverlap높다고주장안함. 원본고해상도정답/alpha증거아님.
- source3+비교12=15페이지직접검수. 전체6파생중v1masonry1무효,나머지5finite/원본·부모·SVG/render/base/recipe RGBA재현/alpha255검사. 최종qa/field_geometry007_review.json. 기존100후보/다른574fieldgroup/전투·20key팩보호파일불변.
- field102후보/46보류/203미처리,local145+directGPT3=148처리그대로. 고유local402/외부전용포함405. 설치/실게임/최종ZIP미완료;GUI복구증거없어실행/검은캡처반복없음.
- 다음496cornice·blockjoint·하단기울기판구조,456/465/466/473줄눈은원본좌표확인후구성,525motif·29·37/38기존보류/전체잔여원본범위계속. outputs/field-geometry007/벽돌_줄눈과_장식_곡선_수정.png.


## 2026-09-23 — FIELD-GEOMETRY-008 / 체크 경계·색·투명도와 건물 모서리
- 이전007 progress. 이번 신규5원본 중 로컬4종/실제RGB추론14회, 직접geometry-only1종. 외부생성0/alpha추론0. 전체목표active.
- 394/430/444 두 로컬모델6출력 모두 보류: 평면 체크가 볼록한 타일·그물·흠집으로 변형됨. 430원본 체크는 잘린우하단포함4영역으로 이전3영역기록정정. 444도4영역, 동일소비자증거아님.
- 498 4칸 각각 Gaussian.35/reflect8source padding→실제local4x→crop→칸별Lanczos2x→원본RGB평균보정. WDN 채택, Photo 내부벽돌/단차형태과해불채택. 경계/위상 정확, 평균RGB채널오차0.5미만이며RGB완전동일은아님.
- 489 4x4 직접원본도형. 금색RGBA255/209/105/255 정확, 붉은칸은 원본alpha64/칸별bilinear. alpha원본NN8x정확, goldmask32768픽셀,16칸1회coverage. 회색이라는 이전표시는배경합성영향이라정정. 새AI아닌직접geometry-only1종.
- 496 v1 원본median단면3띠/11선은 재질을평평한음영띠로바꿔실패. v2 원본anchor로기존Photo좌표보정은재질보존/가로선개선됐으나하단왼모서리에새삼각꺾임. 둘불채택/기존held유지. 다음은교차모서리·양인접선을함께맞추며 grain추가/독립띠warp반복안함.
- 출력11(로컬8+4891+4962) source/model/input/native/output/vector/mask/frozenprogram해시와저장recipeRGBA재현. source/비교28페이지중25직접검수, v1실패후중복하단3미검수. raw489별도직접검수. qa/field_geometry008_review.json authoritative. 보호5파일/관측팩22파일/기존102후보/다른570fieldgroup불변.
- field104정적후보/49보류/198novel미처리. local149+directGPT-only3+geometry-only1=153처리, field문맥미처리423에는battle동일225포함. 전체고유local406. 모든방식title1+battle258+novelfield153=412. 이전405는역사적battlegeometry-only2(BM200/BM269)누락한합계였으며이번신규는5종이지7종이아님.
- 설치/실게임검수/최종ZIP미완료,전체완료율미산정. 잔여field·battle43·인물/적/효과/컷신및미지원원본계속. GUI복구증거없어컴퓨터유즈실행/검은캡처반복없음. 사용자이번묶음마무리ETA15~30분안내,전체ETA확답안함.
- 다음394/430/444체크sourcegeometry,496corner연결구조및기존29/37/38·masonry구조보류와잔여field198. outputs/field-geometry008/체크_경계와_재질_수정.png.


## 2026-09-23 — FIELD-GEOMETRY-009 / 장식 체크3종 복원
- 이전008 progress. 이번3기존held source검토/9재구성출력으로progress. 신규원본·로컬추론·외부생성0. 전체목표active.
- 394 큰격자 source강도에bounded affinefit. v1 재질너무부드러움→v2 source칸내RGB+WDN잔질감σ6/gain.85/±9, v3 아주작은off-axis항0으로고정해 정확한수평수직·90도. v3정적후보. 원본칸별색/먼지유지하며 AI베벨·과장균열제외.
- 430/444 v1은찢긴조각외곽기울기를내부격자로오인해잘못기울임. 원본밝은칸peak초기값으로v2수정:각격자는거의축정렬. v2상단우측처리범위가왼/윗쪽온전한체크조각누락→v3확장. 4조각전체확대검수후두v3정적후보.
- 444는430의halfscale geometry를별도원본색으로재구성. 외형유사성이소비자동일증거아님. 원본별core격자계수9영역모두부호유지,최종/source비.70..1.20검사. 444네영역실제.78..84로WDN의대략절반보존보다개선되나정확한source대비아님.
- 9출력source/PTM/parent/vector/mask/maps/frozenprogram/output해시·RGBArecipe재현·mask밖parent정확·alpha255보존. source/좌표/격자overlay/비교35페이지중34직접검수,394auditv2는본v1과동일hash라중복열기생략. 기하guideSVG의흑백은진단용이며최종색/위상은원본RGB에서옴. 처리polygon에걸친cell목록은전체원본파손칸수의증거아님.
- field107정적후보/46보류/198novel미처리. local149/directGPT-only3/geometry-only1/전체153원본그대로,전게임현재조사범위local406/allroutes412유지. 기존104후보/다른573fieldgroup/보호5파일/팩22파일불변. qa/field_geometry009_review.json authoritative.
- 전체게임완료·설치·실게임·최종ZIP미완료. 다음496모서리와양인접선통합,456/465/466/473줄눈·29/391/396/407기계·37/38원근구조·잔여field198/battle43/나머지캐릭터적효과컷신. GUI복구증거없어에뮬/검은캡처반복안함. outputs/field-geometry009/장식_체크_3종_복원_비교.png.


## 2026-09-23 — FIELD-GEOMETRY-010 / 건물 패널 모서리 통합 보정
- 이전009 progress. 이번기존496보류1종해결과잔여198route정리로progress. 새로컬추론·GPT·고유원본0. 전체목표active.
- 008개별strip보정은왼모서리삼각pinch,median단면은재질평탄화로불채택했던것. 이번원본11segment/sharedcorner를하나의2D최소제곱변위로해석. v1 외관은나아도Jacobian<=0픽셀1376/min-1.65168이라불채택.
- v2같은field를nativeσ3부드러운velocity로바꾸고경계16pxfade/7회scaling-squaring 적분. 합성map전체finite-gridJacobian최소.33748/접힘0,최대이동1.39323source px. 물리연속공간/실게임증거아님. 기존Photo재질좌표만이동하며painted단면안씀.
- 원본오른사선은판윗변보다위sourcey94까지이어짐. 완전닫힌정상trapezoid로자르지않고연장유지. 왼상단모서리/인접선sharedtarget로함께보정. 7비교페이지전체직접검수후v2정적후보.
- 11선내부(endpoint3source px제외)grayscale극값sourceguide RMS모두감소. upper-left.129→.054,recess.102→.052,plate-left.478→.277,plate-right.358→.200,plate-top.359→.293,plate-bottom.772→.305,lower-left.960→.380source px. 미세재질/원본모호성잔여이며모든RGBpixel완벽직선주장안함.
- 두출력source/PTM/parent/previousfailure/vector/mask/maps/frozenprogram/output해시·RGBArecipe재현·mask밖parentRGBA정확·alpha255. 전체18source/비교중14직접검수,수치fold실패v1중복4미검수. qa/field_geometry010_review.json authoritative.
- field108후보/45보류/198novel미처리. local149/directGPT-only3/geometry-only1/전체153그대로. 전체조사범위local406/allroutes412. 기존107후보/다른575fieldgroup/보호5파일/팩22파일불변.
- 남은198은alphaornament17/alphamechanical16/flatgeometry14/identitytext11/architecture10/alphafoliage9등구조·투명도·원화보호대상. qa/field_pending_routing010.json에전체ID/classification보존. 다음9alphafoliage로컬RGB비교+원본alpha별도/양배경/줄기·구멍검수,나머지45보류/198원본·battle43·기타게임범위계속.
- 설치/실게임/최종ZIP미완료,GUI복구증거없어에뮬/검은캡처반복없음. outputs/field-geometry010/건물_패널_모서리_수정.png.


## 2026-09-23 — FIELD-FOLIAGE-006 / 로컬18출력 중간 시각검수
- 사용자 퍼센트 질문: 확정된 battle284+novel field351=635종에서 정적후보349(약55%), 한번 이상 처리411(약65%). 전체 게임 완료율이 아니며 설치/실게임 검수 미완료.
- foliage9종 로컬RGB18회는 이미 완료. 이전 직접검수7페이지에 이번11페이지를 더해 원본/WDN/Photo 양배경 비교18페이지 전부 직접검수. 저장input/alpha/native-full/native/output와 비교페이지hash 전부 raw기록과 일치.
- 신규 선정0. 314/325의 수관이 갈라진 평면으로 바뀌고, 290/301의 잎은 둥글고 왁스 같음. 312/318/320도 연속 얼룩/돌 같은 과장 입자로 보임. 316/317은 상대적으로 나으나 줄기의 평평한 블록 해석이 남아 보류. alpha 연결/구멍 수 검사가 재질 품질의 합격 근거는 아님.
- qa/field_foliage006_visual_check.json에 9종 판정/18페이지 검수와 다음 가설 기록. raw local report는 불변. catalog 미확정이므로 field108후보/45보류/198미처리 등 최종 집계 그대로; 이 9종을 최종집계에 중복 추가하지 않음.
- 다음 실행: 290/314 대표원본에서 nearest-opaque hidden-RGB 채움 대신 원본 RGB/matte를 모델에 제공하는 변경가설을 같은 WDN/Photo로 비교. 원본 alpha 별도 보호, 잎끝/수관/줄기와 밝고 어두운 배경 확인. 전처리가 원인이라는 확정 아님. 그래도 미달이면 다른 local prior 또는 source-guided 직접재작화로 전환. 전체목표 active, 에뮬실행/설치/새키 변경 없음.


## 2026-09-23 — FIELD-FOLIAGE-006 / 식물9종·재작화와 밀도 조정
- 이전 중간검수 turn은 progress. 이번 원본 RGB/matte 비교4회와 SwinIR/Anime6B4회 추가, 기존18회 포함 실제 로컬RGB26회/신규9원본. 로컬26출력은 잎 뭉개짐·돌/평면 해석·ringing 등으로 모두 불채택. 입력/모델/native/crop/resize/원본alpha9recipe 재현 검사.
- built-in image_gen 실제3회: FM0290 2안,FM0314 1안. prompt/raw/reference 해시와 원본을 workspace/gpt-trials에 보존. 290 첫안alpha질량 원본의.84236, 둘째1.18580이라 둘다통째로불채택. 두그림의 signed-distance 윤곽을 직접조정한v3는 질량비.99999929/4주요끝 y변화0,x최대.1source px. 양배경 전체/잎끝/하단 직접검수후 정적후보1종.
- 290v3의세부잎·구멍·alpha는새재작화이며원본pixel/topology동일아님. source-scale maskIoU.866327/289샘플상이. alpha128에서2덩어리모두하단접촉,높은threshold에작은분리조각. 이는실게임alpha-test증거아님. 버려진로컬26의sourcealpha보존검사와선택GPT파생alpha를혼동하지않음.
- 314재작화는잎/나무껍질재질개선됐으나줄기위치/하단배경변경. 원본지면3행복원2안은pixel단차,sourcealpha재적용은잎을둔한덩어리로잘라불채택. 314포함나머지8종보류. 다음원본줄기/분기/하단배경영역정의후재질만대응영역으로전사;추가무작정model/grain강도반복안함.
- 전체33출력 lineage/recipe검증,새후보290v3/보류8. qa/field_foliage006_review.json authoritative. 기존108후보/다른567group/보호5파일/20key팩22파일불변. raw기록은변경안함.
- 현재field158local+3directGPT-only+1geometry-only=162처리,109정적후보/53보류/189novel미처리. context미처리414에는battle동일225포함. 전게임현재조사범위local415/allroutes421. GPT3회는local9와겹치므로고유원본추가안함. 설치/실게임/전체게임완료/최종ZIP미완료,전체목표active.


## 2026-09-23 — FIELD-FOLIAGE-007 / 나무4종 원본 구조·잎과 나무껍질
- 기존314/316/317/325 보류4종을 원본별 색·alpha·잘림·하단 배경으로 재구성. 새고유원본/로컬추론/GPT호출0. 이전006 실제 GPT314 재질과 각 로컬Photo를 사용하므로 순수로컬 AI 확대라고 표시하지 않음.
- 원본 좌표 수관경계와6재질방향 track, 본인source색분류로 나무껍질 범위 제한. v1 좁은재질띠/branch누락, v2 분할좌표늘림의 줄무늬 실패. v3 native donor-scale affine+분기 weighted blend로 해결; v4 본인palette대비/threshold,투명donor RGB배제·검증leafbank로 가장자리재질 보완. 최종v4 네종 정적후보.
- 316/317 source분류 공통하단19픽셀씩314와상이,325는0. 각자마스크사용하며 소비자동일/원본전체동일 주장안함. 7출력 frozenrecipe RGBA재현·원본/PTM/부모/model/GPTraw/prompt/reference/vector/mask/outputhash 검증. source/비교45페이지중41직접검수,v2실패후중복4미검수;donor crop2별도검수.
- source센터alpha8배phase4정확,총alpha질량비.9994263/.9996350/.9999956/.9992547. BOX원본규모IoU.999303/.999010/.998973/.999097이며7/11/10/9샘플상이. 미세edgevariation으로alpha128분리조각/구멍수는원본과다름;source센터없는작은조각최대6출력픽셀,source센터포함구성도분리가능. static수용/실게임alpha-test미검증,완전topology보존주장안함.
- 수관아래alpha,원본좌하단(0,108)-(28,128),마지막3source행RGBA는부모정확. 재질방향6개는총나무개수의증거아님. qa/field_foliage007_review.json authoritative;다른572fieldgroup·기존109후보·보호5파일·20key팩22파일불변.
- field113정적후보/49보류/189novel미처리. local158+GPT-only3+geometry-only1=162처리유지,전체조사범위local415/allroutes421유지. 확정battle284+novelfield351=635에서354후보55.75%,한번이상420처리66.14%. 전체게임완료율아님. 설치/실게임/최종ZIP미완료,전체목표active.
- 다음foliage301/312/318/320 원본별재질수정,기존기계/건축보류·field189/battle43·인물/적/효과/컷신및미지원원본. GUI복구증거없어에뮬실행/검은화면반복없음. outputs/field-foliage007/나무_잎과_껍질_재질_수정.png.


## 2026-09-23 — 사용자 요청 일시정지 / 4K 애셋 리마스터 Git 체크포인트
- 사용자 한도 사유로 재작화 목표paused. 신규애셋생성/추론/후보선정중단. 마지막완료FIELD-FOLIAGE-007 집계유지(known635중354정적후보/420처리;field113후보49보류189미처리).
- FIELD-FOLIAGE-008 GPT실제3회(301/312/320),색조·밀도보정파생4종(301/312/318/320)저장. raw비교8페이지는직접검수; 최신material-v1비교12페이지/후보4종은시각검수전이며catalog에반영하지않음. 최신작업프로세스는정상종료.
- qa/paused_checkpoint_20260923.json에해시/지시문/출력/재개단계보존. 다음은사용자가재개한뒤12비교페이지검수→필요한수정과frozenrecipe검증→후보/보류반영. alpha총량일치만으로합격처리하지않음.
- 기존black-rock-shooter-hd-retexture Git저장소에asset-remaster 체크포인트로정리. 원본ISO/무가공추출/모델가중치/에뮬레이터/세이브는기존로컬에보존하며Git에포함하지않음. 프로젝트명4K애셋리마스터;현PNG전체가4096해상도라는의미아님.
