# rust/syntax/27 — `derive` 매크로(`Debug`·`Clone`·`PartialEq`·`Default`·`Hash`) — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Reference — Derive macros](https://doc.rust-lang.org/reference/attributes/derive.html) ·
> [std — `trait Debug`](https://doc.rust-lang.org/std/fmt/trait.Debug.html) ·
> [std — `trait Default`](https://doc.rust-lang.org/std/default/trait.Default.html) ·
> [std — `trait Hash`](https://doc.rust-lang.org/std/hash/trait.Hash.html).
> ★ `rustc --explain E0277` · `E0369` · `E0407` · `E0599` · `E0665` 는 **확인용으로만 열었고 본문에 옮기지 않았다.**
> **실행 검증** — 이 문서의 모든 출력·에러는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 받은 것이다(한 블록만 `--emit=mir` 을 쓴다 — 배너에 적혀 있다).\
> ★★ **`rustc ex.rs` 만 쓰면 에디션 2015 다** — 에디션을 안 밝힌 결과는 다른 언어를 컴파일한 것과 같다.\
> ★★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
> ★★ **외부 크레이트를 하나도 쓰지 않았다**(네트워크 없음). **`cargo expand` 도 안 썼다** —
> 대신 **안정판 rustc 의 `--emit=mir`** 로 생성된 코드를 직접 본다((4)).
> **버전** — 다섯 `derive` 는 1.0.0 부터다. **`enum` 에 `#[derive(Default)]` 는 1.62.0 부터**(`#[default]` 어트리뷰트).
> `let ... else` 처럼 에디션에 묶인 문법이 아니라 **라이브러리·매크로 기능**이므로 에디션과 무관하다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | `HashMap`·`HashSet` 의 순회 순서 | ★ 이 문서는 **키로 직접 읽어** 피했다. 씨앗도 고정했다(아래) |
| **흔들린다** | 패닉 첫 줄 `thread 'main' (…)` 괄호 안의 OS 스레드 id · `0x…` 주소 | 이 주제에는 패닉 블록이 없지만 규칙은 같다 |
| 안 흔들린다 | **종료 코드 0 · 1** | 컴파일 실패는 1 이다 |
| 안 흔들린다 | 진단의 **제목 · 에러 번호 · 밑줄이 짚는 위치 · `help:` 제안** | 같은 rustc 판에서 고정이다 |
| 안 흔들린다 | `--emit=mir` 의 **지역 번호(`_1`…) · 블록 번호(`bb0`…) · 순서** | ★ 같은 rustc 판·같은 소스에서 고정. **언어 보장은 아니다** |
| 안 흔들린다 | 진단에 박히는 `/rustc/ded5c06cf…/library/core/src/cmp.rs:367:1` | 이 rustc 판의 커밋 해시다. **판이 바뀌면 바뀐다** |
| 안 흔들린다 | `Config { name: "", retries: 0, … }` 같은 **`Debug` 출력 형식** | ★ std 가 정한 형식 — 관찰이다(§구현 세부) |

★★ `HashMap` 을 쓰는 블록은 **`BuildHasherDefault<DefaultHasher>`** 로 씨앗을 고정하고
**키로 직접 읽는다.** 기본 `RandomState` 는 **프로세스마다 씨앗이 달라** 순회 순서가 실행마다 바뀐다.

## 한눈에 — 쉽게 말하면

**`derive` 는 「이 트레이트, 필드대로 뻔하게 써 줘」라고 컴파일러에게 시키는 것이다.**

| 비유 | 실체 |
|---|---|
| 「서식에 **필드 이름을 그대로 찍어 주는 도장**」 | **`Debug`** — `Key { id: 7, name: "가" }`((1)·(2)) |
| 「필드를 **하나씩 따라 복사하는 도장**」 | **`Clone`** — 필드마다 `.clone()`((1)) |
| 「**위에서부터 짝을 맞춰 보다 틀리면 멈추는** 도장」 | ★ **`PartialEq`** — **필드 순서대로 `&&`**((4)·(5)) |
| 「**빈칸에 각 칸의 기본값을 채우는** 도장」 | **`Default`** — `0`·`""`·`[]`·`None`((7)) |
| 「필드를 **차례로 섞어 넣는** 도장」 | **`Hash`** — 필드마다 `hash(state)`((1)) |
| 「도장이 **원본보다 까다로운 조건**을 요구한다」 | ★★★ **`derive` 가 붙이는 경계가 과하다**((5)) |

- ★★★ **판정은 두 줄이다** — ① `derive` 는 **필드 타입에** 그 트레이트를 요구한다((3)·(8)).
  ② 제네릭 타입이면 **모든 타입 파라미터에** 그 트레이트를 요구한다 — **쓰지도 않는 파라미터까지**((5)).
- ★★ **①은 옳고 ②는 과하다.** 필드가 `f64` 인데 `Hash` 를 파생하려는 것은 **정말 안 되는 일**이지만,
  `PhantomData<T>` 밖에 없는데 `T: Clone` 을 요구하는 것은 **필요 없는 조건**이다. **손으로 쓰면 안 그렇다**((6)).
- ★ **`derive` 는 내 타입에만 붙는다.** 그래서 [**26번 주제**](../26-orphan-rule-and-newtype/)의 고아 규칙에 **원리상 안 걸린다** —
  걸리는 것은 **손으로 쓰는 `impl`** 쪽이다.

```text
   derive 가 무엇을 만드나 — 필드를 훑는 다섯 가지 방식

   struct Key { id: u32, name: String }
                  │          │
        ┌─────────┴──────────┴──────────┐
        ▼                                ▼
   Debug   "Key { " + "id: " + {id:?} + ", name: " + {name:?} + " }"
   Clone   Key { id: self.id.clone(), name: self.name.clone() }
   PartialEq   self.id == o.id  &&  self.name == o.name      ← ★ 왼쪽부터, 틀리면 멈춘다
   Default     Key { id: u32::default(), name: String::default() }
   Hash        self.id.hash(s);  self.name.hash(s);


   그래서 요구하는 것 (경계)

   #[derive(Clone)] struct A { x: Foo }        ──▶  Foo: Clone 이라야 한다      ✔ 마땅하다
   #[derive(Clone)] struct B<T> { p: PhantomData<T> }
                                               ──▶  T: Clone 을 요구한다        ✘ 과하다
                                                    (T 값은 하나도 안 들었는데)

   impl<T> Clone for B<T> { … }                ──▶  아무 경계도 없다            ✔ 손으로 쓰면
```

> **`derive`** — `#[derive(Trait)]` 로 트레이트 구현을 **컴파일러가 생성**하게 하는 어트리뷰트.\
> 예: `#[derive(Debug)] struct Key { … }` 는 `impl Debug for Key { … }` 를 만들어 준다.

> **파생 매크로(derive macro)** — `derive` 가 부르는 절차적 매크로. 다섯 개는 **std 가 제공**한다.

> **경계(bound)** — `impl<T: Clone> …` 의 `T: Clone` 처럼 **구현이 성립하기 위한 조건**.\
> ★ `derive` 는 이것을 **자동으로 붙이는데, 필요한 것보다 넓게** 붙인다((5)).

> **`PhantomData<T>`** — **값은 안 들고 타입만 기억하는** 표식 필드. 크기가 0 이다.

## 이 주제가 답하려는 질문

1. ★★ **다섯 `derive` 가 각각 무엇을 만드나** — 그리고 **안 붙이면 어느 자리가 어떤 에러로 막히나**((1)·(3)).
2. ★★★ **`derive` 가 붙이는 경계는 왜 과한가** — `PhantomData<T>` 에 `Clone` 을 파생하면 **`T: Clone` 이 필요해진다**((5)).
   **손으로 쓰면 안 그렇다**((6)) — 그것이 「손으로 쓸 때」의 판별 기준이 된다.
3. ★ **생성된 코드를 볼 수 있나** — `cargo expand` 없이, 나이틀리 없이((4)).

★ [**25번 주제**](../25-traits-definition-impl-default-methods-and-associated-types/)가 「트레이트를 **어떻게 쓰나**」,
[**26번 주제**](../26-orphan-rule-and-newtype/)가 「**누가** 구현할 수 있나」였다면,
여기는 「**안 쓰고 얻는 길**」이다.

## 동작 방식

### (0) 이 주제가 쓰는 네 창

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| **다섯을 붙여 전부 써 보기** | 각 `derive` 가 **실제로 무엇을 주나**((1)) | 기본 창 |
| **하나도 안 붙이고 던지기** | 그것이 **무엇을 막고 있었나** — 에러 다섯 개((3)) | 「에러도 출력이다」 |
| ★★★ **`--emit=mir`** | **생성된 `eq` 의 몸통 그 자체**((4)) | ★ 이 주제의 고유 창 — `cargo expand` 대신 |
| ★★ **진단이 발원지를 짚는 것** | `` unsatisfied trait bound introduced in this `derive` macro ``((5)) | ★ 이 주제의 고유 창 |

★ **`cargo expand` 는 이 환경에서 못 쓴다**(외부 크레이트 · 네트워크 없음).
`rustc -Zunpretty=expanded` 는 **나이틀리 전용**이라 역시 못 쓴다.
★★ 그래서 **생성된 소스 텍스트는** 「**못 잰 것**」이고, 대신 **셋째·넷째 창**으로 우회했다 —
MIR 은 **소스가 아니라 컴파일러 중간 표현**이지만 **필드 순서·단락·`Eq` 연산자**가 그대로 보인다((4)).

### (1) 다섯 `derive` 가 무엇을 만드나

**언제 쓰나** — 거의 언제나. 새 구조체를 만들면 `#[derive(Debug)]` 부터 붙이는 것이 관습이다.

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

- **`Debug`** — `{:?}` 로 찍을 수 있게 된다. 형식은 `` Key { id: 7, name: "가" } `` 로
  **타입 이름 + 필드 이름 + 각 필드의 `{:?}`** 다. `String` 이 따옴표째 나오는 것에 주의한다.
- **`Clone`** — `.clone()` 이 생긴다. 원본이 **그대로 살아 있다**(이동이 아니다).
  ★ `Copy` 와의 경계는 [**9번 주제**](../09-copy-clone-and-drop/)가 정본이다 —
  결론만 옮기면 **`Copy` 는 `Clone` 을 슈퍼트레이트로 요구**하므로 `#[derive(Copy)]` 는 **혼자 못 붙는다.**
- **`PartialEq`** — `==`·`!=` 가 생긴다. **필드가 전부 같아야 같다**((4)·(5)에서 순서까지 본다).
- **`Default`** — `Key::default()` 가 생긴다. **필드마다 그 타입의 `default()`** 를 부른다((7)).
- **`Hash`** — `HashMap`·`HashSet` 의 **키가 될 수 있다.** 단 **혼자로는 부족하다** —
  `HashMap` 은 `Hash + Eq` 를 함께 요구하므로 `Eq` 도 파생해야 한다(그래서 위 예제에 `Eq` 가 함께 있다).
  계약 자체는 [**28번 주제**](../28-partialeq-eq-partialord-ord-and-hash-contracts/)가 정본이다.
- ★ **순회하지 않고 `m.get(&c)` 로 직접 읽었다.** `HashMap` 의 순회 순서는 보장이 없다.

### (2) `Debug` 의 두 얼굴 — `{:?}` 와 `{:#?}`

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

- **`{:?}` 는 한 줄**, **`{:#?}` 는 여러 줄**이다. 같은 `Debug` 구현이 **둘 다 낸다** —
  `#` 은 포매터의 **대체 형식(alternate) 플래그**이고, 파생된 코드가 그 플래그를 보고 갈라 찍는다.
- **네 가지 모양이 각각 다르게 나온다.**
  - **이름 있는 구조체** — `` Inner { x: 1, tags: ["a", "b"] } ``
  - **유닛 구조체** — `Unit` (괄호도 중괄호도 없다)
  - **튜플 구조체** — `Tup(3, 4)` (필드 이름이 없으므로 위치만)
  - **enum** — `Dot` · `Line(5)` · `` Box { w: 6, h: 7 } `` — **변형마다 그 변형의 모양**을 따른다
- ★ **`{:#?}` 는 들여쓰기가 4칸**이고 **마지막 항목 뒤에도 쉼표**가 붙는다(`tags: [ "a", "b", ]`).
  로그에 찍을 때는 `{:?}`, 사람이 읽을 때는 `{:#?}` 다.
- ★ **`Debug` 는 사람이 읽는 형식이지 직렬화 형식이 아니다.** std 는 이 형식을 **안정 보장으로 약속하지 않는다**(§구현 세부).

### (3) ★★ 하나도 안 붙이면 — 다섯 자리가 각각 다른 에러다

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

- ★★ **에러 번호가 세 가지**로 갈린다. 「derive 를 안 붙였다」는 **한 가지 에러가 아니다.**

| 무엇을 하려 했나 | 에러 | 진단이 말하는 것 |
|---|---|---|
| `{:?}` 로 찍기 | **E0277** | `` `Bare` doesn't implement `Debug` `` + `` add `#[derive(Debug)]` … `` |
| `T: Clone` 경계에 넘기기 | **E0277** | `` the trait bound `Bare: Clone` is not satisfied `` |
| `==` | **E0369** | `` binary operation `==` cannot be applied to type `Bare` `` |
| `Bare::default()` | **E0599** | `` no function or associated item named `default` `` |
| `HashMap` 키로 넣기 | **E0599** | `` doesn't satisfy `Bare: Eq` or `Bare: Hash` `` |

- ★ **연산자는 E0369 이고 메서드·연관 함수는 E0599 다.** 「트레이트가 없다」는 같은 사실인데
  **닿는 문법이 무엇이냐**에 따라 진단이 갈린다.
- ★★ **다섯 중 넷이 `help:` 로 정확한 `derive` 를 적어 준다** —
  `` consider annotating `Bare` with `#[derive(Eq, Hash, PartialEq)]` `` 처럼 **필요한 것을 전부** 센다.
  `Default` 만 `help:` 대신 `` candidate #1: `Default` `` 라는 후보 목록으로 답한다.
- **`Debug` 쪽에만 `= note:` 가 하나 더 붙는다** —
  `` this error originates in the macro `$crate::format_args_nl` … `` . `println!` 을 거쳤기 때문이다.

### (4) ★★★ `cargo expand` 없이 생성된 코드 보기 — `--emit=mir`

**언제 쓰나** — 「`derive` 가 **정확히 무엇을** 만들었나」가 궁금할 때. 안정판 rustc 하나면 된다.

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

- ★★★ **생성된 `eq` 의 몸통이 그대로 보인다.** 네 가지가 읽힌다.
  1. **시그니처** — `` fn <impl at ex.rs:3:10: 3:19>::eq(_1: &P, _2: &P) -> bool ``.
     **이름이 없고 `#[derive(PartialEq)]` 가 적힌 위치(3:10\~3:19)로 불린다** — 사람이 안 쓴 `impl` 이라는 뜻이다.
  2. ★ **필드 0 을 먼저 본다** — `bb0` 에서 `` ((*_1).0: u8) `` 과 `` ((*_2).0: u8) `` 를 `Eq` 로 견준다.
  3. ★★ **틀리면 거기서 멈춘다** — `` switchInt(move _3) -> [0: bb2, otherwise: bb1] `` 이고
     `bb2` 는 `` _0 = const false `` 로 **필드 1 을 아예 안 본다.** 이것이 단락(short-circuit)이다.
  4. **맞으면 필드 1 을 보고 그 결과가 반환값**이 된다(`bb1`).
- ★ **한계 — 이것은 소스가 아니라 MIR 이다.** 실제 생성 소스(`self.a == other.a && self.b == other.b`)를
  **글자 그대로** 보려면 `cargo expand` 나 나이틀리의 `-Zunpretty=expanded` 가 필요한데
  **이 환경에서는 둘 다 못 쓴다.** ★★ 그래서 **「생성 소스 텍스트」는 이 문서에서** 「**못 잰 것**」이고,
  **「무엇을 하는 코드인가」는 잰 것**이다. 둘을 갈라 읽는다.
- ★ `sed` 로 잘랐다 — **자른 명령이 배너에 그대로 적혀 있으므로** 실린 것은 「생략한 일부」가 아니라
  **그 명령의 전체 출력**이다. `ex.mir` 전체는 125줄이고 나머지는 `main` 과 포매팅 코드다.

같은 것을 **동작으로도** 볼 수 있다 — 필드마다 흔적을 남기는 타입을 끼워 넣는다.

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

- **`[1]` 에서 셋을 다 비교**하고, **`[2]` 에서는 `first` 하나만** 비교하고 멈춘다.
  **`[3]` 은 `first`·`second` 까지** 보고 멈춘다. (4)의 MIR 과 **같은 사실의 두 얼굴**이다.
- ★ **마커도 결과도 전부 `eprintln!`** 이다. `println!`(표준 출력)과 섞으면 파이프로 받을 때 순서가 갈린다.
- ★ 그래서 **`derive(PartialEq)` 는 「필드 순서에 성능이 달린다」** — 자주 갈리는 필드를 앞에 두면 빨라진다.
  ★★ 다만 **의미는 순서와 무관**하다(`&&` 는 결합적이다). 갈리는 것은 **비용뿐**이다.

### (5) ★★★ `derive` 가 붙이는 경계가 과하다

**언제 쓰나** — 제네릭 타입에 `derive` 를 붙였는데 **쓰는 쪽에서 이상한 에러**가 날 때.

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

- ★★★ **`Tagged<T>` 는 `T` 값을 하나도 안 들고 있다.** 필드는 `i64` 와 `PhantomData<T>` 뿐이고
  `PhantomData<T>` 는 **크기가 0 이다.** 그런데 **`T: Clone` 이 없으면 복제가 안 된다.**
- ★★ **에러가 두 번, 번호가 다르다.**
  - **메서드로 바로 부르면 E0599** — `` the method `clone` exists for struct `Tagged<NotClone>`, but its trait bounds were not satisfied ``.
    「없다」가 아니라 「**있는데 조건이 안 맞는다**」고 말한다.
  - **`T: Clone` 경계를 통과시키려 하면 E0277** — `` the trait bound `NotClone: Clone` is not satisfied ``.
- ★★★ **두 진단 모두 발원지를 짚는다** —
  `` note: trait bound `NotClone: Clone` was not satisfied `` 아래에 **`#[derive(Clone)]` 줄**이 나오고
  `` unsatisfied trait bound introduced in this `derive` macro `` 가 붙는다.
  **`derive` 가 만든 경계라는 사실을 진단이 직접 말해 준다** — (4)의 MIR 말고 **이 줄도 생성 결과를 드러내는 창**이다.
- ★ `help:` 는 `` consider annotating `NotClone` with `#[derive(Clone)]` `` 를 권한다.
  **그것도 답이지만 옳은 답은 아니다** — `NotClone` 은 남의 타입일 수도 있고, 애초에 **필요 없는 조건**이다.

### (6) ★ 손으로 쓰면 그 경계가 안 붙는다

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

- **같은 타입, 같은 쓰임인데 통과한다.** 다른 것은 `impl<T> Clone for Tagged<T>` 에
  **`where T: Clone` 이 없다**는 것 하나뿐이다.
- ★★ **이것이 「`derive` 를 손 구현으로 바꿀 때」의 판별 기준**이다 —
  **타입 파라미터가 필드에 값으로 안 들어 있으면** `derive` 의 경계는 과하다.
  `PhantomData<T>`·`fn(T) -> T` 같은 표식·함수 포인터 필드가 그 자리다.
- **크기는 8바이트로 `i64` 와 같다** — `PhantomData<T>` 가 자리를 안 차지한다(★ 이 판의 관찰이다).
- ★ 대가는 **손품**이다. 필드가 늘면 `clone` 을 손으로 고쳐야 하고, **고치는 것을 잊으면 조용히 틀린다**
  (컴파일은 되고 값만 안 따라온다). 그래서 **기본은 `derive`, 경계가 문제될 때만 손 구현**이다.

### (7) `derive(Default)` — enum 에서만 사람에게 묻는다

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

- ★★ **구조체는 안 묻고 enum 은 묻는다.** 구조체는 「필드마다 그 타입의 기본값」이라는 답이 **한 가지뿐**인데,
  enum 은 **어느 변형이 기본인지 코드에 답이 없다.** 그래서 **E0665** 가 사람에게 되묻는다 —
  `` this enum needs a unit variant marked with `#[default]` ``.
- ★ **`help:` 가 변형 하나하나에 대해 따로 나온다**(`Fast` 에 붙이는 안, `Slow` 에 붙이는 안).
  **고를 사람이 사람이라는 뜻**이다.
- ★★ **`#[default]` 는 유닛 변형에만** 붙는다. 데이터를 담은 변형에 붙이면
  `` the `#[default]` attribute may only be used on unit enum variants `` — ★ **에러 번호가 없는 에러**다.
  `` = help: consider a manual implementation of `Default` `` 가 답을 준다.

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

- **고치면 통과한다.** `Mode::default()` 가 `Slow` 이고,
  **구조체는 필드마다 그 타입의 `default()`** 를 부른다 — `` "" `` · `0` · `0.0` · `false` · `[]` · `Slow` · `None`.
- ★ **`mode: Mode` 필드가 `Mode::default()` 를 부른다** — 파생이 **재귀적으로 이어진다.**
- ★ **`Default` 는 「0 으로 채운다」가 아니라** 「**각 타입이 정한 기본값**」이다.
  `Option` 은 `None`, `Vec` 은 빈 벡터, 내 enum 은 `#[default]` 변형이다.

### (8) ★ `derive` 는 필드에 그 트레이트를 요구한다

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

- **`f64` 는 `Eq` 도 `Hash` 도 아니다.** 그래서 `f64` 필드를 가진 타입은 그 둘을 **파생할 수 없다.**
  (`PartialEq` 는 된다 — `f64` 가 `PartialEq` 이기 때문이다. **이 문서에서 그 셋이 갈리는 첫 자리**다.
  이유는 [**28번 주제**](../28-partialeq-eq-partialord-ord-and-hash-contracts/)가 정본이다.)
- ★★★ **진단이 `derive` 안을 가리킨다** — `` #[derive(PartialEq, Eq, Hash)] `` 줄 아래에
  `` -- in this derive macro expansion `` 이 **`Eq` 쪽과 `Hash` 쪽에 각각** 그어지고,
  밑줄은 **문제가 된 필드(`ratio: f64`)** 를 짚는다. **어느 `derive` 가 어느 필드에서 막혔는지**가 한눈에 나온다.
- ★★ **`Eq` 쪽에는 창이 하나 더 있다** — `` note: required by a bound in `AssertParamIsEq` ``.
  `AssertParamIsEq` 는 **`derive(Eq)` 가 만들어 넣는 내부 타입**이다.
  `Eq` 는 메서드가 없는 표식이라 **「필드가 `Eq` 인가」를 검사할 자리가 따로 필요**했고, 그것이 이 이름으로 샌다.
  ★ **진단이 생성 코드의 조각을 이름으로 흘리는 셈**이다 — (4)·(5)에 이은 **셋째 창**이다.
- **처방은 셋 중 하나다** — ① `f64` 를 안 쓰거나 ② `Eq`·`Hash` 를 포기하거나
  ③ **손으로 쓰되 계약을 지키거나**(28번 주제).

## 문법 — 형태와 규칙

```text
   형태

   #[derive(Debug, Clone, PartialEq, Eq, Default, Hash)]
   struct Key { id: u32, name: String }
       │
       └── 한 줄에 여럿. 순서는 뜻에 영향이 없다(생성 순서만 그 순서다)

   #[derive(Debug, Default)]
   enum Mode { Fast, #[default] Slow }
                     └── enum 의 Default 만 사람에게 묻는다 (1.62.0~)

   생성되는 것 (요약 — 실제 몸통은 (4)의 MIR 로 확인했다)

   Debug       impl Debug for Key      → fmt(&self, f) : 타입 이름 + 필드들
   Clone       impl Clone for Key      → clone(&self) -> Key : 필드마다 .clone()
   PartialEq   impl PartialEq for Key  → eq(&self, o) -> bool : 필드 순서대로 && (단락)
   Default     impl Default for Key    → default() -> Key : 필드마다 Default::default()
   Hash        impl Hash for Key       → hash(&self, s) : 필드마다 hash(s)

   자동으로 붙는 경계

   #[derive(Clone)] struct S<T, U> { a: T, b: PhantomData<U> }
                    ──▶ impl<T: Clone, U: Clone> Clone for S<T, U>
                                       ^^^^^^^^  ★ U 는 값이 없는데도 붙는다
```

**규칙 불릿.**

- ★★★ **`derive` 는 필드 타입에 그 트레이트를 요구한다** — `f64` 필드에 `Eq`·`Hash` 는 못 붙인다((8)).
- ★★★ **제네릭이면 모든 타입 파라미터에 같은 경계를 붙인다** — **필요 없어도 붙는다**((5)).
  손으로 쓰면 안 붙는다((6)).
- **`PartialEq` 는 필드 순서대로 비교하고 틀리면 멈춘다**((4)). 뜻은 그대로, **비용만** 순서에 달렸다.
- **`Default` 는 enum 에서만 `#[default]` 를 요구하고, 그것은 유닛 변형에만 붙는다**((7)).
- **`HashMap` 키에는 `Hash` 만으로 부족하다** — `Eq` 가 함께 있어야 한다((1)·(3)).
- ★ **`Copy` 를 파생하려면 `Clone` 도 함께** 파생해야 한다([**9번 주제**](../09-copy-clone-and-drop/)가 정본).
- ★ **`derive` 는 내 타입에만 붙으므로 고아 규칙에 안 걸린다**([**26번 주제**](../26-orphan-rule-and-newtype/)).

### 금지 사례 — 던져서 받은 다섯

| 던진 것 | 받은 것 |
|---|---|
| `derive` 없이 `{:?}` | **E0277** `` `Bare` doesn't implement `Debug` `` |
| `derive` 없이 `==` | **E0369** `` binary operation `==` cannot be applied `` |
| `derive` 없이 `Bare::default()` | **E0599** `` no function or associated item named `default` `` |
| `#[derive(Default)]` 를 `#[default]` 없는 enum 에 | **E0665** `` this enum needs a unit variant marked with `#[default]` `` |
| `f64` 필드에 `derive(Eq, Hash)` | **E0277** ×2 — `` in this derive macro expansion `` |

## 어디서 틀리나

### 1. ★★★ 「`derive` 는 손으로 쓴 것과 같다」

**경계가 다르다**((5)·(6)). `PhantomData<T>` 만 있는 타입에 `derive(Clone)` 을 붙이면
**`T: Clone` 이 없으면 복제가 안 된다.** 손으로 쓰면 그 조건이 아예 없다.
★ **쓰는 쪽에서 터지므로 만든 쪽은 모른다** — 공개 라이브러리에서 특히 아프다.

### 2. ★★ 「`Hash` 를 파생했으니 `HashMap` 키가 된다」

**`Eq` 가 더 필요하다**((1)·(3)). 진단이 `` doesn't satisfy `Bare: Eq` or `Bare: Hash` `` 라고
**둘을 함께** 말해 준다. 그리고 `Eq` 를 파생하려면 **모든 필드가 `Eq`** 라야 한다((8)).

### 3. ★ 「`Debug` 출력은 형식이 정해져 있다」

**std 가 안정 보장으로 약속하지 않는다**(§구현 세부). **로그·디버깅용**이지
**파싱해서 쓰는 형식이 아니다.** 저장·전송에는 직렬화 크레이트를 쓴다(이 환경에서는 못 쓴다).

### 4. ★★ 「`Default` 는 0 으로 채운다」

**각 타입이 정한 값**이다((7)). `String` 은 `` "" ``, `Vec` 은 `[]`, `Option` 은 `None`,
내 enum 은 **`#[default]` 로 내가 고른 변형**이다. `Option` 이 `None` 인 것은 0 이라서가 아니다.

### 5. ★ 「필드 순서는 아무래도 좋다」

**뜻은 그렇고 비용은 아니다**((4)). `derive(PartialEq)` 는 **왼쪽부터 보고 틀리면 멈춘다** —
비싼 필드(긴 `String`·`Vec`)를 앞에 두면 그만큼 자주 치른다.
★ 그리고 [**28번 주제**](../28-partialeq-eq-partialord-ord-and-hash-contracts/)의 `derive(PartialOrd)` 에서는
**순서가 뜻까지 정한다**(사전식).

### 6. ★ 「에러 번호 하나만 외우면 된다」

**세 가지다**((3)) — 연산자는 **E0369**, 메서드·연관 함수는 **E0599**, 경계는 **E0277**.
같은 「트레이트가 없다」인데 **닿는 문법**에 따라 갈린다.

### 7. 「`cargo expand` 가 없으면 볼 방법이 없다」

**셋이 있다**((4)·(5)·(8)) — **`--emit=mir`** 로 몸통을, **진단의 `` in this derive macro `` 줄**로 경계를,
**`AssertParamIsEq` 같은 내부 이름**으로 생성 조각을 본다.
★ 다만 **생성 소스 텍스트 자체는** 「**못 잰 것**」이다 — 그것만은 안정판으로 못 얻었다.

## 구현 세부사항 대 언어 보장

| 항목 | 무엇인가 | 근거 |
|---|---|---|
| `derive` 가 **필드 타입에 그 트레이트를 요구**하는 것 | ★ **언어 보장** — Reference 의 derive 절 | (3)·(8)의 실측 |
| `derive` 가 **모든 타입 파라미터에 경계를 붙이는** 것 | ★ **언어 보장**(표준 파생 매크로의 규정된 동작) | (5)의 실측 |
| `PartialEq` 가 **필드 순서대로 단락 비교**하는 것 | ★ **언어 보장** — 순서가 규정돼 있다 | (4)의 MIR·동작 |
| enum `Default` 가 `#[default]` 를 요구하는 것 | ★ **언어 보장**(1.62.0\~) | (7)의 실측 |
| **`Debug` 의 출력 형식** | ★ **구현 세부** — std 가 안정 보장을 약속하지 않는다 | (1)·(2)의 관찰 |
| **`--emit=mir` 의 지역·블록 번호와 형태** | ★ **구현 세부** — 컴파일러 중간 표현이다 | (4)의 관찰 |
| `AssertParamIsEq` 라는 **이름** | ★ **구현 세부** — 생성 코드의 내부 이름이다 | (8)의 관찰 |
| `PhantomData<T>` 가 **크기 0** 인 것 | ★ **언어 보장** — 0 크기 타입으로 규정돼 있다 | (6)의 실측(8 = `i64`) |
| `` candidate #1: `Default` `` 같은 제안 | ★ **구현 세부** — 진단 품질 | (3)의 관찰 |
| **`cargo expand` 로만 보이는 생성 소스** | ★ **「못 잰 것」** — 도구가 없다(나이틀리 금지·네트워크 없음) | (4)에 적었다 |

## 언제 쓰고 언제 안 쓰나

- **`derive` 를 쓴다** — 기본값이다. 새 타입을 만들면 `#[derive(Debug)]` 부터 붙인다.
- **`Clone`·`PartialEq` 를 파생한다** — 필드 전부를 비교·복제하는 것이 **맞는 뜻**일 때.
- ★ **손으로 쓴다 ①** — **제네릭 파라미터가 값으로 안 들어 있을 때**((5)·(6)). `PhantomData<T>` 가 대표다.
- ★ **손으로 쓴다 ②** — **필드 전부를 보는 것이 틀린 뜻일 때.** 캐시 필드·타임스탬프처럼
  **같음 판정에서 빼야 하는** 필드가 있으면 파생이 거짓을 만든다.
  ★★ 이때 **`Hash` 도 같이 손으로 써야** 한다 — 안 그러면 계약이 깨진다(28번 주제).
- ★ **손으로 쓴다 ③** — **`Default` 가 유효하지 않은 값을 만들 때.** 「0 인 ID」가 말이 안 되면
  파생하지 말고 **생성자를 강제**한다.
- **`Debug` 를 안 붙인다** — 비밀번호·토큰처럼 **찍히면 안 되는** 필드가 있을 때. 손으로 쓰고 가린다.

## 핵심 문장

- ★★★ **`derive` 는 필드에 요구하고, 제네릭이면 파라미터에도 요구한다** — **앞은 마땅하고 뒤는 과하다.**
- ★★ **과한 경계는 「쓰는 쪽」에서 터진다** — 만든 쪽 컴파일은 통과한다((5)).
- ★★ **「trait 이 없다」는 에러가 셋이다** — 연산자 E0369 · 메서드 E0599 · 경계 E0277((3)).
- ★ **`derive(PartialEq)` 는 필드 순서대로 보고 틀리면 멈춘다** — 뜻이 아니라 **비용**이 순서에 달렸다((4)).
- ★ **`Default` 는 enum 에서만 사람에게 묻는다** — 구조체는 답이 하나뿐이기 때문이다((7)).
- ★ **`cargo expand` 없이도 셋이 보인다** — MIR · 진단의 발원지 줄 · 생성 내부 이름((4)·(5)·(8)).

## 관련 자료

- [**9번 주제** — `Copy`·`Clone`·`Drop`](../09-copy-clone-and-drop/) —
  ★ **경계**: **`Clone` 과 `Copy` 의 정본은 거기다.** 여기서는 **`derive` 로 얻을 때의 결론만** 쓴다
  (`Copy` 는 `Clone` 을 함께 요구한다 · `Clone` 은 필드마다 `.clone()` 을 부른다).
- [**17번 주제** — 열거형과 데이터를 담는 변형](../17-enums-and-data-carrying-variants/) —
  ★ **경계**: 변형의 **설계**는 거기, 여기는 그 변형에 **`#[default]` 를 어떻게 다나**((7)).
- [**25번 주제** — 트레이트 정의·구현·기본 메서드](../25-traits-definition-impl-default-methods-and-associated-types/) —
  ★ **경계**: 손으로 쓰는 `impl` 의 문법은 거기, 여기는 **안 쓰고 얻는 길**이다.
- [**26번 주제** — 고아 규칙과 newtype](../26-orphan-rule-and-newtype/) —
  ★ **경계**: `derive` 는 **내 타입에만** 붙어 고아 규칙에 안 걸린다. 걸리는 것은 손 `impl` 쪽이다.
- [**28번 주제** — `PartialEq`/`Eq`/`PartialOrd`/`Ord`/`Hash` 의 계약](../28-partialeq-eq-partialord-ord-and-hash-contracts/) —
  ★ **경계**: **무엇이 생성되나**는 여기, **그 생성물이 지켜야 하는 계약**은 거기다.
  「`f64` 는 왜 `Eq` 가 아닌가」도 거기다.
- 목록의 **29번 주제** — `From`/`Into`/`TryFrom`. `Default` 와 함께 **「기본값·변환」 표면**을 이룬다.
- 목록의 **57번 주제** — 매크로. `derive` 가 **절차적 매크로**라는 것의 정본이다.
- Kotlin 의 `data class` — [`kotlin/syntax/22-data-class-generated-members/`](../../../kotlin/syntax/22-data-class-generated-members/).
  ★ **대비**: 목적이 같은데 **고르는 방식이 반대**다 — Kotlin 은 `data` 한 낱말로 **다섯을 한꺼번에** 주고,
  Rust 는 **필요한 것만 골라** 적는다. 그리고 Kotlin 은 **주 생성자 프로퍼티만** 보고, Rust 는 **모든 필드**를 본다.
- Java 의 `record` — [`java/syntax/14-records/`](../../../java/syntax/14-records/) ·
  `equals`/`hashCode` 계약은 [`java/syntax/27-equals-hashcode-contract/`](../../../java/syntax/27-equals-hashcode-contract/).
  ★ **대비**: `record` 도 한 낱말로 묶어 주지만 **불변·final 이 함께 강제**된다.
- C# 의 `record` — C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **18번**.
  ★ 동등성 규칙 자체는 같은 목록의 **19번**이다.
- Go 에는 `derive` 가 **없다** — Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **20번**.
  ★ **대비**: `%+v` 가 리플렉션으로 **런타임에** 찍고, 비교는 `==` 가 **언어 차원에서** 구조를 훑는다.
  **코드 생성이 아니라 런타임·언어 규칙**으로 같은 자리를 메운다.

## 용어 풀이

- **`derive`** — 트레이트 구현을 컴파일러에게 생성시키는 어트리뷰트. `#[derive(Debug)]`.
- **파생 매크로(derive macro)** — `derive` 가 부르는 절차적 매크로. 다섯은 std 가 제공한다.
- **경계(bound)** — `impl<T: Clone>` 의 `T: Clone`. 구현이 성립하기 위한 조건.
- **단락(short-circuit)** — `&&` 가 왼쪽이 거짓이면 오른쪽을 아예 안 보는 것.
- **`PhantomData<T>`** — 값은 안 들고 타입만 기억하는 크기 0 짜리 표식 필드.
- **MIR(Mid-level IR)** — rustc 가 타입 검사 뒤에 쓰는 중간 표현. `--emit=mir` 로 뽑는다.
- **대체 형식(alternate)** — `{:#?}` 의 `#`. 포매터가 보는 플래그다.
- **표식 트레이트(marker trait)** — 메서드가 없고 **성질만 표시**하는 트레이트. `Eq`·`Copy` 가 그렇다.

## 더 들어가면

- **완벽한 파생(perfect derive)** — 「필드에 실제로 필요한 경계만 붙이기」는 **오래된 미해결 문제**다.
  (5)의 과한 경계가 그 이유이고, 바꾸면 **하위 호환이 깨진다**(경계가 줄면 공개 API 가 넓어진다).
- **`#[derive]` 를 직접 만들기** — 절차적 매크로 크레이트(`proc-macro = true`)가 필요하다.
  ★ **이 환경에서는 못 만든다**(별도 크레이트가 필요하다).
- **`Clone` 의 `clone_from`** — 파생은 `clone` 만 채우고 `clone_from` 은 **기본 구현**을 쓴다.
  큰 버퍼를 재사용하려면 손으로 쓴다.
- **`#[derive(Copy)]` 와 `Drop` 의 배타** — `Drop` 이 있으면 `Copy` 를 못 붙인다
  ([**9번 주제**](../09-copy-clone-and-drop/)).
- **`Hash` 의 `hash_slice`** — `Hash` 에는 슬라이스 전용 기본 메서드가 하나 더 있다. 파생은 안 건드린다.
