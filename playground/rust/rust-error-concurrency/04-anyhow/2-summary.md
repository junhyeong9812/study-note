# rust/rust-error-concurrency/04 — anyhow 크레이트 — 정리 (힌트)

> 출처 — study-site 항목 `rust/anyhow`(항목 데이터 `data/rust/error-concurrency.json`) · 정답 코드 study-practice `rust/rust-error-concurrency/reference/anyhow.rs`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다).

## 한눈에 — 쉽게 말하면

**anyhow 스타일 에러 처리는 「택배 상자에 쪽지를 덧붙이며 위로 올려 보내기」다.**
창고 맨 안쪽에서 문제가 생기면 그 문제를 적은 쪽지를 상자 하나에 넣는다.
상자는 어떤 크기의 쪽지든 다 들어가는 만능 상자다.
상자가 위층으로 올라갈 때마다 각 층 담당자가 「나는 이 일을 하다가 받았다」는 쪽지를 앞에 덧붙인다.
맨 위층(`main`)에서 상자를 열면 「무엇을 하다가 → 왜 → 어디서」가 한 줄로 읽힌다.
anyhow 스타일 에러 처리도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 만능 상자 | `Box<dyn Error>` (실제 anyhow 에서는 `anyhow::Error`) |
| 맨 안쪽 쪽지 | 원래 에러 (예: 숫자 파싱 실패 에러) |
| 각 층이 덧붙이는 쪽지 | `.context("…")` · `.with_context(|| …)` |
| 「더 볼 것도 없다, 바로 올려 보내」 | `bail!(…)` |
| 「이 조건이 아니면 바로 올려 보내」 | `ensure!(조건, …)` |
| 위층으로 올리는 손 | `?` 연산자 |

```text
parse()  ──실패──▶ [ParseIntError]
                     │ .context("나이 파싱 실패")
                     ▼
                 ["나이 파싱 실패: <원래 메시지>"]
                     │ ?  (한 층 위로)
                     ▼
              호출한 함수 ──▶ 또 .with_context(...) 로 앞에 덧붙임
                     │ ?
                     ▼
                  main 에서 match 로 꺼내 한 줄로 찍음
```

## 이 주제가 답하려는 질문

1. 서로 다른 종류의 에러(파싱 에러, 검증 실패, 값 없음)를 한 함수의 반환 타입 하나로 어떻게 묶나?
2. 에러가 위로 올라가며 「무엇을 하다가 생겼는지」를 어떻게 덧붙이나?
3. 「조건이 틀리면 바로 에러로 빠져나간다」를 어떻게 한 줄로 쓰나?
4. 이런 편한 에러 처리는 어디에 쓰고, 어디에는 쓰지 말아야 하나?

## 동작 방식

이 항목의 코드는 실제 `anyhow` 크레이트를 쓰지 않는다.
anyhow 의 핵심 패턴(`Result` 별칭, `Context` 트레이트, `bail!`, `ensure!`)을 표준 라이브러리만으로 흉내 낸다.
실제로 쓸 때는 `cargo add anyhow` 로 크레이트를 들인다.

> **크레이트(crate)** — Rust 의 컴파일 단위이자 꾸러미(라이브러리) 단위다.\
> 예: `anyhow` · `thiserror` 는 crates.io 에 올라 있는 크레이트다.

### (1) 하나의 에러 통 — `Result<T>` 별칭

**언제 쓰나** — 한 함수 안에서 여러 종류의 에러가 날 수 있고, 호출한 쪽이 에러의 종류를 갈라 처리할 필요가 없을 때 쓴다.

```text
type AnyError = Box<dyn Error>;
type Result<T> = std::result::Result<T, AnyError>;

fn parse_age(s) -> Result<u32>
        │
        ├─ ParseIntError        ─┐
        ├─ "나이는 0보다…" 문자열 ─┼─▶ 모두 Box<dyn Error> 한 통에 담김
        └─ "나이가 비현실…" 문자열 ─┘
```

- `Box<dyn Error>` 는 `Error` 트레이트를 구현한 어떤 값이든 힙에 담아 가리키는 타입이다.
- 그래서 반환 타입에 에러 종류를 하나하나 적지 않아도 된다.
- 별칭 `Result<T>` 는 실제 anyhow 의 `anyhow::Result<T> = Result<T, anyhow::Error>` 역할을 한다.
- 실제 anyhow 는 `Box<dyn Error + Send + Sync>` 를 감싸며 이 흉내보다 더 정교하다(원본 주석).

> **`dyn Error`** — 「`Error` 트레이트를 구현한 무언가」를 실행 중에 결정하는 트레이트 객체다.\
> 예: `Box<dyn Error>` 안에는 `ParseIntError` 도, 문자열에서 만든 에러도 들어간다.

> **동적 디스패치** — 어떤 구현의 메서드를 부를지 컴파일 때가 아니라 실행 중에 고르는 방식이다.\
> 예: `Box<dyn Error>` 의 `to_string()` 은 안에 든 실제 타입의 `Display` 를 실행 중에 찾아 부른다.

### (2) `?` 와 자동 변환

**언제 쓰나** — 에러면 지금 함수를 끝내고 그 에러를 호출한 쪽에 넘기고, 성공이면 값만 꺼내 계속 갈 때 쓴다.

```text
let users = vec![ create_user("Alice", "30")?, ... ];
                    │
          Ok(user) ─┼─▶ user 를 꺼내 vec 에 넣고 다음 줄로
          Err(e)   ─┴─▶ 즉시 return Err(e)  (필요하면 From 으로 변환)
```

- `?` 는 `Ok` 면 안의 값을 꺼내고, `Err` 면 그 자리에서 함수를 끝내며 에러를 돌려준다.
- 돌려줄 때 반환 타입의 에러로 `From` 변환을 거친다.
- 표준 라이브러리에는 `String` 과 `&str` 을 `Box<dyn Error>` 로 바꾸는 변환이 있다 — 그래서 코드 곳곳에서 `msg.into()` 만으로 문자열이 에러가 된다.

### (3) `context` — 에러 앞에 설명 붙이기

**언제 쓰나** — 아래에서 올라온 에러만으로는 「무엇을 하다가」가 안 보일 때 쓴다.
팁: `context()` 는 에러에 설명을 더해 디버깅을 쉽게 만든다.

```text
s.parse::<u32>()                       → Err(ParseIntError)
  .context("나이 파싱 실패")            → map_err(|e| format!("{}: {}", msg, e).into())
                                        → Err("나이 파싱 실패: <ParseIntError 메시지>")
  ?                                     → parse_age 를 끝내고 위로
```

- 원본의 `Context` 는 `Result` 와 `Option` 에 메서드를 덧붙이는 **확장 트레이트**다.
- `Result<T, E>` 용 구현은 `E: Error + 'static` 일 때만 성립한다.
- 안에서는 `map_err` 로 에러만 바꾼다 — `"{메시지}: {원래 에러}"` 꼴의 문자열을 만들어 `Box<dyn Error>` 로 넣는다.
- `Ok` 이면 아무 일도 하지 않고 값을 그대로 둔다.
- 결과적으로 메시지는 **바깥 설명이 앞, 원래 원인이 뒤**로 쌓인다.

> **확장 트레이트** — 남의 타입(여기서는 표준의 `Result` · `Option`)에 새 메서드를 붙이려고 만드는 트레이트다.\
> 예: `trait Context<T>` 를 `Option<T>` 에 구현하면 `items.get(5).context("…")` 가 된다.

### (4) `with_context` — 필요할 때만 만드는 설명

**언제 쓰나** — 설명 문자열을 만드는 데 `format!` 같은 비용이 들거나, 변수(사용자 이름 등)를 섞어야 할 때 쓴다.

```text
parse_age(age_str)
  .with_context(|| format!("'{}' 사용자 생성 중", name))
        │
  Ok  ──┼─▶ 클로저를 부르지 않음 (format! 비용 없음)
  Err ──┴─▶ 클로저를 불러 "'Bob' 사용자 생성 중" 을 만들고
            "'Bob' 사용자 생성 중: <아래에서 올라온 메시지>" 로 감쌈
```

- 인자가 문자열이 아니라 `FnOnce() -> String` 클로저다.
- 클로저는 `map_err` 안, 즉 에러일 때만 불린다 — 원본 주석의 「에러 발생 시에만 호출되어 비용 절약」이 이 뜻이다.
- 이것을 **지연 평가(lazy)** 라고 한다.

> **`FnOnce`** — 한 번만 불릴 수 있는 클로저를 받는 트레이트다.\
> 예: `|| format!("'{}' 사용자 생성 중", name)` 은 `FnOnce() -> String` 을 만족한다.

### (5) `Option` 에 `context` — `None` 을 에러로

**언제 쓰나** — 「찾았나 / 없나」를 돌려주는 `Option` 을 `?` 로 흘려보내고 싶을 때 쓴다.

```text
users.iter().find(|u| u.name == name)   → Some(&User) 또는 None
  .context("사용자를 찾을 수 없음")       → ok_or_else(|| msg.into())
                                          Some(v) → Ok(v)
                                          None    → Err("사용자를 찾을 수 없음")
```

- `Option` 에는 감쌀 원래 에러가 없다 — 그래서 메시지 자체가 에러가 된다.
- 안에서는 `ok_or_else` 로 `Option` 을 `Result` 로 바꾼다.
- `items.get(5)` 처럼 범위를 벗어난 인덱스도 `None` 이므로 같은 방법으로 `Err` 가 된다.

### (6) `bail!` — 즉시 에러 반환

**언제 쓰나** — 「여기서 끝, 이 메시지로 실패」를 한 줄로 쓸 때 쓴다.
팁: `bail!` 은 `Err(anyhow!(...))` 를 돌려주는 것의 축약이다.

```text
bail!("이름이 너무 깁니다: {} 글자", n);
        ↓ 매크로 펼침
return Err(format!("이름이 너무 깁니다: {} 글자", n).into());
```

- `format!` 과 같은 인자를 받는다(`$($arg:tt)*` 로 토큰을 그대로 넘긴다).
- 펼친 결과에 `return` 이 들어 있다 — 그래서 **매크로를 쓴 그 함수**가 끝난다.
- 함수는 자기를 부른 함수를 대신 끝낼 수 없지만, 매크로는 그 자리에 `return` 문을 써 넣으므로 할 수 있다.

> **선언적 매크로(`macro_rules!`)** — 패턴에 맞는 토큰을 받아 코드 조각으로 펼치는 매크로다.\
> 예: `bail!(...)` 은 컴파일 전에 `return Err(...)` 로 바뀐다.

### (7) `ensure!` — 조건 + `bail!`

**언제 쓰나** — 입력 검증처럼 「이 조건이 아니면 실패」를 쓸 때 쓴다.
팁: `ensure!` 는 조건 검사와 `bail!` 을 합친 축약이다.

```text
ensure!(age < 200, "나이가 비현실적입니다: {}", age);
        ↓ 매크로 펼침
if !(age < 200) {
    return Err(format!("나이가 비현실적입니다: {}", age).into());
}
```

- `assert!` 와 닮았지만, 거짓일 때 패닉하지 않고 `Err` 를 돌려준다.
- 그래서 프로그램이 멈추지 않고 호출한 쪽이 실패를 처리할 수 있다.
- 조건은 `$cond:expr` 로 받는다 — `expr` 조각은 한 덩어리 식으로 다뤄지므로 `!$cond` 는 `!(age < 200)` 처럼 조건 전체를 뒤집는다.
- `ensure!` 는 위에서 아래로 차례대로 검사하고, 처음 거짓인 곳에서 끝난다.

> **패닉(panic)** — 복구하지 않고 현재 스레드를 멈추는 Rust 의 비상 정지다.\
> 예: `assert!(false)` 는 패닉한다.

### (8) 메시지가 쌓이는 모양 — `create_user` 의 흐름

**언제 쓰나** — 여러 층의 함수를 거치며 원인과 맥락을 한 줄로 모으고 싶을 때다.

```text
create_user("Alice", "300")
  ensure!(!name.is_empty())        통과
  ensure!(name.len() <= 50)        통과
  parse_age("300")
    parse → 300                    성공
    ensure!(age > 0)               통과
    ensure!(age < 200)             거짓 → Err("나이가 비현실적입니다: 300")
  .with_context(|| "'Alice' 사용자 생성 중")
                                   → Err("'Alice' 사용자 생성 중: 나이가 비현실적입니다: 300")
main 의 match → Err(e) 갈래 → "  실패: " 뒤에 e 를 찍음
```

- 안쪽 원인이 문자열 뒤쪽에, 바깥 맥락이 앞쪽에 붙는다.
- `create_user("", "30")` 은 첫 `ensure!` 에서 바로 끝나므로 `parse_age` 까지 가지 않는다.
- `process_users` 는 `?` 로 여러 단계를 잇고, `find_user(&users, "Charlie")` 의 `Err` 는 `?` 없이 `_not_found` 에 받아 버린다 — 이 실패는 흐름을 멈추지 않는다.
- 단, 이 흐름은 `parse_age` 결과(에러 타입이 `Box<dyn Error>`)에 `with_context` 가 붙는다는 전제 위에 있다 — 그 전제가 의심스러운 까닭은 「어디서 틀리나 4」에 있다.

## 문법 — 형태와 규칙

```rust
use std::error::Error;

type Result<T> = std::result::Result<T, Box<dyn Error>>;

fn check_port(s: &str) -> Result<u16> {
    let port: u16 = s.parse()
        .map_err(|e| format!("포트 파싱 실패: {}", e))?; // String → Box<dyn Error>
    if port == 0 {
        return Err("포트는 0일 수 없다".into());       // bail! 이 펼쳐진 꼴
    }
    Ok(port)
}
```

- 별칭: `type Result<T> = std::result::Result<T, Box<dyn Error>>;` — 반환 타입을 짧게 쓴다.
- 확장 트레이트: `trait Context<T> { fn context(self, msg: &str) -> Result<T>; fn with_context<F: FnOnce() -> String>(self, f: F) -> Result<T>; }`.
- `Result<T, E>` 용 구현은 `E: Error + 'static` 조건이 붙는다.
- `Option<T>` 용 구현은 조건이 없다 — `None` 을 메시지 에러로 바꿀 뿐이다.
- `context(self, …)` 는 `self` 를 값으로 받아 소비한다 — 원래 `Result` · `Option` 은 그 뒤 쓸 수 없다.
- `bail!(형식, 인자…)` — `format!` 과 같은 인자, 펼치면 `return Err(…into())`.
- `ensure!(조건, 형식, 인자…)` — 조건이 거짓이면 `bail!`.
- `bail!` · `ensure!` 는 반환 타입이 `Result` 인 함수 안에서만 쓸 수 있다.
- 실제 anyhow 에서 대응하는 것: `anyhow::Result<T>` · `anyhow::Context` · `anyhow::bail!` · `anyhow::ensure!`.
- 팁: 실제 프로젝트에서는 `main` 이 `anyhow::Result` 를 돌려주게 하면 모든 에러가 깔끔하게 처리된다.

## 어디서 틀리나

### 1. anyhow 를 라이브러리의 공개 API 에 쓴다
팁: anyhow 는 애플리케이션 코드에, thiserror 는 라이브러리 코드에 맞는다.
`anyhow::Error` 는 모든 `Error` 를 감싸므로 호출한 쪽이 에러 종류로 **패턴 매칭할 수 없다**.
라이브러리 사용자는 「파일이 없을 때만 다르게 처리」 같은 갈래를 원한다 — 그러려면 종류가 드러나는 에러 타입(thiserror 로 만든 `enum`)이 필요하다.
원래 타입을 꼭 꺼내야 하면 `downcast_ref::<T>()` 로 되돌릴 수 있다(원본 요약).

### 2. `context` 와 `with_context` 를 아무렇게나 고른다
고정 문자열이면 `context` 로 충분하다.
`format!` 으로 변수를 섞는 설명이면 `with_context(|| format!(…))` 를 쓴다 — 성공할 때는 문자열을 만들지 않는다.
`context(format!(…))` 처럼 쓰면 성공해도 매번 문자열을 만든다.

### 3. `ensure!` 를 `assert!` 처럼 여긴다
`assert!` 는 거짓이면 패닉한다.
`ensure!` 는 거짓이면 `Err` 를 돌려준다.
사용자 입력처럼 「틀릴 수 있는 것」은 `ensure!` 로, 「틀리면 프로그램 버그인 것」은 `assert!` 로 나눈다.

### 4. `Box<dyn Error>` 에 다시 `with_context` 를 붙인다
원본 코드는 `parse_age(age_str).with_context(…)` 처럼, 에러 타입이 이미 `Box<dyn Error>` 인 결과에 `with_context` 를 붙인다.
그런데 원본의 `Result` 용 구현은 `E: Error + 'static` 을 요구한다.
표준 라이브러리에서 `Box<T>` 의 `Error` 구현은 크기가 정해진 `T` 에만 있어서, `Box<dyn Error>` 자체는 `Error` 를 구현하지 않는 것으로 안다 — 그렇다면 이 줄은 컴파일되지 않는다(확인 필요).
같은 일을 하려면 `parse_age(age_str).map_err(|e| format!("'{}' 사용자 생성 중: {}", name, e))?` 처럼 직접 문자열로 바꾸는 방법이 있다(확인 필요).
실제 anyhow 는 이 경우(이미 `anyhow::Error` 인 결과에 context 를 더 붙이기)를 따로 다룬다(확인 필요).

### 5. 「글자 수」라고 쓰고 바이트 수를 센다
`ensure!(name.len() <= 50, "이름이 너무 깁니다: {} 글자", name.len())` 의 `len()` 은 UTF-8 **바이트** 수다.
한글 한 글자는 UTF-8 로 3바이트이므로, 한글 이름은 17글자만 넘어도(51바이트) 걸린다.
메시지의 「글자」는 실제로는 바이트 수다 — 글자 수가 필요하면 `name.chars().count()` 를 쓴다.

### 6. `?` 없이 받은 `Err` 는 조용히 버려진다
`let _not_found = find_user(&users, "Charlie");` 는 `Err` 를 변수에 받기만 하고 아무것도 하지 않는다.
이름을 `_` 로 시작하면 쓰지 않는다는 경고도 나지 않는다.
데모에서는 의도한 것이지만, 실제 코드에서는 실패를 놓치는 흔한 길이다.

### 7. 음수 나이는 `ensure!(age > 0)` 에 걸리지 않는다
나이는 `u32` 로 파싱한다.
`"-5"` 는 `u32` 로 파싱하는 단계에서 이미 실패하므로 `"나이 파싱 실패: …"` 가 된다.
`ensure!(age > 0, …)` 에 걸리는 것은 `"0"` 하나뿐이다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `?` 가 `Err` 면 즉시 반환하고 `From` 으로 변환한다 | 언어(`?` 연산자의 정의) |
| `String` · `&str` 이 `.into()` 로 `Box<dyn Error>` 가 된다 | 표준 라이브러리의 `From` 구현 |
| `macro_rules!` 의 `expr` 조각이 한 덩어리 식으로 펼쳐진다 | 언어(매크로 규칙) |
| `str::len()` 이 바이트 수를 센다 | 표준 라이브러리 문서 |
| `ParseIntError` 의 메시지 문구 | 표준 라이브러리 구현 — 문구 자체는 바뀔 수 있다(확인 필요) |
| 문자열로 만든 `Box<dyn Error>` 를 `{:?}` 로 찍은 모양 | 표준 라이브러리 구현(확인 필요) |
| `anyhow::Error` 가 `Box<dyn Error + Send + Sync>` 를 감싼다 · `downcast_ref` 로 복원 | anyhow 크레이트 — 언어 · 표준이 아니다 |
| anyhow 는 앱용, thiserror 는 라이브러리용 | 생태계의 관례(원본 팁) — 규칙이 아니다 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| CLI · 서버 같은 애플리케이션에서 에러를 위로 모아 찍기 | `anyhow::Result` + `context` | 함수마다 전용 에러 `enum` |
| 남이 쓸 라이브러리의 공개 함수 | thiserror 로 만든 에러 타입 | `anyhow::Error` |
| 입력 검증 실패 | `ensure!` · `bail!` | `assert!` · `panic!` |
| 설명에 변수를 섞기 | `with_context(|| format!(…))` | `context(&format!(…))` |
| `Option` 의 `None` 을 실패로 올리기 | `.context("…")?` | `unwrap()` |
| 호출한 쪽이 에러 종류마다 다르게 처리해야 함 | 구체적인 에러 타입 | 모든 것을 하나로 감싸기 |

## 핵심 문장

1. **anyhow 스타일은 모든 에러를 한 통(`Box<dyn Error>` / `anyhow::Error`)에 담는다** — 대신 종류로 패턴 매칭하기 어렵다.
2. **`context` 는 에러 앞에 「무엇을 하다가」를 붙인다** — 메시지는 바깥 맥락이 앞, 원인이 뒤로 쌓인다.
3. **`with_context` 는 클로저를 받아 에러일 때만 설명을 만든다.**
4. **`bail!` 은 `return Err(…)`, `ensure!` 는 `if !조건 { bail! }`** — 매크로라서 쓴 함수를 끝낼 수 있다.
5. **anyhow 는 애플리케이션용, thiserror 는 라이브러리용이다.**

## 관련 자료

- `thiserror` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `error-handling` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `result-option` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/rust/error-concurrency.json` 의 `anyhow`

## 용어 풀이

- **anyhow** — 애플리케이션의 에러 처리를 편하게 해 주는 크레이트다.
- **thiserror** — 라이브러리용으로 종류가 드러나는 에러 타입을 쉽게 만들게 해 주는 크레이트다.
- **크레이트** — Rust 의 꾸러미 · 컴파일 단위다.
- **`Error` 트레이트** — 표준 에러들의 바탕이 되는 트레이트로, `Display` 와 `Debug` 를 갖춘다.
- **`Box<dyn Error>`** — 어떤 에러든 담는 힙 상자다.
- **트레이트 객체(`dyn`)** — 구체 타입을 실행 중에 정하는 값이다.
- **동적 디스패치** — 실행 중에 어떤 구현을 부를지 고르는 방식이다.
- **타입 별칭(`type`)** — 긴 타입에 짧은 이름을 붙이는 문법이다.
- **`?` 연산자** — `Err` 면 즉시 반환, `Ok` 면 값을 꺼내는 연산자다.
- **`map_err`** — `Result` 의 에러 쪽만 바꾸는 메서드다.
- **`ok_or_else`** — `Option` 을 `Result` 로 바꾸며, `None` 일 때만 에러를 만드는 메서드다.
- **확장 트레이트** — 남의 타입에 메서드를 덧붙이는 트레이트다.
- **`FnOnce`** — 한 번 불릴 수 있는 클로저의 트레이트다.
- **지연 평가(lazy)** — 값이 정말 필요할 때까지 계산을 미루는 것이다.
- **선언적 매크로(`macro_rules!`)** — 패턴에 맞춰 코드로 펼쳐지는 매크로다.
- **패닉** — 복구하지 않고 스레드를 멈추는 비상 정지다.
- **`downcast_ref::<T>()`** — 감싼 에러가 `T` 타입이면 그 참조를 꺼내는 메서드다.
- **`ParseIntError`** — 문자열을 정수로 바꾸다 실패했을 때의 표준 에러 타입이다.

## 더 들어가면

- 표준의 `main` 은 `Result<(), E>`(`E: Debug`)를 돌려줄 수 있고, `Err` 면 에러를 `Debug` 형식으로 찍고 실패 종료 코드로 끝난다(확인 필요).
- `anyhow::Error` 의 `Debug` 출력은 원인 사슬(`Caused by:`)을 줄마다 보여 주는 꼴이라, `main` 이 `anyhow::Result` 를 돌려주면 맥락이 잘 보인다(확인 필요).
- 실제 anyhow 는 context 를 붙일 때 원래 에러를 문자열로 녹이지 않고 **원인 사슬**로 보존한다 — 그래서 context 를 붙인 뒤에도 `downcast_ref` 로 원래 타입을 찾을 수 있다(확인 필요). 이 항목의 흉내는 `format!` 으로 문자열에 녹이므로 원래 타입이 사라진다.
- `{:#}` 형식으로 `anyhow::Error` 를 찍으면 사슬 전체가 「: 」로 이어진 한 줄이 된다(확인 필요).
- `anyhow!` 매크로는 형식 문자열로 `anyhow::Error` 를 만든다 — `bail!` 은 그것을 `return Err(…)` 로 감싼 것이다(확인 필요).
- `Send + Sync` 가 붙어 있으면 에러를 스레드 사이로 넘길 수 있다 — 이 흉내의 `Box<dyn Error>` 는 그 조건이 없다(확인 필요).
