# rust/syntax/07 — 상수·`static`·`const fn` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러·경고는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서 실제로 돌려 얻은 것이다.\
> ★ **상수 평가·주소·해제 시점이 걸린 프로그램은 전부 두 번 돌렸다** — `rustc --edition 2021 ex.rs`(디버그)와 `rustc --edition 2021 -O ex.rs`(릴리스).\
> ★ `static mut` 이 나오는 자리는 **`rustc --edition 2024`** 로 한 번 더 돌렸다. 배너에 어느 에디션인지 적어 두었다.\
> 소스 파일 이름은 전부 `ex.rs` 로 고정했다. **줄 번호는 그 실험 파일 기준**이라 질문의 발췌와 어긋날 수 있다.\
> ★ 패닉 메시지 **괄호 안 번호**(`(1875228)`)는 **실행마다 바뀐다.** 출력을 그대로 옮기느라 남겨 둔 것이고 근거로 읽을 칸이 아니다.\
> ★ 주소의 **절댓값**(`0x57d3…`)도 실행마다 바뀐다. 근거는 **같은가/다른가** 관계뿐이다(4번의 표).\
> `clippy` 출력은 `cargo clippy`(clippy 0.1.92)로 받았고 그 파일 경로만 `src/main.rs` 다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★ 같은 카운터를 `const` 와 `static` 에 두고 세 번 올리면

**출력**

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

**왜 그런가**

- `const` 쪽은 **0**, `static` 쪽은 **3**이다.
- **`rustc` 는 에러도 경고도 내지 않는다.** 위 출력에 진단이 한 줄도 없다.
- **릴리스에서도 똑같다.** 빌드 프로필과 무관한 **의미 규칙**이다.

```text
  const C_COUNT: AtomicI32 = AtomicI32::new(0);

  fetch_add #1        fetch_add #2        fetch_add #3        load
   +------+            +------+            +------+          +------+
   | 새 0 |            | 새 0 |            | 새 0 |          | 새 0 |
   | ->1  |            | ->1  |            | ->1  |          |  읽음|
   +------+            +------+            +------+          +------+
     버림                버림                버림               -> 0


  static S_COUNT: AtomicI32 = AtomicI32::new(0);

   +---------------------------------------------+
   |  한 칸:  0 -> 1 -> 2 -> 3                    |  -> load 가 3 을 읽는다
   +---------------------------------------------+
```

- Reference 가 그 이유를 한 문장으로 적는다.

  > Constants are essentially inlined wherever they are used, meaning that they are copied directly into
  > the relevant context when used.
  > (Reference, Constant items)

- **`clippy` 는 잡는다.** 린트 이름이 둘이다.

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

- **선언 쪽은 `declare_interior_mutable_const`**, 쓰는 쪽은 `borrow_interior_mutable_const`.\
  쓰는 쪽 경고는 `fetch_add` 세 줄에 각각 붙어 **모두 넷**이 났다.
- ★ **판정이 도구에 달린 자리다.** `rustc` 만 돌리면 이 버그는 아무 흔적을 안 남긴다.

> **내부 가변성(interior mutability)** — `&` 만 가지고도 속을 고칠 수 있는 성질.\
> 예: `AtomicI32`·`Cell`·`RefCell`·`Mutex`. 정본은 목록의 **42번 주제**다.

### 2. ★ 같은 항목을 두 번 읽었을 때 나는 해제 줄

**출력**

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

**왜 그런가**

- `const` 쪽은 **두 번** — 그리고 **각 `println!` 문이 끝나는 자리**에서 찍힌다.
- `static` 쪽은 **한 번도 안 찍힌다.** `main` 이 끝나도 안 찍힌다.

```text
  println!("    {}", TEMPLATE.0);      <- 이 문 안에서 D("const") 가 새로 만들어진다
        |
        +-- 읽는다  -> "const" 출력
        +-- 문이 끝난다 -> [해제] const
  println!("    {}", TEMPLATE.0);      <- 또 새로 만든다
        +-- 읽는다  -> "const" 출력
        +-- 문이 끝난다 -> [해제] const

  println!("    {}", GLOBAL.0);        <- 프로그램에 하나뿐인 칸을 읽기만 한다
        +-- 아무것도 안 만들고 안 버린다
```

- `static` 이 해제되지 않는 것은 Reference 가 규정한 성질이다.

  > Static items have the static lifetime, which outlives all other lifetimes in a Rust program.
  > **Static items do not call drop at the end of the program.**
  > (Reference, Static items)

- **1번과 같은 이야기인 이유 한 문장** — 1번은 「사본이 몇 개인가」를 **값으로** 보여 주었고, 2번은 같은 것을 **해제 줄 수로** 보여 준다.
- 그래서 **파일 닫기·플러시·잠금 해제를 `static` 값의 `Drop` 에 기대면 안 된다.**\
  해제 시점 일반론은 [목록의 **09번 주제**](../09-copy-clone-and-drop/), 소유권과 해제의 관계는 [**08번 주제**](../08-ownership-and-move/)가 정본이다.

### 3. `const` 항목에 대입하면

**출력**

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

**왜 그런가**

- **컴파일된다.** 에러가 아니라 **경고 하나**다. 린트 이름은 `const_item_mutation`이고 **기본이 `warn`** 이다.
- 실행되면 **`[0, 0, 0]`** 이 찍힌다 — 바뀐 것은 그 자리에 생겼다 사라진 **임시값**이지 `BUF` 가 아니다.
- `note` 가 이 주제의 규칙을 그대로 말한다 —\
  `each usage of a const item creates a new temporary; the original const item will not be modified`.
- **에러로 올리는 법 둘** — ① `#![deny(const_item_mutation)]` ② 빌드에 `-D warnings`.

```text
   BUF[0] = 9;
     |
     +-- 여기서 [0,0,0] 의 새 임시값이 생긴다
     +-- 그 임시값의 0번 칸에 9 를 넣는다
     +-- 문이 끝나며 임시값이 사라진다
              |
              v
     println!("{:?}", BUF)  ->  또 새 임시값 -> [0, 0, 0]
```

### 4. ★ `&CONST` 와 `&STATIC` 의 주소를 견주면

**출력**

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

**다시 찍은 값** — 절댓값이 실행마다 바뀌는지 보려고 같은 릴리스 바이너리를 세 번 더 돌린 것이다.

```text
===== 릴리스 바이너리를 세 번 더 =====
&LIMIT(const)  #1 = 0x5a51fbc96ab4 const 과 static 이 같은 주소인가? true 
&LIMIT(const)  #1 = 0x629200659ab4 const 과 static 이 같은 주소인가? true 
&LIMIT(const)  #1 = 0x62c41cca8ab4 const 과 static 이 같은 주소인가? true
```

**왜 그런가**

- 세 줄은 디버그에서 **`true` · `true` · `false`**, 릴리스에서 **`true` · `true` · `true`** 다.
- **릴리스에서 달라지는 줄은 셋째 줄**이다 — `const` 의 승격본이 `static` 의 칸과 **합쳐졌다.**
- ★ **근거로 쓸 칸과 못 쓸 칸.**

| 칸 | 흔들리나 | 근거로 쓸 수 있나 |
|---|---|---|
| 주소의 **절댓값** | 실행마다 바뀐다 | ✗ (세 판 전부 달랐다) |
| **같은가/다른가**(한 빌드 안) | 안 바뀐다 | ○ (세 판 전부 같았다) |
| **빌드 프로필 사이**의 관계 | **바뀐다** | ✗ (디버그 `false` → 릴리스 `true`) |

```text
  디버그                                   릴리스 (-O)
  +---------------------------+            +---------------------------+
  |  ...2784 : static TOTAL   |            |  ...ab4 : static TOTAL    |
  |  ...2788 : const 승격본    |            |          = const 승격본   |  <- 합쳐졌다
  +---------------------------+            +---------------------------+
   셋째 줄 false                             셋째 줄 true
```

- **그래서 「`const` 와 `static` 의 차이」를 주소로 설명하면 안 된다.** Reference 가 양쪽을 다 허용한다.

  > References to the same constant are not necessarily guaranteed to refer to the same memory address.
  > (Reference, Constant items)

  > However, the storage of immutable static items can overlap with allocations that do not themselves have
  > a unique address, such as promoteds and const items.
  > (Reference, Static items)

- 둘을 가르는 **진짜 근거는 1번·2번의 동작**이다 — 카운터 값과 해제 줄 수.
- ★ 「`const` 는 인라인되니까 주소가 매번 다르겠지」는 **틀린 예측이었다.** 승격이 그것을 하나로 묶는다.

> **승격(promotion)** — 상수 값에 참조를 만들 때 컴파일러가 그 값을 읽기 전용 자리에 놓아 `&'static` 을 만들어 주는 것.\
> 예: `let a: &'static i32 = &LIMIT;` 이 컴파일되는 이유가 이것이다(11번).

### 5. ★ `static mut` 을 두 에디션에서

**출력** — 2021

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

**출력** — 2024

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

**왜 그런가**

- **2021** — 진단 **두 개**, 등급은 **경고**다. 프로그램은 돌고 `COUNTER = 3` 을 찍는다.
- **2024** — **같은 두 자리가 에러**다. 빌드가 실패한다.
- 갈리는 것은 **린트 하나의 기본 등급**뿐이다 — `#[warn(static_mut_refs)]` ↔ `#[deny(static_mut_refs)]`.\
  괄호 안이 예고다 — `part of #[warn(rust_2024_compatibility)]`.

```text
              같은 소스 ex.rs
                    |
        +-----------+------------+
        v                        v
   --edition 2021           --edition 2024
   static_mut_refs = warn   static_mut_refs = deny
        |                        |
        v                        v
   경고 2 + 실행 (COUNTER = 3)   에러 2 + 빌드 실패
```

- **`&` 를 한 번만 썼는데 진단이 둘인 이유** — `println!("{}", COUNTER)` 가 **보이지 않는 공유 참조**를 만든다.\
  Edition Guide 가 같은 사례를 든다.

  > Note that there are some cases where implicit references are automatically created without a visible
  > `&` operator. For example, these situations will also trigger the lint: `println!("{NUMS:?}");`
  > (Edition Guide, Disallow references to `static mut`)

- **두 에디션 모두 통과시키려면 참조를 안 만들면 된다** — 값을 **복사**해서 읽는다(실측).

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

- **`unsafe` 를 빼면 에디션과 무관하게 거부된다.**

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

`rustc --explain E0133`:

> Unsafe code was used outside of an unsafe block.
> …
> Using unsafe functionality is potentially dangerous and disallowed by safety checks.

- 참조가 꼭 필요하면 **`&raw const`** 로 원시 포인터를 만든다 — 진단의 `help` 가 그것을 짚어 준다.
- 에디션 변경 전수는 목록의 **47번 주제**가 정본이다.

### 6. `const fn` 은 어디까지 쓸 수 있나

**출력**

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
AREA = 16 / grid.len() = 16 / TABLE.len() = 9
런타임 호출 square(1) = 1
(종료 코드 0)
```

**왜 그런가**

- **컴파일되고 다 돈다.** `const` 초기값·`static` 의 배열 길이·**지역 배열 길이**에 전부 쓰였다.
- 마지막 줄이 중요하다 — **같은 함수를 런타임 값으로도 부른다.** `const fn` 은 보통 함수이기도 하다.\
  (`square(1)` 의 `1` 은 실행 인자 개수다.)

**보통 `fn` 으로 바꾸면**

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
error[E0015]: cannot call non-const function `square` in constants
 --> ex.rs:5:20
  |
5 | static TABLE: [u8; square(3)] = [1; 9];
  |                    ^^^^^^^^^
  |
  = note: calls in constants are limited to constant functions, tuple structs and tuple variants

error[E0015]: cannot call non-const function `square` in constants
 --> ex.rs:4:21
  |
4 | const AREA: usize = square(SIDE);
  |                     ^^^^^^^^^^^^
  |
  = note: calls in constants are limited to constant functions, tuple structs and tuple variants

error[E0015]: cannot call non-const function `square` in constants
 --> ex.rs:8:22
  |
8 |     let grid = [0u8; square(SIDE)];
  |                      ^^^^^^^^^^^^
  |
  = note: calls in constants are limited to constant functions, tuple structs and tuple variants

error: aborting due to 3 previous errors

For more information about this error, try `rustc --explain E0015`.
```

- **E0015** 가 **세 번** 난다 — `static` 의 길이, `const` 의 초기값, **그리고 지역 배열의 길이**.
- ★ 셋째가 요점이다. **`let` 문 안이어도 배열 길이 자리는 상수 자리다.**

`rustc --explain E0015`:

> A non-`const` function was called in a `const` context.
> …
> All functions used in a `const` context (constant or static expression) must be marked `const`.

**`const fn` 안에 `println!` 을 넣으면**

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
error[E0015]: cannot call non-const formatting macro in constant functions
 --> ex.rs:2:5
  |
2 |     println!("{msg}");         // const fn 안에서 println! 을 쓰면?
  |     ^^^^^^^^^^^^^^^^^
  |
  = note: calls in constant functions are limited to constant functions, tuple structs and tuple variants
  = note: this error originates in the macro `println` (in Nightly builds, run with -Z macro-backtrace for more info)

error[E0015]: cannot call non-const function `_print` in constant functions
 --> ex.rs:2:5
  |
2 |     println!("{msg}");         // const fn 안에서 println! 을 쓰면?
  |     ^^^^^^^^^^^^^^^^^
  |
  = note: calls in constant functions are limited to constant functions, tuple structs and tuple variants
  = note: this error originates in the macro `println` (in Nightly builds, run with -Z macro-backtrace for more info)
```

- 한 줄에서 **에러가 둘** 난다 — 서식 매크로 자체와 그것이 부르는 `_print`.
- 즉 `const fn` 으로 표시하면 **몸통에서 쓸 수 있는 것이 좁아진다.** 공짜가 아니다.

**「`const fn` 으로 만들면 컴파일 타임에 계산된다」가 틀린 이유**

- **자리가 정한다.** 상수 자리면 평가가 의무이고, 런타임 자리면 보통 호출이다(7번).
- `const fn` 이 하는 일은 「그 함수를 **상수 자리에서 쓸 수 있게 여는 것**」이다.

```text
   const fn square(n) { n * n }
             |
   +---------+----------+
   v                    v
 상수 자리            런타임 자리
 [0u8; square(4)]     square(args_count)
 반드시 컴파일 타임     보통 함수 호출
```

### 7. 같은 `const fn` 이 두 자리에서 0으로 나누면

**출력** — (가) 상수 자리

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

note: erroneous constant encountered
 --> ex.rs:3:24
  |
3 | fn main() { println!("{BAD}"); }
  |                        ^^^

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0080`.
```

**출력** — (나) 런타임 자리

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====

thread 'main' (1875228) panicked at ex.rs:1:39:
attempt to divide by zero
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
(종료 코드 101)
===== 릴리스: rustc --edition 2021 -O ex.rs -o ex_rel =====

thread 'main' (1875282) panicked at ex.rs:1:39:
attempt to divide by zero
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
(종료 코드 101)
```

**왜 그런가**

- **(가)는 컴파일 층에서 죽는다** — **E0080**, 빌드가 실패한다. 실행까지 가지 않는다.
- **(나)는 실행 층에서 죽는다** — **패닉**, 종료 코드 **101**.
- **디버그와 릴리스가 같다.** 0으로 나누기는 오버플로와 달리 **빌드 프로필에 안 갈린다**\
  ([**03번 주제**](../03-primitive-types-and-integer-overflow/)의 오버플로와 대비되는 자리다).
- 에러가 가리키는 자리도 다르다 — (가)는 **`const BAD` 줄**을 가리키며 `note: inside div` 로 내려가고,\
  (나)는 **`div` 안의 `a / b`** 를 가리킨다(`ex.rs:1:39`).

```text
   const fn div(a, b) { a / b }
             |
   +---------+-----------+
   v                     v
 const BAD = div(100,0)  println!("{}", div(100, b))
   |                       |
 컴파일 타임 평가 의무      보통 호출
   |                       |
   v                       v
 error[E0080]            panicked ... (종료 코드 101)
 빌드 실패                디버그·릴리스 동일
```

`rustc --explain E0080`:

> A constant value failed to get evaluated.
> …
> This error indicates that the compiler was unable to sensibly evaluate a constant expression that had
> to be evaluated. Attempting to divide by 0 or causing an integer overflow are two ways to induce this error.

Reference 가 이 갈림을 규정한다.

> In const contexts, these are the only allowed expressions, and are always evaluated at compile time.
> In other places, such as `let` statements, constant expressions may be, but are not guaranteed to be,
> evaluated at compile time.
> (Reference, Constant evaluation)

> Behaviors such as out of bounds array indexing or overflow are compiler errors if the value must be
> evaluated at compile time (i.e. in const contexts). Otherwise, these behaviors are warnings, but will
> likely panic at run-time.
> (Reference, Constant evaluation)

### 8. 타입 표기와 재정의

**출력** — 타입 없음

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
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

error: aborting due to 2 previous errors
```

**출력** — 재정의

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
error[E0428]: the name `LIMIT` is defined multiple times
 --> ex.rs:2:1
  |
1 | const LIMIT: i32 = 100;
  | ----------------------- previous definition of the value `LIMIT` here
2 | const LIMIT: i32 = 200;
  | ^^^^^^^^^^^^^^^^^^^^^^^ `LIMIT` redefined here
  |
  = note: `LIMIT` must be defined only once in the value namespace of this module

error[E0428]: the name `INNER` is defined multiple times
 --> ex.rs:5:5
  |
4 |     const INNER: i32 = 1;
  |     --------------------- previous definition of the value `INNER` here
5 |     const INNER: i32 = 2;
  |     ^^^^^^^^^^^^^^^^^^^^^ `INNER` redefined here
  |
  = note: `INNER` must be defined only once in the value namespace of this block

error: aborting due to 2 previous errors

For more information about this error, try `rustc --explain E0428`.
```

**왜 그런가**

- 타입 누락은 **에러 번호가 없다** — 문법(파서) 단계의 에러다.\
  재정의는 **E0428**로 번호가 붙는다.
- **`help` 문구가 서로 다르다** — `provide a type for the constant` ↔ `provide a type for the static variable`.
- **`let` 은 왜 안 적어도 되나** — `let` 은 **지역 바인딩**이라 오른쪽 식과 쓰임새로 추론한다.\
  `const`·`static` 은 **항목(item)** 이고 다른 모듈에서도 참조되는 **공개 표면**이라 추론에 기대지 않는다.\
  Reference 가 `Constants must be explicitly typed.` 로 못 박는다.
`rustc --explain E0428`:

> A type or module has been defined more than once.

- `note` 는 **정의된 자리에 따라 다르다** — 모듈 최상위면 `value namespace of this module`,\
  함수·블록 안이면 `value namespace of this block`.

```text
   let  x = 5;  x = 6;  let x = "여섯";      <- 다시 묶기·섀도잉 자유 (02번)
   const X: i32 = 5;  const X: i32 = 6;      <- E0428. 항목은 이름 하나에 정의 하나
```

### 9. ★ 상수 이름을 `let` 으로 다시 묶으면

**출력**

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
error[E0005]: refutable pattern in local binding
 --> ex.rs:3:9
  |
1 | const LIMIT: i32 = 100;
  | ---------------- missing patterns are not covered because `LIMIT` is interpreted as a constant pattern, not a new variable
2 | fn main() {
3 |     let LIMIT = 300;
  |         ^^^^^ patterns `i32::MIN..=99_i32` and `101_i32..=i32::MAX` not covered
  |
  = note: `let` bindings require an "irrefutable pattern", like a `struct` or an `enum` with only one variant
  = note: for more information, visit https://doc.rust-lang.org/book/ch19-02-refutability.html
  = note: the matched value is of type `i32`
help: introduce a variable instead
  |
3 |     let LIMIT_var = 300;
  |              ++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0005`.
```

**왜 그런가**

- **컴파일되지 않는다.** 에러 번호는 **E0005**다 — 「섀도잉 금지」라는 말은 어디에도 안 나온다.
- **패턴 이야기를 하는 이유** — `let` 의 왼쪽은 이름이 아니라 **패턴**이다.\
  그 자리에 **상수 이름**이 오면 새 변수가 아니라 **그 값과 맞춰 보는 상수 패턴**으로 읽힌다.
- 컴파일러가 그것을 직접 말한다 — `LIMIT is interpreted as a constant pattern, not a new variable`.\
  그래서 `100` 이외의 값(`i32::MIN..=99_i32` 와 `101_i32..=i32::MAX`)이 안 덮여 **반증 가능한 패턴**이 된다.

```text
   let x = 300;                 x 는 새 이름  -> 늘 성공
   let LIMIT = 300;             LIMIT 는 값 100 을 뜻하는 "패턴"
                                  |
                          300 이 100 과 맞나? -> 맞을 수도 아닐 수도
                                  |
                          let 은 "반드시 맞는 패턴"만 받는다 -> E0005
```

`rustc --explain E0005`:

> Patterns used to bind names must be irrefutable, that is, they must guarantee that a name will be
> extracted in all cases.

**안쪽 블록의 `const` 는 된다**

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
바깥 LIMIT = 100
안쪽 LIMIT = 200
블록을 나오면 = 100
(종료 코드 0)
```

- 안쪽 블록의 `const LIMIT` 는 **그 블록의 별개 항목**이다. 블록을 나오면 바깥 값이 그대로 보인다.
- **02번의 섀도잉과 무엇이 다른가** — [**02번 주제**](../02-bindings-mut-and-shadowing/)의 섀도잉은 **같은 스코프 안에서** 이름을 다시 묶는 것이고,\
  여기 것은 **스코프가 다른 두 항목**일 뿐이다. `const` 는 같은 스코프에서 두 번 정의될 수 없다(8번, E0428).
- 정리하면 — **`let` 은 이름을 다시 묶고, `const` 는 이름 하나에 정의 하나다.**

### 10. `static` 에만 붙는 요구

**출력** — `static` 쪽

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

**출력** — `const` 쪽

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
RefCell { value: 0 }
(종료 코드 0)
```

**왜 그런가**

- **컴파일되는 것은 `const` 쪽**이다. `static` 쪽은 **E0277**로 거부된다.
- `note` 가 규칙을 한 줄로 말한다 — `shared static variables must have a type that implements Sync`.\
  Reference 도 같다 — `The type must have the Sync trait bound to allow thread-safe access.`
- **왜 한쪽에만 붙나** — `static` 은 **모든 스레드가 그 한 칸을 본다.** 그래서 공유 안전성이 요구된다.\
  `const` 는 쓰는 자리마다 **자기 사본**이므로 공유되는 것이 없다.
- ★ **통과하는 쪽이 더 안전한 게 아니다.** `const` 쪽은 **검사를 안 받은 것**이고, 그 결과가 1번의 「세 번 올려도 0」이다.

```text
   static CACHE: RefCell<i32>          const CACHE: RefCell<i32>
   = 공유된다 -> Sync 검사             = 사본이다 -> 검사 없음
        |                                    |
        v                                    v
     E0277 로 거부                     통과. 그리고 값이 안 쌓인다
        |                                    |
   "이건 위험하다" 고 말해 준다         아무도 말해 주지 않는다 (clippy 만 — 1번)
```

`rustc --explain E0277`:

> You tried to use a type which doesn't implement some trait in a place which expected that trait.

- `Sync` 자체의 정본은 목록의 **50번 주제**다.

### 11. `'static` 은 누구의 수명인가

**출력**

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
100 200
(종료 코드 0)
```

**왜 그런가**

- **`&TOTAL` 은 당연히 `&'static i32`** 다. `static` 항목은 프로그램이 끝날 때까지 산다.\
  Reference — `Static items have the static lifetime, which outlives all other lifetimes in a Rust program.`
- **`&LIMIT`(const)도 `&'static i32` 로 쓸 수 있다.** 그 장치의 이름이 **승격(promotion)** 이다.\
  Reference — `A reference to a constant will have 'static lifetime if the constant value is eligible for promotion; otherwise, a temporary will be created.`
- **지역 변수는 안 된다.**

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

`rustc --explain E0597`:

> This error occurs because a value was dropped while it was still borrowed.

```text
   프로그램 시작 ─────────────────────────────────── 끝
     static TOTAL   [==================================]   'static
     const LIMIT    [==================================]   승격되면 'static
     let local          [====]                             그 스코프뿐
                             ^ 여기서 죽는데 &'static 을 요구했다 -> E0597
```

- 수명 표기와 생략 규칙의 정본은 [목록의 **12번 주제**](../12-lifetime-annotations-and-elision/), `&'static` 과 `T: 'static` 을 가르는 것은 [목록의 **13번 주제**](../13-struct-references-and-static/)다.

### 12. 다른 주제와 잇기

- **전역 카운터의 세 후보**
  - `static COUNTER: AtomicU64` — 정수·불리언·포인터면 이것. 정본은 목록의 **53번 주제**.
  - `static Q: Mutex<…>` — 더 복잡한 타입이면 이것. 정본은 목록의 **52번 주제**.
  - `static X: OnceLock<…>` / `LazyLock<…>` — **늦게 한 번만** 초기화해야 하면 이것. 정본은 목록의 **53번 주제**.
  - ★ `static mut` 은 이 셋이 다 안 될 때의 마지막 수단이다. Edition Guide 의 권고도 같은 순서다.
- **`static` 이 `Sync` 를 요구하는 이유** — 목록의 **50번 주제**(`Send`/`Sync`).
- **에디션 변경 전수** — 목록의 **47번 주제**(에디션 2021 대 2024).
- **해제 시점 일반론** — [목록의 **09번 주제**](../09-copy-clone-and-drop/)(`Copy`·`Clone`·`Drop` 시점) · `Drop` 관용구는 목록의 **44번 주제**.\
  「누가 주인이고 언제 사라지나」의 정본은 [**08번 주제**](../08-ownership-and-move/)다.
- **`rustc` 는 침묵하고 다른 도구만 말하는 자리** — **1번**이다.\
  `const` 에 둔 `AtomicI32` 는 `rustc` 기준으로 에러도 경고도 없고, `clippy` 의\
  `declare_interior_mutable_const`·`borrow_interior_mutable_const` 만 잡는다.\
  이 주제에서 **가장 조용한 사고**이고, 그래서 가장 나쁘다.

---

## 실행 검증

| 실험 (`ex.rs`) | 무엇을 확인했나 | 결과 | 문항 |
|---|---|---|---|
| `const`/`static` 에 둔 `AtomicI32` 를 3회 `fetch_add` | **0 대 3** · 디버그·릴리스 동일 · rustc 진단 **없음** | 갈림 | 1 |
| 같은 코드에 `cargo clippy` | `declare_interior_mutable_const` 1건 + `borrow_interior_mutable_const` 3건 | 잡힘 | 1 |
| `const`/`static` 에 `Drop` 타입을 두고 두 번 읽기 | 해제 줄 **2 대 0** · 디버그·릴리스 동일 | 갈림 | 2 |
| `BUF[0] = 9;` (`const` 배열) | **경고** `const_item_mutation` · 실행되고 `[0, 0, 0]` | 통과 | 3 |
| `&LIMIT` ×2 · `&TOTAL` ×2 의 주소 | 디버그 `true/true/false` · 릴리스 `true/true/true` | **프로필로 뒤집힘** | 4 |
| 같은 릴리스 바이너리 3회 재실행 | 절댓값은 매번 다름 · 관계는 `true/true/true` 고정 | 재확인 | 4 |
| `static mut` + `&COUNTER` (2021) | **경고 2** `static_mut_refs` · `COUNTER = 3` | 통과 | 5 |
| 같은 파일 (2024) | **에러 2** · 빌드 실패 | 거부 | 5 |
| `let v = unsafe { COUNTER };` (2021·2024) | 양쪽 `COUNTER = 2` | 통과 | 5 |
| `COUNTER += 1;` 을 `unsafe` 없이 | **E0133** | 거부 | 5 |
| `const fn square` 를 상수·배열·런타임 자리에 | `AREA = 16 / grid.len() = 16 / TABLE.len() = 9` · `square(1) = 1` | 통과 | 6 |
| 같은 코드에서 `const fn` → `fn` | **E0015 ×3**(`static` 길이 · `const` 초기값 · **지역 배열 길이**) | 거부 | 6 |
| `const fn` 안의 `println!` | **E0015 ×2**(서식 매크로 · `_print`) | 거부 | 6 |
| `const BAD: i32 = div(100, 0);` | **E0080** — 빌드 실패 | 컴파일 층 | 7 |
| `let b = 0; div(100, b)` | **패닉** `attempt to divide by zero` · 종료 **101** · 디버그·릴리스 동일 | 실행 층 | 7 |
| `const BOOM: i32 = 100 / ZERO;` | **E0080** `evaluation of BOOM failed here` | 컴파일 층 | 7 |
| `const LIMIT = 100;` · `static TOTAL = 100;` | `missing type for …` **에러 번호 없음** · help 문구가 다름 | 거부 | 8 |
| 같은 스코프 `const` 두 번 | **E0428** · note 가 module/block 으로 갈림 | 거부 | 8 |
| `let LIMIT = 300;` (`const LIMIT` 가 있는 곳) | **E0005** `interpreted as a constant pattern` | 거부 | 9 |
| 안쪽 블록에 같은 이름 `const` | `100 / 200 / 100` | 통과 | 9 |
| `static CACHE: RefCell<i32>` | **E0277** `must have a type that implements Sync` | 거부 | 10 |
| `const CACHE: RefCell<i32>` | `RefCell { value: 0 }` | 통과 | 10 |
| `&TOTAL`·`&LIMIT` 를 `&'static i32` 로 | `100 200` | 통과 | 11 |
| `&local` 을 `&'static i32` 로 | **E0597** `does not live long enough` | 거부 | 11 |
| `static GLOBAL: D` 를 둔 채 프로그램 종료 | `[해제]` 가 **한 줄도 안 찍힘** | 해제 없음 | 2 |

**구현·설정에 달린 항목**(다시 찍을 자리)

| 항목 | 무엇에 달렸나 |
|---|---|
| 주소의 **절댓값** | 실행마다 바뀐다(ASLR). 근거로 쓰지 않는다 |
| **`const` 와 `static` 의 주소가 같아지는지** | **빌드 프로필.** 디버그 `false` → 릴리스 `true` |
| **`const` 두 번의 주소가 같은지** | rustc 구현(승격). Reference 가 보장하지 않는다 |
| 런타임 자리의 `const fn` 이 **컴파일 타임에 접히는지** | 최적화. Reference 가 `not guaranteed` 라고 적는다 |
| **`static_mut_refs` 가 경고냐 에러냐** | **에디션.** 2021 `warn` / 2024 `deny` |
| **`const_item_mutation` 이 경고인 것** | 린트 설정. `#[deny]`·`-D warnings` 로 에러가 된다 |
| **`declare_interior_mutable_const` 로 잡히는 것** | **clippy**(0.1.92). `rustc` 는 침묵한다 |
| clippy 린트 문서 URL | clippy 버전(`rust-1.92.0` 이 URL 에 박힌다) |
| 패닉 메시지의 **괄호 안 번호** | 실행마다 바뀐다 |
| 에러·경고 **문구와 화살표 배치** | rustc 구현. **에러 번호**가 더 안정적이다 |
| **`const` 복사 의미 · `static` 단일 할당 · `Sync` 요구 · 상수 자리 평가 의무** | **전부 언어 보장.** 프로필·플랫폼에 안 흔들린다 |
