# rust/syntax/47 — 에디션 2021 대 2024 — 같은 코드가 다르게 컴파일되는 자리 · `cargo fix --edition` — 질문

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 열여섯 소스 × 두 에디션 (예측)

```bash
# r47_grid.sh
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
```

- 열여섯 행의 두 칸(`runs: …` 면 출력, 아니면 첫 `error` 줄, 그리고 경고 수)을 채워라. 마지막 줄의 `N / 16` 은? 「2021 에서 막히고 2024 에서 통과」하는 행은 어느 것들인가?

### 2. ★★★ 2021 패키지 하나 (예측)

```rust
// r47_fix_main.rs
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
```

```toml
# r47_fix.Cargo.toml
[package]
name = "fixdemo"
version = "0.1.0"
edition = "2021"
```

- `cargo run -q` 의 표준 출력 세 줄과, 표준 오류에 경고가 **몇 개** 나오나? 1번 격자에 같은 모양이 여럿 있는데 왜 경고는 그 수뿐인가?

### 3. ★★ 고치지 않고 판만 올리면 (예측)

- 2번 패키지에서 **소스는 그대로 두고** `Cargo.toml` 의 `edition` 만 `"2024"` 로 바꿔 `cargo build -q` 하면, `error` 로 시작하는 줄은 몇 개이고 무엇인가? 1번 격자에서 2024 가 막은 행 수와 같은가?

### 4. ★★★ `cargo fix --edition` 을 먼저 치면 (예측)

- 2번 패키지(판 `2021` 그대로)에서 `cargo fix --edition --allow-no-vcs` 를 치면 소스의 **어느 자리**가 어떻게 바뀌나? 그 뒤 `Cargo.toml` 의 `edition` 은 무엇인가? 직접 `"2024"` 로 올리고 `cargo run -q` 하면 표준 출력이 2번과 **한 글자도 같은가**?

### 5. ★★ 2021 크레이트의 `gen` 함수를 2024 크레이트에서 (예측)

```rust
// r47_lib2021.rs
pub fn gen() -> i32 {
    7
}
```

```rust
// r47_user2024.rs
fn main() {
    println!("{}", r47_lib2021::r#gen());
}
```

```rust
// r47_user2024_plain.rs
fn main() {
    println!("{}", r47_lib2021::gen());
}
```

- `r47_lib2021.rs` 를 2021 라이브러리로 만들고 두 사용자 소스를 각각 `--edition 2024` 로 붙이면? 에디션이 다른 두 크레이트가 한 바이너리에 링크되나?

### 6. ★★ 한쪽 갈래가 `panic!` 인 `if` — 두 에디션 (예측)

```rust
// r47_never.rs
fn make<T: Default>() -> T {
    T::default()
}

fn main() {
    let flag = false;
    let _x = if flag { panic!() } else { make() };
    println!("done");
}
```

- `--edition 2021` 과 `--edition 2024` 로 각각 던지면 컴파일되나? 막힌다면 무엇이 막나(번호가 없다면 무엇이라 적히나) — 그것은 **에러인가 린트인가**?

### 7. ★★★ 에디션은 무엇을 바꾸고 무엇을 안 바꾸나 (왜)

- 새 기능(예 — `let` 체인)은 왜 **새 에디션에만** 열리고, `impl Trait`·`?` 같은 것은 왜 **모든 에디션**에 풀렸나? 에디션이 **크레이트 단위**라는 것은 5번과 어떻게 이어지나?

### 8. ★★ `cargo fix` 뒤에 남는 일 (경계)

- 4번의 diff 를 1번 격자의 행들과 견주면, 이 패키지에 있던 에디션 차이 중 diff 에 **없는** 것이 있나? 있다면 판을 올린 뒤 무엇이 달라졌나? cargo 문서가 `cargo fix --edition` 뒤에 하라는 단계는 무엇인가?

### 9. ★★ 이미 잰 칸들 (연결)

- 1번 격자의 행 중 다른 편이 **깊게** 잰 것이 있다 — [42번](../42-refcell-cell-interior-mutability/) · [32번](../32-impl-trait-argument-return-position-and-2024-capture/) · [37번](../37-intoiterator-three-forms-iter-iter-mut-into-iter/) · [20번](../20-if-let-while-let-let-else-and-let-chains/) · [07번](../07-const-static-and-const-fn/) · [11번](../11-borrow-checker-rejections/) 은 각각 어느 행인가?

### 10. ★ `go.mod` 의 `go` 줄 (연결)

- Go 는 루프 변수의 뜻을 `go.mod` 의 `go` 줄이 정한다([Go 13번](../../../go/syntax/13-closures-variable-capture-and-loop-variable-change/)). Rust 의 `edition` 과 무엇이 같고 무엇이 다른가 — 단위(모듈 · 크레이트)와 **옛 판 코드와 섞여 링크되는가**를 기준으로.

## 실행 환경

★ 던지는 법 — 격자는 `bash <파일>.sh`, 단일 소스는 `rustc --edition 2021|2024 <파일>.rs`. `cargo fix` 문항은 소스 둘(`main.rs` · `Cargo.toml`)을 **`src/main.rs` · `Cargo.toml` 로 복사한 작은 패키지**에서 친다. cargo 는 `CARGO_NET_OFFLINE=true`(의존성 없음).
★★★ **소스를 보면 먼저 물어라** — 「**이 파일은 몇 년 판 말로 읽히나**」. 에디션은 소스 바깥(`Cargo.toml`·`--edition`)에 적힌다.
★ **문항 10개 중 코드가 붙은 예측형은 4개**다. 소스 펜스는 캡처가 실파일에서 찍었다(`check-source-fences.py` 대조).

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
