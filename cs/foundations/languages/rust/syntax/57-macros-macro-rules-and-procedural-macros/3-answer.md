# rust/syntax/57 — 매크로: `macro_rules!` 맛보기와 절차 매크로의 자리 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `cargo 1.92.0` · `x86_64-unknown-linux-gnu`** 에서, C 대비는 **`gcc 13.3.0 -std=gnu17 -Wall -Wextra`** 로 실제로 돌려 받은 것이다.\
> ★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
> ★★ 블록 첫 줄 `===== 소스: <파일> =====` 아래가 **돌린 소스 전문**이고, **진단의 줄 번호는 그 파일 기준**이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 함수 판이 갈린 칸 `6 / 7` — 에러 넷(E0061 · E0308 · E0425 · E0401) · 다른 답 둘(`text` · `return`)

**출력**

```text
===== 소스: r57_grid.sh =====
# For each row: the same job written as a macro_rules! macro (m_<row>.rs) and as a plain function (f_<row>.rs).
# Each file is compiled with rustc --edition 2021 and, if it compiles, run.
set -u
R="rustc --edition 2021"

w() { cat > "$1"; }   # write stdin to file

# 1 variadic
w m_variadic.rs <<'EOF'
macro_rules! my_vec { ($($x:expr),*) => { { let mut v = Vec::new(); $(v.push($x);)* v } }; }
fn main() { println!("{:?}", my_vec![1, 2, 3]); }
EOF
w f_variadic.rs <<'EOF'
fn my_vec(x: i32) -> Vec<i32> { vec![x] }
fn main() { println!("{:?}", my_vec(1, 2, 3)); }
EOF

# 2 mixed types, one call
w m_mixed.rs <<'EOF'
macro_rules! show_all { ($($x:expr),*) => { $(println!("{:?}", $x);)* }; }
fn main() { show_all!(1, "two", 3.5); }
EOF
w f_mixed.rs <<'EOF'
fn show_all(xs: &[i32]) { for x in xs { println!("{:?}", x); } }
fn main() { show_all(&[1, "two", 3.5]); }
EOF

# 3 an item whose name is written at the call
w m_ident.rs <<'EOF'
macro_rules! make_fn { ($name:ident) => { fn $name() -> &'static str { stringify!($name) } }; }
make_fn!(hello);
fn main() { println!("{}", hello()); }
EOF
w f_ident.rs <<'EOF'
fn make_fn(name: &str) { let _ = name; }
fn main() { make_fn(hello); println!("{}", hello()); }
EOF

# 4 the code text itself
w m_text.rs <<'EOF'
macro_rules! show { ($e:expr) => { println!("{} = {}", stringify!($e), $e) }; }
fn main() { let a = 2; show!(a * 3 + 1); }
EOF
w f_text.rs <<'EOF'
fn show(v: i32) { println!("{} = {}", v, v) }
fn main() { let a = 2; show(a * 3 + 1); }
EOF

# 5 early return on None
w m_return.rs <<'EOF'
macro_rules! or_zero { ($e:expr) => { match $e { Some(v) => v, None => return 0 } }; }
fn half_plus_one(x: Option<i32>) -> i32 { let v = or_zero!(x); println!("reached with {v}"); v / 2 + 1 }
fn main() { println!("{} {}", half_plus_one(Some(8)), half_plus_one(None)); }
EOF
w f_return.rs <<'EOF'
fn or_zero(o: Option<i32>) -> i32 { match o { Some(v) => v, None => return 0 } }
fn half_plus_one(x: Option<i32>) -> i32 { let v = or_zero(x); println!("reached with {v}"); v / 2 + 1 }
fn main() { println!("{} {}", half_plus_one(Some(8)), half_plus_one(None)); }
EOF

# 6 one impl per listed type
w m_impls.rs <<'EOF'
trait Bits { fn bits() -> u32; }
macro_rules! impl_bits { ($($t:ty),*) => { $(impl Bits for $t { fn bits() -> u32 { <$t>::BITS } })* }; }
impl_bits!(u8, u16, u64);
fn main() { println!("{} {} {}", u8::bits(), u16::bits(), u64::bits()); }
EOF
w f_impls.rs <<'EOF'
trait Bits { fn bits() -> u32; }
fn impl_bits<T>() { impl Bits for T { fn bits() -> u32 { 0 } } }
fn main() { impl_bits::<u8>(); println!("{}", u8::bits()); }
EOF

# 7 square a number
w m_square.rs <<'EOF'
macro_rules! square { ($e:expr) => { { let v = $e; v * v } }; }
fn main() { let a = 3; println!("{}", square!(a + 1)); }
EOF
w f_square.rs <<'EOF'
fn square(v: i32) -> i32 { v * v }
fn main() { let a = 3; println!("{}", square(a + 1)); }
EOF

# run one file: prints "<exit>|<first error code or output>"
one() {
  local f=$1 b=${1%.rs} code
  if $R "$f" -o "$b" 2>"$b.err"; then
    printf 'runs: %s' "$(./"$b" | paste -sd'/')"
  else
    code=$(grep -o '^error\[E[0-9]*\]' "$b.err" | head -1 | tr -d 'error[]')
    printf 'compile error %s' "${code:-(no code)}"
  fi
}

printf '%-9s | %-28s | %s\n' row macro function
n=0 differ=0
for row in variadic mixed ident text return impls square; do
  n=$((n + 1))
  m=$(one "m_$row.rs")
  f=$(one "f_$row.rs")
  [ "$m" != "$f" ] && differ=$((differ + 1))
  printf '%-9s | %-28s | %s\n' "$row" "$m" "$f"
done
echo "rows where the function result differs from the macro result: $differ / $n"
===== bash r57_grid.sh =====
row       | macro                        | function
variadic  | runs: [1, 2, 3]              | compile error E0061
mixed     | runs: 1/"two"/3.5            | compile error E0308
ident     | runs: hello                  | compile error E0425
text      | runs: a * 3 + 1 = 7          | runs: 7 = 7
return    | runs: reached with 8/5 0     | runs: reached with 8/reached with 0/5 1
impls     | runs: 8 16 64                | compile error E0401
square    | runs: 16                     | runs: 16
rows where the function result differs from the macro result: 6 / 7
(exit 0)
```

**왜 그런가**

- ★★★ **함수는 값을 받는다** — 개수가 서명에 고정(E0061) · 슬라이스는 원소 타입 하나(E0308) · **이름**을 못 받는다(E0425) · 함수 몸통의 `impl` 은 함수의 타입 인자를 못 쓴다(E0401).
- ★★★ **컴파일되는데 답이 다른 둘** — `text`: 함수는 계산된 `7` 만 받는다(`7 = 7`) · `return`: 함수의 `return` 은 **자기만** 빠져나와 호출한 쪽이 계속 돈다(`reached with 0` 이 찍히고 `5 1`).
- ★ `square` 만 같다 — **함수로 되면 함수를 쓴다.**

### 2. ★★★ Rust `120` · C `1110` · gcc 가 `main` 의 `x`(6행)를 「unused variable」로 짚는다

**출력**

```text
===== 소스: r57_hygiene.rs =====
macro_rules! times_ten_plus_x {
    ($e:expr) => {{
        let x = 100;
        $e * 10 + x
    }};
}

fn main() {
    let x = 1;
    println!("{}", times_ten_plus_x!(x + 1));
}
===== rustc --edition 2021 r57_hygiene.rs =====
(exit 0)
===== ./r57_hygiene =====
120
(exit 0)
```

```text
===== 소스: r57_hygiene.c =====
#include <stdio.h>

#define TIMES_TEN_PLUS_X(e) ({ int x = 100; (e) * 10 + x; })

int main(void) {
    int x = 1;
    printf("%d\n", TIMES_TEN_PLUS_X(x + 1));
    return 0;
}
===== gcc -std=gnu17 -Wall -Wextra r57_hygiene.c -o r57_hygiene =====
r57_hygiene.c: In function ‘main’:
r57_hygiene.c:6:9: warning: unused variable ‘x’ [-Wunused-variable]
    6 |     int x = 1;
      |         ^
(exit 0)
===== ./r57_hygiene =====
1110
(exit 0)
```

**왜 그런가**

- ★★★ Rust 의 `$e`(= `x + 1`)는 **부른 쪽의 `x`(1)** 를 가리킨다 → `2 * 10 + 100`. C 는 글자를 붙여 넣어 매크로 안의 `int x = 100` 이 가렸다 → `101 * 10 + 100`.
- ★★ gcc 경고가 **부른 쪽 `x` 가 한 번도 안 쓰였다**는 것을 말한다 — C 갈래 [42번](../../../c/syntax/42-function-like-macro-pitfalls/)의 「위생이 없다」와 같은 사고.

### 3. ★★★ 앞은 E0425(`y` 없음) · 뒤는 `5`

**출력**

```text
===== 소스: r57_hygiene_out.rs =====
macro_rules! declare_y {
    () => {
        let y = 5;
    };
}

fn main() {
    declare_y!();
    println!("{y}");
}
===== rustc --edition 2021 r57_hygiene_out.rs =====
error[E0425]: cannot find value `y` in this scope
 --> r57_hygiene_out.rs:9:16
  |
9 |     println!("{y}");
  |                ^ not found in this scope

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0425`.
(exit 1)
```

```text
===== 소스: r57_hygiene_ident.rs =====
macro_rules! declare {
    ($name:ident) => {
        let $name = 5;
    };
}

fn main() {
    declare!(y);
    println!("{y}");
}
===== rustc --edition 2021 r57_hygiene_ident.rs =====
(exit 0)
===== ./r57_hygiene_ident =====
5
(exit 0)
```

**왜 그런가**

- ★★★ 매크로가 **스스로 만든** `let y` 는 매크로 쪽 이름이라 바깥에서 안 보인다. **`$name:ident` 로 건네받은** `y` 는 부른 쪽이 쓴 글자라 부른 쪽 이름이다 → 바깥에서 보인다.

### 4. ★★ 안 된다 — 「cannot find macro `twice` in this scope」 + 「a macro with the same name exists, but it appears later」 · 경고 `unused macro definition`

**출력**

```text
===== 소스: r57_order.rs =====
fn main() {
    println!("{}", twice!(4));
}

macro_rules! twice {
    ($e:expr) => {
        $e * 2
    };
}
===== rustc --edition 2021 r57_order.rs =====
error: cannot find macro `twice` in this scope
 --> r57_order.rs:2:20
  |
2 |     println!("{}", twice!(4));
  |                    ^^^^^ consider moving the definition of `twice` before this call
  |
note: a macro with the same name exists, but it appears later
 --> r57_order.rs:5:14
  |
5 | macro_rules! twice {
  |              ^^^^^

warning: unused macro definition: `twice`
 --> r57_order.rs:5:14
  |
5 | macro_rules! twice {
  |              ^^^^^
  |
  = note: `#[warn(unused_macros)]` (part of `#[warn(unused)]`) on by default

error: aborting due to 1 previous error; 1 warning emitted

(exit 1)
```

**왜 그런가**

- ★★ `macro_rules!` 는 **텍스트 스코프** — 소스에 나온 **순서**대로 보인다(Reference). 함수와 달리 정의가 부르는 줄보다 **위에** 있어야 한다. ★ 에러 번호가 없다.

### 5. ★★★ 컴파일 중 표준 오류 네 줄(`input :` · `output:` × 2) · 실행하면 `hello from Point` · `hello from Color`

**출력**

```text
===== 소스: r57_use.rs =====
use r57_hello_pm::Hello;

#[derive(Hello)]
struct Point {
    x: i32,
}

#[derive(Hello)]
enum Color {
    Red,
}

fn main() {
    println!("{}", Point::hello());
    println!("{}", Color::hello());
    let _ = (Point { x: 1 }.x, Color::Red);
}
===== 소스: r57_hello_pm.rs =====
use proc_macro::TokenStream;

#[proc_macro_derive(Hello)]
pub fn derive_hello(input: TokenStream) -> TokenStream {
    let text = input.to_string();
    eprintln!("[derive(Hello)] input : {text}");
    let mut words = text.split_whitespace();
    let mut name = "";
    while let Some(w) = words.next() {
        if w == "struct" || w == "enum" {
            name = words.next().unwrap_or("");
            break;
        }
    }
    let out = format!("impl {name} {{ pub fn hello() -> &'static str {{ \"hello from {name}\" }} }}");
    eprintln!("[derive(Hello)] output: {out}");
    out.parse().unwrap()
}
===== rustc --edition 2021 --crate-type proc-macro --extern proc_macro r57_hello_pm.rs =====
(exit 0)
===== rustc --edition 2021 --extern r57_hello_pm=libr57_hello_pm.so r57_use.rs =====
[derive(Hello)] input : struct Point { x: i32, }
[derive(Hello)] output: impl Point { pub fn hello() -> &'static str { "hello from Point" } }
[derive(Hello)] input : enum Color { Red, }
[derive(Hello)] output: impl Color { pub fn hello() -> &'static str { "hello from Color" } }
(exit 0)
===== ./r57_use =====
hello from Point
hello from Color
(exit 0)
```

**왜 그런가**

- ★★★ 절차 매크로는 **컴파일러가 컴파일 도중에 부르는 Rust 함수**다 — 그래서 `eprintln!` 이 `rustc … r57_use.rs` 단계의 표준 오류로 나온다. `input` 은 **구조체·열거형 정의 전체의 토큰**, `output` 은 **그 뒤에 덧붙을 `impl`** 이다.
- ★★ `derive` 는 원래 아이템을 **지우지 않는다** — `Point { x: 1 }.x` 가 그대로 쓰였다.

### 6. ★★★ 앞 — 「can't use a procedural macro from the same crate that defines it」 · 뒤 — 「the `#[proc_macro_derive]` attribute is only usable with crates of the `proc-macro` crate type」

**출력**

```text
===== 소스: r57_same.rs =====
use proc_macro::TokenStream;

#[proc_macro_derive(Hello)]
pub fn derive_hello(_input: TokenStream) -> TokenStream {
    TokenStream::new()
}

#[derive(Hello)]
struct Point;
===== rustc --edition 2021 --crate-type proc-macro --extern proc_macro r57_same.rs =====
error: can't use a procedural macro from the same crate that defines it
 --> r57_same.rs:8:10
  |
8 | #[derive(Hello)]
  |          ^^^^^

error: aborting due to 1 previous error

(exit 1)
```

```text
===== 소스: r57_notpm.rs =====
extern crate proc_macro;
use proc_macro::TokenStream;

#[proc_macro_derive(Hello)]
pub fn derive_hello(_input: TokenStream) -> TokenStream {
    TokenStream::new()
}
===== rustc --edition 2021 --crate-type lib r57_notpm.rs =====
error: the `#[proc_macro_derive]` attribute is only usable with crates of the `proc-macro` crate type
 --> r57_notpm.rs:4:1
  |
4 | #[proc_macro_derive(Hello)]
  | ^^^^^^^^^^^^^^^^^^^^^^^^^^^

error: aborting due to 1 previous error

(exit 1)
```

**왜 그런가**

- ★★★ Reference — 절차 매크로는 「must be defined in the root of a crate with the crate type of `proc-macro`」(뒤 에러) 이고 「may not be used from the crate where they are defined」(앞 에러). **두 규칙이 합쳐 「매크로 크레이트를 따로 둔다」가 된다.** 매크로 크레이트는 **먼저 컴파일되어 컴파일러에 실려야** 쓰일 수 있다.

### 7. ★★ `input : struct Wrap<T>(T);` — `Wrap<T>(T);` 가 한 낱말이 되어 말이 안 되는 `impl` 이 나온다

**출력**

```text
===== 소스: r57_use_generic.rs =====
use r57_hello_pm::Hello;

#[derive(Hello)]
struct Wrap<T>(T);

fn main() {
    println!("{}", Wrap::<u8>::hello());
    let _ = Wrap(1u8).0;
}
===== 소스: r57_hello_pm.rs =====
use proc_macro::TokenStream;

#[proc_macro_derive(Hello)]
pub fn derive_hello(input: TokenStream) -> TokenStream {
    let text = input.to_string();
    eprintln!("[derive(Hello)] input : {text}");
    let mut words = text.split_whitespace();
    let mut name = "";
    while let Some(w) = words.next() {
        if w == "struct" || w == "enum" {
            name = words.next().unwrap_or("");
            break;
        }
    }
    let out = format!("impl {name} {{ pub fn hello() -> &'static str {{ \"hello from {name}\" }} }}");
    eprintln!("[derive(Hello)] output: {out}");
    out.parse().unwrap()
}
===== rustc --edition 2021 --crate-type proc-macro --extern proc_macro r57_hello_pm.rs =====
(exit 0)
===== rustc --edition 2021 --extern r57_hello_pm=libr57_hello_pm.so r57_use_generic.rs =====
[derive(Hello)] input : struct Wrap<T>(T);
[derive(Hello)] output: impl Wrap<T>(T); { pub fn hello() -> &'static str { "hello from Wrap<T>(T);" } }
error: expected `{}`, found `;`
 --> r57_use_generic.rs:3:10
  |
3 | #[derive(Hello)]
  |          ^^^^^
  |
  = note: this error originates in the derive macro `Hello` (in Nightly builds, run with -Z macro-backtrace for more info)

error: missing `for` in a trait impl
 --> r57_use_generic.rs:3:10
  |
3 | #[derive(Hello)]
  |          ^^^^^
  |
  = note: this error originates in the derive macro `Hello` (in Nightly builds, run with -Z macro-backtrace for more info)

error: proc-macro derive produced unparsable tokens
 --> r57_use_generic.rs:3:10
  |
3 | #[derive(Hello)]
  |          ^^^^^

error[E0404]: expected trait, found struct `Wrap`
 --> r57_use_generic.rs:3:10
  |
3 | #[derive(Hello)]
  |          ^^^^^ not a trait
  |
  = note: this error originates in the derive macro `Hello` (in Nightly builds, run with -Z macro-backtrace for more info)

error[E0412]: cannot find type `T` in this scope
 --> r57_use_generic.rs:3:10
  |
3 | #[derive(Hello)]
  |          ^^^^^ not found in this scope
  |
  = note: this error originates in the derive macro `Hello` (in Nightly builds, run with -Z macro-backtrace for more info)

error: aborting due to 5 previous errors

Some errors have detailed explanations: E0404, E0412.
For more information about an error, try `rustc --explain E0404`.
(exit 1)
```

**왜 그런가**

- ★★★ 문자열로 바꾼 토큰에서 **`Wrap<T>(T);` 사이에 공백이 없어** 「`struct` 다음 낱말」이 이름 + 제네릭 + 필드 + 세미콜론 전부가 됐다 → 「proc-macro derive produced unparsable tokens」를 포함한 에러 다섯.
- ★★★ **`syn` 은 토큰을 구조(이름 · 제네릭 · 필드)로 파싱해 준다.** std 는 `impl Display for TokenStream` 에서 「the exact form of the output is subject to change … **you should not do any kind of simple substring matching on the output string** … Instead, you should work at the `TokenTree` level」이라고 적는다 — 이 편의 문자열판은 **자리를 보이기 위한 최소판**일 뿐이다.

### 8. ★★ `-Z` 는 nightly 전용 · 대신 `stringify!`/`concat!` 와 매크로 안의 `eprintln!` · 못 보는 것은 위생 표시

**출력**

```text
===== 소스: r57_trace.rs =====
macro_rules! my_vec {
    ($($x:expr),*) => {{
        let mut v = Vec::new();
        $(v.push($x);)*
        v
    }};
}

macro_rules! trace_vec {
    ($($x:expr),*) => {
        concat!("let mut v = Vec::new(); ", $("v.push(", stringify!($x), "); ",)* "v")
    };
}

fn main() {
    println!("{:?}", my_vec![1, 2 + 3, 4]);
    println!("{}", trace_vec![1, 2 + 3, 4]);
}
===== rustc --edition 2021 -Zunpretty=expanded r57_trace.rs =====
error: the option `Z` is only accepted on the nightly compiler

help: consider switching to a nightly toolchain: `rustup default nightly`

note: selecting a toolchain with `+toolchain` arguments require a rustup proxy; see <https://rust-lang.github.io/rustup/concepts/index.html>

note: for more information about Rust's stability policy, see <https://doc.rust-lang.org/book/appendix-07-nightly-rust.html#unstable-features>

error: 1 nightly option were parsed

(exit 1)
```

```text
===== 소스: r57_trace.rs =====
macro_rules! my_vec {
    ($($x:expr),*) => {{
        let mut v = Vec::new();
        $(v.push($x);)*
        v
    }};
}

macro_rules! trace_vec {
    ($($x:expr),*) => {
        concat!("let mut v = Vec::new(); ", $("v.push(", stringify!($x), "); ",)* "v")
    };
}

fn main() {
    println!("{:?}", my_vec![1, 2 + 3, 4]);
    println!("{}", trace_vec![1, 2 + 3, 4]);
}
===== rustc --edition 2021 r57_trace.rs =====
(exit 0)
===== ./r57_trace =====
[1, 5, 4]
let mut v = Vec::new(); v.push(1); v.push(2 + 3); v.push(4); v
(exit 0)
```

**왜 그런가**

- ★★★ 「the option `Z` is only accepted on the nightly compiler」 — 이 머신에는 stable 하나뿐이다(서머리 도구 블록). **못 잰 것.**
- ★★ 대신 **같은 패턴으로 잡은 조각을 `stringify!` 로 되찍었다**(`v.push(2 + 3);` — `2 + 3` 이 식 하나로 잡혔다) · 절차 매크로는 **받은 토큰과 낼 코드를 직접 찍었다**(5번).
- ★ **못 보는 것** — 어느 `x` 가 누구 쪽 이름인가(위생 표시). 문자열에는 그냥 `x` 로 나온다 — 그 질문은 2번의 **출력 값**이 답했다.

### 9. ★★ `&[&dyn Debug]` — 대가는 `&` 붙이기와 동적 디스패치 · 격자는 「같은 호출 모양」 기준

**출력**

```text
===== 소스: r57_dyn.rs =====
use std::fmt::Debug;

fn show_all(xs: &[&dyn Debug]) {
    for x in xs {
        println!("{:?}", x);
    }
}

fn main() {
    show_all(&[&1, &"two", &3.5]);
}
===== rustc --edition 2021 r57_dyn.rs =====
(exit 0)
===== ./r57_dyn =====
1
"two"
3.5
(exit 0)
```

**왜 그런가**

- ★★ 트레이트 객체로 받으면 원소 타입이 섞여도 된다([33번](../33-dyn-trait-objects-and-object-safety/)). 대가 — 호출하는 쪽이 원소마다 **`&`** 를 붙이고, 호출은 **vtable 을 거친다**(동적 디스패치 — 시간은 재지 않았다).
- ★ 1번 격자의 함수 판은 **매크로와 같은 호출 모양**(`show_all(&[1, "two", 3.5])`)으로 쓴 것이다 — 우회로가 있는 칸은 이것 하나였다.

### 10. ★★ 지역 변수·루프 라벨·블록 라벨은 **정의 쪽**에서, 나머지는 **호출 쪽**에서

- ★★★ Reference — 「loop labels, block labels, and local variables are looked up at the macro definition site while other symbols are looked up at the macro invocation site」.
- ★★ **2번** — 매크로가 만든 `let x` 는 정의 쪽 지역 변수라, 부른 쪽이 넘긴 `x + 1` 의 `x`(호출 쪽)와 **다른 이름**이다 → `120`. **3번** — 매크로가 만든 `let y` 는 정의 쪽이라 호출 쪽에서 안 보이고(E0425), `$name` 으로 받은 `y` 는 호출 쪽 글자라 보인다(`5`).

### 11. ★★ 같은 종류(파생 절차 매크로) — std 의 것은 **core 에 정의돼 있어** 내 크레이트는 「다른 크레이트」다

- ★★ 27번의 `#[derive(Debug)]` 도 **파생 매크로**다 — 로컬 문서의 `core::fmt` 에 「Derive Macro `Debug`」 페이지가 있다(「Derive macro generating an impl of the trait `Debug`」).
- ★★ 6번의 규칙은 「**정의한** 크레이트에서 못 쓴다」다. `Debug` 는 **core 가 정의**하고 내 크레이트는 **가져다 쓰는 쪽**이라 걸리지 않는다. 5번의 `Hello` 도 `r57_hello_pm` 크레이트가 정의하고 `r57_use` 가 쓰니 통과했다.

### 12. ★ 서머리 (6)의 표 — `#[tokio::main]` 은 절차 매크로(속성형)

| | 선언 매크로 | 절차 매크로 |
|---|---|---|
| 받는 것 | 패턴에 맞춘 토큰 조각 | `TokenStream` 통째로 |
| 만드는 법 | 치환 틀에 채움 | Rust 코드를 실행해 새 토큰을 만듦 |
| 놓이는 곳 | 같은 크레이트 — 정의 뒤 | `proc-macro` 크레이트 — 정의한 크레이트 밖에서만 |
| 확장을 보는 법(stable) | `stringify!` 흔적 | 매크로 안의 `eprintln!` |

- ★ `#[tokio::main]` 은 `tokio-macros` — 55번 (5)의 `cargo tree` 가 **`tokio-macros v2.7.2 (proc-macro)`** 로 보였다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서·서머리의 **모든 블록** | `capture.sh` — 블록마다 명령을 배너에 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` 기본 규칙 넷 · **고칠 것 0** |
| ★★★ **함수로 쓰면 격자** | `r57_grid.sh` — 7줄 × (매크로 · 함수) = 14 파일 | 14 | **`6 / 7`** |
| 막힌 칸 전문 · 우회로 | `r57_fn_variadic` · `r57_fn_impls` · `r57_dyn` | 3 | E0061 · E0401(+E0599) · 통과 |
| ★★★ **위생** | `r57_hygiene`(Rust · C) · `_out` · `_ident` | 4 | `120` · `1110` · E0425 · `5` |
| 정의 순서 · 확장 흔적 | `r57_order` · `r57_unpretty` · `r57_trace` | 3 | 번호 없는 에러 · **nightly 전용** · 조각 셋 |
| ★★★ **절차 매크로** | `r57_pm_noextern` · `r57_pm` · `r57_pm_generic` · `r57_same` · `r57_notpm` · `r57_cargo` | 6 | E0432 · 통과 · 에러 다섯 · 같은 크레이트 에러 · 크레이트 타입 에러 · cargo 통과(플래그 1·1) |
| **안 던진 것** — `#[macro_export]` · 속성형·함수형 절차 매크로 · `syn`/`quote` · C 판 3번 · E0401 의 `help:` 를 따른 판 · 컴파일 시간 | — | 0 | ★ 「안 던졌다」로 표시했다 |

**구현 의존 항목**(버전·환경이 바뀌면 **다시 찍어야 하는** 것).

| 항목 | 왜 |
|---|---|
| `TokenStream::to_string()` 의 공백 — 5·7번의 `input` 줄 | ★ std 가 「subject to change」라고 적는다 |
| 절차 매크로의 `eprintln!` 이 컴파일러 표준 오류로 나오는 것 | ★ 매크로가 컴파일러 프로세스 안에서 도는 구현 |
| 번호 없는 에러(정의 순서 · 절차 매크로 자리)의 문구 | ★ rustc 진단 |
| cargo 가 넘기는 `--extern proc_macro` | ★ cargo 의 동작 |

★ **다시 찍는 법** — `capture.sh <새 디렉토리>` 를 그대로 돌리고 `normalize-shaky.py <원본> <새 디렉토리>` 로 견준다.
