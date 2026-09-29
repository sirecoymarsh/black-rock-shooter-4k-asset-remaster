# 원본 디자인 계승 아이콘 비교본

ICO-001..061의 61묶음, 원본 동형 자산 95개를 다룹니다. 공통 버튼·무기·상태·훈장·조준·필드·미니맵·갤러리 표식입니다.

원본 좌표·색을 기준으로 로컬 업스케일과 도형 보정을 조합했습니다. 모든 아이콘을 손으로 그렸다는 뜻은 아닙니다. 선형 캔버스 8배이며 각 아이콘이 4K라는 뜻도 아닙니다.

정적 183검사, 별도 패딩 2종, 18페이지 144영역 비교, 캐시에서 재조합한 81PNG 바이트 동일성을 확인했습니다. 실게임 설치·실행 검증은 하지 않았습니다. 관측된 아이콘 키와 원본 바이트에서 계산한 후보 키는 QA 보고서에서 구별합니다.

최종 UI 전용 델타: workspace/ui-icons-001/ready-ui-overlay
기존 번역을 포함한 243키 / 81PNG입니다. 최신 배경 팩의 전체 textures.ini를 과거 INI로 덮어쓰지 말고 textures-fragment.ini의 해당 키만 병합해야 합니다. 타이틀 v2 동봉 ISO 조건은 유지됩니다:
workspace/ui-title-ko-002/BRS_UI_title_v2.iso
SHA256 a923932df5b5eb09e692866a4328f8c8bf8fa7a6eef9ddc6965cc4046ae1e572

이 폴더의 atlas-trial, line-sr, classical-sr, binary-sr 파일은 과정 중 시험입니다. 최종 확인은 index.html과 comparison-01..18.png, 최종 배포 파일은 ready-ui-overlay의 manifest 참조 파일만 사용합니다.
