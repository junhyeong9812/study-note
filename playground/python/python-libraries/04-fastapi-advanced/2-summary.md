# python/python-libraries/04 — FastAPI 고급 — 정리 (힌트)

> 출처 — study-site 항목 `python/fastapi-advanced`(항목 데이터 `data/python/libraries.json`) · 정답 코드 study-practice `python/python-libraries/reference/fastapi-advanced.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 원본 예제를 `Python 3.12.3` 에서 2회 돌렸다.

## 한눈에 — 쉽게 말하면

**FastAPI 고급 기능은 「식당 한 곳이 손님 한 명을 맞는 순서」다.**
입구의 직원은 들어오는 손님을 모두 맞고 나가는 손님도 모두 배웅한다.
요리사는 재료를 직접 구하지 않고, 보조가 준비해 건넨 재료로 요리한다.
보조는 요리가 끝나면 쓴 도구를 치운다.
음식을 내준 뒤에 설거지를 하고, 단골 단체 손님과는 전화를 끊지 않고 계속 이야기한다.
FastAPI 앱도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 입구 직원(모든 손님을 맞고 배웅함) | 미들웨어(`@app.middleware("http")` · `CORSMiddleware`) |
| 보조가 재료를 준비해 건넴 | `Depends(...)` 의존성 주입 |
| 보조가 요리 뒤에 도구를 치움 | `yield` 의존성의 `finally` 정리 |
| 음식을 내준 뒤에 하는 설거지 | `BackgroundTasks` |
| 끊지 않는 단체 전화 | `WebSocket` + `ConnectionManager` |
| 층별로 나눈 구역 | `APIRouter` + `include_router` |

```text
요청 ──▶ [미들웨어] ──▶ [의존성들 준비] ──▶ [경로 함수] ──▶ 응답
            ▲                                         │
            └──────────── 응답이 거꾸로 지나감 ◀───────┘
                                   응답을 보낸 뒤 ──▶ [백그라운드 작업]
```

## 이 주제가 답하려는 질문

1. 여러 경로 함수가 함께 쓰는 준비 작업(인증 · DB 세션)을 어떻게 한 곳에 두고 주입하나?
2. 모든 요청에 공통으로 끼어드는 처리(시간 측정 · 로깅 · CORS)는 어디에 두나?
3. 응답을 늦추지 않고 시간이 걸리는 일을 하려면 어떻게 하나?
4. 요청-응답 한 번으로 끝나지 않는 실시간 양방향 통신과 큰 앱의 모듈 나누기는 어떻게 하나?

## 동작 방식

### (1) `Depends` — 준비물을 매개변수로 받는다

**언제 쓰나** — 인증 확인처럼 여러 경로 함수가 똑같이 해야 하는 준비가 있을 때 쓴다.

```text
read_users_me(current_user = Depends(get_current_user), db = Depends(get_db))
   │
   ├─ FastAPI 가 get_current_user 를 먼저 호출 ── 반환값 ──▶ current_user
   ├─ FastAPI 가 get_db 를 먼저 호출 ─────────── 내준 값 ──▶ db
   └─ 둘 다 준비되면 read_users_me 본문 실행 ──▶ current_user 반환
```

- 경로 함수의 기본값 자리에 `Depends(호출 가능한 것)` 을 둔다.
- FastAPI 가 그 호출 가능한 것을 대신 부르고, 결과를 매개변수에 넣는다.
- `get_current_user` 도 `Depends(security)` 로 `HTTPBearer` 가 꺼낸 인증 정보(`credentials`)를 받는다.
- 토큰을 풀어(`decode_token`) 사용자가 없으면 `HTTPException` 으로 401(`HTTP_401_UNAUTHORIZED`, `"Invalid token"`)을 던지고, 경로 함수 본문은 실행되지 않는다.

> **의존성 주입** — 함수가 필요한 것을 스스로 만들지 않고 바깥(프레임워크)이 만들어 넣어 주는 방식.\
> 예: `db = Depends(get_db)` 이면 FastAPI 가 `get_db` 로 세션을 만들어 `db` 에 넣는다.

### (2) `yield` 의존성 — 쓰고 나서 치운다

**언제 쓰나** — DB 세션처럼 열었으면 반드시 닫아야 하는 자원을 줄 때 쓴다.

```text
get_db():  db = SessionLocal()
           try:
               yield db   ──▶ 경로 함수가 db 를 쓴다
           finally:       ◀── 요청 처리가 끝나면 여기로 돌아옴
               db.close()
```

- `return` 대신 `yield` 로 값을 내주면 함수가 거기서 멈춘다.
- FastAPI 는 내준 값을 경로 함수에 넣고, 요청 처리가 끝나면 멈춘 자리부터 이어 실행한다.
- `try/finally` 로 감쌌으므로 도중에 예외가 나도 `db.close()` 는 실행된다.
- 원본 팁의 말대로 「`yield` 의존성으로 리소스 정리가 자동화된다」.

### (3) 중첩 의존성 — 의존성이 의존성을 받는다

**언제 쓰나** — 「로그인한 사용자」 위에 「관리자인가」 같은 조건을 한 겹 더 얹을 때 쓴다.

```text
delete_user(admin = Depends(get_admin_user))
                  └─ get_admin_user(user = Depends(get_current_user))
                                         └─ get_current_user(Depends(security))
토큰이 틀림 → 401 "Invalid token"
토큰은 맞지만 role != "admin" → 403 "Admin only"
둘 다 통과 → {"deleted": user_id}
```

- FastAPI 는 가장 안쪽(`security`)부터 차례로 풀어 올라온다.
- 어느 단계에서든 `HTTPException` 이 나면 그 상태 코드로 응답하고 멈춘다.

### (4) 미들웨어 — 모든 요청의 앞뒤에 끼어든다

**언제 쓰나** — 경로와 상관없이 모든 HTTP 요청에 똑같이 할 일(처리 시간 헤더 · 로그 · CORS)이 있을 때 쓴다.

```text
등록 순서: CORSMiddleware → add_process_time_header → log_requests
실행 순서(등록 역순 — 원본 주석):
요청 ▶ log_requests ▶ add_process_time_header ▶ CORSMiddleware ▶ 경로 함수
응답 ◀ log_requests ◀ add_process_time_header ◀ CORSMiddleware ◀
```

- 커스텀 미들웨어는 `@app.middleware("http")` 로 만들고 `(request, call_next)` 를 받는다.
- `await call_next(request)` 앞은 요청이 들어올 때, 뒤는 응답이 나갈 때 실행된다.
- `add_process_time_header` 는 앞에서 시각을 재고 뒤에서 `X-Process-Time` 헤더를 붙인다.
- `log_requests` 는 앞에서 `[메서드] URL` 을, 뒤에서 `Status: 상태코드` 를 찍는다.
- `CORSMiddleware` 는 `app.add_middleware(...)` 로 붙이며, 브라우저의 CORS 정책을 처리한다(허용 출처 `http://localhost:3000`, 인증 정보 허용, 메서드 · 헤더 전부 허용).
- 원본 주석은 「미들웨어는 등록 역순으로 실행된다」고 적는다 — 나중에 등록한 것이 가장 바깥에서 먼저 요청을 받는다.

> **CORS** — 브라우저가 다른 출처(도메인 · 포트)의 서버에 요청할 때 서버의 허락을 확인하는 규칙.\
> 예: `localhost:3000` 의 화면이 `localhost:8000` 의 API 를 부르면 서버가 그 출처를 허용해야 한다.

### (5) `BackgroundTasks` — 응답을 먼저 보내고 뒤에서 일한다

**언제 쓰나** — 이메일 발송 · 감사 로그처럼 사용자가 결과를 기다릴 필요가 없는 가벼운 일에 쓴다.

```text
send_notification(email, background_tasks)
  add_task(send_email, email, "Welcome!", "Hello!")   ← 등록만
  add_task(write_audit_log, 1, "notification_sent")   ← 등록만
  return {"message": "Notification queued"}  ──▶ 응답 즉시 전송
                                                  └▶ 그 뒤 같은 프로세스에서 send_email(2초) · write_audit_log 실행
```

- 경로 함수가 `BackgroundTasks` 타입 매개변수를 받으면 FastAPI 가 넣어 준다.
- `add_task(함수, 인자들...)` 는 일을 등록만 하고 바로 돌아온다.
- 등록된 일은 응답이 나간 뒤, 같은 프로세스 안에서 실행된다.
- 그래서 원본 팁대로 간단한 작업에 알맞고, 복잡하거나 무거운 작업은 Celery(또는 RQ) 같은 외부 큐로 보낸다.

### (6) `WebSocket` — 연결을 열어 두고 주고받는다

**언제 쓰나** — 채팅처럼 서버와 클라이언트가 실시간으로 서로 먼저 말을 거는 양방향 통신에 쓴다.

```text
클라이언트 A ─┐                   ┌─ manager.active_connections = [A, B]
              ├─ /ws/{client_id} ─┤
클라이언트 B ─┘                   └─ A 가 보낸 "hi" → broadcast → A, B 모두 "Client 1: hi"
B 가 끊음 → WebSocketDisconnect → 목록에서 B 제거 → 남은 이에게 "Client 2 left"
```

- `await websocket.accept()` 로 핸드셰이크를 수락해야 통신이 시작된다.
- `receive_text()` 로 받고 `send_text()` 로 보낸다.
- 상대가 끊으면 `WebSocketDisconnect` 예외가 나므로 `except` 에서 정리한다.
- `ConnectionManager` 는 열린 연결을 파이썬 리스트(메모리)에 모아 두고 `broadcast` 로 모두에게 보낸다.

### (7) `APIRouter` — 라우트를 묶어 떼어 낸다

**언제 쓰나** — 앱이 커져 경로를 파일(모듈)별로 나눌 때 쓴다.

```text
routers/users.py: router = APIRouter(prefix="/users", tags=["users"],
                                     dependencies=[Depends(get_current_user)])
                  @router.get("/")          → 최종 경로 /users/
                  @router.get("/{user_id}") → 최종 경로 /users/{user_id}
main.py:          app.include_router(router)
```

- `prefix` 는 묶음 안 모든 경로 앞에 붙는다.
- `tags` 는 자동 문서에서 묶어 보여 줄 그룹 이름이다.
- `dependencies` 는 묶음 안 모든 경로에 걸리는 공통 의존성이다(여기서는 인증).
- `app.include_router(router)` 를 해야 앱에 등록된다.

### (8) 이 예제 파일의 꼴 — 코드를 문자열로 찍는다

**언제 쓰나** — 원본 예제는 FastAPI 앱을 띄우지 않고, 섹션마다 코드를 삼중 따옴표 문자열로 출력한다.

```text
print("=== 섹션 ===")     → 머리 한 줄
print("""                 → 문자열이 줄바꿈으로 시작 → 머리 밑에 빈 줄
...코드...
""")                      → 문자열이 줄바꿈으로 끝남 + print 의 줄바꿈 → 빈 줄 1
print()                   → 빈 줄 1 더
```

- 그래서 섹션 사이에는 빈 줄이 두 줄 생긴다.
- 문자열 안의 `\\n` 은 파이썬이 역슬래시 하나로 바꾸므로, 출력에는 글자 `\n` 이 보인다.

## 문법 — 형태와 규칙

```python
from fastapi import FastAPI, Depends, BackgroundTasks

app = FastAPI()

def get_token():
    yield "tok"            # 내준 값이 주입된다
    print("정리")           # 요청 처리 뒤에 실행된다

@app.middleware("http")
async def mw(request, call_next):
    response = await call_next(request)   # 다음 단계로 넘긴다
    return response

@app.get("/ping")
async def ping(token = Depends(get_token), tasks: BackgroundTasks = None):
    tasks.add_task(print, "뒤에서")
    return {"token": token}
```

- `Depends(f)` 는 기본값 자리에 둔다. `f` 는 호출 가능한 것이면 된다(함수 · 클래스 · `HTTPBearer()` 같은 객체).
- 의존성 함수도 자기 매개변수에 `Depends` 를 쓸 수 있다(중첩).
- `yield` 의존성은 `try/finally` 로 감싸야 예외 때도 정리된다.
- 커스텀 미들웨어는 반드시 `call_next` 의 응답(또는 다른 응답)을 `return` 해야 한다.
- `add_middleware(클래스, 설정=...)` 는 미들웨어 클래스를 붙이는 방법이다.
- `BackgroundTasks` 는 타입 힌트로 받는다. `add_task(함수, *인자)` 꼴이다.
- WebSocket 경로는 `@app.websocket(경로)` 로 만들고, `accept` → `receive_*` / `send_*` 순서를 지킨다.
- `APIRouter(prefix=..., tags=[...], dependencies=[Depends(...)])` 를 만든 뒤 `app.include_router(router)` 로 붙인다.
- 삼중 따옴표 문자열 안에서 `\n` 을 글자로 남기려면 `\\n` 으로 쓴다.

## 어디서 틀리나

### 1. `Depends` 가 시그니처를 어지럽힌다
`Depends` 매개변수는 경로 파라미터와 똑같은 자리에 있지만 요청에서 오는 값이 아니다.
매개변수가 늘면 무엇이 요청 값이고 무엇이 주입 값인지 읽기 어려워진다(원본 주석의 함정).

### 2. 정리를 `return` 의존성에 넣으면 안 된다
`return db` 로 주면 함수가 끝나 버려 `close` 를 부를 자리가 없다.
정리가 필요하면 `yield` + `try/finally` 로 쓴다.

### 3. `allow_origins=["*"]` 과 `allow_credentials=True` 는 충돌한다
원본 주석은 모든 출처(`"*"`)를 허용하면서 인증 정보도 허용하면 충돌하는 함정이 있다고 적는다.
예제가 출처를 `http://localhost:3000` 으로 콕 집은 까닭이다.

### 4. 미들웨어 순서를 등록 순서로 착각한다
원본 주석대로 등록 역순으로 실행된다.
나중에 등록한 `log_requests` 가 가장 먼저 요청을 받는다.

### 5. 무거운 일을 `BackgroundTasks` 에 맡긴다
같은 프로세스에서 돌므로 워커가 죽으면 등록된 작업이 사라진다(원본 주석의 함정).
재시도 · 보관이 필요한 무거운 작업은 Celery/RQ 같은 외부 큐로 보낸다.

### 6. 메모리 `ConnectionManager` 를 여러 워커에서 쓴다
워커(프로세스)마다 리스트가 따로 있어, 워커 1 에 붙은 클라이언트는 워커 2 의 브로드캐스트를 못 받는다.
원본 주석은 Redis pub/sub 같은 공유 통로가 필요하다고 적는다.

### 7. 발췌에 정의되지 않은 이름이 있다
`decode_token` · `SessionLocal` 은 예제 어디에도 정의되지 않았다.
설명용 발췌라서 그대로 앱으로 띄우면 이름 오류가 난다.

### 8. 라우터 공통 의존성의 반환값은 받을 수 없다
`APIRouter(dependencies=[...])` 의 의존성은 실행만 되고 결과가 경로 함수 매개변수로 오지 않는다.
`list_users` 는 사용자 객체를 모른다 — 필요하면 매개변수에 `Depends` 를 따로 쓴다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 문자열 안의 `\\n` 이 출력에 `\n` 으로 보인다 · `print` 가 끝에 줄바꿈을 붙인다 | 파이썬 언어 · 내장 함수 규칙 |
| 미들웨어가 등록 역순으로 실행된다 | FastAPI(바탕인 Starlette)의 구현 — 언어 보장이 아니다 (확인 필요) |
| `yield` 의존성의 정리가 요청 처리 뒤에 실행된다 | FastAPI 의 동작 — 응답 전송과의 정확한 선후는 버전에 따라 다를 수 있다 (확인 필요) |
| `BackgroundTasks` 가 응답 뒤 같은 프로세스에서 실행된다 | FastAPI/Starlette 의 구현 |
| 끊긴 연결에서 `WebSocketDisconnect` 가 난다 | FastAPI/Starlette 의 구현 |
| 워커마다 `ConnectionManager` 가 따로 생긴다 | 운영체제의 프로세스 모델 — 프로세스는 메모리를 나누지 않는다 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 여러 경로가 같은 인증 확인을 한다 | `Depends(get_current_user)` | 경로마다 토큰 해석 복사 |
| 열고 닫는 자원(DB 세션) | `yield` 의존성 + `try/finally` | `return` 의존성 |
| 모든 요청에 붙는 헤더 · 로그 | 미들웨어 | 경로마다 같은 코드 |
| 응답 뒤 가벼운 메일 · 로그 | `BackgroundTasks` | 응답 전 `time.sleep` 대기 |
| 오래 걸리고 잃으면 안 되는 작업 | Celery/RQ 같은 외부 큐 | `BackgroundTasks` |
| 실시간 양방향 채팅 | `WebSocket` | 짧은 간격으로 HTTP 반복 요청 |
| 여러 워커에 걸친 브로드캐스트 | Redis pub/sub 같은 공유 통로 | 메모리 리스트 하나 |
| 큰 앱의 경로 나누기 | `APIRouter` + `include_router` | 한 파일에 모든 경로 |

## 핵심 문장

1. **`Depends` 는 FastAPI 의 핵심이다** — 준비 작업을 함수로 떼어 내고, 중첩해 쌓으며, 라우터 전체에도 건다.
2. **`yield` 의존성은 「주고, 끝나면 치운다」** — `try/finally` 로 정리가 자동화된다.
3. **미들웨어는 모든 요청의 앞뒤를 감싸고, 등록 역순으로 실행된다.**
4. **`BackgroundTasks` 는 응답 뒤 같은 프로세스에서 도는 가벼운 일 전용이다** — 무거운 일은 외부 큐로.
5. **WebSocket 은 연결을 열어 둔 양방향 통신이다** — 메모리 연결 목록은 워커를 넘지 못한다.

## 관련 자료

- [fastapi-basics](../03-fastapi-basics/2-summary.md)
- `dependency-injection` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `concurrency-patterns` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/python/libraries.json` 의 `fastapi-advanced`

## 용어 풀이

- **의존성(dependency)** — 경로 함수가 실행되기 전에 필요한 값을 만들어 주는 함수나 객체.
- **의존성 주입** — 필요한 것을 바깥에서 만들어 매개변수로 넣어 주는 방식.
- **`yield` 의존성** — 값을 `yield` 로 내주고 요청 처리 뒤 이어서 정리 코드를 실행하는 의존성.
- **중첩 의존성** — 다른 의존성을 `Depends` 로 받는 의존성.
- **미들웨어** — 모든 요청과 응답 사이에 끼어 앞뒤 처리를 하는 층.
- **인터셉터** — 요청을 가로채 앞뒤에 처리를 끼우는 것을 다른 프레임워크에서 부르는 이름. FastAPI 에서는 미들웨어 · 의존성이 그 역할을 한다.
- **`call_next`** — 미들웨어가 다음 단계(다음 미들웨어나 경로 함수)로 요청을 넘기는 함수.
- **CORS** — 다른 출처의 요청을 브라우저가 허락받는 규칙.
- **`BackgroundTasks`** — 응답을 보낸 뒤 실행할 함수를 등록하는 FastAPI 객체.
- **Celery / RQ** — 작업을 별도 워커 프로세스로 넘겨 처리하는 외부 작업 큐.
- **WebSocket** — 한 번 연결한 뒤 양쪽이 언제든 메시지를 보내는 통신 방식.
- **핸드셰이크** — 연결을 시작할 때 양쪽이 수락을 주고받는 절차.
- **`WebSocketDisconnect`** — 상대가 연결을 끊으면 수신 중에 나는 예외.
- **브로드캐스트** — 연결된 모두에게 같은 메시지를 보내는 일.
- **워커** — 앱을 실행하는 프로세스 하나. 여러 개를 띄우면 메모리를 나누지 않는다.
- **pub/sub** — 발행자가 보낸 메시지를 구독자 모두가 받는 통로.
- **`APIRouter`** — 경로들을 묶어 `prefix` · `tags` · 공통 의존성을 함께 주는 단위.
- **`HTTPBearer`** — `Authorization: Bearer 토큰` 헤더에서 토큰을 꺼내는 FastAPI 보안 도구.

## 더 들어가면

- 같은 요청 안에서 같은 의존성이 여러 번 쓰이면 FastAPI 는 기본적으로 한 번만 호출하고 결과를 재사용한다. `Depends(f, use_cache=False)` 로 끌 수 있다 (확인 필요).
- `yield` 의존성의 정리 코드가 응답 전송 앞에 도는지 뒤에 도는지는 FastAPI 버전에 따라 바뀐 적이 있다 (확인 필요).
- `def` 로 쓴 동기 백그라운드 작업(`send_email` 처럼 `time.sleep` 을 쓰는 것)은 스레드 풀에서 돌아 이벤트 루프를 막지 않는다 (확인 필요).
- `HTTPBearer` 는 `Authorization` 헤더가 아예 없으면 의존성 함수가 실행되기 전에 스스로 오류 응답을 낸다. 그 상태 코드는 버전에 따라 다르다 (확인 필요).
- `broadcast` 도중 한 연결이 이미 끊겨 있으면 `send_text` 가 예외를 낼 수 있어, 실무에서는 연결마다 예외를 잡는다 (확인 필요).
- 테스트에서는 `app.dependency_overrides[get_db] = 가짜_함수` 로 의존성을 바꿔 끼울 수 있다 (확인 필요).
