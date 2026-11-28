# rust/rust-project-structures/03 — 로깅 & 트레이싱 — 정리 (힌트)

> 출처 — study-site 항목 `rust/logging-tracing`(항목 데이터 `data/rust/project-structures.json`) · 정답 코드 study-practice `rust/rust-project-structures/reference/logging-tracing.rs`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다).

## 한눈에 — 쉽게 말하면

**로깅과 트레이싱은 「공장의 작업 일지」와 「스톱워치」다.**
작업 일지에는 한 줄마다 등급 도장(주의 · 위험 등), 부서 이름, 내용, 그리고 「기계 번호=7, 불량 수=3」 같은 항목 칸이 있다.
관리자는 「주의 등급 이상만 올려라」 하고 기준을 정한다.
그 기준 아래 줄은 일지에 적히지 않는다.
스톱워치는 작업을 시작할 때 누르고, 작업자가 작업대를 떠나면 저절로 멈추면서 걸린 시간을 적는다.
Rust 의 로깅도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 등급 도장 | `Level` (`Trace` · `Debug` · `Info` · `Warn` · `Error`) |
| 부서 이름 | `target` (예: `"http"` · `"app"`) |
| 내용 | `message` |
| 항목 칸 「기계 번호=7」 | `fields` 의 `key=value` 쌍 |
| 「주의 이상만」 기준 | `SimpleLogger` 의 `min_level` |
| 스톱워치 | `Span` |
| 작업대를 떠남 | 변수가 스코프를 벗어남 → `Drop` 이 불림 |

```text
  작업 시작 ──► [스톱워치 누름: Span::new]
      │
      ├─ 일지 한 줄: [ INFO] http: 요청 수신 method=GET
      ├─ 일지 한 줄: [ INFO] http: 요청 처리 완료 status=200
      │
  작업대 떠남 ──► [스톱워치 멈춤 + 걸린 시간 기록: Drop]
```

## 이 주제가 답하려는 질문

1. 로그 한 줄을 「글 한 줄」이 아니라 「등급 + 출처 + 내용 + key=value 항목」으로 쪼개 남기면 무엇이 좋아지나?
2. 「이 등급 이상만 찍어라」 필터는 어떻게 비교로 바뀌나?
3. 어떤 작업이 얼마나 걸렸는지를, 끝내는 코드를 따로 부르지 않고 어떻게 자동으로 재나?
4. 손으로 만든 이 구조가 실제 `tracing` 크레이트의 무엇에 해당하나?

## 동작 방식

### (1) 로그 레벨과 필터 — 등급을 크기로 비교한다

**언제 쓰나** — 개발 중에는 자세한 로그까지 보고, 운영 중에는 경고 이상만 보고 싶을 때.
등급을 숫자처럼 비교할 수 있으면 「기준 이상만」을 `>=` 한 번으로 거를 수 있다.

```text
enum Level { Trace=0, Debug=1, Info=2, Warn=3, Error=4 }   + derive(PartialOrd, Ord)
          │
          ▼
  Trace < Debug < Info < Warn < Error   (크기 순서가 생긴다)
          │
          ▼
  SimpleLogger { min_level: Debug }
  log(event):  event.level >= Debug ?
          │
   ┌──────┴───────┐
  예(Debug~Error)  아니오(Trace)
   │               │
  한 줄 찍음        아무것도 안 함
```

- `enum Level` 에 `PartialOrd` · `Ord` 를 derive 하면 변형끼리 `<` · `>=` 비교가 된다.
- 이 코드는 낮은 등급부터 선언하고 판별값도 0~4 로 맞췄으므로 `Trace` 가 가장 작고 `Error` 가 가장 크다.
- `SimpleLogger::log` 는 `event.level >= self.min_level` 일 때만 찍는다.
- `main` 은 `min_level` 을 `Debug` 로 두므로 `Trace` 만 걸러지고 나머지는 모두 찍힌다.
- 따라서 이 필터가 맞게 돌려면 **선언 차례가 곧 등급 차례**여야 한다.
  차례를 바꾸면 비교 결과도 함께 바뀌고, 컴파일러는 아무 말도 하지 않는다.

> **derive** — `#[derive(...)]` 로 트레이트 구현을 컴파일러가 자동으로 만들게 하는 것.\
> 예: `#[derive(PartialOrd, Ord)]` 를 달면 `Level::Info >= Level::Debug` 를 쓸 수 있다.

> **판별값** — enum 변형에 붙은 정수 값.\
> 예: `Info = 2` 에서 `2`.

레벨을 글자로 찍을 때는 `fmt::Display` 를 직접 구현한다.
`INFO` 와 `WARN` 은 네 글자라서 앞에 공백을 하나 붙여 `" INFO"` · `" WARN"` 으로 쓴다.
그러면 다섯 레벨이 모두 다섯 칸을 차지해 로그 줄의 세로 줄이 맞는다.

> **Display** — `{}` 로 값을 찍을 때 쓰이는 사람이 읽는 형식의 트레이트.\
> 예: `impl fmt::Display for Level` 이 있으면 `format!("{}", Level::Info)` 가 `" INFO"` 가 된다.

### (2) 구조화된 로그 이벤트 — 메시지와 항목을 따로 담는다

**언제 쓰나** — 나중에 로그 분석 도구에서 「`status=500` 인 줄만」 「`path=/users` 인 줄만」처럼 골라 보고 싶을 때.

```text
LogEvent {
  level:   Info
  target:  "http"
  message: "요청 수신"
  fields:  [("method","GET"), ("path","/users")]
}
          │  Display
          ▼
  write!  "[{level}] {target}: {message}"
  필드마다 " {k}={v}"
          │
          ▼
  [ INFO] http: 요청 수신 method=GET path=/users      ← 찍히는 꼴
```

- `LogEvent` 는 레벨 · 출처(`target`) · 메시지 · 필드 목록 네 칸을 가진 구조체다.
- `Display` 구현은 먼저 `[레벨] 출처: 메시지` 를 쓴다.
- 이어서 필드마다 앞에 공백 하나를 두고 `k=v` 를 덧붙인다.
- `write!(...)?` 의 `?` 는 쓰기가 실패하면 그 `fmt::Error` 를 바로 돌려보낸다.
- `SimpleLogger::log` 는 이 한 줄 앞에 시각 문자열과 공백을 붙여 `println!` 한다.
- 시각은 `chrono_like_now()` 가 돌려주는 **고정 문자열** `"2026-04-04T12:00:00"` 이다.
  실제로는 `chrono::Utc::now()` 같은 것을 쓴다는 흉내다.

> **구조화된 로깅** — 로그를 자유 문장 하나가 아니라 이름 붙은 항목(`key=value`)으로 남기는 방식.\
> 예: `"유저 42 조회"` 대신 `message="유저 조회", user_id=42`.

메시지에 값을 섞어 `"유저 42 조회"` 로 쓰면 사람은 읽어도, 도구는 42 가 무엇의 값인지 모른다.
`user_id=42` 로 따로 두면 도구가 `user_id` 로 검색하고 거를 수 있다.
원본 팁도 이것을 「로그 분석 도구에서 검색과 필터링에 유리하다」고 적는다.

### (3) Span — 스코프가 끝날 때 걸린 시간을 저절로 찍는다

**언제 쓰나** — 함수 전체나 DB 조회처럼 「한 덩어리의 작업」이 얼마나 걸렸는지 재고 싶을 때.

```text
let _span = Span::new("handle_request")      ← start = Instant::now()
               .with_field("method", "GET")   ← self 를 받아 필드 넣고 self 를 돌려줌
               .with_field("path", "/users");
      │
      │   ... 작업 ...
      │
  }  ← 스코프 끝: _span 이 버려짐 → Drop::drop 자동 호출
      │
      ▼
  "  SPAN [handle_request] method=GET path=/users elapsed=<걸린 시간>"
```

- `Span::new` 는 이름을 받고, 지금 시각을 `Instant::now()` 로 기록하며, 필드는 빈 `Vec` 로 시작한다.
- `with_field(mut self, ...) -> Self` 는 값 자체를 받아 필드를 하나 넣고 다시 돌려준다.
  그래서 `.with_field(..).with_field(..)` 처럼 줄줄이 이어 쓸 수 있다.
- `elapsed()` 는 `self.start.elapsed()` 로 시작부터 지금까지 지난 시간을 `Duration` 으로 준다.
- `impl Drop for Span` 의 `drop` 은 필드를 `k=v` 로 만들어 공백으로 잇고, 앞에 공백 두 칸을 둔 `SPAN` 줄을 찍는다.
- 시간은 `{:.3?}` 로 찍는다 — `Duration` 을 디버그 형식으로, 소수점 아래 세 자리까지.
- 끝을 알리는 코드를 따로 부르지 않아도, 변수가 사라지는 순간이 곧 작업의 끝이 된다.
  원본 주석은 이것이 `tracing` 크레이트의 `Span` 과 같은 패턴이라고 적는다.

> **RAII** — 자원의 수명을 변수의 수명에 묶어, 변수가 사라질 때 정리 코드가 저절로 돌게 하는 방식.\
> 예: `Span` 이 스코프를 벗어나면 `Drop` 이 걸린 시간을 찍는다.

> **Drop** — 값이 버려질 때 불리는 트레이트.\
> 예: `impl Drop for Span { fn drop(&mut self) { ... } }`.

> **Instant** — 시간 간격을 재기 위한 시각 값.\
> 예: `let t = Instant::now(); ... t.elapsed()`.

**변수 이름이 수명을 정한다.**

```text
let _span = Span::new(..);   →  이름 있는 바인딩. 스코프 끝까지 산다.
let _     = Span::new(..);   →  바인딩이 아니다. 그 문장이 끝나자마자 버려진다 → 곧바로 SPAN 줄.
```

- `_span` 처럼 밑줄로 **시작하는** 이름은 「쓰지 않아도 경고하지 마라」는 뜻일 뿐, 보통 변수와 똑같이 스코프 끝까지 산다.
- `_` 하나만 쓰면 값을 어디에도 묶지 않으므로 그 자리에서 바로 버려지고, 잰 시간은 거의 0 이 된다.

**여러 Span 이 한 스코프에 있으면 나중에 만든 것부터 버려진다.**
그래서 DB 조회만 재고 싶을 때는 `drop(_db_span)` 으로 그 자리에서 직접 버린다.
직접 버리지 않으면 `_db_span` 은 함수 끝까지 살아서, DB 조회 뒤의 로그 작업까지 시간에 들어간다.

### (4) 요청 하나의 흐름 — `handle_request`

**언제 쓰나** — HTTP 요청 처리처럼 「바깥 작업 안에 안쪽 작업이 있는」 흐름에 로그와 Span 을 함께 붙일 때.

```text
handle_request(logger, "GET", "/users")
  │
  ├─ _span 시작 (handle_request, method, path)            ─┐
  ├─ log Info  "요청 수신" method=GET path=/users           │
  ├─ _db_span 시작 (db_query, table=users)   ─┐            │
  ├─ sleep 10ms                               │ db 시간     │ 전체 시간
  ├─ drop(_db_span) ──► SPAN [db_query] ...  ─┘            │
  ├─ path == "/error" ?                                     │
  │     예  → log Error "요청 처리 실패" status=500          │
  │     아니오 → log Info "요청 처리 완료" status=200         │
  └─ 함수 끝 ──► SPAN [handle_request] ...                 ─┘
```

- 맨 먼저 함수 전체를 덮는 `_span` 을 만든다.
- 「요청 수신」 로그를 `http` 타깃, `method` · `path` 필드로 남긴다.
- DB 조회 흉내로 `_db_span` 을 만들고 10ms 를 잔 뒤 직접 버린다 — 이 자리에서 `db_query` 의 `SPAN` 줄이 찍힌다.
- 경로가 `"/error"` 면 `Error` 레벨로 「요청 처리 실패」 `status=500`, 아니면 `Info` 레벨로 「요청 처리 완료」 `status=200` 을 남긴다.
- 함수가 끝나면 `_span` 이 버려지며 `handle_request` 의 `SPAN` 줄이 **마지막**에 찍힌다.
- 바깥 Span 은 안쪽 Span 보다 먼저 시작해 나중에 끝나므로, 바깥 Span 의 걸린 시간은 안쪽보다 크거나 같다.
- `main` 은 `min_level` 이 `Debug` 인 로거로 「서버 시작」(`port=8080`, `env=development`)을 찍고, `GET /users` · `POST /users` · `GET /error` 세 요청을 차례로 처리한다.

### (5) 진짜 `tracing` 크레이트로 옮기면

**언제 쓰나** — 손으로 만든 구조 대신 실무에서 로깅과 Span 을 한꺼번에 다룰 때.

```text
손으로 만든 것                       tracing 크레이트
─────────────────────────────────    ─────────────────────────────────
LogEvent { level: Info, fields.. }   info!(user_id = id, "유저 조회");
Span::new("get_user") + Drop          #[instrument] 를 함수에 붙임
SimpleLogger { min_level }            tracing_subscriber + EnvFilter (RUST_LOG)
Display 로 한 줄 형식 결정             fmt() ... .json() 같은 출력 형식 설정
```

- `tracing` 은 `log` 크레이트의 상위 호환이고, 여기에 Span(작업 범위)을 더 지원한다(원본 팁).
- `#[instrument]` 를 함수에 붙이면 그 함수에 Span 이 자동으로 붙는다 — 손으로 `Span::new` 를 쓰고 `Drop` 을 구현한 일을 속성 하나가 대신한다.
- `info!(user_id = id, "유저 조회")` 처럼 매크로 안에 `key = value` 를 적어 구조화된 필드를 남긴다.
- `tracing-subscriber` 로 출력 형식(JSON, pretty 등)을 정한다 — 예제는 `fmt().with_env_filter(EnvFilter::from_default_env()).json().init()` 이다.
- `RUST_LOG=info,myapp=debug` 처럼 환경 변수로 모듈별 레벨을 정한다 — 기본은 `info`, `myapp` 모듈은 `debug` 까지.
- `tracing` 의 `target` 필드 기본값이 `module_path!()` 이므로, `mod` 구조가 그대로 로그 필터의 경로가 된다(예: `myapp::handlers=debug`).
- 로깅 초기화는 `main.rs` 나 `lib.rs` 의 `init_tracing()` 같은 도우미에서 **한 번만** 한다.
- feature flag 로 개발용 · 운영용 출력 형식을 나눌 수 있다.
- 예제의 `Cargo.toml` 은 `tracing = "0.1"` 과 `tracing-subscriber` `0.3`(`env-filter` 기능)을 적는다.

> **subscriber** — 만들어진 로그 이벤트와 Span 을 받아 거르고 형식을 입혀 내보내는 쪽.\
> 예: `tracing_subscriber::fmt().json().init()`.

> **`module_path!()`** — 그 코드가 있는 모듈 경로를 문자열로 주는 매크로.\
> 예: `src/handlers.rs` 안이면 `"myapp::handlers"` 꼴.

## 문법 — 형태와 규칙

```rust
use std::time::Instant;

struct Timer { name: String, start: Instant }

impl Drop for Timer {
    fn drop(&mut self) {
        println!("  SPAN [{}] elapsed={:.3?}", self.name, self.start.elapsed());
    }
}

fn main() {
    let _t = Timer { name: "main".to_string(), start: Instant::now() };
    let level_ok = 2 >= 1;                  // enum 을 derive 하면 변형끼리 이렇게 비교된다
    println!("{} {{key}}={}", level_ok, 7); // {{ }} 는 글자 { } 로 찍힌다
}   // ← 여기서 _t 가 버려지며 SPAN 줄이 찍힌다
```

- `#[derive(PartialEq, Eq, PartialOrd, Ord)]` 를 enum 에 달면 변형끼리 크기 비교가 된다.
- `impl fmt::Display for T` 의 `fmt` 는 `write!(f, ...)` 로 쓰고 `fmt::Result` 를 돌려준다. 여러 번 쓸 때는 `?` 로 실패를 넘긴다.
- `fn with_field(mut self, ..) -> Self` 꼴은 값을 받아 고쳐 돌려주는 빌더 꼴이다.
- `impl Drop for T` 의 `drop(&mut self)` 은 값이 버려질 때 한 번 불린다.
- `drop(x)` 를 부르면 그 자리에서 `x` 를 버린다(그때 `Drop` 이 돈다).
- `{:.3?}` 는 디버그 형식(`?`)에 정밀도 3(`.3`)을 준 것이다.
- `"..".into()` 는 `&str` 을 필요한 `String` 으로 바꾼다.
- `println!` 의 형식 문자열 안에서 `{{` 는 `{`, `}}` 는 `}` 로 찍힌다.
- `r#"..."#` 은 raw 문자열이다 — 역슬래시 이스케이프를 해석하지 않고 따옴표를 그대로 담는다.
  그러나 `println!` 에 넘기면 **형식 문자열 규칙은 그대로 적용**되므로 `{{` 는 여전히 `{` 가 된다.

| `tracing` 쪽 문법 | 뜻 (원본 기준) |
|---|---|
| `#[instrument]` | 함수에 Span 을 자동으로 붙인다 |
| `info!(user_id = id, "…")` | `Info` 레벨 이벤트 + `user_id` 필드 |
| `tracing_subscriber::fmt()` | 출력 형식 설정의 출발점 |
| `.with_env_filter(EnvFilter::from_default_env())` | `RUST_LOG` 로 레벨을 거른다 |
| `.json()` | JSON 형식으로 내보낸다 |
| `.init()` | 전역으로 설치한다(한 번만) |
| `RUST_LOG=info,myapp=debug` | 기본 `info`, `myapp` 은 `debug` |

## 어디서 틀리나

### 1. `let _ = Span::new(..)` 로 받는다

`_` 는 바인딩이 아니라서 Span 이 그 문장 끝에서 곧바로 버려진다.
`SPAN` 줄이 작업보다 먼저 찍히고 걸린 시간은 거의 0 이 된다.
스코프 끝까지 살리려면 `_span` 처럼 이름을 붙인다.

### 2. 안쪽 Span 을 직접 닫지 않는다

`drop(_db_span)` 을 빼면 `_db_span` 은 함수 끝까지 살아서, DB 조회 뒤의 로그 작업까지 「DB 시간」에 들어간다.
이때는 버려지는 차례가 나중에 만든 것부터이므로 `db_query` 줄이 `handle_request` 줄 바로 앞, 마지막 로그 뒤에 찍힌다.
재고 싶은 구간이 끝나는 자리에서 직접 버린다.

### 3. `Level` 의 변형 차례를 바꾼다

derive 한 비교는 변형의 차례(이 코드에서는 판별값 0~4 와 같다)를 따른다.
`Error` 를 맨 앞에 두면 `Error` 가 가장 작은 등급이 되고, `>= min_level` 필터가 거꾸로 걸러 낸다.
컴파일 오류가 나지 않으므로 알아채기 어렵다.

### 4. 값을 메시지 문장에 섞는다

`"유저 42 조회"` 처럼 쓰면 분석 도구가 `user_id` 로 찾지 못한다.
값은 `key=value` 필드로 따로 남긴다 — 검색과 필터링에 유리하다(원본 팁).

### 5. 걸린 시간을 정확한 값으로 기대한다

`sleep(10ms)` 를 해도 `elapsed` 가 늘 같은 값으로 찍히지 않는다.
운영체제 스케줄링에 따라 실행마다 달라진다.
알 수 있는 것은 「대략 10ms 이상」과 「바깥 Span ≥ 안쪽 Span」 정도다.

### 6. 시각이 진짜라고 믿는다

`chrono_like_now()` 는 고정 문자열을 돌려주는 흉내다.
모든 줄에 같은 시각이 찍힌다.
실제로는 `chrono::Utc::now()` 같은 것으로 바꿔야 한다.

### 7. 로깅을 여러 군데에서 초기화한다

원본은 로깅 초기화를 `main.rs` 나 `lib.rs` 의 `init_tracing()` 도우미에서 **한 번만** 하라고 적는다.
라이브러리 함수나 테스트마다 따로 `.init()` 을 부르지 않는다.

### 8. `RUST_LOG` 경로가 모듈 경로와 어긋난다

`target` 기본값이 `module_path!()` 이므로 필터 경로는 `mod` 구조를 그대로 따른다.
모듈 이름을 바꾸거나 옮기면 `RUST_LOG=myapp::handlers=debug` 같은 설정이 더는 맞지 않을 수 있다.

### 9. 형식 문자열 속 중괄호

`println!` 에 넘긴 문자열 안의 `{` 는 자리표시자로 읽힌다.
글자 그대로의 중괄호는 `{{` · `}}` 로 적어야 하고, raw 문자열이어도 마찬가지다.

### 10. 필드 없는 Span

`Drop` 의 형식은 `"  SPAN [{}] {} elapsed=.."` 이다.
필드가 비면 가운데 `{}` 가 빈 문자열이 되어 `]` 와 `elapsed` 사이에 공백이 두 칸 생긴다(코드에서 읽은 것).

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 이름 붙은 지역 변수는 스코프 끝에서 버려지고, 한 스코프 안에서는 나중에 선언한 것부터 버려진다 | Rust 언어 |
| `let _ = 식;` 의 값은 그 문장 끝에서 버려진다 | Rust 언어 |
| `drop(x)` 를 부르면 그 자리에서 `Drop` 이 돈다 | Rust 언어 · 표준 라이브러리 |
| derive 한 `PartialOrd` · `Ord` 가 enum 변형을 차례대로 비교한다 | 표준 라이브러리의 derive 규칙 (선언 차례와 판별값이 다를 때 어느 쪽을 따르는지는 확인 필요) |
| `thread::sleep(10ms)` 는 적어도 10ms 를 잔다 | 표준 라이브러리 문서 (확인 필요) |
| `elapsed` 의 실제 값 | 보장 없음 — 운영체제 · 하드웨어 · 부하에 달림 |
| `{:.3?}` 가 `Duration` 을 `10.123ms` 같은 꼴로 찍는다 | 표준 라이브러리의 `Debug` 구현 (정확한 꼴은 확인 필요) |
| `tracing` 은 `log` 의 상위 호환이다 | 크레이트 생태계의 설계 주장 (원본 팁) |
| `target` 기본값이 `module_path!()` 이다 | `tracing` 크레이트 (원본 주석) |
| `RUST_LOG` 로 모듈별 레벨을 정한다 | `tracing-subscriber` 의 `EnvFilter` — 언어가 아니다 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 로그를 도구로 검색 · 집계 | `key=value` 필드 | 값을 섞은 자유 문장 |
| 함수가 얼마나 걸렸나 | Span (`#[instrument]` 또는 RAII 구조체) | 시작 · 끝에 시각을 손으로 찍는 코드 |
| 함수 안 일부 구간만 재기 | 안쪽 Span + 구간 끝에서 `drop` | 함수 끝까지 살아 있는 Span |
| 개발 · 운영의 로그 양 조절 | 레벨 + `RUST_LOG` | 코드에서 `println!` 을 지웠다 켰다 |
| 출력 형식 바꾸기 | subscriber 설정(JSON · pretty), feature flag | 로그 호출마다 형식 바꾸기 |
| 로거 준비 | 진입점에서 한 번 초기화 | 모듈마다 따로 초기화 |

## 핵심 문장

1. **구조화된 로그는 「등급 · 출처 · 메시지 · key=value」를 따로 담아**, 도구가 항목으로 찾고 거를 수 있게 한다.
2. **레벨 필터는 크기 비교 하나다** — 등급의 차례가 곧 비교의 차례이므로 차례를 함부로 바꾸지 않는다.
3. **Span 은 RAII 다** — 변수가 사라질 때 `Drop` 이 걸린 시간을 찍으므로, 변수의 수명(`_span` 대 `_`, 직접 `drop`)이 곧 잰 구간이다.
4. **`tracing` 에서는** `#[instrument]` 가 Span 을, `info!` 등의 매크로가 이벤트를, `tracing-subscriber` 가 필터와 형식을 맡는다.
5. **필터 경로는 모듈 경로다** — `target` 기본값이 `module_path!()` 라서 `RUST_LOG` 가 `mod` 구조를 따라간다.

## 관련 자료

- `config-management` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `rest-api-axum` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- [middleware-tower](../09-middleware-tower/2-summary.md)
- 원본: study-site 항목 데이터 `data/rust/project-structures.json` 의 `logging-tracing`

## 용어 풀이

- **로그 레벨** — 로그의 중요도 등급. 여기서는 `Trace` < `Debug` < `Info` < `Warn` < `Error`.
- **target** — 로그가 어디서 왔는지 적는 출처 이름. 예제에서는 `"http"` · `"app"`.
- **구조화된 로깅** — 로그를 이름 붙은 항목(`key=value`)으로 남기는 방식.
- **필드** — 로그 이벤트나 Span 에 붙는 `key=value` 한 쌍.
- **Span** — 시작과 끝이 있는 작업 범위. 걸린 시간과 필드를 함께 남긴다.
- **RAII** — 자원 정리를 변수의 수명에 묶는 방식.
- **Drop** — 값이 버려질 때 불리는 트레이트.
- **Instant** — 시간 간격을 재는 시각 값.
- **Duration** — 시간의 길이 값. `elapsed()` 가 돌려준다.
- **derive** — 트레이트 구현을 컴파일러가 자동으로 만들게 하는 속성.
- **판별값** — enum 변형에 붙은 정수.
- **Display** — `{}` 형식의 사람이 읽는 출력 트레이트.
- **raw 문자열** — `r#"..."#` 꼴. 이스케이프를 해석하지 않는 문자열.
- **subscriber** — 이벤트와 Span 을 받아 거르고 형식을 입혀 내보내는 쪽.
- **`#[instrument]`** — 함수에 Span 을 자동으로 붙이는 `tracing` 의 속성.
- **`RUST_LOG`** — 레벨 필터를 정하는 환경 변수.
- **`EnvFilter`** — `RUST_LOG` 를 읽어 거르는 `tracing-subscriber` 의 필터.
- **`module_path!()`** — 현재 모듈 경로를 문자열로 주는 매크로.
- **feature flag** — Cargo 기능 이름으로 코드 일부를 켜고 끄는 장치.

## 더 들어가면

- `#[instrument(skip(db))]` 의 `skip(db)` 는 `db` 인자를 Span 의 필드로 기록하지 말라는 뜻이다 — 인자는 기본으로 필드가 되는데, `Debug` 를 구현하지 않았거나 너무 큰 값은 빼야 한다(확인 필요).
- `info!(name = %user.name, ..)` 의 `%` 는 그 값을 `Display` 로, `?` 를 앞에 붙이면 `Debug` 로 기록한다(확인 필요).
- `tracing_subscriber::fmt().init()` 은 전역 subscriber 가 이미 설치돼 있으면 패닉하고, `try_init()` 은 오류를 돌려준다(확인 필요).
- `std::process::exit` 로 끝내거나 `std::mem::forget` 으로 잊은 값은 `Drop` 이 돌지 않는다 — RAII Span 의 끝 줄이 찍히지 않을 수 있다(확인 필요).
- `async fn` 에서는 `.await` 를 지나는 동안 손으로 만든 RAII 가드가 다른 작업과 섞일 수 있어, `tracing` 은 `Instrument` 트레이트(`.instrument(span)`)로 future 에 Span 을 붙이는 방법을 따로 둔다(확인 필요).
- `Instant` 는 단조 증가 시계라서 시스템 시각이 바뀌어도 `elapsed` 가 거꾸로 가지 않는다(확인 필요).
