# rust/syntax/53 — `atomic`·`OnceLock`/`LazyLock` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64` · 논리 코어 24** 에서
> **`rustc --edition 2021`** 로(격자 둘은 `-O` · 6번만 2024) 실제로 돌려 받은 것이다.\
> ★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
> ★★ 블록 첫 줄 `===== 소스: <파일> =====` 아래가 **돌린 소스 전문**이고, **진단의 줄 번호는 그 파일 기준**이다.\
> ★ 1번·2번의 **판 수(`N / 20` · `N / 10`)는 흔들리는 칸**이다(서머리 머리말의 표). 근거로 쓰는 것은 「**한 판이라도**」와 명세다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ `1 / 4` — 원자 연산 둘을 이은 `load_then_store` 만 잃는다

**출력**

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

**왜 그런가**

- ★★★ **`load_then_store` — `0 / 20`, 한 판이라도 잃었다(`yes`).** `load` 와 `store` 가 **각각은** 원자적이지만 둘 사이에 다른 스레드의 `load` 가 끼어들어 같은 값을 두 번 쓴다.
- ★★★ **`SeqCst` 는 영향을 안 준다** — 순서는 「다른 메모리와 어떤 순서로 보이나」를 정할 뿐, **두 연산을 한 연산으로 만들지 않는다.**
- ★★ **`fetch_add` 는 `Relaxed`·`SeqCst` 둘 다 `20 / 20`** — RMW **한 번**이라 끼어들 자리가 없다. `Mutex` 도 `20 / 20`.
- ★ `20 / 20` 의 근거는 판 수가 아니라 **docs**(원자 RMW)다. `0 / 20` 의 「전부」는 이 머신 · 이 부하의 관찰이다.

### 2. ★★★ `sb` 가 갈린다 — `relaxed`·`release_acquire` 는 `10 / 10`, `seqcst` 는 `0 / 10` · `mp` 는 셋 다 `0 / 10`

**출력**

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

**왜 그런가**

- ★★★ **`sb` — 둘 다 0 을 읽은 판이 약한 두 순서에서 판마다 나왔다.** 내가 쓴 값이 **저장 버퍼**에 있는 동안 뒤의 읽기가 먼저 끝나 상대의 옛 값(0)을 본다. x86 도 이 재배치는 한다.
- ★★★ **`seqcst` 는 `0 / 10`** — `SeqCst` 연산은 모든 스레드가 **같은 전체 순서**로 보므로 두 읽기가 둘 다 0 일 수 없다(docs `Ordering::SeqCst`).
- ★★ **`mp` 는 셋 다 `0 / 10`** — x86 은 쓰기끼리·읽기끼리의 순서를 바꾸지 않는다. **그래서 `relaxed` 도 안 나왔다.**
- ★★★ **브리핑의 전제(「x86 에서는 순서 차이를 재현하기 어렵다」)는 절반만 맞았다** — `mp` 는 그랬고 `sb` 는 **판마다** 재현됐다.

### 3. ★★ `init calls 1` · 주소 전부 같다 · `set` 은 `Err("other")` — 20판이 한 가지

**출력**

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

```text
===== 소스: r53_oncelock.sh =====
# 같은 프로그램을 20판 — 판마다 [2] 줄의 init calls 값을 모아 가짓수를 센다
rustc --edition 2021 -o r53_oncelock r53_oncelock.rs || exit 1
for i in $(seq 20); do ./r53_oncelock | sed -n 's/.*init calls \([0-9]*\) .*/init calls \1/p'; done | sort | uniq -c
===== bash r53_oncelock.sh =====
     20 init calls 1
(exit 0)
```

**왜 그런가**

- ★★★ **8 스레드가 동시에 와도 초기화 클로저는 한 번** — 나머지는 끝날 때까지 기다렸다가 **같은 `&String`** 을 받는다. docs: 「it is guaranteed that only one function will be executed **if the function doesn't panic**」.
- ★★ **`[1]` `get()` 은 `None`** — 누군가 처음 부를 때까지 비어 있다. **`[3]` 채워진 뒤의 `set` 은 `Err`** 로 넣으려던 값을 돌려준다. **`[4]`** 값은 처음 것(`"loaded"`) 그대로.
- ★★ 20판의 가짓수는 **`init calls 1` 하나**(20번) — 근거는 20판이 아니라 위 docs 문장이다.

### 4. ★★ `[1]` 은 0, `[2]` 는 1 — `sum 24`

**출력**

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

**왜 그런가**

- ★★★ **`static` 이어도 첫 접근 전에는 안 돈다** — docs: 「A value which is initialized on the **first access**」. `main` 이 시작한 뒤 `[1]` 을 찍을 때까지 아무도 `TABLE` 을 안 만졌다.
- ★★ 8 스레드가 각각 `TABLE["a"] + TABLE["b"]`(= 3)를 읽어 **`sum 24`**, 초기화는 **한 번**. `TABLE[…]` 이 되는 것은 `LazyLock` 이 `Deref` 이기 때문이다.

### 5. ★★ 앞은 통과(`hits 1`) · 뒤는 E0010 + E0015 — 권하는 것은 `LazyLock::new`

**출력**

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

**왜 그런가**

- ★★ **`AtomicUsize::new`·`Mutex::new`·`Vec::new` 는 `const fn`** 이라 `static` 초기화식에 바로 들어간다(`Mutex::new` 의 `const` 는 1.63.0 — 서머리 (5)).
- ★★★ **`vec![1, 2, 3]` 은 힙 할당**(E0010 「allocations are not allowed in statics」)이고 `const` 아닌 함수를 부른다(E0015). `= note:` 가 **「consider wrapping this expression in `std::sync::LazyLock::new(|| ...)`」** 를 권한다.

### 6. ★ 2024 는 에러(`static_mut_refs` deny) · 2021 은 경고

**출력**

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

**왜 그런가**

- ★★ **`println!` 이 `COUNTER` 의 공유 참조를 만든다** — 2024 에서 `#[deny(static_mut_refs)]` 가 기본이라 `unsafe` 안이어도 **컴파일 에러**. 2021 에서는 같은 린트가 `warn` 이라 **경고 1개와 함께 통과**한다(위 블록의 첫 판 — `warning: 1 warning emitted` · 실행 `1`). 정본은 [목록의 **47번 주제**](../47-editions-2021-vs-2024-and-cargo-fix/).
- ★ 처방은 `static mut` 을 버리고 **원자 타입 · `Mutex` · `OnceLock`/`LazyLock`**(1·3·4·5번)으로 바꾸는 것이다.

### 7. ★★★ 원자성은 연산 하나까지 — 순서는 원자성을 늘리지 않는다

- ★★★ `load` → (다른 스레드의 `load`) → `store` → (다른 스레드의 `store`) 가 일어나면 **두 증가가 한 번**이 된다. 각 연산이 원자적이어도 **두 연산 사이**는 보호받지 않는다.
- ★★★ **`SeqCst`** 는 원자 연산들이 모든 스레드에 **같은 순서로 보이게** 할 뿐이다 — 「같은 순서로 보이는 두 연산 사이에 남이 끼어드는 것」은 그대로 허락된다.
- ★★ **`fetch_add(1, Relaxed)`** 는 읽기·더하기·쓰기가 **한 원자 연산**이다. `Relaxed` 가 없애는 것은 **다른 메모리와의 순서**이지 이 연산의 원자성이 아니다(docs: 「No ordering constraints, **only atomic operations**」).

### 8. ★★★ Release/Acquire 는 「앞의 쓰기 → 깃발」과 「깃발 → 뒤의 읽기」를 묶는다 — 「쓰기 → 뒤의 읽기」는 `SeqCst` 만

- ★★★ **`mp`** — 쓰는 쪽의 `Release` 저장은 **그 앞의 쓰기**(데이터)가 먼저 보이게 하고, 읽는 쪽의 `Acquire` 읽기는 **그 뒤의 읽기**가 나중에 일어나게 한다. 깃발 1 을 봤으면 데이터도 본다 — **명세가 약속한다.**
- ★★★ **`sb`** — 문제의 짝은 한 스레드 안의 「**저장 → 그 뒤의 읽기**」다. Release 는 **뒤**를 묶지 않고 Acquire 는 **앞**을 묶지 않으므로 이 짝은 비어 있다 → 2번의 `release_acquire 10 / 10`.
- ★★ 막으려면 **`SeqCst`**(또는 락). 근거는 docs `Ordering::SeqCst` 의 「with the additional guarantee that **all threads see all sequentially consistent operations in the same order**」.

### 9. ★★★ `sb seqcst` 의 0 은 명세가 받치고, `mp relaxed` 의 0 은 x86 이 우연히 준 것이다

- ★★★ **`sb seqcst 0 / 10`** — 명세가 **금지**하는 결과다. 실행은 그 금지와 **어긋나지 않았다**는 확인일 뿐이지만, 어느 CPU 에서도 0 이어야 한다.
- ★★★ **`mp relaxed 0 / 10`** — Rust 의 규칙은 이 결과를 **허락**한다. x86 하드웨어가 안 만들었을 뿐이다 — **약한 메모리 CPU 에서는 나올 수 있고**(이 머신에 없어 **못 쟀다**), 컴파일러도 순서를 바꿀 수 있다. **같은 `0` 이라도 무게가 다르다.**
- ★★ **1번의 `20 / 20`** 도 같은 구조다 — `fetch_add` 는 **docs 가 받치는** 20/20 이고, 판 수는 그 확인이다. 리트머스는 「**나왔다**」는 증명하지만 「**안 나온다**」는 증명하지 못한다.

### 10. ★★ 고정된 표는 `LazyLock`(1.80.0) · 부르는 자리마다 다르거나 밖에서 넣으면 `OnceLock`(1.70.0) · 빈 `Mutex` 는 둘 다 필요 없다

- ★★ **`LazyLock`** — 초기화 코드를 **선언 자리**에 붙이고 `Deref` 로 값처럼 쓴다(4번). Stable **1.80.0**.
- ★★ **`OnceLock`** — `get_or_init(f)` 로 **부르는 자리**에서 초기화하거나 `set(v)` 로 **밖에서 한 번** 넣는다(3번). Stable **1.70.0**.
- ★★★ **전역 `Mutex<Vec<String>>` 을 빈 채로** — `Mutex::new(Vec::new())` 가 `const` 라 **`static` 에 바로** 된다(5번 · `const` 1.63.0). 두 도구 모두 필요 없다.

### 11. ★ `Mutex` 는 임의의 구간을, 원자 연산은 연산 하나를 묶는다

- ★★ **카운터** — `fetch_add(1, Relaxed)`(1번). 끝에 합계만 읽으면 순서가 필요 없다.
- ★★ **합계와 개수를 함께** — 값 **둘**을 한 덩어리로 바꿔야 하므로 **`Mutex`**([52번 주제](../52-mutex-rwlock-arc-and-poisoning/)). 원자 타입 둘을 따로 올리면 그 사이에 읽은 쪽이 **짝이 안 맞는 두 값**을 본다(7번과 같은 틈).
- ★★ **「준비됐다」 깃발** — 쓰는 쪽 `store(true, Release)` · 읽는 쪽 `load(Acquire)`(8번의 MP). `Relaxed` 가 x86 에서 안 깨진 것(2번)을 근거로 삼지 않는다.
- ★ **속도 비교는 하지 않았다** — 고르는 기준은 「무엇을 묶어야 하나」다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서·서머리의 **모든 블록** | `capture.sh` — 블록마다 명령을 배너에 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` 기본 규칙 넷 · **고칠 것 0** |
| ★★★ **원자 연산 격자** | `r53_count.sh` — 방법 넷 × 20판 · 8 스레드 × 100000 · `-O` | 80 실행 | **`cells that lost: 1 / 4`** |
| ★★★ **리트머스 격자** | `r53_litmus.sh` — SB·MP × 순서 셋 × 10판 × 판마다 200000회 · `-O` | 60 실행 | **`sb` 10 · 10 · 0 / `mp` 0 · 0 · 0** |
| ★★ **초기화 호출 수** | `r53_oncelock` 1판 + `r53_oncelock.sh` 20판 · `r53_lazylock` | 22 | **`init calls 1`**(가짓수 하나) · `0 → 1` |
| `static` 초기화식 | `r53_static_const` · `r53_static_vec` | 2 | 통과 · **E0010 + E0015**(`LazyLock` 권함) |
| 에디션 | `r53_static_mut`(2024) | 1 | **`static_mut_refs` deny** |
| 판 표지 | `r53_since` — 로컬 rust-docs grep | 1 | 1.70.0 · 1.80.0 · const 1.63.0 · 1.77.0 |
| **안 던진 것** — 속도 · `compare_exchange` 루프 · `AcqRel` · 초기화 패닉(`OnceLock` 빈 칸 · `LazyLock` 중독) · 약한 메모리 CPU | — | 0 | ★ 「안 던졌다」·「못 잰 것」으로 표시했다 |

**구현 의존 항목**(버전·환경이 바뀌면 **다시 찍어야 하는** 것).

| 항목 | 왜 |
|---|---|
| ★★★ 리트머스 격자 전체 | ★ **CPU 에 매인다** — aarch64 에서는 `mp relaxed` 칸이 달라질 수 있다 · 판 수는 부하에도 매인다 |
| 원자 연산 격자의 `load_then_store` 판 수 | ★ 코어 수 · 부하 · 최적화 수준 |
| E0015 의 `note:`(`LazyLock::new` 권유) | ★ rustc 진단의 제안 — 판에 매인다 |
| `set` 의 `Err("other")` 모양 · `Debug` 문구 | ★ std 구현 |

★ **다시 찍는 법** — `capture.sh <새 디렉토리>` 를 그대로 돌리고 `normalize-shaky.py <원본> <새 디렉토리>` 로 견준다.
