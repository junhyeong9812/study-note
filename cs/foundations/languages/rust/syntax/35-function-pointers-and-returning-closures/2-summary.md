# rust/syntax/35 — 함수 포인터와 클로저를 반환하기 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Reference — Function item types](https://doc.rust-lang.org/reference/types/function-item.html) ·
> [Reference — Function pointer types](https://doc.rust-lang.org/reference/types/function-pointer.html) ·
> [Reference — Closure types(non-capturing)](https://doc.rust-lang.org/reference/types/closure.html) ·
> [Reference — Type coercions](https://doc.rust-lang.org/reference/type-coercions.html)(함수 항목 → fn 포인터 · 비포착 클로저 → fn 포인터 · LUB) ·
> [std — primitive `fn`](https://doc.rust-lang.org/std/primitive.fn.html).
> ★ 위 문서는 **이 머신의 `rust-docs`(1.92.0) 로컬 사본**을 열어 읽었다. 버전은 **그 사본의 `releases.md` 를 블록으로** 실었다((0)).
> **실행 검증** — 이 문서의 모든 출력·에러는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서
> **`rustc --edition 2021 <파일>.rs`** 로 돌려 받은 것이다(C++ 대비 블록은 `g++ 13.3.0` · `clang++ 18.1.3`).\
> ★★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다. 소스 펜스도 캡처가 찍었다.\
> ★★ **외부 크레이트를 하나도 쓰지 않았다**(네트워크 없음). ★ **시간은 한 번도 재지 않았다** — 간접 호출 비용은 이 문서의 주장이 아니다.
> **버전** — 비포착 클로저 → `fn` 강제 **1.19.0**((0)). `impl Fn` 반환은 **1.26.0**([32번 주제](../32-impl-trait-argument-return-position-and-2024-capture/) (0)의 블록).
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
| 안 흔들린다 | `size_of` 격자(`fn` 8 · 함수 항목 0 · 비포착 클로저 0 · `Box<dyn Fn>` 16) | 같은 판·같은 타깃에서 고정이다. ★ **함수 항목 0 은 언어 보장**, 나머지는 구현(§구현 세부) |
| 안 흔들린다 | 강제 격자의 칸마다 진단 코드와 `accepted: 3 / 5` | 같은 판에서 고정이다 |
| 안 흔들린다 | `type_name_of_val` 의 **문자열**(`r35_items_name::add1`) | 같은 판에서 고정이지만 std 문서가 **형식을 보장하지 않는다**(32번과 같다) |
| 안 흔들린다 | 에러 번호·제목·`파일:줄:칸`·종료 코드 | 같은 rustc 판에서 고정이다 |

★ 정규화 규칙은 **기본 넷**만 썼고 **하나도 걸리지 않았다**(제출 전 재대조).

## 한눈에 — 쉽게 말하면

**함수 이름은 「그 함수 하나만을 뜻하는 0바이트짜리 표지」이고, `fn(i32) -> i32` 는 「그 모양의 아무 함수나 가리키는 8바이트 주소」다.
아무것도 안 잡은 클로저는 그 주소로 바뀔 수 있고, 무언가를 잡은 클로저는 못 바뀐다 — 잡은 것을 담을 자리가 주소에는 없기 때문이다.**

| 비유 | 실체 |
|---|---|
| 「**그 가게 하나만 가리키는 간판**」 — 무게 없음 | ★★ **함수 항목 타입** `fn(i32) -> i32 {add1}` — **0 바이트**, 함수마다 **다른 타입**((2)) |
| 「**아무 가게나 적을 수 있는 주소록 한 줄**」 | ★★ **함수 포인터** `fn(i32) -> i32` — **8 바이트**, 모양이 같으면 한 타입((1)·(2)) |
| 「**빈손으로 온 손님은 주소록에 적힌다**」 | ★★★ **비포착 클로저 → `fn` 강제** — 잡은 것이 있으면 E0308((3)) |
| 「**짐을 든 손님은 자기 가방째 온다**」 | 잡은 클로저 — 크기 = 잡은 것. `fn` 이 못 된다((2)·(3)) |
| 「**가방을 봉투에 넣어 돌려주기**」 | ★★ **`-> impl Fn`** — 타입 하나. 인자를 잡으려면 **`move`**((4)) |
| 「**서로 다른 가방을 같은 상자에**」 | ★★ **`-> Box<dyn Fn>`** — 갈래마다 다른 클로저를 돌려줄 때((5)) |

- ★★★ **판정은 한 줄이다 — 「잡은 것이 없으면 `fn` 포인터가 될 수 있고, 있으면 트레이트(`impl Fn`/`dyn Fn`)로만 다룬다.」**
  [32번 주제](../32-impl-trait-argument-return-position-and-2024-capture/) (4)가 **분기 두 갈래**에서 이 한 칸을 쟀다 — 안 잡은 클로저 둘은 `fn(i32) -> i32` 로 모여 통과, 잡은 둘은 E0308. **여기는 그것을 격자로 넓힌다**((3)).
- ★★ **클로저를 돌려줄 때 고르는 법** — 갈래가 **하나**면 `impl Fn`(힙 없음, 크기 = 잡은 것), 갈래마다 **다른 클로저**면 `Box<dyn Fn>`(힙 하나 + vtable)((4)·(5)).

```text
   한 값의 크기 — (2)의 블록 그대로 (이 판 · x86_64)

   add1            ← 함수 항목     0 B   타입이 곧 「add1」 — 값에 담을 것이 없다
   fn(i32) -> i32  ← 함수 포인터   8 B   주소 하나
   Option<fn()>                   8 B   널 주소가 None — 틈새
   |x| x + 1       ← 비포착 클로저  0 B   → fn(i32) -> i32 로 강제 가능 ✔
   move |x| x + k  ← k: i32 포착   4 B   → fn 으로 강제 ✘ E0308
   Box<dyn Fn>                   16 B   데이터 포인터 + vtable 포인터 (33번)

   C++ 대비 (r35_lambda)
   [](int x){…}    ← 빈 람다       1 B   ★ C++ 의 빈 클래스는 0 이 못 된다
   [k](int x){…}                  4 B
```

> **함수 항목 타입(function item type)** — 함수 이름을 값으로 쓸 때의 타입. **그 함수 하나를 가리키는 0바이트 타입**이고, 이름을 적는 문법은 없다. 진단에는 `fn(i32) -> i32 {add1}` 로 보인다.\
> 예: `let f = add1;` 의 `f` 는 0바이트다. 호출에 간접이 없다(Reference).

> **함수 포인터(function pointer)** — `fn(i32) -> i32` 타입. 모양이 같은 **어떤 함수든** 담는 주소.\
> 예: `let table: [fn(i32) -> i32; 2] = [add1, dbl];` — 서로 다른 함수를 한 배열에 담는다.

## 이 주제가 답하려는 질문

1. ★★ **`fn` 타입과 클로저 트레이트는 무엇이 다른가** — 함수 항목·함수 포인터·클로저의 **크기와 타입**((1)·(2)).
2. ★★★ **무엇이 `fn` 포인터로 강제되고 무엇이 안 되나**((3)).
3. ★★ **클로저를 돌려줄 때 `impl Fn` 과 `Box<dyn Fn>` 중 무엇을 고르나** — 그리고 인자를 잡으려면 왜 `move` 인가((4)·(5)).

★ **선행** — [**34번 주제**](../34-closures-fn-fnmut-fnonce-and-move/)의 **세 트레이트와 `move`**. 이 주제는 그 사슬의 다음 칸이다 — **E0373 이 스레드가 아니라 반환에서** 나온다((4)).
[**32번 주제**](../32-impl-trait-argument-return-position-and-2024-capture/) (4)가 **반환 `impl Trait` 의 분기 E0308** 과 **함수 포인터로 모이는 예외**를 봤고 `help:` 가 `Box<dyn Fn>` 을 권하는 데서 멈췄다 — **여기는 그 `Box<dyn>` 쪽으로 푼다**((5)).
[**33번 주제**](../33-dyn-trait-objects-and-object-safety/)의 **넓은 포인터 16바이트**가 `Box<dyn Fn>` 에 그대로 온다.

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ② 강제 격자다

★★★ **본체 창 — ② 「무엇을 `fn(i32) -> i32` 자리에 넣을 수 있나」 격자.** 스크립트가 마지막 줄에 **`accepted: N / 5`** 를 찍는다.

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ① **`size_of`·`size_of_val`** | 함수 항목·포인터·클로저·`Box<dyn Fn>` 이 **몇 바이트**인가((2)) | 쓴다 |
| ② ★★★ **`fn` 강제 격자** | 값마다 **`let f: fn(i32) -> i32 = …` 가 되나**((3)) | ★ **본체** |
| ③ **E0308 전문의 `note:`** | 안 되는 이유를 **컴파일러가 무엇이라 말하나**((2)·(3)) | 쓴다 |
| ④ **`type_name_of_val`** | 함수 항목과 포인터의 **타입 이름**((2)) | 쓴다 — 「같은 질문을 다른 창으로」 |
| ⑤ **C++ `sizeof` · 변환** | 람다가 `operator()` 를 가진 **익명 클래스**인 것((6)) | 대비로 쓴다 |
| 실행 시간 | `fn` 포인터·`dyn Fn` 의 간접 호출 비용 | ★ **부적용 — 재지 않는다** |
| 단형화 벌 수 | `impl Fn` 인자가 클로저마다 찍히는 것 | ★ **부적용 — 31번이 정본** |

★ **「같은 질문을 다른 창으로」(제5의 상태)** — 「`add1` 과 `dbl` 은 같은 타입인가」를 **타입 검사기**에 물으면 **E0308 로 「아니다」** 를 말하고((2)),
같은 질문을 **`type_name_of_val`** 에 물으면 `r35_items_name::add1` · `r35_items_name::dbl` 이라는 **다른 이름**으로 답한다.
★ **이 창이 못 보는 것** — `type_name_of_val` 은 함수 항목을 **함수의 경로**로만 적어 **그것이 0바이트 타입이라는 것**은 말하지 않는다. 크기는 ① 창이 말한다.

**버전 — 설치된 `releases.md` 에서 뽑았다.**

```text
===== awk '/^Version 1\./{v=$2} /Non capturing closures can now be coerced/{print v " | " $0}' "$(rustc --print sysroot)/share/doc/rust/html/releases.md" =====
1.19.0 | - [Non capturing closures can now be coerced into `fn`s,][42162] [RFC 1558]
(exit 0)
```

### (1) 함수를 값으로 — `fn` 포인터와 클로저 트레이트 자리

**언제 쓰나** — **함수 표**(디스패치 테이블)를 만들거나, C 쪽 콜백처럼 **주소 하나**가 필요할 때.

```rust
// r35_fnptr.rs
// 함수를 값으로 — fn 포인터 타입에 담고, 클로저 트레이트 자리에도 넘긴다
fn add1(x: i32) -> i32 {
    x + 1
}
fn dbl(x: i32) -> i32 {
    x * 2
}

fn apply_ptr(f: fn(i32) -> i32, x: i32) -> i32 {
    f(x)
}
fn apply_fn(f: impl Fn(i32) -> i32, x: i32) -> i32 {
    f(x)
}

fn main() {
    let table: [fn(i32) -> i32; 2] = [add1, dbl];
    let outs: Vec<i32> = table.iter().map(|f| f(10)).collect();
    println!("{:?}", outs);
    println!("{} {}", apply_ptr(add1, 1), apply_fn(dbl, 1));
    println!("{}", apply_ptr(|x| x - 1, 1));
}
```

```text
===== rustc --edition 2021 r35_fnptr.rs =====
(exit 0)
===== ./r35_fnptr =====
[11, 20]
2 2
0
(exit 0)
```

- `[fn(i32) -> i32; 2]` 에 **서로 다른 두 함수**가 담겼다 — `[11, 20]`.
- ★★ **`apply_fn(dbl, 1)` 도 통과** — 함수(와 함수 포인터)는 **`Fn`·`FnMut`·`FnOnce` 를 전부 구현한다.** 그래서 **클로저 트레이트 자리에 함수를 넘겨도 된다.**
- ★ **`apply_ptr(|x| x - 1, 1)` 도 통과**(`0`) — 비포착 클로저가 **`fn` 포인터 인자로 강제**됐다((3)).

### (2) ★★ 크기와 타입 — 함수 항목은 0바이트, 함수마다 다른 타입

**언제 쓰나** — `fn` 포인터와 `impl Fn` 중 무엇으로 받을지, 무엇을 담을지 고를 때.

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

```text
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

- ★★★ **함수 항목 `add1` 은 0 · 함수 포인터는 8.** 같은 `add1` 인데 **`let item = add1;`** 은 0바이트, **`let ptr: fn(i32) -> i32 = add1;`** 은 8바이트다.
  Reference 가 직접 적는다 — 함수 항목은 「**0 크기 값**」이고 「**그 타입이 함수를 명시적으로 식별하므로 실제 함수 포인터를 담을 필요가 없고, 부를 때 간접이 필요 없다**」.
- ★ **`Option<fn()>` 도 8** — std 문서가 `fn` 포인터는 「**널이 아니라고 가정된다**」고 적는다. 그래서 널 자리를 `None` 으로 쓴다(33번의 `Option<&dyn>` 과 같은 틈새).
- ★★ **비포착 클로저 0 · `move` 로 `i32` 를 잡으면 4 · `Box<dyn Fn>` 16** — 클로저 크기는 34번 (5)의 격자와 같은 이야기이고, `Box<dyn Fn>` 은 33번 (1)의 **넓은 포인터**다.

**두 함수를 한 변수에 차례로.**

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

```text
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

- ★★ **E0308 — `expected fn item, found a different fn item`.** `note:` 둘이 이유를 적는다 —
  「**expected fn item `fn(_) -> _ {add1}` / found fn item `fn(_) -> _ {dbl}`**」 · 「**different fn items have unique types, even if their signatures are the same**」.
  **시그니처가 같아도 함수마다 타입이 다르다** — 그래서 0바이트가 될 수 있다(타입이 곧 「어느 함수인가」이므로).

**`help:` 대로 — 처음 값을 `fn` 포인터로.**

```rust
// r35_items_help.rs
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
```

```text
===== rustc --edition 2021 r35_items_help.rs =====
(exit 0)
===== ./r35_items_help =====
2
2
(exit 0)
```

- ★ **통과 — `2` · `2`.** 「**consider casting both fn items to fn pointers using `as fn(i32) -> i32`**」 — 첫 값만 캐스팅했는데 둘째 `f = dbl;` 은 **강제**로 들어갔다. 이 `help:` 는 **맞았다**(「둘 다」가 아니어도 됐다).

**타입 이름을 물으면.**

```rust
// r35_items_name.rs
// 같은 두 함수 — 타입 이름을 물어본다
use std::any::type_name_of_val;

fn add1(x: i32) -> i32 {
    x + 1
}
fn dbl(x: i32) -> i32 {
    x * 2
}

fn main() {
    println!("{}", type_name_of_val(&add1));
    println!("{}", type_name_of_val(&dbl));
    let p: fn(i32) -> i32 = add1;
    println!("{}", type_name_of_val(&p));
    println!("{}", p(1) + dbl(1));
}
```

```text
===== rustc --edition 2021 r35_items_name.rs =====
(exit 0)
===== ./r35_items_name =====
r35_items_name::add1
r35_items_name::dbl
fn(i32) -> i32
4
(exit 0)
```

- ★ **함수 항목은 경로(`r35_items_name::add1`), 포인터는 모양(`fn(i32) -> i32`)** 으로 이름이 나온다. 앞 두 줄이 **다르다는 것** — 타입이 다르다는 것 — 이 E0308 과 같은 답이다.

### (3) ★★★ 강제 격자 — 무엇이 `fn` 포인터가 되나

**언제 쓰나** — 콜백 자리를 `fn(…)` 으로 적어 둔 API 에 **클로저를 넘길 수 있는지** 판정할 때.

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

```text
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

- ★★★ **받는 칸 3 / 5.** `fn_item`·`closure_no_capture`·**`closure_static`** 이 되고, **지역 변수 `k` 를 쓰는 둘**이 E0308 이다.
- ★★ **`move` 가 있어도 없어도 같다** — `closure_reads_local`(`move`)과 `closure_ref_local`(빌림)이 **둘 다** 막혔다. 막는 것은 **포착 방식이 아니라 포착했다는 사실**이다.
- ★★ **`closure_static` 은 `move` 가 있는데도 통과**(`6 5`) — `K` 는 **`const`** 라 **환경이 아니다**(포착 대상이 아니다). 「비포착」은 **바깥 이름을 안 쓴다**가 아니라 **지역 변수를 안 잡는다**다.

**잡은 쪽의 에러 전문.**

```rust
// r35_capture.rs
// 환경을 잡은 클로저를 fn 포인터 자리에
fn main() {
    let k = 5;
    let f: fn(i32) -> i32 = |x| x + k;
    println!("{}", f(1));
}
```

```text
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

- ★★★ **E0308 — `expected fn pointer, found closure`.** `note:` 가 규칙을 그대로 말한다 — 「**closures can only be coerced to `fn` types if they do not capture any variables**」, 그리고 **`` `k` captured here ``** 로 잡은 자리를 짚는다.
- ★ 이유 — `fn` 포인터는 **주소 하나**(8바이트)라 **잡은 `k` 를 둘 자리가 없다.** 잡은 클로저는 **잡은 것의 구조체**이고(34번 (5)), 그 구조체를 받으려면 **`impl Fn`·`dyn Fn`** 으로 받아야 한다.

### (4) ★★ 클로저를 돌려주기 — `impl Fn`, 그리고 `move`

**언제 쓰나** — **설정값을 품은 함수**를 만들어 돌려줄 때(가산기·필터·핸들러 공장).

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

```text
===== rustc --edition 2021 r35_ret_impl.rs =====
(exit 0)
===== ./r35_ret_impl =====
11 21
4
(exit 0)
```

- ★ **`adder(10)`·`adder(20)` 이 서로 다른 `n` 을 품는다** — `11 21`. 반환값의 크기는 **4**(잡은 `i32` 하나) — **힙도 vtable 도 없다.**
- ★ `a` 와 `b` 는 **같은 타입**이다(같은 함수의 같은 클로저 식) — 그래서 `impl Fn` 하나로 된다.

**`move` 를 빼면.**

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

```text
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

- ★★ **E0373 — closure may outlive the current function, but it borrows `n`.** `note:` 가 「**closure is returned here**」. 34번 (4)의 E0373 은 **스레드**에서였고, 이번엔 **반환**이다 — **같은 규칙의 두 번째 자리**다.
  `|x| x + n` 은 `n` 을 **빌리는데**, `n` 은 `adder` 가 끝나면 **사라진다.**
- ★ `help:` 가 `move |x| x + n` 을 권한다 — `r35_ret_impl` 이 그 판이다(**맞은 처방**).

### (5) ★★ 갈래마다 다른 클로저 — `impl Fn` 은 막히고 `Box<dyn Fn>` 은 된다

**언제 쓰나** — 설정에 따라 **다른 동작**을 돌려줄 때.

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

```text
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

- ★★ **E0308 — `` `if` and `else` have incompatible types `` · `no two closures, even if identical, have the same type`.** [32번 주제](../32-impl-trait-argument-return-position-and-2024-capture/) (4)와 **같은 에러**다.
  `impl Fn` 은 **숨긴 타입 하나**인데 두 클로저는 **다른 타입**이다.
- ★★ **`help:` 가 두 개다** — ① 「**you could change the return type to be a boxed trait object**」 ② 「**if you change the return type to expect trait objects, box the returned expressions**」.

**첫 처방만 따르면.**

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

```text
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

- ★★★ **다시 E0308 두 건** — 「**expected `Box<dyn Fn(i32) -> i32>`, found closure**」. **반환 타입만 바꾸면 안 된다** — 클로저가 **`Box` 로 자동 포장되지 않는다.** 새 `help:` 가 이번엔 **`Box::new(…)`** 를 권한다.
  **앞 에러의 둘째 `help:` 까지 따라야** 끝난다 — 한 진단의 `help:` 는 **묶음**으로 읽어야 한다.
- ★ 진단이 반환 타입을 **`Box<(dyn Fn(i32) -> i32 + 'static)>`** 로 풀어 적는다 — 33번 (6)의 **기본 수명 `'static`** 이 여기 숨어 있다.

**두 처방을 다 따르면.**

```rust
// r35_ret_branch.rs
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
```

```text
===== rustc --edition 2021 r35_ret_branch.rs =====
(exit 0)
===== ./r35_ret_branch =====
[13, 30]
(exit 0)
```

- ★★ **통과 — `[13, 30]`.** 두 갈래가 **같은 타입 `Box<dyn Fn(i32) -> i32>`** 이 되어 한 배열에도 담겼다.
  **대가는 힙 할당 하나와 vtable 을 거치는 호출**이다 — **이 문서는 그 비용을 재지 않았다.**
- ★ **안 잡는 클로저 둘이면 `fn` 포인터로도 된다** — 32번 (4)의 `r32_branch_fnptr` 이 그 판이다(힙 없이 8바이트). 이 문서는 다시 던지지 않았다.

### (6) C++ 람다 — `operator()` 를 가진 익명 클래스

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

```text
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

- ★★ **C++ 의 빈 람다는 1 바이트**(두 컴파일러 같다) — **C++ 의 모든 완전 객체는 크기가 0 이 못 된다.** Rust 의 비포착 클로저는 **0** 이다((2)).
- ★ **캡처한 람다 4 · 함수 포인터 8** — Rust 와 같은 모양이다. **`same type(none, other) 0`** — 글자가 같은 두 람다가 **다른 타입**이다. Rust 의 「no two closures, even if identical, have the same type」과 같은 규칙이다.

```cpp
// r35_lambda_cap.cpp
// C++ — 캡처한 람다를 함수 포인터에
int main() {
    int k = 5;
    auto cap = [k](int x) { return x + k; };
    int (*p)(int) = cap;
    return p(1);
}
```

```text
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

- ★ **캡처한 람다 → 함수 포인터는 C++ 도 거절한다** — g++ 「cannot convert」, clang++ 「no viable conversion」. 비포착 람다만 함수 포인터로 변환된다(`int (*p)(int) = none;` 이 통과했다).
  C++ 쪽 정본은 C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md))의 **22번**(`operator()`) 이다.

## 문법 — 형태와 규칙

```text
   형태

   fn apply(f: fn(i32) -> i32, x: i32) -> i32      ← fn 포인터 인자 — 비포착 클로저·함수만
   fn apply(f: impl Fn(i32) -> i32, x: i32) -> i32 ← 트레이트 인자 — 함수·클로저 전부
   let table: [fn(i32) -> i32; 2] = [add1, dbl];   ← 함수 표
   let mut f = add1 as fn(i32) -> i32;             ← 함수 항목을 포인터로 캐스팅
   fn adder(n: i32) -> impl Fn(i32) -> i32 { move |x| x + n }         ← 갈래 하나
   fn op(…) -> Box<dyn Fn(i32) -> i32> { if … { Box::new(…) } else { Box::new(…) } }   ← 갈래 여럿


   금지 사례 — 던져서 받은 것

   let f: fn(i32) -> i32 = |x| x + k;   (k 는 지역)      ✘ E0308  "closures can only be coerced … do not capture"
   let mut f = add1;  f = dbl;                          ✘ E0308  "different fn items have unique types"
   fn adder(n) -> impl Fn … { |x| x + n }               ✘ E0373  "closure is returned here"
   -> impl Fn … { if … { move |x| … } else { move |x| … } }   ✘ E0308  "no two closures … have the same type"
   -> Box<dyn Fn …> { if … { move |x| … } … }  (Box::new 없음)  ✘ E0308  "found closure"
```

**규칙 불릿.**

- ★★ **함수 항목은 함수마다 다른 0바이트 타입** — 같은 자리에 두 함수를 담으려면 `fn` 포인터로(강제·캐스팅)((2)).
- ★★★ **비포착 클로저만 `fn` 포인터로 강제된다** — `move` 여부와 무관, `const` 는 포착이 아니다((3)).
- ★ **함수·함수 포인터는 `Fn`·`FnMut`·`FnOnce` 를 전부 구현한다** — 트레이트 자리에 그냥 넘긴다((1)).
- ★★ **인자를 잡은 클로저를 돌려주려면 `move`** — 아니면 E0373((4)).
- ★★ **갈래가 여럿이면 `Box<dyn Fn>` + 갈래마다 `Box::new`** — 반환 타입만 바꾸면 다시 E0308((5)).

## 어디서 틀리나

### 1. ★★★ 「`help:` 대로 반환 타입을 `Box<dyn Fn>` 으로 바꾸면 끝난다」

**다시 E0308 두 건이다**((5)). 클로저는 **자동으로 `Box` 에 안 들어간다.** 첫 진단의 **둘째 `help:`**(「box the returned expressions」)까지 따라야 한다.

### 2. ★★ 「`move` 를 붙이면 `fn` 포인터가 된다」 / 「`move` 가 없으면 된다」

**둘 다 틀리다**((3)). 격자에서 **`move` 판과 빌림 판이 같이 막혔다.** 가르는 것은 **지역 변수를 잡았느냐** 하나다. 반대로 **`move` 가 있어도 `const` 만 쓰면 된다.**

### 3. ★★ 「함수 이름을 변수에 담으면 함수 포인터다」

**함수 항목이다 — 0바이트, 함수마다 다른 타입**((2)). 그래서 `let mut f = add1; f = dbl;` 이 **E0308** 이다. 포인터가 되는 것은 **`fn(…)` 자리를 만났을 때**(강제)나 **`as` 캐스팅**이다.

### 4. ★ 「`fn` 포인터 인자면 클로저를 못 넘긴다」

**비포착 클로저는 넘어간다**((1)의 `apply_ptr(|x| x - 1, 1)`). 못 넘어가는 것은 **잡은 클로저**다.

### 5. ★ 「클로저를 돌려주려면 언제나 `Box` 가 필요하다」

**갈래가 하나면 `impl Fn` 으로 힙 없이 된다**((4) — 반환값 4바이트). `Box<dyn Fn>` 은 **갈래마다 다른 클로저**거나 **여러 클로저를 한 컨테이너에 담을 때**다.

### 6. ★ 「C++ 도 빈 람다는 0 바이트」

**1 바이트다**((6)). C++ 객체는 크기가 0 이 못 된다. Rust 의 비포착 클로저·함수 항목은 **0** 이다.

## 구현 세부사항 대 언어 보장

| 항목 | 무엇인가 | 근거 |
|---|---|---|
| ★★ **함수 항목이 0 크기**이고 **함수마다 다른 타입** | ★ **언어 보장** — Reference(Function item types) 「zero-sized value」「distinct」 | (2)의 0 · E0308 |
| 함수 항목 → `fn` 포인터 **강제**(분기의 LUB 포함) | ★ **언어 보장** — Reference(coercion · function item) | (2)의 `help:` 판 · (1) |
| ★★★ **비포착 클로저 → `fn` 포인터 강제** | ★ **언어 보장** — Reference(Closure types · coercion) · **1.19.0** | (3)의 격자 |
| `fn` 포인터가 **8바이트** · `Option<fn()>` 도 8 | ★ 8 은 **구현 세부**(포인터 폭) · **널이 아니라고 가정된다**는 것은 std 문서(`fn` 원시 타입 — 「FFI 에서 널을 받으려면 `Option<fn()>`」) | (2) |
| **클로저 크기**(0 · 4) | ★ **구현 세부** — Reference 「클로저는 레이아웃 보장이 없다」 | (2)·(4) |
| `Box<dyn Fn>` 16 | ★ **구현 세부** — 33번 (1)의 넓은 포인터 | (2) |
| 두 클로저가 **글자가 같아도 다른 타입** | ★ **언어 보장** — 클로저마다 고유 익명 타입(Reference) | (5)의 E0308 |
| `help:` 문구 · 처방이 **묶음**으로 나오는 것 | ★ **구현 세부** — 진단의 제안 | (2)·(4)·(5) |
| `type_name_of_val` 문자열 | ★ **구현 세부** — std 가 형식을 보장하지 않는다 | (2) |
| C++ 빈 람다 1 바이트 | ★ **C++ 언어 규칙**(완전 객체의 크기는 0 이 아니다)의 결과 — 이 문서는 C++ 표준 조항을 인용하지 않았다(관찰) | (6) |

## 언제 쓰고 언제 안 쓰나

- ★ **`fn` 포인터로 받는다** — **함수 표**, **FFI 콜백**, 받는 쪽이 **상태를 안 받는다고 못 박고 싶을 때.** 비포착 클로저도 들어온다.
- ★★ **`impl Fn` 으로 받는다** — 대부분의 콜백. 잡은 클로저도 받고, 단형화로 **호출이 직접**이 된다(31번의 벌 수 대가).
- ★ **`&dyn Fn`/`Box<dyn Fn>` 으로 받는다** — 한 컨테이너에 **여러 클로저**를 담거나, 단형화 벌 수를 **한 벌로** 묶고 싶을 때.
- ★★ **돌려줄 때** — 갈래 하나면 **`impl Fn` + `move`**, 갈래 여럿이면 **`Box<dyn Fn>` + 갈래마다 `Box::new`**. 안 잡는 갈래뿐이면 **`fn` 포인터**도 된다(32번 (4)).

## 핵심 문장

- ★★★ **잡은 것이 없는 클로저만 `fn` 포인터가 된다** — 격자 **3 / 5**, `move` 여부는 무관, `const` 는 포착이 아니다((3)).
- ★★ **함수 이름은 0바이트짜리 고유 타입이고, `fn(…)` 는 8바이트 주소다**((2)).
- ★★ **인자를 품은 클로저를 돌려주려면 `move`** — 반환 자리의 E0373((4)).
- ★★ **갈래마다 다른 클로저는 `Box<dyn Fn>` 으로** — 반환 타입과 **갈래의 `Box::new` 둘 다** 필요하다((5)).
- ★ **C++ 도 같은 규칙을 갖는다** — 캡처한 람다는 함수 포인터가 못 된다. 다만 **빈 람다는 1 바이트**다((6)).

## 관련 자료

- ★★ [**34번 주제** — 클로저 세 종류와 `move`](../34-closures-fn-fnmut-fnonce-and-move/) — **경계**: 세 트레이트 판정과 `move` 의 뜻은 **거기**다. 여기는 **`fn` 으로의 강제**와 **돌려주기**만 다뤘다.
- ★★ [**32번 주제** — `impl Trait`](../32-impl-trait-argument-return-position-and-2024-capture/) (4) — **분기 E0308 과 함수 포인터 예외**의 첫 실측. **경계**: 그 한 칸은 거기서 쟀고 여기는 **격자**와 **`Box<dyn>` 풀이**를 더했다.
- [**33번 주제** — `dyn Trait`](../33-dyn-trait-objects-and-object-safety/) — `Box<dyn Fn>` 의 16바이트와 기본 수명 `'static`.
- [**36번 주제** — `Iterator`](../36-iterator-adapters-laziness-and-collect/) — 어댑터에 넘기는 클로저·함수(`map(add1)` 도 된다 — 함수가 `FnMut` 을 구현하므로).
- ★ C++ 대비 — C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md))의 **22번**(연산자 오버로딩 · `operator()`). (6)은 크기와 변환 **두 칸**만 쟀다.

## 용어 풀이

- **함수 항목 타입(function item type)** — 함수 하나를 가리키는 0 크기 타입. 이름을 적는 문법이 없고, 진단에 `fn(…) -> … {이름}` 으로 보인다.
- **함수 포인터(function pointer)** — `fn(…) -> …` 타입. 같은 모양의 어떤 함수든 담는 주소.
- **강제(coercion)** — 컴파일러가 **자동으로** 해 주는 타입 변환. 함수 항목 → 포인터, 비포착 클로저 → 포인터 등.
- **비포착 클로저(non-capturing closure)** — 지역 변수를 하나도 안 잡은 클로저. `const`·`static`·함수 이름을 쓰는 것은 포착이 아니다.
- **LUB 강제(least upper bound)** — `if`/`match` 갈래들의 **공통 타입**을 찾는 강제. 두 함수 항목은 `fn` 포인터로 모인다.
- **`Box<dyn Fn>`** — 클로저를 힙에 두고 vtable 로 부르는 트레이트 객체.

## 더 들어가면

- **`extern "C" fn`·`unsafe fn` 포인터** — FFI 콜백의 타입. 1.35 에서 **클로저를 `unsafe fn` 포인터로 강제**할 수 있게 됐다(릴리스 노트 — 이 문서는 던지지 않았다). 목록의 **56번 주제**(`unsafe`) 근처.
- **`fn` 포인터의 비교·주소** — 이 문서는 주소를 한 번도 찍지 않았다(찍으면 흔들리는 칸이 된다).
- **`impl Fn` 을 돌려주는 함수는 호출마다 같은 타입** — (4)의 `a`·`b` 가 그렇다. **다른 함수가 돌려준 클로저**와는 한 컨테이너에 섞을 수 없다(그때가 `Box<dyn>`) — 이 문서는 그 컨테이너 판을 던지지 않았다.
