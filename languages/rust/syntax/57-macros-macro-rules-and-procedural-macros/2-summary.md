# rust/syntax/57 — 매크로: `macro_rules!` 맛보기와 절차 매크로의 자리 — 정리 (힌트)

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
===== gcc --version | head -1 =====
gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
(exit 0)
===== ls "$HOME"/.cargo/registry/cache/*/ | grep -E "^tokio-(1|macros)" =====
tokio-1.52.3.crate
tokio-1.53.1.crate
tokio-macros-2.7.0.crate
tokio-macros-2.7.1.crate
tokio-macros-2.7.2.crate
(exit 0)
```

- ★★★ **nightly 가 없다** — `rustup toolchain list` 에 `stable` 하나. 확장 결과를 찍는 `-Zunpretty=expanded` 는 **못 쓴다**((4)).

★★★ **본체 창 — ① 「같은 일을 함수로 쓰면」 격자다.** 줄마다 **매크로 판과 함수 판**을 각각 컴파일·실행하고, 스크립트가 마지막 줄에 **「함수 판이 매크로 판과 갈린 칸 N / M」** 을 센다.

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| 안 흔들린다 | ★★★ **격자의 갈린 칸 수** · 각 칸의 에러 번호 | 같은 rustc 판에서 고정이다 |
| 안 흔들린다 | 절차 매크로가 **컴파일 중에** 표준 오류로 찍는 입력·출력 토큰 문자열 | 같은 판에서 고정 — ★ 단 **`to_string()` 의 공백은 판이 오르면 바뀔 수 있다**고 std 가 적는다((5)) |
| 안 흔들린다 | E0061 · E0308 · E0425 · E0401 · E0432 · 번호 없는 절차 매크로 에러의 문구 · 종료 코드 | 같은 판에서 고정 |

★ 정규화 규칙은 **기본 넷**만 쓴다. 이 편의 블록에는 걸리는 칸이 없었다.

## 한눈에 — 쉽게 말하면

**함수는 「완성된 값」을 받아 일하는 직원이고, 매크로는 「코드 원고」를 받아 코드를 **다시 써 주는** 편집자다.**
직원에게는 「1, 2, 3 을 줄게」처럼 **정해진 개수의 값**만 건넬 수 있다. 편집자에게는 **원고 조각**을 몇 개든 건넬 수 있고, 편집자는 그 조각으로 **새 함수·새 `impl`·새 `return`** 까지 써 넣는다 — 값이 아니라 **글자를 다루니까.**
Rust 의 편집자는 **자기 메모장(매크로 안의 `let x`)을 원고 주인의 메모장(바깥 `x`)과 섞지 않는다**(위생성). C 의 전처리기는 섞는다.
편집자에는 두 부류가 있다 — **양식지에 빈칸을 채우는 편집자**(`macro_rules!` — 같은 파일 안에서 바로)와 **원고를 통째로 받아 프로그램으로 고쳐 쓰는 편집자**(절차 매크로 — **따로 차린 사무실(별도 크레이트)** 에서만 일한다).

| 비유 | 실체 |
|---|---|
| 「**값을 받는 직원**」 | ★★ **함수** — 인자 개수·타입이 서명에 고정 · 아이템(함수·`impl`)을 **만들어 내지 못한다**((1)) |
| 「**원고를 다시 써 주는 편집자**」 | ★★★ **매크로** — 토큰을 받아 코드로 **펼친다**(확장) · 함수가 못 한 칸 **6 / 7**((1)) |
| 「**메모장을 섞지 않는다**」 | ★★★ **위생성** — 매크로 안의 `let x` 는 바깥 `x` 를 못 가린다(Rust `120` 대 C `1110`)((2)) |
| 「**양식지 편집자**」 | ★★ **`macro_rules!`** — 패턴 → 치환 · 정의 **뒤에서만** 쓸 수 있다((3)) |
| 「**따로 차린 사무실**」 | ★★★ **절차 매크로 = `proc-macro` 크레이트** — 같은 크레이트에서 쓰면 에러((5)) |

```text
   macro_rules!                                  절차 매크로 (proc-macro 크레이트)
   ─────────────                                 ─────────────────────────────
   my_vec![1, 2 + 3, 4]                          #[derive(Hello)] struct Point { x: i32 }
        │ 패턴 ($($x:expr),*) 에 맞추고                   │ 컴파일러가 아이템 토큰을 TokenStream 으로 건넨다
        ▼ 치환 틀에 채운다                               ▼ fn derive_hello(TokenStream) -> TokenStream  ← 컴파일 중에 도는 Rust 함수
   { let mut v = Vec::new();                     impl Point { pub fn hello() -> &'static str { … } }
     v.push(1); v.push(2 + 3); v.push(4); v }         │ 돌려준 토큰을 그 자리에 붙인다
        │                                             ▼
        ▼ 그다음에야 타입 검사                         그다음에야 타입 검사
```

> **확장(expansion)** — 매크로 호출을 매크로가 만든 코드로 바꿔 끼우는 컴파일 단계. 타입 검사보다 **먼저** 일어난다.\
> 예: `my_vec![1, 2 + 3, 4]` 가 `{ let mut v = Vec::new(); v.push(1); … v }` 가 된다((4)의 흔적).

> **토큰(token) · `TokenStream`** — 소스를 낱말 단위로 자른 조각(식별자·기호·리터럴)과, 그 조각들의 줄. 매크로가 받고 돌려주는 것이다.\
> 예: `struct Point { x: i32, }` 는 `struct` · `Point` · `{ … }` 묶음으로 된 토큰 줄이다((5)).

## 이 주제가 답하려는 질문

1. ★★★ **매크로는 함수로 못 하는 무엇을 하나** — 같은 일을 함수로 쓰면 어디서 막히나((1)).
2. ★★ **매크로 안의 이름은 바깥과 섞이나** — C 의 텍스트 치환과 무엇이 다른가((2)).
3. ★★★ **선언 매크로와 절차 매크로는 어디서 갈리나** — 무엇을 받고, 어디에 놓여야 하나((5)·(6)).

★ **선행** — [**27번 주제**](../27-derive-macros-debug-clone-partialeq-default-hash/)가 이 주제의 뿌리다. ★★★ **이미 잰 것 — 다시 재지 않고 인용한다.**
27번 — **`derive` 는 파생 매크로(절차적 매크로)이고 다섯 개(`Debug`·`Clone`·`PartialEq`·`Default`·`Hash`)는 std 가 제공한다** · 파생이 필드에 요구하는 경계와 그 에러. 27번은 「`#[derive]` 를 직접 만들기 — 절차적 매크로 크레이트(`proc-macro = true`)가 필요하다」를 **더 들어가면**에 남겨 두었다 — 이 편 (5)가 그것을 한다.
C 갈래 [42번](../../../c/syntax/42-function-like-macro-pitfalls/) — **C 매크로에는 위생이 없다**(문장 식 안의 지역 변수가 호출하는 쪽의 같은 이름을 가린다). (2)가 같은 모양을 Rust 와 나란히 던진다.

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ① 「함수로 쓰면」 격자다

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ① ★★★ **매크로 판 × 함수 판 격자** | 함수가 **못 하는** 칸과 그 에러 번호 | ★ **본체**((1)) |
| ② ★★★ **출력 값**(Rust 대 C) | 매크로 안의 이름이 바깥을 **가리나** | 쓴다((2)) |
| ③ ★★ **컴파일러 진단** | 정의 순서 · 위생 · 절차 매크로의 자리 | 쓴다((2)·(3)·(5)) |
| ④ ★★ **`stringify!`·`concat!` 흔적** · 절차 매크로의 `eprintln!` | 확장이 **무엇을 만들었나** | 쓴다((4)·(5)) |
| 확장 결과 전문(`-Zunpretty=expanded` · `cargo expand`) | — | ★ **못 잰 것** — nightly 전용이고(에러 전문 (4)) `cargo expand` 는 외부 도구다. **④ 로 바꿔 물었다** |
| 컴파일 시간 | — | ★ **안 쟀다** |

★★ **제5의 상태 — 「같은 질문을 다른 창으로」.** 「매크로가 무엇으로 펼쳐졌나」는 확장 결과를 **찍어 보면** 끝나는 질문인데, stable 에는 그 창이 없다.
그래서 **확장된 코드가 자기 원문을 스스로 말하게** 했다 — `stringify!($x)` 로 받은 조각을 문자열로 되찍고((4)), 절차 매크로는 **받은 토큰과 돌려줄 코드를 컴파일 중에 표준 오류로** 찍었다((5)).
★ 바꾼 창이 못 보는 것 — **위생 표시**(어느 `x` 가 어느 쪽의 `x` 인가)는 문자열에 안 나온다. `stringify!` 는 `x` 를 그냥 `x` 로 찍는다. 그 자리는 ② 의 **출력 값**이 메운다.

### (1) ★★★ 같은 일을 함수로 쓰면 — 일곱 줄 격자

**언제 쓰나** — 「이걸 매크로로 할까 함수로 할까」를 정할 때마다. **함수로 되면 함수가 낫다**(타입 검사·에러 메시지·IDE 지원이 전부 함수 쪽이 좋다).

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

- ★★★ **「함수 판이 매크로 판과 갈린 칸 6 / 7」** — 함수가 **같은 결과를 낸 것은 `square` 하나**뿐이다(대조용 줄). 이 0 이 아닌 1 이 있어야 격자가 「매크로가 늘 이긴다」로 읽히지 않는다.
- ★★★ **컴파일 에러로 막힌 넷** — `variadic`(E0061 — 인자 개수가 서명에 고정) · `mixed`(E0308 — 슬라이스는 원소 타입이 하나) · `ident`(E0425 — 함수 인자는 **값**이라 `hello` 라는 **이름**을 받지 못한다) · `impls`(E0401 — 함수 몸통의 `impl` 은 함수의 타입 인자를 못 쓴다).
- ★★★ **돌기는 도는데 결과가 다른 둘** — `text`: 함수는 **이미 계산된 `7`** 만 받아 `7 = 7`. 매크로는 `stringify!($e)` 로 **식의 원문** `a * 3 + 1` 을 찍었다. `return`: 함수 안의 `return 0` 은 **함수 자신**을 빠져나와 호출한 쪽이 계속 돈다(`reached with 0` 이 찍히고 `1`). 매크로의 `return 0` 은 **호출한 함수**를 빠져나갔다(`reached` 가 한 번 · `0`).
- ★★ **에러가 아니라 「다른 답」인 칸이 더 위험하다** — `text`·`return` 은 함수 판도 **컴파일되고 돈다.** 격자가 출력을 나란히 두지 않았으면 못 봤다.

**막힌 칸 둘의 전문.**

```text
===== 소스: r57_fn_variadic.rs =====
fn my_vec(x: i32) -> Vec<i32> {
    vec![x]
}

fn main() {
    println!("{:?}", my_vec(1, 2, 3));
}
===== rustc --edition 2021 r57_fn_variadic.rs =====
error[E0061]: this function takes 1 argument but 3 arguments were supplied
 --> r57_fn_variadic.rs:6:22
  |
6 |     println!("{:?}", my_vec(1, 2, 3));
  |                      ^^^^^^    -  - unexpected argument #3 of type `{integer}`
  |                                |
  |                                unexpected argument #2 of type `{integer}`
  |
note: function defined here
 --> r57_fn_variadic.rs:1:4
  |
1 | fn my_vec(x: i32) -> Vec<i32> {
  |    ^^^^^^
help: remove the extra arguments
  |
6 -     println!("{:?}", my_vec(1, 2, 3));
6 +     println!("{:?}", my_vec(1));
  |

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0061`.
(exit 1)
```

- ★★ **E0061** — `help:` 가 「remove the extra arguments」를 권한다. Rust 로 정의하는 보통 함수에는 **가변 개수 인자가 없다** — 매크로가 그 자리를 맡는다(`println!`·`vec!`).

```text
===== 소스: r57_fn_impls.rs =====
trait Bits {
    fn bits() -> u32;
}

fn impl_bits<T>() {
    impl Bits for T {
        fn bits() -> u32 {
            0
        }
    }
}

fn main() {
    impl_bits::<u8>();
    println!("{}", u8::bits());
}
===== rustc --edition 2021 r57_fn_impls.rs =====
error[E0401]: can't use generic parameters from outer item
 --> r57_fn_impls.rs:6:19
  |
5 | fn impl_bits<T>() {
  |              - type parameter from outer item
6 |     impl Bits for T {
  |         -         ^ use of generic parameter from outer item
  |         |
  |         help: try introducing a local generic parameter here: `<T>`

error[E0599]: no function or associated item named `bits` found for type `u8` in the current scope
  --> r57_fn_impls.rs:15:24
   |
15 |     println!("{}", u8::bits());
   |                        ^^^^ function or associated item not found in `u8`
   |
   = help: items from traits can only be used if the trait is implemented and in scope
note: `Bits` defines an item `bits`, perhaps you need to implement it
  --> r57_fn_impls.rs:1:1
   |
 1 | trait Bits {
   | ^^^^^^^^^^

error: aborting due to 2 previous errors

Some errors have detailed explanations: E0401, E0599.
For more information about an error, try `rustc --explain E0401`.
(exit 1)
```

- ★★★ **E0401** — `help:` 가 「try introducing a local generic parameter here: `<T>`」를 권한다. 따르면 `impl<T> Bits for T` — **모든 타입에 대한 담요 구현**이 되어 「`u8`·`u16`·`u64` 에만」이라는 뜻이 사라진다(★ 그 판은 던지지 않았다). **타입 목록을 받아 `impl` 을 여러 번 찍는 것은 매크로의 일이다.**

**`mixed` 칸은 함수도 우회할 수 있다 — 대가를 내고.**

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

- ★★ **`&[&dyn Debug]` 로 받으면 돈다** — 대가는 호출하는 쪽이 원소마다 **`&` 를 붙이는 것**과 **동적 디스패치**(트레이트 객체 — [33번](../33-dyn-trait-objects-and-object-safety/)). 매크로 판은 원소마다 **정적으로** `println!` 을 펼친다. ★ 격자의 「함수 판」은 **같은 호출 모양**으로 쓴 판이다 — 우회로가 있는 칸은 이것 하나였다.

### (2) ★★★ 위생성 — 매크로 안의 `let x` 는 바깥 `x` 를 가리나

**Rust.**

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

**같은 모양의 C(GNU 문장 식).**

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

- ★★★ **Rust `120` · C `1110`** — 넘긴 식은 둘 다 `x + 1` 이다. Rust 는 그 `x` 를 **부른 쪽의 `x`(1)** 로 읽어 `2 * 10 + 100`. C 는 **글자를 그대로 붙여 넣어** 매크로 안의 `int x = 100` 이 가렸다 → `101 * 10 + 100`.
- ★★★ **gcc 의 경고가 증거다** — 「unused variable ‘x’」가 `main` 의 `x`(6행)를 짚는다. **부른 쪽의 `x` 가 한 번도 안 쓰였다** — 매크로 안의 `x` 가 전부 가져갔다. Rust 판은 경고가 없다.
- ★★ Reference — 「Macros by example have **mixed-site hygiene**. This means that loop labels, block labels, and **local variables are looked up at the macro definition site** while other symbols are looked up at the macro invocation site.」 매크로가 만든 `let x` 는 **매크로 쪽 표시**를 달고, 부른 쪽에서 넘어온 `x` 는 **부른 쪽 표시**를 단다 — 글자가 같아도 다른 이름이다.
- ★ C 갈래 [42번](../../../c/syntax/42-function-like-macro-pitfalls/)이 같은 사고(「문장 식 안의 지역 변수가 호출하는 쪽의 같은 이름을 가린다」)를 C 안에서 쟀다. 이 편은 **같은 모양을 두 언어로 나란히** 던졌을 뿐이다.

**반대 방향 — 매크로가 만든 이름을 바깥에서 쓰면.**

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

- ★★★ **E0425 — cannot find value `y`** — 매크로 안에서 만든 `let y` 는 **매크로 쪽 이름**이라 호출한 뒤에도 바깥에서 **안 보인다.** ★ 같은 모양의 C 판은 던지지 않았다.

**이름을 호출하는 쪽이 건네면.**

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

- ★★★ **`5`** — `$name:ident` 로 받은 `y` 는 **부른 쪽이 쓴 글자**라 부른 쪽 표시를 단다 → 바깥에서 보인다. **「이름을 새로 만드는 매크로」는 그 이름을 인자로 받아야 한다**((1)의 `ident` 칸 `make_fn!(hello)` 와 같은 원리).

### (3) ★★ 정의 순서 — `macro_rules!` 는 텍스트 순서를 따른다

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

- ★★ **「cannot find macro `twice` in this scope」 + `note:` 「a macro with the same name exists, but it appears later」** — 함수는 파일 어디에 정의해도 부를 수 있지만 `macro_rules!` 는 **정의한 줄 뒤에서만** 보인다(Reference: 텍스트 스코프는 「based largely on the order that things appear in source files」). ★ 에러 번호가 없다.
- ★ 덤으로 `unused macro definition` 경고 — 앞의 호출이 이 정의를 **못 봤으니** 한 번도 안 쓰인 셈이다.
- ★ 다른 모듈·크레이트에서 쓰려면 `#[macro_export]` · `use` 경로 — **던지지 않았다.**

### (4) ★★ 확장을 찍어 볼 수 있나 — `-Zunpretty` 는 못 쓴다

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

- ★★★ **「the option `Z` is only accepted on the nightly compiler」** — 확장 결과 전문을 찍는 길이 stable 에 없다. **못 잰 것**이다(도구 블록: nightly 없음). `cargo expand` 는 이 옵션을 부르는 **외부 도구**라 같은 이유로 제외했다(네트워크 금지이기도 하다).

**대신 — 매크로가 자기 확장을 문자열로 말하게 한다.**

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

- ★★★ **둘째 줄이 첫째 줄을 만든 코드의 모양이다** — `trace_vec!` 는 `my_vec!` 과 **같은 패턴 `$($x:expr),*`** 로 받아 `stringify!($x)` 를 `concat!` 로 이었다. `2 + 3` 이 **식 하나(`$x:expr`)로** 잡혀 `v.push(2 + 3);` 이 됐다는 것이 보인다(쉼표로 나뉜 조각 **셋**).
- ★ 이것은 확장 결과 **그 자체가 아니라** 「같은 패턴으로 잡은 조각을 되찍은 것」이다 — 위생 표시는 안 보인다((0)의 「바꾼 창이 못 보는 것」).

### (5) ★★★ 절차 매크로의 자리 — `#[derive(Hello)]` 를 문자열로

**언제 쓰나** — 선언 매크로의 패턴으로는 못 받는 입력(**아이템 전체** — 구조체 정의·함수)을 **Rust 코드로 분석**해 새 코드를 내야 할 때. `derive` 가 대표다(27번).

**매크로 크레이트와 쓰는 크레이트 — `rustc` 로 직접.**

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

- ★★★ **컴파일 중에 표준 오류 네 줄** — `rustc … r57_use.rs` 단계에서 `[derive(Hello)] input : struct Point { x: i32, }` 가 찍혔다. **절차 매크로는 컴파일러가 컴파일 도중에 부르는 보통의 Rust 함수**다 — 그래서 `eprintln!` 이 **컴파일러의 표준 오류**로 나온다.
- ★★★ **`input` 은 구조체 정의 전체의 토큰**이고 **`output` 은 그 자리에 붙을 코드**다. `derive` 는 원래 아이템을 **지우지 않고 뒤에 덧붙인다** — 그래서 `Point { x: 1 }.x` 가 그대로 쓰인다.
- ★★ **실행 출력 `hello from Point` · `hello from Color`** — 확장이 만든 `impl` 이 진짜로 붙었다.
- ★ 빌드 명령에 **`--crate-type proc-macro`** 와 **`--extern proc_macro`** 가 있다. 뒤엣것을 빼면:

```text
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
===== rustc --edition 2021 --crate-type proc-macro r57_hello_pm.rs =====
error[E0432]: unresolved import `proc_macro`
 --> r57_hello_pm.rs:1:5
  |
1 | use proc_macro::TokenStream;
  |     ^^^^^^^^^^ use of unresolved module or unlinked crate `proc_macro`
  |
  = help: you might be missing a crate named `proc_macro`

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0432`.
(exit 1)
```

- ★★ **E0432 — unresolved import `proc_macro`** — `proc_macro` 크레이트는 `rustc` 단독으로는 **자동으로 안 보인다.** cargo 는 그것을 넘겨 준다(아래 cargo 판의 `-v` 흔적).

**최소판의 한계 — 제네릭 구조체.**

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

- ★★★ **`input : struct Wrap<T>(T);`** — 토큰을 문자열로 바꾸면 **`Wrap<T>(T);` 가 공백 없이 한 낱말**이 되어, 「`struct` 다음 낱말」을 이름으로 잡은 이 최소판이 **`impl Wrap<T>(T); { … }`** 라는 말이 안 되는 코드를 냈다 → 에러 다섯(「proc-macro derive produced unparsable tokens」 · E0404 · E0412 …).
- ★★★ **그래서 `syn` 이 있다** — 토큰을 **구조(이름 · 제네릭 · 필드)** 로 파싱해 주는 라이브러리다. 절차 매크로는 **「토큰을 받아 토큰을 돌려준다」가 계약의 전부**라, 그 사이의 분석은 전부 매크로 작성자의 몫이다. ★★★ **std 가 이 최소판의 방식을 직접 말린다** — `impl Display for TokenStream`: 「Note: the exact form of the output is subject to change, e.g. there might be changes in the whitespace used between tokens. Therefore, **you should not do any kind of simple substring matching on the output string** (as produced by `to_string`) to implement a proc macro … Instead, you should work at the `TokenTree` level」. 이 편의 문자열판은 **외부 크레이트 없이 자리를 보이기 위한 것**이고, `Point` 판이 된 것은 **이 판의 공백 배치에 기댄 우연**이다.

**같은 크레이트에서 쓰면.**

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

- ★★★ **「can't use a procedural macro from the same crate that defines it」** — Reference: 「The macros **may not be used from the crate where they are defined**, and can only be used when imported in another crate.」 매크로 크레이트는 **먼저 컴파일되어 컴파일러에 실려야** 하는데, 자기 자신은 아직 컴파일 중이기 때문이다.

**보통 크레이트에 `#[proc_macro_derive]` 를 달면.**

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

- ★★★ **「the `#[proc_macro_derive]` attribute is only usable with crates of the `proc-macro` crate type」** — Reference: 「Procedural macros must be defined in the root of a crate with the crate type of `proc-macro`」. **두 에러가 합쳐 「별도 크레이트여야 한다」를 만든다** — 정의하는 쪽은 `proc-macro` 크레이트여야 하고, 쓰는 쪽은 그 밖이어야 한다.

**cargo 로 — `[lib] proc-macro = true`.**

```bash
# r57_cargo.sh
# Two packages side by side: the derive lives in its own proc-macro crate, the app depends on it by path.
set -eu
rm -rf hello_pm app
mkdir -p hello_pm/src app/src
cat > hello_pm/Cargo.toml <<'EOF'
[package]
name = "r57_hello_pm"
version = "0.1.0"
edition = "2021"

[lib]
proc-macro = true
EOF
cp r57_hello_pm.rs hello_pm/src/lib.rs
cat > app/Cargo.toml <<'EOF'
[package]
name = "app"
version = "0.1.0"
edition = "2021"

[dependencies]
r57_hello_pm = { path = "../hello_pm" }
EOF
cp r57_use.rs app/src/main.rs
find hello_pm app -type f | sort
```

```text
===== bash r57_cargo.sh =====
app/Cargo.toml
app/src/main.rs
hello_pm/Cargo.toml
hello_pm/src/lib.rs
(exit 0)
===== cd app && cargo run -q --offline 2>/dev/null =====
hello from Point
hello from Color
===== cd app && cargo run -q --offline 2>&1 >/dev/null =====
[derive(Hello)] input : struct Point { x: i32, }
[derive(Hello)] output: impl Point { pub fn hello() -> &'static str { "hello from Point" } }
[derive(Hello)] input : enum Color { Red, }
[derive(Hello)] output: impl Color { pub fn hello() -> &'static str { "hello from Color" } }
(exit 0)
===== cd app && cargo clean -q && cargo build -v --offline 2>&1 >/dev/null | grep -o -e '--crate-type proc-macro' -e '--extern proc_macro' | sort | uniq -c =====
      1 --crate-type proc-macro
      1 --extern proc_macro
(exit 0)
```

- ★★★ **같은 두 줄이 컴파일 중에, 같은 두 줄이 실행에** — `Cargo.toml` 의 `proc-macro = true` 가 `rustc` 판의 `--crate-type proc-macro` 와 같은 일을 한다. 마지막 명령(`cargo build -v`)이 **cargo 가 넘긴 플래그**를 세어 `--crate-type proc-macro` 1 · `--extern proc_macro` 1 을 보였다 — 앞의 E0432 가 cargo 판에서 안 나는 이유다.
- ★ `cargo run -q` 의 표준 오류에도 매크로의 `eprintln!` 줄이 나왔다 — cargo 가 **컴파일러의 표준 오류를 그대로 전해 준다.**

### (6) ★★ 선언 매크로 대 절차 매크로

| | `macro_rules!`(선언 매크로) | 절차 매크로(`derive`·속성형·함수형) |
|---|---|---|
| 받는 것 | 토큰 — **패턴**(`$x:expr`·`$t:ty`·`$name:ident`·`$(…),*`)에 맞춰 | 토큰 — **`TokenStream` 통째로** |
| 만드는 법 | 치환 틀에 채운다(규칙 몇 개) | **Rust 코드를 실행**해 새 `TokenStream` 을 만든다 |
| 놓이는 곳 | 같은 파일·같은 크레이트 — **정의 뒤에서만**((3)) | ★★★ **`proc-macro` 크레이트** — 같은 크레이트에서 못 씀((5)) |
| 위생성 | ★ **혼합 위생**(지역 변수는 정의 쪽)((2)) | 만드는 코드가 정한다(이 편은 재지 않았다) |
| 입력 분석 | 패턴이 대신 해 준다 | ★ **직접** — 보통 `syn`·`quote`((5)의 한계) |
| 확장 결과를 보려면 | stable 에서는 흔적만((4)) | 매크로 안에서 `eprintln!`((5)) |
| 예 | `vec!`·`println!`·(1)의 여섯 줄 | `#[derive(Debug)]`(27번) · `#[tokio::main]`([55번](../55-async-in-practice-runtime-send-and-pin/)) |

## 문법 — 형태와 규칙

```text
   macro_rules! 이름 {
       (패턴) => { 치환 };                 ← 규칙 여러 개 — 위에서부터 맞춰 본다
   }
   조각 지정자   $e:expr  $t:ty  $n:ident  $b:block  $x:tt  …
   반복          $( … ),*   $( … );*   $( … )+
   stringify!($e)   concat!("a", …)      ← 조각을 문자열로 · 문자열 리터럴을 잇기

   // 절차 매크로 크레이트 (Cargo: [lib] proc-macro = true)
   use proc_macro::TokenStream;
   #[proc_macro_derive(이름)]  pub fn f(input: TokenStream) -> TokenStream
   #[proc_macro_attribute]     pub fn g(attr: TokenStream, item: TokenStream) -> TokenStream
   #[proc_macro]               pub fn h(input: TokenStream) -> TokenStream
```

- ★★★ **매크로는 값이 아니라 토큰을 받는다 — 그래서 가변 개수·이름·코드 원문·`return`·아이템을 다룬다**((1)).
- ★★★ **`macro_rules!` 안의 지역 변수는 부른 쪽 이름과 섞이지 않는다 — 이름을 바깥에 내려면 인자로 받는다**((2)).
- ★★★ **절차 매크로는 `proc-macro` 크레이트에 두고 다른 크레이트에서 쓴다**((5)).
- ★ 속성형(`#[proc_macro_attribute]`)·함수형(`#[proc_macro]`)은 **형태만** 적었다 — 이 편은 `derive` 만 던졌다.

## 어디서 틀리나

### 1. ★★★ 「매크로가 더 강력하니 매크로로 쓴다」

(1) — **함수로 되는 칸(`square`)은 함수가 낫다.** 매크로는 함수가 **못 하는** 여섯 칸을 위한 것이다.

### 2. ★★★ 「`return` 을 담은 헬퍼 함수로 조기 반환을 빼낸다」

(1)의 `return` 칸 — 함수의 `return` 은 **자기만** 빠져나온다. 호출한 함수를 빠져나가려면 매크로(또는 `?` 연산자 — 22번)다. ★ **컴파일되고 돌기 때문에** 안 걸린다.

### 3. ★★★ 「매크로는 C 처럼 글자를 붙여 넣는다」

(2) — **Rust `120` 대 C `1110`.** `macro_rules!` 의 지역 변수는 위생적이다. 거꾸로 **매크로 안에서 만든 `let y` 를 바깥에서 못 쓴다**(E0425) — 이름을 내려면 `$name:ident` 로 받는다.

### 4. ★★ 「매크로를 파일 아래쪽에 정의해도 된다」

(3) — **정의 뒤에서만** 보인다. 함수와 다르다.

### 5. ★★★ 「`#[proc_macro_derive]` 를 그냥 내 크레이트에 쓴다」

(5) — 보통 크레이트면 「only usable with crates of the `proc-macro` crate type」, `proc-macro` 크레이트 안에서 쓰면 「can't use a procedural macro from the same crate」. **크레이트를 하나 더 만든다.**

### 6. ★★ 「`TokenStream` 을 문자열로 다루면 간단하다」

(5)의 제네릭 판 — `Wrap<T>(T);` 가 **한 낱말**이 되어 깨졌다. 실전은 `syn` 으로 파싱한다.

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| `macro_rules!` 의 혼합 위생 | ★ **언어**(Reference — Hygiene) | (2) |
| `macro_rules!` 는 텍스트 순서로 보인다 | ★ **언어**(Reference — 텍스트 스코프) | (3) |
| 절차 매크로는 `proc-macro` 크레이트 루트에 · 같은 크레이트에서 못 씀 | ★ **언어**(Reference — Procedural Macros) | (5) |
| `proc-macro = true` 가 `--crate-type proc-macro` · `--extern proc_macro` 가 된다 | ★ **cargo 의 동작**(이 판 `-v` 관찰) | (5) |
| `TokenStream::to_string()` 의 공백 위치 | ★ **구현** — std 가 「subject to change」라며 문자열 매칭을 말린다 | (5) |
| 절차 매크로의 `eprintln!` 이 컴파일러 표준 오류로 나온다 | ★ **구현**(매크로가 컴파일러 프로세스 안에서 돈다 — 이 판 관찰) | (5) |
| `-Z` 옵션은 nightly 전용 | ★ **rustc 의 안정성 정책** | (4) |
| C 매크로의 텍스트 치환 | ★ **C 언어**(전처리기) · 문장 식은 **GNU 확장** | (2) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 근거 |
|---|---|---|
| 값 몇 개를 받아 계산 | **함수** | (1) `square` |
| 가변 개수 인자 · 원소 타입이 섞인 목록 | `macro_rules!`(또는 슬라이스 · `&dyn Trait` — 대가를 내고) | (1) |
| 여러 타입에 같은 `impl` 을 찍는다 | `macro_rules!` | (1) `impls` |
| 조기 반환을 줄인다 | `?`(22번) — 안 되면 `macro_rules!` | (1) `return` |
| 구조체 정의를 읽어 코드를 만든다(`derive`) | **절차 매크로 크레이트** + (실전은) `syn`/`quote` | (5) |
| 확장 결과를 확인하고 싶다 | nightly `-Zunpretty=expanded` / `cargo expand` — **이 머신에서는 못 썼다** | (4) |

## 핵심 문장

- ★★★ **매크로는 값이 아니라 토큰을 받아 코드를 펼친다 — 함수가 못 한 칸 6 / 7(가변 인자 · 섞인 타입 · 이름 · 원문 · 호출한 쪽의 `return` · `impl` 찍기).**
- ★★★ **`macro_rules!` 는 위생적이다 — 안의 `let x` 는 바깥 `x` 를 못 가리고(Rust `120` 대 C `1110`), 안에서 만든 이름은 바깥에서 안 보인다.**
- ★★★ **절차 매크로는 컴파일 중에 도는 Rust 함수이고, `proc-macro` 크레이트에 따로 있어야 한다 — 같은 크레이트에서는 못 쓴다.**
- ★★ **stable 에서는 확장 결과를 못 찍는다 — `stringify!`·`eprintln!` 으로 흔적을 남긴다.**

## 관련 자료

- [**27번 주제**](../27-derive-macros-debug-clone-partialeq-default-hash/) — std 가 주는 파생 매크로 다섯과 그 경계. **그쪽은 「`derive` 를 쓰는 법」, 여기는 「`derive` 가 무엇이고 어디에 사나」.**
- [**22번 주제**](../22-result-question-mark-and-from/) — `?` 연산자. (1)의 `return` 칸이 매크로로 하던 일을 **언어가 문법으로** 가져간 것이다.
- [**33번 주제**](../33-dyn-trait-objects-and-object-safety/) — (1)의 `&dyn Debug` 우회로.
- [**55번 주제**](../55-async-in-practice-runtime-send-and-pin/) — `#[tokio::main]` 은 속성형 절차 매크로다(그쪽 (1)에 소스 주석).
- C 갈래 [42번](../../../c/syntax/42-function-like-macro-pitfalls/) — 함수형 매크로의 함정과 위생 없음.

## 용어 풀이

- **선언 매크로(declarative macro, `macro_rules!`)** — 패턴과 치환 틀로 정의하는 매크로.
- **절차 매크로(procedural macro)** — `TokenStream` 을 받아 `TokenStream` 을 돌려주는 Rust 함수로 정의하는 매크로. `proc-macro` 크레이트에 산다.
- **파생 매크로(derive macro)** — `#[derive(…)]` 로 부르는 절차 매크로. 아이템 뒤에 코드를 덧붙인다.
- **조각 지정자(fragment specifier)** — `$e:expr` 의 `expr` 처럼 패턴 변수가 받을 문법 조각의 종류.
- **위생성(hygiene)** — 매크로가 만든 이름이 부른 쪽 이름과 섞이지 않는 성질. `macro_rules!` 는 혼합 위생이다.
- **텍스트 스코프(textual scope)** — 소스에 **나온 순서**로 정해지는 `macro_rules!` 의 보이는 범위.
- **`syn`·`quote`** — 절차 매크로에서 토큰을 파싱하고 만들어 주는 외부 크레이트(이 편은 안 썼다).

## 더 들어가면

- `#[macro_export]` 와 `$crate` — 크레이트 밖으로 매크로를 내보낼 때 경로를 고정하는 법. **던지지 않았다.**
- 재귀 매크로와 `tt` 먹기(tt muncher) — 선언 매크로로 더 복잡한 입력을 받는 기법.
- 속성형 절차 매크로가 **아이템을 바꿔 치우는** 것(`derive` 는 덧붙이기만 한다) — `#[tokio::main]` 이 `async fn main` 을 `fn main` 으로 바꾸는 그것.
- 절차 매크로의 에러 보고(`compile_error!` · span) — (5)의 제네릭 판 에러가 전부 `#[derive(Hello)]` 자리를 짚은 이유.

## 실행 환경

**기준 소스** — [Reference — Macros By Example](https://doc.rust-lang.org/reference/macros-by-example.html)(§Hygiene 「Macros by example have mixed-site hygiene … local variables are looked up at the macro definition site while other symbols are looked up at the macro invocation site」 · 텍스트 스코프) ·
[Reference — Procedural Macros](https://doc.rust-lang.org/reference/procedural-macros.html)(「must be defined in the root of a crate with the crate type of `proc-macro`」 · 「may not be used from the crate where they are defined」 · Cargo 의 `[lib] proc-macro = true`) ·
[std — `proc_macro::TokenStream`](https://doc.rust-lang.org/proc_macro/struct.TokenStream.html).
★ 전부 **이 머신의 `rust-docs`(1.92.0) 로컬 사본**을 열어 읽었다.
**실행 검증** — `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `cargo 1.92.0` · `x86_64-unknown-linux-gnu`.
선언 매크로는 **`rustc --edition 2021 <파일>.rs`**, 절차 매크로는 **`rustc --crate-type proc-macro`** 로 직접 빌드한 판과 **`cargo --offline`**(`proc-macro = true`) 판 둘. C 대비는 `gcc 13.3.0 -std=gnu17 -Wall -Wextra`.\
★★★ **외부 크레이트를 하나도 쓰지 않았다** — 절차 매크로는 `syn`/`quote` 없이 **`TokenStream` 을 문자열로 다루는 최소판**이다(그래서 한계가 보인다 — (5)).\
★★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
★ **컴파일 시간·바이너리 크기는 재지 않았다.**
**버전** — `macro_rules!` 는 1.0 · 파생 절차 매크로(「macros 1.1」)는 **1.15.0** · 함수형·속성형까지 「Procedural macros are now available」은 **1.30.0**([Rust `RELEASES.md`](https://github.com/rust-lang/rust/blob/master/RELEASES.md) — 스크래치패드에 받아 둔 사본에서 두 줄을 읽었다) · 로컬 std 문서의 `proc_macro::TokenStream` 「Stable since」 **1.15.0**.
