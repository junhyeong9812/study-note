# rust/syntax/51 — `mpsc` 채널 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서
> **`rustc --edition 2021`** 로 실제로 돌려 받은 것이다.\
> ★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
> ★★ 블록 첫 줄 `===== 소스: <파일> =====` 아래가 **돌린 소스 전문**이고, **진단의 줄 번호는 그 파일 기준**이다.\
> ★ 격자의 `false` 는 「**500ms 안에** 안 끝났다」, 배압 표는 「**100ms 동안** 안 돌아왔다」로 잰 것이다(서머리 머리말의 표 — 시간 여유에 기댄 칸).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ `3 / 7` — 송신자가 하나라도 남으면 루프는 안 끝난다

**출력**

```text
===== 소스: r51_grid.sh =====
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
===== bash r51_grid.sh =====
case	loop ended	done message
one tx, moved into producer thread	true	received 3
one tx, main sends and keeps it	false	Timeout
one tx, main sends then drop(tx)	true	received 3
3 clones moved into producers, original dropped	true	received 3
3 clones moved into producers, main keeps original	false	Timeout
3 clones kept in a Vec by main, original dropped	false	Timeout
3 clones, one producer still sleeping with its clone	false	Timeout
ended cells: 3 / 7
(exit 0)
```

**왜 그런가**

- ★★★ **끝난 칸(1·3·4행)은 전부 송신자가 0 개가 된 칸**이다 — 생산자 스레드가 끝나며 `tx` 를 버렸거나(1행), main 이 `drop(tx)` 했다(3·4행). `done message` 는 `received 3`.
- ★★★ **4행 대 5행 — `drop(tx);` 한 줄.** 5행은 복제 셋이 생산자와 함께 사라졌는데 **main 이 원본을 쥐고 있어** 루프가 넷째 값을 기다린다 → `Timeout`.
- ★★ 2행 — main 이 보낸 `tx` 를 안 버렸다. 6행 — 원본은 버렸지만 **복제를 `Vec` 에** 쥐었다. 7행 — 생산자 하나가 보낸 뒤 **잠들어** 복제가 살아 있다. **셋 다 5행과 같은 뿌리**다.

### 2. ★★ E0382 — `send` 가 `job` 을 옮겼다

**출력**

```text
===== 소스: r51_e0382.rs =====
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
===== rustc --edition 2021 r51_e0382.rs =====
error[E0382]: borrow of moved value: `job`
 --> r51_e0382.rs:9:29
  |
7 |         let job = String::from("job-1");
  |             --- move occurs because `job` has type `String`, which does not implement the `Copy` trait
8 |         tx.send(job).unwrap();
  |                 --- value moved here
9 |         println!("sent {}", job);
  |                             ^^^ value borrowed here after move
  |
  = note: this error originates in the macro `$crate::format_args_nl` which comes from the expansion of the macro `println` (in Nightly builds, run with -Z macro-backtrace for more info)

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0382`.
(exit 1)
```

**왜 그런가**

- ★★ **E0382 — borrow of moved value: `job`.** 7행 「move occurs because `job` has type `String`」 · 8행 `tx.send(job)` 「value moved here」 · 9행 「value borrowed here after move」.
- ★ `send` 는 값을 **받는다**(빌리지 않는다). 보낸 뒤에는 보낸 쪽의 것이 아니다. 로그는 `send` **위로** 올려라.

### 3. ★★★ `0` · `1` · `2` · `3` — 막히기 전에 돌아온 `send` 수가 버퍼 크기다

**출력**

```text
===== 소스: r51_bound.rs =====
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
===== rustc --edition 2021 r51_bound.rs =====
(exit 0)
===== ./r51_bound 2>/dev/null =====
sync_channel(0)  sends returned before any recv: 0 / 3   received [1, 2, 3]
sync_channel(1)  sends returned before any recv: 1 / 3   received [1, 2, 3]
sync_channel(2)  sends returned before any recv: 2 / 3   received [1, 2, 3]
channel()        sends returned before any recv: 3 / 3   received [1, 2, 3]
===== ./r51_bound 2>&1 >/dev/null =====

thread '<unnamed>' (3311208) panicked at r51_bound.rs:12:88:
called `Result::unwrap()` on an `Err` value: SendError { .. }
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
(exit 0)
```

**왜 그런가**

- ★★★ **`sync_channel(0)` 0 / 3** — 랑데부. std: 「각 `send` 는 짝이 되는 `recv` 가 올 때까지 돌아오지 않는다」.
- ★★ **`sync_channel(1)` 1 / 3 · `sync_channel(2)` 2 / 3** — 버퍼가 차면 다음 `send` 가 막힌다.
- ★★ **`channel()` 3 / 3** — 무한 버퍼, 어떤 `send` 도 막지 않는다.
- ★ 넷 다 `received [1, 2, 3]` — 막혔던 생산자는 main 이 받기 시작하자 풀려 **보낸 순서대로** 다 넘겼다.

### 4. ★★ `Err("Full(..)")` — 값 `2` 는 돌려받았다

**출력**

```text
===== 소스: r51_try_send.rs =====
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
===== rustc --edition 2021 r51_try_send.rs =====
(exit 0)
===== ./r51_try_send =====
[1] try_send(1) Ok(())
[2] try_send(2) Err("Full(..)")
[3] Display "sending on a full channel"  value returned 2
[4] recv Ok(1)
[5] try_send(3) Ok(())
(exit 0)
```

**왜 그런가**

- ★★ `[1]` 로 버퍼 1 이 찼다 → **`[2]` `Err("Full(..)")`**, `[3]` `Display` **`sending on a full channel`** · 돌려받은 값 **`2`**.
- ★★ `[4]` 로 하나를 비우자 `[5]` `Ok(())`.
- ★★★ **따옴표가 붙은 `"Full(..)"`** — 1.92 std 소스에서 `TrySendError` 의 `Debug` 가 문자열 `"Full(..)"` 을 **문자열의 `Debug` 로** 찍는다. 값 `T` 는 찍지 않는다. **std 구현**이므로 판정은 `matches!(r, Err(TrySendError::Full(_)))` 로 한다.

### 5. ★★ `SendError { .. }` · `RecvError` · `Timeout` 대 `Disconnected`

**출력**

```text
===== 소스: r51_closed.rs =====
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
===== rustc --edition 2021 r51_closed.rs =====
(exit 0)
===== ./r51_closed =====
[1] send after rx dropped: Err(SendError { .. })
[2] Display "sending on a closed channel"  value back "job-1"
[3] recv Ok(7)
[4] recv Err(RecvError)
[5] Display "receiving on a closed channel"
[6] recv_timeout Err(Timeout)
[7] recv_timeout Err(Disconnected)
(exit 0)
```

**왜 그런가**

- ★★ `[1]`·`[2]` — 수신자가 사라지면 `send` 가 **`Err(SendError { .. })`**, `Display` **`sending on a closed channel`**, **`e.0` 으로 `"job-1"` 회수.**
- ★★ `[3]`·`[4]`·`[5]` — 송신자를 버려도 **남은 `7` 을 먼저 받고**, 그다음 `Err(RecvError)` · `receiving on a closed channel`.
- ★★★ **`[6]` 대 `[7]`** — 송신자가 **살아 있으면** 값이 없을 때 `Timeout`, **전부 사라졌으면** `Disconnected`. 「아직 안 왔다」와 「더는 안 온다」다.

### 6. ★★ `report {"a": 1000, "b": 1000, "c": 1000}` · `owner exited, keys 3` — `drop(tx)` 가 없으면 `join` 이 안 돌아온다

**출력**

```text
===== 소스: r51_owner.rs =====
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
===== rustc --edition 2021 r51_owner.rs =====
(exit 0)
===== ./r51_owner =====
report {"a": 1000, "b": 1000, "c": 1000}
owner exited, keys 3
(exit 0)
```

**왜 그런가**

- ★★★ `totals` 는 **주인 스레드의 지역 변수**라 다른 스레드는 명령을 보낼 뿐이다. 읽기도 `Cmd::Report(reply)` 로 **응답 채널을 실어** 보낸다.
- ★★★ **`drop(tx);` 를 지우면** — 생산자 셋의 복제는 사라지지만 main 의 원본이 남아 주인의 `for cmd in rx` 가 **안 끝나고**, `owner.join()` 이 **영영 돌아오지 않는다**. 1번 5행의 모양이다(이 변형은 **던지지 않았다** — 1번 격자가 같은 구조를 재현한다).
- ★ 세 생산자의 도착 순서는 흔들리지만 **합계와 `BTreeMap` 의 키 순서**는 흔들리지 않는다.

### 7. ★★★ 루프는 「값이 다 왔다」를 모른다 — 송신자 개수 0 만 본다

- ★★★ 채널은 **「더 보낼 값이 없다」는 신호를 따로 받지 않는다.** 아는 것은 **살아 있는 `Sender` 의 개수**뿐이고, 0 이 되면 `recv` 가 `Err(RecvError)` 를 돌려 `for` 가 끝난다.
- ★★ std(`channel`): 「`recv` 는 **적어도 하나의 `Sender` 가 살아 있는 동안(복제 포함)** 값이 올 때까지 막힌다」.
- ★★ 1번의 `false` 넷 — **2행 main 의 `tx` · 5행 main 의 원본 `tx` · 6행 main 의 `Vec` 속 복제 셋 · 7행 잠든 생산자의 복제.**

### 8. ★★ 보낸 쪽이 못 만지니 공유가 없다 — 대가는 「안 끝나는 주인」

- ★★★ 2번 — `send` 가 값을 **옮기므로** 보낸 뒤 그 값을 만지는 코드는 **컴파일이 안 된다.** 한 값을 두 스레드가 동시에 만지는 상황이 **타입에서** 사라진다.
- ★★ 6번 — 상태(`totals`)를 **한 스레드의 지역 변수**로 두고 나머지는 **명령만** 보낸다. 만지는 스레드가 하나뿐이라 잠금이 필요 없다.
- ★★ **대가** — 주인 스레드의 수명이 **`Sender` 의 수명에 묶인다.** 송신자를 하나라도 안 버리면 주인이 안 끝난다(1번 5행). 잠금의 실패 모드(가드를 오래 쥐기 · 중독 — 목록의 **52번 주제**)와 **종류가 다르다.** 속도 비교는 하지 않았다.

### 9. ★★ `send` 는 BLOCK · `try_send` 는 결정을 넘긴다 · DROP_OLDEST 는 없다

- ★★ **`sync_channel` 의 `send` = BLOCK** — 3번에서 버퍼가 차자 생산자가 멈췄다.
- ★★ **`try_send`** 는 `Err(Full(v))` 로 **값을 돌려주고 결정을 부른 쪽에** 넘긴다 — 버리면 **DROP_NEWEST**, 에러로 올리면 **FAIL**(4번).
- ★★ **DROP_OLDEST 는 std `mpsc` 로 못 만든다** — 보내는 쪽이 큐의 머리를 꺼낼 수 없다(꺼내기는 `Receiver` 하나만 한다).
- ★ 정원 크기와 대기 시간의 관계, 정책별 손실은 **그 주제의 정본**이다 — 여기서는 재지 않았다.

### 10. ★ Go 는 `close`, Rust 는 송신자 전부의 `Drop` — 남은 값은 둘 다 다 받는다

- ★★ Go 29번 — `range` 는 **`close` 를 부른 뒤** 남은 값을 **다 돈 다음** 끝난다(그 문서의 `1 2 range 뒤 줄`).
- ★★ Rust 에는 `close` 가 없다 — **모든 `Sender` 가 `Drop` 되는 것**이 닫힘이다. 누가 닫을지 정하는 호출이 없으니 **닫는 책임이 송신자 전원에게 흩어진다** — 그래서 1번의 사고가 난다.
- ★★ 남은 값 — Rust 도 5번 `[3]` 에서 **남은 `7` 을 먼저 받고** `[4]` 에서 `RecvError` 다. 이 점은 두 언어가 같다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서·서머리의 **모든 블록** | `capture.sh` — 블록마다 명령을 배너에 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` 기본 규칙 넷 · **고칠 것 0** |
| ★★★ **수신 루프 종료 격자** | `r51_grid.sh` — 일곱 소스를 만들어 컴파일·실행(`\x1f` 구분 · 칸 수 검사 · `recv_timeout(500ms)`) | 7 컴파일 · 7 실행 | **`3 / 7`** |
| ★★ 배압 표 | `r51_bound` — 버퍼 넷 × 세 번 보내기 · 100ms 동안 수신 없음 | 1 | **`0` · `1` · `2` · `3`** / 3 |
| 소유권 이동 | `r51_e0382` | 1 | **E0382** |
| 오류 값 | `r51_try_send` · `r51_closed` | 2 | `"Full(..)"` · `SendError { .. }` · `RecvError` · `Timeout` · `Disconnected` |
| 주인 스레드 설계 | `r51_owner` | 1 | `1000` × 3 · `keys 3` |
| **안 던진 것** — 속도·처리량 · `try_send` 의 `Disconnected` · 6번에서 `drop(tx)` 를 뺀 판 · 여러 소비자 · `recv_deadline` | — | 0 | ★ 「안 던졌다」로 표시했다 |

**구현 의존 항목**(버전·환경이 바뀌면 **다시 찍어야 하는** 것).

| 항목 | 왜 |
|---|---|
| `Display` 문구 · `Debug` 모양(`"Full(..)"` · `SendError { .. }`) | ★ std 구현 — 판마다 바뀔 수 있다 |
| 격자의 `false` · 배압 표의 `N` | ★ **시간 여유**(500ms · 100ms)에 기댄 판정 — 몹시 느린 머신에서는 다시 확인 |
| `mpsc` 가 안에서 `mpmc` 를 감싸는 것 | ★ std 구현 세부 — 공개 API 가 아니다 |

★ **다시 찍는 법** — `capture.sh <새 디렉토리>` 를 그대로 돌리고 `normalize-shaky.py <원본> <새 디렉토리>` 로 견준다.
