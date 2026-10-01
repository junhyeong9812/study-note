# rust/syntax/57 — 매크로: `macro_rules!` 맛보기와 절차 매크로의 자리 — 질문

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 일곱 가지 일, 매크로 판과 함수 판 (예측)

```bash
# r57_grid.sh
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
```

- 표의 **function** 칸 일곱 개를 채워라(`runs: <출력>` 또는 `compile error <번호>`). 마지막 줄의 `N / 7` 은?

### 2. ★★★ 같은 모양의 두 언어 (예측)

```rust
// r57_hygiene.rs
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
```

```c
// r57_hygiene.c
#include <stdio.h>

#define TIMES_TEN_PLUS_X(e) ({ int x = 100; (e) * 10 + x; })

int main(void) {
    int x = 1;
    printf("%d\n", TIMES_TEN_PLUS_X(x + 1));
    return 0;
}
```

- 두 프로그램은 각각 무엇을 찍나? gcc 는 경고를 내나 — 낸다면 **어느 변수**를 짚나?

### 3. ★★★ 안에서 만든 이름, 건네받은 이름 (예측)

```rust
// r57_hygiene_out.rs
macro_rules! declare_y {
    () => {
        let y = 5;
    };
}

fn main() {
    declare_y!();
    println!("{y}");
}
```

```rust
// r57_hygiene_ident.rs
macro_rules! declare {
    ($name:ident) => {
        let $name = 5;
    };
}

fn main() {
    declare!(y);
    println!("{y}");
}
```

- 두 파일은 각각 컴파일되는가? 에러라면 번호는? 되는 쪽의 출력은?

### 4. ★★ 부르는 줄이 정의보다 위 (예측)

```rust
// r57_order.rs
fn main() {
    println!("{}", twice!(4));
}

macro_rules! twice {
    ($e:expr) => {
        $e * 2
    };
}
```

- 컴파일되는가? 안 된다면 에러 문구와 `note:` 는? 경고도 나오나?

### 5. ★★★ 문자열로 짠 `derive` (예측)

```rust
// r57_hello_pm.rs
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
```

```rust
// r57_use.rs
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
```

- `r57_use.rs` 를 **컴파일하는 동안** 표준 오류에 무엇이 찍히나(몇 줄 · 각 줄의 모양)? 실행하면?

### 6. ★★★ 절차 매크로를 놓는 두 자리 (예측)

```rust
// r57_same.rs
use proc_macro::TokenStream;

#[proc_macro_derive(Hello)]
pub fn derive_hello(_input: TokenStream) -> TokenStream {
    TokenStream::new()
}

#[derive(Hello)]
struct Point;
```

```rust
// r57_notpm.rs
extern crate proc_macro;
use proc_macro::TokenStream;

#[proc_macro_derive(Hello)]
pub fn derive_hello(_input: TokenStream) -> TokenStream {
    TokenStream::new()
}
```

- 앞 파일을 `--crate-type proc-macro` 로, 뒤 파일을 `--crate-type lib` 로 컴파일하면 각각 무엇이 나오나?

### 7. ★★ 제네릭 구조체에 5번의 `derive` 를 달면 (경계)

- 5번 매크로를 `#[derive(Hello)] struct Wrap<T>(T);` 에 달면 무엇이 깨질 것 같은가 — `input` 줄이 어떻게 찍히는지부터 추측하라. 실전 절차 매크로가 `syn` 을 쓰는 이유와, std `TokenStream` 문서가 문자열 매칭에 대해 적는 것은?

### 8. ★★ 확장 결과를 보고 싶다 (왜)

- 이 머신에서 `rustc -Zunpretty=expanded` 는 왜 안 되나? 그 대신 이 문서는 무엇으로 「확장이 무엇을 만들었나」를 물었고, 그 창이 **못 보는 것**은 무엇인가?

### 9. ★★ 함수도 할 수 있는 칸 (경계)

- 1번의 `mixed` 칸을 함수로 우회하는 방법은? 그 대가 둘은? 1번 격자의 「함수 판」은 어떤 기준으로 쓴 판인가?

### 10. ★★ 혼합 위생 (왜)

- Reference 는 `macro_rules!` 의 위생을 「mixed-site」라고 부른다. **무엇이 정의 쪽에서, 무엇이 호출 쪽에서** 찾아지나? 그 규칙으로 2번과 3번을 한 문장씩 설명하라.

### 11. ★★ `derive` 다섯과 이 편 (연결)

- [27번 주제](../27-derive-macros-debug-clone-partialeq-default-hash/)의 `#[derive(Debug)]` 와 5번의 `#[derive(Hello)]` 는 같은 종류의 것인가? std 의 파생 매크로가 **같은 크레이트에서 쓰이는데도** 6번의 에러가 안 나는 이유는?

### 12. ★ 두 부류의 편집자 (연결)

- 선언 매크로와 절차 매크로를 「받는 것 · 만드는 법 · 놓이는 곳 · 확장을 보는 법」 네 칸으로 비교하라. `#[tokio::main]`([55번 주제](../55-async-in-practice-runtime-send-and-pin/))은 어느 쪽인가?

## 실행 환경

★ 던지는 법 — 선언 매크로는 `rustc --edition 2021 <파일>.rs`, 격자는 `bash r57_grid.sh`, 절차 매크로는 `rustc --edition 2021 --crate-type proc-macro --extern proc_macro <매크로>.rs` 뒤 `rustc --edition 2021 --extern <이름>=lib<이름>.so <쓰는쪽>.rs`. C 는 `gcc -std=gnu17 -Wall -Wextra`. **외부 크레이트를 하나도 쓰지 않는다.**
★★★ **매크로를 보면 먼저 물어라** — 「**이것은 값을 받나, 토큰을 받나**」와 「**이 이름은 누구 쪽 이름인가**」.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
