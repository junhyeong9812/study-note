# rust/syntax/20 — `if let`·`while let`·`let else`(1.65)·`let` 체인(2024 에디션·1.88) — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [The Rust Reference — `if let` expressions](https://doc.rust-lang.org/reference/expressions/if-expr.html) ·
> [Reference — `let` statements](https://doc.rust-lang.org/reference/statements.html#let-statements) ·
> [Reference — Destructors (temporary scopes)](https://doc.rust-lang.org/reference/destructors.html) ·
> [Edition Guide — Rust 2024](https://doc.rust-lang.org/edition-guide/rust-2024/).
> ★ `rustc --explain E0308` 은 **확인용으로만 열었고 본문에 옮기지 않았다.**
> **실행 검증** — 이 문서의 모든 출력·에러는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 또는 **`rustc --edition 2024 ex.rs -o ex`** 로 실제로 돌려 받은 것이다.\
> **손으로 옮겨 적은 출력은 한 줄도 없다.**\
> ★★★ **이 주제는 에디션이 본체다.** 에디션을 안 밝힌 결과는 이 주제에서 아무 뜻이 없다.\
> 두 에디션을 비교한 자리는 **표준 배너로 한 판씩 따로** 실었다 — 배너의 `--edition` 숫자가 유일한 차이다.\
> ★★ **`rustc ex.rs` 만 쓰면 에디션 2015 다** — 이 주제의 절반이 안 돌아간다.
> **버전** — `if let`·`while let` 은 1.0.0부터다. **`let else` 는 1.65.0**부터이고 **에디션과 무관**하다.\
> **`let` 체인은 1.88.0 + 2024 에디션**이라야 한다. **`if let` 임시값 스코프 변경은 2024 에디션**이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | 패닉 첫 줄 `thread 'main' (…)` 괄호 안의 OS 스레드 id | 실행마다 커널이 주는 번호다 — (5)의 2021 판에 나온다 |
| **흔들린다** | `0x…` 주소 | 실행마다 다르다 |
| 안 흔들린다 | 패닉 메시지 본문·`파일:줄:칸`·`note: run with RUST_BACKTRACE=1 …` | 같은 소스·같은 판에서 고정이다 |
| 안 흔들린다 | **종료 코드 101**(패닉) · `0` · `1` | 고정이다 |
| 안 흔들린다 | `drop` 이 찍히는 **순서** | 에디션이 정한다 — 이 주제의 핵심 근거다 |
| 안 흔들린다 | 에러 번호·제목·`= note:`·`= help:` | 같은 rustc 판에서 고정이다 |

## 한눈에 — 쉽게 말하면

**`match` 를 접는 세 가지 접개와, 조건을 잇는 `&&` 다.**

`match` 는 모든 갈래를 적게 한다. 그런데 갈래 하나만 궁금할 때가 많다 — 그때 쓰는 도구들이다.

| 비유 | 실체 |
|---|---|
| 「**맞으면 들어가고 아니면 지나간다**」 | **`if let`** — 한 갈래만 본다. `else` 도 붙는다 |
| 「**맞는 동안 계속 돈다**」 | **`while let`** — 안 맞는 순간 루프가 끝난다 |
| ★ 「**맞으면 꺼내서 바깥으로, 아니면 여기서 나간다**」 | **`let else`**(1.65) — 성공값이 **바깥 스코프**로 나온다 |
| ★★ 조건 여럿을 **`&&` 로 잇기** | **`let` 체인** — **2024 에디션 + 1.88** 이라야 한다 |
| 접개를 쓰면 **점검표가 사라진다** | ★ `if let` 계열에는 **완전성 검사가 없다**((7)) |

- ★★★ **이 주제의 축은 에디션이다.** 같은 소스가 **2021 에서 에러, 2024 에서 통과**하는 자리가 둘 있다 —
  **`let` 체인**((4))과 **`if let` 임시값 스코프**((5)).
- ★★ **`let else` 의 `else` 는 「나가야」 한다.** 값을 내면 E0308 이고, 진단이 `` expected `!` `` 라고 적는다((3)).
- ★ **`let else` 가 다른 둘과 갈리는 점** — 꺼낸 값이 **블록 안이 아니라 바깥에** 남는다. 들여쓰기가 안 깊어진다.

```text
   같은 일을 네 가지로 — 무엇이 어디에 남나

   match          if let         let else          조합 메서드
   ┌─────────┐    ┌─────────┐    ┌────────────┐    ┌─────────────┐
   │ 갈래 전부│    │ 한 갈래 │    │ 실패면 나감 │    │ Option 전용 │
   │ 값이 남음│    │ 값이 블록│    │ ★ 값이 바깥 │    │ 값이 이어짐 │
   │         │    │  안에만 │    │   에 남음   │    │             │
   └─────────┘    └─────────┘    └────────────┘    └─────────────┘
    완전성 O       완전성 X        완전성 X           해당 없음

   let else 가 들여쓰기를 없애는 방식

     if let Ok(n) = s.parse() {          let Ok(n) = s.parse() else {
         if let Some(d) = n.checked_mul(2) {   return Err(..);
             ...                         };
         }                               let Some(d) = n.checked_mul(2) else {
     }                                       return Err(..);
     └ 「성공 경로」가 안쪽으로 밀린다   };
                                         ...   ← 성공 경로가 「평평하게」 남는다
```

> **`if let`** — 패턴이 맞으면 그 블록을, 아니면 `else` 를 실행한다. **식**이라 값을 낼 수 있다.

> **`while let`** — 패턴이 맞는 동안 반복한다. 안 맞는 순간 루프가 끝난다.

> **`let else`** — 패턴이 맞으면 바깥 스코프에 바인딩을 만들고,\
> 안 맞으면 `else` 블록을 실행한다. **`else` 는 반드시 발산**해야 한다.

> **발산(diverge)** — 그 자리에서 제어가 안 돌아오는 것. `return`·`break`·`continue`·`panic!`·`process::exit`.\
> 타입으로는 **`!`**(never)다([**06번 주제**](../06-functions-and-never-type/)).

> **`let` 체인** — `if let A = a && let B = b && cond` 처럼 `let` 과 조건을 `&&` 로 잇는 것.\
> **2024 에디션 + rustc 1.88.0** 이라야 한다.

## 이 주제가 답하려는 질문

1. **얕은 `match` 를 언제 접나** — 네 도구 중 무엇을 고르나((6)).
2. **`let else` 의 `else` 에 무엇을 적을 수 있나** — 그리고 왜 그것만 되나((3)).
3. **에디션이 무엇을 바꾸나** — 같은 소스가 갈리는 자리 둘을 한 판씩 던져서 본다((4)·(5)).

★ [**19번 주제**](../19-pattern-syntax-guards-bindings-and-match-ergonomics/)가 「한 팔 안의 문법」이었다면
여기는 **반박 가능한 패턴을 `match` 밖에서 쓰는 자리들**이다.

## 동작 방식

### (0) 이 주제가 쓰는 네 창

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **같은 소스를 두 에디션에 던지기** | `let` 체인이 어느 쪽에서 되나 — **한쪽만 된다** | ★ 이 주제의 고유 창 |
| ★★ **`Drop` 이 찍는 순서 읽기** | 임시값이 **언제 죽나** — 2021 과 2024 가 갈린다 | ★ 이 주제의 고유 창 |
| **`RefCell` 로 빌림을 런타임에 터뜨리기** | 그 차이가 **코드의 성패**를 가르는 것 | ★ 이 주제의 고유 창 |
| **일부러 던져서 받는 E0308** | `let else` 의 `else` 가 무엇을 요구하나 — `expected !` | [**11번 주제**](../11-borrow-checker-rejections/) |

★★★ 첫 창이 본체다. **에디션을 안 밝히면 이 주제의 결론은 전부 무효**다.
`--edition 2021` 과 `--edition 2024` 를 **나란히 던져** 한쪽만 되는 것을 보인다.
★ 배너는 표준형 하나만 쓰고 **한 판씩 따로** 싣는다 — 여러 실행을 배너 하나에 묶으면 기계 재검증이 깨진다.

### (1) `if let` — 한 갈래만 본다

**언제 쓰나** — 나머지 갈래에 할 일이 없을 때. `match` 의 `_ => {}` 가 보이면 그 자리다.

```text
===== 소스: ex.rs =====
// ex.rs
// if let — 「한 갈래만 궁금할 때」 match 를 접는다. else 도 붙는다
#[derive(Debug)]
enum Cfg { Port(u16), Host(String), Off }

fn main() {
    let items = vec![Cfg::Port(8080), Cfg::Host(String::from("localhost")), Cfg::Off];
    for c in &items {
        // ① 값이 필요 없으면 문으로
        if let Cfg::Port(p) = c {
            println!("① 포트 {}", p);
        }
        // ② else 를 붙이면 두 갈래가 된다
        if let Cfg::Host(h) = c {
            println!("② 호스트 {}", h);
        } else {
            println!("② 호스트 아님 {:?}", c);
        }
    }
    // ③ if let 도 식이다 — 두 갈래 타입이 같으면 값을 낸다
    let first = &items[0];
    let n: u16 = if let Cfg::Port(p) = first { *p } else { 0 };
    println!("③ {}", n);
    // ④ else if 로 잇는다
    let c = &items[1];
    let s = if let Cfg::Port(p) = c { format!("포트 {}", p) }
            else if let Cfg::Host(h) = c { format!("호스트 {}", h) }
            else { String::from("꺼짐") };
    println!("④ {}", s);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
① 포트 8080
② 호스트 아님 Port(8080)
② 호스트 localhost
② 호스트 아님 Off
③ 8080
④ 호스트 localhost
(종료 코드 0)
```

읽는 법.

- ① `else` 없이 **문**으로 쓴다. 안 맞으면 아무 일도 안 일어난다.
- ② `else` 를 붙이면 두 갈래다.
- ③ ★ **`if let` 도 식이다.** 두 갈래 타입이 같으면 값을 낸다 — `let n: u16 = if let … { *p } else { 0 };`.
  `else` 가 없으면 **양쪽이 `()`** 여야 한다.
- ④ `else if let` 으로 잇는다. ★ 이 사슬이 길어지면 **`match` 로 되돌리는 것**이 낫다((6)).

### (2) `while let` — 맞는 동안 돈다

**언제 쓰나** — 꺼낼 것이 없어질 때까지 꺼낼 때. `pop`·`next`·큐 비우기가 전형이다.

```text
===== 소스: ex.rs =====
// ex.rs
// while let — 「패턴이 맞는 동안」 돈다. 맞지 않는 순간 루프가 끝난다
fn main() {
    // ① 스택을 비울 때까지
    let mut stack = vec![1, 2, 3, 4];
    while let Some(top) = stack.pop() {
        println!("① {} 남은 {:?}", top, stack);
    }

    // ② 이터레이터를 직접 돌린다 — for 가 감추는 것을 펼친 모습
    let v = vec!["가", "나", "다"];
    let mut it = v.iter();
    while let Some(s) = it.next() {
        println!("② {}", s);
    }

    // ③ 슬라이스를 앞에서부터 갉아 먹는다
    let mut rest: &[i32] = &[10, 20, 30];
    while let [head, tail @ ..] = rest {
        println!("③ {} 남은 {:?}", head, tail);
        rest = tail;
    }

    // ④ 조건이 처음부터 안 맞으면 한 번도 안 돈다
    let mut empty: Vec<i32> = Vec::new();
    while let Some(x) = empty.pop() { println!("④ {}", x); }
    println!("④ 한 번도 안 돌았다 {:?}", empty);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
① 4 남은 [1, 2, 3]
① 3 남은 [1, 2]
① 2 남은 [1]
① 1 남은 []
② 가
② 나
② 다
③ 10 남은 [20, 30]
③ 20 남은 [30]
③ 30 남은 []
④ 한 번도 안 돌았다 []
(종료 코드 0)
```

읽는 법.

- ① `stack.pop()` 이 `None` 을 내는 순간 루프가 끝난다.
- ② `it.next()` 를 직접 돌린다 — **`for` 가 감추는 것을 펼친 모습**이다([**05번 주제**](../05-control-flow-loops-and-labels/)).
- ③ 슬라이스를 **앞에서부터 갉아 먹는다** — 19번 주제의 `[head, tail @ ..]` 를 `while let` 에 얹은 것이다.
- ④ 처음부터 안 맞으면 **한 번도 안 돈다.** `loop { match … }` 와 달리 진입 검사가 먼저다.

### (3) ★ `let else` — 꺼낸 값이 바깥에 남는다

**언제 쓰나** — 「실패면 여기서 끝」이고 성공 경로가 길 때. **조기 반환 관용구**다.

```text
===== 소스: ex.rs =====
// ex.rs
// let else (1.65) — 「맞으면 바깥으로 꺼내고, 아니면 나간다」
fn parse(s: &str) -> Result<u32, String> {
    let Ok(n) = s.parse::<u32>() else {
        return Err(format!("{:?} 는 수가 아니다", s));
    };
    let Some(doubled) = n.checked_mul(2) else {
        return Err(format!("{} 는 두 배가 안 된다", n));
    };
    Ok(doubled)                       // ★ n·doubled 가 이 줄에서도 살아 있다
}

fn main() {
    for s in ["21", "가", "4294967295"] {
        println!("{:?} -> {:?}", s, parse(s));
    }
    // else 는 continue·break 로도 나간다
    let mut sum = 0u32;
    for s in ["1", "x", "2", "y", "3"] {
        let Ok(n) = s.parse::<u32>() else { continue };
        sum += n;
    }
    println!("합 {}", sum);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
"21" -> Ok(42)
"가" -> Err("\"가\" 는 수가 아니다")
"4294967295" -> Err("4294967295 는 두 배가 안 된다")
합 6
(종료 코드 0)
```

읽는 법.

- ★★ **`n` 과 `doubled` 가 `else` 블록 밖, 즉 함수 본문에 남는다.** `if let` 이면 블록 안에만 있다.
- `else` 에 `return`·`continue`·`break`·`panic!` 을 적는다. **제어가 안 돌아와야** 한다.
- `"4294967295"` 가 `checked_mul` 에서 걸린 것에 주목 — `let else` 를 **연달아** 쓰면 조건이 층층이 쌓이는데도
  들여쓰기가 안 깊어진다.

**`else` 가 값을 내면 거부된다.**

```text
===== 소스: ex.rs =====
// ex.rs
// let else 의 else 는 「나가야」 한다 — 값을 내면 거부된다
fn main() {
    let text = "가";
    let Ok(n) = text.parse::<u32>() else {
        0
    };
    println!("{}", n);

    let Some(m) = Some(1) else {
        println!("없다");
    };
    println!("{}", m);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0308]: `else` clause of `let...else` does not diverge
 --> ex.rs:5:42
  |
5 |       let Ok(n) = text.parse::<u32>() else {
  |  __________________________________________^
6 | |         0
7 | |     };
  | |_____^ expected `!`, found integer
  |
  = note: expected type `!`
             found type `{integer}`
  = help: try adding a diverging expression, such as `return` or `panic!(..)`
  = help: ...or use `match` instead of `let...else`

error[E0308]: `else` clause of `let...else` does not diverge
  --> ex.rs:10:32
   |
10 |       let Some(m) = Some(1) else {
   |  ________________________________^
11 | |         println!("없다");
12 | |     };
   | |_____^ expected `!`, found `()`
   |
   = note:   expected type `!`
           found unit type `()`
   = help: try adding a diverging expression, such as `return` or `panic!(..)`
   = help: ...or use `match` instead of `let...else`

error: aborting due to 2 previous errors

For more information about this error, try `rustc --explain E0308`.
(종료 코드 1)
```

- **E0308** `` `else` clause of `let...else` does not diverge ``.
- ★★ `` = note: expected type `!` `` — **`!`(never) 타입을 기대한다.** 정수를 내면
  `` found type `{integer}` ``, `println!` 로 끝내면 `` found unit type `()` `` 다.
  ★ **`()` 도 「값을 냈다」로 본다** — 아무것도 안 하는 것과 발산하는 것은 다르다.
- `= help:` 둘이 처방을 준다 — **`return`·`panic!(..)` 같은 발산 식**을 쓰거나 **`match` 를 대신 쓰라**고.
- `!` 가 어떤 타입으로도 강제되는 이유는 [**06번 주제**](../06-functions-and-never-type/)가 정본이다.

### (4) ★★★ `let` 체인 — 2021 에서 에러, 2024 에서 통과

**언제 쓰나** — 「A 도 있고 B 도 있고 그 둘이 어떤 관계일 때」. 그 전에는 `if let` 을 중첩해야 했다.

**같은 소스를 2021 에 던진다.**

```text
===== 소스: ex.rs =====
// ex.rs
// let 체인 — if let 을 && 로 잇는다. 어느 에디션에서 되나
fn lookup(k: &str) -> Option<u32> {
    match k { "a" => Some(1), "b" => Some(2), _ => None }
}

fn main() {
    let x = lookup("a");
    let y = lookup("b");
    if let Some(a) = x && let Some(b) = y && a < b {
        println!("둘 다 있고 {} < {}", a, b);
    } else {
        println!("아니다");
    }

    let mut src = vec![Some(1), Some(2), None, Some(3)];
    while let Some(item) = src.pop() && let Some(n) = item {
        println!("꺼냄 {}", n);
    }
    println!("남은 {:?}", src);
}
===== rustc --edition 2021 ex.rs -o ex =====
error: let chains are only allowed in Rust 2024 or later
  --> ex.rs:10:8
   |
10 |     if let Some(a) = x && let Some(b) = y && a < b {
   |        ^^^^^^^^^^^^^^^

error: let chains are only allowed in Rust 2024 or later
  --> ex.rs:10:27
   |
10 |     if let Some(a) = x && let Some(b) = y && a < b {
   |                           ^^^^^^^^^^^^^^^

error: let chains are only allowed in Rust 2024 or later
  --> ex.rs:17:11
   |
17 |     while let Some(item) = src.pop() && let Some(n) = item {
   |           ^^^^^^^^^^^^^^^^^^^^^^^^^^

error: let chains are only allowed in Rust 2024 or later
  --> ex.rs:17:41
   |
17 |     while let Some(item) = src.pop() && let Some(n) = item {
   |                                         ^^^^^^^^^^^^^^^^^^

error: aborting due to 4 previous errors

(종료 코드 1)
```

**같은 소스를 2024 에 던진다.**

```text
===== 소스: ex.rs =====
// ex.rs
// let 체인 — if let 을 && 로 잇는다. 어느 에디션에서 되나
fn lookup(k: &str) -> Option<u32> {
    match k { "a" => Some(1), "b" => Some(2), _ => None }
}

fn main() {
    let x = lookup("a");
    let y = lookup("b");
    if let Some(a) = x && let Some(b) = y && a < b {
        println!("둘 다 있고 {} < {}", a, b);
    } else {
        println!("아니다");
    }

    let mut src = vec![Some(1), Some(2), None, Some(3)];
    while let Some(item) = src.pop() && let Some(n) = item {
        println!("꺼냄 {}", n);
    }
    println!("남은 {:?}", src);
}
===== rustc --edition 2024 ex.rs -o ex =====
===== ./ex =====
둘 다 있고 1 < 2
꺼냄 3
남은 [Some(1), Some(2)]
(종료 코드 0)
```

읽는 법.

- ★★★ **한 글자도 안 바꾼 같은 파일**인데 2021 은 에러 넷, 2024 는 통과다.
  다른 것은 배너의 **`--edition` 숫자 하나**뿐이다.
- 에러 문구는 `error: let chains are only allowed in Rust 2024 or later` 다.
  ★ **번호가 없다.** `error[E0xxx]` 가 아니고 `For more information …` 줄도 안 붙는다 —
  타입 오류가 아니라 **파서가 에디션으로 막는 것**이기 때문이다.
- 에러가 **넷**인 이유는 `let` 이 넷이기 때문이다 — `if let` 에 둘, `while let` 에 둘.
  **`&&` 개수가 아니라 `let` 개수**를 센다.
- ★★ **`while let` 체인의 결과를 잘 보라.** 출력이 「꺼냄 3」 하나뿐이고 남은 것이 `[Some(1), Some(2)]` 다.
  `src.pop()` 이 `None` 을 꺼낸 순간 **뒤쪽 `let Some(n) = item` 이 실패해 루프가 끝났는데,
  `pop()` 은 이미 일어났다.** ★ **앞 고리의 부작용은 뒤 고리가 실패해도 남는다** — 체인의 함정이다.
- 버전도 함께 필요하다 — **1.88.0 미만**에서는 2024 에디션이어도 안 된다.

### (5) ★★★ `if let` 의 임시값 스코프 — 2024 에서 바뀐 것

**언제 쓰나** — 조건 자리에 **임시값**(락 가드·`RefCell` 빌림·`Drop` 이 있는 값)을 쓸 때.

**같은 소스를 2021 에 던진다.**

```text
===== 소스: ex.rs =====
// ex.rs
// if let 의 「조건 자리 임시값」이 언제 죽나 — 에디션으로 갈린다
struct Noisy(&'static str);

impl Drop for Noisy {
    fn drop(&mut self) { println!("   drop {}", self.0); }
}

impl Noisy {
    fn peek(&self) -> Option<u32> { if self.0 == "있음" { Some(1) } else { None } }
}

fn main() {
    println!("A 참 갈래 진입 전");
    if let Some(v) = Noisy("있음").peek() {
        println!("   then {}", v);
    } else {
        println!("   else");
    }
    println!("A if 끝난 뒤");

    println!("B 거짓 갈래 진입 전");
    if let Some(v) = Noisy("없음").peek() {
        println!("   then {}", v);
    } else {
        println!("   else");
    }
    println!("B if 끝난 뒤");

    println!("C match 는 어떤가");
    match Noisy("있음").peek() {
        Some(v) => println!("   then {}", v),
        None => println!("   none"),
    }
    println!("C match 끝난 뒤");
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
A 참 갈래 진입 전
   then 1
   drop 있음
A if 끝난 뒤
B 거짓 갈래 진입 전
   else
   drop 없음
B if 끝난 뒤
C match 는 어떤가
   then 1
   drop 있음
C match 끝난 뒤
(종료 코드 0)
```

**같은 소스를 2024 에 던진다.**

```text
===== 소스: ex.rs =====
// ex.rs
// if let 의 「조건 자리 임시값」이 언제 죽나 — 에디션으로 갈린다
struct Noisy(&'static str);

impl Drop for Noisy {
    fn drop(&mut self) { println!("   drop {}", self.0); }
}

impl Noisy {
    fn peek(&self) -> Option<u32> { if self.0 == "있음" { Some(1) } else { None } }
}

fn main() {
    println!("A 참 갈래 진입 전");
    if let Some(v) = Noisy("있음").peek() {
        println!("   then {}", v);
    } else {
        println!("   else");
    }
    println!("A if 끝난 뒤");

    println!("B 거짓 갈래 진입 전");
    if let Some(v) = Noisy("없음").peek() {
        println!("   then {}", v);
    } else {
        println!("   else");
    }
    println!("B if 끝난 뒤");

    println!("C match 는 어떤가");
    match Noisy("있음").peek() {
        Some(v) => println!("   then {}", v),
        None => println!("   none"),
    }
    println!("C match 끝난 뒤");
}
===== rustc --edition 2024 ex.rs -o ex =====
===== ./ex =====
A 참 갈래 진입 전
   then 1
   drop 있음
A if 끝난 뒤
B 거짓 갈래 진입 전
   drop 없음
   else
B if 끝난 뒤
C match 는 어떤가
   then 1
   drop 있음
C match 끝난 뒤
(종료 코드 0)
```

```text
   조건 자리의 임시값이 언제 죽나 — 거짓 갈래에서만 갈린다

   2021                                 2024
   ┌ 조건 평가 — 임시값 태어남           ┌ 조건 평가 — 임시값 태어남
   │ 패턴이 안 맞는다                    │ 패턴이 안 맞는다
   │ else 블록 실행                      │ ★ 임시값 죽음   ← 여기가 앞으로 왔다
   │   ← 임시값이 아직 살아 있다          │ else 블록 실행
   └ 임시값 죽음                         └   ← 임시값이 이미 없다

   참 갈래(A)는 양쪽이 같다 — 본문이 꺼낸 값을 써야 하므로 끝까지 산다
   match(C)도 양쪽이 같다 — 2024 가 안 건드렸다

   그래서 「2021 에서 터지던 코드」가 2024 에서 돈다
       if let Some(v) = *cell.borrow() { … } else { *cell.borrow_mut() = … }
                         └ 이 빌림이 else 까지 사느냐 마느냐
```

읽는 법.

- ★★★ **갈리는 자리는 B 하나뿐이다.**

| 자리 | 2021 | 2024 |
|---|---|---|
| A (참 갈래) | `then 1` → `drop 있음` | `then 1` → `drop 있음` — **같다** |
| **B (거짓 갈래)** | **`else` → `drop 없음`** | **`drop 없음` → `else`** |
| C (`match`) | `then 1` → `drop 있음` | `then 1` → `drop 있음` — **같다** |

- **2021** — 조건 자리의 임시값이 **`if let` 전체가 끝날 때까지** 산다. 그래서 `else` 가 도는 동안에도 살아 있다.
- **2024** — **`else` 에 들어가기 전에 죽는다.** 조건이 실패한 시점에 이미 볼 일이 끝났기 때문이다.
- ★ `match` 는 **양쪽 에디션에서 같다** — 원래부터 「`match` 전체가 끝날 때 죽는」 규칙이고 2024 도 안 바꿨다.
  ★★ **그래서 `if let` 을 `match` 로 바꾸면 2024 의 이득이 사라진다.**

**그 차이가 코드의 성패를 가른다.**

```text
===== 소스: ex.rs =====
// ex.rs
// 임시값이 언제 죽는지가 코드의 성패를 가른다 — 마커는 전부 표준 오류로 찍는다
use std::cell::RefCell;

fn main() {
    let cell = RefCell::new(None::<u32>);
    eprintln!("시작 {:?}", cell);
    if let Some(v) = *cell.borrow() {
        eprintln!("then {}", v);
    } else {
        *cell.borrow_mut() = Some(7);       // 조건의 빌림이 아직 살아 있으면 여기서 터진다
        eprintln!("else 에서 채웠다");
    }
    eprintln!("끝 {:?}", cell);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
시작 RefCell { value: None }

thread 'main' (4007597) panicked at ex.rs:11:15:
RefCell already borrowed
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
(종료 코드 101)
```

```text
===== 소스: ex.rs =====
// ex.rs
// 임시값이 언제 죽는지가 코드의 성패를 가른다 — 마커는 전부 표준 오류로 찍는다
use std::cell::RefCell;

fn main() {
    let cell = RefCell::new(None::<u32>);
    eprintln!("시작 {:?}", cell);
    if let Some(v) = *cell.borrow() {
        eprintln!("then {}", v);
    } else {
        *cell.borrow_mut() = Some(7);       // 조건의 빌림이 아직 살아 있으면 여기서 터진다
        eprintln!("else 에서 채웠다");
    }
    eprintln!("끝 {:?}", cell);
}
===== rustc --edition 2024 ex.rs -o ex =====
===== ./ex =====
시작 RefCell { value: None }
else 에서 채웠다
끝 RefCell { value: Some(7) }
(종료 코드 0)
```

- 2021 은 **패닉**한다 — `RefCell already borrowed`, 종료 코드 **101**.
  조건의 `cell.borrow()` 가 아직 살아 있는데 `else` 에서 `borrow_mut()` 을 했기 때문이다.
- 2024 는 **그냥 돈다.** 빌림이 `else` 진입 전에 풀렸다.
- ★ 같은 모양이 `Mutex` 에서는 **교착**으로 나타난다(패닉이 아니라 **멈춘다**).
  그래서 `RefCell` 로 실험했다 — **결정적으로 터지고 종료 코드가 남는다.**
- ★ 마커를 전부 `eprintln!` 로 찍었다. `println!` 과 패닉을 섞으면 **파이프로 받을 때 순서가 뒤집힌다.**

### (6) 얕은 `match` 를 접는 기준

**언제 쓰나** — 네 도구 중 고를 때.

```text
===== 소스: ex.rs =====
// ex.rs
// 같은 일을 네 가지로 — 언제 무엇을 고르나
#[derive(Debug)]
enum Cfg { Port(u16), Off }

fn a_match(c: &Cfg) -> u16 {
    match c {
        Cfg::Port(p) => *p,
        _ => 0,
    }
}

fn b_if_let(c: &Cfg) -> u16 {
    if let Cfg::Port(p) = c { *p } else { 0 }
}

fn c_let_else(c: &Cfg) -> u16 {
    let Cfg::Port(p) = c else { return 0 };
    *p
}

fn d_helper(c: &Cfg) -> u16 {
    // std 가 이미 이름을 붙여 둔 자리 — 접을 게 없다
    matches!(c, Cfg::Port(_)) as u16 * a_match(c)
}

fn main() {
    for c in [Cfg::Port(8080), Cfg::Off] {
        println!("{:?} {} {} {} {}", c, a_match(&c), b_if_let(&c), c_let_else(&c), d_helper(&c));
    }
    // if let 은 「값이 있으면」 한 갈래만 볼 때, let else 는 「없으면 여기서 끝낼」 때
    let v: Option<u32> = None;
    println!("{}", v.map(|n| n + 1).unwrap_or(0));
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
Port(8080) 8080 8080 8080 8080
Off 0 0 0 0
0
(종료 코드 0)
```

읽는 법.

| 쓸 것 | 고르는 기준 |
|---|---|
| **`match`** | 갈래가 **둘 이상 의미 있고** 전부 다뤄야 할 때. ★ 내 열거형이면 기본값 |
| **`if let`** | 나머지에 할 일이 없을 때. `match` 에 `_ => {}` 가 보이면 그 자리 |
| **`let else`** | 실패면 **여기서 끝**이고 성공 경로가 길 때. 들여쓰기가 안 깊어진다 |
| **`matches!` · 조합 메서드** | **참/거짓만** 필요하거나 `Option`/`Result` 의 흔한 변환일 때 |

- ★★ **접으면 완전성 검사를 잃는다**((7)). 그 대가를 알고 접는다.
- `else if let` 사슬이 **셋을 넘으면** `match` 로 되돌린다 — 그때는 접은 이득보다 잃은 안전망이 크다.

### (7) ★ 접개에는 완전성 검사가 없다 — 18번의 실험을 여기서 다시

**언제 쓰나** — 「`if let` 사슬로 써도 되나」를 판단할 때.

**변형 셋을 `if let` 사슬로 처리한 판.**

```text
===== 소스: ex.rs =====
// ex.rs
// if let 에는 완전성 검사가 없다 — 전. 변형 셋을 if let 사슬로 처리한다
#[derive(Debug)]
enum Event { Click, Key, Scroll }

fn label(e: &Event) -> &'static str {
    if let Event::Click = e { "클릭" }
    else if let Event::Key = e { "키" }
    else { "스크롤" }
}

fn main() {
    for e in [Event::Click, Event::Key, Event::Scroll] {
        println!("{:?} {}", e, label(&e));
    }
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
Click 클릭
Key 키
Scroll 스크롤
(종료 코드 0)
```

**같은 파일에 `Drag` 를 더했다.**

```text
===== 소스: ex.rs =====
// ex.rs
// if let 에는 완전성 검사가 없다 — 후. Drag 를 더했는데 경고 한 줄도 안 난다
#[derive(Debug)]
enum Event { Click, Key, Scroll, Drag }

fn label(e: &Event) -> &'static str {
    if let Event::Click = e { "클릭" }
    else if let Event::Key = e { "키" }
    else { "스크롤" }
}

fn main() {
    for e in [Event::Click, Event::Key, Event::Scroll, Event::Drag] {
        println!("{:?} {}", e, label(&e));
    }
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
Click 클릭
Key 키
Scroll 스크롤
Drag 스크롤
(종료 코드 0)
```

읽는 법.

- ★★ **에러도 경고도 없다.** `Drag` 가 마지막 `else` 로 흘러가 **「스크롤」로 찍힌다.**
  18번 주제에서 `match` + `_` 가 만든 것과 **똑같은 침묵**이다.
- ★ 차이는 하나다 — `match` 에서 `_` 는 **내가 고른 것**이라 눈에 보이지만,
  `if let` 사슬의 마지막 `else` 는 **문법이 요구하는 것**이라 선택처럼 안 보인다.
- 그래서 **열거형을 전부 다루는 자리에는 `if let` 사슬을 안 쓴다.** `match` 가 맞다.

## 문법 — 형태와 규칙

**형태.**

```text
if let PAT = expr { … } else { … }              // 식. 두 갈래 타입이 같아야 값이 난다
while let PAT = expr { … }                      // 안 맞는 순간 끝
let PAT = expr else { /* 반드시 발산 */ };       // 1.65+. 바인딩이 바깥에 남는다

// let 체인 — 2024 에디션 + 1.88 이라야 한다
if let Some(a) = x && let Some(b) = y && a < b { … }
while let Some(item) = src.pop() && let Some(n) = item { … }
```

**규칙.**

- `if let`·`while let`·`let else` 는 **반박 가능한 패턴**을 받는다(19번 (7)).
- **`if let` 은 식**이다. `else` 가 없으면 본문이 `()` 라야 한다.
- **`let else` 의 `else` 는 `!` 여야** 한다. `()` 도 거부된다.
- **`let else` 의 바인딩은 바깥 스코프**에 산다. `if let` 은 블록 안에만.
- **`let` 체인은 `let` 개수만큼 에러**가 난다(2021 에서). `&&` 개수가 아니다.
- ★ **체인의 앞 고리 부작용은 뒤 고리가 실패해도 남는다**((4)).
- **완전성 검사가 없다.** 셋 다 그렇다((7)).

**금지 사례.**

```text
// ① let else 의 else 가 값을 낸다 — E0308 (expected `!`)
let Ok(n) = text.parse::<u32>() else { 0 };

// ② let else 의 else 가 아무것도 안 하고 끝난다 — E0308 (found `()`)
let Some(m) = Some(1) else { println!("없다"); };

// ③ 2021 에서 let 체인 — error: let chains are only allowed in Rust 2024 or later
if let Some(a) = x && let Some(b) = y { … }

// ④ 2021 에서 조건의 임시 빌림을 else 에서 다시 잡는다 — 런타임 패닉
if let Some(v) = *cell.borrow() { … } else { *cell.borrow_mut() = Some(7); }

// ⑤ 열거형 전부를 if let 사슬로 — 변형이 늘어도 아무 신호가 없다
if let Event::Click = e { … } else if let Event::Key = e { … } else { … }
```

## 어디서 틀리나

| 자리 | 증상 | 진짜 이유 |
|---|---|---|
| ★★★ **에디션을 안 밝히고 `let` 체인을 쓴다** | 「문법 오류」라고 결론 내린다 | `rustc` **기본은 2015** 다. `--edition 2024` 를 줘야 한다 |
| ★★ **1.88 미만에서 2024 를 쓴다** | 에디션은 맞는데 안 된다 | 체인은 **에디션과 버전 둘 다** 필요하다 |
| **`let else` 의 `else` 에 `println!` 만 적는다** | E0308 `found unit type ()` | `()` 도 「값을 냈다」다. 발산해야 한다 |
| ★★ **2021 에서 조건의 락·빌림을 `else` 에서 다시 잡는다** | 패닉 또는 **교착** | 임시값이 `if let` 전체가 끝날 때까지 산다((5)) |
| ★ **2024 이득을 보려고 `match` 로 바꾼다** | 여전히 터진다 | `match` 의 임시값 규칙은 **안 바뀌었다** |
| **열거형 전부를 `if let` 사슬로** | 변형을 늘려도 **아무 신호가 없다** | 접개에는 완전성 검사가 없다((7)) |
| **`else if let` 사슬이 길어진다** | 읽기 어렵고 안전망도 없다 | 셋을 넘으면 `match` 로 되돌린다 |
| ★ **체인의 앞 고리 부작용을 잊는다** | `pop()` 이 이미 일어났다 | 뒤 고리가 실패해도 앞은 실행된 뒤다((4)) |
| **`if let` 에 값을 기대하는데 `else` 가 없다** | 타입 오류 | `else` 없는 `if let` 은 `()` 다 |

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 |
|---|---|
| `if let`·`while let` 의 문법과 의미 | **언어 보장** — 1.0.0부터 |
| **`let else`(1.65)와 `else` 의 발산 요구** | **언어 보장** — 에디션과 무관 |
| **`let` 체인이 2024 에디션에서만 되는 것** | **언어 보장** — 에디션 제도 자체가 그것이다 |
| **`if let` 임시값 스코프가 2024 에서 바뀐 것** | **언어 보장** — Edition Guide 에 실린 변경이다 |
| `match` 의 임시값 스코프가 **안 바뀐 것** | **언어 보장** |
| `let` 체인 에러에 **번호가 없는 것** | ★ **이 판의 관찰** — 진단 형식은 보장이 아니다 |
| 에러가 **`let` 개수만큼** 나는 것 | ★ **이 판의 관찰** |
| `RefCell` 패닉 메시지 문구와 **줄·칸** | ★ **이 판의 관찰**(종료 코드 101 은 고정) |

★ **여기서 「보장」이 유난히 많은 이유** — 에디션은 **언어가 약속한 제도**다.
「이 판에서는 되더라」가 아니라 「2024 에디션에서 된다」가 정확한 진술이고, 그래서 **재현 가능하다.**

## 언제 쓰고 언제 안 쓰나

**`if let`** — 나머지 갈래에 할 일이 없을 때. **안 쓴다** — 열거형을 전부 다뤄야 할 때.

**`while let`** — 꺼낼 것이 없어질 때까지 꺼낼 때. **안 쓴다** — 전부 훑을 거면 `for` 가 낫다.

**`let else`** — 실패면 여기서 끝이고 성공 경로가 길 때. **안 쓴다** — 실패 쪽에도 할 일이 있으면 `match` 다.

**`let` 체인** — 2024 에디션 프로젝트에서 조건 여럿을 이을 때.
**안 쓴다** — 2021 이거나 1.88 미만이면 못 쓴다. 라이브러리라면 **MSRV** 를 먼저 본다.

## 핵심 문장

1. **`if let` 계열은 `match` 를 접는 도구**이고, 접는 대가는 **완전성 검사**다.
2. **`let else` 의 바인딩은 바깥에 남는다** — 그래서 성공 경로가 평평해진다.
3. **`let else` 의 `else` 는 `!` 여야 한다.** `()` 도 거부된다.
4. **`let` 체인은 2024 에디션 + 1.88** 이다. 2021 에서는 번호 없는 에러가 `let` 개수만큼 난다.
5. **2024 는 `if let` 조건의 임시값을 `else` 진입 전에 죽인다** — `match` 는 안 바뀌었다.
6. **에디션을 안 밝힌 「이 코드는 된다/안 된다」는 이 주제에서 무효다.**

## 관련 자료

- [**19번 주제**](../19-pattern-syntax-guards-bindings-and-match-ergonomics/) — 패턴 문법의 정본.
  여기는 **반박 가능한 패턴을 `match` 밖에서 쓰는 자리**만 맡는다.
- [**18번 주제**](../18-match-and-exhaustiveness/) — 완전성 검사의 정본. 여기는 **그것이 없는 쪽**이다.
- [**06번 주제**](../06-functions-and-never-type/) — `!`(never)의 정본. `let else` 가 요구하는 것이 그것이다.
- [**05번 주제**](../05-control-flow-loops-and-labels/) — `loop`·`while`·`for` 의 정본. `while let` 은 그 위에 얹힌다.
- [**04번 주제**](../04-expressions-and-semicolons/) — `if let` 이 식이라는 규칙의 뿌리.
- [`history/rust/02-에디션.md`](../../../../../../history/rust/02-에디션.md) — 에디션 제도의 **역사**. 여기는 **내 코드가 어느 에디션에서 어떻게 컴파일되나**.
- 목록의 **47번 주제** — 2021 대 2024 변경 **전수**. 여기는 이 주제에 걸린 **둘**만.
- [목록의 **21번 주제**](../21-option-and-combinators/)·**22번 주제** — `Option`/`Result` 의 조합 메서드. 접개 대신 쓰는 넷째 길이다.
- 목록의 **44번 주제** — `Drop` 시점. (5)의 임시값 실험이 그것을 창으로 쓴다.

## 용어 풀이

| 말 | 뜻 |
|---|---|
| **`if let`** | 패턴이 맞으면 블록을, 아니면 `else` 를 실행하는 **식** |
| **`while let`** | 패턴이 맞는 동안 도는 루프 |
| **`let else`** | 맞으면 바깥에 바인딩을 만들고 아니면 `else` 로 나가는 문(1.65+) |
| **발산(diverge)** | 제어가 안 돌아오는 것. 타입으로는 `!` |
| **`!`(never)** | 값이 하나도 없는 타입. 어떤 타입으로도 강제된다 |
| **`let` 체인** | `let` 과 조건을 `&&` 로 잇는 것. 2024 에디션 + 1.88 |
| **임시값(temporary)** | 이름이 없는 중간 값. **언제 죽는지**가 에디션으로 갈린다 |
| **임시값 스코프** | 임시값이 사는 범위. 2024 가 `if let` 에서 이것을 줄였다 |
| **에디션** | 3년 주기의 언어 방언. 크레이트마다 고르고 서로 섞인다 |
| **MSRV** | 그 크레이트가 지원하는 최소 rustc 판 |

## 더 들어가면

- **`let` 체인이 왜 에디션에 걸렸나** — `&&` 의 오른쪽에 `let` 이 오는 문법이 기존 코드와 모호해질 수 있었다.
  에디션은 그런 **문법 변경을 안전하게 넣는 장치**다. 제도 자체의 이야기는 `history/rust/02-에디션.md` 다.
- **`if let ... else if let ...` 은 체인이 아니다.** 체인은 `&&` 로 잇는 것이고, 이쪽은 그냥 중첩이다.
- **2024 의 임시값 변경은 `if let` 에만** 적용된다. `match`·`while let` 의 규칙은 그대로다 —
  전수는 목록의 **47번 주제**에서 확인한다.
- **`let else` 에 `if let` 처럼 `else if` 를 붙일 수 없다.** 발산해야 하므로 붙일 자리가 없다.
