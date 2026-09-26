# rust/syntax/40 — `Box<T>`·재귀 타입·`dyn` 담기 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 던지는 법 — `rustc --edition 2021 <파일>.rs`(최적화 격자는 스크립트가 `-C opt-level` 넷을 돈다). **외부 크레이트를 하나도 쓰지 않는다.**
> ★★★ **`Box` 를 보면 먼저 물어라** — 「**가리키는 것이 `Sized` 인가**」와 「**그 값은 어디서 먼저 만들어지나**」.
> ★ **문항 11개 중 코드가 붙은 예측형은 6개**다. 소스 펜스는 캡처가 실파일에서 찍었다(`check-source-fences.py` 대조).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 자기를 품는 열거형 (예측)

```rust
// r40_rec.rs
enum List {
    Cons(i32, List),
    Nil,
}

fn main() {
    let _l = List::Nil;
}
```

- 컴파일되는가? 에러라면 **번호가 몇 개**이고 각각 무엇인가? `help:` 는 무엇을 권하나?
- ★ `main` 의 `let _l = List::Nil;` 을 지우면(값을 안 만들면) 에러 수가 달라지나?

### 2. ★★★ `help:` 대로 타입만 고치면 (예측)

```rust
// r40_rec_help.rs
enum List {
    Cons(i32, Box<List>),
    Nil,
}

fn sum(l: &List) -> i32 {
    match l {
        List::Cons(x, rest) => x + sum(rest),
        List::Nil => 0,
    }
}

fn main() {
    let l = List::Cons(1, List::Cons(2, List::Nil));
    println!("sum {}  size_of::<List>() = {}", sum(&l), std::mem::size_of::<List>());
}
```

- 컴파일되는가? 에러라면 번호와 개수, 각각의 `help:` 는? 그 `help:` 를 전부 따르면 출력은?

### 3. ★★ 보관증의 크기 (예측)

```rust
// r40_size.rs
use std::fmt::Display;
use std::mem::size_of;

#[allow(dead_code)]
enum List {
    Cons(i32, Box<List>),
    Nil,
}

fn main() {
    println!("{:<28} {}", "i32", size_of::<i32>());
    println!("{:<28} {}", "&i32", size_of::<&i32>());
    println!("{:<28} {}", "Box<i32>", size_of::<Box<i32>>());
    println!("{:<28} {}", "Box<[i32; 100]>", size_of::<Box<[i32; 100]>>());
    println!("{:<28} {}", "Box<[i32]>", size_of::<Box<[i32]>>());
    println!("{:<28} {}", "Box<str>", size_of::<Box<str>>());
    println!("{:<28} {}", "Box<dyn Display>", size_of::<Box<dyn Display>>());
    println!("{:<28} {}", "Option<Box<i32>>", size_of::<Option<Box<i32>>>());
    println!("{:<28} {}", "Option<Box<dyn Display>>", size_of::<Option<Box<dyn Display>>>());
    println!("{:<28} {}", "Option<i32>", size_of::<Option<i32>>());
    println!("{:<28} {}", "(i32, Box<List>)", size_of::<(i32, Box<List>)>());
    println!("{:<28} {}", "List", size_of::<List>());
    println!("{:<28} {}", "Box<List>", size_of::<Box<List>>());
    println!("{:<28} {}", "Option<Box<List>>", size_of::<Option<Box<List>>>());
    println!("{:<28} {}", "Vec<i32>", size_of::<Vec<i32>>());
}
```

- 열다섯 줄의 수는(x86_64)? ★★ 그중 **std 가 보장하는** 수와 **이 판의 구현**인 수를 가르면?

### 4. ★★ 보관증과 물건은 어느 영역에 (예측)

```rust
// r40_where.rs
// Box 가 가리키는 곳과 스택 변수가 「같은 영역」인가 — /proc/self/maps 의 줄 이름으로 판정한다
use std::fs;

fn region(addr: usize) -> String {
    let maps = fs::read_to_string("/proc/self/maps").unwrap();
    for line in maps.lines() {
        let mut parts = line.split_whitespace();
        let range = parts.next().unwrap();
        let (lo, hi) = range.split_once('-').unwrap();
        let lo = usize::from_str_radix(lo, 16).unwrap();
        let hi = usize::from_str_radix(hi, 16).unwrap();
        if lo <= addr && addr < hi {
            let name = parts.nth(4).unwrap_or("");
            return if name.is_empty() { String::from("(anonymous)") } else { name.to_string() };
        }
    }
    String::from("(not mapped)")
}

fn main() {
    let local: i32 = 7;
    let b: Box<i32> = Box::new(7);
    let big: Box<[u8]> = vec![0u8; 1 << 20].into_boxed_slice();
    let a_local = &local as *const i32 as usize;
    let a_box_var = &b as *const Box<i32> as usize;
    let a_box_data = &*b as *const i32 as usize;
    let a_big = big.as_ptr() as usize;
    println!("local i32         : {}", region(a_local));
    println!("the Box variable  : {}", region(a_box_var));
    println!("*b (Box<i32> data): {}", region(a_box_data));
    println!("1 MiB Box<[u8]>   : {}", region(a_big));
    println!("same region as local — box variable {} · box data {} · 1 MiB data {}",
        region(a_box_var) == region(a_local),
        region(a_box_data) == region(a_local),
        region(a_big) == region(a_local));
}
```

- 네 줄의 영역 이름과 마지막 줄의 참/거짓 셋은?
- ★ 이 프로그램은 왜 **주소를 찍지 않았나**?

### 5. ★★ 16 MiB 를 상자에 — 최적화 수준 넷 (예측)

```rust
// r40_big.rs
// 16 MiB 배열을 Box::new 로
const N: usize = 16 << 20;

fn main() {
    let b: Box<[u8; N]> = Box::new([7u8; N]);
    eprintln!("len {} first {} last {}", b.len(), b[0], b[N - 1]);
}
```

```rust
// r40_big_vec.rs
// 같은 16 MiB 를 vec! 로 만들어 Box<[u8]> 로 바꾼다
const N: usize = 16 << 20;

fn main() {
    let b: Box<[u8]> = vec![7u8; N].into_boxed_slice();
    eprintln!("len {} first {} last {}", b.len(), b[0], b[N - 1]);
}
```

```bash
# r40_big_grid.sh
# 소스 둘 × 최적화 수준 넷 — 실행 종료 코드를 세 번씩
printf '%-12s %-16s | %-7s | %s\n' source opt-level 'cc exit' 'run exit x3'
bad=0; total=0
for s in r40_big r40_big_vec; do
  for o in 0 1 2 3; do
    rustc --edition 2021 -C opt-level=$o -o $s.$o $s.rs 2>/dev/null
    cc=$?
    runs=""
    for i in 1 2 3; do
      { ./$s.$o; } >/dev/null 2>&1
      rc=$?
      runs="$runs $rc"
    done
    total=$((total+1))
    [ "$runs" != " 0 0 0" ] && bad=$((bad+1))
    printf '%-12s %-16s | %-7s |%s\n' "$s" "-C opt-level=$o" "$cc" "$runs"
  done
done
echo "ulimit -s = $(ulimit -s)"
echo "cells whose run exit is not 0 0 0: $bad / $total"
```

- ★★★ 여덟 줄의 `run exit x3` 칸은? 마지막 줄의 수는?
- ★ 0 이 아닌 칸이 있다면 **그 한 판**이 표준 오류에 남기는 것은?

### 6. ★★ 옮겨 꺼내기 — `Box` 와 `Rc` (예측)

```rust
// r40_move_out.rs
fn main() {
    let b: Box<String> = Box::new(String::from("boxed"));
    let s: String = *b;
    println!("s = {s}");
}
```

```rust
// r40_move_out_rc.rs
use std::rc::Rc;

fn main() {
    let r: Rc<String> = Rc::new(String::from("shared"));
    let s: String = *r;
    println!("{s}");
}
```

- 두 소스는 각각 컴파일되는가? 에러라면 번호는?
- ★★ 에러 쪽의 `help:` 가 있다면 **각각** 따르면 통과하는가?

### 7. ★★ 빌린 참조로 재귀를 끊으면 (경계)

- 1번의 `Cons(i32, List)` 를 `Cons(i32, &List)` 로 바꾸면 무슨 에러이고, 이어지는 `help:` 를 따라가면 **몇 바퀴** 만에 통과하나? 통과한 판은 **힙을 쓰나**? `Box` 판과 뜻이 어떻게 다른가?

### 8. ★★ `Box::new` 의 시그니처 (왜)

- `Box::new` 는 `pub fn new(x: T) -> Box<T>` 다. 인자 `x` 는 **언제·어디서** 만들어지나? 5번의 결과를 이것으로 설명하면? 최적화 수준에 따라 달라질 수 있는 것은 무엇이고, 그것은 **보장**인가?

### 9. ★★ `Option` 을 씌운 크기 (왜)

- 3번에서 `Option<…>` 을 씌워도 크기가 **그대로인 줄**과 **커진 줄**이 있다면, 그 차이를 만드는 성질은 무엇인가? std 는 **어떤 타입들**에 대해 그것을 보장하나 — [35번 주제](../35-function-pointers-and-returning-closures/)의 `fn` 포인터와 같은 규칙인가?

### 10. ★★ `Box<dyn Display>` 의 크기는 누가 정하나 (연결)

- `Box<dyn Display>` 의 크기는 **언어가 보장**하는가? [33번 주제](../33-dyn-trait-objects-and-object-safety/)가 인용한 Reference **두 쪽**은 각각 무엇이라고 적나 — 어느 쪽이 더 정확한가?

### 11. ★ 크기가 다른 셋을 한 `Vec` 에 (경계)

- 크기가 8 · 16 · 32 인 세 타입을 한 `Vec` 에 담으려면 원소 타입을 무엇으로 하나? 그때 **원소 하나의 크기**는? 그리고 `Box::leak` 은 무엇을 주고 무엇을 잃나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
