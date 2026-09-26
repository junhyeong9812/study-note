# rust/syntax/17 — 열거형과 데이터를 담는 변형 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [The Rust Reference — Enumerations](https://doc.rust-lang.org/reference/items/enumerations.html) ·
> [Reference — Type layout](https://doc.rust-lang.org/reference/type-layout.html) ·
> [Reference — Implementations](https://doc.rust-lang.org/reference/items/implementations.html) ·
> [`std::mem::size_of`](https://doc.rust-lang.org/std/mem/fn.size_of.html) ·
> [`std::mem::discriminant`](https://doc.rust-lang.org/std/mem/fn.discriminant.html) ·
> [`std::option::Option`](https://doc.rust-lang.org/std/option/enum.Option.html).
> ★ `rustc --explain E0559` / `E0605` / `E0732` / `E0204` / `E0665` / `E0072` 는 **확인용으로만 열었고 본문에 옮기지 않았다.**
> 본문의 진단은 전부 내가 던져서 받은 것이다.
> **실행 검증** — 이 문서의 모든 출력·에러·경고는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 받은 것이다. **손으로 옮겨 적은 출력은 한 줄도 없다** —\
> 캡처 스크립트가 블록을 파일로 받고 조립기가 원고에 끼워 넣었다.\
> ★★ **`rustc ex.rs` 만 쓰면 에디션 2015 다.** 이 갈래는 `--edition 2021` 을 반드시 붙인다.\
> 소스 파일 이름은 전부 `ex.rs` 로 고정했고 **진단의 줄 번호는 그 파일 기준**이다.
> **버전** — 열거형·데이터를 담는 변형·`impl for enum` 은 전부 1.0.0부터다.\
> **`#[derive(Default)]` + `#[default]` 변형 표시**는 **1.62.0**부터다. 연관 상수는 1.20.0부터다.\
> 니치 최적화(`Option<Box<T>>` 가 `Box<T>` 와 같은 크기인 것)는 **언어 보장이 아니라 이 판의 관찰**이다(아래 표).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 흔들리는 칸 / 안 흔들리는 칸

이 갈래에서 **다시 돌리면 달라지는 칸**을 미리 갈라 둔다. 제출 전 재대조를 한 줄에 판정하기 위해서다.

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | 패닉 첫 줄 `thread 'main' (…)` 괄호 안의 OS 스레드 id | 실행마다 커널이 주는 번호다 |
| **흔들린다** | `0x…` 주소 · 힙 포인터 값 | 실행마다 다르다 |
| **흔들린다** | `HashSet`·`HashMap` 의 `{:?}` 순회 순서 | 보장이 없다 — 이 문서는 **정렬해서 찍어** 아예 피했다 |
| 안 흔들린다 | `파일:줄:칸`(`ex.rs:23:48`) | 소스가 같으면 같다 |
| 안 흔들린다 | 에러 번호·제목·`= note:`·`help:` 본문 | 같은 rustc 판에서 고정이다 |
| 안 흔들린다 | 종료 코드(`0` · 컴파일 실패 `1` · 패닉 `101`) | 고정이다 |
| 안 흔들린다 | `size_of`·`align_of` 값 | **이 타깃·이 rustc 판에서는** 고정이다(다른 판에서는 아니다 — §구현 세부) |

## 한눈에 — 쉽게 말하면

**열거형은 「또는」이다.** 구조체가 `A 그리고 B 그리고 C` 라면, 열거형은 `A 또는 B 또는 C` 다.

여기서 다른 언어의 enum 과 갈린다. 자바·C 의 enum 은 **이름표 목록**이지만,
Rust 의 열거형은 **변형마다 서로 다른 모양의 짐을 실을 수 있다**.

| 비유 | 실체 |
|---|---|
| 창구에서 받는 **번호표** — 번호만 있다 | **단위 변형** — `Quit`. 짐이 없다 |
| **짐칸이 번호로 매겨진** 수하물 — `.0`·`.1` | **튜플 변형** — `Move(i32, i32)` |
| **짐칸에 이름표가 붙은** 수하물 | **구조체 변형** — `Write { text: String, bold: bool }` |
| 「이 봉투 안에 든 것이 **어느 종류인지** 겉에 찍힌 도장」 | **판별자(discriminant)** — 값 안에 같이 실린 태그 |
| 봉투 크기는 **제일 큰 짐 + 도장 자리** | 열거형의 `size_of` |
| 짐 쪽에 **절대 안 쓰는 무늬**가 있으면 그 무늬를 도장으로 쓴다 | ★ **니치 최적화** — `Option<Box<T>>` 가 `Box<T>` 와 같은 크기인 이유 |
| **양식과 따로 묶인 매뉴얼철** | `impl` 블록. 열거형에도 똑같이 붙는다 |

- ★★ **변형마다 짐이 다르다** — 그래서 꺼낼 때 `match` 가 필요하다(다음 주제).
- ★★ **「불가능한 상태」를 적을 수가 없게 만드는 도구**다. 플래그 세 개를 열거형 하나로 바꾸면
  모순된 조합이 **타입에서 사라진다**((3)).
- ★ **`Option`·`Result` 도 그냥 열거형**이다. 언어 기능이 아니라 표준 라이브러리에 적힌 `enum` 선언이다((6)).

```text
   struct 는 「그리고」 · enum 은 「또는」

   struct Conn { connected: bool, session_id: Option<u32>, error: Option<String> }
        └─ 2 × 2 × 2 = 여덟 가지 조합이 전부 「적을 수 있는 값」이다
           그중 절반은 말이 안 된다 (연결됐는데 세션이 없고 에러가 있다)

   enum Conn { Idle, Connected { session_id: u32 }, Failed(String) }
        └─ 세 가지뿐이다. 말이 안 되는 조합은 「문법으로 적을 수가 없다」

   메모리에서는 이렇게 생겼다 (이 판의 관찰)

     Conn::Connected { session_id: 7 }        Conn::Failed("타임아웃")
     ┌──────┬───────────────────────┐        ┌──────┬───────────────────────┐
     │ 태그 │ session_id: u32 = 7   │        │ 태그 │ String(ptr,cap,len)   │
     │  1   │                       │        │  2   │                       │
     └──────┴───────────────────────┘        └──────┴───────────────────────┘
       └ 판별자. 같은 봉투를 어느 변형으로 읽을지 정한다
       └ 봉투 크기는 「제일 큰 짐」에 맞춘다 — String 쪽이 24바이트라 전체가 32바이트
```

> **열거형(enum)** — 여러 **변형(variant)** 중 **정확히 하나**인 값을 담는 타입.\
> 「합 타입(sum type)」이라고도 한다 — 가짓수가 **더해지기** 때문이다.

> **변형(variant)** — 열거형이 가질 수 있는 한 가지 모양. 단위·튜플·구조체 세 형태가 있다.

> **판별자(discriminant)** — 「지금 어느 변형인가」를 나타내는 값.\
> C 스타일 열거형에서는 `as i32` 로 꺼낼 수 있고, 데이터를 담으면 꺼낼 수 없다((4)).

> **니치(niche)** — 그 타입이 **절대 가지지 않는 비트 패턴**.\
> `bool` 은 2부터 255까지, `&T` 는 `0`(널), `NonZeroU8` 은 `0` 이 니치다.\
> 컴파일러는 그 자리를 **다른 변형의 표식으로 재활용**한다((7)).

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **변형 세 형태 중 무엇을 고르나** — 단위·튜플·구조체가 각각 어느 자리에 맞나.
2. **열거형이 설계에서 무엇을 없애 주나** — 「불가능한 상태」가 왜 **적을 수조차 없게** 되나.
3. **봉투가 몇 바이트인가** — 태그는 어디 살고, 왜 `Option<Box<T>>` 는 **한 바이트도 안 커지나**.

★ [**16번 주제**](../16-structs-impl-and-associated-functions/)가 「칸을 **모으는**」 타입이었다면,
여기는 「칸 중 **하나만 고르는**」 타입이다. 둘은 `impl` 문법을 그대로 공유한다.

## 동작 방식

### (0) 이 주제가 쓰는 네 창

**언제 쓰나** — 아래 모든 절이 이 넷 중 하나로 접지한다.

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| **일부러 던져서 받는 컴파일 에러** | 적을 수 없는 것이 무엇인지 — E0559·E0605·E0204·E0072 | [**11번 주제**](../11-borrow-checker-rejections/)의 「에러도 출력이다」 |
| **`size_of`·`align_of` 로 봉투 재기** | 변형 중 제일 큰 짐 + 태그가 실제로 몇 바이트인가 | [**16번 주제**](../16-structs-impl-and-associated-functions/)에서 이어받았다 |
| ★★ **`transmute` 로 1바이트를 정수로 옮겨 담아 읽기** | **태그가 어디 사는가** — 니치를 쓸 때와 안 쓸 때 | ★ 이 주제의 고유 창 |
| **`std::mem::discriminant` 로 변형만 비교** | 짐을 안 보고 **도장만** 비교하기 | ★ 이 주제의 고유 창 |

★ 세 번째 창이 이 주제의 핵심이다. `size_of` 는 **몇 바이트인지**만 말하지 **그 바이트가 무엇인지**는
말하지 않는다. 1바이트짜리 `Option<bool>`·`Option<NonZeroU8>` 을 `u8` 로 옮겨 담아 **직접 읽으면**
니치가 무엇을 하는지 숫자로 보인다((7)).
★ 크기가 1바이트고 **패딩이 없는 것만** 이렇게 읽는다 — 초기화 안 된 패딩 바이트를 읽는 것은 미정의 동작이다.

### (1) 변형 세 종류 — 선언·생성·꺼내기

**언제 쓰나** — 열거형을 새로 만들 때마다. **변형마다 따로** 고른다.

```text
===== 소스: ex.rs =====
// ex.rs
// 열거형 변형 세 종류 — 단위·튜플·구조체. 선언·생성·꺼내기를 한 파일에서 본다
#[derive(Debug)]
enum Message {
    Quit,                          // 단위 변형 — 데이터 없음
    Move(i32, i32),                // 튜플 변형 — 이름 없는 칸
    Write { text: String, bold: bool },   // 구조체 변형 — 이름 있는 칸
}

fn describe(m: &Message) -> String {
    match m {
        Message::Quit => String::from("끝"),
        Message::Move(x, y) => format!("이동 {} {}", x, y),
        Message::Write { text, bold } => format!("쓰기 {:?} 굵게={}", text, bold),
    }
}

fn main() {
    let msgs = vec![
        Message::Quit,
        Message::Move(3, -4),
        Message::Write { text: String::from("가나"), bold: true },
    ];
    for m in &msgs {
        println!("{} | {:?}", describe(m), m);
    }
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
끝 | Quit
이동 3 -4 | Move(3, -4)
쓰기 "가나" 굵게=true | Write { text: "가나", bold: true }
(종료 코드 0)
```

읽는 법.

- **단위 변형** `Quit` — 짐이 없다. 이름만으로 값이 된다.
- **튜플 변형** `Move(i32, i32)` — 칸에 **번호**가 붙는다. 꺼낼 때 `Message::Move(x, y)`.
- **구조체 변형** `Write { text, bold }` — 칸에 **이름**이 붙는다. 꺼낼 때도 이름으로.
- 셋 모두 **같은 열거형 안에 섞어 둘 수 있다.** 구조체 세 종류와 이름이 같지만(16번 주제),
  **변형은 타입이 아니다** — `Message::Quit` 은 타입이 아니라 `Message` 타입의 **값**이다.
- ★ `Message::Move` 는 **함수이기도 하다** — 튜플 구조체와 같다. `.map(Message::Move)` 로 넘길 수 있다.

### (2) 열거형에도 `impl` 을 붙인다

**언제 쓰나** — 상태 전이·질의를 그 타입 **안에** 두고 싶을 때. 구조체와 문법이 한 글자도 다르지 않다.

```text
===== 소스: ex.rs =====
// ex.rs
// 열거형에도 impl 을 붙인다 — 메서드·연관 함수·연관 상수·Self
#[derive(Debug, Clone, Copy, PartialEq)]
enum Light { Red, Yellow, Green }

impl Light {
    const COUNT: usize = 3;              // 연관 상수

    fn start() -> Self { Light::Red }    // 연관 함수 — self 없음

    fn next(self) -> Self {              // 메서드 — 리시버가 self(값)
        match self {
            Light::Red => Light::Green,
            Light::Green => Light::Yellow,
            Light::Yellow => Light::Red,
        }
    }

    fn can_go(&self) -> bool { matches!(self, Light::Green) }
}

fn main() {
    let mut l = Light::start();
    for _ in 0..3 {
        println!("{:?} 건널 수 있나={} (전체 {}개)", l, l.can_go(), Light::COUNT);
        l = l.next();
    }
    println!("한 바퀴 돌아왔나={}", l == Light::start());
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
Red 건널 수 있나=false (전체 3개)
Green 건널 수 있나=true (전체 3개)
Yellow 건널 수 있나=false (전체 3개)
한 바퀴 돌아왔나=true
(종료 코드 0)
```

읽는 법.

- `fn start() -> Self` 는 **연관 함수**(리시버 없음) — `Light::start()` 로 부른다.
- `fn next(self) -> Self` 는 **메서드**(리시버 `self`) — `l.next()`. `Light` 가 `Copy` 라 원본이 안 죽는다.
- `const COUNT` 는 **연관 상수**. 열거형에도 똑같이 붙는다.
- ★ `matches!(self, Light::Green)` 은 **`match` 를 한 줄로 접는 매크로**다 — `bool` 을 낸다.
- ★★ `impl` 안에서 `Self` 는 `Light` 의 별명이고, `self` 는 **그 값**이다. 16번 주제와 같은 구분이다.

### (3) 불가능한 상태를 타입에서 지우기 — 전과 후

**언제 쓰나** — 「이 불리언이 참이면 저 필드는 반드시 있어야 한다」는 주석을 쓰고 있을 때.
그 주석은 **타입으로 적을 수 있다**.

**전** — 플래그와 `Option` 으로 표현한 판. 모순이 **값으로 만들어진다**.

```text
===== 소스: ex.rs =====
// ex.rs
// 불가능한 상태 — 전. 구조체 + 플래그로 표현하면 모순된 상태가 「만들어진다」
#[derive(Debug)]
struct Conn {
    connected: bool,
    session_id: Option<u32>,
    error: Option<String>,
}

fn report(c: &Conn) -> String {
    if c.connected {
        format!("연결됨 세션={:?}", c.session_id)
    } else if let Some(e) = &c.error {
        format!("실패 {}", e)
    } else {
        String::from("대기")
    }
}

fn main() {
    let ok = Conn { connected: true, session_id: Some(7), error: None };
    // ★ 모순 — 연결됐다면서 세션이 없고, 동시에 에러까지 있다
    let bad = Conn { connected: true, session_id: None, error: Some(String::from("타임아웃")) };
    println!("{}", report(&ok));
    println!("{}", report(&bad));
    println!("{:?}", bad);
    // 2^1 * 2 * 2 = 표현 가능한 조합
    println!("이 타입이 표현할 수 있는 모순 조합이 컴파일러에게 막히나: 아니오");
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
연결됨 세션=Some(7)
연결됨 세션=None
Conn { connected: true, session_id: None, error: Some("타임아웃") }
이 타입이 표현할 수 있는 모순 조합이 컴파일러에게 막히나: 아니오
(종료 코드 0)
```

**후** — 열거형으로 바꾼 판. 같은 모순을 적으면 **컴파일러가 막는다**.

```text
===== 소스: ex.rs =====
// ex.rs
// 불가능한 상태 — 후. 열거형으로 바꾸면 그 모순을 「적을 수가 없다」
#[derive(Debug)]
enum Conn {
    Idle,
    Connected { session_id: u32 },
    Failed(String),
}

fn report(c: &Conn) -> String {
    match c {
        Conn::Idle => String::from("대기"),
        Conn::Connected { session_id } => format!("연결됨 세션={}", session_id),
        Conn::Failed(e) => format!("실패 {}", e),
    }
}

fn main() {
    println!("{}", report(&Conn::Idle));
    println!("{}", report(&Conn::Connected { session_id: 7 }));
    println!("{}", report(&Conn::Failed(String::from("타임아웃"))));
    // ★ 앞 판의 모순을 그대로 적어 본다 — 연결됐는데 세션이 없고 에러도 있는 상태
    let bad = Conn::Connected { session_id: 7, error: String::from("타임아웃") };
    println!("{:?}", bad);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0559]: variant `Conn::Connected` has no field named `error`
  --> ex.rs:23:48
   |
23 |     let bad = Conn::Connected { session_id: 7, error: String::from("타임아웃") };
   |                                                ^^^^^ `Conn::Connected` does not have this field
   |
   = note: all struct fields are already assigned

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0559`.
(종료 코드 1)
```

읽는 법.

- 전 판은 `connected: true` 인데 `session_id: None` 이고 `error: Some(...)` 인 값을 **아무 불평 없이 만든다.**
  `report` 가 그 값을 「연결됨 세션=None」으로 읽는다 — 조용히 틀린 답이다.
- 후 판에서 같은 모순을 적으면 **E0559** 가 난다 — 제목 줄이 `` variant `Conn::Connected` has no field named `error` `` 다.
  ★ 진단이 「그런 칸이 없다」고 말한다. **적을 자리 자체가 없어진 것**이다.
- ★★ 세는 법: 전 판이 표현할 수 있는 값은 `2 × (1+1) × (1+많음)` 이고 그중 절반 이상이 말이 안 된다.
  후 판은 **세 갈래뿐**이고 전부 말이 된다.
- 이 설계의 값은 「실수를 덜 한다」가 아니라 **「그 실수를 적을 수 없다」** 다.

### (4) C 스타일 열거형과 판별값 — 그리고 `as` 가 막히는 자리

**언제 쓰나** — 외부 규약(HTTP 코드·프로토콜 상수)과 숫자로 맞춰야 할 때.

```text
===== 소스: ex.rs =====
// ex.rs
// C 스타일 열거형 — 판별값을 직접 주고 `as` 로 정수로 꺼낸다
#[derive(Debug, Clone, Copy)]
enum Status {
    Ok = 200,
    NotFound = 404,
    Teapot = 418,
}

#[derive(Debug, Clone, Copy)]
enum Step { A, B, C = 10, D }   // 안 적으면 「앞 값 + 1」

fn main() {
    println!("{} {} {}", Status::Ok as i32, Status::NotFound as i32, Status::Teapot as i32);
    println!("{} {} {} {}", Step::A as u8, Step::B as u8, Step::C as u8, Step::D as u8);
    println!("{:?} {:?}", Status::Teapot, Step::D);
    // 크기 — 판별값만 있는 열거형은 판별값 하나만큼이다
    println!("Status {} Step {}", size_of::<Status>(), size_of::<Step>());
    // 역방향은 공짜가 아니다 — 정수에서 열거형으로 가는 `as` 는 없다
    let n = 404;
    let back = match n { 200 => Some(Status::Ok), 404 => Some(Status::NotFound), _ => None };
    println!("{:?}", back);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
200 404 418
0 1 10 11
Teapot D
Status 2 Step 1
Some(NotFound)
(종료 코드 0)
```

읽는 법.

- **판별값을 직접 적으면** `as i32` 로 꺼낼 수 있다. 안 적으면 **0부터, 앞 값 + 1** 이다(`Step::D` 가 11).
- ★ **역방향은 없다.** 정수에서 열거형으로 가는 `as` 는 없고 `match` 나 `TryFrom` 을 손으로 쓴다.
- ★ 크기가 변형 수가 아니라 **판별값의 크기**로 정해진다 — `Status` 는 404·418 때문에 2바이트, `Step` 은 1바이트.

**데이터를 담은 변형이 하나라도 있으면 `as` 가 막힌다.**

```text
===== 소스: ex.rs =====
// ex.rs
// 데이터를 담은 변형이 하나라도 있으면 `as` 로 정수를 못 꺼낸다
enum Mixed {
    Zero,
    One(u32),
}

fn main() {
    println!("{}", Mixed::Zero as i32);
    let m = Mixed::One(7);
    println!("{}", m as i32);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0605]: non-primitive cast: `Mixed` as `i32`
 --> ex.rs:9:20
  |
9 |     println!("{}", Mixed::Zero as i32);
  |                    ^^^^^^^^^^^^^^^^^^ an `as` expression can be used to convert enum types to numeric types only if the enum type is unit-only or field-less
  |
  = note: see https://doc.rust-lang.org/reference/items/enumerations.html#casting for more information

error[E0605]: non-primitive cast: `Mixed` as `i32`
  --> ex.rs:11:20
   |
11 |     println!("{}", m as i32);
   |                    ^^^^^^^^ an `as` expression can be used to convert enum types to numeric types only if the enum type is unit-only or field-less
   |
   = note: see https://doc.rust-lang.org/reference/items/enumerations.html#casting for more information

error: aborting due to 2 previous errors

For more information about this error, try `rustc --explain E0605`.
(종료 코드 1)
```

- **E0605** `non-primitive cast`. 결정적인 문구는
  「``an `as` expression can be used to convert enum types to numeric types only if the enum type is unit-only or field-less`` 」다.
- ★ **`Mixed::Zero` 처럼 짐이 없는 변형에서도 막힌다** — 판정은 **변형 하나가 아니라 열거형 전체**에 걸린다.
  같은 에러가 두 줄에서 각각 난다.

**판별값을 적으면서 데이터 변형을 두면 선언 자체가 막힌다.**

```text
===== 소스: ex.rs =====
// ex.rs
// 판별값을 직접 적으면서 데이터 변형을 두면 선언 자체가 막힌다
enum Mixed {
    Zero = 0,
    One(u32),
}

fn main() {
    let _ = Mixed::Zero;
    let _ = Mixed::One(7);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0732]: `#[repr(inttype)]` must be specified for enums with explicit discriminants and non-unit variants
 --> ex.rs:3:1
  |
3 | enum Mixed {
  | ^^^^^^^^^^
4 |     Zero = 0,
  |            - explicit discriminant specified here
5 |     One(u32),
  |     --- non-unit discriminant declared here

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0732`.
(종료 코드 1)
```

- **E0732** — `#[repr(inttype)]` 을 요구한다. `#[repr(u8)]` 을 붙이면 **선언은 통과**하지만
  `as` 는 여전히 E0605 다(위 규칙이 그대로 산다).

### (5) `#[derive(...)]` — 되는 것과 안 되는 것

**언제 쓰나** — 비교·정렬·해시·기본값이 필요할 때. **파생은 필드/변형에 조건을 건다.**

```text
===== 소스: ex.rs =====
// ex.rs
// 열거형에 붙는 derive — 자동 파생이 되는 것들
use std::collections::HashSet;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, PartialOrd, Ord, Default)]
enum Level {
    #[default]
    Low,        // ★ #[default] 로 어느 변형이 기본인지 찍어 준다 (1.62부터)
    Mid,
    High,
}

fn main() {
    let mut v = vec![Level::High, Level::Low, Level::Mid, Level::High];
    v.sort();                       // Ord — 선언 순서가 곧 순서다
    println!("{:?}", v);
    println!("기본값 {:?}", Level::default());
    println!("같나 {} 작나 {}", Level::Low == Level::Low, Level::Low < Level::High);
    let s: HashSet<Level> = v.iter().copied().collect();   // Hash + Eq
    let mut uniq: Vec<Level> = s.into_iter().collect();
    uniq.sort();                    // ★ HashSet 순회 순서는 보장이 없어 정렬해서 찍는다
    println!("{:?}", uniq);
    println!("복사됐나 {:?}", v[0]);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
[Low, Mid, High, High]
기본값 Low
같나 true 작나 true
[Low, Mid, High]
복사됐나 Low
(종료 코드 0)
```

읽는 법.

- `Ord` 를 파생하면 **선언 순서가 곧 순서**다 — `Low < Mid < High`. 순서를 바꾸면 의미가 바뀐다.
- ★ **`Default` 는 어느 변형이 기본인지 모른다** — 그래서 `#[default]` 로 찍어 준다(**1.62.0부터**).
- `HashSet` 에 넣으려면 `Hash + Eq` 가 둘 다 필요하다.
  ★ **순회 순서는 보장이 없어 정렬해서 찍었다** — 이 규칙은 [`data-structure/05-hashmap`](../../../../../data-structure/05-hashmap/)가 아니라
  이 문서의 「흔들리는 칸」 표에 속한다.

**거부되는 두 자리.**

```text
===== 소스: ex.rs =====
// ex.rs
// derive 가 거부되는 두 자리 — Copy 와 Default
#[derive(Clone, Copy)]
enum Payload {
    Num(u32),
    Text(String),      // String 은 Copy 가 아니다
}

#[derive(Default)]
enum Mode {
    Fast,
    Slow,
}

fn main() {
    let _ = Payload::Num(1);
    let _ = Mode::Fast;
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0665]: `#[derive(Default)]` on enum with no `#[default]`
  --> ex.rs:9:10
   |
 9 |   #[derive(Default)]
   |            ^^^^^^^
10 | / enum Mode {
11 | |     Fast,
12 | |     Slow,
13 | | }
   | |_- this enum needs a unit variant marked with `#[default]`
   |
help: make this unit variant default by placing `#[default]` on it
   |
11 |     #[default] Fast,
   |     ++++++++++
help: make this unit variant default by placing `#[default]` on it
   |
12 |     #[default] Slow,
   |     ++++++++++

error[E0204]: the trait `Copy` cannot be implemented for this type
 --> ex.rs:3:17
  |
3 | #[derive(Clone, Copy)]
  |                 ^^^^
...
6 |     Text(String),      // String 은 Copy 가 아니다
  |          ------ this field does not implement `Copy`

error: aborting due to 2 previous errors

Some errors have detailed explanations: E0204, E0665.
For more information about an error, try `rustc --explain E0204`.
(종료 코드 1)
```

- **E0204** — `Copy` 는 **모든 변형의 모든 칸**이 `Copy` 여야 한다. `String` 이 든 변형 하나가 전체를 막는다.
  진단이 「`` this field does not implement `Copy` `` 」로 **그 칸을 짚는다**.
- **E0665** — `Default` 를 파생했는데 `#[default]` 가 없다. `help:` 가 **변형마다 하나씩** 고친 코드를 준다.
- ★ 파생이 거는 조건은 트레이트마다 다르다 — 그 전수는 [목록의 **27번 주제**](../27-derive-macros-debug-clone-partialeq-default-hash/)의 몫이다.

### (6) `Option` 과 `Result` 도 그냥 열거형이다

**언제 쓰나** — 「Rust 에는 null 이 없다」는 말이 무슨 뜻인지 확인할 때.

```text
===== 소스: ex.rs =====
// ex.rs
// Option 과 Result 도 그냥 열거형이다 — 똑같은 것을 직접 만들어 본다
#[derive(Debug)]
enum MyOption<T> { MyNone, MySome(T) }

#[derive(Debug)]
enum MyResult<T, E> { MyOk(T), MyErr(E) }

use MyOption::{MyNone, MySome};
use MyResult::{MyOk, MyErr};

fn find(v: &[i32], target: i32) -> MyOption<usize> {
    for (i, x) in v.iter().enumerate() {
        if *x == target { return MySome(i); }
    }
    MyNone
}

fn half(n: i32) -> MyResult<i32, String> {
    if n % 2 == 0 { MyOk(n / 2) } else { MyErr(format!("{} 는 홀수", n)) }
}

fn main() {
    let v = [10, 20, 30];
    println!("{:?} {:?}", find(&v, 20), find(&v, 99));
    println!("{:?} {:?}", half(8), half(7));
    // std 것과 크기·모양을 나란히 — 변형 이름만 다르다
    println!("내 것 {} std {}", size_of::<MyOption<i32>>(), size_of::<Option<i32>>());
    println!("std  {:?} {:?}", Some(1usize), None::<usize>);
    // std 의 정의도 이것과 같다: enum Option<T> { None, Some(T) }
    let o: Option<i32> = Some(3);
    println!("{:?}", match o { Some(n) => n * 2, None => -1 });
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
MySome(1) MyNone
MyOk(4) MyErr("7 는 홀수")
내 것 8 std 8
std  Some(1) None
6
(종료 코드 0)
```

읽는 법.

- `MyOption` 은 **이름만 다르고 std 의 `Option` 과 같은 선언**이다. 크기도 8로 같다.
- ★★ std 의 정의는 이것이다 — `enum Option<T> { None, Some(T) }`.
  **언어 기능이 아니라 라이브러리 타입**이고, 그래서 내가 똑같은 것을 만들 수 있다.
- 다른 점은 셋뿐이다 — **prelude 에 들어 있어 `use` 가 필요 없고**, `?` 연산자가 붙고,
  `map`·`and_then` 같은 조합 메서드가 딸려 있다([목록의 **21번 주제**](../21-option-and-combinators/)·**22번 주제**).
- ★ 「null 이 없다」는 **없음을 타입에 적게 강제한다**는 뜻이다 — (3)의 설계가 표준 라이브러리 수준에서 한 번 더 일어난 것이다.

### (7) ★★ 봉투는 몇 바이트인가 — 태그와 니치 최적화

**언제 쓰나** — `Option` 을 씌우는 비용이 걱정될 때. 그리고 열거형이 커지는 이유를 알고 싶을 때.

```text
===== 소스: ex.rs =====
// ex.rs
// 니치 최적화 — Option 을 씌워도 크기가 안 느는 타입들
use std::num::NonZeroU32;

#[derive(Debug)]
enum Never2 { A(u32), B(u32) }          // 데이터 변형 둘 — 태그가 따로 필요하다

fn row(name: &str, bare: usize, opt: usize) {
    println!("{:<22} {:>3} {:>3}  {}", name, bare, opt,
             if bare == opt { "니치 씀" } else { "태그 따로" });
}

fn main() {
    println!("{:<22} {:>3} {:>3}", "타입", "T", "Option<T>");
    row("Box<i32>",      size_of::<Box<i32>>(),      size_of::<Option<Box<i32>>>());
    row("&i32",          size_of::<&i32>(),          size_of::<Option<&i32>>());
    row("&mut i32",      size_of::<&mut i32>(),      size_of::<Option<&mut i32>>());
    row("String",        size_of::<String>(),        size_of::<Option<String>>());
    row("Vec<u8>",       size_of::<Vec<u8>>(),       size_of::<Option<Vec<u8>>>());
    row("NonZeroU32",    size_of::<NonZeroU32>(),    size_of::<Option<NonZeroU32>>());
    row("char",          size_of::<char>(),          size_of::<Option<char>>());
    row("bool",          size_of::<bool>(),          size_of::<Option<bool>>());
    row("u8",            size_of::<u8>(),            size_of::<Option<u8>>());
    row("u32",           size_of::<u32>(),           size_of::<Option<u32>>());
    row("f64",           size_of::<f64>(),           size_of::<Option<f64>>());
    row("()",            size_of::<()>(),            size_of::<Option<()>>());
    row("Never2",        size_of::<Never2>(),        size_of::<Option<Never2>>());
    let get = |e: &Never2| match e { Never2::A(n) | Never2::B(n) => *n };
    let (a, b) = (Never2::A(1), Never2::B(2));
    println!("{:?}={} {:?}={}", a, get(&a), b, get(&b));
    // 니치가 겹겹이 쌓인다
    println!("Option<Option<bool>> {}  Option<Option<Option<bool>>> {}",
             size_of::<Option<Option<bool>>>(), size_of::<Option<Option<Option<bool>>>>());
    println!("Result<Box<i32>, ()> {}  Result<u32, u32> {}",
             size_of::<Result<Box<i32>, ()>>(), size_of::<Result<u32, u32>>());
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
타입                       T Option<T>
Box<i32>                 8   8  니치 씀
&i32                     8   8  니치 씀
&mut i32                 8   8  니치 씀
String                  24  24  니치 씀
Vec<u8>                 24  24  니치 씀
NonZeroU32               4   4  니치 씀
char                     4   4  니치 씀
bool                     1   1  니치 씀
u8                       1   2  태그 따로
u32                      4   8  태그 따로
f64                      8  16  태그 따로
()                       0   1  태그 따로
Never2                   8   8  니치 씀
A(1)=1 B(2)=2
Option<Option<bool>> 1  Option<Option<Option<bool>>> 1
Result<Box<i32>, ()> 8  Result<u32, u32> 8
(종료 코드 0)
```

읽는 법.

- ★★ **`Box<i32>`·`&i32`·`String`·`Vec<u8>`·`NonZeroU32`·`char`·`bool` 은 `Option` 을 씌워도 크기가 안 는다.**
  **널이 될 수 없다·0이 될 수 없다·유효 범위가 좁다**는 성질이 곧 **비어 있는 비트 패턴**이고,
  컴파일러가 거기에 `None` 을 적는다.
- **`u8`·`u32`·`f64` 는 256가지·`2^32`가지를 다 쓴다.** 남는 무늬가 없으니 **태그를 따로** 둔다 —
  그래서 `1 → 2` · `4 → 8` · `8 → 16` 으로 는다(정렬 때문에 딱 1바이트만 늘지 않는다).
- ★ **`()` 는 0바이트인데 `Option<()>` 은 1바이트다** — 구별할 것이 둘인데 담을 곳이 없으면 자리를 새로 만든다.
- ★★ **니치는 겹겹이 쌓인다.** `Option<Option<Option<bool>>>` 까지 **1바이트**다 —
  `bool` 이 남긴 254가지 무늬를 차례로 하나씩 쓴다.
- `Never2 { A(u32), B(u32) }` 는 8바이트인데 `Option<Never2>` 도 8이다 —
  **자기 태그 바이트에 남은 무늬**를 `None` 이 빌려 쓴다.

```text
   니치가 있을 때와 없을 때 — 같은 「한 칸」에 무엇이 적히나

   Option<bool>        1바이트         Option<u8>              2바이트
   ┌────────────────────────┐          ┌──────┬────────────────┐
   │ 0 = Some(false)        │          │ 태그 │     u8 값       │
   │ 1 = Some(true)         │          │ 0/1  │   0 … 255       │
   │ 2 = None   ★ 비어 있던 │          └──────┴────────────────┘
   │            무늬 자리    │            └ u8 은 256가지를 다 쓴다
   └────────────────────────┘               → 태그를 따로 둘 수밖에 없다

   Option<&i32>        8바이트         Option<NonZeroU8>       1바이트
   ┌────────────────────────┐          ┌────────────────────────┐
   │ 0x0000…0000 = None     │          │ 0 = None  ★ 0 을 못 쓰는│
   │ 그 밖 = Some(그 주소)   │          │ 그 밖 = Some(그 값)     │
   └────────────────────────┘          └────────────────────────┘
     └ 참조가 절대 못 갖는 값(널)이 곧 니치다 — 널 포인터 최적화
```

**그 바이트가 실제로 무엇인지 읽어 본다.**

```text
===== 소스: ex.rs =====
// ex.rs
// 태그가 어디 사는가 — 1바이트짜리를 정수로 옮겨 담아 직접 읽는다
use std::num::NonZeroU8;

fn main() {
    // bool 은 0·1 만 쓴다. 남는 값 하나가 None 자리가 된다
    let n: u8 = unsafe { std::mem::transmute::<Option<bool>, u8>(None) };
    let f: u8 = unsafe { std::mem::transmute::<Option<bool>, u8>(Some(false)) };
    let t: u8 = unsafe { std::mem::transmute::<Option<bool>, u8>(Some(true)) };
    println!("Option<bool> 1바이트: None={} Some(false)={} Some(true)={}", n, f, t);

    // NonZeroU8 은 0 을 못 쓴다. 그 0 이 None 자리다
    let n2: u8 = unsafe { std::mem::transmute::<Option<NonZeroU8>, u8>(None) };
    let s2: u8 = unsafe { std::mem::transmute::<Option<NonZeroU8>, u8>(NonZeroU8::new(200)) };
    println!("Option<NonZeroU8> 1바이트: None={} Some(200)={}", n2, s2);

    // 참조는 널이 될 수 없다. 그 널이 None 자리다 — 널 포인터 최적화
    let x = 41i32;
    let r: usize = unsafe { std::mem::transmute::<Option<&i32>, usize>(Some(&x)) };
    let nn: usize = unsafe { std::mem::transmute::<Option<&i32>, usize>(None) };
    println!("Option<&i32>: None={} Some(&x)가 &x 주소와 같나={}",
             nn, r == (&x as *const i32 as usize));

    // 니치가 없으면 태그를 따로 둔다 — u8 은 256가지를 다 쓴다
    println!("Option<u8> 크기={} (u8 크기={})", size_of::<Option<u8>>(), size_of::<u8>());
    // 같은 값인데 서로 다른 변형임을 구별하는 표식
    let a: Option<u8> = Some(0);
    let b: Option<u8> = None;
    println!("판별자가 다른가={}",
             std::mem::discriminant(&a) != std::mem::discriminant(&b));
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
Option<bool> 1바이트: None=2 Some(false)=0 Some(true)=1
Option<NonZeroU8> 1바이트: None=0 Some(200)=200
Option<&i32>: None=0 Some(&x)가 &x 주소와 같나=true
Option<u8> 크기=2 (u8 크기=1)
판별자가 다른가=true
(종료 코드 0)
```

읽는 법.

- `Option<bool>` 을 1바이트 정수로 옮겨 담으면 `Some(false)=0` · `Some(true)=1` · **`None=2`** 다.
  ★ **`bool` 이 안 쓰는 2번 무늬가 `None` 의 자리**다. 태그가 따로 없다.
- `Option<NonZeroU8>` 은 **`None=0`** 이다 — `NonZeroU8` 이 못 쓰는 그 0 이다.
- `Option<&i32>` 의 `None` 은 **`0`**(널)이고 `Some(&x)` 는 **`x` 의 주소 그대로**다.
  이것이 **널 포인터 최적화**다 — C 의 「널이면 없음」과 **메모리에서는 같고 타입에서만 다르다**.
- 니치가 없는 `Option<u8>` 은 2바이트다. 그때는 `discriminant` 가 다른 바이트에 산다.
- ★ `std::mem::discriminant` 는 **짐을 안 보고 도장만** 비교한다 — `Some(0)` 과 `None` 이 다르다고 답한다.

### (8) 재귀 열거형 — 봉투 안에 봉투를 넣으면

**언제 쓰나** — 트리·리스트·표현식을 열거형으로 적을 때. **처음 쓰면 반드시 막히는 자리**다.

```text
===== 소스: ex.rs =====
// ex.rs
// 재귀 열거형은 크기를 못 정한다
#[derive(Debug)]
enum Tree {
    Leaf(i32),
    Node(Tree, Tree),
}

fn main() {
    let t = Tree::Node(Tree::Leaf(1), Tree::Leaf(2));
    println!("{:?}", t);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0072]: recursive type `Tree` has infinite size
 --> ex.rs:4:1
  |
4 | enum Tree {
  | ^^^^^^^^^
5 |     Leaf(i32),
6 |     Node(Tree, Tree),
  |          ---- recursive without indirection
  |
help: insert some indirection (e.g., a `Box`, `Rc`, or `&`) to break the cycle
  |
6 |     Node(Box<Tree>, Tree),
  |          ++++    +

error[E0391]: cycle detected when computing when `Tree` needs drop
 --> ex.rs:4:1
  |
4 | enum Tree {
  | ^^^^^^^^^
  |
  = note: ...which immediately requires computing when `Tree` needs drop again
  = note: cycle used when computing whether `Tree` needs drop
  = note: see https://rustc-dev-guide.rust-lang.org/overview.html#queries and https://rustc-dev-guide.rust-lang.org/query.html for more information

error: aborting due to 2 previous errors

Some errors have detailed explanations: E0072, E0391.
For more information about an error, try `rustc --explain E0072`.
(종료 코드 1)
```

- **E0072** — 제목은 ``recursive type `Tree` has infinite size`` 다. 진단이 `recursive without indirection` 으로
  **어느 칸이 문제인지** 짚고, `help:` 가 `Box`·`Rc`·`&` 셋을 댄다.
- ★ **E0391**(`cycle detected`)이 같이 난다 — 크기를 못 정하니 「해제가 필요한가」도 못 정한다. **딸린 에러**다.

```text
===== 소스: ex.rs =====
// ex.rs
// Box 로 한 칸 건너뛰면 크기가 정해진다 — 그리고 그 크기를 잰다
#[derive(Debug)]
enum Tree {
    Leaf(i32),
    Node(Box<Tree>, Box<Tree>),
}

impl Tree {
    fn sum(&self) -> i32 {
        match self {
            Tree::Leaf(n) => *n,
            Tree::Node(l, r) => l.sum() + r.sum(),
        }
    }
}

fn main() {
    let t = Tree::Node(
        Box::new(Tree::Leaf(1)),
        Box::new(Tree::Node(Box::new(Tree::Leaf(2)), Box::new(Tree::Leaf(3)))),
    );
    println!("{:?}", t);
    println!("합 {}", t.sum());
    println!("Tree {} Box<Tree> {} i32 {}",
             size_of::<Tree>(), size_of::<Box<Tree>>(), size_of::<i32>());
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
Node(Leaf(1), Node(Leaf(2), Leaf(3)))
합 6
Tree 16 Box<Tree> 8 i32 4
(종료 코드 0)
```

- `Box<Tree>` 는 **포인터 하나(8바이트)** 라 크기가 정해진다. `Tree` 전체는 **16바이트** —
  태그 + 정렬 + 포인터 하나 자리다(`Leaf(i32)` 는 4바이트라 `Node` 쪽이 크기를 정한다).
- 상세한 `Box` 이야기는 여기가 정본이 아니다([목록의 **40번 주제**](../40-box-recursive-types-and-dyn/)). 여기서는 **왜 막히나**까지다.

## 문법 — 형태와 규칙

**형태.**

```text
enum Name {
    Unit,                          // 단위 변형
    Tup(T1, T2),                   // 튜플 변형 — 칸에 번호
    Rec { a: T1, b: T2 },          // 구조체 변형 — 칸에 이름
    WithDisc = 5,                  // 판별값 (단위 변형에만, 그리고 전부 단위일 때만 자유롭다)
}

impl Name {
    const N: usize = 4;            // 연관 상수
    fn make() -> Self { Name::Unit }           // 연관 함수
    fn is_unit(&self) -> bool { matches!(self, Name::Unit) }   // 메서드
}
```

**규칙.**

- 변형은 **타입이 아니다.** `Name::Unit` 의 타입은 `Name` 이다 — 변형별 타입은 없다.
- 변형 이름은 **열거형 이름으로 한정**해 쓴다. `use Name::*;` 로 열 수 있지만 **그때 충돌이 생긴다**.
- 튜플 변형의 이름은 **함수**다 — `fn(T1, T2) -> Name`.
- `as` 로 정수를 꺼내는 것은 **열거형 전체가 단위 변형뿐일 때만** 된다((4)).
- `#[repr(u8)]`·`#[repr(C)]` 로 표현을 고정할 수 있다. **안 고정하면 배치는 컴파일러 마음**이다.
- 변형 수는 **비었어도 된다** — `enum Never {}` 는 값이 하나도 없는 타입이다([목록의 **06번 주제**](../06-functions-and-never-type/)의 `!` 와 이웃이다).

**금지 사례.**

```text
// ① 데이터 변형이 있는데 as 로 정수를 꺼낸다 — E0605
enum Mixed { Zero, One(u32) }
let n = Mixed::Zero as i32;

// ② 판별값 + 데이터 변형을 repr 없이 섞는다 — E0732
enum Bad { Zero = 0, One(u32) }

// ③ 없는 칸을 준다 — E0559
enum Conn { Connected { id: u32 } }
let c = Conn::Connected { id: 1, error: String::new() };

// ④ Copy 인데 String 이 든 변형이 있다 — E0204
#[derive(Clone, Copy)]
enum P { N(u32), T(String) }

// ⑤ 크기를 못 정한다 — E0072
enum Tree { Leaf(i32), Node(Tree, Tree) }
```

## 어디서 틀리나

| 자리 | 증상 | 진짜 이유 |
|---|---|---|
| **변형을 타입으로 쓰기** | `fn f(x: Message::Quit)` 가 안 된다 | 변형은 **값**이지 타입이 아니다. 인자 타입은 `Message` 다 |
| **`as` 로 판별값 꺼내기** | E0605 | **열거형 전체**가 단위 변형뿐이어야 한다. 짐 실은 변형 하나가 전부를 막는다 |
| **판별값 + 데이터 섞기** | E0732 | `#[repr(u8)]` 이 필요하다. 붙여도 `as` 는 여전히 막힌다 |
| **`Copy` 파생** | E0204 | **모든 변형의 모든 칸**이 `Copy` 여야 한다 |
| **`Default` 파생** | E0665 | 어느 변형이 기본인지 `#[default]` 로 찍어야 한다(1.62+) |
| **재귀 타입** | E0072 + E0391 | 크기가 안 정해진다. `Box` 로 한 칸 건너뛴다 |
| ★ **`Option` 이 공짜라고 믿기** | `Option<u32>` 가 8바이트 | **니치가 있을 때만** 공짜다. 정수·부동소수점은 태그를 따로 문다((7)) |
| ★ **`size_of` 를 언어 보장으로 읽기** | 다른 판에서 값이 다를 수 있다 | `repr` 을 안 붙인 배치는 **구현 세부**다(아래 절) |
| ★ **`use Enum::*` 를 습관으로 쓰기** | 변형 이름이 지역 변수와 충돌 | 다음 주제의 E0170 사고로 이어진다(18번 (5)) |

## 구현 세부사항 대 언어 보장

★ 이 절이 이 주제에서 특히 무겁다 — **크기와 배치는 대부분 보장이 아니다.**

| 사실 | 누가 보장하나 |
|---|---|
| 변형 셋(단위·튜플·구조체)의 **문법과 의미** | **언어 보장** — Reference 의 Enumerations |
| 단위 변형만 있는 열거형의 **판별값과 `as`** | **언어 보장** — 명시한 값·없으면 0부터 1씩 |
| `#[repr(u8)]`·`#[repr(C)]` 를 붙였을 때의 배치 | **언어 보장** — Reference 의 Type layout |
| `Option<&T>`·`Option<Box<T>>` 가 `&T`·`Box<T>` **와 같은 크기** | ★ **보장이다** — std 문서가 `Option` 에 대해 널 포인터 최적화를 명시한다 |
| `Option<bool>` 이 **1바이트**, `None` 이 **2** | ★★ **이 판의 관찰이다** — 니치 선택 규칙은 명세에 없다 |
| `Option<Option<Option<bool>>>` 이 1바이트 | ★★ **이 판의 관찰** |
| `Never2 { A(u32), B(u32) }` 가 8바이트 | ★★ **이 판의 관찰** — `repr` 없는 배치는 컴파일러 마음이다 |
| `Status { Ok = 200, … }` 가 2바이트 | ★ **관찰** — 판별값을 담을 만한 크기를 고르지만 어느 정수형인지는 고정이 아니다 |
| `std::mem::discriminant` 로 변형을 비교할 수 있다 | **언어 보장**(std 계약) — 단 그 **값 자체**는 보장이 없다 |

★ **읽는 법 하나** — 「같은 크기다」를 근거로 쓰고 싶으면 `Option<&T>`·`Option<Box<T>>` 처럼
**std 가 문서로 약속한 것**만 쓴다. 그 밖의 숫자는 **내 머신에서 그랬다**로 적는다.

## 언제 쓰고 언제 안 쓰나

**쓴다.**

- **상태가 유한하고 서로 배타적일 때** — 연결 상태·요청 결과·파싱 토큰.
- **「이 플래그가 참이면 저 필드가 반드시 있다」는 주석을 쓰고 있을 때** — 그 주석이 열거형이다((3)).
- **변형마다 짐이 다를 때** — 다른 언어라면 상속 계층이나 태그 붙은 구조체를 썼을 자리.
- **외부 규약과 숫자를 맞출 때** — 단위 변형 + 판별값((4)).

**안 쓴다.**

- **변형이 계속 늘고 남이 추가해야 할 때** — 그때는 트레이트가 맞다([목록의 **33번 주제**](../33-dyn-trait-objects-and-object-safety/)).
  열거형은 **닫힌 집합**이고, 그 닫힘이 다음 주제의 완전성 검사를 만든다.
- **변형 하나만 유독 클 때** — 봉투가 제일 큰 짐에 맞춰지므로 **전부가 커진다**.
  그때는 그 변형만 `Box` 로 감싼다.
- **그냥 켜짐/꺼짐일 때** — `bool` 이면 된다. 다만 `bool` **두 개 이상**이면 다시 열거형을 생각한다.

## 핵심 문장

1. **열거형은 「또는」이고 구조체는 「그리고」다.** 가짓수가 곱해지지 않고 더해진다.
2. **변형은 타입이 아니라 값이다.** `Message::Quit` 의 타입은 `Message` 다.
3. **불가능한 상태를 지우는 도구다** — 적을 자리 자체가 없어져 E0559 로 막힌다.
4. **`as` 로 판별값을 꺼내는 것은 열거형 전체가 단위 변형뿐일 때만** 된다(E0605).
5. **`Option<T>` 의 비용은 `T` 에 달렸다** — 니치가 있으면 0바이트, 없으면 태그 + 정렬만큼이다.
6. **`Option`·`Result` 는 언어 기능이 아니라 `enum` 선언**이다. 내가 똑같이 만들 수 있다.

## 관련 자료

- [**16번 주제**](../16-structs-impl-and-associated-functions/) — `impl`·연관 함수·`Self` 의 **정본**. 여기서는 그 문법을 그대로 쓸 뿐이다.
- [**09번 주제**](../09-copy-clone-and-drop/) — `Copy` 파생이 거부되는 이유(E0204)의 뿌리. 여기는 **열거형에서 어떻게 나타나나**까지.
- [**08번 주제**](../08-ownership-and-move/) — 변형에서 값을 꺼낼 때의 이동. 여기는 **선언**까지, 꺼내기는 18번.
- [목록의 **18번 주제**](../18-match-and-exhaustiveness/) — `match` 와 완전성 검사. **이 주제의 값이 거기서 회수된다.**
- [목록의 **21번 주제**](../21-option-and-combinators/)·**22번 주제** — `Option`·`Result` 의 **메서드 표면**. 여기는 **그것이 enum 이라는 사실**까지.
- [목록의 **40번 주제**](../40-box-recursive-types-and-dyn/) — `Box` 와 재귀 타입. 여기는 **왜 막히나**까지, 푸는 법의 정본은 거기다.
- [목록의 **27번 주제**](../27-derive-macros-debug-clone-partialeq-default-hash/) — `derive` 매크로가 거는 조건 전수. 여기는 **열거형에서 걸리는 둘**만.
- [`foundations/memory-management`](../../../../memory-management/) — 스택·힙·정렬 일반. 여기는 **열거형 봉투의 크기**로 좁혔다.

## 용어 풀이

| 말 | 뜻 |
|---|---|
| **열거형(enum)** | 여러 변형 중 정확히 하나인 값을 담는 타입. 합 타입 |
| **변형(variant)** | 열거형이 가질 수 있는 한 모양. 단위·튜플·구조체 |
| **단위 변형** | 짐이 없는 변형. `Quit` |
| **튜플 변형** | 칸에 번호가 붙은 변형. `Move(i32, i32)` |
| **구조체 변형** | 칸에 이름이 붙은 변형. `Write { text, bold }` |
| **판별자(discriminant)** | 「지금 어느 변형인가」를 나타내는 값. `std::mem::discriminant` 로 비교한다 |
| **판별값** | C 스타일 열거형에서 변형에 붙인 정수. `as` 로 꺼낸다 |
| **니치(niche)** | 그 타입이 절대 갖지 않는 비트 패턴. `&T` 의 널, `NonZeroU8` 의 0 |
| **니치 최적화** | 그 빈 무늬를 다른 변형의 표식으로 재활용하는 것 |
| **널 포인터 최적화** | 니치 최적화의 특수한 경우 — `Option<&T>` 의 `None` 이 널이 되는 것 |
| **합 타입(sum type)** | 가짓수가 더해지는 타입. 곱해지는 쪽(구조체)은 곱 타입 |
| **`#[non_exhaustive]`** | 「변형이 더 늘 수 있다」고 남의 크레이트에 알리는 표시. 18번 주제에서 다룬다 |

## 더 들어가면

- **`#[repr(u8)]` 을 붙인 열거형은 C 와 ABI 가 맞는다** — FFI 에서 쓴다. 이 목록 밖이다.
- **`enum` 에 제네릭을 걸 수 있다** — `MyOption<T>` 가 그 예다((6)). 경계 문법은 [목록의 **31번 주제**](../31-generics-trait-bounds-where-and-monomorphization/).
- **변형이 하나뿐인 열거형**은 구조체와 같은 일을 한다. 그런데도 쓰는 이유는
  **나중에 변형을 늘릴 자리를 열어 두려는 것**이다 — 그 설계의 대가는 18번 주제의 `#[non_exhaustive]` 에서 본다.
- **크기를 줄이는 관용구** — 큰 변형만 `Box` 로 싸기, 판별값을 `#[repr(u8)]` 로 줄이기.
  둘 다 **재어 보고** 한다. 재는 법은 (7)에 있다.
