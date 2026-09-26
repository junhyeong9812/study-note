# rust/syntax/29 — 변환 트레이트 `From`/`Into`/`TryFrom`/`AsRef`/`Borrow` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서\
> **`rustc --edition 2021 <파일>.rs`** 로 실제로 돌려 받은 것이다(에디션 2015 판 하나는 배너에 그렇게 적었다).\
> ★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
> ★★ 블록 첫 줄 `===== 소스: <파일>.rs =====` 아래가 **컴파일한 소스 전문**이고, **진단의 줄 번호는 그 파일 기준**이다.\
> ★ 표준 출력과 표준 오류는 **섞지 않았다** — rustc 의 진단은 표준 오류, 프로그램의 `println!` 은 표준 출력이다.\
> ★★ **외부 크레이트를 하나도 쓰지 않았다**(네트워크 없음).\
> ★ 해시값은 **한 번도 안 찍었다** — 「같은가 다른가」만 근거로 쓴다(5번 답).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ `From` 하나로 `into()` 가 생기고, 자기 자신으로도 바뀐다

**출력.**

```text
===== 소스: r29_from.rs =====
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
===== rustc --edition 2021 r29_from.rs =====
(exit 0)
===== ./r29_from =====
from()    212
into()    32
  report  -40
  report  1
(exit 0)
```

**왜 그런가.**

- ★★ **`into()` 는 std 의 포괄 구현** `impl<T, U> Into<U> for T where U: From<T>` 에서 왔다.
  5행의 `From<Celsius> for Fahrenheit` 가 그 조건을 채웠으므로 `Celsius: Into<Fahrenheit>` 가 **자동으로** 생겼다.
- ★ 21행은 **반사 구현** `impl<T> From<T> for T` 덕분이다 — 누구나 자기 자신으로 바뀐다. 그래서 `Fahrenheit: Into<Fahrenheit>` 도 있다.
  이 두 `impl` 의 **실제 소스**는 서머리 (3)이 설치된 std 문서에서 뽑아 보였다(767행·785행).
- 18행이 `let f: Fahrenheit` 로 **타입을 적은 이유** — `into()` 는 목적지를 추론에 맡긴다. 안 적으면 목적지를 못 정한다.

### 2. ★★★ 반대 방향은 안 생긴다 — 다만 `try_from` 은 생긴다

**출력 — `Into` 만 쓰고 반대 방향을 부르면.**

```text
===== 소스: r29_into_only.rs =====
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

**출력 — 같은 `Into` 로 `try_from`.**

```text
===== 소스: r29_into_try.rs =====
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
===== rustc --edition 2021 r29_into_try.rs =====
(exit 0)
===== ./r29_into_try =====
try_from Ok 212
(exit 0)
```

**왜 그런가.**

- ★★★ **에러 2건 — E0308(17행) · E0277(18행).** 16행(직접 쓴 방향)은 **에러가 없다.**
- ★★ **번호가 갈리는 이유** — 결함은 같다(「`From<Celsius> for Fahrenheit` 가 없다」).
  - `Fahrenheit::from(x)` 는 **`Fahrenheit` 가 가진 `From` 중에서** 고른다. 가진 것이 **반사 구현 `From<Fahrenheit>` 하나뿐**이라
    rustc 는 인자가 `Fahrenheit` 여야 한다고 추론했고, 그래서 **타입 불일치(E0308)** 로 나왔다.
  - `convert` 는 **경계 `U: From<T>`** 를 검사하므로 **트레이트 미충족(E0277)** 으로 정면에서 말한다.
  - ★ 첫 에러의 `help:` 「**call `Into::into` on this expression**」가 **`Into` 쪽은 있다**는 rustc 의 자백이다.
- ★★ **뒤 소스는 통과한다** — std 의 포괄 구현 `impl<T, U> TryFrom<U> for T where U: Into<T>` 의 조건이 **`Into`** 이기 때문이다.
  그 구현이 `type Error = Infallible` 을 고정한다. **`Infallible` 은 값이 없는 타입**이라 `Err` 갈래를 **탈 수 없다**(17행 빈 `match`).
- ★ **`convert` 를 고치는 법** — 경계를 **`T: Into<U>`** 로 건다. 그러면 `From` 을 쓴 타입(포괄 구현으로 `Into` 를 얻는다)과
  `Into` 만 쓴 타입을 **둘 다** 받는다 — std 의 `From` 문서가 「경계에는 `Into` 를」이라고 권하는 이유다.

```text
===== 소스: r29_bound_into.rs =====
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
===== rustc --edition 2021 r29_bound_into.rs =====
(exit 0)
===== ./r29_bound_into =====
212 32
(exit 0)
```

### 3. ★★ E0277 — `?` 는 `From` 을 쓴다고 진단이 말한다

**출력.**

```text
===== 소스: r29_qmark.rs =====
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

**왜 그런가.**

- ★★ **E0277** 이고, 마지막 `= note:` 가 트레이트 이름을 적는다 — 「**… using the `From` trait**」.
  Reference 가 `?` 를 「`Result::Err(e)` 이면 **`Result::Err(From::from(e))`** 를 돌려준다」로 정의한다. `Into::into` 가 아니다.
- ★ 7행 `impl Into<PortError> for ParseIntError` 는 **고아 규칙을 통과했다** — `PortError` 가 이 크레이트의 타입이라서다.
  **통과했는데 쓸모가 없다** — 이 자리의 유일한 소비자(`?`)가 그것을 안 본다.
- **고치는 법** — 같은 몸통을 **`impl From<ParseIntError> for PortError`** 로 쓴다. 서머리 (4)의 `r29_qmark_from` 이 그 판이고,
  그때는 `?` 가 돌 뿐 아니라 **`into()` 도 공짜로 생긴다**(24행).

### 4. ★★ 줄이는 `From` 은 없다 — 64비트에서도

**출력 — `from` 으로 줄이기.**

```text
===== 소스: r29_narrow.rs =====
// 무손실만 From 이다 — u64 에서 u32 로
fn main() {
    let big: u64 = 5_000_000_000;
    let a = u32::from(big);
    let n: u32 = 7;
    let b = usize::from(n);
    println!("{} {}", a, b);
}
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

**출력 — `as` · `try_from` · 넓히는 `from`.**

```text
===== 소스: r29_tryfrom.rs =====
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

**왜 그런가.**

- **앞 소스는 에러 2건, 둘 다 E0277.** ★★ **6행 `usize::from(u32)` 도 에러다** — 이 머신이 64비트여도.
  `usize` 가 받는 `From` 은 `u8`·`u16`·`bool`(그리고 불안정 타입 하나)뿐이다. `From` 은 **타깃에 따라 생기고 없어지지 않는다.**
- ★★ **`big as u32` 는 `705032704`** — 윗비트를 **조용히** 버렸다. `u32::try_from(big)` 은 **`Err(TryFromIntError(()))`** 로 알려 준다.
- ★ 마지막 줄 — **`TryFrom<u32> for u64` 는 아무도 안 썼다.** std 에 `From<u32> for u64` 가 있으므로
  포괄 구현 `TryFrom<U> for T where U: Into<T>` 가 걸려 **`Error = Infallible`** 인 판이 생겼다(2번 답과 같은 `impl`).

### 5. ★★★ 빌린 모양으로 찾으면 사라진다 — 값은 그대로 있다

**출력.**

```text
===== 소스: r29_borrow.rs =====
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

**왜 그런가.**

- **첫 둘** — `String` 키는 `&str` 로 찾아진다(`Some(1)`). `String: Borrow<str>` 이고 **두 해시가 같다**(`true`).
- ★★★ **셋째 줄 `None`** — `Tagged` 는 `Borrow<str>` 을 달았지만 **해시에 `"tag"` 를 더 섞어** `str` 과 해시가 **다르다**(넷째 줄 `false`).
  `get("kim")` 은 **`str` 의 해시로 칸을 고르므로** 넣은 칸과 **다른 칸**을 뒤져 못 찾는다.
- ★★ **다섯째 줄 `Some(1)`** — 원래 키 모양(`&Tagged`)으로 찾으면 **같은 해시**라 찾는다. **값은 들어 있다.**
  「빌린 모양으로 찾을 때만」 사라진다 — 그래서 **테스트가 원래 키로만 돌면 안 걸린다.**
- ★ **컴파일러는 못 잡는다.** std 의 `Borrow` 문서가 「**`Eq`·`Ord`·`Hash` 는 빌린 값과 소유 값에서 같아야 한다**」를 **계약**으로 둘 뿐이다.
  어긴 결과는 [**28번 주제**](../28-partialeq-eq-partialord-ord-and-hash-contracts/)가 말한 **논리 오류**다(UB 아님, 답만 틀림).

### 6. ★★ E0308 — `get` 은 `AsRef` 를 안 본다

**출력.**

```text
===== 소스: r29_asref_get.rs =====
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

**왜 그런가.**

- ★★ **E0308** — `` expected `&Name`, found `&str` ``. `HashMap::get` 의 경계는 **`K: Borrow<Q>`** 다.
  `Name` 이 가진 `Borrow` 는 std 의 **반사 구현 `Borrow<Name> for Name`** 하나뿐이므로 `Q = Name` 이 됐고, 그래서 `&Name` 을 기대했다.
- ★ **2번 답의 E0308 과 같은 모양**이다 — 「있는 구현 중 반사 구현만 남아 인자 타입이 정해지고, 그것이 안 맞는다」.
  **결함은 「트레이트가 없다」인데 진단은 「타입이 다르다」로 나온다** — 이 주제에서 두 번 본 패턴이다.

### 7. `From` 쪽에만 조건이 걸려 있어서다

- **조건은 `From` 쪽이다** — `impl<T, U> Into<U> for T where U: From<T>`. `From` 이 있으면 `Into` 가 생기고, `Into` 가 있어도 `From` 은 안 생긴다.
  **그래서 `From` 을 쓰면 둘 다 얻고, `Into` 를 쓰면 하나만 얻는다.**
- 반대 방향 포괄 구현을 **함께** 두면 `From` 은 `Into` 로, `Into` 는 `From` 으로 정의돼 **고리가 된다.**
  내 크레이트에 그 반대쪽을 하나 두어 던지면 rustc 가 **E0391 `cycle detected`** 로 거부한다(서머리 (3)의 `r29_reverse`).
  한 방향만 둔 것은 선택이 아니라 **필수**다.
- ★ **경계에는 `Into`** — 경계는 「**받는 쪽**」이라, `Into` 로 걸어야 **`From` 을 쓴 타입과 `Into` 만 쓴 타입을 다 받는다.**
  **구현은 `From`, 경계는 `Into`** — 한 화살표의 두 끝이다(2번 답의 `convert`).

### 8. ★ 입력은 여러 개일 수 있고, 실패 모양은 입력마다 하나다

- `Percent` 는 `TryFrom<i32>`·`TryFrom<u64>`·`TryFrom<&str>` … 을 **여러 번** 구현할 수 있어야 한다 — 그래서 입력은 **제네릭 파라미터**.
  하지만 `TryFrom<i32> for Percent` **한 구현**에 실패 타입이 둘일 이유는 없다 — 그래서 `Error` 는 **연관 타입**.
  [**25번 주제**](../25-traits-definition-impl-default-methods-and-associated-types/)의 판정 「**한 타입에 몇 번**」이 한 트레이트 안에 둘 다 나온 사례다.
- ★ `From` 을 쓴 타입이 공짜로 받는 `TryFrom` 의 `Error` 는 **`Infallible`** 이고, **`Err` 갈래는 원리상 탈 수 없다**(값이 없는 타입이다).
  4번 답의 마지막 줄 `Ok(7)` 과 2번 답의 17행 빈 `match` 가 그것이다.

### 9. ★★ `Borrow` 는 「같은 해시·같은 동등」까지 약속한다

- **한 문장** — `AsRef` 는 「**싸게 빌려 보여 준다**」만, `Borrow` 는 거기에 「**빌린 모양과 원래 모양의 `Eq`·`Ord`·`Hash` 가 같다**」를 더한다.
- **필드 하나** — `AsRef` 는 된다(그냥 그 필드를 보여 주면 된다). `Borrow` 는 **안 된다** — 필드 하나의 해시는 구조체 전체의 해시와 **다르다.**
  std 의 `AsRef` 문서가 이 예를 직접 든다.
- ★ **`get` 이 `Borrow` 를 요구하는 이유** — `get(q)` 는 **`q` 의 해시로 칸을 고르고 `q` 와의 `==` 로 확인**한다.
  그 두 답이 원래 키의 것과 같아야 찾는다. **그 보증을 가진 트레이트가 `Borrow` 뿐**이다(5번 답이 어기면 무슨 일이 나는지 보였다).

### 10. ★ 이동 한 번을 아끼고, 벌 수와 추론을 낸다

- ★★ **아끼는 것** — 호출자가 **이미 `String` 을 가졌을 때의 복사**. `&str` 인자는 안에서 `to_string()` 으로 **한 번 더 할당·복사**하지만,
  `impl Into<String>` 은 `String` 을 **그대로 옮긴다**(서머리 (9)의 16행). 호출자가 `.to_string()` 을 안 써도 되는 편의는 덤이다.
- **더 내는 것** — ① 함수가 **제네릭**이 되어 인자 타입마다 **따로 찍힐 수 있다** — 서머리 (9)가 31번의 창으로 세어 **`opt-level=0` 에서 네 벌, `opt-level=3` 에서 0 벌**을 보였다(판 격자는 [31번 주제](../31-generics-trait-bounds-where-and-monomorphization/))
  ② 두 번 `into` 하면 중간 타입을 못 정한다 ③ 시그니처만 보고 **무엇이 들어가는지** 안 보인다.
- **읽기만 하면 쓰지 않는다** — 옮겨 받을 이유가 없으므로 득이 0 이고 실만 남는다. `&str` 이나 `impl AsRef<str>` 이다.

### 11. 같은 질문, 다른 답

- ★★ **Go 24번** — `%w` 는 **런타임에** 원래 오류를 **값 안에 품어** 사슬을 만들고, `errors.Is`/`As` 가 **런타임에 사슬을 걸어 내려간다.**
  Rust 의 `?` 는 **컴파일 때 정해진 `From::from` 한 번**으로 타입을 바꾼다. 원인을 남길지는 **내 `From` 몸통이 정한다** —
  3번 답의 `PortError(e.to_string())` 은 **원인을 버렸다.** 남기려면 필드로 품고 `source()` 를 잇는다([24번 주제](../24-error-type-design/)).
- **사용자 정의 암묵 변환은 Rust 에 없다.** `from`/`into` 를 **글자로 적어야** 한다. Rust 가 몰래 끼우는 것은 참조의 **역참조 강제**다(목록의 **43번 주제**).
  C# 의 `implicit` 연산자는 **대입 한 줄에서 보이지 않게** 불린다 — 서머리 (10)에서 **.NET SDK 10.0.401 로 직접 던져** 「`(implicit 변환이 불렸다)`」가 두 번 찍히는 것을 보였다.
- **C++ 04번** — 같은 것은 「**좁히기를 막는다**」. 다른 것은 **무엇이 가르나** —
  C++ 는 **`{}` 로 쓰면 막고 `()`·`=` 로 쓰면 허용**한다(문법 모양이 가른다). Rust 는 **`From` 이 있나 없나**가 가르고,
  비트를 그대로 읽는 `as` 는 **별도 연산자**로 떨어져 있다.
- ★ **E0117** — `From`·`u64`·`u32` **셋 다 남의 것**이라 고아 규칙이 막는다(서머리 (5)). 채울 수 있었다면
  **std 의 「무손실」 약속이 남의 크레이트에서 깨졌을 것**이다. 규칙 전문은 [26번 주제](../26-orphan-rule-and-newtype/)다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서·서머리의 **모든 블록** | `capture.sh` 가 `rustc --edition 2021 <파일>.rs` 로 컴파일하고 실행 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` — **흔들린 칸 0 · 고칠 것 0** |
| ★★★ **`Into` 만 구현** | `r29_into_only` · `r29_qmark` | 2 | **E0308 + E0277** · `?` 는 **E0277 `using the From trait`** |
| ★★ **`Into` 만으로 `try_from`** | `r29_into_try` | 1 | `try_from Ok 212` — `Error = Infallible` |
| ★★ **포괄 구현 네 줄** | `r29_blanket.py` — 설치된 `rust-docs` 의 std 소스 페이지에서 추출 | 1 | 767 · 785 · 811 · 827 행 |
| ★★ **줄이는 `From` 부재** | `r29_narrow` | 1 | `u32: From<u64>` · `usize: From<u32>` **둘 다 E0277** |
| `as` 대 `try_from` | `r29_tryfrom` | 1 | `705032704` 대 `Err(TryFromIntError(()))` |
| ★★ **`Borrow` 계약 위반** | `r29_borrow` — 해시에 `"tag"` 를 섞은 키 | 1 | `&str` 로 **`None`** · 원래 키로 **`Some(1)`** |
| `AsRef` 만 단 키 | `r29_asref_get` | 1 | **E0308** — `get` 은 `Borrow` 를 본다 |
| 고아 규칙 | `r29_orphan` | 1 | **E0117** `…for primitive types` |
| 에디션 2015 | `r29_ed2015` — 같은 `TryFrom` 소스 | 1 | **E0405** — 프렐류드 note |
| ★ **경계를 `Into` 로** | `r29_bound_into` — `Into` 만 쓴 타입 + `From` 을 쓴 타입 | 1 | 둘 다 통과 `212 32` |
| ★ **반대 방향 포괄 구현** | `r29_reverse` — 내 크레이트에 `From<T> for U where T: Into<U>` | 1 | **E0391** `cycle detected` |
| **안 던진 것** — 16비트 타깃의 `usize` | 서머리 (5)에서 **추론으로** 적었다 — `rustup target list --installed` 가 `x86_64-unknown-linux-gnu` 하나뿐이다(블록으로 실었다) | 0 | ★ 「추론」으로 표시했다 |
| ★ `impl Into<String>` 의 **벌 수** | `r31_into_o0`/`o3` — 31번의 창(`nm -C`, v0) | 2 | opt 0 **네 벌** · opt 3 **0 벌** |
| C# 암묵 변환 대비 | `r29_implicit` — `r29_csc.sh`(.NET SDK 10.0.401 의 csc) | 1 | 대입·인자 자리에서 **글자 없이** 불린다 |
| **안 센 것** — 변환의 할당 횟수 | 할당 계수기를 안 세웠다 | 0 | ★ 부적용 창으로 적었다 |
| 외부 크레이트 | **쓰지 않음** | 0 | std 만 |

**구현 의존 항목**(버전·환경이 바뀌면 **다시 찍어야 하는** 것).

| 항목 | 왜 |
|---|---|
| `` the following other types implement trait `From<T>` `` 의 **목록** | ★ std 판이 오르면 구현이 **늘 수 있다**(`u32: From<Char>` 같은 불안정 타입도 섞여 나온다) |
| 결함이 **E0308 로 나오나 E0277 로 나오나** | ★ 추론이 반사 구현을 고른 결과다. 진단 순서·문구는 판마다 바뀔 수 있다 |
| std 소스 페이지의 **줄 번호**와 `const`·`[const]` 표기 | ★ `rust-docs` 판마다 움직인다. `const_convert` 가 안정되면 표기가 바뀐다 |
| 진단에 박히는 `/rustc/ded5c06cf…/library/…` 경로 | ★ **이 rustc 판의 커밋 해시** |
| `Borrow` 계약을 어겼을 때 **`None`** 이 나오는 것 | ★ **이 판의 관찰** — 동작이 규정되지 않는다 |

★ **다시 찍는 법** — `capture.sh <새 디렉토리>` 를 그대로 돌리고 `normalize-shaky.py <원본> <새 디렉토리>` 로 견준다.
**이 주제에는 흔들려야 할 칸이 없다** — 전부 한 글자도 같아야 한다.
