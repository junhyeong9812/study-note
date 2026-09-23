# cs/issue/python/fastapi/websocket-api-contract — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.

## 전체 흐름

```
[연결 요청] ── HTTP Upgrade ──▶ FastAPI 라우팅
                                  │
               ┌──────────────────┴───────────────────┐
               │ ① 엔드포인트 인자 DI (타입 힌트로 해석)   │
               │    ws: WebSocket  → 주입 OK            │
               │    ws (힌트 없음) → 주입 불가 → 403 💥   │
               │    (TestClient 는 이 경로를 우회 → 통과)  │
               └──────────────────┬───────────────────┘
                                  ▼ accept
               ┌──────────────────────────────────────┐
               │ ② 수신 루프                            │
               │    async for m in ws   → __aiter__ 없음 💥│
               │    receive_text()      → binary 오면 예외 💥│
               │    receive() + 타입 분기 → 안전           │
               └──────────────────────────────────────┘

[교정]
   ① 인자에 타입 힌트: async def endpoint(ws: WebSocket)
   ② while True: msg = await ws.receive()  → "text" 만 처리, 나머지 무시
[보조 원인 후보] 프록시 헤더 미들웨어가 WS scope 의 scheme 을 바꿔 403 → 끄거나 WS 구현 교체
```

## 핵심 문장

- "WebSocket"은 라이브러리마다 **다른 계약**이다 — 수신 API·반복 프로토콜·주입 방식이 다르다.
- Starlette의 WebSocket은 **비동기 이터레이터가 아니다** — `async for`가 아니라 `while True: await ws.receive_*()`.
- `receive_text()`는 **text 프레임 전용** — 외부 입력 루프는 `receive()`로 받아 타입을 분기한다.
- FastAPI는 WS 엔드포인트 인자를 **타입 힌트로 주입**한다 — 힌트가 없으면 핸드셰이크가 403.
- TestClient는 실제 서버의 주입 경로를 우회할 수 있다 — WS는 **실제 클라이언트로 한 번 붙어 보는 것**이 검증이다.
