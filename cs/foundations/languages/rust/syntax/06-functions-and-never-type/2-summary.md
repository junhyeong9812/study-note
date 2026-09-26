# rust/syntax/06 — 함수·반환·발산 타입 `!` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [The Rust Reference](https://doc.rust-lang.org/reference/) 의 Functions ·
> Never type · Type coercions(`!` 강제) · Function pointer types 절 ·
> `rustc --explain E0308` / `E0317` / `E0428` / `E0434` / `E0658`.
> 이 머신의 `rust-docs`(1.92.0)를 열어 확인했다.
> **실행 검증** — 이 문서의 모든 출력·에러·경고는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 얻은 것이다. `cargo` 는 쓰지 않았다.
> ★ 패닉 메시지 **괄호 안 번호**(`(1778250)`)는 **실행마다 바뀐다.** 출력을 그대로 옮기느라 남겨 두었을 뿐,\
> 근거로 읽을 칸이 아니다.
> **버전** — 함수 문법과 `-> !` 는 1.0부터다. **`!` 를 타입으로 적는 것**(`let x: !`·`Vec<!>`)은\
> **1.92.0 stable 에서 아직 안 된다**(E0658 — 추적 이슈 #35121). 이 문서는 **stable 에서 되는 것만** 적는다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**함수는 「값을 하나 들고 나오는 방」이고, `!` 는 「나오지 않는 방」이다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 방 | **함수 몸통** |
| 물건을 하나 들고 나온다 | 값을 **반환**한다 |
| 빈손으로 나온다 | 반환 타입이 **`()`**(유닛) |
| **나오지 않는다** | 반환 타입이 **`!`**(발산) |
| 나오지 않는 사람에게 「무슨 물건 들고 나올 거냐」고 묻는 게 무의미하다 | `!` 가 **어떤 타입으로도 강제**된다 |
| 문 앞에서 물건을 내려놓게 하는 규칙 | **세미콜론** |
| 방을 가리키는 번호표 | **함수 포인터** `fn(i32) -> i32` |
| 방마다 하나씩 붙은 고유 문패 | **fn 아이템 타입** `fn(i32) -> i32 {double}` |

- `fn twice(a: i32) -> i32 { a * 2 }` 는 **값을 들고 나온다.**
- `fn greet(name: &str) { ... }` 는 **빈손으로 나온다** — 반환 타입이 `()` 다.
- `fn die(msg: &str) -> ! { ... }` 는 **나오지 않는다** — 그래서 그 자리에 어떤 타입이 와도 맞는다.

```text
   fn twice(a) -> i32          fn greet(n)              fn die(m) -> !
   +-----------------+         +-----------------+      +-----------------+
   |   a * 2         |         |   println!(..)  |      |  process::exit  |
   +--------|--------+         +--------|--------+      +-----------------+
            v                           v                    (문이 없다)
        i32 를 들고                  빈손 = ()              아무것도 안 나온다
          나온다                                                 = !
```

**언어도 똑같은 구조다.** 실측 출력이 이 그림 그대로다.

```text
add = 5
안녕 러스트
u = () / 크기 = 0
early(-1) = 0 / early(5) = 10
```

> **발산(diverging)** — 함수가 정상적으로 돌아오지 않는 것. 패닉하거나, 프로세스를 끝내거나, 영영 돈다.\
> 예: `panic!()` · `std::process::exit(2)` · `loop {}`.

> **발산 타입 `!`** — 「값이 절대 만들어지지 않는다」는 타입. never type 이라고 부른다.\
> 예: `fn die(msg: &str) -> !` 의 반환 타입. 값이 없으므로 **어떤 타입 자리에도 들어간다**.

> **함수 포인터(`fn` 포인터)** — 함수 하나를 가리키는 값. 타입이 `fn(i32) -> i32` 처럼 시그니처로 적힌다.\
> 예: `let p: fn(i32) -> i32 = double;`. 실측 크기는 **8바이트**(이 머신 64비트).

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. 함수는 값을 **어떻게** 돌려주고, **안 돌려주면** 무엇이 되는가 — 그때 컴파일러는 무슨 번호를 다는가.
2. **`!` 는 무엇인가** — 왜 어떤 타입으로도 들어가고, **지금 stable 에서 어디까지 쓸 수 있는가**.
3. **`fn` 이 값이라는 말은 무슨 뜻인가** — 클로저와 무엇이 다른가.

## 동작 방식

### (1) 함수 선언과 반환 — 기본은 꼬리 표현식

**언제 쓰나** — 함수를 쓸 때마다.

```rust
fn add(a: i32, b: i32) -> i32 { a + b }             // 꼬리 표현식
fn greet(name: &str) { println!("안녕 {name}"); }    // -> () 생략
fn unit_explicit() -> () {}                          // 같은 뜻을 적어 둔 것
fn early(a: i32) -> i32 {
    if a < 0 { return 0; }                           // 조기 반환
    a * 2
}
```

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
add = 5
안녕 러스트
u = () / 크기 = 0
early(-1) = 0 / early(5) = 10
```

```text
   fn 이름(인자: 타입, ...) -> 반환타입 { 몸통 }
      |        |               |          |
      |        |               |          +-- 마지막 식(세미콜론 없음) = 반환값
      |        |               +-- 생략하면 () 다. -> () 를 적는 것과 같은 뜻
      |        +-- 인자는 타입을 반드시 적는다 (추론 안 한다)
      +-- 같은 이름을 두 번 못 쓴다 (오버로딩 없음)
```

그림 해설 (한 단계씩):

- **인자 타입은 의무**다. 생략하면 파서가 먼저 막는다(「문법 — 형태와 규칙」).
- **반환 타입 생략 = `-> ()`** 다. `unit_explicit()` 의 값이 `()` 이고 크기가 **0**인 것이 그 증거다.
- 관용은 **꼬리 표현식**이고 `return` 은 **중간에서 빠져나갈 때** 쓴다.\
  둘의 정본은 [**04번 주제**](../04-expressions-and-semicolons/)다 — 여기서는 결론만 쓴다.

비용 — 없음. 반환 규칙은 컴파일 타임에 끝난다.

### (2) ★ 반환이 사라지는 두 자리 — 에러 번호가 갈린다

**언제 쓰나** — 함수를 고치다가 마지막 줄을 건드릴 때마다.

둘 다 「몸통이 `()` 를 낸다」인데 **컴파일러가 다는 번호가 다르다.**

세미콜론 하나를 붙인 경우.

```rust
fn twice(a: i32) -> i32 {
    a * 2;
}
```

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

꼬리가 아예 없고 `else` 없는 `if` 만 있는 경우.

```rust
fn half(a: i32) -> i32 {
    if a < 0 { return 0; }
    // 꼬리 표현식이 없다
}
```

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

```text
   몸통이 () 를 낸다
          |
   +------+------------------------+
   |                               |
 마지막 식에 세미콜론              마지막이 else 없는 if
   |                               |
 E0308 mismatched types          E0317 may be missing an `else` clause
   |                               |
 "remove this semicolon"         "consider adding an `else` block"
```

그림 해설 (한 단계씩):

- **E0308** 은 「타입이 어긋났다」고만 말하고 **지울 세미콜론**을 짚는다.
- **E0317** 은 「`else` 가 빠진 것 같다」고 말한다 — 이쪽은 **없는 갈래가 `()`** 라서 생긴 것이다.
- 즉 **증상이 같아도 고칠 곳이 다르다.** 번호를 먼저 읽으면 어디를 볼지 정해진다.

`rustc --explain E0317`:

> An `if` expression without an `else` block has the type `()`, so this is a type error.
> To resolve it, add an `else` block having the same type as the `if` block.

비용 — 없음.

### (3) ★ 발산 타입 `!` — 「값을 내지 않는다」가 타입이다

**언제 쓰나** — `panic!`·`process::exit`·무한 `loop` 가 값이 필요한 자리에 놓일 때.

```rust
fn main() {
    println!("시작");
    let x: i32 = panic!("여기서 끝");
    println!("{x}");
}
```

**컴파일은 된다.** 에러가 아니라 경고 둘이다.

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

```text
   let x: i32 = panic!("...");
          |          |
        i32 를        ! 를 낸다 (= 아무 값도 안 낸다)
       기대한다          |
          |             v
          +---- ! 는 i32 로 강제된다 -> 타입 검사 통과
                        |
                        v
                실행하면 그 줄에서 패닉, 종료 코드 101
                x 에는 아무것도 안 들어간다
```

그림 해설 (한 단계씩):

- **타입 검사는 통과한다.** `!` 가 `i32` 자리로 강제되기 때문이다.
- 남는 단서는 **경고 둘**뿐이다 — `unreachable_code` 와 `unused_variables`.
- ★ **경고도 출력이다.** 이 자리는 에러가 안 나므로 경고를 안 읽으면 못 잡는다.
- 실행하면 그 줄에서 **패닉**하고 **종료 코드 101**이다.\
  패닉 줄의 괄호 안 번호는 **실행마다 바뀐다** — 근거로 읽을 칸이 아니다.

비용 — 타입 검사는 0. 실행 비용은 그 자리에서 프로세스가 끝나는 것이다.

### (4) ★ `!` 가 어떤 타입으로도 강제된다

**언제 쓰나** — 값이 필요한 자리에서 실패를 처리할 때.

네 자리에 서로 다른 타입을 기대시키고 `!` 를 넣었다. 전부 통과한다.

```rust
fn parse(s: &str) -> i32 {
    match s.parse::<i32>() {
        Ok(n) => n,                       // i32
        Err(_) => panic!("숫자가 아니다"),  // ! -> i32 로 강제된다
    }
}
fn main() {
    let flag = std::env::args().count() > 99; // 항상 거짓 — 아래 ! 갈래는 안 탄다

    let a: i32    = if flag { panic!() } else { 1 };
    let b: String = if flag { panic!() } else { String::from("문자열") };
    let c: Vec<u8>= if flag { std::process::exit(3) } else { vec![7] };
    let d: bool   = if flag { loop {} } else { true };

    println!("a={a} b={b} c={c:?} d={d}");
    println!("parse = {}", parse("42"));
}
```

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
a=1 b=문자열 c=[7] d=true
parse = 42
(종료 코드 0)
```

```text
              panic!()   process::exit(3)   loop {}
                  |             |              |
                  +------+------+--------------+
                         v
                    타입은 전부 !
                         |
         +-------+-------+--------+---------+
         v       v       v        v         v
        i32   String   Vec<u8>   bool   &'static str  ...  어떤 타입이든
```

그림 해설 (한 단계씩):

- **`!` 를 내는 것은 셋**이다 — 패닉, 프로세스 종료, 끝나지 않는 `loop`.
- 이 셋이 **어느 타입 자리에 놓여도 타입 검사가 통과한다.**
- 이유는 한 줄이다 — **값이 절대 만들어지지 않으니 타입을 어기는 일도 일어나지 않는다.**
- `if` 두 갈래의 타입이 같아야 한다는 규칙([**04번 주제**](../04-expressions-and-semicolons/))을\
  `!` 가 **다른 갈래 쪽으로 맞춰 주면서** 통과시킨다.

비용 — 없음. 코드 생성에 아무것도 안 남는다(그 갈래는 값을 안 만든다).

### (5) `match` 한 갈래가 `!` 면 전체 타입은 다른 갈래를 따른다

**언제 쓰나** — `match` 한 갈래에서만 실패 처리를 할 때.

타입을 물어보는 수법은 **일부러 틀린 타입을 주는 것**이다(정본은 [**04번 주제**](../04-expressions-and-semicolons/) 8번).

```rust
let _: () = match n {
    1 => "하나",
    _ => panic!("없음"),
};
```

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

**모든 갈래가 `!`** 면 경고가 하나 더 붙는다.

```rust
let both_never: i32 = match n {
    1 => panic!("a"),
    _ => std::process::exit(1),
};
println!("{both_never}");
```

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
```

```text
   match n {                       match n {
       1 => "하나"     -> &str          1 => panic!()   -> !
       _ => panic!()   -> !             _ => exit(1)    -> !
   }                               }
        |                               |
        v                               v
   전체 타입 = &str                전체 타입 = 아무거나
   (! 가 &str 쪽으로 맞춘다)       "as all arms diverge" 경고
```

그림 해설 (한 단계씩):

- `!` 갈래는 **타입을 주장하지 않는다.** 그래서 남은 갈래가 전체 타입을 정한다.
- 갈래가 **전부 `!`** 면 정할 것이 없어 어떤 타입으로도 받아진다 — 대신 **그 뒤가 도달 불가**다.
- 메시지가 그 사실을 문장으로 말해 준다 — `as all arms diverge`.

비용 — 없음.

### (6) `-> !` 를 직접 쓰기

**언제 쓰나** — 절대 돌아오지 않는 함수를 만들 때(치명적 오류 처리·이벤트 루프).

```rust
fn die(msg: &str) -> ! {
    eprintln!("치명적: {msg}");
    std::process::exit(2);
}
fn spin() -> ! { loop {} }
fn main() {
    let n: i32 = if std::env::args().count() > 99 { die("인자") } else { 7 };
    println!("n = {n}");
    let _ = spin;      // 호출은 안 한다
    die("정상 종료 경로 아님");
}
```

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
n = 7
치명적: 정상 종료 경로 아님
(종료 코드 2)
```

몸통이 **정상적으로 끝나 버리면** 거부된다.

```rust
fn bad() -> ! {
    println!("여기서 끝나 버린다");
}
```

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

그림 해설 (한 단계씩):

- `-> !` 는 **약속**이다 — 「이 함수는 안 돌아온다」.
- 약속을 어기면 **(2)번과 같은 문장**으로 잡힌다 — `implicitly returns () as its body has no tail or return expression`.
- 그래서 `-> !` 함수의 마지막은 늘 **패닉·종료·무한 루프**여야 한다.

비용 — 없음. 호출 쪽에서 반환값을 받을 코드를 아예 만들지 않는다.

### (7) ★ `fn` 이 값이다 — 포인터와 아이템

**언제 쓰나** — 함수를 인자로 넘기거나 표에 담을 때.

```rust
fn double(x: i32) -> i32 { x * 2 }
fn apply(f: fn(i32) -> i32, v: i32) -> i32 { f(v) }
fn main() {
    let p: fn(i32) -> i32 = double;        // 함수가 값이 된다
    println!("p(21) = {}", p(21));
    println!("apply = {}", apply(double, 5));

    // 환경을 안 잡는 클로저는 fn 포인터가 된다
    let c: fn(i32) -> i32 = |x| x + 1;
    println!("c(1) = {}", c(1));

    // 크기
    println!("fn 포인터 크기 = {}", std::mem::size_of::<fn(i32) -> i32>());
    println!("fn 아이템 크기 = {}", std::mem::size_of_val(&double));
}
```

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
p(21) = 42
apply = 10
c(1) = 2
fn 포인터 크기 = 8
fn 아이템 크기 = 0
(종료 코드 0)
```

**함수 이름의 진짜 타입**은 포인터가 아니다. 물어보면 이렇게 답한다.

```rust
let _: () = double;                 // fn 아이템의 진짜 타입을 물어본다
let mut f = double;
f = triple;                         // 다른 함수를 넣어 보면?
```

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

```text
   double 이라는 이름
        |
        v
   fn 아이템 타입  fn(i32) -> i32 {double}    <- 함수마다 고유. 크기 0바이트
        |
        | 타입을 fn(i32) -> i32 로 적으면 강제된다
        v
   fn 포인터 타입  fn(i32) -> i32             <- 여러 함수가 같은 타입. 크기 8바이트
        ^
        | 환경을 안 잡는 클로저도 여기로 온다
        |
   |x| x + 1
```

그림 해설 (한 단계씩):

- 함수 이름 하나하나가 **자기만의 타입**을 갖는다 — `fn(i32) -> i32 {double}`.\
  그래서 `f = triple;` 이 거부된다(`different fn items have unique types`).
- 그 타입은 **크기가 0**이다 — 어느 함수인지가 타입에 이미 적혀 있어 실행 시에 담을 것이 없다.
- **`fn(i32) -> i32` 라고 적으면** 공통 포인터 타입으로 강제되고, 그때 **8바이트**가 생긴다.
- **환경을 안 잡는 클로저**도 이 포인터로 온다. 잡으면 안 된다(다음 절).
- 클로저 세 트레이트의 정본은 [목록의 **34번 주제**](../34-closures-fn-fnmut-fnonce-and-move/), 클로저 반환은 [목록의 **35번 주제**](../35-function-pointers-and-returning-closures/)다.

비용 — fn 아이템은 0바이트(정적 디스패치). fn 포인터는 8바이트 + **간접 호출**이다.

## 문법 — 형태와 규칙

### 형태

```rust
fn 이름(인자: 타입, ...) -> 반환타입 { 몸통 }

fn add(a: i32, b: i32) -> i32 { a + b }   // 꼬리 표현식이 반환값
fn greet(n: &str) { }                     // -> () 생략
fn die(m: &str) -> ! { panic!("{m}") }    // 절대 안 돌아온다
let p: fn(i32) -> i32 = add2;             // 함수 포인터 타입
```

- 인자 타입은 **의무**다. 반환 타입만 생략할 수 있고, 생략하면 `()` 다.
- 몸통의 마지막 식(세미콜론 없음)이 반환값이다 — 정본은 [**04번 주제**](../04-expressions-and-semicolons/).
- 기본값 인자·가변 인자·오버로딩은 **없다.**

### `!` 를 타입으로 적을 수 있는 자리 — 실측 지도

**stable 1.92.0 · 에디션 2021 에서 전수로 던져 본 결과**다.

| 자리 | 예 | 결과 |
|---|---|---|
| 함수의 반환 위치 | `fn die() -> !` | **된다** |
| 함수 포인터 타입의 반환 위치 | `let p: fn() -> ! = spin;` | **된다** |
| 지역 변수 타입 표기 | `let x: ! = panic!();` | **E0658** |
| 제네릭 인자 | `Vec<!>` · `Option<!>` | **E0658** |
| 함수 인자 타입 | `fn take(x: !)` | **E0658** |
| 타입 별칭 | `type Never = !;` | **E0658** |

★ **즉 `!` 는 「반환 위치에만 적을 수 있는 타입」이다.** 나머지는 전부 같은 한 줄로 거부된다.

```text
error[E0658]: the `!` type is experimental
 --> ex.rs:2:12
  |
2 |     let x: ! = panic!("이 타입 표기가 되나");
  |            ^
  |
  = note: see issue #35121 <https://github.com/rust-lang/rust/issues/35121> for more information
```

`rustc --explain E0658`:

> An unstable feature was used.
>
> (… 예제 생략 …)
>
> If you're using a stable or a beta version of rustc, you won't be able to use
> any unstable features. In order to do so, please switch to a nightly version of
> rustc (by using [rustup]).

### 금지 사례 — 던져서 확인한 것들

인자 타입을 생략하면 **파서**가 먼저 막는다(에러 번호가 없다).

```text
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
```

같은 이름의 함수를 두 번 쓰면 **오버로딩이 아니라 중복 정의**다.

```text
error[E0428]: the name `add` is defined multiple times
 --> ex.rs:2:1
  |
1 | fn add(a: i32, b: i32) -> i32 { a + b }
  | ----------------------------- previous definition of the value `add` here
2 | fn add(a: f64, b: f64) -> f64 { a + b }      // 같은 이름, 다른 시그니처
  | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ `add` redefined here
  |
  = note: `add` must be defined only once in the value namespace of this module
```

함수 안에 함수를 써도 **바깥 변수를 못 본다** — 그게 클로저와 갈리는 자리다.

```text
error[E0434]: can't capture dynamic environment in a fn item
 --> ex.rs:3:25
  |
3 |     fn inner() -> i32 { k + 1 }          // 함수 안의 함수가 바깥 변수를 보나?
  |                         ^
  |
  = help: use the `|| { ... }` closure form instead
```

`rustc --explain E0434`:

> A variable used inside an inner function comes from a dynamic environment.
>
> (… 예제 생략 …)
>
> Inner functions do not have access to their containing environment. To fix this
> error, you can replace the function with a closure:

★ `--explain` 은 **길을 하나 더** 알려 준다 — 「Or replace the captured variable with a constant or a static item」.
잡을 것이 상수라면 클로저 대신 `const`/`static` 으로 올리면 된다([**07번 주제**](../07-const-static-and-const-fn/)).

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다. 일곱 중 여섯은 컴파일러가 **에러로 막아 주지만**,
**4번 하나만은 경고로만** 드러난다 — 그래서 그것이 제일 위험하다.

### 1. ★ 마지막 줄에 세미콜론을 붙인다

```text
fn twice(a: i32) -> i32 { a * 2; }
  ->  error[E0308] expected `i32`, found `()`
      implicitly returns `()` as its body has no tail or `return` expression
      help: remove this semicolon to return this value
```

- 다른 언어에서 오면 **거의 반드시 한 번은 밟는다.** 정본은 [**04번 주제**](../04-expressions-and-semicolons/).

### 2. 같은 증상인데 번호가 다르다 — E0308 대 E0317

```text
fn twice(a: i32) -> i32 { a * 2; }            ->  E0308 (세미콜론을 지워라)
fn half(a: i32) -> i32 { if a < 0 { return 0; } }  ->  E0317 (else 를 달아라)
```

- **번호를 먼저 읽어라.** 「타입이 안 맞는다」만 보고 세미콜론을 찾으면 두 번째는 못 고친다.

### 3. ★ `!` 를 타입으로 적으려 한다

```text
let x: ! = panic!();   ->  error[E0658]: the `!` type is experimental
Vec<!> · Option<!> · fn take(x: !) · type Never = !;   ->  전부 E0658
```

- **`-> !` 만 stable 이다.** 「`!` 를 배웠으니 어디든 쓰겠지」가 틀린다.
- nightly 예제를 그대로 옮기면 여기서 막힌다. **툴체인 채널에 달린 문제**다.

### 4. ★ `!` 가 들어간 자리의 경고를 안 읽는다

`!` 뒤의 코드는 **도달하지 않는데 컴파일은 통과한다.** 단서가 경고뿐이다.

같은 린트 하나가 **제목 줄을 둘로 나눠 쓴다.** 문장이 통째로 못 가면 앞엣것, 호출 하나가 못 가면 뒤엣것이다.

```text
warning: unreachable statement
warning: unreachable call
```

★ **`any code following this expression is unreachable` 은 `= note:` 가 아니라 화살표 줄에 붙는 라벨**이다
(바로 아래 전문에서 `^^^^^^^^ -----…` 뒤에 붙어 있다). 린트 이름을 말하는 `= note:` 는 따로 있다.

```text
  = note: `#[warn(unreachable_code)]` (part of `#[warn(unused)]`) on by default
```

```text
warning: unreachable call
 --> ex.rs:9:24
  |
9 |         println!("{}", need_i32(panic!("인자 자리의 ! 도 강제된다")));
  |                        ^^^^^^^^ ----------------------------------- any code following this expression is unreachable
  |                        |
  |                        unreachable call
```

- 「죽은 코드가 왜 안 지워지지」가 아니라 「**거기서 이미 끝난다**」는 신호다.
- 막는 법 — `-D warnings` 로 경고를 에러로 올린다.

### 5. 환경을 잡는 클로저를 `fn` 포인터에 넣는다

```text
let k = 10;
let c: fn(i32) -> i32 = |x| x + k;

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
```

- **`k` 를 하나 잡는 순간** 포인터가 될 수 없다 — 잡은 값을 담을 자리가 포인터에 없기 때문이다.
- 고치는 길은 `impl Fn` 이나 `Box<dyn Fn>` 이다([목록의 **34번 주제**](../34-closures-fn-fnmut-fnonce-and-move/) · **35번 주제**).

### 6. 함수 이름 둘을 한 변수에 넣는다

```text
let mut f = double;
f = triple;
  ->  error[E0308] expected fn item, found a different fn item
      = note: different fn items have unique types, even if their signatures are the same
      = help: consider casting both fn items to fn pointers using `as fn(i32) -> i32`
```

- 고치는 법은 메시지에 있다 — **타입을 `fn(i32) -> i32` 로 적거나 `as` 로 캐스팅**한다.

### 7. 함수 안의 함수가 바깥 변수를 볼 거라 생각한다

```text
fn inner() -> i32 { k + 1 }   ->  error[E0434]: can't capture dynamic environment in a fn item
                                  = help: use the `|| { ... }` closure form instead
```

- `fn` 아이템은 **아무것도 안 잡는다.** 잡아야 하면 클로저다.

## 구현 세부사항 대 언어 보장

이 갈래에서 「구현 세부사항」은 **진단 메시지의 모양·린트 설정·툴체인 채널**이다.

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| 반환 타입을 생략하면 `()` | **언어** | Reference(Functions) · 실측(`u = ()` 크기 0) |
| 마지막 식이 반환값이다 | **언어** | Reference · 실측 |
| 인자 타입 생략 불가 · 오버로딩 없음 | **언어** | 파서 에러 · E0428 |
| `fn` 아이템이 바깥 변수를 못 잡는다 | **언어** | E0434 |
| `!` 가 어떤 타입으로도 강제된다 | **언어** | Reference(Type coercions) · 실측 4종 |
| `-> !` 함수가 정상 반환하면 거부된다 | **언어** | E0308 `expected !, found ()` |
| fn 아이템이 함수마다 고유 타입이다 | **언어** | E0308 `different fn items have unique types` |
| **fn 아이템의 크기가 0** | **언어** | zero-sized type. 실측 `size_of_val(&double) == 0` |
| **fn 포인터의 크기가 8** | **플랫폼** | `x86_64` 의 포인터 폭. 32비트에서는 4다 |
| **`!` 를 타입으로 못 적는 것** | **툴체인 채널** | E0658 — stable 1.92.0 기준. nightly 는 `#![feature(never_type)]` 로 연다 |
| **에러·경고 메시지의 문구와 화살표 배치** | **rustc 구현** | 버전이 오르면 바뀐다. **에러 번호**가 더 안정적이다 |
| **`unreachable_code` 가 경고인 것** | **린트 설정** | `-D warnings`·`#[deny]` 로 에러가 된다 |
| **패닉 줄의 괄호 안 번호** | **실행마다** | 근거로 읽을 칸이 아니다 |
| **종료 코드 101 · 2** | 101은 **런타임**, 2는 **이 프로그램** | 패닉은 101 고정, `exit(2)` 는 내가 고른 값 |

★ 이 주제에서 **디버그·릴리스로 갈리는 자리는 없다.** 전부 컴파일 타임 타입 규칙이다 —
[**03번 주제**](../03-primitive-types-and-integer-overflow/)와 다른 점이다.
대신 **툴체인 채널로 갈리는 자리**가 하나 있다(`!` 타입 표기).

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 이유 |
|---|---|---|
| 값을 하나 돌려준다 | 꼬리 표현식 | 관용이다. `return` 은 `clippy` 가 잡는다 |
| 중간에서 빠져나간다 | `return` | 그게 `return` 의 자리다 |
| 반환값이 없다 | 반환 타입을 안 적는다 | `-> ()` 를 명시할 필요가 없다 |
| 절대 안 돌아오는 함수 | `-> !` | 호출자가 그 뒤를 안 쓰게 타입으로 못 박는다 |
| 복구 불가능한 상태 | `panic!` · `process::exit` | 값이 필요한 자리에도 그냥 들어간다 |
| 아직 안 쓴 갈래 | `todo!()` · `unimplemented!()` | 둘 다 `!` 라 타입이 맞는다 |
| 논리상 못 오는 갈래 | `unreachable!()` | 「여기 오면 버그」를 코드로 적는 것 |
| 함수를 인자로 넘긴다 | `fn(i32) -> i32` | 환경을 안 잡으면 이쪽이 싸다(8바이트) |
| 환경을 잡아야 한다 | 클로저 | `fn` 포인터로는 안 된다([목록의 **34번 주제**](../34-closures-fn-fnmut-fnonce-and-move/)) |

판단 규칙 두 줄.

- **「안 돌아온다」를 주석이 아니라 타입으로 적어라** — `-> !` 가 그 자리다.
- **`!` 를 타입 표기로 쓰고 싶어지면 멈춰라** — stable 에서는 반환 위치뿐이다.

## 핵심 문장

- 함수의 반환값은 **꼬리 표현식**이고, 반환 타입을 생략하면 **`()`** 다.
- 몸통이 `()` 를 내는 사고는 두 가지인데 **번호가 갈린다** — 세미콜론은 **E0308**, 꼬리 없는 `if` 는 **E0317**.
- **`!` 는 「값이 절대 안 만들어진다」는 타입**이고, 그래서 **어떤 타입 자리에도 들어간다**.
- `!` 를 내는 것은 셋이다 — **`panic!`·`process::exit`·끝나지 않는 `loop`**(그리고 `todo!`·`unreachable!`).
- `match` 한 갈래가 `!` 면 **전체 타입은 다른 갈래가 정한다**. 전부 `!` 면 `as all arms diverge` 경고가 붙는다.
- ★ **stable 1.92.0 에서 `!` 를 적을 수 있는 곳은 반환 위치뿐**이다. 나머지는 **E0658**.
- **`fn` 은 값이다** — 함수마다 **고유한 0바이트 아이템 타입**이 있고, `fn(i32) -> i32` 로 적으면 **8바이트 포인터**가 된다.
- **환경을 잡는 클로저는 `fn` 포인터가 될 수 없다.** 잡지 않으면 된다.

## 관련 자료

- [`../README.md`](../README.md) — Rust 문법·API 주제 목록(이 주제는 06번)
- [**04번 주제**](../04-expressions-and-semicolons/)(표현식 지향) — **꼬리 표현식·`return`·`()` 의 정본**.\
  그쪽은 「세미콜론이 블록에 무엇을 하나」까지, 여기는 「**그게 함수 경계에서 무엇이 되나**」부터다
- [**05번 주제**](../05-control-flow-loops-and-labels/)(제어 흐름) — 끝나지 않는 `loop` 가 `!` 라는 사실의 출처
- [**03번 주제**](../03-primitive-types-and-integer-overflow/)(기본 타입) — 디버그·릴리스로 갈리는 주제의 대비
- [**07번 주제**](../07-const-static-and-const-fn/)(상수·`static`·`const fn`) — `const fn` 이라는 다른 종류의 함수
- [**08번 주제**](../08-ownership-and-move/)(소유권과 이동) — 함수 인자·반환이 **값을 이동시킨다**는 쪽
- [`../../언어-특성/README.md`](../../언어-특성/README.md) — 그쪽은 「**왜 Rust 를 고르나**」,\
  여기는 「**이 문법이 실제로 무엇을 하나**」다. 제로 코스트 논증은 그쪽 §6 이고,\
  여기서 실측한 것은 **fn 아이템이 0바이트라는 사실 하나**다
- [목록의 **18번 주제**](../18-match-and-exhaustiveness/)(`match` 와 완전성 검사) · **19번 주제**(패턴 문법) — `match` 의 정본
- [목록의 **23번 주제**](../23-panic-vs-result/)(`panic!` 대 `Result`) — **어디서 끝낼 것인가**의 정본. 여기는 `panic!` 의 **타입**만 다룬다
- [목록의 **34번 주제**](../34-closures-fn-fnmut-fnonce-and-move/)(클로저 `Fn`/`FnMut`/`FnOnce`) · **35번 주제**(함수 포인터와 클로저 반환) — 클로저의 정본
- [목록의 **31번 주제**](../31-generics-trait-bounds-where-and-monomorphization/)(제네릭·단형화) — fn 아이템이 0바이트인 것과 정적 디스패치의 관계

## 용어 풀이

- **함수 아이템(fn item)** — `fn` 으로 선언한 함수 그 자체. 함수마다 **고유한 타입**을 가지며 크기는 0바이트다.
- **함수 포인터(fn pointer)** — `fn(i32) -> i32` 타입의 값. 여러 함수가 같은 타입을 공유하고 크기는 8바이트다.
- **꼬리 표현식(tail expression)** — 몸통의 마지막에 세미콜론 없이 놓인 식. 그 함수의 반환값이 된다.
- **유닛 타입 `()`** — 값이 하나뿐인 타입. 「의미 있는 값이 없다」를 나타낸다. 크기 0바이트.
- **발산 타입 `!`** — 값이 절대 만들어지지 않는 것의 타입. never type.
- **강제(coercion)** — 타입 A 의 값이 타입 B 가 필요한 자리에서 자동으로 B 로 쓰이는 것. `!` 는 모든 타입으로 강제된다.
- **패닉(panic)** — 복구 불가능한 오류로 판단해 스레드를 중단시키는 것. 프로세스 종료 코드는 101이다.
- **`unreachable_code`** — `!` 뒤처럼 도달할 수 없는 줄에 붙는 기본 경고.
- **E0658** — 안정판에서 불안정 기능을 썼을 때의 에러. `!` 타입 표기가 여기 걸린다.
- **툴체인 채널(channel)** — stable · beta · nightly. 어떤 기능이 되는지가 여기서 갈린다.

---

## 더 들어가면

- `!` 를 내는 매크로가 넷 더 있다 — `unreachable!()` · `todo!()` · `unimplemented!()` 와 `panic!()`.\
  `match` 갈래에 섞어도 전체 타입은 나머지 갈래를 따른다(실측 — 다섯 갈래를 섞어 `&'static str` 로 통과).

```text
fn pick(n: i32) -> &'static str {
    match n {
        0 => "영",
        1 => "하나",
        2 => unreachable!("여기는 안 온다"),
        3 => todo!(),
        4 => unimplemented!(),
        _ => std::process::exit(9),
    }
}

영 하나
() 의 크기 = 0
```

- `fn() -> !` 는 **타입 표기 자리인데도 통과한다**(실측). E0658 이 막는 것은 「**독립된 타입으로서의 `!`**」이지\
  **반환 위치**가 아니기 때문이다. 그래서 지도표의 첫 두 줄만 stable 이다.

```text
fn spin() -> ! { loop {} }
let p: fn() -> ! = spin;      // 통과한다
ok
```

- `!` 와 `()` 는 **정반대**다. `()` 는 「값이 하나뿐」이라 크기가 0이고, `!` 는 **「값이 하나도 없다」**.\
  그래서 `()` 는 변수에 담기지만 `!` 는 담을 값 자체가 생기지 않는다. `()` 의 정본은 [**04번 주제**](../04-expressions-and-semicolons/)다.
- 꼬리에 `return` 을 써도 `rustc` 는 침묵하고 `clippy` 가 `needless_return` 으로 잡는다\
  (실측은 [**04번 주제**](../04-expressions-and-semicolons/) 10번에 있다).
- `apply(double, 5)` 처럼 **fn 아이템을 fn 포인터 인자에 넘기면** 그 자리에서 포인터로 강제된다(실측 `apply = 10`).\
  제네릭 `F: Fn(i32) -> i32` 로 받으면 강제 없이 아이템 타입 그대로 단형화된다 — [목록의 **31번 주제**](../31-generics-trait-bounds-where-and-monomorphization/).
