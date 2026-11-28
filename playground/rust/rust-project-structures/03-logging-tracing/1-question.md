# rust/rust-project-structures/03 — 로깅 & 트레이싱 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 요청 하나를 처리하는 동안 찍히는 줄의 차례 (예측)

```rust
// 질문용 발췌 — logger 의 min_level 은 Debug
fn handle_request(logger: &SimpleLogger, method: &str, path: &str) {
    let _span = Span::new("handle_request")
        .with_field("method", method)
        .with_field("path", path);
    logger.log(/* Info, http, "요청 수신", method, path */);
    let _db_span = Span::new("db_query").with_field("table", "users");
    std::thread::sleep(std::time::Duration::from_millis(10));
    drop(_db_span);
    logger.log(/* Info, http, "요청 처리 완료", status=200 */);
}
```

- `handle_request(&logger, "GET", "/users")` 한 번이 찍는 네 줄은 어떤 차례인가?
- 두 `SPAN` 줄의 `elapsed` 가운데 어느 쪽이 크거나 같은가?

### 2. `min_level` 을 `Warn` 으로 둔 로거 (예측)

```rust
// 질문용 발췌 — ev(레벨, 메시지) 는 target 과 fields 를 아무렇게나 채운 LogEvent 를 만든다
let logger = SimpleLogger::new(Level::Warn);
logger.log(&ev(Level::Info, "a"));
logger.log(&ev(Level::Error, "b"));
logger.log(&ev(Level::Debug, "c"));
```

- 세 이벤트 가운데 화면에 찍히는 것은 어느 것인가?

### 3. `let _` 로 받은 Span (예측)

```rust
// 질문용 발췌
fn work() {
    let _ = Span::new("work").with_field("step", "1");
    println!("작업 중");
}
```

- `work()` 를 부르면 `SPAN [work]` 줄과 `작업 중` 줄 가운데 무엇이 먼저 찍히나?
- `let _` 를 `let _guard` 로 바꾸면 차례는 어떻게 되나?

### 4. DB 조회 Span 을 `drop` 으로 직접 닫는 까닭 (왜)

- `handle_request` 는 왜 `_db_span` 을 함수 끝까지 두지 않고 `drop(_db_span)` 으로 그 자리에서 버리나?

### 5. 값을 메시지가 아니라 필드에 두는 까닭 (왜)

- `"요청 처리 완료 500"` 처럼 한 문장으로 쓰지 않고 `status=500` 을 필드로 따로 두는 것이 왜 좋은가?

### 6. `Level` 의 변형 차례를 뒤집으면 (경계)

- `Level` 을 `Error, Warn, Info, Debug, Trace` 차례로 다시 선언하고 판별값도 0 부터 매기면, `min_level` 이 `Debug` 인 로거는 무엇을 찍고 무엇을 버리게 되나?

### 7. 걸린 시간을 어디까지 맞힐 수 있나 (경계)

- `db_query` 의 `elapsed` 값에 대해 코드만 읽고 말할 수 있는 것은 어디까지인가?

### 8. 손으로 만든 `Span` 과 `#[instrument]` (연결)

- 이 예제의 `Span` 구조체와 `Drop` 구현이 하는 일을 `tracing` 크레이트에서는 무엇이 대신하나?

### 9. `RUST_LOG` 경로와 모듈 구조 (연결)

- `RUST_LOG=info,myapp=debug` 같은 설정이 Rust 의 `mod` 구조와 맞물리는 까닭은 무엇인가?

### 10. raw 문자열 속 `{{` (예측)

- `main` 마지막 `println!(r#"…"#)` 안의 `{{ version = "0.3", features = ["env-filter"] }}` 는 화면에 어떤 괄호로 찍히나?

## 실습

### 실습 1. 구조화된 로거와 RAII Span 으로 요청 처리 흐름 기록하기

**만들 것** — 레벨 필터가 있는 구조화된 로거와, 스코프를 벗어나면 걸린 시간을 찍는 `Span` 을 만든다.
그것으로 HTTP 요청 세 개의 처리 흐름을 기록하고, 마지막에 `tracing` 크레이트 사용법 안내를 찍는다.

**요구 조건**

1단계 — 레벨

1. `Level` enum 은 `Trace` · `Debug` · `Info` · `Warn` · `Error` 다섯 변형을 낮은 것부터 판별값 0~4 로 두고, 변형끼리 `>=` 비교가 되도록 derive 한다.
2. `Level` 의 `Display` 는 다섯 칸 이름을 쓴다 — `INFO` · `WARN` 은 앞에 공백 하나를 붙인다.

2단계 — 이벤트와 로거

3. `LogEvent` 는 레벨 · `target` · `message` · `(String, String)` 필드 목록을 가진다.
   `Display` 는 `[레벨] target: message` 를 쓰고, 필드마다 앞에 공백을 두고 `k=v` 를 덧붙인다.
4. `SimpleLogger::new(min_level)` 로 만들고, `log` 는 이벤트 레벨이 `min_level` 이상일 때만 `시각 이벤트` 꼴로 한 줄을 찍는다.
   시각은 `chrono_like_now()` 가 돌려주는 고정 문자열이다.

3단계 — Span

5. `Span::new(이름)` 은 이름 · 지금 시각 · 빈 필드 목록으로 시작한다.
   `with_field` 는 Span 값을 받아 필드를 하나 넣고 돌려주어 줄줄이 이어 쓸 수 있게 한다.
6. `elapsed()` 는 시작부터 지난 시간을 돌려준다.
7. `Span` 이 버려질 때 `  SPAN [이름] k=v k=v elapsed=…` 꼴로 한 줄을 찍는다 — 필드는 공백으로 잇고, 시간은 `Duration` 디버그 형식에 소수 셋째 자리까지.

4단계 — 요청 흐름 `handle_request(logger, method, path)`

8. 함수 전체를 덮는 `handle_request` Span 을 `method` · `path` 필드와 함께 만들고, 함수 끝까지 살아 있게 한다.
9. `Info` 레벨, `http` 타깃으로 「요청 수신」을 `method` · `path` 필드와 함께 남긴다.
10. `table=users` 필드를 가진 `db_query` Span 을 만들고, 10ms 를 잔 뒤 그 자리에서 직접 버린다.
11. 경로가 `"/error"` 면 `Error` 레벨로 「요청 처리 실패」 `status=500`, 아니면 `Info` 레벨로 「요청 처리 완료」 `status=200` 을 남긴다.

5단계 — `main`

12. `min_level` 이 `Debug` 인 로거를 만들고, `=== 구조화된 로깅 ===` 제목 뒤에 `app` 타깃의 `Info` 「서버 시작」을 `port=8080` · `env=development` 필드로 남긴다.
13. `--- GET /users ---` · `--- POST /users ---` · `--- GET /error ---` 제목 줄(앞에 빈 줄)을 찍고 각 요청을 처리한다.
14. 마지막으로 `=== tracing 크레이트 ===` 제목과, 시작 코드에 채워 둔 `tracing` 사용법 안내 문자열을 찍는다.

**시작 코드**

```rust
use std::time::Instant;
use std::fmt;

// === 로그 레벨 ===
// TODO: 크기 비교가 되도록 derive 를 단다
enum Level {
    // TODO: 다섯 변형을 낮은 등급부터, 판별값 0~4
}

impl fmt::Display for Level {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        // TODO: 다섯 칸 이름을 쓴다 (INFO · WARN 은 앞에 공백 하나)
        todo!()
    }
}

// === 구조화된 로그 이벤트 ===
struct LogEvent {
    level: Level,
    target: String,
    message: String,
    fields: Vec<(String, String)>,
}

impl fmt::Display for LogEvent {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        // TODO: [레벨] target: message 를 쓰고, 필드마다 " k=v" 를 덧붙인다
        todo!()
    }
}

// === 간단한 로거 ===
struct SimpleLogger {
    min_level: Level,
}

impl SimpleLogger {
    fn new(min_level: Level) -> Self {
        SimpleLogger { min_level }
    }

    fn log(&self, event: &LogEvent) {
        // TODO: min_level 이상일 때만 "시각 이벤트" 한 줄을 찍는다
    }
}

fn chrono_like_now() -> String {
    "2026-04-04T12:00:00".to_string()
}

// === Span (작업 범위 추적) ===
struct Span {
    name: String,
    start: Instant,
    fields: Vec<(String, String)>,
}

impl Span {
    fn new(name: &str) -> Self {
        // TODO: 이름 · 지금 시각 · 빈 필드
        todo!()
    }

    fn with_field(mut self, key: &str, value: &str) -> Self {
        // TODO: 필드를 넣고 자신을 돌려준다
        todo!()
    }

    fn elapsed(&self) -> std::time::Duration {
        // TODO: 시작부터 지난 시간
        todo!()
    }
}

// TODO: Span 이 버려질 때 "  SPAN [이름] k=v ... elapsed=..." 를 찍는 Drop 구현

// === 서비스 시뮬레이션 ===
fn handle_request(logger: &SimpleLogger, method: &str, path: &str) {
    // TODO: 함수 전체를 덮는 span (method, path)
    // TODO: Info "요청 수신" 로그 (method, path)
    // TODO: db_query span (table=users) → 10ms sleep → 그 자리에서 닫기
    // TODO: path 에 따라 Error "요청 처리 실패" 500 / Info "요청 처리 완료" 200
}

fn main() {
    let logger = SimpleLogger::new(Level::Debug);

    println!("=== 구조화된 로깅 ===");
    // TODO: app 타깃 Info "서버 시작" (port=8080, env=development)

    // TODO: 세 요청 — 제목 줄을 찍고 handle_request 를 부른다
    // "\n--- GET /users ---" · "\n--- POST /users ---" · "\n--- GET /error ---"

    println!("\n=== tracing 크레이트 ===");
    println!(r#"// Cargo.toml:
// tracing = "0.1"
// tracing-subscriber = {{ version = "0.3", features = ["env-filter"] }}

use tracing::{{info, warn, error, instrument}};
use tracing_subscriber::EnvFilter;

#[instrument(skip(db))]  // 자동으로 Span 생성
async fn get_user(db: &Db, id: u64) -> Result<User> {{
    info!(user_id = id, "유저 조회");
    let user = db.find(id).await?;
    info!(name = %user.name, "유저 발견");
    Ok(user)
}}

// 초기화
tracing_subscriber::fmt()
    .with_env_filter(EnvFilter::from_default_env()) // RUST_LOG=info
    .json()  // JSON 포맷
    .init();"#);
}
```

**확인 방법** — 다 채운 뒤 아래처럼 컴파일해 돌린다.
요청마다 「요청 수신」 → `db_query` SPAN → 결과 로그 → `handle_request` SPAN 차례로 찍히고, `/error` 요청에서만 `[ERROR]` 줄이 나오는지 본다.

```bash
rustc logging-tracing.rs -o logging-tracing && ./logging-tracing
```

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
