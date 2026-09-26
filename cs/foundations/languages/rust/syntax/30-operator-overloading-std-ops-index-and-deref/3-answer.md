# rust/syntax/30 — 연산자 오버로딩(`std::ops`)·`Index`·`Deref` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서\
> **`rustc --edition 2021 <파일>.rs`** 로 실제로 돌려 받은 것이다.\
> ★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
> ★★ 블록 첫 줄 `===== 소스: <파일>.rs =====` 아래가 **컴파일한 소스 전문**이고, **진단의 줄 번호는 그 파일 기준**이다.\
> ★ 표준 출력과 표준 오류는 **섞지 않았다** — rustc 의 진단은 표준 오류, 프로그램의 `println!` 은 표준 출력이다.\
> ★★ **외부 크레이트를 하나도 쓰지 않았다**(네트워크 없음).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ E0382 — 연산자가 왼쪽을 옮겼다

**출력.**

```text
===== 소스: r30_move.rs =====
// a + b 는 a.add(b) 다 — self 를 값으로 받는다
use std::ops::Add;

#[derive(Debug)]
struct Poly(Vec<i32>); // 계수 목록 — Copy 가 아니다

impl Add for Poly {
    type Output = Poly;
    fn add(self, rhs: Poly) -> Poly {
        let n = self.0.len().max(rhs.0.len());
        let at = |p: &Poly, i: usize| p.0.get(i).copied().unwrap_or(0);
        Poly((0..n).map(|i| at(&self, i) + at(&rhs, i)).collect())
    }
}

fn main() {
    let a = Poly(vec![1, 2]);
    let b = Poly(vec![10, 20, 30]);
    let c = a + b;
    println!("c = {:?}", c);
    println!("a = {:?}", a);
}
===== rustc --edition 2021 r30_move.rs =====
error[E0382]: borrow of moved value: `a`
  --> r30_move.rs:21:26
   |
17 |     let a = Poly(vec![1, 2]);
   |         - move occurs because `a` has type `Poly`, which does not implement the `Copy` trait
18 |     let b = Poly(vec![10, 20, 30]);
19 |     let c = a + b;
   |             ----- `a` moved due to usage in operator
20 |     println!("c = {:?}", c);
21 |     println!("a = {:?}", a);
   |                          ^ value borrowed here after move
   |
note: if `Poly` implemented `Clone`, you could clone the value
  --> r30_move.rs:5:1
   |
 5 | struct Poly(Vec<i32>); // 계수 목록 — Copy 가 아니다
   | ^^^^^^^^^^^ consider implementing `Clone` for this type
...
19 |     let c = a + b;
   |             - you could clone this value
note: calling this operator moves the left-hand side
  --> /rustc/ded5c06cf21d2b93bffd5d884aa6e96934ee4234/library/core/src/ops/arith.rs:92:12
   = note: this error originates in the macro `$crate::format_args_nl` which comes from the expansion of the macro `println` (in Nightly builds, run with -Z macro-backtrace for more info)

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0382`.
(exit 1)
```

**왜 그런가.**

- ★★★ **E0382** — 19행 `a + b` 에서 `a` 가 옮겨 갔고 21행이 그것을 빌려 쓰려 했다. 밑줄이 **연산자 식 전체**를 짚고 「**moved due to usage in operator**」라고 적는다.
- ★★ **`note: calling this operator moves the left-hand side`** 가 std 의 **`arith.rs:92:12`** 를 가리킨다 — `fn add(self, rhs: Rhs)` 의 **`self`** 다.
  **첫 인자를 값으로 받으므로** `Copy` 가 아닌 `Poly` 는 옮겨 간다.
- ★ **`b` 도 옮겨 갔다** — `rhs: Rhs` 도 값이다. 이 소스는 `b` 를 다시 안 써서 에러가 한 건뿐이다.
- ★ `String + &str` 에서 왼쪽이 사라지는 것([14번 주제](../14-string-vs-str/) (6))이 **같은 시그니처의 std 판**이다.

### 2. ★ `Copy` 면 복사본이 옮겨 가고, `+=` 는 빌려 간다

**출력.**

```text
===== 소스: r30_copy.rs =====
// Copy 타입이면 + 뒤에도 a 가 살아 있다
use std::ops::{Add, AddAssign, Neg};

#[derive(Debug, Clone, Copy, PartialEq)]
struct V2 {
    x: i32,
    y: i32,
}

impl Add for V2 {
    type Output = V2;
    fn add(self, o: V2) -> V2 {
        V2 { x: self.x + o.x, y: self.y + o.y }
    }
}

impl AddAssign for V2 {
    fn add_assign(&mut self, o: V2) {
        self.x += o.x;
        self.y += o.y;
    }
}

impl Neg for V2 {
    type Output = V2;
    fn neg(self) -> V2 {
        V2 { x: -self.x, y: -self.y }
    }
}

fn main() {
    let a = V2 { x: 1, y: 2 };
    let b = V2 { x: 10, y: 20 };
    let c = a + b;
    println!("a + b = {:?}", c);
    println!("a     = {:?}  ★ 복사됐으니 그대로다", a);
    let mut m = a;
    m += b;
    println!("m += b {:?}", m);
    println!("-a    = {:?}", -a);
    println!("a + -a == 0 {}", a + -a == V2 { x: 0, y: 0 });
}
===== rustc --edition 2021 r30_copy.rs =====
(exit 0)
===== ./r30_copy =====
a + b = V2 { x: 11, y: 22 }
a     = V2 { x: 1, y: 2 }  ★ 복사됐으니 그대로다
m += b V2 { x: 11, y: 22 }
-a    = V2 { x: -1, y: -2 }
a + -a == 0 true
(exit 0)
```

**왜 그런가.**

- **`V2` 가 `Copy`** 라 `a + b` 에 **복사본**이 들어갔다. `a` 는 그대로다(둘째 줄).
- ★ **`+` 는 `self`(값), `+=` 는 `&mut self`(가변 빌림)** — `add_assign` 은 왼쪽을 **제자리에서 고친다.** 그래서 `m` 이 `mut` 이어야 하고, `Copy` 가 아닌 타입이어도 `+=` 뒤에 `m` 은 남는다.
- `-a` 는 `Neg::neg(self)` 이고, 마지막 줄의 `==` 는 `derive(PartialEq)` 다 — `std::ops` 가 아니다(8번 답).

### 3. ★★ 2건 — E0308 과 E0369, 그리고 `help:` 는 틀렸다

**출력.**

```text
===== 소스: r30_mixed.rs =====
// 참조 판만 있으면 — 값 + 참조, 참조 + 값은
use std::ops::Add;

#[derive(Debug)]
struct Poly(Vec<i32>);

impl Add for &Poly {
    type Output = Poly;
    fn add(self, rhs: &Poly) -> Poly {
        Poly(self.0.iter().zip(&rhs.0).map(|(x, y)| x + y).collect())
    }
}

fn main() {
    let a = Poly(vec![1, 2]);
    let b = Poly(vec![3, 4]);
    let c = &a + &b; // 된다
    let d = &c + b; // 참조 + 값
    let e = a + &c; // 값 + 참조
    println!("{:?} {:?}", d, e);
}
===== rustc --edition 2021 r30_mixed.rs =====
error[E0308]: mismatched types
  --> r30_mixed.rs:18:18
   |
18 |     let d = &c + b; // 참조 + 값
   |                  ^ expected `&Poly`, found `Poly`
   |
help: consider dereferencing the borrow
   |
18 |     let d = *&c + b; // 참조 + 값
   |             +

error[E0369]: cannot add `&Poly` to `Poly`
  --> r30_mixed.rs:19:15
   |
19 |     let e = a + &c; // 값 + 참조
   |             - ^ -- &Poly
   |             |
   |             Poly
   |
note: an implementation of `Add<&Poly>` might be missing for `Poly`
  --> r30_mixed.rs:5:1
   |
 5 | struct Poly(Vec<i32>);
   | ^^^^^^^^^^^ must implement `Add<&Poly>`
note: the trait `Add` must be implemented
  --> /rustc/ded5c06cf21d2b93bffd5d884aa6e96934ee4234/library/core/src/ops/arith.rs:77:1

error: aborting due to 2 previous errors

Some errors have detailed explanations: E0308, E0369.
For more information about an error, try `rustc --explain E0308`.
(exit 1)
```

**`help:` 를 그대로 따르면.**

```text
===== 소스: r30_mixed_help.rs =====
// help: 가 권한 *&c + b 를 그대로 따르면
use std::ops::Add;

#[derive(Debug)]
struct Poly(Vec<i32>);

impl Add for &Poly {
    type Output = Poly;
    fn add(self, rhs: &Poly) -> Poly {
        Poly(self.0.iter().zip(&rhs.0).map(|(x, y)| x + y).collect())
    }
}

fn main() {
    let a = Poly(vec![1, 2]);
    let b = Poly(vec![3, 4]);
    let c = &a + &b;
    let d = *&c + b; // help: 의 제안
    println!("{:?}", d);
}
===== rustc --edition 2021 r30_mixed_help.rs =====
error[E0369]: cannot add `Poly` to `Poly`
  --> r30_mixed_help.rs:18:17
   |
18 |     let d = *&c + b; // help: 의 제안
   |             --- ^ - Poly
   |             |
   |             Poly
   |
note: an implementation of `Add` might be missing for `Poly`
  --> r30_mixed_help.rs:5:1
   |
 5 | struct Poly(Vec<i32>);
   | ^^^^^^^^^^^ must implement `Add`
note: the trait `Add` must be implemented
  --> /rustc/ded5c06cf21d2b93bffd5d884aa6e96934ee4234/library/core/src/ops/arith.rs:77:1

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0369`.
(exit 1)
```

**왜 그런가.**

- ★★ **18행 `&c + b` — E0308.** 왼쪽 `&Poly` 에는 `Add` 구현이 **하나**(`Add<&Poly>`) 있으므로 rustc 가 오른쪽을 `&Poly` 로 정했고, **값**이 와서 **타입 불일치**가 됐다.
- ★★ **19행 `a + &c` — E0369.** 왼쪽 `Poly` 에는 `Add` 구현이 **하나도 없다** — 고를 후보조차 없으니 「**cannot add**」다.
  **「구현이 하나 있어 타입을 정했다」와 「구현이 없다」가 다른 진단으로 온다** — 비대칭인 실수가 비대칭인 번호를 낸다.
- ★ **`help:` 의 `*&c + b` 는 E0369** — 왼쪽이 `Poly` 가 되자 이번에는 **`Poly + Poly` 가 없다.** 진단의 제안은 **한 자리만 맞춘다.**
- ★ 결론 — `T + T` · `&T + T` · `T + &T` · `&T + &T` 는 **전부 따로** 구현한다(std 의 정수는 네 벌 다 가진다 — 서머리 (3)).

### 4. ★ `Meters(6.0)` · `9.0` · `Meters(6.0)` — 왼쪽 구현은 따로다

**출력.**

```text
===== 소스: r30_scalar.rs =====
// Output 은 연관 타입, Rhs 는 파라미터 — 오른쪽이 다른 타입이어도 된다
use std::ops::Mul;

#[derive(Debug, Clone, Copy)]
struct Meters(f64);

impl Mul<f64> for Meters {
    type Output = Meters; // 길이 × 수 = 길이
    fn mul(self, k: f64) -> Meters {
        Meters(self.0 * k)
    }
}

impl Mul<Meters> for Meters {
    type Output = f64; // ★ 길이 × 길이 = 넓이 — 다른 타입을 돌려준다
    fn mul(self, o: Meters) -> f64 {
        self.0 * o.0
    }
}

impl Mul<Meters> for f64 {
    type Output = Meters; // ★ 왼쪽이 남의 타입(f64)이어도 된다 — Meters 가 내 것이라
    fn mul(self, m: Meters) -> Meters {
        Meters(self * m.0)
    }
}

fn main() {
    let m = Meters(3.0);
    println!("m * 2.0 = {:?}", m * 2.0);
    println!("m * m   = {:?}", m * m);
    println!("2.0 * m = {:?}", 2.0 * m);
}
===== rustc --edition 2021 r30_scalar.rs =====
(exit 0)
===== ./r30_scalar =====
m * 2.0 = Meters(6.0)
m * m   = 9.0
2.0 * m = Meters(6.0)
(exit 0)
```

**21행을 지우면.**

```text
===== 소스: r30_scalar_noleft.rs =====
// 왼쪽이 f64 인 구현을 지우면 — 교환 법칙은 누가 아나
use std::ops::Mul;

#[derive(Debug, Clone, Copy)]
struct Meters(f64);

impl Mul<f64> for Meters {
    type Output = Meters; // 길이 × 수 = 길이
    fn mul(self, k: f64) -> Meters {
        Meters(self.0 * k)
    }
}

impl Mul<Meters> for Meters {
    type Output = f64; // ★ 길이 × 길이 = 넓이 — 다른 타입을 돌려준다
    fn mul(self, o: Meters) -> f64 {
        self.0 * o.0
    }
}

fn main() {
    let m = Meters(3.0);
    println!("m * 2.0 = {:?}", m * 2.0);
    println!("m * m   = {:?}", m * m);
    println!("2.0 * m = {:?}", 2.0 * m);
}
===== rustc --edition 2021 r30_scalar_noleft.rs =====
error[E0277]: cannot multiply `{float}` by `Meters`
  --> r30_scalar_noleft.rs:25:36
   |
25 |     println!("2.0 * m = {:?}", 2.0 * m);
   |                                    ^ no implementation for `{float} * Meters`
   |
   = help: the trait `Mul<Meters>` is not implemented for `{float}`
   = help: the following other types implement trait `Mul<Rhs>`:
             `&f128` implements `Mul<f128>`
             `&f128` implements `Mul`
             `&f16` implements `Mul<f16>`
             `&f16` implements `Mul`
             `&f32` implements `Mul<f32>`
             `&f32` implements `Mul`
             `&f64` implements `Mul<f64>`
             `&f64` implements `Mul`
           and 57 others

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0277`.
(exit 1)
```

**왜 그런가.**

- **둘째 줄 `m * m` 의 결과는 `f64`**(`9.0`, `Meters(…)` 가 아니다) — `Mul<Meters> for Meters` 의 **`Output = f64`** 다. 결과 타입은 **구현마다 고른다.**
- ★★ **21행이 고아 규칙을 통과하는 이유** — `Mul` 도 `f64` 도 남의 것이지만 **`Mul<Meters>` 의 파라미터 자리에 내 타입 `Meters`** 가 있다.
  고아 규칙은 「**어딘가에 내 타입이 (규칙에 맞는 자리에) 있으면**」 허용한다([26번 주제](../26-orphan-rule-and-newtype/)).
- ★★ **지우면 `2.0 * m` 만 깨진다** — `m * 2.0` 은 `Mul<f64> for Meters` 로 남는다. **교환 법칙은 컴파일러가 모른다.**
  ★ 번호가 **E0277** 인 것에 주의 — 왼쪽이 **타입이 안 정해진 부동소수 리터럴 `{float}`** 이라
  「`{float}: Mul<Meters>` 인가」라는 **트레이트 질문**으로 나왔다(3번 답의 E0369 는 왼쪽 타입이 `Poly` 로 정해져 있었다).

### 5. ★★★ 바깥이 가로채고, 안쪽은 바깥을 모르고, 경계는 못 넘는다

**출력 — 이름이 겹치면.**

```text
===== 소스: r30_deref_inherit.rs =====
// Deref 로 「상속」을 흉내 내면 — 이름이 겹칠 때 누가 이기나
use std::ops::Deref;

struct Animal {
    name: String,
}

impl Animal {
    fn name(&self) -> String {
        format!("Animal({})", self.name)
    }
    fn describe(&self) -> String {
        format!("나는 {}", self.name()) // ★ 이 self 는 Animal 이다
    }
}

struct Dog {
    base: Animal,
}

impl Deref for Dog {
    type Target = Animal;
    fn deref(&self) -> &Animal {
        &self.base
    }
}

impl Dog {
    fn name(&self) -> String {
        format!("Dog({})", self.base.name)
    }
}

fn main() {
    let d = Dog { base: Animal { name: String::from("멍") } };
    println!("d.name()       {}", d.name()); // Dog 의 것이 이긴다
    println!("d.describe()   {}", d.describe()); // ★ 「재정의」가 안 먹는다
    println!("(*d).name()    {}", (*d).name());
}
===== rustc --edition 2021 r30_deref_inherit.rs =====
(exit 0)
===== ./r30_deref_inherit =====
d.name()       Dog(멍)
d.describe()   나는 Animal(멍)
(*d).name()    Animal(멍)
(exit 0)
```

**출력 — 트레이트 경계에 넘기면.**

```text
===== 소스: r30_deref_trait.rs =====
// Deref 로는 트레이트 구현이 따라오지 않는다
use std::ops::Deref;

trait Speak {
    fn speak(&self) -> String;
}

struct Animal;

impl Speak for Animal {
    fn speak(&self) -> String {
        String::from("...")
    }
}

struct Dog {
    base: Animal,
}

impl Deref for Dog {
    type Target = Animal;
    fn deref(&self) -> &Animal {
        &self.base
    }
}

fn twice<T: Speak>(x: &T) -> String {
    x.speak() + &x.speak()
}

fn as_animal(a: &Animal) -> String {
    a.speak()
}

fn main() {
    let d = Dog { base: Animal };
    println!("{}", d.speak()); // 메서드 호출 — 자동 역참조로 된다
    println!("{}", as_animal(&d)); // 구체 타입 자리 — 역참조 강제로 된다
    println!("{}", twice(&d)); // 제네릭 경계 — ?
}
===== rustc --edition 2021 r30_deref_trait.rs =====
error[E0277]: the trait bound `Dog: Speak` is not satisfied
  --> r30_deref_trait.rs:39:26
   |
39 |     println!("{}", twice(&d)); // 제네릭 경계 — ?
   |                    ----- ^^ unsatisfied trait bound
   |                    |
   |                    required by a bound introduced by this call
   |
help: the trait `Speak` is not implemented for `Dog`
  --> r30_deref_trait.rs:16:1
   |
16 | struct Dog {
   | ^^^^^^^^^^
   = help: the trait `Speak` is implemented for `Animal`
note: required by a bound in `twice`
  --> r30_deref_trait.rs:27:13
   |
27 | fn twice<T: Speak>(x: &T) -> String {
   |             ^^^^^ required by this bound in `twice`

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0277`.
(exit 1)
```

**왜 그런가.**

- ★★ **`d.name()` 은 `Dog(멍)`** — 메서드 찾기는 **수신자 타입(`Dog`)부터** 후보를 보고, 거기서 찾으면 `deref` 를 안 한다.
- ★★★ **`d.describe()` 는 `나는 Animal(멍)`** — `describe` 는 `Animal` 의 메서드라 그 안의 `self` 는 `&Animal` 이고, `self.name()` 은 **`Animal::name`** 이다.
  **`Dog::name` 은 재정의가 아니라 같은 이름의 다른 함수**다. 가상 디스패치가 없다.
- `(*d).name()` 은 **명시적으로 벗겨** `Animal::name` 을 부른다.
- ★★ **뒤 소스 — 39행만 E0277**(37·38행은 에러가 없다). `help:` 가 「**`Speak` is implemented for `Animal`**」이라고까지 알려 준다.
  37·38행이 **실제로 도는 것**은 서머리 (8)의 `r30_deref_trait_run`(그 두 줄만 남긴 판)이 `...` 두 줄로 보였다.
- ★★★ **`d.speak()` 는 되고 `twice(&d)` 는 안 되는 이유** — 메서드 호출은 **이름으로 후보를 찾으며 역참조를 반복**하므로 `Animal::speak` 에 닿는다.
  제네릭 경계는 **`T = Dog` 를 먼저 정하고** 「`Dog: Speak` 인가」를 묻는다 — **강제가 끼어들 자리가 없다.** `Dog` 는 `Speak` 를 구현하지 않았다.

### 6. ★★ E0507 — 참조 뒤에서는 못 꺼낸다

**출력.**

```text
===== 소스: r30_index_move.rs =====
// 그 * 때문에 — 인덱스로 꺼내 옮기려 하면
use std::ops::Index;

struct Row(Vec<String>);

impl Index<usize> for Row {
    type Output = String;
    fn index(&self, i: usize) -> &String {
        &self.0[i]
    }
}

fn main() {
    let r = Row(vec![String::from("a")]);
    let s = r[0];
    println!("{}", s);
}
===== rustc --edition 2021 r30_index_move.rs =====
error[E0507]: cannot move out of index of `Row`
  --> r30_index_move.rs:15:13
   |
15 |     let s = r[0];
   |             ^^^^ move occurs because value has type `String`, which does not implement the `Copy` trait
   |
help: consider borrowing here
   |
15 |     let s = &r[0];
   |             +
help: consider cloning the value if the performance cost is acceptable
   |
15 |     let s = r[0].clone();
   |                 ++++++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0507`.
(exit 1)
```

**왜 그런가.**

- ★★ **E0507** — `` cannot move out of index of `Row` ``. Reference 가 `a[b]` 를 **`*Index::index(&a, b)`** 로 정의한다.
  `index` 가 돌려준 **`&String` 에 `*` 가 붙은 자리**라, `let s = r[0]` 은 **빌린 것 뒤의 값을 옮기는** 것이 된다.
- `help:` 둘 — **`&r[0]` 로 빌리거나 `r[0].clone()` 으로 복제한다.** 소유권을 꺼내야 하면 `Vec::remove`·`mem::take` 같은 **따로 있는 API** 다.

### 7. 오른쪽은 여러 개일 수 있고, 결과는 오른쪽마다 하나다

- **여러 번 구현되는 경우** — 오른쪽 타입이 여럿일 때. `Meters * f64` 와 `Meters * Meters` 처럼(4번 답). 그래서 `Rhs` 는 **제네릭 파라미터**다.
- **결과가 둘일 이유는 없다** — `Meters * f64` 의 답은 하나다. 그래서 `Output` 은 **연관 타입**(구현당 하나)이다.
  [25번 주제](../25-traits-definition-impl-default-methods-and-associated-types/)의 판정 「한 타입에 몇 번」이 한 트레이트 안에서 **입력과 출력으로 갈라진** 사례다.
- ★ **`Rhs` 를 안 적으면 `Self`** 다 — `trait Add<Rhs = Self>` 의 **기본 타입 파라미터**. 그래서 `impl Add for Poly` 는 `Poly + Poly` 다.

### 8. ★ 비교는 `std::cmp`, `&&`·`||`·`=` 는 트레이트가 없다

**출력 — 비교와 논리 연산자를 `Flag` 에 쓰면.**

```text
===== 소스: r30_notops.rs =====
// std::ops 밖에 있는 것 — 비교와 논리 연산자
use std::ops::Add;

#[derive(Debug, Clone, Copy)]
struct Flag(bool);

impl Add for Flag {
    type Output = Flag;
    fn add(self, o: Flag) -> Flag {
        Flag(self.0 || o.0)
    }
}

fn main() {
    let a = Flag(true);
    let b = Flag(false);
    println!("{:?}", a + b); // Add 는 있다
    println!("{}", a < b); // 비교는 PartialOrd 다
    println!("{}", a && b); // && 는 트레이트가 없다
}
===== rustc --edition 2021 r30_notops.rs =====
error[E0369]: binary operation `<` cannot be applied to type `Flag`
  --> r30_notops.rs:18:22
   |
18 |     println!("{}", a < b); // 비교는 PartialOrd 다
   |                    - ^ - Flag
   |                    |
   |                    Flag
   |
note: an implementation of `PartialOrd` might be missing for `Flag`
  --> r30_notops.rs:5:1
   |
 5 | struct Flag(bool);
   | ^^^^^^^^^^^ must implement `PartialOrd`
help: consider annotating `Flag` with `#[derive(PartialEq, PartialOrd)]`
   |
 5 + #[derive(PartialEq, PartialOrd)]
 6 | struct Flag(bool);
   |

error[E0308]: mismatched types
  --> r30_notops.rs:19:20
   |
19 |     println!("{}", a && b); // && 는 트레이트가 없다
   |                    ^ expected `bool`, found `Flag`

error[E0308]: mismatched types
  --> r30_notops.rs:19:25
   |
19 |     println!("{}", a && b); // && 는 트레이트가 없다
   |                         ^ expected `bool`, found `Flag`

error: aborting due to 3 previous errors

Some errors have detailed explanations: E0308, E0369.
For more information about an error, try `rustc --explain E0308`.
(exit 1)
```

**출력 — 설치된 std 문서의 `std::ops` 트레이트 목록.**

```text
===== ls "$(rustc --print sysroot)/share/doc/rust/html/std/ops/" | grep "^trait" =====
trait.Add.html
trait.AddAssign.html
trait.AsyncFn.html
trait.AsyncFnMut.html
trait.AsyncFnOnce.html
trait.BitAnd.html
trait.BitAndAssign.html
trait.BitOr.html
trait.BitOrAssign.html
trait.BitXor.html
trait.BitXorAssign.html
trait.CoerceShared.html
trait.CoerceUnsized.html
trait.Coroutine.html
trait.Deref.html
trait.DerefMut.html
trait.DerefPure.html
trait.DispatchFromDyn.html
trait.Div.html
trait.DivAssign.html
trait.Drop.html
trait.Fn.html
trait.FnMut.html
trait.FnOnce.html
trait.FromResidual.html
trait.Index.html
trait.IndexMut.html
trait.IntoBounds.html
trait.Mul.html
trait.MulAssign.html
trait.Neg.html
trait.Not.html
trait.OneSidedRange.html
trait.RangeBounds.html
trait.Reborrow.html
trait.Receiver.html
trait.Rem.html
trait.RemAssign.html
trait.Residual.html
trait.Shl.html
trait.ShlAssign.html
trait.Shr.html
trait.ShrAssign.html
trait.Sub.html
trait.SubAssign.html
trait.Try.html
(exit 0)
```

- **`==` 는 `PartialEq`, `<` 는 `PartialOrd`** — `std::cmp` 다. `a < b` 의 E0369 가 「**`PartialOrd` might be missing**」이라 적는다([28번 주제](../28-partialeq-eq-partialord-ord-and-hash-contracts/)).
- ★★ **`&&`·`||`·`=` 에 대응하는 트레이트는 목록에 없다.** `&&`·`||` 는 **오른쪽을 안 볼 수도 있는** 단락 평가라 「두 값을 다 받는 메서드」로 못 적고,
  `=` 는 **이동·복사 그 자체**라 가로챌 자리가 없다(Reference 의 lazy boolean operators 정의에서 읽은 설명이다).
- ★ **진단은 「트레이트가 없다」고 말하지 않는다** — 「**expected `bool`, found `Flag`**」(E0308 두 건, 양쪽 피연산자 각각)일 뿐이다. 그래서 목록을 **다른 창**으로 물었다.
- **`&` 는 `BitAnd`, `&&` 는 없음** — 같은 트레이트가 아니다. 목록에 `BitAnd`·`BitOr`·`Not` 은 있다.

### 9. ★★ 컴파일러가 끼운 세 자리

**출력.**

```text
===== 소스: r30_deref.rs =====
// Deref — 스마트 포인터 관용구
use std::ops::Deref;

struct Tracked<T> {
    value: T,
    reads: std::cell::Cell<u32>,
}

impl<T> Tracked<T> {
    fn new(value: T) -> Self {
        Tracked { value, reads: std::cell::Cell::new(0) }
    }
}

impl<T> Deref for Tracked<T> {
    type Target = T;
    fn deref(&self) -> &T {
        self.reads.set(self.reads.get() + 1);
        &self.value
    }
}

fn takes_str(s: &str) -> usize {
    s.len()
}

fn main() {
    let t = Tracked::new(String::from("hello"));
    println!("*t 로 꺼내면       {}", *t); // 1. 명시 역참조
    println!("t.len()            {}", t.len()); // 2. 메서드 — 자동 역참조
    println!("&t 를 &str 자리에  {}", takes_str(&t)); // 3. 역참조 강제 — 두 번 벗긴다
    println!("deref 호출 횟수    {}", t.reads.get());
}
===== rustc --edition 2021 r30_deref.rs =====
(exit 0)
===== ./r30_deref =====
*t 로 꺼내면       hello
t.len()            5
&t 를 &str 자리에  5
deref 호출 횟수    3
(exit 0)
```

- **세 자리** — ① **`*t`**(명시 역참조) ② **`t.len()`**(메서드 호출의 자동 역참조) ③ **`takes_str(&t)`**(역참조 강제).
- ★ **벗기는 단계는 두 번** — `&Tracked<String>` → `&String` → `&str`. **첫 번째만 `Tracked` 의 `deref`**, 두 번째는 **`String` 의 `Deref`**(→ `str`)라
  이 계수기에 안 잡혔다. 그래서 합이 **3** 이다(4 가 아니다).
- **비싼 일을 하면 안 되는 이유** — 호출이 **소스에 글자로 안 보이고**, 한 줄에서도 여러 번 불릴 수 있다. std 의 `Deref` 문서가 「**컴파일러가 조용히 끼운다**」고 경고한다.
  ★ 「몇 번 부르나」는 **언어가 정하지 않는다** — 3 은 **이 판의 관찰**이다.

### 10. ★★ 안쪽 타입의 메서드와 부딪히지 않으려고

**출력.**

```text
===== 소스: r30_rc_assoc.rs =====
// Rc 가 strong_count 를 메서드로 안 두는 이유
use std::rc::Rc;

fn main() {
    let r = Rc::new(String::from("a"));
    let r2 = Rc::clone(&r);
    println!("{}", Rc::strong_count(&r2));
    println!("{}", r.strong_count());
}
===== rustc --edition 2021 r30_rc_assoc.rs =====
error[E0599]: no method named `strong_count` found for struct `Rc<String>` in the current scope
 --> r30_rc_assoc.rs:8:22
  |
8 |     println!("{}", r.strong_count());
  |                    --^^^^^^^^^^^^--
  |                    | |
  |                    | this is an associated function, not a method
  |                    help: use associated function syntax instead: `Rc::<String>::strong_count(&r)`
  |
  = note: found the following associated functions; to be used as methods, functions must have a `self` parameter
  = note: the candidate is defined in an impl for the type `Rc<T, A>`

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0599`.
(exit 1)
```

- **E0599 — `this is an associated function, not a method`.** `strong_count` 는 `self` 를 안 받는 **연관 함수**라 `Rc::strong_count(&r)` 로만 부른다.
- ★★ **메서드로 뒀다면** — `T` 에 `strong_count` 라는 메서드가 있을 때 **`r.strong_count()` 가 `Rc` 의 것을 불러 버린다.**
  5번 답의 「**이름이 겹치면 바깥이 이긴다**」와 같은 현상이다. std 의 `Rc` 문서가 「**안쪽 타입 `T` 의 메서드와 충돌하지 않게**」라고 이유를 적는다.
- ★ **`Rc::clone(&r)`** — `r.clone()` 도 `Rc` 를 복제하지만 읽는 사람에게는 **`T` 를 깊이 복제하는지** 안 보인다. 연관 함수 꼴이 **무엇을 복제하는지**를 드러낸다.

### 11. 기본값이 반대이거나, 대체 탐색이 있거나, 인터페이스를 만족하거나

- ★★ **C++** — `operator+` 는 관례상 **`const T&`** 로 받는다. 서머리 (10)에서 두 컴파일러로 던지니 `a + b` 뒤에도, **`std::move(a) + b` 뒤에도** `a.size=2` 였다 —
  받는 쪽이 `const&` 라 **`std::move` 를 써도 실제로는 안 옮긴다.** Rust `Add` 는 **값으로 받는 것이 트레이트의 시그니처**라 옮기고, 안 옮기려면 **참조 판을 따로** 구현한다.
  **이동을 정하는 것은 두 언어 다 「받는 시그니처」** 이고, **관례의 기본값이 반대**다. (C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md))의 **22번** — 폴더 없음.)
- **Python** — `2.0 * m` 에서 `float.__mul__` 이 모르면 **`m.__rmul__` 로 넘어간다**([`oop-basics/`](../../../../oop-basics/) §19).
  Rust 는 **왼쪽 타입의 `impl` 하나로 끝난다** — 없으면 4번 답의 E0277.
- ★★ **Go** — 구조체 임베딩은 **승격된 메서드로 인터페이스를 만족한다**([Go 18번](../../../go/syntax/18-embedding-and-field-method-promotion/) (5)).
  Rust 의 `Deref` 는 **트레이트 경계를 못 넘는다**(5번 답의 E0277). 대신 **둘 다 가상 디스패치가 없어** 안쪽 메서드는 바깥의 것을 모른다.
- ★ **Kotlin `by`**([Kotlin 21번](../../../kotlin/syntax/21-class-delegation-by/) (2)) — 「**위임 대상은 내 오버라이드를 모른다**」가 5번의 **`d.describe()` → `나는 Animal(멍)`** 과 같은 함정이다.
  다른 것은 Kotlin `by` 는 **인터페이스를 구현해 준다**는 것 — Rust `Deref` 는 아무 트레이트도 구현하지 않는다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서·서머리의 **모든 블록** | `capture.sh` 가 `rustc --edition 2021 <파일>.rs` 로 컴파일하고 실행 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` — **흔들린 칸 0 · 고칠 것 0** |
| ★★★ **`a + b` 가 `a` 를 옮기는 것** | `r30_move` | 1 | **E0382** + `calling this operator moves the left-hand side` |
| `Copy` · `+=` · `Neg` | `r30_copy` | 1 | `a` 가 남는다 · `+=` 는 `&mut self` |
| ★★ **참조 판과 조합** | `r30_ref` · `r30_mixed` · `r30_mixed_help` · `r30_int_combos` | 4 | 참조 판은 둘 다 산다 · 섞으면 **E0308/E0369** · `help:` 대로 하면 **E0369** · 정수는 네 조합 `3 3 3 3` |
| `Output`·`Rhs`·왼쪽 구현 | `r30_scalar` · `r30_scalar_noleft` | 2 | `m * m` 이 `f64` · 왼쪽 구현을 지우면 **E0277** `cannot multiply {float} by Meters` |
| ★ **`std::ops` 밖** | `r30_notops` · `r30_opslist`(설치된 문서의 파일 목록) | 2 | `<` **E0369** · `&&` **E0308 ×2** · 목록에 `And`·`Or`·`Assign` 없음 |
| `Index` | `r30_index` · `r30_index_move` | 2 | `r[0]` 이 `*r.index(0)` 과 같다 · 옮기면 **E0507** |
| ★★ **`deref` 호출 수** | `r30_deref` — `Cell` 계수기 | 1 | **3** |
| ★★★ **`Deref` 상속 흉내** | `r30_deref_inherit` · `r30_deref_trait_run` · `r30_deref_trait` | 3 | `Dog(멍)` · **`나는 Animal(멍)`** · 메서드·구체 자리는 됨 · 경계는 **E0277** |
| `Rc` 연관 함수 | `r30_rc_assoc` | 1 | **E0599** `associated function, not a method` |
| ★ **C++ `operator+` 대비** | `r30_opplus` × g++·clang++ | 2 | `a + b`·`std::move(a) + b` 뒤에도 `a.size=2` |
| **안 던진 것** — Kotlin `operator fun` | 형제 목록 인용만 했다(폴더 없음) | 0 | ★ 인용으로 표시했다 |
| 외부 크레이트 | **쓰지 않음** | 0 | std 만 |

**구현 의존 항목**(버전·환경이 바뀌면 **다시 찍어야 하는** 것).

| 항목 | 왜 |
|---|---|
| `deref` 가 **3 번** 불린 것 | ★ 언어는 「끼운다」까지만 정한다. 호출 수는 **이 판의 관찰** |
| `help:` 의 처방(`*&c + b`·`clone`) | ★ 진단 품질에 달렸다. 틀린 처방이 **고쳐질 수 있다** |
| 결함이 E0308·E0369·E0277 중 **무엇으로 나오나** | ★ 추론이 어디까지 타입을 정했느냐에 달렸다(3번·4번 답) |
| `std::ops` 파일 목록의 **불안정 트레이트** | ★ `rust-docs` 판마다 바뀐다 |
| 진단의 `/rustc/ded5c06cf…/arith.rs:92:12`·`:77:1` | ★ **이 판의 커밋 해시와 줄 번호** |
| `` and 57 others `` 의 수 | ★ std 구성에 달렸다 |

★ **다시 찍는 법** — `capture.sh <새 디렉토리>` 를 그대로 돌리고 `normalize-shaky.py <원본> <새 디렉토리>` 로 견준다.
**이 주제에는 흔들려야 할 칸이 없다** — 전부 한 글자도 같아야 한다.
