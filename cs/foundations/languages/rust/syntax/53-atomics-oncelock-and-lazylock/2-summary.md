# rust/syntax/53 — `atomic`·`OnceLock`/`LazyLock` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [std — `std::sync::atomic` 모듈 문서](https://doc.rust-lang.org/std/sync/atomic/index.html)(「Rust atomics currently follow the same rules as C++20 atomics」) ·
> [std — `atomic::Ordering`](https://doc.rust-lang.org/std/sync/atomic/enum.Ordering.html)(`Relaxed` 「No ordering constraints, only atomic operations」 · `SeqCst` 「all threads see all sequentially consistent operations in the same order」) ·
> [std — `AtomicUsize::fetch_add`](https://doc.rust-lang.org/std/sync/atomic/struct.AtomicUsize.html#method.fetch_add) ·
> [std — `OnceLock`](https://doc.rust-lang.org/std/sync/struct.OnceLock.html)(`get_or_init` — 「it is guaranteed that only one function will be executed if the function doesn't panic」) ·
> [std — `LazyLock`](https://doc.rust-lang.org/std/sync/struct.LazyLock.html)(「A value which is initialized on the first access」 · §Poisoning) ·
> [std — `Mutex::new`](https://doc.rust-lang.org/std/sync/struct.Mutex.html#method.new)(`const` 표지).
> ★ 위 문서는 **이 머신의 `rust-docs`(1.92.0) 로컬 사본**을 열어 읽었다. 「Stable since」 표지도 거기서 grep 했다((5)의 `r53_since`).
> **실행 검증** — 이 문서의 모든 출력·에러는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64` · 논리 코어 24 에서
> **`rustc --edition 2021 <파일>.rs`** 로 돌려 받은 것이다(격자 둘은 **`-O`** · `static mut` 한 칸만 2024).\
> ★★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다. 소스 펜스도 캡처가 찍었다.\
> ★★★ **속도는 한 번도 재지 않았다** — 「atomic 이 `Mutex` 보다 빠르다」 류의 문장은 **근거가 없으므로 쓰지 않는다.** 이 문서가 보이는 것은 **값이 맞았나**와 **어떤 결과가 나올 수 있었나**뿐이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

★★★ **본체 창 — ① 원자 연산 격자(카운터 `+1` 을 8 스레드 × 100000 번 × 방법 넷 × 20판 → 한 판이라도 잃었나)다.** 둘째 본체는 **② 메모리 순서 리트머스 격자**다 — 「순서가 다르면 무엇이 나올 수 있나」를 **실행으로** 물었다.

```text
===== rustc --version =====
rustc 1.92.0 (ded5c06cf 2025-12-08)
(exit 0)
===== uname -m =====
x86_64
(exit 0)
===== nproc =====
24
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| ★★ **흔들린다(판 수)** | (1) 격자의 `N / 20` · (2) 리트머스의 `N / 10` | 스케줄링이 정한다 — ★ **「한 판이라도」 칸만 근거로 쓴다.** 한 판의 **잃은 개수**·리트머스 **발생 횟수**는 흔들리므로 **아예 찍지 않았다** |
| 안 흔들린다(이 머신에서 재대조 동일) | ★★★ **「잃은 칸 `1 / 4`」** · 리트머스 `seqcst 0 / 10` · `mp` 줄 셋 | 격자의 **결론 칸**이다 — 단 `0 / 10` 은 **관찰**이고 금지는 명세가 한다((2)) |
| 안 흔들린다 | ★★★ `OnceLock`·`LazyLock` 의 **`init calls 1`** · `get() None` · `set` 의 `Err("other")` | std 의 **계약**이다 — 20판 모두 1((4)) |
| 안 흔들린다 | E0010 · E0015 · `static_mut_refs` 진단 · `파일:줄:칸` · 종료 코드 | 같은 rustc 판에서 고정이다 |

★ 정규화 규칙은 **기본 넷**만 쓴다. 판 수 칸은 정규화하지 않았다 — 재대조에서 움직이면 그것이 곧 「흔들렸다」는 기록이 되도록 했다.

## 한눈에 — 쉽게 말하면

**여럿이 한 칠판의 숫자를 올리는 교실을 떠올려라.
「읽고 → 머릿속에서 1 더하고 → 지우고 새로 쓰기」를 세 걸음으로 하면, 두 사람이 같은 숫자를 읽고 같은 숫자를 써서 **한 번이 사라진다.**
원자 연산은 「**칠판에 손을 댄 채 한 동작으로 올리기**」다 — 끼어들 틈이 없다. 자물쇠(`Mutex`)는 「**교실 문을 잠그고 한 사람씩 들어가기**」다.
`OnceLock` 은 「**첫 사람만 칠판을 채우고, 뒤에 온 사람은 채워질 때까지 기다렸다 읽기만**」 하는 칸이다.**

| 비유 | 실체 |
|---|---|
| 「**세 걸음으로 올리기**」 | ★★★ **`load` → `+1` → `store`** — 둘 다 원자 연산인데 **사이가 비었다** → 잃는다((1) `0 / 20`) |
| 「**손을 댄 채 한 동작**」 | ★★★ **`fetch_add`** — 읽기·수정·쓰기가 **한 연산**(RMW) → 안 잃는다. 순서 인자와 **무관하게**(`Relaxed` 도 20/20) |
| 「**문을 잠그고 한 사람씩**」 | ★ **`Mutex`**((1) 넷째 줄 · 정본은 [52번 주제](../52-mutex-rwlock-arc-and-poisoning/)) |
| 「**내 쪽지가 아직 우체통에 있다**」 | ★★ **저장 버퍼** — 내가 쓴 값이 남에게 보이기 **전에** 내 다음 읽기가 먼저 끝난다((2)의 `sb`) |
| 「**모두가 같은 순서로 본다**」 | ★★ **`SeqCst`** — docs: 「all threads see … in the same order」 → `sb` 가 `0 / 10` |
| 「**첫 사람만 채운다**」 | ★★★ **`OnceLock::get_or_init`** · **`LazyLock`** — 초기화 클로저가 **한 번만**((4) `init calls 1`) |

```text
   같은 「+1」, 네 가지 방법 — (1)의 격자가 이 그림을 판정한다

   load_then_store                      fetch_add (Relaxed · SeqCst)
   ─────────────────────                ─────────────────────────────
   A: v = load()   → 5                  A: fetch_add(1)  5 → 6   (한 연산)
   B: v = load()   → 5                  B: fetch_add(1)  6 → 7   (한 연산)
   A: store(v+1)   → 6
   B: store(v+1)   → 6   ← 한 번이 사라진다   끼어들 자리가 없다
   ─────────────────────                ─────────────────────────────
   (1): 20판 중 800000 이 된 판 0          (1): 20판 중 20
```

> **원자 연산(atomic operation)** — 다른 스레드가 **중간 상태를 볼 수 없는** 메모리 연산. `AtomicUsize`·`AtomicBool` 등이 `&self` 로 이것을 준다(`static` 에 두고 여러 스레드가 그냥 부른다).\
> 예: `static HITS: AtomicUsize = AtomicUsize::new(0);` · `HITS.fetch_add(1, Ordering::Relaxed);`.

> **읽기-수정-쓰기(RMW, read-modify-write)** — 읽고 고치고 쓰는 일을 **한 원자 연산으로** 하는 것. `fetch_add`·`fetch_sub`·`swap`·`compare_exchange` 가 이것이다.\
> 예: `A.fetch_add(1, Relaxed)` 는 이전 값을 돌려주며 1 을 더한다.

## 이 주제가 답하려는 질문

1. ★★★ **락 없이 되는 경우는 어디까지인가** — 「값 하나를 RMW 한 번으로 바꾸는」 곳까지. `load`+`store` 로 쪼개면 원자 연산을 써도 잃는다((1)).
2. ★★ **`Ordering` 인자는 무엇을 바꾸나** — 그 변수 **자신의** 원자성이 아니라 **다른 메모리와의 순서**다. 무엇이 보이고 무엇이 이 머신에서 못 보이나((2)).
3. ★★★ **전역 값을 안전하게 한 번만 초기화하는 법** — `const` 로 되면 `static` 에 바로, 안 되면 `OnceLock`/`LazyLock`((3)·(4)·(5)).

★ **선행** — [**52번 주제**](../52-mutex-rwlock-arc-and-poisoning/) — `Mutex` 가 데이터를 감싸는 이유와 가드. 이 편의 (1) 넷째 줄이 그 기준선이다.
[**41번 주제**](../41-rc-arc-shared-ownership-and-weak-cycles/)의 `Arc` 는 **계수를 원자적으로** 올린다는 점이 `Rc` 와의 차이였다 — 이 편이 그 원자 연산을 직접 쓴다.
[**50번 주제**](../50-send-sync-in-compiler-errors/) — `static` 에 두는 값은 여러 스레드가 `&` 로 보므로 `Sync` 여야 한다. `AtomicUsize`·`Mutex`·`OnceLock`·`LazyLock` 이 그 자리에 들어갈 수 있는 이유다.

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ① 원자 연산 격자다

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ① ★★★ **원자 연산 격자**(방법 넷 × 20판 · `-O`) | 최종 값이 800000 인가 · **한 판이라도 잃었나** | ★ **본체**((1)) |
| ② ★★★ **리트머스 격자**(SB·MP × 순서 셋 × 10판 × 판마다 200000회) | 순서를 약하게 주면 **나올 수 있는 결과**가 실제로 나오나 | ★ **둘째 본체**((2)) |
| ③ ★★ **초기화 호출 수 로그**(`OnceLock`·`LazyLock` · 20판) | 초기화 클로저가 **몇 번** 도나 | 쓴다((4)) |
| ④ ★★ **컴파일러 진단** E0010 · E0015 · `static_mut_refs` | `static` 에 무엇을 **못** 두나 · 컴파일러가 무엇을 권하나 | 쓴다((3)·(6)) |
| ⑤ ★ **로컬 rust-docs grep** | 언제부터 Stable 인가 · `const` 표지 | 쓴다((5)) |
| 실행 시간 · 경합 비용 | 「atomic 이 빠르다」 | ★ **부적용 — 재지 않는다** |
| 약한 메모리 하드웨어(ARM·POWER)의 `mp` 재배치 | `Relaxed` MP 가 깨지는 판 | ★ **못 잰 것** — 이 머신이 x86_64 뿐이다((2)). Miri 도 없다(41번 머리말 블록) |

★★ **제5의 상태 — 「같은 질문을 다른 창으로」.** 「이 `Ordering` 으로 충분한가」는 원래 **명세**(C++20 메모리 모델)가 답하는 질문이고, 코드를 읽어서는 답이 안 나온다.
그 질문을 **리트머스의 창**으로 옮겨 물었다((2)) — 「약한 순서가 허락하는 결과가 **이 머신에서 실제로 나오나**」.
★ 바꾼 창이 **못 보는 것** — **이 머신이 안 만드는 재배치.** x86 은 `mp` 재배치를 하드웨어가 하지 않으므로 `Relaxed` 가 `0 / 10` 이어도 **다른 CPU 에서 안전하다는 증거가 아니다.** 리트머스는 「나왔다」만 증명하고 「안 나온다」는 증명하지 못한다.

### (1) ★★★ 원자 연산 격자 — 카운터 `+1` 을 네 가지로

**언제 쓰나** — 여러 스레드가 숫자 하나를 올리는 코드를 보면 매번. 「원자 타입을 썼으니 됐다」가 맞는지 판정할 때.

```text
===== 소스: r53_count.rs =====
use std::env;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Mutex;
use std::thread;

const THREADS: usize = 8;
const PER_THREAD: usize = 100_000;

static A: AtomicUsize = AtomicUsize::new(0);
static M: Mutex<usize> = Mutex::new(0);

fn main() {
    let how = env::args().nth(1).unwrap();
    thread::scope(|s| {
        for _ in 0..THREADS {
            s.spawn(|| {
                for _ in 0..PER_THREAD {
                    match how.as_str() {
                        "fetch_add_relaxed" => { A.fetch_add(1, Ordering::Relaxed); }
                        "fetch_add_seqcst" => { A.fetch_add(1, Ordering::SeqCst); }
                        "load_then_store" => {
                            let v = A.load(Ordering::SeqCst);
                            A.store(v + 1, Ordering::SeqCst);
                        }
                        "mutex" => { *M.lock().unwrap() += 1; }
                        _ => unreachable!(),
                    }
                }
            });
        }
    });
    let got = if how == "mutex" { *M.lock().unwrap() } else { A.load(Ordering::SeqCst) };
    println!("{}", got == THREADS * PER_THREAD);
}
===== rustc --edition 2021 -O r53_count.rs =====
(exit 0)
```

```text
===== 소스: r53_count.sh =====
# 카운터 +1 을 8 스레드 × 100000 번 — 방법마다 20판을 돌려 최종 값이 800000 인 판을 센다
rustc --edition 2021 -O -o r53_count r53_count.rs || exit 1
printf 'method\truns equal to 800000\tlost in at least one run\n'
lost=0; m=0
for how in fetch_add_relaxed fetch_add_seqcst load_then_store mutex; do
  eq=0
  for i in $(seq 20); do
    [ "$(./r53_count "$how")" = true ] && eq=$((eq+1))
  done
  any=no
  [ "$eq" -lt 20 ] && { any=yes; lost=$((lost+1)); }
  printf '%s\t%s / 20\t%s\n' "$how" "$eq" "$any"
  m=$((m+1))
done
echo "cells that lost: $lost / $m"
===== bash r53_count.sh =====
method	runs equal to 800000	lost in at least one run
fetch_add_relaxed	20 / 20	no
fetch_add_seqcst	20 / 20	no
load_then_store	0 / 20	yes
mutex	20 / 20	no
cells that lost: 1 / 4
(exit 0)
```

- ★★★ **「잃은 칸 1 / 4」** — `load_then_store` 만 잃었고 **20판 전부**(`0 / 20`) 800000 이 안 됐다.
- ★★★ **`load` 도 `store` 도 원자 연산인데 잃는다** — 각각은 원자적이지만 **둘 사이**에 다른 스레드가 끼어든다. 원자성은 **연산 하나**의 성질이지 **두 연산의 묶음**의 성질이 아니다. 게다가 이 줄은 **`SeqCst`** 다 — **가장 강한 순서로도 틈은 안 메워진다.** 순서는 원자성을 늘리지 않는다.
- ★★★ **`fetch_add` 는 `Relaxed` 로도 20/20** — `Relaxed` 는 docs 로 「**No ordering constraints, only atomic operations**」다. 순서 보장은 없어도 **RMW 한 번의 원자성은 있다** — 카운터에는 그것으로 충분하다.
- ★★ **`Mutex` 도 20/20** — 락은 **여러 연산을 한 덩어리로** 묶을 수 있다. 원자 연산은 **한 연산**까지만 묶는다 — 그 경계가 「락 없이 되는가」의 경계다((3)의 표).
- ★★★ **「20/20 통과」는 보장이 아니다** — `fetch_add` 의 근거는 **20판이 아니라 docs**(RMW 는 원자적)이다. 거꾸로 `load_then_store` 가 20판 **전부** 잃은 것은 **이 머신 · 이 부하**의 관찰이다 — 스레드가 적거나 반복이 짧으면 통과하는 판이 나올 수 있다(가이드 규칙 3 — 동기화 없는 `int++` 이 20/20 정답이 나온 판이 있었다).
- ★ 한 판에서 **몇 개를 잃었나**는 찍지 않았다 — 흔들리는 칸이라 근거가 못 된다.

```text
   원자성은 「연산 하나」까지다 — (1)이 가른 경계

   fetch_add(1, Relaxed)      한 연산        → 안 잃는다   20 / 20
   fetch_add(1, SeqCst)       한 연산        → 안 잃는다   20 / 20
   load(SeqCst); store(SeqCst)   연산 둘 + 틈   → 잃는다     0 / 20   ← 순서를 올려도 틈은 그대로
   lock(); += 1; unlock        락이 묶은 구간  → 안 잃는다   20 / 20
```

### (2) ★★★ 메모리 순서 — x86 에서 **갈린 것**과 **안 갈린 것**

**언제 쓰나** — `Relaxed` 로 적힌 원자 연산이 **다른 데이터의 신호**(깃발)로 쓰이는 코드를 볼 때. 카운터가 아니라 「깃발을 보고 다른 값을 읽는」 코드다.

★★★ **브리핑의 전제를 뒤집었다.** 브리핑은 「메모리 순서의 차이는 **x86 에서 재현이 어렵다** — 못 잰 것으로 적어라」였다.
**재 보니 절반이 틀렸다** — 리트머스 두 가지 중 **SB 는 x86 에서도 갈렸고**, **MP 만 안 갈렸다.**

```text
===== 소스: r53_litmus.rs =====
// 리트머스 두 가지를 판마다 반복한다. 판마다 main 이 깃발을 0 으로 되돌리고 GO 를 올려
// 두 스레드를 동시에 출발시킨다. 인자: <sb|mp> <relaxed|release_acquire|seqcst>
//   sb — 스레드 A: X=1 쓰고 Y 읽기 · 스레드 B: Y=1 쓰고 X 읽기. 두 읽기가 모두 0 인 판을 센다.
//   mp — 스레드 A: X=1 쓰고 Y=1 쓰기 · 스레드 B: Y 가 1 이 될 때까지 돌다가 X 읽기. X 가 0 인 판을 센다.
use std::env;
use std::sync::atomic::{AtomicUsize, Ordering::{self, *}};
use std::thread;

static X: AtomicUsize = AtomicUsize::new(0);
static Y: AtomicUsize = AtomicUsize::new(0);
static GO: AtomicUsize = AtomicUsize::new(0);
static DONE: AtomicUsize = AtomicUsize::new(0);
const ROUNDS: usize = 200_000;

fn round_loop(mut body: impl FnMut() -> usize) -> Vec<usize> {
    let mut seen = Vec::with_capacity(ROUNDS);
    for r in 1..=ROUNDS {
        while GO.load(SeqCst) != r {}
        seen.push(body());
        DONE.fetch_add(1, SeqCst);
    }
    seen
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let (st, ld): (Ordering, Ordering) = match args[2].as_str() {
        "relaxed" => (Relaxed, Relaxed),
        "release_acquire" => (Release, Acquire),
        "seqcst" => (SeqCst, SeqCst),
        _ => unreachable!(),
    };
    let sb = args[1] == "sb";
    let hits = thread::scope(|s| {
        let a = s.spawn(|| {
            round_loop(|| {
                if sb {
                    X.store(1, st);
                    Y.load(ld)
                } else {
                    X.store(1, Relaxed);
                    Y.store(1, st);
                    1
                }
            })
        });
        let b = s.spawn(|| {
            round_loop(|| {
                if sb {
                    Y.store(1, st);
                    X.load(ld)
                } else {
                    while Y.load(ld) == 0 {}
                    X.load(Relaxed)
                }
            })
        });
        for r in 1..=ROUNDS {
            while DONE.load(SeqCst) != 2 * (r - 1) {}
            X.store(0, SeqCst);
            Y.store(0, SeqCst);
            GO.store(r, SeqCst);
        }
        let (ra, rb) = (a.join().unwrap(), b.join().unwrap());
        ra.iter().zip(&rb).filter(|(p, q)| if sb { **p == 0 && **q == 0 } else { **q == 0 }).count()
    });
    println!("{}", hits > 0);
}
===== rustc --edition 2021 -O r53_litmus.rs =====
(exit 0)
```

```text
===== 소스: r53_litmus.sh =====
# 리트머스 × 순서 — 10판씩 돌려 「그 결과가 한 번이라도 나온 판」을 센다 (판마다 200000회)
rustc --edition 2021 -O -o r53_litmus r53_litmus.rs || exit 1
printf 'test\tordering\truns where the outcome appeared\n'
for t in sb mp; do
  for o in relaxed release_acquire seqcst; do
    n=0
    for i in $(seq 10); do
      [ "$(./r53_litmus "$t" "$o")" = true ] && n=$((n+1))
    done
    printf '%s\t%s\t%s / 10\n' "$t" "$o" "$n"
  done
done
===== bash r53_litmus.sh =====
test	ordering	runs where the outcome appeared
sb	relaxed	10 / 10
sb	release_acquire	10 / 10
sb	seqcst	0 / 10
mp	relaxed	0 / 10
mp	release_acquire	0 / 10
mp	seqcst	0 / 10
(exit 0)
```

- ★★★ **`sb`(store buffering) — `relaxed 10 / 10` · `release_acquire 10 / 10` · `seqcst 0 / 10`.**
  두 스레드가 각자 **자기 깃발을 쓰고 남의 깃발을 읽었는데 둘 다 0 을 읽은** 판이 약한 두 순서에서 **판마다** 나왔다.
  소스 순서대로라면 적어도 한쪽은 1 을 봐야 할 것 같지만 — **내가 쓴 값이 저장 버퍼에 머무는 동안 내 다음 읽기가 먼저 끝났다.**
  x86 의 메모리 모델(x86-TSO)이 허락하는 **유일한 재배치**가 이것(쓰기 뒤의 읽기가 앞당겨지는 것)이다 — ★ 이 문장은 CPU 제조사 문서의 지식이고 **이 문서가 연 기준 소스가 아니다.** 이 문서가 보인 것은 「그 결과가 나왔다」까지다.
- ★★★ **`Release`/`Acquire` 로도 안 막힌다** — Release 는 「내 **앞의** 쓰기를 먼저 내보낸다」, Acquire 는 「내 **뒤의** 읽기를 미룬다」라서 **「쓰기 → 뒤의 읽기」 짝은 둘 다 묶지 않는다.** 이 짝을 막는 것은 **`SeqCst`** 뿐이다 — docs: 「all threads see all sequentially consistent operations **in the same order**」.
- ★★ **`seqcst 0 / 10` 은 관찰이다 — 금지는 명세가 한다.** 10판 × 200000회에서 한 번도 안 나온 것이 근거가 아니라, **모든 스레드가 한 순서를 본다는 docs 의 문장**이 근거다. 실행은 그 문장과 **어긋나지 않았다**는 것만 보인다.
- ★★★ **`mp`(message passing) — 셋 다 `0 / 10`.** 「데이터를 쓰고 → 깃발을 세운다 / 깃발을 보고 → 데이터를 읽는다」에서 **데이터가 0 으로 보인 판**은 `Relaxed` 에서도 **없었다.**
  x86 은 **쓰기끼리 · 읽기끼리의 순서를 하드웨어가 바꾸지 않기** 때문이다.
  ★★★ **그래서 이 `0 / 10` 을 「`Relaxed` 로 충분하다」로 읽으면 틀린다** — Rust 의 규칙(C++20 모델)은 `Relaxed` 깃발에 **아무 순서도 약속하지 않는다.** 약한 메모리 CPU(ARM·POWER)에서는 나올 수 있고, 컴파일러도 순서를 바꿀 권리가 있다. **이 머신에 그런 CPU 가 없어 못 쟀다**(제3의 상태).
- ★ **판 수(`N / 10`)는 흔들리는 칸**이다. 한 판에서 몇 번 나왔나는 **찍지 않았다** — 「한 판이라도 나왔나」만 주장한다.

```text
   리트머스 둘 — 무엇을 묻고, x86 이 무엇을 보여 줬나

   SB   A: X=1 ; r1=Y        B: Y=1 ; r2=X        r1=0 && r2=0 인 판?
        relaxed      10/10    ← 쓰기 뒤의 읽기가 앞당겨졌다 (x86 도 한다)
        rel/acq      10/10    ← Release·Acquire 는 이 짝을 안 묶는다
        seqcst        0/10    ← 명세가 금지 · 실행은 어긋나지 않았다

   MP   A: X=1 ; Y=1          B: Y 가 1 될 때까지 ; r=X     r=0 인 판?
        relaxed       0/10    ← x86 이 안 바꿨을 뿐 — Rust 는 약속하지 않는다
        rel/acq       0/10    ← 이것은 명세가 약속한다
        seqcst        0/10
```

| 짝 | `Relaxed` | `Release`/`Acquire` | `SeqCst` | 이 머신(x86_64)에서 |
|---|---|---|---|---|
| 쓰기 → 뒤의 읽기(SB) | 허락 | **허락** | 금지 | ★★ 약한 둘에서 **나왔다** |
| 데이터 쓰기 → 깃발 쓰기 / 깃발 읽기 → 데이터 읽기(MP) | 허락 | 금지 | 금지 | ★ 셋 다 **안 나왔다** — `Relaxed` 칸은 **못 잰 것** |

### (3) ★★ `static` 에 바로 둘 수 있는 것 — `const fn` 이면 된다

**언제 쓰나** — 전역 카운터·전역 로그를 만들 때 「초기화 도구가 필요한가」를 먼저 가른다.

```text
===== 소스: r53_static_const.rs =====
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Mutex;

static HITS: AtomicUsize = AtomicUsize::new(0);
static LOG: Mutex<Vec<String>> = Mutex::new(Vec::new());

fn main() {
    HITS.fetch_add(1, Ordering::Relaxed);
    LOG.lock().unwrap().push(String::from("first"));
    println!("hits {}  log {:?}", HITS.load(Ordering::Relaxed), LOG.lock().unwrap());
}
===== rustc --edition 2021 r53_static_const.rs =====
(exit 0)
===== ./r53_static_const =====
hits 1  log ["first"]
(exit 0)
```

- ★★★ **`AtomicUsize::new(0)` 과 `Mutex::new(Vec::new())` 는 `static` 초기화식에 바로 들어간다** — 둘 다 **`const fn`** 이라 컴파일 시점에 값이 정해진다. `lazy_static!`·`once_cell` 같은 외부 크레이트가 **필요 없다.**
- ★ `Mutex::new` 가 `const` 가 된 것은 **1.63.0** 부터다((5)의 `r53_since`). 그 전 판에서는 전역 `Mutex` 도 `static` 에 바로 못 두었다는 뜻이다(옛 판은 이 머신에 없어 **던지지 않았다**).

**그런데 `Vec` 을 채워서 두려면.**

```text
===== 소스: r53_static_vec.rs =====
static TABLE: Vec<u32> = vec![1, 2, 3];

fn main() {
    println!("{:?}", TABLE);
}
===== rustc --edition 2021 r53_static_vec.rs =====
error[E0010]: allocations are not allowed in statics
 --> r53_static_vec.rs:1:26
  |
1 | static TABLE: Vec<u32> = vec![1, 2, 3];
  |                          ^^^^^^^^^^^^^ allocation not allowed in statics
  |
  = note: this error originates in the macro `vec` (in Nightly builds, run with -Z macro-backtrace for more info)

error[E0015]: cannot call non-const method `slice::<impl [u32]>::into_vec::<std::alloc::Global>` in statics
 --> r53_static_vec.rs:1:26
  |
1 | static TABLE: Vec<u32> = vec![1, 2, 3];
  |                          ^^^^^^^^^^^^^
  |
  = note: calls in statics are limited to constant functions, tuple structs and tuple variants
  = note: consider wrapping this expression in `std::sync::LazyLock::new(|| ...)`
  = note: this error originates in the macro `vec` (in Nightly builds, run with -Z macro-backtrace for more info)

error: aborting due to 2 previous errors

Some errors have detailed explanations: E0010, E0015.
For more information about an error, try `rustc --explain E0010`.
(exit 1)
```

- ★★ **E0010 「allocations are not allowed in statics」 + E0015 「cannot call non-const method … in statics」.** `vec![1, 2, 3]` 은 **힙 할당**을 하고 `const` 가 아닌 함수를 부른다. `static` 초기화식은 컴파일 시점에 계산돼야 한다.
- ★★★ **컴파일러가 처방을 준다** — `= note:` 「**consider wrapping this expression in `std::sync::LazyLock::new(|| ...)`**」. (4)가 그 길이다.
- ★ `Vec::new()` 는 **할당을 안 하는 `const fn`** 이라 위의 `LOG` 가 됐다 — 「빈 `Vec`」은 되고 「채운 `Vec`」은 안 된다.

### (4) ★★★ `OnceLock`·`LazyLock` — 초기화 클로저는 몇 번 도나

**언제 쓰나** — 설정 파일 읽기·정규식 컴파일·표 만들기처럼 **실행 중에만 만들 수 있는 전역 값**을 여러 스레드가 처음 쓰는 순간.

```text
===== 소스: r53_oncelock.rs =====
use std::sync::atomic::{AtomicUsize, Ordering::SeqCst};
use std::sync::{Barrier, OnceLock};
use std::thread;
use std::time::Duration;

static CONFIG: OnceLock<String> = OnceLock::new();
static INIT_CALLS: AtomicUsize = AtomicUsize::new(0);

fn config() -> &'static String {
    CONFIG.get_or_init(|| {
        INIT_CALLS.fetch_add(1, SeqCst);
        thread::sleep(Duration::from_millis(50));
        String::from("loaded")
    })
}

fn main() {
    println!("[1] before: get() {:?}  init calls {}", CONFIG.get(), INIT_CALLS.load(SeqCst));
    let start = Barrier::new(8);
    let addrs: Vec<usize> = thread::scope(|s| {
        let hs: Vec<_> = (0..8)
            .map(|_| s.spawn(|| { start.wait(); config() as *const String as usize }))
            .collect();
        hs.into_iter().map(|h| h.join().unwrap()).collect()
    });
    let same = addrs.iter().all(|a| *a == addrs[0]);
    println!("[2] 8 threads called get_or_init  init calls {}  all got the same &String {}", INIT_CALLS.load(SeqCst), same);
    println!("[3] set after init {:?}", CONFIG.set(String::from("other")));
    println!("[4] value {:?}", config());
}
===== rustc --edition 2021 r53_oncelock.rs =====
(exit 0)
===== ./r53_oncelock =====
[1] before: get() None  init calls 0
[2] 8 threads called get_or_init  init calls 1  all got the same &String true
[3] set after init Err("other")
[4] value "loaded"
(exit 0)
```

- ★★★ **`init calls 1`** — 8 스레드가 `Barrier` 로 **동시에 출발해** `get_or_init` 을 불렀는데 초기화 클로저(안에 50ms 잠)는 **한 번만** 돌았고, **8 스레드가 받은 `&String` 의 주소가 전부 같다**(`all got the same &String true`).
- ★★ 나머지 7 스레드는 **초기화가 끝날 때까지 기다렸다가** 같은 값을 받는다 — 두 번째 클로저는 **아예 실행되지 않는다.**
- ★★ **`[1]` `get()` 은 `None`** — `OnceLock` 은 **처음 부르는 쪽이** 채운다. **`[3]` 이미 채워진 뒤의 `set` 은 `Err("other")`** — 넣으려던 값을 **돌려준다**(버리지 않는다).

**20판을 돌리면.**

```text
===== 소스: r53_oncelock.sh =====
# 같은 프로그램을 20판 — 판마다 [2] 줄의 init calls 값을 모아 가짓수를 센다
rustc --edition 2021 -o r53_oncelock r53_oncelock.rs || exit 1
for i in $(seq 20); do ./r53_oncelock | sed -n 's/.*init calls \([0-9]*\) .*/init calls \1/p'; done | sort | uniq -c
===== bash r53_oncelock.sh =====
     20 init calls 1
(exit 0)
```

- ★★★ **20판 전부 `init calls 1`** — 가짓수가 **하나**다(`sort | uniq -c`). 그런데 **근거는 20판이 아니라 docs** 다 — 「it is **guaranteed** that only one function will be executed **if the function doesn't panic**」.
- ★★ **단서가 붙어 있다 — 「패닉하지 않으면」.** 초기화가 패닉하면 칸은 **비어 있는 채로** 남고(`get_or_init` §Panics) 다음 호출이 다시 시도한다. **이 문서는 그 판을 던지지 않았다.**

**`LazyLock` 은 초기화 클로저를 선언 자리에 붙인다.**

```text
===== 소스: r53_lazylock.rs =====
use std::collections::HashMap;
use std::sync::atomic::{AtomicUsize, Ordering::SeqCst};
use std::sync::LazyLock;
use std::thread;

static INIT_CALLS: AtomicUsize = AtomicUsize::new(0);

static TABLE: LazyLock<HashMap<&'static str, u32>> = LazyLock::new(|| {
    INIT_CALLS.fetch_add(1, SeqCst);
    HashMap::from([("a", 1), ("b", 2)])
});

fn main() {
    println!("[1] program started   init calls {}", INIT_CALLS.load(SeqCst));
    let sum: u32 = thread::scope(|s| {
        let hs: Vec<_> = (0..8).map(|_| s.spawn(|| TABLE["a"] + TABLE["b"])).collect();
        hs.into_iter().map(|h| h.join().unwrap()).sum()
    });
    println!("[2] 8 threads read    init calls {}  sum {}", INIT_CALLS.load(SeqCst), sum);
}
===== rustc --edition 2021 r53_lazylock.rs =====
(exit 0)
===== ./r53_lazylock =====
[1] program started   init calls 0
[2] 8 threads read    init calls 1  sum 24
(exit 0)
```

- ★★★ **`[1]` 프로그램이 시작돼도 `init calls 0`** — `static` 인데 **첫 접근 전까지 안 돈다**(docs: 「initialized on the **first access**」). **`[2]` 8 스레드가 읽은 뒤 `init calls 1`**, 값은 `sum 24`(= 8 × 3).
- ★★ `TABLE["a"]` 처럼 **그냥 값처럼 쓴다** — `LazyLock<T>` 가 `Deref<Target = T>` 이기 때문이다([43번 주제](../43-deref-coercion-and-smart-pointers/)). `OnceLock` 은 부르는 자리마다 `get_or_init(…)` 을 써야 한다.

| | `OnceLock<T>` | `LazyLock<T>` |
|---|---|---|
| 초기화 코드는 어디에 | **부르는 자리**(`get_or_init(f)`) — 부를 때마다 달라도 된다 | **선언 자리**(`LazyLock::new(f)`) — 하나로 고정 |
| 쓰는 모양 | `CONFIG.get_or_init(\|\| …)` · `get()` 은 `Option` | `*TABLE` · `TABLE[…]` — `Deref` |
| 밖에서 값을 넣기 | ★ **`set(v)`** — 이미 있으면 `Err(v)` | 없다 |
| 초기화가 패닉하면 | 칸은 **빈 채로** 남는다(docs §Panics) | ★ 락이 **중독된다**(docs §Poisoning) — **던지지 않았다** |
| Stable | **1.70.0** | **1.80.0** |
| 단일 스레드 판([42번 주제](../42-refcell-cell-interior-mutability/)) | `OnceCell` | `LazyCell` |

### (5) ★★ 언제부터 되나 — 로컬 문서의 「Stable since」

```text
===== 소스: r53_since.sh =====
# 로컬 rust-docs(1.92.0) 의 「Stable since」 표지를 읽는다
D="$(rustc --print sysroot)/share/doc/rust/html/std/sync"
first() { grep -o -E "$1" "$2" | sed -n 1p; }
echo "OnceLock             $(first 'Stable since Rust version [0-9.]+' $D/struct.OnceLock.html)"
echo "LazyLock             $(first 'Stable since Rust version [0-9.]+' $D/struct.LazyLock.html)"
echo "Mutex::new           $(first 'const since [0-9.]+"[^§]{0,300}method\.new' $D/struct.Mutex.html | grep -o -E 'const since [0-9.]+')"
echo "Mutex::clear_poison  $(first 'version [0-9.]+"[^§]{0,400}method\.clear_poison' $D/struct.Mutex.html | grep -o -E 'version [0-9.]+')"
===== bash r53_since.sh =====
OnceLock             Stable since Rust version 1.70.0
LazyLock             Stable since Rust version 1.80.0
Mutex::new           const since 1.63.0
Mutex::clear_poison  version 1.77.0
(exit 0)
```

- ★★ **`OnceLock` 1.70.0 · `LazyLock` 1.80.0** — 1.80 이전 판을 지원하는 크레이트는 `LazyLock` 대신 `OnceLock` + 함수(`fn config() -> &'static …`)를 쓴다. (4)의 `r53_oncelock` 이 바로 그 모양이다.
- ★ **`Mutex::new` 의 `const` 1.63.0** — (3). **`clear_poison` 1.77.0** — [52번 주제](../52-mutex-rwlock-arc-and-poisoning/)의 중독.
- ★★ 그래서 **1.80 이상이면 `lazy_static!`·`once_cell` 없이** 이 문서의 모든 전역 초기화가 된다 — 이 문서의 소스는 **외부 크레이트를 하나도 쓰지 않는다.** 두 크레이트와 std 타입의 연혁은 **확인하지 않았다**(표지만 읽었다).

### (6) ★ `static mut` — 2024 에디션은 참조를 막는다

```text
===== 소스: r53_static_mut.rs =====
static mut COUNTER: u32 = 0;

fn main() {
    unsafe {
        COUNTER += 1;
        println!("{}", COUNTER);
    }
}
===== rustc --edition 2021 r53_static_mut.rs =====
warning: creating a shared reference to mutable static
 --> r53_static_mut.rs:6:24
  |
6 |         println!("{}", COUNTER);
  |                        ^^^^^^^ shared reference to mutable static
  |
  = note: for more information, see <https://doc.rust-lang.org/edition-guide/rust-2024/static-mut-references.html>
  = note: shared references to mutable statics are dangerous; it's undefined behavior if the static is mutated or if a mutable reference is created for it while the shared reference lives
  = note: `#[warn(static_mut_refs)]` (part of `#[warn(rust_2024_compatibility)]`) on by default

warning: 1 warning emitted

(exit 0)
===== ./r53_static_mut =====
1
(exit 0)
===== rustc --edition 2024 -o r53_static_mut_2024 r53_static_mut.rs =====
error: creating a shared reference to mutable static
 --> r53_static_mut.rs:6:24
  |
6 |         println!("{}", COUNTER);
  |                        ^^^^^^^ shared reference to mutable static
  |
  = note: for more information, see <https://doc.rust-lang.org/edition-guide/rust-2024/static-mut-references.html>
  = note: shared references to mutable statics are dangerous; it's undefined behavior if the static is mutated or if a mutable reference is created for it while the shared reference lives
  = note: `#[deny(static_mut_refs)]` (part of `#[deny(rust_2024_compatibility)]`) on by default

error: aborting due to 1 previous error

(exit 1)
```

- ★★ **2024 에서 `static mut` 의 공유 참조는 기본 거부(`#[deny(static_mut_refs)]`)** — `println!` 이 `COUNTER` 의 **참조**를 만들기 때문이다. `unsafe` 블록 안인데도 막힌다. 2021 에서는 같은 줄이 **경고**다. 에디션의 정본은 목록의 **47번 주제**다 — 여기서는 「**전역 가변 상태는 (1)·(3)·(4)의 도구로**」 한 줄만 챙긴다.

## 문법 — 형태와 규칙

```text
   use std::sync::atomic::{AtomicUsize, Ordering};
   use std::sync::{LazyLock, Mutex, OnceLock};

   static HITS: AtomicUsize = AtomicUsize::new(0);        // const fn — static 에 바로
   static LOG: Mutex<Vec<String>> = Mutex::new(Vec::new()); // const fn (1.63+)
   static CONFIG: OnceLock<String> = OnceLock::new();     // 부르는 쪽이 채운다
   static TABLE: LazyLock<Vec<u32>> = LazyLock::new(|| vec![1, 2, 3]); // 첫 접근에 채운다

   HITS.fetch_add(1, Ordering::Relaxed);   // RMW 한 번 — 이전 값을 돌려준다
   HITS.load(Ordering::SeqCst);            // 읽기
   CONFIG.get_or_init(|| load_config());   // 초기화 클로저는 한 번만 (패닉하지 않으면)
   let n = TABLE.len();                    // Deref
```

- ★★★ **원자성은 연산 하나까지 — 두 연산 사이는 비어 있다**((1)).
- ★★★ **`Ordering` 은 그 변수의 원자성이 아니라 다른 메모리와의 순서를 정한다** — 카운터는 `Relaxed` 로 충분하고, 깃발은 최소 `Release`/`Acquire`, 「쓰고 남의 것 읽기」 짝은 `SeqCst`((2)).
- ★★ **`static` 초기화식은 `const` 여야 한다** — 할당하면 E0010/E0015, 그때 `LazyLock`((3)).
- ★★ **`OnceLock`/`LazyLock` 의 초기화는 한 번만 — 패닉하지 않으면**((4)).

## 어디서 틀리나

### 1. ★★★ 「원자 타입을 썼으니 스레드 안전하다」

(1)의 `load_then_store` — **`AtomicUsize` 인데 20판 전부 잃었다.** 원자 연산 **두 개**를 이어 쓰면 그 사이가 비어 있다. 읽고-고치고-쓰기는 **`fetch_add`·`compare_exchange` 한 번**으로 한다.

### 2. ★★★ 「`SeqCst` 로 올리면 그 틈도 막힌다」

(1) — `load_then_store` 는 **이미 `SeqCst`** 였다. 순서는 **원자성을 늘리지 않는다.**

### 3. ★★★ 「카운터는 `SeqCst` 라야 정확하다」

(1) — **`Relaxed` 도 20/20** 이고, 근거는 docs(RMW 의 원자성)다. 카운터에 순서가 필요한 것은 **그 값을 다른 데이터의 신호로 쓸 때**뿐이다.

### 4. ★★★ 「x86 에서는 `Relaxed` 도 `SeqCst` 처럼 동작한다」

(2)의 `sb` — **x86 에서도 `Relaxed`·`Release`/`Acquire` 가 둘 다 0 을 읽는 판을 판마다 냈다.** x86 이 막아 주는 것은 MP 쪽 재배치뿐이다.

### 5. ★★★ 「내 머신에서 `Relaxed` 깃발이 안 깨졌으니 괜찮다」

(2)의 `mp` — `0 / 10` 은 **x86 이 안 바꾼 것**이지 Rust 가 약속한 것이 아니다. 깃발에는 **`Release`(쓰기)/`Acquire`(읽기)** 를 쓴다 — 그 짝은 명세가 약속한다.

### 6. ★★ 「전역 `Vec` 은 `static` 에 `vec![]` 로 두면 된다」

(3) — **E0010 + E0015.** 컴파일러의 `note:` 대로 **`LazyLock::new(|| …)`**.

### 7. ★★ 「전역 지연 초기화에는 `lazy_static!` 이 필요하다」

(4)·(5) — **1.70 부터 `OnceLock`, 1.80 부터 `LazyLock`** 이 std 에 있다. 전역 `Mutex`·원자 타입은 애초에 `const` 로 된다((3)).

### 8. ★ 「atomic 은 락이 없으니 `Mutex` 보다 빠르다」

**이 문서는 재지 않았다.** 적을 수 있는 차이는 **무엇을 묶을 수 있나**뿐이다 — 원자 연산은 한 연산, `Mutex` 는 임의의 구간((1)).

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| `fetch_add` 는 읽기-수정-쓰기가 **한 원자 연산**이다 | ★ **std 의 계약**(원자 타입 문서) | (1) 20/20 과 어긋나지 않음 |
| `load` + `store` 사이에 끼어들 수 있다 | ★ **언어의 메모리 모델**(두 연산은 두 연산) | (1) 0/20 |
| `load_then_store` 가 **20판 전부** 잃는다 | ★ **이 머신 · 이 부하의 관찰** — 보장이 아니다 | (1) |
| `Relaxed`·`Release`/`Acquire` 가 SB 결과를 **허락**한다 · `SeqCst` 는 금지 | ★ **언어**(C++20 모델을 따른다 — atomic 모듈 문서) | (2) |
| SB 가 x86 에서 **실제로 나온다** | ★ **하드웨어**(x86-TSO 의 저장 버퍼) · 이 머신 관찰 | (2) 10/10 |
| MP 가 x86 에서 `Relaxed` 로도 **안 나온다** | ★ **하드웨어의 성질** — Rust 는 약속하지 않는다 | (2) 0/10 |
| `OnceLock`/`LazyLock` 초기화가 한 번만 | ★ **std 의 계약**(「guaranteed … if the function doesn't panic」) | (4) 20/20 |
| `LazyLock` 이 첫 접근에서 초기화된다 | ★ **std 의 계약** | (4) `init calls 0` → `1` |
| `static` 초기화식은 `const` 여야 한다 | ★ **언어**(컴파일러가 E0010·E0015 로 강제) | (3) |
| `Mutex::new`·`AtomicUsize::new` 가 `const fn` | ★ **std 의 시그니처**(1.63.0 표지) | (3)·(5) |
| `static_mut_refs` 가 2024 에서 deny | ★ **언어 · 에디션**(린트 수준) | (6) |
| `set` 이 `Err` 에 넣으려던 값을 돌려준다 | ★ **std 의 시그니처**(`Result<(), T>`) | (4) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 근거 |
|---|---|---|
| 숫자 하나를 여럿이 올리고 **끝에 합계만** 읽는다 | ★ **`AtomicUsize::fetch_add(…, Relaxed)`** | (1) |
| 값 **둘 이상**을 함께 바꾼다 · 읽고 판단하고 쓴다 | ★ **`Mutex`**(또는 `compare_exchange` 루프 — 이 문서는 던지지 않았다) | (1) — 원자 연산은 한 연산까지 |
| 「준비됐다」 깃발로 **다른 데이터**를 넘긴다 | **`store(…, Release)` / `load(…, Acquire)`** | (2)의 MP |
| 두 스레드가 각자 쓰고 **남의 것을 읽어** 판단한다 | **`SeqCst`**(또는 락) | (2)의 SB |
| 전역 카운터 · 전역 `Mutex<Vec<_>>`(빈 채로 시작) | **`static` 에 `const fn` 으로 바로** | (3) |
| 실행 중에만 만들 수 있는 전역 값, 초기화 코드가 하나 | ★ **`LazyLock`** | (4) |
| 초기화 코드가 부르는 자리마다 다르다 · 밖에서 한 번 넣는다 | **`OnceLock`**(`get_or_init` · `set`) | (4) |
| `static mut` | ★ **쓰지 않는다** — 위의 도구로 바꾼다 | (6) |

## 핵심 문장

- ★★★ **원자성은 연산 하나까지다 — `load` 와 `store` 를 이어 쓰면 원자 타입이어도 잃는다. 읽고-고치고-쓰기는 RMW 한 번으로.**
- ★★★ **`Ordering` 은 그 변수의 원자성이 아니라 다른 메모리와의 순서를 정한다 — 카운터는 `Relaxed` 로 충분하다.**
- ★★★ **x86 에서도 SB 재배치는 나온다 — `Release`/`Acquire` 로는 못 막고 `SeqCst` 라야 막는다. MP 가 안 나온 것은 x86 의 성질이지 Rust 의 약속이 아니다.**
- ★★ **`static` 에는 `const fn` 으로 만든 값만 바로 들어간다 — 할당이 필요하면 `LazyLock`(컴파일러가 그렇게 권한다).**
- ★★ **`OnceLock`/`LazyLock` 의 초기화 클로저는 여러 스레드가 동시에 와도 한 번만 돈다 — 패닉하지 않으면.**

## 관련 자료

- [**52번 주제**](../52-mutex-rwlock-arc-and-poisoning/) — `Mutex` 가 데이터를 감싸는 이유 · 가드 · 중독. **그쪽은 락, 여기는 락 없이 되는 경우와 전역 초기화.**
- [**41번 주제**](../41-rc-arc-shared-ownership-and-weak-cycles/) — `Arc` 의 계수가 원자적이라는 점(`Rc` 와의 차이). **여기는 원자 연산을 직접 쓴다.**
- [**42번 주제**](../42-refcell-cell-interior-mutability/) — `OnceCell`·`LazyCell` 은 이 편 두 타입의 **단일 스레드 판**이다(std `cell` 모듈 문서).
- [**50번 주제**](../50-send-sync-in-compiler-errors/) — `static` 값이 `Sync` 여야 하는 이유의 에러 읽기.
- 목록의 **47번 주제**(에디션 — `static mut` 참조 금지의 정본) · **56번 주제**(`unsafe`).
- [Go 33번](../../../go/syntax/33-sync-atomic-and-sync-map/) — Go 의 `sync/atomic` 과 `sync.Map`. **그쪽은 Go 의 원자 타입과 맵, 여기는 Rust 의 `Ordering` 인자와 전역 초기화.**
- [Java 55번](../../../java/syntax/55-atomics-and-concurrent-collections/) — `AtomicInteger` 와 동시성 컬렉션. **그쪽은 JVM, 여기는 Rust.**

## 용어 풀이

- **`AtomicUsize` 등 원자 타입** — `&self` 로 원자 연산(`load`·`store`·`fetch_add`·`compare_exchange`)을 주는 타입. `Sync` 라 `static` 에 두고 여러 스레드가 부른다.
- **RMW(읽기-수정-쓰기)** — 읽고 고치고 쓰기를 한 원자 연산으로 하는 것.
- **`Ordering`** — 원자 연산이 **다른 메모리 접근과** 어떤 순서를 지키나. `Relaxed`(없음) · `Release`(쓰기 — 앞의 쓰기를 먼저) · `Acquire`(읽기 — 뒤의 읽기를 나중에) · `AcqRel` · `SeqCst`(모두가 같은 전체 순서).
- **리트머스 테스트(litmus test)** — 메모리 모델이 허락하는 결과가 실제로 나오나 보는 아주 작은 두 스레드 프로그램.
- **SB(store buffering)** — 두 스레드가 각자 쓰고 남의 것을 읽는 리트머스. 둘 다 옛 값을 읽으면 「쓰기 뒤의 읽기」가 앞당겨진 것이다.
- **MP(message passing)** — 데이터를 쓰고 깃발을 세우는 쪽과, 깃발을 보고 데이터를 읽는 쪽의 리트머스.
- **x86-TSO** — x86 의 메모리 모델. 쓰기가 저장 버퍼에 머물 수 있어 **쓰기 뒤의 읽기**만 앞당겨진다.
- **`OnceLock<T>`** — 한 번만 쓸 수 있는 스레드 안전 칸. `get_or_init` · `get` · `set`.
- **`LazyLock<T>`** — 첫 접근에 선언 자리의 클로저로 초기화되는 스레드 안전 칸. `Deref` 로 값처럼 쓴다.
- **`const fn`** — 컴파일 시점에 부를 수 있는 함수. `static` 초기화식에 쓸 수 있다.

## 더 들어가면

- **`compare_exchange` 루프** — `fetch_add` 로 안 되는 갱신(최댓값 갱신 등)을 락 없이 하는 표준 모양. **이 문서는 던지지 않았다.** `fetch_max` 같은 전용 RMW 가 있으면 그쪽이 먼저다.
- **`AcqRel`** — RMW 에 Release 와 Acquire 를 함께 붙이는 순서. 리트머스에 넣지 않았다.
- **약한 메모리 CPU 에서의 MP** — aarch64 머신에서 (2)의 `mp relaxed` 를 다시 돌리면 이 문서의 「못 잰 것」 칸이 채워진다.
- **`LazyLock` 중독** — 초기화 클로저가 패닉하면 이후 접근도 패닉한다(docs §Poisoning). **던지지 않았다.**
