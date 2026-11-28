# python/python-libraries/04 — FastAPI 고급 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 문자열 속 `\\n` 이 찍히는 모습 (예측)

```python
# 질문용 발췌
print("""
def write_audit_log(user_id: int, action: str):
    with open("audit.log", "a") as f:
        f.write(f"{user_id}: {action}\\n")
""")
```

- 출력의 `f.write(...)` 줄에서 `\\n` 자리는 어떤 글자로 보이나?

### 2. 섹션과 섹션 사이 (예측)

```python
# 질문용 발췌
print("""
...
    return {"deleted": user_id}
""")

print()
print("=== Middleware ===")
```

- `return {"deleted": user_id}` 줄과 `=== Middleware ===` 줄 사이에는 빈 줄이 몇 줄 찍히나?

### 3. 미들웨어 셋을 붙였을 때 요청을 처음 받는 쪽 (예측)

```python
# 질문용 발췌
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"])

@app.middleware("http")
async def add_process_time_header(request, call_next): ...

@app.middleware("http")
async def log_requests(request, call_next): ...
```

- 요청 하나가 들어오면 셋 중 어느 미들웨어의 `call_next` 앞부분이 가장 먼저 실행되나?

### 4. 일반 사용자의 `DELETE /users/7` (예측)

- 토큰은 올바르지만 `role` 이 `"user"` 인 사용자가 `delete_user` 를 부르면 응답의 상태 코드와 `detail` 은 무엇인가?

### 5. `get_db` 가 `yield` 를 쓰는 까닭 (왜)

- `get_db` 는 왜 `return db` 가 아니라 `try` 안에서 `yield db` 를 하나?

### 6. `send_notification` 이 바로 응답하는 까닭 (왜)

- `send_email` 안에 `time.sleep(2)` 가 있는데 왜 `send_notification` 의 응답은 2초를 기다리지 않나?

### 7. 모든 출처 허용과 인증 정보 허용 (경계)

- `allow_origins=["*"]` 로 바꾸고 `allow_credentials=True` 를 그대로 두면 무엇이 문제가 되나?

### 8. 워커를 넷으로 늘린 채팅 서버 (경계)

- 워커 넷으로 띄운 서버에서 A 와 B 가 다른 워커에 붙으면 A 의 메시지는 왜 B 에게 닿지 않나?

### 9. 라우터 공통 의존성의 반환값 (경계)

- `APIRouter(dependencies=[Depends(get_current_user)])` 아래의 `list_users` 는 현재 사용자 객체를 매개변수로 받을 수 있나?

### 10. 「인터셉터」 자리의 미들웨어와 `Depends` (연결)

- 요청을 가로채 앞뒤 처리를 끼운다는 점에서 미들웨어와 `Depends` 는 각각 어느 범위에 걸리고, 어떤 일에 알맞나?

## 실습

### 실습 1. FastAPI 고급 기능 다섯 섹션을 출력하는 스크립트

**만들 것** — FastAPI 고급 기능(의존성 주입 · 미들웨어 · 백그라운드 작업 · WebSocket · 라우터 분리)의 예제 코드를 섹션마다 삼중 따옴표 문자열로 출력하는 파이썬 스크립트를 만든다.

**준비물** — 이 스크립트는 FastAPI 코드를 문자열로 찍기만 하므로 실행에 FastAPI 가 필요 없다. 문자열 속 코드는 FastAPI 앱을 흉내 낸 발췌이고 `decode_token` · `SessionLocal` 은 정의하지 않는다.

**요구 조건**

1. **1단계(뼈대)** — 다섯 섹션을 차례로 출력한다. 섹션마다 `=== 이름 ===` 머리 한 줄을 찍고, 이어서 코드 문자열을 `print("""…""")` 로 찍는다. 섹션 사이에는 `print()` 로 빈 줄을 하나 더 넣는다.
2. **2단계(의존성 주입)** — 문자열 속 코드에 `HTTPBearer` 로 토큰을 받는 `get_current_user`(사용자가 없으면 401 `"Invalid token"`), `try/finally` 안에서 `yield` 로 세션을 주고 `close` 하는 `get_db`, 두 의존성을 받아 사용자를 돌려주는 `GET /users/me`, `role` 이 `"admin"` 이 아니면 403 `"Admin only"` 를 던지는 중첩 의존성 `get_admin_user`, 그것을 받아 `{"deleted": user_id}` 를 돌려주는 `DELETE /users/{user_id}` 를 담는다.
3. **3단계(미들웨어)** — 문자열 속 코드에 `add_middleware` 로 붙인 `CORSMiddleware`(허용 출처 하나, 인증 정보 허용, 메서드 · 헤더 전부 허용), 처리 시간을 재어 `X-Process-Time` 응답 헤더에 넣는 미들웨어, 요청 메서드 · URL 과 응답 상태 코드를 찍는 미들웨어를 담는다.
4. **4단계(백그라운드 작업)** — 문자열 속 코드에 2초 걸리는 `send_email`, `audit.log` 에 한 줄을 덧붙이는 `write_audit_log`(줄 끝의 `\n` 이 출력에 글자로 보이게), 두 작업을 `add_task` 로 등록하고 `{"message": "Notification queued"}` 를 바로 돌려주는 `POST /send-notification` 을 담는다.
5. **5단계(WebSocket)** — 문자열 속 코드에 연결 목록을 가진 `ConnectionManager`(`connect` 는 수락 후 추가, `disconnect` 는 제거, `broadcast` 는 모두에게 전송)와, 받은 글을 `Client {client_id}: …` 로 브로드캐스트하고 끊기면 목록에서 빼고 `Client {client_id} left` 를 알리는 `/ws/{client_id}` 경로를 담는다.
6. **6단계(라우터 분리)** — 문자열 속 코드에 `prefix` · `tags` · 공통 인증 의존성을 가진 `APIRouter`, 목록을 돌려주는 `GET /`, 아이디를 돌려주는 `GET /{user_id}`, `app.include_router` 등록을 담는다.

**시작 코드**

```python
# [주요 라이브러리] FastAPI 고급

print("=== 의존성 주입 (Depends) ===")
print("""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

app = FastAPI()
security = HTTPBearer()

# TODO: get_current_user — Depends(security) 로 토큰을 받고, 사용자가 없으면 401
# TODO: get_db — try 안에서 yield, finally 에서 close
# TODO: GET /users/me — 두 의존성을 받는다
# TODO: get_admin_user — 중첩 의존성, admin 이 아니면 403
# TODO: DELETE /users/{user_id}
""")

print()
print("=== Middleware ===")
print("""
import time
from fastapi.middleware.cors import CORSMiddleware

# TODO: CORSMiddleware 를 add_middleware 로 붙인다 (출처 "http://localhost:3000")
# TODO: 처리 시간을 X-Process-Time 헤더에 넣는 미들웨어
# TODO: 요청 메서드·URL 과 응답 상태를 찍는 미들웨어
""")

print()
print("=== BackgroundTasks ===")
print("""
from fastapi import BackgroundTasks

# TODO: send_email — time.sleep(2) 뒤 발송 메시지 출력
# TODO: write_audit_log — audit.log 에 한 줄 덧붙이기 (\\n 을 글자로 남긴다)
# TODO: POST /send-notification — add_task 두 번, 바로 응답
""")

print()
print("=== WebSocket ===")
print("""
from fastapi import WebSocket, WebSocketDisconnect

# TODO: ConnectionManager — connect / disconnect / broadcast
# TODO: /ws/{client_id} — 받아서 브로드캐스트, 끊기면 정리하고 알림
""")

print()
print("=== 라우터 분리 (APIRouter) ===")
print("""
from fastapi import APIRouter

# routers/users.py
# TODO: prefix · tags · 공통 의존성을 가진 router
# TODO: GET / 와 GET /{user_id}

# main.py
# TODO: include_router
""")
```

**확인 방법** — `python fastapi-advanced.py` 로 돌려, 다섯 섹션의 머리와 코드가 차례로 찍히고 섹션 사이에 빈 줄이 두 줄씩 있는지, `write_audit_log` 줄 끝이 `\n")` 로 보이는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
