# rust/syntax/09 — `Copy`와 `Clone`, 그리고 `Drop` 시점 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [The Rust Reference](https://doc.rust-lang.org/reference/) 의 Destructors 절 ·
> [std `Copy`](https://doc.rust-lang.org/std/marker/trait.Copy.html) · [std `Clone`](https://doc.rust-lang.org/std/clone/trait.Clone.html) ·
> [std `Drop`](https://doc.rust-lang.org/std/ops/trait.Drop.html) · [std `mem::drop`](https://doc.rust-lang.org/std/mem/fn.drop.html) ·
> `rustc --explain E0184` / `E0204` / `E0040` / `E0277` / `E0599`.
> **실행 검증** — 이 문서의 모든 출력·에러·경고는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 얻은 것이다. `cargo` 는 쓰지 않았다.\
> ★ **`rustc ex.rs` 만 쓰면 에디션 2015 다.** 이 갈래는 `--edition 2021` 을 반드시 붙인다.\
> 소스 파일 이름은 전부 `ex.rs` 로 고정했고, **진단의 줄 번호는 그 파일 기준**이다.
> **버전** — `Copy`·`Clone`·`Drop`·`mem::drop` 은 전부 1.0.0부터다(std 문서의 Stable since 확인).\
> `dropping_copy_types` 린트만 이름이 바뀐 적이 있다(아래 「구현 세부사항 대 언어 보장」).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**베끼면 끝나는 물건과, 주인이 나갈 때 뒷정리가 필요한 물건은 다르게 다룬다.**

[**08번 주제**](../08-ownership-and-move/)가 「값을 넘기면 잃는다」였다면, 이 주제는
「**어떤 값은 안 잃는다**」와 「**잃은 값이 정확히 언제 치워지나**」다.

| 비유 | 실체 |
|---|---|
| 종이에 적은 전화번호 — 베껴 적어도 원본이 멀쩡하다 | **`Copy`** 타입(`i32`·`bool`·`&T` …) |
| 사진을 인화해 한 장 더 만든다 — 돈과 시간이 든다 | **`Clone`** — `clone()` 을 **내가 불러야** 생긴다 |
| 베껴 적을 수 있으려면 「베끼는 법」이 정의돼 있어야 한다 | **`Copy: Clone`** — `Copy` 는 `Clone` 을 **요구한다** |
| 나갈 때 불 끄고 문 잠그는 사람 | **`Drop`** 을 구현한 타입 |
| 불 끌 게 있으면 「그냥 베끼기」를 못 한다 | **`Copy` 와 `Drop` 은 같이 못 온다**(E0184) |
| 방을 나가는 순서 — 나중에 들어온 사람이 먼저 나간다 | 지역 변수는 **선언 역순** 해제 |
| 상자 안 칸을 치우는 순서 — 적힌 순서대로 | 구조체 필드는 **선언 순** 해제 |

- `Copy` 는 **트레이트 하나**다. 크기도 힙 여부도 기준이 아니다(08번 주제의 결론).
- `Clone` 은 **비싼 쪽**이고 **명시적**이다. `Copy` 는 **싼 쪽**이고 **암묵적**이다.
- `Drop` 이 붙으면 **해제 시점이 관찰 가능해진다** — 이 주제가 그 창을 계속 쓴다.

```text
   Copy                              Clone                           Drop
   let b = a;  뒤에도 a 가 산다        let b = a.clone();  내가 부른다    스코프 끝에서 내 코드가 불린다
        |                                  |                               |
   비트 복사로 끝난다                    깊이는 타입이 정한다                뒷정리가 필요한 타입
        |                                  |                               |
        +---- Copy 는 Clone 을 요구한다 ----+                               |
        |                                                                  |
        +------------ 이 둘은 같이 못 온다 (E0184) -------------------------+
```

**언어도 똑같은 구조다.** 실측이 이 그림 그대로다.

```text
error[E0184]: the trait `Copy` cannot be implemented for this type; the type has a destructor
 --> ex.rs:2:17
  |
2 | #[derive(Clone, Copy)]
  |                 ^^^^ `Copy` not allowed on types with destructors
```

> **`Copy`** — 비트를 그대로 베껴도 두 값이 각자 멀쩡한 타입에 붙는 표식(marker).\
> 예: `let b = a;` 뒤에 `a` 가 살아 있으면 `a` 의 타입이 `Copy` 다.

> **`Clone`** — 사본을 만드는 법을 정의한 트레이트. `clone()` 을 **내가 불러야** 동작한다.\
> 예: `String::clone` 은 힙을 새로 할당하고, `Rc::clone` 은 카운트만 올린다.

> **`Drop`** — 값이 해제되는 순간에 불릴 코드를 적는 자리.\
> 예: `impl Drop for D { fn drop(&mut self) { println!(...) } }` 로 해제 시점을 출력한다.

> **소멸자(destructor)** — 해제 시 자동으로 실행되는 정리 코드.\
> Rust 에서는 `Drop::drop` 과 **필드들의 재귀적 해제**를 합쳐 부른다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **어떤 타입이 `Copy` 가 되나** — 붙일 수 있는 조건과 못 붙이는 조건은 무엇인가.
2. **`clone()` 이 무엇을 베끼나** — 얕은가 깊은가, 그리고 그것을 누가 정하나.
3. **정확히 어느 줄에서 해제되나** — 지역 변수·구조체 필드·튜플·`Vec` 원소의 순서는 각각 무엇인가.

★ 08번이 「그 값이 누구 것인가」였다면 여기는 「**누구 것인지가 안 바뀌는 타입**」과
「**주인이 나갈 때 무슨 일이 일어나나**」다.

## 동작 방식

### (0) 이 주제가 쓰는 세 창

**언제 쓰나** — 아래 모든 절이 이 셋 중 하나로 접지한다.

| 창 | 무엇을 보여 주나 | 08번에서 이어받은 것 |
|---|---|---|
| **`impl Drop` + `println!`** | **해제 시점** — 컴파일러가 말해 주지 않는 유일한 것 | ★ 08의 창 그대로 |
| **일부러 던져서 받는 컴파일 에러** | `Copy` 판정 규칙 — E0184·E0204·E0277 | 08의 「에러도 출력이다」 |
| **`size_of`·`align_of`** | 크기가 `Copy` 판정과 **무관**하다는 반증 | 새로 세운다 |

```rust
struct D(&'static str);
impl Drop for D {
    fn drop(&mut self) { println!("        [해제] {}", self.0); }
}
```

- 이 `D` 하나를 문서 끝까지 쓴다. `String`·`Vec` 자체에는 `Drop` 을 못 단다(고아 규칙 — [목록의 **26번 주제**](../26-orphan-rule-and-newtype/)).
- ★ **`D` 는 `Copy` 가 될 수 없다.** 아래 (3)이 그 이유다 — 그래서 이 창은 `Copy` 타입에는 못 쓴다.

비용 — 없음. 관찰용 `println!` 하나뿐이다.

### (1) ★ `Copy` 는 `Clone` 을 요구한다

**언제 쓰나** — `#[derive(Copy)]` 를 쓸 때마다.

```text
===== 소스: ex.rs =====
// Copy 만 파생하면? — Copy 가 Clone 을 요구하는지 던져서 본다
#[derive(Copy)]
struct P { x: i32, y: i32 }

fn main() {
    let a = P { x: 1, y: 2 };
    let b = a;
    println!("{} {} / {} {}", a.x, a.y, b.x, b.y);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0277]: the trait bound `P: Clone` is not satisfied
 --> ex.rs:2:10
  |
2 | #[derive(Copy)]
  |          ^^^^ the trait `Clone` is not implemented for `P`
  |
note: required by a bound in `Copy`
 --> /rustc/ded5c06cf21d2b93bffd5d884aa6e96934ee4234/library/core/src/marker.rs:465:1
help: consider annotating `P` with `#[derive(Clone)]`
  |
3 + #[derive(Clone)]
4 | struct P { x: i32, y: i32 }
  |

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0277`.
```

```text
   std 의 선언                       내 타입에 요구되는 것
   pub trait Copy: Clone { }         #[derive(Copy)]      -> E0277
                 ^^^^^^^             #[derive(Clone, Copy)] -> 통과
                 상위 트레이트

   Clone 만 있어도 된다               Copy 만 있을 수는 없다
   #[derive(Clone)]  -> 통과          (베끼는 법이 정의돼 있어야 한다)
```

그림 해설 (한 단계씩):

- 에러가 이유를 통째로 말한다 — **`required by a bound in Copy`**.
- `Copy` 의 선언이 `pub trait Copy: Clone` 이므로 **`Clone` 이 상위 트레이트**다.
- 즉 **`Copy` 는 `Clone` 의 부분집합**이다. 거꾸로는 아니다 — `String` 은 `Clone` 이지만 `Copy` 가 아니다.
- 컴파일러가 고치는 법까지 댄다 — `consider annotating P with #[derive(Clone)]`.

비용 — 없음. `derive(Clone)` 이 만드는 `clone()` 은 `Copy` 타입에서는 비트 복사와 같다.

### (2) ★ `Copy` 를 붙일 수 있는 조건 — 필드 하나가 결정한다

**언제 쓰나** — 구조체를 값으로 여기저기 넘기고 싶을 때.

```text
===== 소스: ex.rs =====
// String 이 든 구조체에 Copy 를 붙이면?
#[derive(Clone, Copy)]
struct Label { text: String }

fn main() {
    let l = Label { text: String::from("라벨") };
    println!("{}", l.text);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0204]: the trait `Copy` cannot be implemented for this type
 --> ex.rs:2:17
  |
2 | #[derive(Clone, Copy)]
  |                 ^^^^
3 | struct Label { text: String }
  |                ------------ this field does not implement `Copy`

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0204`.
```

`rustc --explain E0204`:

> The `Copy` trait was implemented on a type which contains a field that doesn't
> implement the `Copy` trait.
>
> (…)
>
> ```
> #[derive(Copy)] // error!
> struct Foo<'a> {
>     ty: &'a mut bool,
> }
> ```
>
> This fails because `&mut T` is not `Copy`, even when `T` is `Copy` (this
> differs from the behavior for `&T`, which is always `Copy`).

그림 해설 (한 단계씩):

- **필드 하나라도 `Copy` 가 아니면 그 구조체는 `Copy` 가 못 된다.** 전부 `Copy` 여야 한다.
- 에러가 **범인을 정확히 짚는다** — `this field does not implement Copy`.
- ★ `--explain` 이 덤으로 하나 더 말한다 — **`&T` 는 항상 `Copy` 이고 `&mut T` 는 아니다.**\
  그 정본은 [**10번 주제**](../10-borrowing-and-aliasing-rules/)다.

비용 — 없음. 전부 컴파일 타임 판정이다.

### (3) ★★ `Copy` 와 `Drop` 은 함께 못 온다

**언제 쓰나** — 「가벼우니 `Copy` 로 해 두자」와 「해제 때 로그를 남기자」가 만나는 자리.

```text
===== 소스: ex.rs =====
// Copy 와 Drop 을 함께 달면?
#[derive(Clone, Copy)]
struct Tag(i32);

impl Drop for Tag {
    fn drop(&mut self) { println!("[해제] Tag({})", self.0); }
}

fn main() {
    let t = Tag(1);
    let u = t;
    println!("{} {}", t.0, u.0);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0184]: the trait `Copy` cannot be implemented for this type; the type has a destructor
 --> ex.rs:2:17
  |
2 | #[derive(Clone, Copy)]
  |                 ^^^^ `Copy` not allowed on types with destructors

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0184`.
```

`rustc --explain E0184`:

> Explicitly implementing both `Drop` and `Copy` trait on a type is currently
> disallowed. This feature can make some sense in theory, but the current
> implementation is incorrect and can lead to memory unsafety (see
> [issue #20126][iss20126]), so it has been disabled for now.

**왜 그런가 — 08번의 해제 시점으로 설명된다.**

```text
   Copy 가 아닌 Drop 타입               만약 Copy 이면서 Drop 이라면
   let t = Tag(1);                     let t = Tag(1);
   let u = t;      <- 이동              let u = t;      <- 복사 (t 도 산다)
   +---------------+                   +----------------+
   | t  [무효]     |                   | t  Tag(1)      |
   | u  Tag(1)     |                   | u  Tag(1)      |
   +---------------+                   +----------------+
   }  -> [해제] 한 번                   }  -> [해제] t
                                          -> [해제] u    <- 같은 자원을 두 번
   08번의 「해제는 정확히 한 번」          double free 로 가는 길
```

그림 해설 (한 단계씩):

- 08번이 세운 규칙은 「**이동해도 해제는 정확히 한 번**」이었다. 이름이 옮겨 가면 옛 이름 쪽은 해제를 안 한다.
- `Copy` 는 **옛 이름도 살려 둔다**. 그러면 **같은 값이 두 이름에 있고, 스코프 끝에 소멸자가 두 번** 불린다.
- 소멸자가 하는 일이 「힙 반납」이면 그것이 곧 **double free** 다. 그래서 언어가 조합 자체를 막는다.
- ★ 뒤집어 읽으면 이렇다 — **`Copy` 타입에는 소멸자가 있을 수 없다.**\
  그래서 (0)의 관찰 창(`impl Drop`)을 `Copy` 타입에는 **원리적으로 못 단다.**
- `--explain` 은 「이론적으로는 말이 될 수 있지만 현재 구현이 틀려서 막아 둔 것」이라고 **이유를 구현 쪽에 둔다.**\
  ★ 그 문장의 `currently`·`for now` 는 **언어 보장이 아니라 현재 상태**라는 신호다.

비용 — 없음. 설계 단계에서 **둘 중 하나를 고르라**는 강제다.

### (4) ★ `clone()` 이 얕은가 깊은가 — 타입이 정한다

**언제 쓰나** — `clone()` 을 붙이기 전에 「무엇이 복제되나」를 물을 때.

```text
===== 소스: ex.rs =====
// clone() 은 얕은가 깊은가 — Vec 과 Rc 를 같은 자리에서 대조한다
use std::rc::Rc;

fn main() {
    println!("(1) Vec::clone — 버퍼를 새로 할당한다");
    let v1 = vec![1u8, 2, 3];
    let v2 = v1.clone();
    println!("    v1 버퍼 {:p} / v2 버퍼 {:p}", v1.as_ptr(), v2.as_ptr());
    println!("    같은 버퍼인가? {}", std::ptr::eq(v1.as_ptr(), v2.as_ptr()));

    println!("(2) Rc::clone — 카운트만 올린다");
    let r1 = Rc::new(vec![1u8, 2, 3]);
    println!("    r1 만든 직후 strong_count = {}", Rc::strong_count(&r1));
    let r2 = Rc::clone(&r1);
    println!("    r2 = Rc::clone(&r1) 뒤 strong_count = {}", Rc::strong_count(&r1));
    println!("    r1 속 버퍼 {:p} / r2 속 버퍼 {:p}", r1.as_ptr(), r2.as_ptr());
    println!("    같은 버퍼인가? {}", std::ptr::eq(r1.as_ptr(), r2.as_ptr()));
    drop(r2);
    println!("    r2 를 drop 한 뒤 strong_count = {}", Rc::strong_count(&r1));

    println!("(3) Rc 안의 Vec 을 (*r1).clone() 하면 — 이건 깊다");
    let deep: Vec<u8> = (*r1).clone();
    println!("    deep 버퍼 {:p} / 같은 버퍼인가? {}", deep.as_ptr(), std::ptr::eq(r1.as_ptr(), deep.as_ptr()));
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
(1) Vec::clone — 버퍼를 새로 할당한다
    v1 버퍼 0x607669d5ed00 / v2 버퍼 0x607669d5ed20
    같은 버퍼인가? false
(2) Rc::clone — 카운트만 올린다
    r1 만든 직후 strong_count = 1
    r2 = Rc::clone(&r1) 뒤 strong_count = 2
    r1 속 버퍼 0x607669d5ed40 / r2 속 버퍼 0x607669d5ed40
    같은 버퍼인가? true
    r2 를 drop 한 뒤 strong_count = 1
(3) Rc 안의 Vec 을 (*r1).clone() 하면 — 이건 깊다
    deep 버퍼 0x607669d5ed60 / 같은 버퍼인가? false
(종료 코드 0)
```

★ **주소 절댓값은 실행마다 바뀐다**(ASLR). 근거로 읽을 칸은 「**같은가 / 다른가**」와 **카운트 값**뿐이다.

```text
   Vec::clone — 깊다                    Rc::clone — 얕다
   v1 ptr --+--> [1,2,3]  0x..d00       r1 --+                     count
   v2 ptr --+--> [1,2,3]  0x..d20            +--> (count=2)--> [1,2,3]  0x..d40
            서로 다른 버퍼                r2 --+
            고치면 따로 논다                   같은 버퍼. 고치면 둘 다 본다
                                              drop(r2) -> count=1
```

그림 해설 (한 단계씩):

- **`clone()` 자체는 「깊게 하라」는 뜻이 아니다.** 무엇을 베낄지는 **그 타입의 `Clone` 구현**이 정한다.
- `Vec`·`String` 은 **버퍼를 새로 할당**한다(주소가 다르다 — 08번 2번 실측과 같은 근거).
- ★ **`Rc::clone` 은 카운트만 1 올린다**(`1 → 2`, `drop` 하면 `1`). 버퍼는 **그대로 공유**한다.\
  정본은 [목록의 **41번 주제**](../41-rc-arc-shared-ownership-and-weak-cycles/)다. 여기서는 **현상만** 싣는다.
- (3)이 갈라 보여 준다 — `Rc` 를 벗기고 `(*r1).clone()` 하면 **안쪽 `Vec` 의 깊은 복제**가 된다.\
  같은 `.clone()` 글자인데 **어느 타입에 붙었느냐**로 갈린다.

비용 — `Vec::clone` 은 **할당 + 원소 복사**. `Rc::clone` 은 **정수 하나 증가**.

### (5) `derive(Clone)` 이 만드는 것과 손으로 쓴 `impl Clone`

**언제 쓰나** — 제네릭 타입에 `Clone` 을 붙일 때.

```text
===== 소스: ex.rs =====
// derive(Clone) 이 만드는 것 — 제네릭 파라미터에 T: Clone 경계를 붙인다
use std::rc::Rc;

#[derive(Clone)]
struct Derived<T>(Rc<T>);      // Rc<T> 는 T 가 뭐든 Clone 인데?

struct Manual<T>(Rc<T>);
impl<T> Clone for Manual<T> {  // 손으로 쓰면 경계를 안 붙일 수 있다
    fn clone(&self) -> Self { Manual(Rc::clone(&self.0)) }
}

struct NotClone;               // Clone 이 아닌 타입

fn main() {
    let m = Manual(Rc::new(NotClone));
    let _m2 = m.clone();
    println!("손으로 쓴 impl Clone: 통과");

    let d = Derived(Rc::new(NotClone));
    let _d2 = d.clone();
    println!("derive(Clone): 통과");
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0599]: the method `clone` exists for struct `Derived<NotClone>`, but its trait bounds were not satisfied
  --> ex.rs:20:17
   |
 5 | struct Derived<T>(Rc<T>);      // Rc<T> 는 T 가 뭐든 Clone 인데?
   | ----------------- method `clone` not found for this struct because it doesn't satisfy `Derived<NotClone>: Clone`
...
12 | struct NotClone;               // Clone 이 아닌 타입
   | --------------- doesn't satisfy `NotClone: Clone`
...
20 |     let _d2 = d.clone();
   |                 ^^^^^ method cannot be called on `Derived<NotClone>` due to unsatisfied trait bounds
   |
note: trait bound `NotClone: Clone` was not satisfied
  --> ex.rs:4:10
   |
 4 | #[derive(Clone)]
   |          ^^^^^ unsatisfied trait bound introduced in this `derive` macro
help: consider annotating `NotClone` with `#[derive(Clone)]`
   |
12 + #[derive(Clone)]
13 | struct NotClone;               // Clone 이 아닌 타입
   |

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0599`.
```

```text
   #[derive(Clone)] 이 만드는 것          손으로 쓴 것
   impl<T: Clone> Clone for Derived<T>   impl<T> Clone for Manual<T>
          ^^^^^^^                               ^
          파라미터마다 경계를 붙인다             경계가 없다

   Derived<NotClone> -> clone() 없음      Manual<NotClone> -> clone() 있다
   (필드 타입이 Rc<T> 라서 사실 필요 없는데도)
```

그림 해설 (한 단계씩):

- `derive(Clone)` 은 **타입 파라미터마다 `T: Clone` 경계를 기계적으로 붙인다.**
- 그런데 여기 필드는 `Rc<T>` 이고 **`Rc<T>` 는 `T` 가 무엇이든 `Clone` 이다.** 경계가 필요 없는데 붙었다.
- 에러가 그 사실을 직접 말한다 — **`unsatisfied trait bound introduced in this derive macro`**.
- ★ 그래서 **파생은 편의이지 최선이 아니다.** 제네릭 타입에서 `derive` 가 과하게 조이는 자리가 있다.
- 손으로 쓴 `impl<T> Clone for Manual<T>` 는 그 경계가 없어 **`NotClone` 에도 통한다.**
- `derive` 전수는 [목록의 **27번 주제**](../27-derive-macros-debug-clone-partialeq-default-hash/)가 정본이다.

비용 — 없음(컴파일 타임). 대가는 **API 가 불필요하게 좁아지는 것**이다.

### (6) ★★ `Drop` 순서 — 출력 순서로 본다

**언제 쓰나** — 자원 정리 순서가 중요한 타입(락·파일·트랜잭션 가드)을 쓸 때마다.

```text
===== 소스: ex.rs =====
// Drop 순서 — 지역 변수와 구조체 필드가 서로 반대인지 출력으로 본다
struct D(&'static str);
impl Drop for D {
    fn drop(&mut self) { println!("        [해제] {}", self.0); }
}

struct Pair { first: D, second: D }      // 선언 순서: first -> second

impl Drop for Pair {
    fn drop(&mut self) { println!("    [해제] Pair 본체 먼저"); }
}

struct Plain { a: D, b: D }              // Drop 을 안 단 구조체

fn main() {
    println!("(1) 지역 변수 — 선언 역순인가?");
    {
        let _x = D("지역-1번째");
        let _y = D("지역-2번째");
        let _z = D("지역-3번째");
        println!("    블록 끝 직전");
    }

    println!("(2) 구조체 필드 — 선언 순인가? (Drop 없는 구조체)");
    {
        let _p = Plain { a: D("필드-a(먼저 선언)"), b: D("필드-b(나중 선언)") };
        println!("    블록 끝 직전");
    }

    println!("(3) Drop 을 단 구조체 — 본체와 필드 중 누가 먼저인가?");
    {
        let _p = Pair { first: D("필드-first"), second: D("필드-second") };
        println!("    블록 끝 직전");
    }

    println!("(4) 튜플");
    {
        let _t = (D("튜플-0"), D("튜플-1"), D("튜플-2"));
        println!("    블록 끝 직전");
    }

    println!("(5) Vec 원소");
    {
        let _v = vec![D("벡터-0"), D("벡터-1"), D("벡터-2")];
        println!("    블록 끝 직전");
    }

    println!("(6) 함수 인자 — 여러 개면?");
    fn two(_p: D, _q: D) { println!("    two 몸통 끝"); }
    two(D("인자-앞"), D("인자-뒤"));

    println!("(7) main 끝");
}
===== rustc --edition 2021 ex.rs -o ex =====
warning: fields `first` and `second` are never read
 --> ex.rs:7:15
  |
7 | struct Pair { first: D, second: D }      // 선언 순서: first -> second
  |        ----   ^^^^^     ^^^^^^
  |        |
  |        fields in this struct
  |
  = note: `#[warn(dead_code)]` (part of `#[warn(unused)]`) on by default

warning: fields `a` and `b` are never read
  --> ex.rs:13:16
   |
13 | struct Plain { a: D, b: D }              // Drop 을 안 단 구조체
   |        -----   ^     ^
   |        |
   |        fields in this struct

warning: 2 warnings emitted

===== ./ex =====
(1) 지역 변수 — 선언 역순인가?
    블록 끝 직전
        [해제] 지역-3번째
        [해제] 지역-2번째
        [해제] 지역-1번째
(2) 구조체 필드 — 선언 순인가? (Drop 없는 구조체)
    블록 끝 직전
        [해제] 필드-a(먼저 선언)
        [해제] 필드-b(나중 선언)
(3) Drop 을 단 구조체 — 본체와 필드 중 누가 먼저인가?
    블록 끝 직전
    [해제] Pair 본체 먼저
        [해제] 필드-first
        [해제] 필드-second
(4) 튜플
    블록 끝 직전
        [해제] 튜플-0
        [해제] 튜플-1
        [해제] 튜플-2
(5) Vec 원소
    블록 끝 직전
        [해제] 벡터-0
        [해제] 벡터-1
        [해제] 벡터-2
(6) 함수 인자 — 여러 개면?
    two 몸통 끝
        [해제] 인자-뒤
        [해제] 인자-앞
(7) main 끝
(종료 코드 0)
```

```text
   지역 변수 — 역순(LIFO)              구조체 필드 — 선언 순(FIFO)
   let _x = D("1번째")  +              struct Plain { a, b }
   let _y = D("2번째")  |  +                          |  |
   let _z = D("3번째")  |  |  +                       |  +-> [해제] b  나중
   }                    |  |  +-> [해제] 3번째        +----> [해제] a  먼저
                        |  +----> [해제] 2번째
                        +-------> [해제] 1번째
   나중에 들어온 것이 먼저 나간다        적힌 순서대로 치운다
```

```text
   Drop 을 단 구조체 — 본체가 먼저, 그 다음 필드
   struct Pair { first, second }
   impl Drop for Pair { ... }
        |
        +-> [해제] Pair 본체 먼저     <- Drop::drop(&mut self) 가 먼저 불린다
              +-> [해제] 필드-first    <- 그 다음에 필드가 선언 순으로
              +-> [해제] 필드-second
   ★ 소멸자가 필드를 읽을 수 있어야 하므로 이 순서일 수밖에 없다 (08번의 E0509 와 같은 이유)
```

그림 해설 (한 단계씩):

- ★ **지역 변수는 역순, 구조체 필드는 선언 순** — 방향이 **정반대**다. 이 대비가 이 절의 핵심이다.
- **튜플·`Vec` 원소도 선언 순**(앞에서 뒤로)이다. 필드와 같은 규칙으로 읽으면 된다.
- **`Drop` 을 구현한 구조체는 「본체 먼저, 필드 나중」이다**.\
  `Drop::drop(&mut self)` 안에서 **필드를 읽을 수 있어야** 하므로 순서가 이럴 수밖에 없다.\
  ★ 08번의 **E0509**(`Drop` 구현체는 부분 이동 금지)가 **같은 사실의 다른 얼굴**이다.
- ★ **함수 인자도 역순으로 해제됐다**(`인자-뒤` → `인자-앞`) — 인자는 그 함수의 **지역 변수**처럼 다뤄진다.
- **경고도 출력이다** — `dead_code` 가 「필드를 읽은 적이 없다」를 짚는다. 해제는 읽기가 아니다.

비용 — 없음. 해제 호출을 컴파일러가 **컴파일 타임에 정해진 자리**에 끼워 넣는다.

### (7) `Drop::drop` 은 직접 못 부르고, `mem::drop` 은 그냥 함수다

**언제 쓰나** — 해제를 앞당기고 싶을 때.

```text
===== 소스: ex.rs =====
// Drop::drop 을 직접 부르면?
struct D(&'static str);
impl Drop for D {
    fn drop(&mut self) { println!("[해제] {}", self.0); }
}

fn main() {
    let mut d = D("직접호출");
    d.drop();
    println!("그 뒤");
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0040]: explicit use of destructor method
 --> ex.rs:9:7
  |
9 |     d.drop();
  |       ^^^^ explicit destructor calls not allowed
  |
help: consider using `drop` function
  |
9 -     d.drop();
9 +     drop(d);
  |

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0040`.
```

`rustc --explain E0040`:

> It is not allowed to manually call destructors in Rust.
>
> (…)
>
> It is unnecessary to do this since `drop` is called automatically whenever a
> value goes out of scope. However, if you really need to drop a value by hand,
> you can use the `std::mem::drop` function

**그 `drop` 함수는 특별한 게 없다 — 빈 몸통 함수로 똑같이 된다.**

```text
===== 소스: ex.rs =====
// std::mem::drop 은 그냥 값을 먹는 함수다 — 같은 모양을 내가 써 본다
struct D(&'static str);
impl Drop for D {
    fn drop(&mut self) { println!("        [해제] {}", self.0); }
}

fn my_drop<T>(_x: T) {}          // std::mem::drop 과 같은 몸통(빈 몸통)

fn main() {
    println!("(1) std::mem::drop");
    let a = D("a");
    println!("    drop(a) 직전");
    drop(a);
    println!("    drop(a) 직후");

    println!("(2) 빈 몸통 함수로도 똑같이 된다");
    let b = D("b");
    println!("    my_drop(b) 직전");
    my_drop(b);
    println!("    my_drop(b) 직후");

    println!("(3) Copy 타입을 drop 하면?");
    let n = 7i32;
    drop(n);
    println!("    drop(n) 뒤에도 n = {}", n);

    println!("(4) 크기·정렬 — Copy 판정과 무관하다");
    println!("    i32      size={} align={}", size_of::<i32>(), align_of::<i32>());
    println!("    [i32; 3] size={} align={}", size_of::<[i32; 3]>(), align_of::<[i32; 3]>());
    println!("    String   size={} align={}", size_of::<String>(), align_of::<String>());
    println!("    Vec<i32> size={} align={}", size_of::<Vec<i32>>(), align_of::<Vec<i32>>());
    println!("    &i32     size={} align={}", size_of::<&i32>(), align_of::<&i32>());
    println!("    D        size={} align={}", size_of::<D>(), align_of::<D>());
    println!("(5) main 끝");
}
===== rustc --edition 2021 ex.rs -o ex =====
warning: calls to `std::mem::drop` with a value that implements `Copy` does nothing
  --> ex.rs:24:5
   |
24 |     drop(n);
   |     ^^^^^-^
   |          |
   |          argument has type `i32`
   |
   = note: `#[warn(dropping_copy_types)]` on by default
help: use `let _ = ...` to ignore the expression or result
   |
24 -     drop(n);
24 +     let _ = n;
   |

warning: 1 warning emitted

===== ./ex =====
(1) std::mem::drop
    drop(a) 직전
        [해제] a
    drop(a) 직후
(2) 빈 몸통 함수로도 똑같이 된다
    my_drop(b) 직전
        [해제] b
    my_drop(b) 직후
(3) Copy 타입을 drop 하면?
    drop(n) 뒤에도 n = 7
(4) 크기·정렬 — Copy 판정과 무관하다
    i32      size=4 align=4
    [i32; 3] size=12 align=4
    String   size=24 align=8
    Vec<i32> size=24 align=8
    &i32     size=8 align=8
    D        size=16 align=8
(5) main 끝
(종료 코드 0)
```

```text
   d.drop()                            drop(d)
   = Drop::drop(&mut d) 를 직접 호출     = 값을 먹는 함수에 넘긴다
   -> E0040                            -> 그 함수의 몸통 끝에서 해제
   자원이 반납됐는데 d 가 아직 살아 있게    08번의 「함수에 넘기면 그 함수가 주인」과 같은 규칙
   되므로 막는다
```

그림 해설 (한 단계씩):

- **`d.drop()` 은 E0040** 이다. 소멸자를 직접 부르면 **자원은 반납됐는데 `d` 라는 이름은 아직 살아 있게** 된다.
- ★ **`drop(d)` 는 소유권을 먹어 가므로 그 뒤에 `d` 라는 이름이 죽는다**(08번의 E0382). 그 차이가 전부다.
- **빈 몸통 함수 `my_drop` 이 똑같이 동작했다** — `drop` 에 마법이 없다는 실측이다.\
  std 의 정의도 `pub fn drop<T>(_x: T) {}` 한 줄이다.
- ★ **`Copy` 타입을 `drop()` 하면 아무 일도 안 난다** — `n` 이 그대로 살아 있고, **린트가 경고한다**\
  (`dropping_copy_types`: `does nothing`). **먹어 간 것이 사본**이기 때문이다.
- (4)가 반증이다 — **`[i32; 3]`(12바이트)은 `Copy` 고 `Vec<i32>`(24바이트)는 아니다.**\
  ★ **크기는 `Copy` 판정과 무관하다.** 기준은 **트레이트 하나**다.

비용 — 없음.

## 문법 — 형태와 규칙

### 형태 — 세 트레이트를 붙이는 법

```rust
#[derive(Clone)]                // Clone 만: 언제나 가능(필드가 전부 Clone 이면)
struct A { s: String }

#[derive(Clone, Copy)]          // Copy: Clone 이 반드시 함께 와야 한다
struct B { x: i32, y: i32 }

impl Clone for C {              // 손으로 쓰면 경계를 내가 정한다
    fn clone(&self) -> Self { /* ... */ C }
}

impl Drop for D {               // 소멸자 — derive 는 없다. 반드시 손으로 쓴다
    fn drop(&mut self) { /* 정리 */ }
}
```

- **`Drop` 에는 `derive` 가 없다.** 정리할 것이 무엇인지는 컴파일러가 모른다.
- `Drop::drop` 의 시그니처는 **`fn drop(&mut self)`** 다 — `self` 를 먹지 않는다(먹으면 그 안에서 또 해제된다).

### 금지 사례 — 세 가지 조합이 막힌다

| 쓴 것 | 결과 | 에러가 짚는 곳 |
|---|---|---|
| `#[derive(Copy)]` 만 | **E0277** `the trait bound P: Clone is not satisfied` | `Copy` 의 상위 트레이트 |
| `Copy` + `Copy` 아닌 필드 | **E0204** `this field does not implement Copy` | **그 필드** |
| `Copy` + `impl Drop` | **E0184** `the type has a destructor` | `derive(Copy)` 자리 |
| `d.drop()` | **E0040** `explicit destructor calls not allowed` | 메서드 호출 자리 |

### `Copy` 인 것과 아닌 것

| `Copy` 다 | `Copy` 가 아니다 |
|---|---|
| `i32`·`u8`·`f64`·`bool`·`char` | `String`·`Vec<T>`·`Box<T>`·`HashMap` |
| `&T` (불변 참조) | **`&mut T`** (가변 참조) — `--explain E0204` 가 직접 말한다 |
| `Copy` 만 담은 튜플·배열 (`(i32, bool)`·`[i32; 3]`) | `Copy` 아닌 필드를 하나라도 가진 구조체 |
| `#[derive(Clone, Copy)]` 붙인 구조체 | **`impl Drop` 을 가진 모든 타입** |

## 어디서 틀리나

### 1. ★ 「가벼우니까 `Copy` 겠지」

- 갈리는 기준은 **크기가 아니라 트레이트**다. `[i32; 3]`(12바이트)은 `Copy` 고 `Vec<i32>`(24바이트)는 아니다.
- **`Vec<i32>` 는 원소가 `Copy` 여도 `Copy` 가 아니다** — 컨테이너 타입이 정한다(08번 9번 실측).

### 2. ★★ `Copy` 를 달아 두고 나중에 `Drop` 을 추가한다

- 처음엔 `#[derive(Clone, Copy)] struct Tag(i32);` 로 잘 돌다가,\
  나중에 「해제 때 로그를 남기자」로 `impl Drop` 을 붙이는 순간 **E0184** 가 난다.
- ★ **고치는 방향이 둘뿐이고 둘 다 크다** — `Copy` 를 떼고 모든 호출부를 이동/빌림으로 고치거나, 정리를 포기하거나.
- **그래서 이건 설계 순서 문제다.** 「이 타입이 뒷정리를 하나」를 **먼저** 정하고 `Copy` 를 결정한다.

### 3. ★ `clone()` 이 항상 깊다고 읽는다

- **`Rc::clone` 은 카운트만 올린다.** 같은 데이터를 두 이름이 본다.
- `Arc`·`Rc` 를 `.clone()` 으로 부르면 **의도가 안 보인다** — 관용구는 `Rc::clone(&r)` 쪽이다(같은 동작, 읽는 사람이 구분한다).
- **얕은지 깊은지는 타입 문서를 봐야 안다.** 글자만으로는 안 갈린다.

### 4. `derive(Clone)` 이 공짜라고 본다

- 제네릭 타입에서는 **`T: Clone` 경계가 따라붙는다**(실측 E0599의 `introduced in this derive macro`).
- 필드가 `Rc<T>`·`&T` 처럼 **`T` 와 무관하게 `Clone`** 인 경우 그 경계는 **군더더기**다.
- 라이브러리 경계에서는 손으로 `impl` 하는 쪽이 낫다.

### 5. ★ 해제 순서를 지역 변수 감각으로 읽는다

- **지역 변수는 역순, 필드는 선언 순** — 방향이 반대다. 락을 필드로 묶어 둔 구조체에서 이 차이가 드러난다.
- **`Drop` 을 단 구조체는 본체가 먼저**다. 필드가 아직 살아 있는 상태에서 내 정리 코드가 돈다.

### 6. `d.drop()` 으로 해제를 앞당기려 한다

- **E0040** 이다. `drop(d)` 를 쓴다.
- `drop(d)` 뒤에 `d` 를 쓰면 **E0382** — 08번의 다른 이동들과 **같은 번호**다.
- ★ **`Copy` 타입에 `drop()` 을 부르면 아무 일도 안 난다**(경고 `dropping_copy_types`).

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| `Copy` 는 `Clone` 을 상위 트레이트로 요구한다 | **언어**(std 선언) | E0277 `required by a bound in Copy` |
| `Copy` 아닌 필드가 있으면 `Copy` 를 못 만든다 | **언어** | **E0204** + `--explain` |
| `Copy` 와 `Drop` 은 함께 구현 못 한다 | **언어**(현재) | **E0184**. ★ `--explain` 이 `currently`·`for now` 라고 적는다 |
| 지역 변수는 **선언 역순** 해제 | **언어** | Reference(Destructors) · 실측 |
| 구조체 필드·튜플·배열 원소는 **선언 순** 해제 | **언어** | Reference(Destructors) · 실측 |
| `Drop` 구현체는 **본체 먼저, 필드 나중** | **언어** | Reference(Destructors) · 실측 |
| `Drop::drop` 을 직접 못 부른다 | **언어** | **E0040** |
| `drop(x)` 이 그냥 값을 먹는 함수인 것 | **언어**(std API) | 빈 몸통 함수로 재현됨 |
| **`Vec::clone` 이 버퍼를 새로 할당하는 것** | **std 계약** | 주소 실측. `Clone` 트레이트 자체는 깊이를 강제하지 않는다 |
| **`Rc::clone` 이 카운트만 올리는 것** | **std 계약** | `strong_count` 1→2→1 실측. 정본은 [목록의 **41번 주제**](../41-rc-arc-shared-ownership-and-weak-cycles/) |
| **주소 절댓값**(`0x6076...`) | **런타임 ASLR** | 실행마다 바뀐다. 근거는 「같은가/다른가」뿐 |
| **`String`·`Vec` 의 크기 24바이트** | **플랫폼**(64비트) | `size_of` 실측. 포인터 폭이 다르면 달라진다 |
| **`D` 의 크기 16바이트** | **구현**(필드 배치) | `&'static str` 이 16바이트라서다. 배치 규칙은 `repr` 의 자유 |
| **`dropping_copy_types` 가 경고인 것** | **린트 설정** | `-D warnings` 로 에러가 된다 |
| **에러·경고의 문구와 `help` 제안** | **rustc 구현** | 버전이 오르면 바뀐다 — **에러 번호**가 더 안정적이다 |

★ **`Clone` 트레이트 자체는 「깊은 복사」를 강제하지 않는다.** 문서가 요구하는 것은
「`a.clone()` 이 `a` 와 **같은 값**을 주는 것」 정도이고, **무엇을 공유할지는 구현이 정한다.**
`Rc` 가 그 자유를 쓴 대표 사례다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 이유 |
|---|---|---|
| 작은 값 타입(좌표·ID·플래그) | `#[derive(Clone, Copy)]` | 넘겨도 안 잃어 호출부가 조용해진다 |
| 힙을 쥔 타입 | `Clone` 만 | `Copy` 는 애초에 못 붙는다(E0204) |
| 정리할 자원이 있다 | `impl Drop` — **`Copy` 는 포기** | 둘은 공존 불가(E0184) |
| 사본이 **따로 살아야** 한다 | `.clone()` | 원본과 남남이 되는 것이 목적일 때 |
| **같은 데이터를 여럿이 본다** | `Rc::clone`/`Arc::clone` | 카운트만 오른다([목록의 **41번 주제**](../41-rc-arc-shared-ownership-and-weak-cycles/)) |
| 해제를 앞당긴다 | `drop(x)` — `x.drop()` 아니다 | E0040 |
| 해제 시점을 **관찰**한다 | `impl Drop` + `println!` | 유일한 창. 단 `Copy` 타입에는 못 단다 |
| 제네릭 타입에 `Clone` 을 연다 | 손으로 `impl Clone` | `derive` 는 `T: Clone` 을 군더더기로 붙인다 |

판단 규칙 두 줄.

- **「이 타입이 뒷정리를 하나」를 먼저 정한다.** 그 답이 `Copy` 여부를 결정한다.
- **`clone()` 을 쓰기 전에 「무엇이 복제되나」를 타입 문서로 확인한다.** 글자는 같아도 하는 일이 다르다.

## 핵심 문장

- **`Copy` 는 `Clone` 의 부분집합**이다 — `pub trait Copy: Clone` 이라 `Clone` 없이는 못 붙인다(E0277).
- **필드 하나라도 `Copy` 가 아니면 구조체도 `Copy` 가 못 된다**(E0204). `&T` 는 되고 `&mut T` 는 안 된다.
- ★ **`Copy` 와 `Drop` 은 함께 못 온다**(E0184) — 둘 다면 같은 자원에 소멸자가 두 번 불린다.\
  뒤집으면 **`Copy` 타입에는 소멸자가 있을 수 없다**.
- **`clone()` 의 깊이는 타입이 정한다** — `Vec` 은 버퍼를 새로 잡고, `Rc` 는 카운트만 올린다.
- **`derive(Clone)` 은 파라미터마다 `T: Clone` 을 붙인다** — 필요 없을 때도 붙는다.
- ★ **해제 순서는 지역 변수가 역순, 구조체 필드·튜플·`Vec` 원소가 선언 순**이다. 방향이 반대다.
- **`Drop` 을 단 구조체는 본체 먼저, 필드 나중** — 소멸자가 필드를 읽을 수 있어야 하기 때문이다.
- **`Drop::drop` 은 직접 못 부른다**(E0040). `drop(x)` 는 **그냥 값을 먹는 빈 몸통 함수**다.
- **크기는 `Copy` 판정과 무관하다** — `[i32; 3]`(12B)은 `Copy` 고 `Vec<i32>`(24B)는 아니다.

## 관련 자료

- [`../README.md`](../README.md) — Rust 문법·API 주제 목록(이 주제는 09번)
- [**08번 주제**](../08-ownership-and-move/)(소유권과 이동) — ★ **직접 선행**. `impl Drop` + `println!` 창을 거기서 세웠고,\
  「해제는 정확히 한 번」이 여기 E0184 의 이유가 된다. **그쪽은 이동이 무엇인가, 여기는 이동 안 하는 타입과 해제 순서**다
- [**02번 주제**](../02-bindings-mut-and-shadowing/)(바인딩·섀도잉) — 섀도잉이 해제를 앞당기지 않는다는 실측은 거기
- [**05번 주제**](../05-control-flow-loops-and-labels/)(제어 흐름) — `for x in v` 가 무엇을 주나
- [**07번 주제**](../07-const-static-and-const-fn/)(`const`·`static`) — `&'static str` 이 어디 사는가
- [**10번 주제**](../10-borrowing-and-aliasing-rules/)(빌림 `&`·`&mut`) — **`&T` 가 `Copy` 이고 `&mut T` 는 아닌 것**의 정본
- [`../../../../memory-management/`](../../../../memory-management/) — 할당·해제·참조 카운팅의 **일반론**은 거기,\
  **여기는 Rust 가 그 시점을 어느 줄로 정하나**까지
- [목록의 **27번 주제**](../27-derive-macros-debug-clone-partialeq-default-hash/)(`derive` 매크로) — 어떤 파생이 어떤 제약을 거는지의 정본
- [목록의 **41번 주제**](../41-rc-arc-shared-ownership-and-weak-cycles/)(`Rc`/`Arc`) — `Rc::clone` 이 카운트만 올리는 것의 정본. 여기서는 **현상만**
- [목록의 **44번 주제**](../44-drop-mem-drop-replace-and-take/)(`Drop`·`mem::replace`/`take`) — 자원 타입을 직접 설계하는 쪽
- [목록의 **26번 주제**](../26-orphan-rule-and-newtype/)(고아 규칙) — 남의 타입에 `Drop` 을 못 다는 이유

## 용어 풀이

- **`Copy`** — 비트 복사만으로 두 값이 각자 유효해지는 타입에 붙는 표식 트레이트.
- **표식 트레이트(marker trait)** — 메서드가 없고 「이 타입은 이렇다」만 말하는 트레이트.
- **`Clone`** — 사본을 만드는 법을 정의한 트레이트. `clone()` 은 **명시적 호출**이다.
- **상위 트레이트(supertrait)** — `trait Copy: Clone` 의 `Clone` 처럼, 구현하려면 먼저 있어야 하는 트레이트.
- **`Drop`** — 해제 순간에 실행될 코드를 적는 트레이트. `derive` 가 없다.
- **소멸자(destructor)** — `Drop::drop` + 필드들의 재귀적 해제를 합친 것.
- **얕은 복사(shallow copy)** — 포인터만 베껴 같은 데이터를 공유하는 것. `Rc::clone` 쪽.
- **깊은 복사(deep copy)** — 가리키는 데이터까지 새로 만드는 것. `Vec::clone` 쪽.
- **참조 카운트(reference count)** — 그 데이터를 몇 명이 보고 있나를 세는 정수. `Rc::strong_count`.
- **double free** — 같은 자원을 두 번 반납하는 버그. E0184 가 막는 것이 이것이다.
- **`dropping_copy_types`** — `Copy` 값에 `drop()` 을 부르면 경고하는 린트.

---

## 더 들어가면

- **`Copy` 가 「싸다」는 뜻은 아니다.** `[u8; 4096]` 도 `Copy` 다 — 4KB 를 통째로 베낀다.\
  `Copy` 가 말하는 것은 「**비트 복사가 의미상 옳다**」뿐이고, **비용은 별개**다.
- ★ **`Clone` 은 `Copy` 타입에도 의미가 있다.** `Copy` 가 `Clone` 을 요구하므로 `i32`·`[i32; 3]` 같은 타입도\
  `clone()` 을 가진다 — 제네릭 코드가 `T: Clone` 만 요구해도 `Copy` 타입이 통과하는 이유다.
- **`Drop` 은 패닉 중에도 불린다**(unwind 중 정리). 그래서 `drop` 안에서 다시 패닉하면 프로그램이 죽는다.\
  자세한 것은 [목록의 **23번 주제**](../23-panic-vs-result/)(`panic!` 대 `Result`) 쪽이다.
- ★ **`mem::forget` 은 해제를 건너뛴다** — 안전한 함수인데도 소멸자를 안 부른다.\
  「메모리 누수는 Rust 의 안전성 보장 대상이 아니다」는 자리다. [목록의 **44번 주제**](../44-drop-mem-drop-replace-and-take/).
- **필드 해제 순서를 바꾸려면 필드 선언 순서를 바꾼다.** 언어가 따로 지정 문법을 주지 않는다.\
  락 가드 두 개를 순서대로 풀어야 하면 그 순서가 **구조체 정의에 박힌다**.
- ★ **`Copy` 를 뗐을 때 깨지는 곳이 많다는 것이 곧 설계 신호**다 — 값이 여기저기 복제돼 흩어져 있었다는 뜻이다.
