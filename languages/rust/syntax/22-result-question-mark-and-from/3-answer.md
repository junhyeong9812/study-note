# rust/syntax/22 — `Result` 와 `?`·`From` 변환 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 받은 것이다.\
> ★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
> ★★ **`--edition` 을 빼면 에디션 2015 다.** 이 갈래에서 그것은 「안 돌려 본 것」과 같다.\
> 실험 파일 이름은 전부 **`ex.rs`** 로 고정했고 **진단의 줄 번호는 그 파일 기준**이다.\
> ★ `rustc --explain E0277` · `E0271` 은 **확인용으로만 열었고 본문에 옮기지 않았다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ E0277 — 컴파일러가 「`?` 는 `From` 으로 변환한다」고 직접 적는다

**출력.**

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

**왜 그런가**

- 에러 번호는 **E0277**, 제목은 `` `?` couldn't convert the error to `ConfigError` `` 다.
- **에러는 하나**다. `?` 가 둘인데 하나만 걸린 이유 —
  첫 번째 `?`(`ok_or(ConfigError::Missing)?`)는 이미 `ConfigError` 라
  **`impl<T> From<T> for T`(반사 impl)** 로 변환이 끝난다. **변환이 없는 것이 아니라 항등 변환이 있는 것**이다.
- ★★★ 마지막 `= note:` 가 이 주제 전체의 증거다 —
  `` the question mark operation (`?`) implicitly performs a conversion on the error value using the `From` trait ``.
  **「`?` 는 `From` 을 쓴다」를 문서에서 옮겨 적은 것이 아니라 컴파일러에게서 받아 적은 것이다.**
- ★★ 그 위의 `note:` 는 처방을 타입까지 찍어 준다 — `` `ConfigError` needs to implement `From<ParseIntError>` ``.
  그리고 `` --> ex.rs:6:1 `` 로 **어느 선언에 붙이라는지**까지 가리킨다.
- 나머지 두 줄이 양쪽 타입을 말한다 —
  `` expected `ConfigError` because of this ``(반환 타입에서 온 요구)와
  `` this can't be annotated with `?` because it has type `Result<_, ParseIntError>` ``(실제로 들어온 것).
- **더해야 하는 줄은 여섯이다**(아래 `diff` 가 그것을 기계로 보여 준다).

**고치는 법 — `impl From` 만 더한다.**

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

**그 판을 돌린 결과.**

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

- ★★ `diff` 에 **주석 한 줄과 `impl From` 여섯 줄**밖에 없다. `port` 함수 본문은 **한 글자도 안 고쳤다.**
  그런데 통과한다 — **`?` 가 찾고 있던 것이 정확히 그 impl** 이었다는 뜻이다.
- 출력의 `Err(BadNumber(ParseIntError { kind: InvalidDigit }))` 가 변환이 일어난 자국이다.
  `ParseIntError` 가 내 열거형 안에 **담겨서** 올라왔다.
- 마지막 줄에서 그 원인을 `if let Err(ConfigError::BadNumber(cause))` 로 꺼내 `invalid digit found in string` 을 찍었다 —
  ★ **감싼 원인을 되찾을 수 있다**는 것이 열거형 오류의 값이고, [**24번 주제**](../24-error-type-design/)가 그 설계를 다룬다.

### 2. ★★ E0271 — 같은 결함인데 `From` 이라는 낱말조차 안 나온다

**출력.**

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

**왜 그런가**

- ★★★ **번호가 다르다 — E0271** (`type mismatch resolving …`). 1번과 **결함은 같은데** 진단 경로가 다르다.
- ★★ **`From` 이라는 낱말이 아예 안 나온다.** 「구현해라」도, 「`?` 는 `From` 으로 변환한다」도 없다.
  진단이 **다섯 줄**로 끝난다(1번은 열여섯 줄이었다).
- 왜 갈리나 — `let n: u16 = value.parse()?` 에서는 `parse` 의 타입 파라미터가 **`?` 를 거쳐 나온 결과 타입에서 역으로** 정해진다.
  그래서 컴파일러가 이 문제를 **`<u16 as FromStr>::Err` 이 `ConfigError` 와 같아야 한다**는
  **연관 타입 등식**으로 먼저 읽고, 그 등식이 깨졌다고 보고한다. `From` 을 찾는 단계까지 가지도 않는다.
- ★ 그래서 실무 처방은 **`?` 앞의 표현식에 타입을 구체적으로 적는 것**이다(`value.parse::<u16>()?`).
  같은 결함이 **훨씬 친절한 진단**으로 나온다.
- ★★ 이 차이는 **구현 세부**다. 언어 보장은 「`?` 가 `From` 변환을 한다」까지이고,
  **어느 번호로 어떻게 보고할지는 rustc 판에 달렸다.**

### 3. ★ E0277 — `?` 는 반환 타입이 `Result`/`Option` 이라야 한다

**출력.**

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

**왜 그런가**

- 번호는 **E0277**, 제목은
  `` the `?` operator can only be used in a function that returns `Result` or `Option` (or another type that implements `FromResidual`) `` 다.
- 진단은 `main` 을 이렇게 가리킨다 — `` this function should return `Result` or `Option` to accept `?` ``.
  그리고 `?` 자리에는 `` cannot use the `?` operator in a function that returns `()` `` 를 붙인다.
- ★★ `help` 는 **문장이 아니라 코드**다. 고쳐 쓴 `main` 을 통째로 보여 준다 —
  `3 ~ fn main() -> Result<(), Box<dyn std::error::Error>> {` 와 `6 + Ok(())`.
  ★ `~` 는 **바뀐 줄**, `+` 는 **더할 줄**이라는 rustc 의 표기다.
- 그 처방을 적용하면 반환 타입은 **`Result<(), Box<dyn std::error::Error>>`** 가 된다 —
  실무에서 `main` 에 가장 많이 쓰는 꼴이고, [**24번 주제**](../24-error-type-design/)가 그 봉투를 다룬다.

### 4. ★★ 종료 코드 1 · 그리고 찍히는 것은 `Debug` 다

**출력.**

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

**왜 그런가**

- 표준 오류에 두 줄이 나온다 — 내가 찍은 `먼저 성공한다 8080` 과 런타임이 찍은
  `Error: ParseIntError { kind: InvalidDigit }`.
- ★★★ **종료 코드는 1 이다.** 패닉의 **101** 과 다르고, `process::exit(n)` 으로 내가 정하는 값과도 다르다.
  셋을 한자리에서 나란히 던진 것이 [**23번 주제**](../23-panic-vs-result/)다.
- ★★★ `Error: ` 뒤는 **`Debug`** 다. 근거는 출력 그 자체다 —
  `ParseIntError` 의 `Display` 는 `invalid digit found in string` 인데(22번 9번 답·24번에서 여러 번 나온다),
  여기 찍힌 것은 `ParseIntError { kind: InvalidDigit }` **구조체 꼴**이다.
  ★ 그래서 **오류 타입을 설계할 때 `Debug` 도 사람이 읽을 만하게** 만들어야 한다 — 24번 6번 답이 그 실험이다.
- `main` 의 오류 타입에는 **`Debug` 경계**가 필요하다. `std::process::Termination` 구현이 그것을 요구한다.
- 성공했으면 종료 코드는 **0** 이다.

### 5. ★★ 양쪽 다 거부된다 — 그리고 처방이 다르다

**출력.**

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

**왜 그런가**

- 에러는 **둘**이다. **양쪽 방향 다 막힌다.**
  - `Result` 함수에서 `Option` 에 `?` →
    `` the `?` operator can only be used on `Result`s, not `Option`s, in a function that returns `Result` ``
  - `Option` 함수에서 `Result` 에 `?` →
    `` the `?` operator can only be used on `Option`s, not `Result`s, in a function that returns `Option` ``
- 처방 둘 —
  - `` use `.ok_or(...)?` to provide an error compatible with `Result<usize, ParseIntError>` ``
  - `` use `.ok()?` if you want to discard the `Result<Infallible, ParseIntError>` error information ``
- ★★ 뒤쪽에 **`discard … error information`** 이 적혀 있다. `Result` → `Option` 은 **왜 실패했는지를 버리는** 변환이라
  **컴파일러가 자동으로 해 주지 않는다.** 앞쪽(`Option` → `Result`)은 **없던 이유를 만들어 내야** 해서 역시 자동이 아니다.
  ★ 두 방향 다 「정보량이 달라서」 막히는 것이지 문법 문제가 아니다.
- 다리는 **`ok_or`/`ok_or_else`** 와 **`ok()`** 다(9번 답의 블록이 그 실행이다).

### 6. ★ 같은 값을 낸다 — `?` 는 `From::from` 한 줄이다

**출력.**

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

**왜 그런가**

- `두 판이 같은가` 가 **두 번 다 `true`** 다. 성공 경로(`Ok(8080)`)와 실패 경로 모두에서 같은 값이 나왔다.
- ★ 펼쳐진 모양은 이 줄이다 — `Err(e) => return Err(From::from(e))`.
  성공이면 값이 식의 자리에 남고, 실패면 **변환해서 즉시 반환**한다.
- ★ `From::from(e)` 은 「`e` 로부터 **반환 타입이 요구하는 오류 타입**을 만든다」이다.
  여기서는 `ConfigError` 를 요구하므로 내가 쓴 `impl From<ParseIntError> for ConfigError` 가 불린다.
- ★★ 실제 컴파일러는 `Try`/`FromResidual` 트레이트를 거쳐 펼친다 — 그 이름은 3번 답의 에러 제목 괄호에 보인다.
  ★ **그러나 그것은 불안정(unstable) API 이므로 결론의 근거로 쓰지 않는다.**
  근거로 쓰는 것은 **관찰 가능한 결과**(두 판의 출력이 같다)와 **안정된 진단 문구**(`From` 으로 변환한다)다.

### 7. `?` 가 하는 두 가지

**출력** — 오류 타입이 같아 변환이 안 보이는 판.

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

**왜 그런가**

- **성공이면** `Ok(v)` 의 `v` 를 꺼내 **식의 값**으로 남긴다 — `let n: u16 = raw.parse()?;` 의 `n` 이 그것이다.
- **실패면** `Err(From::from(e))` 를 **즉시 반환**한다. 그 아래 줄은 실행되지 않는다.
- 오류 타입이 같으면 **변환이 반사 impl 로 끝나** 눈에 안 보인다. 이 블록이 그 경우다.
  `From<T> for T` 가 std 에 있어서 **「변환이 필요 없다」가 아니라 「항등 변환이 있다」** 로 처리된다.
- ★ **`?` 는 식이다.** `let n = f()?;` · `g(f()?)` · `Ok(f()? + 1)` 이 전부 된다.
  근거 — 위 코드의 `raw.parse()?` 가 `let` 의 오른쪽 **표현식 자리**에 그대로 쓰였다.
- **1.13.0 이전에는 `try!(expr)` 매크로**가 같은 일을 했다. `try` 는 2018 에디션부터 예약어라 지금은 `r#try` 로만 부른다.
- ★ `"99999"` 가 `PosOverflow` 로 온 것도 눈여겨볼 것 — 실패의 **종류**가 오류 값 안에 들어 있다.
  `Option` 이었으면 그냥 `None` 이었다([**21번 주제**](../21-option-and-combinators/)).

### 8. `?` 가 되는 자리

**왜 그런가**

- 쓸 수 있는 반환 타입 —
  - **`Result<T, E>`** — 안쪽이 `Result` 면 `E: From<그 오류>` 라야 하고, 안쪽이 `Option` 이면 **안 된다**(5번).
  - **`Option<T>`** — 안쪽이 `Option` 일 때만.
  - `ControlFlow` 등 `FromResidual` 을 구현한 타입(★ 불안정 영역이라 실무 기준은 위 둘이다).
- ★ **클로저 안의 `?` 는 클로저 자신의 반환 타입을 기준**으로 판정된다. 바깥 함수가 `Result` 라도
  클로저가 `Option` 을 돌려주면 그 기준으로 막힌다. 처방은 **클로저 반환 타입을 적거나** 로직을 밖으로 빼는 것이다.
- **`main` 의 실무 기본형은 `Result<(), Box<dyn Error>>`** 다(3번의 `help` 가 그대로 그것을 제안했다).
- ★ `?` 가 한 함수에 **열 번 넘게** 있으면 그 함수가 **여러 층을 한꺼번에 밟고 있는 것**이다.
  층을 쪼개면 오류 타입도 같이 쪼개지고, 그때 [**24번 주제**](../24-error-type-design/)의 열거형 설계가 필요해진다.

### 9. 손으로 변환하기 — `map_err`·`ok_or_else`·`ok`

**출력** — `?` 없이 손으로 쓴 판과 어댑터로 쓴 판.

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

**두 세계를 잇는 다리.**

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

**왜 그런가**

- **`impl From` 을 쓴다** — 그 **타입 쌍에서 변환이 늘 같을 때**. 한 번 쓰면 `?` 가 전부 알아서 쓴다.
- **`map_err` 를 쓴다** — **이 호출 자리에서만의 사정**을 붙일 때. 위 블록의
  `map_err(|e| MyError(format!("숫자가 아니다: {}", e)))` 가 그 꼴이다.
  ★ **`map_err` 는 `Err` 쪽에만 거는 `map`** 으로 읽으면 된다.
- **`ok_or` 와 `ok_or_else` 의 차이는 평가 시점**이다 — `_else` 쪽은 **`None` 일 때만** 클로저를 부른다.
  정본은 [**21번 주제**](../21-option-and-combinators/) (4)이고, 거기서 부작용으로 증명했다.
- **`ok()` 는 오류 값을 버린다.** 위 블록 마지막 줄의 `None` 이 그 자국이다 —
  `Err("gopher 의 포트를 모른다")` 가 `None` 이 되면서 **이유가 사라졌다.**
- ★ **`?` 는 문맥을 안 붙인다.** 「어느 설정을 읽다가 실패했나」 같은 정보는
  `map_err` 로 감싸거나 **`source` 사슬**을 만들어 넣는다 — 그 설계의 정본이 [**24번 주제**](../24-error-type-design/)다.

### 10. 이웃 주제·다른 언어와 잇기

- ★ **20번과의 경계 — 한 줄로**: 겹치는 것은 **조기 반환이라는 모양**뿐이고,
  갈리는 것은 **반환값을 누가 만드나**다. `let else` 는 **내가** `else` 블록에 적고,
  `?` 는 **컴파일러가** `From::from` 을 끼워 만든다([**20번 주제**](../20-if-let-while-let-let-else-and-let-chains/)가 문법의 정본이다).
- `Result` 가 열거형이라는 사실의 정본은 [**17번 주제**](../17-enums-and-data-carrying-variants/) (6)이다.
  거기서 `Option`·`Result` 를 직접 만들어 봤다.
- ★ **Go 는 세 줄이다** — `v, err := f(); if err != nil { return nil, err }`.
  변환도 손으로 한다(`fmt.Errorf("...: %w", err)`).
  Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **12번**(다중 반환)·**23번**(값으로서의 오류)·**24번**(`%w` 래핑)이 그 자리다.
  ★ **가장 큰 차이** — Go 는 `err` 를 **안 보고 지나가도 컴파일된다.** Rust 는 `Result` 를 안 쓰면
  `#[must_use]` 경고가 나고, `?` 없이 값을 쓰려 하면 타입이 안 맞아 **컴파일이 막힌다.**
- ★ **Java 의 예외와의 차이는 「무엇이 코드에 보이나」다**([`java/syntax/25-exceptions/`](../../../java/syntax/25-exceptions/)).
  unchecked 예외는 **아무 표시 없이** 호출 스택을 뚫고 올라간다. `?` 는 **그 자리에 한 글자가 찍혀 있어야** 올라간다 —
  실패가 새는 지점이 **전부 눈에 보인다.**
- **`Box<dyn Error>` 가 어떤 오류든 받는 이유**는 std 에 `impl<E: Error + 'static> From<E> for Box<dyn Error>` 가 있어서다.
  즉 **이 주제의 `From` 규칙이 그대로 적용된 것**이고, 정본은 [**24번 주제**](../24-error-type-design/)다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh` 가 `rustc --edition 2021 ex.rs -o ex` 로 컴파일하고 `./ex` 실행 | 배치 내내 + **제출 전 전수 재실행 1회** | `diff -rq` — 전 블록 동일 |
| ★★★ **`?` 가 `From` 을 끼우는 것** | `b22-02`(E0277 전문) · `b22-diff`(차이) · `b22-03`(통과) | 3 | `= note:` 한 줄이 직접 증언 |
| ★★ **같은 결함의 다른 번호** | `b22-10`(E0271) | 1 | `From` 이라는 낱말이 안 나옴 |
| `main` 과 `?` | `b22-04`(E0277) · `b22-05`(종료 코드 1) | 2 | `Error: ` 뒤는 `Debug` |
| `Option`·`Result` 섞기 | `b22-06`(에러 2개) | 1 | 처방이 방향마다 다름 |
| 손으로 펼친 판 | `b22-08` — 문자열 비교를 **프로그램이** 하게 함 | 1 | `true` 두 번 |
| 어댑터 | `b22-07`(`map_err`) · `b22-09`(`ok_or_else`·`ok`) | 2 | 손 판과 같은 값 |
| 기본 `?` | `b22-01` | 1 | `PosOverflow` 까지 확인 |

**구현 의존 항목**(버전이 오르면 **다시 찍어야 하는** 것).

| 항목 | 왜 |
|---|---|
| **E0277 이냐 E0271 이냐** | ★ 같은 결함의 진단 경로가 갈린다 — 판에 달렸다 |
| `help:` 가 **코드로** 처방을 보여 주는 것 | 진단 품질은 판마다 는다 |
| `ParseIntError` 의 `Debug` 형식(`kind: InvalidDigit`) | std 의 구현 세부다 |
| `FromResidual` 이라는 이름이 제목에 보이는 것 | ★ **불안정 API** — 결론의 근거로 쓰지 않았다 |
| `Error: ` 접두 문구 | std 의 문구다(종료 코드 1 은 계약) |

★ **다시 찍는 법** — `capture.sh` 를 그대로 돌리고 `diff -rq` 한다.
이 주제에는 패닉 블록이 없으므로 **달라지는 파일이 하나도 없어야** 한다.
