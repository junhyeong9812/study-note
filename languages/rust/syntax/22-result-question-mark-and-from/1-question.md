# rust/syntax/22 — `Result` 와 `?`·`From` 변환 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 답을 모르겠으면 **던져 보라.** `rustc --edition 2021 ex.rs -o ex && ./ex` 다.
> ★★ **`--edition` 을 빼면 에디션 2015 로 돌아간다** — 답을 맞춰도 다른 언어를 컴파일한 것이다.
> ★★★ 이 주제의 문항 절반은 **에러 전문을 묻는다.** 「안 된다」가 아니라 **무엇이 적히는가**를 답하라.
> ★ 종료 코드를 묻는 문항이 있다 — `./ex; echo $?` 로 확인한다.

> ★ 아래 코드 펜스의 **첫 줄 `// bNN-….rs` 는 캡처 원본 파일 이름**이고, 그 아래 `// ex.rs` 가 **컴파일할 때의 이름**이다.
> 캡처 스크립트가 원본을 `ex.rs` 로 복사해 던지므로 **진단에 박히는 파일명은 언제나 `ex.rs`** 다.
> 펜스가 실파일과 한 글자도 같은지는 `check-source-fences.py` 가 기계로 대조했다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 오류 타입이 둘인데 변환 impl 이 없으면 (예측)

```rust
// b22-02.rs
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
```

- 컴파일되는가? 안 되면 **에러 번호**와 **제목 한 줄**은 무엇인가?
- 에러는 **몇 개**이며, `?` 가 **두 개**인데 왜 그 개수인가?
- ★★★ 진단의 마지막 `= note:` 는 무엇을 말하는가 — **`?` 의 내부 동작**에 대해?
- ★★ 그 위의 `note:` 는 **무엇을 구현하라고** 적는가?
- 이 파일을 통과시키려면 **몇 줄**을 더해야 하는가?

### 2. ★★ 같은 결함인데 타입을 추론에 맡기면 (예측)

```rust
// b22-10.rs
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
```

- 1번과 **결함이 같다.** 에러 번호도 같은가?
- 진단에 **`From` 이라는 낱말이 나오는가**?
- 왜 이런 차이가 나는가 — `parse` 의 타입은 어디에서 정해지는가?
- 그래서 `?` 앞의 표현식에는 **무엇을 적는 것이 유리한가**?
- 이 차이는 언어 보장인가 구현 세부인가?

### 3. ★ `main` 이 `()` 인데 `?` 를 쓰면 (예측)

```rust
// b22-04.rs
// ex.rs
// main 이 () 를 반환하면 ? 를 못 쓴다
fn main() {
    let n: u16 = "8080".parse()?;
    println!("{}", n);
}
```

- 에러 번호와 제목은 무엇인가?
- 진단이 `main` 을 **어떻게 가리키는가** — 한 줄로 무엇이라 적히는가?
- ★ `help` 는 **무엇을 보여 주는가** — 문장인가 코드인가?
- 그 처방을 그대로 적용하면 반환 타입은 무엇이 되는가?

### 4. ★★ `main` 이 `Result` 를 반환하고 실패하면 (예측)

```rust
// b22-05.rs
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
```

- 표준 출력·표준 오류에 무엇이 찍히는가?
- ★★★ **종료 코드**는 얼마인가? 패닉일 때와 같은가?
- ★★ `Error: ` 뒤에 찍히는 것은 **`Display` 인가 `Debug` 인가** — 어떻게 아는가?
- `main` 의 오류 타입에 필요한 트레이트 경계는 무엇인가?
- 성공했으면 종료 코드는 얼마였겠는가?

### 5. ★★ `Option` 과 `Result` 를 `?` 로 섞으면 (예측)

```rust
// b22-06.rs
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
```

- 에러는 **몇 개**인가? 한쪽만 걸리는가 양쪽 다 걸리는가?
- 두 제목은 각각 무엇인가?
- ★ 진단이 주는 처방 **둘**은 무엇인가?
- ★★ 한쪽 처방에 「**버린다**」는 말이 들어 있다. 무엇을 버리는가?
- 그래서 두 세계를 잇는 다리 함수 **둘**은 무엇인가?

### 6. ★ `?` 를 손으로 펼치면 같은 것이 되나 (예측)

```rust
// b22-08.rs
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
```

- `두 판이 같은가` 줄에는 무엇이 찍히는가?
- `by_hand` 의 어느 한 줄이 `?` 가 펼쳐진 모양인가?
- ★ 그 줄에서 **`From::from`** 이 하는 일은 무엇인가?
- 실제 컴파일러가 거치는 트레이트 이름은 무엇이며, 그것을 **결론의 근거로 써도 되는가**?

### 7. `?` 가 하는 두 가지 (왜)

- `?` 가 성공일 때와 실패일 때 각각 무엇을 하는가?
- 오류 타입이 **같으면** 무엇이 생략되는가?
- `From<T> for T` 반사 impl 이 여기서 하는 역할은 무엇인가?
- `?` 는 문(statement)인가 식(expression)인가 — 근거는?
- `?` 이전(1.13.0 이전)에는 같은 일을 무엇이 했는가?

### 8. `?` 가 되는 자리와 안 되는 자리 (경계)

- `?` 를 쓸 수 있는 함수 반환 타입을 전부 댈 수 있는가?
- 클로저 안에서 `?` 를 쓰면 **무엇을 기준으로** 판정되는가?
- `main` 에서 쓸 때 실무의 기본형은 무엇인가?
- `?` 를 한 함수에서 열 번 넘게 쓰고 있다면 무엇을 의심해야 하는가?

### 9. 변환을 손으로 할 때 (연결)

- `impl From` 과 `map_err` 중 어느 쪽을 언제 고르는가?
- `ok_or` 와 `ok_or_else` 의 차이는 무엇이며 그 정본은 몇 번 주제인가?
- `ok()` 는 무엇을 버리는가?
- `?` 가 **못 붙이는 것**(문맥·위치 정보)은 무엇으로 붙이는가?

### 10. 이웃 주제·다른 언어와 잇기 (연결)

- ★ 20번의 `let else` 와 `?` 는 무엇이 겹치고 무엇이 갈리는가 — **한 줄로** 답하라.
- `Result` 가 열거형이라는 사실의 정본은 몇 번 주제인가?
- Go 의 `(T, error)` 관례는 같은 일을 몇 줄로 적는가? 변환은 무엇으로 하는가?
- Java 의 예외와 `?` 의 가장 큰 차이는 **무엇이 코드에 보이는가**로 답할 수 있는가?
- `Box<dyn Error>` 가 어떤 오류든 받는 이유는 무엇이며, 그 정본은 몇 번 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
