# rust/syntax/46 — 크레이트 · `Cargo.toml` · feature · 워크스페이스 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러는 **`cargo 1.92.0 (344c4567c 2025-10-21)`** · **`rustc 1.92.0 (ded5c06cf 2025-12-08)`** · `x86_64-unknown-linux-gnu` 에서
> 블록 배너의 명령으로 실제로 돌려 받은 것이다. cargo 는 **`CARGO_NET_OFFLINE=true`** · `CARGO_HOME` 을 작업 디렉토리 안에 두고 돌렸다(네트워크 없음 — 의존성은 전부 경로).\
> ★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
> ★★ cargo 가 찍는 **절대 경로는 배너의 `sed "s|$PWD|.|g"` 로 `./` 로 바꿨다**(표준 출력·표준 오류 각각에 건다). 그 필터는 **캡처가 원 명령의 출력을 다 받은 뒤** 걸었다 — 종료 코드는 원 명령의 것이다.\
> ★ `Finished … in 0.28s` 의 **시간**은 실행마다 바뀌는 칸이다(서머리 머리말의 표).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ `a=true b=false` → `a=true b=true` × 2 → 다시 `a=true b=false` — 같이 빌드한 패키지가 feature 를 합친다

**출력**

```text
===== 소스: r46_ws.sh =====
# 워크스페이스 ws — 라이브러리 gear(feature a·b) 하나를 앱 둘이 각자 다른 feature 로 쓴다
mkdir -p ws/gear/src ws/app1/src ws/app2/src
cat > ws/Cargo.toml <<'TOML'
[workspace]
members = ["gear", "app1", "app2"]
resolver = "2"
TOML
cat > ws/gear/Cargo.toml <<'TOML'
[package]
name = "gear"
version = "0.1.0"
edition = "2021"

[features]
a = []
b = []
TOML
cat > ws/gear/src/lib.rs <<'RS'
pub fn report() -> String {
    format!("a={} b={}", cfg!(feature = "a"), cfg!(feature = "b"))
}
RS
for n in 1 2; do
  feat=$([ "$n" = 1 ] && echo a || echo b)
  cat > "ws/app$n/Cargo.toml" <<TOML
[package]
name = "app$n"
version = "0.1.0"
edition = "2021"

[dependencies]
gear = { path = "../gear", features = ["$feat"] }
TOML
  printf 'fn main() {\n    println!("{}", gear::report());\n}\n' > "ws/app$n/src/main.rs"
done
===== bash r46_ws.sh =====
(exit 0)
===== cd ws && cargo run -q -p app1 =====
a=true b=false
(exit 0)
===== cd ws && cargo build -q --workspace =====
(exit 0)
===== ws/target/debug/app1 =====
a=true b=true
(exit 0)
===== ws/target/debug/app2 =====
a=true b=true
(exit 0)
===== cd ws && cargo run -q -p app1 =====
a=true b=false
(exit 0)
```

**왜 그런가**

- ★★★ **`-p app1` 만 고르면 gear 는 app1 이 켠 `a` 만** 켜진 채 빌드된다(`a=true b=false`).
- ★★★ **`--workspace` 로 둘을 함께 고르면 gear 는 한 번만 빌드되고, 두 앱이 켠 feature 의 합집합(`a`+`b`)으로** 빌드된다 — 그래서 **app1 의 실행 파일도 `b=true` 를 답한다**(app1 은 `b` 를 요청한 적이 없다).
- ★★ **마지막 `cargo run -p app1` 이 다시 `b=false`** — 선택이 바뀌자 gear 를 다른 feature 조합으로 **다시 빌드해 app1 을 다시 링크**했다. **같은 경로의 같은 실행 파일이 「마지막에 무엇과 함께 빌드됐나」에 따라 다르게 동작한다.**
- ★ feature 의 합산 단위는 **「이번 명령이 선택한 패키지들」** 이다(cargo 문서 — Feature unification). 트리로 본 같은 사실 —

```text
===== 소스: r46_ws.sh =====
# 워크스페이스 ws — 라이브러리 gear(feature a·b) 하나를 앱 둘이 각자 다른 feature 로 쓴다
mkdir -p ws/gear/src ws/app1/src ws/app2/src
cat > ws/Cargo.toml <<'TOML'
[workspace]
members = ["gear", "app1", "app2"]
resolver = "2"
TOML
cat > ws/gear/Cargo.toml <<'TOML'
[package]
name = "gear"
version = "0.1.0"
edition = "2021"

[features]
a = []
b = []
TOML
cat > ws/gear/src/lib.rs <<'RS'
pub fn report() -> String {
    format!("a={} b={}", cfg!(feature = "a"), cfg!(feature = "b"))
}
RS
for n in 1 2; do
  feat=$([ "$n" = 1 ] && echo a || echo b)
  cat > "ws/app$n/Cargo.toml" <<TOML
[package]
name = "app$n"
version = "0.1.0"
edition = "2021"

[dependencies]
gear = { path = "../gear", features = ["$feat"] }
TOML
  printf 'fn main() {\n    println!("{}", gear::report());\n}\n' > "ws/app$n/src/main.rs"
done
===== bash r46_ws.sh =====
(exit 0)
===== cd ws && cargo tree -e features -p app1 | sed "s|$PWD|.|g" =====
app1 v0.1.0 (./ws/app1)
├── gear feature "a"
│   └── gear v0.1.0 (./ws/gear)
└── gear feature "default"
    └── gear v0.1.0 (./ws/gear)
(exit 0)
===== cd ws && cargo tree -e features --workspace -i gear | sed "s|$PWD|.|g" =====
gear v0.1.0 (./ws/gear)
├── gear feature "a"
│   └── app1 v0.1.0 (./ws/app1)
│       └── app1 feature "default" (command-line)
├── gear feature "b"
│   └── app2 v0.1.0 (./ws/app2)
│       └── app2 feature "default" (command-line)
└── gear feature "default" (command-line)
    ├── app1 v0.1.0 (./ws/app1) (*)
    └── app2 v0.1.0 (./ws/app2) (*)
(exit 0)
```

- ★★ `-p app1` 트리에는 **`gear feature "a"` 만**, `--workspace -i gear`(누가 gear 의 feature 를 켰나를 거꾸로) 트리에는 **`a` ← app1 · `b` ← app2** 가 나란히 있다.

### 2. ★★★ app1 통과 · app2 통과 · 워크스페이스 빌드는 **app1** 에서 E0425

**출력**

```text
===== 소스: r46_neg.sh =====
# gear 에 「켜면 함수가 사라지는」 feature minimal 을 둔다. app1 은 그 함수를 쓰고, app2 는 minimal 을 켠다
mkdir -p ws/gear/src ws/app1/src ws/app2/src
printf '[workspace]\nmembers = ["gear", "app1", "app2"]\nresolver = "2"\n' > ws/Cargo.toml
cat > ws/gear/Cargo.toml <<'TOML'
[package]
name = "gear"
version = "0.1.0"
edition = "2021"

[features]
minimal = []
TOML
cat > ws/gear/src/lib.rs <<'RS'
pub fn core_fn() -> &'static str {
    "core"
}

#[cfg(not(feature = "minimal"))]
pub fn extra() -> &'static str {
    "extra"
}
RS
printf '[package]\nname = "app1"\nversion = "0.1.0"\nedition = "2021"\n\n[dependencies]\ngear = { path = "../gear" }\n' > ws/app1/Cargo.toml
printf 'fn main() {\n    println!("{} {}", gear::core_fn(), gear::extra());\n}\n' > ws/app1/src/main.rs
printf '[package]\nname = "app2"\nversion = "0.1.0"\nedition = "2021"\n\n[dependencies]\ngear = { path = "../gear", features = ["minimal"] }\n' > ws/app2/Cargo.toml
printf 'fn main() {\n    println!("{}", gear::core_fn());\n}\n' > ws/app2/src/main.rs
===== bash r46_neg.sh =====
(exit 0)
===== cd ws && cargo run -q -p app1 =====
core extra
(exit 0)
===== cd ws && cargo run -q -p app2 =====
core
(exit 0)
===== cd ws && cargo build -q --workspace 2>&1 >/dev/null | sed "s|$PWD|.|g" =====
error[E0425]: cannot find function `extra` in crate `gear`
 --> app1/src/main.rs:2:46
  |
2 |     println!("{} {}", gear::core_fn(), gear::extra());
  |                                              ^^^^^ not found in `gear`
  |
note: found an item that was configured out
 --> ./ws/gear/src/lib.rs:6:8
  |
5 | #[cfg(not(feature = "minimal"))]
  |          --------------------- the item is gated here
6 | pub fn extra() -> &'static str {
  |        ^^^^^

For more information about this error, try `rustc --explain E0425`.
error: could not compile `app1` (bin "app1") due to 1 previous error
(exit 101)
```

**왜 그런가**

- ★★★ **각자 따로 빌드하면 둘 다 통과한다** — 그래서 이 결함은 **각 패키지의 CI 로는 안 잡힌다.**
- ★★★ **함께 빌드하면 gear 는 `minimal` 이 켜진 한 벌뿐**이고(1번의 합집합), 그 벌에는 `extra` 가 **없다**. 그래서 **`minimal` 을 요청하지도 않은 app1 이 깨진다** — 에러는 app2 가 아니라 **app1** 에서 났다.
- ★★ **E0425 의 `note: found an item that was configured out`** 이 `#[cfg(not(feature = "minimal"))]` 줄을 짚는다 — rustc 가 「있었는데 cfg 로 빠졌다」까지 알려 준다.

### 3. ★★ `a=false` · `a=true` · 워크스페이스 빌드 뒤 app1 은 **`a=true`**

**출력**

```text
===== 소스: r46_default.sh =====
# gear 의 기본 feature 는 a. app1 은 default-features = false, app2 는 아무것도 안 적는다
mkdir -p ws/gear/src ws/app1/src ws/app2/src
printf '[workspace]\nmembers = ["gear", "app1", "app2"]\nresolver = "2"\n' > ws/Cargo.toml
cat > ws/gear/Cargo.toml <<'TOML'
[package]
name = "gear"
version = "0.1.0"
edition = "2021"

[features]
default = ["a"]
a = []
TOML
printf 'pub fn report() -> String {\n    format!("a={}", cfg!(feature = "a"))\n}\n' > ws/gear/src/lib.rs
printf '[package]\nname = "app1"\nversion = "0.1.0"\nedition = "2021"\n\n[dependencies]\ngear = { path = "../gear", default-features = false }\n' > ws/app1/Cargo.toml
printf '[package]\nname = "app2"\nversion = "0.1.0"\nedition = "2021"\n\n[dependencies]\ngear = { path = "../gear" }\n' > ws/app2/Cargo.toml
for n in 1 2; do printf 'fn main() {\n    println!("{}", gear::report());\n}\n' > "ws/app$n/src/main.rs"; done
===== bash r46_default.sh =====
(exit 0)
===== cd ws && cargo run -q -p app1 =====
a=false
(exit 0)
===== cd ws && cargo run -q -p app2 =====
a=true
(exit 0)
===== cd ws && cargo build -q --workspace =====
(exit 0)
===== ws/target/debug/app1 =====
a=true
(exit 0)
```

**왜 그런가**

- ★★ **`default-features = false` 는 「나는 기본 feature 를 요청하지 않는다」이지 「꺼라」가 아니다.** 혼자 빌드하면 꺼져 있고(`a=false`), app2 와 함께면 app2 가 **기본(`default` → `a`)** 을 요청하므로 합집합에서 켜진다.
- ★ 1번과 같은 규칙의 다른 얼굴이다 — **feature 요청에는 「켜 달라」만 있고 「끄라」가 없다.**

### 4. ★★★ resolver 2 — 빌드 스크립트 `a=false b=true` · 본체 `a=true b=false` / resolver 1 — **둘 다 `a=true b=true`**

**출력**

```text
===== 소스: r46_resolver.sh =====
# app1 이 gear 를 두 번 쓴다 — 일반 의존성으로는 feature a, 빌드 스크립트(build.rs)의 의존성으로는 feature b
mkdir -p ws/gear/src ws/app1/src
printf '[workspace]\nmembers = ["gear", "app1"]\nresolver = "2"\n' > ws/Cargo.toml
printf '[package]\nname = "gear"\nversion = "0.1.0"\nedition = "2021"\n\n[features]\na = []\nb = []\n' > ws/gear/Cargo.toml
printf 'pub fn report() -> String {\n    format!("a={} b={}", cfg!(feature = "a"), cfg!(feature = "b"))\n}\n' > ws/gear/src/lib.rs
cat > ws/app1/Cargo.toml <<'TOML'
[package]
name = "app1"
version = "0.1.0"
edition = "2021"

[dependencies]
gear = { path = "../gear", features = ["a"] }

[build-dependencies]
gear = { path = "../gear", features = ["b"] }
TOML
printf 'fn main() {\n    println!("cargo:warning=build script sees {}", gear::report());\n}\n' > ws/app1/build.rs
printf 'fn main() {\n    println!("binary sees {}", gear::report());\n}\n' > ws/app1/src/main.rs
===== bash r46_resolver.sh =====
(exit 0)
===== cd ws && cargo build -p app1 2>&1 >/dev/null | sed "s|$PWD|.|g" =====
   Compiling gear v0.1.0 (./ws/gear)
   Compiling app1 v0.1.0 (./ws/app1)
warning: app1@0.1.0: build script sees a=false b=true
    Finished `dev` profile [unoptimized + debuginfo] target(s) in 0.24s
(exit 0)
===== ws/target/debug/app1 =====
binary sees a=true b=false
(exit 0)
===== sed -i "s/^resolver = \"2\"/resolver = \"1\"/" ws/Cargo.toml =====
(exit 0)
===== cd ws && cargo build -p app1 2>&1 >/dev/null | sed "s|$PWD|.|g" =====
   Compiling gear v0.1.0 (./ws/gear)
   Compiling app1 v0.1.0 (./ws/app1)
warning: app1@0.1.0: build script sees a=true b=true
    Finished `dev` profile [unoptimized + debuginfo] target(s) in 0.21s
(exit 0)
===== ws/target/debug/app1 =====
binary sees a=true b=true
(exit 0)
```

**왜 그런가**

- ★★★ **resolver 2 는 빌드 의존성(`[build-dependencies]`)과 일반 의존성의 feature 를 합치지 않는다** — gear 를 **두 벌** 빌드해 빌드 스크립트는 `b` 만, 본체는 `a` 만 본다.
- ★★★ **resolver 1 은 둘을 합친다** — 한 벌에 `a`+`b` 가 켜져 빌드 스크립트와 본체가 **같은 것**을 본다. 빌드 스크립트용으로 켠 feature 가 **실행 파일로 샌다.**
- ★ cargo 문서 — resolver 2 가 합치지 않는 자리는 셋이다: ① 지금 빌드하지 않는 플랫폼 전용 의존성 · ② **빌드 의존성·proc-macro 대 일반 의존성** · ③ 테스트·예제를 빌드하지 않을 때의 dev-의존성. **이 블록은 ②만 쟀다.**

### 5. ★★ `"0.2"` 는 경로 의존성에서도 **판 선택 실패** · 고친 뒤 `req` 는 app1 `^0.1.0` · app2 `*`

**출력**

```text
===== 소스: r46_version.sh =====
# 경로 의존성에 version 도 적는다 — gear 는 0.1.0 인데 app1 은 "0.2" 를 요구한다. app2 는 version 을 안 적는다
mkdir -p ws/gear/src ws/app1/src ws/app2/src
printf '[workspace]\nmembers = ["gear", "app1", "app2"]\nresolver = "2"\n' > ws/Cargo.toml
printf '[package]\nname = "gear"\nversion = "0.1.0"\nedition = "2021"\n' > ws/gear/Cargo.toml
printf 'pub fn v() -> &%sstatic str {\n    env!("CARGO_PKG_VERSION")\n}\n' "'" > ws/gear/src/lib.rs
printf '[package]\nname = "app1"\nversion = "0.1.0"\nedition = "2021"\n\n[dependencies]\ngear = { path = "../gear", version = "0.2" }\n' > ws/app1/Cargo.toml
printf '[package]\nname = "app2"\nversion = "0.1.0"\nedition = "2021"\n\n[dependencies]\ngear = { path = "../gear" }\n' > ws/app2/Cargo.toml
for n in 1 2; do printf 'fn main() {\n    println!("gear {}", gear::v());\n}\n' > "ws/app$n/src/main.rs"; done
===== bash r46_version.sh =====
(exit 0)
===== cd ws && cargo build -q -p app1 2>&1 >/dev/null | sed "s|$PWD|.|g" =====
error: failed to select a version for the requirement `gear = "^0.2"`
candidate versions found which didn't match: 0.1.0
location searched: ./ws/gear
required by package `app1 v0.1.0 (./ws/app1)`
As a reminder, you're using offline mode (--offline) which can sometimes cause surprising resolution failures, if this error is too confusing you may wish to retry without `--offline`.
(exit 101)
===== sed -i "s/version = \"0.2\"/version = \"0.1.0\"/" ws/app1/Cargo.toml =====
(exit 0)
===== cd ws && cargo build -q -p app1 =====
(exit 0)
===== cd ws && cargo metadata -q --format-version 1 --no-deps | python3 -c 'import json,sys; [print(p["name"], p["version"], [(d["name"], d["req"]) for d in p["dependencies"]]) for p in json.load(sys.stdin)["packages"]]' =====
gear 0.1.0 []
app1 0.1.0 [('gear', '^0.1.0')]
app2 0.1.0 [('gear', '*')]
(exit 0)
```

**왜 그런가**

- ★★★ **`path` 가 있어도 `version` 을 적으면 cargo 는 그 요구를 검사한다** — `` failed to select a version for the requirement `gear = "^0.2"` `` · `candidate versions found which didn't match: 0.1.0`. 경로 의존성은 「판 번호를 무시하는 지름길」이 아니다.
- ★★★ **`version = "0.1.0"` 은 `^0.1.0`** 으로 기록된다 — cargo 의 기본 요구는 **캐럿**이다(문서: 「가장 왼쪽의 0 아닌 자리가 같으면 호환」 — 그래서 `^0.1.0` 은 `0.1.x` 만, `^1.2.3` 은 `2.0.0` 미만).
- ★★ **`version` 을 안 적은 경로 의존성은 `*`** — 아무 판이나 받는다.
- ★ 마지막 줄 `As a reminder, you're using offline mode (--offline) …` 은 **이 캡처가 `CARGO_NET_OFFLINE=true` 로 돌았기 때문에** 붙은 줄이다 — 네트워크를 켠 판에서는 이 줄이 없을 수 있다(켠 판은 재지 않았다).

### 6. ★★ `a=true b=false` · `a=true b=true` · app3 은 `a=true b=false` + **「`default-features` is ignored」** 경고

**출력**

```text
===== 소스: r46_inherit.sh =====
# 워크스페이스 루트가 의존성을 한 번 적고([workspace.dependencies]), 멤버가 workspace = true 로 물려받는다
mkdir -p ws/gear/src ws/app1/src ws/app2/src ws/app3/src
cat > ws/Cargo.toml <<'TOML'
[workspace]
members = ["gear", "app1", "app2", "app3"]
resolver = "2"

[workspace.dependencies]
gear = { path = "gear", features = ["a"] }
TOML
printf '[package]\nname = "gear"\nversion = "0.1.0"\nedition = "2021"\n\n[features]\na = []\nb = []\n' > ws/gear/Cargo.toml
printf 'pub fn report() -> String {\n    format!("a={} b={}", cfg!(feature = "a"), cfg!(feature = "b"))\n}\n' > ws/gear/src/lib.rs
printf '[package]\nname = "app1"\nversion = "0.1.0"\nedition = "2021"\n\n[dependencies]\ngear = { workspace = true }\n' > ws/app1/Cargo.toml
printf '[package]\nname = "app2"\nversion = "0.1.0"\nedition = "2021"\n\n[dependencies]\ngear = { workspace = true, features = ["b"] }\n' > ws/app2/Cargo.toml
printf '[package]\nname = "app3"\nversion = "0.1.0"\nedition = "2021"\n\n[dependencies]\ngear = { workspace = true, default-features = false }\n' > ws/app3/Cargo.toml
for n in 1 2 3; do printf 'fn main() {\n    println!("{}", gear::report());\n}\n' > "ws/app$n/src/main.rs"; done
===== bash r46_inherit.sh =====
(exit 0)
===== cd ws && cargo run -q -p app1 =====
a=true b=false
(exit 0)
===== cd ws && cargo run -q -p app2 =====
a=true b=true
(exit 0)
===== cd ws && cargo run -p app3 2>/dev/null | sed "s|$PWD|.|g" =====
a=true b=false
===== cd ws && cargo run -p app3 2>&1 >/dev/null | sed "s|$PWD|.|g" =====
warning: ./ws/app3/Cargo.toml: `default-features` is ignored for gear, since `default-features` was not specified for `workspace.dependencies.gear`, this could become a hard error in the future
   Compiling app3 v0.1.0 (./ws/app3)
    Finished `dev` profile [unoptimized + debuginfo] target(s) in 0.09s
     Running `target/debug/app3`
(exit 0)
```

**왜 그런가**

- ★★ **`workspace = true` 는 루트의 `[workspace.dependencies]` 한 줄(경로·feature `a`)을 그대로 물려받는다**(app1).
- ★★ **멤버가 `features = ["b"]` 를 더하면 합쳐진다** — 루트의 `a` 에 `b` 가 **더해졌다**(app2). 물려받은 feature 를 **뺄 수는 없다.**
- ★★★ **`default-features = false` 는 무시됐다** — 루트가 `default-features` 를 안 적었기 때문이라고 경고가 말하고, `this could become a hard error in the future` 라고 덧붙인다. 멤버에서 기본 feature 를 끄려면 **루트에 `default-features = false` 를 적어야 한다.**
- ★ 이 경고는 `-q` 로 돌리면 **안 보인다** — app1·app2 는 `-q`, app3 은 일부러 `-q` 없이 돌렸다.

### 7. ★★★ 「합집합이다」 — 그래서 feature 는 기능을 **더하기만** 해야 하고, 배타적이면 `compile_error!` 로 막는다

- ★★★ **한 빌드에서 한 크레이트는 한 벌만 빌드되고, 그 벌의 feature 는 요청들의 합집합이다**(1·3번). 누가 무엇을 켰는지 모르는 채 합쳐지므로 **어떤 조합이든 동시에 켜져도 깨지지 않아야** 한다 — 2번이 그 반례다.
- ★★ **「끄는 feature」는 「켜는 feature」로 뒤집는다** — cargo 문서: 「`no_std` 를 지원하려면 `no_std` feature 를 쓰지 말고 **`std` 를 켜는 `std` feature** 를 써라」. 그래야 누가 `std` 를 켜면 **기능이 늘기만** 한다(흔히 그 `std` 를 기본 feature 에 넣고, 필요 없는 쪽이 `default-features = false` 로 요청을 뺀다 — 3번).
- ★ cargo 문서 — 배타적 feature 는 **가능하면 피하고**, 불가피하면 `#[cfg(all(feature = "foo", feature = "bar"))] compile_error!(…)` 로 **동시 활성화를 빌드 에러로** 만들라고 권한다. 조용히 한쪽이 이기는 것보다 낫다.

### 8. ★★ `resolver = "1"` 로 떨어지며 경고 — 2024 멤버면 「implies `resolver = "3"`」 · resolver 는 **워크스페이스 전체에 하나**

```text
===== 소스: r46_resolver.sh =====
# app1 이 gear 를 두 번 쓴다 — 일반 의존성으로는 feature a, 빌드 스크립트(build.rs)의 의존성으로는 feature b
mkdir -p ws/gear/src ws/app1/src
printf '[workspace]\nmembers = ["gear", "app1"]\nresolver = "2"\n' > ws/Cargo.toml
printf '[package]\nname = "gear"\nversion = "0.1.0"\nedition = "2021"\n\n[features]\na = []\nb = []\n' > ws/gear/Cargo.toml
printf 'pub fn report() -> String {\n    format!("a={} b={}", cfg!(feature = "a"), cfg!(feature = "b"))\n}\n' > ws/gear/src/lib.rs
cat > ws/app1/Cargo.toml <<'TOML'
[package]
name = "app1"
version = "0.1.0"
edition = "2021"

[dependencies]
gear = { path = "../gear", features = ["a"] }

[build-dependencies]
gear = { path = "../gear", features = ["b"] }
TOML
printf 'fn main() {\n    println!("cargo:warning=build script sees {}", gear::report());\n}\n' > ws/app1/build.rs
printf 'fn main() {\n    println!("binary sees {}", gear::report());\n}\n' > ws/app1/src/main.rs
===== bash r46_resolver.sh =====
(exit 0)
===== sed -i "/^resolver/d" ws/Cargo.toml =====
(exit 0)
===== cd ws && cargo build -p app1 2>&1 >/dev/null | sed "s|$PWD|.|g" =====
warning: virtual workspace defaulting to `resolver = "1"` despite one or more workspace members being on edition 2021 which implies `resolver = "2"`
  |
  = note: to keep the current resolver, specify `workspace.resolver = "1"` in the workspace root's manifest
  = note: to use the edition 2021 resolver, specify `workspace.resolver = "2"` in the workspace root's manifest
  = note: for more details see https://doc.rust-lang.org/cargo/reference/resolver.html#resolver-versions
   Compiling gear v0.1.0 (./ws/gear)
   Compiling app1 v0.1.0 (./ws/app1)
warning: app1@0.1.0: build script sees a=true b=true
    Finished `dev` profile [unoptimized + debuginfo] target(s) in 0.26s
(exit 0)
===== ws/target/debug/app1 =====
binary sees a=true b=true
(exit 0)
===== sed -i "s/edition = \"2021\"/edition = \"2024\"/" ws/*/Cargo.toml =====
(exit 0)
===== cd ws && cargo build -p app1 2>&1 >/dev/null | sed "s|$PWD|.|g" =====
warning: virtual workspace defaulting to `resolver = "1"` despite one or more workspace members being on edition 2024 which implies `resolver = "3"`
  |
  = note: to keep the current resolver, specify `workspace.resolver = "1"` in the workspace root's manifest
  = note: to use the edition 2024 resolver, specify `workspace.resolver = "3"` in the workspace root's manifest
  = note: for more details see https://doc.rust-lang.org/cargo/reference/resolver.html#resolver-versions
   Compiling gear v0.1.0 (./ws/gear)
   Compiling app1 v0.1.0 (./ws/app1)
warning: app1@0.1.0: build script sees a=true b=true
    Finished `dev` profile [unoptimized + debuginfo] target(s) in 0.22s
(exit 0)
```

- ★★★ **가상 워크스페이스(루트에 `[package]` 가 없는 것)는 `resolver` 를 안 적으면 1 이다** — 멤버가 2021 이어도. 경고가 「멤버가 2021 이라 2 를 뜻하는데 1 로 떨어진다」고 말하고, 빌드 스크립트가 다시 `a=true b=true` 를 본다(4번의 resolver 1 과 같다).
- ★★ 멤버를 2024 로 올리면 **「implies `resolver = "3"`」** 로 바뀐다 — 2024 에디션의 기본은 3 이다(cargo 문서: 3 은 `rust-version` 과 맞지 않는 판을 고르는 기본값을 바꾼다 — **이 블록은 3 의 동작을 재지 않았다**).
- ★ cargo 문서 — 「resolver 는 **워크스페이스 전체에 걸리는 전역 옵션**이고 의존성 쪽에 적힌 값은 무시된다. 가상 워크스페이스면 `[workspace]` 에 적는다」. 멤버마다 다르게 줄 수 **없다.**

### 9. ★★ 처음엔 둘 다 없음 → 멤버 디렉토리에서 빌드해도 **워크스페이스 루트**에 생긴다

```text
===== 소스: r46_ws.sh =====
# 워크스페이스 ws — 라이브러리 gear(feature a·b) 하나를 앱 둘이 각자 다른 feature 로 쓴다
mkdir -p ws/gear/src ws/app1/src ws/app2/src
cat > ws/Cargo.toml <<'TOML'
[workspace]
members = ["gear", "app1", "app2"]
resolver = "2"
TOML
cat > ws/gear/Cargo.toml <<'TOML'
[package]
name = "gear"
version = "0.1.0"
edition = "2021"

[features]
a = []
b = []
TOML
cat > ws/gear/src/lib.rs <<'RS'
pub fn report() -> String {
    format!("a={} b={}", cfg!(feature = "a"), cfg!(feature = "b"))
}
RS
for n in 1 2; do
  feat=$([ "$n" = 1 ] && echo a || echo b)
  cat > "ws/app$n/Cargo.toml" <<TOML
[package]
name = "app$n"
version = "0.1.0"
edition = "2021"

[dependencies]
gear = { path = "../gear", features = ["$feat"] }
TOML
  printf 'fn main() {\n    println!("{}", gear::report());\n}\n' > "ws/app$n/src/main.rs"
done
===== bash r46_ws.sh =====
(exit 0)
===== ls ws ws/app1 =====
ws:
Cargo.toml
app1
app2
gear

ws/app1:
Cargo.toml
src
(exit 0)
===== cd ws/app1 && cargo build -q =====
(exit 0)
===== ls ws ws/app1 =====
ws:
Cargo.lock
Cargo.toml
app1
app2
gear
target

ws/app1:
Cargo.toml
src
(exit 0)
```

- ★★★ **`cd ws/app1` 에서 빌드했는데 `Cargo.lock` 과 `target/` 이 `ws/` 에 생기고 `ws/app1/` 에는 없다** — cargo 는 위로 올라가며 **워크스페이스 루트를 찾아** 거기서 잠금 파일과 출력 디렉토리를 공유한다(cargo 문서: 「모든 패키지가 루트의 `Cargo.lock` 하나와 `target` 하나를 공유한다」).
- ★ 그래서 1번에서 app1 과 app2 가 **같은 `ws/target/debug/`** 에 실행 파일을 두었고, 같은 gear 빌드를 나눠 썼다.

### 10. ★★ Go `v1.1.0` · Cargo `1.3.0` — Cargo 는 선택이 **시간(레지스트리 상태)** 에 달려 `Cargo.lock` 이 필요하다

- ★★ [Go 41번](../../../go/syntax/41-modules-go-mod-version-selection-and-workspaces/) (8) — `a 1.1.0 → c "1.1.0"`, `b 1.0.0 → c "1.0.0"`, 레지스트리에 `c 1.0.0`\~`1.3.0` 인 그래프에서 **Go 는 요구의 최댓값 `v1.1.0`, Cargo 는 `^1.1.0` 범위의 최신 `1.3.0`** 을 골랐다(그 편은 **로컬 디렉토리 레지스트리**로 쟀다).
- ★★★ Cargo 의 답은 **레지스트리에 새 판이 올라오면 바뀐다** — 그래서 고른 판을 `Cargo.lock` 에 적어 고정한다. Go 는 선택이 요구만의 함수라 `go.mod` 로 재현된다.
- ★ 5번의 `req = "^0.1.0"` 이 그 「범위」다. **이 편은 레지스트리를 쓰지 않았으므로 「범위 안의 최신」을 직접 재지 않았다** — 경로 의존성은 후보가 하나(그 경로의 판)뿐이다. **못 잰 것**이고, 잰 곳은 Go 41번이다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서·서머리의 **모든 블록** | `capture.sh` — 블록마다 명령을 배너에 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` 기본 규칙 넷(시간 칸이 걸린다) · **고칠 것 0** |
| ★★★ **feature 통합** | `r46_unify` · `r46_tree` | 6 + 2 | `-p app1` → `b=false` · `--workspace` → **`b=true`** |
| 끄는 feature | `r46_neg` | 3 | 통과 · 통과 · **E0425(app1)** |
| `default-features = false` | `r46_default` · `r46_inherit`(app3) | 4 · 3 | 혼자 `a=false` · 함께 **`a=true`** · 상속에서는 **무시 + 경고** |
| ★★ **resolver 1 대 2** | `r46_resolver` · `r46_noresolver` | 2 × 2 · 2 | 2 → 빌드 스크립트 `b` 만 · 1 → **합쳐짐** · 미기재 → 1 + 경고 |
| 판 요구 | `r46_version` | 3 | `^0.2` 실패 · `^0.1.0` · `*` |
| 공유 잠금·출력 | `r46_lock` | 2 | 루트에만 생김 |
| ★ **못 잰 것** — 레지스트리의 「범위 안의 최신」 | 네트워크 금지 · 경로 의존성은 후보가 하나 | 0 | ★ [Go 41번](../../../go/syntax/41-modules-go-mod-version-selection-and-workspaces/) (8)이 디렉토리 레지스트리로 잰 것을 인용 |
| **안 던진 것** — resolver 3 의 `rust-version` 판 선택 · dev-의존성 · 플랫폼 전용 의존성 · `--features` 명령행 · `[patch]` | — | 0 | ★ 「안 던졌다」로 표시했다 |

**구현 의존 항목**(버전·환경이 바뀌면 **다시 찍어야 하는** 것).

| 항목 | 왜 |
|---|---|
| feature 통합 · resolver 동작 · 경고 문구 | ★ **cargo 의 규칙**(이 머신 `cargo 1.92.0`) — 언어(rustc)가 아니다 |
| `default-features` 무시 경고(「hard error 가 될 수 있다」) | ★ cargo 판에 매인다 |
| offline 안내 줄 | ★ 이 캡처의 환경(`CARGO_NET_OFFLINE`) |

★ **다시 찍는 법** — `capture.sh <새 디렉토리>` 를 그대로 돌리고 `normalize-shaky.py <원본> <새 디렉토리>` 로 견준다.
