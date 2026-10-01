# rust/syntax/52 — `Mutex`/`RwLock` 과 `Arc<Mutex<T>>` · 중독 — 질문

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 열두 가지 가드 모양 × 두 에디션 (예측)

```bash
# r52_grid.sh
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
```

- 스물네 칸(`edition 2021` · `edition 2024`)에 `blocked` 또는 `free` 를 채워라. 마지막 줄의 `N / 24` 는?
- ★ 두 에디션 열이 서로 다른 행이 있다면 어느 것인가?

### 2. ★★★ 락 하나와 변수 하나 (예측)

```rust
// r52_wrap.rs
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
```

- 컴파일되는가? 에러라면 번호와, 컴파일러가 **무엇을 무엇과 겹친다고** 보는가?

### 3. ★★ 여덟 스레드의 카운터 (예측)

```rust
// r52_arc_mutex.rs
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
```

- 두 줄의 출력은?

### 4. ★★★ 가드를 쥔 채 쓰러진 스레드 (예측)

```rust
// r52_poison.rs
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
```

- `[1]`\~`[8]` 여덟 줄의 값은? `[6]` 의 데이터에는 `4` 가 들어 있나?

### 5. ★★ 읽기 가드와 쓰기 가드 (예측)

```rust
// r52_rwlock.rs
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
```

- 다섯 줄의 `try_read` · `try_write` 칸은 각각 `ok` 인가 `no` 인가?

### 6. ★★ 같은 스레드가 두 번 (예측)

```rust
// r52_relock.rs
use std::sync::Mutex;

fn main() {
    let m = Mutex::new(0);
    let _first = m.lock().unwrap();
    eprintln!("[1] first guard taken");
    let _second = m.lock().unwrap();
    eprintln!("[2] second guard taken");
}
```

- `timeout 2 ./r52_relock` 으로 돌리면 표준 오류에 몇 번 줄까지 찍히고 종료 코드는? 그 결과는 std 가 **보장**한 것인가?

### 7. ★★★ 락이 데이터를 감싸는 이유 (왜)

- 2번의 소스는 두 스레드가 **둘 다 잠근 뒤** 고치는데 왜 거부되나? `count` 를 `Mutex<i32>` 안에 넣으면 무엇이 **타입으로** 강제되나? 그 판에 `Arc` 가 필요 없는 이유는?

### 8. ★★★ `match`·`if`·`while let` 의 가드 (왜)

- 1번에서 `match m.lock().unwrap().len()` 과 `if m.lock().unwrap().len() < 9` 는 왜 결과가 갈리나? `while let Some(x) = m.lock().unwrap().pop() { … }` 의 본문에서 같은 락을 `lock()` 으로 잡으면 무슨 일이 생기나 — 어떻게 고치나?

### 9. ★★ 중독된 `lock()` 의 `Err` (경계)

- 중독된 락에 `lock()` 하면 **잠금은 얻었나 못 얻었나**? `lock().unwrap()` 과 `PoisonError::into_inner()` 는 각각 어떤 판단을 적은 코드인가? `clear_poison` 은 몇 판부터인가?

### 10. ★★ 격자에서 뺀 행과 `try_lock` (경계)

- `let _ = m.lock().unwrap();` 행은 왜 1번 격자에 없나? 격자가 `lock()` 이 아니라 `try_lock()` 으로 판정한 이유는 무엇이고, `try_lock` 이 **못 가르는 것**은?

### 11. ★ `RefCell` 격자와 Go·Kotlin 의 락 (연결)

- [42번 주제](../42-refcell-cell-interior-mutability/)의 런타임 빌림 격자와 1번은 어디가 같고, 겹쳤을 때의 **실패 모양**은 어떻게 다른가? Go 의 `sync.Mutex` 를 값으로 복사하는 실수는 누가 잡나 — [Go 32번](../../../go/syntax/32-sync-mutex-rwmutex-waitgroup-once/)? kotlinx `Mutex` 는 재진입이 되나 — [Kotlin 56번](../../../kotlin/syntax/56-channel-mutex-and-shared-mutable-state/)?

## 실행 환경

★ 던지는 법 — `rustc --edition 2021 <파일>.rs`. 격자는 `bash <파일>.sh`(가드 격자는 스크립트가 2021·2024 를 돈다). **외부 크레이트를 하나도 쓰지 않는다.**
★★★ **락을 보면 먼저 물어라** — 「**지금 살아 있는 가드는 몇 개이고, 각각 어느 줄에서 `Drop` 되나**」.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
