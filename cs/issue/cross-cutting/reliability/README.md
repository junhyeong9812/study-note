# reliability — 신뢰성 (조용한 실패·자원 고갈)

실패가 났는데 **성공 신호가 나가거나**, 자원이 **상한 없이 소진되는** 부류. 실측 최다 사고 유형.

| 패턴 | 한 줄 | 사례 이슈 |
|------|-------|-----------|
| [silent-failure-vs-artifact](silent-failure-vs-artifact/) | 성공 로그·exit 0·202 ≠ 산출물 — 산출물을 되물어 삼켜진 실패를 드러낸다 | be2·10 · front3 · llm1·3 · ci-cd2·3 |
| [resource-bounding-last-defense](resource-bounding-last-defense/) | 클라이언트 타임아웃은 서버측 생성을 못 멈춘다 → 서버 자원 상한이 유일 방어선 | llm1 · be5·12 · front5 · ci-cd1 |
