# rust/syntax/30 — 연산자 오버로딩(`std::ops`)·`Index`·`Deref` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [std — `std::ops` 모듈](https://doc.rust-lang.org/std/ops/index.html) ·
> [`trait Add`](https://doc.rust-lang.org/std/ops/trait.Add.html) ·
> [`trait Index`](https://doc.rust-lang.org/std/ops/trait.Index.html) ·
> [`trait Deref`](https://doc.rust-lang.org/std/ops/trait.Deref.html) ·
> [`struct Rc`](https://doc.rust-lang.org/std/rc/struct.Rc.html) ·
> [Reference — Operator expressions](https://doc.rust-lang.org/reference/expressions/operator-expr.html) ·
> [Reference — Index expressions](https://doc.rust-lang.org/reference/expressions/array-expr.html#array-and-slice-indexing-expressions) ·
> [Reference — Method-call expressions](https://doc.rust-lang.org/reference/expressions/method-call-expr.html).
> ★ 위 문서는 **이 머신의 `rust-docs`(1.92.0) 로컬 사본**을 열어 읽었다. `std::ops` 의 트레이트 목록은 **그 사본의 파일 목록을 블록으로** 실었다((5)).
> **실행 검증** — 이 문서의 모든 출력·에러는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서\
> **`rustc --edition 2021 <파일>.rs`** 로 실제로 돌려 받은 것이다.\
> ★★ **`--edition` 을 빼면 에디션 2015 다** — 에디션을 안 밝힌 결과는 다른 언어를 컴파일한 것과 같다.\
> ★★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.
> 소스 펜스도 캡처가 찍었다(첫 줄 `// <파일명>.rs` 가 실제로 컴파일한 파일 이름이다).\
> ★★ **외부 크레이트를 하나도 쓰지 않았다**(네트워크 없음).
> **버전** — `std::ops` 의 산술·`Index`·`Deref` 트레이트는 전부 **1.0.0** 이고, `AddAssign` 같은 복합 대입 트레이트는 **1.8.0** 부터다(std 문서의 배지).
> **전부 에디션과 무관하다.**
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
| 안 흔들린다 | **종료 코드 0 · 1** | 컴파일 실패는 1 이다. 이 주제에는 패닉 블록이 없다 |
| 안 흔들린다 | 에러 번호·제목·`= note:`·`help:` 줄·`파일:줄:칸` | 같은 rustc 판에서 고정이다 |
| 안 흔들린다 | 진단에 박히는 `/rustc/ded5c06cf…/library/core/src/ops/arith.rs:92:12` | ★ **이 rustc 판의 커밋 해시와 줄 번호**다. 판이 바뀌면 바뀐다 |
| 안 흔들린다 | `deref` 호출 **횟수**((7)) | 셀 수 있는 계수다. ★ 다만 **몇 번 부르나는 언어가 정하지 않는다**(§구현 세부) |
| 안 흔들린다 | `std::ops` 의 **파일 목록**((5)) | 같은 `rust-docs` 판에서 고정이다. ★ **불안정 트레이트도 섞여 있다** — 판이 오르면 바뀐다 |

★ 정규화 규칙은 **기본 넷**만 썼고 **하나도 걸리지 않았다**(제출 전 재대조).

## 한눈에 — 쉽게 말하면

**Rust 의 연산자는 「기호」가 아니라 「이름이 정해진 메서드 호출」이다.**
`a + b` 는 `Add::add(a, b)` 이고, **그 메서드가 `self` 를 값으로 받으므로 `a` 가 옮겨 간다.**

| 비유 | 실체 |
|---|---|
| 「**기호마다 정해진 창구 번호**」 | ★ **`std::ops` 의 트레이트** — `+` 는 `Add`, `+=` 는 `AddAssign`, `-x` 는 `Neg`, `a[i]` 는 `Index`((1)·(5)) |
| 「**창구에 서류를 맡기면 돌려받지 못한다**」 | ★★★ **`add(self, rhs)`** — 두 피연산자를 **값으로 받는다.** `Copy` 가 아니면 **옮겨 간다**((1)) |
| 「**복사본을 맡기는 손님**」 | **`Copy` 타입** — 옮기는 대신 복사되어 원본이 남는다((2)) |
| 「**서류는 보여 주기만 하는 창구**」 | ★★ **`impl Add for &T`** — 참조를 받는 판을 따로 둔다. **조합마다 따로** 적어야 한다((3)) |
| 「**창구가 돌려주는 서류의 종류**」 | **`Output` 연관 타입** — 결과 타입. 입력과 달라도 된다((4)) |
| 「**창구가 아예 없는 기호**」 | ★ **`&&`·`\|\|`·`=`** — 트레이트가 없어 **오버로드할 수 없다**. 비교는 `std::ops` 가 아니라 **`PartialEq`/`PartialOrd`**((5)) |
| 「**대리인이 문을 열어 주는 건물**」 | ★★ **`Deref`** — `*x`·메서드 호출·`&x` 강제에서 **컴파일러가 몰래 `deref()` 를 끼운다**((7)) |
| 「**대리인을 상속 서류로 착각하기**」 | ★★★ **`Deref` 로 상속 흉내** — 이름이 겹치면 **바깥이 이기고**, 안쪽은 **바깥을 모르며**, **트레이트 구현은 안 따라온다**((8)) |

- ★★★ **판정은 한 줄이다 — 「연산자를 쓰면 피연산자가 옮겨 간다고 가정하라.」**
  `Copy` 타입이거나 **참조에 구현해 둔 경우만** 예외다. 증거가 `E0382` 와 그 `note:` 「**calling this operator moves the left-hand side**」다((1)).
- ★★ **`Deref` 는 「포인터처럼 보이는 타입」에만** 단다 — 상속을 흉내 내면 **메서드 해석이 바뀌고**(누가 불리나), **경계는 통과하지 않는다**((8)).

```text
   a + b 가 컴파일러 안에서 무엇이 되나

   a + b          ──▶   Add::add(a, b)        ← fn add(self, rhs: Rhs) -> Self::Output
                             │  │
                             │  └── b 를 값으로 받는다
                             └───── a 를 값으로 받는다 ── Copy 가 아니면 ✘ 이후 a 사용 = E0382 (1)

   &a + &b        ──▶   Add::add(&a, &b)      ← impl Add<&Poly> for &Poly 가 있어야 (3)
                                                 참조는 Copy 라 둘 다 남는다

   a += b         ──▶   AddAssign::add_assign(&mut a, b)      ← a 는 빌려 간다 (2)
   -a             ──▶   Neg::neg(a)
   a[i]           ──▶   *Index::index(&a, i)  ← ★ 결과는 &Output 이고 * 가 붙어 들어간다 (6)
   a < b          ──▶   PartialOrd::lt(&a, &b)        ← std::ops 가 아니다 (5) · 28번
   a && b         ──▶   (트레이트 없음) bool 만 받는다    ✘ E0308 (5)


   *x · x.method() · &x → &Target  ──▶  Deref::deref(&x) 를 컴파일러가 끼운다 (7)

   메서드 이름을 찾는 순서 (자동 역참조)
   Dog 에서 찾는다 ──있으면 끝── Dog::name   ← ★ 바깥이 이긴다 (8)
        │ 없으면
        ▼ deref
   Animal 에서 찾는다 ────────── Animal::describe  ← 그 안의 self.name() 은 Animal::name (8)
```

> **연산자 오버로딩(operator overloading)** — 기호 연산자가 사용자 타입에서 무슨 일을 할지 정의하는 것.\
> 예: `impl Add for Poly` 를 쓰면 `Poly + Poly` 가 컴파일된다.

> **역참조 강제(deref coercion)** — `&T` 를 기대하는 자리에 `&U` 를 주면 `U: Deref<Target = T>` 일 때 **컴파일러가 `deref` 를 끼워 맞추는 것**.\
> 예: `&String` 을 `&str` 자리에 넣으면 된다. 정본은 [목록의 **43번 주제**](../43-deref-coercion-and-smart-pointers/)다.

> **스마트 포인터(smart pointer)** — 값을 가리키면서 **소유·해제 규칙을 더 얹은** 타입. std 문서는 `Deref` 를 구현한 타입을 흔히 이렇게 부른다고 적는다.\
> 예: `Box<T>`·`Rc<T>`·`String`.

## 이 주제가 답하려는 질문

1. ★★★ **`+` 를 구현하면 소유권이 어떻게 움직이나** — 무엇이 옮겨 가고, 어떻게 안 옮기게 하나((1)·(2)·(3)).
2. ★★ **어떤 기호가 어떤 트레이트로 가고, 어떤 기호는 못 건드리나**((4)·(5)·(6)).
3. ★★★ **`Deref` 를 남용하면 안 되는 이유는 무엇인가** — 「상속」 흉내가 **어디서 깨지나**를 출력으로((7)·(8)·(9)).

★ [**29번 주제**](../29-conversion-traits-from-into-tryfrom-asref-borrow/)가 「값을 다른 타입으로 **바꾸는** 표준 트레이트」였다면
여기는 「**기호를 메서드로 바꾸는** 표준 트레이트」다. 둘 다 **컴파일러가 이름을 알고 있는 트레이트**다.
★ [**26번 주제**](../26-orphan-rule-and-newtype/) (5)가 `Deref` 로 newtype 의 **불변식이 새는 것**을 보였다 —
**여기는 그 반대편**, `Deref` 가 **메서드 해석과 트레이트 경계에서 어떻게 구는가**다. 겹치지 않는다.

## 동작 방식

### (0) 이 주제가 쓰는 네 창

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **연산자를 쓴 뒤 피연산자를 다시 쓰기** | 연산자가 **소유권을 옮긴다**는 것 — E0382 와 그 note((1)) | ★ **이 주제의 본체 ①** |
| ★★★ **이름을 겹쳐 두고 누가 불리나 찍기** | `Deref` 가 **메서드 해석을 바꾼다**는 것((8)) | ★ **이 주제의 본체 ②** |
| ★★ **`deref()` 안에 계수기 달기** | 컴파일러가 **몰래 끼운 호출의 수**((7)) | ★ 이 주제의 고유 창 |
| **조합을 하나씩 비워 두고 던지기** | 연산자 구현은 **조합마다 따로**라는 것 — E0308·E0369((3)) | 「에러도 출력이다」 |

★★ **「부적용인 창」** — **실행 시간·기계어**다. `&a + &b` 가 `a + b` 보다 싼지 비싼지는 **이 주제의 질문이 아니고 재지도 않았다.**
여기서 묻는 것은 「**컴파일되나, 무엇이 남나**」뿐이다.
★ **「같은 질문을 다른 창으로」 하나** — 「`std::ops` 에 `&&` 트레이트가 **없다**」는 것을 에러 문구 대신
**설치된 std 문서의 파일 목록**으로 물었다((5)). 에러는 「`bool` 을 기대했다」고만 말하고 「트레이트가 없다」고는 말하지 않기 때문이다.

### (1) ★★★ `a + b` 는 `a` 를 옮긴다

**언제 쓰나** — 값 타입(`Copy` 가 아닌)에 `Add` 를 구현할 때. **한 번 더하면 `a` 는 사라진다.**

```rust
// r30_move.rs
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
```

```text
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

- ★★★ **E0382** — `` borrow of moved value: `a` ``. 19행의 `a + b` 가 `a` 를 옮겼고 21행이 그것을 다시 썼다.
  밑줄이 **어디서 옮겼는지를 연산자 전체**(`a + b`)로 짚고 「**`a` moved due to usage in operator**」라고 적는다.
- ★★ **`note: calling this operator moves the left-hand side`** — rustc 가 **std 의 `arith.rs:92:12`** 를 가리킨다.
  그 자리가 `fn add(self, rhs: Rhs) -> Self::Output` 의 **`self`** 다. **값으로 받는 `self`** 가 이동의 원인이다.
- ★ `b` 도 값으로 들어갔다 — `rhs: Rhs` 도 값이다(시그니처에서 읽은 것이다). 이 블록은 **`a` 만** 다시 써서 에러가 한 건이다.
- ★ [**14번 주제**](../14-string-vs-str/) (6)의 「**`+` 는 왼쪽을 먹는다**」(`String + &str`)가 **바로 이 규칙의 std 판**이다.
  `String` 의 `Add` 구현이 `impl Add<&str> for String` 이라 **왼쪽만 옮기고 오른쪽은 빌린다.** 규칙은 문자열 전용이 아니라 **`Add` 의 시그니처**다.
- ★ **`help:` 가 `Clone` 을 권한다** — `Poly` 가 `Clone` 을 안 가졌으므로 「구현하면 복제할 수 있다」고 적는다. **복제는 해결이 아니라 비용**이다 — (3)이 대안이다.

### (2) `Copy` 면 안 옮긴다 — `+=` 는 빌려 간다

**언제 쓰나** — 작은 값 타입(좌표·벡터·돈). **`Copy` 를 붙일 수 있으면** 연산자가 가장 자연스럽다.

```rust
// r30_copy.rs
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
```

```text
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

- **`a + b` 뒤에도 `a` 가 산다** — `V2` 가 `Copy` 라 `add(self, …)` 에 **복사본**이 들어갔다. 소유권 규칙은 같고 **옮겨 간 것이 복사본**일 뿐이다([**09번 주제**](../09-copy-clone-and-drop/)).
- ★ **`AddAssign::add_assign(&mut self, …)`** — `+=` 는 **왼쪽을 빌려 간다.** 그래서 `m` 은 `mut` 여야 하고, **옮겨 가지 않는다.**
  `Copy` 가 아닌 타입에서도 `+=` 는 왼쪽을 잃지 않는다 — **`+` 와 `+=` 는 소유권 모양이 다르다.**
- **`Neg::neg(self)`** 도 값으로 받는다. 마지막 줄 `a + -a == 0` 의 `==` 는 `derive(PartialEq)` 다 — `std::ops` 가 아니다((5)).

### (3) ★★ 참조에 구현한다 — 그리고 조합마다 따로다

**언제 쓰나** — `Copy` 가 안 되는 타입(힙을 가진 것)에서 **피연산자를 살리고** 싶을 때. std 의 `&i32 + &i32` 가 같은 관용이다.

```rust
// r30_ref.rs
// 참조에 구현한다 — &a + &b 는 아무도 안 옮긴다
use std::ops::Add;

#[derive(Debug)]
struct Poly(Vec<i32>);

fn at(p: &Poly, i: usize) -> i32 {
    p.0.get(i).copied().unwrap_or(0)
}

impl Add for &Poly {
    type Output = Poly; // ★ 결과는 새 값이다 — 참조가 아니다
    fn add(self, rhs: &Poly) -> Poly {
        let n = self.0.len().max(rhs.0.len());
        Poly((0..n).map(|i| at(self, i) + at(rhs, i)).collect())
    }
}

fn main() {
    let a = Poly(vec![1, 2]);
    let b = Poly(vec![10, 20, 30]);
    let c = &a + &b;
    println!("c = {:?}", c);
    println!("a = {:?} · b = {:?}  ★ 둘 다 산다", a, b);
    let d = &c + &c;
    println!("d = {:?}", d);
}
```

```text
===== rustc --edition 2021 r30_ref.rs =====
(exit 0)
===== ./r30_ref =====
c = Poly([11, 22, 30])
a = Poly([1, 2]) · b = Poly([10, 20, 30])  ★ 둘 다 산다
d = Poly([22, 44, 60])
(exit 0)
```

- ★★ **`impl Add for &Poly`** — 왼쪽 타입이 **`&Poly`** 다. `Rhs` 의 기본값이 `Self` 라 오른쪽도 `&Poly` 가 됐다.
  **참조는 `Copy`** 이므로 `&a` 를 값으로 넘겨도 **`a` 는 그대로다**(24행 「둘 다 산다」).
- ★ **12행 `type Output = Poly`** — 결과는 **새 값**이다. 참조끼리 더해 참조가 나오는 것이 아니다.

**참조 판만 두고 다른 조합을 쓰면.**

```rust
// r30_mixed.rs
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
```

```text
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

- ★★ **에러 2건, 번호가 다르다** — 비대칭인 두 실수가 **다른 진단**으로 온다.
  - **18행 `&c + b`(참조 + 값) — E0308.** 왼쪽 `&Poly` 의 `Add` 구현이 **하나뿐**이라 rustc 가 오른쪽을 `&Poly` 로 정했고, 값 `Poly` 가 와서 **타입 불일치**다.
    ★ `help:` 의 `*&c + b` 는 **틀린 처방**이다 — 아래에서 그대로 따라 던졌다.
  - **19행 `a + &c`(값 + 참조) — E0369** `` cannot add `&Poly` to `Poly` ``. 왼쪽 `Poly` 에는 `Add` 구현이 **하나도 없다.**
**`help:` 를 그대로 따르면.**

```rust
// r30_mixed_help.rs
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
```

```text
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

- ★ **E0369** — `` cannot add `Poly` to `Poly` ``. `*&c` 가 왼쪽을 `Poly` 로 바꾸자 이번에는 **`Poly + Poly` 구현이 없다.**
  **진단의 `help:` 는 틀릴 수 있다** — 한 자리의 타입만 맞추는 제안이라 **다음 자리를 안 본다**(구현 세부).

**std 의 정수는 네 조합을 다 가진다.**

```rust
// r30_int_combos.rs
// std 의 정수는 네 조합을 다 가진다
fn main() {
    let (x, y) = (1_i32, 2_i32);
    println!("{} {} {} {}", x + y, &x + y, x + &y, &x + &y);
    println!("x 는 그대로 {}", x);
}
```

```text
===== rustc --edition 2021 r30_int_combos.rs =====
(exit 0)
===== ./r30_int_combos =====
3 3 3 3
x 는 그대로 1
(exit 0)
```

- ★★★ **연산자 구현은 네 조합이 전부 따로다** — `T + T` · `&T + T` · `T + &T` · `&T + &T`.
  std 의 정수는 **네 벌을 다 가져서** 네 식이 전부 `3` 이다. 내 타입에서는 **필요한 조합만** 적는다.

### (4) `Output` 은 연관 타입, `Rhs` 는 파라미터

**언제 쓰나** — 단위가 있는 수(길이 × 수, 길이 × 길이). **오른쪽 타입마다 다른 결과**를 줄 때.

```rust
// r30_scalar.rs
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
```

```text
===== rustc --edition 2021 r30_scalar.rs =====
(exit 0)
===== ./r30_scalar =====
m * 2.0 = Meters(6.0)
m * m   = 9.0
2.0 * m = Meters(6.0)
(exit 0)
```

- ★★ **`Meters` 에 `Mul` 이 두 번 구현됐다** — `Mul<f64>` 와 `Mul<Meters>`. **`Rhs` 가 제네릭 파라미터**라 한 타입에 여러 번 된다.
  그리고 **결과 타입이 다르다** — 길이 × 수는 `Meters`, 길이 × 길이는 **`f64`**(넓이). `Output` 은 **구현마다 하나**인 연관 타입이다.
  [**25번 주제**](../25-traits-definition-impl-default-methods-and-associated-types/)가 「`Add<Rhs = Self>` 는 **입력**에 제네릭 파라미터를 쓴다」며 이 주제로 넘긴 자리가 여기다.
- ★★ **21행 `impl Mul<Meters> for f64`** — **왼쪽이 남의 타입**(`f64`)인데 통과했다. 고아 규칙은 `Meters` 가 **파라미터 자리에 있는 내 타입**이라 허용한다([**26번 주제**](../26-orphan-rule-and-newtype/)).
  `2.0 * m` 을 쓰려면 **이 구현을 따로 적어야** 한다 — `m * 2.0` 이 된다고 저절로 생기지 않는다(**교환 법칙은 컴파일러가 모른다**).

**21행 구현만 지우면**(소스 전문을 같이 싣는다).

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

- ★ **`2.0 * m` 한 줄만** 깨지고 번호는 **E0277** 이다. 왼쪽이 **타입이 정해지지 않은 리터럴 `{float}`** 이라 「`{float}: Mul<Meters>` 인가」라는 트레이트 질문이 됐다((3)의 E0369 는 왼쪽이 `Poly` 로 정해져 있었다).
- ★ 대비 — Python 은 `__mul__` 이 없으면 **오른쪽의 `__rmul__` 을 찾는다**([`oop-basics/`](../../../../oop-basics/) §19). Rust 에는 그런 **대체 탐색이 없다** — 왼쪽 타입의 `impl` 하나로 끝난다.

### (5) ★ `std::ops` 밖 — 비교는 다른 트레이트, `&&` 는 트레이트가 없다

**언제 쓰나** — 「이 기호도 오버로드되나」를 판정할 때.

```rust
// r30_notops.rs
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
```

```text
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

- ★ **18행 `a < b` — E0369** 이고 `note:` 가 「**`PartialOrd` might be missing**」이라 적는다. 비교 연산자는 `std::ops` 가 아니라 **`std::cmp` 의 `PartialOrd`** 로 간다.
  `==` 도 같다(`PartialEq`). 그 계약은 [**28번 주제**](../28-partialeq-eq-partialord-ord-and-hash-contracts/)가 정본이다.
- ★★ **19행 `a && b` — E0308 두 건**(양쪽 피연산자 각각). 진단은 「**expected `bool`, found `Flag`**」 — `&&` 는 **`bool` 만 받는 내장 연산자**다.
  **「오버로드할 트레이트가 없다」고는 말하지 않는다** — 그래서 트레이트 목록을 **다른 창**으로 물었다.

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

- ★★ **`std::ops` 에 `And`·`Or`·`Assign` 같은 이름이 없다.** 있는 것은 `BitAnd`(`&`)·`BitOr`(`|`)·`Not`(`!`) — **비트 연산자**다.
  **`&&`·`||` 는 단락 평가(오른쪽을 안 볼 수 있음)** 라 「두 값을 받는 메서드」로 표현할 수 없고, **`=` 는 이동·복사 그 자체**라 가로챌 자리가 없다.
  (Reference 의 「lazy boolean operators」 절이 `&&`·`||` 를 「**불리언 타입 피연산자에 쓴다**」고 정의하고,
  「**오른쪽은 왼쪽이 답을 정하지 않을 때만 평가한다**」고 적는다 — 단락 평가가 이유라는 것은 **그 정의에서 읽은 설명**이다. 목록 자체는 블록이 증거다.)
- ★ 목록에는 **불안정 트레이트도 섞여 있다**(`Coroutine`·`Try`·`Residual`·`CoerceShared` 등) — 파일이 있다고 안정 API 인 것은 아니다.
  복합 대입은 `AddAssign`·`SubAssign` … 으로 **따로** 있다((2)).

### (6) `Index` 는 `&T` 를 돌려주고, `a[i]` 는 `*a.index(i)` 다

**언제 쓰나** — 컨테이너 모양의 내 타입에 `[]` 를 줄 때.

```rust
// r30_index.rs
// Index 는 &T 를 돌려주고, grid[i] 는 *grid.index(i) 다
use std::ops::{Index, IndexMut};

struct Row(Vec<String>);

impl Index<usize> for Row {
    type Output = String;
    fn index(&self, i: usize) -> &String {
        &self.0[i]
    }
}

impl IndexMut<usize> for Row {
    fn index_mut(&mut self, i: usize) -> &mut String {
        &mut self.0[i]
    }
}

fn main() {
    let mut r = Row(vec![String::from("a"), String::from("b")]);
    println!("r[0]         {}", r[0]); // 읽기 — Index
    println!("r[0].len()   {}", r[0].len()); // 자동으로 빌린다
    r[1].push('!'); // 쓰기 — IndexMut
    println!("r[1]         {}", r[1]);
    let first: &String = &r[0]; // & 를 붙이면 참조
    println!("&r[0]        {}", first);
    println!("*r.index(0)  {}", *r.index(0)); // ★ 같은 것을 손으로 펼친 꼴
}
```

```text
===== rustc --edition 2021 r30_index.rs =====
(exit 0)
===== ./r30_index =====
r[0]         a
r[0].len()   1
r[1]         b!
&r[0]        a
*r.index(0)  a
(exit 0)
```

- **`index(&self, i) -> &String`** — 참조를 돌려준다. 그런데 21행 `r[0]` 은 **`String` 자리**(자리 표현식)로 쓰였다 —
  Reference 가 `a[b]` 를 **`*std::ops::Index::index(&a, b)`** 로 정의하기 때문이다. **`*` 가 붙어 들어간다.**
- 22행 `r[0].len()` 은 그 자리에서 **메서드를 빌려** 부른다. 23행 `r[1].push('!')` 는 **가변 자리**라 `IndexMut` 이 쓰였다.
- 27행 `*r.index(0)` 은 **컴파일러가 하는 일을 손으로 적은 꼴**이다 — 21행과 같은 출력이다.

**그 `*` 때문에 — 인덱스로 꺼내 옮기려 하면.**

```rust
// r30_index_move.rs
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
```

```text
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

- ★★ **E0507** — `` cannot move out of index of `Row` ``. `r[0]` 이 `*r.index(0)` 이라 **참조 뒤의 값을 옮기려는 것**이 된다.
  `help:` 둘이 정석이다 — **`&r[0]` 로 빌리거나, `.clone()` 으로 복제한다.** `Vec` 도 똑같이 막힌다(그래서 `Vec::remove`·`swap_remove`·`mem::take` 가 따로 있다 — [목록의 **44번 주제**](../44-drop-mem-drop-replace-and-take/)).

### (7) `Deref` — 스마트 포인터 관용구, 그리고 컴파일러가 끼운 호출 수

**언제 쓰나** — 값을 **감싸되 안쪽처럼 쓰이게** 하는 포인터 모양의 타입(`Box`·`Rc`·`String`·`Vec`).

```rust
// r30_deref.rs
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
```

```text
===== rustc --edition 2021 r30_deref.rs =====
(exit 0)
===== ./r30_deref =====
*t 로 꺼내면       hello
t.len()            5
&t 를 &str 자리에  5
deref 호출 횟수    3
(exit 0)
```

- ★★ **`deref` 가 세 번 불렸다** — 소스에 `deref()` 라는 글자는 **17행 정의 하나뿐**이다. 호출은 **컴파일러가 끼웠다.**
  1. **29행 `*t`** — 명시 역참조. `*t` 는 `*Deref::deref(&t)` 다.
  2. **30행 `t.len()`** — 메서드 호출. `Tracked` 에 `len` 이 없어 **자동 역참조**로 `String::len` 을 찾았다.
  3. **31행 `takes_str(&t)`** — **역참조 강제**. `&Tracked<String>` → `&String` → `&str` 로 **두 번 벗겼는데**
     두 번째(`String` → `str`)는 **`String` 의 `Deref`** 라 이 계수기에 안 잡혔다. 그래서 **3 이다**(4 가 아니다).
- ★ 역참조 강제의 **전이 규칙**(몇 단계까지 벗기나, 어디서 무너지나)은 [**14번 주제**](../14-string-vs-str/) (4)와 [목록의 **43번 주제**](../43-deref-coercion-and-smart-pointers/)가 정본이다 — 여기는 **호출이 몰래 끼워진다**는 것만 센다.
- ★ std 의 `Deref` 문서가 **경고**를 단다 — 「**컴파일러가 `Deref::deref` 호출을 조용히 끼운다**. 그래서 역참조 강제가 **바람직할 때만** 구현하라」.

### (8) ★★★ `Deref` 로 「상속」을 흉내 내면 — 세 군데서 깨진다

**언제 쓰나** — 쓰지 않는다. **이 절은 「왜 안 쓰나」의 증거다.**

```rust
// r30_deref_inherit.rs
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
```

```text
===== rustc --edition 2021 r30_deref_inherit.rs =====
(exit 0)
===== ./r30_deref_inherit =====
d.name()       Dog(멍)
d.describe()   나는 Animal(멍)
(*d).name()    Animal(멍)
(exit 0)
```

- ★★ **① 이름이 겹치면 바깥이 이긴다** — `d.name()` 은 **`Dog::name`**. 메서드 찾기는 **`Dog` 에서 먼저** 찾고, 있으면 **`deref` 를 안 한다.**
  그래서 **나중에 `Dog` 에 같은 이름을 하나 추가하면 기존 호출이 조용히 다른 함수로 간다** — 에러도 경고도 없다.
- ★★★ **② 안쪽은 바깥을 모른다** — `d.describe()` 는 **`나는 Animal(멍)`** 이다. `describe` 는 `Animal` 의 메서드이고,
  그 안의 `self` 는 **`&Animal`** 이라 13행 `self.name()` 은 **`Animal::name`** 을 부른다. **`Dog::name` 은 「재정의」가 아니다** — 가상 디스패치가 없다.
  상속이 있는 언어에서 기대하는 「`Dog(멍)`」이 **안 나온다.**
- ③은 트레이트다 — 아래 두 블록.

```rust
// r30_deref_trait_run.rs
// 같은 Dog — 메서드 호출과 구체 타입 자리만 남기면
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

fn as_animal(a: &Animal) -> String {
    a.speak()
}

fn main() {
    let d = Dog { base: Animal };
    println!("{}", d.speak()); // 메서드 호출 — 자동 역참조로 된다
    println!("{}", as_animal(&d)); // 구체 타입 자리 — 역참조 강제로 된다
}
```

```text
===== rustc --edition 2021 r30_deref_trait_run.rs =====
(exit 0)
===== ./r30_deref_trait_run =====
...
...
(exit 0)
```

```rust
// r30_deref_trait.rs
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
```

```text
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

- ★★★ **③ 트레이트 구현은 안 따라온다** — 앞 블록의 **메서드 호출 `d.speak()`**(자동 역참조)와
  **구체 타입 자리 `as_animal(&d)`**(역참조 강제)는 **된다**. 그런데 뒤 블록 39행의 **제네릭 경계 `T: Speak`** 는 **E0277** —
  「**the trait `Speak` is not implemented for `Dog`**」, 그리고 `help:` 가 「**`Speak` is implemented for `Animal`**」이라고까지 적는다.
- ★★ **왜 갈리나** — 자동 역참조와 역참조 강제는 **「이 자리에 무엇이 와야 하나」가 이미 정해진 곳**에서만 일어난다(메서드 이름·구체 타입).
  제네릭 경계는 **`T` 를 먼저 `Dog` 로 정하고** 「`Dog: Speak` 인가」를 묻는다 — 거기에는 **강제가 끼어들 자리가 없다.**
  [**26번 주제**](../26-orphan-rule-and-newtype/) (5)가 「트레이트 구현은 `Deref` 로 안 따라온다」고 **산문으로** 적었던 것을 여기서 **에러 전문으로** 확인했다.
- ★ **그래서 「상속 흉내」는 사용자에게 두 얼굴을 보인다** — `d.speak()` 가 되니 `Dog` 가 `Speak` 인 줄 알았는데 **라이브러리 함수에 넘기면 막힌다.**

### (9) `Rc` 는 왜 `strong_count` 를 메서드로 안 두나

**언제 쓰나** — 내가 `Deref` 를 다는 타입에 **메서드를 붙일지** 정할 때. std 가 답을 보여 준다.

```rust
// r30_rc_assoc.rs
// Rc 가 strong_count 를 메서드로 안 두는 이유
use std::rc::Rc;

fn main() {
    let r = Rc::new(String::from("a"));
    let r2 = Rc::clone(&r);
    println!("{}", Rc::strong_count(&r2));
    println!("{}", r.strong_count());
}
```

```text
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

- ★★ **E0599 — `this is an associated function, not a method`.** `Rc::strong_count(&r)` 는 되고 `r.strong_count()` 는 **없는 메서드**다.
  std 의 `Rc` 문서가 이유를 적는다 — 「**`Rc` 의 고유 메서드는 전부 연관 함수다. 안쪽 타입 `T` 의 메서드와 충돌하지 않게 하려는 것이다**」.
- ★★★ **(8)의 ①을 std 가 피해 간 방법이 이것이다** — `Rc<T>` 가 `.strong_count()` 를 메서드로 가지면
  **`T` 에 같은 이름의 메서드가 있을 때 `Rc` 쪽이 이겨 버린다.** 그래서 **`self` 를 안 받는 연관 함수**로만 둔다.
  `Deref` 문서도 같은 권고를 한다 — 「**`Target` 이 정해지지 않은 제네릭 포인터는 메서드를 두지 마라. 어떤 메서드든 `Target` 과 충돌할 수 있다**」(`Box<T>` 에 메서드가 거의 없는 이유).
- ★ 같은 이유로 **`Rc::clone(&r)`** 을 쓰는 관용이 있다(6행) — `r.clone()` 도 되지만 **무엇을 복제하는지**(`Rc` 인가 `T` 인가)가 읽는 사람에게 안 보인다.

### (10) 대비 — C++ 의 `operator+`, 두 컴파일러로

**언제 쓰나** — 「연산자가 피연산자를 옮기나」의 기본값이 언어마다 어떻게 다른지 가를 때. C++ 갈래에 이 번호의 폴더가 없어 **직접 던졌다.**

```cpp
// r30_opplus.cpp
// C++ — 관례대로 const T& 로 받는 operator+ : 더한 뒤에도 a 가 산다
#include <cstdio>
#include <utility>
#include <vector>

struct Poly {
    std::vector<int> c;
};

Poly operator+(const Poly& a, const Poly& b) { // ★ 참조로 받는다 — 아무도 안 옮긴다
    Poly r;
    for (std::size_t i = 0; i < a.c.size() || i < b.c.size(); ++i) {
        int x = i < a.c.size() ? a.c[i] : 0;
        int y = i < b.c.size() ? b.c[i] : 0;
        r.c.push_back(x + y);
    }
    return r;
}

int main() {
    Poly a{{1, 2}};
    Poly b{{10, 20, 30}};
    Poly c = a + b;
    std::printf("c.size=%zu  a.size=%zu (a 가 그대로다)\n", c.c.size(), a.c.size());
    Poly d = std::move(a) + b; // ★ 옮기려면 쓰는 사람이 고른다 — 그래도 const& 라 안 옮겨진다
    std::printf("d.size=%zu  a.size=%zu\n", d.c.size(), a.c.size());
    return 0;
}
```

```text
===== g++ -std=c++20 -Wall -Wextra r30_opplus.cpp -o r30_opplus_g =====
(exit 0)
===== ./r30_opplus_g =====
c.size=3  a.size=2 (a 가 그대로다)
d.size=3  a.size=2
(exit 0)
===== clang++ -std=c++20 -Wall -Wextra r30_opplus.cpp -o r30_opplus_c =====
(exit 0)
===== ./r30_opplus_c =====
c.size=3  a.size=2 (a 가 그대로다)
d.size=3  a.size=2
(exit 0)
```

- ★★ **`a + b` 뒤에 `a.size=2`** — 관례대로 **`const Poly&` 로 받는** `operator+` 라 아무도 안 옮겨 간다. (1)의 Rust 는 **같은 자리에서 E0382** 였다.
- ★★ **`std::move(a) + b` 뒤에도 `a.size=2`** — `std::move` 는 **옮겨도 된다는 표시**일 뿐이고, 받는 쪽이 **`const&` 라 실제로는 안 옮긴다.**
  **C++ 에서 이동은 「받는 시그니처」가 정한다** — Rust 도 사실 같다(`add(self, …)` 가 값으로 받아서 옮긴다). 다른 것은 **관례의 기본값**이다 —
  C++ 은 **참조로 받는 것이 관례**, Rust `Add` 는 **값으로 받는 것이 트레이트의 시그니처**다. 그래서 Rust 에서 안 옮기려면 (3)처럼 **참조 판을 따로** 구현한다.
- 두 컴파일러(g++ 13.3.0 · clang++ 18.1.3)의 출력이 **한 글자도 같았고** `-Wall -Wextra` 경고는 **0 건**이다.

## 문법 — 형태와 규칙

```text
   형태 — 기호와 트레이트

   a + b     impl Add<Rhs> for T { type Output; fn add(self, rhs: Rhs) -> Output }
   a += b    impl AddAssign<Rhs> for T { fn add_assign(&mut self, rhs: Rhs) }
   -a        impl Neg for T { type Output; fn neg(self) -> Output }
   !a        impl Not for T          a & b  BitAnd   a | b  BitOr   a ^ b  BitXor
   a << b    Shl   a >> b  Shr       a - b  Sub   a * b  Mul   a / b  Div   a % b  Rem
   a[i]      impl Index<Idx> for T { type Output; fn index(&self, i: Idx) -> &Output }   → *a.index(i)
   a[i] = v  impl IndexMut<Idx> for T { fn index_mut(&mut self, i: Idx) -> &mut Output }
   *a        impl Deref for T { type Target; fn deref(&self) -> &Target }
   a == b    PartialEq (std::cmp)    a < b   PartialOrd (std::cmp)        ← std::ops 가 아니다

   참조에 구현하는 관용
   impl Add for &Poly { type Output = Poly; fn add(self, rhs: &Poly) -> Poly { … } }


   금지 사례 — 던져서 받은 것

   let c = a + b;  이후  a 사용 (Copy 아님)          ✘ E0382  "calling this operator moves the left-hand side"
   &T + T      (impl Add for &T 만 있을 때)           ✘ E0308
   *&c + b     (위 E0308 의 help: 를 따르면)          ✘ E0369  T + T 구현이 없다
   T + &T      (T 에 Add 구현이 없을 때)              ✘ E0369
   a < b       (PartialOrd 없음)                     ✘ E0369  → derive(PartialEq, PartialOrd)
   a && b      (a·b 가 bool 이 아님)                  ✘ E0308  트레이트 자체가 없다
   let s = row[0];   (Output 이 Copy 아님)            ✘ E0507  → &row[0] 또는 .clone()
   Deref 흉내 타입을 T: Trait 경계에                   ✘ E0277
   rc.strong_count()                                ✘ E0599  → Rc::strong_count(&rc)
```

**규칙 불릿.**

- ★★★ **`add(self, rhs)` 는 둘 다 값으로 받는다** — `Copy` 가 아니면 **양쪽 다 옮겨 간다**((1)).
- ★★ **안 옮기려면 참조에 구현한다** — `impl Add for &T`. 조합(`T+T`·`T+&T`·`&T+T`·`&T+&T`)은 **전부 따로**((3)).
- ★ **`+=` 는 `&mut self`** — 왼쪽을 옮기지 않는다((2)).
- **`Output` 은 연관 타입, `Rhs` 는 제네릭 파라미터**(기본값 `Self`) — 오른쪽마다 다른 결과가 된다((4)).
- ★ **왼쪽이 남의 타입이어도 오른쪽이 내 타입이면 구현할 수 있다** — 교환 법칙은 **내가 따로 적는다**((4)).
- ★ **비교는 `PartialEq`/`PartialOrd`, `&&`·`||`·`=` 는 오버로드 불가**((5)).
- **`a[i]` 는 `*a.index(i)`** — 결과 자리에서 값을 옮기면 E0507((6)).
- ★★ **`Deref` 는 포인터 모양의 타입에만** — 메서드 이름이 겹치면 **바깥이 이기고**, 안쪽은 **바깥을 모르며**, **경계는 안 통과한다**((8)).
- ★ **`Deref` 를 다는 타입의 고유 기능은 연관 함수로** 둔다(`Rc::strong_count`)((9)).

## 어디서 틀리나

### 1. ★★★ 「`a + b` 는 읽기만 하니 `a` 는 그대로다」

**옮겨 간다**((1)). `add` 는 `self` 를 값으로 받는다. `Copy` 가 아닌 타입이면 E0382 이고, note 가 「**calling this operator moves the left-hand side**」라고 적는다.

### 2. ★★ 「`impl Add for &T` 하나면 섞어 써도 된다」

**조합마다 따로다**((3)). `&T + T` 는 **E0308**, `T + &T` 는 **E0369** — 번호까지 다르게 온다.
그리고 `help:` 가 권한 `*&c + b` 는 **틀린 처방**이다(왼쪽이 `T` 가 되면 `T + T` 구현이 필요하다).

### 3. ★ 「`m * 2.0` 이 되니 `2.0 * m` 도 된다」

**안 된다 — 따로 적는다**((4)). `impl Mul<Meters> for f64` 가 필요하다. 교환 법칙은 컴파일러가 모른다.

### 4. ★ 「비교 연산자도 `std::ops` 에 있겠지」

**없다**((5)). `<` 는 `PartialOrd`, `==` 는 `PartialEq` — `std::cmp` 다. `derive` 로 붙이는 것이 기본이다(28번).

### 5. ★ 「`&&` 를 내 타입에 오버로드할 수 있다」

**트레이트가 없다**((5)). 비트 연산 `&`(`BitAnd`)와 헷갈리기 쉽다. `&&` 는 **단락 평가**를 하는 `bool` 전용 연산자다.

### 6. ★★ 「`row[0]` 은 값을 준다」

**`*row.index(0)` — 참조 뒤의 자리다**((6)). 읽거나 빌리는 것은 되고 **옮기는 것은 E0507** 이다.

### 7. ★★★ 「`Deref` 를 달면 상속이 된다」

**세 군데서 깨진다**((8)). ① 같은 이름은 **바깥이 가로챈다** ② 안쪽 메서드는 **바깥의 「재정의」를 모른다**(`나는 Animal(멍)`)
③ **트레이트 경계는 통과하지 않는다**(E0277) — 그런데 메서드 호출은 되므로 **된다고 착각하기 쉽다.**
상속이 필요하면 **트레이트 + 합성**으로 쓴다(바깥이 트레이트를 직접 구현하고 안쪽에 위임한다).

### 8. ★ 「`deref` 는 내가 부를 때만 불린다」

**컴파일러가 끼운다**((7)). 한 줄에서 여러 번 불릴 수 있고 **소스에 글자가 없다.** 그래서 `deref` 안에서 비싼 일·부수 효과를 하면 안 된다.

## 구현 세부사항 대 언어 보장

| 항목 | 무엇인가 | 근거 |
|---|---|---|
| `a + b` 가 `Add::add(a, b)` 인 것 | ★ **언어 보장** — Reference 의 operator expressions | (1)의 실측 |
| `add` 가 `self` 를 **값으로** 받는 것 | ★ **라이브러리 보장** — `trait Add` 의 시그니처 | (1)의 note |
| `a[i]` 가 `*Index::index(&a, i)` 인 것 | ★ **언어 보장** — Reference 의 index expressions | (6)의 실측 |
| `&&`·`\|\|`·`=` 를 **오버로드할 수 없는** 것 | ★ **언어 보장** — 대응 트레이트가 없다 | (5)의 목록·실측 |
| 메서드 찾기가 **바깥 타입부터**인 것 | ★ **언어 보장** — Reference 의 method-call expressions(후보를 수신자 타입부터 역참조하며 모은다) | (8)의 실측 |
| 제네릭 경계에 **역참조 강제가 안 끼는** 것 | ★ **언어 보장** — 강제는 **정해진 타입이 기대되는 자리**에서만 일어난다 | (8)의 E0277 |
| `deref` 가 **몇 번** 불리나 | ★ **구현 세부** — 언어는 「끼운다」까지만 정한다. 3 은 **이 판의 관찰** | (7)의 계수 |
| `help:` 의 처방(`*&c + b`·`clone`) | ★ **구현 세부** — 진단의 제안은 틀릴 수 있다 | (3)의 실측 |
| `std::ops` 목록의 **불안정 트레이트** | ★ **판에 매인다** | (5)의 목록 |
| 진단의 `/rustc/ded5c06cf…/arith.rs:92:12` | ★ **이 판의 값** | (1)·(3) |

## 언제 쓰고 언제 안 쓰나

- **연산자를 구현한다** — 수학적 의미가 **분명한** 타입(벡터·행렬·다항식·돈·단위). 기호를 보고 **놀랄 일이 없어야** 한다.
- ★ **`Copy` 가 되면 `Copy` 로** — 연산자와 가장 잘 맞는다((2)).
- ★ **힙을 가진 타입이면 참조 판을 함께** — `impl Add for &T` 를 두면 피연산자가 산다((3)). **필요한 조합만** 쓴다.
- **`+=` 를 따로 구현한다** — `a = a + b` 가 새로 할당하는 타입에서 `AddAssign` 은 **제자리에서** 바꿀 수 있다.
- **`Index` 를 구현한다** — 컨테이너 모양일 때. 범위 밖은 **패닉**이 관례다(`Vec` 처럼) — 실패를 값으로 주려면 `get` 메서드를 따로 둔다.
- ★★ **`Deref` 를 구현한다** — **포인터 모양일 때만**(감싼 것처럼 **쓰이는 것이 목적**인 타입). **상속·코드 재사용 목적으로 쓰지 않는다**((8)).
- ★ **`Deref` 타입에 기능을 붙일 때는 연관 함수로** — `Rc::strong_count` 처럼((9)).

## 핵심 문장

- ★★★ **연산자는 이름이 정해진 메서드 호출이고, `add` 는 `self` 를 값으로 받는다** — 그래서 `a + b` 는 `a` 를 옮긴다((1)).
- ★★ **안 옮기려면 `Copy` 거나 참조에 구현하고, 조합은 전부 따로다**((2)·(3)).
- ★ **비교는 `std::cmp`, `&&`·`||`·`=` 는 트레이트가 없다**((5)).
- ★ **`a[i]` 는 `*a.index(i)`** — 그래서 인덱스로 꺼내 옮기면 E0507 이다((6)).
- ★★★ **`Deref` 상속 흉내는 이름을 가로채고, 재정의가 안 먹고, 경계를 못 넘는다** — 포인터에만 단다((8)·(9)).

## 관련 자료

- [**14번 주제** — `String` 대 `&str`](../14-string-vs-str/) —
  ★ **경계**: (6)의 「`+` 는 왼쪽을 먹는다」가 **`String` 판**이고, (4)가 **역참조 강제의 전이 규칙**이다. 여기는 **`Add` 트레이트 일반**과 **`deref` 호출 수**만.
- [**26번 주제** — 고아 규칙과 newtype](../26-orphan-rule-and-newtype/) —
  ★ **경계**: (5)의 「`Deref` 로 되찾으면 **불변식이 샌다**」는 거기, 여기는 「**메서드 해석과 경계**」((8)). `impl Mul<Meters> for f64` 가 통과하는 이유도 거기다.
- [**28번 주제** — 비교·해시 계약](../28-partialeq-eq-partialord-ord-and-hash-contracts/) — 비교 연산자의 정본((5)).
- [**25번 주제** — 트레이트·연관 타입](../25-traits-definition-impl-default-methods-and-associated-types/) — `Rhs = Self` 기본 타입 파라미터를 여기로 넘겼다((4)).
- [**09번 주제** — `Copy`·`Clone`·`Drop`](../09-copy-clone-and-drop/) — (2)의 「옮겨 간 것이 복사본」.
- [**29번 주제** — 변환 트레이트](../29-conversion-traits-from-into-tryfrom-asref-borrow/) — 같은 「컴파일러가 이름을 아는 트레이트」의 변환 판.
- [목록의 **43번 주제**](../43-deref-coercion-and-smart-pointers/) — `Deref` 강제와 스마트 포인터. **역참조 강제의 정본**이다. (7)은 호출 수만 셌다.
- [목록의 **44번 주제**](../44-drop-mem-drop-replace-and-take/) — `mem::take`/`replace`. (6)의 E0507 을 푸는 다른 길.
- Go 의 임베딩 — [`go/syntax/18-embedding-and-field-method-promotion/`](../../../go/syntax/18-embedding-and-field-method-promotion/).
  ★ **대비**: Go 의 임베딩은 **승격된 메서드로 인터페이스를 만족한다**(그 편 (5)). **Rust 의 `Deref` 는 트레이트 경계를 못 넘는다**((8)의 E0277).
  둘 다 「안쪽 메서드가 바깥의 것을 모른다」는 같다 — 가상 디스패치가 아니다.
- Kotlin 의 클래스 위임 — [`kotlin/syntax/21-class-delegation-by/`](../../../kotlin/syntax/21-class-delegation-by/).
  ★ **대비**: 그 편 (2)의 「**위임 대상은 내 오버라이드를 모른다**」가 (8)의 `나는 Animal(멍)` 과 **같은 함정**이다.
  다른 것은 Kotlin `by` 는 **인터페이스를 구현한다**(포워딩 메서드를 컴파일러가 만든다) — Rust `Deref` 는 **아무 트레이트도 구현하지 않는다.**
- Python 의 연산자 오버로딩 — [`oop-basics/`](../../../../oop-basics/) §19~20(`__add__`·`__radd__`).
  ★ **대비**: Python 은 왼쪽이 모르면 **오른쪽의 `__radd__` 로 넘어간다**. Rust 는 **왼쪽 타입의 `impl` 하나**로 끝난다((4)).
- Python 의 컨테이너 프로토콜 — [`python/syntax/32-container-protocol/`](../../../python/syntax/32-container-protocol/). `x[i]` 가 `__getitem__` 으로 가는 것이 `Index` 와 같은 자리다.
- C++ 의 연산자 오버로딩 — C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md))의 **22번**(폴더 없음). 이 문서 (10)에서 **두 컴파일러로 직접 던졌다.**
- Kotlin 의 `operator fun` — Kotlin 갈래 목록([`kotlin/syntax/README.md`](../../../kotlin/syntax/README.md))의 **31번**(폴더 없음).

## 용어 풀이

- **연산자 오버로딩** — 기호 연산자를 사용자 타입에 정의하는 것. Rust 에서는 `std::ops`(산술·비트·인덱스·역참조)와 `std::cmp`(비교)의 트레이트를 구현한다.
- **`Rhs`** — 오른쪽 피연산자 타입. `Add<Rhs = Self>` 처럼 **기본값이 `Self`** 인 제네릭 파라미터다.
- **`Output`** — 연산 결과 타입. 구현마다 하나인 연관 타입.
- **복합 대입 연산자** — `+=`·`-=` 등. `AddAssign` 처럼 **`&mut self`** 를 받는 별도 트레이트.
- **자리 표현식(place expression)** — 값이 **있는 곳**을 가리키는 식. `a[i]`·`*p`·`x.f` 가 그렇다. 옮기면 원래 자리가 빈다.
- **자동 역참조(auto-deref)** — 메서드 호출에서 수신자에 `*` 를 필요한 만큼 붙여 가며 메서드를 찾는 것.
- **역참조 강제(deref coercion)** — `&U` 를 `&T` 자리에 넣을 때 `deref` 를 끼워 맞추는 것.
- **스마트 포인터** — 값을 가리키면서 소유·해제 규칙을 얹은 타입. `Deref` 를 구현한다.
- **연관 함수(associated function)** — `self` 를 안 받는 함수. `Rc::strong_count(&r)` 처럼 **타입 이름으로** 부른다.
- **단락 평가(short-circuit)** — 왼쪽만으로 답이 나면 오른쪽을 안 보는 평가. `&&`·`||` 가 그렇다.

## 더 들어가면

- **`DerefMut`** — `&mut` 판 역참조. [**26번 주제**](../26-orphan-rule-and-newtype/) (5)가 이것으로 불변식이 새는 것을 보였다.
- **`Fn`·`FnMut`·`FnOnce` 도 `std::ops` 에 있다** — `f(x)` 호출 기호의 트레이트다. 사용자가 직접 구현하는 것은 **불안정**이다([목록의 **34번 주제**](../34-closures-fn-fnmut-fnonce-and-move/)).
- **`RangeBounds`** — `a..b` 를 받는 API(`Vec::drain` 등)가 쓰는 트레이트. `..` 자체는 범위 **타입**을 만드는 문법이다.
- **`Try`·`FromResidual`** — `?` 를 다른 타입에 열어 주는 트레이트. (5)의 목록에 있지만 **불안정**이다.
- **`impl<'a> Add<&'a T> for &'a T` 의 수명** — 참조 판에 수명을 명시하는 꼴. (3)은 생략 규칙에 맡겼다([**12번 주제**](../12-lifetime-annotations-and-elision/)).
