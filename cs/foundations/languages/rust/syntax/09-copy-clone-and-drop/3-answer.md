# rust/syntax/09 — `Copy`와 `Clone`, 그리고 `Drop` 시점 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러·경고는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 얻은 것이다. `cargo` 는 쓰지 않았다.\
> ★ **`--edition` 을 빼면 에디션 2015 다.** 이 문서의 결과는 전부 **2021** 기준이다.\
> 실험 파일 이름은 전부 **`ex.rs`** 로 고정했고, **진단의 줄 번호는 그 파일 기준**이라\
> 질문 쪽 발췌와 어긋날 수 있다. 그래서 **진단을 싣는 블록마다 그 진단을 낸 소스를 같은 자리에** 뒀다.\
> ★ **주소값(`0x6076...`)은 실행마다 바뀐다**(ASLR). 근거로 읽을 칸은 「**같은가 / 다른가**」와 **카운트**뿐이다.\
> ★ 해제 시점은 컴파일러가 말해 주지 않으므로 **`impl Drop` 의 `println!`** 으로 관찰했다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★ 파생을 하나만 붙이면

**출력**

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

**왜 그런가**

- **컴파일되지 않는다. E0277**, 제목은 **`the trait bound P: Clone is not satisfied`** 다.
- `note:` 가 **std 의 `core/src/marker.rs`** 를 가리킨다 — **`required by a bound in Copy`**.\
  즉 내 코드가 아니라 **`Copy` 트레이트 선언 쪽의 제약**이라는 뜻이다.
- std 의 선언이 **`pub trait Copy: Clone { }`** 이라 **`Clone` 이 상위 트레이트**다.
- **`#[derive(Clone)]` 만 붙이면 통과한다.** 한쪽 방향만 강제다.

```text
   Clone ⊃ Copy

   +--------------------------- Clone -------------------------+
   |  String · Vec<T> · HashMap · Box<T>                        |
   |  +-------------------- Copy --------------------+          |
   |  |  i32 · bool · char · &T · [i32; 3] · (i32,b) |          |
   |  +----------------------------------------------+          |
   +------------------------------------------------------------+

   Copy 만 있는 영역은 없다 (E0277)
```

> **상위 트레이트(supertrait)** — `trait A: B` 에서의 `B`. `A` 를 구현하려면 `B` 가 먼저 있어야 한다.\
> 예: `Copy: Clone` 이라 `Clone` 없이 `Copy` 를 못 붙인다.

### 2. ★ `String` 이 든 구조체에 `Copy` 를 던지면

**출력**

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

**왜 그런가**

- **E0204** 다. 밑줄(`^^^^`)은 **`derive` 목록의 `Copy` 글자**에, 밑줄(`----`)은 **문제의 필드**에 그어진다.\
  ★ **범인을 필드 단위로 짚어 준다** — `this field does not implement Copy`.
- **필드가 열 개인데 아홉만 `Copy` 여도 거부된다.** 전부 `Copy` 여야 한다. 하나로 충분히 막힌다.

`rustc --explain E0204`:

> The `Copy` trait was implemented on a type which contains a field that doesn't
> implement the `Copy` trait.
>
> (…)
>
> This fails because `&mut T` is not `Copy`, even when `T` is `Copy` (this
> differs from the behavior for `&T`, which is always `Copy`).

- ★ 덤으로 얹는 문장은 **`&mut T` 는 `Copy` 가 아니고 `&T` 는 항상 `Copy` 다**라는 것이다.
- 그 둘이 갈리는 이유(가변 별칭이 공짜로 생기면 안 된다)의 정본은 [**10번 주제**](../10-borrowing-and-aliasing-rules/)다.

### 3. ★★ 둘을 같이 달면

**출력**

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

**왜 그런가**

- **E0184**, 제목은 **`the trait Copy cannot be implemented for this type; the type has a destructor`** 다.
- 막는 이유는 [**08번 주제**](../08-ownership-and-move/)가 세운 규칙 하나로 설명된다 — **해제는 정확히 한 번**이다.

```text
   지금 (Copy 아님)                     만약 Copy 이면서 Drop 이라면
   let t = Tag(1);                     let t = Tag(1);
   let u = t;      <- 이동              let u = t;      <- 복사. t 도 산다
   +---------------+                   +----------------+
   | t  [무효]     |                   | t  Tag(1)      |
   | u  Tag(1)     |                   | u  Tag(1)      |
   +---------------+                   +----------------+
   }                                   }
     -> [해제] 한 번                      -> [해제] t
                                          -> [해제] u   <- 같은 자원을 두 번
   08번의 보장 그대로                      double free
```

- `Copy` 는 **옛 이름을 죽이지 않는다**. 그러면 같은 값이 두 이름에 있고 **소멸자가 두 번** 불린다.
- 소멸자가 「힙 반납」이면 그것이 곧 **double free** 다. 그래서 언어가 조합 자체를 막는다.
- ★ **뒤집어 읽으면 — `Copy` 타입에는 소멸자가 있을 수 없다.**\
  그래서 이 주제의 관찰 창(`impl Drop` + `println!`)을 `Copy` 타입에는 **원리적으로 못 단다.**

`rustc --explain E0184`:

> Explicitly implementing both `Drop` and `Copy` trait on a type is currently
> disallowed. This feature can make some sense in theory, but the current
> implementation is incorrect and can lead to memory unsafety (see
> [issue #20126][iss20126]), so it has been disabled for now.

- ★ 영구 규칙이 아닐 수 있다는 신호는 **`currently`** 와 **`for now`** 다.\
  그리고 이유를 「**이론적으로는 말이 될 수 있는데 구현이 틀렸다**」로 적는다 — 설계가 아니라 **구현 쪽 사유**다.

### 4. ★ 두 `clone()` 의 결과

**출력**

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

**왜 그런가**

- **`Vec::clone` 은 버퍼가 다르다**(`false`). **`Rc::clone` 은 버퍼가 같다**(`true`).
- `Rc::clone` 뒤 `strong_count` 는 **2**, `drop(r2)` 뒤에는 **1** 이다.
- **`(*r1).clone()` 은 깊다** — `Rc` 를 벗기고 안쪽 `Vec` 의 `Clone` 을 부르기 때문이다.
- 「`clone()` 은 깊은 복사다」는 **틀린 문장**이다. **깊이는 그 타입의 `Clone` 구현이 정한다.**\
  `Clone` 트레이트 자체는 깊이를 강제하지 않는다.

```text
   Vec::clone — 깊다                    Rc::clone — 얕다
   v1 ptr --+--> [1,2,3]  0x..d00       r1 --+                   count
   v2 ptr --+--> [1,2,3]  0x..d20            +--> (count=2)--> [1,2,3]  0x..d40
            서로 다른 버퍼                r2 --+
            고치면 따로 논다                   같은 버퍼. drop(r2) -> count=1
```

**근거로 읽어도 되는 칸과 안 되는 칸**

| 칸 | 읽어도 되나 | 이유 |
|---|---|---|
| `같은 버퍼인가? false`(Vec) | **근거** | 관계는 실행마다 고정 |
| `같은 버퍼인가? true`(Rc) | **근거** | 〃 |
| `strong_count` 1 → 2 → 1 | **근거** | `Rc` 의 계약 |
| `0x607669d5ed00` 같은 **절댓값** | **아니다** | ASLR 로 실행마다 바뀐다 |

- `Rc` 의 정본은 목록의 **41번 주제**다. 여기서는 **현상만** 싣는다.

### 5. `derive(Clone)` 이 붙이는 것

**출력**

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

**왜 그런가**

- **거부되는 쪽은 `Derived`**(파생한 쪽)다. 에러 번호는 **E0599** 다.\
  ★ **손으로 쓴 `Manual` 쪽 줄은 에러가 안 났다** — 그 줄을 지우면 통과한다.
- `note:` 가 범인을 직접 지목한다 — **`unsatisfied trait bound introduced in this derive macro`**.\
  즉 **그 경계를 넣은 것은 `derive` 매크로**다.
- `derive(Clone)` 은 **타입 파라미터마다 기계적으로 `T: Clone` 을 붙인다**.\
  여기 필드는 `Rc<T>` 이고 `Rc<T>` 는 `T` 와 무관하게 `Clone` 인데도 붙는다.

```text
   derive 가 만든 것                     손으로 쓴 것
   impl<T: Clone> Clone for Derived<T>  impl<T> Clone for Manual<T>
          ^^^^^^^                              ^ 경계 없음
   Derived<NotClone> -> clone() 없음     Manual<NotClone> -> clone() 있다
```

- 라이브러리 경계에서 문제가 되는 이유 — **내 타입의 `Clone` 가능 조건이 실제보다 좁게 공개된다.**\
  쓰는 쪽은 「왜 이게 안 되지」를 겪고, 고치려면 **공개 API 를 바꿔야** 한다.
- `derive` 전수는 목록의 **27번 주제**가 정본이다.

### 6. ★★ 이 프로그램의 출력 순서

**출력**

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

**왜 그런가**

- **지역 변수는 선언 역순**이다 — `3번째` → `2번째` → `1번째`. 나중에 만든 것이 먼저 죽는다(LIFO).
- **구조체 필드는 선언 순**이다 — `a` → `b`. ★ **지역 변수와 방향이 정반대**다.
- **`Pair` 는 본체가 먼저**다 — `Drop::drop(&mut self)` 가 먼저 불리고 그 뒤에 필드가 선언 순으로 해제된다.\
  ★ **그럴 수밖에 없다** — 내 소멸자가 `self.first` 를 읽을지도 모르는데 필드가 먼저 사라지면 안 된다.\
  08번의 **E0509**(`Drop` 구현체는 부분 이동 금지)가 **같은 사실의 다른 얼굴**이다.
- **튜플·`Vec` 원소는 선언 순**(앞에서 뒤로) — 필드와 같은 규칙이다.
- ★ **함수 인자는 역순**이다(`인자-뒤` → `인자-앞`) — 인자는 그 함수의 **지역 변수**로 다뤄진다.

```text
   지역 변수·함수 인자 — 역순            필드·튜플·Vec 원소 — 선언 순
   let _x = D("1번째")  +               struct Plain { a, b }
   let _y = D("2번째")  |  +                           |  |
   let _z = D("3번째")  |  |  +                        |  +-> [해제] b  나중
   }                    |  |  +-> [해제] 3번째         +----> [해제] a  먼저
                        |  +----> [해제] 2번째
                        +-------> [해제] 1번째
```

```text
   Drop 을 단 구조체 — 본체 먼저, 필드 나중
   impl Drop for Pair
        |
        +-> [해제] Pair 본체 먼저      <- 여기서 self.first 를 읽을 수 있어야 한다
              +-> [해제] 필드-first
              +-> [해제] 필드-second
```

- **경고도 출력이다** — `dead_code` 가 「필드를 읽은 적이 없다」를 짚는다. **해제는 읽기로 안 쳐 준다.**

### 7. `d.drop()` 을 부르면

**출력**

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

**왜 그런가**

- **E0040**, `explicit destructor calls not allowed` 다. `help:` 가 **`drop(d)`** 를 대신 쓰라고 한다.

`rustc --explain E0040`:

> It is not allowed to manually call destructors in Rust.
>
> (…)
>
> It is unnecessary to do this since `drop` is called automatically whenever a
> value goes out of scope. However, if you really need to drop a value by hand,
> you can use the `std::mem::drop` function

- 결정적 차이는 **소유권** 한 낱말이다.
  - `d.drop()` 은 **`&mut self`** 를 받는다 — 자원은 반납됐는데 **`d` 라는 이름은 아직 살아 있다.**\
    그 뒤에 `d` 를 쓰면 반납된 자원을 만지게 되고, 스코프 끝에 **또 한 번 해제**된다.
  - `drop(d)` 는 **값을 먹는다** — 그 순간 `d` 라는 이름이 죽는다(08번의 E0382).
- **`std::mem::drop` 의 몸통은 비어 있다.** 정의가 `pub fn drop<T>(_x: T) {}` 한 줄이다.\
  해제는 「`drop` 이라서」가 아니라 **「먹은 쪽의 몸통이 끝나서」** 일어난다 — 아래 8번 출력의 (2)가 그 재현이다.

```text
   d.drop()                             drop(d)
   = Drop::drop(&mut d) 직접 호출        = 값을 먹는 빈 몸통 함수에 넘긴다
   -> E0040                             -> 그 함수 몸통 끝에서 해제
   d 가 아직 이름으로 살아 있다            d 라는 이름이 죽는다
```

### 8. `Copy` 값을 `drop()` 하면

**출력**

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

**왜 그런가**

- **컴파일된다.** `n` 은 `drop(n)` 뒤에도 **그대로 `7`** 이다 — 먹어 간 것이 **사본**이기 때문이다.
- ★ 컴파일러가 가만히 있지 않는다 — **`dropping_copy_types`** 린트가\
  **`calls to std::mem::drop with a value that implements Copy does nothing`** 이라고 경고한다.
- 제안하는 대안은 **`let _ = n;`** 이다(「값을 버리겠다」는 뜻을 더 정확히 적는 형태).
- (2)가 7번의 답을 재현한다 — **빈 몸통 함수 `my_drop` 이 `drop` 과 똑같이 해제시켰다.** `drop` 에 마법이 없다.
- ★ **`Copy` 타입은 애초에 소멸자를 가질 수 없으므로**(3번의 E0184) `drop()` 이 할 일이 정말로 없다.

### 9. `Copy` 와 `Clone` 의 관계

**왜 그런가**

- **부분집합은 `Copy` 쪽**이다. `pub trait Copy: Clone` 이므로 **모든 `Copy` 타입은 `Clone`** 이다.
- 코드에서 드러나는 차이.

| | `Copy` | `Clone` |
|---|---|---|
| 언제 일어나나 | **대입·인자 전달에서 자동** | **`clone()` 을 내가 부를 때만** |
| 코드에 보이나 | **안 보인다**(`let b = a;`) | **보인다**(`let b = a.clone();`) |
| 비용 신호 | 없음 | ★ **호출 글자가 곧 비용 표시**다 |
| 구현 방법 | 표식만(메서드 없음) | `fn clone(&self) -> Self` 를 쓴다 |

- **`Copy` 인데 `Clone` 이 아닌 타입은 있을 수 없다.** 상위 트레이트 제약이라 E0277 로 막힌다(1번).
- ★ **`Copy` 를 「싸다」로 읽으면 틀린다.** `[u8; 4096]` 도 `Copy` 다 — 4KB 를 통째로 베낀다.\
  `Copy` 가 말하는 것은 「**비트 복사가 의미상 옳다**」뿐이고 **비용은 별개**다.\
  반대로 `Rc` 는 `Clone` 이지만 그 `clone()` 은 정수 하나 증가라 **싸다**(4번). **트레이트와 비용은 직교한다.**

### 10. 크기와 `Copy` 판정

**출력** — 8번 출력의 (4)를 다시 읽는다

```text
    i32      size=4 align=4
    [i32; 3] size=12 align=4
    String   size=24 align=8
    Vec<i32> size=24 align=8
    &i32     size=8 align=8
    D        size=16 align=8
```

**왜 그런가**

- **`Copy` 인 쪽은 `[i32; 3]`**(12바이트)이고 `Vec<i32>`(24바이트)는 아니다.
- 이 대비가 반증하는 것 — **「작으면 `Copy`, 크면 이동」이 아니다.** 갈리는 기준은 **트레이트 하나**다.\
  ★ 08번이 「크기도 힙도 기준이 아니다」라고 한 것의 수치 근거가 이것이다.
- `size_of::<String>()` 과 `size_of::<Vec<i32>>()` 는 **둘 다 24** 다(포인터·길이·용량 세 칸).
- 그 수치는 **플랫폼**(포인터 폭)에 달렸다 — 이 머신은 64비트라 8×3 = 24 다.\
  32비트 타깃에서는 12가 된다. **이 머신에서만 잰 값**으로 읽어야 한다.

```text
   Copy 여부와 크기는 직교한다

   크기 →      4B        12B        24B
   Copy        i32     [i32; 3]      —
   Copy 아님    —          —      Vec<i32> · String
                        ^^^^^^^^
                        Vec<i32> 보다 작은데 Copy 다
```

### 11. 다른 주제와 잇기

- **`Rc::clone` 이 카운트만 올리는 것의 정본** — 목록의 **41번 주제**(`Rc`/`Arc` 공유 소유권).\
  여기서는 `strong_count` 1→2→1 이라는 **현상만** 실었다.
- **`mem::take`/`replace` 의 정본** — 목록의 **44번 주제**.\
  08번의 E0509(`Drop` 구현체에서 필드를 못 빼낸다)로 막힌 자리가 정확히 그 도구의 자리다.
- **`&T` 는 `Copy`, `&mut T` 는 아니다** — 정본은 [**10번 주제**](../10-borrowing-and-aliasing-rules/).\
  그렇게 정한 이유는 **`&mut` 가 `Copy` 면 가변 별칭이 공짜로 생기기 때문**이다.\
  별칭 규칙(공유 다수 **또는** 가변 하나) 자체가 무너진다.
- **E0509 와 해제 순서의 연결** — 둘 다 「**소멸자가 필드를 읽을 수 있어야 한다**」에서 나온다.\
  그래서 `Drop` 타입은 **필드를 못 빼내고**(E0509), 해제할 때 **본체가 먼저**다(6번 실측).\
  한 문장 규칙 — **`Drop` 을 단 값은 쪼갤 수 없는 한 덩어리로 다뤄진다.**
- **에러가 아니라 출력 순서로만 드러나는 사실** — **해제 순서 전부**다.\
  지역 변수 역순 · 필드 선언 순 · `Drop` 구현체의 본체 우선 · 튜플과 `Vec` 원소의 순서 ·\
  함수 인자가 역순인 것. **컴파일러는 이 중 어느 것도 말해 주지 않는다.**\
  `impl Drop` + `println!` 이 유일한 창이다([**08번 주제**](../08-ownership-and-move/)가 세웠다).

---

## 실행 검증

| 실험 (`ex.rs`) | 무엇을 확인했나 | 결과 |
|---|---|---|
| `#[derive(Copy)]` 만 | **E0277** `the trait bound P: Clone is not satisfied` + `required by a bound in Copy` | 1 |
| `#[derive(Clone, Copy)]` + `String` 필드 | **E0204** `this field does not implement Copy` | 2 |
| `rustc --explain E0204` | `&mut T` 는 `Copy` 아님 / `&T` 는 항상 `Copy` — 공식 문장 | 2·11 |
| `#[derive(Clone, Copy)]` + `impl Drop` | **E0184** `the type has a destructor` | 3 |
| `rustc --explain E0184` | `currently` · `for now` · `can lead to memory unsafety` | 3 |
| `Vec::clone` 주소 대조 | 버퍼 **다름**(`false`) | 4 |
| `Rc::clone` 주소 + `strong_count` | 버퍼 **같음**(`true`) · 카운트 **1 → 2 → 1** | 4 |
| `(*r1).clone()` | 버퍼 **다름** — `Rc` 를 벗기면 깊어진다 | 4 |
| `derive(Clone)` vs 손으로 쓴 `impl Clone`(제네릭) | **E0599** `unsatisfied trait bound introduced in this derive macro`. 손으로 쓴 쪽은 **통과** | 5 |
| `Drop` 6장면(지역·필드·`Drop` 구현체·튜플·`Vec`·함수 인자) | 지역 **역순** / 필드·튜플·`Vec` **선언 순** / `Drop` 구현체 **본체 먼저** / 인자 **역순** | 6 |
| `d.drop()` | **E0040** `explicit destructor calls not allowed` + `help: drop(d)` | 7 |
| `rustc --explain E0040` | `std::mem::drop` 을 쓰라는 공식 문장 | 7 |
| `fn my_drop<T>(_x: T) {}` | **`drop` 과 동일하게 해제됨** — `drop` 에 마법이 없다 | 7·8 |
| `drop(n)`(`i32`) | **경고** `dropping_copy_types` · `does nothing` · `n` 은 **그대로 7** | 8 |
| `size_of`/`align_of` 6종 | `i32` 4 · `[i32;3]` 12 · `String` 24 · `Vec<i32>` 24 · `&i32` 8 · `D` 16 | 8·10 |

**구현·설정에 달린 항목**(다시 찍을 자리)

| 항목 | 무엇에 달렸나 |
|---|---|
| **주소 절댓값**(`0x6076...`) | **런타임 ASLR** — 실행마다 바뀐다. 근거는 「같은가/다른가」뿐 |
| `String`·`Vec<i32>` 의 24바이트, `&i32` 의 8바이트 | **플랫폼**(64비트). 포인터 폭이 다르면 달라진다 |
| `D` 의 16바이트 | **구현**(필드 배치). `&'static str` 이 두 칸이라 그렇다 |
| **`Copy` + `Drop` 금지** | **현재 언어 규칙** — `--explain` 이 `currently`·`for now` 라고 적는다 |
| `dropping_copy_types`·`dead_code` 가 **경고**인 것 | **린트 설정**. `-D warnings` 로 에러가 된다 |
| 에러·경고의 **문구와 `help` 제안** | **rustc 구현**. 버전이 오르면 바뀐다 — **에러 번호**가 더 안정적이다 |
| **`Rc::clone` 이 카운트만 올리는 것** | **std 계약**(문서화된 동작). `Clone` 트레이트 자체의 보장은 아니다 |
| **`Copy` 판정·해제 순서 규칙 자체** | **전부 언어 보장.** Reference 의 Destructors 절과 실측이 일치했다 |
