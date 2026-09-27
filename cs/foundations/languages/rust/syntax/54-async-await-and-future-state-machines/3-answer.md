# rust/syntax/54 — `async`/`await` 와 `Future` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·경고는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서
> **`rustc --edition 2021`** 로(크기 표만 `-C opt-level=3` 판을 하나 더) 실제로 돌려 받은 것이다.\
> ★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
> ★★ 블록 첫 줄 `===== 소스: <파일> =====` 아래가 **돌린 소스 전문**이고, **진단의 줄 번호는 그 파일 기준**이다. 실행기(`r54_exec.rs`)를 쓰는 블록은 그 파일도 배너째 함께 실렸다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 경고는 7행 `f();` 하나 · 표준 출력에 `body of f` 는 0줄

**출력**

```text
===== 소스: r54_lazy.rs =====
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
===== rustc --edition 2021 r54_lazy.rs =====
warning: unused implementer of `Future` that must be used
 --> r54_lazy.rs:7:5
  |
7 |     f();
  |     ^^^
  |
  = note: futures do nothing unless you `.await` or poll them
  = note: `#[warn(unused_must_use)]` (part of `#[warn(unused)]`) on by default

warning: 1 warning emitted

(exit 0)
===== ./r54_lazy =====
[1] before f()
[2] after f();
[3] after let _ = f();
[4] after let fut = f();
[5] after drop(fut)
(exit 0)
```

**왜 그런가**

- ★★★ Reference — 「**Async functions do no work when called: instead, they capture their arguments into a future.**」 네 번 불렀지만 네 번 다 **future 값을 만들기만** 했다.
- ★★ **경고는 결과를 버린 식 문장 `f();` 에만** — `Future` 의 `#[must_use]`. `let _ = f();` · `let fut = f();` 는 **값을 받았으니** 경고가 없다. 경고의 유무는 「돌았나」와 **상관이 없다.**
- ★ `drop(fut)` 뒤에도 아무 줄이 없다 — 시작하지 않은 계산은 버려도 흔적이 없다.

### 2. ★★★ `[1] future created` → `poll #1` → `body of f` → `Ready` → `[2] block_on returned 7`

**출력**

```text
===== rustc --edition 2021 r54_run.rs =====
(exit 0)
===== ./r54_run =====
[1] future created
  [exec] poll #1
body of f
  [exec] poll #1 returned Ready
[2] block_on returned 7
(exit 0)
```

**왜 그런가**

- ★★★ `let fut = f();` 에서는 몸통이 안 돌고, **`block_on` 의 첫 `poll` 안에서** 돈다. 그래서 `body of f` 는 `[1]` **뒤**, `poll #1` 과 `returned Ready` **사이**다.
- ★★ `f` 는 기다릴 것이 없어 **첫 poll 에 끝까지** 간다 — `Pending` 이 한 번도 없다.

### 3. ★★★ poll 은 `#3` 까지 · `[body] start` 는 한 번 · `waker called` 가 `[leaf] Pending` 보다 먼저

**출력**

```text
===== rustc --edition 2021 r54_poll.rs =====
(exit 0)
===== ./r54_poll wake =====
[main] call_waker = true
  [exec] poll #1
  [body] start
  [exec] waker called
    [leaf] Pending
  [exec] poll #1 returned Pending -- park
  [exec] poll #2
    [leaf] Ready
  [body] between the two awaits
  [exec] waker called
    [leaf] Pending
  [exec] poll #2 returned Pending -- park
  [exec] poll #3
    [leaf] Ready
  [body] end
  [exec] poll #3 returned Ready
[main] done
(exit 0)
```

**왜 그런가**

- ★★★ **멈출 자리(await)가 둘 → poll 셋.** 각 멈춤 뒤에 한 번씩 더 불렸다.
- ★★★ **`[body] start` 한 번** — 두 번째·세 번째 poll 은 **멈춘 자리부터** 이어 갔다(8번).
- ★★ **잎이 `Pending` 을 돌려주기 전에 깨웠다** — 그래서 `waker called` 가 먼저다. `park` 는 먼저 놓인 토큰 덕에 바로 돌아온다(std `thread::park`).

### 4. ★★★ `poll #1 returned Pending -- park` 에서 멈춤 · `exit 124` · `[main] done` 없음

**출력**

```text
===== 소스: r54_poll.rs =====
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
===== rustc --edition 2021 r54_poll.rs =====
(exit 0)
===== timeout 2 ./r54_poll =====
[main] call_waker = false
  [exec] poll #1
  [body] start
    [leaf] Pending
  [exec] poll #1 returned Pending -- park
(exit 124)
```

**왜 그런가**

- ★★★ **잎이 `Pending` 을 돌려주면서 아무도 깨우지 않았다** → 실행기는 `park` 에서 영원히 잔다 → `timeout 2` 가 죽였다(`124`).
- ★★ std `Future::poll` — 실행기는 「future 가 `wake()` 로 준비됐다고 알릴 때만」 poll 한다. **깨우지 않은 쪽의 버그**이고, 에러도 경고도 없다.

### 5. ★★★ 1024 를 넘는 행 — `b` 1032 · `d` 1026 · `f` 2050 · `g` 2050 · `h` 1026

**출력**

```text
===== 소스: r54_size.rs =====
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
===== rustc --edition 2021 r54_size.rs =====
(exit 0)
===== ./r54_size =====
tick                          1
a_no_buffer                   2
b_used_before_only         1032
b2_indexed_before_only        8
c_inner_block_before          8
d_used_after               1026
e_created_after               2
f_two_buffers_two_awaits   2050
g_two_buffers_one_await    2050
h_two_buffers_two_blocks   1026
type: r54_size::a_no_buffer::{{closure}}
(exit 0)
```

**왜 그런가**

- ★★★ **`d`(await 뒤에서 씀) 1026 · `e`(await 뒤에서 만듦) 2** — 멈춘 동안 살아 있어야 하는 값만 future 에 들어간다.
- ★★★ **`b` 1032 대 `b2` 8** — 둘 다 await 앞에서만 썼는데, **`&buf` 로 빌린 `b` 만** 들어갔다. **`c` 8** — 빌렸어도 안쪽 블록에서 끝내면 안 들어간다.
- ★★ **`f` 2050 대 `h` 1026** — `f` 는 `a` 가 함수 끝까지 스코프에 있어 **두 await 를 다** 가로질렀다. `h` 는 두 배열을 **서로 다른 블록**에 가둬 한 자리를 나눠 썼다.

### 6. ★★ 한 글자도 안 바뀐다 · 앞은 의미상 필연, 뒤는 rustc 의 이 판

**출력**

```text
===== 소스: r54_size.rs =====
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
===== rustc --edition 2021 -C opt-level=3 -o r54_size_o r54_size.rs =====
(exit 0)
===== ./r54_size_o =====
tick                          1
a_no_buffer                   2
b_used_before_only         1032
b2_indexed_before_only        8
c_inner_block_before          8
d_used_after               1026
e_created_after               2
f_two_buffers_two_awaits   2050
g_two_buffers_one_await    2050
h_two_buffers_two_blocks   1026
type: r54_size::a_no_buffer::{{closure}}
(exit 0)
```

**왜 그런가**

- ★★★ **디버그 판과 같다** — 상태 기계에 **무엇을 담나**는 최적화가 아니라 **그 전의 분석**이 정한다(규칙 24 — 2판 격자).
- ★★ **「await 너머로 살아 있어야 할 값은 future 안에」** — 멈춘 동안 스택 프레임이 없으니 **그렇지 않으면 성립할 수 없다**(의미상 필연). **「빌린 적이 있으면 스코프 끝까지」·「두 자리가 칸을 나눠 쓴다」·바이트 수** — Reference 는 크기를 말하지 않는다. **rustc 1.92 의 관찰**이고 판이 오르면 다시 찍을 칸이다.

### 7. ★★ 잎(`YieldOnce::poll`)만 만진다 · `.await` 는 받은 `Context` 를 그대로 넘긴다

- ★★★ 실행기가 만든 `Context` 가 **바깥 future(`two_steps`)의 poll** 로 들어가고, 몸통의 `.await` 가 **같은 `Context` 로 잎을 poll** 한다. Reference — Await expressions: 「This pinned future is then polled by calling the `Future::poll` method and **passing it the current task context**」.
- ★★ 그래서 `async fn` 을 쓰는 쪽은 `Waker` 를 볼 일이 없다 — **`Waker` 는 기다림이 실제로 생기는 곳(잎 · 입출력 · 타이머)** 의 몫이다.

### 8. ★★ 멈춘 상태를 저장해 두었다가 그 자리로 돌아온다

- ★★★ `async fn` 의 future 는 **「몇 번째 await 에서 멈췄나」와 그때 필요한 지역 변수**를 담은 상태 기계다(5번의 크기가 그 흔적). 다음 poll 은 그 상태를 보고 **멈춘 await 로 곧장** 간다.
- ★★ Reference — `Pending` 이면 「the future returns `Poll::Pending`, **suspending its state** so that, when the surrounding async context is re-polled, execution returns to step 3」(3단계 = 안쪽 future 를 poll 하는 자리).

### 9. ★★ Rust 는 Python 편 — 둘 다 몸통 0줄 · 갈리는 칸은 「버린 것을 누가 알리나」

| 언어 | 부르기만 하면 | 어떻게 쟀나 |
|---|---|---|
| Rust | future 만 — **몸통 0줄** | 이 편 1번 — 표준 출력 줄 |
| Python | 코루틴 객체만 — **몸통 0줄** | Python 51 (1) — 표준 출력 줄 + 표준 오류의 `never awaited` |
| JavaScript | **첫 `await` 까지 지금 돈다** | JS 39 (9) — 같은 탐침을 Python 과 나란히 |
| Kotlin | 일반 함수에서는 **못 부른다**(컴파일 에러) · 코루틴 안에서는 보통 호출 | Kotlin 52 (2) 호출 격자 · (4) 순서 로그 |

- ★★★ **같은 편 안에서 갈리는 칸** — Rust 는 **컴파일러**가 버린 식 문장을 경고하고 실행 중에는 말이 없다. Python 은 **런타임**이 버려지는 순간 `RuntimeWarning` 을 낸다.

### 10. ★★ 「futures do nothing unless you `.await` or poll them」 대 「iterators are lazy and do nothing unless consumed」 — `let _ =` 는 경고만 끈다

- ★★ 두 경고 모두 **트레이트에 붙은 `#[must_use]`** 에서 온다. **`let _ =` 를 붙이면 경고가 사라지고, 여전히 아무 일도 안 한다** — 36번 (3)은 이터레이터로, 이 편 1번은 future 로 쟀다(9행).

### 11. ★★ `drop a` 는 없다 · `drop b` 는 `poll returned Pending` 뒤, `[3]` 앞

**출력**

```text
===== 소스: r54_cancel.rs =====
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
===== rustc --edition 2021 r54_cancel.rs =====
(exit 0)
===== ./r54_cancel =====
[1] never polled
[2] polled once, then dropped
  body of b started
  poll returned Pending
  drop b
[3] end of main
(exit 0)
```

**왜 그런가**

- ★★★ **`a` — 한 번도 poll 안 된 future.** 몸통이 안 돌았으니 `Noisy("a")` 는 **만들어진 적도 없다** → 버려도 `drop a` 가 없다. future 가 들고 있던 것은 **인자(`tag`)뿐**이었다(Reference: 「capture their arguments into a future」).
- ★★★ **`b` — 한 번 poll 되어 멈춘 future.** 몸통이 `_held` 를 만들고 `NeverReady.await` 에서 멈췄다 → 상태 기계가 `_held` 를 **들고 있다**(서머리 (4)의 크기와 같은 이유) → 블록 끝에서 future 가 버려지며 **`drop b` 가 돈다.** `body of b finished` 는 영영 안 찍힌다.
- ★★ 이것이 Rust async 의 **취소**다 — 「future 를 버리면 멈춘 자리에서 끝나고, 들고 있던 값이 정리된다」. 해제 순서 규칙은 [44번 주제](../44-drop-mem-drop-replace-and-take/)의 것이 그대로 적용된다.
- ★ `Waker::noop()`(1.85.0)는 「아무 일도 안 하는 `Waker`」다 — 한 번만 poll 할 것이라 깨울 필요가 없다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서·서머리의 **모든 블록** | `capture.sh` — 블록마다 명령을 배너에 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` 기본 규칙 넷 · **고칠 것 0** |
| ★★★ **게으름** | `r54_lazy` — 네 가지로 부르고 버림 | 1 | 경고 **1개(7행)** · `body of f` **0줄** |
| 실행기 | `r54_exec.rs` + `r54_run` | 1 | `poll #1` 안에서 몸통 · `7` |
| ★★★ **poll 횟수** | `r54_poll wake` · `timeout 2 ./r54_poll` | 2 | poll **3** · 멈춤 **`124`** |
| ★★★ **크기 격자** | `r54_size` × (디버그 · `-O3`) | 2판 × 10행 | **두 판 동일** · 1024 초과 **5 / 10** 행 |
| ★ **이미 잰 것 — 다시 안 돌림** | Python 51 · JS 39 · Kotlin 52 · Rust 36 | — | 각 편의 블록 |
| 취소 | `r54_cancel` — 안 poll 한 것 · 한 번 poll 한 것을 버림 | 1 | `drop a` **없음** · `drop b` **있음** |
| **안 던진 것** — 재귀 `async fn` · `-Zprint-type-sizes`(nightly) · 시간·메모리 | — | 0 | ★ 「안 던졌다 / 못 잰 것」으로 표시했다 |

**구현 의존 항목**(버전·환경이 바뀌면 **다시 찍어야 하는** 것).

| 항목 | 왜 |
|---|---|
| `size_of_val` 의 바이트 수 · 「빌린 지역 변수는 스코프 끝까지」 | ★ rustc 의 상태 기계 분석·배치 — 언어는 크기를 약속하지 않는다 |
| `type_name_of_val` 의 `{{closure}}` 문자열 | ★ std 가 「exact output is not guaranteed」라고 적는다 |
| 경고 문구 · 린트 이름 | ★ rustc 판에 매인다 |

★ **다시 찍는 법** — `capture.sh <새 디렉토리>` 를 그대로 돌리고 `normalize-shaky.py <원본> <새 디렉토리>` 로 견준다.
