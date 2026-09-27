# rust/syntax/36 — `Iterator`와 어댑터·게으름·`collect` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 던지는 법 — `rustc --edition 2021 <파일>.rs`. **외부 크레이트를 하나도 쓰지 않는다.**
> ★★★ **사슬을 보면 두 가지를 먼저 물어라** — 「**끝에서 누가 `next` 를 부르나**」와 「**그 소비자가 몇 개를 원하나**」.
> ★ **문항 11개 중 코드가 붙은 예측형은 6개**다. 소스 펜스는 캡처가 실파일에서 찍었다(`check-source-fences.py` 대조).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 같은 파이프라인 — 단계마다 모으기와 사슬 (예측)

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

- ★★★ `[1]` 의 `map calls`·`filter calls` 와 `order` 줄은? `[2]` 의 `log entries` 와 두 호출 수, `order` 줄은?
- ★★ `[3]` 의 세 줄 — `next#1`·`next#2`·`next#3` 이 각각 **무엇을 돌려주고 어떤 클로저를 부르나**?
- ★ `map(5)` 는 각 판에서 불리는가?

### 2. ★★ 어댑터만 만들고 버리면 (예측)

```rust
// r36_unused.rs
// 어댑터만 만들고 버린다
fn main() {
    let v = vec![1, 2, 3];
    v.iter().map(|x| println!("{}", x));
    println!("end");
}
```

```rust
// r36_unused_let.rs
// 첫 help: 대로 let _ = 를 붙이면
fn main() {
    let v = vec![1, 2, 3];
    let _ = v.iter().map(|x| println!("{}", x));
    println!("end");
}
```

- 앞 소스는 컴파일되는가? 경고가 있다면 몇 개이고, 실행 출력은?
- ★★★ 뒤 소스는 앞 소스의 **첫 `help:`** 를 따른 판이다. 경고는? 실행 출력은?

### 3. ★★★ `Result` 로 모을 때 (예측)

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

- 첫 두 줄의 출력은? 원본 다섯 개 중 **몇 개에 클로저가 불렸나**?
- 뒤 두 줄은? ★ 이 결과는 std 가 **보장**하는가, 이 판의 관찰인가?

### 4. ★★ 같은 사슬, 받는 타입을 바꿔 가며 (예측)

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

- 일곱 줄 각각의 출력은? `HashSet` 줄은 왜 `len` 만 찍었을까?
- ★ `Result<Vec<i32>, _>` 와 `Vec<Result<i32, _>>` 는 **무엇이 다른가**?

### 5. ★ `next` 하나만 구현한 타입 (예측)

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

- 다섯 줄의 출력은? `collect`·`filter`·`zip`·`max` 는 **어디서 왔나**?

### 6. ★★ `for` 로 돈 뒤 (예측)

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

- 컴파일되는가? 에러면 번호와, 진단이 드러내는 **숨은 호출**은?
- ★ `iter`·`iter_mut`·`into_iter` 는 각각 무엇을 내놓는가(`Vec<String>` 에서)?

### 7. ★★ 받는 타입을 안 적으면 (경계)

- `let v = [1, 2, 3].iter().map(|x| x * 2).collect();` 는 무슨 번호의 에러인가? `help:` 대로 무엇을 적으면 되는가 — 원소 타입까지 적어야 하는가?
- `let s = v.iter().sum();` 은? 에러 번호는 같은가?

### 8. ★★ 무한 원본 (경계)

- `(0..).filter(|x| x % 2 == 0).map(|x| x * x).take(4).collect::<Vec<u64>>()` 는 끝나는가? 결과는?
- ★ 무한 원본에 부르면 **안 끝날 수 있는** 메서드는 어떤 종류인가?

### 9. ★★ 세로 대 가로 — JS 와 (연결)

- JS 갈래의 [21번](../../../js/syntax/21-iterator-helpers/)은 같은 파이프라인에서 배열판과 헬퍼판의 호출 수를 각각 얼마로 냈나? Rust 의 두 판과 **맞는 짝**은?
- ★ 두 언어에서 **기본값**(아무 생각 없이 쓰는 쪽)은 각각 가로인가 세로인가?

### 10. ★ 경고가 사라졌다는 것 (왜)

- 2번의 `let _ =` 판은 왜 경고가 없는데 **틀린 코드**인가? 이 자리에 맞는 처방은?

### 11. ★ 이터레이터와 제로 코스트 (연결)

- 이 주제는 「이터레이터는 손으로 짠 루프만큼 빠르다」를 **주장하는가**? 무엇을 세었고, 그 논증의 정본은 어디인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
