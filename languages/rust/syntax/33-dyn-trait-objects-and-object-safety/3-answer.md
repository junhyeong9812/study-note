# rust/syntax/33 — `dyn Trait` 트레이트 객체와 객체 안전성 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서
> **`rustc --edition 2021`** 로 실제로 돌려 받은 것이다(C++ 블록은 `g++ 13.3.0` · `clang++ 18.1.3`).\
> ★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
> ★★ 블록 첫 줄 `===== 소스: <파일> =====` 아래가 **컴파일한 소스 전문**이고, **진단의 줄 번호는 그 파일 기준**이다.\
> ★★ **외부 크레이트를 하나도 쓰지 않았다**(네트워크 없음). **시간은 한 번도 재지 않았다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ 넓어지는 것은 DST 를 가리키는 포인터 — 크기는 vtable 에서 읽힌다

**출력.**

```text
===== 소스: r33_size.rs =====
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

**출력 — `dyn Shape` 자체의 크기.**

```text
===== 소스: r33_unsized.rs =====
// dyn Trait 자체의 크기를 물으면
trait Shape {
    fn area(&self) -> f64;
}

fn main() {
    let n = std::mem::size_of::<dyn Shape>();
    println!("{}", n);
}
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

**왜 그런가.**

- ★★ **`&Sq`·`Box<Sq>` 8, 나머지 일곱은 16.** `&dyn`·`Box<dyn>`·`*const dyn`·`&[u8]`·`&str` 이 전부 **포인터 + 메타데이터**다. `Option<&dyn Shape>` 도 16(널이 될 수 없는 자리를 `None` 으로 쓴다).
- ★★★ **`size_of_val` 이 `a=8 b=16` 으로 다르다** — 타입은 같은 `&dyn Shape` 이므로 컴파일러는 모른다. **실행 때 vtable 의 크기 칸**을 읽은 값이다(5번 답의 IR 에서 그 칸이 보인다).
- ★ **`size_of::<dyn Shape>()` 는 E0277** — `dyn Shape` 는 **크기가 없는 타입**이라 `Sized` 를 요구하는 자리에 못 온다.

### 2. ★★★ E0038 네 건 — 「vtable 을 만들 수 있어야 한다」

**출력.**

```text
===== 소스: r33_violations.rs =====
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

**왜 그런가.**

- ★★ **E0038 × 4**, `note:` 가 한 줄씩 — `A` 「**method `pick` has generic type parameters**」 · `B` 「**method `dup` references the `Self` type in its return type**」 ·
  `C` 「**it contains this associated `const`**」 · `D` 「**it requires `Self: Sized`**」.
- ★★★ **한 문장** — 첫 `note:` 「**for a trait to be dyn compatible it needs to allow building a vtable**」. 제네릭은 칸이 무한, `Self` 반환은 크기를 모르는 값, 상수는 함수가 아님, `Sized` 는 `dyn` 의 무크기와 모순.
- ★ `help:` 는 `A`·`B`·`C` 에 「**consider moving … to another trait**」, 넷 다에 「**only type `S` implements …; consider using it directly**」를 붙였다. `D` 에는 옮길 항목이 없어 앞 줄이 없다.

### 3. ★★★ 갈린 칸 7 / 9 — `const` 만 여전히 막힌다

**출력.**

```text
===== 소스: r33_grid.sh =====
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

**출력 — `const` 줄 오른쪽 칸의 전문.**

```text
===== 소스: r33_const_sized.rs =====
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

**왜 그런가.**

- ★★ **왼쪽 열 — `control`·`by_value` 만 ok, 일곱이 E0038.** `arg_self`(`&Self` 인자)는 「`Self` 를 수신자 밖에서 쓰지 마라」, `gat` 은 「제네릭 연관 타입이 없어야 한다」 조항이다.
- ★★ **`by_value` 는 처음부터 ok** — Reference 가 「**`self` 수신자(값)는 `where Self: Sized` 를 함의한다**」고 적는다. 값으로 받는 메서드는 **이미 명시적으로 디스패치 불가**다.
- ★★★ **오른쪽 열 — `const` 만 E0658**, 나머지 전부 ok. 갈린 칸은 **7 / 9** 이고, **안 갈린 줄은 `control`·`by_value`(둘 다 ok → ok)** 둘이다.
  `const` 줄은 **코드가 E0038 → E0658 로 바뀌었지만** 여전히 에러라 「갈린 칸」에 들어간다 — **풀린 칸은 6** 이다. 상수에 `where` 절을 다는 문법 자체가 **불안정**(generic const items)이다.

### 4. ★★ 24행 하나 — 번호 없는 에러

**출력.**

```text
===== 소스: r33_where_call.rs =====
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

**왜 그런가.**

- ★★ **24행 `d.scaled(2.0)` 만 에러.** 20행(실물 `Sq` 에서 호출)과 22행(`dyn` 만들기)은 통과했다 — `where Self: Sized` 는 **그 메서드를 vtable 에서 빼고**, 그래서 `dyn` 쪽에는 **그 메서드가 없다.**
- ★ **빠진 것 — `E` 번호와 `For more information…` 줄.** 「**the `scaled` method cannot be invoked on a trait object**」와 「**this has a `Sized` requirement**」만 있다.

### 5. ★★ 칸 다섯씩 — 첫 칸이 드롭, 순서는 트레이트 선언

**출력.**

```text
===== 소스: r33_vt.rs =====
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
===== rustc --edition 2021 -C opt-level=0 -C symbol-mangling-version=v0 --emit=llvm-ir -o r33_vt.ll r33_vt.rs =====
(exit 0)
===== grep -E '^@vtable' r33_vt.ll | c++filt =====
@vtable.0 = private unnamed_addr constant <{ [24 x i8], ptr, ptr, ptr }> <{ [24 x i8] c"\00\00\00\00\00\00\00\00\08\00\00\00\00\00\00\00\08\00\00\00\00\00\00\00", ptr @<std[836535f787e97d3]::rt::lang_start<()>::{closure#0} as core[2e27404414be4892]::ops::function::FnOnce<()>>::call_once::{shim:vtable#0}, ptr @std[836535f787e97d3]::rt::lang_start::<()>::{closure#0}, ptr @std[836535f787e97d3]::rt::lang_start::<()>::{closure#0} }>, align 8
@vtable.1 = private unnamed_addr constant <{ [24 x i8], ptr, ptr }> <{ [24 x i8] c"\00\00\00\00\00\00\00\00\08\00\00\00\00\00\00\00\08\00\00\00\00\00\00\00", ptr @<r33_vt[20af6a1668313135]::Sq as r33_vt[20af6a1668313135]::Shape>::area, ptr @<r33_vt[20af6a1668313135]::Sq as r33_vt[20af6a1668313135]::Shape>::label }>, align 8
@vtable.2 = private unnamed_addr constant <{ ptr, [16 x i8], ptr, ptr }> <{ ptr @core[2e27404414be4892]::ptr::drop_in_place::<r33_vt[20af6a1668313135]::Tagged>, [16 x i8] c" \00\00\00\00\00\00\00\08\00\00\00\00\00\00\00", ptr @<r33_vt[20af6a1668313135]::Tagged as r33_vt[20af6a1668313135]::Shape>::area, ptr @<r33_vt[20af6a1668313135]::Tagged as r33_vt[20af6a1668313135]::Shape>::label }>, align 8
(exit 0)
```

**왜 그런가.**

- ★★ **`@vtable.1`(Sq)** — `[24 x i8]`(8바이트 세 칸) + `area` + `label` = **다섯 칸.** 첫 칸 `\00…` 은 **드롭할 것이 없는** 타입의 빈 드롭 자리다.
- ★★ **`@vtable.2`(Tagged)** — **`ptr @drop_in_place::<Tagged>`** + `[16 x i8]`(두 칸) + `area` + `label` = **다섯 칸.** `String` 을 풀어야 하므로 드롭 칸에 함수가 들어갔다.
- ★★ **메서드는 `area` → `label`** — `impl` 에 적은 순서가 아니라 **트레이트 선언 순서**다(이 판의 관찰).
- ★ **크기는 `c" \00\00…"` 의 공백 글자** — 바이트 `0x20` = **32**(`String` 24 + `f64` 8). 다음 칸 `\08` 이 정렬이다. **칸 배치의 해석은 이 판의 읽기**다(Reference 는 배치를 적지 않는다).

### 6. ★★ `'static` 이 숨어 있었다 — 번호 없는 수명 에러

**출력.**

```text
===== 소스: r33_static.rs =====
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

**출력 — `+ 'a` 를 적으면.**

```text
===== 소스: r33_static_fix.rs =====
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
===== rustc --edition 2021 r33_static_fix.rs =====
(exit 0)
===== ./r33_static_fix =====
1 hi
(exit 0)
```

**왜 그런가.**

- ★★★ **「`'1` must outlive `'static`」** — 시그니처에 `'static` 은 없지만 **`Box<dyn Display>` 는 `Box<dyn Display + 'static>`** 이다(Reference 의 기본 트레이트 객체 수명 — `Box<T>` 는 `T` 에 수명 경계가 없으므로 `'static`).
- ★ **`E` 번호가 없다.** `help:` 도 없다. `Box<dyn Display + 'a>` 로 적으면 통과한다(`1 hi`).

### 7. ★★ E0225 — 그리고 `help:` 는 반쪽이었다

**출력 — 트레이트 둘.**

```text
===== 소스: r33_two.rs =====
// dyn 에 트레이트 둘을 더하기
use std::fmt::{Debug, Display};

fn main() {
    let a: Box<dyn Display + Send> = Box::new(1);
    println!("{}", a);
    let b: Box<dyn Display + Debug> = Box::new(2);
    println!("{}", b);
}
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

**출력 — `help:` 대로 새 트레이트만.**

```text
===== 소스: r33_two_help.rs =====
// help: 가 권한 대로 — 두 트레이트를 슈퍼트레이트로 둔 새 트레이트
use std::fmt::{Debug, Display};

trait NewTrait: Display + Debug {}

fn main() {
    let b: Box<dyn NewTrait> = Box::new(2);
    println!("{} {:?}", b, b);
}
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

**출력 — 담요 구현까지.**

```text
===== 소스: r33_two_blanket.rs =====
// 새 트레이트에 담요 구현을 더하면
use std::fmt::{Debug, Display};

trait NewTrait: Display + Debug {}
impl<T: Display + Debug> NewTrait for T {}

fn main() {
    let b: Box<dyn NewTrait> = Box::new(2);
    println!("{} {:?}", b, b);
}
===== rustc --edition 2021 r33_two_blanket.rs =====
(exit 0)
===== ./r33_two_blanket =====
2 2
(exit 0)
```

- **`dyn Display + Send` 는 되고 `dyn Display + Debug` 는 E0225** — 「**only auto traits can be used as additional traits in a trait object**」. vtable 은 **한 장**이다.
- ★★★ **`help:` 는 `trait NewTrait: Display + Debug {}` 를 권한다 — 그대로 하면 E0277**(「`{integer}: NewTrait` is not satisfied」, 「**this trait has no implementations**」).
  **`impl<T: Display + Debug> NewTrait for T {}`** 를 더해야 `2 2` 가 나온다.

### 8. ★ 업캐스팅은 1.86 부터, 다운캐스트는 `Any`

**출력 — 업캐스팅.**

```text
===== 소스: r33_super.rs =====
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
===== rustc --edition 2021 r33_super.rs =====
(exit 0)
===== ./r33_super =====
sq2 Sq(2.0)
debug Sq(2.0)
Sq(3.0)
(exit 0)
```

**출력 — `as` 로 되돌리기.**

```text
===== 소스: r33_cast.rs =====
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

**출력 — `Any`.**

```text
===== 소스: r33_any.rs =====
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
===== rustc --edition 2021 r33_any.rs =====
(exit 0)
===== ./r33_any =====
i32 7
String hi
other
u8 9
(exit 0)
```

- ★★ **`&dyn Named` → `&dyn Debug`, `Box<dyn Named>` → `Box<dyn Debug>` 가 통과**했다. 릴리스 노트가 **1.86.0** 「Stabilize upcasting trait objects to supertraits」(서머리 (0)). 이 판(1.92)에서 된다 — **1.85 이하는 이 문서가 돌려 보지 않았다**(툴체인이 하나뿐).
- ★ **`as &Sq` 는 E0605**(non-primitive cast). **대신 `Any`** — `downcast_ref::<T>()`(→ `Option`), `Box<dyn Any>` 의 `downcast::<T>()`(→ `Result`).
  **조건** — `Any` 는 `pub trait Any: 'static` 이라 **`'static` 이 아닌 참조를 품은 타입은 안 된다**(std 문서).

### 9. ★★ C++ 는 객체에, Rust 는 포인터에

**출력.**

```text
===== 소스: r33_vptr.cpp =====
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

- ★★ **C++** — `Plain` 8 · 가상 함수가 있는 **`Shape` 16** · `Shape*` **8**. **Rust** — `Sq(f64)` **8 그대로** · `&dyn Shape` **16**(1번 답).
- ★ **뜻** — C++ 는 가상 함수를 가진 클래스의 **모든 객체**가 vptr 만큼 크다(`dyn` 처럼 안 써도). Rust 는 **`dyn` 포인터를 만드는 자리에서만** 16 이 된다 — 배열에 `Sq` 를 백만 개 담아도 한 개 8바이트다.
  ★ C++ 의 vptr 위치는 **C++ 표준이 아니라 ABI(Itanium)의 관찰**이다.

### 10. ★★ 「적어도 포인터 크기」까지가 보장이다

- ★★ **Reference 의 두 절이 다르다** — DST 절은 「DST 포인터는 **두 배 크기**」, Type layout 절은 「**적어도** 포인터 크기·정렬이 보장된다. **지금은** 모든 DST 포인터가 `usize` 두 배지만 **기대지 마라**」.
  **더 정확한 쪽은 layout 절**이다 — 16 은 **이 판의 구현**으로 읽는다. [25번 주제](../25-traits-definition-impl-default-methods-and-associated-types/)도 「언어 보장은 아니다」로 적었다.
- ★ **vtable 칸 배치는 컴파일러가 정한다** — Reference 는 「각 메서드 구현의 함수 포인터가 든다」까지만 적는다. 드롭·크기·정렬의 **자리**는 5번 답의 **IR 읽기**다.

### 11. 벌 수는 31, 칸은 33 — 둘 다 시간을 안 쟀다

- ★★ [31번](../31-generics-trait-bounds-where-and-monomorphization/)은 **벌 수와 바이트**(제네릭 3·3·2·2벌 대 `dyn` 1벌 + 타입마다 `@vtable` 하나)를, 이 주제는 **포인터 바이트 · vtable 칸 · 위반 격자**를 셌다.
  **「`dyn` 은 느리다」는 두 문서 어디에서도 주장이 아니다** — 시간을 한 번도 안 쟀다. 논증의 정본은 [`언어-특성/README.md`](../../언어-특성/README.md) §6.
- [32번](../32-impl-trait-argument-return-position-and-2024-capture/) (8)의 RPITIT E0038 은 격자의 **`rpitit` 줄**이다 — 그리고 **`where Self: Sized` 를 붙이면 풀린다**(오른쪽 열 ok). 32번은 그 구제를 던지지 않았다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서·서머리의 **모든 블록** | `capture.sh` — 블록마다 명령을 배너에 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` — **흔들린 칸 0 · 고칠 것 0** |
| 버전 | `r33_versions` — 설치된 `releases.md` | 1 | 1.27.0 · 1.72.0 · 1.78.0 · **1.86.0** |
| ★★ 포인터 크기 | `r33_size` · `r33_unsized` | 2 | 8 / 16 · `size_of_val` 8·16 · **E0277** |
| ★★ vtable | `r33_vt` — `--emit=llvm-ir` · `opt-level=0` | 1 | 칸 다섯 · 드롭 칸 0 / `drop_in_place` · 크기 8 / 32 |
| ★★★ **위반 격자** | `r33_violations` · `r33_grid` · `r33_const_sized` | 3 | E0038 × 4 · **갈린 칸 7 / 9** · `const` 는 **E0658** |
| `where Self: Sized` 호출 | `r33_where_call` | 1 | **번호 없는 에러** |
| 업캐스팅 | `r33_super` | 1 | 통과(1.92) |
| 트레이트 둘 | `r33_two` · `r33_two_help` · `r33_two_blanket` | 3 | **E0225** · `help:` 대로 **E0277** · 담요 구현으로 통과 |
| 수명 | `r33_static` · `r33_static_fix` · `r33_static_order` | 3 | **번호 없는 에러** · 통과 · **E0597** |
| 다운캐스트 | `r33_cast` · `r33_any` | 2 | **E0605** · `Any` 통과 |
| C++ 대비 | `r33_vptr` — g++ · clang++ | 2 | 두 컴파일러 **같은 값** 8 · 16 · 8 |
| **안 던진 것** — 실행 시간 · 1.85 이하의 업캐스팅 · 디버추얼라이제이션 · `as_any` 관용구 | — | 0 | ★ 「안 던졌다」로 표시했다 |

**구현 의존 항목**(버전·환경이 바뀌면 **다시 찍어야 하는** 것).

| 항목 | 왜 |
|---|---|
| ★★ **포인터 16바이트** | ★ Type layout 이 「지금은 두 배, 기대지 마라」 |
| ★★ **vtable 칸 배치와 메서드 순서** | ★ Reference 가 배치를 적지 않는다 — IR 읽기 |
| 연관 상수 `where` 의 **E0658** | ★ 불안정 기능 — 안정되면 격자의 `const` 줄이 바뀔 수 있다 |
| (4)·(6)의 **번호 없는 에러**와 `help:` 문구 | ★ 진단 등록과 제안은 판마다 바뀐다 |

★ **다시 찍는 법** — `capture.sh <새 디렉토리>` 를 그대로 돌리고 `normalize-shaky.py <원본> <새 디렉토리>` 로 견준다.
