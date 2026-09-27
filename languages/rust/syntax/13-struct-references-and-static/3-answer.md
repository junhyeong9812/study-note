# rust/syntax/13 — 구조체에 참조 담기·`'static`의 두 의미 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러·경고는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 얻은 것이다. `cargo` 는 쓰지 않았다.\
> ★★ **`--edition` 을 빼면 에디션 2015 다.** 이 문서의 결과는 전부 **2021** 기준이다.\
> 실험 파일 이름은 전부 **`ex.rs`** 로 고정했고, **진단의 줄 번호는 그 파일 기준**이라\
> 질문 쪽 발췌와 어긋날 수 있다. 그래서 **진단을 싣는 블록마다 그 진단을 낸 소스를 같은 자리에** 뒀다.\
> ★ `rustc --explain` 은 **확인용으로만** 열었고 본문에 옮기지 않았다.\
> ★ 이 주제의 고유 창은 **수명 파라미터 세기**(8번)와 **이동 전후 주소 대조**(5번)다.\
> ★★ **`'static` 의 두 뜻**(`&'static T` 대 `T: 'static`)은 [**12번 주제**](../12-lifetime-annotations-and-elision/) **(4)절이 정본**이고,\
> 여기 11번 답은 **필드 자리에서만** 되짚는다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★ 컴파일되지 않는다 — E0726(E0106 이 아니다)

**출력**

```text
===== 소스: ex.rs =====
// 참조 필드를 가진 구조체에 impl 을 수명 없이 적으면?
struct Tag<'a> {
    name: &'a str,
}

impl Tag {
    fn name(&self) -> &str { self.name }
}

fn main() {
    let s = String::from("제목");
    let t = Tag { name: &s };
    println!("{}", t.name());
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0726]: implicit elided lifetime not allowed here
 --> ex.rs:6:6
  |
6 | impl Tag {
  |      ^^^ expected lifetime parameter
  |
help: indicate the anonymous lifetime
  |
6 | impl Tag<'_> {
  |         ++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0726`.
```

**왜 그런가**

- ★ **번호가 E0106 이 아니라 E0726 이다.** 문구를 그대로 읽으면 차이가 보인다 —\
  E0106 은 `missing lifetime specifier`(**칸이 비었다**)이고,\
  E0726 은 `implicit elided lifetime **not allowed here**`(**이 자리에서는 생략 자체가 금지**)다.
- 함수 인자 자리에서는 `&Tag` 라고 써도 조용히 통과한다(생략 규칙 1이 새 이름을 준다).\
  **`impl` 의 대상 타입 자리는 다르다** — 최소한 `'_` 는 적어야 한다.
- **`impl<'a> Tag<'a>` 와 `impl Tag<'_>` 는 둘 다 된다.** 한 타입에 `impl` 블록을 여럿 달 수 있고 형태를 섞어도 된다.

```text
===== 소스: ex.rs =====
// impl<'a> Tag<'a> 와 impl Tag<'_> 가 둘 다 되나 — 한 파일에 나란히 둔다
struct Tag<'a> {
    name: &'a str,
}

impl<'a> Tag<'a> {
    // 필드의 수명을 그대로 내보낸다
    fn name(&self) -> &'a str { self.name }
}

impl Tag<'_> {
    // 이름을 안 짓는 판 — 필드 수명을 내보낼 수는 없다
    fn len(&self) -> usize { self.name.len() }
}

fn main() {
    let s = String::from("제목");
    let t = Tag { name: &s };
    println!("{} {}", t.name(), t.len());
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
제목 6
(종료 코드 0)
```

- ★★ **그렇다고 둘이 같은 것은 아니다.** `impl Tag<'_>` 안에서 필드 수명을 반환에 실으려 하면 막힌다.

```text
===== 소스: ex.rs =====
// impl Tag<'_> 안에서 필드의 수명을 내보내려 하면?
struct Tag<'a> {
    name: &'a str,
}

impl Tag<'_> {
    fn name(&self) -> &'a str { self.name }
}

fn main() {
    let s = String::from("제목");
    let t = Tag { name: &s };
    println!("{}", t.name());
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0261]: use of undeclared lifetime name `'a`
 --> ex.rs:7:24
  |
7 |     fn name(&self) -> &'a str { self.name }
  |                        ^^ undeclared lifetime
  |
help: consider introducing lifetime `'a` here
  |
7 |     fn name<'a>(&self) -> &'a str { self.name }
  |            ++++
help: consider introducing lifetime `'a` here
  |
6 | impl<'a> Tag<'_> {
  |     ++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0261`.
```

- **E0261 — 「이름이 없다」.** `'_` 는 「수명이 있긴 하다」만 적은 표기라 **부를 이름이 아니다.**

| 형태 | 컴파일 | 필드 수명을 반환에 실을 수 있나 |
|---|---|---|
| `impl Tag` | ✗ **E0726** | — |
| `impl Tag<'_>` | ✓ | ✗ **E0261** |
| `impl<'a> Tag<'a>` | ✓ | ✓ `-> &'a str` |

★ 외울 한 줄 — **헷갈리면 `impl<'a> Tag<'a>`.** 이름을 지어 두면 나중에 부를 수 있다.

### 2. ★★ 막히는 것은 `longer_tag` 쪽 하나 — 그리고 경고가 사라진다

**출력**

```text
===== 소스: ex.rs =====
// 질문 2의 파일 그대로 — 두 함수를 한 파일에 두면 무엇이 먼저 나오나
struct Tag<'a> {
    name: &'a str,
}

fn tag_of(s: &str) -> Tag {
    Tag { name: s }
}

fn longer_tag(a: &str, b: &str) -> Tag<'_> {
    if a.len() >= b.len() { Tag { name: a } } else { Tag { name: b } }
}

fn main() {
    let x = String::from("가나다");
    let y = String::from("라");
    println!("{} {}", tag_of(&x).name, longer_tag(&x, &y).name);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0106]: missing lifetime specifier
  --> ex.rs:10:40
   |
10 | fn longer_tag(a: &str, b: &str) -> Tag<'_> {
   |                  ----     ----         ^^ expected named lifetime parameter
   |
   = help: this function's return type contains a borrowed value, but the signature does not say whether it is borrowed from `a` or `b`
help: consider introducing a named lifetime parameter
   |
10 - fn longer_tag(a: &str, b: &str) -> Tag<'_> {
10 + fn longer_tag<'a>(a: &'a str, b: &'a str) -> Tag<'a> {
   |

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0106`.
```

**왜 그런가**

- ★★ **`tag_of` 쪽 경고가 안 보인다.** 에러가 나면 컴파일이 거기서 **중단**되어 린트가 안 돈다.\
  **「경고 0건」을 에러 난 컴파일에서 세면 안 된다** — 고치고 나면 나타난다.
- `longer_tag` 만 고치면 그제야 경고가 나오고 프로그램이 돈다.

```text
===== 소스: ex.rs =====
// longer_tag 만 고치면 — tag_of 의 경고가 그제야 보인다
struct Tag<'a> {
    name: &'a str,
}

fn tag_of(s: &str) -> Tag {
    Tag { name: s }
}

fn longer_tag<'a>(a: &'a str, b: &'a str) -> Tag<'a> {
    if a.len() >= b.len() { Tag { name: a } } else { Tag { name: b } }
}

fn main() {
    let x = String::from("가나다");
    let y = String::from("라");
    println!("{} {}", tag_of(&x).name, longer_tag(&x, &y).name);
}
===== rustc --edition 2021 ex.rs -o ex =====
warning: hiding a lifetime that's elided elsewhere is confusing
 --> ex.rs:6:14
  |
6 | fn tag_of(s: &str) -> Tag {
  |              ^^^^     ^^^ the same lifetime is hidden here
  |              |
  |              the lifetime is elided here
  |
  = help: the same lifetime is referred to in inconsistent ways, making the signature confusing
  = note: `#[warn(mismatched_lifetime_syntaxes)]` on by default
help: use `'_` for type paths
  |
6 | fn tag_of(s: &str) -> Tag<'_> {
  |                          ++++

warning: 1 warning emitted

===== ./ex =====
가나다 가나다
(종료 코드 0)
```

- **`-> Tag` 는 컴파일된다.** 생략 규칙 2(입력 참조가 하나 → 출력에 준다)가 풀기 때문이다.\
  ★ **`impl Tag` 가 E0726 으로 거부된 것과 다른 이유가 이것이다** — `impl` 대상 자리에는 **풀어 줄 규칙이 없다.**
- **경고의 뜻**은 「틀렸다」가 아니라 「**한 시그니처에서 표기를 섞지 마라**」다.\
  `&str` 은 `&` 가 보여 참조인 줄 알겠는데 `Tag` 는 **이름만 봐서는 모른다.** 그래서 `'_` 를 적어 드러내라는 것이다.
- **`'_` 를 적었는데도 막히는 이유** — `'_` 는 「아무거나」가 아니라 「**생략 규칙이 푸는 그것**」이다.\
  입력 참조가 둘이면 규칙 2가 못 돌고, 규칙 3은 `&self` 가 없어 안 돈다 → 그대로 **E0106**.
- **인자 자리의 `&str` 들이 아무 말도 안 듣는 이유** — 생략 규칙 1이 **입력마다 새 이름**을 주기 때문이다.\
  입력 자리는 **언제나 풀린다.** 막히는 것은 늘 **출력 자리**다(12번 (2)의 순서도).

### 3. ★★ 컴파일되지 않는다 — E0621

**출력**

```text
===== 소스: ex.rs =====
// 연관 함수 new 에서 인자의 수명을 생략하면 — Self 는 'a 인데 인자는 익명이다
struct Tag<'a> {
    name: &'a str,
}

impl<'a> Tag<'a> {
    fn new(name: &str) -> Self {
        Tag { name }
    }
}

fn main() {
    let s = String::from("제목");
    println!("{}", Tag::new(&s).name);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0621]: explicit lifetime required in the type of `name`
 --> ex.rs:8:9
  |
8 |         Tag { name }
  |         ^^^^^^^^^^^^ lifetime `'a` required
  |
help: add explicit lifetime `'a` to the type of `name`
  |
7 |     fn new(name: &'a str) -> Self {
  |                   ++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0621`.
```

**왜 그런가**

- ★ **E0621 — 「이 인자에는 명시적 수명이 필요하다」.** E0106(칸이 비었다)도 E0726(생략 금지 자리)도 아니다.\
  **같은 「수명이 없다」가 네 번호로 갈린다**(12번 답 참조).
- **`Self` 가 가리키는 정확한 타입은 `Tag<'a>`** 다. `impl<'a> Tag<'a>` 안이니 `'a` 가 **이미 못 박혀** 있다.
- 그런데 `name: &str` 은 **생략 규칙 1** 이 **다른 새 이름**을 준다. 그 이름은 `'a` 보다 짧을 수 있으므로\
  `Tag { name }` 이 **`Tag<'a>` 가 못 된다.**
- ★★ **`&self` 가 있는 메서드에서는 이 일이 안 일어난다** — 메서드는 `Self` 를 **만들어 반환하지 않고**\
  이미 있는 `self` 를 읽을 뿐이고, 반환에 참조가 있으면 **규칙 3**(`&self` 의 수명)이 풀어 준다.\
  **연관 함수에는 `self` 가 없어 규칙 3이 안 돈다** — 이것이 갈림길이다.
- 고치는 법은 **인자에 `'a` 를 적는 것** 한 줄이고 컴파일러가 그 줄을 그대로 준다.\
  **자유 함수로 쓰면 생략형도 통과한다** — `Self` 라는 못이 없고 입력 참조가 하나뿐이라 규칙 2가 푼다.

```text
===== 소스: ex.rs =====
// 고친 판 — 인자에 'a 를 적으면 통과한다. 생성 함수는 「필드의 수명 = 인자의 수명」을 적는 자리다
struct Tag<'a> {
    name: &'a str,
}

impl<'a> Tag<'a> {
    fn new(name: &'a str) -> Self {
        Tag { name }
    }
}

// 자유 함수로 쓰면 생략형도 된다 — 입력 참조가 하나뿐이라 규칙 2 가 푼다
fn tag_of(name: &str) -> Tag<'_> {
    Tag { name }
}

fn main() {
    let s = String::from("제목");
    println!("{} {}", Tag::new(&s).name, tag_of(&s).name);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
제목 제목
(종료 코드 0)
```

### 4. ★★ 컴파일된다 — 참조 필드 구조체는 `Copy` 가 된다

**출력**

```text
===== 소스: ex.rs =====
// 참조 필드를 가진 구조체에 Debug·Clone·Copy 를 붙이면 되나 — 던져 본다
#[derive(Debug, Clone, Copy)]
struct Tag<'a> {
    name: &'a str,
    hits: u32,
}

fn main() {
    let s = String::from("제목");
    let t = Tag { name: &s, hits: 3 };
    let u = t;                       // Copy 라면 t 가 살아 있어야 한다
    println!("{:?} / {:?}", t, u);
    println!("{} {}", t.name.len(), u.hits);
    println!("size_of = {}", std::mem::size_of::<Tag>());
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
Tag { name: "제목", hits: 3 } / Tag { name: "제목", hits: 3 }
6 3
size_of = 24
(종료 코드 0)
```

**왜 그런가**

- ★★ **`let u = t;` 다음 줄에서 `t` 를 쓸 수 있다.** 이동이 아니라 **복사**였다는 증거다.\
  `&T` 자체가 `Copy` 이므로 필드가 전부 `Copy` 면 구조체도 `Copy` 가 된다([**09번 주제**](../09-copy-clone-and-drop/)).
- **`size_of = 24`** — `&str` 은 **뚱뚱한 포인터**(주소 + 길이)라 **16**, `u32` 가 **4**,\
  정렬이 8이라 **패딩 4** 가 붙어 **16 + 4 + 4 = 24** 다(같은 툴체인에서 `size_of::<&str>()` 가 16, 정렬이 8인 것을 따로 확인했다).
- **필드를 `String` 으로 바꾸면 `Copy` 가 안 된다.**

```text
===== 소스: ex.rs =====
// 같은 구조체의 필드를 String 으로 바꾸면 Copy 가 되나
#[derive(Debug, Clone, Copy)]
struct Tag {
    name: String,
    hits: u32,
}

fn main() {
    let t = Tag { name: String::from("제목"), hits: 3 };
    let u = t.clone();
    println!("{:?} / {:?}", t, u);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0204]: the trait `Copy` cannot be implemented for this type
 --> ex.rs:2:24
  |
2 | #[derive(Debug, Clone, Copy)]
  |                        ^^^^
3 | struct Tag {
4 |     name: String,
  |     ------------ this field does not implement `Copy`

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0204`.
```

- ★★ **직감과 반대다.** 「참조를 담으면 제약이 늘어난다」가 기본 감각인데 **`Copy` 에서는 참조 판만 된다.**\
  소유 필드는 **해제할 것이 있어** 비트 복사가 안전하지 않고, 참조 필드는 **주소뿐이라** 안전하다.
- **`&'a mut u32` 로 바꾸면 에러가 둘**이다.

```text
===== 소스: ex.rs =====
// 참조 필드를 &'a mut 으로 바꾸면 — Copy 가 되나
#[derive(Clone, Copy)]
struct Counter<'a> {
    slot: &'a mut u32,
}

fn main() {
    let mut n = 0u32;
    let c = Counter { slot: &mut n };
    *c.slot += 1;
    println!("{}", n);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0204]: the trait `Copy` cannot be implemented for this type
 --> ex.rs:2:17
  |
2 | #[derive(Clone, Copy)]
  |                 ^^^^
3 | struct Counter<'a> {
4 |     slot: &'a mut u32,
  |     ----------------- this field does not implement `Copy`

error[E0277]: the trait bound `&'a mut u32: Clone` is not satisfied
 --> ex.rs:4:5
  |
2 | #[derive(Clone, Copy)]
  |          ----- in this derive macro expansion
3 | struct Counter<'a> {
4 |     slot: &'a mut u32,
  |     ^^^^^^^^^^^^^^^^^ the trait `Clone` is not implemented for `&'a mut u32`
  |
  = help: the trait `Clone` is implemented for `u32`
  = note: `Clone` is implemented for `&'a u32`, but not for `&'a mut u32`
note: required by a bound in `AssertParamIsClone`
 --> /rustc/ded5c06cf21d2b93bffd5d884aa6e96934ee4234/library/core/src/clone.rs:325:1

error: aborting due to 2 previous errors

Some errors have detailed explanations: E0204, E0277.
For more information about an error, try `rustc --explain E0204`.
```

- ★ **`Clone` 쪽 `= note:` 가 답을 글자로 준다** — `Clone` **is implemented for `&'a u32`, but not for `&'a mut u32`**.\
  가변 참조를 복제하면 **같은 자리를 가리키는 가변 참조가 둘**이 되어 [**10번 주제**](../10-borrowing-and-aliasing-rules/)의 별칭 규칙이 깨진다.
- 그래서 **`&mut` 필드 구조체는 값으로 넘기면 이동**한다.

```text
===== 소스: ex.rs =====
// &'a mut 필드를 가진 구조체는 값으로 넘기면 이동한다 — 두 번 넘겨 본다
struct Counter<'a> {
    slot: &'a mut u32,
}

fn bump(c: Counter) { *c.slot += 1; }

fn main() {
    let mut n = 0u32;
    let c = Counter { slot: &mut n };
    bump(c);
    bump(c);
    println!("{}", n);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0382]: use of moved value: `c`
  --> ex.rs:12:10
   |
10 |     let c = Counter { slot: &mut n };
   |         - move occurs because `c` has type `Counter<'_>`, which does not implement the `Copy` trait
11 |     bump(c);
   |          - value moved here
12 |     bump(c);
   |          ^ value used here after move
   |
note: consider changing this parameter type in function `bump` to borrow instead if owning the value isn't necessary
  --> ex.rs:6:12
   |
 6 | fn bump(c: Counter) { *c.slot += 1; }
   |    ----    ^^^^^^^ this parameter takes ownership of the value
   |    |
   |    in this function
note: if `Counter<'_>` implemented `Clone`, you could clone the value
  --> ex.rs:2:1
   |
 2 | struct Counter<'a> {
   | ^^^^^^^^^^^^^^^^^^ consider implementing `Clone` for this type
...
11 |     bump(c);
   |          - you could clone this value

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0382`.
```

★ 진단이 타입을 **`Counter<'_>`** 라고 찍는다 — 컴파일러도 **수명을 타입 이름의 일부로** 말한다.

### 5. ★★★ 에러 둘 — E0515 + E0505. 표기로는 못 푼다

**출력**

```text
===== 소스: ex.rs =====
// 자기 참조 구조체를 fn new 로 만들려 하면?
struct SelfRef<'a> {
    data: String,
    first: &'a str,
}

impl<'a> SelfRef<'a> {
    fn new(data: String) -> Self {
        let first = &data[..3];
        SelfRef { data, first }
    }
}

fn main() {
    let s = SelfRef::new(String::from("가나다"));
    println!("{} {}", s.data, s.first);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0515]: cannot return value referencing function parameter `data`
  --> ex.rs:10:9
   |
 9 |         let first = &data[..3];
   |                      ---- `data` is borrowed here
10 |         SelfRef { data, first }
   |         ^^^^^^^^^^^^^^^^^^^^^^^ returns a value referencing data owned by the current function

error[E0505]: cannot move out of `data` because it is borrowed
  --> ex.rs:10:19
   |
 7 | impl<'a> SelfRef<'a> {
   |      -- lifetime `'a` defined here
 8 |     fn new(data: String) -> Self {
   |            ---- binding `data` declared here
 9 |         let first = &data[..3];
   |                      ---- borrow of `data` occurs here
10 |         SelfRef { data, first }
   |         ----------^^^^---------
   |         |         |
   |         |         move out of `data` occurs here
   |         returning this value requires that `data` is borrowed for `'a`
   |
help: consider cloning the value if the performance cost is acceptable
   |
 9 |         let first = &data.clone()[..3];
   |                          ++++++++

error: aborting due to 2 previous errors

Some errors have detailed explanations: E0505, E0515.
For more information about an error, try `rustc --explain E0505`.
```

**왜 그런가**

- **에러는 둘** — **E0515**(`cannot return value referencing function parameter`)와 **E0505**(`cannot move out of data because it is borrowed`).
- ★ **`lifetime 'a defined here` 가 가리키는 줄은 7번 줄, 즉 `impl<'a> SelfRef<'a>` 의 `<'a>`** 다.\
  그 줄이 뜻하는 것은 「**`'a` 는 이 타입을 쓰는 쪽이 고르는 이름이다**」다. 함수 안에서 정해지는 것이 아니다.
- ★★ `returning this value requires that data is borrowed for 'a` 를 평서문으로 옮기면 —\
  **「이 값을 돌려주려면 `data` 가 호출자가 고른 구간 내내 빌려져 있어야 한다」.**\
  그런데 `data` 는 **이 함수가 소유한 값**이고 반환과 함께 **호출자에게 넘어간다.**\
  **남에게 준 물건을 「내가 빌려주는 중」이라고 적을 수가 없다** — 그래서 모순이다.
```text
   'a 는 누가 고르나 — 진단 두 줄을 그림으로

   7 | impl<'a> SelfRef<'a> {          "lifetime 'a defined here"
          └┬┘
           └── 이 이름은 호출하는 쪽이 채운다 (함수 바깥의 어떤 구간)

   8 |     fn new(data: String) -> Self {
                   └──┬──┘
                      └── 이 값은 이 함수가 소유한다 (함수가 끝나면 호출자에게 간다)

   10|         SelfRef { data, first }
                         ────  ─────
                         옮긴다  data 를 'a 동안 빌린 채로
                                 "requires that `data` is borrowed for `'a`"

   ★ 남에게 준 물건을 「내가 빌려주는 중」이라고 적을 수가 없다.
```

- **타입 자체는 멀쩡하다.** `first` 를 **바깥 값**으로 돌리면 같은 구조체가 컴파일되고, **통째로 이동도 된다.**

```text
===== 소스: ex.rs =====
// 자기 참조 「타입」 자체는 멀쩡하다 — 바깥 값을 가리키게 하면 통과한다
struct SelfRef<'a> {
    data: String,
    first: &'a str,
}

fn main() {
    let outside = String::from("바깥 문자열");
    let s = SelfRef { data: String::from("안쪽 문자열"), first: &outside[..6] };
    let moved = s;                      // 통째로 옮겨도 된다
    println!("{} / {}", moved.data, moved.first);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
안쪽 문자열 / 바깥
(종료 코드 0)
```

- ★ **막히는 것은 타입이 아니라 「자기 자신을 가리키는 것」뿐**이다. 이유는 둘이다.
  1. **이름이 없다** — `'a` 는 **바깥에서 오는 파라미터**라 「이 값 자신」을 가리킬 수가 없다.
  2. **이동을 막을 수 없다** — Rust 의 모든 값은 언제든 이동할 수 있고(이동 = 바이트 복사, [**08번 주제**](../08-ownership-and-move/)),\
     값 **안**을 가리키는 참조는 그 복사로 **끊긴다.**
- 두 번째 이유를 재 본다 — **이동이 무엇을 옮기나.**

```text
===== 소스: ex.rs =====
// 「값이 이동해도 참조가 살아 있어야 한다」 — 이동이 무엇을 옮기나
fn addr_of_inline(x: &[u8; 8]) -> usize { x.as_ptr() as usize }

fn main() {
    // (1) 구조체 안에 직접 박힌 배열
    let a = [b'a', b'b', b'c', b'd', b'e', b'f', b'g', b'h'];
    let p1 = addr_of_inline(&a);
    let b = a;                          // 이동(Copy)
    let p2 = addr_of_inline(&b);
    println!("배열 필드 — 이동 뒤 주소가 같은가: {}", p1 == p2);

    // (2) String 이 가리키는 힙 버퍼
    let s = String::from("abcdefgh");
    let q1 = s.as_ptr() as usize;
    let t = s;                          // 이동
    let q2 = t.as_ptr() as usize;
    println!("힙 버퍼 — 이동 뒤 주소가 같은가: {}", q1 == q2);
    println!("{}{}", b[0] as char, t.len());
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
배열 필드 — 이동 뒤 주소가 같은가: false
힙 버퍼 — 이동 뒤 주소가 같은가: true
a8
(종료 코드 0)
```

> ★ **대조할 것은 `true`/`false` 자체가 아니라 「값 안에 박힌 것은 이동하면 자리가 바뀌고, 힙 버퍼는 안 바뀐다」는 성질이다.**\
> `-O` 를 붙여 세 번 더 돌려도 두 줄이 같았지만, **주소는 최적화·플랫폼에 달린 관찰**이지 보장이 아니다.

- ★★ **`String` 의 힙 버퍼가 안 옮겨지는 것은 `String` 의 구현 세부**다. 언어가 보장하지 않으므로\
  **컴파일러는 그 운을 근거로 자기 참조를 허용할 수 없다.**
- **처방**(참조 대신 **인덱스·범위**를 담기)은 [**11번 주제**](../11-borrow-checker-rejections/)의 「전형 10」이 정본이다.\
  ★ 11번은 `let` **한 줄**로 만들다 **E0106 → E0505** 를 받았고, 여기는 **생성자로 캡슐화**하려다 **E0515 + E0505** 를 받았다.\
  **자리가 달라도 벽은 같다.**

### 6. ★ `Drop` 을 지우면 통과하고, 달면 E0597 이다 — drop check

**출력** — 먼저 `Drop` 이 없는 판.

```text
===== 소스: ex.rs =====
// 참조 필드 구조체를 「빌린 값보다 먼저 선언」하면 — Drop 이 없을 때
struct Tag<'a> {
    name: &'a str,
}

fn main() {
    let t;                              // 먼저 선언 = 나중에 해제
    let s = String::from("제목");
    t = Tag { name: &s };
    println!("{}", t.name);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
제목
(종료 코드 0)
```

`Drop` 을 달면.

```text
===== 소스: ex.rs =====
// 같은 코드에 Drop 을 달면 — 해제 순서가 검사 대상이 된다
struct Tag<'a> {
    name: &'a str,
}

impl<'a> Drop for Tag<'a> {
    fn drop(&mut self) { println!("Tag 해제: {}", self.name); }
}

fn main() {
    let t;                              // 먼저 선언 = 나중에 해제
    let s = String::from("제목");
    t = Tag { name: &s };
    println!("{}", t.name);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0597]: `s` does not live long enough
  --> ex.rs:13:21
   |
12 |     let s = String::from("제목");
   |         - binding `s` declared here
13 |     t = Tag { name: &s };
   |                     ^^ borrowed value does not live long enough
14 |     println!("{}", t.name);
15 | }
   | -
   | |
   | `s` dropped here while still borrowed
   | borrow might be used here, when `t` is dropped and runs the `Drop` code for type `Tag`
   |
   = note: values in a scope are dropped in the opposite order they are defined

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0597`.
```

**왜 그런가**

- ★★ **`impl Drop` 을 지우면 통과한다.** 한 줄을 더했을 뿐인데 컴파일이 깨진다 — 이것이 **drop check**다.
- `Drop` 이 **없으면** 빌림은 **마지막 사용까지만** 산다(NLL, [**10번 주제**](../10-borrowing-and-aliasing-rules/)).\
  `t.name` 을 찍은 뒤로는 아무도 `s` 를 안 보므로 안전하다.
- `Drop` 이 **있으면** 해제 코드가 `self.name` 을 **읽을 수 있다.** 그래서 빌림이 **스코프 끝까지** 살아야 한다.
- 마지막 줄 — `= note: values in a scope are dropped in the opposite order they are defined`.\
  `t` 를 **먼저 선언**했으니 **나중에 해제**되고, 그 시점에 `s` 는 이미 없다([**09번 주제**](../09-copy-clone-and-drop/)의 해제 순서 그대로다).
- ★ **가장 짧은 고침은 표기가 아니라 선언 순서**다 — `let s` 를 `let t` **앞으로** 옮기면 된다.\
  `'a` 를 어떻게 고쳐도 안 풀린다.

### 7. 일곱 자리로 번진다 — 그리고 제네릭에서 멈춘다

**출력**

| # | 자리 | 적는 모양 |
|---|---|---|
| ① | 구조체 **선언** | `struct Tag<'a> { name: &'a str }` |
| ② | **`impl` 블록** | `impl<'a> Tag<'a> { … }` |
| ③ | **생성 함수**(연관 함수) | `fn new(name: &'a str) -> Self` |
| ④ | **반환 타입** | `fn wrap(s: &str) -> Tag<'_>` |
| ⑤ | 그 타입을 **품는 구조체** | `struct Doc<'a> { tags: Vec<Tag<'a>> }` |
| ⑥ | **그 구조체의 `impl`** | `impl<'a> Doc<'a> { … }` |
| ⑦ | 그것을 **쓰는 함수** | `fn render<'a>(d: &Doc<'a>) -> String` |

**왜 그런가**

- ★★ **`Vec<Tag>` 에는 `&` 가 한 글자도 없는데 막힌다.**

```text
===== 소스: ex.rs =====
// 참조 필드를 가진 구조체를 「필드로 품는」 구조체 — 수명을 안 적으면?
struct Tag<'a> {
    name: &'a str,
}

struct Doc {
    tags: Vec<Tag>,
}

fn main() {
    let s = String::from("제목");
    let d = Doc { tags: vec![Tag { name: &s }] };
    println!("{}", d.tags[0].name);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0106]: missing lifetime specifier
 --> ex.rs:7:15
  |
7 |     tags: Vec<Tag>,
  |               ^^^ expected named lifetime parameter
  |
help: consider introducing a named lifetime parameter
  |
6 ~ struct Doc<'a> {
7 ~     tags: Vec<Tag<'a>>,
  |

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0106`.
```

- **「참조를 담았나」는 타입 이름만 봐서 모른다.** 그래서 Rust 는 `&` 를 쓴 자리가 아니라 **타입 이름**에 수명을 붙이고,\
  그 이름을 쓰는 곳마다 수명이 따라온다. `help:` 가 **`Doc` 의 선언까지** 고치라고 하는 것을 보라.
- **전파가 멈추는 자리** — 타입 이름을 **직접 안 적고 제네릭으로 받으면** 안 번진다.

```text
===== 소스: ex.rs =====
// 감염이 멈추는 자리 — 타입 이름을 직접 안 적고 제네릭으로 받으면
struct Tag<'a> {
    name: &'a str,
}

struct Wrapper<T> {          // 수명 파라미터가 하나도 없다
    inner: T,
}

impl<T> Wrapper<T> {         // 여기도 없다
    fn get(&self) -> &T { &self.inner }
}

fn main() {
    let s = String::from("제목");
    let w = Wrapper { inner: Tag { name: &s } };   // 'a 는 이 자리에서 정해진다
    println!("{}", w.get().name);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
제목
(종료 코드 0)
```

- ★ **`Vec<T>`·`Option<T>` 가 수명 없이 선언돼 있는데도 `Vec<Tag<'a>>` 가 되는 것이 같은 이유다.**\
  수명은 **사용처에서 채워진다.** 다만 `Wrapper<Tag<'a>>` 라는 **구체 타입에는 수명이 들어 있다** —\
  **사라진 것이 아니라 선언에서 안 보일 뿐**이다.
- **전파는 「참조를 품었나」가 아니라 「타입 이름을 적었나」로 번진다.**

### 8. ★★★ 19 대 0 — 한 필드가 타입 전체를 감염시킨다

**출력** — 판 A(필드가 참조).

```text
===== 소스: ex.rs =====
// 판 A — 필드를 참조로 둔다. 판 B 와 같은 프로그램이고 수명 파라미터만 다르다
struct Tag<'a> {
    name: &'a str,
}

impl<'a> Tag<'a> {
    fn new(name: &'a str) -> Tag<'a> { Tag { name } }
    fn name(&self) -> &'a str { self.name }
}

struct Doc<'a> {
    title: &'a str,
    tags: Vec<Tag<'a>>,
}

impl<'a> Doc<'a> {
    fn new(title: &'a str) -> Doc<'a> { Doc { title, tags: Vec::new() } }
    fn push(&mut self, t: Tag<'a>) { self.tags.push(t); }
    fn first_tag(&self) -> Option<&'a str> { self.tags.first().map(|t| t.name()) }
}

fn render<'a>(d: &Doc<'a>) -> String {
    let names: Vec<&'a str> = d.tags.iter().map(|t| t.name()).collect();
    format!("{} [{}]", d.title, names.join(","))
}

fn main() {
    let title = String::from("보고서");
    let a = String::from("긴급");
    let b = String::from("내부");
    let mut d = Doc::new(&title);
    d.push(Tag::new(&a));
    d.push(Tag::new(&b));
    println!("{}", render(&d));
    println!("{:?}", d.first_tag());
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
보고서 [긴급,내부]
Some("긴급")
(종료 코드 0)
===== grep -o "'a" ex.rs | wc -l =====
19
===== grep -c "'a" ex.rs =====
14
```

판 B(필드가 `String`).

```text
===== 소스: ex.rs =====
// 판 B — 같은 프로그램에서 필드만 String 으로 바꿨다. 수명 파라미터가 몇 개 남나
struct Tag {
    name: String,
}

impl Tag {
    fn new(name: String) -> Tag { Tag { name } }
    fn name(&self) -> &str { &self.name }
}

struct Doc {
    title: String,
    tags: Vec<Tag>,
}

impl Doc {
    fn new(title: String) -> Doc { Doc { title, tags: Vec::new() } }
    fn push(&mut self, t: Tag) { self.tags.push(t); }
    fn first_tag(&self) -> Option<&str> { self.tags.first().map(|t| t.name()) }
}

fn render(d: &Doc) -> String {
    let names: Vec<&str> = d.tags.iter().map(|t| t.name()).collect();
    format!("{} [{}]", d.title, names.join(","))
}

fn main() {
    let title = String::from("보고서");
    let a = String::from("긴급");
    let b = String::from("내부");
    let mut d = Doc::new(title);
    d.push(Tag::new(a));
    d.push(Tag::new(b));
    println!("{}", render(&d));
    println!("{:?}", d.first_tag());
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
보고서 [긴급,내부]
Some("긴급")
(종료 코드 0)
===== grep -o "'a" ex.rs | wc -l =====
0
===== grep -c "'a" ex.rs =====
0
```

**왜 그런가**

| 센 것 | 명령 | 판 A | 판 B |
|---|---|---|---|
| `'a` 토큰 **전부** | `grep -o "'a" ex.rs \| wc -l` | **19** | **0** |
| 그중 `<'a>` 꼴(선언·전달) | `grep -o "<'a>" ex.rs \| wc -l` | **12** | **0** |
| 나머지 `&'a` 꼴(참조 타입) | 19 − 12 | **7** | **0** |
| `'a` 가 **나오는 줄 수** | `grep -c "'a" ex.rs` | **14** | **0** |
| 전체 줄 수 | `wc -l` | **36** | **36** |

```text
   같은 자리, 두 판

   판 A                        판 B
   ────────────────────        ────────────────────
   struct Tag<'a>              struct Tag
       name: &'a str               name: String      ★ 다른 것은 이 한 줄뿐
   impl<'a> Tag<'a>            impl Tag
     fn new(&'a str)->Tag<'a>    fn new(String)->Tag
     fn name(&self)->&'a str     fn name(&self)->&str
   struct Doc<'a>              struct Doc
       title: &'a str              title: String
       tags: Vec<Tag<'a>>          tags: Vec<Tag>
   impl<'a> Doc<'a>            impl Doc
     fn new(&'a str)->Doc<'a>    fn new(String)->Doc
     fn push(Tag<'a>)            fn push(Tag)
     fn first_tag()->…&'a str    fn first_tag()->…&str
   fn render<'a>(&Doc<'a>)     fn render(&Doc)
       Vec<&'a str>                Vec<&str>

   36줄 · 같은 출력 · 'a 가 19 대 0.
```

- ★★ **줄 수가 36으로 같고 출력이 한 글자도 같은데 `'a` 만 19 대 0**이다.\
  달라진 것은 **필드 타입 하나**뿐이다(`&'a str` → `String`).
- ★ **`grep -c` 는 줄 수를 센다** — 한 줄에 `'a` 가 둘 있으면 **1로 센다.**\
  실측에서 `grep -o … | wc -l` 이 19, `grep -c` 가 14 로 **다섯 개 차이**가 났다.\
  **출현 수를 세려면 `-o` 로 쪼개서 세야 한다.**
- ★ 두 판 모두 **첫 줄 주석에서 `'a` 를 일부러 뺐다** — 처음엔 주석의 `'a` 가 섞여 21·1이 나왔다.\
  **「도구가 무엇을 보는지」를 먼저 확인한 자리**다.
- ★★ **판 B 에서 참조가 사라진 것이 아니다.** `fn name(&self) -> &str` 도 `Vec<&str>` 도 참조다.\
  달라진 것은 **생략 규칙 2·3이 다시 먹히는 자리로 바뀌었다**는 것이다 —\
  **소유로 바꾸면 수명이 없어지는 게 아니라 「함수 하나 안」으로 갇힌다.**
- **19가 이 선택의 눈금**이다. 참조로 두면 그만큼의 표기와 제약을 **호출부까지** 지고 가고, 소유로 두면 **복사 비용**을 낸다.

### 9. `'a` 하나는 교집합이다 — 갈라 적으면 풀린다

**출력** — 묶은 판.

```text
===== 소스: ex.rs =====
// 두 참조 필드를 수명 하나로 묶은 판 — 호출부에서 무엇이 달라지나
struct Pair<'a> {
    key: &'a str,
    val: &'a str,
}

impl<'a> Pair<'a> {
    fn key(&self) -> &'a str { self.key }
}

fn main() {
    let long = String::from("오래 사는 키");
    let k;
    {
        let tmp = String::from("잠깐 사는 값");
        let p = Pair { key: &long, val: &tmp };
        println!("안에서: {}", p.val);
        k = p.key();
    }
    println!("밖에서: {}", k);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0597]: `tmp` does not live long enough
  --> ex.rs:16:41
   |
15 |         let tmp = String::from("잠깐 사는 값");
   |             --- binding `tmp` declared here
16 |         let p = Pair { key: &long, val: &tmp };
   |                                         ^^^^ borrowed value does not live long enough
...
19 |     }
   |     - `tmp` dropped here while still borrowed
20 |     println!("밖에서: {}", k);
   |                            - borrow later used here

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0597`.
```

몸통을 한 글자도 안 고치고 수명만 갈라 적은 판.

```text
===== 소스: ex.rs =====
// 같은 코드에서 수명만 둘로 갈라 적은 판
struct Pair<'a, 'b> {
    key: &'a str,
    val: &'b str,
}

impl<'a, 'b> Pair<'a, 'b> {
    fn key(&self) -> &'a str { self.key }
}

fn main() {
    let long = String::from("오래 사는 키");
    let k;
    {
        let tmp = String::from("잠깐 사는 값");
        let p = Pair { key: &long, val: &tmp };
        println!("안에서: {}", p.val);
        k = p.key();
    }
    println!("밖에서: {}", k);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
안에서: 잠깐 사는 값
밖에서: 오래 사는 키
(종료 코드 0)
```

**왜 그런가**

- **`'a` 하나로 묶으면 그것은 두 입력의 교집합**이 된다 — `long` 과 `tmp` 중 **짧은 쪽**에 맞춰진다.\
  그래서 `key()` 가 돌려준 참조도 **안쪽 블록까지**만 살고, 밖에서 쓰면 E0597 이다(12번 (6)과 같은 구조).
- **갈라 적으면 `key` 는 `'a`(= `long`), `val` 은 `'b`(= `tmp`) 로 따로 묶인다.**\
  `key()` 의 반환이 `&'a str` 이므로 `tmp` 가 죽어도 살아 있다. **풀린 것은 「둘이 같은 구간이어야 한다」는 제약**이다.
- ★★ **그래도 처음부터 갈라 적는 것이 늘 이득은 아니다.** 수명이 늘면 시그니처가 읽기 어려워지고,\
  그 타입을 쓰는 **모든 자리**에 파라미터가 하나 더 따라다닌다(7번의 일곱 자리 × 2).\
  **기본은 묶고, 호출부가 막히면 그때 가른다.**
- **12번 (10)의 `'long: 'short` 는 갈라 적은 뒤의 다음 수**다 — 갈라 놓고 **둘 사이의 관계**를 선언해\
  `&'long str` 을 `&'short str` 자리에 쓸 수 있게 한다.

### 10. 에러다 — E0392

**출력**

```text
===== 소스: ex.rs =====
// <'a> 를 선언해 놓고 필드 어디에도 안 쓰면?
struct Tag<'a> {
    name: String,
}

fn main() {
    let t = Tag { name: String::from("제목") };
    println!("{}", t.name);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0392]: lifetime parameter `'a` is never used
 --> ex.rs:2:12
  |
2 | struct Tag<'a> {
  |            ^^ unused lifetime parameter
  |
  = help: consider removing `'a`, referring to it in a field, or using a marker such as `PhantomData`

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0392`.
```

**왜 그런가**

- ★ **경고가 아니라 에러다.** 쓰이지 않는 함수 인자는 경고인데 **쓰이지 않는 제네릭 파라미터는 컴파일을 깬다.**
- 이유는 **변성(variance)과 drop check** 다. 필드 어디에도 안 쓰이면 컴파일러가\
  **그 파라미터를 더 짧은 것으로 바꿔 써도 되는지**(변성)와 **해제 시점에 유효해야 하는지**(dropck)를 **정할 근거가 없다.**\
  「아무거나로 두자」는 답이 없으므로 언어가 **선언 자체를 금지**한다.
- `help:` 가 제안하는 **세 가지** — ① `'a` 를 **지운다** ② 어떤 **필드에서 쓴다** ③ **`PhantomData` 같은 표지**를 쓴다.\
  ★ **`PhantomData` 가 컴파일러 입에서 먼저 나온다.** 이 주제에서는 **이름까지만** 알아 둔다(2-summary 의 「더 들어가면」).
- ★ **리팩토링 순서** — 참조 필드를 소유 필드로 되돌릴 때 **가장 먼저 지울 것**은 「선언의 `<'a>`」가 아니라 「**필드의 `&'a`**」다.\
  필드부터 고치면 E0392 가 **남은 `<'a>` 를 전부 짚어 준다** — 컴파일러를 체크리스트로 쓴다.

### 11. `&'static str` 필드는 수명 파라미터를 지우는 대신 값을 줄인다

**출력**

```text
===== 소스: ex.rs =====
// 필드를 &'static str 로 못 박으면 — 리터럴은 되고 지역 String 의 참조는?
struct Label {
    text: &'static str,
}

fn main() {
    let a = Label { text: "리터럴" };      // 통과한다
    println!("{}", a.text);

    let owned = String::from("지역 문자열");
    let b = Label { text: &owned };        // 여기는?
    println!("{}", b.text);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0597]: `owned` does not live long enough
  --> ex.rs:11:27
   |
10 |     let owned = String::from("지역 문자열");
   |         ----- binding `owned` declared here
11 |     let b = Label { text: &owned };        // 여기는?
   |                           ^^^^^^
   |                           |
   |                           borrowed value does not live long enough
   |                           this usage requires that `owned` is borrowed for `'static`
12 |     println!("{}", b.text);
13 | }
   | - `owned` dropped here while still borrowed

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0597`.
```

**왜 그런가**

- ★ **`struct Label` 에 `<'a>` 가 없다.** 수명을 **`'static` 으로 못 박았으니** 고를 것이 없고, **전파가 멈춘다.**
- 대신 **넣을 수 있는 값이 줄어든다.** 라벨 한 줄이 그것을 말한다 —\
  `this usage requires that owned is borrowed for 'static`.

| 필드 타입 | 구조체 선언 | 넣을 수 있는 값 | 전파 |
|---|---|---|---|
| `&'a str` | `struct S<'a>` | **아무 `&str`** | 일곱 자리로 **번진다** |
| `&'static str` | `struct S` | 리터럴 · 전역 · `Box::leak` 로 누출한 것 | **안 번진다** |
| `String` | `struct S` | 아무 문자열(복사 비용을 낸다) | **안 번진다** |

- ★★ **`T: 'static`(트레이트 경계)은 이 표의 어느 칸도 아니다.** 그것은 **필드 타입이 아니라 제네릭 경계**이고,\
  `String` 필드만 있는 `S` 는 그 경계를 **통과**한다.\
  두 뜻의 대비(`&'static T` 대 `T: 'static`, `String` 이 경계를 통과하는 것, `Holder<'a>` 가 거부되는 것)는\
  **[**12번 주제**](../12-lifetime-annotations-and-elision/) (4)절이 정본**이고 여기서 다시 쓰지 않는다.

### 12. 번호 지도와 경계

**출력**

| 번호 | 어느 자리에서 나나 | 이 주제의 실측 |
|---|---|---|
| **E0106** | **필드**·**반환 타입**의 수명 칸이 비었다 | 2·7번 (`&str` 필드 · `Vec<Tag>` · `-> Tag<'_>` 인데 입력 둘) |
| **E0726** | **`impl` 대상 타입** — 생략 자체가 금지된 자리 | 1번 |
| **E0261** | `'_` 로 적은 `impl` 안에서 **이름을 불렀다** | 1번 |
| **E0621** | **연관 함수 인자** — `Self` 가 `'a` 를 요구한다 | 3번 |
| **E0392** | 수명 파라미터를 **선언만 하고 안 썼다** | 10번 |
| **E0204 · E0277** | `Copy`/`Clone` 이 **필드 때문에** 안 된다 | 4번 (`String` · `&mut`) |
| **E0382** | `Copy` 가 아닌 구조체를 **두 번 넘겼다** | 4번 |
| **E0597** | 빌린 값이 **먼저 죽는다** | 6·9·11번 (dropck · 교집합 · `'static` 필드) |
| **E0515 · E0505** | **자기 참조** — 소유한 값을 빌린 채로 내보낸다 | 5번 |

**왜 그런가**

- ★★ **같은 「수명이 없다」가 넷으로 갈린다** — **E0106**(칸이 비었다) · **E0726**(생략 금지 자리) ·\
  **E0261**(부를 이름이 없다) · **E0621**(이 인자에 필요하다). **번호가 곧 「어디를 고칠지」의 이름표**다.
- **자기 참조의 처방**은 [**11번 주제**](../11-borrow-checker-rejections/)가 정본이다(참조 대신 **인덱스·범위**).\
  이 주제가 더한 것은 **① 왜 원리적으로 못 받는가**(`'a` 는 바깥에서 오는 이름 + 모든 값은 이동 가능)와\
  **② 생성자(`fn new`)로 캡슐화하려 할 때의 진단**(E0515 + E0505)이다.
- **`&T` 는 `Copy`, `&mut T` 는 아니다** — 정본은 [**09번 주제**](../09-copy-clone-and-drop/)다.\
  **해제 순서**(`= note:` 의 「선언의 역순」)도 거기가 정본이다.
- **값이 이동하면 바이트가 복사된다** — 정본은 [**08번 주제**](../08-ownership-and-move/)다. 5번 답의 전제가 그것이다.
- **함수 인자를 `String` 으로 받을까 `&str` 로 받을까** — [**14번 주제**](../14-string-vs-str/)다.\
  8번 답의 **판 A / 판 B 선택을 함수 표면에서** 다룬다.
- 곁들여 — **슬라이스 `&data[..3]` 의 바이트 경계**는 [**15번 주제**](../15-slices-ranges-and-utf8-boundaries/),\
  **`impl`·연관 함수·`Self` 일반**은 [**16번 주제**](../16-structs-impl-and-associated-functions/)가 정본이다.

---

## 실행 검증

| 실험 (`ex.rs`) | 무엇을 확인했나 | 결과 |
|---|---|---|
| `struct Tag { name: &str }` | **E0106** — 필드에는 생략 규칙이 없다 | 2-summary (1) |
| `impl Tag { … }`(`Tag<'a>` 에) | **E0726** — `impl` 대상 자리는 생략 금지 | 1 |
| `impl<'a> Tag<'a>` + `impl Tag<'_>` 한 파일 | **통과** — `제목 6` (둘 다 되고 섞어도 된다) | 1 |
| ★ `impl Tag<'_>` 안에서 `-> &'a str` | **E0261** — `'_` 는 부를 이름이 아니다 | 1 |
| `struct Doc { tags: Vec<Tag> }` | **E0106** — `&` 가 없는데도 번진다 | 7 |
| `struct Wrapper<T> { inner: T }` | **통과** — 제네릭에서 전파가 멈춘다 | 7 |
| `fn tag_of(s: &str) -> Tag` | **통과 + `mismatched_lifetime_syntaxes` 경고** | 2 |
| `fn longer_tag(a,b) -> Tag<'_>` | **E0106** — `'_` 는 「아무거나」가 아니다 | 2 |
| ★ 두 함수를 한 파일에 | **E0106 만 나오고 경고는 안 보인다**(컴파일 중단) | 2 |
| `fn show(t: &Tag) -> usize` | **통과** — 인자 자리는 조용하다 | 2-summary (5) |
| `impl<'a> Tag<'a> { fn new(name: &str) -> Self }` | **E0621** — `Self` 가 `'a` 를 요구한다 | 3 |
| `fn new(name: &'a str) -> Self` + `tag_of` | **통과** — `제목 제목` | 3 |
| `#[derive(Debug, Clone, Copy)]` + `&'a str` | **통과** — `Copy` 가 된다 · `size_of = 24` | 4 |
| 같은 구조체의 필드를 `String` 으로 | **E0204** — `Copy` 가 안 된다 | 4 |
| 필드를 `&'a mut u32` 로 | **E0204 + E0277** — `Clone` 도 안 된다 | 4 |
| `&mut` 필드 구조체를 두 번 넘기기 | **E0382** — 타입이 `Counter<'_>` 로 찍힌다 | 4 |
| ★ `impl<'a> SelfRef<'a> { fn new(d: String) }` | **E0515 + E0505** — `'a` 는 바깥에서 온다 | 5 |
| `SelfRef` 에 **바깥** 값을 넣고 이동 | **통과** — 타입 자체는 멀쩡하다 | 5 |
| ★ 이동 전후 **주소 대조** | 배열 `false` / 힙 버퍼 `true`(성질이 대조 대상) | 5 |
| 참조 필드 구조체 + **`Drop` 없음** | **통과** — `제목` | 6 |
| ★ 같은 코드 + **`Drop` 있음** | **E0597** + `= note:` 해제 역순 (drop check) | 6 |
| ★ **판 A** — 필드가 참조, 36줄 | **통과** · `'a` **19개** · 줄 기준 **14** | 8 |
| ★ **판 B** — 필드가 `String`, 36줄 | **통과**(출력 동일) · `'a` **0개** | 8 |
| `Pair<'a>` (묶은 판) | **E0597** — `'a` 는 교집합 | 9 |
| `Pair<'a, 'b>` (갈라 적은 판) | **통과** — 몸통은 한 글자도 안 고쳤다 | 9 |
| `struct Tag<'a> { name: String }` | **E0392** — 경고가 아니라 에러 | 10 |
| `struct Label { text: &'static str }` | 리터럴 **통과** / 지역 `&String` **E0597** | 11 |

**구현·설정에 달린 항목**(다시 찍을 자리)

| 항목 | 무엇에 달렸나 |
|---|---|
| **에러 번호가 자리마다 갈리는 것** | **rustc 구현**. 번호는 안정적이고 **문구·`help` 는 바뀐다** |
| `mismatched_lifetime_syntaxes` 가 **기본 경고** | **rustc 판** — 린트는 판마다 추가·승격된다 |
| E0277 의 `note: required by a bound in AssertParamIsClone` **경로** | **rustc 커밋 해시가 박힌다**(`/rustc/ded5c06c…/library/core/src/clone.rs:325:1`) |
| `size_of::<Tag>() == 24` | **플랫폼**(64비트 포인터). `&str` 16 + `u32` 4 + 패딩 4 |
| ★ **이동 뒤 주소 비교의 `true`/`false`** | **최적화·플랫폼**. `-O` 에서도 같았지만 **관찰이지 보장이 아니다** |
| ★ **`String` 힙 버퍼가 이동해도 안 옮겨지는 것** | **`String` 의 구현 세부** — 언어가 보장하지 않는다 |
| `grep` 로 센 `'a` 개수 | **소스를 한 글자라도 고치면 바뀐다**. 센 명령을 같이 실었다 |
| **전파·E0106/E0726/E0261/E0621/E0392·dropck·자기 참조 금지** | **전부 언어 보장.** 실측과 Reference 가 일치했다 |
