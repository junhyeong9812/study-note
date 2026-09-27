# rust/syntax/50 — `Send`/`Sync` 가 코드에 나타나는 방식 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서
> **`rustc --edition 2021`** 로(에디션 대조 한 곳은 2018·2021) 실제로 돌려 받은 것이다.\
> ★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
> ★★ 블록 첫 줄 `===== 소스: <파일> =====` 아래가 **돌린 소스 전문**이고, **진단의 줄 번호는 그 파일 기준**이다.\
> ★ 이 편에는 **흔들리는 칸이 없다** — 판정이 전부 컴파일 시점이다(서머리 머리말의 표).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ `11 / 20` — `send` 열은 `cannot be sent`, `sync` 열은 `cannot be shared`

**출력**

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

**왜 그런가**

- ★★★ **문구가 곧 빠진 트레이트다** — `send` 열(값을 `move` 로 넘김)은 **`Send`** 가, `sync` 열(두 스레드가 `&x`)은 **`Sync`** 가 필요하다. `&x` 를 가진 클로저가 `Send` 이려면 `x: Sync` 이기 때문이다(std `impl<T> Send for &T` 의 조건 `T: Sync`).
- ★★ **둘 다 통과** — `Arc` · `Mutex` · `RwLock` · `Arc<Mutex>`. **둘 다 막힘** — `Rc` · `*const` · `Arc<RefCell>`.
- ★★★ **엇갈림** — `Cell`·`RefCell` 은 **보내기만**, `MutexGuard` 는 **함께 보기만** 된다(8번).
- ★ `Arc<RefCell>` 의 `send` 칸이 `shared` 문구인 이유는 7번.

### 2. ★★★ E0277 — 첫 줄은 `Rc<String>`, 사슬은 `Cache` → `Session` → 클로저 → `spawn`

**출력**

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

**왜 그런가**

- ★★★ **첫 줄은 넘긴 `Session` 이 아니라 가장 안쪽의 범인 `Rc<String>`** 을 댄다.
- ★★★ **`note:` 는 안에서 밖으로** — `appears within the type` **`Cache`**(4행) → **`Session`**(9행) → `used within this closure`(23행) → `required by a bound in spawn`(std 소스).
- ★★ **고칠 자리는 첫 `appears within` 이 가리키는 `Cache` 의 필드 `last`** — `Rc` → `Arc` 로 바꾸면 사슬째 사라진다([41번 주제](../41-rc-arc-shared-ownership-and-weak-cycles/) (3)).

### 3. ★★★ 첫 줄은 같고 사슬은 0줄 — 2018 은 2줄

**출력**

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

**왜 그런가**

- ★★★ **첫 줄은 2번과 한 글자도 같다**(`Rc<String>` cannot be sent) — 그런데 **`appears within the type` 줄이 없다.**
- ★★★ **2021 정밀 포착** — 클로저가 `s` 통째가 아니라 쓴 경로 `s.user`·`s.cache.hits`·`s.cache.last` 만 잡는다. 클로저가 가진 것이 `Rc<String>` 그 자체이니 **품은 구조체가 사슬에 안 나온다**([34번 주제](../34-closures-fn-fnmut-fnonce-and-move/) (6)).
- ★★ **2018 은 2줄** — 변수 통째 포착이라 2번과 같은 사슬(`Cache` → `Session`)이 나온다. **통과 여부는 두 에디션이 같고(둘 다 `exit 1`) 에러의 모양만 다르다.**
- ★ 사슬이 없으면 `= help:` 의 `for` 타입(`Rc<String>`)을 **클로저 몸통에서 쓰는 식**(`s.cache.last.len()`)과 맞춰 원인 필드를 찾는다.

### 4. ★★ E0277 두 개 — 범인 `*const ()`, 사슬 `PhantomData<*const ()>` → `Handle`

**출력**

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

**왜 그런가**

- ★★ **`assert_send` 와 `assert_sync` 가 각각 막힌다** — `*const ()` 는 `!Send` 이고 `!Sync` 다(std 부정 구현).
- ★★★ `PhantomData<*const ()>` 는 **값이 없는(크기 0) 필드**인데 타입 성질은 빌려 온다 — 사슬이 `PhantomData<*const ()>`(std `core/src/marker.rs`) → `Handle` 로 올라간다. **필드가 평범해도 타입을 끄는 관용구**다.

### 5. ★★ E0658 — 부정 구현은 안정판에 없다, 「marker types」를 쓰라

**출력**

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

**왜 그런가**

- ★★ 「**negative trait bounds are not fully implemented; use marker types for now**」 — 사용자 코드의 `impl !Send` 는 미안정 기능이다(issue #68318). 컴파일러가 권하는 **marker type** 이 4번의 `PhantomData<*const ()>` 다.
- ★ std 는 부정 구현을 **쓴다**(`impl<T, A> !Send for Rc<T, A>` — 서머리 (4)의 `r50_impls`).

### 6. ★★ E0277 — `MutexGuard<'_, Vec<i32>>` cannot be sent between threads safely

**출력**

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

**왜 그런가**

- ★★ **`static` 이라 `'static` 요구는 만족한다** — 그래서 남은 에러가 **순수하게 `Send` 부재**다. 49번의 E0373/E0597 과 섞이지 않는다.
- ★★ 근거는 std 의 **`impl<T: ?Sized> !Send for MutexGuard<'_, T>`**(서머리 (4)). **왜 그렇게 정했는지는 이 문서가 확인하지 못했다.**
- ★ 고치려면 가드가 아니라 **데이터를 꺼내 넘기거나**(`g.clone()`), 락을 **그 스레드 안에서** 잡는다([52번 주제](../52-mutex-rwlock-arc-and-poisoning/)).

### 7. ★★★ `Arc<T>: Send` 는 `T: Sync` 를 요구한다 — 넘긴 뒤에도 원래 스레드에 복제본이 남기 때문이다

- ★★★ std `Sync` 문서: 「**a type `T` is `Sync` if and only if `&T` is `Send`**」.
- ★★★ `Arc` 를 넘겨도 **원래 스레드에 다른 복제본이 남을 수 있다** — 그러면 두 스레드가 **같은 `RefCell` 을 `&` 로** 보는 것과 같다. 그래서 `Arc<T>` 를 보내는 데 `T: Sync` 가 필요하고, 막힌 이유가 **`RefCell<i32>` cannot be shared** 로 나온다.
- ★ [42번 주제](../42-refcell-cell-interior-mutability/) (7)의 전문이 이 연결을 `= note: required for Arc<RefCell<i32>> to implement Send` 로 직접 적는다. 처방은 `RefCell` → **`Mutex`/`RwLock`**(격자에서 `Arc<Mutex>` 는 둘 다 통과).

### 8. ★★ `Cell` 은 넘기기만, `MutexGuard` 는 함께 보기만 — 두 성질은 따로 계산된다

- ★★ **`Cell<i32>`** — 통째로 넘기면 원래 스레드엔 아무것도 없으니 **`Send`**. 두 스레드가 `&Cell` 을 가지면 **둘 다 `set` 으로 고칠 수 있으니 `!Sync`**(std `impl<T> !Sync for Cell<T>`).
- ★★ **`MutexGuard`** — std 가 **`!Send`** 로 못 박았다(6번). 반면 `&MutexGuard` 로는 안을 **읽기만** 할 수 있어 **`T: Sync` 이면 `Sync`**(std 구현 목록).
- ★★★ **그래서 「`!Send` 면 `!Sync`」는 틀리다** — 격자의 네 모양 중 두 칸이 이 엇갈림이다(서머리 (1)의 그림).

### 9. ★★ 컴파일되고 돈다 — 컴파일러는 믿고, 보증은 사람이 했다

- ★★ **컴파일되고 `thread returned true`**(서머리 (6)의 `r50_unsafe_impl`). 자동으로는 `*const u8` 때문에 `!Send` 인 타입이다.
- ★★★ **컴파일러가 확인한 것** — `Send` 가 `unsafe trait` 이므로 **`unsafe impl` 으로 썼다는 것**뿐이다. **안 한 것** — 그 포인터가 다른 스레드에서 써도 안전한지. 여기서는 `static` 을 가리키므로 괜찮다는 **판단을 사람이** 했다.
- ★ `unsafe` 가 푸는 범위와 경계 설계는 목록의 **56번 주제**가 정본이다.

### 10. ★★ 된다 — 자동 트레이트 · 원리는 `언어-특성` §5 · `Rc` → `Arc`, `RefCell` → `Mutex`/`RwLock`

- ★★ **impl 없이 `Send + Sync`** — 서머리 (4)의 `r50_auto` 가 `assert_send`·`assert_sync` 를 통과하고 스레드에 넘어갔다(`thread returned 2`). **필드가 전부 그러면 구조체도 그렇다**는 **자동 트레이트(auto trait)** 규칙이다.
- ★★ **원리의 정본** — [`../../언어-특성/README.md`](../../언어-특성/README.md) §5(「데이터 레이스가 타입 오류가 되는 원리」). 이 편은 **에러를 읽고 고치는 쪽**이다.
- ★★ **바꾼 것** — 41번: `Rc` → **`Arc`**(E0277 이 사라지고 strong 2→1) · 42번: `RefCell` → **`RwLock`**(컴파일러 권고)·`Mutex`.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서·서머리의 **모든 블록** | `capture.sh` — 블록마다 명령을 배너에 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` 기본 규칙 넷 · **고칠 것 0** |
| ★★★ **경계 격자** | `r50_grid.sh` — 열 타입 × send/sync 로 스무 소스를 만들어 컴파일(`\x1f` 구분 · 칸 수 검사) | 20 컴파일 | **`11 / 20`** |
| ★★★ **사슬 읽기** | `r50_chain` · `r50_chain_fields` · `r50_chain_fields_ed`(2018·2021) | 4 컴파일 | 사슬 `Cache` → `Session` · **2018 은 2줄 · 2021 은 0줄** |
| 자동 구현 · 끄기 · 켜기 | `r50_auto` · `r50_phantom` · `r50_negative` · `r50_unsafe_impl` | 4 컴파일 · 2 실행 | 통과 · **E0277 ×2** · **E0658** · 통과 |
| `MutexGuard` | `r50_guard` | 1 | **E0277** |
| std 구현 목록 | `r50_impls.sh` — 로컬 `rust-docs` 의 태그를 벗겨 grep | 8 줄 | **8 / 8 found** |
| **안 던진 것** — 속도 · TSan/Miri · async `Send` 경계 · 범인 아닌 필드만 쓰는 2021 클로저 | — | 0 | ★ 「안 던졌다」로 표시했다 |

**구현 의존 항목**(버전·환경이 바뀌면 **다시 찍어야 하는** 것).

| 항목 | 왜 |
|---|---|
| E0277 문구 · `note:` 사슬의 줄 수와 순서 | ★ rustc 진단 구현 — 판에 매인다 |
| `note:` 가 가리키는 std 소스의 줄 번호(`thread/mod.rs:725` · `marker.rs:822`) | ★ std 판마다 바뀐다 |
| E0658 의 권고 문구와 issue 번호 | ★ 기능이 안정화되면 바뀐다 |
| 로컬 문서의 구현 목록 표기 | ★ rustdoc 판에 매인다(grep 형식) |

★ **다시 찍는 법** — `capture.sh <새 디렉토리>` 를 그대로 돌리고 `normalize-shaky.py <원본> <새 디렉토리>` 로 견준다.
