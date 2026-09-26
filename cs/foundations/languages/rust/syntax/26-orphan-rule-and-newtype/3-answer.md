# rust/syntax/26 — 고아 규칙과 newtype — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 받은 것이다.\
> ★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
> ★★ **`--edition` 을 빼면 에디션 2015 다.** 이 갈래에서 그것은 「안 돌려 본 것」과 같다.\
> ★★ **외부 크레이트를 하나도 쓰지 않았다**(네트워크 없음). 「남의 크레이트」 자리는 **std 가 맡는다**.\
> 실험 파일 이름은 전부 **`ex.rs`** 로 고정했고 **진단의 줄 번호는 그 파일 기준**이다.\
> ★ `rustc --explain E0117` · `E0599` 는 **확인용으로만 열었고 본문에 옮기지 않았다.**
> ★★★ 이 주제의 근거는 **진단 전문**이다. 아래 블록의 **제목 · 밑줄 · `= note:` 줄**은
> 같은 rustc 판에서 안 흔들리는 칸이다([2-summary.md](2-summary.md) 머리말의 표).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ E0117 — 제목 한 줄이 규칙 전부다

**출력.**

```text
===== 소스: ex.rs =====
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
===== rustc --edition 2021 ex.rs -o ex =====
error[E0117]: only traits defined in the current crate can be implemented for types defined outside of the crate
 --> ex.rs:5:1
  |
5 | impl fmt::Display for Vec<String> {
  | ^^^^^^^^^^^^^^^^^^^^^^-----------
  |                       |
  |                       `Vec` is not defined in the current crate
  |
  = note: impl doesn't have any local type before any uncovered type parameters
  = note: for more information see https://doc.rust-lang.org/reference/items/implementations.html#orphan-rules
  = note: define and implement a trait or new type instead

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0117`.
(종료 코드 1)
```

**왜 그런가**

- **에러 번호는 E0117**, 에러는 **1건**, 종료 코드 **1** 이다.
- ★★★ **제목** — `` only traits defined in the current crate can be implemented for types defined outside of the crate ``.
  「밖에서 정의된 타입에는 **지금 크레이트에서 정의한 트레이트만** 구현할 수 있다」 —
  **규칙 전부가 이 한 줄**이고, 나머지 줄은 그 한 줄을 이 코드에 적용해 보여 주는 것이다.
- ★★ **밑줄은 두 종류가 갈라 그어진다.** 캐럿(`^`)이 `` impl fmt::Display for `` 를 덮고,
  **하이픈(`-`)이 `Vec<String>` 쪽만** 덮는다. 문구가 붙는 쪽은 **하이픈 쪽**이고
  `` `Vec` is not defined in the current crate `` 다 — **어느 쪽이 문제인지 손가락으로 짚어 준다.**
  (`Display` 쪽에는 아무 문구도 안 붙는다. 트레이트도 남의 것이지만 **둘 다 남의 것일 때만** 막히므로
  진단은 「남의 타입」 쪽 하나만 지목한다.)
- ★★ **`= note:` 는 세 줄**이고 역할이 각각 다르다.
  1. `` impl doesn't have any local type before any uncovered type parameters `` — **정식 판정 문구.**
     「내 타입이 **어디에도** 안 들어 있다」는 뜻이고, 뒤집으면 **인자 자리에라도 내 타입이 있으면 통과**한다(2번 답).
  2. `` for more information see … #orphan-rules `` — **근거**(Reference 링크).
  3. ★ `` define and implement a trait or new type instead `` — **처방.** 이 줄이 답을 두 갈래로 준다:
     **내 트레이트를 만들거나**(2번 답 ③) · **내 타입으로 감싸거나**(3번 답 이후의 newtype).
- 꼬리 두 줄(`` error: aborting due to 1 previous error `` · `` For more information … ``)까지가 한 블록이다.

### 2. ★★ 되는 것이 셋 — 막히는 칸은 하나뿐이다

**출력.**

```text
===== 소스: ex.rs =====
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
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
① 1200원
② 3400원
③ 7 1
(종료 코드 0)
```

**왜 그런가**

- **세 구현이 전부 통과한다**(종료 코드 0). 출력은 `` ① 1200원 `` · `` ② 3400원 `` · `` ③ 7 1 `` 세 줄이다.
- **①** `impl Display for Money` — **내 타입 + 남의 트레이트.** 가장 흔한 꼴이고 아무 문제가 없다.
- ★★ **②** `impl From<Money> for String` — `String` 도 `From` 도 std 것인데 **통과한다.**
  1번 답의 `= note:` 첫 줄이 「**uncovered 타입 파라미터 앞에 local type 이 있나**」를 물었고,
  여기서는 **트레이트의 인자 자리에 내 타입 `Money` 가 있어** 그 조건이 참이 된다.
  판정이 「`for` 뒤의 자기 타입」만 보는 것이 아니라 **`트레이트<T1,…,Tn> for T0` 를 왼쪽부터 훑는다**는 뜻이다.
  ★ 그래서 `Money(3400).into()` 가 `String` 을 내놓는다 — `From` 을 쓰면 `Into` 가 공짜로 따라온다.
- **③** `impl AsWon for i64` · `impl AsWon for Vec<String>` — **남의 타입 + 내 트레이트.**
  내가 만든 트레이트라면 남의 타입 아무 데나 붙고, **남의 제네릭 타입(`Vec<String>`)에도 된다.**
  `` ③ 7 1 `` 에서 `1` 은 `` vec!["가"].len() `` 이다.
- 정리하면 두 축 네 칸 중 **막히는 것은 「남의 트레이트 × 남의 타입」 한 칸뿐**이다.
  「고아 규칙 때문에 남의 타입은 못 건드린다」는 과장이다.

### 3. ★★ E0599 가 두 번 — 감싸는 순간 메서드를 전부 잃는다

**출력.**

```text
===== 소스: ex.rs =====
// ex.rs
// newtype 의 대가 — 안쪽 타입의 메서드를 전부 잃는다
struct Wrapper(Vec<String>);

fn main() {
    let mut w = Wrapper(vec![String::from("가")]);
    println!("{}", w.len());
    w.push(String::from("나"));
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0599]: no method named `len` found for struct `Wrapper` in the current scope
 --> ex.rs:7:22
  |
3 | struct Wrapper(Vec<String>);
  | -------------- method `len` not found for this struct
...
7 |     println!("{}", w.len());
  |                      ^^^ method not found in `Wrapper`
  |
  = help: items from traits can only be used if the trait is implemented and in scope
  = note: the following trait defines an item `len`, perhaps you need to implement it:
          candidate #1: `ExactSizeIterator`
help: one of the expressions' fields has a method of the same name
  |
7 |     println!("{}", w.0.len());
  |                      ++

error[E0599]: no method named `push` found for struct `Wrapper` in the current scope
 --> ex.rs:8:7
  |
3 | struct Wrapper(Vec<String>);
  | -------------- method `push` not found for this struct
...
8 |     w.push(String::from("나"));
  |       ^^^^ method not found in `Wrapper`
  |
help: one of the expressions' fields has a method of the same name
  |
8 |     w.0.push(String::from("나"));
  |       ++

error: aborting due to 2 previous errors

For more information about this error, try `rustc --explain E0599`.
(종료 코드 1)
```

**왜 그런가**

- **컴파일 안 된다.** 에러 번호는 **E0599**, 개수는 **2** 다(`len` 하나, `push` 하나).
  `Wrapper` 는 `Vec<String>` **이 아니다** — 같은 바이트를 들고 있을 뿐 표면이 전혀 다르다.
- ★ `help:` 의 고침안은 `` one of the expressions' fields has a method of the same name `` 이고,
  제안 코드는 **`w.0.len()`** · **`w.0.push(…)`** 다. **필드를 거쳐서 부르라**는 뜻이다.
- ★ `` candidate #1: `ExactSizeIterator` `` 는 **쓸모없는 제안**이다.
  진단이 「`len` 이라는 이름의 항목을 가진 트레이트」를 훑다가 걸린 것일 뿐,
  `Wrapper` 를 이터레이터로 만들라는 말이 아니다. **읽고 흘린다** — 진짜 답은 `help:` 쪽이다.
  (`push` 쪽에는 이 줄이 아예 없다. 이름이 겹치는 트레이트가 없기 때문이다.)
- **크기는 안쪽과 같다.** 3번 블록이 아니라 8번 답의 블록이 그것을 찍는다 — `Wrapper` 24 · `Vec<String>` 24.
  ★ **표면은 비싸고 크기는 공짜**라는 것이 newtype 의 한 줄 요약이다.

### 4. ★★★ `Deref` 는 되찾아 주고 동시에 새게 한다

**출력.**

```text
===== 소스: ex.rs =====
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
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
정문으로  ["가", "나", "다", "라"] · 정렬됐나 true
len()     4
first()   Some("가")
&Vec 인자 4
뒷문 뒤   ["가", "나", "다", "라", "가"] · 정렬됐나 false
직접 고쳐 ["가", "가", "나", "다", "라"] · 정렬됐나 true
(종료 코드 0)
```

**왜 그런가**

- **여섯 줄이 위 블록 그대로**다. 핵심은 다섯째 줄의 `정렬됐나 false` 다.
- ★★★ **약속은 끝까지 안 지켜진다.** 이 타입의 불변식은 「안의 `Vec` 은 항상 오름차순」이었고
  정문은 `insert` 하나였다. `DerefMut` 을 다는 순간 `` s.push(String::from("가")) `` 가 **그 정문을 우회**한다 —
  `가` 가 맨 뒤에 붙어 `["가","나","다","라","가"]` 가 되고 `sorted_now()` 가 `false` 를 답한다.
  마지막 줄의 `s.sort()` 도 같은 뒷문이다. **우연히** 정렬이 복구됐을 뿐 약속이 지켜진 것이 아니다.
- ★★ **새는 것 셋을 갈라 보면** —
  ① **메서드가 샌다** — `len`·`first`·`push`·`sort` 등 `Vec<String>` 의 표면 전부가 `SortedNames` 에 보인다.
  ② **타입이 샌다** — `` count(&s) `` 가 된다. `&SortedNames` 가 `&Vec<String>` 자리에 그대로 들어간다
     (역참조 강제 — [**14번 주제**](../14-string-vs-str/)가 정본이다).
  ③ ★ **불변식이 샌다** — ①·②의 결과다. **정문이 하나가 아니게 된다.**
- ★ **`Deref` 로 안 따라오는 것은 트레이트 구현이다.** `Vec<String>` 이 `Display` 를 구현했든 말든
  `SortedNames` 가 그것을 구현한 것은 아니다. 그래서 **1번에서 막힌 `Display` 를 `Deref` 로는 못 얻는다** —
  newtype 에 **직접 써야** 한다. 이것이 「`Deref` 를 달면 newtype 의 단점이 다 사라진다」가 틀린 이유다.

### 5. ★★ `?` 를 위한 `From` — 고아 규칙을 처음 만나는 자리

**출력.**

```text
===== 소스: ex.rs =====
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
===== rustc --edition 2021 ex.rs -o ex =====
error[E0117]: only traits defined in the current crate can be implemented for types defined outside of the crate
 --> ex.rs:6:1
  |
6 | impl From<ParseIntError> for io::Error {
  | ^^^^^-------------------^^^^^---------
  |      |                       |
  |      |                       `std::io::Error` is not defined in the current crate
  |      `ParseIntError` is not defined in the current crate
  |
  = note: impl doesn't have any local type before any uncovered type parameters
  = note: for more information see https://doc.rust-lang.org/reference/items/implementations.html#orphan-rules
  = note: define and implement a trait or new type instead

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0117`.
(종료 코드 1)
```

**왜 그런가**

- **컴파일 안 되고, 에러는 1건**이다(E0117).
- ★★ **밑줄이 두 군데를 짚는다.** 1번에서는 `Vec<String>` 한 군데였는데 여기서는
  `` `ParseIntError` is not defined in the current crate `` 와
  `` `std::io::Error` is not defined in the current crate `` 가 **각각** 붙는다.
  **트레이트 인자와 자기 타입이 둘 다 남의 것**이라 짚을 곳이 둘이다 —
  2번 답의 ②가 통과한 이유(인자에 내 타입)가 **여기서는 하나도 성립하지 않는다.**
- ★★ **`port` 안의 `?` 는 추가 에러를 안 낸다.** rustc 가 **거부한 `impl` 을 그래도 등록해 두고**
  타입 검사를 진행하기 때문이다(에러 복구 전략 — 구현 세부).
  **「에러 1건」이 「문제 1곳」이라는 뜻이 아니다.** 고쳐서 다시 던져야 남은 문제가 보인다.
- **가장 짧은 길은 내 오류 타입을 하나 만드는 것**이다 — 1번 답의 `= note:` 셋째 줄 그대로다.

```text
===== 소스: ex.rs =====
// ex.rs
// newtype 으로 그 From 을 뚫는다 — 내 오류 타입 하나면 된다
use std::fmt;
use std::num::ParseIntError;

#[derive(Debug)]
struct PortError(ParseIntError);

impl fmt::Display for PortError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "포트를 못 읽었다: {}", self.0)
    }
}

impl From<ParseIntError> for PortError {
    fn from(e: ParseIntError) -> PortError {
        PortError(e)
    }
}

fn port(raw: &str) -> Result<u16, PortError> {
    let n: u16 = raw.parse()?;
    Ok(n)
}

fn main() {
    println!("{:?}", port("8080"));
    match port("팔공팔공") {
        Ok(n) => println!("{}", n),
        Err(e) => println!("{}", e),
    }
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
Ok(8080)
포트를 못 읽었다: invalid digit found in string
(종료 코드 0)
```

- `PortError(ParseIntError)` 는 **내 타입**이므로 `impl From<ParseIntError> for PortError` 가 통과하고,
  `?` 가 그 위에서 돈다. 출력은 `Ok(8080)` 과 `` 포트를 못 읽었다: invalid digit found in string `` 두 줄이다.
- ★ [**24번 주제**](../24-error-type-design/)가 「오류 타입을 왜 직접 만드나」라고 했던 이유 중 하나가 이것이다 —
  **편의가 아니라 고아 규칙이 강제하는 구조**다.

### 6. ★★★ 껍데기는 뚫어 주지 않는다 — 다만 제목이 갈린다

**출력.**

```text
===== 소스: ex.rs =====
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
===== rustc --edition 2021 ex.rs -o ex =====
error[E0117]: only traits defined in the current crate can be implemented for arbitrary types
 --> ex.rs:5:1
  |
5 | impl fmt::Display for &Vec<String> {
  | ^^^^^^^^^^^^^^^^^^^^^^------------
  |                       |
  |                       `Vec` is not defined in the current crate
  |
  = note: impl doesn't have any local type before any uncovered type parameters
  = note: for more information see https://doc.rust-lang.org/reference/items/implementations.html#orphan-rules
  = note: define and implement a trait or new type instead

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0117`.
(종료 코드 1)
```

```text
===== 소스: ex.rs =====
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
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
상자 안 [가, 나]
(종료 코드 0)
```

**왜 그런가**

- **앞 소스는 거부되고 뒤 소스는 통과한다.** 뒤쪽 출력은 `상자 안 [가, 나]` 한 줄이다.
- ★★★ **거부된 쪽의 제목이 1번과 다르다.** 1번은
  `` … can be implemented for types defined outside of the crate `` 였는데 여기서는
  `` … can be implemented for arbitrary types `` 다. **번호는 똑같이 E0117** 이고 `= note:` 세 줄도 같다.
  `&T` 가 **`#[fundamental]`** 이라 자기 타입이 「그냥 남의 타입」으로 분류되지 않아 **판정 경로가 갈린 것**이다.
  ★ **같은 규칙인데 제목이 둘**이라는 것을 알아 두면 에러를 검색할 때 헷갈리지 않는다.
- ★★ **`&T` 와 `Box<T>` 의 공통점이 `#[fundamental]`** 이다. 이 표시가 붙은 껍데기는 **속을 가리지 않는다** —
  그래서 `Box<Wrapper>` 는 속(`Wrapper`)이 내 타입이므로 **껍데기째 내 타입으로 센다.**
  `&Vec<String>` 이 막히는 것은 껍데기 때문이 아니라 **속(`Vec`)이 남의 것**이기 때문이다.
  **껍데기가 아니라 속이 판정한다.**
- ★ **`#[fundamental]` 은 내 타입에 못 붙인다.** std 만 쓰는 불안정 어트리뷰트다
  (`&T`·`&mut T`·`Box<T>`·`Pin<T>`). 이 주제에서는 **이름과 결과까지만** 안다.

### 7. 무엇을 막으려는 규칙인가

- **이 규칙이 없으면 손해를 보는 쪽은** 「**두 크레이트를 같이 쓰는 사람**」이다.
  내가 `impl Display for Vec<String>` 을 쓰고 남도 같은 것을 쓰면, 두 크레이트를 한 프로그램에 넣는 순간
  **같은 타입·같은 트레이트에 구현이 둘**이 되어 어느 쪽을 부를지 정할 수 없다.
- ★★ **손해를 보는 쪽은 잘못을 한 쪽이 아니다.** 쓰는 사람은 두 크레이트를 의존성에 적었을 뿐이고,
  고칠 수단도 없다(남의 코드를 못 고친다). **잘못 없는 쪽이 깨지는 구조**라서 언어가 **처음부터** 막는다.
- **경계는 크레이트**다 — 컴파일 단위. 「내 것 / 남의 것」이 여기서 갈린다(정본은 목록의 **46번 주제**).
- **트레이트도 내 것이고 타입도 내 것이면** 충돌이 나도 **내 크레이트 안**에서 난다.
  그것은 컴파일러가 그 자리에서 **E0119**(`conflicting implementations`)로 잡아 주고
  **내가 고칠 수 있다**([**25번 주제**](../25-traits-definition-impl-default-methods-and-associated-types/) 3번 답).
  고아 규칙이 막는 것은 **고칠 수 없는 충돌**뿐이다.

### 8. newtype — 크기는 공짜, 표면은 비싸다

**출력.**

```text
===== 소스: ex.rs =====
// ex.rs
// newtype 으로 뚫기 — 껍데기 하나가 「내 타입」을 만든다
use std::fmt;

struct Wrapper(Vec<String>);

impl fmt::Display for Wrapper {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "[{}]", self.0.join(", "))
    }
}

fn main() {
    let w = Wrapper(vec![String::from("가"), String::from("나")]);
    println!("{}", w);
    println!("안쪽은 그대로 {:?}", w.0);
    println!("크기 Wrapper {} · Vec<String> {}",
             std::mem::size_of::<Wrapper>(),
             std::mem::size_of::<Vec<String>>());
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
[가, 나]
안쪽은 그대로 ["가", "나"]
크기 Wrapper 24 · Vec<String> 24
(종료 코드 0)
```

**왜 그런가**

- **쓰는 이유는 둘이다.** ① **고아 규칙을 뚫으려고** — 남의 타입에 std 트레이트를 붙여야 할 때
  (`Display`·`From`·`Iterator` 처럼 내 트레이트로 대신할 수 없는 것들).
  ② **불변식을 지키려고** — 이때는 표면을 좁히는 것이 **대가가 아니라 목적**이다.
- **런타임 비용은 이 판의 관찰로 0 이다** — `Wrapper` 24 · `Vec<String>` 24 로 **같다.**
  ★ 다만 이것은 **구현 세부**다. 기본 표현(`repr(Rust)`)의 배치는 언어가 보장하지 않는다.
  「필드 하나짜리 구조체는 그 필드와 같은 크기」는 **관찰이지 보장이 아니다.**
- **잃은 메서드를 되찾는 길은 둘**이고 대가가 다르다.
  ① **위임 메서드를 손으로 쓴다** — 대가는 **손품**(메서드 수만큼 줄이 는다). 대신 **무엇을 열지 내가 고른다.**
  ② **`Deref` 를 단다** — 대가는 **표면 전부와 불변식**(4번 답). 손품은 0 이다.
- ★ **자동으로 따라오는 좋은 것은 캡슐화**다. 감싸는 순간 안쪽 표면이 **기본값으로 닫히고**,
  `w.0` 을 통하지 않으면 아무것도 못 한다. 3번 답의 E0599 두 개가 **그 캡슐화가 실제로 작동한 증거**다.

### 9. `Deref` 를 다는 자리와 안 다는 자리

- ★ **다는 것이 옳은 newtype 은** 「**스마트 포인터**」다 — 값을 **감싸 들고 다니는 것이 전부**이고
  안쪽 표면을 **그대로 열어 주는 것이 의도**인 것. std 의 `Box`·`Rc`·`String` 이 그 꼴이다.
  (정본은 [목록의 **43번 주제**](../43-deref-coercion-and-smart-pointers/).)
- **불변식을 지키는 newtype 에 `DerefMut` 을 달면 「안쪽 타입의 가변 메서드 전부」가 공개 API 가 된다.**
  4번 답에서 `push`·`sort` 가 그랬다. 문서에 안 적었어도 **쓸 수 있으면 공개 API** 다 —
  나중에 안쪽 타입을 바꾸면 그 전부가 깨진다.
- **읽기만 열고 쓰기는 정문으로 받고 싶으면 `Deref` 만 달고 `DerefMut` 은 안 단다.**
  그러면 `len()`·`first()` 는 되고 `push()` 는 안 된다. ★ 완전하지는 않다 —
  `&Vec<String>` 로 새는 것(4번 답 ②)은 여전히 막히지 않는다.
- ★ **더 좁은 트레이트 둘은 `AsRef` 와 `Borrow`** 다([목록의 **29번 주제**](../29-conversion-traits-from-into-tryfrom-asref-borrow/)가 정본).
  **자동으로 끼어들지 않고**(`.as_ref()`·`.borrow()` 라고 적어야 하고),
  **어느 타입으로 열지 고를 수 있다.** `Deref` 는 타깃이 하나뿐이고 **부르지 않아도 끼어든다.**

### 10. 다른 언어는 어디서 같은 문제를 막나

- **Kotlin 의 확장 함수**([`kotlin/syntax/13-extension-functions-and-properties/`](../../../kotlin/syntax/13-extension-functions-and-properties/)) —
  **정적 디스패치**라 충돌이 원리상 안 난다. 확장 함수는 **가져온(import) 쪽에서만 보이고**
  호출할 것이 **정적 타입으로** 정해지므로, 두 라이브러리가 같은 이름을 붙여도 프로그램이 깨지지 않는다.
  그래서 **고아 규칙이 필요 없다.** ★ **대신 잃는 것은 다형성**이다 —
  확장 함수는 인터페이스 구현이 아니므로 `List<T>` 를 받는 제네릭 경계나 가상 호출에 **쓰이지 않는다.**
- **Go 의 인터페이스**(Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **20번**) —
  **구현을 선언하지 않는다**(메서드 집합이 맞으면 그것이 구현이다). 그러니
  「누가 구현했나」라는 물음 **자체가 없다.** ★ 같은 문제는 **다른 자리에서** 막는다 —
  **남의 패키지 타입에는 메서드를 못 붙인다.** 붙이려면 감싸야 하고, **그것이 곧 newtype** 이다.
- **Java 의 인터페이스**([`java/syntax/11-interfaces-default-methods/`](../../../java/syntax/11-interfaces-default-methods/)) —
  **클래스 선언에 `implements` 를 적어야** 하므로 남이 나중에 붙일 수 없다. **고아 문제가 원리상 안 생긴다.**
  ★ 그 대가로 **어댑터 클래스를 만들게 되는데, 그것이 곧 newtype 이다** —
  Rust 는 「감싸기」를 **예외적 우회**로 쓰고 Java 는 **기본 수단**으로 쓴다.
- ★ **Rust 에서 가장 자주 부딪히는 실무 상황은 `?` 를 위한 `From`** 이다(5번 답).
  std 오류에서 std 오류로 가는 변환을 내가 못 쓰기 때문에, 오류 타입을 하나 만들게 된다.
  그다음으로 흔한 것이 **남의 타입을 내 형식으로 찍고 싶을 때의 `Display`**(1번 답)다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서·서머리의 **모든 블록** | `capture.sh` 가 `rustc --edition 2021 ex.rs -o ex` 로 컴파일하고 `./ex` 실행 | 배치 내내 + **제출 전 전수 재실행 1회** | `normalize-shaky.py` — **9블록 전부 동일** |
| ★★★ **E0117 전문** | `b26-01` — 남의 타입 × 남의 트레이트 | 1 | 제목 · 밑줄 1군데 · `= note:` 3줄 |
| ★★ **되는 셋** | `b26-02` — ①내 타입+남의 트레이트 ②인자에 내 타입 ③내 트레이트 | 1 | **셋 다 통과**(종료 코드 0) |
| newtype 의 크기 | `b26-03` 의 `size_of` | 1 | **24 대 24** — ★ 구현 세부 |
| ★ **newtype 의 대가** | `b26-04` — 감싼 뒤 안쪽 메서드 호출 | 1 | **E0599 ×2** |
| ★★★ **`Deref` 로 새는 것** | `b26-05` — 정문·뒷문을 한 프로그램에서 | 1 | `정렬됐나 false` 가 **약속이 깨진 순간** |
| ★★ **`?` 를 위한 `From`** | `b26-06`(E0117 · 밑줄 2군데) · `b26-07`(newtype 으로 통과) | 2 | 에러 **1건**뿐 — `?` 는 추가 에러 없음 |
| ★ **`#[fundamental]`** | `b26-08`(`&Vec<String>` 거부) · `b26-09`(`Box<Wrapper>` 통과) | 2 | **제목이 갈린다** |
| **안 던져 본 것** — E0119 | 7번 답에서 **번호만** 적었다(정본은 25번 주제) | 0 | ★ 블록이 없으므로 번호 외에는 단정하지 않았다 |
| 외부 크레이트 | **쓰지 않음** | 0 | std 만 |

**구현 의존 항목**(버전·환경이 바뀌면 **다시 찍어야 하는** 것).

| 항목 | 왜 |
|---|---|
| `Wrapper` 와 `Vec<String>` 이 **둘 다 24바이트**인 것 | ★ `repr(Rust)` 의 배치는 **언어 보장이 아니다** |
| E0117 의 **제목이 둘**인 것(`` … outside of the crate `` 대 `` … arbitrary types ``) | ★ 판정 경로에 따라 문구가 갈린다 — 진단 품질 개선으로 바뀔 수 있다 |
| `` candidate #1: `ExactSizeIterator` `` 같은 제안 | ★ 진단이 이름으로 훑어 준 것 — 후보 목록은 std 판에 달렸다 |
| 거부된 `impl` 을 **그래도 등록**해 뒤 에러를 줄이는 것 | ★ rustc 의 **에러 복구 전략** |
| `invalid digit found in string` | ★ std 의 `ParseIntError` 문구 |
| `help:` 문구와 제안 코드(`w.0.len()`) | ★ 진단 품질 개선으로 자주 바뀌는 자리다 |

★ **다시 찍는 법** — `capture.sh` 를 그대로 돌리고 `normalize-shaky.py` 로 견준다.
이 주제에는 패닉도 주소도 없으므로 **달라지는 파일이 하나도 없어야** 한다.
