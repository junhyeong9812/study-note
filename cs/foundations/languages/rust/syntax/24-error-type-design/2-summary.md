# rust/syntax/24 — 오류 타입 설계 — 열거형 오류·`Error` 트레이트·`source`·`Box<dyn Error>` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [std — `trait Error`](https://doc.rust-lang.org/std/error/trait.Error.html) ·
> [std — `Error::source`](https://doc.rust-lang.org/std/error/trait.Error.html#method.source) ·
> [std — `Box<dyn Error>` 의 `downcast_ref`](https://doc.rust-lang.org/std/error/trait.Error.html#method.downcast_ref) ·
> [std — `trait Display`](https://doc.rust-lang.org/std/fmt/trait.Display.html).
> ★ `rustc --explain E0308` · `E0277` · `E0271` 은 **확인용으로만 열었고 본문에 옮기지 않았다.**
> **실행 검증** — 이 문서의 모든 출력·에러는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 받은 것이다.\
> ★★ **`rustc ex.rs` 만 쓰면 에디션 2015 다** — 에디션을 안 밝힌 결과는 다른 언어를 컴파일한 것과 같다.\
> ★★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
> ★★ **외부 크레이트를 하나도 쓰지 않았다.** `thiserror`·`anyhow` 는 **이름만** 나온다((8)) —
> 이 주제의 목적은 **표준만으로 어디까지 되는지**를 먼저 세우는 것이다.
> **버전** — `std::error::Error` 는 **1.0.0**, **`Error::source` 는 1.30.0**(그 전에는 `cause`, 지금은 deprecated) 부터.\
> `Box<dyn Error>` 의 `downcast_ref` 는 1.0.0 부터다. **전부 에디션과 무관하다.**
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | 패닉 첫 줄 `thread 'main' (…)` 괄호 안의 OS 스레드 id | 이 주제에는 패닉 블록이 없지만 규칙은 같다 |
| **흔들린다** | `0x…` 주소 | 실행마다 다르다 |
| 안 흔들린다 | **종료 코드 0 · 1** | `main` 이 `Err` 면 **1** 이다 |
| 안 흔들린다 | 에러 번호·제목·`= note:`·`help:` 줄·`파일:줄:칸` | 같은 rustc 판에서 고정이다 |
| 안 흔들린다 | `source()` 사슬의 **층수와 순서** | 내가 구현한 대로다 — 이 주제의 핵심 근거다 |
| 안 흔들린다 | `No such file or directory (os error 2)` | ★ 같은 OS·같은 std 판에서 고정이다(다른 OS 면 다르다 — §구현 세부) |

## 한눈에 — 쉽게 말하면

**오류 타입 설계는 「호출자가 무엇을 할 수 있게 할 것인가」를 정하는 일이다.**

| 비유 | 실체 |
|---|---|
| 「**사유 코드가 찍힌 반려 서류**」 | **열거형 오류** — 호출자가 **갈래로 분기**할 수 있다((7)) |
| 「**서류에 적힌 사람이 읽을 문장**」 | **`Display`** — 사용자·로그에 보여 줄 한 줄 |
| 「**서류 뒤에 붙은 원본 반려증**」 | ★ **`source()`** — 아래 층의 오류. 사슬이 된다((2)) |
| 「**아무 서류나 담는 서류 봉투**」 | **`Box<dyn Error>`** — 어떤 오류든 받는다. ★ 대신 **갈래를 잃는다**((3)) |
| 봉투에서 **원래 서류를 도로 꺼내기** | **`downcast_ref::<T>()`** — 타입을 **찍어서** 물어야 한다((4)) |
| 「이 서류는 **개발자용**」 | **`Debug`** — `main` 이 `Err` 를 낼 때 찍히는 쪽((6)) |

- ★★★ **갈림길은 하나다 — 호출자가 「분기」해야 하나, 「보고」만 하면 되나.**
  분기해야 하면 **열거형**(라이브러리), 보고만 하면 **`Box<dyn Error>`**(애플리케이션·`main`).
- ★★ **`Box<dyn Error>` 로 감싸는 순간 잃는 것이 있다** — `match` 가 안 된다((3)).
  되찾으려면 **내가 타입을 알고 있어야** 한다(`downcast_ref::<ConfigError>()`) — **컴파일러가 도와주지 않는다.**
- ★ **`?` 는 `Box<dyn Error>` 로는 거의 다 변환해 준다**((5)). 구체 타입으로는 **`From` 이 없으면 막힌다**([**22번 주제**](../22-result-question-mark-and-from/)).

```text
   오류 한 덩어리가 가진 네 표면

   ┌──────────────────────────────────────────────┐
   │  MyError                                     │
   │   ├─ Display   "설정 `port` 의 값을 못 읽었다" │ ← 사람에게 (한 층만 말한다)
   │   ├─ Debug     MyError { key: "port", … }    │ ← 개발자에게 · main 이 이걸 찍는다
   │   ├─ source()  Some(&ParseIntError)          │ ← ★ 아래 층으로 가는 링크
   │   └─ 변형들     Missing / OutOfRange / …      │ ← ★ 호출자가 분기하는 축
   └──────────────────────────────────────────────┘


   사슬을 걷는다 — Display 는 자기 층만 말하므로

   StartupError ──source()──▶ ConfigError ──source()──▶ ParseIntError ──source()──▶ None
   "설정 읽기 단계에서      "설정 `port` 의 값을      "invalid digit
    기동에 실패했다"          읽지 못했다"              found in string"
        │                         │                          │
        └─ 이 한 줄만 찍으면 원인이 안 보인다. ★ while let 으로 끝까지 걷는다((2)).


   두 표면, 두 용도

   라이브러리 ──▶ enum MyError { … }     호출자가 match 한다 · 변형이 공개 API 다
   애플리케이션 ─▶ Box<dyn Error>        그냥 위로 올린다 · main 에서 보고하고 끝
```

> **`std::error::Error`** — 오류 타입이 구현하는 표준 트레이트.\
> `Debug + Display` 를 **요구**하고, `source()` 를 **선택적으로** 제공한다.

> **`source()`** — 이 오류를 **일으킨 아래 층 오류**를 돌려준다. 기본 구현은 `None`.\
> 구현해 두면 원인 사슬이 만들어진다.

> **`Box<dyn Error>`** — 「`Error` 를 구현한 어떤 타입」을 담는 동적 봉투.\
> 크기가 컴파일 시점에 안 정해지므로 `Box` 로 감싼다(트레이트 객체의 정본은 [목록의 **33번 주제**](../33-dyn-trait-objects-and-object-safety/)).

> **다운캐스트(downcast)** — 동적 봉투에서 **구체 타입을 지정해** 되꺼내는 것.\
> `downcast_ref::<T>()` 는 맞으면 `Some(&T)`, 아니면 `None` 이다.

## 이 주제가 답하려는 질문

1. **오류 타입 하나에 무엇을 구현해야 하나** — `Debug`·`Display`·`Error`·`source` 의 분업((1)·(2)).
2. ★★ **`Box<dyn Error>` 로 받으면 무엇을 잃나** — 그리고 되찾는 값은 얼마인가((3)·(4)).
3. **라이브러리와 애플리케이션이 왜 다른 표면을 쓰나** — `?` 의 편의와 호출자의 선택권 사이((5)\~(7)).

★ [**23번 주제**](../23-panic-vs-result/)가 「`Result` 로 갈지 패닉할지」를 정했다면, 여기는 **「`Result` 로 가기로 했으면 그 `E` 를 어떻게 만드나」** 다.

## 동작 방식

### (0) 이 주제가 쓰는 네 창

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| **`{}` 와 `{:?}` 를 나란히 찍기** | 두 표면이 **다른 문장**을 낸다 | 기본 창 |
| ★★★ **`source()` 사슬을 `while let` 으로 걷기** | 원인이 **몇 층**이고 각 층이 무엇을 말하나 | ★ 이 주제의 고유 창 |
| ★★ **`Box<dyn Error>` 에 `match` 를 던져 보기** | 무엇을 **잃는가** — 컴파일 에러가 그것을 말한다 | [**11번 주제**](../11-borrow-checker-rejections/)의 방식 |
| ★ **`downcast_ref` 로 되찾아 보기** | 잃은 것을 **얼마의 값을 치르고** 되찾나 | ★ 이 주제의 고유 창 |

★★★ 둘째 창이 본체다. `source()` 는 **구현해 두고도 아무도 안 불러 보면 없는 것과 같다** —
std 는 사슬을 **자동으로 찍어 주지 않는다.** 그래서 이 주제는 **직접 걸어서 출력으로 보인다.**

### (1) 기본형 — 열거형 + `Display` + `Error`

**언제 쓰나** — 내 모듈이 실패할 수 있는 **이유가 두 가지 이상**일 때.

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

- `#[derive(Debug)]` 는 **파생**, `Display` 와 `Error` 는 **직접 쓴다**.
  `Error` 트레이트가 `Debug + Display` 를 **요구**하기 때문에 셋이 한 벌이다.
- ★ `impl Error for ConfigError {}` 가 **비어 있다** — `source()` 의 기본 구현이 `None` 이라 그렇다.
  출력의 `source        false` 가 그 확인이다.
- ★★ `{}` 와 `{:?}` 가 **다른 문장**을 낸다 — 앞엣것은 내가 쓴 한국어 문장, 뒤엣것은 파생된 구조체 꼴이다.
  **`{}` 는 사용자·로그, `{:?}` 는 개발자·`main`** 이라는 분업이 여기서 정해진다((6)).
- ★ 변형에 **필드 이름을 붙인 것**(`OutOfRange { key, got, max }`)에 주의 —
  호출자가 `match` 에서 **필요한 필드만** 꺼낼 수 있고, 나중에 필드를 더해도 `..` 로 덜 깨진다.

### (2) ★★★ `source()` 사슬을 실제로 걷기

**언제 쓰나** — 아래 층 오류를 감싸 올릴 때. 감싸면 **원인이 가려지므로** 링크를 남겨야 한다.

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

- ★★★ **사슬이 3층이다** — `StartupError` → `ConfigError` → `ParseIntError`.
  마지막 층의 `source()` 가 `None` 이라 루프가 끝난다.
- ★★ **`Display` 만 찍으면 맨 위 한 줄뿐이다** — `설정 읽기 단계에서 기동에 실패했다`.
  **왜 실패했는지는 안 나온다.** 이것이 `source` 를 구현해야 하는 이유이자,
  **구현만 하고 안 걷으면 소용없는 이유**다.
- ★★ **`Debug` 는 반대로 전부 보여 준다** — `StartupError { stage: …, cause: ConfigError { …, cause: ParseIntError { … } } }`.
  ★ 파생 `Debug` 가 **중첩 구조를 그대로** 찍기 때문이다. 그래서 `main` 이 `Err` 를 낼 때는
  사슬이 어느 정도 보인다((6)).
- 사슬을 걷는 코드는 이 모양이 표준이다 — `while let Some(s) = cur { … cur = s.source(); }`.
  ★ std 에 **사슬을 찍어 주는 함수는 없다**(`Error::sources()` 이터레이터는 아직 불안정).
- ★ `source()` 의 반환 타입이 `Option<&(dyn Error + 'static)>` 인 것에 주의 —
  `'static` 경계가 붙어 있어 **다운캐스트가 가능**하다((4)).

### (3) ★★ `Box<dyn Error>` 로 받으면 — 변형을 못 본다

**언제 쓰나** — 편하다고 `Box<dyn Error>` 를 쓴 뒤, 호출자가 갈래로 분기하려 할 때.

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

- ★★★ **E0308 이 두 번** 난다. `` expected `Box<dyn Error>`, found `ConfigError` `` —
  **봉투에 담은 순간 타입이 `Box<dyn Error>` 로 바뀌었고, 패턴은 그 타입에만 맞출 수 있다.**
- ★★ **열거형의 변형이 사라진 것이 아니라 보이지 않게 된 것**이다. 값은 그대로 안에 있다 —
  다만 **컴파일러가 그 사실을 모른다**(그것이 `dyn` 의 뜻이다).
- ★ 진단이 `` unit variant defined here `` 로 내 변형 선언을 가리켜 준다 —
  **무엇을 하려 했는지는 알지만 그렇게는 안 된다**는 말이다.

### (4) ★ 되찾는 법 — `downcast_ref`

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

- **되찾힌다.** 세 경우 모두 원래 타입으로 다시 갈라졌다.
- ★★ **대가가 셋이다.**
  ① **타입을 내가 적어야 한다**(`downcast_ref::<ConfigError>()`). 후보를 **빠뜨려도 컴파일이 통과**한다.
  ② **완전성 검사가 없다** — `else` 로 떨어지는 경우를 내가 챙겨야 한다([**18번 주제**](../18-match-and-exhaustiveness/)와 정반대다).
  ③ **런타임 검사**다(`TypeId` 비교). 컴파일 시점에 아무것도 보장되지 않는다.
- ★ 그래서 규칙은 이렇다 — **호출자가 분기해야 하면 처음부터 열거형으로 준다.**
  `Box<dyn Error>` 는 「분기하지 않고 보고만 할 것」이라는 **선언**에 가깝다.
- ★ 세 번째 경우(`ParseIntError`)가 보여 주듯 **std 오류도 같은 방식으로 되찾는다.**

### (5) `?` 가 `Box<dyn Error>` 로는 거의 다 변환해 준다

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

- 한 함수 안에서 **세 가지 오류**(`ParseIntError`·`io::Error`·내 `MyError`)가 전부 `?` 로 올라갔다.
  ★ std 에 `impl<E: Error + 'static> From<E> for Box<dyn Error>` 가 있기 때문이고,
  이것은 [**22번 주제**](../22-result-question-mark-and-from/)의 `From` 규칙이 그대로 적용된 것이다.
- ★ `Err(MyError("내가 만든 실패"))?` 처럼 **`?` 를 `Err` 에 직접 붙이는** 관용구도 같은 변환을 쓴다.
- `1 Err  No such file or directory (os error 2)` 가 `io::Error` 의 `Display` 다 — OS 메시지가 그대로 들어 있다.

**같은 코드를 구체 타입으로 바꾸면 막힌다.**

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

- ★★ 에러가 **둘**이다. `"8080".parse()` 쪽은 **E0271**(타입을 추론에 맡긴 자리),
  `read_to_string` 쪽은 **E0277**(`` `?` couldn't convert the error to `MyError` ``).
  ★ **같은 결함이 두 번호로 갈리는 것**은 22번 (3)에서 본 그대로다.
- ★★★ 그리고 여기서도 `= note:` 가 증언한다 —
  `` the question mark operation (`?`) implicitly performs a conversion on the error value using the `From` trait ``.
- ★ 그래서 **구체 타입으로 가려면 `From` 을 층마다 써야 한다.** 그 비용이 아까우면 `Box<dyn Error>` 이고,
  그 비용이 **호출자의 선택권을 사는 값**이라고 보면 열거형이다.

### (6) `main` 이 `Err` 를 낼 때 찍히는 것은 `Debug` 다

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

- ★★★ **`Display` 를 구현해 뒀는데 그 문장이 안 나왔다.** 나온 것은 `Debug` 쪽이다 —
  소스에서 두 구현이 **서로 다른 문장**을 내도록 해 두었기 때문에 **어느 쪽이 쓰였는지 출력만으로 판정된다.**
- ★★ 그래서 오류 타입을 설계할 때 **`Debug` 도 사람이 읽을 만하게** 만드는 선택지가 있다.
  `#[derive(Debug)]` 대신 **직접 구현**하면 `main` 의 출력이 읽을 만해진다(이 블록이 그 실험이다).
- ★ 종료 코드는 **1** 이다([**23번 주제**](../23-panic-vs-result/)의 표).
- ★ 대안 — `main` 에서 `eprintln!("{}", e)` 로 `Display` 를 찍고 **사슬까지 걸어** 보여 준 뒤
  `process::exit(1)` 을 부르는 것. 실무의 CLI 는 대개 이쪽이다.

### (7) 호출자가 갈래로 복구한다 — 열거형의 값

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

- 세 변형이 **서로 다른 복구 행동**으로 이어졌다 — 기본값으로 계속 · 재시도 예약 · 위로 올림.
  ★ **이것이 `Box<dyn Error>` 로는 못 하는 일**이다((3)).
- ★ `Err(e @ FetchError::Corrupt { .. })` 는 **`@` 바인딩**이다 — 변형을 확인하면서 값 전체도 잡는다
  ([**19번 주제**](../19-pattern-syntax-guards-bindings-and-match-ergonomics/)).
- ★★ **변형을 늘리면 호출자의 `match` 가 깨진다**([**18번 주제**](../18-match-and-exhaustiveness/)) — 이것은 **비용이자 안전망**이다.
  공개 API 라면 `#[non_exhaustive]` 를 붙여 **호출자가 `_` 팔을 쓰도록 강제**하는 선택지가 있다((8)).

### (8) 외부 크레이트는 이름만 — 표준으로 어디까지 되나

- **`thiserror`** — `Display` 와 `Error`/`source` 구현을 **파생 매크로로** 만들어 준다.
  (1)·(2)에서 손으로 쓴 그 `impl` 들이 줄어드는 것이고, **만들어지는 타입의 성질은 같다.**
- **`anyhow`** — `Box<dyn Error>` 자리에 쓰는 **애플리케이션용 오류 타입**. 문맥 붙이기(`context`)와 백트레이스가 붙는다.
- ★★ **이 주제는 그 둘을 쓰지 않는다.** 기준 소스가 std 가 아니게 되고(네트워크로 받아야 한다),
  무엇보다 **표준만으로 되는 것과 크레이트가 줄여 주는 것을 구분하지 못하게 된다.**
- ★ 실무의 대략적인 관례 — **라이브러리는 `thiserror`(열거형 유지), 애플리케이션은 `anyhow`(봉투)**.
  그 구분선이 정확히 (3)\~(7)에서 본 **「호출자가 분기하나」** 다.
- **`#[non_exhaustive]`** 는 std 기능이다. 공개 오류 열거형에 붙이면 **하위 호환을 지키며 변형을 늘릴 수 있다.**

## 문법 — 형태와 규칙

```text
   오류 타입 한 벌의 최소 형태

   #[derive(Debug)]                      ← Error 가 Debug 를 요구한다
   enum MyError { A, B { src: OtherError } }

   impl std::fmt::Display for MyError {  ← Error 가 Display 도 요구한다
       fn fmt(&self, f: &mut Formatter<'_>) -> fmt::Result { write!(f, "…") }
   }

   impl std::error::Error for MyError {
       fn source(&self) -> Option<&(dyn Error + 'static)> {   ← 선택. 기본은 None
           match self { MyError::B { src } => Some(src), _ => None }
       }
   }

   사슬을 걷는 표준 관용구

   let mut cur: Option<&(dyn Error + 'static)> = Some(&e);
   while let Some(s) = cur { println!("{}", s); cur = s.source(); }

   봉투와 되꺼내기

   fn f() -> Result<T, Box<dyn Error>>        ← 어떤 오류든 ? 로 받는다
   e.downcast_ref::<MyError>() -> Option<&MyError>    ← 런타임 타입 검사
   e.downcast::<MyError>()     -> Result<Box<MyError>, Box<dyn Error>>   ← 소유권째
```

- **`Error` 트레이트는 `Debug + Display` 를 요구한다.** 셋을 한 벌로 생각한다.
- ★ **`source()` 의 반환에는 `'static` 이 붙는다** — 다운캐스트(`TypeId`)가 가능하려면 필요하다.
- **`Box<dyn Error>` 는 `Send`/`Sync` 가 아니다.** 스레드를 넘겨야 하면 `Box<dyn Error + Send + Sync>` 를 쓴다.
- ★ **`main` 의 오류 타입에는 `Debug` 가 필요하다**(`Termination` 계약 — 23번).
- **`?` 는 `Box<dyn Error>` 로 자동 변환된다** — std 의 `From` impl 덕분이다((5)).

## 어디서 틀리나

| 증상 | 진짜 원인 | 고치는 법 |
|---|---|---|
| ★★ `Box<dyn Error>` 를 `match` 하려는데 E0308 | 봉투에 담는 순간 타입이 바뀌었다 | 열거형으로 돌려주거나 `downcast_ref`((3)·(4)) |
| 오류 메시지가 **원인을 안 보여 준다** | `Display` 는 자기 층만 말한다 | `source()` 를 걸고 **걸어서 찍는다**((2)) |
| `source()` 를 구현했는데 **아무 데도 안 나온다** | std 가 자동으로 안 찍는다 | 직접 `while let` 으로 걷는다((2)) |
| `main` 이 낸 오류가 **구조체 꼴**로 나온다 | `Error:` 뒤는 `Debug` 다 | `Debug` 를 직접 구현하거나 직접 찍는다((6)) |
| ★ 구체 오류 타입에 `?` 가 안 먹는다 | 층마다 `From` 이 필요하다 | `impl From` 또는 `Box<dyn Error>`((5)·22번) |
| `downcast_ref` 가 **늘 `None`** 이다 | 타입이 다르다(감싸 놓고 안쪽 타입을 물었다) | 사슬을 걸어 각 층에 물어본다 |
| 오류 열거형에 변형을 더했더니 **호출자가 깨진다** | 완전성 검사 — **정상이다** | 공개 API 면 `#[non_exhaustive]`((7)·(8)) |
| ★ 스레드 경계를 넘길 때 컴파일 거부 | `Box<dyn Error>` 는 `Send`/`Sync` 가 아니다 | `Box<dyn Error + Send + Sync>` |

★★ **가장 흔한 설계 실수는 「라이브러리가 `Box<dyn Error>` 를 반환하는 것」이다.**
편하지만 **호출자에게서 분기할 능력을 빼앗는다.** 반대로 애플리케이션이 층마다 열거형을 만드는 것도
**아무도 안 쓰는 변형을 유지보수하는 비용**이 된다.

## 구현 세부사항 대 언어 보장

| 항목 | 무엇인가 | 근거 |
|---|---|---|
| `Error` 가 `Debug + Display` 를 요구하는 것 | ★ **std 계약** | std 문서 |
| `source()` 의 **기본 구현이 `None`** | ★ **std 계약** | (1)의 실측(`source false`) |
| `?` 가 `Box<dyn Error>` 로 변환되는 것 | ★ **std 의 `From` impl** — 계약이다 | (5)의 실측 |
| `main` 의 `Err` 가 **`Debug` 로 찍히고 종료 코드 1** | ★ **std 계약**(`Termination`) | (6)의 실측 |
| `downcast_ref` 가 `TypeId` 로 판정하는 것 | ★ **문서화된 동작** — 런타임 검사다 | (4)의 실측 |
| `ParseIntError`·`io::Error` 의 **`Display` 문구** | ★ **구현 세부** — std 판·OS 에 달렸다 | (2)·(5)의 실측 |
| `No such file or directory (os error 2)` | ★ **OS 세부** — 다른 OS 면 문구도 번호도 다르다 | (5)의 실측 |
| 파생 `Debug` 의 **중첩 출력 형식** | ★ **구현 세부** | (2)의 실측 |
| 에러 번호가 E0271 이냐 E0277 이냐 | ★ **구현 세부** | (5)의 실측 |

## 언제 쓰고 언제 안 쓰나

- **열거형 오류를 쓴다** — **라이브러리**, 호출자가 분기해야 할 때, 실패 이유가 **유한하고 이름을 붙일 수 있을** 때.
- **`Box<dyn Error>` 를 쓴다** — **애플리케이션·`main`·프로토타입**, 그리고 **보고하고 끝낼** 때.
- **`source()` 를 건다** — 아래 층 오류를 **감쌀 때마다**. 안 걸면 원인이 사라진다.
- **`Display` 를 짧게 쓴다** — 자기 층만. 사슬이 원인을 말해 준다. **원인을 `Display` 에 이어 붙이면 중복으로 찍힌다.**
- ★ **`Debug` 를 직접 구현한다** — `main` 이 그 오류를 낼 수 있고, 그 출력이 **사용자에게 보일 때**.
- ★ **`#[non_exhaustive]` 를 붙인다** — 공개 오류 열거형에. 나중에 변형을 더할 여지를 남긴다.

## 핵심 문장

- ★★★ **오류 타입 설계는 「호출자가 분기하나, 보고만 하나」 한 질문으로 갈린다.**
- ★★ **`Box<dyn Error>` 는 편의를 주고 갈래를 가져간다.** 되찾으려면 타입을 내가 적어야 하고 완전성 검사도 없다.
- ★★ **`Display` 는 자기 층만 말한다.** 원인은 `source()` 사슬을 **직접 걸어야** 보인다 — std 가 안 찍어 준다.
- ★ **`main` 이 찍는 것은 `Debug` 다.** 그래서 `Debug` 도 설계 대상이다.
- **`thiserror`·`anyhow` 는 이 구조를 줄여 주는 도구일 뿐, 구조 자체는 표준이 다 정해 둔 것이다.**

## 관련 자료

- [**23번 주제** — `panic!` 대 `Result`](../23-panic-vs-result/) —
  ★ **경계**: **어느 길로 갈지**는 거기, **`Result` 로 가기로 한 뒤의 `E` 설계**는 여기다.
- [**22번 주제** — `Result` 와 `?`·`From`](../22-result-question-mark-and-from/) —
  ★ **경계**: `?` 의 변환 규칙은 거기가 정본이고, 여기는 **그 규칙 위에서 타입을 설계하는 쪽**이다.
- [**21번 주제** — `Option` 과 조합 메서드](../21-option-and-combinators/) — 「없음」에는 이유가 없다. 이유를 담기 시작하는 곳이 `Result` 다.
- [**17번 주제** — 열거형](../17-enums-and-data-carrying-variants/) · [**18번 주제** — `match` 와 완전성](../18-match-and-exhaustiveness/) —
  오류 열거형이 얻는 **완전성 검사**의 정본이다.
- [목록의 **33번 주제**](../33-dyn-trait-objects-and-object-safety/) — `dyn Trait` 와 객체 안전성. `Box<dyn Error>` 가 왜 `Box` 여야 하는지의 정본.
- 목록의 **48번 주제** — `Display`/`Debug` 구현과 포맷. 여기서는 오류에 필요한 만큼만 썼다.
- [`ops-patterns/failure-modes/`](../../../../../ops-patterns/failure-modes/) —
  ★ **경계**: 실패 모드 **분류**는 거기, 여기는 **그 분류를 타입으로 적는 법**이다.
- Go 의 오류 래핑 — Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **24번**(`%w`·`errors.Is`/`As`/`Join`).
  ★ **대비**: Go 의 `Unwrap()` 이 `source()` 이고, `errors.As` 가 `downcast_ref` 다. **구조가 거의 같다** —
  다른 점은 Rust 가 **`match` 로 완전성 검사를 얹을 수 있다**는 것이다.
- Java 의 예외 — [`java/syntax/25-exceptions/`](../../../java/syntax/25-exceptions/).
  ★ **대비**: `getCause()` 가 `source()` 이고, **스택 트레이스가 언어에 내장**돼 있다.
  Rust 의 오류 값에는 **스택 트레이스가 없다**(`RUST_BACKTRACE` 는 패닉 쪽이다) — 그래서 `anyhow` 같은 크레이트가 그 자리를 채운다.

## 용어 풀이

- **`std::error::Error`** — 오류 타입의 표준 트레이트. `Debug + Display` 를 요구한다.
- **`source()`** — 이 오류를 일으킨 아래 층 오류. 기본 구현은 `None`.
- **오류 사슬(error chain)** — `source()` 를 따라 이어지는 원인들의 줄.
- **`Box<dyn Error>`** — 어떤 오류든 담는 동적 봉투.
- **다운캐스트(downcast)** — 동적 봉투에서 구체 타입을 지정해 되꺼내는 것. 런타임 검사다.
- **`#[non_exhaustive]`** — 열거형에 변형이 더 생길 수 있다고 선언하는 어트리뷰트.
- **`thiserror`·`anyhow`** — 각각 라이브러리·애플리케이션 오류를 줄여 주는 외부 크레이트. **이 주제에서는 이름만 쓴다.**

## 더 들어가면

- **`Error::sources()`** — 사슬을 이터레이터로 주는 API. **아직 불안정**이라 여기서는 `while let` 으로 걸었다.
- **`Box<dyn Error + Send + Sync + 'static>`** — 스레드 경계를 넘는 오류 봉투. 실무에서 자주 본다.
- **`std::io::Error` 의 구조** — `ErrorKind` 라는 **열거형 축**과 OS 코드·메시지를 같이 갖는다. 설계 참고감이다.
- **`From` 을 오류 변환에 쓸 때의 고아 규칙** — 남의 오류를 남의 타입으로 변환하는 impl 은 못 쓴다([목록의 **26번 주제**](../26-orphan-rule-and-newtype/)).
- **백트레이스** — `std::backtrace::Backtrace` 를 오류 구조체 필드로 들고 다니는 패턴이 있다.
