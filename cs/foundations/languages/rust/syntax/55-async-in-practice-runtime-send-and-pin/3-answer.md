# rust/syntax/55 — async 실전: 런타임 선택 · `Send` 경계 · `Pin` 맛보기 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `cargo 1.92.0` · `x86_64-unknown-linux-gnu`** 에서 실제로 돌려 받은 것이다.
> 표준 라이브러리만 쓰는 블록은 `rustc --edition 2021`, tokio 블록은 **로컬 캐시의 tokio 1.52.3 을 `--offline`** 으로.\
> ★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
> ★★ 블록 첫 줄 `===== 소스: <파일> =====` 아래가 **돌린 소스 전문**이고, **진단의 줄 번호는 그 파일 기준**이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ E0728 — `fn main`(「this is not `async`」)과 `.await`(6행)

**출력**

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

**왜 그런가**

- ★★★ Reference — 「Await expressions are legal only within an async context」. 보통 함수에는 멈췄다 이어 갈 **상태 기계가 없다**(54번 (3)).

### 2. ★★★ E0752 — 1번과 다른 번호

**출력**

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

**왜 그런가**

- ★★★ `main` 의 future 를 **poll 할 실행기가 표준에 없다.** 런타임 매크로(`#[tokio::main]`)가 `async fn main` 을 `fn main` + `block_on` 으로 바꿔 이 자리를 채운다(서머리 (1)의 tokio-macros 주석).

### 3. ★★★ 번호 없는 `error:` · 9행 「has type `Rc<i32>` which is not `Send`」 · 10행 「await occurs here, with `r` maybe used later」

**출력**

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

**왜 그런가**

- ★★★ **에러 번호가 없다** — 같은 `Send` 실패라도 스레드([41번](../41-rc-arc-shared-ownership-and-weak-cycles/) (3))는 E0277 인데, future 는 rustc 가 **전용 문구**로 낸다.
- ★★★ 사슬 — `help:`(무엇이 `!Send` 인가) → `note:`(어느 변수가 · 어느 await 를 가로질렀나) → `note:`(누가 `Send` 를 요구했나 — `need_send` 의 경계).

### 4. ★★★ `r55_send_rc_drop.rs` 는 에러(`read_then_drop`) · `r55_send_rc_ok.rs` 는 통과

**출력**

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

**왜 그런가**

- ★★★ **`read_then_drop` 은 10행 `*r` 로 `r` 을 빌렸다** — 빌린 적이 있는 지역 변수는 `drop` 뒤에도 **await 너머로 살아 있을 수 있다**고 판정됐다. 진단이 `...` 로 10\~11행을 건너뛰고 9행 `let r` 과 12행 `.await` 를 짚는다.
- ★★ **`drop_without_reading`(빌린 적 없음) · `read_in_inner_block`(스코프가 await 앞에서 닫힘)은 통과.** 처방은 **안쪽 블록**이다.

### 5. ★★★ `ok` 하나만 통과 · 가드 타입은 `std::sync::MutexGuard<'_, u32>`

**출력**

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

**왜 그런가**

- ★★★ **`*g += 1` 이 `g` 를 빌렸다**(`DerefMut`) — 그래서 `drop(g)` 판도 4번의 `read_then_drop` 과 같은 이유로 에러다. **가드는 쓰려고 잡는 것**이라 「빌리지 않고 `drop`」은 쓸모가 없다 — 블록에 가둔다.

### 6. ★★ 앞은 E0277 「cannot be unpinned」(처방 `pin!` · `Box::pin`) · 뒤는 통과 — `7` · `3`

**출력**

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

```text
===== 소스: r55_boxpin.rs =====
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
===== 소스: r54_exec.rs =====
// The smallest executor: poll once, park the thread until the waker unparks it, poll again.
use std::future::Future;
use std::pin::pin;
use std::sync::Arc;
use std::task::{Context, Poll, Wake, Waker};
use std::thread::{self, Thread};

struct ThreadWaker(Thread);

impl Wake for ThreadWaker {
    fn wake(self: Arc<Self>) {
        self.wake_by_ref();
    }
    fn wake_by_ref(self: &Arc<Self>) {
        eprintln!("  [exec] waker called");
        self.0.unpark();
    }
}

pub fn block_on<F: Future>(fut: F) -> F::Output {
    let mut fut = pin!(fut);
    let waker = Waker::from(Arc::new(ThreadWaker(thread::current())));
    let mut cx = Context::from_waker(&waker);
    let mut n = 0;
    loop {
        n += 1;
        eprintln!("  [exec] poll #{n}");
        match fut.as_mut().poll(&mut cx) {
            Poll::Ready(v) => {
                eprintln!("  [exec] poll #{n} returned Ready");
                return v;
            }
            Poll::Pending => {
                eprintln!("  [exec] poll #{n} returned Pending -- park");
                thread::park();
            }
        }
    }
}
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

**왜 그런가**

- ★★★ `async fn` 이 만든 타입은 **`Unpin` 이 아니다** — 빌리는 것 하나 없는 `f` 인데도 그렇다(자기 참조일 **수 있는** 상태 기계 전부에서 뺀다).
- ★★ **`Pin<Box<dyn Future<Output = u32>>>` 는 `Unpin` 이다** — 옮겨지는 것은 **상자(포인터)** 뿐이고 future 는 힙 그 자리에 있다. 그래서 `need_unpin(&jobs[0])` 이 통과하고, 타입이 다른 두 future 가 한 `Vec` 에 들어간다.

### 7. ★★ 양식(`Future`·`IntoFuture`·`Poll`) · 벨(`Context`·`Waker`·`Wake`·`RawWaker`·`RawWakerVTable`) · 작은 future(`ready`·`pending`·`poll_fn`) — 없는 것은 「돌리는 쪽」

- ★★★ **없는 것** — `block_on` · 작업 생성(`spawn`) · 실행 대기열 · 타이머·입출력 반응기. **poll 을 부를 주체가 없다.**
- ★★ 그래서 **`fn main` 은 `.await` 할 수 없고(1번 — 상태 기계가 없다) `main` 은 `async` 일 수 없다(2번 — poll 할 사람이 없다).** 둘은 같은 사실의 두 얼굴이다.
- ★ `join!`·`LocalWaker`·`ContextBuilder` 는 **nightly-only** 였다(목록의 셋째 칸).

### 8. ★★ pthread 는 「잠근 스레드에서 풀어야 한다」 — 가드가 옮겨 가면 다른 스레드에서 풀린다

- ★★★ std — 「A `MutexGuard` is not `Send` to maximize platform portability. **On platforms that use POSIX threads … there is a requirement to release mutex locks on the same thread they were acquired.**」
- ★★ 멀티스레드 런타임은 `Pending` 에서 멈춘 작업을 **다음에는 다른 워커가 poll** 할 수 있다. 가드가 future 의 필드로 들어가 있으면 **다른 스레드에서 `drop`(=풀기)** 될 수 있다 — 그래서 `!Send` 이고, 5번의 에러가 된다.

### 9. ★★ 교착의 구조 — 처방은 「await 전에 놓기」와 「비동기 락」 · 재현은 하지 않았다

- ★★ `std::sync::Mutex::lock` 은 **스레드를 막는** 호출이다. 작업 A 가 가드를 쥔 채 `Pending` 으로 스레드를 내주고, 같은 스레드의 작업 B 가 `lock()` 에서 **스레드를 막으면** A 는 다시 poll 될 수 없어 가드를 못 놓는다(서머리 (3)의 개념 도식).
- ★★ **처방** — ① 가드를 **블록에 가둬 await 전에 놓는다**(5번의 `ok` — `Send` 문제도 같이 풀린다) ② 꼭 쥐어야 하면 **`tokio::sync::Mutex`**(`lock().await` 로 기다리며 스레드를 내준다 — 10번 블록의 `async mutex : 2`).
- ★ **재현하지 않았다** — 교착은 판마다 안 날 수도 있고(안 터졌다 ≠ 안전하다), 같은 질문을 컴파일러가 **`Send` 판에서는** 판마다 같게 답한다(제5의 상태).

### 10. ★★ `{"main"}` 대 `{"tokio-rt-worker"}` · `spawn` 은 `Send + 'static`, `spawn_local` 은 `Send` 불요 · `current_thread` 에서도 요구한다

**출력**

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

**왜 그런가**

- ★★★ `current_thread` 는 `block_on` 을 부른 스레드(`main`)에서, `multi_thread` 는 **워커 스레드들**에서 작업이 돌았다.
- ★★★ **`tokio::spawn` 의 경계는 서명이다** — `F: Future + Send + 'static`(에러가 tokio 소스 `spawn.rs:176:21` 을 짚는다). `rc_spawn_ct.rs`(`current_thread`)도 **같은 자리에서** 막혔다. `spawn_local` 은 작업을 그 스레드에 묶는 대신 `Send` 를 안 요구해 `Rc` 작업이 `5` 를 냈다.

### 11. ★★ 자기 참조 상태 기계 — 옮기면 포인터가 옛 주소를 가리킨다 · 상자는 옮겨도 알맹이는 그 자리

- ★★★ std `pin` — 「A key example of such self-referential types are **the state machines generated by the compiler to implement `Future` for async fns**.」 · 「But if that value is moved, the pointer will still point to the **old address** … thus becoming invalid.」
- ★★ await 너머로 **버퍼와 그 버퍼를 빌린 참조가 함께** 살면 future 안의 필드가 같은 future 안을 가리킨다(서머리 (4)의 도식). 한 번 poll 한 뒤 옮기면 그 참조가 깨진다 — 그래서 **poll 은 고정된 것(`Pin<&mut Self>`)만** 받는다.
- ★★ **`Pin<Box<T>>`** 를 옮기면 **포인터만** 옮겨지고 `T` 는 힙 그 자리에 있다 — 그래서 `Unpin` 이다(6번).

### 12. ★★ 같은 분석 — 「빌린 적이 있으면 스코프 끝까지 살아 있다」 · 언어 보장이 아니라 rustc 의 판정

- ★★★ 54번 `b` 는 `&buf` 로 빌린 배열이 await 앞에서만 쓰였는데도 **future 안에 남았다**(1032). 4번 `read_then_drop` 은 `*r` 로 빌린 `Rc` 가 `drop` 됐는데도 **await 너머로 살아 있다고** 판정됐다. **한쪽은 크기로, 한쪽은 `Send` 로 드러난 같은 판정**이다.
- ★★ Reference 는 이 판정의 세부를 정하지 않는다 — **rustc 1.92 의 관찰**이고, 판이 오르면 분석이 정교해져 **4번의 `drop` 판이 통과로 바뀔 수 있는 칸**이다(다시 찍을 것).

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서·서머리의 **모든 블록** | `capture.sh` — 블록마다 명령을 배너에 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` 기본 규칙 넷 · **고칠 것 0** |
| 실행기 없음 | `r55_await_in_main` · `r55_async_main` · `r55_std_task`(로컬 문서 목록) | 3 | **E0728** · **E0752** · 실행기 항목 0 |
| ★★★ **`Send` 경계** | `r55_send_rc` · `_drop` · `_ok` · `r55_send_guard` · `_drop` · `_ok` | 6 | 에러 **4** · 통과 **2**(둘 다 「빌린 적 없음」 또는 「블록」) |
| `Pin` | `r55_unpin` · `r55_boxpin` · `r55_pin_doc` | 3 | **E0277** · `7`/`3` · 서명·명세 인용 |
| ★★ **tokio 판별 + 런타임** | 캐시 목록 · `cargo tree --offline` · `flavors` · `rc_spawn` · `rc_spawn_ct` | 5 | **1.52.3 `--offline` 빌드 성공** · 스레드 집합 2 · `Send` 에러 2 |
| **안 던진 것** — 교착 재현 · 자기 참조를 옮기는 `unsafe` 실험 · `spawn` 의 `'static` 에러 · 시간 | — | 0 | ★ 「일부러 안 했다 / 안 던졌다」로 표시했다 |

**구현 의존 항목**(버전·환경이 바뀌면 **다시 찍어야 하는** 것).

| 항목 | 왜 |
|---|---|
| 「빌린 뒤 `drop` 해도 await 너머로 산다」는 판정 | ★ rustc 의 분석 — 판이 오르면 바뀔 수 있다 |
| future `Send` 실패에 번호가 없는 문구 | ★ rustc 의 진단 |
| tokio 의 `Send + 'static` 경계 · `tokio-rt-worker` 이름 · `#[tokio::main]` 의 기본 `multi_thread` | ★ tokio 1.52.3 · tokio-macros 2.7.2 |
| 캐시에 있는 tokio 판 | ★ 이 머신의 `~/.cargo/registry` — 다른 머신에서는 `--offline` 이 실패할 수 있다 |

★ **다시 찍는 법** — `capture.sh <새 디렉토리>` 를 그대로 돌리고 `normalize-shaky.py <원본> <새 디렉토리>` 로 견준다.
