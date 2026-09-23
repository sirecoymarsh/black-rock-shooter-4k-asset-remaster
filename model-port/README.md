# 블랙 록 슈터 얼굴·의상 모델 이식 — 개발 체크포인트

2026-09-24 부스터 유닛 PGR 모델의 실제 로딩과 사용자 동작 확인을 반영했습니다. [정상 로딩 확인본](../checkpoints/booster-working-20260924/README.md)과 [STATUS.json](STATUS.json)이 현재 상태입니다. 이동·전투·장시간 검증은 남아 있습니다.

## 보존한 결과

- 퍼니싱 기본 외형의 얼굴·눈·머리·몸·코트·지퍼: 15,846정점, 18,863삼각형을 PSP 47개 관절에 맞춘 변환 데이터.
- PSP INSM/SC 모델 해석·재작성 도구와 `FCHR_P_BRS02_pgr_candidate.BIN`. 현재 교체 대상은 **부스터 유닛**입니다.
- 양쪽 원본 및 변환 후 정적 미리보기, 참고 GLB 2종, 사용한 컬러 텍스처와 재질 설정.
- 이전 PSP 부스터 의상용 2048×2048 텍스처 보정본과 실제 GPU 업로드 확인 기록.

## 확인된 범위

원본 모델을 재작성한 시험판은 부스터 유닛으로 변경했을 때 게임에 정상 표시됐습니다. 재작성 INSM 전체가 게임 메모리의 두 위치에서 바이트 단위로 일치했습니다. 근거는 [reencoded-consumption.json](records/runtime/reencoded-consumption.json)입니다.

퍼니싱 후보는 파일 구조·정점·가중치·텍스처 인코딩과 정적 미리보기를 확인했습니다. 머리카락의 알파 임계값은 원본 PGR 재질의 `_Cutoff=0.1`에 맞췄습니다. 2026-09-22 18:55에 후보 시험판을 실행했지만 사용자 Esc로 조작이 중단되어 **당시에는 실제 후보 모델 표시·이동·전투가 미검증**이었습니다. 2026-09-24 메모리 v2 수정 후 전체 모델의 RAM 바이트 일치와 사용자 동작 확인을 완료했습니다. 직접 화면 캡처와 이동·전투 검증은 남아 있습니다. 과거 기록의 '원본 재작성 검증 전' 상태는 이 문서와 STATUS.json으로 정정합니다. 보존한 `records/runtime/*-reencoded.json`의 `tested:false`는 실행 시 초기값이며, 최종 판정은 이후 생성된 `reencoded-consumption.json`을 따릅니다.

## 미리보기

`viewer/Model_port_preview.html`을 브라우저에서 열고 **PSP 변환 후보**를 선택하면 저장된 PSP 파일을 다시 읽어 만든 정적 외형을 볼 수 있습니다. HTML에 필요한 코드·텍스처가 포함되어 있습니다. 원본 툰 셰이더, 조명, 표정, 애니메이션은 재현하지 않았습니다.

`viewer/*_static_reference.glb` 두 파일은 PGR 원본 참고 모델입니다. PSP용 스킨·애니메이션을 가진 게임 교체 파일이 아닙니다. `geometry/pgr_on_psp_skin.json`에 PSP 관절로 변환한 스킨 데이터가 있습니다.

## 남은 작업

- 새 PGR 파일의 전체 RAM 소비 확인은 완료했습니다. 이후 검증에서는 성공 ISO 해시와 64MiB 설정을 유지합니다.
- 메뉴·필드 이동·전투에서 관절, 코트·머리카락 간섭, 무기 연결, 메모리 여유를 검증합니다.
- PSP용 256×256 팔레트 텍스처와 별도로 원본 크기 PNG(얼굴/몸512,코트/머리1024)의 실제 고해상도 교체를 연결·확인합니다.
- PGR 표정 블렌드셰이프는 아직 이식하지 않았습니다. 손가락·보조 관절과 코트·머리카락 연결은 PSP 관절 수에 맞춰 단순화됐습니다.

## 재개에 필요한 파일과 도구

`tools/`는 작업 시점 스크립트의 정확한 사본입니다. 원래 P: 작업 경로와 외부 로컬 아카이브 경로를 유지하므로, 다른 컴퓨터에서 바로 실행하거나 실행 스크립트를 자동 호출하면 안 됩니다. 전체 로컬 작업 공간은 `P:/AI/Codex/projects/black-rock-shooter-hd-retexture`입니다. Python의 Pillow/numpy/msgpack/UnityPy1.24.2와 원래 `workspace/tooldeps` 환경을 사용했습니다. `tools/dependencies/`에는 ISO와 PTMD 형식 보조 코드를 보존했습니다.

처리 순서는 `brs_model_port.py` → `pgr_skin_source.py` → `pgr_retarget_psp.py` → `brs_build_model_candidate.py` → `build_model_test_iso.py`입니다. 뷰어는 `build_port_viewer.py`로 만듭니다. 재빌드는 로컬 원본 PSP 캐릭터 BIN/ISO, PGR 번들 스냅샷 및 별도 로컬 키 파일을 요구합니다. 이미 보존한 변환 결과와 미리보기 확인에는 그 입력이 필요하지 않습니다.

원본 ISO/번들, 복호화 키, 실행기, 세이브, 게임 RAM 덤프는 포함하지 않았습니다. 시험 ISO의 해시는 `candidate/iso_validation.json`에 있고 실제 ISO는 기존 로컬 작업 공간에 있습니다. [snapshot-manifest.json](snapshot-manifest.json)에 각 보존 파일의 원래 위치·SHA-256·크기를 기록했습니다.

사용자 요청에 따른 보존 작업이며, 이 커밋으로 에뮬레이터 검증을 재개하지 않습니다. 메뉴·폰트·다른 애셋 작업은 저장소의 `asset-remaster/`에서 별도로 관리합니다. 모델·원본 텍스처의 권리는 해당 원작 권리자에게 있으며, 포함된 third-party 코드·문서의 라이선스 표시는 유지했습니다.
