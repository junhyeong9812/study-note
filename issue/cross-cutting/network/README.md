# network — 프로토콜·연결·프록시·서브넷

HTTP/TCP의 경계와 중간 장치(프록시·터널)에서 터지는 부류. "라이브러리가 대신 처리해 줬다고 믿은 것"이 실제로는 규격 불일치였던 이슈가 많다.

| 패턴 | 한 줄 | 사례 이슈 |
|------|-------|-----------|
| [chunked-vs-content-length](chunked-vs-content-length/) | chunked transfer-encoding vs Content-Length 불일치 → 0바이트 | be12 · ci-cd4 |
| [http-streaming-status-locked](http-streaming-status-locked/) | 200 헤더 전송 순간 status 확정 → 스트림 시작 후 오류코드 못 바꿈 | llm6 · be12 |
| [bind-address-loopback-vs-lan](bind-address-loopback-vs-lan/) | fail-closed 바인딩(LAN only) vs 헬스체크 127.0.0.1 → 정상인데 unhealthy | be9·1 · ci-cd3 |
| [proxy-passthrough](proxy-passthrough/) | 프록시 버퍼링·status 보존·쿠키 양방향 왕복 안 하면 스트림·세션이 깨짐 | front3·11 |
| [reverse-tunnel-nat-traversal](reverse-tunnel-nat-traversal/) | 서브넷 라우팅 단절 → 연결 방향 역전(역SSH터널+socat) | ci-cd4 |
