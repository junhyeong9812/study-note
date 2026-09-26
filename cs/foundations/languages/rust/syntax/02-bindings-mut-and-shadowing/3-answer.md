# rust/syntax/02 — 변수 바인딩·`mut`·섀도잉·타입 추론 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러·경고는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)`** 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 얻은 것이다. `cargo` 는 쓰지 않았다.\
> 소스 파일 이름은 전부 `ex.rs` 로 고정했다 — 에러 메시지의 `--> ex.rs:N:C` 가 그래서 같은 이름이다.\
> 줄 번호는 **그 실험 파일 기준**이라 질문 파일의 발췌와 어긋날 수 있다(발췌는 `fn main` 을 생략했다).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 이 네 줄은 컴파일되는가

**출력**

```text
error[E0384]: cannot assign twice to immutable variable `x`
 --> ex.rs:4:5
  |
2 |     let x = 5;
  |         - first assignment to `x`
3 |     println!("x = {x}");
4 |     x = 6;
  |     ^^^^^ cannot assign twice to immutable variable
  |
help: consider making this binding mutable
  |
2 |     let mut x = 5;
  |         +++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0384`.
```

**왜 그런가**

- **컴파일되지 않는다.** 에러 번호는 **E0384**다.
- 핵심 낱말은 「**twice**」다. 금지된 것은 대입 자체가 아니라 **두 번째** 대입이다.\
  이 한 낱말이 2번 질문의 답을 이미 품고 있다.
- `help:` 는 `let mut x = 5;` 로 고치라고 하고, `+++` 는 **끼워 넣을 세 글자**(`mut` )를 가리킨다.

`rustc --explain E0384` 의 해법은 둘이다(원문).

> By default, variables in Rust are immutable. To fix this error, add the keyword
> `mut` after the keyword `let` when declaring the variable.
>
> Alternatively, you might consider initializing a new variable: either with a new
> bound name or (by [shadowing]) with the bound name of your existing variable.

- 두 번째 길이 **섀도잉**(`let x = 6;`)이다. 공식 설명이 직접 이름을 댄다.
- 둘은 뜻이 다르다 — `mut` 는 **같은 바인딩의 값**을 바꾸고, 섀도잉은 **새 바인딩**을 만든다(3·4번).

> **E0384** — 불변 바인딩에 두 번째 대입을 했을 때의 에러 번호.\
> 예: `let x = 5; x = 6;` 이 정확히 이 에러다.

### 2. `mut` 가 없는데 대입이 있다

**출력**

```text
x = 5
label = 큼
```

**왜 그런가**

- **컴파일되고 실행된다.** `mut` 가 없는데도 통과한다.
- 「불변」은 **「대입 금지」가 아니라 「한 번만 대입」으로 읽어야** 한다.\
  1번의 「cannot assign **twice**」가 그 뜻이다.

```text
let x: i32;         선언만 — 아직 값 없음 (읽으면 E0381)
      |
      v
x = 5;              첫 대입 — 여기서 값이 생긴다 (허용)
      |
      v
x = 6;              둘째 대입 — E0384
```

- 갈래마다 한 번씩 대입하는 것도 된다 — `if`/`else` 각 갈래에서 `label` 에 한 번씩 넣었다.\
  컴파일러가 **모든 경로에서 정확히 한 번**인지를 흐름 분석으로 본다.

`x = 6;` 을 더하면 — 에러 하나와 **경고 하나**가 같이 나온다.

```text
error[E0384]: cannot assign twice to immutable variable `x`
 --> ex.rs:4:5
  |
3 |     x = 5;
  |     ----- first assignment to `x`
4 |     x = 6;
  |     ^^^^^ cannot assign twice to immutable variable
  |
help: consider making this binding mutable
  |
2 |     let mut x: i32;
  |         +++

warning: value assigned to `x` is never read
 --> ex.rs:3:5
  |
3 |     x = 5;
  |     ^^^^^
  |
  = help: maybe it is overwritten before being read?
  = note: `#[warn(unused_assignments)]` (part of `#[warn(unused)]`) on by default
```

- 경고 이름은 **`unused_assignments`** 다. 「첫 대입이 읽히기 전에 덮였다」를 알려 준다.

`x = 5;` 를 지우면 다른 에러다.

```text
error[E0381]: used binding `x` is possibly-uninitialized
 --> ex.rs:3:16
  |
2 |     let x: i32;
  |         - binding declared here but left uninitialized
3 |     println!("{x}");
  |                ^ `x` used here but it is possibly-uninitialized
```

- **E0381**(초기화 전 사용)과 **E0384**(두 번째 대입)가 규칙의 양쪽 끝을 지킨다.
- `rustc --explain E0381` 첫 줄: "It is not allowed to use or capture an uninitialized variable."

### 3. 이 다섯 줄의 출력을 예측하라

**출력**

```text
1) x = 5 / 크기 4
2) x = "다섯" / 크기 16
3) x = 6 / 크기 8
```

**왜 그런가**

- 값은 `5` → `"다섯"` → `6`, 크기는 **4 → 16 → 8** 이다.

```text
let x = 5;            [상자 A: i32   5]        크기 4
                            ^ x

let x = "다섯";        [상자 B: &str "다섯"]    크기 16   <- x 가 여기를 가리킨다
                      [상자 A: i32   5]                 <- 가려짐

let x = x.len();      [상자 C: usize 6]        크기 8    <- x 는 여기
                      [상자 B: &str "다섯"]              <- 가려짐
                      [상자 A: i32   5]                 <- 가려짐
```

- **크기가 바뀌었다는 것이 「상자가 여러 개」라는 증거다.** 하나를 고쳤다면 크기가 변할 수 없다.\
  `i32` 4바이트 → `&str` 16바이트(포인터+길이의 팻 포인터) → `usize` 8바이트.
- 3번 줄이 **6**인 이유 — `x.len()` 은 `&str` 의 **UTF-8 바이트 수**다.\
  「다섯」은 한글 두 글자이고 한 글자가 3바이트라 6이다(글자 수를 원하면 `chars().count()`, 정본은 [목록의 **15번 주제**](../15-slices-ranges-and-utf8-boundaries/)).
- `let mut x = 5;` 로는 2번 줄에서 막힌다 — 타입이 굳어 있기 때문이다(5번).

> **팻 포인터(fat pointer)** — 주소 하나에 길이 같은 정보가 더 붙은 참조. `&str`·`&[T]` 가 그렇다.\
> 예: 64비트에서 주소 8바이트 + 길이 8바이트 = 16바이트라 `size_of_val` 이 16이 나온다.

### 4. 블록 안에서 가린 것

**출력**

```text
안: 99
밖: 5
```

**왜 그런가**

- 안에서는 99, 밖에서는 **5**다. 99가 아니다.

```text
      바깥 스코프                블록 안                    블록이 끝난 뒤
  +----------------+       +----------------+       +----------------+
  | x -> 5         |       | x -> 99  (앞줄) |       | x -> 5         |
  +----------------+       | x -> 5   (가림) |       +----------------+
                           +----------------+
```

- 한 문장 답: **「바꾼 게 아니라 가린 것이고, 가림은 블록과 함께 끝난다.」**
- 진짜로 바깥 값을 바꾸려면 두 가지를 동시에 고친다.

```rust
let mut x = 5;          // (1) mut 를 붙이고
{
    x = 99;             // (2) let 을 빼고 대입한다
}
println!("밖: {x}");     // 99
```

- 스코프로 말하면 — **섀도잉은 새 바인딩을 현재 스코프에 만든다.**\
  스코프가 끝나면 그 바인딩이 사라지고, 가려져 있던 바깥 바인딩이 다시 보인다.\
  대입은 바인딩을 만들지 않으므로 스코프가 끝나도 되돌아갈 것이 없다.

### 5. `mut` 로 타입을 바꾸면

**출력**

```text
error[E0308]: mismatched types
 --> ex.rs:3:9
  |
2 |     let mut x = 5;
  |                 - expected due to this value
3 |     x = "다섯";
  |         ^^^^^^ expected integer, found `&str`

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0308`.
```

**왜 그런가**

- **컴파일되지 않는다.** 에러 번호는 **E0308**, 문구는 「expected integer, found `&str`」이다.
- 「expected due to this value」가 가리키는 곳은 **`let mut x = 5;` 의 `5`** 다.

```text
let mut x = 5;
            ^
            여기서 타입이 굳는다. 내가 한 글자도 안 적었어도 굳는다.

x = "다섯";
    ^^^^^^ 굳은 규격에 안 맞는다 -> E0308
```

- 타입을 안 적었는데 정해진 이유는 **추론**이다(8번). 초기값 `5` 가 유일한 근거였다.
- 가르는 두 줄:
  - `mut` **가 푸는 것** — 같은 바인딩에 값을 **다시 대입**해도 된다.
  - `mut` **가 못 푸는 것** — **타입**. 타입을 바꾸려면 새 바인딩(섀도잉)이어야 한다.

`rustc --explain E0308` 의 첫 줄: "Expected type did not match the received type."

### 6. 이 두 줄은 컴파일되는가

**출력**

```text
error[E0282]: type annotations needed for `Vec<_>`
 --> ex.rs:2:9
  |
2 |     let v = Vec::new();
  |         ^   ---------- type must be known at this point
  |
help: consider giving `v` an explicit type, where the type for type parameter `T` is specified
  |
2 |     let v: Vec<T> = Vec::new();
  |          ++++++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0282`.
```

**왜 그런가**

- **컴파일되지 않는다.** 에러 번호는 **E0282**다.
- `println!("{:?}", v)` 가 힌트가 못 되는 이유 — **모든 `Vec<T>` 가 `Debug` 이기 때문**이다(`T: Debug` 이기만 하면).\
  「출력해 보면 알겠지」는 컴파일러 입장에서 아무 정보가 아니다. 후보가 좁혀지지 않는다.
- 고치는 세 가지는 `rustc --explain E0282` 가 그대로 들고 있다(원문).

> The type can be specified on the variable: `let x: Vec<i32> = Vec::new();`
>
> The type can also be specified in the path of the expression: `let x = Vec::<i32>::new();`
>
> Another way to provide the compiler with enough information, is to specify the
> generic type parameter: `"hello".chars().rev().collect::<Vec<char>>()`

- 즉 ① 바인딩에 표기 ② 경로에 표기(`Vec::<i32>::new()`) ③ 터보피시(`collect::<Vec<_>>()`).

**네 번째 길 — 쓰는 자리가 힌트가 된다.**

```rust
let mut v = Vec::new();
v.push(7u8);
println!("{:?}", v);
println!("원소 크기 = {}", std::mem::size_of_val(&v[0]));
```

```text
[7]
원소 크기 = 1
```

- `push(7u8)` 한 줄로 `T = u8` 이 정해졌다. 원소 크기 1이 그 증거다.
- **추론은 그 줄만 보는 게 아니라 함수 전체를 본다**(8번).

### 7. 이 프로그램이 내는 경고를 전부 대라

**출력**

```text
warning: variable does not need to be mutable
 --> ex.rs:4:9
  |
4 |     let mut never_changed = 3;
  |         ----^^^^^^^^^^^^^
  |         |
  |         help: remove this `mut`
  |
  = note: `#[warn(unused_mut)]` (part of `#[warn(unused)]`) on by default

warning: unused variable: `unused`
 --> ex.rs:2:9
  |
2 |     let unused = 1;
  |         ^^^^^^ help: if this is intentional, prefix it with an underscore: `_unused`
  |
  = note: `#[warn(unused_variables)]` (part of `#[warn(unused)]`) on by default

warning: variable `myValue` should have a snake case name
 --> ex.rs:6:9
  |
6 |     let myValue = 4;
  |         ^^^^^^^ help: convert the identifier to snake case: `my_value`
  |
  = note: `#[warn(non_snake_case)]` (part of `#[warn(nonstandard_style)]`) on by default

warning: 3 warnings emitted
```

컴파일은 끝났고, 이어서 **실행**한 결과는 따로다.

```text
never_changed = 3
myValue = 4
```

**왜 그런가**

- 경고는 **세 개**다. 린트 이름은 **`unused_mut`·`unused_variables`·`non_snake_case`** 다.\
  앞의 둘은 `unused` 묶음, 마지막은 `nonstandard_style` 묶음에 속한다 — 메시지가 그것까지 말해 준다.
- `_unused` 에 경고가 없는 이유 — **밑줄로 시작하는 이름은 「일부러 안 쓴다」는 약속**이라 `unused_variables` 가 봐 준다.\
  `unused` 쪽 경고가 제안하는 고침도 정확히 그것이다(`prefix it with an underscore`).
- **실행된다.** 마지막 두 줄이 프로그램의 출력이다. **경고는 컴파일을 막지 않는다.**

`#![deny(unused_variables)]` 를 붙이면 —

```text
warning: variable does not need to be mutable
 --> ex.rs:6:9
  |
6 |     let mut never_changed = 3;
  |         ----^^^^^^^^^^^^^
  |         |
  |         help: remove this `mut`
  |
  = note: `#[warn(unused_mut)]` (part of `#[warn(unused)]`) on by default

error: unused variable: `unused`
 --> ex.rs:4:9
  |
4 |     let unused = 1;
  |         ^^^^^^ help: if this is intentional, prefix it with an underscore: `_unused`
  |
note: the lint level is defined here
 --> ex.rs:1:9
  |
1 | #![deny(unused_variables)]
  |         ^^^^^^^^^^^^^^^^

warning: variable `myValue` should have a snake case name
 --> ex.rs:8:9
  |
8 |     let myValue = 4;
  |         ^^^^^^^ help: convert the identifier to snake case: `my_value`
  |
  = note: `#[warn(non_snake_case)]` (part of `#[warn(nonstandard_style)]`) on by default

error: aborting due to 1 previous error; 2 warnings emitted
```

(어트리뷰트 한 줄과 빈 줄이 앞에 붙어 **줄 번호가 둘씩 밀렸다.**)

- 같은 코드가 **에러**가 되어 컴파일이 멈춘다. **승격된 것은 `unused_variables` 하나뿐**이고 나머지 둘은 여전히 경고다.
- **`E0xxx` 번호가 없다.** 린트로 승격된 에러는 에러 코드를 갖지 않는다 — 그래서 `--explain` 할 것도 없다.\
  대신 `note: the lint level is defined here` 로 **누가 이걸 에러로 만들었는지**를 가리킨다.
- 같은 이유로 CI 에서는 `-D warnings` 를 쓴다. 경고를 「나중에」로 미루면 쌓인다.

### 8. 타입을 안 적으면 무엇이 되는가

**출력**

```text
n 의 타입 = i32 / f 의 타입 = f64
m 의 타입 = u64
합 = 6
```

**왜 그런가**

- `let n = 3;` 은 **`i32`**, `let f = 3.0;` 은 **`f64`** 다. 힌트가 전혀 없을 때 쓰이는 **타입 폴백**이다.
- 위 출력은 `std::any::type_name_of_val`(1.76.0부터)로 얻은 것인데, **이 함수의 문자열은 보장되지 않는다.**\
  `std::any::type_name` 문서 원문:

  > This is intended for diagnostic use. The exact contents and format of the string returned
  > are not specified ... the output may change between versions of the compiler.

- 그래서 **언어 규칙 쪽 증거를 따로 댄다.** 타입을 안 적고 `i32` 범위를 넘겨 보면 컴파일러가 이름을 말한다.

```text
$ cat ex.rs
fn main() {
    let x = 3_000_000_000;
    println!("{x}");
}

error: literal out of range for `i32`
 --> ex.rs:2:13
  |
2 |     let x = 3_000_000_000;
  |             ^^^^^^^^^^^^^
  |
  = note: the literal `3_000_000_000` does not fit into the type `i32` whose range is `-2147483648..=2147483647`
  = help: consider using the type `u32` instead
  = note: `#[deny(overflowing_literals)]` on by default
```

- **「does not fit into the type `i32`」** — 컴파일러가 직접 `i32` 라고 말했다. 이쪽이 진짜 근거다.

`let big = 3u64; let m = 3;` 에서 `m` 은 **`u64`** 다.

```text
let big = 3u64;      big : u64  (접미사로 못박힘)
let m = 3;           m   : ?
big + m              두 피연산자의 타입이 같아야 한다
      |
      v
m 은 u64 로 결정된다 — 폴백(i32)은 쓰이지 않는다
```

- **추론은 그 줄만 보지 않는다.** 함수 전체(정확히는 추론 문맥 전체)를 보고 제약을 모은 뒤 푼다.
- 제약이 하나라도 있으면 폴백이 안 쓰이고, 제약이 하나도 없을 때만 `i32`/`f64` 로 떨어진다.
- 제약이 모순되거나 답이 여럿이면 거부한다(6번의 E0282).

### 9. `const` 와 `let` 의 경계

**출력**

```text
$ cat ex.rs
const LIMIT = 100;
fn main() { println!("{LIMIT}"); }

error: missing type for `const` item
 --> ex.rs:1:12
  |
1 | const LIMIT = 100;
  |            ^ help: provide a type for the constant: `: i32`
```

```text
$ cat ex.rs
let x = 1;
fn main() { println!("{x}"); }

error: expected item, found keyword `let`
 --> ex.rs:1:1
  |
1 | let x = 1;
  | ^^^
  | |
  | `let` cannot be used for global variables
  | help: consider using `static` or `const` instead of `let`
  |
  = note: for a full list of items that can appear in modules, see <https://doc.rust-lang.org/reference/items.html>
```

**왜 그런가**

- `const LIMIT = 100;` 은 **컴파일되지 않는다.** 빠진 것은 **타입 표기**다 — `const` 는 추론이 없다.\
  (컴파일러가 `: i32` 를 제안하는 것이 8번의 폴백과 같은 값이라는 점도 눈여겨볼 만하다.)
- 함수 밖의 `let` 도 거부되고, 컴파일러가 **`static` 또는 `const`** 를 쓰라고 한다.
- 가르는 축 둘:
  - **타입 표기** — `const` 는 의무, `let` 은 추론.
  - **놓일 수 있는 자리** — `const`/`static` 은 모듈 최상위에도 놓이고, `let` 은 **함수 안**에서만.
- 더 깊이 안 다루는 이유 — 메모리 배치(`const` 는 쓰이는 자리마다 인라인, `static` 은 고정 주소)와 `const fn` 은 **다른 주제의 본문**이기 때문이다.\
  정본은 [목록의 **07번 주제**](../07-const-static-and-const-fn/)(상수·`static`·`const fn`)다. 여기서는 **`let` 과 갈리는 두 줄**까지만 둔다.

### 10. 다른 주제와 잇기

**섀도잉으로 가려진 옛 값은 언제 해제되는가**

- **가려져도 살아 있고, 스코프가 끝날 때 해제된다.** 섀도잉은 해제를 앞당기지 않는다.
- 정본은 [목록의 **09번 주제**](../09-copy-clone-and-drop/)(`Copy`·`Clone`·`Drop` 시점)다. 이 주제에서는 「가려질 뿐 사라지지 않는다」까지만 말한다.

**`let _ = f();` 와 `let _x = f();`**

`Drop` 을 찍어 실측했다.

```text
A 시작
  drop: _ 로 받음          <- 그 줄에서 바로 해제된다
A 블록 끝 직전
A 끝
B 시작
B 블록 끝 직전
  drop: _x 로 받음         <- 블록이 끝날 때 해제된다
B 끝
```

- `_` 는 **이름을 붙이지 않는 것**이라 값이 바인딩되지 않고 그 자리에서 버려진다.
- `_x` 는 **이름을 붙이는 것**이라 스코프 끝까지 산다. 경고만 안 날 뿐 보통 바인딩이다.
- 락 가드처럼 「살아 있는 동안 효력이 있는」 값에서 이 차이가 사고를 만든다(정본은 목록의 **52번 주제**).

**`rustc` 에 반드시 붙일 플래그**

- **`--edition 2021`**. 안 붙이면 `rustc` 는 **2015**로 읽는다.\
  근거와 실측은 [**01번 주제**](../01-cargo-crates-and-modules/) 8번에 있다.

**`let x = { ... };` 의 오른쪽이 값인 이유**

- 블록이 **표현식**이기 때문이다. 정본은 [**04번 주제**](../04-expressions-and-semicolons/)(표현식 지향)다.\
  거기서 **세미콜론 하나가 그 값의 타입을 `()` 로 바꾼다.**

---

## 실행 검증

| 실험 (`ex.rs`) | 무엇을 확인했나 | 결과 |
|---|---|---|
| `let x = 5; x = 6;` | **E0384** + `help: let mut x` | 1번 |
| `rustc --explain E0384` | 공식 해법 둘(`mut` · 섀도잉) | 1번 |
| `let x: i32; x = 5;` (+ `if`/`else` 대입) | **통과** — `mut` 없이 한 번 대입은 된다 | 2번 |
| 거기에 `x = 6;` 추가 | **E0384** + `unused_assignments` 경고 | 2번 |
| `let x: i32;` 뒤 바로 읽기 | **E0381** | 2번 |
| 섀도잉 3단계 + `size_of_val` | 크기 4 → 16 → 8 · `"다섯".len() == 6` | 3번 |
| 블록 섀도잉 | `안: 99` / `밖: 5` | 4번 |
| `let mut x = 5; x = "다섯";` | **E0308** `expected integer, found &str` | 5번 |
| `let v = Vec::new();` | **E0282** | 6번 |
| `rustc --explain E0282` | 고치는 세 가지(표기·경로·터보피시) | 6번 |
| `let mut v = Vec::new(); v.push(7u8);` | `[7]` · 원소 크기 1 | 6번 |
| 경고 네 줄짜리 프로그램 | 경고 **3개** · `_unused` 는 무경고 · **실행됨** | 7번 |
| `#![deny(unused_variables)]` | 같은 코드가 에러 · **에러 코드 없음** · `lint level is defined here` | 7번 |
| `#![forbid(...)]` + `#[allow(...)]` | **E0453** overruled by previous forbid | 2-summary 더 들어가면 |
| `type_name_of_val` 3종 | `i32` · `f64` · `u64` (**관찰** — 보장 아님) | 8번 |
| `let x = 3_000_000_000;` | `literal out of range for i32` (**언어 규칙 근거**) | 8번 |
| `let big = 3u64; let m = 3; big + m` | `m` 이 `u64` · 합 6 | 8번 |
| `const LIMIT = 100;` | `missing type for const item` | 9번 |
| 함수 밖 `let x = 1;` | `let cannot be used for global variables` | 9번 |
| `Drop` 으로 `let _` ↔ `let _x` | 즉시 해제 ↔ 블록 끝 해제 | 10번 |
| `let mut x = 5; x += 1; let x = x;` | 다시 불변으로 굳힘 — 통과 | 더 들어가면 |
| `"  42  "` → `trim` → `parse` 섀도잉 4단계 | `input = 42` · `i32` | 더 들어가면 |
| `collect::<Vec<_>>()` ↔ `let a: Vec<i32>` | 둘 다 `[1, 2, 3]` | 더 들어가면 |

**구현에 달린 항목**(버전이 오르면 다시 찍을 자리)

| 항목 | 무엇에 달렸나 |
|---|---|
| `type_name_of_val` 이 돌려주는 문자열(`i32`·`alloc::vec::Vec<i32>`) | **보장 없음** — std 문서가 명시. 진단용이다 |
| 경고·에러 **문구와 화살표 배치** | rustc 구현. 에러 **번호**가 더 안정적이다 |
| 어떤 린트가 기본 `warn` 인지 | rustc 기본 설정. `#[allow]`/`#[deny]`·`-D warnings` 로 뒤집힌다 |
| `size_of_val(&"...")` 이 16 | **플랫폼**(64비트). 32비트에서는 8이다 |
| `let x; x = 5;` 가 통과하는 범위 | 언어 규칙이지만 흐름 분석의 **정밀도**는 컴파일러 구현이다 |
