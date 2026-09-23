# 런타임 텍스처 수집 및 인벤토리

## 고정 기준

- 대상: NPUH10126, 한국어 패치 v1.0.1.
- ISO SHA-256: `525b5d2b7d8f4723be25b026e72b69d07d30c2cf84d8a48235577ca3728fc92a`.
- 실행기: PPSSPP v1.20.4. 실제 경로·실행기 SHA-256·원본 저장 데이터 해시는 `qa/evidence/environment.json`이 기준이다.
- 최신 생성 후보 `runtime_hotfix_20260824_rc1`의 ISO(`2a6f6f55...`)는 공개 v1.0.1 타깃과 다르므로 사용하지 않았다.
- 원본 ISO, 아카이브 PPSSPP, 기존 배포 ZIP, 원본 저장 데이터는 읽기 전용 입력이다. 프로젝트 실행기와 세션별 메모리스틱만 쓴다.

## 해시 기준

새 세션은 `hash=xxh64`, `ignoreAddress=true`, `reduceHash=false`, `ignoreMipmap=false`로 수집한다. `SaveNewTextures=True`, `ReplaceTextures=False`이며 기존 UI 교체본은 로드하지 않는다. 과거 `quick` 해시를 새 알고리즘 값으로 수학적으로 변환하거나 이름을 추정하지 않는다. 같은 크기의 RGBA 픽셀 전체가 같을 때에만 관측된 두 파일 사이에 내용 동일 관계를 기록한다.

이 선택은 [PPSSPP 공식 텍스처 문서](https://www.ppsspp.org/docs/reference/texture-replacement/)의 권장 사항을 따른다. `quick`과 `xxh64` 변경 시 해시는 바뀐다. 과거 와일드카드 매핑은 검토 후보이며 새 교체팩의 승인된 매핑이 아니다.

논리 ID `TEX-000001` 등의 등록표는 `workspace/inventory/asset_ids.json`이다. 이미지 이동이나 목록 정렬과 무관하게 유지된다. 픽셀이 같아도 서로 다른 출처·세션·PPSSPP 키·밉 레벨은 `observations.json`에서 모두 보존한다. 같은 픽셀 그룹이라는 사실은 같은 UV나 같은 소비 화면을 증명하지 않는다.

## 현재 자료의 의미

- `LEGACY-NEW`: 기존 PPSSPP `new` 폴더. 과거 실제 덤프지만 파일별 ISO·수집 장면은 미확정이다.
- `LEGACY-DONE`: 기존 `done` 폴더. 원본 덤프인지 교체 후보인지 파일별 역할이 미확정이므로 참고 자료로만 취급한다.
- S001/S002: 이번 프로젝트에서 v1.0.1 ISO로 부팅한 세션. 원본 설정 스냅샷과 실제 부팅·저장 로그, 입력 이력이 있다.
- 과거 폴더의 `textures.ini`는 `quick`이다. 이 사실이 과거 모든 파일의 생성 당시 설정을 독립적으로 보증하지는 않는다.
- 화면 읽기 API가 Vulkan과 OpenGL 모두 `Could not download output`을 반환했다. 따라서 실제 장면의 스크린샷·화면 판정은 없다. 텍스처 시트는 덤프 검토 이미지이며 게임 화면으로 취급하지 않는다.
- 초기 안내의 확인 입력을 세 번 보냈다. 게임 메모리 수정이나 세이브스테이트 로드는 하지 않았다. 복사한 인게임 세이브의 전체 진행 범위는 아직 검증하지 않았다.

## 파일 구성

| 파일 | 역할 |
|---|---|
| `workspace/inventory/index.html` | 현재/과거 구분, 해시·ID·크기 검색과 페이지 이동이 있는 로컬 검토 목록 |
| `workspace/inventory/observations.json` | 원본 PNG 경로, 파일 SHA-256, 픽셀 SHA-256, 크기, PNG 모드, 알파 분포, 해시 부분, 밉, 세션 |
| `workspace/inventory/assets.json` | 픽셀 그룹별 논리 ID, 분류, UV·반복·출력 크기·제작법·후보 해시·QA 상태 |
| `workspace/inventory/annotations.json` | 수동 검토 주석. 목록을 재생성해도 보존 |
| `workspace/inventory/crosswalk.json` | 이번 xxh64 덤프와 과거 파일의 픽셀 동일 대조표 |
| `workspace/inventory/baseline_mapping_audit.json` | UI 27장의 원본 매핑, 중복·와일드카드, 관측 파일과의 매칭 후보 |
| `workspace/inventory/errors.json` | 잘못된 PNG/파일명, 키 중복과 픽셀 차이 |
| `qa/evidence/inventory_summary.json` | 기계 생성 집계. 진행 보고 수치의 기준 |
| `qa/coverage.json` | UI/HUD/캐릭터/적/배경/오브젝트/이펙트/컷신 및 지역·경로 수집 범위 |
| `workspace/sessions/*/session.json` | ISO·설정 해시, 저장 데이터 출처, 세션의 검증 범위와 한계 |

인벤토리의 모든 교체본은 현재 `release_eligible=false`다. 원본 크기·알파와 실제 키는 수집됐지만 UV·반복 여부·소비 화면과 제작·출력·후보 해시는 아직 미확정이다. NULL과 unknown을 실제 검증값으로 대신하지 않는다.

## 다음 세션 실행

Windows PowerShell에서 프로젝트의 `tools/Launch-Dump.ps1 -Interactive`를 실행하면, 음소거된 PPSSPP 창과 새 메모리스틱 세션이 생긴다. 이 옵션은 사용자가 화면을 직접 확인하거나 창 표시를 요청한 경우에 쓴다. 옵션을 생략하면 숨김 실행이다. 기존 프로젝트 PPSSPP가 켜져 있으면 새 실행을 거절한다. ISO와 실행기 해시가 바뀌어도 거절한다.

실행 후 `tools/runtime.mjs status`로 게임 ID를 확인한다. `snapshot LABEL`은 현재 덤프 파일 목록만 기록한다. `capture LABEL`은 CPU를 멈추고 프레임 캡처를 시도하며, 실패하면 오류와 덤프 목록을 기록한다. 실패를 성공 캡처로 대신하지 않는다. `resume`은 실행을 재개하고, `press cross`처럼 입력을 보낼 수 있다. 이 도구는 실시간 지연을 사용하므로 정확한 프레임 재현 도구가 아니다.

다음 관측은 창을 표시한 상태에서 초기 안내를 통과해 타이틀을 확인하고 같은 시점의 화면·덤프 목록을 함께 확보하는 것이다. 그 뒤 `qa/coverage.json` 순서로 메뉴, 전투, 지역 1~6, EX/진엔딩, 컷신을 수집한다. 아직 보지 않은 구간을 완료로 표시하지 않는다.

수집 세션 종료 또는 일시 정지 후 `tools/inventory.py`를 실행해 목록을 재생성한다. 런타임은 `qa/evidence/environment.json`의 Python/Node 경로를 사용한다. Pillow 외 추가 Python 패키지는 필요 없다.

## 이번 실행에서 수정한 문제

처음 두 세션에서 `EnableSound`라는 잘못된 키를 바꾸려 했기 때문에 실제 `[Sound] Enable=True`가 남았고 숨김 실행 중 소리가 났다. 두 BRS 프로세스는 실행 파일 경로와 PID·시작 시간을 확인한 뒤 종료했다. 이후 라이브 세션 설정과 재사용 템플릿은 `[Sound] Enable=False`, `GameVolume=0`, `UIVolume=0`, `GamePreviewVolume=0`으로 고쳤다. 수집 당시의 `ppsspp.initial.ini`는 증거로 보존했다. 수정 후 게임을 다시 실행하지 않았으므로 음소거는 설정 검증까지 완료한 상태다.

별도 `fate-extra-psp-korean` PPSSPP 프로세스가 관측됐지만 이 프로젝트의 프로세스가 아니므로 조작하지 않았다.
