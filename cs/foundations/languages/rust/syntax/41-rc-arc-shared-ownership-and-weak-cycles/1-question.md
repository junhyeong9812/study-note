# rust/syntax/41 — `Rc`/`Arc` 공유 소유권 · `Weak` 와 순환 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 던지는 법 — `rustc --edition 2021 <파일>.rs`. 격자는 `bash <파일>.sh`, Python 은 `python3 <파일>.py`. **외부 크레이트를 하나도 쓰지 않는다.**
> ★★★ **`Rc` 를 보면 먼저 물어라** — 「**지금 강한 참조를 쥔 것이 누구누구인가**」와 「**그 고리가 닫혀 있나**」.
> ★ **문항 11개 중 코드가 붙은 예측형은 6개**다. 소스 펜스는 캡처가 실파일에서 찍었다(`check-source-fences.py` 대조).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 한 줄마다 두 수 (예측)

```rust
// r41_count.rs
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
```

- `[1]`\~`[8]` 각 줄의 `strong` · `weak` 는? `drop value` 는 **어느 두 줄 사이**에 찍히나?
- 두 번의 `upgrade is_some` 은 각각 무엇인가?

### 2. ★★★ 서로를 쥔 두 노드 (예측)

```rust
// r41_cycle_rc.rs
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
```

- 출력 전체를 적어라. `drop` 으로 시작하는 줄은 **몇 줄**이고 어디에 나오나? `[2]` 의 두 수는?
- 컴파일러는 이 코드에 대해 무엇이라고 말하나?

### 3. ★★★ 한쪽 링크만 바꾼 판 (예측)

```rust
// r41_cycle_weak.rs
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
```

- 출력 전체를 적어라. `drop` 줄의 **순서**와 그 이유는? `[1]` 에서 `parent strong` 이 2 가 아닌 이유는?

### 4. ★★ 여섯 가지 링크 조합 (예측)

```bash
# r41_cycle_grid.sh
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
```

- 여섯 행의 셋째 · 넷째 · 다섯째 칸을 채워라. 마지막 줄의 `N / 6` 은?
- ★ 넷째 칸만 보면 같아 보이는 행들을 셋째 칸이 어떻게 가르나?

### 5. ★★ 스레드로 넘긴 공유 포인터 (예측)

```rust
// r41_send.rs
use std::rc::Rc;
use std::thread;

fn main() {
    let a = Rc::new(String::from("shared"));
    let b = Rc::clone(&a);
    let h = thread::spawn(move || b.len());
    println!("{}", h.join().unwrap());
}
```

- 컴파일되는가? 에러라면 번호와 `= help:` 의 요지는?
- `Rc` 를 `Arc` 로 바꾸고 `spawn` 전·`join` 뒤에 `Arc::strong_count` 를 찍으면 각각 몇인가?

### 6. ★★ 고치기 전에 주인을 센다 (예측)

```rust
// r41_make_mut.rs
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
```

- 네 줄의 출력은? `[2]` 에서 `b` 는 무엇을 보나 — 그리고 두 `strong` 은?

### 7. ★★ Python 은 같은 고리를 어떻게 다루나 (연결)

- Python 에서 두 객체가 서로를 속성으로 쥐게 하고, 자동 수집을 끈 채(`gc.disable()`) 이름을 `del` 하면 `__del__` 이 불리나? 그다음 `gc.collect()` 를 부르면? 그 결과를 2번과 나란히 놓으면 Rust 에 **없는 것**은 무엇인가?

### 8. ★★★ 새는데도 컴파일러가 막지 않는 이유 (왜)

- 2번은 `exit 0` 이다. 왜 Rust 는 순환 누수를 **컴파일 에러로 만들지 않나**? std 의 어느 문서가 그 근거를 적나?

### 9. ★★ 메모리 도구 없이 「샜다」를 말하는 법 (경계)

- 이 머신에는 Miri 도 valgrind 도 없다. 그런데도 2번이 「해제되지 않았다」고 말할 수 있는 근거 둘은? 그 두 창이 **말해 주지 않는 것**은 무엇인가?

### 10. ★★ `Arc` 의 대가를 적는 법 (경계)

- `Arc` 가 `Rc` 와 다른 점을 std 는 무엇이라고 적나? 「`Arc` 는 느리다」라고 쓰려면 무엇이 필요한가? 그리고 `Arc` 로 바꿔도 **여전히 막히는** 경우는?

### 11. ★ 네 가지 「고치는」 길 (연결)

- `Rc::make_mut` · `Rc::get_mut` · `Rc::try_unwrap`([40번 주제](../40-box-recursive-types-and-dyn/) (5)) · `Rc<RefCell<T>>` 는 공유 중일 때 각각 무엇을 하나? 「모두가 같은 값을 고친다」가 필요하면 어느 것인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
