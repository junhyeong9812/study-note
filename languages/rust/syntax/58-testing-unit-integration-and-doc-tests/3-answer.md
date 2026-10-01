# rust/syntax/58 — 테스트: `#[test]` · 통합 테스트 · 문서 테스트 — 정답

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ `unit it doc ex(built)` · `unit` · `doc` · `it` — `9 / 12` · `1 / 4` · 막힌 셋은 전부 E0603

**출력**

````text
===== 소스: r58_grid.sh =====
# One package, four places a test (or example) can live. Every run uses --offline and a fresh copy.
set -u
export CARGO_TARGET_DIR="$PWD/target"

base() {   # base <dir> : lay out the package
  rm -rf "$1"; mkdir -p "$1/src" "$1/tests" "$1/examples"
  printf '[package]\nname = "r58"\nversion = "0.1.0"\nedition = "2021"\n' > "$1/Cargo.toml"
  cp r58_lib.rs "$1/src/lib.rs"
  cp r58_it.rs "$1/tests/it.rs"
  cp r58_ex.rs "$1/examples/ex.rs"
}

# which(<dir>, <cargo test args...>) -> the set of things that ran, e.g. "unit it doc ex(built)"
which() {
  local d=$1; shift
  rm -rf "$CARGO_TARGET_DIR/debug/examples"
  local out; out=$(cd "$d" && cargo test -q --offline "$@" -- --format pretty 2>/dev/null)
  local s=""
  grep -q '^test tests::unit_add \.\.\. ok' <<<"$out" && s="$s unit"
  grep -q '^test it_add \.\.\. ok' <<<"$out" && s="$s it"
  grep -q '^test src/lib.rs - add (line 3) \.\.\. ok' <<<"$out" && s="$s doc"
  [ -e "$CARGO_TARGET_DIR/debug/examples/ex" ] && s="$s ex(built)"
  echo "${s# }"
}

base pkg
echo "--- part 1: which runs pick up which place"
full=$(which pkg)
printf '%-22s %s\n' "cargo test" "$full"
diff=0 cells=0
for f in "--lib" "--doc" "--test it"; do
  got=$(which pkg $f)
  printf '%-22s %s\n' "cargo test $f" "$got"
  for place in unit it doc "ex(built)"; do
    cells=$((cells + 1))
    a=0; b=0
    [[ " $full " == *" $place "* ]] && a=1
    [[ " $got " == *" $place "* ]] && b=1
    [ $a != $b ] && diff=$((diff + 1))
  done
done
echo "cells where the filtered run differs from plain cargo test: $diff / $cells"

echo "--- part 2: can each place call the private fn secret()?"
reach=0
probe() {   # probe <place> <how to plant the call>
  base p2; eval "$2"
  local err code
  err=$(cd p2 && cargo test -q --offline 2>&1)
  code=$(grep -o 'error\[E[0-9]*\]' <<<"$err" | head -1)
  if [ -z "$code" ]; then reach=$((reach + 1)); code="compiles"; fi
  printf '%-10s %s\n' "$1" "$code"
}
probe unit 'sed -i "s/assert_eq!(add(1, 1), 2);/assert_eq!(secret(), 42);/" p2/src/lib.rs'
probe it   'echo "#[test] fn it_secret() { assert_eq!(r58::secret(), 42); }" >> p2/tests/it.rs'
probe doc  'sed -i "s/assert_eq!(r58::add(2, 3), 5);/assert_eq!(r58::secret(), 42);/" p2/src/lib.rs'
probe ex   'sed -i "s/r58::add(1, 1)/r58::secret()/" p2/examples/ex.rs'
echo "places that reach the private fn: $reach / 4"
===== 소스: r58_lib.rs =====
/// Adds two numbers.
///
/// ```
/// assert_eq!(r58::add(2, 3), 5);
/// ```
pub fn add(a: i32, b: i32) -> i32 {
    a + b
}

#[allow(dead_code)]
fn secret() -> i32 {
    42
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn unit_add() {
        assert_eq!(add(1, 1), 2);
    }
}
===== 소스: r58_it.rs =====
#[test]
fn it_add() {
    assert_eq!(r58::add(1, 1), 2);
}
===== 소스: r58_ex.rs =====
fn main() {
    println!("{}", r58::add(1, 1));
}
===== bash r58_grid.sh =====
--- part 1: which runs pick up which place
cargo test             unit it doc ex(built)
cargo test --lib       unit
cargo test --doc       doc
cargo test --test it   it
cells where the filtered run differs from plain cargo test: 9 / 12
--- part 2: can each place call the private fn secret()?
unit       compiles
it         error[E0603]
doc        error[E0603]
ex         error[E0603]
places that reach the private fn: 1 / 4
(exit 0)
````

**왜 그런가**

- ★★★ **필터는 자기 자리 하나만** 돌린다 — 12칸 중 같은 것은 셋, **갈린 칸 9**.
- ★★★ **`ex(built)` 는 필터 없는 `cargo test` 에만** — `examples/` 를 **빌드만** 하고 돌리지 않는다.
- ★★★ **비공개에 닿는 것은 단위 테스트 하나(`1 / 4`)** — 통합·문서·예제는 **크레이트 밖**이라 `secret()` 이 E0603(private function).

### 2. ★★★ `tests::unit_add ... ok` · `src/lib.rs - add (line 3) ... FAILED` · `101` · 「error: doctest failed, to rerun pass `--doc`」

**출력**

````text
===== 소스: r58_docfail_lib.rs =====
/// Adds two numbers.
///
/// ```
/// assert_eq!(r58d::add(2, 2), 5);
/// ```
pub fn add(a: i32, b: i32) -> i32 {
    a + b
}

#[cfg(test)]
mod tests {
    #[test]
    fn unit_add() {
        assert_eq!(super::add(1, 1), 2);
    }
}
===== 소스: r58_pkg.sh =====
# Lay out a one-crate package in ./pkg from the given files (an empty src/lib.rs if no crate root is given).
#   bash r58_pkg.sh <name> <file>=<path in package> ...
set -eu
name=$1; shift
rm -rf pkg; mkdir -p pkg
printf '[package]\nname = "%s"\nversion = "0.1.0"\nedition = "2021"\n' "$name" > pkg/Cargo.toml
for pair in "$@"; do
  mkdir -p "pkg/$(dirname "${pair#*=}")"
  cp "${pair%%=*}" "pkg/${pair#*=}"
done
[ -e pkg/src/lib.rs ] || [ -e pkg/src/main.rs ] || { mkdir -p pkg/src; : > pkg/src/lib.rs; }
find pkg -type f | sort
===== bash r58_pkg.sh r58d r58_docfail_lib.rs=src/lib.rs =====
pkg/Cargo.toml
pkg/src/lib.rs
(exit 0)
===== cd pkg && cargo test --offline 2>/dev/null | sed "s#$PWD#.#g" =====

running 1 test
test tests::unit_add ... ok

test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s


running 1 test
test src/lib.rs - add (line 3) ... FAILED

failures:

---- src/lib.rs - add (line 3) stdout ----
Test executable failed (exit status: 101).

stderr:

thread 'main' (1166766) panicked at src/lib.rs:5:1:
assertion `left == right` failed
  left: 4
 right: 5
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace



failures:
    src/lib.rs - add (line 3)

test result: FAILED. 0 passed; 1 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.08s

===== cd pkg && cargo test --offline 2>&1 >/dev/null | sed "s#$PWD#.#g" =====
   Compiling r58d v0.1.0 (./pkg)
    Finished `test` profile [unoptimized + debuginfo] target(s) in 0.16s
     Running unittests src/lib.rs (target/debug/deps/r58d-7a4eda2f4b279411)
   Doc-tests r58d
error: doctest failed, to rerun pass `--doc`
(exit 101)
````

**왜 그런가**

- ★★★ 문서 예제의 `assert_eq!(r58d::add(2, 2), 5)` 가 **컴파일되고 실행되어** 패닉했다(`left: 4` · `right: 5`). **틀린 설명서가 곧 실패한 테스트**다.
- ★★ 「Test executable failed (exit status: 101)」 — 문서 테스트는 예제마다 **따로 컴파일된 실행 파일**이다(스레드 이름도 `main`).

### 3. ★★★ `ignored` · `ok` · `compile fail ... ok` · `ok` · `compile fail ... FAILED` · `compile ... ok` — 「Test compiled successfully, but it's marked `compile_fail`.」

**출력**

````text
===== 소스: r58_docattrs_lib.rs =====
/// Example 1.
///
/// ```
/// assert_eq!(r58a::half(8), 4);
/// ```
///
/// Example 2.
///
/// ```no_run
/// loop { r58a::half(8); }
/// ```
///
/// Example 3.
///
/// ```ignore
/// this is not rust at all
/// ```
///
/// Example 4.
///
/// ```should_panic
/// r58a::half(7);
/// ```
///
/// Example 5.
///
/// ```compile_fail
/// let x: i32 = "text";
/// ```
///
/// Example 6.
///
/// ```compile_fail
/// let x: i32 = r58a::half(8);
/// ```
pub fn half(n: i32) -> i32 {
    assert!(n % 2 == 0, "odd input: {n}");
    n / 2
}
===== 소스: r58_pkg.sh =====
# Lay out a one-crate package in ./pkg from the given files (an empty src/lib.rs if no crate root is given).
#   bash r58_pkg.sh <name> <file>=<path in package> ...
set -eu
name=$1; shift
rm -rf pkg; mkdir -p pkg
printf '[package]\nname = "%s"\nversion = "0.1.0"\nedition = "2021"\n' "$name" > pkg/Cargo.toml
for pair in "$@"; do
  mkdir -p "pkg/$(dirname "${pair#*=}")"
  cp "${pair%%=*}" "pkg/${pair#*=}"
done
[ -e pkg/src/lib.rs ] || [ -e pkg/src/main.rs ] || { mkdir -p pkg/src; : > pkg/src/lib.rs; }
find pkg -type f | sort
===== bash r58_pkg.sh r58a r58_docattrs_lib.rs=src/lib.rs =====
pkg/Cargo.toml
pkg/src/lib.rs
(exit 0)
===== cd pkg && cargo test --offline --doc -- --test-threads=1 2>/dev/null | sed "s#$PWD#.#g" =====

running 6 tests
test src/lib.rs - half (line 15) ... ignored
test src/lib.rs - half (line 21) ... ok
test src/lib.rs - half (line 27) - compile fail ... ok
test src/lib.rs - half (line 3) ... ok
test src/lib.rs - half (line 33) - compile fail ... FAILED
test src/lib.rs - half (line 9) - compile ... ok

failures:

---- src/lib.rs - half (line 33) stdout ----
Test compiled successfully, but it's marked `compile_fail`.

failures:
    src/lib.rs - half (line 33)

test result: FAILED. 4 passed; 1 failed; 1 ignored; 0 measured; 0 filtered out; finished in 0.31s

===== cd pkg && cargo test --offline --doc -- --test-threads=1 2>&1 >/dev/null | sed "s#$PWD#.#g" =====
   Compiling r58a v0.1.0 (./pkg)
    Finished `test` profile [unoptimized + debuginfo] target(s) in 0.10s
   Doc-tests r58a
error: doctest failed, to rerun pass `--doc`
(exit 101)
````

**왜 그런가**

- ★★★ **33행 `compile_fail` 은 컴파일이 되어서 실패했다** — `let x: i32 = r58a::half(8);` 은 멀쩡하다. **27행**(`&str` 을 `i32` 에)은 정말 안 되어 통과.
- ★★ **9행 `no_run` → `- compile ... ok`**(컴파일만) · **15행 `ignore` → `ignored`**(Rust 도 아닌 글자인데 에러가 없다 — 아예 안 본다) · **21행 `should_panic` → `ok`**(`half(7)` 의 `assert!` 패닉) · **3행 → `ok`**.
- ★ 줄 순서는 **이름(`line 15` · `line 21` · … · `line 9`)의 문자열 순**이다 — `--test-threads=1` 에서의 관찰.

### 4. ★★ 통과 3 · 실패 1(`panic_with_other_text`) · 무시 1(`slow_one ... ignored, slow`) · `--ignored` 면 `slow_one ... ok` 하나

**출력**

```text
===== 소스: r58_attrs_test.rs =====
fn first(v: &[i32]) -> i32 {
    if v.is_empty() {
        panic!("no elements");
    }
    v[0]
}

#[test]
fn plain() {
    assert_eq!(first(&[3, 4]), 3);
}

#[test]
#[should_panic]
fn any_panic() {
    first(&[]);
}

#[test]
#[should_panic(expected = "no elements")]
fn panic_with_matching_text() {
    first(&[]);
}

#[test]
#[should_panic(expected = "empty slice")]
fn panic_with_other_text() {
    first(&[]);
}

#[test]
#[ignore = "slow"]
fn slow_one() {
    assert_eq!(first(&[9]), 9);
}
===== 소스: r58_pkg.sh =====
# Lay out a one-crate package in ./pkg from the given files (an empty src/lib.rs if no crate root is given).
#   bash r58_pkg.sh <name> <file>=<path in package> ...
set -eu
name=$1; shift
rm -rf pkg; mkdir -p pkg
printf '[package]\nname = "%s"\nversion = "0.1.0"\nedition = "2021"\n' "$name" > pkg/Cargo.toml
for pair in "$@"; do
  mkdir -p "pkg/$(dirname "${pair#*=}")"
  cp "${pair%%=*}" "pkg/${pair#*=}"
done
[ -e pkg/src/lib.rs ] || [ -e pkg/src/main.rs ] || { mkdir -p pkg/src; : > pkg/src/lib.rs; }
find pkg -type f | sort
===== bash r58_pkg.sh r58t r58_attrs_test.rs=tests/attrs.rs =====
pkg/Cargo.toml
pkg/src/lib.rs
pkg/tests/attrs.rs
(exit 0)
===== cd pkg && cargo test --offline --test attrs -- --test-threads=1 2>/dev/null | sed "s#$PWD#.#g" =====

running 5 tests
test any_panic - should panic ... ok
test panic_with_matching_text - should panic ... ok
test panic_with_other_text - should panic ... FAILED
test plain ... ok
test slow_one ... ignored, slow

failures:

---- panic_with_other_text stdout ----

thread 'panic_with_other_text' (1167280) panicked at tests/attrs.rs:3:9:
no elements
note: panic did not contain expected string
      panic message: "no elements"
 expected substring: "empty slice"

failures:
    panic_with_other_text

test result: FAILED. 3 passed; 1 failed; 1 ignored; 0 measured; 0 filtered out; finished in 0.00s

===== cd pkg && cargo test --offline --test attrs -- --test-threads=1 2>&1 >/dev/null | sed "s#$PWD#.#g" =====
   Compiling r58t v0.1.0 (./pkg)
    Finished `test` profile [unoptimized + debuginfo] target(s) in 0.21s
     Running tests/attrs.rs (target/debug/deps/attrs-ce1ef0947c3a282a)
error: test failed, to rerun pass `--test attrs`
(exit 101)
===== cd pkg && cargo test --offline --test attrs -- --ignored 2>/dev/null | sed "s#$PWD#.#g" =====

running 1 test
test slow_one ... ok

test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 4 filtered out; finished in 0.00s

===== cd pkg && cargo test --offline --test attrs -- --ignored 2>&1 >/dev/null | sed "s#$PWD#.#g" =====
    Finished `test` profile [unoptimized + debuginfo] target(s) in 0.01s
     Running tests/attrs.rs (target/debug/deps/attrs-ce1ef0947c3a282a)
(exit 0)
```

**왜 그런가**

- ★★★ 실패 메시지 — 「panic did not contain expected string」 · 「panic message: "no elements"」 · 「expected substring: "empty slice"」. **패닉은 났지만 문구가 틀렸다.**
- ★★ `--ignored` 는 **무시 표시가 붙은 것만** 돌린다 — `4 filtered out`.

### 5. ★★ 안 된다 — E0433 「use of unresolved module or unlinked crate `r58b`」 · `help:` 는 `cargo add r58b`

**출력**

```text
===== 소스: r58_bin_main.rs =====
pub fn double(n: i32) -> i32 {
    n * 2
}

fn main() {
    println!("{}", double(21));
}
===== 소스: r58_pkg.sh =====
# Lay out a one-crate package in ./pkg from the given files (an empty src/lib.rs if no crate root is given).
#   bash r58_pkg.sh <name> <file>=<path in package> ...
set -eu
name=$1; shift
rm -rf pkg; mkdir -p pkg
printf '[package]\nname = "%s"\nversion = "0.1.0"\nedition = "2021"\n' "$name" > pkg/Cargo.toml
for pair in "$@"; do
  mkdir -p "pkg/$(dirname "${pair#*=}")"
  cp "${pair%%=*}" "pkg/${pair#*=}"
done
[ -e pkg/src/lib.rs ] || [ -e pkg/src/main.rs ] || { mkdir -p pkg/src; : > pkg/src/lib.rs; }
find pkg -type f | sort
===== 소스: r58_bin_it.rs =====
#[test]
fn it_double() {
    assert_eq!(r58b::double(21), 42);
}
===== bash r58_pkg.sh r58b r58_bin_main.rs=src/main.rs r58_bin_it.rs=tests/it.rs =====
pkg/Cargo.toml
pkg/src/main.rs
pkg/tests/it.rs
(exit 0)
===== cd pkg && cargo test --offline -j 1 | sed "s#$PWD#.#g" =====
   Compiling r58b v0.1.0 (./pkg)
error[E0433]: failed to resolve: use of unresolved module or unlinked crate `r58b`
 --> tests/it.rs:3:16
  |
3 |     assert_eq!(r58b::double(21), 42);
  |                ^^^^ use of unresolved module or unlinked crate `r58b`
  |
  = help: if you wanted to use a crate named `r58b`, use `cargo add r58b` to add it to your `Cargo.toml`

For more information about this error, try `rustc --explain E0433`.
error: could not compile `r58b` (test "it") due to 1 previous error
(exit 101)
```

**왜 그런가**

- ★★★ **바이너리 크레이트는 다른 크레이트가 링크할 라이브러리를 만들지 않는다** — `pub fn double` 이어도 `tests/it.rs` 가 `r58b` 라는 크레이트를 못 찾는다. Book 11.3: 「Only library crates expose functions that other crates can use」.
- ★ `help:` 의 `cargo add r58b` 는 **자기 자신을 의존성으로 넣으라는** 엉뚱한 처방이다 — 문구가 원인을 가리키지 않는다(규칙 27).

### 6. ★★★ 기본은 둘 다 `ok` · `--test-threads=1` 이면 `a_waits_for_b` 가 약 2초 뒤 「timed out waiting for the flag」으로 `FAILED` · `101`

**출력**

```text
===== 소스: r58_par_test.rs =====
use std::sync::atomic::{AtomicBool, Ordering};
use std::time::{Duration, Instant};

static B_STARTED: AtomicBool = AtomicBool::new(false);

#[test]
fn a_waits_for_b() {
    eprintln!("[a] start on thread {:?}", std::thread::current().name());
    let t = Instant::now();
    while !B_STARTED.load(Ordering::SeqCst) {
        assert!(t.elapsed() < Duration::from_secs(2), "timed out waiting for the flag");
        std::thread::sleep(Duration::from_millis(10));
    }
    eprintln!("[a] saw b");
}

#[test]
fn b_sets_flag() {
    eprintln!("[b] start on thread {:?}", std::thread::current().name());
    B_STARTED.store(true, Ordering::SeqCst);
}
===== 소스: r58_pkg.sh =====
# Lay out a one-crate package in ./pkg from the given files (an empty src/lib.rs if no crate root is given).
#   bash r58_pkg.sh <name> <file>=<path in package> ...
set -eu
name=$1; shift
rm -rf pkg; mkdir -p pkg
printf '[package]\nname = "%s"\nversion = "0.1.0"\nedition = "2021"\n' "$name" > pkg/Cargo.toml
for pair in "$@"; do
  mkdir -p "pkg/$(dirname "${pair#*=}")"
  cp "${pair%%=*}" "pkg/${pair#*=}"
done
[ -e pkg/src/lib.rs ] || [ -e pkg/src/main.rs ] || { mkdir -p pkg/src; : > pkg/src/lib.rs; }
find pkg -type f | sort
===== bash r58_pkg.sh r58p r58_par_test.rs=tests/par.rs =====
pkg/Cargo.toml
pkg/src/lib.rs
pkg/tests/par.rs
(exit 0)
===== cd pkg && cargo test --offline --test par | grep -E '^test ' | sort =====
test a_waits_for_b ... ok
test b_sets_flag ... ok
test result: ok. 2 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
(exit 0)
===== cd pkg && cargo test --offline --test par -- --test-threads=1 2>/dev/null | sed "s#$PWD#.#g" =====

running 2 tests
test a_waits_for_b ... FAILED
test b_sets_flag ... ok

failures:

---- a_waits_for_b stdout ----
[a] start on thread Some("a_waits_for_b")

thread 'a_waits_for_b' (1168027) panicked at tests/par.rs:11:9:
timed out waiting for the flag
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace


failures:
    a_waits_for_b

test result: FAILED. 1 passed; 1 failed; 0 ignored; 0 measured; 0 filtered out; finished in 2.00s

===== cd pkg && cargo test --offline --test par -- --test-threads=1 2>&1 >/dev/null | sed "s#$PWD#.#g" =====
    Finished `test` profile [unoptimized + debuginfo] target(s) in 0.00s
     Running tests/par.rs (target/debug/deps/par-ef0eae4f66e52e0e)
error: test failed, to rerun pass `--test par`
(exit 101)
```

**왜 그런가**

- ★★★ **기본 병렬** — 두 테스트가 동시에 돌아 `a` 가 `b` 의 깃발을 봤다. **`--test-threads=1`** — 이름순으로 `a` 가 **혼자 먼저** 돌아 깃발을 못 봤다(`finished in 2.01s` 근처 — 시간은 흔들리는 칸).
- ★★ **같은 코드가 실행 방식만으로 통과/실패가 갈렸다** — 테스트끼리 **전역 상태(`static B_STARTED`)** 를 공유했기 때문이다.

### 7. ★★ 셋 다 내 크레이트 밖의 별도 크레이트 — rustdoc 은 `extern crate <mycrate>;` 를 끼워 넣는다

- ★★★ **통합 테스트** — `tests/` 의 파일 하나가 크레이트 하나. **예제** — `examples/` 의 파일 하나가 바이너리 크레이트 하나. **문서 테스트** — rustdoc: 「If the example does not contain `extern crate`, … then `extern crate <mycrate>;` is inserted」. 셋 다 **밖에서 쓰는 쪽**이라 비공개가 안 보인다(E0603).
- ★★ 단위 테스트만 **같은 크레이트 안의 모듈**(`use super::*`)이라 비공개에 닿는다.

### 8. ★★ `compile_fail` 은 「컴파일이 실패해야 통과」 — 「이렇게 쓰면 안 된다」를 문서로 약속할 때

- ★★★ rustdoc: 「`compile_fail` tells rustdoc that the compilation should fail」. 33행은 **컴파일이 되어서** 약속을 어겼다.
- ★★ **쓰는 자리** — API 가 **막아 주는 사용법**을 문서로 보이고, 그 막음이 풀리면(누가 경계를 느슨하게 고치면) **테스트가 알린다.** ★ rustdoc 의 정의(「the compilation should fail」)는 **왜** 실패하는지를 묻지 않는다 — 오타로 실패해도 통과할 것이다(★ 그 판은 던지지 않았다).

### 9. ★★ 엉뚱한 곳의 패닉도 통과시킨다 · `expected` 는 부분 문자열 비교

- ★★★ `any_panic` 은 **어디서 무슨 패닉이 나든** 통과다 — 준비 코드의 버그로 패닉해도 초록불이다.
- ★★ `expected = "no elements"` 는 통과, `expected = "empty slice"` 는 실패 — 메시지 「no elements」가 **그 문자열을 포함하나**만 본다(「expected substring」).

### 10. ★★ 넷 — `src/lib.rs` 단위 · `src/main.rs` 단위 · `tests/it.rs` · 문서 테스트

**출력**

```text
===== 소스: r58_split_lib.rs =====
pub fn double(n: i32) -> i32 {
    n * 2
}
===== 소스: r58_pkg.sh =====
# Lay out a one-crate package in ./pkg from the given files (an empty src/lib.rs if no crate root is given).
#   bash r58_pkg.sh <name> <file>=<path in package> ...
set -eu
name=$1; shift
rm -rf pkg; mkdir -p pkg
printf '[package]\nname = "%s"\nversion = "0.1.0"\nedition = "2021"\n' "$name" > pkg/Cargo.toml
for pair in "$@"; do
  mkdir -p "pkg/$(dirname "${pair#*=}")"
  cp "${pair%%=*}" "pkg/${pair#*=}"
done
[ -e pkg/src/lib.rs ] || [ -e pkg/src/main.rs ] || { mkdir -p pkg/src; : > pkg/src/lib.rs; }
find pkg -type f | sort
===== 소스: r58_split_main.rs =====
fn main() {
    println!("{}", r58b::double(21));
}
===== 소스: r58_bin_it.rs =====
#[test]
fn it_double() {
    assert_eq!(r58b::double(21), 42);
}
===== bash r58_pkg.sh r58b r58_split_lib.rs=src/lib.rs r58_split_main.rs=src/main.rs r58_bin_it.rs=tests/it.rs =====
pkg/Cargo.toml
pkg/src/lib.rs
pkg/src/main.rs
pkg/tests/it.rs
(exit 0)
===== cd pkg && cargo test --offline -j 1 2>/dev/null | sed "s#$PWD#.#g" =====

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s


running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s


running 1 test
test it_double ... ok

test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s


running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

===== cd pkg && cargo test --offline -j 1 2>&1 >/dev/null | sed "s#$PWD#.#g" =====
   Compiling r58b v0.1.0 (./pkg)
    Finished `test` profile [unoptimized + debuginfo] target(s) in 0.50s
     Running unittests src/lib.rs (target/debug/deps/r58b-4c550ea57c278918)
     Running unittests src/main.rs (target/debug/deps/r58b-18efd22b364272dc)
     Running tests/it.rs (target/debug/deps/it-a5584e4ba551db7e)
   Doc-tests r58b
(exit 0)
===== cd pkg && cargo run -q --offline =====
42
(exit 0)
```

**왜 그런가**

- ★★★ 한 패키지에 **크레이트가 둘**(라이브러리 `r58b` · 바이너리 `r58b`)이고, `#[cfg(test)]` 단위 테스트는 **크레이트마다** 실행 파일이 하나씩 생긴다 → `Running unittests src/lib.rs` · `Running unittests src/main.rs`. 여기에 `tests/it.rs` 하나와 `Doc-tests r58b` 하나.
- ★★ `it_double ... ok` — 통합 테스트는 **라이브러리 쪽**을 부른다. `main.rs` 는 `r58b::double` 을 부르는 껍질이다(`cargo run -q` → `42`).

### 11. ★★ 「by default they run in parallel」 대 「run in parallel with (and only with) other parallel tests」 — Rust 는 끄고, Go 는 켠다 · 이 문서는 Go 를 안 쟀다

- ★★ Book 11.2 — 「When you run multiple tests, **by default they run in parallel using threads**」. Go 49 의 `go doc` — `Parallel` 은 「this test is to be run in parallel with (**and only with**) other parallel tests」.
- ★★ `t.Parallel()` 없는 Go 테스트는 병렬 무리에 끼지 않으므로 6번의 **`--test-threads=1` 쪽**(차례대로)에 가까울 것이다 — ★ **추측이다. 이 문서는 Go 를 돌리지 않았다.**

### 12. ★ 병렬 판의 `ok` 두 줄 순서가 흔들린다(30판 중 1판) — 근거는 순서가 아니라 통과/실패

- ★★ `test b_sets_flag ... ok` 가 먼저인 판이 29, `a_waits_for_b` 가 먼저인 판이 1 이었다 — **완료 순서는 약속이 없다.** 그래서 줄을 **정렬해** 실어 블록을 결정적으로 만들었다(규칙 11).
- ★★★ **결론의 근거는 「서로 기다리는 테스트가 끝나나」** — 병렬이면 통과, 차례면 실패. **순서 대신 결과로 물었다**(제5의 상태).

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서·서머리의 **모든 블록** | `capture.sh` — 블록마다 명령을 배너에 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` 기본 규칙 넷(시간 · 스레드 id) · **고칠 것 0** |
| ★★★ **배치 격자** | `r58_grid.sh` — `cargo test` × 4 명령 · 비공개 탐침 4 | 8 | **`9 / 12`** · **`1 / 4`** |
| ★★★ **문서 테스트 실패** | `r58_docfail` | 1 | `FAILED` · `101` |
| 예제 표시 | `r58_docattrs` | 1(6예제) | ok 4 · FAILED 1 · ignored 1 |
| `should_panic`·`ignore` | `r58_attrs` × (기본 · `--ignored`) | 2 | 3·1·1 · `1 passed` |
| 바이너리 크레이트 | `r58_bin` · `r58_split` | 2 | **E0433** · 통과(실행 파일 4) |
| ★★ **병렬** | `r58_par` × (기본 · `--test-threads=1`) + 예행 30판 | 2 + 30 | 통과 · **실패** · 순서 29 대 1 |
| **안 던진 것** — 앞 단계 실패 시 문서 단계 · `tests/common` · `--no-fail-fast` · Go 판 · 실행 시간 | — | 0 | ★ 「안 던졌다」로 표시했다 |

**구현 의존 항목**(버전·환경이 바뀌면 **다시 찍어야 하는** 것).

| 항목 | 왜 |
|---|---|
| `--test-threads=1` 에서 이름순 · 테스트마다 자기 이름의 스레드 | ★ libtest 구현 — Book 은 순서를 약속하지 않는다 |
| `cargo test` 가 `examples/` 를 빌드하는 것 · 실행 파일 순서 | ★ cargo 의 동작 |
| 문서 테스트 패닉의 줄 번호 `5:1` | ★ rustdoc 이 예제를 감싸는 방식 |
| E0433 의 `help:` 문구 | ★ rustc 진단 |
| `target/debug/deps/…-<해시>` | ★ cargo 의 메타데이터 해시 — 판·설정이 바뀌면 바뀐다 |

★ **다시 찍는 법** — `capture.sh <새 디렉토리>` 를 그대로 돌리고 `normalize-shaky.py <원본> <새 디렉토리>` 로 견준다.

## 실행 환경

이 파일의 모든 출력·에러는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `cargo 1.92.0 (344c4567c 2025-10-21)` · `x86_64-unknown-linux-gnu`** 에서 **`cargo test --offline`** 으로 실제로 돌려 받은 것이다.\
★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
★★ 블록 첫 줄 `===== 소스: <파일> =====` 아래가 **돌린 소스 전문**이다(패키지를 만드는 `r58_pkg.sh` 도 배너째 함께 실렸다). **진단의 줄 번호는 패키지 안 경로 기준**이다(`src/lib.rs` · `tests/it.rs`).\
★ `finished in …s` 의 시간과 패닉 줄의 `thread '…' (NNN)` 은 **실행마다 바뀌는 칸**이다(서머리 맨 위 부분의 표).
