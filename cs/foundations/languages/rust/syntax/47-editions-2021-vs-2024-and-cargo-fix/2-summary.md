# rust/syntax/47 — 에디션 2021 대 2024 — 같은 코드가 다르게 컴파일되는 자리 · `cargo fix --edition` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Edition Guide — Rust 2024](https://doc.rust-lang.org/edition-guide/rust-2024/)(항목별 페이지 — `if let` 임시값 · 꼬리식 임시값 · RPIT 포착 · `!` 폴백 · `unsafe extern` · unsafe 속성 · `expr` 조각 · `gen` · `Box<[T]>` · 새로 unsafe 가 된 함수 · `static mut` 참조 · `unsafe_op_in_unsafe_fn`) ·
> [Cargo Book — `cargo fix`](https://doc.rust-lang.org/cargo/commands/cargo-fix.html)(「`--edition` 은 매니페스트의 `edition` 을 **갱신하지 않는다**」 · 절차 ① fix ② `edition` 수정 ③ **테스트**).
> ★ 두 문서 모두 **이 머신의 `rust-docs`(1.92.0) 로컬 사본**을 열어 읽었다.
> **실행 검증** — 이 문서의 모든 출력·에러는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `cargo 1.92.0` · `x86_64-unknown-linux-gnu` 에서
> 블록 배너의 **`rustc --edition 2021` / `--edition 2024`** · cargo 명령으로 돌려 받은 것이다(cargo 는 `CARGO_NET_OFFLINE=true`, 의존성 0개).\
> ★★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다. 소스 펜스도 캡처가 찍었다.\
> ★ **버전** — 2021 에디션은 **1.56.0**, 2024 에디션은 **1.85.0** 에 안정화됐다(아래 `tools` 블록 — 로컬 `releases.md`). ★ **속도·메모리는 재지 않았다.**
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

★★★ **본체 창 — ⑧ 에디션 판 격자(같은 소스 × `--edition 2021` / `2024` → 컴파일되나 · 출력이 같은가 · 경고 수)다.** 컴파일러 하나로 두 규칙을 내므로 **차이가 컴파일러 판도 최적화도 아닌 「에디션 그 자체」** 임이 한 줄마다 증명된다.

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
===== echo "CARGO_NET_OFFLINE=$CARGO_NET_OFFLINE" =====
CARGO_NET_OFFLINE=true
(exit 0)
===== awk '/^Version 1\./{v=$2} /The 2021 Edition is now stable|The 2024 Edition is now stable/{print v " | " $0}' "$(rustc --print sysroot)/share/doc/rust/html/releases.md" =====
1.85.0 | - [The 2024 Edition is now stable.](https://github.com/rust-lang/rust/pull/133349)
1.56.0 | - [The 2021 Edition is now stable.][rust#88100]
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| ★★ **흔들린다(정규화)** | `cargo fix` 의 `Finished … in 0.26s` **시간** | 실행마다 바뀐다 — 기본 규칙이 `<time>s` 로 바꾼다 |
| 안 흔들린다 | ★★★ **격자의 두 칸과 「갈린 행 13 / 16」** | 에디션은 **같은 판의 같은 컴파일러가 정한다** — **이 주제의 본체** |
| 안 흔들린다 | `cargo fix` 의 diff · `11 fixes` · 실행 출력 · 진단 번호 · 종료 코드 | 같은 판에서 고정이다 |
| ★ **판이 정한다** | 「2021 에서도 막는」 칸(`missing_frag` · `!` 폴백 린트) | ★ 컴파일러가 **옛 에디션에 켠 린트·에러** — 판이 오르면 달라질 수 있다 |
| ★ **캡처가 바꾼 칸** | cargo 의 절대 경로 → `.` | 배너의 `sed "s\|$PWD\|.\|g"` |

★ 정규화 규칙은 **기본 넷**만 쓴다(시간 칸이 걸린다).

## 한눈에 — 쉽게 말하면

**에디션은 「맞춤법 개정」이다.** 같은 글자(소스)를 **어느 해의 맞춤법으로 읽을지**를 문서마다(크레이트마다) 표지에 적는다.
새 맞춤법에서 바뀐 것은 셋뿐이다 — **새로 쓸 수 없게 된 낱말**(`gen`), **같은 문장의 뜻이 바뀐 것**(`if let` 임시값 · `expr` 조각), **기본값이 바뀐 것**(`!` 폴백 · `impl Trait` 포착).
옛 문서도 표지를 안 바꾸면 계속 옛 맞춤법으로 읽히고, 옛 문서와 새 문서를 한 책(바이너리)에 묶을 수 있다. 표지를 바꿀 때는 **교정기**(`cargo fix --edition`)가 옛 뜻을 지키는 쪽으로 고쳐 주지만 — **전부는 못 잡는다.**

| 비유 | 실체 |
|---|---|
| 「**새로 금지된 낱말**」 | ★★ **`gen` 이 예약어** — 2021 크레이트의 `gen` 은 2024 에서 **`r#gen`** 으로 부른다((1)·(4)) |
| 「**같은 문장, 다른 뜻**」 | ★★★ **통과하는데 출력이 다른 4행** — `Box<[T]>` · `!` 폴백 · `expr` 조각 · `if let` 임시값((1)) |
| 「**더 엄격해진 규정**」 | ★★ **2021 통과 → 2024 에러 6행** — `unsafe extern` · `unsafe(no_mangle)` · `set_var` · `static mut` 참조 · RPIT 포착 · `gen`((1)) |
| 「**더 너그러워진 규정**」 | ★★ **2021 에러 → 2024 통과 2행** — 꼬리식 임시값 · `let` 체인((1)) |
| 「**표지는 사람이 바꾼다**」 | ★★★ **`cargo fix --edition` 은 `edition` 을 안 올린다**((3)) |
| 「**교정기가 놓친 한 문장**」 | ★★★ **`RefCell` 가드의 `if let`** — 고쳐지지 않아 **`free=false` → `free=true`**((3)) |
| 「**옛 문서와 새 문서를 한 책에**」 | ★★ **2021 rlib + 2024 바이너리가 링크된다**((4)) |

```text
   (1)의 16행을 한 장으로

   2021 통과 → 2024 에러 (6)   gen_ident · extern_block · no_mangle · set_var · static_mut · rpit_capture
   2021 에러 → 2024 통과 (2)   tail_temp · let_chain
   둘 다 통과, 출력이 다름 (4)  boxed_slice · never_typename · macro_expr · iflet_drop    ← 컴파일러가 말없이 뜻을 바꾼다
   둘 다 통과, 경고만 다름 (1)  unsafe_op
   같음 (3)                    array_into_iter · closure_capture (2018→2021 의 변화) · missing_frag (둘 다 에러)
```

> **에디션(edition)** — 크레이트마다 고르는 **언어 규칙의 판**(2015·2018·2021·2024). `Cargo.toml` 의 `edition` · rustc 의 `--edition` 으로 정한다.\
> 예: 같은 `let gen = 1;` 이 2021 에서는 통과, 2024 에서는 「reserved keyword」 에러.

> **원시 식별자(raw identifier)** — `r#이름` 꼴. 예약어를 **이름으로** 쓰게 한다.\
> 예: 2021 크레이트의 `pub fn gen()` 을 2024 크레이트가 `r#gen()` 으로 부른다.

## 이 주제가 답하려는 질문

1. ★★★ **같은 소스가 2021 과 2024 에서 어디서 갈리나 — 그중 무엇이 조용히 갈리나**((1)).
2. ★★★ **`cargo fix --edition` 은 무엇을 고치고, 무엇을 안 고치고, 무엇을 안 하나**((2)·(3)).
3. ★★ **에디션은 무엇의 단위인가 — 섞어 쓸 수 있나**((4)).

★ **선행** — [**46번 주제**](../46-crates-cargo-toml-features-and-workspaces/) — 에디션은 `Cargo.toml` 의 한 줄이고, **resolver 기본값**도 에디션이 정한다(2021 → 2 · 2024 → 3, 그 편 (4)).
★★★ **이미 잰 것 — 다시 재지 않고 인용한다**(격자에는 **한 칸씩만** 다시 놓았다).
[42번](../42-refcell-cell-interior-mutability/) (2) — **`if let` 가드 × 두 에디션 — 패닉 칸 3 / 4** · [32번](../32-impl-trait-argument-return-position-and-2024-capture/) (5) — **RPIT 포착 네 칸** · [37번](../37-intoiterator-three-forms-iter-iter-mut-into-iter/) (2) — **`.into_iter()` 네 판**(배열 2021 · `Box<[T]>` 2024) ·
[20번](../20-if-let-while-let-let-else-and-let-chains/) — **`let` 체인 1.88 + 2024** · [07번](../07-const-static-and-const-fn/) 5번 — **`static mut` 2021 경고 / 2024 에러** · [11번](../11-borrow-checker-rejections/) (11) — **한 파일 2021 E0597 / 2024 통과** · [01번](../01-cargo-crates-and-modules/) — **`cargo new` 는 2024, `rustc` 기본은 2015**.
[`history/rust/02-에디션.md`](../../../../../../history/rust/02-에디션.md) — **에디션 제도의 연혁**(2015 → 2024 · opt-in · 크레이트 단위 · 「새 기능 ≠ 에디션 전용」). 이 편은 **「내 코드가 무엇을 고쳐야 하나」** 로 좁힌다.

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ⑧ 에디션 판 격자다

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ⑧ ★★★ **에디션 판 격자**(같은 소스 × 2021/2024 — 컴파일 · 출력 · 경고 수) | **어디서 갈리나 · 어떻게 갈리나** | ★ **본체**((1)) |
| ⑨ ★★★ **`cargo fix --edition` 의 diff** | 교정기가 **옛 뜻을 지키려고** 무엇을 바꾸나 | 쓴다((3)) |
| ③ ★★ **린트 묶음 `rust_2024_compatibility`**(기본 꺼짐 — `-W` 로 켠다) | 올리기 **전에** 무엇이 깨질지 | 쓴다((2)) |
| ① ★★ **판 올린 뒤 실행 출력 대조** | 교정 뒤에도 **뜻이 바뀐 칸**이 남았나 | 쓴다((3)) — ★ **③ 이 침묵한 칸을 잡은 창** |
| 2015·2018 판 | — | ★ **이미 잰 것** — 37번 (2)의 네 판 격자 · 45번 (5)의 `extern crate` |

★★ **제5의 상태 — 「같은 질문을 다른 창으로」.** 「교정 뒤 뜻이 그대로인가」를 ③ 린트 목록에 물으면 **`first_even` 의 `if let` 이 목록에 없어** 「안전하다」로 읽힌다. **판을 올린 뒤 실행 출력을 두 번 찍어 대조**(①)해야 `free=false` → `free=true` 가 보인다 — 린트가 **못 보는 것**을 출력이 봤다.

### (1) ★★★ 열여섯 소스 × 두 에디션 — 격자

**언제 쓰나** — `edition` 을 올리기 전에 「내 코드에 이 모양이 있나」를 훑을 때.

```text
===== 소스: r47_grid.sh =====
# 소스 하나를 --edition 2021 과 --edition 2024 로 각각 컴파일·실행해 두 결과를 한 줄에 놓는다
# 결과 칸 = 「runs: 표준 출력(줄은 / 로 이음)」 또는 첫 error 줄, 그리고 경고 수(요약 줄 제외)
T=$'\t'
names=()
probe() { names+=("$1"); cat > "$1.rs"; }

probe gen_ident <<'RS'
fn main() {
    let gen = 1;
    println!("{gen}");
}
RS
probe extern_block <<'RS'
extern "C" {
    fn abs(x: i32) -> i32;
}

fn main() {
    println!("{}", unsafe { abs(-3) });
}
RS
probe no_mangle <<'RS'
#[no_mangle]
pub extern "C" fn exported() -> i32 {
    1
}

fn main() {
    println!("{}", exported());
}
RS
probe set_var <<'RS'
fn main() {
    std::env::set_var("PROBE_VAR", "1");
    println!("{}", std::env::var("PROBE_VAR").unwrap());
}
RS
probe static_mut <<'RS'
static mut COUNT: i32 = 0;

fn main() {
    unsafe {
        COUNT += 1;
        let r = &COUNT;
        println!("{r}");
    }
}
RS
probe unsafe_op <<'RS'
unsafe fn read(p: *const i32) -> i32 {
    *p
}

fn main() {
    let x = 5;
    println!("{}", unsafe { read(&x) });
}
RS
probe rpit_capture <<'RS'
fn counter(v: &Vec<i32>) -> impl Fn() -> usize {
    let n = v.len();
    move || n
}

fn main() {
    let mut v = vec![1, 2];
    let c = counter(&v);
    v.push(3);
    println!("{} {}", c(), v.len());
}
RS
probe boxed_slice <<'RS'
fn main() {
    let b: Box<[i32]> = vec![1, 2].into_boxed_slice();
    for x in b.into_iter() {
        println!("{}", std::any::type_name_of_val(&x));
    }
}
RS
probe never_typename <<'RS'
fn result_type<T>(_: impl FnOnce() -> T) -> &'static str {
    std::any::type_name::<T>()
}

fn main() {
    println!("{}", result_type(|| panic!()));
}
RS
probe macro_expr <<'RS'
macro_rules! kind {
    ($e:expr) => {
        "expr"
    };
    (const $b:block) => {
        "const block"
    };
    (_) => {
        "underscore"
    };
}

fn main() {
    println!("{} {}", kind!(const { 1 }), kind!(_));
}
RS
probe tail_temp <<'RS'
use std::cell::RefCell;

fn len() -> usize {
    let c = RefCell::new(vec![1, 2, 3]);
    c.borrow().len()
}

fn main() {
    println!("{}", len());
}
RS
probe iflet_drop <<'RS'
struct Guard(&'static str);
impl Drop for Guard {
    fn drop(&mut self) {
        println!("drop {}", self.0);
    }
}
impl Guard {
    fn get(&self) -> Option<i32> {
        None
    }
}

fn main() {
    if let Some(n) = Guard("temp").get() {
        println!("then {n}");
    } else {
        println!("else branch");
    }
}
RS
probe let_chain <<'RS'
fn main() {
    let a = Some(3);
    if let Some(x) = a && x > 2 {
        println!("big {x}");
    }
}
RS
probe array_into_iter <<'RS'
fn main() {
    let a = [1, 2];
    for x in a.into_iter() {
        println!("{}", std::any::type_name_of_val(&x));
    }
}
RS
probe closure_capture <<'RS'
struct P {
    a: String,
    b: String,
}
impl Drop for P {
    fn drop(&mut self) {}
}

fn main() {
    let p = P { a: String::from("a"), b: String::from("b") };
    let c = || println!("{}", p.a);
    c();
    println!("{}", p.b);
}
RS
probe missing_frag <<'RS'
macro_rules! first {
    ($x) => {};
}

fn main() {
    println!("ok");
}
RS

run() {  # $1 = 이름, $2 = 에디션 → 결과 칸 한 줄
  local out w
  if rustc --edition "$2" -o "$1_$2" "$1.rs" 2>err.txt; then
    out="runs: $(./"$1_$2" | paste -sd/)"
  else
    out=$(grep -m1 '^error' err.txt)
  fi
  w=$(grep -v 'emitted$' err.txt | grep -c '^warning')
  printf '%s (warnings %s)' "$out" "$w"
}

printf 'probe\t2021\t2024\n'
diff=0; total=0
for n in "${names[@]}"; do
  a=$(run "$n" 2021); b=$(run "$n" 2024)
  [ "$a" != "$b" ] && diff=$((diff+1))
  row="$n$T$a$T$b"
  c=$(printf '%s' "$row" | awk -F'\t' '{print NF}')
  [ "$c" = 3 ] || { echo "column count $c != 3"; exit 1; }
  printf '%s\n' "$row"
  total=$((total+1))
done
echo "rows where the two editions differ: $diff / $total"
===== bash r47_grid.sh =====
probe	2021	2024
gen_ident	runs: 1 (warnings 0)	error: expected identifier, found reserved keyword `gen` (warnings 0)
extern_block	runs: 3 (warnings 0)	error: extern blocks must be unsafe (warnings 0)
no_mangle	runs: 1 (warnings 0)	error: unsafe attribute used without unsafe (warnings 0)
set_var	runs: 1 (warnings 0)	error[E0133]: call to unsafe function `set_var` is unsafe and requires unsafe block (warnings 0)
static_mut	runs: 1 (warnings 1)	error: creating a shared reference to mutable static (warnings 0)
unsafe_op	runs: 5 (warnings 0)	runs: 5 (warnings 1)
rpit_capture	runs: 2 3 (warnings 0)	error[E0502]: cannot borrow `v` as mutable because it is also borrowed as immutable (warnings 0)
boxed_slice	runs: &i32/&i32 (warnings 1)	runs: i32/i32 (warnings 0)
never_typename	runs: () (warnings 0)	runs: ! (warnings 0)
macro_expr	runs: const block underscore (warnings 0)	runs: expr expr (warnings 0)
tail_temp	error[E0597]: `c` does not live long enough (warnings 0)	runs: 3 (warnings 0)
iflet_drop	runs: else branch/drop temp (warnings 0)	runs: drop temp/else branch (warnings 0)
let_chain	error: let chains are only allowed in Rust 2024 or later (warnings 0)	runs: big 3 (warnings 0)
array_into_iter	runs: i32/i32 (warnings 0)	runs: i32/i32 (warnings 0)
closure_capture	runs: a/b (warnings 0)	runs: a/b (warnings 0)
missing_frag	error: missing fragment specifier (warnings 1)	error: missing fragment specifier (warnings 1)
rows where the two editions differ: 13 / 16
(exit 0)
```

- ★★★ **「갈린 행 13 / 16」.** 갈린 모양은 넷이다 — **2024 에러 6 · 2021 에러 2 · 출력만 다름 4 · 경고만 다름 1.**
- ★★★ **출력만 다른 4행이 가장 위험하다** — 컴파일러가 **아무 말 없이** 뜻을 바꾼다.
  `boxed_slice`(`&i32` → `i32`, 2021 에서 **경고 1개**로 미리 알려 준다) · **`never_typename`(`()` → `!`) · `macro_expr`(`const block underscore` → `expr expr`) · `iflet_drop`(`else branch` 와 `drop temp` 의 순서가 뒤집힘)은 2021 에서 경고 0개**다.
- ★★ **2021 에러 → 2024 통과** — `tail_temp`(꼬리식의 `c.borrow()` 임시값이 2024 에서 **`c` 보다 먼저** 버려진다) · `let_chain`.
- ★ **같은 3행** — `array_into_iter`·`closure_capture` 는 **2018 → 2021** 의 변화라 2021·2024 사이에서는 같다(37번이 네 판으로 쟀다). `missing_frag` 는 에디션 가이드의 2024 항목인데 **1.92 에서는 두 판 모두 에러**다.

### (2) ★★★ 2021 패키지 — 올리기 전에 무엇이 보이나

**언제 쓰나** — `cargo fix` 를 치기 전, 「지금 경고가 없으니 괜찮다」고 판단하려 할 때.

```text
===== 소스: r47_fix_main.rs =====
use std::cell::RefCell;

extern "C" {
    fn abs(x: i32) -> i32;
}

#[no_mangle]
pub extern "C" fn exported() -> i32 {
    1
}

macro_rules! twice {
    ($e:expr) => {
        $e * 2
    };
}

unsafe fn read(p: *const i32) -> i32 {
    *p
}

fn counter(v: &Vec<i32>) -> impl Fn() -> usize {
    let n = v.len();
    move || n
}

struct Guard(&'static str);
impl Drop for Guard {
    fn drop(&mut self) {
        println!("drop {}", self.0);
    }
}
impl Guard {
    fn get(&self) -> Option<i32> {
        None
    }
}

fn guarded() {
    if let Some(n) = Guard("g").get() {
        println!("then {n}");
    } else {
        println!("else");
    }
}

fn first_even(c: &RefCell<Vec<i32>>) -> String {
    if let Some(x) = c.borrow().iter().find(|x| *x % 2 == 0) {
        format!("even {x}")
    } else {
        format!("free={}", c.try_borrow_mut().is_ok())
    }
}

fn main() {
    let gen = 2;
    let b: Box<[i32]> = vec![gen, 3].into_boxed_slice();
    let mut total = 0;
    for x in b.into_iter() {
        total += x;
    }
    std::env::set_var("PROBE_VAR", "1");
    let x = 5;
    let mut v = vec![1];
    let count = counter(&v);
    v.push(2);
    guarded();
    let c = RefCell::new(vec![1, 3]);
    println!(
        "{} {} {} {} {} {} {}",
        unsafe { abs(-3) },
        exported(),
        twice!(gen),
        unsafe { read(&x) },
        count(),
        total,
        first_even(&c)
    );
}
===== 소스: r47_fix.Cargo.toml =====
[package]
name = "fixdemo"
version = "0.1.0"
edition = "2021"
===== mkdir src && cp r47_fix_main.rs src/main.rs && cp r47_fix.Cargo.toml Cargo.toml =====
(exit 0)
===== cargo run -q 2>/dev/null =====
else
drop g
3 1 4 5 1 5 free=false
===== cargo run -q 2>&1 >/dev/null =====
warning: this method call resolves to `<&Box<[T]> as IntoIterator>::into_iter` (due to backwards compatibility), but will resolve to `<Box<[T]> as IntoIterator>::into_iter` in Rust 2024
  --> src/main.rs:59:16
   |
59 |     for x in b.into_iter() {
   |                ^^^^^^^^^
   |
   = warning: this changes meaning in Rust 2024
   = note: for more information, see <https://doc.rust-lang.org/edition-guide/rust-2024/intoiterator-box-slice.html>
   = note: `#[warn(boxed_slice_into_iter)]` (part of `#[warn(rust_2024_compatibility)]`) on by default
help: use `.iter()` instead of `.into_iter()` to avoid ambiguity
   |
59 -     for x in b.into_iter() {
59 +     for x in b.iter() {
   |
help: or remove `.into_iter()` to iterate by value
   |
59 -     for x in b.into_iter() {
59 +     for x in b {
   |

(exit 0)
```

- ★★★ **기본 경고는 `boxed_slice_into_iter` 하나** — 이 파일에는 (1)에서 2024 가 갈라놓은 모양이 **여럿** 더 있다.

```text
===== 소스: r47_fix_main.rs =====
use std::cell::RefCell;

extern "C" {
    fn abs(x: i32) -> i32;
}

#[no_mangle]
pub extern "C" fn exported() -> i32 {
    1
}

macro_rules! twice {
    ($e:expr) => {
        $e * 2
    };
}

unsafe fn read(p: *const i32) -> i32 {
    *p
}

fn counter(v: &Vec<i32>) -> impl Fn() -> usize {
    let n = v.len();
    move || n
}

struct Guard(&'static str);
impl Drop for Guard {
    fn drop(&mut self) {
        println!("drop {}", self.0);
    }
}
impl Guard {
    fn get(&self) -> Option<i32> {
        None
    }
}

fn guarded() {
    if let Some(n) = Guard("g").get() {
        println!("then {n}");
    } else {
        println!("else");
    }
}

fn first_even(c: &RefCell<Vec<i32>>) -> String {
    if let Some(x) = c.borrow().iter().find(|x| *x % 2 == 0) {
        format!("even {x}")
    } else {
        format!("free={}", c.try_borrow_mut().is_ok())
    }
}

fn main() {
    let gen = 2;
    let b: Box<[i32]> = vec![gen, 3].into_boxed_slice();
    let mut total = 0;
    for x in b.into_iter() {
        total += x;
    }
    std::env::set_var("PROBE_VAR", "1");
    let x = 5;
    let mut v = vec![1];
    let count = counter(&v);
    v.push(2);
    guarded();
    let c = RefCell::new(vec![1, 3]);
    println!(
        "{} {} {} {} {} {} {}",
        unsafe { abs(-3) },
        exported(),
        twice!(gen),
        unsafe { read(&x) },
        count(),
        total,
        first_even(&c)
    );
}
===== rustc --edition 2021 --emit=metadata -W rust-2024-compatibility r47_fix_main.rs 2>&1 >/dev/null | grep -E "^warning" =====
warning: `gen` is a keyword in the 2024 edition
warning: `gen` is a keyword in the 2024 edition
warning: `gen` is a keyword in the 2024 edition
warning: extern blocks should be unsafe
warning: unsafe attribute used without unsafe
warning: the `expr` fragment specifier will accept more expressions in the 2024 edition
warning[E0133]: dereference of raw pointer is unsafe and requires unsafe block
warning: call to deprecated safe function `std::env::set_var` is unsafe and requires unsafe block
warning: `impl Fn() -> usize` will capture more lifetimes than possibly intended in edition 2024
warning: `if let` assigns a shorter lifetime since Edition 2024
warning: this method call resolves to `<&Box<[T]> as IntoIterator>::into_iter` (due to backwards compatibility), but will resolve to `<Box<[T]> as IntoIterator>::into_iter` in Rust 2024
warning: 11 warnings emitted
(exit 0)
```

- ★★★ **묶음을 켜면 경고 11개**(요약 줄 제외) — `gen` 셋 · `unsafe extern` · unsafe 속성 · `expr` 조각 · `unsafe_op`(E0133) · `set_var` · RPIT 포착 · **`if let` 하나** · `Box<[T]>`. ★ **`if let` 은 둘인데 경고는 하나** — `first_even` 의 것이 없다((3)).

**판만 올리면.**

```text
===== 소스: r47_fix_main.rs =====
use std::cell::RefCell;

extern "C" {
    fn abs(x: i32) -> i32;
}

#[no_mangle]
pub extern "C" fn exported() -> i32 {
    1
}

macro_rules! twice {
    ($e:expr) => {
        $e * 2
    };
}

unsafe fn read(p: *const i32) -> i32 {
    *p
}

fn counter(v: &Vec<i32>) -> impl Fn() -> usize {
    let n = v.len();
    move || n
}

struct Guard(&'static str);
impl Drop for Guard {
    fn drop(&mut self) {
        println!("drop {}", self.0);
    }
}
impl Guard {
    fn get(&self) -> Option<i32> {
        None
    }
}

fn guarded() {
    if let Some(n) = Guard("g").get() {
        println!("then {n}");
    } else {
        println!("else");
    }
}

fn first_even(c: &RefCell<Vec<i32>>) -> String {
    if let Some(x) = c.borrow().iter().find(|x| *x % 2 == 0) {
        format!("even {x}")
    } else {
        format!("free={}", c.try_borrow_mut().is_ok())
    }
}

fn main() {
    let gen = 2;
    let b: Box<[i32]> = vec![gen, 3].into_boxed_slice();
    let mut total = 0;
    for x in b.into_iter() {
        total += x;
    }
    std::env::set_var("PROBE_VAR", "1");
    let x = 5;
    let mut v = vec![1];
    let count = counter(&v);
    v.push(2);
    guarded();
    let c = RefCell::new(vec![1, 3]);
    println!(
        "{} {} {} {} {} {} {}",
        unsafe { abs(-3) },
        exported(),
        twice!(gen),
        unsafe { read(&x) },
        count(),
        total,
        first_even(&c)
    );
}
===== 소스: r47_fix.Cargo.toml =====
[package]
name = "fixdemo"
version = "0.1.0"
edition = "2021"
===== mkdir src && cp r47_fix_main.rs src/main.rs && cp r47_fix.Cargo.toml Cargo.toml =====
(exit 0)
===== sed -i "s/edition = \"2021\"/edition = \"2024\"/" Cargo.toml =====
(exit 0)
===== cargo build -q 2>&1 >/dev/null | grep -E "^error" =====
error: expected identifier, found reserved keyword `gen`
error: expected expression, found reserved keyword `gen`
error: expected expression, found reserved keyword `gen`
error: extern blocks must be unsafe
error: unsafe attribute used without unsafe
error: could not compile `fixdemo` (bin "fixdemo") due to 5 previous errors; 1 warning emitted
(exit 101)
```

- ★★ **에러 5개로 멈춘다** — 구문·속성 단계(`gen` · `extern` · `no_mangle`)에서 막혀 **타입·빌림 검사까지 안 간다.** (1)에서 2024 가 막은 `set_var`(E0133)·`rpit_capture`(E0502) 모양이 여기 있는데 **안 나왔다.** 「에러 N개」는 **첫 관문의 수**다.

### (3) ★★★ `cargo fix --edition` — 무엇을 고치고, 무엇을 안 하고, 무엇을 놓치나

**언제 쓰나** — 에디션을 올릴 때마다. **순서는 fix → `edition` 수정 → 테스트.**

```text
===== 소스: r47_fix_main.rs =====
use std::cell::RefCell;

extern "C" {
    fn abs(x: i32) -> i32;
}

#[no_mangle]
pub extern "C" fn exported() -> i32 {
    1
}

macro_rules! twice {
    ($e:expr) => {
        $e * 2
    };
}

unsafe fn read(p: *const i32) -> i32 {
    *p
}

fn counter(v: &Vec<i32>) -> impl Fn() -> usize {
    let n = v.len();
    move || n
}

struct Guard(&'static str);
impl Drop for Guard {
    fn drop(&mut self) {
        println!("drop {}", self.0);
    }
}
impl Guard {
    fn get(&self) -> Option<i32> {
        None
    }
}

fn guarded() {
    if let Some(n) = Guard("g").get() {
        println!("then {n}");
    } else {
        println!("else");
    }
}

fn first_even(c: &RefCell<Vec<i32>>) -> String {
    if let Some(x) = c.borrow().iter().find(|x| *x % 2 == 0) {
        format!("even {x}")
    } else {
        format!("free={}", c.try_borrow_mut().is_ok())
    }
}

fn main() {
    let gen = 2;
    let b: Box<[i32]> = vec![gen, 3].into_boxed_slice();
    let mut total = 0;
    for x in b.into_iter() {
        total += x;
    }
    std::env::set_var("PROBE_VAR", "1");
    let x = 5;
    let mut v = vec![1];
    let count = counter(&v);
    v.push(2);
    guarded();
    let c = RefCell::new(vec![1, 3]);
    println!(
        "{} {} {} {} {} {} {}",
        unsafe { abs(-3) },
        exported(),
        twice!(gen),
        unsafe { read(&x) },
        count(),
        total,
        first_even(&c)
    );
}
===== 소스: r47_fix.Cargo.toml =====
[package]
name = "fixdemo"
version = "0.1.0"
edition = "2021"
===== mkdir src && cp r47_fix_main.rs src/main.rs && cp r47_fix.Cargo.toml Cargo.toml =====
(exit 0)
===== cargo fix --edition --allow-no-vcs 2>&1 >/dev/null | sed "s|$PWD|.|g" =====
   Migrating Cargo.toml from 2021 edition to 2024
    Checking fixdemo v0.1.0 (.)
   Migrating src/main.rs from 2021 edition to 2024
       Fixed src/main.rs (11 fixes)
    Finished `dev` profile [unoptimized + debuginfo] target(s) in 0.23s
(exit 0)
===== diff -u --label before --label after r47_fix_main.rs src/main.rs =====
--- before
+++ after
@@ -1,25 +1,25 @@
 use std::cell::RefCell;
 
-extern "C" {
+unsafe extern "C" {
     fn abs(x: i32) -> i32;
 }
 
-#[no_mangle]
+#[unsafe(no_mangle)]
 pub extern "C" fn exported() -> i32 {
     1
 }
 
 macro_rules! twice {
-    ($e:expr) => {
+    ($e:expr_2021) => {
         $e * 2
     };
 }
 
-unsafe fn read(p: *const i32) -> i32 {
+unsafe fn read(p: *const i32) -> i32 { unsafe {
     *p
-}
+}}
 
-fn counter(v: &Vec<i32>) -> impl Fn() -> usize {
+fn counter(v: &Vec<i32>) -> impl Fn() -> usize + use<> {
     let n = v.len();
     move || n
 }
@@ -37,11 +37,11 @@
 }
 
 fn guarded() {
-    if let Some(n) = Guard("g").get() {
+    match Guard("g").get() { Some(n) => {
         println!("then {n}");
-    } else {
+    } _ => {
         println!("else");
-    }
+    }}
 }
 
 fn first_even(c: &RefCell<Vec<i32>>) -> String {
@@ -53,13 +53,14 @@
 }
 
 fn main() {
-    let gen = 2;
-    let b: Box<[i32]> = vec![gen, 3].into_boxed_slice();
+    let r#gen = 2;
+    let b: Box<[i32]> = vec![r#gen, 3].into_boxed_slice();
     let mut total = 0;
-    for x in b.into_iter() {
+    for x in b.iter() {
         total += x;
     }
-    std::env::set_var("PROBE_VAR", "1");
+    // TODO: Audit that the environment access only happens in single-threaded code.
+    unsafe { std::env::set_var("PROBE_VAR", "1") };
     let x = 5;
     let mut v = vec![1];
     let count = counter(&v);
@@ -70,7 +71,7 @@
         "{} {} {} {} {} {} {}",
         unsafe { abs(-3) },
         exported(),
-        twice!(gen),
+        twice!(r#gen),
         unsafe { read(&x) },
         count(),
         total,
(exit 1)
===== grep -n edition Cargo.toml =====
4:edition = "2021"
(exit 0)
===== sed -i "s/edition = \"2021\"/edition = \"2024\"/" Cargo.toml =====
(exit 0)
===== cargo run -q =====
else
drop g
3 1 4 5 1 5 free=true
(exit 0)
```

- ★★★ **고친 것(11 fixes)** — 전부 **「2024 로 읽혀도 2021 의 뜻이 유지되도록」** 고친다.

```text
   2021 에 쓴 것                      cargo fix 가 바꾼 것                 지키려는 뜻
   extern "C" { … }                  unsafe extern "C" { … }            (2024 에서 필수 표기)
   #[no_mangle]                      #[unsafe(no_mangle)]               (2024 에서 필수 표기)
   ($e:expr)                         ($e:expr_2021)                     const {} · _ 를 안 받던 옛 뜻
   unsafe fn … { *p }                unsafe fn … { unsafe { *p } }      2024 의 unsafe_op_in_unsafe_fn
   -> impl Fn() -> usize             -> impl Fn() -> usize + use<>      인자 수명을 안 품던 옛 포착
   if let … { } else { }             match … { Some(n) => …, _ => … }   임시값이 else 까지 살던 옛 수명
   let gen = 2;                      let r#gen = 2;                     예약어 회피
   b.into_iter()   (Box<[T]>)        b.iter()                           &T 로 돌던 옛 뜻
   std::env::set_var(..)             unsafe { … } + // TODO: Audit …   2024 에서 unsafe 가 된 함수
```

- ★★★ **안 하는 것 — `Cargo.toml` 의 `edition` 은 `"2021"` 그대로다.** `Migrating Cargo.toml` 이라고 찍지만 판을 안 올린다(cargo 문서: 「`--edition` 은 매니페스트의 `edition` 을 갱신하지 않는다」).
- ★★★ **놓친 것 — `first_even` 의 `if let`(std `RefCell` 가드).** 올린 뒤 실행하면 **`free=false` → `free=true`** — 같은 규칙의 `guarded()`(사용자 `impl Drop` 을 가진 `Guard`)는 `match` 로 고쳐져 순서를 지켰다. 에디션 가이드는 `if_let_rescope` 가 **「사용자 정의의 사소하지 않은 `Drop` 을 가진 임시값」** 일 때 제안한다고 적는데, **이 판에서 `Ref` 가드 모양은 침묵했다**(어느 조건 때문인지는 확인하지 않았다).
- ★★ 그래서 cargo 문서의 셋째 단계가 **「테스트를 돌려 전부 여전히 동작하는지 확인하라」** 다 — 린트가 못 본 칸은 **출력**이 본다.

### (4) ★★ 에디션은 크레이트 단위 — 섞어 링크된다

```text
===== 소스: r47_user2024.rs =====
fn main() {
    println!("{}", r47_lib2021::r#gen());
}
===== 소스: r47_lib2021.rs =====
pub fn gen() -> i32 {
    7
}
===== rustc --edition 2021 --crate-type lib r47_lib2021.rs =====
(exit 0)
===== rustc --edition 2024 --extern r47_lib2021=libr47_lib2021.rlib r47_user2024.rs =====
(exit 0)
===== ./r47_user2024 =====
7
(exit 0)
```

```text
===== 소스: r47_user2024_plain.rs =====
fn main() {
    println!("{}", r47_lib2021::gen());
}
===== 소스: r47_lib2021.rs =====
pub fn gen() -> i32 {
    7
}
===== rustc --edition 2021 --crate-type lib r47_lib2021.rs =====
(exit 0)
===== rustc --edition 2024 --extern r47_lib2021=libr47_lib2021.rlib r47_user2024_plain.rs =====
error: expected identifier, found reserved keyword `gen`
 --> r47_user2024_plain.rs:2:33
  |
2 |     println!("{}", r47_lib2021::gen());
  |                                 ^^^ expected identifier, found reserved keyword
  |
help: escape `gen` to use it as an identifier
  |
2 |     println!("{}", r47_lib2021::r#gen());
  |                                 ++

error: aborting due to 1 previous error

(exit 1)
```

- ★★★ **2021 rlib 의 `pub fn gen` 을 2024 바이너리가 `r#gen()` 으로 불러 실행했다(`7`).** 맨 `gen()` 은 **파싱 단계**에서 막힌다(`help:` 가 `r#` 를 권한다).
- ★★ 에디션은 **소스를 읽는 규칙**이지 **산출물의 형식이 아니다** — 그래서 생태계가 한꺼번에 이사하지 않아도 된다(history 02 의 「크레이트 단위 격리 + 무결한 상호운용」).

**옛 에디션에도 미리 켜진 칸.**

```text
===== 소스: r47_never.rs =====
fn make<T: Default>() -> T {
    T::default()
}

fn main() {
    let flag = false;
    let _x = if flag { panic!() } else { make() };
    println!("done");
}
===== rustc --edition 2021 r47_never.rs =====
error: this function depends on never type fallback being `()`
 --> r47_never.rs:5:1
  |
5 | fn main() {
  | ^^^^^^^^^
  |
  = warning: this was previously accepted by the compiler but is being phased out; it will become a hard error in Rust 2024 and in a future release in all editions!
  = note: for more information, see <https://doc.rust-lang.org/edition-guide/rust-2024/never-type-fallback.html>
  = help: specify the types explicitly
note: in edition 2024, the requirement `!: Default` will fail
 --> r47_never.rs:7:42
  |
7 |     let _x = if flag { panic!() } else { make() };
  |                                          ^^^^^^
  = note: `#[deny(dependency_on_unit_never_type_fallback)]` (part of `#[deny(rust_2024_compatibility)]`) on by default
help: use `()` annotations to avoid fallback changes
  |
7 |     let _x: () = if flag { panic!() } else { make() };
  |           ++++

error: aborting due to 1 previous error

(exit 1)
===== rustc --edition 2024 r47_never.rs =====
error[E0277]: the trait bound `!: Default` is not satisfied
 --> r47_never.rs:7:42
  |
7 |     let _x = if flag { panic!() } else { make() };
  |                                          ^^^^^^ the trait `Default` is not implemented for `!`
  |
  = note: this error might have been caused by changes to Rust's type-inference algorithm (see issue #48950 <https://github.com/rust-lang/rust/issues/48950> for more information)
  = help: you might have intended to use the type `()` here instead
note: required by a bound in `make`
 --> r47_never.rs:1:12
  |
1 | fn make<T: Default>() -> T {
  |            ^^^^^^^ required by this bound in `make`

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0277`.
(exit 1)
```

- ★★★ **2021 도 막힌다** — 에러가 아니라 **기본 거부(deny) 린트** `dependency_on_unit_never_type_fallback` 이고, 「앞으로 **모든 에디션**에서 hard error 가 된다」고 적는다. 2024 는 폴백이 `!` 라 **E0277 `!: Default`**. 「2021 은 되고 2024 만 막힌다」가 **이 판에서는 틀렸다.**

## 문법 — 형태와 규칙

```text
   Cargo.toml   [package] edition = "2024"      ← 크레이트 하나에 하나 (cargo new 의 기본은 2024 — 01번)
   rustc        --edition 2024                  ← rustc 의 기본은 2015 (01번)

   올리는 절차 (cargo 문서)
   ① cargo fix --edition            ← 판은 그대로, 코드를 「두 판 모두에서 옛 뜻」으로 고친다
   ② edition = "2024"               ← 사람이 고친다
   ③ cargo test                      ← 린트가 못 본 뜻의 변화를 여기서 잡는다
```

- ★★★ **에디션이 가르는 것은 옛 코드를 깨는 변화뿐** — 예약어 · 뜻의 변화 · 기본값 전환(history 02).
- ★★★ **`cargo fix` 는 옛 뜻을 보존하는 쪽으로 고친다**(`expr_2021` · `use<>` · `match`) — **2024 의 새 뜻을 원하면 그다음에 사람이 바꾼다.**
- ★★ **에디션은 크레이트 단위, 링크는 자유**((4)).

## 어디서 틀리나

### 1. ★★★ 「2021 에서 경고가 없으니 올려도 된다」

(2) — **기본 경고는 하나뿐**이었고, 올리면 에러 5개(그 뒤에 더). `-W rust-2024-compatibility` 로 켜야 보인다.

### 2. ★★★ 「`cargo fix --edition` 을 쳤으니 이사가 끝났다」

(3) — **`edition` 은 안 바뀌었고**, 올린 뒤에도 **뜻이 바뀐 칸이 하나 남았다**(`free=`). 테스트가 마지막 단계다.

### 3. ★★ 「에디션을 올리면 컴파일 에러로 다 알려 준다」

(1) — **출력만 다른 4행**은 에러도 경고도 없이 뜻이 바뀐다.

### 4. ★★ 「에러 목록이 곧 고칠 목록」

(2) — 첫 관문에서 멈춘다. 고칠 때마다 **다음 관문의 에러**가 나온다.

### 5. ★★ 「2021 코드는 1.92 에서도 예전처럼 컴파일된다」

(1)·(4) — `missing_frag` 와 `!` 폴백은 **1.92 가 2021 에도 막았다.** 에디션은 「그 판의 컴파일러가 그 에디션에 적용하는 규칙」이다.

### 6. ★ 「`gen` 을 쓴 옛 라이브러리는 2024 에서 못 쓴다」

(4) — **`r#gen`** 으로 부른다.

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| 에디션별 규칙(예약어 · 임시값 · 폴백 · 포착 · unsafe 표기) | ★ **언어**(Edition Guide · Reference) | (1) |
| 에디션이 크레이트 단위이고 섞어 링크된다 | ★ **언어·툴체인의 약속**(Edition Guide · history 02) | (4) |
| 어떤 린트가 기본 경고/거부인가 | ★ **rustc 린트 설정** — 판에 매인다 | (2)·(4) |
| 옛 에디션에서도 막는 칸(`missing_frag` · `!` 폴백) | ★ **컴파일러 판**(1.92)의 결정 | (1)·(4) |
| `cargo fix` 가 무엇을 고치나 · `if_let_rescope` 가 짚는 모양 | ★ **린트 구현**(rustc) + **cargo** — 에디션 가이드는 조건을 서술할 뿐 | (3) |
| `cargo fix` 가 `edition` 을 안 올린다 | ★ **cargo 문서** | (3) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 근거 |
|---|---|---|
| 판을 올린다 | **① `cargo fix --edition` ② `edition` 수정 ③ 테스트** — 순서대로 | (3) |
| 올리기 전에 규모를 본다 | **`-W rust-2024-compatibility`**(또는 `cargo fix` 의 diff) | (2) |
| 가드·락을 `if let` 으로 잡는 코드가 있다 | **올린 뒤 출력·테스트로 확인** — 린트가 침묵할 수 있다 | (3) |
| 2024 의 새 뜻을 쓰고 싶다(`expr` 이 `const {}` 를 받게 등) | fix 가 넣은 **`expr_2021` · `use<>` · `match` 를 사람이 되돌린다** | (3) |
| 예약어가 된 이름의 옛 API | **`r#이름`** | (4) |
| feature 뒤에 숨은 코드가 있다 | cargo 문서 — **`--all-features`** 로 fix(이 편은 던지지 않았다) | cargo 문서 |

## 핵심 문장

- ★★★ **같은 소스 16개 중 13개가 2021 과 2024 에서 갈렸다 — 그중 4개는 에러도 경고도 없이 출력만 달랐다.**
- ★★★ **`cargo fix --edition` 은 코드를 「옛 뜻 그대로」로 고칠 뿐 `edition` 을 올리지 않는다.**
- ★★★ **교정 뒤에도 뜻이 바뀐 칸이 남았다(`RefCell` 가드의 `if let`) — 그래서 마지막 단계가 테스트다.**
- ★★ **기본 경고는 거의 침묵한다 — `-W rust-2024-compatibility` 가 11개를 보였다.**
- ★★ **에디션은 크레이트 단위라 2021 과 2024 가 한 바이너리로 링크된다 — 예약어가 된 이름은 `r#` 로 부른다.**

## 관련 자료

- [`history/rust/02-에디션.md`](../../../../../../history/rust/02-에디션.md) — **에디션 제도의 역사**(2015 → 2024). 여기는 **「내 코드가 무엇을 고쳐야 하나」**.
- [**42번**](../42-refcell-cell-interior-mutability/) · [**32번**](../32-impl-trait-argument-return-position-and-2024-capture/) · [**37번**](../37-intoiterator-three-forms-iter-iter-mut-into-iter/) · [**20번**](../20-if-let-while-let-let-else-and-let-chains/) · [**07번**](../07-const-static-and-const-fn/) · [**11번**](../11-borrow-checker-rejections/) — 격자의 칸을 **깊게** 잰 편들(3-answer 9번의 표).
- [**46번 주제**](../46-crates-cargo-toml-features-and-workspaces/) — 에디션이 정하는 resolver 기본값.
- [**45번 주제**](../45-module-system-mod-use-pub-crate-and-file-layout/) (5) — 2015 대 2018 의 `use` 경로 · `pub(in path)`.
- Go 갈래 [`13-closures-variable-capture-and-loop-variable-change`](../../../go/syntax/13-closures-variable-capture-and-loop-variable-change/) — **`go.mod` 의 `go` 줄 · 파일 단위 `//go:build go1.21`** — Rust 는 크레이트 단위다.

## 용어 풀이

- **에디션** — 크레이트마다 고르는 언어 규칙의 판.
- **`cargo fix --edition`** — 다음 에디션에서 깨지거나 뜻이 바뀔 코드를 **현재 에디션에서 옛 뜻을 지키도록** 고치는 명령.
- **`rust_2024_compatibility`** — 2024 이사용 린트 묶음. 대부분 기본 꺼짐.
- **`expr_2021`** — 2021 의 `expr` 조각(= `const {}`·`_` 를 안 받는 옛 뜻).
- **`use<..>`** — 반환 `impl Trait` 이 품는 수명·타입을 **직접 적는** 표기(32번).
- **`!` 폴백** — 타입이 안 정해진 `!`(발산) 식이 떨어지는 기본 타입. 2021 `()` · 2024 `!`.
- **꼬리식 임시값** — 블록 마지막 식의 임시값. 2024 에서 **블록의 지역 변수보다 먼저** 버려진다.
- **원시 식별자 `r#`** — 예약어를 이름으로 쓰는 표기.

## 더 들어가면

- `gen` 블록 자체(제너레이터) — 2024 는 **낱말만 예약**했다. **던지지 않았다.**
- 예약 구문 `#"…"#`(guarded string) · rustfmt 의 스타일 에디션 · rustdoc 의 doctest 병합 — **던지지 않았다.**
- 꼬리식 임시값의 **`Drop` 순서** 변화(`tail_expr_drop_order` 린트) — 격자의 `tail_temp` 는 **빌림 쪽**만 봤다. **던지지 않았다.**
- `cargo fix --edition-idioms` — 새 에디션의 관용 표기로 바꾸기. **던지지 않았다.**
