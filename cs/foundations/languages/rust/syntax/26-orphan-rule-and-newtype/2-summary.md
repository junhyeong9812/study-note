# rust/syntax/26 — 고아 규칙과 newtype — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Reference — Implementations / Orphan rules](https://doc.rust-lang.org/reference/items/implementations.html#orphan-rules) ·
> [std — `trait Deref`](https://doc.rust-lang.org/std/ops/trait.Deref.html) ·
> [std — `trait From`](https://doc.rust-lang.org/std/convert/trait.From.html).
> ★ `rustc --explain E0117` · `E0599` 는 **확인용으로만 열었고 본문에 옮기지 않았다.**
> **실행 검증** — 이 문서의 모든 출력·에러는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 받은 것이다.\
> ★★ **`rustc ex.rs` 만 쓰면 에디션 2015 다** — 에디션을 안 밝힌 결과는 다른 언어를 컴파일한 것과 같다.\
> ★★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
> ★★ **외부 크레이트를 하나도 쓰지 않았다**(네트워크 없음). 「남의 크레이트」 자리는 **std 가 맡는다** —
> `Vec`·`String`·`Display`·`From`·`io::Error` 가 전부 남의 것이다.
> **버전** — 고아 규칙은 1.0.0 부터, 지금의 완화된 판정(covered type 규칙)은 RFC 2451 이후다. **에디션과 무관하다.**\
> ★★★ **이 주제는 「에러가 곧 규칙」인 주제다.** 아래 **E0117 전문의 `= note:` 세 줄**이
> 규칙·근거·처방을 그대로 말해 준다((1)). 본문은 그 전문을 읽는 순서로 짜여 있다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | 패닉 첫 줄 `thread 'main' (…)` 괄호 안의 OS 스레드 id | 이 주제에는 패닉 블록이 없지만 규칙은 같다 |
| **흔들린다** | `0x…` 주소 | 실행마다 다르다 |
| 안 흔들린다 | **종료 코드 0 · 1** | 컴파일 실패는 1 이다 |
| 안 흔들린다 | E0117 의 **제목 · `= note:` 세 줄 · 밑줄이 짚는 위치** | 같은 rustc 판에서 고정이다 — 이 주제의 핵심 근거다 |
| 안 흔들린다 | `Wrapper` 와 `Vec<String>` 이 **둘 다 24바이트**인 것 | ★ 같은 판·같은 타깃에서 고정. **언어 보장은 아니다**(§구현 세부) |
| 안 흔들린다 | `invalid digit found in string` | std 의 `ParseIntError` 문구 — 같은 std 판에서 고정이다 |

## 한눈에 — 쉽게 말하면

**고아 규칙은 「이 구현이 어느 집에 사는가」를 반드시 하나로 정하게 만드는 규칙이다.**

| 비유 | 실체 |
|---|---|
| 「**남의 집 가전제품에 남의 회사 스티커 붙이기**」 | ★★★ **금지** — 남의 타입에 남의 트레이트 → **E0117**((1)) |
| 「내 집 가전제품에 남의 회사 스티커」 | **된다** — 내 타입 + 남의 트레이트((2)) |
| 「남의 집 가전제품에 **내가 만든** 스티커」 | **된다** — 남의 타입 + 내 트레이트((2)) |
| 「남의 가전제품을 **내 상자에 넣고** 스티커 붙이기」 | ★★ **newtype** — 껍데기 하나가 「내 타입」을 만든다((3)) |
| 상자에 넣었더니 **버튼이 다 가려졌다** | ★ **newtype 의 대가** — 안쪽 메서드를 전부 잃는다((4)) |
| 상자에 **구멍을 뚫어** 버튼을 꺼낸다 | **`Deref`** — 메서드가 되살아난다. ★★ **불변식도 같이 샌다**((5)) |

- ★★★ **판정은 한 줄이다 — 「트레이트와 자기 타입 중 적어도 하나가 내 크레이트 것인가?」**
  둘 다 남의 것이면 막힌다. ★ 단 **트레이트의 인자 자리에 내 타입이 있으면 그것도 「내 것」으로 센다**((2)의 ②).
- ★★ **막는 이유는 「둘 다 붙였을 때 누가 이기나」를 정할 수 없어서**다 —
  내가 `impl Display for Vec<String>` 을 쓰고 남도 쓰면, 두 크레이트를 같이 쓰는 순간 충돌이 난다.
  **쓰는 쪽이 아무 잘못도 안 했는데 깨지는 것**이라 언어가 처음부터 막는다.
- ★ **처방은 진단이 직접 적어 준다** — `` define and implement a trait or new type instead ``.
  「내 트레이트를 만들거나(2), **내 타입으로 감싸라**(3)」는 두 갈래가 그 한 줄이다.

```text
   두 축으로 갈리는 네 칸 — 막히는 것은 한 칸뿐이다

                    │  트레이트가 내 것  │  트레이트가 남의 것
   ─────────────────┼───────────────────┼─────────────────────
   자기 타입이 내 것 │       ✔           │        ✔   (2)①
   ─────────────────┼───────────────────┼─────────────────────
   자기 타입이 남 것 │   ✔   (2)③       │  ✘ E0117   (1)
                    │                   │  ★ 단 인자에 내 타입이 있으면 ✔ (2)②


   막힌 칸을 뚫는 길 — 껍데기 하나

   impl Display for Vec<String>        ✘   남의 타입에 직접
                  │
                  ▼
   struct Wrapper(Vec<String>);            ← 이 줄 하나가 「내 타입」을 만든다
   impl Display for Wrapper            ✔


   그 대가와 되찾기

   Wrapper                  Wrapper + Deref<Target = Vec<String>>
   ├─ Display  ✔            ├─ Display  ✔
   ├─ len()    ✘ E0599      ├─ len()    ✔  (안쪽 것이 보인다)
   ├─ push()   ✘ E0599      ├─ push()   ✔  ← ★ 지키려던 불변식이 여기로 샌다
   └─ .0 으로만 접근         └─ &Wrapper 가 &Vec<String> 자리에 그냥 들어간다
```

> **고아 규칙(orphan rule)** — 트레이트도 타입도 남의 것이면 그 구현을 못 쓰게 막는 규칙.\
> 예: 내 크레이트에서 `impl Display for Vec<String>` 은 안 된다.

> **newtype** — 남의 타입을 **필드 하나짜리 구조체로 감싼 것**.\
> 예: `struct Wrapper(Vec<String>);` — 이것은 내 타입이므로 무엇이든 구현할 수 있다.

> **`Deref`** — `*x` 와 **메서드 찾기**를 안쪽 타입으로 넘기는 트레이트.\
> 예: `Deref<Target = Vec<String>>` 를 달면 `w.len()` 이 `w.0.len()` 처럼 동작한다.

> **`#[fundamental]`** — `&T`·`Box<T>` 처럼 **껍데기가 속을 안 가리게** 표시된 std 타입.\
> 속이 내 타입이면 껍데기째로도 「내 타입」으로 센다((7)).

## 이 주제가 답하려는 질문

1. ★★★ **무엇이 막히고 무엇이 되나** — 네 칸 중 막히는 것은 하나뿐이고, **E0117 전문이 그 규칙을 그대로 말한다**((1)·(2)).
2. **막힌 자리를 어떻게 뚫나** — newtype 으로 뚫고, **무슨 대가를 치르나**((3)·(4)·(5)).
3. ★★ **이것이 실제로 어디서 걸리나** — `?` 를 쓰려고 `From` 을 구현할 때 바로 걸린다((6)).

★ [**25번 주제**](../25-traits-definition-impl-default-methods-and-associated-types/)가 「**무엇을** 구현하나」였다면,
여기는 「**누가 구현할 수 있나**」다.

## 동작 방식

### (0) 이 주제가 쓰는 네 창

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **E0117 전문을 통째로 읽기** | **규칙 자체** — 제목·밑줄·`= note:` 세 줄 | ★ 이 주제의 고유 창 |
| **네 칸을 전수로 던지기** | 막히는 칸이 **하나뿐**이라는 것 | 기본 창 |
| ★ **뚫은 뒤에 무엇을 잃었나 세기** | newtype 의 **대가**(E0599 두 개) | ★ 이 주제의 고유 창 |
| ★★ **되찾은 뒤에 무엇이 새나 찍기** | `Deref` 가 **불변식을 흘리는 것**을 출력으로 | ★ 이 주제의 고유 창 |

★★★ 첫째 창이 본체다. 이 주제는 **규칙을 외우는 주제가 아니라 진단 한 편을 읽는 주제**다 —
아래 전문에 규칙(제목) · 근거(`= note:` 첫 줄) · 처방(`= note:` 셋째 줄)이 **전부 들어 있다.**

### (1) ★★★ E0117 전문 — 이 진단이 곧 규칙이다

**언제 쓰나** — 남의 타입을 조금 더 편하게 쓰려고 트레이트를 붙이려 할 때. 거의 언제나 여기서 막힌다.

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

**전문을 네 조각으로 읽는다.**

- ★★★ **제목** — `` only traits defined in the current crate can be implemented for types defined outside of the crate ``.
  **「밖에서 정의된 타입에는 지금 크레이트에서 정의한 트레이트만 구현할 수 있다」** — 규칙 전부가 이 한 줄이다.
- ★★ **밑줄** — `` impl fmt::Display for Vec<String> `` 아래에 캐럿과 하이픈이 **갈라 그어진다.**
  하이픈이 그어진 쪽(`Vec<String>`)에 `` `Vec` is not defined in the current crate `` 가 붙는다 —
  **어느 쪽이 문제인지 손가락으로 짚어 준다.**
- ★ **`= note:` 첫 줄** — `` impl doesn't have any local type before any uncovered type parameters ``.
  이것이 **정식 판정 문구**다. 「내 타입이 **어디에도** 안 들어 있다」는 말이고,
  뒤집으면 **인자 자리에라도 내 타입이 있으면 통과**한다는 뜻이다((2)의 ②).
- ★ **`= note:` 셋째 줄** — `` define and implement a trait or new type instead ``.
  **처방 두 갈래**다 — 내 트레이트를 만들거나((2)③), **내 타입으로 감싸거나**((3)).

### (2) 되는 셋 — 한쪽만 내 것이면 통과한다

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

- **① 내 타입 + 남의 트레이트** — `impl Display for Money`. 가장 흔한 꼴이고 아무 문제가 없다.
- ★★ **② 자기 타입도 트레이트도 남의 것인데 통과한다** — `impl From<Money> for String`.
  `String` 도 `From` 도 std 것이지만 **트레이트의 인자 자리에 내 타입 `Money` 가 있다.**
  (1)의 `= note:` 가 말한 「uncovered type parameter 앞에 local type 이 있나」가 **여기서 참**이 된다.
- **③ 남의 타입 + 내 트레이트** — `impl AsWon for i64`·`for Vec<String>`.
  **내가 만든 트레이트라면 남의 타입 아무 데나 붙여도 된다.** 제네릭 타입(`Vec<String>`)도 된다.
- ★ 그래서 네 칸 중 **막히는 것은 (1)의 한 칸뿐**이다. 「고아 규칙 때문에 아무것도 못 한다」는 인상은 과장이다.

### (3) ★★ newtype 으로 뚫기 — 껍데기 한 줄

**언제 쓰나** — (1)에서 막혔고, 내 트레이트로는 대신할 수 없을 때(`Display`·`From`·`Iterator` 같은 std 트레이트).

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

- **`struct Wrapper(Vec<String>);` 한 줄이 「내 타입」을 만든다.** 그 뒤로는 아무 트레이트나 붙는다.
- ★ **런타임 비용이 없다** — `Wrapper` 와 `Vec<String>` 이 **둘 다 24바이트**다.
  필드 하나짜리 구조체는 그 필드와 같은 배치를 갖는다(★ 이 수치는 이 판의 관찰이다 — §구현 세부).
- ★ 안쪽은 `w.0` 으로 그대로 꺼낼 수 있다. **감싼 것이지 바꾼 것이 아니다.**

### (4) ★ newtype 의 대가 — 메서드를 전부 잃는다

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

- ★★ **E0599 가 두 번** — `` no method named `len` found for struct `Wrapper` `` ·
  `` no method named `push` ``. **`Wrapper` 는 `Vec<String>` 이 아니다.**
- ★ `help:` 가 답을 준다 — `` one of the expressions' fields has a method of the same name `` 하고
  **`w.0.len()`** 으로 고쳐 준다. 필드를 거치면 된다는 뜻이다.
- ★ `` the following trait defines an item `len`, perhaps you need to implement it: candidate #1: `ExactSizeIterator` `` 는
  **엉뚱한 제안**이다 — 진단이 이름이 같은 트레이트를 훑다가 찾은 것이다. 이런 줄은 **읽고 흘린다.**
- **이것이 newtype 의 값이자 대가다.** 캡슐화가 공짜로 따라오지만, 쓰려면 **위임 메서드를 손으로 써야** 한다.

### (5) ★★★ `Deref` 로 되찾기 — 그리고 무엇이 새나

**언제 쓰나** — 위임 메서드를 수십 개 쓰기 싫을 때. **불변식을 지키려고 감쌌다면 다시 생각한다.**

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

- **되찾힌다.** `s.len()`·`s.first()` 가 그냥 된다. 게다가 `count(&s)` 처럼
  **`&SortedNames` 가 `&Vec<String>` 자리에 그대로 들어간다**(역참조 강제 — [**14번 주제**](../14-string-vs-str/)가 정본이다).
- ★★★ **그런데 같은 문으로 불변식이 샌다.** 이 타입의 약속은 「안의 `Vec` 은 **항상 정렬돼 있다**」였고
  정문은 `insert` 하나였다. `DerefMut` 을 달자 **`s.push("가")` 가 그 정문을 우회했고**,
  출력의 `정렬됐나 false` 가 **약속이 깨진 순간**이다.
- ★★ **새는 것을 세 가지로 갈라 보면** —
  ① **메서드가 샌다**(`push`·`sort` 등 안쪽의 전부) ② **타입이 샌다**(`&SortedNames` 를 `&Vec<String>` 로 받을 수 있다)
  ③ ★ **불변식이 샌다** — ①·②의 결과다. **정문이 하나가 아니게 된다.**
- ★ **안 새는 것도 있다** — **트레이트 구현은 `Deref` 로 안 따라온다.**
  `Vec<String>` 이 무엇을 구현했든 `SortedNames` 가 그것을 구현한 것은 아니다.
  (그래서 (1)에서 막힌 `Display` 를 `Deref` 로 얻을 수는 **없다** — newtype 에 직접 써야 한다.)
- ★★ **처방** — **`Deref` 는 「스마트 포인터」에만** 단다(`Box`·`Rc`·`String`).
  **불변식을 지키는 newtype 에는 `Deref` 를 달지 말고**, 꼭 읽기만 열고 싶으면
  `Deref` 만 달고 **`DerefMut` 은 안 다는** 절충이 있다. 정본은 목록의 **43번 주제**다.

### (6) ★★ 실제로 어디서 걸리나 — `?` 를 위한 `From`

**언제 쓰나** — [**22번 주제**](../22-result-question-mark-and-from/)의 `?` 를 쓰려고 오류 변환을 붙일 때.

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

- ★★ **여기가 고아 규칙을 처음 만나는 자리다.** `?` 는 `From` 을 부르는데,
  **std 오류에서 std 오류로 가는 변환**은 내가 못 쓴다 — `ParseIntError` 도 `io::Error` 도 남의 것이다.
- ★★ **밑줄이 양쪽을 다 짚는다** — 이번에는 캐럿과 하이픈이 **두 군데**에 그어지고
  `` `ParseIntError` is not defined in the current crate `` 와 `` `std::io::Error` is not defined in the current crate `` 가
  **각각** 붙는다. (1)에서는 한 군데였다.
- ★ **에러가 하나뿐인 것에 주의** — `port` 안의 `?` 는 **추가 에러를 내지 않는다.**
  거부된 `impl` 을 rustc 가 **그래도 등록해 두고** 타입 검사를 통과시키기 때문이다.
  **「에러 1건」이 「문제 1곳」이라는 뜻이 아니다.**
- **처방은 (1)의 `= note:` 셋째 줄 그대로** — 내 타입을 하나 만든다.

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

- **newtype 오류 타입 하나**로 풀렸다. `PortError(ParseIntError)` 는 내 타입이므로
  `impl From<ParseIntError> for PortError` 가 통과하고, **`?` 가 그 위에서 돈다.**
- ★ 이것이 [**24번 주제**](../24-error-type-design/)가 「오류 타입을 왜 직접 만드나」라고 했던 이유 중 하나다 —
  **편의가 아니라 고아 규칙이 강제하는 구조**다.

### (7) 껍데기를 씌우면 뚫리나 — `#[fundamental]`

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

- ★★ **안 뚫린다.** `&Vec<String>` 도 여전히 남의 타입이다.
- ★★★ **그런데 제목이 (1)과 다르다** — 이번에는
  `` only traits defined in the current crate can be implemented for arbitrary types `` 다(`for types defined outside of the crate` 가 아니다).
  `&T` 가 **`#[fundamental]`** 이라 자기 타입이 「그냥 남의 타입」으로 분류되지 않아 **판정 경로가 갈린 것**이다.
  ★ **같은 규칙인데 제목이 둘**이라는 것을 알아 두면 에러를 찾을 때 헷갈리지 않는다.
- ★ **`#[fundamental]` 이 실제로 무엇을 하는지는 속이 내 타입일 때 드러난다.**

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

- ★★ **`impl Display for Box<Wrapper>` 가 통과한다.** `Box` 가 `#[fundamental]` 이라
  **속(`Wrapper`)이 내 타입이면 `Box<Wrapper>` 도 내 타입으로 센다.**
- ★ `&Vec<String>` 이 막히고 `Box<Wrapper>` 가 통과하는 것 — **껍데기가 아니라 속이 판정한다**는 뜻이다.
- ★ `#[fundamental]` 은 **std 만 붙일 수 있는 불안정 어트리뷰트**다. 내 타입에는 못 붙인다.
  이 주제에서는 **이름과 결과까지만** 안다.

## 문법 — 형태와 규칙

```text
   판정하는 순서 (내 크레이트 안에서 impl 을 쓸 때)

   impl<파라미터들> 트레이트<T1, …, Tn> for T0
        │
        ├─ 트레이트가 내 크레이트 것인가?  ──▶ 예: 통과
        │
        └─ 아니오
             └─ T0, T1, … Tn 을 왼쪽부터 보며 내 타입이 나오나?
                  ├─ 나온다(그 앞에 uncovered 타입 파라미터가 없다) ──▶ 통과
                  └─ 안 나온다 ──▶ E0117

   #[fundamental] (&T · &mut T · Box<T> · Pin<T>)
        속이 내 타입이면 껍데기째 「내 타입」으로 센다

   newtype 의 형태

   struct Wrapper(Vec<String>);                       ← 튜플 구조체 한 줄
   impl Display for Wrapper { … }                     ← 이제 무엇이든 붙는다
   impl Deref for Wrapper { type Target = Vec<String>; … }   ← 대가를 되사는 선택지
```

**규칙 불릿.**

- ★★★ **트레이트와 `for` 뒤 타입 중 적어도 하나가 내 크레이트 것**이라야 한다.
- ★ **트레이트의 인자 자리에 내 타입이 있어도 된다** — `impl From<Money> for String` 이 통과하는 이유((2)②).
- **내가 만든 트레이트는 남의 타입 아무 데나 붙는다**((2)③).
- **newtype 은 런타임 비용이 없다** — 필드 하나짜리 구조체는 그 필드와 같은 크기다((3)).
- ★ **`Deref` 는 메서드와 타입은 흘리고 트레이트 구현은 안 흘린다**((5)).
- **`#[fundamental]` 은 std 전용**이다. `&T`·`Box<T>` 가 대표다((7)).

### 금지 사례 — 던져서 받은 넷

| 던진 것 | 받은 것 |
|---|---|
| `impl Display for Vec<String>` | **E0117** `` … for types defined outside of the crate `` |
| `impl From<ParseIntError> for io::Error` | **E0117** — 밑줄이 **양쪽**을 짚는다 |
| `impl Display for &Vec<String>` | **E0117** — 제목이 `` … for arbitrary types `` 로 **바뀐다** |
| newtype 에 안쪽 메서드 호출 | **E0599** ×2 — `` no method named `len`/`push` `` |

## 어디서 틀리나

### 1. ★★★ 「고아 규칙 때문에 남의 타입은 건드릴 수 없다」

**네 칸 중 막히는 것은 한 칸뿐**이다((2)).
**내가 만든 트레이트**라면 `i64` 든 `Vec<String>` 이든 마음대로 붙는다.
막히는 것은 **「남의 트레이트 × 남의 타입」** 그 한 조합이다.

### 2. ★★ 「`impl From<Money> for String` 은 당연히 막히겠지」

**통과한다**((2)②). `String` 도 `From` 도 남의 것인데,
**트레이트 인자에 내 타입이 있으면** (1)의 `= note:` 가 말하는 판정을 통과한다.
「Self 타입만 본다」고 외우면 이 자리를 놓친다.

### 3. ★★★ 「newtype 은 공짜다」

크기는 공짜인데((3)) **표면이 공짜가 아니다** — 안쪽 메서드를 **전부 잃는다**((4)).
되찾는 길은 둘이다: **위임 메서드를 손으로 쓰거나**, **`Deref` 를 달거나.** 뒤엣것에는 대가가 있다.

### 4. ★★★ 「`Deref` 를 달면 newtype 의 단점이 사라진다」

**사라지는 것은 단점이고, 같이 사라지는 것은 장점이다**((5)).
불변식을 지키려고 감쌌다면 `DerefMut` 은 **그 불변식을 깨는 공개 API** 다.
실측에서 `s.push("가")` 한 줄이 정렬 약속을 깼다.

### 5. ★ 「`Deref` 를 달면 트레이트 구현도 따라온다」

**안 따라온다**((5)). 고아 규칙에 막힌 `Display` 를 `Deref` 로 우회할 수는 **없다** —
newtype 에 **직접 구현해야** 한다.

### 6. ★★ 「에러가 한 건이니 문제도 한 곳이다」

(6)에서 `impl` 이 거부됐는데 **그것을 쓰는 `?` 는 추가 에러를 안 냈다.**
rustc 가 거부된 `impl` 을 **그래도 등록해 두기** 때문이다. **고치고 다시 던져야** 남은 문제가 보인다.

### 7. 진단의 제안을 전부 믿는다

(4)의 `` candidate #1: `ExactSizeIterator` `` 는 **아무 관계 없는 제안**이다.
진단은 이름이 같은 후보를 훑어 준 것뿐이다 — **`help:` 의 `w.0.len()` 쪽이 진짜 답**이다.

## 구현 세부사항 대 언어 보장

| 항목 | 무엇인가 | 근거 |
|---|---|---|
| 고아 규칙 자체 | ★ **언어 보장** — Reference 의 orphan rules 절 | (1)의 실측 |
| 인자 자리에 내 타입이 있으면 통과하는 것 | ★ **언어 보장**(covered type 규칙) | (2)의 실측 |
| `&T`·`Box<T>` 가 `#[fundamental]` 인 것 | ★ **std 가 붙인 표시** — 내 타입에는 못 붙인다 | (7)의 실측 |
| `Deref` 가 **메서드만** 흘리고 트레이트는 안 흘리는 것 | ★ **언어 보장** | (5)의 실측 |
| newtype 이 **크기가 같은 것** | ★ **구현 세부** — 기본 표현의 배치는 보장되지 않는다 | (3)의 실측(둘 다 24) |
| E0117 의 **제목이 둘**인 것 | ★ **구현 세부** — 판정 경로에 따라 문구가 갈린다 | (1)·(7)의 실측 |
| 거부된 `impl` 을 **그래도 등록**해 뒤 에러를 줄이는 것 | ★ **구현 세부**(에러 복구 전략) | (6)의 실측 |
| `` candidate #1: `ExactSizeIterator` `` 같은 제안 | ★ **구현 세부** | (4)의 실측 |
| `invalid digit found in string` | ★ **std 구현 세부** | (6)의 실측 |

## 언제 쓰고 언제 안 쓰나

- **내 트레이트를 만든다** — 남의 타입들에 공통 능력을 붙이고 싶고, std 트레이트일 필요가 없을 때((2)③).
- **newtype 을 쓴다** — std 트레이트(`Display`·`From`·`Iterator`)를 남의 타입에 붙여야 할 때((3)).
- ★ **newtype 을 쓴다(두 번째 이유)** — **불변식**을 지키고 싶을 때. 이때는 표면을 좁히는 것이 **목적**이다.
- **`Deref` 를 단다** — newtype 이 **스마트 포인터**일 때(값을 감싸 들고 다니는 것이 전부일 때).
- ★ **`Deref` 를 안 단다** — 불변식을 지키는 newtype. 대신 **필요한 메서드만 위임**해 쓴다.
- ★ **`DerefMut` 만 뺀다** — 읽기는 편하게 열고 쓰기는 정문으로만 받고 싶을 때의 절충((5)).

## 핵심 문장

- ★★★ **E0117 전문이 규칙 그 자체다** — 제목이 규칙, `= note:` 첫 줄이 판정, 셋째 줄이 처방이다.
- ★★ **막히는 것은 「남의 트레이트 × 남의 타입」 한 칸뿐**이다. 인자에 내 타입이 있으면 그것도 통과한다.
- ★★ **newtype 은 크기가 공짜고 표면이 비싸다** — 안쪽 메서드를 전부 잃는다.
- ★★★ **`Deref` 로 되찾으면 불변식이 같이 샌다.** 정문이 하나가 아니게 된다.
- ★ **`?` 를 위한 `From` 이 이 규칙을 처음 만나는 자리**다 — 그래서 오류 타입을 직접 만들게 된다.

## 관련 자료

- [**25번 주제** — 트레이트 정의·구현·기본 메서드·연관 타입](../25-traits-definition-impl-default-methods-and-associated-types/) —
  ★ **경계**: 「**무엇을** 구현하나」는 거기, 여기는 「**누가 구현할 수 있나**」다.
- [**22번 주제** — `Result` 와 `?`·`From`](../22-result-question-mark-and-from/) —
  ★ **경계**: `?` 가 `From` 을 부르는 **규칙**은 거기, 여기는 **그 `From` 을 못 쓰게 되는 자리**다((6)).
- [**24번 주제** — 오류 타입 설계](../24-error-type-design/) —
  오류 타입을 직접 만드는 이유 중 하나가 **이 규칙**이다((6)).
- [**14번 주제** — `String` 대 `&str`](../14-string-vs-str/) —
  ★ **경계**: **역참조 강제**의 정본이 거기다. 여기서는 (5)에서 **그것이 newtype 에 무엇을 하는지**만 봤다.
- [**27번 주제** — `derive` 매크로](../27-derive-macros-debug-clone-partialeq-default-hash/) —
  `derive` 는 **내 타입에 붙이는 것**이라 고아 규칙에 안 걸린다. 걸리는 것은 **손으로 쓰는 `impl`** 쪽이다.
- 목록의 **29번 주제** — `From`/`Into`/`TryFrom`/`AsRef`/`Borrow`. **어느 방향으로 구현하나**의 정본이다.
- 목록의 **30번 주제** — 연산자 오버로딩과 `Deref`. ★ **`Deref` 남용의 정본**이 거기다.
- 목록의 **43번 주제** — `Deref` 강제와 스마트 포인터 감각. (5)의 절충안이 거기서 깊어진다.
- 목록의 **46번 주제** — 크레이트와 워크스페이스. 「크레이트 경계」가 무엇인지의 정본이다.
- Kotlin 의 확장 함수 — [`kotlin/syntax/13-extension-functions-and-properties/`](../../../kotlin/syntax/13-extension-functions-and-properties/).
  ★ **대비**: 남의 타입에 함수를 붙이는 목적이 겹치는데, **확장 함수는 정적 디스패치라 충돌이 안 난다**
  (가져온 쪽에서만 보인다). 그래서 Kotlin 에는 **고아 규칙이 필요 없다** — 대신 **다형성도 없다**.
- C# 의 확장 메서드 — C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **30번**. 같은 구조다.
- Go 의 인터페이스 — Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **20번**.
  ★ **대비**: Go 는 **구현을 선언하지 않으므로** 「누가 구현했나」라는 물음 자체가 없다.
  대신 **남의 타입에 메서드를 못 붙인다**(같은 패키지가 아니면) — 막는 자리가 다를 뿐 **같은 문제를 다르게 푼 것**이다.
- Java 의 인터페이스 — [`java/syntax/11-interfaces-default-methods/`](../../../java/syntax/11-interfaces-default-methods/).
  ★ **대비**: Java 는 **클래스 선언에 `implements` 를 적어야** 하므로 남이 나중에 붙일 수 없다 —
  **고아 문제가 원리상 안 생긴다.** 그 대가로 **어댑터 클래스를 만들게 되는데, 그것이 곧 newtype 이다.**

## 용어 풀이

- **고아 규칙(orphan rule)** — 트레이트도 타입도 남의 것이면 그 구현을 금지하는 규칙.
- **크레이트(crate)** — 컴파일 단위. 「내 것 / 남의 것」의 경계가 여기다.
- **newtype** — 남의 타입을 필드 하나짜리 구조체로 감싼 것. 감싸는 순간 내 타입이 된다.
- **`Deref` / `DerefMut`** — `*x` 와 메서드 찾기를 안쪽 타입으로 넘기는 트레이트. 뒤엣것은 가변 쪽이다.
- **역참조 강제(deref coercion)** — `&Wrapper` 가 `&Vec<String>` 자리에 자동으로 들어가는 것.
- **`#[fundamental]`** — 속이 내 타입이면 껍데기도 내 타입으로 세게 하는 std 전용 표시. `&T`·`Box<T>`.
- **불변식(invariant)** — 타입이 늘 지키겠다고 약속한 성질. 예: 「안의 `Vec` 은 항상 정렬돼 있다」.
- **위임 메서드(delegating method)** — newtype 이 안쪽 메서드를 한 줄씩 다시 열어 주는 것.

## 더 들어가면

- **포괄 구현(blanket impl)** — `impl<T: Display> MyTrait for T`. 내 트레이트라면 된다.
  단 **남이 같은 타입에 직접 구현하면 충돌**하므로 공개 트레이트에서는 신중해야 한다.
- **`#[non_exhaustive]` 와 하위 호환** — 고아 규칙과 함께 「**누가 나중에 무엇을 더할 수 있나**」를 정하는 장치들이다.
- **`Borrow`/`AsRef` 로 위임하기** — `Deref` 대신 쓰는 더 좁은 길. 어느 쪽을 열지 **고를 수 있다**(목록의 **29번 주제**).
- **`derive_more` 같은 크레이트** — 위임 메서드를 매크로로 만들어 준다. ★ **이 환경에서는 못 쓴다**(외부 크레이트 금지).
- **RFC 2451(re-rebalancing coherence)** — 지금의 covered type 규칙이 들어온 제안. (2)②가 통과하는 근거다.
