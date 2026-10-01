# rust/syntax/45 — 모듈 시스템 — `mod` · `use` · `pub(crate)` · 파일 배치 — 정답

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ `19 / 30` — 막힌 11칸은 전부 E0603 하나

**출력**

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

**왜 그런가**

- ★★★ **「통과 19 / 30」** — `pub` 6 · `pub(crate)` 5 · `pub(super)` 3 · `pub(in crate::a)` 4 · 없음 1.
- ★★★ **규칙은 한 줄이다 — 「`f` 가 보이는 범위는 어떤 모듈 M 이고, 부르는 자리가 M 이거나 M 의 자손이면 통과」.** 다섯 가시성은 **M 을 고르는 법**일 뿐이다.

```text
   가시성            f 가 보이는 범위 M          통과한 자리
   ──────────────── ────────────────────────── ─────────────────────────────────────
   (없음)            c (자기 모듈)               same
   pub(super)        b (부모)                    same · sibling · parent
   pub(in crate::a)  a (지정한 조상)             same · sibling · parent · grandparent
   pub(crate)        크레이트 루트               + root                (다른 크레이트는 막힘)
   pub               어디서나                    + other
```

- ★★ **「형제(`b::s`)」는 `f` 가 비공개면 막히고 `pub(super)` 면 통과한다** — 형제는 `c` 의 자손이 아니지만 `b` 의 자손이기 때문이다. 「형제끼리는 보인다」가 아니라 **「부모까지 열면 부모의 자손 전부가 본다」** 다.
- ★★ **에러 번호는 한 가지(E0603)** 다. 범위가 무엇이었는지는 번호가 말해 주지 않는다(8번).
- ★ **다른 크레이트 칸은 `pub` 만 통과** — `pub(crate)` 의 「크레이트」가 **경계**다. 같은 사실을 [01번](../01-cargo-crates-and-modules/)이 `lib.rs` 와 `main.rs` 사이에서 쟀다(한 패키지 안이어도 크레이트가 둘이면 막힌다).

### 2. ★★★ `4 / 8` — 후보는 둘, 겹치면 E0761, 없으면 E0583, 안쪽 모듈은 **부모 이름의 폴더**에서

**출력**

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

**왜 그런가**

- ★★★ **`mod a;` 의 후보는 `a.rs` 와 `a/mod.rs` 둘** — 하나면 통과(1·2행), 둘 다면 **E0761**(3행), 없으면 **E0583**(4행). 여기까지는 [01번](../01-cargo-crates-and-modules/) (2)가 이미 쟀다.
- ★★★ **`a` 안의 `mod b;` 는 `a/b.rs` 에서 찾는다 — `a.rs` 를 썼든 `a/mod.rs` 를 썼든 같다**(5·7행). `main.rs` 옆의 `b.rs` 는 **안 본다**(6·8행 E0583).
- ★★ 진단이 그 경로를 직접 말한다 —

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

- `` = help: to create the module `b`, create file "a/b.rs" or "a/b/mod.rs" `` — **후보 경로가 부모 모듈의 이름을 폴더로 쓴다.** 모듈 트리(`crate::a::b`)와 폴더 트리(`a/b.rs`)가 **같은 모양**이 되도록 강제하는 규칙이다.

### 3. ★★ 3행 `shelf::inner::tool()` 이 E0603(`` module `inner` is private ``) — `help:` 는 `shelf::tool()`

**출력**

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

**왜 그런가**

- ★★★ **`tool` 은 `pub` 인데도 `shelf::inner::tool` 로는 못 부른다** — 경로 위의 **`inner` 가 비공개**다. 항목의 `pub` 은 「부모가 허락하면 보인다」이지 「어디서나 보인다」가 아니다.
- ★★★ **`pub use inner::tool;` 이 같은 함수를 `shelf::tool` 이라는 공개 경로에 다시 건다(재수출).** 2행은 통과했고, `help:` 도 **재수출된 경로를 권한다.**
- ★ 이것이 라이브러리의 **공개 API 와 내부 파일 배치를 떼어 놓는** 관용구다 — 파일을 어떻게 쪼개든 밖에서 보이는 경로는 `pub use` 가 정한다.
- ★ 라이브러리는 `--remap-path-prefix "$PWD=."` 로 만들어 진단의 파일 경로를 상대 경로(`./r45_shelf.rs`)로 줄였다 — 다른 크레이트의 소스는 진단이 **그 크레이트가 컴파일된 경로**로 가리킨다.

### 4. ★★ E0412 + E0433 두 개 — 후보는 `use crate::HashMap;` 과 `use std::collections::HashMap;`

**출력**

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

**왜 그런가**

- ★★★ **`use` 는 그 선언이 있는 모듈 하나에만 이름을 들인다.** 루트의 `use std::collections::HashMap;` 은 `store` 안으로 **상속되지 않는다** — 타입 자리(E0412)와 경로 자리(E0433)가 따로 막혔다.
- ★★★ **`help:` 의 첫 후보가 `use crate::HashMap;`** — 루트의 `use` 가 **루트 모듈의 (비공개) 항목**이 되었다는 뜻이다. 비공개 항목은 **자기 모듈과 그 자손**이 보므로(1번의 규칙) `store` 가 `crate::HashMap`·`super::HashMap` 으로 가져올 수 있다.

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

- ★ 실제로 `use super::HashMap;` 한 줄로 통과했다(`0` — 빈 맵의 길이).

### 5. ★★ 2015 는 `use` 에서 E0432 · 2018 은 통과 — 그런데 2015 도 **식 안의 `shelf::tool()`** 은 통과

**출력**

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

**왜 그런가**

- ★★ **2015 에서 막힌 것은 `use shelf::tool;` 한 줄이다(E0432)** — `help:` 가 `extern crate shelf;` 를 권한다. 2015 의 `use` 경로는 **크레이트 루트 기준**이라 `--extern` 으로 붙인 이름이 루트에 없으면 못 찾는다.
- ★★★ **그런데 같은 2015 에서 모듈 안의 식 `shelf::tool()` 은 `extern crate` 없이 통과했다**(`7`). 「2018 이전에는 `extern crate` 가 반드시 필요했다」는 **이 판(1.92)에서 틀렸다** — 막히는 자리는 `use` 경로였다.
- ★ 2018 부터는 `use` 경로도 `--extern` 이름을 바로 본다. cargo 는 의존성마다 `--extern` 을 넘기므로 2018+ 크레이트에 `extern crate` 줄이 필요 없다.

### 6. ★ 네 행 모두 `run=42` · 해시가 같다 — `1 / 4`

**출력**

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

**왜 그런가**

- ★★★ **가시성만 바꾼 네 바이너리가 바이트 단위로 같았다(해시 1가지).** 가시성은 **컴파일 시점의 이름 해석 규칙**이고, 통과한 뒤 실행 파일에 남기는 것이 **없다** — 「재 봤더니 같았다」가 아니라 **「잴 것이 없다」** 를 보인 블록이다(서머리 (0)의 부적용 창).
- ★ 파일 이름을 `p.rs` 로 고정한 이유 — 이름이 다르면 **가시성과 무관한 까닭**으로 해시가 갈릴 여지가 있어 그 변수를 막았다(이름만 바꾼 판은 재지 않았다).
- ★ **바이너리 크레이트·최적화 없음 한 판**의 관찰이다. 라이브러리의 `pub` 은 **메타데이터(rlib)** 로 다른 크레이트에 노출되므로 이 결론을 rlib 로 넓히지 않는다(재지 않았다).

### 7. ★★ E0742 · E0433(`` too many leading `super` ``) · 2018 은 「relative paths are not supported」

```text
===== 소스: r45_vis_nonancestor.rs =====
mod a {
    pub mod x {}
}

mod b {
    pub(in crate::a) fn f() {}
}

fn main() {}
===== rustc --edition 2021 r45_vis_nonancestor.rs =====
error[E0742]: visibilities can only be restricted to ancestor modules
 --> r45_vis_nonancestor.rs:6:12
  |
6 |     pub(in crate::a) fn f() {}
  |            ^^^^^^^^

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0742`.
(exit 1)
```

```text
===== 소스: r45_vis_root_super.rs =====
pub(super) fn f() {}

fn main() {}
===== rustc --edition 2021 r45_vis_root_super.rs =====
error[E0433]: failed to resolve: there are too many leading `super` keywords
 --> r45_vis_root_super.rs:1:5
  |
1 | pub(super) fn f() {}
  |     ^^^^^ there are too many leading `super` keywords

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0433`.
(exit 1)
```

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

- ★★ **`pub(in path)` 의 path 는 그 항목의 조상이어야 한다(E0742)** — 가시성은 **자기 조상 쪽으로만** 넓힐 수 있다. 옆 가지(`a`)에 「너만 봐라」로 줄 수는 없다.
- ★ **루트에는 부모가 없다** — 루트 항목의 `pub(super)` 는 `super` 가 가리킬 곳이 없어 경로 해석 에러(E0433)다.
- ★ **2015 의 `pub(in a)`(루트 기준 상대 경로)는 통과, 2018 부터는 번호 없는 에러**로 `crate::a` 를 권한다(Reference: 「`pub(in path)` 는 `crate`·`self`·`super` 로 시작해야 한다. 2015 는 루트의 모듈로 시작해도 된다」).

### 8. ★★ 번호는 같고 **`note:` 가 선언 줄을 끼워 보여 준다**

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

- ★★ 1번의 11칸이 모두 **E0603 `` function `f` is private ``** 였다 — **`pub(super)` 도 「private」로 적힌다.** 「비공개」가 아니라 **「이 자리에서는 안 보인다」** 로 읽어야 한다.
- ★★★ 범위를 알려 주는 것은 **`` note: the function `f` is defined here `` 아래에 끼워진 선언 줄**(`pub(super) fn f() -> i32 {`)이다. 번호와 제목만 보면 「`pub` 을 붙이면 되겠지」로 고치게 되는데, 실제로 필요한 것은 **그 자리까지 범위를 넓히는 것**(`pub(in crate::a)` 이면 충분할 수도 있다)이다.

### 9. ★★ 없을 때 `` unreachable `pub` item ``(권고 `pub(crate)`), 있을 때 침묵 — 도달 가능성은 **경로 전체**가 정한다

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

- ★★ **`pub use` 가 없는 판**(`r45_shelf_bare.rs`)은 `-W unreachable_pub` 이 `inner::tool` 을 짚고 **`pub(crate)` 로 줄이라** 권한다 — 적힌 `pub` 이 실제로는 크레이트 밖에 닿지 않는다는 뜻이다.
- ★★ **`pub use` 가 있는 판**(3번 블록 첫 명령, 같은 플래그)은 **경고 0줄에 `exit 0`** — 재수출이 도달 경로를 만들었기 때문이다.
- ★★★ **「밖에서 보인다」는 항목 하나의 `pub` 이 아니라 루트에서 그 항목까지 가는 경로(또는 재수출)가 전부 열려 있어야 성립한다.** 이 린트는 **기본으로 꺼져 있다**(`requested on the command line`) — 켜 봐야 보인다.

### 10. ★★ 대문자 ↔ `pub` 은 짝, `internal` ↔ `pub(in path)` 는 어긋난 짝 — `internal` 은 **`go` 명령**이 집행한다

- ★★ Go 의 **대문자 첫 글자(내보냄)** 는 Rust 의 **`pub`** 과 짝이다 — 둘 다 **언어 명세**가 정한다. 단 Go 의 비공개(소문자)는 **패키지 전체**가 보고, Rust 의 비공개는 **그 모듈과 자손**만 본다(1번 — 형제 모듈도 막혔다).
- ★★ Go 의 **`internal`** 은 「이 디렉토리의 부모 아래에서만 import」 — Rust 의 **`pub(in 조상)`** 과 모양이 가장 가깝다. 차이는 둘 —
  ① Go 는 **import 경로(디렉토리)** 단위, Rust 는 **모듈 트리** 단위 ·
  ② ★★★ **`internal` 은 명세가 아니라 `go` 명령의 규칙**이다([Go 40번](../../../go/syntax/40-package-visibility-naming-and-internal/) — 명세에 그 규칙이 없다는 것을 그 편이 grep 으로 보였다). Rust 의 `pub(in path)` 는 **언어(Reference)** 이고 **rustc 가** 막는다(1번 — cargo 없이 rustc 만으로 막혔다).
- ★ **`pub(crate)` 의 짝은 Go 에 없다** — Go 의 공개 단위는 모듈(`go.mod`)이 아니라 패키지다.

### 11. ★ `mod` 로 안 올린 파일은 **컴파일되지 않는다** — 트리는 **선언**이 정하고, 디렉토리는 **그 선언이 찾을 자리**만 정한다

- ★★ [01번](../01-cargo-crates-and-modules/) — **`mod` 로 올리지 않은 `.rs` 파일은 에러도 경고도 없이 빌드에서 빠진다.** Rust 에 자동 수집은 없다.
- ★★ 2번 — `mod b;` 가 **있어야** 파일을 찾고, 찾는 **자리**는 부모 모듈 이름의 폴더다. 그래서 「폴더가 트리를 정한다」가 아니라 **「선언이 트리를 정하고, 폴더 배치는 그 선언을 따라야 한다」** 다.
- ★ Python 은 **`import` 하는 순간 파일을 찾아 실행**하고([42번](../../../python/syntax/42-modules-packages-and-import/)), JS ESM 은 **`import` 명세자(경로)가 곧 모듈**이다([42번](../../../js/syntax/42-esm-modules/)). Rust 의 `mod` 는 import 가 아니라 **「이 크레이트의 트리에 이 모듈이 있다」는 등록**이고, 가져다 쓰는 것은 `use` 다 — **등록과 사용이 두 낱말로 갈려 있다.**

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서·서머리의 **모든 블록** | `capture.sh` — 블록마다 명령을 배너에 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` 기본 규칙 넷 · **고칠 것 0** |
| ★★★ **가시성 격자** | `r45_vis_grid.sh` — 서른 칸마다 크레이트를 새로 만들어 컴파일(다른 크레이트 칸은 rlib + `--extern`) · 탭 구분 · 칸 수 검사 | 30 | **`19 / 30`** · 막힌 칸 전부 E0603 |
| ★★ **파일 배치 격자** | `r45_files.sh` — 여덟 배치 | 8 | **`4 / 8`** · E0761 1 · E0583 3 |
| 재수출 · 린트 | `r45_shelf` · `r45_shelf_bare` | 2 | E0603(`inner`) · `unreachable_pub` 1건 / 0건 |
| `use` 의 범위 | `r45_use_scope` · `r45_use_super` | 2 | E0412 + E0433 · `0` |
| 에디션 | `r45_extern`(2015·2018) · `r45_extern_expr`(2015) · `r45_vis_relative`(2015·2018) | 5 | E0432 · 통과 · 통과 · 통과 · 에러 |
| 가시성 한계 | `r45_vis_nonancestor` · `r45_vis_root_super` · `r45_e0603` | 3 | E0742 · E0433 · E0603 |
| ★ **부적용 창** | `r45_same_bin.sh` — 가시성 넷의 바이너리 해시 | 4 | **`1 / 4`**(한 가지) |
| **안 던진 것** — `#[path]` 속성 · `pub(self)` · rlib 메타데이터의 가시성 · cargo 의 `src/bin/` 자동 탐색 | — | 0 | ★ 「안 던졌다」로 표시했다 |

**구현 의존 항목**(버전·환경이 바뀌면 **다시 찍어야 하는** 것).

| 항목 | 왜 |
|---|---|
| 진단 문구(`help:` 가 권하는 후보 · `private module` 등) | ★ rustc 의 문구 — 판에 매인다 |
| 2015 에서 식 경로가 `--extern` 이름을 보는 것 | ★ 이 판(1.92)의 관찰 — 옛 컴파일러에서는 다를 수 있다 |
| 가시성만 다른 바이너리가 같은 해시 | ★ 컴파일러가 만든 산출물의 관찰 — 언어 보장이 아니다 |

★ **다시 찍는 법** — `capture.sh <새 디렉토리>` 를 그대로 돌리고 `normalize-shaky.py <원본> <새 디렉토리>` 로 견준다.

## 실행 환경

이 파일의 모든 출력·에러는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서
블록 배너에 적은 명령(기본 `rustc --edition 2021`, 에디션 비교는 `2015`·`2018`)으로 실제로 돌려 받은 것이다.\
★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
★★ 블록 첫 줄 `===== 소스: <파일> =====` 아래가 **돌린 소스 전문**이고, **진단의 줄 번호는 그 파일 기준**이다(격자 스크립트가 만드는 `lib.rs`·`main.rs` 는 스크립트 안에서 생긴다).\
★ 이 주제의 출력에는 **흔들리는 칸이 없다**(서머리 맨 위 부분의 표).
