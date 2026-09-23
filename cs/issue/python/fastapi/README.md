# python/fastapi — 실행 모델·응답 경계

FastAPI·Starlette의 실행 모델과 응답 경계에서 나오는 패턴이다.\
공통 원리: **프레임워크가 핸들러 밖에서 하는 일(스레드 배치·검증 오류 응답·WebSocket 프로토콜)도 계약의 일부다.**

## 공통 원리

```
  요청 ──▶ 미들웨어(LIFO) ──▶ 검증 ──▶ 핸들러 (def=스레드풀 / async def=루프)
                               │           │
                               ▼           ▼
                   프레임워크가 만든 응답   내가 만든 응답
                   (422·404·500)            (봉투 계약)
                         └── 봉투 정규화가 없으면 계약의 구멍
```

## 패턴 카드

- [handler-execution-model](handler-execution-model/) — FastAPI에서 `def`는 스레드풀 병렬, `async def`는 이벤트 루프 단일 스레드에서 실행되고 미들웨어는 LIFO다 — 실행 모델에 맞춰 동기 I/O·check-then-act·요청 스코프를 배치한다.
- [response-normalization-framework-boundary](response-normalization-framework-boundary/) — 프레임워크가 핸들러 밖에서 만드는 응답(검증 오류·필터 예외·미처리 예외)이 계약의 구멍이다 — 구체 예외 타입별 핸들러로 봉투를 정규화한다.
- [websocket-api-contract](websocket-api-contract/) — Starlette/FastAPI WebSocket은 타입 특화 수신·타입 힌트 DI·비이터레이터 프로토콜이라 다른 라이브러리 관용구가 그대로 통하지 않는다(TestClient는 이 경로를 우회).
- [yagni-dead-contract](yagni-dead-contract/) — 예측으로 예약한 계약은 유지비만 든다 — YAGNI로 제거하고 결정 흔적만 남긴다.

> 이 폴더의 메타 태그: `resource-bounding`(1) · `contract-drift`(2) — 태그별 전체 목록은 [cs/issue 태그 역인덱스](../../README.md#태그-역인덱스).
