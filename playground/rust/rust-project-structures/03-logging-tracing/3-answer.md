# rust/rust-project-structures/03 — 로깅 & 트레이싱 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 「요청 수신」 → `db_query` SPAN → 「요청 처리 완료」 → `handle_request` SPAN, 바깥 Span 이 크거나 같다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
2026-04-04T12:00:00 [ INFO] http: 요청 수신 method=GET path=/users
  SPAN [db_query] table=users elapsed=<10ms 남짓 — 실행마다 다름>
2026-04-04T12:00:00 [ INFO] http: 요청 처리 완료 status=200
  SPAN [handle_request] method=GET path=/users elapsed=<db_query 이상 — 실행마다 다름>
```

**왜 그런가**
- 「요청 수신」 로그는 두 Span 이 끝나기 전에 바로 찍힌다.
- `drop(_db_span)` 이 sleep 바로 뒤에서 `Drop` 을 부르므로 `db_query` 줄이 결과 로그보다 앞선다.
- `_span` 은 함수 끝에서 버려지므로 `handle_request` 줄이 가장 마지막이다.
- `handle_request` Span 은 `db_query` 보다 먼저 시작해 나중에 끝나므로 걸린 시간이 크거나 같다.
- 근거: 2-summary 「동작 방식 (3)」 · 「동작 방식 (4)」.

### 2. `b`(Error) 하나만 찍힌다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`Info`(2) 와 `Debug`(1) 는 `Warn`(3) 보다 작아 걸러지고, `Error`(4) 만 `>= Warn` 을 통과한다.

**왜 그런가**
- derive 한 비교에서 `Trace < Debug < Info < Warn < Error` 이고, `log` 는 `event.level >= self.min_level` 일 때만 찍는다.
- 근거: 2-summary 「동작 방식 (1)」.

### 3. `let _` 이면 SPAN 줄이 먼저, `let _guard` 면 `작업 중` 이 먼저다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
- `let _ = …` 는 값을 묶지 않으므로 그 문장 끝에서 Span 이 버려진다 → `  SPAN [work] step=1 elapsed=…`(거의 0) 이 먼저, 그다음 `작업 중`.
- `let _guard = …` 는 이름 있는 바인딩이라 함수 끝까지 산다 → `작업 중` 이 먼저, 그다음 `SPAN [work]` 줄.

**왜 그런가**
- 밑줄로 시작하는 이름은 「안 써도 경고하지 마라」는 뜻일 뿐 수명은 보통 변수와 같고, `_` 하나만은 바인딩이 아니다.
- 근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 1」.

### 4. DB 조회 구간만 재려고

Span 은 버려지는 순간에 걸린 시간을 찍는다.
`_db_span` 을 함수 끝까지 두면 DB 조회 뒤의 결과 로그 작업까지 「DB 시간」에 들어간다.
또 나중에 만든 것부터 버려지므로 `db_query` 줄이 결과 로그 뒤, `handle_request` 줄 바로 앞으로 밀린다.
`drop(_db_span)` 으로 재고 싶은 구간이 끝나는 자리에서 직접 버려야 그 구간만 잰다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 2」.

### 5. 도구가 항목으로 검색 · 필터링할 수 있어서

값을 문장에 섞으면 사람은 읽을 수 있어도 도구는 `500` 이 무엇의 값인지 모른다.
`status=500` 처럼 이름을 붙여 따로 두면 「`status=500` 인 줄만」 같은 검색과 거르기가 된다.
원본 팁도 구조화된 로깅이 로그 분석 도구에서 검색과 필터링에 유리하다고 적는다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 4」.

### 6. `Debug` 와 `Trace` 만 찍고, `Info` · `Warn` · `Error` 를 버린다

뒤집으면 차례가 `Error < Warn < Info < Debug < Trace` 가 된다.
`>= Debug` 를 통과하는 것은 `Debug` 와 `Trace` 뿐이라, 정작 중요한 `Error` 가 걸러진다.
컴파일러는 이것을 오류로 잡지 않는다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 3」.

### 7. 「대략 10ms 이상」과 「바깥 Span 이상」까지

`sleep(10ms)` 가 들어 있으므로 10ms 남짓이라는 것, 그리고 `handle_request` 의 값이 `db_query` 의 값보다 크거나 같다는 것까지는 말할 수 있다.
정확한 값은 운영체제 스케줄링과 부하에 따라 실행마다 달라 코드만으로는 맞힐 수 없다.
근거: 2-summary 「어디서 틀리나 5」 · 「구현 세부사항 대 언어 보장」.

### 8. `#[instrument]` 속성

`#[instrument]` 를 함수에 붙이면 그 함수에 Span 이 자동으로 붙는다.
손으로 `Span::new` 를 부르고 `Drop` 으로 끝을 찍던 일을 속성 하나가 대신한다.
이벤트 쪽은 `LogEvent` 를 손으로 채우는 대신 `info!(user_id = id, "…")` 같은 매크로가 맡고, 필터와 형식은 `tracing-subscriber` 가 맡는다.
근거: 2-summary 「동작 방식 (5)」.

### 9. `target` 기본값이 `module_path!()` 라서

`tracing` 의 이벤트는 `target` 을 따로 적지 않으면 그 코드의 모듈 경로를 쓴다.
`RUST_LOG` 의 `myapp=debug` · `myapp::handlers=debug` 같은 경로는 이 `target` 과 견주므로, `mod` 구조가 그대로 필터 경로가 된다.
그래서 모듈을 옮기거나 이름을 바꾸면 필터 설정도 함께 바꿔야 할 수 있다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 8」.

### 10. 중괄호 하나씩 — `{ version = "0.3", features = ["env-filter"] }`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`r#"…"#` 은 이스케이프를 해석하지 않는 raw 문자열이지만, `println!` 에 넘겼으므로 형식 문자열 규칙은 그대로 적용된다.
그래서 `{{` 는 `{`, `}}` 는 `}` 로 찍히고, `use tracing::{{info, …}};` 도 `use tracing::{info, …};` 로 찍힌다.

**왜 그런가**
- 형식 문자열 안의 맨 `{` 는 자리표시자로 읽히므로, 글자 중괄호는 두 번 써서 나타낸다.
- 근거: 2-summary 「문법 — 형태와 규칙」 · 「어디서 틀리나 9」.

## 실습 정답

### 실습 1. 구조화된 로거와 RAII Span 으로 요청 처리 흐름 기록하기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 다섯 변형 · 판별값 0~4 · 비교 가능 | `#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)] enum Level` |
| 2. 다섯 칸 이름 | `impl fmt::Display for Level` 의 `match` (`" INFO"` · `" WARN"`) |
| 3. 이벤트 구조와 한 줄 형식 | `struct LogEvent` · `impl fmt::Display for LogEvent` (`write!` + `for (k, v)` 반복) |
| 4. 레벨 필터와 시각 | `SimpleLogger::new` · `SimpleLogger::log` 의 `event.level >= self.min_level` · `chrono_like_now` |
| 5. Span 시작과 체이닝 | `Span::new` (`Instant::now()`) · `with_field(mut self, ..) -> Self` |
| 6. 지난 시간 | `Span::elapsed` (`self.start.elapsed()`) |
| 7. 버려질 때 SPAN 줄 | `impl Drop for Span` 의 `map` · `join(" ")` · `"{:.3?}"` |
| 8. 함수 전체 Span | `handle_request` 의 `let _span = Span::new("handle_request")…` |
| 9. 「요청 수신」 로그 | 첫 `logger.log(&LogEvent { level: Level::Info, target: "http" … })` |
| 10. DB 구간 Span | `let _db_span = Span::new("db_query")…` · `thread::sleep(from_millis(10))` · `drop(_db_span)` |
| 11. 경로별 결과 로그 | `if path == "/error"` 의 `Level::Error` 500 / `else` 의 `Level::Info` 200 |
| 12. 서버 시작 로그 | `main` 의 `SimpleLogger::new(Level::Debug)` · `"서버 시작"` 이벤트 |
| 13. 세 요청 | `main` 의 `"\n--- GET /users ---"` 등 세 제목과 `handle_request` 호출 |
| 14. tracing 안내 | `main` 끝의 `println!(r#"…"#)` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`rust/rust-project-structures/reference/logging-tracing.rs`

```rust
// [실무 프로젝트 구조] 로깅 & 트레이싱
// 설명: tracing 크레이트 패턴으로 구조화된 로깅과 성능 추적
// 팁: tracing은 log 크레이트의 상위 호환이며 Span(작업 범위)을 지원한다. #[instrument]로 함수에 자동 Span을 붙인다. tracing-subscriber로 출력 형식(JSON, pretty 등)을 설정한다. RUST_LOG=info,myapp=debug 로 모듈별 레벨을 설정한다. 구조화된 로깅(key=value)은 로그 분석 도구에서 검색과 필터링에 유리하다.
// Rust 모듈 시스템 특징: 로깅 초기화는 main.rs 또는 lib.rs의 init_tracing() 헬퍼에서 한 번만 수행한다. RUST_LOG 환경변수의 모듈 경로(예: myapp::handlers=debug)는 Rust 모듈 시스템과 일치한다. tracing의 target 필드 기본값이 module_path!()이므로 mod 구조가 그대로 로그 필터에 반영된다. feature flag로 dev/prod 출력 포맷을 분기.

// 시간 측정과 fmt 트레이트
use std::time::Instant;
use std::fmt;

// === 로그 레벨 ===
// 비교 가능한 enum (PartialOrd로 >= 비교 지원)
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
enum Level {
    Trace = 0,
    Debug = 1,
    Info = 2,
    Warn = 3,
    Error = 4,
}

// 로그 레벨 출력 포맷 (5자리 정렬)
impl fmt::Display for Level {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Level::Trace => write!(f, "TRACE"),
            Level::Debug => write!(f, "DEBUG"),
            Level::Info => write!(f, " INFO"),
            Level::Warn => write!(f, " WARN"),
            Level::Error => write!(f, "ERROR"),
        }
    }
}

// === 구조화된 로그 이벤트 ===
// 단일 로그 항목 - 메시지 + 키/값 필드들
struct LogEvent {
    level: Level,
    target: String,
    message: String,
    fields: Vec<(String, String)>,
}

// 이벤트 출력 포맷: [LEVEL] target: message k1=v1 k2=v2
impl fmt::Display for LogEvent {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "[{}] {}: {}", self.level, self.target, self.message)?;
        for (k, v) in &self.fields {
            write!(f, " {}={}", k, v)?;
        }
        Ok(())
    }
}

// === 간단한 로거 ===
// 최소 레벨 이상만 출력하는 로거
struct SimpleLogger {
    min_level: Level,
}

impl SimpleLogger {
    fn new(min_level: Level) -> Self {
        SimpleLogger { min_level }
    }

    // 이벤트 출력 (필터 통과 시)
    fn log(&self, event: &LogEvent) {
        if event.level >= self.min_level {
            let now = chrono_like_now(); // 시간 시뮬레이션
            println!("{} {}", now, event);
        }
    }
}

// 시간 시뮬레이션 (실제로는 chrono::Utc::now())
fn chrono_like_now() -> String {
    "2026-04-04T12:00:00".to_string()
}

// === Span (작업 범위 추적) ===
// 시작/종료 시간을 자동 기록하는 RAII 구조체
struct Span {
    name: String,
    start: Instant,
    fields: Vec<(String, String)>,
}

impl Span {
    // span 시작
    fn new(name: &str) -> Self {
        Span {
            name: name.to_string(),
            start: Instant::now(),
            fields: Vec::new(),
        }
    }

    // 필드 추가 (체이닝)
    fn with_field(mut self, key: &str, value: &str) -> Self {
        self.fields.push((key.to_string(), value.to_string()));
        self
    }

    // 시작부터 경과 시간
    fn elapsed(&self) -> std::time::Duration {
        self.start.elapsed()
    }
}

// Drop 트레이트로 RAII 구현 - span이 스코프 벗어나면 자동 출력
// tracing 크레이트의 Span도 동일한 패턴
impl Drop for Span {
    fn drop(&mut self) {
        // 필드를 key=value 형태로 직렬화
        let fields: String = self.fields.iter()
            .map(|(k, v)| format!("{}={}", k, v))
            .collect::<Vec<_>>()
            .join(" ");
        println!("  SPAN [{}] {} elapsed={:.3?}",
                 self.name, fields, self.elapsed());
    }
}

// === 서비스 시뮬레이션 ===
// HTTP 요청 처리 흐름에 로깅과 span을 적용한 예
fn handle_request(logger: &SimpleLogger, method: &str, path: &str) {
    // 함수 전체 범위 span (drop 시점에 elapsed 자동 출력)
    let _span = Span::new("handle_request")
        .with_field("method", method)
        .with_field("path", path);

    // 요청 수신 로그
    logger.log(&LogEvent {
        level: Level::Info,
        target: "http".into(),
        message: "요청 수신".into(),
        fields: vec![
            ("method".into(), method.into()),
            ("path".into(), path.into()),
        ],
    });

    // 비즈니스 로직
    // DB 쿼리 부분만 별도 span으로 측정
    let _db_span = Span::new("db_query")
        .with_field("table", "users");
    std::thread::sleep(std::time::Duration::from_millis(10));
    drop(_db_span);

    // 경로별로 다른 결과 로그
    if path == "/error" {
        logger.log(&LogEvent {
            level: Level::Error,
            target: "http".into(),
            message: "요청 처리 실패".into(),
            fields: vec![("status".into(), "500".into())],
        });
    } else {
        logger.log(&LogEvent {
            level: Level::Info,
            target: "http".into(),
            message: "요청 처리 완료".into(),
            fields: vec![("status".into(), "200".into())],
        });
    }
}

// 진입점: 다양한 레벨/span 시연
fn main() {
    let logger = SimpleLogger::new(Level::Debug);

    println!("=== 구조화된 로깅 ===");
    // 서버 시작 로그 (구조화 필드 포함)
    logger.log(&LogEvent {
        level: Level::Info,
        target: "app".into(),
        message: "서버 시작".into(),
        fields: vec![
            ("port".into(), "8080".into()),
            ("env".into(), "development".into()),
        ],
    });

    // 요청 처리
    println!("\n--- GET /users ---");
    handle_request(&logger, "GET", "/users");

    println!("\n--- POST /users ---");
    handle_request(&logger, "POST", "/users");

    println!("\n--- GET /error ---");
    handle_request(&logger, "GET", "/error");

    // tracing 크레이트 사용법
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

**실행 결과** — 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다).

**풀이 요점**
- `>=` 필터는 derive 한 `Ord` 에 기대므로, 변형을 낮은 등급부터 선언하는 것이 곧 필터의 정의다.
- `LogEvent` 의 `Display` 는 `write!(..)?` 를 여러 번 이어 쓰고 마지막에 `Ok(())` 를 돌려준다.
- `with_field` 가 `mut self` 를 받고 `Self` 를 돌려주므로 `Span::new(..).with_field(..).with_field(..)` 가 한 식으로 이어진다.
- 함수 전체 Span 은 `_span` 처럼 이름을 붙여 끝까지 살리고, DB 구간 Span 은 `drop` 으로 그 자리에서 닫는다.
- `handle_request` Span 의 줄은 결과 로그 뒤, 함수가 끝날 때 찍힌다.
- 마지막 안내 문자열 속 `{{` · `}}` 는 화면에 중괄호 하나씩으로 찍힌다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
