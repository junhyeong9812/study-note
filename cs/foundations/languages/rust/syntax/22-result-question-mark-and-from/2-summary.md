# rust/syntax/22 — `Result` 와 `?`·`From` 변환 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [The Rust Reference — The question mark operator](https://doc.rust-lang.org/reference/expressions/operator-expr.html#the-question-mark-operator) ·
> [std — `enum Result`](https://doc.rust-lang.org/std/result/enum.Result.html) ·
> [std — `trait From`](https://doc.rust-lang.org/std/convert/trait.From.html) ·
> [std — `trait Termination`](https://doc.rust-lang.org/std/process/trait.Termination.html).
> ★ `rustc --explain E0277` · `E0271` 은 **확인용으로만 열었고 본문에 옮기지 않았다.**
> **실행 검증** — 이 문서의 모든 출력·에러는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 받은 것이다.\
> ★★ **`rustc ex.rs` 만 쓰면 에디션 2015 다** — 에디션을 안 밝힌 결과는 다른 언어를 컴파일한 것과 같다.\
> ★★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.
> **버전** — `Result` 와 `?` 는 **1.0.0**(`?` 는 1.13.0 부터의 표기이고 그 전에는 `try!` 매크로였다).\
> **`main` 이 `Result` 를 반환할 수 있는 것은 1.26.0** 부터다. `?` 가 `Option` 에도 되는 것은 1.22.0 부터다. **전부 에디션과 무관하다.**
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | 패닉 첫 줄 `thread 'main' (…)` 괄호 안의 OS 스레드 id | 이 주제에는 패닉 블록이 없지만 규칙은 같다 |
| **흔들린다** | `0x…` 주소 | 실행마다 다르다 |
| 안 흔들린다 | 에러 번호·제목·`= note:`·`help:` 줄·`파일:줄:칸` | 같은 rustc 판에서 고정이다 |
| 안 흔들린다 | **종료 코드 0 · 1** | `main` 이 `Err` 를 돌려주면 **1** 이다(고정) |
| 안 흔들린다 | `Error: ParseIntError { kind: InvalidDigit }` 의 **형식** | 런타임이 `{:?}` 로 찍는다 — Debug 구현이 바뀌지 않는 한 고정 |
| 안 흔들린다 | `diff` 블록의 줄 번호·기호 | 같은 두 파일이면 고정이다 |

## 한눈에 — 쉽게 말하면

**`?` 는 「성공값을 꺼내고, 실패면 지금 여기서 반환한다」 한 글자다 — 그리고 반환하면서 오류 타입을 갈아 끼운다.**

두 번째 절반이 이 주제의 전부다. 많은 사람이 `?` 를 「조기 반환 설탕」으로만 알고 쓰다가,
**오류 타입이 다른 순간** 컴파일러에게 막히고 왜 막혔는지 모른다.

| 비유 | 실체 |
|---|---|
| 「**되면 통과, 안 되면 여기서 되돌려보냄**」 | **`?`** — 조기 반환 |
| ★ 되돌려보낼 때 **양식을 갈아 끼운다** | ★★ **`From::from`** 이 자동으로 낀다 — 이 주제의 핵심 |
| 갈아 끼울 **양식이 없으면 반려** | **E0277** — `` `?` couldn't convert the error to … `` |
| 양식을 **내가 만들어 주면 통과** | `impl From<A> for B` 한 덩어리 |
| 「없음」 봉투를 **영수증**으로 바꾼다 | `ok_or`·`ok_or_else` — [**21번 주제**](../21-option-and-combinators/)에서 이어진다 |
| 아무 양식이나 받는 **만능 봉투** | `Box<dyn Error>` — [**24번 주제**](../24-error-type-design/)가 정본 |

- ★★★ **`?` 는 두 가지를 동시에 한다** — ① 성공이면 값을 꺼내 식의 값으로 쓰고 ② 실패면 **`From::from(e)` 을 거쳐** 반환한다.
- ★★ **증거는 에러 메시지에 그대로 적혀 있다** —
  `` = note: the question mark operation (`?`) implicitly performs a conversion on the error value using the `From` trait ``.
  컴파일러가 **자기 입으로** 말한다((3)).
- ★ **`main` 에서도 `?` 가 된다** — 단 `main` 의 반환 타입이 `Result` 라야 한다. 그때 종료 코드는 **1** 이고 **`Debug` 로 찍힌다**((5)).

```text
   ? 한 글자가 펼쳐지는 모양

     let n = expr?;
        │
        ▼ 컴파일러가 이렇게 바꾼다(개념적으로)
     let n = match expr {
         Ok(v)  => v,                      ← 성공: 값이 식의 자리에 남는다
         Err(e) => return Err(From::from(e)),   ← ★ 실패: 변환하고 즉시 반환
     };


   같은 실패가 세 세계를 건너가는 길

     Option<T>            Result<T, A>            Result<T, B>
        │                     │                        │
        │ ok_or(e)            │ ?  (From<A> for B)     │ ?  (From<B> for Box<dyn Error>)
        ▼                     ▼                        ▼
     Result<T, E> ────────▶ 호출자 ────────────────▶ main → 종료 코드 1

     ★ 한 칸을 건널 때마다 「그 변환 impl 이 있는가」를 컴파일러가 묻는다.
```

> **`Result<T, E>`** — 성공이면 `Ok(T)`, 실패면 `Err(E)` 인 표준 열거형.\
> `Option` 과 달리 **실패에 이유(`E`)를 담는다.**

> **`?` (물음표 연산자)** — 성공값을 꺼내거나, 실패면 `From` 변환을 거쳐 함수에서 즉시 반환한다.\
> 1.13.0 이전에는 같은 일을 `try!` 매크로가 했다.

> **`From` 트레이트** — 「A 로부터 B 를 만든다」는 변환 계약. `impl From<A> for B` 를 쓰면\
> `B::from(a)` 와 `a.into()` 가 **둘 다** 생긴다(변환 트레이트의 정본은 [목록의 **29번 주제**](../29-conversion-traits-from-into-tryfrom-asref-borrow/)).

> **오류 변환(error conversion)** — 아래 층의 오류 타입을 내 층의 오류 타입으로 감싸거나 바꾸는 것.\
> `?` 가 자동으로 하고, 손으로 하면 `map_err` 다.

## 이 주제가 답하려는 질문

1. ★★ **`?` 는 정확히 무엇으로 펼쳐지나** — 특히 **오류 타입이 다를 때 무엇이 끼어드나**((3)·(4)).
2. **`?` 가 안 먹는 자리는 어디인가** — `main` 이 `()` 일 때, `Option` 과 섞였을 때((5)·(6)).
3. **변환을 손으로 하면 어떤 코드가 되나** — 그래서 `?` 가 무엇을 줄여 주나((4)·(7)).

★ [**20번 주제**](../20-if-let-while-let-let-else-and-let-chains/)와 겹치는 것처럼 보이는 지점이 있다 — **경계를 한 줄로 선언한다.**

> **경계 선언** — `let else` 는 **「패턴이 안 맞으면 내가 적은 블록으로 나간다」**(문법 · 20번이 정본)이고,\
> `?` 는 **「`Result`/`Option` 이 실패면 그 실패값을 변환해 반환한다」**(연산자 · 여기가 정본)다.\
> ★ 겹치는 것은 **조기 반환이라는 모양**뿐이고, 갈리는 것은 **누가 반환값을 만드나**다 —\
> `let else` 는 **내가** 쓰고, `?` 는 **컴파일러가** `From::from` 을 끼워 만든다.

## 동작 방식

### (0) 이 주제가 쓰는 네 창

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| **되는 판을 먼저 돌리기** | `?` 가 성공·실패를 어떻게 옮기나 | 기본 창 |
| ★★★ **변환 impl 을 빼고 던지기** | `?` 안에 **`From::from` 이 끼어 있다**는 증거 — 에러 전문이 그것을 말한다 | ★ 이 주제의 고유 창 |
| ★★ **`diff` 로 두 판의 차이를 기계가 찍게 하기** | 「`impl From` **만** 더하면 통과한다」를 **눈이 아니라 도구로** 보이는 것 | ★ 이 주제의 고유 창 |
| ★ **손으로 펼친 판과 문자열 비교** | `?` 가 펼쳐진 모양이 정말 그것인가 — **출력이 같은지로 확인** | ★ 이 주제의 고유 창 |

★★★ 둘째 창이 본체다. **「`?` 가 `From` 을 부른다」는 말을 문서에서 읽어 옮기지 않고,
그 impl 을 지운 채 던져 컴파일러가 스스로 그 사실을 말하게 한다.**

### (1) `Result` 도 그냥 열거형이다

[**17번 주제**](../17-enums-and-data-carrying-variants/) (6)에서 확인한 대로 `Result` 는 std 에 적힌 열거형이다.

```text
   enum Result<T, E> { Ok(T), Err(E) }        ← std 의 선언(개념적으로 이 한 줄)
   enum Option<T>    { Some(T), None }        ← 21번에서 쓴 것

   갈리는 점 하나 — Err 쪽에 ★ 값이 들어간다. 그래서 「왜 실패했나」를 담는다.
```

- `match`·`if let`·`?` 가 전부 그 위에 얹힌 것이다. **문법이 아니라 타입이다.**
- ★ 「봉투가 몇 바이트인가」·「니치」는 **17번이 정본**이다. 여기서 다시 재지 않는다.

### (2) `?` 가 하는 첫 번째 일 — 조기 반환

**언제 쓰나** — 실패를 **그대로 호출자에게 올릴 때**. 오류 타입이 같으면 이게 전부다.

```text
===== 소스: ex.rs =====
// ex.rs
// ? 는 「성공값을 꺼내거나, 실패면 지금 반환」이다
fn parse_port(raw: &str) -> Result<u16, std::num::ParseIntError> {
    let n: u16 = raw.parse()?;
    Ok(n)
}

fn main() {
    println!("{:?}", parse_port("8080"));
    println!("{:?}", parse_port("팔공팔공"));
    println!("{:?}", parse_port("99999"));
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
Ok(8080)
Err(ParseIntError { kind: InvalidDigit })
Err(ParseIntError { kind: PosOverflow })
(종료 코드 0)
```

- `parse_port("8080")` 은 `Ok(8080)` — `?` 가 값을 꺼내 `n` 에 넣고 다음 줄로 간다.
- 나머지 둘은 `Err(…)` — `?` 가 **그 자리에서 함수를 끝낸다.**
- ★ `"99999"` 가 `PosOverflow` 인 것에 주의 — `u16` 의 최댓값은 65535 다. **「숫자가 아님」과 「범위를 넘음」이 다른 종류**로 온다.
- 여기서는 함수의 오류 타입과 `parse` 의 오류 타입이 **둘 다 `ParseIntError`** 라 변환이 필요 없었다.

### (3) ★★★ `?` 가 하는 두 번째 일 — `From::from` 이 낀다

**언제 쓰나** — 아래 층의 오류를 **내 오류 타입으로 감싸** 올릴 때. 실무의 `?` 는 거의 전부 이 경우다.

**전** — 오류 타입이 둘(`ParseIntError` · `ConfigError`)인데 변환 impl 이 없다.

```text
===== 소스: ex.rs =====
// ex.rs
// ? 는 오류를 그대로 옮기지 않는다 — 변환 impl 이 없으면
use std::num::ParseIntError;

#[derive(Debug)]
enum ConfigError {
    Missing,
    BadNumber(ParseIntError),
}

fn port(line: &str) -> Result<u16, ConfigError> {
    let value = line.strip_prefix("port=").ok_or(ConfigError::Missing)?;
    let n = value.parse::<u16>()?;
    Ok(n)
}

fn main() {
    println!("{:?}", port("port=8080"));
    println!("{:?}", port("port=팔공"));
    println!("{:?}", port("host=localhost"));

    // 감싼 원인을 꺼내 읽을 수 있다 — 이것이 Box<dyn Error> 와 갈리는 지점이다
    if let Err(ConfigError::BadNumber(cause)) = port("port=팔공") {
        println!("감싼 원인 {}", cause);
    }
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0277]: `?` couldn't convert the error to `ConfigError`
  --> ex.rs:13:33
   |
11 | fn port(line: &str) -> Result<u16, ConfigError> {
   |                        ------------------------ expected `ConfigError` because of this
12 |     let value = line.strip_prefix("port=").ok_or(ConfigError::Missing)?;
13 |     let n = value.parse::<u16>()?;
   |                   --------------^ the trait `From<ParseIntError>` is not implemented for `ConfigError`
   |                   |
   |                   this can't be annotated with `?` because it has type `Result<_, ParseIntError>`
   |
note: `ConfigError` needs to implement `From<ParseIntError>`
  --> ex.rs:6:1
   |
 6 | enum ConfigError {
   | ^^^^^^^^^^^^^^^^
   = note: the question mark operation (`?`) implicitly performs a conversion on the error value using the `From` trait

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0277`.
(종료 코드 1)
```

- ★★★ **마지막 `= note:` 한 줄이 이 주제의 증거다** —
  `` the question mark operation (`?`) implicitly performs a conversion on the error value using the `From` trait ``.
  **`?` 안에 `From` 이 끼어 있다는 것을 컴파일러가 자기 입으로 말한다.**
- ★★ 그 위의 `note:` 는 **무엇을 만들어야 하는지까지** 찍어 준다 — `` `ConfigError` needs to implement `From<ParseIntError>` ``.
- `` this can't be annotated with `?` because it has type `Result<_, ParseIntError>` `` 줄이
  **어느 타입이 들어왔는지**를, `` expected `ConfigError` because of this `` 줄이 **어느 타입이 필요한지**를 말한다.
- ★ 같은 파일의 **첫 번째 `?`**(`ok_or(ConfigError::Missing)?`)는 **아무 말도 안 나왔다.**
  이미 `ConfigError` 라 변환이 `From<ConfigError> for ConfigError`(std 의 반사 impl)로 끝나기 때문이다.

**고치는 법 — `impl From` 한 덩어리.** 두 파일의 차이를 기계가 찍게 한 것이 아래다.

```text
===== diff b22-02.rs b22-03.rs =====
2c2
< // ? 는 오류를 그대로 옮기지 않는다 — 변환 impl 이 없으면
---
> // From 을 구현하면 같은 ? 가 통과한다 — 한 줄도 안 고쳤다
8a9,14
> }
> 
> impl From<ParseIntError> for ConfigError {
>     fn from(e: ParseIntError) -> Self {
>         ConfigError::BadNumber(e)
>     }
(종료 코드 1)
```

**후** — 그 impl 만 더한 판.

```text
===== 소스: ex.rs =====
// ex.rs
// From 을 구현하면 같은 ? 가 통과한다 — 한 줄도 안 고쳤다
use std::num::ParseIntError;

#[derive(Debug)]
enum ConfigError {
    Missing,
    BadNumber(ParseIntError),
}

impl From<ParseIntError> for ConfigError {
    fn from(e: ParseIntError) -> Self {
        ConfigError::BadNumber(e)
    }
}

fn port(line: &str) -> Result<u16, ConfigError> {
    let value = line.strip_prefix("port=").ok_or(ConfigError::Missing)?;
    let n = value.parse::<u16>()?;
    Ok(n)
}

fn main() {
    println!("{:?}", port("port=8080"));
    println!("{:?}", port("port=팔공"));
    println!("{:?}", port("host=localhost"));

    // 감싼 원인을 꺼내 읽을 수 있다 — 이것이 Box<dyn Error> 와 갈리는 지점이다
    if let Err(ConfigError::BadNumber(cause)) = port("port=팔공") {
        println!("감싼 원인 {}", cause);
    }
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
Ok(8080)
Err(BadNumber(ParseIntError { kind: InvalidDigit }))
Err(Missing)
감싼 원인 invalid digit found in string
(종료 코드 0)
```

- ★★ **본문 코드는 한 글자도 안 바뀌었다.** `diff` 가 주석 한 줄과 `impl From` 여섯 줄만 보여 준다.
  `?` 는 그대로인데 통과한다 — **`?` 가 찾던 것이 정확히 그 impl** 이었다는 뜻이다.
- 출력의 `Err(BadNumber(ParseIntError { kind: InvalidDigit }))` 가 **변환이 실제로 일어난 자국**이다.
  `ParseIntError` 가 `ConfigError::BadNumber` 안에 들어가 있다.
- ★ 마지막 줄 — 감싼 원인을 `if let Err(ConfigError::BadNumber(cause))` 로 **꺼내 읽을 수 있다.**
  이것이 `Box<dyn Error>` 와 갈리는 지점이고, 그 비교는 [**24번 주제**](../24-error-type-design/)가 정본이다.

**같은 결함인데 번호가 다른 자리** — 오류 타입을 **추론에 맡기면** 진단이 다르게 나온다.

```text
===== 소스: ex.rs =====
// ex.rs
// 같은 결함인데 번호가 다르다 — 오류 타입을 추론에 맡긴 판
use std::num::ParseIntError;

#[derive(Debug)]
enum ConfigError {
    Missing,
    BadNumber(ParseIntError),
}

fn port(line: &str) -> Result<u16, ConfigError> {
    let value = line.strip_prefix("port=").ok_or(ConfigError::Missing)?;
    let n: u16 = value.parse()?;
    Ok(n)
}

fn main() {
    println!("{:?}", port("port=8080"));
    println!("{:?}", port("port=팔공"));
    println!("{:?}", port("host=localhost"));

    // 감싼 원인을 꺼내 읽을 수 있다 — 이것이 Box<dyn Error> 와 갈리는 지점이다
    if let Err(ConfigError::BadNumber(cause)) = port("port=팔공") {
        println!("감싼 원인 {}", cause);
    }
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0271]: type mismatch resolving `<u16 as FromStr>::Err == ConfigError`
  --> ex.rs:13:24
   |
13 |     let n: u16 = value.parse()?;
   |                        ^^^^^ expected `ConfigError`, found `ParseIntError`

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0271`.
(종료 코드 1)
```

- ★★ **E0271 이다.** `let n: u16 = value.parse()?` 는 `parse` 의 타입 파라미터가 **반환 타입 쪽에서 역으로 정해지는** 꼴이라,
  컴파일러가 **`FromStr::Err` 연관 타입이 `ConfigError` 여야 한다**고 읽고 「타입이 안 맞는다」로 보고한다.
- ★★★ **같은 결함(「변환 impl 이 없다」)인데 진단이 완전히 다르다.** E0277 판에 있던
  **「`From` 을 구현해라」도, 「`?` 는 `From` 으로 변환한다」도 없다.**
- ★ 그래서 **`?` 가 붙는 자리에는 타입을 구체적으로 적는 쪽이 진단이 훨씬 친절하다**
  (`value.parse::<u16>()?`). 이것은 문법 규칙이 아니라 **진단 품질의 문제**다 —
  「안 되는 이유를 컴파일러에게 잘 묻는 법」에 가깝다.

### (4) ★ `?` 를 손으로 펼치면

**언제 쓰나** — `?` 가 무엇을 줄여 주는지 한 번 확인하고 싶을 때.

```text
===== 소스: ex.rs =====
// ex.rs
// ? 가 펼쳐지는 모양 — 같은 함수를 ? 로 한 번, 손으로 한 번
use std::num::ParseIntError;

#[derive(Debug)]
struct ConfigError(ParseIntError);

impl From<ParseIntError> for ConfigError {
    fn from(e: ParseIntError) -> Self {
        ConfigError(e)
    }
}

fn with_question(raw: &str) -> Result<u16, ConfigError> {
    let n: u16 = raw.parse()?;
    Ok(n)
}

fn by_hand(raw: &str) -> Result<u16, ConfigError> {
    let n: u16 = match raw.parse() {
        Ok(v) => v,
        Err(e) => return Err(From::from(e)),
    };
    Ok(n)
}

fn main() {
    for raw in ["8080", "팔공"] {
        let a = format!("{:?}", with_question(raw));
        let b = format!("{:?}", by_hand(raw));
        println!("{}", a);
        println!("{}", b);
        println!("두 판이 같은가 {}", a == b);
    }
    if let Err(ConfigError(cause)) = with_question("팔공") {
        println!("감싼 원인 {}", cause);
    }
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
Ok(8080)
Ok(8080)
두 판이 같은가 true
Err(ConfigError(ParseIntError { kind: InvalidDigit }))
Err(ConfigError(ParseIntError { kind: InvalidDigit }))
두 판이 같은가 true
감싼 원인 invalid digit found in string
(종료 코드 0)
```

- 두 함수가 **같은 값을 냈다**(`두 판이 같은가 true` 가 두 번).
- ★ `by_hand` 의 `return Err(From::from(e))` 가 `?` 가 펼쳐지는 모양이다.
  **`From::from` 을 손으로 적은 것**이고, `?` 는 그 한 줄을 대신한다.
- ★★ 실제 컴파일러는 `Try`/`FromResidual` 트레이트를 거쳐 펼치지만
  (그래서 에러 문구에 `FromResidual` 이 나온다 — (5)), **관찰 가능한 결과는 위 모양과 같다.**
  ★ 「내부적으로 어떤 트레이트를 거치나」는 **불안정(unstable) API** 이므로 여기서 결론으로 삼지 않는다.

### (5) `?` 가 되는 자리 · 안 되는 자리 — `main`

**전** — `main` 이 `()` 를 반환하는데 `?` 를 썼다.

```text
===== 소스: ex.rs =====
// ex.rs
// main 이 () 를 반환하면 ? 를 못 쓴다
fn main() {
    let n: u16 = "8080".parse()?;
    println!("{}", n);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0277]: the `?` operator can only be used in a function that returns `Result` or `Option` (or another type that implements `FromResidual`)
 --> ex.rs:4:32
  |
3 | fn main() {
  | --------- this function should return `Result` or `Option` to accept `?`
4 |     let n: u16 = "8080".parse()?;
  |                                ^ cannot use the `?` operator in a function that returns `()`
  |
help: consider adding return type
  |
3 ~ fn main() -> Result<(), Box<dyn std::error::Error>> {
4 |     let n: u16 = "8080".parse()?;
5 |     println!("{}", n);
6 +     Ok(())
  |

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0277`.
(종료 코드 1)
```

- ★ 제목이 그대로 답이다 — `` the `?` operator can only be used in a function that returns `Result` or `Option` (or another type that implements `FromResidual`) ``.
- ★★ `help` 가 **고쳐 쓴 `main` 전문**을 보여 준다 — 반환 타입을 `Result<(), Box<dyn std::error::Error>>` 로 바꾸고
  끝에 `Ok(())` 를 넣으라고. **처방이 코드 조각으로 나온다.**

**후** — `main` 이 `Result` 를 반환하면 된다. 그때 **종료 코드와 출력**이 이 절의 관찰 대상이다.

```text
===== 소스: ex.rs =====
// ex.rs
// main 이 Result 를 반환하면 ? 가 된다 — 실패하면 무엇이 찍히고 종료 코드는 얼마인가
use std::error::Error;

fn parse_port(raw: &str) -> Result<u16, std::num::ParseIntError> {
    Ok(raw.parse::<u16>()?)
}

fn main() -> Result<(), Box<dyn Error>> {
    let good = parse_port("8080")?;
    eprintln!("먼저 성공한다 {}", good);
    let bad = parse_port("팔공팔공")?;
    eprintln!("여기는 안 온다 {}", bad);
    Ok(())
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
먼저 성공한다 8080
Error: ParseIntError { kind: InvalidDigit }
(종료 코드 1)
```

- ★★★ **종료 코드가 1 이다.** 패닉의 101 과 다르다([**23번 주제**](../23-panic-vs-result/)에서 셋을 나란히 놓는다).
- ★★★ **`Error: ` 뒤에 찍히는 것은 `Debug` 다** — `Display` 가 아니다.
  출력이 `ParseIntError { kind: InvalidDigit }`(Debug)이지 `invalid digit found in string`(Display)이 아니다.
  ★ 이 성질이 오류 타입 설계에 직접 영향을 준다 — [**24번 주제**](../24-error-type-design/)가 그것을 다룬다.
- `Result<(), Box<dyn Error>>` 가 **`main` 의 실용 기본형**이다. 어떤 오류 타입이든 `?` 로 받아 준다((6)·24번).

### (6) `Option` 과 `Result` 를 섞으면

```text
===== 소스: ex.rs =====
// ex.rs
// Option 과 Result 를 ? 로 섞으면 — 양쪽 다 던져 본다
fn head_len(s: &str) -> Result<usize, std::num::ParseIntError> {
    let head = s.split(',').next()?;
    Ok(head.len())
}

fn first_number(s: &str) -> Option<u16> {
    let head = s.split(',').next()?;
    let n = head.parse::<u16>()?;
    Some(n)
}

fn main() {
    println!("{:?} {:?}", head_len("a,b"), first_number("8080,x"));
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0277]: the `?` operator can only be used on `Result`s, not `Option`s, in a function that returns `Result`
 --> ex.rs:4:35
  |
3 | fn head_len(s: &str) -> Result<usize, std::num::ParseIntError> {
  | -------------------------------------------------------------- this function returns a `Result`
4 |     let head = s.split(',').next()?;
  |                                   ^ use `.ok_or(...)?` to provide an error compatible with `Result<usize, ParseIntError>`

error[E0277]: the `?` operator can only be used on `Option`s, not `Result`s, in a function that returns `Option`
  --> ex.rs:10:32
   |
 8 | fn first_number(s: &str) -> Option<u16> {
   | --------------------------------------- this function returns an `Option`
 9 |     let head = s.split(',').next()?;
10 |     let n = head.parse::<u16>()?;
   |                                ^ use `.ok()?` if you want to discard the `Result<Infallible, ParseIntError>` error information

error: aborting due to 2 previous errors

For more information about this error, try `rustc --explain E0277`.
(종료 코드 1)
```

- ★★ **양쪽 방향 다 거부된다.** 그리고 **진단이 처방까지 갈라 준다** —
  - `Result` 함수에서 `Option` 에 `?` → `` use `.ok_or(...)?` to provide an error compatible with … ``
  - `Option` 함수에서 `Result` 에 `?` → `` use `.ok()?` if you want to discard the `Result<Infallible, ParseIntError>` error information ``
- ★ 뒤쪽 처방에 **`discard … error information`** 이라고 적혀 있는 것이 요점이다 —
  `Result` → `Option` 은 **정보를 버리는** 변환이라 **자동으로 해 주지 않는다.**
- 두 세계를 잇는 다리는 이 둘이다.

```text
===== 소스: ex.rs =====
// ex.rs
// 두 세계를 건너는 다리 — ok_or_else 와 ok()
fn port_of(name: &str) -> Option<u16> {
    if name == "https" { Some(443) } else { None }
}

fn need_port(name: &str) -> Result<u16, String> {
    let p = port_of(name).ok_or_else(|| format!("{} 의 포트를 모른다", name))?;
    Ok(p)
}

fn maybe_port(raw: &str) -> Option<u16> {
    let p = raw.parse::<u16>().ok()?;
    Some(p)
}

fn main() {
    println!("{:?}", need_port("https"));
    println!("{:?}", need_port("gopher"));
    println!("{:?}", maybe_port("443"));
    println!("{:?}", maybe_port("사사삼"));
    println!("{:?}", need_port("gopher").ok());
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
Ok(443)
Err("gopher 의 포트를 모른다")
Some(443)
None
None
(종료 코드 0)
```

- `ok_or_else` 는 **이유를 붙여** `Option` 을 `Result` 로 올린다(게으른 쪽 — [**21번 주제**](../21-option-and-combinators/) (4)).
- `ok()` 는 **이유를 버리고** `Result` 를 `Option` 으로 내린다. 마지막 줄의 `None` 이 버려진 자국이다.

### (7) 손으로 변환하기 — `map_err`

```text
===== 소스: ex.rs =====
// ex.rs
// ? 없이 손으로 — map_err · ok_or_else 가 하는 일
#[derive(Debug)]
struct MyError(String);

fn by_hand(line: &str) -> Result<u16, MyError> {
    let value = match line.strip_prefix("port=") {
        Some(v) => v,
        None => return Err(MyError(String::from("port= 로 시작하지 않는다"))),
    };
    match value.parse::<u16>() {
        Ok(n) => Ok(n),
        Err(e) => Err(MyError(format!("숫자가 아니다: {}", e))),
    }
}

fn by_adapters(line: &str) -> Result<u16, MyError> {
    let value = line
        .strip_prefix("port=")
        .ok_or_else(|| MyError(String::from("port= 로 시작하지 않는다")))?;
    let n = value
        .parse::<u16>()
        .map_err(|e| MyError(format!("숫자가 아니다: {}", e)))?;
    Ok(n)
}

fn main() {
    for line in ["port=8080", "port=팔공", "host=x"] {
        println!("{:?}", by_hand(line));
        println!("{:?}", by_adapters(line));
    }
    if let Err(MyError(msg)) = by_adapters("host=x") {
        println!("메시지만 꺼내면 {}", msg);
    }
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
Ok(8080)
Ok(8080)
Err(MyError("숫자가 아니다: invalid digit found in string"))
Err(MyError("숫자가 아니다: invalid digit found in string"))
Err(MyError("port= 로 시작하지 않는다"))
Err(MyError("port= 로 시작하지 않는다"))
메시지만 꺼내면 port= 로 시작하지 않는다
(종료 코드 0)
```

- `by_hand` 와 `by_adapters` 가 **같은 값을 낸다**(여섯 줄이 둘씩 짝).
- ★ **`map_err` 는 `Err` 쪽에만 거는 `map`** 이다. `?` 가 `From` 으로 못 하는 변환(문자열 가공 등)을 여기서 한다.
- ★ 고르는 기준 — **변환이 그 타입 쌍에서 늘 같으면 `impl From`, 이 호출 자리에서만의 사정이면 `map_err`.**

## 문법 — 형태와 규칙

```text
   형태

   expr?                              expr 은 Result<T, E> 또는 Option<T>
   ──────────────────────────────────────────────────────────────────────
   성공  Ok(v) / Some(v)   →  식의 값이 v 가 된다
   실패  Err(e)            →  return Err(From::from(e))
         None              →  return None

   되는 자리 / 안 되는 자리

   fn f() -> Result<T, E>   { x? }    ✔  x 가 Result 이고 E: From<x 의 오류>
   fn f() -> Option<T>      { x? }    ✔  x 가 Option
   fn f() -> Result<T, E>   { opt? }  ✘  E0277 — ok_or(…)? 로 바꾼다
   fn f() -> Option<T>      { res? }  ✘  E0277 — ok()? 로 바꾼다(정보 버림)
   fn main() -> ()          { x? }    ✘  E0277 — 반환 타입을 Result 로
   fn main() -> Result<(), E>{ x? }   ✔  E: Debug 라야 한다. 실패 시 종료 코드 1

   변환을 만드는 두 가지

   impl From<A> for B { fn from(a: A) -> B { … } }   ← ? 가 자동으로 쓴다(그 타입 쌍이면 늘)
   res.map_err(|a| B::new(a))?                        ← 이 호출 자리에서만
```

- **`?` 는 식이다.** `let n = f()?;` 도 되고 `g(f()?)` 도 되고 `Ok(f()? + 1)` 도 된다.
- ★ **`main` 의 오류 타입에는 `Debug` 가 필요하다**(`Termination` 이 그것을 요구한다). `Display` 만으로는 안 된다.
- ★ **`Box<dyn Error>` 는 거의 모든 오류를 받는다** — std 에 `impl<E: Error + 'static> From<E> for Box<dyn Error>` 가 있기 때문이다(24번).
- **`?` 는 `From<E> for E` 반사 impl 덕분에 같은 타입이면 그냥 통과**한다.
- ★ 1.13.0 이전의 `try!(expr)` 매크로가 `?` 의 전신이다. `try` 는 2018 에디션부터 **예약어**라 지금은 `r#try` 로만 쓴다.

## 어디서 틀리나

| 증상 | 진짜 원인 | 고치는 법 |
|---|---|---|
| ★★ `` `?` couldn't convert the error to … `` | 그 타입 쌍의 `From` impl 이 없다 | `impl From<아래층> for 내오류`((3)) |
| ★ `type mismatch resolving <… as FromStr>::Err == …`(E0271) | 같은 결함인데 **타입을 추론에 맡겨** 진단이 딴 모양이 됐다 | 터보피시로 타입을 적고 다시 던진다((3)) |
| `` can only be used in a function that returns `Result` or `Option` `` | `main` 이나 함수의 반환 타입이 `()` 다 | 반환 타입을 바꾸고 끝에 `Ok(())`((5)) |
| `` can only be used on `Result`s, not `Option`s `` | 두 세계를 섞었다 | `ok_or(…)?`((6)) |
| `` can only be used on `Option`s, not `Result`s `` | 반대 방향 | `ok()?` — **오류 정보가 버려진다**((6)) |
| `main` 이 실패했는데 **메시지가 이상하다** | `Error:` 뒤는 **`Debug`** 다 | `Debug` 를 직접 구현하거나 오류를 감싼다(24번) |
| ★ 오류를 `?` 로 올렸더니 **어디서 났는지 모르겠다** | `?` 는 **문맥을 안 붙인다** | `map_err` 로 층을 감싸거나 `source` 사슬을 만든다(24번) |
| `?` 를 클로저 안에서 썼더니 이상한 에러 | `?` 는 **클로저의 반환 타입**을 기준으로 본다 | 클로저 반환 타입을 적거나 밖으로 뺀다 |

★★ **가장 비싼 실수는 `unwrap()` 으로 `?` 를 대신하는 것이다.** 컴파일은 통과하지만
**호출자가 복구할 기회를 없애고 패닉으로 바꾼다** — 그 판단의 정본이 [**23번 주제**](../23-panic-vs-result/)다.

## 구현 세부사항 대 언어 보장

| 항목 | 무엇인가 | 근거 |
|---|---|---|
| `?` 가 **`From` 변환을 수행하는 것** | ★ **언어 보장** — Reference 의 `?` 절에 적혀 있다 | Reference + (3)의 실측 |
| `main` 이 `Err` 면 **종료 코드 1** | ★ **std 계약** — `Termination` 구현이 그렇게 정의돼 있다 | std 문서 + (5)의 실측 |
| `Error: ` 접두와 **`Debug` 로 찍는 것** | ★ **std 계약**(문서화된 동작). 다만 **문구는 std 구현** | (5)의 실측 |
| 에러 번호가 **E0277 이냐 E0271 이냐** | ★ **구현 세부** — 같은 결함이 진단 경로에 따라 갈린다 | (3)의 실측 두 블록 |
| `help:` 가 고쳐 쓴 코드를 보여 주는 것 | ★ **구현 세부** — 진단 품질은 판마다 는다 | (5)의 실측 |
| `?` 가 내부적으로 거치는 **`Try`/`FromResidual`** | ★ **불안정 API** — 이름이 진단에 보이지만 결론의 근거로 쓰지 않는다 | 에러 제목의 괄호 |
| `ParseIntError` 의 `Debug` 출력 형식 | ★ **구현 세부** — `kind: InvalidDigit` 는 계약이 아니다 | (2)의 실측 |

## 언제 쓰고 언제 안 쓰나

- **`?` 를 쓴다** — 실패를 **호출자가 다뤄야 할 때**. 라이브러리 함수의 기본값이다.
- **`?` 를 안 쓴다** — 실패가 **프로그램 버그**일 때. 그건 `panic!` 이다([**23번 주제**](../23-panic-vs-result/)).
- **`impl From` 을 쓴다** — 그 변환이 **타입 쌍마다 늘 같을 때**. 오류 층이 정해져 있으면 대부분 여기.
- **`map_err` 를 쓴다** — 이 호출 자리에서만의 문맥을 붙일 때(「`port` 를 읽다가」).
- **`Box<dyn Error>` 를 쓴다** — **애플리케이션·`main`** 에서. 라이브러리 공개 API 에는 구체 타입을 둔다(24번).
- ★ **`?` 를 한 함수에 열 번 넘게 쓰고 있으면** 함수가 너무 많은 층을 밟고 있는 것이다. 층을 쪼개면 오류 타입도 같이 쪼개진다.

## 핵심 문장

- ★★★ **`?` 는 조기 반환 + `From` 변환이다.** 뒤엣것을 모르면 E0277 앞에서 멈춘다.
- ★★ **그 증거는 문서가 아니라 에러 메시지에 있다** — 컴파일러가 「`?` 는 `From` 으로 변환한다」고 직접 적는다.
- **`impl From` 만 더하면 본문을 한 글자도 안 고치고 통과한다** — `diff` 로 기계가 보여 준다.
- ★ **같은 결함도 타입을 추론에 맡기면 다른 번호(E0271)로 나온다.** 터보피시를 적으면 진단이 친절해진다.
- **`main` 이 `Err` 를 돌려주면 종료 코드 1 이고 `Debug` 로 찍힌다** — 101(패닉)과 다르다.

## 관련 자료

- [**21번 주제** — `Option` 과 조합 메서드](../21-option-and-combinators/) —
  ★ **경계**: 「없음」을 다루는 메서드는 거기, 「실패를 위로 올리는 연산자」는 여기다. `ok_or` 가 다리다.
- [**20번 주제** — `if let`·`while let`·`let else`](../20-if-let-while-let-let-else-and-let-chains/) —
  ★ **경계**: 조기 반환의 **문법**(내가 블록을 쓴다)은 거기, `?` 의 **변환**(컴파일러가 `From` 을 끼운다)은 여기다.
- [**23번 주제** — `panic!` 대 `Result`](../23-panic-vs-result/) — **어디서 끝낼 것인가**. 종료 코드 1·101·내가 정한 값을 거기서 나란히 던진다.
- [**24번 주제** — 오류 타입 설계](../24-error-type-design/) — `Box<dyn Error>`·`source` 사슬·다운캐스트. 이 주제의 `ConfigError` 를 제대로 설계하는 법.
- [**17번 주제** — 열거형](../17-enums-and-data-carrying-variants/) — `Result` 가 그냥 열거형이라는 것의 정본.
- [목록의 **29번 주제**](../29-conversion-traits-from-into-tryfrom-asref-borrow/) — `From`/`Into`/`TryFrom`. 변환 트레이트 자체의 정본이다.
- Go 의 `(T, error)` 관례 — Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **12번**·**23번**.
  ★ **대비**: Go 는 `if err != nil { return nil, err }` 를 **손으로** 적고 변환도 `fmt.Errorf("%w")` 로 손으로 한다.
  Rust 는 그 세 줄이 `?` 한 글자이고 **변환은 타입 시스템이 강제**한다.
- Java 의 예외 — [`java/syntax/25-exceptions/`](../../../java/syntax/25-exceptions/).
  ★ **대비**: 예외는 **던지면 알아서 위로 간다**(선언하지 않아도 되는 unchecked 가 있다).
  `?` 는 **그 자리에 글자가 있어야** 올라간다 — 「어디서 실패가 위로 새는가」가 코드에 보인다.

## 용어 풀이

- **`Result<T, E>`** — 성공 `Ok(T)` / 실패 `Err(E)` 인 표준 열거형.
- **`?` (물음표 연산자)** — 성공값을 꺼내거나, 실패면 `From` 변환 후 즉시 반환한다.
- **`From` 트레이트** — 「A 로부터 B 를 만든다」는 변환 계약. `?` 가 자동으로 쓴다.
- **터보피시(turbofish)** — `parse::<u16>()` 처럼 `::<>` 로 타입 인자를 직접 적는 표기.
- **`Termination` 트레이트** — `main` 의 반환값을 종료 코드로 바꾸는 std 트레이트.
- **`Box<dyn Error>`** — 어떤 오류든 담는 동적 봉투. 24번이 정본.
- **반사 impl(reflexive impl)** — `impl<T> From<T> for T`. 같은 타입 변환이 항상 되는 이유.

## 더 들어가면

- **`?` 와 `try` 블록** — `try { … }` 식은 아직 불안정하다. 지금은 클로저나 내부 함수로 흉내 낸다.
- **`FromResidual`** — `?` 의 실제 펼침이 거치는 불안정 트레이트. 이름은 E0277 제목의 괄호에 나온다.
- **`Result` 의 조합 메서드** — `map`·`and_then`·`or_else`·`unwrap_or_else` 가 `Option` 과 같은 모양으로 있다(21번과 같은 규칙).
- **`collect::<Result<Vec<_>, _>>()`** — 실패가 하나라도 있으면 전체가 `Err` 가 되는 관용구([목록의 **36번 주제**](../36-iterator-adapters-laziness-and-collect/)).
- **`?` 와 `async`** — `async fn` 안에서도 그대로 쓴다. 반환 타입이 `Result` 인 future 라야 한다(목록의 **54번 주제**).
