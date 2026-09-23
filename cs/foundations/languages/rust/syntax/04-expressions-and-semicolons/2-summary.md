# rust/syntax/04 — 표현식 지향: 블록이 값·세미콜론의 의미 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [The Rust Reference](https://doc.rust-lang.org/reference/) 의 Statements and expressions ·
> Block expressions · `if`/`match`/`loop` expressions 절 · `rustc --explain E0308` / `E0317`.
> 이 머신의 `rust-docs`(1.92.0)를 열어 확인했다.
> **실행 검증** — 이 문서의 모든 출력·에러·경고는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 얻은 것이다. `cargo` 는 쓰지 않았다.
> **버전** — 여기 나오는 문법은 전부 1.0부터다. 관찰용 `type_name_of_val` 만 **1.76.0**부터다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**세미콜론은 마침표가 아니라 「손에 든 것을 내려놓고 나와라」는 표시다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 방 | **블록** `{ ... }` |
| 방에서 나오는 사람이 **손에 든 물건** | 그 블록의 **값** |
| **빈손**으로 나오는 것 | 값이 **`()`**(유닛) |
| 문 앞에서 물건을 내려놓게 하는 규칙 | **세미콜론** |
| 물건을 들고 나올 수 있는 사람 | **식**(expression) |
| 애초에 물건이 없는 사람 | **문**(statement) — `let`·항목 선언 |

- `{ let a = 3; a + 1 }` 은 **4를 들고 나온다.**
- `{ let a = 3; a + 1; }` 은 세미콜론 때문에 **빈손으로 나온다** — 값이 `()` 다.
- **글자 하나 차이로 그 블록의 타입이 `i32` 에서 `()` 로 바뀐다.** 이 언어의 성격이 여기 다 들어 있다.

```text
  let y = { let a = 3; a + 1  };        let z = { let a = 3; a + 1; };
                          ^                                     ^
                    세미콜론 없음                            세미콜론 있음

  +---------------------------+        +---------------------------+
  |  방 안                     |        |  방 안                     |
  |    a = 3                  |        |    a = 3                  |
  |    a + 1  -> 4 를 든다     |        |    a + 1; -> 4 를 내려놓는다|
  +------------|--------------+        +------------|--------------+
               v                                    v
          y = 4  (i32)                        z = ()  (유닛, 0바이트)
```

**언어도 똑같은 구조다.** 실측 출력이 이 그림 그대로다.

```text
y = 4 / 타입 i32
z = () / 타입 ()
z 의 크기 = 0
```

> **식(expression)** — 값으로 평가되는 것. `3 + 1`·`if c {1} else {2}`·`{ ... }`·`match`·`loop` 전부 식이다.\
> 예: Rust 에서는 `if` 가 식이라 `let x = if c { 1 } else { 2 };` 가 그냥 된다.

> **문(statement)** — 값으로 평가되지 않는 것. `let` 선언과 항목 선언(`fn`·`struct`·`mod`)이 그렇다.\
> 예: `let x = (let y = 5);` 는 문법 에러다 — `let` 은 값이 아니다.

> **유닛 타입 `()`** — 값이 딱 하나뿐인 타입. 「의미 있는 값이 없다」를 나타낸다.\
> 예: 반환 타입을 안 적은 함수는 `-> ()` 이고, `println!` 도 `()` 를 돌려준다. 크기는 **0바이트**다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **세미콜론 하나가 무엇을 바꾸는가** — 그리고 컴파일러는 그걸 어떤 메시지로 알려 주는가.
2. `if`·`match`·`loop` 를 **값으로 쓸 때** 지켜야 하는 제약은 무엇인가.
3. **`()` 는 무엇인가** — 왜 「아무것도 아님」이 아니라 「값」인가.

## 동작 방식

### (1) 블록이 값이다

**언제 쓰나** — 계산을 몇 줄로 나누되 중간 이름을 밖으로 흘리고 싶지 않을 때.

```rust
let y = {
    let a = 3;
    a + 1
};
```

```text
   let y = { ... };
             |
             +-- 블록의 마지막 "식"(세미콜론 없음)이 블록의 값이 된다
             |
             +-- a 는 블록 안에서만 산다. 밖으로 안 샌다
```

```text
y = 4 / 타입 i32
```

그림 해설 (한 단계씩):

- 블록 안의 `let a = 3;` 은 **문**이라 값이 없다. 값을 내는 것은 마지막 줄뿐이다.
- 마지막 줄에 세미콜론이 없으면 그것이 **꼬리 표현식**(tail expression)이다.
- `a` 는 블록 밖에서 안 보인다 — 임시 이름을 바깥 스코프에 안 남긴다.

비용 — 없음. 블록은 런타임에 아무 일도 하지 않는다.

### (2) ★ 세미콜론 하나가 타입을 바꾼다

**언제 쓰나** — 함수를 쓸 때마다. **이 주제의 정점이다.**

```rust
fn plus_one(a: i32) -> i32 {
    a + 1;              // 세미콜론 하나
}
```

```text
error[E0308]: mismatched types
 --> ex.rs:1:24
  |
1 | fn plus_one(a: i32) -> i32 {
  |    --------            ^^^ expected `i32`, found `()`
  |    |
  |    implicitly returns `()` as its body has no tail or `return` expression
2 |     a + 1;              // 세미콜론 하나
  |          - help: remove this semicolon to return this value

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0308`.
```

★ **도식이 본체다.**

```text
        a + 1              a + 1;
          |                   |
     [식 expression]     [문 statement]
          |                   |
          v                   v
      값 4 를 낸다        값을 버린다
          |                   |
          v                   v
     블록의 값 = 4       블록의 값 = ()
          |                   |
          v                   v
      -> i32  (맞다)      -> ()  (E0308)
```

메시지가 셋을 한꺼번에 말해 준다.

- **`expected i32, found ()`** — 무엇이 어긋났나.
- **`implicitly returns () as its body has no tail or return expression`** — 왜 그렇게 됐나.
- **`help: remove this semicolon to return this value`** — 세미콜론을 가리키며 고칠 곳을 짚는다.

블록을 `let` 에 쓸 때도 같다. 다만 **거기엔 에러가 아니라 경고가 붙는다.**

```rust
let z = {
    let a = 3;
    a + 1;
};
```

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
```

- 타입 표기가 없으면 `z` 가 그냥 `()` 가 되어 **컴파일은 통과한다.**
- 그때 남는 단서가 이 경고 하나다 — **「값을 만들어 놓고 버렸다」**.
- ★ **경고도 출력이다.** 이 자리는 에러가 안 나므로 경고를 안 읽으면 못 잡는다.

비용 — 없음. 컴파일 타임 타입 규칙이다.

### (3) `if` 가 식이다 — 두 갈래의 타입이 같아야 한다

**언제 쓰나** — 조건에 따라 다른 값을 고를 때. 삼항 연산자가 없는 이유가 이것이다.

```rust
let x = if c { 1 } else { 2 };
println!("바로 = {}", if c { "참" } else { "거짓" });
```

```text
x = 1
바로 = 참
```

타입이 갈리면 거부한다.

```text
let x = if c { 1 } else { "둘" };

error[E0308]: `if` and `else` have incompatible types
 --> ex.rs:3:31
  |
3 |     let x = if c { 1 } else { "둘" };
  |                    -          ^^^^ expected integer, found `&str`
  |                    |
  |                    expected because of this
```

`else` 가 없으면 또 다른 에러다.

```text
let x = if c { 1 };

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
```

```text
          if c { 1 } else { 2 }          if c { 1 }
                |      |                       |
               i32    i32                     i32   (else 갈래가 없다)
                +--+---+                       +--> 없는 갈래는 () 다
                   v                                +--+---+
                  i32                                  v
                                                   i32 와 () 가 만난다 -> E0317
```

그림 해설 (한 단계씩):

- **두 갈래가 같은 타입**이어야 `if` 전체의 타입이 정해진다.
- `else` 가 없으면 **없는 쪽이 `()`** 로 취급된다 — 그래서 값으로 못 쓴다.
- 반대로 **갈래 값이 원래 `()`** 면 `else` 가 없어도 된다(실측 — `if c { println!("참"); }` 은 `()` 라 통과).

비용 — 없음.

### (4) `match` 와 `loop` 도 식이다

**언제 쓰나** — 여러 갈래에서 값을 고를 때(`match`) · 조건이 맞을 때까지 돌며 값을 얻을 때(`loop`).

```rust
let name = match n { 1 => "하나", 2 => "둘", _ => "많음" };

let mut i = 0;
let found = loop {
    i += 1;
    if i * i > 50 { break i; }
};
```

```text
name = 둘
found = 8
```

`match` 는 팔끼리 타입이 같아야 하고, `loop` 는 `break` 값끼리 같아야 한다.

```text
let s = match n {
    1 => "하나",
    _ => { "많음"; }          // 이 팔만 세미콜론
};

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
```

```text
let v = loop {
    if i == 1 { break 1; }
    if i == 2 { break "둘"; }
};

error[E0308]: mismatched types
 --> ex.rs:6:27
  |
5 |         if i == 1 { break 1; }
  |                     ------- expected because of this `break`
6 |         if i == 2 { break "둘"; }
  |                           ^^^^ expected integer, found `&str`
```

그림 해설 (한 단계씩):

- `match` 팔 안에서도 **세미콜론이 같은 일을 한다.** 에러가 그 세미콜론을 직접 가리킨다.
- `loop` 는 **`break` 로 값을 낸다.** `while`·`for` 에는 이 문법이 없다.
- `break` 가 아예 없는 `loop` 는 타입이 **`!`**(발산)라 어떤 타입 자리에도 들어간다.\
  `fn never() -> i32 { loop {} }` 가 컴파일된다(실측). 정본은 목록의 **06번 주제**.

비용 — 없음.

### (5) `return` 과 꼬리 표현식

**언제 쓰나** — 함수 중간에서 빠져나갈 때(`return`) · 마지막 값을 낼 때(꼬리).

```rust
fn tail(a: i32) -> i32 { a * 2 }                    // 꼬리 표현식
fn early(a: i32) -> i32 { if a < 0 { return 0; } a * 2 }
fn mixed(a: i32) -> i32 {
    let b: i32 = if a < 0 { return -1 } else { a }; // return 이 식 자리에 있다
    b * 10
}
```

```text
tail(3)   = 6
early(-3) = 0
early(3)  = 6
mixed(-3) = -1
mixed(3)  = 30
```

```text
      함수 몸통의 마지막 줄
              |
     +--------+--------+
     |                 |
  세미콜론 없음      return ...;
     |                 |
  "꼬리 표현식"      "조기 반환"
  = 블록의 값        = 그 자리에서 나간다
     |                 |
     +--------+--------+
              v
        둘 다 반환값이 된다
```

그림 해설 (한 단계씩):

- 관용은 **꼬리 표현식**이다. `return` 은 **중간에서 빠져나갈 때** 쓴다.
- 꼬리 자리에 `return` 을 써도 컴파일은 된다 — `rustc` 는 아무 말도 안 한다.\
  다만 `clippy` 가 `needless_return` 으로 잡는다(기본 켜짐, 실측).
- `return` 은 **식**이고 타입이 `!` 라 `if` 갈래처럼 값이 필요한 자리에도 들어간다(`mixed`).

비용 — 없음. 같은 기계어가 된다.

### (6) `()` 는 「아무것도 아님」이 아니라 **값**이다

**언제 쓰나** — 반환값이 없는 함수·`println!`·대입문 전부.

```rust
fn nothing() {}
fn nothing2() -> () {}

let a = nothing();
let b = nothing2();
let c = println!("println! 도 값을 낸다");
```

```text
println! 도 값을 낸다
a=() b=() c=()
셋 다 크기 0 0 0
a == b ? true
```

대입도 식이다.

```text
let mut x = 0;
let a = { x = 5 };
x = 5 / a = () / a 의 크기 0
```

```text
   "값이 없다"                       "값이 하나뿐이다"
   +------------------+              +------------------+
   | null / void      |              |  ()              |
   | 특별 취급이 필요  |              |  보통 타입이다     |
   +------------------+              +------------------+
                                       크기 0 · 비교 가능
                                       Vec<()> 도 만들 수 있다
```

그림 해설 (한 단계씩):

- 반환 타입을 생략한 함수는 **`-> ()`** 와 같은 뜻이다.
- `()` 는 값이 하나뿐이라 **크기가 0바이트**다. 비교도 된다(`a == b` 가 `true`).
- `println!` 도, **대입문도** `()` 를 낸다 — 대입이 식이기 때문이다.
- Rust 에 `void` 라는 특수 개념이 없는 이유다. **보통 타입 하나로 해결했다.**

비용 — 0바이트. 런타임에 아무것도 차지하지 않는다.

## 문법 — 형태와 규칙

### 식인 것과 문인 것

| 식(값을 낸다) | 문(값이 없다) |
|---|---|
| 리터럴 · 변수 · 연산 `a + 1` | `let x = 5;` |
| 블록 `{ ... }` | 항목 선언 `fn`·`struct`·`mod`·`use` |
| `if` / `if let` | |
| `match` | |
| `loop`(`break 값` 가능) | |
| `while` / `for` (**항상 `()`**) | |
| 함수 호출 · 매크로 호출 | |
| 대입 `x = 5` (**값은 `()`**) | |
| `return` · `break` · `continue` (**타입 `!`**) | |

- `while`·`for` 는 **식이지만 값이 늘 `()`** 다. `break` 로 값을 낼 수 없다.

```text
let x: i32 = while i < 3 { i += 1; };

error[E0308]: mismatched types
 --> ex.rs:3:18
  |
3 |     let x: i32 = while i < 3 { i += 1; };
  |            ---   ^^^^^^^^^^^^^^^^^^^^^^^ expected `i32`, found `()`
```

### 금지 사례 — `let` 은 식이 아니다

```text
let x = (let y = 5);

error: expected expression, found `let` statement
 --> ex.rs:2:14
  |
2 |     let x = (let y = 5);
  |              ^^^
  |
  = note: only supported directly in conditions of `if` and `while` expressions
```

- `note` 가 말하는 예외가 **`if let`·`while let`** 이다(정본은 목록의 **20번 주제**).
- 그 밖의 자리에서 `let` 은 값이 될 수 없다.

### 타입을 컴파일러에게 물어보는 수법

```rust
let v = { let a = 3; a + 1 };
let _: () = v;
```

**일부러 틀린 타입을 주면** 에러가 진짜 타입을 말해 준다.

```text
error[E0308]: mismatched types
 --> ex.rs:3:17
  |
3 |     let _: () = v;
  |            --   ^ expected `()`, found integer
  |            |
  |            expected due to this
```

- **에러 메시지가 진짜 타입을 말해 준다.** 세미콜론을 하나 넣었다 뺐다 하며 이 수법으로 확인하면 규칙이 손에 붙는다.
- `type_name_of_val` 보다 강하다 — 저쪽 문자열은 보장되지 않지만 **타입 검사 결과는 언어 규칙**이다.

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다. 다섯 중 둘은 **에러가 아니라 경고로만** 드러난다.

### 1. ★ 함수 끝에 세미콜론을 붙인다

```text
fn plus_one(a: i32) -> i32 { a + 1; }
  ->  error[E0308] expected `i32`, found `()`
      implicitly returns `()` as its body has no tail or `return` expression
      help: remove this semicolon to return this value
```

- 다른 언어에서 오면 **거의 반드시 한 번은 밟는다.** 세미콜론을 「문장 끝 표시」로 읽기 때문이다.
- 메시지가 세미콜론을 직접 가리키므로 **읽으면 바로 고친다.** 안 읽으면 타입 얘기라 헤맨다.

### 2. ★ `let` 에서는 **에러가 아니라 경고**만 난다

```text
let z = { let a = 3; a + 1; };     // 컴파일 통과. z 는 ()

warning: unused arithmetic operation that must be used
   = note: `#[warn(unused_must_use)]` (part of `#[warn(unused)]`) on by default
```

- 타입 표기가 없으면 컴파일러가 `z: ()` 로 받아들이고 **넘어간다.**
- 그 다음 줄에서 `z` 를 숫자처럼 쓰면 **그때서야** 다른 에러가 난다 — **틀린 자리와 터지는 자리가 멀어진다.**
- 막는 법 둘: ① `let z: i32 = ...` 로 **타입을 적어 둔다** ② `-D warnings` 로 경고를 에러로 올린다.

### 3. `if` 두 갈래의 타입이 다르다 / `else` 가 없다

```text
let x = if c { 1 } else { "둘" };   ->  E0308 `if` and `else` have incompatible types
let x = if c { 1 };                 ->  E0317 `if` may be missing an `else` clause
```

- `E0317` 의 `note` 가 규칙을 한 줄로 말한다 — **「`if` expressions without `else` evaluate to `()`」**.
- `rustc --explain E0317` 의 설명도 같다:

  > An `if` expression without an `else` block has the type `()`, so this is a type error.
  > To resolve it, add an `else` block having the same type as the `if` block.

### 4. `match` 팔 하나에만 세미콜론

```text
_ => { "많음"; }
  ->  error[E0308] `match` arms have incompatible types
      | help: consider removing this semicolon
```

- 팔이 여럿이라 **한 팔만 `()` 가 되는** 사고가 난다. 눈으로는 잘 안 보인다.
- 에러가 세미콜론을 정확히 짚어 주므로 메시지를 끝까지 읽는다.

### 5. `while`·`for` 에서 값을 꺼내려 한다

```text
let x: i32 = while i < 3 { i += 1; };   ->  E0308 expected `i32`, found `()`
```

- 값을 내는 반복은 **`loop` + `break 값`** 뿐이다.
- `while`/`for` 로 값을 모으려면 이터레이터 쪽으로 간다(목록의 **36번 주제**).

## 구현 세부사항 대 언어 보장

이 갈래에서 「구현 세부사항」은 **진단 메시지의 모양과 린트 설정**이다. **규칙 자체는 전부 언어 보장**이다.

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| 블록의 꼬리 표현식이 블록의 값이다 | **언어** | Reference(Block expressions) · 실측 |
| 세미콜론을 붙이면 그 블록의 값이 `()` 가 된다 | **언어** | E0308 + `implicitly returns ()` · 실측 |
| `if`/`match`/`loop` 가 식이다 | **언어** | Reference · 실측 |
| `if` 두 갈래의 타입이 같아야 한다 | **언어** | E0308 |
| `else` 없는 `if` 의 타입이 `()` | **언어** | E0317 `note` 가 명시 |
| `while`/`for` 의 타입이 항상 `()` | **언어** | E0308 · 실측 |
| `break` 없는 `loop` 의 타입이 `!` | **언어** | `fn never() -> i32 { loop {} }` 가 컴파일됨 |
| **`()` 의 크기가 0** | **언어** | `size_of::<()>() == 0`. Reference 가 zero-sized 로 정의 |
| `let` 이 식이 아니다 | **언어** | `expected expression, found let statement` |
| **에러·경고 메시지의 문구와 화살표 배치** | **rustc 구현** | 버전이 오르면 바뀐다. **에러 번호**가 더 안정적이다 |
| **`unused_must_use` 가 경고인 것** | **린트 설정** | `-D warnings`·`#[deny]` 로 에러가 된다 |
| 꼬리 `return` 에 `rustc` 가 침묵하는 것 | **린트 설정** | `clippy::needless_return` 은 잡는다(기본 켜짐) |

★ **이 주제는 「구현에 달린 것」이 드물다.** 세미콜론 규칙은 문법이고 컴파일 타임에 끝난다 —
[03번](../03-primitive-types-and-integer-overflow/)처럼 **빌드 프로필에 따라 답이 갈리는 자리가 없다.**
대신 **경고냐 에러냐가 설정에 달린다** — 「어디서 틀리나」 2번이 정확히 그 자리다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 이유 |
|---|---|---|
| 조건에 따라 값을 고른다 | `let x = if c { .. } else { .. };` | 삼항 연산자가 없다. 이게 그 자리다 |
| 갈래가 셋 이상 | `match` | 완전성 검사가 따라온다(목록의 **18번 주제**) |
| 몇 줄 계산해 값 하나를 만든다 | 블록 식 `let y = { ... };` | 임시 이름이 밖으로 안 샌다 |
| 조건이 맞을 때까지 돌며 값을 얻는다 | `loop` + `break 값` | `while`/`for` 로는 값을 못 낸다 |
| 함수 중간에서 빠져나간다 | `return` | 꼬리에는 안 쓰는 것이 관용이다 |
| 반환값이 필요 없다 | 아무것도 안 적는다(`-> ()`) | `-> ()` 를 명시할 필요가 없다 |
| 값을 일부러 버린다 | `let _ = 식;` | `unused_must_use` 경고를 의도로 바꾼다 |

판단 규칙 두 줄.

- **세미콜론을 붙일지 말지는 「이 값을 쓸 것인가」로 정한다.** 문장 끝이라서 붙이는 게 아니다.
- **블록의 타입이 궁금하면 `let _: () = 식;` 을 던져 컴파일러에게 물어본다.**

## 핵심 문장

- 블록의 값은 **꼬리 표현식**이고, 세미콜론을 붙이면 그 값이 버려져 블록이 **`()`** 가 된다.
- 함수에서는 그게 **E0308**로 터지고, 메시지가 `remove this semicolon` 까지 짚어 준다.
- `let` 에서는 **에러가 아니라 `unused_must_use` 경고**만 난다 — 이 자리가 조용해서 더 위험하다.
- `if`·`match`·`loop` 는 **식**이다. 갈래의 타입이 같아야 하고, `else` 없는 `if` 는 `()` 다(**E0317**).
- `while`·`for` 는 식이지만 **값이 늘 `()`** 다. 값을 내는 반복은 `loop` + `break 값` 뿐이다.
- `()` 는 「없음」이 아니라 **값이 하나뿐인 타입**이고 크기는 **0바이트**다. 대입문도 `println!` 도 `()` 를 낸다.
- **`break` 없는 `loop` 의 타입은 `!`** 라 어떤 타입 자리에도 들어간다(정본은 목록의 **06번 주제**).

## 관련 자료

- [`../README.md`](../README.md) — Rust 문법·API 주제 목록(이 주제는 04번)
- [**02번 주제**](../02-bindings-mut-and-shadowing/)(변수 바인딩) — `let x = { ... };` 의 **왼쪽**이 무엇인가는 거기
- [**03번 주제**](../03-primitive-types-and-integer-overflow/)(기본 타입) — `size_of::<()>() == 0` 의 실측 표가 거기
- [**01번 주제**](../01-cargo-crates-and-modules/)(`cargo`·크레이트) — 이 문서의 예제를 돌리는 방법
- [`../../언어-특성/README.md`](../../언어-특성/README.md) — **그쪽은 Rust 를 고르는 논증**까지,\
  **여기는 그 언어의 문법이 식 중심이라는 사실과 그 결과**부터다. 소유권은 이 문서에 나오지 않는다.
- 목록의 **05번 주제**(제어 흐름 — `loop`·라벨·`break` 값) — `loop` 의 정본
- 목록의 **06번 주제**(함수·반환·발산 타입 `!`) — `!` 의 정본. 여기서는 **대비만** 했다
- 목록의 **18번 주제**(`match` 와 완전성 검사) · **19번 주제**(패턴 문법) — `match` 의 정본
- 목록의 **20번 주제**(`if let`·`while let`·`let else`) — `let` 이 조건 자리에 오는 예외
- 목록의 **36번 주제**(`Iterator`) — 반복에서 값을 모으는 관용

## 용어 풀이

- **식(expression)** — 값으로 평가되는 것. Rust 문법의 대부분이 식이다.
- **문(statement)** — 값으로 평가되지 않는 것. `let` 선언과 항목 선언.
- **블록 식(block expression)** — `{ ... }`. 마지막 꼬리 표현식이 그 값이 된다.
- **꼬리 표현식(tail expression)** — 블록의 마지막에 **세미콜론 없이** 놓인 식.
- **유닛 타입 `()`** — 값이 하나뿐인 타입. 크기 0바이트. 「의미 있는 값이 없다」를 나타낸다.
- **발산 타입 `!`** — 값을 절대 내지 않는 것의 타입. `return`·`break`·`panic!`·`loop {}` 가 그렇다.
- **표현식 지향(expression-oriented)** — 제어 구조까지 값을 내는 언어 설계. 삼항 연산자가 필요 없어진다.
- **`unused_must_use`** — 값을 내는 식을 세미콜론으로 버렸을 때의 기본 경고.
- **`unreachable_code`** — `!` 뒤의 코드처럼 도달할 수 없는 줄에 붙는 기본 경고.

---

## 더 들어가면

- 대입 `x = 5` 자체가 식이고 값은 `()` 다(실측 — `let a = { x = 5 };` 에서 `a` 가 `()`, 크기 0).\
  C 의 `a = b = 5` 연쇄가 Rust 에서 안 되는 이유다 — `b = 5` 의 값이 `5` 가 아니라 `()` 라서. 던져서 확인했다.

```text
error[E0308]: mismatched types
 --> ex.rs:4:9
  |
2 |     let mut a = 0;
  |                 - expected due to this value
3 |     let mut b = 0;
4 |     a = b = 5;
  |         ^^^^^ expected integer, found `()`
```
- `break` 없는 `loop` 뒤에 코드를 두면 경고가 붙는다(실측).

```text
let x: i32 = loop {};
println!("{x}");

warning: unreachable statement
  = note: `#[warn(unreachable_code)]` (part of `#[warn(unused)]`) on by default
```

- 꼬리에 `return` 을 써도 `rustc` 는 침묵하지만 `clippy` 는 기본으로 잡는다(실측).

```text
warning: unneeded `return` statement
  = note: `#[warn(clippy::needless_return)]` on by default
help: remove `return`
```

- `if c { println!("참"); }` 처럼 **갈래 값이 원래 `()`** 면 `else` 가 없어도 값으로 쓸 수 있다(실측 — `x = ()`, 크기 0).\
  E0317 이 뜨는 것은 **`()` 아닌 타입을 기대할 때**뿐이다.
- `let _: () = 식;` 수법은 제네릭 코드에서 특히 쓸모 있다 — 추론된 타입을 **에러 메시지로 뽑아내는** 방법이다.
