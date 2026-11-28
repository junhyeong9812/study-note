# rust/rust-practical/10 — 로깅 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 일곱 줄 가운데 여섯 줄 — `db::pool` 의 `Trace` 만 빠진다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

시각 자리는 실행할 때마다 다르므로 `HH:MM:SS` 로 적는다.

```text
HH:MM:SS [INFO ] http::server - 요청 수신: req-001 /api/users
HH:MM:SS [DEBUG] http::auth - 토큰 검증 중...
HH:MM:SS [TRACE] http::auth - 토큰 디코딩 세부 정보...
HH:MM:SS [INFO ] http::auth - 인증 성공: user_42
HH:MM:SS [DEBUG] db::query - SELECT * FROM users WHERE id = 42
HH:MM:SS [INFO ] http::server - 응답 전송: 200 OK
```

실제 `process_request` 에서는 이 앞뒤에 `  -> process_request 시작` 과 `  <- process_request 완료 {request_id=req-001, path=/api/users} (걸린 시간)` 이 붙는다.

**왜 그런가**
- `http::server` 는 어느 필터에도 걸리지 않아 전역 `Info` 로 판정한다 — `Info` 두 줄은 통과한다.
- `http::auth` 는 `"http::auth"` 필터(`Trace`)에 걸린다 — `Debug` · `Trace` · `Info` 모두 `Trace` 이상이라 통과한다.
- `db::query` 는 `"db"` 필터(`Debug`)에 걸리고 `Debug >= Debug` 라 통과한다.
- `db::pool` 도 `"db"` 필터에 걸리지만 `Trace >= Debug` 가 거짓이라 버려진다.
- 근거: 2-summary 「동작 방식 (2)」.

### 2. 안쪽이 먼저 시작 뒤 먼저 끝난다 — 필드는 완료 줄에만, 시간은 그때그때 다르다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
  -> http_request 시작
  -> db_query 시작
  <- db_query 완료 {sql=SELECT * FROM users} (걸린 시간)
  <- http_request 완료 {method=GET, path=/api/users} (걸린 시간)
```

**왜 그런가**
- `Span::new` 가 불리는 순간 「시작」을 찍으므로 바깥 → 안쪽 차례로 시작한다.
- 안쪽 블록이 먼저 닫혀 `_inner` 가 먼저 drop 되고, 그다음 바깥 블록이 닫혀 `_outer` 가 drop 된다.
- `.field` 는 「시작」을 찍은 뒤에 붙으므로 필드는 「완료」 줄에만 나온다.
- 걸린 시간은 `Instant` 로 잰 `Duration` 을 `{:?}` 로 찍은 것이라 실행마다 달라 미리 알 수 없다.
- 근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 6」.

### 3. 찍히지 않는다 — 먼저 넣은 `"http"` 필터에 걸린다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

아무 줄도 찍히지 않는다.

**왜 그런가**
- `enabled` 는 필터를 넣은 차례로 보고, `"http::auth".starts_with("http")` 가 참이라 첫 필터 `Warn` 으로 판정하고 바로 돌아간다.
- `Debug >= Warn` 은 거짓이므로 버려진다.
- 뒤의 `"http::auth"` 필터(`Trace`)는 보지도 않는다.
- 근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 2」.

### 4. `derive(PartialOrd, Ord)` 가 선언 차례로 순서를 매기기 때문이다

`Level` 에 `PartialOrd` · `Ord` 를 derive 하면 변형을 선언한 차례대로 작은 것부터 큰 것이 된다.
`Trace` 를 맨 앞, `Error` 를 맨 뒤에 적었으므로 `Trace < Debug < Info < Warn < Error` 가 되고, `>=` 가 곧 「문턱 이상인가」가 된다.
근거: 2-summary 「동작 방식 (1)」 · 「구현 세부사항 대 언어 보장」.

### 5. 범위를 벗어날 때 `Drop::drop` 이 저절로 불리기 때문이다(RAII)

`_span` 은 `process_request` 가 끝나 범위를 벗어날 때 drop 되고, 그때 `impl Drop for Span` 의 `drop` 이 불려 「완료」 줄과 `start.elapsed()` 를 찍는다.
「끝」을 따로 부를 필요가 없어서 일찍 `return` 하는 길이 생겨도 완료 기록이 빠지지 않는다.
밑줄로 시작하는 이름은 「안 쓰는 변수」 경고만 막을 뿐, 이름이 있으니 범위 끝까지 산다.
근거: 2-summary 「동작 방식 (5)」 · 「문법 — 형태와 규칙」.

### 6. 걸린다 — `starts_with` 는 `::` 경계를 따지지 않는다

`"dbx::cache".starts_with("db")` 는 참이므로 `"db"` 필터의 `Debug` 문턱이 `dbx::cache` 에도 적용된다.
의도와 다른 모듈까지 자세히 찍히거나 덜 찍힐 수 있다.
근거: 2-summary 「어디서 틀리나 3」.

### 7. `format!` 비용은 이미 냈고, 시간 계산과 찍기만 아꼈다

`log_msg!` 는 `&format!(...)` 으로 문자열을 만든 뒤에 `log` 를 부른다.
`log` 는 첫머리에서 `enabled` 로 판정하고 떨어지면 돌아가므로, `SystemTime` 계산과 `println!` 은 하지 않는다.
근거: 2-summary 「동작 방식 (3)」 · 「동작 방식 (4)」 · 「어디서 틀리나 4」.

### 8. `Logger::new(Level::Debug).with_module_level("hyper", Level::Warn)`

`RUST_LOG` 의 쉼표 앞 `debug` 는 전역 문턱이라 `Logger::new(Level::Debug)` 다.
`hyper=warn` 은 모듈 필터라 `.with_module_level("hyper", Level::Warn)` 이다.
차이는 `RUST_LOG` 가 환경변수라 다시 빌드하지 않고 실행할 때 바꿀 수 있다는 점이다.
근거: 2-summary 「동작 방식 (2)」 · 「동작 방식 (6)」 · 「어디서 틀리나 1」.

### 9. 필드별로 기계가 검색 · 집계할 수 있게 된다

`request_id=req-001` 처럼 이름 붙은 필드는 JSON 으로 내보내면 수집 시스템이 그 필드 이름으로 거르고 모을 수 있다.
사람이 읽는 `HH:MM:SS [INFO ] …` 꼴은 문장 속에서 값을 뽑아내야 해서 검색이 어렵다.
원본 팁도 프로덕션에서는 JSON 출력과 ELK · Datadog 수집을 함께 쓴다고 한다 — 원본 예의 `.json()` 이 그 자리다.
근거: 2-summary 「한눈에」의 구조화된 로깅 용어 · 「어디서 틀리나 8」.

## 실습 정답

### 실습 1. 레벨 필터 로거와 RAII 스팬 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 다섯 변형 · 선언 차례 비교 | `#[derive(..., PartialOrd, Ord)] enum Level` |
| 2. 다섯 글자 `Display` | `impl fmt::Display for Level` 의 `match` (`"INFO "` · `"WARN "`) |
| 3. 전역 레벨 + 모듈 필터 목록 | `struct Logger { min_level, module_filters }` |
| 4. 생성 · 필터 더하기 빌더 | `Logger::new` · `with_module_level(mut self, …) -> Self` |
| 5. 접두사 첫 일치 판정 | `enabled` 의 `for` + `starts_with` + `return level >= *filter_level` |
| 6. 판정 후 시각과 한 줄 | `log` 의 `if !self.enabled(..) { return; }` · `% 86400` · `println!("{:02}:{:02}:{:02} [{}] {} - {}", …)` |
| 7. 시작 줄 + 시작 시각 | `Span::new` 의 `println!("  -> {} 시작", …)` · `Instant::now()` |
| 8. 필드 빌더 | `Span::field(mut self, …) -> Self` |
| 9. drop 시 완료 줄 | `impl Drop for Span` 의 `fields_str` · `format!(" {{{}}}", …)` · `self.start.elapsed()` |
| 10. 형식 인자 매크로 | `macro_rules! log_msg` 의 `$($arg:tt)*` → `format!($($arg)*)` |
| 11. 요청 · 에러 흉내 | `process_request` 의 `_span` · `simulate_error` |
| 12. `main` 다섯 절 | `logger` (Trace) · `filtered_logger` · `simulate_error(&filtered_logger)` · `_outer` / `_inner` 블록 · `println!(r#"…"#)` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`rust/rust-practical/reference/logging.rs`

```rust
// [실전 Rust] 로깅
// 설명: log, env_logger, tracing을 이용한 구조화된 로깅 패턴
// 팁: RUST_LOG 환경변수로 런타임에 로그 레벨을 조절한다(예: RUST_LOG=debug,hyper=warn). tracing은 log보다 구조화되어 있고 async 환경에 적합하다. 프로덕션에서는 JSON 형식 출력과 함께 ELK나 Datadog으로 수집한다.

// === 로깅 패턴: 구조화된 로그 시스템 ===
// Cargo.toml:
//   log = "0.4"
//   env_logger = "0.11"
//   tracing = "0.1"
//   tracing-subscriber = "0.3"

// Display 구현
use std::fmt;
// 타임스탬프 생성용
use std::time::SystemTime;

// ===== 1. 로그 레벨 정의 =====

// 로그 레벨 - PartialOrd로 비교 연산 가능 (level >= min_level)
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
enum Level {
    Trace,
    Debug,
    Info,
    Warn,
    Error,
}

// 5글자로 정렬되도록 패딩
impl fmt::Display for Level {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            Level::Trace => write!(f, "TRACE"),
            Level::Debug => write!(f, "DEBUG"),
            Level::Info =>  write!(f, "INFO "),
            Level::Warn =>  write!(f, "WARN "),
            Level::Error => write!(f, "ERROR"),
        }
    }
}

// ===== 2. 로거 구현 =====

// 로거 - 최소 레벨 + 모듈별 필터 (env_logger의 RUST_LOG 동작)
struct Logger {
    min_level: Level,
    // (모듈명 prefix, 해당 모듈 최소 레벨)
    module_filters: Vec<(String, Level)>,
}

impl Logger {
    // 기본 레벨로 초기화
    fn new(min_level: Level) -> Self {
        Logger {
            min_level,
            module_filters: Vec::new(),
        }
    }

    // 특정 모듈에 별도 레벨 적용 - RUST_LOG=info,db=debug 패턴
    fn with_module_level(mut self, module: &str, level: Level) -> Self {
        self.module_filters.push((module.to_string(), level));
        self
    }

    // 출력 여부 결정 - 모듈 prefix 매칭 우선, 없으면 전역 레벨
    fn enabled(&self, level: Level, module: &str) -> bool {
        for (filter_module, filter_level) in &self.module_filters {
            if module.starts_with(filter_module.as_str()) {
                return level >= *filter_level;
            }
        }
        level >= self.min_level
    }

    // 실제 로그 출력 - 시간 + 레벨 + 모듈 + 메시지
    fn log(&self, level: Level, module: &str, message: &str) {
        // 필터 체크 - 통과 못하면 즉시 리턴
        if !self.enabled(level, module) {
            return;
        }

        // UNIX epoch부터의 초 -> HH:MM:SS 변환
        let now = SystemTime::now()
            .duration_since(SystemTime::UNIX_EPOCH)
            .unwrap();
        let secs = now.as_secs() % 86400; // 하루 내 초
        let hours = secs / 3600;
        let mins = (secs % 3600) / 60;
        let s = secs % 60;

        // 표준 포맷 출력
        println!("{:02}:{:02}:{:02} [{}] {} - {}",
            hours, mins, s, level, module, message);
    }
}

// ===== 3. 구조화된 로깅 (tracing 스타일) =====

// 작업 단위(Span) - 시작/종료 시간 자동 측정
#[derive(Debug)]
struct Span {
    name: String,
    // 구조화된 필드 (key=value 쌍)
    fields: Vec<(String, String)>,
    start: std::time::Instant,
}

impl Span {
    // 시작 - 진입 로그 출력
    fn new(name: &str) -> Self {
        println!("  -> {} 시작", name);
        Span {
            name: name.to_string(),
            fields: Vec::new(),
            start: std::time::Instant::now(),
        }
    }

    // 필드 추가 - tracing의 span!(field = value) 시뮬레이션
    fn field(mut self, key: &str, value: &str) -> Self {
        self.fields.push((key.to_string(), value.to_string()));
        self
    }
}

// 스팬 종료 시 자동 호출 - RAII 패턴으로 자동 측정/출력
impl Drop for Span {
    fn drop(&mut self) {
        let elapsed = self.start.elapsed();
        // 필드들을 "key=value, key=value" 포맷으로
        let fields_str: Vec<String> = self.fields.iter()
            .map(|(k, v)| format!("{}={}", k, v))
            .collect();
        let fields = if fields_str.is_empty() {
            String::new()
        } else {
            format!(" {{{}}}", fields_str.join(", "))
        };
        println!("  <- {} 완료{} ({:?})", self.name, fields, elapsed);
    }
}

// ===== 4. 로그 매크로 시뮬레이션 =====

// log::info! 같은 매크로 - format! 인자를 그대로 전달
macro_rules! log_msg {
    ($logger:expr, $level:expr, $module:expr, $($arg:tt)*) => {{
        $logger.log($level, $module, &format!($($arg)*));
    }};
}

// ===== 5. 실제 사용 예시 =====

// HTTP 요청 처리 시뮬레이션 - 여러 모듈에서 다양한 레벨로 로그
fn process_request(logger: &Logger, request_id: &str, path: &str) {
    // _span: drop될 때까지 살아있는 스팬 (언더스코어 prefix는 unused 경고 회피)
    let _span = Span::new("process_request")
        .field("request_id", request_id)
        .field("path", path);

    // 일반 정보 로그
    log_msg!(logger, Level::Info, "http::server", "요청 수신: {} {}", request_id, path);

    // 인증 단계 - debug/trace로 상세 정보
    log_msg!(logger, Level::Debug, "http::auth", "토큰 검증 중...");
    log_msg!(logger, Level::Trace, "http::auth", "토큰 디코딩 세부 정보...");
    log_msg!(logger, Level::Info, "http::auth", "인증 성공: user_42");

    // DB 쿼리
    log_msg!(logger, Level::Debug, "db::query", "SELECT * FROM users WHERE id = 42");
    log_msg!(logger, Level::Trace, "db::pool", "커넥션 풀에서 연결 획득");

    // 응답
    log_msg!(logger, Level::Info, "http::server", "응답 전송: 200 OK");
}

// 에러 시뮬레이션 - warn/error 레벨 사용 예
fn simulate_error(logger: &Logger) {
    log_msg!(logger, Level::Warn, "db::pool", "커넥션 풀 80% 사용 중");
    log_msg!(logger, Level::Error, "db::query", "쿼리 실패: connection refused");
    log_msg!(logger, Level::Error, "http::server", "내부 서버 에러: 500");
}

fn main() {
    println!("=== 1. 기본 로깅 (모든 레벨) ===");
    // Trace 이상 모두 출력
    let logger = Logger::new(Level::Trace);
    log_msg!(logger, Level::Trace, "app", "트레이스 메시지");
    log_msg!(logger, Level::Debug, "app", "디버그 메시지");
    log_msg!(logger, Level::Info, "app", "정보 메시지");
    log_msg!(logger, Level::Warn, "app", "경고 메시지");
    log_msg!(logger, Level::Error, "app", "에러 메시지");

    println!("\n=== 2. 모듈별 필터링 ===");
    // 기본 INFO + db는 DEBUG + http::auth는 TRACE
    let filtered_logger = Logger::new(Level::Info)
        .with_module_level("db", Level::Debug)    // DB는 Debug부터
        .with_module_level("http::auth", Level::Trace); // 인증은 Trace부터

    println!("필터: 기본=INFO, db=DEBUG, http::auth=TRACE");
    process_request(&filtered_logger, "req-001", "/api/users");

    println!("\n=== 3. 에러 로깅 ===");
    simulate_error(&filtered_logger);

    println!("\n=== 4. 구조화된 로깅 (Span) ===");
    {
        // 외부 스팬 - HTTP 요청 전체
        let _outer = Span::new("http_request")
            .field("method", "GET")
            .field("path", "/api/users");

        {
            // 내부 스팬 - DB 쿼리 (외부 스팬 안에 중첩)
            let _inner = Span::new("db_query")
                .field("sql", "SELECT * FROM users");
            // 쿼리 실행 시뮬레이션 - 부하 발생
            let sum: u64 = (0..100_000).sum();
            let _ = sum;
        } // db_query 스팬 종료 + 소요 시간 출력

    } // http_request 스팬 종료

    // 실제 라이브러리 사용 코드
    println!("\n=== 실제 사용 코드 ===");
    println!(r#"
// // env_logger
// env_logger::init();  // RUST_LOG=debug cargo run
// log::info!("서버 시작");
// log::debug!("설정: {{:?}}", config);
//
// // tracing
// tracing_subscriber::fmt()
//     .with_max_level(tracing::Level::DEBUG)
//     .with_target(true)
//     .json()  // JSON 형식 출력
//     .init();
//
// #[tracing::instrument]
// async fn handle_request(req: Request) -> Response {{
//     tracing::info!(path = %req.path(), "요청 처리");
//     let user = get_user(req.user_id()).await;
//     tracing::debug!(?user, "유저 조회 완료");
// }}
"#);
}
```

**실행 결과** — 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다).

**풀이 요점**
- 레벨 비교는 `derive(PartialOrd, Ord)` 한 줄이 다 한다 — 변형을 덜 중요한 것부터 적는 것이 핵심이다.
- `enabled` 는 첫 일치에서 `return` 하므로 구체적인 필터를 먼저 넣어야 한다.
- `log` 는 판정을 맨 앞에 두어 버릴 메시지의 시간 계산과 찍기를 건너뛴다(문자열 꾸미기는 매크로에서 이미 끝났다).
- 스팬의 「완료」는 `Drop` 이 맡는다 — 이름 있는 변수(`_span` · `_outer` · `_inner`)에 묶어야 범위 끝까지 산다.
- 중첩 블록 덕에 `db_query` 가 `http_request` 보다 먼저 끝난다.
- 원시 문자열 안이라도 `println!` 의 형식 문자열이므로 `{{` · `}}` 로 중괄호를 적는다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
