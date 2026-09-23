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
