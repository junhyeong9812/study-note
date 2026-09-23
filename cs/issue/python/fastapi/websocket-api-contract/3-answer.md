# cs/issue/python/fastapi/websocket-api-contract — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 사건 기록 대조·추상화. 복습 전 읽지 말 것.

태그: `contract-drift`

## 정답
<!-- 질문 1:1 대응 -->

1. **`receive_text()`가 예외를 던지고 입력 루프가 죽는다.** 타입 특화 수신 API는 "text 프레임이 올 것"을 전제로 한 편의 함수라, 프레임 타입이 다르면 예외로 처리한다(Starlette는 받은 메시지에서 `"text"` 키를 바로 꺼내므로 binary 메시지면 KeyError 류 — 버전에 따라 모양은 다를 수 있다). 입력 루프는 보통 예외 하나로 빠져나가므로, 클라이언트가 binary 프레임 하나만 보내도 그 연결의 입력 처리가 멈춘다. 외부 입력은 무엇이 올지 서버가 정하지 못하므로, 루프는 일반 `receive()`로 받아 **메시지 타입을 분기**하고, 기대하지 않은 타입은 버리거나(continue) 명시적으로 거절해야 한다. 고친 뒤 "binary 무시" 테스트로 고정했다.
   > **프레임 타입** — WebSocket 메시지는 text(UTF-8)와 binary로 구분되어 전송된다. 수신 쪽은 둘 중 무엇이 올지 미리 알 수 없다.

2. **Starlette/FastAPI의 WebSocket 객체는 비동기 이터레이터 프로토콜을 구현하지 않기 때문이다.** 서버 로그는 `'async for' requires an object with __aiter__ method, got WebSocket` — `async for`가 쓸 `__aiter__`/`__anext__`가 없다는 뜻이다. 다른 WebSocket 라이브러리의 연결 객체는 이 프로토콜을 구현해 `async for msg in ws:`가 관용구지만, Starlette 객체는 `receive_*()` 메서드를 직접 부르거나, 별도 비동기 제너레이터 메서드(`async for msg in ws.iter_text():` — 연결 종료 시 조용히 끝남)를 쓰는 방식이다. 엔드포인트가 이 예외로 바로 끝나니 클라이언트 입장에선 "붙자마자 끊김"이 반복된다. 교정은 `while True: raw = await ws.receive_text()`(또는 `ws.iter_text()`).
   > **비동기 이터레이터 프로토콜** — `__aiter__`가 이터레이터를 돌려주고, `__anext__`가 다음 값을 await로 돌려주는 규약. `async for`는 이 두 메서드만 호출한다.

3. **HTTP 403으로 핸드셰이크가 거절된다.** FastAPI는 엔드포인트 인자를 **타입 힌트로 해석해** 무엇을 주입할지 결정한다(DI). `ws: WebSocket`이면 연결 객체를 주입하지만, 힌트가 없으면 그 인자를 **필수 쿼리 파라미터 `ws`**로 해석한다. 요청에 그런 쿼리가 없으니 검증 실패 → FastAPI가 accept 전에 연결을 닫고(정책 위반 close), ASGI 서버는 accept 전 close를 HTTP 403 핸드셰이크 거절로 돌려준다. REST 엔드포인트는 정상이라 "WS만 권한 문제"처럼 보이지만, 권한이 아니라 **함수 시그니처가 프레임워크의 주입 계약을 어긴 것**이다. 교정은 `async def endpoint(ws: WebSocket)` 한 줄.
   > **타입 힌트 기반 DI** — 함수 인자의 타입 주석을 보고 프레임워크가 알맞은 객체(요청·연결·의존성)를 채워 넣는 방식. 힌트가 곧 주입 계약이다.

4. **TestClient가 실제 서버의 그 경로를 거치지 않았기 때문이다.** 기록된 결론은 "TestClient는 이 DI 경로를 우회해 실제 서버와 다른 결과를 낸다"이다. 다만 일반론으로 TestClient는 ASGI 앱을 직접 호출하므로 FastAPI의 라우팅·DI 자체는 그대로 거친다 — 우회하는 것은 **ASGI 서버(uvicorn 등)와 네트워크 층**(실제 핸드셰이크 처리·프록시 헤더 미들웨어·WS 구현)이다. 그래서 테스트와 실서버의 차이를 볼 때는 그 층(5번의 보조 원인 후보)을 함께 의심해야 한다. 어느 쪽이든 실제 네트워크 클라이언트가 거치는 단계가 테스트에 포함되지 않았다. 이것은 **테스트가 계약이 아니라 하네스의 경로를 검증하는** 형태의 green 위장이다. WS처럼 연결 수립 단계에 로직이 있는 기능은 실제 클라이언트(브라우저·curl·WS 클라이언트 라이브러리)로 한 번 붙는 스모크가 필요하다.

5. **호스트에서 직접 띄워도 같은 403이 나는지로 배제했다.** 컨테이너 밖(호스트)에서도 동일하게 재현되자 "Docker가 원인 아님"으로 기록했다. 원인을 좁히는 순서: (a) 같은 서버의 REST는 정상인지 → 서버·네트워크 자체는 살아 있음 (b) 컨테이너 안/밖 모두 재현되는지 → 배포 환경 배제 (c) 핸드셰이크 단계에서 무엇이 거절하는지 → 엔드포인트 시그니처(타입 힌트)가 주원인. 보조 원인 후보로는 서버의 프록시 헤더 처리가 기본 활성일 때 그 미들웨어가 WS scope의 scheme을 http/https로 바꿔 403이 날 수 있다는 점이 함께 기록됐다 — 프록시 헤더 처리를 끄거나 WS 구현을 바꾸는 선택지다.

6. **"같은 이름의 API = 같은 계약"이 아니다.** 세 사건은 모두 WebSocket이라는 이름은 같지만 라이브러리마다 다른 세 축에서 났다 — **수신 방식**(타입 특화 `receive_text()` vs 일반 `receive()`), **반복 프로토콜**(`async for` 지원 여부), **주입 방식**(타입 힌트 기반 DI). 관용구를 새 프레임워크로 옮길 때는 (a) 연결 객체가 어떤 프로토콜을 구현하는지 (b) 수신 API가 예상 밖 입력에 어떻게 반응하는지 (c) 엔드포인트 시그니처를 프레임워크가 어떻게 해석하는지를 먼저 확인하고, 테스트 하네스가 아닌 **실제 클라이언트 경로**로 확인한다.

## 문제 구조 (추상화 코드)

### 변형 A — 타입 특화 수신 API가 예상 밖 프레임에서 예외
① 문제 코드
```python
@app.websocket("/ws/term")
async def term(ws: WebSocket):
    await ws.accept()
    while True:
        text = await ws.receive_text()      # binary 프레임 → 예외 → 루프 종료
        handle(json.loads(text))
```
② 고친 코드
```python
    while True:
        msg = await ws.receive()
        if msg["type"] == "websocket.disconnect":   # 종료 메시지 — 여기서 빠져야 함(이후 receive()는 RuntimeError)
            break
        if msg.get("text") is None:          # binary 등 → 무시
            continue
        handle(json.loads(msg["text"]))      # input / resize
# 테스트: binary 프레임을 보낸 뒤에도 입력이 계속 처리되는지
```
무엇이 깨졌나: "text만 온다"는 가정을 외부 입력에 걸었다.

### 변형 B — 다른 라이브러리의 `async for` 관용구
① 문제 코드
```python
@app.websocket("/ws/agent")
async def agent(ws: WebSocket):
    await ws.accept()
    async for raw in ws:                     # TypeError: __aiter__ 없음 → 연결 직후 종료
        handle(raw)
```
② 고친 코드
```python
    while True:
        raw = await ws.receive_text()        # 종료 시 WebSocketDisconnect 로 빠짐
        handle(raw)
# 또는: async for raw in ws.iter_text(): handle(raw)
```
무엇이 깨졌나: 반복 프로토콜을 구현한 라이브러리의 관용구를, 구현하지 않은 객체에 썼다.

### 변형 C — 타입 힌트 없는 WS 인자 (TestClient는 통과)
① 문제 코드
```python
@app.websocket("/ws/deploy")
async def ws_release(ws):                     # 힌트 없음 → 필수 쿼리 파라미터로 해석 → 검증 실패 → 실제 클라이언트는 403
    await ws.accept()
    # ...
```
② 고친 코드
```python
@app.websocket("/ws/deploy")
async def ws_release(ws: WebSocket):          # 힌트가 곧 주입 계약
    await ws.accept()
    # ...
# 보조: 프록시 헤더 처리 미들웨어가 WS scope scheme 을 바꾸면 403 가능 → 비활성화 또는 WS 구현 교체
```
무엇이 깨졌나: 시그니처가 프레임워크의 DI 계약을 어겼고, 테스트 하네스는 실서버 경로를 거치지 않아 초록불이었다(기록된 판단 — 일반론으로 TestClient가 건너뛰는 것은 ASGI 서버·네트워크 층이다).

## 검증 기록
- 2026-09-24: 사건 기록 대조·추상화(Claude 초안)
