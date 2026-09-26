# rust/syntax/29 — 변환 트레이트 `From`/`Into`/`TryFrom`/`AsRef`/`Borrow` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [std — `trait From`](https://doc.rust-lang.org/std/convert/trait.From.html) ·
> [`trait Into`](https://doc.rust-lang.org/std/convert/trait.Into.html) ·
> [`trait TryFrom`](https://doc.rust-lang.org/std/convert/trait.TryFrom.html) ·
> [`trait AsRef`](https://doc.rust-lang.org/std/convert/trait.AsRef.html) ·
> [`trait Borrow`](https://doc.rust-lang.org/std/borrow/trait.Borrow.html) ·
> [Reference — The try propagation expression](https://doc.rust-lang.org/reference/expressions/operator-expr.html#the-try-propagation-expression).
> ★ 위 문서는 **이 머신의 `rust-docs`(1.92.0) 로컬 사본**을 열어 읽었다 — 온라인 판과 문구가 다를 수 있다.
> ★ 포괄 구현(blanket impl)은 **이 머신에 설치된 `rust-docs` 의 std 소스 페이지**(`src/core/convert/mod.rs.html`)를 **스크립트로 뽑아** 확인했다((3)).
> **실행 검증** — 이 문서의 모든 출력·에러는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서\
> **`rustc --edition 2021 <파일>.rs`** 로 실제로 돌려 받은 것이다.\
> ★★ **`--edition` 을 빼면 에디션 2015 다** — 에디션을 안 밝힌 결과는 다른 언어를 컴파일한 것과 같다.\
> ★★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.
> 소스 펜스도 캡처가 찍었다(첫 줄 `// <파일명>.rs` 가 실제로 컴파일한 파일 이름이다).\
> ★★ **외부 크레이트를 하나도 쓰지 않았다**(네트워크 없음).
> **버전** — `From`·`Into`·`AsRef`·`Borrow` 는 **1.0.0**, `TryFrom`·`TryInto` 는 **1.34.0** 부터다((3)의 `#[stable(since = …)]` 속성 그대로).
> **2021 에디션부터 `TryFrom`·`TryInto` 가 프렐류드에 들어 있어** `use` 없이 쓴다(이 문서의 소스가 전부 그렇다).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

```text
===== rustc --version =====
rustc 1.92.0 (ded5c06cf 2025-12-08)
(exit 0)
===== cargo --version =====
cargo 1.92.0 (344c4567c 2025-10-21)
(exit 0)
===== g++ --version | head -1 =====
g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
(exit 0)
===== clang++ --version | head -1 =====
Ubuntu clang version 18.1.3 (1ubuntu1)
(exit 0)
===== nm --version | head -1 =====
GNU nm (GNU Binutils for Ubuntu) 2.42
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | 해시값 자체 | 이 문서는 **값을 안 찍고** 「같나 다르나」만 찍는다((8)) — 28번과 같은 방침 |
| 안 흔들린다 | **종료 코드 0 · 1** | 컴파일 실패는 1 이다. 이 주제에는 패닉 블록이 없다 |
| 안 흔들린다 | 에러 번호·제목·`= note:`·`help:` 줄·`파일:줄:칸` | 같은 rustc 판에서 고정이다 |
| 안 흔들린다 | 진단에 박히는 `/rustc/ded5c06cf…/library/…` 경로 | ★ **이 rustc 판의 커밋 해시**다. 판이 바뀌면 바뀐다 |
| 안 흔들린다 | `` the following other types implement trait `From<T>` `` 의 **목록** | 같은 std 판에서 고정이다. ★ **판이 오르면 늘 수 있다**(구현 세부) |
| 안 흔들린다 | std 소스 페이지의 **줄 번호**((3)) | 같은 `rust-docs` 판에서 고정이다. 판이 오르면 움직인다 |

★ 정규화 규칙은 **기본 넷**(주소·PID·스레드 id·시간)만 썼고 **하나도 걸리지 않았다**(제출 전 재대조).

## 한눈에 — 쉽게 말하면

**변환 트레이트는 「이 값을 저 타입으로 바꿀 수 있다」를 한 방향으로 적어 두는 문서다.
그런데 문서를 한 장 쓰면 std 가 뒷면을 자동으로 찍어 준다 — 단, 한쪽 면에만.**

| 비유 | 실체 |
|---|---|
| 「**환전소가 붙여 둔 환율표**」 — 받는 쪽이 적는다 | **`From<A> for B`** — `B` 쪽에서 「`A` 를 받아 나를 만든다」 |
| 「**그 표를 보고 손님이 거꾸로 읽는 창구**」 | ★★ **`Into<B> for A`** — **std 가 자동으로 세운다**((1)·(3)). 내가 쓸 일이 거의 없다 |
| 「**창구만 세우고 환율표는 안 붙인 가게**」 | ★★★ `Into` 만 손으로 쓰면 **`From` 은 안 생긴다** — `?` 도 못 쓴다((2)·(4)) |
| 「**환전이 거절될 수 있는 창구**」 | **`TryFrom`** — `Result` 를 돌려준다. 거절 사유는 **연관 타입 `Error`**((5)·(6)) |
| 「**여권을 잠깐 보여 주기**」 | **`AsRef<str>`** — 빌려서 **보기만** 한다. 값은 그대로 네 것이다((7)) |
| 「**여권을 보여 줘도 같은 사람으로 판정돼야 한다는 약속**」 | ★★ **`Borrow<str>`** — `AsRef` 에 **`Hash`·`Eq` 가 같다는 계약**을 더한 것((8)) |

- ★★★ **판정은 두 줄이다 — 「구현은 `From` 으로 하고, 경계는 `Into` 로 건다.」**
  `From` 하나에서 `Into`·`TryFrom`·`TryInto` 가 **포괄 구현으로 전부** 생긴다((3)).
  거꾸로 `Into` 만 쓰면 **`From` 이 끝내 안 생긴다** — 포괄 구현이 한 방향으로만 걸려 있기 때문이다.
  그래서 **받는 쪽 경계는 `Into`** 로 걸어야 **양쪽 구현을 다 받는다**(std 의 `From` 문서가 그렇게 권한다 — (2)의 `convert` 가 그 반례다).
- ★★ **`From` 은 「무손실·무실패」의 약속이다** — 그래서 `u64 → u32` 에는 `From` 이 **없다**((5)).
  `as` 는 조용히 자르고, `TryFrom` 은 묻고, `From` 은 **애초에 실패할 수 없는 쪽에만** 있다.
- ★★ **`AsRef` 와 `Borrow` 는 시그니처가 같은데 계약이 다르다** — `HashMap::get` 이 `Borrow` 를 요구하는 이유가 그 계약이다((8)).

```text
   어느 쪽을 구현하면 무엇이 생기나 — 포괄 구현의 화살표 (3)의 std 소스 그대로

        내가 쓴 것                         std 가 자동으로 세우는 것
   ┌────────────────────┐
   │ impl From<A> for B │ ──────────▶  impl Into<B> for A           ★ (1) into() 가 된다
   └────────────────────┘      │
                               └────▶  impl TryFrom<A> for B        Error = Infallible  (5)
                                         └──▶ impl TryInto<B> for A

   ┌────────────────────┐
   │ impl Into<B> for A │ ──────────▶  impl TryFrom<A> for B        Error = Infallible  ★ (2) 뜻밖
   └────────────────────┘                └──▶ impl TryInto<B> for A
            │
            └────── ✘ ──────▶  impl From<A> for B  은 끝내 안 생긴다
                                  → B::from(a)          E0308 (2)
                                  → U: From<T> 경계     E0277 (2)
                                  → ? 연산자             E0277 (4)

   ┌───────────────────────┐
   │ impl TryFrom<A> for B │ ──────▶  impl TryInto<B> for A        Error 는 내가 고른 것 (6)
   └───────────────────────┘

   그리고 누구나 공짜로 가진 것 —  impl From<T> for T   (자기 자신으로 바꾸기, (1)의 넷째 줄)
```

> **포괄 구현(blanket impl)** — 특정 타입이 아니라 **조건을 만족하는 모든 타입**에 한 번에 거는 구현.\
> 예: `impl<T, U> Into<U> for T where U: From<T>` — 「`U` 가 `T` 로부터 만들어질 수 있으면 `T` 는 `U` 로 바뀔 수 있다」.

> **무손실 변환(lossless conversion)** — 어떤 입력에 대해서도 **정보를 잃지 않고 실패하지도 않는** 변환.\
> 예: `u32 → u64` 는 무손실이다. `u64 → u32` 는 아니다(큰 값이 안 담긴다).

> **프렐류드(prelude)** — `use` 없이 모든 모듈에 자동으로 들어오는 이름 묶음.\
> 예: 2021 에디션의 프렐류드에는 `TryFrom`·`TryInto` 가 있고, 2015·2018 에는 없다.

## 이 주제가 답하려는 질문

1. ★★★ **어느 방향으로 구현해야 양쪽이 생기나** — `From` 이다. `Into` 만 쓰면 무엇이 안 되나((1)·(2)·(3)·(4)).
2. ★★ **변환이 실패할 수 있으면 어떻게 적나** — `From` 이 없는 자리, `TryFrom` 과 `as` 의 차이((5)·(6)).
3. ★★ **빌려서 보기만 하는 변환은 왜 둘인가** — `AsRef` 와 `Borrow`, 그리고 `impl Into<String>` 인자의 득실((7)·(8)·(9)).

★ [**25번 주제**](../25-traits-definition-impl-default-methods-and-associated-types/)가 「제네릭 파라미터 판 트레이트는 한 타입에 여러 번 구현된다」고 했다.
**`From<T>` 가 그 대표 사례다** — `String` 은 `From<&str>`·`From<char>`·`From<Box<str>>` … 를 전부 가진다.
여기는 「**그 여러 구현이 서로 무엇을 만들어 내나**」다.

## 동작 방식

### (0) 이 주제가 쓰는 네 창

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **한쪽만 구현하고 반대쪽을 불러 보기** | 「**한쪽만 구현하면 양쪽이 생기나**」를 **컴파일러가 말한다**((1)·(2)·(4)) | ★ **이 주제의 본체** |
| ★★ **std 소스 페이지에서 포괄 구현 뽑기** | 화살표가 **왜 그 방향인가** — 네 줄의 `impl<…>`((3)) | ★ 이 주제의 고유 창 |
| **없는 변환을 불러 보기** | `From` 이 **무엇에 없는가** — E0277 의 후보 목록((5)) | 「에러도 출력이다」 |
| ★ **해시를 「같나 다르나」로만 찍기** | `Borrow` 의 계약이 **깨지면 조회가 사라진다**((8)) | [**28번 주제**](../28-partialeq-eq-partialord-ord-and-hash-contracts/)의 방식 |

★★ **「부적용인 창」이 하나 있다** — **런타임 비용**이다. 변환이 **복사하는지 옮기는지**는 (9)에서 **말로만** 적는다
(`String` 을 넘기면 옮기고 `&str` 을 넘기면 새로 할당한다 — 할당 계수기를 이 주제에서는 안 세웠다).
★ **「같은 질문을 다른 창으로」 하나** — (9)의 「`impl Into<String>` 이 **몇 벌** 생기나」는 [**31번 주제**](../31-generics-trait-bounds-where-and-monomorphization/)의 본체 창(**심볼 표**)을 빌려 물었다((9)의 두 블록).

### (1) ★★ `From` 하나로 `into()` 까지 — 내가 안 쓴 메서드가 불린다

**언제 쓰나** — 내 타입 둘 사이에 변환이 있을 때. **`From` 쪽으로 쓴다.**

```rust
// r29_from.rs
// From 하나만 구현한다 — into() 는 어디서 오나
struct Celsius(f64);
struct Fahrenheit(f64);

impl From<Celsius> for Fahrenheit {
    fn from(c: Celsius) -> Fahrenheit {
        Fahrenheit(c.0 * 1.8 + 32.0)
    }
}

fn report(t: impl Into<Fahrenheit>) {
    let f: Fahrenheit = t.into(); // ★ 이 into() 는 내가 안 썼다
    println!("  report  {}", f.0);
}

fn main() {
    println!("from()    {}", Fahrenheit::from(Celsius(100.0)).0);
    let f: Fahrenheit = Celsius(0.0).into();
    println!("into()    {}", f.0);
    report(Celsius(-40.0));
    report(Fahrenheit(1.0)); // ★ 자기 자신으로도 into 된다
}
```

```text
===== rustc --edition 2021 r29_from.rs =====
(exit 0)
===== ./r29_from =====
from()    212
into()    32
  report  -40
  report  1
(exit 0)
```

- ★★ **12행과 18행의 `into()` 는 이 파일 어디에도 정의가 없다.** 내가 쓴 것은 5행의 `From` 하나뿐이다.
  `into()` 는 std 의 **포괄 구현** `impl<T, U> Into<U> for T where U: From<T>` 에서 왔다((3)).
- **호출 모양이 둘이다** — `Fahrenheit::from(c)` 는 **받는 쪽 이름으로**, `c.into()` 는 **보내는 쪽 값으로** 부른다.
  `into()` 는 **목적지를 추론에 맡기므로** 18행처럼 `let f: Fahrenheit` 로 **타입을 적어 줘야** 한다.
- ★ **21행 `report(Fahrenheit(1.0))` 도 통과했다** — `Fahrenheit` 를 `Fahrenheit` 로 바꾸는 `From` 은 내가 안 썼다.
  이것은 std 의 또 하나의 포괄 구현 **`impl<T> From<T> for T`**(반사 구현)에서 온다((3)의 둘째 `impl`).
  그래서 **`impl Into<X>` 인자는 `X` 자체도 받는다** — (9)의 `User::new(String)` 이 그 효과다.

### (2) ★★★ `Into` 만 구현하면 — 컴파일러가 방향을 말한다

**언제 쓰나** — 안 쓴다. **이 절은 「왜 안 쓰나」의 증거다.**

```rust
// r29_into_only.rs
// Into 만 구현하면 — From 쪽은 생기나
struct Celsius(f64);
struct Fahrenheit(f64);

impl Into<Fahrenheit> for Celsius {
    fn into(self) -> Fahrenheit {
        Fahrenheit(self.0 * 1.8 + 32.0)
    }
}

fn convert<T, U: From<T>>(t: T) -> U {
    U::from(t)
}

fn main() {
    let a: Fahrenheit = Celsius(100.0).into(); // 직접 쓴 방향
    let b = Fahrenheit::from(Celsius(0.0)); // 반대 방향
    let c: Fahrenheit = convert(Celsius(0.0)); // From 경계
    println!("{} {} {}", a.0, b.0, c.0);
}
```

```text
===== rustc --edition 2021 r29_into_only.rs =====
error[E0308]: mismatched types
  --> r29_into_only.rs:17:30
   |
17 |     let b = Fahrenheit::from(Celsius(0.0)); // 반대 방향
   |             ---------------- ^^^^^^^^^^^^ expected `Fahrenheit`, found `Celsius`
   |             |
   |             arguments to this function are incorrect
   |
note: associated function defined here
  --> /rustc/ded5c06cf21d2b93bffd5d884aa6e96934ee4234/library/core/src/convert/mod.rs:592:8
help: call `Into::into` on this expression to convert `Celsius` into `Fahrenheit`
   |
17 |     let b = Fahrenheit::from(Celsius(0.0).into()); // 반대 방향
   |                                          +++++++

error[E0277]: the trait bound `Fahrenheit: From<Celsius>` is not satisfied
  --> r29_into_only.rs:18:25
   |
18 |     let c: Fahrenheit = convert(Celsius(0.0)); // From 경계
   |                         ^^^^^^^^^^^^^^^^^^^^^ unsatisfied trait bound
   |
help: the trait `From<Celsius>` is not implemented for `Fahrenheit`
  --> r29_into_only.rs:3:1
   |
 3 | struct Fahrenheit(f64);
   | ^^^^^^^^^^^^^^^^^
note: required by a bound in `convert`
  --> r29_into_only.rs:11:18
   |
11 | fn convert<T, U: From<T>>(t: T) -> U {
   |                  ^^^^^^^ required by this bound in `convert`

error: aborting due to 2 previous errors

Some errors have detailed explanations: E0277, E0308.
For more information about an error, try `rustc --explain E0277`.
(exit 1)
```

- ★★★ **에러가 두 건이고 번호가 다르다** — 같은 결함(「`From<Celsius> for Fahrenheit` 가 없다」)인데 **E0308 과 E0277** 로 갈렸다.
  - **17행 E0308** — `Fahrenheit::from(…)` 을 부르자 rustc 는 **있는 `From` 중에서 고른다.**
    `Fahrenheit` 가 가진 `From` 은 **반사 구현 `From<Fahrenheit>` 하나뿐**이라 인자 타입을 `Fahrenheit` 로 기대했고,
    그래서 「**expected `Fahrenheit`, found `Celsius`**」라는 **타입 불일치**로 나온다.
  - **18행 E0277** — 제네릭 경계 `U: From<T>` 를 거치면 비로소 「**the trait bound `Fahrenheit: From<Celsius>` is not satisfied**」로 **정면으로** 말한다.
- ★★ **`help:` 가 방향을 알려 준다** — 「**call `Into::into` on this expression**」.
  rustc 는 `Into` 쪽 구현이 **있다는 것을 알고** 그것을 쓰라고 권한다. **반대쪽은 안 생겼다는 자백**이다.
- 16행(직접 쓴 방향)은 **에러가 없다** — 두 건 모두 **반대 방향**에서만 났다.
- ★★ **18행의 에러는 `convert` 의 경계 탓이기도 하다** — `U: From<T>` 로 걸면 **`Into` 만 가진 타입을 못 받는다.**
  std 의 `From` 문서가 「**제네릭 함수의 경계에는 `From` 보다 `Into` 를 쓰라**」고 권하는 이유가 이것이다 —
  `T: Into<U>` 로 걸었다면 `From` 을 쓴 타입(포괄 구현으로 `Into` 를 얻는다)과 `Into` 만 쓴 타입을 **둘 다** 받는다.
  **구현은 `From`, 경계는 `Into`** — 화살표 하나로 둘 다 설명된다.

**경계를 `Into` 로 고치면.**

```rust
// r29_bound_into.rs
// 경계를 Into 로 걸면 — 양쪽 구현을 다 받는다
struct Celsius(f64);
struct Kelvin(f64);
struct Fahrenheit(f64);

impl Into<Fahrenheit> for Celsius {
    // Into 만 쓴 쪽
    fn into(self) -> Fahrenheit {
        Fahrenheit(self.0 * 1.8 + 32.0)
    }
}

impl From<Kelvin> for Fahrenheit {
    // From 을 쓴 쪽
    fn from(k: Kelvin) -> Fahrenheit {
        Fahrenheit((k.0 - 273.15) * 1.8 + 32.0)
    }
}

fn convert<T: Into<U>, U>(t: T) -> U {
    t.into()
}

fn main() {
    let a: Fahrenheit = convert(Celsius(100.0));
    let b: Fahrenheit = convert(Kelvin(273.15));
    println!("{} {}", a.0, b.0);
}
```

```text
===== rustc --edition 2021 r29_bound_into.rs =====
(exit 0)
===== ./r29_bound_into =====
212 32
(exit 0)
```

- ★★ **`Into` 만 쓴 `Celsius` 와 `From` 을 쓴 `Kelvin` 이 한 `convert` 를 둘 다 통과했다**(`212 32`).
  `Kelvin` 은 `From` 에서 포괄 구현으로 `Into` 를 얻었고, `Celsius` 는 `Into` 를 직접 가졌다 — **경계가 보는 것은 `Into` 하나**다.

**그런데 뜻밖에 생기는 것도 있다** — `try_from` 이다.

```rust
// r29_into_try.rs
// Into 만 구현했는데 — try_from 은 된다
use std::convert::Infallible;

struct Celsius(f64);
struct Fahrenheit(f64);

impl Into<Fahrenheit> for Celsius {
    fn into(self) -> Fahrenheit {
        Fahrenheit(self.0 * 1.8 + 32.0)
    }
}

fn main() {
    let r: Result<Fahrenheit, Infallible> = Fahrenheit::try_from(Celsius(100.0));
    match r {
        Ok(f) => println!("try_from Ok {}", f.0),
        Err(never) => match never {},
    }
}
```

```text
===== rustc --edition 2021 r29_into_try.rs =====
(exit 0)
===== ./r29_into_try =====
try_from Ok 212
(exit 0)
```

- ★★ **`Into` 만 구현했는데 `Fahrenheit::try_from(Celsius)` 가 된다** — 그리고 `Error` 가 **`Infallible`**(값이 하나도 없는 타입)이다.
  (3)의 넷째 포괄 구현이 **`TryFrom<U> for T where U: Into<T>`** 로, `From` 이 아니라 **`Into`** 에 걸려 있기 때문이다.
- ★ 17행 `Err(never) => match never {}` — **`Infallible` 은 만들 수 없는 값**이라 빈 `match` 로 끝난다. 그 갈래는 **절대 안 탄다**는 것을 타입이 보증한다.
- ★ **이 비대칭이 판정을 바꾸지는 않는다** — `?` 와 `U: From<T>` 경계가 **여전히 막힌다**((4)). 그래서 답은 그대로 「`From` 을 써라」다.

### (3) ★★ 화살표가 왜 그 방향인가 — std 소스의 포괄 구현 넷

**언제 쓰나** — (1)·(2)의 결과를 **외우지 않고 유도**하고 싶을 때. 네 줄이면 된다.

```python
# r29_blanket.py
# 설치된 rust-docs 의 std 소스 페이지에서 변환 트레이트의 포괄 구현 넷만 뽑는다
import html
import re
import subprocess

root = subprocess.run(["rustc", "--print", "sysroot"], capture_output=True, text=True).stdout.strip()
page = root + "/share/doc/rust/html/src/core/convert/mod.rs.html"
text = html.unescape(re.sub(r"<[^>]+>", "", open(page, encoding="utf-8").read()))
lines = text.split("\n")
want = re.compile(r"^(\d+)(impl<T(, U)?> const (Into<U>|From<T>|TryInto<U>|TryFrom<U>) for T)")

for i, l in enumerate(lines):
    if want.match(l):
        k = i - 2  # 위의 #[stable(..)] 속성 두 줄부터
        while True:
            m = re.match(r"^(\d+)(.*)$", lines[k])
            no, code = m.group(1), m.group(2)
            if not code.strip().startswith("///"):
                print(f"{no:>4} {code}")
            if code.startswith("}"):
                break
            k += 1
        print()
```

```text
===== python3 r29_blanket.py =====
 765 #[stable(feature = "rust1", since = "1.0.0")]
 766 #[rustc_const_unstable(feature = "const_convert", issue = "143773")]
 767 impl<T, U> const Into<U> for T
 768 where
 769     U: [const] From<T>,
 770 {
 775     #[inline]
 776     #[track_caller]
 777     fn into(self) -> U {
 778         U::from(self)
 779     }
 780 }

 783 #[stable(feature = "rust1", since = "1.0.0")]
 784 #[rustc_const_unstable(feature = "const_convert", issue = "143773")]
 785 impl<T> const From<T> for T {
 787     #[inline(always)]
 788     fn from(t: T) -> T {
 789         t
 790     }
 791 }

 809 #[stable(feature = "try_from", since = "1.34.0")]
 810 #[rustc_const_unstable(feature = "const_convert", issue = "143773")]
 811 impl<T, U> const TryInto<U> for T
 812 where
 813     U: [const] TryFrom<T>,
 814 {
 815     type Error = U::Error;
 816 
 817     #[inline]
 818     fn try_into(self) -> Result<U, U::Error> {
 819         U::try_from(self)
 820     }
 821 }

 825 #[stable(feature = "try_from", since = "1.34.0")]
 826 #[rustc_const_unstable(feature = "const_convert", issue = "143773")]
 827 impl<T, U> const TryFrom<U> for T
 828 where
 829     U: [const] Into<T>,
 830 {
 831     type Error = Infallible;
 832 
 833     #[inline]
 834     fn try_from(value: U) -> Result<Self, Self::Error> {
 835         Ok(U::into(value))
 836     }
 837 }

(exit 0)
```

- ★★★ **767행 — `impl<T, U> Into<U> for T where U: From<T>`.** 조건이 **`From` 쪽**에 걸려 있다.
  그래서 `From` 을 쓰면 `Into` 가 생기고, **`Into` 를 써도 `From` 은 안 생긴다** — 반대 방향의 포괄 구현이 **존재하지 않는다.**
- ★ **왜 반대쪽을 안 두나** — 두 포괄 구현이 **서로를 정의**하게 된다. 내 크레이트에 그 반대쪽을 하나 두어 던져 봤다.
```rust
// r29_reverse.rs
// 반대 방향 포괄 구현을 내가 하나 더 두면
impl<T, U> From<T> for U
where
    T: Into<U>,
{
    fn from(t: T) -> U {
        t.into()
    }
}

fn main() {}
```

```text
===== rustc --edition 2021 r29_reverse.rs =====
error[E0391]: cycle detected when computing whether impls specialize one another
 --> r29_reverse.rs:2:1
  |
2 | / impl<T, U> From<T> for U
3 | | where
4 | |     T: Into<U>,
  | |_______________^
  |
  = note: ...which immediately requires computing whether impls specialize one another again
note: cycle used when building specialization graph of trait `core::convert::From`
 --> /rustc/ded5c06cf21d2b93bffd5d884aa6e96934ee4234/library/core/src/convert/mod.rs:587:1
  = note: see https://rustc-dev-guide.rust-lang.org/overview.html#queries and https://rustc-dev-guide.rust-lang.org/query.html for more information

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0391`.
(exit 1)
```

- ★★ **E0391 — `cycle detected`.** 고아 규칙(E0210 류)보다 먼저 **순환 탐지**가 걸렸다 —
  rustc 가 「이 `From` 구현이 std 의 것과 겹치나」를 계산하려다 **`Into` 를 보고, 그 `Into` 가 다시 `From` 을 보는** 고리에 빠졌다.
  **한 방향만 둔 것은 선택이 아니라 필수**라는 것을 컴파일러가 순환으로 말해 준다.
  ★ 어느 진단이 **먼저** 나오나(순환 대 고아 규칙)는 **구현 세부**다 — 판정의 근거로 쓰는 것은 「**이 `impl` 은 성립하지 않는다**」까지다.
- **785행 — `impl<T> From<T> for T`** — (1)의 21행 `report(Fahrenheit(1.0))` 이 된 이유.
- ★★ **827행 — `impl<T, U> TryFrom<U> for T where U: Into<T>`**, `type Error = Infallible` — (2)의 뜻밖의 `try_from`.
  조건이 `From` 이 아니라 **`Into`** 라서, `From` 을 쓰면 `Into` 를 거쳐 **이중으로** 도달하고, `Into` 만 써도 도달한다.
- ★ 속성 줄의 **`since = "1.0.0"`·`since = "1.34.0"`** 이 머리말의 버전 근거다.
  ★ `const`·`[const]` 는 **불안정 기능(`const_convert`)의 표식**이다(766행 `rustc_const_unstable`) — 안정 판 사용자 코드에는 안 쓴다.

### (4) ★★ `?` 는 `From` 을 부른다 — `Into` 만으로는 못 돈다

**언제 쓰나** — [**22번 주제**](../22-result-question-mark-and-from/)의 `?` 로 오류를 올릴 때. **변환은 반드시 `From` 으로 쓴다.**

```rust
// r29_qmark.rs
// ? 는 From 을 부른다 — Into 만 있으면
use std::num::ParseIntError;

#[derive(Debug)]
struct PortError(String);

impl Into<PortError> for ParseIntError {
    fn into(self) -> PortError {
        PortError(self.to_string())
    }
}

fn port(raw: &str) -> Result<u16, PortError> {
    let n = raw.parse::<u16>()?;
    Ok(n)
}

fn main() {
    println!("{:?}", port("80"));
}
```

```text
===== rustc --edition 2021 r29_qmark.rs =====
error[E0277]: `?` couldn't convert the error to `PortError`
  --> r29_qmark.rs:14:31
   |
13 | fn port(raw: &str) -> Result<u16, PortError> {
   |                       ---------------------- expected `PortError` because of this
14 |     let n = raw.parse::<u16>()?;
   |                 --------------^ the trait `From<ParseIntError>` is not implemented for `PortError`
   |                 |
   |                 this can't be annotated with `?` because it has type `Result<_, ParseIntError>`
   |
note: `PortError` needs to implement `From<ParseIntError>`
  --> r29_qmark.rs:5:1
   |
 5 | struct PortError(String);
   | ^^^^^^^^^^^^^^^^
   = note: the question mark operation (`?`) implicitly performs a conversion on the error value using the `From` trait

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0277`.
(exit 1)
```

- ★★★ **7행에 `Into<PortError> for ParseIntError` 가 있는데도 E0277 이다.**
  진단의 마지막 `= note:` 가 이유를 그대로 말한다 — 「**the question mark operation (`?`) implicitly performs a conversion on the error value using the `From` trait**」.
  `?` 는 `Into::into` 가 아니라 **`From::from`** 을 부른다.
- ★ 이 `impl` 자체는 **고아 규칙에 안 걸렸다** — `Into` 도 `ParseIntError` 도 남의 것이지만 **`PortError` 가 내 것**이라
  통과한다([**26번 주제**](../26-orphan-rule-and-newtype/)). **통과한 것이 더 나쁘다** — 쓸모없는 구현이 조용히 남는다.
- ★ 22번 (3)의 E0277 과 **번호·note 가 같다** — 거기는 변환 impl 이 **아예 없었고**, 여기는 **반대 방향으로 있었다.** 컴파일러에게는 둘이 같다.

**같은 변환을 `From` 으로 쓰면.**

```rust
// r29_qmark_from.rs
// 같은 변환을 From 쪽으로 쓰면 — ? 가 돈다
use std::num::ParseIntError;

struct PortError(String);

impl From<ParseIntError> for PortError {
    fn from(e: ParseIntError) -> PortError {
        PortError(e.to_string())
    }
}

fn port(raw: &str) -> Result<u16, PortError> {
    let n = raw.parse::<u16>()?; // ★ 여기서 From::from 이 불린다
    Ok(n)
}

fn main() {
    for raw in ["80", "팔공"] {
        match port(raw) {
            Ok(n) => println!("Ok  {}", n),
            Err(PortError(msg)) => println!("Err {}", msg),
        }
    }
    let e: PortError = "x".parse::<u16>().unwrap_err().into(); // ★ Into 는 공짜로 생겼다
    println!("into() {}", e.0);
}
```

```text
===== rustc --edition 2021 r29_qmark_from.rs =====
(exit 0)
===== ./r29_qmark_from =====
Ok  80
Err invalid digit found in string
into() invalid digit found in string
(exit 0)
```

- `From` 으로 바꾸자 13행의 `?` 가 돌고, 24행의 **`into()` 도 공짜로 생겼다** — (1)의 화살표 그대로다.
- ★★ **Go 와 대비** — Go 갈래 [**24번**](../../../go/syntax/24-error-wrapping-and-errors-is-as-join/)은 `fmt.Errorf("…%w", err)` 로
  **원래 오류를 안에 품은 채** 사슬을 만들고, `errors.Is`/`As` 가 **런타임에 사슬을 걸어 내려가며** 찾는다.
  Rust 의 `?` 는 **컴파일 때 정해진 `From::from` 한 번으로 타입을 바꾼다** — 이 예의 `PortError(String)` 처럼 **원래 오류를 버릴 수도 있다.**
  원인을 남기려면 **필드로 품고 `source()` 를 이어야** 한다([**24번 주제**](../24-error-type-design/)).
  「**어디서 바뀌나**(컴파일 대 런타임)」와 「**원인을 누가 붙들고 있나**(언어 대 내 타입)」가 두 언어를 가르는 축이다.

### (5) ★★ `From` 은 무손실만 — `u64 → u32` 에는 없다

**언제 쓰나** — 숫자 폭을 바꿀 때. **넓히면 `From`, 좁히면 `TryFrom`, `as` 는 알고 쓸 때만.**

```rust
// r29_narrow.rs
// 무손실만 From 이다 — u64 에서 u32 로
fn main() {
    let big: u64 = 5_000_000_000;
    let a = u32::from(big);
    let n: u32 = 7;
    let b = usize::from(n);
    println!("{} {}", a, b);
}
```

```text
===== rustc --edition 2021 r29_narrow.rs =====
error[E0277]: the trait bound `u32: From<u64>` is not satisfied
 --> r29_narrow.rs:4:13
  |
4 |     let a = u32::from(big);
  |             ^^^ the trait `From<u64>` is not implemented for `u32`
  |
  = help: the following other types implement trait `From<T>`:
            `u32` implements `From<Char>`
            `u32` implements `From<Ipv4Addr>`
            `u32` implements `From<bool>`
            `u32` implements `From<char>`
            `u32` implements `From<u16>`
            `u32` implements `From<u8>`

error[E0277]: the trait bound `usize: From<u32>` is not satisfied
 --> r29_narrow.rs:6:13
  |
6 |     let b = usize::from(n);
  |             ^^^^^ the trait `From<u32>` is not implemented for `usize`
  |
  = help: the following other types implement trait `From<T>`:
            `usize` implements `From<bool>`
            `usize` implements `From<std::ptr::Alignment>`
            `usize` implements `From<u16>`
            `usize` implements `From<u8>`

error: aborting due to 2 previous errors

For more information about this error, try `rustc --explain E0277`.
(exit 1)
```

- ★★ **`u32: From<u64>` 가 없다** — `help:` 의 후보 목록이 곧 증거다. `u32` 가 받는 정수는 **`u8`·`u16` 뿐**이다(더 좁은 것).
  `From` 의 문서 계약이 「**무손실이어야 한다**」이므로, 큰 값이 안 담기는 변환에는 std 가 **구현을 안 준다.**
- ★★★ **더 뜻밖인 것 — `usize: From<u32>` 도 없다.** 이 머신은 64비트라 `u32` 가 **언제나 담기는데도** 없다.
  `usize` 는 **플랫폼마다 폭이 다르고**(16비트 타깃이 있다), `From` 의 구현은 **타깃에 따라 있다 없다 하지 않도록** 가장 좁은 플랫폼 기준으로 잡혀 있다.
  (목록의 `From<u16>`·`From<u8>` 이 그 기준이다. **이 이유는 std 목록에서 추론한 것**이다 — 16비트 타깃으로는 못 던졌다.
  ★ **「못 잰 것」의 근거** — 이 머신에 설치된 표준 라이브러리 타깃은 하나뿐이다.)

```text
===== rustup target list --installed =====
x86_64-unknown-linux-gnu
(exit 0)
```
- ★ 후보 중 `` `u32` implements `From<Char>` `` 의 `Char` 는 **불안정 기능 `core::ascii::Char`** 다 — 목록은 **안정·불안정을 가리지 않고** 보여 준다.

```rust
// r29_tryfrom.rs
// as 는 자르고 · TryFrom 은 묻고 · From 은 넓힌다
use std::convert::Infallible;

fn main() {
    let big: u64 = 5_000_000_000;
    println!("as u32          {}", big as u32);
    println!("u32::try_from   {:?}", u32::try_from(big));
    println!("u32::try_from 7 {:?}", u32::try_from(7_u64));
    println!("u64::from(7u32) {}", u64::from(7_u32));
    println!("usize try 7u32  {:?}", usize::try_from(7_u32));

    // ★ From 이 있으면 TryFrom 도 생긴다 — 실패할 수 없는 쪽으로
    let r: Result<u64, Infallible> = u64::try_from(7_u32);
    println!("넓히는 try_from {:?}", r);
}
```

```text
===== rustc --edition 2021 r29_tryfrom.rs =====
(exit 0)
===== ./r29_tryfrom =====
as u32          705032704
u32::try_from   Err(TryFromIntError(()))
u32::try_from 7 Ok(7)
u64::from(7u32) 7
usize try 7u32  Ok(7)
넓히는 try_from Ok(7)
(exit 0)
```

- ★★ **`as` 는 조용히 잘랐다** — `5_000_000_000` 이 **`705032704`** 가 됐다. 에러도 경고도 없다([**03번 주제**](../03-primitive-types-and-integer-overflow/) (4)가 정본).
- **`u32::try_from(big)` 은 `Err(TryFromIntError(()))`** — 못 담는다는 것을 **값으로** 알려 준다. 담기면 `Ok(7)`.
- ★ **`usize::try_from(7_u32)` 는 된다** — `From` 이 없는 자리를 `TryFrom` 이 메운다. 64비트에서는 **언제나 `Ok`** 일 테지만 **타입은 실패를 가정한다.**
- ★ 마지막 줄 — **`u64::try_from(7_u32)` 가 `Result<u64, Infallible>`** 이다. `From<u32> for u64` 가 있으므로 (3)의 넷째 포괄 구현이 걸렸다.

**그럼 `From<u64> for u32` 를 내가 만들면.**

```rust
// r29_orphan.rs
// 그럼 u64 → u32 From 을 내가 만들면
impl From<u64> for u32 {
    fn from(v: u64) -> u32 {
        v as u32
    }
}

fn main() {
    println!("{}", u32::from(5_u64));
}
```

```text
===== rustc --edition 2021 r29_orphan.rs =====
error[E0117]: only traits defined in the current crate can be implemented for primitive types
 --> r29_orphan.rs:2:1
  |
2 | impl From<u64> for u32 {
  | ^^^^^---------^^^^^---
  |      |             |
  |      |             `u32` is not defined in the current crate
  |      `u64` is not defined in the current crate
  |
  = note: impl doesn't have any local type before any uncovered type parameters
  = note: for more information see https://doc.rust-lang.org/reference/items/implementations.html#orphan-rules
  = note: define and implement a trait or new type instead

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0117`.
(exit 1)
```

- ★ **E0117** — `From`·`u64`·`u32` **셋 다 남의 것**이라 막힌다. 제목이 「**…for primitive types**」로 26번 (1)의 판과 **한 낱말 다르다**(대상이 기본 타입이라서).
  규칙의 정본은 [**26번 주제**](../26-orphan-rule-and-newtype/) (1)이다 — 여기는 「**없는 `From` 을 내가 채울 수는 없다**」만 확인한다.
- ★ 채울 수 있었다면 **std 의 「무손실」 약속이 남의 크레이트에서 깨졌을 것**이다. 고아 규칙이 그 약속을 지켜 준다.

### (6) `TryFrom` 을 직접 쓴다 — `Error` 는 연관 타입이다

**언제 쓰나** — 검증을 거쳐야 만들어지는 타입(범위가 있는 숫자·형식이 있는 문자열).

```rust
// r29_tryfrom_impl.rs
// TryFrom 을 직접 구현한다 — Error 는 연관 타입이다
#[derive(Debug)]
struct Percent(u8);

#[derive(Debug)]
enum PercentError {
    TooBig,
    Negative,
}

impl TryFrom<i32> for Percent {
    type Error = PercentError;
    fn try_from(v: i32) -> Result<Percent, PercentError> {
        if v < 0 {
            Err(PercentError::Negative)
        } else if v > 100 {
            Err(PercentError::TooBig)
        } else {
            Ok(Percent(v as u8))
        }
    }
}

fn main() {
    for v in [42, 150, -3] {
        let p: Result<Percent, _> = v.try_into(); // ★ TryInto 도 따라 생긴다
        match p {
            Ok(Percent(n)) => println!("{:>4} -> Ok {}%", v, n),
            Err(e) => println!("{:>4} -> Err {:?}", v, e),
        }
    }
}
```

```text
===== rustc --edition 2021 r29_tryfrom_impl.rs =====
(exit 0)
===== ./r29_tryfrom_impl =====
  42 -> Ok 42%
 150 -> Err TooBig
  -3 -> Err Negative
(exit 0)
```

- **12행 `type Error = PercentError;`** — 실패의 모양을 **구현마다 하나** 고른다. 25번이 말한 **연관 타입**의 전형이다.
- ★ **왜 제네릭 파라미터가 아닌가** — `TryFrom<i32> for Percent` 하나에 **실패 타입이 둘일 이유가 없다.**
  입력(`i32`)은 여러 개일 수 있어 **제네릭 파라미터**, 실패 모양은 입력마다 하나라 **연관 타입**이다 —
  [**25번 주제**](../25-traits-definition-impl-default-methods-and-associated-types/)의 판정 「**한 타입에 몇 번**」이 여기서 한 트레이트 안에 **둘 다** 나온다.
- ★ **26행의 `try_into()` 는 내가 안 썼다** — (3)의 셋째 포괄 구현(`TryInto<U> for T where U: TryFrom<T>`)이다.

**같은 소스를 에디션 2015 로 던지면.**

```text
===== rustc --edition 2015 r29_tryfrom_impl.rs =====
error[E0405]: cannot find trait `TryFrom` in this scope
  --> r29_tryfrom_impl.rs:11:6
   |
11 | impl TryFrom<i32> for Percent {
   |      ^^^^^^^ not found in this scope
   |
   = note: 'std::convert::TryFrom' is included in the prelude starting in Edition 2021
help: consider importing this trait
   |
 2 + use std::convert::TryFrom;
   |

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0405`.
(exit 1)
```

- ★ **E0405** — `TryFrom` 이라는 **이름을 못 찾는다.** `note:` 가 이유를 직접 말한다 — 「**included in the prelude starting in Edition 2021**」.
  트레이트가 없어진 것이 아니라 **프렐류드에 없을 뿐**이라 `use std::convert::TryFrom;` 한 줄이면 된다(`help:`).
  ★ 머리말의 「`--edition` 을 빼면 다른 언어」가 **이 주제에서는 이 한 줄**로 나타난다.

### (7) `AsRef<str>` — 빌려서 보기만 한다

**언제 쓰나** — 인자를 **읽기만** 하는데 `String`·`&str`·`Box<str>` 을 다 받고 싶을 때.

```rust
// r29_asref.rs
// AsRef<str> — 빌려서 보기만 한다
use std::path::Path;

fn shout(s: impl AsRef<str>) -> String {
    s.as_ref().to_uppercase()
}

fn ext(p: impl AsRef<Path>) -> Option<String> {
    p.as_ref().extension().map(|e| e.to_string_lossy().into_owned())
}

fn main() {
    let owned = String::from("abc");
    println!("&str      {}", shout("abc"));
    println!("&String   {}", shout(&owned));
    println!("String    {}", shout(owned)); // ★ 소유권째 넘겨도 된다
    println!("Box<str>  {}", shout(Box::<str>::from("abc")));
    println!("Path 쪽   {:?} {:?}", ext("a/b.rs"), ext(String::from("c.toml")));
}
```

```text
===== rustc --edition 2021 r29_asref.rs =====
(exit 0)
===== ./r29_asref =====
&str      ABC
&String   ABC
String    ABC
Box<str>  ABC
Path 쪽   Some("rs") Some("toml")
(exit 0)
```

- **`impl AsRef<str>` 하나로 네 가지가 들어왔다** — `&str` · `&String` · `String` · `Box<str>`.
  ★ **16행은 `String` 을 소유권째 넘겼다** — `shout` 는 그것을 **빌려 보고 버린다.** 호출자는 `owned` 를 잃는다.
  읽기만 할 거면 **`&str` 인자 하나로도 셋은 받는다**([**14번 주제**](../14-string-vs-str/) (3)) — `AsRef` 가 더 받는 것은 **소유 값**이다.
- ★ `AsRef<Path>` 는 **`&str` 과 `String` 을 경로로** 받는다 — std 의 파일 API(`File::open` 등)가 이 모양이다.
- ★ `AsRef` 는 「**싸고 실패하지 않는 참조 변환**」이다. **새 값을 만들지 않는다** — 만들어야 하면 `From`/`Into` 다.

### (8) ★★ `Borrow` — `AsRef` 와 시그니처가 같은데 계약이 다르다

**언제 쓰나** — 컬렉션 조회. `HashMap<String, V>` 을 **`&str` 로** 찾을 수 있는 것이 이것 덕분이다.

```rust
// r29_borrow.rs
// Borrow — HashMap<String, _> 을 &str 로 찾는 이유
use std::borrow::Borrow;
use std::collections::HashMap;
use std::collections::hash_map::DefaultHasher;
use std::hash::{BuildHasherDefault, Hash, Hasher};

type Map<K> = HashMap<K, i32, BuildHasherDefault<DefaultHasher>>;

fn hash_of<T: Hash + ?Sized>(x: &T) -> u64 {
    let mut h = DefaultHasher::new();
    x.hash(&mut h);
    h.finish()
}

// ★ Borrow<str> 을 달았는데 Hash 가 str 과 다르다
#[derive(PartialEq, Eq)]
struct Tagged(String);

impl Hash for Tagged {
    fn hash<H: Hasher>(&self, state: &mut H) {
        "tag".hash(state); // ★ 계약 위반 — str 의 해시와 달라진다
        self.0.hash(state);
    }
}

impl Borrow<str> for Tagged {
    fn borrow(&self) -> &str {
        &self.0
    }
}

fn main() {
    let mut m: Map<String> = Map::default();
    m.insert(String::from("kim"), 1);
    println!("String 키를 &str 로  {:?}", m.get("kim"));
    println!("해시 같나(String/str) {}", hash_of(&String::from("kim")) == hash_of("kim"));

    let mut t: Map<Tagged> = Map::default();
    t.insert(Tagged(String::from("kim")), 1);
    println!("Tagged 키를 &str 로  {:?}", t.get("kim"));
    println!("해시 같나(Tagged/str) {}", hash_of(&Tagged(String::from("kim"))) == hash_of("kim"));
    println!("Tagged 로 찾으면     {:?}", t.get(&Tagged(String::from("kim"))));
}
```

```text
===== rustc --edition 2021 r29_borrow.rs =====
(exit 0)
===== ./r29_borrow =====
String 키를 &str 로  Some(1)
해시 같나(String/str) true
Tagged 키를 &str 로  None
해시 같나(Tagged/str) false
Tagged 로 찾으면     Some(1)
(exit 0)
```

- **첫 줄 — `String` 키를 `&str` 로 찾았다**(`Some(1)`). `HashMap::get` 은 `K: Borrow<Q>` 를 요구하고, std 가 `String: Borrow<str>` 을 준다.
  ★ 그리고 **`String` 과 `str` 의 해시가 같다**(`true`) — 그래야 **같은 칸**을 뒤진다.
- ★★★ **셋째 줄 — `Tagged` 키를 `&str` 로 찾으니 `None`.** `Tagged` 는 `Borrow<str>` 을 **달았지만**
  21행에서 해시에 `"tag"` 를 더 섞어 **`str` 과 다른 해시**를 낸다(넷째 줄 `false`). 그래서 **다른 칸을 뒤져 못 찾는다.**
  **컴파일은 통과했다** — 이것이 28번이 말한 **논리 오류**의 `Borrow` 판이다.
- ★★ **`Borrow` 의 계약**(std 문서) — **빌린 쪽과 원래 쪽의 `Eq`·`Ord`·`Hash` 가 같아야 한다.**
  `AsRef` 에는 이 계약이 **없다.** 그래서 **조회에 쓸 수 있는 것은 `Borrow` 뿐**이다.
- 다섯째 줄 — **`Tagged` 로 찾으면 찾는다**(`Some(1)`). 값은 들어 있다. **빌린 모양으로 찾을 때만 사라진다.**

**그럼 `AsRef` 만 달면 조회가 되나.**

```rust
// r29_asref_get.rs
// HashMap::get 은 AsRef 가 아니라 Borrow 를 요구한다
use std::collections::HashMap;

struct Name(String);

impl AsRef<str> for Name {
    fn as_ref(&self) -> &str {
        &self.0
    }
}

impl PartialEq for Name {
    fn eq(&self, o: &Self) -> bool {
        self.0 == o.0
    }
}
impl Eq for Name {}
impl std::hash::Hash for Name {
    fn hash<H: std::hash::Hasher>(&self, h: &mut H) {
        self.0.hash(h)
    }
}

fn main() {
    let mut m: HashMap<Name, i32> = HashMap::new();
    m.insert(Name(String::from("kim")), 1);
    println!("{:?}", m.get("kim"));
}
```

```text
===== rustc --edition 2021 r29_asref_get.rs =====
error[E0308]: mismatched types
  --> r29_asref_get.rs:27:28
   |
27 |     println!("{:?}", m.get("kim"));
   |                        --- ^^^^^ expected `&Name`, found `&str`
   |                        |
   |                        arguments to this method are incorrect
   |
   = note: expected reference `&Name`
              found reference `&'static str`
note: method defined here
  --> /rustc/ded5c06cf21d2b93bffd5d884aa6e96934ee4234/library/std/src/collections/hash/map.rs:909:12

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0308`.
(exit 1)
```

- ★★ **E0308** — `` expected `&Name`, found `&str` ``. `Name` 은 `AsRef<str>` 을 가졌지만 `HashMap::get` 은 **그것을 보지 않는다.**
  `Name` 이 가진 `Borrow` 는 **반사 구현 `Borrow<Name>` 하나뿐**이라 `Q = Name` 으로 정해졌고, 그래서 `&Name` 을 기대했다.
  ★ **(2)의 E0308 과 같은 모양**이다 — 「있는 구현 중에서 고르다가 반사 구현만 남아 타입 불일치로 끝난다」.

### (9) `impl Into<String>` 인자 — 부르는 쪽이 편해진다

**언제 쓰나** — **값을 저장하는** 생성자·설정 함수. 읽기만 하면 `&str` 이나 `AsRef<str>` 이다.

```rust
// r29_into_arg.rs
// impl Into<String> 인자 — 부르는 쪽이 편해진다
struct User {
    name: String,
}

impl User {
    fn new(name: impl Into<String>) -> User {
        User { name: name.into() }
    }
}

fn main() {
    let owned = String::from("lee");
    let users = [
        User::new("kim"),          // &str   → 복사해 새 String
        User::new(owned),          // String → 그대로 옮긴다(복사 없음)
        User::new('p'),            // char   → String: From<char>
        User::new(&String::from("choi")), // &String
    ];
    for u in &users {
        println!("{}", u.name);
    }
}
```

```text
===== rustc --edition 2021 r29_into_arg.rs =====
(exit 0)
===== ./r29_into_arg =====
kim
lee
p
choi
(exit 0)
```

- **네 가지가 한 시그니처로 들어왔다** — `&str` · `String` · `char` · `&String`. 전부 std 의 `From<…> for String` 이 있다.
- ★★ **득** — ① 호출자가 `.to_string()` 을 안 쓴다 ② ★ **`String` 을 넘기면 옮기기만 하고 복사하지 않는다**(16행) —
  `&str` 인자로 받아 안에서 `to_string()` 하면 **이미 가진 `String` 도 한 번 더 복사**한다. 이 차이가 핵심 득이다.
- ★★ **실** — ① **`new` 가 제네릭이 된다** — 인자 타입마다 **따로 찍힐 수 있다**(단형화). 31번의 창(심볼 표)으로 셌다:

```text
===== rustc --edition 2021 -C opt-level=0 -C symbol-mangling-version=v0 r29_into_arg.rs =====
(exit 0)
===== nm -C r29_into_arg | awk '/User>::new/ {$1=""; print substr($0, 2)}' =====
t <r29_into_arg::User>::new::<alloc::string::String>
t <r29_into_arg::User>::new::<&alloc::string::String>
t <r29_into_arg::User>::new::<&str>
t <r29_into_arg::User>::new::<char>
(exit 0)
```

```text
===== rustc --edition 2021 -C opt-level=3 -C symbol-mangling-version=v0 r29_into_arg.rs =====
(exit 0)
===== nm -C r29_into_arg | awk '/User>::new/ {$1=""; print substr($0, 2)}' =====
(exit 0)
```

  **`opt-level=0` 에서 네 벌**(`<String>`·`<&String>`·`<&str>`·`<char>`), **`opt-level=3` 에서 0 벌**(전부 `main` 에 녹았다 — awk 가 한 줄도 못 찾았고 `exit 0`).
  **몇 벌인가는 판이 정한다** — 판 격자와 그 해석은 [**31번 주제**](../31-generics-trait-bounds-where-and-monomorphization/) (8)이 정본이다.
  ② **타입 추론이 한 칸 흐려진다** — `User::new(x.into())` 처럼 **두 번 `into`** 하면 중간 타입을 못 정한다.
  ③ **문서에서 받는 타입이 안 보인다** — `impl Into<String>` 만 보고는 `char` 가 되는지 모른다.
- ★ 관용 — **표준 라이브러리 자신은 드물게 쓴다**(`String::from` 처럼 구체 타입을 받는 쪽이 많다). 판단은 「**저장하나, 읽기만 하나**」 하나다.

### (10) 대비 — C# 의 사용자 정의 암묵 변환

**언제 쓰나** — 「Rust 에는 왜 `implicit` 이 없나」를 가를 때. C# 갈래에 이 번호의 폴더가 없어 **직접 던졌다.**

```bash
# r29_csc.sh
# C# 한 파일을 csc 로 컴파일하고 실행한다 — 이 머신의 .NET SDK 10.0.401 에 든 Roslyn 을 직접 부른다
set -u -o pipefail
export PATH="$HOME/.local/bin:$PATH" DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1 DOTNET_CLI_UI_LANGUAGE=en
home="$(dirname "$(readlink -f "$(command -v dotnet)")")"
ls "$home"/packs/Microsoft.NETCore.App.Ref/10.0.12/ref/net10.0/*.dll | sed 's/^/-r:/' > refs.rsp
echo '{"runtimeOptions":{"tfm":"net10.0","framework":{"name":"Microsoft.NETCore.App","version":"10.0.0"}}}' > "${1%.cs}.runtimeconfig.json"
dotnet --version
dotnet exec "$home/sdk/10.0.401/Roslyn/bincore/csc.dll" -nologo -nostdlib -noconfig @refs.rsp \
  -preferreduilang:en-US -langversion:latest -out:"${1%.cs}.dll" "$1" || exit $?
dotnet exec "${1%.cs}.dll"
```

```csharp
// r29_implicit.cs
// C# — 사용자 정의 암묵 변환은 대입 한 줄에서 보이지 않게 불린다
using System;

struct Celsius {
    public double V;
    public Celsius(double v) { V = v; }
}

struct Fahrenheit {
    public double V;
    public Fahrenheit(double v) { V = v; }
    public static implicit operator Fahrenheit(Celsius c) {
        Console.WriteLine("  (implicit 변환이 불렸다)");
        return new Fahrenheit(c.V * 1.8 + 32.0);
    }
}

static class Program {
    static void Report(Fahrenheit f) => Console.WriteLine($"report {f.V}");
    static void Main() {
        Fahrenheit f = new Celsius(100.0); // ★ 변환 호출이 글자로 안 보인다
        Console.WriteLine($"f = {f.V}");
        Report(new Celsius(0.0));
    }
}
```

```text
===== bash r29_csc.sh r29_implicit.cs =====
10.0.401
  (implicit 변환이 불렸다)
f = 212
  (implicit 변환이 불렸다)
report 32
(exit 0)
```

- ★★ **대입 한 줄 `Fahrenheit f = new Celsius(100.0);` 에서 변환이 불렸다** — 소스에는 **변환 호출이 글자로 없는데** 출력에 「`(implicit 변환이 불렸다)`」가 찍혔다. 인자 자리(`Report(new Celsius(0.0))`)도 같다.
- ★★ **Rust 에는 사용자 정의 암묵 변환이 없다** — (1)의 `c.into()`·`Fahrenheit::from(c)` 처럼 **글자로 적어야** 불린다.
  Rust 가 몰래 끼우는 것은 **참조의 역참조 강제**뿐이다([**30번 주제**](../30-operator-overloading-std-ops-index-and-deref/) (7) · 목록의 **43번 주제**).
- ★ 첫 줄 `10.0.401` 은 `r29_csc.sh` 가 찍은 **.NET SDK 판**이다(규칙 26 — 도구 판을 블록으로).

## 문법 — 형태와 규칙

```text
   형태 — 무엇을 쓰나

   impl From<A> for B {                     ← ★ 이것만 쓴다. Into·TryFrom·TryInto 는 std 가 세운다
       fn from(a: A) -> B { … }
   }
   impl TryFrom<A> for B {                  ← 실패할 수 있으면
       type Error = MyError;                  ← 실패 모양은 연관 타입
       fn try_from(a: A) -> Result<B, MyError> { … }
   }
   impl AsRef<str> for B { fn as_ref(&self) -> &str { … } }     ← 싸게 빌려 보기
   impl Borrow<str> for B { fn borrow(&self) -> &str { … } }    ← + Hash·Eq 가 str 과 같다는 약속

   부르는 쪽
   B::from(a)          a.into()            ← into 는 목적지 타입을 적어 줘야 한다
   B::try_from(a)?     a.try_into()?
   fn f(s: impl AsRef<str>)   fn g(s: impl Into<String>)


   금지 사례 — 던져서 받은 것

   impl Into<B> for A  만 두고  B::from(a)         ✘ E0308  (반사 From 만 남는다)
                                 U: From<T> 경계    ✘ E0277
                                 ? 연산자            ✘ E0277  "using the From trait"
   u32::from(u64) · usize::from(u32)               ✘ E0277  From 이 없다(무손실 아님 · 플랫폼)
   impl From<u64> for u32                          ✘ E0117  셋 다 남의 것
   AsRef 만 있는 키를 &str 로 HashMap::get          ✘ E0308  get 은 Borrow 를 본다
```

**규칙 불릿.**

- ★★★ **`From` 을 구현한다** — `Into`·`TryFrom`·`TryInto` 가 포괄 구현으로 생긴다. **`Into` 를 직접 쓰는 자리는 거의 없다**((1)·(3)).
- ★★ **경계는 `Into` 로 건다** — `T: Into<U>` 는 `From` 을 쓴 타입과 `Into` 만 쓴 타입을 다 받는다((2)).
- ★★ **`?` 는 `From::from` 을 부른다** — `Into` 만 있으면 E0277((4)).
- ★★ **`From` 은 무손실·무실패일 때만** — 좁히는 변환은 `TryFrom`, 비트를 그대로 읽는 것은 `as`((5)).
- **`TryFrom` 의 실패 모양은 연관 타입 `Error`** 다((6)).
- ★★ **`AsRef` 는 싸게 빌려 보기, `Borrow` 는 거기에 `Hash`·`Eq`·`Ord` 가 같다는 계약** — 조회는 `Borrow` 만 쓴다((7)·(8)).
- ★ **`impl Into<String>` 인자는 「저장할 때」** — 득은 이동, 실은 단형화와 추론((9)).

## 어디서 틀리나

### 1. ★★★ 「`Into` 를 구현하면 `From` 도 되겠지」

**안 된다**((2)). 포괄 구현은 **`From` → `Into` 한 방향**뿐이다((3)의 767행).
증상은 한 가지로 안 온다 — `B::from` 은 **E0308**, 제네릭 경계는 **E0277**, `?` 는 **E0277 + `using the From trait`**.
**번호가 달라서 같은 결함인 줄 모르기 쉽다.**

### 2. ★★ 「경계도 `From` 으로 걸어야 짝이 맞는다」

**거꾸로다**((2)). **구현은 `From`, 경계는 `Into`.** `U: From<T>` 경계는 `Into` 만 가진 타입을 막는다.

### 3. ★★ 「`Into` 만 구현하면 아무것도 안 생긴다」

**`TryFrom` 은 생긴다**((2)·(3)의 827행). 조건이 `Into` 에 걸려 있기 때문이다.
그래서 「`Into` 만 쓰면 `From` 이 없다」는 맞지만 「**`Into` 만 쓰면 공짜가 하나도 없다**」는 틀리다.

### 4. ★★ 「`usize` 는 64비트니 `u32` 에서 `From` 이 되겠지」

**안 된다**((5)). `From` 은 **타깃에 따라 있다 없다 하지 않는다.** `usize::try_from` 을 쓴다.

### 5. ★★ 「`as` 와 `from` 은 같은 변환의 두 표기다」

**다르다**((5)). `as` 는 **안 담기면 조용히 자르고**, `From` 은 **안 담길 수 있으면 아예 없다.**
`from` 이 컴파일되면 **그 변환은 실패할 수 없다** — 그 보증이 `From` 의 값이다.

### 6. ★★ 「`AsRef<str>` 을 달았으니 `HashMap` 에서 `&str` 로 찾아지겠지」

**E0308 이다**((8)). 조회는 **`Borrow`** 를 본다. 그리고 `Borrow` 를 달 때는 **해시가 빌린 쪽과 같아야 한다** — 다르면 **컴파일은 되고 `None` 이 나온다.**

### 7. ★ 「`impl Into<String>` 이 `&str` 보다 항상 낫다」

**읽기만 하면 `&str` 이 낫다**((9)). `impl Into<String>` 의 득(이동)은 **저장할 때만** 생기고, 실(단형화·추론)은 **언제나** 생긴다.

### 8. ★ 「`?` 가 원인을 품어 준다」

**`From` 이 무엇을 하느냐에 달렸다**((4)). `PortError(e.to_string())` 은 **원래 오류를 버린다.** Go 의 `%w` 처럼 사슬을 남기려면 **필드로 품어야** 한다.

## 구현 세부사항 대 언어 보장

| 항목 | 무엇인가 | 근거 |
|---|---|---|
| `From` → `Into` 포괄 구현, **반대는 없음** | ★ **라이브러리 보장** — std 가 1.0.0 부터 안정으로 둔 `impl` | (3)의 소스 · (2)의 실측 |
| `impl<T> From<T> for T` | ★ **라이브러리 보장** | (1)·(3) |
| `Into` 만으로 `TryFrom` 이 생기는 것 | ★ **라이브러리 보장** — 827행의 조건이 `Into` 다 | (2)·(3) |
| `?` 가 **`From`** 을 부르는 것 | ★ **언어 보장** — Reference 의 `?` 해설(에러 경로가 `From::from`) | (4)의 실측 · 진단 note |
| `From` 이 **무손실**이어야 하는 것 | ★ **문서 계약** — 컴파일러 강제는 **없다**(내 `From` 은 손실이어도 통과한다) | std 문서 |
| `u32: From<u64>`·`usize: From<u32>` 가 **없는** 것 | ★ **이 std 판의 구성** — 목록은 판이 오르면 **늘 수 있다** | (5)의 실측 |
| `Borrow` 의 `Hash`/`Eq`/`Ord` 일치 | ★ **문서 계약** — 어기면 **논리 오류**(UB 아님) | (8)의 실측 |
| 계약을 어겼을 때 `get` 이 **`None`** 인 것 | ★ **이 판의 관찰** — 동작이 규정되지 않는다 | (8)의 실측 |
| (2)의 결함이 **E0308 로 나오는** 것 | ★ **구현 세부** — 추론이 반사 구현을 고른 결과다. 진단은 판마다 바뀔 수 있다 | (2)의 실측 |
| 진단의 `/rustc/ded5c06cf…` 경로와 std 소스 **줄 번호** | ★ **이 판의 값** | (2)·(3) |
| `TryFrom`·`TryInto` 가 **프렐류드**에 있는 것 | ★ **에디션 보장** — 2021 부터 | 이 문서의 소스 전부 |

## 언제 쓰고 언제 안 쓰나

- **`From` 을 쓴다** — 무손실·무실패 변환. 내 타입 둘 사이, 내 오류 타입으로의 래핑.
- **`TryFrom` 을 쓴다** — 검증이 필요한 생성(범위·형식). **생성자 대신 쓰면 `?` 와 잘 맞는다.**
- **`as` 를 쓴다** — **자르는 것이 목적**일 때만(해시 섞기·비트 조작). 좁히기 변환의 기본값으로 쓰지 않는다.
- **`AsRef<T>` 를 쓴다** — 인자를 **읽기만** 하고 여러 모양을 받고 싶을 때(`Path`·`[u8]`·`str`).
- **`Borrow<T>` 를 쓴다** — **조회 키**로 쓰일 타입. 달 때 `Hash`·`Eq` 를 빌린 쪽과 **같게** 쓴다.
- **`impl Into<String>` 을 쓴다** — 값을 **저장하는** 생성자. 공개 API 에서 편의가 코드 크기보다 중요할 때.
- ★ **`Into` 를 직접 구현하지 않는다** — `From` 이 안 되는 자리(고아 규칙)에서만 쓰는데, 그러면 `?` 가 안 된다는 것을 **알고** 쓴다.

## 핵심 문장

- ★★★ **`From` 을 쓰면 `Into`·`TryFrom`·`TryInto` 가 생기고, `Into` 를 써도 `From` 은 끝내 안 생긴다** — 포괄 구현이 한 방향이다((2)·(3)).
- ★★ **그래서 구현은 `From`, 경계는 `Into`** — 같은 화살표의 두 끝이다((2)).
- ★★ **`?` 는 `From` 을 부른다** — 오류 변환은 `From` 으로 쓴다((4)).
- ★★ **`From` 이 컴파일되면 그 변환은 실패할 수 없다** — 그래서 `u64 → u32` 에는 `From` 이 없다((5)).
- ★★ **`Borrow` 는 `AsRef` 에 「같은 해시·같은 동등」이라는 계약을 더한 것**이고, 조회는 그 계약에 기댄다((8)).
- ★ **`impl Into<String>` 의 득은 이동이고 실은 단형화다** — 저장할 때만 쓴다((9)).

## 관련 자료

- [**25번 주제** — 트레이트 정의·구현·연관 타입](../25-traits-definition-impl-default-methods-and-associated-types/) —
  ★ **경계**: 제네릭 파라미터와 연관 타입의 **판정 기준**은 거기, 여기는 **`TryFrom` 한 트레이트에 둘이 함께 나오는 사례**((6)).
- [**22번 주제** — `Result` 와 `?`·`From`](../22-result-question-mark-and-from/) —
  ★ **경계**: `?` 의 **펼침과 조기 반환**은 거기, 여기는 「**`Into` 로는 안 된다**」는 방향 문제만((4)).
- [**26번 주제** — 고아 규칙과 newtype](../26-orphan-rule-and-newtype/) —
  ★ **경계**: E0117 의 **규칙 전문**은 거기, 여기는 `From<u64> for u32` 한 판만((5)).
- [**28번 주제** — 비교·해시 계약](../28-partialeq-eq-partialord-ord-and-hash-contracts/) —
  `Borrow` 의 계약은 28번의 `Hash`/`Eq` 계약을 **빌린 모양까지 넓힌 것**이다((8)). 28번 「더 들어가면」이 여기를 가리켰다.
- [**03번 주제** — 기본 타입·오버플로·`as`](../03-primitive-types-and-integer-overflow/) —
  ★ **경계**: `as` 의 **비트 규칙**(자르기·부호 확장·부동→정수 포화)은 거기, 여기는 `From`/`TryFrom` 과의 **대비**만((5)).
- [**14번 주제** — `String` 대 `&str`](../14-string-vs-str/) — 인자를 `&str` 로 받는 기본 판정. (7)·(9)가 그 위에 선다.
- [**31번 주제** — 제네릭과 트레이트 경계·단형화](../31-generics-trait-bounds-where-and-monomorphization/) — (9)의 「실」을 **센다.**
- [목록의 **39번 주제**](../39-hashmap-vs-btreemap-and-entry-api/) — `HashMap`·`BTreeMap`. `entry` 와 조회 API 의 정본.
- Go 의 오류 래핑 — [`go/syntax/24-error-wrapping-and-errors-is-as-join/`](../../../go/syntax/24-error-wrapping-and-errors-is-as-join/).
  ★ **대비**: Go 는 **런타임 사슬**(`%w` + `errors.Is`/`As`), Rust `?` 는 **컴파일 때 한 번의 `From`**((4)).
- C# 의 `implicit`/`explicit` 변환 연산자 — C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **49번**(폴더 없음). 이 문서 (10)에서 **직접 던졌다.**
- C++ 의 좁히기 — [`cpp/syntax/04-brace-initialization-narrowing-and-initializer-list/`](../../../cpp/syntax/04-brace-initialization-narrowing-and-initializer-list/).
  ★ **대비**: C++ 는 `{}` 초기화에서 **좁히기를 컴파일 에러로** 막고 `()`·`=` 에서는 **허용한다** — 같은 변환이 **문법 모양**에 따라 갈린다.
  Rust 는 **`From` 이 있나 없나**로 한 번에 갈린다(`as` 는 따로 적는 별도 연산자다).

## 용어 풀이

- **변환 트레이트** — 값을 다른 타입으로 바꾸는 능력을 적어 둔 트레이트. `From`·`Into`·`TryFrom`·`TryInto`·`AsRef`·`AsMut`·`Borrow`.
- **포괄 구현(blanket impl)** — 조건을 만족하는 모든 타입에 한 번에 거는 구현. `impl<T, U> Into<U> for T where U: From<T>`.
- **반사 구현(reflexive impl)** — 자기 자신으로의 변환 `impl<T> From<T> for T`. 아무 일도 안 하고 값을 돌려준다.
- **무손실 변환** — 어떤 입력에서도 정보를 잃지 않고 실패하지 않는 변환. `From` 의 문서 계약.
- **`Infallible`** — 값이 하나도 없는 열거형. 「실패할 수 없음」을 타입으로 적는다.
- **`TryFromIntError`** — 정수 좁히기 `try_from` 이 실패할 때의 오류 타입.
- **`AsRef<T>`** — `&self` 에서 `&T` 를 싸게 얻는 변환. 계약은 「싸고 실패하지 않는다」뿐.
- **`Borrow<T>`** — `AsRef` 와 같은 모양에 **`Eq`·`Ord`·`Hash` 가 같다는 계약**을 더한 것. 컬렉션 조회가 쓴다.
- **프렐류드(prelude)** — `use` 없이 들어오는 이름 묶음. 2021 부터 `TryFrom`·`TryInto` 가 있다.
- **단형화(monomorphization)** — 제네릭 함수를 타입마다 따로 찍어 내는 것. 31번의 본체.

## 더 들어가면

- **`AsMut`** — `AsRef` 의 가변 판. `&mut self` 에서 `&mut T` 를 얻는다.
- **`ToOwned`·`Cow`** — `Borrow` 의 짝. `&str` 에서 `String` 을 만드는 쪽이 `ToOwned` 이고, 둘을 한 타입에 담는 것이 `Cow<'_, str>` 이다.
- **`FromStr` 과 `parse`** — 문자열에서 만드는 변환은 `From<&str>` 이 아니라 **`FromStr`** 이다(실패가 있으므로). `"80".parse::<u16>()` 이 그것이다.
- **`From<!> for T`** — (3)의 소스 페이지에 **「아직 없지만 자리를 예약해 둔」 구현**이 있다(`rustc_reservation_impl`). `!` 타입이 안정되면 들어올 자리다.
- **`impl Into<T>` 대신 제네릭** — `fn new<S: Into<String>>(s: S)` 는 같은 뜻이고 **터보피시로 타입을 찍을 수 있다**([**32번 주제**](../32-impl-trait-argument-return-position-and-2024-capture/)의 (1)).
- **1.41 이전의 `Into`** — std 의 `Into` 문서는 「1.41 전에는 **남의 타입으로 가는 변환**을 고아 규칙 때문에 `From` 으로 못 써서 `Into` 를 직접 썼다」고 적는다. 지금 `Into` 를 직접 쓴 코드를 보면 대개 그 시절의 흔적이다.
