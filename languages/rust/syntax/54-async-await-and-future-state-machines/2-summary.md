# rust/syntax/54 — `async`/`await` 와 `Future` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Reference — Async functions](https://doc.rust-lang.org/reference/items/functions.html#async-functions)(「Async functions do no work when called: instead, they capture their arguments into a future」) ·
> [Reference — Await expressions](https://doc.rust-lang.org/reference/expressions/await-expr.html)(`poll` 이 `Pending` 이면 「그 future 도 `Pending` 을 돌려주며 상태를 멈춰 둔다」) ·
> [std — `Future`](https://doc.rust-lang.org/std/future/trait.Future.html)(§Runtime characteristics 「Futures alone are inert; they must be actively polled」) ·
> [std — `task::Wake`](https://doc.rust-lang.org/std/task/trait.Wake.html) · [std — `pin`](https://doc.rust-lang.org/std/pin/index.html).
> ★ 전부 **이 머신의 `rust-docs`(1.92.0) 로컬 사본**을 열어 읽었다.
> **실행 검증** — 이 문서의 모든 출력·경고는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서
> **`rustc --edition 2021 <파일>.rs`** 로 돌려 받은 것이다(크기 표만 `-C opt-level=3` 판을 하나 더).\
> ★★★ **외부 크레이트를 하나도 쓰지 않았다** — 실행기는 표준 라이브러리만으로 직접 썼다(`Wake` 트레이트 · `thread::park` · `unsafe` 0줄).\
> ★★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다. 소스 펜스도 캡처가 찍었다.\
> ★ **속도·메모리 사용량은 재지 않았다** — 「async 가 스레드보다 가볍다」 같은 주장은 이 문서에 없다. 잰 것은 **future 값 하나의 바이트 크기**(`size_of_val`)뿐이다.
> **버전** — `async`/`await` 는 **1.39.0**(에디션 2018 부터 — Reference: 「Async functions are only available beginning with Rust 2018」) · `Wake` 트레이트 **1.51.0** · `std::pin::pin!` **1.68.0** · `type_name_of_val` **1.76.0** · `Waker::noop` **1.85.0**(모두 로컬 std 문서의 「Stable since」).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

★★★ **본체 창 — ① 게으름 로그(「몸통이 찍는 줄이 있나」)와 ② 상태 기계 크기 격자(`size_of_val`)다.** 「future 는 상태 기계다」는 **바이트 수가 await 너머의 지역 변수를 따라 움직이는 것**으로 본다 — 컴파일러가 만든 타입을 직접 열어 볼 도구가 이 판(stable)에 없기 때문이다.

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| 안 흔들린다 | ★★★ **게으름 로그** — 몸통이 찍는 줄의 **있음·없음과 순서** | 언어가 정한다(Reference — Async functions) · 마커는 전부 **표준 오류**로 찍어 순서를 고정했다(규칙 18) |
| 안 흔들린다 | ★★★ **poll 횟수 로그** · `timeout` 의 종료 코드 `124` | 실행기가 결정적이다(스레드 하나 · 깨우는 쪽이 자기 자신) |
| ★ **구현이 정한다(재현은 된다)** | ★★ **`size_of_val` 의 바이트 수** | 상태 기계 **배치는 rustc 가 정한다** — 언어는 크기를 약속하지 않는다. 이 판에서 **디버그·`-O3` 두 판이 한 글자도 같았다** |
| ★ **구현이 정한다** | `type_name_of_val` 의 문자열 `…::{{closure}}` | std 문서가 「형식은 보장하지 않는다」고 적는 함수다 |

★ 정규화 규칙은 **기본 넷**만 쓴다. 이 편의 블록에는 걸리는 칸이 없었다(재대조 전부 동일).

## 한눈에 — 쉽게 말하면

**`async fn` 을 부르는 것은 「요리를 시작하는 것」이 아니라 「주문서를 한 장 쓰는 것」이다.**
주문서(future)는 쓰기만 하면 주방에서 아무 일도 안 일어난다. **누군가 그 주문서를 들고 주방에 「다 됐어?」라고 물어야(`poll`)** 요리가 한 단계씩 나아간다.
요리가 중간에 기다려야 하면(`Pending`) 주방은 **「다 되면 벨을 울릴게(`Waker`)」** 라고 하고 손을 뗀다. 벨이 울려야 다시 묻는다.
주문서에는 **「몇 번째 단계까지 했나」와 「그때 도마 위에 있던 재료」** 가 적혀 있다 — 기다리는 동안에도 남아 있어야 하는 것만. 그래서 **도마 위에 큰 재료를 올려 둔 채 기다리면 주문서가 두꺼워진다.**

| 비유 | 실체 |
|---|---|
| 「**주문서를 쓴다**」 | ★★★ **`f()` — future 값을 만든다. 몸통은 0줄 돈다**((1)) |
| 「**써 놓고 버린 주문서**」 | ★★ **`#[must_use]` 경고 — 「futures do nothing unless you `.await` or poll them」**((1)) |
| 「**다 됐어? 하고 묻는 사람**」 | ★★★ **실행기(executor)가 `poll` 을 부른다** — 표준 라이브러리에는 이 사람이 없다(55번)((2)) |
| 「**다 되면 벨을 울릴게**」 | ★★★ **`Poll::Pending` + `cx.waker().wake()`** — 벨이 안 울리면 **다시는 안 묻는다**((3)) |
| 「**몇 번째 단계**」 | ★★ **상태 기계의 현재 상태** — `await` 한 자리마다 하나((3)·(4)) |
| 「**기다리는 동안 도마 위에 남은 재료**」 | ★★★ **await 를 가로질러 살아 있는 지역 변수** — future 의 크기에 들어간다((4)) |

```text
   async fn two_steps() {            ─ 컴파일러가 만드는 것 (개념 그림 — 실제 배치는 rustc 가 정한다)
       A;                               enum 상태 {
       leaf1.await;   ── 멈출 자리 ①        처음부터,
       B;                                   ①에서 멈춤 { leaf1, ①너머로 살아 있는 지역 변수 },
       leaf2.await;   ── 멈출 자리 ②        ②에서 멈춤 { leaf2, ②너머로 살아 있는 지역 변수 },
       C;                                   끝남,
   }                                    }
                                        poll 한 번 = 지금 상태에서 다음 멈출 자리(또는 끝)까지 달린다
```

> **future** — 「나중에 값이 되는 계산」을 담은 값. `Future` 트레이트를 구현하고, **누가 `poll` 해야만** 나아간다.\
> 예: `let fut = f();` 의 `fut`. 이 줄에서 `f` 의 몸통은 한 줄도 안 돌았다.

> **poll** — future 에게 「한 단계 나아가 봐」라고 묻는 호출. 답은 `Poll::Ready(값)`(끝남) 또는 `Poll::Pending`(아직 — 준비되면 깨워 주겠다).\
> 예: (3)의 로그에서 `poll #1 returned Pending`.

> **Waker** — `Pending` 을 돌려준 future 가 「이제 다시 poll 해도 된다」고 실행기에 알리는 손잡이. `cx.waker()` 로 받는다.\
> 예: (3)에서 `[exec] waker called` 가 찍힌 뒤에야 `poll #2` 가 온다.

## 이 주제가 답하려는 질문

1. ★★★ **`async fn` 을 부르면 무엇이 일어나나** — 몸통은 도나, 무엇을 돌려받나, 그것을 버리면 컴파일러는 무엇이라 하나((1)).
2. ★★★ **누가 몸통을 돌리나** — `poll` 이 몇 번 불리고, `Pending` 뒤에 무엇이 있어야 다시 불리나((2)·(3)).
3. ★★ **「상태 기계」는 무엇으로 보이나** — 지역 변수를 await 앞/뒤에 두면 future 의 **크기**가 어떻게 움직이나((4)).

★ **선행** — [**36번 주제**](../36-iterator-adapters-laziness-and-collect/)가 이 주제의 뿌리다. ★★★ **이미 잰 것 — 다시 재지 않고 인용한다.**
36번 (2) — **어댑터 사슬은 만든 직후 로그 0 줄** · (3) — **`#[must_use]` 「iterators are lazy and do nothing unless consumed」** · **`let _ =` 를 붙이면 경고는 사라지지만 여전히 아무 일도 안 한다**(제5의 상태).
이 편은 같은 모양의 게으름이 **`async fn` 에도** 있다는 것을 보이고, 그 위에 **누가 돌리나(실행기·`Waker`)** 와 **무엇이 남나(상태 기계 크기)** 를 더한다.
[**42번 주제**](../42-refcell-cell-interior-mutability/) · [**44번 주제**](../44-drop-mem-drop-replace-and-take/) — 가드와 임시값이 **어느 줄에서 버려지나**. (4)의 크기 격자가 그 해제 시점을 **바이트로** 다시 보여 준다.

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ① 게으름 로그와 ② 크기 격자다

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ① ★★★ **게으름 로그**(표준 출력·오류 줄) | 부른 순간 몸통이 **도나** | ★ **본체**((1)) |
| ② ★★★ **`size_of_val` 격자** | await 를 가로지르는 지역 변수가 **future 안에 들어가나** | ★ **본체**((4)) |
| ③ ★★ **컴파일러 경고** `unused_must_use` | 버린 future 를 **컴파일러가 잡나** | 쓴다((1)) |
| ④ ★★★ **직접 만든 실행기의 poll 로그** | `poll` 횟수 · `Waker` 가 불린 자리 | 쓴다((2)·(3)) |
| ⑤ ★ **`timeout` 종료 코드** | 벨이 안 울리면 **끝나지 않는다** | 쓴다((3)) |
| 상태 기계의 **필드 이름·배치** | 컴파일러가 만든 타입의 내부 | ★ **못 잰 것** — stable 에 덤프 도구가 없다(`-Zunpretty`·`-Zprint-type-sizes` 는 nightly 전용 — [57번](../57-macros-macro-rules-and-procedural-macros/)의 머리말 블록). **그래서 ② 로 바꿔 물었다**(아래) |
| 시간·메모리 사용량 | — | ★ **안 쟀다** — 이 주제의 질문이 아니다 |
| ⑥ ★★ **`Drop` 로그** | 버린 future 가 **무엇을 정리하나**(취소) | 쓴다((5)) |
| 다른 언어의 「부른 순간」 | — | ★ **이미 잰 것** — Python 51 · JS 39 · Kotlin 52 가 쟀다((6)) |

★★ **제5의 상태 — 「같은 질문을 다른 창으로」.** Kotlin 52 는 `javap` 로 상태 기계 클래스의 **필드**(`label` · `I$0`)를 직접 봤다. Rust stable 에는 그런 창이 없다.
그래서 질문을 **「그 변수가 future 안에 들어가나」 → 「future 의 바이트 수가 그 변수만큼 커지나」** 로 바꿔 ② 에게 물었다.
★ 바꾼 창이 못 보는 것 — **어느 필드가 어느 상태에 속하는지**는 안 보인다. 보이는 것은 **합**뿐이다.

### (1) ★★★ 부르기만 하면 — 몸통이 찍는 줄이 있나

**언제 쓰나** — `async fn` 을 처음 쓸 때마다. 다른 언어의 감으로 「불렀으니 돌았다」고 믿는 자리다.

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

- ★★★ **표준 출력에 `body of f` 가 한 번도 없다** — `f();` 를 부르고, `let _ = f();` 로 버리고, `let fut = f();` 로 받고, `drop(fut)` 로 버렸는데 **몸통은 0줄** 돌았다. Reference: 「**Async functions do no work when called: instead, they capture their arguments into a future.**」
- ★★★ **경고는 `f();` 줄(7행) 하나뿐** — ``unused implementer of `Future` that must be used`` · 「**futures do nothing unless you `.await` or poll them**」. **`let _ = f();`(9행)와 `let fut = f();`(11행)에는 경고가 없다** — 그런데 둘 다 안 돌았다([36번](../36-iterator-adapters-laziness-and-collect/) (3)의 「경고가 없다는 것은 돌았다가 아니다」와 같은 모양이고, 이번에는 future 로 쟀다).
- ★★ **`drop(fut)` 해도 몸통은 안 돈다** — future 를 버리는 것은 「주문 취소」다. **시작도 안 한 계산은 취소해도 아무 흔적이 없다.**
- ★ 이 경고는 `Future` 트레이트에 붙은 `#[must_use]` 에서 온다(경고 문구 첫 줄 「unused implementer of `Future`」). 이터레이터의 그것과 **문구만 다른 같은 장치**다.

### (2) ★★★ 누가 돌리나 — 실행기 30줄

**언제 쓰나** — 「표준 라이브러리에는 실행기가 없다」(55번)는 말이 무슨 뜻인지 손으로 확인할 때. **tokio 없이** 돌려 본다.

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

- ★★★ **실행기가 하는 일은 셋뿐이다** — ① future 를 **고정**한다(`pin!` — 옮기지 않겠다는 약속. 왜 필요한지는 55번) ② `Waker` 를 만들어 `Context` 에 담는다 ③ `poll` 을 부르고, `Pending` 이면 **스레드를 재운다**(`thread::park`). 깨우는 것은 `Waker` 의 몫이다(`unpark`).
- ★★ **`Wake` 트레이트(1.51.0)** 를 구현하면 `Waker::from(Arc<…>)` 로 `Waker` 가 나온다 — **`unsafe` 없이**. 옛 방식(`RawWaker` + 함수 포인터 표)은 `unsafe` 가 필요하다.

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

- ★★★ **`[1] future created` 다음에야 `body of f`** — 몸통은 **`poll #1` 안에서** 돌았다. `f` 는 기다릴 것이 없어서 **첫 poll 에 끝까지** 달려 `Ready` 를 돌려줬다.
- ★ **`block_on` 이 `7` 을 돌려줬다** — `Poll::Ready(v)` 의 `v` 가 `async fn` 의 반환값이다.

### (3) ★★★ `Pending` 뒤에 무엇이 있어야 다시 poll 되나 — poll 횟수 로그

**언제 쓰나** — 손으로 `Future` 를 구현할 때, 그리고 「왜 이 작업이 멈춰 있지?」를 읽을 때.

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

**`Waker` 를 부르는 판.**

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

- ★★★ **`poll` 은 3번** — `await` 가 두 개라 **멈출 자리가 둘**이고, 매번 한 번 멈췄다가 한 번 더 불렸다. **`[body] start` 는 한 번만** 찍힌다 — 두 번째 poll 은 몸통을 **처음부터 다시 돌지 않고 멈춘 자리부터** 이어 간다. 이것이 「상태 기계」다(Reference — Await expressions: `Pending` 이면 「suspending its state so that, when the surrounding async context is re-polled, execution returns to step 3」 — 3단계는 안쪽 future 를 poll 하는 자리다).
- ★★ **`[exec] waker called` 가 `[leaf] Pending` 보다 먼저** — 잎 future 가 `Pending` 을 돌려주기 **전에** 깨웠다. 그래도 실행기는 `park` 에서 **바로 깨어난다** — std `thread::park`: `unpark` 가 **토큰**을 먼저 놓아 두면 `park` 는 「blocks … unless or until the token is available」이라 막히지 않는다. ★ 같은 문서가 「**It may also return spuriously**」라고 적으므로 이 실행기는 가끔 **한 번 더 poll 할 수도** 있다 — 이 판의 3번에서는 그런 일이 없었다.
- ★★ **잎(leaf)만 `Waker` 를 만진다** — `two_steps` 의 몸통(`async fn`)에는 `Waker` 가 한 글자도 없다. `.await` 가 **자기가 받은 `Context` 를 잎에게 그대로 넘긴다**(Reference — Await expressions 의 「task context」).

**`Waker` 를 안 부르는 판.**

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

- ★★★ **`poll #1 returned Pending -- park` 에서 멈췄고 `timeout 2` 가 죽였다(`exit 124`)** — `[body] between…` 도 `[main] done` 도 없다. **`Pending` 은 「나중에 깨워 주겠다」는 약속**이고, 약속을 안 지키면 **실행기는 다시 묻지 않는다.** std `Future::poll` 문서가 이것을 계약으로 적는다 — 「When a future is not ready yet, poll returns `Poll::Pending` and **stores a clone of the `Waker`** copied from the current `Context`」 · 「The poll function should not be called repeatedly in a tight loop – instead, it should **only be called when the future indicates that it is ready** to make progress (by calling `wake()`)」.
- ★ 그래서 이 판은 **에러도 경고도 없이 조용히 멈춘다**(18-A — 침묵이 결론). 바쁜 루프로 계속 poll 하는 실행기라면 멈추지 않았을 것이다 — **이 실행기는 계약대로 깨울 때만 poll 한다.**
- ★ 이 블록만 마커를 **표준 오류**로 찍은 것이 결정적이었다 — `timeout` 이 SIGTERM 으로 죽이면 **표준 출력 버퍼는 flush 되지 않는다**(규칙 19-A).

### (4) ★★★ 상태 기계의 크기 — await 를 가로지르는 지역 변수

**언제 쓰나** — 큰 버퍼를 든 채 await 하는 코드를 쓸 때. future 는 **값**이라 스택·힙에 통째로 놓인다.

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

- ★★★ **`a_no_buffer` 2 · `d_used_after` 1026** — 1024바이트 배열을 **await 앞에서 만들고 뒤에서 쓰면** 그 배열이 **future 안에** 들어간다. 멈춘 동안에도 남아 있어야 하기 때문이다.
- ★★★ **`e_created_after` 2** — 같은 배열을 **await 뒤에서 만들면** 안 커진다. 멈추는 순간에는 **아직 없는** 값이라 담을 필요가 없다(poll 이 도는 동안 **스택**에 있다가 사라진다).
- ★★★ **`b_used_before_only` 1032 대 `b2_indexed_before_only` 8** — 둘 다 await **앞에서만** 배열을 썼는데 갈렸다. **`b` 는 `&buf` 로 빌렸고 `b2` 는 `buf[0]` 으로 원소만 읽었다.** 빌린 적이 있는 지역 변수는 **스코프가 끝날 때까지** 상태 기계에 남았다 — 그 뒤에 안 써도.
  **`c_inner_block_before` 8** — 빌렸더라도 **안쪽 블록에서 끝내면** 안 들어간다. 스코프가 await 앞에서 닫히기 때문이다.
- ★★ **`h_two_buffers_two_blocks` 1026 대 `f_two_buffers_two_awaits` 2050** — 두 배열이 **서로 다른 멈출 자리**에만 걸쳐 있으면 **한 자리를 나눠 쓴다**(`h` — 각각 블록에 가뒀다). `f` 는 `a` 가 **함수 끝까지 스코프에 있어** 두 번째 await 도 가로질렀다 → 둘 다 들어간다(`g` 와 같은 2050).
- ★★ **`tick` 1 · `a_no_buffer` 2** — 아무것도 안 들어도 **「몇 번째 상태인가」를 적을 칸**이 있다. 기다리는 future(`tick()`)를 품으면 그만큼 더해진다.
- ★ **`type: r54_size::a_no_buffer::{{closure}}`** — future 의 타입은 **컴파일러가 지어 준 이름 없는 타입**이다. 그래서 `async fn` 의 반환 타입을 손으로 못 적고 `impl Future` 로 부른다(Reference: 「roughly equivalent to a function that returns `impl Future`」).

**`-C opt-level=3` 로 다시.**

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

- ★★★ **디버그 판과 한 글자도 같다** — 이 크기는 **최적화가 줄여 주는 값이 아니다**(규칙 24 의 판 격자 — 2판). 「상태 기계에 무엇을 담나」는 최적화 **전에** 정해진다.
- ★★ **층 가르기** — 「await 너머로 살아 있어야 하는 값은 future 안에 있어야 한다」는 **의미상 필연**이다. 그런데 「**빌린 적이 있으면 스코프 끝까지 담는다**」·「두 자리가 칸을 나눠 쓴다」는 **rustc 의 분석이 이 판에서 그렇게 한 것**이다(Reference 는 크기를 말하지 않는다). 판이 오르면 **다시 찍을 칸**이다.

### (5) ★★ 버리면 — 취소는 「멈춘 자리에서 끝」이다

**언제 쓰나** — 타임아웃·`select` 처럼 **다 끝나기 전에 future 를 버리는** 코드를 읽을 때(그런 도구는 런타임의 것이다 — 55번).

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

- ★★★ **한 번도 poll 안 된 `a` 는 버려도 `drop a` 가 없다** — 몸통이 안 돌았으니 `Noisy("a")` 가 **만들어진 적이 없다.** future 안에는 인자만 있었다.
- ★★★ **한 번 poll 되어 멈춘 `b` 는 버리는 순간 `drop b`** — 상태 기계가 await 너머로 **들고 있던** `_held` 가 정리된다((4)의 「future 안에 들어간 값」이 바로 이것). `finished` 줄은 **영영** 없다.
- ★★ **Rust 의 취소는 「future 를 버리는 것」 하나다** — 별도의 취소 신호가 없다. 그래서 **await 사이에서 중간 상태를 남기는 코드**(반쯤 쓴 파일 등)는 거기서 끊길 수 있다.
- ★ `Waker::noop()`(1.85.0) — 아무것도 안 하는 `Waker`. 한 번만 poll 하는 이 탐침에는 깨울 일이 없다.

### (6) ★★ 네 언어 — 부른 순간 몸통이 도나

★★★ **세 언어는 이미 쟀다 — 다시 돌리지 않고 인용한다.** Rust 칸만 이 편의 (1)·(2)다.

| 언어 | 부르기만 하면 | 돌게 하려면 | 버리면 | 근거 |
|---|---|---|---|---|
| **Rust `async fn`** | ★★★ **future 값만 — 몸통 0줄** | 실행기가 `poll`(`.await` 는 **바깥 future 의 poll 안에서** 안쪽을 poll 한다) | ★ **컴파일 경고**(`unused_must_use`) · 실행 중에는 아무 말 없음 | (1)·(2) |
| **Python `async def`** | 코루틴 객체만 — **몸통 0줄** | `await` · `asyncio.run` · `create_task` | ★ **실행 중 경고** — `RuntimeWarning: coroutine 'f' was never awaited`(버리는 **그 순간**, 표준 오류) | [Python 51번](../../../python/syntax/51-asyncio-coroutine-basics/) (1) |
| **JavaScript `async function`** | ★★★ **첫 `await` 까지 지금 돈다** — 프라미스가 나온다 | (이미 돌고 있다) | 경고 없음 — 거부되면 처리기 없는 거부로 도착한다 | [JS 39번](../../../js/syntax/39-async-await/) (1)·(9) |
| **Kotlin `suspend fun`** | ★★ **일반 함수에서는 부를 수 없다**(컴파일 에러) · 코루틴 안에서는 **보통 호출** — 몸통이 끝까지 돈다(중단점에서 부른 쪽이 같이 멈춘다) | 따로 돌리려면 `launch`/`async`(라이브러리) | — | [Kotlin 52번](../../../kotlin/syntax/52-coroutine-basics-suspend-scope-launch-async/) (2)·(4) |

- ★★★ **Rust 와 Python 이 같은 편이고, JS 가 반대편이다** — 「부르면 몸통이 도나」가 갈린다. JS 39 가 같은 탐침을 Python 과 나란히 돌려 `caller: before f() > f: line 1 > caller: after f()`(JS)와 `f: line 1` 없음(Python)을 얻었다.
- ★★ **Rust 와 Python 이 갈리는 칸은 「버린 것을 누가 알려 주나」다** — Rust 는 **컴파일러**가 (1)에서, Python 은 **런타임**이 버리는 순간에. Rust 는 실행 중에는 **아무 말이 없다**((1)의 `drop(fut)` 뒤에 아무 줄도 없다).
- ★★ **Kotlin 은 질문 자체가 다르다** — `suspend` 함수는 부를 수 있는 **자리**가 정해져 있고(52 (2)의 격자), 부르면 **보통 함수처럼** 끝까지 간다. Kotlin 의 「상태 기계」(`label`)는 `javap` 로 **필드째** 보였고, Rust 의 그것은 (4)의 **바이트 수**로만 보인다.
- ★ **C#** — C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **40번**(`async`/`await` 와 `Task`)이 서면 이 표의 칸이 하나 는다. **이 문서는 C# 을 재지 않았다.**

## 문법 — 형태와 규칙

```text
   async fn f(x: T) -> U { … }         ← 부르면 impl Future<Output = U> 를 돌려준다 · 몸통은 안 돈다
   async { … }   async move { … }       ← 같은 것을 식으로 (이 편은 async fn 만 던졌다)
   식.await                              ← async 문맥 안에서만 (밖이면 E0728 — 55번)
   impl Future for T {                   ← 손으로 쓰는 future (잎)
       type Output = …;
       fn poll(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Self::Output>
   }
   Poll::Ready(v) / Poll::Pending        ← Pending 이면 cx.waker() 를 깨우도록 예약할 책임
   impl Wake for W { fn wake(self: Arc<Self>) }   Waker::from(Arc::new(w))   ← unsafe 없는 Waker
```

- ★★★ **`async fn` 은 부르면 future 를 만들 뿐이다 — 몸통은 누가 `poll` 할 때 돈다**((1)·(2)).
- ★★★ **`Pending` 은 「깨워 주겠다」는 약속이다 — 안 깨우면 다시 poll 되지 않는다**((3)).
- ★★ **await 를 가로질러 살아 있는 지역 변수가 future 의 크기가 된다**((4)).

## 어디서 틀리나

### 1. ★★★ 「`async fn` 을 부르면 백그라운드에서 돌기 시작한다」

(1) — **몸통 0줄.** JS 의 감이다((6)). Rust 는 **누가 poll 하기 전에는** 아무 일도 없다. `f();` 로 부르고 끝내면 **그 일은 영원히 안 일어난다** — 컴파일 경고 한 줄이 유일한 신호다.

### 2. ★★★ 「경고가 안 나면 돌았다」

(1) — `let _ = f();` 와 `let fut = f();` 는 경고가 없는데 **안 돌았다.** 이터레이터에서 잰 것([36번](../36-iterator-adapters-laziness-and-collect/) (3))과 같은 모양이다.

### 3. ★★ 「`poll` 이 `Pending` 을 돌려주면 실행기가 알아서 다시 부른다」

(3) — **깨우지 않으면 안 부른다**(`exit 124`). 손으로 `Future` 를 구현할 때 **`Pending` 을 돌려주는 모든 길에서** `Waker` 를 챙겨야 한다.

### 4. ★★ 「두 번째 poll 은 몸통을 처음부터 다시 돈다」

(3) — `[body] start` 는 **한 번**뿐이다. 멈춘 자리부터 이어 간다.

### 5. ★★ 「await 앞에서만 쓴 변수는 future 에 안 들어간다」

(4) — **빌린 적이 있으면 들어간다**(`b` 1032). 안쪽 블록으로 가두면 빠진다(`c` 8). ★ 이 규칙은 **55번의 `Send` 에러**에서 한 번 더 나온다 — 같은 분석이 「`Rc` 를 쥐고 await 했나」를 판정한다.

### 6. ★ 「future 의 크기는 최적화가 줄여 준다」

(4) — `-O3` 판이 **한 글자도 같다.**

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| `async fn` 은 불렸을 때 일을 하지 않는다 | ★ **언어**(Reference — Async functions) | (1) |
| `.await` 는 안쪽을 poll 하고, `Pending` 이면 바깥도 `Pending` 으로 멈춘다 | ★ **언어**(Reference — Await expressions) | (3) |
| `Pending` 을 돌려줄 때 `Waker` 를 챙겨 두고, 실행기는 깨워졌을 때만 poll 한다 | ★ **std 의 계약**(`Future::poll` 문서) | (3) |
| 버린 future 에 대한 경고 | ★ **rustc 린트**(`unused_must_use` — `Future` 의 `#[must_use]`) | (1) |
| future 의 **바이트 크기**와 「빌린 변수는 스코프 끝까지」 | ★ **rustc 의 분석·배치**(이 판의 관찰 — 두 최적화 판에서 같음) | (4) |
| `type_name_of_val` 의 문자열 | ★ **구현**(std 가 형식을 보장하지 않는다고 적는다) | (4) |
| `thread::park` 가 먼저 온 `unpark` 로 즉시 돌아온다 · 까닭 없이 돌아올 수도 있다 | ★ **std 의 계약**(`thread::park` 문서) | (3) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 근거 |
|---|---|---|
| 기다리는 일이 많고(입출력) 스레드를 늘리기 싫다 | `async` + **런타임**(55번) | ★ 성능은 **이 문서가 재지 않았다** |
| 계산만 하는 함수 | 보통 `fn` — `async` 를 붙여도 poll 한 번에 끝날 뿐이다((2)의 `f`) | (2) |
| 큰 버퍼를 들고 await 해야 한다 | ★ **안쪽 블록으로 가두거나 `Box` 로 힙에** — future 가 통째로 커진다 | (4) |
| `Future` 를 손으로 구현한다 | ★ **`Pending` 의 모든 길에서 `Waker` 를 챙긴다** | (3) |
| 테스트·예제에서 잠깐 돌리고 싶다 | 직접 만든 `block_on`(이 편) 또는 런타임의 것 | (2) |

## 핵심 문장

- ★★★ **`async fn` 을 부르면 future 가 나올 뿐이다 — 몸통은 누가 `poll` 해야 돈다.** 버리면 컴파일러가 경고하고, 실행 중에는 아무 말도 없다.
- ★★★ **실행기는 poll 하고, `Pending` 이면 잠들고, `Waker` 가 깨우면 다시 poll 한다 — 그뿐이다.** 깨우지 않으면 영원히 멈춘다.
- ★★★ **future 는 상태 기계다 — 멈춘 자리부터 이어 가고, 멈춘 동안 살아 있어야 할 지역 변수를 제 안에 담는다.** 그래서 await 너머로 든 버퍼만큼 커진다.
- ★★ **future 를 버리면 멈춘 자리에서 끝나고 들고 있던 값이 정리된다 — 그것이 취소다.**
- ★★ **Rust·Python 은 부르기만 해서는 안 돌고, JS 는 첫 await 까지 지금 돈다.**

## 관련 자료

- [**36번 주제**](../36-iterator-adapters-laziness-and-collect/) — 이터레이터의 게으름과 `#[must_use]`. **그쪽은 「소비하기 전엔 안 돈다」, 여기는 「poll 하기 전엔 안 돈다」와 그 기계.**
- [**55번 주제**](../55-async-in-practice-runtime-send-and-pin/) — 표준에 실행기가 없다는 것의 결과 · `Send` 경계 · `Pin`. **이 편의 (4) 분석이 그쪽의 `Send` 에러를 만든다.**
- [`history/rust/04-비동기-동시성.md`](../../../../history/rust/04-비동기-동시성.md) — **그쪽은 `futures` 0.1 에서 `async/await` 안정화(1.39)까지의 역사와 poll–wake 모델의 설명**, 여기는 그 모델을 **직접 돌려 로그와 바이트로** 본다.
- [Python 51번](../../../python/syntax/51-asyncio-coroutine-basics/) · [JS 39번](../../../js/syntax/39-async-await/) · [Kotlin 52번](../../../kotlin/syntax/52-coroutine-basics-suspend-scope-launch-async/) — (6)의 세 칸.
- [**44번 주제**](../44-drop-mem-drop-replace-and-take/) — (5)의 취소가 따르는 해제 규칙.

## 용어 풀이

- **future** — 나중에 값이 되는 계산. `Future` 트레이트를 구현한 값이고, poll 되어야 나아간다.
- **`poll`** — future 를 한 단계 나아가게 하는 메서드. `Ready(값)` 또는 `Pending`.
- **실행기(executor)** — future 를 poll 하는 쪽. 표준 라이브러리에는 없다.
- **`Waker` · `Context`** — 「다시 poll 해도 된다」를 알리는 손잡이와, 그것을 poll 에 실어 나르는 상자.
- **`Wake` 트레이트** — `Arc` 에 담긴 값으로 `Waker` 를 안전하게 만드는 트레이트(1.51.0).
- **상태 기계(state machine)** — 「지금 몇 번째 상태인가」와 그 상태에 필요한 값만 들고 다니는 구조. `async fn` 의 future 가 이것이다.
- **잎 future(leaf future)** — 다른 future 를 await 하지 않고 `poll` 을 직접 구현한 future. `Waker` 를 만지는 곳이다.
- **`thread::park` / `unpark`** — 스레드를 재우고 깨우는 std 함수.

## 더 들어가면

- `async` 블록·`async move` 와 캡처 — 이 편은 `async fn` 만 던졌다.
- `async fn` 이 인자를 **어떻게 캡처하나**(참조 인자의 수명이 future 에 묶인다 — Reference 의 desugar 예) — 55번의 `'static` 경계와 이어진다.
- `-Zprint-type-sizes`(nightly) — 상태 기계의 **상태별 배치**를 찍는다. 이 머신은 stable 뿐이라 **못 잰 것**이다.
- 재귀 `async fn` 은 크기가 무한이 되어 `Box::pin` 이 필요하다 — **던지지 않았다.**
