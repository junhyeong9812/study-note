# rust/syntax/45 — 모듈 시스템 — `mod` · `use` · `pub(crate)` · 파일 배치 — 정리 (힌트)

★★★ **본체 창 — ② 컴파일러 진단의 격자(가시성 다섯 × 부르는 자리 여섯 → 통과인가, 막히면 무슨 번호인가)다.** 가시성은 실행 중에 아무것도 남기지 않으므로 **컴파일러가 막느냐**로만 보인다((0)의 부적용 창이 그 증명이다).

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| 안 흔들린다 | ★★★ **격자의 결과 칸과 「통과 19 / 30」 · 파일 배치의 「4 / 8」** | 가시성·파일 탐색 규칙은 **언어가 정한다**(Reference) — **이 주제의 본체** |
| 안 흔들린다 | E0603 · E0583 · E0761 · E0412 · E0433 · E0432 · E0742 번호 · `파일:줄:칸` · 종료 코드 | 같은 rustc 판에서 고정이다 |
| 안 흔들린다 | 가시성만 바꾼 바이너리의 해시 `1 / 4` | 같은 판·같은 플래그에서 고정이다(관찰) |
| ★ **구현이 정한다** | `help:` 가 권하는 후보(`use crate::HashMap;` 등)와 문구 | ★ rustc 진단의 문구 — 판에 매인다 |

★ 이 주제의 블록에는 **흔들리는 칸이 없다** — 패닉도 주소도 시간도 안 찍힌다. 정규화는 기본 넷만 걸었고 **걸린 칸이 0** 이어야 맞다.

## 한눈에 — 쉽게 말하면

**모듈은 「회사의 부서 조직도」다.** 조직도는 인사 발령(`mod`)으로만 생기고, 사무실 배치(파일)는 그 조직도를 따라야 한다.
문서(항목)마다 「열람 범위」 도장을 찍는데, 도장은 전부 **「어느 부서까지」** 하나로 읽힌다 — 우리 팀(없음) · 상위 부서(`pub(super)`) · 지정한 본부(`pub(in …)`) · 회사 전체(`pub(crate)`) · 외부 공개(`pub`).
그 부서와 **그 아래 조직 전부**가 문서를 본다. 옆 부서는 못 본다.

| 비유 | 실체 |
|---|---|
| 「**인사 발령으로만 부서가 생긴다**」 | ★★★ **`mod a;` 가 있어야 `a` 가 트리에 들어온다** — 파일만 두면 빌드에서 빠진다([01번](../01-cargo-crates-and-modules/)) |
| 「**사무실은 부서 이름의 층에**」 | ★★★ **`a` 안의 `mod b;` 는 `a/b.rs`** — `main.rs` 옆 `b.rs` 는 안 본다((2)) |
| 「**열람 범위 = 어느 부서까지**」 | ★★★ **가시성 다섯은 전부 「보이는 모듈 M」 하나를 고르는 법** — 부르는 자리가 M 이거나 그 자손이면 통과((1)) |
| 「**옆 팀은 못 본다**」 | ★★ **비공개 항목은 형제 모듈에서 막힌다** — 형제가 보려면 `pub(super)`((1)) |
| 「**외부 공개 문서라도 그 부서가 비공개면**」 | ★★ **`pub fn` 이 비공개 모듈 안에 있으면 밖에서 그 경로로 못 온다** — `pub use` 로 공개 경로에 다시 건다((3)) |
| 「**공지는 붙인 게시판에만**」 | ★★ **`use` 는 그 모듈에만 이름을 들인다** — 자식 모듈은 따로 가져와야 한다((4)) |
| 「**도장은 서류에만, 제품에는 없다**」 | ★ **가시성만 바꾼 바이너리는 바이트 단위로 같았다**((0)) |

```text
   (1)의 격자를 한 장으로 — f 는 a::b::c 에 산다

   crate ─┬─ a ─┬─ b ─┬─ c ── f        ← 여기 도장을 찍는다
          │     │     └─ s             ← 형제
          │     └──(b 가 부모, a 가 조부모)
          └─ (다른 크레이트는 트리 밖)

   도장           보이는 범위 M    →  통과한 자리
   (없음)         c               →  c
   pub(super)     b               →  c · s · b
   pub(in crate::a) a             →  c · s · b · a
   pub(crate)     crate           →  c · s · b · a · 루트
   pub            어디서나        →  + 다른 크레이트
```

> **가시성(visibility)** — 그 항목의 이름을 **어느 모듈에서 부를 수 있나**를 정하는 표시(`pub` 계열).\
> 예: `pub(super) fn f()` 는 부모 모듈과 그 자손에서만 `f` 를 부를 수 있다.

> **재수출(re-export)** — `pub use 경로;` 로 **다른 곳에 있는 항목을 이 모듈의 공개 이름으로 다시 거는 것**.\
> 예: `mod inner { pub fn tool() }` + `pub use inner::tool;` → 밖에서 `shelf::tool()`.

## 이 주제가 답하려는 질문

1. ★★★ **가시성 표시 다섯은 각각 어디까지 여나 — 그리고 막히면 진단은 무엇을 말하나**((1)·(5)).
2. ★★★ **파일을 어디에 두어야 `mod` 가 찾나 — 모듈 트리와 폴더 트리는 어떻게 맞물리나**((2)).
3. ★★ **공개 API 를 내부 배치와 떼어 놓으려면 — `pub use` 와 `use` 의 범위**((3)·(4)).

★ **선행** — [**16번 주제**](../16-structs-impl-and-associated-functions/)가 「**필드는 기본 비공개**」까지를 다뤘다(E0603 = 타입이 안 보임 · E0616 = 필드가 안 보임). 그 편이 「모듈 시스템 자체는 45번이 정본」이라고 이 편을 가리킨다.
★★★ **이미 잰 것 — 다시 재지 않고 인용한다.**
[01번](../01-cargo-crates-and-modules/) (2) — **`mod x;` 의 후보는 `x.rs`·`x/mod.rs` 둘 · 없으면 E0583 · 둘 다면 E0761** · **`mod` 로 안 올린 파일은 경고 없이 빠진다** ·
(3) — **`crate::`·`super::`·`self::` 경로**(`greet/polite.rs` 배치까지) · 어디서 틀리나 3 — **같은 패키지의 `main.rs` 와 `lib.rs` 는 다른 크레이트라 `pub(crate)` 가 서로 안 보인다(E0603)**.
이 편은 그 위에 **다섯 × 여섯 가시성 격자**, **자식 모듈의 파일 탐색 자리**, **재수출과 도달 가능성**, **`use` 의 범위**, **에디션이 경로를 바꾸는 자리**를 더한다.

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ② 컴파일러 진단 격자다

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ② ★★★ **컴파일러 진단 격자**(칸마다 크레이트를 새로 만들어 컴파일) | 그 자리에서 **이름이 보이나** — 통과 / E0603 | ★ **본체**((1)) |
| ② ★★ **파일 배치 격자** | `mod` 가 **어느 파일**을 여나 — E0583 / E0761 | 쓴다((2)) |
| ③ ★★ **린트 `unreachable_pub`**(기본 꺼짐 — `-W` 로 켠다) | 적힌 `pub` 이 **실제로 크레이트 밖에 닿나** | 쓴다((3)) |
| ④ ★★ **에디션 2015 × 2018** | `use` 경로·`pub(in path)` 가 **어디서 시작하나** | 쓴다((5)) |
| ① 실행 출력 | — | ★ **부적용** — 가시성은 실행 중에 아무것도 안 한다. **증명**: 아래 블록 |
| `crate::`·`super::`·`self::` 경로 · `mod` 안 올린 파일 | — | ★ **이미 잰 것** — 01번 (2)·(3) |

```text
===== 소스: r45_same_bin.sh =====
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
===== bash r45_same_bin.sh =====
pub         run=42 sha256=dfe9fa5468427ab5
pub(crate)  run=42 sha256=dfe9fa5468427ab5
pub(super)  run=42 sha256=dfe9fa5468427ab5
(none)      run=42 sha256=dfe9fa5468427ab5
distinct hashes: 1 / 4
(exit 0)
```

- ★★★ **가시성 넷(`pub`·`pub(crate)`·`pub(super)`·없음)의 바이너리가 해시 한 가지(`1 / 4`)** — 가시성은 **컴파일 시점의 이름 해석**이고 통과한 뒤에는 흔적이 없다. 「재 봤더니 같다」가 아니라 **「잴 것이 없다」** 의 증거다(바이너리 크레이트 한 판의 관찰 — rlib 메타데이터는 재지 않았다).

### (1) ★★★ 가시성 다섯 × 부르는 자리 여섯 — 서른 칸 격자

**언제 쓰나** — 항목에 도장을 찍을 때마다. **「어느 범위까지 열까」를 칸으로 보고 고른다.**

```text
===== 소스: r45_vis_grid.sh =====
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
===== bash r45_vis_grid.sh =====
visibility	site	result
pub	same	compiles
pub	sibling	compiles
pub	parent	compiles
pub	grandparent	compiles
pub	root	compiles
pub	other	compiles
pub(crate)	same	compiles
pub(crate)	sibling	compiles
pub(crate)	parent	compiles
pub(crate)	grandparent	compiles
pub(crate)	root	compiles
pub(crate)	other	error[E0603]: function `f` is private
pub(super)	same	compiles
pub(super)	sibling	compiles
pub(super)	parent	compiles
pub(super)	grandparent	error[E0603]: function `f` is private
pub(super)	root	error[E0603]: function `f` is private
pub(super)	other	error[E0603]: function `f` is private
pub(in crate::a)	same	compiles
pub(in crate::a)	sibling	compiles
pub(in crate::a)	parent	compiles
pub(in crate::a)	grandparent	compiles
pub(in crate::a)	root	error[E0603]: function `f` is private
pub(in crate::a)	other	error[E0603]: function `f` is private
(none)	same	compiles
(none)	sibling	error[E0603]: function `f` is private
(none)	parent	error[E0603]: function `f` is private
(none)	grandparent	error[E0603]: function `f` is private
(none)	root	error[E0603]: function `f` is private
(none)	other	error[E0603]: function `f` is private
cells that compiled: 19 / 30
(exit 0)
```

- ★★★ **「통과 19 / 30」** — `pub` 6 · `pub(crate)` 5 · `pub(super)` 3 · `pub(in crate::a)` 4 · 없음 1.
- ★★★ **다섯 표시는 전부 「보이는 모듈 M」 하나를 고른다** — 없음 = 자기 모듈 `c` · `pub(super)` = 부모 `b` · `pub(in crate::a)` = 지정한 조상 `a` · `pub(crate)` = 루트 · `pub` = 제한 없음. **부르는 자리가 M 이거나 M 의 자손이면 통과**다(Reference 의 「비공개 항목은 현재 모듈과 그 자손이 접근한다」를 M 에 대입한 것).
- ★★ **형제 `b::s` 가 비공개 `f` 에서 막힌다** — 형제는 `c` 의 자손이 아니다. `pub(super)` 로 부모까지 열어야 형제가 본다.
- ★★ **막힌 11칸이 전부 E0603 하나** — 범위가 무엇이었든 제목은 `` function `f` is private `` 다((5)).
- ★ **다른 크레이트 칸은 `pub` 만** — `pub(crate)` 의 경계는 **크레이트**다. 01번이 같은 경계를 한 패키지의 `lib.rs`/`main.rs` 사이에서 쟀다.

비용 — 없음((0)의 해시).

### (2) ★★★ `mod a;` 가 찾는 파일 — 여덟 배치

**언제 쓰나** — 모듈을 파일로 쪼갤 때. 특히 **모듈 안에 모듈**을 둘 때.

```text
===== 소스: r45_files.sh =====
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
===== bash r45_files.sh =====
files next to main.rs	result
a.rs	runs: a.rs
a/mod.rs	runs: a/mod.rs
a.rs a/mod.rs	error[E0761]: file for module `a` found at both "a.rs" and "a/mod.rs"
(none)	error[E0583]: file not found for module `a`
a.rs a/b.rs	runs: a/b.rs
a.rs b.rs	error[E0583]: file not found for module `b`
a/mod.rs a/b.rs	runs: a/b.rs
a/mod.rs b.rs	error[E0583]: file not found for module `b`
layouts that compiled: 4 / 8
(exit 0)
```

- ★★★ **「통과 4 / 8」** — `a.rs` · `a/mod.rs` · (`a.rs` + `a/b.rs`) · (`a/mod.rs` + `a/b.rs`).
- ★★ 1\~4행은 01번 (2)의 재확인이다(후보 둘 · 둘 다면 E0761 · 없으면 E0583).
- ★★★ **`a` 안의 `mod b;` 는 `a/b.rs` 를 연다 — `a` 를 `a.rs` 로 두었든 `a/mod.rs` 로 두었든 같다.** `main.rs` 옆의 `b.rs` 는 **보지 않는다**(6·8행).

```text
===== 소스: r45_nested.sh =====
# a.rs 가 `mod b;` 를 품고, b.rs 는 main.rs 옆에 있다 — rustc 의 진단 전문
mkdir -p p && cd p || exit 1
printf 'mod a;\nfn main() {\n    println!("{}", a::name());\n}\n' > main.rs
printf 'mod b;\npub fn name() -> &%sstatic str {\n    b::NAME\n}\n' "'" > a.rs
printf 'pub const NAME: &str = "b.rs";\n' > b.rs
rustc --edition 2021 main.rs
===== bash r45_nested.sh =====
error[E0583]: file not found for module `b`
 --> a.rs:1:1
  |
1 | mod b;
  | ^^^^^^
  |
  = help: to create the module `b`, create file "a/b.rs" or "a/b/mod.rs"
  = note: if there is a `mod b` elsewhere in the crate already, import it with `use crate::...` instead

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0583`.
(exit 1)
```

- ★★ **`help:` 가 후보 경로 둘을 직접 적는다** — `"a/b.rs"` 또는 `"a/b/mod.rs"`. **부모 모듈의 이름이 폴더가 된다** — 모듈 트리 `crate::a::b` 와 폴더 트리 `a/b.rs` 가 같은 모양이 되도록 강제하는 규칙이다.

```text
   모듈 트리             파일 트리 (둘 중 하나로)
   crate  (main.rs)      main.rs
    └─ a                  a.rs         또는   a/mod.rs
        └─ b              a/b.rs       또는   a/b/mod.rs      ← main.rs 옆 b.rs 는 후보가 아니다
```

### (3) ★★ `pub fn` 인데 밖에서 못 부른다 — 경로 전체와 `pub use`

**언제 쓰나** — 라이브러리의 공개 API 를 정할 때. **내부 파일 배치와 밖에서 보이는 경로를 떼어 놓는다.**

```text
===== 소스: r45_shelf.rs =====
mod inner {
    pub fn tool() -> i32 {
        7
    }
}

pub use inner::tool;
===== 소스: r45_user.rs =====
fn main() {
    println!("{}", shelf::tool());
    println!("{}", shelf::inner::tool());
}
===== rustc --edition 2021 --crate-type lib --crate-name shelf --remap-path-prefix "$PWD=." -W unreachable_pub r45_shelf.rs =====
(exit 0)
===== rustc --edition 2021 --extern shelf=libshelf.rlib r45_user.rs =====
error[E0603]: module `inner` is private
 --> r45_user.rs:3:27
  |
3 |     println!("{}", shelf::inner::tool());
  |                           ^^^^^ private module
  |
note: the module `inner` is defined here
 --> ./r45_shelf.rs:1:1
help: consider importing this function instead
  |
3 -     println!("{}", shelf::inner::tool());
3 +     println!("{}", shelf::tool());
  |

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0603`.
(exit 1)
```

- ★★★ **`shelf::inner::tool()` 은 E0603 `` module `inner` is private ``** — `tool` 은 `pub` 이지만 **경로 위의 `inner` 가 막는다.** 항목 하나의 `pub` 은 「부모가 허락하면」이다.
- ★★★ **`pub use inner::tool;` 이 공개 경로 `shelf::tool` 을 만든다** — 2행은 통과했고 `help:` 도 그 경로를 권했다.
- ★★ **린트로 본 같은 사실** — `-W unreachable_pub` 이 이 판에서는 **0줄**, 재수출이 없는 판에서는 한 줄이다.

```text
===== 소스: r45_shelf_bare.rs =====
mod inner {
    pub fn tool() -> i32 {
        7
    }
}
===== rustc --edition 2021 --crate-type lib -A dead_code -W unreachable_pub r45_shelf_bare.rs =====
warning: unreachable `pub` item
 --> r45_shelf_bare.rs:2:5
  |
2 |     pub fn tool() -> i32 {
  |     ---^^^^^^^^^^^^^^^^^
  |     |
  |     help: consider restricting its visibility: `pub(crate)`
  |
  = help: or consider exporting it for use by other crates
  = note: requested on the command line with `-W unreachable-pub`

warning: 1 warning emitted

(exit 0)
```

- ★★ `pub(crate)` 로 줄이라는 권고 — 적힌 `pub` 이 **크레이트 밖에 닿지 않으니 과장**이라는 뜻이다. 이 린트는 **기본으로 꺼져 있다**(`requested on the command line`).

### (4) ★★ `use` 는 그 모듈에만 — 자식은 따로 가져온다

**언제 쓰나** — 파일을 쪼갠 뒤 「위에서 `use` 했는데 왜 안 보이나」가 나올 때.

```text
===== 소스: r45_use_scope.rs =====
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
===== rustc --edition 2021 r45_use_scope.rs =====
error[E0412]: cannot find type `HashMap` in this scope
 --> r45_use_scope.rs:4:22
  |
4 |     pub fn make() -> HashMap<&'static str, i32> {
  |                      ^^^^^^^ not found in this scope
  |
help: consider importing one of these structs
  |
4 +     use crate::HashMap;
  |
4 +     use std::collections::HashMap;
  |

error[E0433]: failed to resolve: use of undeclared type `HashMap`
 --> r45_use_scope.rs:5:9
  |
5 |         HashMap::new()
  |         ^^^^^^^ use of undeclared type `HashMap`
  |
help: consider importing one of these structs
  |
4 +     use crate::HashMap;
  |
4 +     use std::collections::HashMap;
  |

error: aborting due to 2 previous errors

Some errors have detailed explanations: E0412, E0433.
For more information about an error, try `rustc --explain E0412`.
(exit 1)
```

- ★★★ **E0412(타입 자리) + E0433(경로 자리)** — 루트의 `use std::collections::HashMap;` 은 **`store` 로 상속되지 않는다.** `use` 는 선언한 모듈 하나의 이름표다.
- ★★★ **`help:` 첫 후보가 `use crate::HashMap;`** — 루트의 `use` 는 **루트의 비공개 항목**이고, 비공개는 **자손이 본다**((1)). 그래서 자식이 `super::HashMap` 으로 가져올 수 있다 —

```text
===== 소스: r45_use_super.rs =====
use std::collections::HashMap;

mod store {
    use super::HashMap;

    pub fn make() -> HashMap<&'static str, i32> {
        HashMap::new()
    }
}

fn main() {
    let m: HashMap<&str, i32> = store::make();
    println!("{}", m.len());
}
===== rustc --edition 2021 r45_use_super.rs =====
(exit 0)
===== ./r45_use_super =====
0
(exit 0)
```

### (5) ★★ 막히면 진단은 무엇을 말하나 — 그리고 에디션이 경로를 바꾸는 자리

**E0603 의 전문.**

```text
===== 소스: r45_e0603.rs =====
pub mod a {
    pub mod b {
        pub mod c {
            pub(super) fn f() -> i32 {
                1
            }
        }
    }
}

pub fn root() -> i32 {
    a::b::c::f()
}
===== rustc --edition 2021 --crate-type lib r45_e0603.rs =====
error[E0603]: function `f` is private
  --> r45_e0603.rs:12:14
   |
12 |     a::b::c::f()
   |              ^ private function
   |
note: the function `f` is defined here
  --> r45_e0603.rs:4:13
   |
 4 |             pub(super) fn f() -> i32 {
   |             ^^^^^^^^^^^^^^^^^^^^^^^^

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0603`.
(exit 1)
```

- ★★ 제목은 `pub(super)` 인데도 **`private function`** — 「비공개」가 아니라 **「이 자리에서 안 보인다」** 로 읽는다. 범위는 **`note:` 아래 끼워진 선언 줄**이 말한다.

**에디션 — `use` 경로의 시작점.**

```text
===== 소스: r45_extern.rs =====
use shelf::tool;

fn main() {
    println!("{}", tool());
}
===== 소스: r45_shelf.rs =====
mod inner {
    pub fn tool() -> i32 {
        7
    }
}

pub use inner::tool;
===== rustc --edition 2021 --crate-type lib --crate-name shelf r45_shelf.rs =====
(exit 0)
===== rustc --edition 2015 --extern shelf=libshelf.rlib r45_extern.rs =====
error[E0432]: unresolved import `shelf`
 --> r45_extern.rs:1:5
  |
1 | use shelf::tool;
  |     ^^^^^ use of unresolved module or unlinked crate `shelf`
  |
help: you might be missing a crate named `shelf`, add it to your project and import it in your code
  |
1 + extern crate shelf;
  |

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0432`.
(exit 1)
===== rustc --edition 2018 --extern shelf=libshelf.rlib r45_extern.rs =====
(exit 0)
===== ./r45_extern =====
7
(exit 0)
```

- ★★ **2015 는 `use shelf::tool;` 에서 E0432**(`help:` `extern crate shelf;`), **2018 은 통과.** 2015 의 `use` 경로는 크레이트 루트에서 시작한다.

```text
===== 소스: r45_extern_expr.rs =====
mod m {
    pub fn f() -> i32 {
        shelf::tool()
    }
}

fn main() {
    println!("{}", m::f());
}
===== 소스: r45_shelf.rs =====
mod inner {
    pub fn tool() -> i32 {
        7
    }
}

pub use inner::tool;
===== rustc --edition 2021 --crate-type lib --crate-name shelf r45_shelf.rs =====
(exit 0)
===== rustc --edition 2015 --extern shelf=libshelf.rlib r45_extern_expr.rs =====
(exit 0)
===== ./r45_extern_expr =====
7
(exit 0)
```

- ★★★ **그런데 2015 에서도 식 안의 `shelf::tool()` 은 `extern crate` 없이 통과했다.** 「2018 전에는 `extern crate` 가 필수」는 이 판에서 **`use` 경로에만** 맞았다.

**에디션 — `pub(in path)` 의 시작점.**

```text
===== 소스: r45_vis_relative.rs =====
mod a {
    pub(in a) fn f() {}
}

fn main() {}
===== rustc --edition 2015 -A dead_code r45_vis_relative.rs =====
(exit 0)
===== rustc --edition 2018 -A dead_code r45_vis_relative.rs =====
error: relative paths are not supported in visibilities in 2018 edition or later
 --> r45_vis_relative.rs:2:12
  |
2 |     pub(in a) fn f() {}
  |            ^ help: try: `crate::a`

error: aborting due to 1 previous error

(exit 1)
```

- ★ 2015 는 `pub(in a)`(루트 기준) 통과, 2018 부터 **`crate::a` 로 쓰라**는 에러다(Reference 의 조항 그대로).

## 문법 — 형태와 규칙

```text
   mod a;                       ← a.rs 또는 a/mod.rs 를 트리에 등록 (둘 다면 E0761, 없으면 E0583)
   mod a { … }                  ← 같은 파일 안에 등록
   pub fn f()                   ← 제한 없음 (경로 위 모듈이 전부 열려 있어야 밖에서 닿는다)
   pub(crate) fn f()            ← 이 크레이트
   pub(super) fn f()            ← 부모 모듈과 그 자손      (루트에서는 E0433)
   pub(in crate::a) fn f()      ← 조상 a 와 그 자손       (조상이 아니면 E0742)
   fn f()                       ← 자기 모듈과 그 자손
   use crate::a::b;  use super::x;  use self::y;       ← 이 모듈에만 이름을 들인다
   pub use inner::tool;                                ← 다른 경로에 공개 이름으로 다시 건다
```

- ★★★ **가시성 = 「보이는 모듈 M」, 통과 = 「부르는 자리 ∈ M 의 부분 트리」**((1)).
- ★★★ **`mod b;` 의 파일은 부모 모듈 이름의 폴더 안**((2)).
- ★★ **밖에 닿는 것은 경로 전체가 열려 있을 때** — 아니면 `pub use`((3)).
- ★★ **`use` 는 상속되지 않는다**((4)).

## 어디서 틀리나

### 1. ★★★ 「비공개는 같은 파일(또는 형제)끼리는 보인다」

(1) — **형제 모듈에서 E0603.** 비공개의 범위는 **자기 모듈과 그 자손**이다. 형제에게 보이려면 `pub(super)`.

### 2. ★★★ 「`pub` 을 붙였으니 밖에서 쓸 수 있다」

(3) — **경로 위 모듈이 비공개면 E0603(`module … is private`).** `pub use` 로 공개 경로를 만들거나 모듈을 `pub mod` 로 연다. `-W unreachable_pub` 이 이 과장을 짚는다.

### 3. ★★ 「`b.rs` 를 `main.rs` 옆에 두면 `a` 안의 `mod b;` 가 찾는다」

(2) — **`a/b.rs` 여야 한다**(E0583, `help:` 가 경로를 적어 준다).

### 4. ★★ 「루트에서 `use` 했으니 하위 모듈에서도 보인다」

(4) — **E0412 · E0433.** 하위 모듈에서 `use super::…` 로 다시 가져온다.

### 5. ★★ 「E0603 이면 `pub` 을 붙이면 된다」

(5) — 제목이 범위를 말하지 않는다. **`note:` 의 선언 줄**을 보고 **필요한 만큼만** 넓힌다(`pub(super)` → `pub(in crate::a)` 로 충분할 수 있다).

### 6. ★ 「2018 이전에는 다른 크레이트를 쓰려면 무조건 `extern crate`」

(5) — **이 판에서 2015 의 식 경로는 `--extern` 이름을 봤다.** 막힌 것은 `use` 경로였다.

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| 비공개 = 현재 모듈과 자손 · `pub(in path)` 는 조상만 | ★ **언어**(Reference — Visibility) | (1) · E0742 |
| `mod` 의 파일 후보(`a.rs`·`a/mod.rs` · 자식은 `a/b.rs`) | ★ **언어**(Reference — Modules) | (2) |
| `use` 가 그 모듈에만 이름을 들인다 · `use` 가 항목이다 | ★ **언어**(Reference — Use declarations) | (4) |
| 2018+ 의 `use` 가 `--extern` 이름을 본다 | ★ **에디션** | (5) |
| 2015 의 식 경로가 `--extern` 이름을 본다 | ★ **이 판(1.92)의 관찰** — 옛 컴파일러는 확인하지 않았다 | (5) |
| `unreachable_pub` 이 기본 꺼짐 · 권고 문구 | ★ **rustc 린트 설정** — 판에 매인다 | (3) |
| 가시성만 다른 바이너리가 같은 해시 | ★ **산출물의 관찰** — 언어가 약속한 것이 아니다 | (0) |
| `help:` 의 후보 · 문구 | ★ **rustc 진단** | (2)·(4) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 근거 |
|---|---|---|
| 이 모듈 안에서만 쓰는 도우미 | **표시 없음** | (1) |
| 형제 모듈과 나눠 쓴다 | **`pub(super)`** | (1) |
| 한 서브트리(`a` 아래)에서만 | **`pub(in crate::a)`** | (1) |
| 크레이트 안 어디서나, 밖에는 비공개 | **`pub(crate)`** — 바이너리 크레이트라면 사실상 `pub` 과 같은 효과 | (1) |
| 라이브러리의 공개 API | **`pub` + 경로 전체를 열거나 `pub use` 로 재수출** | (3) |
| 파일을 쪼개도 공개 경로는 그대로 두고 싶다 | **비공개 `mod` + `pub use`** | (3) |
| 하위 모듈에서 부모의 `use` 를 쓰고 싶다 | **`use super::이름;`** | (4) |

## 핵심 문장

- ★★★ **가시성 표시는 전부 「보이는 모듈 M」을 고르는 것이고, 부르는 자리가 M 의 부분 트리면 통과한다 — 서른 칸 중 19칸이 통과했다.**
- ★★★ **비공개는 형제에게도 안 보인다 — 부모까지 열어야(`pub(super)`) 형제가 본다.**
- ★★★ **`a` 안의 `mod b;` 는 `a/b.rs` 에서 찾는다 — 모듈 트리가 폴더 트리를 정한다.**
- ★★ **`pub fn` 도 경로가 막히면 밖에서 못 온다 — `pub use` 가 공개 경로를 따로 만든다.**
- ★★ **`use` 는 상속되지 않는다 — 막힌 11칸이 모두 E0603 이듯, 진단 번호는 범위를 말하지 않으니 `note:` 의 선언 줄을 읽는다.**

## 관련 자료

- [**01번 주제**](../01-cargo-crates-and-modules/) — `mod` 후보 둘 · E0583/E0761 · 경로 세 가지 · 안 올린 파일 · `lib.rs`/`main.rs` 경계. **그쪽은 「트리를 만드는 법」, 여기는 「트리 위에서 누가 무엇을 보나」.**
- [**16번 주제**](../16-structs-impl-and-associated-functions/) — 필드 가시성(E0616) · 타입 가시성(E0603).
- [**26번 주제**](../26-orphan-rule-and-newtype/) — 크레이트 경계가 **트레이트 구현**을 막는 다른 규칙(고아 규칙).
- [**46번 주제**](../46-crates-cargo-toml-features-and-workspaces/) — 크레이트를 묶는 쪽(Cargo · 워크스페이스). ★ 이 편이 rustc 만 쓴 이유 — 가시성은 cargo 와 무관하다.
- Go 갈래 [`40-package-visibility-naming-and-internal`](../../../go/syntax/40-package-visibility-naming-and-internal/) — **대문자 규칙(명세)과 `internal`(도구)** — Rust 는 둘 다 **언어**(rustc)다.
- Python 갈래 [`42-modules-packages-and-import`](../../../python/syntax/42-modules-packages-and-import/) · JS 갈래 [`42-esm-modules`](../../../js/syntax/42-esm-modules/) — **파일이 곧 모듈**인 언어들. Rust 는 **등록(`mod`)과 사용(`use`)이 갈린다.**

## 용어 풀이

- **모듈(module)** — 이름을 담는 상자. 크레이트 루트가 뿌리인 트리를 이룬다.
- **크레이트 루트(crate root)** — 트리의 뿌리 파일(`main.rs`·`lib.rs`). 경로 `crate::` 가 가리킨다.
- **`mod`** — 모듈을 트리에 **등록**한다. 몸통이 없으면 파일을 연다.
- **`use`** — 긴 경로에 **이 모듈 안의 짧은 이름**을 준다. 그 자체가 항목이라 가시성을 가진다.
- **`pub(crate)` · `pub(super)` · `pub(in path)`** — 보이는 범위를 크레이트 · 부모 · 지정한 조상으로 **제한한 공개**.
- **재수출(re-export)** — `pub use` 로 다른 경로의 항목을 공개 이름으로 다시 거는 것.
- **E0603** — 「이 자리에서 그 항목(또는 경로 위 모듈)이 안 보인다」.
- **E0583 / E0761** — `mod` 의 파일이 없다 / 후보가 둘 다 있다.
- **E0742** — `pub(in path)` 의 path 가 조상이 아니다.
- **`unreachable_pub`** — 적힌 `pub` 이 크레이트 밖에 닿지 않을 때 짚는 린트(기본 꺼짐).

## 더 들어가면

- `#[path = "..."]` 속성 — `mod` 의 파일 위치를 직접 지정한다. **이 문서는 던지지 않았다.**
- `pub(self)` — 「표시 없음」과 같다(Reference). **던지지 않았다.**
- cargo 가 `src/bin/*.rs` 를 **자동으로 바이너리 크레이트**로 잡는 규칙 — 크레이트 자동 탐색은 cargo 의 일이고 모듈 탐색(이 편)과 다르다. **던지지 않았다.**

## 실행 환경

**기준 소스** — [Reference — Visibility and privacy](https://doc.rust-lang.org/reference/visibility-and-privacy.html)(「비공개 항목은 **현재 모듈과 그 자손**이 접근한다」 · 「`pub(in path)` 의 path 는 **그 항목의 조상 모듈**이어야 한다 · `crate`·`self`·`super` 로 시작해야 하고 2015 는 루트의 모듈로 시작해도 된다」) ·
[Reference — Modules](https://doc.rust-lang.org/reference/items/modules.html)(파일 모듈의 경로) · [Reference — Use declarations](https://doc.rust-lang.org/reference/items/use-declarations.html).
★ Reference 는 **이 머신의 `rust-docs`(1.92.0) 로컬 사본**을 열어 읽었다.
**실행 검증** — 이 문서의 모든 출력·에러는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서
블록 배너의 명령(기본 **`rustc --edition 2021`**, 에디션 비교는 `2015`·`2018`)으로 돌려 받은 것이다. **cargo 는 쓰지 않았다** — 모듈과 가시성은 **rustc 의 일**이라 rustc 만으로 전부 재현된다.\
★★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다. 소스 펜스도 캡처가 찍었다.\
★ **속도·메모리는 재지 않았다.**
