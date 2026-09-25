# rust/syntax/26 — 고아 규칙과 newtype — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 던지는 법 — `rustc --edition 2021 ex.rs -o ex && ./ex`.
> ★★ **`--edition` 을 빼면 에디션 2015 로 돌아간다** — 답을 맞춰도 다른 언어를 컴파일한 것이다.
> ★★ **외부 크레이트를 하나도 쓰지 않는다.** 「남의 크레이트」 자리는 **std 가 맡는다**.
> ★★★ **이 주제는 에러 전문을 읽는 주제다.** 「거부된다」로 끝내지 말고
> **제목 · 밑줄이 짚는 곳 · `= note:` 세 줄**을 각각 적어 보라.

> ★ 아래 코드 펜스의 **첫 줄 `// bNN-….rs` 는 캡처 원본 파일 이름**이고, 그 아래 `// ex.rs` 가 **컴파일할 때의 이름**이다.
> 캡처 스크립트가 원본을 `ex.rs` 로 복사해 던지므로 **진단에 박히는 파일명은 언제나 `ex.rs`** 다.
> 펜스가 실파일과 한 글자도 같은지는 `check-source-fences.py` 가 기계로 대조했다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 남의 타입에 남의 트레이트를 붙이면 (예측)

```rust
// b26-01.rs
// ex.rs
// 고아 규칙 — 남의 타입(Vec<String>)에 남의 트레이트(Display)를 구현하려 하면
use std::fmt;

impl fmt::Display for Vec<String> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "[{}]", self.join(", "))
    }
}

fn main() {
    let v = vec![String::from("가"), String::from("나")];
    println!("{}", v);
}
```

- 컴파일하면 어떻게 되는가? **에러 번호**는 무엇인가?
- ★★★ 진단의 **제목 한 줄**을 적을 수 있는가?
- 밑줄(캐럿과 하이픈)은 **어느 쪽**을 짚는가? 거기 붙는 문구는 무엇인가?
- ★★ `= note:` 는 **몇 줄**이고 각각 무엇을 말하는가 — 그중 **처방**을 말하는 줄은?

### 2. ★★ 한쪽만 내 것이면 (예측)

```rust
// b26-02.rs
// ex.rs
// 되는 셋 — 한쪽만 내 것이면 통과한다
use std::fmt;

struct Money(i64); // 내 타입

impl fmt::Display for Money {
    // ① 내 타입 + 남의 트레이트
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}원", self.0)
    }
}

impl From<Money> for String {
    // ② Self 도 트레이트도 남의 것인데 인자가 내 타입이다
    fn from(m: Money) -> String {
        format!("{}", m)
    }
}

trait AsWon {
    // ③ 내 트레이트
    fn as_won(&self) -> i64;
}

impl AsWon for i64 {
    // 남의 타입 + 내 트레이트
    fn as_won(&self) -> i64 {
        *self
    }
}

impl AsWon for Vec<String> {
    // 남의 제네릭 타입에도 된다
    fn as_won(&self) -> i64 {
        self.len() as i64
    }
}

fn main() {
    println!("① {}", Money(1200));
    let s: String = Money(3400).into();
    println!("② {}", s);
    println!("③ {} {}", 7i64.as_won(), vec![String::from("가")].as_won());
}
```

- 세 구현 중 **몇 개**가 통과하는가?
- ★★ `impl From<Money> for String` 은 `String` 도 `From` 도 남의 것이다. 왜 이것이 통과하는가?
- `impl AsWon for Vec<String>` 처럼 **남의 제네릭 타입**에도 되는가?
- 출력 세 줄은 각각 무엇인가?

### 3. ★★ 감싸고 나서 안쪽 메서드를 부르면 (예측)

```rust
// b26-04.rs
// ex.rs
// newtype 의 대가 — 안쪽 타입의 메서드를 전부 잃는다
struct Wrapper(Vec<String>);

fn main() {
    let mut w = Wrapper(vec![String::from("가")]);
    println!("{}", w.len());
    w.push(String::from("나"));
}
```

- 컴파일되는가? 안 되면 **에러 번호**와 **개수**는?
- `help:` 가 제안하는 고침안은 무엇인가?
- ★ 진단에 `` candidate #1: `ExactSizeIterator` `` 같은 줄이 나온다면 그것은 **쓸모 있는 제안인가**?
- newtype 의 **크기**는 안쪽 타입과 같은가 다른가?

### 4. ★★★ 잃은 것을 `Deref` 로 되찾으면 (예측)

```rust
// b26-05.rs
// ex.rs
// Deref 로 되찾으면 — 같이 새는 것이 있다
use std::ops::{Deref, DerefMut};

// 불변식: 안의 Vec 은 「항상 오름차순으로 정렬돼 있다」
struct SortedNames(Vec<String>);

impl SortedNames {
    fn new(mut v: Vec<String>) -> Self {
        v.sort();
        SortedNames(v)
    }
    fn insert(&mut self, s: &str) {
        // 불변식을 지키는 정문
        self.0.push(String::from(s));
        self.0.sort();
    }
    fn sorted_now(&self) -> bool {
        self.0.windows(2).all(|w| w[0] <= w[1])
    }
}

impl Deref for SortedNames {
    type Target = Vec<String>;
    fn deref(&self) -> &Vec<String> {
        &self.0
    }
}

impl DerefMut for SortedNames {
    fn deref_mut(&mut self) -> &mut Vec<String> {
        &mut self.0
    }
}

fn count(v: &Vec<String>) -> usize {
    v.len()
}

fn main() {
    let mut s = SortedNames::new(vec!["다".into(), "가".into(), "나".into()]);
    s.insert("라");
    println!("정문으로  {:?} · 정렬됐나 {}", s.0, s.sorted_now());

    // Deref 가 되살린 것 — Vec 의 메서드가 그대로 보인다
    println!("len()     {}", s.len());
    println!("first()   {:?}", s.first());
    println!("&Vec 인자 {}", count(&s));

    // ★ 그리고 DerefMut 이 뒷문을 연다
    s.push(String::from("가"));
    println!("뒷문 뒤   {:?} · 정렬됐나 {}", s.0, s.sorted_now());
    s.sort();
    println!("직접 고쳐 {:?} · 정렬됐나 {}", s.0, s.sorted_now());
}
```

- 여섯 줄의 출력을 **한 글자도 안 틀리게** 적을 수 있는가?
- ★★★ 이 타입의 약속은 「안의 `Vec` 은 항상 정렬돼 있다」였다. **그 약속은 끝까지 지켜지는가**?
- ★★ `Deref` 를 달아서 **새는 것 셋**을 갈라 댈 수 있는가?
- ★ `Deref` 로 **안 따라오는 것**은 무엇인가 — 1번에서 막혔던 `Display` 를 이렇게 얻을 수 있는가?

### 5. ★★ `?` 를 쓰려고 `From` 을 붙이면 (예측)

```rust
// b26-06.rs
// ex.rs
// 22번의 ? 가 요구하는 From 을 남의 타입 둘로 쓰려 하면
use std::io;
use std::num::ParseIntError;

impl From<ParseIntError> for io::Error {
    fn from(e: ParseIntError) -> io::Error {
        io::Error::new(io::ErrorKind::InvalidData, e)
    }
}

fn port(raw: &str) -> Result<u16, io::Error> {
    let n: u16 = raw.parse()?;
    Ok(n)
}

fn main() {
    println!("{:?}", port("8080"));
}
```

- 컴파일되는가? 에러는 **몇 건**인가?
- ★★ 밑줄은 **몇 군데**를 짚는가? 1번과 무엇이 다른가?
- ★★ `port` 안의 `?` 는 **추가 에러를 내는가**? 안 낸다면 왜인가?
- 이 코드를 통과시키는 가장 짧은 길은 무엇인가?

### 6. ★ 껍데기를 씌우면 뚫리나 (예측)

```rust
// b26-08.rs
// ex.rs
// 참조를 씌우면 뚫릴까 — &Vec<String> 에 Display
use std::fmt;

impl fmt::Display for &Vec<String> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "[{}]", self.join(", "))
    }
}

fn main() {
    let v = vec![String::from("가")];
    println!("{}", &v);
}
```

```rust
// b26-09.rs
// ex.rs
// Box 는 #[fundamental] 이다 — Box<내 타입> 은 「내 타입」으로 센다
use std::fmt;

struct Wrapper(Vec<String>);

impl fmt::Display for Box<Wrapper> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "상자 안 [{}]", self.0.join(", "))
    }
}

fn main() {
    let b = Box::new(Wrapper(vec![String::from("가"), String::from("나")]));
    println!("{}", b);
}
```

- 앞 소스는 컴파일되는가? 뒤 소스는?
- ★★★ 둘 다 거부된다면 **제목이 같은가**? 다르다면 어떻게 다른가?
- 갈린다면 그 이유는 무엇인가 — `&T` 와 `Box<T>` 의 공통점은?
- `#[fundamental]` 을 **내 타입에 붙일 수 있는가**?

### 7. 고아 규칙은 무엇을 막으려는 것인가 (왜)

- 이 규칙이 없으면 **누가 무슨 손해**를 보는가?
- 손해를 보는 쪽은 **잘못을 한 쪽인가**?
- 이 규칙은 컴파일 단위 중 **무엇**을 경계로 삼는가?
- 「트레이트도 내 것, 타입도 내 것」인 경우는 왜 문제가 안 되는가?

### 8. newtype 의 값과 대가 (경계)

- newtype 을 쓰는 이유는 **둘**이다. 무엇과 무엇인가?
- 런타임 비용은 얼마인가? 그것은 언어 보장인가 구현 세부인가?
- 잃은 메서드를 되찾는 길은 **둘**이다. 각각 무엇을 대가로 내는가?
- newtype 을 쓰면 **자동으로 따라오는 좋은 것**은 무엇인가?

### 9. `Deref` 를 언제 달고 언제 안 다나 (경계)

- `Deref` 를 다는 것이 **옳은** newtype 은 어떤 것인가?
- 불변식을 지키는 newtype 에 `DerefMut` 을 달면 무엇이 공개 API 가 되는가?
- 읽기만 열고 쓰기는 정문으로 받고 싶으면 무엇을 어떻게 하는가?
- `Deref` 대신 쓸 수 있는 **더 좁은 트레이트** 둘은 무엇인가?

### 10. 다른 언어에는 이 규칙이 있나 (연결)

- Kotlin 의 확장 함수에는 왜 고아 규칙이 필요 없는가? 대신 무엇을 잃는가?
- Go 에는 왜 「누가 구현했나」라는 물음이 없는가? 그럼 같은 문제를 무엇으로 막는가?
- Java 는 왜 고아 문제가 원리상 안 생기는가? 그 대가로 무엇을 만들게 되는가?
- Rust 에서 이 규칙과 가장 자주 부딪히는 실무 상황은 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
