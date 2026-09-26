# rust/syntax/44 — `Drop` · `mem::drop` · `mem::replace`/`take` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서
> **`rustc --edition 2021`** 로(패닉 전략 비교는 `-C panic=abort`), C++ 대비는 **`g++ 13.3.0 -std=c++20`** 으로 실제로 돌려 받은 것이다.\
> ★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
> ★★ 블록 첫 줄 `===== 소스: <파일> =====` 아래가 **돌린 소스 전문**이고, **진단의 줄 번호는 그 파일 기준**이다.\
> ★ 패닉 첫 줄의 `thread 'main' (NNN)` 은 **실행마다 바뀌는 칸**이다(서머리 머리말의 표).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ `5 / 12` — `let _ = 값`·식 문장·`drop`·대입·`.0.len()` 만 바로 버려진다

**출력**

```text
===== 소스: r44_grid.sh =====
# 문장 하나마다 프로그램을 만들어 D("a") 의 drop 이 어디서 찍히는지 본다 — 다음 문장 전 / 블록 끝 / 끝내 안 찍힘
T=$'\t'
cases=(
  'let _ = D("a");'
  'let _x = D("a");'
  'D("a");'
  'let x = D("a"); let _ = x;'
  'let x = D("a"); let _y = x;'
  'let x = D("a"); drop(x);'
  'let x = D("a"); let x = D("b");'
  'let mut x = D("a"); x = D("b");'
  'let n = D("a").0.len();'
  'let r = &D("a");'
  'let v = vec![D("a")]; let _ = v.len();'
  'std::mem::forget(D("a"));'
)
printf 'statement\twhere "drop a" appears\n'
early=0; total=0
for s in "${cases[@]}"; do
  printf 'struct D(&'"'"'static str);\nimpl Drop for D { fn drop(&mut self) { println!("drop {}", self.0); } }\nfn main() {\n    {\n        %s\n        println!("<next statement>");\n        println!("<block end>");\n    }\n    println!("<after block>");\n}\n' "$s" > g.rs
  rustc --edition 2021 -A unused -o g g.rs 2>err.txt || { echo "compile failed: $s"; cat err.txt; exit 1; }
  out=$(./g) || exit 1
  pos=$(printf '%s\n' "$out" | awk '/^drop a$/{print prev; found=1; exit} {prev=$0} END{if(!found) print "none"}')
  case $pos in
    '') where='before <next statement>'; early=$((early+1)) ;;
    '<next statement>') where='before <next statement>'; early=$((early+1)) ;;
    '<block end>') where='at block end' ;;
    none) where='never' ;;
    *) where="after: $pos" ;;
  esac
  [ "$pos" = 'drop b' ] && { where='at block end (after drop b)'; }
  row="$s${T}$where"
  cols=$(printf '%s' "$row" | awk -F'\t' '{print NF}')
  [ "$cols" = 2 ] || { echo "column count $cols != 2"; exit 1; }
  printf '%s\n' "$row"
  total=$((total+1))
done
echo "cells dropped before the next statement: $early / $total"
===== bash r44_grid.sh =====
statement	where "drop a" appears
let _ = D("a");	before <next statement>
let _x = D("a");	at block end
D("a");	before <next statement>
let x = D("a"); let _ = x;	at block end
let x = D("a"); let _y = x;	at block end
let x = D("a"); drop(x);	before <next statement>
let x = D("a"); let x = D("b");	at block end (after drop b)
let mut x = D("a"); x = D("b");	before <next statement>
let n = D("a").0.len();	before <next statement>
let r = &D("a");	at block end
let v = vec![D("a")]; let _ = v.len();	at block end
std::mem::forget(D("a"));	never
cells dropped before the next statement: 5 / 12
(exit 0)
```

**왜 그런가**

- ★★★ **바로(다음 문장 전)** — `let _ = D("a")`(묶지 않은 값 → 문장 끝의 임시값) · `D("a");` · `drop(x)` · `x = D("b")`(대입이 옛 값을 버림) · `D("a").0.len()`(연장 없는 임시값).
- ★★★ **블록 끝** — `let _x`(보통 이름) · **`let _ = x`(자리 식이라 이동 안 함)** · `let _y = x`(이동했지만 `_y` 도 같은 블록) · `let r = &D("a")`(수명 연장) · `vec![…]`(`v` 가 쥠) · **섀도잉**(가려진 `a` 는 `drop b` **뒤에**).
- ★ **`forget` — 끝내 안 찍힘.**

### 2. ★★★ 앞은 `still usable: x` → `drop x` · 뒤는 E0382, 10행 `let _y = x;` 를 짚는다

**출력**

```text
===== 소스: r44_let_underscore.rs =====
struct D(&'static str);
impl Drop for D {
    fn drop(&mut self) {
        println!("drop {}", self.0);
    }
}

fn main() {
    let x = D("x");
    let _ = x;
    println!("still usable: {}", x.0);
}
===== rustc --edition 2021 r44_let_underscore.rs =====
(exit 0)
===== ./r44_let_underscore =====
still usable: x
drop x
(exit 0)
```

```text
===== 소스: r44_let_named.rs =====
struct D(&'static str);
impl Drop for D {
    fn drop(&mut self) {
        println!("drop {}", self.0);
    }
}

fn main() {
    let x = D("x");
    let _y = x;
    println!("still usable: {}", x.0);
}
===== rustc --edition 2021 r44_let_named.rs =====
error[E0382]: borrow of moved value: `x`
  --> r44_let_named.rs:11:34
   |
 9 |     let x = D("x");
   |         - move occurs because `x` has type `D`, which does not implement the `Copy` trait
10 |     let _y = x;
   |              - value moved here
11 |     println!("still usable: {}", x.0);
   |                                  ^^^ value borrowed here after move
   |
note: if `D` implemented `Clone`, you could clone the value
  --> r44_let_named.rs:1:1
   |
 1 | struct D(&'static str);
   | ^^^^^^^^ consider implementing `Clone` for this type
...
10 |     let _y = x;
   |              - you could clone this value
   = note: this error originates in the macro `$crate::format_args_nl` which comes from the expansion of the macro `println` (in Nightly builds, run with -Z macro-backtrace for more info)

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0382`.
(exit 1)
```

**왜 그런가**

- ★★★ Reference — 와일드카드 패턴은 「**복사하지도, 이동하지도, 빌리지도 않는다**」. `x` 는 그대로 `x` 의 것이다.
- ★★★ **`_y` 는 보통 이름**이라 이동이 일어나 11행에서 **E0382**(「value moved here」가 10행).

### 3. ★★★ E0509 — `help:` 는 빌리기·복제 · `take` 판은 `drop job name="placeholder" token=None`

**출력**

```text
===== 소스: r44_e0509.rs =====
struct Job {
    name: String,
}

impl Drop for Job {
    fn drop(&mut self) {
        println!("drop job {:?}", self.name);
    }
}

fn main() {
    let j = Job { name: String::from("build") };
    let n = j.name;
    println!("{n}");
}
===== rustc --edition 2021 r44_e0509.rs =====
error[E0509]: cannot move out of type `Job`, which implements the `Drop` trait
  --> r44_e0509.rs:13:13
   |
13 |     let n = j.name;
   |             ^^^^^^
   |             |
   |             cannot move out of here
   |             move occurs because `j.name` has type `String`, which does not implement the `Copy` trait
   |
help: consider borrowing here
   |
13 |     let n = &j.name;
   |             +
help: consider cloning the value if the performance cost is acceptable
   |
13 |     let n = j.name.clone();
   |                   ++++++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0509`.
(exit 1)
```

```text
===== 소스: r44_e0509_take.rs =====
use std::mem;

struct Job {
    name: String,
    token: Option<Box<u32>>,
}

impl Drop for Job {
    fn drop(&mut self) {
        println!("drop job name={:?} token={:?}", self.name, self.token);
    }
}

fn main() {
    let mut j = Job { name: String::from("build"), token: Some(Box::new(7)) };
    let n = mem::take(&mut j.name);
    let t = j.token.take();
    let old = mem::replace(&mut j.name, String::from("placeholder"));
    println!("took name={n:?} token={t:?} replaced={old:?}");
}
===== rustc --edition 2021 r44_e0509_take.rs =====
(exit 0)
===== ./r44_e0509_take =====
took name="build" token=Some(7) replaced=""
drop job name="placeholder" token=None
(exit 0)
```

**왜 그런가**

- ★★ **E0509** — `Drop` 을 단 타입은 소멸자가 필드를 읽으므로 **부분 이동 금지**. `help:` 는 **`&j.name`**·**`j.name.clone()`** — 어느 쪽도 빼 가기가 아니다.
- ★★★ 뒤 소스 — `take` 가 `""` 을, `Option::take` 가 `None` 을 남기고, `replace` 가 `""` 을 `"placeholder"` 로 바꿨다. **소멸자는 한 번 돌고 남긴 값을 본다** — 구멍이 없으니 E0509 가 풀린다.

### 4. ★★ E0507 → (`help:` 대로 빌리면) E0308 두 개 → `mem::replace` 로 푼다

**출력**

```text
===== 소스: r44_state.rs =====
enum State {
    Draft(String),
    Sent(String),
}

struct Mail {
    state: State,
}

impl Mail {
    fn send(&mut self) {
        self.state = match self.state {
            State::Draft(body) => State::Sent(body),
            State::Sent(body) => State::Sent(body),
        };
    }
}

fn main() {
    let mut m = Mail { state: State::Draft(String::from("hi")) };
    m.send();
}
===== rustc --edition 2021 r44_state.rs =====
error[E0507]: cannot move out of `self.state` as enum variant `Draft` which is behind a mutable reference
  --> r44_state.rs:12:28
   |
12 |         self.state = match self.state {
   |                            ^^^^^^^^^^
13 |             State::Draft(body) => State::Sent(body),
   |                          ---- data moved here
14 |             State::Sent(body) => State::Sent(body),
   |                         ---- ...and here
   |
   = note: move occurs because these variables have types that don't implement the `Copy` trait
help: consider borrowing here
   |
12 |         self.state = match &self.state {
   |                            +

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0507`.
(exit 1)
```

```text
===== 소스: r44_state_help.rs =====
enum State {
    Draft(String),
    Sent(String),
}

struct Mail {
    state: State,
}

impl Mail {
    fn send(&mut self) {
        self.state = match &self.state {
            State::Draft(body) => State::Sent(body),
            State::Sent(body) => State::Sent(body),
        };
    }
}

fn main() {
    let mut m = Mail { state: State::Draft(String::from("hi")) };
    m.send();
}
===== rustc --edition 2021 r44_state_help.rs =====
error[E0308]: mismatched types
  --> r44_state_help.rs:13:47
   |
13 |             State::Draft(body) => State::Sent(body),
   |                                   ----------- ^^^^ expected `String`, found `&String`
   |                                   |
   |                                   arguments to this enum variant are incorrect
   |
note: tuple variant defined here
  --> r44_state_help.rs:3:5
   |
 3 |     Sent(String),
   |     ^^^^
help: try using a conversion method
   |
13 |             State::Draft(body) => State::Sent(body.to_string()),
   |                                                   ++++++++++++

error[E0308]: mismatched types
  --> r44_state_help.rs:14:46
   |
14 |             State::Sent(body) => State::Sent(body),
   |                                  ----------- ^^^^ expected `String`, found `&String`
   |                                  |
   |                                  arguments to this enum variant are incorrect
   |
note: tuple variant defined here
  --> r44_state_help.rs:3:5
   |
 3 |     Sent(String),
   |     ^^^^
help: try using a conversion method
   |
14 |             State::Sent(body) => State::Sent(body.to_string()),
   |                                                  ++++++++++++

error: aborting due to 2 previous errors

For more information about this error, try `rustc --explain E0308`.
(exit 1)
```

```text
===== 소스: r44_state_fix.rs =====
use std::mem;

enum State {
    Draft(String),
    Sent(String),
    Empty,
}

struct Mail {
    state: State,
}

impl Mail {
    fn send(&mut self) {
        self.state = match mem::replace(&mut self.state, State::Empty) {
            State::Draft(body) => State::Sent(body),
            other => other,
        };
    }
}

fn main() {
    let mut m = Mail { state: State::Draft(String::from("hi")) };
    m.send();
    match &m.state {
        State::Sent(b) => println!("sent {b}"),
        State::Draft(_) => println!("draft"),
        State::Empty => println!("empty"),
    }
}
===== rustc --edition 2021 r44_state_fix.rs =====
(exit 0)
===== ./r44_state_fix =====
sent hi
(exit 0)
```

**왜 그런가**

- ★★ **E0507** — `&mut self` 뒤의 `self.state` 는 빌린 것이라 통째로 옮길 수 없다. `help:` 「consider borrowing here」(`match &self.state`).
- ★★★ 따르면 **E0308 × 2 — expected `String`, found `&String`**, `help:` 는 **`body.to_string()`**(복제). 빌리면 옮길 수 없다.
- ★★ **`mem::replace(&mut self.state, State::Empty)`** 가 옛 상태를 소유권째 꺼낸다 → `sent hi`.

### 5. ★★ 되감기 — 패닉 뒤 `drop inner` → `drop main` · `101` / abort 면 `drop` 0 줄 · `134`

**출력**

```text
===== 소스: r44_panic.rs =====
struct D(&'static str);
impl Drop for D {
    fn drop(&mut self) {
        eprintln!("drop {}", self.0);
    }
}

fn inner() {
    let _i = D("inner");
    panic!("stop");
}

fn main() {
    let _m = D("main");
    eprintln!("[1] calling inner");
    inner();
    eprintln!("[2] after inner");
}
===== rustc --edition 2021 r44_panic.rs =====
(exit 0)
===== ./r44_panic =====
[1] calling inner

thread 'main' (1257992) panicked at r44_panic.rs:10:5:
stop
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
drop inner
drop main
(exit 101)
```

```text
===== 소스: r44_panic.rs =====
struct D(&'static str);
impl Drop for D {
    fn drop(&mut self) {
        eprintln!("drop {}", self.0);
    }
}

fn inner() {
    let _i = D("inner");
    panic!("stop");
}

fn main() {
    let _m = D("main");
    eprintln!("[1] calling inner");
    inner();
    eprintln!("[2] after inner");
}
===== rustc --edition 2021 -C panic=abort -o r44_panic_abort r44_panic.rs =====
(exit 0)
===== ./r44_panic_abort =====
[1] calling inner

thread 'main' (1258068) panicked at r44_panic.rs:10:5:
stop
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
(exit 134)
```

**왜 그런가**

- ★★★ **기본(`panic=unwind`)** — 되감기가 안쪽 프레임부터 값을 버린다. `[2]` 는 안 찍힌다. **`main` 을 빠져나가는 패닉이어도** 되감는다.
- ★★★ **`-C panic=abort`** — Reference: 패닉 처리기가 abort 면 **되감기 없이** 끝나 **소멸자가 실행되지 않는다.** 종료 `134`(`SIGABRT`).

### 6. ★★ 락은 `let_underscore_lock` 이 막는다(번호 없음) · `RefCell` 은 통과하고 `true`

**출력**

```text
===== 소스: r44_lock.rs =====
use std::sync::Mutex;
fn main() {
    let m = Mutex::new(0);
    let _ = m.lock().unwrap();
    println!("{}", m.try_lock().is_ok());
}
===== rustc --edition 2021 r44_lock.rs =====
error: non-binding let on a synchronization lock
 --> r44_lock.rs:4:9
  |
4 |     let _ = m.lock().unwrap();
  |         ^ this lock is not assigned to a binding and is immediately dropped
  |
  = note: `#[deny(let_underscore_lock)]` (part of `#[deny(let_underscore)]`) on by default
help: consider binding to an unused variable to avoid immediately dropping the value
  |
4 |     let _unused = m.lock().unwrap();
  |          ++++++
help: consider immediately dropping the value
  |
4 -     let _ = m.lock().unwrap();
4 +     drop(m.lock().unwrap());
  |

error: aborting due to 1 previous error

(exit 1)
```

```text
===== 소스: r44_refcell_guard.rs =====
use std::cell::RefCell;
fn main() {
    let c = RefCell::new(0);
    let _ = c.borrow_mut();
    println!("{}", c.try_borrow_mut().is_ok());
}
===== rustc --edition 2021 r44_refcell_guard.rs =====
(exit 0)
===== ./r44_refcell_guard =====
true
(exit 0)
```

**왜 그런가**

- ★★★ **`Mutex` 가드** — **`#[deny(let_underscore_lock)]` 가 기본으로 켜진 린트**라 에러다(오류 번호가 없다 — 린트 이름이 곧 식별자다). 「this lock is not assigned to a binding and is immediately dropped」 · `help:` `let _unused` / `drop(…)`.
- ★★★ **`RefCell` 가드** — 그 린트는 **동기화 락**만 본다. 통과하고, 가드가 **그 문장에서 반납**되어 `try_borrow_mut` 가 **`true`**. **같은 실수가 조용히 지나간다.**

### 7. ★★ 안 찍힌다(구현 정의 — g++ 13) · 잡으면 전부 찍힌다

**출력**

```text
===== 소스: r44_uncaught.cpp =====
#include <cstdio>
#include <stdexcept>

struct D {
    const char* tag;
    explicit D(const char* t) : tag(t) {}
    ~D() { std::fprintf(stderr, "~D %s\n", tag); }
};

void inner() {
    D i{"inner"};
    throw std::runtime_error("stop");
}

int main() {
    D m{"main"};
    std::fprintf(stderr, "[1] calling inner\n");
    inner();
    std::fprintf(stderr, "[2] after inner\n");
}
===== g++ -std=c++20 -Wall -Wextra -pedantic r44_uncaught.cpp -o r44_uncaught =====
(exit 0)
===== ./r44_uncaught =====
[1] calling inner
terminate called after throwing an instance of 'std::runtime_error'
  what():  stop
(exit 134)
```

```text
===== 소스: r44_caught.cpp =====
#include <cstdio>
#include <stdexcept>

struct D {
    const char* tag;
    explicit D(const char* t) : tag(t) {}
    ~D() { std::fprintf(stderr, "~D %s\n", tag); }
};

void inner() {
    D i{"inner"};
    throw std::runtime_error("stop");
}

int main() {
    D m{"main"};
    std::fprintf(stderr, "[1] calling inner\n");
    try {
        inner();
    } catch (const std::exception& e) {
        std::fprintf(stderr, "[catch] %s\n", e.what());
    }
    std::fprintf(stderr, "[2] after inner\n");
}
===== g++ -std=c++20 -Wall -Wextra -pedantic r44_caught.cpp -o r44_caught =====
(exit 0)
===== ./r44_caught =====
[1] calling inner
~D inner
[catch] stop
[2] after inner
~D main
(exit 0)
```

- ★★★ **잡히지 않으면 `~D` 가 한 줄도 없다** — `terminate called after throwing an instance of 'std::runtime_error'` · `134`. cppreference: 「잡히지 않은 예외에서 **되감기가 일어나는지는 구현 정의**」 — 이 판은 안 되감았다.
- ★★ **잡으면** `~D inner` → `[catch] stop` → `[2]` → `~D main`.
- ★★★ **Rust 와의 차이** — Rust 기본 전략은 **잡는 코드가 없어도 되감는다**(5번). C++ 은 **`catch` 가 없으면 구현에 맡긴다.**

### 8. ★★★ 소멸자 실행은 안전성 보장에 들어 있지 않다 — 「불린다」는 규칙, 「반드시」는 보장 아님

- ★★★ std `mem::forget` §Safety — 「`forget` 이 `unsafe` 가 아닌 것은 **Rust 의 안전성 보장에 소멸자가 반드시 실행된다는 보장이 없기** 때문이다. **`Rc` 로 참조 순환**을 만들거나 **`process::exit`** 로 소멸자 없이 끝낼 수 있다」(서머리 (6)의 `r44_forget` — `drop a` 가 끝내 없다).
- ★★ **「`drop` 이 불린다」** — 정상 경로(스코프 끝·대입·`panic=unwind` 되감기)의 **언어 규칙**(Reference — Destructors).
- ★★★ **「반드시 불린다」** — **누구도 보장하지 않는다**(`forget` · [41번](../41-rc-arc-shared-ownership-and-weak-cycles/)의 순환 · `panic=abort` · `process::exit`). 그래서 **안전성을 `Drop` 에 걸면 안 된다**(std).

### 9. ★★ 섀도잉은 블록 끝(`b` 뒤) · 대입은 그 자리 — 이름이 둘인가 하나인가

- ★★ **섀도잉** — `let x` 가 **두 번째 변수**를 만든다. 첫 `x` 는 **가려졌을 뿐 살아 있고**, 자기 블록 끝에서 선언 역순으로 버려진다 → `drop b` 뒤에 `drop a`.
- ★★ **대입** — 변수는 **하나**이고 자리의 값만 바뀐다. 새 값이 들어오기 전에 **옛 값이 그 자리에서** 버려진다 → 다음 문장 전.

### 10. ★★ Rust 필드는 선언 순 · C++ 멤버는 선언 역순 · `Drop` 본체가 먼저 — 그래서 필드를 못 뺀다

- ★★ [09번](../09-copy-clone-and-drop/) (6) — Rust 구조체 필드는 **선언 순**(`필드-a` → `필드-b`). C++ [14번](../../../cpp/syntax/14-destructors-and-deterministic-destruction/2-summary.md) (1) — C++ 멤버는 **선언 역순**(생성의 역순). **방향이 반대다.** 지역 변수는 둘 다 역순이다.
- ★★★ `Drop` 을 단 구조체는 **본체(`drop(&mut self)`) 먼저, 필드 나중**(09번 (6)). 본체가 필드를 **읽을 수 있어야** 하므로 필드를 미리 빼 가면 안 된다 — 그것이 **E0509** 다(3번).

### 11. ★ `Default` · 준 값 · `None` — `State` 에 `Default` 가 없어서 `replace`, 대가는 `Empty` 변형

| 도구 | 남기는 것 | 요구 |
|---|---|---|
| `mem::take` | `Default::default()` | `T: Default` |
| `mem::replace` | 내가 준 값 | 없음 |
| `Option::take` | `None` | 없음 |

- ★★ 4번의 `State` 는 `Default` 가 없어 `take` 를 못 쓰고 **`replace` 에 `State::Empty` 를 준다.**
- ★ **대가** — 「비어 있는 상태」 변형이 타입에 생기고, `match` 가 그것을 다뤄야 한다(서머리 (4)).

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서·서머리의 **모든 블록** | `capture.sh` — 블록마다 명령을 배너에 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` 기본 규칙 넷(스레드 id 가 걸린다) · **고칠 것 0** |
| ★★★ **해제 격자** | `r44_grid.sh` — 열두 소스를 만들어 실행(탭 구분 · 칸 수 검사) | 12 · 12 | **`5 / 12`** |
| `_` 판별 | `r44_let_underscore` · `r44_let_named` · `r44_lock` · `r44_refcell_guard` | 4 | 통과 · **E0382** · **`let_underscore_lock`** · `true` |
| E0509 → `take` | `r44_e0509` · `r44_e0509_take` | 2 | **E0509** · `placeholder`/`None` |
| E0507 → `replace` | `r44_state` · `r44_state_help` · `r44_state_fix` | 3 | **E0507** · **E0308 × 2** · `sent hi` |
| 패닉 전략 · C++ | `r44_panic` · `r44_panic_abort` · `r44_uncaught` · `r44_caught` | 4 | `101` · `134` · `134`(소멸자 0 줄) · `0` |
| `forget` | `r44_forget` | 1 | `drop a` 없음 |
| ★ **이미 잰 것 — 다시 안 돌림** | 지역·필드·튜플·`Vec`·인자 순서 · E0184 · E0040 | — | 09번 (3)·(6)·(7) |
| **안 던진 것** — `ManuallyDrop` · 이중 패닉 · clang 의 잡히지 않은 예외 · 메모리 | — | 0 | ★ 「안 던졌다」로 표시했다 |

**구현 의존 항목**(버전·환경이 바뀌면 **다시 찍어야 하는** 것).

| 항목 | 왜 |
|---|---|
| C++ 잡히지 않은 예외의 되감기 여부 | ★ 표준이 **구현 정의** — 컴파일러·표준 라이브러리마다 다를 수 있다 |
| `let_underscore_lock` 이 기본 거부인 것 | ★ rustc 린트 설정 — 판에 매인다 |
| 종료 코드 `101`·`134` | ★ std 런타임 관행 · OS 시그널 |

★ **다시 찍는 법** — `capture.sh <새 디렉토리>` 를 그대로 돌리고 `normalize-shaky.py <원본> <새 디렉토리>` 로 견준다.
