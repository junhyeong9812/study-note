# rust/syntax/41 — `Rc`/`Arc` 공유 소유권 · `Weak` 와 순환 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [std — `std::rc` 모듈 문서](https://doc.rust-lang.org/std/rc/index.html)(「A cycle between `Rc` pointers will never be deallocated」 · `Send` 아님) ·
> [std — `Rc`](https://doc.rust-lang.org/std/rc/struct.Rc.html)(`make_mut` · `get_mut` · `try_unwrap`) ·
> [std — `Weak`](https://doc.rust-lang.org/std/rc/struct.Weak.html)(`upgrade` · `weak_count`) ·
> [std — `Arc`](https://doc.rust-lang.org/std/sync/struct.Arc.html) ·
> [std — `mem::forget`](https://doc.rust-lang.org/std/mem/fn.forget.html)(§Safety — 순환이 안전한 누수라는 근거).
> ★ 위 문서는 **이 머신의 `rust-docs`(1.92.0) 로컬 사본**을 열어 읽었다.
> **실행 검증** — 이 문서의 모든 출력·에러는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서
> **`rustc --edition 2021 <파일>.rs`** 로 돌려 받은 것이다. Python 대비는 `Python 3.12.3`.\
> ★★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다. 소스 펜스도 캡처가 찍었다.\
> ★★ **외부 크레이트를 하나도 쓰지 않았다.** ★★★ **속도는 한 번도 재지 않았다** — 「`Arc` 는 원자 연산이라 느리다」 류의 문장은 이 문서에 **근거가 없으므로 쓰지 않는다.**
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

★★★ **본체 창 — ① `Drop` 로그와 ② `strong_count`/`weak_count` 카운트 로그다.** 「해제됐나」를 **메모리 도구가 아니라 이 둘로** 묻는다(아래 (0) — 제5의 상태).

```text
===== rustc --version =====
rustc 1.92.0 (ded5c06cf 2025-12-08)
(exit 0)
===== cargo --version =====
cargo 1.92.0 (344c4567c 2025-10-21)
(exit 0)
===== rustup toolchain list =====
stable-x86_64-unknown-linux-gnu (active, default)
(exit 0)
===== g++ --version | head -1 =====
g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
(exit 0)
===== python3 --version =====
Python 3.12.3
(exit 0)
===== rustup component list --installed =====
cargo-x86_64-unknown-linux-gnu
clippy-x86_64-unknown-linux-gnu
rust-docs-x86_64-unknown-linux-gnu
rust-std-x86_64-unknown-linux-gnu
rustc-x86_64-unknown-linux-gnu
rustfmt-x86_64-unknown-linux-gnu
(exit 0)
===== cargo miri --version >/dev/null 2>&1; echo "cargo miri --version exit=$?" =====
cargo miri --version exit=1
(exit 0)
===== command -v valgrind; echo "command -v valgrind exit=$?" =====
command -v valgrind exit=1
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| 안 흔들린다 | ★★★ **`Drop` 로그의 줄 수와 순서** · **카운트 값** | 해제 시점은 언어가 정한다(09번). 카운트는 `Rc` 의 공개 API 가 돌려주는 수다 — **이 주제의 본체** |
| 안 흔들린다 | 순환 격자의 **「`drop` 줄이 없는 칸 1 / 6」** | 스크립트가 세어 마지막 줄로 찍는다 |
| 안 흔들린다 | E0277 번호·제목·`파일:줄:칸` · 종료 코드 | 같은 rustc 판에서 고정이다 |
| 안 흔들린다 — 단 **CPython 판의 세부** | `gc.collect()` 의 반환값 `2` | 판이 바뀌면 수집기가 세는 법이 바뀔 수 있다 |
| ★ **싣지 않았다** | 주소값 | `make_mut` 의 「같은 할당인가」는 **참/거짓**(`Rc::as_ptr` 비교 · `Rc::ptr_eq`)으로만 찍었다 |

★ 정규화 규칙은 **기본 넷**만 쓴다. 이 편의 블록에는 걸리는 칸이 없었다(패닉이 없다).

## 한눈에 — 쉽게 말하면

**`Rc` 는 「공동 명의 통장」이다. 명의자가 몇 명인지(강한 카운트)를 은행이 세고, 마지막 명의자가 빠지는 날 통장을 닫는다.
`Weak` 는 「조회만 되는 카드」다 — 통장이 아직 열려 있으면 그때 잠깐 명의자가 될 수 있고(`upgrade`), 닫혔으면 `None` 이다.
두 사람이 **서로를 명의자로** 올려 두면 둘 다 떠나도 통장은 영영 안 닫힌다 — 그게 순환이다.**

| 비유 | 실체 |
|---|---|
| 「**명의자 수**」 | ★★ **`Rc::strong_count`** — `clone` 마다 +1, `drop` 마다 −1((1)) |
| 「**조회 카드 수**」 | ★ **`Rc::weak_count`** — `downgrade` 로 늘어난다. ★ **명의자가 0 이 되면 0 으로 답한다**((1)의 `[7]`) |
| 「**조회 카드로 잠깐 명의자 되기**」 | ★★ **`Weak::upgrade`** — `Some(Rc)` 를 쥐는 동안 강한 카운트가 **하나 는다**((1)의 `[4]`) |
| 「**서로를 명의자로**」 | ★★★ **부모↔자식 `Rc` 순환** — 스코프가 끝나도 **`drop` 줄이 0 줄**, 카운트 **1 · 1** 이 남는다((2)) |
| 「**한쪽을 조회 카드로**」 | ★★★ **자식 → 부모를 `Weak`** — `drop parent` · `drop child` 가 찍힌다((2)) |
| 「**다른 지점으로 못 들고 간다**」 | ★★ **`Rc` 는 `Send` 가 아니다** — `thread::spawn` 에 넘기면 **E0277**. `Arc` 는 된다((3)) |
| 「**명의자가 나 하나면 그냥 고치고, 아니면 사본을 떠서 고친다**」 | ★ **`Rc::make_mut`** — 카운트가 1 이면 제자리, 2 면 **복사**((4)) |

```text
   ★ 순환이 왜 안 풀리나 — (2)의 두 블록 그대로

   Rc ↔ Rc                                        Rc → / ← Weak
   ┌─parent─┐  Rc   ┌─child──┐                     ┌─parent─┐  Rc   ┌─child──┐
   │ strong ├──────▶│ strong │                     │ strong ├──────▶│ strong │
   │   2    │◀──────┤   2    │                     │   1    │◀ ─ ─ ┤   2    │
   └────────┘  Rc   └────────┘                     └────────┘ Weak  └────────┘
   변수 둘이 사라지면 → 1 · 1                       변수 둘이 사라지면 → parent 0 → drop parent
   서로가 서로의 마지막 명의자라 0 이 안 된다          → parent 가 쥔 Rc 가 풀려 child 0 → drop child
   drop 줄 0 줄 · main 이 끝나도                     drop 줄 2 줄
```

> **공유 소유권(shared ownership)** — 값 하나에 **주인이 여럿**인 것. Rust 의 기본은 주인 하나다(08번). `Rc` 는 그 규칙을 **런타임 카운트로 완화**한다.\
> 예: `let b = Rc::clone(&a);` — 이제 `a` 와 `b` 가 같은 값을 소유한다.

> **강한 참조 / 약한 참조(strong / weak)** — 강한 쪽은 값을 **살려 두고**, 약한 쪽은 **살려 두지 않는다.** std: 「`Weak` 는 할당 안의 **값**을 살려 두지 않는다. 다만 **할당**(뒷받침 저장소)은 살려 둔다」.\
> 예: `Rc::downgrade(&a)` 는 약한 참조를 만든다.

## 이 주제가 답하려는 질문

1. ★★★ **「한 소유자」 규칙을 풀면 무엇을 내나** — 카운트가 언제 움직이고, 값은 **정확히 어느 줄에서** 해제되나((1)).
2. ★★★ **순환 참조는 왜 해제되지 않고, `Weak` 는 그것을 어떻게 고치나** — 그리고 **어느 방향**을 약하게 두나((2)).
3. ★★ **`Rc` 와 `Arc` 는 무엇으로 갈리나** — 그리고 공유된 값을 **고치려면**((3)·(4)).

★ **선행** — [**40번 주제**](../40-box-recursive-types-and-dyn/)의 (1) `Rc` 판(꼬리를 나눠 가진 리스트 — `owners of the shared tail 3`)과 (5)의 **E0507**(`*r` 로 옮겨 꺼낼 수 없다)·**`Rc::try_unwrap`**(주인이 둘이면 `Err`, 하나면 `Ok`)이 이 주제의 출발점이다 — **다시 재지 않고 인용한다.**
[**30번 주제**](../30-operator-overloading-std-ops-index-and-deref/)의 (9)는 **`Rc::strong_count` 가 메서드가 아닌 이유**(E0599 · `T` 의 메서드와 안 부딪히게)를 이미 에러 전문으로 보였다.
[**09번 주제**](../09-copy-clone-and-drop/)의 (6)이 **`Drop` 로그로 해제 시점을 보는 창**의 정본이다.

★★★ **정본 경계** — 목록 README 는 「참조 카운팅 일반은 [`memory-management/`](../../../../memory-management/README.md)」라고 적지만, **그 문서에는 참조 카운팅 절이 없다**(`grep -n '참조 카운팅\|카운팅\|순환'` → 0줄 — 확인했다). 스택·힙 일반만 있다.
참조 카운팅과 순환 수집의 **일반론**은 실제로 이 셋에 흩어져 있다 — [`variables-and-memory/`](../../../../variables-and-memory/README.md)(「참조 횟수로 해결하지 못하는 케이스가 순환참조」 한 줄) ·
Python 갈래 [`01-object-and-name-binding`](../../../python/syntax/01-object-and-name-binding/2-summary.md)(`sys.getrefcount` · 순환은 `gc` 모듈) ·
C++ 갈래 [`27-shared-ptr-and-reference-counting`](../../../cpp/syntax/27-shared-ptr-and-reference-counting/2-summary.md) · [`28-weak-ptr-and-reference-cycles`](../../../cpp/syntax/28-weak-ptr-and-reference-cycles/2-summary.md)(제어 블록·원자 명령·순환).
**여기는 `Rc`/`Arc` 를 쓸지·어느 쪽을 `Weak` 로 둘지의 판단만** 쓴다.
★ **C++ 27편 (8)과 28편 (6)이 Rust 블록을 이미 하나씩 던졌다**(`Rc` 를 스레드로 → E0277 · `Rc`/`Weak` 트리 두 판). 이 편은 그 **정본 자리**이고, 두 블록과 **같은 결과**를 이 편의 캡처로 다시 얻었다((2)·(3)).

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ① `Drop` 로그와 ② 카운트 로그다

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ① ★★★ **`impl Drop` + `println!`** | 값이 **해제됐나, 어느 줄에서** | ★ **본체** — 순환 누수의 증거는 **이 로그가 0 줄**인 것이다 |
| ② ★★★ **`strong_count` / `weak_count`** | 해제되지 **않은 이유**(누가 아직 쥐고 있나) | ★ **본체** — 스코프가 끝난 뒤에도 **1** 이 남는 것 |
| ③ ★★ **컴파일러 진단 E0277** | `Rc` 가 스레드를 **못 넘는** 것 | 쓴다((3)) |
| ④ ★ **`Rc::ptr_eq` · `Rc::as_ptr` 비교(참/거짓)** | `make_mut` 가 **복사했나** | 쓴다((4)) — 주소값 자체는 싣지 않는다 |
| ⑤ **Python `__del__` 로그 + `gc.collect()`** | 추적 수집기가 있는 언어는 순환을 **회수하나** | 대비로 쓴다((5)) |
| 메모리 누수량(바이트) | 「얼마나 샜나」 | ★★★ **못 잰 것** — Miri 도 valgrind 도 이 머신에 없다(머리말 블록: 설치된 구성 요소에 `miri` 가 없고 `cargo miri --version exit=1` · `command -v valgrind exit=1`). **누수량은 주장하지 않는다** |
| 실행 시간 · 원자 명령 비용 | 「`Arc` 는 느리다」 | ★ **부적용 — 재지 않는다.** 원자 명령을 **센** 것은 C++ 27편 (7)이다(`shared_ptr` 복사 대입 한 번 = 원자 명령 4개) — Rust 쪽은 세지 않았다 |

★★ **제5의 상태 — 「같은 질문을 다른 창으로」.** 「순환이면 **샌다**」를 메모리 도구로 물을 수 없어서(도구 없음), 질문을 **「그 값의 `Drop` 이 불렸나 · 누가 아직 쥐고 있나」** 로 바꿔 ①·② 에 물었다.
★ 바꾼 창이 **못 보는 것** — ①·②는 「**해제 안 됨**」까지만 말한다. **몇 바이트가 남았는지, `Weak` 가 붙든 할당이 언제 반납되는지**는 못 본다. 그 자리는 C++ 27편 (6)이 ASan·계수기로 쟀다(`make_shared` + `weak_ptr` 가 남으면 **블록이 언제 풀리나**).

### (1) ★★★ 카운트 로그 — `clone` · `downgrade` · `upgrade` · `drop` 마다

**언제 쓰나** — 「이 값은 지금 누가 쥐고 있나」가 궁금할 때마다. 디버깅의 첫 창이다.

```text
===== 소스: r41_count.rs =====
use std::rc::{Rc, Weak};

struct D(&'static str);
impl Drop for D {
    fn drop(&mut self) {
        println!("      drop {}", self.0);
    }
}

fn show(step: &str, w: &Weak<D>) {
    println!("{step:<34} strong {}  weak {}", w.strong_count(), w.weak_count());
}

fn main() {
    let a = Rc::new(D("value"));
    let w = Rc::downgrade(&a);
    show("[1] Rc::new + one downgrade", &w);
    let b = Rc::clone(&a);
    show("[2] after Rc::clone", &w);
    let w2 = w.clone();
    show("[3] after Weak::clone", &w);
    {
        let up = w.upgrade();
        show("[4] while an upgrade is held", &w);
        println!("    upgrade is_some = {}", up.is_some());
    }
    show("[5] after the upgrade is dropped", &w);
    drop(a);
    show("[6] after drop(a)", &w);
    drop(b);
    show("[7] after drop(b)", &w);
    println!("    upgrade is_some = {}", w.upgrade().is_some());
    drop(w2);
    show("[8] after drop(w2)", &w);
}
===== rustc --edition 2021 r41_count.rs =====
(exit 0)
===== ./r41_count =====
[1] Rc::new + one downgrade        strong 1  weak 1
[2] after Rc::clone                strong 2  weak 1
[3] after Weak::clone              strong 2  weak 2
[4] while an upgrade is held       strong 3  weak 2
    upgrade is_some = true
[5] after the upgrade is dropped   strong 2  weak 2
[6] after drop(a)                  strong 1  weak 2
      drop value
[7] after drop(b)                  strong 0  weak 0
    upgrade is_some = false
[8] after drop(w2)                 strong 0  weak 0
(exit 0)
```

- ★★ **`Rc::clone` → 강한 +1**(`[2]`) · **`Weak::clone` → 약한 +1**(`[3]`) — 둘 다 **값을 복사하지 않는다.** 카운트만 는다.
- ★★ **`upgrade` 가 `Some` 을 돌려주는 동안 강한 카운트가 3**(`[4]`) — `upgrade` 는 「보기」가 아니라 **잠깐 명의자가 되는 것**이다. 쥔 `Rc` 가 블록 끝에서 버려지자 **2 로 돌아왔다**(`[5]`).
- ★★★ **`drop value` 는 `[6]` 과 `[7]` 사이에 찍혔다** — 즉 **`drop(b)` 가 마지막 강한 참조를 버린 그 자리**다. `drop(a)` 때는 안 찍혔다(`b` 가 남아 있었다).
- ★★★ **그 뒤 `upgrade` 는 `None`(`is_some = false`)** — 이것이 「`Weak::upgrade` 가 `None` 이 되는 순간」이다. **`Weak` 두 개(`w` · `w2`)가 아직 살아 있는데도** 값은 이미 없다.
- ★★ **예상과 달랐던 칸 — `[7]` 의 `weak 0`.** `w`·`w2` 가 살아 있으니 2 일 줄 알았다. std 의 `Weak::weak_count` 문서: 「**If no strong pointers remain, this will return zero.**」 — **강한 쪽이 0 이면 약한 수를 세지 않고 0 을 답한다.** 그래서 이 수로 「`Weak` 가 몇 개 남았나」를 셀 수는 없다.

```text
   (1)의 강한 카운트 — 한 줄에 한 사건

   [1] Rc::new        ● ─────────────────────────── 1
   [2] Rc::clone      ● ● ───────────────────────── 2
   [4] upgrade 쥠     ● ● ● ─────────────────────── 3   ← upgrade 도 명의자다
   [5] 그것을 버림    ● ● ───────────────────────── 2
   [6] drop(a)        ● ─────────────────────────── 1
   [7] drop(b)        (0) ── drop value ─────────── 0   ← 이 줄에서 해제
       upgrade        None                              ← Weak 는 둘 다 살아 있는데
```

비용 — 카운트 증감이 **런타임에** 일어난다(그것이 「대가」의 첫째다). **얼마나 비싼지는 재지 않았다.**

### (2) ★★★ 순환 누수 재현 — `Rc ↔ Rc` 대 `Rc → / ← Weak`

**언제 쓰나** — 트리의 부모 포인터, 그래프, 관찰자 목록처럼 **양방향 링크**가 필요할 때.

**둘 다 `Rc` 로 서로를 쥐면.**

```text
===== 소스: r41_cycle_rc.rs =====
use std::cell::RefCell;
use std::rc::Rc;

struct Node {
    name: &'static str,
    other: RefCell<Option<Rc<Node>>>,
}
impl Drop for Node {
    fn drop(&mut self) {
        println!("      drop {}", self.name);
    }
}

fn main() {
    let probe_p;
    let probe_c;
    {
        let parent = Rc::new(Node { name: "parent", other: RefCell::new(None) });
        let child = Rc::new(Node { name: "child", other: RefCell::new(None) });
        *parent.other.borrow_mut() = Some(Rc::clone(&child));
        *child.other.borrow_mut() = Some(Rc::clone(&parent));
        probe_p = Rc::downgrade(&parent);
        probe_c = Rc::downgrade(&child);
        println!("[1] in scope      parent strong {}  child strong {}", probe_p.strong_count(), probe_c.strong_count());
    }
    println!("[2] scope ended   parent strong {}  child strong {}", probe_p.strong_count(), probe_c.strong_count());
    println!("[3] end of main");
}
===== rustc --edition 2021 r41_cycle_rc.rs =====
(exit 0)
===== ./r41_cycle_rc =====
[1] in scope      parent strong 2  child strong 2
[2] scope ended   parent strong 1  child strong 1
[3] end of main
(exit 0)
```

- ★★★ **`drop` 줄이 한 줄도 없다** — 스코프가 끝나도(`[2]`), `main` 이 끝나도(`[3]` 뒤). **이 0 줄이 누수의 증거다.**
- ★★★ **`[2]` 카운트 1 · 1** — 변수 `parent`·`child` 는 사라졌는데 **서로가 서로를 한 번씩 쥐고 있다.** 0 이 될 길이 없다. 탐침(`probe_p`·`probe_c`)이 `Weak` 라서 이 수를 **값을 살려 두지 않고** 읽을 수 있었다.
- ★★ **컴파일 에러도 경고도 없다**(`exit 0`). std 모듈 문서가 그대로 적는다 — 「**A cycle between `Rc` pointers will never be deallocated.**」

**자식 → 부모를 `Weak` 로 바꾸면.**

```text
===== 소스: r41_cycle_weak.rs =====
use std::cell::RefCell;
use std::rc::{Rc, Weak};

struct Parent {
    child: RefCell<Option<Rc<Child>>>,
}
struct Child {
    parent: RefCell<Weak<Parent>>,
}
impl Drop for Parent {
    fn drop(&mut self) {
        println!("      drop parent");
    }
}
impl Drop for Child {
    fn drop(&mut self) {
        println!("      drop child");
    }
}

fn main() {
    let probe_p;
    let probe_c;
    {
        let parent = Rc::new(Parent { child: RefCell::new(None) });
        let child = Rc::new(Child { parent: RefCell::new(Weak::new()) });
        *parent.child.borrow_mut() = Some(Rc::clone(&child));
        *child.parent.borrow_mut() = Rc::downgrade(&parent);
        probe_p = Rc::downgrade(&parent);
        probe_c = Rc::downgrade(&child);
        println!("[1] in scope      parent strong {}  child strong {}", probe_p.strong_count(), probe_c.strong_count());
        println!("    child -> parent upgrade is_some = {}", child.parent.borrow().upgrade().is_some());
    }
    println!("[2] scope ended   parent strong {}  child strong {}", probe_p.strong_count(), probe_c.strong_count());
    println!("[3] end of main");
}
===== rustc --edition 2021 r41_cycle_weak.rs =====
(exit 0)
===== ./r41_cycle_weak =====
[1] in scope      parent strong 1  child strong 2
    child -> parent upgrade is_some = true
      drop parent
      drop child
[2] scope ended   parent strong 0  child strong 0
[3] end of main
(exit 0)
```

- ★★★ **`drop parent` → `drop child` 두 줄이 스코프 끝에 찍혔다.** `[2]` 카운트 **0 · 0**.
- ★★ **`[1]` parent strong 1** — 자식이 쥔 것은 `Weak` 라 부모의 강한 수에 안 들어간다. 그래서 변수 `parent` 가 사라지는 순간 **0 이 되어 부모가 먼저 해제**되고, 부모가 쥔 `Rc<Child>` 가 풀리면서 자식이 뒤따른다.
- ★ 자식은 필요할 때 `child.parent.borrow().upgrade()` 로 부모를 **잠깐** 얻는다(`is_some = true`). 부모가 이미 없으면 `None` — (1)에서 본 그 순간이다.
- ★ **`RefCell` 이 끼어 있다** — 만든 **뒤에** 링크를 채워야 해서다(`Rc` 안의 값은 공유 참조로만 보인다). `RefCell` 은 [**42번 주제**](../42-refcell-cell-interior-mutability/)가 정본이다.

**어느 방향을 `Weak` 로 두나 — 여섯 칸 격자.**

```text
===== 소스: r41_cycle_grid.sh =====
# parent->child 와 child->parent 링크를 각각 Rc / Weak / 없음 으로 바꿔 던진다 — 스코프가 끝난 뒤 drop 줄 수를 센다
T=$'\t'
printf 'parent->child\tchild->parent\tchild strong after drop(c)\tdrop lines at scope end\tparent strong after scope\n'
n=0; total=0
for pc in Rc Weak; do
  for cp in Rc Weak none; do
    { echo 'use std::cell::RefCell;'
      echo 'use std::rc::{Rc, Weak};'
      echo 'struct N { name: &'"'"'static str, a: RefCell<Option<Rc<N>>>, b: RefCell<Weak<N>> }'
      echo 'impl Drop for N { fn drop(&mut self) { println!("drop {}", self.name); } }'
      echo 'fn main() {'
      echo '    let probe;'
      echo '    {'
      echo '        let p = Rc::new(N { name: "parent", a: RefCell::new(None), b: RefCell::new(Weak::new()) });'
      echo '        let c = Rc::new(N { name: "child", a: RefCell::new(None), b: RefCell::new(Weak::new()) });'
      [ $pc = Rc ]   && echo '        *p.a.borrow_mut() = Some(Rc::clone(&c));'
      [ $pc = Weak ] && echo '        *p.b.borrow_mut() = Rc::downgrade(&c);'
      [ $cp = Rc ]   && echo '        *c.a.borrow_mut() = Some(Rc::clone(&p));'
      [ $cp = Weak ] && echo '        *c.b.borrow_mut() = Rc::downgrade(&p);'
      echo '        probe = Rc::downgrade(&p);'
      echo '        let pc = Rc::downgrade(&c);'
      echo '        drop(c);'
      echo '        println!("~~~ {}", pc.strong_count());'
      echo '        println!("---");'
      echo '    }'
      echo '    println!("=== {}", probe.strong_count());'
      echo '}'
    } > g.rs
    rustc --edition 2021 -A unused -o g g.rs || exit 1
    out=$(./g) || exit 1
    drops=$(printf '%s\n' "$out" | sed -n '/^---$/,/^===/p' | grep -c '^drop' || true)
    strong=$(printf '%s\n' "$out" | sed -n 's/^=== //p')
    cs=$(printf '%s\n' "$out" | sed -n 's/^~~~ //p')
    row="$pc${T}$cp${T}$cs${T}$drops${T}$strong"
    cols=$(printf '%s' "$row" | awk -F'\t' '{print NF}')
    [ "$cols" = 5 ] || { echo "column count $cols != 5"; exit 1; }
    printf '%s\n' "$row"
    total=$((total+1)); [ "$drops" = 0 ] && n=$((n+1))
  done
done
echo "cells with no drop line at scope end: $n / $total"
===== bash r41_cycle_grid.sh =====
parent->child	child->parent	child strong after drop(c)	drop lines at scope end	parent strong after scope
Rc	Rc	1	0	1
Rc	Weak	1	2	0
Rc	none	1	2	0
Weak	Rc	0	1	0
Weak	Weak	0	1	0
Weak	none	0	1	0
cells with no drop line at scope end: 1 / 6
(exit 0)
```

- ★★★ **「`drop` 줄이 없는 칸 1 / 6」** — **둘 다 `Rc` 인 칸 하나뿐**이다. 어느 한쪽이라도 `Weak`(또는 없음)면 순환이 아니라 스코프 끝에 풀린다.
- ★★★ **그런데 방향이 다른 것을 가른다 — 셋째 칸 `child strong after drop(c)`.** 부모 → 자식이 **`Rc` 인 세 칸은 1**(변수 `c` 를 버려도 **부모가 자식을 살려 둔다**), **`Weak` 인 세 칸은 0**(변수를 버리는 순간 **자식이 죽는다** — 스코프 끝의 `drop` 줄이 1 줄인 이유가 그것이다. 자식은 이미 그 전에 갔다).
- ★★ **그래서 판단 규칙** — **「누가 누구를 살려 둬야 하나」로 고른다.** 트리에서는 부모가 자식을 소유하므로 **부모 → 자식이 `Rc`, 자식 → 부모가 `Weak`** 다(std 모듈 문서의 예와 같다). 반대로 두면 순환은 없지만 **자식이 태어나자마자 죽는다.**
- ★ C++ 28편 (3)이 같은 질문(「어느 방향을 `weak_ptr` 로」)을 설계 셋으로 쟀다 — **답의 모양이 같다.**

비용 — `Weak` 를 쓰는 쪽은 **매번 `upgrade` 로 `Option` 을 풀어야** 한다. 코드가 길어지는 것이 대가다.

### (3) ★★ `Rc` 를 스레드로 보내면 — E0277, 그리고 `Arc`

**언제 쓰나** — 공유 값을 **다른 스레드**에 넘겨야 할 때.

```text
===== 소스: r41_send.rs =====
use std::rc::Rc;
use std::thread;

fn main() {
    let a = Rc::new(String::from("shared"));
    let b = Rc::clone(&a);
    let h = thread::spawn(move || b.len());
    println!("{}", h.join().unwrap());
}
===== rustc --edition 2021 r41_send.rs =====
error[E0277]: `Rc<String>` cannot be sent between threads safely
 --> r41_send.rs:7:27
  |
7 |     let h = thread::spawn(move || b.len());
  |             ------------- -------^^^^^^^^
  |             |             |
  |             |             `Rc<String>` cannot be sent between threads safely
  |             |             within this `{closure@r41_send.rs:7:27: 7:34}`
  |             required by a bound introduced by this call
  |
  = help: within `{closure@r41_send.rs:7:27: 7:34}`, the trait `Send` is not implemented for `Rc<String>`
note: required because it's used within this closure
 --> r41_send.rs:7:27
  |
7 |     let h = thread::spawn(move || b.len());
  |                           ^^^^^^^
note: required by a bound in `spawn`
 --> /rustc/ded5c06cf21d2b93bffd5d884aa6e96934ee4234/library/std/src/thread/mod.rs:725:1

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0277`.
(exit 1)
```

- ★★★ **E0277 — `` `Rc<String>` cannot be sent between threads safely ``.** `= help:` 가 「the trait `Send` is not implemented for `Rc<String>`」 — `thread::spawn` 이 `F: Send` 를 요구하고, 클로저가 `Rc` 를 쥐었기 때문이다.
- ★ std 모듈 문서: 「`Rc` 는 **비원자(non-atomic)** 카운트를 쓴다 … 그래서 `Rc` 는 스레드 사이로 보낼 수 없고 `Send` 를 구현하지 않는다. **컴파일러가 컴파일 시점에 검사한다.** 원자 카운트가 필요하면 `sync::Arc`」.
- ★ [**32번 주제**](../32-impl-trait-argument-return-position-and-2024-capture/) (3)이 같은 E0277 을 **`impl Display` 뒤에 숨은 `Rc<i32>`** 로 보였다(에러가 감춘 타입을 이름으로 말한다). C++ 27편 (8)의 `rcsend.rs` 도 같은 번호·같은 문구다.

**`Arc` 로 바꾸면.**

```text
===== 소스: r41_send_arc.rs =====
use std::sync::Arc;
use std::thread;

fn main() {
    let a = Arc::new(String::from("shared"));
    let b = Arc::clone(&a);
    println!("before spawn   strong {}", Arc::strong_count(&a));
    let h = thread::spawn(move || b.len());
    println!("thread returned {}", h.join().unwrap());
    println!("after join     strong {}", Arc::strong_count(&a));
}
===== rustc --edition 2021 r41_send_arc.rs =====
(exit 0)
===== ./r41_send_arc =====
before spawn   strong 2
thread returned 6
after join     strong 1
(exit 0)
```

- ★★ **통과** — `spawn` 전 **strong 2**, `join` 뒤 **strong 1**(스레드가 쥔 `b` 가 스레드와 함께 해제됐다).
- ★★★ **대가를 적는 법** — `Arc` 가 `Rc` 와 다른 것은 **카운트를 원자적으로 갱신한다**는 것이다(std). **그것이 얼마의 시간인지는 이 문서가 재지 않았다** — 「느리다」로 적지 않는다. 적을 수 있는 것은 **「`Rc` 로 되는 자리에 `Arc` 를 쓸 이유가 없다」는 타입 수준의 판단**까지다.
- ★ `Arc` 는 **안의 값에 대해서는 아무것도 안 해 준다** — `Arc<T>` 가 `Send` 이려면 `T: Send + Sync` 여야 한다(std 의 `impl Send for Arc<T>` 경계). `Arc<RefCell<T>>` 가 막히는 자리가 [**42번 주제**](../42-refcell-cell-interior-mutability/)의 E0277 이다.

### (4) ★ 공유된 값을 고치려면 — `make_mut` · `get_mut` · `try_unwrap`

**언제 쓰나** — `Rc<T>` 는 `&T` 만 주므로(`Deref`), 안을 고치려면 **나 혼자인지**를 먼저 물어야 한다.

```text
===== 소스: r41_make_mut.rs =====
use std::rc::Rc;

fn main() {
    let mut a = Rc::new(String::from("v1"));
    let p0 = Rc::as_ptr(&a);
    Rc::make_mut(&mut a).push_str("+x");
    println!("[1] one owner   a={a}  same allocation {}  strong {}", Rc::as_ptr(&a) == p0, Rc::strong_count(&a));

    let b = Rc::clone(&a);
    Rc::make_mut(&mut a).push_str("+y");
    println!("[2] two owners  a={a}  b={b}  ptr_eq {}  strong a {} b {}", Rc::ptr_eq(&a, &b), Rc::strong_count(&a), Rc::strong_count(&b));

    let mut c = Rc::clone(&b);
    println!("[3] get_mut while shared   is_some {}", Rc::get_mut(&mut c).is_some());
    drop(b);
    println!("[4] get_mut after drop(b)  is_some {}", Rc::get_mut(&mut c).is_some());
}
===== rustc --edition 2021 r41_make_mut.rs =====
(exit 0)
===== ./r41_make_mut =====
[1] one owner   a=v1+x  same allocation true  strong 1
[2] two owners  a=v1+x+y  b=v1+x  ptr_eq false  strong a 1 b 1
[3] get_mut while shared   is_some false
[4] get_mut after drop(b)  is_some true
(exit 0)
```

- ★★ **`[1]` 주인이 하나** — `make_mut` 가 **제자리에서** 고쳤다(`same allocation true` · strong 1).
- ★★★ **`[2]` 주인이 둘** — `make_mut` 가 **안의 값을 복사해 새 할당으로** 옮기고 거기를 고쳤다. `a=v1+x+y` · **`b=v1+x` 그대로** · `ptr_eq false` · 카운트 **1 · 1**(갈라졌다). std: 「다른 `Rc` 가 있으면 **안의 값을 새 할당으로 복제**한다 — **clone-on-write**」.
- ★ **`[3]`·`[4]` `get_mut`** — 공유 중이면 `None`, 혼자가 되면 `Some`. **복사하지 않는 대신 실패할 수 있는** 쪽이다.
- ★ **`try_unwrap`**(혼자면 안의 값을 **옮겨** 꺼냄)은 [**40번 주제**](../40-box-recursive-types-and-dyn/) (5)의 `r40_rc_ways` 가 쟀다 — 주인 둘이면 `Err`, 하나면 `Ok(String)`.

| 함수 | 공유 중일 때 | 혼자일 때 | 요구 |
|---|---|---|---|
| `Rc::make_mut(&mut rc)` | ★ **복제 후 고침**(갈라진다) | 제자리 | `T: Clone` |
| `Rc::get_mut(&mut rc)` | `None` | `Some(&mut T)` | 없음 |
| `Rc::try_unwrap(rc)` | `Err(rc)` | `Ok(T)` — 옮겨 꺼냄 | 없음 |
| `Rc<RefCell<T>>` | ★ **모두가 같은 값을 고친다** | 〃 | 런타임 빌림 검사(42번) |

★★ **마지막 줄이 갈림길이다** — 「각자 사본」을 원하면 `make_mut`, 「모두가 같은 것」을 원하면 `Rc<RefCell<T>>` 다.

### (5) ★★ Python 대비 — 추적 수집기가 있는 언어는 순환을 회수한다

**언제 쓰나** — 「참조 카운팅 언어는 다 순환에서 새나」를 물을 때.

```text
===== 소스: r41_py_cycle.py =====
import gc

class Node:
    def __init__(self, name):
        self.name = name
        self.other = None
    def __del__(self):
        print("      del", self.name)

gc.disable()
p, c = Node("parent"), Node("child")
p.other, c.other = c, p
del p, c
print("[1] names deleted")
print("[2] gc.collect() returned", gc.collect())
print("[3] end")
===== python3 r41_py_cycle.py =====
[1] names deleted
      del parent
      del child
[2] gc.collect() returned 2
[3] end
(exit 0)
```

- ★★★ **`del p, c` 뒤에는 `__del__` 이 안 불렸다**(`[1]` 다음 줄이 곧장 `gc.collect()`). **참조 카운트만으로는 Rust 와 같다** — 서로를 쥐어 0 이 안 된다(`gc.disable()` 로 자동 수집을 꺼 두었다).
- ★★★ **`gc.collect()` 가 부르자 `del parent` · `del child` 가 찍혔다**(반환값 2). CPython 은 참조 카운팅 위에 **순환 수집기**를 따로 둔다.
- ★★★ **Rust 에는 그 수집기가 없다** — (2)의 `Rc ↔ Rc` 는 **`main` 이 끝날 때까지** `drop` 이 0 줄이었다. **Rust 는 순환을 절대 회수하지 않는다. 끊는 것은 `Weak` 를 쓰는 사람의 몫이다.**
- ★ C++ 27편 (8)이 같은 대비를 `weakref` 로 쟀다(「살아 있나 `True` → `gc.collect()` 2 → `False`」). 이 편은 **`Drop` 로그와 짝이 되게 `__del__` 로그**로 물었다.

## 문법 — 형태와 규칙

```text
   use std::rc::{Rc, Weak};         use std::sync::{Arc, Weak as AWeak};   ← 스레드를 넘으면 Arc

   let a = Rc::new(v);              ← 강한 1
   let b = Rc::clone(&a);           ← 강한 +1 (값은 복사하지 않는다) — a.clone() 도 되지만 무엇을 복제하는지 안 보인다(30번 (9))
   let w: Weak<T> = Rc::downgrade(&a);   ← 약한 +1
   if let Some(rc) = w.upgrade() { … }   ← 살아 있으면 잠깐 강한 +1
   Rc::strong_count(&a)  Rc::weak_count(&a)   ← 연관 함수 — 메서드 문법 아님(E0599, 30번 (9))
   Rc::make_mut(&mut a)  Rc::get_mut(&mut a)  Rc::try_unwrap(a)
```

- ★★★ **값은 마지막 강한 참조가 사라지는 줄에서 해제된다** — `Weak` 는 셈에 안 든다((1)).
- ★★★ **`Rc` 끼리의 순환은 해제되지 않는다** — 에러도 경고도 없다((2)).
- ★★ **`Rc` 는 `Send`·`Sync` 가 아니다 — 스레드를 넘으면 `Arc`**((3)).
- ★ **`Rc<T>` 는 `&T` 만 준다** — 고치려면 `make_mut`·`get_mut`·`RefCell`((4)).

## 어디서 틀리나

### 1. ★★★ 「Rust 는 메모리 안전하니 누수도 없다」

(2)가 반증이다 — **`Rc ↔ Rc` 는 `drop` 이 0 줄**이고 `exit 0` 이다. std 의 `mem::forget` 문서가 이유를 적는다: 「Rust 의 안전성 보장에는 **소멸자가 반드시 불린다는 보장이 없다.** 예를 들어 `Rc` 로 순환을 만들 수 있다」. **누수는 안전하다(정의되지 않은 동작이 아니다) — 그래서 컴파일러가 안 막는다.**

### 2. ★★★ 「순환만 끊으면 어느 쪽을 `Weak` 로 해도 같다」

(2)의 격자 셋째 칸 — **부모 → 자식을 `Weak` 로 두면 자식이 곧장 죽는다**(`0`). 해제 여부(`1 / 6`)만 보면 다섯 칸이 같아 보이지만 **수명은 다르다.**

### 3. ★★ 「`Weak` 가 살아 있으면 `weak_count` 로 셀 수 있다」

(1)의 `[7]` — `Weak` 가 둘 살아 있는데 **0** 이다. 강한 쪽이 0 이면 0 을 답한다(std).

### 4. ★★ 「`upgrade` 는 보기만 한다」

(1)의 `[4]` — 쥐는 동안 **강한 카운트가 3** 이다. `upgrade` 로 얻은 `Rc` 를 오래 쥐면 **그동안 값이 안 죽는다.**

### 5. ★★ 「`Arc` 로 바꾸면 스레드 문제가 전부 풀린다」

`Arc` 가 주는 것은 **카운트의 원자성**뿐이다. 안의 값이 `Sync` 가 아니면 여전히 막힌다 — `Arc<RefCell<T>>` 의 E0277([42번](../42-refcell-cell-interior-mutability/)).

### 6. ★★ 「`make_mut` 는 늘 제자리에서 고친다」

(4)의 `[2]` — 주인이 둘이면 **복제**하고 갈라진다. 다른 주인은 **옛 값**을 본다.

### 7. ★ 「`Arc` 는 원자 연산이라 느리니 피한다」

**이 문서는 재지 않았다.** 「원자적이다」는 std 의 사실이고, 「느리다」는 측정이 필요한 주장이다. 판단은 **「스레드를 넘느냐」**(타입이 알려 준다 — E0277)로 한다.

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| 마지막 강한 참조가 사라질 때 값이 `drop` 된다 | ★ **std 의 `Rc` 계약** | std `Rc` 문서 · (1) |
| `Rc` 끼리의 순환은 해제되지 않는다 | ★ **std 가 명시** 「will never be deallocated」 | (2) |
| 누수가 **안전**하다(컴파일러가 막지 않는다) | ★ **언어의 안전성 정의** — 소멸자 실행은 보장 밖 | `mem::forget` §Safety |
| `Rc: !Send`, `Arc: Send`(경계 붙음) | ★ **std 의 트레이트 구현** — 컴파일러가 강제 | E0277 · (3) |
| `weak_count` 가 강한 0 에서 0 을 답한다 | ★ **std 문서의 계약** | (1) `[7]` |
| 카운트가 **어디에** 있나(값 옆의 두 칸) | ★ **구현 세부** — std 가 공개 API 로 약속하지 않는다. 이 문서는 **레이아웃을 싣지 않았다** | — |
| `gc.collect()` 가 `2` 를 돌려준 것 | ★ **CPython 판의 세부** | (5) |

★ **E0277 의 문구와 `help:` 모양은 rustc 판에 매인다** — 번호와 「`Send` 가 없다」는 성질을 기억한다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 근거 |
|---|---|---|
| 주인이 하나 | **`Box`**(40번) 또는 그냥 값 | 카운트가 필요 없다 |
| 한 스레드 안에서 주인이 여럿, 누가 마지막일지 모른다 | **`Rc`** | (1) |
| 스레드를 넘는다 | **`Arc`** | (3) — `Rc` 는 E0277 |
| 양방향 링크(부모 포인터·관찰자) | **소유하는 쪽 `Rc`, 거꾸로 `Weak`** | (2)의 격자 |
| 여럿이 **같은 값을 고친다** | **`Rc<RefCell<T>>`** / 스레드면 `Arc<Mutex<T>>` | (4) · [42번](../42-refcell-cell-interior-mutability/) |
| 각자 사본을 고친다 | **`Rc::make_mut`** | (4) |
| 그래프가 크고 순환이 많다 | ★ **인덱스(`Vec` + `usize`)** — [11번 주제](../11-borrow-checker-rejections/)의 열쇠 5 | `Weak` 를 빠뜨리면 조용히 샌다 |

## 핵심 문장

- ★★★ **`Rc` 는 한 소유자 규칙을 런타임 카운트로 완화한다 — 값은 마지막 강한 참조가 사라지는 줄에서 해제된다.**
- ★★★ **`Rc` 끼리의 순환은 `drop` 이 0 줄이다. Rust 에는 순환 수집기가 없다 — `Weak` 로 끊는 것은 사람의 몫이다.**
- ★★ **어느 쪽을 `Weak` 로 둘지는 「누가 누구를 살려 둬야 하나」로 고른다** — 트리는 부모 → 자식 `Rc`, 자식 → 부모 `Weak`.
- ★★ **`Rc` 는 스레드를 못 넘는다(E0277) — `Arc` 는 카운트만 원자적으로 바꿀 뿐 안의 값은 책임지지 않는다.**
- ★ **`Weak::upgrade` 는 강한 참조를 잠깐 하나 늘리고, 값이 없으면 `None` 이다.**

## 관련 자료

- [**40번 주제**](../40-box-recursive-types-and-dyn/) — `Rc` 로 꼬리를 나눈 리스트 · `*r` 의 E0507 · `try_unwrap`. **그쪽은 `Box` 와의 갈림, 여기는 카운트와 순환.**
- [**42번 주제**](../42-refcell-cell-interior-mutability/) — `Rc<RefCell<T>>`. (2)·(4)의 `RefCell` 이 거기서 본체가 된다.
- [**43번 주제**](../43-deref-coercion-and-smart-pointers/) — `&Rc<String>` 이 `&str` 자리에 들어가는 이유.
- [**44번 주제**](../44-drop-mem-drop-replace-and-take/) — `mem::forget`(안전한 누수의 다른 길).
- [**30번 주제**](../30-operator-overloading-std-ops-index-and-deref/) (9) — `strong_count` 가 연관 함수인 이유.
- 목록의 **50번 주제**(`Send`/`Sync`) · **52번 주제**(`Arc<Mutex<T>>`) — 스레드 쪽 정본.
- C++ 갈래 [`27-shared-ptr-and-reference-counting`](../../../cpp/syntax/27-shared-ptr-and-reference-counting/2-summary.md) · [`28-weak-ptr-and-reference-cycles`](../../../cpp/syntax/28-weak-ptr-and-reference-cycles/2-summary.md) — **제어 블록·원자 명령·ASan 누수 리포트는 거기**, 여기는 Rust 의 판단.
- Python 갈래 [`01-object-and-name-binding`](../../../python/syntax/01-object-and-name-binding/2-summary.md) — `sys.getrefcount` 와 순환 수집기의 일반.

## 용어 풀이

- **`Rc<T>`** — 단일 스레드 참조 카운팅 포인터. `clone` 이 카운트를 올린다.
- **`Arc<T>`** — 카운트를 **원자적으로** 갱신하는 `Rc`. 스레드를 넘을 수 있다.
- **`Weak<T>`** — 값을 살려 두지 않는 참조. `upgrade` 로 `Option<Rc<T>>` 를 얻는다.
- **강한 카운트 / 약한 카운트** — 값을 살려 두는 참조 수 / 안 살려 두는 참조 수.
- **순환 참조(reference cycle)** — 강한 참조가 고리를 이뤄 카운트가 0 이 안 되는 것.
- **clone-on-write** — 공유 중일 때만 복사하고 고치는 전략. `Rc::make_mut`.
- **`Send`** — 그 값을 다른 스레드로 **옮겨도** 되는가를 나타내는 자동 트레이트.

## 더 들어가면

- `Rc::new_cyclic` — 만드는 도중에 자기를 가리키는 `Weak` 를 받는 생성자(자기 참조 노드). **이 문서는 던지지 않았다.**
- `Weak` 가 살려 두는 **할당**이 언제 반납되는지 — std 는 「값은 안 살리고 할당은 살린다」고만 적는다. 바이트 수준의 확인은 **메모리 도구가 있는 판**에서 할 일이다(C++ 27편 (6)이 `shared_ptr` 쪽을 쟀다).
