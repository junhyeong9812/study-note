# rust/syntax/50 — `Send`/`Sync` 가 코드에 나타나는 방식 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [std — `std::marker::Send`](https://doc.rust-lang.org/std/marker/trait.Send.html)(「Types that can be transferred across thread boundaries」 · 자동 구현 · 구현 목록) ·
> [std — `std::marker::Sync`](https://doc.rust-lang.org/std/marker/trait.Sync.html)(「a type `T` is `Sync` if and only if `&T` is `Send`」) ·
> [std — `MutexGuard`](https://doc.rust-lang.org/std/sync/struct.MutexGuard.html)(`!Send` · `T: Sync` 이면 `Sync`) ·
> [Rustonomicon — Send and Sync](https://doc.rust-lang.org/nomicon/send-and-sync.html)(자동 트레이트 · `unsafe impl`) ·
> [Reference — Closure types · Capture precision](https://doc.rust-lang.org/reference/types/closure.html)(2021 정밀 포착).
> ★ std 문서는 **이 머신의 `rust-docs`(1.92.0) 로컬 사본**을 열어 읽었다 — 구현 목록은 (4)의 `r50_impls` 블록이 직접 grep 한다.
> **실행 검증** — 이 문서의 모든 출력·에러는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서
> **`rustc --edition 2021 <파일>.rs`** 로 돌려 받은 것이다(에디션 대조 한 곳은 2018·2021).\
> ★★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다. 소스 펜스도 캡처가 찍었다.\
> ★★ **속도는 한 번도 재지 않았다.** 이 주제는 **컴파일러가 막는가**만 다룬다 — 거의 모든 근거가 **컴파일 로그**다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

★★★ **본체 창 — ① 경계 격자(타입 × 「보내기 / 함께 보기」 → 컴파일되나)다.** 두 마커는 실행 중에 아무 일도 하지 않는다 — **판정은 전부 컴파일 시점**이고, 그래서 창도 실행 결과가 아니라 **컴파일러 진단**이다.

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| 안 흔들린다 | ★★★ **격자의 통과/에러 칸과 「compiling cells N / M」** | 트레이트 구현은 std 와 컴파일러가 정한다 — **이 주제의 본체** |
| 안 흔들린다 | E0277 · E0658 번호 · `파일:줄:칸` · `note:` 사슬의 순서 · 종료 코드 | 같은 rustc 판에서 고정이다 |
| 안 흔들린다 — 단 **rustc 판의 문구** | ★★ `cannot be sent between threads safely` / `cannot be shared between threads safely` · `required because it appears within the type` | ★ **진단 문구는 rustc 구현**이다. 판이 바뀌면 바뀔 수 있다 — **「E0277 로 막힌다」가 계약, 문구는 구현** |
| 흔들린다 | ★ **없다** — 실행 출력은 `r50_auto`·`r50_unsafe_impl` 두 줄뿐이고 스레드 id 도 안 찍힌다 | 정규화 규칙은 기본 넷만 쓴다(걸리는 칸이 없다) |

## 한눈에 — 쉽게 말하면

**`Send` 는 「택배로 부쳐도 되는 물건」 표시이고, `Sync` 는 「여러 사람이 같이 들여다봐도 되는 물건」 표시다.
표시는 사람이 붙이지 않는다 — **상자 안의 물건이 전부 표시가 있으면 상자에도 자동으로 붙는다.**
하나라도 표시 없는 물건(예: `Rc`)이 들어 있으면 상자째 거절되고, 컴파일러는 **「상자 → 안쪽 상자 → 그 물건」** 순서로 어디서 막혔는지 적어 준다.**

| 비유 | 실체 |
|---|---|
| 「**택배로 부치기**」 | ★★ **`Send`** — 값을 `move` 로 다른 스레드에 **넘긴다**((1)의 `send` 열) |
| 「**여럿이 같이 들여다보기**」 | ★★ **`Sync`** — 값은 제자리에 두고 여러 스레드가 **`&` 로 함께 본다**((1)의 `sync` 열). std: 「`T` 가 `Sync` ⟺ `&T` 가 `Send`」 |
| 「**상자에 자동으로 붙는 표시**」 | ★★★ **자동 트레이트** — 필드가 전부 `Send` 면 구조체도 `Send`((4)) |
| 「**어느 물건 때문에 거절됐나 적힌 쪽지**」 | ★★★ **`note: required because it appears within the type …`** 사슬((2)) |
| 「**일부러 붙이는 ‘부치지 마시오’ 딱지**」 | ★ **`PhantomData<*const ()>`** 필드((5)) |
| 「**보증인이 서명하고 억지로 붙이는 표시**」 | ★ **`unsafe impl Send`** — 컴파일러는 믿는다. 책임은 사람((6)) |
| 「**그 자리에서만 쓰는 번호표**」 | ★★ **`MutexGuard`** — 다른 스레드로 못 부친다(`!Send`), 같이 보는 것은 된다((7)) |

```text
   한 값이 스레드 경계를 넘는 두 가지 길 — (1) 격자의 두 열

   send 열                                    sync 열
   ─────────────────────────                  ─────────────────────────────────
   let x = …;                                 let x = …;
   s.spawn(move || { … &x … })                s.spawn(|| { … &x … })   ← 두 스레드가
        │                                     s.spawn(|| { … &x … })     같은 x 를 &
        ▼                                          │
   클로저가 x 를 「가진다」                      클로저가 &x 를 「가진다」
   → 클로저: Send 이려면  x: Send               → 클로저: Send 이려면  &x: Send
                                                 ⟺  x: Sync   (std marker::Sync)
```

> **마커 트레이트(marker trait)** — 메서드가 하나도 없고 **「이 타입은 이런 성질이 있다」는 표시만** 하는 트레이트. `Send`·`Sync`·`Copy` 가 그렇다.\
> 예: `fn need<T: Send>(_: T) {}` — `T` 에 대해 아무것도 부르지 않고 **경계로만** 쓴다.

> **자동 트레이트(auto trait)** — 사람이 `impl` 을 안 써도 **컴파일러가 구성 요소를 보고 계산해 붙이는** 트레이트. std 소스의 선언이 `pub unsafe auto trait Send { }` 다.\
> 예: `struct P { id: u64, name: String }` 는 아무것도 안 써도 `Send + Sync`((4)).

## 이 주제가 답하려는 질문

1. ★★★ **어떤 타입이 왜 스레드 경계를 못 넘나** — 「보내기」와 「함께 보기」가 **따로 막힌다**((1)).
2. ★★★ **E0277 을 어떻게 읽나** — 첫 줄의 타입, `help:` 의 `within`, `note:` 사슬이 **각각 무엇을 가리키나**((2)·(3)).
3. ★★ **자동 구현은 언제 되고, 어떻게 끄고 켜나** — 필드 조건 · `PhantomData` · `unsafe impl`((4)·(5)·(6)).

★ **선행** — [**49번 주제**](../49-threads-spawn-join-and-move-closures/) — `thread::spawn` 이 클로저에 `'static` 을 요구하고 `thread::scope` 가 빌림을 허용한다. 이 편의 격자는 **`'static` 문제를 지우려고 전부 `thread::scope` 안에서** 던진다 — 남는 에러가 **순수하게 `Send`/`Sync`** 이게 하려는 것이다.
[**41번 주제**](../41-rc-arc-shared-ownership-and-weak-cycles/) (3)이 `Rc` 를 스레드로 보내는 E0277 과 `Arc` 판(strong 2→1)을, [**42번 주제**](../42-refcell-cell-interior-mutability/) (7)이 `Arc<RefCell<_>>` 의 E0277 과 컴파일러가 권하는 `RwLock` 을 **이미 쟀다** — 이 편은 그 둘을 **열 타입 격자로 넓히고 에러를 읽는 법**을 붙인다.
★ **정본 경계** — 두 마커가 **데이터 레이스를 타입 오류로 바꾸는 원리**는 [`../../언어-특성/README.md`](../../언어-특성/README.md) §5 가 정본이다. 여기는 **에러를 읽고 고치는 쪽**으로 좁힌다.

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ① 경계 격자다

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ① ★★★ **경계 격자**(타입 × send/sync 로 소스를 만들어 **컴파일**) | 어느 칸이 E0277 로 막히나 · 문구가 `sent` 인가 `shared` 인가 | ★ **본체**((1)) |
| ② ★★★ **E0277 전문의 `note:` 사슬** | 어느 필드가 원인인가 | 쓴다((2)·(5)) |
| ③ ★★ **에디션 대조**(2018 × 2021) | 클로저가 무엇을 잡느냐가 **사슬의 모양**을 바꾸나 | 쓴다((3)) |
| ④ ★★ **로컬 std 문서 grep** | 구현 목록에 `!Send`·`!Sync`·조건부 `impl` 이 있나 | 쓴다((4)) |
| ⑤ 실행 출력 | 통과한 칸이 **정말 돈다** | 두 곳만((4)의 `r50_auto` · (6)) |
| 실행 시간 · 원자 연산 비용 | 「`Arc` 는 `Rc` 보다 느리다」 | ★ **부적용 — 재지 않는다.** 이 주제의 판정은 컴파일에서 끝난다 |
| 런타임 데이터 레이스 탐지(TSan · Miri) | — | ★ **잴 것이 없다** — 막힌 칸은 **실행 파일이 안 생긴다.** 레이스를 일으킬 프로그램 자체가 없다 |

★★ **제5의 상태 — 「같은 질문을 다른 창으로」.** 「`Arc<T>` 는 언제 `Send` 인가」는 원래 **std 의 `impl` 선언**이 답한다. 그 선언은 로컬 문서에서 태그가 쪼개져 grep 으로 온전히 못 읽었다(④에서 `Arc` 줄만 빠진 이유) — 그래서 같은 질문을 **컴파일러의 `note:` 창**으로 물었다: `Arc<RefCell<i32>>` 를 보내는 칸이 「`` `RefCell<i32>` cannot be shared ``」로 막힌다((1)).
★ 바꾼 창이 **못 보는 것** — `note:` 는 **막힌 이유 하나**만 말한다. `Arc<T>: Send` 의 **전체 조건**(`T: Send + Sync`)은 [41번 주제](../41-rc-arc-shared-ownership-and-weak-cycles/) (3)과 42번 (7)의 `= note: required for Arc<RefCell<i32>> to implement Send` 두 조각으로 맞춘 것이다.

### (1) ★★★ 경계 격자 — 열 타입 × 두 길

**언제 쓰나** — 「이 타입을 스레드에 넘길 수 있나」·「여러 스레드가 이것을 같이 볼 수 있나」를 판정할 때마다.

```text
===== 소스: r50_grid.sh =====
# 타입마다 두 가지 프로그램을 만들어 던진다
#   send — 값을 move 로 다른 스레드에 넘긴다
#   sync — 값은 main 에 두고 두 스레드가 & 로 함께 본다
S=$'\x1f'
types=(
  "Rc<i32>${S}Rc::new(1)"
  "Arc<i32>${S}Arc::new(1)"
  "Cell<i32>${S}Cell::new(1)"
  "RefCell<i32>${S}RefCell::new(1)"
  "Mutex<i32>${S}Mutex::new(1)"
  "RwLock<i32>${S}RwLock::new(1)"
  "Arc<RefCell<i32>>${S}Arc::new(RefCell::new(1))"
  "Arc<Mutex<i32>>${S}Arc::new(Mutex::new(1))"
  "*const i32${S}&1 as *const i32"
  "MutexGuard<'_, i32>${S}M.lock().unwrap()"
)
hdr='use std::cell::{Cell, RefCell};\nuse std::hint::black_box;\nuse std::rc::Rc;\nuse std::sync::{Arc, Mutex, RwLock};\nuse std::thread;\nstatic M: Mutex<i32> = Mutex::new(0);\nfn main() {\n    let x = %s;\n'
first_error() { grep -m1 '^error' cc.txt; }
printf 'type\tsend\tsync\n'
ok=0; m=0
for spec in "${types[@]}"; do
  ty=${spec%%"$S"*}
  make=${spec#*"$S"}
  { printf "$hdr" "$make"; printf '    thread::scope(|s| {\n        s.spawn(move || { black_box(&x); });\n    });\n}\n'; } > send.rs
  { printf "$hdr" "$make"; printf '    thread::scope(|s| {\n        s.spawn(|| { black_box(&x); });\n        s.spawn(|| { black_box(&x); });\n    });\n}\n'; } > sync.rs
  res=()
  for k in send sync; do
    if rustc --edition 2021 -A unused -o "$k" "$k.rs" 2>cc.txt; then
      res+=(pass); ok=$((ok+1))
    else
      res+=("$(first_error)")
    fi
    m=$((m+1))
  done
  row="$ty${S}${res[0]}${S}${res[1]}"
  cols=$(printf '%s' "$row" | awk -F"$S" '{print NF}')
  [ "$cols" = 3 ] || { echo "column count $cols != 3"; exit 1; }
  printf '%s\n' "$row" | tr "$S" '\t'
done
echo "compiling cells: $ok / $m"
===== bash r50_grid.sh =====
type	send	sync
Rc<i32>	error[E0277]: `Rc<i32>` cannot be sent between threads safely	error[E0277]: `Rc<i32>` cannot be shared between threads safely
Arc<i32>	pass	pass
Cell<i32>	pass	error[E0277]: `Cell<i32>` cannot be shared between threads safely
RefCell<i32>	pass	error[E0277]: `RefCell<i32>` cannot be shared between threads safely
Mutex<i32>	pass	pass
RwLock<i32>	pass	pass
Arc<RefCell<i32>>	error[E0277]: `RefCell<i32>` cannot be shared between threads safely	error[E0277]: `RefCell<i32>` cannot be shared between threads safely
Arc<Mutex<i32>>	pass	pass
*const i32	error[E0277]: `*const i32` cannot be sent between threads safely	error[E0277]: `*const i32` cannot be shared between threads safely
MutexGuard<'_, i32>	error[E0277]: `std::sync::MutexGuard<'_, i32>` cannot be sent between threads safely	pass
compiling cells: 11 / 20
(exit 0)
```

- ★★★ **「compiling cells: 11 / 20」.** 막힌 아홉 칸이 전부 **E0277** 이고, 문구가 둘로 갈린다 — **`send` 열은 `cannot be sent`**, **`sync` 열은 `cannot be shared`**. 문구가 곧 **어느 트레이트가 빠졌나**다.
- ★★★ **`Cell`·`RefCell` 은 보낼 수는 있고 함께 볼 수는 없다** — 값을 통째로 넘기면 원래 스레드에는 **아무것도 안 남으니** 괜찮고, 두 스레드가 `&` 로 같이 보면 **둘 다 `&self` 로 고칠 수 있으니** 안 된다(42번의 내부 가변성).
- ★★★ **`Rc` 는 둘 다 막힌다** — 복제본끼리 카운트를 **원자적이지 않게** 나눠 쓰므로, 한 복제본을 넘겨도(보내기) 같이 봐도(`&Rc` 로 `clone` 가능) 카운트가 깨질 수 있다. 언어-특성 §5 가 원리를 말한다.
- ★★★ **`Arc<RefCell<i32>>` 의 `send` 칸이 `cannot be shared` 다** — `Arc` 를 넘기는데 `Send` 가 아니라 **`RefCell` 의 `Sync`** 가 빠졌다고 한다. `Arc` 는 **넘긴 뒤에도 원래 스레드에 복제본이 남아** 두 스레드가 같은 `RefCell` 을 보게 되므로, `Arc<T>: Send` 가 `T: Sync` 를 요구한다(42번 (7)의 `required for Arc<RefCell<i32>> to implement Send`).
- ★★ **`Mutex`·`RwLock` 은 둘 다 통과** — 안쪽을 고치려면 락을 거쳐야 하기 때문이다. **`Arc<Mutex<i32>>` 도 둘 다** — 52번 주제의 기본 모양이다.
- ★★ **`*const i32` 는 둘 다 막힌다** — std 가 원시 포인터에 `!Send`·`!Sync` 를 **명시해** 두었다((4)의 `impl<T> !Send for *const T`). 포인터가 가리키는 곳을 컴파일러가 모르기 때문에 **보수적으로 끈 것**이다.
- ★★★ **`MutexGuard` 는 거꾸로다 — 보내기는 막히고 함께 보기는 된다.** (7)에서 따로 본다.

```text
   (1) 격자를 두 열로 접으면 — 네 가지 모양

                     sync 통과              sync 막힘
                ┌──────────────────────┬──────────────────────────┐
   send 통과    │ Arc · Mutex · RwLock │ Cell · RefCell           │
                │ Arc<Mutex>           │  (넘기기만 된다)          │
                ├──────────────────────┼──────────────────────────┤
   send 막힘    │ MutexGuard           │ Rc · *const · Arc<RefCell>│
                │  (같이 보기만 된다)   │  (둘 다 안 된다)          │
                └──────────────────────┴──────────────────────────┘
```

★ 격자 스크립트는 **`thread::scope` 안의 `s.spawn`** 으로 던진다 — `thread::spawn` 이면 `'static` 요구가 먼저 걸려 `MutexGuard` 같은 빌린 값은 **`Send` 가 아닌 이유로** 막힐 수 있다. 49번의 그 제약을 지운 판이다.

### (2) ★★★ E0277 의 사슬 읽기 — 어느 필드가 원인인가

**언제 쓰나** — 큰 구조체를 스레드에 넘기다 막혔는데 첫 줄의 타입이 **내 구조체가 아닐** 때.

```text
===== 소스: r50_chain.rs =====
use std::rc::Rc;
use std::thread;

struct Cache {
    hits: u32,
    last: Rc<String>,
}

struct Session {
    user: String,
    cache: Cache,
}

fn total(s: Session) -> usize {
    s.user.len() + s.cache.hits as usize + s.cache.last.len()
}

fn main() {
    let s = Session {
        user: String::from("kim"),
        cache: Cache { hits: 0, last: Rc::new(String::new()) },
    };
    let h = thread::spawn(move || total(s));
    println!("{}", h.join().unwrap());
}
===== rustc --edition 2021 r50_chain.rs =====
error[E0277]: `Rc<String>` cannot be sent between threads safely
  --> r50_chain.rs:23:27
   |
23 |     let h = thread::spawn(move || total(s));
   |             ------------- -------^^^^^^^^^
   |             |             |
   |             |             `Rc<String>` cannot be sent between threads safely
   |             |             within this `{closure@r50_chain.rs:23:27: 23:34}`
   |             required by a bound introduced by this call
   |
   = help: within `{closure@r50_chain.rs:23:27: 23:34}`, the trait `Send` is not implemented for `Rc<String>`
note: required because it appears within the type `Cache`
  --> r50_chain.rs:4:8
   |
 4 | struct Cache {
   |        ^^^^^
note: required because it appears within the type `Session`
  --> r50_chain.rs:9:8
   |
 9 | struct Session {
   |        ^^^^^^^
note: required because it's used within this closure
  --> r50_chain.rs:23:27
   |
23 |     let h = thread::spawn(move || total(s));
   |                           ^^^^^^^
note: required by a bound in `spawn`
  --> /rustc/ded5c06cf21d2b93bffd5d884aa6e96934ee4234/library/std/src/thread/mod.rs:725:1

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0277`.
(exit 1)
```

- ★★★ **첫 줄은 구조체가 아니라 원인 타입을 댄다** — `` `Rc<String>` cannot be sent between threads safely ``. 넘긴 것은 `Session` 인데 **가장 안쪽의 범인**이 먼저 나온다.
- ★★★ **`note:` 사슬은 안에서 밖으로 올라간다** — ``required because it appears within the type `Cache` `` → `` … `Session` `` → `required because it's used within this closure` → ``required by a bound in `spawn` ``. **범인 → 그것을 품은 필드의 타입 → 그 바깥 → 클로저 → 요구한 함수** 순서다.
- ★★ ``= help: within {closure…}, the trait `Send` is not implemented for `Rc<String>` `` — **「무엇 안에서(within)」와 「무엇이(for)」** 를 한 줄에 준다. `within` 은 가장 바깥(클로저), `for` 는 가장 안쪽(범인)이다.
- ★ **고치는 자리는 사슬의 첫 `note:` 가 가리키는 타입의 필드**다 — 여기서는 `Cache::last`. `Rc` → `Arc` 로 바꾸면 사슬 전체가 사라진다(41번 (3)).

```text
   (2)의 사슬 — 읽는 순서

   error[E0277]: `Rc<String>` cannot be sent …         ← 범인(가장 안쪽 타입)
   = help: within {closure…}, … not implemented for Rc<String>
   note: … appears within the type `Cache`              ← 범인을 품은 구조체 (여기를 고친다)
   note: … appears within the type `Session`            ← 그 바깥
   note: … used within this closure                     ← 클로저가 Session 을 잡았다
   note: required by a bound in `spawn`                 ← 경계를 건 함수
```

### (3) ★★★ 같은 범인, 사라진 사슬 — 클로저가 무엇을 잡느냐

**언제 쓰나** — 사슬을 따라가려는데 **`appears within the type` 줄이 하나도 없을** 때.

같은 두 구조체를, 이번에는 클로저 안에서 **필드를 하나씩** 쓴다.

```text
===== 소스: r50_chain_fields.rs =====
use std::rc::Rc;
use std::thread;

struct Cache {
    hits: u32,
    last: Rc<String>,
}

struct Session {
    user: String,
    cache: Cache,
}

fn main() {
    let s = Session {
        user: String::from("kim"),
        cache: Cache { hits: 0, last: Rc::new(String::new()) },
    };
    let h = thread::spawn(move || s.user.len() + s.cache.hits as usize + s.cache.last.len());
    println!("{}", h.join().unwrap());
}
===== rustc --edition 2021 r50_chain_fields.rs =====
error[E0277]: `Rc<String>` cannot be sent between threads safely
  --> r50_chain_fields.rs:19:27
   |
19 |     let h = thread::spawn(move || s.user.len() + s.cache.hits as usize + s.cache.last.len());
   |             ------------- -------^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   |             |             |
   |             |             `Rc<String>` cannot be sent between threads safely
   |             |             within this `{closure@r50_chain_fields.rs:19:27: 19:34}`
   |             required by a bound introduced by this call
   |
   = help: within `{closure@r50_chain_fields.rs:19:27: 19:34}`, the trait `Send` is not implemented for `Rc<String>`
note: required because it's used within this closure
  --> r50_chain_fields.rs:19:27
   |
19 |     let h = thread::spawn(move || s.user.len() + s.cache.hits as usize + s.cache.last.len());
   |                           ^^^^^^^
note: required by a bound in `spawn`
  --> /rustc/ded5c06cf21d2b93bffd5d884aa6e96934ee4234/library/std/src/thread/mod.rs:725:1

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0277`.
(exit 1)
```

- ★★★ **첫 줄은 같은데(`Rc<String>` cannot be sent) `appears within the type` 줄이 없다.** `Cache`·`Session` 이 에러에서 **사라졌다.**
- ★★★ **이유는 2021 의 정밀 포착이다** — 클로저가 `s` 통째가 아니라 **쓴 자리 `s.user`·`s.cache.hits`·`s.cache.last` 만** 잡는다(Reference — Capture precision · [34번 주제](../34-closures-fn-fnmut-fnonce-and-move/) (6)). 그러니 클로저가 가진 것은 `Rc<String>` 그 자체이고, **품은 구조체가 없으니 사슬도 없다.**

**에디션을 바꿔 사슬 줄을 세면.**

```text
===== 소스: r50_chain_fields_ed.sh =====
# 필드를 하나씩 쓰는 클로저 — 에디션마다 「appears within the type」 줄이 몇 개 나오나
for e in 2018 2021; do
  rustc --edition "$e" -o cf r50_chain_fields.rs 2>cc.txt
  rc=$?
  echo "edition $e: rustc exit $rc, first line: $(grep -m1 '^error' cc.txt)"
  echo "edition $e: 'appears within the type' lines: $(grep -c 'appears within the type' cc.txt)"
done
===== bash r50_chain_fields_ed.sh =====
edition 2018: rustc exit 1, first line: error[E0277]: `Rc<String>` cannot be sent between threads safely
edition 2018: 'appears within the type' lines: 2
edition 2021: rustc exit 1, first line: error[E0277]: `Rc<String>` cannot be sent between threads safely
edition 2021: 'appears within the type' lines: 0
(exit 0)
```

- ★★★ **2018 은 2줄, 2021 은 0줄.** 소스는 한 글자도 같고 **첫 줄도 같다** — 2018 은 클로저가 `s` 를 통째로 잡아 (2)와 같은 사슬이 나온다.
- ★★ **읽는 법의 결론** — 사슬이 없으면 **클로저가 그 필드를 직접 잡은 것**이다. 원인 필드는 `= help:` 의 `for` 타입과 **클로저 몸통에서 그 타입을 쓰는 식**(`s.cache.last.len()`)을 맞춰 찾는다.
- ★ 2021 이 **통과시켜 주지는 않는다** — 범인 필드를 쓰는 한 여전히 E0277 이다. 다만 **범인이 아닌 필드만 쓰면** 2021 에서는 통과한다(`Rc` 필드를 안 건드리면 안 잡으므로). **이 조합은 던지지 않았다** — 추론이다.

### (4) ★★ 자동 구현 — 필드가 전부 그러면 구조체도

**언제 쓰나** — 내가 만든 구조체가 스레드를 넘을 수 있는지 **`impl` 없이** 판정할 때.

```text
===== 소스: r50_auto.rs =====
use std::collections::HashMap;
use std::sync::{Arc, Mutex};

fn assert_send<T: Send>() {}
fn assert_sync<T: Sync>() {}

struct Plain {
    id: u64,
    name: String,
    tags: Vec<String>,
    index: HashMap<String, usize>,
    shared: Arc<Mutex<Vec<u8>>>,
}

fn main() {
    assert_send::<Plain>();
    assert_sync::<Plain>();
    let p = Plain { id: 1, name: "a".into(), tags: vec![], index: HashMap::new(), shared: Arc::default() };
    let h = std::thread::spawn(move || p.id + p.name.len() as u64 + p.tags.len() as u64 + p.index.len() as u64 + p.shared.lock().unwrap().len() as u64);
    println!("Plain: thread returned {}", h.join().unwrap());
}
===== rustc --edition 2021 r50_auto.rs =====
(exit 0)
===== ./r50_auto =====
Plain: thread returned 2
(exit 0)
```

- ★★ **`impl Send`·`impl Sync` 를 한 줄도 안 썼는데** `assert_send::<Plain>()`·`assert_sync::<Plain>()` 가 통과하고 실제로 스레드에 넘어갔다. `u64`·`String`·`Vec<String>`·`HashMap`·`Arc<Mutex<_>>` 가 **전부 `Send + Sync`** 이기 때문이다.
- ★★★ **판정은 필드의 합성이다** — std: 「This trait is automatically implemented when the compiler determines it's appropriate」. Rustonomicon: 구성 요소가 전부 `Send` 면 `Send`. **필드 하나가 빠지면 구조체 전체가 빠진다**((2)).
- ★ **`assert_send::<T>()` 꼴** — 값 없이 **타입만으로** 컴파일러에게 묻는 관용구다. 실행 비용이 없다(빈 함수).

**std 는 무엇을 명시해 두었나 — 로컬 문서의 구현 목록.**

```text
===== 소스: r50_impls.sh =====
# 로컬 rust-docs(1.92.0) 의 구현 목록을 태그를 벗겨 읽는다 — 각 줄이 문서에 있나
D="$(rustc --print sysroot)/share/doc/rust/html/std"
strip() { sed -e 's/<[^>]*>//g' -e 's/&lt;/</g; s/&gt;/>/g; s/&amp;/\&/g; s/&#39;/'"'"'/g' "$1"; }
look() {
  if strip "$D/$1" | grep -q -F -- "$2"; then echo "found     $2"; else echo "not found $2"; fi
}
look marker/trait.Send.html 'impl<T> Send for &T'
look marker/trait.Send.html 'impl<T, A> !Send for Rc<T, A>'
look marker/trait.Send.html 'impl<T> !Send for *const T'
look marker/trait.Sync.html 'impl<T> !Sync for Cell<T>'
look marker/trait.Sync.html 'impl<T> !Sync for RefCell<T>'
look sync/struct.MutexGuard.html "impl<T: ?Sized> !Send for MutexGuard<'_, T>"
look sync/struct.MutexGuard.html "impl<T: ?Sized + Sync> Sync for MutexGuard<'_, T>"
look sync/struct.Mutex.html 'impl<T: ?Sized + Send> Sync for Mutex<T>'
===== bash r50_impls.sh =====
found     impl<T> Send for &T
found     impl<T, A> !Send for Rc<T, A>
found     impl<T> !Send for *const T
found     impl<T> !Sync for Cell<T>
found     impl<T> !Sync for RefCell<T>
found     impl<T: ?Sized> !Send for MutexGuard<'_, T>
found     impl<T: ?Sized + Sync> Sync for MutexGuard<'_, T>
found     impl<T: ?Sized + Send> Sync for Mutex<T>
(exit 0)
```

- ★★ **`impl<T> Send for &T` (조건 `T: Sync`)** — (1)의 `sync` 열이 이 한 줄이다. `&x` 를 가진 클로저가 `Send` 이려면 `x: Sync`.
- ★★ **`!Send for Rc` · `!Send for *const T` · `!Sync for Cell` · `!Sync for RefCell`** — 자동 계산에 맡기지 않고 **std 가 부정 구현으로 못 박은** 자리다. (1)의 막힌 칸들이 여기서 온다.
- ★★ **`MutexGuard` 는 `!Send` 이고, `T: Sync` 이면 `Sync`** · **`Mutex<T>` 는 `T: Send` 이면 `Sync`** — `Mutex` 는 안쪽이 `Sync` 가 아니어도(예: `Mutex<Cell<_>>`) 함께 볼 수 있다. 한 번에 한 스레드만 안을 만지기 때문이다.

### (5) ★ 일부러 끄기 — `PhantomData<*const ()>`

**언제 쓰나** — FFI 핸들처럼 **필드는 전부 평범한데 스레드를 넘기면 안 되는 타입**을 만들 때.

```text
===== 소스: r50_phantom.rs =====
use std::marker::PhantomData;

fn assert_send<T: Send>() {}
fn assert_sync<T: Sync>() {}

struct Handle {
    id: u64,
    _marker: PhantomData<*const ()>,
}

fn main() {
    assert_send::<Handle>();
    assert_sync::<Handle>();
}
===== rustc --edition 2021 r50_phantom.rs =====
error[E0277]: `*const ()` cannot be sent between threads safely
  --> r50_phantom.rs:12:19
   |
12 |     assert_send::<Handle>();
   |                   ^^^^^^ `*const ()` cannot be sent between threads safely
   |
   = help: within `Handle`, the trait `Send` is not implemented for `*const ()`
note: required because it appears within the type `PhantomData<*const ()>`
  --> /rustc/ded5c06cf21d2b93bffd5d884aa6e96934ee4234/library/core/src/marker.rs:822:12
note: required because it appears within the type `Handle`
  --> r50_phantom.rs:6:8
   |
 6 | struct Handle {
   |        ^^^^^^
note: required by a bound in `assert_send`
  --> r50_phantom.rs:3:19
   |
 3 | fn assert_send<T: Send>() {}
   |                   ^^^^ required by this bound in `assert_send`

error[E0277]: `*const ()` cannot be shared between threads safely
  --> r50_phantom.rs:13:19
   |
13 |     assert_sync::<Handle>();
   |                   ^^^^^^ `*const ()` cannot be shared between threads safely
   |
   = help: within `Handle`, the trait `Sync` is not implemented for `*const ()`
note: required because it appears within the type `PhantomData<*const ()>`
  --> /rustc/ded5c06cf21d2b93bffd5d884aa6e96934ee4234/library/core/src/marker.rs:822:12
note: required because it appears within the type `Handle`
  --> r50_phantom.rs:6:8
   |
 6 | struct Handle {
   |        ^^^^^^
note: required by a bound in `assert_sync`
  --> r50_phantom.rs:4:19
   |
 4 | fn assert_sync<T: Sync>() {}
   |                   ^^^^ required by this bound in `assert_sync`

error: aborting due to 2 previous errors

For more information about this error, try `rustc --explain E0277`.
(exit 1)
```

- ★★ **E0277 두 개** — `send` 와 `sync` 가 **각각** 막힌다. 첫 줄의 범인은 **`*const ()`** — 크기 0 인 `PhantomData` 안에 든 원시 포인터 타입이다.
- ★★★ **사슬이 (2)와 같은 모양이다** — ``appears within the type `PhantomData<*const ()>` `` → ``appears within the type `Handle` ``. 첫 `note:` 가 std 소스(`core/src/marker.rs`)를 가리키는 것만 다르다.
- ★ `PhantomData<T>` 는 **값이 없는 필드**다 — 메모리를 안 쓰고 **타입 성질만** 빌려 온다. `*const ()` 의 `!Send + !Sync` 를 빌려 와 `Handle` 전체를 끈다.

**`impl !Send` 로 직접 쓰면.**

```text
===== 소스: r50_negative.rs =====
struct Handle {
    id: u64,
}

impl !Send for Handle {}

fn main() {
    let h = Handle { id: 1 };
    println!("{}", h.id);
}
===== rustc --edition 2021 r50_negative.rs =====
error[E0658]: negative trait bounds are not fully implemented; use marker types for now
 --> r50_negative.rs:5:6
  |
5 | impl !Send for Handle {}
  |      ^^^^^
  |
  = note: see issue #68318 <https://github.com/rust-lang/rust/issues/68318> for more information

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0658`.
(exit 1)
```

- ★★ **E0658 — 「negative trait bounds are not fully implemented; use marker types for now」.** 안정판에서는 **부정 구현을 사용자가 쓸 수 없다**(std 는 쓴다 — (4)의 목록). 컴파일러가 **「marker types 를 써라」** 고 권하는 것이 바로 `PhantomData` 다.

### (6) ★ 억지로 켜기 — `unsafe impl Send`

```text
===== 소스: r50_unsafe_impl.rs =====
use std::thread;

struct Wrapper(*const u8);

unsafe impl Send for Wrapper {}

fn main() {
    static BYTE: u8 = 7;
    let w = Wrapper(&BYTE);
    let h = thread::spawn(move || {
        let w = w;
        w.0 as usize != 0
    });
    println!("thread returned {}", h.join().unwrap());
}
===== rustc --edition 2021 r50_unsafe_impl.rs =====
(exit 0)
===== ./r50_unsafe_impl =====
thread returned true
(exit 0)
```

- ★★ **컴파일되고 돈다**(`thread returned true`). `*const u8` 필드 때문에 자동으로는 `!Send` 인 `Wrapper` 에 사람이 `Send` 를 붙였다.
- ★★★ **`unsafe` 는 컴파일러가 검사를 포기한다는 표시가 아니라 「이 약속은 내가 진다」는 서명이다** — `Send` 가 `unsafe trait` 이라 구현에 `unsafe impl` 이 필요하다. 컴파일러는 그 약속을 **믿고** 경계를 연다.
- ★ 이 예의 포인터는 `static` 을 가리키므로 괜찮지만, **그 판단은 컴파일러가 하지 않았다.** `unsafe` 가 푸는 것과 안전 경계 설계는 목록의 **56번 주제**가 정본이다.

### (7) ★★ `MutexGuard` 는 보낼 수 없다

**언제 쓰나** — 락을 잡은 채 그 가드를 다른 스레드(또는 `await` 너머)로 넘기려 할 때.

```text
===== 소스: r50_guard.rs =====
use std::sync::Mutex;
use std::thread;

static M: Mutex<Vec<i32>> = Mutex::new(Vec::new());

fn main() {
    let g = M.lock().unwrap();
    let h = thread::spawn(move || g.len());
    println!("{}", h.join().unwrap());
}
===== rustc --edition 2021 r50_guard.rs =====
error[E0277]: `std::sync::MutexGuard<'_, Vec<i32>>` cannot be sent between threads safely
 --> r50_guard.rs:8:27
  |
8 |     let h = thread::spawn(move || g.len());
  |             ------------- -------^^^^^^^^
  |             |             |
  |             |             `std::sync::MutexGuard<'_, Vec<i32>>` cannot be sent between threads safely
  |             |             within this `{closure@r50_guard.rs:8:27: 8:34}`
  |             required by a bound introduced by this call
  |
  = help: within `{closure@r50_guard.rs:8:27: 8:34}`, the trait `Send` is not implemented for `std::sync::MutexGuard<'_, Vec<i32>>`
note: required because it's used within this closure
 --> r50_guard.rs:8:27
  |
8 |     let h = thread::spawn(move || g.len());
  |                           ^^^^^^^
note: required by a bound in `spawn`
 --> /rustc/ded5c06cf21d2b93bffd5d884aa6e96934ee4234/library/std/src/thread/mod.rs:725:1

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0277`.
(exit 1)
```

- ★★ **E0277 — `` `std::sync::MutexGuard<'_, Vec<i32>>` cannot be sent between threads safely ``.** `static` 뮤텍스라 `'static` 문제는 없다 — **순수하게 `Send` 가 빠진 것**이다.
- ★★★ **왜 `!Send` 인가** — 이 판의 로컬 std 문서에서 **이유를 찾지 못했고, 실행으로도 확인하지 않았다.** 확인한 것은 (4)의 **`impl<T: ?Sized> !Send for MutexGuard<'_, T>`** 한 줄이다 — 「막힌다」는 사실까지만 적는다.
- ★★ **그런데 `Sync` 는 된다**((1) 마지막 행) — 여러 스레드가 `&MutexGuard` 로 **안을 읽기만** 하는 것은 `T: Sync` 면 안전하다.
- ★ 가드가 **`await` 를 가로지르면** 같은 `!Send` 가 async 의 `Send` 경계에 걸린다 — 목록의 **55번 주제**.

## 문법 — 형태와 규칙

```text
   fn assert_send<T: Send>() {}           // 타입만으로 묻기 — (4)
   fn assert_sync<T: Sync>() {}

   thread::spawn(f)                       // F: FnOnce + Send + 'static   — 클로저가 잡은 것이 전부 Send
   s.spawn(f)  (thread::scope 안)          // F: Send  ('static 은 안 요구)

   struct Handle { id: u64, _p: PhantomData<*const ()> }   // 끄기 — (5)
   unsafe impl Send for Wrapper {}                         // 켜기 — 책임은 사람 (6)
   // impl !Send for X {}                                  // 안정판 불가 — E0658 (5)
```

- ★★★ **`Send` = 넘겨도 된다 · `Sync` = `&` 로 함께 봐도 된다 · `T: Sync` ⟺ `&T: Send`**((1)·(4)).
- ★★★ **둘 다 자동 트레이트다 — 필드가 전부 그러면 구조체도 그렇다**((4)).
- ★★ **E0277 의 첫 줄은 가장 안쪽 범인, `note:` 사슬은 그 바깥으로**((2)). **정밀 포착이면 사슬이 없을 수 있다**((3)).
- ★ **끄기는 `PhantomData`, 켜기는 `unsafe impl`** — 부정 구현은 안정판에 없다((5)·(6)).

## 어디서 틀리나

### 1. ★★★ 「에러 첫 줄의 타입을 고치면 된다」

(2) — 첫 줄의 `Rc<String>` 은 **내 코드의 어느 필드**인지 말하지 않는다. **첫 `appears within the type` 이 가리키는 구조체의 필드**가 고칠 자리다. 사슬이 없으면((3)) 클로저 몸통에서 그 타입을 쓰는 식을 찾는다.

### 2. ★★★ 「`Arc` 로 감싸면 스레드를 넘는다」

(1)의 `Arc<RefCell<i32>>` — **보내기부터 막힌다.** `Arc<T>: Send` 는 `T: Sync` 를 요구한다. 안쪽을 `Mutex`/`RwLock` 으로 바꿔야 한다(42번 (7)). 41번 「어디서 틀리나」 5번과 같은 자리다.

### 3. ★★ 「`Cell`·`RefCell` 은 스레드에 못 쓴다」

(1) — **넘기기(`Send`)는 된다.** 막히는 것은 여럿이 **함께 보기(`Sync`)** 다. 한 스레드에 통째로 넘겨 그쪽에서만 쓰는 설계는 통과한다.

### 4. ★★ 「`Send` 가 아니면 `Sync` 도 아니다」

(1)의 `MutexGuard` — **`!Send` 인데 `Sync`** 다. 두 성질은 **따로 계산된다**(격자의 네 모양).

### 5. ★★ 「2018 과 2021 의 E0277 은 모양이 같다」

(3) — 같은 소스에서 **`appears within the type` 줄이 2 → 0** 으로 바뀌었다. 에디션이 **통과 여부**는 안 바꿨지만 **에러가 가리키는 자리**는 바꿨다.

### 6. ★ 「`impl !Send for X {}` 로 끄면 된다」

(5) — **E0658**(안정판 불가). `PhantomData<*const ()>` 필드를 쓴다.

### 7. ★ 「`unsafe impl Send` 를 붙이면 안전해진다」

(6) — **컴파일러가 믿을 뿐 확인하지 않는다.** 붙인 사람이 그 타입의 모든 사용이 안전함을 증명해야 한다(56번 주제).

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| `Send`·`Sync` 가 **자동 트레이트**다(필드 합성) | ★ **언어**(컴파일러의 자동 트레이트 규칙) · std 선언 `pub unsafe auto trait` | (4) `r50_auto` |
| `T: Sync` ⟺ `&T: Send` | ★ **std 의 정의 + `impl<T> Send for &T`** | (4) `r50_impls` |
| `Rc`·`*const T` 가 `!Send`, `Cell`·`RefCell` 이 `!Sync` | ★ **std 의 부정 구현** | (1) · (4) |
| `MutexGuard` 가 `!Send`, `T: Sync` 면 `Sync` | ★ **std 의 구현** — **이유는 이 문서가 확인하지 못했다** | (7) · (4) |
| 막힌 칸이 **E0277** 이다 | ★ **rustc** — 트레이트 경계 불만족 | (1) |
| 진단 **문구**(`cannot be sent`/`shared` · `appears within the type`) | ★ **rustc 구현** — 판이 바뀌면 바뀔 수 있다 | (1)·(2) |
| 정밀 포착이면 **사슬 줄이 사라진다** | ★ **언어(2021 캡처 규칙)의 결과 + rustc 진단 모양** — 사슬을 몇 줄 찍나는 구현 | (3) |
| 사용자 코드의 `impl !Trait` 불가 | ★ **언어 기능 미안정**(E0658 · issue #68318) | (5) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 근거 |
|---|---|---|
| 여러 스레드가 **공유 소유**한다 | **`Arc`**(`Rc` 는 막힌다) | (1) · 41번 |
| 여러 스레드가 **함께 고친다** | **`Arc<Mutex<T>>`** · `Arc<RwLock<T>>` | (1) · 52번 주제 |
| 값을 **한 스레드에 통째로** 넘긴다 | `Cell`/`RefCell` 이 들어 있어도 **된다** — `move` 로 넘긴다 | (1) `send` 열 |
| 내 타입이 넘을 수 있나 확인 | **`assert_send::<T>()`** 한 줄 | (4) |
| 넘으면 안 되는 핸들 | **`PhantomData<*const ()>`** | (5) |
| 원시 포인터를 품었지만 안전함을 **증명할 수 있다** | `unsafe impl Send` — **증명을 주석으로 남긴다** | (6) · 56번 주제 |
| 락 가드를 다른 스레드로 넘기고 싶다 | ★ **설계를 바꾼다** — 데이터를 꺼내 넘기거나 채널로 보낸다(51번 주제) | (7) |

## 핵심 문장

- ★★★ **`Send` 는 넘기기, `Sync` 는 `&` 로 함께 보기 — 둘은 따로 막히고, `T: Sync` 는 `&T: Send` 와 같은 말이다.**
- ★★★ **두 마커는 자동 트레이트라 필드 하나가 빠지면 구조체 전체가 빠진다 — E0277 은 가장 안쪽 범인을 먼저 대고, `note:` 사슬이 그것을 품은 타입들을 바깥으로 올라간다.**
- ★★ **2021 정밀 포착은 클로저가 필드만 잡게 해 사슬을 지울 수 있다 — 사슬이 없으면 클로저 몸통에서 범인 타입을 쓰는 식을 찾는다.**
- ★★ **`Arc` 는 안쪽이 `Sync` 여야 넘어간다 — `Arc<RefCell>` 은 보내기부터 막힌다.**
- ★ **끄는 것은 `PhantomData<*const ()>`, 켜는 것은 `unsafe impl` — 뒤엣것은 컴파일러가 믿을 뿐이다.**

## 관련 자료

- [`../../언어-특성/README.md`](../../언어-특성/README.md) §5 — **두 마커가 데이터 레이스를 타입 오류로 바꾸는 원리는 거기, 여기는 E0277 을 읽고 고치는 쪽.**
- [**49번 주제**](../49-threads-spawn-join-and-move-closures/) — `thread::spawn` 의 `'static` 과 `thread::scope`. 이 편 격자가 `scope` 로 던지는 이유.
- [**41번 주제**](../41-rc-arc-shared-ownership-and-weak-cycles/) — `Rc` 의 E0277 과 `Arc`(strong 2→1).
- [**42번 주제**](../42-refcell-cell-interior-mutability/) — `Arc<RefCell>` 의 E0277 과 `RwLock` 권고.
- [**34번 주제**](../34-closures-fn-fnmut-fnonce-and-move/) — 2021 정밀 포착((3)의 사슬이 사라지는 이유).
- [**51번 주제**](../51-mpsc-channels-and-sender-drop/) · [**52번 주제**](../52-mutex-rwlock-arc-and-poisoning/) — `Send` 인 값을 채널로 넘기기 · `Mutex` 로 `Sync` 를 얻기.
- 목록의 **55번 주제**(async 의 `Send` 경계) · **56번 주제**(`unsafe`).

## 용어 풀이

- **`Send`** — 그 타입의 값을 다른 스레드로 **옮겨도** 안전하다는 자동 트레이트.
- **`Sync`** — 그 타입을 여러 스레드가 **`&` 로 함께 봐도** 안전하다는 자동 트레이트. `&T: Send` 와 같다.
- **자동 트레이트(auto trait)** — 컴파일러가 필드를 보고 계산해 붙이는 트레이트.
- **부정 구현(negative impl)** — `impl !Send for X` — 「이 타입은 아니다」를 못 박는 구현. 안정판에서는 std 만 쓴다.
- **`PhantomData<T>`** — 크기 0 인 필드. 값 없이 `T` 의 타입 성질(여기서는 `!Send`)만 빌려 온다.
- **E0277** — 「트레이트 경계를 만족하지 않는다」. `Send`/`Sync` 위반이 전부 이 번호로 나온다.
- **`note:` 사슬** — E0277 뒤에 붙는 「required because …」 줄들. 요구가 어디서 어디로 번졌는지를 안에서 밖으로 적는다.
- **정밀 포착(precise capture)** — 2021 에디션부터 클로저가 변수 통째가 아니라 **쓴 경로(필드)** 만 잡는 규칙.

## 더 들어가면

- `Sync` 이지만 `Send` 가 아닌 타입이 `MutexGuard` 말고도 std 에 있다(구현 목록). **이 문서는 목록을 전수로 훑지 않았다.**
- `Arc<T>: Send` 의 정확한 선언(`T: Sync + Send`)은 로컬 문서에서 태그가 쪼개져 grep 으로 못 읽었다 — 41번과 42번의 진단 두 조각으로 맞췄다((0)의 제5의 상태).
- async 에서는 `Future` 가 `Send` 인지가 같은 사슬 모양의 에러로 나온다(`await` 를 가로지르는 `!Send` 값) — 목록의 **55번 주제**.
