# rust/syntax/31 — 제네릭과 트레이트 경계·`where`·단형화 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 와
> **`g++ 13.3.0` · `clang++ 18.1.3` · `GNU nm 2.42`** 에서 실제로 돌려 받은 것이다(판 블록은 서머리 머리).\
> ★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
> ★★ 블록 첫 줄 `===== 소스: <파일> =====` 아래가 **컴파일한 소스 전문**이고, **진단의 줄 번호는 그 파일 기준**이다.\
> ★ `nm` 의 **주소 열은 캡처가 버렸다**(배너의 `awk`) — 이름·크기만 남겼다. 필터는 **원 명령의 출력을 다 받은 뒤** 걸었고 종료 코드는 원 명령의 것이다.\
> ★★★ **속도는 한 번도 재지 않았다.** 벌 수와 바이트만 셌다.\
> ★★ **외부 크레이트를 하나도 쓰지 않았다**(네트워크 없음).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ E0599 — 호출이 없어도 정의 자리에서 막힌다

**출력.**

```text
===== 소스: r31_nobound.rs =====
// 경계 없이 메서드를 부르면 — 호출이 하나도 없어도
trait Shape {
    fn area(&self) -> f64;
}

fn total<T>(items: &[T]) -> f64 {
    items.iter().map(|it| it.area()).sum()
}

fn main() {}
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

**왜 그런가.**

- ★★ **E0599**. `main` 이 비어 `total` 은 **한 번도 안 불렸다.** 그래도 막힌다 — 몸통은 **정의 자리에서 경계만 보고** 검사된다.
- 몸통이 `T` 에 대해 아는 것은 **경계에 적힌 능력뿐**이다. 경계가 없으니 `area` 를 부를 근거가 없다.
  `help:` 가 「**restrict type parameter `T`**」로 `T: Shape` 를 권한다.

### 2. ★ E0277 — 주 진단은 호출 자리, 경계는 note

**출력.**

```text
===== 소스: r31_missing.rs =====
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

**왜 그런가.**

- ★ **E0277** 이고 **주 밑줄은 21행 호출 자리의 인자**(`&Sq(2.0)`)다. 16행 경계(`Debug`)는 `` note: required by a bound in `a` `` 로 따라온다.
- **두 자리** — 1번(몸통 → **정의 자리** E0599)과 이것(인자 → **호출 자리** E0277). Rust 는 **양쪽에서** 막는다.

### 3. ★ 16행만 — 숨은 `Sized` 경계

**출력.**

```text
===== 소스: r31_sized.rs =====
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

**왜 그런가.**

- ★ **16행 `plain(s)` 만 E0277** 이고, `note:` 가 「**required by an implicit `Sized` bound in `plain`**」이라 짚는다.
  15행 `plain(&s)` 는 `T = &str`(참조는 크기가 있다)이라 통과, 14행 `relaxed(s)` 는 `?Sized` 라 `T = str` 을 받는다.
- **모든 타입 파라미터에 `Sized` 가 숨어 있다**(Reference). `help:` 대로 **`T: Display + ?Sized`** 로 푼다 — `?` 는 **빼는** 경계다.

### 4. ★★ C++ 는 인스턴스화 때 몸통을 본다

**출력 — 정의만 하고 안 쓰면.**

```text
===== 소스: r31_tmpl.cpp =====
// C++ 템플릿 — 몸통을 언제 검사하나
template <class T>
double total(const T& x) {
    return x.area(); // T 가 area 를 가지는지 이 자리에서는 모른다
}

int main() {
    return 0; // ★ 한 번도 인스턴스화하지 않는다
}
===== g++ -std=c++20 -Wall -Wextra -c r31_tmpl.cpp -o r31_tmpl.o =====
(exit 0)
===== clang++ -std=c++20 -Wall -Wextra -c r31_tmpl.cpp -o r31_tmpl.o =====
(exit 0)
```

**출력 — `int` 로 인스턴스화하면.**

```text
===== 소스: r31_tmpl_int.cpp =====
// 인스턴스화하는 순간 — int 로 부르면
template <class T>
double total(const T& x) {
    return x.area();
}

int main() {
    return total(3) == 0.0 ? 0 : 1;
}
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

**출력 — 콘셉트로 요구를 선언하면.**

```text
===== 소스: r31_concept.cpp =====
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

**출력 — 콘셉트를 달고 몸통이 콘셉트 밖 능력을 쓰면.**

```text
===== 소스: r31_concept_body.cpp =====
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
===== g++ -std=c++20 -Wall -Wextra -c r31_concept_body.cpp -o r31_concept_body.o =====
(exit 0)
===== clang++ -std=c++20 -Wall -Wextra -c r31_concept_body.cpp -o r31_concept_body.o =====
(exit 0)
```

**왜 그런가.**

- ★★★ **앞 파일 — 두 컴파일러 다 `exit 0`, 진단 0줄.** `x.area()` 는 **`T` 에 의존하는 식**이라 인스턴스화 전까지 검사되지 않는다.
  1번 Rust 는 **같은 모양에서 E0599** 였다.
- ★★ **뒤 파일 — 에러는 4행(템플릿 몸통)** 에서 난다. 8행 호출 자리는 g++ 의 `required from here`, clang++ 의 `note: in instantiation of … requested here` 로 **뒤따른다.**
  Rust(2번)는 **호출 자리가 주 진단**이었다. **순서가 뒤집혀 있다.** (두 컴파일러의 문구·캐럿 열은 서로 다르다 — 같은 것은 성질이다.)
- ★★ **콘셉트** — 에러가 **호출 자리(11행)** 로 온다(「**no matching function** … **constraints not satisfied**」). Rust 경계와 **같은 자리**다.
- ★★★ **그래도 남는 차이 둘** — ① 콘셉트는 **모양**(`x.area()` 가 성립하나)을 보고 Rust 는 **이름**(`impl Shape for …`)을 본다.
  ② **콘셉트를 달아도 몸통은 콘셉트로 검사되지 않는다** — 마지막 블록의 `x.perimeter()` 는 콘셉트 밖인데 **두 컴파일러 다 통과**했다. Rust 는 1번처럼 **막는다.**

### 5. ★★★ MIR 1줄 · opt 0 에서 3벌 · opt 3 에서 0벌

**출력 — MIR.**

```text
===== 소스: r31_mono.rs =====
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

**출력 — `opt-level=0`.**

```text
===== 소스: r31_mono.rs =====
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

**출력 — `opt-level=3`.**

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

**왜 그런가.**

- ★★ **MIR 은 `fn total(_1: &[T])` 한 줄** — 단형화 **이전**이라 `T` 가 그대로다. **몇 벌인지 모른다.**
- ★★★ **opt 0 — `total::<Sq>`·`total::<Rect>`·`total::<Circle>` 세 벌, `total_dyn` 한 벌.**
- ★★ **opt 3 — `r31_mono::main` 하나만 남았다.** 전부 **인라인**으로 `main` 에 녹아 **심볼이 없다.** 「타입마다 한 벌」은 **opt 0 의 관찰**이다.
- ★ **std 함수도 타입마다 찍혔다** — `slice::Iter<…>::next` 와 `&[…]::into_iter` 가 `Sq`·`Rect`·`Circle`·`&dyn Shape` **네 벌씩**.
  제네릭이 제네릭을 부르면 **곱으로** 는다 — `total` 만 세면 과소 집계다.

### 6. ★★★ 3 · 3 · 2 · 2 — `Tile` 이 `Sq` 에 합쳐진다

**출력.**

```text
===== 소스: r31_grid.sh =====
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

**왜 그런가.**

- ★★★ **벌 수 `3 → 3 → 2 → 2`.** `opt-level=2` 부터 **`total::<Tile>` 이 사라졌다** — `Tile` 과 `Sq` 는 **둘 다 `f64` 하나에 `area` 몸통이 같아**
  찍어 놓고 보니 **기계어가 같았고**, 최적화기가 **하나로 합쳤다.** `area` 몸통도 **3 → 2** 로 같이 줄었다. `-Z` 없이 **안정 판 기본 설정**에서다.
- ★★ **바이트 — 제네릭 합 `318 · 579 · 370 · 370` 대 `dyn` `111 · 87 · 87 · 87`.** **모든 판에서 제네릭 쪽이 컸다.**
  그러나 **폭은 판마다 다르다** — 그리고 한 벌의 크기가 **opt 0 의 106B 에서 opt 1 의 209B 로 커지기도** 했다. **한 판의 절댓값으로 배수를 말하지 않는다.**
- ★ 이 격자는 **함수 심볼만** 센다 — 인라인되어 `main` 에 들어간 양과 **속도**는 안 봤다.

### 7. 같은 뜻, 다른 자리 — 그리고 왼쪽이 파라미터가 아니면 `where` 뿐

- **뜻은 같다** — 서머리 (2)의 `a`(꺾쇠)와 `b`(`where`)가 **같은 출력**을 냈다.
- ★ 꺾쇠 안의 경계는 **`T: …` 꼴 — 왼쪽이 그 자리에서 선언하는 파라미터**여야 한다.
  `Vec<T>: Debug`·`I::Item: Display` 는 **왼쪽이 파라미터가 아닌 타입**이라 **`where` 에만** 쓸 자리가 있다.

### 8. ★ E0271 — 이터레이터이긴 한데 `Item` 이 다르다

- **E0271** — 「**expected `IntoIter<u16>` to be an iterator that yields `u8`, but it yields `u16`**」(서머리 (4)).
- **E0277 이 아닌 이유** — `IntoIter<u16>` 은 **`Iterator` 를 구현한다.** 트레이트는 채웠고, **연관 타입 `Item` 의 고정(`= u8`)** 이 안 맞은 것이다.
  「트레이트가 없다」와 「트레이트는 있는데 연관 타입이 다르다」가 **다른 번호**로 온다.

### 9. ★★★ 구현이 정한다 — 인라인과 병합

- **언어 보장이 아니다.** 언어(Reference)는 제네릭의 **의미**만 정한다. 「단형화」라는 말도 **Book** 이 쓴다. 벌 수는 **컴파일러의 선택**이다.
- ★★ **인라인** — `r31_mono` 를 opt 3 에서 **0 벌**로 만들었다(5번). **함수 병합** — `r31_keep` 을 opt 2 부터 **3 → 2 벌**로 만들었다(6번).
- ★ **MIR 은 단형화 이전**이라 언제나 한 벌로 보인다. **`-Z print-mono-items` 는 nightly 전용**인데 이 머신은 **stable 하나뿐**이다(서머리 (8)의 블록).
  그래서 **링크 뒤의 심볼 표**(`nm -C`, v0 맨글링)로 **같은 질문을 다른 창으로** 물었다.
  ★ 그 창이 **못 보는 것** — **인라인되어 심볼이 없어진 벌.** 「0 벌」이 「안 찍었다」인지 「녹였다」인지 가르려고 `#[inline(never)]` 판(6번)을 따로 세웠다.

### 10. ★★ 이름이냐 모양이냐

- ★★ **진짜 축은 「이름(명목)이냐 모양(구조)이냐」** 다. 검사 자리는 **Rust·TS 둘 다 양쪽**이다([TS 20번](../../../ts/syntax/20-generic-constraints-and-defaults/) (6)이 rustc 1.92.0 으로 던져 보인 것).
- `Loud` 는 **`impl Display for Loud` 가 없어서**다. Rust 경계는 **선언된 `impl`** 을 본다 — 이름이 같은 메서드가 있어도 **모양으로는 안 넘는다.**
- **Go 20번** — `implements` 를 안 적는 **암묵 구현**, 모양 쪽. **Python 35번** — **`Protocol` 은 모양, `ABC` 는 이름**, 한 언어에 둘 다.
- ★ **C++20 콘셉트는 모양** 이다(`requires { x.area(); }`). 그리고 콘셉트를 달아도 **몸통이 콘셉트 밖 능력을 쓰면 통과**한다(4번의 마지막 블록) — **몸통은 여전히 인스턴스화 때** 본다.

### 11. 크기 쪽 한 칸을 세었다

- ★★ **정본은 [`언어-특성/README.md`](../../언어-특성/README.md) §6** — 「무엇이 0이고 무엇이 0이 아닌가」, 「청구서가 컴파일 시간과 **바이너리 크기**로 옮겨 간다」.
  이 주제는 그 논증을 다시 쓰지 않고 **바이너리 크기 쪽 한 칸**(함수 심볼의 벌 수·바이트)을 **판 격자로 세었다.** 컴파일 시간과 속도는 **안 쟀다.**
- **`dyn` 판은 함수 한 벌 + 타입마다 vtable 하나** 를 만든다(서머리 (8)의 IR — `@vtable.1`~`.3`). 타입이 늘면 **표가** 는다. 단형화는 **함수 몸통이** 는다.
- **Java 의 타입 소거는 반대 끝** — 컴파일 뒤 타입 인자를 지우고 **한 벌**만 남긴다([Java 19번](../../../java/syntax/19-type-erasure/) — 이 배치에서 안 던졌다).
- ★ **겉은 제네릭 한 줄, 속은 비제네릭 `inner(&Path)`** — 설치된 std 소스의 `fs::read` 가 그 모양이었다(서머리 「언제 쓰고」). `P` 마다 찍히는 것은 **겉의 한 줄뿐**이다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서·서머리의 **모든 블록** | `capture.sh` — `rustc --edition 2021` · `g++`/`clang++ -std=c++20 -Wall -Wextra` · `nm -C` | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` — **흔들린 칸 0 · 고칠 것 0** |
| ★★ **경계 검사 자리** | `r31_nobound`(호출 0) · `r31_missing` | 2 | **E0599**(정의 자리) · **E0277**(호출 자리) |
| 경계 모양 | `r31_bounds` · `r31_assoc` · `r31_sized` · `r31_default` | 4 | `a`=`b` · **E0271** · **E0277 implicit `Sized`** · 타입 기본 인자 됨 |
| ★★ **C++ 템플릿** | `r31_tmpl` · `r31_tmpl_int` · `r31_concept` · `r31_concept_body` · `r31_tmpl_default` × **g++·clang++** | 5 × 2 | 정의만 **exit 0** · 인스턴스화 때 몸통 에러 · 콘셉트는 호출 자리 · 콘셉트 밖 몸통 **exit 0** · 함수 기본 인자 **exit 0** |
| ★ 단형화 목록 창 | `r31_nightly` — `rustup toolchain list` + `-Z print-mono-items` | 1 | stable 하나뿐 · **nightly 전용** |
| ★★ MIR 창 | `r31_mir` | 1 | `fn total(_1: &[T])` **한 줄** |
| ★★★ **심볼 벌 수** | `r31_mono_o0` · `r31_mono_o3` | 2 | **3 벌** + std 제네릭 네 벌씩 · opt 3 은 **`main` 하나** |
| ★★★ **판 격자** | `r31_grid.sh` — `r31_keep.rs` × opt 0·1·2·3 | 4 | 벌 수 **3·3·2·2** · 바이트 **318·579·370·370** 대 dyn **111·87·87·87** |
| `dyn` 의 vtable | `r31_vtable` — LLVM IR | 1 | 타입마다 `@vtable` 하나 |
| std 의 겉/속 분리 | `r31_inner.py` — 설치된 std 소스 | 1 | `fs::read` → `inner(&Path)` |
| **TS 20번 인용** — 함수 기본 타입 인자 금지 · `Loud` 의 E0277 | **다시 던지지 않았다**(같은 rustc 판의 형제 실측) | 0 | ★ 인용으로 표시했다 |
| **안 잰 것** — 실행 시간 · 컴파일 시간 · `main` 이 커진 양 · 병합 패스 이름 | — | 0 | ★ 부적용·미확인으로 표시했다 |
| 외부 크레이트 | **쓰지 않음** | 0 | std 만 |

**구현 의존 항목**(버전·환경이 바뀌면 **다시 찍어야 하는** 것).

| 항목 | 왜 |
|---|---|
| ★★★ **벌 수 3·3·2·2 와 0** | ★ 인라인·병합의 판단이 LLVM 판·rustc 판·기본 설정에 달렸다 |
| ★★ **바이트 전부** | ★ 코드 생성이 바뀌면 바뀐다. **opt 1 에서 커진 것**도 이 판의 관찰이다 |
| `-C symbol-mangling-version=v0` 이 **기본값이 아닌** 것 | ★ rustc book 이 「기본값은 바뀔 수 있다」고 적는다 |
| vtable 의 **칸 모양** | ★ 레이아웃은 언어가 정하지 않는다 |
| `-Z print-mono-items` 가 **nightly 전용**인 것 | ★ 불안정 옵션의 지위는 바뀔 수 있다 |
| C++ 두 컴파일러의 **문구·캐럿 열** | ★ 컴파일러마다·판마다 다르다. 성질(인스턴스화 때 검사)만 근거로 썼다 |

★ **다시 찍는 법** — `capture.sh <새 디렉토리>` 를 그대로 돌리고 `normalize-shaky.py <원본> <새 디렉토리>` 로 견준다.
**이 판에서는 흔들린 칸이 0 이었다** — 벌 수·바이트도 **같은 판·같은 플래그**면 한 글자 같았다. **판을 바꾸면** 그것들이 먼저 움직일 칸이다.
