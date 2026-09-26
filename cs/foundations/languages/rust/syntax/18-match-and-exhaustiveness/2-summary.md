# rust/syntax/18 — `match` 와 완전성 검사 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [The Rust Reference — `match` expressions](https://doc.rust-lang.org/reference/expressions/match-expr.html) ·
> [Reference — Patterns](https://doc.rust-lang.org/reference/patterns.html) ·
> [Reference — Attributes: `non_exhaustive`](https://doc.rust-lang.org/reference/attributes/type_system.html) ·
> [`std::matches!`](https://doc.rust-lang.org/std/macro.matches.html).
> ★ `rustc --explain E0004` / `E0308` / `E0170` / `E0382` 는 **확인용으로만 열었고 본문에 옮기지 않았다.**
> **실행 검증** — 이 문서의 모든 출력·에러·경고는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 받은 것이다. **손으로 옮겨 적은 출력은 한 줄도 없다.**\
> ★ 크레이트 둘이 필요한 실험((6))만 명령이 셋이다 — 배너에 전부 적혀 있다.\
> ★★ **`rustc ex.rs` 만 쓰면 에디션 2015 다.** 이 갈래는 `--edition 2021` 을 반드시 붙인다.
> **버전** — `match`·완전성 검사는 1.0.0부터다. **`#[non_exhaustive]`** 는 **1.40.0**부터,\
> **`matches!`** 는 **1.42.0**부터다. 배타적 범위 패턴 `a..b` 는 **1.80.0**부터다(이 문서는 `..=` 만 쓴다).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | 패닉 첫 줄 `thread 'main' (…)` 괄호 안의 OS 스레드 id | 실행마다 커널이 주는 번호다 |
| **흔들린다** | `0x…` 주소 | 실행마다 다르다 |
| **흔들린다** | 크레이트 둘짜리 실험에서 `lib.rs` 의 **절대 경로** | 머신마다 다르다 — 그래서 `--remap-path-prefix` 로 `./lib.rs` 로 고정했다 |
| 안 흔들린다 | `파일:줄:칸` · 에러 번호 · 제목 · `= note:` · `help:` 본문 | 같은 rustc 판에서 고정이다 |
| 안 흔들린다 | **에러 개수**(이 주제의 핵심 수치) | 소스가 같으면 같다 |
| 안 흔들린다 | 종료 코드(`0` · 컴파일 실패 `1`) | 고정이다 |

## 한눈에 — 쉽게 말하면

**`match` 는 「빠짐없이 다 적었나」를 컴파일러가 세어 주는 분기다.**

다른 언어의 `switch` 는 안 적은 경우를 **런타임에 조용히 지나간다**. Rust 는 **컴파일을 거부한다.**
그래서 `match` 는 분기 문법이 아니라 **점검표**에 가깝다.

| 비유 | 실체 |
|---|---|
| **체크리스트** — 칸을 다 채워야 제출된다 | **완전성 검사**. 빠지면 E0004 |
| 검사관이 **빠진 칸 이름을 대 준다** | ``patterns `X` and `Y` not covered`` |
| **「그 밖 전부」 칸에 미리 체크해 둔 도장** | **`_` 팔**. 편한데, **칸이 늘어도 아무 말을 안 한다** |
| 서류가 **값을 낸다** — 접수증이 나온다 | **`match` 는 식**이다. 모든 팔의 타입이 같아야 한다 |
| 칸을 열어 **내용물을 꺼내 가면** 원본이 빈다 | 팔에서 이름으로 묶으면 **이동**한다 |
| 남의 회사 양식에 「**칸이 더 생길 수 있음**」이라고 적힌 것 | **`#[non_exhaustive]`** — 남의 크레이트에서만 `_` 를 강제한다 |

- ★★ **이 주제의 값은 「변형을 늘렸을 때 컴파일러가 어디를 깨뜨리나」** 하나다. 그것을 세는 실험이 (3)이다.
- ★★ **`_` 는 편의가 아니라 안전망을 끄는 스위치**다. 같은 코드에서 깨지는 자리가 **네 곳에서 0곳**이 된다.
- ★ **`match` 가 식**이라는 사실이 「팔 타입이 다르다」는 에러를 만든다((1)).

```text
   완전성 검사가 세는 것 — 「값의 공간을 다 덮었나」

   enum Event { Click, Key, Scroll, Drag }
                  │      │      │      │
   match e {      ▼      ▼      ▼      ▼
       Event::Click => …  ✔
       Event::Key   => …     ✔
       Event::Scroll=> …        ✔
   }                              ✘ ← 여기가 비었다
                                  │
                                  └─ error[E0004]: non-exhaustive patterns:
                                       `Event::Drag` not covered

   `_` 를 넣으면 공간 전체가 한 번에 덮인다 — 늘어난 칸까지 「미리」

   match e {
       Event::Click => …  ✔
       Event::Key   => …     ✔
       _            => …  ▓▓▓▓▓▓▓▓▓▓▓▓  ← Scroll 도 Drag 도, 앞으로 생길 것도
   }
```

> **완전성 검사(exhaustiveness checking)** — `match` 의 팔들이 **그 타입의 모든 값**을 덮는지\
> 컴파일러가 확인하는 것. 안 덮이면 **E0004** 로 거부한다.

> **팔(arm)** — `패턴 => 식` 한 줄. 패턴·선택적 가드·몸통으로 이루어진다.

> **와일드카드 `_`** — 「무엇이든」 잡는 패턴. **이름을 묶지 않는다**(`_x` 는 묶는다).

> **`#[non_exhaustive]`** — 「이 타입에 변형/필드가 더 늘 수 있다」고 선언하는 표시.\
> **다른 크레이트**에서 `match` 할 때 `_` 팔을 강제한다. **같은 크레이트에서는 아무 일도 안 한다.**

## 이 주제가 답하려는 질문

1. **컴파일러가 무엇을 세나** — 완전성 검사는 어디까지 계산하고, 어디서 포기하나.
2. **변형을 하나 늘리면 어디가 깨지나** — 그리고 `_` 가 그것을 **몇 곳으로** 줄이나.
3. **남의 타입은 어떻게 다루나** — `#[non_exhaustive]` 가 크레이트 경계에서 무엇을 바꾸나.

★ [**17번 주제**](../17-enums-and-data-carrying-variants/)가 「값을 **담는**」 쪽이었다면 여기는 「그것을 **꺼내는**」 쪽이다.
완전성 검사가 성립하는 이유 자체가 **열거형이 닫힌 집합**이라는 17번의 사실에 있다.

## 동작 방식

### (0) 이 주제가 쓰는 네 창

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| **일부러 던져서 받는 E0004** | 무엇이 안 덮였는지 — 컴파일러가 **이름으로 댄다** | [**11번 주제**](../11-borrow-checker-rejections/)의 「에러도 출력이다」 |
| ★★ **변형을 하나 늘리고 에러 개수를 세기** | `_` 가 안전망을 **얼마나** 없애나 — 4 대 0 | ★ 이 주제의 고유 창 |
| **크레이트를 둘로 갈라 컴파일하기** | `#[non_exhaustive]` 가 **경계에서만** 하는 일 | ★ 이 주제의 고유 창 |
| **`help:` 가 주는 고친 코드 읽기** | 컴파일러가 **빠진 범위를 직접 계산**한다 — `(true, Some(1_u8..=u8::MAX))` | ★ 이 주제의 고유 창 |

★ 두 번째 창이 본체다. 「`_` 를 쓰지 마라」는 조언은 흔하지만 **숫자로 보여 주는 것**은 드물다.
같은 소스에 변형 한 줄을 더하고 **에러가 몇 곳에서 나는지 세면** 그 조언이 수치가 된다((3)).

### (1) `match` 는 식이다

**언제 쓰나** — 분기의 결과를 **값으로 받고 싶을 때**. Rust 에서는 그것이 기본이다.

```text
===== 소스: ex.rs =====
// ex.rs
// match 는 식이다 — 값을 내고, 모든 팔의 타입이 같아야 한다
#[derive(Debug)]
enum Coin { Penny, Nickel, Dime, Quarter }

fn main() {
    for c in [Coin::Penny, Coin::Nickel, Coin::Dime, Coin::Quarter] {
        // ① 값으로 받는다
        let v = match c {
            Coin::Penny => 1,
            Coin::Nickel => 5,
            Coin::Dime => 10,
            Coin::Quarter => 25,
        };
        // ② 식이므로 인자 자리에 그대로 들어간다
        // ③ 팔 하나가 블록이어도 「마지막 식」이 그 팔의 값이다
        let s = match v {
            25 => { let q = 100 / v; format!("{}개면 1달러", q) }
            _ => String::from("모자람"),
        };
        println!("{} {} {}", v, match v { 25 => "쿼터", _ => "그 밖" }, s);
    }
    // ④ 값이 필요 없으면 타입이 () 다 — 그때는 문처럼 보인다
    let unit: () = match 1 { 1 => println!("하나"), _ => println!("아님") };
    println!("{:?}", unit);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
1 그 밖 모자람
5 그 밖 모자람
10 그 밖 모자람
25 쿼터 4개면 1달러
하나
()
(종료 코드 0)
```

읽는 법.

- `let v = match c { … };` — **값을 낸다.** 세미콜론은 `let` 문의 것이지 `match` 의 것이 아니다.
- 인자 자리에 그대로 들어간다 — `println!("{}", match v { … })`.
- 팔이 **블록**이어도 **마지막 식**이 그 팔의 값이다([**04번 주제**](../04-expressions-and-semicolons/)).
- 값이 필요 없으면 타입이 `()` 다 — 위 출력의 마지막 줄이 `()` 를 찍어 그것을 보인다.

**팔의 타입이 어긋나면 그 사실이 에러로 드러난다.**

```text
===== 소스: ex.rs =====
// ex.rs
// 팔의 타입이 어긋나면 — match 가 식이라는 사실이 에러로 드러난다
enum Coin { Penny, Quarter }

fn main() {
    let c = Coin::Quarter;
    let v = match c {
        Coin::Penny => 1,
        Coin::Quarter => "스물다섯",
    };
    println!("{:?}", v);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0308]: `match` arms have incompatible types
  --> ex.rs:9:26
   |
 7 |       let v = match c {
   |  _____________-
 8 | |         Coin::Penny => 1,
   | |                        - this is found to be of type `{integer}`
 9 | |         Coin::Quarter => "스물다섯",
   | |                          ^^^^^^^^^^ expected integer, found `&str`
10 | |     };
   | |_____- `match` arms have incompatible types

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0308`.
(종료 코드 1)
```

- **E0308** `match arms have incompatible types`. 진단이 **첫 팔의 타입을 먼저 정하고**(`` this is found to be of type `{integer}` ``)
  그 뒤 팔을 그것과 맞춰 본다.
- ★ 세로 막대가 `match` **전체**를 감싸며 「`match` arms have incompatible types」를 가리킨다 —
  **식 하나가 통째로 문제**라는 표시다.

### (2) 완전성 검사 — 컴파일러가 빠진 것을 이름으로 댄다

**언제 쓰나** — 열거형을 `match` 할 때마다 자동으로.

```text
===== 소스: ex.rs =====
// ex.rs
// 완전성 검사 — 변형 하나를 빼면 컴파일러가 「무엇이 빠졌는지」 이름으로 댄다
enum Event { Click, Key, Scroll, Drag }

fn label(e: &Event) -> &'static str {
    match e {
        Event::Click => "클릭",
        Event::Key => "키",
    }
}

fn main() {
    println!("{}", label(&Event::Click));
    println!("{}", label(&Event::Drag));
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0004]: non-exhaustive patterns: `&Event::Scroll` and `&Event::Drag` not covered
 --> ex.rs:6:11
  |
6 |     match e {
  |           ^ patterns `&Event::Scroll` and `&Event::Drag` not covered
  |
note: `Event` defined here
 --> ex.rs:3:6
  |
3 | enum Event { Click, Key, Scroll, Drag }
  |      ^^^^^               ------  ---- not covered
  |                          |
  |                          not covered
  = note: the matched value is of type `&Event`
help: ensure that all possible cases are being handled by adding a match arm with a wildcard pattern, a match arm with multiple or-patterns as shown, or multiple match arms
  |
8 ~         Event::Key => "키",
9 ~         &Event::Scroll | &Event::Drag => todo!(),
  |

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0004`.
(종료 코드 1)
```

읽는 법.

- **E0004** ``non-exhaustive patterns: `&Event::Scroll` and `&Event::Drag` not covered``.
  ★★ **빠진 것을 이름으로 전부 댄다.** 둘이면 둘 다, 넷이면 넷 다.
- `note:` 가 **열거형 선언 자리**를 가리키고, 그 안에서 **안 덮인 변형에만 밑줄**을 긋는다.
- `help:` 는 고친 코드를 준다 — `&Event::Scroll | &Event::Drag => todo!()`.
  ★ or 패턴으로 묶어 주는 것이 19번 주제의 문법이다.
- ★ 패턴에 `&` 가 붙은 것은 `match e` 의 `e` 가 **`&Event`** 이기 때문이다 — 매치 인체공학(19번 (5)).

### (3) ★★ 변형을 하나 늘렸을 때 깨지는 자리 전수

**언제 쓰나** — 「`_` 를 써도 되나」를 판단할 때. **이 실험이 답을 수치로 준다.**

**① `_` 팔이 하나도 없는 판 — 변형 셋.** 통과한다.

```text
===== 소스: ex.rs =====
// ex.rs
// 변형 추가 실험 — 전. `_` 팔이 하나도 없는 판. 지금은 통과한다
#[derive(Debug, Clone, Copy)]
enum Event { Click, Key, Scroll }

fn label(e: Event) -> &'static str {
    match e { Event::Click => "클릭", Event::Key => "키", Event::Scroll => "스크롤" }
}

fn code(e: Event) -> u8 {
    match e { Event::Click => 1, Event::Key => 2, Event::Scroll => 3 }
}

fn needs_focus(e: Event) -> bool {
    match e { Event::Key => true, Event::Click | Event::Scroll => false }
}

fn main() {
    let all = [Event::Click, Event::Key, Event::Scroll];
    for e in all {
        let kind = match e {
            Event::Click => "포인터",
            Event::Key => "키보드",
            Event::Scroll => "포인터",
        };
        println!("{:?} {} {} {} {}", e, label(e), code(e), needs_focus(e), kind);
    }
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
Click 클릭 1 false 포인터
Key 키 2 true 키보드
Scroll 스크롤 3 false 포인터
(종료 코드 0)
```

**② 같은 파일에 변형 `Drag` 한 줄만 더했다.** `match` 는 한 글자도 안 고쳤다.

```text
===== 소스: ex.rs =====
// ex.rs
// 변형 추가 실험 — 후. enum 에 Drag 한 줄만 더했다. match 는 한 글자도 안 고쳤다
#[derive(Debug, Clone, Copy)]
enum Event { Click, Key, Scroll, Drag }

fn label(e: Event) -> &'static str {
    match e { Event::Click => "클릭", Event::Key => "키", Event::Scroll => "스크롤" }
}

fn code(e: Event) -> u8 {
    match e { Event::Click => 1, Event::Key => 2, Event::Scroll => 3 }
}

fn needs_focus(e: Event) -> bool {
    match e { Event::Key => true, Event::Click | Event::Scroll => false }
}

fn main() {
    let all = [Event::Click, Event::Key, Event::Scroll];
    for e in all {
        let kind = match e {
            Event::Click => "포인터",
            Event::Key => "키보드",
            Event::Scroll => "포인터",
        };
        println!("{:?} {} {} {} {}", e, label(e), code(e), needs_focus(e), kind);
    }
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0004]: non-exhaustive patterns: `Event::Drag` not covered
 --> ex.rs:7:11
  |
7 |     match e { Event::Click => "클릭", Event::Key => "키", Event::Scroll => "스크롤" }
  |           ^ pattern `Event::Drag` not covered
  |
note: `Event` defined here
 --> ex.rs:4:6
  |
4 | enum Event { Click, Key, Scroll, Drag }
  |      ^^^^^                       ---- not covered
  = note: the matched value is of type `Event`
help: ensure that all possible cases are being handled by adding a match arm with a wildcard pattern or an explicit pattern as shown
  |
7 |     match e { Event::Click => "클릭", Event::Key => "키", Event::Scroll => "스크롤", Event::Drag => todo!() }
  |                                                                                    ++++++++++++++++++++++++

error[E0004]: non-exhaustive patterns: `Event::Drag` not covered
  --> ex.rs:11:11
   |
11 |     match e { Event::Click => 1, Event::Key => 2, Event::Scroll => 3 }
   |           ^ pattern `Event::Drag` not covered
   |
note: `Event` defined here
  --> ex.rs:4:6
   |
 4 | enum Event { Click, Key, Scroll, Drag }
   |      ^^^^^                       ---- not covered
   = note: the matched value is of type `Event`
help: ensure that all possible cases are being handled by adding a match arm with a wildcard pattern or an explicit pattern as shown
   |
11 |     match e { Event::Click => 1, Event::Key => 2, Event::Scroll => 3, Event::Drag => todo!() }
   |                                                                     ++++++++++++++++++++++++

error[E0004]: non-exhaustive patterns: `Event::Drag` not covered
  --> ex.rs:15:11
   |
15 |     match e { Event::Key => true, Event::Click | Event::Scroll => false }
   |           ^ pattern `Event::Drag` not covered
   |
note: `Event` defined here
  --> ex.rs:4:6
   |
 4 | enum Event { Click, Key, Scroll, Drag }
   |      ^^^^^                       ---- not covered
   = note: the matched value is of type `Event`
help: ensure that all possible cases are being handled by adding a match arm with a wildcard pattern or an explicit pattern as shown
   |
15 |     match e { Event::Key => true, Event::Click | Event::Scroll => false, Event::Drag => todo!() }
   |                                                                        ++++++++++++++++++++++++

error[E0004]: non-exhaustive patterns: `Event::Drag` not covered
  --> ex.rs:21:26
   |
21 |         let kind = match e {
   |                          ^ pattern `Event::Drag` not covered
   |
note: `Event` defined here
  --> ex.rs:4:6
   |
 4 | enum Event { Click, Key, Scroll, Drag }
   |      ^^^^^                       ---- not covered
   = note: the matched value is of type `Event`
help: ensure that all possible cases are being handled by adding a match arm with a wildcard pattern or an explicit pattern as shown
   |
24 ~             Event::Scroll => "포인터",
25 ~             Event::Drag => todo!(),
   |

error: aborting due to 4 previous errors

For more information about this error, try `rustc --explain E0004`.
(종료 코드 1)
```

★★ **에러가 네 개 난다.** `label`(7줄) · `code`(11줄) · `needs_focus`(15줄) · `main` 안의 `match`(21줄) —
**`match` 가 있는 자리 전부**다. 각각 `help:` 로 그 자리에 맞는 고친 코드를 준다.

**③ 같은 코드에서 마지막 팔만 `_` 로 바꾼 판 — 변형 셋.** 역시 통과한다.

```text
===== 소스: ex.rs =====
// ex.rs
// 변형 추가 실험 — `_` 팔을 넣은 판. 네 자리 전부 마지막 팔을 `_` 로 바꿨다
#[derive(Debug, Clone, Copy)]
enum Event { Click, Key, Scroll }

fn label(e: Event) -> &'static str {
    match e { Event::Click => "클릭", Event::Key => "키", _ => "스크롤" }
}

fn code(e: Event) -> u8 {
    match e { Event::Click => 1, Event::Key => 2, _ => 3 }
}

fn needs_focus(e: Event) -> bool {
    match e { Event::Key => true, _ => false }
}

fn main() {
    let all = [Event::Click, Event::Key, Event::Scroll];
    for e in all {
        let kind = match e {
            Event::Click => "포인터",
            Event::Key => "키보드",
            _ => "포인터",
        };
        println!("{:?} {} {} {} {}", e, label(e), code(e), needs_focus(e), kind);
    }
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
Click 클릭 1 false 포인터
Key 키 2 true 키보드
Scroll 스크롤 3 false 포인터
(종료 코드 0)
```

**④ 그 `_` 판에 `Drag` 를 더했다.** `match` 는 역시 한 글자도 안 고쳤다.

```text
===== 소스: ex.rs =====
// ex.rs
// 변형 추가 실험 — `_` 판에 Drag 를 더했다. 역시 match 는 한 글자도 안 고쳤다
#[derive(Debug, Clone, Copy)]
enum Event { Click, Key, Scroll, Drag }

fn label(e: Event) -> &'static str {
    match e { Event::Click => "클릭", Event::Key => "키", _ => "스크롤" }
}

fn code(e: Event) -> u8 {
    match e { Event::Click => 1, Event::Key => 2, _ => 3 }
}

fn needs_focus(e: Event) -> bool {
    match e { Event::Key => true, _ => false }
}

fn main() {
    let all = [Event::Click, Event::Key, Event::Scroll];
    for e in all {
        let kind = match e {
            Event::Click => "포인터",
            Event::Key => "키보드",
            _ => "포인터",
        };
        println!("{:?} {} {} {} {}", e, label(e), code(e), needs_focus(e), kind);
    }
}
===== rustc --edition 2021 ex.rs -o ex =====
warning: variant `Drag` is never constructed
 --> ex.rs:4:34
  |
4 | enum Event { Click, Key, Scroll, Drag }
  |      ----- variant in this enum  ^^^^
  |
  = note: `Event` has derived impls for the traits `Clone` and `Debug`, but these are intentionally ignored during dead code analysis
  = note: `#[warn(dead_code)]` (part of `#[warn(unused)]`) on by default

warning: 1 warning emitted

===== ./ex =====
Click 클릭 1 false 포인터
Key 키 2 true 키보드
Scroll 스크롤 3 false 포인터
(종료 코드 0)
```

★★ **에러가 0개다.** 컴파일이 통과하고 프로그램이 돈다 —
`Drag` 는 **아무도 처리하지 않은 채 `_` 팔로 흘러간다.**
유일한 불평은 ``warning: variant `Drag` is never constructed`` 인데
**이건 「안 쓰였다」는 말이지 「안 처리했다」는 말이 아니다.** 어딘가에서 한 번만 만들면 그 경고도 사라진다.

**격자로 세면 이렇다.**

| 판 | `match` 자리 | 변형 추가 전 | 변형 추가 후 **에러** | 변형 추가 후 **경고** |
|---|---|---|---|---|
| `_` 없음 | 4곳 | 통과 | **4** (E0004 × 4) | 0 |
| `_` 있음 | 4곳 | 통과 | **0** | 1 (never constructed — 처리 누락과 무관) |

- ★ 그래서 `_` 는 「짧게 쓰는 법」이 아니라 「**안전망을 끄는 선택**」이다.
- ★ 쓸 자리는 있다 — **그 타입이 내 손 밖에 있을 때**((6))와 **값의 공간이 열거형이 아닐 때**(정수·문자).
- ★ 내 열거형에는 `_` 대신 **남은 변형을 or 패턴으로 나열**한다. 그러면 늘었을 때 다시 깨진다.

### (4) 완전성은 열거형만의 일이 아니다 — 범위·튜플·중첩

**언제 쓰나** — 정수·문자·튜플을 `match` 할 때. **덮으면 `_` 가 필요 없다.**

```text
===== 소스: ex.rs =====
// ex.rs
// 범위 패턴의 완전성 — i32 를 전부 덮으면 `_` 없이도 통과한다
fn grade(n: i32) -> &'static str {
    match n {
        i32::MIN..=-1 => "음수",
        0 => "영",
        1..=9 => "한 자리",
        10..=i32::MAX => "두 자리 이상",
    }
}

fn kind(c: char) -> &'static str {
    match c {
        'a'..='z' => "소문자",
        'A'..='Z' => "대문자",
        '0'..='9' => "숫자",
        _ => "그 밖",
    }
}

fn main() {
    for n in [i32::MIN, -1, 0, 7, 10, i32::MAX] { println!("{} {}", n, grade(n)); }
    for c in ['q', 'Q', '7', '가'] { println!("{} {}", c, kind(c)); }
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
-2147483648 음수
-1 음수
0 영
7 한 자리
10 두 자리 이상
2147483647 두 자리 이상
q 소문자
Q 대문자
7 숫자
가 그 밖
(종료 코드 0)
```

읽는 법.

- ★★ **`i32` 전체를 범위로 덮으면 `_` 없이 통과한다.** `i32::MIN..=-1` · `0` · `1..=9` · `10..=i32::MAX` 넷이
  **42억 가지를 빠짐없이** 덮는다. 컴파일러가 그것을 계산한다.
- `char` 는 덮기가 현실적으로 어렵다(유니코드 스칼라 전체) — 그래서 `_` 를 쓴다. **이것이 `_` 의 제자리**다.

**한 칸이라도 비면 「빈 구간」을 숫자로 짚어 준다.**

```text
===== 소스: ex.rs =====
// ex.rs
// 한 칸이라도 비면 컴파일러가 「빈 구간」을 숫자로 짚어 준다
fn grade(n: i32) -> &'static str {
    match n {
        i32::MIN..=-1 => "음수",
        0 => "영",
        1..=9 => "한 자리",
        11..=i32::MAX => "두 자리 이상",
    }
}

fn byte(b: u8) -> &'static str {
    match b {
        0..=127 => "ASCII",
    }
}

fn main() {
    println!("{} {}", grade(10), byte(200));
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0004]: non-exhaustive patterns: `10_i32` not covered
 --> ex.rs:4:11
  |
4 |     match n {
  |           ^ pattern `10_i32` not covered
  |
  = note: the matched value is of type `i32`
help: ensure that all possible cases are being handled by adding a match arm with a wildcard pattern or an explicit pattern as shown
  |
8 ~         11..=i32::MAX => "두 자리 이상",
9 ~         10_i32 => todo!(),
  |

error[E0004]: non-exhaustive patterns: `128_u8..=u8::MAX` not covered
  --> ex.rs:13:11
   |
13 |     match b {
   |           ^ pattern `128_u8..=u8::MAX` not covered
   |
   = note: the matched value is of type `u8`
help: ensure that all possible cases are being handled by adding a match arm with a wildcard pattern or an explicit pattern as shown
   |
14 ~         0..=127 => "ASCII",
15 ~         128_u8..=u8::MAX => todo!(),
   |

error: aborting due to 2 previous errors

For more information about this error, try `rustc --explain E0004`.
(종료 코드 1)
```

- `1..=9` 와 `11..=i32::MAX` 사이의 **정확히 `10`** 을 짚는다 — ``pattern `10_i32` not covered``.
- `u8` 쪽은 **`128_u8..=u8::MAX`** 를 짚는다. ★ 컴파일러가 **구간을 직접 계산해서** 적어 준다.

```text
   (bool, Option<u8>) 의 값 공간을 격자로 펴면 — 「무엇이 빠졌나」

                Some(0)        Some(1..=255)        None
            ┌─────────────┬──────────────────┬─────────────┐
    true    │ (true,S(0)) │   ★ 여기가 비었다 │ (true,None) │
            ├─────────────┴──────────────────┼─────────────┤
    false   │        (false, Some(_))        │ (false,None)│
            └────────────────────────────────┴─────────────┘

   컴파일러가 그 빈 칸을 이렇게 적어 준다
       pattern `(true, Some(1_u8..=u8::MAX))` not covered
   ★ 「Some(_) 에서 이미 덮인 0 을 뺀 나머지」를 구간으로 계산한 것이다.
     사람이 손으로 세던 격자를 컴파일러가 대신 센다.
```

**튜플·중첩도 같은 방식으로 센다.**

```text
===== 소스: ex.rs =====
// ex.rs
// 완전성은 열거형만의 일이 아니다 — 튜플·중첩도 격자로 센다
fn cell(a: bool, b: Option<u8>) -> &'static str {
    match (a, b) {
        (true, Some(0)) => "참·영",
        (true, Some(_)) => "참·수",
        (true, None) => "참·없음",
        (false, Some(_)) => "거짓·수",
        (false, None) => "거짓·없음",
    }
}

fn main() {
    for a in [true, false] {
        for b in [Some(0u8), Some(9u8), None] {
            println!("{:<5} {:<8} {}", a, format!("{:?}", b), cell(a, b));
        }
    }
    // 두 칸짜리 격자는 2 * 3 = 6 갈래지만, 패턴 다섯으로 덮었다
    println!("갈래 {} 팔 {}", 2 * 3, 5);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
true  Some(0)  참·영
true  Some(9)  참·수
true  None     참·없음
false Some(0)  거짓·수
false Some(9)  거짓·수
false None     거짓·없음
갈래 6 팔 5
(종료 코드 0)
```

```text
===== 소스: ex.rs =====
// ex.rs
// 한 칸을 빼면 — 튜플에서도 「빠진 조합」을 그대로 적어 준다
fn cell(a: bool, b: Option<u8>) -> &'static str {
    match (a, b) {
        (true, Some(0)) => "참·영",
        (true, None) => "참·없음",
        (false, Some(_)) => "거짓·수",
        (false, None) => "거짓·없음",
    }
}

fn main() {
    println!("{}", cell(true, Some(9)));
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0004]: non-exhaustive patterns: `(true, Some(1_u8..=u8::MAX))` not covered
 --> ex.rs:4:11
  |
4 |     match (a, b) {
  |           ^^^^^^ pattern `(true, Some(1_u8..=u8::MAX))` not covered
  |
  = note: the matched value is of type `(bool, Option<u8>)`
help: ensure that all possible cases are being handled by adding a match arm with a wildcard pattern or an explicit pattern as shown
  |
8 ~         (false, None) => "거짓·없음",
9 ~         (true, Some(1_u8..=u8::MAX)) => todo!(),
  |

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0004`.
(종료 코드 1)
```

- 위는 `(bool, Option<u8>)` 여섯 갈래를 **팔 다섯**으로 덮었다 — `(true, Some(_))` 하나가 여러 칸을 먹는다.
- 아래는 `(true, Some(9))` 자리를 비웠더니 **`(true, Some(1_u8..=u8::MAX))`** 를 짚는다.
  ★★ **덮인 `Some(0)` 을 빼고 남은 구간**을 계산해 낸 것이다. 사람이 손으로 세던 격자를 컴파일러가 대신 센다.

### (5) 묶인 값의 이동 — 그리고 변수 패턴이라는 함정

**언제 쓰나** — 팔에서 `String`·`Vec` 처럼 `Copy` 가 아닌 값을 이름으로 받을 때.

```text
===== 소스: ex.rs =====
// ex.rs
// 묶인 값의 이동 — 팔에서 값을 「이름으로 받으면」 그 자리에서 옮겨진다
#[derive(Debug)]
enum Msg { Text(String), Num(u32) }

fn main() {
    let m = Msg::Text(String::from("가나다"));
    match m {
        Msg::Text(s) => println!("글 {}", s),
        Msg::Num(n) => println!("수 {}", n),
    }
    println!("{:?}", m);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0382]: borrow of partially moved value: `m`
  --> ex.rs:12:22
   |
 9 |         Msg::Text(s) => println!("글 {}", s),
   |                   - value partially moved here
...
12 |     println!("{:?}", m);
   |                      ^ value borrowed here after partial move
   |
   = note: partial move occurs because value has type `String`, which does not implement the `Copy` trait
   = note: this error originates in the macro `$crate::format_args_nl` which comes from the expansion of the macro `println` (in Nightly builds, run with -Z macro-backtrace for more info)
help: borrow this binding in the pattern to avoid moving the value
   |
 9 |         Msg::Text(ref s) => println!("글 {}", s),
   |                   +++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0382`.
(종료 코드 1)
```

- **E0382** `` borrow of partially moved value: `m` ``. 팔에서 `Msg::Text(s)` 로 **이름을 묶는 순간 이동**한다.
  `_` 로 받거나 참조를 매치하면 안 옮겨진다.
- ★ `help:` 가 **`ref s`** 를 제안한다 — 19번 주제에서 다룰 옛 도구다.

**고치는 법 셋.**

```text
===== 소스: ex.rs =====
// ex.rs
// 고치는 법 셋 — 참조로 매치 / 빌려서 매치 / 안 쓰는 칸은 `..` 로 건너뛰기
#[derive(Debug)]
enum Msg { Text(String), Num(u32) }

fn main() {
    let m = Msg::Text(String::from("가나다"));

    // ① 참조를 매치한다 — s 는 &String 이 된다(19번 주제의 매치 인체공학)
    match &m {
        Msg::Text(s) => println!("① 글 {} (길이 {})", s, s.len()),
        Msg::Num(n) => println!("① 수 {}", n),
    }
    println!("① 뒤 원본 {:?}", m);

    // ② 칸을 아예 안 묶는다 — 이동할 것이 없다
    match m {
        Msg::Text(..) => println!("② 글이다"),
        Msg::Num(..) => println!("② 수다"),
    }
    println!("② 뒤 원본 {:?}", m);

    // ③ Copy 인 칸은 묶어도 이동이 아니다
    let k = Msg::Num(7);
    match k {
        Msg::Num(n) => println!("③ 수 {}", n),
        Msg::Text(_) => println!("③ 글"),
    }
    println!("③ 뒤 원본 {:?}", k);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
① 글 가나다 (길이 9)
① 뒤 원본 Text("가나다")
② 글이다
② 뒤 원본 Text("가나다")
③ 수 7
③ 뒤 원본 Num(7)
(종료 코드 0)
```

- ① **참조를 매치한다**(`match &m`) — `s` 가 `&String` 이 된다. 19번 주제의 매치 인체공학이다.
- ② **칸을 안 묶는다**(`Msg::Text(..)`) — 이동할 것이 없다.
- ③ **`Copy` 인 칸은 묶어도 이동이 아니다** — `Msg::Num(n)` 뒤에도 원본이 산다([**09번 주제**](../09-copy-clone-and-drop/)).

**경로를 빼먹으면 「변형을 짚은 것」이 아니라 「새 변수를 묶은 것」이 된다.**

```text
===== 소스: ex.rs =====
// ex.rs
// 변수 패턴은 「무엇이든」 잡는다 — 경로를 안 쓰면 안전망이 조용히 사라진다
#[derive(Debug)]
enum Event { Click, Key, Scroll }

fn main() {
    let e = Event::Scroll;
    let s = match e {
        Click => "클릭",          // ★ Event:: 를 빼먹었다 — 이건 새 변수다
        Event::Key => "키",
        Event::Scroll => "스크롤",
    };
    println!("{}", s);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0170]: pattern binding `Click` is named the same as one of the variants of the type `Event`
 --> ex.rs:9:9
  |
9 |         Click => "클릭",          // ★ Event:: 를 빼먹었다 — 이건 새 변수다
  |         ^^^^^ help: to match on the variant, qualify the path: `Event::Click`
  |
  = note: `#[deny(bindings_with_variant_name)]` on by default

warning: unreachable pattern
  --> ex.rs:10:9
   |
 9 |         Click => "클릭",          // ★ Event:: 를 빼먹었다 — 이건 새 변수다
   |         ----- matches any value
10 |         Event::Key => "키",
   |         ^^^^^^^^^^ no value can reach this
   |
   = note: `#[warn(unreachable_patterns)]` (part of `#[warn(unused)]`) on by default

warning: unreachable pattern
  --> ex.rs:11:9
   |
 9 |         Click => "클릭",          // ★ Event:: 를 빼먹었다 — 이건 새 변수다
   |         ----- matches any value
10 |         Event::Key => "키",
11 |         Event::Scroll => "스크롤",
   |         ^^^^^^^^^^^^^ no value can reach this

warning: unused variable: `Click`
 --> ex.rs:9:9
  |
9 |         Click => "클릭",          // ★ Event:: 를 빼먹었다 — 이건 새 변수다
  |         ^^^^^
  |
  = note: `#[warn(unused_variables)]` (part of `#[warn(unused)]`) on by default
help: you might have meant to pattern match on the similarly named variant `Click`
  |
9 |         Event::Click => "클릭",          // ★ Event:: 를 빼먹었다 — 이건 새 변수다
  |         +++++++
help: if this is intentional, prefix it with an underscore
  |
9 |         _Click => "클릭",          // ★ Event:: 를 빼먹었다 — 이건 새 변수다
  |         +

warning: variants `Click` and `Key` are never constructed
 --> ex.rs:4:14
  |
4 | enum Event { Click, Key, Scroll }
  |      -----   ^^^^^  ^^^
  |      |
  |      variants in this enum
  |
  = note: `Event` has a derived impl for the trait `Debug`, but this is intentionally ignored during dead code analysis
  = note: `#[warn(dead_code)]` (part of `#[warn(unused)]`) on by default

warning: variable `Click` should have a snake case name
 --> ex.rs:9:9
  |
9 |         Click => "클릭",          // ★ Event:: 를 빼먹었다 — 이건 새 변수다
  |         ^^^^^ help: convert the identifier to snake case (notice the capitalization): `click`
  |
  = note: `#[warn(non_snake_case)]` (part of `#[warn(nonstandard_style)]`) on by default

error: aborting due to 1 previous error; 5 warnings emitted

For more information about this error, try `rustc --explain E0170`.
(종료 코드 1)
```

- ★★ **E0170** — `` pattern binding `Click` is named the same as one of the variants of the type `Event` ``.
  `#[deny(bindings_with_variant_name)]` 이 **기본 deny** 라 **경고가 아니라 에러**다.
- 그 뒤로 경고가 줄줄이 붙는다 — **`unreachable pattern` 둘**(`Click` 이 `matches any value`),
  `unused variable`, `non_snake_case`, `dead_code`. **다섯 경고 + 에러 하나.**
- ★ 이 사고가 무서운 이유는 **`use Event::*;` 로 변형을 열어 두면 E0170 조차 안 난다**는 데 있다 —
  그때는 진짜로 변형을 짚은 것이 되기 때문이다. 그래서 17번 주제가 `use Enum::*` 를 습관으로 쓰지 말라고 했다.

### (6) `#[non_exhaustive]` — 크레이트 경계에서만 일어나는 일

**언제 쓰나** — 내가 **라이브러리**를 만들고, 변형을 나중에 늘려도 남의 코드를 안 깨뜨리고 싶을 때.

**같은 크레이트 안에서는 아무 일도 안 한다.**

```text
===== 소스: ex.rs =====
// ex.rs
// #[non_exhaustive] — 「같은 크레이트 안에서는」 아무 일도 안 한다
#[non_exhaustive]
#[derive(Debug)]
pub enum Level { Low, High }

fn name(l: &Level) -> &'static str {
    match l {                    // `_` 팔이 없는데도 통과한다
        Level::Low => "낮음",
        Level::High => "높음",
    }
}

fn main() {
    println!("{} {}", name(&Level::Low), name(&Level::High));
    println!("{:?}", Level::High);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
낮음 높음
High
(종료 코드 0)
```

- `#[non_exhaustive]` 를 붙였는데 **`_` 팔 없이 통과한다.** 같은 크레이트는 「내 손 안」이라
  변형을 늘리면 **내가 고치면 되기 때문**이다.

**크레이트를 갈라서 같은 코드를 컴파일하면 갈린다.**

```text
===== 소스: lib.rs =====
// lib.rs
// 남의 크레이트가 되는 쪽 — 변형을 나중에 늘릴 여지를 열어 둔다
#[non_exhaustive]
#[derive(Debug)]
pub enum Level { Low, High }

#[derive(Debug)]
pub enum Plain { Low, High }     // 표시 없는 쪽 — 대조용
===== 소스: ex.rs =====
// ex.rs
// 쓰는 쪽 — 같은 파일이 아니라 「다른 크레이트」가 되면 규칙이 갈린다
fn name(l: &upstream::Level) -> &'static str {
    match l {
        upstream::Level::Low => "낮음",
        upstream::Level::High => "높음",
    }
}

fn plain(p: &upstream::Plain) -> &'static str {
    match p {
        upstream::Plain::Low => "낮음",
        upstream::Plain::High => "높음",
    }
}

fn main() {
    println!("{} {}", name(&upstream::Level::Low), plain(&upstream::Plain::High));
}
===== rustc --edition 2021 --remap-path-prefix="$PWD"=. --crate-type=lib --crate-name=upstream lib.rs =====
===== rustc --edition 2021 --extern upstream=libupstream.rlib ex.rs -o ex =====
error[E0004]: non-exhaustive patterns: `&_` not covered
 --> ex.rs:4:11
  |
4 |     match l {
  |           ^ pattern `&_` not covered
  |
note: `Level` defined here
 --> ./lib.rs:5:1
  = note: the matched value is of type `&Level`
  = note: `Level` is marked as non-exhaustive, so a wildcard `_` is necessary to match exhaustively
help: ensure that all possible cases are being handled by adding a match arm with a wildcard pattern or an explicit pattern as shown
  |
6 ~         upstream::Level::High => "높음",
7 ~         &_ => todo!(),
  |

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0004`.
(종료 코드 1)
```

- **E0004** 가 나는데 짚는 것이 **`&_`** 다 — 「변형 하나가 빠졌다」가 아니라 **「그 밖 전부가 빠졌다」**.
- 결정적인 줄은 ``= note: `Level` is marked as non-exhaustive, so a wildcard `_` is necessary to match exhaustively`` 다.
- ★★ **같은 파일에 있는 `Plain`(표시 없는 쪽)은 아무 에러도 안 낸다.** 크레이트가 달라도
  **표시가 없으면 완전성 검사가 그대로 산다.** 갈리는 것은 **크레이트 경계 × 표시** 둘이 겹칠 때뿐이다.

**고친 판.**

```text
===== 소스: lib.rs =====
// lib.rs
// 남의 크레이트가 되는 쪽 — 변형을 나중에 늘릴 여지를 열어 둔다
#[non_exhaustive]
#[derive(Debug)]
pub enum Level { Low, High }

#[derive(Debug)]
pub enum Plain { Low, High }     // 표시 없는 쪽 — 대조용
===== 소스: ex.rs =====
// ex.rs
// 고친 판 — 표시가 붙은 쪽에만 `_` 팔을 넣었다. 안 붙은 쪽은 그대로 둔다
fn name(l: &upstream::Level) -> &'static str {
    match l {
        upstream::Level::Low => "낮음",
        upstream::Level::High => "높음",
        _ => "앞으로 늘어날 것",
    }
}

fn plain(p: &upstream::Plain) -> &'static str {
    match p {
        upstream::Plain::Low => "낮음",
        upstream::Plain::High => "높음",
    }
}

fn main() {
    println!("{} {}", name(&upstream::Level::Low), plain(&upstream::Plain::High));
}
===== rustc --edition 2021 --remap-path-prefix="$PWD"=. --crate-type=lib --crate-name=upstream lib.rs =====
===== rustc --edition 2021 --extern upstream=libupstream.rlib ex.rs -o ex =====
===== ./ex =====
낮음 높음
(종료 코드 0)
```

- 표시가 붙은 쪽에만 `_` 를 넣었다. 안 붙은 쪽은 그대로 두었고 여전히 통과한다.
- ★ 이것이 `_` 를 **써야만 하는** 자리다 — 그 타입이 **내 손 밖**에 있다.

## 문법 — 형태와 규칙

**형태.**

```text
let v = match scrutinee {
    Pattern1 => expr,
    Pattern2 | Pattern3 => expr,          // or 패턴 (19번)
    Pattern4 if cond => expr,             // 가드 (19번)
    x @ 1..=9 => expr,                    // @ 바인딩 (19번)
    _ => expr,                            // 와일드카드
};

matches!(value, Pattern)                  // match 를 bool 한 줄로 (1.42+)
```

**규칙.**

- **팔은 위에서 아래로** 본다. 먼저 맞는 팔이 이긴다 — 그래서 `_` 는 **맨 끝**에 둔다.
- **모든 팔의 타입이 같아야** 한다. 값이 필요 없으면 전부 `()` 다.
- **완전성**은 타입의 값 공간 전체를 기준으로 센다 — 열거형 변형·정수 범위·튜플 조합·슬라이스 길이.
- **가드가 붙은 팔은 덮은 것으로 안 친다**(19번 (2)에서 던져서 확인한다).
- `_` 는 **이름을 묶지 않는다.** `_x` 는 묶되 「안 쓴다」는 표시라 경고가 안 난다.
- `..` 는 **여러 칸을 건너뛴다**(구조체·튜플·슬라이스). `_` 는 **한 칸**이다.

**금지 사례.**

```text
// ① 변형이 빠졌다 — E0004
match e { Event::Click => 1, Event::Key => 2 }

// ② 팔 타입이 다르다 — E0308
match c { Coin::Penny => 1, Coin::Quarter => "스물다섯" }

// ③ 경로 없이 변형 이름을 썼다 — E0170 (deny by default)
match e { Click => "클릭", Event::Key => "키" }

// ④ 팔에서 Copy 아닌 값을 묶고 원본을 또 쓴다 — E0382
match m { Msg::Text(s) => println!("{}", s), _ => {} }
println!("{:?}", m);

// ⑤ 남의 크레이트의 #[non_exhaustive] 타입을 _ 없이 — E0004 (`&_` not covered)
match lvl { upstream::Level::Low => 1, upstream::Level::High => 2 }
```

## 어디서 틀리나

| 자리 | 증상 | 진짜 이유 |
|---|---|---|
| ★★ **습관적으로 `_` 를 붙이기** | 변형을 늘려도 **아무 데서도 안 깨진다** | 완전성 검사를 끈 것이다. 깨지는 자리가 **4곳에서 0곳**이 된다((3)) |
| **`_` 를 맨 위에 두기** | 아래 팔이 전부 `unreachable pattern` | 팔은 위에서 아래로 본다 |
| **경로를 빼먹기** | E0170 + `unreachable pattern` 경고들 | 대문자 이름도 **변수 패턴**이다((5)) |
| **`use Enum::*` 를 쓴 상태에서 오타** | E0170 조차 안 난다 | 그때는 진짜 변형이라 검사가 통과한다 |
| **팔에서 `String` 묶기** | E0382 partial move | 이름을 묶으면 이동한다. `&` 로 매치하거나 `..` 로 건너뛴다 |
| **팔 타입 섞기** | E0308 incompatible types | `match` 는 식이라 값 하나를 내야 한다 |
| **범위를 한 칸 비우기** | E0004 with `10_i32` | 컴파일러가 **빈 구간을 계산**한다 |
| ★ **`#[non_exhaustive]` 를 같은 크레이트에서 시험하기** | 아무 일도 안 일어난다 | **크레이트 경계에서만** 작동한다((6)) |
| ★ **`_` 대신 남은 변형을 나열하지 않기** | 늘었을 때 안 깨진다 | 내 열거형이면 **or 패턴으로 나열**한다 |

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 |
|---|---|
| `match` 는 **식**이고 모든 팔의 타입이 같아야 한다 | **언어 보장** |
| 열거형·정수 범위·튜플·슬라이스에 대한 **완전성 검사** | **언어 보장** |
| 가드가 붙은 팔은 **덮은 것으로 안 친다** | **언어 보장** — 진단이 `match arms with guards don't count towards exhaustivity` 로 말한다 |
| `#[non_exhaustive]` 가 **다른 크레이트에서만** `_` 를 강제한다 | **언어 보장** |
| `bindings_with_variant_name` 이 **deny** 인 것 | ★ **이 rustc 판의 정책이다** — lint 수준은 판마다 바뀔 수 있다 |
| 진단이 **빠진 구간을 `128_u8..=u8::MAX` 처럼 계산해 주는 것** | ★ **이 판의 관찰** — 진단 품질은 보장이 아니다 |
| 에러 **개수**가 `match` 자리 수와 같은 것 | ★ **관찰이되 견고하다** — 자리마다 따로 검사하므로 |
| `help:` 가 주는 고친 코드의 모양 | ★ **이 판의 관찰** |

## 언제 쓰고 언제 안 쓰나

**`match` 를 쓴다.**

- **갈래가 둘 이상이고 전부 다뤄야 할 때.** 특히 **내 열거형**이면 거의 언제나.
- **값을 받아야 할 때** — 분기의 결과를 변수·인자·반환값으로 쓸 때.

**`_` 를 쓴다.**

- **그 타입이 내 손 밖**일 때 — 남의 크레이트, 특히 `#[non_exhaustive]`.
- **값 공간이 열거형이 아닐 때** — `char`·문자열·큰 정수 범위.
- ★ **내 열거형에는 안 쓴다.** 대신 남은 변형을 **or 패턴으로 나열**한다.

**`match` 말고 다른 것을 쓴다.**

- **한 갈래만 궁금하면 `if let`** — 다음 주제([목록의 **20번 주제**](../20-if-let-while-let-let-else-and-let-chains/)).
- **참/거짓만 필요하면 `matches!`** — `matches!(c, Cfg::Port(_))`.
- **`Option`/`Result` 의 흔한 변환이면 조합 메서드** — `map`·`unwrap_or`([목록의 **21번 주제**](../21-option-and-combinators/)).

## 핵심 문장

1. **`match` 는 분기가 아니라 점검표다.** 빠진 칸을 컴파일러가 **이름으로 대 준다**.
2. **`_` 는 짧게 쓰는 법이 아니라 안전망을 끄는 스위치다** — 같은 코드에서 깨지는 자리가 **4 → 0** 이 된다.
3. **완전성은 열거형만의 일이 아니다** — 범위·튜플·슬라이스도 컴파일러가 구간을 계산해 센다.
4. **팔에서 이름을 묶으면 값이 이동한다.** 참조를 매치하거나 `..` 로 건너뛴다.
5. **경로를 빼먹은 대문자 이름은 변형이 아니라 변수다** — E0170 과 `unreachable pattern`.
6. **`#[non_exhaustive]` 는 크레이트 경계에서만 일한다.** 같은 크레이트에서는 아무 일도 안 한다.

## 관련 자료

- [**17번 주제**](../17-enums-and-data-carrying-variants/) — 열거형과 변형. **완전성 검사가 성립하는 근거**가 거기 있다(닫힌 집합).
- [**04번 주제**](../04-expressions-and-semicolons/) — 「블록이 값」이라는 규칙의 정본. 여기는 **`match` 가 그 규칙을 쓰는 방식**만.
- [**09번 주제**](../09-copy-clone-and-drop/) — 묶인 값이 이동하나 복사되나의 정본.
- [**08번 주제**](../08-ownership-and-move/) — 부분 이동(E0382)의 정본.
- [목록의 **19번 주제**](../19-pattern-syntax-guards-bindings-and-match-ergonomics/) — 가드·`@`·or 패턴·매치 인체공학. **이 주제가 미뤄 둔 패턴 문법 전부**가 거기다.
- [목록의 **20번 주제**](../20-if-let-while-let-let-else-and-let-chains/) — `if let`·`while let`·`let else`. **완전성 검사가 없는 쪽**이다.
- [목록의 **33번 주제**](../33-dyn-trait-objects-and-object-safety/) — 변형이 열려야 할 때 쓰는 트레이트 객체.
- 목록의 **47번 주제** — 에디션 차이 전수. 이 주제의 결과는 **2021 기준**이다.

## 용어 풀이

| 말 | 뜻 |
|---|---|
| **`match`** | 값을 패턴들과 맞춰 보고 먼저 맞는 팔을 고르는 **식** |
| **팔(arm)** | `패턴 => 식` 한 줄. 가드가 붙을 수 있다 |
| **대상 값(scrutinee)** | `match` 가 보고 있는 값. `match e` 의 `e` |
| **완전성 검사** | 팔들이 타입의 모든 값을 덮는지 컴파일러가 확인하는 것 |
| **와일드카드 `_`** | 무엇이든 잡고 **이름을 안 묶는** 패턴 |
| **변수 패턴** | 소문자든 대문자든 **경로가 아닌 이름**. 무엇이든 잡고 이름을 묶는다 |
| **`..`(rest 패턴)** | 나머지 칸을 **여럿** 건너뛴다. `_` 는 한 칸 |
| **`#[non_exhaustive]`** | 「더 늘 수 있다」는 표시. 다른 크레이트에서 `_` 를 강제한다 |
| **`matches!`** | `match` 를 `bool` 한 줄로 접는 매크로(1.42+) |
| **`unreachable pattern`** | 앞 팔이 이미 다 덮어 닿을 수 없는 팔. **경고**다 |

## 더 들어가면

- **완전성 검사는 알고리즘이다** — 「유용성(usefulness)」 계산이라 부르고, 팔을 하나씩 추가하며
  「이 팔이 새로 덮는 값이 있나」를 묻는다. `unreachable pattern` 경고가 그 계산의 부산물이다.
- **빈 타입**(`enum Never {}`)을 `match` 하면 **팔이 하나도 없어도 완전**하다 — 덮을 값이 없기 때문이다.
- **`#[non_exhaustive]` 는 구조체와 변형에도 붙는다** — 그때는 `..` 를 강제한다. 이 목록 밖이다.
- **배타적 범위 패턴** `a..b` 는 **1.80.0부터** 안정이다. 이 문서는 전부 `..=` 를 썼다.
