# rust/syntax/33 — `dyn Trait` 트레이트 객체와 객체 안전성 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Reference — Trait objects](https://doc.rust-lang.org/reference/types/trait-object.html) ·
> [Reference — Dyn compatibility](https://doc.rust-lang.org/reference/items/traits.html#dyn-compatibility) ·
> [Reference — Dynamically sized types](https://doc.rust-lang.org/reference/dynamically-sized-types.html) ·
> [Reference — Type layout](https://doc.rust-lang.org/reference/type-layout.html) ·
> [Reference — Default trait object lifetimes](https://doc.rust-lang.org/reference/lifetime-elision.html#default-trait-object-lifetimes) ·
> [Reference — Type coercions(unsized)](https://doc.rust-lang.org/reference/type-coercions.html#unsized-coercions).
> ★ 위 문서는 **이 머신의 `rust-docs`(1.92.0) 로컬 사본**을 열어 읽었다. 버전은 **그 사본의 `releases.md` 를 블록으로** 실었다((0)).
> **실행 검증** — 이 문서의 모든 출력·에러는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서
> **`rustc --edition 2021 <파일>.rs`** 로 돌려 받은 것이다(C++ 대비 블록은 `g++ 13.3.0` · `clang++ 18.1.3`).\
> ★★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다. 소스 펜스도 캡처가 찍었다.\
> ★★ **외부 크레이트를 하나도 쓰지 않았다**(네트워크 없음).
> ★★★ **이 문서는 속도를 한 번도 재지 않았다.** 「`dyn` 은 느리다」는 **이 문서의 주장이 아니다.** 센 것은 **바이트 수·vtable 칸·진단 코드**뿐이다.
> 제로 코스트 논증의 정본은 [`언어-특성/README.md`](../../언어-특성/README.md) §6 이고, **벌 수**는 [**31번 주제**](../31-generics-trait-bounds-where-and-monomorphization/) (8)이 이미 셌다.
> **버전** — `dyn` 키워드 **1.27.0** · `Self: Sized` 연관 타입을 `dyn` 에 안 적어도 됨 **1.72.0** · 자동 트레이트 쪽 업캐스팅 **1.78.0** · ★ **슈퍼트레이트 업캐스팅 1.86.0**. 전부 (0)의 블록이 근거다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

```text
===== rustc --version =====
rustc 1.92.0 (ded5c06cf 2025-12-08)
(exit 0)
===== cargo --version =====
cargo 1.92.0 (344c4567c 2025-10-21)
(exit 0)
===== rustup toolchain list =====
stable-x86_64-unknown-linux-gnu (active, default)
(exit 0)
===== g++ --version | head -1 =====
g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
(exit 0)
===== clang++ --version | head -1 =====
Ubuntu clang version 18.1.3 (1ubuntu1)
(exit 0)
===== python3 --version =====
Python 3.12.3
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| 안 흔들린다 | **포인터 크기**(`&dyn Shape` = 16 · `&Sq` = 8)와 `size_of_val`·`align_of_val` | ★ 같은 판·같은 타깃에서 고정이다. **16 은 언어 보장이 아니다**(§구현 세부 — Reference 가 「지금은 두 배, 기대지 마라」고 적는다) |
| 안 흔들린다 | LLVM IR 의 `@vtable.N` **줄** — 칸 수·순서·바이트 | 같은 판·같은 플래그에서 고정이다. 줄 안의 `[20af6a1668313135]` 같은 **크레이트 해시**도 재실행에서 같았다 |
| 안 흔들린다 | 격자 표(`r33_grid`)의 **칸마다 진단 코드**와 마지막 줄 `7 / 9` | 같은 판에서 고정이다 |
| 안 흔들린다 | 에러 번호·제목·`파일:줄:칸`·`note:`·종료 코드 | 같은 rustc 판에서 고정이다 |

★ 정규화 규칙은 **기본 넷**만 썼고 **하나도 걸리지 않았다**(제출 전 재대조).

## 한눈에 — 쉽게 말하면

**`dyn Trait` 는 「무슨 타입인지 모르는 값 + 그 값의 기능 목록표」를 한 쌍으로 들고 다니는 것이다.
목록표에는 칸이 정해져 있어서, 칸 하나에 함수 하나로 못 적히는 것(제네릭 메서드·`Self` 를 돌려주는 것·상수)이 있으면 그 트레이트는 `dyn` 이 못 된다.**

| 비유 | 실체 |
|---|---|
| 「**물건과 설명서를 한 봉투에**」 | ★★ **넓은 포인터(fat pointer)** — `&dyn Shape` 는 **데이터 포인터 + vtable 포인터**, 16바이트((1)) |
| 「**설명서의 목차**」 | ★★ **vtable** — **드롭 함수 · 크기 · 정렬 · 메서드들** 순서의 상수 표((2)) |
| 「**목차 한 칸에 한 줄로 못 적는 항목**」 | ★★★ **dyn 호환(객체 안전성) 위반** — E0038((3)) |
| 「**그 항목에 『실물 전용』 딱지**」 | ★★ **`where Self: Sized`** — 그 항목만 목차에서 뺀다. 단 **상수에는 못 붙인다**((4)) |
| 「**상위 자격 설명서로 바꿔 끼우기**」 | **업캐스팅** `&dyn Sub` → `&dyn Super` — 1.86 부터((5)) |
| 「**봉투 속 물건의 실명 확인**」 | **다운캐스트는 `Any` 로만** — `as` 로는 못 한다((7)) |

- ★★★ **판정은 한 줄이다 — 「vtable 한 칸에 함수 포인터 하나로 적을 수 있는가」.** 제네릭 메서드는 칸이 무한히 필요하고,
  `Self` 를 돌려주는 메서드는 크기를 모르는 값을 돌려줘야 하고, 연관 상수는 함수가 아니다. **E0038 의 `note:` 가 그 이유를 한 줄씩 말한다**((3)).
- ★★ **C++ 와 반대 자리에 표를 둔다** — C++ 는 **객체 안에** vptr 을 넣고(포인터 8바이트), Rust 는 **포인터 안에** vtable 포인터를 넣는다(객체 크기 그대로)((1)).

```text
   &dyn Shape 한 개 — 16 바이트 (이 판 · x86_64)

   ┌──────────── 데이터 포인터 (8) ──┐        ┌──── Sq(2.0) ────┐
   │  ────────────────────────────────────▶   │  f64            │  ← 객체는 8 바이트 그대로
   ├──────────── vtable 포인터 (8) ──┤        └─────────────────┘
   │  ──────────┐                    │
   └────────────│────────────────────┘
                ▼   @vtable (r33_vt 의 IR 에서 본 순서)
        ┌──────────────────────────────┬──────────────────────────────┐
        │  Sq                          │  Tagged { tag: String, w }   │
        ├──────────────────────────────┼──────────────────────────────┤
        │  drop     0 (할 일 없음)      │  drop_in_place::<Tagged>     │
        │  size     8                  │  size     32                 │
        │  align    8                  │  align    8                  │
        │  area     <Sq>::area         │  area     <Tagged>::area     │
        │  label    <Sq>::label        │  label    <Tagged>::label    │  ← impl 에서는 label 을 먼저 적었다
        └──────────────────────────────┴──────────────────────────────┘
          ★ 칸의 배치는 구현 세부다 — 언어는 「vtable 이 있다」까지만 말한다
```

> **트레이트 객체(trait object)** — `dyn Trait` 타입의 값. 구체 타입이 무엇인지 **지운** 값이라 크기를 모른다(DST). 언제나 `&`·`Box`·`Rc` 같은 포인터 뒤에 있다.\
> 예: `Box<dyn Shape>` 에 `Sq` 도 `Circle` 도 담긴다 — 한 `Vec` 에 섞어 담을 수 있다.

> **vtable** — 트레이트 객체가 가리키는 **함수 포인터 표**. 구체 타입 하나 × 트레이트 하나마다 한 장.\
> 예: `Sq` 를 `dyn Shape` 로 쓰면 `<Sq as Shape>::area` 의 주소가 적힌 표가 하나 생긴다.

> **dyn 호환(dyn compatible)** — 트레이트가 `dyn` 이 될 수 있는 성질. **옛 이름이 객체 안전성(object safety)** 이다(Reference 의 Note).\
> 예: `trait Clone` 은 `fn clone(&self) -> Self` 때문에 dyn 호환이 아니다.

## 이 주제가 답하려는 질문

1. ★★ **`dyn Trait` 는 메모리에서 어떤 모양인가** — 포인터는 몇 바이트이고, vtable 에는 무엇이 어느 순서로 드나((1)·(2)).
2. ★★★ **어떤 트레이트가 `dyn` 이 될 수 없나** — 컴파일러가 이유를 무엇이라 말하고, `where Self: Sized` 로 어디까지 구제되나((3)·(4)).
3. ★ **`dyn` 을 다른 `dyn` 이나 원래 타입으로 바꿀 수 있나** — 업캐스팅·트레이트 둘 더하기·수명·다운캐스트((5)·(6)·(7)).

★ [**25번 주제**](../25-traits-definition-impl-default-methods-and-associated-types/) (5)가 **E0038 두 이유**(`self` 없는 연관 함수 · 제네릭 메서드)와 `&dyn Greet` 16바이트까지 닿았다.
[**31번 주제**](../31-generics-trait-bounds-where-and-monomorphization/) (8)은 **정적 대 동적의 벌 수**를 셌다 — 제네릭 `total` 은 `opt-level` 에 따라 3·3·2·2벌, **`dyn` 판은 1벌**, IR 에 **타입마다 `@vtable` 하나**.
[**32번 주제**](../32-impl-trait-argument-return-position-and-2024-capture/) (8)은 **RPITIT 가 있으면 E0038** 을 봤다.
★★ **여기는 그 뒤** — 위반을 **한 격자에** 모으고, **`where Self: Sized` 로 풀리는 칸과 안 풀리는 칸**을 가르고, vtable 의 **칸 내용**을 읽는다. 벌 수는 다시 세지 않는다.

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ③ 격자다

★★★ **본체 창 — ③ 「트레이트 항목 하나씩 × 두 벌(그대로 / `where Self: Sized`)」 격자.** 격자 스크립트가 마지막 줄에 **갈린 칸 N / M** 을 찍는다.

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ① **`size_of`·`size_of_val`·`align_of_val`** | 포인터가 몇 바이트인가, vtable 이 **크기·정렬을 들고 있나**((1)) | 쓴다 |
| ② **LLVM IR 의 `@vtable` 상수**(`--emit=llvm-ir`) | vtable 칸의 **내용과 순서**((2)) | 쓴다 |
| ③ ★★★ **dyn 호환 위반 격자** | 항목마다 **E0038 인가**, `where Self: Sized` 를 붙이면 **풀리나**((3)·(4)) | ★ **본체** |
| ④ **E0038 전문의 `note:`** | 컴파일러가 **이유를 무엇이라 말하나**((3)) | 쓴다 — 「컴파일러가 규칙을 말한다」 |
| ⑤ **C++ `sizeof`** | 표를 **객체에 두느냐 포인터에 두느냐**((1)) | 대비로 쓴다 |
| 실행 시간 | 「`dyn` 은 느리다」 | ★ **부적용 — 재지 않는다.** 이 문서는 칸과 바이트만 센다 |
| 벌 수(`nm -C -S`) | 정적 대 동적의 **코드 크기** | ★ **부적용 — 31번 (8)이 정본.** 다시 세지 않았다 |

★ **「같은 질문을 다른 창으로」(제5의 상태)** — 「vtable 에 크기가 들어 있나」를 ② IR 로 물으면 **바이트 열**(`\08`·`\20`)로 답하고,
같은 질문을 ① `size_of_val(a)` 로 물으면 **8 · 16** 이라는 **실행 값**으로 답한다. **실행 값은 vtable 을 읽어서만 나올 수 있다**(데이터 포인터만으로는 크기를 모른다). 둘이 같은 사실을 가리킨다.
★ **이 창이 못 보는 것** — IR 의 칸 이름. IR 은 **바이트와 함수 이름**만 준다. 「첫 칸이 드롭, 둘째가 크기」는 **내 읽기**다(31번 (8)과 같은 단서).

**버전 — 설치된 `releases.md` 에서 뽑았다.**

```text
===== awk '/^Version 1\./{v=$2} /Box<Trait> == Box<dyn Trait>|Don.t require associated types with Self: Sized bounds|allow upcasting from .dyn Trait. to .dyn Trait \+ Auto.|Stabilize upcasting trait objects/{print v " | " $0}' "$(rustc --print sysroot)/share/doc/rust/html/releases.md" =====
1.86.0 | - [Stabilize upcasting trait objects to supertraits.](https://github.com/rust-lang/rust/pull/134367)
1.78.0 | - [`trait Trait: Auto {}`: allow upcasting from `dyn Trait` to `dyn Trait + Auto`](https://github.com/rust-lang/rust/pull/119338)
1.72.0 | - [Don't require associated types with Self: Sized bounds in `dyn Trait` objects](https://github.com/rust-lang/rust/pull/112319/)
1.27.0 |   `Box<Trait> == Box<dyn Trait>`.
(exit 0)
```

- **1.27.0** — `Box<Trait>` 를 `Box<dyn Trait>` 로 쓰는 `dyn` 문법. ★ **1.86.0** — 슈퍼트레이트로의 업캐스팅((5)).
- 1.72.0 · 1.78.0 은 가장자리 조항이다 — `where Self: Sized` 연관 타입을 `dyn` 에 안 적어도 되는 것, 자동 트레이트 쪽 업캐스팅.

### (1) ★★ 넓은 포인터 — 데이터 포인터 + vtable 포인터

**언제 쓰나** — 서로 다른 타입을 **한 컨테이너에** 담거나, 타입마다 함수를 찍지 않고 **한 벌로** 부르고 싶을 때.

```rust
// r33_basic.rs
// 한 Vec 에 서로 다른 타입을 담고 같은 메서드를 부른다
trait Shape {
    fn area(&self) -> f64;
    fn name(&self) -> String {
        String::from("shape")
    }
}

struct Sq(f64);
struct Circle(f64);

impl Shape for Sq {
    fn area(&self) -> f64 {
        self.0 * self.0
    }
    fn name(&self) -> String {
        String::from("sq")
    }
}
impl Shape for Circle {
    fn area(&self) -> f64 {
        3.0 * self.0 * self.0
    }
}

fn show(s: &dyn Shape) {
    println!("{} {}", s.name(), s.area());
}

fn main() {
    let v: Vec<Box<dyn Shape>> = vec![Box::new(Sq(2.0)), Box::new(Circle(1.0))];
    for s in &v {
        show(s.as_ref());
    }
    let c = Circle(2.0);
    show(&c);
}
```

```text
===== rustc --edition 2021 r33_basic.rs =====
(exit 0)
===== ./r33_basic =====
sq 4
shape 3
shape 12
(exit 0)
```

- `Vec<Box<dyn Shape>>` 에 `Sq` 와 `Circle` 이 섞여 들어갔다. `show` 는 **한 벌**이고 실행 때 표를 보고 고른다.
- ★ `Circle` 은 `name` 을 안 적어서 **기본 메서드 `shape`** 가 나왔다 — 기본 메서드도 vtable 의 한 칸이다([**25번 주제**](../25-traits-definition-impl-default-methods-and-associated-types/)).
- ★ `show(&c)` — `&Circle` 이 `&dyn Shape` 로 **강제 변환**(unsized coercion)됐다. Reference 의 강제 목록에 「`T` → `dyn U` (`T: U + Sized`, `U` 가 dyn 호환)」로 있다.

**포인터 하나의 크기.**

```rust
// r33_size.rs
// 포인터 하나의 크기 — 가리키는 타입에 따라
use std::fmt::Display;
use std::mem::{align_of_val, size_of, size_of_val};

trait Shape {
    fn area(&self) -> f64;
}
struct Sq(f64);
struct Rect(f64, f64);
impl Shape for Sq {
    fn area(&self) -> f64 {
        self.0 * self.0
    }
}
impl Shape for Rect {
    fn area(&self) -> f64 {
        self.0 * self.1
    }
}

fn main() {
    println!("&Sq              {}", size_of::<&Sq>());
    println!("&dyn Shape       {}", size_of::<&dyn Shape>());
    println!("Box<Sq>          {}", size_of::<Box<Sq>>());
    println!("Box<dyn Shape>   {}", size_of::<Box<dyn Shape>>());
    println!("&[u8]            {}", size_of::<&[u8]>());
    println!("&str             {}", size_of::<&str>());
    println!("*const dyn Shape {}", size_of::<*const dyn Shape>());
    println!("&dyn Display     {}", size_of::<&dyn Display>());
    println!("Option<&dyn Shape> {}", size_of::<Option<&dyn Shape>>());
    let a: &dyn Shape = &Sq(1.0);
    let b: &dyn Shape = &Rect(1.0, 2.0);
    println!("size_of_val  a={} b={}", size_of_val(a), size_of_val(b));
    println!("align_of_val a={} b={}", align_of_val(a), align_of_val(b));
    println!("area {}", a.area() + b.area());
}
```

```text
===== rustc --edition 2021 r33_size.rs =====
(exit 0)
===== ./r33_size =====
&Sq              8
&dyn Shape       16
Box<Sq>          8
Box<dyn Shape>   16
&[u8]            16
&str             16
*const dyn Shape 16
&dyn Display     16
Option<&dyn Shape> 16
size_of_val  a=8 b=16
align_of_val a=8 b=8
area 3
(exit 0)
```

- ★★ **`&Sq` 8 · `&dyn Shape` 16** — `&[u8]`·`&str` 도 16 이다(길이를 더 들고 있다). `Box` 도 `*const` 도 같다 — **넓어지는 것은 가리키는 쪽이 DST 일 때**다.
- ★ **`Option<&dyn Shape>` 도 16** — 데이터 포인터가 널이 될 수 없어 그 자리를 `None` 으로 쓴다(틈새 최적화).
- ★★★ **`size_of_val(a)=8`·`size_of_val(b)=16`** — `a`·`b` 는 **둘 다 `&dyn Shape`** 인데 답이 다르다.
  **컴파일러는 어느 타입인지 모르므로** 이 값은 **실행 때 vtable 에서 읽은 것**이다. 정렬(`align_of_val`)도 같다.

**`dyn Shape` 자체의 크기를 물으면.**

```rust
// r33_unsized.rs
// dyn Trait 자체의 크기를 물으면
trait Shape {
    fn area(&self) -> f64;
}

fn main() {
    let n = std::mem::size_of::<dyn Shape>();
    println!("{}", n);
}
```

```text
===== rustc --edition 2021 r33_unsized.rs =====
error[E0277]: the size for values of type `dyn Shape` cannot be known at compilation time
 --> r33_unsized.rs:7:33
  |
7 |     let n = std::mem::size_of::<dyn Shape>();
  |                                 ^^^^^^^^^ doesn't have a size known at compile-time
  |
  = help: the trait `Sized` is not implemented for `dyn Shape`
note: required by an implicit `Sized` bound in `std::mem::size_of`
 --> /rustc/ded5c06cf21d2b93bffd5d884aa6e96934ee4234/library/core/src/mem/mod.rs:335:1

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0277`.
(exit 1)
```

- ★★ **E0277 — the size for values of type `dyn Shape` cannot be known at compilation time.** `size_of::<T>()` 는 숨은 `T: Sized` 를 요구한다.
  **`dyn Shape` 는 크기가 없는 타입**이라는 것이 **언어 규칙**이다(Reference — DST). 크기는 **값마다** 다르고, 그래서 포인터가 vtable 을 들고 다닌다.

**C++ 는 표를 어디에 두나.**

```cpp
// r33_vptr.cpp
// C++ — 가상 함수가 있는 클래스의 크기와 포인터의 크기
#include <cstdio>

struct Plain {
    double w;
};
struct Shape {
    virtual double area() const { return 0; }
    virtual ~Shape() = default;
    double w = 0;
};

int main() {
    std::printf("sizeof(Plain)  %zu\n", sizeof(Plain));
    std::printf("sizeof(Shape)  %zu\n", sizeof(Shape));
    std::printf("sizeof(Shape*) %zu\n", sizeof(Shape*));
}
```

```text
===== g++ -std=c++20 -Wall -Wextra r33_vptr.cpp -o r33_vptr_g =====
(exit 0)
===== ./r33_vptr_g =====
sizeof(Plain)  8
sizeof(Shape)  16
sizeof(Shape*) 8
(exit 0)
===== clang++ -std=c++20 -Wall -Wextra r33_vptr.cpp -o r33_vptr_c =====
(exit 0)
===== ./r33_vptr_c =====
sizeof(Plain)  8
sizeof(Shape)  16
sizeof(Shape*) 8
(exit 0)
```

- ★★ **C++ 는 객체가 커진다** — `double` 하나인 `Plain` 은 8, 가상 함수가 있는 `Shape` 는 **16**(vptr 8 + `double` 8). **포인터 `Shape*` 는 8** 이다.
- ★★ **Rust 는 반대다** — `Sq(f64)` 는 **8 그대로**이고 **`&dyn Shape` 가 16** 이다. 표를 **값 안에 넣느냐, 포인터 옆에 들고 다니느냐**의 차이다.
  그래서 Rust 에서는 `Sq` 를 **`dyn` 으로 안 쓰는 자리에서 한 바이트도 안 낸다.** C++ 의 가상 호출 비용 논의는 C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md))의 **21번**이 정본이다(이 문서는 시간을 안 쟀다).

### (2) ★★ vtable 의 칸 — 드롭 · 크기 · 정렬 · 메서드

**언제 쓰나** — 「`dyn` 이 무엇을 대신 만드나」를 **글자로** 보고 싶을 때. [**31번 주제**](../31-generics-trait-bounds-where-and-monomorphization/) (8)은 **드롭할 것이 없는** 세 타입만 봤다 — 여기는 **드롭할 것이 있는 타입**과 **메서드 둘**을 더했다.

```rust
// r33_vt.rs
// vtable 에 무엇이 들어가나 — 드롭할 것이 있는 타입과 없는 타입
trait Shape {
    fn area(&self) -> f64;
    fn label(&self) -> usize;
}

struct Sq(f64);
struct Tagged {
    tag: String,
    w: f64,
}

impl Shape for Sq {
    fn area(&self) -> f64 {
        self.0 * self.0
    }
    fn label(&self) -> usize {
        0
    }
}
// impl 에서는 label 을 먼저 적었다
impl Shape for Tagged {
    fn label(&self) -> usize {
        self.tag.len()
    }
    fn area(&self) -> f64 {
        self.w
    }
}

fn run(v: &[Box<dyn Shape>]) -> f64 {
    v.iter().map(|s| s.area() + s.label() as f64).sum()
}

fn main() {
    let v: Vec<Box<dyn Shape>> = vec![
        Box::new(Sq(2.0)),
        Box::new(Tagged { tag: String::from("ab"), w: 1.0 }),
    ];
    println!("{}", run(&v));
}
```

```text
===== rustc --edition 2021 -C opt-level=0 -C symbol-mangling-version=v0 --emit=llvm-ir -o r33_vt.ll r33_vt.rs =====
(exit 0)
===== grep -E '^@vtable' r33_vt.ll | c++filt =====
@vtable.0 = private unnamed_addr constant <{ [24 x i8], ptr, ptr, ptr }> <{ [24 x i8] c"\00\00\00\00\00\00\00\00\08\00\00\00\00\00\00\00\08\00\00\00\00\00\00\00", ptr @<std[836535f787e97d3]::rt::lang_start<()>::{closure#0} as core[2e27404414be4892]::ops::function::FnOnce<()>>::call_once::{shim:vtable#0}, ptr @std[836535f787e97d3]::rt::lang_start::<()>::{closure#0}, ptr @std[836535f787e97d3]::rt::lang_start::<()>::{closure#0} }>, align 8
@vtable.1 = private unnamed_addr constant <{ [24 x i8], ptr, ptr }> <{ [24 x i8] c"\00\00\00\00\00\00\00\00\08\00\00\00\00\00\00\00\08\00\00\00\00\00\00\00", ptr @<r33_vt[20af6a1668313135]::Sq as r33_vt[20af6a1668313135]::Shape>::area, ptr @<r33_vt[20af6a1668313135]::Sq as r33_vt[20af6a1668313135]::Shape>::label }>, align 8
@vtable.2 = private unnamed_addr constant <{ ptr, [16 x i8], ptr, ptr }> <{ ptr @core[2e27404414be4892]::ptr::drop_in_place::<r33_vt[20af6a1668313135]::Tagged>, [16 x i8] c" \00\00\00\00\00\00\00\08\00\00\00\00\00\00\00", ptr @<r33_vt[20af6a1668313135]::Tagged as r33_vt[20af6a1668313135]::Shape>::area, ptr @<r33_vt[20af6a1668313135]::Tagged as r33_vt[20af6a1668313135]::Shape>::label }>, align 8
(exit 0)
```

- `@vtable.0` 은 `main` 을 부르는 **런타임 쪽 클로저**의 것이다(31번과 같다). **우리 것은 `.1`(Sq)·`.2`(Tagged)** 다.
- ★★ **`Sq` 의 표** — `[24 x i8]` 세 칸(`\00…` · `\08…` · `\08…`) + **`area` · `label`** 함수 포인터 둘.
  첫 칸이 **0** 이다 — **드롭할 것이 없는 타입**은 드롭 자리가 비어 있다.
- ★★★ **`Tagged` 의 표** — 첫 칸이 **`ptr @drop_in_place::<Tagged>`**(`String` 을 풀어야 하므로), 이어서 `[16 x i8]` 두 칸 —
  `c" \00…"` 의 **공백 글자는 바이트 `0x20` = 32**(`String` 24 + `f64` 8)이고 다음 칸 `\08` 이 **정렬 8** 이다.
  **(1)의 `size_of_val` 이 읽은 곳이 바로 이 칸**이다.
- ★★ **메서드 순서는 트레이트 선언 순서다** — `Tagged` 의 `impl` 에서는 **`label` 을 먼저** 적었는데 표에는 **`area` → `label`** 이다.
- ★ **이 칸 해석은 이 판의 읽기다** — Reference 는 vtable 에 「각 메서드의 구현을 가리키는 함수 포인터가 든다」까지만 적고, **드롭·크기·정렬의 배치는 적지 않는다**(§구현 세부).

### (3) ★★★ dyn 호환 위반 — 컴파일러가 이유를 말한다

**언제 쓰나** — `Box<dyn …>` 에 담으려는데 E0038 을 받았을 때. **`note:` 한 줄이 어느 항목이 왜인지를 짚는다.**

```rust
// r33_violations.rs
// 네 트레이트를 각각 dyn 으로 만들어 본다
trait A {
    fn pick<U>(&self, u: U) -> U;
}
trait B {
    fn dup(&self) -> Self;
}
trait C {
    const N: u32;
}
trait D: Sized {
    fn area(&self) -> f64;
}

struct S;
impl A for S {
    fn pick<U>(&self, u: U) -> U {
        u
    }
}
impl B for S {
    fn dup(&self) -> Self {
        S
    }
}
impl C for S {
    const N: u32 = 1;
}
impl D for S {
    fn area(&self) -> f64 {
        1.0
    }
}

fn main() {
    let _a: &dyn A = &S;
    let _b: &dyn B = &S;
    let _c: &dyn C = &S;
    let _d: &dyn D = &S;
}
```

```text
===== rustc --edition 2021 r33_violations.rs =====
error[E0038]: the trait `A` is not dyn compatible
  --> r33_violations.rs:36:18
   |
36 |     let _a: &dyn A = &S;
   |                  ^ `A` is not dyn compatible
   |
note: for a trait to be dyn compatible it needs to allow building a vtable
      for more information, visit <https://doc.rust-lang.org/reference/items/traits.html#dyn-compatibility>
  --> r33_violations.rs:3:8
   |
 2 | trait A {
   |       - this trait is not dyn compatible...
 3 |     fn pick<U>(&self, u: U) -> U;
   |        ^^^^ ...because method `pick` has generic type parameters
   = help: consider moving `pick` to another trait
   = help: only type `S` implements `A`; consider using it directly instead.

error[E0038]: the trait `B` is not dyn compatible
  --> r33_violations.rs:37:18
   |
37 |     let _b: &dyn B = &S;
   |                  ^ `B` is not dyn compatible
   |
note: for a trait to be dyn compatible it needs to allow building a vtable
      for more information, visit <https://doc.rust-lang.org/reference/items/traits.html#dyn-compatibility>
  --> r33_violations.rs:6:22
   |
 5 | trait B {
   |       - this trait is not dyn compatible...
 6 |     fn dup(&self) -> Self;
   |                      ^^^^ ...because method `dup` references the `Self` type in its return type
   = help: consider moving `dup` to another trait
   = help: only type `S` implements `B`; consider using it directly instead.

error[E0038]: the trait `C` is not dyn compatible
  --> r33_violations.rs:38:18
   |
38 |     let _c: &dyn C = &S;
   |                  ^ `C` is not dyn compatible
   |
note: for a trait to be dyn compatible it needs to allow building a vtable
      for more information, visit <https://doc.rust-lang.org/reference/items/traits.html#dyn-compatibility>
  --> r33_violations.rs:9:11
   |
 8 | trait C {
   |       - this trait is not dyn compatible...
 9 |     const N: u32;
   |           ^ ...because it contains this associated `const`
   = help: consider moving `N` to another trait
   = help: only type `S` implements `C`; consider using it directly instead.

error[E0038]: the trait `D` is not dyn compatible
  --> r33_violations.rs:39:18
   |
39 |     let _d: &dyn D = &S;
   |                  ^ `D` is not dyn compatible
   |
note: for a trait to be dyn compatible it needs to allow building a vtable
      for more information, visit <https://doc.rust-lang.org/reference/items/traits.html#dyn-compatibility>
  --> r33_violations.rs:11:10
   |
11 | trait D: Sized {
   |       -  ^^^^^ ...because it requires `Self: Sized`
   |       |
   |       this trait is not dyn compatible...
   = help: only type `S` implements `D`; consider using it directly instead.

error: aborting due to 4 previous errors

For more information about this error, try `rustc --explain E0038`.
(exit 1)
```

- ★★★ **E0038 네 건, `note:` 가 이유를 한 줄씩** —
  `A` 「**method `pick` has generic type parameters**」 · `B` 「**method `dup` references the `Self` type in its return type**」 ·
  `C` 「**it contains this associated `const`**」 · `D` 「**it requires `Self: Sized`**」.
- ★★ **네 이유가 한 문장으로 모인다** — 첫 `note:` 가 「**for a trait to be dyn compatible it needs to allow building a vtable**」라고 적는다.
  `pick::<u8>`·`pick::<String>` … 은 **칸이 무한히** 필요하고, `dup` 은 **크기 모르는 값**을 돌려줘야 하고, `N` 은 **함수가 아니고**, `D: Sized` 는 **`dyn D` 가 크기 없는 타입이라는 것과 모순**이다.
- ★ **`help:` 두 줄** — 「**consider moving `pick` to another trait**」와 「**only type `S` implements `A`; consider using it directly instead**」. **`D` 에는 앞 줄이 없다**(옮길 메서드가 없는 위반이다).

**격자 — 항목 하나씩, 두 벌로.** ★ 스크립트가 트레이트 `T` 에 항목 하나만 넣고 `Box<dyn T>` 를 만들어 본다. 오른쪽 열은 그 항목에 **`where Self: Sized`** 를 붙인 판이다.

```bash
# r33_grid.sh
# 트레이트 항목 하나씩을 두 벌(그대로 / `where Self: Sized` 를 붙여)로 넣고 dyn 을 만들어 본다
# 칸마다: 통과면 ok, 에러면 진단 코드(번호 없는 에러는 첫 줄 앞부분)
row() {  # row <이름> <트레이트 항목(끝 ; 없이)> <impl 몸통>
  local name=$1 item=$2 body=$3 out=() k
  for k in plain sized; do
    local w=""
    [ $k = sized ] && w=" where Self: Sized"
    printf 'trait T {\n    %s%s;\n}\nstruct S;\nimpl T for S {\n    %s\n}\nfn main() {\n    let _b: Box<dyn T> = Box::new(S);\n}\n' \
      "$item" "$w" "$body" >g.rs
    if rustc --edition 2021 -A warnings --crate-name g g.rs -o g 2>g.err; then
      out+=(ok)
    else
      out+=("$(grep -m1 -oE '^error(\[E[0-9]+\])?: .{0,28}' g.err | sed -E 's/^error\[(E[0-9]+)\].*/\1/')")
    fi
  done
  printf '%-10s %-46s | %-8s | %s\n' "$name" "$item" "${out[0]}" "${out[1]}"
  [ "${out[0]}" != "${out[1]}" ] && flips=$((flips + 1))
  total=$((total + 1))
}
flips=0 total=0
printf '%-10s %-46s | %-8s | %s\n' case item plain '+ where Self: Sized'
row control  'fn area(&self) -> f64'            'fn area(&self) -> f64 { 1.0 }'
row generic  'fn pick<U>(&self, u: U) -> U'     'fn pick<U>(&self, u: U) -> U { u }'
row ret_self 'fn dup(&self) -> Self'            'fn dup(&self) -> Self { S }'
row arg_self 'fn same(&self, o: &Self) -> bool' 'fn same(&self, _o: &Self) -> bool { true }'
row no_recv  'fn make() -> u32'                 'fn make() -> u32 { 1 }'
row rpitit   'fn items(&self) -> impl Iterator<Item = u32>' 'fn items(&self) -> impl Iterator<Item = u32> { 0..1 }'
row by_value 'fn consume(self) -> u32'          'fn consume(self) -> u32 { 1 }'
row gat      'type Out<U>'                      'type Out<U> = U;'
row const    'const N: u32'                     'const N: u32 = 1;'
rm -f g.rs g.err g
echo "cells that differ between the two columns: $flips / $total"
```

```text
===== bash r33_grid.sh =====
case       item                                           | plain    | + where Self: Sized
control    fn area(&self) -> f64                          | ok       | ok
generic    fn pick<U>(&self, u: U) -> U                   | E0038    | ok
ret_self   fn dup(&self) -> Self                          | E0038    | ok
arg_self   fn same(&self, o: &Self) -> bool               | E0038    | ok
no_recv    fn make() -> u32                               | E0038    | ok
rpitit     fn items(&self) -> impl Iterator<Item = u32>   | E0038    | ok
by_value   fn consume(self) -> u32                        | ok       | ok
gat        type Out<U>                                    | E0038    | ok
const      const N: u32                                   | E0038    | E0658
cells that differ between the two columns: 7 / 9
(exit 0)
```

- ★★★ **갈린 칸 7 / 9.** 위반 일곱(`generic`·`ret_self`·`arg_self`·`no_recv`·`rpitit`·`gat`·`const`)이 **왼쪽 열에서 전부 E0038** 이다.
  **`arg_self`**(`&Self` 인자)·**`gat`**(제네릭 연관 타입) 두 줄은 25번이 안 본 이유이고, **`rpitit`** 은 32번 (8)의 것이다.
- ★★ **`by_value`(`fn consume(self)`)는 처음부터 ok** — Reference 가 「**`self` 수신자는 `where Self: Sized` 를 함의한다**」고 적는다. **값으로 받는 메서드는 이미 「실물 전용」** 이다.
- ★★ **오른쪽 열은 `const` 하나만 ok 가 아니다** — 나머지 여섯은 `where Self: Sized` 로 **그 항목만 빠져** 통과했다((4)).

### (4) ★★ `where Self: Sized` — 그 항목만 목차에서 뺀다, 상수는 못 뺀다

**언제 쓰나** — 트레이트를 `dyn` 으로도 쓰고 싶은데 **`Self` 를 돌려주는 편의 메서드** 같은 것이 하나 끼어 있을 때.

**뺀 메서드를 `dyn` 에서 부르면.**

```rust
// r33_where_call.rs
// where Self: Sized 를 단 메서드 — dyn 으로 만들고, 그 메서드를 dyn 에서 부른다
trait Shape {
    fn area(&self) -> f64;
    fn scaled(&self, k: f64) -> Self
    where
        Self: Sized;
}

struct Sq(f64);
impl Shape for Sq {
    fn area(&self) -> f64 {
        self.0 * self.0
    }
    fn scaled(&self, k: f64) -> Self {
        Sq(self.0 * k)
    }
}

fn main() {
    let s = Sq(1.0);
    println!("{}", s.scaled(3.0).area());
    let d: &dyn Shape = &s;
    println!("{}", d.area());
    let e = d.scaled(2.0);
}
```

```text
===== rustc --edition 2021 r33_where_call.rs =====
error: the `scaled` method cannot be invoked on a trait object
  --> r33_where_call.rs:24:15
   |
 6 |         Self: Sized;
   |               ----- this has a `Sized` requirement
...
24 |     let e = d.scaled(2.0);
   |               ^^^^^^

error: aborting due to 1 previous error

(exit 1)
```

- ★★ **에러는 24행 `d.scaled(2.0)` 하나뿐이다** — 20행 `s.scaled(3.0)`(실물 `Sq`)과 22행 `let d: &dyn Shape = &s`(dyn 만들기)는 **통과했다.**
  `where Self: Sized` 는 **「그 메서드를 vtable 에 안 넣는다」** 는 뜻이고, 그래서 **`dyn` 에서는 그 메서드가 없다.**
- ★★ **이 에러에는 `E` 번호가 없다** — 「**the `scaled` method cannot be invoked on a trait object**」, `For more information…` 줄도 없다.
  32번 (7)의 `use<>` 에 이어 **번호 없는 에러**가 또 하나다.

**연관 상수에 붙이면.**

```rust
// r33_const_sized.rs
// 연관 상수에도 where Self: Sized 를 붙여 본다
trait T {
    const N: u32 where Self: Sized;
}
struct S;
impl T for S {
    const N: u32 = 1;
}
fn main() {
    let _b: Box<dyn T> = Box::new(S);
}
```

```text
===== rustc --edition 2021 r33_const_sized.rs =====
error[E0658]: generic const items are experimental
 --> r33_const_sized.rs:3:18
  |
3 |     const N: u32 where Self: Sized;
  |                  ^^^^^^^^^^^^^^^^^
  |
  = note: see issue #113521 <https://github.com/rust-lang/rust/issues/113521> for more information

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0658`.
(exit 1)
```

- ★★★ **E0658 — generic const items are experimental.** 상수에 `where` 절을 다는 문법 자체가 **불안정 기능**이다.
  그래서 격자의 `const` 줄은 **E0038 → E0658** 로 **코드만 바뀌고 여전히 막힌다.** Reference 의 조건도 「연관 상수가 **없어야** 한다」이고 예외 조항이 없다.
- ★ **고치는 법** — 상수를 **다른 트레이트로 옮기거나**(E0038 의 `help:` 가 권하는 쪽) **`fn n(&self) -> u32` 메서드로 바꾼다.**

### (5) 슈퍼트레이트와 업캐스팅 — 1.86 부터

**언제 쓰나** — `dyn Named` 를 받았는데 `&dyn Debug` 를 받는 함수에 넘기고 싶을 때.

```rust
// r33_super.rs
// 슈퍼트레이트가 있는 트레이트의 dyn — 슈퍼트레이트 메서드와 업캐스팅
use std::fmt::Debug;

trait Named: Debug {
    fn name(&self) -> String;
}

#[derive(Debug)]
struct Sq(f64);
impl Named for Sq {
    fn name(&self) -> String {
        format!("sq{}", self.0)
    }
}

fn show_debug(d: &dyn Debug) {
    println!("debug {:?}", d);
}

fn main() {
    let n: &dyn Named = &Sq(2.0);
    println!("{} {:?}", n.name(), n);
    let d: &dyn Debug = n;
    show_debug(d);
    let b: Box<dyn Named> = Box::new(Sq(3.0));
    let bd: Box<dyn Debug> = b;
    println!("{:?}", bd);
}
```

```text
===== rustc --edition 2021 r33_super.rs =====
(exit 0)
===== ./r33_super =====
sq2 Sq(2.0)
debug Sq(2.0)
Sq(3.0)
(exit 0)
```

- ★ **`n` 으로 `{:?}` 가 된다** — 트레이트 객체는 **기반 트레이트와 그 슈퍼트레이트를 구현한다**(Reference). `Named: Debug` 이므로 `dyn Named` 의 vtable 에 `Debug` 칸도 있다.
- ★★ **`let d: &dyn Debug = n;` 과 `Box<dyn Named>` → `Box<dyn Debug>` 가 통과했다** — **트레이트 업캐스팅**이다.
  Reference 의 강제 목록에 「**`dyn T` → `dyn U`, `U` 가 `T` 의 슈퍼트레이트일 때**」가 있고, (0)의 블록이 **1.86.0** 에 안정됐다고 적는다. 릴리스 노트대로라면 **1.85 이하에서는 안 된다** — ★ 이 문서는 옛 판을 돌려 보지 않았다(툴체인이 1.92 하나뿐이다).

### (6) `dyn` 에 트레이트를 둘 — 그리고 기본 수명 `'static`

**언제 쓰나** — `Display` 와 `Debug` 를 **둘 다** 쓰는 값을 담고 싶을 때, 그리고 **빌린 값**을 `Box<dyn …>` 에 넣을 때.

```rust
// r33_two.rs
// dyn 에 트레이트 둘을 더하기
use std::fmt::{Debug, Display};

fn main() {
    let a: Box<dyn Display + Send> = Box::new(1);
    println!("{}", a);
    let b: Box<dyn Display + Debug> = Box::new(2);
    println!("{}", b);
}
```

```text
===== rustc --edition 2021 r33_two.rs =====
error[E0225]: only auto traits can be used as additional traits in a trait object
 --> r33_two.rs:7:30
  |
7 |     let b: Box<dyn Display + Debug> = Box::new(2);
  |                    -------   ^^^^^ additional non-auto trait
  |                    |
  |                    first non-auto trait
  |
  = help: consider creating a new trait with all of these as supertraits and using that trait here instead: `trait NewTrait: std::fmt::Display + Debug {}`
  = note: auto-traits like `Send` and `Sync` are traits that have special properties; for more information on them, visit <https://doc.rust-lang.org/reference/special-types-and-traits.html#auto-traits>

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0225`.
(exit 1)
```

- ★★ **E0225 — only auto traits can be used as additional traits in a trait object.** `dyn Display + Send`(5행)는 통과했고 `dyn Display + Debug`(7행)만 막혔다.
  Reference 가 적는 대로 **자동 트레이트가 아닌 트레이트는 하나만** 올 수 있다 — vtable 이 **한 장**이기 때문이다.

**`help:` 대로 — 두 트레이트를 슈퍼트레이트로 둔 새 트레이트.**

```rust
// r33_two_help.rs
// help: 가 권한 대로 — 두 트레이트를 슈퍼트레이트로 둔 새 트레이트
use std::fmt::{Debug, Display};

trait NewTrait: Display + Debug {}

fn main() {
    let b: Box<dyn NewTrait> = Box::new(2);
    println!("{} {:?}", b, b);
}
```

```text
===== rustc --edition 2021 r33_two_help.rs =====
error[E0277]: the trait bound `{integer}: NewTrait` is not satisfied
 --> r33_two_help.rs:7:32
  |
7 |     let b: Box<dyn NewTrait> = Box::new(2);
  |                                ^^^^^^^^^^^ the trait `NewTrait` is not implemented for `{integer}`
  |
help: this trait has no implementations, consider adding one
 --> r33_two_help.rs:4:1
  |
4 | trait NewTrait: Display + Debug {}
  | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  = note: required for the cast from `Box<{integer}>` to `Box<dyn NewTrait>`

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0277`.
(exit 1)
```

- ★★★ **처방대로 했더니 다시 에러다 — E0277 `{integer}: NewTrait` is not satisfied.** `help:` 는 **트레이트 선언만** 알려 줬고, **아무 타입도 그것을 구현하지 않는다**
  (이번 `help:` 가 「**this trait has no implementations, consider adding one**」라고 스스로 말한다). **첫 처방은 반쪽이었다.**

**담요 구현을 더하면.**

```rust
// r33_two_blanket.rs
// 새 트레이트에 담요 구현을 더하면
use std::fmt::{Debug, Display};

trait NewTrait: Display + Debug {}
impl<T: Display + Debug> NewTrait for T {}

fn main() {
    let b: Box<dyn NewTrait> = Box::new(2);
    println!("{} {:?}", b, b);
}
```

```text
===== rustc --edition 2021 r33_two_blanket.rs =====
(exit 0)
===== ./r33_two_blanket =====
2 2
(exit 0)
```

- ★★ **`impl<T: Display + Debug> NewTrait for T {}` 한 줄로 통과**(`2 2`). **두 트레이트를 가진 모든 타입이 자동으로 `NewTrait`** 이 된다.

**빌린 값을 `Box<dyn Display>` 에 넣으면.**

```rust
// r33_static.rs
// Box<dyn Display> 에 빌린 값을 넣는 함수
use std::fmt::Display;

fn keep(v: &mut Vec<Box<dyn Display>>, s: &str) {
    v.push(Box::new(s));
}

fn main() {
    let mut v = Vec::new();
    let owned = String::from("hi");
    keep(&mut v, &owned);
    println!("{}", v.len());
}
```

```text
===== rustc --edition 2021 r33_static.rs =====
error: lifetime may not live long enough
 --> r33_static.rs:5:12
  |
4 | fn keep(v: &mut Vec<Box<dyn Display>>, s: &str) {
  |                                           - let's call the lifetime of this reference `'1`
5 |     v.push(Box::new(s));
  |            ^^^^^^^^^^^ coercion requires that `'1` must outlive `'static`

error: aborting due to 1 previous error

(exit 1)
```

- ★★★ **「lifetime may not live long enough」 — `` coercion requires that `'1` must outlive `'static` ``.** 시그니처에는 `'static` 이 한 글자도 없다.
  **`Box<dyn Display>` 는 `Box<dyn Display + 'static>` 이다** — Reference 의 기본 트레이트 객체 수명 규칙(「`Box<T>` 는 `T` 에 수명 경계가 없으므로 `'static`」)이다.
- ★ **이 에러에도 `E` 번호가 없다.** `help:` 도 없다.

```rust
// r33_static_fix.rs
// 트레이트 객체의 수명을 적어 준다
use std::fmt::Display;

fn keep<'a>(v: &mut Vec<Box<dyn Display + 'a>>, s: &'a str) {
    v.push(Box::new(s));
}

fn main() {
    let owned = String::from("hi");
    let mut v = Vec::new();
    keep(&mut v, &owned);
    println!("{} {}", v.len(), v[0]);
}
```

```text
===== rustc --edition 2021 r33_static_fix.rs =====
(exit 0)
===== ./r33_static_fix =====
1 hi
(exit 0)
```

- ★ **`Box<dyn Display + 'a>` 로 적으면 통과**(`1 hi`). 다만 `owned` 를 `v` **보다 먼저** 선언했다. 거꾸로 두면.

```rust
// r33_static_order.rs
// 트레이트 객체의 수명을 적고, 선언 순서를 거꾸로 둔다
use std::fmt::Display;

fn keep<'a>(v: &mut Vec<Box<dyn Display + 'a>>, s: &'a str) {
    v.push(Box::new(s));
}

fn main() {
    let mut v = Vec::new();
    let owned = String::from("hi");
    keep(&mut v, &owned);
    println!("{} {}", v.len(), v[0]);
}
```

```text
===== rustc --edition 2021 r33_static_order.rs =====
error[E0597]: `owned` does not live long enough
  --> r33_static_order.rs:11:18
   |
10 |     let owned = String::from("hi");
   |         ----- binding `owned` declared here
11 |     keep(&mut v, &owned);
   |                  ^^^^^^ borrowed value does not live long enough
12 |     println!("{} {}", v.len(), v[0]);
13 | }
   | -
   | |
   | `owned` dropped here while still borrowed
   | borrow might be used here, when `v` is dropped and runs the `Drop` code for type `Vec`
   |
   = note: values in a scope are dropped in the opposite order they are defined

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0597`.
(exit 1)
```

- ★ **E0597** — 이제 `v` 가 **`owned` 를 빌린 값을 품으므로** 드롭 순서가 걸린다(`note:` 「values in a scope are dropped in the opposite order they are defined」).
  **`'static` 일 때는 없던 제약**이 수명을 적는 순간 생긴다 — `'static` 기본값이 **이 부담을 대신 지고 있었던** 셈이다.

### (7) 다운캐스트는 `Any` 로만 — `as` 로는 못 한다

**언제 쓰나** — `dyn` 으로 받은 값이 **실제로 어떤 타입인지** 가려야 할 때.

```rust
// r33_cast.rs
// dyn Shape 를 원래 타입으로 as 캐스팅해 보면
trait Shape {
    fn area(&self) -> f64;
}
struct Sq(f64);
impl Shape for Sq {
    fn area(&self) -> f64 {
        self.0 * self.0
    }
}

fn main() {
    let d: &dyn Shape = &Sq(2.0);
    let s = d as &Sq;
    println!("{}", s.0);
}
```

```text
===== rustc --edition 2021 r33_cast.rs =====
error[E0605]: non-primitive cast: `&dyn Shape` as `&Sq`
  --> r33_cast.rs:14:13
   |
14 |     let s = d as &Sq;
   |             ^^^^^^^^ an `as` expression can only be used to convert between primitive types or to coerce to a specific trait object

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0605`.
(exit 1)
```

- ★★ **E0605 — non-primitive cast: `&dyn Shape` as `&Sq`.** `as` 는 **원시 타입 사이**나 **트레이트 객체로 강제**할 때만 쓴다. **반대 방향(`dyn` → 구체)은 없다.**

```rust
// r33_any.rs
// dyn 에서 원래 타입을 되찾기 — Any 로
use std::any::Any;

fn describe(x: &dyn Any) -> String {
    if let Some(n) = x.downcast_ref::<i32>() {
        format!("i32 {}", n)
    } else if let Some(s) = x.downcast_ref::<String>() {
        format!("String {}", s)
    } else {
        String::from("other")
    }
}

fn main() {
    println!("{}", describe(&7));
    println!("{}", describe(&String::from("hi")));
    println!("{}", describe(&1.5));
    let b: Box<dyn Any> = Box::new(9u8);
    match b.downcast::<u8>() {
        Ok(v) => println!("u8 {}", v),
        Err(_) => println!("not u8"),
    }
}
```

```text
===== rustc --edition 2021 r33_any.rs =====
(exit 0)
===== ./r33_any =====
i32 7
String hi
other
u8 9
(exit 0)
```

- ★ **`&dyn Any` 의 `downcast_ref::<i32>()`** 는 `Option` 을, **`Box<dyn Any>` 의 `downcast::<u8>()`** 는 `Result` 를 돌려준다. **실패는 값으로 온다**(`other`).
- ★ **경계** — `Any` 는 **`'static` 타입만** 구현한다(std 문서). 빌린 것이 든 타입은 다운캐스트할 수 없다. **`dyn Shape` 에서 바로 내려가는 길은 없고**, 필요하면 트레이트에 `fn as_any(&self) -> &dyn Any` 를 두는 관용구를 쓴다(이 문서는 던지지 않았다).

## 문법 — 형태와 규칙

```text
   형태

   &dyn Shape · Box<dyn Shape> · Rc<dyn Shape>      ← 언제나 포인터 뒤에. 포인터가 넓어진다
   Box<dyn Shape + Send>                             ← 자동 트레이트는 더할 수 있다
   Box<dyn Shape + 'a>                               ← 수명을 적는다. 안 적으면 Box 에서는 'static
   fn scaled(&self) -> Self where Self: Sized;       ← 이 메서드만 vtable 에서 뺀다
   trait Named: Debug { … }  →  &dyn Named as &dyn Debug   ← 업캐스팅(1.86~)
   let x: &dyn Any = &7;  x.downcast_ref::<i32>()    ← 다운캐스트는 Any 로


   금지 사례 — 던져서 받은 것

   제네릭 메서드 · Self 반환 · &Self 인자 · self 없는 연관 함수     ✘ E0038
   RPITIT · 제네릭 연관 타입 · 연관 상수 · trait T: Sized              ✘ E0038
   연관 상수에 where Self: Sized                                      ✘ E0658  "generic const items are experimental"
   where Self: Sized 로 뺀 메서드를 dyn 에서 호출                     ✘ (번호 없음) "cannot be invoked on a trait object"
   dyn Display + Debug                                               ✘ E0225
   Box<dyn Display> 에 &str 을 넣는 함수                              ✘ (번호 없음) "must outlive 'static"
   &dyn Shape as &Sq                                                 ✘ E0605
   size_of::<dyn Shape>()                                            ✘ E0277
```

**규칙 불릿.**

- **트레이트 객체는 크기가 없는 타입이다** — 포인터 뒤에만 오고, 포인터는 **데이터 + vtable**((1)).
- ★★★ **vtable 한 칸에 함수 하나로 못 적는 항목이 있으면 E0038** — 제네릭 메서드 · `Self` 반환/인자 · 수신자 없는 함수 · RPITIT · GAT · 연관 상수 · `Self: Sized` 슈퍼트레이트((3)).
- ★★ **`where Self: Sized` 는 그 항목을 뺀다** — 메서드·연관 함수·GAT 는 풀리고 **상수는 못 푼다**(E0658)((4)).
- ★ **자동 트레이트가 아닌 트레이트는 하나만**(E0225) — 둘이 필요하면 **슈퍼트레이트 둘을 가진 새 트레이트 + 담요 구현**((6)).
- ★ **`Box<dyn T>` 의 수명은 기본 `'static`**((6)) · **업캐스팅은 1.86~**((5)) · **다운캐스트는 `Any`**((7)).

## 어디서 틀리나

### 1. ★★★ 「`where Self: Sized` 를 붙이면 무엇이든 `dyn` 이 된다」

**연관 상수는 안 된다**((4)). 붙이는 순간 **E0658**(불안정 문법)이고, 격자의 `const` 줄이 **E0038 → E0658** 로 코드만 바뀐다.
★ 그리고 **뺀 메서드는 `dyn` 에서 없다** — 불러 보면 **번호 없는 에러**다.

### 2. ★★ 「`&dyn Trait` 가 16바이트인 것은 언어가 보장한다」

**Reference 두 쪽의 말이 다르다.** DST 절은 「**두 배 크기**」라고 적고, Type layout 절은 「**적어도 포인터 크기**이다. 지금은 모든 DST 포인터가 `usize` 두 배이지만 **기대지 마라**」라고 적는다.
**보장은 뒤쪽이 더 정확하다** — 16 은 **이 판의 구현**으로 읽는다((1)·§구현 세부).

### 3. ★★ 「`dyn` 은 객체에 vptr 을 넣는다(C++ 처럼)」

**Rust 는 포인터에 넣는다**((1)). `Sq(f64)` 는 `dyn` 으로 써도 **8바이트 그대로**이고 커지는 것은 **포인터**다. C++ 는 가상 함수가 하나라도 있으면 **모든 객체**가 커진다(8 → 16).

### 4. ★★ 「`dyn A + B` 로 트레이트 둘을 쓸 수 있다」

**E0225** — 둘째가 **자동 트레이트**여야 한다((6)). ★ 그리고 **`help:` 대로 새 트레이트만 만들면 다시 E0277** 이다 — **담요 구현까지** 해야 끝난다.

### 5. ★ 「`Box<dyn Display>` 는 아무 값이나 담는다」

**`'static` 값만** 담는다((6)). 빌린 `&str` 을 넣으면 **번호 없는 수명 에러**다. `+ 'a` 를 적어야 한다.

### 6. ★ 「`dyn Trait` 를 원래 타입으로 `as` 캐스팅하면 된다」

**E0605**((7)). 내려가는 길은 **`Any`** 뿐이고, `Any` 는 **`'static` 타입**만 된다.

### 7. ★ 「`dyn` 은 느리다」

**이 문서는 재지 않았다.** 센 것은 — **포인터 16바이트**, **vtable 한 장에 칸 다섯**, 31번의 **「함수 한 벌 + 타입마다 표 하나」**.
「느린가」는 **인라인이 막히는가**의 문제이고 그것은 벤치마크와 판 격자로만 말할 수 있다(규칙 24). 논증의 정본은 [`언어-특성/README.md`](../../언어-특성/README.md) §6.

## 구현 세부사항 대 언어 보장

| 항목 | 무엇인가 | 근거 |
|---|---|---|
| 트레이트 객체가 **크기 없는 타입**(DST)인 것 | ★ **언어 보장** — Reference(Trait objects · DST) | (1)의 E0277 |
| 포인터에 **데이터 포인터 + vtable 포인터**가 드는 것 | ★ **언어 보장** — Reference(Trait objects) 「각 포인터는 … vtable 을 포함한다」 | (1)·(2) |
| ★★ 넓은 포인터가 **정확히 16바이트**(`usize` 두 배)인 것 | ★ **구현 세부** — Type layout 은 「**적어도** 포인터 크기」만 보장하고 「지금은 두 배, 기대지 마라」 | (1)의 `size_of` |
| ★★ **vtable 의 칸 배치**(드롭 · 크기 · 정렬 · 메서드 순서) | ★ **구현 세부** — Reference 는 「메서드 구현을 가리키는 함수 포인터」까지만 적는다 | (2)의 IR |
| 메서드 칸이 **트레이트 선언 순서**인 것 | ★ **이 판의 관찰** — `impl` 순서를 바꿔 봤다 | (2)의 IR |
| ★★★ **dyn 호환 조건 목록** | ★ **언어 보장** — Reference(Dyn compatibility) | (3)의 격자 |
| `self` 수신자가 `Self: Sized` 를 **함의**하는 것 | ★ **언어 보장** — Reference 의 괄호 | (3)의 `by_value` |
| 연관 상수의 `where` 절이 **불안정**인 것 | ★ **이 판의 상태** — E0658, 추적 이슈 #113521 | (4) |
| 비자동 트레이트는 **하나만** | ★ **언어 보장** — Reference(Trait objects) | (6)의 E0225 |
| `Box<dyn T>` 의 기본 수명 **`'static`** | ★ **언어 보장** — Reference(Default trait object lifetimes) | (6) |
| 슈퍼트레이트 **업캐스팅** | ★ **언어 보장 — 1.86 부터**(Reference 의 unsized coercion 목록 · 릴리스 노트) | (5) |
| (4)·(6)의 에러에 **번호가 없는** 것 · `help:` 문구 | ★ **구현 세부** — 진단 등록 여부와 제안 | (4)·(6) |
| C++ 의 vptr 이 **객체 안에** 있는 것 | ★ **C++ 구현(Itanium ABI)의 관찰** — C++ 표준은 vtable 을 말하지 않는다 | (1)의 C++ 블록 |

## 언제 쓰고 언제 안 쓰나

- ★ **`dyn` 을 쓴다** — 타입이 **실행 때 섞일 때**(한 `Vec` 에 여러 타입, 플러그인, 콜백 목록), **코드 크기**를 한 벌로 묶고 싶을 때(31번 (8)).
- **제네릭을 쓴다** — 타입이 **컴파일 때 정해지고** 섞이지 않을 때. `Self` 반환·제네릭 메서드가 필요한 트레이트는 **애초에 제네릭 전용**이다.
- ★★ **트레이트를 설계할 때 dyn 호환을 먼저 정한다** — `dyn` 으로 쓸 계획이면 편의 메서드(`Self` 반환·제네릭)에 **`where Self: Sized`** 를 달고, **상수는 넣지 않는다**((4)).
- ★ **트레이트 둘이 필요하면** 슈퍼트레이트 둘을 가진 새 트레이트 + **담요 구현**((6)).
- ★ **빌린 것을 담을 거면 `+ 'a`** 를 적는다((6)). **다운캐스트가 자주 필요하면** `dyn` 보다 **`enum`** 이 맞는 자리인지 먼저 본다.

## 핵심 문장

- ★★★ **dyn 호환은 「vtable 한 칸에 함수 하나로 적을 수 있나」다** — E0038 의 `note:` 가 이유를 한 줄씩 말한다((3)).
- ★★ **`where Self: Sized` 는 항목을 vtable 에서 뺀다** — 격자 **7 / 9** 칸이 갈렸고, **상수만** E0658 로 여전히 막혔다((3)·(4)).
- ★★ **Rust 는 표를 포인터에 둔다** — 객체는 그대로, `&dyn` 이 16(이 판). C++ 는 객체가 커진다((1)).
- ★ **vtable 은 드롭 · 크기 · 정렬 · 메서드**(이 판의 배치) — `size_of_val` 이 거기서 읽는다((2)).
- ★ **`Box<dyn T>` 는 `'static`**, **비자동 트레이트는 하나**, **업캐스팅은 1.86~**, **다운캐스트는 `Any`**((5)·(6)·(7)).

## 관련 자료

- [**25번 주제** — 트레이트](../25-traits-definition-impl-default-methods-and-associated-types/) (5) — E0038 의 **두 이유**와 `&dyn Greet` 16바이트. **경계**: 여기는 그 두 이유를 **아홉 줄 격자**로 넓히고 `where Self: Sized` 의 구제 범위를 셌다.
- ★★ [**31번 주제** — 제네릭·단형화](../31-generics-trait-bounds-where-and-monomorphization/) (8) — **정적 대 동적의 벌 수·바이트**. **경계**: 벌 수는 **거기**가 정본이고 여기는 다시 세지 않았다. 여기는 **vtable 칸 내용**을 더했다.
- [**32번 주제** — `impl Trait`](../32-impl-trait-argument-return-position-and-2024-capture/) (8) — RPITIT 가 있으면 E0038. 격자의 `rpitit` 줄이 그것이다.
- [**30번 주제** — `Deref`](../30-operator-overloading-std-ops-index-and-deref/) — `Box<dyn Shape>` 에서 `.area()` 가 불리는 경로(`Box` 의 `Deref` 를 거쳐 `dyn Shape` 의 vtable 로).
- ★ [`언어-특성/README.md`](../../언어-특성/README.md) §6 — **제로 코스트 논증의 정본.** 「`dyn` 은 단형화 이점이 사라진다」는 **거기**의 문장이고, 이 문서는 시간을 재지 않았다.
- ★ C++ 대비 — C++ 갈래의 [**19번**](../../../cpp/syntax/19-inheritance-virtual-functions-override-final/)(가상 함수)과 C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md))의 **21번**(vtable 비용). (1)의 `sizeof` 는 그 대비의 **크기 한 칸**만 쟀다.
- [**34번 주제** — 클로저 세 종류](../34-closures-fn-fnmut-fnonce-and-move/) · [**35번 주제** — 클로저 반환](../35-function-pointers-and-returning-closures/) — `Box<dyn Fn>` 은 이 주제의 트레이트 객체가 **클로저 트레이트**에 쓰인 것이다.
- 목록의 **40번 주제** — `Box<T>`·재귀 타입·`dyn` 담기. `Box<dyn …>` 를 **소유 쪽에서** 다루는 자리.
- 목록의 **50번 주제** — `Send`/`Sync`. (6)의 `dyn Display + Send` 가 스레드 경계에서 쓰이는 자리.

## 용어 풀이

- **트레이트 객체(trait object)** — `dyn Trait` 타입의 값. 구체 타입을 지워 크기가 없다.
- **DST(dynamically sized type)** — 크기를 실행 때만 아는 타입. `dyn Trait`·`[T]`·`str`.
- **넓은 포인터(fat pointer)** — DST 를 가리키는 포인터. 데이터 포인터 + 메타데이터(길이 또는 vtable).
- **vtable** — 구체 타입 × 트레이트마다 한 장인 함수 포인터 표. 이 판에서는 드롭 · 크기 · 정렬 · 메서드 순.
- **dyn 호환(dyn compatible)** — `dyn` 이 될 수 있는 트레이트의 성질. 옛 이름 **객체 안전성(object safety)**.
- **디스패치 가능(dispatchable)** — vtable 에 칸을 가지는 메서드. `where Self: Sized` 가 붙은 것은 **명시적으로 디스패치 불가**.
- **자동 트레이트(auto trait)** — `Send`·`Sync`·`Unpin` 등. 트레이트 객체에 **몇 개든 더할 수 있다.**
- **업캐스팅(upcasting)** — `dyn Sub` 를 `dyn Super` 로 강제 변환하는 것(1.86~).
- **다운캐스트(downcast)** — 지운 타입을 되찾는 것. `Any` 로만.
- **담요 구현(blanket impl)** — `impl<T: Bound> Trait for T` — 경계를 만족하는 모든 타입에 한 번에 구현.
- **GAT(generic associated type)** — 제네릭 파라미터를 가진 연관 타입(`type Out<U>`).

## 더 들어가면

- **`dyn Trait` 에 연관 타입이 있으면** — `Box<dyn Iterator<Item = u32>>` 처럼 **연관 타입을 적어야** 한다. (0)의 1.72.0 조항은 그중 `where Self: Sized` 인 연관 타입은 **안 적어도 된다**는 완화다(이 문서는 던지지 않았다).
- **`impl dyn Trait { … }`** — 트레이트 객체 타입 자체에 고유 메서드를 붙일 수 있다. Reference 의 기본 수명 예가 `impl dyn Foo {}` = `impl dyn Foo + 'static {}` 이다.
- **`Rc<Self>`·`Arc<Self>`·`Pin<&mut Self>` 수신자** — Reference 의 디스패치 가능 수신자 목록에 들어 있다. `async fn` 은 **dyn 호환이 아니다**(숨은 `Future` 타입 — 32번 RPITIT 와 같은 이유).
- **디버추얼라이제이션** — 컴파일러가 `dyn` 호출의 대상을 알아내 **직접 호출로 바꾸는** 최적화. **이 문서는 IR 에서 그것을 찾아보지 않았다**(`opt-level=0` 만 봤다).
