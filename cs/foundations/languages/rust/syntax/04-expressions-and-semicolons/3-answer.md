# rust/syntax/04 — 표현식 지향: 블록이 값·세미콜론의 의미 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러·경고는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)`** 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 얻은 것이다. `cargo` 는 10번에서만 썼다(`clippy`).\
> 소스 파일 이름은 전부 `ex.rs` 로 고정했다. **줄 번호는 그 실험 파일 기준**이라 질문의 발췌와 어긋날 수 있다.\
> 관찰용 타입 이름은 `std::any::type_name_of_val`(1.76.0부터)로 찍었다 — **그 문자열은 보장되지 않는다.**\
> 타입 자체의 근거는 **컴파일 에러**다(8번의 `let _: () = 식;` 수법).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★ 세미콜론 하나 차이

**출력**

```text
warning: unused arithmetic operation that must be used
 --> ex.rs:8:9
  |
8 |         a + 1;
  |         ^^^^^ the arithmetic operation produces a value
  |
  = note: `#[warn(unused_must_use)]` (part of `#[warn(unused)]`) on by default
help: use `let _ = ...` to ignore the resulting value
  |
8 |         let _ = a + 1;
  |         +++++++

warning: 1 warning emitted
```

```text
y = 4 / 타입 i32
z = () / 타입 ()
z 의 크기 = 0
```

**왜 그런가**

- `y` 는 **`4`**(타입 `i32`), `z` 는 **`()`**(타입 `()`)다.
- **컴파일은 된다.** 에러가 아니라 **경고 하나**만 난다.
- 린트 이름은 **`unused_must_use`** 이고, 지적하는 것은 「**값을 만들어 놓고 버렸다**」다\
  (`the arithmetic operation produces a value`).
- `z` 의 크기는 **0**이다.

```text
  let y = { ... a + 1  };            let z = { ... a + 1; };
                     ^                                  ^
                세미콜론 없음                       세미콜론 있음
                     |                                  |
              "꼬리 표현식"                      "값을 버리는 문"
                     |                                  |
                     v                                  v
             블록의 값 = 4                       블록의 값 = ()
                 y : i32                             z : ()
                                                   크기 0바이트
```

- **글자 하나로 타입이 바뀐다.** 이것이 이 주제의 전부다.
- 이 자리가 **에러가 아니라 경고**라는 점이 위험하다 — 2번과 대비된다.

> **꼬리 표현식(tail expression)** — 블록의 마지막에 세미콜론 없이 놓인 식. 그 블록의 값이 된다.\
> 예: `{ let a = 3; a + 1 }` 의 `a + 1`.

### 2. ★ 함수 끝의 세미콜론

**출력**

```text
error[E0308]: mismatched types
 --> ex.rs:1:24
  |
1 | fn plus_one(a: i32) -> i32 {
  |    --------            ^^^ expected `i32`, found `()`
  |    |
  |    implicitly returns `()` as its body has no tail or `return` expression
2 |     a + 1;
  |          - help: remove this semicolon to return this value

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0308`.
```

**왜 그런가**

- **컴파일되지 않는다.** 에러 번호는 **E0308**이다.
- 「**expected `i32`, found `()`**」 — 선언한 반환 타입과 몸통이 내는 값이 어긋났다.
- 설명 한 줄 — 「**implicitly returns `()` as its body has no tail or `return` expression**」.\
  즉 **꼬리 표현식도 `return` 도 없으면 함수는 암묵적으로 `()` 를 돌려준다.**
- `help:` 는 **세미콜론 그 자체**를 가리킨다(`a + 1;` 의 `;` 밑에 `-` 표시).\
  `remove this semicolon to return this value` — **지울 글자 하나까지 짚어 준다.**

**1번과의 차이 한 문장**

- **기대 타입이 있느냐 없느냐**다.

```text
  1번: let z = { ... a + 1; };        2번: fn f() -> i32 { a + 1; }
       기대 타입이 없다                     기대 타입이 i32 로 선언돼 있다
              |                                    |
              v                                    v
       z 를 () 로 받아들인다                  () 와 i32 가 어긋난다
       -> 경고(unused_must_use)             -> 에러(E0308)
```

- 그래서 **`let` 쪽이 더 위험하다.** 통과해 버리고, 틀린 것은 `z` 를 쓰는 **다른 줄**에서 드러난다.
- 막는 법 둘: ① `let z: i32 = ...` 로 **기대 타입을 적어 둔다**(그 순간 2번과 같은 에러가 난다) ② `-D warnings`.

### 3. `if` 를 값으로 쓰면

**출력** — 되는 두 줄부터

```text
참
a = 1 / e = () / e 의 크기 0
```

**출력** — `let b = if c { 1 } else { "둘" };`

```text
error[E0308]: `if` and `else` have incompatible types
 --> ex.rs:3:31
  |
3 |     let x = if c { 1 } else { "둘" };
  |                    -          ^^^^ expected integer, found `&str`
  |                    |
  |                    expected because of this

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0308`.
```

**출력** — `let d = if c { 1 };`

```text
error[E0317]: `if` may be missing an `else` clause
 --> ex.rs:3:13
  |
3 |     let x = if c { 1 };
  |             ^^^^^^^-^^
  |             |      |
  |             |      found here
  |             expected integer, found `()`
  |
  = note: `if` expressions without `else` evaluate to `()`
  = help: consider adding an `else` block that evaluates to the expected type

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0317`.
```

**왜 그런가**

- 컴파일되는 것은 **`a` 와 `e`** 다.
- `b` 는 **E0308**(`if` and `else` have incompatible types), `d` 는 **E0317**(may be missing an `else` clause).
- `E0317` 의 `note` 가 규칙을 한 줄로 말한다 — **「`if` expressions without `else` evaluate to `()`」**.

```text
   if c { 1 } else { 2 }        if c { 1 } else { "둘" }        if c { 1 }
        |        |                   |          |                   |
       i32      i32                 i32        &str                i32
        +---+----+                   +----+-----+                   |
            v                             v                    없는 else 갈래 = ()
           i32  (OK)                  타입 불일치 E0308              +---+---+
                                                                        v
                                                                  i32 와 () -> E0317
```

- **`e` 가 되는 이유** — 갈래의 값이 원래 `()` 라서다(`println!` 이 `()` 를 낸다).\
  없는 `else` 갈래도 `()` 이므로 **둘이 맞는다.** 값은 `()`, 크기는 **0**이다.
- 정리하면 — **`else` 가 필요한 것이 아니라 두 갈래의 타입이 맞아야** 하는 것이고,\
  `else` 가 없는 쪽은 `()` 로 채워진다. `()` 를 기대하는 자리면 `else` 가 없어도 된다.

`rustc --explain E0317`:

> An `if` expression without an `else` block has the type `()`, so this is a type error.
> To resolve it, add an `else` block having the same type as the `if` block.

### 4. `match` 팔 하나에만 세미콜론

**출력**

```text
error[E0308]: `match` arms have incompatible types
 --> ex.rs:5:16
  |
3 |       let s = match n {
  |  _____________-
4 | |         1 => "하나",
  | |              ------ this is found to be of type `&str`
5 | |         _ => { "많음"; }
  | |                ^^^^^^-
  | |                |     |
  | |                |     help: consider removing this semicolon
  | |                expected `&str`, found `()`
6 | |     };
  | |_____- `match` arms have incompatible types

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0308`.
```

**왜 그런가**

- **컴파일되지 않는다.** 에러 번호는 **E0308**, 제목 줄은 **`match` arms have incompatible types** 다.
- 컴파일러가 가리키는 곳이 셋이다.
  - 첫 팔 `"하나"` 밑 — `this is found to be of type &str`(기준이 된 팔).
  - 둘째 팔의 `"많음"` 밑 — `expected &str, found ()`.
  - **그 뒤의 세미콜론 밑** — `help: consider removing this semicolon`.
- 고치는 법은 **그 세미콜론을 지우는 것**이다. 중괄호는 남겨도 된다 — `_ => { "많음" }`.
- 규칙 한 문장: **「모든 팔이 같은 타입의 값을 내야 한다.」**\
  세미콜론 하나가 그 팔만 `()` 로 만들기 때문에 이 사고가 난다.

```text
   match n {
       1 => "하나"          -> &str
       _ => { "많음"; }     -> ()      <- 세미콜론 때문에 여기만 갈라진다
   }
            |
            v
      두 타입이 안 맞는다 -> E0308
```

### 5. `loop` 에서 값 꺼내기

**출력**

```text
found = 8 / 타입 i32
```

**출력** — `break` 값의 타입이 갈리면

```text
error[E0308]: mismatched types
 --> ex.rs:6:27
  |
5 |         if i == 1 { break 1; }
  |                     ------- expected because of this `break`
6 |         if i == 2 { break "둘"; }
  |                           ^^^^ expected integer, found `&str`

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0308`.
```

**왜 그런가**

- `found` 는 **8**이다. `i` 가 1부터 올라가며 `i * i > 50` 이 처음 참이 되는 값이 8이다(64 > 50, 49는 아니다).
- 아래쪽 `v` 는 **컴파일되지 않는다**. **E0308**, `expected integer, found &str`.\
  **첫 `break` 가 기준**이 된다 — ``expected because of this `break` `` 가 그것을 가리킨다.

```text
   loop {
       break 1;        -> i32   <- 기준이 된다
       break "둘";     -> &str  <- 안 맞는다  E0308
   }
```

**`break` 가 하나도 없는 `loop`**

- 타입은 **`!`**(발산 타입)다. 「값을 절대 내지 않는다」는 뜻이라 **어떤 타입 자리에도 들어간다.**
- 그래서 `fn never() -> i32 { loop {} }` 는 **컴파일된다**(실측 — 경고도 없다).

```text
fn never() -> i32 {
    loop {}            // 타입 ! -> i32 자리에 그대로 들어간다
}
```

- `!` 뒤에 코드를 두면 경고가 붙는다(실측).

```text
let x: i32 = loop {};
println!("{x}");

warning: unreachable statement
  = note: `#[warn(unreachable_code)]` (part of `#[warn(unused)]`) on by default
```

- `!` 의 정본은 [목록의 **06번 주제**](../06-functions-and-never-type/)(함수·반환·발산 타입)다. 여기서는 **대비까지만**.

### 6. 유닛 타입을 만나는 자리

**출력**

```text
warning: value assigned to `x` is never read
 --> ex.rs:8:17
  |
8 |     let mut x = 0;
  |                 ^
  |
  = help: maybe it is overwritten before being read?
  = note: `#[warn(unused_assignments)]` (part of `#[warn(unused)]`) on by default

warning: 1 warning emitted
```

```text
println! 도 값을 낸다
a=() b=() c=() d=()
크기 0 0 0 0
a == b ? true / x = 5
```

**왜 그런가**

- `a` `b` `c` `d` 가 **전부 `()`** 다. 크기는 넷 다 **0**이다.
- `a == b` 는 **컴파일되고 `true`** 다. `()` 는 값이 하나뿐이라 두 값이 다를 수가 없다.

```text
  fn nothing() {}          반환 타입 생략 = -> ()
  fn nothing2() -> () {}   같은 뜻
  println!(...)            매크로도 () 를 낸다
  { x = 5 }                대입도 식이고 값이 ()
        |
        +--> 넷 다 "의미 있는 값이 없다"를 () 라는 보통 타입 하나로 표현한다
```

**`d` 가 말하는 것 — C 의 `a = b = 5` 는 Rust 에서 안 된다**

```text
let mut a = 0;
let mut b = 0;
a = b = 5;

error[E0308]: mismatched types
 --> ex.rs:4:9
  |
2 |     let mut a = 0;
  |                 - expected due to this value
3 |     let mut b = 0;
4 |     a = b = 5;
  |         ^^^^^ expected integer, found `()`
```

- `b = 5` 의 값이 **`5` 가 아니라 `()`** 라서 `a` 에 못 넣는다.
- C 계열의 연쇄 대입이 Rust 에 없는 이유가 이것이다 — **대입의 값을 일부러 `()` 로 정해 두었다.**
- 부수적으로 `x = 5` 뒤에 `x` 를 읽지 않으면 `unused_assignments` 경고가 붙는다(위 출력).

### 7. 반복문에서 값을 꺼내려면

**출력**

```text
error[E0308]: mismatched types
 --> ex.rs:3:18
  |
3 |     let x: i32 = while i < 3 { i += 1; };
  |            ---   ^^^^^^^^^^^^^^^^^^^^^^^ expected `i32`, found `()`
  |            |
  |            expected due to this

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0308`.
```

**왜 그런가**

- **컴파일되지 않는다.** **E0308**, 「found」는 **`()`** 다.
- `while`·`for` 는 **식이다.** 다만 **타입이 늘 `()`** 라 값으로 쓸 수 없다.\
  「문이라서 안 된다」가 아니라 **「식인데 값이 `()` 라서」** 안 되는 것이다 — 메시지가 그 차이를 말해 준다.
- 값을 내는 반복은 **`loop` + `break 값`** 뿐이다(5번). `while`/`for` 에는 `break 값` 문법이 없다.
- 값을 **모으고** 싶으면 이터레이터로 간다 — `map`/`filter`/`collect`. 정본은 목록의 **36번 주제**다.

```text
  while / for          loop
  +---------------+    +---------------------+
  | 타입 = ()      |    | 타입 = break 값의 타입 |
  | break 값 없음  |    | break 없으면 !       |
  +---------------+    +---------------------+
```

### 8. `let` 은 식인가

**출력**

```text
error: expected expression, found `let` statement
 --> ex.rs:2:14
  |
2 |     let x = (let y = 5);
  |              ^^^
  |
  = note: only supported directly in conditions of `if` and `while` expressions

warning: unnecessary parentheses around assigned value
 --> ex.rs:2:13
  |
2 |     let x = (let y = 5);
  |             ^         ^
  |
  = note: `#[warn(unused_parens)]` (part of `#[warn(unused)]`) on by default
help: remove these parentheses
  |
2 -     let x = (let y = 5);
2 +     let x = let y = 5 ;
  |

error: aborting due to 1 previous error; 1 warning emitted
```

**왜 그런가**

- **컴파일되지 않는다.** 첫 줄은 **`error: expected expression, found let statement`** 다.\
  에러 번호가 없다 — **문법(파서) 단계**의 에러다.
- `note` 가 말하는 예외 두 곳은 **`if` 의 조건**과 **`while` 의 조건**이다\
  (`only supported directly in conditions of if and while expressions`) — 곧 **`if let`·`while let`** 이다.
- 그 예외의 정본은 목록의 **20번 주제**(`if let`·`while let`·`let else`·`let` 체인)다.

**타입을 컴파일러에게 물어보는 한 줄짜리 수법**

```rust
let v = { let a = 3; a + 1 };
let _: () = v;
```

```text
error[E0308]: mismatched types
 --> ex.rs:3:17
  |
3 |     let _: () = v;
  |            --   ^ expected `()`, found integer
  |            |
  |            expected due to this
```

- **일부러 틀린 타입(`()`)을 주면** 에러가 진짜 타입을 말해 준다.
- `type_name_of_val` 보다 강한 근거다 — 저쪽 문자열은 std 가 보장하지 않지만 **타입 검사 결과는 언어 규칙**이다.
- 세미콜론을 넣었다 뺐다 하며 이걸 반복하면 이 주제의 규칙이 손에 붙는다.

### 9. `()` 는 무엇인가

**왜 그런가**

- **「값이 없음」으로 읽으면 두 군데가 틀린다.**
  - `()` 는 **타입**이고 그 타입의 **값도 `()`** 다. 변수에 담기고(`let a = nothing();`) 비교도 된다(`a == b` 가 `true`).
  - `Vec<()>`·`Option<()>`·`Result<(), E>` 처럼 **타입 인자 자리에도 들어간다.**\
    `fn main() -> Result<(), E>` 가 바로 그 형태다([**01번 주제**](../01-cargo-crates-and-modules/) 5번).
- **크기가 0인 이유** — 값이 하나뿐이라 **구별할 정보가 없기 때문**이다.\
  비트를 한 개도 쓰지 않아도 「어떤 값인지」가 늘 정해진다.
- 반환 타입을 안 적은 함수의 실제 반환 타입은 **`()`** 다. `fn nothing() {}` 과 `fn nothing2() -> () {}` 는 같은 뜻이다(6번).
- **`void` 가 없는 이유** — `void` 는 「타입이 아닌 것」이라 특별 취급이 필요하다.\
  제네릭에 못 넣고, 변수에 못 담고, 반환 규칙이 따로 생긴다.\
  Rust 는 **값이 하나뿐인 보통 타입**을 하나 두어 그 특별 취급을 전부 없앴다.

```text
   void (특별 취급)                    () (보통 타입)
   +--------------------------+       +--------------------------+
   | 변수에 못 담는다           |       | let a = nothing();  OK   |
   | 제네릭 인자로 못 쓴다      |       | Vec<()>             OK   |
   | 반환 규칙이 따로 있다      |       | Result<(), E>       OK   |
   +--------------------------+       +--------------------------+
                                        크기 0바이트 — 비용도 없다
```

### 10. `return` 과 꼬리 표현식

**출력** — `rustc`

```text
$ cat ex.rs
fn f(a: i32) -> i32 {
    return a + 1;
}
fn main() { println!("{}", f(1)); }

$ rustc --edition 2021 ex.rs -o ex
(아무 줄도 없음)

$ ./ex
2
```

**출력** — `cargo clippy`(기본 설정)

```text
warning: unneeded `return` statement
 --> src/main.rs:2:5
  |
2 |     return a + 1;
  |     ^^^^^^^^^^^^
  |
  = help: for further information visit https://rust-lang.github.io/rust-clippy/rust-1.92.0/index.html#needless_return
  = note: `#[warn(clippy::needless_return)]` on by default
help: remove `return`
  |
2 -     return a + 1;
2 +     a + 1
  |
```

**왜 그런가**

- **`rustc` 는 아무 말도 안 한다.** 문법적으로 완전히 정상이다.
- **`clippy` 는 기본 설정에서 잡는다** — `clippy::needless_return`, `on by default`.\
  관용은 **꼬리 표현식**이고 `return` 은 **중간에서 빠져나갈 때** 쓴다는 뜻이다.
- **`return` 은 식이다.** 타입은 **`!`**(발산)다. 값을 내지 않고 그 자리에서 함수를 떠난다.

`let b: i32 = if a < 0 { return -1 } else { a };` **가 컴파일되는 이유**

```text
   if a < 0 { return -1 } else { a }
                  |                |
                  !               i32
                  |                |
       ! 는 어떤 타입으로도 강제된다 |
                  +--------+-------+
                           v
                          i32   -> b 에 들어간다
```

- `!` 가 `i32` 자리에 **강제**되므로 두 갈래의 타입이 `i32` 로 맞는다(3번의 규칙을 그대로 통과한다).
- 실측 — `mixed(-3) = -1`, `mixed(3) = 30`. 첫 갈래를 타면 함수가 **거기서 끝난다.**
- `!` 의 정본은 [목록의 **06번 주제**](../06-functions-and-never-type/)다.

### 11. 다른 주제와 잇기

- **발산 타입 `!`** — [목록의 **06번 주제**](../06-functions-and-never-type/)(함수·반환·발산 타입 `!`).\
  이 주제에서는 `loop {}`·`return`·`break` 가 `!` 라는 **대비까지만** 했다.
- **`loop`·라벨·`break` 값 전수** — [목록의 **05번 주제**](../05-control-flow-loops-and-labels/)(제어 흐름).
- **`match` 의 완전성 검사** — 목록의 **18번 주제**. 패턴 문법 전수는 **19번 주제**.
- **`size_of::<()>() == 0` 실측 표** — [**03번 주제**](../03-primitive-types-and-integer-overflow/)(기본 타입) 6번에 19종 표가 있다.
- **에러가 아니라 경고로만 드러나는 자리** — **1번**(`let z = { ... a + 1; };`)이다.\
  기대 타입이 없어서 `z` 가 `()` 로 받아들여지고 `unused_must_use` 경고만 난다.\
  에러로 바꾸는 법은 둘 — **`let z: i32 = ...` 로 기대 타입을 적거나**, `#![deny(unused_must_use)]`·`-D warnings` 로 린트를 올린다.

---

## 실행 검증

| 실험 (`ex.rs`) | 무엇을 확인했나 | 결과 |
|---|---|---|
| `let y = { a + 1 }` ↔ `let z = { a + 1; }` | `y = 4`(i32) / `z = ()` · 크기 0 · **경고** `unused_must_use` | 1 |
| `fn plus_one(a: i32) -> i32 { a + 1; }` | **E0308** + `implicitly returns ()` + `remove this semicolon` | 2 |
| `if c {1} else {2}` · `if c { println!(); }` | `a = 1` · `e = ()` 크기 0 | 3 |
| `if c {1} else {"둘"}` | **E0308** `if and else have incompatible types` | 3 |
| `if c {1}` | **E0317** + `note: … evaluate to ()` | 3 |
| `rustc --explain E0317` | 공식 설명 인용 | 3 |
| `match` 한 팔만 세미콜론 | **E0308** `match arms have incompatible types` + 세미콜론 지목 | 4 |
| `loop { if i*i>50 { break i; } }` | `found = 8` | 5 |
| `loop` 안에서 `break 1` / `break "둘"` | **E0308** `expected because of this break` | 5 |
| `fn never() -> i32 { loop {} }` | **컴파일 성공** — `loop {}` 의 타입이 `!` | 5 |
| `let x: i32 = loop {}; println!("{x}");` | `unreachable_code` 경고 | 5 |
| `nothing()`/`nothing2()`/`println!`/`{ x = 5 }` | 넷 다 `()` · 크기 0 0 0 0 · `a == b` 가 `true` | 6 |
| `a = b = 5;` | **E0308** `expected integer, found ()` | 6 |
| `let x: i32 = while i < 3 { i += 1; };` | **E0308** `found ()` | 7 |
| `let x = (let y = 5);` | `expected expression, found let statement` + `note` 로 예외 두 곳 | 8 |
| `let _: () = v;` | **E0308** 가 진짜 타입을 말해 준다 | 8 |
| `return a + 1;` 을 꼬리에 | `rustc` **무진단** / `clippy` **`needless_return`**(기본 켜짐) | 10 |
| `if a < 0 { return -1 } else { a }` | `mixed(-3) = -1` · `mixed(3) = 30` | 10 |
| `tail`/`early` 3식 | `6` · `0` · `6` | 10 |

**구현·설정에 달린 항목**(다시 찍을 자리)

| 항목 | 무엇에 달렸나 |
|---|---|
| 에러·경고 **문구와 화살표 배치** | rustc 구현. **에러 번호**가 더 안정적이다 |
| `unused_must_use` 가 **경고**인 것 | 린트 설정. `#[deny]`·`-D warnings` 로 에러가 된다 |
| 꼬리 `return` 에 `rustc` 가 침묵하는 것 | 린트 설정. `clippy::needless_return` 은 기본으로 잡는다 |
| `clippy` 린트 이름·문서 URL | **clippy 버전**(0.1.92) |
| `type_name_of_val` 이 돌려주는 문자열 | **보장 없음** — std 문서가 명시. 타입의 근거는 컴파일 에러 쪽이다 |
| **세미콜론·블록·`if`/`match`/`loop` 의 타입 규칙** | **전부 언어 보장.** 빌드 프로필·플랫폼에 흔들리지 않는다 |
