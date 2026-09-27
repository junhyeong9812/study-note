# rust/syntax/35 — 함수 포인터와 클로저를 반환하기 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 던지는 법 — `rustc --edition 2021 <파일>.rs`. **외부 크레이트를 하나도 쓰지 않는다.**
> ★★★ **함수·클로저를 값으로 다룰 때 두 가지를 먼저 물어라** — 「**이것은 무엇을 잡았나**」와 「**받는 자리가 주소(`fn`)인가 트레이트(`impl Fn`/`dyn Fn`)인가**」.
> ★ **문항 10개 중 코드가 붙은 예측형은 6개**다. 소스 펜스는 캡처가 실파일에서 찍었다(`check-source-fences.py` 대조).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ 한 값의 바이트 (예측)

```rust
// r35_size.rs
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
```

- 앞의 여덟 줄은 각각 몇인가? 특히 첫 두 줄 — 같은 `add1` 인데 같은 값인가?
- ★ `Option<fn()>` 과 `fn()` 의 크기 관계는? 그 이유를 std 문서는 어떻게 적는가?

### 2. ★★★ `fn(i32) -> i32` 자리에 넣을 수 있는 것 (예측)

```bash
# r35_coerce_grid.sh
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
```

- 다섯 줄 각각 `ok` 인가, 무슨 코드인가? 마지막 줄의 수는?
- ★★ `closure_reads_local` 과 `closure_ref_local` 은 `move` 한 단어가 다르다. 결과도 다른가?
- ★★ `closure_static` 은 `move` 가 있고 바깥 이름 `K` 를 쓴다. 결과는? 왜?

### 3. ★★ 두 함수를 한 변수에 차례로 (예측)

```rust
// r35_items.rs
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
```

- 컴파일되는가? 에러면 번호와, `note:` 가 두 함수의 타입을 **각각 어떻게 적는가**?
- ★ `help:` 를 따르면 통과하는가?

### 4. ★★ 인자를 잡는 클로저를 돌려주기 (예측)

```rust
// r35_ret_impl.rs
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
```

```rust
// r35_ret_nomove.rs
// 같은 함수에서 move 를 빼면
fn adder(n: i32) -> impl Fn(i32) -> i32 {
    |x| x + n
}

fn main() {
    println!("{}", adder(10)(1));
}
```

- 앞 소스의 출력 두 줄은? 반환값은 몇 바이트이고 힙을 쓰는가?
- 뒤 소스는? 에러면 번호와 `note:` 가 짚는 자리는? [34번](../34-closures-fn-fnmut-fnonce-and-move/)의 같은 번호와 **무엇이 다른가**?

### 5. ★★★ 갈래마다 다른 클로저 — 첫 처방만 (예측)

```rust
// r35_ret_branch_impl.rs
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
```

```rust
// r35_ret_branch_help.rs
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
```

- 앞 소스의 에러 번호와 `help:` 는 **몇 개**의 처방을 주는가?
- ★★★ 뒤 소스는 그 **첫 처방만** 따른 판이다. 컴파일되는가? 안 되면 몇 건이고 새 `help:` 는 무엇을 권하는가?
- ★ 진단이 반환 타입을 풀어 적을 때 **보이지 않던 수명**이 드러나는가?

### 6. ★★ C++ 람다 (예측)

```cpp
// r35_lambda.cpp
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
```

- 네 `sizeof` 줄과 `same type` 줄은? 특히 **빈 람다**의 크기는 Rust 의 비포착 클로저와 같은가?
- ★ 캡처한 람다를 `int (*)(int)` 에 넣으면 두 컴파일러는 무엇이라 말할까?

### 7. ★★ 함수 항목과 함수 포인터 (왜)

- `let f = add1;` 의 `f` 와 `let p: fn(i32) -> i32 = add1;` 의 `p` 는 **무엇이 다른가**? 크기가 다른 이유를 Reference 는 어떻게 적는가?
- ★ `type_name_of_val` 은 두 값의 타입을 각각 어떻게 적는가 — 그 창이 **못 보는 것**은?

### 8. 함수를 클로저 트레이트 자리에 (경계)

- `fn apply(f: impl Fn(i32) -> i32, …)` 에 함수 `dbl` 을 넘길 수 있는가? `fn apply_ptr(f: fn(i32) -> i32, …)` 에 비포착 클로저는?

### 9. ★★ `impl Fn` 과 `Box<dyn Fn>` 중 무엇을 (경계)

- 돌려줄 클로저가 **하나의 식**이면 무엇을 고르나? **갈래마다 다르면**? 각각의 대가는?
- ★ 안 잡는 클로저 둘이면 셋째 길이 있다 — 무엇이고, 어느 편이 그것을 쟀나?

### 10. 32번과 34번에서 무엇을 이었나 (연결)

- [32번](../32-impl-trait-argument-return-position-and-2024-capture/) (4)가 잰 것과 이 주제의 강제 격자는 어떻게 이어지는가?
- [34번](../34-closures-fn-fnmut-fnonce-and-move/)의 E0373 과 이 주제의 E0373 은 **같은 규칙의 어느 두 자리**인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
