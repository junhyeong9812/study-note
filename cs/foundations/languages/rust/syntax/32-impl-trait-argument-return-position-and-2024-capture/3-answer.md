# rust/syntax/32 — `impl Trait` — 인자 위치·반환 위치와 2024의 수명 포착 변화 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서\
> **`rustc --edition 2021` 과 `rustc --edition 2024`** 로 실제로 돌려 받은 것이다 — **에디션은 블록마다 배너에 적었다.**\
> ★★ **같은 소스의 두 에디션 판은 두 블록으로 갈라 실었다**(한 배너에 묶지 않았다).\
> ★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
> ★★ 블록 첫 줄 `===== 소스: <파일>.rs =====` 아래가 **컴파일한 소스 전문**이고, **진단의 줄 번호는 그 파일 기준**이다.\
> ★★ **외부 크레이트를 하나도 쓰지 않았다**(네트워크 없음).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ 이름 있는 `T` 는 찍고, `impl Trait` 자리는 못 찍는다

**출력 — 이름 있는 파라미터만 찍으면.**

```text
===== 소스: r32_apit.rs =====
// 인자 위치 impl Trait — 이름 없는 제네릭 파라미터
use std::fmt::Display;

fn show(x: impl Display) -> String {
    format!("<{}>", x)
}

fn pair<T: Display>(a: T, b: impl Display) -> String {
    format!("{} {}", a, b)
}

fn main() {
    println!("{}", show(1));
    println!("{}", show("a"));
    println!("{}", pair::<u8>(7, "b")); // ★ 이름 있는 T 만 찍는다
}
===== rustc --edition 2021 r32_apit.rs =====
(exit 0)
===== ./r32_apit =====
<1>
<a>
7 b
(exit 0)
```

**출력 — `impl Trait` 자리까지 찍으면.**

```text
===== 소스: r32_apit_turbofish.rs =====
// impl Trait 자리를 터보피시로 찍으려 하면
use std::fmt::Display;

fn show(x: impl Display) -> String {
    format!("<{}>", x)
}

fn pair<T: Display>(a: T, b: impl Display) -> String {
    format!("{} {}", a, b)
}

fn main() {
    println!("{}", show::<i32>(1));
    println!("{}", pair::<u8, &str>(7, "b"));
}
===== rustc --edition 2021 r32_apit_turbofish.rs =====
error[E0107]: function takes 0 generic arguments but 1 generic argument was supplied
  --> r32_apit_turbofish.rs:13:20
   |
13 |     println!("{}", show::<i32>(1));
   |                    ^^^^------- help: remove the unnecessary generics
   |                    |
   |                    expected 0 generic arguments
   |
note: function defined here, with 0 generic parameters
  --> r32_apit_turbofish.rs:4:4
   |
 4 | fn show(x: impl Display) -> String {
   |    ^^^^
   = note: `impl Trait` cannot be explicitly specified as a generic argument

error[E0107]: function takes 1 generic argument but 2 generic arguments were supplied
  --> r32_apit_turbofish.rs:14:20
   |
14 |     println!("{}", pair::<u8, &str>(7, "b"));
   |                    ^^^^     ------ help: remove the unnecessary generic argument
   |                    |
   |                    expected 1 generic argument
   |
note: function defined here, with 1 generic parameter: `T`
  --> r32_apit_turbofish.rs:8:4
   |
 8 | fn pair<T: Display>(a: T, b: impl Display) -> String {
   |    ^^^^ -
   = note: `impl Trait` cannot be explicitly specified as a generic argument

error: aborting due to 2 previous errors

For more information about this error, try `rustc --explain E0107`.
(exit 1)
```

**왜 그런가.**

- ★★ **앞 소스는 통과** — 15행 `pair::<u8>` 은 **이름 있는 `T`** 만 찍었다. 1.63 부터 `impl Trait` 인자와 명시 제네릭 인자가 **공존**한다.
- ★★ **뒤 소스는 E0107 두 건.** `show` 는 「**takes 0 generic arguments**」, `pair` 는 「**takes 1 generic argument but 2 … were supplied**」 —
  **`impl Trait` 자리는 파라미터 목록에 이름이 없어 개수에도 안 든다.** 두 `note:` 가 같은 이유를 적는다(「**`impl Trait` cannot be explicitly specified as a generic argument**」).
- ★ **호출자를 깨는 이유** — `<T: Trait>` 를 `impl Trait` 로 바꾸면 **제네릭 인자 개수가 줄어** `f::<X>(…)` 로 부르던 호출자가 E0107 이 된다(반대도 같다).
  Reference 가 이 점을 **직접 경고**한다(서머리 (1)).

### 2. ★★ E0599 — 「opaque type」에는 `len` 이 없다

**출력.**

```text
===== 소스: r32_hide.rs =====
// 반환 위치 impl Trait 가 감추는 것
use std::fmt::Display;

fn name() -> impl Display {
    String::from("kim")
}

fn main() {
    let n = name();
    println!("{}", n); // Display 는 약속했다
    println!("{}", n.len()); // String 의 메서드는 약속 안 했다
}
===== rustc --edition 2021 r32_hide.rs =====
error[E0599]: no method named `len` found for opaque type `impl std::fmt::Display` in the current scope
  --> r32_hide.rs:11:22
   |
11 |     println!("{}", n.len()); // String 의 메서드는 약속 안 했다
   |                      ^^^ method not found in `impl std::fmt::Display`

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0599`.
(exit 1)
```

**왜 그런가.**

- ★★ **E0599** — 진단이 `n` 의 타입을 `` opaque type `impl std::fmt::Display` `` 라 부른다. 숨긴 타입이 `String` 이어도 호출자에게 보이는 것은 **`Display` 약속뿐**이다.
- **값** — 몸통의 타입을 바꿔도(`String` → `Box<str>`) **약속한 것만 쓴 호출자는 안 깨진다.** 이름을 공개 API 에서 뺄 수 있다.

### 3. ★★★ 통과하고, 에러는 숨긴 타입을 이름으로 말한다

**출력 — 숨긴 타입이 `String`.**

```text
===== 소스: r32_leak.rs =====
// 그런데 새어 나오는 것 — 자동 트레이트와 런타임 타입 이름
use std::fmt::Display;

fn name() -> impl Display {
    String::from("kim")
}

fn need_send<T: Send>(_: T) -> &'static str {
    "Send 통과"
}

fn main() {
    println!("{}", need_send(name())); // ★ 시그니처에는 Send 가 없다
    println!("{}", std::any::type_name_of_val(&name()));
}
===== rustc --edition 2021 r32_leak.rs =====
(exit 0)
===== ./r32_leak =====
Send 통과
alloc::string::String
(exit 0)
```

**출력 — 숨긴 타입이 `Rc<i32>`.**

```text
===== 소스: r32_leak_rc.rs =====
// 숨긴 타입이 Send 가 아니면 — 에러가 무엇을 말하나
use std::fmt::Display;
use std::rc::Rc;

fn shared() -> impl Display {
    Rc::new(5)
}

fn need_send<T: Send>(_: T) -> &'static str {
    "Send 통과"
}

fn main() {
    println!("{}", need_send(shared()));
}
===== rustc --edition 2021 r32_leak_rc.rs =====
error[E0277]: `Rc<i32>` cannot be sent between threads safely
  --> r32_leak_rc.rs:14:30
   |
 5 | fn shared() -> impl Display {
   |                ------------ within this `impl std::fmt::Display`
...
14 |     println!("{}", need_send(shared()));
   |                    --------- ^^^^^^^^ `Rc<i32>` cannot be sent between threads safely
   |                    |
   |                    required by a bound introduced by this call
   |
   = help: within `impl std::fmt::Display`, the trait `Send` is not implemented for `Rc<i32>`
note: required because it appears within the type `impl std::fmt::Display`
  --> r32_leak_rc.rs:5:16
   |
 5 | fn shared() -> impl Display {
   |                ^^^^^^^^^^^^
note: required by a bound in `need_send`
  --> r32_leak_rc.rs:9:17
   |
 9 | fn need_send<T: Send>(_: T) -> &'static str {
   |                 ^^^^ required by this bound in `need_send`

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0277`.
(exit 1)
```

**왜 그런가.**

- **앞 소스는 통과** — `Send 통과` 와 **`alloc::string::String`**(런타임에 물으면 숨긴 타입 이름이 나온다).
- ★★★ **뒤 소스의 E0277 은 `Rc<i32>` 를 이름으로 말한다** — 시그니처에는 `impl Display` 뿐인데. `note:` 가 「**appears within the type `impl std::fmt::Display`**」로 봉투 속을 가리킨다.
- ★★ **깨지는 경로** — 라이브러리가 몸통을 `String` → `Rc` 로 바꾸면 **시그니처는 그대로인데** 그것을 스레드로 넘기던 **다른 크레이트**가 E0277 이 된다.
  **막는 법** — 약속을 **적는다**: `-> impl Display + Send`. 그러면 `Rc` 로 바꾸는 순간 **라이브러리 쪽**에서 에러가 난다.
- ★ 자동 트레이트 누수의 근거는 **이 두 실측**이다 — 로컬 Reference 에서 명문은 찾지 못했다(서머리 §구현 세부).

### 4. ★★ 잡은 클로저 둘은 E0308, 안 잡은 클로저 둘은 함수 포인터로 모인다

**출력 — 환경을 잡는 클로저.**

```text
===== 소스: r32_branch_closure.rs =====
// 두 갈래가 다른 클로저를 돌려주면 — 환경을 잡는 클로저
fn step(k: i32, big: bool) -> impl Fn(i32) -> i32 {
    if big {
        move |x| x + k * 10
    } else {
        move |x| x + k
    }
}

fn main() {
    println!("{}", step(1, true)(1));
}
===== rustc --edition 2021 r32_branch_closure.rs =====
error[E0308]: `if` and `else` have incompatible types
 --> r32_branch_closure.rs:6:9
  |
3 | /     if big {
4 | |         move |x| x + k * 10
  | |         -------------------
  | |         |
  | |         the expected closure
  | |         expected because of this
5 | |     } else {
6 | |         move |x| x + k
  | |         ^^^^^^^^^^^^^^ expected closure, found a different closure
7 | |     }
  | |_____- `if` and `else` have incompatible types
  |
  = note: expected closure `{closure@r32_branch_closure.rs:4:9: 4:17}`
             found closure `{closure@r32_branch_closure.rs:6:9: 6:17}`
  = note: no two closures, even if identical, have the same type
  = help: consider boxing your closure and/or using it as a trait object
help: you could change the return type to be a boxed trait object
  |
2 - fn step(k: i32, big: bool) -> impl Fn(i32) -> i32 {
2 + fn step(k: i32, big: bool) -> Box<dyn Fn(i32) -> i32> {
  |
help: if you change the return type to expect trait objects, box the returned expressions
  |
4 ~         Box::new(move |x| x + k * 10)
5 |     } else {
6 ~         Box::new(move |x| x + k)
  |

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0308`.
(exit 1)
```

**출력 — 환경을 안 잡는 클로저.**

```text
===== 소스: r32_branch_fnptr.rs =====
// 두 갈래가 다른 클로저를 돌려주면 — 아무것도 안 잡는 클로저
fn step(big: bool) -> impl Fn(i32) -> i32 {
    if big {
        |x| x + 10
    } else {
        |x| x + 1
    }
}

fn main() {
    println!("{} {}", step(true)(1), step(false)(1));
    println!("{}", std::any::type_name_of_val(&step(true)));
}
===== rustc --edition 2021 r32_branch_fnptr.rs =====
(exit 0)
===== ./r32_branch_fnptr =====
11 2
fn(i32) -> i32
(exit 0)
```

**왜 그런가.**

- ★★ **앞 소스는 E0308** — 「**no two closures, even if identical, have the same type**」. 반환 `impl Trait` 는 **숨긴 타입 하나**인데 두 갈래가 **다른 클로저 타입**이다.
- ★★★ **뒤 소스는 통과** — `11 2` 와 **`fn(i32) -> i32`**. 가르는 것은 **환경을 잡느냐**다.
  환경을 안 잡은 클로저는 **함수 포인터로 강제**될 수 있어서(Reference 의 강제 목록), `if`/`else` 두 갈래가 **함수 포인터라는 공통 타입**으로 모였다.
  앞 소스는 `move |x| x + k` 로 **`k` 를 잡아서** 그 강제가 안 된다.

### 5. ★★★ 네 칸 — ①은 에러→통과, ②는 통과→에러

**출력 — ① 2021.**

```text
===== 소스: r32_capture_a.rs =====
// 같은 소스, 두 에디션 — ① 빌린 것을 돌려주는 반환 impl Trait
fn lens<'a>(v: &'a [String]) -> impl Iterator<Item = usize> {
    v.iter().map(|s| s.len())
}

fn main() {
    let v = vec![String::from("ab"), String::from("cde")];
    let total: usize = lens(&v).sum();
    println!("합 {}", total);
}
===== rustc --edition 2021 r32_capture_a.rs =====
error[E0700]: hidden type for `impl Iterator<Item = usize>` captures lifetime that does not appear in bounds
 --> r32_capture_a.rs:3:5
  |
2 | fn lens<'a>(v: &'a [String]) -> impl Iterator<Item = usize> {
  |         --                      --------------------------- opaque type defined here
  |         |
  |         hidden type `Map<std::slice::Iter<'a, String>, {closure@r32_capture_a.rs:3:18: 3:21}>` captures the lifetime `'a` as defined here
3 |     v.iter().map(|s| s.len())
  |     ^^^^^^^^^^^^^^^^^^^^^^^^^
  |
help: add a `use<...>` bound to explicitly capture `'a`
  |
2 | fn lens<'a>(v: &'a [String]) -> impl Iterator<Item = usize> + use<'a> {
  |                                                             +++++++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0700`.
(exit 1)
```

**출력 — ① 2024.**

```text
===== rustc --edition 2024 r32_capture_a.rs =====
(exit 0)
===== ./r32_capture_a =====
합 5
(exit 0)
```

**출력 — ② 2021.**

```text
===== 소스: r32_capture_b.rs =====
// 같은 소스, 두 에디션 — ② 빌리지 않는 값을 돌려주는 반환 impl Trait
fn counter(v: &Vec<i32>) -> impl Fn() -> usize {
    let n = v.len(); // 길이만 복사해 둔다 — v 는 안 잡는다
    move || n
}

fn main() {
    let mut v = vec![1, 2, 3];
    let c = counter(&v);
    v.push(4); // ★ c 가 v 를 빌리고 있나?
    println!("{} {}", c(), v.len());
}
===== rustc --edition 2021 r32_capture_b.rs =====
(exit 0)
===== ./r32_capture_b =====
3 4
(exit 0)
```

**출력 — ② 2024.**

```text
===== rustc --edition 2024 r32_capture_b.rs =====
error[E0502]: cannot borrow `v` as mutable because it is also borrowed as immutable
  --> r32_capture_b.rs:10:5
   |
 9 |     let c = counter(&v);
   |                     -- immutable borrow occurs here
10 |     v.push(4); // ★ c 가 v 를 빌리고 있나?
   |     ^^^^^^^^^ mutable borrow occurs here
11 |     println!("{} {}", c(), v.len());
   |                       - immutable borrow later used here
   |
note: this call may capture more lifetimes than intended, because Rust 2024 has adjusted the `impl Trait` lifetime capture rules
  --> r32_capture_b.rs:9:13
   |
 9 |     let c = counter(&v);
   |             ^^^^^^^^^^^
help: use the precise capturing `use<...>` syntax to make the captures explicit
   |
 2 | fn counter(v: &Vec<i32>) -> impl Fn() -> usize + use<> {
   |                                                +++++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0502`.
(exit 1)
```

**왜 그런가.**

| | 2021 | 2024 |
|---|---|---|
| ① `lens` — 빌린 것을 돌려준다 | ✘ **E0700** | ✔ `합 5` |
| ② `counter` — 안 빌리는 값을 돌려준다 | ✔ `3 4` | ✘ **E0502** |

- ★★★ **①** — 숨긴 타입이 `'a` 를 쓰는데 2021 은 **경계에 적힌 수명만** 포착해 E0700. 2024 는 **시야 안의 수명을 전부** 포착해 통과.
- ★★★ **②** — 2021 은 `&Vec<i32>` 의 익명 수명을 **안 품어서** 호출자가 `c` 를 쥔 채 `v.push(4)` 를 해도 된다. 2024 는 그 수명을 **품는다고 보아**
  **10행 `v.push(4)` — 호출자** — 에서 E0502. `note:` 가 「**because Rust 2024 has adjusted the `impl Trait` lifetime capture rules**」라고 적는다.
- ★ **한 단어씩** — ①에는 **`+ use<'a>`**, ②에는 **`+ use<>`**. 두 `help:` 가 각각 그것을 권했고, 서머리 (7)의 `r32_use` 가 **두 에디션에서 같은 출력**(`합 5` · `3 4`)을 냈다.

### 6. ★★ 1건 — 고유 메서드 `own` 만

**출력 — 2021.**

```text
===== 소스: r32_rpitit.rs =====
// 트레이트 안의 impl Trait 반환(RPITIT) — 그리고 같은 모양의 고유 메서드
trait Source {
    fn items(&self) -> impl Iterator<Item = u32>;
}

struct Bag(Vec<u32>);

impl Source for Bag {
    fn items(&self) -> impl Iterator<Item = u32> {
        self.0.iter().copied()
    }
}

impl Bag {
    fn own(&self) -> impl Iterator<Item = u32> {
        self.0.iter().copied()
    }
}

fn main() {
    let b = Bag(vec![1, 2]);
    println!("{:?} {:?}", b.items().collect::<Vec<_>>(), b.own().collect::<Vec<_>>());
}
===== rustc --edition 2021 r32_rpitit.rs =====
error[E0700]: hidden type for `impl Iterator<Item = u32>` captures lifetime that does not appear in bounds
  --> r32_rpitit.rs:16:9
   |
15 |     fn own(&self) -> impl Iterator<Item = u32> {
   |            -----     ------------------------- opaque type defined here
   |            |
   |            hidden type `Copied<std::slice::Iter<'_, u32>>` captures the anonymous lifetime defined here
16 |         self.0.iter().copied()
   |         ^^^^^^^^^^^^^^^^^^^^^^
   |
help: add a `use<...>` bound to explicitly capture `'_`
   |
15 |     fn own(&self) -> impl Iterator<Item = u32> + use<'_> {
   |                                                +++++++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0700`.
(exit 1)
```

**출력 — 2024.**

```text
===== rustc --edition 2024 r32_rpitit.rs =====
(exit 0)
===== ./r32_rpitit =====
[1, 2] [1, 2]
(exit 0)
```

**왜 그런가.**

- ★★ **2021 에서 E0700 한 건 — 15~16행 `own`(고유 메서드).** 9행 `items`(트레이트 구현)는 **에러가 없다.**
- ★★ **트레이트 안의 `impl Trait`(RPITIT)는 모든 에디션에서 시야 안의 수명을 전부 포착**하고, 2021 의 좁은 규칙은 **보통 함수와 고유 메서드**에만 있었다(Edition Guide).
  **자리가 규칙을 갈랐다.** 2024 에서는 **둘 다 통과**(`[1, 2] [1, 2]`) — 보통 함수 쪽이 트레이트 쪽 규칙에 맞춰졌다.

### 7. 좁은 규칙을 없애고 한쪽으로 맞췄다

- **2021 의 조건** — 수명이 **`impl Trait` 의 경계 안에 글자로 적혀 있을 때만** 포착. 이 규칙은 **보통 함수와 고유 메서드**의 반환 `impl Trait` 에만 있었다.
- ★ **RPITIT 와 `async fn` 은 2021 에서도 전부 포착**했다(6번 답 · Edition Guide). 2024 는 **보통 함수를 그쪽에 맞췄다.**
  Edition Guide 는 이 변경으로 **`Captures` 트릭·`'_` 경계 트릭**을 `use<..>` 로 바꾸거나 **2024 에서는 지울 수 있다**고 적는다 — 옛 우회가 필요 없어졌다.
- **「더 관대해졌다」는 틀리다** — 5번 답의 ②처럼 **호출자가 조여지는** 방향도 있다. **기본값이 옮겨 갔다.**

### 8. ★★ 수명만 좁힌다 — 타입은 못 뺀다

**출력 — `use<>` 로 타입 파라미터까지 빼면.**

```text
===== 소스: r32_use_type.rs =====
// use<> 로 타입 파라미터까지 빼려 하면
fn keep<T: Clone>(t: &T) -> impl std::fmt::Debug + use<> {
    let _ = t.clone();
    0u8
}

fn main() {
    println!("{:?}", keep(&1));
}
===== rustc --edition 2024 r32_use_type.rs =====
error: `impl Trait` must mention all type parameters in scope in `use<...>`
 --> r32_use_type.rs:2:29
  |
2 | fn keep<T: Clone>(t: &T) -> impl std::fmt::Debug + use<> {
  |         -                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  |         |
  |         type parameter is implicitly captured by this `impl Trait`
  |
  = note: currently, all type parameters are required to be mentioned in the precise captures list

error: aborting due to 1 previous error

(exit 1)
```

**출력 — 이전용 린트를 2021 에서 켜면.**

```text
===== 소스: r32_capture_b.rs =====
// 같은 소스, 두 에디션 — ② 빌리지 않는 값을 돌려주는 반환 impl Trait
fn counter(v: &Vec<i32>) -> impl Fn() -> usize {
    let n = v.len(); // 길이만 복사해 둔다 — v 는 안 잡는다
    move || n
}

fn main() {
    let mut v = vec![1, 2, 3];
    let c = counter(&v);
    v.push(4); // ★ c 가 v 를 빌리고 있나?
    println!("{} {}", c(), v.len());
}
===== rustc --edition 2021 -W impl_trait_overcaptures r32_capture_b.rs =====
warning: `impl Fn() -> usize` will capture more lifetimes than possibly intended in edition 2024
 --> r32_capture_b.rs:2:29
  |
2 | fn counter(v: &Vec<i32>) -> impl Fn() -> usize {
  |                             ^^^^^^^^^^^^^^^^^^
  |
  = warning: this changes meaning in Rust 2024
  = note: for more information, see <https://doc.rust-lang.org/edition-guide/rust-2024/rpit-lifetime-capture.html>
note: specifically, this lifetime is in scope but not mentioned in the type's bounds
 --> r32_capture_b.rs:2:15
  |
2 | fn counter(v: &Vec<i32>) -> impl Fn() -> usize {
  |               ^
  = note: all lifetimes in scope will be captured by `impl Trait`s in edition 2024
  = note: requested on the command line with `-W impl-trait-overcaptures`
help: use the precise capturing `use<...>` syntax to make the captures explicit
  |
2 | fn counter(v: &Vec<i32>) -> impl Fn() -> usize + use<> {
  |                                                +++++++

warning: 1 warning emitted

(exit 0)
```

- `use<'a>` 는 「**`'a` 만 포착**」, `use<>` 는 「**수명을 하나도 포착하지 않음**」. **1.82 의 일반 문법이라 에디션에 안 매인다**(서머리 (7)의 두 에디션 판이 같았다).
- ★★ **타입 파라미터는 못 뺀다** — 「**must mention all type parameters in scope in `use<...>`**」, `note:` 가 「**currently**」라고 적는다(이 판의 제약).
  ★ 이 에러에는 **`E` 번호도 `For more information…` 줄도 없다.**
- **린트는 `impl_trait_overcaptures`** — `-W` 로 켜면 **경고만** 내고 **`exit 0`** 이다. 2021 의미는 그대로이고 **2024 에서 더 품을 자리**를 알려 준다. `cargo fix --edition` 이 자동으로 켠다(Edition Guide — 이 문서는 `cargo fix` 를 돌리지 않았다).

### 9. ★ E0038 — 구현마다 반환 타입이 달라서

**출력 — RPITIT 트레이트를 `dyn` 으로.**

```text
===== 소스: r32_rpitit_dyn.rs =====
// RPITIT 가 있는 트레이트를 dyn 으로 쓰려 하면
trait Source {
    fn items(&self) -> impl Iterator<Item = u32>;
}

struct Evens(u32);

impl Source for Evens {
    fn items(&self) -> impl Iterator<Item = u32> {
        (0..self.0).map(|x| x * 2)
    }
}

fn main() {
    let e = Evens(3);
    println!("{:?}", e.items().collect::<Vec<_>>());
    let b: Box<dyn Source> = Box::new(Evens(2));
    println!("{}", b.items().count());
}
===== rustc --edition 2024 r32_rpitit_dyn.rs =====
error[E0038]: the trait `Source` is not dyn compatible
  --> r32_rpitit_dyn.rs:17:20
   |
17 |     let b: Box<dyn Source> = Box::new(Evens(2));
   |                    ^^^^^^ `Source` is not dyn compatible
   |
note: for a trait to be dyn compatible it needs to allow building a vtable
      for more information, visit <https://doc.rust-lang.org/reference/items/traits.html#dyn-compatibility>
  --> r32_rpitit_dyn.rs:3:24
   |
 2 | trait Source {
   |       ------ this trait is not dyn compatible...
 3 |     fn items(&self) -> impl Iterator<Item = u32>;
   |                        ^^^^^^^^^^^^^^^^^^^^^^^^^ ...because method `items` references an `impl Trait` type in its return type
   = help: consider moving `items` to another trait
   = help: only type `Evens` implements `Source`; consider using it directly instead.

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0038`.
(exit 1)
```

**출력 — `Box<dyn Iterator>` 판.**

```text
===== 소스: r32_rpitit_box.rs =====
// dyn 이 필요하면 — Box<dyn Iterator> 를 돌려주는 판
trait Source {
    fn items(&self) -> Box<dyn Iterator<Item = u32> + '_>;
}

struct Evens(u32);
struct Bag(Vec<u32>);

impl Source for Evens {
    fn items(&self) -> Box<dyn Iterator<Item = u32> + '_> {
        Box::new((0..self.0).map(|x| x * 2))
    }
}

impl Source for Bag {
    fn items(&self) -> Box<dyn Iterator<Item = u32> + '_> {
        Box::new(self.0.iter().copied())
    }
}

fn main() {
    let all: Vec<Box<dyn Source>> = vec![Box::new(Evens(3)), Box::new(Bag(vec![7, 8]))];
    for s in &all {
        println!("{:?}", s.items().collect::<Vec<_>>());
    }
}
===== rustc --edition 2024 r32_rpitit_box.rs =====
(exit 0)
===== ./r32_rpitit_box =====
[0, 2, 4]
[7, 8]
(exit 0)
```

- ★ **E0038** — 「**method `items` references an `impl Trait` type in its return type**」. 숨긴 타입이 **구현마다 하나씩** 달라 vtable 한 칸에 **한 시그니처로** 못 담는다.
- **`Box<dyn Iterator<Item = u32> + '_>` 로 바꾸면** 구현마다 반환 타입이 **같아져** `Vec<Box<dyn Source>>` 에 두 구현을 담아 돌았다.
  대가는 **힙 할당 하나와 간접 호출**이다(이 문서는 **재지 않았다**).

### 10. ★ 이름 없는 제네릭이라 타입마다 찍힌다

- 인자 위치 `impl Trait` 는 **이름 없는 제네릭 파라미터**라 [31번 주제](../31-generics-trait-bounds-where-and-monomorphization/)의 **단형화가 그대로** 적용된다 —
  `opt-level=0` 이면 **타입마다 한 벌**, 최적화가 켜지면 **인라인·병합으로 줄어든다**(31번의 격자). 이 주제는 **다시 세지 않았다.**
- [29번 주제](../29-conversion-traits-from-into-tryfrom-asref-borrow/) (9)의 `fn new(name: impl Into<String>)` 는 **인자 위치 `impl Trait`** 다 — 1번 답의 「터보피시를 닫는다」도 그대로 적용된다.

### 11. 연혁은 거기, 출력은 여기

- ★★ [`history/rust/02-에디션.md`](../../../../../../history/rust/02-에디션.md) 는 **에디션 제도·연혁**과 RPIT 포착 규칙의 **요약·예 두 줄**을 적었다.
  이 주제는 그것을 다시 쓰지 않고 **같은 소스를 두 에디션에 던져 두 방향의 깨짐**(5번)과 **자리에 따른 차이**(6번)를 **출력으로** 더했다.
- **`let` 체인** — [20번 주제](../20-if-let-while-let-let-else-and-let-chains/)(`if let … && let …` 이 **2024 에서만** 된다).
- ★ **에디션과 무관한 것** — 1번(터보피시)·2번(감춤)·3번(`Send` 누수)·4번(분기)·8번(`use<..>`)·9번(dyn 호환). **에디션이 가르는 것은 수명 포착 하나**다(5번·6번).

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서·서머리의 **모든 블록** | `capture.sh` — 블록마다 `--edition 2021` 또는 `2024` 를 배너에 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` — **흔들린 칸 0 · 고칠 것 0** |
| 버전 | `r32_versions` — 설치된 `releases.md` | 1 | 1.26.0 · 1.26.1 · 1.63.0 · 1.75.0 · 1.82.0 · 1.85.0 · 1.87.0 |
| 인자 위치 | `r32_apit` · `r32_apit_turbofish` | 2 | `pair::<u8>` 통과 · **E0107 ×2** |
| ★★ **감춤·누수** | `r32_hide` · `r32_leak` · `r32_leak_rc` | 3 | **E0599** · `Send` 통과 + `alloc::string::String` · **E0277 이 `Rc<i32>` 를 말한다** |
| ★★ 분기 | `r32_branch_closure` · `r32_branch_fnptr` | 2 | **E0308** · 통과 `fn(i32) -> i32` |
| ★★★ **에디션 쌍 ①** | `r32_capture_a` × 2021 / 2024 | 2 | **E0700** / `합 5` |
| ★★★ **에디션 쌍 ②** | `r32_capture_b` × 2021 / 2024 | 2 | `3 4` / **E0502**(호출자) |
| 이전 린트 | `r32_lint` — 2021 + `-W impl_trait_overcaptures` | 1 | 경고 1 · `exit 0` |
| ★★ `use<..>` | `r32_use` × 2021 / 2024 · `r32_use_type` | 3 | 두 에디션 같은 출력 · 타입 파라미터는 **번호 없는 에러** |
| ★★ **RPITIT 에디션 쌍** | `r32_rpitit` × 2021 / 2024 | 2 | 2021 은 **고유 메서드만 E0700** / 2024 통과 |
| dyn | `r32_rpitit_dyn` · `r32_rpitit_box` | 2 | **E0038** · `Box<dyn Iterator>` 판 통과 |
| `let` 자리 | `r32_let` | 1 | **E0562** |
| **안 던진 것** — `cargo fix --edition` · RPITIT 의 `use<..>`(1.87) · 실행 비용 | Edition Guide·릴리스 노트로만 적었다 | 0 | ★ 「안 던졌다」로 표시했다 |
| 외부 크레이트 | **쓰지 않음** | 0 | std 만 |

**구현 의존 항목**(버전·환경이 바뀌면 **다시 찍어야 하는** 것).

| 항목 | 왜 |
|---|---|
| ★★ **자동 트레이트 누수** | ★ 근거가 **이 판의 실측**이다 — 명문을 못 찾았다 |
| `use<..>` 가 **타입 파라미터를 못 빼는** 것 | ★ note 가 「**currently**」라고 적는다 — 풀릴 수 있다 |
| `type_name_of_val` 의 **문자열** | ★ std 문서가 형식을 보장하지 않는다 |
| (8)의 에러에 **번호가 없는** 것 | ★ 진단 등록 여부는 판마다 바뀐다 |
| `help:` 가 권하는 `use<'a>`·`use<>`·`Box<dyn …>` | ★ 진단의 제안 |
| `impl_trait_overcaptures` 가 **기본 꺼짐**인 것 | ★ 린트 기본값은 판마다 바뀔 수 있다 |

★ **다시 찍는 법** — `capture.sh <새 디렉토리>` 를 그대로 돌리고 `normalize-shaky.py <원본> <새 디렉토리>` 로 견준다.
**이 주제에는 흔들려야 할 칸이 없다** — 에디션이 가르는 칸은 **에디션을 적은 배너가 따로** 있으므로 한 글자도 같아야 한다.
