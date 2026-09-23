# workflow — API별 처리 흐름·시스템 규약

각 문서: ASCII 흐름도 + 단계별 절차 설명. 코드 위치가 아니라 **요청이 겪는 일** 중심.

| 문서 | 흐름 |
|---|---|
| [sync.md](sync.md) | study-note push → 색인 갱신 (멱등·증분) |
| [content.md](content.md) | 트리·문서·히스토리 조회 |
| [search.md](search.md) | 검색(하이브리드·폴백) + 자동완성(suggest) |
| [deploy.md](deploy.md) | 서비스 push → 자동 배포 (master/agent) |
| [chat-design.md](chat-design.md) | (설계) 우측 채팅 — 세션·스트리밍·에스컬레이션 |
| [streaming-mvc-vs-webflux.md](streaming-mvc-vs-webflux.md) | 방법론 비교 — 스트리밍에 WebFlux가 필요한가 |
| [logging.md](logging.md) | 로그 규약(횡단관심사) — requestId·이중기록(stdout+Redis XADD) |
