# rust/syntax/51 — `mpsc` 채널 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 던지는 법 — `rustc --edition 2021 <파일>.rs`. 격자는 `bash <파일>.sh`. **외부 크레이트를 하나도 쓰지 않는다.**
> ★★★ **채널을 보면 먼저 물어라** — 「**지금 살아 있는 `Sender` 는 몇 개이고, 각각 누가 쥐고 있나**」.
> ★ **문항 10개 중 코드가 붙은 예측형은 6개**다. 소스 펜스는 캡처가 실파일에서 찍었다(`check-source-fences.py` 대조).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 송신자 구성 일곱 가지와 수신 루프 (예측)

```bash
# r51_grid.sh
# 송신자 구성 × 드롭 방식마다 프로그램을 만들어 던진다
# 수신 스레드는 `for msg in rx` 를 돌고, 루프가 끝나면 done 채널로 받은 개수를 보낸다.
# main 은 done 을 recv_timeout(500ms) 으로 기다린다 — 끝났나를 멈추지 않고 판정한다.
S=$'\x1f'
cases=(
  "one tx, moved into producer thread${S}thread::spawn(move || { for i in 0..3 { tx.send(i).unwrap(); } });"
  "one tx, main sends and keeps it${S}for i in 0..3 { tx.send(i).unwrap(); }"
  "one tx, main sends then drop(tx)${S}for i in 0..3 { tx.send(i).unwrap(); } drop(tx);"
  "3 clones moved into producers, original dropped${S}for _ in 0..3 { let t = tx.clone(); thread::spawn(move || t.send(1).unwrap()); } drop(tx);"
  "3 clones moved into producers, main keeps original${S}for _ in 0..3 { let t = tx.clone(); thread::spawn(move || t.send(1).unwrap()); }"
  "3 clones kept in a Vec by main, original dropped${S}let keep: Vec<_> = (0..3).map(|_| tx.clone()).collect(); for t in &keep { t.send(1).unwrap(); } drop(tx);"
  "3 clones, one producer still sleeping with its clone${S}for k in 0..3 { let t = tx.clone(); thread::spawn(move || { t.send(1).unwrap(); if k == 0 { thread::sleep(Duration::from_secs(5)); } }); } drop(tx);"
)
printf 'case\tloop ended\tdone message\n'
e=0; m=0
for spec in "${cases[@]}"; do
  label=${spec%%"$S"*}
  body=${spec#*"$S"}
  cat > g.rs <<RS
use std::sync::mpsc;
use std::thread;
use std::time::Duration;
fn main() {
    let (tx, rx) = mpsc::channel::<i32>();
    let (done_tx, done_rx) = mpsc::channel::<usize>();
    thread::spawn(move || {
        let mut n = 0;
        for _msg in rx {
            n += 1;
        }
        let _ = done_tx.send(n);
    });
    $body
    match done_rx.recv_timeout(Duration::from_millis(500)) {
        Ok(n) => println!("true\x1freceived {n}"),
        Err(err) => println!("false\x1f{err:?}"),
    }
}
RS
  rustc --edition 2021 -A unused -o g g.rs 2>cc.txt || { echo "compile failed: $label"; cat cc.txt; exit 1; }
  out=$(./g)
  row="$label${S}$out"
  cols=$(printf '%s' "$row" | awk -F"$S" '{print NF}')
  [ "$cols" = 3 ] || { echo "column count $cols != 3"; exit 1; }
  printf '%s\n' "$row" | tr "$S" '\t'
  case $out in true*) e=$((e+1)) ;; esac
  m=$((m+1))
done
echo "ended cells: $e / $m"
```

- 일곱 행의 `loop ended` 칸(`true`/`false`)과 `done message` 칸은? 마지막 줄의 `N / 7` 은?
- ★ 4행과 5행은 소스에서 무엇 하나가 다른가?

### 2. ★★ 보낸 뒤에 찍기 (예측)

```rust
// r51_e0382.rs
use std::sync::mpsc;
use std::thread;

fn main() {
    let (tx, rx) = mpsc::channel();
    thread::spawn(move || {
        let job = String::from("job-1");
        tx.send(job).unwrap();
        println!("sent {}", job);
    });
    println!("got {}", rx.recv().unwrap());
}
```

- 컴파일되는가? 에러라면 번호와, 표지 세 개가 각각 가리키는 자리는?

### 3. ★★★ 버퍼 크기 네 가지 (예측)

```rust
// r51_bound.rs
use std::sync::mpsc;
use std::thread;
use std::time::Duration;

// 생산자가 세 번 보낸다. send 가 돌아올 때마다 log 채널에 한 줄 남긴다.
// main 은 100ms 동안 아무것도 받지 않다가, 그때까지 돌아온 send 수를 센다.
fn run(label: &str, cap: Option<usize>) {
    let (log_tx, log_rx) = mpsc::channel::<i32>();
    let rx: Box<dyn Fn() -> i32> = match cap {
        Some(n) => {
            let (tx, rx) = mpsc::sync_channel::<i32>(n);
            thread::spawn(move || for i in 1..=3 { tx.send(i).unwrap(); log_tx.send(i).unwrap(); });
            Box::new(move || rx.recv().unwrap())
        }
        None => {
            let (tx, rx) = mpsc::channel::<i32>();
            thread::spawn(move || for i in 1..=3 { tx.send(i).unwrap(); log_tx.send(i).unwrap(); });
            Box::new(move || rx.recv().unwrap())
        }
    };
    thread::sleep(Duration::from_millis(100));
    let returned_before_any_recv = log_rx.try_iter().count();
    let got: Vec<i32> = (0..3).map(|_| rx()).collect();
    println!("{label:<16} sends returned before any recv: {returned_before_any_recv} / 3   received {got:?}");
}

fn main() {
    run("sync_channel(0)", Some(0));
    run("sync_channel(1)", Some(1));
    run("sync_channel(2)", Some(2));
    run("channel()", None);
}
```

- 네 줄의 `sends returned before any recv: N / 3` 의 `N` 은? `received` 칸은?

### 4. ★★ 버퍼 1 짜리에 `try_send` (예측)

```rust
// r51_try_send.rs
use std::sync::mpsc::{self, TrySendError};

fn main() {
    let (tx, rx) = mpsc::sync_channel::<i32>(1);
    println!("[1] try_send(1) {:?}", tx.try_send(1));
    let r = tx.try_send(2);
    println!("[2] try_send(2) {:?}", r);
    if let Err(TrySendError::Full(v)) = &r {
        println!("[3] Display \"{}\"  value returned {}", r.as_ref().unwrap_err(), v);
    }
    println!("[4] recv {:?}", rx.recv());
    println!("[5] try_send(3) {:?}", tx.try_send(3));
}
```

- 다섯 줄의 출력은? `[2]` 의 `Debug` 는 어떤 모양으로 찍히나?

### 5. ★★ 반대편이 사라진 채널 (예측)

```rust
// r51_closed.rs
use std::sync::mpsc;
use std::time::Duration;

fn main() {
    let (tx, rx) = mpsc::channel::<String>();
    drop(rx);
    let r = tx.send(String::from("job-1"));
    println!("[1] send after rx dropped: {:?}", r);
    let e = r.unwrap_err();
    println!("[2] Display \"{}\"  value back {:?}", e, e.0);

    let (tx, rx) = mpsc::channel::<i32>();
    tx.send(7).unwrap();
    drop(tx);
    println!("[3] recv {:?}", rx.recv());
    println!("[4] recv {:?}", rx.recv());
    println!("[5] Display \"{}\"", rx.recv().unwrap_err());

    let (tx, rx) = mpsc::channel::<i32>();
    println!("[6] recv_timeout {:?}", rx.recv_timeout(Duration::from_millis(50)));
    drop(tx);
    println!("[7] recv_timeout {:?}", rx.recv_timeout(Duration::from_millis(50)));
}
```

- `[1]`\~`[7]` 의 출력은? `[6]` 과 `[7]` 은 무엇이 달라서 갈리나?

### 6. ★★ 주인 스레드 하나 (예측)

```rust
// r51_owner.rs
use std::collections::BTreeMap;
use std::sync::mpsc;
use std::thread;

enum Cmd {
    Add(String, u32),
    Report(mpsc::Sender<BTreeMap<String, u32>>),
}

fn main() {
    let (tx, rx) = mpsc::channel::<Cmd>();

    // 상태의 주인은 이 스레드 하나다 — 잠금이 없다
    let owner = thread::spawn(move || {
        let mut totals: BTreeMap<String, u32> = BTreeMap::new();
        for cmd in rx {
            match cmd {
                Cmd::Add(k, n) => *totals.entry(k).or_insert(0) += n,
                Cmd::Report(reply) => reply.send(totals.clone()).unwrap(),
            }
        }
        totals.len()
    });

    let workers: Vec<_> = ["a", "b", "c"]
        .into_iter()
        .map(|name| {
            let tx = tx.clone();
            thread::spawn(move || {
                for _ in 0..1000 {
                    tx.send(Cmd::Add(name.to_string(), 1)).unwrap();
                }
            })
        })
        .collect();
    for w in workers {
        w.join().unwrap();
    }

    let (reply_tx, reply_rx) = mpsc::channel();
    tx.send(Cmd::Report(reply_tx)).unwrap();
    println!("report {:?}", reply_rx.recv().unwrap());
    drop(tx);
    println!("owner exited, keys {}", owner.join().unwrap());
}
```

- 두 줄의 출력은? `drop(tx);` 줄을 지우면 무엇이 달라지나?

### 7. ★★★ `for msg in rx` 는 무엇을 보고 끝나나 (왜)

- 수신 루프는 「보낼 값이 다 왔다」를 어떻게 아는가 — 아니면 모르는가? std 문서는 `recv` 가 막히는 조건을 어떻게 적나? 1번에서 `false` 가 나온 칸은 각각 **누가 쥔 `Sender`** 때문인가?

### 8. ★★ `send` 가 공유 상태를 지운다는 말 (왜)

- 2번의 에러와 6번의 설계는 어떻게 이어지나? 6번에서 `totals` 에 잠금이 **필요 없는** 이유는 무엇이고, 그 대가로 생기는 실패 모드는 무엇인가?

### 9. ★★ 배압 — std 가 주는 것과 안 주는 것 (경계)

- [`ops-patterns/05-backpressure`](../../../../cs/ops-patterns/05-backpressure/) 의 오버플로 정책 넷(BLOCK · DROP_NEWEST · DROP_OLDEST · FAIL) 중 `sync_channel` 의 `send` 는 무엇에 해당하나? `try_send` 로 만들 수 있는 것과 **std `mpsc` 로는 못 만드는 것**은?

### 10. ★ Go 의 `close` 와 Rust 의 `drop` (연결)

- [Go 29번](../../../go/syntax/29-channels-buffering-direction-close-range-and-nil/)에서 `range` 는 무엇을 계기로 끝나나? Rust 에서 그 자리를 맡는 것은 무엇이고, 두 언어에서 **닫힌 뒤 남아 있던 값**은 각각 어떻게 되나 — 5번의 `[3]`·`[4]` 로 답하라.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
