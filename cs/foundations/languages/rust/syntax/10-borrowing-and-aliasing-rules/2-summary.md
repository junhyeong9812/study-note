# rust/syntax/10 — 빌림 `&`와 `&mut`, 별칭 규칙 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [The Rust Reference](https://doc.rust-lang.org/reference/types/pointer.html) 의 References 절 ·
> [The Rust Book ch.4.2](https://doc.rust-lang.org/book/ch04-02-references-and-borrowing.html) ·
> `rustc --explain E0499` / `E0502` / `E0503` / `E0596` / `E0382` / `E0204`.
> **실행 검증** — 이 문서의 모든 출력·에러·경고는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 얻은 것이다. `cargo` 는 쓰지 않았다.\
> ★ **`rustc ex.rs` 만 쓰면 에디션 2015 다.** 이 갈래는 `--edition 2021` 을 반드시 붙인다.\
> 소스 파일 이름은 전부 `ex.rs` 로 고정했고, **진단의 줄 번호는 그 파일 기준**이다.
> **버전** — `&`·`&mut` 문법은 1.0부터다. **NLL**(non-lexical lifetimes)에 관해 이 툴체인의\
> `releases.html` 에서 직접 확인한 두 줄 — **1.36.0**(2019-07-04) 「Non-Lexical Lifetimes are now enabled\
> on the 2015 edition.」 · **1.39.0**(2019-11-07) 「the NLL borrow checker is now a hard error in Rust 2018.」\
> 실측으로도 확인했다 — (3)절의 통과하는 파일은 **`--edition 2015` 로도 통과**한다(1.92.0 기준).\
> 본문 결과는 전부 **2021** 기준이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**잃지 않고 빌려주되, 고치는 사람은 한 번에 한 명이다.**

[**08번 주제**](../08-ownership-and-move/)가 「값을 넘기면 잃는다」였다면 여기는 「**잃지 않고 빌려주는 법**」이다.
그 대가가 **별칭 규칙**이다.

| 비유 | 실체 |
|---|---|
| 책을 빌려준다 — 주인은 그대로 나 | **빌림**(borrow) — `&x`. 소유권은 안 움직인다 |
| **읽기용 열람권** — 여러 명이 같이 봐도 된다 | **`&T`** 공유 빌림. 몇 개든 된다 |
| **편집권** — 한 명에게만 준다 | **`&mut T`** 가변 빌림. **하나뿐** |
| 편집권이 나가 있는 동안엔 **주인도 못 읽는다** | 가변 빌림 중엔 원본 이름도 못 쓴다(E0502) |
| 빌려준 쪽지 — 베껴도 된다 | **`&T` 는 `Copy`** |
| 편집권 쪽지 — 베끼면 편집자가 둘이 된다 | **`&mut T` 는 `Copy` 가 아니다** |
| **책을 마지막으로 본 순간** 대출이 끝난다 | **NLL** — 스코프 끝이 아니라 **마지막 사용**까지 |
| 편집자가 잠깐 남에게 넘겼다 돌려받는다 | **재빌림**(reborrow) — `&mut *r` |

- ★★ **별칭 규칙 한 줄** — 어느 한 시점에 **공유 빌림 여럿** 또는 **가변 빌림 하나**, 둘 중 하나만.
- `rustc --explain E0499` 가 같은 말을 한다 —\
  「you can either have many immutable references, or one mutable reference」.
- ★ **빌림이 사는 구간은 스코프가 아니라 「마지막 사용까지」다**. 이것이 NLL 이고, 실측으로 가른다.

```text
   허용되는 상태 (어느 한 시점)

   (가) 공유 빌림 여럿                  (나) 가변 빌림 하나
   s ──┬── &s ── r1 (읽기)              s ─── &mut s ── w (읽기·쓰기)
       ├── &s ── r2 (읽기)                    그동안 s 라는 이름도 못 쓴다
       └── &s ── r3 (읽기)
       s 로 읽는 것도 된다

   금지되는 상태

   (다) 공유 + 가변                     (라) 가변 + 가변
   s ──┬── &s     ── r  ← E0502         s ──┬── &mut s ── a  ← E0499
       └── &mut s ── w                      └── &mut s ── b
```

**언어도 똑같은 구조다.** 실측이 이 그림 그대로다.

```text
error[E0502]: cannot borrow `v` as mutable because it is also borrowed as immutable
error[E0499]: cannot borrow `s` as mutable more than once at a time
```

> **빌림(borrow)** — 소유권을 넘기지 않고 값을 가리키는 참조를 만드는 것.\
> 예: `f(&s)` 는 `s` 를 넘기지 않으므로 호출 뒤에도 `s` 가 산다.

> **참조(reference)** — 다른 값이 있는 자리를 가리키는 값. `&T`(공유)와 `&mut T`(가변) 두 종류다.\
> 예: `&s` 의 크기는 이 머신에서 8바이트다(포인터 하나).

> **별칭(alias)** — 같은 데이터에 닿는 길이 둘 이상인 상태.\
> 예: `&mut` 가 둘이면 한쪽이 고치는 동안 다른 쪽이 옛 값을 본다.

> **NLL(non-lexical lifetimes)** — 빌림이 사는 구간을 **중괄호가 아니라 마지막 사용 지점**으로 정하는 규칙.\
> 예: `let r = &v[0]; println!("{r}"); v.push(4);` 는 통과한다 — `r` 의 대출이 `println!` 에서 끝났다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **어떻게 안 잃고 넘기나** — `&`·`&mut` 가 08번의 「넘기면 잃는다」를 어떻게 푸나.
2. **동시에 몇 개까지 되나** — 별칭 규칙은 정확히 무엇을 금지하고, 어느 에러로 나타나나.
3. **그 빌림은 언제까지 사나** — 스코프 끝인가 마지막 사용인가, 그리고 그것을 어떻게 확인하나.

★ 08번이 「누가 주인인가」였다면 여기는 「**주인은 그대로 두고 누가 손대나**」다.

## 동작 방식

### (0) 이 주제가 쓰는 네 창

**언제 쓰나** — 아래 모든 절이 이 넷 중 하나로 접지한다.

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| **일부러 던져서 받는 컴파일 에러** | 별칭 규칙 — E0499·E0502·E0503·E0596 | 08의 「에러도 출력이다」 |
| **`rustc --explain`** | 그 규칙의 **공식 문장** | 08 |
| **`let _: () = 식;`** | 어떤 식이 **무슨 타입인지** 컴파일러에게 묻기 | [**04번 주제**](../04-expressions-and-semicolons/) |
| ★★ **같은 코드의 순서만 바꿔 던지기** | **NLL** — 마지막 사용 위치가 통과/거부를 가른다 | 이 주제가 세운다 |

★ 네 번째가 이 주제의 고유 창이다. **빌림이 언제 끝나는지는 에러 메시지 자체가 말해 준다** —
`immutable borrow later used here` 가 가리키는 줄이 곧 **대출 만료일**이다.

비용 — 없음. 전부 컴파일 타임이다.

### (1) 빌림의 기본 — 넘겨도 안 잃는다

**언제 쓰나** — 함수에 값을 주는 거의 모든 자리.

```text
===== 소스: ex.rs =====
// 빌림의 기본 — 넘겨도 안 잃는다, 공유는 여럿이 된다
fn borrow_len(s: &String) -> usize { s.len() }
fn append(s: &mut String) { s.push_str("!!"); }

fn main() {
    println!("(1) & 로 넘기면 원본이 산다 — 08 의 takes(s) 와 대비");
    let s = String::from("hello");
    let n = borrow_len(&s);
    println!("    길이 {} / 원본 {}", n, s);

    println!("(2) 공유 빌림은 여럿이 공존한다");
    let r1 = &s;
    let r2 = &s;
    let r3 = &s;
    println!("    {} {} {} / 원본 {}", r1, r2, r3, s);

    println!("(3) 가변 빌림은 하나만 — 그 동안 원본 이름도 못 쓴다");
    let mut t = String::from("bye");
    append(&mut t);
    println!("    {}", t);

    println!("(4) 참조가 가리키는 주소는 원본 그대로다");
    let p_owner = &t as *const String as usize;
    let rt = &t;
    let p_ref = rt as *const String as usize;
    println!("    같은 자리를 가리키나? {}", p_owner == p_ref);
    println!("    &String 자체의 크기 = {} 바이트", size_of::<&String>());
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
(1) & 로 넘기면 원본이 산다 — 08 의 takes(s) 와 대비
    길이 5 / 원본 hello
(2) 공유 빌림은 여럿이 공존한다
    hello hello hello / 원본 hello
(3) 가변 빌림은 하나만 — 그 동안 원본 이름도 못 쓴다
    bye!!
(4) 참조가 가리키는 주소는 원본 그대로다
    같은 자리를 가리키나? true
    &String 자체의 크기 = 8 바이트
(종료 코드 0)
```

```text
   08번 — 값으로 넘긴다                 10번 — 빌려준다
   main                takes            main                borrow_len
   s ──(이동)────────> s                s ──(&s)──────────> s: &String
   +-----------+                        +-----------+
   | s  [무효] |                        | s  hello  |  <- 그대로 산다
   +-----------+                        +-----------+
   반환 타입에 값을 얹어야 돌려받는다      반환 타입은 usize 그대로
   fn takes(s: String) -> (String, usize)  fn borrow_len(s: &String) -> usize
```

```text
   메모리에서 본 & — 새 칸 하나가 원본을 가리킨다
   스택                       힙
   +-----------+             +---------+
   | t  ptr ---+-----------> | bye!!   |
   |    len    |             +---------+
   |    cap    |                 ^
   +-----------+                 |
   | rt  ptr --+-----------------+     rt 는 t 의 스택 자리를 가리킨다 (8바이트)
   +-----------+                       같은 자리를 가리키나? true
```

그림 해설 (한 단계씩):

- **`&` 로 넘기면 반환 타입이 안 부푼다.** 08번 5번의 「돌려받기」가 필요 없어진다.
- **공유 빌림은 몇 개든 공존한다**(`r1`·`r2`·`r3` + 원본 `s` 까지 넷이 같이 읽었다).
- **참조 하나의 크기는 8바이트**(이 머신). `String` 24바이트를 옮기는 대신 8바이트를 준다.
- ★ 참조는 **원본과 같은 자리를 가리킨다**(`true`). 사본이 아니다.

비용 — 없음. 참조 만들기는 주소 하나를 적는 것이고, 규칙 검사는 컴파일 타임이다.

### (2) ★★ 별칭 규칙 — 공유 다수 또는 가변 하나

**언제 쓰나** — 같은 값에 두 길이 생기는 모든 자리. 이 절이 주제의 정점이다.

**(가) 공유가 살아 있는데 가변을 만들면 — E0502**

```text
===== 소스: ex.rs =====
// 공유 빌림이 살아 있는데 가변 빌림을 만들면?
fn main() {
    let mut v = vec![1, 2, 3];
    let first = &v[0];        // 공유 빌림
    v.push(4);                // 가변 빌림 (push 가 &mut self 를 받는다)
    println!("첫 원소 = {}", first);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0502]: cannot borrow `v` as mutable because it is also borrowed as immutable
 --> ex.rs:5:5
  |
4 |     let first = &v[0];        // 공유 빌림
  |                  - immutable borrow occurs here
5 |     v.push(4);                // 가변 빌림 (push 가 &mut self 를 받는다)
  |     ^^^^^^^^^ mutable borrow occurs here
6 |     println!("첫 원소 = {}", first);
  |                              ----- immutable borrow later used here

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0502`.
```

**(나) 가변을 둘 만들면 — E0499**

```text
===== 소스: ex.rs =====
// 가변 빌림을 둘 만들면?
fn main() {
    let mut s = String::from("안녕");
    let a = &mut s;
    let b = &mut s;
    a.push('!');
    b.push('?');
    println!("{a} {b}");
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0499]: cannot borrow `s` as mutable more than once at a time
 --> ex.rs:5:13
  |
4 |     let a = &mut s;
  |             ------ first mutable borrow occurs here
5 |     let b = &mut s;
  |             ^^^^^^ second mutable borrow occurs here
6 |     a.push('!');
  |     - first borrow later used here

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0499`.
```

`rustc --explain E0499`:

> Please note that in Rust, you can either have many immutable references, or one
> mutable reference.

**(다) 가변이 살아 있는데 원본 이름으로 읽으면 — 이것도 E0502**

```text
===== 소스: ex.rs =====
// 가변 빌림이 사는 동안 원본 이름을 쓰면?
fn main() {
    let mut s = String::from("안녕");
    let r = &mut s;
    println!("원본 이름으로 읽기 = {}", s);
    r.push('!');
    println!("{}", r);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0502]: cannot borrow `s` as immutable because it is also borrowed as mutable
 --> ex.rs:5:33
  |
4 |     let r = &mut s;
  |             ------ mutable borrow occurs here
5 |     println!("원본 이름으로 읽기 = {}", s);
  |                                         ^ immutable borrow occurs here
6 |     r.push('!');
  |     - mutable borrow later used here
  |
  = note: this error originates in the macro `$crate::format_args_nl` which comes from the expansion of the macro `println` (in Nightly builds, run with -Z macro-backtrace for more info)

error: aborting due to 1 previous error
```

```text
   별칭 규칙 — 어느 한 시점의 상태 넷

   (가) 공유 여럿           OK          (나) 가변 하나          OK
   v ──┬── &v ── r1                     s ─── &mut s ── w
       ├── &v ── r2                           s 는 그동안 못 쓴다
       └── v 로 읽기도 OK

   (다) 공유 + 가변       E0502         (라) 가변 + 가변      E0499
   v ──┬── &v     ── first              s ──┬── &mut s ── a
       └── &mut v ── push(4)                └── &mut s ── b

   (마) 가변 + 원본 읽기  E0502
   s ──┬── &mut s ── r
       └── s 로 읽기
```

그림 해설 (한 단계씩):

- **에러 번호가 상황을 가른다** — 서로 다른 종류가 섞이면 **E0502**, 가변이 둘이면 **E0499** 다.
- ★ (다)가 중요하다 — **`&mut` 를 내준 동안에는 원본 이름조차 읽을 수 없다.**\
  「주인이니까 읽는 건 되겠지」가 안 통한다. 읽기도 **공유 빌림**이기 때문이다.
- `v.push(4)` 가 가변 빌림인 이유 — **`push` 의 시그니처가 `fn push(&mut self, ...)`** 다.\
  ★ 메서드 호출은 **리시버 타입이 무엇을 요구하는지**로 읽어야 한다.
- ★ 에러의 **세 번째 줄 라벨**(`immutable borrow later used here`)이 이 주제의 열쇠다 —\
  컴파일러가 **그 빌림의 마지막 사용 지점**을 직접 짚어 준다. 다음 절이 그것을 쓴다.

비용 — 없음. 런타임 검사가 아니라 **대여 관계의 정적 검사**다.

### (3) ★★ NLL — 빌림은 「마지막 사용」까지만 산다

**언제 쓰나** — 「스코프 안에 있는데 왜 되지/안 되지」가 헷갈릴 때마다.

**같은 네 줄이다. 순서만 바꿨다.**

```text
===== 소스: ex.rs =====
// NLL — 같은 세 줄, 순서만 바꾼다 (가) 마지막 사용이 push 앞
fn main() {
    let mut v = vec![1, 2, 3];
    let first = &v[0];               // 공유 빌림 시작
    println!("첫 원소 = {}", first); // ★ first 의 마지막 사용 — 빌림은 여기서 끝난다
    v.push(4);                       // 가변 빌림
    println!("v = {:?}", v);
}                                    // first 라는 이름은 여기까지 스코프에 있다
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
첫 원소 = 1
v = [1, 2, 3, 4]
(종료 코드 0)
```

```text
===== 소스: ex.rs =====
// NLL — 같은 세 줄, 순서만 바꾼다 (나) 마지막 사용이 push 뒤
fn main() {
    let mut v = vec![1, 2, 3];
    let first = &v[0];               // 공유 빌림 시작
    v.push(4);                       // 가변 빌림
    println!("첫 원소 = {}", first); // ★ first 의 마지막 사용 — 빌림이 여기까지 산다
    println!("v = {:?}", v);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0502]: cannot borrow `v` as mutable because it is also borrowed as immutable
 --> ex.rs:5:5
  |
4 |     let first = &v[0];               // 공유 빌림 시작
  |                  - immutable borrow occurs here
5 |     v.push(4);                       // 가변 빌림
  |     ^^^^^^^^^ mutable borrow occurs here
6 |     println!("첫 원소 = {}", first); // ★ first 의 마지막 사용 — 빌림이 여기까지 산다
  |                              ----- immutable borrow later used here

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0502`.
```

**`&mut` 에서도 똑같다.**

```text
===== 소스: ex.rs =====
// E0499 도 마찬가지다 — 첫 빌림의 마지막 사용만 앞으로 옮긴다
fn main() {
    let mut s = String::from("안녕");
    let a = &mut s;
    a.push('!');          // ★ a 의 마지막 사용이 여기로 왔다
    let b = &mut s;
    b.push('?');
    println!("{b}");
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
안녕!?
(종료 코드 0)
```

```text
   (가) 통과                             (나) 거부

   3  let mut v = vec![1,2,3];           3  let mut v = vec![1,2,3];
   4  let first = &v[0];   ┐             4  let first = &v[0];   ┐
   5  println!("{first}"); ┘ 대출 구간   5  v.push(4);           │ 대출 구간
   6  v.push(4);             (4~5)       6  println!("{first}"); ┘  (4~6)
   7  println!("{v:?}");                 7  println!("{v:?}");
   8  }                                  8  }
      ^ first 는 여기까지 스코프에           ^ 스코프는 (가)와 똑같다
        있지만 대출은 5에서 끝났다
                                            5번 줄이 대출 구간 안이라 E0502
```

```text
   스코프(lexical)와 대출 구간(NLL)은 다른 것이다

   let first = &v[0];
        |
        +---- 이름의 스코프 ----------------------------> } 블록 끝
        +---- 대출 구간 ---> 마지막 사용
                             ^^^^^^^^^^
                             에러가 `borrow later used here` 로 짚어 주는 줄
```

그림 해설 (한 단계씩):

- ★★ **두 파일은 같은 네 줄이고 순서만 다르다.** 그런데 하나는 통과하고 하나는 E0502 다.
- 갈린 것은 **스코프가 아니다** — `first` 는 두 파일 모두 블록 끝까지 스코프에 있다.
- 갈린 것은 **마지막 사용 위치**다. 대출은 **마지막 사용에서 끝난다.**
- ★ **에러가 그 사실을 스스로 말한다** — `immutable borrow later used here` 는\
  「이 빌림이 **여기까지** 쓰이므로 그 사이에 가변을 못 만든다」는 뜻이다.
- **고치는 법이 곧 이것이다** — 충돌하는 줄 **앞으로 마지막 사용을 옮긴다**.\
  블록(`{ }`)으로 감싸는 것은 같은 일을 **명시적으로** 하는 것이다.
- ★ NLL 이전(2015 에디션 초기)에는 대출이 **스코프 끝까지** 살아서 (가)도 거부됐다.\
  지금 통과하는 것은 **규칙이 느슨해진 것이 아니라 정밀해진 것**이다.

비용 — 없음. 컴파일 타임 분석이다.

### (4) `&mut` 재빌림(reborrow) — 넘겨도 왜 안 죽나

**언제 쓰나** — `&mut` 를 함수에 두 번 넘길 때, 그리고 「`&mut` 는 `Copy` 가 아닌데 왜 되지」가 걸릴 때.

```text
===== 소스: ex.rs =====
// &mut 재빌림(reborrow) — 함수에 넘겨도 왜 안 죽나
fn bump(r: &mut i32) { *r += 1; }

fn main() {
    println!("(1) &mut 를 함수에 두 번 넘긴다 — 이동이면 두 번째가 막혀야 한다");
    let mut n = 0;
    let r = &mut n;
    bump(r);
    bump(r);
    println!("    n = {}", *r);

    println!("(2) 명시적 재빌림 &mut *r — 안쪽 빌림이 끝나면 바깥이 되살아난다");
    let mut m = 10;
    let outer = &mut m;
    {
        let inner = &mut *outer;    // outer 를 재빌림
        *inner += 5;
        println!("    inner 로 고친 뒤 = {}", *inner);
    }
    *outer += 1;                    // inner 의 마지막 사용이 지났으므로 outer 가 다시 쓰인다
    println!("    outer 로 고친 뒤 = {}", *outer);

    println!("(3) 재빌림 중에 바깥을 쓰면?");
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
(1) &mut 를 함수에 두 번 넘긴다 — 이동이면 두 번째가 막혀야 한다
    n = 2
(2) 명시적 재빌림 &mut *r — 안쪽 빌림이 끝나면 바깥이 되살아난다
    inner 로 고친 뒤 = 15
    outer 로 고친 뒤 = 16
(3) 재빌림 중에 바깥을 쓰면?
(종료 코드 0)
```

**재빌림이 살아 있는 동안 바깥을 쓰면 — E0503**

```text
===== 소스: ex.rs =====
// 재빌림 중에 바깥 참조를 쓰면?
fn main() {
    let mut k = 0;
    let out = &mut k;
    let inn = &mut *out;      // out 을 재빌림
    *out += 1;                // inn 이 아직 살아 있는데 out 을 쓴다
    *inn += 1;
    println!("{}", k);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0503]: cannot use `*out` because it was mutably borrowed
 --> ex.rs:6:5
  |
5 |     let inn = &mut *out;      // out 을 재빌림
  |               --------- `*out` is borrowed here
6 |     *out += 1;                // inn 이 아직 살아 있는데 out 을 쓴다
  |     ^^^^^^^^^ use of borrowed `*out`
7 |     *inn += 1;
  |     --------- borrow later used here

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0503`.
```

```text
   이동이라면 (실제로는 아니다)          재빌림 (실제)
   let r = &mut n;                      let r = &mut n;
   bump(r);   <- r 이 죽는다             bump(&mut *r);  <- 컴파일러가 이렇게 읽는다
   bump(r);   <- E0382                          |
                                                +-- bump 안에서만 사는 새 빌림
                                        bump(r);  <- r 은 그대로 살아 있다
```

```text
   재빌림의 계층 — 빌린 것을 또 빌려준다

   n (원본)
    └── outer : &mut n            빌린 동안 n 을 못 쓴다
          └── inner : &mut *outer  빌린 동안 outer 도 못 쓴다  ← E0503
                |
          inner 의 마지막 사용이 지나면
          └── outer 가 다시 쓰인다
```

그림 해설 (한 단계씩):

- `bump(r)` 을 두 번 불러도 통과한다 — **`&mut` 를 함수에 넘길 때 컴파일러가 자동으로 재빌림**하기 때문이다.
- 즉 `bump(r)` 은 사실상 **`bump(&mut *r)`** 이다. 새 빌림이 그 호출 동안만 살고 끝난다.
- ★ 그래서 **「`&mut` 는 `Copy` 가 아닌데 왜 여러 번 넘겨지나」의 답은 재빌림**이다. 복사가 아니다.
- 재빌림이 살아 있는 동안에는 **바깥 참조도 못 쓴다** — **E0503**. 계층이 한 겹 더 생긴 것뿐이다.
- 안쪽 빌림의 **마지막 사용이 지나면 바깥이 되살아난다**((2)의 `*outer += 1`) — NLL 이 여기도 적용된다.

비용 — 없음.

### (5) 역참조 `*` 와 자동 역참조

**언제 쓰나** — 참조로 값을 읽고 쓸 때.

```text
===== 소스: ex.rs =====
// 역참조 * 와 자동 역참조(메서드 호출)
fn main() {
    let mut n = 10;
    let r = &mut n;

    println!("(1) 읽고 쓸 때는 * 가 필요하다");
    println!("    *r = {}", *r);
    *r += 5;
    println!("    *r += 5 뒤 = {}", *r);

    println!("(2) 메서드 호출은 * 를 안 써도 된다 — 몇 겹이든 벗겨 준다");
    let s = String::from("안녕하세요");
    let rs: &String = &s;
    let rrs: &&String = &rs;
    let rrrs: &&&String = &rrs;
    println!("    s.len()       = {}", s.len());
    println!("    rs.len()      = {}", rs.len());
    println!("    rrs.len()     = {}", rrs.len());
    println!("    rrrs.len()    = {}", rrrs.len());
    println!("    (***rrrs).len() = {}", (***rrrs).len());

    println!("(3) 연산자는 한 겹까지만 — 자동 역참조가 아니라 std 의 impl 이다");
    let a = &5;
    let b = &7;
    println!("    a + b   = {}", a + b);      // impl Add<&i32> for &i32 가 있다
    println!("    *a + *b = {}", *a + *b);

    println!("(4) 비교는 참조끼리도 되지만 뜻이 다르다");
    let x = String::from("같다");
    let y = String::from("같다");
    println!("    x == y             {}", x == y);
    println!("    &x == &y           {}", &x == &y);              // 내용 비교
    println!("    ptr::eq(&x, &y)    {}", std::ptr::eq(&x, &y));  // 주소 비교
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
(1) 읽고 쓸 때는 * 가 필요하다
    *r = 10
    *r += 5 뒤 = 15
(2) 메서드 호출은 * 를 안 써도 된다 — 몇 겹이든 벗겨 준다
    s.len()       = 15
    rs.len()      = 15
    rrs.len()     = 15
    rrrs.len()    = 15
    (***rrrs).len() = 15
(3) 연산자는 한 겹까지만 — 자동 역참조가 아니라 std 의 impl 이다
    a + b   = 12
    *a + *b = 12
(4) 비교는 참조끼리도 되지만 뜻이 다르다
    x == y             true
    &x == &y           true
    ptr::eq(&x, &y)    false
(종료 코드 0)
```

★ **연산자에는 자동 역참조가 없다.** 한 겹 더 씌우면 드러난다.

```text
===== 소스: ex.rs =====
// 연산자에는 자동 역참조가 없다 — 한 겹 더 씌우면 드러난다
fn main() {
    let a = &5;
    let b = &7;
    println!("&i32 + &i32   = {}", a + b);     // std 가 impl Add<&i32> for &i32 를 준다
    let aa = &a;
    let bb = &b;
    println!("&&i32 + &&i32 = {}", aa + bb);   // 이건?
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0369]: cannot add `&&{integer}` to `&&{integer}`
 --> ex.rs:8:39
  |
8 |     println!("&&i32 + &&i32 = {}", aa + bb);   // 이건?
  |                                    -- ^ -- &&{integer}
  |                                    |
  |                                    &&{integer}

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0369`.
```

```text
   메서드 호출 — 겹을 다 벗긴다           연산자 — std 의 impl 이 있는 만큼만
   &&&String .len()                      &i32 + &i32    -> impl Add<&i32> for &i32 가 있다
      |                                  &&i32 + &&i32  -> 그런 impl 이 없다 -> E0369
      +-> &&String                       ★ 벗겨 주는 게 아니라 «미리 구현해 둔 것»이다
      +-> &String
      +-> String  ── len() 발견
```

그림 해설 (한 단계씩):

- **읽고 쓰는 자리에는 `*` 가 필요하다** — `*r`·`*r += 5`.
- **메서드 호출에는 안 붙여도 된다** — 컴파일러가 **겹을 벗겨 가며** 그 메서드를 찾는다(자동 역참조).\
  실측에서 **세 겹(`&&&String`)까지 그대로 불렸다.**
- ★ **연산자는 다르다.** `&i32 + &i32` 가 되는 것은 자동 역참조가 아니라\
  **std 가 `impl Add<&i32> for &i32` 를 미리 써 뒀기 때문**이다. 한 겹 더 씌우면 **E0369** 다.\
  ★ 내가 브리핑에서 「연산자는 자동 역참조가 없다」를 뭉뚱그려 두었다가 **한 번 뒤집힌 자리**다 —\
  「안 된다」가 아니라 「**되는 만큼만 미리 구현돼 있다**」가 맞다.
- `==` 는 **내용 비교**다. 주소를 비교하려면 **`std::ptr::eq`** 를 써야 한다(`false`).

비용 — 없음. 전부 컴파일 타임 해결이다.

### (6) `&T` 는 `Copy`, `&mut T` 는 아니다

**언제 쓰나** — 참조를 다른 이름에 담거나 구조체에 넣을 때.

```text
===== 소스: ex.rs =====
// & 는 Copy, &mut 는 아니다 — 같은 모양의 두 블록을 던진다
fn main() {
    println!("(가) &T 를 두 이름에 나눠 담는다");
    let n = 1;
    let r1 = &n;
    let r2 = r1;              // 복사인가 이동인가?
    println!("    r1 = {}, r2 = {}", r1, r2);

    println!("(나) &mut T 를 두 이름에 나눠 담는다");
    let mut m = 1;
    let w1 = &mut m;
    let w2 = w1;              // 여기가 갈린다
    *w2 += 1;
    println!("    w1 = {}, w2 = {}", w1, w2);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0382]: borrow of moved value: `w1`
  --> ex.rs:14:38
   |
11 |     let w1 = &mut m;
   |         -- move occurs because `w1` has type `&mut i32`, which does not implement the `Copy` trait
12 |     let w2 = w1;              // 여기가 갈린다
   |              -- value moved here
13 |     *w2 += 1;
14 |     println!("    w1 = {}, w2 = {}", w1, w2);
   |                                      ^^ value borrowed here after move
   |
   = note: this error originates in the macro `$crate::format_args_nl` which comes from the expansion of the macro `println` (in Nightly builds, run with -Z macro-backtrace for more info)

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0382`.
```

★ **(가) 쪽 줄에는 에러가 안 났다.** `&i32` 는 복사되고 `r1` 도 산다.

```text
   &T 가 Copy 여도 안전한 이유             &mut T 가 Copy 라면 (그래서 아니다)
   n ──┬── r1 (읽기)                       m ──┬── w1 (쓰기)
       └── r2 (읽기)                           └── w2 (쓰기)
   둘 다 읽기만 한다 = 별칭 규칙의 (가)      쓰기가 둘 = 별칭 규칙의 (라)
   이미 허용된 상태다                       «가변 하나» 가 공짜로 깨진다
```

그림 해설 (한 단계씩):

- **`&T` 는 `Copy` 다.** 복사해 봐야 **공유 빌림이 하나 더 생길 뿐**이고 그건 이미 허용된 상태다.
- **`&mut T` 는 `Copy` 가 아니다.** 만약 `Copy` 라면 `let w2 = w1;` 한 줄로 **가변 별칭이 공짜로** 생긴다.\
  ★ 그러면 이 주제의 규칙 전체가 무너진다. **그래서 타입 수준에서 막아 둔 것**이다.
- 09번이 인용한 `--explain E0204` 가 같은 말을 했다 —\
  `&mut T` is not `Copy`, even when `T` is `Copy` (this differs from the behavior for `&T`).
- **넘겨야 할 때는 이동이 아니라 재빌림**을 쓴다((4)절) — `f(&mut *w1)`, 또는 그냥 `f(w1)`.

비용 — 없음.

### (7) ★ 필드별 빌림 — 메서드를 거치면 안 된다

**언제 쓰나** — 구조체의 두 필드를 동시에 만질 때. **가장 자주 걸리는 실전 벽**이다.

**(가) 필드를 직접 짚으면 통과한다**

```text
===== 소스: ex.rs =====
// 필드별 빌림 (가) 필드를 직접 짚으면
struct S { a: String, b: String }

fn main() {
    let mut s = S { a: String::from("A"), b: String::from("B") };
    let ra = &mut s.a;          // a 만 가변 빌림
    let rb = &s.b;              // b 는 공유 빌림
    ra.push('!');
    println!("a = {} / b = {}", ra, rb);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
a = A! / b = B
(종료 코드 0)
```

**(나) 같은 일을 메서드로 하면 거부된다**

```text
===== 소스: ex.rs =====
// 필드별 빌림 (나) 같은 일을 메서드로 하면
struct S { a: String, b: String }

impl S {
    fn a_mut(&mut self) -> &mut String { &mut self.a }
    fn b_ref(&self) -> &String { &self.b }
}

fn main() {
    let mut s = S { a: String::from("A"), b: String::from("B") };
    let ra = s.a_mut();         // &mut self — 구조체 전체를 가변 빌림
    let rb = s.b_ref();         // &self    — 구조체 전체를 공유 빌림
    ra.push('!');
    println!("a = {} / b = {}", ra, rb);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0502]: cannot borrow `s` as immutable because it is also borrowed as mutable
  --> ex.rs:12:14
   |
11 |     let ra = s.a_mut();         // &mut self — 구조체 전체를 가변 빌림
   |              - mutable borrow occurs here
12 |     let rb = s.b_ref();         // &self    — 구조체 전체를 공유 빌림
   |              ^ immutable borrow occurs here
13 |     ra.push('!');
   |     -- mutable borrow later used here

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0502`.
```

```text
   (가) 필드를 직접 짚는다               (나) 메서드를 거친다
   s                                    s
   +-----------+                        +-----------+
   | a  ← &mut |  따로                  |  전체  ← &mut self  |
   | b  ← &    |  따로                  |        ← &self      | ← 겹친다
   +-----------+                        +-----------+
   검사기가 «칸 단위» 로 본다              시그니처에 «전체» 라고 적혀 있다
   -> 통과                               -> E0502
```

```text
   왜 갈리나 — 시그니처가 말하는 범위가 다르다

   &mut s.a        : 「s 의 a 칸」을 빌린다        -> 칸 하나
   s.a_mut()       : fn a_mut(&mut self)         -> s 전체
                              ^^^^^^^^^
                     반환값이 a 뿐이어도 «받은 것» 은 전체다
   ★ 검사기는 몸통을 안 본다. 시그니처만 본다.
```

그림 해설 (한 단계씩):

- ★ **필드를 직접 짚으면 검사기가 칸 단위로 본다** — 서로 다른 필드는 따로 빌릴 수 있다.\
  08번의 **부분 이동**(칸 단위 이동)과 **같은 결의 규칙**이다.
- **메서드를 거치면 칸 단위가 사라진다.** `fn a_mut(&mut self)` 는 **`s` 전체**를 가변 빌림한다.
- ★ **검사기는 메서드 몸통을 보지 않는다.** `a_mut` 가 사실 `a` 만 건드린다는 것을 알 방법이 없고,\
  시그니처가 계약이므로 **전체를 잡은 것으로 본다**. 이것이 **함수 단위 분석**의 대가다.
- 푸는 법 셋 — **① 필드를 직접 쓴다 ② 두 필드를 한 번에 돌려주는 메서드를 만든다\
  ③ 구조체를 쪼갠다**. 전형과 처방은 [**11번 주제**](../11-borrow-checker-rejections/)가 모은다.

비용 — 없음. 대가는 **API 모양이 규칙에 끌려가는 것**이다.

## 문법 — 형태와 규칙

### 형태

```rust
let r  = &x;          // 공유 빌림  : 읽기만
let w  = &mut x;      // 가변 빌림  : 읽기·쓰기. x 는 mut 바인딩이어야 한다
*w += 1;              // 역참조해서 쓴다
let rr = &mut *w;     // 재빌림 : w 를 빌린다

fn f(s: &String)       {}   // 빌려 받는다
fn g(s: &mut String)   {}   // 고칠 수 있게 빌려 받는다
fn h(s: String)        {}   // 08번 — 먹는다
```

- **`&mut x` 는 `x` 가 `mut` 바인딩일 때만** 된다 — 아니면 **E0596**.
- **`&` 는 타입에도 값에도 쓰인다** — `s: &String`(타입)과 `&s`(값 만들기).

### 금지 사례 — 던져서 받은 다섯

```text
let r = &mut s;  (s 가 mut 아님)     -> E0596  cannot borrow `s` as mutable, as it is not declared as mutable
let a = &mut s; let b = &mut s;      -> E0499  cannot borrow `s` as mutable more than once at a time
let r = &s;     s.push(..);          -> E0502  cannot borrow `s` as mutable because it is also borrowed as immutable
let r = &mut s; println!("{s}");     -> E0502  cannot borrow `s` as immutable because it is also borrowed as mutable
let inn = &mut *out; *out += 1;      -> E0503  cannot use `*out` because it was mutably borrowed
let w2 = w1;    (w1 이 &mut)         -> E0382  borrow of moved value: `w1`
```

★ **E0596 은 별칭 규칙이 아니라 「원본이 `mut` 인가」다**. 헷갈리기 쉬우니 갈라 둔다.

```text
===== 소스: ex.rs =====
// mut 이 아닌 바인딩을 가변 빌림하면?
fn main() {
    let s = String::from("불변");
    let r = &mut s;
    r.push('!');
    println!("{}", r);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0596]: cannot borrow `s` as mutable, as it is not declared as mutable
 --> ex.rs:4:13
  |
4 |     let r = &mut s;
  |             ^^^^^^ cannot borrow as mutable
  |
help: consider changing this to be mutable
  |
3 |     let mut s = String::from("불변");
  |         +++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0596`.
```

### 타입을 컴파일러에게 묻는 법

[**04번 주제**](../04-expressions-and-semicolons/)가 세운 수법을 그대로 쓴다 — **`let _: () = 식;`**.

```text
===== 소스: ex.rs =====
// 타입을 컴파일러에게 묻는다 — let _: () = 식;
fn main() {
    let mut v = vec![1, 2, 3];
    let s = String::from("hi");
    let _: () = &v;
    let _: () = &mut v;
    let _: () = &v[0];
    let _: () = &s;
    let _: () = &&s;
    let _: () = &*s;
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0308]: mismatched types
 --> ex.rs:5:17
  |
5 |     let _: () = &v;
  |            --   ^^ expected `()`, found `&Vec<{integer}>`
  |            |
  |            expected due to this
  |
  = note: expected unit type `()`
             found reference `&Vec<{integer}>`

error[E0308]: mismatched types
 --> ex.rs:6:17
  |
6 |     let _: () = &mut v;
  |            --   ^^^^^^ expected `()`, found `&mut Vec<{integer}>`
  |            |
  |            expected due to this
  |
  = note:      expected unit type `()`
          found mutable reference `&mut Vec<{integer}>`

error[E0308]: mismatched types
 --> ex.rs:7:17
  |
7 |     let _: () = &v[0];
  |            --   ^^^^^ expected `()`, found `&{integer}`
  |            |
  |            expected due to this

error[E0308]: mismatched types
 --> ex.rs:8:17
  |
8 |     let _: () = &s;
  |            --   ^^ expected `()`, found `&String`
  |            |
  |            expected due to this

error[E0308]: mismatched types
 --> ex.rs:9:17
  |
9 |     let _: () = &&s;
  |            --   ^^^ expected `()`, found `&&String`
  |            |
  |            expected due to this

error[E0308]: mismatched types
  --> ex.rs:10:17
   |
10 |     let _: () = &*s;
   |            --   ^^^ expected `()`, found `&str`
   |            |
   |            expected due to this

error: aborting due to 6 previous errors

For more information about this error, try `rustc --explain E0308`.
```

- 여섯 물음에 여섯 답이 한 번에 나온다. **`&*s` 가 `&str`** 인 것이 눈에 띈다 —\
  `String` 에 `*` 를 붙이면 `str` 이 되고, 거기에 `&` 를 붙여 `&str` 이 된다(**`Deref` 강제** — 목록의 **43번 주제**).
- ★ **여섯 줄이 서로 빌림 충돌을 안 냈다.** NLL 때문이다 — 각 임시 빌림이 그 줄에서 끝난다.

## 어디서 틀리나

### 1. ★★ 「스코프 안에 있으니 아직 빌려 간 상태겠지」

- 아니다. **NLL** 때문에 대출은 **마지막 사용**에서 끝난다((3)절).
- 증상 — 「블록으로 감싸야만 되는 줄 알았는데 그냥 순서만 바꿔도 됐다」.
- ★ 에러 메시지의 **`borrow later used here`** 줄이 **대출 만료일**을 알려 준다. 그 줄을 먼저 본다.

### 2. ★ 「읽기만 하는데 왜 막히지」

- `&mut` 가 나가 있는 동안에는 **원본 이름으로 읽는 것도 공유 빌림**이라 막힌다(E0502, (2)-(다)).
- 「주인이니까 읽는 건 되겠지」가 안 통한다.

### 3. ★★ 메서드로 감쌌더니 갑자기 막힌다

- (7)절이다. **`&mut self` 는 구조체 전체**를 잡는다. 필드를 직접 짚을 때와 결과가 다르다.
- ★ **리팩터링으로 코드를 메서드로 빼는 순간 E0499/E0502 가 새로 나는 일이 흔하다.**\
  검사기가 몸통을 안 보기 때문이고, 이것은 **버그가 아니라 계약 단위**다.

### 4. `&mut` 를 여러 번 넘기는 게 왜 되는지 모른다

- **재빌림**이다((4)절). 복사도 이동도 아니다.
- 반대로 `let w2 = w1;` 은 **진짜 이동**이라 `w1` 이 죽는다(E0382).
- ★ 둘의 차이는 「**함수 인자 자리인가 대입 자리인가**」다.

### 5. `*` 를 언제 쓰는지 헷갈린다

| 자리 | `*` 필요? |
|---|---|
| 메서드 호출 `r.len()` | **불필요** — 자동 역참조가 겹을 벗긴다 |
| 값 읽기 `println!("{}", *r)` | `{}` 는 `Display` 를 통하므로 **없어도 된다** |
| 산술·대입 `*r += 1` | **필요** |
| 값 자체를 꺼내기 `let v = *r;` | **필요**(그리고 `T: Copy` 여야 한다) |
| 연산자 `a + b`(둘 다 `&i32`) | **불필요** — 단 **std 가 그 impl 을 준 만큼만** |

### 6. `&String` 을 인자 타입으로 쓴다

- 돌아간다. 그러나 **`&str` 이 거의 항상 낫다** — 정본은 [목록의 **14번 주제**](../14-string-vs-str/)다.
- 여기서는 **`&*s` 가 `&str` 이라는 실측**까지만 둔다.

### 7. E0596 을 별칭 문제로 읽는다

- **`let mut` 이 빠진 것**이다. 별칭과 무관하다. `help` 가 `+++` 로 `mut` 을 넣으라고 직접 말한다.

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| 공유 빌림 여럿 **또는** 가변 하나 | **언어** | E0499·E0502 · `--explain E0499` 의 문장 |
| 가변 빌림 중엔 **원본 이름도 못 쓴다** | **언어** | E0502 실측 |
| `&T` 는 `Copy`, `&mut T` 는 아니다 | **언어** | E0382 실측 · `--explain E0204` |
| **빌림이 마지막 사용까지만 산다(NLL)** | **언어**(2018 에디션 이후) | ★ 순서만 바꾼 두 파일의 통과/거부 |
| 함수 인자 자리의 `&mut` 는 **재빌림** | **언어** | `bump(r)` 두 번 통과 |
| 필드를 직접 짚으면 **칸 단위 빌림** | **언어** | (7)-(가) 통과 |
| `&mut self` 메서드는 **전체**를 빌린다 | **언어**(시그니처가 계약) | (7)-(나) E0502 |
| 메서드 호출의 **자동 역참조** | **언어** | `&&&String` 에서 `len()` 통과 |
| 연산자가 **한 겹까지만** 되는 것 | **std 의 impl 범위** | `&&i32 + &&i32` → **E0369** |
| `&` 하나의 크기 8바이트 | **플랫폼**(64비트) | `size_of::<&String>()` 실측 |
| **참조가 원본과 같은 자리를 가리키는 것** | **언어(의미)** | 주소 비교 `true` |
| **주소 절댓값** | **런타임 ASLR** | 근거는 「같은가/다른가」뿐 |
| **에러 번호가 상황별로 갈리는 것** | **rustc 구현** | 번호는 안정적이지만 **문구와 `help` 는 바뀐다** |
| **빌림 검사가 런타임 비용을 안 내는 것** | **언어** | 전부 컴파일 타임 판정. 검사 결과는 코드 생성에 안 남는다 |

★ **NLL 은 지금은 에디션과 무관하다** — 이 툴체인에서 (3)절의 통과하는 파일을 **`--edition 2015`**
로 돌려도 통과했다. `releases.html` 이 그 사실을 1.36.0 항목(2015 에디션에 NLL 적용)으로 적어 둔다.
**옛 자료에서 「스코프 끝까지 빌림이 산다」를 읽었다면 그건 NLL 이전 이야기**다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 이유 |
|---|---|---|
| 읽기만 한다 | `&T` | 몇 개든 공존한다. **기본값** |
| 고쳐야 한다 | `&mut T` | 하나만. 그동안 원본도 못 쓴다 |
| 받은 쪽이 **끝까지 책임**진다 | 값으로 (`String`) | 08번 |
| `&mut` 를 함수에 또 넘긴다 | 그냥 넘긴다 | **재빌림**이 자동으로 된다 |
| `&mut` 를 다른 이름에 담아야 한다 | `&mut *w` (명시적 재빌림) | 그냥 대입하면 **이동**이다 |
| 두 필드를 동시에 만진다 | **필드를 직접 짚는다** | 메서드를 거치면 전체가 잡힌다 |
| 빌림 충돌이 난다 | ★ **마지막 사용을 앞으로 옮긴다** | NLL. 블록으로 감싸는 것도 같은 일 |
| 그래도 안 되면 | `clone`·인덱스·`split_at_mut`·`RefCell` | 전형과 처방은 [**11번 주제**](../11-borrow-checker-rejections/) |
| 참조를 **반환**해야 한다 | 수명 표기가 필요해진다 | [**12번 주제**](../12-lifetime-annotations-and-elision/) |

판단 규칙 두 줄.

- **`&` 로 시작하고, 고쳐야 할 때만 `&mut` 로 올린다.** 반대로 가면 충돌이 늘어난다.
- **충돌이 나면 먼저 「마지막 사용이 어디인가」를 본다.** 설계를 바꾸는 것은 그 다음이다.

## 핵심 문장

- ★★ **별칭 규칙** — 어느 한 시점에 **공유 빌림 여럿** 또는 **가변 빌림 하나**, 둘 중 하나만.
- 섞이면 **E0502**, 가변이 둘이면 **E0499**, 재빌림 중 바깥을 쓰면 **E0503**, 원본이 `mut` 이 아니면 **E0596**.
- **가변 빌림 중에는 원본 이름으로 읽는 것도 막힌다** — 읽기도 공유 빌림이다.
- ★★ **빌림은 스코프 끝이 아니라 「마지막 사용」까지 산다**(NLL).\
  같은 네 줄이라도 **순서만 바꾸면 통과와 거부가 갈린다.**
- 에러의 **`borrow later used here`** 줄이 곧 **그 빌림의 만료 지점**이다.
- **`&T` 는 `Copy` 고 `&mut T` 는 아니다** — 아니면 가변 별칭이 공짜로 생긴다.
- **함수 인자 자리의 `&mut` 는 이동이 아니라 재빌림**이다. 대입 자리는 이동이다.
- **메서드 호출은 자동 역참조로 겹을 다 벗긴다.** 연산자는 **std 가 impl 을 준 만큼만** 된다.
- ★ **필드는 따로 빌릴 수 있지만 `&mut self` 메서드를 거치면 전체가 잡힌다** — 검사기는 몸통을 안 본다.

## 관련 자료

- [`../README.md`](../README.md) — Rust 문법·API 주제 목록(이 주제는 10번)
- [**08번 주제**](../08-ownership-and-move/)(소유권과 이동) — ★ **직접 선행**. 「넘기면 잃는다」의 불편함이 여기로 이어진다.\
  **그쪽은 값을 넘기는 법, 여기는 안 넘기고 쓰는 법**이다
- [**09번 주제**](../09-copy-clone-and-drop/)(`Copy`·`Clone`·`Drop`) — **`&mut T` 가 `Copy` 가 아닌 것**의 판정 규칙이 거기 있다.\
  여기서는 **왜 그렇게 정했나**를 별칭 규칙으로 답한다
- [**04번 주제**](../04-expressions-and-semicolons/)(표현식 지향) — `let _: () = 식;` 으로 타입을 묻는 수법의 출처
- [**02번 주제**](../02-bindings-mut-and-shadowing/)(바인딩·`mut`) — `let mut` 이 무엇인지. E0596 은 거기로 돌아가는 에러다
- [**11번 주제**](../11-borrow-checker-rejections/)(빌림 검사기가 거부하는 전형) — **이 규칙에 걸리는 코드와 처방**의 모음
- [**12번 주제**](../12-lifetime-annotations-and-elision/)(수명 표기 `'a`) — **빌린 것이 원본보다 오래 살면 안 된다**를 표기로 적는 법
- [`../../언어-특성/README.md`](../../언어-특성/README.md) §3 — **그쪽은** 「**왜 별칭과 변경을 동시에 안 주나**」(모델의 논증),\
  **여기는** 「**그 규칙이 코드에서 어떤 에러로 나타나고 무엇으로 고치나**」다
- [`../../../../../../history/rust/03-소유권-시스템.md`](../../../../../../history/rust/03-소유권-시스템.md) — 모델의 **역사**는 거기
- [목록의 **14번 주제**](../14-string-vs-str/)(`String` 대 `&str`) · **37번 주제**(`IntoIterator` 세 형태) ·\
  **42번 주제**(`RefCell` 내부 가변성) · **43번 주제**(`Deref` 강제) · **56번 주제**(`unsafe`)

## 용어 풀이

- **빌림(borrow)** — 소유권을 안 넘기고 값을 가리키는 참조를 만드는 것.
- **참조(reference)** — 다른 값의 자리를 가리키는 값. `&T` 와 `&mut T` 두 종류.
- **공유 빌림(shared borrow)** — `&T`. 읽기만 되고 여러 개가 공존한다. **불변 빌림**과 같은 말.
- **가변 빌림(mutable borrow)** — `&mut T`. 읽기·쓰기가 되고 **하나뿐**이다. **배타 빌림**이라고도 한다.
- **별칭(alias)** — 같은 데이터에 닿는 길이 둘 이상인 상태.
- **별칭 규칙(aliasing rule)** — 「공유 여럿 **또는** 가변 하나」. 이 주제의 중심 규칙.
- **NLL(non-lexical lifetimes)** — 빌림 구간을 중괄호가 아니라 **마지막 사용 지점**으로 정하는 규칙.
- **재빌림(reborrow)** — 빌린 것을 다시 빌리는 것. `&mut *r`. 함수 인자 자리에서 자동으로 일어난다.
- **역참조(dereference)** — `*r` 로 참조가 가리키는 값에 닿는 것.
- **자동 역참조(auto-deref)** — 메서드를 찾을 때 컴파일러가 `*` 를 알아서 붙여 가는 것.
- **리시버(receiver)** — 메서드의 `self` 자리. `&self`·`&mut self`·`self` 중 무엇인지가 빌림 범위를 정한다.

---

## 더 들어가면

- **빌림 검사는 함수 단위**다. 호출된 함수의 몸통은 보지 않고 **시그니처만** 본다.\
  ★ 그래서 (7)-(나)가 거부되고, 같은 이유로 **시그니처가 곧 계약**이 된다.\
  「몸통을 보면 안전한데 거부되는」 자리의 모음은 [**11번 주제**](../11-borrow-checker-rejections/)에 있다.
- ★ **별칭 규칙은 최적화의 근거이기도 하다.** `&mut T` 가 유일하다는 것은 「다른 길로 이 값이 안 바뀐다」는 뜻이라
  컴파일러가 값을 레지스터에 붙들어 둘 수 있다. **다만 이 문서에서는 그 효과를 재지 않았다** — 수치를 적지 않는다.
- **`&` 는 두 자리에서 뜻이 다르다** — 타입 자리(`s: &String`)에서는 **타입**이고,\
  값 자리(`&s`)에서는 **참조를 만드는 연산**이다. 패턴 자리(`let &x = r;`)에서는 **벗기는** 뜻이 된다(목록의 **19번 주제**).
- **런타임으로 옮기는 길**이 `RefCell`/`Cell` 이다(목록의 **42번 주제**).\
  규칙이 사라지는 게 아니라 **위반이 컴파일 에러에서 패닉으로 바뀐다** — 11번에 실측이 있다.
- **스레드 경계를 넘는 공유**는 같은 규칙 위에 `Send`/`Sync` 가 얹힌다(목록의 **50번 주제**·**52번 주제**).\
  `Arc<Mutex<T>>` 가 「공유 다수」와 「가변 하나」를 **런타임 비용을 내고** 동시에 얻는 모양이다.
- ★ **`&mut` 를 「mutable reference」가 아니라 「exclusive reference」로 읽으면 헷갈림이 줄어든다.**\
  중요한 성질은 「고칠 수 있다」가 아니라 「**나 말고 아무도 없다**」다.
