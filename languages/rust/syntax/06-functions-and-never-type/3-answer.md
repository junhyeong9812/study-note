# rust/syntax/06 — 함수·반환·발산 타입 `!` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러·경고는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)`** 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 얻은 것이다. `cargo` 는 쓰지 않았다.\
> 소스 파일 이름은 전부 `ex.rs` 로 고정했다. **줄 번호는 그 실험 파일 기준**이라 질문의 발췌와 어긋날 수 있다.\
> ★ 패닉 메시지 **괄호 안 번호**(`(1778250)`)는 **실행마다 바뀐다.** 출력을 그대로 옮기느라 남겨 두었을 뿐,\
> 근거로 읽을 칸이 아니다.\
> ★ 이 주제는 **디버그·릴리스로 갈리는 자리가 없다** — 전부 컴파일 타임 타입 규칙이다.\
> 타입의 근거는 **컴파일 에러**다(`let _: () = 식;` 수법 — [**04번 주제**](../04-expressions-and-semicolons/) 8번).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 함수 넷의 반환값과 크기

**출력**

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
add = 5
안녕 러스트
u = () / 크기 = 0
early(-1) = 0 / early(5) = 10
(종료 코드 0)
```

**왜 그런가**

- `add(2, 3)` 은 **5**, `early(-1)` 은 **0**, `early(5)` 는 **10**이다.
- `greet` 와 `unit_explicit` 의 반환 타입은 **둘 다 `()`** 다. **완전히 같은 뜻**이다 —\
  반환 타입을 생략하는 것이 `-> ()` 를 적는 것이다.
- `u` 의 값은 **`()`**, 크기는 **0바이트**다.
- **인자 타입은 생략할 수 없고**(10번), **반환 타입만 생략할 수 있다.**

```text
   fn add(a: i32, b: i32) -> i32 { a + b }
          --------------    ---     -----
          의무              생략 가능  꼬리 표현식 = 반환값

   fn greet(name: &str) { ... }     ==     fn greet(name: &str) -> () { ... }
```

- 몸통 마지막 줄에 세미콜론이 없으면 그것이 **꼬리 표현식**이고 반환값이 된다.
- `early` 처럼 **중간에서 빠져나갈 때만** `return` 을 쓰는 것이 관용이다.\
  꼬리와 `return` 의 정본은 [**04번 주제**](../04-expressions-and-semicolons/)다.

> **꼬리 표현식(tail expression)** — 몸통의 마지막에 세미콜론 없이 놓인 식. 그 함수의 반환값이 된다.\
> 예: `fn add(a: i32, b: i32) -> i32 { a + b }` 의 `a + b`.

### 2. ★ 마지막 줄을 건드린 함수 둘

**출력** — `fn twice(a: i32) -> i32 { a * 2; }`

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
error[E0308]: mismatched types
 --> ex.rs:1:21
  |
1 | fn twice(a: i32) -> i32 {
  |    -----            ^^^ expected `i32`, found `()`
  |    |
  |    implicitly returns `()` as its body has no tail or `return` expression
2 |     a * 2;
  |          - help: remove this semicolon to return this value

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0308`.
```

**출력** — `fn half(a: i32) -> i32 { if a < 0 { return 0; } }`

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
error[E0317]: `if` may be missing an `else` clause
 --> ex.rs:2:5
  |
1 | fn half(a: i32) -> i32 {
  |                    --- expected `i32` because of this return type
2 |     if a < 0 { return 0; }
  |     ^^^^^^^^^^^^^^^^^^^^^^ expected `i32`, found `()`
  |
  = note: `if` expressions without `else` evaluate to `()`
  = help: consider adding an `else` block that evaluates to the expected type

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0317`.
```

**왜 그런가**

- **둘 다 컴파일되지 않는다.** 그런데 **번호가 다르다** — `twice` 는 **E0308**, `half` 는 **E0317**이다.
- 둘을 가른 것은 「**몸통의 마지막에 무엇이 있느냐**」다.

```text
   fn twice ... { a * 2; }              fn half ... { if a < 0 { return 0; } }
                       ^                              ^^^^^^^^^^^^^^^^^^^^^^
                  세미콜론이 값을 버린다          else 없는 if 가 꼬리에 있다
                       |                                     |
                       v                                     v
            "꼬리가 아예 없다"                      "꼬리는 있는데 그 타입이 ()"
                       |                                     |
                       v                                     v
              E0308 mismatched types            E0317 may be missing an `else` clause
              help: remove this semicolon       help: consider adding an `else` block
```

- `help:` 가 가리키는 고칠 곳도 다르다 — 앞엣것은 **세미콜론**, 뒤엣것은 **`else` 블록**이다.
- 「`implicitly returns () as its body has no tail or return expression`」은\
  **꼬리 표현식도 `return` 도 없으면 함수가 암묵적으로 `()` 를 돌려준다**는 뜻이다.
- ★ **번호를 먼저 읽어라.** 둘 다 `expected i32, found ()` 라서 문구만 보면 같아 보인다.

`rustc --explain E0317`:

> An `if` expression without an `else` block has the type `()`, so this is a type
> error. To resolve it, add an `else` block having the same type as the `if`
> block.

### 3. ★ 기대 타입이 `i32` 인 자리에 `panic!`

**출력**

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
warning: unreachable statement
 --> ex.rs:4:5
  |
3 |     let x: i32 = panic!("여기서 끝");
  |                  ------------------- any code following this expression is unreachable
4 |     println!("{x}");
  |     ^^^^^^^^^^^^^^^ unreachable statement
  |
  = note: `#[warn(unreachable_code)]` (part of `#[warn(unused)]`) on by default
  = note: this warning originates in the macro `println` (in Nightly builds, run with -Z macro-backtrace for more info)

warning: unused variable: `x`
 --> ex.rs:3:9
  |
3 |     let x: i32 = panic!("여기서 끝");
  |         ^ help: if this is intentional, prefix it with an underscore: `_x`
  |
  = note: `#[warn(unused_variables)]` (part of `#[warn(unused)]`) on by default

warning: 2 warnings emitted

시작

thread 'main' (1778250) panicked at ex.rs:3:18:
여기서 끝
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
(종료 코드 101)
```

**왜 그런가**

- **컴파일된다.** 에러는 하나도 없고 **경고가 둘**이다.
- 린트 이름은 **`unreachable_code`** 와 **`unused_variables`** 다.
- 출력은 `시작` 한 줄뿐이고, 그 다음 줄에서 **패닉**한다. **종료 코드는 101**이다.
- `x` 에는 **아무것도 안 들어간다.** 대입이 일어나기 전에 프로그램이 끝나기 때문이다.

```text
   let x: i32 = panic!("여기서 끝");
          |          |
        i32 를        ! 를 낸다 (= 값이 절대 안 만들어진다)
       기대한다          |
          |             v
          +---- ! 가 i32 로 강제된다 -> 타입 검사 통과
                        |
                        v
                  실행하면 그 줄에서 끝
                  다음 줄은 unreachable -> 경고
```

- ★ **이 자리가 조용하다.** 에러가 안 나므로 **경고를 안 읽으면 못 잡는다.**
- 패닉 줄의 괄호 안 번호(`(1778250)`)는 **실행마다 바뀐다** — 근거로 읽을 칸이 아니다.

> **발산 타입 `!`** — 값이 절대 만들어지지 않는 것의 타입. never type.\
> 예: `panic!()` · `std::process::exit(2)` · 끝나지 않는 `loop {}`.

### 4. ★ 네 자리에 넣은 세 가지

**출력**

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
a=1 b=문자열 c=[7] d=true
parse = 42
(종료 코드 0)
```

**왜 그런가**

- **네 줄 다 컴파일된다.** 경고도 없다(`flag` 가 런타임 값이라 도달 불가 판정이 안 난다).
- `if` 두 갈래의 타입이 같아야 한다는 규칙은 **`!` 가 다른 갈래 쪽으로 맞춰 주면서** 통과한다.
- 세 식의 공통 타입은 **`!`**(발산)다.
- **들어갈 수 없는 타입 자리는 없다.** `!` 는 **모든 타입으로 강제**된다.

```text
              panic!()   process::exit(3)   loop {}
                  |             |              |
                  +------+------+--------------+
                         v
                    타입은 전부 !
                         |
         +-------+-------+--------+---------+
         v       v       v        v         v
        i32   String   Vec<u8>   bool     ...  어떤 타입이든

   이유 한 줄: 값이 절대 안 만들어지니, 타입을 어길 일도 일어나지 않는다.
```

- `parse` 가 이 규칙의 실용 형태다 — `Ok(n) => n`(`i32`)와 `Err(_) => panic!(…)`(`!`)가 한 `match` 에 있다.\
  전체 타입은 **`i32`** 로 정해진다(5번).

> **강제(coercion)** — 타입 A 의 값이 타입 B 를 기대하는 자리에서 자동으로 B 로 쓰이는 것.\
> 예: `!` 는 모든 타입으로 강제된다. `let x: i32 = panic!();` 이 통과하는 이유다.

### 5. `match` 한 갈래만 다른 것

**출력** — 위쪽(`let _: () = match …`)

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
error[E0308]: mismatched types
 --> ex.rs:4:17
  |
4 |       let _: () = match n {
  |  ____________--___^
  | |            |
  | |            expected due to this
5 | |         1 => "하나",
6 | |         _ => panic!("없음"),
7 | |     };
  | |_____^ expected `()`, found `&str`

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0308`.
```

**출력** — 아래쪽(모든 갈래가 `!`)

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
warning: unreachable statement
 --> ex.rs:7:5
  |
3 |       let both_never: i32 = match n {        // 두 갈래가 다 ! 다
  |  ___________________________-
4 | |         1 => panic!("a"),
5 | |         _ => std::process::exit(1),
6 | |     };
  | |_____- any code following this `match` expression is unreachable, as all arms diverge
7 |       println!("{both_never}");
  |       ^^^^^^^^^^^^^^^^^^^^^^^^ unreachable statement
  |
  = note: `#[warn(unreachable_code)]` (part of `#[warn(unused)]`) on by default
  = note: this warning originates in the macro `println` (in Nightly builds, run with -Z macro-backtrace for more info)

warning: unused variable: `both_never`
 --> ex.rs:3:9
  |
3 |     let both_never: i32 = match n {        // 두 갈래가 다 ! 다
  |         ^^^^^^^^^^ help: if this is intentional, prefix it with an underscore: `_both_never`
  |
  = note: `#[warn(unused_variables)]` (part of `#[warn(unused)]`) on by default

warning: 2 warnings emitted


thread 'main' (1781395) panicked at ex.rs:4:14:
a
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
(종료 코드 101)
```

**왜 그런가**

- 위쪽 `match` 전체의 타입은 **`&str`** 이다. 일부러 `()` 를 기대시켰더니 **`found &str`** 이라고 답했다.
- 즉 **`!` 갈래는 타입을 주장하지 않고**, 남은 갈래가 전체 타입을 정한다.
- 아래쪽은 **컴파일된다.** `i32` 자리에 **`String` 을 적어도 그대로 통과한다**(실측 — 같은 경고 둘만 난다).
- 경고의 `note` 는 **`as all arms diverge`** — 「갈래가 전부 발산해서 그 뒤가 도달 불가」라는 뜻이다.

```text
   match n {                       match n {
       1 => "하나"     -> &str          1 => panic!()   -> !
       _ => panic!()   -> !             _ => exit(1)    -> !
   }                               }
        |                               |
        v                               v
   전체 타입 = &str                정할 것이 없다 -> 아무 타입이나 받는다
   (! 가 &str 쪽으로 맞춘다)       그 뒤는 unreachable
```

- 「모든 팔이 같은 타입을 내야 한다」는 규칙([**04번 주제**](../04-expressions-and-semicolons/) 4번)과 어긋나지 않는다 —\
  **`!` 는 어떤 타입에도 맞춰지므로 애초에 어긋날 수가 없다.**

### 6. 함수 이름을 변수에 담으면

**출력** — 되는 쪽

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
p(21) = 42
apply = 10
c(1) = 2
fn 포인터 크기 = 8
fn 아이템 크기 = 0
(종료 코드 0)
```

**출력** — `let _: () = double;` 과 `f = triple;`

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
error[E0308]: mismatched types
 --> ex.rs:4:17
  |
4 |     let _: () = double;                 // fn 아이템의 진짜 타입을 물어본다
  |            --   ^^^^^^ expected `()`, found fn item
  |            |
  |            expected due to this
  |
  = note: expected unit type `()`
               found fn item `fn(i32) -> i32 {double}`

error[E0308]: mismatched types
 --> ex.rs:6:9
  |
5 |     let mut f = double;                 // f 의 타입은?
  |                 ------ expected due to this value
6 |     f = triple;                         // 다른 함수를 넣어 보면?
  |         ^^^^^^ expected fn item, found a different fn item
  |
  = note: expected fn item `fn(_) -> _ {double}`
             found fn item `fn(_) -> _ {triple}`
  = note: different fn items have unique types, even if their signatures are the same
  = help: consider casting both fn items to fn pointers using `as fn(i32) -> i32`

error: aborting due to 2 previous errors

For more information about this error, try `rustc --explain E0308`.
```

**왜 그런가**

- `p` 는 **만들어진다.** `let p: fn(i32) -> i32 = double;` 은 아이템을 **포인터로 강제**한다.
- `f = triple;` 은 **E0308** 로 거부된다. `note` 가 이유를 말한다 —\
  **`different fn items have unique types, even if their signatures are the same`**.
- `double` 의 진짜 타입 이름은 **`fn(i32) -> i32 {double}`** 다. 함수 이름이 타입 안에 들어 있다.
- 두 수는 **8**과 **0**이다.

```text
   double 이라는 이름
        |
        v
   fn 아이템 타입  fn(i32) -> i32 {double}    <- 함수마다 고유. 크기 0바이트
        |
        | fn(i32) -> i32 라고 적으면 강제된다
        v
   fn 포인터 타입  fn(i32) -> i32             <- 여러 함수가 공유. 크기 8바이트
```

- **아이템이 0바이트인 이유** — 어느 함수인지가 **타입에 이미 적혀 있어서** 실행 시에 담을 것이 없다.
- **포인터가 8바이트인 이유** — 여러 함수가 같은 타입을 쓰므로 **어느 함수인지를 값으로 들고 다녀야** 한다.
- 컴파일러가 주는 고치는 법 둘 — ① 타입을 **`fn(i32) -> i32` 로 적는다**\
  ② **`as fn(i32) -> i32` 로 캐스팅**한다(`help:` 가 그렇게 말한다).
- 8은 **이 머신(64비트)의 포인터 폭**이다 — 플랫폼에 달렸다.

> **fn 아이템(fn item)** — `fn` 으로 선언한 함수 자체의 타입. 함수마다 고유하고 크기가 0바이트다.\
> 예: `double` 이라는 이름의 타입은 `fn(i32) -> i32 {double}` 이다.

### 7. ★ `!` 를 타입으로 적을 수 있는 자리

**출력** — 통과하는 것 (가)·(나)

```text
===== 소스: ex.rs =====
fn spin() -> ! { loop {} }
fn main() {
    let p: fn() -> ! = spin;          // 반환 위치의 ! 를 포인터 타입에 적으면?
    let _ = p;
    println!("ok");
}
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
ok
(종료 코드 0)
```

**출력** — (다) `let x: ! = panic!();`

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
error[E0658]: the `!` type is experimental
 --> ex.rs:2:12
  |
2 |     let x: ! = panic!("이 타입 표기가 되나");
  |            ^
  |
  = note: see issue #35121 <https://github.com/rust-lang/rust/issues/35121> for more information
```

**출력** — (라) `Vec<!>` · `Option<!>`

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
error[E0658]: the `!` type is experimental
 --> ex.rs:2:20
  |
2 | fn opt() -> Option<!> { None }            // 제네릭 인자 자리의 !
  |                    ^
  |
  = note: see issue #35121 <https://github.com/rust-lang/rust/issues/35121> for more information

error[E0658]: the `!` type is experimental
 --> ex.rs:5:16
  |
5 |     let v: Vec<!> = Vec::new();           // 제네릭 인자 자리
  |                ^
  |
  = note: see issue #35121 <https://github.com/rust-lang/rust/issues/35121> for more information

error: aborting due to 2 previous errors

For more information about this error, try `rustc --explain E0658`.
```

**출력** — (마) 인자 자리 · (바) 타입 별칭

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
error[E0658]: the `!` type is experimental
 --> ex.rs:1:12
  |
1 | fn take(x: !) -> i32 { x }                // 인자 자리의 !
  |            ^
  |
  = note: see issue #35121 <https://github.com/rust-lang/rust/issues/35121> for more information
```

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
error[E0658]: the `!` type is experimental
 --> ex.rs:1:14
  |
1 | type Never = !;
  |              ^
  |
  = note: see issue #35121 <https://github.com/rust-lang/rust/issues/35121> for more information
```

**왜 그런가**

- 통과하는 것은 **(가)와 (나) 둘뿐**이다. 나머지 넷은 전부 **E0658 `the ! type is experimental`** 이다.

| 자리 | 예 | 결과 |
|---|---|---|
| (가) 함수의 반환 위치 | `fn spin() -> !` | **된다** |
| (나) 함수 포인터 타입의 반환 위치 | `let p: fn() -> ! = spin;` | **된다** |
| (다) 지역 변수 타입 표기 | `let x: ! = panic!();` | E0658 |
| (라) 제네릭 인자 | `Vec<!>` · `Option<!>` | E0658 |
| (마) 함수 인자 타입 | `fn take(x: !)` | E0658 |
| (바) 타입 별칭 | `type Never = !;` | E0658 |

```text
   ! 를 적을 수 있는 자리
   +--------------------------------+
   |  fn ... -> !        (가)       |   <- 반환 위치
   |  fn() -> !          (나)       |   <- 함수 포인터의 반환 위치
   +--------------------------------+
   그 밖의 모든 타입 자리 -> E0658
```

- 「experimental」은 **버전도 에디션도 아니라 툴체인 채널**에 달린 문제다.\
  stable·beta 에서는 못 쓰고, nightly 에서 `#![feature(never_type)]` 로 연다(추적 이슈 #35121).
- ★ 규칙 한 문장 — **「stable 에서 `!` 는 반환 위치에만 적을 수 있다.」**
- ★ (나)가 통과한다는 것이 이 지도의 핵심이다. E0658 이 막는 것은 **독립된 타입으로서의 `!`** 이지\
  **반환 위치 자체**가 아니다.

`rustc --explain E0658`:

> An unstable feature was used.
>
> (… 예제 생략 …)
>
> If you're using a stable or a beta version of rustc, you won't be able to use
> any unstable features. In order to do so, please switch to a nightly version of
> rustc (by using [rustup]).

### 8. `-> !` 가 약속하는 것

**출력** — `die`

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
n = 7
치명적: 정상 종료 경로 아님
(종료 코드 2)
```

**출력** — `bad`

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
error[E0308]: mismatched types
 --> ex.rs:1:13
  |
1 | fn bad() -> ! {
  |    ---      ^ expected `!`, found `()`
  |    |
  |    implicitly returns `()` as its body has no tail or `return` expression
  |
  = note:   expected type `!`
          found unit type `()`

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0308`.
```

**왜 그런가**

- `die` 는 **컴파일된다.** 종료 코드는 **2**다 — `std::process::exit(2)` 에 내가 준 값이다.\
  (패닉의 101과 달리 이건 **프로그램이 고른 값**이다.)
- `bad` 는 **E0308** 로 거부된다. 「**expected `!`, found `()`**」다.
- 붙는 설명 한 줄은 2번의 `twice` 와 **완전히 같은 문장**이다 —\
  **`implicitly returns () as its body has no tail or return expression`**.\
  즉 `-> i32` 든 `-> !` 든, **몸통이 그냥 끝나면 `()` 를 낸다**는 같은 규칙에 걸린다.

```text
   fn die(..) -> ! {                  fn bad() -> ! {
       process::exit(2);                  println!("...");
   }                                  }
       |                                  |
   끝까지 가지 않는다                   끝까지 가서 () 를 낸다
       |                                  |
       v                                  v
     통과                            E0308 expected `!`, found `()`
```

- `-> !` 함수의 몸통 마지막에 올 수 있는 것은 **패닉 · 프로세스 종료 · 끝나지 않는 `loop`** 다.\
  (`spin()` 처럼 `loop {}` 만으로도 된다.)
- `die` 를 값이 필요한 자리에 써도 된다 — `let n: i32 = if … { die("인자") } else { 7 };` 가 통과했다(4번의 규칙).

### 9. 클로저와 `fn` 포인터의 경계

**출력** — `c2`(환경을 잡는 클로저)

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
error[E0308]: mismatched types
 --> ex.rs:3:29
  |
3 |     let c: fn(i32) -> i32 = |x| x + k;
  |            --------------   ^^^^^^^^^ expected fn pointer, found closure
  |            |
  |            expected due to this
  |
  = note: expected fn pointer `fn(i32) -> i32`
                found closure `{closure@ex.rs:3:29: 3:32}`
note: closures can only be coerced to `fn` types if they do not capture any variables
 --> ex.rs:3:37
  |
3 |     let c: fn(i32) -> i32 = |x| x + k;
  |                                     ^ `k` captured here

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0308`.
```

**출력** — `inner`(함수 안의 함수)

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
error[E0434]: can't capture dynamic environment in a fn item
 --> ex.rs:3:25
  |
3 |     fn inner() -> i32 { k + 1 }          // 함수 안의 함수가 바깥 변수를 보나?
  |                         ^
  |
  = help: use the `|| { ... }` closure form instead

warning: unused variable: `k`
 --> ex.rs:2:9
  |
2 |     let k = 10;
  |         ^ help: if this is intentional, prefix it with an underscore: `_k`
  |
  = note: `#[warn(unused_variables)]` (part of `#[warn(unused)]`) on by default

error: aborting due to 1 previous error; 1 warning emitted

For more information about this error, try `rustc --explain E0434`.
```

**왜 그런가**

- **`c1` 은 컴파일되고 `c2` 는 안 된다.** `c1` 은 아무것도 안 잡으므로 포인터로 강제된다(6번 출력 `c(1) = 2`).
- `c2` 는 **E0308** 이고, `note` 가 규칙을 한 줄로 말한다 —\
  **`closures can only be coerced to fn types if they do not capture any variables`**.\
  그리고 **`k` captured here** 로 잡은 변수를 정확히 짚는다.
- `inner` 도 **거부된다.** **E0434 `can't capture dynamic environment in a fn item`**,\
  `help: use the || { ... } closure form instead`.

```text
   |x| x + 1          아무것도 안 잡는다   ->  fn(i32) -> i32 로 강제 가능
   |x| x + k          k 를 잡는다         ->  포인터에 담을 자리가 없다  E0308
   fn inner() { k }   fn 아이템은 못 잡는다 ->  E0434
```

- 가르는 기준 한 문장 — 「**환경을 잡느냐**」다.\
  잡은 값은 어딘가에 들고 다녀야 하는데 **`fn` 포인터에는 그 자리가 없다**(주소 8바이트뿐).
- `--explain E0434` 가 주는 해결책은 **둘**이다.
  - ① **클로저로 바꾼다** — 「To fix this error, you can replace the function with a closure」.
  - ② **잡을 값을 상수로 올린다** — 「Or replace the captured variable with a constant or a static item」\
    ([**07번 주제**](../07-const-static-and-const-fn/)).
- 클로저 세 트레이트의 정본은 [목록의 **34번 주제**](../34-closures-fn-fnmut-fnonce-and-move/), 클로저 반환은 [목록의 **35번 주제**](../35-function-pointers-and-returning-closures/)다.

### 10. 인자 타입과 같은 이름

**출력** — `fn add(a, b) -> i32`

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
error: expected one of `:`, `@`, or `|`, found `,`
 --> ex.rs:1:9
  |
1 | fn add(a, b) -> i32 { a + b }
  |         ^ expected one of `:`, `@`, or `|`
  |
help: if this is a parameter name, give it a type
  |
1 | fn add(a: TypeName, b) -> i32 { a + b }
  |         ++++++++++
help: if this is a type, explicitly ignore the parameter name
  |
1 | fn add(_: a, b) -> i32 { a + b }
  |        ++

error: expected one of `:`, `@`, or `|`, found `)`
 --> ex.rs:1:12
  |
1 | fn add(a, b) -> i32 { a + b }
  |            ^ expected one of `:`, `@`, or `|`
  |
help: if this is a parameter name, give it a type
  |
1 | fn add(a, b: TypeName) -> i32 { a + b }
  |            ++++++++++
help: if this is a type, explicitly ignore the parameter name
  |
1 | fn add(a, _: b) -> i32 { a + b }
  |           ++

error: aborting due to 2 previous errors
```

**출력** — 같은 이름의 함수 둘

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
error[E0428]: the name `add` is defined multiple times
 --> ex.rs:2:1
  |
1 | fn add(a: i32, b: i32) -> i32 { a + b }
  | ----------------------------- previous definition of the value `add` here
2 | fn add(a: f64, b: f64) -> f64 { a + b }      // 같은 이름, 다른 시그니처
  | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ `add` redefined here
  |
  = note: `add` must be defined only once in the value namespace of this module

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0428`.
```

**왜 그런가**

- 위쪽은 **에러 번호가 붙지 않는다.** 제목 줄이 `error:` 로 시작하고 그 뒤가\
  「expected one of `:`, `@`, or `|`, found `,`」다 — 위 출력 그대로다.
- ★ **번호가 없다는 것은 「파서 단계에서 막혔다」는 뜻**이다.\
  타입 검사까지 가지도 못했다 — **문법이 아예 성립하지 않는다.**\
  번호가 붙은 에러(E0308·E0428)는 **문법은 읽혔는데 의미가 틀린** 것이다.
- 아래쪽은 **오버로딩이 아니라 중복 정의**다 — **E0428**,\
  `note: add must be defined only once in the value namespace of this module`.
- 「같은 일을 여러 타입에 대해」 하려면 **제네릭과 트레이트**로 간다 —\
  [목록의 **25번 주제**](../25-traits-definition-impl-default-methods-and-associated-types/)(트레이트) · **31번 주제**(제네릭·트레이트 경계).

```text
   fn add(a, b)            -> 파서 에러 (번호 없음)   "문법이 아니다"
   fn add(..) 가 둘        -> E0428 (번호 있음)      "문법은 맞는데 이름이 겹친다"
```

`rustc --explain E0428`:

> A type or module has been defined more than once.
>
> (… 예제 생략 …)
>
> Please verify you didn't misspell the type/module's name or remove/rename the
> duplicated one. Example:

★ 설명이 「이름을 고치거나 지워라」로 끝난다 — **오버로딩이라는 선택지가 아예 없다.**

### 11. `!` 와 `()` 는 무엇이 다른가

**왜 그런가**

- 정의 한 문장씩.
  - **`()`** 는 **값이 딱 하나뿐인 타입**이다. 「의미 있는 값이 없다」를 나타낸다.
  - **`!`** 는 **값이 하나도 없는 타입**이다. 「여기서 값이 안 만들어진다」를 나타낸다.
- **`()` 의 크기는 0이다**(실측 — `size_of::<()>()` 가 `0`, `u = () / 크기 = 0`).\
  **`!` 의 크기는 이 툴체인에서 잴 수 없다** — `size_of::<!>()` 를 적으려면 `!` 를 제네릭 인자로 써야 하고\
  그 자리가 **E0658** 이다(7번의 (라)). ★ **「안 돌려 봄」이 아니라 「stable 에서는 잴 수 없다」가 답이다.**
- `let a = nothing();` 은 되고 `let x: ! = panic!();` 은 안 되는 이유는 **두 층이 다르다.**
  - 앞엣것은 **`()` 라는 값이 실제로 존재**하므로 변수에 담긴다.
  - 뒤엣것은 값의 문제가 아니라 **`!` 를 타입 표기 자리에 적은 것**이 stable 에서 막힌 것이다(E0658).\
    같은 코드에서 **타입 표기만 지우면**(`let x = panic!();`) 그 문제는 사라진다.

```text
   "값이 하나뿐"                      "값이 하나도 없다"
   +------------------+              +------------------+
   | ()               |              | !                |
   | 크기 0           |              | 값이 생기지 않는다 |
   | 변수에 담긴다     |              | 담을 값이 없다     |
   | 어디에나 적는다   |              | 반환 위치에만 적는다|
   +------------------+              +------------------+
```

- **호출자 쪽에서 다른 것** — `-> ()` 함수는 **돌아온다.** 그 다음 줄이 실행된다.\
  `-> !` 함수는 **안 돌아온다.** 그래서 그 다음 줄이 `unreachable_code` 로 잡히고,\
  값이 필요한 자리에 놓여도 타입이 맞는다.
- `()` 의 정본은 [**04번 주제**](../04-expressions-and-semicolons/)다.

### 12. 다른 주제와 잇기

- **꼬리 표현식과 `return`** — [**04번 주제**](../04-expressions-and-semicolons/)(표현식 지향)가 정본이다.\
  이 주제는 그것이 **함수 경계에서 어떤 에러 번호가 되는지**(E0308·E0317)만 다룬다.
- **끝나지 않는 `loop` 가 `!`** 라는 사실 — [**05번 주제**](../05-control-flow-loops-and-labels/)(제어 흐름)에서 나왔다.\
  거기서 `fn forever() -> i32 { loop {} }` 가 컴파일되는 것을 실측했다.
- **클로저 세 트레이트** — [목록의 **34번 주제**](../34-closures-fn-fnmut-fnonce-and-move/). **클로저 반환** — [목록의 **35번 주제**](../35-function-pointers-and-returning-closures/).\
  여기서는 **fn 포인터와의 대비까지만** 했다.
- **`panic!` 대 `Result`** — [목록의 **23번 주제**](../23-panic-vs-result/)가 정본이다.\
  이 주제는 「어디서 끝낼 것인가」를 다루지 않는다 — **`panic!` 의 타입이 `!` 라는 사실 하나**만 쓴다.
- **함수 인자·반환이 값을 이동시킨다** — [**08번 주제**](../08-ownership-and-move/)(소유권과 이동)다.\
  이 주제의 `fn add(a: i32, b: i32)` 가 조용했던 것은 `i32` 가 `Copy` 라서다.
- **에러가 아니라 경고로만 드러나는 자리** — **3번**과 **5번**이다.\
  `!` 가 들어간 줄은 타입 검사를 통과하고 **`unreachable_code` 경고만** 남긴다.\
  에러로 바꾸는 법은 **`-D warnings`** 또는 `#![deny(unreachable_code)]` 다.

---

## 실행 검증

| 실험 (`ex.rs`) | 무엇을 확인했나 | 결과 |
|---|---|---|
| `add`/`greet`/`unit_explicit`/`early` | `add = 5` · `u = ()` 크기 0 · `early(-1) = 0` · `early(5) = 10` | 1 |
| `fn add(a, b) -> i32` | **파서 에러**(번호 없음) `expected one of :, @, or \|` | 10 |
| `fn twice(a: i32) -> i32 { a * 2; }` | **E0308** + `remove this semicolon` | 2 |
| `fn half(a: i32) -> i32 { if … }` | **E0317** + `consider adding an else block` | 2 |
| `rustc --explain E0317` | 공식 설명 인용 | 2 |
| `let x: i32 = panic!("여기서 끝");` | **컴파일 성공** · 경고 2 · 출력 `시작` · **종료 코드 101** | 3 |
| `i32`/`String`/`Vec<u8>`/`bool` 자리의 `!` | 넷 다 통과 · `a=1 b=문자열 c=[7] d=true` | 4 |
| `match` 한 갈래만 `panic!` + `let _: ()` | **E0308** `found &str` — 전체 타입이 `&str` | 5 |
| 모든 갈래가 `!`(`i32` 표기) | **컴파일 성공** · `as all arms diverge` 경고 · 패닉 101 | 5 |
| 모든 갈래가 `!`(`String` 표기) | **같은 결과** — 타입 표기를 바꿔도 통과 | 5 |
| `let p: fn(i32)->i32 = double;` · `apply(double, 5)` | `p(21) = 42` · `apply = 10` · `c(1) = 2` | 6 |
| `size_of::<fn(i32)->i32>()` · `size_of_val(&double)` | **8** · **0** | 6 |
| `let _: () = double;` | **E0308** `found fn item fn(i32) -> i32 {double}` | 6 |
| `f = triple;` | **E0308** `different fn items have unique types` | 6 |
| `fn spin() -> !` · `let p: fn() -> ! = spin;` | **둘 다 통과** — `ok` | 7 |
| `let x: !` · `Vec<!>` · `Option<!>` · `fn take(x: !)` · `type Never = !;` | **전부 E0658** `the ! type is experimental` | 7 |
| `rustc --explain E0658` | 공식 설명 인용 | 7 |
| `fn die(msg) -> !` | `n = 7` · **종료 코드 2** | 8 |
| `fn bad() -> ! { println!(…); }` | **E0308** `expected !, found ()` | 8 |
| `let c: fn(i32)->i32 = \|x\| x + k;` | **E0308** + `closures can only be coerced to fn types if they do not capture` | 9 |
| `fn inner() -> i32 { k + 1 }` | **E0434** + `use the \|\| { ... } closure form instead` | 9 |
| `rustc --explain E0434` | 공식 설명 인용(해결책 둘) | 9 |
| `fn add` 두 번 선언 | **E0428** `defined multiple times` | 10 |
| `rustc --explain E0428` | 공식 설명 인용 | 10 |
| `unreachable!`/`todo!`/`unimplemented!`/`exit` 를 한 `match` 에 | 전부 `&'static str` 로 통과 · `영 하나` | 더 들어가면 |
| `return` 뒤의 코드 · 인자 자리의 `panic!` | `unreachable statement` · **`unreachable call`** | 3 · 더 들어가면 |
| `size_of::<()>()` | **0** | 11 |

**구현·설정에 달린 항목**(다시 찍을 자리)

| 항목 | 무엇에 달렸나 |
|---|---|
| **`!` 를 타입으로 못 적는 것**(E0658) | **툴체인 채널.** stable 1.92.0 기준이다. nightly 는 `#![feature(never_type)]` 로 연다 |
| 에러·경고 **문구와 화살표 배치** | rustc 구현. **에러 번호**가 더 안정적이다 |
| `unreachable_code`·`unused_variables` 가 **경고**인 것 | 린트 설정. `-D warnings`·`#[deny]` 로 에러가 된다 |
| **fn 포인터 크기 8** | **플랫폼**(`x86_64`). 32비트에서는 4다 |
| **패닉 줄의 괄호 안 번호** | **실행마다 바뀐다.** 근거로 읽을 칸이 아니다 |
| **종료 코드 101** | 런타임이 정한다(패닉). **종료 코드 2** 는 내가 `exit(2)` 로 고른 값이다 |
| 닫힌 클로저 타입 이름(`{closure@ex.rs:3:29: 3:32}`) | rustc 구현. **줄·열이 소스에 따라 바뀐다** |
| **반환 규칙 · `!` 강제 · fn 아이템 고유성** | **전부 언어 보장.** 빌드 프로필에 흔들리지 않는다 |
