# rust/syntax/20 — `if let`·`while let`·`let else`(1.65)·`let` 체인(2024 에디션·1.88) — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 또는 **`rustc --edition 2024 ex.rs -o ex`** 로 실제로 돌려 받은 것이다.\
> ★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
> ★★★ **에디션 대조는 표준 배너로 한 판씩 따로** 실었다. 두 블록의 유일한 차이는 배너의 `--edition` 숫자다.\
> 소스는 **한 글자도 같은 파일**이다 — 그 동일성도 기계로 대조했다.\
> ★★ **`--edition` 을 빼면 에디션 2015 다.** 이 주제에서 그것은 「안 돌려 본 것」과 같다.\
> 실험 파일 이름은 전부 **`ex.rs`** 로 고정했고 **진단의 줄 번호는 그 파일 기준**이다.\
> ★ 패닉 첫 줄의 `thread 'main' (…)` 괄호 안 숫자는 **실행마다 다른 OS 스레드 id** 다 — 대조할 칸이 아니다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 2021 은 에러 **넷**, 2024 는 통과

**출력** — 2021.

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

**같은 파일, 2024.**

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

**왜 그런가**

- 2021 에서 나오는 문구는 **`error: let chains are only allowed in Rust 2024 or later`** 다.
- ★★ **번호가 없다.** `error[E0xxx]` 가 아니고 끝에 `For more information …` 줄도 안 붙는다.
  타입 검사에서 걸린 것이 아니라 **파서가 에디션으로 막은 것**이기 때문이다.
  ★ 「번호 없는 진단」은 이 갈래에서 드물어 그 자체가 정보다.
- **에러는 넷**이고, 개수를 정하는 것은 **`let` 개수**다 — `if let` 줄에 둘(10:8, 10:27),
  `while let` 줄에 둘(17:11, 17:41). `&&` 는 셋인데 에러는 넷이다.
- 2024 에서는 통과하고 출력은 **`둘 다 있고 1 < 2`** · **`꺼냄 3`** · **`남은 [Some(1), Some(2)]`** 다.
- ★★★ **`while let` 체인의 함정** — `src` 는 `[Some(1), Some(2), None, Some(3)]` 이었다.
  첫 바퀴에 `pop()` 이 `Some(3)` 을 꺼내 `n = 3` 이 찍혔다.
  둘째 바퀴에 `pop()` 이 **`None` 을 꺼냈고**(벡터에서 빠졌다) 뒤 고리 `let Some(n) = item` 이 실패해 루프가 끝났다.
  **앞 고리의 부작용은 뒤 고리가 실패해도 남는다** — 그래서 남은 것이 `[Some(1), Some(2)]` 다.
- **버전도 필요하다** — `let` 체인은 **1.88.0부터**다. 1.85\~1.87 에서 2024 에디션을 써도 안 된다.
  2024 에디션 자체는 **1.85.0**에서 안정됐다.

### 2. ★★★ 갈리는 줄은 **B 한 자리**뿐이다

**출력** — 2021.

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

**같은 파일, 2024.**

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

**왜 그런가**

| 자리 | 2021 | 2024 | 갈리나 |
|---|---|---|---|
| A (참 갈래) | `then 1` → `drop 있음` | `then 1` → `drop 있음` | **아니오** |
| **B (거짓 갈래)** | **`else` → `drop 없음`** | **`drop 없음` → `else`** | ★★ **예** |
| C (`match`) | `then 1` → `drop 있음` | `then 1` → `drop 있음` | **아니오** |

- **2021** — 조건 자리의 임시값이 **`if let` 전체가 끝날 때까지** 산다. `else` 가 도는 동안에도 살아 있다.
- **2024** — 조건이 실패한 시점에 **볼 일이 끝났으므로 `else` 에 들어가기 전에 죽인다.**
- ★ **A 가 안 갈리는 이유** — 참 갈래에서는 꺼낸 값을 본문이 쓸 수 있어야 하므로
  임시값이 본문 끝까지 사는 것이 양쪽 다 같다.
- ★★ **C(`match`)는 2024 에서도 안 바뀌었다.** `match` 의 임시값은 원래부터 `match` 전체가 끝날 때 죽고
  2024 는 그것을 건드리지 않았다.
- **그래서 「2024 의 이득을 보려고 `if let` 을 `match` 로 바꾸면」 이득이 사라진다.**
  오히려 2021 의 동작으로 되돌아간다 — 방향이 거꾸로다.

### 3. ★★ 2021 은 패닉(종료 코드 101), 2024 는 그냥 돈다

**출력** — 2021.

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

**같은 파일, 2024.**

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

**왜 그런가**

- 2021 은 **`RefCell already borrowed`** 로 패닉하고 종료 코드가 **101** 이다.
  조건의 `cell.borrow()`(불변 빌림)가 아직 살아 있는데 `else` 에서 `borrow_mut()` 을 했기 때문이다.
  위치는 `ex.rs:11:15` — **`borrow_mut()` 호출 자리**다.
- 2024 는 조건의 빌림이 `else` 진입 전에 풀려 **그냥 돈다.** 마지막 줄이 `끝 RefCell { value: Some(7) }` 이다.
- ★ **`Mutex` 로 했으면 교착이었다** — 패닉이 아니라 **멈춘다.** 출력도 종료 코드도 안 남고
  타임아웃으로만 확인된다. `RefCell` 은 **결정적으로 터지고 종료 코드 101 을 남기므로**
  문서에 실을 근거로 훨씬 낫다. ★ 「재현 가능한 실패」를 고르는 것도 실험 설계다.
- ★ **마커를 `eprintln!` 으로 찍은 이유** — 패닉 메시지는 **표준 오류**로 나간다.
  `println!`(표준 출력)과 섞으면 **파이프·파일로 받을 때 순서가 뒤집힌다**(stdout 이 블록 버퍼가 되기 때문).
  전부 표준 오류로 찍으면 순서가 고정된다. 이 문서의 블록은 파이프로 받은 것이라 그 처방이 필요했다.
- ★ 패닉 첫 줄의 `thread 'main' (…)` 괄호 안 숫자는 **실행마다 다르다** — 위 블록의 값과 당신 머신의 값이 다를 것이다.
  **흔들리는 칸**이므로 대조하지 않는다. 메시지 본문·위치·`note:` 줄·종료 코드는 안 흔들린다.

### 4. ★★ 거부된다 — E0308 **두 개**. `` expected `!` ``

**출력**

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

**왜 그런가**

- **E0308** 이 두 번 나고 제목이 둘 다 `` `else` clause of `let...else` does not diverge `` 다.
- **기대하는 타입은 `!`** 다 — `` = note: expected type `!` ``.
- `found` 쪽은 각각 **`{integer}`**(정수 `0` 을 냈다)와 **`()`**(`println!` 로 끝났다)다.
  ★★ **둘째가 중요하다** — 아무 값도 안 냈는데도 걸린다. **`()` 도 「값을 냈다」** 로 친다.
  `let else` 가 요구하는 것은 「값을 안 내는 것」이 아니라 **「제어가 안 돌아오는 것」** 이다.
- `= help:` 는 둘이다 — ① `` try adding a diverging expression, such as `return` or `panic!(..)` ``
  ② `` ...or use `match` instead of `let...else` ``. 두 번째가 정직하다 —
  **실패 쪽에도 할 일이 있으면 `let else` 가 맞는 도구가 아니다.**
- ★ **이 요구는 에디션과 무관하다.** `let else` 자체가 **1.65.0**부터이고 전 에디션에서 같다.
- `!` 가 어떤 타입으로도 강제되는 성질의 정본은 [**06번 주제**](../06-functions-and-never-type/)다.

### 5. ★ 에러 0 · 경고 0 — `Drag` 가 「스크롤」로 찍힌다

**출력** — 변형 셋.

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

**`Drag` 를 더했다.**

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

**왜 그런가**

- ★★ **에러도 경고도 없다.** `Drag` 는 마지막 `else` 로 흘러가 **「스크롤」로 찍힌다.**
  18번 주제의 `match` + `_` 판이 만든 것과 **똑같은 침묵**이다.
- ★ **다른 점은 하나다.** `match` 에서 `_` 는 **내가 일부러 고른 것**이라 눈에 보이고
  코드 리뷰에서 지적할 수 있다. 그런데 `if let` 사슬의 마지막 `else` 는
  **문법이 요구하는 것**이라 「선택」처럼 보이지 않는다. **더 조용하다.**
- 게다가 여기서는 `Drag` 를 실제로 만들어 돌렸기 때문에 18번 판에 있던
  `variant Drag is never constructed` 경고조차 없다 — **신호가 하나도 안 남는다.**
- **그래서 열거형을 전부 다루는 자리에는 `match` 를 쓴다.** 접개는 「나머지에 할 일이 없을 때」의 도구다.

### 6. `let else` 가 다른 둘과 갈리는 점

**출력**

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

**왜 그런가**

- ★★ **꺼낸 값이 바깥 스코프에 남는다.** 위 코드의 `n` 과 `doubled` 는 `else` 블록 밖,
  즉 **함수 본문**에서 계속 쓰인다. `if let` 이면 블록 안에만 있다.
- **코드 모양에 하는 일** — 성공 경로가 **안쪽으로 안 밀린다.**
  `let else` 를 연달아 써도 들여쓰기가 그대로다. 실패 처리가 위로 모이고 성공 경로가 아래에 평평하게 남는다.
- **`else` 에 적을 수 있는 것 넷** — `return` · `break` · `continue` · `panic!`(또는 `todo!`·`unreachable!`·`process::exit`).
  공통점은 **제어가 안 돌아온다**는 것이다. 위 출력의 둘째 실험이 `continue` 를 쓴 판이다.
- **1.65.0부터**이고 **에디션과 무관**하다.
- **`else if` 를 붙일 수 없다.** `else` 가 반드시 발산해야 하므로 그 뒤에 이을 자리가 없다.

### 7. `if let` 이 식이라는 것

**출력**

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

**왜 그런가**

- `let n = if let … { … } else { … };` 가 되려면 **두 갈래 타입이 같아야** 한다.
  위의 ③이 그 예다 — 양쪽이 `u16` 이다.
- **`else` 가 없으면 본문이 `()`** 라야 한다. 값을 내면 「`else` 가 없는데 값을 낸다」로 막힌다.
- **`else if let` 으로 이을 수 있다**(④). ★ 다만 **셋을 넘으면 `match` 로 되돌린다** —
  그때는 접어서 얻은 것보다 잃은 완전성 검사가 크다(5번 답).

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

- **`while let` 은 조건이 처음부터 안 맞으면 한 번도 안 돈다**(④). 진입 검사가 먼저다.
- **`for` 와 갈리는 자리** — `for` 는 `IntoIterator` 를 받아 **끝까지** 돌고,
  `while let` 은 **아무 식이나** 받아 **패턴이 안 맞는 순간** 끝난다.
  ②가 그 관계를 보인다 — `while let Some(s) = it.next()` 가 곧 `for s in v.iter()` 다.
  ★ `for` 가 그것을 감추고 있다는 것이 [**05번 주제**](../05-control-flow-loops-and-labels/)의 내용이다.

### 8. 무엇을 고르나

**출력**

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

**왜 그런가**

| 쓸 것 | 고르는 기준 |
|---|---|
| **`match`** | 갈래가 둘 이상 의미 있고 전부 다뤄야 할 때. ★ **내 열거형이면 기본값** |
| **`if let`** | 나머지에 할 일이 없을 때 |
| **`let else`** | 실패면 여기서 끝이고 성공 경로가 길 때 |
| **`matches!`·조합 메서드** | 참/거짓만 필요하거나 `Option`/`Result` 의 흔한 변환일 때 |

- **접개를 쓸 때 잃는 것은 완전성 검사**다. 변형을 늘려도 **아무 신호가 없다**(5번 답).
- **`match` 에 `_ => {}` 가 보이면** 「이건 `if let` 자리 아닌가」를 생각한다.
  반대로 `_` 가 **의미 있는 일을 하고 있으면** `match` 가 맞다.
- **내 열거형을 전부 다루는 자리의 기본값은 `match`** 다. 그래야 변형이 늘 때 깨진다.

### 9. 에디션 대조

| 갈리는 것 | 2021 | 2024 |
|---|---|---|
| **`let` 체인**(`if let A = a && let B = b`) | ★ **에러** — `let chains are only allowed in Rust 2024 or later` (번호 없음) | ★ **통과** |
| **`if let` 조건의 임시값 스코프** | `else` **가 돈 뒤** 죽는다 | `else` **에 들어가기 전** 죽는다 |
| `match` 의 임시값 스코프 | `match` 전체가 끝날 때 | **같다**(안 바뀌었다) |
| `let else` | 된다 | 된다 — **에디션 무관**(1.65+) |
| `if let`·`while let` 자체 | 된다 | 된다 |

- **`let else` 는 에디션으로 안 갈린다.** 버전(1.65)만 맞으면 된다.
- **`--edition` 을 안 주면 에디션 2015** 다. 이 주제에서 그것은 사실상 「안 돌려 본 것」이다.
- **2024 에디션은 1.85.0(2025-02-20)에서 안정**됐고, **`let` 체인은 1.88.0부터**다.
  ★ 그래서 **1.85\~1.87 에서는 2024 에디션인데도 체인이 안 된다** — 둘을 같은 것으로 외우면 틀린다.
- **에디션 변경 전수**는 목록의 **47번 주제**이고,
  **에디션 제도의 역사**는 [`history/rust/02-에디션.md`](../../../../../../history/rust/02-에디션.md)가 정본이다.

### 10. 다른 주제와 잇기

- **`!`(never)의 정본**은 [**06번 주제**](../06-functions-and-never-type/)다. `let else` 의 `else` 가 요구하는 것이 그 타입이다.
- **완전성 검사의 정본**은 [**18번 주제**](../18-match-and-exhaustiveness/)다.
  이 주제는 **그 검사가 없는 쪽**이라 18번과 짝을 이룬다 — 5번 답이 그 실험을 여기서 다시 돌린 것이다.
- **반박 가능/불가 패턴의 구분**은 [**19번 주제**](../19-pattern-syntax-guards-bindings-and-match-ergonomics/) (7)에서 나왔다.
  `let`·함수 인자·`for`·클로저 인자는 불가만 받고, `if let`·`while let`·`let else` 가 **가능을 받는 자리**다.
- **루프 문법의 정본**은 [**05번 주제**](../05-control-flow-loops-and-labels/)다. `while let` 은 그 위에 얹힌다.
- (5)의 임시값 실험이 창으로 쓴 것은 **`Drop` 이 찍는 순서**이고, `Drop` 시점의 정본은
  [**09번 주제**](../09-copy-clone-and-drop/)와 목록의 **44번 주제**다.
- **넷째 길(조합 메서드)** 은 목록의 **21번 주제**(`Option`)와 **22번 주제**(`Result`·`?`)다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh` 가 `rustc --edition <ed> ex.rs -o ex` 로 컴파일하고 `./ex` 실행 | 배치 내내 + **제출 전 전수 재실행 1회** | `diff -rq` — 패닉 블록의 스레드 id만 달라짐 |
| ★★★ **`let` 체인 에디션 대조** | `b20-05-e2021`(에러 4) · `b20-05-e2024`(통과) — **같은 소스** | 2 | 배너의 `--edition` 숫자만 다르다 |
| ★★★ **임시값 스코프 대조** | `b20-06-e2021` · `b20-06-e2024` — **같은 소스** | 2 | **B 한 자리만** 갈림 |
| ★★ **그 차이의 결과** | `b20-07-e2021`(패닉 101) · `b20-07-e2024`(통과) | 2 | `RefCell already borrowed` |
| `let else` 발산 요구 | `b20-04`(E0308 ×2) | 1 | `expected type !` · `found ()` 까지 |
| `let else` 동작 | `b20-03` | 1 | 바인딩이 바깥에 남는다 |
| `if let` · `while let` | `b20-01` · `b20-02` | 2 | 식으로 쓰기·진입 검사 |
| 접기 기준 | `b20-08` | 1 | 네 길이 같은 값을 낸다 |
| 완전성 없음 | `b20-09a`(셋) · `b20-09b`(넷) | 2 | **에러 0 · 경고 0** |
| 두 에디션 블록의 **소스 동일성** | `diff` 로 `-q` 조각 대조 | 1 | 한 글자도 같음 |

**구현 의존 항목**(버전이 오르면 **다시 찍어야 하는** 것).

| 항목 | 왜 |
|---|---|
| `let` 체인 에러에 **번호가 없는 것** | 진단 형식은 보장이 아니다 |
| 에러가 **`let` 개수만큼** 나는 것 | 진단 구현에 달렸다 |
| `RefCell` 패닉 메시지 문구와 **줄·칸** | 표준 라이브러리 문구는 바뀔 수 있다(종료 코드 101 은 고정) |
| 패닉 첫 줄의 **스레드 id** | ★ **실행마다 다르다** — 대조 대상이 아니다 |
| **1.88 미만 + 2024 에디션** 조합 | 이 머신에는 1.92 뿐이라 **못 던져 봤다** — 아래 참조 |

★ **못 던져 본 것 하나** — 「1.85\~1.87 에서 2024 에디션이면 `let` 체인이 안 된다」는
**이 머신에 그 판이 없어 실행으로 확인하지 못했다.** 릴리스 노트의 안정화 버전 표기에 기댄 진술이다.
★ 「안 돌려 봄」이 아니라 **「이 환경에서 못 돌린다」** 이므로 그렇게 적는다 —
1.92 하나로는 버전 경계를 만들 수 없다.

★ **다시 찍는 법** — `capture.sh` 를 그대로 돌리고 `diff -rq` 한다.
달라지는 파일은 **패닉이 있는 `b20-07-e2021` 하나**이고, 그 차이는 **스레드 id 한 칸**이라야 한다.
