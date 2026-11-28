# rust/rust-project-structures/09 — Tower 미들웨어 패턴 — 정리 (힌트)

> 출처 — study-site 항목 `rust/middleware-tower`(항목 데이터 `data/rust/project-structures.json`) · 정답 코드 study-practice `rust/rust-project-structures/reference/middleware-tower.rs`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다).

## 한눈에 — 쉽게 말하면

**미들웨어는 「사무실까지 가는 길에 놓인 여러 겹의 문」이다.**
방문객(요청)은 바깥 문부터 차례로 지나 맨 안쪽 사무실(핸들러)에 닿는다.
각 문에는 일하는 사람이 있다.
정문 안내원은 어디서 왔는지 확인하고, 보안 요원은 출입증을 검사하며, 기록원은 들어간 시각과 나온 결과를 장부에 적는다.
사무실에서 받은 답(응답)은 들어온 길을 거꾸로 되짚어 나간다.
보안 요원이 출입증 없는 사람을 돌려보내면, 그 사람은 안쪽 문에 아예 닿지 못한다.

Tower 미들웨어도 똑같은 구조다.
모든 문과 사무실이 「요청을 받아 응답을 돌려준다」는 같은 꼴을 지키므로, 문을 몇 겹이든 겹칠 수 있다.

| 비유 | 실체 |
|---|---|
| 방문객 | `Request` |
| 사무실이 내준 답 | `Response` |
| 맨 안쪽 사무실 | `AppHandler` (라우팅과 실제 일) |
| 정문 안내원 | `CorsMiddleware` |
| 보안 요원 | `AuthMiddleware` |
| 기록원 | `LoggingMiddleware` |
| 「요청 받고 응답 준다」는 공통 규칙 | `Service` 트레이트의 `call` |
| 문 뒤에 있는 다음 문 | 각 미들웨어의 `inner` 필드 |

```text
 요청 →  [ CORS [ Auth [ Logging [ Handler ] ] ] ]
 응답 ←  (안쪽에서 만들어져 바깥으로 되돌아 나온다)
```

## 이 주제가 답하려는 질문

1. 로깅 · 인증 · CORS 같은 공통 처리를 핸들러 코드를 고치지 않고 어떻게 덧붙이나?
2. 미들웨어를 여러 겹 겹치면 요청과 응답은 어떤 차례로 지나가나?
3. 한 미들웨어가 요청을 막을지, 안쪽으로 넘길지는 어떻게 정하나?
4. 손으로 감싼 스택은 실제 Tower 의 `ServiceBuilder` 와 어떻게 이어지나?

## 동작 방식

### (1) `Service` 트레이트 — 모두가 지키는 한 가지 꼴

**언제 쓰나** — 핸들러와 미들웨어를 같은 자리에 끼워 넣을 수 있게 하고 싶을 때 쓴다.

```text
trait Service { fn call(&self, req: Request) -> Response; }

   Request ──▶ [ 무엇이든 Service ] ──▶ Response
```

- `call` 은 요청 하나를 받아 응답 하나를 돌려준다.
- `&self` 로 받으므로 같은 서비스를 여러 번 부를 수 있다.
- `req` 는 값으로 받는다 — 요청의 소유권이 `call` 안으로 옮겨 간다.
- 핸들러(`AppHandler`)도, 미들웨어도 이 트레이트를 구현한다.

이 예제의 `Service` 는 실제 Tower 의 것을 흉내 낸 **동기** 버전이다.
원본 팁이 말하듯 실제 Tower 는 **비동기** 요청-응답 추상화이고, axum · hyper · tonic 이 그 위에 서 있다.

> **트레이트** — 타입이 구현해야 할 메서드 꼴을 정한 Rust 의 약속.\
> 예: `impl Service for AppHandler` 는 `AppHandler` 가 `call` 을 갖추었다는 선언이다.

### (2) 감싸기 — 미들웨어도 `Service` 다

**언제 쓰나** — 기존 서비스 앞뒤에 일을 덧붙이고 싶을 때 쓴다.

```text
struct LoggingMiddleware<S: Service> { inner: S }
impl<S: Service> Service for LoggingMiddleware<S> { fn call(..) { ...; self.inner.call(req); ... } }

   LoggingMiddleware
   ┌──────────────────────────────┐
   │  앞 처리 → inner.call(req) → 뒤 처리 │
   └──────────────────────────────┘
          inner 는 아무 Service 나 될 수 있다
```

- 미들웨어는 안쪽 서비스를 `inner` 필드에 들고 있다.
- `<S: Service>` 라는 제네릭 경계 덕에 `inner` 는 핸들러일 수도, 다른 미들웨어일 수도 있다.
- 미들웨어 자신도 `Service` 를 구현하므로, 또 다른 미들웨어의 `inner` 가 될 수 있다.
- 그래서 「감싼 것을 또 감싼다」가 끝없이 된다 — 정답 코드 주석은 이것을 **양파 패턴**, 그리고 **데코레이터 패턴**이라 부른다.

> **미들웨어** — 핸들러 앞뒤에 끼어 공통 처리를 하는 층.\
> 예: 모든 요청의 처리 시간을 찍는 로깅 층.

> **데코레이터 패턴** — 같은 인터페이스를 가진 객체로 원래 객체를 감싸 기능을 덧붙이는 설계.\
> 예: `LoggingMiddleware::new(handler)` 는 핸들러에 로그 기능을 덧씌운다.

### (3) 스택 조립과 요청 · 응답의 흐름

**언제 쓰나** — 여러 미들웨어의 차례를 정할 때 쓴다.

```text
조립 코드 (안쪽부터 쓴다)
  let handler = AppHandler;
  let logging = LoggingMiddleware::new(handler);
  let auth    = AuthMiddleware::new(logging, vec!["/health"]);
  let app     = CorsMiddleware::new(auth, vec!["*"]);

만들어진 모양
  app = Cors( Auth( Logging( Handler ) ) )

app.call(req) 를 부르면
  요청:  Cors → Auth → Logging → Handler
  응답:  Handler → Logging → Auth → Cors → 호출한 쪽
```

- 조립은 가장 안쪽인 핸들러부터 쓴다.
- 마지막에 감싼 것(`CorsMiddleware`)이 가장 바깥이다.
- `app.call` 은 바깥 층부터 불리고, 각 층이 `inner.call` 을 불러 한 층씩 안으로 들어간다.
- 핸들러가 응답을 만들면, 각 층의 `inner.call(...)` 이 값을 돌려주며 한 층씩 바깥으로 나온다.
- 그래서 「안쪽 호출 뒤에」 하는 일(로그 찍기)은 안쪽 층들의 일이 다 끝난 뒤에 일어난다.

### (4) 로깅 미들웨어 — 안쪽 호출 앞뒤에서 일한다

**언제 쓰나** — 요청마다 메서드 · 경로 · 상태 코드 · 걸린 시간을 남기고 싶을 때 쓴다.

```text
let start  = Instant::now();          ① 시각 기록
let method = req.method.clone();      ② 로그에 쓸 값 복사
let path   = req.path.clone();
let resp   = self.inner.call(req);    ③ req 를 안쪽으로 넘김 (소유권 이동)
println!("  [LOG] {} {} -> {} ({:.3?})", method, path, resp.status, start.elapsed());  ④
resp                                  ⑤ 응답을 그대로 돌려줌
```

- ① 안쪽을 부르기 전에 현재 시각을 잡는다.
- ② `req` 는 ③에서 안쪽으로 옮겨 가 더는 쓸 수 없으므로, 로그에 쓸 메서드와 경로를 미리 복사해 둔다.
- ③ 안쪽 서비스를 부른다.
- ④ 응답이 돌아온 뒤 한 줄을 찍는다 — 상태 코드는 응답에서 읽고, 걸린 시간은 `start.elapsed()` 로 잰다.
- ⑤ 응답은 건드리지 않고 바깥으로 돌려준다.
- 로그 줄은 안쪽(핸들러)의 일이 끝난 **뒤**에 찍힌다.

> **소유권 이동(move)** — 값을 다른 곳에 값으로 넘기면 원래 변수는 더 쓸 수 없게 되는 Rust 의 규칙.\
> 예: `self.inner.call(req)` 뒤에 `req.path` 를 읽으면 컴파일 오류다.

### (5) 인증 미들웨어 — 막거나, 넘기거나

**언제 쓰나** — 일부 경로만 열어 두고 나머지는 토큰을 요구할 때 쓴다.

```text
요청 도착
  │
  ├─ 경로가 public_paths 에 있나? ── 예 ──▶ inner.call(req)   (검사 없이 통과, 아무것도 안 찍음)
  │
  └─ 아니오 → Authorization 헤더가 "Bearer " 로 시작하나?
        ├─ 예   ──▶ "  [AUTH] 인증 성공: <토큰 앞부분>" 찍고 inner.call(req)
        └─ 아니오 ─▶ "  [AUTH] 인증 실패" 찍고 Response::error(401, "Unauthorized")
                      (inner 를 부르지 않는다)
```

- 공개 경로(`/health`)는 헤더를 보지 않고 바로 안쪽으로 넘긴다.
- 헤더가 없거나 `"Bearer "` 로 시작하지 않으면 401 응답을 **직접 만들어** 돌려준다.
- 이때 `inner.call` 을 부르지 않으므로, 안쪽 층(로깅 · 핸들러)은 그 요청을 전혀 모른다 — 이것을 「단락(short-circuit)」이라 한다.
- 성공할 때 찍는 토큰 조각은 `&auth[7..17.min(auth.len())]` 이다.
- `"Bearer "` 가 7바이트이므로 7번 바이트부터, 최대 17번 바이트 앞까지(최대 10바이트)를 잘라 보인다.
- 문자열이 17바이트보다 짧으면 `17.min(auth.len())` 이 끝을 문자열 길이로 줄인다.
- 예를 들어 `"Bearer token"` 은 12바이트라 7..12, 곧 `token` 이 찍힌다.

> **단락(short-circuit)** — 뒤 단계를 부르지 않고 그 자리에서 결과를 정해 돌려주는 것.\
> 예: 인증 실패 시 핸들러를 부르지 않고 바로 401 을 돌려준다.

> **Bearer 토큰** — `Authorization: Bearer <토큰>` 꼴로 보내는 인증 값.\
> 예: `Bearer valid-token-123`.

### (6) CORS 미들웨어 — 이 예제에서는 기록만 한다

**언제 쓰나** — 요청이 어느 출처(Origin)에서 왔는지 따지고 싶을 때 쓴다.

```text
origin  = Origin 헤더 값, 없으면 "unknown"
allowed = 허용 목록 중 하나라도 (o == origin 또는 o == "*")
allowed 가 아니면 "  [CORS] 거부: <origin>" 찍기
어느 쪽이든 inner.call(req)
```

- 허용 목록에 `"*"` 가 있으면 어떤 출처든, `Origin` 헤더가 없어도 허용된다.
- 허용되지 않아도 이 예제는 **요청을 막지 않는다** — 한 줄 찍고 그대로 안쪽으로 넘긴다.
- 정답 코드 주석은 이것이 단순 로깅일 뿐이고, 실제 CORS 는 응답에 헤더를 덧붙이는 일이라고 적는다.

> **CORS** — 브라우저가 다른 출처의 요청을 허용할지 판단하게 하는 규칙. 서버는 응답 헤더로 허용을 알린다.\
> 예: 이 예제의 `allowed_origins` 에 `"*"` 를 넣으면 모든 출처를 허용한다는 뜻이다.

### (7) 실제 Tower — `Layer` 와 `ServiceBuilder`

**언제 쓰나** — 실무 서버(axum 등)에 미들웨어를 붙일 때 쓴다.

```text
ServiceBuilder::new()
    .layer(TraceLayer::new_for_http())                    ← 가장 바깥 (로깅)
    .layer(CorsLayer::permissive())                       ← 그 안 (CORS)
    .layer(TimeoutLayer::new(Duration::from_secs(30)))    ← 그 안 (타임아웃)
    .service(router);                                     ← 가장 안쪽

요청: Trace → Cors → Timeout → router
응답: router → Timeout → Cors → Trace
```

- 원본 팁: 미들웨어를 체이닝하는 단위가 `Layer` 다.
- 원본 팁: `ServiceBuilder` 로 스택을 조립하며, **위에서 아래로** 적용된다 — 요청은 위에서 아래로, 응답은 아래에서 위로 흐른다.
- 곧 `ServiceBuilder` 에서는 **바깥 층을 먼저** 쓴다. 손 조립(안쪽부터 쓴다)과 쓰는 차례가 반대다.
- 원본 팁: 흔히 쓰는 미들웨어는 `tower-http` 크레이트의 `TraceLayer` · `CorsLayer` · `CompressionLayer` 다.
- 원본 설명은 타임아웃 미들웨어를 말하지만, 이 예제 코드는 타임아웃을 직접 구현하지 않는다 — `TimeoutLayer` 는 마지막에 찍는 `ServiceBuilder` 예시 문자열에만 나온다.

> **`Layer`** — 서비스 하나를 받아 그것을 감싼 새 서비스를 만들어 주는 Tower 의 단위.\
> 예: `TraceLayer` 는 서비스를 받아 로깅 서비스로 감싼다.

## 문법 — 형태와 규칙

새 미들웨어 하나를 만드는 최소 꼴이다(직접 쓴 예):

```rust
// 요청 경로를 찍고 그대로 넘기는 최소 미들웨어
struct PathPrinter<S: Service> {
    inner: S,
}

impl<S: Service> Service for PathPrinter<S> {
    fn call(&self, req: Request) -> Response {
        println!("  [PATH] {}", req.path); // 넘기기 전에는 req 를 읽을 수 있다
        let resp = self.inner.call(req);   // 여기서 req 는 안쪽으로 옮겨 간다
        println!("  [PATH] status {}", resp.status);
        resp
    }
}

// 감싸기: let app = PathPrinter { inner: AppHandler };
```

- 미들웨어 구조체는 `inner: S` 필드와 `<S: Service>` 경계를 갖는다.
- `impl<S: Service> Service for 미들웨어<S>` 로 자신도 `Service` 가 된다.
- 넘기기: `self.inner.call(req)` 를 부르고 그 결과를 돌려준다.
- 막기: `inner.call` 을 부르지 않고 `Response::error(...)` 같은 응답을 직접 돌려준다.
- 뒤 처리가 요청 값을 써야 하면, `inner.call(req)` **앞에서** 필요한 필드를 `clone()` 해 둔다.
- 설정값(공개 경로 · 허용 출처)은 `new` 에서 `Vec<&str>` 로 받아 `iter().map(|s| s.to_string()).collect()` 로 `Vec<String>` 에 담는다.
- 조립은 `let 바깥 = 미들웨어::new(안쪽, ...)` 을 안쪽부터 차례로 쓴다.
- 요청 쪽 도우미: `with_header(mut self, ..) -> Self` 는 `self` 를 받아 고친 뒤 돌려주므로 `.with_header(..).with_header(..)` 로 이어 쓸 수 있다.
- `get_header` 는 이름이 **글자 그대로 같은** 첫 헤더의 값을 `Option<&str>` 로 돌려준다.
- 원본의 모듈 구성 조언: 미들웨어는 보통 `src/middleware/` 모듈로 묶고 `mod auth; mod cors; mod logging;` 처럼 파일을 나눈다. `tower-http` 같은 외부 크레이트는 `Cargo.toml` 의 dependencies 에 넣은 뒤 `use tower_http::trace::TraceLayer;` 꼴로 가져온다.

## 어디서 틀리나

### 1. 조립 코드의 차례를 요청 흐름으로 읽는다
손 조립은 `handler → logging → auth → cors` 차례로 **쓰지만**, 요청은 `cors → auth → logging → handler` 차례로 **지나간다**.
마지막에 감싼 것이 가장 바깥이다.
`ServiceBuilder` 는 반대로 위에 쓴 층이 바깥이다 — 두 방식을 섞어 생각하면 차례를 거꾸로 읽게 된다.

### 2. 안쪽으로 넘긴 `req` 를 다시 쓴다
`self.inner.call(req)` 뒤에 `req.method` 를 읽으려 하면 소유권이 이미 옮겨 가 컴파일되지 않는다.
로깅 미들웨어가 `method` 와 `path` 를 먼저 `clone()` 하는 까닭이 이것이다.

### 3. 막는 층보다 안쪽에 둔 로그는 막힌 요청을 못 본다
이 스택에서 로깅은 인증 **안쪽**에 있다.
인증이 401 로 단락하면 로깅의 `call` 은 불리지 않으므로 `[LOG]` 줄이 남지 않는다.
거절된 요청까지 기록하려면 로깅을 인증 바깥에 두어야 한다.
`ServiceBuilder` 예시에서 `TraceLayer` 를 맨 위(가장 바깥)에 둔 것도 같은 생각이다.

### 4. 토큰 자르기가 바이트 기준이다
`&auth[7..17.min(auth.len())]` 는 **바이트** 위치로 자른다.
Rust 문자열 슬라이스는 경계가 UTF-8 문자 한가운데에 떨어지면 패닉한다.
토큰에 한글처럼 여러 바이트짜리 글자가 있고 17번 바이트가 그 글자 중간이면, 인증 성공 줄을 찍다가 프로그램이 멈춘다.
7번 바이트는 늘 안전하다 — 앞의 `"Bearer "` 가 모두 ASCII 라 7바이트로 딱 끝나기 때문이다.
또 토큰의 일부라도 로그에 찍는 것은 비밀값을 남기는 일이라 실무에서는 조심한다.

### 5. 이 CORS 미들웨어는 아무것도 막지 않는다
허용되지 않은 출처여도 `[CORS] 거부` 를 찍을 뿐 `inner.call` 을 그대로 부른다.
「거부」라는 글자만 보고 요청이 차단되었다고 읽으면 틀린다.
실제 CORS 처리는 응답에 헤더를 덧붙이는 일이다.

### 6. 헤더 이름과 접두사를 글자 그대로 비교한다
`get_header` 는 `k == key` 로 비교하므로 `"authorization"` 처럼 대소문자가 다르면 찾지 못한다.
`starts_with("Bearer ")` 도 대소문자와 뒤의 빈칸까지 맞아야 한다.
실제 HTTP 에서 헤더 이름은 대소문자를 가리지 않으므로, 이 단순화는 실무 코드와 다르다.

### 7. 이 `Service` 를 실제 Tower 의 것으로 착각한다
원본 팁대로 Tower 는 **비동기** 추상화이고, 이 예제의 `call` 은 동기 함수다.
그래서 이 예제는 원본 설명에 나오는 타임아웃을 구현하지 않았고, 타임아웃은 `ServiceBuilder` 예시 문자열에만 등장한다.
`Layer` 도 이 예제에는 없다 — 여기서는 `Middleware::new(inner)` 가 `Layer` 의 일을 대신한다.

### 8. 쓰지 않는 필드가 남아 있다
`Request` 의 `body` 필드는 만들기만 하고 어디서도 읽지 않는다.
요청 모델을 흉내 내려고 둔 자리일 뿐, 이 예제의 동작에는 관여하지 않는다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `inner.call(req)` 뒤에는 `req` 를 쓸 수 없다 | Rust 언어(소유권 규칙) |
| 문자 경계가 아닌 바이트 위치로 `&str` 을 자르면 패닉한다 | Rust 표준 라이브러리(`str` 인덱싱 규칙) |
| `{:.3?}` 로 `Duration` 을 찍는 모양 | 표준 라이브러리의 `Debug` 구현 — 언어가 정한 꼴이 아니다 |
| 이 예제의 `Service` 는 `call(&self, Request) -> Response` 하나뿐이다 | 이 예제 코드만의 단순화 — 실제 Tower 의 트레이트와 다르다 |
| `ServiceBuilder` 는 위에 쓴 층이 바깥이 된다 | `tower` 크레이트의 API 약속(원본 팁) — 언어가 아니다 |
| `TraceLayer` · `CorsLayer` · `CompressionLayer` 는 `tower-http` 에 있다 | `tower-http` 크레이트(원본 팁) |
| `Instant::now()` 와 `elapsed()` 의 정밀도 | 운영체제와 표준 라이브러리 구현에 달렸다(확인 필요) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 모든 요청에 같은 처리(로그 · 인증 · CORS)를 붙인다 | 미들웨어 한 층 | 핸들러의 각 분기마다 같은 코드를 복사하기 |
| 조건에 따라 요청을 거절한다 | `inner.call` 을 부르지 않고 응답을 직접 돌려주기 | 안쪽까지 보낸 뒤 핸들러에서 거절하기 |
| 거절된 요청까지 기록한다 | 로깅을 막는 층보다 바깥에 두기 | 로깅을 인증 안쪽에 두기 |
| 실무 axum · hyper · tonic 서버 | `tower` · `tower-http` 의 `Layer` 와 `ServiceBuilder` | 이 예제의 동기 `Service` 를 그대로 가져가기 |
| 특정 경로 하나에서만 하는 일 | 그 핸들러 안의 코드 | 모든 요청이 지나는 미들웨어 |
| 미들웨어가 여럿이 된다 | `src/middleware/` 아래 `mod auth; mod cors; mod logging;` | 한 파일에 몰아넣기 |

## 핵심 문장

1. **핸들러와 미들웨어가 모두 `Service` 를 구현하므로, 미들웨어는 아무 서비스나 `inner` 로 감쌀 수 있다** — 감싼 것을 또 감싸는 양파 구조가 된다.
2. **손 조립은 안쪽부터 쓰고, 요청은 바깥부터 지나며, 응답은 안쪽부터 되돌아 나온다.**
3. **미들웨어는 `inner.call` 을 부르면 넘기고, 부르지 않으면 막는다** — 막힌 요청은 안쪽 층에 닿지 않는다.
4. **안쪽 호출 뒤에 하는 일은 안쪽 일이 다 끝난 뒤에 일어나고, 그때 쓸 요청 값은 미리 복사해야 한다.**
5. **실제 Tower 는 비동기이고, `ServiceBuilder` 에서는 위에 쓴 `Layer` 가 바깥이다.**

## 관련 자료

- `rest-api-axum` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- [auth-jwt](../08-auth-jwt/2-summary.md)
- [logging-tracing](../03-logging-tracing/2-summary.md)
- 원본: study-site 항목 데이터 `data/rust/project-structures.json` 의 `middleware-tower`

## 용어 풀이

- **Tower** — 비동기 요청-응답을 추상화한 Rust 크레이트. axum · hyper · tonic 의 기반이다.
- **`Service`** — 요청을 받아 응답을 돌려주는 공통 꼴. 이 예제에서는 `call(&self, Request) -> Response`.
- **`Layer`** — 서비스를 받아 감싼 서비스를 만드는 Tower 의 미들웨어 단위.
- **`ServiceBuilder`** — 여러 `Layer` 를 위에서 아래 차례로 쌓아 서비스 스택을 만드는 Tower 도구.
- **미들웨어** — 핸들러 앞뒤에 끼어 공통 처리를 하는 층.
- **핸들러** — 스택의 가장 안쪽에서 실제 일을 하는 서비스. 이 예제에서는 `AppHandler`.
- **`inner`** — 미들웨어가 감싸고 있는 바로 안쪽 서비스.
- **양파 패턴** — 층이 겹겹이 싸여 요청은 바깥에서 안으로, 응답은 안에서 바깥으로 흐르는 구조.
- **데코레이터 패턴** — 같은 인터페이스로 감싸 기능을 덧붙이는 설계.
- **단락(short-circuit)** — 뒤 단계를 부르지 않고 그 자리에서 결과를 돌려주는 것.
- **트레이트** — 타입이 구현할 메서드 꼴을 정한 Rust 의 약속.
- **제네릭 경계 `<S: Service>`** — `S` 자리에 `Service` 를 구현한 타입만 올 수 있다는 조건.
- **소유권 이동(move)** — 값으로 넘기면 원래 변수는 더 쓸 수 없게 되는 규칙.
- **Bearer 토큰** — `Authorization: Bearer <토큰>` 꼴의 인증 값.
- **CORS** — 다른 출처의 요청 허용 여부를 응답 헤더로 알리는 브라우저 규칙.
- **Origin 헤더** — 요청이 어느 출처에서 왔는지 알리는 헤더.
- **공개 경로** — 인증 없이 통과시키는 경로. 이 예제에서는 `/health`.
- **`tower-http`** — `TraceLayer` · `CorsLayer` · `CompressionLayer` 같은 HTTP 미들웨어를 모은 크레이트.

## 더 들어가면

- 실제 Tower 의 `Service` 트레이트는 연관 타입 `Response` · `Error` · `Future` 와, 호출 전에 받을 준비가 되었는지 묻는 `poll_ready`, 그리고 `Future` 를 돌려주는 `call(&mut self, req)` 로 이루어진다(확인 필요).
- 실제 `Layer` 트레이트는 `fn layer(&self, inner: S) -> Self::Service` 꼴로, 이 예제의 `Middleware::new(inner)` 에 해당한다(확인 필요).
- 타임아웃은 안쪽 작업이 끝나기를 기다리는 동안 시간을 재다 먼저 포기해야 하는 일이라, 동기 `call` 로는 바깥에서 끊기 어렵고 비동기 `Future` 위에서 자연스럽다(확인 필요).
- 제네릭으로 감싸면 최종 타입이 `CorsMiddleware<AuthMiddleware<LoggingMiddleware<AppHandler>>>` 처럼 길어지지만, 정적 디스패치라 호출마다 동적 조회가 없다. 대신 층을 런타임에 바꾸려면 `Box<dyn Service>` 같은 방식이 필요하다(확인 필요).
- axum 에서는 `Router::layer(...)` 로 Tower `Layer` 를 붙일 수 있고, 라우트별로 붙이는 방법도 있다(확인 필요).
- `tower-http` 의 각 미들웨어는 크레이트 기능 플래그(features)를 켜야 쓸 수 있는 경우가 있다(확인 필요).
- 컴파일러는 읽지 않는 필드(`body`)에 대해 dead code 경고를 낼 수 있다(확인 필요).
