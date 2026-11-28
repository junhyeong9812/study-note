# rust/rust-project-structures/09 — Tower 미들웨어 패턴 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 인증 헤더 없이 `POST /users` 를 보내면 (예측)

```rust
// 질문용 발췌
let handler = AppHandler;
let logging = LoggingMiddleware::new(handler);
let auth = AuthMiddleware::new(logging, vec!["/health"]);
let app = CorsMiddleware::new(auth, vec!["*"]);

let resp = app.call(Request::new("POST", "/users"));
println!("  응답: {} {}\n", resp.status, resp.body);
```

- `[CORS]` · `[AUTH]` · `[LOG]` 가운데 어느 줄이 찍히고, 응답 줄에는 무엇이 찍히는가?

### 2. 토큰 `valid-token-123` 의 인증 성공 줄 (예측)

```rust
// 질문용 발췌 — auth 는 "Bearer valid-token-123"
println!("  [AUTH] 인증 성공: {}", &auth[7..17.min(auth.len())]);
```

- `인증 성공:` 뒤에 찍히는 글자는 무엇인가?

### 3. `Bearer token` 을 붙여 `GET /unknown` 을 보내면 (예측)

- 문항 1 과 같은 스택에 `Authorization: Bearer token` 만 붙이고 `Origin` 헤더 없이 `GET /unknown` 을 보내면, 어떤 줄이 어떤 차례로 찍히는가?

### 4. 로깅 미들웨어가 `method` 와 `path` 를 먼저 복사하는 까닭 (왜)

- `LoggingMiddleware` 는 왜 `inner.call(req)` 를 부르기 전에 `req.method.clone()` 과 `req.path.clone()` 을 해 두는가?

### 5. 미들웨어도 `Service` 를 구현하게 만든 까닭 (왜)

- 미들웨어 구조체가 스스로 `Service` 트레이트를 구현하지 않으면 스택 조립의 어디가 막히는가?

### 6. 허용 목록에 없는 출처가 오면 (경계)

- `CorsMiddleware::new(auth, vec!["http://a.com"])` 로 만든 스택에 `Origin: http://b.com` 인 요청이 오면, 그 요청은 핸들러까지 가는가?

### 7. 토큰 자르기가 깨지는 입력 (경계)

- `&auth[7..17.min(auth.len())]` 가 프로그램을 패닉시키는 `Authorization` 값은 어떤 꼴인가?

### 8. 로깅을 인증 바깥으로 옮기면 (예측)

```rust
// 질문용 발췌 — 조립 차례만 바꿨다
let handler = AppHandler;
let auth = AuthMiddleware::new(handler, vec!["/health"]);
let logging = LoggingMiddleware::new(auth);
let app = CorsMiddleware::new(logging, vec!["*"]);

let resp = app.call(Request::new("POST", "/users"));
```

- 이번에는 어떤 줄들이 어떤 차례로 찍히는가?

### 9. 손 조립 차례와 `ServiceBuilder` 차례 (연결)

- 이 예제의 손 조립에서 가장 바깥 층은 몇 번째 줄에 쓰고, `ServiceBuilder` 에서 가장 바깥 층은 몇 번째 `.layer` 에 쓰는가?

### 10. 이 감싸기 구조와 프로젝트의 모듈 나누기 (연결)

- 미들웨어를 `inner` 로 감싸 기능을 덧붙이는 이 구조는 어떤 설계 패턴이라 부르는가?
- 미들웨어가 셋으로 늘었을 때 실무 Rust 프로젝트에서는 파일과 모듈을 어떻게 나누는가?

## 실습

### 실습 1. 손으로 만든 Tower 식 미들웨어 스택

**만들 것** — `Service` 트레이트 하나를 핸들러와 세 미들웨어(CORS · 인증 · 로깅)가 함께 구현하게 하고, 그것들을 겹겹이 감싸 네 가지 요청을 흘려 본다.

**준비물** — 외부 크레이트는 필요 없다. 표준 라이브러리만으로 실제 Tower 의 `Service` · 미들웨어를 동기 버전으로 흉내 낸 것이다.

**요구 조건**

1단계 — 요청 도구

1. `Request::get_header(&self, key)` 는 이름이 `key` 와 글자 그대로 같은 첫 헤더의 값을 `Option<&str>` 로 돌려준다.

2단계 — `Service` 와 핸들러

2. `Service` 트레이트는 `call(&self, req: Request) -> Response` 메서드 하나를 갖는다.
3. `AppHandler` 는 (메서드, 경로)로 라우팅한다: `GET /health` → 200 `OK`, `GET /users` → 200 `[{"id": 1, "name": "Alice"}]`, `POST /users` → 200 `{"id": 2, "name": "New"}`, 나머지 → 404 `Not Found`.

3단계 — 미들웨어 셋 (모두 `<S: Service>` 로 `inner` 를 감싸고, 자신도 `Service` 를 구현한다)

4. `LoggingMiddleware` 는 안쪽을 부르기 전에 시각을 잡고, 안쪽이 돌려준 뒤 `  [LOG] 메서드 경로 -> 상태 (경과시간)` 한 줄을 찍고(경과시간은 `{:.3?}`), 응답을 그대로 돌려준다.
5. `AuthMiddleware` 는 경로가 공개 경로 목록에 있으면 검사 없이 안쪽으로 넘긴다.
6. 그 밖에는 `Authorization` 헤더가 `"Bearer "` 로 시작하면 `  [AUTH] 인증 성공: <7번 바이트부터 최대 10바이트>` 를 찍고 안쪽으로 넘기고, 아니면 `  [AUTH] 인증 실패` 를 찍고 안쪽을 부르지 않은 채 401 `Unauthorized` 를 돌려준다.
7. `CorsMiddleware` 는 `Origin` 헤더(없으면 `"unknown"`)가 허용 목록의 값과 같거나 목록에 `"*"` 가 있으면 허용으로 본다. 허용이 아니면 `  [CORS] 거부: <origin>` 을 찍는다. 어느 쪽이든 안쪽으로 넘긴다.

4단계 — 조립과 시연

8. `main` 은 핸들러 → 로깅 → 인증(공개 경로 `/health`) → CORS(허용 `"*"`) 차례로 감싸 `app` 을 만든다.
9. `app` 에 네 요청을 보내고 각 응답의 상태와 본문을 찍는다: `GET /health`, `Authorization: Bearer valid-token-123` 과 `Origin: http://example.com` 을 붙인 `GET /users`, 헤더 없는 `POST /users`, `Authorization: Bearer token` 을 붙인 `GET /unknown`.
10. 마지막에 실제 Tower 의 `ServiceBuilder` 조립 예시를 원시 문자열로 찍는다.

**시작 코드**

```rust
use std::time::Instant;

#[derive(Debug, Clone)]
struct Request {
    method: String,
    path: String,
    headers: Vec<(String, String)>,
    body: String,
}

impl Request {
    fn new(method: &str, path: &str) -> Self {
        Request { method: method.into(), path: path.into(), headers: Vec::new(), body: String::new() }
    }

    fn with_header(mut self, key: &str, value: &str) -> Self {
        self.headers.push((key.into(), value.into()));
        self
    }

    fn get_header(&self, key: &str) -> Option<&str> {
        // TODO: 이름이 key 와 같은 첫 헤더의 값을 돌려준다
        todo!()
    }
}

#[derive(Debug)]
struct Response {
    status: u16,
    body: String,
}

impl Response {
    fn ok(body: &str) -> Self { Response { status: 200, body: body.into() } }
    fn error(status: u16, body: &str) -> Self { Response { status, body: body.into() } }
}

// TODO: Service 트레이트 (call 하나)

struct AppHandler;
// TODO: impl Service for AppHandler — (메서드, 경로)로 라우팅

struct LoggingMiddleware<S: Service> {
    inner: S,
}
// TODO: new, 그리고 impl<S: Service> Service — 시각 기록, 값 복사, 안쪽 호출, [LOG] 한 줄

struct AuthMiddleware<S: Service> {
    inner: S,
    public_paths: Vec<String>,
}
// TODO: new(inner, Vec<&str>), 그리고 impl Service — 공개 경로 통과 / Bearer 검사 / 401

struct CorsMiddleware<S: Service> {
    inner: S,
    allowed_origins: Vec<String>,
}
// TODO: new(inner, Vec<&str>), 그리고 impl Service — Origin 확인, 거부면 찍기, 늘 안쪽으로

fn main() {
    println!("=== Tower 미들웨어 패턴 ===");
    println!("스택: CORS -> Auth -> Logging -> Handler\n");

    // TODO: handler → logging → auth → app(CORS) 차례로 감싸기

    println!("--- GET /health (공개) ---");
    // TODO: 요청 1 보내고 "  응답: {} {}\n" 찍기

    println!("--- GET /users (인증 있음) ---");
    // TODO: 요청 2 (Authorization, Origin 헤더)

    println!("--- POST /users (인증 없음) ---");
    // TODO: 요청 3

    println!("--- GET /unknown ---");
    // TODO: 요청 4 (Authorization: Bearer token), 응답 줄은 끝에 빈 줄 없이

    println!("\n=== 실제 Tower 미들웨어 ===");
    // TODO: ServiceBuilder 조립 예시를 r#"..."# 원시 문자열로 찍기
}
```

**확인 방법** — `rustc middleware-tower.rs && ./middleware-tower` 로 돌려, 네 요청마다 `[AUTH]` · `[LOG]` 줄이 어떤 요청에 찍히고 어떤 요청에 빠지는지, 응답 상태가 200 · 200 · 401 · 404 인지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
