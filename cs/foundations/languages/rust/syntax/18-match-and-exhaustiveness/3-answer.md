# rust/syntax/18 — `match` 와 완전성 검사 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러·경고는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 받은 것이다.\
> ★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
> ★ 7번 답만 크레이트가 둘이라 명령이 셋이다(`lib.rs` 컴파일 → `ex.rs` 컴파일 → 실행).\
> `lib.rs` 의 절대 경로는 머신마다 다르므로 `--remap-path-prefix` 로 **`./lib.rs`** 로 고정했다.\
> ★★ **`--edition` 을 빼면 에디션 2015 다.** 이 문서의 결과는 전부 **2021** 기준이다.\
> 실험 파일 이름은 **`ex.rs`**(와 `lib.rs`)로 고정했고 **진단의 줄 번호는 그 파일 기준**이다.\
> ★ `rustc --explain` 은 **확인용으로만** 열었고 본문에 옮기지 않았다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ `_` 없는 판은 **네 곳**에서 깨지고, `_` 판은 **0곳**이다

**출력** — ① `_` 없는 판, 변형 셋. 통과한다.

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

**② 같은 파일에 `Drag` 한 줄만 더했다.**

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

**③ 마지막 팔만 `_` 로 바꾼 판, 변형 셋. 역시 통과한다.**

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

**④ 그 `_` 판에 `Drag` 를 더했다.**

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

**왜 그런가**

- ★★★ **`_` 없는 판은 E0004 가 네 개** 난다 — `label`(7줄) · `code`(11줄) · `needs_focus`(15줄) ·
  `main` 안의 `match`(21줄). **`match` 가 있는 자리 전부**다. 완전성 검사는 **자리마다 따로** 돌기 때문이다.
- 네 `help:` 는 각각 **그 자리의 코드에 맞춘** 고친 코드를 준다 — 한 줄짜리 `match` 에는
  `, Event::Drag => todo!() }` 를 덧붙이고, 여러 줄짜리에는 `Event::Drag => todo!(),` 를 한 줄로 넣는다.
- ★★★ **`_` 판은 에러가 0개**다. 컴파일이 통과하고 프로그램이 돌며 `Drag` 는 조용히 `_` 팔로 흘러간다.
- 유일한 불평은 ``warning: variant `Drag` is never constructed`` 인데
  ★ 이것은 「**안 쓰였다**」는 말이지 「**안 처리했다**」는 말이 아니다.
  다른 곳에서 `Drag` 를 한 번만 만들면 그 경고마저 사라진다 — 그러면 **아무 신호도 안 남는다.**

| 판 | `match` 자리 | 추가 전 | 추가 후 **에러** | 추가 후 **경고** |
|---|---|---|---|---|
| `_` 없음 | 4곳 | 통과 | **4** | 0 |
| `_` 있음 | 4곳 | 통과 | **0** | 1 (never constructed — 처리 누락과 무관) |

- **내 열거형에 `_` 대신 쓸 것** — **남은 변형을 or 패턴으로 나열**한다.
  `Event::Click | Event::Scroll => false` 처럼. 그러면 변형이 늘 때 **다시 깨진다.**

### 2. ★★ E0004 — 빠진 것을 **둘 다** 이름으로 댄다. 에러는 하나다

**출력**

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

**왜 그런가**

- **E0004**, 제목은 ``non-exhaustive patterns: `&Event::Scroll` and `&Event::Drag` not covered`` 다.
  ★ **빠진 것을 전부 나열한다** — 둘이면 둘, 넷이면 넷.
- `note:` 는 **열거형 선언 자리**(`ex.rs:3:6`)를 가리키고, 거기서 **안 덮인 변형에만** `not covered` 밑줄을 긋는다.
  `Click`·`Key` 에는 안 긋는다.
- `help:` 는 **or 패턴**으로 묶은 고친 코드를 준다 — `&Event::Scroll | &Event::Drag => todo!()`.
  그 문법은 다음 주제([목록의 **19번 주제**](../19-pattern-syntax-guards-bindings-and-match-ergonomics/))에서 다룬다.
- ★ 패턴에 `&` 가 붙은 것은 대상 값이 **`&Event`** 이기 때문이다 — `label` 이 `&Event` 를 받는다.
  `= note: the matched value is of type &Event` 가 그것을 말한다.
- ★★ **에러는 하나다.** 「빠진 변형마다 하나」가 아니라 **「`match` 자리마다 하나」** 다 — 1번 답의 개수 세기가 그 위에 선다.

### 3. ★★ 에러 둘 — `10_i32` 와 `128_u8..=u8::MAX`. 컴파일러가 **계산한다**

**출력**

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

**왜 그런가**

- 첫 에러는 `1..=9` 와 `11..=i32::MAX` 사이에 남은 **정확히 `10`** 을 짚는다.
- 둘째 에러는 `0..=127` 을 뺀 나머지 **`128_u8..=u8::MAX`** 를 짚는다.
- ★★ 이것은 **나열이 아니라 계산**이다. `u8` 의 남은 128가지를 하나씩 세어 보여 주는 것이 아니라
  **구간으로 압축해서** 적는다. 열거형 쪽이 이름을 대는 것과 같은 일을 정수 공간에서 하는 것이다.

**`i32` 전체를 범위 넷으로 덮으면 `_` 없이 통과한다.**

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

- `i32::MIN..=-1` · `0` · `1..=9` · `10..=i32::MAX` 가 **42억 가지를 빠짐없이** 덮는다.
- ★ `char` 는 유니코드 스칼라 전체라 그렇게 못 한다 — 그래서 `kind` 에는 `_` 를 썼다.
- **그래서 `_` 는 언제 써도 되나** — **값 공간이 현실적으로 못 덮일 때**(`char`·`&str`·큰 정수)와
  **그 타입이 내 손 밖일 때**(7번 답)다. **내 열거형에는 안 쓴다.**

### 4. ★ `(true, Some(1_u8..=u8::MAX))` — 덮인 것을 뺀 나머지를 적어 준다

**출력**

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

**왜 그런가**

- 안 덮인 조합은 **`(true, Some(1_u8..=u8::MAX))`** 다.
- `Some(0)` 이 빠진 이유는 `(true, Some(0))` 팔이 **이미 덮었기** 때문이다.
  ★ 컴파일러는 **「남은 것」을 빼기로 계산**한다 — 튜플 한 칸 안의 범위까지 파고든다.

**다섯 팔로 여섯 갈래를 덮은 판.**

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

- 갈래는 `2 × 3 = 6` 인데 팔은 **다섯**이다 — `(false, Some(_))` 하나가 `Some(0)`·`Some(9)` 두 칸을 함께 먹는다.
- **중첩이 깊어져도 된다.** 열거형 안의 열거형 안의 범위까지 같은 방식으로 센다.

### 5. ★★ 에러다 — **E0170**, 그리고 경고가 **다섯** 붙는다

**출력**

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

**왜 그런가**

- **E0170** — `` pattern binding `Click` is named the same as one of the variants of the type `Event` ``.
  ★ `= note: #[deny(bindings_with_variant_name)] on by default` — **기본이 deny 라 경고가 아니라 에러**다.
- 경고는 **다섯**이다 — `unreachable pattern` **둘**(`Event::Key`·`Event::Scroll`),
  `unused variable: Click`, `variants Click and Key are never constructed`, `variable Click should have a snake case name`.
- ★★ `Click` 은 **새 변수**로 해석됐다. 그것을 말하는 구절은 `unreachable pattern` 진단이
  `Click` 줄에 붙여 놓은 **`matches any value`** 다 — 「무엇이든 잡는다」.
- ★ **`use Event::*;` 를 먼저 써 두었다면 이 진단은 안 난다.** 그때는 `Click` 이 진짜 변형이라
  완전성 검사도 통과하고 아무 문제가 없다. 문제는 **오타가 났을 때** 그것을 걸러 줄 그물이 사라진다는 것이다.
- 그래서 [**17번 주제**](../17-enums-and-data-carrying-variants/)가 `use Enum::*` 를 **습관으로 쓰지 말라**고 했다 —
  경로를 적으면 오타가 E0170 이나 E0433 으로 잡히지만, 열어 두면 **변수 패턴으로 조용히 통과**한다.

### 6. ★★ E0382 — 팔에서 이름을 묶는 순간 이동한다

**출력**

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

**왜 그런가**

- **E0382**, 제목은 `` borrow of partially moved value: `m` `` 다.
  `Msg::Text(s)` 의 `s` 가 **`String` 을 통째로 가져간다** — `value partially moved here`.
- `help:` 가 제안하는 낱말은 **`ref`** 다(`Msg::Text(ref s)`) — 매치 인체공학 이전의 옛 도구이고,
  [목록의 **19번 주제**](../19-pattern-syntax-guards-bindings-and-match-ergonomics/)에서 「왜 요즘은 거의 안 쓰이나」까지 다룬다.

**원본을 살리는 세 가지.**

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

- ① **참조를 매치한다** — `match &m` 이면 `s` 가 `&String` 이 된다(19번 주제의 매치 인체공학).
- ② **칸을 안 묶는다** — `Msg::Text(..)` 는 꺼낼 것이 없으니 이동도 없다.
- ③ **`Copy` 인 칸은 묶어도 이동이 아니다** — `Msg::Num(n)` 뒤에도 `k` 가 살아 있다.
  `u32` 는 `Copy` 라 **복사**된다([**09번 주제**](../09-copy-clone-and-drop/)).

### 7. ★★ 같은 크레이트에서는 아무 일도 안 하고, 경계를 넘으면 `_` 를 강제한다

**출력** — ① 같은 크레이트. `_` 없이 통과한다.

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

**② 크레이트를 갈랐다.**

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

**왜 그런가**

- ★★ 같은 크레이트에서는 **표시가 있어도 완전성 검사가 그대로**다. 변형을 늘리면 **내가 고치면 되기** 때문이다.
- 크레이트를 가르면 **E0004** 가 나는데 짚는 것이 **`&_`** 다 —
  「어느 변형이 빠졌다」가 아니라 **「그 밖 전부가 빠졌다」**.
  앞으로 생길 변형까지 포함하므로 **이름을 댈 수가 없다.**
- 결정적인 줄은 ``= note: `Level` is marked as non-exhaustive, so a wildcard `_` is necessary to match exhaustively`` 다.
- ★★ **같은 `lib.rs` 의 `Plain`(표시 없는 쪽)은 크레이트가 달라도 에러가 안 난다.**
  위 출력에서 `plain` 함수는 아무 진단도 안 받았다 — 갈리는 것은 **크레이트 경계와 표시가 겹칠 때뿐**이다.

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

- 표시 붙은 쪽에만 `_` 를 넣었다. **안 붙은 쪽은 그대로 두었고** 여전히 통과한다.
- **붙이는 쪽이 얻는 것** — 변형을 늘려도 **남의 코드가 안 깨진다**(semver 호환).
  **잃는 것** — 남이 쓸 때 `_` 를 강제당하므로, **남은 내가 변형을 늘린 것을 영원히 모른다.**
  받는 쪽에서는 그 `_` 안에 「모르는 변형이 왔다」는 로그를 남기는 것이 관용구다.

### 8. `match` 는 식이다

**출력**

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

**왜 그런가**

- `let v = match c { … };` 의 세미콜론은 **`let` 문의 것**이다. `match` 자체는 식이라 세미콜론이 없다.
- 팔이 **블록**이면 그 블록의 **마지막 식**이 팔의 값이다 —
  `{ let q = 100 / v; format!("{}개면 1달러", q) }` 가 `String` 을 낸다.
- 팔 타입이 다르면 **E0308**(`match arms have incompatible types`)이고,
  진단은 **첫 팔의 타입을 먼저 정한 뒤**(`this is found to be of type {integer}`) 뒤 팔을 거기 맞춘다.

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

- 값이 필요 없으면 `match` 의 타입은 **`()`** 다. 위 출력의 마지막 줄이 `()` 를 직접 찍어 그것을 보인다.
- 이 성질은 [**04번 주제**](../04-expressions-and-semicolons/)의 「블록이 값이고 세미콜론이 값을 버린다」를 그대로 쓴 것이다.

### 9. 완전성 검사가 세는 단위

- 다루는 값 공간 **넷** — ① **열거형 변형** ② **정수·문자 범위** ③ **튜플·구조체 조합(곱)**
  ④ **슬라이스 길이**(`[]`·`[a]`·`[a, b]`·`[a, .., b]` — [목록의 **19번 주제**](../19-pattern-syntax-guards-bindings-and-match-ergonomics/)).
- **빈 열거형**(`enum Never {}`)은 **팔이 하나도 없어도 완전**하다. 덮을 값이 없기 때문이다.
- `_` 를 **맨 위**에 두면 아래 팔이 전부 `unreachable pattern` **경고**다 — **에러가 아니다.**
  5번 답의 출력에서 그 경고를 볼 수 있다.
- **`..` 는 여러 칸을 건너뛰고 `_` 는 한 칸**이다. `Msg::Text(..)` 와 `Msg::Text(_)` 는
  칸이 하나뿐이라 같지만, 칸이 셋이면 `..` 는 셋을 한 번에 건너뛴다.
- ★ **가드가 붙은 팔은 완전성 계산에 안 들어간다.** 그 증거(`match arms with guards don't count
  towards exhaustivity`)는 [목록의 **19번 주제**](../19-pattern-syntax-guards-bindings-and-match-ergonomics/)에서 던져서 받는다.

### 10. 다른 갈래로 접기

| 번호 | 언제 나나 |
|---|---|
| **E0004** | `match` 가 값 공간을 다 안 덮었다 |
| **E0308** | 팔 타입이 서로 다르다(같은 번호가 타입 불일치 전반에 쓰인다) |
| **E0170** | 경로 없이 변형과 같은 이름을 패턴에 적었다 — **deny 라 에러** |
| **E0382** | 팔에서 묶어 옮긴 값을 나중에 또 썼다 |

- 한 갈래만 궁금하면 **`if let`** — [목록의 **20번 주제**](../20-if-let-while-let-let-else-and-let-chains/). 그쪽에는 **완전성 검사가 없다.**
- 참/거짓만 필요하면 **`matches!`** 매크로 — **1.42.0부터**.
- 완전성 검사가 성립하는 **근거**는 [**17번 주제**](../17-enums-and-data-carrying-variants/)의
  「**열거형은 닫힌 집합**」이라는 사실이다. 변형이 무한하면 셀 수가 없다.
- 변형이 **열려야 하는** 설계라면 열거형 대신 **트레이트 객체**([목록의 **33번 주제**](../33-dyn-trait-objects-and-object-safety/))를 쓴다.
  그 대가로 완전성 검사를 잃는다.
- 이 주제가 미뤄 둔 패턴 문법(가드·`@`·or 패턴·구조 분해·슬라이스 패턴·매치 인체공학)은
  [목록의 **19번 주제**](../19-pattern-syntax-guards-bindings-and-match-ergonomics/)에 전부 있다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh` 가 `rustc --edition 2021 ex.rs -o ex` 로 컴파일하고 `./ex` 실행 | 배치 내내 + **제출 전 전수 재실행 1회** | `diff -rq` **동일** |
| ★★ **변형 추가 실험** | `b18-04a`(통과) → `b18-04b`(E0004 **4개**) · `b18-05a`(통과) → `b18-05b`(**0개**) | 4 | **4 대 0**. 같은 소스에 변형 한 줄만 다르다 |
| 완전성 진단 | `b18-03`(변형 둘) · `b18-09`(범위) · `b18-13`(튜플) | 3 | 빠진 것을 **이름·구간·조합**으로 댄다 |
| 범위로 다 덮기 | `b18-08` — `i32` 를 넷으로 | 1 | `_` 없이 통과 |
| `match` 가 식 | `b18-01`(통과) · `b18-02`(E0308) | 2 | 마지막 줄이 `()` 를 찍는다 |
| 변수 패턴 함정 | `b18-11` | 1 | **E0170 + 경고 5** |
| 묶인 값의 이동 | `b18-10`(E0382) · `b18-10b`(세 가지 회피) | 2 | — |
| `#[non_exhaustive]` | `b18-06`(같은 크레이트) · `b18-07`(다른 크레이트, E0004) · `b18-07b`(고친 판) | 3 | 크레이트 둘짜리는 명령이 셋 |

**구현 의존 항목**(버전이 오르면 **다시 찍어야 하는** 것).

| 항목 | 왜 |
|---|---|
| `bindings_with_variant_name` 이 **deny** 인 것 | lint 수준은 rustc 판의 정책이다 |
| 진단이 빈 구간을 `128_u8..=u8::MAX` 로 **압축해 적는 것** | 진단 품질은 보장이 아니다 |
| `help:` 가 주는 고친 코드의 모양 | 같은 이유 |
| 경고 **개수**(5번 답의 다섯) | lint 구성이 바뀌면 달라진다 |
| `--remap-path-prefix` 를 쓸 때 `note:` 에서 **소스 발췌가 사라지는 것** | 7번 답 출력에서 `lib.rs` 줄이 안 끼워진다 |

★ **다시 찍는 법** — `capture.sh`·`capture2.sh` 를 그대로 돌리고 `diff -rq` 한다.
