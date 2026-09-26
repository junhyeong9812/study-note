# rust/syntax/36 — `Iterator`와 어댑터·게으름·`collect` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서
> **`rustc --edition 2021`** 로 실제로 돌려 받은 것이다.\
> ★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
> ★★ 블록 첫 줄 `===== 소스: <파일> =====` 아래가 **컴파일한 소스 전문**이고, **진단의 줄 번호는 그 파일 기준**이다.\
> ★★ **외부 크레이트를 하나도 쓰지 않았다**(네트워크 없음). **시간은 한 번도 재지 않았다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ `10 · 10` 가로, `0 → 4 · 4` 세로

**출력.**

```text
===== 소스: r36_lazy.rs =====
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

**왜 그런가.**

- ★★★ **`[1]` — `map calls 10 · filter calls 10`**, 순서는 `map(1)` … `map(10)` 다음 `filter(10)` … `filter(100)` — **단계별(가로).** 단계마다 `collect` 해서 **전부를 계산**했다.
- ★★★ **`[2]` — 만든 직후 `log entries 0`**, `collect()` 뒤 **`map calls 4 · filter calls 4`**, 순서 `map(1) filter(10) map(2) filter(20) map(3) filter(30) map(4) filter(40)` — **원소별(세로).**
- ★★ **`[3]`** — `next#1` = `Some(20)`(`map(1) filter(10) map(2) filter(20)`) · `next#2` = `Some(40)`(`map(3) filter(30) map(4) filter(40)`) · **`next#3` = `None`, 클로저 `(none)`.** `take(2)` 가 두 개 뒤 원본을 **더 안 당겼다.**
- ★ **`map(5)` 는 `[1]` 에서만** 불린다(단계마다 모은 판). 사슬 판에서는 영영 안 불린다.

### 2. ★★ 경고 둘에 `end` 한 줄 — `let _ =` 는 경고만 지운다

**출력 — 그대로.**

```text
===== 소스: r36_unused.rs =====
// 어댑터만 만들고 버린다
fn main() {
    let v = vec![1, 2, 3];
    v.iter().map(|x| println!("{}", x));
    println!("end");
}
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

**출력 — 첫 `help:` 대로 `let _ =`.**

```text
===== 소스: r36_unused_let.rs =====
// 첫 help: 대로 let _ = 를 붙이면
fn main() {
    let v = vec![1, 2, 3];
    let _ = v.iter().map(|x| println!("{}", x));
    println!("end");
}
===== rustc --edition 2021 r36_unused_let.rs =====
(exit 0)
===== ./r36_unused_let =====
end
(exit 0)
```

**출력 — 둘째 `help:` 대로 `for_each`.**

```text
===== 소스: r36_unused_each.rs =====
// 둘째 help: 대로 for_each 로 바꾸면
fn main() {
    let v = vec![1, 2, 3];
    v.iter().for_each(|x| println!("{}", x));
    println!("end");
}
===== rustc --edition 2021 r36_unused_each.rs =====
(exit 0)
===== ./r36_unused_each =====
1
2
3
end
(exit 0)
```

**왜 그런가.**

- ★★ **앞 소스 — 경고 둘**(`unused_must_use` 「unused `Map` that must be used」 + `map_unit_fn`), **실행 출력 `end` 한 줄.** `note:` 「**iterators are lazy and do nothing unless consumed**」.
- ★★★ **뒤 소스 — 경고 0, 실행 출력 여전히 `end` 한 줄.** `let _ =` 는 「버린다는 걸 안다」는 표시일 뿐 **사슬을 안 돌린다.** 부수 효과가 목적이면 **틀린 처방**이다.
- ★ **둘째 `help:`(`for_each`)** 가 이 자리의 뜻 — `1 2 3 end`.

### 3. ★★★ 셋째에서 멈춘다 — std 의 보장

**출력.**

```text
===== 소스: r36_result_stop.rs =====
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
===== rustc --edition 2021 r36_result_stop.rs =====
(exit 0)
===== ./r36_result_stop =====
Err(ParseIntError { kind: InvalidDigit })
parse called on ["1", "2", "x"]
None
parse called on ["1", "x"]
(exit 0)
```

**왜 그런가.**

- ★★★ **`Err(ParseIntError { kind: InvalidDigit })` · `parse called on ["1", "2", "x"]`** — 다섯 개 중 **세 개에만** 클로저가 불렸다. `"4"`·`"y"` 는 **불리지도 않았다.**
- ★★ **`None` · `parse called on ["1", "x"]`** — `Option` 도 같다.
- ★★ **보장이다** — std 의 `Result`·`Option` `FromIterator` 문서가 「**첫 `Err`(`None`) 뒤로는 원소를 더 가져가지 않는다**」고 적고 예까지 싣는다(누적 합 `6` 이 `16` 이 아니라는 예).

### 4. ★★ 받는 타입이 결과를 정한다

**출력.**

```text
===== 소스: r36_collect.rs =====
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

**왜 그런가.**

- ★★ **`Vec` `["b", "a", "b", "c"]` · `HashSet` `len 3` · `BTreeSet` `{"a", "b", "c"}` · `String` `"babc"` · `Result` `Ok([1, 2, 3])` · `Option` `Some([1, 2, 3])` · `Vec<Result>` `[Ok(1), Err(ParseIntError { kind: InvalidDigit })]`.**
- ★ **`HashSet` 은 순회 순서가 보장되지 않고 실행마다 바뀔 수 있다** — 그래서 `len` 만 찍었다(규칙 11). 순서가 필요한 판은 `BTreeSet` 으로 따로 찍었다.
- ★★ **`Result<Vec<_>, _>` 는 바깥이 하나**(전부 `Ok` 면 `Ok(Vec)`, 아니면 **첫 `Err`**)이고, **`Vec<Result<_, _>>` 는 원소마다 남는다**(에러를 전부 볼 수 있다 — 대신 멈추지 않는다).

### 5. ★ 전부 기본 메서드다

**출력.**

```text
===== 소스: r36_next_only.rs =====
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

- ★ **`[5, 4, 3, 2, 1]` · `90` · `[(3, 'a'), (2, 'b'), (1, 'c')]` · `Some(4) 4 Some(3)` · `Some(2) Some(1) None`.**
- ★★ 구현한 것은 **`type Item` + `fn next`** 뿐 — 나머지는 `Iterator` 의 **기본 메서드**다([25번 주제](../25-traits-definition-impl-default-methods-and-associated-types/)). 로컬 std 문서에서 필수 메서드는 **`next` 하나**다.

### 6. ★★ E0382 — `for` 가 `into_iter()` 를 불렀다

**출력.**

```text
===== 소스: r36_for_move.rs =====
// for 로 돈 뒤에 원래 Vec 을 쓰면
fn main() {
    let v = vec![String::from("a"), String::from("b")];
    for s in v {
        println!("{}", s);
    }
    println!("{}", v.len());
}
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

**출력 — 셋이 내놓는 것.**

```text
===== 소스: r36_three.rs =====
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
===== rustc --edition 2021 r36_three.rs =====
(exit 0)
===== ./r36_three =====
iter      &alloc::string::String
iter_mut  &mut alloc::string::String
["a!", "b"]
into_iter alloc::string::String
(exit 0)
```

- ★★ **E0382 — borrow of moved value: `v`** — 「**`v` moved due to this implicit call to `.into_iter()`**」. `for s in v` 는 Reference 의 탈당대로 **`IntoIterator::into_iter(v)`** 다. `help:` 는 `for s in &v`.
- ★ **`iter` → `&String` · `iter_mut` → `&mut String` · `into_iter` → `String`.** 정본은 [목록의 **37번 주제**](../37-intoiterator-three-forms-iter-iter-mut-into-iter/).

### 7. ★★ E0282 — `Vec<_>` 만 적으면 된다 · `sum` 은 E0283

**출력 — `collect`.**

```text
===== 소스: r36_no_type.rs =====
// 모을 타입을 적지 않으면
fn main() {
    let v = [1, 2, 3].iter().map(|x| x * 2).collect();
    println!("{}", v.len());
}
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

**출력 — `help:` 대로.**

```text
===== 소스: r36_no_type_help.rs =====
// help: 대로 Vec<_> 를 적으면
fn main() {
    let v: Vec<_> = [1, 2, 3].iter().map(|x| x * 2).collect();
    println!("{} {:?}", v.len(), v);
}
===== rustc --edition 2021 r36_no_type_help.rs =====
(exit 0)
===== ./r36_no_type_help =====
3 [2, 4, 6]
(exit 0)
```

**출력 — `sum`.**

```text
===== 소스: r36_sum_type.rs =====
// sum 의 결과 타입을 적지 않으면
fn main() {
    let v = [3, 1, 4];
    let s = v.iter().sum();
    println!("{}", s);
}
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

- ★★ **E0282**, `help:` 「consider giving `v` an explicit type」 — **`let v: Vec<_>`** 만 적으면 통과(`3 [2, 4, 6]`). **원소 타입은 `_` 로 추론**된다.
- ★ **`sum` 은 E0283**(번호가 다르다) — 「cannot satisfy `_: Sum<&i32>`」와 `Sum` 을 구현한 타입 목록(「and 88 others」). 이쪽 `help:` 는 `/* Type */` 자리만 준다 — `let s: i32` 로 적는다(서머리 (5)의 `r36_consume`).

### 8. ★★ 끝난다 — `[0, 4, 16, 36]`

**출력.**

```text
===== 소스: r36_consume.rs =====
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
===== rustc --edition 2021 r36_consume.rs =====
(exit 0)
===== ./r36_consume =====
14 3 31415
[0, 4, 16, 36]
Some(8)
(exit 0)
```

- ★★ **`take(4)` 가 네 개만 당겨 끝났다** — `[0, 4, 16, 36]`. `(1..).find(|x| x * x > 50)` 도 **처음 맞는 `Some(8)`** 에서 멈췄다.
- ★ **안 끝날 수 있는 것 — 끝까지 가야 답이 나오는 소비자**(`min`·`max`·`count`·`sum`·`collect` 에 `take` 없이). std 문서가 「**수학적으로 유한한 시간에 답이 정해져도 끝나지 않을 수 있다**」고 경고한다(이 문서는 던지지 않았다).

### 9. ★★ 배열판 ↔ `Vec` 판, 헬퍼판 ↔ 어댑터 사슬

| | JS 배열 메서드 | JS 이터레이터 헬퍼 | Rust 단계마다 `Vec` | Rust 어댑터 사슬 |
|---|---|---|---|---|
| `map` 호출 | 10 | 4 | 10 | 4 |
| `filter` 호출 | 10 | 4 | 10 | 4 |
| 만든 직후 로그 | — | 0 | — | 0 |
| 순서 | 가로 | 세로 | 가로 | 세로 |

- ★★ **수와 순서가 넷 다 맞는다** — JS 쪽은 [21번](../../../js/syntax/21-iterator-helpers/)의 블록을 **인용**했다(`map calls 10 · filter calls 10` / `map calls 4 · filter calls 4`).
- ★ **기본값이 반대다** — JS 는 **배열 메서드(가로)** 가 흔한 기본이고 헬퍼는 `values()` 로 **골라야** 한다. Rust 는 **이터레이터(세로)** 가 기본이고 가로로 가려면 `collect` 를 **일부러** 끼운다.

### 10. ★ 경고는 「돌았다」의 증거가 아니다

- `let _ =` 는 `#[must_use]` 경고를 **끄는 표시**다. 사슬은 여전히 **소비자가 없어** 아무 일도 안 한다(2번 답 — 경고 0, `end` 한 줄). **경고가 없다는 것과 사슬이 돌았다는 것은 다른 질문**이다.
- **맞는 처방은 `for_each` 나 `for`** — 소비자가 `next` 를 부른다.

### 11. ★ 주장하지 않는다

- **센 것은 콜백 호출 횟수와 순서뿐**이다(1·3번). 속도는 **한 번도 재지 않았다.**
  「제로 코스트」의 근거와 경계(「많은 경우」·단형화의 대가)는 [`언어-특성/README.md`](../../언어-특성/README.md) §6 이 정본이고, 단형화의 벌 수는 [31번 주제](../31-generics-trait-bounds-where-and-monomorphization/)가 셌다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서·서머리의 **모든 블록** | `capture.sh` — 블록마다 명령을 배너에 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` — **흔들린 칸 0 · 고칠 것 0** |
| `next` 만 구현 | `r36_next_only` | 1 | 기본 메서드 전부 동작 |
| ★★★ **게으름 로그** | `r36_lazy` | 1 | **`10 · 10`(가로) / `0` → `4 · 4`(세로)** · `next#3 (none)` |
| 파이썬 대비 | `r36_gen.py` | 1 | `0` → 세로 · `[20, 40]` |
| ★★ `#[must_use]` | `r36_unused` · `r36_unused_let` · `r36_unused_each` | 3 | 경고 2 + `end` · **경고 0 + `end`** · `1 2 3 end` |
| ★★ `collect` 격자 | `r36_collect` | 1 | 일곱 타입 |
| ★★★ **조기 종료** | `r36_result_stop` | 1 | **`["1", "2", "x"]`** · `["1", "x"]` |
| 타입 주석 | `r36_no_type` · `r36_no_type_help` · `r36_sum_type` | 3 | **E0282** · 통과 · **E0283** |
| 소비자·무한 | `r36_consume` | 1 | `14 3 31415` · `[0, 4, 16, 36]` · `Some(8)` |
| 셋과 `for` | `r36_three` · `r36_for_move` | 2 | `&String` · `&mut String` · `String` · **E0382** |
| 배열 `into_iter` 에디션 | `r36_array18` · `r36_array21` | 2 | `&i32`(경고) · `i32` |
| **안 던진 것** — 속도 · 무한 원본의 `count`/`min` · `try_fold` · JS 재실행 | — | 0 | ★ 「안 던졌다」로 표시했다 |

**구현 의존 항목**(버전·환경이 바뀌면 **다시 찍어야 하는** 것).

| 항목 | 왜 |
|---|---|
| `take` 뒤 원본을 **안 당기는** 것 | ★ 명문이 없다 — 이 판의 로그가 근거 |
| `#[must_use]`·`map_unit_fn` 경고와 `help:` 문구 | ★ 린트와 제안은 판마다 바뀐다 |
| `type_name_of_val` 문자열 | ★ std 가 형식을 보장하지 않는다 |

★ **다시 찍는 법** — `capture.sh <새 디렉토리>` 를 그대로 돌리고 `normalize-shaky.py <원본> <새 디렉토리>` 로 견준다.
