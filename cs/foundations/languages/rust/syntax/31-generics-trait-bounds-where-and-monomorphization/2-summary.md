# rust/syntax/31 — 제네릭과 트레이트 경계·`where`·단형화 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Reference — Generic parameters](https://doc.rust-lang.org/reference/items/generics.html) ·
> [Reference — Trait and lifetime bounds](https://doc.rust-lang.org/reference/trait-bounds.html) ·
> [Reference — `Sized`](https://doc.rust-lang.org/reference/special-types-and-traits.html#sized) ·
> [Book 10.1 — Performance of Code Using Generics](https://doc.rust-lang.org/book/ch10-01-syntax.html#performance-of-code-using-generics) ·
> [rustc book — Codegen options(`symbol-mangling-version`)](https://doc.rust-lang.org/rustc/codegen-options/index.html#symbol-mangling-version).
> ★ 위 문서는 **이 머신의 `rust-docs`(1.92.0) 로컬 사본**을 열어 읽었다.
> ★★ **단형화(monomorphization)라는 말은 Reference 가 아니라 Book 이 쓴다** — 언어는 제네릭의 **의미**만 정하고, **몇 벌을 찍나는 구현이 정한다**(§구현 세부).
> **실행 검증** — 이 문서의 모든 출력·에러는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서\
> **`rustc --edition 2021 <파일>.rs`** 로 실제로 돌려 받은 것이다. **`-C` 플래그는 전부 배너에 적었다**(`opt-level`·`symbol-mangling-version`).\
> C++ 대비는 **`g++ 13.3.0` 과 `clang++ 18.1.3`** 두 컴파일러로 `-std=c++20 -Wall -Wextra` 로 던졌다(아래 판 블록).\
> ★★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다. 소스 펜스도 캡처가 찍었다.\
> ★★ **외부 크레이트를 하나도 쓰지 않았다**(네트워크 없음).
> ★★★ **이 문서는 속도를 한 번도 재지 않았다.** 「단형화는 빠르고 `dyn` 은 느리다」는 **이 문서의 주장이 아니다.**
> 잰 것은 **벌 수(심볼 개수)와 바이트(심볼 크기)** 둘뿐이다.
> **버전** — 제네릭·트레이트 경계·`where`·`?Sized` 는 전부 **1.0.0**, 에디션과 무관하다.
> `-C symbol-mangling-version=v0` 은 **이 판의 안정 코드젠 옵션**이다(rustc book 이 지원 값으로 `v0` 을 적는다).
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
| ★★ **판을 탄다** | **심볼 벌 수** — 같은 소스도 `opt-level` 에 따라 **3 → 3 → 2 → 2**((8)) | 인라인·함수 병합이 벌 수를 바꾼다. ★ **그래서 판 격자로만 싣는다** |
| ★★ **판을 탄다** | **심볼 바이트** — 같은 함수가 `opt-level` 에 따라 **106 → 209B**((8)) | 최적화가 몸통을 바꾼다. ★ **절댓값 한 칸은 근거가 아니다**(규칙 24) |
| 안 흔들린다 | **같은 판·같은 플래그의 벌 수와 바이트** | 재실행해도 한 글자 같았다(제출 전 재대조) |
| 안 흔들린다 | `nm -C` 가 푼 심볼 **이름**(`r31_mono::total::<r31_mono::Sq>`) | ★ v0 맨글링을 이름으로 풀었다 — **해시가 안 보인다** |
| 안 흔들린다 | LLVM IR 의 `@vtable.N` **줄**((8)) | 같은 판에서 고정이다. 줄 안의 `[836535f787e97d3]` 같은 **크레이트 해시**도 재실행에서 같았다 |
| 안 흔들린다 | 에러 번호·제목·`파일:줄:칸`·종료 코드 | 같은 컴파일러 판에서 고정이다(rustc·g++·clang++ 각각) |

★ 정규화 규칙은 **기본 넷**만 썼고 **하나도 걸리지 않았다.** nm 의 **주소 열은 캡처가 버렸다**(`awk` 로 이름·크기만 남겼다 — 배너에 적혀 있다).

## 한눈에 — 쉽게 말하면

**제네릭 함수는 「틀」이고, 트레이트 경계는 「이 틀에 들어갈 수 있는 재료의 자격」이다.
컴파일러는 틀을 받아 재료마다 따로 한 벌씩 찍어 낸다 — 단, 찍어 놓고 똑같은 것은 합치고, 작은 것은 쓰는 자리에 녹여 넣는다.**

| 비유 | 실체 |
|---|---|
| 「**틀에 적힌 자격 요건**」 | ★ **트레이트 경계 `T: Shape`** — 몸통이 쓰는 능력을 **미리 적는다**((1)) |
| 「**요건을 안 적었으면 틀 안에서 그 능력을 못 쓴다**」 | ★★ **E0599** — 호출이 **하나도 없어도** 정의 자리에서 막힌다((1)) |
| 「**재료가 자격이 없으면 입구에서 돌려보낸다**」 | **E0277** — 호출 자리에서 막힌다((3)) |
| 「**요건을 따로 적는 별지**」 | **`where` 절** — 긴 경계, 그리고 **타입 파라미터가 아닌 것에 거는 경계**((2)) |
| 「**틀이 몰래 붙여 둔 기본 요건 — 크기가 정해진 재료만**」 | ★ **숨은 `Sized` 경계** — `?Sized` 로 푼다((5)) |
| 「**재료마다 한 벌씩 찍는 공장**」 | ★★★ **단형화** — `total::<Sq>`·`total::<Circle>`·`total::<Rect>` 세 벌((8)) |
| 「**찍어 보니 똑같은 두 벌은 하나로**」 | ★★ **함수 병합** — `opt-level=2` 부터 `total::<Tile>` 이 사라진다((8)) |
| 「**작은 틀은 아예 쓰는 자리에 녹인다**」 | ★★ **인라인** — `opt-level=3` 에서 `total` 이 **0 벌**이 된다((8)) |
| 「**한 벌만 두고 표를 보고 고르는 창구**」 | **`dyn Trait`** — 함수 **한 벌 + 타입마다 vtable**((8)) |

- ★★★ **판정은 두 줄이다.**
  **① 몸통은 경계만 믿는다** — 경계에 없는 능력은 **호출이 있든 없든** 못 쓴다((1)). C++ 템플릿은 **인스턴스화할 때** 본다((7)).
  **② 벌 수는 언어가 아니라 컴파일러가 정한다** — 「타입마다 한 벌」은 **`opt-level=0` 의 관찰**이고, 최적화가 켜지면 **합치고 녹인다**((8)).
- ★★ **「코드 팽창」은 크기(바이트)로 재야 판단이 선다** — 이 문서의 격자에서 제네릭 `total` 들의 합은 `dyn` 한 벌보다 **언제나 컸다**(판마다 폭이 다르다).
  **그 값이 무엇을 사는지(속도)는 재지 않았다.** 크기 쪽 청구서만 보였다.

```text
   단형화 — 같은 소스가 몇 벌이 되나 (8)의 블록 그대로

   fn total<T: Shape>(items: &[T])       ←  MIR 에서는 한 벌 (제네릭 그대로 — 단형화 이전)
             │
             │  호출 세 곳 : total(&[Sq…]) · total(&[Circle…]) · total(&[Rect…])
             ▼
   ┌─────────────── opt-level=0 ───────────────┐   ┌──── opt-level=3 ────┐
   │ total::<Sq>        ┐                      │   │                     │
   │ total::<Circle>    ├ 3 벌                  │   │  (전부 main 에      │
   │ total::<Rect>      ┘                      │   │   녹았다 — 0 벌)    │
   │ + Iter<Sq>::next · Iter<Circle>::next …   │   │                     │
   │   ★ 부른 std 제네릭도 타입마다 따로 3 벌  │   │  main 하나만 남는다 │
   └───────────────────────────────────────────┘   └─────────────────────┘

   인라인을 막으면(#[inline(never)]) · Sq 와 몸이 같은 Tile 을 더하면     (8)의 격자
   opt-level      0        1        2        3
   total 벌 수    3        3        2 ★      2        ← ★ total::<Tile> 이 total::<Sq> 에 합쳐졌다
   total 바이트   318      579      370      370
   total_dyn      1 벌     1 벌     1 벌     1 벌
   dyn 바이트     111      87       87       87       + vtable 3 개 (타입마다 하나, IR 에서 본다)
```

> **단형화(monomorphization)** — 제네릭 함수를 **쓰인 타입마다 따로 기계어로 찍어 내는** 컴파일 전략.\
> 예: `total::<Sq>` 와 `total::<Rect>` 가 서로 다른 심볼로 바이너리에 들어간다(`opt-level=0`).

> **트레이트 경계(trait bound)** — 타입 파라미터가 가져야 할 능력. `T: Shape` 는 「`T` 는 `Shape` 를 구현해야 한다」.\
> 예: `fn total<T: Shape>(…)` 의 몸통은 **`Shape` 의 메서드만** 부를 수 있다.

> **심볼(symbol)** — 오브젝트·실행 파일 안에서 함수·데이터에 붙은 이름. `nm` 이 목록을 보여 준다.\
> 예: `t r31_mono::total::<r31_mono::Sq>` — `t` 는 「코드 영역의 지역 심볼」이다.

> **맨글링(mangling)** — 소스의 경로·제네릭 인자를 심볼 이름 하나로 **인코딩**하는 것. `v0` 방식은 **제네릭 인자를 이름에 담아** `nm -C` 가 `<…Sq>` 로 풀어 준다.\
> 예: 기본(legacy) 방식은 인자 대신 **해시**(`17h332d…E`)를 붙여 어느 타입 판인지 이름으로 안 보인다.

## 이 주제가 답하려는 질문

1. **경계를 어떻게 읽고 쓰나** — 인라인·`where`·여러 경계·연관 타입 경계·숨은 `Sized`((1)~(6)).
2. ★★ **경계는 언제 검사되나** — 정의 자리인가 호출 자리인가. **C++ 템플릿·TS 제약과 무엇이 다른가**((1)·(3)·(7)·(9)).
3. ★★★ **단형화는 코드 크기에 무엇을 하나** — 몇 벌이 생기고, **그 수가 무엇에 따라 바뀌나**((8)).

★ [**25번 주제**](../25-traits-definition-impl-default-methods-and-associated-types/)가 트레이트를 **정의**했다면 여기는 그것을 **경계로 쓰는** 쪽이다.
★★ **정본 경계가 둘이다** —
**컴파일 단계 일반**(어휘·구문 분석·심볼 테이블·링커)은 [`compiler-pipeline/`](../../../../compiler-pipeline/)이 정본이고,
**「제로 코스트」의 논증**(무엇이 0이고 무엇이 0이 아닌가, 청구서가 컴파일 시간·바이너리 크기로 옮겨 간다는 것)은
[`언어-특성/README.md`](../../언어-특성/README.md) §6 이 정본이다. **여기서는 그 논증을 다시 쓰지 않는다** —
여기는 「**경계 문법**」과 「**벌 수와 바이트를 실제로 세면 무엇이 나오나**」뿐이다.

## 동작 방식

### (0) 이 주제가 쓰는 네 창

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **심볼 표(`nm -C -S`) × `opt-level` 격자** | **몇 벌이 생기나·몇 바이트인가**((8)) | ★ **이 주제의 본체** |
| ★★ **LLVM IR 의 `@vtable`** | `dyn` 판이 **무엇을 대신 만드나**((8)) | 대비 창 |
| **경계를 빼고·틀리게 던지기** | 경계가 **언제·어디서** 검사되나 — E0599·E0277·E0271((1)·(3)·(4)·(5)) | 「에러도 출력이다」 |
| ★★ **같은 질문을 C++ 두 컴파일러로** | 템플릿은 **인스턴스화 때** 본다((7)) | ★ 교차 언어 창 |

★★★ **「같은 질문을 다른 창으로 물었다」가 둘 있다**(제5의 상태).
- **MIR 창(`--emit=mir`)은 이 질문에 답하지 못한다** — 27번은 이 창으로 `derive` 생성물을 **보았지만**, MIR 은 **단형화 이전**이라
  제네릭 `total` 을 **`fn total(_1: &[T])` 한 벌**로만 보여 준다((8)). 「몇 벌」을 물으면 **언제나 1** 이라 답한다 — 틀린 답이 아니라 **다른 질문의 답**이다.
- **rustc 의 단형화 목록(`-Z print-mono-items`)은 nightly 전용**이라 이 판에서 **안 열린다**((8), 블록으로 확인).
  그래서 **같은 질문을 링크 뒤의 심볼 표로 물었다.** ★ 이 창이 **못 보는 것** — 인라인되어 **심볼이 없어진 벌**은 안 세어진다.
  그래서 `#[inline(never)]` 판을 **따로** 세웠다(0 벌이 「안 찍었다」인지 「녹였다」인지를 가르려고).

★ **「부적용인 창」** — **실행 시간**이다. 이 주제는 속도를 **재지 않는다**(머리말).

### (1) ★★ 경계 없이 메서드를 부르면 — 호출이 하나도 없어도 막힌다

**언제 쓰나** — 안 쓴다. 경계가 **왜 필요한지**의 증거다.

```rust
// r31_nobound.rs
// 경계 없이 메서드를 부르면 — 호출이 하나도 없어도
trait Shape {
    fn area(&self) -> f64;
}

fn total<T>(items: &[T]) -> f64 {
    items.iter().map(|it| it.area()).sum()
}

fn main() {}
```

```text
===== rustc --edition 2021 r31_nobound.rs =====
error[E0599]: no method named `area` found for reference `&T` in the current scope
 --> r31_nobound.rs:7:30
  |
7 |     items.iter().map(|it| it.area()).sum()
  |                              ^^^^ method not found in `&T`
  |
  = help: items from traits can only be used if the type parameter is bounded by the trait
help: the following trait defines an item `area`, perhaps you need to restrict type parameter `T` with it:
  |
6 | fn total<T: Shape>(items: &[T]) -> f64 {
  |           +++++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0599`.
(exit 1)
```

- ★★ **E0599** — `` no method named `area` found for reference `&T` ``. **`main` 이 비어 있다** — `total` 은 **한 번도 안 불렸다.**
  그래도 막힌다. **몸통은 정의 자리에서 경계만 보고 검사된다** — `T` 에 대해 아는 것은 **경계에 적힌 것뿐**이다.
- `help:` 가 처방을 준다 — 「**restrict type parameter `T` with it**」: `fn total<T: Shape>`.
- ★ 이 성질이 (7)의 C++ 템플릿과 갈리는 자리다 — 같은 모양의 C++ 코드는 **인스턴스화 전까지 통과한다.**

### (2) 경계를 쓰는 세 모양 — 인라인 · `where` · 여러 경계

**언제 쓰나** — 경계가 둘 이상이거나 길어질 때 `where` 로 뺀다. **타입 파라미터가 아닌 것**에 걸 때는 `where` 만 된다.

```rust
// r31_bounds.rs
// 같은 경계를 세 가지로 쓴다 — 인라인 · where · 여러 경계
use std::fmt::Debug;

trait Shape {
    fn area(&self) -> f64;
}

#[derive(Debug, Clone)]
struct Sq(f64);

impl Shape for Sq {
    fn area(&self) -> f64 {
        self.0 * self.0
    }
}

fn a<T: Shape + Debug>(x: &T) -> String {
    format!("{:?}={}", x, x.area())
}

fn b<T>(x: &T) -> String
where
    T: Shape + Debug,
{
    format!("{:?}={}", x, x.area())
}

// ★ where 만 쓸 수 있는 자리 — 경계의 왼쪽이 타입 파라미터가 아니다
fn c<T>(xs: Vec<T>) -> String
where
    Vec<T>: Debug,
    T: Shape + Clone,
{
    let first = xs[0].clone();
    format!("{:?} 첫 넓이 {}", xs, first.area())
}

fn main() {
    println!("a  {}", a(&Sq(2.0)));
    println!("b  {}", b(&Sq(2.0)));
    println!("c  {}", c(vec![Sq(1.0), Sq(3.0)]));
}
```

```text
===== rustc --edition 2021 r31_bounds.rs =====
(exit 0)
===== ./r31_bounds =====
a  Sq(2.0)=4
b  Sq(2.0)=4
c  [Sq(1.0), Sq(3.0)] 첫 넓이 1
(exit 0)
```

- **`a` 와 `b` 는 같은 함수다** — `T: Shape + Debug` 를 **꺾쇠 안**에 쓰나 **`where` 절**에 쓰나의 차이뿐. 출력이 같다.
- ★ **여러 경계는 `+`** 로 잇는다 — `Shape + Debug` 면 몸통이 `x.area()` 와 `{:?}` 를 **둘 다** 쓸 수 있다.
- ★★ **31행 `Vec<T>: Debug`** — 경계의 **왼쪽이 `T` 가 아니라 `Vec<T>`** 다. 이런 경계는 **꺾쇠 안에 쓸 자리가 없다** — `where` 전용이다.
  (`Vec<T>: Debug` 는 결국 `T: Debug` 를 요구하므로 이 예에서는 돌려 적은 것이다 — **모양을 보이려는 예**다.)

### (3) 빠진 경계는 호출 자리에서 막힌다

```rust
// r31_missing.rs
// 여러 경계 중 하나가 빠지면 — 호출 자리의 에러
use std::fmt::Debug;

trait Shape {
    fn area(&self) -> f64;
}

struct Sq(f64); // ★ Debug 가 없다

impl Shape for Sq {
    fn area(&self) -> f64 {
        self.0 * self.0
    }
}

fn a<T: Shape + Debug>(x: &T) -> String {
    format!("{:?}={}", x, x.area())
}

fn main() {
    println!("{}", a(&Sq(2.0)));
}
```

```text
===== rustc --edition 2021 r31_missing.rs =====
error[E0277]: `Sq` doesn't implement `Debug`
  --> r31_missing.rs:21:22
   |
21 |     println!("{}", a(&Sq(2.0)));
   |                    - ^^^^^^^^ the trait `Debug` is not implemented for `Sq`
   |                    |
   |                    required by a bound introduced by this call
   |
   = note: add `#[derive(Debug)]` to `Sq` or manually `impl Debug for Sq`
note: required by a bound in `a`
  --> r31_missing.rs:16:17
   |
16 | fn a<T: Shape + Debug>(x: &T) -> String {
   |                 ^^^^^ required by this bound in `a`
help: consider annotating `Sq` with `#[derive(Debug)]`
   |
 8 + #[derive(Debug)]
 9 | struct Sq(f64); // ★ Debug 가 없다
   |

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0277`.
(exit 1)
```

- ★ **E0277 — `Sq` doesn't implement `Debug`**, 밑줄은 **21행 호출 자리**(`&Sq(2.0)`)다. 그리고 `note:` 가 **16행 경계**(`Debug`)를 짚는다.
- ★★ **(1)과 합치면 Rust 는 두 자리에서 막는다** — **몸통은 정의 자리**(경계에 없는 능력 → E0599),
  **인자는 호출 자리**(경계를 못 채운 타입 → E0277). 한쪽만이 아니다.
- ★★ [TS 갈래 20번](../../../ts/syntax/20-generic-constraints-and-defaults/) (6)이 **rustc 1.92.0 으로 이것을 실제로 던져**
  「**Rust 는 정의 자리, TS 는 사용 자리」는 틀린 요약이다 — 둘 다 양쪽에서 막는다**」고 적었다. 여기 (1)·(3)이 그 **Rust 쪽 분해도**다.
  그 편이 짚은 **진짜 축**은 (9)에서 잇는다 — **이름이냐 모양이냐.**

### (4) 연관 타입에 경계 — `Iterator<Item = u8>`

**언제 쓰나** — 「이터레이터면 된다」가 아니라 「**`u8` 을 내는** 이터레이터」여야 할 때.

```rust
// r31_assoc.rs
// 연관 타입에 경계 — Iterator<Item = u8>
fn checksum<I: Iterator<Item = u8>>(it: I) -> u8 {
    it.fold(0u8, |acc, b| acc.wrapping_add(b))
}

fn loud<I>(it: I) -> Vec<String>
where
    I: Iterator,
    I::Item: std::fmt::Display, // ★ 연관 타입 자체에 경계
{
    it.map(|x| format!("{}!", x)).collect()
}

fn main() {
    println!("{}", checksum(vec![250u8, 10].into_iter()));
    println!("{}", checksum("ab".bytes()));
    println!("{:?}", loud([1, 2].into_iter()));
    println!("{}", checksum(vec![1u16, 2].into_iter()));
}
```

```text
===== rustc --edition 2021 r31_assoc.rs =====
error[E0271]: expected `IntoIter<u16>` to be an iterator that yields `u8`, but it yields `u16`
  --> r31_assoc.rs:18:29
   |
18 |     println!("{}", checksum(vec![1u16, 2].into_iter()));
   |                    -------- ^^^^^^^^^^^^^^^^^^^^^^^^^ expected `u8`, found `u16`
   |                    |
   |                    required by a bound introduced by this call
   |
note: required by a bound in `checksum`
  --> r31_assoc.rs:2:25
   |
 2 | fn checksum<I: Iterator<Item = u8>>(it: I) -> u8 {
   |                         ^^^^^^^^^ required by this bound in `checksum`

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0271`.
(exit 1)
```

- ★ **E0271** — `` expected `IntoIter<u16>` to be an iterator that yields `u8`, but it yields `u16` ``.
  `Item = u8` 은 **연관 타입을 고정하는 경계**다. 번호가 E0277(트레이트 미충족)이 아니라 **E0271(연관 타입 불일치)** 인 것에 주의 — `IntoIter<u16>` 은 **`Iterator` 이긴 하다.**
- ★ **9행 `I::Item: Display`** — 연관 타입 **자체에** 경계를 거는 꼴. 이것도 왼쪽이 `I` 가 아니라 **`where` 전용**이다.
- 15~17행은 **에러가 없다** — `Vec<u8>` 의 이터레이터와 `"ab".bytes()` 는 둘 다 `u8` 을 낸다.

### (5) ★ 숨은 경계 `Sized` — `?Sized` 로 푼다

**언제 쓰나** — `&T` 로 받는 함수에 **`str`·`[T]`·`dyn Trait` 처럼 크기가 안 정해진 타입**을 넣고 싶을 때.

```rust
// r31_sized.rs
// 숨어 있는 경계 Sized — str 을 T 로 받으려 하면
use std::fmt::Display;

fn plain<T: Display>(x: &T) -> String {
    format!("[{}]", x)
}

fn relaxed<T: Display + ?Sized>(x: &T) -> String {
    format!("[{}]", x)
}

fn main() {
    let s: &str = "hi";
    println!("{}", relaxed(s)); // T = str
    println!("{}", plain(&s)); // T = &str — 크기가 있다
    println!("{}", plain(s)); // T = str
}
```

```text
===== rustc --edition 2021 r31_sized.rs =====
error[E0277]: the size for values of type `str` cannot be known at compilation time
  --> r31_sized.rs:16:26
   |
16 |     println!("{}", plain(s)); // T = str
   |                    ----- ^ doesn't have a size known at compile-time
   |                    |
   |                    required by a bound introduced by this call
   |
   = help: the trait `Sized` is not implemented for `str`
note: required by an implicit `Sized` bound in `plain`
  --> r31_sized.rs:4:10
   |
 4 | fn plain<T: Display>(x: &T) -> String {
   |          ^ required by the implicit `Sized` requirement on this type parameter in `plain`
help: consider relaxing the implicit `Sized` restriction
   |
 4 | fn plain<T: Display + ?Sized>(x: &T) -> String {
   |                     ++++++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0277`.
(exit 1)
```

- ★★ **E0277** — `` the size for values of type `str` cannot be known at compilation time ``.
  `note:` 가 정확히 짚는다 — 「**required by an implicit `Sized` bound in `plain`**」. **4행에 `Sized` 라는 글자가 없는데** 걸렸다.
  **모든 타입 파라미터에는 `Sized` 경계가 숨어 있다**(Reference 의 `Sized` 절).
- ★ **16행만 에러다** — 15행 `plain(&s)` 는 `T = &str`(참조는 크기가 있다)이라 통과, 14행 `relaxed(s)` 는 **`?Sized` 로 숨은 경계를 풀어서** `T = str` 이 된다.
- `help:` 가 처방을 준다 — `T: Display + ?Sized`. **`?` 는 「요구하지 않는다」** 는 뜻이다(더하는 경계가 아니라 **빼는 경계**).

### (6) 기본 타입 인자 — 구조체·트레이트에는 되고 함수에는 안 된다

```rust
// r31_default.rs
// 기본 타입 인자 — 구조체·트레이트에는 된다
use std::ops::Add;

#[derive(Debug)]
struct Wrap<T = i32>(T);

#[derive(Debug, Clone, Copy)]
struct M(i32);

impl Add for M {
    // Add<Rhs = Self> — 기본값이 Self 라 Rhs 를 안 적었다
    type Output = M;
    fn add(self, o: M) -> M {
        M(self.0 + o.0)
    }
}

fn main() {
    let w: Wrap = Wrap(3); // Wrap<i32>
    let v: Wrap<&str> = Wrap("x");
    println!("{:?} {:?} {:?}", w, v, M(1) + M(2));
}
```

```text
===== rustc --edition 2021 r31_default.rs =====
(exit 0)
===== ./r31_default =====
Wrap(3) Wrap("x") M(3)
(exit 0)
```

- **5행 `struct Wrap<T = i32>`** — 타입에 기본 인자를 줬다. 19행 `let w: Wrap` 은 `Wrap<i32>` 다.
- ★ **10~16행 `impl Add for M`** — `Add<Rhs = Self>` 의 **기본 인자**라 `Rhs` 를 안 적었다([**30번 주제**](../30-operator-overloading-std-ops-index-and-deref/) (4)).
- ★★ **함수에는 안 된다** — [TS 갈래 20번](../../../ts/syntax/20-generic-constraints-and-defaults/) (6)이 **`fn defaulted<T = i32>`** 를 rustc 1.92.0 에 던져
  「**defaults for generic parameters are not allowed here**」를 받았다(`deny(invalid_type_param_default)` — **옛날에는 받아 줬다가 거둬들이는 중**인 문맥).
  **TS 는 함수에도 된다.** 이 문서는 그 판을 **다시 던지지 않고 인용한다**(같은 rustc 판이다).

### (7) ★★ C++ 템플릿 — 두 컴파일러로 같은 질문을

**언제 쓰나** — 「Rust 제네릭은 C++ 템플릿과 같은가」를 가를 때.

**① 템플릿을 정의만 하고 한 번도 안 쓰면.**

```cpp
// r31_tmpl.cpp
// C++ 템플릿 — 몸통을 언제 검사하나
template <class T>
double total(const T& x) {
    return x.area(); // T 가 area 를 가지는지 이 자리에서는 모른다
}

int main() {
    return 0; // ★ 한 번도 인스턴스화하지 않는다
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -c r31_tmpl.cpp -o r31_tmpl.o =====
(exit 0)
===== clang++ -std=c++20 -Wall -Wextra -c r31_tmpl.cpp -o r31_tmpl.o =====
(exit 0)
```

- ★★★ **g++ 도 clang++ 도 `exit 0`, 진단 0줄.** 4행 `x.area()` 는 **`T` 가 무엇인지 모르는 채** 통과했다 —
  C++ 는 `T` 에 **의존하는 식**을 **인스턴스화할 때** 검사한다. (1)의 Rust 는 **같은 모양에서 E0599** 였다.
- ★ `-Wall -Wextra` 로도 **경고 0 건**이다. **「종료 코드 0」과 「진단 0 줄」을 같이 봐야** 이 결론이 선다.

**② `int` 로 인스턴스화하면.**

```cpp
// r31_tmpl_int.cpp
// 인스턴스화하는 순간 — int 로 부르면
template <class T>
double total(const T& x) {
    return x.area();
}

int main() {
    return total(3) == 0.0 ? 0 : 1;
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -c r31_tmpl_int.cpp -o r31_tmpl_int.o =====
r31_tmpl_int.cpp: In instantiation of ‘double total(const T&) [with T = int]’:
r31_tmpl_int.cpp:8:17:   required from here
r31_tmpl_int.cpp:4:14: error: request for member ‘area’ in ‘x’, which is of non-class type ‘const int’
    4 |     return x.area();
      |            ~~^~~~
(exit 1)
===== clang++ -std=c++20 -Wall -Wextra -c r31_tmpl_int.cpp -o r31_tmpl_int.o =====
r31_tmpl_int.cpp:4:13: error: member reference base type 'const int' is not a structure or union
    4 |     return x.area();
      |            ~^~~~~
r31_tmpl_int.cpp:8:12: note: in instantiation of function template specialization 'total<int>' requested here
    8 |     return total(3) == 0.0 ? 0 : 1;
      |            ^
1 error generated.
(exit 1)
```

- ★★ **에러가 템플릿 몸통(4행)에서 난다** — g++ 은 「**In instantiation of … [with T = int]**」, clang++ 은 「**in instantiation of function template specialization 'total<int>'**」.
  **호출 자리(8행)는 `required from here`·`note:` 로 뒤따를 뿐**이다. Rust (3)은 **호출 자리가 주 진단**이고 경계가 `note:` 였다 — **순서가 뒤집혀 있다.**
- ★ 두 컴파일러의 **문구·캐럿 열이 다르다**(g++ 은 14열, clang++ 은 13열) — **표준은 진단의 모양을 안 정한다.** 같은 것은 「**인스턴스화 때 몸통에서 난다**」는 성질이다.

**③ C++20 콘셉트로 요구를 선언하면.**

```cpp
// r31_concept.cpp
// C++20 콘셉트 — 요구를 선언하면 에러가 호출 자리로 온다
template <class T>
concept Shape = requires(const T& x) { x.area(); };

template <Shape T>
double total(const T& x) {
    return x.area();
}

int main() {
    return total(3) == 0.0 ? 0 : 1;
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -c r31_concept.cpp -o r31_concept.o =====
r31_concept.cpp: In function ‘int main()’:
r31_concept.cpp:11:17: error: no matching function for call to ‘total(int)’
   11 |     return total(3) == 0.0 ? 0 : 1;
      |            ~~~~~^~~
r31_concept.cpp:6:8: note: candidate: ‘template<class T>  requires  Shape<T> double total(const T&)’
    6 | double total(const T& x) {
      |        ^~~~~
r31_concept.cpp:6:8: note:   template argument deduction/substitution failed:
r31_concept.cpp:6:8: note: constraints not satisfied
r31_concept.cpp: In substitution of ‘template<class T>  requires  Shape<T> double total(const T&) [with T = int]’:
r31_concept.cpp:11:17:   required from here
r31_concept.cpp:3:9:   required for the satisfaction of ‘Shape<T>’ [with T = int]
r31_concept.cpp:3:17:   in requirements with ‘const T& x’ [with T = int]
r31_concept.cpp:3:46: note: the required expression ‘x.area()’ is invalid
    3 | concept Shape = requires(const T& x) { x.area(); };
      |                                        ~~~~~~^~
cc1plus: note: set ‘-fconcepts-diagnostics-depth=’ to at least 2 for more detail
(exit 1)
===== clang++ -std=c++20 -Wall -Wextra -c r31_concept.cpp -o r31_concept.o =====
r31_concept.cpp:11:12: error: no matching function for call to 'total'
   11 |     return total(3) == 0.0 ? 0 : 1;
      |            ^~~~~
r31_concept.cpp:6:8: note: candidate template ignored: constraints not satisfied [with T = int]
    6 | double total(const T& x) {
      |        ^
r31_concept.cpp:5:11: note: because 'int' does not satisfy 'Shape'
    5 | template <Shape T>
      |           ^
r31_concept.cpp:3:41: note: because 'x.area()' would be invalid: member reference base type 'const int' is not a structure or union
    3 | concept Shape = requires(const T& x) { x.area(); };
      |                                         ^
1 error generated.
(exit 1)
```

- ★★ **에러가 호출 자리(11행)로 왔다** — 「**no matching function for call**」 + 「**constraints not satisfied**」.
  C++20 콘셉트는 **요구를 선언으로 올려** Rust 의 경계와 **같은 자리**에서 막는다.
- ★★ **그래도 다른 것이 남는다** — 콘셉트는 **`requires(…) { x.area(); }` 라는 모양**(식이 성립하나)을 본다. **구조적**이다.
  Rust 의 경계는 **`impl Shape for Sq` 라는 선언**이 있어야 통과한다. **명목적**이다((9)).

**④ 콘셉트를 달고 몸통에서 콘셉트 밖의 능력을 쓰면.**

```cpp
// r31_concept_body.cpp
// 콘셉트를 달아도 — 몸통이 콘셉트 밖의 능력을 쓰면
template <class T>
concept Shape = requires(const T& x) { x.area(); };

template <Shape T>
double total(const T& x) {
    return x.area() + x.perimeter(); // perimeter 는 콘셉트에 없다
}

int main() {
    return 0; // 인스턴스화하지 않는다
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -c r31_concept_body.cpp -o r31_concept_body.o =====
(exit 0)
===== clang++ -std=c++20 -Wall -Wextra -c r31_concept_body.cpp -o r31_concept_body.o =====
(exit 0)
```

- ★★★ **두 컴파일러 다 `exit 0`, 진단 0줄.** 7행 `x.perimeter()` 는 **콘셉트 `Shape` 에 없는 능력**인데 통과했다.
  **콘셉트는 호출 자리를 검사할 뿐 몸통을 콘셉트로 검사하지 않는다** — 몸통은 **여전히 인스턴스화 때** 본다(①의 성질 그대로).
  Rust (1)은 **같은 자리에서 E0599** 다 — **몸통이 경계 밖을 쓰는 것 자체를 막는다.** 이것이 콘셉트와 경계의 **두 번째 차이**다.

**⑤ 함수 템플릿에 기본 타입 인자를 주면.**

```cpp
// r31_tmpl_default.cpp
// 함수 템플릿의 기본 타입 인자
template <class T = int>
T zero() {
    return T{};
}

int main() {
    return zero() + zero<long>() == 0 ? 0 : 1; // zero() 는 zero<int>()
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -c r31_tmpl_default.cpp -o r31_tmpl_default.o =====
(exit 0)
===== clang++ -std=c++20 -Wall -Wextra -c r31_tmpl_default.cpp -o r31_tmpl_default.o =====
(exit 0)
```

- ★ **C++ 는 함수에도 기본 타입 인자가 된다**(두 컴파일러 `exit 0`). Rust 는 (6)의 인용대로 「**not allowed here**」다.

### (8) ★★★ 단형화를 센다 — 창 셋, 판 넷

**언제 쓰나** — 제네릭 함수가 **몇 벌 생기나**, 그것이 **몇 바이트인가**를 판단할 때.

**먼저 — 세는 도구가 이 판에 있나.**

```text
===== rustup toolchain list =====
stable-x86_64-unknown-linux-gnu (active, default)
(exit 0)
===== rustc --edition 2021 -Z print-mono-items=lazy r31_mono.rs =====
error: the option `Z` is only accepted on the nightly compiler

help: consider switching to a nightly toolchain: `rustup default nightly`

note: selecting a toolchain with `+toolchain` arguments require a rustup proxy; see <https://rust-lang.github.io/rustup/concepts/index.html>

note: for more information about Rust's stability policy, see <https://doc.rust-lang.org/book/appendix-07-nightly-rust.html#unstable-features>

error: 1 nightly option were parsed

(exit 1)
```

- rustc 의 **단형화 목록 옵션은 nightly 전용**이고, 이 머신의 툴체인은 **stable 하나뿐**이다. **그래서 이 창은 「못 연 창」이다.**

**다음 — MIR 로 물으면.**

```rust
// r31_mono.rs
// 같은 제네릭 함수를 세 타입으로 부른다 — 몇 벌 생기나
trait Shape {
    fn area(&self) -> f64;
}

struct Sq(f64);
struct Circle(f64);
struct Rect(f64, f64);

impl Shape for Sq {
    fn area(&self) -> f64 {
        self.0 * self.0
    }
}
impl Shape for Circle {
    fn area(&self) -> f64 {
        3.0 * self.0 * self.0
    }
}
impl Shape for Rect {
    fn area(&self) -> f64 {
        self.0 * self.1
    }
}

fn total<T: Shape>(items: &[T]) -> f64 {
    let mut s = 0.0;
    for it in items {
        s += it.area();
    }
    s
}

fn total_dyn(items: &[&dyn Shape]) -> f64 {
    let mut s = 0.0;
    for it in items {
        s += it.area();
    }
    s
}

fn main() {
    let g = total(&[Sq(1.0), Sq(2.0)]) + total(&[Circle(1.0)]) + total(&[Rect(1.0, 2.0)]);
    let (s1, s2, c, r) = (Sq(1.0), Sq(2.0), Circle(1.0), Rect(1.0, 2.0));
    let d = total_dyn(&[&s1, &s2, &c, &r]);
    println!("{} {}", g, d);
}
```

```text
===== rustc --edition 2021 --emit=mir -o r31_mono.mir r31_mono.rs =====
(exit 0)
===== grep -E '^fn ' r31_mono.mir =====
fn <impl at r31_mono.rs:10:1: 10:18>::area(_1: &Sq) -> f64 {
fn <impl at r31_mono.rs:15:1: 15:22>::area(_1: &Circle) -> f64 {
fn <impl at r31_mono.rs:20:1: 20:20>::area(_1: &Rect) -> f64 {
fn total(_1: &[T]) -> f64 {
fn total_dyn(_1: &[&dyn Shape]) -> f64 {
fn main() -> () {
fn Sq(_1: f64) -> Sq {
fn Sq(_1: f64) -> Sq {
fn Circle(_1: f64) -> Circle {
fn Circle(_1: f64) -> Circle {
fn Rect(_1: f64, _2: f64) -> Rect {
fn Rect(_1: f64, _2: f64) -> Rect {
(exit 0)
```

- ★★ **`fn total(_1: &[T]) -> f64` 가 한 줄** — `T` 가 **그대로** 있다. MIR 은 **단형화 이전**의 중간 표현이라 **몇 벌인지 모른다.**
  [**27번 주제**](../27-derive-macros-debug-clone-partialeq-default-hash/) (4)는 이 창으로 `derive` 생성물을 **잘 보았다** — **보는 질문이 달랐다.**
  (`fn Sq(_1: f64) -> Sq` 가 **두 번** 나오는 것은 튜플 구조체 생성자의 MIR 두 판이다 — 이 주제의 질문과 무관하다.)

**그래서 — 링크 뒤의 심볼 표로 물었다.** `opt-level=0`.

```text
===== rustc --edition 2021 -C opt-level=0 -C symbol-mangling-version=v0 r31_mono.rs =====
(exit 0)
===== nm -C r31_mono | awk '/r31_mono::/ {$1=""; print substr($0, 2)}' =====
t r31_mono::total::<r31_mono::Sq>
t r31_mono::total::<r31_mono::Rect>
t r31_mono::total::<r31_mono::Circle>
t r31_mono::main
t r31_mono::total_dyn
t <r31_mono::Sq as r31_mono::Shape>::area
t <r31_mono::Rect as r31_mono::Shape>::area
t <core::slice::iter::Iter<r31_mono::Sq> as core::iter::traits::iterator::Iterator>::next
t <core::slice::iter::Iter<r31_mono::Rect> as core::iter::traits::iterator::Iterator>::next
t <core::slice::iter::Iter<r31_mono::Circle> as core::iter::traits::iterator::Iterator>::next
t <core::slice::iter::Iter<&dyn r31_mono::Shape> as core::iter::traits::iterator::Iterator>::next
t <r31_mono::Circle as r31_mono::Shape>::area
t <&[r31_mono::Sq] as core::iter::traits::collect::IntoIterator>::into_iter
t <&[r31_mono::Rect] as core::iter::traits::collect::IntoIterator>::into_iter
t <&[r31_mono::Circle] as core::iter::traits::collect::IntoIterator>::into_iter
t <&[&dyn r31_mono::Shape] as core::iter::traits::collect::IntoIterator>::into_iter
(exit 0)
===== ./r31_mono =====
10 10
(exit 0)
```

- ★★★ **`total::<Sq>` · `total::<Rect>` · `total::<Circle>` — 세 벌.** 소스의 `total` 은 **하나**다. `total_dyn` 은 **한 벌**이다.
- ★★ **팽창은 내 함수에서 끝나지 않는다** — `total` 이 부른 **`slice::Iter::next`·`IntoIterator::into_iter` 도 타입마다 한 벌씩** 찍혔다
  (`<Sq>`·`<Rect>`·`<Circle>`·`<&dyn Shape>` 네 벌씩). **제네릭 하나가 제네릭을 부르면 곱으로 는다.** `total` 만 세면 **과소 집계**다.
- ★ **`-C symbol-mangling-version=v0`** 이 이 창을 연 열쇠다 — v0 은 **제네릭 인자를 심볼 이름에 담는다.** 기본 방식은 **해시**를 붙여 `nm -C` 로 봐도 **어느 타입 판인지 이름이 안 보인다.**

**같은 소스를 `opt-level=3` 으로.**

```text
===== rustc --edition 2021 -C opt-level=3 -C symbol-mangling-version=v0 r31_mono.rs =====
(exit 0)
===== nm -C r31_mono | awk '/r31_mono::/ {$1=""; print substr($0, 2)}' =====
t r31_mono::main
(exit 0)
===== ./r31_mono =====
10 10
(exit 0)
```

- ★★★ **`r31_mono::main` 하나만 남았다.** `total` 세 벌·`total_dyn`·`area`·이터레이터 전부 **심볼이 없다** — **`main` 안으로 녹았다**(인라인).
  **「타입마다 한 벌」은 `opt-level=0` 의 관찰**이었다. 벌 수는 언어가 아니라 **최적화기가 정한다.**
- ★ 출력(`10 10`)은 두 판이 같다 — **의미는 언어가 정하고, 모양은 컴파일러가 정한다.**

**같은 창으로 [29번 주제](../29-conversion-traits-from-into-tryfrom-asref-borrow/) (9)의 `impl Into<String>` 인자를 세면.**

```text
===== 소스: r29_into_arg.rs =====
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

- ★★ **`User::new` 가 opt 0 에서 네 벌, opt 3 에서 0 벌**(awk 가 한 줄도 못 찾고 `exit 0` — 규칙 18-A 의 빈 출력 블록).
  인자 위치 `impl Trait` 도 **이름 없는 제네릭**이라 단형화가 똑같이 적용된다([**32번 주제**](../32-impl-trait-argument-return-position-and-2024-capture/) (1)).

**`dyn` 판은 무엇을 대신 만드나 — IR 의 vtable.**

```text
===== rustc --edition 2021 -C opt-level=0 -C symbol-mangling-version=v0 --emit=llvm-ir -o r31_mono.ll r31_mono.rs =====
(exit 0)
===== grep -E '^@vtable' r31_mono.ll | c++filt =====
@vtable.0 = private unnamed_addr constant <{ [24 x i8], ptr, ptr, ptr }> <{ [24 x i8] c"\00\00\00\00\00\00\00\00\08\00\00\00\00\00\00\00\08\00\00\00\00\00\00\00", ptr @<std[836535f787e97d3]::rt::lang_start<()>::{closure#0} as core[2e27404414be4892]::ops::function::FnOnce<()>>::call_once::{shim:vtable#0}, ptr @std[836535f787e97d3]::rt::lang_start::<()>::{closure#0}, ptr @std[836535f787e97d3]::rt::lang_start::<()>::{closure#0} }>, align 8
@vtable.1 = private unnamed_addr constant <{ [24 x i8], ptr }> <{ [24 x i8] c"\00\00\00\00\00\00\00\00\08\00\00\00\00\00\00\00\08\00\00\00\00\00\00\00", ptr @<r31_mono[fecef943a53cb8bc]::Sq as r31_mono[fecef943a53cb8bc]::Shape>::area }>, align 8
@vtable.2 = private unnamed_addr constant <{ [24 x i8], ptr }> <{ [24 x i8] c"\00\00\00\00\00\00\00\00\08\00\00\00\00\00\00\00\08\00\00\00\00\00\00\00", ptr @<r31_mono[fecef943a53cb8bc]::Circle as r31_mono[fecef943a53cb8bc]::Shape>::area }>, align 8
@vtable.3 = private unnamed_addr constant <{ [24 x i8], ptr }> <{ [24 x i8] c"\00\00\00\00\00\00\00\00\10\00\00\00\00\00\00\00\08\00\00\00\00\00\00\00", ptr @<r31_mono[fecef943a53cb8bc]::Rect as r31_mono[fecef943a53cb8bc]::Shape>::area }>, align 8
(exit 0)
```

- **`@vtable.1`~`.3` 이 `Sq`·`Circle`·`Rect` 에 하나씩**(`@vtable.0` 은 `main` 을 부르는 런타임 쪽 것이다).
  각 표는 **`[24 x i8]`** 세 칸(8바이트씩)과 **`area` 함수 포인터 하나**다. 둘째 칸이 **`Rect` 만 `\10`(16), 나머지는 `\08`(8)** — 타입 크기로 읽히고,
  첫 칸(전부 0)은 드롭할 것이 없는 타입의 **드롭 자리**, 셋째 칸(`\08`)은 **정렬**로 읽힌다. (이 칸 해석은 **레이아웃이 구현 세부**라 이 판의 읽기다.)
- ★★ **`dyn` 은 「함수 한 벌 + 타입마다 표 하나」** 로 같은 일을 한다. 단형화는 「**타입마다 함수 한 벌**」이다.
  **팽창의 단위가 다르다** — 표는 포인터 몇 칸이고, 함수는 몸통 전체다.

**격자 — 인라인을 막고(`#[inline(never)]`), `Sq` 와 몸이 똑같은 `Tile` 을 더해, 판 넷으로.**

```bash
# r31_grid.sh
# r31_keep.rs 를 opt-level 넷으로 빌드하고, 함수 심볼의 벌 수와 바이트(nm -S)를 센다
for o in 0 1 2 3; do
  rustc --edition 2021 -C opt-level=$o -C symbol-mangling-version=v0 r31_keep.rs -o k$o
  echo "== opt-level=$o"
  nm -C -S -t d k$o | awk '
    /r31_keep::total::</ { g++; gb += $2; print "   " $2 + 0 "B  " $4 }
    /r31_keep::total_dyn/ { d++; db += $2; print "   " $2 + 0 "B  " $4 }
    / as r31_keep::Shape>::area/ { a++ }
    END { printf "   제네릭 total %d 벌 %dB · dyn total %d 벌 %dB · area 몸통 %d 벌\n", g, gb, d, db, a }'
done
```

```text
===== bash r31_grid.sh =====
== opt-level=0
   106B  r31_keep::total::<r31_keep::Sq>
   106B  r31_keep::total::<r31_keep::Rect>
   106B  r31_keep::total::<r31_keep::Tile>
   111B  r31_keep::total_dyn
   제네릭 total 3 벌 318B · dyn total 1 벌 111B · area 몸통 3 벌
== opt-level=1
   209B  r31_keep::total::<r31_keep::Sq>
   161B  r31_keep::total::<r31_keep::Rect>
   209B  r31_keep::total::<r31_keep::Tile>
   87B  r31_keep::total_dyn
   제네릭 total 3 벌 579B · dyn total 1 벌 87B · area 몸통 3 벌
== opt-level=2
   209B  r31_keep::total::<r31_keep::Sq>
   161B  r31_keep::total::<r31_keep::Rect>
   87B  r31_keep::total_dyn
   제네릭 total 2 벌 370B · dyn total 1 벌 87B · area 몸통 2 벌
== opt-level=3
   209B  r31_keep::total::<r31_keep::Sq>
   161B  r31_keep::total::<r31_keep::Rect>
   87B  r31_keep::total_dyn
   제네릭 total 2 벌 370B · dyn total 1 벌 87B · area 몸통 2 벌
(exit 0)
```

`r31_grid.sh` 가 빌드하는 소스(`r31_keep.rs`)는 이것이다.

```rust
// r31_keep.rs
// 인라인을 막고 세면 — 그리고 몸이 같은 두 벌은
use std::hint::black_box;

trait Shape {
    fn area(&self) -> f64;
}

struct Sq(f64);
struct Tile(f64); // ★ Sq 와 모양도 area 몸통도 같다
struct Rect(f64, f64);

impl Shape for Sq {
    fn area(&self) -> f64 {
        self.0 * self.0
    }
}
impl Shape for Tile {
    fn area(&self) -> f64 {
        self.0 * self.0
    }
}
impl Shape for Rect {
    fn area(&self) -> f64 {
        self.0 * self.1
    }
}

#[inline(never)]
fn total<T: Shape>(items: &[T]) -> f64 {
    let mut s = 0.0;
    for it in items {
        s += it.area();
    }
    s
}

#[inline(never)]
fn total_dyn(items: &[&dyn Shape]) -> f64 {
    let mut s = 0.0;
    for it in items {
        s += it.area();
    }
    s
}

fn main() {
    let a = [Sq(1.0), Sq(2.0)];
    let b = [Tile(1.0)];
    let c = [Rect(1.0, 2.0)];
    let g = total(black_box(&a)) + total(black_box(&b)) + total(black_box(&c));
    let d: [&dyn Shape; 3] = [&Sq(1.0), &Tile(1.0), &Rect(1.0, 2.0)];
    println!("{} {}", g, total_dyn(black_box(&d)));
}
```

- ★★★ **벌 수가 `3 → 3 → 2 → 2`** — `opt-level=2` 부터 **`total::<Tile>` 이 사라졌다.** `area` 몸통도 **3 → 2** 다.
  `Tile` 과 `Sq` 는 **둘 다 `f64` 하나이고 `area` 몸통이 같다** — 찍어 놓고 보니 **기계어가 같아서 하나로 합쳤다**(LLVM 의 함수 병합으로 보인다 — **패스 이름은 이 문서가 확인하지 않았다**).
  **`-Z` 옵션 없이도, 안정 판 기본 설정에서** 일어난다.
- ★★ **바이트는 벌 수와 따로 움직인다** — `total::<Sq>` 한 벌이 **106B(opt 0) → 209B(opt 1)** 로 **커졌다.** 최적화가 몸통을 키울 수도 있다(이유는 안 들여다봤다).
  그래서 제네릭 합계는 **318 → 579 → 370 → 370**, `dyn` 은 **111 → 87 → 87 → 87** 이다.
- ★★ **판정** — 이 격자의 **모든 판에서** 제네릭 쪽 합이 `dyn` 한 벌보다 **컸다**(318/111 · 579/87 · 370/87). **「코드 팽창」은 실재한다.**
  그러나 **몇 배인가는 판마다 다르고**(318 대 111 · 579 대 87 · 370 대 87 — **나눗셈은 안 했다**), **인라인되면 0 벌까지** 간다(`r31_mono` 의 opt 3).
  **한 판의 절댓값으로 「단형화는 N배 크다」고 말할 수 없다**(규칙 24).
- ★ **이 격자가 안 보는 것** — **`main` 이 커진 양**(인라인된 몸통은 `main` 에 들어간다)과 **실행 시간.** 크기 판단은 **바이너리 전체**를 봐야 끝난다 — 이 문서는 **함수 심볼**만 셌다.

### (9) ★★ 명목이냐 구조냐 — 네 언어를 한 줄에

**언제 쓰나** — 「제네릭 제약」이 언어마다 무엇을 **보고** 통과시키나를 비교할 때.

```text
   경계/제약이 무엇을 보나            정의 자리 몸통 검사     함수에 기본 타입 인자     근거
   Rust   이름 — impl … for 가 있어야   ✔ (1) E0599            ✘ not allowed here       이 문서 · TS 20 (6)
   C++    모양 — 식이 성립하나(콘셉트)   ✘ 인스턴스화 때 (7)①④  ✔ (7)⑤                  이 문서 (7)
   TS     모양 — 구조적 타입            ✔ TS2339               ✔                        TS 20 (1)·(4)
   Go     모양 — 메서드 집합(암묵 구현)  (Go 20 은 경계가 아니라 인터페이스 만족을 본다)      Go 20
   Python 모양(Protocol) · 이름(ABC)    (타입 검사기만 본다 — 런타임은 ABC 만)                Python 35
```

- ★★★ **Rust 의 경계는 이름으로 걸린다** — `Sq` 에 `area` 라는 메서드가 **있어도** `impl Shape for Sq` 가 **없으면** `T: Shape` 를 못 넘는다.
  [TS 20번](../../../ts/syntax/20-generic-constraints-and-defaults/) (6)이 `struct Loud` 에 `fmt` 메서드를 **두고도** `Display` 경계에서 E0277 을 받아 보인 것이 그 증거다.
  TS 는 `implements` 없이 **모양만 맞으면** 통과한다. **축은 「정의 자리냐 사용 자리냐」가 아니라 「이름이냐 모양이냐」다.**
- ★ **Go** — [Go 20번](../../../go/syntax/20-interface-declaration-and-implicit-implementation/)은 **`implements` 를 안 적는** 암묵 구현이다(모양). 그 편이 「Rust 는 `impl Trait for T` 를 적는다 — 빠진 메서드가 **선언 자리에서** 드러난다」고 대비했다.
  Go 의 제네릭(타입 파라미터·제약 인터페이스)은 Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **37번**이다(폴더 없음).
- ★ **Python** — [Python 35번](../../../python/syntax/35-abc-and-protocol/)은 **`Protocol` 은 모양, `ABC` 는 이름**이고 **`Protocol` 의 구조 판정은 타입 검사기만 본다**고 적는다.
  **한 언어 안에 두 축이 다 있는** 네 번째 점이다.
- ★ **C++ 콘셉트는 모양이다**((7)③). 그래서 「Rust 경계 = C++20 콘셉트」는 **검사 자리**(호출 자리)는 맞고 **무엇을 보나**(이름 대 모양)는 틀리다.

## 문법 — 형태와 규칙

```text
   형태

   fn f<T: A + B>(x: T)                       ← 인라인 경계, 여러 개는 +
   fn f<T>(x: T) where T: A + B,              ← where 절 — 같은 뜻
   fn f<T>(x: Vec<T>) where Vec<T>: Debug     ← ★ 왼쪽이 파라미터가 아니면 where 전용
   fn f<I: Iterator<Item = u8>>(it: I)        ← 연관 타입 고정
   fn f<I>(it: I) where I: Iterator, I::Item: Display   ← 연관 타입에 경계 (where 전용)
   fn f<T: Display + ?Sized>(x: &T)           ← 숨은 Sized 를 푼다 — str·[T]·dyn 을 받는다
   struct W<T = i32>(T);  trait Add<Rhs = Self>        ← 타입·트레이트에는 기본 인자 가능
   fn f<T = i32>(x: T)                        ✘ not allowed here (TS 20 (6) 인용)
   f::<Sq>(…)                                 ← 터보피시로 타입을 찍는다


   금지 사례 — 던져서 받은 것

   경계 없는 T 에 x.area()   (호출 0 개여도)      ✘ E0599  정의 자리
   경계를 못 채운 타입으로 호출                     ✘ E0277  호출 자리
   Iterator<Item = u8> 에 u16 이터레이터            ✘ E0271  연관 타입 불일치
   fn f<T: Display>(x: &T) 에 str                  ✘ E0277  implicit Sized bound
   -Z print-mono-items  (stable)                   ✘ only accepted on the nightly compiler
```

**규칙 불릿.**

- ★★ **몸통은 경계에 적힌 능력만 쓴다** — 호출이 없어도 정의 자리에서 검사된다((1)).
- ★ **인자는 호출 자리에서 경계와 대조된다** — Rust 는 **양쪽에서** 막는다((3)).
- **`where` 는 같은 뜻의 다른 자리**이고, **왼쪽이 타입 파라미터가 아닌 경계**는 `where` 에만 쓴다((2)·(4)).
- ★ **모든 타입 파라미터에 `Sized` 가 숨어 있다** — `?Sized` 로 푼다((5)).
- **기본 타입 인자는 타입·트레이트에만** — 함수에는 안 된다((6)).
- ★★★ **벌 수·바이트는 구현이 정한다** — `opt-level` 격자로만 말한다. 이 판에서 **3 → 0 벌**(인라인) · **3 → 2 벌**(병합)을 봤다((8)).

## 어디서 틀리나

### 1. ★★★ 「제네릭 함수는 타입마다 한 벌씩 바이너리에 들어간다」

**`opt-level=0` 의 관찰일 뿐이다**((8)). `opt-level=3` 에서는 **0 벌**(전부 인라인), 인라인을 막아도 몸이 같은 판은 **합쳐져 2 벌**이 됐다.
**언어가 정하는 것은 의미**이고 **벌 수는 최적화기가 정한다.**

### 2. ★★ 「MIR 을 보면 몇 벌인지 안다」

**MIR 은 단형화 이전이다**((8)). 제네릭 함수는 **언제나 한 벌**로 보인다. 벌 수는 **링크 뒤(심볼 표)나 LLVM IR** 에서 센다.

### 3. ★★ 「단형화는 빠르고 `dyn` 은 느리다」

**이 문서는 그것을 재지 않았다.** 잰 것은 **크기**다 — 제네릭 쪽이 이 격자에서 **언제나 컸다.** 속도는 **다른 실험**이다.
「제로 코스트」의 논증 자체는 [`언어-특성/README.md`](../../언어-특성/README.md) §6 이 정본이다.

### 4. ★★ 「`total` 만 세면 팽창을 안다」

**과소 집계다**((8)). `total` 이 부른 **std 제네릭(`Iter::next` 등)도 타입마다** 찍혔다. 팽창은 **호출 그래프를 따라 곱으로** 는다.

### 5. ★★ 「Rust 는 정의 자리, C++ 는 사용 자리에서 검사한다 — 그러니 C++20 콘셉트면 같다」

**반만 맞다**((7)·(9)). 콘셉트는 **검사 자리**를 호출로 당기지만 **보는 것은 모양**이다. Rust 경계는 **이름**(`impl`)을 본다.
그리고 Rust 도 **호출 자리에서 막는다**((3)) — 「정의 자리만」이 아니다.

### 6. ★ 「`&T` 로 받으면 무엇이든 받는다」

**숨은 `Sized` 때문에 `str` 을 못 받는다**((5)). `?Sized` 를 달아야 한다.

### 7. ★ 「경계가 길면 어쩔 수 없이 꺾쇠가 길어진다」

**`where` 로 뺀다**((2)). 그리고 `Vec<T>: Debug`·`I::Item: Display` 처럼 **`where` 에만 쓸 수 있는 경계**가 있다.

## 구현 세부사항 대 언어 보장

| 항목 | 무엇인가 | 근거 |
|---|---|---|
| 몸통이 **경계에 적힌 능력만** 쓰는 것 | ★ **언어 보장** — Reference(trait bounds) | (1)의 E0599 |
| 인자를 **호출 자리에서** 경계와 대조하는 것 | ★ **언어 보장** | (3)의 E0277 |
| 숨은 **`Sized`** 경계 | ★ **언어 보장** — Reference(`Sized`) | (5)의 note |
| 함수에 **기본 타입 인자 금지** | ★ **언어 보장** — 옛 판에서 받아 주던 것을 **린트로 거둬들이는 중**(`deny` 기본) | TS 20 (6) 인용 |
| **단형화라는 전략** 자체 | ★ **구현 전략** — Book 이 설명하고, Reference 는 **의미만** 정한다 | 머리말 |
| ★★★ **몇 벌이 생기나** | ★ **구현 세부** — `opt-level`·인라인·병합에 달렸다. **3 · 0 · 2** 를 봤다 | (8)의 격자 |
| ★★ **몸이 같은 두 벌이 합쳐지는** 것 | ★ **구현 세부** — `opt-level=2` 부터 이 판에서 관찰 | (8)의 격자 |
| 심볼 **바이트** | ★ **구현 세부** — 판마다 다르다(106 · 209) | (8)의 격자 |
| `dyn` 의 **vtable 모양**(드롭·크기·정렬·메서드) | ★ **구현 세부** — 레이아웃은 언어가 정하지 않는다 | (8)의 IR |
| `-C symbol-mangling-version=v0` | ★ **이 판의 안정 코드젠 옵션** — 기본값은 「바뀔 수 있다」고 rustc book 이 적는다 | 머리말 |
| C++ 템플릿이 **인스턴스화 때** 몸통을 검사하는 것 | ★ **C++ 표준의 성질**(의존 이름) — 두 컴파일러가 같았다. **진단 모양은 달랐다** | (7) |

## 언제 쓰고 언제 안 쓰나

- **제네릭 + 경계를 쓴다** — 호출마다 타입이 **컴파일 때 정해지고**, 그 타입의 능력을 **정적으로** 쓰고 싶을 때. 기본값이다.
- **`where` 를 쓴다** — 경계가 둘 이상이거나, **왼쪽이 파라미터가 아닌** 경계가 필요할 때.
- **`?Sized` 를 단다** — `&T`·`Box<T>` 로 받는 함수가 **`str`·슬라이스·`dyn`** 도 받아야 할 때.
- ★ **`dyn` 을 고른다** — 타입이 **실행 때 섞이거나**(한 `Vec` 에 여러 타입), **코드 크기가 중요**하고 타입 수가 많을 때.
  이 문서가 보인 것은 **크기 쪽 값**뿐이다 — 속도와의 거래는 목록의 **33번 주제**에서 정적·동적 디스패치 선택으로 다룬다.
- ★★ **코드 크기를 판단할 때는 판을 정하고 잰다** — `--release` 판(= `opt-level=3`)에서 심볼 표를 보라. `opt-level=0` 의 벌 수로 판단하지 않는다.
- ★ **제네릭 안에서 비제네릭 몸통을 떼어 낸다** — 경계가 필요 없는 큰 부분을 **보통 함수로 빼면** 그 부분은 한 벌만 찍힌다.
  std 자신이 그렇게 쓴다 — 설치된 std 소스에서 `fs::read` 를 뽑으면:

```python
# r31_inner.py
# 설치된 rust-docs 의 std 소스에서 fs::read 의 몸통을 뽑는다 — 제네릭 겉과 비제네릭 속
import html
import re
import subprocess

root = subprocess.run(["rustc", "--print", "sysroot"], capture_output=True, text=True).stdout.strip()
page = root + "/share/doc/rust/html/src/std/fs.rs.html"
lines = html.unescape(re.sub(r"<[^>]+>", "", open(page, encoding="utf-8").read())).split("\n")
start = next(i for i, l in enumerate(lines) if re.match(r"^\d+pub fn read<P: AsRef<Path>>", l))
for l in lines[start:start + 14]:
    m = re.match(r"^(\d+)(.*)$", l)
    print(f"{m.group(1):>4} {m.group(2)}")
    if m.group(2) == "}":
        break
```

```text
===== python3 r31_inner.py =====
 304 pub fn read<P: AsRef<Path>>(path: P) -> io::Result<Vec<u8>> {
 305     fn inner(path: &Path) -> io::Result<Vec<u8>> {
 306         let mut file = File::open(path)?;
 307         let size = file.metadata().map(|m| usize::try_from(m.len()).unwrap_or(usize::MAX)).ok();
 308         let mut bytes = Vec::try_with_capacity(size.unwrap_or(0))?;
 309         io::default_read_to_end(&mut file, &mut bytes, size)?;
 310         Ok(bytes)
 311     }
 312     inner(path.as_ref())
 313 }
(exit 0)
```

  겉 `read<P: AsRef<Path>>` 는 **한 줄**(312행 `inner(path.as_ref())`)이고, 몸통은 **`&Path` 를 받는 비제네릭 `inner`** 에 있다.
  `P` 마다 찍히는 것은 겉의 한 줄뿐이다(**이 문서는 그 벌 수를 세지 않았다** — 소스의 모양만 보였다).

## 핵심 문장

- ★★ **몸통은 경계만 믿고, 인자는 호출 자리에서 경계와 대조된다** — Rust 는 양쪽에서 막는다((1)·(3)).
- ★★ **경계는 이름으로 걸린다** — 모양이 맞아도 `impl` 이 없으면 못 넘는다. 이것이 TS·Go·C++ 콘셉트와 갈리는 축이다((9)).
- ★ **모든 타입 파라미터에는 `Sized` 가 숨어 있다**((5)).
- ★★★ **「타입마다 한 벌」은 `opt-level=0` 의 관찰이다** — 이 판에서 인라인은 **0 벌**, 병합은 **3 → 2 벌**을 만들었다((8)).
- ★★ **팽창은 실재하지만 배수는 판마다 다르다** — 크기는 재었고 속도는 재지 않았다((8)).

## 관련 자료

- ★★ [`compiler-pipeline/`](../../../../compiler-pipeline/) —
  **경계**: **컴파일 단계 일반**(어휘·구문 분석·AST·심볼 테이블·링커)은 **거기**다. 여기는 그 끝의 **심볼 표를 도구로 빌려** 벌 수를 셌을 뿐이다.
- ★★ [`언어-특성/README.md`](../../언어-특성/README.md) §6 — 제로 코스트 추상 —
  **경계**: 「**무엇이 0이고 무엇이 0이 아닌가**」와 「**청구서가 컴파일 시간·바이너리 크기로 옮겨 간다**」는 **논증은 거기**다.
  여기는 그 논증을 **다시 쓰지 않고**, 청구서의 **크기 쪽 한 칸을 실제로 세어 판 격자로** 보였다((8)).
- [**25번 주제** — 트레이트 정의·구현](../25-traits-definition-impl-default-methods-and-associated-types/) — 경계에 쓰는 트레이트의 정의 쪽. 25번 「용어 풀이」가 단형화를 한 줄로 예고했다.
- [**27번 주제** — `derive`](../27-derive-macros-debug-clone-partialeq-default-hash/) (4) — MIR 창의 첫 사용. 여기서는 **그 창이 못 보는 것**을 보였다((8)).
- [**29번 주제** — 변환 트레이트](../29-conversion-traits-from-into-tryfrom-asref-borrow/) (9) — `impl Into<String>` 인자의 「실」이 이 주제의 벌 수다.
- [**32번 주제** — `impl Trait`](../32-impl-trait-argument-return-position-and-2024-capture/) — 인자 자리 `impl Trait` 는 **이름 없는 제네릭**이라 여기의 단형화가 그대로 적용된다.
- 목록의 **33번 주제** — `dyn Trait` 와 객체 안전성. (8)의 vtable 이 거기서 깊어진다.
- ★★ TS 의 제네릭 제약 — [`ts/syntax/20-generic-constraints-and-defaults/`](../../../ts/syntax/20-generic-constraints-and-defaults/) (6).
  ★ **그 편이 rustc 1.92.0 으로 직접 던진 판**을 (3)·(6)·(9)에서 인용했다 — 이 문서는 **다시 재지 않았다.**
- Go 의 암묵 구현 — [`go/syntax/20-interface-declaration-and-implicit-implementation/`](../../../go/syntax/20-interface-declaration-and-implicit-implementation/) — 모양(구조) 쪽 셋째 점((9)).
- Python 의 `ABC`/`Protocol` — [`python/syntax/35-abc-and-protocol/`](../../../python/syntax/35-abc-and-protocol/) — 한 언어에 두 축이 다 있는 넷째 점((9)).
- Java 의 타입 소거 — [`java/syntax/19-type-erasure/`](../../../java/syntax/19-type-erasure/).
  ★ **대비(이 배치에서 안 던졌다)**: Java 제네릭은 **컴파일 뒤 타입 인자를 지워** **한 벌**만 남긴다 — Rust `opt-level=0` 의 「타입마다 한 벌」과 **정반대 끝**이다.
- C++ 의 템플릿·콘셉트 — C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md))의 **31번**(함수 템플릿)·**35번**(인스턴스화)·**36번**(콘셉트). 폴더가 없어 (7)에서 **직접 던졌다.**

## 용어 풀이

- **제네릭(generic)** — 타입을 파라미터로 받는 함수·타입. `fn total<T>(…)`.
- **트레이트 경계(trait bound)** — 타입 파라미터에 거는 능력 요구. `T: Shape`.
- **`where` 절** — 경계를 시그니처 뒤에 따로 적는 자리. 왼쪽이 파라미터가 아닌 경계도 쓸 수 있다.
- **연관 타입 경계** — `Iterator<Item = u8>` 처럼 연관 타입을 고정하거나, `I::Item: Display` 처럼 거기에 경계를 거는 것.
- **`Sized` / `?Sized`** — 컴파일 때 크기가 정해진 타입 / 그 요구를 **빼는** 표시.
- **단형화(monomorphization)** — 제네릭을 쓰인 타입마다 따로 찍는 구현 전략.
- **인라인(inline)** — 함수 호출 자리에 몸통을 **복사해 넣는** 최적화. 심볼이 사라질 수 있다.
- **함수 병합(function merging)** — 기계어가 같은 두 함수를 **하나로 합치는** 최적화.
- **심볼 표 / `nm`** — 바이너리 안 이름 목록과 그것을 찍는 도구. `-C` 는 이름 풀기, `-S` 는 크기.
- **v0 맨글링** — 제네릭 인자를 심볼 이름에 담는 Rust 맨글링 방식. `-C symbol-mangling-version=v0`.
- **MIR** — rustc 의 중간 표현. **단형화 이전**이다.
- **LLVM IR** — rustc 가 LLVM 에 넘기는 중간 표현. 여기서는 **단형화된 뒤**라 타입마다 따로 보인다.
- **vtable** — `dyn Trait` 가 가리키는 **메서드 표**. 드롭·크기·정렬·메서드 포인터가 든다.
- **명목적(nominal) / 구조적(structural)** — **선언(이름)** 으로 자격을 주느냐 / **모양** 으로 주느냐.
- **인스턴스화(instantiation)** — C++ 가 템플릿을 구체 타입으로 찍어 내는 것. 그때 몸통을 검사한다.

## 더 들어가면

- **`impl` 블록의 경계와 조건부 구현** — `impl<T: Display> Wrapper<T> { … }` 는 `T` 가 `Display` 일 때만 메서드가 생긴다.
- **고차 경계(HRTB)** — `where F: for<'a> Fn(&'a str)` — 수명에 대해 전칭하는 경계. 목록의 **34번 주제**(클로저) 근처에서 만난다.
- **`const` 제네릭** — `fn f<const N: usize>(a: [u8; N])` — 값으로 단형화된다. 벌 수 세기가 그대로 적용된다(이 문서는 안 셌다).
- **`-C codegen-units`·LTO** — 크레이트를 나눠 컴파일하는 단위와 링크 때 최적화. **벌 수·병합에 영향을 줄 수 있는 축**이다 — 이 격자는 기본값만 썼다.
- **`cargo bloat` 같은 도구** — 외부 크레이트라 이 문서는 안 썼다. `nm -C -S --size-sort` 가 같은 질문의 std 판이다.
