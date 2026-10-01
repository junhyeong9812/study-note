# rust/syntax/55 — async 실전: 런타임 선택 · `Send` 경계 · `Pin` 맛보기 — 정리 (힌트)

```text
===== rustc --version =====
rustc 1.92.0 (ded5c06cf 2025-12-08)
(exit 0)
===== cargo --version =====
cargo 1.92.0 (344c4567c 2025-10-21)
(exit 0)
===== rustup toolchain list =====
stable-x86_64-unknown-linux-gnu (active, default)
(exit 0)
===== gcc --version | head -1 =====
gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
(exit 0)
===== ls "$HOME"/.cargo/registry/cache/*/ | grep -E "^tokio-(1|macros)" =====
tokio-1.52.3.crate
tokio-1.53.1.crate
tokio-macros-2.7.0.crate
tokio-macros-2.7.1.crate
tokio-macros-2.7.2.crate
(exit 0)
```

- ★ **nightly 가 없다**(`stable` 하나) · **tokio 는 캐시에 두 판**(1.52.3 · 1.53.1)이 있다 — `Cargo.toml` 에서 `=1.52.3` 으로 못 박았다.

★★★ **본체 창 — ① 컴파일러의 `Send` 진단 사슬이다.** 「await 를 가로지르는 락이 왜 문제인가」를 **교착을 재현하지 않고** 진단의 `note:` 사슬(「has type … which is not `Send`」 → 「await occurs here, with … maybe used later」)로 본다.

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| 안 흔들린다 | ★★★ **`Send` 진단의 사슬** — 어느 변수 · 어느 await · 어느 경계 | 같은 rustc 판에서 고정이다 |
| 안 흔들린다 | E0728 · E0752 · E0277 번호 · `파일:줄:칸` · 종료 코드 | 〃 |
| 안 흔들린다 | tokio 판의 **스레드 이름 집합**(`{"main"}` · `{"tokio-rt-worker"}`) | 여러 작업의 이름을 **집합으로** 모아 순서를 지웠다(규칙 11) |
| ★ **구현이 정한다** | ★★ **「빌린 뒤 `drop` 해도 `Send` 가 안 된다」** | rustc 의 await 너머 생존 분석 — 54번 (4)의 크기와 같은 분석이다. 판이 오르면 **다시 찍을 칸** |
| ★ **구현이 정한다** | tokio 워커 스레드 이름 `tokio-rt-worker` | 그 라이브러리 판의 선택이다 |

★ 정규화 규칙은 **기본 넷**만 쓴다. ★ tokio 블록의 레지스트리 경로는 캡처가 `<registry>/` 로 바꿨다(배너에 그 `sed` 가 적혀 있다 — 규칙 33).

## 한눈에 — 쉽게 말하면

**Rust 표준 라이브러리는 「주문서 양식(`Future`)과 벨(`Waker`)」만 준다. 「주방장(실행기)」은 안 준다 — 직접 쓰거나(54번) 데려와야 한다(tokio).**
데려온 주방장이 **여러 명(멀티스레드)** 이면, 주문서는 **이 주방장 손에서 저 주방장 손으로** 넘어갈 수 있다. 그러려면 주문서에 끼워 둔 물건이 **다른 사람 손에 넘겨도 되는 것(`Send`)** 이어야 한다.
`Rc`(한 사람만 세는 계수기)나 `std` 의 락 열쇠(`MutexGuard` — 연 사람이 닫아야 하는 열쇠)는 **넘기면 안 되는 물건**이다. 그것을 **기다리는 동안(await) 주문서에 끼워 두면** 주문서째 못 넘긴다 — 컴파일러가 막는다.
그리고 주문서는 **자기 안의 다른 칸을 가리키는 메모**를 품을 수 있어서, **한 번 놓은 자리에서 옮기면 안 된다** — 그 약속이 `Pin` 이다.

| 비유 | 실체 |
|---|---|
| 「**주방장은 안 준다**」 | ★★★ **std 에는 실행기가 없다** — `fn main` 에서 `.await` 는 E0728, `async fn main` 은 E0752((1)) |
| 「**넘겨도 되는 물건**」 | ★★ **`Send`** — 다른 스레드로 옮겨도 되는 타입((2)) |
| 「**기다리는 동안 끼워 둔 넘기면 안 되는 물건**」 | ★★★ **await 를 가로지른 `Rc` · `MutexGuard`** → 「future cannot be sent between threads safely」((2)·(3)) |
| 「**끼우기 전에 치운다**」 | ★★★ **안쪽 블록으로 가둔다** — `drop()` 은 **빌린 적이 있으면** 안 통한다((2)·(3)) |
| 「**옮기면 안 되는 주문서**」 | ★★ **`Pin`** — `async fn` 의 future 는 `Unpin` 이 아니다 · `Box::pin` 이 힙에 고정한다((4)) |
| 「**주방장 고르기**」 | ★★ **tokio `current_thread` 대 `multi_thread`** · `spawn`(`Send` 요구) 대 `spawn_local`((5)) |

```text
   await 를 가로지른 값 → future 의 필드가 된다 (54번 (4))
          │
          ▼
   그 필드의 타입이 !Send (Rc · std MutexGuard)
          │
          ▼
   future 전체가 !Send  ── Send 를 요구하는 자리 ──▶  컴파일 에러 「future cannot be sent between threads safely」
          │                  (need_send · tokio::spawn)       note: has type `…` which is not `Send`
          │                                                   note: await occurs here, with `…` maybe used later
          ▼
   Send 를 안 요구하는 자리(block_on · spawn_local)에서는 그대로 돈다
```

> **`Send`** — 「이 값의 소유권을 다른 스레드로 옮겨도 안전하다」는 표시 트레이트. 컴파일러가 필드를 보고 자동으로 붙인다.\
> 예: `Rc<i32>` 는 `Send` 가 아니다([41번](../41-rc-arc-shared-ownership-and-weak-cycles/) (3) — `thread::spawn` 에 넘기면 E0277).

> **런타임(runtime)** — 실행기에 입출력·타이머·작업 생성까지 얹은 라이브러리. tokio 가 대표다.\
> 예: (5)의 `tokio::runtime::Builder::new_multi_thread()`.

## 이 주제가 답하려는 질문

1. ★★★ **표준 라이브러리에 실행기가 없다는 것은 코드에서 무엇으로 드러나나** — `fn main` 에서 `.await` 하면 · `async fn main` 이면 · std 의 `task`·`future` 모듈에는 무엇이 있나((1)).
2. ★★★ **await 를 가로지르는 `Rc`·락은 왜 막히나 — 그리고 어떻게 풀리나**((2)·(3)).
3. ★★ **`Pin` 은 왜 `poll` 서명에 있나** — `async fn` 의 future 를 `Unpin` 자리에 넣으면 · `Box::pin` 이면((4)).
4. ★★ **런타임을 고르면 무엇이 달라지나** — 스레드 · `spawn` 의 경계((5)).

★ **선행** — [**54번 주제**](../54-async-await-and-future-state-machines/)가 이 주제의 뿌리다. ★★★ **이미 잰 것 — 다시 재지 않고 인용한다.**
54번 (2) — **실행기 30줄**(`Wake` · `park`/`unpark` · `pin!`) · (3) — **`Waker` 가 안 불리면 영원히 멈춘다**(`exit 124`) · ★★★ (4) — **빌린 적이 있는 지역 변수는 await 앞에서만 썼어도 future 에 들어간다**(`b` 1032 대 `b2` 8).
[**41번 주제**](../41-rc-arc-shared-ownership-and-weak-cycles/) (3) — **`Rc` 는 `Send` 가 아니다**(E0277) · [**42번 주제**](../42-refcell-cell-interior-mutability/) — `Mutex` 가드 · [**44번 주제**](../44-drop-mem-drop-replace-and-take/) — 가드가 버려지는 줄.
이 편은 그 위에 **await 를 가로지를 때의 `Send`** 와 **실행기가 없다는 것의 결과**, **`Pin` 이 서명에 있는 이유**를 더한다.

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ① `Send` 진단 사슬이다

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ① ★★★ **컴파일러 진단 사슬** | await 를 가로지른 값이 **어느 줄에서 무엇 때문에** future 를 `!Send` 로 만드나 | ★ **본체**((2)·(3)) |
| ② ★★★ **E0728 · E0752** | std 에 실행기가 없다는 것이 **문법에서** 어떻게 드러나나 | 쓴다((1)) |
| ③ ★★ **로컬 문서의 항목 목록** | std `task`·`future` 에 **무엇이 있고 무엇이 없나** | 쓴다((1)) |
| ④ ★★ **E0277 `cannot be unpinned`** + `Box::pin` 실행 | `Pin` 이 필요한 자리 | 쓴다((4)) |
| ⑤ ★★ **tokio(캐시 · `--offline`)** | 런타임의 스레드 · `spawn` 경계 | 쓴다((5)) |
| **교착(deadlock) 재현** | await 를 가로지른 락이 실제로 막히는 장면 | ★ **일부러 안 했다** — ① 이 **같은 질문을 컴파일 시점에** 답한다(아래) |
| 자기 참조 구조체의 **이동 사고** | 옮긴 뒤 옛 주소를 가리키는 포인터 | ★ **안 던졌다** — `unsafe` 가 필요하다(56번 몫). **도식 + 명세 인용**((4)) |
| 시간·스레드 비용 | — | ★ **안 쟀다** |

★★ **제5의 상태 — 「같은 질문을 다른 창으로」.** 「await 를 가로지르는 `std` 락은 왜 문제인가」를 **실행으로** 물으면 교착을 일부러 만들어야 하고, 교착은 **판마다 안 날 수도 있다**(안 터졌다 ≠ 안전하다).
그래서 질문을 **「그 future 를 다른 스레드로 넘길 수 있나」** 로 바꿔 **컴파일러**에게 물었다 — 답은 **판마다 같다.**
★ 바꾼 창이 못 보는 것 — **단일 스레드 실행기**(`Send` 를 안 요구한다)에서의 교착은 이 창에 **안 걸린다.** 그 자리는 (3)의 산문과 tokio 의 비동기 락으로 메운다.

### (1) ★★★ std 에 실행기가 없다 — 문법이 먼저 막는다

**`fn main` 에서 `.await`.**

```text
===== 소스: r55_await_in_main.rs =====
async fn f() -> u32 {
    7
}

fn main() {
    let v = f().await;
    println!("{v}");
}
===== rustc --edition 2021 r55_await_in_main.rs =====
error[E0728]: `await` is only allowed inside `async` functions and blocks
 --> r55_await_in_main.rs:6:17
  |
5 | fn main() {
  | --------- this is not `async`
6 |     let v = f().await;
  |                 ^^^^^ only allowed inside `async` functions and blocks

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0728`.
(exit 1)
```

- ★★★ **E0728 — `await` is only allowed inside `async` functions and blocks.** 표지 「this is not `async`」가 `fn main` 을 짚는다. Reference: 「Await expressions are legal only within an async context, like an async fn, async closure, or async block」.
- ★★ `.await` 는 **바깥 future 의 poll 안에서만** 뜻이 있다(54번 (3)) — 보통 함수에는 「멈췄다 이어 갈」 상태 기계가 없다.

**그럼 `main` 을 `async` 로.**

```text
===== 소스: r55_async_main.rs =====
async fn f() -> u32 {
    7
}

async fn main() {
    let v = f().await;
    println!("{v}");
}
===== rustc --edition 2021 r55_async_main.rs =====
error[E0752]: `main` function is not allowed to be `async`
 --> r55_async_main.rs:5:1
  |
5 | async fn main() {
  | ^^^^^^^^^^^^^^^ `main` function is not allowed to be `async`

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0752`.
(exit 1)
```

- ★★★ **E0752 — `main` function is not allowed to be `async`.** 누군가 `main` 의 future 를 poll 해야 하는데 **그 누군가가 표준에 없다.** Reference 는 `main` 에 「its return type must implement the `Termination` trait」라는 제약을 두고, rustc 는 `async` 를 **따로 번호를 붙여**(E0752) 거부한다.
- ★★ **그래서 `#[tokio::main]` 같은 속성이 있다** — tokio-macros 소스의 문서 주석이 「Equivalent code not using `#[tokio::main]`」으로 그 뜻을 적는다:

````text
===== sed -n '/^\/\/\/ ## Using the multi-threaded runtime/,/^\/\/\/ ## Using the current-thread runtime/p' "$(ls -d $HOME/.cargo/registry/src/*/tokio-macros-2.7.2)/src/lib.rs" =====
/// ## Using the multi-threaded runtime
///
/// ```rust
/// #[tokio::main]
/// async fn main() {
///     println!("Hello world");
/// }
/// ```
///
/// Equivalent code not using `#[tokio::main]`
///
/// ```rust
/// fn main() {
///     tokio::runtime::Builder::new_multi_thread()
///         .enable_all()
///         .build()
///         .unwrap()
///         .block_on(async {
///             println!("Hello world");
///         })
/// }
/// ```
///
/// ## Using the current-thread runtime
(exit 0)
````

- ★★ **`async fn main` 이 보통 `fn main` + 런타임 생성 + `block_on` 으로 바뀐다** — 54번에서 손으로 쓴 `block_on` 의 자리를 런타임이 채운다. ★ 이 블록은 **캐시에 있는 tokio-macros 2.7.2 의 소스 주석**이다(매크로 확장 결과를 직접 본 것이 아니다 — `cargo expand` 도 `-Zunpretty` 도 이 머신에서 못 쓴다 · [57번](../57-macros-macro-rules-and-procedural-macros/) 맨 위 부분).

**std 의 `task`·`future` 에 무엇이 있나.**

```text
===== 소스: r55_std_task.py =====
# List every item page under std::task and std::future in the local rust-docs copy,
# with the "Stable since" version from the page heading (or "nightly-only" if the heading has none).
import os
import re
import subprocess

doc = subprocess.run(["rustc", "--print", "sysroot"], capture_output=True, text=True).stdout.strip()
doc += "/share/doc/rust/html/std"

for module in ["task", "future"]:
    for name in sorted(os.listdir(os.path.join(doc, module))):
        kind, _, rest = name.partition(".")
        if kind not in ("struct", "trait", "enum", "fn", "macro") or "!" in name:
            continue
        page = open(os.path.join(doc, module, name), encoding="utf-8").read()
        head = page[page.find("<h1"):page.find('<details class="toggle top-doc"')]
        m = re.search(r"Stable since Rust version ([0-9.]+)", head)
        since = m.group(1) if m else "nightly-only"
        print(f"std::{module}::{rest[:-5]:<20} {kind:<7} {since}")
===== python3 r55_std_task.py =====
std::task::Poll                 enum    1.36.0
std::task::ready                macro   1.64.0
std::task::Context              struct  1.36.0
std::task::ContextBuilder       struct  nightly-only
std::task::LocalWaker           struct  nightly-only
std::task::RawWaker             struct  1.36.0
std::task::RawWakerVTable       struct  1.36.0
std::task::Waker                struct  1.36.0
std::task::LocalWake            trait   nightly-only
std::task::Wake                 trait   1.51.0
std::future::async_drop_in_place  fn      nightly-only
std::future::pending              fn      1.48.0
std::future::poll_fn              fn      1.64.0
std::future::ready                fn      1.48.0
std::future::join                 macro   nightly-only
std::future::Pending              struct  1.48.0
std::future::PollFn               struct  1.64.0
std::future::Ready                struct  1.48.0
std::future::AsyncDrop            trait   nightly-only
std::future::Future               trait   1.36.0
std::future::IntoFuture           trait   1.64.0
(exit 0)
```

- ★★★ **실행기·작업 생성·`block_on`·타이머가 없다** — 있는 것은 **양식**(`Future` · `IntoFuture` · `Poll`)과 **벨**(`Waker` · `Context` · `Wake` · `RawWaker`)과 **작은 future 몇 개**(`ready` · `pending` · `poll_fn`)뿐이다. `join!` 조차 **nightly-only** 다.
- ★ 이것이 「표준에 실행기가 없다」의 **출력**이다 — 목록을 **로컬 문서에서 뽑았고**, 각 항목의 「Stable since」를 페이지 머리에서 읽었다(없으면 `nightly-only`). 역사적 이유는 [`history/rust/04-비동기-동시성.md`](../../../../history/rust/04-비동기-동시성.md) 4부 「왜 런타임을 표준 라이브러리 밖으로 분리했나」.

### (2) ★★★ await 를 가로지른 `Rc` — `Send` 를 요구하는 자리에서

**언제 쓰나** — 멀티스레드 런타임의 `spawn` 에 future 를 넘길 때마다. 여기서는 그 경계만 떼어 **`fn need_send<F: Future + Send>(_f: F)`** 로 흉내 낸다(poll 은 안 한다 — 타입 검사만).

```text
===== 소스: r55_send_rc.rs =====
use std::future::Future;
use std::rc::Rc;

async fn tick() {}

fn need_send<F: Future + Send>(_f: F) {}

async fn keeps_rc() {
    let r = Rc::new(5);
    tick().await;
    println!("{r}");
}

fn main() {
    need_send(keeps_rc());
}
===== rustc --edition 2021 r55_send_rc.rs =====
error: future cannot be sent between threads safely
  --> r55_send_rc.rs:15:15
   |
15 |     need_send(keeps_rc());
   |               ^^^^^^^^^^ future returned by `keeps_rc` is not `Send`
   |
   = help: within `impl Future<Output = ()>`, the trait `Send` is not implemented for `Rc<i32>`
note: future is not `Send` as this value is used across an await
  --> r55_send_rc.rs:10:12
   |
 9 |     let r = Rc::new(5);
   |         - has type `Rc<i32>` which is not `Send`
10 |     tick().await;
   |            ^^^^^ await occurs here, with `r` maybe used later
note: required by a bound in `need_send`
  --> r55_send_rc.rs:6:26
   |
 6 | fn need_send<F: Future + Send>(_f: F) {}
   |                          ^^^^ required by this bound in `need_send`

error: aborting due to 1 previous error

(exit 1)
```

- ★★★ **「future cannot be sent between threads safely」** — ★ **에러 번호가 없다**(`error:` 만). 같은 `Send` 실패라도 스레드 쪽([41번](../41-rc-arc-shared-ownership-and-weak-cycles/) (3))은 **E0277** 이었는데, future 쪽은 rustc 가 **따로 만든 문구**로 낸다.
- ★★★ **사슬 셋** — ① `help:` 「the trait `Send` is not implemented for `Rc<i32>`」(**무엇이** 문제인가) ② `note:` 「**has type `Rc<i32>` which is not `Send`**」가 9행 `let r` 을, 「**await occurs here, with `r` maybe used later**」가 10행 `.await` 를 짚는다(**어디서** 문제가 되나) ③ `note:` 「required by a bound in `need_send`」(**누가** 요구했나).
- ★★ **`Rc` 가 있어서가 아니라 `Rc` 를 쥔 채 await 해서다** — 「await occurs here, with `r` maybe used later」가 핵심 문장이다. await 너머로 살아 있는 값은 **future 의 필드**가 되고(54번 (4)), 필드 하나가 `!Send` 면 future 전체가 `!Send` 다.

**await 전에 `drop(r)` 하면.**

```text
===== 소스: r55_send_rc_drop.rs =====
use std::future::Future;
use std::rc::Rc;

async fn tick() {}

fn need_send<F: Future + Send>(_f: F) {}

async fn read_then_drop() {
    let r = Rc::new(5);
    let n = *r;
    drop(r);
    tick().await;
    println!("{n}");
}

fn main() {
    need_send(read_then_drop());
}
===== rustc --edition 2021 r55_send_rc_drop.rs =====
error: future cannot be sent between threads safely
  --> r55_send_rc_drop.rs:17:15
   |
17 |     need_send(read_then_drop());
   |               ^^^^^^^^^^^^^^^^ future returned by `read_then_drop` is not `Send`
   |
   = help: within `impl Future<Output = ()>`, the trait `Send` is not implemented for `Rc<i32>`
note: future is not `Send` as this value is used across an await
  --> r55_send_rc_drop.rs:12:12
   |
 9 |     let r = Rc::new(5);
   |         - has type `Rc<i32>` which is not `Send`
...
12 |     tick().await;
   |            ^^^^^ await occurs here, with `r` maybe used later
note: required by a bound in `need_send`
  --> r55_send_rc_drop.rs:6:26
   |
 6 | fn need_send<F: Future + Send>(_f: F) {}
   |                          ^^^^ required by this bound in `need_send`

error: aborting due to 1 previous error

(exit 1)
```

- ★★★ **여전히 에러다** — `drop(r);`(11행)이 await(12행) **앞에** 있는데도 「await occurs here, with `r` maybe used later」. 진단이 `...` 로 10\~11행을 건너뛰고 9행과 12행만 짚는다.
- ★★★ **이유는 10행의 `*r`** — `r` 을 **한 번 빌렸다**(역참조는 `Deref::deref(&r)` 다). 54번 (4)에서 **빌린 적이 있는 지역 변수는 스코프 끝까지 future 에 남았다**(`b` 1032) — 같은 분석이 여기서는 「`r` 이 await 너머로 살아 있을 수 있다」고 판정한다.

**빌리지 않고 버리거나, 안쪽 블록에 가두면.**

```text
===== 소스: r55_send_rc_ok.rs =====
use std::future::Future;
use std::rc::Rc;

async fn tick() {}

fn need_send<F: Future + Send>(_f: F) {}

async fn drop_without_reading() {
    let r = Rc::new(5);
    drop(r);
    tick().await;
}

async fn read_in_inner_block() {
    let n = {
        let r = Rc::new(5);
        *r
    };
    tick().await;
    println!("{n}");
}

fn main() {
    need_send(drop_without_reading());
    need_send(read_in_inner_block());
    eprintln!("[main] reached the end");
}
===== rustc --edition 2021 r55_send_rc_ok.rs =====
(exit 0)
===== ./r55_send_rc_ok =====
[main] reached the end
(exit 0)
```

- ★★★ **둘 다 통과** — `drop_without_reading` 은 `r` 을 **빌린 적이 없어** `drop` 이 통했고, `read_in_inner_block` 은 **스코프가 await 앞에서 닫혔다.**
- ★★ **실무 처방은 안쪽 블록이다** — 쓰지도 않을 값을 만들 일은 없으니 `drop` 판은 거의 쓸모가 없다. **「`!Send` 값은 블록에 가두고, 필요한 값만 꺼내 await 한다」.**

### (3) ★★★ await 를 가로지른 `std::sync::MutexGuard`

```text
===== 소스: r55_send_guard.rs =====
use std::future::Future;
use std::sync::Mutex;

async fn tick() {}

fn need_send<F: Future + Send>(_f: F) {}

async fn guard_across_await(m: &Mutex<u32>) {
    let mut g = m.lock().unwrap();
    *g += 1;
    tick().await;
    *g += 1;
}

fn main() {
    static M: Mutex<u32> = Mutex::new(0);
    need_send(guard_across_await(&M));
}
===== rustc --edition 2021 r55_send_guard.rs =====
error: future cannot be sent between threads safely
  --> r55_send_guard.rs:17:15
   |
17 |     need_send(guard_across_await(&M));
   |               ^^^^^^^^^^^^^^^^^^^^^^ future returned by `guard_across_await` is not `Send`
   |
   = help: within `impl Future<Output = ()>`, the trait `Send` is not implemented for `std::sync::MutexGuard<'_, u32>`
note: future is not `Send` as this value is used across an await
  --> r55_send_guard.rs:11:12
   |
 9 |     let mut g = m.lock().unwrap();
   |         ----- has type `std::sync::MutexGuard<'_, u32>` which is not `Send`
10 |     *g += 1;
11 |     tick().await;
   |            ^^^^^ await occurs here, with `mut g` maybe used later
note: required by a bound in `need_send`
  --> r55_send_guard.rs:6:26
   |
 6 | fn need_send<F: Future + Send>(_f: F) {}
   |                          ^^^^ required by this bound in `need_send`

error: aborting due to 1 previous error

(exit 1)
```

- ★★★ **같은 문구 · 같은 사슬** — 「has type `std::sync::MutexGuard<'_, u32>` which is not `Send`」 · 「await occurs here, with `mut g` maybe used later」.
- ★★★ **`MutexGuard` 는 왜 `!Send` 인가** — std: 「A `MutexGuard` is not `Send` to maximize platform portability. **On platforms that use POSIX threads … there is a requirement to release mutex locks on the same thread they were acquired.**」 락을 연 스레드가 닫아야 한다 — 가드를 쥔 future 가 다른 워커로 옮겨 가 **거기서 가드를 버리면** 그 약속이 깨진다.

**가드를 쓰고 `drop(g)` 한 뒤 await 하면.**

```text
===== 소스: r55_send_guard_drop.rs =====
use std::future::Future;
use std::sync::Mutex;

async fn tick() {}

fn need_send<F: Future + Send>(_f: F) {}

async fn guard_dropped(m: &Mutex<u32>) {
    let mut g = m.lock().unwrap();
    *g += 1;
    drop(g);
    tick().await;
}

fn main() {
    static M: Mutex<u32> = Mutex::new(0);
    need_send(guard_dropped(&M));
}
===== rustc --edition 2021 r55_send_guard_drop.rs =====
error: future cannot be sent between threads safely
  --> r55_send_guard_drop.rs:17:15
   |
17 |     need_send(guard_dropped(&M));
   |               ^^^^^^^^^^^^^^^^^ future returned by `guard_dropped` is not `Send`
   |
   = help: within `impl Future<Output = ()>`, the trait `Send` is not implemented for `std::sync::MutexGuard<'_, u32>`
note: future is not `Send` as this value is used across an await
  --> r55_send_guard_drop.rs:12:12
   |
 9 |     let mut g = m.lock().unwrap();
   |         ----- has type `std::sync::MutexGuard<'_, u32>` which is not `Send`
...
12 |     tick().await;
   |            ^^^^^ await occurs here, with `mut g` maybe used later
note: required by a bound in `need_send`
  --> r55_send_guard_drop.rs:6:26
   |
 6 | fn need_send<F: Future + Send>(_f: F) {}
   |                          ^^^^ required by this bound in `need_send`

error: aborting due to 1 previous error

(exit 1)
```

- ★★★ **여전히 에러** — (2)와 같다. `*g += 1` 이 `g` 를 **빌렸다**(`DerefMut`). 가드는 **쓰려고 잡는 것**이니 「빌리지 않고 `drop`」판은 없다 — **가드는 블록에 가둔다.**

```text
===== 소스: r55_send_guard_ok.rs =====
use std::future::Future;
use std::sync::Mutex;

async fn tick() {}

fn need_send<F: Future + Send>(_f: F) {}

async fn guard_in_block(m: &Mutex<u32>) {
    {
        let mut g = m.lock().unwrap();
        *g += 1;
    }
    tick().await;
}

fn main() {
    static M: Mutex<u32> = Mutex::new(0);
    need_send(guard_in_block(&M));
    eprintln!("[main] reached the end");
}
===== rustc --edition 2021 r55_send_guard_ok.rs =====
(exit 0)
===== ./r55_send_guard_ok =====
[main] reached the end
(exit 0)
```

- ★★★ **통과** — 가드의 스코프가 await 앞에서 닫혔다.

**그런데 `Send` 가 안 걸리는 자리라면 — await 를 가로지른 락의 두 번째 문제.**

```text
   단일 스레드 실행기 (Send 를 안 요구한다 — 이 컴파일 창에는 안 걸린다)

   작업 A:  g = m.lock()  ──▶  .await (Pending — 스레드를 내준다)
                                         │
   작업 B:           m.lock()  ◀─────────┘ 같은 스레드에서 B 가 돈다 → A 가 쥔 락을 기다리며 스레드를 막는다
                                         │
   작업 A:  다시 poll 되어야 g 를 놓는데, 스레드가 B 에게 막혀 있다  →  아무도 나아가지 못한다 (교착)
```

- ★★ **이 그림은 개념 도식이다 — 재현하지 않았다.** 요점은 `std::sync::Mutex::lock` 이 **스레드를 막는(blocking)** 호출이라는 것이다 — async 의 규칙(「기다릴 때는 `Pending` 으로 스레드를 내준다」)과 맞지 않는다.
- ★★ **처방** — ① 가드를 **블록에 가둬 await 전에 놓는다**(위 `ok` 판 — 두 문제를 다 푼다) ② await 너머로 **쥐어야만** 하면 **런타임의 비동기 락**(`tokio::sync::Mutex` — `lock().await` 로 기다리며 스레드를 내준다)을 쓴다((5)에서 `spawn` 안에서 통과함을 봤다).

### (4) ★★ `Pin` 맛보기 — 왜 `poll` 서명에 있나

**서명과 명세.**

```text
===== 소스: r55_pin_doc.py =====
# Quote from the local rust-docs copy: the poll signature and two sentences of the std::pin module page.
import html
import re
import subprocess

doc = subprocess.run(["rustc", "--print", "sysroot"], capture_output=True, text=True).stdout.strip()
doc += "/share/doc/rust/html"


def text_of(path):
    t = open(doc + path, encoding="utf-8").read()
    return html.unescape(re.sub(r"<[^>]+>", "", t))


src = text_of("/src/core/future/future.rs.html")
print([l.strip() for l in src.split("\n") if "fn poll(self: Pin<&mut Self>" in l][0])

pin = re.sub(r"\s+", " ", text_of("/std/pin/index.html"))
for key in ["A key example of such self-referential types", "But if that value is moved, the pointer"]:
    m = re.search(re.escape(key) + r"[^.]*\.", pin)
    print("--", m.group(0))
===== python3 r55_pin_doc.py =====
113    fn poll(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Self::Output>;
-- A key example of such self-referential types are the state machines generated by the compiler to implement Future for async fns.
-- But if that value is moved, the pointer will still point to the old address where the value was located and not into the new location of self, thus becoming invalid.
(exit 0)
```

- ★★★ **`fn poll(self: Pin<&mut Self>, …)`** — `&mut Self` 가 아니라 **`Pin<&mut Self>`** 다(첫 줄의 `113` 은 소스 파일의 줄 번호다). 「이 future 는 **지금 자리에서 안 옮겨진다**고 약속된 상태로만 poll 할 수 있다」는 뜻이다.
- ★★★ **std: 「A key example of such self-referential types are the state machines generated by the compiler to implement `Future` for async fns.」** · 「But if that value is moved, the pointer will still point to the **old address** … thus becoming invalid.」

```text
   async fn f() { let buf = [0u8; 8]; let r = &buf; tick().await; use(r); }    (개념 도식 — 실제 배치는 rustc 가 정한다)

   future 가 주소 1000 에 있을 때            옮겨서 주소 2000 에 놓으면
   ┌──────────── 1000 ───────────┐           ┌──────────── 2000 ───────────┐
   │ buf : [0; 8]   ◀──┐         │           │ buf : [0; 8]                │
   │ r   : 1000 ───────┘         │   ──▶     │ r   : 1000  ─────▶ (옛 자리 — 이미 다른 값)   ✗
   │ 상태 : ①에서 멈춤              │           │ 상태 : ①에서 멈춤              │
   └─────────────────────────────┘           └─────────────────────────────┘
   await 너머로 buf 와 r 이 함께 산다 → 자기 안을 가리키는 필드 → 한 번 poll 한 뒤에는 옮기면 안 된다
```

- ★★ **그래서 첫 poll 전에 고정한다** — 54번의 실행기는 `pin!(fut)` 로 **스택에** 고정했다. 고정된 값은 안전한 코드로는 **다시 옮길 수 없다**(std: 「safe code cannot move that value to a different location」).

**`async fn` 의 future 를 `Unpin`(「옮겨도 괜찮다」) 자리에 넣으면.**

```text
===== 소스: r55_unpin.rs =====
use std::future::Future;

async fn f() -> u32 {
    7
}

fn need_unpin<F: Future + Unpin>(_f: F) {}

fn main() {
    need_unpin(f());
}
===== rustc --edition 2021 r55_unpin.rs =====
error[E0277]: `{async fn body of f()}` cannot be unpinned
  --> r55_unpin.rs:10:16
   |
 3 | async fn f() -> u32 {
   | ------------------- within this `impl Future<Output = u32>`
...
10 |     need_unpin(f());
   |     ---------- ^^^ within `impl Future<Output = u32>`, the trait `Unpin` is not implemented for `{async fn body of f()}`
   |     |
   |     required by a bound introduced by this call
   |
   = note: consider using the `pin!` macro
           consider using `Box::pin` if you need to access the pinned value outside of the current scope
note: required because it appears within the type `impl Future<Output = u32>`
  --> r55_unpin.rs:3:1
   |
 3 | async fn f() -> u32 {
   | ^^^^^^^^^^^^^^^^^^^
note: required by a bound in `need_unpin`
  --> r55_unpin.rs:7:27
   |
 7 | fn need_unpin<F: Future + Unpin>(_f: F) {}
   |                           ^^^^^ required by this bound in `need_unpin`

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0277`.
(exit 1)
```

- ★★★ **E0277 — `{async fn body of f()}` cannot be unpinned.** `async fn` 이 만든 타입은 **`Unpin` 이 아니다** — 이 `f` 는 **빌리는 것이 하나도 없는데도** 그렇다. 자기 참조일 **수 있는** 상태 기계에서 컴파일러가 `Unpin` 을 뺀다(보수적). `= note:` 가 처방 둘을 준다 — **`pin!` 매크로** · 「**`Box::pin`** if you need to access the pinned value outside of the current scope」.

**`Box::pin` 으로 — 서로 다른 future 를 한 `Vec` 에.**

```rust
// r55_boxpin.rs
mod r54_exec;

use std::future::Future;
use std::pin::Pin;

async fn seven() -> u32 {
    7
}

async fn add(a: u32, b: u32) -> u32 {
    a + b
}

fn need_unpin<F: Future + Unpin>(_f: &F) {}

fn main() {
    // Two different future types in one Vec: box them and pin the boxes.
    let jobs: Vec<Pin<Box<dyn Future<Output = u32>>>> = vec![Box::pin(seven()), Box::pin(add(1, 2))];
    need_unpin(&jobs[0]);
    for job in jobs {
        let v = r54_exec::block_on(job);
        eprintln!("[main] got {v}");
    }
}
```

```text
===== rustc --edition 2021 r55_boxpin.rs =====
(exit 0)
===== ./r55_boxpin =====
  [exec] poll #1
  [exec] poll #1 returned Ready
[main] got 7
  [exec] poll #1
  [exec] poll #1 returned Ready
[main] got 3
(exit 0)
```

- ★★★ **컴파일되고 `7` · `3`** — `Box::pin(seven())` 과 `Box::pin(add(1, 2))` 는 **타입이 다른 두 future** 인데 `Pin<Box<dyn Future<Output = u32>>>` 로 한 `Vec` 에 담겼다. **`need_unpin(&jobs[0])` 도 통과했다** — `Pin<Box<T>>` 자체는 옮겨도 된다(**상자만 옮겨지고 안의 future 는 힙 그 자리에 있다**).
- ★★ **`pin!` 대 `Box::pin`** — `pin!` 은 **스택에**, 그 스코프 안에서만. `Box::pin` 은 **힙에**, 들고 다닐 수 있다(대가: 할당 한 번 — **재지 않았다**).

### (5) ★★ 런타임 선택 — tokio 한 판(캐시 · `--offline`)

**언제 쓰나** — 실행기를 직접 쓰지 않을 모든 실전 코드. ★ 여기서는 **tokio 하나만** 잰다 — 다른 런타임과 비교하지 않았다.

```text
===== 소스: r55_tokio.sh =====
# One cargo package, three binaries. tokio comes from the local cargo cache (--offline, no network).
set -u
mkdir -p src/bin
cat > Cargo.toml <<'EOF'
[package]
name = "r55tk"
version = "0.1.0"
edition = "2021"

[dependencies]
tokio = { version = "=1.52.3", features = ["rt", "rt-multi-thread", "macros", "sync"] }
EOF

cat > src/bin/flavors.rs <<'EOF'
use std::collections::BTreeSet;
use std::rc::Rc;
use std::sync::Arc;

async fn tick() {
    tokio::task::yield_now().await;
}

async fn thread_names() -> BTreeSet<String> {
    let mut handles = Vec::new();
    for _ in 0..8 {
        handles.push(tokio::spawn(async {
            tick().await;
            std::thread::current().name().unwrap_or("?").to_string()
        }));
    }
    let mut names = BTreeSet::new();
    for h in handles {
        names.insert(h.await.unwrap());
    }
    names
}

fn main() {
    let ct = tokio::runtime::Builder::new_current_thread().build().unwrap();
    println!("current_thread : {:?}", ct.block_on(thread_names()));

    let mt = tokio::runtime::Builder::new_multi_thread().worker_threads(2).build().unwrap();
    println!("multi_thread   : {:?}", mt.block_on(thread_names()));

    // A task that keeps an Rc across an await: spawn_local on a LocalSet.
    let local = tokio::task::LocalSet::new();
    let v = local.block_on(&ct, async {
        tokio::task::spawn_local(async {
            let r = Rc::new(5);
            tick().await;
            *r
        })
        .await
        .unwrap()
    });
    println!("spawn_local    : {v}");

    // A tokio::sync::Mutex guard held across an await inside tokio::spawn.
    let m = Arc::new(tokio::sync::Mutex::new(0u32));
    let m2 = m.clone();
    let n = mt.block_on(async move {
        tokio::spawn(async move {
            let mut g = m2.lock().await;
            *g += 1;
            tick().await;
            *g += 1;
            *g
        })
        .await
        .unwrap()
    });
    println!("async mutex    : {n}");
}
EOF

cat > src/bin/rc_spawn.rs <<'EOF'
use std::rc::Rc;

#[tokio::main]
async fn main() {
    let h = tokio::spawn(async {
        let r = Rc::new(5);
        tokio::task::yield_now().await;
        *r
    });
    println!("{}", h.await.unwrap());
}
EOF

cat > src/bin/rc_spawn_ct.rs <<'EOF'
use std::rc::Rc;

#[tokio::main(flavor = "current_thread")]
async fn main() {
    let h = tokio::spawn(async {
        let r = Rc::new(5);
        tokio::task::yield_now().await;
        *r
    });
    println!("{}", h.await.unwrap());
}
EOF
===== bash r55_tokio.sh =====
(exit 0)
===== cargo tree --offline -e normal 2>/dev/null | sed "s#$PWD#.#g" =====
r55tk v0.1.0 (.)
└── tokio v1.52.3
    ├── pin-project-lite v0.2.17
    └── tokio-macros v2.7.2 (proc-macro)
        ├── proc-macro2 v1.0.107
        │   └── unicode-ident v1.0.24
        ├── quote v1.0.47
        │   └── proc-macro2 v1.0.107 (*)
        └── syn v3.0.3
            ├── proc-macro2 v1.0.107 (*)
            ├── quote v1.0.47 (*)
            └── unicode-ident v1.0.24
===== cargo tree --offline -e normal 2>&1 >/dev/null | sed "s#$PWD#.#g" =====
     Locking 7 packages to latest compatible versions
      Adding tokio v1.52.3 (available: v1.53.1)
(exit 0)
===== cargo run -q --offline --bin flavors =====
current_thread : {"main"}
multi_thread   : {"tokio-rt-worker"}
spawn_local    : 5
async mutex    : 2
(exit 0)
===== cargo build -q --offline --bin rc_spawn 2>&1 >/dev/null | sed "s#$HOME/.cargo/registry/src/[^/]*/#<registry>/#" =====
error: future cannot be sent between threads safely
   --> src/bin/rc_spawn.rs:5:13
    |
  5 |       let h = tokio::spawn(async {
    |  _____________^
  6 | |         let r = Rc::new(5);
  7 | |         tokio::task::yield_now().await;
  8 | |         *r
  9 | |     });
    | |______^ future created by async block is not `Send`
    |
    = help: within `{async block@src/bin/rc_spawn.rs:5:26: 5:31}`, the trait `Send` is not implemented for `Rc<i32>`
note: future is not `Send` as this value is used across an await
   --> src/bin/rc_spawn.rs:7:34
    |
  6 |         let r = Rc::new(5);
    |             - has type `Rc<i32>` which is not `Send`
  7 |         tokio::task::yield_now().await;
    |                                  ^^^^^ await occurs here, with `r` maybe used later
note: required by a bound in `tokio::spawn`
   --> <registry>/tokio-1.52.3/src/task/spawn.rs:176:21
    |
174 |     pub fn spawn<F>(future: F) -> JoinHandle<F::Output>
    |            ----- required by a bound in this function
175 |     where
176 |         F: Future + Send + 'static,
    |                     ^^^^ required by this bound in `spawn`

error: could not compile `r55tk` (bin "rc_spawn") due to 1 previous error
(exit 101)
===== cargo build -q --offline --bin rc_spawn_ct 2>&1 >/dev/null | grep -E '^(error|note)|--> ' | sed "s#$HOME/.cargo/registry/src/[^/]*/#<registry>/#" =====
error: future cannot be sent between threads safely
   --> src/bin/rc_spawn_ct.rs:5:13
note: future is not `Send` as this value is used across an await
   --> src/bin/rc_spawn_ct.rs:7:34
note: required by a bound in `tokio::spawn`
   --> <registry>/tokio-1.52.3/src/task/spawn.rs:176:21
error: could not compile `r55tk` (bin "rc_spawn_ct") due to 1 previous error
(exit 101)
```

- ★★★ **`current_thread : {"main"}`** — 작업 8개가 전부 **`block_on` 을 부른 스레드**에서 돌았다. **`multi_thread : {"tokio-rt-worker"}`** — 작업이 **워커 스레드들**에서 돌았다(이름이 같아 집합이 한 원소다 — 워커 **몇 개**가 썼는지는 이 탐침이 세지 않는다).
- ★★★ **`tokio::spawn` 에 `Rc` 를 쥔 채 await 하는 블록을 넘기면 — (2)와 같은 문구 · 같은 사슬**, 그리고 마지막 `note:` 가 **요구한 자리**를 tokio 소스에서 짚는다: `F: Future + Send + 'static`. `need_send` 로 흉내 낸 경계가 **실제 런타임의 경계 그대로**였다.
- ★★★ **`spawn_local : 5`** — 같은 `Rc` 작업을 **`LocalSet` 위의 `spawn_local`** 로 넘기면 돈다. `spawn_local` 은 **작업을 그 스레드에 묶어 두는** 대신 `Send` 를 안 요구한다.
- ★★ **`async mutex : 2`** — `tokio::sync::Mutex` 의 가드는 await 를 가로질러 쥐어도 **`tokio::spawn` 을 통과했다**((3)의 `std` 가드와 대비).
- ★ **도구 판** — `cargo tree` 가 `tokio v1.52.3` · `tokio-macros v2.7.2` · `pin-project-lite v0.2.17` 을 보인다. ★ 표준 오류의 「Adding tokio v1.52.3 (available: v1.53.1)」는 **캐시에 더 새 판이 있다**는 cargo 의 안내다.

| 고를 것 | 작업이 도는 스레드 | `spawn` 이 요구하는 것 | `Rc`·`std` 가드를 await 너머로 |
|---|---|---|---|
| 직접 만든 `block_on`(54번) | 부른 스레드 하나 | (작업 생성이 없다) | 된다(`Send` 를 안 요구) |
| tokio `current_thread` + `spawn` | 부른 스레드(`main`) | ★ **`Send + 'static`**(런타임 종류와 무관한 **함수의 경계**) | ★ **막힌다** |
| tokio `LocalSet` + `spawn_local` | 그 스레드에 묶임 | `'static` | 된다 |
| tokio `multi_thread` + `spawn` | 워커 스레드들 | `Send + 'static` | 막힌다 |

- ★★ **`current_thread` 에서도 `tokio::spawn` 은 `Send` 를 요구한다** — 블록 마지막의 `rc_spawn_ct.rs`(`flavor = "current_thread"`)가 **같은 에러 · 같은 `spawn.rs:176:21`** 로 막혔다(진단을 `error`·`note`·`-->` 줄로 줄여 실었다 — 배너의 `grep`). 경계는 **`spawn` 함수의 서명**에 있지 런타임 종류에 있지 않다. `rc_spawn.rs` 의 `#[tokio::main]` 기본은 `multi_thread` 다(위 tokio-macros 주석).

## 문법 — 형태와 규칙

```text
   fn main() { f().await }                 ← E0728 — async 문맥 밖
   async fn main() { … }                   ← E0752 — 누가 poll 하나? (런타임 매크로가 풀어 준다)
   fn need_send<F: Future + Send>(f: F)    ← spawn 류의 경계를 흉내 내는 탐침
   { let g = m.lock().unwrap(); … }        ← !Send 값은 블록에 가둔 뒤 .await
   fn poll(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Self::Output>
   std::pin::pin!(fut)   Box::pin(fut)     ← 스택에 고정 / 힙에 고정 (Pin<Box<_>> 는 Unpin)
   tokio::spawn(fut)        ← F: Future + Send + 'static
   tokio::task::spawn_local(fut)   (LocalSet 안에서)   ← Send 불요
```

- ★★★ **await 너머로 살아 있는 `!Send` 값 하나가 future 전체를 `!Send` 로 만든다**((2)·(3)).
- ★★★ **「살아 있나」는 rustc 가 판정한다 — 빌린 적이 있으면 `drop()` 으로는 안 끝난다. 블록에 가둔다**((2)·(3)).
- ★★ **`async fn` 의 future 는 `Unpin` 이 아니다 — poll 하려면 `pin!` 이나 `Box::pin` 으로 고정한다**((4)).

## 어디서 틀리나

### 1. ★★★ 「`async fn main` 을 쓰면 된다」

(1) — **E0752.** 표준에는 `main` 의 future 를 돌릴 사람이 없다 — 런타임의 매크로(`#[tokio::main]`)가 그 자리를 채운다.

### 2. ★★★ 「await 앞에서 `drop(guard)` 하면 `Send` 가 된다」

(2)·(3) — **이 판에서는 안 된다**(빌린 적이 있으면). ★ 흔한 조언이 틀린 자리다 — **안쪽 블록**이 되는 방법이다. 판이 오르면 분석이 정교해져 뒤집힐 수 있는 **구현의 칸**이다.

### 3. ★★★ 「`Rc` 를 async 코드에서 쓰면 안 된다」

(2)·(5) — **`Rc` 가 아니라 「`Rc` 를 쥔 채 await」가 문제다.** 블록 안에서만 쓰면 `Send` 판에도 통과하고, `spawn_local` 이면 await 를 가로질러도 된다.

### 4. ★★ 「단일 스레드 런타임이면 `std::sync::Mutex` 를 await 너머로 쥐어도 된다」

(3) — `Send` 에러는 피할 수 있어도 **교착의 구조**가 남는다(개념 도식 — 재현하지 않았다). **await 전에 놓거나 비동기 락**을 쓴다.

### 5. ★★ 「`current_thread` 런타임의 `spawn` 은 `Send` 를 안 요구한다」

(5) — `tokio::spawn` 의 경계는 **서명**에 있다(`F: Future + Send + 'static`). `Send` 를 안 요구하는 것은 **`spawn_local`** 이다.

### 6. ★ 「`Pin` 은 값을 못 바꾸게 하는 것이다」

(4) — **못 옮기게** 하는 것이다. poll 은 `Pin<&mut Self>` 로 **바꾸면서** 진행한다.

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| `.await` 는 async 문맥에서만 | ★ **언어**(Reference — E0728) | (1) |
| `main` 은 `async` 일 수 없다 | ★ **언어**(E0752 · Reference 의 `main` 제약) | (1) |
| std 에 실행기가 없다 | ★ **std 의 구성**(로컬 문서 목록) | (1) |
| `!Send` 필드 하나면 future 전체가 `!Send` | ★ **언어**(자동 트레이트 규칙) | (2) |
| 「빌린 적이 있으면 `drop` 뒤에도 await 너머로 살아 있다」고 보는 판정 | ★ **rustc 의 분석**(이 판의 관찰 — 54번 (4)의 크기와 같은 모양) | (2)·(3) |
| future `Send` 실패의 문구·번호 없음 | ★ **rustc 의 진단**(판에 매인다) | (2) |
| `MutexGuard: !Send` | ★ **std 의 선택** — 「to maximize platform portability」(pthread 규칙) | (3) |
| `async fn` future 가 `Unpin` 이 아니다 · `Pin<Box<T>>: Unpin` | ★ **언어·std** | (4) |
| 자기 참조 future 를 옮기면 포인터가 옛 주소를 가리킨다 | ★ **std `pin` 문서의 설명**(이 문서는 재현 안 함) | (4) |
| `tokio::spawn` 의 `Send + 'static` · 워커 이름 | ★ **tokio 1.52.3 의 API·구현** | (5) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 근거 |
|---|---|---|
| 실전 서비스·입출력 | **런타임**(tokio 등) — 표준에는 없다 | (1)·(5) |
| 작업을 여러 스레드로 퍼뜨린다 | `multi_thread` + `spawn` — **`Send` 인 future 만** | (5) |
| `Rc`·`RefCell` 을 await 너머로 꼭 써야 한다 | `LocalSet` + `spawn_local` | (5) |
| 락을 잠깐 잡고 await 한다 | ★★ **블록으로 가둬 await 전에 놓는다** — `std::sync::Mutex` 그대로 | (3) |
| 락을 쥔 채 await 해야만 한다 | 비동기 락(`tokio::sync::Mutex`) | (3)·(5) |
| 서로 다른 future 를 한 컬렉션에 | `Pin<Box<dyn Future<Output = T>>>` | (4) |
| 한 스코프에서 잠깐 poll | `std::pin::pin!` | (4) · 54번 (2) |

## 핵심 문장

- ★★★ **표준 라이브러리는 `Future`·`Waker` 까지만 준다 — 실행기는 없다. 그래서 `fn main` 에서 `.await` 는 E0728, `async fn main` 은 E0752 다.**
- ★★★ **await 를 가로질러 쥔 `Rc`·`std` 락 가드는 future 전체를 `!Send` 로 만든다 — 진단이 「has type … which is not `Send`」와 「await occurs here, with … maybe used later」로 자리를 짚는다.**
- ★★★ **빌린 적이 있는 값은 `drop()` 해도 await 너머로 살아 있다고 판정된다(이 판) — 안쪽 블록에 가둬라.**
- ★★ **`async fn` 의 future 는 자기 안을 가리킬 수 있어 `Unpin` 이 아니다 — `pin!`·`Box::pin` 으로 고정하고 poll 한다.**
- ★★ **tokio 의 `spawn` 은 런타임 종류와 무관하게 `Send + 'static` 을 요구하고, `spawn_local` 은 `Send` 를 안 요구한다.**

## 관련 자료

- [**54번 주제**](../54-async-await-and-future-state-machines/) — 게으름 · 실행기 · 상태 기계 크기. **그쪽은 「무엇이 돌고 무엇이 남나」, 여기는 「남은 것이 어디로 갈 수 있나」.**
- [**41번 주제**](../41-rc-arc-shared-ownership-and-weak-cycles/) — `Rc: !Send`(E0277) · `Arc`. [**42번 주제**](../42-refcell-cell-interior-mutability/) · [**44번 주제**](../44-drop-mem-drop-replace-and-take/) — 가드와 그 해제 시점.
- [**50번 주제**](../50-send-sync-in-compiler-errors/) · [**52번 주제**](../52-mutex-rwlock-arc-and-poisoning/) — `Send`/`Sync` 진단과 `Mutex` 자체. **그쪽은 스레드 경계, 여기는 await 경계.**
- 목록의 **56번 주제** — `unsafe`. **자기 참조 구조체를 실제로 만들어 옮기는 실험은 그쪽 몫**이다.
- [`history/rust/04-비동기-동시성.md`](../../../../history/rust/04-비동기-동시성.md) — **그쪽은 런타임을 표준 밖에 둔 이유와 Tokio·async-std 의 분화, `Pin` 이 들어온 역사**, 여기는 그 결과를 **진단으로** 본다.
- [Kotlin 52번](../../../kotlin/syntax/52-coroutine-basics-suspend-scope-launch-async/) — `runBlocking`·`launch` 는 **라이브러리**(kotlinx.coroutines)다. **「실행 엔진이 표준 밖」이라는 모양은 Rust 와 같다.**

## 용어 풀이

- **`Send`** — 다른 스레드로 소유권을 옮겨도 되는 타입의 표시 트레이트.
- **자동 트레이트(auto trait)** — 필드가 모두 구현하면 컴파일러가 자동으로 붙이는 트레이트(`Send`·`Sync`·`Unpin`).
- **런타임** — 실행기 + 입출력·타이머·작업 생성을 묶은 라이브러리.
- **`spawn` / `spawn_local`** — 작업을 런타임에 올리는 함수 / 그 스레드에 묶어 올리는 함수.
- **`Pin<P>`** — 포인터 `P` 가 가리키는 값을 **옮기지 않겠다**는 약속을 타입으로 든 것.
- **`Unpin`** — 「고정되어 있어도 옮겨도 괜찮다」는 자동 트레이트. 대부분의 타입이 구현하고, `async fn` 의 future 는 아니다.
- **자기 참조(self-referential)** — 값 안의 필드가 같은 값 안의 다른 곳을 가리키는 것.
- **비동기 락** — 기다릴 때 스레드를 막지 않고 `Pending` 으로 내주는 락(`tokio::sync::Mutex`).

## 더 들어가면

- `Send` 경계의 `'static` 쪽 — 참조를 캡처한 future 를 `spawn` 하면 나는 수명 에러. **던지지 않았다.**
- `tokio::task::spawn_blocking` — 막는 호출을 전용 스레드로. **던지지 않았다.**
- 트레이트 안의 `async fn`(history 문서 기준 1.75)과 반환 future 의 `Send` 를 호출하는 쪽이 못 정하는 문제 — [`history/rust/04-비동기-동시성.md`](../../../../history/rust/04-비동기-동시성.md) 5부.
- 자기 참조 구조체를 직접 만들어 `Pin` 없이 옮겨 보기 — `unsafe` 가 필요하다. 목록의 **56번 주제**.

## 실행 환경

**기준 소스** — [Reference — Await expressions](https://doc.rust-lang.org/reference/expressions/await-expr.html)(「Await expressions are legal only within an async context」) ·
[Reference — Crates and source files §main](https://doc.rust-lang.org/reference/crates-and-source-files.html)(`main` 의 제약) ·
[std — `MutexGuard`](https://doc.rust-lang.org/std/sync/struct.MutexGuard.html)(`impl !Send` 와 그 이유) · [std — `pin`](https://doc.rust-lang.org/std/pin/index.html) · [std — `Future::poll`](https://doc.rust-lang.org/std/future/trait.Future.html) ·
std `task`·`future` 모듈의 **항목 목록 자체**((1)의 블록이 로컬 문서에서 뽑았다).
★ 전부 **이 머신의 `rust-docs`(1.92.0) 로컬 사본**을 열어 읽었다. tokio 는 **로컬 cargo 캐시의 소스**를 컴파일했다(문서는 안 읽었다).
**실행 검증** — `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `cargo 1.92.0 (344c4567c 2025-10-21)` · `x86_64-unknown-linux-gnu`.
표준 라이브러리만 쓰는 블록은 **`rustc --edition 2021 <파일>.rs`**, tokio 블록은 **`cargo … --offline`**(네트워크 없이 캐시만) 이다.\
★★★ **tokio 판별** — 이 머신의 `~/.cargo/registry` 에 **tokio 1.52.3 이 캐시돼 있었고 `--offline` 으로 빌드됐다**(맨 위 도구 블록 · (5)). 그래서 「런타임 선택」 한 칸만 tokio 로 쟀다. 나머지는 전부 표준 라이브러리다.\
★★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
★ **속도·메모리·스레드 비용은 재지 않았다.** `unsafe` 코드는 0줄이다(자기 참조 구조체는 **개념 도식 + 명세 인용**으로만 다룬다 — `unsafe` 는 목록의 **56번 주제** 몫).
