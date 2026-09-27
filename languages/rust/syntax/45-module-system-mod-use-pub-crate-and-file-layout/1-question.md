# rust/syntax/45 — 모듈 시스템 — `mod` · `use` · `pub(crate)` · 파일 배치 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 던지는 법 — `rustc --edition 2021 <파일>.rs`(라이브러리는 `--crate-type lib`, 다른 크레이트에서 부르는 쪽은 `--extern 이름=lib이름.rlib`). 격자는 `bash <파일>.sh`. **cargo 도 외부 크레이트도 쓰지 않는다.**
> ★★★ **이름을 보면 먼저 물어라** — 「**이 항목은 어느 모듈에 사나**」와 「**부르는 자리는 그 모듈의 자손인가**」.
> ★ **문항 11개 중 코드가 붙은 예측형은 6개**다. 소스 펜스는 캡처가 실파일에서 찍었다(`check-source-fences.py` 대조).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 다섯 가시성 × 여섯 자리 (예측)

```bash
# r45_vis_grid.sh
# 항목 f 를 a::b::c 에 두고, 가시성 × 부르는 자리마다 크레이트를 새로 만들어 컴파일한다
# 부르는 자리 — c 안 · c 의 형제(b::s) · 부모(b) · 조부모(a) · 크레이트 루트 · 다른 크레이트
T=$'\t'
vis=('pub' 'pub(crate)' 'pub(super)' 'pub(in crate::a)' '')
sites=(same sibling parent grandparent root other)
call() {  # $1 = 자리 → 「어느 모듈:그 모듈에 둘 호출 한 줄」
  case $1 in
    same) echo 'c:pub fn g() -> i32 { f() }' ;;
    sibling) echo 's:pub fn g() -> i32 { super::c::f() }' ;;
    parent) echo 'b:pub fn g() -> i32 { c::f() }' ;;
    grandparent) echo 'a:pub fn g() -> i32 { b::c::f() }' ;;
    root) echo 'root:pub fn g() -> i32 { a::b::c::f() }' ;;
    other) echo 'none:' ;;
  esac
}
printf 'visibility\tsite\tresult\n'
ok=0; total=0
for v in "${vis[@]}"; do
  for s in "${sites[@]}"; do
    c=$(call "$s"); at=${c%%:*}; line=${c#*:}
    put() { [ "$at" = "$1" ] && echo "            $line"; }
    {
      echo 'pub mod a {'
      put a
      echo '    pub mod b {'
      put b
      echo '        pub mod c {'
      echo "            $v fn f() -> i32 { 1 }"
      put c
      echo '        }'
      echo '        pub mod s {'
      put s
      echo '        }'
      echo '    }'
      echo '}'
      put root
    } > lib.rs
    if [ "$s" = other ]; then
      rustc --edition 2021 --crate-type lib --crate-name lib -A dead_code lib.rs 2>/dev/null || { echo "lib failed"; exit 1; }
      printf 'fn main() {\n    let _ = lib::a::b::c::f();\n}\n' > user.rs
      rustc --edition 2021 --extern lib=liblib.rlib user.rs 2>err.txt; rc=$?
    else
      rustc --edition 2021 --crate-type lib --crate-name lib -A dead_code lib.rs 2>err.txt; rc=$?
    fi
    if [ $rc = 0 ]; then r=compiles; ok=$((ok+1)); else r=$(grep -m1 '^error' err.txt); fi
    row="${v:-(none)}$T$s$T$r"
    n=$(printf '%s' "$row" | awk -F'\t' '{print NF}')
    [ "$n" = 3 ] || { echo "column count $n != 3"; exit 1; }
    printf '%s\n' "$row"
    total=$((total+1))
  done
done
echo "cells that compiled: $ok / $total"
```

- 서른 행의 셋째 칸(`compiles` 또는 첫 `error` 줄)을 채워라. 마지막 줄의 `N / 30` 은? 에러가 나는 칸들의 **에러 번호는 몇 가지**인가?

### 2. ★★★ `mod a;` 하나와 여덟 가지 파일 배치 (예측)

```bash
# r45_files.sh
# main.rs 에는 `mod a;` 한 줄. 파일을 어디에 두느냐만 바꿔 가며 컴파일한다
# a 가 `mod b;` 를 품는 판은 b 가 어디 있어야 하나를 본다
T=$'\t'
layouts=(
  'a.rs'
  'a/mod.rs'
  'a.rs a/mod.rs'
  ''
  'a.rs a/b.rs'
  'a.rs b.rs'
  'a/mod.rs a/b.rs'
  'a/mod.rs b.rs'
)
printf 'files next to main.rs\tresult\n'
ok=0; total=0
for l in "${layouts[@]}"; do
  rm -rf p; mkdir p; cd p || exit 1
  printf 'mod a;\nfn main() {\n    println!("{}", a::name());\n}\n' > main.rs
  for f in $l; do
    mkdir -p "$(dirname "$f")"
    case $f in
      a.rs|a/mod.rs)
        if [[ " $l " == *'b.rs '* ]]; then
          printf 'mod b;\npub fn name() -> &%sstatic str {\n    b::NAME\n}\n' "'" > "$f"
        else
          printf 'pub fn name() -> &%sstatic str {\n    "%s"\n}\n' "'" "$f" > "$f"
        fi ;;
      *) printf 'pub const NAME: &str = "%s";\n' "$f" > "$f" ;;
    esac
  done
  if rustc --edition 2021 main.rs 2>err.txt; then r="runs: $(./main)"; ok=$((ok+1)); else r=$(grep -m1 '^error' err.txt); fi
  cd .. || exit 1
  printf '%s\n' "${l:-(none)}$T$r"
  total=$((total+1))
done
echo "layouts that compiled: $ok / $total"
```

- 여덟 행의 둘째 칸을 채워라(`runs: …` 면 찍히는 파일 이름까지, 에러면 번호). `a.rs` 가 `mod b;` 를 품을 때 `b` 는 **어느 폴더**에서 찾나?

### 3. ★★ 안쪽에 숨긴 모듈과 바깥에 다시 건 이름 (예측)

```rust
// r45_shelf.rs
mod inner {
    pub fn tool() -> i32 {
        7
    }
}

pub use inner::tool;
```

```rust
// r45_user.rs
fn main() {
    println!("{}", shelf::tool());
    println!("{}", shelf::inner::tool());
}
```

- `r45_shelf.rs` 를 `--crate-name shelf` 라이브러리로 만들고 `r45_user.rs` 를 붙이면 컴파일되는가? 안 된다면 **어느 줄**이 무슨 번호로 막히고, `help:` 는 무엇을 권하나?

### 4. ★★ 크레이트 루트에서 가져온 이름을 안쪽 모듈에서 (예측)

```rust
// r45_use_scope.rs
use std::collections::HashMap;

mod store {
    pub fn make() -> HashMap<&'static str, i32> {
        HashMap::new()
    }
}

fn main() {
    let m: HashMap<&str, i32> = store::make();
    println!("{}", m.len());
}
```

- 컴파일되는가? 에러라면 번호와 개수는? `help:` 가 내놓는 후보 **두 가지**는 무엇인가?

### 5. ★★ 같은 소스 두 에디션 — `use` 로 부른 다른 크레이트 (예측)

```rust
// r45_extern.rs
use shelf::tool;

fn main() {
    println!("{}", tool());
}
```

```rust
// r45_extern_expr.rs
mod m {
    pub fn f() -> i32 {
        shelf::tool()
    }
}

fn main() {
    println!("{}", m::f());
}
```

- 둘 다 `--extern shelf=libshelf.rlib` 로 붙인다. `r45_extern.rs` 를 `--edition 2015` 와 `--edition 2018` 로 각각 던지면? `r45_extern_expr.rs` 를 `--edition 2015` 로 던지면?

### 6. ★ 가시성만 바꾼 네 바이너리 (예측)

```bash
# r45_same_bin.sh
# 같은 바이너리 크레이트에서 f 의 가시성만 바꿔 빌드하고 실행 파일의 sha256 을 견준다
# (소스 파일 이름은 p.rs 로 고정한다)
hashes=""
for v in 'pub' 'pub(crate)' 'pub(super)' '(none)'; do
  w=${v/(none)/}
  rm -rf d && mkdir d && cd d || exit 1
  printf 'mod m {\n    %s fn f() -> i32 {\n        41\n    }\n    pub fn g() -> i32 {\n        f() + 1\n    }\n}\n\nfn main() {\n    println!("{}", m::g());\n}\n' "$w" > p.rs
  rustc --edition 2021 p.rs 2>/dev/null || { echo "build failed: $v"; exit 1; }
  h=$(sha256sum p | cut -c1-16)
  printf '%-11s run=%s sha256=%s\n' "$v" "$(./p)" "$h"
  hashes="$hashes$h"$'\n'
  cd .. || exit 1
done
echo "distinct hashes: $(printf '%s' "$hashes" | sort -u | wc -l) / 4"
```

- 네 행의 `run=` 과 `sha256=` 칸은 어떻게 되나? 마지막 줄의 `N / 4` 는?

### 7. ★★ 조상이 아닌 경로 · 루트의 `super` · 상대 경로 (경계)

- `pub(in crate::a)` 를 **`a` 의 자손이 아닌** 모듈 `b` 의 항목에 달면? 크레이트 루트의 항목에 `pub(super)` 를 달면? 2015 에서 되던 `pub(in a)` 는 2018 에서 어떻게 되나?

### 8. ★★ 막힌 칸의 진단은 범위를 말하나 (왜)

- 1번에서 막힌 칸의 진단 **제목**에 그 항목의 가시성 범위(부모까지 · `a` 까지 …)가 적혀 있나? 적혀 있지 않다면 진단의 **어느 줄**이 범위를 대신 알려 주나?

### 9. ★★ `pub` 이 곧 「밖에서 보인다」인가 (경계)

- `-W unreachable_pub` 을 켜고 3번의 `r45_shelf.rs` 와, 거기서 `pub use` 줄만 뺀 판을 각각 라이브러리로 컴파일하면 무엇이 나오나? 「크레이트 밖에서 실제로 닿는가」는 무엇이 정하나?

### 10. ★★ 대문자와 `internal` (연결)

- Go 는 가시성을 **이름의 첫 글자**로, 모듈 경계를 **`internal` 디렉토리**로 정한다([Go 40번](../../../go/syntax/40-package-visibility-naming-and-internal/)). Rust 의 `pub` · `pub(crate)` · `pub(in path)` 와 각각 무엇이 짝이 되고, 무엇이 짝이 없나? `internal` 규칙을 **누가** 집행하는가(언어 · 도구)?

### 11. ★ 파일이 곧 모듈인가 (연결)

- Python([42번](../../../python/syntax/42-modules-packages-and-import/))과 JS([42번](../../../js/syntax/42-esm-modules/))에서는 파일을 두기만 하면 import 할 수 있다. Rust 에서 `mod` 로 올리지 않은 `.rs` 파일은 어떻게 되나([01번](../01-cargo-crates-and-modules/))? 모듈 트리는 **디렉토리가** 정하나, **선언이** 정하나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
