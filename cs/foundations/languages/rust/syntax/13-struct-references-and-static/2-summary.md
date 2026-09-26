# rust/syntax/13 — 구조체에 참조 담기·`'static`의 두 의미 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [The Rust Reference — Lifetime elision](https://doc.rust-lang.org/reference/lifetime-elision.html) ·
> [Reference — Generic parameters](https://doc.rust-lang.org/reference/items/generics.html) ·
> [Reference — Destructors(드롭 순서·drop check)](https://doc.rust-lang.org/reference/destructors.html) ·
> [The Rust Book 10.3](https://doc.rust-lang.org/book/ch10-03-lifetime-syntax.html) ·
> `rustc --explain E0106` / `E0726` / `E0261` / `E0621` / `E0392` / `E0204` / `E0277` / `E0382` / `E0515` / `E0505` / `E0597`.
> ★ `--explain` 은 **확인용으로만 열었고 본문에 옮기지 않았다.** 본문의 진단은 전부 내가 던져서 받은 것이다.
> **실행 검증** — 이 문서의 모든 출력·에러·경고는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 얻은 것이다. `cargo` 는 쓰지 않았다.\
> ★★ **`rustc ex.rs` 만 쓰면 에디션 2015 다.** 이 갈래는 `--edition 2021` 을 반드시 붙인다.\
> 소스 파일 이름은 전부 `ex.rs` 로 고정했고, **진단의 줄 번호는 그 파일 기준**이다.
> **버전** — 구조체에 수명 파라미터를 다는 문법은 1.0.0부터다. `'_`(익명 수명)는 **2018 에디션**부터,\
> `mismatched_lifetime_syntaxes` 경고는 **이 툴체인에서 기본 켜져 있는 것을 실측**했다(rustc 판에 달렸다).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.
>
> ★★ **경계 선언** — `'static` 의 **두 뜻**(`&'static T` 대 `T: 'static`)은\
> [**12번 주제**](../12-lifetime-annotations-and-elision/) **(4)절이 정본**이고, 여기서 다시 쓰지 않는다.\
> 이 주제는 「**그것을 필드로 담을 때 무엇이 따라오나**」다 — 수명 파라미터가 **선언·`impl`·생성 함수·반환 타입·\
> 그 타입을 품는 다른 구조체**까지 **어디까지 번지는가**가 본체다.

## 한눈에 — 쉽게 말하면

**구조체에 남의 물건을 하나라도 넣으면, 그 상자 자체가 「남의 물건이 든 상자」로 이름이 바뀐다.**

[**12번 주제**](../12-lifetime-annotations-and-elision/)가 「**함수 시그니처의 수명 칸을 어떻게 채우나**」였다면,
이 주제는 「**그 칸이 타입 이름에 붙으면 무슨 일이 벌어지나**」다.

| 비유 | 실체 |
|---|---|
| 상자 안에 **빌린 물건**을 하나 넣는다 | 필드가 `&'a T` — **참조 필드** |
| 그 순간 상자 이름이 **「누구에게서 빌렸는지」까지 포함**하게 된다 | `Tag` 가 아니라 **`Tag<'a>`** 가 타입 이름이다 |
| 그 상자를 **더 큰 상자에 넣으면** 큰 상자 이름도 바뀐다 | `struct Doc<'a> { tags: Vec<Tag<'a>> }` — **전파** |
| 큰 상자 겉에는 **빌린 물건이 안 보인다** | `Vec<Tag>` 에 `&` 가 한 글자도 없는데 **E0106** |
| 상자를 **만드는 사람**이 대출증에 서명해야 한다 | `fn new(name: &'a str) -> Self` — **E0621** |
| 상자가 **자기 안의 물건**을 가리킬 수는 없다 | 자기 참조 — **E0515 + E0505** |
| 상자를 **통째로 옮길 수 있어야** 한다 | 이동해도 참조가 살아 있어야 한다는 전제 |
| 빌린 물건만 든 상자는 **복사가 싸다** | 참조 필드 구조체는 **`Copy` 가 된다**(소유 필드는 안 된다) |

- ★★ **수명 파라미터는 타입의 일부**다. `Tag` 와 `Tag<'a>` 는 **다른 글자**이고, `Tag` 만 적으면 컴파일러가 거부한다.
- ★ **한 필드가 타입 전체를 감염시킨다.** 필드 열 개 중 하나만 참조여도 `<'a>` 는 **위 일곱 자리 전부**에 번진다.
- **감염은 「타입 이름을 직접 적은 자리」에만 번진다** — 제네릭 `T` 로 받으면 선언에는 안 번진다((8)).

```text
   필드 하나가 참조이면 <'a> 가 어디까지 번지나

   ① 구조체 선언      struct Tag<'a> { name: &'a str }
                              └┬┘
   ② impl 블록                │      impl<'a> Tag<'a> { … }
   ③ 생성 함수                │      fn new(name: &'a str) -> Self
   ④ 반환 타입                ├────▶ fn wrap(s: &str) -> Tag<'_>
   ⑤ 품는 구조체              │      struct Doc<'a> { tags: Vec<Tag<'a>> }
   ⑥ 그 구조체의 impl         │      impl<'a> Doc<'a> { … }
   ⑦ 그것을 쓰는 함수         └────▶ fn render<'a>(d: &Doc<'a>) -> String

   ★ ⑤ 에는 & 가 한 글자도 안 보이는데 E0106 이 난다.
     「참조를 담았나」는 타입 이름만 봐서는 모른다 — 그래서 컴파일러가 이름을 바꾸라고 한다.
```

> **수명 파라미터(lifetime parameter)** — `'a` 처럼 `<>` 안에 선언하는 이름. 타입 파라미터(`T`)와 같은 자리에 쓴다.\
> 예: `struct Tag<'a>` 의 `'a`. **이 이름은 그 타입을 쓰는 쪽이 고른다.**

> **전파(감염)** — 한 필드가 참조라서 `<'a>` 가 선언·`impl`·시그니처·품는 타입까지 번지는 것.\
> 이 문서에서만 쓰는 말이다(명세 용어가 아니다). 명세 쪽 이름은 **제네릭 파라미터의 전달**이다.

> **참조 필드(reference field)** — 타입이 `&'a T` 또는 `&'a mut T` 인 필드.\
> 그 구조체는 **빌린 값보다 오래 살 수 없다.**

> **자기 참조 구조체(self-referential struct)** — 한 필드가 **같은 값의 다른 필드**를 가리키는 구조체.\
> 안전한 Rust 로는 만들 수 없다((7)).

> **drop check(dropck)** — `Drop` 을 구현한 타입은 **해제 시점에도 필드가 유효해야** 하므로\
> 빌림 검사가 더 엄해진다. `Drop` 을 다는 것만으로 통과하던 코드가 거부될 수 있다((9)).

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **필드 하나를 참조로 바꾸면 `<'a>` 가 어디까지 번지나** — 선언에서 멈추나, 호출부까지 가나.
2. **참조를 품은 타입을 만들고 돌려주려면 시그니처가 어떻게 되나** — `fn new` 는 무엇을 적어야 하나.
3. **왜 자기 자신을 가리키는 구조체는 안 되나** — 표기 문제인가, 원리 문제인가.

★ 12번이 「**시그니처의 수명 칸**」이었다면 여기는 「**타입 이름에 붙은 수명 칸**」이다.
`'static` 의 두 뜻은 **12번이 정본**이고, 여기서는 **필드 자리에서만** 한 번 되짚는다((10)).

## 동작 방식

### (0) 이 주제가 쓰는 네 창

**언제 쓰나** — 아래 모든 절이 이 넷 중 하나로 접지한다.

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| **일부러 던져서 받는 컴파일 에러** | 전파가 멈춘 자리 — E0106·E0726·E0261·E0621·E0392 | 10·11·12번에서 이어받음 |
| **같은 프로그램의 두 판을 나란히 컴파일** | 한 글자 차이가 만드는 제약의 차이 | 12번의 「생략형·명시형 대조」에서 이어받음 |
| ★ **수명 파라미터를 세어서 보인다** | **한 필드가 타입 전체를 감염시킨다**는 것을 **숫자로** | ★ 이 주제의 고유 창 |
| ★ **이동 전후 주소를 대조** | 「값이 이동해도 참조가 살아 있어야 한다」는 전제 | ★ 이 주제의 고유 창 |

★ 세 번째 창이 이 주제의 핵심 도구다. **전파는 「번진다」고 말로 하면 감이 안 온다** —
같은 프로그램을 두 판 써 놓고 `'a` 를 **세면** 19 대 0 이 나온다((6)).

비용 — 없음. 전부 컴파일과 `grep` 뿐이다.

### (1) 전파의 출발점 — 필드에 참조를 적으면

**언제 쓰나** — 구조체 필드에 `&` 를 처음 적을 때.

```text
===== 소스: ex.rs =====
// 전파의 출발점 — 필드에 참조를 적고 수명을 안 쓰면
struct Tag {
    name: &str,
}

fn main() {
    let s = String::from("제목");
    let t = Tag { name: &s };
    println!("{}", t.name);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0106]: missing lifetime specifier
 --> ex.rs:3:11
  |
3 |     name: &str,
  |           ^ expected named lifetime parameter
  |
help: consider introducing a named lifetime parameter
  |
2 ~ struct Tag<'a> {
3 ~     name: &'a str,
  |

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0106`.
```

- ★ **`help:` 에 「어디서 빌렸나」를 묻는 구절이 없다.** 함수 쪽 E0106 은
  `but the signature does not say whether it is borrowed from x or y` 를 달지만((12)의 (1)), **필드 쪽은 그냥 이름을 달라고 한다.**\
  **구조체 필드에는 생략 규칙 2·3이 아예 없기 때문**이다 — 채워 줄 근거 자체가 없다. **생략 규칙의 정본은 12번**이다.
- ★★ **고치는 법이 한 줄이 아니라 두 줄**이라는 점을 보라. `help:` 가 **2번 줄(선언)과 3번 줄(필드)을 같이** 고친다.\
  **여기가 전파의 첫 칸**이다 — 필드 하나를 고치려면 **타입 이름부터 바뀐다.**

### (2) ★★ 전파(감염) — `<'a>` 가 어디까지 번지나

**언제 쓰나** — 참조 필드를 가진 타입을 **쓰기 시작할 때마다.**

`'a` 를 붙여 선언을 고쳤다. 그럼 `impl` 은 어떻게 적어야 하나 — **그냥 `impl Tag` 로 던져 본다.**

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

★ **에러 번호가 E0106 이 아니라 E0726 이다.** 문구도 다르다 —
`implicit elided lifetime **not allowed here**` 는 「빈 칸이 있다」가 아니라 「**이 자리에서는 생략 자체가 금지**」라는 뜻이다.
`impl` 의 대상 타입 자리는 **`'_` 라도 적어야** 한다.

그럼 **품는 구조체**는 어떻게 되나 — `&` 가 한 글자도 안 보이는 자리다.

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

★★ **이것이 이 주제에서 가장 중요한 실측이다.** `Vec<Tag>` 안에는 **`&` 가 한 글자도 없다.**
그런데도 E0106 이 나고, `help:` 는 **`Doc` 의 선언까지 고치라고** 한다.

```text
   「참조를 담았나」는 타입 이름만 봐서 모른다

   struct Tag<'a> { name: &'a str }     ← 여기에 & 가 있다
   struct Doc<'a> { tags: Vec<Tag<'a>> }      ↑
                         └──────┬──────┘      │
                                └─ 여기엔 & 가 없는데 ─┘ 수명은 따라온다

   그래서 Rust 는 「& 를 쓴 자리」가 아니라 「타입 이름」에 수명을 붙인다.
   이름이 계약서고, 계약서는 전염된다.
```

### (3) ★ `impl` 블록의 세 얼굴

**언제 쓰나** — 참조 필드를 가진 타입에 메서드를 달 때마다.

`impl Tag` 는 E0726 이었다. 남은 둘 — `impl<'a> Tag<'a>` 와 `impl Tag<'_>` 는 **둘 다 되나**? 한 파일에 나란히 둔다.

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

★ **둘 다 통과한다.** 같은 타입에 `impl` 블록을 **두 개** 달 수 있고, 형태를 섞어도 된다.

그런데 **둘이 같은 것은 아니다.** `impl Tag<'_>` 안에서 필드의 수명을 내보내려 하면?

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

★★ **E0261 — 「이름이 없다」.** `'_` 는 「**수명이 있긴 하다**」만 적은 것이라 **부를 이름이 없다.**
필드의 수명을 반환값에 실어 내보내려면 **`impl<'a> Tag<'a>` 로 이름을 지어야** 한다.

| 형태 | 컴파일 | 필드 수명을 반환에 실을 수 있나 | 언제 쓰나 |
|---|---|---|---|
| `impl Tag` | ✗ **E0726** | — | 쓸 수 없다 |
| `impl Tag<'_>` | ✓ | ✗ **E0261**(이름이 없다) | 반환이 `self` 에만 묶이면 충분할 때 |
| `impl<'a> Tag<'a>` | ✓ | ✓ `-> &'a str` | **필드의 참조를 내보낼 때** — 기본형 |

★ 판단 규칙 한 줄 — **헷갈리면 `impl<'a> Tag<'a>` 를 쓴다.** 이름을 지어 두면 나중에 필요할 때 부를 수 있고,
`impl Tag<'_>` 는 **나중에 반환 수명이 필요해지는 순간 통째로 고쳐야** 한다.

### (4) ★ 참조 필드를 가진 타입을 반환할 때 — 생성 함수의 시그니처

**언제 쓰나** — `fn new` 를 쓸 때. **여기가 이 주제에서 가장 자주 막히는 자리다.**

먼저 **자유 함수**부터. 반환 타입에서 수명을 생략하면?

```text
===== 소스: ex.rs =====
// 참조 필드를 가진 구조체를 반환할 때 수명을 생략하면?
struct Tag<'a> {
    name: &'a str,
}

fn tag_of(s: &str) -> Tag {
    Tag { name: s }
}

fn main() {
    let s = String::from("제목");
    println!("{}", tag_of(&s).name);
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
제목
(종료 코드 0)
```

★ **함수의 반환 자리는 `impl` 자리와 다르다** — `-> Tag` 는 **컴파일된다.** 경고만 난다.
생략 규칙 2(입력 참조가 하나)가 풀어 주기 때문이다. `impl Tag` 가 **E0726 으로 거부**된 것과 대비된다.

**입력 참조가 둘이면** 그 규칙이 안 돈다 — `'_` 를 적어도 소용없다.

```text
===== 소스: ex.rs =====
// 입력 참조가 둘인데 Tag<'_> 로 반환하면?
struct Tag<'a> {
    name: &'a str,
}

fn longer_tag(a: &str, b: &str) -> Tag<'_> {
    if a.len() >= b.len() { Tag { name: a } } else { Tag { name: b } }
}

fn main() {
    let x = String::from("가나다");
    let y = String::from("라");
    println!("{}", longer_tag(&x, &y).name);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0106]: missing lifetime specifier
 --> ex.rs:6:40
  |
6 | fn longer_tag(a: &str, b: &str) -> Tag<'_> {
  |                  ----     ----         ^^ expected named lifetime parameter
  |
  = help: this function's return type contains a borrowed value, but the signature does not say whether it is borrowed from `a` or `b`
help: consider introducing a named lifetime parameter
  |
6 - fn longer_tag(a: &str, b: &str) -> Tag<'_> {
6 + fn longer_tag<'a>(a: &'a str, b: &'a str) -> Tag<'a> {
  |

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0106`.
```

★ **`'_` 는 「아무거나」가 아니다.** 「**생략 규칙이 푸는 그것**」이라는 뜻이고, 규칙이 못 풀면 그대로 E0106 이다.
여기 `help:` 는 (1)과 달리 **`from a or b` 구절을 단다** — 함수 시그니처라서 물어볼 입력이 있기 때문이다.

이제 **연관 함수 `new`**. `impl<'a> Tag<'a>` 안이라 `Self` 는 이미 `Tag<'a>` 인데, **인자의 수명을 생략하면?**

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

★★ **E0621 — 또 다른 번호다.** 「수명 칸이 비었다」(E0106)도 「생략이 금지된 자리」(E0726)도 아니고,
「**이 인자에는 명시적 수명이 필요하다**」이다. 생략 규칙 1이 `name` 에 **새 이름**을 줬는데,
`Self = Tag<'a>` 는 **`'a` 를 요구**하므로 둘이 안 맞는다.

고치면 통과한다. **생성 함수는 「필드의 수명 = 인자의 수명」을 적어 주는 자리**다.

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

```text
   같은 생성을 세 가지로 적으면

   impl<'a> Tag<'a> { fn new(name: &'a str) -> Self }      ← 인자에 'a 를 적어야 한다 (E0621 회피)
   impl<'a> Tag<'a> { fn new(name: &'a str) -> Tag<'a> }   ← Self 를 펼쳐 적은 것. 같다
   fn tag_of(name: &str) -> Tag<'_>                        ← 자유 함수는 생략 규칙 2 가 푼다

   ★ 연관 함수에 &self 가 없다는 것이 갈림길이다.
     &self 가 없으니 규칙 3 이 안 돌고, Self 가 'a 를 못 박아 놓아 규칙 1 과 충돌한다.
```

### (5) 인자 자리와 반환 자리는 다르다

**언제 쓰나** — 참조 필드 타입을 **받기만** 하는 함수를 쓸 때.

```text
===== 소스: ex.rs =====
// 인자 자리에서는 생략이 되나 — 반환 자리와 갈라 본다
struct Tag<'a> {
    name: &'a str,
}

// 인자 자리: 수명을 안 적어도 된다(규칙 1 이 새 이름을 준다)
fn show(t: &Tag) -> usize { t.name.len() }

// 반환 자리: 입력 참조가 하나뿐이면 규칙 2 가 푼다
fn wrap(s: &str) -> Tag<'_> { Tag { name: s } }

fn main() {
    let s = String::from("제목");
    let t = wrap(&s);
    println!("{} {}", t.name, show(&t));
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
제목 6
(종료 코드 0)
```

★ **`&Tag` 는 경고조차 안 난다.** (4)의 `-> Tag` 가 경고를 받은 것은
**같은 시그니처 안에서 `&str` 은 `&` 로 보이고 `Tag` 는 안 보여** 표기가 섞였기 때문이다.
여기 `show` 는 **입력에만** 나오므로 섞일 것이 없다.

| 자리 | `Tag` 라고만 적으면 | 이유 |
|---|---|---|
| `impl` 의 대상 | ✗ **E0726** | 생략 자체가 금지된 자리 |
| 구조체 **필드** | ✗ **E0106** | 채워 줄 규칙이 없다 |
| 함수 **인자** | ✓ (조용히 통과) | 규칙 1이 새 이름을 준다 |
| 함수 **반환**(입력 참조 1개) | ✓ (`mismatched_lifetime_syntaxes` 경고) | 규칙 2가 푼다 |
| 함수 **반환**(입력 참조 2개) | ✗ **E0106** | 규칙 2·3이 못 푼다 |

### (6) ★★★ 네 번째 창 — 수명 파라미터를 세어서 보인다

**언제 쓰나** — 「참조를 담을까 소유할까」를 고를 때. **비용을 숫자로 보고 싶을 때.**

「번진다」는 말로는 감이 안 온다. **같은 프로그램을 두 판 써 놓고 `'a` 를 센다.**
두 판은 **줄 수가 36줄로 같고, 출력도 한 글자도 같다.** 다른 것은 **필드의 타입 하나뿐**이다.

**판 A — 필드를 `&'a str` 로 둔다**

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
===== grep -o "<'a>" ex.rs | wc -l =====
12
```

**판 B — 필드만 `String` 으로 바꾼다**

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
===== grep -o "<'a>" ex.rs | wc -l =====
0
```

**센 방법과 결과**

| 센 것 | 명령 | 판 A | 판 B |
|---|---|---|---|
| `'a` 토큰 **전부** | `grep -o "'a" ex.rs \| wc -l` | **19** | **0** |
| 그중 `<'a>` 꼴(선언·전달) | `grep -o "<'a>" ex.rs \| wc -l` | **12** | **0** |
| 나머지 `&'a` 꼴(참조 타입) | 19 − 12 | **7** | **0** |
| `'a` 가 **나오는 줄** | `grep -c "'a" ex.rs` | **14 / 36줄** | **0 / 36줄** |

★ **주석에서 `'a` 를 일부러 뺐다.** 두 판 모두 첫 줄 주석에 `'a` 가 안 들어가게 써서
**센 19가 전부 코드**다(처음엔 주석의 `'a` 가 섞여 21·1이 나왔다 — 「도구가 무엇을 보는지」를 먼저 확인한 자리다).

```text
   19 대 0 이 말하는 것

   판 A        판 B
   ──────      ──────
   struct Tag<'a>            struct Tag            ← 선언
   &'a str                   String                ← 필드          ★ 여기 한 글자만 다르다
   impl<'a> Tag<'a>          impl Tag              ← impl
   fn new(&'a str)->Tag<'a>  fn new(String)->Tag   ← 생성 함수
   struct Doc<'a>            struct Doc            ← 품는 구조체
   Vec<Tag<'a>>              Vec<Tag>              ← 그 필드
   impl<'a> Doc<'a>          impl Doc              ← 그 impl
   fn push(Tag<'a>)          fn push(Tag)          ← 그 메서드
   Option<&'a str>           Option<&str>          ← 그 반환
   fn render<'a>(&Doc<'a>)   fn render(&Doc)       ← 쓰는 함수
   Vec<&'a str>              Vec<&str>             ← 그 안의 지역 변수

   36줄 같은 프로그램 · 같은 출력 · 'a 만 19 대 0.
   수명 파라미터는 타입의 일부이고, 한 필드가 타입 전체를 감염시킨다.
```

★★ **판 B 에서 참조가 사라진 것이 아니다.** `fn name(&self) -> &str` 에는 여전히 `&` 가 있다 —
달라진 것은 **생략 규칙 3이 다시 먹히는 자리로 바뀌었다**는 것이다.
**소유로 바꾸면 수명이 없어지는 게 아니라, 수명이 「함수 하나 안」으로 갇힌다.**

### (7) 수명을 하나로 묶을까 갈라 적을까

**언제 쓰나** — 참조 필드가 **둘 이상**일 때.

**판 ① — 하나로 묶는다**

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

**판 ② — 둘로 갈라 적는다. 몸통은 한 글자도 안 고쳤다.**

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

```text
   묶은 판과 갈라 적은 판

   long ├──────────────────────────────────────┤
   tmp          ├────────────────┤

   판 ①  'a = long ∩ tmp = └──────┘            key() 의 반환도 여기까지 -> E0597
   판 ②  'a = long ├──────────────────────────┤ key() 의 반환은 long 까지 -> 통과
          'b = tmp         └────────┘           val 은 tmp 까지만

   ★ 묶는 것은 「간단히 적는 것」이 아니라 「제약을 하나 더 거는 것」이다.
     호출부가 그 제약을 진다.
```

- ★ **기본은 갈라 적는 것이 아니라 묶는 것**이다 — 수명이 늘면 시그니처가 읽기 어려워진다.
- ★★ **호출부가 막히면 그때 가른다.** 막히기 전에 미리 가르면 **읽는 비용만 늘고 얻는 것이 없다.**
- 12번 (10)의 `'long: 'short` 는 **두 수명을 갈라 적고 관계를 다는** 방법이다 — 여기서 갈라 적은 뒤의 다음 수다.

### (8) 전파가 멈추는 자리 — 제네릭으로 받으면

**언제 쓰나** — 참조 필드 타입을 담는 **범용 컨테이너**를 만들 때.

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

★★ **`Wrapper` 선언에는 `'a` 가 한 글자도 없다.** `Vec<Tag<'a>>` 를 필드로 쓴 (2)의 `Doc` 과 대비된다 —
차이는 **타입 이름 `Tag` 를 직접 적었나**다. `T` 로 받으면 수명은 **사용처에서 채워진다.**

- **전파는 「참조를 품었나」가 아니라 「타입 이름을 적었나」로 번진다.**
- ★ 그래서 `Vec<T>`·`Option<T>`·`HashMap<K, V>` 같은 표준 컨테이너는 **선언에 `'a` 가 없는데도**
  `Vec<Tag<'a>>` 를 담을 수 있다. 같은 원리다.
- 다만 **`Wrapper<Tag<'a>>` 라는 구체 타입에는 수명이 들어 있다** — 사라진 것이 아니라 **선언에서 안 보일 뿐**이다.

### (9) 참조 필드와 `Copy`·`Drop` — 09번과 이어지는 자리

**언제 쓰나** — 참조 필드 구조체에 `derive` 를 붙이거나 `Drop` 을 달 때.

**`derive(Debug, Clone, Copy)` 를 던져 본다.**

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

★★ **된다.** `let u = t;` 뒤에도 `t` 가 살아 있다 — **참조 필드 구조체는 `Copy` 가 된다.**
`&T` 자체가 `Copy` 이기 때문이다([**09번 주제**](../09-copy-clone-and-drop/)).

**같은 구조체의 필드를 `String` 으로 바꾸면?**

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

★★ **뒤집혀 있다.** 「참조를 담으면 제약이 늘어난다」가 기본 직감인데, **`Copy` 에서는 참조 판만 된다.**
소유 필드는 해제할 것이 있어 복사가 공짜가 아니고, **참조 필드는 주소 하나라 공짜**다.

**`&'a mut` 이면 또 달라진다.**

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

★ **`Copy` 도 `Clone` 도 안 된다.** `= note:` 가 정확히 말한다 —
`Clone` **is implemented for `&'a u32`, but not for `&'a mut u32`**. 가변 참조를 복제하면 **별칭이 둘**이 되어
10번의 규칙이 깨지기 때문이다([**10번 주제**](../10-borrowing-and-aliasing-rules/)).

그래서 **`&mut` 필드 구조체는 값으로 넘기면 이동한다.**

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

★ 진단이 **`Counter<'_>`** 라고 찍는 것을 보라 — 컴파일러도 **타입 이름에 수명을 붙여** 말한다([**08번 주제**](../08-ownership-and-move/)의 E0382 와 같은 모양이다).

**`Drop` 을 달면 수명 제약이 강해진다.** 먼저 `Drop` 없는 판.

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

**같은 코드에 `Drop` 만 달면?**

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

★★ **`Drop` 을 다는 것만으로 통과하던 코드가 거부된다.** 이것이 **drop check**다.

- `Drop` 이 없으면 **마지막 사용까지만**(NLL) 빌림이 산다 — `t.name` 을 찍은 뒤로는 아무도 안 본다.
- `Drop` 이 있으면 **해제 코드가 `self.name` 을 읽을 수 있으므로** 빌림이 **스코프 끝까지** 살아야 한다.
- `= note: values in a scope are dropped in the opposite order they are defined` 가 **09번의 해제 순서**를 그대로 인용한다 —\
  `t` 를 **먼저 선언**했으니 **나중에 해제**되고, 그때 `s` 는 이미 없다.
- ★ 고치는 법은 **선언 순서를 바꾸는 것**이다(`s` 를 먼저 선언). 표기를 고칠 일이 아니다.

### (10) 필드 자리의 `'static` — 12번을 되짚는 한 칸

**언제 쓰나** — 필드 타입에 `'static` 을 적고 싶을 때.

★★ **`'static` 의 두 뜻은 [**12번 주제**](../12-lifetime-annotations-and-elision/) (4)절이 정본이다.**
여기서는 **필드 자리에서 무엇이 되나**만 한 판 던진다.

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

★ **필드를 `&'static str` 로 못 박으면 `<'a>` 가 사라진다** — `struct Label` 에 수명 파라미터가 없다.
**전파가 멈춘다.** 대신 **넣을 수 있는 값이 리터럴·전역으로 줄어든다.**

| 필드 타입 | 구조체 선언 | 넣을 수 있는 값 | 전파 |
|---|---|---|---|
| `&'a str` | `struct S<'a>` | **아무 `&str`** | 일곱 자리로 **번진다** |
| `&'static str` | `struct S` | 리터럴·전역·누출(`Box::leak`)만 | **안 번진다** |
| `String` | `struct S` | 아무 문자열(복사 비용을 낸다) | **안 번진다** |

★ **`T: 'static`(트레이트 경계)은 이 표의 어느 칸도 아니다** — 그것은 **필드 타입이 아니라 제네릭 경계**이고,
`String` 필드만 있는 `S` 는 그 경계를 **통과**한다. 두 뜻의 대비와 `Holder<'a>` 실측은 **12번 (4)절이 정본**이다.

### (11) ★ 자기 참조 — 왜 원리적으로 못 받나

**언제 쓰나** — 「데이터와 그 안의 슬라이스를 한 구조체에 담고 싶다」는 생각이 들 때.

★★ **처방은 [**11번 주제**](../11-borrow-checker-rejections/)의 「전형 10」이 정본이다**(참조 대신 **인덱스·범위**를 담는다).
여기서는 **왜 원리적으로 못 받는가**를 판다.

**먼저 타입 자체는 멀쩡하다는 것부터 확인한다.**

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

★ **`String` 필드와 참조 필드가 한 구조체에 같이 있는 것은 아무 문제가 없다.**
막히는 것은 **그 참조가 같은 값의 다른 필드를 가리킬 때**뿐이다.

**이제 생성자로 캡슐화해 본다** — 11번은 `let` 한 줄로 만들다 막혔고, 여기서는 **`fn new` 로** 던진다.

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

★★★ **E0505 쪽 진단이 이 절의 답을 글자로 준다.**

```text
 7 | impl<'a> SelfRef<'a> {
   |      -- lifetime `'a` defined here
   ...
   |         returning this value requires that `data` is borrowed for `'a`
```

읽으면 이렇다 — **「`'a` 는 7번 줄에서 정의됐고**(= **호출하는 쪽이 고르는 수명**)**,
그 값을 돌려주려면 `data` 가 `'a` 동안 빌려져 있어야 한다」.**
그런데 `data` 는 **이 함수가 소유한 값**이라 함수가 끝나면 호출자에게 **넘어가 버린다.**
**남에게 준 물건을 「내가 빌려주는 중」이라고 적을 수가 없다.**

```text
   'a 는 누가 고르나

   impl<'a> SelfRef<'a> { fn new(data: String) -> SelfRef<'a> }
        └┬┘                                              └┬┘
         └───── 호출하는 쪽이 고른다 ─────────────────────┘

   ┌── 함수 안 ─────────────────┐
   │  data: String  (이 함수 소유) │
   │  first = &data[..3] ────────┼──▶ 이 참조의 수명은 「data 가 여기 있는 동안」
   └────────────────────────────┘
        │ 반환하면 data 가 호출자에게 간다
        ▼
   호출자가 고른 'a 는 「함수 바깥의 어떤 구간」이다.
   「이 값 자신」을 가리키는 이름이 문법에 없다 — 그래서 적을 수가 없다.
```

**두 번째 이유 — 값이 이동하면 안이 옮겨 간다.** 이동이 무엇을 옮기는지 재 본다.

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
> 이 판에서는 `-O` 를 붙여도 같은 두 줄이 나왔다(세 번 돌려 확인). 그래도 **주소는 최적화·플랫폼에 달린 관찰**이지 보장이 아니다.

- ★ **`String` 의 힙 버퍼가 안 옮겨지는 것은 `String` 의 구현 세부**다. 언어가 「이동해도 힙 주소는 그대로」를 보장하지 않는다.\
  그래서 **컴파일러는 그 운을 근거로 삼을 수 없다.**
- ★★ Rust 는 **모든 값이 언제든 이동할 수 있다**를 전제로 서 있다(이동이 곧 바이트 복사다 — [**08번 주제**](../08-ownership-and-move/)).\
  **자기 참조를 허용하려면 그 전제를 깨야** 하고, 그러면 언어 전체가 달라진다.
- ★ 결론 두 줄 — ① **이름이 없다**(`'a` 는 바깥에서 오는 파라미터라 「자기 자신」을 못 가리킨다) ·\
  ② **이동을 막을 수 없다**(값 안을 가리키는 참조는 이동으로 끊긴다).\
  **`'a` 를 어떻게 적어도 안 된다** — 이건 표기 문제가 아니라 설계 전제 문제다.
- **처방**(인덱스·범위로 바꾸기)은 [**11번 주제**](../11-borrow-checker-rejections/)의 「전형 10」이 정본이다.

### (12) 선언만 하고 안 쓰는 수명 파라미터

**언제 쓰나** — 필드를 소유로 바꿨는데 `<'a>` 를 안 지웠을 때.

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

★ **경고가 아니라 에러다.** 타입 파라미터 `T` 도 같은 E0392 를 낸다 —
**쓰이지 않는 제네릭 파라미터는 타입의 변성(variance)과 drop check 를 정할 수 없어서** 언어가 금지한다.

★ `help:` 가 **`PhantomData` 를 먼저 꺼낸다.** 이 주제에서는 **이름만** 알아 두면 된다(「더 들어가면」).

## 문법 — 형태와 규칙

### 형태

```rust
// 1) 참조 필드 — 선언에 수명 파라미터가 따라붙는다
struct Tag<'a> { name: &'a str }

// 2) 가변 참조 필드
struct Counter<'a> { slot: &'a mut u32 }

// 3) 수명 둘 — 필드마다 출처가 다를 때
struct Pair<'a, 'b> { key: &'a str, val: &'b str }

// 4) impl — 이름을 지어 두는 기본형
impl<'a> Tag<'a> {
    fn new(name: &'a str) -> Self { Tag { name } }   // 생성 함수는 인자에 'a 를 적는다
    fn name(&self) -> &'a str { self.name }          // 필드 수명을 내보낸다
}

// 5) impl — 이름을 안 짓는 판. 반환에 필드 수명을 못 쓴다
impl Tag<'_> {
    fn len(&self) -> usize { self.name.len() }
}

// 6) 반환 타입 — 입력 참조가 하나면 '_ 로 충분하다
fn wrap(s: &str) -> Tag<'_> { Tag { name: s } }

// 7) 품는 구조체 — & 가 안 보여도 번진다
struct Doc<'a> { title: &'a str, tags: Vec<Tag<'a>> }

// 8) 제네릭으로 받으면 선언에는 안 번진다
struct Wrapper<T> { inner: T }

// 9) 'static 으로 못 박으면 수명 파라미터가 사라진다(넣을 값이 줄어든다)
struct Label { text: &'static str }
```

### 금지 사례 — 던져서 받은 아홉

| 코드 | 에러 | 한 줄 |
|---|---|---|
| `struct Tag { name: &str }` | **E0106** | 필드에는 생략 규칙이 **없다** |
| `struct Doc { tags: Vec<Tag> }` | **E0106** | `&` 가 안 보여도 **번진다** |
| `impl Tag { … }`(`Tag<'a>` 에) | **E0726** | `impl` 대상 자리는 **생략 금지**. `'_` 라도 적는다 |
| `impl Tag<'_> { fn f() -> &'a str }` | **E0261** | `'_` 는 **부를 이름이 없다** |
| `fn longer(a: &str, b: &str) -> Tag<'_>` | **E0106** | `'_` 는 「아무거나」가 아니다 |
| `impl<'a> Tag<'a> { fn new(name: &str) -> Self }` | **E0621** | `Self` 는 `'a` 인데 인자가 익명이다 |
| `struct Tag<'a> { name: String }` | **E0392** | 안 쓰는 수명 파라미터는 **에러** |
| `#[derive(Copy)] struct C<'a> { s: &'a mut u32 }` | **E0204 + E0277** | `&mut` 은 `Clone` 도 `Copy` 도 아니다 |
| `impl<'a> SelfRef<'a> { fn new(d: String) -> Self }` | **E0515 + E0505** | 자기 참조 — **원리적으로 못 받는다** |

### 「어디에 무엇을 적나」를 손으로 돌리는 순서

```text
   필드에 & 를 적었다
        │
        ▼
   ① 선언에 <'a> 를 단다                  struct S<'a> { f: &'a T }
        │
        ▼
   ② impl 을 쓰나? ── 예 ──▶ impl<'a> S<'a>  (필드 수명을 반환에 안 쓸 거면 impl S<'_>)
        │
        ▼
   ③ 이 타입을 돌려주는 함수가 있나?
        ├─ 연관 함수(&self 없음) ──▶ 인자에 'a 를 적는다   fn new(x: &'a T) -> Self
        ├─ 자유 함수 · 입력 참조 1개 ──▶ -> S<'_> 로 충분
        └─ 자유 함수 · 입력 참조 2개+ ──▶ <'a> 를 직접 적는다
        │
        ▼
   ④ 이 타입을 필드로 품는 타입이 있나? ── 예 ──▶ 그 타입에도 <'a> 를 단다
        └─ 제네릭 T 로 받으면 안 번진다
        │
        ▼
   ⑤ 참조 필드가 둘 이상인가?
        ├─ 호출부가 안 막힌다 ──▶ 'a 하나로 묶는다(기본)
        └─ 막힌다 ──▶ <'a, 'b> 로 가른다
```

★ **이 순서를 거꾸로 쓰면 「소유로 바꾸는」 절차**가 된다 — 필드를 `String` 으로 바꾸면 ①\~⑤ 가 전부 지워진다((6)의 19 대 0).

## 어디서 틀리나

### 1. ★★ 「참조 필드는 그 구조체 선언에만 영향을 준다」

- 가장 큰 오해다. **일곱 자리**로 번진다 — 선언·`impl`·생성 함수·반환 타입·품는 구조체·그 `impl`·쓰는 함수((2)·(6)).
- 실측: 같은 36줄 프로그램에서 **`'a` 가 19개 대 0개**였다.
- ★ **`Vec<Tag>` 처럼 `&` 가 한 글자도 없는 자리**에서 E0106 이 나는 것이 이 오해가 깨지는 지점이다.

### 2. ★★ 「`impl Tag` 라고 적으면 알아서 채워 준다」

- **E0726** 이다 — `impl` 대상 자리는 **생략 자체가 금지**다. 함수 인자 자리와 다르다((2)·(5)).
- ★ **에러 번호가 E0106 이 아니라는 점**을 보라. 「칸이 비었다」가 아니라 「**여기서는 못 비운다**」다.

### 3. ★ 「`impl Tag<'_>` 와 `impl<'a> Tag<'a>` 는 같다」

- 둘 다 컴파일되지만 **같지 않다.** `'_` 는 **부를 이름이 없어** 필드 수명을 반환에 못 싣는다(**E0261**)((3)).
- 판단 규칙 — **헷갈리면 `impl<'a> Tag<'a>`.** 나중에 필요해지면 그때 부를 수 있다.

### 4. ★★ 「`fn new` 는 인자를 그냥 `&str` 로 받으면 된다」

- **E0621** 이다. `Self = Tag<'a>` 가 `'a` 를 요구하는데 생략 규칙 1이 인자에 **다른 이름**을 준다((4)).
- ★ **`&self` 가 없으니 규칙 3이 안 돈다** — 메서드는 되는데 연관 함수는 안 되는 이유가 이것이다.
- 고치는 법은 **인자에 `'a` 를 적는 것** 한 줄이고, 컴파일러가 그 줄을 그대로 준다.

### 5. ★ 「수명은 하나로 묶는 게 간단하다」

- 묶는 것은 **제약을 하나 더 거는 것**이다 — `'a` 는 **교집합으로 좁아지고** 그 대가는 **호출부가** 낸다((7)).
- 실측: 몸통을 한 글자도 안 고치고 `<'a>` 를 `<'a, 'b>` 로만 바꾸니 **E0597 이 통과로 바뀌었다.**
- ★ 그래도 **기본은 묶는 것**이다. 막히면 그때 가른다 — 미리 가르면 읽는 비용만 는다.

### 6. ★★ 「참조를 담으면 제약이 늘어난다」 — `Copy` 에서는 뒤집힌다

- 참조 필드 구조체는 **`Copy` 가 되고**, 같은 구조체의 필드를 `String` 으로 바꾸면 **E0204** 다((9)).
- ★ `&'a mut` 이면 또 뒤집힌다 — **`Copy` 도 `Clone` 도 안 되고**(E0204 + E0277) 값으로 넘기면 **이동**한다(E0382).
- 외울 것은 번호가 아니라 **「`&T` 는 `Copy`, `&mut T` 는 아니다」** 한 줄이다([**09번 주제**](../09-copy-clone-and-drop/)).

### 7. ★ 「`Drop` 은 해제할 때만 도는 코드다」

- **`Drop` 을 다는 것만으로 빌림 검사가 엄해진다**(drop check). 통과하던 코드가 **E0597** 이 된다((9)).
- `= note: values in a scope are dropped in the opposite order they are defined` 가 이유를 준다.
- 고치는 법은 **선언 순서**다 — 빌려주는 값을 **먼저** 선언한다.

### 8. 「`'a` 를 붙이면 자기 참조가 된다」

- **안 된다.** `fn new` 로 캡슐화하면 **E0515 + E0505** 가 나고, 진단이 이유를 글자로 준다 —\
  `returning this value requires that data is borrowed for 'a` 와 `lifetime 'a defined here`((11)).
- ★ 11번은 `let` 한 줄로 만들다 **E0106 → E0505** 를 받았다. **자리가 달라도 벽은 같다.**
- 처방(인덱스·범위)은 [**11번 주제**](../11-borrow-checker-rejections/)가 정본이다.

### 9. 「필드를 `&'static str` 로 하면 편하다」

- 전파는 멈추지만 **넣을 수 있는 값이 리터럴·전역으로 줄어든다**((10)). 지역 `String` 의 참조는 **E0597** 이다.
- ★ **`T: 'static`(트레이트 경계)과 혼동하지 마라** — 뜻이 다르다. 그 대비는 [**12번 주제**](../12-lifetime-annotations-and-elision/) (4)절이 정본이다.

### 10. 「안 쓰는 `<'a>` 는 그냥 둬도 된다」

- **E0392** 로 컴파일이 깨진다((12)). 경고가 아니다.
- 필드를 소유로 바꿨으면 **`<'a>` 도 같이 지운다** — 감염을 되돌리는 작업은 **선언부터** 한다.

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| 참조 필드가 **선언에 수명 파라미터를 요구**하는 것 | **언어** | `struct Tag { name: &str }` → E0106 |
| **품는 타입까지 번지는** 것 | **언어** | `Vec<Tag>` → E0106 (`&` 가 없는데도) |
| `impl` 대상 자리에서 **생략이 금지**된 것 | **언어** | E0726 — 함수 인자 자리와 다르다 |
| `'_` 가 **이름이 아닌** 것 | **언어** | `impl Tag<'_>` 안에서 `'a` → E0261 |
| 연관 함수 인자에 **명시적 수명이 필요**한 것 | **언어** | E0621 — `Self` 가 `'a` 를 못 박는다 |
| 안 쓰는 수명 파라미터가 **에러**인 것 | **언어**(변성·dropck 결정 불가) | E0392 |
| `&T` 가 **`Copy`**, `&mut T` 가 **아닌** 것 | **언어** | E0204 + E0277 (`note:` 가 명시) |
| `Drop` 이 **빌림 검사를 강화**하는 것(dropck) | **언어** | 같은 코드가 `Drop` 만 달아 E0597 |
| 스코프 안 값이 **선언의 역순으로 해제**되는 것 | **언어** | 진단의 `= note:` 가 그대로 말한다 |
| 자기 참조가 **안 되는 것** | **언어**(모든 값이 이동 가능하다는 전제) | E0515 + E0505 |
| 수명 파라미터가 **런타임에 없는 것** | **언어**(제로 코스트) | [**12번 주제**](../12-lifetime-annotations-and-elision/) (3)의 오브젝트 파일 대조 |
| `mismatched_lifetime_syntaxes` 가 **기본 경고** | **rustc 판** | 이 툴체인(1.92.0) 실측 — 린트는 판마다 승격된다 |
| **에러 번호가 자리마다 갈리는 것** | **rustc 구현** | 같은 「수명이 없다」가 E0106·E0726·E0261·E0621 넷으로 갈린다 |
| `help:` 가 **고친 코드를 통째로 주는** 것 | **rustc 구현** | 문구는 판마다 바뀐다 |
| ★ **`String` 의 힙 버퍼가 이동해도 안 옮겨지는 것** | **`String` 의 구현 세부** | 실측 `true` — 언어가 보장하지 않는다 |
| ★ **값 안에 박힌 배열이 이동하면 주소가 바뀌는 것** | **관찰**(이 빌드·이 플랫폼) | 실측 `false` — `-O` 에서도 같았다 |
| `size_of::<Tag>() == 24` | **플랫폼**(64비트 포인터) | `&str` 16 + `u32` 4 + 정렬 |

★ **「번호가 넷으로 갈린다」가 이 주제의 실용 결론이다** — 같은 「수명이 없다」인데
**E0106**(칸이 비었다) · **E0726**(생략 금지 자리) · **E0261**(이름이 없다) · **E0621**(이 인자에 필요하다) 로 갈린다.
**번호가 곧 「어디를 고칠지」의 이름표**다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 이유 |
|---|---|---|
| 원본을 **잠깐 들여다보는** 뷰 타입(파서·이터레이터·`split` 결과) | **참조 필드** `&'a T` | 복사가 없다. 감염을 감수할 값어치가 있다 |
| 그 타입이 **함수 하나 안에서** 태어나고 죽는다 | **참조 필드** | 감염 범위가 그 함수까지다 |
| 타입을 **저장·반환·스레드 이동**시킨다 | ★ **소유 필드**(`String`·`Vec<T>`) | 감염이 호출부 전체로 번진다. 소유로 끊는다 |
| 필드를 **자기 안의 다른 필드**가 가리켜야 한다 | ★ **인덱스·범위** | 자기 참조는 원리적으로 안 된다 — [**11번 주제**](../11-borrow-checker-rejections/) |
| 값이 **리터럴·전역**뿐이다 | `&'static str` | 감염이 안 번진다. 넣을 값이 줄 뿐 |
| 참조 필드가 둘이고 **호출부가 안 막힌다** | `<'a>` **하나로** | 읽기 쉽다 |
| 참조 필드가 둘이고 **호출부가 막힌다** | `<'a, 'b>` 로 **가른다** | 교집합 제약을 푼다 |
| 필드 수명을 **반환에 실어야** 한다 | `impl<'a> S<'a>` | `impl S<'_>` 로는 **부를 이름이 없다** |
| 참조 필드 타입을 **담기만** 하는 컨테이너 | **제네릭 `T`** | 선언에 감염이 안 번진다 |
| 참조 필드 구조체에 **정리 코드**가 필요하다 | ★ **`Drop` 을 신중히** | dropck 로 수명 제약이 강해진다 |
| 필드를 소유로 되돌렸다 | **`<'a>` 도 같이 지운다** | 안 지우면 **E0392** |

판단 규칙 두 줄.

- ★ **「이 타입이 함수 밖으로 나가나」를 먼저 묻는다.** 나가면 소유, 안 나가면 참조.
- ★ **감염이 세 자리를 넘으면 소유로 바꿀 때다.** (6)의 19 대 0 이 그 비용의 눈금이다.

## 핵심 문장

- ★★ **수명 파라미터는 타입의 일부다.** `Tag` 와 `Tag<'a>` 는 다른 글자이고, **한 필드가 타입 전체를 감염시킨다.**
- ★ **감염은 일곱 자리로 번진다** — 선언 · `impl` · 생성 함수 · 반환 타입 · 품는 구조체 · 그 `impl` · 쓰는 함수.
- ★★ **`&` 가 한 글자도 안 보이는 자리에서도 E0106 이 난다**(`Vec<Tag>`). 타입 이름만 봐서는 참조를 품었는지 모른다.
- ★ **같은 「수명이 없다」가 번호 넷으로 갈린다** — E0106 · E0726 · E0261 · E0621. **번호가 고칠 자리의 이름표**다.
- ★ **`impl` 대상 자리는 생략이 금지**다(E0726). 함수 **인자** 자리는 조용히 통과하고, **반환** 자리는 경고가 난다.
- ★ **`fn new` 는 인자에 `'a` 를 적는 자리**다 — `&self` 가 없어 규칙 3이 안 돌기 때문이다(E0621).
- ★★ **감염은 「타입 이름을 적은 자리」로 번진다** — 제네릭 `T` 로 받으면 선언에는 안 번진다.
- ★ **수명을 묶는 것은 제약을 거는 것**이다. 대가는 호출부가 낸다 — 막히면 갈라 적는다.
- ★★ **참조 필드 구조체는 `Copy` 가 된다.** 소유 필드로 바꾸면 못 된다(E0204) — **직감과 반대다.**
- ★ **`Drop` 을 다는 것만으로 수명 제약이 강해진다**(drop check). 고치는 법은 **선언 순서**다.
- ★★ **자기 참조는 표기 문제가 아니다** — `'a` 는 **바깥에서 오는 이름**이라 자기 자신을 못 가리키고,
  **모든 값이 이동 가능**하다는 전제가 값 안을 가리키는 참조를 못 받는다.
- ★ **필드를 소유로 바꾸면 수명이 사라지는 게 아니라 함수 하나 안으로 갇힌다.**

## 관련 자료

- [`../README.md`](../README.md) — Rust 문법·API 주제 목록(이 주제는 13번)
- [**12번 주제**](../12-lifetime-annotations-and-elision/)(수명 표기 `'a`와 생략 규칙) — ★★ **직접 선행이자 경계.**\
  **그쪽은** 생략 규칙 세 개와 **`'static` 의 두 뜻**(`&'static T` 대 `T: 'static`, `String` 이 경계를 통과하는 것,\
  `Holder<'a>` 가 거부되는 것)까지가 **정본**이다. **여기는** 그 수명 칸이 **타입 이름에 붙었을 때의 전파**부터다.\
  (10)절은 **필드 자리에서만** 한 판 되짚은 것이고, 두 뜻의 대비는 다시 쓰지 않았다
- [**11번 주제**](../11-borrow-checker-rejections/)(빌림 검사기가 거부하는 전형) — ★★ **경계.**\
  **그쪽은** 자기 참조의 **처방**(참조 대신 **인덱스·범위**)이 정본이고 `let` 한 줄로 만들다 막히는 모양을 싣는다.\
  **여기는** **왜 원리적으로 못 받는가**와 **`fn new` 로 캡슐화하려 할 때**의 진단((11))이다
- [**10번 주제**](../10-borrowing-and-aliasing-rules/)(빌림 `&`·`&mut`) — `&mut` 를 복제하면 안 되는 이유가 거기다\
  ((9)의 E0277 `note:` 가 그 규칙의 타입 표면이다)
- [**09번 주제**](../09-copy-clone-and-drop/)(`Copy`·`Clone`·`Drop`) — ★ **(9)절의 짝.**\
  **그쪽은** 어떤 타입이 `Copy` 인가와 **해제 시점**이 정본, **여기는** 그것이 **참조 필드 구조체에서 어떻게 보이나**다
- [**08번 주제**](../08-ownership-and-move/)(소유권과 이동) — **이동이 곧 바이트 복사**라는 전제가 (11)의 뿌리다
- [**14번 주제**](../14-string-vs-str/)(`String` 대 `&str`) — **(6)의 판 A/판 B 선택**을 **함수 인자**에서 다룬다
- [**15번 주제**](../15-slices-ranges-and-utf8-boundaries/)(슬라이스·범위·UTF-8 경계) — (11)의 `&data[..3]` 이 왜 3인지는 거기
- [**16번 주제**](../16-structs-impl-and-associated-functions/)(구조체 세 종류·`impl`·연관 함수) — ★ **경계.**\
  **그쪽은** `impl`·연관 함수·`Self` **일반**, **여기는** 그것들이 **수명 파라미터를 만났을 때**다
- [목록의 **41번 주제**](../41-rc-arc-shared-ownership-and-weak-cycles/)(`Rc`/`Arc`·`Weak`) — 자기 참조·순환을 **런타임 비용을 내고** 푸는 길
- 목록의 **49번 주제**(스레드와 `'static`) · **55번 주제**(`Pin` 맛보기 — 자기 참조 future)
- [`../../언어-특성/README.md`](../../언어-특성/README.md) §4 — **그쪽은** 수명이라는 **개념이 왜 필요한가**,\
  **여기는** 그것이 **타입 선언에 어떻게 박히나**다

## 용어 풀이

- **수명 파라미터(lifetime parameter)** — `'a`. `<>` 안에 선언한다. **그 타입을 쓰는 쪽이 고른다.**
- **참조 필드(reference field)** — `&'a T` · `&'a mut T` 타입의 필드. 그 구조체는 빌린 값보다 오래 못 산다.
- **전파(감염)** — 참조 필드 하나 때문에 `<'a>` 가 선언·`impl`·시그니처·품는 타입까지 번지는 것(이 문서의 말).
- **익명 수명(`'_`)** — 「수명이 있긴 하다」만 적는 표기. **이름이 아니라서 부를 수 없다**(E0261).
- **연관 함수(associated function)** — `impl` 안의 `self` 없는 함수. `Tag::new` 가 그것이다(16번).
- **`Self`** — `impl` 대상 타입의 별명. `impl<'a> Tag<'a>` 안에서 `Self` 는 **`Tag<'a>`** 다.
- **drop check(dropck)** — `Drop` 구현 타입은 **해제 시점에도 필드가 유효해야** 한다는 추가 검사.
- **자기 참조 구조체** — 한 필드가 같은 값의 다른 필드를 가리키는 구조체. 안전한 Rust 로는 못 만든다.
- **변성(variance)** — 수명·타입 파라미터를 더 짧은 것으로 바꿔 쓸 수 있는지의 규칙. E0392 의 배경이다.
- **`PhantomData<T>`** — 크기 0인 표지 타입. 쓰이지 않는 파라미터를 「쓴 것으로」 만든다(E0392 의 `help:`).

---

## 더 들어가면

- ★ **`PhantomData`** — E0392 의 `help:` 가 직접 꺼내는 이름이다. `struct S<'a> { _m: PhantomData<&'a ()> }` 처럼
  **필드 없이 수명만 붙잡아 두는** 표지다. 크기 0이고 런타임에 아무것도 아니다. 여기서는 **이름까지만** 둔다.
- **변성(variance)** — `&'long T` 를 `&'short T` 자리에 쓸 수 있는 것이 공변이고, `&'a mut T` 의 `T` 는 **불변**이다.
  그래서 (9)의 `&mut` 필드 구조체는 수명을 바꿔 끼우는 자유가 `&` 판보다 좁다. 제대로 된 논의는 Reference 의 Subtyping 절이다.
- **`#[may_dangle]`** — 표준 라이브러리의 `Vec`·`Box` 는 이 특별 표지로 dropck 를 완화한다.
  안정판에서 쓸 수 없는 나이틀리 기능이고, **왜 `Vec<&'a T>` 는 `Drop` 이 있는데도 (9)처럼 안 막히나**의 답이 여기 있다.
- **자기 참조를 진짜로 하는 길** — `Pin` + `unsafe`, 또는 `Rc`/`Weak`, 또는 인덱스.
  표준만으로는 **인덱스가 정답**이고(11번), `async` 가 만드는 상태 기계는 **컴파일러가 자기 참조를 만들어 놓고 `Pin` 으로 고정**한다(목록의 **55번 주제**).
- **뷰 타입(view type) 설계** — `&'a str` 필드를 가진 타입을 `Cow<'a, str>` 로 바꾸면 **빌린 것과 소유한 것을 한 타입에** 담을 수 있다.
  감염은 그대로 남지만 **판 A/판 B 를 고르는 시점을 런타임으로 미루는** 수다.
- ★ **감염을 세는 습관** — 리팩토링 전에 `grep -o "'a" src/**.rs | wc -l` 를 한 번 찍어 두면
  **소유로 바꿨을 때 지워질 줄 수**가 먼저 보인다. (6)이 그 눈금이다.
