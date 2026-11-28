# rust/rust-project-structures/09 — Tower 미들웨어 패턴 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. `[AUTH] 인증 실패` 만 찍히고 401 — 로깅까지 닿지 않는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
  [AUTH] 인증 실패
  응답: 401 Unauthorized
```

`응답:` 줄 뒤에는 `\n` 때문에 빈 줄이 하나 더 생긴다.

**왜 그런가**
- CORS 층: `Origin` 헤더가 없어 `"unknown"` 이지만 허용 목록에 `"*"` 가 있어 허용이다 — 아무것도 찍지 않고 넘긴다.
- 인증 층: `/users` 는 공개 경로가 아니고 `Authorization` 헤더가 없으므로 `인증 실패` 를 찍고 401 을 직접 돌려준다.
- 인증 층이 `inner.call` 을 부르지 않으므로 그 안쪽의 로깅 층과 핸들러는 불리지 않는다 — `[LOG]` 줄이 없다.
- 근거: 2-summary 「동작 방식 (5)」 · 「동작 방식 (6)」 · 「어디서 틀리나 3」.

### 2. `valid-toke` — 앞 10바이트만 잘린다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
  [AUTH] 인증 성공: valid-toke
```

**왜 그런가**
- `"Bearer valid-token-123"` 은 `"Bearer "` 7바이트 + `"valid-token-123"` 15바이트 = 22바이트다.
- `17.min(22)` 은 17 이므로 7..17, 곧 7번 바이트부터 10바이트가 잘린다.
- `valid-token-123` 의 앞 10글자(모두 ASCII 라 한 글자 = 한 바이트)는 `valid-toke` 다.
- 근거: 2-summary 「동작 방식 (5)」.

### 3. 인증 성공 → 로그(404) → 응답 404 차례

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
  [AUTH] 인증 성공: token
  [LOG] GET /unknown -> 404 (<경과 시간>)
  응답: 404 Not Found
```

`<경과 시간>` 자리는 실행할 때마다 다른 값이 `{:.3?}` 꼴로 들어간다.

**왜 그런가**
- CORS 층: `Origin` 이 없어도 `"*"` 허용이라 찍는 것 없이 넘긴다.
- 인증 층: `"Bearer token"` 은 12바이트라 `17.min(12)` = 12, 7..12 가 `token` 이다. 성공을 찍고 안쪽으로 넘긴다.
- 로깅 층: 시각을 잡고 핸들러를 부른다.
- 핸들러: `("GET", "/unknown")` 은 어느 분기와도 맞지 않아 404 `Not Found` 를 돌려준다.
- 로깅 층은 응답이 돌아온 **뒤** 로그를 찍으므로 `[LOG]` 줄은 `[AUTH]` 줄 다음에 온다.
- 인증은 통과했지만 라우팅에서 404 가 난 것이다 — 두 층의 책임이 다르다.
- 근거: 2-summary 「동작 방식 (3)」 · 「동작 방식 (4)」 · 「동작 방식 (5)」.

### 4. `req` 가 안쪽으로 옮겨 간 뒤에는 읽을 수 없기 때문이다

`self.inner.call(req)` 는 `req` 를 값으로 넘기므로 소유권이 안쪽으로 옮겨 간다.
로그는 응답이 돌아온 뒤에 찍어야 하는데, 그때는 `req.method` · `req.path` 를 쓸 수 없다.
그래서 넘기기 전에 필요한 두 값을 복사해 둔다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 2」.

### 5. 미들웨어를 다른 미들웨어의 `inner` 로 넣을 수 없게 된다

각 미들웨어의 `inner` 는 `<S: Service>` 로 제한되어 있다.
`LoggingMiddleware` 가 `Service` 를 구현하지 않으면 `AuthMiddleware::new(logging, ...)` 의 `S` 자리에 넣을 수 없고, 감싼 것을 또 감싸는 양파 구조가 끊긴다.
또 가장 바깥 `app` 에서 `app.call(...)` 을 부를 수도 없다.
근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (2)」.

### 6. 간다 — 이 CORS 층은 거부를 찍기만 한다

`"http://b.com"` 은 목록의 `"http://a.com"` 과 다르고 목록에 `"*"` 도 없으므로 허용이 아니다.
그래서 `  [CORS] 거부: http://b.com` 을 찍는다.
하지만 그 뒤 어느 쪽이든 `self.inner.call(req)` 를 부르므로 요청은 인증 층으로 넘어가고, 인증을 통과하면 핸들러까지 간다.
실제 CORS 처리는 응답에 헤더를 덧붙이는 일이다.
근거: 2-summary 「동작 방식 (6)」 · 「어디서 틀리나 5」.

### 7. `"Bearer "` 뒤에 여러 바이트 글자가 있어 17번 바이트가 글자 한가운데에 떨어지는 값

슬라이스 범위는 바이트 위치다.
`auth` 가 17바이트보다 길고, 17번 바이트가 UTF-8 글자(예: 3바이트짜리 한글)의 중간이면 `&auth[7..17]` 이 패닉한다.
예를 들어 `"Bearer 토큰값입니다"` 는 `토`(7~9) · `큰`(10~12) · `값`(13~15) · `입`(16~18) 이라 17번 바이트가 `입` 의 중간이다.
시작 위치 7번은 늘 안전하다 — `"Bearer "` 가 모두 ASCII 라 7바이트에서 딱 끝나기 때문이다.
17바이트보다 짧으면 `17.min(len)` 이 끝을 문자열 끝으로 줄이므로 길이 때문에는 패닉하지 않는다.
근거: 2-summary 「어디서 틀리나 4」 · 「동작 방식 (5)」.

### 8. 이번에는 401 도 로그에 남는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
  [AUTH] 인증 실패
  [LOG] POST /users -> 401 (<경과 시간>)
```

**왜 그런가**
- 이제 요청은 CORS → 로깅 → 인증 → 핸들러 차례로 지나간다.
- 로깅 층이 시각을 잡고 인증 층을 부른다.
- 인증 층은 실패를 찍고 401 을 돌려준다 — 핸들러는 불리지 않는다.
- 로깅 층은 돌아온 응답(401)을 받아 그 뒤에 `[LOG]` 줄을 찍는다.
- 막는 층보다 **바깥**에 있는 로깅은 막힌 요청도 본다.
- 근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 3」.

### 9. 손 조립은 마지막 줄, `ServiceBuilder` 는 첫 `.layer`

손 조립은 안쪽(핸들러)부터 써 나가므로, 가장 바깥 층(`CorsMiddleware`)은 **마지막** 줄에 쓴다.
`ServiceBuilder` 는 위에서 아래로 적용되어 요청이 위에서 아래로 흐르므로, 가장 바깥 층(`TraceLayer`)은 **첫 번째** `.layer` 에 쓰고 핸들러(`router`)는 맨 끝 `.service` 에 온다.
쓰는 차례는 반대지만, 만들어지는 양파의 모양은 같은 원리다.
근거: 2-summary 「동작 방식 (3)」 · 「동작 방식 (7)」 · 「어디서 틀리나 1」.

### 10. 데코레이터 패턴 · `src/middleware/` 모듈

같은 `Service` 인터페이스로 원래 서비스를 감싸 기능을 덧붙이므로 데코레이터 패턴이다(겹겹이 싸인 모양 때문에 양파 패턴이라고도 부른다).
실무에서는 미들웨어를 `src/middleware/` 모듈로 묶고 `mod auth; mod cors; mod logging;` 처럼 파일을 나눈다.
`tower-http` 같은 외부 크레이트는 dependencies 에 넣고 `use tower_http::trace::TraceLayer;` 꼴로 가져온다.
근거: 2-summary 「동작 방식 (2)」 · 「문법 — 형태와 규칙」.

## 실습 정답

### 실습 1. 손으로 만든 Tower 식 미들웨어 스택

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 이름이 같은 첫 헤더의 값 | `Request::get_header` — `iter().find(|(k, _)| k == key).map(|(_, v)| v.as_str())` |
| 2. `call` 하나짜리 트레이트 | `trait Service { fn call(&self, req: Request) -> Response; }` |
| 3. (메서드, 경로) 라우팅 | `impl Service for AppHandler` 의 `match (req.method.as_str(), req.path.as_str())` |
| 4. 시각 · 복사 · 안쪽 호출 · `[LOG]` | `impl<S: Service> Service for LoggingMiddleware<S>` — `Instant::now()`, `clone()`, `self.inner.call(req)`, `println!("  [LOG] ...")` |
| 5. 공개 경로 통과 | `AuthMiddleware::call` 의 `if self.public_paths.contains(&req.path)` |
| 6. Bearer 검사와 401 단락 | `match req.get_header("Authorization")` 의 `Some(auth) if auth.starts_with("Bearer ")` 와 `_ => Response::error(401, "Unauthorized")` |
| 7. Origin 확인과 거부 찍기 | `CorsMiddleware::call` 의 `unwrap_or("unknown")`, `any(|o| o == origin || o == "*")`, `if !allowed` |
| 3단계 공통: `<S: Service>` 로 감싸기 | 각 미들웨어의 `inner: S` 와 `new(inner, ...)` |
| 8. 안쪽부터 감싸기 | `main` 의 `handler` → `logging` → `auth` → `app` |
| 9. 네 요청과 응답 줄 | `main` 의 네 `app.call(...)` 과 `println!("  응답: {} {}...")` |
| 10. `ServiceBuilder` 예시 | `main` 끝의 `println!(r#"use tower::ServiceBuilder; ..."#)` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`rust/rust-project-structures/reference/middleware-tower.rs`

```rust
// [실무 프로젝트 구조] Tower 미들웨어 패턴
// 설명: Tower Service/Layer 패턴: 요청 로깅, 인증, 타임아웃 미들웨어
// 팁: Tower는 비동기 요청-응답 추상화로, axum/hyper/tonic의 기반이다. Service 트레이트: call(Request) -> Response. Layer로 미들웨어를 체이닝한다. ServiceBuilder로 스택을 조립: 위에서 아래로 적용되고, 요청은 위에서 아래로, 응답은 아래에서 위로 흐른다. 공통 미들웨어: tower-http의 TraceLayer, CorsLayer, CompressionLayer.
// Rust 모듈 시스템 특징: 미들웨어는 보통 src/middleware/ 모듈로 묶고 mod auth; mod cors; mod logging;으로 분리한다. 각 미들웨어는 제네릭 <S: Service>로 inner 서비스를 감싸 데코레이터 패턴 구현. tower-http 같은 외부 크레이트는 dependencies에 추가 후 use tower_http::trace::TraceLayer; 형태로 사용.

// 응답 시간 측정용
use std::time::Instant;

// === 요청/응답 타입 ===
// HTTP 요청 모델 (실제로는 http::Request)
#[derive(Debug, Clone)]
struct Request {
    method: String,
    path: String,
    headers: Vec<(String, String)>,
    body: String,
}

// 빌더 스타일 메서드
impl Request {
    // 메서드와 경로로 요청 생성
    fn new(method: &str, path: &str) -> Self {
        Request {
            method: method.into(),
            path: path.into(),
            headers: Vec::new(),
            body: String::new(),
        }
    }

    // 헤더 추가 (체이닝)
    fn with_header(mut self, key: &str, value: &str) -> Self {
        self.headers.push((key.into(), value.into()));
        self
    }

    // 헤더 값 조회
    fn get_header(&self, key: &str) -> Option<&str> {
        self.headers.iter()
            .find(|(k, _)| k == key)
            .map(|(_, v)| v.as_str())
    }
}

// HTTP 응답 모델
#[derive(Debug)]
struct Response {
    status: u16,
    body: String,
}

// 응답 생성 헬퍼
impl Response {
    // 200 OK
    fn ok(body: &str) -> Self {
        Response { status: 200, body: body.into() }
    }
    // 임의 상태 코드의 에러 응답
    fn error(status: u16, body: &str) -> Self {
        Response { status, body: body.into() }
    }
}

// === Service 트레이트 (Tower 패턴) ===
// 모든 핸들러/미들웨어가 구현하는 공통 인터페이스
trait Service {
    fn call(&self, req: Request) -> Response;
}

// === 실제 핸들러 (innermost) ===
// 미들웨어 스택의 가장 안쪽 - 최종 비즈니스 로직
struct AppHandler;

// 라우팅 + 응답
impl Service for AppHandler {
    fn call(&self, req: Request) -> Response {
        // 메서드 + 경로 패턴 매칭으로 라우팅
        match (req.method.as_str(), req.path.as_str()) {
            ("GET", "/health") => Response::ok("OK"),
            ("GET", "/users") => Response::ok("[{\"id\": 1, \"name\": \"Alice\"}]"),
            ("POST", "/users") => Response::ok("{\"id\": 2, \"name\": \"New\"}"),
            _ => Response::error(404, "Not Found"),
        }
    }
}

// === 로깅 미들웨어 ===
// inner Service를 감싸 요청/응답을 로그
struct LoggingMiddleware<S: Service> {
    inner: S,
}

impl<S: Service> LoggingMiddleware<S> {
    fn new(inner: S) -> Self {
        LoggingMiddleware { inner }
    }
}

// 미들웨어도 Service trait 구현 → 다른 미들웨어로 감쌀 수 있음
impl<S: Service> Service for LoggingMiddleware<S> {
    fn call(&self, req: Request) -> Response {
        // 시작 시각 기록
        let start = Instant::now();
        // 이후 로그용으로 미리 복사 (req는 inner로 이동)
        let method = req.method.clone();
        let path = req.path.clone();

        // 안쪽 서비스 호출
        let resp = self.inner.call(req);

        // 응답 후 로그
        println!("  [LOG] {} {} -> {} ({:.3?})",
                 method, path, resp.status, start.elapsed());
        resp
    }
}

// === 인증 미들웨어 ===
// 공개 경로 외에는 Authorization 헤더 검증
struct AuthMiddleware<S: Service> {
    inner: S,
    public_paths: Vec<String>,
}

impl<S: Service> AuthMiddleware<S> {
    // 공개 경로 리스트와 함께 생성
    fn new(inner: S, public_paths: Vec<&str>) -> Self {
        AuthMiddleware {
            inner,
            public_paths: public_paths.iter().map(|s| s.to_string()).collect(),
        }
    }
}

// 인증 로직
impl<S: Service> Service for AuthMiddleware<S> {
    fn call(&self, req: Request) -> Response {
        // 공개 경로는 인증 건너뛰기
        if self.public_paths.contains(&req.path) {
            return self.inner.call(req);
        }

        // Authorization 헤더 확인
        // Bearer 토큰만 허용
        match req.get_header("Authorization") {
            Some(auth) if auth.starts_with("Bearer ") => {
                println!("  [AUTH] 인증 성공: {}", &auth[7..17.min(auth.len())]);
                self.inner.call(req)
            }
            _ => {
                println!("  [AUTH] 인증 실패");
                Response::error(401, "Unauthorized")
            }
        }
    }
}

// === CORS 미들웨어 ===
// 허용된 Origin인지 확인
struct CorsMiddleware<S: Service> {
    inner: S,
    allowed_origins: Vec<String>,
}

impl<S: Service> CorsMiddleware<S> {
    fn new(inner: S, origins: Vec<&str>) -> Self {
        CorsMiddleware {
            inner,
            allowed_origins: origins.iter().map(|s| s.to_string()).collect(),
        }
    }
}

// CORS 검증 (단순 로깅; 실제로는 응답에 헤더 추가)
impl<S: Service> Service for CorsMiddleware<S> {
    fn call(&self, req: Request) -> Response {
        let origin = req.get_header("Origin").unwrap_or("unknown");
        // 와일드카드 또는 정확 매치 허용
        let allowed = self.allowed_origins.iter().any(|o| o == origin || o == "*");
        if !allowed {
            println!("  [CORS] 거부: {}", origin);
        }
        self.inner.call(req)
    }
}

// 진입점: 미들웨어 스택 조립 + 요청 시연
fn main() {
    println!("=== Tower 미들웨어 패턴 ===");
    println!("스택: CORS -> Auth -> Logging -> Handler\n");

    // 미들웨어 스택 조립 (안쪽에서 바깥으로)
    // 핸들러를 감싸고, 또 감싸는 구조 → 양파 패턴
    let handler = AppHandler;
    let logging = LoggingMiddleware::new(handler);
    let auth = AuthMiddleware::new(logging, vec!["/health"]);
    let app = CorsMiddleware::new(auth, vec!["*"]);

    // 요청 1: 공개 엔드포인트
    // /health는 공개 경로 → 인증 건너뜀
    println!("--- GET /health (공개) ---");
    let resp = app.call(Request::new("GET", "/health"));
    println!("  응답: {} {}\n", resp.status, resp.body);

    // 요청 2: 인증 성공
    println!("--- GET /users (인증 있음) ---");
    let resp = app.call(
        Request::new("GET", "/users")
            .with_header("Authorization", "Bearer valid-token-123")
            .with_header("Origin", "http://example.com")
    );
    println!("  응답: {} {}\n", resp.status, resp.body);

    // 요청 3: 인증 없음
    // Authorization 헤더 없음 → 401
    println!("--- POST /users (인증 없음) ---");
    let resp = app.call(Request::new("POST", "/users"));
    println!("  응답: {} {}\n", resp.status, resp.body);

    // 요청 4: 없는 경로
    // 인증은 통과하지만 핸들러에서 404
    println!("--- GET /unknown ---");
    let resp = app.call(
        Request::new("GET", "/unknown")
            .with_header("Authorization", "Bearer token")
    );
    println!("  응답: {} {}", resp.status, resp.body);

    println!("\n=== 실제 Tower 미들웨어 ===");
    println!(r#"use tower::ServiceBuilder;
let app = ServiceBuilder::new()
    .layer(TraceLayer::new_for_http())      // 로깅
    .layer(CorsLayer::permissive())          // CORS
    .layer(TimeoutLayer::new(Duration::from_secs(30))) // 타임아웃
    .service(router);"#);
}
```

**실행 결과** — 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다).

**풀이 요점**
- 핸들러와 미들웨어가 모두 `Service` 를 구현하기 때문에 `new(inner, ...)` 로 끝없이 감쌀 수 있다.
- 넘기기는 `self.inner.call(req)` 를 돌려주는 것이고, 막기는 그것을 부르지 않고 응답을 직접 만드는 것이다.
- 로깅은 인증 안쪽에 있으므로 401 이 난 요청 3 에는 `[LOG]` 줄이 없다.
- `req` 는 안쪽으로 옮겨 가므로 로그용 값은 그 전에 `clone()` 해야 한다.
- CORS 층은 거부를 찍기만 하고 요청은 늘 넘긴다 — 허용 목록이 `"*"` 라 이 시연에서는 아무것도 찍지 않는다.
- 손 조립은 안쪽부터 쓰고, 끝에 찍는 `ServiceBuilder` 예시는 바깥 층부터 쓴다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
