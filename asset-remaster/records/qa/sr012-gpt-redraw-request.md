# BM110 GPT 재그리기 요청과 판정

- 도구: built-in image_gen. 외부 이미지 편집 1회이며 로컬 모델 추론으로 세지 않습니다.
- 원본: `workspace/source/battle_maps/map_b_stg02_03.vol/001_map_b_stg02_03.bin/025.png`
- 원본 RGBA SHA-256: `9f0f8f1cfc6ea3c7d8bc958b9ce335926ba88439f9159f86c8a78abbb69eb250`
- 보존한 결과: `workspace/manual-redraw/sr012/BM110-gpt-redraw-rejected.png`
- 결과 SHA-256: `332bc1245d937c3f7499654529d799813ec08cb7bb59c194160a61074a2ff87b`
- 판정: 미채택. 격자 선의 개수/간격, 원형 중심부와 지지대, 원본의 배치가 바뀌었습니다. 생성 크기1774×887, 축소 alpha128 IoU0.8425656. 자세한 검사는 `qa/local_sr012_manual_grille.json` 및 `qa/local_sr012_review.json`에 기록했습니다.
- 대체 후보: Codex가 직접 작성한 SVG 격자/중심부 + 로컬 WDN 외곽 재질 + 원본 명암. `workspace/manual-redraw/sr012/BM110-codex-grid-and-fastener-v3.png`. 실제 게임 표시는 검증 전입니다.

## 실제 요청문

Use case: precise-object-edit. This is a production game texture remaster, not concept art. Edit target: the supplied 64×32 RGBA texture atlas, showing a cropped rectangular metal ventilation grille on the left and a circular mechanical medallion on the right. Redraw it sharply at 8× resolution, ideally 512×256 pixels, with exactly the same 2:1 canvas and normalized positions. Preserve all of the original geometry and original subdued charcoal / medium-gray metal palette. Left grille is intentionally clipped at the internal x=32 source-pixel boundary: do not invent a right border. Trace every visible original horizontal and vertical slat: identical count and positions, thin straight lines, no bent bars, no removed lines, no pseudo-text. Right object: accurately trace the circular outline, concentric circular tracks, four cardinal dark supports and small irregular central fastener, with restrained original shading; do not redesign as a new emblem, logo, alien face, or wheel. Keep the source margins and gap exactly, do not enlarge or re-center the objects. Very restrained surface detail only, no scratches or chrome highlights that aren't in the source. All pixels outside the two original silhouettes must have real transparent alpha, not a white, black, gray or checkerboard background. No shadow outside silhouettes, no text, no labels, no border. Output only the actual texture atlas. The source's geometric layout is authoritative; crisp legible design fidelity matters much more than speculative realism.
