# rust/syntax/36 — `Iterator`와 어댑터·게으름·`collect` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [std — `std::iter` 모듈 문서](https://doc.rust-lang.org/std/iter/index.html)(Laziness · Infinity · for 의 탈당 · Iterating by reference) ·
> [std — `Iterator`](https://doc.rust-lang.org/std/iter/trait.Iterator.html) ·
> [std — `Result` 의 `FromIterator`](https://doc.rust-lang.org/std/result/enum.Result.html) · [std — `Option` 의 `FromIterator`](https://doc.rust-lang.org/std/option/enum.Option.html) ·
> [Reference — `for` 의 탈당](https://doc.rust-lang.org/reference/expressions/loop-expr.html#iterator-loops).
> ★ 위 문서는 **이 머신의 `rust-docs`(1.92.0) 로컬 사본**을 열어 읽었다.
> **실행 검증** — 이 문서의 모든 출력·에러는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서
> **`rustc --edition 2021 <파일>.rs`** 로 돌려 받은 것이다(「더 들어가면」의 한 쌍만 2018). 파이썬 대비는 `Python 3.12.3`.\
> ★★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다. 소스 펜스도 캡처가 찍었다.\
> ★★ **외부 크레이트를 하나도 쓰지 않았다**(네트워크 없음).
> ★★★ **이 문서는 속도를 한 번도 재지 않았다.** 「이터레이터는 제로 코스트다」는 **이 문서의 주장이 아니다** — 센 것은 **콜백 호출 횟수와 순서**뿐이다.
> 제로 코스트 논증의 정본은 [`언어-특성/README.md`](../../언어-특성/README.md) §6 이다(그 절이 Book 의 벤치마크를 인용한다).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

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
===== clang++ --version | head -1 =====
Ubuntu clang version 18.1.3 (1ubuntu1)
(exit 0)
===== python3 --version =====
Python 3.12.3
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| 안 흔들린다 | 호출 로그의 **횟수와 순서**(`map calls 4 · filter calls 4`, `map(1) filter(10) …`) | ★ 단일 스레드 · 결정적 입력이다. **이 주제의 본체** |
| ★ **흔들릴 수 있어 피했다** | `HashSet` 의 **순회 순서** | Rust `HashSet` 은 실행마다 시드가 바뀐다 — 그래서 **`len` 만** 찍고 정렬된 판은 **`BTreeSet`** 으로 따로 찍었다(규칙 11) |
| 안 흔들린다 | `type_name_of_val` 의 문자열 | 같은 판에서 고정. 형식은 보장되지 않는다(std) |
| 안 흔들린다 | 에러·경고 번호·제목·`파일:줄:칸`·종료 코드 | 같은 rustc 판에서 고정이다 |

★ 정규화 규칙은 **기본 넷**만 썼고 **하나도 걸리지 않았다**(제출 전 재대조).

## 한눈에 — 쉽게 말하면

**어댑터 사슬은 「조립만 해 둔 컨베이어 벨트」다. `map`·`filter`·`take` 를 붙이는 것은 벨트에 기계를 다는 것일 뿐이고, 벨트는 끝에서 누가 물건을 달라고 할 때 비로소 한 칸 움직인다.
그리고 물건은 한 개씩 기계 전부를 차례로 통과한다 — 기계마다 전부를 한꺼번에 처리하지 않는다.**

| 비유 | 실체 |
|---|---|
| 「**기계를 달기만 한 벨트**」 | ★★★ **어댑터(`map`·`filter`·`take`)는 게으르다** — 만든 직후 **로그 0 줄**((2)) |
| 「**끝에서 당기는 손**」 | ★★ **소비자(`collect`·`sum`·`count`·`for`)** — `next` 를 부른다((2)·(5)) |
| 「**물건 하나가 기계 전부를 지나간다**」 | ★★★ **세로로 돈다** — `map(1) filter(10) map(2) filter(20) …`((2)) |
| 「**필요한 만큼만 당긴다**」 | ★★ **`take(2)`** — 두 개를 채우면 **원본을 더 안 당긴다** — `map calls 4`((2)) |
| 「**달기만 하고 안 돌린 벨트에 붙는 경고 딱지**」 | ★ **`#[must_use]`** — 「iterators are lazy and do nothing unless consumed」((3)) |
| 「**받을 상자가 결과를 정한다**」 | ★★ **`collect` 는 타입이 주도한다** — 같은 사슬이 `Vec`·`HashSet`·`String`·`Result<Vec>`((4)) |
| 「**불량품이 나오면 벨트를 세운다**」 | ★★★ **`Result` 로 모으면 첫 `Err` 에서 멈춘다** — 뒤는 **안 불린다**((4)) |

- ★★★ **판정은 한 줄이다 — 「어댑터는 아무것도 안 한다. 소비자가 `next` 를 부를 때 한 원소가 사슬 전체를 지나간다.」**
  그래서 **호출 횟수는 소비자가 몇 개를 원하느냐**로 정해지고, **순서는 원소 단위로 번갈아** 간다.
- ★★ **JS 이터레이터 헬퍼와 한 글자도 같은 로그가 나왔다** — JS 갈래의 [**21번**](../../../js/syntax/21-iterator-helpers/)이 같은 파이프라인으로 **배열판 `map 10 · filter 10` / 헬퍼판 `map 4 · filter 4`** 를 냈고,
  Rust 도 **Vec 을 단계마다 모으는 판 10 · 10 / 어댑터 사슬 판 4 · 4**, 순서까지 같다((2)).

```text
   ★ 평가 순서 — 같은 결과 [20, 40] 을 얻는 두 벌 ((2)의 블록 그대로)

   단계마다 Vec   map(1) map(2) … map(10) │ filter(10) filter(20) … filter(100) │ take
                 └──── 1단계를 전부 ─────┘ └──────── 2단계를 전부 ───────────┘      ← 가로로

   어댑터 사슬    (만든 순간: 0)   collect() ─▶ map(1) filter(10) map(2) filter(20) │ map(3) filter(30) map(4) filter(40) │ (끝)
                                          └──────── next#1 이 한 일 ────────┘ └──────── next#2 가 한 일 ─────────┘  next#3: (none)
                                                                                                                      ← 세로로

   ★ JS 21번의 표 — 배열판 map 10 · filter 10 / 헬퍼판 map 4 · filter 4 — 와 같은 수, 같은 순서
```

> **이터레이터(iterator)** — `fn next(&mut self) -> Option<Self::Item>` 하나를 구현한 값. `None` 이 나오면 끝이다.\
> 예: `(1..=3).next()` 는 `Some(1)` 이고 세 번 더 부르면 `None` 이 된다.

> **어댑터(adapter)** — 이터레이터를 받아 **다른 이터레이터**를 돌려주는 메서드(std 의 말 — 「iterator adapters」). `map`·`filter`·`take`·`zip`.\
> 예: `v.iter().map(f)` 는 `Map<Iter<…>, F>` 라는 **값**이고, 아직 `f` 를 한 번도 안 불렀다.

> **게으름(laziness)** — 값이 **필요해질 때** 계산하는 것. std 문서: 「**이터레이터(와 어댑터)는 게으르다 … `next` 를 부르기 전에는 아무 일도 안 일어난다**」.\
> 예: `v.iter().map(|x| println!("{x}"));` 는 아무것도 안 찍는다.

## 이 주제가 답하려는 질문

1. ★★★ **어댑터 사슬은 언제, 몇 번, 어떤 순서로 클로저를 부르나** — 그리고 **Vec 을 단계마다 모으는 판과 무엇이 다른가**((2)).
2. ★★ **`collect` 는 무엇을 만드나** — 같은 사슬이 **받는 타입**에 따라 무엇이 되고, `Result`/`Option` 으로 모으면 **어디서 멈추나**((4)).
3. ★ **`next` 하나만 구현하면 무엇이 생기나** — 그리고 `iter`/`iter_mut`/`into_iter` 는 **무엇을 내놓나**((1)·(6)).

★ **선행** — [**34번 주제**](../34-closures-fn-fnmut-fnonce-and-move/)의 **클로저**. 어댑터가 받는 클로저는 **`FnMut`** 이다(여러 번 부르고, 상태를 고칠 수 있게) — 그래서 (4)의 `calls.push(…)` 가 된다.
[**25번 주제**](../25-traits-definition-impl-default-methods-and-associated-types/)의 **기본 메서드**와 **연관 타입**이 `Iterator` 의 뼈대다((1)).
★ **정본 경계** — **`IntoIterator` 세 형태와 `for` 의 소유권**은 [목록의 **37번 주제**](../37-intoiterator-three-forms-iter-iter-mut-into-iter/)가 정본이다. 여기서는 (6)에서 **타입 셋과 E0382 한 칸**만 찍는다.

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ① 호출 로그다

★★★ **본체 창 — ① 클로저 안에 로그를 심어 「언제 · 몇 번 · 어떤 순서로」를 찍는다.** 값으로는 원리상 못 가른다 — 두 판의 결과가 **둘 다 `[20, 40]`** 이다.

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ① ★★★ **콜백 호출 로그**(`RefCell<Vec<String>>`) | 사슬을 만든 직후 **몇 줄**인가, 소비 뒤 **몇 번·어떤 순서**인가, `next` 한 번이 **무슨 일을 했나**((2)) | ★ **본체** |
| ② **컴파일러 경고** `#[must_use]`·`map_unit_fn` | 소비하지 않은 사슬을 **컴파일러가 잡는가**((3)) | 쓴다 |
| ③ **`collect` 의 받는 타입 격자** | 같은 사슬이 타입마다 **무엇이 되나**((4)) | 쓴다 |
| ④ **`Result`/`Option` 수집 + 호출 로그** | 첫 `Err`/`None` **뒤가 불렸나**((4)) | 쓴다 — ①을 다시 쓴다 |
| ⑤ **`type_name_of_val`** | `iter`/`iter_mut`/`into_iter` 가 **무엇을 내놓나**((6)) | 쓴다 |
| ⑥ **파이썬 제너레이터 대비** | 다른 언어의 게으른 파이프라인도 **세로로 도나**((2)) | 대비로 쓴다 |
| 실행 시간 · 기계어 | 「이터레이터는 손으로 짠 루프만큼 빠르다」 | ★ **부적용 — 재지 않는다.** 정본은 `언어-특성/` §6 |

★ **「같은 질문을 다른 창으로」(제5의 상태)** — 「사슬이 아무 일도 안 했나」를 **② 컴파일러**에 물으면 **경고**로 답하지만,
**`help:` 대로 `let _ =` 를 붙이면 경고가 사라진다** — 그런데 ① 로그로 물으면 **여전히 아무 일도 안 했다**((3)). **경고가 없다는 것은 「돌았다」가 아니다.**

### (1) `next` 하나만 구현하면 — 어댑터가 전부 생긴다

**언제 쓰나** — 내 타입을 `for`·`map`·`sum` 에 쓰고 싶을 때.

```rust
// r36_next_only.rs
// next 하나만 구현한 이터레이터에 어댑터를 붙여 본다
struct Countdown(u32);

impl Iterator for Countdown {
    type Item = u32;
    fn next(&mut self) -> Option<u32> {
        if self.0 == 0 {
            None
        } else {
            self.0 -= 1;
            Some(self.0 + 1)
        }
    }
}

fn main() {
    let v: Vec<u32> = Countdown(5).collect();
    println!("{:?}", v);
    let s: u32 = Countdown(5).filter(|x| x % 2 == 1).map(|x| x * 10).sum();
    println!("{}", s);
    let z: Vec<(u32, char)> = Countdown(3).zip("abc".chars()).collect();
    println!("{:?}", z);
    println!("{:?} {} {:?}", Countdown(4).max(), Countdown(4).count(), Countdown(4).nth(1));
    let mut c = Countdown(2);
    println!("{:?} {:?} {:?}", c.next(), c.next(), c.next());
}
```

```text
===== rustc --edition 2021 r36_next_only.rs =====
(exit 0)
===== ./r36_next_only =====
[5, 4, 3, 2, 1]
90
[(3, 'a'), (2, 'b'), (1, 'c')]
Some(4) 4 Some(3)
Some(2) Some(1) None
(exit 0)
```

- ★★ **구현한 것은 `type Item` 과 `fn next` 둘뿐**인데 `collect`·`filter`·`map`·`sum`·`zip`·`max`·`count`·`nth` 가 **전부 됐다.**
  이것들은 `Iterator` 트레이트의 **기본 메서드**다 — [**25번 주제**](../25-traits-definition-impl-default-methods-and-associated-types/)의 기본 메서드가 가장 크게 쓰인 자리다(로컬 std 문서의 `Iterator` 쪽에 **필수 메서드는 `next` 하나, 제공 메서드 id 는 75개**다 — 불안정 메서드 포함).
- ★ **마지막 줄 `Some(2) Some(1) None`** — `next` 를 직접 부르면 **`Option` 으로 한 칸씩** 나온다. `None` 이 곧 끝이다. `for` 도 이 `next` 를 `None` 까지 부르는 것이다(std 의 탈당 예).

### (2) ★★★ 게으름 — 호출 로그로 본다

**언제 쓰나** — 사슬이 **언제 일하는지**, **얼마나 일하는지** 알아야 할 때(비싼 클로저, 부수 효과, 무한 원본).

```rust
// r36_lazy.rs
// 같은 파이프라인을 두 벌로 — 단계마다 Vec 으로 모으는 판과 어댑터 사슬 판.
// 원본은 1..=10. map 은 x*10, filter 는 20 의 배수만, 앞의 두 개만 취한다.
use std::cell::RefCell;

fn main() {
    let log = RefCell::new(Vec::<String>::new());
    let src: Vec<i32> = (1..=10).collect();
    let map_fn = |x: &i32| {
        log.borrow_mut().push(format!("map({})", x));
        x * 10
    };
    let keep = |x: &i32| {
        log.borrow_mut().push(format!("filter({})", x));
        x % 20 == 0
    };
    let n = |p: &str| log.borrow().iter().filter(|m| m.starts_with(p)).count();

    println!("[1] Vec per stage: map -> collect -> filter -> collect -> take(2)");
    let a1: Vec<i32> = src.iter().map(map_fn).collect();
    let a2: Vec<i32> = a1.into_iter().filter(keep).collect();
    let a: Vec<i32> = a2.into_iter().take(2).collect();
    println!("    result {:?}", a);
    println!("    map calls {} · filter calls {}", n("map("), n("filter("));
    println!("    order  {}", log.borrow().join(" "));

    println!();
    println!("[2] adapter chain: iter().map(f).filter(g).take(2)");
    log.borrow_mut().clear();
    let pipe = src.iter().map(map_fn).filter(keep).take(2);
    println!("    after building the pipeline:  log entries {}", log.borrow().len());
    let h: Vec<i32> = pipe.collect();
    println!("    after collect():  result {:?}", h);
    println!("    map calls {} · filter calls {}", n("map("), n("filter("));
    println!("    order  {}", log.borrow().join(" "));

    println!();
    println!("[3] the same chain, one next() at a time");
    log.borrow_mut().clear();
    let mut step = src.iter().map(map_fn).filter(keep).take(2);
    for i in 1..=3 {
        let before = log.borrow().len();
        let r = step.next();
        let ran = log.borrow()[before..].join(" ");
        println!("    next#{}  {:<10} callbacks run in this call: {}", i, format!("{:?}", r), if ran.is_empty() { "(none)".to_string() } else { ran });
    }
}
```

```text
===== rustc --edition 2021 r36_lazy.rs =====
(exit 0)
===== ./r36_lazy =====
[1] Vec per stage: map -> collect -> filter -> collect -> take(2)
    result [20, 40]
    map calls 10 · filter calls 10
    order  map(1) map(2) map(3) map(4) map(5) map(6) map(7) map(8) map(9) map(10) filter(10) filter(20) filter(30) filter(40) filter(50) filter(60) filter(70) filter(80) filter(90) filter(100)

[2] adapter chain: iter().map(f).filter(g).take(2)
    after building the pipeline:  log entries 0
    after collect():  result [20, 40]
    map calls 4 · filter calls 4
    order  map(1) filter(10) map(2) filter(20) map(3) filter(30) map(4) filter(40)

[3] the same chain, one next() at a time
    next#1  Some(20)   callbacks run in this call: map(1) filter(10) map(2) filter(20)
    next#2  Some(40)   callbacks run in this call: map(3) filter(30) map(4) filter(40)
    next#3  None       callbacks run in this call: (none)
(exit 0)
```

- ★★★ **`[1]` Vec 을 단계마다 모은 판은 `map calls 10 · filter calls 10`** — 로그가 **`map` 열 개 → `filter` 열 개**로 **단계별로 뭉쳐** 있다. `take(2)` 는 이미 다 계산된 것에서 앞 둘을 자를 뿐이다.
- ★★★ **`[2]` 어댑터 사슬은 만든 직후 `log entries 0`** — `map`·`filter`·`take` 를 **다 붙였는데 클로저가 한 번도 안 돌았다.**
  `collect()` 를 부르자 **`map calls 4 · filter calls 4`**, 순서는 **`map(1) filter(10) map(2) filter(20) …`** — **원소마다 사슬 전체를 지나간다**(세로).
- ★★★ **`[3]` `next()` 를 하나씩 부르면** — `next#1` 이 `map(1) filter(10) map(2) filter(20)` 을, `next#2` 가 `map(3) filter(30) map(4) filter(40)` 을 했고,
  **`next#3` 은 클로저를 하나도 안 부르고 `None`** 이다. `take(2)` 가 **두 개를 내준 뒤 원본을 더 안 당겼다** — 그래서 `map(5)` 가 영영 없다.
- ★ 결과는 두 판 다 **`[20, 40]`** — **같은 값을 다른 양의 일로 얻었다.** 값만 보면 둘을 못 가른다.

**JS 21번과 나란히.**

| | JS 배열 메서드 | JS 이터레이터 헬퍼 | Rust 단계마다 `Vec` | Rust 어댑터 사슬 |
|---|---|---|---|---|
| 만든 직후 로그 | — | **0** | — | **0** |
| `map` 호출 | 10 | **4** | 10 | **4** |
| `filter` 호출 | 10 | **4** | 10 | **4** |
| 순서 | 단계별(가로) | 원소별(세로) | 단계별(가로) | 원소별(세로) |
| `next#3` 이 한 일 | — | (none) | — | (none) |

- ★★ **네 칸의 수와 순서가 JS 21번 블록과 같다**(JS 쪽 수치는 그 편의 블록을 **인용**했다 — 이 문서는 브라우저를 다시 돌리지 않았다).
  **Rust 의 `Vec` 판이 JS 의 배열판**이고, **Rust 의 어댑터가 JS 의 헬퍼**다. ★ 다만 **JS 배열 메서드는 기본값이 가로**이고 **Rust 이터레이터는 기본값이 세로**다 — Rust 에서 가로로 돌리려면 `collect` 를 **일부러** 끼워야 한다.

**파이썬 제너레이터 식도.**

```python
# r36_gen.py
# 파이썬 — 같은 파이프라인을 제너레이터 식으로. 콜백이 언제 · 몇 번 불리나
from itertools import islice

log = []
def map_fn(x):
    log.append(f"map({x})")
    return x * 10
def keep(x):
    log.append(f"filter({x})")
    return x % 20 == 0

pipe = islice((y for y in (map_fn(x) for x in range(1, 11)) if keep(y)), 2)
print("after building the pipeline: log entries", len(log))
print("result", list(pipe))
print("order ", " ".join(log))
```

```text
===== python3 r36_gen.py =====
after building the pipeline: log entries 0
result [20, 40]
order  map(1) filter(10) map(2) filter(20) map(3) filter(30) map(4) filter(40)
(exit 0)
```

- ★ **파이썬도 만든 직후 0, 순서는 세로, 결과 `[20, 40]`.** 게으른 파이프라인은 **언어를 안 가리고** 같은 모양으로 돈다. 정본은 Python 갈래의 [**15번**](../../../python/syntax/15-generator-expressions-lazy-eval/)(제너레이터 식)·[**16번**](../../../python/syntax/16-iterator-protocol/)(이터레이터 프로토콜).

### (3) ★ 안 쓴 사슬 — `#[must_use]` 경고, 그리고 `help:` 의 함정

**언제 쓰나** — `map` 을 **부수 효과**(출력·기록)용으로 쓰려 할 때.

```rust
// r36_unused.rs
// 어댑터만 만들고 버린다
fn main() {
    let v = vec![1, 2, 3];
    v.iter().map(|x| println!("{}", x));
    println!("end");
}
```

```text
===== rustc --edition 2021 r36_unused.rs =====
warning: unused `Map` that must be used
 --> r36_unused.rs:4:5
  |
4 |     v.iter().map(|x| println!("{}", x));
  |     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  |
  = note: iterators are lazy and do nothing unless consumed
  = note: `#[warn(unused_must_use)]` (part of `#[warn(unused)]`) on by default
help: use `let _ = ...` to ignore the resulting value
  |
4 |     let _ = v.iter().map(|x| println!("{}", x));
  |     +++++++

warning: `Iterator::map` call that discard the iterator's values
 --> r36_unused.rs:4:14
  |
4 |     v.iter().map(|x| println!("{}", x));
  |              ^^^^---------------------^
  |              |   |
  |              |   this function returns `()`, which is likely not what you wanted
  |              |   called `Iterator::map` with callable that returns `()`
  |              after this call to map, the resulting iterator is `impl Iterator<Item = ()>`, which means the only information carried by the iterator is the number of items
  |
  = note: `Iterator::map`, like many of the methods on `Iterator`, gets executed lazily, meaning that its effects won't be visible until it is iterated
  = note: `#[warn(map_unit_fn)]` (part of `#[warn(unused)]`) on by default
help: you might have meant to use `Iterator::for_each`
  |
4 -     v.iter().map(|x| println!("{}", x));
4 +     v.iter().for_each(|x| println!("{}", x));
  |

warning: 2 warnings emitted

(exit 0)
===== ./r36_unused =====
end
(exit 0)
```

- ★★ **경고 둘, 실행 출력은 `end` 한 줄** — 1·2·3 이 **안 찍혔다.**
  첫 경고 「**unused `Map` that must be used**」의 `note:` 가 「**iterators are lazy and do nothing unless consumed**」 — std 문서의 Laziness 절이 인용한 바로 그 문장이다.
  둘째 경고 `map_unit_fn` 은 「`()` 를 돌려주는 클로저로 `map` 했다」를 따로 잡는다.
- ★ **`help:` 가 두 갈래다** — ① 「**use `let _ = ...` to ignore the resulting value**」 ② 「**you might have meant to use `Iterator::for_each`**」.

**첫 `help:` 대로 `let _ =` 를 붙이면.**

```rust
// r36_unused_let.rs
// 첫 help: 대로 let _ = 를 붙이면
fn main() {
    let v = vec![1, 2, 3];
    let _ = v.iter().map(|x| println!("{}", x));
    println!("end");
}
```

```text
===== rustc --edition 2021 r36_unused_let.rs =====
(exit 0)
===== ./r36_unused_let =====
end
(exit 0)
```

- ★★★ **경고가 전부 사라졌는데 여전히 `end` 한 줄뿐이다.** `let _ =` 는 「**결과를 버린다는 걸 안다**」는 표시일 뿐 **사슬을 돌리지 않는다.**
  **처방이 경고는 지웠지만 버그는 그대로 뒀다** — 이 자리의 뜻(부수 효과)에는 **틀린 처방**이다.

**둘째 `help:` 대로 `for_each` 로.**

```rust
// r36_unused_each.rs
// 둘째 help: 대로 for_each 로 바꾸면
fn main() {
    let v = vec![1, 2, 3];
    v.iter().for_each(|x| println!("{}", x));
    println!("end");
}
```

```text
===== rustc --edition 2021 r36_unused_each.rs =====
(exit 0)
===== ./r36_unused_each =====
1
2
3
end
(exit 0)
```

- ★ **`1 2 3` 이 찍혔다.** `for_each` 는 **소비자**다 — `next` 를 끝까지 부른다.

### (4) ★★ `collect` 는 받는 타입이 정한다 — 그리고 `Result` 는 멈춘다

**언제 쓰나** — 사슬 끝에서 **무엇으로 모을지** 고를 때. **실패할 수 있는 변환**을 한꺼번에 할 때.

```rust
// r36_collect.rs
// 같은 사슬을 서로 다른 타입으로 모은다
use std::collections::{BTreeSet, HashSet};

fn main() {
    let words = ["b", "a", "b", "c"];
    let v: Vec<&str> = words.iter().copied().collect();
    let hs: HashSet<&str> = words.iter().copied().collect();
    let bs: BTreeSet<&str> = words.iter().copied().collect();
    let s: String = words.iter().copied().collect();
    println!("Vec      {:?}", v);
    println!("HashSet  len {}", hs.len());
    println!("BTreeSet {:?}", bs);
    println!("String   {:?}", s);

    let nums = ["1", "2", "3"];
    let ok: Result<Vec<i32>, _> = nums.iter().map(|t| t.parse::<i32>()).collect();
    println!("Result   {:?}", ok);
    let some: Option<Vec<i32>> = nums.iter().map(|t| t.parse::<i32>().ok()).collect();
    println!("Option   {:?}", some);
    let each: Vec<Result<i32, _>> = ["1", "x"].iter().map(|t| t.parse::<i32>()).collect();
    println!("Vec<Result> {:?}", each);
}
```

```text
===== rustc --edition 2021 r36_collect.rs =====
(exit 0)
===== ./r36_collect =====
Vec      ["b", "a", "b", "c"]
HashSet  len 3
BTreeSet {"a", "b", "c"}
String   "babc"
Result   Ok([1, 2, 3])
Option   Some([1, 2, 3])
Vec<Result> [Ok(1), Err(ParseIntError { kind: InvalidDigit })]
(exit 0)
```

- ★★ **같은 `words.iter().copied()` 가 넷이 됐다** — `Vec` 은 **순서·중복 그대로**, `HashSet` 은 **중복을 지워 3개**(순서는 안 찍었다 — 흔들린다), `BTreeSet` 은 **정렬**, `String` 은 **이어 붙이기**(`"babc"`).
  **`collect` 는 한 메서드인데 결과는 받는 쪽의 `FromIterator` 구현이 정한다.**
- ★★ **`Result<Vec<i32>, _>` · `Option<Vec<i32>>`** — 원소마다 `Result`/`Option` 인 이터레이터를 **바깥이 하나인 값**으로 뒤집어 모은다(`Ok([1, 2, 3])` · `Some([1, 2, 3])`).
  같은 원소를 **`Vec<Result<…>>`** 로 모으면 **안 뒤집고** 원소마다 남는다(`[Ok(1), Err(…)]`).

**`Result` 로 모을 때 — 첫 `Err` 뒤가 불리나.**

```rust
// r36_result_stop.rs
// Result 로 모을 때 — 파싱 클로저가 몇 번 불리나
fn main() {
    let mut calls = Vec::new();
    let r: Result<Vec<i32>, std::num::ParseIntError> = ["1", "2", "x", "4", "y"]
        .iter()
        .map(|t| {
            calls.push(*t);
            t.parse::<i32>()
        })
        .collect();
    println!("{:?}", r);
    println!("parse called on {:?}", calls);

    let mut calls2 = Vec::new();
    let o: Option<Vec<i32>> = ["1", "x", "3"]
        .iter()
        .map(|t| {
            calls2.push(*t);
            t.parse::<i32>().ok()
        })
        .collect();
    println!("{:?}", o);
    println!("parse called on {:?}", calls2);
}
```

```text
===== rustc --edition 2021 r36_result_stop.rs =====
(exit 0)
===== ./r36_result_stop =====
Err(ParseIntError { kind: InvalidDigit })
parse called on ["1", "2", "x"]
None
parse called on ["1", "x"]
(exit 0)
```

- ★★★ **`parse called on ["1", "2", "x"]`** — 원본은 다섯 개(`"1" "2" "x" "4" "y"`)인데 **셋째에서 멈췄다.** `"4"`·`"y"` 는 **클로저가 불리지도 않았다.**
  결과는 **첫 `Err`**(`"x"` 의 `InvalidDigit`)이고, 뒤의 `"y"` 가 낼 둘째 `Err` 는 **만들어지지도 않았다.**
- ★★ **`Option` 도 같다** — `["1", "x"]` 까지만 불리고 `None`.
  std 문서가 이것을 **보장**으로 적는다 — 「**`Err` 이면 더 이상 원소를 가져가지 않는다**」(`Result` 의 `FromIterator`) · `Option` 도 같은 문장. **게으름 + 조기 종료**가 합쳐진 결과다.

**받는 타입을 안 적으면.**

```rust
// r36_no_type.rs
// 모을 타입을 적지 않으면
fn main() {
    let v = [1, 2, 3].iter().map(|x| x * 2).collect();
    println!("{}", v.len());
}
```

```text
===== rustc --edition 2021 r36_no_type.rs =====
error[E0282]: type annotations needed
 --> r36_no_type.rs:3:9
  |
3 |     let v = [1, 2, 3].iter().map(|x| x * 2).collect();
  |         ^
4 |     println!("{}", v.len());
  |                    - type must be known at this point
  |
help: consider giving `v` an explicit type
  |
3 |     let v: Vec<_> = [1, 2, 3].iter().map(|x| x * 2).collect();
  |          ++++++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0282`.
(exit 1)
```

- ★★ **E0282 — type annotations needed.** `collect` 는 **무엇으로 모을지를 받는 쪽에서** 알아야 한다. `help:` 가 「**consider giving `v` an explicit type**」 — `let v: Vec<_>`.

```rust
// r36_no_type_help.rs
// help: 대로 Vec<_> 를 적으면
fn main() {
    let v: Vec<_> = [1, 2, 3].iter().map(|x| x * 2).collect();
    println!("{} {:?}", v.len(), v);
}
```

```text
===== rustc --edition 2021 r36_no_type_help.rs =====
(exit 0)
===== ./r36_no_type_help =====
3 [2, 4, 6]
(exit 0)
```

- ★ **`help:` 대로 `Vec<_>` 만 적으면 통과**(`3 [2, 4, 6]`). **바깥 컨테이너만** 정하면 원소 타입(`_`)은 추론된다. 이 처방은 **맞았다.**

### (5) 소비자 — `sum`·`count`·`fold`, 그리고 무한 원본

```rust
// r36_consume.rs
// 소비하는 메서드 — sum · count · fold, 그리고 무한 이터레이터에 take
fn main() {
    let v = [3, 1, 4, 1, 5];
    let s: i32 = v.iter().sum();
    let c = v.iter().filter(|x| **x > 1).count();
    let f = v.iter().fold(String::new(), |acc, x| format!("{}{}", acc, x));
    println!("{} {} {}", s, c, f);
    let evens: Vec<u64> = (0..).filter(|x| x % 2 == 0).map(|x| x * x).take(4).collect();
    println!("{:?}", evens);
    let first = (1..).find(|x| x * x > 50);
    println!("{:?}", first);
}
```

```text
===== rustc --edition 2021 r36_consume.rs =====
(exit 0)
===== ./r36_consume =====
14 3 31415
[0, 4, 16, 36]
Some(8)
(exit 0)
```

- ★ **`sum` 14 · `count` 3 · `fold` `"31415"`** — 셋 다 **소비자**다(끝까지 당긴다).
- ★★ **`(0..)` 은 끝이 없다** — 그래도 `.filter().map().take(4)` 가 **네 개만** 당겨 `[0, 4, 16, 36]` 에서 끝났다. `find` 도 **처음 맞는 것**(`Some(8)`)에서 멈춘다.
  ★ std 문서의 경고 — 무한 이터레이터에 **`min`·`count` 처럼 끝까지 가야 하는 메서드**를 부르면 **끝나지 않을 수 있다**(이 문서는 던지지 않았다 — 무한 루프다).

**`sum` 의 결과 타입을 안 적으면.**

```rust
// r36_sum_type.rs
// sum 의 결과 타입을 적지 않으면
fn main() {
    let v = [3, 1, 4];
    let s = v.iter().sum();
    println!("{}", s);
}
```

```text
===== rustc --edition 2021 r36_sum_type.rs =====
error[E0283]: type annotations needed
 --> r36_sum_type.rs:4:9
  |
4 |     let s = v.iter().sum();
  |         ^            --- type must be known at this point
  |
  = note: cannot satisfy `_: Sum<&i32>`
  = help: the following types implement trait `Sum<A>`:
            `Duration` implements `Sum<&'a Duration>`
            `Duration` implements `Sum`
            `Option<T>` implements `Sum<Option<U>>`
            `Result<T, E>` implements `Sum<Result<U, E>>`
            `Saturating<u128>` implements `Sum<&'a Saturating<u128>>`
            `Saturating<u128>` implements `Sum`
            `Saturating<u16>` implements `Sum<&'a Saturating<u16>>`
            `Saturating<u16>` implements `Sum`
          and 88 others
note: required by a bound in `std::iter::Iterator::sum`
 --> /rustc/ded5c06cf21d2b93bffd5d884aa6e96934ee4234/library/core/src/iter/traits/iterator.rs:3576:5
help: consider giving `s` an explicit type
  |
4 |     let s: /* Type */ = v.iter().sum();
  |          ++++++++++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0283`.
(exit 1)
```

- ★ **E0283 — type annotations needed · `cannot satisfy _: Sum<&i32>`.** `sum` 도 **받는 쪽이 정한다**(`Duration`·`Option`·`Result`·… 「**and 88 others**」가 `Sum` 을 구현한다). `collect` 와 같은 집안이다.

### (6) `iter` / `iter_mut` / `into_iter` — 무엇을 내놓나

**언제 쓰나** — 돌고 나서 **원본을 또 쓸지** 정할 때(정본은 [목록의 **37번 주제**](../37-intoiterator-three-forms-iter-iter-mut-into-iter/)).

```rust
// r36_three.rs
// iter / iter_mut / into_iter 가 내놓는 것의 타입
use std::any::type_name_of_val;

fn main() {
    let mut v = vec![String::from("a"), String::from("b")];
    if let Some(x) = v.iter().next() {
        println!("iter      {}", type_name_of_val(&x));
    }
    if let Some(x) = v.iter_mut().next() {
        println!("iter_mut  {}", type_name_of_val(&x));
        x.push('!');
    }
    println!("{:?}", v);
    if let Some(x) = v.into_iter().next() {
        println!("into_iter {}", type_name_of_val(&x));
    }
}
```

```text
===== rustc --edition 2021 r36_three.rs =====
(exit 0)
===== ./r36_three =====
iter      &alloc::string::String
iter_mut  &mut alloc::string::String
["a!", "b"]
into_iter alloc::string::String
(exit 0)
```

- ★★ **`&String` · `&mut String` · `String`** — 빌려 읽기 / 빌려 고치기 / **옮겨 가지기.** `iter_mut` 으로 `"a!"` 가 됐다.

```rust
// r36_for_move.rs
// for 로 돈 뒤에 원래 Vec 을 쓰면
fn main() {
    let v = vec![String::from("a"), String::from("b")];
    for s in v {
        println!("{}", s);
    }
    println!("{}", v.len());
}
```

```text
===== rustc --edition 2021 r36_for_move.rs =====
error[E0382]: borrow of moved value: `v`
 --> r36_for_move.rs:7:20
  |
3 |     let v = vec![String::from("a"), String::from("b")];
  |         - move occurs because `v` has type `Vec<String>`, which does not implement the `Copy` trait
4 |     for s in v {
  |              - `v` moved due to this implicit call to `.into_iter()`
...
7 |     println!("{}", v.len());
  |                    ^ value borrowed here after move
  |
note: `into_iter` takes ownership of the receiver `self`, which moves `v`
 --> /rustc/ded5c06cf21d2b93bffd5d884aa6e96934ee4234/library/core/src/iter/traits/collect.rs:310:18
help: consider iterating over a slice of the `Vec<String>`'s content to avoid moving into the `for` loop
  |
4 |     for s in &v {
  |              +

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0382`.
(exit 1)
```

- ★★ **E0382 — borrow of moved value: `v`.** `for s in v` 는 **`v.into_iter()`** 로 탈당된다 — 진단이 「**`v` moved due to this implicit call to `.into_iter()`**」라고 **숨은 호출을 드러낸다.**
  `help:` 는 **`for s in &v`**(= `v.iter()`). std 문서의 탈당 예와 같다.

## 문법 — 형태와 규칙

```text
   형태

   impl Iterator for T { type Item = U; fn next(&mut self) -> Option<U> { … } }   ← 이것만 구현한다
   v.iter().map(f).filter(g).take(n)          ← 어댑터 사슬 — 아직 아무 일도 안 한다
   … .collect::<Vec<_>>()   /   let v: Vec<_> = … .collect();   ← 받는 타입을 적는다
   let r: Result<Vec<i32>, _> = it.map(|t| t.parse()).collect();  ← 첫 Err 에서 멈춘다
   let s: i32 = v.iter().sum();               ← sum 도 받는 타입을 적는다
   v.iter().for_each(|x| …)                   ← 부수 효과는 for_each 나 for
   (0..).filter(…).take(4)                    ← 무한 원본은 take·find 로 끊는다


   금지 사례 · 경고 — 던져서 받은 것

   v.iter().map(|x| println!(…));             ⚠ unused `Map` that must be used  (그리고 아무것도 안 찍힌다)
   let _ = v.iter().map(…);                   ⚠ 없음 — 그런데 여전히 아무것도 안 찍힌다
   let v = it.collect();                      ✘ E0282
   let s = v.iter().sum();                    ✘ E0283
   for s in v { … }  v.len()                  ✘ E0382  "implicit call to `.into_iter()`"
```

**규칙 불릿.**

- ★★★ **어댑터는 게으르다** — 소비자가 `next` 를 부를 때만 일하고, **원소마다 사슬 전체를 지나간다**((2)).
- ★★ **`take`·`find`·`Result` 수집은 일찍 멈춘다** — 뒤의 클로저는 **안 불린다**((2)·(4)·(5)).
- ★★ **`collect`·`sum` 은 받는 타입이 정한다** — 안 적으면 E0282·E0283((4)·(5)).
- ★ **`next` 하나면 기본 메서드가 전부 생긴다**((1)).
- ★ **`iter` = `&T` · `iter_mut` = `&mut T` · `into_iter`(와 `for x in v`) = `T`** — 뒤엣것은 원본을 옮긴다((6)).

## 어디서 틀리나

### 1. ★★★ 「`map` 을 부르면 클로저가 원소마다 돈다」

**소비자가 없으면 한 번도 안 돈다**((2)·(3)). 사슬을 만든 직후 로그는 **0 줄**이다. 부수 효과를 원하면 **`for_each`·`for`**.

### 2. ★★★ 「경고가 사라졌으니 고쳐졌다」

**`let _ =` 는 경고만 지운다**((3)). `help:` 의 첫 처방을 따르면 **경고 0 · 출력도 0** 이 된다. **둘째 처방(`for_each`)이 이 자리의 뜻**이다.

### 3. ★★ 「사슬은 `map` 을 전부 끝낸 다음 `filter` 를 전부 한다」

**그건 단계마다 `collect` 한 판이다**((2)). 어댑터 사슬은 **원소마다 세로로** 돈다 — 그래서 `take(2)` 뒤로는 `map(5)` 가 **영영 없다.** ★ JS 배열 메서드에 익숙하면 여기서 틀린다 — JS 는 배열 메서드가 기본(가로)이고 Rust 는 이터레이터가 기본(세로)이다.

### 4. ★★ 「`Result` 로 모으면 전부 돌고 에러를 모아 준다」

**첫 `Err` 에서 멈추고, 그 하나만** 돌려준다((4)) — 뒤의 원소는 **클로저조차 안 불린다.** 에러를 전부 모으려면 **`Vec<Result<…>>`** 로 모은 뒤 가른다.

### 5. ★ 「`HashSet` 으로 모으면 넣은 순서대로 나온다」

**아니다** — 그래서 이 문서는 `len` 만 찍었다((4)). 순서가 필요하면 **`BTreeSet`**(정렬)이나 `Vec` + `dedup`.

### 6. ★ 「`for x in v` 뒤에도 `v` 를 쓸 수 있다」

**E0382**((6)) — `for` 가 **`into_iter()`** 를 부른다. `for x in &v` 로.

### 7. ★ 「이터레이터 사슬은 손으로 쓴 루프만큼 빠르다(제로 코스트)」

**이 문서는 재지 않았다.** 센 것은 **호출 횟수와 순서**뿐이다. 그 주장의 근거와 경계(「많은 경우」·단형화의 대가)는 [`언어-특성/README.md`](../../언어-특성/README.md) §6 이 정본이다.

## 구현 세부사항 대 언어 보장

| 항목 | 무엇인가 | 근거 |
|---|---|---|
| ★★★ **어댑터가 게으른** 것 | ★ **std 의 약속** — 모듈 문서 Laziness 절 「이터레이터(와 어댑터)는 게으르다」 | (2)의 `log entries 0` |
| 원소마다 **세로로** 도는 것 | ★ **std 어댑터의 정의에서 따라 나온다** — 각 어댑터의 `next` 가 안쪽 `next` 를 **한 번씩** 부른다. **이 문서는 로그로 관찰**했다 | (2)의 순서 |
| ★★ **`Result`/`Option` 수집이 첫 실패에서 멈추는** 것 | ★ **std 의 약속** — `FromIterator` 문서 「no further elements are taken」 | (4)의 호출 로그 |
| `take(n)` 이 n 개 뒤 원본을 **안 당기는** 것 | ★ **이 판의 관찰** — `take` 문서는 「n 개를 내거나 끝나면 멈춘다」까지 적고 **원본을 더 당기지 않는다는 명문은 없다**(로그가 근거) | (2)의 `next#3 (none)` |
| `#[must_use]` 경고와 문구 | ★ **구현 세부**(린트) — 경고 「unused `Map` that must be used」가 `Map` 에 `#[must_use]` 가 달렸다는 증거다(**이 머신에 std 소스가 없어 속성 원문은 안 읽었다**). 문구는 판마다 바뀔 수 있다 | (3) |
| `help:` 의 `let _ =` 처방 | ★ **구현 세부** — 진단의 제안. **이 자리에서는 틀린 처방** | (3) |
| `for` 의 `IntoIterator::into_iter` 탈당 | ★ **언어 보장** — Reference(`expr.loop.for.desugar`) · std 모듈 문서의 탈당 예 | (6)의 E0382 |
| `HashSet` 순회 순서 | ★ **보장 없음** — 이 문서는 찍지 않았다 | (4) |

## 언제 쓰고 언제 안 쓰나

- ★★ **어댑터 사슬을 쓴다** — 변환·걸러내기·앞 몇 개만·무한 원본. **필요한 만큼만 일한다**((2)·(5)).
- ★ **중간에 `collect` 하지 않는다** — 단계마다 모으면 **전부를 계산**한다(`map calls 10`). 중간 결과를 **두 번 이상 쓸 때만** 모은다.
- ★★ **실패할 수 있는 변환은 `Result<Vec<_>, _>` 로 모은다** — 첫 에러에서 멈춘다. **에러를 전부 보고 싶으면** `Vec<Result<…>>` 로 모은 뒤 `partition` 류로 가른다((4)).
- ★ **부수 효과는 `for` 나 `for_each`** — `map` 은 값을 만드는 데 쓴다((3)).
- ★ **순서가 필요한 집합은 `BTreeSet`**((4)).

## 핵심 문장

- ★★★ **어댑터는 아무것도 안 한다 — 소비자가 `next` 를 부르면 한 원소가 사슬 전체를 지나간다**((2)).
- ★★★ **같은 파이프라인이 단계마다 모으면 `10 · 10`, 사슬이면 `4 · 4`** — JS 21번의 배열판·헬퍼판과 **수도 순서도 같다**((2)).
- ★★ **`Result` 로 모으면 첫 `Err` 에서 멈춘다 — 뒤의 클로저는 불리지도 않는다**((4)).
- ★★ **`collect` 는 받는 타입이 정한다** — 같은 사슬이 `Vec`·`HashSet`·`String`·`Result<Vec>` 가 된다((4)).
- ★ **`let _ =` 는 경고를 지울 뿐 사슬을 돌리지 않는다**((3)).

## 관련 자료

- ★★ JS 갈래의 [**21번**](../../../js/syntax/21-iterator-helpers/) — 이터레이터 헬퍼. **경계**: 호출 로그 방법과 JS 쪽 수치(배열판 10 · 10 / 헬퍼판 4 · 4)는 **거기**다. 여기는 **같은 파이프라인을 Rust 로 던져** 같은 표를 얻었다.
- ★ Python 갈래의 [**15번**](../../../python/syntax/15-generator-expressions-lazy-eval/) · [**16번**](../../../python/syntax/16-iterator-protocol/) · [**17번**](../../../python/syntax/17-generators-yield/) — 파이썬의 게으른 이터레이션. (2)의 파이썬 블록은 한 칸 대비다.
- ★ [`언어-특성/README.md`](../../언어-특성/README.md) §6 — **제로 코스트 논증의 정본.** 이 문서는 시간을 재지 않았다.
- [**34번 주제** — 클로저](../34-closures-fn-fnmut-fnonce-and-move/) — 어댑터가 받는 클로저의 트레이트(`FnMut`). (2)의 로그 클로저가 `&RefCell` 만 잡아 **`Copy`** 라 세 사슬에 거듭 쓰였다.
- [**25번 주제** — 트레이트·기본 메서드·연관 타입](../25-traits-definition-impl-default-methods-and-associated-types/) — `type Item` 과 기본 메서드 70여 개의 뼈대((1)).
- [**35번 주제** — 함수 포인터](../35-function-pointers-and-returning-closures/) — `map(add1)` 처럼 **함수 이름**을 어댑터에 넘길 수 있는 이유.
- [**22번 주제** — `Result` 와 `?`](../22-result-question-mark-and-from/) · [**21번 주제** — `Option` 조합자](../21-option-and-combinators/) — (4)의 `Result`/`Option` 수집이 거기서 본 타입이다.
- [목록의 **37번 주제**](../37-intoiterator-three-forms-iter-iter-mut-into-iter/) — `IntoIterator` 세 형태. (6)과 「더 들어가면」의 배열 `into_iter` 가 거기서 본체가 된다.
- 목록의 **42번 주제** — `RefCell`. (2)의 로그 장치가 그것이다.

## 용어 풀이

- **`Iterator`** — `next(&mut self) -> Option<Item>` 하나를 요구하는 트레이트. 나머지 메서드는 기본 메서드다.
- **어댑터(adapter)** — 이터레이터를 받아 이터레이터를 돌려주는 메서드. 게으르다.
- **소비자(consumer)** — `next` 를 불러 값을 끌어내는 메서드·구문. `collect`·`sum`·`count`·`fold`·`for_each`·`for`.
- **게으름(laziness)** — 필요할 때까지 계산을 미루는 것.
- **`FromIterator`** — `collect` 가 무엇을 만들지 정하는 트레이트. 받는 타입이 구현한다.
- **`#[must_use]`** — 결과를 안 쓰면 경고를 내라는 속성. 어댑터 타입에 달려 있다.
- **탈당(desugaring)** — 문법 설탕을 원래 모양으로 푸는 것. `for x in v` → `IntoIterator::into_iter(v)` + `loop { match next() … }`.
- **무한 이터레이터** — 끝(`None`)이 없는 이터레이터. `(0..)`·`repeat`·`cycle`.

## 더 들어가면

- **배열의 `into_iter()` 는 에디션이 가른다** — 2018 은 **`&i32`**(경고와 함께), 2021 은 **`i32`**:

```text
===== 소스: r36_array_into.rs =====
// 배열에 into_iter() 를 부르면 무엇이 나오나
use std::any::type_name_of_val;

fn main() {
    let a = [10, 20];
    if let Some(x) = a.into_iter().next() {
        println!("{}", type_name_of_val(&x));
    }
}
===== rustc --edition 2018 r36_array_into.rs =====
warning: this method call resolves to `<&[T; N] as IntoIterator>::into_iter` (due to backwards compatibility), but will resolve to `<[T; N] as IntoIterator>::into_iter` in Rust 2021
 --> r36_array_into.rs:6:24
  |
6 |     if let Some(x) = a.into_iter().next() {
  |                        ^^^^^^^^^
  |
  = warning: this changes meaning in Rust 2021
  = note: for more information, see <https://doc.rust-lang.org/edition-guide/rust-2021/IntoIterator-for-arrays.html>
  = note: `#[warn(array_into_iter)]` (part of `#[warn(rust_2021_compatibility)]`) on by default
help: use `.iter()` instead of `.into_iter()` to avoid ambiguity
  |
6 -     if let Some(x) = a.into_iter().next() {
6 +     if let Some(x) = a.iter().next() {
  |
help: or use `IntoIterator::into_iter(..)` instead of `.into_iter()` to explicitly iterate by value
  |
6 -     if let Some(x) = a.into_iter().next() {
6 +     if let Some(x) = IntoIterator::into_iter(a).next() {
  |

warning: 1 warning emitted

(exit 0)
===== ./r36_array_into =====
&i32
(exit 0)
```

```text
===== 소스: r36_array_into.rs =====
// 배열에 into_iter() 를 부르면 무엇이 나오나
use std::any::type_name_of_val;

fn main() {
    let a = [10, 20];
    if let Some(x) = a.into_iter().next() {
        println!("{}", type_name_of_val(&x));
    }
}
===== rustc --edition 2021 r36_array_into.rs =====
(exit 0)
===== ./r36_array_into =====
i32
(exit 0)
```

  ★ 같은 소스가 **2018 에서 `&i32`, 2021 에서 `i32`** 다. 2018 경고가 「**this changes meaning in Rust 2021**」라고 적는다. `IntoIterator` 세 형태는 [목록의 **37번 주제**](../37-intoiterator-three-forms-iter-iter-mut-into-iter/), 에디션 이전은 **47번 주제**가 정본이다.
- **`DoubleEndedIterator`·`ExactSizeIterator`** — `rev`·`len` 을 주는 추가 트레이트. 1.66 릴리스 노트가 `impl ExactSizeIterator` 에도 `#[must_use]` 가 먹게 했다고 적는다(이 문서는 던지지 않았다).
- **`try_fold`·`try_for_each`** — `Result`/`Option` 을 돌려주는 클로저로 **도중에 멈추는** 소비자. (4)의 조기 종료를 직접 쓰는 길이다.
- **어댑터가 패닉하면** — std 문서 「이터레이터는 **지정되지 않은(하지만 메모리 안전한) 상태**가 된다」. 패닉 뒤의 값에 기대지 마라.
