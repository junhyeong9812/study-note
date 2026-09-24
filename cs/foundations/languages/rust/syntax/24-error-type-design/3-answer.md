# rust/syntax/24 — 오류 타입 설계 — 열거형 오류·`Error` 트레이트·`source`·`Box<dyn Error>` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 받은 것이다.\
> ★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
> ★★ **외부 크레이트를 하나도 쓰지 않았다** — `thiserror`·`anyhow` 는 10번 답에 **이름만** 나온다.\
> ★★ **`--edition` 을 빼면 에디션 2015 다.** 이 갈래에서 그것은 「안 돌려 본 것」과 같다.\
> 실험 파일 이름은 전부 **`ex.rs`** 로 고정했고 **진단의 줄 번호는 그 파일 기준**이다.\
> ★ `rustc --explain E0308` · `E0277` · `E0271` 은 **확인용으로만 열었고 본문에 옮기지 않았다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 사슬 3층 — `Display` 는 한 층, `Debug` 는 전부

**출력.**

```text
===== 소스: ex.rs =====
// ex.rs
// source 사슬 — 세 층을 쌓고 실제로 걸어서 찍는다
use std::error::Error;
use std::fmt;
use std::num::ParseIntError;

#[derive(Debug)]
struct ConfigError {
    key: &'static str,
    cause: ParseIntError,
}

impl fmt::Display for ConfigError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "설정 `{}` 의 값을 읽지 못했다", self.key)
    }
}

impl Error for ConfigError {
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        Some(&self.cause)
    }
}

#[derive(Debug)]
struct StartupError {
    stage: &'static str,
    cause: ConfigError,
}

impl fmt::Display for StartupError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{} 단계에서 기동에 실패했다", self.stage)
    }
}

impl Error for StartupError {
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        Some(&self.cause)
    }
}

fn boot() -> Result<u16, StartupError> {
    let raw = "팔공팔공";
    let cause = raw.parse::<u16>().unwrap_err();
    Err(StartupError {
        stage: "설정 읽기",
        cause: ConfigError { key: "port", cause },
    })
}

fn print_chain(e: &dyn Error) {
    println!("맨 위      {}", e);
    let mut level = 0;
    let mut cur: Option<&(dyn Error + 'static)> = e.source();
    while let Some(s) = cur {
        level += 1;
        println!("  원인 {}   {}", level, s);
        cur = s.source();
    }
    println!("사슬 길이  {} 층", level + 1);
}

fn main() {
    match boot() {
        Ok(p) => println!("포트 {}", p),
        Err(e) => {
            print_chain(&e);
            println!("Display 만 찍으면  {}", e);
            println!("Debug 로 찍으면    {:?}", e);
        }
    }
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
맨 위      설정 읽기 단계에서 기동에 실패했다
  원인 1   설정 `port` 의 값을 읽지 못했다
  원인 2   invalid digit found in string
사슬 길이  3 층
Display 만 찍으면  설정 읽기 단계에서 기동에 실패했다
Debug 로 찍으면    StartupError { stage: "설정 읽기", cause: ConfigError { key: "port", cause: ParseIntError { kind: InvalidDigit } } }
(종료 코드 0)
```

**왜 그런가**

- `사슬 길이  3 층` 이다. `StartupError` → `ConfigError` → `ParseIntError` 로 두 번 내려갔다.
- 각 층의 `Display` —
  ① `설정 읽기 단계에서 기동에 실패했다` ② ``설정 `port` 의 값을 읽지 못했다`` ③ `invalid digit found in string`.
  ★ ③은 **std 가 준 문장**이다 — 내 층은 둘뿐이고 바닥은 표준 라이브러리다.
- ★★ **`Display` 만 찍은 줄은 맨 위 한 줄뿐**이라 **원인이 안 보인다.**
  반면 **`Debug` 는 중첩 구조를 통째로** 찍는다 —
  `StartupError { stage: "설정 읽기", cause: ConfigError { key: "port", cause: ParseIntError { kind: InvalidDigit } } }`.
  ★ 파생 `Debug` 가 필드를 재귀적으로 찍기 때문이지 **`source()` 를 따라간 것이 아니다.**
  (필드로 안 들고 `source()` 로만 잇는 설계라면 `Debug` 에도 안 보인다.)
- 루프는 **`source()` 가 `None` 을 돌려주는 것**을 보고 멈춘다. `ParseIntError` 의 `source()` 가 `None` 이다.
- ★★ **std 에 사슬을 찍어 주는 함수는 없다.** `Error::sources()` 이터레이터는 **아직 불안정**이라
  안정 판에서는 `while let` 으로 직접 걷는다 — 이 블록의 `print_chain` 이 그 표준형이다.

### 2. ★★ E0308 두 번 — 봉투에 담는 순간 타입이 바뀐다

**출력.**

```text
===== 소스: ex.rs =====
// ex.rs
// Box<dyn Error> 로 받으면 무엇을 잃나 — 변형으로 갈라 보려 하면
use std::error::Error;
use std::fmt;

#[derive(Debug)]
enum ConfigError {
    Missing,
    OutOfRange(u32),
}

impl fmt::Display for ConfigError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "설정 오류 {:?}", self)
    }
}

impl Error for ConfigError {}

fn load() -> Result<u16, Box<dyn Error>> {
    Err(Box::new(ConfigError::OutOfRange(70000)))
}

fn main() {
    match load() {
        Ok(p) => println!("포트 {}", p),
        Err(ConfigError::Missing) => println!("없다"),
        Err(ConfigError::OutOfRange(n)) => println!("범위 밖 {}", n),
    }
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0308]: mismatched types
  --> ex.rs:27:13
   |
 8 |     Missing,
   |     ------- unit variant defined here
...
25 |     match load() {
   |           ------ this expression has type `Result<u16, Box<dyn std::error::Error>>`
26 |         Ok(p) => println!("포트 {}", p),
27 |         Err(ConfigError::Missing) => println!("없다"),
   |             ^^^^^^^^^^^^^^^^^^^^ expected `Box<dyn Error>`, found `ConfigError`
   |
   = note: expected struct `Box<dyn std::error::Error>`
                found enum `ConfigError`

error[E0308]: mismatched types
  --> ex.rs:28:13
   |
25 |     match load() {
   |           ------ this expression has type `Result<u16, Box<dyn std::error::Error>>`
...
28 |         Err(ConfigError::OutOfRange(n)) => println!("범위 밖 {}", n),
   |             ^^^^^^^^^^^^^^^^^^^^^^^^^^ expected `Box<dyn Error>`, found `ConfigError`
   |
   = note: expected struct `Box<dyn std::error::Error>`
                found enum `ConfigError`

error: aborting due to 2 previous errors

For more information about this error, try `rustc --explain E0308`.
(종료 코드 1)
```

**왜 그런가**

- **E0308 이 두 개** 난다 — `match` 의 `Err` 팔이 둘이라 각각 걸린다.
- `` expected struct `Box<dyn std::error::Error>` `` / `` found enum `ConfigError` `` 다.
  `load()` 의 타입이 `Result<u16, Box<dyn Error>>` 이므로 **패턴도 그 타입에만 맞출 수 있다.**
- ★★★ **변형이 사라진 것이 아니라 보이지 않는 것**이다. 값은 봉투 안에 그대로 있고
  3번 답에서 `downcast_ref` 로 되꺼낸다. **컴파일러가 그 사실을 모를 뿐**이고,
  「무엇이 들었는지 컴파일 시점에 모른다」가 바로 `dyn` 의 뜻이다.
- 진단은 `` unit variant defined here `` 로 `Missing` 선언을 가리킨다 —
  **내가 무엇을 하려 했는지는 알아보지만 그렇게는 안 된다**는 말이다.

### 3. ★ 되찾힌다 — 대신 대가가 셋

**출력.**

```text
===== 소스: ex.rs =====
// ex.rs
// 되찾는 법 — downcast_ref 로 구체 타입을 다시 꺼낸다
use std::error::Error;
use std::fmt;
use std::num::ParseIntError;

#[derive(Debug)]
enum ConfigError {
    Missing,
    OutOfRange(u32),
}

impl fmt::Display for ConfigError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "설정 오류 {:?}", self)
    }
}

impl Error for ConfigError {}

fn load(which: u8) -> Result<u16, Box<dyn Error>> {
    match which {
        0 => Err(Box::new(ConfigError::Missing)),
        1 => Err(Box::new(ConfigError::OutOfRange(70000))),
        _ => Err(Box::new("팔공".parse::<u16>().unwrap_err())),
    }
}

fn main() {
    for which in 0..3 {
        let e = load(which).unwrap_err();
        print!("{} 받은 것 {} | ", which, e);
        if let Some(c) = e.downcast_ref::<ConfigError>() {
            match c {
                ConfigError::Missing => println!("내 오류 · 없음 갈래"),
                ConfigError::OutOfRange(n) => println!("내 오류 · 범위 밖 {}", n),
            }
        } else if let Some(p) = e.downcast_ref::<ParseIntError>() {
            println!("std 오류 · ParseIntError({})", p);
        } else {
            println!("무엇인지 모른다");
        }
    }
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
0 받은 것 설정 오류 Missing | 내 오류 · 없음 갈래
1 받은 것 설정 오류 OutOfRange(70000) | 내 오류 · 범위 밖 70000
2 받은 것 invalid digit found in string | std 오류 · ParseIntError(invalid digit found in string)
(종료 코드 0)
```

**왜 그런가**

- 세 경우가 전부 원래 타입으로 갈라졌다 — 내 열거형 두 변형과 std 의 `ParseIntError`.
- ★★ `downcast_ref` 는 **런타임**에 `TypeId` 를 비교한다. 컴파일 시점에는 아무것도 확인되지 않는다.
- ★★★ `match` 에 비해 잃는 것 셋 —
  ① **타입을 내가 적어야 한다** — `downcast_ref::<ConfigError>()` 의 그 이름을 **내가 알고 있어야** 한다.
  ② **완전성 검사가 없다** — 후보를 빠뜨려도 컴파일이 통과하고, 조용히 `else` 로 떨어진다
  ([**18번 주제**](../18-match-and-exhaustiveness/)가 준 안전망이 사라진다).
  ③ **분기가 중첩된다** — `if let … else if let … else` 사슬이 되고, 각 갈래 안에서 다시 `match` 한다.
- **std 오류도 똑같이 되찾아진다**(세 번째 줄). `Error + 'static` 이면 모두 대상이다.
- ★ 그래서 규칙 — **호출자가 분기할 것을 알고 있으면 처음부터 열거형으로 준다.**
  `Box<dyn Error>` 는 「분기 안 하고 보고만 하겠다」는 선언이다.

### 4. ★ 세 오류가 전부 `?` 로 올라간다

**출력.**

```text
===== 소스: ex.rs =====
// ex.rs
// ? 는 Box<dyn Error> 로는 그냥 변환된다 — 서로 다른 오류 셋을 한 함수에서
use std::error::Error;
use std::fmt;

#[derive(Debug)]
struct MyError(&'static str);

impl fmt::Display for MyError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "내 오류: {}", self.0)
    }
}

impl Error for MyError {}

fn mixed(step: u8) -> Result<u16, Box<dyn Error>> {
    let n: u16 = "8080".parse()?;
    if step == 1 {
        let _text = std::fs::read_to_string("없는파일.txt")?;
    }
    if step == 2 {
        let _bad: u16 = "팔공".parse()?;
    }
    if step == 3 {
        Err(MyError("내가 만든 실패"))?;
    }
    Ok(n)
}

fn main() {
    for step in 0..4 {
        match mixed(step) {
            Ok(v) => println!("{} Ok({})", step, v),
            Err(e) => println!("{} Err  {}", step, e),
        }
    }
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
0 Ok(8080)
1 Err  No such file or directory (os error 2)
2 Err  invalid digit found in string
3 Err  내 오류: 내가 만든 실패
(종료 코드 0)
```

**왜 그런가**

- 네 줄 —
  `0 Ok(8080)` · `1 Err  No such file or directory (os error 2)` ·
  `2 Err  invalid digit found in string` · `3 Err  내 오류: 내가 만든 실패`.
- ★★ 세 타입이 전부 통과하는 이유는 std 의 **`impl<E: Error + 'static> From<E> for Box<dyn Error>`** 때문이다.
  즉 [**22번 주제**](../22-result-question-mark-and-from/)에서 본 **`?` 의 `From` 규칙이 그대로 적용된 것**이고,
  특별한 문법이 생긴 것이 아니다.
- `Err(MyError("내가 만든 실패"))?` 는 **「여기서 이 오류로 끝낸다」를 `?` 로 적은 것**이다.
  `Err(...)` 에 `?` 를 붙이면 **변환 후 즉시 반환**되므로 `return Err(Box::new(...))` 와 같은 일이 된다.
- 찍힌 것은 **`Display`** 다 — `{}` 로 찍었기 때문이다(`1 Err  No such file…`).
  `{:?}` 였다면 `Os { code: 2, kind: NotFound, message: … }` 꼴이 나왔을 것이다.
  ★ 두 표면을 고르는 것은 **찍는 쪽**이다.

### 5. ★★ 에러 둘 — E0271 과 E0277

**출력.**

```text
===== 소스: ex.rs =====
// ex.rs
// 구체 타입으로 받으면 — 같은 ? 가 거부된다
use std::fmt;

#[derive(Debug)]
struct MyError(&'static str);

impl fmt::Display for MyError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "내 오류: {}", self.0)
    }
}

impl std::error::Error for MyError {}

fn mixed() -> Result<u16, MyError> {
    let n: u16 = "8080".parse()?;
    let _text = std::fs::read_to_string("없는파일.txt")?;
    Ok(n)
}

fn main() {
    println!("{:?}", mixed());
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0271]: type mismatch resolving `<u16 as FromStr>::Err == MyError`
  --> ex.rs:17:25
   |
17 |     let n: u16 = "8080".parse()?;
   |                         ^^^^^ expected `MyError`, found `ParseIntError`

error[E0277]: `?` couldn't convert the error to `MyError`
  --> ex.rs:18:52
   |
16 | fn mixed() -> Result<u16, MyError> {
   |               -------------------- expected `MyError` because of this
17 |     let n: u16 = "8080".parse()?;
18 |     let _text = std::fs::read_to_string("없는파일.txt")?;
   |                 ---------------------------------------^ the trait `From<std::io::Error>` is not implemented for `MyError`
   |                 |
   |                 this can't be annotated with `?` because it has type `Result<_, std::io::Error>`
   |
note: `MyError` needs to implement `From<std::io::Error>`
  --> ex.rs:6:1
   |
 6 | struct MyError(&'static str);
   | ^^^^^^^^^^^^^^
   = note: the question mark operation (`?`) implicitly performs a conversion on the error value using the `From` trait

error: aborting due to 2 previous errors

Some errors have detailed explanations: E0271, E0277.
For more information about an error, try `rustc --explain E0271`.
(종료 코드 1)
```

**왜 그런가**

- 에러는 **둘**이고 번호가 **다르다** — `"8080".parse()` 쪽이 **E0271**, `read_to_string` 쪽이 **E0277** 이다.
- ★ 갈리는 이유는 [**22번 주제**](../22-result-question-mark-and-from/) 2번 답에서 본 그대로다 —
  **오류 타입을 추론에 맡긴 자리**(`let n: u16 = "8080".parse()?`)는 연관 타입 등식으로 먼저 읽혀
  「타입이 안 맞는다」가 되고, **구체 타입인 자리**(`io::Error`)는 `From` 을 찾다가 없어서 E0277 이 된다.
  ★★ **같은 결함이 두 얼굴을 갖는다** — 이 주제에서 한 번 더 확인된 셈이다.
- ★★★ `= note:` 가 다시 증언한다 —
  `` the question mark operation (`?`) implicitly performs a conversion on the error value using the `From` trait ``.
  그리고 `` `MyError` needs to implement `From<std::io::Error>` `` 로 처방까지 준다.
- 통과시키는 방법 **둘** —
  ① **`impl From<ParseIntError> for MyError` 와 `impl From<io::Error> for MyError` 를 쓴다**(층마다 하나씩),
  ② **반환 타입을 `Result<u16, Box<dyn Error>>` 로 바꾼다**(4번 답의 판).
  ★ 전자는 호출자의 선택권을 사는 값이고, 후자는 그것을 포기하고 편의를 얻는 것이다.

### 6. ★★ `Debug` 가 찍힌다 — `Display` 는 안 쓰인다

**출력.**

```text
===== 소스: ex.rs =====
// ex.rs
// main 이 Err 를 돌려줄 때 찍히는 것은 Display 가 아니라 Debug 다
use std::error::Error;
use std::fmt;

struct ConfigError {
    key: &'static str,
}

impl fmt::Display for ConfigError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "설정 `{}` 이 없다 — 사람이 읽을 문장", self.key)
    }
}

impl fmt::Debug for ConfigError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "ConfigError {{ key: {:?} }} ← 이 줄이 Debug 다", self.key)
    }
}

impl Error for ConfigError {}

fn main() -> Result<(), ConfigError> {
    eprintln!("A 시작");
    Err(ConfigError { key: "port" })
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
A 시작
Error: ConfigError { key: "port" } ← 이 줄이 Debug 다
(종료 코드 1)
```

**왜 그런가**

- 찍히는 것은 `Error: ConfigError { key: "port" } ← 이 줄이 Debug 다` 이고, 그 앞에 내 마커 `A 시작` 이 있다.
- ★★★ **이 소스는 두 구현이 서로 다른 문장을 내도록 일부러 만들어 두었다.**
  `Display` 는 ``설정 `port` 이 없다 — 사람이 읽을 문장`` 인데 **그 문장이 안 나왔다.**
  ★ **출력 하나로 「어느 표면이 쓰이나」가 판정된다** — 문서를 읽고 옮긴 것이 아니다.
- 종료 코드는 **1** 이다([**23번 주제**](../23-panic-vs-result/) 10번 답의 표).
- `Display` 문장을 보여 주는 방법 셋 —
  ① **`Debug` 를 직접 구현**해 `Display` 와 같은(또는 더 자세한) 문장을 내게 한다 — 이 블록이 그 방식이다.
  ② `main` 을 `Result` 로 두지 않고, 안에서 `eprintln!("{}", e)` + **사슬 걷기**를 하고 `process::exit(1)`.
  ③ `Display` 를 `Debug` 로 위임하는 **래퍼 타입**으로 감싸 `main` 이 그것을 반환하게 한다.

### 7. 호출자가 분기하나, 보고만 하나

**왜 그런가**

- ★★★ **한 질문으로 줄인다 — 「호출자가 이 실패들을 갈라서 다르게 행동할 것인가?」**
  그렇다면 **열거형**, 아니면 **`Box<dyn Error>`** 다.
- 라이브러리가 `Box<dyn Error>` 를 반환하면 호출자에게서 **갈래로 분기할 능력**을 빼앗는다.
  호출자는 `downcast_ref` 로 **내부 타입 이름을 추측해** 되찾아야 하고,
  그 이름은 **문서에 적히지 않으면 알 수도 없다**(2번·3번 답).
- 애플리케이션이 층마다 열거형을 만들면 **아무도 `match` 하지 않는 변형**과
  **층마다의 `From` impl** 을 유지보수하게 된다 — 5번 답의 ①이 그 비용이다.
- 변형을 더하면 호출자의 `match` 가 **컴파일 에러로 깨진다**([**18번 주제**](../18-match-and-exhaustiveness/)).
  이것은 **비용이자 안전망**이고, 공개 API 라면 **`#[non_exhaustive]`** 로 완화한다 —
  그러면 호출자가 `_` 팔을 **반드시** 두게 되어 변형 추가가 하위 호환이 된다.

### 8. 네 표면의 분업

**출력** — 기본형 한 벌.

```text
===== 소스: ex.rs =====
// ex.rs
// 열거형 오류 타입의 기본형 — Debug 는 파생, Display 와 Error 는 직접
use std::error::Error;
use std::fmt;

#[derive(Debug)]
enum ConfigError {
    Missing { key: &'static str },
    OutOfRange { key: &'static str, got: u32, max: u32 },
}

impl fmt::Display for ConfigError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ConfigError::Missing { key } => write!(f, "설정 `{}` 이 없다", key),
            ConfigError::OutOfRange { key, got, max } => {
                write!(f, "설정 `{}` 이 범위를 넘었다: {} > {}", key, got, max)
            }
        }
    }
}

impl Error for ConfigError {}

fn check(key: &'static str, got: u32) -> Result<u32, ConfigError> {
    if got > 65535 {
        return Err(ConfigError::OutOfRange { key, got, max: 65535 });
    }
    Ok(got)
}

fn main() {
    let e = ConfigError::Missing { key: "port" };
    println!("Display {{}}   {}", e);
    println!("Debug   {{:?}}  {:?}", e);
    println!("source        {:?}", e.source().is_some());

    match check("port", 70000) {
        Ok(v) => println!("좋다 {}", v),
        Err(e) => println!("실패    {} / {:?}", e, e),
    }
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
Display {}   설정 `port` 이 없다
Debug   {:?}  Missing { key: "port" }
source        false
실패    설정 `port` 이 범위를 넘었다: 70000 > 65535 / OutOfRange { key: "port", got: 70000, max: 65535 }
(종료 코드 0)
```

**왜 그런가**

- **`Error` 는 `Debug + Display` 를 요구한다.** 그래서 오류 타입은 늘 **세 구현이 한 벌**이다.
  (`Debug` 는 보통 파생, `Display` 는 직접.)
- **`source()` 의 기본 구현은 `None`** 이다. 실행으로 확인된다 — 이 블록의 `source        false` 줄이
  `e.source().is_some()` 의 결과다. ★ `impl Error for ConfigError {}` 가 **비어 있는데도 컴파일되는 것**이 그 증거이기도 하다.
- ★ **`Display` 에 원인까지 이어 붙이면 중복으로 찍힌다** — 사슬을 걷는 쪽에서 각 층을 이미 찍기 때문이다.
  그래서 **`Display` 는 자기 층만** 말하는 것이 관례다(1번 답의 사슬을 보라).
- ★★ **`source()` 의 반환에 `'static` 이 붙은 이유** — 다운캐스트가 `TypeId` 로 판정하는데,
  `TypeId` 는 **`'static` 타입에만** 있다. 즉 `'static` 경계가 **3번 답의 되찾기를 가능하게 하는 조건**이다.

### 9. 갈래마다 다른 복구

**출력.**

```text
===== 소스: ex.rs =====
// ex.rs
// 호출자가 갈래로 복구한다 — 열거형 오류가 Box<dyn Error> 와 갈리는 지점
use std::fmt;

#[derive(Debug)]
enum FetchError {
    NotFound { key: String },
    Throttled { retry_after_ms: u32 },
    Corrupt { at: usize },
}

impl fmt::Display for FetchError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            FetchError::NotFound { key } => write!(f, "`{}` 가 없다", key),
            FetchError::Throttled { retry_after_ms } => {
                write!(f, "{}ms 뒤에 다시 오라", retry_after_ms)
            }
            FetchError::Corrupt { at } => write!(f, "{}바이트 자리가 깨졌다", at),
        }
    }
}

impl std::error::Error for FetchError {}

fn fetch(key: &str) -> Result<String, FetchError> {
    match key {
        "a" => Ok(String::from("값 A")),
        "b" => Err(FetchError::NotFound { key: key.to_string() }),
        "c" => Err(FetchError::Throttled { retry_after_ms: 250 }),
        _ => Err(FetchError::Corrupt { at: 12 }),
    }
}

fn main() {
    for key in ["a", "b", "c", "d"] {
        match fetch(key) {
            Ok(v) => println!("{} 성공 {}", key, v),
            Err(FetchError::NotFound { .. }) => println!("{} 기본값으로 계속한다", key),
            Err(FetchError::Throttled { retry_after_ms }) => {
                println!("{} {}ms 재시도 예약", key, retry_after_ms)
            }
            Err(e @ FetchError::Corrupt { .. }) => println!("{} 복구 불가 — 위로 올린다: {}", key, e),
        }
    }
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
a 성공 값 A
b 기본값으로 계속한다
c 250ms 재시도 예약
d 복구 불가 — 위로 올린다: 12바이트 자리가 깨졌다
(종료 코드 0)
```

**왜 그런가**

- 세 변형이 **서로 다른 행동**으로 이어졌다 — 기본값으로 계속 · 250ms 재시도 예약 · 위로 올림.
  ★ 이것이 `Box<dyn Error>` 로는 **컴파일러의 도움을 받으며 할 수 없는 일**이다(2번 답).
- `Err(e @ FetchError::Corrupt { .. })` 의 **`@` 는 「이 패턴에 맞으면서, 값 전체도 `e` 로 잡아라」** 다
  ([**19번 주제**](../19-pattern-syntax-guards-bindings-and-match-ergonomics/)). 그래서 같은 팔에서 `{}` 로 찍을 수 있다.
- **이름 있는 필드**(`Throttled { retry_after_ms }`)를 쓰면 호출자가 **필요한 것만** 꺼내고
  `..` 로 나머지를 무시할 수 있다. 튜플 변형은 위치를 외워야 한다.
- `Box<dyn Error>` 로 바꾸면 — 이 `match` 전체를 **`downcast_ref` 사슬**로 다시 써야 하고,
  **완전성 검사도 잃는다**(3번 답).

### 10. 크레이트·다른 언어와 잇기

- **`thiserror`** — `Display` 와 `Error`/`source` 구현을 **파생 매크로로** 만들어 준다. **라이브러리** 쪽이다.
  **`anyhow`** — `Box<dyn Error>` 자리에 쓰는 봉투 타입에 **문맥 붙이기와 백트레이스**를 더한 것. **애플리케이션** 쪽이다.
  ★ 둘 다 **이 주제의 구조를 줄여 줄 뿐 바꾸지 않는다.**
- 표준만으로 쓰면서 **손으로 쓴 impl** 은 — `impl Display`(문장), `impl Error`(트레이트 자체),
  `fn source()`(사슬 링크), 그리고 필요할 때 `impl From<아래층>`(22번) 과 `impl Debug`(6번)다.
- ★ **Go 와 구조가 거의 같다**(Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **24번**) —
  `Unwrap()` 이 `source()`, `errors.As` 가 `downcast_ref`, `errors.Is` 가 「같은 오류인가」 비교다.
  ★ **다른 점** — Rust 는 오류를 **열거형**으로 두면 `match` 의 **완전성 검사**가 얹힌다.
  Go 의 오류는 인터페이스 값이라 그 검사가 원리상 없다.
- ★ **Java 의 `getCause()` 가 `source()` 와 같은 자리**다([`java/syntax/25-exceptions/`](../../../java/syntax/25-exceptions/)).
  ★★ **다른 점은 스택 트레이스**다 — Java 예외는 **언어가 스택 트레이스를 넣어 준다.**
  Rust 의 오류 **값**에는 스택 트레이스가 없다(`RUST_BACKTRACE` 는 **패닉** 쪽 기능이다 —
  [**23번 주제**](../23-panic-vs-result/)의 `note:` 줄이 그것이다). 그 빈자리를 `anyhow` 나
  `std::backtrace::Backtrace` 필드가 채운다.
- **스레드 경계를 넘기려면 `Box<dyn Error + Send + Sync>`** 라야 한다.
  `Box<dyn Error>` 는 `Send`/`Sync` 가 아니라 스레드로 못 넘어간다(목록의 **50번 주제**).

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh` 가 `rustc --edition 2021 ex.rs -o ex` 로 컴파일하고 `./ex` 실행 | 배치 내내 + **제출 전 전수 재실행 1회** | `diff -rq` — 전 블록 동일 |
| ★★★ **`source()` 사슬** | `b24-02` — `while let` 으로 **직접 걸어** 출력 | 1 | **3층** · 마지막이 `None` |
| ★★ **`Box<dyn Error>` 가 잃는 것** | `b24-03`(E0308 ×2) · `b24-04`(되찾기) | 2 | 변형은 남아 있고 **보이지 않을 뿐** |
| `?` 와 `Box<dyn Error>` | `b24-05`(세 오류 통과) · `b24-06`(구체 타입은 거부) | 2 | E0271 + E0277 |
| `main` 의 표면 | `b24-07` — `Display` 와 `Debug` 를 **다른 문장**으로 만들어 판정 | 1 | `Debug` 가 찍힘 · 종료 코드 1 |
| 기본형 한 벌 | `b24-01` — `source()` 기본값까지 확인 | 1 | `source false` |
| 갈래별 복구 | `b24-08` | 1 | 세 변형이 세 행동으로 |
| 외부 크레이트 | **쓰지 않음** — 네트워크 없이 std 만 | 0 | `thiserror`·`anyhow` 는 이름만 |

**구현 의존 항목**(버전·환경이 바뀌면 **다시 찍어야 하는** 것).

| 항목 | 왜 |
|---|---|
| `No such file or directory (os error 2)` | ★ **OS 세부** — 다른 OS 면 문구도 번호도 다르다 |
| `ParseIntError` 의 `Display`·`Debug` 문구 | std 의 구현 세부다 |
| 에러 번호가 E0271 이냐 E0277 이냐 | ★ 같은 결함의 진단 경로가 갈린다 |
| 파생 `Debug` 의 중첩 출력 형식 | 파생 매크로의 형식이다 |
| `Error::sources()` 가 **불안정**인 것 | ★ 안정화되면 1번 답의 `while let` 관용구가 바뀐다 |
| **못 던져 본 것** — `thiserror`·`anyhow` 로 같은 구조를 짠 판 | ★ **외부 크레이트 금지**(네트워크 없음)라 **이 환경에서 못 돌린다.** 「안 돌려 봄」이 아니라 그렇게 적는다 |

★ **다시 찍는 법** — `capture.sh` 를 그대로 돌리고 `diff -rq` 한다.
이 주제에는 패닉 블록이 없으므로 **달라지는 파일이 하나도 없어야** 한다.
