# rust/syntax/41 — `Rc`/`Arc` 공유 소유권 · `Weak` 와 순환 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서
> **`rustc --edition 2021`** 로(Python 대비는 `Python 3.12.3`) 실제로 돌려 받은 것이다.\
> ★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
> ★★ 블록 첫 줄 `===== 소스: <파일> =====` 아래가 **돌린 소스 전문**이고, **진단의 줄 번호는 그 파일 기준**이다.\
> ★★ **외부 크레이트를 하나도 쓰지 않았다.** **시간도 주소도 싣지 않았다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ `drop value` 는 `[6]` 과 `[7]` 사이 — `upgrade` 는 `true` 다음 `false`, 그리고 `[7]` 의 `weak 0`

**출력**

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

**왜 그런가**

- ★★ `Rc::clone` 은 **강한 +1**, `Weak::clone` 은 **약한 +1** — 값은 복사되지 않는다(`[2]`·`[3]`).
- ★★ **`upgrade` 가 준 `Rc` 를 쥐는 동안 강한 3**(`[4]`) — `upgrade` 도 명의자가 되는 것이다. 블록 끝에서 버려져 2(`[5]`).
- ★★★ **`drop(a)` 로는 안 죽고 `drop(b)` 에서 죽는다** — 마지막 강한 참조가 사라지는 줄이 해제 줄이다. 그 뒤 `upgrade` 는 **`None`**.
- ★★ **`[7]` `weak 0`** — `w`·`w2` 가 살아 있는데도 0. std `Weak::weak_count`: 「If no strong pointers remain, this will return zero.」

### 2. ★★★ `drop` 줄 0 줄 · `[2]` 는 1 · 1 — 컴파일러는 아무 말도 안 한다

**출력**

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

**왜 그런가**

- ★★★ **변수 둘이 사라져도 서로가 서로를 한 번씩 쥐고 있어** 강한 카운트가 1 에서 멈춘다. **`main` 이 끝나도 `drop` 줄이 없다.**
- ★★ **컴파일 `exit 0` · 경고 0 줄**(블록의 첫 배너). std `rc` 모듈 문서: 「A cycle between `Rc` pointers will never be deallocated.」
- ★ 탐침이 `Weak` 라서 카운트를 **값을 살려 두지 않고** 읽었다 — 탐침이 `Rc` 였다면 탐침 자체가 명의자가 된다.

### 3. ★★★ `drop parent` → `drop child` — 자식의 부모 링크는 강한 수에 안 든다

**출력**

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

**왜 그런가**

- ★★ **`[1]` parent strong 1** — 변수 `parent` 하나뿐이다. 자식이 쥔 것은 `Weak` 라 강한 수에 안 든다. child strong 2 = 변수 `child` + 부모가 쥔 `Rc`.
- ★★★ **순서** — 지역 변수는 선언 역순으로 사라지므로(09번 (6)) `child` 변수가 먼저 가지만 **부모가 쥐고 있어 1 로 남는다.** 다음에 `parent` 변수가 가면 부모가 **0 → `drop parent`**, 그 필드(`Rc<Child>`)가 풀리며 자식이 **0 → `drop child`**.
- ★ `[2]` 0 · 0 — 둘 다 해제됐다.

### 4. ★★ `1 / 6` — 그리고 셋째 칸이 「누가 누구를 살려 두나」를 가른다

**출력**

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

**왜 그런가**

- ★★★ **`drop` 줄이 없는 칸은 `Rc`·`Rc` 하나뿐**(`1 / 6`) — 한쪽이라도 `Weak` 면 고리가 닫히지 않는다.
- ★★★ **셋째 칸** — 부모 → 자식이 `Rc` 인 세 칸은 `drop(c)` 뒤에도 자식이 **1** 로 산다(부모가 살려 둔다). `Weak` 인 세 칸은 **0** — 변수를 버리는 순간 자식이 죽는다. 그래서 그 세 칸의 넷째 칸은 **1**(스코프 끝에는 부모만 남아 있었다).
- ★★ **판단** — 트리는 부모가 자식을 소유하므로 **부모 → 자식 `Rc` · 자식 → 부모 `Weak`**. 넷째 칸만 보면 다섯 칸이 같아 보여 「아무 쪽이나 끊으면 된다」로 읽힌다 — **수명이 다르다.**

### 5. ★★ E0277 — `Rc<String>` 은 `Send` 가 아니다 · `Arc` 로 바꾸면 `2` → `1`

**출력**

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

**왜 그런가**

- ★★★ **E0277 — `` `Rc<String>` cannot be sent between threads safely ``**, `= help:` 「the trait `Send` is not implemented for `Rc<String>`」. `thread::spawn` 의 `F: Send` 경계에서 걸렸다(`note: required by a bound in spawn`).
- ★★ std: `Rc` 는 **비원자 카운트**라 `Send` 를 구현하지 않고, **컴파일러가 컴파일 시점에 검사한다.**
- ★★ `Arc` 판 — `spawn` 전 **2**(`a` + 클로저로 옮긴 `b`), `join` 뒤 **1**(스레드가 끝나며 `b` 가 해제됐다).
- ★ 같은 E0277 을 [32번 주제](../32-impl-trait-argument-return-position-and-2024-capture/) (3)과 C++ 갈래 [27편](../../../cpp/syntax/27-shared-ptr-and-reference-counting/2-summary.md) (8)이 먼저 보였다.

### 6. ★★ 주인이 둘이면 복제한다 — `b` 는 옛 값 `v1+x`, 카운트 1 · 1

**출력**

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

**왜 그런가**

- ★★ `[1]` 주인 하나 — **제자리**(`same allocation true`).
- ★★★ `[2]` 주인 둘 — **안의 `String` 을 새 할당으로 복제한 뒤** 고쳤다. `a` 는 새 값, **`b` 는 옛 값**, `ptr_eq false`, 카운트가 **1 · 1 로 갈라졌다.** std: clone-on-write.
- ★ `[3]` 공유 중 `get_mut` 은 `None`, `[4]` 혼자가 되면 `Some`.

### 7. ★★ `del` 로는 안 불리고 `gc.collect()` 가 부른다 — Rust 에는 순환 수집기가 없다

**출력**

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

- ★★★ **`[1]` 뒤에 `del` 줄이 없다** — 참조 카운트만으로는 Rust 의 2번과 같다.
- ★★★ **`gc.collect()` 가 두 객체를 회수**하며 `__del__` 이 불렸다(반환값 2 — CPython 판의 세부).
- ★★★ **Rust 에 없는 것은 그 추적 수집기다.** `Rc ↔ Rc` 는 `main` 끝까지 `drop` 0 줄이다 — 끊는 것은 `Weak` 를 쓰는 사람의 몫이다.

### 8. ★★★ 누수는 안전하다 — 소멸자 실행은 Rust 의 안전성 보장에 들어 있지 않다

- ★★★ std `mem::forget` 의 §Safety: 「`forget` 은 `unsafe` 가 아니다. **Rust 의 안전성 보장에는 소멸자가 반드시 실행된다는 보장이 없기 때문이다.** 예를 들어 **`Rc` 로 참조 순환을 만들거나** `process::exit` 로 소멸자 없이 끝낼 수 있다」.
- ★★ 즉 순환 누수는 **정의되지 않은 동작이 아니라 「자원이 안 돌아오는 것」이고**, 컴파일러가 막는 대상(메모리 안전 위반)이 아니다. 그래서 `exit 0` 이다.
- ★ 같은 이유로 `mem::forget` 도 안전 함수다 — [44번 주제](../44-drop-mem-drop-replace-and-take/)에서 로그로 보였다.

### 9. ★★ `Drop` 로그 0 줄과 카운트 1 — 남은 바이트는 말해 주지 않는다

- ★★★ **근거 둘** — ① **`Drop` 로그가 0 줄**(해제 코드가 한 번도 안 돌았다) ② **스코프 뒤 강한 카운트 1**(누가 아직 쥐고 있다 — `Weak` 탐침으로 읽었다).
- ★★ **제5의 상태** — 「샜나」를 메모리 도구 대신 **이 두 창으로 바꿔 물은 것**이다. 도구가 없다는 것은 서머리 머리말 블록(`rustup component list --installed` 에 `miri` 없음 · `cargo miri --version exit=1` · `command -v valgrind exit=1`)이 근거다.
- ★★ **못 보는 것** — **몇 바이트가 남았나**, `Weak` 가 붙든 **할당**이 언제 반납되나, `Drop` 을 안 단 타입의 누수. 그 자리는 메모리 도구가 있는 판의 일이다(C++ 27편 (6)이 `shared_ptr` 쪽을 ASan·계수기로 쟀다).

### 10. ★★ 「원자적으로 센다」까지가 사실이다 — 「느리다」는 측정이 필요하다 · `Arc<RefCell<T>>` 는 여전히 막힌다

- ★★ std `rc` 문서: `Rc` 는 **비원자** 카운트, 스레드가 필요하면 **원자** 카운트의 `Arc`. **이것이 적을 수 있는 차이의 전부**다 — 이 문서는 시간을 재지 않았다.
- ★★ 「느리다」를 쓰려면 **같은 작업을 두 판으로 여러 번 잰 측정**(판 격자 · 흔들림 폭)이 있어야 한다. 원자 명령 수를 **센** 것은 C++ 27편 (7)이고 Rust 쪽은 세지 않았다.
- ★★★ **여전히 막히는 경우** — `Arc<T>` 가 `Send` 이려면 **`T: Send + Sync`**(std 의 `impl Send for Arc<T, A>` 경계). `T = RefCell<i32>` 면 E0277 — [42번 주제](../42-refcell-cell-interior-mutability/)의 `r42_sync`.

### 11. ★ 복제 · `None` · `Err` · 같은 값 — 「모두가 같은 값」은 `Rc<RefCell<T>>`

| 길 | 공유 중일 때 | 혼자일 때 |
|---|---|---|
| `Rc::make_mut` | **복제 후 고침** — 다른 주인은 옛 값(6번) | 제자리 |
| `Rc::get_mut` | `None` | `Some(&mut T)` |
| `Rc::try_unwrap` | `Err(rc)` | `Ok(T)`(40번 (5)) |
| `Rc<RefCell<T>>` | **모두가 같은 값을 고친다** — 대신 빌림 검사가 런타임으로 간다 | 〃 |

- ★★ 「모두가 같은 값을 고친다」 → **`Rc<RefCell<T>>`**(42번의 `r42_rc_refcell`: `strong 3 · ["from a", "from b"]`). 스레드를 넘으면 `Arc<Mutex<T>>`(목록의 **52번 주제**).

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서·서머리의 **모든 블록** | `capture.sh` — 블록마다 명령을 배너에 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` 기본 규칙 넷 · **고칠 것 0** |
| ★★★ **카운트 로그** | `r41_count` | 1 | `[6]`·`[7]` 사이 `drop value` · `[7]` `weak 0` |
| ★★★ **순환 재현** | `r41_cycle_rc` · `r41_cycle_weak` | 2 | `drop` **0 줄 · 1 1** 대 **2 줄 · 0 0** |
| ★★ **방향 격자** | `r41_cycle_grid.sh` — 여섯 소스를 만들어 던진다(탭 구분 · 칸 수 검사) | 6 컴파일 · 6 실행 | **`1 / 6`** |
| 스레드 | `r41_send` · `r41_send_arc` | 2 | **E0277** · `2 → 1` |
| 고치기 | `r41_make_mut` | 1 | 복제 · `None`/`Some` |
| Python 대비 | `r41_py_cycle.py` | 1 | `gc.collect()` 2 · `del` 두 줄 |
| 도구 확인 | `rustup component list --installed` · `cargo miri --version` · `command -v valgrind` | 3 | `miri` 없음 · 둘 다 `exit=1` — **누수량은 못 잰 것** |
| **안 던진 것** — 속도 · `Rc::new_cyclic` · `Arc` 의 `make_mut` · 메모리 바이트 | — | 0 | ★ 「안 던졌다」로 표시했다 |

**구현 의존 항목**(버전·환경이 바뀌면 **다시 찍어야 하는** 것).

| 항목 | 왜 |
|---|---|
| E0277 의 문구·`help:`·`note:` 모양 | ★ rustc 판에 매인다 |
| `note: required by a bound in spawn` 의 `/rustc/<해시>/…:725:1` | ★ 툴체인 해시와 std 소스 줄 번호 |
| `gc.collect()` 의 반환값 | ★ CPython 판의 세부 |

★ **다시 찍는 법** — `capture.sh <새 디렉토리>` 를 그대로 돌리고 `normalize-shaky.py <원본> <새 디렉토리>` 로 견준다.
