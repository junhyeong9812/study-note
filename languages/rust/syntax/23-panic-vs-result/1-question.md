# rust/syntax/23 — `panic!` 대 `Result` — 어디서 끝낼 것인가 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ **이 주제의 문항 절반은 「종료 코드」를 묻는다.** `./ex; echo $?` 로 확인한다.
> ★ 던지는 법 — `rustc --edition 2021 ex.rs -o ex && ./ex`.
> 일부 문항은 **플래그를 더해 한 번 더** 던져야 한다(`-C panic=abort` · `-O`).
> ★★ **`--edition` 을 빼면 에디션 2015 로 돌아간다** — 답을 맞춰도 다른 언어를 컴파일한 것이다.

> ★ 아래 코드 펜스의 **첫 줄 `// bNN-….rs` 는 캡처 원본 파일 이름**이고, 그 아래 `// ex.rs` 가 **컴파일할 때의 이름**이다.
> 캡처 스크립트가 원본을 `ex.rs` 로 복사해 던지므로 **진단에 박히는 파일명은 언제나 `ex.rs`** 다.
> 펜스가 실파일과 한 글자도 같은지는 `check-source-fences.py` 가 기계로 대조했다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ 패닉으로 끝난 프로세스가 남기는 번호 (예측)

```rust
// b23-01.rs
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
```

- 표준 오류에 **몇 줄**이 찍히는가?
- ★★ **종료 코드**는 얼마인가?
- `C 여기는 안 온다` 는 찍히는가?
- 패닉 첫 줄에서 **실행마다 바뀌는 칸**은 어디인가?
- 이 프로그램이 마커를 `eprintln!` 으로 찍은 이유는 무엇인가?

### 2. ★★★ 같은 소스를 두 패닉 전략으로 던지면 (예측)

```rust
// b23-03.rs
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
```

- 기본 빌드에서 `drop` 줄은 **몇 개** 찍히며 **어느 순서**인가?
- 그 줄들은 패닉 메시지보다 **앞인가 뒤인가**?
- ★★★ `-C panic=abort` 로 다시 던지면 무엇이 **사라지는가**?
- ★★ 두 판의 **종료 코드**는 각각 얼마인가? 두 번째 숫자는 **어디서 온 숫자**인가?
- 이 차이가 실무에서 무엇을 깨뜨릴 수 있는가 — 둘만 대 보라.

### 3. ★★ `process::exit` 가 건너뛰는 것 (예측)

```rust
// b23-02.rs
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
```

- `drop 안쪽` 과 `drop 바깥` 중 **무엇이 찍히고 무엇이 안 찍히는가**?
- ★★ 종료 코드는 얼마인가 — 그 숫자는 **누가 정했는가**?
- 패닉과 무엇이 같고 무엇이 다른가?
- 이 함수를 프로그램 **중간**에서 부르면 무엇이 위험한가?

### 4. ★★ `main` 이 `Err` 를 돌려주면 (예측)

```rust
// b23-05.rs
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
```

- 표준 오류에 무엇이 찍히는가 — **접두어**까지 적을 수 있는가?
- ★★★ 찍히는 것은 **`Display` 인가 `Debug` 인가**? 이 소스에는 둘 다 있는데 어떻게 아는가?
- ★★ 종료 코드는 얼마인가? 패닉과 같은가?
- 사람이 읽을 문장을 보여 주려면 무엇을 해야 하는가?

### 5. ★ 패닉을 잡아 보면 (예측)

```rust
// b23-06.rs
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
```

- `catch_unwind` 가 패닉을 잡는가? 프로그램의 **종료 코드**는 얼마인가?
- ★★ 잡았는데도 **표준 오류에 패닉 메시지가 찍히는가**?
- 페이로드를 `&str` 로 꺼낼 수 있는가 — 어떤 경우에 못 꺼내는가?
- ★ `-C panic=abort` 에서 이 코드는 어떻게 되는가?
- 이것을 업무 오류 처리에 쓰면 안 되는 이유는 무엇인가?

### 6. ★★ 같은 소스를 `-O` 로 다시 던지면 (예측)

```rust
// b23-07.rs
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
```

- 기본 빌드에서 어디까지 찍히고 **종료 코드**는 얼마인가?
- ★★★ `-O` 로 던지면 어디까지 찍히고 종료 코드는 얼마인가?
- 두 검사(`assert!` · `debug_assert!`) 중 **사라지는 것**은 어느 쪽인가?
- ★ `-O` 판에서 `assert!` 가 안 터진 것은 **사라져서인가 통과해서인가**?
- 정확히 무엇이 `debug_assert!` 를 끄는가 — `-O` 인가 다른 플래그인가?

### 7. 경계를 어디에 긋나 (왜)

- 「복구 가능」과 「복구 불가능」을 가르는 **한 문장** 기준은 무엇인가?
- 같은 프로그램에서 `Result` 를 내는 함수와 `assert!` 로 끝내는 함수가 공존할 수 있는가?
- `Result` 로 네 번 실패한 프로그램의 종료 코드는 얼마인가?
- 「라이브러리는 패닉하지 않는다」는 관례에 **예외**가 있는가?

### 8. `unwrap` 을 써도 되는 자리 (경계)

- 그 줄 위에서 불변식이 보장되는 **경우 넷**을 댈 수 있는가?
- 밖에서 온 값(사용자 입력·파일·환경변수)에 `unwrap` 을 쓰면 무엇이 달라지는가?
- `Result` 를 `unwrap` 했을 때 패닉 메시지에 들어가는 것은 무엇인가?
- `unwrap` 이 늘어난 코드에서 컴파일러가 경고해 주는가?

### 9. `expect` 메시지를 어떻게 쓰나 (경계)

- `expect("값이 있어야 함")` 은 왜 쓸모가 없는가?
- 좋은 `expect` 메시지는 **무엇을 적는가** — 한 문장으로.
- `unwrap` 과 `expect` 의 출력에서 **같은 칸과 다른 칸**은 각각 무엇인가?
- `assert!` 의 메시지에도 같은 기준이 적용되는가?

### 10. 다른 언어·다른 주제와 잇기 (연결)

- 종료 코드 **네 가지**를 표로 적을 수 있는가(정상·패닉·`main` 의 `Err`·`process::exit`)?
- `panic!` 이 어떤 타입 자리에도 놓이는 이유는 무엇이며 정본은 몇 번 주제인가?
- Go 의 `panic`/`recover` 관례는 Rust 와 같은가? **강제력**은 어떻게 다른가?
- Java 의 예외와 Rust 의 두 경로는 **무엇이 다른가** — 「타입만 보고 아는가」로 답하라.
- 자식 스레드가 패닉하면 프로세스는 죽는가? 그때 `Mutex` 에 무슨 일이 생기는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
