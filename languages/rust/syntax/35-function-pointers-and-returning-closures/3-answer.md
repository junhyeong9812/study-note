# rust/syntax/35 — 함수 포인터와 클로저를 반환하기 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서
> **`rustc --edition 2021`** 로 실제로 돌려 받은 것이다(C++ 블록은 `g++ 13.3.0` · `clang++ 18.1.3`).\
> ★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
> ★★ 블록 첫 줄 `===== 소스: <파일> =====` 아래가 **컴파일한 소스 전문**이고, **진단의 줄 번호는 그 파일 기준**이다.\
> ★★ **외부 크레이트를 하나도 쓰지 않았다**(네트워크 없음). **시간은 한 번도 재지 않았다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ 함수 항목 0 · 함수 포인터 8

**출력.**

```text
===== 소스: r35_size.rs =====
// fn 항목 · fn 포인터 · 클로저 · 트레이트 객체 — 하나에 몇 바이트인가
use std::mem::{size_of, size_of_val};

fn add1(x: i32) -> i32 {
    x + 1
}

fn main() {
    let k: i32 = 5;
    let item = add1;
    let ptr: fn(i32) -> i32 = add1;
    let no_cap = |x: i32| x + 1;
    let cap_i32 = move |x: i32| x + k;
    let boxed: Box<dyn Fn(i32) -> i32> = Box::new(cap_i32);
    println!("fn item (add1)          {}", size_of_val(&item));
    println!("fn(i32) -> i32          {}", size_of_val(&ptr));
    println!("size_of::<fn()>()       {}", size_of::<fn()>());
    println!("Option<fn()>            {}", size_of::<Option<fn()>>());
    println!("closure, no capture     {}", size_of_val(&no_cap));
    println!("closure, move i32       {}", size_of_val(&cap_i32));
    println!("Box<dyn Fn(i32) -> i32> {}", size_of_val(&boxed));
    println!("&dyn Fn(i32) -> i32     {}", size_of::<&dyn Fn(i32) -> i32>());
    println!("{}", item(1) + ptr(1) + no_cap(1) + boxed(1));
}
===== rustc --edition 2021 r35_size.rs =====
(exit 0)
===== ./r35_size =====
fn item (add1)          0
fn(i32) -> i32          8
size_of::<fn()>()       8
Option<fn()>            8
closure, no capture     0
closure, move i32       4
Box<dyn Fn(i32) -> i32> 16
&dyn Fn(i32) -> i32     16
12
(exit 0)
```

**왜 그런가.**

- ★★★ **첫 두 줄이 다르다 — `add1` 을 그대로 담으면 0, `fn(i32) -> i32` 로 담으면 8.** 함수 항목은 **타입이 곧 「어느 함수인가」** 라 값에 담을 것이 없다(Reference 「zero-sized value」).
- ★ **`size_of::<fn()>()` 8 · `Option<fn()>` 8** — std 문서가 함수 포인터는 「**널이 아니라고 가정된다**」고 적어 널 자리를 `None` 으로 쓴다.
- ★ 비포착 클로저 **0** · `i32` 를 잡은 클로저 **4** · `Box<dyn Fn>`·`&dyn Fn` **16**(33번의 넓은 포인터).

### 2. ★★★ 3 / 5 — 막는 것은 「지역 변수를 잡았다」 하나

**출력.**

```text
===== 소스: r35_coerce_grid.sh =====
# 무엇을 `fn(i32) -> i32` 자리에 넣을 수 있나 — 칸: 통과면 ok, 에러면 진단 코드
cases=(
  'fn_item|add1'
  'closure_no_capture||x| x + 1'
  'closure_reads_local|move |x| x + k'
  'closure_ref_local||x| x + k'
  'closure_static|move |x| x + K'
)
ok=0 total=0
printf '%-20s %-18s | %s\n' case value 'let f: fn(i32) -> i32 = value;'
for c in "${cases[@]}"; do
  name=${c%%|*} val=${c#*|}
  printf 'const K: i32 = 5;\nfn add1(x: i32) -> i32 {\n    x + 1\n}\nfn main() {\n    let k = 5;\n    let f: fn(i32) -> i32 = %s;\n    println!("{} {}", f(1), k);\n}\n' "$val" >g.rs
  if rustc --edition 2021 -A warnings --crate-name g g.rs -o g 2>g.err; then
    r="ok -> $(./g)"; ok=$((ok + 1))
  else
    r=$(grep -m1 -oE '^error\[E[0-9]+\]' g.err | sed -E 's/error\[(.*)\]/\1/')
  fi
  total=$((total + 1))
  printf '%-20s %-18s | %s\n' "$name" "$val" "$r"
done
rm -f g.rs g.err g
echo "accepted: $ok / $total"
===== bash r35_coerce_grid.sh =====
case                 value              | let f: fn(i32) -> i32 = value;
fn_item              add1               | ok -> 2 5
closure_no_capture   |x| x + 1          | ok -> 2 5
closure_reads_local  move |x| x + k     | E0308
closure_ref_local    |x| x + k          | E0308
closure_static       move |x| x + K     | ok -> 6 5
accepted: 3 / 5
(exit 0)
```

**출력 — 잡은 쪽 전문.**

```text
===== 소스: r35_capture.rs =====
// 환경을 잡은 클로저를 fn 포인터 자리에
fn main() {
    let k = 5;
    let f: fn(i32) -> i32 = |x| x + k;
    println!("{}", f(1));
}
===== rustc --edition 2021 r35_capture.rs =====
error[E0308]: mismatched types
 --> r35_capture.rs:4:29
  |
4 |     let f: fn(i32) -> i32 = |x| x + k;
  |            --------------   ^^^^^^^^^ expected fn pointer, found closure
  |            |
  |            expected due to this
  |
  = note: expected fn pointer `fn(i32) -> i32`
                found closure `{closure@r35_capture.rs:4:29: 4:32}`
note: closures can only be coerced to `fn` types if they do not capture any variables
 --> r35_capture.rs:4:37
  |
4 |     let f: fn(i32) -> i32 = |x| x + k;
  |                                     ^ `k` captured here

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0308`.
(exit 1)
```

**왜 그런가.**

- ★★★ **`accepted: 3 / 5`** — `fn_item`·`closure_no_capture`·`closure_static` 이 ok, **`k` 를 쓰는 둘이 E0308.**
- ★★ **`move` 판과 빌림 판이 둘 다 막혔다** — 포착 **방식**이 아니라 포착 **여부**가 가른다. `note:` 「**closures can only be coerced to `fn` types if they do not capture any variables**」 · 「`` `k` captured here ``」.
- ★★ **`closure_static` 은 통과(`6 5`)** — `K` 는 `const` 라 **환경이 아니다.** `move` 가 있어도 잡을 것이 없다.

### 3. ★★ E0308 — 함수마다 타입이 다르다

**출력.**

```text
===== 소스: r35_items.rs =====
// 두 함수를 한 변수에 차례로 담기
fn add1(x: i32) -> i32 {
    x + 1
}
fn dbl(x: i32) -> i32 {
    x * 2
}

fn main() {
    let mut f = add1;
    println!("{}", f(1));
    f = dbl;
    println!("{}", f(1));
}
===== rustc --edition 2021 r35_items.rs =====
error[E0308]: mismatched types
  --> r35_items.rs:12:9
   |
10 |     let mut f = add1;
   |                 ---- expected due to this value
11 |     println!("{}", f(1));
12 |     f = dbl;
   |         ^^^ expected fn item, found a different fn item
   |
   = note: expected fn item `fn(_) -> _ {add1}`
              found fn item `fn(_) -> _ {dbl}`
   = note: different fn items have unique types, even if their signatures are the same
   = help: consider casting both fn items to fn pointers using `as fn(i32) -> i32`

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0308`.
(exit 1)
```

**출력 — `help:` 대로.**

```text
===== 소스: r35_items_help.rs =====
// help: 가 권한 대로 — 처음 값을 fn 포인터로 캐스팅
fn add1(x: i32) -> i32 {
    x + 1
}
fn dbl(x: i32) -> i32 {
    x * 2
}

fn main() {
    let mut f = add1 as fn(i32) -> i32;
    println!("{}", f(1));
    f = dbl;
    println!("{}", f(1));
}
===== rustc --edition 2021 r35_items_help.rs =====
(exit 0)
===== ./r35_items_help =====
2
2
(exit 0)
```

**왜 그런가.**

- ★★ **E0308 — `expected fn item, found a different fn item`.** `note:` 가 **`fn(_) -> _ {add1}`** 과 **`fn(_) -> _ {dbl}`** 로 적는다 — 중괄호 안의 **함수 이름이 타입의 일부**다. 「**different fn items have unique types, even if their signatures are the same**」.
- ★ **`help:` 대로 첫 값을 `as fn(i32) -> i32` 로 캐스팅하면 통과**(`2` · `2`) — 둘째 `f = dbl;` 은 **강제**로 들어간다. 이 처방은 **맞았다.**

### 4. ★★ `11 21` · 4바이트 · 힙 없음 — `move` 를 빼면 E0373

**출력 — `move` 판.**

```text
===== 소스: r35_ret_impl.rs =====
// 클로저를 돌려주기 — 인자 n 을 잡는다
fn adder(n: i32) -> impl Fn(i32) -> i32 {
    move |x| x + n
}

fn main() {
    let a = adder(10);
    let b = adder(20);
    println!("{} {}", a(1), b(1));
    println!("{}", std::mem::size_of_val(&a));
}
===== rustc --edition 2021 r35_ret_impl.rs =====
(exit 0)
===== ./r35_ret_impl =====
11 21
4
(exit 0)
```

**출력 — `move` 없이.**

```text
===== 소스: r35_ret_nomove.rs =====
// 같은 함수에서 move 를 빼면
fn adder(n: i32) -> impl Fn(i32) -> i32 {
    |x| x + n
}

fn main() {
    println!("{}", adder(10)(1));
}
===== rustc --edition 2021 r35_ret_nomove.rs =====
error[E0373]: closure may outlive the current function, but it borrows `n`, which is owned by the current function
 --> r35_ret_nomove.rs:3:5
  |
3 |     |x| x + n
  |     ^^^     - `n` is borrowed here
  |     |
  |     may outlive borrowed value `n`
  |
note: closure is returned here
 --> r35_ret_nomove.rs:3:5
  |
3 |     |x| x + n
  |     ^^^^^^^^^
help: to force the closure to take ownership of `n` (and any other referenced variables), use the `move` keyword
  |
3 |     move |x| x + n
  |     ++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0373`.
(exit 1)
```

**왜 그런가.**

- ★ **`11 21`, 반환값 4바이트** — 잡은 `i32` 하나다. **힙도 vtable 도 없다**(`impl Fn` 은 숨긴 타입이 곧 그 클로저).
- ★★ **E0373** — 「closure may outlive the current function, but it borrows `n`」, `note:` 「**closure is returned here**」.
  [34번](../34-closures-fn-fnmut-fnonce-and-move/)의 E0373 은 **스레드**(`'static` 요구)에서, 여기는 **반환**에서다. `help:` 의 `move` 가 둘 다 맞았다.

### 5. ★★★ 첫 처방만 따르면 E0308 두 건 — `help:` 는 묶음이다

**출력 — `impl Fn` 두 갈래.**

```text
===== 소스: r35_ret_branch_impl.rs =====
// 같은 두 갈래를 impl Fn 으로 돌려주면
fn op(kind: &str, n: i32) -> impl Fn(i32) -> i32 {
    if kind == "add" {
        move |x| x + n
    } else {
        move |x| x * n
    }
}

fn main() {
    println!("{}", op("add", 3)(10));
}
===== rustc --edition 2021 r35_ret_branch_impl.rs =====
error[E0308]: `if` and `else` have incompatible types
 --> r35_ret_branch_impl.rs:6:9
  |
3 | /     if kind == "add" {
4 | |         move |x| x + n
  | |         --------------
  | |         |
  | |         the expected closure
  | |         expected because of this
5 | |     } else {
6 | |         move |x| x * n
  | |         ^^^^^^^^^^^^^^ expected closure, found a different closure
7 | |     }
  | |_____- `if` and `else` have incompatible types
  |
  = note: expected closure `{closure@r35_ret_branch_impl.rs:4:9: 4:17}`
             found closure `{closure@r35_ret_branch_impl.rs:6:9: 6:17}`
  = note: no two closures, even if identical, have the same type
  = help: consider boxing your closure and/or using it as a trait object
help: you could change the return type to be a boxed trait object
  |
2 - fn op(kind: &str, n: i32) -> impl Fn(i32) -> i32 {
2 + fn op(kind: &str, n: i32) -> Box<dyn Fn(i32) -> i32> {
  |
help: if you change the return type to expect trait objects, box the returned expressions
  |
4 ~         Box::new(move |x| x + n)
5 |     } else {
6 ~         Box::new(move |x| x * n)
  |

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0308`.
(exit 1)
```

**출력 — 반환 타입만 `Box<dyn Fn>`.**

```text
===== 소스: r35_ret_branch_help.rs =====
// help: 가 권한 첫 처방 — 반환 타입을 Box<dyn Fn> 으로 바꾼다
fn op(kind: &str, n: i32) -> Box<dyn Fn(i32) -> i32> {
    if kind == "add" {
        move |x| x + n
    } else {
        move |x| x * n
    }
}

fn main() {
    println!("{}", op("add", 3)(10));
}
===== rustc --edition 2021 r35_ret_branch_help.rs =====
error[E0308]: mismatched types
 --> r35_ret_branch_help.rs:4:9
  |
2 | fn op(kind: &str, n: i32) -> Box<dyn Fn(i32) -> i32> {
  |                              ----------------------- expected `Box<(dyn Fn(i32) -> i32 + 'static)>` because of return type
3 |     if kind == "add" {
4 |         move |x| x + n
  |         ^^^^^^^^^^^^^^ expected `Box<dyn Fn(i32) -> i32>`, found closure
  |
  = note: expected struct `Box<(dyn Fn(i32) -> i32 + 'static)>`
            found closure `{closure@r35_ret_branch_help.rs:4:9: 4:17}`
  = note: for more on the distinction between the stack and the heap, read https://doc.rust-lang.org/book/ch15-01-box.html, https://doc.rust-lang.org/rust-by-example/std/box.html, and https://doc.rust-lang.org/std/boxed/index.html
help: store this in the heap by calling `Box::new`
  |
4 |         Box::new(move |x| x + n)
  |         +++++++++              +

error[E0308]: mismatched types
 --> r35_ret_branch_help.rs:6:9
  |
2 | fn op(kind: &str, n: i32) -> Box<dyn Fn(i32) -> i32> {
  |                              ----------------------- expected `Box<(dyn Fn(i32) -> i32 + 'static)>` because of return type
...
6 |         move |x| x * n
  |         ^^^^^^^^^^^^^^ expected `Box<dyn Fn(i32) -> i32>`, found closure
  |
  = note: expected struct `Box<(dyn Fn(i32) -> i32 + 'static)>`
            found closure `{closure@r35_ret_branch_help.rs:6:9: 6:17}`
  = note: for more on the distinction between the stack and the heap, read https://doc.rust-lang.org/book/ch15-01-box.html, https://doc.rust-lang.org/rust-by-example/std/box.html, and https://doc.rust-lang.org/std/boxed/index.html
help: store this in the heap by calling `Box::new`
  |
6 |         Box::new(move |x| x * n)
  |         +++++++++              +

error: aborting due to 2 previous errors

For more information about this error, try `rustc --explain E0308`.
(exit 1)
```

**출력 — 갈래마다 `Box::new` 까지.**

```text
===== 소스: r35_ret_branch.rs =====
// 조건에 따라 서로 다른 클로저를 돌려주기 — 반환을 Box<dyn Fn> 으로
fn op(kind: &str, n: i32) -> Box<dyn Fn(i32) -> i32> {
    if kind == "add" {
        Box::new(move |x| x + n)
    } else {
        Box::new(move |x| x * n)
    }
}

fn main() {
    let fs = [op("add", 3), op("mul", 3)];
    let outs: Vec<i32> = fs.iter().map(|f| f(10)).collect();
    println!("{:?}", outs);
}
===== rustc --edition 2021 r35_ret_branch.rs =====
(exit 0)
===== ./r35_ret_branch =====
[13, 30]
(exit 0)
```

**왜 그런가.**

- **앞은 E0308** — 「`if` and `else` have incompatible types」「no two closures, even if identical, have the same type」. `help:` 는 **두 개** — ① 반환 타입을 `Box<dyn Fn(i32) -> i32>` 로 ② **돌려주는 식을 `Box::new` 로 감싸라**.
- ★★★ **첫 처방만 따른 판은 E0308 두 건** — 「**expected `Box<dyn Fn(i32) -> i32>`, found closure**」. 클로저는 **자동으로 `Box` 에 안 들어간다.** 새 `help:` 가 `Box::new(…)` 를 권한다. **둘 다 따라야** `[13, 30]` 이 나온다.
- ★ **보이지 않던 수명** — 진단이 반환 타입을 **`Box<(dyn Fn(i32) -> i32 + 'static)>`** 로 풀어 적는다. [33번](../33-dyn-trait-objects-and-object-safety/) (6)의 기본 수명이다.

### 6. ★★ 빈 람다는 1 바이트 — 캡처한 람다는 함수 포인터가 못 된다

**출력.**

```text
===== 소스: r35_lambda.cpp =====
// C++ — 람다의 크기, 함수 포인터로의 변환, 두 람다의 타입
#include <cstdio>
#include <type_traits>

int add1(int x) { return x + 1; }

int main() {
    int k = 5;
    auto none = [](int x) { return x + 1; };
    auto cap = [k](int x) { return x + k; };
    auto other = [](int x) { return x + 1; };
    int (*p)(int) = none;
    std::printf("sizeof(none)  %zu\n", sizeof(none));
    std::printf("sizeof(cap)   %zu\n", sizeof(cap));
    std::printf("sizeof(p)     %zu\n", sizeof(p));
    std::printf("same type(none, other) %d\n", (int)std::is_same_v<decltype(none), decltype(other)>);
    std::printf("%d %d %d %d\n", none(1), cap(1), other(1), p(1) + add1(0));
}
===== g++ -std=c++20 -Wall -Wextra r35_lambda.cpp -o r35_lambda_g =====
(exit 0)
===== ./r35_lambda_g =====
sizeof(none)  1
sizeof(cap)   4
sizeof(p)     8
same type(none, other) 0
2 6 2 3
(exit 0)
===== clang++ -std=c++20 -Wall -Wextra r35_lambda.cpp -o r35_lambda_c =====
(exit 0)
===== ./r35_lambda_c =====
sizeof(none)  1
sizeof(cap)   4
sizeof(p)     8
same type(none, other) 0
2 6 2 3
(exit 0)
```

**출력 — 캡처한 람다를 함수 포인터에.**

```text
===== 소스: r35_lambda_cap.cpp =====
// C++ — 캡처한 람다를 함수 포인터에
int main() {
    int k = 5;
    auto cap = [k](int x) { return x + k; };
    int (*p)(int) = cap;
    return p(1);
}
===== g++ -std=c++20 -Wall -Wextra -c r35_lambda_cap.cpp -o r35_lambda_cap.o =====
r35_lambda_cap.cpp: In function ‘int main()’:
r35_lambda_cap.cpp:5:21: error: cannot convert ‘main()::<lambda(int)>’ to ‘int (*)(int)’ in initialization
    5 |     int (*p)(int) = cap;
      |                     ^~~
      |                     |
      |                     main()::<lambda(int)>
(exit 1)
===== clang++ -std=c++20 -Wall -Wextra -c r35_lambda_cap.cpp -o r35_lambda_cap.o =====
r35_lambda_cap.cpp:5:11: error: no viable conversion from '(lambda at r35_lambda_cap.cpp:4:16)' to 'int (*)(int)'
    5 |     int (*p)(int) = cap;
      |           ^         ~~~
1 error generated.
(exit 1)
```

- ★★ **`sizeof(none)` 1 · `cap` 4 · `p` 8 · `same type 0`** — 두 컴파일러가 같다. **C++ 는 빈 객체도 0 이 못 된다**(Rust 의 비포착 클로저는 0).
- ★ **캡처한 람다 → 함수 포인터는 둘 다 거절** — g++ 「**cannot convert**」, clang++ 「**no viable conversion**」. 비포착 람다만 변환된다(`int (*p)(int) = none;` 은 통과). Rust 의 2번 답과 **같은 규칙**이다.

### 7. ★★ 타입이 함수를 식별하느냐, 값이 주소를 들고 있느냐

- ★★ **`f` 는 함수 항목**(0바이트, `add1` 만을 뜻하는 고유 타입), **`p` 는 함수 포인터**(8바이트 주소, 모양이 같은 어떤 함수든). Reference — 함수 항목은 「**그 타입이 함수를 명시적으로 식별하므로 실제 함수 포인터를 담을 필요가 없고, 부를 때 간접이 필요 없다**」.
- ★ **`type_name_of_val`** 은 `r35_items_name::add1` · `r35_items_name::dbl` · `fn(i32) -> i32` 로 적는다(서머리 (2)). **못 보는 것 — 크기.** 「0바이트 타입」이라는 것은 `size_of_val` 이 말한다.

### 8. 둘 다 된다

- ★ **`apply_fn(dbl, 1)` 통과** — 함수는 `Fn`·`FnMut`·`FnOnce` 를 구현한다. **`apply_ptr(|x| x - 1, 1)` 통과** — 비포착 클로저가 `fn` 포인터로 강제된다(서머리 (1): `[11, 20]` · `2 2` · `0`).

### 9. ★★ 하나면 `impl Fn`, 여럿이면 `Box<dyn Fn>`

- ★★ **식 하나 → `impl Fn`** — 힙 없음, 크기 = 잡은 것(4번 답 4바이트). **갈래마다 다르면 → `Box<dyn Fn>`** — 힙 할당 하나 + vtable 을 거친 호출(**재지 않았다**).
- ★ **셋째 길 — `fn` 포인터.** 안 잡는 클로저 둘은 `fn(i32) -> i32` 로 모여 **힙 없이 8바이트**로 돌려줄 수 있다. [32번](../32-impl-trait-argument-return-position-and-2024-capture/) (4)의 `r32_branch_fnptr` 이 그것을 쟀다.

### 10. 한 칸을 격자로, 같은 규칙의 두 자리

- ★★ [32번](../32-impl-trait-argument-return-position-and-2024-capture/) (4)는 **분기 두 갈래**에서 「안 잡으면 `fn` 으로 모이고 잡으면 E0308」을 **한 칸** 쟀다. 이 주제는 그것을 **`let f: fn(…) = …` 의 다섯 칸 격자**로 넓혀 **`move` 무관 · `const` 는 포착 아님**을 더했다.
- ★ **E0373 의 두 자리** — 「빌린 것을 잡은 클로저가 **주인보다 오래 산다**」는 한 규칙이 **스레드(34번)** 와 **반환(여기)** 에서 나온다. 처방도 같은 **`move`** 다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서·서머리의 **모든 블록** | `capture.sh` — 블록마다 명령을 배너에 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` — **흔들린 칸 0 · 고칠 것 0** |
| 버전 | `r35_versions` — 설치된 `releases.md` | 1 | **1.19.0** |
| 값으로서의 함수 | `r35_fnptr` | 1 | `[11, 20]` · `2 2` · `0` |
| ★★ 크기 | `r35_size` | 1 | 0 · 8 · 8 · 8 · 0 · 4 · 16 · 16 |
| ★★★ **강제 격자** | `r35_coerce_grid` · `r35_capture` | 6 컴파일 | **3 / 5** · E0308 |
| 함수 항목 | `r35_items` · `r35_items_help` · `r35_items_name` | 3 | **E0308** · `help:` 대로 통과 · 이름 둘 |
| 반환 | `r35_ret_impl` · `r35_ret_nomove` | 2 | `11 21` · 4 · **E0373** |
| ★★ 갈래 | `r35_ret_branch_impl` · `r35_ret_branch_help` · `r35_ret_branch` | 3 | **E0308** · 첫 처방만 **E0308 ×2** · 통과 `[13, 30]` |
| C++ 대비 | `r35_lambda` · `r35_lambda_cap` — g++ · clang++ | 4 | 1 · 4 · 8 · 0 · 두 컴파일러 거절 |
| **안 던진 것** — 실행 시간 · `unsafe fn` 강제 · `fn` 포인터 비교 · 다른 함수의 클로저를 섞는 컨테이너 | — | 0 | ★ 「안 던졌다」로 표시했다 |

**구현 의존 항목**(버전·환경이 바뀌면 **다시 찍어야 하는** 것).

| 항목 | 왜 |
|---|---|
| `fn` 포인터 8 · `Box<dyn Fn>` 16 · 클로저 크기 | ★ 포인터 폭과 레이아웃은 구현이다(함수 항목 0 만 언어 보장) |
| `help:` 문구와 **묶음** 구성 | ★ 진단의 제안 |
| `type_name_of_val` 문자열 | ★ std 가 형식을 보장하지 않는다 |

★ **다시 찍는 법** — `capture.sh <새 디렉토리>` 를 그대로 돌리고 `normalize-shaky.py <원본> <새 디렉토리>` 로 견준다.
