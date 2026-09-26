# rust/syntax/52 — `Mutex`/`RwLock` 과 `Arc<Mutex<T>>` · 중독 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [std — `Mutex`](https://doc.rust-lang.org/std/sync/struct.Mutex.html)(`lock` 의 같은 스레드 재잠금 문단 · §Errors · `try_lock` · `into_inner` · `clear_poison`) ·
> [std — `RwLock`](https://doc.rust-lang.org/std/sync/struct.RwLock.html) ·
> [std — `PoisonError`](https://doc.rust-lang.org/std/sync/struct.PoisonError.html) ·
> [std — `MutexGuard`](https://doc.rust-lang.org/std/sync/struct.MutexGuard.html) ·
> [Reference — Destructors · Temporary scopes](https://doc.rust-lang.org/reference/destructors.html#temporary-scopes)(`match`·`if`·`if let`·`while let` 의 임시값).
> ★ 위 문서는 **이 머신의 `rust-docs`(1.92.0) 로컬 사본**을 열어 읽었다. 판 표지(`clear_poison` 1.77.0 · `Mutex::new` 의 const 1.63.0)는 로컬 문서에서 grep 했다((6)의 `r53_since`).
> **실행 검증** — 이 문서의 모든 출력·에러는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서
> **`rustc --edition 2021 <파일>.rs`** 로 돌려 받은 것이다(가드 격자만 2021·2024 둘).\
> ★★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다. 소스 펜스도 캡처가 찍었다.\
> ★★★ **속도는 한 번도 재지 않았다** — 「`RwLock` 이 `Mutex` 보다 빠르다」·「락은 느리다」 류의 문장은 **근거가 없으므로 쓰지 않는다.**
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

★★★ **본체 창 — ① 가드 해제 격자(모양마다 두 번째 잠금이 막히나)다.** 판정은 **`try_lock` 한 번**으로 한다 — `lock` 을 두 번 부르면 교착으로 멈추므로((7)), 멈추지 않는 물음으로 바꿔 물었다.

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| ★★ **흔들린다(정규화)** | 패닉 첫 줄의 **스레드 id** `thread '<unnamed>' (NNN)` · `thread 'main' (NNN)` | 실행마다 바뀐다 — 기본 규칙이 `(<tid>)` 로 바꾼다 |
| 안 흔들린다 | ★★★ **가드 격자의 `blocked`/`free` 칸과 「`blocked cells: N / M`」** | 가드가 버려지는 줄은 **언어**(임시값 스코프)가 정한다 — **이 주제의 본체** |
| 안 흔들린다 | `total 800000` · `strong after join 1` · 중독 로그 `[1]`\~`[8]` · `RwLock` 격자 | 동기화가 걸린 값·순서다(`join` 뒤에 읽는다) |
| 안 흔들린다 — 단 **std 판의 문구** | `poisoned lock: another task failed inside` · `PoisonError { .. }` | ★ **std 구현**이다. 「`Err` 가 온다」는 계약, **문구는 구현** |
| ★ **관찰일 뿐** | 같은 스레드 재잠금의 `(exit 124)` | std 는 「unspecified」라고 적는다((7)) — 이 판·이 OS 에서 멈췄다는 한 판의 결과 |
| 안 흔들린다 | E0499 번호·`파일:줄:칸` · 종료 코드(`101`) | 같은 rustc 판에서 고정이다 |

★ 정규화 규칙은 **기본 넷**만 쓴다(패닉 스레드 id 가 걸린다). 격자는 `try_lock` 결과만 칸에 옮겨 스레드 id 가 들어가지 않는다.

## 한눈에 — 쉽게 말하면

**`Mutex<T>` 는 「물건이 든 금고」이고, 가드는 「금고 문이 열려 있는 동안 손에 쥔 열쇠」다.
다른 언어의 락은 「금고 옆에 걸어 둔 열쇠」라서, 열쇠 없이 물건에 손을 대도 아무도 말리지 않는다.
Rust 는 물건을 **금고 안에** 넣어 버렸다 — 열쇠(가드)를 받지 않으면 물건에 닿을 길 자체가 없다.
그리고 열쇠는 **손을 놓는 순간(가드가 `Drop` 될 때)** 돌려준다. 언제 손을 놓는지가 이 주제의 절반이다.**

| 비유 | 실체 |
|---|---|
| 「**금고 안의 물건**」 | ★★★ **`Mutex<T>` 의 `T`** — `lock()` 을 거치지 않으면 `&mut T` 를 얻을 방법이 없다((2)) |
| 「**손에 쥔 열쇠**」 | ★★ **`MutexGuard<T>`** — `Deref`/`DerefMut` 로 `T` 처럼 쓰인다 |
| 「**손을 놓는 때**」 | ★★★ **가드가 `Drop` 될 때** — 스코프 끝·`drop(g)`·**문장 끝(임시값)**·**`match`/`if let`/`while let` 이 든 문장 끝**((1)) |
| 「**문 앞에서 한 번 당겨 보기**」 | ★★ **`try_lock()`** — 잠겨 있으면 기다리지 않고 `Err`((1)의 판정 도구) |
| 「**열쇠를 쥔 채 쓰러진 사람**」 | ★★★ **중독(poisoning)** — 가드를 쥔 스레드가 패닉하면 다음 `lock()` 은 `Err(PoisonError)`((4)) |
| 「**그래도 물건은 꺼낼 수 있다**」 | ★★ **`PoisonError::into_inner()`** · **`clear_poison()`**(1.77)((4)) |
| 「**구경은 여럿, 손대는 건 혼자**」 | ★ **`RwLock<T>`** — 읽기 가드 여럿 또는 쓰기 가드 하나((6)) |
| 「**금고를 여럿이 나눠 들기**」 | ★ **`Arc<Mutex<T>>`** — `'static` 스레드에 넘길 때. 스코프 스레드면 `&Mutex<T>` 로 충분((3)) |

```text
   다른 언어의 락                              Rust 의 Mutex<T>

   lock ─┐    count                            Mutex ┌──────────┐
         │    (옆에 따로 있다)                        │  count   │   ← lock() 이 준 가드로만 닿는다
   lock()│    count += 1   ← 락 없이도 된다          └──────────┘
         │                                      g = m.lock()  →  *g += 1
   unlock┘                                      g 가 Drop 되면 → 풀린다

   (2) r52_wrap        : 락을 옆에 두면 → E0499 (컴파일러는 그 락이 count 를 지키는 줄 모른다)
   (2) r52_wrap_fix    : count 를 Mutex 안에 → 통과, 2
```

> **가드(guard)** — `lock()` 이 돌려주는 `MutexGuard<T>`. 이것을 쥔 동안만 안의 값에 닿을 수 있고, **`Drop` 될 때 잠금이 풀린다.**\
> 예: `let mut g = m.lock().unwrap(); g.push(1);` — `g` 의 스코프가 끝나면 풀린다.

> **중독(poisoning)** — std 의 말: 가드를 쥔 스레드가 패닉하면 그 락은 **중독된** 것으로 표시되고, 이후의 `lock()` 은 `Err` 를 돌려준다. 데이터가 **반쯤 고쳐진 채** 남았을 수 있다는 경고다.\
> 예: 스레드가 `g.push(4)` 뒤 패닉 → 다음 `m.lock()` 은 `Err(PoisonError { .. })`.

## 이 주제가 답하려는 질문

1. ★★★ **가드는 정확히 언제 풀리나** — 변수·`drop`·임시값·`match`·`if`·`if let`·`while let`, 그리고 에디션((1)).
2. ★★★ **왜 락이 데이터를 감싸는 타입인가** — 감싸지 않으면 무엇이 안 되나((2)·(3)).
3. ★★ **중독된 락을 어떻게 다루나** — `Err` 의 정체 · 값 꺼내기 · 되돌리기((4)·(5)).

★ **선행** — [**51번 주제**](../51-mpsc-channels-and-sender-drop/) — 채널은 **소유권을 넘겨** 공유 상태를 없앤다. 이 편은 반대로 **공유 상태를 두고 규칙을 붙인다.**
[**42번 주제**](../42-refcell-cell-interior-mutability/)가 **같은 모양의 격자**를 `RefCell` 로 이미 쟀다 — 런타임 빌림 격자 `panic cells: 5 / 12` · `if let` 에디션 격자 `3 / 4`. 이 편의 (1)은 그 **스레드 판**이다(`borrow_mut` 의 패닉 대신 `try_lock` 의 `Err`).
[**44번 주제**](../44-drop-mem-drop-replace-and-take/)가 `let _ = m.lock().unwrap();` 이 **기본 거부 린트 `let_underscore_lock`** 으로 컴파일 에러임을 쟀다 — 그래서 (1)의 격자에서 그 행을 뺐다(던지면 컴파일이 안 된다).
[**49번 주제**](../49-threads-spawn-join-and-move-closures/)의 `thread::scope` · [**50번 주제**](../50-send-sync-in-compiler-errors/)의 경계 격자(`Mutex<i32>` 는 send·sync 둘 다 통과, `MutexGuard` 는 send 만 막힘)가 (3)의 전제다.

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ① 가드 해제 격자다

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ① ★★★ **가드 해제 격자**(모양마다 소스를 만들어 **실행**, 판정은 `try_lock`) × 에디션 둘 | 가드가 **어느 줄까지** 사나 | ★ **본체**((1)) |
| ② ★★ **컴파일러 진단** E0499 | 락이 데이터 **옆에** 있으면 왜 안 되나 | 쓴다((2)) |
| ③ ★★ **중독 로그**(`is_poisoned`·`Err`·`into_inner`·`clear_poison`) | 패닉 뒤의 락 상태 | 쓴다((4)·(5)) |
| ④ ★ **`RwLock` 격자**(`try_read`·`try_write`) | 읽기 여럿 / 쓰기 하나 | 쓴다((6)) |
| ⑤ ★ **`timeout` 의 종료 코드** | 같은 스레드 재잠금이 돌아오나 | 쓴다 — **관찰**((7)) |
| 실행 시간 · 경합 비용 · `RwLock` 대 `Mutex` 속도 | 「어느 쪽이 빠르다」 | ★ **부적용 — 재지 않는다** |
| 데이터 레이스 탐지기(TSan·Miri) | — | ★ **잴 것이 없다** — 안전한 코드에서 락 없이 공유 값을 고치는 프로그램은 **컴파일이 안 된다**((2)). 탐지할 실행 파일이 생기지 않는다 |

★★ **제5의 상태 — 「같은 질문을 다른 창으로」.** 「이 자리에서 가드가 아직 살아 있나」의 정직한 창은 **두 번째 `lock()`** 이다. 그런데 그 창은 살아 있으면 **영영 돌아오지 않는다**((7) — 멈춘다). 그래서 같은 질문을 **`try_lock()` 의 `Ok`/`Err`** 로 옮겨 물었다.
★ 바꾼 창이 **못 보는 것** — **다른 스레드가 쥔 가드와 내 스레드가 쥔 가드를 가르지 않는다.** `try_lock` 은 「지금 잠겨 있나」만 답한다. 격자는 스레드가 하나라서 「잠겨 있다 = 앞의 가드가 살아 있다」로 읽을 수 있을 뿐이다.

### (1) ★★★ 가드 해제 격자 — 열두 모양 × 두 에디션

**언제 쓰나** — 락을 쥔 코드에서 「여기서 다시 잠그면 막히나(교착하나)」를 판정할 때마다.

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

- ★★★ **「`blocked cells: 13 / 24`」.** **두 에디션 열이 서로 다른 행은 `if let … else` 의 else 갈래 행**이다(2021 `blocked` · 2024 `free`). 그 밖의 행은 두 열이 같다. ★ 스크립트는 「갈린 행」을 따로 세지 않았다 — 표를 행으로 읽은 것이다.
- ★★ **변수에 담으면 스코프 끝까지** — `let g` 도 `let _g` 도 `blocked`(1·2행). **`_g` 는 이름 있는 변수**다. `let _ = …` 만 그 자리에서 버리는데 그것은 컴파일 에러다(44번 — `let_underscore_lock`).
- ★★ **풀어 주는 세 가지** — 안쪽 블록 끝(3행) · `drop(g)`(4행) · **자기 문장이 끝난 임시값**(5행). `let n = m.lock().unwrap().len();` 도 `free`(6행) — `len()` 이 `usize` 를 넘기고 그 `let` 문장 끝에서 가드가 버려진다.
- ★★★ **한 문장 안이면 겹친다** — 7행 `m.lock().unwrap().push(probe(&m));` 은 `blocked`. 수신자의 가드가 **인자를 평가하는 동안** 살아 있다. 실제 코드에서 `probe` 자리에 `m.lock()` 을 쓰면 **교착**이다.
- ★★★ **`match` 의 조사 대상은 문장 끝까지** — 8행 `blocked`. 값은 `usize` 하나인데도 가드가 팔 전체를 따라간다.
- ★★ **`if` 조건은 조건 직후에 풀린다** — 9행 `free`. `match` 와 `if` 가 반대다 — 42번 (1)의 10·11행과 **같은 모양 같은 답**이다.
- ★★★ **`if let` 의 then 본문은 두 에디션 다 `blocked`**(10행) · **else 갈래만 2024 에서 `free`**(11행). 42번 (2)의 `3 / 4` 와 같은 규칙이다 — 2024 가 바꾼 것은 「`if let` 임시값은 `else` 블록 전에 버려진다」까지다.
- ★★★ **`while let` 은 본문 내내 쥔다** — 12행 `blocked`(두 에디션 다). `while let Some(x) = m.lock().unwrap().pop() { … }` 의 본문에서 같은 락을 다시 잡으면 **매 바퀴** 교착이다. **꺼낸 뒤 가드를 버리는 모양**(`let x = m.lock().unwrap().pop();` 을 루프 안에서 따로)으로 바꾼다.

```text
   가드(MutexGuard)는 언제 풀리나 — (1)의 blocked / free 가 이 표로 갈린다

   let g = m.lock().unwrap();            변수          → 스코프 끝(또는 drop(g))       1·2·3·4행
   m.lock().unwrap().push(1);            임시값        → 그 문장의 끝                   5·6행 free
   m.lock().unwrap().push(<다시 잠금>)   한 문장 안     → 인자 평가 동안 살아 있다        7행 blocked
   match m.lock().unwrap().len() {…};    scrutinee     → match 가 든 문장의 끝          8행 blocked
   if m.lock().unwrap().len() < 9 {…}    if 조건        → 조건 평가 직후                 9행 free
   if let … = m.lock()… {…} else {…}     scrutinee     → then: 끝까지 / else: 2024 만 전에   10·11행
   while let … = m.lock()….pop() {…}     scrutinee     → 본문 내내                      12행 blocked
```

★ 42번과의 차이는 **실패의 모양**이다 — `RefCell` 은 겹치면 **패닉**하지만, `Mutex` 를 같은 스레드에서 겹쳐 `lock()` 하면 **돌아오지 않는다**((7)). 격자에서 `try_lock` 을 쓴 이유다.

### (2) ★★★ 락이 데이터를 감싸는 이유 — 옆에 둔 락은 컴파일러가 모른다

**언제 쓰나** — C·Java 식으로 「락 하나 + 공유 변수 하나」를 짜려는 순간.

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

- ★★★ **E0499 — cannot borrow `count` as mutable more than once at a time.** 두 클로저가 **둘 다 `lock` 을 잡고 나서** `count += 1` 을 하는데도 거부된다. 컴파일러가 보는 것은 **`count` 에 대한 가변 빌림 둘**뿐이고, `lock` 이 그 둘을 떼어 놓는다는 사실은 **타입 어디에도 적혀 있지 않다.**
- ★★ 표지 「first borrow occurs due to use of `count` in closure」 · 「second mutable borrow occurs here」 — 겹침은 **클로저 단위**로 잡혔다.

**`count` 를 `Mutex` 안에 넣으면.**

```text
===== 소스: r52_wrap_fix.rs =====
use std::sync::Mutex;
use std::thread;

fn main() {
    let count = Mutex::new(0);
    thread::scope(|s| {
        for _ in 0..2 {
            s.spawn(|| {
                *count.lock().unwrap() += 1;
            });
        }
    });
    println!("{}", count.into_inner().unwrap());
}
===== rustc --edition 2021 r52_wrap_fix.rs =====
(exit 0)
===== ./r52_wrap_fix =====
2
(exit 0)
```

- ★★★ **통과 — `2`.** 이제 `count` 에 닿는 길은 `lock()` 이 주는 가드뿐이라 **「잠그고 고친다」가 타입으로 강제된다.** 공유된 것은 `&Mutex<i32>`(공유 참조)이고, `Mutex<i32>: Sync` 라서 두 스레드가 나눠 가져도 된다(50번 경계 격자의 `Mutex<i32>` 행).
- ★ 끝에서 `count.into_inner()` — 스코프가 끝나 **빌린 자가 없으니** 금고째 열어 값을 꺼낸다. `Result` 인 이유는 중독 때문이다((4)).
- ★ 이 소스에는 **`Arc` 가 없다** — `thread::scope` 는 빌림을 허용하므로(49번) `&Mutex` 로 충분했다.

### (3) ★★ `Arc<Mutex<T>>` — `'static` 스레드에 나눠 줄 때

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

- ★★ **`total 800000`** — 8 스레드 × 100000 번 `*t.lock().unwrap() += 1`. 가드가 **문장마다** 풀리므로((1)의 5행) 스레드끼리 번갈아 잡는다.
- ★★ **`strong after join 1`** — 스레드마다 가졌던 `Arc` 복제가 스레드와 함께 버려졌다(41번 (3)의 `strong 2 → 1` 과 같은 모양).
- ★★ **역할 분담** — `Arc` 는 「주인 여럿」(`thread::spawn` 이 `'static` 을 요구하므로 빌림 대신 소유권 공유), `Mutex` 는 「공유 참조로 고치기」. 42번의 `Rc<RefCell<T>>` 의 **스레드 판**이 `Arc<Mutex<T>>` 다.
- ★ **`thread::scope` 를 쓸 수 있으면 `Arc` 는 필요 없다**((2)의 `r52_wrap_fix`). `Arc` 는 스레드가 **함수보다 오래 살 수 있을 때**의 값이다.
- ★ 이 블록은 **맞는 값이 나왔다는 것만** 보인다. 동기화 없는 판과의 대비(잃은 갱신)는 목록의 **53번 주제**가 원자 연산 격자로 쟀다.

### (4) ★★★ 중독 — 가드를 쥔 채 패닉하면

**언제 쓰나** — `lock().unwrap()` 을 쓰는 모든 곳. 그 `unwrap` 이 무엇을 풀고 있는지 알아야 한다.

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

- ★★★ **`[2] is_poisoned true` · `[3] lock() is_err true`** — 자식 스레드가 가드를 쥔 채 패닉했다. std §Errors: 「If another user of this mutex panicked while holding the mutex, then this call will return an error once the mutex is acquired.」 — ★ **잠금 자체는 얻는다**(「once the mutex is acquired」). `Err` 안에 **가드가 들어 있다.**
- ★★ **`[4] Debug PoisonError { .. }` · `[5] Display "poisoned lock: another task failed inside"`** — 문구는 std 구현이다.
- ★★★ **`[6] into_inner -> guard, data [1, 2, 3, 4]`** — `PoisonError::into_inner()` 가 가드를 돌려준다. **패닉 직전의 `push(4)` 가 들어 있다** — 중독은 「데이터가 망가졌다」가 아니라 **「중간 상태일 수 있다」는 표시**다. 그 값이 쓸 만한지는 **프로그램이 판단한다.**
- ★★ **`[7] still poisoned after that true`** — 값을 꺼내 봤다고 표시가 지워지지 않는다.
- ★★ **`[8] after clear_poison: is_poisoned false  lock is_ok true`** — `clear_poison()` 은 **1.77.0** 부터다(로컬 문서의 판 표지):

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

- ★ 표준 오류 한 흐름에 **자식의 패닉 → `[1]`\~`[8]`** 순으로 찍혔다. 마커를 전부 `eprintln!` 으로 찍어 **한 스트림**에 두었다(규칙 18).

### (5) ★★ 중독을 `unwrap` 하면 — 패닉이 번진다

```text
===== 소스: r52_poison_unwrap.rs =====
use std::sync::Mutex;
use std::thread;

static M: Mutex<i32> = Mutex::new(0);

fn main() {
    let _ = thread::spawn(|| {
        let _g = M.lock().unwrap();
        panic!("first panic");
    })
    .join();
    let g = M.lock().unwrap();
    eprintln!("not reached {}", *g);
}
===== rustc --edition 2021 r52_poison_unwrap.rs =====
(exit 0)
===== ./r52_poison_unwrap =====

thread '<unnamed>' (3313397) panicked at r52_poison_unwrap.rs:9:9:
first panic
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace

thread 'main' (3313396) panicked at r52_poison_unwrap.rs:12:22:
called `Result::unwrap()` on an `Err` value: PoisonError { .. }
(exit 101)
```

- ★★★ **`main` 스레드의 두 번째 패닉** — ``called `Result::unwrap()` on an `Err` value: PoisonError { .. }`` · `exit 101`. 첫 패닉은 자식에서 났는데 **두 번째 패닉이 `main` 에서** 난다. `lock().unwrap()` 은 「중독이면 나도 패닉한다」는 선택이다.
- ★★ **관용구가 `lock().unwrap()` 인 이유** — 중독된 상태를 **이어서 쓸 근거가 없으면** 멈추는 것이 안전한 기본값이라서다. 복구할 근거가 있으면 (4)처럼 `into_inner()` 로 꺼낸다(`lock().unwrap_or_else(|e| e.into_inner())` 꼴). ★ **이 한 줄 꼴은 던지지 않았다** — (4)의 `into_inner` 가 같은 일을 한 블록이다.
- ★ `static M: Mutex<i32> = Mutex::new(0);` — `Mutex::new` 가 **const 1.63.0** 이라 `static` 에 바로 둔다((4)의 판 표지). 전역 초기화 쪽은 53번.

### (6) ★ `RwLock` — 읽기 여럿 / 쓰기 하나

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

- ★★ **읽기 가드를 쥔 동안 `try_read ok`, `try_write no`**(one read · two reads) · **쓰기 가드를 쥔 동안 둘 다 `no`**(one write). 규칙은 42번 `RefCell` 과 같다 — 「공유 여럿 또는 독점 하나」. 42번 (7)에서 컴파일러가 `RefCell` 의 스레드 판으로 **`RwLock`** 을 권한 이유다.
- ★ 블록이 끝나면 가드가 버려져 다시 `ok ok`(마지막 줄).
- ★ **`RwLock` 이 `Mutex` 보다 빠르다는 주장은 하지 않는다 — 재지 않았다.** 이 블록이 보이는 것은 **어느 조합이 허용되나**뿐이다.

### (7) ★ 같은 스레드에서 두 번 `lock()` — 관찰일 뿐

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

- ★★ **`[1]` 만 찍히고 `(exit 124)`** — `timeout 2` 가 2초 뒤 끊었다. **`[2]` 는 안 찍혔다.**
- ★★★ **이것은 보장이 아니라 관찰이다.** std: 「The exact behavior on locking a mutex in the thread which already holds the lock is **left unspecified**. However, this function **will not return on the second call** (it might panic or deadlock, for example).」 — 보장은 **「돌아오지 않는다」** 까지다. 이 판·이 OS 에서 멈춘(교착) 것은 한 판의 결과다.
- ★ 그래서 (1)의 격자는 `lock` 이 아니라 `try_lock` 으로 물었다(제5의 상태).
- ★ 재진입 락이 필요하면 std 에 `ReentrantLock` 이 있다(1.92 문서 목록에 있음) — **이 문서는 던지지 않았다.**

## 문법 — 형태와 규칙

```text
   use std::sync::{Arc, Mutex, RwLock};

   let m = Mutex::new(v);               // 데이터를 감싼다 — const fn (1.63) 이라 static 에도
   let mut g = m.lock().unwrap();       // LockResult<MutexGuard<T>> — 중독이면 Err
   *g += 1;                             // 가드는 DerefMut
   drop(g);                             // 가드를 버리면 풀린다
   m.try_lock()                         // TryLockResult — 잠겨 있으면 기다리지 않고 Err
   m.is_poisoned()  m.clear_poison()    // 중독 확인 · 되돌리기(1.77)
   m.into_inner()                       // 금고째 열어 T 를 꺼낸다 — Result(중독)

   let shared = Arc::new(Mutex::new(v)); // 'static 스레드에 나눠 줄 때
   let l = RwLock::new(v);  l.read()  l.write()  l.try_read()  l.try_write()
```

- ★★★ **데이터는 락 안에 있다 — 가드 없이는 닿을 수 없다**((2)).
- ★★★ **가드는 `Drop` 될 때 풀린다** — 변수면 스코프 끝, 임시값이면 문장 끝, **`match`·`if let`(then)·`while let` 의 조사 대상이면 그 구문 끝**((1)).
- ★★ **`if let` 의 else 갈래만 2024 에서 가드가 먼저 풀린다**((1)의 11행).
- ★★ **`lock()` 의 `Err` 는 중독이다 — 잠금은 얻었고, 가드가 `Err` 안에 있다**((4)).
- ★ **`let _ = m.lock().unwrap();` 은 컴파일 에러**(44번 — `let_underscore_lock`).

## 어디서 틀리나

### 1. ★★★ 「`m.lock().unwrap().len()` 은 `usize` 만 남으니 가드는 바로 풀린다」

(1)의 8·10·12행 — **`match`·`if let`·`while let` 의 조사 대상이면 그 구문 끝까지 산다.** 문장 하나로 된 `let n = …;` 이면 풀린다(6행). **값을 먼저 `let` 에 담아라.**

### 2. ★★★ 「`while let Some(job) = queue.lock().unwrap().pop()` 은 한 번 꺼내고 놓는다」

(1)의 12행 — **본문 내내 쥔다.** 본문에서 같은 큐에 넣으면 교착이다. 2024 에디션도 같다.

### 3. ★★★ 「락만 잡으면 옆의 변수를 고쳐도 된다」

(2) — **E0499.** 컴파일러는 그 락이 무엇을 지키는지 모른다. **데이터를 `Mutex` 안에 넣어야** 「잠그고 고친다」가 타입이 된다.

### 4. ★★ 「중독된 락은 데이터가 망가져서 못 쓴다」

(4) — `into_inner()` 로 **패닉 직전 상태**(`[1, 2, 3, 4]`)를 꺼낼 수 있고, `clear_poison()` 으로 표시를 지울 수 있다. 중독은 **「확인해라」라는 표시**다.

### 5. ★★ 「`lock()` 이 `Err` 면 잠금을 못 얻은 것이다」

(4) — std: 「once the mutex is **acquired**」. **얻었고**, 가드는 `Err` 안에 있다. 못 얻은 것은 `try_lock` 의 `WouldBlock` 쪽이다.

### 6. ★★ 「같은 스레드에서 두 번 잠그면 패닉한다」 / 「교착한다」

(7) — std 는 **unspecified** 다. 보장은 「돌아오지 않는다」 뿐이고, 이 판에서 멈춘 것은 관찰이다.

### 7. ★ 「`Mutex` 는 늘 `Arc` 로 감싸야 한다」

(2) — `thread::scope` 면 `&Mutex<T>` 로 된다. `Arc` 는 `'static` 스레드용이다((3)).

### 8. ★ 「`RwLock` 이 `Mutex` 보다 빠르니 읽기가 많으면 `RwLock`」

**이 문서는 재지 않았다.** 적을 수 있는 것은 **허용 조합**((6))뿐이다.

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| 가드가 **어느 줄에서** 버려지나(임시값 스코프) | ★ **언어**(Reference — Destructors · Temporary scopes) | (1) |
| `if let` 임시값이 2024 에서 `else` 전에 버려진다 | ★ **언어 · 에디션** | (1)의 11행 |
| 락 옆의 변수를 두 스레드가 고치면 거부 | ★ **언어**(빌림 규칙 E0499) | (2) |
| `Mutex<T>: Sync`(`T: Send` 일 때) · `MutexGuard: !Send` | ★ **std 의 트레이트 구현** — 컴파일러가 강제 | 50번 |
| 가드를 쥔 채 패닉하면 `lock()` 이 `Err` | ★ **std 의 계약**(`lock` §Errors) | (4) |
| 중독 문구 · `PoisonError { .. }` 의 `Debug` | ★ **std 구현** — 판에 매인다 | (4) |
| 같은 스레드 재잠금 | ★ **std: unspecified** — 「돌아오지 않는다」만 계약 | (7) |
| 재잠금에서 **멈췄다**(`exit 124`) | ★ **이 판·이 OS 의 관찰** | (7) |
| `clear_poison` 1.77.0 · `Mutex::new` const 1.63.0 | ★ **std 판 표지**(로컬 문서) | (4) |
| 락의 속도 · 공정성 · 대기열 순서 | ★ **구현 세부** — **재지 않았다** | — |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 근거 |
|---|---|---|
| 상태를 **한 스레드가 소유**할 수 있다 | ★ **채널**(51번) — 락이 아예 없다 | 51번 |
| 여러 스레드가 **같은 값을 고친다** | **`Mutex<T>`** — 스코프 스레드면 `&Mutex`, 아니면 `Arc<Mutex<T>>` | (2)·(3) |
| 읽기 여럿이 동시에 봐야 한다 | **`RwLock<T>`** — 허용 조합만 근거, 속도는 재지 않았다 | (6) |
| 카운터 하나·플래그 하나 | 락 없이 되는지 먼저 본다 — 목록의 **53번 주제** | — |
| 가드를 쥔 채 `await` 한다 | ★ **다른 문제** — 목록의 **55번 주제** | — |
| 루프 조건에서 잠근다(`while let … lock()`) | ★ **꺼내기와 처리를 떼라** | (1)의 12행 |
| 중독을 복구할 근거가 있다 | `into_inner()` · `clear_poison()` | (4) |

## 핵심 문장

- ★★★ **Rust 의 락은 데이터를 감싼다 — 가드 없이는 닿을 길이 없어서, 「잠그고 고친다」가 타입이 된다.**
- ★★★ **가드는 `Drop` 될 때 풀린다 — `match`·`if let`(then)·`while let` 의 조사 대상이면 그 구문 끝까지 쥔다.**
- ★★ **에디션 2024 가 이 격자에서 바꾼 것은 `if let` 의 else 갈래 행이다 — then 본문·`match`·`while let` 은 그대로다.**
- ★★ **중독된 `lock()` 은 잠금을 얻고 `Err` 안에 가드를 넣어 준다 — 데이터는 꺼낼 수 있고, 판단은 프로그램이 한다.**
- ★ **같은 스레드 재잠금은 unspecified 다 — 보장은 「돌아오지 않는다」뿐이다.**

## 관련 자료

- [`../../../../process-thread/`](../../../../process-thread/) — §10 경쟁 조건 · §11 상호 배제와 Lock. **상호 배제의 원리는 거기, 여기는 Rust 의 락이 데이터를 감싸는 방식과 가드의 수명으로 좁힌다.**
- [**42번 주제**](../42-refcell-cell-interior-mutability/) — 같은 모양의 **단일 스레드 판**(`panic cells: 5 / 12` · `3 / 4`). 그쪽은 겹치면 패닉, 여기는 겹치면 교착.
- [**44번 주제**](../44-drop-mem-drop-replace-and-take/) — `let _ = m.lock()` 의 `let_underscore_lock` · `Drop` 순서.
- [**49번 주제**](../49-threads-spawn-join-and-move-closures/) — `thread::scope` 가 `Arc` 없이 빌림을 허용하는 이유.
- [**50번 주제**](../50-send-sync-in-compiler-errors/) — `Mutex`·`MutexGuard` 의 `Send`/`Sync` 칸.
- [**51번 주제**](../51-mpsc-channels-and-sender-drop/) — 공유하지 않는 설계(채널).
- [**53번 주제**](../53-atomics-oncelock-and-lazylock/) — 락 없이 되는 경우 · `static` 에 두는 전역.
- 목록의 **55번 주제** — `await` 를 가로지르는 락.
- 대비 한 줄씩 —
  [Go 32번](../../../go/syntax/32-sync-mutex-rwmutex-waitgroup-once/): Go 의 `sync.Mutex` 는 데이터를 감싸지 않고, **값으로 복사하면 컴파일러가 아니라 `go vet` 의 `copylocks` 가** 잡는다(그 편의 탐침 18 중 13 이 답했다) ·
  [Kotlin 56번](../../../kotlin/syntax/56-channel-mutex-and-shared-mutable-state/): kotlinx `Mutex` 는 KDoc 이 **non-reentrant** 라고 적고, `synchronized` 블록 안의 중단점은 **컴파일 에러**다 ·
  [Python 53번](../../../python/syntax/53-gil-and-choosing-concurrency/): `n += 1` 은 바이트코드 명령 넷이라 GIL 이 한 덩어리로 묶지 않는다(그 격자에서는 안 잃었지만 **보장이 아니다**).

## 용어 풀이

- **`Mutex<T>`** — 한 번에 한 스레드만 안의 `T` 에 닿게 하는 락. 데이터를 감싼다.
- **`MutexGuard<T>`** — `lock()` 이 주는 가드. `Deref`/`DerefMut` 로 `T` 처럼 쓰이고, `Drop` 될 때 풀린다. `!Send`.
- **`try_lock`** — 기다리지 않는 잠금 시도. 잠겨 있으면 `Err(TryLockError::WouldBlock)`.
- **중독(poisoning)** — 가드를 쥔 스레드가 패닉했다는 표시. 이후 `lock()` 이 `Err(PoisonError)`.
- **`PoisonError<G>`** — 중독 오류. `into_inner()` 로 안의 가드(`G`)를 꺼낸다.
- **`RwLock<T>`** — 읽기 가드 여럿 또는 쓰기 가드 하나를 허용하는 락.
- **`Arc<T>`** — 원자적 참조 카운팅 공유 소유권(41번). 스레드에 나눠 줄 때 쓴다.
- **조사 대상(scrutinee)** — `match x`·`if let P = x`·`while let P = x` 의 `x`. 그 임시값은 구문 전체만큼 산다.

## 더 들어가면

- `Condvar` — 가드를 넘겨주며 기다리기. **이 문서는 던지지 않았다.**
- `MutexGuard::map`(`MappedMutexGuard`) — 1.92 문서 목록에 있다. 안정화 여부는 **확인하지 않았다.**
- std 에 `sync::nonpoison` 모듈이 1.92 문서에 보인다 — **안정 여부를 확인하지 않았고 던지지 않았다.**
