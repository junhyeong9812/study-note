# rust/syntax/23 — `panic!` 대 `Result` — 어디서 끝낼 것인가 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서\
> **`rustc --edition 2021 ex.rs -o ex`**(일부는 `-C panic=abort` 또는 `-O` 를 더해) 실제로 돌려 받은 것이다.\
> ★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
> ★★★ **플래그 대조는 표준 배너로 한 판씩 따로** 실었다. 두 블록의 유일한 차이는 배너의 플래그이고
> **소스는 한 글자도 같은 파일**이다 — 그 동일성도 기계로 대조했다.\
> ★★ **`--edition` 을 빼면 에디션 2015 다.** 이 갈래에서 그것은 「안 돌려 본 것」과 같다.\
> ★ 패닉 첫 줄의 `thread 'main' (…)` 괄호 안 숫자는 **실행마다 다른 OS 스레드 id** 다 — 대조할 칸이 아니다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ 종료 코드 101

**출력.**

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

**왜 그런가**

- 표준 오류에 **다섯 줄**이 찍힌다 — `A 0.75` · 빈 줄 · `thread 'main' (…) panicked at ex.rs:5:9:` ·
  메시지 본문 · `note: run with …` 다.
- ★★ **종료 코드는 101** 이다. 패닉으로 끝난 프로세스의 고정값이고,
  `main` 의 `Err`(1)·`process::exit(n)` 과 **셸에서 구분된다**.
- **`C 여기는 안 온다` 는 안 찍힌다.** `ratio(3, 0)` 이 인자 평가 중에 패닉해서
  `eprintln!("B …")` 자체가 끝나지 않았고, 그 뒤 줄은 실행되지 않는다.
- 실행마다 바뀌는 칸은 **`thread 'main' (814051)` 의 괄호 안 OS 스레드 id** 하나뿐이다.
  `파일:줄:칸`·메시지·`note:` 줄은 고정이다.
- ★ 마커를 `eprintln!` 으로 찍은 이유 — **패닉은 표준 오류로 나간다.**
  `println!` 과 섞으면 터미널에서 본 순서와 파이프로 받은 순서가 갈릴 수 있다.

### 2. ★★★ 되감기는 정리하고, 중단은 안 한다

**출력** — 기본(되감기).

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

**같은 파일, `-C panic=abort`.**

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

**왜 그런가**

- 기본 빌드에서 `drop` 은 **두 줄**이고 `drop inner 의 자원` → `drop main 의 자원` 순이다 —
  **안쪽 프레임부터 바깥쪽으로** 스택을 풀기 때문이다.
- 그 줄들은 **패닉 메시지 뒤**에 온다. 패닉 메시지는 **되감기를 시작하기 전에** 찍히기 때문이다.
- ★★★ `-C panic=abort` 판에서는 **`drop` 두 줄이 통째로 사라진다.** 되감기를 아예 안 하므로 `Drop` 이 안 돈다.
- ★★ 종료 코드는 **101 대 134** 다. 134 는 `SIGABRT`(신호 6)로 죽은 프로세스를
  셸이 `128 + 6` 으로 보고하는 관례에서 온 숫자다. ★ 그래서 **101 은 Rust 가 정한 값**이고
  **134 는 OS·셸의 표기**다 — 성격이 다른 숫자다.
- 실무에서 깨지는 것 —
  - **임시 파일·락**이 `Drop` 으로 정리되던 코드가 정리 없이 죽는다.
  - **버퍼가 flush 되지 않는다**(`BufWriter` 를 `Drop` 에 맡긴 경우).
  - ★ 덤으로 **`catch_unwind` 가 무력해진다**(5번 답).

### 3. ★★ `process::exit` 는 스택을 되감지 않는다

**출력.**

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

**왜 그런가**

- **`drop 안쪽` 은 찍히고 `drop 바깥` 은 안 찍힌다.** 안쪽 것은 블록을 정상적으로 벗어나며 이미 돌았고,
  바깥 것은 `process::exit` 가 **스택을 되감지 않고 프로세스를 끝내서** 영영 안 돈다.
- ★★ 종료 코드는 **2** 이고 그 숫자를 정한 것은 **나**다(`exit(2)`).
  패닉의 101 도 `main` 의 1 도 아니다.
- 패닉과 **같은 점** — 정상 흐름이 끝나지 않는다. **다른 점** — 되감기가 없고(그래서 `Drop` 도 없고),
  메시지도 안 찍히고, **종료 코드를 내가 고른다**.
- ★ 중간에서 부르면 **그 위 스택의 모든 `Drop` 이 건너뛰어진다** — 로그 flush·락 해제·임시 파일 삭제가 전부 안 된다.
  그래서 `process::exit` 는 **`main` 의 맨 끝**에서, 값을 거기까지 돌려보낸 다음에 부르는 것이 원칙이다.

### 4. ★★ 종료 코드 1 · 그리고 `Debug` 로 찍힌다

**출력.**

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

**왜 그런가**

- 접두어까지 적으면 `Error: ConfigError { key: "port", detail: "파일에 그 줄이 없다" }` 다.
- ★★★ 찍힌 것은 **`Debug`** 다. 이 소스에는 `Display` 도 있고 그 문장은
  `설정 port 을(를) 읽지 못했다: 파일에 그 줄이 없다` 인데 **그 문장이 안 나왔다.**
  나온 것은 `#[derive(Debug)]` 가 만든 **구조체 꼴**이다. ★ **출력 자체가 근거다.**
- ★★ 종료 코드는 **1** 이다. 패닉의 101 과 다르다 — 「프로그램이 실패로 끝났다」와
  「프로그램이 깨졌다」를 **셸이 구분할 수 있다.**
- 사람이 읽을 문장을 보여 주려면 셋 중 하나다 —
  ① `Debug` 를 **직접 구현**해 `Display` 와 같은 문장을 내게 한다(24번 6번 답이 그 실험이다),
  ② `main` 안에서 `eprintln!("{}", e)` 로 찍고 `process::exit(1)`,
  ③ `Display` 를 `Debug` 로 위임하는 래퍼 타입을 만든다.

### 5. ★ 잡히지만 — 예외 처리가 아니다

**출력.**

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

**왜 그런가**

- **잡힌다.** `B 잡았나 true` 이고 프로그램은 **종료 코드 0** 으로 끝났다. `D 프로그램은 계속 돈다` 까지 찍혔다.
- ★★ **잡았는데도 패닉 메시지가 표준 오류에 찍혔다.** `catch_unwind` 는 **되감기를 받아 낼 뿐**이고,
  메시지를 찍는 것은 그 전에 도는 **패닉 훅**이다. 조용히 하려면 `panic::set_hook` 을 따로 걸어야 한다.
- 페이로드는 `panic!("0 은 못 받는다")` 처럼 **문자열 리터럴 하나**면 `&str` 로 꺼내진다.
  ★ `panic!("{} 는 못 받는다", n)` 처럼 **포맷이 들어가면 `String`** 이라 `downcast_ref::<&str>()` 로는 못 꺼낸다.
- ★ `-C panic=abort` 에서는 **되감기 자체가 없어서 잡히지 않는다.** 프로세스가 그냥 죽는다(2번 답).
- ★★★ 업무 오류에 쓰면 안 되는 이유 — **타입에 아무 흔적이 안 남는다.**
  어떤 함수가 패닉할 수 있는지 시그니처로 알 수 없고, 호출자가 **무엇을 복구해야 하는지도 모른다.**
  그 정보를 타입에 적는 것이 `Result` 다. `catch_unwind` 의 자리는 **FFI 경계·스레드 풀·테스트 하네스**뿐이다.

### 6. ★★ `-O` 에서 `debug_assert!` 가 사라진다

**출력** — 기본 빌드.

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

**같은 파일, `-O`.**

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

**왜 그런가**

- 기본 빌드는 `A 작은 값 20` 까지 찍고 **`debug_assert!` 에서 패닉**한다 — **종료 코드 101**.
- ★★★ `-O` 판은 `C 여기까지 오나` 까지 **전부 찍고 종료 코드 0** 이다. 같은 소스인데 결과가 반대다.
- **사라지는 것은 `debug_assert!`** 다. `assert!` 는 두 판 모두 코드에 남아 있다.
- ★ `-O` 판에서 `assert!` 가 안 터진 것은 **통과해서**다 — `5000 < 100_000` 이 참이다.
  **사라져서가 아니다.** ★ 이 구분이 중요하다: 「안 터졌다」를 「없어졌다」로 읽으면 안 된다.
- ★★ 정확히 `debug_assert!` 를 끄는 것은 **`-C debug-assertions` 플래그**이고,
  그 **기본값이 최적화 수준을 따라간다**(최적화가 켜지면 꺼짐).
  그래서 Cargo 에서 `[profile.release] debug-assertions = true` 로 **되살릴 수도 있다** —
  `-O` 가 직접 지우는 것이 아니라 **기본값을 바꾸는 것**이다.

### 7. 누가 고칠 수 있나

**출력.**

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

**왜 그런가**

- ★★★ 한 문장 기준 — **「사용자·운영자가 고칠 수 있으면 `Result`, 코드를 고쳐야만 되면 `panic!`」** 이다.
- **공존한다.** 이 프로그램이 그 예다 — `parse_port` 는 밖에서 온 값을 받으므로 `Result` 를 내고,
  `percent` 는 호출 규약(`whole > 0`)을 지키지 않은 **호출자의 버그**를 `assert!` 로 끝낸다.
- ★★ **네 번 실패했는데 종료 코드는 0** 이다. `Result` 로 다룬 실패는 **프로그램의 실패가 아니다** —
  예상된 경로를 지나간 것이다. 이것이 두 길을 가르는 실질적인 이유다.
- ★ 관례의 **예외** — 「라이브러리는 패닉하지 않는다」에도 예외가 있다.
  **호출 규약 위반**(범위를 벗어난 인덱스, 잘못된 인자 조합)과 **불변식 파괴**는 패닉한다.
  std 자신이 그렇다 — `Vec` 의 인덱스 초과, `RefCell` 의 이중 가변 빌림, 슬라이스의 UTF-8 경계 침범이 전부 패닉이다
  ([**15번 주제**](../15-slices-ranges-and-utf8-boundaries/)).

### 8. 불변식이 그 줄 위에서 보장될 때

**출력.**

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

**왜 그런가**

- 경우 넷 —
  ① **상수 리터럴** — `"8080".parse::<u16>()` 은 실패할 수 없다.
  ② **방금 확인함** — `is_empty()` 로 비지 않음을 확인한 `else` 가지 안의 `max()`.
  ③ **방금 넣음** — 바로 위에서 `Some(7)` 을 넣었다.
  ④ **형태가 고정된 상수 문자열** — `"timeout=30"` 에 `'='` 가 있다.
- ★★ 밖에서 온 값에 쓰면 **그 프로그램의 실패 모드가 패닉이 된다.**
  사용자가 빈 문자열을 넣으면 그때 **101 로 죽는다** — 복구할 기회가 없다.
  그것은 7번의 경계를 넘은 것이다.
- ★ **`Result` 를 `unwrap` 하면 패닉 메시지에 `Err` 값의 `Debug` 가 함께 들어간다.**
  `Option` 쪽은 담을 값이 없어 std 의 문장만 나온다([**21번 주제**](../21-option-and-combinators/) 5번 답).
  ★ 실패 이유가 메시지에 남는다는 점에서 `Result` 의 `unwrap` 이 그나마 낫지만,
  **호출자가 복구할 기회를 없앤다는 성질은 같다.**
- ★★★ **컴파일러는 `unwrap` 에 아무 경고도 하지 않는다.** `Result` 를 **안 쓰고 버리면**
  `#[must_use]` 경고가 나지만, `unwrap` 은 **제대로 쓴 것**이기 때문이다.
  그래서 이 판단은 **도구가 아니라 사람이** 지켜야 한다(린트로는 `clippy::unwrap_used` 가 있다).

### 9. `expect` 메시지는 「무엇이 깨졌나」다

**왜 그런가**

- `expect("값이 있어야 함")` 이 쓸모없는 이유 — **패닉 메시지를 읽는 사람이 이미 아는 사실**이기 때문이다.
  `None` 이라서 여기 온 것을 모를 리 없다. 정보가 0이다.
- ★★ 좋은 메시지는 **「이 자리에서 그 값이 있어야 한다고 내가 믿은 이유」** 를 적는다.
  8번 블록의 `expect("이 상수 문자열에는 '=' 가 반드시 있다")` 가 그 꼴이다 —
  읽는 사람이 **어느 가정이 깨졌는지** 바로 안다.
- **같은 칸과 다른 칸**(21번 5번 답의 두 블록) — `파일:줄:칸`·`note:` 줄·**종료 코드 101** 이 같고,
  **메시지 본문 한 줄만** 다르다. 그래서 `expect` 는 **비용 없이 정보를 더하는 것**이다.
- ★ `assert!` 의 메시지도 같은 기준이다 — 7번 블록의
  `assert!(whole > 0, "percent 는 whole > 0 을 요구한다(호출자 버그)")` 는
  **어느 규약을 누가 어겼는지**를 적었다.

### 10. 다른 언어·다른 주제와 잇기

- **종료 코드 네 가지** —

| 길 | `Drop` | 종료 코드 | 누가 정하나 |
|---|---|---|---|
| 정상 반환 | 돈다 | **0** | — |
| `panic!`(되감기 기본) | 돈다 | **101** | Rust 런타임 |
| `panic!`(`-C panic=abort`) | ★ 안 돈다 | **134** | OS·셸(`128 + SIGABRT`) |
| `main` 이 `Err` 반환 | 돈다 | **1** | std(`Termination`) |
| `process::exit(n)` | ★ 안 돈다 | **n** | ★ 내가 |

- **`panic!` 은 `!`(never) 타입**이라 어떤 타입이 필요한 자리에도 놓인다.
  정본은 [**06번 주제**](../06-functions-and-never-type/)다.
- ★ **Go 의 관례는 같고 강제력이 다르다**(Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **23번**).
  Go 도 「라이브러리는 `error`, 진짜 버그만 `panic`」이지만, **`err` 를 안 보고 지나가도 컴파일된다.**
  Rust 는 `Result` 를 버리면 `#[must_use]` 경고가 나고, **값을 쓰려면 반드시 갈래를 다뤄야** 한다.
  ★ **관례가 같아도 지켜지는 정도가 다르다** — 그 차이를 만드는 것이 타입 시스템이다.
- ★ **Java 와의 차이는 「타입만 보고 아는가」다**([`java/syntax/25-exceptions/`](../../../java/syntax/25-exceptions/)).
  Java 는 **한 메커니즘(예외)** 안에서 checked/unchecked 로 가르고, unchecked 는 시그니처에 **안 보인다.**
  Rust 는 **두 메커니즘**이고, `Result` 가 시그니처에 **적혀 있다** —
  패닉은 시그니처에 안 보이지만 **관례상 라이브러리가 안 쓰므로** 그 자체가 신호가 된다.
  Python 도 예외 한 갈래다(Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **25번**).
- ★ **자식 스레드가 패닉해도 프로세스는 안 죽는다.** `join()` 이 `Err(페이로드)` 를 돌려준다(목록의 **49번 주제**).
  그때 그 스레드가 들고 있던 **`Mutex` 는 중독(poisoned)** 되어, 이후 `lock()` 이 `Err` 를 낸다(목록의 **52번 주제**).
  ★ 「패닉은 그 스레드에서 끝난다」와 「그래도 공유 상태에는 자국이 남는다」를 같이 기억한다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh` 가 `rustc --edition 2021 …` 로 컴파일하고 `./ex` 실행 | 배치 내내 + **제출 전 전수 재실행 1회** | `diff -rq` — 패닉 블록의 스레드 id만 달라짐 |
| ★★★ **종료 코드 네 가지** | `b23-01`(101) · `b23-05`(1) · `b23-02`(2) · `b23-04`(134) | 4 | 캡처가 블록 끝에 `(종료 코드 N)` 으로 기록 |
| ★★★ **되감기 대 중단** | `b23-03` · `b23-04` — **같은 소스**, 배너의 `-C panic=abort` 만 다름 | 2 | `drop` 두 줄이 통째로 사라짐 |
| ★★ **`debug_assert!` 대 `assert!`** | `b23-07` · `b23-08` — **같은 소스**, 배너의 `-O` 만 다름 | 2 | 101 대 0 으로 갈림 |
| `process::exit` 와 `Drop` | `b23-02` | 1 | `drop 바깥` 이 안 찍힘 |
| `catch_unwind` | `b23-06` | 1 | 잡혀도 메시지는 찍힘 · 종료 코드 0 |
| 경계 설계 | `b23-09` | 1 | 네 번 실패하고도 종료 코드 0 |
| `unwrap` 이 안전한 자리 | `b23-10` | 1 | 네 경우 모두 통과 |
| 두 플래그 블록의 **소스 동일성** | `capture.sh` 가 **같은 파일**을 두 번 복사해 던짐 | 2 | 한 글자도 같음 |

**구현 의존 항목**(버전·환경이 바뀌면 **다시 찍어야 하는** 것).

| 항목 | 왜 |
|---|---|
| ★ **abort 판의 134** | `SIGABRT` 에 대한 **셸의 `128+N` 관례**다. 다른 OS·셸이면 보고 형식이 다르다 |
| 패닉 **메시지 문구**·`note:` 줄 | std 의 구현 세부다 |
| `ConfigError` 의 `Debug` 출력 형식 | `derive(Debug)` 의 형식이다 |
| `debug_assert!` 의 기본 on/off | ★ **플래그 기본값** — Cargo 프로필에서 바꿀 수 있다 |
| 패닉 첫 줄의 **스레드 id** | ★ **실행마다 다르다** — 대조 대상이 아니다 |
| **못 던져 본 것** — Cargo 프로필(`[profile.release] panic = "abort"`) | ★ 이 배치는 **`rustc` 단독**으로만 던졌다. Cargo 경유는 안 돌려 봤고, **같은 플래그로 내려간다는 문서 근거**에 기댄 진술이다 |

★ **다시 찍는 법** — `capture.sh` 를 그대로 돌리고 `diff -rq` 한다.
달라지는 파일은 **패닉이 있는 `b23-01`·`b23-03`·`b23-04`·`b23-06`·`b23-07` 다섯**이고,
그 차이는 **스레드 id 한 칸**이라야 한다.
