# PPSSPP API 근거

2026-09-22에 공식 v1.20.4 소스에서 다음 파일을 읽기 전용 참조로 가져왔다. 각 파일의 GPL 저작권 고지는 원문에 보존되어 있다.

- https://raw.githubusercontent.com/hrydgard/ppsspp/v1.20.4/Core/Debugger/WebSocket/GPUBufferSubscriber.cpp
- https://raw.githubusercontent.com/hrydgard/ppsspp/v1.20.4/Core/Debugger/WebSocket/GameSubscriber.cpp
- https://raw.githubusercontent.com/hrydgard/ppsspp/v1.20.4/Core/Debugger/WebSocket/SteppingSubscriber.cpp

입력 API는 같은 태그의 `InputSubscriber.cpp`, CPU 중단/재개 이벤트의 무응답 특성은 로컬 PPSSPP 1.20.4 `assets/debugger/static/js/main.fe87e942.js.map`의 `sdk/ppsspp.js` 및 `components/CPU/DisasmButtons.js`에서 확인했다. 호스트 메모리스틱 경로 선택은 `Windows/main.cpp`의 `installed.txt` 처리에서 확인했다.

관련 공식 문서:

- https://www.ppsspp.org/docs/reference/texture-replacement/
- https://www.ppsspp.org/docs/reference/command-line/
- https://www.ppsspp.org/download/
