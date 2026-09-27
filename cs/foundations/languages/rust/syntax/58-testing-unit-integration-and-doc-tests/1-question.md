# rust/syntax/58 — 테스트: `#[test]` · 통합 테스트 · 문서 테스트 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 던지는 법 — 패키지는 아래 `r58_pkg.sh` 로 만든다(`bash r58_pkg.sh <이름> <파일>=<패키지 안 경로> …`). 그다음 `cd pkg && cargo test --offline`. 격자는 `bash r58_grid.sh`. **외부 의존성이 하나도 없다.**
> ★★★ **테스트 파일을 보면 먼저 물어라** — 「**이것은 내 크레이트 안인가, 밖인가**」와 「**이것을 돌리는 명령은 무엇인가**」.
> ★ **문항 12개 중 코드가 붙은 예측형은 6개**다. 소스 펜스는 캡처가 실파일에서 찍었다(`check-source-fences.py` 대조).

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

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 네 자리와 네 명령 (예측)

격자 스크립트와, 그것이 `pkg/` 에 복사하는 세 파일.

```bash
# r58_grid.sh
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
```

````rust
// r58_lib.rs
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
````

```rust
// r58_it.rs
#[test]
fn it_add() {
    assert_eq!(r58::add(1, 1), 2);
}
```

```rust
// r58_ex.rs
fn main() {
    println!("{}", r58::add(1, 1));
}
```

- part 1 의 네 줄 오른쪽 칸(무엇이 돌았나)을 채워라. 두 개수 줄 `… N / 12` 와 `… N / 4` 의 N 은? part 2 에서 `compiles` 가 아닌 줄의 에러 번호는?

### 2. ★★★ 틀린 설명서 (예측)

````rust
// r58_docfail_lib.rs
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
````

- `bash r58_pkg.sh r58d r58_docfail_lib.rs=src/lib.rs` 뒤 `cd pkg && cargo test --offline` — 무엇이 `ok` 이고 무엇이 `FAILED` 인가? 종료 코드는? 표준 오류의 마지막 줄은?

### 3. ★★★ 코드 블록의 표시 (예측)

````rust
// r58_docattrs_lib.rs
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
````

- `cargo test --offline --doc -- --test-threads=1` 의 여섯 줄 결과(`ok` · `ignored` · `FAILED` · 줄 끝의 꼬리표)를 적어라. 실패하는 것이 있다면 그 실패 메시지는?

### 4. ★★ 패닉을 기대하는 테스트와 미뤄 둔 테스트 (예측)

```rust
// r58_attrs_test.rs
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
```

- `tests/attrs.rs` 로 두고 `cargo test --offline --test attrs -- --test-threads=1` 을 돌리면 몇 개가 통과·실패·무시되나? 실패하는 것의 메시지 세 줄은? `-- --ignored` 로 돌리면?

### 5. ★★ `main.rs` 만 있는 패키지 (예측)

```rust
// r58_bin_main.rs
pub fn double(n: i32) -> i32 {
    n * 2
}

fn main() {
    println!("{}", double(21));
}
```

```rust
// r58_bin_it.rs
#[test]
fn it_double() {
    assert_eq!(r58b::double(21), 42);
}
```

- `src/main.rs` 와 `tests/it.rs` 로 두고 `cargo test --offline -j 1` 을 돌리면 컴파일되는가? 안 된다면 에러 번호와, `help:` 가 권하는 것은?

### 6. ★★★ 서로 기다리는 두 테스트 (예측)

```rust
// r58_par_test.rs
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
```

- 옵션 없이 `cargo test --offline --test par` 와 `-- --test-threads=1` 을 붙인 것은 각각 어떻게 끝나나? 뒤쪽에서 실패가 있다면 어느 테스트가, 무슨 메시지로, 대략 몇 초 뒤에?

### 7. ★★ 크레이트 밖의 세 자리 (왜)

- 1번 part 2 에서 통합 테스트·문서 테스트·예제가 모두 같은 번호로 막힌 이유는? rustdoc 문서는 문서 테스트 예제에 무엇을 끼워 넣는다고 적나?

### 8. ★★ 컴파일되면 실패하는 테스트 (경계)

- 3번의 33행 예제는 멀쩡한 코드인데 왜 `FAILED` 인가? 그런 표시를 **일부러** 쓰는 자리는 어디인가?

### 9. ★★ 문구 없는 `should_panic` (경계)

- 4번의 `any_panic` 은 어떤 패닉이든 통과시킨다. 그것이 위험한 이유와, `expected` 는 **어떤 비교**를 하나(4번의 두 판으로)?

### 10. ★★ `lib.rs` 로 나누면 (왜)

- 5번을 `src/lib.rs` + 얇은 `src/main.rs` 로 나누면 `cargo test` 가 도는 테스트 실행 파일은 **몇 개**이고 각각 무엇인가? 왜 단위 테스트 실행 파일이 둘인가?

### 11. ★★ Go 와 기본값 (연결)

- [Go 49번](../../../go/syntax/49-testing-table-driven-t-run-cleanup-and-parallel/)이 인용한 `go doc testing.T.Parallel` 의 문장과 Book 11.2 의 문장을 나란히 적어라. 두 언어의 기본값은 어떻게 반대인가? 6번의 두 테스트를 Go 로 옮기면(`t.Parallel()` 없이) 어느 쪽 결과에 가까울 것 같은가 — 이 문서는 그것을 쟀나?

### 12. ★ 정렬해서 실은 블록 (경계)

- 서머리 (6)의 첫 블록은 왜 `grep '^test ' | sort` 를 거쳐 실렸나? 그 대신 무엇을 결론의 근거로 삼았나(제5의 상태)?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
