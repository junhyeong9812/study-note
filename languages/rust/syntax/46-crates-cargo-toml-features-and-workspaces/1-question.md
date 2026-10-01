# rust/syntax/46 — 크레이트 · `Cargo.toml` · feature · 워크스페이스 — 질문

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 같은 실행 파일을 세 번 (예측)

```bash
# r46_ws.sh
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
```

- 스크립트 뒤에 `cd ws && cargo run -q -p app1` → `cd ws && cargo build -q --workspace` → `ws/target/debug/app1` → `ws/target/debug/app2` → 다시 `cd ws && cargo run -q -p app1` 를 친다. 네 번의 출력(`a=… b=…`)은?

### 2. ★★★ 켜면 사라지는 함수 (예측)

```bash
# r46_neg.sh
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
```

- `cargo run -q -p app1` · `cargo run -q -p app2` · `cargo build -q --workspace` 를 차례로 친다(전부 `ws/` 에서). 각각 통과하나? 막힌다면 무슨 번호가 **어느 패키지**에서 나나?

### 3. ★★ 기본 feature 를 끈 쪽과 안 끈 쪽 (예측)

```bash
# r46_default.sh
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
```

- `cargo run -q -p app1` · `cargo run -q -p app2` · `cargo build -q --workspace` 뒤 `ws/target/debug/app1` 의 출력은?

### 4. ★★★ 빌드 스크립트의 의존성과 본체의 의존성 (예측)

```bash
# r46_resolver.sh
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
```

- `cd ws && cargo build -p app1` 이 표준 오류에 내는 `build script sees …` 줄과 `ws/target/debug/app1` 의 출력은? 루트의 `resolver = "2"` 를 `"1"` 로 바꾸고 같은 두 명령을 치면?

### 5. ★★ 경로 의존성에 적은 판 번호 (예측)

```bash
# r46_version.sh
# 경로 의존성에 version 도 적는다 — gear 는 0.1.0 인데 app1 은 "0.2" 를 요구한다. app2 는 version 을 안 적는다
mkdir -p ws/gear/src ws/app1/src ws/app2/src
printf '[workspace]\nmembers = ["gear", "app1", "app2"]\nresolver = "2"\n' > ws/Cargo.toml
printf '[package]\nname = "gear"\nversion = "0.1.0"\nedition = "2021"\n' > ws/gear/Cargo.toml
printf 'pub fn v() -> &%sstatic str {\n    env!("CARGO_PKG_VERSION")\n}\n' "'" > ws/gear/src/lib.rs
printf '[package]\nname = "app1"\nversion = "0.1.0"\nedition = "2021"\n\n[dependencies]\ngear = { path = "../gear", version = "0.2" }\n' > ws/app1/Cargo.toml
printf '[package]\nname = "app2"\nversion = "0.1.0"\nedition = "2021"\n\n[dependencies]\ngear = { path = "../gear" }\n' > ws/app2/Cargo.toml
for n in 1 2; do printf 'fn main() {\n    println!("gear {}", gear::v());\n}\n' > "ws/app$n/src/main.rs"; done
```

- `cargo build -q -p app1` 은 통과하나? 그다음 app1 의 `version = "0.2"` 를 `"0.1.0"` 으로 고치고 다시 빌드한 뒤 `cargo metadata` 로 두 앱의 요구(`req`)를 찍으면 각각 무엇인가?

### 6. ★★ 루트에 한 번 적은 의존성 (예측)

```bash
# r46_inherit.sh
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
```

- `cargo run -q -p app1` · `cargo run -q -p app2` · `cargo run -p app3` 의 출력은? app3 의 `default-features = false` 는 무엇을 하나?

### 7. ★★★ feature 는 왜 「더하기」여야 하나 (왜)

- 1\~3번에서 cargo 가 feature 를 합친 방식을 한 문장으로 말하라. 2번 같은 「끄는 feature」 대신 같은 목적을 무엇으로 설계해야 하나(예: `no_std` 지원)? cargo 문서는 배타적인 feature 가 **불가피할 때** 무엇을 권하나?

### 8. ★★ `resolver` 를 안 적은 워크스페이스 (경계)

- 4번 스크립트에서 `resolver` 줄을 **지우고** 빌드하면 cargo 는 몇 번 resolver 를 쓰고 무엇을 경고하나? 멤버의 `edition` 을 `"2024"` 로 올리면 경고가 무엇으로 바뀌나? 멤버마다 resolver 를 다르게 줄 수 있나?

### 9. ★★ 잠금 파일과 `target/` 은 어디에 (경계)

- 1번 스크립트로 워크스페이스를 만든 직후 `ls ws ws/app1` 은? `cd ws/app1 && cargo build -q` 뒤에는 `Cargo.lock` 과 `target/` 이 **어느 디렉토리**에 생기나?

### 10. ★★ 「요구의 최댓값」과 「범위 안의 최신」 (연결)

- Go 는 최소 판 선택(MVS)으로 판을 고르고 Cargo 는 캐럿 요구 범위에서 고른다. [Go 41번](../../../go/syntax/41-modules-go-mod-version-selection-and-workspaces/) (8)이 같은 요구 그래프에서 두 도구가 고른 판을 쟀다 — 각각 무엇이었고, 그 차이가 **`Cargo.lock` 의 필요**를 어떻게 설명하나? 5번의 `req` 와는 어떻게 이어지나?

## 실행 환경

★ 던지는 법 — 각 소스는 **워크스페이스 `ws/` 를 만드는 셸 스크립트**다(`bash <파일>.sh`). 그 뒤 질문에 적힌 명령을 **그 순서대로** 친다. cargo 는 `CARGO_NET_OFFLINE=true` 로 돌렸다 — **의존성은 전부 로컬 경로(`path = …`)이고 레지스트리(crates.io)에 가지 않는다.**
★★★ **feature 를 보면 먼저 물어라** — 「**이번 빌드에 함께 선택된 패키지는 누구인가**」.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
