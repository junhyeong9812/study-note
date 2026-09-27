# rust/syntax/53 — `atomic`·`OnceLock`/`LazyLock` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 던지는 법 — `rustc --edition 2021 <파일>.rs`. 격자는 `bash <파일>.sh`(격자 둘은 `-O` 로 빌드한다). **외부 크레이트를 하나도 쓰지 않는다.**
> ★ 이 머신은 `x86_64` 다 — 2번의 답은 **CPU 에 매인다.** 다른 CPU 에서 돌리면 답이 달라질 수 있는 칸이 있다.
> ★★★ **원자 연산을 보면 먼저 물어라** — 「**이 갱신은 원자 연산 몇 개로 되어 있나 — 그리고 이 값을 다른 데이터의 신호로 쓰나**」.
> ★ **문항 11개 중 코드가 붙은 예측형은 6개**다. 소스 펜스는 캡처가 실파일에서 찍었다(`check-source-fences.py` 대조).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 카운터를 올리는 네 가지 방법 (예측)

```rust
// r53_count.rs
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
```

```bash
# r53_count.sh
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
```

- 네 줄의 `runs equal to 800000` 칸(`N / 20`)과 `lost in at least one run` 칸은? 마지막 줄의 `N / 4` 는?
- ★ 셋째 방법은 `SeqCst` 를 썼다. 그것이 결과에 영향을 주나?

### 2. ★★★ 두 리트머스 × 세 순서 (예측)

```rust
// r53_litmus.rs
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
```

```bash
# r53_litmus.sh
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
```

- 여섯 줄의 `N / 10` 은? 이 머신(x86_64)에서 **`sb` 와 `mp` 중 어느 쪽이** 순서에 따라 갈리나?

### 3. ★★ 여덟 스레드가 동시에 부르는 `get_or_init` (예측)

```rust
// r53_oncelock.rs
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
```

```bash
# r53_oncelock.sh
# 같은 프로그램을 20판 — 판마다 [2] 줄의 init calls 값을 모아 가짓수를 센다
rustc --edition 2021 -o r53_oncelock r53_oncelock.rs || exit 1
for i in $(seq 20); do ./r53_oncelock | sed -n 's/.*init calls \([0-9]*\) .*/init calls \1/p'; done | sort | uniq -c
```

- 네 줄의 출력은? 20판을 돌린 스크립트는 몇 가지 줄을 몇 번씩 내나?

### 4. ★★ `static` 에 둔 `LazyLock` 은 언제 도나 (예측)

```rust
// r53_lazylock.rs
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
```

- `[1]` 과 `[2]` 의 `init calls` 는 각각 몇인가? `sum` 은?

### 5. ★★ `static` 초기화식 두 가지 (예측)

```rust
// r53_static_const.rs
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Mutex;

static HITS: AtomicUsize = AtomicUsize::new(0);
static LOG: Mutex<Vec<String>> = Mutex::new(Vec::new());

fn main() {
    HITS.fetch_add(1, Ordering::Relaxed);
    LOG.lock().unwrap().push(String::from("first"));
    println!("hits {}  log {:?}", HITS.load(Ordering::Relaxed), LOG.lock().unwrap());
}
```

```rust
// r53_static_vec.rs
static TABLE: Vec<u32> = vec![1, 2, 3];

fn main() {
    println!("{:?}", TABLE);
}
```

- 각각 컴파일되는가? 안 된다면 에러 번호는 무엇이고, 컴파일러가 **대신 쓰라고 권하는 것**은?

### 6. ★ 2024 에디션의 `static mut` (예측)

```rust
// r53_static_mut.rs
static mut COUNTER: u32 = 0;

fn main() {
    unsafe {
        COUNTER += 1;
        println!("{}", COUNTER);
    }
}
```

- `rustc --edition 2024` 로 컴파일되는가? 안 된다면 어느 린트가 무엇을 막나 — 2021 에서는?

### 7. ★★★ 원자 연산 둘을 이어 쓰면 (왜)

- `load` 와 `store` 는 각각 원자 연산인데 1번의 셋째 방법은 왜 잃나? 순서를 `SeqCst` 로 올려도 왜 안 고쳐지나 — 그리고 `Relaxed` 의 `fetch_add` 는 왜 되나?

### 8. ★★★ `Release`/`Acquire` 가 막는 것과 못 막는 것 (왜)

- 2번에서 `release_acquire` 는 `mp` 에서 무엇을 약속하고 `sb` 에서는 왜 약속하지 못하나? `sb` 를 막으려면 무엇이 필요하고, docs 의 어느 문장이 그 근거인가?

### 9. ★★★ 리트머스의 빈 칸을 어떻게 읽나 (경계)

- 2번에서 `0 / 10` 이 나온 칸들은 모두 같은 무게의 근거인가 — 각각 무엇이 보장하고 무엇이 관찰일 뿐인가? 1번의 `20 / 20` 은?

### 10. ★★ `OnceLock` 과 `LazyLock` 중 무엇을 (경계)

- 초기화 코드가 하나로 고정된 전역 표와, 부르는 자리에 따라 초기화 방법이 다르거나 밖에서 한 번 넣는 설정값은 각각 어느 것이 알맞나? 각각 **몇 판부터** Stable 인가 — 전역 `Mutex<Vec<String>>` 을 빈 채로 두는 데는 둘 중 무엇이 필요한가?

### 11. ★ 락 없이 되는 경우 (연결)

- [52번 주제](../52-mutex-rwlock-arc-and-poisoning/)의 `Mutex` 와 이 편의 원자 연산은 각각 **얼마만큼**을 한 덩어리로 묶을 수 있나? 숫자 하나를 올리는 카운터 · 합계와 개수를 함께 바꾸는 통계 · 「준비됐다」 깃발 셋에 각각 무엇을 고르나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
