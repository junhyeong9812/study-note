# rust/syntax/27 — `derive` 매크로(`Debug`·`Clone`·`PartialEq`·`Default`·`Hash`) — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 받은 것이다(한 블록만 `--emit=mir` — 배너에 적혀 있다).\
> ★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
> ★★ **`--edition` 을 빼면 에디션 2015 다.** 이 갈래에서 그것은 「안 돌려 본 것」과 같다.\
> ★★ **외부 크레이트를 하나도 쓰지 않았다**(네트워크 없음). **`cargo expand` 도 안 썼다**(7번 답).\
> 실험 파일 이름은 전부 **`ex.rs`** 로 고정했고 **진단의 줄 번호는 그 파일 기준**이다.\
> ★ `rustc --explain E0277` · `E0369` · `E0407` · `E0599` · `E0665` 는 **확인용으로만 열었고 본문에 옮기지 않았다.**
> ★★ `HashMap` 을 쓰는 블록은 **씨앗을 고정하고 키로 직접 읽는다** — 순회 순서는 보장이 없다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ 다섯이 각각 하나씩을 준다 — `Hash` 만 혼자 못 선다

**출력.**

```text
===== 소스: ex.rs =====
// ex.rs
// 다섯 derive 가 무엇을 만드나 — 하나씩 실제로 써 본다
use std::collections::HashMap;
use std::collections::hash_map::DefaultHasher;
use std::hash::BuildHasherDefault;

#[derive(Debug, Clone, PartialEq, Eq, Default, Hash)]
struct Key {
    id: u32,
    name: String,
}

fn main() {
    let k = Key { id: 7, name: String::from("가") };

    println!("Debug      {:?}", k);
    let c = k.clone();
    println!("Clone      {:?} · 원본도 살아 있다 {:?}", c, k);
    println!("PartialEq  {} {}", k == c, k == Key { id: 8, name: String::from("가") });
    println!("Default    {:?}", Key::default());

    // Hash — HashMap 키로 쓸 수 있다. ★ 순회하지 않고 키로 직접 읽는다
    let mut m: HashMap<Key, &str, BuildHasherDefault<DefaultHasher>> = HashMap::default();
    m.insert(k.clone(), "값");
    println!("Hash       {:?} · len {}", m.get(&c), m.len());
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
Debug      Key { id: 7, name: "가" }
Clone      Key { id: 7, name: "가" } · 원본도 살아 있다 Key { id: 7, name: "가" }
PartialEq  true false
Default    Key { id: 0, name: "" }
Hash       Some("값") · len 1
(종료 코드 0)
```

**왜 그런가**

- **`Debug`** → `{:?}` 로 찍히는 것. 형식은 **타입 이름 + 중괄호 + `필드이름: 값`** 이고,
  각 필드는 **자기 `Debug`** 로 찍힌다. 그래서 `String` 은 `` "가" `` 처럼 **따옴표째** 나온다
  (`Display` 였다면 따옴표가 없다).
- **`Clone`** → `.clone()`. 원본 `k` 가 **그대로 살아 있다**(같은 줄에서 둘을 함께 찍었다). 이동이 아니다.
- **`PartialEq`** → `==`. 같은 값이면 `true`, `id` 하나만 달라도 `false` 다.
- **`Default`** → `Key::default()`. 필드마다 그 타입의 기본값을 부르므로 `` Key { id: 0, name: "" } `` 다.
- **`Hash`** → `HashMap` 키가 되는 것. `` Some("값") `` 이 나왔다.
- ★★ **`Eq` 가 끼어 있는 이유** — `HashMap` 의 키 경계가 `` K: Hash + Eq `` 이기 때문이다.
  **빼면 마지막 두 줄(`insert`·`get`)이 E0599 로 깨진다** — 3번 답의 다섯째 행이 바로 그 진단이다.
  ★ `Eq` 는 **메서드가 없는 표식**이라 파생해도 코드가 안 생긴다. 그 이야기는
  [**28번 주제**](../28-partialeq-eq-partialord-ord-and-hash-contracts/)가 정본이다.
- ★ **순회하지 않고 `m.get(&c)` 로 읽었고 씨앗도 고정했다.** `HashMap` 의 순회 순서는 보장이 없다.

### 2. ★ 같은 구현이 두 형식을 낸다

**출력.**

```text
===== 소스: ex.rs =====
// ex.rs
// Debug 의 두 얼굴 — {:?} 와 {:#?}
#[derive(Debug)]
struct Inner {
    x: i32,
    tags: Vec<&'static str>,
}

#[derive(Debug)]
struct Unit;

#[derive(Debug)]
struct Tup(i32, i32);

#[derive(Debug)]
enum Shape {
    Dot,
    Line(i32),
    Box { w: i32, h: i32 },
}

#[derive(Debug)]
struct Outer {
    name: String,
    inner: Inner,
    unit: Unit,
    tup: Tup,
    shapes: Vec<Shape>,
}

fn main() {
    let o = Outer {
        name: String::from("가"),
        inner: Inner { x: 1, tags: vec!["a", "b"] },
        unit: Unit,
        tup: Tup(3, 4),
        shapes: vec![Shape::Dot, Shape::Line(5), Shape::Box { w: 6, h: 7 }],
    };
    println!("--- {{:?}} ---");
    println!("{:?}", o);
    println!("--- {{:#?}} ---");
    println!("{:#?}", o);
}
===== rustc --edition 2021 ex.rs -o ex =====
warning: fields `x` and `tags` are never read
 --> ex.rs:5:5
  |
4 | struct Inner {
  |        ----- fields in this struct
5 |     x: i32,
  |     ^
6 |     tags: Vec<&'static str>,
  |     ^^^^
  |
  = note: `Inner` has a derived impl for the trait `Debug`, but this is intentionally ignored during dead code analysis
  = note: `#[warn(dead_code)]` (part of `#[warn(unused)]`) on by default

warning: fields `0` and `1` are never read
  --> ex.rs:13:12
   |
13 | struct Tup(i32, i32);
   |        --- ^^^  ^^^
   |        |
   |        fields in this struct
   |
   = help: consider removing these fields
   = note: `Tup` has a derived impl for the trait `Debug`, but this is intentionally ignored during dead code analysis

warning: field `0` is never read
  --> ex.rs:18:10
   |
18 |     Line(i32),
   |     ---- ^^^
   |     |
   |     field in this variant
   |
   = note: `Shape` has a derived impl for the trait `Debug`, but this is intentionally ignored during dead code analysis
help: consider changing the field to be of unit type to suppress this warning while preserving the field numbering, or remove the field
   |
18 -     Line(i32),
18 +     Line(()),
   |

warning: fields `w` and `h` are never read
  --> ex.rs:19:11
   |
19 |     Box { w: i32, h: i32 },
   |     ---   ^       ^
   |     |
   |     fields in this variant
   |
   = note: `Shape` has a derived impl for the trait `Debug`, but this is intentionally ignored during dead code analysis

warning: fields `name`, `inner`, `unit`, `tup`, and `shapes` are never read
  --> ex.rs:24:5
   |
23 | struct Outer {
   |        ----- fields in this struct
24 |     name: String,
   |     ^^^^
25 |     inner: Inner,
   |     ^^^^^
26 |     unit: Unit,
   |     ^^^^
27 |     tup: Tup,
   |     ^^^
28 |     shapes: Vec<Shape>,
   |     ^^^^^^
   |
   = note: `Outer` has a derived impl for the trait `Debug`, but this is intentionally ignored during dead code analysis

warning: 5 warnings emitted
===== ./ex =====
--- {:?} ---
Outer { name: "가", inner: Inner { x: 1, tags: ["a", "b"] }, unit: Unit, tup: Tup(3, 4), shapes: [Dot, Line(5), Box { w: 6, h: 7 }] }
--- {:#?} ---
Outer {
    name: "가",
    inner: Inner {
        x: 1,
        tags: [
            "a",
            "b",
        ],
    },
    unit: Unit,
    tup: Tup(
        3,
        4,
    ),
    shapes: [
        Dot,
        Line(
            5,
        ),
        Box {
            w: 6,
            h: 7,
        },
    ],
}
(종료 코드 0)
```

**왜 그런가**

- ★ **`Debug` 구현은 하나뿐이고 `{:#?}` 의 `#` 는 포매터의 플래그**다(대체 형식).
  파생된 코드가 그 플래그를 보고 **한 줄로 찍을지 여러 줄로 찍을지** 가른다. 구현이 둘이 아니다.
- **네 모양이 각각 다르다.**
  - **이름 있는 구조체** — `` Inner { x: 1, tags: ["a", "b"] } ``
  - **유닛 구조체** — `Unit` (괄호도 중괄호도 없다)
  - **튜플 구조체** — `Tup(3, 4)` (이름이 없으니 위치만)
  - **enum** — `Dot` · `Line(5)` · `` Box { w: 6, h: 7 } `` — **변형마다 그 변형의 모양**을 따른다
- **들여쓰기는 4칸**이고 **마지막 항목 뒤에도 쉼표가 붙는다**(`` "b", `` 다음 줄이 `]`).
  중첩되면 그만큼 더 들어간다(`shapes` 안의 `` Box { `` 는 8칸, 그 안의 `w: 6,` 은 12칸).
- ★ **파싱해서 쓰면 안 된다.** std 는 `Debug` 출력 형식을 **안정 보장으로 약속하지 않는다.**
  판이 바뀌면 바뀔 수 있는 자리다 — **로그·디버깅용**이다.

### 3. ★★★ 에러 번호가 셋 · 「필드가 못 따라가는」 것은 또 다른 자리

**출력.**

```text
===== 소스: ex.rs =====
// ex.rs
// derive 를 하나도 안 붙이면 — 다섯 자리가 각각 다른 에러로 막힌다
use std::collections::HashMap;

struct Bare {
    n: i32,
}

fn dup<T: Clone>(x: &T) -> T {
    x.clone()
}

fn main() {
    let a = Bare { n: 1 };
    println!("{:?}", a);            // Debug
    let _b = dup(&a);               // Clone
    println!("{}", a == a);         // PartialEq
    let _d = Bare::default();       // Default
    let mut m: HashMap<Bare, i32> = HashMap::new();
    m.insert(Bare { n: a.n }, 1);   // Hash + Eq
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0277]: `Bare` doesn't implement `Debug`
  --> ex.rs:15:22
   |
15 |     println!("{:?}", a);            // Debug
   |               ----   ^ `Bare` cannot be formatted using `{:?}` because it doesn't implement `Debug`
   |               |
   |               required by this formatting parameter
   |
   = help: the trait `Debug` is not implemented for `Bare`
   = note: add `#[derive(Debug)]` to `Bare` or manually `impl Debug for Bare`
   = note: this error originates in the macro `$crate::format_args_nl` which comes from the expansion of the macro `println` (in Nightly builds, run with -Z macro-backtrace for more info)
help: consider annotating `Bare` with `#[derive(Debug)]`
   |
 5 + #[derive(Debug)]
 6 | struct Bare {
   |

error[E0277]: the trait bound `Bare: Clone` is not satisfied
  --> ex.rs:16:18
   |
16 |     let _b = dup(&a);               // Clone
   |              --- ^^ the trait `Clone` is not implemented for `Bare`
   |              |
   |              required by a bound introduced by this call
   |
note: required by a bound in `dup`
  --> ex.rs:9:11
   |
 9 | fn dup<T: Clone>(x: &T) -> T {
   |           ^^^^^ required by this bound in `dup`
help: consider annotating `Bare` with `#[derive(Clone)]`
   |
 5 + #[derive(Clone)]
 6 | struct Bare {
   |

error[E0369]: binary operation `==` cannot be applied to type `Bare`
  --> ex.rs:17:22
   |
17 |     println!("{}", a == a);         // PartialEq
   |                    - ^^ - Bare
   |                    |
   |                    Bare
   |
note: an implementation of `PartialEq` might be missing for `Bare`
  --> ex.rs:5:1
   |
 5 | struct Bare {
   | ^^^^^^^^^^^ must implement `PartialEq`
help: consider annotating `Bare` with `#[derive(PartialEq)]`
   |
 5 + #[derive(PartialEq)]
 6 | struct Bare {
   |

error[E0599]: no function or associated item named `default` found for struct `Bare` in the current scope
  --> ex.rs:18:20
   |
 5 | struct Bare {
   | ----------- function or associated item `default` not found for this struct
...
18 |     let _d = Bare::default();       // Default
   |                    ^^^^^^^ function or associated item not found in `Bare`
   |
   = help: items from traits can only be used if the trait is implemented and in scope
   = note: the following trait defines an item `default`, perhaps you need to implement it:
           candidate #1: `Default`

error[E0599]: the method `insert` exists for struct `HashMap<Bare, i32>`, but its trait bounds were not satisfied
  --> ex.rs:20:7
   |
 5 | struct Bare {
   | ----------- doesn't satisfy `Bare: Eq` or `Bare: Hash`
...
20 |     m.insert(Bare { n: a.n }, 1);   // Hash + Eq
   |       ^^^^^^
   |
   = note: the following trait bounds were not satisfied:
           `Bare: Eq`
           `Bare: Hash`
help: consider annotating `Bare` with `#[derive(Eq, Hash, PartialEq)]`
   |
 5 + #[derive(Eq, Hash, PartialEq)]
 6 | struct Bare {
   |

error: aborting due to 5 previous errors

Some errors have detailed explanations: E0277, E0369, E0599.
For more information about an error, try `rustc --explain E0277`.
(종료 코드 1)
```

**왜 그런가**

- **앞 소스의 에러는 5건**이고 **번호는 세 가지**(E0277 · E0369 · E0599)다.

| 무엇을 하려 했나 | 에러 | 왜 그 번호인가 |
|---|---|---|
| `{:?}` 로 찍기 | **E0277** | 포매팅 인자가 `` Debug `` 경계를 요구한다 |
| `T: Clone` 경계에 넘기기 | **E0277** | 함수의 **경계**가 안 맞는다 |
| `==` | **E0369** | ★ **연산자** 전용 진단이다 |
| `Bare::default()` | **E0599** | ★ **연관 함수**를 못 찾았다 |
| `HashMap` 키로 넣기 | **E0599** | ★ **메서드는 있는데 경계**가 안 맞는다 |

- ★★ **갈림의 축은** 「**닿는 문법**」이다 — **연산자면 E0369**, **이름으로 찾는 것(메서드·연관 함수)이면 E0599**,
  **경계 검사면 E0277**. 「트레이트가 없다」는 사실은 다섯 다 같은데 진단이 셋으로 갈린다.
- ★ **`PartialEq` 까지 들어가는 `help:` 는 다섯째**다 —
  `` consider annotating `Bare` with `#[derive(Eq, Hash, PartialEq)]` ``.
  `Eq` 가 `PartialEq` 를 슈퍼트레이트로 요구하므로 **셋을 함께** 세어 준다.
- ★ **`Default` 만 `help:` 가 아니라 후보 목록**으로 답한다(`` candidate #1: `Default` ``).
  이름으로 찾다 실패한 자리라 진단이 「그 이름을 가진 트레이트」를 훑은 것이다.
- **`Debug` 쪽에만 `= note:` 가 하나 더** 붙는다 — `` this error originates in the macro `$crate::format_args_nl` … ``.
  `println!` 을 거쳤기 때문이고, 다른 넷은 매크로를 안 거친다.

**뒤 소스 — 붙였는데 필드가 못 따라가는 자리.**

```text
===== 소스: ex.rs =====
// ex.rs
// derive 는 필드에 그 트레이트를 요구한다 — f64 는 Hash 도 Eq 도 아니다
#[derive(PartialEq, Eq, Hash)]
struct Point {
    x: i32,
    ratio: f64,
}

fn main() {
    let a = Point { x: 1, ratio: 0.5 };
    let b = Point { x: 1, ratio: 0.5 };
    println!("{}", a == b);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0277]: the trait bound `f64: Eq` is not satisfied
 --> ex.rs:6:5
  |
3 | #[derive(PartialEq, Eq, Hash)]
  |                     -- in this derive macro expansion
...
6 |     ratio: f64,
  |     ^^^^^^^^^^ the trait `Eq` is not implemented for `f64`
  |
  = help: the following other types implement trait `Eq`:
            i128
            i16
            i32
            i64
            i8
            isize
            u128
            u16
          and 4 others
note: required by a bound in `AssertParamIsEq`
 --> /rustc/ded5c06cf21d2b93bffd5d884aa6e96934ee4234/library/core/src/cmp.rs:367:1

error[E0277]: the trait bound `f64: Hash` is not satisfied
 --> ex.rs:6:5
  |
3 | #[derive(PartialEq, Eq, Hash)]
  |                         ---- in this derive macro expansion
...
6 |     ratio: f64,
  |     ^^^^^^^^^^ the trait `Hash` is not implemented for `f64`
  |
  = help: the following other types implement trait `Hash`:
            i128
            i16
            i32
            i64
            i8
            isize
            u128
            u16
          and 4 others

error: aborting due to 2 previous errors

For more information about this error, try `rustc --explain E0277`.
(종료 코드 1)
```

- **`PartialEq` 는 통과하고 `Eq`·`Hash` 만 막힌다.** `f64` 는 `PartialEq` 는 구현하지만
  **`Eq` 도 `Hash` 도 구현하지 않기** 때문이다. ★ **이 셋이 갈리는 첫 자리**이고, 이유는 28번 주제가 정본이다.
- ★★★ **진단이 `derive` 안을 가리킨다** — `` #[derive(PartialEq, Eq, Hash)] `` 줄 아래에
  `` -- in this derive macro expansion `` 이 **`Eq` 쪽과 `Hash` 쪽에 각각** 그어지고,
  밑줄은 **문제가 된 필드(`ratio: f64`)** 를 짚는다. **어느 `derive` 가 어느 필드에서 막혔는지**가 한눈에 나온다.
- ★★ **`` AssertParamIsEq `` 는 `derive(Eq)` 가 만들어 넣는 내부 타입**이다.
  `Eq` 는 **메서드가 없는 표식**이라 「필드가 정말 `Eq` 인가」를 검사할 자리가 따로 필요했고,
  파생 코드가 그 이름의 보조 타입을 하나 만들어 경계를 건다. `` note: required by a bound in `AssertParamIsEq` `` 가
  **생성 코드의 조각을 이름으로 흘린 것**이다(7번 답의 셋째 창).
- `Hash` 쪽에는 그 note 가 없다 — `Hash` 는 진짜 메서드가 있어서 보조 타입이 필요 없다.

### 4. ★★★ `PhantomData<T>` 인데 `T: Clone` 이 필요해진다

**출력.**

```text
===== 소스: ex.rs =====
// ex.rs
// derive 가 붙이는 경계가 과하다 — PhantomData<T> 인데 T: Clone 을 요구한다
use std::marker::PhantomData;

#[derive(Clone)]
struct Tagged<T> {
    n: i64,
    p: PhantomData<T>,
}

struct NotClone; // Clone 이 아니다

fn dup<T: Clone>(x: &T) -> T {
    x.clone()
}

fn main() {
    let a: Tagged<NotClone> = Tagged { n: 1, p: PhantomData };
    let b = a.clone();  // ① 메서드로 바로
    let c = dup(&a);    // ② T: Clone 경계를 통해
    println!("{} {}", b.n, c.n);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0599]: the method `clone` exists for struct `Tagged<NotClone>`, but its trait bounds were not satisfied
  --> ex.rs:19:15
   |
 6 | struct Tagged<T> {
   | ---------------- method `clone` not found for this struct because it doesn't satisfy `Tagged<NotClone>: Clone`
...
11 | struct NotClone; // Clone 이 아니다
   | --------------- doesn't satisfy `NotClone: Clone`
...
19 |     let b = a.clone();  // ① 메서드로 바로
   |               ^^^^^ method cannot be called on `Tagged<NotClone>` due to unsatisfied trait bounds
   |
note: trait bound `NotClone: Clone` was not satisfied
  --> ex.rs:5:10
   |
 5 | #[derive(Clone)]
   |          ^^^^^ unsatisfied trait bound introduced in this `derive` macro
help: consider annotating `NotClone` with `#[derive(Clone)]`
   |
11 + #[derive(Clone)]
12 | struct NotClone; // Clone 이 아니다
   |

error[E0277]: the trait bound `NotClone: Clone` is not satisfied
  --> ex.rs:20:17
   |
20 |     let c = dup(&a);    // ② T: Clone 경계를 통해
   |             --- ^^ the trait `Clone` is not implemented for `NotClone`
   |             |
   |             required by a bound introduced by this call
   |
note: required for `Tagged<NotClone>` to implement `Clone`
  --> ex.rs:5:10
   |
 5 | #[derive(Clone)]
   |          ^^^^^ unsatisfied trait bound introduced in this `derive` macro
note: required by a bound in `dup`
  --> ex.rs:13:11
   |
13 | fn dup<T: Clone>(x: &T) -> T {
   |           ^^^^^ required by this bound in `dup`
help: consider annotating `NotClone` with `#[derive(Clone)]`
   |
11 + #[derive(Clone)]
12 | struct NotClone; // Clone 이 아니다
   |

error: aborting due to 2 previous errors

Some errors have detailed explanations: E0277, E0599.
For more information about an error, try `rustc --explain E0277`.
(종료 코드 1)
```

**왜 그런가**

- **컴파일 안 되고 에러는 2건**이다. **번호가 다르다** — **E0599** 와 **E0277**.
- ★★ **번호를 가른 것은** 「**어떻게 닿았나**」다.
  - `a.clone()` 처럼 **메서드로 바로** 부르면 **E0599** —
    `` the method `clone` exists for struct `Tagged<NotClone>`, but its trait bounds were not satisfied ``.
    「없다」가 아니라 「**있는데 조건이 안 맞는다**」고 말하고,
    `` doesn't satisfy `NotClone: Clone` `` 로 **범인까지** 짚는다.
  - `dup(&a)` 처럼 **`T: Clone` 경계를 통과시키려** 하면 **E0277** —
    `` the trait bound `NotClone: Clone` is not satisfied `` 에
    `` note: required for `Tagged<NotClone>` to implement `Clone` `` 가 붙는다.
- ★★★ **두 진단 모두 `#[derive(Clone)]` 줄을 가리키며 같은 말을 한다** —
  `` unsatisfied trait bound introduced in this `derive` macro ``.
  「**이 경계는 네가 쓴 게 아니라 `derive` 가 붙인 것이다**」라고 컴파일러가 직접 말해 준다.
  ★ 이것이 **생성 결과를 보는 둘째 창**이다(7번 답).
- ★★★ **왜 과한가** — `Tagged<T>` 의 필드는 `i64` 와 `PhantomData<T>` 뿐이고
  `PhantomData<T>` 는 **`T` 값을 하나도 안 들고 크기도 0** 이다. 복제에 `T: Clone` 이 **필요하지 않다.**
  그런데 `derive` 는 「**제네릭 파라미터마다 같은 경계를 붙인다**」는 한 가지 규칙만 따르므로 붙인다.
- ★ `help:` 의 `` consider annotating `NotClone` with `#[derive(Clone)]` `` 는 **답이지만 옳은 답은 아니다** —
  `NotClone` 이 남의 타입이면 못 고치고, 애초에 **필요 없는 조건**이다.

**뒤 소스 — 한 가지만 다르다.**

```text
===== 소스: ex.rs =====
// ex.rs
// 손으로 구현하면 그 경계가 안 붙는다 — 같은 타입, 같은 쓰임
use std::marker::PhantomData;

struct Tagged<T> {
    n: i64,
    p: PhantomData<T>,
}

impl<T> Clone for Tagged<T> {
    // ★ where T: Clone 이 없다
    fn clone(&self) -> Self {
        Tagged { n: self.n, p: PhantomData }
    }
}

struct NotClone; // 여전히 Clone 이 아니다

fn dup<T: Clone>(x: &T) -> T {
    x.clone()
}

fn main() {
    let a: Tagged<NotClone> = Tagged { n: 1, p: PhantomData };
    let b = a.clone();
    let c = dup(&a);
    println!("메서드로 {} · 경계로 {}", b.n, c.n);
    println!("크기 Tagged<NotClone> {} · i64 {}",
             std::mem::size_of::<Tagged<NotClone>>(),
             std::mem::size_of::<i64>());
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
메서드로 1 · 경계로 1
크기 Tagged<NotClone> 8 · i64 8
(종료 코드 0)
```

- **다른 것은 `impl<T> Clone for Tagged<T>` 에 `where T: Clone` 이 없다는 것 하나뿐**이다.
  타입도 쓰임도 같은데 **둘 다 통과한다**(메서드로도, 경계로도).
- ★★ **그래서 판별 기준이 선다** — **타입 파라미터가 필드에 값으로 안 들어 있으면 `derive` 의 경계는 과하다.**
  `PhantomData<T>` · `fn(T) -> T` 같은 표식·함수 포인터 필드가 그 자리다.
- **크기는 8바이트로 `i64` 와 같다.** `PhantomData<T>` 가 자리를 안 차지한다
  (★ 0 크기 타입인 것은 언어 보장이고, **구조체 전체 배치**는 이 판의 관찰이다).
- ★ 대가는 **손품**이다 — 필드가 늘면 `clone` 을 손으로 고쳐야 하고,
  **잊으면 컴파일은 되고 값만 안 따라온다**(9번 답).

### 5. ★★ 3줄 · 1줄 · 2줄 — 왼쪽부터 보고 멈춘다

**출력.**

```text
===== 소스: ex.rs =====
// ex.rs
// 같은 것을 동작으로도 — 필드 순서대로 보고 틀리면 거기서 멈춘다
// ★ 마커도 결과도 전부 표준 오류로 찍는다(섞이지 않게)
struct Probe(u8, &'static str);

impl PartialEq for Probe {
    fn eq(&self, other: &Self) -> bool {
        eprintln!("  비교: {}", self.1);
        self.0 == other.0
    }
}

#[derive(PartialEq)]
struct Row {
    first: Probe,
    second: Probe,
    third: Probe,
}

fn row(a: u8, b: u8, c: u8) -> Row {
    Row {
        first: Probe(a, "first"),
        second: Probe(b, "second"),
        third: Probe(c, "third"),
    }
}

fn main() {
    eprintln!("[1] 전부 같다");
    eprintln!("  결과 {}", row(1, 2, 3) == row(1, 2, 3));
    eprintln!("[2] 첫 필드부터 다르다");
    eprintln!("  결과 {}", row(9, 2, 3) == row(1, 2, 3));
    eprintln!("[3] 둘째 필드가 다르다");
    eprintln!("  결과 {}", row(1, 9, 3) == row(1, 2, 3));
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
[1] 전부 같다
  비교: first
  비교: second
  비교: third
  결과 true
[2] 첫 필드부터 다르다
  비교: first
  결과 false
[3] 둘째 필드가 다르다
  비교: first
  비교: second
  결과 false
(종료 코드 0)
```

**왜 그런가**

- **`[1]` 은 세 번, `[2]` 는 한 번, `[3]` 은 두 번** 비교한다(`결과` 줄은 따로다).
- ★★ **드러나는 성질은 둘이다.**
  ① **필드 선언 순서대로** 본다 — `first` → `second` → `third`.
  ② **틀리면 거기서 멈춘다**(단락) — `[2]` 에서 `second`·`third` 는 **아예 안 불린다.**
- ★ **마커를 `eprintln!` 로만 찍은 이유** — `println!`(표준 출력)과 섞으면
  **파이프·파일로 받을 때 순서가 갈린다.** 표준 오류는 버퍼링을 안 해 순서가 고정된다.
  「돌려 봤다」를 지켜도 **받아 적으면 재현이 안 되는** 사고가 여기서 난다.
- ★★ **바뀌는 것은 비용이지 뜻이 아니다.** `&&` 는 결합적이라 **결과는 순서와 무관**하다.
  다만 **비싼 필드(긴 `String`·`Vec`)를 앞에 두면 그만큼 자주 치른다** — 자주 갈리는 필드를 앞에 둔다.
  ★ [**28번 주제**](../28-partialeq-eq-partialord-ord-and-hash-contracts/)의 `derive(PartialOrd)` 에서는
  **순서가 뜻까지 정한다**(사전식) — 여기서 「순서는 비용뿐」을 외워 두면 거기서 틀린다.

### 6. ★★ enum 에는 답이 코드에 없다 — 그래서 되묻는다

**출력.**

```text
===== 소스: ex.rs =====
// ex.rs
// derive(Default) 는 enum 에서만 사람에게 묻는다 — 어느 변형이 기본인가
#[derive(Debug, Default)]
enum Mode {
    // ★ 아무 변형에도 #[default] 가 없다
    Fast,
    Slow,
}

#[derive(Debug, Default)]
enum Level {
    #[default]
    Named(u8), // ★ 유닛 변형이 아니다
    Other,
}

fn main() {
    println!("{:?} {:?}", Mode::default(), Level::default());
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0665]: `#[derive(Default)]` on enum with no `#[default]`
 --> ex.rs:3:17
  |
3 |   #[derive(Debug, Default)]
  |                   ^^^^^^^
4 | / enum Mode {
5 | |     // ★ 아무 변형에도 #[default] 가 없다
6 | |     Fast,
7 | |     Slow,
8 | | }
  | |_- this enum needs a unit variant marked with `#[default]`
  |
help: make this unit variant default by placing `#[default]` on it
  |
6 |     #[default] Fast,
  |     ++++++++++
help: make this unit variant default by placing `#[default]` on it
  |
7 |     #[default] Slow,
  |     ++++++++++

error: the `#[default]` attribute may only be used on unit enum variants
  --> ex.rs:13:5
   |
13 |     Named(u8), // ★ 유닛 변형이 아니다
   |     ^^^^^
   |
   = help: consider a manual implementation of `Default`

error: aborting due to 2 previous errors

For more information about this error, try `rustc --explain E0665`.
(종료 코드 1)
```

**왜 그런가**

- **에러는 2건**이고 **한 건은 번호가 없다.**
  - `` error[E0665]: `#[derive(Default)]` on enum with no `#[default]` `` — 번호가 있는 쪽.
    밑줄이 **enum 몸통 전체**에 그어지고 `` this enum needs a unit variant marked with `#[default]` `` 가 붙는다.
  - `` error: the `#[default]` attribute may only be used on unit enum variants `` — **번호가 없는 쪽.**
    `` = help: consider a manual implementation of `Default` `` 가 답을 준다.
    ★ 어트리뷰트 검사 단계에서 나는 에러라 코드가 안 붙었다.
- ★★ **구조체는 안 묻고 enum 은 묻는 이유** — 구조체의 기본값은 「**필드마다 그 타입의 기본값**」이라는
  답이 **한 가지뿐**이라 코드에서 유도된다. enum 은 **어느 변형인지가 코드 어디에도 없다** —
  `Fast` 도 `Slow` 도 똑같이 그럴듯하다. **사람만 아는 것**이라 `#[default]` 로 받는다.
- ★ **`help:` 가 변형마다 따로 나오는 것**(`Fast` 에 붙이는 안 · `Slow` 에 붙이는 안)이 그 증거다 —
  컴파일러가 **고를 수 없어서** 둘 다 내놓은 것이다.
- **`#[default]` 는 유닛 변형에만** 붙는다. `Named(u8)` 에 붙이면 **`u8` 값을 무엇으로 할지** 또 모르기 때문이다.

```text
===== 소스: ex.rs =====
// ex.rs
// 고쳐서 던지면 — #[default] 는 유닛 변형 하나에만 붙는다
#[derive(Debug, Default)]
enum Mode {
    Fast,
    #[default]
    Slow,
}

#[derive(Debug, Default)]
struct Config {
    name: String,   // ""
    retries: u32,   // 0
    ratio: f64,     // 0.0
    on: bool,       // false
    tags: Vec<u8>,  // []
    mode: Mode,     // ★ 필드 타입의 Default 를 그대로 부른다
    opt: Option<u8>,
}

fn main() {
    println!("변형 둘   {:?} {:?}", Mode::Fast, Mode::Slow);
    println!("기본 변형 {:?}", Mode::default());
    let c = Config::default();
    println!("구조체    {:?}", c);
    println!("필드마다  {:?} {} {} {} {:?} {:?} {:?}",
             c.name, c.retries, c.ratio, c.on, c.tags, c.mode, c.opt);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
변형 둘   Fast Slow
기본 변형 Slow
구조체    Config { name: "", retries: 0, ratio: 0.0, on: false, tags: [], mode: Slow, opt: None }
필드마다  "" 0 0 false [] Slow None
(종료 코드 0)
```

- **출력은 네 줄**이다. `Mode::default()` 가 **`Slow`**(내가 `#[default]` 를 붙인 쪽)이고,
  구조체는 필드마다 그 타입의 `default()` 를 부른다 — `` "" `` · `0` · `0.0` · `false` · `[]` · `Slow` · `None`.
- ★ **`Option<u8>` 은 `None`** 이다. **0 이라서가 아니라 `Option` 의 `Default` 가 `None` 이라서**다.
  `` Default `` 는 「0 으로 채운다」가 아니라 「**각 타입이 정한 기본값**」이다.
- ★ **`mode: Mode` 필드가 `Mode::default()` 를 부른다** — 파생이 **재귀적으로 이어진다.**

### 7. ★★ 셋은 보이고 하나는 「못 잰 것」이다

**출력.**

```text
===== 소스: ex.rs =====
// ex.rs
// cargo expand 없이 derive 가 만든 것을 보는 길 — 안정판 rustc 의 --emit=mir
#[derive(PartialEq)]
struct P {
    a: u8,
    b: u8,
}

fn main() {
    println!("{}", P { a: 1, b: 2 } == P { a: 1, b: 3 });
}
===== rustc --edition 2021 --emit=mir ex.rs -o ex.mir =====
===== sed -n '/^fn <impl at ex.rs/,/^}/p' ex.mir =====
fn <impl at ex.rs:3:10: 3:19>::eq(_1: &P, _2: &P) -> bool {
    debug self => _1;
    debug other => _2;
    let mut _0: bool;
    let mut _3: bool;
    let mut _4: u8;
    let mut _5: u8;
    let mut _6: u8;
    let mut _7: u8;

    bb0: {
        _4 = copy ((*_1).0: u8);
        _5 = copy ((*_2).0: u8);
        _3 = Eq(move _4, move _5);
        switchInt(move _3) -> [0: bb2, otherwise: bb1];
    }

    bb1: {
        _6 = copy ((*_1).1: u8);
        _7 = copy ((*_2).1: u8);
        _0 = Eq(move _6, move _7);
        goto -> bb3;
    }

    bb2: {
        _0 = const false;
        goto -> bb3;
    }

    bb3: {
        return;
    }
}
(종료 코드 0)
```

**왜 그런가**

- ★★★ **길이 있다 — 안정판 rustc 의 `--emit=mir`** 이다. `cargo expand`(외부 크레이트)도
  `-Zunpretty=expanded`(나이틀리)도 없이, **생성된 `eq` 의 몸통**이 그대로 나온다.
- **필드 순서와 단락을 이렇게 읽는다.**
  1. 시그니처가 `` fn <impl at ex.rs:3:10: 3:19>::eq(_1: &P, _2: &P) -> bool `` 이다 —
     **이름이 없고 `#[derive(PartialEq)]` 가 적힌 위치로 불린다.** 사람이 안 쓴 `impl` 이라는 뜻이다.
  2. `bb0` 이 **필드 0** 을 본다 — `` ((*_1).0: u8) `` 과 `` ((*_2).0: u8) `` 를 `Eq` 로 견준다.
  3. `` switchInt(move _3) -> [0: bb2, otherwise: bb1] `` — **0(거짓)이면 `bb2`**,
     그리고 `bb2` 는 `` _0 = const false `` 뿐이다. **필드 1 을 아예 안 본다** — 이것이 단락이다.
  4. 참이면 `bb1` 이 **필드 1** 을 보고 그 결과가 반환값이 된다.
- ★★★ **이것은 생성 소스 그 자체가 아니다.** MIR 은 **타입 검사 뒤의 중간 표현**이라
  `self.a == other.a && self.b == other.b` 라는 **글자**는 여기 없다.
  ★ 그래서 갈라 적는다 — **「무엇을 하는 코드인가」는 잰 것**이고,
  **「생성 소스 텍스트」는** 「**못 잰 것**」이다(도구가 없다 · 나이틀리 금지 · 네트워크 없음).
  ★ **「안 돌려 봤다」가 아니다** — 측정 수단 자체가 이 환경에 없다.
- ★ **진단 쪽에도 두 자리가 있다.**
  ① `` unsatisfied trait bound introduced in this `derive` macro `` — **생성된 경계**를 말해 준다(4번 답).
  ② `` note: required by a bound in `AssertParamIsEq` `` — **생성 코드의 내부 타입 이름**이 샌다(3번 답).
- ★ `sed` 로 잘랐지만 **자른 명령이 배너에 그대로** 있으므로 실린 것은
  「생략한 일부」가 아니라 **그 명령의 전체 출력**이다. `ex.mir` 전체는 125줄이다.

### 8. `Copy` 는 `Clone` 을 슈퍼트레이트로 요구한다

- `#[derive(Copy)]` 만 적으면 거부된다 — **`Copy: Clone`** 이기 때문이다.
  `Copy` 를 구현하려면 `Clone` 이 이미 있어야 하므로 **`#[derive(Clone, Copy)]` 로 함께** 적는다.
- **한 문장** — `` Clone `` 은 **「명시적으로 복제할 수 있다」**(메서드를 부른다),
  `` Copy `` 는 **「이동 대신 비트 복사로 넘긴다」**(부르지 않아도 된다). 뒤엣것이 앞엣것을 포함한다.
- `Drop` 이 있는 타입에는 `Copy` 를 **못 붙인다.** 값이 둘이 되면 **해제가 두 번** 일어나기 때문이다.
- ★ **정본은 [**9번 주제**](../09-copy-clone-and-drop/)** 다. 여기서는 **`derive` 로 얻을 때의 결론만** 쓴다 —
  판정 규칙·해제 시점·이동과의 관계는 거기서 본다.
  ★ 이 문서에 그 블록은 **없다** — 「던져 본 것만 싣는다」는 규칙에 따라 **결론과 링크만** 적었다.

### 9. 손으로 쓰는 세 자리

- ★ **① 제네릭 파라미터가 값으로 안 들어 있을 때**(4번 답) — `PhantomData<T>` 가 대표다.
  `derive` 의 경계가 **과해서 쓰는 쪽이 막힌다.**
- ★★ **② 필드 전부를 보는 것이 틀린 뜻일 때** — 캐시 필드·`last_accessed` 타임스탬프·
  일련번호처럼 **같음 판정에서 빼야 하는** 필드가 있으면 파생이 **거짓을 만든다.**
  ★ 이때 **`Hash` 도 반드시 함께 손으로 써야 한다** — `eq` 가 무시한 필드를 `hash` 가 섞으면
  **같은 값인데 해시가 달라져** `HashMap` 에서 값이 사라진다
  ([**28번 주제**](../28-partialeq-eq-partialord-ord-and-hash-contracts/)가 정본이다).
- **③ `Default` 가 유효하지 않은 값을 만들 때** — 「0 인 ID」·「빈 URL」이 말이 안 되면
  파생하지 말고 **생성자를 강제**한다.
- **`Debug` 를 안 붙이는 경우** — 비밀번호·토큰·주민번호처럼 **로그에 찍히면 안 되는** 필드가 있을 때.
  손으로 쓰고 그 필드를 가린다.
- ★★ **손 구현의 대가는 손품이고, 그 실수는 컴파일로 안 잡힌다.**
  필드를 하나 더했는데 `clone`·`eq`·`hash` 를 안 고치면 **컴파일은 되고 값만 조용히 틀린다.**
  그래서 **기본은 `derive`, 위 셋에 해당할 때만 손 구현**이다.

### 10. `derive` 는 내 타입에만 붙는다

- ★ `derive` 는 **타입 정의 바로 위에 적는 어트리뷰트**다. **내가 정의하는 타입에만** 쓸 수 있으므로
  「남의 타입 × 남의 트레이트」라는 [**26번 주제**](../26-orphan-rule-and-newtype/)의 금지 조합이
  **원리상 만들어지지 않는다.** 고아 규칙에 걸리는 것은 **손으로 쓰는 `impl`** 쪽이다.
- **newtype 에 `derive` 를 붙여도 안쪽 구현이 따라오는 것이 아니다** — `derive` 는
  **껍데기 타입의 필드(즉 안쪽 값 하나)를 훑어** 새 구현을 만든다.
  안쪽이 그 트레이트를 구현하고 있어야 하지만, 생기는 것은 **껍데기의 구현**이다.
- **남의 타입에는 못 붙인다.** 남의 타입 정의를 내가 못 고치기 때문이다.
  필요하면 **감싸서 내 타입으로 만든 뒤** 붙인다(26번 주제의 newtype).
- ★ **newtype 의 `Debug` 는 껍데기 이름이 앞에 붙는다** — `` Wrapper(["가", "나"]) `` 꼴이다.
  안쪽만 그대로 찍고 싶으면 `Debug` 를 **손으로** 쓴다.
  ★ 이 문서에 그 블록은 **없다** — 결론만 적고 단정은 26번 주제의 실측에 기댄다.

### 11. 생성인가, 강제인가, 런타임인가

- **Kotlin 의 `data class`**([`kotlin/syntax/22-data-class-generated-members/`](../../../kotlin/syntax/22-data-class-generated-members/)) —
  ★ **같은 것**: 컴파일러가 `toString`·`equals`/`hashCode`·`copy` 를 **생성**한다.
  ★ **다른 것 둘**: ① **고르는 단위** — Kotlin 은 `data` 한 낱말로 **한 묶음을 통째로** 주고,
  Rust 는 **필요한 것만 골라** 적는다(`Debug` 만, 또는 `Hash` 빼고).
  ② **보는 범위** — Kotlin 은 **주 생성자 프로퍼티만** 보고, Rust 의 `derive` 는 **모든 필드**를 본다.
- **Java 의 `record`**([`java/syntax/14-records/`](../../../java/syntax/14-records/)) —
  ★ **함께 강제되는 것**: **불변**(필드가 `final`)·**상속 불가**·**컴포넌트 접근자**.
  Rust 의 `derive` 는 **구현만 만들고 타입의 성질은 안 건드린다** — 가변 필드에도 `Debug` 를 붙일 수 있다.
  ★ 계약 쪽은 [`java/syntax/27-equals-hashcode-contract/`](../../../java/syntax/27-equals-hashcode-contract/)가 정본이다.
- **C# 의 `record`** — C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **18번**,
  동등성 규칙은 같은 목록의 **19번**. Java 와 같은 자리다.
- **Go**(Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **20번**) —
  `derive` 가 **없다.** 같은 자리를 **둘로** 메운다: ① `%+v` 가 **런타임 리플렉션**으로 필드를 찍고
  ② `==` 가 **언어 규칙**으로 구조를 훑는다(비교 가능한 타입만).
- ★ **셋으로 갈라 세우면** — **생성**(Rust `derive` · Kotlin `data` · Java `record`) ·
  **강제**(Java·C# 의 `record` 는 불변까지 묶는다) · **런타임**(Go 의 리플렉션).
  ★ **Rust 만 「생성하되 아무것도 강제하지 않는」 쪽**이다 — 그래서 **고르는 책임이 사람에게 있다**(9번 답).

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서·서머리의 **모든 블록** | `capture.sh` 가 `rustc --edition 2021 ex.rs -o ex` 로 컴파일하고 `./ex` 실행 | 배치 내내 + **제출 전 전수 재실행 1회** | `normalize-shaky.py` — **10블록 전부 동일** |
| ★ **다섯 derive 가 주는 것** | `b27-01` — 다섯을 한 타입에 붙이고 전부 사용 | 1 | 다섯 줄 전부 통과 |
| `{:?}` 대 `{:#?}` | `b27-02` — 유닛·튜플·이름 있는 구조체·enum 을 한 번에 | 1 | **같은 구현이 둘을 낸다** |
| ★★ **안 붙이면 무엇이 막히나** | `b27-03` — 다섯 자리를 한 프로그램에 | 1 | **E0277 ×2 · E0369 · E0599 ×2** |
| ★★★ **경계가 과한 것** | `b27-04`(E0599 + E0277) · `b27-05`(손 구현 — 통과) | 2 | **`derive` 만 막힌다** |
| ★★★ **생성된 코드 보기** | `b27-06` — `rustc --emit=mir` + `sed` (배너에 명령 전문) | 1 | `eq` 의 **필드 순서·단락**이 MIR 로 보인다 |
| ★★ **같은 것을 동작으로** | `b27-07` — 비교 때 흔적을 남기는 필드 타입 | 1 | **3줄 · 1줄 · 2줄** |
| `derive(Default)` 와 enum | `b27-08`(E0665 + 번호 없는 에러) · `b27-09`(통과) | 2 | `#[default]` 는 **유닛 변형에만** |
| ★ **필드가 못 따라가는 것** | `b27-10` — `f64` 필드에 `Eq`·`Hash` | 1 | **E0277 ×2** · `AssertParamIsEq` 가 샌다 |
| ★★ **「못 잰 것」** — 생성 소스 텍스트 | `cargo expand`(외부 크레이트) · `-Zunpretty`(나이틀리) **둘 다 없음** | 0 | ★ **「안 돌려 봄」이 아니라 「못 잼」**(7번 답) |
| **안 던져 본 것** — `Copy` 파생 · newtype 의 `Debug` | 8번·10번 답에서 **결론과 링크만** 적었다 | 0 | ★ 블록이 없으므로 단정하지 않았다 |
| 외부 크레이트 | **쓰지 않음** | 0 | std 만 |

**구현 의존 항목**(버전·환경이 바뀌면 **다시 찍어야 하는** 것).

| 항목 | 왜 |
|---|---|
| **`Debug` 의 출력 형식**(`` Key { id: 7, name: "가" } `` · 들여쓰기 4칸) | ★ std 가 **안정 보장을 약속하지 않는다** |
| **`--emit=mir` 의 지역 번호·블록 번호·문법** | ★ **컴파일러 중간 표현**이다. 판이 바뀌면 모양이 바뀐다 |
| `` AssertParamIsEq `` 라는 **이름** | ★ 파생 코드의 **내부 이름** — 바뀔 수 있다 |
| 진단에 박히는 `/rustc/ded5c06cf…/library/core/src/cmp.rs:367:1` | ★ **이 rustc 판의 커밋 해시**다 |
| `` candidate #1: `Default` `` · `help:` 의 제안 코드 | ★ 진단 품질 개선으로 자주 바뀌는 자리다 |
| `Tagged<NotClone>` 이 **8바이트**인 것 | ★ `PhantomData` 가 0 크기인 것은 보장이지만 **구조체 배치**는 구현 세부다 |
| `` error: the `#[default]` attribute … `` 에 **번호가 없는** 것 | ★ 어트리뷰트 검사 단계의 에러라 코드가 안 붙었다 — 붙을 수 있다 |

★ **다시 찍는 법** — `capture.sh` 를 그대로 돌리고 `normalize-shaky.py` 로 견준다.
이 주제에는 패닉도 주소도 없고 `HashMap` 순회도 안 쓰므로 **달라지는 파일이 하나도 없어야** 한다.
