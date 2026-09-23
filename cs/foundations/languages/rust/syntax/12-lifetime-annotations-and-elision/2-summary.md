# rust/syntax/12 — 수명 표기 `'a`와 생략 규칙 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [The Rust Reference — Lifetime elision](https://doc.rust-lang.org/reference/lifetime-elision.html) ·
> [Reference — Trait and lifetime bounds](https://doc.rust-lang.org/reference/trait-bounds.html) ·
> [Reference — Destructors(임시값 수명 연장)](https://doc.rust-lang.org/reference/destructors.html) ·
> [The Rust Book 10.3](https://doc.rust-lang.org/book/ch10-03-lifetime-syntax.html) ·
> `rustc --explain E0106` / `E0597` / `E0505` / `E0499` / `E0515` / `E0716`.
> ★ `--explain` 은 **확인용으로만 열었고 본문에 옮기지 않았다.** 본문의 진단은 전부 내가 던져서 받은 것이다.
> **실행 검증** — 이 문서의 모든 출력·에러·경고는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 얻은 것이다. `cargo` 는 쓰지 않았다.\
> ★★ **`rustc ex.rs` 만 쓰면 에디션 2015 다.** 이 갈래는 `--edition 2021` 을 반드시 붙인다 —\
> 붙이지 않으면 **다른 언어를 컴파일하는 셈**이고, 이 주제에는 **2021 에서 거부되고 2024 에서 통과하는 파일**이 실제로 있다(아래 (8)).\
> 소스 파일 이름은 전부 `ex.rs` 로 고정했고, **진단의 줄 번호는 그 파일 기준**이다.
> **버전** — 수명 생략 규칙 세 개는 1.0.0부터다. `'_`(익명 수명)는 **2018 에디션**부터 쓸 수 있고,\
> `mismatched_lifetime_syntaxes` 경고는 **이 툴체인에서 기본 켜져 있는 것을 실측**했다(rustc 판에 달렸다 — 아래 「구현 세부사항 대 언어 보장」).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**빌린 물건에는 「누구한테서 빌렸는지」가 적혀 있어야 반납할 자리를 안다.**

[**10번 주제**](../10-borrowing-and-aliasing-rules/)가 「**한 시점에 누가 몇 명 빌릴 수 있나**」였다면,
이 주제는 「**그 빌림이 언제까지 유효한가를 어떻게 적나**」다.

| 비유 | 실체 |
|---|---|
| 도서관 대출증에 적힌 **반납일** | **수명**(lifetime) — 참조가 유효한 구간 |
| 「이 책은 **저 서가**에서 온 것」이라고 적는 칸 | **`'a`** — 출력 참조가 **어느 입력**에서 왔는지 적는 이름 |
| 창구 직원이 **뻔한 칸은 대신 채워 준다** | **생략**(elision) — 규칙 3개로 컴파일러가 채운다 |
| 서가가 **둘인데** 어디서 왔는지 안 적혀 있다 | **`E0106`** — 생략 규칙이 못 푸는 자리 |
| 「**영구 소장본**」 — 반납일이 없다 | **`&'static T`** — 참조 수명이 프로그램 끝까지 |
| 「**빌린 물건이 하나도 안 섞인 짐**」 | **`T: 'static`** — 트레이트 경계. ★ 뜻이 전혀 다르다 |
| 반납일을 **늦춰 적는다고 책이 안 없어지진 않는다** | `'a` 를 붙여도 **값의 수명은 안 늘어난다**(E0515·E0597) |
| 대출증은 **창구에서만 쓰이고 책에는 안 남는다** | 수명은 **컴파일 타임에만** 있다 — 기계어에 흔적이 없다 |

- ★★ **`'a` 는 「얼마나 오래 살아라」가 아니라 「이것과 저것이 같은 출처다」라는 표시**다.\
  명령이 아니라 **관계의 선언**이다. 이 한 줄을 놓치면 이 주제 전체가 안 잡힌다.
- **대부분의 자리에서 안 적어도 된다.** 생략 규칙 3개가 푼다 — 그래서 **못 푸는 자리만 배우면 된다**.
- ★ **`'static` 은 낱말 하나에 뜻이 둘**이고, 이것이 이 주제에서 가장 흔한 오해다.

```text
   함수 시그니처 하나를 컴파일러가 어떻게 읽나

   fn longest(x: &str, y: &str) -> &str
              └─┬──┘  └─┬──┘     └─┬┘
                │       │          │
   규칙1 ──▶  '1      '2          ?      입력마다 제 이름을 준다
   규칙2 ──▶  입력 수명이 둘이다 ───▶ 못 쓴다
   규칙3 ──▶  &self 가 없다 ──────▶ 못 쓴다
                                     │
                                     ▼
                              E0106 — 출력 칸이 빈 채로 남았다
```

**언어도 똑같은 구조다.** 실측이 이 그림 그대로다.

```text
error[E0106]: missing lifetime specifier
 --> ex.rs:2:33
  |
2 | fn longest(x: &str, y: &str) -> &str {
  |               ----     ----     ^ expected named lifetime parameter
  |
  = help: this function's return type contains a borrowed value, but the signature does not say whether it is borrowed from `x` or `y`
```

> **수명(lifetime)** — 참조가 유효한 코드 구간. 값의 수명이 아니라 **참조의 유효 구간**이다.\
> 예: `let r = &x;` 에서 `r` 이 마지막으로 쓰이는 줄까지가 그 빌림의 구간이다(10번의 NLL).

> **수명 파라미터(lifetime parameter)** — `'a` 처럼 작은따옴표로 시작하는 이름.\
> 타입 파라미터(`T`)와 같은 자리(`<>`)에 쓰지만 **값이 아니라 구간**을 받는다.

> **생략(elision)** — 시그니처의 수명 칸을 컴파일러가 규칙으로 채워 주는 것.\
> 예: `fn f(s: &str) -> &str` 는 `fn f<'a>(s: &'a str) -> &'a str` 로 풀린다.

> **`'static`** — ★ **두 가지 뜻이 있다.** ① 참조 수명 `&'static T` = 프로그램 끝까지 유효한 참조.\
> ② 트레이트 경계 `T: 'static` = 그 타입이 **수명 짧은 빌림을 품고 있지 않다**. 소유값은 전부 만족한다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **언제 `'a` 를 직접 써야 하나** — 생략 규칙 셋이 못 푸는 자리를 **시그니처만 보고** 판정할 수 있나.
2. **`'a` 를 적으면 무엇이 달라지나** — 값이 더 오래 사나(아니다), 그러면 무엇이 바뀌나.
3. **`'static` 두 자리는 어떻게 다른가** — `&'static str` 을 못 넘기는 값이 `T: 'static` 은 왜 통과하나.

★ 10번이 「**한 시점에 누가 빌릴 수 있나**」였다면 여기는 「**그 빌림이 어디서 왔고 어디까지 가나를 적는 법**」이다.

## 동작 방식

### (0) 이 주제가 쓰는 네 창

**언제 쓰나** — 아래 모든 절이 이 넷 중 하나로 접지한다.

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| **일부러 던져서 받는 컴파일 에러** | 생략이 못 푸는 자리 — E0106·E0597·E0515 | 10번의 「에러도 출력이다」 |
| ★ **함수 포인터 타입에 담아 보기** | **생략형이 무엇으로 풀렸는지**를 컴파일러가 말하게 한다 | ★ 이 주제의 고유 창 |
| ★ **생략형·명시형을 각각 컴파일해 오브젝트 파일 대조** | 둘이 **같은 것**임 + 수명이 **런타임에 없음** | ★ 이 주제의 고유 창 |
| **같은 파일을 에디션 바꿔 던지기** | 무엇이 에디션에 달려 있고 무엇이 안 달렸나 | 10번에서 이어받음 |

★ 두 번째 창이 이 주제의 핵심 도구다. **생략은 눈에 안 보이는 변환**이라 그림으로 그려 봐야
「내가 그린 게 맞나」를 확인할 수 없는데, **컴파일러에게 물으면 답을 준다**(아래 (2)).

비용 — 없음. 전부 컴파일만 해 보면 된다.

### (1) 수명을 안 적으면 무엇이 나나

**언제 쓰나** — 참조를 **돌려주는** 함수를 쓸 때마다.

```text
===== 소스: ex.rs =====
// 두 참조 중 하나를 돌려주는 함수 — 수명을 안 적으면?
fn longest(x: &str, y: &str) -> &str {
    if x.len() >= y.len() { x } else { y }
}

fn main() {
    println!("{}", longest("가나다", "라"));
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0106]: missing lifetime specifier
 --> ex.rs:2:33
  |
2 | fn longest(x: &str, y: &str) -> &str {
  |               ----     ----     ^ expected named lifetime parameter
  |
  = help: this function's return type contains a borrowed value, but the signature does not say whether it is borrowed from `x` or `y`
help: consider introducing a named lifetime parameter
  |
2 | fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
  |           ++++     ++          ++          ++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0106`.
```

읽는 법.

- **`expected named lifetime parameter`** 가 **출력 자리**(`^`)에 붙는다. 빈 칸은 거기다.
- ★ **`help:` 한 줄이 이 에러의 본체**다 — 「`x` 에서 빌린 건지 `y` 에서 빌린 건지 **시그니처가 말해 주지 않는다**」.\
  컴파일러는 몸통을 안 본다. **시그니처만 본다.**
- 마지막 `help:` 는 **고친 코드를 그대로 준다.** `++++` 는 **끼워 넣을 자리** 표시다.

시킨 대로 적으면 통과한다.

```text
===== 소스: ex.rs =====
// 같은 함수에 'a 를 붙이면
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() >= y.len() { x } else { y }
}

fn main() {
    println!("{}", longest("가나다", "라"));
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
가나다
(종료 코드 0)
```

★ **`'a` 를 세 자리에 적었다고 뭔가 오래 살게 된 것이 아니다.** 적은 것은 이 한 문장뿐이다 —
**「반환값은 `x` 와 `y` 중 짧은 쪽만큼은 산다」**. 호출하는 쪽이 그 계약을 지켜야 한다((6)에서 깨 본다).

### (2) ★★ 생략 규칙 세 개 — 컴파일러가 채우는 칸

**언제 쓰나** — 시그니처를 볼 때마다. **머릿속에서 이 셋을 순서대로 돌린다.**

| # | 규칙 | 한 줄 |
|---|------|------|
| **1** | **입력** 자리의 생략된 수명은 **각각 제 이름**을 받는다 | `f(a: &str, b: &str)` → `f<'1, 'a2>(a: &'1 str, b: &'a2 str)` |
| **2** | 입력 수명이 **정확히 하나**면 그것을 **모든 출력**에 준다 | `f(s: &str) -> &str` → `f<'a>(s: &'a str) -> &'a str` |
| **3** | 입력에 **`&self`·`&mut self`** 가 있으면 **self 의 수명**을 모든 출력에 준다 | `fn m(&self, o: &str) -> &str` → 출력은 **self** 쪽 |

- 규칙 1은 **항상** 돈다. 2와 3은 **출력에 참조가 있을 때**만 필요하다.
- **셋을 다 돌려도 출력 칸이 비면 E0106** 이다. 그게 (1)이었다.
- ★ 규칙 3이 규칙 2를 **이긴다** — `&self` 가 있으면 입력 수명이 여럿이어도 풀린다.

**규칙 1 — 출력에 참조가 없으면 그것으로 끝난다**

```text
===== 소스: ex.rs =====
// 생략 규칙 1 — 입력마다 제 수명을 받는다. 출력에 참조가 없으면 그것으로 끝이다.
fn cmp_len(a: &str, b: &str) -> usize { a.len() + b.len() }

// 손으로 푼 것
fn cmp_len_explicit<'a, 'b>(a: &'a str, b: &'b str) -> usize { a.len() + b.len() }

fn main() {
    println!("{} {}", cmp_len("가", "나다"), cmp_len_explicit("가", "나다"));
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
9 9
(종료 코드 0)
```

★ **둘 다 통과하고 같은 값을 낸다**(`9 9` — 한글 한 글자가 UTF-8 3바이트라 3+6=9). 수명이 둘이어도 **출력에 참조가 없으면 아무 문제가 없다.**

**규칙 2 — 컴파일러에게 「뭘로 풀었냐」를 직접 물어본다**

말로 「이렇게 풀린다」고 적는 대신, **그 모양의 함수 포인터에 담아 본다.** 같은 것이면 담긴다.

```text
===== 소스: ex.rs =====
// 생략형 함수를 「손으로 푼 타입」의 함수 포인터에 담아 본다 — 같은 것이면 통과한다.
fn first_word(s: &str) -> &str {
    s.split(' ').next().unwrap()
}

fn main() {
    // 규칙 1+2 가 푼다고 주장하는 모양 그대로
    let f: for<'a> fn(&'a str) -> &'a str = first_word;
    println!("{}", f("hello rust"));
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
hello
(종료 코드 0)
```

그럼 **다른 모양에는 안 담기나**를 확인한다. 출력만 `'static` 으로 바꿔 던진다.

```text
===== 소스: ex.rs =====
// 그럼 다른 모양에는 안 담기나? — 출력만 'static 으로 바꿔 본다
fn first_word(s: &str) -> &str {
    s.split(' ').next().unwrap()
}

fn main() {
    let f: fn(&str) -> &'static str = first_word;
    println!("{}", f("hello rust"));
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0308]: mismatched types
 --> ex.rs:7:39
  |
7 |     let f: fn(&str) -> &'static str = first_word;
  |            ------------------------   ^^^^^^^^^^ one type is more general than the other
  |            |
  |            expected due to this
  |
  = note: expected fn pointer `for<'a> fn(&'a _) -> &'static _`
                found fn item `for<'a> fn(&'a _) -> &'a _ {first_word}`

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0308`.
```

★★ **`= note:` 두 줄이 이 절의 결론**이다. 컴파일러가 `first_word` 의 실제 타입을
**`for<'a> fn(&'a _) -> &'a _`** 라고 **글자로 찍어 준다** — 내가 손으로 푼 것과 같다.
**생략은 문법 설탕이고, 풀린 모양은 컴파일러에게 물어보면 나온다.**

**규칙 3 — `&self` 가 출력을 가져간다**

```text
===== 소스: ex.rs =====
// 생략 규칙 3 — &self 가 있으면 출력은 self 의 수명을 받는다
struct Parser { text: String }

impl Parser {
    // 생략형
    fn head(&self, sep: &str) -> &str {
        self.text.split(sep).next().unwrap()
    }
    // 손으로 푼 것 — 출력이 'a(= self)에 묶인다
    fn head_explicit<'a, 'b>(&'a self, sep: &'b str) -> &'a str {
        self.text.split(sep).next().unwrap()
    }
}

fn main() {
    let p = Parser { text: String::from("a,b,c") };
    println!("{} {}", p.head(","), p.head_explicit(","));
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
a a
(종료 코드 0)
```

★ **정말 self 를 고르는지 반증한다** — 같은 시그니처에서 **두 번째 인자를 돌려주려** 해 본다.

```text
===== 소스: ex.rs =====
// 규칙 3 이 정말 self 를 고르는가 — 두 번째 인자를 돌려주려 해 본다
struct Parser { text: String }

impl Parser {
    fn head(&self, sep: &str) -> &str {
        let _ = &self.text;
        sep                       // ★ self 가 아니라 sep 을 돌려준다
    }
}

fn main() {
    let p = Parser { text: String::from("a,b,c") };
    println!("{}", p.head(","));
}
===== rustc --edition 2021 ex.rs -o ex =====
error: lifetime may not live long enough
 --> ex.rs:7:9
  |
5 |     fn head(&self, sep: &str) -> &str {
  |             -           - let's call the lifetime of this reference `'1`
  |             |
  |             let's call the lifetime of this reference `'2`
6 |         let _ = &self.text;
7 |         sep                       // ★ self 가 아니라 sep 을 돌려준다
  |         ^^^ method was supposed to return data with lifetime `'2` but it is returning data with lifetime `'1`
  |
help: consider introducing a named lifetime parameter and update trait if needed
  |
5 |     fn head<'a>(&self, sep: &'a str) -> &'a str {
  |            ++++              ++          ++

error: aborting due to 1 previous error
```

- ★ **이 에러에는 번호가 없다.** `error[E0…]` 가 아니라 그냥 `error:` 다 — `--explain` 으로 찾아볼 수 없는 부류다.\
  **번호 없는 진단도 있다**는 것을 여기서 처음 만난다.
- `'1`·`'2` 는 **컴파일러가 즉석에서 붙인 이름**이다(`let's call the lifetime of this reference`).\
  `'2` 가 self, `'1` 이 `sep` 인데 **출력은 `'2`(self)로 정해져 있었다**는 것이 규칙 3의 실증이다.

**`&self` 가 없으면 규칙 3이 안 돈다** — 연관 함수로 바꿔 보면 바로 E0106 이다.

```text
===== 소스: ex.rs =====
// 인자가 둘인데 &self 가 없으면 — 규칙 3 이 못 쓰이고 규칙 2 도 못 쓰인다
struct Parser { text: String }

impl Parser {
    fn pick(this: &Parser, other: &str) -> &str {
        if this.text.len() > other.len() { &this.text } else { other }
    }
}

fn main() {
    let p = Parser { text: String::from("a,b,c") };
    println!("{}", Parser::pick(&p, ","));
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0106]: missing lifetime specifier
 --> ex.rs:5:44
  |
5 |     fn pick(this: &Parser, other: &str) -> &str {
  |                   -------         ----     ^ expected named lifetime parameter
  |
  = help: this function's return type contains a borrowed value, but the signature does not say whether it is borrowed from `this` or `other`
help: consider introducing a named lifetime parameter
  |
5 |     fn pick<'a>(this: &'a Parser, other: &'a str) -> &'a str {
  |            ++++        ++                 ++          ++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0106`.
```

★ **`self` 라는 이름이 아니라 `self` 라는 자리**가 규칙 3을 켠다. 같은 `impl` 블록 안이어도
첫 인자를 `this: &Parser` 로 적으면 **평범한 인자**이고 규칙 3은 안 돈다.

**입력 참조가 하나뿐이면 다른 인자는 몇 개든 상관없다**

```text
===== 소스: ex.rs =====
// 입력 참조가 하나뿐이면 다른 인자가 몇 개든 규칙 2 가 푼다
fn take(s: &str, n: usize, pad: char) -> &str {
    let _ = pad;
    &s[..n]
}

fn main() { println!("{}", take("hello", 3, '-')); }
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
hel
(종료 코드 0)
```

★ 규칙 2가 세는 것은 **인자 개수가 아니라 「생략된 입력 수명」 개수**다. `usize`·`char` 에는 수명이 없다.

### (3) ★★ 생략형과 명시형이 정말 같은가 — 기계어로 대조한다

**언제 쓰나** — 「생략은 그냥 안 적은 것뿐인가, 다른 코드가 나오나」가 궁금할 때.

(2)에서 **타입이 같다**는 것은 컴파일러가 말해 줬다. **생성물까지 같은지**는 따로 확인한다.

```text
===== 소스: ex.rs (생략형) =====
// 수명이 런타임에 남는가 — 생략형과 명시형을 각각 컴파일해 기계어를 비교한다
pub fn first_word(s: &str) -> &str {
    s.split(' ').next().unwrap()
}
fn main() { println!("{}", first_word("hello rust")); }
===== 소스: ex.rs (명시형) =====
// 수명이 런타임에 남는가 — 명시형
pub fn first_word<'a>(s: &'a str) -> &'a str {
    s.split(' ').next().unwrap()
}
fn main() { println!("{}", first_word("hello rust")); }
===== rustc --edition 2021 -O --emit=obj ex.rs -o a_elided.o / a_explicit.o =====
-rw-rw-r-- 1 jun jun 4624  9월 24 03:02 a_elided.o
-rw-rw-r-- 1 jun jun 4624  9월 24 03:02 a_explicit.o
cmp: 바이트 단위로 같다
6ad33506f02a06a39c0b57bc77e3bdbcb938a0c4560232da9337743fbdc2995c  a_elided.o
6ad33506f02a06a39c0b57bc77e3bdbcb938a0c4560232da9337743fbdc2995c  a_explicit.o
```

★★ **오브젝트 파일이 바이트 단위로 같다.** 두 가지를 동시에 말해 준다.

1. **생략형과 명시형은 같은 것**이다 — 타입만이 아니라 **생성물까지** 같다.
2. **수명은 런타임에 아무것도 아니다** — 기계어에 흔적이 없다. 대출증은 창구에서만 쓰인다.

> ★ **측정 조건**: `-O` · `--emit=obj` · 두 판 모두 **파일 이름을 `ex.rs` 로 맞췄다.**\
> (`ls -l` 의 날짜·시각은 그 실행의 것이라 다시 찍으면 바뀐다. 근거로 읽을 칸은 **크기와 해시**뿐이다.)\
> ★★ **처음엔 파일명을 `t12-21.rs`·`t12-22.rs` 로 두고 재서 「다르다」가 나왔다** — 921바이트째부터 갈렸다.\
> **소스 파일 이름이 오브젝트 안에 박히기 때문**이다. 이름을 맞추니 해시까지 같아졌다.\
> 이 실패를 지우지 않고 남기는 이유는, **「달랐다」를 그대로 믿었으면 정반대 결론을 적을 뻔했기 때문**이다.

### (4) ★★ `'static` — 낱말 하나에 뜻이 둘

**언제 쓰나** — `'static` 이라는 글자를 볼 때마다. **어느 자리에 있는지 먼저 본다.**

```text
   'static 이 나오는 두 자리

   (가) 참조 타입 안               (나) 트레이트 경계 자리
   s: &'static str                 T: 'static
      ^^^^^^^                         ^^^^^^^
   「이 참조는 프로그램 끝까지        「이 타입 안에 프로그램 끝까지
     유효한 것을 가리킨다」            못 사는 빌림이 없다」

   String 을 던지면                 String 을 던지면
   &String -> ✗ E0597               String -> ✓ 통과
   (지역 변수라 끝까지 못 산다)       (빌린 것을 하나도 안 품었다)
```

**(나)부터 던져 본다 — 소유값은 전부 `T: 'static` 을 만족한다.**

```text
===== 소스: ex.rs =====
// 'static 의 뜻 (1) — 참조 수명. 이 참조는 프로그램 끝까지 유효하다
fn needs_static_ref(s: &'static str) { println!("참조: {}", s); }

// 'static 의 뜻 (2) — 트레이트 경계. 이 타입은 빌린 것을 품고 있지 않다
fn needs_static_bound<T: 'static>(t: T) { println!("경계: {}", std::mem::size_of_val(&t)); }

fn main() {
    let owned = String::from("소유한 문자열");

    needs_static_bound(owned);          // ★ String 은 T: 'static 을 만족한다
    needs_static_bound(42i32);          // i32 도
    needs_static_bound(vec![1, 2, 3]);  // Vec<i32> 도

    needs_static_ref("리터럴");          // &'static str
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
경계: 24
경계: 4
경계: 24
참조: 리터럴
(종료 코드 0)
```

★★ **`String` 이 `T: 'static` 을 통과한다.** 이게 가장 흔한 오해가 깨지는 자리다 —
`'static` 을 보고 「리터럴이나 전역만 되는 것」이라고 읽으면 여기서 막힌다.
**힙에 있든 방금 만들었든, 빌린 것을 안 품었으면 만족한다.**

**같은 `String` 을 두 자리에 각각 던지면 갈린다.**

```text
===== 소스: ex.rs =====
// 같은 String 을 두 자리에 각각 던져 본다
fn needs_static_ref(s: &'static str) { println!("참조: {}", s); }
fn needs_static_bound<T: 'static>(_t: T) { println!("경계: 통과"); }

fn main() {
    let owned = String::from("소유한 문자열");

    needs_static_ref(&owned);   // (가) 빌린 것을 &'static 자리에
    needs_static_bound(owned);  // (나) 소유한 것을 T: 'static 자리에
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0597]: `owned` does not live long enough
  --> ex.rs:8:22
   |
 6 |     let owned = String::from("소유한 문자열");
   |         ----- binding `owned` declared here
 7 |
 8 |     needs_static_ref(&owned);   // (가) 빌린 것을 &'static 자리에
   |     -----------------^^^^^^-
   |     |                |
   |     |                borrowed value does not live long enough
   |     argument requires that `owned` is borrowed for `'static`
 9 |     needs_static_bound(owned);  // (나) 소유한 것을 T: 'static 자리에
10 | }
   | - `owned` dropped here while still borrowed

error[E0505]: cannot move out of `owned` because it is borrowed
 --> ex.rs:9:24
  |
6 |     let owned = String::from("소유한 문자열");
  |         ----- binding `owned` declared here
7 |
8 |     needs_static_ref(&owned);   // (가) 빌린 것을 &'static 자리에
  |     ------------------------
  |     |                |
  |     |                borrow of `owned` occurs here
  |     argument requires that `owned` is borrowed for `'static`
9 |     needs_static_bound(owned);  // (나) 소유한 것을 T: 'static 자리에
  |                        ^^^^^ move out of `owned` occurs here
  |
help: consider cloning the value if the performance cost is acceptable
  |
8 |     needs_static_ref(&owned.clone());   // (가) 빌린 것을 &'static 자리에
  |                            ++++++++

error: aborting due to 2 previous errors

Some errors have detailed explanations: E0505, E0597.
For more information about an error, try `rustc --explain E0505`.
```

- **(가)** — `&owned` 를 `&'static str` 자리에 넣으니 **E0597**.\
  라벨 `argument requires that owned is borrowed for 'static` 이 **왜 그 수명이 요구됐는지**를 말해 준다.
- ★ **E0505 는 덤으로 따라온 것**이다 — (가)가 `owned` 를 `'static` 동안 빌렸다고 **가정하고 검사를 계속하니**,
  그다음 줄의 이동이 「빌린 채로 옮긴 것」이 된다. **에러 하나가 다음 에러를 만든다** — 위에서부터 고친다.

**`T: 'static` 이 실제로 거부하는 것은 무엇인가** — 「소유가 아닌 것」이 아니라 「**빌린 것을 품은 타입**」이다.

```text
===== 소스: ex.rs =====
// T: 'static 이 거부하는 것은 「소유 아님」이 아니라 「빌린 것을 품은 타입」이다
fn needs_static_bound<T: 'static>(_t: T) { println!("통과"); }

struct Holder<'a> { r: &'a str }

fn main() {
    let owned = String::from("가나다");
    let h = Holder { r: &owned };   // 빌린 것을 품은 값
    needs_static_bound(h);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0597]: `owned` does not live long enough
  --> ex.rs:8:25
   |
 7 |     let owned = String::from("가나다");
   |         ----- binding `owned` declared here
 8 |     let h = Holder { r: &owned };   // 빌린 것을 품은 값
   |                         ^^^^^^ borrowed value does not live long enough
 9 |     needs_static_bound(h);
   |     --------------------- argument requires that `owned` is borrowed for `'static`
10 | }
   | - `owned` dropped here while still borrowed
   |
note: requirement that the value outlives `'static` introduced here
  --> ex.rs:2:26
   |
 2 | fn needs_static_bound<T: 'static>(_t: T) { println!("통과"); }
   |                          ^^^^^^^

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0597`.
```

★ `note: requirement that the value outlives 'static introduced here` 가 **경계 자리를 직접 짚어 준다.**
`Holder<'a>` 는 `'a` 가 `'static` 일 때만 `T: 'static` 이 된다 — 그래서 **소유가 아니라 무엇을 품었나**다.

| 쓴 모양 | 무슨 뜻인가 | `String` 은? | 지역 `&String` 은? |
|---|---|---|---|
| `&'static T` | **이 참조**가 프로그램 끝까지 유효하다 | 해당 없음(참조가 아니다) | ✗ **E0597** |
| `T: 'static` | **이 타입**이 짧은 빌림을 안 품었다 | ✓ **통과** | ✗(`&'a String` 은 `'a: 'static` 이어야) |

★ 외울 문장 — **`&'static` 은 「이 참조가 영원하다」, `T: 'static` 은 「이 타입이 남의 것을 안 들고 있다」.**

### (5) 수명을 적어도 값이 더 살지는 않는다

**언제 쓰나** — E0106 을 보고 `'a` 를 붙였는데 다른 에러가 났을 때.

```text
===== 소스: ex.rs =====
// 지역 값의 참조를 돌려주려 하면
fn make_ref() -> &String {
    let s = String::from("가나다");
    &s
}

fn main() { println!("{}", make_ref()); }
===== rustc --edition 2021 ex.rs -o ex =====
error[E0106]: missing lifetime specifier
 --> ex.rs:2:18
  |
2 | fn make_ref() -> &String {
  |                  ^ expected named lifetime parameter
  |
  = help: this function's return type contains a borrowed value, but there is no value for it to be borrowed from
help: consider using the `'static` lifetime, but this is uncommon unless you're returning a borrowed value from a `const` or a `static`
  |
2 | fn make_ref() -> &'static String {
  |                   +++++++
help: instead, you are more likely to want to return an owned value
  |
2 - fn make_ref() -> &String {
2 + fn make_ref() -> String {
  |

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0106`.
```

★ **같은 E0106 인데 `help:` 가 (1)과 다르다** — 입력이 아예 없으니 「어디서 빌린 건지」를 못 묻고,
「**소유값을 돌려주는 게 맞을 것**」이라고 말한다. **에러 번호보다 `help:` 문구가 정보가 많다.**

시킨 대로 하지 말고 **`'a` 를 붙여** 본다 — 수명이 늘어난다는 착각을 깨는 실험이다.

```text
===== 소스: ex.rs =====
// 수명을 적어 주면 통과하나 — 'a 를 붙여 본다
fn make_ref<'a>() -> &'a String {
    let s = String::from("가나다");
    &s
}

fn main() { println!("{}", make_ref()); }
===== rustc --edition 2021 ex.rs -o ex =====
error[E0515]: cannot return reference to local variable `s`
 --> ex.rs:4:5
  |
4 |     &s
  |     ^^ returns a reference to data owned by the current function

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0515`.
```

★★ **E0106 이 E0515 로 바뀌었을 뿐이다.** `'a` 는 **적는 칸**을 채웠지 **값을 살려 주지 않았다.**

```text
   'a 를 붙이면 무엇이 달라지나

   전:  출력 수명 칸이 비었다        -> E0106  「어디서 왔는지 안 적혔다」
   후:  출력 수명 칸에 'a 가 찼다    -> E0515  「적힌 대로면 거짓말이다」

   수명 표기는 「계약서」다. 칸을 채우면 검사가 그다음 단계로 넘어갈 뿐,
   계약을 못 지키면 거기서 또 막힌다.
```

### (6) `'a` 는 「같은 출처」의 선언이다 — 호출하는 쪽이 계약을 진다

**언제 쓰나** — `'a` 를 붙인 함수를 쓸 때.

```text
===== 소스: ex.rs =====
// 'a 가 「수명을 늘려 준다」면 이것이 통과해야 한다
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() >= y.len() { x } else { y }
}

fn main() {
    let long = String::from("가나다라마");
    let winner;
    {
        let short = String::from("가나");
        winner = longest(&long, &short);
    }
    println!("{}", winner);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0597]: `short` does not live long enough
  --> ex.rs:11:33
   |
10 |         let short = String::from("가나");
   |             ----- binding `short` declared here
11 |         winner = longest(&long, &short);
   |                                 ^^^^^^ borrowed value does not live long enough
12 |     }
   |     - `short` dropped here while still borrowed
13 |     println!("{}", winner);
   |                    ------ borrow later used here

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0597`.
```

★ **실행하면 `가나다라마` 가 나올 코드인데 거부된다.** 빌림 검사기는 **몸통을 안 보고 시그니처만** 보므로
「둘 중 하나가 나온다」만 알고 「짧은 쪽이 안 나온다」는 모른다. — **시그니처가 곧 계약**이다(10번의 결론과 같다).

```text
   두 참조를 'a 하나로 묶으면

   long  ├──────────────────────────────────┤   (바깥 스코프)
   short         ├───────────┤                  (안쪽 스코프)
   'a            └───────────┘                  ← 둘의 교집합으로 좁혀진다
   winner        ·············└──?              ← 'a 밖에서 쓰려 하니 E0597

   'a 는 「늘린다」가 아니라 「두 입력과 출력이 같은 구간을 공유한다」다.
   공유 구간은 항상 짧은 쪽에 맞춰진다.
```

### (7) ★ NLL — 어디까지가 되고 어디부터 안 되나

**언제 쓰나** — 「사람 눈에는 안전한데 왜 막히지」 싶을 때.

10번에서 본 대로 **빌림은 마지막 사용까지만 산다**(NLL). 여기서는 **그 경계**를 본다.

**되는 자리 — 같은 값에 대한 두 가변 빌림도 구간이 안 겹치면 통과한다**

```text
===== 소스: ex.rs =====
// NLL 이 푸는 자리 — 같은 코드에서 마지막 사용만 앞으로 옮긴다
fn main() {
    let mut n = 1;
    let a = &mut n;
    *a += 1;          // a 의 마지막 사용
    let b = &mut n;   // 그 뒤에 새 가변 빌림
    *b += 1;
    println!("{}", n);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
3
(종료 코드 0)
```

**안 되는 자리 — 빌림이 함수 밖으로 나갈 때, 갈래 하나에서만 나가도 전체가 막힌다**

```text
===== 소스: ex.rs =====
// NLL 이 못 푸는 자리 — 한쪽 갈래에서만 빌림이 반환되는데도 전체가 막힌다
use std::collections::HashMap;

fn get_or_insert(map: &mut HashMap<u32, String>) -> &String {
    match map.get(&0) {
        Some(v) => v,
        None => {
            map.insert(0, String::from("기본값"));
            map.get(&0).unwrap()
        }
    }
}

fn main() {
    let mut m: HashMap<u32, String> = HashMap::new();
    println!("{}", get_or_insert(&mut m));
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0502]: cannot borrow `*map` as mutable because it is also borrowed as immutable
 --> ex.rs:8:13
  |
4 | fn get_or_insert(map: &mut HashMap<u32, String>) -> &String {
  |                       - let's call the lifetime of this reference `'1`
5 |     match map.get(&0) {
  |           --- immutable borrow occurs here
6 |         Some(v) => v,
  |                    - returning this value requires that `*map` is borrowed for `'1`
7 |         None => {
8 |             map.insert(0, String::from("기본값"));
  |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ mutable borrow occurs here

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0502`.
```

★★ **`None` 갈래에서는 `map.get(&0)` 의 빌림을 안 쓴다.** 사람 눈에는 안전하다.
그런데 **`Some` 갈래가 그 빌림을 `'1`(호출자에게)로 내보내기 때문에** 빌림 구간이 **match 전체**로 늘어난다.

```text
   NLL 이 하는 것과 못 하는 것

   되는 것   — 빌림 구간을 「마지막 사용」까지로 줄인다 (블록이 아니라 사용 위치 기준)
   되는 것   — 갈래마다 다른 구간을 갖는 것도 함수 안에서 다 쓰이고 끝나면 된다
   ───────────────────────────────────────────────────────────────
   못 하는 것 — 빌림이 「반환값」이 되면 그 구간이 호출자의 수명('1)으로 고정된다.
                한 갈래만 반환해도 match 전체가 '1 로 잡힌다.
                (이 모양은 Rust 팀이 「NLL problem case #3」로 부르는 알려진 한계다)
```

**사람이 푼다 — 빌림을 갈래 밖으로 뺀다.**

```text
===== 소스: ex.rs =====
// NLL 이 못 푸는 자리를 사람이 푼다 — 빌림을 갈래 밖으로 뺀다
use std::collections::HashMap;

fn get_or_insert(map: &mut HashMap<u32, String>) -> &String {
    if !map.contains_key(&0) {              // 빌림이 이 줄에서 끝난다
        map.insert(0, String::from("기본값"));
    }
    map.get(&0).unwrap()                    // 새로 빌린다
}

fn main() {
    let mut m: HashMap<u32, String> = HashMap::new();
    println!("{}", get_or_insert(&mut m));
    m.insert(0, String::from("바뀐값"));
    println!("{}", get_or_insert(&mut m));
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
기본값
바뀐값
(종료 코드 0)
```

★ 값은 같고 **탐색이 한 번 더 늘었다.** 「안전을 못 증명했으니 비용을 낸다」가 이 자리의 정직한 요약이다.
같은 모양의 다른 처방(`entry` API)은 [**11번 주제**](../11-borrow-checker-rejections/)가 모은다.

### (8) 익명 수명 `'_` 와 에디션

**언제 쓰나** — 반환 타입에 `Excerpt`·`Iter` 처럼 **수명 파라미터를 가진 타입**을 쓸 때.

```text
===== 소스: ex.rs =====
// 익명 수명 '_ — 「여기 수명이 있다」만 적고 이름은 안 짓는다
struct Excerpt<'a> { part: &'a str }

fn first_sentence(novel: &str) -> Excerpt<'_> {
    Excerpt { part: novel.split('.').next().unwrap() }
}

fn main() {
    let novel = String::from("첫 문장. 둘째 문장.");
    println!("{}", first_sentence(&novel).part);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
첫 문장
(종료 코드 0)
```

`'_` 를 빼도 **컴파일은 된다**(기본은 경고). 린트를 `deny` 로 올려 무엇을 말하는지 본다.

```text
===== 소스: ex.rs =====
// '_ 를 빼면? — 경로에서 수명을 생략한 것이다
#![deny(elided_lifetimes_in_paths)]
struct Excerpt<'a> { part: &'a str }

fn first_sentence(novel: &str) -> Excerpt {
    Excerpt { part: novel.split('.').next().unwrap() }
}

fn main() {
    let novel = String::from("첫 문장. 둘째 문장.");
    println!("{}", first_sentence(&novel).part);
}
===== rustc --edition 2021 ex.rs -o ex =====
error: hidden lifetime parameters in types are deprecated
 --> ex.rs:5:35
  |
5 | fn first_sentence(novel: &str) -> Excerpt {
  |                                   ^^^^^^^ expected lifetime parameter
  |
note: the lint level is defined here
 --> ex.rs:2:9
  |
2 | #![deny(elided_lifetimes_in_paths)]
  |         ^^^^^^^^^^^^^^^^^^^^^^^^^
help: indicate the anonymous lifetime
  |
5 | fn first_sentence(novel: &str) -> Excerpt<'_> {
  |                                          ++++

warning: hiding a lifetime that's elided elsewhere is confusing
 --> ex.rs:5:26
  |
5 | fn first_sentence(novel: &str) -> Excerpt {
  |                          ^^^^     ^^^^^^^ the same lifetime is hidden here
  |                          |
  |                          the lifetime is elided here
  |
  = help: the same lifetime is referred to in inconsistent ways, making the signature confusing
  = note: `#[warn(mismatched_lifetime_syntaxes)]` on by default
help: use `'_` for type paths
  |
5 | fn first_sentence(novel: &str) -> Excerpt<'_> {
  |                                          ++++

error: aborting due to 1 previous error; 1 warning emitted
```

- **`&str` 에서 생략한 것**과 **`Excerpt` 에서 생략한 것**은 **보이는 정도가 다르다** —\
  앞은 `&` 가 있어 「참조구나」가 보이고, 뒤는 **타입 이름만 봐서는 참조를 품었는지 모른다.** 그래서 린트가 있다.
- ★ **`mismatched_lifetime_syntaxes` 는 기본 경고**다(이 툴체인 실측). 한 시그니처에서 **표기 방식을 섞지 말라**는 뜻이다.

**같은 파일이 에디션에 따라 갈리는 자리** — 이 주제에서 가장 강한 에디션 실측은 **임시값 수명**이다.

```text
===== 소스: ex.rs =====
// 에디션 차이 — if let 의 임시값이 else 갈래까지 사는가
use std::cell::RefCell;

fn main() {
    let c: RefCell<Option<i32>> = RefCell::new(None);
    if let Some(v) = *c.borrow() {
        println!("있음 {}", v);
    } else {
        *c.borrow_mut() = Some(7);        // 빌림 가드가 아직 살아 있나?
        println!("없음 -> 채웠다 {:?}", c);
    }
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0597]: `c` does not live long enough
  --> ex.rs:6:23
   |
 5 |     let c: RefCell<Option<i32>> = RefCell::new(None);
   |         - binding `c` declared here
 6 |     if let Some(v) = *c.borrow() {
   |                       ^---------
   |                       |
   |                       borrowed value does not live long enough
   |                       a temporary with access to the borrow is created here ...
...
12 | }
   | -
   | |
   | `c` dropped here while still borrowed
   | ... and the borrow might be used here, when that temporary is dropped and runs the destructor for type `Ref<'_, Option<i32>>`
   |
help: consider adding semicolon after the expression so its temporaries are dropped sooner, before the local variables declared by the block are dropped
   |
11 |     };
   |      +

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0597`.
===== rustc --edition 2024 ex.rs -o ex =====
===== ./ex =====
없음 -> 채웠다 RefCell { value: Some(7) }
(종료 코드 0)
```

★★ **한 글자도 안 고친 같은 파일이 2021 에서 거부되고 2024 에서 통과해 실행된다.**
`if let` 의 임시값 스코프가 2024 에디션에서 바뀌었다(README 의 버전표가 미리 적어 둔 항목이다).
**에디션을 안 밝히고 「이 코드는 안 된다」를 적으면 그 문장은 절반만 참이다.**

**생략 규칙 자체는 에디션에 안 달려 있다** — 같은 파일을 셋 다 던져 봤다.

```text
===== 소스: ex.rs =====
// 2015 에디션에서도 같은가 — 생략 규칙은 에디션에 달려 있지 않다
fn first_word(s: &str) -> &str { s.split(' ').next().unwrap() }
fn longest(x: &str, y: &str) -> &str {
    if x.len() >= y.len() { x } else { y }
}
fn main() { println!("{}", first_word("hello rust")); let _ = longest; }
===== rustc --edition 2021 ex.rs -o ex =====
error[E0106]: missing lifetime specifier
 --> ex.rs:3:33
  |
3 | fn longest(x: &str, y: &str) -> &str {
  |               ----     ----     ^ expected named lifetime parameter
  |
  = help: this function's return type contains a borrowed value, but the signature does not say whether it is borrowed from `x` or `y`
help: consider introducing a named lifetime parameter
  |
3 | fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
  |           ++++     ++          ++          ++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0106`.
```

위는 **2021** 판이고, **`--edition 2015`** 와 **`--edition 2024`** 로 각각 다시 던진 출력이
★ **한 글자도 다르지 않았다**(관찰 — 세 판 모두 직접 던져 대조했다). 다만 「여러 판에서 같았다」는 보장이 아니므로,
**보장 쪽 근거는 Reference 의 Lifetime elision 절이 에디션을 조건으로 달지 않는다는 것**이다.

### (9) 생략이 늘 옳지는 않다 — 규칙 3이 골라 주는 수명이 너무 짧을 때

**언제 쓰나** — 참조를 품은 구조체(`Excerpt<'a>`)에 메서드를 달 때.

```text
===== 소스: ex.rs =====
// 같은 몸통, 반환 수명만 다르다 — 생략형은 self 에 묶인다
struct Excerpt<'a> { part: &'a str }

impl<'a> Excerpt<'a> {
    fn part_elided(&self) -> &str { self.part }   // 규칙 3: self 의 수명
}

fn main() {
    let novel = String::from("첫 문장. 둘째 문장.");
    let long_lived;
    {
        let e = Excerpt { part: novel.split('.').next().unwrap() };
        long_lived = e.part_elided();
    }
    println!("{}", long_lived);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0597]: `e` does not live long enough
  --> ex.rs:13:22
   |
12 |         let e = Excerpt { part: novel.split('.').next().unwrap() };
   |             - binding `e` declared here
13 |         long_lived = e.part_elided();
   |                      ^ borrowed value does not live long enough
14 |     }
   |     - `e` dropped here while still borrowed
15 |     println!("{}", long_lived);
   |                    ---------- borrow later used here

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0597`.
```

반환 수명을 **필드의 수명 `'a`** 로 직접 적으면 통과한다.

```text
===== 소스: ex.rs =====
// impl 블록의 메서드 — 규칙 3 이 여기서도 쓰인다
struct Excerpt<'a> { part: &'a str }

impl<'a> Excerpt<'a> {
    // 생략형: 출력은 &self 의 수명을 받는다
    fn announce(&self, ann: &str) -> &str {
        println!("알림! {}", ann);
        self.part
    }
    // 반환을 'a(필드의 수명)로 적으면 self 보다 오래 살 수 있다
    fn part(&self) -> &'a str { self.part }
}

fn main() {
    let novel = String::from("첫 문장. 둘째 문장.");
    let long_lived;
    {
        let e = Excerpt { part: novel.split('.').next().unwrap() };
        println!("{}", e.announce("공지"));
        long_lived = e.part();   // e 는 여기서 죽지만 반환값은 novel 에 묶여 있다
    }
    println!("{}", long_lived);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
알림! 공지
첫 문장
첫 문장
(종료 코드 0)
```

```text
   같은 몸통 self.part 를 돌려주는 두 메서드

   fn part_elided(&self) -> &str      ← 규칙 3: self 의 수명. e 가 죽으면 끝난다
   fn part(&self)        -> &'a str   ← 필드의 수명. novel 이 살아 있으면 산다

   e     ├───────┤              (안쪽 블록)
   novel ├────────────────────┤ (바깥)
   part_elided 의 반환  └─┘     -> e 와 함께 끝난다 -> E0597
   part 의 반환         └──────┘ -> novel 까지 간다 -> 통과
```

★ **구조체가 품은 참조를 그대로 내보낼 때는 생략을 믿지 말고 `'a` 를 적는다.**
참조를 필드로 담는 이야기 전체는 목록의 **13번 주제**가 정본이다.

### (10) 수명 사이의 관계 — `'long: 'short`

**언제 쓰나** — 수명이 둘 이상인데 하나가 다른 것보다 오래 산다고 말해야 할 때.

```text
===== 소스: ex.rs =====
// 수명 사이의 관계를 적는다 — 'long 이 'short 보다 오래 산다
fn pick<'long: 'short, 'short>(a: &'long str, b: &'short str) -> &'short str {
    if a.len() > b.len() { a } else { b }
}

fn main() {
    let outer = String::from("가나다라마바사");
    {
        let inner = String::from("가나");
        println!("{}", pick(&outer, &inner));
    }
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
가나다라마바사
(종료 코드 0)
```

- `'long: 'short` 는 「**`'long` 이 `'short` 보다 짧지 않다**」로 읽는다(outlives 경계).\
  `T: 'static` 의 `:` 와 **같은 기호이고 같은 뜻**이다 — 왼쪽이 오른쪽만큼은 산다.
- 덕분에 `&'long str` 을 `&'short str` 자리에 쓸 수 있다.\
  ★ (6)의 `longest<'a>` 가 두 입력을 하나로 묶어 짧은 쪽에 맞춘 것과 **같은 일을 더 정밀하게** 한 것이다.

## 문법 — 형태와 규칙

### 형태

```rust
// 1) 함수 — <> 안에 선언하고 참조마다 붙인다
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str { x }

// 2) 서로 다른 수명 두 개
fn pick<'a, 'b>(a: &'a str, b: &'b str) -> &'a str { a }

// 3) 관계(outlives) — 'a 가 'b 보다 짧지 않다
fn pick2<'a: 'b, 'b>(a: &'a str, b: &'b str) -> &'b str { a }

// 4) 구조체 — 참조를 필드로 담으면 반드시 필요하다
struct Excerpt<'a> { part: &'a str }

// 5) impl 블록 — 타입의 수명을 impl 쪽에도 선언한다
impl<'a> Excerpt<'a> {
    fn part(&self) -> &'a str { self.part }
}

// 6) 익명 수명 — 「있긴 있다」만 적는다
fn first(novel: &str) -> Excerpt<'_> { Excerpt { part: novel } }

// 7) 트레이트 경계 자리의 'static — 참조 수명이 아니다
fn spawn_like<T: Send + 'static>(_t: T) {}

// 8) 참조 수명 자리의 'static
const GREETING: &'static str = "안녕";
```

### 금지 사례 — 던져서 받은 여섯

| 코드 | 에러 | 한 줄 |
|---|---|---|
| `fn longest(x: &str, y: &str) -> &str` | **E0106** | 입력 수명이 둘이라 생략 규칙이 못 푼다 |
| `struct Excerpt { part: &str }` | **E0106** | 구조체 필드는 **규칙 2·3이 아예 없다** |
| `fn make() -> &String` | **E0106** | 빌려올 입력이 없다 — `help:` 가 소유값을 권한다 |
| `fn make<'a>() -> &'a String { &local }` | **E0515** | 칸은 찼지만 계약이 거짓이다 |
| 짧은 스코프의 값을 `longest<'a>` 에 | **E0597** | `'a` 는 교집합으로 좁혀진다 |
| 지역 `&String` 을 `&'static str` 자리에 | **E0597** | (+ 뒤이어 **E0505**) |

### 생략 판정을 손으로 돌리는 순서

```text
   시그니처를 받았다
        │
        ▼
   ① 출력에 참조가 있나? ── 아니오 ──▶ 끝. 아무것도 안 적어도 된다
        │ 예
        ▼
   ② 입력에 &self / &mut self 가 있나? ── 예 ──▶ 출력 = self 의 수명 (규칙 3). 끝
        │ 아니오
        ▼
   ③ 생략된 입력 수명이 정확히 하나인가? ── 예 ──▶ 출력 = 그 수명 (규칙 2). 끝
        │ 아니오 (0개 또는 2개 이상)
        ▼
   E0106. 직접 적어야 한다.
```

★ 이 순서도를 **거꾸로** 쓰면 진단 도구가 된다 — E0106 을 보면 **②와 ③이 왜 안 걸렸는지**만 보면 된다.

### 타입을 컴파일러에게 묻는 법

```rust
// 생략형이 무엇으로 풀렸는지 알고 싶을 때
let f: for<'a> fn(&'a str) -> &'a str = first_word;   // 맞으면 통과
let g: fn(&str) -> &'static str = first_word;         // 틀리면 E0308 이 실제 타입을 찍어 준다
```

진단의 `= note: found fn item` 줄에 `for<'a> fn(&'a _) -> &'a _ {first_word}` 가 찍힌다 — 이 줄이 답이다.
**10번의 `let _: () = 식;` 수법과 같은 계열**이고, 여기서는 **수명까지 찍힌다**는 점이 다르다.

## 어디서 틀리나

### 1. ★★ 「`'a` 를 붙이면 더 오래 산다」

- 가장 큰 오해다. `'a` 는 **관계의 선언**이지 **연장 명령**이 아니다.
- 실측: `fn make_ref<'a>() -> &'a String` 은 **E0106 이 E0515 로 바뀔 뿐**이다((5)).
- 고치는 법은 **소유값을 돌려주는 것**이다. 컴파일러도 그렇게 권한다.

### 2. ★★ 「`'static` 은 리터럴·전역만 되는 것」

- `&'static str` 자리에서는 맞지만 **`T: 'static` 자리에서는 틀렸다.**
- 실측: `String`·`Vec<i32>`·`i32` 가 전부 `T: 'static` 을 통과했다((4)).
- **`T: 'static` 이 거부하는 것은 「빌린 것을 품은 타입」이다** — `Holder<'a>` 가 그 예다.
- ★ 그래서 `thread::spawn` 이 `'static` 을 요구한다고 「소유값만 된다」로 읽으면 절반만 맞다.\
  정확히는 「**빌린 것을 안 품은 값만 된다**」이고 소유값은 전부 그렇다(목록의 **49번 주제**).

### 3. ★ 「생략 규칙은 함수에만 있다」

- 구조체·열거형 필드에는 **규칙 2·3이 없다.** `struct Excerpt { part: &str }` 는 **항상** E0106 이다.
- 실측에서 `help:` 문구도 다르다 — 함수 쪽은 「어디서 빌렸나」를 묻고, 구조체 쪽은 그냥 **이름을 달라**고 한다.

### 4. ★ 「메서드니까 생략하면 잘 된다」

- 규칙 3이 골라 주는 것은 **`self` 의 수명**이라 **너무 짧을 수 있다**((9)).
- 구조체가 품은 참조를 내보내는 메서드는 **`-> &'a T` 를 직접 적는다.**

### 5. 「몸통이 안전하면 통과한다」

- 빌림 검사는 **시그니처만** 본다. (6)의 `longest` 는 **실행하면 항상 긴 쪽**이 나오는데도 거부된다.
- 10번의 「필드는 되는데 메서드는 안 되는」 자리와 **같은 원인**이다.

### 6. 「NLL 이 다 해 준다」

- 빌림이 **반환값이 되는 순간** 구간이 호출자의 수명으로 고정된다 — 갈래 하나만 반환해도 그렇다((7)).
- 이 모양은 알려진 한계이고, **처방은 코드를 바꾸는 것**이다(`contains_key` 선분리 · `entry`).

### 7. `'_` 를 안 적어 타입에 참조가 숨는다

- `-> Excerpt` 는 컴파일되지만 **읽는 사람이 참조인 줄 모른다.**
- `mismatched_lifetime_syntaxes` 경고가 「한 시그니처에서 표기를 섞지 마라」고 말한다((8)).

### 8. 에디션을 안 밝히고 「이 코드는 안 된다」를 적는다

- 실측: `if let` + `RefCell` 한 파일이 **2021 E0597 / 2024 통과**였다((8)).
- ★ `rustc` 의 **기본 에디션은 2015** 다. `--edition` 없이 잰 결과는 2021 의 근거가 아니다.

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| 생략 규칙 **3개**와 그 우선순위 | **언어** | Reference — Lifetime elision · (2)의 세 실측 |
| 생략형과 명시형이 **같은 타입** | **언어** | `for<'a> fn(&'a _) -> &'a _` 를 E0308 이 찍어 줌 |
| **수명이 런타임에 없는 것** | **언어**(제로 코스트) | ★ 오브젝트 파일이 **바이트 단위로 동일**(sha256 일치) |
| 구조체 필드에는 생략이 **없는 것** | **언어** | `struct Excerpt { part: &str }` → E0106 |
| `T: 'static` 을 **소유값이 만족**하는 것 | **언어** | `String`·`Vec<i32>`·`i32` 통과 실측 |
| `&'static T` 와 `T: 'static` 이 **다른 것** | **언어** | 같은 `String` 이 한쪽만 통과 |
| `'a` 가 **값의 수명을 안 늘리는 것** | **언어** | E0515 실측 |
| `'long: 'short` 의 뜻 | **언어** | Reference — Trait and lifetime bounds · 실측 통과 |
| **에러 번호**가 상황별로 갈리는 것 | **rustc 구현** | 번호는 안정적이고 **문구·`help` 는 바뀐다** |
| ★ **번호 없는 진단이 있는 것** | **rustc 구현** | `error: lifetime may not live long enough` |
| `'1`·`'2` 같은 **즉석 이름** | **rustc 의 진단 표기** | `let's call the lifetime of this reference` |
| `mismatched_lifetime_syntaxes` 가 **기본 경고** | **rustc 판** | 이 툴체인(1.92.0) 실측 — 린트는 판마다 추가·승격된다 |
| **NLL 이 `get_or_insert` 를 못 푸는 것** | **현재 구현의 한계** | 알려진 문제 사례. 언어가 금지한 것이 아니라 **검사기가 증명 못 한 것** |
| `if let` 임시값 스코프 | **에디션**(2024에서 변경) | 같은 파일 2021 E0597 / 2024 통과 |
| 생략 규칙이 **에디션 무관**인 것 | **언어**(Reference가 조건을 안 담) | 2015·2021·2024 출력 동일(관찰) |
| 오브젝트 파일에 **소스 파일명이 박히는 것** | **rustc·플랫폼 구현** | 파일명 다르면 921바이트째부터 갈림 |

★ **「NLL 이 못 푼다」와 「언어가 금지한다」는 다른 말이다.** (7)의 코드는 **안전한데 거부된** 것이고,
검사기가 나아지면 통과할 수 있다. **거부됐다고 그 코드가 위험한 것은 아니다** — 이 구분이 이 주제에서 제일 중요하다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 이유 |
|---|---|---|
| 출력에 참조가 없다 | **아무것도 안 적는다** | 규칙 1로 끝난다 |
| 입력 참조가 하나다 | **안 적는다** | 규칙 2가 푼다 |
| `&self` 가 있고 출력이 self 에서 온다 | **안 적는다** | 규칙 3이 푼다 |
| `&self` 가 있는데 **필드의 참조를 내보낸다** | **`-> &'a T`** 를 적는다 | 규칙 3이 주는 것보다 길어야 한다 |
| 입력 참조가 둘이고 출력이 그중 하나다 | **`'a` 를 직접** | E0106. 어느 쪽인지만 적으면 된다 |
| 둘 중 **한쪽에서만** 온다 | `<'a, 'b>` 로 **갈라 적는다** | 묶으면 교집합으로 좁아져 호출부가 손해다 |
| 참조를 필드에 담는다 | `struct X<'a>` | 선택지가 없다. 자세한 것은 목록의 **13번 주제** |
| 지역 값의 참조를 돌려주고 싶다 | ★ **소유값을 돌려준다** | `'a` 로는 못 푼다(E0515) |
| 스레드·`Box<dyn Any>` 에 넘긴다 | `T: 'static` 경계를 읽는다 | 소유값이면 대개 이미 만족한다 |
| NLL 이 못 푸는 모양이다 | **코드를 바꾼다** | `contains_key` 선분리 · `entry` — [**11번 주제**](../11-borrow-checker-rejections/) |

판단 규칙 두 줄.

- **먼저 안 적고 던진다.** E0106 이 나면 그때 적는다 — 어디에 적을지까지 `help:` 가 알려 준다.
- **`'a` 를 적어도 안 되면 그건 표기 문제가 아니라 설계 문제다.** 소유로 돌리거나 구조를 바꾼다.

## 핵심 문장

- ★★ **`'a` 는 「오래 살아라」가 아니라 「이것과 저것이 같은 출처다」라는 관계의 선언**이다.
- **생략 규칙 3개** — ① 입력마다 제 이름 ② 입력 수명이 하나면 출력에 준다 ③ `&self` 가 있으면 self 의 것을 준다.
- **셋을 다 돌려도 출력 칸이 비면 E0106** 이고, 그때만 직접 적는다.
- ★ **생략형과 명시형은 같은 것**이다 — 타입도 같고 **오브젝트 파일이 바이트 단위로 같다.**
- ★★ **`'static` 은 뜻이 둘** — `&'static T`(참조가 영원)와 `T: 'static`(빌린 것을 안 품음).\
  **`String` 은 `T: 'static` 을 만족하고 `&'static str` 자리에는 못 간다.**
- **수명은 컴파일 타임에만 있다** — 기계어에 흔적이 없다.
- **`'a` 는 값을 살려 주지 않는다** — E0106 이 E0515 로 바뀔 뿐이다.
- **빌림 검사는 시그니처만 본다** — 몸통이 안전해도 시그니처가 말 안 하면 거부된다.
- ★ **NLL 이 못 푸는 것과 언어가 금지한 것은 다르다.** 반환값이 되는 빌림은 호출자의 수명으로 고정된다.
- ★ **`rustc` 의 기본 에디션은 2015** 다. 에디션을 안 밝힌 컴파일 결과는 근거가 못 된다.

## 관련 자료

- [`../README.md`](../README.md) — Rust 문법·API 주제 목록(이 주제는 12번)
- [**10번 주제**](../10-borrowing-and-aliasing-rules/)(빌림 `&`·`&mut`) — ★ **직접 선행**.\
  **그쪽은** 「한 시점에 누가 몇 명 빌리나」, **여기는** 「그 빌림이 어디서 왔는지 적는 법」이다.\
  NLL·`borrow later used here` 읽는 법이 거기 있다
- [**11번 주제**](../11-borrow-checker-rejections/)(빌림 검사기가 거부하는 전형) — **형제**.\
  **그쪽은** 거부되는 코드와 **처방의 모음**, **여기는** 수명 **표기와 생략 규칙**이다.\
  (7)의 `get_or_insert` 처방 모음은 그쪽이 정본이다
- [**08번 주제**](../08-ownership-and-move/)(소유권과 이동) — E0505·E0507 의 뿌리
- [**09번 주제**](../09-copy-clone-and-drop/)(`Copy`·`Clone`·`Drop`) — 값이 **언제 죽나**가 E0597 의 전제다
- [**04번 주제**](../04-expressions-and-semicolons/)(표현식 지향) — 「컴파일러에게 타입을 묻는」 수법의 출처
- 목록의 **13번 주제**(구조체에 참조 담기·`'static`의 두 의미) — ★ **여기는 표기와 생략 규칙까지**,\
  **참조를 필드로 담는 타입의 설계**와 `'static` 심화는 거기다
- 목록의 **14번 주제**(`String` 대 `&str`) · **32번 주제**(`impl Trait` 의 2024 수명 포착) ·\
  **42번 주제**(`RefCell`) · **47번 주제**(에디션 2021 대 2024) · **49번 주제**(스레드와 `'static`)
- [`../../언어-특성/README.md`](../../언어-특성/README.md) §4 — **그쪽은** 「**수명이라는 개념이 왜 필요한가**」,\
  **여기는** 「**그것을 코드에 어떻게 적고 언제 안 적어도 되나**」다
- [`../../../../../../history/rust/03-소유권-시스템.md`](../../../../../../history/rust/03-소유권-시스템.md) — 모델의 **역사**는 거기

## 용어 풀이

- **수명(lifetime)** — 참조가 유효한 코드 구간. 값의 수명이 아니라 **참조의 유효 구간**이다.
- **수명 파라미터(lifetime parameter)** — `'a`. `<>` 안에 선언하고 참조 타입에 붙인다.
- **생략(elision)** — 시그니처의 수명 칸을 컴파일러가 규칙으로 채우는 것. 규칙 3개.
- **익명 수명(`'_`)** — 「수명이 있긴 하다」만 적고 이름을 안 짓는 표기. 2018 에디션부터.
- **`'static`** — ① 참조 수명: 프로그램 끝까지. ② 트레이트 경계: 빌린 것을 안 품은 타입.
- **outlives 경계(`'a: 'b`)** — `'a` 가 `'b` 보다 짧지 않다. `T: 'a` 도 같은 기호·같은 뜻.
- **NLL(non-lexical lifetimes)** — 빌림 구간을 중괄호가 아니라 **마지막 사용 지점**으로 정하는 규칙.
- **HRTB(`for<'a>`)** — 「어떤 `'a` 에 대해서든」. 함수 포인터·클로저 타입에 나온다.
- **임시값(temporary)** — 이름이 없는 중간 값. `let` 에 직접 묶이면 **수명이 연장**되기도 한다(11번).
- **시그니처(signature)** — 함수의 이름·인자 타입·반환 타입. **빌림 검사가 보는 유일한 것**이다.

---

## 더 들어가면

- **수명은 타입 시스템의 일부이지 값이 아니다.** `'a` 를 인자로 넘길 수도, 런타임에 비교할 수도 없다.\
  오브젝트 파일이 같다는 실측이 그 한 면이다.
- ★ **`for<'a>`(HRTB)** 는 「어떤 수명이 와도 된다」는 뜻이다. (2)에서 컴파일러가 찍어 준 `for<'a> fn(&'a _) -> &'a _` 가 그것이고,\
  클로저를 인자로 받는 API 에서 자주 나온다(목록의 **34번 주제**·**35번 주제**).
- **반환 위치 `impl Trait`** 는 어떤 수명을 「포착」하는지가 **2024 에디션에서 바뀌었다** — 목록의 **32번 주제**.
- ★ **NLL 의 다음 단계**를 Rust 팀은 Polonius 라는 이름으로 부른다. (7)의 모양이 그 대표 사례다.\
  **이 문서에서는 나이틀리 플래그를 쓰지 않았다** — 안정판에서 되는 것만 실었다.
- **수명 생략은 `dyn Trait` 와 `Box<dyn Trait>` 에도 규칙이 따로 있다**(기본 객체 수명).\
  `Box<dyn Error>` 가 왜 `'static` 을 기본으로 갖는지가 거기서 나온다 — 목록의 **24번 주제**·**33번 주제**.
- ★ **`'a` 를 읽는 요령** — 시그니처에서 **같은 이름이 몇 번 나오는지**만 센다.\
  두 번 이상 나오면 **그 자리들이 한 덩어리로 묶였다**는 뜻이고, 그것이 호출부가 지게 될 제약의 전부다.
