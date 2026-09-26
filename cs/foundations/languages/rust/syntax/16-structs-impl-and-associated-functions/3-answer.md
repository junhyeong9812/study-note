# rust/syntax/16 — 구조체 세 종류·`impl`·연관 함수·`Self` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러·경고는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 얻은 것이다.\
> ★ **11번 답의 `cargo doc` 블록만 예외**로 `cargo 1.92.0 (344c4567c 2025-10-21)` 을 쓴다 —\
> 그 블록의 `ex.rs` 는 임시 크레이트의 **`src/lib.rs`** 로 복사되고, 명령 배너에 그 변환까지 적혀 있다.\
> ★★ **`--edition` 을 빼면 에디션 2015 다.** 이 문서의 결과는 전부 **2021** 기준이다.\
> 실험 파일 이름은 전부 **`ex.rs`** 로 고정했고, **진단의 줄 번호는 그 파일 기준**이라\
> 질문 쪽 발췌와 어긋날 수 있다. 그래서 **진단을 싣는 블록마다 그 진단을 낸 소스를 같은 자리에** 뒀다.\
> ★ `rustc --explain` 은 **확인용으로만** 열었고 본문에 옮기지 않았다.\
> ★ 이 주제의 고유 창은 **진단에게 후보를 나열시키기**(6번) · **`cargo doc` HTML 세기**(11번) ·\
> **`size_of`/`align_of` 로 재기**(3번) 셋이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ 거부된다 — E0382 `borrow of partially moved value`

**출력**

```text
===== 소스: ex.rs =====
// 구조체 갱신 문법 ..other 는 이동인가 복사인가 — String 필드를 두고 원본을 다시 써 본다
#[derive(Debug)]
struct Config { name: String, retries: u32, verbose: bool }

fn main() {
    let base = Config { name: String::from("기본"), retries: 3, verbose: false };
    let derived = Config { retries: 5, ..base };
    println!("{:?}", derived);
    println!("{:?}", base);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0382]: borrow of partially moved value: `base`
 --> ex.rs:9:22
  |
7 |     let derived = Config { retries: 5, ..base };
  |                   ----------------------------- value partially moved here
8 |     println!("{:?}", derived);
9 |     println!("{:?}", base);
  |                      ^^^^ value borrowed here after partial move
  |
  = note: partial move occurs because `base.name` has type `String`, which does not implement the `Copy` trait
  = note: this error originates in the macro `$crate::format_args_nl` which comes from the expansion of the macro `println` (in Nightly builds, run with -Z macro-backtrace for more info)

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0382`.
```

**왜 그런가**

- **E0382**, 제목은 **`borrow of partially moved value: base`** 다.
- ★★ 결정적인 낱말은 **`partially moved`**(부분 이동)다. `..base` 는 구조체를 **통째로 옮기는 것이 아니라 칸마다** 처리한다 —
  `Copy` 인 칸은 복사하고, 아닌 칸은 **옮긴다**.
- `= note:` 가 짚는 것은 **`base.name`** 하나다. `retries: u32` 와 `verbose: bool` 은 `Copy` 라 복사됐고,
  **`String` 인 `name` 만 이동**했기 때문이다. ★ 그래서 진단이 **「어느 칸 때문인지」를 이름으로** 댄다.
- 두 번째 `= note:` 는 `println!` 매크로 확장 때문에 붙은 **위치 안내**다 — 에러의 원인이 아니다.

**세 필드를 전부 `Copy` 로 바꾸면 통과한다.** 같은 `..base` 인데 결과가 갈린다.

```text
===== 소스: ex.rs =====
// 같은 ..other 인데 필드가 전부 Copy 면? — 그리고 필드 초기화 축약
#[derive(Debug)]
struct Config { retries: u32, verbose: bool }

fn make(retries: u32, verbose: bool) -> Config {
    Config { retries, verbose }   // 필드 초기화 축약 — retries: retries 를 줄인 것
}

fn main() {
    let base = make(3, false);
    let derived = Config { retries: 5, ..base };
    println!("파생: {} {}", derived.retries, derived.verbose);
    println!("원본: {} {}", base.retries, base.verbose);   // Copy 필드뿐이라 원본이 살아 있다
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
파생: 5 false
원본: 3 false
(종료 코드 0)
```

- ★ **`base.retries` 하나만 읽는 것은 첫 번째 파일에서도 된다.** 부분 이동은 **옮겨진 칸만** 막는다.
  막힌 것은 `base` **전체**를 빌리려 한 `{:?}` 였다.
- 위 파일의 `Config { retries, verbose }` 가 **필드 초기화 축약**이다 — `retries: retries` 를 줄인 것이고,
  **이름이 같을 때만** 쓸 수 있다.

```text
   ..base 가 칸마다 하는 일

   base : | name: String | retries: u32 | verbose: bool |
                │              (안 씀)          │
              이동                             복사
                ▼                               ▼
   derived: | name: String | retries: 5   | verbose: bool |
```

★ 판정 규칙은 [**09번 주제**](../09-copy-clone-and-drop/)의 `Copy` 판정 그대로다 — **새 규칙이 아니라 칸 단위 적용**이다.

### 2. ★★ 에러 둘 — E0599 와 E0061. **두 방향이 대칭이 아니다**

**출력**

```text
===== 소스: ex.rs =====
// 연관 함수와 메서드 — 리시버가 있냐 없냐. 호출 문법을 바꿔 불러 본다
struct Counter { n: u32 }

impl Counter {
    fn new() -> Self { Counter { n: 0 } }   // 연관 함수 — self 없음
    fn get(&self) -> u32 { self.n }         // 메서드 — &self 있음
}

fn main() {
    let c = Counter::new();
    println!("{}", c.new());   // 연관 함수를 . 으로
    println!("{}", Counter::get());  // 메서드를 :: 으로
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0599]: no method named `new` found for struct `Counter` in the current scope
  --> ex.rs:11:22
   |
 2 | struct Counter { n: u32 }
   | -------------- method `new` not found for this struct
...
11 |     println!("{}", c.new());   // 연관 함수를 . 으로
   |                    --^^^--
   |                    | |
   |                    | this is an associated function, not a method
   |                    help: use associated function syntax instead: `Counter::new()`
   |
   = note: found the following associated functions; to be used as methods, functions must have a `self` parameter
note: the candidate is defined in an impl for the type `Counter`
  --> ex.rs:5:5
   |
 5 |     fn new() -> Self { Counter { n: 0 } }   // 연관 함수 — self 없음
   |     ^^^^^^^^^^^^^^^^

error[E0061]: this function takes 1 argument but 0 arguments were supplied
  --> ex.rs:12:20
   |
12 |     println!("{}", Counter::get());  // 메서드를 :: 으로
   |                    ^^^^^^^^^^^^-- argument #1 of type `&Counter` is missing
   |
note: method defined here
  --> ex.rs:6:8
   |
 6 |     fn get(&self) -> u32 { self.n }         // 메서드 — &self 있음
   |        ^^^ -----
help: provide the argument
   |
12 |     println!("{}", Counter::get(/* &Counter */));  // 메서드를 :: 으로
   |                                 ++++++++++++++

error: aborting due to 2 previous errors

Some errors have detailed explanations: E0061, E0599.
For more information about an error, try `rustc --explain E0061`.
```

**왜 그런가**

| 틀리게 부른 방향 | 번호 | 진단이 하는 말 | 성격 |
|---|---|---|---|
| 연관 함수를 `.` 으로 (`c.new()`) | **E0599** | `this is an associated function, not a method` | **그런 메서드가 없다.** 문법을 바꾸라고 한다 |
| 메서드를 `::` 으로 (`Counter::get()`) | **E0061** | `argument #1 of type &Counter is missing` | ★ **문법은 맞다.** 인자를 안 줬을 뿐이다 |

- ★★ **`Counter::get(&c)` 는 컴파일된다.** `c.get()` 이 그것의 **줄임**이기 때문이다.
  진단이 `Counter::get(/* &Counter */)` 를 끼워 넣으라고 말하는 것이 증거다 —
  **`.` 은 리시버를 첫 인자로 넣어 주는 설탕**이고, 그래서 **두 방향의 에러가 대칭이 아니다.**
- ★ `= note: found the following associated functions; to be used as methods, functions must have a self parameter`
  이 한 줄이 **연관 함수와 메서드의 정의를 컴파일러 입으로 말한 것**이다.
  **메서드는 연관 함수 중 리시버가 있는 것**이다 — 부분집합이지 반대가 아니다.
- `note: the candidate is defined in an impl for the type Counter` 가 **어느 `impl` 에 있는지**까지 짚는다.
  ★ 후보가 **하나**라서 `the candidate` 이고, 여럿이면 `candidate #1`·`#2` 가 된다(6번 답).

### 3. ★★ 0바이트인 것이 넷 — 그리고 필드 순서는 보장이 아니다

**출력**

```text
===== 소스: ex.rs =====
// 유닛 구조체·튜플 구조체·이름 있는 구조체의 크기와 정렬을 전부 찍는다
use std::mem::{align_of, size_of};

struct Unit;                       // 유닛 구조체
struct Empty();                    // 빈 튜플 구조체
struct Newtype(u64);               // 필드 하나인 튜플 구조체(newtype)
struct Pair(u8, u32);              // 필드 둘인 튜플 구조체
struct Named { a: u8, b: u32 }     // 이름 있는 구조체
struct Reordered { b: u32, a: u8 } // 같은 필드, 선언 순서만 바꿈

fn row(name: &str, size: usize, align: usize) {
    println!("{:<10} size={} align={}", name, size, align);
}

fn main() {
    row("Unit", size_of::<Unit>(), align_of::<Unit>());
    row("Empty", size_of::<Empty>(), align_of::<Empty>());
    row("Newtype", size_of::<Newtype>(), align_of::<Newtype>());
    row("u64", size_of::<u64>(), align_of::<u64>());
    row("Pair", size_of::<Pair>(), align_of::<Pair>());
    row("Named", size_of::<Named>(), align_of::<Named>());
    row("Reordered", size_of::<Reordered>(), align_of::<Reordered>());
    row("()", size_of::<()>(), align_of::<()>());
    row("[u8; 0]", size_of::<[u8; 0]>(), align_of::<[u8; 0]>());

    // 필드를 실제로 읽어 dead_code 경고를 없앤다
    let n = Newtype(7);
    let p = Pair(1, 2);
    let s = Named { a: 3, b: 4 };
    let r = Reordered { b: 5, a: 6 };
    let _ = (Unit, Empty());
    println!("값 확인: {} {} {} {} {} {}", n.0, p.0, p.1, s.a, s.b, r.a + r.b as u8);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
Unit       size=0 align=1
Empty      size=0 align=1
Newtype    size=8 align=8
u64        size=8 align=8
Pair       size=8 align=4
Named      size=8 align=4
Reordered  size=8 align=4
()         size=0 align=1
[u8; 0]    size=0 align=1
값 확인: 7 1 2 3 4 11
(종료 코드 0)
```

**왜 그런가**

| 타입 | `size_of` | `align_of` | 한 줄 |
|---|---|---|---|
| `struct Unit;` | **0** | **1** | 유닛 구조체 — 담을 것이 없다 |
| `struct Empty();` | **0** | **1** | 빈 튜플 구조체 — 위와 같은 것을 튜플 문법으로 쓴 것 |
| `struct Newtype(u64);` | 8 | 8 | ★ 안쪽 `u64` 와 **같다** |
| `u64` | 8 | 8 | 대조군 |
| `struct Pair(u8, u32);` | 8 | 4 | 패딩 3바이트 |
| `struct Named { a: u8, b: u32 }` | 8 | 4 | 튜플이든 이름이든 같다 |
| `struct Reordered { b: u32, a: u8 }` | 8 | 4 | 순서를 바꿔도 같았다(**관찰**) |
| `()` | **0** | **1** | 유닛 타입 |
| `[u8; 0]` | **0** | **1** | 길이 0 배열 |

- ★★ **0바이트인 것은 넷**이다 — `Unit` · `Empty()` · `()` · `[u8; 0]`. 이런 타입을 **ZST**(zero-sized type)라 부른다.
- **정렬은 넷 다 `1`** 이다. **`0` 이 아니다** — 정렬의 최솟값이 1이기 때문이다.
- ★ **newtype 은 안쪽 타입과 크기·정렬이 같다.** 감싸는 비용이 0이라는 것이 newtype 관용구의 근거다.
  ★ 다만 이것은 **구현**이 그렇게 한 것이고, Reference 는 단일 필드 구조체의 레이아웃을 **약속하지 않는다.**
- ★★ **`Named` 와 `Reordered` 가 같은 크기인 것은 「관찰」이지 보장이 아니다.**
  기본 표현 `repr(Rust)` 는 **필드를 재배치할 수 있다** — 실제로 재배치했는지 주소를 직접 재면 나온다.

```text
===== 소스: ex.rs =====
// 필드가 실제로 어느 자리에 놓이나 — repr(Rust) 대 repr(C)
struct Named { a: u8, b: u32 }

#[repr(C)]
struct NamedC { a: u8, b: u32 }

fn main() {
    let s = Named { a: 1, b: 2 };
    let base = &s as *const Named as usize;
    println!("repr(Rust)  size={}  a@{}  b@{}",
             std::mem::size_of::<Named>(),
             (&s.a as *const u8 as usize) - base,
             (&s.b as *const u32 as usize) - base);

    let c = NamedC { a: 1, b: 2 };
    let basec = &c as *const NamedC as usize;
    println!("repr(C)     size={}  a@{}  b@{}",
             std::mem::size_of::<NamedC>(),
             (&c.a as *const u8 as usize) - basec,
             (&c.b as *const u32 as usize) - basec);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
repr(Rust)  size=8  a@4  b@0
repr(C)     size=8  a@0  b@4
(종료 코드 0)
```

★★ **`repr(Rust)` 에서 `a` 가 4번 바이트, `b` 가 0번 바이트에 놓였다 — 선언 순서와 반대다.**
`#[repr(C)]` 를 붙이면 선언 순서대로 `a@0`·`b@4` 가 된다.

> ★ **대조할 것은 숫자가 아니라 「기본 표현에서는 필드 순서가 보장되지 않는다」는 성질이다.**\
> 이 오프셋은 **rustc 판과 대상 플랫폼에 달렸다.** 같은 툴체인·같은 머신에서는 재현되지만
> **다음 판에서 달라져도 버그가 아니다.** 고정이 필요하면 `#[repr(C)]` 를 적는다.

### 4. ★ 된다 — `s.f` 와 `s.f()` 는 다른 이름 공간이다

**출력**

```text
===== 소스: ex.rs =====
// 필드와 메서드가 이름이 같아도 되나 — 그리고 필드가 클로저일 때는 어떻게 부르나
struct Widget {
    width: u32,
    render: Box<dyn Fn() -> String>,
}

impl Widget {
    fn width(&self) -> u32 { self.width * 2 }       // 필드와 같은 이름
    fn render(&self) -> String { String::from("메서드 render") }
}

fn main() {
    let w = Widget { width: 10, render: Box::new(|| String::from("필드 render")) };

    println!("필드   w.width   = {}", w.width);
    println!("메서드 w.width() = {}", w.width());
    println!("메서드 w.render() = {}", w.render());
    println!("필드   (w.render)() = {}", (w.render)());
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
필드   w.width   = 10
메서드 w.width() = 20
메서드 w.render() = 메서드 render
필드   (w.render)() = 필드 render
(종료 코드 0)
```

**왜 그런가**

- **된다.** 경고 한 줄도 없다. **필드와 메서드는 이름 공간이 다르다.**
- ★★ **`w.render()` 는 메서드를 부른다.** 필드가 함수여도 **메서드가 이긴다** — `메서드 render` 가 나온 것이 그 증거다.
- **`(w.render)()` 의 괄호는 「먼저 필드를 읽어라」를 강제한다.** 괄호 안이 필드 접근이 되고, 그 결과를 호출한다.

```text
   s.f   와  s.f()  는 서로 다른 이름 공간을 본다

   s.f        → 필드 f
   s.f()      → 메서드 f   ★ 필드가 함수여도 메서드가 이긴다
   (s.f)()    → 필드 f 를 꺼내서 호출
```

**메서드를 지우면 진단이 괄호를 권한다.**

```text
===== 소스: ex.rs =====
// 클로저 필드를 메서드처럼 부르면
struct Widget { render: Box<dyn Fn() -> String> }

fn main() {
    let w = Widget { render: Box::new(|| String::from("필드 render")) };
    println!("{}", w.render());
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0599]: no method named `render` found for struct `Widget` in the current scope
 --> ex.rs:6:22
  |
2 | struct Widget { render: Box<dyn Fn() -> String> }
  | ------------- method `render` not found for this struct
...
6 |     println!("{}", w.render());
  |                      ^^^^^^ field, not a method
  |
help: to call the trait object stored in `render`, surround the field access with parentheses
  |
6 |     println!("{}", (w.render)());
  |                    +        +

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0599`.
```

★ **`field, not a method`** — 2번의 `associated function, not a method` 와 짝이다.
**E0599 는 「메서드가 아닌 무엇이 그 이름을 쓰고 있다」를 종류별로 갈라 말한다.**

### 5. ★ E0382 — 그리고 `mut` 없는 바인딩에서는 E0596

**출력**

```text
===== 소스: ex.rs =====
// self 를 받는 메서드를 두 번 부르면
struct Builder { parts: Vec<String> }

impl Builder {
    fn new() -> Self { Builder { parts: Vec::new() } }
    fn add(mut self, s: &str) -> Self { self.parts.push(s.to_string()); self }
    fn build(self) -> String { self.parts.join("-") }
}

fn main() {
    let b = Builder::new().add("가").add("나");
    println!("{}", b.build());
    println!("{}", b.build());
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0382]: use of moved value: `b`
  --> ex.rs:13:20
   |
11 |     let b = Builder::new().add("가").add("나");
   |         - move occurs because `b` has type `Builder`, which does not implement the `Copy` trait
12 |     println!("{}", b.build());
   |                      ------- `b` moved due to this method call
13 |     println!("{}", b.build());
   |                    ^ value used here after move
   |
note: `Builder::build` takes ownership of the receiver `self`, which moves `b`
  --> ex.rs:7:14
   |
 7 |     fn build(self) -> String { self.parts.join("-") }
   |              ^^^^

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0382`.
```

**왜 그런가**

- **E0382 `use of moved value`** 다. [**08번 주제**](../08-ownership-and-move/)의 그 에러와 **같은 것**이고,
  이동이 **메서드 호출 자리에서** 일어났다는 점만 다르다.
- ★ `note:` 가 짚는 것은 **리시버**다 — `Builder::build takes ownership of the receiver self` 라고 말하고,
  캐럿은 시그니처의 **`self` 글자**에 붙는다. 호출 자리는 `moved due to this method call` 로 따로 표시된다.
- ★★ **`fn add(mut self, …)` 의 `mut` 는 `&mut self` 가 아니다.** 리시버 종류는 여전히 **`self`(소비)** 이고,
  `mut` 는 「받은 값을 몸통 안에서 고치겠다」는 **바인딩 표시**다. 빌더 관용구가 이 모양을 쓴다.

**`&mut self` 를 `mut` 없는 바인딩에서 부르면.**

```text
===== 소스: ex.rs =====
// &mut self 메서드를 부르는데 let 이 mut 가 아니면
struct Counter { n: u32 }

impl Counter {
    fn new() -> Self { Counter { n: 0 } }
    fn bump(&mut self) { self.n += 1; }
    fn get(&self) -> u32 { self.n }
}

fn main() {
    let c = Counter::new();
    c.bump();
    println!("{}", c.get());
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0596]: cannot borrow `c` as mutable, as it is not declared as mutable
  --> ex.rs:12:5
   |
12 |     c.bump();
   |     ^ cannot borrow as mutable
   |
help: consider changing this to be mutable
   |
11 |     let mut c = Counter::new();
   |         +++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0596`.
```

- **E0596** 이고, ★ `help:` 가 고치라고 짚는 줄은 **호출 줄(12)이 아니라 선언 줄(11)** 이다 — `let mut c`.
- ★★ **`c.bump()` 라는 점 하나가 `&mut c` 를 만든다.** 빌림이 문법에 안 보인다.
  [**02번 주제**](../02-bindings-mut-and-shadowing/)의 `mut` 와 [**10번 주제**](../10-borrowing-and-aliasing-rules/)의 가변 빌림이 **메서드 호출 자리에서 만난다.**

**그 가변 빌림은 값 「전체」를 잡는다.**

```text
===== 소스: ex.rs =====
// 리시버 세 가지가 호출 자리에 무엇을 요구하나 — &mut self 가 전체를 잡는다
struct Log { lines: Vec<String> }

impl Log {
    fn new() -> Self { Log { lines: Vec::new() } }
    fn first(&self) -> &String { &self.lines[0] }       // 공유 빌림
    fn push(&mut self, s: &str) { self.lines.push(s.to_string()); }   // 가변 빌림
}

fn main() {
    let mut log = Log::new();
    log.push("첫 줄");
    let head = log.first();     // 공유 빌림이 살아 있는 동안
    log.push("둘째 줄");        // 가변 빌림을 요청하면?
    println!("{}", head);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0502]: cannot borrow `log` as mutable because it is also borrowed as immutable
  --> ex.rs:14:5
   |
13 |     let head = log.first();     // 공유 빌림이 살아 있는 동안
   |                --- immutable borrow occurs here
14 |     log.push("둘째 줄");        // 가변 빌림을 요청하면?
   |     ^^^^^^^^^^^^^^^^^^^ mutable borrow occurs here
15 |     println!("{}", head);
   |                    ---- immutable borrow later used here

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0502`.
```

★ `first` 가 읽은 것은 `lines[0]` 하나인데 **`log` 전체**가 잡혔다 — 시그니처가 `&self` 라고 말했기 때문이다.
처방(분할 빌림·필드 직접 접근)은 [**11번 주제**](../11-borrow-checker-rejections/)가 정본이다.

### 6. ★★ E0599 — 후보를 `candidate #1`·`#2` 로 **둘** 나열한다

**출력**

```text
===== 소스: ex.rs =====
// 같은 이름의 연관 함수가 두 impl 에 있으면 진단이 몇 개를 나열하나
struct Counter { n: u32 }

trait Make { fn build() -> Self; }

impl Counter {
    fn build() -> Self { Counter { n: 0 } }
}

impl Make for Counter {
    fn build() -> Self { Counter { n: 9 } }
}

fn main() {
    let c = Counter { n: 1 };
    println!("{}", c.build().n);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0599]: no method named `build` found for struct `Counter` in the current scope
  --> ex.rs:16:22
   |
 2 | struct Counter { n: u32 }
   | -------------- method `build` not found for this struct
...
16 |     println!("{}", c.build().n);
   |                      ^^^^^ this is an associated function, not a method
   |
   = note: found the following associated functions; to be used as methods, functions must have a `self` parameter
note: candidate #1 is defined in the trait `Make`
  --> ex.rs:4:14
   |
 4 | trait Make { fn build() -> Self; }
   |              ^^^^^^^^^^^^^^^^^^^
note: candidate #2 is defined in an impl for the type `Counter`
  --> ex.rs:7:5
   |
 7 |     fn build() -> Self { Counter { n: 0 } }
   |     ^^^^^^^^^^^^^^^^^^
help: disambiguate the associated function for candidate #1
   |
16 -     println!("{}", c.build().n);
16 +     println!("{}", <Counter as Make>::build().n);
   |

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0599`.
```

**왜 그런가**

- **E0599** 이고, **후보 둘**을 `candidate #1`·`candidate #2` 로 **번호를 매겨** 나열한다.
- ★★ 둘의 설명 문구가 **다르다** — `#1 is defined in the trait Make` / `#2 is defined in an impl for the type Counter`.
  **트레이트에 선언된 것과 고유 `impl` 에 있는 것**을 갈라서 말한다.
- `help:` 가 주는 고친 코드는 **완전 수식 문법**(fully qualified syntax) `<Counter as Make>::build()` 다 —
  「어느 트레이트의 것인지」를 타입 자리에 적어 모호성을 없앤다.
- ★ **이것이 이 주제의 두 번째 창**이다 — 진단이 **자기가 찾은 것을 나열하게** 만들면 `impl` 표면이 보인다.

**같은 이름을 고유 `impl` 두 블록에 두면 번호가 갈린다.**

```text
===== 소스: ex.rs =====
// 같은 메서드를 두 impl 블록에 중복 정의하면
struct Counter { n: u32 }

impl Counter {
    fn get(&self) -> u32 { self.n }
}

impl Counter {
    fn get(&self) -> u32 { self.n + 100 }
}

fn main() {
    let c = Counter { n: 1 };
    println!("{}", c.get());
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0592]: duplicate definitions with name `get`
 --> ex.rs:5:5
  |
5 |     fn get(&self) -> u32 { self.n }
  |     ^^^^^^^^^^^^^^^^^^^^ duplicate definitions for `get`
...
9 |     fn get(&self) -> u32 { self.n + 100 }
  |     -------------------- other definition for `get`

error[E0034]: multiple applicable items in scope
  --> ex.rs:14:22
   |
14 |     println!("{}", c.get());
   |                      ^^^ multiple `get` found
   |
note: candidate #1 is defined in an impl for the type `Counter`
  --> ex.rs:5:5
   |
 5 |     fn get(&self) -> u32 { self.n }
   |     ^^^^^^^^^^^^^^^^^^^^
note: candidate #2 is defined in an impl for the type `Counter`
  --> ex.rs:9:5
   |
 9 |     fn get(&self) -> u32 { self.n + 100 }
   |     ^^^^^^^^^^^^^^^^^^^^

error: aborting due to 2 previous errors

Some errors have detailed explanations: E0034, E0592.
For more information about an error, try `rustc --explain E0034`.
```

★ **에러가 둘 난다** — **E0592**(정의 쪽: 중복 정의)와 **E0034**(호출 쪽: 어느 것인지 모르겠다)다.
**고유 `impl` 끼리는 이름이 겹치면 정의 자체가 거부**되고, 트레이트와 고유 `impl` 사이는 **공존하되 호출이 모호**해진다.

### 7. `Self` 는 타입, `self` 는 값 — 자리는 **세 갈래**

**출력**

```text
===== 소스: ex.rs =====
// Self 가 쓰이는 자리를 한 파일에 전부 모은다 — 몇 자리인가
struct Point { x: i32, y: i32 }

impl Point {
    // ① 연관 상수의 타입 자리 + ② 값 자리(구조체 리터럴)
    const ORIGIN: Self = Self { x: 0, y: 0 };

    // ③ 연관 함수의 반환 타입 + ④ 생성자 몸통의 Self { … }
    fn new(x: i32, y: i32) -> Self { Self { x, y } }

    // ⑤ 인자 타입 자리
    fn add(&self, other: &Self) -> Self { Self::new(self.x + other.x, self.y + other.y) }

    // ⑥ 지역 변수 타입 자리 + ⑦ 경로 한정자(Self::연관함수 · Self::연관상수)
    fn doubled(&self) -> Self {
        let base: Self = Self::ORIGIN;
        Self::new(base.x + self.x * 2, base.y + self.y * 2)
    }

    // ⑧ 리시버 타입을 직접 적는 자리 — self: &Self 는 &self 의 원래 형태다
    fn len2(self: &Self) -> i32 { self.x * self.x + self.y * self.y }

    // ⑨ 패턴 자리
    fn parts(&self) -> (i32, i32) {
        let Self { x, y } = *self;
        (x, y)
    }
}

// ⑩ 튜플 구조체에서는 Self 가 생성자 함수 이름으로도 쓰인다
struct Meters(f64);
impl Meters {
    fn zero() -> Self { Self(0.0) }
    fn plus(self, d: f64) -> Self { Self(self.0 + d) }
}

// ⑪ 유닛 구조체에서는 Self 하나가 값이다
struct Marker;
impl Marker {
    fn make() -> Self { Self }
}

// ⑫ 트레이트의 연관 타입 자리
trait Doubler {
    type Out;
    fn twice(self) -> Self::Out;
}
impl Doubler for Point {
    type Out = Self;                    // 연관 타입에 Self
    fn twice(self) -> Self::Out { self.doubled() }
}

fn main() {
    let p = Point::new(3, 4);
    let q = p.add(&Point::ORIGIN);
    println!("add     = ({}, {})", q.x, q.y);
    println!("doubled = ({}, {})", p.doubled().x, p.doubled().y);
    println!("len2    = {}", p.len2());
    println!("parts   = {:?}", p.parts());
    println!("twice   = ({}, {})", p.twice().x, q.y);
    println!("meters  = {}", Meters::zero().plus(2.5).0);
    let _m: Marker = Marker::make();
    println!("marker  = 만들어졌다");
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
add     = (3, 4)
doubled = (6, 8)
len2    = 25
parts   = (3, 4)
twice   = (6, 4)
meters  = 2.5
marker  = 만들어졌다
(종료 코드 0)
```

**왜 그런가**

- ★ **가르는 한 문장** — **`Self` 는 타입의 이름이고 `self` 는 값의 이름**이다. 타입 자리에 `self` 를 쓸 수 없고 반대도 안 된다.
- ★★ **자리를 성격으로 묶으면 셋**이다. 「반환 타입 · 생성자 몸통 · 타입 이름 대신 · 연관 상수/타입」 **넷으로 세면 모자란다** —
  **경로 한정자**·**패턴**·**리시버 타입**이 빠진다.

| 갈래 | 무엇인가 | 위 파일의 예 |
|---|---|---|
| **타입 자리** | 타입 이름을 적는 모든 곳 | `-> Self` · `other: &Self` · `let base: Self` · `const ORIGIN: Self` · `type Out = Self` · `self: &Self` |
| **값·패턴 자리** | 생성자 표현식과 패턴 | `Self { x, y }` · `Self(0.0)` · `Self`(유닛) · `let Self { x, y } = *self` |
| **경로 한정자 자리** | `Self::` 로 시작하는 경로 | `Self::new(…)` · `Self::ORIGIN` · `Self::Out` |

- ★ **`self: &Self` 는 `&self` 와 같은 것**이다. 위 파일에서 `len2(self: &Self)` 가 `p.len2()` 로 그냥 불린다 —
  `&self` 는 **그 표기의 줄임**이다.
- **이름 있는 구조체에서 `Self` 를 값으로 쓰면 거부된다.**

```text
===== 소스: ex.rs =====
// 타입 Self 와 리시버 self 는 다른 것이다 — 자리를 바꿔 써 본다
struct Point { x: i32, y: i32 }

impl Point {
    fn new() -> Self { Self }          // 이름 있는 구조체인데 Self 를 값으로
    fn sum(&self) -> i32 { Self.x }    // 리시버 자리에 Self
}

fn main() {
    let p = Point::new();
    println!("{} {}", p.sum(), p.y);
}
===== rustc --edition 2021 ex.rs -o ex =====
error: the `Self` constructor can only be used with tuple or unit structs
 --> ex.rs:5:24
  |
5 |     fn new() -> Self { Self }          // 이름 있는 구조체인데 Self 를 값으로
  |                        ^^^^ help: use curly brackets: `Self { /* fields */ }`

error: the `Self` constructor can only be used with tuple or unit structs
 --> ex.rs:6:28
  |
6 |     fn sum(&self) -> i32 { Self.x }    // 리시버 자리에 Self
  |                            ^^^^ help: use curly brackets: `Self { /* fields */ }`

error: aborting due to 2 previous errors
```

- ★ **이 진단에는 번호가 없다** — `error[E0…]` 가 아니라 그냥 `error:` 다.
- 문구가 답이다 — **`Self` 생성자는 튜플 구조체와 유닛 구조체에서만 쓸 수 있다.**
  이름 있는 구조체에서는 **반드시 중괄호**가 있어야 한다.

**`impl` 밖에서는 `Self` 라는 이름이 없다.**

```text
===== 소스: ex.rs =====
// Self 는 impl(과 트레이트) 안에서만 이름이 있다 — 밖에서 쓰면
struct Point { x: i32, y: i32 }

fn make() -> Self { Self { x: 0, y: 0 } }

fn main() {
    let p = make();
    println!("{} {}", p.x, p.y);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0411]: cannot find type `Self` in this scope
 --> ex.rs:4:14
  |
4 | fn make() -> Self { Self { x: 0, y: 0 } }
  |    ----      ^^^^ `Self` is only available in impls, traits, and type definitions
  |    |
  |    `Self` not allowed in a function

error[E0411]: cannot find struct, variant or union type `Self` in this scope
 --> ex.rs:4:21
  |
4 | fn make() -> Self { Self { x: 0, y: 0 } }
  |    ----             ^^^^ `Self` is only available in impls, traits, and type definitions
  |    |
  |    `Self` not allowed in a function

error: aborting due to 2 previous errors

For more information about this error, try `rustc --explain E0411`.
```

★★ **E0411** 이고, 진단이 유효 범위를 한 줄로 말해 준다 —
**`Self` is only available in impls, traits, and type definitions**.
★ 같은 줄에서 **타입 자리와 값 자리가 따로** 걸려 E0411 이 **둘** 났다는 것도 위 분류와 맞는다.

### 8. 여럿 둬도 된다 — 나누는 이유는 **제네릭 경계**다

**출력**

```text
===== 소스: ex.rs =====
// 같은 타입에 impl 블록을 셋 두면 되나 — 이름만 안 겹치면 된다
struct Counter { n: u32 }

impl Counter {
    fn new() -> Self { Counter { n: 0 } }
}

impl Counter {
    fn bump(&mut self) -> &mut Self { self.n += 1; self }
}

impl Counter {
    fn get(&self) -> u32 { self.n }
}

fn main() {
    let mut c = Counter::new();
    c.bump().bump().bump();
    println!("{}", c.get());
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
3
(종료 코드 0)
```

**왜 그런가**

- **된다. 개수 제한은 없다.** 경고도 없다 — `impl` 은 타입 선언과 **분리**돼 있기 때문이다.
- ★ **나눠야만 되는 것**이 제네릭 경계다. 경계가 다른 메서드를 한 블록에 못 넣는다.

```text
===== 소스: ex.rs =====
// impl 블록을 여럿 두는 실제 이유 — 제네릭 경계별로 가르기
use std::fmt::Display;

struct Wrapper<T> { inner: T }

impl<T> Wrapper<T> {
    fn new(inner: T) -> Self { Wrapper { inner } }     // 경계 없이 늘 된다
}

impl<T: Display> Wrapper<T> {
    fn show(&self) -> String { format!("[{}]", self.inner) }  // Display 일 때만 생긴다
}

struct NoDisplay;

fn main() {
    let a = Wrapper::new(42);
    println!("{}", a.show());

    let b = Wrapper::new(NoDisplay);   // new 는 된다
    let _ = &b.inner;
    println!("{}", b.show());          // show 는?
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0599]: the method `show` exists for struct `Wrapper<NoDisplay>`, but its trait bounds were not satisfied
  --> ex.rs:22:22
   |
 4 | struct Wrapper<T> { inner: T }
   | ----------------- method `show` not found for this struct
...
14 | struct NoDisplay;
   | ---------------- doesn't satisfy `NoDisplay: std::fmt::Display`
...
22 |     println!("{}", b.show());          // show 는?
   |                      ^^^^ method cannot be called on `Wrapper<NoDisplay>` due to unsatisfied trait bounds
   |
note: trait bound `NoDisplay: std::fmt::Display` was not satisfied
  --> ex.rs:10:9
   |
10 | impl<T: Display> Wrapper<T> {
   |         ^^^^^^^  ----------
   |         |
   |         unsatisfied trait bound introduced here
note: the trait `std::fmt::Display` must be implemented
  --> /rustc/ded5c06cf21d2b93bffd5d884aa6e96934ee4234/library/core/src/fmt/mod.rs:1007:1

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0599`.
```

- ★★ 진단이 「없다」고 하지 않는다 — **`the method show exists … but its trait bounds were not satisfied`**,
  즉 「**있는데 조건이 안 맞는다**」다.
- ★ `note:` 가 **그 조건을 만든 `impl` 블록의 줄 번호**를 짚어 준다(`ex.rs:10:9`, 캐럿이 `Display` 글자에).
  **어느 블록 때문인지 진단이 직접 알려 준다.**
- `Wrapper::new` 는 경계 없는 블록에 있으므로 **같은 타입에서 그대로 된다** — 이것이 나누는 값이다.
- ★★ **나눈 것이 컴파일 결과에는 안 남고 문서에는 남는다**(11번 답). 블록 수는 **읽는 사람에게 보이는 설계 선택**이다.

### 9. E0599 의 네 얼굴 — 번호가 아니라 문구를 읽는다

**출력**

| 문구 | 무엇이 문제인가 | 처방 | 이 문서의 자리 |
|---|---|---|---|
| `method not found in X` | 그 이름이 **아예 없다** | 오타 확인 | 아래 블록 |
| `this is an associated function, not a method` | **연관 함수**다(리시버가 없다) | `T::name()` 으로 | 2번·6번 |
| `exists … but its trait bounds were not satisfied` | **있는데 경계 불만족** | 경계를 만족시키거나 다른 타입으로 | 8번 |
| `field, not a method` | **필드**다 | `(v.f)()` | 4번 |
| `items from traits can only be used if the trait is in scope` | 구현은 있는데 **트레이트가 스코프 밖** | `use` 를 추가 | 아래 블록 |

**없는 이름을 부르면 — `impl` 블록은 하나도 나열되지 않는다.**

```text
===== 소스: ex.rs =====
// impl 블록이 셋인 타입에서 없는 메서드를 부르면 진단이 무엇을 나열하나
struct Counter { n: u32 }

impl Counter {
    fn new() -> Self { Counter { n: 0 } }
}

impl Counter {
    fn get(&self) -> u32 { self.n }
}

impl Counter {
    fn reset(&mut self) { self.n = 0; }
}

fn main() {
    let mut c = Counter::new();
    c.reset();
    println!("{}", c.get());
    c.increment();
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0599]: no method named `increment` found for struct `Counter` in the current scope
  --> ex.rs:20:7
   |
 2 | struct Counter { n: u32 }
   | -------------- method `increment` not found for this struct
...
20 |     c.increment();
   |       ^^^^^^^^^
   |
help: there is a method `reset` with a similar name
   |
20 -     c.increment();
20 +     c.reset();
   |

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0599`.
```

**왜 그런가**

- ★★ **`impl` 블록을 셋 뒀는데 진단은 하나도 안 짚는다.** 짚는 것은 **구조체 선언 줄**뿐이고,
  나머지는 **「비슷한 이름」 제안**이다(`reset` 을 권했다).
- ★ **나열은 「후보가 실제로 있을 때」만** 나온다 — 6번의 `candidate #1`·`#2`, 8번의 `note: trait bound … was not satisfied` 가 그 경우다.
  **「어디를 뒤졌나」를 보여 주는 진단은 없다.** 그래서 이 주제는 `cargo doc` 이라는 창을 따로 쓴다(11번).

**구현은 있는데 트레이트가 스코프 밖이면 — 또 다른 문구다.**

```text
===== 소스: ex.rs =====
// 메서드는 impl 안에 있는데 트레이트가 스코프에 없으면 — 진단이 어느 impl 을 짚나
mod shape {
    pub trait Area { fn area(&self) -> f64; }
    pub struct Square { pub side: f64 }
    impl Area for Square { fn area(&self) -> f64 { self.side * self.side } }
}

use shape::Square;

fn main() {
    let s = Square { side: 3.0 };
    println!("{}", s.area());
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0599]: no method named `area` found for struct `Square` in the current scope
  --> ex.rs:12:22
   |
 3 |     pub trait Area { fn area(&self) -> f64; }
   |                         ---- the method is available for `Square` here
 4 |     pub struct Square { pub side: f64 }
   |     ----------------- method `area` not found for this struct
...
12 |     println!("{}", s.area());
   |                      ^^^^ method not found in `Square`
   |
   = help: items from traits can only be used if the trait is in scope
help: trait `Area` which provides `area` is implemented but not in scope; perhaps you want to import it
   |
 2 + use crate::shape::Area;
   |

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0599`.
```

★ **`the method is available for Square here`** — 「찾았는데 부를 수 없다」다. `use` 한 줄을 그대로 준다.

### 10. E0616 / E0603 — 그리고 생성 에러는 E0063 / E0560

**출력**

```text
===== 소스: ex.rs =====
// 같은 모듈 안에서는 필드가 다 보이나 — mod 로 감싸면?
mod geo {
    pub struct Point { pub x: i32, y: i32 }   // y 에만 pub 이 없다

    impl Point {
        pub fn new(x: i32, y: i32) -> Self { Point { x, y } }
        pub fn y(&self) -> i32 { self.y }     // 같은 모듈 안에서는 y 가 보인다
    }

    struct Hidden { pub v: i32 }              // 타입 자체에 pub 이 없다
    impl Hidden { pub fn new() -> Self { Hidden { v: 1 } } }
}

fn main() {
    let p = geo::Point::new(1, 2);
    println!("x = {}", p.x);
    println!("y() = {}", p.y());
    println!("y  = {}", p.y);
    let h = geo::Hidden::new();
    println!("{}", h.v);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0603]: struct `Hidden` is private
  --> ex.rs:19:18
   |
19 |     let h = geo::Hidden::new();
   |                  ^^^^^^ private struct
   |
note: the struct `Hidden` is defined here
  --> ex.rs:10:5
   |
10 |     struct Hidden { pub v: i32 }              // 타입 자체에 pub 이 없다
   |     ^^^^^^^^^^^^^

error[E0616]: field `y` of struct `Point` is private
  --> ex.rs:18:27
   |
18 |     println!("y  = {}", p.y);
   |                           ^ private field
   |
help: a method `y` also exists, call it with parentheses
   |
18 |     println!("y  = {}", p.y());
   |                            ++

error: aborting due to 2 previous errors

Some errors have detailed explanations: E0603, E0616.
For more information about an error, try `rustc --explain E0603`.
```

**왜 그런가**

- ★ **같은 모듈 안에서는 `y` 가 그냥 보인다** — `impl Point` 의 `pub fn y(&self)` 가 `self.y` 를 읽는 데 아무 표시가 없었다.
  가시성은 **모듈 경계**에서만 작동한다.
- **두 에러가 다른 것을 가린다.**

| 번호 | 무엇이 안 보이나 | 고치는 법 |
|---|---|---|
| **E0603** | **타입 자체**가 비공개 | `pub struct Hidden` |
| **E0616** | 타입은 보이는데 **필드**가 비공개 | `pub y: i32` 또는 접근자 메서드 |

- ★★ **`pub struct` 를 써도 필드는 안 열린다.** `pub struct Point { pub x: i32, y: i32 }` 에서 `x` 만 열렸다 —
  **칸마다 따로** 정한다.
- ★★ **E0616 의 `help:` 가 관용구를 권한다** — `p.y` 가 막히자 **`p.y()`** 를 쓰라고 한다.
  **접근자를 필드와 같은 이름으로 짓는 것**이 그 관용구이고, 4번에서 본 「이름 공간이 다르다」가 그것을 가능하게 한다.
- ★ 모듈 시스템 자체(`pub(crate)`·경로·파일 배치)는 목록의 **45번 주제**가 정본이다.

**생성 에러 둘.**

```text
===== 소스: ex.rs =====
// 필드를 빠뜨리면 · 없는 필드를 주면
struct Point { x: i32, y: i32, z: i32 }

fn main() {
    let a = Point { x: 1 };
    let b = Point { x: 1, y: 2, z: 3, w: 4 };
    println!("{} {}", a.x, b.x);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0063]: missing fields `y` and `z` in initializer of `Point`
 --> ex.rs:5:13
  |
5 |     let a = Point { x: 1 };
  |             ^^^^^ missing `y` and `z`

error[E0560]: struct `Point` has no field named `w`
 --> ex.rs:6:39
  |
6 |     let b = Point { x: 1, y: 2, z: 3, w: 4 };
  |                                       ^ `Point` does not have this field
  |
  = note: all struct fields are already assigned

error: aborting due to 2 previous errors

Some errors have detailed explanations: E0063, E0560.
For more information about an error, try `rustc --explain E0063`.
```

★ **E0063**(빠뜨림 — 빠진 이름을 전부 대 준다)과 **E0560**(없는 필드)이다.
**필드를 하나 더하면 모든 생성 자리가 E0063 으로 깨진다** — 이것이 안전망이므로
**새 필드를 놓치고 싶지 않은 타입에는 `..Default::default()` 를 쓰지 않는다.**

### 11. 세 덩어리로 나온다 — 합쳐지지 않는다

**출력**

```text
===== 소스: ex.rs =====
//! cargo doc 이 impl 블록을 몇 덩어리로 내놓나 — 이 파일이 크레이트의 src/lib.rs 가 된다
use std::fmt::Display;

/// 경계가 다른 impl 블록을 셋 가진 타입
pub struct Wrapper<T> { pub inner: T }

impl<T> Wrapper<T> {
    /// 경계 없는 블록
    pub fn new(inner: T) -> Self { Wrapper { inner } }
}

impl<T: Display> Wrapper<T> {
    /// Display 경계가 붙은 블록
    pub fn show(&self) -> String { format!("[{}]", self.inner) }
}

impl<T: Clone> Wrapper<T> {
    /// Clone 경계가 붙은 블록
    pub fn duplicate(&self) -> T { self.inner.clone() }
}
===== mkdir -p dc/src && cp ex.rs dc/src/lib.rs && printf '[package]\nname = "dc"\nversion = "0.1.0"\nedition = "2021"\n' > dc/Cargo.toml && (cd dc && cargo doc --no-deps --quiet) =====
===== grep -o 'id="\(impl-Wrapper%3CT%3E[^"]*\|method\.[a-z_]*\)"' dc/target/doc/dc/struct.Wrapper.html =====
id="impl-Wrapper%3CT%3E"
id="method.new"
id="impl-Wrapper%3CT%3E-1"
id="method.show"
id="impl-Wrapper%3CT%3E-2"
id="method.duplicate"
id="method.type_id"
id="method.borrow"
id="method.borrow_mut"
id="method.from"
id="method.into"
id="method.try_from"
id="method.try_into"
(종료 코드 0)
```

**왜 그런가**

- ★★ **세 덩어리 그대로**다. 앵커가 `impl-Wrapper%3CT%3E` · `-1` · `-2` 셋이고,
  **각각 바로 뒤에 그 블록의 메서드가 하나씩** 붙어 있다(`new` · `show` · `duplicate`).
  `%3C`·`%3E` 는 `<`·`>` 의 URL 인코딩이다.
- **기계적으로 세는 법** — 위 두 번째 배너가 그것이다. `grep -o` 로 **앵커 id 만 뽑아** 문서 순서대로 찍는다.
  눈으로 HTML 을 읽지 않고 **세고 대조할 수 있는 형태**로 만드는 것이 요점이다.
- **따라 붙은 일곱 메서드**(`type_id`·`borrow`·`borrow_mut`·`from`·`into`·`try_from`·`try_into`)는
  내가 쓴 것이 아니다 — 표준 라이브러리의 **포괄 구현**(blanket impl)이 모든 타입에 딸려 오는 것이고,
  페이지에서는 `<h2 id="blanket-implementations">` 절에 모인다.
  `Send`·`Sync`·`Unpin` 같은 자동 구현은 `<h2 id="synthetic-implementations">` 로 따로 모인다.

```text
   cargo doc 이 만든 페이지의 뼈대

   <h2 id="fields">                       ← pub 필드
   <h2 id="implementations">              ← 내가 쓴 세 블록이 전부 여기 아래
        ├ impl-Wrapper%3CT%3E      : impl<T> Wrapper<T>            → new
        ├ impl-Wrapper%3CT%3E-1    : impl<T: Display> Wrapper<T>   → show
        └ impl-Wrapper%3CT%3E-2    : impl<T: Clone> Wrapper<T>     → duplicate
   <h2 id="synthetic-implementations">    ← Send/Sync/Unpin 등 자동 구현
   <h2 id="blanket-implementations">      ← From/Into/TryFrom 등 포괄 구현
```

★ **`impl` 을 몇 개로 나눴는지는 바이너리에 안 남고 문서에는 남는다.** 8번의 결론이 여기서 눈에 보인다.

**`derive(Debug)` 없이 `{:?}` 를 쓰면 E0277 이다.**

```text
===== 소스: ex.rs =====
// derive(Debug) 없이 {:?} 를 쓰면
struct Point { x: i32, y: i32 }

fn main() {
    let p = Point { x: 1, y: 2 };
    println!("{:?}", p);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0277]: `Point` doesn't implement `Debug`
 --> ex.rs:6:22
  |
6 |     println!("{:?}", p);
  |               ----   ^ `Point` cannot be formatted using `{:?}` because it doesn't implement `Debug`
  |               |
  |               required by this formatting parameter
  |
  = help: the trait `Debug` is not implemented for `Point`
  = note: add `#[derive(Debug)]` to `Point` or manually `impl Debug for Point`
  = note: this error originates in the macro `$crate::format_args_nl` which comes from the expansion of the macro `println` (in Nightly builds, run with -Z macro-backtrace for more info)
help: consider annotating `Point` with `#[derive(Debug)]`
  |
2 + #[derive(Debug)]
3 | struct Point { x: i32, y: i32 }
  |

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0277`.
```

**`{:?}` 와 `{:#?}` 의 차이 — 세 형태에 각각.**

```text
===== 소스: ex.rs =====
// {:?} 와 {:#?} 는 무엇이 다른가 — 세 종류를 다 찍어 본다
#[derive(Debug)]
struct Point { x: i32, y: i32 }
#[derive(Debug)]
struct Meters(f64);
#[derive(Debug)]
struct Marker;

fn main() {
    let p = Point { x: 1, y: 2 };
    println!("합    {}", p.x + p.y);          // 필드를 실제로 읽는다(dead_code 경고 제거)
    println!("{:?}", p);
    println!("{:#?}", p);
    let m = Meters(1.5);
    println!("안쪽  {}", m.0);
    println!("{:?} / {:#?}", m, Meters(1.5));
    println!("{:?} / {:#?}", Marker, Marker);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
합    3
Point { x: 1, y: 2 }
Point {
    x: 1,
    y: 2,
}
안쪽  1.5
Meters(1.5) / Meters(
    1.5,
)
Marker / Marker
(종료 코드 0)
```

- **`{:?}`** 는 한 줄, **`{:#?}`** 는 **여러 줄 + 4칸 들여쓰기 + 꼬리 쉼표**다.
- ★ **세 형태가 각각 다르게 찍힌다** — 이름 있는 것은 `{ }`, 튜플은 `( )`, 유닛은 **이름만**.
  `{:?}` 출력만 봐도 어느 형태인지 읽을 수 있다.
- `derive` 자체는 [목록의 **27번 주제**](../27-derive-macros-debug-clone-partialeq-default-hash/), `Display`/`Debug` 직접 구현은 목록의 **48번 주제**가 정본이다.

### 12. 에러 번호 지도

**출력**

| 번호 | 언제 나나 | 이 주제의 실측 |
|---|---|---|
| **E0063** | 구조체 생성에서 **필드를 빠뜨렸다** | 10번 |
| **E0560** | 구조체에 **없는 필드**를 줬다 | 10번 |
| **E0423** | 이름 있는 구조체의 **이름을 값으로** 썼다 | 2-summary (1) |
| **E0599** | ★ **네 얼굴** — 없다 / 연관 함수다 / 경계 불만족 / 트레이트 스코프 밖 | 2·4·6·8·9번 |
| **E0061** | 인자 개수가 모자라다 — **메서드를 `::` 으로** 부르면 여기로 온다 | 2번 |
| **E0592** | 같은 이름을 **두 고유 `impl`** 에 정의했다(정의 쪽) | 6번 |
| **E0034** | 호출 자리에서 **후보가 여럿**이다(호출 쪽) | 6번 |
| **E0382** | 이동한 값을 다시 썼다 — `self` 리시버 · `..other` 부분 이동 | 1·5번 |
| **E0596** | `mut` 아닌 바인딩에서 **`&mut self`** 를 불렀다 | 5번 |
| **E0502** | `&self` 빌림 중에 `&mut self` 를 불렀다 | 5번 · [**10번 주제**](../10-borrowing-and-aliasing-rules/)가 정본 |
| **E0616** | 다른 모듈에서 **비공개 필드**를 읽었다 | 10번 |
| **E0603** | **타입 자체**가 비공개다 | 10번 |
| **E0411** | `impl` 밖에서 **`Self`** 를 썼다 | 7번 |
| **E0277** | 트레이트가 구현 안 됐다 — `Debug` 없이 `{:?}` | 11번 |

**왜 그런가**

- ★ **번호 없는 진단**을 이 주제에서 만났다 —
  **`error: the Self constructor can only be used with tuple or unit structs`**(7번).
  `--explain` 으로 찾아볼 수 없는 부류이고, [**12번 주제**](../12-lifetime-annotations-and-elision/)에서도 같은 부류를 만났다.
- **`&self` 메서드 하나가 값 전체를 잡는 이유**는 [**10번 주제**](../10-borrowing-and-aliasing-rules/),
  **그 처방(분할 빌림·`mem::take` 등)** 은 [**11번 주제**](../11-borrow-checker-rejections/)가 정본이다.
- **참조를 필드로 담는 구조체**는 [목록의 **13번 주제**](../13-struct-references-and-static/)가 정본이다 —
  이 주제의 예제는 **전부 소유한 값만** 담았다. `struct X<'a> { r: &'a str }` 의 제약은 거기다.
- ★ **객체·캡슐화 일반**은 [`../../../../oop-basics/`](../../../../oop-basics/) 가 정본이다.
  **그쪽은** 클래스·정보 은닉·상속·다형성의 **일반론**, **여기는** Rust 의 **구조체 세 종류와 `impl` 문법**이다.
  ★ Rust 에는 **클래스도 상속도 없다** — 데이터는 `struct`, 동작은 `impl`, 공통 표면은 트레이트로 갈라져 있다.
- **`impl Trait for Type`**(트레이트 구현)은 [목록의 **25번 주제**](../25-traits-definition-impl-default-methods-and-associated-types/)다.
  이 주제가 다룬 `impl Type { }` 은 **고유 impl**(inherent impl)이라고 부른다.
- ★ **에러 메시지가 고친 코드를 그대로 준 자리**가 이 주제에 넷 있었다 —
  E0277 의 `2 + #[derive(Debug)]` · E0599 의 `(w.render)()` · E0599 의 `<Counter as Make>::build()` ·
  E0596 의 `let mut c`. **`help:` 가 여럿이면 다 읽는다.**

---

## 실행 검증

| 실험 (`ex.rs`) | 무엇을 확인했나 | 결과 |
|---|---|---|
| 세 형태 선언·생성·접근·구조 분해 | **통과** — `3 4` / `1.5` / `Marker` / 분해 / `..` 로 일부만 | 2-summary (1) |
| 튜플 구조체 이름을 `fn(f64) -> Meters` 에 담기 | **통과** — 생성자가 **진짜 함수**다 | 2-summary (1) |
| 이름 있는 구조체 이름을 값으로 | **E0423** — 중괄호 리터럴을 권함 | 12 |
| `..base` + `String` 필드 | **E0382** `borrow of partially moved value` | 1 |
| `..base` + `Copy` 필드만 | **통과** — 원본이 살아 있다 | 1 |
| 연관 함수를 `.` 으로 · 메서드를 `::` 으로 | **E0599** + **E0061** — ★ 성격이 다르다 | 2 |
| ★ `size_of`/`align_of` 아홉 타입 | **0바이트 넷**(`Unit`·`Empty()`·`()`·`[u8; 0]`), 정렬은 전부 **1** | 3 |
| ★ newtype 대 안쪽 타입 | **`8/8` 로 같다** | 3 |
| ★ 필드 오프셋 `repr(Rust)` 대 `repr(C)` | **`a@4 b@0`** 대 **`a@0 b@4`** — 재배치가 일어났다 | 3 |
| 필드와 메서드 동명 | **통과** — `10` / `20` / `메서드 render` / `필드 render` | 4 |
| 클로저 필드를 `.` 으로 | **E0599** `field, not a method` + `(w.render)()` 권유 | 4·9 |
| `self` 리시버 메서드 두 번 | **E0382** + `note:` 가 **리시버**를 짚음 | 5 |
| `&mut self` 를 `mut` 없는 바인딩에서 | **E0596** — `help:` 가 **선언 줄**을 고치라 함 | 5 |
| `&self` 빌림 중 `&mut self` | **E0502** — 값 전체가 잡힌다 | 5 |
| `Self` 열두 자리 한 파일 | **통과** — 성격으로 묶으면 **세 갈래** | 7 |
| ★ 이름 있는 구조체에서 `Self` 를 값으로 | **번호 없는 error** — 튜플·유닛만 된다 | 7 |
| `impl` 밖의 `Self` | **E0411** ×2 — 타입 자리와 값 자리가 따로 걸림 | 7 |
| `impl` 블록 셋(이름 안 겹침) | **통과** — `3` | 8 |
| 경계 다른 `impl` 에서 미충족 호출 | **E0599** `trait bounds were not satisfied` + **블록 줄 번호** | 8 |
| 같은 이름 두 고유 `impl` | **E0592** + **E0034**(`candidate #1`·`#2`) | 6 |
| 고유 `impl` + 트레이트 동명 연관 함수 | **E0599** + `candidate #1`(트레이트)·`#2`(impl) + 완전 수식 문법 | 6 |
| 없는 메서드 (블록 셋) | **E0599** — ★ `impl` 블록을 **하나도 나열 안 함** | 9 |
| 트레이트가 스코프 밖 | **E0599** + `use crate::shape::Area;` 를 그대로 줌 | 9 |
| `mod` 밖에서 비공개 필드·비공개 타입 | **E0616** + **E0603** — `help:` 가 동명 접근자를 권함 | 10 |
| 필드 빠뜨림 · 없는 필드 | **E0063** + **E0560** | 10 |
| ★ `cargo doc --no-deps` 후 앵커 세기 | **세 덩어리** — `impl-Wrapper%3CT%3E`·`-1`·`-2` | 11 |
| `Debug` 없이 `{:?}` | **E0277** + `#[derive(Debug)]` 를 통째로 줌 | 11 |
| `{:?}` 대 `{:#?}` 세 형태 | **통과** — 4칸 들여쓰기·꼬리 쉼표. 형태별로 괄호가 다름 | 11 |

**구현·설정에 달린 항목**(다시 찍을 자리)

| 항목 | 무엇에 달렸나 |
|---|---|
| ★ **필드 오프셋 `a@4`·`b@0`** | **rustc 판·대상 플랫폼.** `repr(Rust)` 는 재배치 자유를 갖는다 — `#[repr(C)]` 만 고정이다 |
| ★ `Named` 와 `Reordered` 의 **크기가 같은 것** | **관찰**이지 보장이 아니다 |
| ★ **newtype 이 안쪽과 같은 크기** | **구현.** Reference 는 단일 필드 레이아웃을 약속하지 않는다 |
| `size_of` 가 **0**인 것(ZST) | **언어.** ZST 는 언어 개념이다 |
| `align_of` **최솟값 1** | **언어** |
| **에러 번호**가 상황별로 갈리는 것 | **rustc 구현.** 번호는 안정적이고 **문구·`help` 는 바뀐다** |
| ★ **E0599 한 번호에 문구가 넷** | **rustc 구현** |
| ★ **번호 없는 진단이 있는 것** | **rustc 구현** |
| `candidate #1`·`#2` 표기 | **rustc 의 진단 표기** |
| 비슷한 이름 제안(`reset` 을 권한 것) | **rustc 의 편집 거리 구현** |
| `/rustc/<해시>/library/…` 경로 | **이 툴체인의 빌드 해시.** 판이 바뀌면 달라진다 |
| 앵커 id 의 **`%3C` 인코딩·`-1` 접미** | **rustdoc 구현** |
| 포괄 구현 **일곱 개의 목록** | **std 판.** 트레이트가 추가되면 늘어난다 |
| `{:#?}` 의 **4칸 들여쓰기** | **std 의 `Formatter` 구현** |
| **세 형태·`impl` 다중·이름 공간 분리·필드 기본 비공개·`Self` 유효 범위** | **전부 언어 보장.** 실측과 Reference 가 일치했다 |
