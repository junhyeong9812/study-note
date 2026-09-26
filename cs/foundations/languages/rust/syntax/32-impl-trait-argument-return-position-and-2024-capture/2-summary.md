# rust/syntax/32 — `impl Trait` — 인자 위치·반환 위치와 2024의 수명 포착 변화 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Reference — Impl trait type](https://doc.rust-lang.org/reference/types/impl-trait.html) ·
> [Edition Guide — RPIT lifetime capture rules (2024)](https://doc.rust-lang.org/edition-guide/rust-2024/rpit-lifetime-capture.html) ·
> [Reference — dyn compatibility](https://doc.rust-lang.org/reference/items/traits.html#dyn-compatibility) ·
> [std — `type_name_of_val`](https://doc.rust-lang.org/std/any/fn.type_name_of_val.html).
> ★ 위 문서는 **이 머신의 `rust-docs`(1.92.0) 로컬 사본**을 열어 읽었다. 버전은 **그 사본의 `releases.md` 를 블록으로** 실었다((0)).
> **실행 검증** — 이 문서의 모든 출력·에러는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서\
> ★★★ **`rustc --edition 2021 <파일>.rs` 와 `rustc --edition 2024 <파일>.rs` 를 블록마다 배너에 갈라 적어** 돌려 받은 것이다.
> **같은 소스를 두 에디션으로 던진 블록은 한 배너에 묶지 않고 두 블록으로 실었다**(규칙 10).\
> ★★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다. 소스 펜스도 캡처가 찍었다.\
> ★★ **외부 크레이트를 하나도 쓰지 않았다**(네트워크 없음).
> **버전** — 인자·반환 위치 `impl Trait` **1.26.0** · 인자 위치에 터보피시 금지 **1.26.1** · 명시 제네릭 인자와 인자 위치 `impl Trait` 공존 **1.63.0** ·
> 트레이트 안의 반환 위치 `impl Trait`(RPITIT) **1.75.0** · `use<..>` 정밀 포착 **1.82.0** · **2024 에디션 1.85.0**. 전부 아래 (0)의 블록이 근거다.
> ★ **에디션이 넷째 축**이다 — 이 주제의 결론 하나는 **언어 판(에디션)** 에 매여 있다((5)). 나머지는 **에디션과 무관**하다(블록마다 2021 판으로 확인했다).
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
| ★★★ **에디션이 가른다** | **(5)의 네 칸** — 같은 소스가 2021 에서 통과·2024 에서 에러, 또는 그 반대 | ★ **이 주제의 본체**다. **흔들리는 것이 아니라 에디션이 정한다** — 같은 판·같은 에디션이면 고정이다 |
| 안 흔들린다 | `type_name_of_val` 의 **문자열**(`alloc::string::String`·`fn(i32) -> i32`) | ★ **같은 판에서 고정**이지만 std 문서가 **형식은 보장하지 않는다**고 적는다(§구현 세부) |
| 안 흔들린다 | 진단의 `{closure@r32_branch_closure.rs:4:9: 4:17}` 같은 **클로저 이름** | 소스 위치로 이름을 짓는다 — 소스가 같으면 같다 |
| 안 흔들린다 | 에러 번호·제목·`파일:줄:칸`·종료 코드 | 같은 rustc 판에서 고정이다 |

★ 정규화 규칙은 **기본 넷**만 썼고 **하나도 걸리지 않았다**(제출 전 재대조).

## 한눈에 — 쉽게 말하면

**`impl Trait` 는 「이름 대신 자격만 적은 칸」이다. 인자 자리에서는 「무엇이든 이 자격이면 받는다」,
반환 자리에서는 「무엇인지는 비밀이고 이 자격만 보장한다」.
2024 에디션은 그 비밀 봉투가 「빌린 것을 품고 있을 수 있다」를 기본값으로 바꿨다.**

| 비유 | 실체 |
|---|---|
| 「**이 자격만 있으면 누구든**」 | **인자 위치 `impl Trait`** — 이름 없는 제네릭 파라미터. **터보피시로 못 찍는다**((1)) |
| 「**내용은 비밀인 봉투 — 겉에 적힌 기능만 쓸 수 있다**」 | ★★ **반환 위치 `impl Trait`** — 구체 타입을 **감춘다.** `.len()` 을 못 부른다((2)) |
| 「**봉투를 넘어 새는 것**」 | ★★ **자동 트레이트**(`Send`·`Sync`)는 **새어 나온다** — 그리고 **에러 문구가 속을 말해 버린다**((3)) |
| 「**봉투 하나에는 물건 하나**」 | **분기마다 다른 타입이면 E0308** — 단, **아무것도 안 잡은 클로저는 함수 포인터 하나로 모인다**((4)) |
| 「**봉투가 빌려 온 물건을 품고 있을지도 모른다는 딱지**」 | ★★★ **수명 포착** — 2021 은 **적힌 수명만**, 2024 는 **시야 안의 수명 전부**를 품는다고 본다((5)) |
| 「**딱지를 직접 적기**」 | ★★ **`use<..>`** — 에디션에 안 매이게 포착 목록을 적는다. **타입 파라미터는 못 뺀다**((7)) |
| 「**트레이트 약속서에 봉투를 적기**」 | **RPITIT** — 트레이트 메서드가 `impl Trait` 를 돌려준다. 대신 **`dyn` 이 안 된다**((8)) |

- ★★★ **판정은 한 줄이다 — 「2024 에서 반환 `impl Trait` 는 인자로 받은 참조를 빌리고 있다고 가정된다. 아니면 `use<>` 로 적어라.」**
  그래서 **같은 소스가 두 방향으로 갈린다** — 빌린 것을 **정말 돌려주는** 함수는 2021 에서 막히고 2024 에서 풀리며(E0700 → 통과),
  **안 빌리는** 함수를 호출한 쪽은 2021 에서 되고 2024 에서 막힌다(통과 → E0502)((5)).
- ★★ **반환 `impl Trait` 가 감추는 것은 「타입 검사기에 대한 이름」뿐이다** — `Send` 여부는 새고, 런타임 타입 이름도 물으면 나온다((3)).

```text
   같은 소스, 두 에디션 — (5)의 네 블록

   ① 빌린 것을 돌려준다                        ② 빌리지 않는 값을 돌려준다
   fn lens<'a>(v: &'a [String])               fn counter(v: &Vec<i32>)
       -> impl Iterator<Item = usize>             -> impl Fn() -> usize
   { v.iter().map(…) }   ← 'a 를 쓴다          { let n = v.len(); move || n }   ← v 를 안 쓴다

   2021: 'a 는 경계에 안 적혀 있다 → 안 품는다    2021: 안 적혀 있다 → 안 품는다
         그런데 숨긴 타입이 'a 를 쓴다                  호출자의 v.push() 가 된다
         → ✘ E0700                                      → ✔ 「3 4」

   2024: 시야 안의 'a 를 품는다                   2024: 익명 수명을 품는다
         → ✔ 「합 5」                                  → c 가 v 를 빌린 것으로 본다
                                                       → ✘ E0502 (호출자 쪽!)

   고치는 법 — 에디션에 안 매이게 (7)
   ① + use<'a>   (2021 에서도 통과)              ② + use<>   (2024 에서도 통과)

   ★ 트레이트 안의 impl Trait (RPITIT) 는 2021 에서도 이미 「전부 품는다」 — (8)
     2024 는 보통 함수를 그쪽 규칙에 맞춘 것이다
```

> **불투명 타입(opaque type)** — 반환 위치 `impl Trait` 가 만드는 타입. 호출자에게는 **적힌 트레이트만** 보이고, 속의 **숨긴 타입(hidden type)** 은 안 보인다.\
> 예: `fn name() -> impl Display` 의 숨긴 타입은 `String` 이지만 호출자는 `.len()` 을 못 부른다.

> **수명 포착(lifetime capture)** — 불투명 타입이 **어떤 제네릭 파라미터(수명 포함)를 쓸 수 있다고 표시하는 것**. 포착한 수명만큼 값이 **빌림을 이어 간다.**\
> 예: 2024 의 `fn counter(v: &Vec<i32>) -> impl Fn() -> usize` 는 `v` 의 수명을 포착한다 — 그래서 반환값이 살아 있는 동안 `v` 를 못 바꾼다.

> **에디션(edition)** — 하위 호환을 깨는 변경을 **크레이트 단위로 골라 켜는** Rust 의 판. 같은 컴파일러가 판마다 다른 규칙으로 컴파일한다.\
> 예: `rustc --edition 2021` 과 `--edition 2024` 는 같은 rustc 1.92.0 이다. 연혁은 [`history/rust/02-에디션.md`](../../../../../../history/rust/02-에디션.md).

## 이 주제가 답하려는 질문

1. **인자 위치 `impl Trait` 는 무엇의 설탕인가** — 그리고 무엇을 못 하나(터보피시)((1)).
2. ★★ **반환 위치 `impl Trait` 는 무엇을 감추고 무엇을 드러내나**((2)·(3)·(4)).
3. ★★★ **2024 에디션은 수명 포착을 어떻게 바꿨나** — 같은 소스로 두 방향의 차이를 보이고, `use<..>` 로 고친다((5)·(6)·(7)·(8)).

★ [**25번 주제**](../25-traits-definition-impl-default-methods-and-associated-types/) (6)이 `impl Trait` 의 **두 자리와 갈래 E0308** 까지 닿았고 「정본은 32번」이라며 넘겼다.
여기는 그 뒤 — **감춤의 경계, 새는 것, 에디션.** [**31번 주제**](../31-generics-trait-bounds-where-and-monomorphization/)의 **단형화**는 인자 위치 `impl Trait` 에 그대로 적용된다(이름 없는 제네릭이므로).
★★ **정본 경계** — **에디션 제도와 연혁**(언제 들어왔나, 2024 에 무엇이 함께 들어왔나)은 [`history/rust/02-에디션.md`](../../../../../../history/rust/02-에디션.md)가 정본이다.
그 편의 「RPIT 수명 캡처 규칙」 절은 **규칙을 한 문단과 예 두 줄**로 적었다 — **여기서는 그것을 다시 쓰지 않고**, 같은 소스를 두 에디션에 던져 **어느 쪽으로 무엇이 깨지나**를 출력으로 보인다.
**에디션 이전 절차 전체**(`cargo fix --edition`)는 목록의 **47번 주제**다.

## 동작 방식

### (0) 이 주제가 쓰는 네 창 — 그리고 버전

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **같은 소스를 `--edition 2021` / `2024` 로 두 번** | 수명 포착 규칙이 **어느 쪽으로 무엇을 깨나**((5)·(8)) | ★ **이 주제의 본체** |
| ★★ **숨긴 타입에 없는 것을 시켜 보기** | 감추는 것 — E0599·E0308((2)·(4)) | 「에러도 출력이다」 |
| ★★ **감춘 뒤에 `Send` 를 요구해 보기** | 새는 것 — 통과하거나, **에러 문구가 숨긴 타입을 말한다**((3)) | ★ 이 주제의 고유 창 |
| ★ **`type_name_of_val` 로 런타임에 묻기** | 숨긴 타입이 **실행 때는 그대로**라는 것((3)·(4)) | ★ 「같은 질문을 다른 창으로」 |

★★ **「같은 질문을 다른 창으로」** — 「숨긴 타입은 무엇인가」를 **타입 검사기**에 물으면 E0599 로 **거절**당한다((2)).
같은 질문을 **런타임**(`type_name_of_val`)에 물으면 **답한다.** 그 창이 못 보는 것 — **보장**이다. std 문서가 **문자열 형식을 보장하지 않는다**고 적는다.
★ **「부적용인 창」** — **실행 비용.** 인자 위치 `impl Trait` 는 **제네릭과 같은 단형화**이고 그 크기는 [**31번 주제**](../31-generics-trait-bounds-where-and-monomorphization/)에서 셌다. 여기서는 다시 세지 않는다.

**버전 — 설치된 `releases.md` 에서 뽑았다.**

```text
===== awk '/^Version 1\./{v=$2} /is now stable allowing you to have abstract types|Prohibit using turbofish for .impl Trait.|explicit generic arguments in the presence|return-position .impl Trait. in traits|use<.lt>. opaque type precise capturing|The 2024 Edition is now stable|precise_capturing_in_traits/{print v " | " $0}' "$(rustc --print sysroot)/share/doc/rust/html/releases.md" =====
1.87.0 | - [Stabilize `feature(precise_capturing_in_traits)` allowing `use<...>` bounds on return position `impl Trait` in `trait`s](https://github.com/rust-lang/rust/pull/138128)
1.85.0 | - [The 2024 Edition is now stable.](https://github.com/rust-lang/rust/pull/133349)
1.82.0 | - [Stabilize `+ use<'lt>` opaque type precise capturing (RFC 3617)](https://github.com/rust-lang/rust/pull/127672)
1.75.0 | - [Stabilize `async fn` and return-position `impl Trait` in traits.](https://github.com/rust-lang/rust/pull/115822/)
1.63.0 | - [Allow explicit generic arguments in the presence of `impl Trait` args.][96868]
1.26.1 | - [Prohibit using turbofish for `impl Trait` in method arguments.][50950]
1.26.0 | - [`impl Trait` is now stable allowing you to have abstract types in returns
(exit 0)
```

- **1.26.0** 에 두 자리가 함께 안정됐고, **바로 다음 판 1.26.1** 에 인자 위치에서 **터보피시를 금지**했다. **1.63.0** 에 「**명시 제네릭 인자와 공존**」이 허용됐다((1)).
- **1.75.0** RPITIT((8)) · **1.82.0** `use<..>`((7)) · **1.85.0** 2024 에디션((5)).

### (1) 인자 위치 `impl Trait` — 이름 없는 제네릭, 터보피시는 이름 있는 것만

**언제 쓰나** — 짧게 쓰고 싶고, **호출자가 타입을 찍을 일이 없을 때.**

```rust
// r32_apit.rs
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
```

```text
===== rustc --edition 2021 r32_apit.rs =====
(exit 0)
===== ./r32_apit =====
<1>
<a>
7 b
(exit 0)
```

- `show(x: impl Display)` 는 **`fn show<T: Display>(x: T)` 와 같은 일**을 한다 — 정수와 문자열이 둘 다 들어갔다.
- ★★ **15행 `pair::<u8>(7, "b")` 가 통과한다** — `impl Display` 가 있어도 **이름 있는 파라미터 `T` 는 찍을 수 있다**(1.63 부터).
  「`impl Trait` 인자가 있으면 터보피시를 못 쓴다」는 **1.26.1 ~ 1.62 의 규칙**이다.

**`impl Trait` 자리를 찍으려 하면.**

```rust
// r32_apit_turbofish.rs
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
```

```text
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

- ★★ **E0107 두 건** — `show` 는 「**takes 0 generic arguments**」, `pair` 는 「**takes 1 generic argument but 2 … were supplied**」.
  두 `note:` 가 같은 이유를 적는다 — 「**`impl Trait` cannot be explicitly specified as a generic argument**」.
  **`impl Trait` 자리는 파라미터 목록에 이름이 없다** — 그래서 **셀 때도 안 센다**(`pair` 는 `T` 하나뿐이다).
- ★ **공개 API 의 판단** — `impl Trait` 인자는 **호출자가 타입을 찍을 길을 닫는다.** 추론이 안 되는 자리(`into()` 를 거친 인자 등)에서 호출자가 막힌다.
  ★★ Reference 가 직접 경고한다 — 「**`<T: Trait>` 와 인자 위치 `impl Trait` 는 정확히 같지 않다. 둘 사이를 바꾸면 제네릭 인자의 개수가 바뀌어 호출자에게 깨지는 변경이 될 수 있다**」.
  E0107 의 「**takes 1 generic argument**」가 그 개수다.
  [**29번 주제**](../29-conversion-traits-from-into-tryfrom-asref-borrow/) (9)의 `impl Into<String>` 도 같은 자리다.

### (2) ★★ 반환 위치 `impl Trait` 가 감추는 것 — 구체 타입의 메서드

**언제 쓰나** — 돌려주는 타입이 **하나**이고 그 이름을 약속하고 싶지 않을 때(이터레이터 체인·클로저).

```rust
// r32_hide.rs
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
```

```text
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

- ★★ **E0599** — `` no method named `len` found for opaque type `impl std::fmt::Display` ``. 숨긴 타입은 `String` 인데
  호출자에게 보이는 것은 **「`Display` 를 구현한 어떤 타입」** 뿐이다. `len` 은 약속에 없다.
- ★ 진단이 **「opaque type」** 이라는 말을 쓴다 — 컴파일러 안에서 이것은 **별도의 타입**이다. `String` 의 별칭이 아니다.
- ★ **이것이 감춤의 값이다** — 함수를 고쳐 `String` 대신 `Box<str>` 을 돌려줘도 **호출자 코드가 안 깨진다**(약속한 것만 썼으므로).

### (3) ★★ 그런데 새어 나오는 것 — 자동 트레이트, 그리고 에러 문구

**언제 쓰나** — 반환 `impl Trait` 를 스레드·`async` 경계로 넘길 때. **시그니처에 안 적은 것이 결과를 가른다.**

```rust
// r32_leak.rs
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
```

```text
===== rustc --edition 2021 r32_leak.rs =====
(exit 0)
===== ./r32_leak =====
Send 통과
alloc::string::String
(exit 0)
```

- ★★ **`need_send(name())` 가 통과했다** — `name` 의 시그니처는 `impl Display` 뿐이고 **`Send` 는 한 글자도 없다.**
  **자동 트레이트(`Send`·`Sync` 등)는 숨긴 타입에서 새어 나온다.** 숨긴 `String` 이 `Send` 이므로 통과했다.
  ★ **근거의 종류를 밝힌다** — 로컬 Reference 의 impl trait 절과 auto traits 절에서 **이 누수를 명시한 문장은 찾지 못했다.** 근거는 **이 판의 실측**(이 블록의 통과와 아래 블록의 E0277)이다.
- ★ **둘째 줄 `alloc::string::String`** — `type_name_of_val` 은 **런타임에** 숨긴 타입 이름을 답한다. 감춤은 **타입 검사기에 대한 것**이다.

**숨긴 타입이 `Send` 가 아니면.**

```rust
// r32_leak_rc.rs
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
```

```text
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

- ★★★ **E0277 — `` `Rc<i32>` cannot be sent between threads safely ``.** 시그니처는 `impl Display` 인데 **에러가 숨긴 타입 `Rc<i32>` 를 이름으로 말한다.**
  `note:` 가 「**required because it appears within the type `impl std::fmt::Display`**」로 **봉투 속을 가리킨다.**
- ★★ **그래서 함수 몸통만 바꿔도 호출자가 깨진다** — `String` 을 `Rc` 로 바꾸는 순간 **시그니처는 그대로인데** 다른 크레이트의 `need_send(shared())` 가 E0277 이 된다.
  **자동 트레이트 누수는 공개 API 의 숨은 계약**이다. 약속하려면 `-> impl Display + Send` 로 **적는다.**

### (4) 분기마다 다른 타입 — E0308, 단 함수 포인터로 모이는 경우

**언제 쓰나** — 조건에 따라 다른 동작을 돌려줄 때. **`impl Trait` 는 타입 하나**다.

```rust
// r32_branch_closure.rs
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
```

```text
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

- ★★ **E0308 — `` `if` and `else` have incompatible types `` · `no two closures, even if identical, have the same type`.**
  두 클로저는 **글자가 비슷해도 타입이 다르다**(진단이 소스 위치로 이름을 붙였다 — `{closure@…:4:9: 4:17}`·`{closure@…:6:9: 6:17}`).
  `help:` 가 **`Box<dyn Fn(i32) -> i32>`** 로 바꾸라고 권한다 — 25번 (6)에서 구조체 두 개로 본 것과 **같은 처방**이다.

**그런데 아무것도 안 잡는 클로저면.**

```rust
// r32_branch_fnptr.rs
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
```

```text
===== rustc --edition 2021 r32_branch_fnptr.rs =====
(exit 0)
===== ./r32_branch_fnptr =====
11 2
fn(i32) -> i32
(exit 0)
```

- ★★★ **통과한다** — 그리고 숨긴 타입이 **`fn(i32) -> i32`**(함수 포인터)다.
  **환경을 안 잡는 클로저는 함수 포인터로 강제될 수 있어서**, `if`/`else` 두 갈래가 **공통 타입 하나**(함수 포인터)로 모였다.
  **「분기마다 다른 클로저면 E0308」은 「환경을 잡는 클로저」에서만 참**이다 — 위 블록이 `move |x| x + k` 로 **`k` 를 잡은** 판이었다.
- ★ 이 차이가 **런타임 비용**으로도 이어질 수 있다(함수 포인터 호출은 간접 호출이다) — **이 문서는 재지 않았다.**

### (5) ★★★ 2024 의 수명 포착 변화 — 같은 소스, 두 에디션, 두 방향

**언제 쓰나** — 2021 크레이트를 2024 로 올릴 때, 그리고 **반환 `impl Trait` 가 참조 인자를 받는 모든 함수**를 쓸 때.

**① 빌린 것을 정말 돌려주는 함수.**

```rust
// r32_capture_a.rs
// 같은 소스, 두 에디션 — ① 빌린 것을 돌려주는 반환 impl Trait
fn lens<'a>(v: &'a [String]) -> impl Iterator<Item = usize> {
    v.iter().map(|s| s.len())
}

fn main() {
    let v = vec![String::from("ab"), String::from("cde")];
    let total: usize = lens(&v).sum();
    println!("합 {}", total);
}
```

```text
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

```text
===== rustc --edition 2024 r32_capture_a.rs =====
(exit 0)
===== ./r32_capture_a =====
합 5
(exit 0)
```

- ★★★ **2021 — E0700 `hidden type … captures lifetime that does not appear in bounds`.**
  숨긴 타입(`Map<Iter<'a, String>, …>`)이 **`'a` 를 쓰는데**, 2021 규칙은 **경계에 글자로 적힌 수명만** 포착한다 — `impl Iterator<Item = usize>` 에는 `'a` 가 없다.
- ★★★ **2024 — 통과, `합 5`.** 2024 규칙은 **시야 안의 수명을 전부** 포착한다(Edition Guide). `'a` 를 포착했으므로 숨긴 타입이 그것을 써도 된다.
- ★ 2021 의 `help:` 가 이미 **`+ use<'a>`** 를 권한다 — 2021 에서도 이렇게 적으면 된다((7)).

**② 빌리지 않는 값을 돌려주는 함수 — 이번에는 호출자 쪽.**

```rust
// r32_capture_b.rs
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
```

```text
===== rustc --edition 2021 r32_capture_b.rs =====
(exit 0)
===== ./r32_capture_b =====
3 4
(exit 0)
```

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

- ★★★ **2021 — 통과, `3 4`.** 반환 클로저는 `v.len()` 을 **복사**해 둘 뿐이라 `v` 를 안 빌린다. 2021 은 **익명 수명(`&Vec<i32>` 의 것)을 포착하지 않으므로**
  호출자가 `c` 를 쥔 채로 `v.push(4)` 를 해도 된다.
- ★★★ **2024 — E0502** `` cannot borrow `v` as mutable because it is also borrowed as immutable ``. **에러가 함수가 아니라 호출자(10행)** 에서 난다.
  2024 는 그 익명 수명을 **포착한다고 가정**하므로, `c` 가 살아 있는 동안(11행에서 쓴다) `v` 가 **빌린 상태**로 남는다.
  ★ `note:` 가 이유를 직접 적는다 — 「**because Rust 2024 has adjusted the `impl Trait` lifetime capture rules**」. `help:` 는 **`+ use<>`**.
- ★★ **두 방향을 한 줄로** — 2024 는 「**품는다**」를 기본값으로 바꿨다. 그래서 **정말 빌린 것을 돌려주는 함수는 풀리고**(①),
  **안 빌리는데 참조를 받는 함수의 호출자는 조여진다**(②). **어느 에디션이 「더 관대하다」가 아니다** — 기본값이 옮겨 갔을 뿐이다.
- ★ **바뀐 것은 수명뿐이다** — 타입 파라미터는 **모든 에디션에서** 전부 포착한다(Edition Guide). 그래서 (7)의 `use<>` 로도 **타입은 못 뺀다.**

### (6) 옮기기 전에 알려 주는 린트 — `impl_trait_overcaptures`

**언제 쓰나** — 2021 크레이트를 올리기 **전에** ②같은 자리를 찾을 때.

```text
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

- ★★ **2021 에서 `-W impl_trait_overcaptures` 를 켜면** ② 의 함수에 **경고**를 단다 — 「**will capture more lifetimes than possibly intended in edition 2024**」.
  **컴파일은 통과한다**(`exit 0`) — 2021 의미는 그대로이고 **2024 에서의 의미를 미리 알려 줄 뿐**이다.
- ★ Edition Guide 에 따르면 이 린트는 `rust-2024-compatibility` 묶음에 들어 있어 **`cargo fix --edition` 이 자동으로 켜고, 대개 `use<..>` 를 자동으로 넣는다.** 그 절차는 목록의 **47번 주제**다(이 문서는 `cargo fix` 를 돌리지 않았다).
- ★ **①의 함수에는 이 경고가 안 붙는다** — 2021 에서 이미 에러이기 때문이다(① 블록).

### (7) ★★ `use<..>` — 포착 목록을 직접 적는다, 에디션에 안 매이게

**언제 쓰나** — 에디션 기본값에 기대지 않고 **포착할 것을 적고 싶을 때.** 2024 로 옮길 때 ②를 고치는 표준 처방이다.

```rust
// r32_use.rs
// use<..> 정밀 포착 — 에디션에 안 매이게 적는다
fn lens<'a>(v: &'a [String]) -> impl Iterator<Item = usize> + use<'a> {
    v.iter().map(|s| s.len())
}

fn counter(v: &Vec<i32>) -> impl Fn() -> usize + use<> {
    let n = v.len();
    move || n
}

fn main() {
    let w = vec![String::from("ab"), String::from("cde")];
    println!("합 {}", lens(&w).sum::<usize>());
    let mut v = vec![1, 2, 3];
    let c = counter(&v);
    v.push(4);
    println!("{} {}", c(), v.len());
}
```

```text
===== rustc --edition 2021 r32_use.rs =====
(exit 0)
===== ./r32_use =====
합 5
3 4
(exit 0)
```

```text
===== rustc --edition 2024 r32_use.rs =====
(exit 0)
===== ./r32_use =====
합 5
3 4
(exit 0)
```

- ★★ **두 에디션 다 통과, 출력도 같다.** `use<'a>` 는 ①을 2021 에서 풀었고, `use<>` 는 ②를 2024 에서 풀었다.
  **`use<..>` 는 에디션 기능이 아니라 1.82 의 일반 문법**이다 — 그래서 한 소스가 **두 에디션에서 같은 뜻**이 된다.
- ★ **`use<>`**(빈 목록) — 「**아무 수명도 포착하지 않는다**」. `use<'a>` — 「`'a` 만」.

**타입 파라미터까지 빼려 하면.**

```rust
// r32_use_type.rs
// use<> 로 타입 파라미터까지 빼려 하면
fn keep<T: Clone>(t: &T) -> impl std::fmt::Debug + use<> {
    let _ = t.clone();
    0u8
}

fn main() {
    println!("{:?}", keep(&1));
}
```

```text
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

- ★★ **에러 — `impl Trait` must mention all type parameters in scope in `use<...>`.** 그리고 `note:` 가 「**currently**」라고 적는다 — 지금 판의 제약이다.
  **`use<..>` 는 수명을 좁히는 도구이지 타입 파라미터를 빼는 도구가 아니다**(이 판).
- ★ 이 에러에는 **`E` 번호가 없다** — `For more information…` 줄도 없다. **번호 없는 에러**도 있다는 것을 적어 둔다(블록이 그대로다).

### (8) 트레이트 안의 `impl Trait` 반환(RPITIT) — 그리고 `dyn`

**언제 쓰나** — 트레이트 메서드가 **구현마다 다른 이터레이터·퓨처**를 돌려줘야 할 때(1.75 부터).

```rust
// r32_rpitit.rs
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
```

```text
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

```text
===== rustc --edition 2024 r32_rpitit.rs =====
(exit 0)
===== ./r32_rpitit =====
[1, 2] [1, 2]
(exit 0)
```

- ★★★ **2021 에서 에러는 하나뿐이다 — 16행 `own`(고유 메서드).** **9행 `items`(트레이트 구현)는 통과했다.**
  **시그니처가 한 글자도 같은데**(`fn …(&self) -> impl Iterator<Item = u32>`) 자리만 다르다.
  Edition Guide 가 적는 대로 **RPITIT 와 `async fn` 은 모든 에디션에서 이미 「시야 안의 수명을 전부」 포착**했고,
  2021 의 좁은 규칙은 **보통 함수와 고유 메서드**에만 있었다. **2024 는 그쪽을 트레이트 쪽에 맞췄다** — 2024 판은 둘 다 통과(`[1, 2] [1, 2]`).

**RPITIT 가 있는 트레이트를 `dyn` 으로.**

```rust
// r32_rpitit_dyn.rs
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
```

```text
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

- ★★ **E0038 — the trait `Source` is not dyn compatible** — 「**method `items` references an `impl Trait` type in its return type**」.
  구현마다 **반환 타입이 다르므로**(숨긴 타입이 구현마다 하나씩) vtable 의 한 칸에 **한 시그니처로 못 담는다.**
  [**25번 주제**](../25-traits-definition-impl-default-methods-and-associated-types/) (5)가 본 dyn 호환 조건에 **이유가 하나 더** 붙은 것이다. 정본은 [목록의 **33번 주제**](../33-dyn-trait-objects-and-object-safety/).
- ★ `help:` 가 두 길을 적는다 — 그 메서드를 **다른 트레이트로 옮기거나**, 구현이 하나뿐이면 **그 타입을 직접 쓰라.**

**`dyn` 이 필요하면 — 반환을 `Box<dyn Iterator>` 로.**

```rust
// r32_rpitit_box.rs
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
```

```text
===== rustc --edition 2024 r32_rpitit_box.rs =====
(exit 0)
===== ./r32_rpitit_box =====
[0, 2, 4]
[7, 8]
(exit 0)
```

- ★ **두 구현을 한 `Vec<Box<dyn Source>>` 에 담아 돌았다.** 반환 타입이 **구현마다 같은 `Box<dyn Iterator<…> + '_>`** 이 되어 vtable 한 칸에 들어간다.
  값은 **힙 할당 하나와 간접 호출**이다(재지 않았다). `+ '_` 는 **`&self` 를 빌린다**는 표시 — 반환 `impl Trait` 의 포착을 **손으로 적은 꼴**이다.

## 문법 — 형태와 규칙

```text
   형태

   fn f(x: impl Display)                     ← 인자 위치 = 이름 없는 제네릭. f::<…> 로 못 찍는다
   fn g<T: Debug>(a: T, b: impl Display)     ← g::<u8>(…) 는 된다(1.63~) — 찍는 것은 T 뿐
   fn h() -> impl Iterator<Item = u32>       ← 반환 위치 = 숨긴 타입 하나
   fn h() -> impl Display + Send             ← 새는 Send 를 약속으로 적기
   fn h<'a>(v: &'a [T]) -> impl Iterator<Item = &'a T> + use<'a, T>   ← 포착 목록(1.82~)
   fn h(v: &Vec<i32>) -> impl Fn() -> usize + use<>                  ← 수명을 하나도 안 품는다
   trait S { fn items(&self) -> impl Iterator<Item = u32>; }          ← RPITIT(1.75~)


   금지 사례 — 던져서 받은 것

   f::<i32>(1)  (f 의 인자가 impl Trait)              ✘ E0107  "impl Trait cannot be explicitly specified"
   impl Display 로 돌려받은 값에 .len()               ✘ E0599  "for opaque type"
   숨긴 타입이 Rc 인데 T: Send 에 넘김                  ✘ E0277  에러가 Rc<i32> 를 이름으로 말한다
   if/else 가 환경을 잡은 클로저 둘                    ✘ E0308  no two closures … have the same type
   2021: 경계에 없는 수명을 숨긴 타입이 씀              ✘ E0700
   2024: 안 빌리는 함수의 반환값을 쥔 채 인자 변경      ✘ E0502  (호출자 쪽)
   use<> 로 타입 파라미터를 뺌                         ✘ (번호 없음) must mention all type parameters
   RPITIT 트레이트를 dyn 으로                         ✘ E0038
```

**규칙 불릿.**

- **인자 위치 `impl Trait` 는 이름 없는 제네릭** — 그 자리는 터보피시로 못 찍고, **이름 있는 파라미터는 찍을 수 있다**(1.63~)((1)).
- ★★ **반환 위치는 타입 하나를 감춘다** — 약속한 트레이트만 보인다(E0599)((2)).
- ★★ **자동 트레이트는 샌다** — 약속하려면 `+ Send` 로 적는다((3)).
- ★ **분기는 공통 타입이 있어야 한다** — 환경을 잡은 클로저 둘은 E0308, 안 잡은 클로저는 함수 포인터로 모인다((4)).
- ★★★ **2021 은 적힌 수명만, 2024 는 시야 안의 수명 전부를 포착한다** — 보통 함수·고유 메서드의 반환 `impl Trait` 에서((5)).
- ★★ **`use<..>` 는 에디션에 안 매이게 포착을 적는다** — 수명만 좁힐 수 있고 타입 파라미터는 못 뺀다(이 판)((7)).
- ★ **RPITIT 는 모든 에디션에서 전부 포착**하고, **`dyn` 호환이 아니다**((8)).

## 어디서 틀리나

### 1. ★★★ 「2024 는 수명 규칙이 더 관대해졌다」

**기본값이 옮겨 갔을 뿐이다**((5)). 빌린 것을 돌려주는 함수는 **풀렸고**(E0700 → 통과), 안 빌리는 함수의 **호출자는 조여졌다**(통과 → E0502).
★ 게다가 조여진 쪽 에러는 **함수가 아니라 호출자에서** 난다 — 라이브러리를 2024 로 올리면 **다른 크레이트의 호출 코드**가 깨질 수 있다.

### 2. ★★ 「반환 `impl Trait` 는 속을 완전히 감춘다」

**자동 트레이트는 새고, 에러 문구는 속을 말한다**((3)). 몸통을 `String` 에서 `Rc` 로 바꾸면 **시그니처가 그대로인데** 호출자가 E0277 이 된다.

### 3. ★★ 「`impl Trait` 인자가 있으면 터보피시를 아예 못 쓴다」

**1.63 이후로는 이름 있는 파라미터는 찍는다**((1)). 못 찍는 것은 **`impl Trait` 자리**뿐이고, 그 자리는 **개수에도 안 든다**(E0107 의 「takes 1」).
★ 이 문장은 [**25번 주제**](../25-traits-definition-impl-default-methods-and-associated-types/) 「어디서 틀리나」 5 의 「`show::<Square>(…)` 로 못 부른다」를 **좁혀 적은 것**이다 — 그 편의 예(`impl Trait` 인자 하나뿐)에서는 여전히 맞다.

### 4. ★★ 「분기마다 다른 클로저면 무조건 E0308」

**환경을 안 잡은 클로저는 함수 포인터로 모여 통과한다**((4)). E0308 은 **잡은 클로저**에서다.

### 5. ★★ 「`use<>` 로 무엇이든 포착에서 뺄 수 있다」

**수명만이다**((7)). 타입 파라미터는 「**must mention all type parameters**」로 막힌다(이 판의 제약 — note 가 「currently」).

### 6. ★ 「트레이트 메서드와 고유 메서드는 `impl Trait` 규칙이 같다」

**2021 에서는 달랐다**((8)). 시그니처가 같아도 **트레이트 쪽(RPITIT)은 전부 포착**, 고유 메서드는 **적힌 것만** — 그래서 한쪽만 E0700.

### 7. ★ 「`impl Trait` 를 돌려주는 트레이트도 `dyn` 으로 쓸 수 있다」

**E0038 이다**((8)). 구현마다 반환 타입이 달라 vtable 한 칸에 못 담는다.

## 구현 세부사항 대 언어 보장

| 항목 | 무엇인가 | 근거 |
|---|---|---|
| 인자 위치 = 익명 제네릭, 그 자리 터보피시 금지 | ★ **언어 보장** — Reference(impl trait) | (1)의 E0107 |
| 이름 있는 파라미터 터보피시 공존 | ★ **언어 보장** — **1.63 부터** | (0)·(1) |
| 반환 위치가 **약속한 트레이트만** 드러내는 것 | ★ **언어 보장** | (2)의 E0599 |
| **자동 트레이트 누수** | ★ **이 판의 관찰** — 로컬 Reference 에서 **명문을 못 찾았다.** 두 실측(통과·E0277)이 근거 | (3) |
| ★★★ **수명 포착 규칙** | ★ **에디션 보장** — 2021 은 적힌 수명, 2024 는 시야 안 전부(보통 함수·고유 메서드). **RPITIT·`async fn` 은 모든 에디션에서 전부** | (5)·(8)의 에디션 쌍 |
| 타입 파라미터는 **언제나** 포착 | ★ **언어 보장**(모든 에디션) | Edition Guide · (7) |
| `use<..>` 가 **타입 파라미터를 못 빼는** 것 | ★ **이 판의 제약** — note 가 「currently」라고 적는다 | (7)의 에러 |
| 환경을 안 잡은 클로저의 **함수 포인터 강제** | ★ **언어 보장** — 클로저 → 함수 포인터 강제 | (4)의 통과 |
| `type_name_of_val` 의 **문자열** | ★ **구현 세부** — std 문서가 형식을 보장하지 않는다 | (3)·(4) |
| 진단의 `help:`(`use<'a>`·`use<>`·`Box<dyn …>`) | ★ **구현 세부** — 진단의 제안 | (4)·(5) |
| `impl_trait_overcaptures` 가 **기본으로 꺼져 있는** 것 | ★ **이 판의 린트 설정** — `-W` 로 켰다 | (6) |
| (7)의 에러에 **번호가 없는** 것 | ★ **구현 세부** — 진단 등록 여부 | (7)의 블록 |

## 언제 쓰고 언제 안 쓰나

- **인자 위치 `impl Trait` 를 쓴다** — 내부 함수, 짧은 콜백 인자. **공개 API 에서 호출자가 타입을 찍을 일이 있으면** 이름 있는 제네릭으로 쓴다.
- **반환 위치 `impl Trait` 를 쓴다** — 이터레이터 체인·클로저처럼 **이름을 적을 수 없거나 적기 싫은** 타입 하나를 돌려줄 때.
- ★★ **자동 트레이트를 약속하고 싶으면 적는다** — `-> impl Iterator<Item = u32> + Send`. 안 적으면 **몸통이 계약**이 된다((3)).
- **갈래가 필요하면 `Box<dyn Trait>`** — 환경을 잡는 클로저·서로 다른 구조체를 돌려줄 때((4)). 안 잡은 클로저 둘이면 **`fn` 포인터**로도 된다.
- ★★ **2024 로 옮길 때** — `-W impl_trait_overcaptures` 로 자리를 찾고(또는 `cargo fix --edition`), **빌리지 않는 반환에는 `use<>`** 를 단다((6)·(7)).
- ★ **라이브러리는 `use<..>` 를 명시해 두는 편이 안전하다** — 에디션 기본값에 기대지 않으므로 **어느 에디션의 호출자에게도 같은 뜻**이 된다((7)).
- **트레이트 메서드가 이터레이터를 돌려줘야 하면 RPITIT** — 단, 그 트레이트를 `dyn` 으로 쓸 계획이면 **`Box<dyn …>` 반환**으로 쓴다((8)).

## 핵심 문장

- ★★★ **2024 는 반환 `impl Trait` 가 시야 안의 수명을 전부 품는다고 본다** — 빌린 것을 돌려주는 함수는 풀리고, 안 빌리는 함수의 호출자는 조여진다((5)).
- ★★ **`use<..>` 는 에디션에 안 매이는 포착 목록이다** — 수명만 좁힌다((7)).
- ★★ **반환 `impl Trait` 는 이름을 감추지만 `Send` 는 새고 에러는 속을 말한다**((3)).
- ★ **인자 위치의 `impl Trait` 자리는 이름이 없어 찍을 수 없다** — 이름 있는 파라미터는 찍는다(1.63~)((1)).
- ★ **트레이트 안의 `impl Trait` 는 처음부터 전부 품었고, `dyn` 이 안 된다**((8)).

## 관련 자료

- ★★ [`history/rust/02-에디션.md`](../../../../../../history/rust/02-에디션.md) —
  **경계**: **에디션 제도·연혁**과 「RPIT 수명 캡처 규칙 — `use<..>` 바운드」 절의 **규칙 요약**은 **거기**다.
  여기는 그 규칙을 **다시 쓰지 않고**, **같은 소스를 두 에디션에 던져 어느 방향으로 무엇이 깨지나**를 출력으로 보였다((5)·(8)).
- [**25번 주제** — 트레이트·`impl Trait`](../25-traits-definition-impl-default-methods-and-associated-types/) (6) — 두 자리와 구조체 갈래의 E0308. 여기 (4)는 **클로저 판과 함수 포인터 예외**를 더했다.
- [**31번 주제** — 제네릭·단형화](../31-generics-trait-bounds-where-and-monomorphization/) — 인자 위치 `impl Trait` 의 **벌 수**는 거기서 센 제네릭과 같다.
- [**29번 주제** — 변환 트레이트](../29-conversion-traits-from-into-tryfrom-asref-borrow/) (9) — `impl Into<String>` 인자는 인자 위치 `impl Trait` 의 대표 사례다.
- [**12번 주제** — 수명 표기와 생략](../12-lifetime-annotations-and-elision/) — `&Vec<i32>` 의 **익명 수명**이 무엇인지. (5)② 가 포착한 것이 그것이다.
- [**20번 주제** — `let` 체인](../20-if-let-while-let-let-else-and-let-chains/) — 같은 갈래에서 **2024 에디션에서만** 되는 또 하나의 문법.
- [목록의 **33번 주제**](../33-dyn-trait-objects-and-object-safety/) — `dyn Trait` 와 dyn 호환. (8)의 E0038 이 거기서 깊어진다.
- [목록의 **34번**](../34-closures-fn-fnmut-fnonce-and-move/)·[**35번 주제**](../35-function-pointers-and-returning-closures/) — 클로저 세 종류와 **클로저를 돌려주기**(`impl Fn` 대 `Box<dyn Fn>`). (4)의 정본이다.
- 목록의 **47번 주제** — 에디션 2021 대 2024, `cargo fix --edition`. (6)의 린트가 거기서 절차로 쓰인다.
- 목록의 **50번 주제** — `Send`/`Sync`. (3)의 누수가 **스레드 경계**에서 나타나는 자리.

## 용어 풀이

- **`impl Trait`** — 타입 자리에 「이 트레이트를 구현한 어떤 타입」을 적는 문법.
- **APIT / RPIT** — Argument-Position / Return-Position `impl Trait`. 인자 자리 / 반환 자리.
- **RPITIT** — Return-Position `impl Trait` In Trait. 트레이트 메서드의 반환 자리(1.75~).
- **불투명 타입(opaque type)** — RPIT 가 만드는 타입. 약속한 트레이트만 드러낸다.
- **숨긴 타입(hidden type)** — 불투명 타입의 속에 있는 구체 타입.
- **자동 트레이트(auto trait)** — `Send`·`Sync` 처럼 **구성 요소를 보고 컴파일러가 자동으로 구현하는** 트레이트. 불투명 타입을 넘어 샌다.
- **수명 포착(lifetime capture)** — 불투명 타입이 쓸 수 있는 수명을 표시하는 것. 포착한 만큼 빌림이 이어진다.
- **정밀 포착(precise capturing) `use<..>`** — 포착 목록을 직접 적는 문법(1.82~).
- **에디션(edition)** — 크레이트마다 골라 켜는 언어 판. 2015·2018·2021·2024.
- **`impl_trait_overcaptures`** — 2024 에서 더 많이 포착될 자리를 알려 주는 이전용 린트.
- **dyn 호환(dyn compatible)** — `dyn Trait` 가 될 수 있는 성질. 옛 이름 「객체 안전」.
- **함수 포인터 강제** — 환경을 안 잡은 클로저를 `fn(…) -> …` 타입으로 바꾸는 것.

## 더 들어가면

- **`impl Trait` in `let`·타입 별칭** — `let x: impl Display = …` 는 **안정 판에서 안 된다**(타입 별칭 판 TAIT 는 불안정):

```text
===== 소스: r32_let.rs =====
// impl Trait 를 let 의 타입으로 쓰면
use std::fmt::Display;

fn main() {
    let x: impl Display = 3;
    println!("{}", x);
}
===== rustc --edition 2024 r32_let.rs =====
error[E0562]: `impl Trait` is not allowed in the type of variable bindings
 --> r32_let.rs:5:12
  |
5 |     let x: impl Display = 3;
  |            ^^^^^^^^^^^^
  |
  = note: `impl Trait` is only allowed in arguments and return types of functions and methods
  = note: see issue #63065 <https://github.com/rust-lang/rust/issues/63065> for more information

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0562`.
(exit 1)
```

  **E0562** — 「**only allowed in arguments and return types of functions and methods**」. Reference 의 Limitations 절과 같은 말이다.
- **`async fn` 의 반환** — `async fn` 은 **`impl Future` 를 돌려주는 설탕**이고, Edition Guide 가 적는 대로 **모든 에디션에서 전부 포착**한다(목록의 **54번 주제**).
- **`Captures` 트릭** — 2021 에서 `use<..>` 없이 수명을 포착시키려고 쓰던 빈 트레이트 기법. Edition Guide 가 「`use<..>` 로 바꾸거나 2024 에서는 지우라」고 적는다.
- **트레이트 안의 `use<..>`** — RPITIT 에 `use<..>` 를 쓰는 것은 **1.87** 에 안정됐다((0)의 버전 블록 첫 줄). 이 판(1.92)에 들어 있지만 **이 문서는 그 문법을 던지지 않았다.**
