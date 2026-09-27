# rust/syntax/47 — 에디션 2021 대 2024 — 같은 코드가 다르게 컴파일되는 자리 · `cargo fix --edition` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)`** · **`cargo 1.92.0 (344c4567c 2025-10-21)`** · `x86_64-unknown-linux-gnu` 에서
> 블록 배너의 명령으로 실제로 돌려 받은 것이다. cargo 는 `CARGO_NET_OFFLINE=true`(의존성 0개).\
> ★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
> ★★ `cargo fix` 가 찍는 절대 경로는 배너의 `sed "s|$PWD|.|g"` 로 `.` 로 바꿨다. `Finished … in 0.26s` 의 **시간**은 실행마다 바뀌는 칸이다(서머리 머리말의 표).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ `13 / 16` — 2021 에서 막히고 2024 에서 통과하는 행은 둘(`tail_temp` · `let_chain`)

**출력**

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

**왜 그런가**

- ★★★ **「갈린 행 13 / 16」** — 같았던 셋은 `array_into_iter` · `closure_capture`(둘 다 **2018 → 2021** 에서 바뀐 것이라 2021·2024 사이에서는 같다) · `missing_frag`(**두 판 모두 에러** — 아래).
- ★★★ **2021 에서 막히고 2024 에서 통과 — `tail_temp`(E0597 → `3`) · `let_chain`(「only allowed in Rust 2024」 → `big 3`)** 둘뿐이다. 갈린 13행을 모양별로 나누면 —

| 갈린 모양 | 행 | 수 |
|---|---|---|
| 2021 통과 → **2024 에러** | `gen_ident` · `extern_block` · `no_mangle` · `set_var` · `static_mut` · `rpit_capture` | 6 |
| **2021 에러** → 2024 통과 | `tail_temp` · `let_chain` | 2 |
| 둘 다 통과, **출력이 다름** | `boxed_slice`(`&i32` → `i32`) · `never_typename`(`()` → `!`) · `macro_expr`(`const block underscore` → `expr expr`) · `iflet_drop`(`drop` 과 `else` 의 순서) | 4 |
| 둘 다 통과, **경고만 다름** | `unsafe_op`(0 → 1) | 1 |
| **같음** | `array_into_iter` · `closure_capture` · `missing_frag` | 3 |

- ★★★ **「통과하는데 출력이 다른」 4행이 가장 위험하다** — 컴파일러가 아무 말도 안 하고 **뜻이 바뀐다.** `boxed_slice` 는 2021 에서 경고 1개(`boxed_slice_into_iter`)로 미리 알려 주지만, **`never_typename` · `macro_expr` · `iflet_drop` 은 2021 에서 경고 0개**였다.
- ★ `missing_frag` — 조각 지정자 없는 `$x` 는 2024 에디션 가이드 항목이지만 **이 판(1.92)에서는 2021 도 에러**였다. 에디션 가이드의 「2024 에서 바뀜」이 **지금 컴파일러에서도 두 판이 갈린다**는 뜻은 아니다.

### 2. ★★★ `else` · `drop g` · `3 1 4 5 1 5 free=false` — 경고는 **하나**(`boxed_slice_into_iter`)

**출력**

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

**왜 그런가**

- ★★ 표준 출력 — `guarded()` 가 `else` 를 찍은 **뒤에** 임시값 `Guard("g")` 가 버려졌고(2021 의 `if let` 임시값은 `else` 까지 산다), `first_even` 은 `else` 갈래에서 **`try_borrow_mut` 가 실패**했다(`free=false` — `c.borrow()` 의 가드가 아직 살아 있다).
- ★★★ **경고는 `boxed_slice_into_iter` 하나뿐이다.** `gen` 식별자 · `extern` 블록 · `#[no_mangle]` · `set_var` · `impl Trait` 포착 · `if let` 임시값 — 1번에서 2024 가 갈라놓은 모양이 이 파일에 더 있는데 **기본 경고로는 침묵**했다. 묶음을 직접 켜면 보인다 —

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

- ★★ **`-W rust-2024-compatibility` 로 켜자 경고가 늘었다** — 그 린트들은 이 묶음에 들어 있지만 **기본으로 꺼져 있다.** `cargo fix --edition` 이 이 묶음의 제안을 적용하는 명령이다(4번). ★ 이 목록에도 **`first_even` 의 `if let` 은 없다**(8번).

### 3. ★★ `error` 로 시작하는 줄 여섯 — 에러 5개 + 요약 1줄 · 1번의 2024 에러 행 수(6)와 **다르다**

**출력**

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

**왜 그런가**

- ★★★ **보고된 에러는 `gen` 셋 · `extern` · `no_mangle` 다섯뿐**이다 — 1번에서 2024 가 막은 `set_var`(E0133) · `rpit_capture`(E0502) 모양이 이 파일에도 있는데 **안 나왔다.** 앞의 다섯은 **구문·속성 단계**에서 막혀 빌드가 뒤 단계(타입 검사·빌림 검사)까지 **가지 않았다.**
- ★★ 그래서 **「에러 N개」는 고칠 것의 수가 아니라 「첫 관문에서 걸린 수」** 다. 판만 올리고 에러를 하나씩 지우면 **다음 관문의 에러가 새로 나온다** — `cargo fix --edition` 을 **판을 올리기 전에** 치는 이유다(4번).

### 4. ★★★ 11곳이 고쳐지고 · `edition` 은 **`"2021"` 그대로** · 올려서 돌리면 마지막 칸이 **`free=false` → `free=true`**

**출력**

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

**왜 그런가**

- ★★★ **diff 가 보여 준 치환** — `extern "C"` → `unsafe extern "C"` · `#[no_mangle]` → `#[unsafe(no_mangle)]` · `$e:expr` → **`$e:expr_2021`**(옛 뜻을 보존) · `unsafe fn` 몸통을 `unsafe { … }` 로 감쌈 · `impl Fn() -> usize` → **`+ use<>`**(옛 포착 규칙을 보존) · **`if let … else` → `match … { Some(n) => … _ => … }`**(옛 임시값 수명을 보존) · `gen` → **`r#gen`** · `b.into_iter()` → **`b.iter()`** · `set_var` 를 `unsafe { }` 로 감싸고 **`// TODO: Audit …` 주석**을 단다.
- ★★★ **`Cargo.toml` 은 `edition = "2021"` 그대로다** — `Migrating Cargo.toml from 2021 edition to 2024` 라고 찍지만 판 번호는 **안 바꾼다.** cargo 문서(`cargo fix`): 「`--edition` 은 매니페스트의 `edition` 을 **갱신하지 않는다** — 끝난 뒤 직접 고쳐야 한다」.
- ★★★ **올려서 돌리면 셋째 줄의 마지막 칸이 `free=false` → `free=true`** — 나머지는 한 글자도 같다. **`cargo fix` 는 `guarded()` 의 `if let` 은 `match` 로 바꿔 옛 순서(`else` → `drop g`)를 지켰는데, `first_even()` 의 `if let` 은 건드리지 않았다**(8번).
- ★ `Fixed src/main.rs (11 fixes)` — diff 의 치환 자리를 세면 11이다(`r#gen` 이 세 곳 — `let` · `vec!` · `twice!`).

### 5. ★★ `r#gen()` 은 통과(`7`) · 맨 `gen()` 은 「reserved keyword」 에러 — 두 에디션의 크레이트가 한 바이너리로 링크된다

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

- ★★★ **2021 라이브러리의 `pub fn gen` 은 그대로 있다** — 2024 사용자는 **원시 식별자 `r#gen`** 으로 부른다. `help:` 도 `r#` 를 권한다.
- ★★★ **에디션은 크레이트마다 따로다** — 2021 로 컴파일된 rlib 와 2024 로 컴파일된 바이너리가 **링크되어 실행됐다**(`7`). 에디션은 **소스를 읽는 규칙**이지 산출물의 형식이 아니다.

### 6. ★★ 2021 — 번호 없는 에러 「depends on never type fallback being `()`」(**거부 린트**) · 2024 — E0277 `!: Default`

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

- ★★★ **2021 은 컴파일이 되던 모양인데 이 판(1.92)에서는 막힌다** — 그 에러는 **린트** `dependency_on_unit_never_type_fallback` 이 **기본 거부(deny)** 로 켜져 있어서다(`note:` 가 그렇게 말하고, 「앞으로 **모든 에디션**에서 hard error 가 된다」고 덧붙인다). `help:` 는 `let _x: () = …` 로 타입을 적으라 한다.
- ★★ **2024 는 폴백이 `!` 라 `make::<!>()` 를 부르게 되어 `!: Default` 가 없다(E0277).** 1번의 `never_typename` 행(`()` → `!`)이 같은 규칙을 **통과하는 모양**으로 보인 것이다.
- ★ 그래서 「2021 은 되고 2024 만 막힌다」가 **이 판에서는 틀렸다** — 컴파일러가 옛 에디션에도 **미리 막는 린트**를 켜 둔 자리가 있다.

### 7. ★★★ 에디션은 **옛 코드를 깨는 변화**만 가른다 — 크레이트 단위라 섞여 링크된다

- ★★★ 에디션이 가르는 것은 **하위 호환을 깨는 것뿐**이다 — 새 키워드(`gen`) · 문법 뜻의 변화(`expr` 조각 · `if let` 임시값) · 기본값 전환(`!` 폴백 · `impl Trait` 포착). `impl Trait`·`?` 는 옛 코드를 깨지 않으므로 **일반 릴리스로 모든 에디션에** 풀렸다([`history/rust/02-에디션.md`](../../../../../../history/rust/02-에디션.md) 의 「새 기능 ≠ 에디션 전용」).
- ★★ **`let` 체인은 왜 2024 전용인가** — 같은 모양이 2021 에서 **다른 뜻**(`if let` 임시값 규칙과 얽힌 파싱)을 가질 수 있어 2024 에만 열었다([20번](../20-if-let-while-let-let-else-and-let-chains/)이 1.88 + 2024 를 쟀다). 1번 격자의 `let_chain` 행이 그 경계다.
- ★★ **크레이트 단위라서** 5번처럼 **2021 크레이트와 2024 크레이트가 한 바이너리로 링크**된다 — 생태계가 **한꺼번에 이사하지 않아도** 된다.

### 8. ★★ `first_even` 의 `if let`(`RefCell` 가드) — 린트가 침묵해 **동작이 바뀐 채** 넘어갔다 · 문서의 마지막 단계는 「테스트를 돌려라」

- ★★★ 4번 diff 에 **`first_even` 이 없다** — `if let Some(x) = c.borrow().iter().find(…) { … } else { … }` 의 가드는 2021 에서 `else` 까지 살고(`free=false`) 2024 에서는 `else` 전에 반납된다(`free=true`). **같은 규칙(`if let` 임시값)의 `guarded()` 는 `match` 로 고쳐 옛 동작을 지켰는데, 이쪽은 `if_let_rescope` 린트가 짚지 않아** 그대로 남았다.
- ★★ 에디션 가이드의 조건 — 「`if_let_rescope` 린트는 **수명 문제가 생기거나**, scrutinee 에서 **사용자 정의의 사소하지 않은 `Drop` 을 가진 임시값**이 생길 때 고침을 제안한다」. `Guard` 는 `impl Drop` 을 가진 사용자 타입이고, `first_even` 의 임시값은 std 의 `Ref` 다. **이 판에서 이 모양이 침묵했다**는 것까지가 관찰이고, 어느 조건에서 갈렸는지는 **확인하지 않았다.**
- ★★★ cargo 문서(`cargo fix`)의 절차 — ① `cargo fix --edition` → ② `Cargo.toml` 의 `edition` 을 **직접** 올린다 → ③ **테스트를 돌려 전부 여전히 동작하는지 확인한다.** 이 패키지에 `free=` 를 확인하는 테스트가 있었다면 ③에서 잡혔다.

### 9. ★★ `iflet_drop` · `rpit_capture` · `boxed_slice`(+ `array_into_iter`) · `let_chain` · `static_mut` · `tail_temp`

| 편 | 이 격자의 행 | 그 편이 더 잰 것 |
|---|---|---|
| [42번](../42-refcell-cell-interior-mutability/) (2) | `iflet_drop` | `RefCell` 가드로 `then`/`else` × 두 에디션 — **패닉 칸 3 / 4** |
| [32번](../32-impl-trait-argument-return-position-and-2024-capture/) (5) | `rpit_capture` | 네 칸 격자 · `use<..>` 로 할 수 있는 것 |
| [37번](../37-intoiterator-three-forms-iter-iter-mut-into-iter/) (2) | `boxed_slice` · `array_into_iter` | **2015 · 2018 · 2021 · 2024 네 판** — 배열은 2021, `Box<[T]>` 는 2024 |
| [20번](../20-if-let-while-let-let-else-and-let-chains/) | `let_chain` | 1.88 + 2024 · `if let` 임시값 |
| [07번](../07-const-static-and-const-fn/) 5번 | `static_mut` | 2021 경고 · 2024 에러의 전문 |
| [11번](../11-borrow-checker-rejections/) (11) · [12번](../12-lifetime-annotations-and-elision/) (8) | `tail_temp` 과 같은 방향(2021 거부 → 2024 통과) | `if let` + `RefCell` 한 파일 **2021 E0597 / 2024 통과** |

- ★ 이 편은 그 칸들을 **한 격자에 한 칸씩** 다시 놓았다 — 깊이는 그 편들이 정본이다.

### 10. ★ 같은 것 — 「옛 규칙을 고르는 스위치가 소스 밖(매니페스트)에 있다」 · 다른 것 — 단위와 섞임

- ★★ **같다** — Go 의 `go.mod` `go 1.21` 과 Rust 의 `edition = "2021"` 은 둘 다 **툴체인이 아니라 매니페스트가** 언어 규칙을 고른다. 컴파일러는 하나(Go 13번은 go1.27.1 하나로, 이 편은 rustc 1.92 하나로 두 규칙을 냈다).
- ★★ **다르다 — 단위.** Go 는 **파일 첫 줄 `//go:build go1.21`** 로 **파일 하나만** 내릴 수 있다([Go 13번](../../../go/syntax/13-closures-variable-capture-and-loop-variable-change/) (2)). Rust 의 에디션은 **크레이트 하나에 하나**다(rustc 의 `--edition` 은 크레이트 전체에 걸린다).
- ★ **섞임** — 둘 다 옛 판 코드와 새 판 코드가 **한 프로그램으로 링크**된다(Go 는 모듈마다, Rust 는 크레이트마다 — 5번).

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서·서머리의 **모든 블록** | `capture.sh` — 블록마다 명령을 배너에 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` 기본 규칙 넷(시간 칸이 걸린다) · **고칠 것 0** |
| ★★★ **에디션 격자** | `r47_grid.sh` — 소스 열여섯을 두 판으로 컴파일·실행(탭 구분 · 칸 수 검사 · 경고 수는 요약 줄 제외) | 16 × 2 | **`13 / 16`** |
| ★★★ **`cargo fix --edition` 절차** | `r47_fix_before` · `r47_nofix` · `r47_fix`(fix → diff → `edition` 확인 → 올림 → 실행) | 3 | 경고 1 · 에러 5 · **11 fixes · `edition` 그대로 · `free=false` → `free=true`** |
| 에디션 섞어 링크 | `r47_interop` · `r47_interop_plain` | 2 | `7` · reserved keyword |
| `!` 폴백 | `r47_never`(2021 · 2024) | 2 | 거부 린트 · E0277 |
| 판 연혁 | 머리말 `tools` 블록 — 로컬 `releases.md` | 1 | 2021 = 1.56.0 · 2024 = 1.85.0 |
| **안 던진 것** — 2015·2018 판 · `cargo fix --edition-idioms` · `--all-features` 로 feature 뒤의 코드까지 고치기 · rustfmt 의 스타일 에디션 · `gen` 블록 · 예약 구문 `#"…"#` · 꼬리식 임시값의 `Drop` 순서 | — | 0 | ★ 「안 던졌다」로 표시했다 |

**구현 의존 항목**(버전·환경이 바뀌면 **다시 찍어야 하는** 것).

| 항목 | 왜 |
|---|---|
| `missing_frag` 가 2021 에서도 에러 · `!` 폴백 린트가 2021 에서 거부 | ★ **컴파일러 판**(1.92)이 옛 에디션에도 켠 것 — 판이 오르면 더 늘 수 있다 |
| 어떤 린트가 기본 경고인가(`boxed_slice_into_iter` 만 켜져 있었다) | ★ rustc 린트 설정 |
| `cargo fix` 가 고친 자리 · `if_let_rescope` 가 침묵한 모양 | ★ **린트 구현** — 에디션 가이드는 조건을 서술할 뿐이다 |
| 진단 문구 | ★ rustc·cargo 판에 매인다 |

★ **다시 찍는 법** — `capture.sh <새 디렉토리>` 를 그대로 돌리고 `normalize-shaky.py <원본> <새 디렉토리>` 로 견준다.
