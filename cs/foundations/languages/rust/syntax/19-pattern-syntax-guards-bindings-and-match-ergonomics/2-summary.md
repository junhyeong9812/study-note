# rust/syntax/19 — 패턴 문법 전수 — 가드·`@`·or 패턴·구조 분해·매치 인체공학 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [The Rust Reference — Patterns](https://doc.rust-lang.org/reference/patterns.html) ·
> [Reference — `match` expressions](https://doc.rust-lang.org/reference/expressions/match-expr.html) ·
> [Reference — Slice patterns](https://doc.rust-lang.org/reference/patterns.html#slice-patterns) ·
> [Reference — Binding modes](https://doc.rust-lang.org/reference/patterns.html#binding-modes).
> ★ `rustc --explain E0004` / `E0308` / `E0408` / `E0381` / `E0507` 는 **확인용으로만 열었고 본문에 옮기지 않았다.**
> **실행 검증** — 이 문서의 모든 출력·에러·경고는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 받은 것이다. **손으로 옮겨 적은 출력은 한 줄도 없다.**\
> ★★ **`rustc ex.rs` 만 쓰면 에디션 2015 다.** 이 갈래는 `--edition 2021` 을 반드시 붙인다.
> **버전** — 가드·`@`·구조 분해는 1.0.0부터다. **매치 인체공학**(RFC 2005)은 **1.26.0**부터이고 **에디션과 무관**하다.\
> **슬라이스 패턴의 `rest @ ..`** 는 **1.42.0**부터, **중첩 or 패턴**(`Some(1 | 3)`)은 **1.53.0**부터,\
> **`@` 가 or 패턴을 감싸는 것**(`v @ (1 | 3)`)은 **1.65.0**부터다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | 패닉 첫 줄 `thread 'main' (…)` 괄호 안의 OS 스레드 id | 실행마다 커널이 주는 번호다 |
| **흔들린다** | `0x…` 주소 | 실행마다 다르다 |
| 안 흔들린다 | `파일:줄:칸` · 에러 번호 · 제목 · `= note:` · `help:` 본문 | 같은 rustc 판에서 고정이다 |
| 안 흔들린다 | ★ **에러가 찍어 주는 바인딩의 타입**(`&String`·`&mut String`·`String`) | 이 주제의 핵심 근거다 |
| 안 흔들린다 | 종료 코드(`0` · 컴파일 실패 `1`) | 고정이다 |

## 한눈에 — 쉽게 말하면

**패턴은 「모양을 대 보고, 맞으면 안쪽을 이름으로 꺼내는」 것이다.**

`match` 만의 문법이 아니다. `let`·함수 인자·`for`·클로저 인자·`if let`·`while let` 이 **전부 패턴을 받는다**((7)).

| 비유 | 실체 |
|---|---|
| **모양 자**를 대 본다 | 패턴 매칭 — 맞나 안 맞나 |
| 자에 난 **구멍으로 안쪽을 집어낸다** | 바인딩 — `Some(s)` 의 `s` |
| 자를 대 본 뒤 **한 번 더 재 본다** | **가드** — `if x > limit` |
| 집어내면서 **통째로도 하나 챙긴다** | **`@` 바인딩** — `n @ 1..=9` |
| 자 여러 개를 **한 칸에 겹쳐 댄다** | **or 패턴** — `Key::Up \| Key::Down` |
| 자 안에 **또 자가 들어 있다** | **중첩 구조 분해** — `Seg(Line { from: Point { x, .. }, .. })` |
| 줄 선 사람 중 **맨 앞과 맨 뒤만** 본다 | **슬라이스 패턴** — `[first, .., last]` |
| ★ 상자를 **안 열고 들여다보면** 꺼낸 것도 「보기만 한 것」이 된다 | **매치 인체공학** — `&Option<String>` 을 `Some(s)` 로 받으면 `s` 는 `&String` |

- ★★ **이 주제의 값은 「`Some(s)` 의 `s` 가 무엇인가」** 하나다. 같은 글자인데 `String`·`&String`·`&mut String` 셋이 된다.
  그것을 **에러 메시지로 찍어** 증명한다((5)).
- ★★ **매치 인체공학이 빌림을 만든다** — 그래서 [**10번**](../10-borrowing-and-aliasing-rules/)·[**11번 주제**](../11-borrow-checker-rejections/)가 이 주제의 뒷배경이다.
- ★ **가드가 붙으면 완전성 검사가 포기한다**((2)) — 18번 주제의 안전망이 여기서 한 칸 약해진다.

```text
   대상 값의 「참조 한 겹」이 패턴을 통과하면 안쪽 이름에 그대로 옮겨 붙는다

   대상: &Option<String>          패턴: Some(s)
         │                              │
         └ & 가 한 겹 있다 ─────────────┘  패턴에는 & 가 없다
                     │
                     ▼  「기본 바인딩 모드」가 ref 로 바뀐다
                  s: &String        ← 이동이 아니라 빌림. 원본이 산다

   대상: &mut Option<String>       패턴: Some(s)  →  s: &mut String
   대상:      Option<String>       패턴: Some(s)  →  s:  String   ← 이동한다

   ★ 글자는 셋 다 `Some(s)` 로 똑같다. 갈리는 것은 「대상에 & 가 몇 겹 있나」다.
```

> **패턴(pattern)** — 값의 **모양**을 적은 것. 맞으면 안쪽을 이름에 묶는다.

> **바인딩(binding)** — 패턴이 이름에 값을 묶는 것. `Some(s)` 의 `s`.

> **반박 가능(refutable) / 불가(irrefutable)** — 안 맞을 수 있는 패턴 / 항상 맞는 패턴.\
> `let` 과 함수 인자는 **불가**한 패턴만 받는다. `match` 팔·`if let` 은 **가능**한 것도 받는다.

> **가드(guard)** — 패턴 뒤의 `if 식`. 패턴이 못 보는 **값들 사이의 관계**를 본다.

> **매치 인체공학(match ergonomics)** — 대상 값에 참조가 씌워져 있으면\
> 패턴에 `&`·`ref` 를 안 적어도 **바인딩이 알아서 참조가 되는** 규칙(1.26.0부터, 에디션 무관).

## 이 주제가 답하려는 질문

1. **패턴으로 무엇까지 할 수 있나** — 가드·`@`·or·중첩·슬라이스를 한 번에 본다.
2. **`Some(s)` 의 `s` 는 정확히 무슨 타입인가** — 그리고 그것을 **어떻게 증명하나**.
3. **패턴이 규칙을 어기는 자리는 어디인가** — or 패턴의 이름, 가드 안의 이동, 완전성 포기.

★ [**18번 주제**](../18-match-and-exhaustiveness/)가 「팔을 **빠짐없이** 적었나」였다면
여기는 「**한 팔 안에서 얼마나 정교하게** 적을 수 있나」다.

## 동작 방식

### (0) 이 주제가 쓰는 네 창

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| **일부러 던져서 받는 컴파일 에러** | 패턴이 어기는 규칙 — E0408·E0381·E0507 | [**11번 주제**](../11-borrow-checker-rejections/) |
| ★★ **`let _probe: () = s;` 로 바인딩 타입을 에러에 찍게 하기** | `s` 가 **`&String` 인가 `String` 인가** | ★ 이 주제의 고유 창 |
| **완전성 검사에게 물어보기** | 가드가 붙으면 **덮은 것으로 안 친다** | [**18번 주제**](../18-match-and-exhaustiveness/)에서 이어받았다 |
| **묶은 뒤 원본을 다시 읽어 보기** | 빌린 것인가 가져간 것인가 — 행동으로 | [**08번 주제**](../08-ownership-and-move/) |

★★ **두 번째 창이 이 주제의 본체다.** 타입은 눈에 안 보인다 — IDE 없이는 `s` 가 무엇인지 알 길이 없다.
**일부러 틀린 타입을 적으면 컴파일러가 실제 타입을 대신 찍어 준다.**
`let _probe: () = s;` 한 줄이면 `` expected `()`, found `&String` `` 이 나온다. 지어낼 수 없는 근거다.

### (1) 가드 — 패턴 뒤에 붙는 `if`

**언제 쓰나** — 패턴만으로는 못 보는 것을 볼 때. **값들 사이의 관계**와 **바깥 변수**가 대표다.

```text
===== 소스: ex.rs =====
// ex.rs
// 가드 — 패턴 뒤에 붙는 if. 패턴이 못 보는 「값들 사이의 관계」를 본다
fn kind(p: (i32, i32)) -> &'static str {
    match p {
        (x, y) if x == y => "대각선",
        (x, _) if x == 0 => "세로축",
        (_, y) if y == 0 => "가로축",
        _ => "그 밖",
    }
}

fn main() {
    for p in [(0, 0), (3, 3), (0, 5), (5, 0), (2, 7)] {
        println!("{:?} {}", p, kind(p));
    }
    // 가드는 「그 팔의 모든 갈래」에 걸린다 — or 패턴 전체를 덮는다
    let n = 6;
    println!("{}", match n { 4 | 6 | 8 if n > 5 => "5보다 큰 짝수", _ => "그 밖" });
    // 바깥 변수를 가드에서 읽을 수 있다 — 패턴 자리에서는 못 한다
    let limit = 5;
    println!("{}", match n { x if x > limit => "한계 초과", _ => "이내" });
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
(0, 0) 대각선
(3, 3) 대각선
(0, 5) 세로축
(5, 0) 가로축
(2, 7) 그 밖
5보다 큰 짝수
한계 초과
(종료 코드 0)
```

읽는 법.

- `(x, y) if x == y` — **두 칸의 관계**는 패턴으로 못 적는다. `(x, x)` 는 문법이 아니다.
- `4 | 6 | 8 if n > 5` — ★ **가드는 or 패턴 전체에 걸린다.** 마지막 갈래에만 걸리는 것이 아니다.
- `x if x > limit` — **바깥 변수 `limit` 을 가드에서 읽는다.** 패턴 자리에 `limit` 을 쓰면
  그것은 비교가 아니라 **새 변수 바인딩**이다(18번 (5)의 함정과 같은 뿌리).

### (2) ★ 가드가 붙으면 완전성 검사가 포기한다

**언제 쓰나** — 「전부 덮었는데 왜 에러지?」 하는 순간. **이 규칙이 답이다.**

```text
===== 소스: ex.rs =====
// ex.rs
// 가드가 붙으면 완전성 검사가 그 팔을 「덮은 것으로 치지 않는다」
fn sign(n: i32) -> &'static str {
    match n {
        x if x < 0 => "음수",
        x if x == 0 => "영",
        x if x > 0 => "양수",
    }
}

fn flag(b: bool) -> &'static str {
    match b {
        true => "참",
        x if !x => "거짓",
    }
}

fn main() {
    println!("{} {}", sign(-1), flag(false));
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0004]: non-exhaustive patterns: `i32::MIN..=i32::MAX` not covered
 --> ex.rs:4:11
  |
4 |     match n {
  |           ^ pattern `i32::MIN..=i32::MAX` not covered
  |
  = note: the matched value is of type `i32`
  = note: match arms with guards don't count towards exhaustivity
help: ensure that all possible cases are being handled by adding a match arm with a wildcard pattern or an explicit pattern as shown
  |
7 ~         x if x > 0 => "양수",
8 ~         i32::MIN..=i32::MAX => todo!(),
  |

error[E0004]: non-exhaustive patterns: `false` not covered
  --> ex.rs:12:11
   |
12 |     match b {
   |           ^ pattern `false` not covered
   |
   = note: the matched value is of type `bool`
help: ensure that all possible cases are being handled by adding a match arm with a wildcard pattern or an explicit pattern as shown
   |
14 ~         x if !x => "거짓",
15 ~         false => todo!(),
   |

error: aborting due to 2 previous errors

For more information about this error, try `rustc --explain E0004`.
(종료 코드 1)
```

읽는 법.

- `x < 0` · `x == 0` · `x > 0` 셋이 **사람 눈에는 `i32` 전체**인데 **E0004** 가 난다.
  진단이 이유를 한 줄로 말한다 — `= note: match arms with guards don't count towards exhaustivity`.
- 두 번째 예는 더 선명하다. `true` 와 `x if !x` 로 `bool` 두 값을 덮었는데 **`false` not covered** 다.
- ★★ **왜 그런가** — 가드는 **임의의 식**이라 컴파일러가 참인지 판정할 수 없다.
  `x > 0` 이 언제 참인지 계산하려면 컴파일러가 정리 증명기가 돼야 한다. **모르면 안 센다**가 안전한 쪽이다.
- 처방은 하나다 — **마지막 팔의 가드를 떼거나 `_` 를 둔다.**

### (3) `@` 바인딩과 or 패턴

**언제 쓰나** — `@` 는 「거르면서 통째로도 챙길 때」, or 패턴은 「여러 모양을 한 팔로 묶을 때」.

```text
===== 소스: ex.rs =====
// ex.rs
// @ 바인딩 — 「거른 값을 이름으로도 받는다」. 거름과 묶음을 동시에
#[derive(Debug)]
enum Msg { Id(u32), Name(String) }

fn main() {
    for m in [Msg::Id(3), Msg::Id(42), Msg::Id(500), Msg::Name(String::from("가"))] {
        let s = match m {
            Msg::Id(n @ 1..=9) => format!("한 자리 id {}", n),
            Msg::Id(n @ 10..=99) => format!("두 자리 id {}", n),
            Msg::Id(n) => format!("큰 id {}", n),
            Msg::Name(ref s) => format!("이름 {}", s),
        };
        println!("{}", s);
    }
    // 구조체 변형 전체를 @ 로 받으면서 안쪽도 본다
    #[derive(Debug)]
    struct P { x: i32, y: i32 }
    let p = P { x: 3, y: 9 };
    match p {
        P { x: x @ 1..=5, y } => println!("x={} 가 1\u{7e}5 이고 y={}", x, y),
        P { x, y } => println!("그 밖 {} {}", x, y),
    }
    // @ 는 or 패턴도 감쌀 수 있다 (1.65부터)
    let n = 7;
    match n {
        v @ (1 | 3 | 5 | 7 | 9) => println!("홀수 {}", v),
        v => println!("그 밖 {}", v),
    }
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
한 자리 id 3
두 자리 id 42
큰 id 500
이름 가
x=3 가 1~5 이고 y=9
홀수 7
(종료 코드 0)
```

읽는 법.

- `Msg::Id(n @ 1..=9)` — **범위로 거르면서** 그 값을 `n` 에 묶는다. `@` 가 없으면 둘 중 하나만 된다.
- `P { x: x @ 1..=5, y }` — 구조체 칸에도 붙는다.
- `v @ (1 | 3 | 5 | 7 | 9)` — ★ **`@` 가 or 패턴을 감싸는 것은 1.65.0부터**다.
- `Msg::Name(ref s)` — 여기서는 `m` 이 값이라 `ref` 가 필요했다((6)에서 다룬다).

```text
===== 소스: ex.rs =====
// ex.rs
// or 패턴 — 어느 자리에 쓸 수 있나. 2021 에서는 중첩 자리에도 쓴다
#[derive(Debug)]
enum Key { Up, Down, Left, Right, Esc }

fn axis(k: &Key) -> &'static str {
    match k {
        Key::Up | Key::Down => "세로",
        Key::Left | Key::Right => "가로",
        Key::Esc => "없음",
    }
}

fn main() {
    for k in [Key::Up, Key::Down, Key::Left, Key::Right, Key::Esc] { println!("{:?} {}", k, axis(&k)); }
    // 중첩 자리 — Some(1 | 3) 처럼 안쪽에 쓴다
    for o in [Some(1), Some(2), Some(3), None] {
        println!("{:?} {}", o, match o { Some(1 | 3) => "홀수 후보", Some(_) => "그 밖의 수", None => "없음" });
    }
    // 맨 앞의 | 는 써도 되고 안 써도 된다
    let n = 2;
    println!("{}", match n { | 1 | 2 => "하나나 둘", _ => "그 밖" });
    // let 과 함수 인자 자리에서는? — 거부되지 않는 것만 쓸 수 있다
    let (1 | 2) = n else { unreachable!() };
    println!("let 에서도 or 패턴이 된다");
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
Up 세로
Down 세로
Left 가로
Right 가로
Esc 없음
Some(1) 홀수 후보
Some(2) 그 밖의 수
Some(3) 홀수 후보
None 없음
하나나 둘
let 에서도 or 패턴이 된다
(종료 코드 0)
```

- `Key::Up | Key::Down` — 같은 팔에 여러 모양.
- `Some(1 | 3)` — ★ **중첩 자리의 or 패턴은 1.53.0부터**다. 그 전에는 `Some(1) | Some(3)` 이라야 했다.
- `| 1 | 2` — **맨 앞의 `|`** 는 써도 되고 안 써도 된다(여러 줄로 늘어놓을 때 모양이 는다).
- `let (1 | 2) = n else { … };` — ★ **`let` 자리에서도 or 패턴이 된다.**
  단 `let` 은 **반박 불가** 패턴만 받으므로 `else` 가 필요하다([목록의 **20번 주제**](../20-if-let-while-let-let-else-and-let-chains/)).

★★ **or 패턴에는 규칙이 둘 있다 — 이름이 같아야 하고, 타입도 같아야 한다.**

```text
===== 소스: ex.rs =====
// ex.rs
// or 패턴의 규칙 — 모든 갈래가 「같은 이름들」을 묶어야 한다
enum Shape {
    Circle { r: f64 },
    Square { side: f64 },
    Rect { w: f64, h: f64 },
}

fn main() {
    let s = Shape::Rect { w: 2.0, h: 3.0 };
    let x = match s {
        Shape::Circle { r } | Shape::Square { side } => r,
        Shape::Rect { w, h } => w * h,
    };
    println!("{}", x);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0408]: variable `side` is not bound in all patterns
  --> ex.rs:12:9
   |
12 |         Shape::Circle { r } | Shape::Square { side } => r,
   |         ^^^^^^^^^^^^^^^^^^^                   ---- variable not in all patterns
   |         |
   |         pattern doesn't bind `side`

error[E0408]: variable `r` is not bound in all patterns
  --> ex.rs:12:31
   |
12 |         Shape::Circle { r } | Shape::Square { side } => r,
   |                         -     ^^^^^^^^^^^^^^^^^^^^^^ pattern doesn't bind `r`
   |                         |
   |                         variable not in all patterns

error[E0381]: used binding `r` is possibly-uninitialized
  --> ex.rs:12:57
   |
12 |         Shape::Circle { r } | Shape::Square { side } => r,
   |                         -                               ^ `r` used here but it is possibly-uninitialized
   |                         |
   |                         binding initialized here in some conditions
   |                         binding declared here but left uninitialized

warning: unused variable: `side`
  --> ex.rs:12:47
   |
12 |         Shape::Circle { r } | Shape::Square { side } => r,
   |                                               ^^^^ help: try ignoring the field: `side: _`
   |
   = note: `#[warn(unused_variables)]` (part of `#[warn(unused)]`) on by default

error: aborting due to 3 previous errors; 1 warning emitted

Some errors have detailed explanations: E0381, E0408.
For more information about an error, try `rustc --explain E0381`.
(종료 코드 1)
```

- **E0408** 이 **두 번** 난다 — `side is not bound in all patterns` 와 `r is not bound in all patterns`.
  ★ **양쪽에서 한 번씩** 본다. 「`Circle` 이 `side` 를 안 묶는다」와 「`Square` 가 `r` 을 안 묶는다」다.
- **E0381**(``used binding `r` is possibly-uninitialized``)이 딸려 온다 —
  팔의 몸통이 `r` 을 쓰는데 `Square` 로 들어오면 `r` 이 **안 채워진 채**이기 때문이다.
  진단이 `binding initialized here in some conditions` 로 그 사정을 말한다.

**이름을 맞춰도 타입이 갈리면 다른 번호가 난다.**

```text
===== 소스: ex.rs =====
// ex.rs
// 이름은 맞췄는데 타입이 갈리면 — 또 다른 번호가 나온다
enum V {
    A(u32),
    B(String),
}

fn main() {
    let v = V::A(1);
    match v {
        V::A(x) | V::B(x) => println!("{:?}", x),
    }
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0308]: mismatched types
  --> ex.rs:11:24
   |
10 |     match v {
   |           - this expression has type `V`
11 |         V::A(x) | V::B(x) => println!("{:?}", x),
   |              -         ^ expected `u32`, found `String`
   |              |
   |              first introduced with type `u32` here
   |
   = note: in the same arm, a binding must have the same type in all alternatives

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0308`.
(종료 코드 1)
```

- **E0308** — `` expected `u32`, found `String` ``.
  `= note: in the same arm, a binding must have the same type in all alternatives` 가 규칙을 그대로 적는다.
- ★ 진단이 ``first introduced with type `u32` here`` 로 **먼저 나온 갈래가 타입을 정한다**는 것도 말해 준다.

### (4) 구조 분해와 슬라이스 패턴

**언제 쓰나** — 중첩된 값에서 **깊은 곳 한둘만** 필요할 때. 그리고 연속된 것의 **앞뒤**를 볼 때.

```text
===== 소스: ex.rs =====
// ex.rs
// 구조 분해 — 구조체·열거형·튜플이 몇 겹이든 한 패턴으로 내려간다
#[derive(Debug)]
struct Point { x: i32, y: i32 }
#[derive(Debug)]
struct Line { from: Point, to: Point, label: Option<String> }

#[derive(Debug)]
enum Shape { Seg(Line), Dot(Point) }

fn read(s: &Shape) -> String {
    match s {
        // 세 겹을 한 줄에 — enum → struct → struct/Option
        Shape::Seg(Line { from: Point { x: x1, y: y1 },
                          to: Point { x: x2, y: y2 },
                          label: Some(name) }) =>
            format!("이름 있는 선 {} ({},{})\u{2192}({},{})", name, x1, y1, x2, y2),
        Shape::Seg(Line { from: Point { x: x1, .. }, label: None, .. }) =>
            format!("이름 없는 선, 시작 x={}", x1),
        Shape::Dot(Point { x: 0, y: 0 }) => String::from("원점"),
        Shape::Dot(Point { x, y }) => format!("점 ({},{})", x, y),
    }
}

fn main() {
    let a = Shape::Seg(Line { from: Point { x: 0, y: 0 }, to: Point { x: 3, y: 4 },
                              label: Some(String::from("빗변")) });
    let b = Shape::Seg(Line { from: Point { x: 7, y: 1 }, to: Point { x: 9, y: 1 }, label: None });
    let c = Shape::Dot(Point { x: 0, y: 0 });
    let d = Shape::Dot(Point { x: 2, y: 5 });
    for s in [&a, &b, &c, &d] { println!("{}", read(s)); }

    // let 도 패턴이다 — 함수 인자·for 도 마찬가지
    let Line { from: Point { x, .. }, .. } = Line {
        from: Point { x: 11, y: 12 }, to: Point { x: 0, y: 0 }, label: None };
    println!("let 으로 뽑은 x={}", x);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
이름 있는 선 빗변 (0,0)→(3,4)
이름 없는 선, 시작 x=7
원점
점 (2,5)
let 으로 뽑은 x=11
(종료 코드 0)
```

읽는 법.

- 패턴 하나가 **열거형 → 구조체 → 구조체·`Option`** 세 겹을 내려간다.
- `label: Some(name)` — **칸의 값까지 패턴으로** 건다. 그래서 「이름 있는 선」과 「이름 없는 선」이 **다른 팔**이 된다.
- `Point { x: x1, .. }` — **`..` 로 나머지 칸을 통째로 건너뛴다.** `_` 는 한 칸, `..` 는 여럿이다.
- `Point { x: 0, y: 0 }` — **값을 그대로 적으면 그 값일 때만** 맞는다.
- 마지막 `let Line { … } = …;` 이 **`let` 도 패턴**임을 보인다.

```text
===== 소스: ex.rs =====
// ex.rs
// 슬라이스 패턴 — 앞·뒤·가운데를 한 번에 짚는다
fn shape(v: &[i32]) -> String {
    match v {
        [] => String::from("빈 것"),
        [only] => format!("하나 {}", only),
        [a, b] => format!("둘 {} {}", a, b),
        [first, .., last] => format!("셋 이상 처음 {} 끝 {}", first, last),
    }
}

fn head_tail(v: &[i32]) -> String {
    match v {
        [head, tail @ ..] => format!("머리 {} 꼬리 {:?}(길이 {})", head, tail, tail.len()),
        [] => String::from("빈 것"),
    }
}

fn main() {
    for v in [vec![], vec![1], vec![1, 2], vec![1, 2, 3], vec![1, 2, 3, 4, 5]] {
        println!("{:?} | {} | {}", v, shape(&v), head_tail(&v));
    }
    // 고정 길이 배열은 길이를 알아서 `[a, b, c]` 하나로 완전하다
    let arr = [10, 20, 30];
    let [a, b, c] = arr;
    println!("배열 분해 {} {} {}", a, b, c);
    // 문자열 바이트에도 쓴다 — 15번 주제의 &[u8]
    let bytes = "AB가".as_bytes();
    println!("{}", match bytes {
        [b'A', rest @ ..] => format!("A 로 시작, 나머지 {}바이트", rest.len()),
        _ => String::from("그 밖"),
    });
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
[] | 빈 것 | 빈 것
[1] | 하나 1 | 머리 1 꼬리 [](길이 0)
[1, 2] | 둘 1 2 | 머리 1 꼬리 [2](길이 1)
[1, 2, 3] | 셋 이상 처음 1 끝 3 | 머리 1 꼬리 [2, 3](길이 2)
[1, 2, 3, 4, 5] | 셋 이상 처음 1 끝 5 | 머리 1 꼬리 [2, 3, 4, 5](길이 4)
배열 분해 10 20 30
A 로 시작, 나머지 4바이트
(종료 코드 0)
```

- `[]` · `[only]` · `[a, b]` · `[first, .., last]` — **길이별로** 갈린다.
- `[head, tail @ ..]` — ★ **`rest @ ..` 는 1.42.0부터**다. 「나머지 전부를 슬라이스로」 묶는다.
- **고정 길이 배열**(`[i32; 3]`)은 길이를 컴파일러가 아니까 `[a, b, c]` 하나로 **완전**하다.
- `[b'A', rest @ ..]` — 바이트 슬라이스에도 쓴다([**15번 주제**](../15-slices-ranges-and-utf8-boundaries/)).

```text
   슬라이스 패턴이 짚는 자리

     [10, 20, 30, 40, 50]
      │    └─── .. ───┘ │
      └ first           └ last          ← [first, .., last]
        가운데는 「있다는 것만」 보고 안 묶는다

     [10, 20, 30, 40, 50]
      │   └──────┬──────┘
      └ head     └ tail                 ← [head, tail @ ..]
                    슬라이스 하나로 묶인다(길이 4)

     [10, 20, 30]  →  [a, b, c]         ← 고정 길이 배열은 이 하나로 완전
     &[i32]        →  []·[a]·[a,b]·[a,..,b] 를 다 덮어야 완전

   ★ `..` 는 한 패턴에 한 번만. 두 번 쓰면 어디서 끊을지 정해지지 않는다
```

**길이를 모르는 슬라이스는 「몇 개짜리」를 다 덮어야 한다.**

```text
===== 소스: ex.rs =====
// ex.rs
// 길이를 모르는 슬라이스는 「몇 개짜리」를 다 덮어야 한다
fn shape(v: &[i32]) -> String {
    match v {
        [] => String::from("빈 것"),
        [only] => format!("하나 {}", only),
        [a, b] => format!("둘 {} {}", a, b),
    }
}

fn arr(a: [i32; 3]) -> i32 {
    match a {
        [x, y, z] => x + y + z,
    }
}

fn main() {
    println!("{} {}", shape(&[1, 2, 3]), arr([1, 2, 3]));
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0004]: non-exhaustive patterns: `&[_, _, _, ..]` not covered
 --> ex.rs:4:11
  |
4 |     match v {
  |           ^ pattern `&[_, _, _, ..]` not covered
  |
  = note: the matched value is of type `&[i32]`
help: ensure that all possible cases are being handled by adding a match arm with a wildcard pattern or an explicit pattern as shown
  |
7 ~         [a, b] => format!("둘 {} {}", a, b),
8 ~         &[_, _, _, ..] => todo!(),
  |

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0004`.
(종료 코드 1)
```

- **`&[_, _, _, ..]` not covered** — 「셋 이상」이 통째로 안 덮였다고 짚는다.
- 아래쪽 `[i32; 3]` 은 **에러가 안 났다** — 길이가 타입에 있어 `[x, y, z]` 하나로 완전하기 때문이다.

### (5) ★★ 매치 인체공학 — `Some(s)` 의 `s` 는 무엇인가

**언제 쓰나** — 항상. 이것을 모르면 **왜 어떨 때는 원본이 살고 어떨 때는 죽는지** 설명이 안 된다.

**증명하는 법 — 일부러 틀린 타입을 적어 컴파일러가 실제 타입을 찍게 한다.**

```text
===== 소스: ex.rs =====
// ex.rs
// 매치 인체공학 — &Option<String> 을 Some(s) 로 받으면 s 는 무엇인가
// let 로 받으면서 일부러 타입을 틀리게 적어 컴파일러가 실제 타입을 찍게 한다
fn main() {
    let owned: Option<String> = Some(String::from("가나"));

    let r: &Option<String> = &owned;
    match r {
        Some(s) => { let _probe: () = s; }
        None => {}
    }

    let mut owned2: Option<String> = Some(String::from("다라"));
    let m: &mut Option<String> = &mut owned2;
    match m {
        Some(s) => { let _probe: () = s; }
        None => {}
    }

    match owned2 {
        Some(s) => { let _probe: () = s; }
        None => {}
    }
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0308]: mismatched types
 --> ex.rs:9:39
  |
9 |         Some(s) => { let _probe: () = s; }
  |                                  --   ^ expected `()`, found `&String`
  |                                  |
  |                                  expected due to this

error[E0308]: mismatched types
  --> ex.rs:16:39
   |
16 |         Some(s) => { let _probe: () = s; }
   |                                  --   ^ expected `()`, found `&mut String`
   |                                  |
   |                                  expected due to this

error[E0308]: mismatched types
  --> ex.rs:21:39
   |
21 |         Some(s) => { let _probe: () = s; }
   |                                  --   ^ expected `()`, found `String`
   |                                  |
   |                                  expected due to this

error: aborting due to 3 previous errors

For more information about this error, try `rustc --explain E0308`.
(종료 코드 1)
```

읽는 법.

- ★★★ **글자가 셋 다 `Some(s)` 인데 타입이 셋 다 다르다.**

| 대상 값 | 패턴 | `s` 의 타입 | 원본은? |
|---|---|---|---|
| `&Option<String>` | `Some(s)` | **`&String`** | 산다(빌림) |
| `&mut Option<String>` | `Some(s)` | **`&mut String`** | 산다(가변 빌림) |
| `Option<String>` | `Some(s)` | **`String`** | 죽는다(이동) |

- 규칙은 한 줄이다 — **대상 값에 참조가 씌워져 있으면 그 참조가 안쪽 바인딩에 그대로 옮겨 붙는다.**
  이것을 **기본 바인딩 모드**가 `ref`/`ref mut` 로 바뀐다고 말한다.
- ★ `let _probe: () = s;` 는 **타입을 캐는 도구**다. `()` 는 어떤 것과도 안 맞으니
  진단이 `` expected `()`, found `…` `` 로 **실제 타입을 대신 적어 준다.**

**찍힌 타입대로 실제로 써 본다.**

```text
===== 소스: ex.rs =====
// ex.rs
// 찍힌 타입대로 써 보면 — &T 는 읽기, &mut T 는 고치기, T 는 가져오기
fn main() {
    let owned: Option<String> = Some(String::from("가나"));
    let r: &Option<String> = &owned;
    match r {
        Some(s) => println!("① {} 길이 {} (s: &String — 읽기만)", s, s.len()),
        None => println!("① 없음"),
    }
    println!("① 뒤 원본 {:?}", owned);

    let mut owned2: Option<String> = Some(String::from("다라"));
    match &mut owned2 {
        Some(s) => { s.push_str("마"); println!("② 고쳤다 {} (s: &mut String)", s); }
        None => println!("② 없음"),
    }
    println!("② 뒤 원본 {:?}", owned2);

    match owned2 {
        Some(s) => println!("③ 가져왔다 {} (s: String)", s),
        None => println!("③ 없음"),
    }
    // ③ 뒤에는 owned2 를 못 읽는다 — 18번 주제의 「묶인 값의 이동」

    // & 를 패턴에 직접 적으면 「벗겨서」 받는다 — 그때는 T 가 Copy 여야 한다
    let nums = vec![1, 2, 3];
    let total: i32 = nums.iter().map(|&n| n).sum();       // n: i32
    let total2: i32 = nums.iter().map(|n| *n).sum();      // n: &i32
    println!("④ {} {}", total, total2);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
① 가나 길이 6 (s: &String — 읽기만)
① 뒤 원본 Some("가나")
② 고쳤다 다라마 (s: &mut String)
② 뒤 원본 Some("다라마")
③ 가져왔다 다라마 (s: String)
④ 6 6
(종료 코드 0)
```

- ① `&String` 이라 **읽기만** 된다. 매치 뒤에도 원본이 산다.
- ② `&mut String` 이라 **고칠 수 있다.** `push_str` 이 먹고 원본이 바뀐다.
- ③ `String` 이라 **가져간다.** 그 뒤로 `owned2` 는 못 읽는다(18번 (5)의 E0382).
- ④ ★ **패턴에 `&` 를 직접 적으면 「벗겨서」 받는다** — `|&n|` 의 `n` 은 `i32` 다.
  그러려면 안쪽이 `Copy` 여야 한다. `|n| *n` 과 결과가 같고, 어디서 벗기느냐만 다르다.

### (6) `ref` / `ref mut` — 왜 거의 안 쓰이게 됐나

**언제 쓰나** — 옛 코드를 읽을 때. 그리고 **`let` 에서 일부만 빌려 잡을 때**.

```text
===== 소스: ex.rs =====
// ex.rs
// ref / ref mut — 인체공학이 생기기 전의 도구. 지금은 같은 일을 하는 두 길이 된다
fn main() {
    let owned: Option<String> = Some(String::from("가나"));

    // 옛 방식 — 값을 매치하면서 팔에서 빌린다
    match owned {
        Some(ref s) => println!("① ref {} ({}바이트)", s, s.len()),
        None => println!("① 없음"),
    }
    println!("① 뒤 원본 {:?}", owned);

    // 지금 방식 — 참조를 매치한다. 같은 결과다
    match &owned {
        Some(s) => println!("② 인체공학 {} ({}바이트)", s, s.len()),
        None => println!("② 없음"),
    }
    println!("② 뒤 원본 {:?}", owned);

    // ref mut 도 마찬가지로 &mut 매치로 갈음된다
    let mut v = Some(String::from("다라"));
    match v {
        Some(ref mut s) => s.push('마'),
        None => {}
    }
    println!("③ {:?}", v);

    // ref 가 아직 필요한 자리 — let 에서 일부만 빌려 잡을 때
    let pair = (String::from("바"), String::from("사"));
    let (ref a, b) = pair;          // a 는 빌리고 b 는 가져간다
    println!("④ a={} b={}", a, b);
    println!("④ pair.0 은 아직 읽힌다: {}", pair.0);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
① ref 가나 (6바이트)
① 뒤 원본 Some("가나")
② 인체공학 가나 (6바이트)
② 뒤 원본 Some("가나")
③ Some("다라마")
④ a=바 b=사
④ pair.0 은 아직 읽힌다: 바
(종료 코드 0)
```

읽는 법.

- ①과 ②는 **결과가 같다.** ①은 값을 매치하면서 팔에서 `ref` 로 빌리고, ②는 **참조를 매치**한다.
- ★★ **1.26.0 이전에는 ②가 안 됐다.** `match &owned` 를 하면 패턴에도 `&Some(ref s)` 를 적어야 했다.
  매치 인체공학이 그 `&`·`ref` 를 **안 적어도 되게** 만들면서 ①이 쓸 일이 없어졌다.
- ★ **아직 필요한 자리** — `let (ref a, b) = pair;` 처럼 **한 패턴 안에서 어떤 칸은 빌리고 어떤 칸은 가져갈 때**다.
  대상이 값이라 인체공학이 안 켜지고, `&pair` 로 바꾸면 `b` 까지 빌림이 된다.
- 요약 — **`match &x` 로 될 일은 `ref` 를 안 쓴다.** 진단이 `ref` 를 제안하더라도(18번 (5)의 `help:`)
  대개는 **참조를 매치하는 쪽**이 읽기 쉽다.

**가드 안에서는 값을 가져갈 수 없다.**

```text
===== 소스: ex.rs =====
// ex.rs
// 가드는 「빌려서 볼 뿐」이다 — 가드 안에서 값을 가져가려 하면 막힌다
fn main() {
    let v = Some(String::from("가나"));
    fn takes(s: String) -> bool { s.len() > 3 }
    match v {
        Some(s) if takes(s) => println!("길다"),
        _ => println!("짧거나 없다"),
    }
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0507]: cannot move out of `s` in pattern guard
 --> ex.rs:7:26
  |
7 |         Some(s) if takes(s) => println!("길다"),
  |                          ^ move occurs because `s` has type `String`, which does not implement the `Copy` trait
  |
  = note: variables bound in patterns cannot be moved from until after the end of the pattern guard
help: consider cloning the value if the performance cost is acceptable
  |
7 |         Some(s) if takes(s.clone()) => println!("길다"),
  |                           ++++++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0507`.
(종료 코드 1)
```

- **E0507** ``cannot move out of `s` in pattern guard``.
- `= note: variables bound in patterns cannot be moved from until after the end of the pattern guard` —
  ★ **이유가 분명하다.** 가드가 거짓이면 다음 팔이 그 값을 다시 봐야 하는데, 가드가 가져가 버리면 볼 것이 없다.
- 처방은 **빌려서 보는 것**(`takes(&s)`)이거나 진단이 제안하는 `s.clone()` 이다.

### (7) 패턴이 쓰이는 자리는 여섯이다

**언제 쓰나** — `match` 밖에서도 같은 문법이 그대로 쓰인다는 것을 알아 둘 때.

```text
===== 소스: ex.rs =====
// ex.rs
// 패턴이 쓰이는 자리는 match 만이 아니다 — 여섯 자리를 한 파일에서 본다
struct Pt { x: i32, y: i32 }

fn dist(Pt { x, y }: &Pt) -> f64 {          // ④ 함수 인자
    (((x * x) + (y * y)) as f64).sqrt()
}

fn main() {
    let pts = vec![Pt { x: 3, y: 4 }, Pt { x: 6, y: 8 }];

    let Pt { x, y } = &pts[0];              // ① let
    println!("① {} {}", x, y);

    for Pt { x, y } in &pts {               // ② for
        println!("② {} {}", x, y);
    }

    let f = |Pt { x, .. }: &Pt| *x * 10;    // ③ 클로저 인자
    println!("③ {}", f(&pts[1]));

    println!("④ {}", dist(&pts[0]));

    if let [first, ..] = &pts[..] {         // ⑤ if let
        println!("⑤ {}", first.x);
    }

    let mut it = pts.iter();
    while let Some(Pt { x, y }) = it.next() {   // ⑥ while let
        println!("⑥ {} {}", x, y);
    }
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
① 3 4
② 3 4
② 6 8
③ 60
④ 5
⑤ 3
⑥ 3 4
⑥ 6 8
(종료 코드 0)
```

읽는 법.

- ① `let` · ② `for` · ③ 클로저 인자 · ④ 함수 인자 · ⑤ `if let` · ⑥ `while let`.
- ★ ①\~④ 는 **반박 불가** 패턴만 받는다 — 안 맞을 수가 없어야 한다.
  구조체 하나짜리는 늘 맞으니 되고, `Some(x)` 는 안 된다(그때가 `if let`·`let else` 자리다).
- ⑤·⑥ 은 **반박 가능**을 받는다 — 안 맞으면 그냥 안 들어가거나 루프가 끝난다([목록의 **20번 주제**](../20-if-let-while-let-let-else-and-let-chains/)).

## 문법 — 형태와 규칙

**형태.**

```text
// 리터럴 · 범위 · 변수 · 와일드카드
1              'a'..='z'        x            _

// 열거형 · 구조체 · 튜플 · 참조
Some(x)        Point { x, y }   (a, b)       &v      &mut v

// or · @ · 나머지 · 슬라이스
A | B          n @ 1..=9        Foo { x, .. }        [first, rest @ ..]

// 가드 (패턴이 아니라 팔의 일부다)
Some(x) if x > 3 => …

// ref / ref mut (옛 도구)
Some(ref s) => …      Some(ref mut s) => …
```

**규칙.**

- **변수 패턴은 무엇이든 잡는다.** 대문자여도 그렇다(18번 (5)의 E0170).
- **or 패턴의 모든 갈래가 같은 이름을 같은 타입으로 묶어야** 한다(E0408 · E0308).
- **가드는 or 패턴 전체에 걸린다.** 마지막 갈래에만 걸리지 않는다.
- **가드가 붙은 팔은 완전성 계산에 안 들어간다**((2)).
- **가드 안에서 묶인 값을 가져갈 수 없다**(E0507).
- **대상 값의 참조가 바인딩에 옮겨 붙는다**(매치 인체공학). 패턴에 `&` 를 적으면 **한 겹 벗긴다.**
- `..` 는 **여러 칸**, `_` 는 **한 칸**. `..` 는 한 패턴에 **한 번만** 쓸 수 있다.
- `let` · 함수 인자 · `for` · 클로저 인자는 **반박 불가** 패턴만 받는다.

**금지 사례.**

```text
// ① or 패턴의 갈래마다 이름이 다르다 — E0408 (+ E0381)
Shape::Circle { r } | Shape::Square { side } => r,

// ② 이름은 같은데 타입이 다르다 — E0308
V::A(x) | V::B(x) => …,     // A(u32) · B(String)

// ③ 가드 안에서 묶인 값을 가져간다 — E0507
Some(s) if takes(s) => …,   // takes(s: String)

// ④ 가드로 전부 덮었다고 믿는다 — E0004
match n { x if x < 0 => …, x if x == 0 => …, x if x > 0 => … }

// ⑤ 길이를 모르는 슬라이스에서 「셋 이상」을 안 적었다 — E0004
match v { [] => …, [a] => …, [a, b] => … }
```

## 어디서 틀리나

| 자리 | 증상 | 진짜 이유 |
|---|---|---|
| ★★ **`Some(s)` 의 `s` 를 늘 `String` 으로 읽기** | 어떨 때는 원본이 살고 어떨 때는 죽는다 | **대상에 `&` 가 몇 겹 있나**로 갈린다((5)) |
| **가드로 다 덮고 `_` 를 뺐다** | E0004 | 가드는 완전성 계산에 안 들어간다((2)) |
| **or 패턴에서 이름을 다르게** | E0408 + E0381 | 모든 갈래가 같은 이름을 묶어야 한다 |
| **or 패턴에서 타입이 다르게** | E0308 | 같은 이름은 **같은 타입**이라야 한다 |
| **가드 안에서 값을 넘기기** | E0507 | 가드가 거짓이면 다음 팔이 그 값을 봐야 한다 |
| **`(x, x)` 로 같은 값 검사** | 문법 오류 | 관계는 **가드**로 본다 |
| **패턴 자리에 바깥 변수 이름** | 조용히 새 변수가 된다 | 비교가 아니라 바인딩이다. 가드로 비교한다 |
| **슬라이스에서 「셋 이상」 빠뜨리기** | E0004 `&[_, _, _, ..]` | 길이를 모르는 슬라이스는 길이도 값 공간이다 |
| ★ **`ref` 를 습관으로 쓰기** | 읽기 어려워진다 | `match &x` 로 되는 일이면 안 쓴다((6)) |
| **`..` 를 두 번 쓰기** | 문법 오류 | 한 패턴에 한 번만 |

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 |
|---|---|
| 패턴 문법 전부(가드·`@`·or·구조 분해·슬라이스) | **언어 보장** — Reference 의 Patterns |
| **매치 인체공학의 바인딩 모드 규칙** | **언어 보장** — Reference 의 Binding modes |
| 가드가 완전성 계산에 안 들어가는 것 | **언어 보장** — 진단이 그 문장을 직접 적는다 |
| or 패턴의 이름·타입 일치 요구 | **언어 보장** |
| 가드 안에서 이동 금지 | **언어 보장** |
| `let _probe: () = s;` 가 **타입을 찍어 주는 것** | ★ **진단 품질에 기댄 기법**이다. 메시지 문구는 판마다 달라질 수 있다 |
| E0408 에 **E0381 이 딸려 오는 것** | ★ **이 판의 관찰** — 에러 개수는 진단 구현에 달렸다 |
| `help:` 가 주는 고친 코드의 모양 | ★ **이 판의 관찰** |

★ **에디션과 무관한 것 하나** — 매치 인체공학은 **1.26.0부터 전 에디션에 적용**된다.
2015 에디션에서도 같다. 「2018 에디션 기능」으로 외우면 틀린다.

## 언제 쓰고 언제 안 쓰나

**가드를 쓴다** — 값들 사이의 관계, 바깥 변수와의 비교, 범위로 못 적는 조건.
**안 쓴다** — 마지막 팔에는 안 쓴다(완전성이 깨진다). 범위로 적을 수 있으면 범위를 쓴다.

**`@` 를 쓴다** — 거르면서 그 값도 필요할 때. **안 쓴다** — 둘 중 하나만 필요하면 그냥 적는다.

**or 패턴을 쓴다** — 여러 변형이 같은 처리를 받을 때. ★ **`_` 대신 남은 변형을 나열할 때**(18번 (3)).

**슬라이스 패턴을 쓴다** — 앞뒤 몇 개만 볼 때, 길이로 갈릴 때.
**안 쓴다** — 전부 훑을 거면 이터레이터가 낫다([목록의 **36번 주제**](../36-iterator-adapters-laziness-and-collect/)).

**`ref` 를 쓴다** — `let` 에서 칸마다 빌림/이동을 갈라야 할 때. **그 밖에는 `match &x`.**

## 핵심 문장

1. **패턴은 `match` 만의 문법이 아니다** — `let`·함수 인자·`for`·클로저·`if let`·`while let` 여섯 자리에 쓴다.
2. **`Some(s)` 의 `s` 는 대상에 `&` 가 몇 겹 있느냐로 정해진다** — `String`·`&String`·`&mut String`.
3. **타입이 궁금하면 일부러 틀리게 적어 컴파일러가 찍게 한다** — `let _probe: () = s;`.
4. **가드가 붙은 팔은 완전성 계산에 안 들어간다.** 컴파일러가 가드를 못 풀기 때문이다.
5. **or 패턴의 모든 갈래가 같은 이름을 같은 타입으로 묶어야** 한다.
6. **가드 안에서는 묶인 값을 가져갈 수 없다** — 거짓이면 다음 팔이 그 값을 봐야 한다.

## 관련 자료

- [**18번 주제**](../18-match-and-exhaustiveness/) — 완전성 검사의 정본. 여기는 **한 팔 안의 문법**을 맡는다.
- [**17번 주제**](../17-enums-and-data-carrying-variants/) — 패턴이 분해하는 대상(열거형 변형).
- [**10번 주제**](../10-borrowing-and-aliasing-rules/) · [**11번 주제**](../11-borrow-checker-rejections/) — ★ **매치 인체공학이 만드는 것이 빌림**이라
  이 둘이 뒷배경이다. 빌림 규칙 자체는 거기가 정본이다.
- [**08번 주제**](../08-ownership-and-move/) — 팔에서 값을 가져가는 것(이동)의 정본.
- [**15번 주제**](../15-slices-ranges-and-utf8-boundaries/) — 슬라이스와 범위. 여기는 **슬라이스를 패턴으로 가르는 법**만.
- [**04번 주제**](../04-expressions-and-semicolons/) — `match` 가 식이라는 규칙.
- [목록의 **20번 주제**](../20-if-let-while-let-let-else-and-let-chains/) — `if let`·`while let`·`let else`. **반박 가능한 패턴을 쓰는 자리**들이다.
- [목록의 **36번 주제**](../36-iterator-adapters-laziness-and-collect/) — 이터레이터. 슬라이스를 전부 훑을 때의 대안.

## 용어 풀이

| 말 | 뜻 |
|---|---|
| **패턴** | 값의 모양을 적은 것. 맞으면 안쪽을 이름에 묶는다 |
| **바인딩** | 패턴이 이름에 값을 묶는 것 |
| **반박 가능/불가** | 안 맞을 수 있는 패턴 / 항상 맞는 패턴 |
| **가드** | 패턴 뒤의 `if 식`. 완전성 계산에 안 들어간다 |
| **`@` 바인딩** | 거르면서 그 값도 이름에 묶는 것. `n @ 1..=9` |
| **or 패턴** | `\|` 로 여러 모양을 한 팔에 묶는 것 |
| **rest 패턴 `..`** | 나머지 칸을 여럿 건너뛴다. 한 패턴에 한 번 |
| **슬라이스 패턴** | 길이와 앞뒤로 슬라이스를 가르는 패턴 |
| **매치 인체공학** | 대상의 참조가 바인딩에 옮겨 붙는 규칙(1.26.0+, 에디션 무관) |
| **기본 바인딩 모드** | 그 규칙이 바꾸는 것 — `move` / `ref` / `ref mut` |
| **`ref` / `ref mut`** | 바인딩 모드를 손으로 적는 옛 문법 |

## 더 들어가면

- **바인딩 모드는 「한 겹씩」 바뀐다** — `&&Option<T>` 를 `Some(s)` 로 받으면 `s` 는 `&T` 다.
  참조 두 겹이 한 겹으로 접힌다. 실무에서 헷갈리는 자리다.
- **2024 에디션은 이 규칙을 한 번 손봤다** — 인체공학이 켜진 뒤에 `&`·`ref` 를 **섞어 적는 것**을 막는다.
  전수는 목록의 **47번 주제**에서 본다.
- **배타적 범위 패턴** `a..b` 는 1.80.0부터다. 이 문서는 전부 `..=` 를 썼다.
- **`box` 패턴**은 아직 nightly 다. 이 목록 밖이다.
