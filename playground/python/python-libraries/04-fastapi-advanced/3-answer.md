# python/python-libraries/04 — FastAPI 고급 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 역슬래시 하나와 `n` — 글자 `\n` 으로 보인다

**출력**

```text
def write_audit_log(user_id: int, action: str):
    with open("audit.log", "a") as f:
        f.write(f"{user_id}: {action}\n")
```

**왜 그런가**
일반 문자열 안에서 `\\` 는 역슬래시 한 글자를 뜻한다.
그래서 `\\n` 은 「역슬래시 + n」 두 글자가 되고 줄바꿈이 되지 않는다.
출력된 코드를 그대로 파일에 붙이면 원래 의도대로 `\n` 이 줄바꿈 이스케이프로 읽힌다.
근거: 2-summary 「동작 방식 (8)」.

### 2. 두 줄

**출력**

```text
    return {"deleted": user_id}


=== Middleware ===
```

**왜 그런가**
삼중 따옴표 문자열이 `return …` 줄 뒤 줄바꿈으로 끝나고, `print` 가 끝에 줄바꿈을 하나 더 붙여 빈 줄 하나가 생긴다.
이어서 `print()` 가 빈 줄을 하나 더 찍는다.
근거: 2-summary 「동작 방식 (8)」.

### 3. 가장 나중에 등록한 `log_requests`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
요청이 들어오면 `log_requests` 가 먼저 `[메서드] URL` 을 찍고, 다음으로 `add_process_time_header` 가 시작 시각을 재고, 그다음 `CORSMiddleware`, 마지막으로 경로 함수가 실행된다.
응답은 거꾸로 지나가므로 `log_requests` 의 `Status: …` 가 가장 나중에 찍힌다.

**왜 그런가**
원본 주석은 미들웨어가 등록 역순으로 실행된다고 적는다.
나중에 등록한 것일수록 바깥 껍질이 되어 요청을 먼저 받고 응답을 나중에 받는다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 4」.

### 4. 403, `"Admin only"`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
상태 코드 403, `detail` 은 `"Admin only"` 다.

**왜 그런가**
`delete_user` 는 `get_admin_user` 에, `get_admin_user` 는 `get_current_user` 에 기댄다.
토큰이 올바르니 `get_current_user` 는 사용자를 돌려주고 401 은 나지 않는다.
`get_admin_user` 에서 `user.role != "admin"` 이 참이라 `HTTPException(status_code=403, detail="Admin only")` 가 나고, `delete_user` 본문은 실행되지 않는다.
근거: 2-summary 「동작 방식 (3)」.

### 5. 세션을 쓰게 한 뒤 반드시 닫기 위해

`return` 하면 함수가 끝나 버려 경로 함수가 세션을 다 쓴 뒤에 `close` 를 부를 자리가 없다.
`yield` 는 값을 내준 채 함수를 멈춰 두고, FastAPI 가 요청 처리가 끝나면 멈춘 자리부터 이어 실행한다.
`try/finally` 로 감쌌으니 경로 함수에서 예외가 나도 `db.close()` 가 실행된다 — 원본 팁의 「리소스 정리 자동화」다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 2」.

### 6. `add_task` 는 등록만 하고, 실행은 응답을 보낸 뒤라서

`background_tasks.add_task(send_email, …)` 는 함수를 부르지 않고 목록에 올리기만 한 뒤 바로 돌아온다.
`send_notification` 은 곧장 `{"message": "Notification queued"}` 를 돌려주고, 등록된 작업은 응답이 나간 뒤 같은 프로세스에서 실행된다.
그래서 2초는 사용자의 대기 시간에 들어가지 않는다.
다만 같은 프로세스에서 돌기 때문에 워커가 죽으면 작업이 사라지므로, 무거운 일은 Celery/RQ 같은 외부 큐로 보낸다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 5」.

### 7. 모든 출처 허용과 인증 정보 허용이 충돌한다

원본 주석은 `allow_origins` 에 `"*"` 를 쓰면서 `allow_credentials=True` 를 함께 두면 충돌하는 함정이 있다고 적는다.
인증 정보(쿠키 · 인증 헤더)를 함께 보내는 요청을 아무 출처에나 열어 줄 수는 없기 때문에, 예제처럼 허용할 출처를 `http://localhost:3000` 같이 구체적으로 적어야 한다.
근거: 2-summary 「어디서 틀리나 3」. 「아무 출처에나 열어 줄 수 없다」는 까닭 풀이는 (원본에 근거 없음 — 추론).

### 8. 연결 목록이 워커마다 따로 있어서

`ConnectionManager` 의 `active_connections` 는 파이썬 리스트, 곧 그 프로세스의 메모리에 있다.
워커는 서로 메모리를 나누지 않으므로 워커 1 의 `broadcast` 는 워커 1 리스트에 있는 연결에만 보낸다.
B 는 워커 2 의 리스트에 있으니 A 의 메시지를 못 받는다.
원본 주석은 Redis pub/sub 같은 공유 통로로 워커끼리 메시지를 넘겨야 한다고 적는다.
근거: 2-summary 「동작 방식 (6)」 · 「어디서 틀리나 6」 · 「구현 세부사항 대 언어 보장」.

### 9. 받을 수 없다 — 실행만 된다

라우터의 `dependencies=[…]` 에 둔 의존성은 묶음 안 모든 경로에서 실행되어 인증을 검사하지만, 반환값이 경로 함수 매개변수로 오지 않는다.
`list_users` 에서 사용자 객체가 필요하면 매개변수에 `user = Depends(get_current_user)` 를 따로 적어야 한다.
근거: 2-summary 「동작 방식 (7)」 · 「어디서 틀리나 8」.

### 10. 미들웨어는 모든 요청, `Depends` 는 그것을 쓴 경로

다른 프레임워크에서 「인터셉터」가 맡는 일을 FastAPI 에서는 둘이 나눠 맡는다.
미들웨어는 경로와 상관없이 모든 HTTP 요청의 앞뒤를 감싸므로 처리 시간 헤더 · 요청 로그 · CORS 처럼 전부에 똑같이 할 일에 알맞다.
`Depends` 는 그것을 매개변수(또는 라우터 `dependencies`)에 적은 경로에서만 실행되고 결과를 함수에 넘겨주므로, 인증된 사용자 · DB 세션처럼 경로 함수가 값을 받아 써야 하는 일에 알맞다.
근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (4)」 · 「언제 쓰고 언제 안 쓰나」 · 「용어 풀이」의 인터셉터.

## 실습 정답

### 실습 1. FastAPI 고급 기능 다섯 섹션을 출력하는 스크립트

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1단계 섹션 머리 · 코드 문자열 · 빈 줄 | `print("=== … ===")` · `print("""…""")` · 섹션 사이 `print()` |
| 2단계 토큰 인증과 401 | `get_current_user` 의 `Depends(security)` · `HTTP_401_UNAUTHORIZED` |
| 2단계 `yield` 세션 | `get_db` 의 `try: yield db` / `finally: db.close()` |
| 2단계 두 의존성을 받는 경로 | `read_users_me` (`@app.get("/users/me")`) |
| 2단계 중첩 의존성과 403 | `get_admin_user` · `delete_user` (`@app.delete("/users/{user_id}")`) |
| 3단계 CORS | `app.add_middleware(CORSMiddleware, …)` |
| 3단계 처리 시간 헤더 | `add_process_time_header` 의 `response.headers["X-Process-Time"]` |
| 3단계 요청 · 상태 로그 | `log_requests` |
| 4단계 두 작업 함수 | `send_email` · `write_audit_log` (`\\n`) |
| 4단계 등록 후 즉시 응답 | `send_notification` 의 `add_task` 두 번 · `{"message": "Notification queued"}` |
| 5단계 연결 관리 | `ConnectionManager` 의 `connect` · `disconnect` · `broadcast` |
| 5단계 채팅 경로 | `websocket_endpoint` (`@app.websocket("/ws/{client_id}")`) · `except WebSocketDisconnect` |
| 6단계 라우터 | `APIRouter(prefix="/users", tags=["users"], dependencies=[…])` · `list_users` · `get_user` · `app.include_router(router)` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-libraries/reference/fastapi-advanced.py`

```python
# [주요 라이브러리] FastAPI 고급
# 설명: Depends, middleware, BackgroundTasks, WebSocket 등 고급 기능
# 팁: Depends는 FastAPI의 핵심. yield 의존성으로 리소스 정리가 자동화된다. BackgroundTasks는 간단한 비동기 작업에 적합하고, 복잡한 작업은 Celery를 사용한다. WebSocket은 실시간 양방향 통신에 사용된다.

# 섹션 헤더 출력: Depends를 이용한 의존성 주입 패턴
print("=== 의존성 주입 (Depends) ===")
# Depends는 호출 가능한 객체를 받아 결과를 자동 주입
# yield 의존성은 generator처럼 동작하여 try/finally 정리가 가능(DB 세션 패턴)
# 의존성은 중첩 가능(get_admin_user는 내부에서 get_current_user에 의존)
# 함정: Depends는 path 파라미터처럼 보이지 않게 동작하므로 시그니처 어지러워질 수 있음
print("""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

app = FastAPI()
security = HTTPBearer()

# 공통 의존성: 인증 체크
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    user = decode_token(token)  # JWT 디코딩
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    return user

# DB 세션 의존성
async def get_db():
    db = SessionLocal()
    try:
        yield db  # yield로 제공 -> 요청 완료 후 자동 정리
    finally:
        db.close()

# 의존성 사용
@app.get("/users/me")
async def read_users_me(
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    return current_user

# 중첩 의존성
async def get_admin_user(user = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return user

@app.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    admin = Depends(get_admin_user)  # get_current_user -> get_admin_user
):
    return {"deleted": user_id}
""")

# 빈 줄 출력으로 섹션 분리
print()
# 섹션 헤더 출력: 미들웨어 등록 방법
print("=== Middleware ===")
# CORSMiddleware는 브라우저 CORS 정책 처리(allow_origins에 "*" 사용 시 credentials와 충돌 함정)
# @app.middleware("http") 데코레이터로 커스텀 미들웨어 정의(call_next로 다음 핸들러 호출)
# 미들웨어는 등록 역순으로 실행됨
print("""
import time
from fastapi.middleware.cors import CORSMiddleware

# CORS 미들웨어
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 커스텀 미들웨어: 요청 시간 측정
@app.middleware("http")
async def add_process_time_header(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# 커스텀 미들웨어: 요청 로깅
@app.middleware("http")
async def log_requests(request, call_next):
    print(f"[{request.method}] {request.url}")
    response = await call_next(request)
    print(f"Status: {response.status_code}")
    return response
""")

# 빈 줄 출력으로 섹션 분리
print()
# 섹션 헤더 출력: BackgroundTasks로 응답 후 후처리 실행
print("=== BackgroundTasks ===")
# BackgroundTasks는 응답 반환 후 같은 프로세스에서 실행됨(가벼운 작업 전용)
# 무거운 작업은 Celery/RQ 등 외부 큐로 보내야 한다(함정: 워커 다운 시 작업 유실)
print("""
from fastapi import BackgroundTasks

def send_email(email: str, subject: str, body: str):
    # 시간이 걸리는 작업 (이메일 발송, 로그 기록 등)
    import time
    time.sleep(2)  # 실제로는 SMTP 전송
    print(f"Email sent to {email}: {subject}")

def write_audit_log(user_id: int, action: str):
    with open("audit.log", "a") as f:
        f.write(f"{user_id}: {action}\\n")

@app.post("/send-notification")
async def send_notification(
    email: str,
    background_tasks: BackgroundTasks
):
    # 응답은 즉시 반환, 이메일은 백그라운드에서 전송
    background_tasks.add_task(send_email, email, "Welcome!", "Hello!")
    background_tasks.add_task(write_audit_log, 1, "notification_sent")
    return {"message": "Notification queued"}
""")

# 빈 줄 출력으로 섹션 분리
print()
# 섹션 헤더 출력: WebSocket 양방향 통신
print("=== WebSocket ===")
# WebSocket은 accept() 호출로 핸드셰이크 수락
# receive_text/send_text 등으로 메시지 송수신, 끊기면 WebSocketDisconnect 예외
# 멀티 워커 환경에서는 메모리 기반 ConnectionManager가 워커별로 분리되므로 Redis pub/sub 등 필요(함정)
print("""
from fastapi import WebSocket, WebSocketDisconnect

# 연결 관리자
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Client {client_id}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client {client_id} left")
""")

# 빈 줄 출력으로 섹션 분리
print()
# 섹션 헤더 출력: APIRouter로 라우트를 모듈화
print("=== 라우터 분리 (APIRouter) ===")
# APIRouter는 라우트의 prefix, tags(문서 그룹), 공통 dependencies를 묶는 단위
# main.py에서 app.include_router로 등록하여 큰 앱을 모듈화
print("""
from fastapi import APIRouter

# routers/users.py
router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(get_current_user)]
)

@router.get("/")
async def list_users():
    return [{"id": 1, "name": "Alice"}]

@router.get("/{user_id}")
async def get_user(user_id: int):
    return {"id": user_id}

# main.py
app.include_router(router)
""")
```

**실행 결과** — 원본 예제(`component`)를 실제로 돌린 출력이다. 환경 `Python 3.12.3` · 2026-11-28 · exit 0 · 두 번 돌려 출력이 같았다.

````text
$ python3 -I example.py
=== 의존성 주입 (Depends) ===

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

app = FastAPI()
security = HTTPBearer()

# 공통 의존성: 인증 체크
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    user = decode_token(token)  # JWT 디코딩
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    return user

# DB 세션 의존성
async def get_db():
    db = SessionLocal()
    try:
        yield db  # yield로 제공 -> 요청 완료 후 자동 정리
    finally:
        db.close()

# 의존성 사용
@app.get("/users/me")
async def read_users_me(
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    return current_user

# 중첩 의존성
async def get_admin_user(user = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return user

@app.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    admin = Depends(get_admin_user)  # get_current_user -> get_admin_user
):
    return {"deleted": user_id}


=== Middleware ===

import time
from fastapi.middleware.cors import CORSMiddleware

# CORS 미들웨어
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 커스텀 미들웨어: 요청 시간 측정
@app.middleware("http")
async def add_process_time_header(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# 커스텀 미들웨어: 요청 로깅
@app.middleware("http")
async def log_requests(request, call_next):
    print(f"[{request.method}] {request.url}")
    response = await call_next(request)
    print(f"Status: {response.status_code}")
    return response


=== BackgroundTasks ===

from fastapi import BackgroundTasks

def send_email(email: str, subject: str, body: str):
    # 시간이 걸리는 작업 (이메일 발송, 로그 기록 등)
    import time
    time.sleep(2)  # 실제로는 SMTP 전송
    print(f"Email sent to {email}: {subject}")

def write_audit_log(user_id: int, action: str):
    with open("audit.log", "a") as f:
        f.write(f"{user_id}: {action}\n")

@app.post("/send-notification")
async def send_notification(
    email: str,
    background_tasks: BackgroundTasks
):
    # 응답은 즉시 반환, 이메일은 백그라운드에서 전송
    background_tasks.add_task(send_email, email, "Welcome!", "Hello!")
    background_tasks.add_task(write_audit_log, 1, "notification_sent")
    return {"message": "Notification queued"}


=== WebSocket ===

from fastapi import WebSocket, WebSocketDisconnect

# 연결 관리자
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Client {client_id}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client {client_id} left")


=== 라우터 분리 (APIRouter) ===

from fastapi import APIRouter

# routers/users.py
router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(get_current_user)]
)

@router.get("/")
async def list_users():
    return [{"id": 1, "name": "Alice"}]

@router.get("/{user_id}")
async def get_user(user_id: int):
    return {"id": user_id}

# main.py
app.include_router(router)
````

**풀이 요점**

- 스크립트는 FastAPI 앱을 띄우지 않고 코드를 문자열로 찍는다 — 확인할 것은 출력의 꼴이다.
- 삼중 따옴표 문자열이 줄바꿈으로 시작하고 끝나서 머리 밑에 빈 줄 하나, 섹션 끝에 `print()` 까지 더해 빈 줄 두 줄이 생긴다.
- `write_audit_log` 에서 `\\n` 으로 써야 출력에 글자 `\n` 이 남는다.
- 의존성은 `security` → `get_current_user` → `get_admin_user` 로 쌓이고, 401 과 403 이 서로 다른 단계에서 난다.
- 미들웨어 셋은 등록 역순으로 감싸고, `BackgroundTasks` 는 응답 뒤에, WebSocket 은 끊길 때까지 루프를 돈다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 원본 예제를 `Python 3.12.3` 에서 2회 돌렸다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
