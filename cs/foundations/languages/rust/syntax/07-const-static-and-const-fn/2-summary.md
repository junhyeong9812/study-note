# rust/syntax/07 — 상수·`static`·`const fn` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [The Rust Reference](https://doc.rust-lang.org/reference/) 의 Constant items ·
> Static items · Constant evaluation 절 · [Edition Guide](https://doc.rust-lang.org/edition-guide/rust-2024/static-mut-references.html) 의
> Disallow references to `static mut` · `rustc --explain E0005` / `E0015` / `E0080` / `E0133` / `E0428`.
> 이 머신의 `rust-docs`(1.92.0)를 열어 확인했고, 인용은 그 판의 원문이다.
> **실행 검증** — 이 문서의 모든 출력·에러·경고는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서 돌렸다.\
> ★ **상수 평가·주소·해제 시점이 걸린 프로그램은 전부 두 번 돌렸다** — `rustc --edition 2021 ex.rs`(디버그)와\
> `rustc --edition 2021 -O ex.rs`(릴리스). 에디션이 갈리는 자리는 **`rustc --edition 2024`** 로 한 번 더 돌렸다.
> **버전** — `const`·`static`·`const fn` 문법은 이 문서가 쓰는 범위 안에서 전부 안정판이다.\
> **2024 에디션은 1.85.0(2025-02-20)에 안정화**되었다(목록 [README](../README.md) 가 고정한 사실).\
> `clippy` 출력은 `clippy 0.1.92` 다. `!` 타입 표기처럼 **안정판에서 못 쓰는 것은 이 문서에 쓰지 않았다.**
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**`const` 는 도장이고 `static` 은 게시판에 붙은 한 장이다.**

도장은 쓸 때마다 종이에 **새 자국**을 남긴다. 자국 열 개는 서로 남남이다.\
게시판의 한 장은 누가 보든 **그 한 장**이다. 고치면 모두가 고쳐진 것을 본다.

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 도장 | `const` — 이름이 붙은 **값** |
| 도장을 찍은 자국 | `const` 를 쓴 **자리마다 새로 생기는 임시값** |
| 게시판에 붙은 한 장 | `static` — 프로그램 안에 **딱 하나인 할당** |
| 게시판을 고치려면 관리자 열쇠가 필요하다 | `static mut` 에는 **`unsafe`** 가 필요하다 |
| 책상 위 메모지 | `let` — 스코프가 끝나면 버린다 |
| 도장을 **미리 파 두는 공정** | `const fn` — 컴파일 타임에 값을 만들어 두는 함수 |

```text
   const LIMIT: i32 = 100;              static TOTAL: i32 = 100;

   쓸 때마다 새 자국                      프로그램에 한 칸
   +--------+  +--------+  +--------+    +------------------+
   | 사본 1 |  | 사본 2 |  | 사본 3 |    |  TOTAL = 100     |  <- 모두가 이 칸을 본다
   +--------+  +--------+  +--------+    +------------------+
       ^           ^           ^                ^   ^   ^
     첫 사용     둘째 사용    셋째 사용        첫 사용 둘째 셋째
```

**언어도 똑같은 구조다.** 값이 하나뿐인 `AtomicI32` 를 세 번 올려 보면 바로 갈린다.

```text
const  세 번 올린 뒤 = 0
static 세 번 올린 뒤 = 3
```

- `const` 쪽은 **매번 새 사본을 올리고 버렸다.** 그래서 0이다.
- `static` 쪽은 **한 칸을 세 번 올렸다.** 그래서 3이다.
- ★ **에러도 경고도 없다.** 디버그·릴리스 둘 다 같은 답이었다. 「`const` 로 둔 카운터」는 조용히 안 센다.

> **상수 항목(constant item)** — 이름이 붙은 값. 쓰는 자리마다 **그 자리에 복사돼 들어간다**.\
> 예: `const LIMIT: i32 = 100;` 을 세 곳에서 쓰면 100이라는 값이 세 곳에 각각 놓인다.

> **정적 항목(static item)** — 프로그램이 도는 내내 한 자리를 차지하는 **할당**.\
> 예: `static TOTAL: i32 = 100;` 은 어디서 `&TOTAL` 을 해도 같은 칸을 가리킨다.

> **`const fn`** — 상수 자리에서 부를 수 있게 표시한 함수.\
> 예: `const fn square(n: usize) -> usize { n * n }` 은 `[0u8; square(4)]` 처럼 배열 길이에 쓸 수 있다.

Reference 가 두 문장으로 못 박는다.

> Constants are essentially inlined wherever they are used, meaning that they are copied directly into the relevant context when used.
> (Reference, Constant items)

> A static item is similar to a constant, except that it represents an allocation in the program …
> All references and raw pointers to the static refer to the same allocation.
> (Reference, Static items)

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. `const` 와 `static` 은 **메모리에서 무엇이 다른가** — 그리고 그 차이가 **코드의 답을 바꾸는 자리**는 어디인가.
2. `const fn` 은 **언제 컴파일 타임에 계산되는가** — 그게 보장인가 아닌가.
3. `const` 는 왜 **타입을 적어야 하고 섀도잉이 안 되는가** — `let` 과 무엇이 다른 종류의 이름인가.

## 동작 방식

### (1) ★ `const` 는 쓸 때마다 새 값이고 `static` 은 한 칸이다

**언제 쓰나** — 고정값을 모듈 최상위에 둘 때. **둘 중 무엇을 고르냐가 이 주제의 전부다.**

```rust
use std::sync::atomic::{AtomicI32, Ordering};

const C_COUNT: AtomicI32 = AtomicI32::new(0);
static S_COUNT: AtomicI32 = AtomicI32::new(0);

fn main() {
    C_COUNT.fetch_add(1, Ordering::SeqCst);
    C_COUNT.fetch_add(1, Ordering::SeqCst);
    C_COUNT.fetch_add(1, Ordering::SeqCst);

    S_COUNT.fetch_add(1, Ordering::SeqCst);
    S_COUNT.fetch_add(1, Ordering::SeqCst);
    S_COUNT.fetch_add(1, Ordering::SeqCst);

    println!("const  세 번 올린 뒤 = {}", C_COUNT.load(Ordering::SeqCst));
    println!("static 세 번 올린 뒤 = {}", S_COUNT.load(Ordering::SeqCst));
}
```

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
const  세 번 올린 뒤 = 0
static 세 번 올린 뒤 = 3
(종료 코드 0)
===== 릴리스: rustc --edition 2021 -O ex.rs -o ex_rel =====
const  세 번 올린 뒤 = 0
static 세 번 올린 뒤 = 3
(종료 코드 0)
```

★ **도식이 본체다.**

```text
  const C_COUNT                                static S_COUNT
  +-----+     +-----+     +-----+              +-----------+
  | 0->1|     | 0->1|     | 0->1|              |  0->1->2->3|
  +-----+     +-----+     +-----+              +-----------+
     |           |           |                       ^  ^  ^
   버린다      버린다      버린다                  세 호출이 같은 칸을 친다
     |
     v
  load 는 또 새 사본을 읽는다 -> 0                 load 도 그 칸을 읽는다 -> 3
```

그림 해설 (한 단계씩):

- `C_COUNT.fetch_add(...)` 한 줄마다 **그 자리에 `AtomicI32::new(0)` 이 새로 놓인다.**
- 올린 값은 그 문이 끝나면서 **버려진다.** 다음 줄은 다시 0에서 시작한다.
- 마지막 `load` 도 예외가 아니다 — **또 하나의 새 사본을 읽으므로** 0이다.
- `static` 쪽은 세 호출과 `load` 가 전부 **같은 할당**을 본다.

비용 — `const` 쪽은 사본을 만드는 비용, `static` 쪽은 프로그램 내내 차지하는 한 칸.\
둘 다 작지만 **답이 다르다**는 것이 요점이다.

### (2) 해제 시점이 그 차이를 눈으로 보여 준다

**언제 쓰나** — 「사본이 몇 개 생기나」를 확인하고 싶을 때. `Drop` 을 붙이면 출력 순서로 드러난다.

```rust
struct D(&'static str);
impl Drop for D {
    fn drop(&mut self) { println!("        [해제] {}", self.0); }
}

const  TEMPLATE: D = D("const");
static GLOBAL:   D = D("static");

fn main() {
    println!("(1) const 를 두 번 읽는다");
    println!("    {}", TEMPLATE.0);
    println!("    {}", TEMPLATE.0);

    println!("(2) static 을 두 번 읽는다");
    println!("    {}", GLOBAL.0);
    println!("    {}", GLOBAL.0);

    println!("(3) main 끝");
}
```

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
(1) const 를 두 번 읽는다
    const
        [해제] const
    const
        [해제] const
(2) static 을 두 번 읽는다
    static
    static
(3) main 끝
(종료 코드 0)
===== 릴리스: rustc --edition 2021 -O ex.rs -o ex_rel =====
(1) const 를 두 번 읽는다
    const
        [해제] const
    const
        [해제] const
(2) static 을 두 번 읽는다
    static
    static
(3) main 끝
(종료 코드 0)
```

```text
   const 를 두 번 썼다                      static 을 두 번 썼다
   +----------------------+                +----------------------+
   | 임시값 #1 생성        |                | 그 한 칸을 읽는다     |
   |   읽고 -> [해제]      |                |   (아무 일도 없다)    |
   | 임시값 #2 생성        |                | 그 한 칸을 읽는다     |
   |   읽고 -> [해제]      |                |   (아무 일도 없다)    |
   +----------------------+                +----------------------+
     해제 줄 2개                              해제 줄 0개
```

그림 해설 (한 단계씩):

- `const` 는 **쓴 횟수만큼 값이 만들어지고 그 문이 끝날 때 해제된다.** 해제 줄이 두 번 찍힌다.
- `static` 은 **해제가 아예 없다.** Reference 가 그렇게 규정한다.

  > Static items do not call drop at the end of the program.
  > (Reference, Static items)

- 그래서 `static` 에 둔 값의 소멸자는 **프로그램이 끝나도 안 돈다** — 파일 닫기·플러시를 거기 기대면 안 된다.
- 해제 시점 일반론은 [**08번 주제**](../08-ownership-and-move/) 와 [목록의 **09번 주제**](../09-copy-clone-and-drop/)가 정본이다.

비용 — `const` 쪽은 쓸 때마다 생성·소멸 비용이 든다. 큰 값을 `const` 로 두면 그게 코드에 퍼진다.

### (3) `const` 를 고치려 들면 — 경고 한 줄로 끝난다

**언제 쓰나** — 실수로 상수를 「변수처럼」 다뤘을 때. **에러가 아니라 경고다.**

```rust
const BUF: [i32; 3] = [0, 0, 0];
fn main() {
    BUF[0] = 9;
    println!("{:?}", BUF);
}
```

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
warning: attempting to modify a `const` item
 --> ex.rs:3:5
  |
3 |     BUF[0] = 9;
  |     ^^^^^^^^^^
  |
  = note: each usage of a `const` item creates a new temporary; the original `const` item will not be modified
note: `const` item defined here
 --> ex.rs:1:1
  |
1 | const BUF: [i32; 3] = [0, 0, 0];
  | ^^^^^^^^^^^^^^^^^^^
  = note: `#[warn(const_item_mutation)]` on by default

warning: 1 warning emitted

[0, 0, 0]
(종료 코드 0)
```

- **컴파일러가 규칙을 문장으로 말해 준다** — `each usage of a const item creates a new temporary; the original const item will not be modified`.
- **린트는 `const_item_mutation`이고 기본이 경고다.** 프로그램은 돌고 `[0, 0, 0]` 을 찍는다.
- ★ **경고도 출력이다.** 이 자리는 에러가 안 나므로 경고를 안 읽으면 못 잡는다.

비용 — 없음. 다만 **버그가 조용히 산다.**

### (4) `const` 의 주소는 보장이 아니다 — `static` 의 한 칸만 보장이다

**언제 쓰나** — 「같은 것인가」를 주소로 판정하려 할 때. **직관과 반대로 나온다.**

```rust
const LIMIT: i32 = 100;
static TOTAL: i32 = 100;

#[inline(never)]
fn c_addr1() -> usize { &LIMIT as *const i32 as usize }
#[inline(never)]
fn c_addr2() -> usize { &LIMIT as *const i32 as usize }
#[inline(never)]
fn s_addr1() -> usize { &TOTAL as *const i32 as usize }
#[inline(never)]
fn s_addr2() -> usize { &TOTAL as *const i32 as usize }

fn main() {
    let (c1, c2, s1, s2) = (c_addr1(), c_addr2(), s_addr1(), s_addr2());
    println!("&LIMIT(const)  #1 = {c1:#x}");
    println!("&LIMIT(const)  #2 = {c2:#x}   같은가? {}", c1 == c2);
    println!("&TOTAL(static) #1 = {s1:#x}");
    println!("&TOTAL(static) #2 = {s2:#x}   같은가? {}", s1 == s2);
    println!("const 과 static 이 같은 주소인가? {}", c1 == s1);
}
```

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
&LIMIT(const)  #1 = 0x57d3a63a2788
&LIMIT(const)  #2 = 0x57d3a63a2788   같은가? true
&TOTAL(static) #1 = 0x57d3a63a2784
&TOTAL(static) #2 = 0x57d3a63a2784   같은가? true
const 과 static 이 같은 주소인가? false
(종료 코드 0)
===== 릴리스: rustc --edition 2021 -O ex.rs -o ex_rel =====
&LIMIT(const)  #1 = 0x63037b8b0ab4
&LIMIT(const)  #2 = 0x63037b8b0ab4   같은가? true
&TOTAL(static) #1 = 0x63037b8b0ab4
&TOTAL(static) #2 = 0x63037b8b0ab4   같은가? true
const 과 static 이 같은 주소인가? true
(종료 코드 0)
```

★ **근거로 쓸 칸을 먼저 선언한다.**

| 칸 | 흔들리나 | 왜 |
|---|---|---|
| 주소의 **절댓값**(`0x57d3…`) | **흔들린다** | 실행마다 다르다(같은 릴리스 바이너리를 세 번 돌려 확인했다) |
| **같은가/다른가** 관계 | 한 빌드 안에서는 안 흔들린다 | 세 판 모두 `true`/`true`/`true` 였다 |
| **빌드 프로필 사이**의 관계 | **흔들린다** | 마지막 줄이 디버그 `false` → 릴리스 `true` 로 뒤집혔다 |

```text
  디버그                                   릴리스 (-O)
  +---------------------------+            +---------------------------+
  |  ...2784 : static TOTAL   |            |  ...ab4 : static TOTAL    |
  |  ...2788 : const 승격본    |            |          = const 승격본   |  <- 한 칸으로 합쳐졌다
  +---------------------------+            +---------------------------+
   const != static (false)                  const == static (true)
```

그림 해설 (한 단계씩):

- `&LIMIT` 를 두 번 해도 **같은 주소가 나왔다** — 「`const` 니까 매번 다른 주소」는 **틀린 예측이다.**\
  값이 승격(promotion)될 수 있으면 컴파일러가 읽기 전용 자리에 하나 만들어 재사용한다.
- 그런데 **릴리스에서는 그 자리가 `static` 의 칸과 합쳐졌다.** 값이 같고 둘 다 읽기 전용이기 때문이다.
- 즉 **주소로 `const` 와 `static` 을 구별할 수 없다.** Reference 가 양쪽 모두를 허용한다.

  > References to the same constant are not necessarily guaranteed to refer to the same memory address.
  > (Reference, Constant items)

  > However, the storage of immutable static items can overlap with allocations that do not themselves
  > have a unique address, such as promoteds and const items.
  > (Reference, Static items)

- ★ 그래서 **결론은 「주소가 다르다」가 아니라 「`const` 의 주소는 근거가 못 된다」** 다.\
  둘을 가르는 근거는 (1)·(2)의 **동작**이지 주소가 아니다.

비용 — 없음. 다만 **주소 비교에 기대는 코드는 빌드 프로필 하나로 뒤집힌다.**

### (5) `static mut` — `unsafe` 이고 에디션이 갈린다

**언제 쓰나** — 전역 가변 상태가 필요할 때. **거의 항상 다른 방법이 낫다**(아래 「언제 쓰고 언제 안 쓰나」).

```rust
static mut COUNTER: i32 = 0;

fn bump() {
    unsafe { COUNTER += 1; }
}

fn main() {
    bump(); bump(); bump();
    unsafe { println!("COUNTER = {}", COUNTER); }
    let r = unsafe { &COUNTER };       // static mut 에 참조를 만든다
    println!("참조로 읽으면 = {}", r);
}
```

같은 파일을 에디션만 바꿔 두 번 돌린다.

```text
===== 2021: rustc --edition 2021 ex.rs -o ex_dbg =====
warning: creating a shared reference to mutable static
 --> ex.rs:9:39
  |
9 |     unsafe { println!("COUNTER = {}", COUNTER); }
  |                                       ^^^^^^^ shared reference to mutable static
  |
  = note: for more information, see <https://doc.rust-lang.org/edition-guide/rust-2024/static-mut-references.html>
  = note: shared references to mutable statics are dangerous; it's undefined behavior if the static is mutated or if a mutable reference is created for it while the shared reference lives
  = note: `#[warn(static_mut_refs)]` (part of `#[warn(rust_2024_compatibility)]`) on by default

warning: creating a shared reference to mutable static
  --> ex.rs:10:22
   |
10 |     let r = unsafe { &COUNTER };       // static mut 에 참조를 만든다
   |                      ^^^^^^^^ shared reference to mutable static
   |
   = note: for more information, see <https://doc.rust-lang.org/edition-guide/rust-2024/static-mut-references.html>
   = note: shared references to mutable statics are dangerous; it's undefined behavior if the static is mutated or if a mutable reference is created for it while the shared reference lives
help: use `&raw const` instead to create a raw pointer
   |
10 |     let r = unsafe { &raw const COUNTER };       // static mut 에 참조를 만든다
   |                       +++++++++

warning: 2 warnings emitted

COUNTER = 3
참조로 읽으면 = 3
(종료 코드 0)
```

```text
===== 2024: rustc --edition 2024 ex.rs -o ex_dbg24 =====
error: creating a shared reference to mutable static
 --> ex.rs:9:39
  |
9 |     unsafe { println!("COUNTER = {}", COUNTER); }
  |                                       ^^^^^^^ shared reference to mutable static
  |
  = note: for more information, see <https://doc.rust-lang.org/edition-guide/rust-2024/static-mut-references.html>
  = note: shared references to mutable statics are dangerous; it's undefined behavior if the static is mutated or if a mutable reference is created for it while the shared reference lives
  = note: `#[deny(static_mut_refs)]` (part of `#[deny(rust_2024_compatibility)]`) on by default

error: creating a shared reference to mutable static
  --> ex.rs:10:22
   |
10 |     let r = unsafe { &COUNTER };       // static mut 에 참조를 만든다
   |                      ^^^^^^^^ shared reference to mutable static
   |
   = note: for more information, see <https://doc.rust-lang.org/edition-guide/rust-2024/static-mut-references.html>
   = note: shared references to mutable statics are dangerous; it's undefined behavior if the static is mutated or if a mutable reference is created for it while the shared reference lives
help: use `&raw const` instead to create a raw pointer
   |
10 |     let r = unsafe { &raw const COUNTER };       // static mut 에 참조를 만든다
   |                       +++++++++

error: aborting due to 2 previous errors
```

```text
              같은 소스 ex.rs
                    |
        +-----------+------------+
        v                        v
   --edition 2021           --edition 2024
   static_mut_refs = warn   static_mut_refs = deny
        |                        |
        v                        v
   경고 2개 + 실행됨          에러 2개 + 빌드 실패
   COUNTER = 3
```

그림 해설 (한 단계씩):

- **린트 하나의 기본 등급이 에디션으로 갈린다** — 2021 은 `warn`, 2024 는 `deny`.
- ★ **`println!("{}", COUNTER)` 자체가 공유 참조를 만든다.** `&` 를 안 썼는데도 잡힌다.\
  Edition Guide 가 같은 사례를 든다.

  > Note that there are some cases where implicit references are automatically created without a
  > visible `&` operator. For example, these situations will also trigger the lint: `println!("{NUMS:?}");`
  > (Edition Guide, Disallow references to `static mut`)

- **참조를 아예 안 만들면 두 에디션 모두 통과한다** — 복사로 읽으면 된다(실측).

```rust
static mut COUNTER: i32 = 0;
fn main() {
    unsafe { COUNTER += 1; COUNTER += 1; }
    let v = unsafe { COUNTER };            // 참조가 아니라 복사
    println!("COUNTER = {v}");
}
```

```text
===== 2021 =====
COUNTER = 2
(종료 코드 0)
===== 2024 =====
COUNTER = 2
(종료 코드 0)
```

- **`unsafe` 를 빼면 에디션과 무관하게 에러다** — E0133(아래 「문법」).

비용 — 전역 가변 상태의 정합성을 **사람이 전 범위에서 따져야 한다**(Edition Guide 의 표현으로 `reasoning about your code globally`).

### (6) `const fn` — 컴파일 타임 평가를 「허용」하는 것이지 「약속」하는 게 아니다

**언제 쓰나** — 배열 길이·`const`·`static` 초기값처럼 **상수 자리**에서 함수를 부르고 싶을 때.

```rust
const fn square(n: usize) -> usize { n * n }

const SIDE: usize = 4;
const AREA: usize = square(SIDE);          // 컴파일 타임 평가
static TABLE: [u8; square(3)] = [1; 9];    // 배열 길이 자리에서도 된다

fn main() {
    let grid = [0u8; square(SIDE)];        // 지역 배열 길이에도
    println!("AREA = {AREA} / grid.len() = {} / TABLE.len() = {}", grid.len(), TABLE.len());

    // 같은 const fn 을 런타임 값으로도 부를 수 있다
    let n: usize = std::env::args().count();
    println!("런타임 호출 square({n}) = {}", square(n));
}
```

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
AREA = 16 / grid.len() = 16 / TABLE.len() = 9
런타임 호출 square(1) = 1
(종료 코드 0)
```

같은 함수가 **두 자리에서 다르게 논다.** 0으로 나눠 보면 갈린다.

```rust
const fn div(a: i32, b: i32) -> i32 { a / b }
const BAD: i32 = div(100, 0);          // 상수 자리 -> 컴파일 타임 평가
fn main() { println!("{BAD}"); }
```

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
error[E0080]: attempt to divide `100_i32` by zero
 --> ex.rs:2:18
  |
2 | const BAD: i32 = div(100, 0);          // 상수 자리 -> 컴파일 타임 평가
  |                  ^^^^^^^^^^^ evaluation of `BAD` failed inside this call
  |
note: inside `div`
 --> ex.rs:1:39
  |
1 | const fn div(a: i32, b: i32) -> i32 { a / b }
  |                                       ^^^^^ the failure occurred here
```

```rust
const fn div(a: i32, b: i32) -> i32 { a / b }
fn main() {
    let b = std::env::args().count() as i32 - 1;   // 0
    println!("{}", div(100, b));                   // 런타임 호출
}
```

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====

thread 'main' (1805609) panicked at ex.rs:1:39:
attempt to divide by zero
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
(종료 코드 101)
===== 릴리스: rustc --edition 2021 -O ex.rs -o ex_rel =====

thread 'main' (1805663) panicked at ex.rs:1:39:
attempt to divide by zero
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
(종료 코드 101)
```

```text
                 const fn div(a, b) { a / b }
                            |
          +-----------------+------------------+
          v                                    v
    상수 자리                              런타임 자리
    const BAD: i32 = div(100, 0);          println!("{}", div(100, b));
          |                                    |
    반드시 컴파일 타임에 평가된다           보통 함수 호출이다
          |                                    |
          v                                    v
    E0080 — 빌드가 실패한다                  패닉 — 종료 코드 101
```

그림 해설 (한 단계씩):

- **상수 자리(const context)에서는 평가가 의무다.** 실패하면 **컴파일 에러**다.
- **런타임 자리에서는 그냥 함수다.** 실패하면 **패닉**이고, 디버그·릴리스가 같다.
- Reference 가 이 갈림을 그대로 적는다.

  > In const contexts, these are the only allowed expressions, and are always evaluated at compile time.
  > In other places, such as `let` statements, constant expressions may be, but are not guaranteed to be,
  > evaluated at compile time.
  > (Reference, Constant evaluation)

  > Behaviors such as out of bounds array indexing or overflow are compiler errors if the value must be
  > evaluated at compile time (i.e. in const contexts). Otherwise, these behaviors are warnings, but will
  > likely panic at run-time.
  > (Reference, Constant evaluation)

- ★ 그래서 **「`const fn` 으로 쓰면 빨라진다」는 틀린 요약이다.** `const fn` 이 하는 일은 **그 함수를 상수 자리에서 쓸 수 있게 여는 것**이다.

비용 — `const fn` 안에서는 쓸 수 있는 것이 좁아진다(`println!` 도 못 쓴다 — 아래 「문법」).

### (7) `static` 은 `Sync` 를 요구하고 `const` 는 안 한다

**언제 쓰나** — 전역에 「속을 고칠 수 있는 타입」을 두려 할 때.

```rust
use std::cell::RefCell;
static CACHE: RefCell<i32> = RefCell::new(0);
fn main() { println!("{:?}", CACHE); }
```

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
error[E0277]: `RefCell<i32>` cannot be shared between threads safely
 --> ex.rs:2:15
  |
2 | static CACHE: RefCell<i32> = RefCell::new(0);
  |               ^^^^^^^^^^^^ `RefCell<i32>` cannot be shared between threads safely
  |
  = help: the trait `Sync` is not implemented for `RefCell<i32>`
  = note: if you want to do aliasing and mutation between multiple threads, use `std::sync::RwLock` instead
  = note: shared static variables must have a type that implements `Sync`

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0277`.
```

같은 타입을 `const` 로 두면 **그냥 컴파일되고 찍힌다.**

```rust
use std::cell::RefCell;
const CACHE: RefCell<i32> = RefCell::new(0);
fn main() { println!("{:?}", CACHE); }
```

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
RefCell { value: 0 }
(종료 코드 0)
```

```text
   static CACHE: RefCell<i32>            const CACHE: RefCell<i32>
   = 모든 스레드가 그 한 칸을 본다        = 쓰는 자리마다 새 사본
            |                                     |
   그래서 Sync 가 필요하다               공유되는 것이 없다 -> 요구 없음
            |                                     |
            v                                     v
       E0277 로 거부                         통과 (그리고 안 센다)
```

그림 해설 (한 단계씩):

- `static` 은 **공유되므로** 타입이 `Sync` 여야 한다. Reference 도 한 줄로 적는다 — `The type must have the Sync trait bound to allow thread-safe access.`
- `const` 는 공유되는 게 없으니 **그 요구가 없다.** 그래서 (1)의 사고가 **타입 검사에 안 걸린다.**
- ★ 이 대비가 (1) 결론의 **타입 층 증거**다. 「왜 `const` 카운터는 컴파일러가 안 막아 주나」의 답이 여기 있다.
- `Sync` 자체의 정본은 목록의 **50번 주제**다.

비용 — 없음(컴파일 타임 판정).

### (8) `static` 의 수명은 `'static` 이고, `const` 를 빌려도 `'static` 이 된다

**언제 쓰나** — 참조를 오래 들고 다녀야 할 때.

```rust
const LIMIT: i32 = 100;
static TOTAL: i32 = 200;
fn keep(r: &'static i32) -> i32 { *r }
fn main() {
    let a: &'static i32 = &LIMIT;   // const 승격(promotion)
    let b: &'static i32 = &TOTAL;   // static 은 원래 'static
    println!("{} {}", keep(a), keep(b));
}
```

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
100 200
(종료 코드 0)
```

지역 변수는 안 된다.

```text
    let local = 5;
    let c: &'static i32 = &local;

error[E0597]: `local` does not live long enough
  --> ex.rs:12:27
   |
11 |     let local = 5;
   |         ----- binding `local` declared here
12 |     let c: &'static i32 = &local;   // 지역 변수를 'static 으로?
   |            ------------   ^^^^^^ borrowed value does not live long enough
   |            |
   |            type annotation requires that `local` is borrowed for `'static`
13 |     println!("{}", keep(c));
14 | }
   | - `local` dropped here while still borrowed
```

- `static` 항목은 **프로그램 내내 살아 있으므로** 그 참조가 `&'static` 이다.
- `const` 는 항목 자체에 자리가 없지만, **승격될 수 있으면** 그 참조도 `&'static` 이 된다(Reference: `A reference to a constant will have 'static lifetime if the constant value is eligible for promotion; otherwise, a temporary will be created.`).
- 수명 표기와 생략 규칙의 정본은 [목록의 **12번 주제**](../12-lifetime-annotations-and-elision/), `&'static` 과 `T: 'static` 을 가르는 것은 [목록의 **13번 주제**](../13-struct-references-and-static/)다.

비용 — 없음.

## 문법 — 형태와 규칙

### 형태

```rust
const  LIMIT: i32 = 100;              // 타입 표기 필수
static TOTAL: i32 = 100;              // 타입 표기 필수
static mut COUNTER: i32 = 0;          // 접근에 unsafe 필요

const fn square(n: usize) -> usize { n * n }

fn main() {
    const INNER: i32 = 1;             // 함수 안에도 둘 수 있다
    let x = 5;                        // let 은 함수 안에서만
    println!("{LIMIT} {TOTAL} {INNER} {x} {}", square(3));
}
```

규칙 불릿.

- **이름은 관례상 `SCREAMING_SNAKE_CASE`** 다. 안 지키면 `non_upper_case_globals` 경고가 붙는다.
- **초기값은 상수 표현식**이어야 한다. `static` 도 마찬가지다 — Reference: `The static initializer is a constant expression evaluated at compile time.`
- `const`·`static` 은 **모듈 최상위에도, 함수 안에도, 블록 안에도** 둘 수 있다.
- `let` 은 **함수 안에서만** 쓸 수 있다([**02번 주제**](../02-bindings-mut-and-shadowing/)).

### 금지 사례

```text
const LIMIT = 100;          // 타입 없음
static TOTAL = 100;         // 타입 없음

error: missing type for `const` item
 --> ex.rs:1:12
  |
1 | const LIMIT = 100;          // 타입 없음
  |            ^ help: provide a type for the constant: `: i32`

error: missing type for `static` item
 --> ex.rs:2:13
  |
2 | static TOTAL = 100;         // 타입 없음
  |             ^ help: provide a type for the static variable: `: i32`
```

- `const` 는 **타입을 추론하지 않는다.** Reference 가 `Constants must be explicitly typed.` 로 못 박는다.
- help 문구가 서로 다르다 — `for the constant` 와 `for the static variable`.

```text
const LIMIT: i32 = 100;
const LIMIT: i32 = 200;

error[E0428]: the name `LIMIT` is defined multiple times
  = note: `LIMIT` must be defined only once in the value namespace of this module
```

- 같은 스코프에서 **두 번 정의할 수 없다.** 블록 안이면 `of this block` 으로 바뀐다.
- ★ 이것이 **섀도잉이 안 된다**는 말의 정확한 뜻이다 — `let` 은 같은 스코프에서 몇 번이고 다시 묶인다.

```text
fn square(n: usize) -> usize { n * n }
const AREA: usize = square(4);

error[E0015]: cannot call non-const function `square` in constants
  = note: calls in constants are limited to constant functions, tuple structs and tuple variants
```

```text
const fn shout(msg: &str) -> usize {
    println!("{msg}");
    msg.len()
}

error[E0015]: cannot call non-const formatting macro in constant functions
error[E0015]: cannot call non-const function `_print` in constant functions
  = note: calls in constant functions are limited to constant functions, tuple structs and tuple variants
```

- **상수 자리에서는 `const fn` 만 부를 수 있고**, `const fn` 안에서도 마찬가지다.
- `println!` 은 `const fn` 안에서 **두 개의 에러**를 낸다(매크로 하나와 그 안의 `_print` 하나).

```text
static mut COUNTER: i32 = 0;
fn main() {
    COUNTER += 1;

error[E0133]: use of mutable static is unsafe and requires unsafe function or block
 --> ex.rs:3:5
  |
3 |     COUNTER += 1;
  |     ^^^^^^^ use of mutable static
  |
  = note: mutable statics can be mutated by multiple threads: aliasing violations or data races will cause undefined behavior
```

- `static mut` 은 **읽기도 쓰기도 `unsafe`** 다. `note` 가 이유를 한 줄로 말한다.

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다. **여섯 중 셋은 에러가 아니라 경고이거나 아예 조용하다.**

### 1. ★★ 카운터·캐시를 `const` 로 둔다

```text
const C_COUNT: AtomicI32 = AtomicI32::new(0);
  ->  세 번 올려도 0. 에러도 경고도 없다(rustc 기준).
```

- **가장 나쁜 자리다.** 타입 검사도 통과하고 실행도 되고 답만 틀린다.
- `static` 이었으면 `Sync` 검사라도 붙지만((7)), `const` 는 그 검사조차 안 받는다.
- **막는 법** — `clippy` 를 돌린다. 기본 린트로 잡는다.

```text
warning: named constant with interior mutability
 --> src/main.rs:3:7
  |
3 | const C_COUNT: AtomicI32 = AtomicI32::new(0);
  |       ^^^^^^^
  |
  = help: did you mean to make this a `static` item
  = help: for further information visit https://rust-lang.github.io/rust-clippy/rust-1.92.0/index.html#declare_interior_mutable_const
  = note: `#[warn(clippy::declare_interior_mutable_const)]` on by default

warning: borrow of a named constant with interior mutability
 --> src/main.rs:7:5
  |
7 |     C_COUNT.fetch_add(1, Ordering::SeqCst);
  |     ^^^^^^^
  |
  = note: there is a compiler inserted borrow here
  = help: this lint can be silenced by assigning the value to a local variable before borrowing
  = help: for further information visit https://rust-lang.github.io/rust-clippy/rust-1.92.0/index.html#borrow_interior_mutable_const
  = note: `#[warn(clippy::borrow_interior_mutable_const)]` on by default
```

- **`rustc` 는 침묵하고 `clippy` 만 말한다.** 판정이 도구에 달린 자리다.
- 판단 규칙 한 줄: **속을 고칠 수 있는 타입은 `const` 에 두지 않는다.**

### 2. `const` 항목을 고치려 든다

```text
BUF[0] = 9;
  ->  warning: attempting to modify a `const` item
      = note: each usage of a `const` item creates a new temporary; the original `const` item will not be modified
      실행되고 [0, 0, 0] 을 찍는다
```

- 린트 `const_item_mutation`이 **경고**라 빌드가 통과한다.
- `-D warnings` 로 올리면 에러가 된다.

### 3. ★ 상수 이름을 `let` 으로 다시 묶는다

```text
const LIMIT: i32 = 100;
let LIMIT = 300;
  ->  error[E0005]: refutable pattern in local binding
```

- **이름이 새 변수가 아니라 「상수 패턴」으로 읽힌다.** 그래서 `let` 이 매치에 실패할 수 있는 패턴이 된다.
- 에러가 그것을 직접 말한다 — `LIMIT is interpreted as a constant pattern, not a new variable`.
- 메시지가 `E0005`(패턴 에러)라서 **「섀도잉 금지」라는 말이 어디에도 안 나온다** — 처음 보면 헤맨다.
- 반면 **안쪽 블록에 같은 이름의 `const` 를 새로 정의하는 것은 된다**(별개 항목이다, 실측). 섀도잉과 가르는 자리다.

### 4. `static mut` 을 쓰고 2024 로 옮긴다

```text
2021: warning: creating a shared reference to mutable static  (실행됨)
2024: error:   creating a shared reference to mutable static  (빌드 실패)
```

- **2021 에서 경고를 흘려보내면 에디션을 올리는 날 빌드가 깨진다.**\
  경고 note 에 `part of #[warn(rust_2024_compatibility)]` 라고 미리 적혀 있다 — 그게 예고다.
- `println!("{}", COUNTER)` 처럼 **`&` 가 안 보이는 자리도 대상이다.**

### 5. `const` 의 주소로 같음을 판정한다

```text
디버그: const 과 static 이 같은 주소인가? false
릴리스: const 과 static 이 같은 주소인가? true
```

- **같은 소스인데 빌드 프로필 하나로 뒤집혔다.** 주소를 근거로 쓴 코드는 릴리스에서 무너진다.

### 6. `static` 에 둔 값의 소멸자를 기대한다

```text
static GLOBAL: D = D("static");    // D 는 Drop 을 구현한다
  ->  프로그램이 끝나도 [해제] 가 한 줄도 안 찍힌다
```

- Reference 가 명시한다 — `Static items do not call drop at the end of the program.`
- 파일 플러시·잠금 해제를 `static` 값의 `Drop` 에 기대면 **아무 일도 안 일어난다.**

## 구현 세부사항 대 언어 보장

이 갈래에서 「구현 세부사항」은 **주소·최적화·린트 등급**이다. **의미 규칙은 전부 언어 보장**이다.

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| `const` 는 쓰는 자리마다 **복사된다** | **언어** | Reference `Constants are essentially inlined wherever they are used` · 실측(카운터 0, 해제 2회) |
| `static` 의 모든 참조가 **같은 할당**을 가리킨다 | **언어** | Reference `All references and raw pointers to the static refer to the same allocation.` |
| **`const` 두 번의 주소가 같은지** | **구현** | Reference 가 명시적으로 보장하지 않는다. 실측에서는 같았다 |
| **`const` 와 `static` 이 같은 주소가 되는지** | **구현** | 디버그 `false` → 릴리스 `true`. Reference 가 겹침을 허용한다 |
| 주소의 **절댓값** | **런타임 환경** | 실행마다 바뀐다(ASLR). 근거로 쓸 칸이 아니다 |
| `static` 항목은 **드롭되지 않는다** | **언어** | Reference `Static items do not call drop at the end of the program.` · 실측 |
| `static` 의 타입이 **`Sync`** 여야 한다 | **언어** | E0277 `shared static variables must have a type that implements Sync` |
| `static mut` 접근이 **`unsafe`** 인 것 | **언어** | E0133 |
| **`static_mut_refs` 가 경고냐 에러냐** | **에디션** | 2021 `warn` / 2024 `deny`. Edition Guide 가 정본 |
| 상수 자리의 식이 **컴파일 타임에 평가되는 것** | **언어** | Reference `always evaluated at compile time` · E0080 |
| 런타임 자리의 `const fn` 호출이 **컴파일 타임에 접히는지** | **구현(최적화)** | Reference `may be, but are not guaranteed to be, evaluated at compile time` |
| `const`·`static` 의 **타입 표기 의무** | **언어** | Reference `Constants must be explicitly typed.` · 실측 |
| 같은 스코프 **재정의 금지**(E0428) · `let` 재묶기 실패(E0005) | **언어** | 실측 |
| **`const_item_mutation` 이 경고인 것** | **린트 설정** | `-D warnings`·`#[deny]` 로 에러가 된다 |
| **`declare_interior_mutable_const` 로 잡히는 것** | **clippy** | `rustc` 는 침묵한다. clippy 0.1.92 기준 |
| 에러·경고 **문구와 화살표 배치** | **rustc 구현** | 버전이 오르면 바뀐다. **에러 번호**가 더 안정적이다 |

★ **이 주제는 [**03번 주제**](../03-primitive-types-and-integer-overflow/) 와 같은 성격의 갈림이 둘이나 있다.**
03이 「디버그냐 릴리스냐」로 갈렸다면 여기는 **「빌드 프로필」(주소)과 「에디션」(`static mut`)** 으로 갈린다.
그래서 이 문서의 프로그램은 **전부 두 번씩 돌렸다.**

## 언제 쓰고 언제 안 쓰나

| 상황 | `const` | `static` | `let` |
|---|---|---|---|
| 모듈 최상위의 고정 숫자·문자열 | **이것** | 가능하나 과하다 | 아예 못 쓴다 |
| 배열 길이·다른 상수의 초기값 | **이것** | 안 된다 | 안 된다 |
| 큰 배열·표를 **한 벌만** 두고 싶다 | 쓰면 사본이 퍼진다 | **이것** | 아니다 |
| 주소가 하나여야 한다 | 근거가 안 된다 | **이것** | 아니다 |
| 속을 고칠 수 있는 타입(`Atomic*`·`Mutex`) | ★ **절대 아니다** | **이것** | 지역이면 `let` |
| 전역 카운터 | 아니다 | `static COUNTER: AtomicU64` | 아니다 |
| 전역 가변 컬렉션 | 아니다 | `static Q: Mutex<…>` | 아니다 |
| 전역을 **한 번만 늦게** 초기화 | 아니다 | `OnceLock`/`LazyLock`(목록의 **53번 주제**) | 아니다 |
| 함수 안의 임시 이름 | 가능하나 드물다 | 드물다 | **이것** |
| 같은 이름을 다른 타입으로 다시 쓴다 | 안 된다 | 안 된다 | **이것**(섀도잉) |

판단 규칙 세 줄.

- **「값이냐 자리냐」로 고른다.** 값이면 `const`, **자리가 필요하면** `static`.
- ★ **속을 고칠 수 있는 타입이 보이면 `static` 이다.** `const` 로 두면 조용히 안 센다.
- **`static mut` 은 마지막 수단이다.** `Atomic*`·`Mutex`·`OnceLock` 을 먼저 본다(Edition Guide 의 권고도 같다).

## 핵심 문장

- `const` 는 **쓰는 자리마다 복사되는 값**이고 `static` 은 **프로그램에 하나뿐인 할당**이다.
- 그 차이가 답을 바꾸는 자리가 **내부 가변성**이다 — `const` 카운터는 세 번 올려도 0이고, `rustc` 는 아무 말도 안 한다.
- `const` 의 **주소는 근거가 못 된다** — 디버그에서 `static` 과 달랐던 주소가 릴리스에서 같아졌다.
- `static` 은 **`Sync`** 를 요구하고 **드롭되지 않는다**. `static mut` 은 `unsafe` 이고, 참조를 만들면 **2021 경고 · 2024 에러**다.
- `const fn` 은 **상수 자리에서 쓸 수 있게 여는 표시**다 — 상수 자리면 컴파일 타임 평가가 의무(E0080), 런타임 자리면 보통 호출(패닉).
- `const`·`static` 은 **타입 표기가 의무**고 **같은 스코프 재정의가 금지**다. `let` 으로 덮으려 하면 이름이 **패턴**으로 읽혀 E0005 가 난다.

## 관련 자료

- [`../README.md`](../README.md) — Rust 문법·API 주제 목록(이 주제는 07번)
- [**02번 주제**](../02-bindings-mut-and-shadowing/)(변수 바인딩·`mut`·섀도잉) — 거기가 `let` 의 정본이고 `const` 는 **경계만** 다뤘다.\
  **여기가 `const` 의 정본**이다. 섀도잉이 왜 `const` 에는 없는지가 이 문서 「어디서 틀리나」 3번이다
- [**03번 주제**](../03-primitive-types-and-integer-overflow/)(기본 타입·오버플로) — **빌드 프로필로 답이 갈리는** 같은 성격의 주제
- [**04번 주제**](../04-expressions-and-semicolons/)(표현식 지향) — 상수 초기값이 **식**이라는 것
- [**08번 주제**](../08-ownership-and-move/)(소유권과 이동) — 「누가 주인이고 언제 사라지나」. `static` 은 **주인이 프로그램**이고 **사라지지 않는다**
- [`../../언어-특성/README.md`](../../언어-특성/README.md) — **그쪽은 「왜 이 언어인가」**(소유권 모델의 논증·청구서)까지,\
  **여기는 「이 문법이 실제로 무엇을 하나」**(어느 키워드가 어떤 메모리·어떤 진단을 만드나)부터다
- [목록의 **09번 주제**](../09-copy-clone-and-drop/)(`Copy`·`Clone`·`Drop` 시점) — 해제 시점 일반론
- [목록의 **12번 주제**](../12-lifetime-annotations-and-elision/)(수명 표기 `'a`) · **13번 주제**(`'static` 의 두 의미) — `&'static` 의 정본
- 목록의 **47번 주제**(에디션 2021 대 2024) — `static_mut_refs` 를 포함한 에디션 변경 전수
- 목록의 **50번 주제**(`Send`/`Sync`) — `static` 이 `Sync` 를 요구하는 이유
- 목록의 **52번 주제**(`Mutex`/`RwLock`) · **53번 주제**(`atomic`·`OnceLock`/`LazyLock`) — `static mut` 의 대안

## 용어 풀이

- **상수 항목(constant item)** — 이름이 붙은 값. 쓰는 자리마다 복사돼 들어간다.
- **정적 항목(static item)** — 프로그램 내내 한 자리를 차지하는 할당. 모든 참조가 그 한 자리를 가리킨다.
- **상수 자리(const context)** — 상수 표현식만 허용되고 **반드시 컴파일 타임에 평가되는** 자리. `const`·`static` 초기값·배열 길이가 그렇다.
- **상수 표현식(constant expression)** — 컴파일 타임에 계산될 수 있는 식.
- **`const fn`** — 상수 자리에서 부를 수 있게 표시한 함수. 런타임 자리에서는 보통 함수다.
- **승격(promotion)** — 상수 값에 참조를 만들 때 컴파일러가 읽기 전용 자리에 그 값을 두어 `&'static` 을 만들어 주는 것.
- **내부 가변성(interior mutability)** — `&` 만 가지고도 속을 고칠 수 있는 성질. `Cell`·`RefCell`·`Atomic*`·`Mutex` 가 그렇다(정본은 [목록의 **42번 주제**](../42-refcell-cell-interior-mutability/)).
- **`Sync`** — 여러 스레드가 **참조를 나눠 가져도** 안전한 타입임을 나타내는 표시(정본은 목록의 **50번 주제**).
- **`'static` 수명** — 프로그램이 끝날 때까지 유효한 참조의 수명.
- **`static_mut_refs`** — `static mut` 에 참조를 만들면 켜지는 린트. 2021 은 경고, 2024 는 에러.
- **`const_item_mutation`** — `const` 항목에 대입하려 할 때 켜지는 기본 경고.
- **린트(lint)** — 컴파일은 되지만 의심스러운 코드를 지적하는 검사. 등급(`allow`/`warn`/`deny`)을 조절할 수 있다.

---

## 더 들어가면

- **`static` 안에서도 `const fn` 이 배열 길이를 만든다** — `static TABLE: [u8; square(3)] = [1; 9];` 가 컴파일된다(실측, `TABLE.len() = 9`).
- **같은 나눗셈이 자리에 따라 층이 다르다** — `const BOOM: i32 = 100 / ZERO;` 는 E0080 으로 **빌드가 죽고**, 런타임 나눗셈은 **패닉(101)** 이다(실측 양쪽).

```text
error[E0080]: attempt to divide `100_i32` by zero
 --> ex.rs:2:19
  |
2 | const BOOM: i32 = 100 / ZERO;     // 컴파일 타임에 평가된다
  |                   ^^^^^^^^^^ evaluation of `BOOM` failed here
```

- **`static` 은 `static` 을 읽을 수 있다** — Reference: `Static initializers may refer to and read from other statics.`
- **`const` 는 함수 안·블록 안에도 둘 수 있다.** 안쪽 블록의 같은 이름 `const` 는 **별개 항목**이라 바깥 것을 가리지 않는다(블록을 나오면 바깥 값이 그대로 보인다 — 실측).
- **`&raw const` 가 2024 의 권고 형태다.** `static mut` 에 접근해야 하면 참조 대신 원시 포인터를 만든다 — 진단의 `help` 가 그것을 직접 제시한다(`use &raw const instead to create a raw pointer`).
- **`static mut` 은 읽기만 해도 `unsafe`** 다. 「쓸 때만 위험하다」가 아니다 — E0133 의 note 가 `aliasing violations or data races` 를 이유로 든다.
