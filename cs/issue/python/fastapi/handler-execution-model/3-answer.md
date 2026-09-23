# cs/issue/python/fastapi/handler-execution-model — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 출처 원문 대조. 복습 전 읽지 말 것.

태그: `resource-bounding`

## 정답
<!-- 질문 1:1 대응 -->

1. **`def` 핸들러는 스레드풀에서 병렬로 실행되기 때문이다.** FastAPI는 동기(`def`) 엔드포인트를 이벤트 루프에서 직접 돌리지 않고 스레드풀 워커에 맡긴다. 그래서 프로세스가 하나여도 저장 요청 두 개가 서로 다른 스레드에서 동시에 진행된다. "stat으로 mtime 확인"과 "write" 사이에 다른 요청의 write가 끼어들면, 검사는 통과했는데 그 사이 바뀐 내용을 덮어쓴다. 이 틈이 **TOCTOU**다. 교정은 검사와 쓰기를 전역 락 하나로 묶어 원자화하는 것이다. 파일별 `flock`은 그 파일을 쓰는 다른 도구(에디터 등)가 flock을 쓰지 않아 실효가 없어 선택하지 않았고, 핸들러를 `async def`로 바꾸는 방법은 파일 I/O가 이벤트 루프를 막는 비용 때문에 선택하지 않았다. 외부 도구의 변경은 mtime 불일치 → 409 → 사용자 확인 후 강제 저장으로 처리한다.
   > **TOCTOU(Time-Of-Check to Time-Of-Use)** — 검사한 시점과 그 결과를 쓰는 시점 사이에 상태가 바뀌어 검사가 무의미해지는 경쟁 조건.

2. **"읽기→결정→등록"이 한 임계구역에 있지 않았기 때문이다.** 락이 "신규/재개 판정"만 감싸면 요청 A는 락 안에서 "신규"로, 요청 B는 A가 남긴 마커를 보고 "재개"로 판정한 뒤 둘 다 락을 풀고 등록으로 간다. 락 밖에서 B의 등록이 먼저 돌면 같은 키에 "재개" 명령이 등록되고, A는 get-or-create에서 이미 있는 그 항목을 재사용한다 — 존재하지 않는 세션을 재개하려는 영구 실패다. 판정이 전제로 삼은 상태와 실제 등록 순서가 어긋난 것이다. 교정은 판정 + 충돌 검사 + 명령 조립 + 등록을 **전부** 같은 락 안으로 옮기는 것이다(락 범위 확장). 검증은 5스레드 동시 시작 → 키 하나만 생성되는지로 했다. 락을 두 개 이상 중첩으로 잡게 되면 획득 순서를 고정해야 한다는 점이 함께 검토 대상이 됐다.
   > **check-then-act** — 공유 상태를 읽고, 그 결과로 결정하고, 행동하는 3단계. 세 단계가 원자적이지 않으면 결정의 전제가 행동 시점에 이미 무너져 있을 수 있다.

3. **이벤트 루프가 하나라서 동기 호출 하나가 모든 요청을 멈춘다.** `async def` 핸들러는 이벤트 루프 스레드에서 직접 실행된다. 그 안에서 동기 소켓 I/O를 부르면 응답이 올 때까지 루프 스레드가 붙잡혀, 같은 워커의 다른 코루틴은 await 차례를 얻지 못한다. 단독 실행에선 기다릴 다른 요청이 없으니 느린 것 외에 티가 안 난다. 병렬로 몰리면 요청들이 줄줄이 대기하다 **클라이언트 타임아웃**을 넘긴다. 실측 모양: 병렬 API 테스트 310개 중 82건 실패 — `500`, `Server disconnected without sending a response`, `ReadTimeout`, 서버 로그 `Connection timed out`. 단독 실행은 통과. "느려짐"이 아니라 "타임아웃·끊김"으로 보이는 이유는 지연이 요청마다 더해지지 않고 **대기열 전체에 전파**되기 때문이다.
   > **이벤트 루프** — 하나의 스레드가 여러 코루틴을 번갈아 실행하는 스케줄러. 코루틴이 `await`로 양보할 때만 다른 코루틴이 돈다.

4. **호출 체인 중간의 `def`는 실행 스레드를 바꾸지 않는다.** `async def report()`가 await 없이 동기 `generate()`를 부르면, `generate()`와 그 안의 모든 호출(문서 생성 CPU 작업, 이미지 N개 순차 다운로드, 동기 객체 저장소 업로드)은 **여전히 루프 스레드에서** 실행된다. `def`라는 표시가 스레드풀 오프로드를 일으키는 건 **FastAPI가 핸들러(와 `Depends` 의존성 함수)를 직접 호출할 때뿐**이다. 핸들러 내부에서 부르는 동기 함수는 그냥 같은 스레드에서 도는 함수 호출이다. 그래서 검증자의 "동기 체인 안이라 블로킹 안 함"은 거꾸로 된 판정이다. 이후 두 리뷰어가 독립적으로 같은 항목을 크리티컬로 확인했다. 교훈: 블로킹 여부는 "호출하는 함수가 async인가"가 아니라 **"그 코드가 어느 스레드에서 도는가"**로 판정한다. 같은 구조로, 쿼리 조립 중 동기 NoSQL·캐시 클라이언트 조회, 검색마다 동기 count 호출도 함께 지적됐다.

5. 셋은 고치는 층이 다르다.
   - **async 클라이언트로 전환**(`await client.async_search(...)`) — 근본. 대기 중 루프를 양보하므로 다른 요청이 돈다. 같은 클래스에 async 메서드가 이미 있으면 호출부만 바꾸면 되고, "동기 메서드 호출 0건"을 회귀 테스트로 고정한다.
   - **스레드로 오프로드**(`await anyio.to_thread.run_sync(generate, ...)`) — async 판이 없는 동기 라이브러리·CPU 작업용. 루프는 풀리지만 스레드 수(anyio 기본 스레드 한도 — FastAPI의 `def` 핸들러와 공유)만큼만 병렬이다. CPU 바운드 작업은 GIL 때문에 스레드로 처리량이 늘지 않으므로(루프 응답성만 확보) 무거우면 프로세스 풀이 맞다. 그래서 동시 작업 수를 세마포어로 상한하고, 외부 다운로드에는 전체 기한을 둔다.
   - **워커 수 증가**(`--workers 4`) — 워커마다 독립 루프가 생겨 한 워커가 멈춰도 다른 워커가 받는다. 그러나 **각 워커 안의 정지는 그대로**라 동시 요청이 워커 수를 넘으면 같은 증상이 재현된다. 그래서 우회다. 개발용 `--reload`를 운영 기동에서 뺀 것도 같은 정리에 포함됐다.
   > **오프로드(offload)** — 블로킹 작업을 루프 스레드 밖(스레드풀·프로세스)으로 보내고, 루프에서는 그 완료를 await하는 것.

6. **나중에 등록한 미들웨어가 먼저 실행된다(LIFO).** Starlette의 `add_middleware`는 새 미들웨어로 기존 스택을 **바깥에서 감싼다**. 그래서 A→B→C 순으로 등록하면 요청은 C→B→A 순으로 통과한다. 실행 순서가 "컨텍스트 → 차단 → 제한 → 인증"인데 클라이언트 IP를 **인증(마지막)** 한 곳만 채우면, 앞선 차단·제한은 `getattr(request.state, "client_ip", "unknown")`의 폴백 값 `"unknown"`을 읽는다. 결과: IP 차단이 전혀 걸리지 않고, 모든 클라이언트가 **요청 제한 카운터 하나를 공유**한다. 카운터를 공유하므로 한 사용자가 한도를 채우면 전원이 막히는 구조다(귀결). 테스트로 `block:unknown`·`rate:unknown`·카운터 공유 세 가지를 RED로 재현했다. (방안 비교 1 참고)
   > **LIFO 미들웨어 스택** — 미들웨어를 등록할 때마다 기존 앱을 바깥에서 한 겹 더 감싸는 구조. 마지막에 감싼 층을 요청이 가장 먼저 지난다.

7. **공통 원리: 어떤 객체는 특정 시점·특정 실행 경로에서만 존재한다.** `add_middleware(Cls, **kwargs)`의 인자는 **등록 시점(모듈 로드·앱 구성)**에 평가되고, 스택은 앱이 처음 호출될 때(lifespan 시작 메시지 포함) 그 인자로 인스턴스화된다 — 어느 쪽이든 lifespan 본문보다 먼저다(Starlette 기준). lifespan에서 만드는 자원은 **그보다 늦게** 생기므로 생성자 인자로 넘길 방법이 없다. 그래서 lifespan에서 `app.state.outbox`에 저장하고, 미들웨어는 **요청이 올 때** `request.app.state.outbox`로 찾아 쓴다. 같은 이유로 생성자를 직접 호출해 만든 미들웨어 객체는 스택에 들어가지 않아 요청을 하나도 기록하지 못했다(캐시 크기 0). 상태 보관 객체와 HTTP 가로채기 미들웨어를 분리한 뒤 `add_middleware()`로 등록해 고쳤다. 요청 스코프 의존성도 같다 — HTTP Request는 **HTTP 요청 경로에만** 있고, 이벤트 핸들러(메시지 소비 등 HTTP 밖 경로)에는 없다. 그래서 같은 의존 체인이 이벤트 경로에서 "Request를 만들 팩토리 없음"으로 실패한다. Spring에서 RequestScope 빈을 `@Async` 스레드에서 쓰는 것과 같은 구조다. (방안 비교 2 참고)
   > **요청 스코프(request scope)** — 요청 하나가 사는 동안만 존재하는 의존성 범위. 요청 밖 경로(백그라운드·이벤트)에서는 해석할 대상이 없다.

## 문제 구조 (추상화 코드)

### 변형 A — `def` 핸들러의 검사-후-행동이 스레드풀에서 경쟁
① 문제 코드
```python
@app.post("/save")
def save(req: SaveIn):                                   # def → 스레드풀에서 병렬
    if not req.force and p.stat().st_mtime != req.mtime:  # check
        raise HTTPException(409)
    p.write_text(req.content)                             # act — 사이에 다른 스레드가 끼어듦
```
② 고친 코드
```python
save_lock = threading.Lock()

@app.post("/save")
def save(req: SaveIn):
    with save_lock:                                       # 검사+쓰기 원자화
        if not req.force and abs(p.stat().st_mtime - req.mtime) > 1e-6:
            raise HTTPException(409)
        p.write_text(req.content)
        return {"mtime": p.stat().st_mtime}
```
무엇이 깨졌나: "단일 프로세스 = 경쟁 없음"이라 가정했지만 동기 핸들러는 스레드 여러 개에서 동시에 돈다.

같은 구조 (락 범위가 결정만 감쌈):
```python
# 문제
with lock:
    key, resumed = decide(folder)                 # 신규/재개 판정만 락 안
registry.get_or_create(key, build_cmd(key, resumed))   # 등록은 락 밖 → 다른 요청의 등록이 먼저 끼어듦
# 고친
with lock:
    key, resumed = decide(folder)
    existing = registry.get(key)
    if existing is not None and existing.cwd != folder:
        key, resumed = new_marker(folder), False
    registry.get_or_create(key, build_cmd(key, resumed))   # 판정~등록 전부 한 임계구역
```

### 변형 B — `async def` 안의 동기 I/O가 이벤트 루프를 점유
① 문제 코드
```python
@app.post("/search")
async def search(req: SearchIn):
    result = client.search(index, query, size=10)        # 동기 소켓 I/O — 루프 정지
    # ...
```
② 고친 코드
```python
@app.post("/search")
async def search(req: SearchIn):
    result = await client.async_search(index, query, size=10)   # 대기 중 루프 양보
    # ...
# 회귀 테스트: 서비스 경로에서 동기 search()/health_check() 호출이 0건임을 단언
```
무엇이 깨졌나: 리팩토링 중 동기·비동기 메서드가 한 클래스에 공존해, 일부 호출부만 async로 전환되고 나머지는 루프를 막았다.\
같은 구조: 서비스 메서드 10곳이 동기 호출로 남아 전체 요청이 지연됨 → 같은 클래스의 async 메서드로 전환 + 동기 호출 0건 테스트 3개.\
같은 구조: 병렬 테스트에서만 500·연결 끊김·ReadTimeout이 대량 발생, 단독 실행은 통과 → async 전환(근본) + 워커 4개·`--reload` 제거(우회).

### 변형 C — 동기 함수 체인을 거쳐도 루프 스레드에서 돈다 (오판정 사례)
① 문제 코드
```python
@app.post("/report")
async def report(req: ReportIn):
    return builder.generate(req)          # await 없음 → 아래 전부 루프 스레드

def generate(req):                        # "def니까 블로킹 아님"이라는 오판정
    doc = render_document(req)            # CPU 작업
    for url in image_urls:
        requests.get(url, timeout=10)     # N번 순차 다운로드
    storage.upload_fileobj(doc, ...)      # 동기 업로드
```
② 고친 코드 (계획)
```python
report_slots = asyncio.Semaphore(MAX_CONCURRENT_REPORTS)

@app.post("/report")
async def report(req: ReportIn):
    async with report_slots:                                   # 동시 보고서 수 상한
        return await anyio.to_thread.run_sync(builder.generate, req)   # 루프 밖으로 오프로드
# + 이미지 다운로드에 전체 deadline, 효과는 생성 중 /health 지연 전후 측정으로 입증
```
무엇이 깨졌나: "스레드풀로 간다"는 성질은 FastAPI가 핸들러(·의존성)를 호출할 때만 적용되는데, 그것을 내부 함수 호출에도 적용된다고 착각했다.

### 변형 D — 미들웨어를 생성자로 만들어 스택 밖에 둠 / lifespan 자원을 생성자에 주입
① 문제 코드
```python
metrics_mw = MetricsMiddleware(app)            # 스택에 등록되지 않음 → 요청 0건 기록
app.add_middleware(RateLimitMiddleware, outbox=outbox)   # 인자는 등록 시점에 평가 — outbox 는 lifespan 에서야 생김
```
② 고친 코드
```python
app.add_middleware(MetricsMiddleware)          # 상태(collector)와 HTTP 가로채기 분리 후 등록

@asynccontextmanager
async def lifespan(app):
    app.state.outbox = await create_outbox()   # 자원은 lifespan 에서 생성·보관
    yield

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        outbox = request.app.state.outbox       # 요청 시점에 동적 참조
        # ...
```
무엇이 깨졌나: 스택 빌드(구성 시점)와 자원 생성(lifespan)의 시간 순서를 무시하고 생성자로 묶으려 했다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log

## 방안 비교

기본 방안(위 변형 A~D)은 "핸들러·자원을 그것이 실제로 도는 스레드·시점에 맞춰 배치한다"이다. 같은 원리(실행 모델에 따라 무엇이 언제 어디서 존재하는가)에 다른 방안이 쓰인 사례:

### 방안 1 — 미들웨어 실행 순서는 불변식으로 두고, 상태를 가장 먼저 실행되는 층에서 채움
```python
# 문제: 등록 LIFO → 실행 Context → Block → RateLimit → Auth
class AuthMiddleware:                          # 마지막 실행 — 유일한 client_ip 설정 지점
    async def dispatch(self, request, call_next):
        request.state.client_ip = claims.ip
class RateLimitMiddleware:                     # 앞에서 실행 → 폴백만 읽음
    async def dispatch(self, request, call_next):
        ip = getattr(request.state, "client_ip", "unknown")   # 전원이 "unknown" 키 공유

# 고친: 순서는 그대로, 가장 먼저 실행되는 층이 채움
class ContextMiddleware:
    async def dispatch(self, request, call_next):
        request.state.client_ip = client_ip_of(request)   # 신뢰 홉 기준 XFF > peer (network/proxy-passthrough 방안 2)
        return await call_next(request)
# IP 추출은 공용 함수 하나로 (중복 정의 금지)
```

### 방안 2 — 요청 스코프 의존성을 HTTP 밖 경로에서 분리
```python
class AppProvider(Provider):
    request = from_context(provides=Request, scope=Scope.REQUEST)   # HTTP 요청에서만 채워짐

    @provide(scope=Scope.REQUEST)
    async def session(self, factory) -> AsyncIterable[Session]:     # 제너레이터 팩토리는 반환 타입 명시
        async with factory() as s:
            yield s

# 문제: 이벤트 핸들러(메시지 소비 — HTTP 밖)가 같은 요청 스코프 체인을 요구
async def on_event(msg, service: FromDI[Service]):   # Service → ... → Request  → 해석 실패
    ...
# 이벤트 경로용 의존 체인은 별도 작업으로 분리(선택지 비교 후 결정 보류)
```
같은 구조(부수): 테스트 설정 키 오타(`asyncio_mode`)로 비동기 픽스처가 "fixture not found".

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 기본: 스레드·시점에 맞춘 배치 | 핸들러가 어느 스레드·시점에 도는지 안다 | 락·async 전환·lifespan 재배치 | 락 범위가 좁거나 동기 호출 하나가 남으면 재발 | 핸들러 본문의 경쟁·블로킹 |
| 1. 순서 불변 + 선두 층에서 상태 채움 | 미들웨어 순서가 설계 의도다 | 1줄 추가 + 공용 추출 함수 | 새 미들웨어가 선두보다 바깥에 등록되면 다시 폴백 | 여러 미들웨어가 같은 요청 상태를 읽을 때 |
| 2. 요청 스코프와 HTTP 밖 경로 분리 | DI가 스코프를 실행 경로로 판정한다 | 경로별 의존 체인 설계 | 공용 서비스가 요청 스코프에 묶여 있으면 이벤트 경로 전체가 실패 | 같은 서비스를 HTTP·이벤트 양쪽에서 쓸 때 |

**결론**: 핸들러 본문의 문제(경쟁·블로킹)는 **실행 스레드**를 기준으로 고친다(기본).\
미들웨어처럼 **실행 순서**가 계약인 곳은 순서를 바꾸지 말고 상태를 가장 먼저 도는 층에서 만든다(1) — 순서를 바꾸면 차단·제한·인증의 설계 의도가 함께 흔들린다.\
**실행 경로**(HTTP vs 이벤트)가 다르면 요청 스코프에 기대는 의존성을 경로별로 나눈다(2).
