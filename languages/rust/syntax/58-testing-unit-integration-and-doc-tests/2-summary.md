# rust/syntax/58 — 테스트: `#[test]` · 통합 테스트 · 문서 테스트 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [The Book — 11.2 Running Tests](https://doc.rust-lang.org/book/ch11-02-running-tests.html)(「by default they run in parallel using threads」 · `--test-threads`) ·
> [The Book — 11.3 Test Organization](https://doc.rust-lang.org/book/ch11-03-test-organization.html)(단위 테스트는 비공개를 시험할 수 있다 · 「If our project is a binary crate that only contains a `src/main.rs` file … we can't create integration tests in the `tests` directory and bring functions defined in the `src/main.rs` file into scope」) ·
> [rustdoc — Documentation tests](https://doc.rust-lang.org/rustdoc/write-documentation/documentation-tests.html)(`ignore` · `should_panic` · `no_run` · `compile_fail` · 「`extern crate <mycrate>;` is inserted」).
> ★ 전부 **이 머신의 `rust-docs`(1.92.0) 로컬 사본**을 열어 읽었다.
> **실행 검증** — `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `cargo 1.92.0 (344c4567c 2025-10-21)` · `x86_64-unknown-linux-gnu` 에서 **`cargo test --offline`**(외부 의존성 0 — 네트워크를 안 쓴다).\
> ★★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다. 패키지는 스크립트(`r58_pkg.sh`)가 **파일을 제자리에 복사해** 매번 새로 만든다.\
> ★ **테스트 실행 시간은 재지 않았다** — `finished in 0.00s` 같은 숫자는 흔들리는 칸이다(아래 표).
> 이 본문은 Claude 작성이다(원고 없음).

★★★ **본체 창 — ① 배치 격자다** — 「테스트를 **어디에** 두었나(단위 · 통합 · 문서 · `examples/`)」 × 「**어떤 명령이** 그것을 돌리나 · **비공개 함수에** 닿나」. 스크립트가 마지막 두 줄로 **「필터가 전체와 갈린 칸 N / M」** 과 **「비공개에 닿은 자리 N / 4」** 를 센다.

```bash
# r58_pkg.sh
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
```

- ★ 이 편의 모든 cargo 블록은 이 스크립트로 `pkg/` 를 만든 뒤 `cd pkg && cargo …` 를 던진다. 표준 오류의 **절대 경로는 캡처가 `sed` 로 `.` 로 바꿨다**(배너에 그 `sed` 가 적혀 있다 — 규칙 33).

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| ★★ **흔들린다(정규화)** | `finished in 0.00s` · `target(s) in 0.15s` 의 **시간** | 기본 규칙이 `<time>` 으로 바꾼다 |
| ★★ **흔들린다(정규화)** | 패닉 첫 줄의 **스레드 id** `thread 'main' (NNN)` | 기본 규칙 |
| ★★★ **흔들린다 — 블록을 결정적으로 바꿨다** | ★ **병렬 실행에서 `test … ok` 줄의 순서** | 완료 순서라 약속이 없다 — 예행 **30판 중 1판**이 뒤집혔다. 그래서 그 블록만 `grep '^test ' \| sort` 로 **정렬해** 실었다(규칙 11) |
| 안 흔들린다 | ★★★ **격자의 두 수** · 각 칸의 결과 · 에러 번호 · 종료 코드 `101` | 같은 판에서 고정이다 |
| 안 흔들린다 | `--test-threads=1` 판의 **테스트 순서** | 이름순으로 돌았다 — ★ **관찰**이다(Book 은 순서를 약속하지 않는다) |
| 안 흔들린다 | `target/debug/deps/r58d-7a4eda2f4b279411` 같은 **해시** | 이 판에서 **다른 디렉토리에서 돌려도 같았다**(예행) — cargo 의 메타데이터 해시다 |

★ 정규화 규칙은 **기본 넷**만 쓴다(시간 · 스레드 id 가 걸린다).

## 한눈에 — 쉽게 말하면

**테스트는 「어디서 검사하느냐」에 따라 보이는 것이 다르다.**
**단위 테스트(`#[cfg(test)] mod tests`)는 공장 안의 검사원**이다 — 같은 건물(같은 크레이트)이라 **비공개 부품까지** 만져 본다.
**통합 테스트(`tests/`)는 매장에서 물건을 산 손님**이다 — **공개된 것(`pub`)만** 쓸 수 있다. 문서 예제(문서 테스트)도 손님이다 — rustdoc 이 **예제마다 따로 프로그램을 만들어** 돌린다.
**`examples/`** 는 진열용 견본이다 — `cargo test` 가 **조립은 해 보지만(빌드) 켜 보지는 않는다(실행 안 함).**
그리고 **설명서(문서 주석)에 적은 예제가 틀리면 검사가 실패한다** — 설명서가 코드와 따로 놀 수 없게 된다.

| 비유 | 실체 |
|---|---|
| 「**공장 안 검사원**」 | ★★ **단위 테스트** — `src/` 안 · 비공개에 닿는다 · `--lib` 로 골라 돈다((1)) |
| 「**매장의 손님**」 | ★★★ **통합 테스트 `tests/*.rs`** — 크레이트를 **밖에서** 쓴다 · 비공개는 E0603((1)) |
| 「**설명서 속 예제**」 | ★★★ **문서 테스트** — 예제가 틀리면 **`cargo test` 가 실패한다**((2)) |
| 「**진열용 견본**」 | ★★ **`examples/`** — `cargo test` 가 **빌드만** 한다((1)) |
| 「**견본만 있는 가게**」 | ★★ **바이너리 크레이트(`main.rs` 만)** — 통합 테스트가 부를 수 없다 → `lib.rs` 로 나눈다((5)) |
| 「**검사원 여럿이 동시에**」 | ★★ **테스트는 기본 병렬** — `--test-threads=1` 이면 차례로((6)) |

```text
   pkg/
   ├── Cargo.toml
   ├── src/lib.rs          ← #[cfg(test)] mod tests { … }     단위 테스트    (같은 크레이트 — 비공개 OK)
   │                       ← /// ``` … ```                     문서 테스트    (예제마다 별도 프로그램 — 공개만)
   ├── tests/it.rs         ← #[test] fn …                      통합 테스트    (별도 크레이트 — 공개만)
   └── examples/ex.rs      ← fn main()                         예제          (cargo test 가 빌드만 — 공개만)

   cargo test          → 네 자리를 다 다룬다   (examples 는 빌드만)
   cargo test --lib    → 단위만     --doc → 문서만     --test it → tests/it.rs 만
```

> **단위 테스트(unit test)** — 같은 소스 파일 안의 `#[cfg(test)]` 모듈에 둔 `#[test]` 함수. 테스트 빌드에서만 컴파일된다.\
> 예: (1) `r58_lib.rs` 의 `tests::unit_add`.

> **통합 테스트(integration test)** — `tests/` 디렉토리의 파일 하나하나. **파일마다 별도 크레이트**로 컴파일되어 내 크레이트를 `use` 해서 쓴다.\
> 예: (1) `tests/it.rs` 의 `it_add`.

> **문서 테스트(doctest)** — 문서 주석(`///`) 안의 코드 블록. rustdoc 이 예제마다 `extern crate <내 크레이트>;` 를 붙인 **별도 프로그램**으로 컴파일해 돌린다.\
> 예: (2)의 `src/lib.rs - add (line 3)`.

## 이 주제가 답하려는 질문

1. ★★★ **테스트를 어디에 두나** — 네 자리가 각각 **비공개에 닿나**, **어떤 명령에 돌려지나**((1)).
2. ★★★ **문서 예제가 깨지면 빌드가 깨지나** — `cargo test` 는 무엇을 출력하고 몇으로 끝나나((2)) · `no_run`·`ignore`·`should_panic`·`compile_fail` 은 무엇을 바꾸나((3)).
3. ★★ **`main.rs` 만 있는 크레이트는 왜 통합 테스트가 안 되나**((5)) · **테스트는 동시에 도나**((6)).

★ **선행** — [**45번 주제**](../45-module-system-mod-use-pub-crate-and-file-layout/)(모듈 시스템 — `mod`·`use`·`pub(crate)`·파일 배치)가 이 주제의 뿌리다. 가시성 규칙의 정본은 그쪽이고, 이 편은 「`pub` 이면 크레이트 밖에서 보인다 · 아니면 E0603」까지만 쓴다.
[**01번 주제**](../01-cargo-crates-and-modules/) — 바이너리 크레이트와 라이브러리 크레이트의 파일 배치 · `cargo` 가 `rustc` 에게 무엇을 건네나. [**23번 주제**](../23-panic-vs-result/) — 패닉. (4)의 `should_panic` 이 그 위에 선다.

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ① 배치 격자다

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ① ★★★ **배치 격자**(스크립트가 칸을 세어 마지막 줄로) | 네 자리 × (전체 · `--lib` · `--doc` · `--test`) · 비공개 접근 | ★ **본체**((1)) |
| ② ★★★ **`cargo test` 출력 전문 + 종료 코드** | 문서 테스트가 깨졌을 때 **무엇이 실패로 보고되나** | 쓴다((2)·(3)·(4)) |
| ③ ★★ **컴파일러 진단** | 비공개(E0603) · 바이너리 크레이트(E0433) | 쓴다((1)·(5)) |
| ④ ★★ **서로 기다리는 두 테스트** | 기본이 **정말 병렬인가** | 쓴다((6)) |
| 테스트 실행 시간 | — | ★ **안 쟀다** — 흔들리는 칸으로만 둔다 |
| 다른 언어의 병렬 기본값 | — | ★ **이미 잰 것** — [Go 49번](../../../go/syntax/49-testing-table-driven-t-run-cleanup-and-parallel/)((6)) |

★★ **제5의 상태 — 「같은 질문을 다른 창으로」.** 「테스트가 병렬로 도나」를 **출력 순서**로 물으면 흔들린다(30판 중 1판이 뒤집혔다 — 순서는 우연이다).
그래서 질문을 **「서로를 기다리는 두 테스트가 끝나나」** 로 바꿨다((6)) — 병렬이면 통과, 차례면 한쪽이 시간 초과로 **실패한다.** 결과가 **통과/실패**라 판마다 같다.
★ 바꾼 창이 못 보는 것 — **몇 개가 동시에** 도는지(스레드 수)는 안 보인다. 「적어도 둘은 겹친다」까지만 말한다.

### (1) ★★★ 네 자리 — 무엇이 돌리고, 무엇에 닿나

**언제 쓰나** — 테스트 파일을 새로 만들 때마다. 자리가 곧 **보이는 범위**다.

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

- ★★★ **「필터가 전체와 갈린 칸 9 / 12」** — `--lib`·`--doc`·`--test it` 는 **각각 자기 자리 하나만** 돌렸다. 세 필터 × 네 자리 = 12칸 중 **자기 자리 셋만 같고 나머지 아홉이 갈렸다.**
- ★★★ **`ex(built)` 는 필터 없는 `cargo test` 에만** — `cargo test` 는 `examples/` 를 **빌드한다**(그래서 예제가 컴파일이 안 되면 `cargo test` 가 깨진다 — part 2 의 `ex` 행). **실행은 하지 않는다** — 예제의 `main` 이 찍었을 `2` 가 출력 어디에도 없다.
- ★★★ **「비공개에 닿은 자리 1 / 4」** — 단위 테스트만 `secret()` 를 불렀다. **통합 · 문서 · 예제는 전부 E0603**(private function) — 셋 다 **내 크레이트 밖의 별도 크레이트**이기 때문이다. rustdoc 문서: 예제에 `extern crate <mycrate>;` 가 **끼워 넣어진다.**
- ★★ Book 11.3 — 「Unit tests … **can test private interfaces**」. 비공개를 시험하고 싶으면 **단위 테스트 자리**다.

### (2) ★★★ 문서 예제가 깨지면 — `cargo test` 가 실패한다

**언제 쓰나** — 문서 주석에 예제를 적을 때마다. **예제가 곧 테스트**다.

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

- ★★★ **단위 테스트는 `ok` 인데 문서 테스트가 `FAILED` → 종료 `101`** — 표준 오류 끝 줄 「**error: doctest failed, to rerun pass `--doc`**」. 예제의 `assert_eq!(r58d::add(2, 2), 5)` 가 **틀린 설명서**였고, 그것이 **빌드(테스트) 실패**가 됐다.
- ★★★ **「Test executable failed (exit status: 101)」** — 문서 테스트는 **따로 컴파일된 실행 파일**로 돈다. 그 안의 패닉이 `thread 'main' … panicked at src/lib.rs:5:1` 으로 나온다(**예제마다 자기 `main`** — 스레드 이름이 `main` 이다).
- ★★ **순서** — 표준 오류의 `Running unittests …` → `Doc-tests r58d` 가 보이듯 cargo 는 **단위 → (통합) → 문서** 순으로 돌리고, 문서 테스트가 **마지막**이다((5)의 `r58_split` 블록도 같은 순서). ★ **앞 단계가 실패하는 판은 던지지 않았다** — 그때 문서 단계까지 가는지는 이 문서가 모른다.
- ★ 패닉 위치가 `src/lib.rs:5:1` 인 것 — 예제의 `assert_eq!` 는 4행에 있다. rustdoc 이 예제를 감싼 코드의 줄을 원래 파일에 맞춰 옮긴 결과로 보이며, **정확한 대응 규칙은 확인하지 않았다.**

### (3) ★★★ 예제 표시 다섯 — `no_run` · `ignore` · `should_panic` · `compile_fail`

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

- ★★★ **`compile_fail` 인데 컴파일되면 `FAILED`** — 「**Test compiled successfully, but it's marked `compile_fail`.**」(33행 판 — `let x: i32 = r58a::half(8);` 은 멀쩡한 코드다). **「이 코드는 안 된다」를 문서로 약속해 두고, 그 약속이 깨지면 테스트가 잡는다.** 27행 판(`&str` 을 `i32` 에)은 정말 안 되어 `- compile fail ... ok`.
- ★★★ **`no_run` — `- compile ... ok`** — 9행의 `loop { … }` 는 **컴파일만** 하고 안 돌렸다(돌렸으면 끝나지 않는다). rustdoc 문서: 「The `no_run` attribute will compile your code but not run it」.
- ★★ **`ignore` — `ignored`** — 15행은 Rust 도 아닌 글자인데 **컴파일조차 안 해서** 에러가 없다. **`should_panic` — `ok`** — 21행의 `half(7)` 이 `assert!` 로 패닉해서 통과했다.
- ★★ **`--test-threads=1` 을 준 이유** — 문서 테스트 여섯이 **이름순(`line 15` · `line 21` · `line 27` · `line 3` · `line 33` · `line 9` — 문자열 순)** 으로 차례차례 돌아 줄 순서가 고정된다(관찰). 병렬이면 줄 순서가 흔들린다((6)).

### (4) ★★ `#[should_panic(expected = …)]` · `#[ignore]`

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

- ★★★ **`panic_with_other_text` 만 `FAILED`** — 패닉은 났는데 **문구가 다르다**: 「panic did not contain expected string / panic message: "no elements" / expected substring: "empty slice"」. `expected` 는 **부분 문자열** 비교다(`"no elements"` 판은 통과).
- ★★ **`#[should_panic]`(문구 없음)은 어떤 패닉이든 통과** — `any_panic ... ok`. 엉뚱한 곳의 패닉도 통과시키므로 **`expected` 를 붙이는 쪽이 안전하다.**
- ★★ **`#[ignore = "slow"]` → `ignored, slow`** — 이유 문자열이 출력에 붙는다. **`-- --ignored`** 로 그것만 돌리면 `slow_one ... ok` · `4 filtered out`.
- ★ 이 블록도 `--test-threads=1` 이다 — 다섯 줄이 이름순으로 고정된다.

### (5) ★★ `main.rs` 만 있으면 — 통합 테스트가 함수를 못 부른다

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

- ★★★ **E0433 — failed to resolve: use of unresolved module or unlinked crate `r58b`** — `tests/it.rs` 에서 `r58b::double` 을 불렀는데, **바이너리 크레이트는 다른 크레이트가 링크할 라이브러리를 만들지 않는다.** Book 11.3: 「Only library crates expose functions that other crates can use; binary crates are meant to be run on their own.」
- ★ `help:` 가 「`cargo add r58b`」를 권하는데 — **자기 자신을 의존성으로 추가하라는 엉뚱한 처방**이다. 진단 문구가 원인을 가리키지 않는 사례다(규칙 27 — 코드와 종료 코드만 근거로 쓴다).

**`lib.rs` 로 나누면 — 관용구.**

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

- ★★★ **통과 · `it_double ... ok`** — 로직은 `src/lib.rs`(라이브러리 크레이트 `r58b`), `src/main.rs` 는 그것을 **`r58b::double` 로 부르는 얇은 껍질**이다. 통합 테스트는 라이브러리를 쓴다.
- ★★ **테스트 실행 파일이 넷** — 표준 오류의 `Running unittests src/lib.rs` · `Running unittests src/main.rs` · `Running tests/it.rs` · `Doc-tests r58b`. 한 패키지에 **크레이트가 둘**(lib · bin)이라 단위 테스트 실행 파일도 둘이다.
- ★ `cargo run -q` 는 `42` — 바이너리 쪽도 그대로 돈다.

### (6) ★★ 테스트는 기본 병렬이다 — 서로 기다리는 두 테스트로

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

- ★★★ **기본 — 둘 다 `ok`** — `a_waits_for_b` 는 `b_sets_flag` 가 깃발을 세울 때까지 기다리는데, **동시에 돌았으니** 깃발을 봤다. Book 11.2: 「by default they run in parallel using threads」.
- ★★★ **`--test-threads=1` — `a_waits_for_b` 가 2초 뒤 `FAILED`** — 이름순으로 `a` 가 **먼저 혼자** 돌아 `b` 를 영영 못 봤다(「timed out waiting for the flag」). **같은 코드가 실행 방식만으로 통과/실패가 갈린다** — 테스트끼리 **전역 상태를 공유하면** 이렇게 된다.
- ★★ **스레드 이름** — `[a] start on thread Some("a_waits_for_b")` · 패닉 줄 `thread 'a_waits_for_b'`. **`--test-threads=1` 에서도 테스트는 자기 이름의 스레드에서** 돌았다(이 판의 관찰).
- ★ 첫 블록은 **`grep '^test ' | sort`** 로 줄을 정렬해 실었다 — 병렬 판의 `ok` 두 줄 순서는 **30판 중 1판이 뒤집혔다**(흔들리는 칸).

| | Rust `cargo test` | Go `go test` |
|---|---|---|
| 기본 | ★★ **병렬**(스레드 — Book 11.2) | **`t.Parallel()` 을 부른 테스트만** 서로 병렬 |
| 끄기 / 켜기 | `-- --test-threads=1` 로 **끈다** | `t.Parallel()` 로 **켠다** |
| 근거 | 이 편 (6) | [Go 49번](../../../go/syntax/49-testing-table-driven-t-run-cleanup-and-parallel/) 머리말 블록의 `go doc` — `Parallel` 은 「this test is to be run in parallel with (**and only with**) other parallel tests」 · `Run` 은 「blocks until f returns **or calls t.Parallel**」 |

- ★★ **기본값이 반대다** — Rust 는 **쓰는 쪽이 끄고**, Go 는 **쓰는 쪽이 켠다.** 그래서 Rust 에서 **전역 상태를 쓰는 테스트**는 아무 표시 없이 병렬로 섞인다((6)의 두 테스트가 그 모양). ★ Go 쪽 칸은 Go 49 의 블록을 인용한 것이고 **이 편은 Go 를 돌리지 않았다.**

## 문법 — 형태와 규칙

````text
   #[cfg(test)]                        ← 테스트 빌드에서만 컴파일
   mod tests {
       use super::*;                   ← 같은 크레이트 — 비공개도 보인다
       #[test] fn name() { assert_eq!(…); }
       #[test] #[should_panic(expected = "부분 문자열")] fn p() { … }
       #[test] #[ignore = "이유"] fn slow() { … }
   }
   tests/<파일>.rs                      ← 파일마다 별도 크레이트 — 공개 API 만
   /// ```            → 컴파일 + 실행        /// ```no_run       → 컴파일만
   /// ```ignore      → 아무것도 안 함        /// ```should_panic → 패닉해야 통과
   /// ```compile_fail → 컴파일이 실패해야 통과
   cargo test [--lib | --doc | --test <이름> | <이름 필터>] [-- --test-threads=1 | --ignored | --nocapture]
````

- ★★★ **자리가 곧 가시성이다 — 단위만 비공개에 닿고, 통합·문서·예제는 크레이트 밖이다**((1)).
- ★★★ **문서 예제는 테스트다 — 틀리면 `cargo test` 가 `101` 로 실패한다**((2)).
- ★★ **`compile_fail` 은 「안 된다」를 약속하는 테스트다 — 컴파일되면 실패**((3)).
- ★★ **로직은 `lib.rs`, `main.rs` 는 껍질 — 그래야 통합 테스트가 부른다**((5)).

## 어디서 틀리나

### 1. ★★★ 「문서 주석의 예제는 그냥 설명이다」

(2) — **컴파일되고 실행된다.** 틀리면 `cargo test` 가 실패한다. 설명서가 코드와 따로 놀지 못하게 하는 장치다.

### 2. ★★★ 「`tests/` 에서도 비공개 함수를 시험할 수 있다」

(1) — **E0603.** 통합 테스트는 **크레이트 밖**이다. 비공개는 단위 테스트에서.

### 3. ★★ 「`cargo test` 는 `examples/` 와 무관하다」

(1) — **빌드한다.** 예제가 깨지면 `cargo test` 도 깨진다(part 2 의 `ex` 행). 실행은 안 한다.

### 4. ★★ 「`#[should_panic]` 을 달았으니 그 패닉을 시험했다」

(4) — 문구 없는 `should_panic` 은 **아무 패닉이나** 통과시킨다. `expected` 를 붙인다.

### 5. ★★ 「`main.rs` 에 `pub fn` 을 두면 통합 테스트가 부른다」

(5) — **E0433.** `pub` 이어도 바이너리 크레이트는 링크할 라이브러리가 없다. `lib.rs` 로 나눈다.

### 6. ★★★ 「테스트는 적힌 순서대로 하나씩 돈다」

(6) — **기본 병렬.** 전역 상태를 공유하면 **실행 방식에 따라 통과/실패가 갈린다.** `--test-threads=1` 로 고쳐지면 그것은 **테스트끼리 샌다는 신호**다.

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| `#[test]`·`#[cfg(test)]`·`#[should_panic]`·`#[ignore]` | ★ **언어·컴파일러의 내장 속성** + libtest | (1)·(4) |
| 통합 테스트가 별도 크레이트라 비공개가 안 보인다 | ★ **가시성 규칙(언어)** + **cargo 의 배치 규칙**(`tests/` 파일마다 크레이트) | (1) |
| 문서 테스트가 별도 프로그램으로 돈다 · `extern crate` 가 끼워진다 | ★ **rustdoc 의 동작**(문서에 적힌 것) | (1)·(2) |
| `cargo test` 가 `examples/` 를 빌드한다 · 단위 → 통합 → 문서 순 | ★ **cargo 의 동작**(이 판 관찰) | (1)·(2) |
| 테스트 기본 병렬 | ★ **libtest 의 기본값**(Book 11.2) | (6) |
| `--test-threads=1` 에서 이름순 · 테스트마다 자기 이름의 스레드 | ★ **libtest 구현**(이 판 관찰 — 약속 아님) | (3)·(6) |
| 문서 테스트 패닉의 줄 번호(`5:1`) | ★ **rustdoc 구현**(대응 규칙 확인 안 함) | (2) |
| E0433 의 `help:`(`cargo add`) | ★ **rustc 진단** — 이 경우 엉뚱하다 | (5) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 근거 |
|---|---|---|
| 비공개 함수·내부 불변식을 시험한다 | **단위 테스트** `#[cfg(test)] mod tests` | (1) |
| 공개 API 를 사용자처럼 시험한다 | **`tests/*.rs`** | (1) |
| 사용법을 보여 주면서 계속 맞는지 확인한다 | **문서 테스트** | (2) |
| 예제가 네트워크·무한 루프라 돌리면 안 된다 | `no_run` | (3) |
| 「이렇게 쓰면 컴파일이 안 된다」를 보장한다 | `compile_fail` | (3) |
| 바이너리를 시험한다 | ★ **`lib.rs` + 얇은 `main.rs`** | (5) |
| 테스트가 전역 상태를 쓴다 | 상태를 **테스트마다 따로** — 안 되면 `--test-threads=1`(임시방편) | (6) |

## 핵심 문장

- ★★★ **테스트의 자리가 가시성을 정한다 — 단위 테스트만 비공개에 닿고, 통합·문서·예제는 내 크레이트 밖의 별도 크레이트다(비공개에 닿은 자리 1 / 4).**
- ★★★ **문서 주석의 예제는 컴파일되고 실행되는 테스트다 — 틀리면 `cargo test` 가 `doctest failed` 와 `101` 로 실패한다.**
- ★★ **`cargo test` 는 `examples/` 를 빌드만 하고, `--lib`·`--doc`·`--test` 는 자기 자리 하나만 돌린다.**
- ★★ **`main.rs` 만 있으면 통합 테스트가 부를 것이 없다 — 로직을 `lib.rs` 로.**
- ★★ **테스트는 기본 병렬이다 — Go 와 기본값이 반대다.**

## 관련 자료

- [**45번 주제**](../45-module-system-mod-use-pub-crate-and-file-layout/) — 모듈 시스템·가시성(`pub(crate)` 등). **그쪽은 「무엇이 어디서 보이나」, 여기는 「그래서 테스트를 어디에 두나」.**
- [**01번 주제**](../01-cargo-crates-and-modules/) — 바이너리·라이브러리 크레이트의 배치와 `cargo` 하위 명령.
- [**23번 주제**](../23-panic-vs-result/) — 패닉과 `Result`. `should_panic` 의 바탕.
- [**57번 주제**](../57-macros-macro-rules-and-procedural-macros/) — 절차 매크로가 별도 크레이트인 것과 통합 테스트가 별도 크레이트인 것은 **같은 「크레이트 경계」** 이야기다.
- [Go 49번](../../../go/syntax/49-testing-table-driven-t-run-cleanup-and-parallel/) — `t.Parallel` 과 정리 순서.

## 용어 풀이

- **libtest** — `#[test]` 함수들을 모아 돌리는 Rust 의 기본 테스트 실행기. `cargo test -- <옵션>` 의 `--` 뒤가 이것의 옵션이다.
- **`#[cfg(test)]`** — 테스트 빌드에서만 그 아이템을 컴파일하라는 조건부 컴파일 속성.
- **통합 테스트 크레이트** — `tests/` 의 파일 하나 = 크레이트 하나.
- **문서 테스트** — 문서 주석 속 코드 블록을 rustdoc 이 별도 프로그램으로 컴파일·실행하는 것.
- **`no_run` · `ignore` · `should_panic` · `compile_fail`** — 문서 테스트 코드 블록에 붙이는 표시(컴파일만 · 무시 · 패닉해야 통과 · 컴파일이 실패해야 통과).
- **E0603** — 비공개 아이템을 크레이트·모듈 밖에서 썼을 때의 에러.

## 더 들어가면

- `tests/common/mod.rs` — 통합 테스트끼리 도우미를 나누는 관용구(파일 하나 = 크레이트 하나라서 생기는 문제). **던지지 않았다.**
- `cargo test --no-fail-fast` — 실패한 테스트 실행 파일 뒤의 것도 돌리라는 옵션. **던지지 않았다.**
- 문서 테스트의 `#` 숨김 줄 · `edition2024` 표시 — rustdoc 문서.
