# rust/syntax/54 — `async`/`await` 와 `Future` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 던지는 법 — `rustc --edition 2021 <파일>.rs`. 실행기를 쓰는 소스는 **같은 디렉토리에 `r54_exec.rs`** 를 두고 컴파일한다(`mod r54_exec;`). **외부 크레이트를 하나도 쓰지 않는다.**
> ★★★ **future 를 보면 먼저 물어라** — 「**누가 이것을 poll 하나**」와 「**멈춘 동안 무엇을 들고 있어야 하나**」.
> ★ **문항 11개 중 코드가 붙은 예측형은 6개**다. 소스 펜스는 캡처가 실파일에서 찍었다(`check-source-fences.py` 대조).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 부르고, 받고, 버리고 (예측)

```rust
// r54_lazy.rs
async fn f() {
    println!("body of f");
}

fn main() {
    println!("[1] before f()");
    f();
    println!("[2] after f();");
    let _ = f();
    println!("[3] after let _ = f();");
    let fut = f();
    println!("[4] after let fut = f();");
    drop(fut);
    println!("[5] after drop(fut)");
}
```

- 컴파일할 때 경고가 나오는가? 나온다면 **몇 행**에 무엇이라고 나오나? 실행하면 표준 출력에 무엇이 찍히나?

### 2. ★★★ 직접 만든 실행기에 넘기면 (예측)

아래 두 파일을 같은 디렉토리에 두고 `r54_run.rs` 를 컴파일한다.

```rust
// r54_exec.rs
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
```

```rust
// r54_run.rs
mod r54_exec;

async fn f() -> u32 {
    eprintln!("body of f");
    7
}

fn main() {
    let fut = f();
    eprintln!("[1] future created");
    let v = r54_exec::block_on(fut);
    eprintln!("[2] block_on returned {v}");
}
```

- 표준 오류에 찍히는 줄을 순서대로 적어라. `body of f` 는 `[1] future created` 의 앞인가 뒤인가?

### 3. ★★★ 두 번 기다리는 몸통 (예측)

```rust
// r54_poll.rs
mod r54_exec;

use std::future::Future;
use std::pin::Pin;
use std::task::{Context, Poll};

// A leaf future: the first poll returns Pending, the second returns Ready.
struct YieldOnce {
    polled: bool,
    call_waker: bool,
}

impl Future for YieldOnce {
    type Output = ();
    fn poll(mut self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<()> {
        if self.polled {
            eprintln!("    [leaf] Ready");
            return Poll::Ready(());
        }
        self.polled = true;
        if self.call_waker {
            cx.waker().wake_by_ref();
        }
        eprintln!("    [leaf] Pending");
        Poll::Pending
    }
}

async fn two_steps(call_waker: bool) {
    eprintln!("  [body] start");
    YieldOnce { polled: false, call_waker }.await;
    eprintln!("  [body] between the two awaits");
    YieldOnce { polled: false, call_waker }.await;
    eprintln!("  [body] end");
}

fn main() {
    let call_waker = std::env::args().nth(1).as_deref() == Some("wake");
    eprintln!("[main] call_waker = {call_waker}");
    r54_exec::block_on(two_steps(call_waker));
    eprintln!("[main] done");
}
```

- `./r54_poll wake` 로 돌리면 `[exec] poll #…` 은 몇 번까지 가나? `[body] start` 는 몇 번 찍히나? `[exec] waker called` 는 `[leaf] Pending` 의 앞인가 뒤인가?

### 4. ★★★ 벨을 안 울리는 잎 (예측)

- 3번 소스를 **인자 없이** `timeout 2 ./r54_poll` 로 돌리면 표준 오류에 무엇이 찍히고 종료 코드는 얼마인가? 그 뒤에 `[main] done` 은 찍히나?

### 5. ★★★ 1024바이트 배열을 어디에 두나 (예측)

```rust
// r54_size.rs
use std::mem::size_of_val;

async fn tick() {}

fn total(b: &[u8]) -> u32 {
    b.iter().map(|&x| x as u32).sum()
}

async fn a_no_buffer() {
    tick().await;
}

async fn b_used_before_only() {
    let buf = [1u8; 1024];
    let s = total(&buf);
    tick().await;
    println!("{s}");
}

async fn b2_indexed_before_only() {
    let buf = [1u8; 1024];
    let s = buf[0] as u32 + buf[1023] as u32;
    tick().await;
    println!("{s}");
}

async fn c_inner_block_before() {
    let s = {
        let buf = [1u8; 1024];
        total(&buf)
    };
    tick().await;
    println!("{s}");
}

async fn d_used_after() {
    let buf = [1u8; 1024];
    tick().await;
    println!("{}", total(&buf));
}

async fn e_created_after() {
    tick().await;
    let buf = [1u8; 1024];
    println!("{}", total(&buf));
}

async fn f_two_buffers_two_awaits() {
    let a = [1u8; 1024];
    tick().await;
    println!("{}", total(&a));
    let b = [2u8; 1024];
    tick().await;
    println!("{}", total(&b));
}

async fn g_two_buffers_one_await() {
    let a = [1u8; 1024];
    let b = [2u8; 1024];
    tick().await;
    println!("{}", total(&a) + total(&b));
}

async fn h_two_buffers_two_blocks() {
    {
        let a = [1u8; 1024];
        tick().await;
        println!("{}", total(&a));
    }
    {
        let b = [2u8; 1024];
        tick().await;
        println!("{}", total(&b));
    }
}

fn main() {
    println!("tick                      {:>5}", size_of_val(&tick()));
    println!("a_no_buffer               {:>5}", size_of_val(&a_no_buffer()));
    println!("b_used_before_only        {:>5}", size_of_val(&b_used_before_only()));
    println!("b2_indexed_before_only    {:>5}", size_of_val(&b2_indexed_before_only()));
    println!("c_inner_block_before      {:>5}", size_of_val(&c_inner_block_before()));
    println!("d_used_after              {:>5}", size_of_val(&d_used_after()));
    println!("e_created_after           {:>5}", size_of_val(&e_created_after()));
    println!("f_two_buffers_two_awaits  {:>5}", size_of_val(&f_two_buffers_two_awaits()));
    println!("g_two_buffers_one_await   {:>5}", size_of_val(&g_two_buffers_one_await()));
    println!("h_two_buffers_two_blocks  {:>5}", size_of_val(&h_two_buffers_two_blocks()));
    println!("type: {}", std::any::type_name_of_val(&a_no_buffer()));
}
```

- 열 줄의 숫자 중 **1024 를 넘는 것은 어느 행**인가? `b_used_before_only` 와 `b2_indexed_before_only` 는 같은가? `f_two_buffers_two_awaits` 와 `h_two_buffers_two_blocks` 는?

### 6. ★★ 최적화를 켜면 (경계)

- 5번을 `-C opt-level=3` 으로 다시 빌드하면 숫자가 바뀌나? 「await 너머로 살아 있어야 할 값은 future 안에 있다」와 「빌린 적이 있는 지역 변수는 스코프 끝까지 담는다」 — 각각 언어가 보장하나, rustc 가 이 판에서 그렇게 한 것인가?

### 7. ★★ `Waker` 를 만지는 쪽 (왜)

- 3번에서 `two_steps` 의 몸통에는 `Waker` 가 한 글자도 없는데도 깨우기가 돌아간다. 누가 `Waker` 를 만지고, `.await` 는 받은 `Context` 를 어떻게 하나?

### 8. ★★ 두 번째 poll 은 어디서 시작하나 (왜)

- 3번의 두 번째 poll 이 `[body] start` 를 다시 찍지 않는 이유를 「상태 기계」로 설명하라. Reference 의 Await expressions 는 `Pending` 뒤를 어떻게 적나?

### 9. ★★ 네 언어의 「부른 순간」 (연결)

- [Python 51번](../../../python/syntax/51-asyncio-coroutine-basics/) · [JS 39번](../../../js/syntax/39-async-await/) · [Kotlin 52번](../../../kotlin/syntax/52-coroutine-basics-suspend-scope-launch-async/)은 「부르기만 하면 몸통이 도나」를 각각 무엇으로 쟀나? Rust 는 어느 언어와 같은 편이고, **같은 편 안에서 갈리는 칸**은 무엇인가?

### 10. ★★ 이터레이터의 게으름과 (연결)

- [36번 주제](../36-iterator-adapters-laziness-and-collect/) (3)의 `#[must_use]` 경고 문구와 1번의 경고 문구를 나란히 적어라. `let _ =` 를 붙였을 때 두 주제에서 공통으로 일어나는 일은?

### 11. ★★ 버리는 시점이 다른 두 future (예측)

```rust
// r54_cancel.rs
use std::future::Future;
use std::pin::{pin, Pin};
use std::task::{Context, Poll, Waker};

struct Noisy(&'static str);

impl Drop for Noisy {
    fn drop(&mut self) {
        eprintln!("  drop {}", self.0);
    }
}

struct NeverReady;

impl Future for NeverReady {
    type Output = ();
    fn poll(self: Pin<&mut Self>, _cx: &mut Context<'_>) -> Poll<()> {
        Poll::Pending
    }
}

async fn job(tag: &'static str) {
    let _held = Noisy(tag);
    eprintln!("  body of {tag} started");
    NeverReady.await;
    eprintln!("  body of {tag} finished");
}

fn main() {
    let mut cx = Context::from_waker(Waker::noop());

    eprintln!("[1] never polled");
    let a = job("a");
    drop(a);

    eprintln!("[2] polled once, then dropped");
    {
        let mut b = pin!(job("b"));
        let r = b.as_mut().poll(&mut cx);
        eprintln!("  poll returned {:?}", r);
    }
    eprintln!("[3] end of main");
}
```

- 표준 오류에 찍히는 줄을 순서대로 적어라. `drop a` 와 `drop b` 는 각각 찍히나 — 찍힌다면 어디서?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
