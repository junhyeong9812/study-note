# rust/syntax/51 — `mpsc` 채널 — 정리 (힌트)

★★★ **본체 창 — ① 수신 루프 종료 격자(송신자 구성 × 드롭 방식 → `for msg in rx` 가 끝났나)다.** 「끝났나」를 **멈추지 않고** 판정하려고 수신 스레드가 루프를 빠져나오면 `done` 채널로 알리고, main 은 그것을 `recv_timeout(500ms)` 으로 기다린다.

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| 안 흔들린다 | ★★★ **격자의 `loop ended` 칸과 「ended cells N / M」** | 루프가 끝나는 조건(송신자가 전부 사라졌나)은 std 의 계약이다 — **이 주제의 본체** |
| 안 흔들린다 — 단 **시간 여유에 기댄 칸** | ★★ 격자의 `false`(500ms 안에 안 끝남) · 배압 표의 「sends returned before any recv」(100ms 동안 수신 없음) | 「영원히 안 끝난다」를 **500ms 로**, 「막혔다」를 **100ms 동안 안 돌아왔다로** 잰 것이다. 시간은 흔들리지만 **여유가 커서** 제출 전 재실행까지 한 글자도 같았다 |
| 안 흔들린다 — 단 **std 판의 문구** | `Display` 문구(`sending on a full channel` 등) · `Debug` 모양(`SendError { .. }` · `"Full(..)"`) | ★ **std 구현**이다((4)·(5)) |
| 안 흔들린다 | E0382 번호·`파일:줄:칸` · 종료 코드 | 같은 rustc 판에서 고정이다 |
| 순서 | 수신 순서 — 생산자가 여럿이면 **도착 순서는 흔들린다** | 그래서 출력에 싣지 않았다 — 격자는 **개수**만, (6)은 **`BTreeMap`** 으로 찍는다 |

★ 정규화 규칙은 **기본 넷**만 쓴다. 이 편의 블록에는 패닉도 스레드 id 도 없다.

## 한눈에 — 쉽게 말하면

채널은 「한 방향으로만 흐르는 우편함」이다. 편지를 넣는 구멍(`Sender`)은 복사해서 여럿이 나눠 가질 수 있지만, 꺼내는 문(`Receiver`)은 하나다.
편지를 넣으면 **그 편지는 내 손을 떠난다**(소유권 이동). 그리고 우편함은 「이제 올 편지가 없다」를 **넣는 구멍이 전부 막혔을 때만** 안다 —
구멍 하나라도 누군가 쥐고 있으면, 꺼내는 사람은 **영원히 다음 편지를 기다린다.**

| 비유 | 실체 |
|---|---|
| 「**넣는 구멍**」 | ★★ **`Sender<T>`** — `clone()` 으로 여럿. `send(v)` 가 **`v` 를 옮긴다**((2)) |
| 「**꺼내는 문**」 | ★★ **`Receiver<T>`** — 하나뿐(`Clone` 이 없다 · `!Sync`) |
| 「**구멍이 전부 막혔다**」 | ★★★ **모든 `Sender` 가 `Drop`** → `recv` 가 `Err(RecvError)` → **`for msg in rx` 가 끝난다**((1)) |
| 「**구멍 하나를 주머니에 넣고 잊었다**」 | ★★★ **main 이 원본 `tx` 를 쥔 채** — 수신 루프가 **안 끝난다**((1)의 `Timeout`) |
| 「**우편함 크기**」 | ★★ `channel()` = 끝없음 · **`sync_channel(n)`** = n 통 · **`sync_channel(0)`** = 손에서 손으로(랑데부)((3)) |
| 「**꽉 찼으면 들고 기다리기 / 되돌려 받기**」 | ★★ `send` 는 **막힌다** · `try_send` 는 **`Err(Full(v))` 로 편지를 돌려준다**((4)) |
| 「**문이 사라졌다**」 | ★ `Receiver` 가 `Drop` → `send` 가 **`Err(SendError(v))`** — 편지를 **돌려받는다**((5)) |

```text
   수신 루프는 언제 끝나나 — (1)의 한 쌍 그대로

   producer 스레드들 ─ t.clone() ─┐
                                   ├──►  [ channel ]  ──►  for msg in rx { … }
   main ─ 원본 tx ─────────────────┘                        │
                                                            ▼
   drop(tx) 했나?   예 → 송신자 0 개 → recv 가 RecvError → 루프 끝 (ended true · received 3)
                    아니오 → 송신자 1 개 남음 → recv 가 계속 기다림 (500ms 뒤 Timeout)
```

> **채널(channel)** — 스레드 사이에 값을 **옮기는** 통로. `mpsc` 는 multi-producer, single-consumer — 넣는 쪽은 여럿, 꺼내는 쪽은 하나.\
> 예: `let (tx, rx) = mpsc::channel(); tx.send(1).unwrap(); rx.recv()` → `Ok(1)`.

> **끊김(hang up · disconnect)** — 반대편이 **전부** `Drop` 된 상태. std 는 `Receiver::iter` 를 「채널이 끊기면 `None` 을 돌려준다」로 적는다.\
> 예: 송신자가 모두 사라진 뒤 `rx.recv()` → `Err(RecvError)`.

## 이 주제가 답하려는 질문

1. ★★★ **`for msg in rx` 는 언제 끝나나** — 「보낼 것을 다 보냈을 때」가 아니라 「**송신자가 전부 사라졌을 때**」다. 그 차이가 사고를 만든다((1)).
2. ★★ **채널이 공유 상태를 어떻게 지우나** — `send` 가 소유권을 옮기고, 상태는 **주인 스레드 하나**가 쥔다((2)·(6)).
3. ★★ **버퍼 크기가 무엇을 바꾸나** — 보내는 쪽이 **언제 막히나**, 꽉 찼을 때 **누가 결정하나**((3)·(4)).

★ **선행** — [**49번 주제**](../49-threads-spawn-join-and-move-closures/) — 생산자 스레드에 `tx` 복제를 넘길 때 `move` 가 필요하고, `JoinHandle` 을 버리면 detach 된다. 이 편의 격자는 **수신 스레드를 detach 한 채** main 이 먼저 끝나는 구조다(49의 detach 칸).
[**44번 주제**](../44-drop-mem-drop-replace-and-take/) — 「끝났다」는 신호가 결국 **`Sender` 의 `Drop`** 이다. `drop(tx)` 와 스코프 끝이 무엇을 부르는지는 그쪽이 정본이다.

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ① 수신 루프 종료 격자다

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ① ★★★ **수신 루프 종료 격자**(조합마다 소스를 만들어 실행 · `recv_timeout` 으로 판정) | 어느 송신자 구성에서 **루프가 끝나나** | ★ **본체**((1)) |
| ② ★★ **컴파일러 진단** E0382 | `send` 뒤에 그 값을 쓸 수 있나 | 쓴다((2)) |
| ③ ★★ **배압 표**(send 가 돌아온 횟수를 **다른 채널**로 센다) | 버퍼 크기마다 **몇 번 보내고 막히나** | 쓴다((3)) |
| ④ ★★ **오류 값 찍기**(`Debug` · `Display`) | 꽉 참 · 끊김 · 시간 초과가 **어떻게 구별되나** | 쓴다((4)·(5)) |
| ⑤ ★ **std 소스 읽기** | `Debug` 모양이 **어디서 오나** | 쓴다((4)) |
| 처리량 · 지연 시간 | 「채널은 느리다/빠르다」 | ★ **부적용 — 재지 않는다** |
| 교착 탐지기 | 「이 수신 루프는 영원히 기다린다」 | ★ **못 잰 것** — 표준 라이브러리에 그런 도구가 없다. **「영원히」는 원리상 잴 수 없다** |

★★ **제5의 상태 — 「같은 질문을 다른 창으로」.** 「이 루프는 영원히 기다리나」는 원래 **잴 수 없는** 질문이다(프로그램이 멈추면 판정도 멈춘다). 그래서 질문을 「**500ms 안에 끝났나**」로 바꿔 `recv_timeout` 의 창으로 물었다((1)).
★ 바꾼 창이 **못 보는 것** — **501ms 째에 끝나는 루프.** 격자의 `false` 는 「안 끝난다」의 증명이 아니라 「**500ms 안에는** 안 끝났다」다. 이 격자에서 `false` 칸의 원인은 전부 **소스에 보이는 살아 있는 송신자**라서 그 읽기가 맞다 — 원인이 안 보이는 `false` 였다면 시간을 늘려 다시 물어야 한다.

### (1) ★★★ 수신 루프 종료 격자 — 일곱 조합

**언제 쓰나** — `for msg in rx` 를 쓰는 모든 코드에서, 「이 루프는 끝나나」를 판정할 때마다.

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

- ★★★ **「ended cells 3 / 7」.** 끝난 칸은 셋 다 **모든 송신자가 사라진** 칸이다 — 생산자 스레드가 끝나며 `tx` 를 버렸거나(1행), main 이 `drop(tx)` 했다(3·4행).
- ★★★ **5행이 가장 흔한 사고다** — 복제 셋은 생산자와 함께 사라졌는데 **main 이 원본 `tx` 를 쥐고 있다.** 보낼 것은 다 보냈는데(`t.send(1)` 셋) 루프는 **다음 값이 올지도 모르니** 기다린다. `drop(tx)` 한 줄이 4행과 5행을 가른다.
- ★★ **2행도 같은 뿌리다** — main 이 직접 보내고 `tx` 를 버리지 않았다. `tx` 는 **`main` 이 끝나야** 버려지는데, main 은 루프가 끝나기를 기다리고 있다 — 이 격자는 `recv_timeout` 이라 빠져나왔지만 **`recv()` 나 `join()` 으로 기다렸다면 영영 안 끝난다.**
- ★★ **6행 — 원본을 버려도 복제를 쥐면 같다.** 「원본」이 특별한 게 아니다 — **`Sender` 는 몇 개든 전부 같은 자격**이고, 루프는 **개수가 0 이 되는 순간**만 본다.
- ★★ **7행 — 보낼 것을 다 보낸 스레드라도 살아 있으면 같다.** 생산자 하나가 `send` 뒤 5초를 잔다 — 그 스레드의 `t` 가 아직 살아 있다. std 의 말로 「`recv` 는 **적어도 하나의 `Sender` 가 살아 있는 동안**(복제 포함) 값이 올 때까지 막힌다」.
- ★ `done message` 칸 — 끝난 칸은 **`received 3`**(받은 개수), 안 끝난 칸은 **`Timeout`**(`RecvTimeoutError::Timeout` 의 `Debug`). 안 끝난 칸에서도 값 셋은 **이미 받았다** — 루프가 막힌 것은 **넷째 값을 기다리는 자리**다.

```text
   for msg in rx 가 한 바퀴마다 하는 일

   rx.recv()
     ├─ 값이 있다                      → Ok(v)   → 루프 몸통
     ├─ 값이 없고 Sender 가 1 개 이상   → 막혀서 기다린다         ← 2·5·6·7행이 여기서 멈췄다
     └─ 값이 없고 Sender 가 0 개        → Err(RecvError) → 루프 끝  ← 1·3·4행
```

### (2) ★★ `send` 는 소유권을 넘긴다 — E0382

**언제 쓰나** — 보낸 값을 로그로 찍고 싶어질 때.

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

- ★★ **E0382 — borrow of moved value: `job`.** 표지가 셋이다 — 「move occurs because `job` has type `String`」 · 「value moved here」(`tx.send(job)`) · 「value borrowed here after move」.
- ★★★ **이것이 「공유 상태를 지운다」의 뜻이다** — 보낸 뒤에는 **보낸 쪽이 그 값을 못 만진다.** 그러니 두 스레드가 같은 값을 동시에 만질 일이 **타입 수준에서** 없다. 잠금이 필요 없는 이유가 이 에러 하나에 들어 있다.
- ★ 로그가 필요하면 **보내기 전에** 찍거나(`println!` 을 `send` 위로), 보낼 값의 복제를 보낸다. `send(job.clone())` 은 **복제를 옮기는 것**이지 공유가 아니다.

### (3) ★★ 버퍼 크기 — 보내는 쪽이 언제 막히나

**언제 쓰나** — 생산자가 소비자보다 빠를 때, 「쌓이게 둘까 · 생산자를 세울까」를 정할 때.

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

- ★★★ **막히기 전에 돌아온 `send` 수 = 버퍼 크기**다 — `sync_channel(0)` **0 / 3** · `sync_channel(1)` **1 / 3** · `sync_channel(2)` **2 / 3** · `channel()` **3 / 3**. 생산자는 세 번 보내려 했고, main 은 100ms 동안 **아무것도 받지 않았다.**
- ★★★ **`sync_channel(0)` 은 랑데부다** — std: 「각 `send` 는 **짝이 되는 `recv` 가 올 때까지** 돌아오지 않는다」. 버퍼가 없으니 **첫 `send` 부터** 막혔다(0 / 3).
- ★★ **`channel()` 은 한 번도 안 막혔다**(3 / 3) — std: 「**무한 버퍼**를 가지며 어떤 `send` 도 호출 스레드를 막지 않는다」. 소비자가 느리면 **큐가 메모리를 먹으며 자란다** — 그 자람을 재는 것은 배압 주제의 일이다(아래 경계).
- ★ 넷 다 `received [1, 2, 3]` — **막혔다가 풀린 뒤 순서대로** 다 받았다(한 생산자 안의 순서는 std: 「보낸 순서대로」).
- ★ 세는 방법 — 생산자가 `send` 가 돌아올 때마다 **두 번째 채널(`log_tx`)** 에 한 줄 남기고, main 이 `try_iter().count()` 로 **막히지 않고** 센다. 원자 변수([목록의 **53번 주제**](../53-atomics-oncelock-and-lazylock/)) 없이 채널만으로 셌다.

★ **경계** — [`ops-patterns/05-backpressure`](../../../../cs/ops-patterns/05-backpressure/) 가 **배압 일반의 정본**이다(정원 · 오버플로 정책 넷 BLOCK · DROP_NEWEST · DROP_OLDEST · FAIL · 정원과 대기 시간). 여기서는 **std 가 무엇을 주나**만 — `sync_channel` 의 `send` 는 그 표의 **BLOCK** 이고, (4)의 `try_send` 는 **결정을 호출자에게 넘긴다**(돌려받은 값을 버리면 DROP_NEWEST, 에러로 올리면 FAIL). **DROP_OLDEST 는 std `mpsc` 에 없다** — 보내는 쪽이 큐의 머리를 꺼낼 수 없기 때문이다.

### (4) ★★ `try_send` — 꽉 찼으면 편지를 돌려받는다

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

- ★★ **`[2]` `Err("Full(..)")`** — 버퍼 1 이 `[1]` 로 찼다. `[3]` `Display` 는 **`sending on a full channel`**, 그리고 **보내려던 값 `2` 를 돌려받았다**(`TrySendError::Full(v)`). 값이 사라지지 않으니 **버릴지·다시 보낼지·에러로 올릴지**를 부른 쪽이 고른다.
- ★★ `[4]` 에서 하나를 받자 `[5]` 는 `Ok(())` — 자리가 나면 다시 된다.
- ★★★ **`Debug` 에 따옴표가 붙는다** — `Full(..)` 가 아니라 `"Full(..)"`. 1.92 의 std 소스(`src/std/sync/mpsc.rs.html`)를 보면 `TrySendError` 의 `Debug` 가 **문자열 `"Full(..)"` 을 그 문자열의 `Debug` 로** 찍는다 — 그래서 따옴표째 나온다. **값 `T` 는 `Debug` 에 안 나온다**(`T: Debug` 를 요구하지 않으려는 모양이다). ★ **이것은 std 구현이다** — 로그를 이 모양으로 grep 하지 마라.

### (5) ★★ 끊김과 시간 초과 — 세 가지 오류 값

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

- ★★ **`[1]` 수신자가 사라진 뒤 `send` → `Err(SendError { .. })`.** `[2]` `Display` 는 **`sending on a closed channel`**, 그리고 **`e.0` 으로 값 `"job-1"` 을 돌려받았다.** 보낸 쪽이 **「안 갔다」를 안다** — 조용히 버려지지 않는다.
- ★★ **`[3]`→`[4]` 송신자를 버린 뒤** — 남은 값 `Ok(7)` 을 **먼저 다 받고**, 그다음에 `Err(RecvError)`. 끊김은 **버퍼가 빈 뒤에야** 보인다. (1)의 루프가 `received 3` 을 채운 뒤 끝나는 것이 이것이다.
- ★★★ **`[6]` 대 `[7]`** — `recv_timeout` 은 두 실패를 **가른다.** 송신자가 살아 있는데 값이 없으면 **`Timeout`**, 송신자가 전부 사라졌으면 **`Disconnected`**. (1)의 격자가 `false` 칸에서 본 것이 `[6]` 쪽이다.

| 부른 것 | 상대편이 사라졌다 | 꽉 찼다 / 값이 없다 |
|---|---|---|
| `send` | `Err(SendError(v))` — 값 회수 | `channel()`: 안 막힘 · `sync_channel`: **막힌다** |
| `try_send` | `Err(TrySendError::Disconnected(v))` | `Err(TrySendError::Full(v))` — 값 회수((4)) |
| `recv` | `Err(RecvError)` — **남은 값을 다 받은 뒤** | **막힌다** |
| `recv_timeout` | `Err(Disconnected)` | `Err(Timeout)` |
| `for msg in rx` | **루프 끝** | **막힌다** |

★ `try_send` 의 `Disconnected` 칸은 **던지지 않았다**(std `TrySendError` 문서의 변형 이름).

### (6) ★★ 상태의 주인을 한 스레드로 — 잠금 없는 설계

**언제 쓰나** — 여러 스레드가 **한 표를 고쳐야** 할 때. `Arc<Mutex<_>>`([목록의 **52번**](../52-mutex-rwlock-arc-and-poisoning/))와 다른 길이다.

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

- ★★★ **`totals` 는 주인 스레드의 지역 변수다** — 다른 스레드는 `totals` 를 **볼 방법이 없다.** 그들은 **명령(`Cmd::Add`)을 보낼 뿐**이고, 고치는 것은 주인 하나다. 잠금이 없고, 있을 자리도 없다.
- ★★ **읽기도 명령이다** — `Cmd::Report(reply)` 가 **응답용 채널의 `Sender`** 를 싣고 간다. 주인은 복제본을 그 채널로 돌려보낸다(`report {"a": 1000, "b": 1000, "c": 1000}`).
- ★★ **끝내는 법이 (1) 그대로다** — 생산자 셋이 끝나 복제가 사라지고, main 이 `drop(tx)` 하자 주인의 `for cmd in rx` 가 끝나 **`owner exited, keys 3`**. `drop(tx)` 를 빼면 `owner.join()` 이 **영영 안 돌아온다**(5행의 모양).
- ★ 세 생산자의 **도착 순서는 흔들린다** — 그래서 `BTreeMap` 으로 키를 정렬해 찍었다. 합계는 흔들리지 않는다.

```text
   두 설계 — 같은 「공유 카운터」

   Arc<Mutex<Map>>  (52번)                     채널 + 주인 스레드  (이 편)
   ─────────────────────────                   ──────────────────────────────
   스레드마다 Arc 복제 → lock → 고침 → 풀기       스레드마다 Sender 복제 → send(Cmd)
   상태를 여럿이 번갈아 만진다                    상태를 주인 하나만 만진다
   실패 모드: 가드를 오래 쥐기 · 중독             실패 모드: Sender 를 안 버려 주인이 안 끝남
```

★ **속도 비교는 하지 않았다.** 고르는 기준은 **실패 모드와 코드 모양**이다.

## 문법 — 형태와 규칙

```text
   use std::sync::mpsc;

   let (tx, rx) = mpsc::channel::<T>();        // (Sender<T>, Receiver<T>) — 끝없는 버퍼
   let (tx, rx) = mpsc::sync_channel::<T>(n);  // (SyncSender<T>, Receiver<T>) — n 통, 0 이면 랑데부
   let tx2 = tx.clone();                       // 송신자는 여럿 — 수신자는 하나
   tx.send(v)?;                                // v 를 옮긴다 · Err(SendError(v)) 면 값 회수
   tx.try_send(v);                             // SyncSender 만 — Err(Full(v)) / Err(Disconnected(v))
   rx.recv();  rx.try_recv();  rx.recv_timeout(d);
   for msg in rx { … }                         // 송신자가 전부 Drop 되면 끝
   drop(tx);                                   // 「더 보낼 것 없다」를 알리는 유일한 방법
```

- ★★★ **`close` 가 없다 — 모든 `Sender` 의 `Drop` 이 곧 닫힘**이다((1)).
- ★★ **`send` 는 소유권을 옮긴다**((2)) · **실패하면 값을 돌려준다**((4)·(5)).
- ★★ **`sync_channel(n)` 은 n 통 뒤에 `send` 를 막는다 · `channel()` 은 막지 않는다**((3)).
- ★ **`Receiver` 는 하나** — `Clone` 이 없고 `!Sync` 다(std 의 트레이트 구현 목록). 여러 소비자가 나눠 받으려면 `Arc<Mutex<Receiver<T>>>` 같은 것을 따로 세워야 한다(**던지지 않았다**).

## 어디서 틀리나

### 1. ★★★ 「보낼 것을 다 보냈으니 수신 루프는 끝난다」

(1)의 5행 — **main 이 원본 `tx` 를 쥐고 있으면 안 끝난다.** 루프는 「값이 더 안 온다」를 **송신자 개수 0** 으로만 안다. 생산자에게 복제를 나눠 준 뒤 **`drop(tx)`**.

### 2. ★★ 「원본만 버리면 된다」

(1)의 6·7행 — **복제를 어딘가 쥐고 있어도 같다**(`Vec` 에 모아 둔 것 · 아직 살아 있는 생산자). `Sender` 에는 원본·복제의 구분이 없다.

### 3. ★★ 「보내고 나서 로그로 찍으면 된다」

(2) — **E0382.** `send` 가 값을 옮겼다. 보내기 전에 찍어라.

### 4. ★★ 「`sync_channel(0)` 은 버퍼가 0 이라 아무것도 못 보낸다」

(3) — **보낼 수 있다. 받는 쪽이 올 때까지 막힐 뿐**이다(랑데부). 넷 다 `received [1, 2, 3]`.

### 5. ★★ 「`channel()` 이면 배압 걱정이 없다」

(3) — **안 막히는 것이 곧 걱정거리다.** 생산자가 빠르면 큐가 자란다. 세울 필요가 있으면 `sync_channel`.

### 6. ★★ 「`send` 가 실패하면 값은 사라진다」

(4)·(5) — **돌려받는다**(`Full(v)` · `SendError(v)` 의 `e.0`). 조용히 버려지는 경로가 없다.

### 7. ★ 「`try_send` 의 에러는 `Full(..)` 로 찍힌다」

(4) — 1.92 에서는 **`"Full(..)"` 로 따옴표째** 찍힌다. **std 구현**이라 판마다 다를 수 있다 — `matches!(r, Err(TrySendError::Full(_)))` 로 **변형을 보고** 판정하라.

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| 송신자가 전부 사라지면 `recv` 가 `RecvError` · 루프 끝 | ★ **std 의 계약**(`channel`·`Receiver::iter` 문서) | (1)·(5) |
| 살아 있는 송신자가 있으면 `recv` 가 막힌다 | ★ **std 의 계약**(「at least one `Sender` alive (including clones)」) | (1) |
| `send` 뒤에 그 값을 못 쓴다 | ★ **언어**(이동 의미론 — `send(self, t: T)` 가 값을 받는다) | (2) E0382 |
| `sync_channel(0)` 이 랑데부 · n 통 뒤 막힘 | ★ **std 의 계약**(`sync_channel` 문서) | (3) |
| 한 송신자가 보낸 순서대로 받는다 | ★ **std 의 계약** | (3) |
| **여러 송신자 사이의** 도착 순서 | ★ **정해지지 않는다** — 그래서 출력에 싣지 않았다 | (6) |
| `Display` 문구 · `Debug` 모양(`"Full(..)"` · `SendError { .. }`) | ★ **std 구현** | (4)·(5) |
| 1.92 의 `mpsc::Receiver` 가 안에서 `mpmc::Receiver` 를 감싼다 | ★ **std 구현 세부** — 로컬 `src/std/sync/mpsc.rs.html` 에서 읽었다. **공개 API 가 아니다** | — |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 근거 |
|---|---|---|
| 작업을 넘기고 결과를 모은다(파이프라인) | **`channel()`** + 생산자마다 `tx.clone()` · main 은 **`drop(tx)`** | (1) |
| 여러 스레드가 한 표를 고친다 | **주인 스레드 + 명령 채널**, 또는 `Arc<Mutex<_>>`(52번) | (6) |
| 생산자가 소비자를 앞지르면 안 된다 | **`sync_channel(n)`** | (3) |
| 꽉 찼을 때 버릴지 에러로 할지 **내가** 정한다 | **`try_send`** | (4) |
| 「언제 끝나나」를 멈추지 않고 확인한다 | **`recv_timeout`** — `Timeout` 과 `Disconnected` 를 가른다 | (5) |
| 소비자가 여럿 | ★ std `mpsc` 는 **맞지 않는다**(수신자 하나) — **이 문서는 대안을 던지지 않았다** | — |

## 핵심 문장

- ★★★ **수신 루프는 「보낼 것이 끝났을 때」가 아니라 「송신자가 전부 사라졌을 때」 끝난다 — main 이 쥔 원본 `tx` 하나가 루프를 영원히 붙든다.**
- ★★★ **`send` 는 값을 옮긴다 — 보낸 쪽이 더는 못 만지므로 공유 상태 자체가 생기지 않는다.**
- ★★ **버퍼 크기는 「막히기 전에 몇 번 보낼 수 있나」다 — 0 이면 랑데부, `channel()` 이면 한 번도 안 막힌다.**
- ★★ **실패한 `send`/`try_send` 는 값을 돌려준다 — 채널에는 조용히 버려지는 경로가 없다.**
- ★ **`Timeout` 과 `Disconnected` 는 다른 답이다 — 「아직 안 왔다」와 「더는 안 온다」.**

## 관련 자료

- [`ops-patterns/05-backpressure`](../../../../cs/ops-patterns/05-backpressure/) — **배압 일반·정원과 대기 시간·오버플로 정책 넷의 정본.** 그쪽은 정책을 **구현하며 재고**, 여기는 **std `mpsc` 가 그중 무엇을 주나**(BLOCK = `sync_channel` 의 `send` · 결정 위임 = `try_send`)로 좁힌다.
- [Go 29번](../../../go/syntax/29-channels-buffering-direction-close-range-and-nil/) — Go 는 **`close` 를 명시적으로** 부르고, `range` 는 닫힌 뒤 **남은 값을 다 돈 다음** 끝난다. Rust 에는 `close` 가 없고 **송신자 전부의 `Drop`** 이 그 자리를 맡는다 — 「남은 값을 다 받고 끝난다」는 같다((5)의 `[3]`→`[4]`).
- [**49번 주제**](../49-threads-spawn-join-and-move-closures/) — 생산자에게 `tx` 를 `move` 로 넘기기 · detach.
- [**44번 주제**](../44-drop-mem-drop-replace-and-take/) — `drop(tx)` 가 부르는 것은 `Sender` 의 `Drop` 이다.
- [**52번 주제**](../52-mutex-rwlock-arc-and-poisoning/) — 공유 상태를 **잠금으로** 다루는 반대편 설계.
- [**50번 주제**](../50-send-sync-in-compiler-errors/) — 채널로 보낼 값은 `Send` 여야 한다(`Sender<T>: Send` 는 `T: Send` 일 때).
- [목록의 **54번 주제**](../54-async-await-and-future-state-machines/)(`async`) — 비동기 런타임의 채널은 이 편의 범위 밖이다.

## 용어 풀이

- **`mpsc`** — multi-producer, single-consumer. 넣는 쪽 여럿, 꺼내는 쪽 하나.
- **`Sender<T>` / `SyncSender<T>`** — 넣는 쪽. `clone` 으로 늘린다. 뒤엣것은 `sync_channel` 의 것으로 `try_send` 가 있다.
- **`Receiver<T>`** — 꺼내는 쪽. 하나뿐이고 `IntoIterator` 라 `for msg in rx` 로 돈다.
- **끊김(disconnected · hang up)** — 반대편이 전부 `Drop` 된 상태.
- **랑데부 채널** — 버퍼 0. 보내기와 받기가 **만나야** 둘 다 진행된다.
- **배압(backpressure)** — 소비자가 느릴 때 생산자를 늦추거나 거절하는 것.
- **`SendError(T)` · `TrySendError::Full(T)` · `RecvError` · `RecvTimeoutError::{Timeout, Disconnected}`** — 채널 연산의 실패 값. 앞의 둘은 **값을 싣고 돌아온다.**

## 더 들어가면

- `Receiver::recv_deadline` 은 1.92 문서의 메서드 목록에 있지만 **안정 판 표지(`Stable since`)가 붙어 있지 않다** — 이 문서는 쓰지 않았다.
- 1.92 문서에는 `std::sync::mpmc` 모듈 페이지도 있다(여러 소비자). **안정 API 인지 확인하지 않았고 던지지 않았다.**
- `select!` 처럼 여러 채널을 한꺼번에 기다리는 기능은 std `mpsc` 에 없다(Go 30번의 `select` 와 대비). **대안 크레이트는 다루지 않는다** — 외부 크레이트를 하나도 쓰지 않는 갈래다.

## 실행 환경

**기준 소스** — [std — `std::sync::mpsc` 모듈](https://doc.rust-lang.org/std/sync/mpsc/index.html) ·
[std — `mpsc::channel`](https://doc.rust-lang.org/std/sync/mpsc/fn.channel.html)(「infinite buffer」 · 「at least one `Sender` alive (including clones)」) ·
[std — `mpsc::sync_channel`](https://doc.rust-lang.org/std/sync/mpsc/fn.sync_channel.html)(「buffer size of 0 is valid … rendezvous channel」) ·
[std — `Receiver`](https://doc.rust-lang.org/std/sync/mpsc/struct.Receiver.html)(`iter` 은 「channel has hung up」이면 `None`) ·
std 소스 `std/src/sync/mpsc.rs`(`TrySendError` 의 `Debug` — 로컬 `rust-docs` 의 `src/std/sync/mpsc.rs.html`).
★ 위 문서는 **이 머신의 `rust-docs`(1.92.0) 로컬 사본**을 열어 읽었다.
**실행 검증** — 이 문서의 모든 출력·에러는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서
**`rustc --edition 2021 <파일>.rs`** 로 돌려 받은 것이다.\
★★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다. 소스 펜스도 캡처가 찍었다.\
★★★ **속도·처리량은 한 번도 재지 않았다** — 「채널이 락보다 빠르다/느리다」 류의 문장은 **근거가 없으므로 쓰지 않는다.**
