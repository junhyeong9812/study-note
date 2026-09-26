# rust/syntax/40 — `Box<T>`·재귀 타입·`dyn` 담기 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [std — `std::boxed` 모듈 문서](https://doc.rust-lang.org/std/boxed/index.html)(재귀 구조 · Memory layout · Editions) ·
> [std — `Box`](https://doc.rust-lang.org/std/boxed/struct.Box.html)(`new` · `leak`) ·
> [std — `std::option` 모듈 문서](https://doc.rust-lang.org/std/option/index.html)(Representation — 널 포인터 최적화) ·
> [Reference — Recursive types](https://doc.rust-lang.org/reference/types.html#recursive-types) ·
> [Reference — Moved and copied types](https://doc.rust-lang.org/reference/expressions.html#moved-and-copied-types)(옮겨 꺼낼 수 있는 자리).
> ★ 위 문서는 **이 머신의 `rust-docs`(1.92.0) 로컬 사본**을 열어 읽었다.
> **실행 검증** — 이 문서의 모든 출력·에러는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서
> **`rustc --edition 2021 <파일>.rs`** 로 돌려 받은 것이다(최적화 격자는 `-C opt-level=0\~3`).\
> ★★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다. 소스 펜스도 캡처가 찍었다.\
> ★★ **외부 크레이트를 하나도 쓰지 않았다**(네트워크 없음). **속도는 한 번도 재지 않았다.** 주소도 **싣지 않았다** — 「어느 영역인가」를 참/거짓과 영역 이름으로만 찍었다((3)).
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
===== python3 --version =====
Python 3.12.3
(exit 0)
===== node --version =====
v18.19.1
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| 안 흔들린다 | ★★★ **E0072** 와 `help:` 를 따라간 **사슬의 번호**(E0308 · E0106) | 같은 rustc 판에서 고정이다. **이 주제의 첫째 본체** |
| 안 흔들린다 | ★★ **`size_of` 격자**의 수 | 같은 판·같은 타깃에서 고정. ★ **`Box<T>`(`T: Sized`)가 포인터 하나인 것은 std 보장, `Box<dyn T>` 16 은 아니다**(§구현 세부 — 33번의 Reference 두 쪽) |
| ★★★ **흔들린다 — 그래서 싣지 않았다** | **주소값** | ASLR 로 실행마다 바뀐다. 대신 **`/proc/self/maps` 의 영역 이름**과 **「스택 변수와 같은 영역인가」 참/거짓**을 찍었다((3)) |
| 안 흔들린다 — 단 **환경의 관찰** | 영역 이름 `[stack]`·`[heap]`·`(anonymous)` | ★ Linux · glibc 할당기의 성질이다. **언어 보장이 아니다** — std 는 「힙(Rust 가 쓰도록 설정된 할당기가 정의하는)」까지만 말한다 |
| ★★ **최적화 수준이 가른다** | **큰 배열 `Box::new` 의 종료 코드**(`134` 대 `0`) | ★ 흔들리는 것이 아니라 **`-C opt-level` 이 정한다** — 칸마다 **세 번씩** 돌려 한 글자도 같았다((4)) |
| 흔들린다(정규화) | 스택 오버플로 첫 줄의 **스레드 id** `thread 'main' (NNN)` | 실행마다 바뀐다 — 기본 규칙이 `(<tid>)` 로 바꾼다 |
| 안 흔들린다 | 에러 번호·제목·`파일:줄:칸`·종료 코드 | 같은 rustc 판에서 고정이다 |

★ 정규화 규칙은 **기본 넷**만 썼다(제출 전 재대조 — 「3-answer」의 실행 검증 표). ★ 셸이 시그널 종료에 붙이는 「`Aborted (core dumped)`」 줄은 **프로그램의 출력이 아니어서** 싣지 않았다 — 캡처가 한 낱말짜리 명령을 `exec` 로 돌려 그 줄을 블록 밖으로 뺐다.

## 한눈에 — 쉽게 말하면

**`Box` 는 「창고 보관증」이다. 물건은 창고(힙)에 두고, 손에는 **보관증 한 장**(포인터)만 쥔다.
「안에 자기와 같은 상자를 넣는 상자」는 크기를 못 정한다 — 끝없이 커지니까. 하지만 **「다음 상자의 보관증」을 넣는 상자**는 크기가 정해진다. 보관증은 늘 같은 크기이기 때문이다.**

| 비유 | 실체 |
|---|---|
| 「**자기를 통째로 품는 상자**」 | ★★★ **`enum List { Cons(i32, List), Nil }`** — **E0072** 「recursive type `List` has infinite size」((1)) |
| 「**다음 상자의 보관증을 품는 상자**」 | ★★ **`Cons(i32, Box<List>)`** — 크기 **16** 으로 정해진다((1)·(2)) |
| 「**보관증 한 장**」 | ★★ **`Box<i32>` 8** — `T` 가 `Sized` 면 **포인터 하나**(std 보장)((2)) |
| 「**크기 적힌 보관증**」 | ★ **`Box<[i32]>`·`Box<str>`·`Box<dyn Display>` 16** — 포인터 + 길이/vtable. 33번의 fat pointer 와 같다((2)) |
| 「**빈 보관증 자리를 `None` 으로**」 | ★★ **`Option<Box<i32>>` 8** — 널이 될 수 없으니 널을 `None` 으로 쓴다(std 보장)((2)) |
| 「**물건을 먼저 손에 들고 창고로 간다**」 | ★★ **`Box::new(x)`** — `x` 를 **값으로 받는 함수**다. 16 MiB 배열을 넘기면 `-C opt-level=0` 에서 **스택 오버플로**((4)) |
| 「**보관증으로 물건을 찾아 나오기**」 | ★ **`let s = *b;`** — **`Box` 만** 되는 이동. `Rc` 는 **E0507**((5)) |

- ★★★ **판정은 한 줄이다 — 「재귀 필드는 포인터여야 한다(Reference). `Box` 는 그 포인터 중 소유하는 것이다.」**
  `help:` 는 `Box`·`Rc`·`&` 셋을 권하는데 **셋 다 한 번에 끝나지 않는다**((1)) — 따라가 보면 사슬이 나온다.

```text
   ★ 재귀 enum 의 크기 — (1)·(2)의 블록 그대로

   enum List { Cons(i32, List), Nil }        Cons 안에 List 가 통째로 ─▶ 그 안에 또 ─▶ …   ✘ E0072 (infinite size)

   enum List { Cons(i32, Box<List>), Nil }
      ┌──── List: 16 바이트 (스택) ────┐
      │ i32 (4) │ 정렬 │ Box<List> (8) ──┼──▶ [ List: 16 (힙) ] ──▶ [ List: 16 (힙) ] ──▶ Nil
      └────────────────────────────────┘
      size_of::<(i32, Box<List>)>() = 16 = size_of::<List>()   ← Nil 을 위한 칸이 따로 없다 (Box 는 널이 아니다)
```

> **재귀 타입(recursive type)** — 필드가 (직간접으로) 자기 타입을 가리키는 타입. Reference: 「재귀 타입의 크기는 **유한해야** 한다 — 즉 **재귀 필드는 포인터 타입이어야** 한다」.\
> 예: `enum List { Cons(i32, Box<List>), Nil }`.

> **`Sized`** — 컴파일 시점에 크기가 정해진 타입. `[i32]`·`str`·`dyn Trait` 는 **아니다**(33번의 DST).\
> 예: `Box<i32>` 는 포인터 하나, `Box<[i32]>` 는 포인터 + 길이.

> **틈새(niche) · 널 포인터 최적화** — 값이 절대 안 가지는 비트 패턴(예: 널)을 `enum` 의 다른 변형에 쓰는 것. std 가 `Box<U>`·`&U`·`fn` 등에 대해 **보장한다.**\
> 예: `Option<Box<i32>>` 는 8 — `None` 이 널 자리다.

## 이 주제가 답하려는 질문

1. ★★★ **재귀 열거형은 왜 크기를 못 정하나 — 그리고 `Box` 는 그것을 어떻게 푸나**((1)·(2)).
2. ★★ **`Box` 는 몇 바이트이고, 무엇이 보장인가** — `Box<T>` · `Box<[T]>` · `Box<dyn T>` · `Option<Box<T>>`((2)).
3. ★★ **`Box` 는 정말 힙에 두나 — `Box::new` 는 언제 스택을 거치나**((3)·(4)). 그리고 **`Box` 만 할 수 있는 것**((5)).

★ **선행** — [**33번 주제**](../33-dyn-trait-objects-and-object-safety/)의 **`dyn Trait` 와 fat pointer**(`&dyn` 16 · `&T` 8) — 이 주제는 거기서 갈라진다. `Box<dyn T>` 가 16 인 것과 **그 16 이 보장이 아닌 것**을 거기서 인용한다.
[**35번 주제**](../35-function-pointers-and-returning-closures/)의 **`Option<fn()>` 8**(틈새)과 `Box<dyn Fn>` 16 도 같은 규칙이다. [**08번 주제**](../08-ownership-and-move/)의 **이동**이 (5)의 뿌리다.
★ **정본 경계** — **스택·힙의 일반**(스택 프레임·가상 주소 공간의 세그먼트·힙의 성장)은 [`memory-management/`](../../../../memory-management/README.md)의 「**3. 함수 호출과 스택 프레임**」·「**4. 가상 주소 공간과 4개 세그먼트**」·「**11. 페이지 폴트와 다이나믹 힙**」이 정본이다.
여기는 **`Box` 가 그 위에서 무엇을 보장하고 무엇을 안 하나**만 쓴다.

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ① E0072 사슬과 ② `size_of` 격자다

★★★ **본체 창 — ① 컴파일러에게 「재귀 타입은 크기가 없다」를 말하게 하고 `help:` 사슬을 끝까지 따라가기** 와 **② `size_of` 격자.**

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ① ★★★ **E0072 + `help:` 따라 하기** | 재귀 타입이 **왜** 막히고, 권한 처방 셋(`Box`·`&`·`Rc`)이 **몇 번 만에** 통과하나((1)) | ★ **본체** |
| ② ★★ **`size_of` 격자** | `Box` 의 크기 · 틈새 · 재귀 `List` 의 크기((2)) | ★ **본체** |
| ③ ★ **`/proc/self/maps` 영역 이름** | `Box` 가 가리키는 곳이 **스택과 같은 영역인가**((3)) | 쓴다 — **주소값 대신** |
| ④ ★★ **최적화 격자 `-C opt-level=0\~3` × 종료 코드** | 큰 배열 `Box::new` 가 **스택을 거치나**((4)) | 쓴다 |
| ⑤ **컴파일러 진단 E0507 + `help:`** | `*b` 이동이 **`Box` 만** 되나((5)) | 쓴다 |
| 실행 시간 · 할당 횟수 | 「`Box` 는 느리다」류 | ★ **부적용 — 재지 않는다** |
| 주소값 자체 | — | ★ **부적용** — 흔들린다. ③으로 **질문을 바꿔** 물었다 |

★ **「같은 질문을 다른 창으로」(제5의 상태)** — 「`Box` 는 힙에 두나」를 **주소로** 물으면 답이 판마다 흔들린다. 그래서 질문을 **「그 주소가 어느 매핑에 속하나」** 로 바꿔 **③ `/proc/self/maps`** 에 물었다.
★ ③이 못 보는 것 — **「힙」이라는 이름은 할당기(glibc)의 사정**이다. 1 MiB 할당은 `[heap]` 이 아니라 **이름 없는 매핑**으로 갔다((3)) — 둘 다 「스택이 아니다」는 같다.

### (1) ★★★ 재귀 타입 E0072 — 그리고 `help:` 사슬을 끝까지

**언제 쓰나** — 연결 리스트·트리·식(expression) 트리처럼 **자기 타입을 품는 타입**을 만들 때.

```rust
// r40_rec.rs
enum List {
    Cons(i32, List),
    Nil,
}

fn main() {
    let _l = List::Nil;
}
```

```text
===== rustc --edition 2021 r40_rec.rs =====
error[E0072]: recursive type `List` has infinite size
 --> r40_rec.rs:1:1
  |
1 | enum List {
  | ^^^^^^^^^
2 |     Cons(i32, List),
  |               ---- recursive without indirection
  |
help: insert some indirection (e.g., a `Box`, `Rc`, or `&`) to break the cycle
  |
2 |     Cons(i32, Box<List>),
  |               ++++    +

error[E0391]: cycle detected when computing when `List` needs drop
 --> r40_rec.rs:1:1
  |
1 | enum List {
  | ^^^^^^^^^
  |
  = note: ...which immediately requires computing when `List` needs drop again
  = note: cycle used when computing whether `List` needs drop
  = note: see https://rustc-dev-guide.rust-lang.org/overview.html#queries and https://rustc-dev-guide.rust-lang.org/query.html for more information

error: aborting due to 2 previous errors

Some errors have detailed explanations: E0072, E0391.
For more information about an error, try `rustc --explain E0072`.
(exit 1)
```

- ★★★ **E0072 — recursive type `List` has infinite size** · 표지 「**recursive without indirection**」 · `help:` 「**insert some indirection (e.g., a `Box`, `Rc`, or `&`) to break the cycle**」 + `Box<List>` 제안.
- ★★ **에러가 둘이다 — E0391(cycle detected when computing when `List` needs drop)이 따라 나왔다.** `main` 에서 **값을 만들었기 때문**이다 — 값을 안 만들면:

```rust
// r40_rec_nomain.rs
#[allow(dead_code)]
enum List {
    Cons(i32, List),
    Nil,
}

fn main() {}
```

```text
===== rustc --edition 2021 r40_rec_nomain.rs =====
error[E0072]: recursive type `List` has infinite size
 --> r40_rec_nomain.rs:2:1
  |
2 | enum List {
  | ^^^^^^^^^
3 |     Cons(i32, List),
  |               ---- recursive without indirection
  |
help: insert some indirection (e.g., a `Box`, `Rc`, or `&`) to break the cycle
  |
3 |     Cons(i32, Box<List>),
  |               ++++    +

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0072`.
(exit 1)
```

- ★ **E0072 하나뿐이다.** E0391 은 「이 값을 버릴 때 무엇을 해야 하나」를 계산하다 **같은 무한 재귀**에 걸린 것이다 — **원인은 하나**(E0072)이고 **증상이 하나 더** 보였을 뿐이다. 고치면 둘 다 사라진다.

**`help:` 의 첫 처방 `Box<List>` — 타입만 고치면.**

```rust
// r40_rec_help.rs
enum List {
    Cons(i32, Box<List>),
    Nil,
}

fn sum(l: &List) -> i32 {
    match l {
        List::Cons(x, rest) => x + sum(rest),
        List::Nil => 0,
    }
}

fn main() {
    let l = List::Cons(1, List::Cons(2, List::Nil));
    println!("sum {}  size_of::<List>() = {}", sum(&l), std::mem::size_of::<List>());
}
```

```text
===== rustc --edition 2021 r40_rec_help.rs =====
error[E0308]: mismatched types
  --> r40_rec_help.rs:14:41
   |
14 |     let l = List::Cons(1, List::Cons(2, List::Nil));
   |                           ----------    ^^^^^^^^^ expected `Box<List>`, found `List`
   |                           |
   |                           arguments to this enum variant are incorrect
   |
   = note: expected struct `Box<List>`
                found enum `List`
   = note: for more on the distinction between the stack and the heap, read https://doc.rust-lang.org/book/ch15-01-box.html, https://doc.rust-lang.org/rust-by-example/std/box.html, and https://doc.rust-lang.org/std/boxed/index.html
note: tuple variant defined here
  --> r40_rec_help.rs:2:5
   |
 2 |     Cons(i32, Box<List>),
   |     ^^^^
help: store this in the heap by calling `Box::new`
   |
14 |     let l = List::Cons(1, List::Cons(2, Box::new(List::Nil)));
   |                                         +++++++++         +

error[E0308]: mismatched types
  --> r40_rec_help.rs:14:27
   |
14 |     let l = List::Cons(1, List::Cons(2, List::Nil));
   |             ----------    ^^^^^^^^^^^^^^^^^^^^^^^^ expected `Box<List>`, found `List`
   |             |
   |             arguments to this enum variant are incorrect
   |
   = note: expected struct `Box<List>`
                found enum `List`
   = note: for more on the distinction between the stack and the heap, read https://doc.rust-lang.org/book/ch15-01-box.html, https://doc.rust-lang.org/rust-by-example/std/box.html, and https://doc.rust-lang.org/std/boxed/index.html
note: tuple variant defined here
  --> r40_rec_help.rs:2:5
   |
 2 |     Cons(i32, Box<List>),
   |     ^^^^
help: store this in the heap by calling `Box::new`
   |
14 |     let l = List::Cons(1, Box::new(List::Cons(2, List::Nil)));
   |                           +++++++++                        +

error: aborting due to 2 previous errors

For more information about this error, try `rustc --explain E0308`.
(exit 1)
```

- ★★★ **E0308 두 개** — 「expected `Box<List>`, found `List`」. **타입 정의만 고치면 만드는 자리가 안 맞는다.** 각 에러에 `help:` 「**store this in the heap by calling `Box::new`**」가 붙는다 — **안쪽 하나 · 바깥 하나**. **묶음 전체를 따라야** 한다.

**둘 다 `Box::new` 로 감싸면.**

```rust
// r40_rec_box.rs
enum List {
    Cons(i32, Box<List>),
    Nil,
}

fn sum(l: &List) -> i32 {
    match l {
        List::Cons(x, rest) => x + sum(rest),
        List::Nil => 0,
    }
}

fn main() {
    let l = List::Cons(1, Box::new(List::Cons(2, Box::new(List::Nil))));
    println!("sum {}  size_of::<List>() = {}", sum(&l), std::mem::size_of::<List>());
}
```

```text
===== rustc --edition 2021 r40_rec_box.rs =====
(exit 0)
===== ./r40_rec_box =====
sum 3  size_of::<List>() = 16
(exit 0)
```

- ★★ **통과 — `sum 3 · size_of::<List>() = 16`.** 처방은 **맞았지만 한 번에 끝나지 않았다** — E0072 → E0308 × 2 → 통과, **두 바퀴**다.

**`help:` 의 셋째 후보 `&` — 따라가 보면.**

```rust
// r40_rec_ref.rs
enum List {
    Cons(i32, &List),
    Nil,
}

fn main() {
    let _l = List::Nil;
}
```

```text
===== rustc --edition 2021 r40_rec_ref.rs =====
error[E0106]: missing lifetime specifier
 --> r40_rec_ref.rs:2:15
  |
2 |     Cons(i32, &List),
  |               ^ expected named lifetime parameter
  |
help: consider introducing a named lifetime parameter
  |
1 ~ enum List<'a> {
2 ~     Cons(i32, &'a List),
  |

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0106`.
(exit 1)
```

```rust
// r40_rec_ref_help.rs
enum List<'a> {
    Cons(i32, &'a List),
    Nil,
}

fn main() {
    let _l = List::Nil;
}
```

```text
===== rustc --edition 2021 r40_rec_ref_help.rs =====
error[E0106]: missing lifetime specifier
 --> r40_rec_ref_help.rs:2:19
  |
2 |     Cons(i32, &'a List),
  |                   ^^^^ expected named lifetime parameter
  |
help: consider using the `'a` lifetime
  |
2 |     Cons(i32, &'a List<'a>),
  |                       ++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0106`.
(exit 1)
```

```rust
// r40_rec_ref_help2.rs
enum List<'a> {
    Cons(i32, &'a List<'a>),
    Nil,
}

fn sum(l: &List) -> i32 {
    match l {
        List::Cons(x, rest) => x + sum(rest),
        List::Nil => 0,
    }
}

fn main() {
    let nil = List::Nil;
    let two = List::Cons(2, &nil);
    let one = List::Cons(1, &two);
    println!("sum {}  size_of::<List>() = {}", sum(&one), std::mem::size_of::<List>());
}
```

```text
===== rustc --edition 2021 r40_rec_ref_help2.rs =====
(exit 0)
===== ./r40_rec_ref_help2 =====
sum 3  size_of::<List>() = 16
(exit 0)
```

- ★★★ **`&List` → E0106**(missing lifetime specifier, `help:` `enum List<'a>` + `&'a List`) → 따르면 **또 E0106**(`help:` `&'a List<'a>`) → 따르면 **통과**(`sum 3 · 16`). **세 바퀴**다.
- ★★ **`&` 판은 힙을 안 쓴다** — 세 노드가 전부 `main` 의 지역 변수(`nil`·`two`·`one`)다. 대신 **리스트가 그 지역 변수들보다 오래 못 산다**(수명 `'a`). **`Box` 는 소유하고, `&` 는 빌린다** — 같은 E0072 의 처방인데 뜻이 다르다.

**`help:` 의 둘째 후보 `Rc` — 꼬리를 나눠 갖기.**

```rust
// r40_rec_rc.rs
use std::rc::Rc;

enum List {
    Cons(i32, Rc<List>),
    Nil,
}

fn sum(l: &List) -> i32 {
    match l {
        List::Cons(x, rest) => x + sum(rest),
        List::Nil => 0,
    }
}

fn main() {
    let tail = Rc::new(List::Cons(2, Rc::new(List::Nil)));
    let a = List::Cons(1, Rc::clone(&tail));
    let b = List::Cons(9, Rc::clone(&tail));
    println!("sum a {} · sum b {} · owners of the shared tail {}", sum(&a), sum(&b), Rc::strong_count(&tail));
}
```

```text
===== rustc --edition 2021 r40_rec_rc.rs =====
(exit 0)
===== ./r40_rec_rc =====
sum a 3 · sum b 11 · owners of the shared tail 3
(exit 0)
```

- ★ **통과**(처음부터 `Rc::new` 로 만드는 자리까지 짰다) — `a`·`b` 가 **같은 꼬리**를 나눠 가져 `owners of the shared tail 3`(`tail` 변수 + `a` + `b`). **`Box` 는 한 주인, `Rc` 는 여러 주인**이다. `Rc` 는 목록의 **41번 주제**가 정본이다.

### (2) ★★ `size_of` 격자 — 보관증의 크기

```rust
// r40_size.rs
use std::fmt::Display;
use std::mem::size_of;

#[allow(dead_code)]
enum List {
    Cons(i32, Box<List>),
    Nil,
}

fn main() {
    println!("{:<28} {}", "i32", size_of::<i32>());
    println!("{:<28} {}", "&i32", size_of::<&i32>());
    println!("{:<28} {}", "Box<i32>", size_of::<Box<i32>>());
    println!("{:<28} {}", "Box<[i32; 100]>", size_of::<Box<[i32; 100]>>());
    println!("{:<28} {}", "Box<[i32]>", size_of::<Box<[i32]>>());
    println!("{:<28} {}", "Box<str>", size_of::<Box<str>>());
    println!("{:<28} {}", "Box<dyn Display>", size_of::<Box<dyn Display>>());
    println!("{:<28} {}", "Option<Box<i32>>", size_of::<Option<Box<i32>>>());
    println!("{:<28} {}", "Option<Box<dyn Display>>", size_of::<Option<Box<dyn Display>>>());
    println!("{:<28} {}", "Option<i32>", size_of::<Option<i32>>());
    println!("{:<28} {}", "(i32, Box<List>)", size_of::<(i32, Box<List>)>());
    println!("{:<28} {}", "List", size_of::<List>());
    println!("{:<28} {}", "Box<List>", size_of::<Box<List>>());
    println!("{:<28} {}", "Option<Box<List>>", size_of::<Option<Box<List>>>());
    println!("{:<28} {}", "Vec<i32>", size_of::<Vec<i32>>());
}
```

```text
===== rustc --edition 2021 r40_size.rs =====
(exit 0)
===== ./r40_size =====
i32                          4
&i32                         8
Box<i32>                     8
Box<[i32; 100]>              8
Box<[i32]>                   16
Box<str>                     16
Box<dyn Display>             16
Option<Box<i32>>             8
Option<Box<dyn Display>>     16
Option<i32>                  8
(i32, Box<List>)             16
List                         16
Box<List>                    8
Option<Box<List>>            8
Vec<i32>                     24
(exit 0)
```

- ★★ **`Box<i32>` 8 · `Box<[i32; 100]>` 8** — 가리키는 것이 **아무리 커도** `Sized` 면 포인터 하나다. std: 「**`T: Sized` 인 한 `Box<T>` 는 포인터 하나로 표현됨이 보장되고 C 포인터와 ABI 호환이다**」.
- ★★ **`Box<[i32]>` · `Box<str>` · `Box<dyn Display>` 16** — 가리키는 것이 **크기 없는 타입**(DST)이면 **포인터 + 길이 / vtable** 두 칸이다. [**33번 주제**](../33-dyn-trait-objects-and-object-safety/)의 `&dyn Shape` 16 과 **같은 fat pointer** 다.
  ★★★ **16 은 보장이 아니다** — 33편이 짚은 대로 **Reference 두 쪽의 말이 어긋난다.** DST 절은 「**두 배 크기**」, Type layout 절은 「**적어도 포인터 크기**이다. 지금은 모든 DST 포인터가 `usize` 두 배이지만 **기대지 마라**」. 뒤쪽이 더 정확하다 — **16 은 이 판의 구현**이다.
- ★★ **`Option<Box<i32>>` 8 · `Option<Box<List>>` 8 · `Option<Box<dyn Display>>` 16** — `Option` 이 **한 바이트도 안 늘었다.** std(Option Representation): 「`Option<T>` 가 `T` 와 **같은 크기·정렬·ABI** 를 갖도록 최적화함을 **보장**한다 — `Box<U>`·`&U`·`&mut U`·`fn`·`NonZero*`·`NonNull<U>`」.
  [**35번 주제**](../35-function-pointers-and-returning-closures/)의 `Option<fn()>` 8 과 **같은 규칙**이다. ★ 대비 — **`Option<i32>` 는 8**(`i32` 4 보다 크다): `i32` 는 **모든 비트 패턴이 유효한 값**이라 빈자리가 없다.
- ★★ **`(i32, Box<List>)` 16 = `List` 16** — `Cons` 의 짐만으로 16 이고, **`Nil` 을 가르는 칸이 따로 없다.** `Box` 가 널일 수 없으니 **널 자리가 곧 `Nil`** 인 셈이다(같은 틈새). ★ 이 해석은 **크기가 같다는 관찰**에서 읽은 것이다 — 배치 자체는 보지 않았다.
- ★ **`Box<List>` 8 · `Vec<i32>` 24** — `Vec` 은 (포인터·용량·길이) 셋([38번 주제](../38-vec-api-capacity-retain-and-drain/) (3)).

### (3) ★ `Box` 는 어디를 가리키나 — 주소 대신 영역 이름으로

**언제 쓰나** — 「`Box` = 힙」을 **눈으로 확인**하고 싶을 때. 주소를 찍으면 흔들리니 **질문을 바꾼다.**

```rust
// r40_where.rs
// Box 가 가리키는 곳과 스택 변수가 「같은 영역」인가 — /proc/self/maps 의 줄 이름으로 판정한다
use std::fs;

fn region(addr: usize) -> String {
    let maps = fs::read_to_string("/proc/self/maps").unwrap();
    for line in maps.lines() {
        let mut parts = line.split_whitespace();
        let range = parts.next().unwrap();
        let (lo, hi) = range.split_once('-').unwrap();
        let lo = usize::from_str_radix(lo, 16).unwrap();
        let hi = usize::from_str_radix(hi, 16).unwrap();
        if lo <= addr && addr < hi {
            let name = parts.nth(4).unwrap_or("");
            return if name.is_empty() { String::from("(anonymous)") } else { name.to_string() };
        }
    }
    String::from("(not mapped)")
}

fn main() {
    let local: i32 = 7;
    let b: Box<i32> = Box::new(7);
    let big: Box<[u8]> = vec![0u8; 1 << 20].into_boxed_slice();
    let a_local = &local as *const i32 as usize;
    let a_box_var = &b as *const Box<i32> as usize;
    let a_box_data = &*b as *const i32 as usize;
    let a_big = big.as_ptr() as usize;
    println!("local i32         : {}", region(a_local));
    println!("the Box variable  : {}", region(a_box_var));
    println!("*b (Box<i32> data): {}", region(a_box_data));
    println!("1 MiB Box<[u8]>   : {}", region(a_big));
    println!("same region as local — box variable {} · box data {} · 1 MiB data {}",
        region(a_box_var) == region(a_local),
        region(a_box_data) == region(a_local),
        region(a_big) == region(a_local));
}
```

```text
===== rustc --edition 2021 r40_where.rs =====
(exit 0)
===== ./r40_where =====
local i32         : [stack]
the Box variable  : [stack]
*b (Box<i32> data): [heap]
1 MiB Box<[u8]>   : (anonymous)
same region as local — box variable true · box data false · 1 MiB data false
(exit 0)
```

- ★★ **`local i32` · `the Box variable` → `[stack]` · `*b` → `[heap]`** — **`Box` 변수(보관증) 자체는 스택에**, **가리키는 값은 힙에** 있다. `same region as local — box variable true · box data false`.
- ★ **`1 MiB Box<[u8]>` → `(anonymous)`** — 큰 할당은 glibc 가 **`[heap]` 이 아닌 따로 된 익명 매핑**으로 준다. 이름은 달라도 **「스택이 아니다」(`false`)** 는 같다.
  ★ **이것은 이 환경(Linux · glibc)의 관찰**이다 — std 는 「(기본 할당기가 정의하는) **힙**」까지만 말하고 매핑 이름은 약속하지 않는다. 영역의 일반론은 [`memory-management/`](../../../../memory-management/README.md) 「4. 가상 주소 공간과 4개 세그먼트」.

### (4) ★★ `Box::new` 는 값을 받는다 — 큰 배열의 판 격자

**언제 쓰나** — **스택에 안 들어가는 큰 값**을 `Box` 에 담으려 할 때.

```rust
// r40_big.rs
// 16 MiB 배열을 Box::new 로
const N: usize = 16 << 20;

fn main() {
    let b: Box<[u8; N]> = Box::new([7u8; N]);
    eprintln!("len {} first {} last {}", b.len(), b[0], b[N - 1]);
}
```

```rust
// r40_big_vec.rs
// 같은 16 MiB 를 vec! 로 만들어 Box<[u8]> 로 바꾼다
const N: usize = 16 << 20;

fn main() {
    let b: Box<[u8]> = vec![7u8; N].into_boxed_slice();
    eprintln!("len {} first {} last {}", b.len(), b[0], b[N - 1]);
}
```

```bash
# r40_big_grid.sh
# 소스 둘 × 최적화 수준 넷 — 실행 종료 코드를 세 번씩
printf '%-12s %-16s | %-7s | %s\n' source opt-level 'cc exit' 'run exit x3'
bad=0; total=0
for s in r40_big r40_big_vec; do
  for o in 0 1 2 3; do
    rustc --edition 2021 -C opt-level=$o -o $s.$o $s.rs 2>/dev/null
    cc=$?
    runs=""
    for i in 1 2 3; do
      { ./$s.$o; } >/dev/null 2>&1
      rc=$?
      runs="$runs $rc"
    done
    total=$((total+1))
    [ "$runs" != " 0 0 0" ] && bad=$((bad+1))
    printf '%-12s %-16s | %-7s |%s\n' "$s" "-C opt-level=$o" "$cc" "$runs"
  done
done
echo "ulimit -s = $(ulimit -s)"
echo "cells whose run exit is not 0 0 0: $bad / $total"
```

```text
===== bash r40_big_grid.sh =====
source       opt-level        | cc exit | run exit x3
r40_big      -C opt-level=0   | 0       | 134 134 134
r40_big      -C opt-level=1   | 0       | 0 0 0
r40_big      -C opt-level=2   | 0       | 0 0 0
r40_big      -C opt-level=3   | 0       | 0 0 0
r40_big_vec  -C opt-level=0   | 0       | 0 0 0
r40_big_vec  -C opt-level=1   | 0       | 0 0 0
r40_big_vec  -C opt-level=2   | 0       | 0 0 0
r40_big_vec  -C opt-level=3   | 0       | 0 0 0
ulimit -s = 8192
cells whose run exit is not 0 0 0: 1 / 8
(exit 0)
```

- ★★★ **`Box::new([7u8; N])` 는 `-C opt-level=0` 에서만 `134 134 134`**(SIGABRT) — `opt-level=1·2·3` 은 `0 0 0`. **`vec![7u8; N].into_boxed_slice()` 는 네 판 전부 `0`.** 마지막 줄 **`1 / 8`**.
- ★★ **세 번씩 돌려 칸마다 한 글자도 같았다** — **흔들리는 칸이 아니라 최적화 수준이 정하는 칸**이다. `ulimit -s = 8192`(KiB — 주 스레드 스택 8 MiB) 에 16 MiB 배열이다.

**`opt-level=0` 의 한 판 — 표준 오류.**

```text
===== rustc --edition 2021 -C opt-level=0 -o r40_big_o0 r40_big.rs =====
(exit 0)
===== ./r40_big_o0 =====

thread 'main' (501099) has overflowed its stack
fatal runtime error: stack overflow, aborting
(exit 134)
```

- ★★ **「thread 'main' (…) has overflowed its stack」 · 「fatal runtime error: stack overflow, aborting」 · exit 134.** 패닉이 아니라 **런타임이 프로세스를 멈춘다**(`Result` 로 못 받는다).
- ★★★ **왜 스택인가** — `Box::new` 는 **`pub fn new(x: T) -> Box<T>`** 다. 인자 `x` 는 **호출 전에 만들어져 값으로 넘어간다** — 최적화 없는 판에서는 그 16 MiB 가 **먼저 스택 위에 만들어진다.** std 의 말도 「힙에 메모리를 잡고 **그 다음** `x` 를 그 안에 둔다」다.
  최적화 판에서 안 터진 것은 **컴파일러가 복사를 없앤 결과**다 — ★ **보장이 아니다.** `vec!` 판은 **처음부터 힙에** 채우므로 판을 안 탄다.

### (5) ★ `*b` 로 옮겨 꺼내기 — `Box` 만의 특권

```rust
// r40_move_out.rs
fn main() {
    let b: Box<String> = Box::new(String::from("boxed"));
    let s: String = *b;
    println!("s = {s}");
}
```

```text
===== rustc --edition 2021 r40_move_out.rs =====
(exit 0)
===== ./r40_move_out =====
s = boxed
(exit 0)
```

- ★★ **`let s: String = *b;` 가 통과**(`s = boxed`). **역참조로 값을 옮겨 꺼냈다.** Reference: 옮겨 꺼낼 수 있는 자리 네 가지 중 하나가 「**`Box<T>` 타입 식을 역참조한 결과(그 식도 옮겨 꺼낼 수 있을 때)**」다. **다른 스마트 포인터는 이 목록에 없다.**

**같은 것을 `Rc` 로.**

```rust
// r40_move_out_rc.rs
use std::rc::Rc;

fn main() {
    let r: Rc<String> = Rc::new(String::from("shared"));
    let s: String = *r;
    println!("{s}");
}
```

```text
===== rustc --edition 2021 r40_move_out_rc.rs =====
error[E0507]: cannot move out of an `Rc`
 --> r40_move_out_rc.rs:5:21
  |
5 |     let s: String = *r;
  |                     ^^ move occurs because value has type `String`, which does not implement the `Copy` trait
  |
help: consider removing the dereference here
  |
5 -     let s: String = *r;
5 +     let s: String = r;
  |
help: consider cloning the value if the performance cost is acceptable
  |
5 -     let s: String = *r;
5 +     let s: String = r.clone();
  |

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0507`.
(exit 1)
```

- ★★ **E0507 — cannot move out of an `Rc`.** `help:` 가 **둘**이다 — ① 「consider removing the dereference」(`r`) ② 「consider cloning the value」(`r.clone()`).

**두 처방을 각각 따르면.**

```rust
// r40_rc_help1.rs
use std::rc::Rc;

fn main() {
    let r: Rc<String> = Rc::new(String::from("shared"));
    let s: String = r;
    println!("{s}");
}
```

```text
===== rustc --edition 2021 r40_rc_help1.rs =====
error[E0308]: mismatched types
 --> r40_rc_help1.rs:5:21
  |
5 |     let s: String = r;
  |            ------   ^ expected `String`, found `Rc<String>`
  |            |
  |            expected due to this
  |
  = note: expected struct `String`
             found struct `Rc<String>`
help: try using a conversion method
  |
5 |     let s: String = r.to_string();
  |                      ++++++++++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0308`.
(exit 1)
```

```rust
// r40_rc_help2.rs
use std::rc::Rc;

fn main() {
    let r: Rc<String> = Rc::new(String::from("shared"));
    let s: String = r.clone();
    println!("{s}");
}
```

```text
===== rustc --edition 2021 r40_rc_help2.rs =====
error[E0308]: mismatched types
 --> r40_rc_help2.rs:5:21
  |
5 |     let s: String = r.clone();
  |            ------   ^^^^^^^^^ expected `String`, found `Rc<String>`
  |            |
  |            expected due to this
  |
  = note: expected struct `String`
             found struct `Rc<String>`
help: try using a conversion method
  |
5 -     let s: String = r.clone();
5 +     let s: String = r.to_string();
  |

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0308`.
(exit 1)
```

- ★★★ **둘 다 E0308 — expected `String`, found `Rc<String>`.** ① `*` 를 빼면 `Rc<String>` 을 `String` 자리에 넣는 것이고, ② `r.clone()` 은 **`String` 이 아니라 `Rc` 를 복제**한다(`Rc` 가 `Clone` 이라 메서드 해석이 `Rc::clone` 을 고른다). **E0507 의 `help:` 둘이 다 틀렸다.**
- ★ 둘 다 새 `help:` 「try using a conversion method」(`r.to_string()`)를 준다 — 따르면:

```rust
// r40_rc_help3.rs
use std::rc::Rc;

fn main() {
    let r: Rc<String> = Rc::new(String::from("shared"));
    let s: String = r.to_string();
    println!("{s}");
}
```

```text
===== rustc --edition 2021 r40_rc_help3.rs =====
(exit 0)
===== ./r40_rc_help3 =====
shared
(exit 0)
```

- ★ **통과**(`shared`) — 그런데 이것은 **`String` 이 `Display` 라서 되는 복사**다(`to_string`). 옮긴 것이 아니다. **세 바퀴 만의 통과이고, 원소 타입이 `Display` 가 아니면 이 길도 없다.**

**뜻에 맞는 길 — 복제하거나, 주인이 하나일 때만 꺼내거나.**

```rust
// r40_rc_ways.rs
use std::rc::Rc;

fn main() {
    let r: Rc<String> = Rc::new(String::from("shared"));
    let copy: String = (*r).clone();
    println!("[1] (*r).clone()          {copy}   strong_count {}", Rc::strong_count(&r));
    let r2 = Rc::clone(&r);
    let back = Rc::try_unwrap(r);
    println!("[2] try_unwrap with 2 owners -> is_err {}", back.is_err());
    drop(back);
    let only: String = Rc::try_unwrap(r2).unwrap();
    println!("[3] try_unwrap with 1 owner  -> {only}");
}
```

```text
===== rustc --edition 2021 r40_rc_ways.rs =====
(exit 0)
===== ./r40_rc_ways =====
[1] (*r).clone()          shared   strong_count 1
[2] try_unwrap with 2 owners -> is_err true
[3] try_unwrap with 1 owner  -> shared
(exit 0)
```

- ★★ **`[1]` `(*r).clone()`** — 가리키는 `String` 을 복제(`strong_count 1` 그대로). **`[2]` 주인이 둘이면 `Rc::try_unwrap` 이 `Err`** · **`[3]` 주인이 하나면 `Ok(String)`** — **옮겨 꺼내기는 「나 말고 주인이 없을 때」만** 된다. 여러 주인이 가능한 `Rc` 가 `*r` 이동을 못 하는 이유가 그것이다.

### (6) `Box<dyn Trait>` 로 이질 컬렉션 · `Box::leak`

```rust
// r40_hetero.rs
// 크기가 다른 타입들을 한 Vec 에 — Box<dyn Trait>
use std::mem::size_of;

trait Shape {
    fn area(&self) -> f64;
    fn label(&self) -> String;
}
struct Sq(f64);
struct Rect(f64, f64);
struct Named {
    side: f64,
    name: String,
}
impl Shape for Sq {
    fn area(&self) -> f64 { self.0 * self.0 }
    fn label(&self) -> String { String::from("sq") }
}
impl Shape for Rect {
    fn area(&self) -> f64 { self.0 * self.1 }
    fn label(&self) -> String { String::from("rect") }
}
impl Shape for Named {
    fn area(&self) -> f64 { self.side * self.side }
    fn label(&self) -> String { self.name.clone() }
}

fn main() {
    let shapes: Vec<Box<dyn Shape>> = vec![
        Box::new(Sq(2.0)),
        Box::new(Rect(2.0, 3.0)),
        Box::new(Named { side: 1.0, name: String::from("tile") }),
    ];
    for s in &shapes {
        print!("{}={} ", s.label(), s.area());
    }
    println!();
    println!("sizes of the values: {} {} {}", size_of::<Sq>(), size_of::<Rect>(), size_of::<Named>());
    println!("size of each element in the Vec: {}", size_of::<Box<dyn Shape>>());
}
```

```text
===== rustc --edition 2021 r40_hetero.rs =====
(exit 0)
===== ./r40_hetero =====
sq=4 rect=6 tile=1 
sizes of the values: 8 16 32
size of each element in the Vec: 16
(exit 0)
```

- ★★ **크기가 8 · 16 · 32 로 다른 세 타입이 한 `Vec` 에** 들어갔다 — 원소 하나는 **`Box<dyn Shape>` 16 으로 같다.** `Vec<T>` 는 `T` 의 크기가 하나여야 하는데, **`Box` 가 크기를 포인터로 바꿔** 그것을 맞췄다.
  디스패치(vtable)와 dyn 호환 조건은 [**33번 주제**](../33-dyn-trait-objects-and-object-safety/)가 정본이다 — 여기서는 **담는 쪽**만 본다.

```rust
// r40_leak.rs
fn config() -> &'static str {
    let s: String = format!("mode={}", 3);
    Box::leak(s.into_boxed_str())
}

fn main() {
    let c: &'static str = config();
    println!("{c}");
}
```

```text
===== rustc --edition 2021 r40_leak.rs =====
(exit 0)
===== ./r40_leak =====
mode=3
(exit 0)
```

- ★ **`Box::leak` 은 `Box` 를 먹고 `&'a mut T` 를 준다** — 여기서는 `'static` 으로 받았다(`mode=3`). std: 「프로그램이 **끝날 때까지 사는** 데이터에 주로 쓴다. 돌려받은 참조를 버리면 **메모리가 샌다**」. **경계만** — 누수는 안전하지만(메모리 안전 위반이 아니다) **되돌리려면 `Box::from_raw`** 가 필요하다(std — 이 문서는 던지지 않았다).

## 문법 — 형태와 규칙

```text
   형태

   enum List { Cons(i32, Box<List>), Nil }                  ← 재귀 필드는 포인터(Box · & · Rc)
   List::Cons(1, Box::new(List::Cons(2, Box::new(List::Nil))))   ← 만드는 자리마다 Box::new
   let b: Box<[u8]> = vec![0u8; N].into_boxed_slice();       ← 큰 값은 처음부터 힙에
   let s: String = *b;                                       ← Box 에서만 옮겨 꺼내기
   let v: Vec<Box<dyn Shape>> = vec![Box::new(A), Box::new(B)];   ← 크기가 다른 타입을 한 Vec 에
   let r: &'static str = Box::leak(s.into_boxed_str());      ← 새는 대신 'static


   금지 사례 — 던져서 받은 것 (번호만) · help: 를 따라간 사슬

   enum List { Cons(i32, List), Nil }         ✘ E0072 (+ 값을 만들면 E0391)
     → Box<List> 로 (타입만)                   ✘ E0308 ×2 → Box::new ×2 → ✔        (두 바퀴)
     → &List 로                                ✘ E0106 → <'a> + &'a List → ✘ E0106 → &'a List<'a> → ✔   (세 바퀴)
   let s: String = *rc;                       ✘ E0507
     → help ① *를 빼라 / ② r.clone()          ✘ E0308 / ✘ E0308 → help r.to_string() → ✔ (복사)
   Box::new([7u8; 16 MiB])  -C opt-level=0    실행 exit 134 (stack overflow) — 1·2·3 은 0
```

**규칙 불릿.**

- ★★★ **재귀 필드는 포인터여야 한다**(Reference) — `Box` 는 소유 · `&` 는 빌림(수명) · `Rc` 는 공유((1)).
- ★★ **`Box<T>`(`T: Sized`)는 포인터 하나(보장) · DST 를 가리키면 두 칸(16 — 이 판) · `Option<Box<_>>` 는 안 커진다(보장)**((2)).
- ★★ **`Box::new(x)` 는 `x` 를 먼저 만든다** — 큰 값은 `vec!`·`into_boxed_slice` 로((4)).
- ★ **`*b` 이동은 `Box` 만** — `Rc` 는 `try_unwrap`·`(*r).clone()`((5)).

## 어디서 틀리나

### 1. ★★★ 「`help:` 대로 `Box` 를 넣으면 끝이다」

**만드는 자리가 E0308 로 두 번 더 막힌다**((1)). `help:` 가 고친 것은 **타입 정의**뿐이다. 각 E0308 의 `help:`(`Box::new`)를 **전부** 따라야 통과한다. `&` 를 고르면 **E0106 이 두 번** 더 나온다.

### 2. ★★★ 「`Box<dyn Trait>` 는 16 바이트다(보장)」

**Reference 가 「기대지 마라」고 적는다**((2) · 33번). 보장은 **`T: Sized` 인 `Box<T>` 가 포인터 하나**라는 것과 **`Option<Box<_>>` 가 안 커진다**는 것이다.

### 3. ★★ 「`Box::new` 에 넣으면 처음부터 힙에 만들어진다」

**`x` 는 먼저 만들어져 값으로 넘어간다**((4)). 16 MiB 배열이 `opt-level=0` 에서 **스택 오버플로 · exit 134** 였다. 최적화 판이 안 터진 것은 **보장이 아니다.**

### 4. ★★ 「`Box` 변수도 힙에 있다」

**보관증(변수)은 스택, 물건(값)은 힙**((3) — `the Box variable : [stack]` · `*b : [heap]`).

### 5. ★★ 「`Rc` 도 `*r` 로 꺼낼 수 있다」

**E0507**((5)). 그리고 **`help:` 둘이 다 E0308** 로 틀렸다. 주인이 하나일 때만 `Rc::try_unwrap`, 아니면 `(*r).clone()`.

### 6. ★ 「에러가 둘이니 원인도 둘이다」

**E0391 은 E0072 의 그림자**다((1)) — 값을 안 만들면 사라진다. **첫 에러부터** 고쳐라.

### 7. ★ 「`Option<i32>` 도 틈새로 4 바이트다」

**8** 이다((2)). `i32` 에는 **안 쓰는 비트 패턴이 없다.** 틈새는 **널이 될 수 없는 포인터**·`NonZero` 같은 타입에만 있다.

## 구현 세부사항 대 언어 보장

| 항목 | 무엇인가 | 근거 |
|---|---|---|
| ★★★ **재귀 필드가 포인터여야** 하는 것 | ★ **언어 보장** — Reference(Recursive types) 「the recursive fields of the type must be pointer types」 | (1)의 E0072 |
| E0391 이 **따라 나오는** 것 | ★ **구현 세부** — 컴파일러의 질의(drop 계산) 순서. 판마다 바뀔 수 있다 | (1) |
| `help:` 의 처방·사슬 | ★ **구현 세부** — 진단의 제안. **E0072 는 맞지만 미완**, **E0507 은 둘 다 틀림** | (1)·(5) |
| ★★ `Box<T>`(`T: Sized`) = **포인터 하나** | ★ **std 보장** — boxed 모듈 문서 Memory layout | (2) — 8 |
| `Box<[T]>`·`Box<dyn T>` = **16** | ★ **구현 세부** — Reference Type layout 「Though you should not rely on this, all pointers to DSTs are currently twice the size of … usize」(33번) | (2) |
| ★★ `Option<Box<U>>` 가 **안 커지는** 것 | ★ **std 보장** — Option Representation | (2) — 8 · 16 |
| `List` 가 `(i32, Box<List>)` 와 **같은 16** | ★ **이 판의 관찰** — 배치(`Nil` 을 널로)는 크기에서 읽은 것이다 | (2) |
| `Box` 값이 **힙**에 있는 것 | ★ **std** — 「기본 할당기가 정의하는 힙」 · 영역 **이름**(`[heap]`·익명)은 **glibc 의 관찰** | (3) |
| ★★ 큰 배열 `Box::new` 가 **opt-level=0 에서만** 터지는 것 | ★ **구현 세부 + 환경** — 복사 제거는 최적화의 결과(보장 아님) · 스택 8 MiB 는 `ulimit` | (4) |
| `*b` 이동이 **`Box` 만** 되는 것 | ★ **언어 보장** — Reference `expr.move.movable-place` | (5) |
| `Box::leak` 이 **`&'a mut T`** 를 주는 것 | ★ **std 의 API**(1.26.0~) | (6) |

## 언제 쓰고 언제 안 쓰나

- ★★ **재귀 타입** — 한 주인이면 `Box`, 꼬리를 나눠 가지면 `Rc`(41번), 스택 위의 짧은 구조면 `&`((1)).
- ★★ **크기가 다른 타입을 한 컬렉션에** — `Vec<Box<dyn Trait>>`((6) · 33번).
- ★★ **스택에 안 들어가는 큰 값** — `Box::new([…; N])` 말고 **`vec![…; N].into_boxed_slice()`**((4)).
- ★ **값을 힙으로 옮겨 이동을 싸게** — 큰 구조체를 자주 옮기면 `Box` 로 보관증만 옮긴다(**이 문서는 비용을 재지 않았다**).
- ★ **안 쓴다** — 작은 `Sized` 값을 그냥 `Box` 에 넣는 것. 크기가 정해진 값은 **그대로 두는 게 기본**이다. `Vec`·`String` 은 **이미 힙을 쓴다**(`Box<Vec<T>>` 는 보관증의 보관증이다).
- ★ **`Box::leak`** — 프로그램 끝까지 사는 설정·문자열 테이블 정도. 반복해서 부르면 **계속 샌다**((6)).

## 핵심 문장

- ★★★ **`enum List { Cons(i32, List), Nil }` 은 E0072 — 재귀 필드는 포인터여야 한다(Reference). `help:` 대로 `Box` 를 넣으면 만드는 자리가 E0308 × 2 로 한 바퀴 더 돈다**((1)).
- ★★ **`Box<i32>` 8(보장) · `Box<[i32]>`·`Box<dyn Display>` 16(이 판) · `Option<Box<i32>>` 8(보장) · `List` 16 = `(i32, Box<List>)` 16**((2)).
- ★★ **`Box` 변수는 스택, 가리키는 값은 힙 — 주소 대신 영역 이름으로 `true` · `false`**((3)).
- ★★ **`Box::new([7u8; 16 MiB])` 는 `opt-level=0` 에서만 exit 134 — `Box::new` 는 값을 먼저 만든다. `vec!` 판은 네 판 다 0**((4)).
- ★ **`*b` 이동은 `Box` 만 — `Rc` 는 E0507, 그 `help:` 둘은 다 E0308**((5)).

## 관련 자료

- ★★ [`memory-management/`](../../../../memory-management/README.md) — **경계**: 스택 프레임(3절) · 가상 주소 공간의 세그먼트(4절) · 힙의 성장(11절) 같은 **스택·힙 일반은 거기**다. 여기는 **`Box` 가 그 위에서 무엇을 보장하나**(포인터 하나 · 널 아님 · 옮겨 꺼내기)만 쓴다.
- ★★ [**33번 주제** — `dyn Trait`](../33-dyn-trait-objects-and-object-safety/) — 이 주제가 갈라져 나온 곳. **fat pointer 16 과 Reference 두 쪽의 어긋남**, vtable 배치를 거기서 인용했다.
- ★ [**35번 주제** — 함수 포인터](../35-function-pointers-and-returning-closures/) — `Option<fn()>` 8 · `Box<dyn Fn>` 16. (2)의 틈새와 같은 규칙.
- [**08번 주제** — 이동](../08-ownership-and-move/) — (5)의 뿌리. 08번이 받은 E0507 은 **`Vec` 의 인덱스에서** 옮기려 한 경우다(「cannot move out of index of `Vec<String>`」) — 같은 번호, 다른 자리.
- [**38번 주제** — `Vec<T>`](../38-vec-api-capacity-retain-and-drain/) — `into_boxed_slice`(남는 용량을 버린다)와 `Vec` 헤더 24.
- [**37번 주제** — `IntoIterator` 세 형태](../37-intoiterator-three-forms-iter-iter-mut-into-iter/) (2) — `Box<[T]>` 의 `.into_iter()` 가 2024 에서 뜻이 바뀐 것(boxed 모듈 문서의 Editions 절).
- 목록의 **41번 주제** — `Rc`/`Arc`. (1)의 `Rc` 판과 (5)의 `try_unwrap` 이 거기서 본체가 된다.
- 목록의 **43번 주제** — `Deref` 강제. `&Box<T>` 가 `&T` 처럼 쓰이는 이유(`sum(rest)` 에 `&Box<List>` 를 넘긴 자리).

## 용어 풀이

- **`Box<T>`** — 힙에 `T` 하나를 두고 그것을 소유하는 포인터. 버려지면 값도 풀린다.
- **재귀 타입** — 필드가 자기 타입을 (직간접으로) 품는 타입. 재귀 필드는 포인터여야 한다.
- **DST(크기 없는 타입)** — `[T]`·`str`·`dyn Trait`. 포인터 뒤에서만 쓴다.
- **fat pointer** — 주소 + 부가 정보(길이·vtable)를 함께 든 포인터.
- **틈새(niche) / 널 포인터 최적화** — 절대 안 쓰는 비트 패턴을 `None` 등에 쓰는 것.
- **스택 오버플로** — 스레드 스택이 한도를 넘는 것. Rust 는 런타임이 프로세스를 **중단**시킨다(`abort`).
- **`Box::leak`** — `Box` 를 먹고 긴 수명의 참조를 주는 함수. 메모리는 돌아가지 않는다.
- **`Rc::try_unwrap`** — 주인이 하나일 때만 안쪽 값을 **옮겨** 꺼낸다.

## 더 들어가면

- **`Box<dyn Trait>` 의 기본 수명은 `'static`** — `Box<dyn Display>` 는 `Box<dyn Display + 'static>` 이다. [33번 주제](../33-dyn-trait-objects-and-object-safety/) (6)이 받았다.
- **`Box::new_uninit`(1.82)** — 초기화 안 된 상자를 먼저 힙에 잡고 나중에 채운다. (4)의 스택 경유를 피하는 다른 길이다(이 문서는 던지지 않았다).
- **`Box<[T]>` 의 `.into_iter()` 는 2024 부터 값** — std boxed 모듈 문서의 Editions 절이 배열의 2021 특례와 나란히 적는다. 격자는 37편 (2).
- **스레드 스택 크기** — 주 스레드는 `ulimit -s`, `std::thread::Builder::stack_size` 로 새 스레드의 스택을 정할 수 있다(목록의 **49번 주제** — 이 문서는 던지지 않았다).
