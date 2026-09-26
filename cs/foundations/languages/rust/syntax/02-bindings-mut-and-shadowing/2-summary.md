# rust/syntax/02 — 변수 바인딩·`mut`·섀도잉·타입 추론 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [The Rust Reference](https://doc.rust-lang.org/reference/) 의 Variables · `let` statements · Type inference 절 ·
> `rustc --explain E0384` / `E0308` / `E0282` / `E0381` 의 공식 설명. 이 머신의 `rust-docs`(1.92.0)를 열어 확인했다.
> **실행 검증** — 이 문서의 모든 출력·에러·경고는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 얻은 것이다. `cargo` 는 쓰지 않았다.\
> 컴파일러가 **거부한 코드**가 이 주제의 본문이다 — 에러 메시지를 통째로 싣는다.
> **버전** — 여기 나오는 문법은 전부 1.0부터다. 관찰용으로 쓴 `std::any::type_name_of_val` 만 **1.76.0**부터다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**`let` 은 상자를 만드는 것이 아니라 상자에 이름표를 붙여 선반 앞줄에 올리는 것이다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 상자 | 값(value) |
| 이름표 | **바인딩**(binding) — `let x = 5` 의 `x` |
| 선반의 앞줄 | 지금 그 이름으로 보이는 것 |
| 이름표를 매직으로 씀 | 기본 — 값을 바꿀 수 없다 |
| 「고쳐도 되는 상자」 도장 | `mut` — 같은 상자의 내용을 바꾼다 |
| 같은 이름표를 새 상자에 붙여 **앞줄에 겹쳐 올림** | **섀도잉**(shadowing) |
| 앞줄을 치우면 뒤의 상자가 다시 보임 | 블록이 끝나면 섀도잉이 풀린다 |

- `x = 6` 은 **상자 안의 내용을 고치는 것**이라 기본으로는 거부당한다(E0384).
- `let mut x` 는 그 상자에 「고쳐도 된다」 도장을 찍는다.\
  대신 **상자의 규격(타입)은 못 바꾼다** — 안에 5를 넣던 상자에 문자열은 안 들어간다(E0308).
- `let x = "다섯"` 은 **새 상자**다. 규격이 달라도 상관없다 — 같은 이름표를 앞줄에 겹쳐 올렸을 뿐이다.
- 블록 안에서 겹쳐 올린 것은 **블록이 끝나면 치워지고**, 뒤에 있던 상자가 다시 보인다.

```text
let x = 5;              선반:  [ x -> 5 ]

let x = "다섯";          선반:  [ x -> "다섯" ]  <- 앞줄
                                [ x -> 5 ]      <- 가려짐 (사라진 게 아니다)

{ let x = vec![1,2,3];  선반:  [ x -> [1,2,3] ] <- 블록 안에서만 앞줄
                                [ x -> "다섯" ]
                                [ x -> 5 ]
}                       블록이 끝나면 앞줄이 치워진다

println!("{x}")         선반:  [ x -> "다섯" ]  <- 다시 이게 보인다
```

**언어도 똑같은 구조다.** 실측 출력이 이 그림 그대로였다 — 블록 안에서 `[1, 2, 3]`, 블록 밖에서 다시 앞 값.

> **바인딩(binding)** — 값에 이름을 묶는 것. 「변수에 값을 넣는다」가 아니라 「**이 값을 이 이름으로 부른다**」에 가깝다.\
> 예: `let x = 5;` 는 5라는 값에 `x` 라는 이름을 묶은 것이다.

> **섀도잉(shadowing)** — 같은 이름으로 **새 바인딩**을 만들어 앞의 것을 가리는 것.\
> 예: `let x = 5; let x = "다섯";` 은 변수 하나를 고친 게 아니라 **바인딩이 둘**이다.

> **타입 추론(type inference)** — 내가 안 적은 타입을 컴파일러가 코드 전체를 보고 채우는 것.\
> 예: `let mut v = Vec::new(); v.push(7u8);` 에서 `v` 는 **다음 줄 때문에** `Vec<u8>` 이 된다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. `let x = 5;` 뒤에 `x = 6;` 을 쓰면 **컴파일러가 정확히 뭐라고 하는가** — 그리고 `mut` 말고 다른 길이 있는가.
2. **섀도잉과 `mut` 는 무엇이 다른가** — 둘 중 하나로만 할 수 있는 일은 각각 무엇인가.
3. 타입을 안 적어도 되는 이유는 무엇이고, **안 적으면 안 되는 자리**는 어디인가.

## 동작 방식

### (1) `let` 은 기본이 불변 — 거부 메시지가 정확히 무엇을 말하는가

**언제 쓰나** — 값에 이름을 붙이는 모든 자리. Rust 코드의 대부분.

```rust
let x = 5;
println!("x = {x}");
x = 6;
```

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
```

`rustc --explain E0384` 의 공식 설명은 **두 가지 해법**을 든다(원문).

> By default, variables in Rust are immutable. To fix this error, add the keyword
> `mut` after the keyword `let` when declaring the variable.
>
> Alternatively, you might consider initializing a new variable: either with a new
> bound name or (by [shadowing]) with the bound name of your existing variable.

그림 해설 (한 단계씩):

- 문구가 「cannot assign」이 아니라 「**cannot assign twice**」다.\
  즉 금지된 것은 대입 자체가 아니라 **두 번째** 대입이다((2)번으로 이어진다).
- 에러가 `help:` 로 **고칠 코드까지 보여 준다.** `+++` 는 끼워 넣을 글자다.
- 공식 설명이 `mut` 와 **섀도잉**을 나란히 놓는다 — 둘은 대안 관계다.

비용 — 없음. 컴파일 타임 검사다.

### (2) 불변은 「대입 금지」가 아니라 「한 번만 대입」이다

**언제 쓰나** — 조건에 따라 다른 값을 넣고 그 뒤로는 안 바꿀 때.

```rust
let x: i32;
x = 5;                     // mut 가 없는데도 통과한다
println!("x = {x}");

let label: &str;
if x > 3 { label = "큼"; } else { label = "작음"; }
println!("label = {label}");
```

```text
x = 5
label = 큼
```

여기서 대입을 **한 번 더** 하면 그때 E0384 다.

```text
let x: i32;
x = 5;
x = 6;
  ->  error[E0384]: cannot assign twice to immutable variable `x`
      3 |     x = 5;
        |     ----- first assignment to `x`
      + warning: value assigned to `x` is never read   (#[warn(unused_assignments)])
```

읽기 전에 쓰면 다른 에러다.

```text
let x: i32;
println!("{x}");
  ->  error[E0381]: used binding `x` is possibly-uninitialized
```

그림 해설 (한 단계씩):

- **선언과 초기화를 떼어 놓을 수 있다.** 갈래마다 정확히 한 번만 대입하면 된다.
- 그래서 「불변 = 선언 자리에서 값을 정해야 한다」는 틀린 요약이다.
- 초기화 전에 읽으면 **E0381**이고, 두 번 대입하면 **E0384**다. 두 에러가 규칙의 양쪽 끝을 지킨다.

비용 — 없음. 컴파일 타임 흐름 분석이다.

### (3) `mut` — 같은 상자의 내용만 바꾼다

**언제 쓰나** — 루프 카운터·누적값처럼 **같은 타입**으로 값이 계속 바뀔 때.

```rust
let mut x = 5;
x = "다섯";
```

```text
error[E0308]: mismatched types
 --> ex.rs:3:9
  |
2 |     let mut x = 5;
  |                 - expected due to this value
3 |     x = "다섯";
  |         ^^^^^^ expected integer, found `&str`
```

그림 해설 (한 단계씩):

- `mut` 가 푸는 것은 **「값을 바꿔도 되나」** 하나뿐이다.
- **타입은 선언 시점에 굳는다.** `5` 를 보고 정해진 정수 타입이 그 바인딩의 규격이다.
- 「expected due to this value」가 그 굳은 지점을 가리킨다 — **내가 타입을 안 적었어도 굳었다.**

비용 — 없음. `mut` 자체에 런타임 비용은 없다.

### (4) 섀도잉 — 새 바인딩이므로 타입까지 바뀐다

**언제 쓰나** — 같은 것의 **표현을 바꿔 가며** 다듬을 때(문자열 → 다듬은 문자열 → 숫자).

```rust
let x = 5;
println!("1) x = {x:?} / 크기 {}", std::mem::size_of_val(&x));
let x = "다섯";
println!("2) x = {x:?} / 크기 {}", std::mem::size_of_val(&x));
let x = x.len();
println!("3) x = {x:?} / 크기 {}", std::mem::size_of_val(&x));
{
    let x = vec![1, 2, 3];
    println!("4) 블록 안 x = {x:?}");
}
println!("5) 블록 밖 x = {x:?}");
```

```text
1) x = 5 / 크기 4
2) x = "다섯" / 크기 16
3) x = 6 / 크기 8
4) 블록 안 x = [1, 2, 3]
5) 블록 밖 x = 6
```

그림 해설 (한 단계씩):

- 크기가 **4 → 16 → 8** 로 바뀐다. 같은 상자를 고친 게 아니라 **상자가 셋**이라는 뜻이다.
- 3번 줄의 `x.len()` 은 **앞 바인딩의 값**을 읽어 새 바인딩을 만든다. 순환이 아니다.
- `"다섯".len()` 이 **6**인 것도 이 줄에서 드러난다 — `len()` 은 글자 수가 아니라 **UTF-8 바이트 수**다(정본은 [목록의 **15번 주제**](../15-slices-ranges-and-utf8-boundaries/)).
- 블록 안의 섀도잉은 **블록이 끝나면 풀린다**(4 → 5). `mut` 로는 이런 되돌림이 없다.

비용 — 없음. 새 바인딩일 뿐 할당이 더 생기지는 않는다(값 자체의 비용은 별개다).

### (5) 타입 추론 — 뒤에서 앞으로도 흐른다

**언제 쓰나** — 거의 모든 `let`. 타입을 적는 편이 오히려 드물다.

```rust
let mut v = Vec::new();      // 이 줄만 보면 Vec<무엇>인지 모른다
v.push(7u8);                 // 이 줄이 답을 준다
println!("v = {v:?} / 원소 크기 {}", std::mem::size_of_val(&v[0]));

let n = 3;                   // 아무 힌트가 없으면 정수 기본값
let f = 3.0;                 // 부동소수 기본값

let big = 3u64;
let m = 3;                   // big 과 더해지므로 u64 가 된다
println!("합 = {}", big + m);
```

```text
v = [7] / 원소 크기 1
n 의 타입 = i32 / f 의 타입 = f64
m 의 타입 = u64
합 = 6
```

```text
       let mut v = Vec::new();     <- 미지수 T
              |
              |  컴파일러는 이 함수 전체를 본다
              v
       v.push(7u8);                <- T = u8 로 결정
              |
              v
       Vec<u8> 로 굳는다
```

그림 해설 (한 단계씩):

- 추론은 **줄 단위가 아니라 함수 단위**다. 나중 줄이 앞 줄의 타입을 정한다.
- 어디서도 답이 안 나오면 **기본값**이 쓰인다 — 정수는 `i32`, 부동소수는 `f64`.
- 힌트가 하나라도 있으면 기본값이 안 쓰인다(`m` 이 `u64` 가 된 것).
- 답이 여럿이거나 없으면 거부한다 — **E0282**(「어디서 틀리나」 3번).

비용 — 컴파일 타임만. 런타임에 타입 정보를 들고 다니지 않는다.

## 문법 — 형태와 규칙

직접 쓴 최소 예제다. 묻는 것 하나만 남겼다.

### `let` 의 형태들

```rust
let x = 5;                 // 추론
let x: i64 = 5;            // 표기
let mut x = 5;             // 가변
let x;                     // 선언만 — 뒤에서 정확히 한 번 대입
let (a, b) = (1, 2);       // 구조 분해 (정본은 [목록의 **19번 주제**](../19-pattern-syntax-guards-bindings-and-match-ergonomics/))
let _ = 5;                 // 이름을 안 붙인다
let _unused = 5;           // 이름은 붙이되 경고를 끈다
```

### 네 가지를 가르는 표

| | 값을 바꿀 수 있나 | 타입을 바꿀 수 있나 | 스코프가 끝나면 |
|---|---|---|---|
| `let x` | 아니오 (두 번째 대입 불가) | 아니오 | 사라진다 |
| `let mut x` | **예** | 아니오 | 사라진다 |
| `let x` 를 다시 (섀도잉) | — (새 바인딩이다) | **예** | **앞의 바인딩이 다시 보인다** |
| `const X` | 아니오 | 아니오 | (스코프가 다르다 — 아래) |

### `const` 와의 대비 — 여기서는 경계만

정본은 [목록의 **07번 주제**](../07-const-static-and-const-fn/)(상수·`static`·`const fn`)다. 여기서는 **실측으로 갈린 두 줄**만 둔다.

```text
const LIMIT = 100;              ->  error: missing type for `const` item
                                    help: provide a type for the constant: `: i32`

let x = 1;   (함수 밖에)         ->  error: expected item, found keyword `let`
                                    | `let` cannot be used for global variables
                                    help: consider using `static` or `const` instead of `let`
```

- `const` 는 **타입 표기가 의무**다. `let` 은 추론된다.
- `let` 은 **함수 안에서만** 쓸 수 있다. 모듈 최상위에는 `const`/`static` 을 쓴다.
- 나머지(메모리 배치·`const fn`·`static` 과의 차이)는 07번이 정본이다.

### 경고를 켜고 끄는 표기

```rust
#![deny(unused_variables)]      // 크레이트 전체 — 경고를 에러로 승격
#![allow(non_snake_case)]       // 크레이트 전체 — 아예 끈다

#[allow(unused_mut)]            // 바로 아래 항목에만
fn f() { let mut x = 1; println!("{x}"); }
```

- 수준은 넷이다 — `allow` < `warn` < `deny` < `forbid`(`forbid` 는 안쪽에서 다시 `allow` 하는 것까지 막는다).
- `#![...]`(느낌표 있음)은 **그 파일/크레이트 전체**, `#[...]`(없음)은 **바로 다음 항목**이다.
- 명령줄로도 된다 — `rustc -W unused -A non_snake_case -D warnings`.

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다. 넷 중 하나는 **에러가 아니라 경고로만** 드러난다.

### 1. `mut` 로 타입을 바꾸려 한다

```text
let mut x = 5;  x = "다섯";
  ->  error[E0308]: mismatched types — expected integer, found `&str`
```

- `mut` 는 **값**의 문이고 섀도잉은 **타입**의 문이다. 둘을 섞으면 여기서 막힌다.
- 고치는 법은 `mut` 를 빼고 `let x = "다섯";` 로 **다시 묶는 것**이다.

### 2. 섀도잉을 「값 변경」으로 읽는다 — 블록에서 되돌아온다

```text
let x = 5;
{ let x = 99; println!("안: {x}"); }    // 99
println!("밖: {x}");                     // 5  <- 99가 아니다
```

- 「블록 안에서 바꿨는데 왜 안 바뀌었지?」가 이 주제에서 가장 자주 나오는 오해다.
- **바꾼 게 아니라 가린 것**이고, 블록이 끝나면 가림이 풀린다.
- 진짜로 바깥 값을 바꾸려면 **`mut` 를 쓰고 대입**해야 한다 — `let` 을 다시 쓰면 안 된다.

### 3. 추론이 안 되는 자리 — `Vec::new()` 만 쓰고 끝낸다

```rust
let v = Vec::new();
println!("{:?}", v);
```

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
```

`rustc --explain E0282` 가 드는 고치는 길은 셋이다(원문 요약 — 예제는 공식 설명에 있다).

> The type can be specified on the variable: `let x: Vec<i32> = Vec::new();`
> The type can also be specified in the path of the expression: `let x = Vec::<i32>::new();`
> ... you need not specify the full type if the compiler can infer it: `collect::<Vec<_>>()`

- `println!("{:?}", v)` 는 **힌트가 못 된다** — 어떤 `Vec<T>` 든 `Debug` 이기 때문이다.
- `v.push(7u8)` 한 줄이면 해결된다((5)번 참조). **쓰는 자리가 곧 힌트**다.
- 실무에서는 `collect()` 가 같은 모양으로 막힌다 — `let a: Vec<i32> = ....collect();` 또는 `collect::<Vec<_>>()`.

### 4. 경고를 안 읽는다 — 네 가지가 전부 「출력」이다

```rust
let unused = 1;
let _unused = 2;
let mut never_changed = 3;
println!("never_changed = {never_changed}");
let myValue = 4;
println!("myValue = {myValue}");
```

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

- `_unused` 는 **경고가 안 났다.** 밑줄 접두는 「일부러 안 쓴다」는 표시다.
- 경고가 **자기 이름을 말해 준다** — `unused_mut`·`unused_variables`·`non_snake_case`.\
  그 이름을 그대로 `#[allow(...)]`·`#[deny(...)]` 에 쓴다.
- **경고는 컴파일을 막지 않는다.** 위 프로그램은 실행됐다(`never_changed = 3` 출력).\
  그래서 CI 에서 `-D warnings` 로 막지 않으면 조용히 쌓인다.

## 구현 세부사항 대 언어 보장

이 갈래에서 「구현 세부사항」은 **린트 설정·컴파일러 진단 형식·에디션에 달린 것**이다.

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| `let` 이 기본 불변이고 두 번째 대입이 거부된다 | **언어** | E0384 · Reference(Variables) |
| 섀도잉이 새 바인딩이고 타입을 바꿀 수 있다 | **언어** | E0384 공식 설명이 대안으로 제시 · 실측 |
| 섀도잉이 블록 끝에서 풀린다 | **언어**(스코프 규칙) | 실측 |
| **정수 기본 타입이 `i32`, 부동소수가 `f64`** | **언어**(타입 폴백 규칙) | `3_000_000_000` 이 **`i32` 범위 초과**로 거부된 메시지 |
| `mut` 가 타입을 못 바꾼다 | **언어** | E0308 |
| **린트가 경고인지 에러인지** | **컴파일러 설정** | `#[warn]`/`#[deny]`·`-D warnings` 로 뒤집힌다 |
| **경고·에러 메시지의 문구와 배치** | **rustc 구현** | 버전이 오르면 바뀐다. 에러 **번호**가 더 안정적이다 |
| **`type_name_of_val` 이 돌려주는 문자열** | **보장 없음** | std 문서가 명시한다(아래) |

★ 타입 이름 문자열은 **관찰이지 보장이 아니다.** `std::any::type_name` 문서 원문:

> This is intended for diagnostic use. The exact contents and format of the string returned
> are not specified, other than being a best-effort description of the type. ...
> In addition, the output may change between versions of the compiler.

그래서 이 문서는 `i32`·`f64` 를 **두 층으로** 접지했다 —
① `type_name_of_val` 출력(관찰) ② `3_000_000_000` 이 `i32` 범위를 넘었다는 **컴파일 에러**(언어 규칙).
②만으로도 결론이 선다.

★ **「경고가 없다」가 「문제가 없다」가 아니다.** 린트 수준은 설정이라 `#[allow]` 한 줄로 사라진다.
반대로 `#[deny]` 하나로 같은 코드가 **에러**가 된다 — 실측에서 `#![deny(unused_variables)]` 가 붙자
같은 프로그램이 컴파일 실패했고, **그 에러에는 `E0xxx` 번호가 없었다**(린트는 에러 코드를 갖지 않는다).

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 이유 |
|---|---|---|
| 값을 한 번 정하고 안 바꾼다 | `let` | 기본. 대부분이 여기다 |
| 루프 카운터·누적값 | `let mut` | 같은 타입으로 계속 바뀐다 |
| 입력을 단계적으로 다듬는다(문자열 → 다듬기 → 파싱) | **섀도잉** | 중간 이름(`input_trimmed`·`input_num`)을 지어내지 않아도 된다 |
| 조건에 따라 다른 값을 한 번만 넣는다 | `let x;` + 갈래별 대입 | `mut` 가 필요 없다 |
| 일부러 안 쓰는 값 | `let _` 또는 `_이름` | 경고를 끄되 의도를 남긴다 |
| 모듈 최상위의 고정값 | `const` | `let` 은 아예 못 쓴다 (정본은 [목록의 **07번 주제**](../07-const-static-and-const-fn/)) |

판단 규칙 두 줄.

- **타입이 바뀌면 섀도잉, 값만 바뀌면 `mut`.** 이 한 줄로 거의 다 갈린다.
- **`mut` 를 붙이기 전에 「정말 바꿔야 하나」를 먼저 묻는다.** 안 바꾸면 `unused_mut` 가 알려 준다.

## 핵심 문장

- `let` 은 기본 불변이고, 거부 메시지는 「cannot assign **twice**」다 — 금지된 것은 **두 번째** 대입이다.
- 그래서 `let x; x = 5;` 는 `mut` 없이도 통과한다. 읽기 전에 쓰면 **E0381**, 두 번 대입하면 **E0384**.
- `mut` 는 **값**의 문이고 섀도잉은 **타입**의 문이다. `mut` 로 타입을 바꾸려 하면 **E0308**이다.
- 섀도잉은 새 바인딩이라 **블록이 끝나면 풀린다.** 「바꿨는데 왜 안 바뀌지」의 정체가 이것이다.
- 추론은 함수 전체를 본다 — **뒤 줄이 앞 줄의 타입을 정한다.** 답이 안 나오면 **E0282**.
- 힌트가 전혀 없으면 정수는 `i32`, 부동소수는 `f64`. **`3_000_000_000` 이 거부되는 것이 그 증거다.**
- 경고도 출력이다 — `unused_variables`·`unused_mut`·`non_snake_case`·`unused_assignments` 가 **자기 이름을 말해 준다.**

## 관련 자료

- [`../README.md`](../README.md) — Rust 문법·API 주제 목록(이 주제는 02번)
- [**01번 주제**](../01-cargo-crates-and-modules/)(`cargo`·크레이트·모듈) — 이 문서의 예제를 돌리는 방법(`rustc --edition 2021`)이 거기 있다
- [**03번 주제**](../03-primitive-types-and-integer-overflow/)(기본 타입·정수 오버플로) — **추론된 `i32` 가 실제로 어떻게 넘치는가**는 거기
- [**04번 주제**](../04-expressions-and-semicolons/)(표현식 지향) — `let x = { ... };` 의 오른쪽이 **왜 값인가**는 거기
- [`../../../variables-and-memory/`](../../../../variables-and-memory/) — **그쪽은 변수가 메모리에서 무엇인가의 일반론**까지,\
  **여기는 Rust 의 `let` 이 무엇을 거부하는가**부터다. 스택·힙 배치는 여기서 다루지 않는다.
- [`../../언어-특성/README.md`](../../언어-특성/README.md) — **그쪽은 불변을 기본으로 고른 것이 어떤 보증을 사는가**,\
  **여기는 그 선택이 컴파일 에러로 어떻게 나타나는가**다.
- [목록의 **07번 주제**](../07-const-static-and-const-fn/)(상수·`static`·`const fn`) — `const` 의 정본
- [목록의 **08번 주제**](../08-ownership-and-move/)(소유권과 이동) — 섀도잉된 옛 값이 **언제 해제되는가**는 거기
- [목록의 **19번 주제**](../19-pattern-syntax-guards-bindings-and-match-ergonomics/)(패턴 문법) — `let (a, b) = ...` 구조 분해의 정본
- [목록의 **15번 주제**](../15-slices-ranges-and-utf8-boundaries/)(슬라이스·UTF-8) — `"다섯".len() == 6` 의 정본

## 용어 풀이

- **바인딩(binding)** — 값에 이름을 묶는 것. `let` 이 만드는 것.
- **불변(immutable)** — 묶인 뒤 값을 바꿀 수 없음. Rust 의 기본값.
- **`mut`** — 그 바인딩을 통해 값을 바꿔도 된다는 표시. 타입은 못 바꾼다.
- **섀도잉(shadowing)** — 같은 이름으로 새 바인딩을 만들어 앞의 것을 가리는 것.
- **스코프(scope)** — 이름이 보이는 범위. 보통 중괄호 블록.
- **타입 추론(type inference)** — 안 적은 타입을 컴파일러가 채우는 것. 함수 단위로 본다.
- **타입 폴백(type fallback)** — 힌트가 전혀 없을 때 쓰이는 기본 타입. 정수 `i32`, 부동소수 `f64`.
- **터보피시(turbofish)** — `collect::<Vec<i32>>()` 의 `::<...>`. 식 쪽에 타입을 박는 표기.
- **린트(lint)** — 컴파일러의 스타일·위험 경고. 이름마다 수준(`allow`/`warn`/`deny`/`forbid`)이 있다.
- **어트리뷰트(attribute)** — `#[...]`·`#![...]`. 앞엣것은 다음 항목에, 뒤엣것은 감싸는 범위 전체에 붙는다.

---

## 더 들어가면

- `let mut x = 5; x += 1; let x = x;` 로 **다시 불변으로 굳힐 수 있다**(실측).\
  「여기까지만 바꾸고 그 뒤로는 안 바꾼다」를 타입 수준에서 못박는 관용구다.
- 섀도잉은 같은 줄에서도 된다 — `let x = x.trim();` 처럼 **앞 바인딩을 읽어 새 바인딩을 만든다.**\
  실측한 4단계: `"  42  "` → `trim()` → `parse()` → `i32`. 중간 이름을 하나도 안 지었다.
- `_` 하나만 쓰면 **이름을 붙이지 않는 것**이고 `let _x` 는 이름을 붙이는 것이다 — **해제 시점이 다르다.**\
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

  해제 시점의 정본은 [목록의 **09번 주제**](../09-copy-clone-and-drop/)다.
- 터보피시 두 형태가 같은 값을 냈다(실측) — `let a: Vec<i32> = ...collect();` 와 `...collect::<Vec<_>>()`.\
  `Vec<_>` 의 `_` 는 **거기만 추론에 맡긴다**는 뜻이다.
- 린트 수준 `forbid` 는 `deny` 보다 강하다 — 안쪽 항목에서 `#[allow(...)]` 로 되돌리는 것까지 막는다(실측).

```text
// ex.rs — 1행이 forbid, 2행은 빈 줄, 3행이 allow
#![forbid(unused_variables)]

#[allow(unused_variables)]
fn main() {
    let unused = 1;
}
```

```text
error[E0453]: allow(unused_variables) incompatible with previous forbid
 --> ex.rs:3:9
  |
1 | #![forbid(unused_variables)]
  |           ---------------- `forbid` level set here
2 |
3 | #[allow(unused_variables)]
  |         ^^^^^^^^^^^^^^^^ overruled by previous forbid

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0453`.
```
