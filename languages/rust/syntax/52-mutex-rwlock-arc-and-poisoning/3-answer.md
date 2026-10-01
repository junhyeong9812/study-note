# rust/syntax/52 — `Mutex`/`RwLock` 과 `Arc<Mutex<T>>` · 중독 — 정답

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ `13 / 24` — `match`·`if let`(then)·`while let` 은 쥐고, `if` 조건은 놓는다 · 에디션이 가른 것은 `if let` 의 else 행

**출력**

```text
===== 소스: r52_grid.sh =====
# 가드를 쥐는 모양마다 프로그램을 만들어 두 에디션으로 던진다.
# probe() 는 그 자리에서 m.try_lock() 을 불러, 첫 번째 가드가 아직 살아 있나를 멈추지 않고 본다.
S=$'\x1f'
cases=(
  "let g = lock; probe in same scope${S}let g = m.lock().unwrap(); probe(&m); let _ = g.len();"
  "let _g = lock; probe in same scope${S}let _g = m.lock().unwrap(); probe(&m);"
  "let g in inner block, probe after block${S}{ let g = m.lock().unwrap(); let _ = g.len(); } probe(&m);"
  "let g, drop(g), probe${S}let g = m.lock().unwrap(); drop(g); probe(&m);"
  "temporary in its own statement, probe next${S}m.lock().unwrap().push(1); probe(&m);"
  "let n = lock.len(); probe${S}let n = m.lock().unwrap().len(); probe(&m); let _ = n;"
  "one statement: guard receiver + probe argument${S}m.lock().unwrap().push(probe(&m));"
  "match on lock.len(), probe in arm${S}match m.lock().unwrap().len() { _ => { probe(&m); } };"
  "if condition lock.len(), probe in body${S}if m.lock().unwrap().len() < 9 { probe(&m); };"
  "if let on lock.first(), probe in then${S}if let Some(_) = m.lock().unwrap().first().copied() { probe(&m); };"
  "if let on lock.first(), probe in else${S}if let Some(_) = m.lock().unwrap().get(9).copied() { } else { probe(&m); };"
  "while let on lock.pop(), probe in body${S}while let Some(_) = m.lock().unwrap().pop() { probe(&m); };"
)
printf 'case\tedition 2021\tedition 2024\n'
b=0; m=0
for spec in "${cases[@]}"; do
  label=${spec%%"$S"*}
  body=${spec#*"$S"}
  printf 'use std::sync::Mutex;\nfn probe(m: &Mutex<Vec<i32>>) -> i32 {\n    let free = m.try_lock().is_ok();\n    println!("{}", if free { "free" } else { "blocked" });\n    0\n}\nfn main() {\n    let m = Mutex::new(vec![1, 2, 3]);\n    %s\n}\n' "$body" > g.rs
  res=()
  for ed in 2021 2024; do
    rustc --edition "$ed" -A unused -o g g.rs 2>cc.txt || { echo "compile failed: $label ($ed)"; cat cc.txt; exit 1; }
    r=$(./g | head -n 1)
    res+=("$r")
    [ "$r" = blocked ] && b=$((b+1))
    m=$((m+1))
  done
  row="$label${S}${res[0]}${S}${res[1]}"
  cols=$(printf '%s' "$row" | awk -F"$S" '{print NF}')
  [ "$cols" = 3 ] || { echo "column count $cols != 3"; exit 1; }
  printf '%s\n' "$row" | tr "$S" '\t'
done
echo "blocked cells: $b / $m"
===== bash r52_grid.sh =====
case	edition 2021	edition 2024
let g = lock; probe in same scope	blocked	blocked
let _g = lock; probe in same scope	blocked	blocked
let g in inner block, probe after block	free	free
let g, drop(g), probe	free	free
temporary in its own statement, probe next	free	free
let n = lock.len(); probe	free	free
one statement: guard receiver + probe argument	blocked	blocked
match on lock.len(), probe in arm	blocked	blocked
if condition lock.len(), probe in body	free	free
if let on lock.first(), probe in then	blocked	blocked
if let on lock.first(), probe in else	blocked	free
while let on lock.pop(), probe in body	blocked	blocked
blocked cells: 13 / 24
(exit 0)
```

**왜 그런가**

- ★★ 1·2행 — 변수(`g` · `_g`)에 담긴 가드는 **스코프 끝까지** 산다 → `blocked`.
- ★★ 3·4·5·6행 — 블록 끝 · `drop(g)` · **자기 문장이 끝난 임시값** · `let n = ….len();` 의 문장 끝 → `free`.
- ★★★ 7행 — **한 문장 안**: 수신자 `m.lock().unwrap()` 의 가드가 인자 `probe(&m)` 평가 동안 살아 있다 → `blocked`.
- ★★★ 8행 대 9행 — `match` 의 조사 대상은 **문장 끝까지**(`blocked`), `if` 의 조건식은 **그 자체가 임시값 스코프**(`free`).
- ★★★ 10·11행 — `if let` 의 **then 본문은 두 에디션 다 `blocked`**, **else 갈래는 2021 `blocked` · 2024 `free`**. 두 열이 다른 행은 이 11행이다.
- ★★ 12행 — `while let` 은 **본문 내내** 쥔다(두 에디션 다).
- ★ 42번의 `RefCell` 판(`5 / 12` · `3 / 4`)과 **같은 규칙, 같은 답**이다 — 가드가 참조가 아니라 **값**이라 `Drop` 시점이 기준이다.

### 2. ★★★ E0499 — 컴파일러가 보는 것은 `count` 에 대한 가변 빌림 둘뿐이다

**출력**

```text
===== 소스: r52_wrap.rs =====
use std::sync::Mutex;
use std::thread;

fn main() {
    let mut count = 0;
    let lock = Mutex::new(());
    thread::scope(|s| {
        s.spawn(|| {
            let _g = lock.lock().unwrap();
            count += 1;
        });
        s.spawn(|| {
            let _g = lock.lock().unwrap();
            count += 1;
        });
    });
    println!("{}", count);
}
===== rustc --edition 2021 r52_wrap.rs =====
error[E0499]: cannot borrow `count` as mutable more than once at a time
  --> r52_wrap.rs:12:17
   |
 7 |       thread::scope(|s| {
   |                      - has type `&'1 Scope<'1, '_>`
 8 |           s.spawn(|| {
   |           -       -- first mutable borrow occurs here
   |  _________|
   | |
 9 | |             let _g = lock.lock().unwrap();
10 | |             count += 1;
   | |             ----- first borrow occurs due to use of `count` in closure
11 | |         });
   | |__________- argument requires that `count` is borrowed for `'1`
12 |           s.spawn(|| {
   |                   ^^ second mutable borrow occurs here
13 |               let _g = lock.lock().unwrap();
14 |               count += 1;
   |               ----- second borrow occurs due to use of `count` in closure
   |
note: requirement that the value outlives `'1` introduced here
  --> /rustc/ded5c06cf21d2b93bffd5d884aa6e96934ee4234/library/std/src/thread/scoped.rs:196:35

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0499`.
(exit 1)
```

**왜 그런가**

- ★★★ **E0499 — cannot borrow `count` as mutable more than once at a time.** 「first borrow occurs due to use of `count` in closure」 · 「second mutable borrow occurs here」 — **두 클로저가 `count` 를 가변으로 빌린 것이 겹친다.**
- ★★★ `lock` 이 그 둘을 떼어 놓는다는 사실은 **타입 어디에도 없다** — `Mutex<()>` 는 `()` 만 지킨다. 그래서 **데이터를 락 안에 넣는다**(7번).

### 3. ★★ `total 800000` · `strong after join 1`

**출력**

```text
===== 소스: r52_arc_mutex.rs =====
use std::sync::{Arc, Mutex};
use std::thread;

fn main() {
    let total = Arc::new(Mutex::new(0u64));
    let handles: Vec<_> = (0..8)
        .map(|_| {
            let t = Arc::clone(&total);
            thread::spawn(move || {
                for _ in 0..100_000 {
                    *t.lock().unwrap() += 1;
                }
            })
        })
        .collect();
    for h in handles {
        h.join().unwrap();
    }
    println!("total {}", *total.lock().unwrap());
    println!("strong after join {}", Arc::strong_count(&total));
}
===== rustc --edition 2021 r52_arc_mutex.rs =====
(exit 0)
===== ./r52_arc_mutex =====
total 800000
strong after join 1
(exit 0)
```

**왜 그런가**

- ★★ 가드는 `*t.lock().unwrap() += 1` **문장마다** 풀려(1번의 5행) 스레드끼리 번갈아 잡는다 → 잃지 않는다.
- ★★ `join` 으로 스레드가 끝나며 각자의 `Arc` 복제가 버려져 **`strong 1`** — 41번 (3)과 같은 모양이다.
- ★ 이 블록은 **값이 맞았다**는 것만 보인다. 속도는 재지 않았다.

### 4. ★★★ `lock()` 은 `Err` — 그래도 `into_inner` 로 `[1, 2, 3, 4]` 를 꺼낸다

**출력**

```text
===== 소스: r52_poison.rs =====
use std::sync::{Arc, Mutex};
use std::thread;

fn main() {
    let m = Arc::new(Mutex::new(vec![1, 2, 3]));
    let m2 = Arc::clone(&m);
    let r = thread::spawn(move || {
        let mut g = m2.lock().unwrap();
        g.push(4);
        panic!("failed while holding the guard");
    })
    .join();
    eprintln!("[1] child join is_err {}", r.is_err());
    eprintln!("[2] is_poisoned {}", m.is_poisoned());

    let r = m.lock();
    eprintln!("[3] lock() is_err {}", r.is_err());
    let e = r.unwrap_err();
    eprintln!("[4] Debug {:?}", e);
    eprintln!("[5] Display \"{}\"", e);
    let g = e.into_inner();
    eprintln!("[6] into_inner -> guard, data {:?}", *g);
    drop(g);

    eprintln!("[7] still poisoned after that {}", m.is_poisoned());
    m.clear_poison();
    eprintln!("[8] after clear_poison: is_poisoned {}  lock is_ok {}", m.is_poisoned(), m.lock().is_ok());
}
===== rustc --edition 2021 r52_poison.rs =====
(exit 0)
===== ./r52_poison =====

thread '<unnamed>' (3313307) panicked at r52_poison.rs:10:9:
failed while holding the guard
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
[1] child join is_err true
[2] is_poisoned true
[3] lock() is_err true
[4] Debug PoisonError { .. }
[5] Display "poisoned lock: another task failed inside"
[6] into_inner -> guard, data [1, 2, 3, 4]
[7] still poisoned after that true
[8] after clear_poison: is_poisoned false  lock is_ok true
(exit 0)
```

**왜 그런가**

- ★★★ **`[2] is_poisoned true` · `[3] lock() is_err true`** — 가드를 쥔 스레드가 패닉했다. std §Errors: 「this call will return an error **once the mutex is acquired**」.
- ★★ **`[4]`** `Debug` 는 `PoisonError { .. }`, **`[5]`** `Display` 는 `poisoned lock: another task failed inside`(std 구현의 문구).
- ★★★ **`[6]` 에 `4` 가 있다** — 패닉 **직전의** `push(4)` 가 남았다. 중독은 「망가졌다」가 아니라 「**중간 상태일 수 있다**」는 표시다.
- ★★ **`[7]`** 값을 꺼내도 표시는 남는다 · **`[8]`** `clear_poison()` 뒤에 `is_poisoned false`, `lock is_ok true`.

### 5. ★★ 읽기 중엔 `ok no` · 쓰기 중엔 `no no`

**출력**

```text
===== 소스: r52_rwlock.rs =====
use std::sync::RwLock;

fn show(held: &str, l: &RwLock<i32>) {
    println!(
        "{held:<12} try_read {:<5}  try_write {}",
        if l.try_read().is_ok() { "ok" } else { "no" },
        if l.try_write().is_ok() { "ok" } else { "no" }
    );
}

fn main() {
    let l = RwLock::new(0);
    show("nothing", &l);
    {
        let _r1 = l.read().unwrap();
        show("one read", &l);
        let _r2 = l.read().unwrap();
        show("two reads", &l);
    }
    {
        let _w = l.write().unwrap();
        show("one write", &l);
    }
    show("nothing", &l);
}
===== rustc --edition 2021 r52_rwlock.rs =====
(exit 0)
===== ./r52_rwlock =====
nothing      try_read ok     try_write ok
one read     try_read ok     try_write no
two reads    try_read ok     try_write no
one write    try_read no     try_write no
nothing      try_read ok     try_write ok
(exit 0)
```

**왜 그런가**

- ★★ 읽기 가드가 **하나든 둘이든** 읽기는 더 되고 쓰기는 안 된다. 쓰기 가드가 있으면 **둘 다** 안 된다. 「공유 여럿 또는 독점 하나」 — 42번 `RefCell` 과 같은 규칙이다.
- ★ 블록이 끝나 가드가 버려지면 다시 `ok ok`.
- ★ 이 블록은 **허용 조합**만 보인다. `RwLock` 과 `Mutex` 의 속도는 재지 않았다.

### 6. ★★ `[1]` 까지 · `(exit 124)` — 보장은 「돌아오지 않는다」까지

**출력**

```text
===== 소스: r52_relock.rs =====
use std::sync::Mutex;

fn main() {
    let m = Mutex::new(0);
    let _first = m.lock().unwrap();
    eprintln!("[1] first guard taken");
    let _second = m.lock().unwrap();
    eprintln!("[2] second guard taken");
}
===== rustc --edition 2021 r52_relock.rs =====
(exit 0)
===== timeout 2 ./r52_relock =====
[1] first guard taken
(exit 124)
```

**왜 그런가**

- ★★ 두 번째 `lock()` 이 돌아오지 않아 `timeout 2` 가 끊었다(`124` 는 `timeout` 의 종료 코드). **`[2]` 는 안 찍혔다.**
- ★★★ **std 는 이 경우를 「left unspecified」라고 적는다** — 「this function **will not return on the second call** (it might panic or deadlock, for example)」. **멈춘 것은 이 판·이 OS 의 관찰**이고, 보장은 「돌아오지 않는다」뿐이다.

### 7. ★★★ 데이터가 락 안에 있으면 「잠그고 고친다」가 타입이 된다 · 스코프 스레드는 빌림을 허용한다

- ★★★ 2번 — 컴파일러는 **`count` 에 대한 가변 빌림 둘**만 보고, 옆의 락이 그것을 지킨다는 것은 모른다 → E0499.
- ★★★ `count` 를 **`Mutex<i32>` 안에** 넣으면 `count` 에 닿는 길은 `lock()` 이 주는 **가드뿐**이다. 공유되는 것은 `&Mutex<i32>` 이고 `Mutex<i32>: Sync` 라 두 스레드가 나눠 가져도 된다(서머리 (2)의 `r52_wrap_fix` — `2`).
- ★★ **`Arc` 가 필요 없는 이유** — `thread::scope` 는 스코프 끝에서 스레드를 기다리므로 **지역 값을 빌려 줄 수 있다**(49번). `Arc` 는 `thread::spawn` 처럼 `'static` 을 요구할 때의 값이다(3번).

### 8. ★★★ `match` 조사 대상은 문장 끝까지 · `if` 조건은 직후 · `while let` 은 본문 내내 — 본문에서 다시 `lock()` 이면 교착

- ★★★ Reference(Destructors · Temporary scopes) — **`if` 의 (패턴이 아닌) 조건식은 임시값 스코프**라 조건 평가 뒤 가드가 버려진다(9행 `free`). **`match` 의 조사 대상은 아니다** — 그 임시값은 문장 끝까지 산다(8행 `blocked`).
- ★★★ **`while let` 도 조사 대상이라 본문 내내 가드를 쥔다**(12행). 본문에서 `lock()` 을 부르면 **같은 스레드 재잠금** — 6번처럼 돌아오지 않는다.
- ★★ 고치는 법 — **꺼내기를 따로 문장으로**: `loop { let job = m.lock().unwrap().pop(); let Some(job) = job else { break }; … }` 꼴. `let` 문장 끝에서 가드가 버려진다(6행 `free`). ★ **이 꼴 자체는 던지지 않았다** — 근거는 6행이다.

### 9. ★★ 얻었다 — `Err` 안에 가드가 있다 · `unwrap` 은 「멈춘다」, `into_inner` 는 「이어 쓴다」 · 1.77.0

- ★★★ std §Errors 의 「once the mutex is **acquired**」 — 잠금은 **얻었고**, `PoisonError` 가 그 가드를 품고 있다(4번 `[6]`).
- ★★ **`lock().unwrap()`** — 「중독이면 나도 패닉한다」. 서머리 (5)의 `r52_poison_unwrap` 은 `main` 에서 ``called `Result::unwrap()` on an `Err` value: PoisonError { .. }`` 로 `exit 101`.
- ★★ **`into_inner()`** — 「중간 상태를 알고도 이어 쓴다」. 그 판단의 근거는 프로그램이 가져야 한다.
- ★ **`clear_poison`** — 로컬 문서 표지 **1.77.0**(서머리 (4)의 `r53_since`).

### 10. ★★ `let _ =` 행은 컴파일 에러라서 · `lock()` 은 멈추므로 `try_lock` · 누가 쥐었는지는 못 가른다

- ★★ **`let _ = m.lock().unwrap();`** 은 rustc 의 **기본 거부 린트 `let_underscore_lock`** 에 걸린다(44번 — 「non-binding let on a synchronization lock」). 던지면 실행 파일이 안 생긴다.
- ★★ **`try_lock`** — 잠겨 있으면 **기다리지 않고** `Err` 를 준다. 두 번째 `lock()` 으로 물으면 살아 있는 칸에서 **돌아오지 않는다**(6번). 같은 질문을 멈추지 않는 창으로 옮긴 것이다(제5의 상태).
- ★ **못 가르는 것** — `try_lock` 은 「지금 잠겨 있나」만 답하고 **어느 스레드의 가드인지** 모른다. 격자가 단일 스레드라서 「잠김 = 앞의 가드가 산다」로 읽을 수 있었다.

### 11. ★ 규칙은 같고 실패가 다르다(패닉 대 교착) · Go 는 `go vet` · kotlinx `Mutex` 는 재진입 불가

- ★★ **같은 것** — 가드가 **`Drop` 될 때** 반납된다는 것, 그래서 `match`·`if`·`if let` 행의 답이 42번 격자와 같다.
- ★★ **다른 것** — `RefCell` 은 겹치면 **패닉**(`already borrowed`), 같은 스레드의 `Mutex` 는 **돌아오지 않는다**(6번 — 이 판에서는 교착). 42번은 실행이 판정했고, 이 편은 `try_lock` 이 판정했다.
- ★ **Go** — `sync.Mutex` 는 데이터를 감싸지 않고, 값으로 복사하는 실수는 **컴파일러가 아니라 `go vet` 의 `copylocks`** 가 잡는다(Go 32번 — 탐침 18 중 13).
- ★ **Kotlin** — kotlinx `Mutex` 는 KDoc 이 **non-reentrant** 라고 적는다. 그리고 `synchronized` 블록 안의 중단점은 **컴파일 에러**다(Kotlin 56번).

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서·서머리의 **모든 블록** | `capture.sh` — 블록마다 명령을 배너에 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` 기본 규칙 넷(패닉 스레드 id 가 걸린다) |
| ★★★ **가드 해제 격자** | `r52_grid.sh` — 열두 소스 × 2021·2024 를 컴파일·실행, 판정은 `try_lock`(`\x1f` 구분 · 칸 수 검사) | 24 컴파일 · 24 실행 | **`13 / 24`** |
| 락이 데이터를 감싸는 이유 | `r52_wrap` · `r52_wrap_fix` | 2 | **E0499** · `2` |
| `Arc<Mutex<T>>` | `r52_arc_mutex` — 8 × 100000 | 1 | `total 800000` · `strong after join 1` |
| 중독 | `r52_poison` · `r52_poison_unwrap` | 2 | `[1]`\~`[8]` · `exit 101` |
| `RwLock` 허용 조합 | `r52_rwlock` | 1 | 다섯 줄 |
| 같은 스레드 재잠금 | `r52_relock` — `timeout 2` | 1 | **`exit 124`**(관찰) |
| 판 표지 | `r53_since` — 로컬 문서 grep | 1 | `clear_poison` 1.77.0 · `Mutex::new` const 1.63.0 |
| **안 던진 것** — 속도 · 공정성 · `Condvar` · `ReentrantLock` · `MutexGuard::map` · `unwrap_or_else(\|e\| e.into_inner())` 꼴 · 8번의 `loop` 꼴 | — | 0 | ★ 「안 던졌다」로 표시했다 |

**구현 의존 항목**(버전·환경이 바뀌면 **다시 찍어야 하는** 것).

| 항목 | 왜 |
|---|---|
| `poisoned lock: another task failed inside` · `PoisonError { .. }` | ★ std 구현 — 판마다 바뀔 수 있다 |
| 같은 스레드 재잠금이 **멈춘다** | ★ std 는 unspecified — OS·std 구현이 바뀌면 패닉이 될 수 있다 |
| `if let` else 행의 에디션 갈림 | ★ 에디션 규칙 — 다음 에디션에서 다시 찍는다 |
| 종료 코드 `101` · `124` | ★ std 런타임의 관행 · `timeout` 의 관행 |

★ **다시 찍는 법** — `capture.sh <새 디렉토리>` 를 그대로 돌리고 `normalize-shaky.py <원본> <새 디렉토리>` 로 견준다.

## 실행 환경

이 파일의 모든 출력·에러는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서
**`rustc --edition 2021`** 로(가드 격자는 2021·2024) 실제로 돌려 받은 것이다.\
★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
★★ 블록 첫 줄 `===== 소스: <파일> =====` 아래가 **돌린 소스 전문**이고, **진단의 줄 번호는 그 파일 기준**이다.\
★ 패닉 첫 줄의 `thread '<unnamed>' (NNN)` · `thread 'main' (NNN)` 은 **실행마다 바뀌는 칸**이다(서머리 맨 위 부분의 표).
