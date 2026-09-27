# rust/syntax/40 — `Box<T>`·재귀 타입·`dyn` 담기 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서
> **`rustc --edition 2021`** 로(최적화 격자는 배너의 `-C opt-level`) 실제로 돌려 받은 것이다.\
> ★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
> ★★ 블록 첫 줄 `===== 소스: <파일> =====` 아래가 **컴파일한 소스 전문**이고, **진단의 줄 번호는 그 파일 기준**이다.\
> ★★ **외부 크레이트를 하나도 쓰지 않았다**(네트워크 없음). **시간도 주소도 싣지 않았다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ E0072 + E0391 — `help:` 는 `Box`·`Rc`·`&`, 값을 안 만들면 E0072 하나

**출력.**

```text
===== 소스: r40_rec.rs =====
enum List {
    Cons(i32, List),
    Nil,
}

fn main() {
    let _l = List::Nil;
}
===== rustc --edition 2021 r40_rec.rs =====
error[E0072]: recursive type `List` has infinite size
 --> r40_rec.rs:1:1
  |
1 | enum List {
  | ^^^^^^^^^
2 |     Cons(i32, List),
  |               ---- recursive without indirection
  |
help: insert some indirection (e.g., a `Box`, `Rc`, or `&`) to break the cycle
  |
2 |     Cons(i32, Box<List>),
  |               ++++    +

error[E0391]: cycle detected when computing when `List` needs drop
 --> r40_rec.rs:1:1
  |
1 | enum List {
  | ^^^^^^^^^
  |
  = note: ...which immediately requires computing when `List` needs drop again
  = note: cycle used when computing whether `List` needs drop
  = note: see https://rustc-dev-guide.rust-lang.org/overview.html#queries and https://rustc-dev-guide.rust-lang.org/query.html for more information

error: aborting due to 2 previous errors

Some errors have detailed explanations: E0072, E0391.
For more information about an error, try `rustc --explain E0072`.
(exit 1)
```

**출력 — 값을 안 만들면.**

```text
===== 소스: r40_rec_nomain.rs =====
#[allow(dead_code)]
enum List {
    Cons(i32, List),
    Nil,
}

fn main() {}
===== rustc --edition 2021 r40_rec_nomain.rs =====
error[E0072]: recursive type `List` has infinite size
 --> r40_rec_nomain.rs:2:1
  |
2 | enum List {
  | ^^^^^^^^^
3 |     Cons(i32, List),
  |               ---- recursive without indirection
  |
help: insert some indirection (e.g., a `Box`, `Rc`, or `&`) to break the cycle
  |
3 |     Cons(i32, Box<List>),
  |               ++++    +

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0072`.
(exit 1)
```

**왜 그런가.**

- ★★★ **에러 둘** — **E0072** 「recursive type `List` has infinite size」(표지 「recursive without indirection」) + **E0391** 「cycle detected when computing when `List` needs drop」.
- ★★ `help:` — 「**insert some indirection (e.g., a `Box`, `Rc`, or `&`) to break the cycle**」 + `Cons(i32, Box<List>)` 제안.
- ★ **값을 안 만들면 E0072 하나** — E0391 은 값의 **drop 을 계산하다** 같은 무한 재귀에 걸린 그림자다. 원인은 하나(Reference: 재귀 필드는 **포인터여야** 한다).

### 2. ★★★ E0308 두 개 — 각각의 `help:`(`Box::new`)를 전부 따르면 `sum 3 · 16`

**출력.**

```text
===== 소스: r40_rec_help.rs =====
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
===== rustc --edition 2021 r40_rec_help.rs =====
error[E0308]: mismatched types
  --> r40_rec_help.rs:14:41
   |
14 |     let l = List::Cons(1, List::Cons(2, List::Nil));
   |                           ----------    ^^^^^^^^^ expected `Box<List>`, found `List`
   |                           |
   |                           arguments to this enum variant are incorrect
   |
   = note: expected struct `Box<List>`
                found enum `List`
   = note: for more on the distinction between the stack and the heap, read https://doc.rust-lang.org/book/ch15-01-box.html, https://doc.rust-lang.org/rust-by-example/std/box.html, and https://doc.rust-lang.org/std/boxed/index.html
note: tuple variant defined here
  --> r40_rec_help.rs:2:5
   |
 2 |     Cons(i32, Box<List>),
   |     ^^^^
help: store this in the heap by calling `Box::new`
   |
14 |     let l = List::Cons(1, List::Cons(2, Box::new(List::Nil)));
   |                                         +++++++++         +

error[E0308]: mismatched types
  --> r40_rec_help.rs:14:27
   |
14 |     let l = List::Cons(1, List::Cons(2, List::Nil));
   |             ----------    ^^^^^^^^^^^^^^^^^^^^^^^^ expected `Box<List>`, found `List`
   |             |
   |             arguments to this enum variant are incorrect
   |
   = note: expected struct `Box<List>`
                found enum `List`
   = note: for more on the distinction between the stack and the heap, read https://doc.rust-lang.org/book/ch15-01-box.html, https://doc.rust-lang.org/rust-by-example/std/box.html, and https://doc.rust-lang.org/std/boxed/index.html
note: tuple variant defined here
  --> r40_rec_help.rs:2:5
   |
 2 |     Cons(i32, Box<List>),
   |     ^^^^
help: store this in the heap by calling `Box::new`
   |
14 |     let l = List::Cons(1, Box::new(List::Cons(2, List::Nil)));
   |                           +++++++++                        +

error: aborting due to 2 previous errors

For more information about this error, try `rustc --explain E0308`.
(exit 1)
```

**출력 — 두 `help:` 를 전부 따르면.**

```text
===== 소스: r40_rec_box.rs =====
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
    let l = List::Cons(1, Box::new(List::Cons(2, Box::new(List::Nil))));
    println!("sum {}  size_of::<List>() = {}", sum(&l), std::mem::size_of::<List>());
}
===== rustc --edition 2021 r40_rec_box.rs =====
(exit 0)
===== ./r40_rec_box =====
sum 3  size_of::<List>() = 16
(exit 0)
```

- ★★★ **E0308 × 2** — 「expected `Box<List>`, found `List`」 — **안쪽**(`List::Nil`, 14:41)과 **바깥쪽**(`List::Cons(2, …)`, 14:27). `help:` 는 각각 「**store this in the heap by calling `Box::new`**」.
- ★★ **둘 다 따라야** 통과한다 — `sum 3  size_of::<List>() = 16`. E0072 의 `help:` 는 **맞았지만 미완**이었다(타입 정의만 고쳤다) — **두 바퀴**.

### 3. ★★ `4 8 8 8 16 16 16 8 16 8 16 16 8 8 24` — 보장은 「`Sized` 면 포인터 하나」와 「`Option<Box>` 는 안 커진다」

**출력.**

```text
===== 소스: r40_size.rs =====
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
===== rustc --edition 2021 r40_size.rs =====
(exit 0)
===== ./r40_size =====
i32                          4
&i32                         8
Box<i32>                     8
Box<[i32; 100]>              8
Box<[i32]>                   16
Box<str>                     16
Box<dyn Display>             16
Option<Box<i32>>             8
Option<Box<dyn Display>>     16
Option<i32>                  8
(i32, Box<List>)             16
List                         16
Box<List>                    8
Option<Box<List>>            8
Vec<i32>                     24
(exit 0)
```

- ★★ **std 보장** — `Box<i32>`·`Box<[i32; 100]>`·`Box<List>` 가 **포인터 하나**(`T: Sized` — boxed 모듈 문서) · `Option<Box<i32>>`·`Option<Box<List>>`·`Option<Box<dyn Display>>` 가 **`Box` 와 같은 크기**(Option Representation).
- ★★ **이 판의 구현** — **8 이라는 수**(64비트 포인터) · **`Box<[i32]>`·`Box<str>`·`Box<dyn Display>` 의 16**(Reference Type layout 「기대지 마라」 — 10번) · `List` 16 · `(i32, Box<List>)` 16 · `Vec<i32>` 24(38번 — 「셋」은 보장, 24 는 타깃).
- ★ **`Option<i32>` 8** — `i32` 4 보다 크다. 9번.

### 4. ★★ `[stack] [stack] [heap] (anonymous)` · `true false false`

**출력.**

```text
===== 소스: r40_where.rs =====
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
===== rustc --edition 2021 r40_where.rs =====
(exit 0)
===== ./r40_where =====
local i32         : [stack]
the Box variable  : [stack]
*b (Box<i32> data): [heap]
1 MiB Box<[u8]>   : (anonymous)
same region as local — box variable true · box data false · 1 MiB data false
(exit 0)
```

- ★★ **`local i32` `[stack]` · `the Box variable` `[stack]` · `*b` `[heap]` · `1 MiB Box<[u8]>` `(anonymous)`** — `same region as local — box variable true · box data false · 1 MiB data false`.
- ★★ **보관증(`Box` 변수)은 스택, 물건은 힙.** 1 MiB 는 glibc 가 `[heap]` 이 아닌 **익명 매핑**으로 줬다 — 이름은 환경의 관찰이고, **「스택이 아니다」** 가 결론이다.
- ★ **주소를 안 찍은 이유** — ASLR 로 **실행마다 흔들린다.** 흔들리는 수 대신 **「어느 매핑에 속하나」** 로 질문을 바꿔 **결정적인 답**을 얻었다.

### 5. ★★ `Box::new` 판의 `opt-level=0` 만 `134 134 134` · `1 / 8`

**출력.**

```text
===== 소스: r40_big_grid.sh =====
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
===== bash r40_big_grid.sh =====
source       opt-level        | cc exit | run exit x3
r40_big      -C opt-level=0   | 0       | 134 134 134
r40_big      -C opt-level=1   | 0       | 0 0 0
r40_big      -C opt-level=2   | 0       | 0 0 0
r40_big      -C opt-level=3   | 0       | 0 0 0
r40_big_vec  -C opt-level=0   | 0       | 0 0 0
r40_big_vec  -C opt-level=1   | 0       | 0 0 0
r40_big_vec  -C opt-level=2   | 0       | 0 0 0
r40_big_vec  -C opt-level=3   | 0       | 0 0 0
ulimit -s = 8192
cells whose run exit is not 0 0 0: 1 / 8
(exit 0)
```

**출력 — 그 한 판의 표준 오류.**

```text
===== 소스: r40_big.rs =====
// 16 MiB 배열을 Box::new 로
const N: usize = 16 << 20;

fn main() {
    let b: Box<[u8; N]> = Box::new([7u8; N]);
    eprintln!("len {} first {} last {}", b.len(), b[0], b[N - 1]);
}
===== rustc --edition 2021 -C opt-level=0 -o r40_big_o0 r40_big.rs =====
(exit 0)
===== ./r40_big_o0 =====

thread 'main' (501099) has overflowed its stack
fatal runtime error: stack overflow, aborting
(exit 134)
```

- ★★★ **`r40_big` `-C opt-level=0` 만 `134 134 134`**(SIGABRT) — 나머지 일곱 칸은 `0 0 0`. **`vec!` 판은 네 판 다 0.** 마지막 줄 **`1 / 8`**. 세 번씩 돌려 **칸마다 같았다**(흔들리는 칸이 아니다).
- ★★ 표준 오류 — **「thread 'main' (…) has overflowed its stack」 · 「fatal runtime error: stack overflow, aborting」 · exit 134.** 스레드 id 는 흔들리는 칸이다.

### 6. ★★ `Box` 는 통과 · `Rc` 는 E0507 — 그 `help:` 둘은 둘 다 E0308

**출력 — `Box`.**

```text
===== 소스: r40_move_out.rs =====
fn main() {
    let b: Box<String> = Box::new(String::from("boxed"));
    let s: String = *b;
    println!("s = {s}");
}
===== rustc --edition 2021 r40_move_out.rs =====
(exit 0)
===== ./r40_move_out =====
s = boxed
(exit 0)
```

**출력 — `Rc`.**

```text
===== 소스: r40_move_out_rc.rs =====
use std::rc::Rc;

fn main() {
    let r: Rc<String> = Rc::new(String::from("shared"));
    let s: String = *r;
    println!("{s}");
}
===== rustc --edition 2021 r40_move_out_rc.rs =====
error[E0507]: cannot move out of an `Rc`
 --> r40_move_out_rc.rs:5:21
  |
5 |     let s: String = *r;
  |                     ^^ move occurs because value has type `String`, which does not implement the `Copy` trait
  |
help: consider removing the dereference here
  |
5 -     let s: String = *r;
5 +     let s: String = r;
  |
help: consider cloning the value if the performance cost is acceptable
  |
5 -     let s: String = *r;
5 +     let s: String = r.clone();
  |

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0507`.
(exit 1)
```

**출력 — `help:` ① `*` 를 빼면 · ② `r.clone()`.**

```text
===== 소스: r40_rc_help1.rs =====
use std::rc::Rc;

fn main() {
    let r: Rc<String> = Rc::new(String::from("shared"));
    let s: String = r;
    println!("{s}");
}
===== rustc --edition 2021 r40_rc_help1.rs =====
error[E0308]: mismatched types
 --> r40_rc_help1.rs:5:21
  |
5 |     let s: String = r;
  |            ------   ^ expected `String`, found `Rc<String>`
  |            |
  |            expected due to this
  |
  = note: expected struct `String`
             found struct `Rc<String>`
help: try using a conversion method
  |
5 |     let s: String = r.to_string();
  |                      ++++++++++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0308`.
(exit 1)
```

```text
===== 소스: r40_rc_help2.rs =====
use std::rc::Rc;

fn main() {
    let r: Rc<String> = Rc::new(String::from("shared"));
    let s: String = r.clone();
    println!("{s}");
}
===== rustc --edition 2021 r40_rc_help2.rs =====
error[E0308]: mismatched types
 --> r40_rc_help2.rs:5:21
  |
5 |     let s: String = r.clone();
  |            ------   ^^^^^^^^^ expected `String`, found `Rc<String>`
  |            |
  |            expected due to this
  |
  = note: expected struct `String`
             found struct `Rc<String>`
help: try using a conversion method
  |
5 -     let s: String = r.clone();
5 +     let s: String = r.to_string();
  |

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0308`.
(exit 1)
```

- ★★ **`Box` — 통과**(`s = boxed`). Reference: 옮겨 꺼낼 수 있는 자리에 「**`Box<T>` 를 역참조한 결과**」가 있다 — 다른 포인터는 없다.
- ★★ **`Rc` — E0507 「cannot move out of an `Rc`」.** `help:` ① 「consider removing the dereference」 ② 「consider cloning the value」.
- ★★★ **둘 다 E0308 — 「expected `String`, found `Rc<String>`」.** ①은 `Rc` 째 넣은 것, ②는 **`Rc` 를 복제**한 것이다. **`help:` 둘이 다 틀렸다.** 둘째 `help:`(`r.to_string()`)는 통과하지만 **`Display` 복사**다(서머리 (5)의 `r40_rc_help3`). 뜻에 맞는 길은 **`(*r).clone()`** 이나 **`Rc::try_unwrap`**(주인이 하나일 때만).

### 7. ★★ E0106 → E0106 → 통과(세 바퀴) — 힙을 안 쓰고, 빌린다

**출력.**

```text
===== 소스: r40_rec_ref.rs =====
enum List {
    Cons(i32, &List),
    Nil,
}

fn main() {
    let _l = List::Nil;
}
===== rustc --edition 2021 r40_rec_ref.rs =====
error[E0106]: missing lifetime specifier
 --> r40_rec_ref.rs:2:15
  |
2 |     Cons(i32, &List),
  |               ^ expected named lifetime parameter
  |
help: consider introducing a named lifetime parameter
  |
1 ~ enum List<'a> {
2 ~     Cons(i32, &'a List),
  |

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0106`.
(exit 1)
```

```text
===== 소스: r40_rec_ref_help.rs =====
enum List<'a> {
    Cons(i32, &'a List),
    Nil,
}

fn main() {
    let _l = List::Nil;
}
===== rustc --edition 2021 r40_rec_ref_help.rs =====
error[E0106]: missing lifetime specifier
 --> r40_rec_ref_help.rs:2:19
  |
2 |     Cons(i32, &'a List),
  |                   ^^^^ expected named lifetime parameter
  |
help: consider using the `'a` lifetime
  |
2 |     Cons(i32, &'a List<'a>),
  |                       ++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0106`.
(exit 1)
```

```text
===== 소스: r40_rec_ref_help2.rs =====
enum List<'a> {
    Cons(i32, &'a List<'a>),
    Nil,
}

fn sum(l: &List) -> i32 {
    match l {
        List::Cons(x, rest) => x + sum(rest),
        List::Nil => 0,
    }
}

fn main() {
    let nil = List::Nil;
    let two = List::Cons(2, &nil);
    let one = List::Cons(1, &two);
    println!("sum {}  size_of::<List>() = {}", sum(&one), std::mem::size_of::<List>());
}
===== rustc --edition 2021 r40_rec_ref_help2.rs =====
(exit 0)
===== ./r40_rec_ref_help2 =====
sum 3  size_of::<List>() = 16
(exit 0)
```

- ★★ **`&List` → E0106**(`help:` `enum List<'a>` + `&'a List`) → **E0106**(`help:` `&'a List<'a>`) → **통과**(`sum 3  size_of::<List>() = 16`). **세 바퀴**다.
- ★★ **힙을 안 쓴다** — 노드 셋(`nil`·`two`·`one`)이 전부 `main` 의 지역 변수다. **`Box` 판은 소유(리스트가 노드를 가진다) · `&` 판은 빌림(노드가 먼저 있고 리스트가 그보다 오래 못 산다).** 둘 다 크기는 16 으로 같다.

### 8. ★★ `x` 는 호출 전에 값으로 만들어진다 — 최적화가 그 복사를 없앤 것은 보장이 아니다

- ★★★ **`pub fn new(x: T) -> Box<T>`** — `x` 는 **인자**다. 인자는 **호출 전에 평가되어 값으로 넘어간다**(언어 규칙). 최적화 없는 판에서 `[7u8; N]` 16 MiB 가 **먼저 스택에 만들어져** 스택(8 MiB)을 넘었다 — 5번의 `134`.
- ★★ std 의 말도 순서가 그렇다 — 「**힙에 메모리를 잡은 다음 `x` 를 그 안에 둔다**」.
- ★★ **최적화 판이 안 터진 것은 컴파일러가 스택 경유 복사를 없앤 결과**다 — **보장이 아니다.** 판을 타지 않으려면 **처음부터 힙에** 채우는 `vec![…; N].into_boxed_slice()` 로(5번 — 네 판 다 0).

### 9. ★★ 「절대 안 쓰는 비트 패턴」이 있느냐 — std 가 `Box`·`&`·`fn`·`NonZero`·`NonNull` 에 보장한다

- ★★ **그대로인 줄** — `Option<Box<i32>>` 8 · `Option<Box<List>>` 8 · `Option<Box<dyn Display>>` 16. **커진 줄** — `Option<i32>` 8(`i32` 4).
- ★★★ 가르는 성질은 **틈새(niche)** — `Box` 는 **널이 될 수 없으니** 널 비트 패턴을 `None` 으로 쓴다. `i32` 는 **모든 비트 패턴이 유효한 값**이라 빈자리가 없어 태그를 따로 붙인다.
- ★★ **std 보장**(Option Representation) — 「`Option<T>` 가 `T` 와 같은 크기·정렬·ABI 를 갖도록 최적화함을 보장한다」 — `Box<U>` · `&U` · `&mut U` · **`fn`**·`extern "C" fn` · `num::NonZero*` · `ptr::NonNull<U>` · 이것들을 감싼 `#[repr(transparent)]` 구조체. **35번의 `Option<fn()>` 8 과 같은 표의 같은 규칙**이다.

### 10. ★★ 보장하지 않는다 — DST 절 「두 배」 · Type layout 절 「적어도 포인터 크기, 지금은 두 배, 기대지 마라」

- ★★ **보장하지 않는다.** 33번이 짚은 대로 Reference **DST 절**은 「**두 배 크기**」라고 적고, **Type layout 절**은 「**적어도 포인터 크기**이다. 지금은 모든 DST 포인터가 `usize` 두 배이지만 **기대지 마라**」라고 적는다.
- ★ **뒤쪽이 더 정확하다** — 16 은 **이 판의 구현**이다. 보장은 「`T: Sized` 인 `Box<T>` 는 포인터 하나」와 「`Option<Box<_>>` 는 안 커진다」까지다(3번).

### 11. ★ `Box<dyn Trait>` — 원소 하나 16 · `leak` 은 `'static` 참조를 주고 메모리를 돌려받을 길을 잃는다

**출력.**

```text
===== 소스: r40_hetero.rs =====
// 크기가 다른 타입들을 한 Vec 에 — Box<dyn Trait>
use std::mem::size_of;

trait Shape {
    fn area(&self) -> f64;
    fn label(&self) -> String;
}
struct Sq(f64);
struct Rect(f64, f64);
struct Named {
    side: f64,
    name: String,
}
impl Shape for Sq {
    fn area(&self) -> f64 { self.0 * self.0 }
    fn label(&self) -> String { String::from("sq") }
}
impl Shape for Rect {
    fn area(&self) -> f64 { self.0 * self.1 }
    fn label(&self) -> String { String::from("rect") }
}
impl Shape for Named {
    fn area(&self) -> f64 { self.side * self.side }
    fn label(&self) -> String { self.name.clone() }
}

fn main() {
    let shapes: Vec<Box<dyn Shape>> = vec![
        Box::new(Sq(2.0)),
        Box::new(Rect(2.0, 3.0)),
        Box::new(Named { side: 1.0, name: String::from("tile") }),
    ];
    for s in &shapes {
        print!("{}={} ", s.label(), s.area());
    }
    println!();
    println!("sizes of the values: {} {} {}", size_of::<Sq>(), size_of::<Rect>(), size_of::<Named>());
    println!("size of each element in the Vec: {}", size_of::<Box<dyn Shape>>());
}
===== rustc --edition 2021 r40_hetero.rs =====
(exit 0)
===== ./r40_hetero =====
sq=4 rect=6 tile=1 
sizes of the values: 8 16 32
size of each element in the Vec: 16
(exit 0)
```

**출력 — `Box::leak`.**

```text
===== 소스: r40_leak.rs =====
fn config() -> &'static str {
    let s: String = format!("mode={}", 3);
    Box::leak(s.into_boxed_str())
}

fn main() {
    let c: &'static str = config();
    println!("{c}");
}
===== rustc --edition 2021 r40_leak.rs =====
(exit 0)
===== ./r40_leak =====
mode=3
(exit 0)
```

- ★ **`Vec<Box<dyn Shape>>`** — 값의 크기 `8 16 32` 가 달라도 **원소 하나는 16**(fat pointer). `Box` 가 크기를 **포인터로 바꿔** `Vec` 의 「원소 크기는 하나」를 맞췄다(33번).
- ★ **`Box::leak`** — `Box` 를 먹고 **`&'a mut T`**(여기서는 `'static`)를 준다(`mode=3`). **잃는 것** — 그 메모리를 **돌려받을 주인**이다. std: 「돌려받은 참조를 버리면 **메모리가 샌다**」(되돌리려면 `Box::from_raw` — 이 문서는 던지지 않았다).

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서·서머리의 **모든 블록** | `capture.sh` — 블록마다 명령을 배너에 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` — 기본 규칙 넷(스레드 id 가 걸린다) · **고칠 것 0** |
| ★★★ **E0072 + `help:` 사슬** | `r40_rec` · `r40_rec_nomain` · `r40_rec_help` · `r40_rec_box` · `r40_rec_ref` · `r40_rec_ref_help` · `r40_rec_ref_help2` · `r40_rec_rc` | 8 | **E0072+E0391** · E0072 · **E0308×2** · 통과 · **E0106** · **E0106** · 통과 · 통과 |
| ★★ **`size_of` 격자** | `r40_size` | 1 | 열다섯 줄 |
| ★ 영역 | `r40_where` — `/proc/self/maps` | 1 | `[stack] [stack] [heap] (anonymous)` · `true false false` |
| ★★ **큰 배열 판 격자** | `r40_big_grid.sh` — 소스 둘 × `opt-level` 넷 × 실행 세 번 | 8 컴파일 · 24 실행 | **`1 / 8`** — `Box::new` 의 `opt-level=0` 만 134 |
| 옮겨 꺼내기 | `r40_move_out` · `r40_move_out_rc` · `r40_rc_help1`·`2`·`3` · `r40_rc_ways` | 6 | 통과 · **E0507** · **E0308** · **E0308** · 통과(복사) · 세 길 |
| `dyn` 담기 · `leak` | `r40_hetero` · `r40_leak` | 2 | 원소 16 · `mode=3` |
| **안 던진 것** — 속도 · `Box::new_uninit` · `Box::from_raw` · 다른 `ulimit -s` · 다른 할당기 | — | 0 | ★ 「안 던졌다」로 표시했다 |

**구현 의존 항목**(버전·환경이 바뀌면 **다시 찍어야 하는** 것).

| 항목 | 왜 |
|---|---|
| fat pointer **16** · `List` **16** | ★ Reference 가 「기대지 마라」고 적는다 · 배치는 구현이다 |
| 큰 배열 판 격자의 **어느 칸이 터지나** | ★ 최적화기의 복사 제거와 `ulimit -s` 에 달렸다 |
| 영역 이름 `[heap]`·익명 | ★ OS·할당기(glibc)의 성질 |
| E0391 의 동반 · `help:` 사슬 | ★ 컴파일러의 질의 순서와 진단 제안은 판마다 바뀐다 |

★ **다시 찍는 법** — `capture.sh <새 디렉토리>` 를 그대로 돌리고 `normalize-shaky.py <원본> <새 디렉토리>` 로 견준다.
