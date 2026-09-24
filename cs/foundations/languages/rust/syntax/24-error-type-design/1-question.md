# rust/syntax/24 — 오류 타입 설계 — 열거형 오류·`Error` 트레이트·`source`·`Box<dyn Error>` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 던지는 법 — `rustc --edition 2021 ex.rs -o ex && ./ex`.
> ★★ **`--edition` 을 빼면 에디션 2015 로 돌아간다** — 답을 맞춰도 다른 언어를 컴파일한 것이다.
> ★★ **이 주제는 외부 크레이트를 하나도 쓰지 않는다.** `thiserror`·`anyhow` 는 이름만 묻는다.
> ★ 「무엇이 되나」보다 **「무엇을 잃나」** 를 묻는 문항이 많다.

> ★ 아래 코드 펜스의 **첫 줄 `// bNN-….rs` 는 캡처 원본 파일 이름**이고, 그 아래 `// ex.rs` 가 **컴파일할 때의 이름**이다.
> 캡처 스크립트가 원본을 `ex.rs` 로 복사해 던지므로 **진단에 박히는 파일명은 언제나 `ex.rs`** 다.
> 펜스가 실파일과 한 글자도 같은지는 `check-source-fences.py` 가 기계로 대조했다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 세 층을 쌓고 원인을 따라 걸으면 (예측)

```rust
// b24-02.rs
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
```

- `사슬 길이` 줄에는 무엇이 찍히는가?
- 각 층의 `Display` 문장을 **순서대로** 적을 수 있는가?
- ★★ `Display` 만 찍은 줄과 `Debug` 로 찍은 줄은 **얼마나 다른가**?
- ★ 루프는 무엇을 보고 멈추는가?
- std 에 이 사슬을 **찍어 주는 함수**가 있는가?

### 2. ★★ 봉투에 담은 오류를 변형으로 가르려 하면 (예측)

```rust
// b24-03.rs
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
```

- 컴파일되는가? 안 되면 **에러 번호**와 **개수**는?
- 진단이 `expected` / `found` 로 적는 두 타입은 각각 무엇인가?
- ★★ 열거형의 변형은 **사라진 것인가 안 보이는 것인가**?
- 진단이 내 열거형 선언을 가리키며 뭐라고 적는가?

### 3. ★ 봉투에서 원래 타입을 되꺼내면 (예측)

```rust
// b24-04.rs
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
```

- 세 줄의 출력은 각각 어떻게 갈리는가?
- `downcast_ref` 는 **무엇을 근거로** 판정하는가 — 컴파일 시점인가 런타임인가?
- ★★ 이 방식이 `match` 에 비해 **잃는 것 셋**을 댈 수 있는가?
- std 오류(`ParseIntError`)도 같은 방식으로 되찾아지는가?

### 4. ★ 서로 다른 오류 셋을 한 함수에서 `?` 로 올리면 (예측)

```rust
// b24-05.rs
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
```

- 네 줄의 출력은 각각 무엇인가?
- ★ 세 오류 타입이 전부 통과하는 이유는 무엇인가 — 어떤 impl 덕분인가?
- `Err(MyError(…))?` 처럼 `Err` 에 `?` 를 붙이는 것은 무슨 뜻인가?
- 찍히는 것은 `Display` 인가 `Debug` 인가?

### 5. ★★ 같은 코드를 구체 오류 타입으로 바꾸면 (예측)

```rust
// b24-06.rs
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
```

- 에러는 **몇 개**이며 번호는 각각 무엇인가?
- ★ 두 번호가 갈리는 이유를 22번의 어느 관찰과 이어 설명할 수 있는가?
- ★★ 진단의 `= note:` 는 `?` 에 대해 무엇을 말하는가?
- 이 코드를 통과시키는 방법은 **둘**이다. 무엇인가?

### 6. ★★ `main` 이 `Err` 를 낼 때 찍히는 표면 (예측)

```rust
// b24-07.rs
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
```

- 표준 오류에 무엇이 찍히는가 — **한 글자도 안 틀리게** 적을 수 있는가?
- ★★★ 이 소스에는 `Display` 와 `Debug` 가 **서로 다른 문장**을 내도록 돼 있다. 어느 쪽이 나오는가?
- 종료 코드는 얼마인가?
- 사용자에게 `Display` 문장을 보여 주려면 무엇을 해야 하는가 — **셋** 중 하나를 대라.

### 7. 열거형 오류와 `Box<dyn Error>` 중 무엇을 고르나 (왜)

- 고르는 기준을 **한 질문**으로 줄일 수 있는가?
- 라이브러리가 `Box<dyn Error>` 를 반환하면 호출자에게서 **무엇을 빼앗는가**?
- 애플리케이션이 층마다 열거형을 만들면 무엇이 비용이 되는가?
- 공개 오류 열거형에 변형을 더하면 호출자에게 무슨 일이 생기며, 그것을 완화하는 어트리뷰트는 무엇인가?

### 8. 네 표면의 분업 (경계)

- `Error` 트레이트가 **요구하는** 트레이트 둘은 무엇인가?
- `source()` 의 **기본 구현**은 무엇인가? 그것을 실행으로 확인할 수 있는가?
- `Display` 에 원인까지 이어 붙이면 무엇이 문제인가?
- `source()` 의 반환 타입에 `'static` 이 붙어 있는 이유는 무엇인가?

### 9. 호출자가 갈래로 복구한다 (경계)

- 오류 변형 셋에 서로 다른 복구 행동을 붙이는 코드를 그려 볼 수 있는가?
- `Err(e @ FetchError::Corrupt { .. })` 에서 `@` 는 무엇을 하는가?
- 변형에 **이름 있는 필드**를 쓰면 무엇이 편해지는가?
- 이 코드를 `Box<dyn Error>` 로 바꾸면 무엇을 다시 써야 하는가?

### 10. 크레이트·다른 언어와 잇기 (연결)

- `thiserror` 와 `anyhow` 는 각각 **무엇을 줄여 주는가**? 각각 라이브러리·애플리케이션 중 어느 쪽인가?
- 그 둘을 안 쓰고 표준만으로 쓴 이 주제에서 **손으로 쓴 impl** 은 무엇무엇인가?
- Go 의 `Unwrap()`·`errors.As` 는 Rust 의 무엇에 대응하는가?
- Java 의 `getCause()` 와 `source()` 는 같은 것인가? **스택 트레이스**는 어느 쪽에 있는가?
- `Box<dyn Error>` 를 스레드 경계 너머로 보내려면 무엇을 더 붙여야 하는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
