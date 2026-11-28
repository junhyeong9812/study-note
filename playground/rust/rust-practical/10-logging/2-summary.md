# rust/rust-practical/10 — 로깅 — 정리 (힌트)

> 출처 — study-site 항목 `rust/logging`(항목 데이터 `data/rust/practical.json`) · 정답 코드 study-practice `rust/rust-practical/reference/logging.rs`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다).

## 한눈에 — 쉽게 말하면

**로깅은 「우편물에 중요도 도장을 찍고, 비서가 그 도장을 보고 위로 올릴지 거르는 일」이다.**
모든 편지(메시지)에는 「사소함 · 참고 · 보통 · 주의 · 긴급」 같은 도장(레벨)이 찍힌다.
비서(로거)는 「보통 이상만 올려라」라는 지시(최소 레벨)를 받고 그보다 낮은 편지는 버린다.
그런데 「재무팀 편지는 참고 수준도 올려라」처럼 부서마다 따로 지시(모듈 필터)를 줄 수도 있다.
회의가 열리면 시작 시각과 끝 시각, 안건 메모(필드)를 회의록 한 장(스팬)에 묶어 남긴다.
Rust 의 `log` · `env_logger` · `tracing` 도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 중요도 도장 | `Level` (`Trace` · `Debug` · `Info` · `Warn` · `Error`) |
| 비서 | `Logger` |
| 「보통 이상만 올려라」 | `min_level` |
| 「재무팀은 참고도 올려라」 | `module_filters` · `RUST_LOG=info,db=debug` |
| 회의록 한 장 | `Span` |
| 안건 메모 | 스팬의 필드 `key=value` |

```text
  메시지(레벨, 모듈, 글)
          │
          ▼
   ┌──────────────┐   문턱보다 낮다
   │  Logger 판정 │ ─────────────────▶ 버림
   └──────┬───────┘
          │ 문턱 이상
          ▼
  HH:MM:SS [LEVEL] 모듈 - 글   ← 한 줄 찍기
```

> **로그 레벨** — 메시지의 중요도 등급이다.\
> 예: `Trace` < `Debug` < `Info` < `Warn` < `Error`.

> **구조화된 로깅** — 메시지를 문장 하나가 아니라 `key=value` 필드와 함께 남겨 기계가 읽기 쉽게 하는 방식이다.\
> 예: `request_id=req-001, path=/api/users`.

## 이 주제가 답하려는 질문

1. 들어온 메시지 가운데 무엇을 찍고 무엇을 버리나?
2. 모듈마다 다른 문턱을 두려면 어떻게 판정하나?
3. 「요청 하나」 같은 작업 단위의 시작 · 끝 · 소요 시간 · 맥락을 어떻게 한데 묶어 남기나?
4. 손수 만든 이 구조가 실제 크레이트 `log` · `env_logger` · `tracing` 과 어떻게 이어지나?

## 동작 방식

### (1) 레벨에 순서를 매긴다 — `derive(PartialOrd, Ord)`

**언제 쓰나** — 「이 메시지가 문턱 이상인가」를 `>=` 한 번으로 판정하고 싶을 때 쓴다.

```text
#[derive(..., PartialOrd, Ord)]
enum Level { Trace, Debug, Info, Warn, Error }
        │
        ▼  선언한 차례가 곧 크기 차례
Trace < Debug < Info < Warn < Error
        │
        ▼
level >= min_level  →  true / false
```

- `enum` 에 `PartialOrd` · `Ord` 를 derive 하면 변형(variant)을 **선언한 차례대로** 작은 것부터 큰 것이 된다.
- 그래서 `Trace` 를 맨 위에, `Error` 를 맨 아래에 적으면 「덜 중요한 것 < 더 중요한 것」이 된다.
- 문턱 판정은 정수 비교처럼 `level >= self.min_level` 한 줄로 끝난다.
- `Display` 구현은 `"INFO "` · `"WARN "` 처럼 뒤에 공백을 붙여 다섯 글자로 맞춘다 — 줄마다 `[레벨]` 칸 너비가 같아져 눈으로 훑기 쉽다.

> **derive** — 컴파일러가 트레이트 구현을 자동으로 만들게 하는 속성이다.\
> 예: `#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]`.

### (2) 찍을지 판정한다 — `enabled` 의 접두사 첫 일치

**언제 쓰나** — 전체는 `Info` 로 조용히 두고 특정 모듈만 더 자세히(또는 더 조용히) 보고 싶을 때 쓴다.

```text
module_filters = [("db", Debug), ("http::auth", Trace)]   min_level = Info

enabled(Trace, "db::pool")
   │
   ├─ "db::pool".starts_with("db")?  예 → Trace >= Debug ? 아니오 → false (여기서 끝)
   │
enabled(Info, "http::server")
   ├─ starts_with("db")?          아니오
   ├─ starts_with("http::auth")?  아니오
   └─ 필터 없음 → Info >= Info ? 예 → true
```

- `module_filters` 를 **넣은 차례대로** 훑는다.
- 모듈 이름이 필터 이름으로 **시작하면**(`starts_with`) 그 필터의 레벨로 판정하고 바로 돌아간다 — 뒤 필터는 보지 않는다.
- 어느 필터에도 걸리지 않으면 전역 `min_level` 로 판정한다.
- 이것이 `RUST_LOG=info,db=debug` 의 뜻을 흉내 낸 것이다 — `info` 가 전역 문턱, `db=debug` 가 모듈 필터다.

> **접두사(prefix) 일치** — 문자열이 어떤 문자열로 시작하는지 보는 비교다.\
> 예: `"db::query".starts_with("db")` 는 참이다.

### (3) 한 줄을 찍는다 — `log`

**언제 쓰나** — 판정을 통과한 메시지를 시간 · 레벨 · 모듈 · 글 꼴로 남길 때다.

```text
log(level, module, message)
   │
   ├─ enabled? 아니오 → return (시간 계산도 하지 않는다)
   │
   ├─ SystemTime::now() - UNIX_EPOCH → 초
   ├─ 초 % 86400 → 하루 안의 초 → 시 · 분 · 초
   │
   └─ println!("{:02}:{:02}:{:02} [{}] {} - {}", …)
          → 예: 14:03:27 [INFO ] http::server - 응답 전송: 200 OK
```

- 판정에서 떨어지면 곧바로 돌아가므로, 버려질 메시지는 시간을 구하는 비용을 치르지 않는다.
- 시각은 UNIX epoch 부터 흐른 초를 하루(86400초)로 나눈 나머지로 만든다.
- `{:02}` 는 두 자리로 맞추고 빈자리를 0 으로 채운다.

### (4) 매크로로 부른다 — `log_msg!`

**언제 쓰나** — `log::info!("…{}", x)` 처럼 `format!` 꼴 인자를 그대로 받고 싶을 때다.

```text
log_msg!(logger, Level::Info, "http::server", "요청 수신: {} {}", id, path)
        │
        ▼  $($arg:tt)* 가 뒤쪽 인자를 통째로 받는다
logger.log(Level::Info, "http::server", &format!("요청 수신: {} {}", id, path))
```

- `$($arg:tt)*` 는 남은 토큰을 모두 받아 `format!` 에 그대로 넘긴다.
- 펼쳐진 코드는 `format!` 으로 문자열을 **먼저 만든 뒤** `log` 를 부른다 — 판정은 그다음이다.

> **`macro_rules!`** — 패턴에 맞춰 코드를 펼치는 선언형 매크로다.\
> 예: `log_msg!(logger, Level::Debug, "db", "{}", sql)`.

### (5) 작업 단위를 묶는다 — `Span` 과 `Drop`

**언제 쓰나** — 「요청 하나」「쿼리 하나」의 시작 · 끝 · 걸린 시간 · 맥락 필드를 한데 남기고 싶을 때다.

```text
{
  let _outer = Span::new("http_request")   → "  -> http_request 시작"
                 .field("method","GET") …   (필드는 시작 줄에 없다)
  {
    let _inner = Span::new("db_query")     → "  -> db_query 시작"
    … 작업 …
  }  ← _inner 가 범위를 벗어남 → drop    → "  <- db_query 완료 {sql=…} (걸린 시간)"
}    ← _outer 가 범위를 벗어남 → drop    → "  <- http_request 완료 {method=GET, path=…} (걸린 시간)"
```

- `Span::new` 는 「시작」 줄을 찍고 `Instant::now()` 를 적어 둔다.
- `.field(k, v)` 는 `self` 를 받아 필드를 넣고 다시 돌려주는 빌더 꼴이라 줄줄이 이을 수 있다.
- 「시작」 줄은 `new` 안에서 찍히므로 그 뒤에 붙인 필드는 시작 줄에 나오지 않는다.
- 변수가 범위를 벗어나면 `Drop::drop` 이 저절로 불려 「완료」 줄과 걸린 시간을 찍는다 — 따로 「끝」을 부를 필요가 없다.
- 안쪽 블록이 먼저 닫히므로 안쪽 스팬이 먼저 끝난다.
- 필드가 없으면 중괄호 부분을 빼고, 있으면 `" {k=v, k=v}"` 꼴로 붙인다(`format!` 안의 `{{` · `}}` 는 중괄호 글자 자체다).
- 걸린 시간은 `Duration` 을 `{:?}` 로 찍은 것이라 실행할 때마다 값이 달라진다.

> **RAII** — 값이 만들어질 때 자원을 잡고, 범위를 벗어날 때 소멸자로 자동 정리하는 패턴이다.\
> 예: `_span` 이 범위를 벗어나면 「완료」 줄이 찍힌다.

### (6) 실제 크레이트로 옮기면

**언제 쓰나** — 손수 만든 구조를 실제 서비스 코드로 바꿀 때다.

```text
이 문서의 구조                    실제 크레이트
Logger::new(Info)                 env_logger::init() + RUST_LOG=info
  .with_module_level("db",Debug)  RUST_LOG=info,db=debug
log_msg!(…, Level::Info, …)       log::info!("서버 시작")
Span::new(..).field(..)           #[tracing::instrument] · tracing::info!(path = %…, "…")
println! 한 줄                    tracing_subscriber::fmt().json().init()  → JSON 한 줄
```

- 원본의 예는 `env_logger::init()` 뒤 `RUST_LOG=debug cargo run` 으로 문턱을 고르고 `log::info!` · `log::debug!` 를 부른다.
- `tracing` 쪽은 `tracing_subscriber::fmt()` 에 `.with_max_level(tracing::Level::DEBUG)` · `.with_target(true)` · `.json()` 을 이어 붙인 뒤 `.init()` 한다.
- `#[tracing::instrument]` 를 `async fn` 에 붙이고, 안에서 `tracing::info!(path = %req.path(), "요청 처리")` 처럼 필드와 메시지를 함께 남긴다.
- `RUST_LOG` 는 환경변수라서 다시 컴파일하지 않고 **실행할 때** 레벨을 바꿀 수 있다.

## 문법 — 형태와 규칙

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
enum Level { Trace, Debug, Info, Warn, Error }

let logger = Logger::new(Level::Info)              // 전역 문턱
    .with_module_level("db", Level::Debug);        // db 로 시작하는 모듈은 Debug 부터

log_msg!(logger, Level::Debug, "db::query", "SQL: {}", "SELECT 1"); // 찍힌다
log_msg!(logger, Level::Debug, "http::server", "무시됨");          // 버려진다

{
    let _span = Span::new("job").field("id", "7"); // "  -> job 시작"
}                                                  // "  <- job 완료 {id=7} (…)"
```

- 레벨 순서는 `enum` 선언 차례로 정해진다 — 덜 중요한 것을 먼저 적는다.
- `with_module_level` 과 `field` 는 `mut self` 를 받아 `Self` 를 돌려주는 빌더다 — 결과를 다시 변수에 받거나 이어서 부른다.
- 모듈 필터는 넣은 차례로 보고 처음 일치한 것 하나만 쓴다.
- 스팬은 이름 있는 변수(`_span` 처럼 밑줄로 시작해도 된다)에 묶어야 범위 끝까지 살아 있다 — 밑줄 접두사는 「안 쓰는 변수」 경고만 막는다.
- 로그 한 줄 꼴: `HH:MM:SS [LEVEL] 모듈 - 메시지`.
- 스팬 줄 꼴: `  -> 이름 시작` / `  <- 이름 완료 {k=v, …} (걸린 시간)`.

| 레벨 | `Display` | 쓰임(원본 예제 기준) |
|---|---|---|
| `Trace` | `TRACE` | 토큰 디코딩 세부 · 커넥션 획득 같은 가장 잘게 쪼갠 흐름 |
| `Debug` | `DEBUG` | 토큰 검증 중 · 실행한 SQL 같은 개발용 상세 |
| `Info` | `INFO ` | 요청 수신 · 인증 성공 · 응답 전송 같은 정상 흐름 |
| `Warn` | `WARN ` | 커넥션 풀 80% 사용 같은 위험 신호 |
| `Error` | `ERROR` | 쿼리 실패 · 500 에러 같은 실패 |

## 어디서 틀리나

### 1. 레벨은 다시 빌드하지 않고 `RUST_LOG` 로 고른다
원본 팁: `RUST_LOG` 환경변수로 **런타임에** 레벨을 조절한다.
예: `RUST_LOG=debug,hyper=warn` — 전역은 `debug`, `hyper` 모듈은 `warn` 부터만.
레벨을 코드에 박아 두면 바꿀 때마다 다시 컴파일해야 한다.

### 2. 필터를 넣는 차례가 결과를 바꾼다
이 문서의 `enabled` 는 **처음 일치한** 필터로 끝낸다.
`"http"` 를 `"http::auth"` 보다 먼저 넣으면 `http::auth` 모듈도 `"http"` 필터에 걸려 뒤의 더 자세한 설정이 무시된다.
구체적인 필터를 먼저 넣어야 의도대로 된다.

### 3. 접두사 일치는 이름 경계를 모른다
`starts_with("db")` 는 `db::query` 뿐 아니라 `dbx::cache` 처럼 `db` 로 시작하는 엉뚱한 모듈에도 걸린다.
`::` 경계를 따지지 않기 때문이다.

### 4. 버려질 메시지도 `format!` 비용은 낸다
`log_msg!` 는 `format!` 으로 문자열을 만든 **뒤** `log` 를 부른다.
`log` 안의 판정에서 떨어져도 문자열은 이미 만들어졌다.
`log` 가 먼저 판정하고 돌아가 아끼는 것은 시간 계산과 찍기뿐이다.

### 5. 찍히는 시각은 지역 시간이 아니다
`epoch 초 % 86400` 은 UTC 기준 하루 안의 초다.
한국에서 보면 시가 9시간 어긋난다(원본에 근거 없음 — 추론).
`duration_since(UNIX_EPOCH).unwrap()` 은 시스템 시계가 epoch 보다 앞서 있으면 패닉한다.

### 6. 스팬 시작 줄에는 필드가 없다
`Span::new` 가 「시작」을 먼저 찍고, `.field` 는 그 뒤에 붙는다.
필드는 「완료」 줄에서만 보인다.

### 7. `tracing` 은 `log` 보다 구조화되어 있고 async 에 맞는다
원본 팁 그대로다.
`log` 의 한 줄은 문장 하나지만, `tracing` 은 스팬(작업 단위)과 필드로 맥락을 붙인다.
여러 요청이 번갈아 처리되면 줄만으로는 어느 요청의 줄인지 가리기 어렵고, 스팬 필드(`request_id` 같은)가 그 묶음을 준다(원본에 근거 없음 — 추론).

### 8. 프로덕션은 JSON 으로 내보내 수집한다
원본 팁: 프로덕션에서는 JSON 형식 출력과 함께 ELK 나 Datadog 으로 수집한다.
사람이 읽는 `HH:MM:SS [INFO ] …` 꼴은 기계가 필드별로 검색하기 어렵다.
원본 예의 `.json()` 이 그 자리다.

### 9. `Display` 의 공백은 일부러다
`"INFO "` · `"WARN "` 의 뒤 공백은 오타가 아니라 다섯 글자 정렬용이다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| derive 한 `PartialOrd` · `Ord` 는 `enum` 변형을 선언 차례로 비교한다 | 언어 · 표준 라이브러리 문서 |
| 지역 변수는 범위 끝에서 drop 되고, 안쪽 블록 변수가 먼저 drop 된다 | 언어 |
| `Instant` 로 잰 걸린 시간의 값 | 실행 환경마다 다르다 — 보장 없음 |
| `Duration` 의 `{:?}` 표기 꼴 | 표준 라이브러리의 `Debug` 구현 — `Debug` 꼴은 안정성을 약속하지 않는다(확인 필요) |
| `RUST_LOG` 를 읽어 모듈별 레벨을 정하는 동작 | `env_logger` 크레이트(언어 아님) |
| `tracing` 이 async 에 적합하다 | `tracing` 크레이트의 설계 · 원본 팁의 주장 |
| 「처음 일치한 필터로 끝낸다」 | 이 문서의 손수 만든 `Logger` 구현일 뿐이다 — 실제 `env_logger` 의 규칙과 같다고 보장하지 않는다 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 평소엔 조용히, 문제 모듈만 자세히 | `RUST_LOG=info,db=debug` 같은 모듈 필터 | 전역 `trace` (다른 모듈 줄에 파묻힌다) |
| 요청 하나의 흐름과 걸린 시간 추적 | 스팬(`tracing`, 이 문서의 `Span`) | 흩어진 `info` 줄만 |
| async 서버 | `tracing` + `#[tracing::instrument]` | 맥락 없는 줄 로그만 |
| 프로덕션 수집 · 검색 | JSON 출력 + ELK · Datadog | 사람이 읽는 텍스트만 |
| 정상 흐름 기록 / 실패 기록 | `Info` / `Warn` · `Error` | 모든 걸 `Error` 로 |
| 로거 원리 공부 | 이 문서의 손수 만든 `Logger` | 실제 서비스(실제 크레이트를 쓴다) |

## 핵심 문장

1. **레벨은 순서가 있는 등급이고, 로거는 문턱 이상만 찍는다** — `derive(PartialOrd)` 덕에 `>=` 한 번이면 된다.
2. **모듈 필터는 전역 문턱 위에 모듈별 예외를 얹는다** — `RUST_LOG=info,db=debug` 가 그 꼴이다.
3. **스팬은 RAII 로 작업 단위를 감싼다** — 만들 때 시작, 범위를 벗어날 때 `Drop` 이 완료와 걸린 시간을 남긴다.
4. **구조화된 필드는 기계를 위한 것이다** — `key=value` · JSON 으로 남겨야 수집 · 검색이 된다.
5. **레벨은 런타임에 환경변수로 고른다** — 다시 빌드하지 않는다.

## 관련 자료

- [testing](../09-testing/2-summary.md)
- [config](../11-config/2-summary.md)
- 원본: study-site 항목 데이터 `data/rust/practical.json` 의 `logging`

## 용어 풀이

- **로깅** — 프로그램이 하는 일을 시간 순서로 글로 남기는 일이다.
- **로그 레벨** — 메시지 중요도 등급(`Trace` < `Debug` < `Info` < `Warn` < `Error`)이다.
- **최소 레벨(문턱)** — 이보다 낮은 레벨의 메시지는 버리는 기준이다.
- **모듈 필터** — 특정 모듈 이름에만 따로 적용하는 문턱이다.
- **접두사 일치** — 문자열이 어떤 문자열로 시작하는지 보는 비교다.
- **`RUST_LOG`** — `env_logger` 가 읽는 로그 레벨 환경변수다.
- **`log`** — 로그 매크로(`log::info!` 등)를 주는 크레이트다.
- **`env_logger`** — `RUST_LOG` 를 읽어 로그를 찍어 주는 크레이트다.
- **`tracing`** — 스팬과 필드로 구조화된 기록을 남기는 크레이트다.
- **`tracing-subscriber`** — `tracing` 기록을 받아 어떤 꼴로 내보낼지 정하는 크레이트다.
- **구조화된 로깅** — 메시지를 `key=value` 필드와 함께 남기는 방식이다.
- **스팬(Span)** — 시작과 끝이 있는 작업 단위 기록이다.
- **필드** — 스팬이나 로그에 붙는 `key=value` 맥락 값이다.
- **RAII** — 범위를 벗어날 때 소멸자로 자동 정리하는 패턴이다.
- **`Drop`** — 값이 사라질 때 불리는 소멸자 트레이트다.
- **derive** — 트레이트 구현을 컴파일러가 자동으로 만들게 하는 속성이다.
- **빌더 패턴** — `self` 를 받아 고친 뒤 돌려주어 호출을 줄줄이 잇는 꼴이다.
- **`macro_rules!`** — 패턴에 맞춰 코드를 펼치는 선언형 매크로다.
- **UNIX epoch** — 1970-01-01 00:00:00 UTC, 시간 계산의 기준점이다.
- **`Instant`** — 걸린 시간을 재는 단조 시계 값이다.
- **ELK · Datadog** — 로그를 모아 검색 · 시각화하는 수집 시스템이다.

## 더 들어가면

- 실제 `env_logger` 는 여러 지시어가 한 모듈에 걸리면 넣은 차례가 아니라 가장 구체적인(긴) 이름을 고른다고 알려져 있다(확인 필요).
- 실제 `log` 의 `info!` 같은 매크로는 레벨을 먼저 확인한 뒤에야 메시지를 꾸민다고 알려져 있다 — 이 문서의 `log_msg!` 와 다른 점이다(확인 필요).
- `log` 는 파사드라서 `env_logger` 같은 백엔드를 초기화하지 않으면 아무것도 찍히지 않는다(확인 필요).
- `let _ = Span::new(..)` 처럼 이름 없이 `_` 에 받으면 값이 그 문장 끝에서 바로 drop 된다 — 스팬이 곧바로 끝나 버린다. `_span` 처럼 이름을 주어야 범위 끝까지 산다(확인 필요).
- `tracing::info!(path = %req.path(), …)` 의 `%` 는 `Display` 로, `?user` 의 `?` 는 `Debug` 로 필드를 기록하는 표기다(확인 필요).
- async 함수는 `.await` 마다 멈췄다 재개되므로, `tracing` 은 스팬에 들어가고 나오는 일을 재개 시점마다 다시 맞춰 준다(확인 필요).
