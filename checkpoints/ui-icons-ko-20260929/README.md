# 4K 애셋 리마스터 — 원본 디자인 계승 아이콘·한글 UI

2026-09-29 작업 체크포인트. ICO-001..061의 61묶음(원본 동형 95개)을 원본 형태·색·굵기에 맞게 보정한 최종 아이콘과 기존 한국어 UI를 보관합니다. 최종 델타는 243키/81PNG입니다. 선형 8배 제작이며 모든 이미지가 4096픽셀이라는 뜻은 아닙니다.

이 체크포인트에는 최종 UI 델타, 제작 코드, 소비한 합성 캐시, 번역/검수 매니페스트, 18페이지 비교표, 타이틀 v2 ISO 차분 패치가 포함됩니다. `review/index.html`에서 비교합니다. 모델 가중치, 원본 ISO, 무가공 게임 추출물, 세이브, 에뮬레이터는 포함하지 않습니다.

한국어 문구 작성: `translator_model: Codex internal`. 아이콘 후속 작업에서는 기존 한국어 픽셀을 보존했습니다. Orbit Regular는 SIL OFL 1.1이며 저자와 라이선스는 `licensed-font/orbit/OFL.txt`에 있습니다.

## 검증 상태

183개 기본 정적검사, 패딩 변형 2종, 18페이지 144영역 비교, 캐시 합성 재빌드의 81PNG 바이트 일치 통과. 아이콘 연결 225키 중 실관측 38키/계산 후보 187키입니다. 키 수가 고유 아이콘 수나 실게임 전 상태 검증 수를 뜻하지 않습니다.

실게임 화면·상태 전환 검증은 아직 하지 않았습니다. 튜토리얼 내부 스크린샷과 PSP 시스템 저장 화면은 별도 범위입니다. `qa`의 원래 검수 기록은 설치 전 증거이므로 수정하지 않았습니다. 이 체크포인트의 실제 설치 결과는 `installation.json`을 확인합니다.

## 적용과 복구

에뮬레이터를 종료하고, 기존 부스터 정상 작동 통합본을 대상으로 실행합니다. Python 3.10 이상 표준 라이브러리만 필요합니다.

```powershell
python apply_checkpoint.py "P:\AI\Codex\projects\black-rock-shooter-hd-retexture\release\combined-test-20260924-001005"
python apply_checkpoint.py "P:\AI\Codex\projects\black-rock-shooter-hd-retexture\release\combined-test-20260924-001005" --apply
```

첫 명령은 읽기 전용 사전검사입니다. 둘째 명령은 `ui-backups`에 ISO/INI/실행 매니페스트를 백업하고, 타이틀 전용 차분을 적용한 뒤 최신 INI의 해당 243키만 병합합니다. 기존 PNG·다른 키·INI 설정 보존을 검사합니다. 전체 INI를 이 체크포인트의 파일로 덮어쓰지 마세요.

지원 입력 ISO SHA-256: `b162f45f10622992a4fd068b8414008cd7f455c7c9b203c1c610554d43de9b21`

출력 ISO SHA-256: `a923932df5b5eb09e692866a4328f8c8bf8fa7a6eef9ddc6965cc4046ae1e572`

부스터 수정·다른 ISO 바이트는 보존합니다. 이미 적용되었거나 다른 ISO면 해시 검사로 중단합니다. 복구하려면 에뮬레이터를 종료하고 설치 기록의 백업 폴더에서 ISO와 `build-manifest.json`을 통합본 루트로, `textures.ini`를 `memstick/PSP/TEXTURES/NPUH10126`으로 복사하세요. 추가 PNG는 이전 INI에서 참조하지 않으므로 남겨도 됩니다. 설치 후 다른 작업이 추가되었다면 전체 롤백 전에 그 작업을 보존해야 합니다.

## 제작 재개

`historical-tools`는 당시 로컬 경로/입력에 의존하는 제작 코드입니다. 단독 실행형 빌드 도구가 아닙니다. 로컬 작업 루트 `P:\AI\Codex\projects\black-rock-shooter-hd-ui-fonts`와 해시가 일치하는 원본 추출물, 이전 단계 팩, 모델 환경이 필요합니다. 원본은 Git에 포함하지 않습니다. `composition-cache`는 최종 합성에 소비한 결과와 캐시 메타데이터만 보관하며, 무작위 재추론의 동일성을 보장하지 않습니다.

다음 단계는 적용한 통합본에서 타이틀/공통 아이콘/메뉴/훈장/조준/미니맵 상태별 화면과 부스터 복장 회귀를 확인하는 것입니다.
