# rust/syntax/23 — `panic!` 대 `Result` — 어디서 끝낼 것인가 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [std — `macro panic!`](https://doc.rust-lang.org/std/macro.panic.html) ·
> [std — `panic::catch_unwind`](https://doc.rust-lang.org/std/panic/fn.catch_unwind.html) ·
> [std — `process::exit`](https://doc.rust-lang.org/std/process/fn.exit.html) ·
> [std — `trait Termination`](https://doc.rust-lang.org/std/process/trait.Termination.html) ·
> [Cargo Book — `profile.panic`](https://doc.rust-lang.org/cargo/reference/profiles.html#panic) ·
> [rustc Book — `-C panic`](https://doc.rust-lang.org/rustc/codegen-options/index.html#panic).
> **실행 검증** — 이 문서의 모든 출력·에러는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서\
> **`rustc --edition 2021 ex.rs -o ex`**(일부 블록은 `-C panic=abort` 또는 `-O` 를 더해) 실제로 돌려 받은 것이다.\
> ★★ **`rustc ex.rs` 만 쓰면 에디션 2015 다** — 에디션을 안 밝힌 결과는 다른 언어를 컴파일한 것과 같다.\
> ★★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
> ★ **종료 코드는 `./ex` 의 것**이고 캡처가 `(종료 코드 N)` 으로 블록 끝에 적었다.
> **버전** — `panic!`·`assert!`·`debug_assert!`·`process::exit` 는 **1.0.0** 부터.\
> **`catch_unwind` 는 1.9.0**, **`main` 이 `Result` 를 반환할 수 있는 것은 1.26.0** 부터다. **전부 에디션과 무관하다.**
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | 패닉 첫 줄 `thread 'main' (…)` 괄호 안의 OS 스레드 id | 실행마다 커널이 주는 번호다 — 이 주제의 패닉 블록 넷에 전부 나온다 |
| **흔들린다** | `0x…` 주소 | 실행마다 다르다 |
| 안 흔들린다 | ★★ **종료 코드 101 · 1 · 2 · 134** | 이 주제의 결론 자체다 |
| 안 흔들린다 | 패닉 **메시지 본문**·`파일:줄:칸`·`note: run with RUST_BACKTRACE=1 …` | 같은 소스·같은 판에서 고정이다 |
| 안 흔들린다 | `drop` 이 찍히는 **줄과 순서** | 되감기 전략이 정한다 — 이 주제의 핵심 근거다 |
| 안 흔들린다 | `Error: ` 로 시작하는 `main` 의 실패 출력 | 런타임이 `{:?}` 로 찍는다 |

## 한눈에 — 쉽게 말하면

**「호출자가 손쓸 수 있는 실패」와 「이미 뭔가 잘못된 상태」는 다른 길로 끝낸다.**

| 비유 | 실체 |
|---|---|
| 「**양식에 사유를 적어 돌려보낸다**」 | **`Result`** — 호출자가 읽고 **복구할 수 있다** |
| 「**여기서 셔터를 내린다**」 | **`panic!`** — 호출자가 손쓸 것이 없다. 종료 코드 **101** |
| 「셔터를 내리며 **정리는 하고 간다**」 | `panic = "unwind"`(기본) — **`Drop` 이 돈다** |
| ★ 「셔터도 안 내리고 **그냥 쓰러진다**」 | `panic = "abort"` — **`Drop` 이 안 돈다**. 종료 코드 **134** |
| 「내가 정한 번호로 **바로 나간다**」 | `std::process::exit(n)` — ★ **`Drop` 이 안 돈다** |
| 「`main` 이 사유서를 들고 나온다」 | `main` 이 `Err` 반환 — `Error: {:?}` + 종료 코드 **1** |
| 「쓰러지는 것을 **받아 낸다**」 | `catch_unwind` — 잡을 수는 있다. 그러나 **예외 처리가 아니다** |

- ★★★ **이 주제의 축은 「종료 코드」다.** 세 경로가 다른 번호를 남기므로 **셸에서 구분된다.**
- ★★ **`unwrap` 은 「패닉을 고르는 것」이다.** 21번에서 본 `unwrap`/`expect` 는 문법이 아니라 **설계 결정**이다.
- ★ **라이브러리는 패닉하지 않는다** — 관례다. 호출자의 프로세스를 **내 판단으로 죽이지 않는다**.
  다만 **호출 규약을 어긴 것(버그)** 은 예외다 — 그것이 `assert!` 의 자리다((1)).

```text
   프로그램이 끝나는 네 가지 길과 종료 코드

   ┌──────────────────────┬──────────────┬───────────┬──────────────┐
   │ 길                   │ Drop 이 도나 │ 종료 코드 │ 누가 고르나  │
   ├──────────────────────┼──────────────┼───────────┼──────────────┤
   │ 정상 반환            │ 돈다         │ 0         │ —            │
   │ panic! (unwind 기본) │ ★ 돈다       │ 101       │ 런타임       │
   │ panic! (abort)       │ ★ 안 돈다    │ 134       │ 런타임(SIGABRT)│
   │ main 이 Err 반환     │ 돈다         │ 1         │ 런타임       │
   │ process::exit(n)     │ ★ 안 돈다    │ n         │ ★ 내가       │
   └──────────────────────┴──────────────┴───────────┴──────────────┘


   어디서 끝낼 것인가 — 판단의 경로

     실패가 생겼다
         │
         ├─ 밖에서 온 값 때문인가?(사용자 입력·파일·네트워크·파싱)
         │     └─ 예 → Result 로 돌려보낸다 ── 호출자가 고친다
         │
         └─ 내 코드의 약속이 깨진 것인가?(인덱스·불변식·호출 규약)
               └─ 예 → panic!/assert! ── 고칠 사람은 프로그래머다
```

> **패닉(panic)** — 복구 불가로 판단해 현재 스레드를 끝내는 것.\
> 기본 전략은 **되감기(unwind)** 이고, 되감으며 스택의 값들에 `Drop` 을 돌린다.

> **되감기(unwind)** — 스택 프레임을 역순으로 풀며 정리 코드를 실행하는 것.\
> 「`Drop` 이 도는가」가 이 전략의 관찰 가능한 결과다((3)).

> **중단(abort)** — 되감지 않고 프로세스를 즉시 죽이는 것. `SIGABRT` 가 난다.\
> `-C panic=abort`(rustc) 또는 `[profile.*] panic = "abort"`(Cargo)로 고른다.

> **복구 가능한 실패(recoverable)** — 호출자가 다르게 행동할 수 있는 실패. `Result` 로 낸다.

> **복구 불가능한 실패(unrecoverable)** — 프로그램의 가정이 이미 깨진 상태. `panic!` 으로 끝낸다.

## 이 주제가 답하려는 질문

1. **어느 실패를 어느 길로 보내나** — 경계를 어디에 긋나((1)).
2. ★★ **각 길이 남기는 자국은 무엇인가** — **종료 코드**와 **`Drop` 이 도는가**((2)\~(5)).
3. **`unwrap`/`expect`/`assert!` 를 써도 되는 자리는 어디인가** — 그리고 메시지에 무엇을 적나((7)·(8)).

★ [**21번**](../21-option-and-combinators/)·[**22번 주제**](../22-result-question-mark-and-from/)가 「값으로 다루는 법」이었다면 여기는 **「값으로 안 다루기로 결정하는 자리」** 다.

## 동작 방식

### (0) 이 주제가 쓰는 네 창

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **종료 코드 읽기** | 네 길이 **셸에서 구분된다** — 101·1·2·134 | ★ 이 주제의 고유 창 |
| ★★ **`Drop` 이 찍는 줄 세기** | 되감기냐 중단이냐 — **같은 소스를 두 플래그로** 던진다 | [**20번 주제**](../20-if-let-while-let-let-else-and-let-chains/)에서 쓰던 창 |
| ★ **`catch_unwind` 로 받아 보기** | 패닉이 **값으로 잡히는가** — 잡은 뒤 무엇이 남나 | ★ 이 주제의 고유 창 |
| ★ **최적화 수준을 바꿔 다시 던지기** | `debug_assert!` 가 **사라지는 것** | 이 갈래의 공통 창(`-O`) |

★★★ 첫 창이 본체다. 「패닉은 심각하고 `Result` 는 가볍다」 같은 형용사 대신
**셸이 읽는 숫자**로 네 길을 가른다. ★ 두 번째 창은 **같은 소스에 플래그만 바꿔 던져야** 뜻이 있다 —
소스가 다르면 `Drop` 차이가 플래그 때문인지 코드 때문인지 못 가른다.

### (1) 경계 — 밖에서 온 것과 안에서 깨진 것

**언제 쓰나** — 함수를 쓸 때마다. 이 판단이 이 주제의 전부다.

```text
===== 소스: ex.rs =====
// ex.rs
// 경계 — 밖에서 온 것은 Result, 안에서 깨진 것은 panic
#[derive(Debug)]
enum ParseError {
    Empty,
    NotANumber(String),
}

// 「라이브러리」 쪽 — 사용자 입력은 언제든 틀릴 수 있다. 패닉하지 않는다.
fn parse_port(raw: &str) -> Result<u16, ParseError> {
    if raw.is_empty() {
        return Err(ParseError::Empty);
    }
    raw.parse::<u16>().map_err(|_| ParseError::NotANumber(raw.to_string()))
}

// 「내부」 쪽 — 호출 규약을 어긴 것은 버그다. 여기서 끝낸다.
fn percent(part: u32, whole: u32) -> u32 {
    assert!(whole > 0, "percent 는 whole > 0 을 요구한다(호출자 버그)");
    part * 100 / whole
}

fn main() {
    for raw in ["8080", "", "팔공팔공", "99999"] {
        match parse_port(raw) {
            Ok(p) => println!("입력 {:?} -> 포트 {}", raw, p),
            Err(ParseError::Empty) => println!("입력 {:?} -> 사용자에게 알린다: 비었다", raw),
            Err(ParseError::NotANumber(got)) => {
                println!("입력 {:?} -> 사용자에게 알린다: 수가 아니다({})", raw, got)
            }
        }
    }
    println!("내부 계산 {}%", percent(3, 4));
    println!("프로그램은 정상 종료한다");
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
입력 "8080" -> 포트 8080
입력 "" -> 사용자에게 알린다: 비었다
입력 "팔공팔공" -> 사용자에게 알린다: 수가 아니다(팔공팔공)
입력 "99999" -> 사용자에게 알린다: 수가 아니다(99999)
내부 계산 75%
프로그램은 정상 종료한다
(종료 코드 0)
```

- **`parse_port` 는 패닉하지 않는다.** 빈 문자열·한글·범위 초과가 전부 **정상적으로 일어날 수 있는 입력**이고,
  호출자는 「다시 입력받기」·「기본값 쓰기」로 **복구할 수 있다.**
- **`percent` 는 `assert!` 로 끝낸다.** `whole > 0` 은 **호출 규약**이고, 그걸 어긴 쪽은 사용자가 아니라 **프로그래머**다.
  `Result` 로 돌려줘 봐야 호출자가 할 수 있는 일이 없다.
- ★★ 판단 기준은 **「누가 고칠 수 있나」** 다 — 사용자·운영자가 고칠 수 있으면 `Result`,
  **코드를 고쳐야만** 되면 `panic!`.
- ★ 이 프로그램은 종료 코드 **0** 으로 끝난다. **네 번 실패했는데도** 그렇다 —
  `Result` 로 다룬 실패는 **프로그램의 실패가 아니다.**

### (2) 패닉의 자국 — 종료 코드 101

```text
===== 소스: ex.rs =====
// ex.rs
// 패닉으로 끝나는 프로그램의 종료 코드 — 마커는 전부 표준 오류로 찍는다
fn ratio(hit: u32, total: u32) -> f64 {
    if total == 0 {
        panic!("total 이 0 이다 — 호출자가 빈 표를 넘겼다(프로그램 버그)");
    }
    hit as f64 / total as f64
}

fn main() {
    eprintln!("A {:.2}", ratio(3, 4));
    eprintln!("B {:.2}", ratio(3, 0));
    eprintln!("C 여기는 안 온다");
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
A 0.75

thread 'main' (870287) panicked at ex.rs:5:9:
total 이 0 이다 — 호출자가 빈 표를 넘겼다(프로그램 버그)
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
(종료 코드 101)
```

- ★★ **종료 코드 101** 이다. 셸에서 `./ex; echo $?` 로 확인된다.
- 첫 줄 `thread 'main' (…) panicked at ex.rs:5:9:` 의 **괄호 안 숫자만** 실행마다 바뀐다(머리말의 표).
- **`C 여기는 안 온다` 가 안 찍혔다** — 패닉은 그 스레드를 거기서 끝낸다.
- ★ 마커를 `eprintln!` 으로 찍은 이유 — 패닉은 **표준 오류**로 나간다. 한 블록 안에서 스트림을 섞지 않는다.

### (3) ★★ 되감기에서는 `Drop` 이 돈다 — 중단에서는 안 돈다

**언제 쓰나** — 파일 핸들·락·임시 파일을 들고 있는 코드가 패닉할 때 **정리가 되는지** 알아야 할 때.

**기본(되감기).**

```text
===== 소스: ex.rs =====
// ex.rs
// 패닉이 스택을 되감을 때 Drop 이 도는가 — 같은 소스를 두 전략으로 던진다
struct Guard(&'static str);

impl Drop for Guard {
    fn drop(&mut self) {
        eprintln!("   drop {}", self.0);
    }
}

fn inner() {
    let _g = Guard("inner 의 자원");
    eprintln!("B inner 진입");
    panic!("여기서 터진다");
}

fn main() {
    let _g = Guard("main 의 자원");
    eprintln!("A main 진입");
    inner();
    eprintln!("C 여기는 안 온다");
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
A main 진입
B inner 진입

thread 'main' (870445) panicked at ex.rs:14:5:
여기서 터진다
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
   drop inner 의 자원
   drop main 의 자원
(종료 코드 101)
```

**같은 소스, `-C panic=abort`.**

```text
===== 소스: ex.rs =====
// ex.rs
// 패닉이 스택을 되감을 때 Drop 이 도는가 — 같은 소스를 두 전략으로 던진다
struct Guard(&'static str);

impl Drop for Guard {
    fn drop(&mut self) {
        eprintln!("   drop {}", self.0);
    }
}

fn inner() {
    let _g = Guard("inner 의 자원");
    eprintln!("B inner 진입");
    panic!("여기서 터진다");
}

fn main() {
    let _g = Guard("main 의 자원");
    eprintln!("A main 진입");
    inner();
    eprintln!("C 여기는 안 온다");
}
===== rustc --edition 2021 -C panic=abort ex.rs -o ex =====
===== ./ex =====
A main 진입
B inner 진입

thread 'main' (870502) panicked at ex.rs:14:5:
여기서 터진다
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
(종료 코드 134)
```

- ★★★ **소스가 한 글자도 다르지 않다.** 배너의 `-C panic=abort` 만 다르다.
- 되감기 판에서는 패닉 메시지 **뒤에** `drop inner 의 자원` → `drop main 의 자원` 이 찍힌다 —
  **안쪽부터 바깥쪽으로** 스택을 풀며 정리한 것이다.
- ★★★ 중단 판에서는 **그 두 줄이 아예 없다.** `Drop` 이 안 돈다.
- ★★ **종료 코드도 다르다 — 101 대 134.** 134 는 `SIGABRT`(6)로 죽었을 때 셸이 보고하는 `128 + 6` 이다.
- ★ 그래서 `panic = "abort"` 를 켜면 **「패닉해도 정리는 된다」는 가정이 통째로 깨진다** —
  락 해제·임시 파일 삭제·버퍼 flush 를 `Drop` 에 기대고 있었다면 전부 안 돈다.
- ★ 고르는 자리 — rustc 는 `-C panic=abort`, Cargo 는 `[profile.release] panic = "abort"` 다.
  바이너리 크기와 속도를 얻고 **`catch_unwind` 를 잃는다**((6)).

### (4) `process::exit` — 내 번호로 나가되 정리도 없다

```text
===== 소스: ex.rs =====
// ex.rs
// process::exit 는 패닉이 아니다 — Drop 도 안 돌고 종료 코드도 내가 정한다
struct Guard(&'static str);

impl Drop for Guard {
    fn drop(&mut self) {
        eprintln!("   drop {}", self.0);
    }
}

fn main() {
    let _g = Guard("바깥");
    {
        let _inner = Guard("안쪽");
        eprintln!("A 안쪽 블록 끝");
    }
    eprintln!("B exit 직전");
    std::process::exit(2);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
A 안쪽 블록 끝
   drop 안쪽
B exit 직전
(종료 코드 2)
```

- **`drop 안쪽` 은 찍혔다.** 블록을 정상적으로 벗어났기 때문이다.
- ★★★ **`drop 바깥` 은 안 찍혔다.** `process::exit` 는 **스택을 되감지 않고 즉시 프로세스를 끝낸다.**
- ★★ **종료 코드는 내가 준 2** 다. 패닉(101)도 `main` 의 `Err`(1)도 아닌 **내가 고른 값**이다.
- ★ 그래서 `process::exit` 는 **`main` 의 맨 끝**이나 **CLI 의 종료 코드 규약**을 맞출 때만 쓴다.
  중간에서 부르면 **그 위 스택의 `Drop` 이 전부 건너뛰어진다.**

### (5) `main` 이 `Err` 를 반환하면 — 종료 코드 1

```text
===== 소스: ex.rs =====
// ex.rs
// main 이 Err 를 반환하면 — 무엇이 찍히고 종료 코드는 얼마인가
#[derive(Debug)]
struct ConfigError {
    key: &'static str,
    detail: String,
}

impl std::fmt::Display for ConfigError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "설정 {} 을(를) 읽지 못했다: {}", self.key, self.detail)
    }
}

fn load() -> Result<u16, ConfigError> {
    Err(ConfigError { key: "port", detail: String::from("파일에 그 줄이 없다") })
}

fn main() -> Result<(), ConfigError> {
    eprintln!("A 시작");
    let port = load()?;
    eprintln!("B 여기는 안 온다 {}", port);
    Ok(())
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
A 시작
Error: ConfigError { key: "port", detail: "파일에 그 줄이 없다" }
(종료 코드 1)
```

- ★★ **종료 코드 1** 이다. 그리고 `Error: ` 뒤에 찍히는 것은 **`Debug`** 다 —
  `ConfigError { key: "port", detail: "파일에 그 줄이 없다" }` 가 구조체 꼴로 나왔다.
- ★★★ **이 프로그램에는 `Display` 구현이 있는데 안 쓰였다.** 런타임은 `{:?}` 로 찍는다.
  ★ 그래서 **사람이 읽을 문장을 보여 주려면** `Debug` 를 직접 구현하거나
  `main` 안에서 `eprintln!("{}", e)` 를 하고 `process::exit` 를 부른다 — [**24번 주제**](../24-error-type-design/)가 그 설계를 다룬다.
- `?` 로 올린 실패가 그대로 `main` 의 `Err` 가 됐다([**22번 주제**](../22-result-question-mark-and-from/)).

### (6) `catch_unwind` — 잡을 수는 있다

```text
===== 소스: ex.rs =====
// ex.rs
// catch_unwind — 패닉을 잡을 수는 있다. 잡은 뒤에 무엇이 남나
use std::panic;

fn risky(n: u32) -> u32 {
    if n == 0 {
        panic!("0 은 못 받는다");
    }
    100 / n
}

fn main() {
    let ok = panic::catch_unwind(|| risky(4));
    eprintln!("A 성공 판 {:?}", ok);

    let caught = panic::catch_unwind(|| risky(0));
    eprintln!("B 잡았나 {} · 값은 {:?}", caught.is_err(), caught.as_ref().err().is_some());

    if let Err(payload) = caught {
        if let Some(s) = payload.downcast_ref::<&str>() {
            eprintln!("C 페이로드 {:?}", s);
        } else {
            eprintln!("C 페이로드를 &str 로 못 읽었다");
        }
    }
    eprintln!("D 프로그램은 계속 돈다");
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
A 성공 판 Ok(25)

thread 'main' (870766) panicked at ex.rs:7:9:
0 은 못 받는다
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
B 잡았나 true · 값은 true
C 페이로드 "0 은 못 받는다"
D 프로그램은 계속 돈다
(종료 코드 0)
```

- **잡힌다.** `caught.is_err()` 가 `true` 이고, 프로그램은 **종료 코드 0** 으로 정상 종료했다.
- ★★ **그런데도 패닉 메시지는 표준 오류에 찍혔다.** 잡는 것과 **조용히 만드는 것**은 다르다
  (조용히 하려면 `panic::set_hook` 을 따로 건다).
- `downcast_ref::<&str>()` 로 **페이로드**를 꺼냈다 — `panic!("0 은 못 받는다")` 의 문자열이 그대로 나온다.
  ★ `panic!("{}", x)` 처럼 **포맷이 들어가면 페이로드는 `String`** 이라 `&str` 로는 안 꺼내진다.
- ★★★ **이것은 예외 처리가 아니다.** 쓰는 자리는 **FFI 경계**(패닉이 C 경계를 넘으면 UB)와
  **스레드 풀·테스트 하네스**뿐이다. 업무 로직의 실패를 이걸로 다루면 안 된다 — 그건 `Result` 다.
- ★ `-C panic=abort` 에서는 **잡히지 않는다.** 되감기 자체가 없기 때문이다((3)).

### (7) `assert!` 와 `debug_assert!` — 한쪽만 사라진다

**기본 빌드(디버그 어서션 켜짐).**

```text
===== 소스: ex.rs =====
// ex.rs
// assert! 와 debug_assert! — 최적화 수준에 따라 한쪽만 사라진다
fn scale(n: u32) -> u32 {
    debug_assert!(n < 1000, "n 은 1000 미만이라는 내부 불변식 — 받은 값 {}", n);
    assert!(n < 100_000, "n 이 표현 범위를 넘었다 — 받은 값 {}", n);
    n * 2
}

fn main() {
    eprintln!("A 작은 값 {}", scale(10));
    eprintln!("B 큰 값 {}", scale(5000));
    eprintln!("C 여기까지 오나");
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
A 작은 값 20

thread 'main' (870851) panicked at ex.rs:4:5:
n 은 1000 미만이라는 내부 불변식 — 받은 값 5000
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
(종료 코드 101)
```

**같은 소스, `-O`.**

```text
===== 소스: ex.rs =====
// ex.rs
// assert! 와 debug_assert! — 최적화 수준에 따라 한쪽만 사라진다
fn scale(n: u32) -> u32 {
    debug_assert!(n < 1000, "n 은 1000 미만이라는 내부 불변식 — 받은 값 {}", n);
    assert!(n < 100_000, "n 이 표현 범위를 넘었다 — 받은 값 {}", n);
    n * 2
}

fn main() {
    eprintln!("A 작은 값 {}", scale(10));
    eprintln!("B 큰 값 {}", scale(5000));
    eprintln!("C 여기까지 오나");
}
===== rustc --edition 2021 -O ex.rs -o ex =====
===== ./ex =====
A 작은 값 20
B 큰 값 10000
C 여기까지 오나
(종료 코드 0)
```

- ★★★ **같은 소스가 한쪽에서는 죽고 한쪽에서는 끝까지 돈다.**
  기본 빌드에서는 `debug_assert!` 가 터져 **종료 코드 101**, `-O` 에서는 그 검사가 **아예 사라져** **종료 코드 0** 이다.
- ★★ `assert!` 는 **두 판 모두 살아 있다.** `-O` 판이 `B 큰 값 10000` 을 찍고 지나간 것은
  `5000 < 100_000` 이 **참**이라서이지 검사가 사라져서가 아니다.
- ★ 그래서 **불변식이 「깨지면 위험한 것」이면 `assert!`, 「개발 중에만 보고 싶은 것」이면 `debug_assert!`** 다.
  뒤엣것은 **릴리스에서 없는 셈** 치고 설계해야 한다.
- ★ 정확히는 `debug_assert!` 는 **`-C debug-assertions` 플래그**에 달려 있고,
  그 기본값이 최적화 수준을 따라간다(`-O` 면 꺼짐). **`-O` 자체가 끄는 것이 아니라 기본값이 바뀌는 것**이다.

### (8) `unwrap` 을 써도 되는 자리

```text
===== 소스: ex.rs =====
// ex.rs
// unwrap 을 써도 되는 자리 — 불변식이 그 줄 위에서 보장될 때
fn main() {
    // (1) 상수 리터럴 — 이 parse 는 실패할 수 없다
    let port: u16 = "8080".parse().unwrap();
    println!("(1) {}", port);

    // (2) 바로 위에서 비지 않음을 확인했다
    let scores = vec![3, 9, 4];
    if scores.is_empty() {
        println!("(2) 빈 표");
    } else {
        println!("(2) 최댓값 {}", scores.iter().max().unwrap());
    }

    // (3) 방금 넣었다
    let mut slot: Option<u32> = None;
    if slot.is_none() {
        slot = Some(7);
    }
    println!("(3) {}", slot.unwrap());

    // (4) 불변식을 말로 적는다 — expect 가 unwrap 보다 나은 이유
    let cfg = "timeout=30";
    let value = cfg
        .split_once('=')
        .expect("이 상수 문자열에는 '=' 가 반드시 있다")
        .1;
    println!("(4) {}", value);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
(1) 8080
(2) 최댓값 9
(3) 7
(4) 30
(종료 코드 0)
```

- 네 경우 다 **그 줄 위에서 불변식이 보장된다** — ① 상수 리터럴 ② 비지 않음을 방금 확인 ③ 방금 넣음 ④ 상수 문자열의 형태.
- ★★ **(4)가 `expect` 를 쓴 이유** — 「이 상수 문자열에는 `'='` 가 반드시 있다」는 **내가 아는 이유**이고,
  그것이 깨졌다면 **상수를 고친 사람이 읽어야 할 문장**이다.
- ★★★ **`expect` 메시지는 「무엇을 기대했나」가 아니라 「무엇이 깨졌길래 여기 왔나」를 적는다.**
  `expect("값이 있어야 함")` 은 쓸모가 없고, `expect("설정 파일은 빌드에 내장돼 있어 항상 파싱된다")` 는 쓸모가 있다.
- ★ 반대로 **밖에서 온 값**(사용자 입력·파일·환경변수)에 `unwrap` 을 쓰면 **그 순간 프로그램의 실패 모드가 패닉이 된다.**
  그건 (1)의 경계를 넘은 것이다.

## 문법 — 형태와 규칙

```text
   끝내는 도구들

   panic!("메시지 {}", x)           즉시 패닉. 종료 코드 101(unwind 기본)
   unreachable!()                   도달 불가라고 선언. 도달하면 패닉
   todo!() / unimplemented!()       미구현 표시. 호출되면 패닉
   assert!(cond, "메시지")           거짓이면 패닉 — ★ 릴리스에도 남는다
   assert_eq!(a, b)                 다르면 양쪽 값을 찍고 패닉
   debug_assert!(cond)              ★ debug-assertions 가 꺼지면 사라진다
   std::process::exit(n)            즉시 종료. ★ Drop 이 안 돈다
   std::panic::catch_unwind(f)      되감기를 잡는다. abort 에서는 못 잡는다

   빌드 설정

   rustc  -C panic=abort            되감기 없음 → Drop 안 돔 · catch_unwind 무력
   rustc  -O                        최적화 + ★ debug-assertions 기본 꺼짐
   Cargo  [profile.release] panic = "abort"
   Cargo  [profile.release] debug-assertions = true   ← 되살릴 수도 있다
```

- **`panic!` 은 `!`(never) 타입**이라 어떤 타입 자리에도 놓인다([**06번 주제**](../06-functions-and-never-type/)).
- ★ **`Result` 를 `unwrap` 하면 `Err` 의 `Debug` 가 패닉 메시지에 들어간다** — `Option` 과 다른 점이다.
- **`main` 의 오류 타입에는 `Debug` 가 필요하다**(`Termination` 계약).
- ★ **스레드 하나가 패닉해도 프로세스가 죽지는 않는다** — `join` 이 `Err` 를 돌려준다(목록의 **49번 주제**).
- **`#[should_panic]`** 으로 패닉을 테스트한다(목록의 **58번 주제**).

## 어디서 틀리나

| 증상 | 진짜 원인 | 고치는 법 |
|---|---|---|
| 라이브러리가 사용자 입력에 **패닉**한다 | 경계를 잘못 그었다 | `Result` 로 바꾼다((1)) |
| `panic = "abort"` 로 바꿨더니 **임시 파일이 남는다** | `Drop` 이 안 돈다 | 정리를 `Drop` 에만 기대지 않는다((3)) |
| `process::exit` 를 중간에서 불러 **로그가 안 남는다** | 스택의 `Drop` 이 건너뛰어졌다 | `main` 끝까지 값을 돌려보내고 거기서 나간다((4)) |
| `main` 이 실패했는데 **메시지가 구조체 꼴**이다 | `Error: ` 뒤는 `Debug` 다 | `Debug` 를 직접 구현하거나 직접 찍는다((5)·24번) |
| `debug_assert!` 가 **릴리스에서 안 잡는다** | 원래 사라진다 | 진짜 불변식이면 `assert!`((7)) |
| `catch_unwind` 로 업무 오류를 다룬다 | 예외 처리로 오해 | `Result` 로 바꾼다. `catch_unwind` 는 FFI·경계용((6)) |
| ★ `unwrap()` 이 늘어나 **실패 모드가 전부 패닉**이 됐다 | 「일단 컴파일 통과」로 쓴 것 | `?` 로 올린다([**22번 주제**](../22-result-question-mark-and-from/)) |
| 패닉했는데 **어느 `unwrap`** 인지 모른다 | `unwrap` 은 std 문장만 찍는다 | `expect` 로 바꾼다((8)) |

★★ **가장 조용한 사고는 「패닉이 안 나는 것」이다** — `unwrap` 이 **지금까지는** 안 터졌을 뿐인 코드.
[**21번 주제**](../21-option-and-combinators/)에서 본 대로 `unwrap` 은 **타입에서 실패 가능성을 지운다.**
그 뒤로는 컴파일러가 아무 경고도 하지 않는다.

## 구현 세부사항 대 언어 보장

| 항목 | 무엇인가 | 근거 |
|---|---|---|
| **패닉 종료 코드 101** | ★ **std 의 문서화된 동작** — 되감기 판에서 고정 | (2)의 실측 |
| `main` 이 `Err` 면 **종료 코드 1** | ★ **std 계약**(`Termination`) | (5)의 실측 |
| `process::exit(n)` 의 **n** | ★ **계약** — 내가 준 값이 그대로 | (4)의 실측 |
| ★ **abort 의 134** | ★ **구현·플랫폼 세부** — `SIGABRT`(6)에 대한 **셸의 128+N 관례**다. 다른 OS·셸이면 보고 형식이 다르다 | (3)의 실측 |
| `Drop` 이 **되감기에서 돌고 중단에서 안 도는 것** | ★ **전략의 정의** — 보장으로 읽어도 된다 | (3)의 두 블록 |
| `debug_assert!` 가 `-O` 에서 사라지는 것 | ★ **플래그의 기본값** — `-C debug-assertions` 로 되살릴 수 있다 | (7)의 두 블록 |
| 패닉 **메시지 문구**와 `note:` 줄 | ★ **구현 세부** | 전 블록 |
| `catch_unwind` 페이로드가 `&str` 인 것 | ★ **`panic!` 인자 형태에 달렸다** — 포맷을 쓰면 `String` | (6)의 실측 |

## 언제 쓰고 언제 안 쓰나

- **`Result` 를 낸다** — 밖에서 온 값, I/O, 파싱, 네트워크, 사용자 입력. **라이브러리의 기본값.**
- **`panic!`/`assert!` 를 쓴다** — 호출 규약 위반, 불변식 파괴, 도달 불가 분기. **고칠 사람이 프로그래머일 때.**
- **`unwrap`/`expect` 를 쓴다** — 그 줄 위에서 불변식이 보장될 때. **애플리케이션·테스트·프로토타입**에서.
- **`process::exit` 를 쓴다** — 종료 코드를 규약에 맞춰야 하는 CLI 의 **맨 끝**에서.
- **`catch_unwind` 를 쓴다** — FFI 경계, 스레드 풀, 테스트 하네스. **업무 로직에는 안 쓴다.**
- ★ **`panic = "abort"` 를 고른다** — 바이너리 크기·속도가 중요하고 **`Drop` 기반 정리에 기대지 않을 때.**
  임베디드·짧은 CLI 가 그 자리다.

## 핵심 문장

- ★★★ **경계는 「누가 고칠 수 있나」로 긋는다** — 사용자·운영자면 `Result`, 프로그래머면 `panic!`.
- ★★ **네 길은 종료 코드로 구분된다** — 정상 0 · 패닉 101 · `main` 의 `Err` 1 · `process::exit(n)` 의 n.
- ★★ **`panic = "abort"` 에서는 `Drop` 이 안 돈다.** 같은 소스, 플래그만 바꿔 던져 확인했다.
- ★ **`debug_assert!` 는 릴리스에서 없는 셈 치고 설계한다.** 진짜 불변식이면 `assert!`.
- **`expect` 메시지는 「무엇이 깨졌길래 여기 왔나」를 적는 자리다.**

## 관련 자료

- [**21번 주제** — `Option` 과 조합 메서드](../21-option-and-combinators/) —
  ★ **경계**: `unwrap`/`expect` 의 **메서드 표면**은 거기, **어디에 써도 되는가의 판단**은 여기다.
- [**22번 주제** — `Result` 와 `?`](../22-result-question-mark-and-from/) —
  ★ **경계**: 실패를 **위로 올리는 방법**은 거기, **올릴지 여기서 끝낼지 고르는 것**은 여기다.
- [**24번 주제** — 오류 타입 설계](../24-error-type-design/) — `Result` 로 가기로 했으면 **그 `E` 를 어떻게 만드나**.
- [**06번 주제** — 함수·발산 타입 `!`](../06-functions-and-never-type/) — `panic!` 이 어떤 타입 자리에도 놓이는 이유.
- [**09번 주제** — `Copy`·`Clone`·`Drop` 시점](../09-copy-clone-and-drop/) — `Drop` 이 언제 도는가의 정본. 여기서는 **패닉 경로**만 본다.
- [`ops-patterns/failure-modes/`](../../../../../ops-patterns/failure-modes/) —
  ★ **경계**: 실패 모드 **분류 총론**은 거기, 여기는 **Rust 의 두 경로 선택**이다.
- Go 의 `panic`/`recover` — Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **23번**.
  ★ **대비**: Go 도 관례가 같다(라이브러리는 `error`, 진짜 버그만 `panic`). **다른 점은 강제력이다** —
  Go 의 `error` 는 **무시해도 컴파일되고**, Rust 의 `Result` 는 안 쓰면 경고가 나고 값을 쓰려면 반드시 갈래를 다뤄야 한다.
- Java 의 예외 — [`java/syntax/25-exceptions/`](../../../java/syntax/25-exceptions/).
  ★ **대비**: Java 는 **한 메커니즘(예외)** 안에서 checked/unchecked 로 가르고,
  Rust 는 **두 메커니즘**(`Result` 와 패닉)으로 가른다. 그래서 Rust 에서는 **타입만 보고** 어느 쪽인지 안다.
- Python 의 예외 — Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **25번**.

## 용어 풀이

- **패닉(panic)** — 복구 불가로 판단해 스레드를 끝내는 것. 종료 코드 101.
- **되감기(unwind)** — 스택을 역순으로 풀며 `Drop` 을 실행하는 것. 기본 전략.
- **중단(abort)** — 되감지 않고 즉시 죽는 것. `SIGABRT`.
- **`catch_unwind`** — 되감기를 잡아 `Result` 로 받는 함수. 예외 처리가 아니다.
- **`Termination`** — `main` 의 반환값을 종료 코드로 바꾸는 std 트레이트.
- **불변식(invariant)** — 그 코드가 항상 참이라고 가정하는 조건. 깨지면 버그다.
- **호출 규약(contract)** — 호출자가 지켜야 하는 조건. 어기면 `assert!` 가 잡는다.
- **디버그 어서션(debug assertions)** — `-C debug-assertions` 로 켜고 끄는 검사. `debug_assert!` 계열이 여기 달렸다.

## 더 들어가면

- **`panic::set_hook`** — 패닉 메시지 출력을 통째로 갈아 끼운다. 잡는 것과 찍는 것을 분리할 수 있다((6)).
- **`#[panic_handler]`** — `no_std` 환경에서 패닉 동작을 직접 정의한다.
- **`RUST_BACKTRACE=1`** — `note:` 줄이 안내하는 그것. 백트레이스를 켠다.
- **스레드 경계의 패닉** — 자식 스레드가 패닉해도 프로세스는 살고 `join` 이 `Err` 를 낸다(목록의 **49번 주제**).
  ★ `Mutex` 는 그때 **중독(poisoned)** 된다(목록의 **52번 주제**).
- **`#[should_panic]`** — 패닉을 기대하는 테스트(목록의 **58번 주제**).
