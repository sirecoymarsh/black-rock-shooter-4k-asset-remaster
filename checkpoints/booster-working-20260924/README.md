# 부스터 유닛 정상 로딩 확인본 — 2026-09-24

사용자가 성공을 확인한 통합 버전의 보존용 체크포인트입니다. 새 애셋 제작은 일시정지 상태입니다.

- ISO SHA-256: `b162f45f10622992a4fd068b8414008cd7f455c7c9b203c1c610554d43de9b21`
- 부스터 유닛 PGR 모델 전체 INSM 3,109,904바이트가 RAM `0x08cc9750`, `0x0a22d2a0`에서 정확히 일치했습니다. 사용자가 `?되네?`라고 동작을 확인했습니다.
- 직접 화면 캡처는 없으며 이동·전투·의상 반복 변경·장시간 플레이는 아직 검증하지 않았습니다. 전체 게임 완료판은 아닙니다.
- 현재 설치된 정확키 711개와 연결 PNG 711장을 보존했습니다: 폰트 671, UI 17, 배경/타이틀 23. 미관측 글자 배열은 원본으로 표시될 수 있습니다.
- 모델 후보는 기존 `model-port/candidate/FCHR_P_BRS02_pgr_candidate.BIN`과 동일합니다. 메시나 텍스처를 축소하지 않았습니다.

## 원인과 수정

기존 모델 힙 1.5MiB에서 3,605,392바이트 SC 압축 해제 버퍼를 확보하지 못해 NULL에 쓰다가 PC `0x089599ac`에서 멈췄습니다. 모델 힙을 6MiB로 늘리고 공유 로딩 공간 7.5MiB, 상위 힙 28.5MiB, SDK 예약 29MiB를 함께 맞췄습니다. PARAM.SFO의 MEMSIZE=1과 PSP Slim/64MiB 환경이 필요합니다. RVLS의 크기·SHA-1과 설치 데이터도 동일 후보에 맞췄습니다.

네 패치 위치의 원래/변경 워드와 입력·출력 해시는 `records/model-memory-fix-v2-build.json`, 실제 로딩 근거는 `records/model-memory-fix-runtime-proof.json` 및 `records/model-ram-verification.json`에 있습니다. SDK 예약을 늘리지 않은 초기 v1은 부팅 실패본이므로 사용하지 않습니다.

## 현재 실행본과 복원 자료

로컬 실행본: `P:/AI/Codex/projects/black-rock-shooter-hd-retexture/release/combined-test-20260924-001005/게임 실행.cmd`.
정상 ISO와 실행기는 그 로컬 폴더에 그대로 보존합니다. `local-bundle-files/`는 실행 진입점의 사본이며 Git 폴더에서 곧바로 실행하는 독립 게임 배포물이 아닙니다.

`PSP/TEXTURES/NPUH10126/`는 현재 매핑에서 실제 참조하는 파일만 보존한 팩입니다. 기존 실행본을 복원할 때 이 팩을 사용하며, 원본 덤프 `new/`는 포함하지 않았습니다. 354개 후보의 전체 보존본은 기존 `asset-remaster/`에 있고 여기에는 적용된 항목만 들어 있습니다.

`historical-tools/`는 당시 사용한 도구의 정확한 사본입니다. 호스트 경로와 당시 입력 해시가 고정된 조사/빌드 기록이며 자동 재실행하지 않습니다. 특히 최초 통합 빌더와 폰트 빌더는 이전 ISO 해시를 기대하므로 현재 실행본에 다시 적용하지 않습니다.
재구성 단계는 기존 `model-port/` 후보 ISO → RVLS/설치 데이터 동기화 → 메모리 v2 수정입니다. 각 단계 입력은 기록된 해시와 일치해야 합니다. 메모리 빌더는 로컬 PPSSPP의 복호화 EBOOT도 필요합니다. `model-port/tools/dependencies/brs_patch.py`에 ISO/RTDP 보조 코드가 있습니다. 원본 ISO, 복호화 실행 파일, 에뮬레이터, 세이브, 전체 RAM 덤프는 Git에 포함하지 않았습니다.

과거 단계 보고서의 `runtime_pending` 또는 폰트 QA의 `combined_model_runtime_verified:false`는 해당 시점/별도 폰트 시험 범위의 기록입니다. 현재 모델 로딩 판정은 이 폴더의 STATUS.json을 따릅니다.
