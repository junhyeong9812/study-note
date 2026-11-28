# rust/rust-practical/10 — 로깅 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 모듈 필터가 걸린 로거로 요청 하나를 처리하면 (예측)

```rust
// 질문용 발췌
let filtered_logger = Logger::new(Level::Info)
    .with_module_level("db", Level::Debug)
    .with_module_level("http::auth", Level::Trace);

log_msg!(logger, Level::Info,  "http::server", "요청 수신: {} {}", request_id, path);
log_msg!(logger, Level::Debug, "http::auth",   "토큰 검증 중...");
log_msg!(logger, Level::Trace, "http::auth",   "토큰 디코딩 세부 정보...");
log_msg!(logger, Level::Info,  "http::auth",   "인증 성공: user_42");
log_msg!(logger, Level::Debug, "db::query",    "SELECT * FROM users WHERE id = 42");
log_msg!(logger, Level::Trace, "db::pool",     "커넥션 풀에서 연결 획득");
log_msg!(logger, Level::Info,  "http::server", "응답 전송: 200 OK");
```

- 아래 일곱 줄(`logger` 자리에 `filtered_logger` 가 들어간다) 가운데 찍히는 것은 몇 줄인가?
- 찍히지 않는 줄이 있다면 어느 줄이고, 어느 필터 때문인가?

### 2. 스팬을 두 겹으로 감싸면 (예측)

```rust
// 질문용 발췌
{
    let _outer = Span::new("http_request")
        .field("method", "GET")
        .field("path", "/api/users");
    {
        let _inner = Span::new("db_query")
            .field("sql", "SELECT * FROM users");
        let sum: u64 = (0..100_000).sum();
        let _ = sum;
    }
}
```

- 스팬 줄 네 개는 어떤 차례로 찍히나?
- 「시작」 줄에 필드가 보이나, 그리고 괄호 안 걸린 시간은 미리 알 수 있나?

### 3. 필터를 넣는 차례를 바꾸면 (예측)

```rust
// 질문용 발췌
let logger = Logger::new(Level::Info)
    .with_module_level("http", Level::Warn)
    .with_module_level("http::auth", Level::Trace);

log_msg!(logger, Level::Debug, "http::auth", "토큰 검증 중...");
```

- 마지막 줄의 메시지는 찍히나?

### 4. `enum` 끼리 `>=` 로 비교되는 까닭 (왜)

- `level >= self.min_level` 이 `Level` 에서 컴파일되고 「덜 중요한 것 < 더 중요한 것」으로 맞게 동작하는 까닭은 무엇인가?

### 5. 「완료」 줄을 아무도 부르지 않는데 찍히는 까닭 (왜)

- `process_request` 안에 「끝」을 알리는 호출이 없는데도 스팬의 「완료」 줄과 걸린 시간이 남는 까닭은 무엇인가?

### 6. `db` 필터가 미치는 범위 (경계)

- `"db"` 필터는 `dbx::cache` 라는 모듈에도 걸리나?

### 7. 버려지는 메시지의 비용 (경계)

- 문턱에서 떨어져 찍히지 않는 `log_msg!` 호출이 이미 치르고 만 비용과 아낀 비용은 각각 무엇인가?

### 8. 팁의 `RUST_LOG` 를 이 로거로 옮기기 (연결)

- 팁의 `RUST_LOG=debug,hyper=warn` 을 이 문서의 `Logger` 로 옮기면 어떤 호출이 되나?

### 9. 스팬 필드와 프로덕션 수집 (연결)

- `request_id=req-001` 같은 구조화된 필드가 JSON 출력 · ELK · Datadog 수집과 만나면 사람이 읽는 한 줄 로그보다 무엇이 나아지나?

## 실습

### 실습 1. 레벨 필터 로거와 RAII 스팬 만들기

**만들 것** — 표준 라이브러리만으로 레벨 · 모듈 필터를 가진 로거와, 범위를 벗어날 때 걸린 시간을 남기는 스팬을 만들어 HTTP 요청 처리를 흉내 낸다.

**준비물** — 표준 라이브러리만 쓴다. `log` · `env_logger` · `tracing` 은 흉내 낸 것이라 크레이트를 받지 않아도 되고, 실제 사용 예는 글자로만 찍는다.

**요구 조건**

1단계 — 레벨
1. `Level` 은 `Trace` · `Debug` · `Info` · `Warn` · `Error` 다섯 변형이고, 이 차례대로 작은 것부터 큰 것으로 비교된다.
2. `Level` 을 `Display` 로 찍으면 `TRACE` · `DEBUG` · `INFO ` · `WARN ` · `ERROR` 처럼 다섯 글자로 맞춘다.

2단계 — 로거
3. `Logger` 는 전역 최소 레벨과 (모듈 이름 접두사, 레벨) 목록을 가진다.
4. `Logger::new(level)` 은 필터 없이 만들고, `with_module_level(module, level)` 은 필터를 하나 더한 로거를 돌려줘 호출을 이을 수 있다.
5. `enabled(level, module)` 은 필터를 넣은 차례로 보고 모듈 이름이 그 접두사로 시작하면 그 필터 레벨로만 판정하며, 일치하는 필터가 없으면 전역 레벨로 판정한다.
6. `log(level, module, message)` 은 판정에서 떨어지면 바로 돌아가고, 통과하면 UNIX epoch 초로 하루 안의 시각을 구해 `HH:MM:SS [LEVEL] 모듈 - 메시지` 꼴로 한 줄 찍는다.

3단계 — 스팬
7. `Span::new(name)` 은 `  -> 이름 시작` 을 찍고 시작 시각을 적어 둔다.
8. `field(key, value)` 는 필드를 더한 스팬을 돌려줘 호출을 이을 수 있다.
9. 스팬이 drop 되면 `  <- 이름 완료 {k=v, k=v} (걸린 시간)` 을 찍는다 — 필드가 없으면 중괄호 부분을 뺀다.

4단계 — 매크로와 사용
10. `log_msg!(로거, 레벨, 모듈, 형식 문자열, 인자…)` 는 뒤쪽 인자를 `format!` 으로 묶어 `log` 를 부른다.
11. `process_request` 는 스팬으로 감싼 채 여러 모듈 · 레벨의 로그를 남기고, `simulate_error` 는 `Warn` · `Error` 로그를 남긴다.
12. `main` 은 차례로 ① 모든 레벨을 `Trace` 로거로 찍고 ② 기본 `Info` · `db`=`Debug` · `http::auth`=`Trace` 로거로 요청을 처리하고 ③ 같은 로거로 에러를 흉내 내고 ④ 두 겹 스팬을 만들고 ⑤ 실제 `env_logger` · `tracing` 사용 예를 글자로 찍는다.

**시작 코드**

```rust
use std::fmt;
use std::time::SystemTime;

// TODO: 비교가 되도록 derive 를 단다
enum Level {
    Trace,
    Debug,
    Info,
    Warn,
    Error,
}

impl fmt::Display for Level {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        // TODO: 다섯 글자로 맞춘 이름을 쓴다
        todo!()
    }
}

struct Logger {
    min_level: Level,
    module_filters: Vec<(String, Level)>,
}

impl Logger {
    fn new(min_level: Level) -> Self {
        // TODO
        todo!()
    }

    fn with_module_level(mut self, module: &str, level: Level) -> Self {
        // TODO: 필터를 더하고 self 를 돌려준다
        todo!()
    }

    fn enabled(&self, level: Level, module: &str) -> bool {
        // TODO: 접두사 첫 일치 → 필터 레벨, 없으면 전역 레벨
        todo!()
    }

    fn log(&self, level: Level, module: &str, message: &str) {
        // TODO: 판정 → 하루 안의 시·분·초 → 한 줄 찍기
    }
}

#[derive(Debug)]
struct Span {
    name: String,
    fields: Vec<(String, String)>,
    start: std::time::Instant,
}

impl Span {
    fn new(name: &str) -> Self {
        // TODO: 시작 줄을 찍고 시작 시각을 적는다
        todo!()
    }

    fn field(mut self, key: &str, value: &str) -> Self {
        // TODO
        todo!()
    }
}

// TODO: impl Drop for Span — 완료 줄 + 필드 + 걸린 시간

// TODO: macro_rules! log_msg { ... }

fn process_request(logger: &Logger, request_id: &str, path: &str) {
    let _span = Span::new("process_request")
        .field("request_id", request_id)
        .field("path", path);

    log_msg!(logger, Level::Info, "http::server", "요청 수신: {} {}", request_id, path);
    log_msg!(logger, Level::Debug, "http::auth", "토큰 검증 중...");
    log_msg!(logger, Level::Trace, "http::auth", "토큰 디코딩 세부 정보...");
    log_msg!(logger, Level::Info, "http::auth", "인증 성공: user_42");
    log_msg!(logger, Level::Debug, "db::query", "SELECT * FROM users WHERE id = 42");
    log_msg!(logger, Level::Trace, "db::pool", "커넥션 풀에서 연결 획득");
    log_msg!(logger, Level::Info, "http::server", "응답 전송: 200 OK");
}

fn simulate_error(logger: &Logger) {
    log_msg!(logger, Level::Warn, "db::pool", "커넥션 풀 80% 사용 중");
    log_msg!(logger, Level::Error, "db::query", "쿼리 실패: connection refused");
    log_msg!(logger, Level::Error, "http::server", "내부 서버 에러: 500");
}

fn main() {
    println!("=== 1. 기본 로깅 (모든 레벨) ===");
    // TODO: Trace 로거로 다섯 레벨을 "app" 모듈에서 찍는다

    println!("\n=== 2. 모듈별 필터링 ===");
    // TODO: 기본 Info + db=Debug + http::auth=Trace 로거를 만든다
    println!("필터: 기본=INFO, db=DEBUG, http::auth=TRACE");
    // TODO: process_request(&로거, "req-001", "/api/users");

    println!("\n=== 3. 에러 로깅 ===");
    // TODO: simulate_error

    println!("\n=== 4. 구조화된 로깅 (Span) ===");
    // TODO: http_request 스팬 안에 db_query 스팬을 두 겹으로

    println!("\n=== 실제 사용 코드 ===");
    // TODO: env_logger · tracing 사용 예를 원시 문자열 r#"..."# 로 찍는다
}
```

**확인 방법** — `rustc logging.rs && ./logging` 으로 돌려, 2절에서 `db::pool` 의 `TRACE` 줄만 빠지는지, 4절에서 `db_query 완료` 가 `http_request 완료` 보다 먼저 찍히는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
