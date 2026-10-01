# rust/syntax/46 — 크레이트 · `Cargo.toml` · feature · 워크스페이스 — 정리 (힌트)

★★★ **본체 창 — ⑤ cargo 가 고른 feature 를 「실행 파일이 스스로 말하게」 하는 창**(`cfg!(feature = "…")` 를 찍는 라이브러리 + `cargo tree -e features`)이다. feature 통합은 컴파일러가 아니라 **cargo 가 rustc 에 넘기는 `--cfg` 의 차이**라 소스·진단 어디에도 안 보이고, **만들어진 바이너리의 동작으로만** 보인다.

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| ★★ **흔들린다(정규화)** | `Finished … target(s) in 0.28s` 의 **시간** | 실행마다 바뀐다 — 기본 규칙이 `<time>s` 로 바꾼다 |
| 안 흔들린다 | ★★★ **실행 파일이 찍는 `a=… b=…` · `build script sees …` 줄** | 같은 cargo 판·같은 명령 순서에서 고정이다 — **이 주제의 본체** |
| 안 흔들린다 | `cargo tree` 의 모양 · E0425 · 판 선택 실패 문구 · `req` · 종료 코드(`101`) | 같은 판에서 고정이다 |
| ★ **환경이 정한다** | `As a reminder, you're using offline mode …` 줄 | ★ 이 캡처가 `CARGO_NET_OFFLINE=true` 로 돌았기 때문이다 |
| ★ **캡처가 바꾼 칸** | cargo 가 찍는 절대 경로 → `./` | 배너의 `sed "s\|$PWD\|.\|g"` 가 바꿨다(두 스트림 각각) |

★ 정규화 규칙은 **기본 넷**만 쓴다(시간 칸이 걸린다). ★ **명령 순서가 결과를 바꾼다**((1)) — 블록은 적힌 순서 그대로 돌렸다.

## 한눈에 — 쉽게 말하면

**feature 는 「공동 주문서의 옵션 칸」이다.** 한 식당(워크스페이스)에서 여러 손님이 같은 요리(gear)를 시키면 주방은 **한 접시만** 만들고,
각자 적은 옵션을 **전부 얹는다** — 누구는 치즈(a), 누구는 양파(b)를 적었으면 모두의 접시에 치즈와 양파가 올라간다.
그래서 옵션은 **「더하기」만** 있어야 한다. 「양파 빼 주세요」(끄는 feature)를 적으면, 양파가 들어가야 맛이 나는 다른 손님의 요리가 망가진다.

| 비유 | 실체 |
|---|---|
| 「**한 접시에 모두의 옵션**」 | ★★★ **함께 빌드한 패키지들이 켠 feature 의 합집합**으로 gear 가 한 번 빌드된다((1)) |
| 「**혼자 시키면 내 옵션만**」 | ★★★ **`-p app1` 만 고르면 app1 의 feature 만** — 같은 실행 파일이 무엇과 함께 빌드됐나에 따라 다르게 동작한다((1)) |
| 「**양파 빼 주세요**」 | ★★ **끄는 feature** — 혼자는 통과, 함께면 **요청하지 않은 쪽**이 E0425((2)) |
| 「**기본 옵션은 사양합니다**」 | ★★ **`default-features = false`** — 「요청 안 함」이지 「끔」이 아니다. 누가 기본을 요청하면 켜진다((3)) |
| 「**포장 주문은 따로 조리**」 | ★★★ **resolver 2** — 빌드 스크립트용 의존성은 **따로 빌드**되어 feature 가 안 섞인다. resolver 1 은 섞는다((4)) |
| 「**공용 주방·공용 장부**」 | ★★ **워크스페이스는 `target/` 과 `Cargo.lock` 을 루트에 하나** 둔다((5)) |

```text
   (1)을 한 장으로 — gear 는 한 벌만 빌드된다

   cargo run -p app1                cargo build --workspace
   ─────────────────                ─────────────────────────
   app1 ── a ──▶ gear[a]            app1 ── a ──┐
                                                ├──▶ gear[a,b] ◀── app1 도 이 벌에 링크
                                    app2 ── b ──┘
   app1 → "a=true b=false"          app1 → "a=true b=true"   ← app1 은 b 를 요청한 적이 없다
```

> **feature** — 크레이트가 `[features]` 에 선언하는 **조건부 컴파일 스위치**. 켜지면 cargo 가 rustc 에 `--cfg feature="이름"` 을 넘긴다.\
> 예: `#[cfg(feature = "std")]` 가 붙은 함수는 `std` feature 가 켜졌을 때만 있다.

> **feature 통합(feature unification)** — 한 빌드에서 한 크레이트는 한 벌만 빌드되고, 그 벌의 feature 는 **그 크레이트에 대한 요청들의 합집합**이 되는 것.\
> 예: app1 이 `a`, app2 가 `b` 를 켜고 둘을 함께 빌드하면 gear 는 `a`+`b` 로 한 번 빌드된다.

## 이 주제가 답하려는 질문

1. ★★★ **feature 는 왜 가산적이어야 하나 — 통합은 어느 범위에서 일어나나**((1)·(2)·(3)).
2. ★★ **resolver 1·2·3 은 무엇이 다른가 — 안 적으면 몇 번인가**((4)).
3. ★★ **워크스페이스는 무엇을 공유하고, 의존성 요구는 어떻게 읽히나**((5)·(6)).

★ **선행** — [**45번 주제**](../45-module-system-mod-use-pub-crate-and-file-layout/) — 모듈·가시성은 **rustc** 의 일이었다(cargo 없이 전부 재현). 이 편은 크레이트를 **묶는 쪽(cargo)** 이다.
★★★ **이미 잰 것 — 다시 재지 않고 인용한다.**
[01번](../01-cargo-crates-and-modules/) — **`Cargo.lock` 은 첫 빌드에서 생기고 의존성이 0개여도 자기 자신이 들어간다** · `cargo build -v` 가 rustc 에게 넘기는 것 · 한 패키지의 `lib.rs`/`main.rs` 는 다른 크레이트.
[Go 41번](../../../go/syntax/41-modules-go-mod-version-selection-and-workspaces/) (8) — **레지스트리가 있을 때 Cargo 는 캐럿 범위의 최신(`1.3.0`), Go 는 요구의 최댓값(`v1.1.0`)** — 로컬 디렉토리 레지스트리로 쟀다.
이 편은 그 위에 **feature 통합의 범위**, **끄는 feature 가 깨지는 자리**, **resolver 1 대 2**, **경로 의존성의 판 요구**, **워크스페이스 상속**을 더한다.

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ⑤ 「바이너리가 스스로 말하는」 feature 로그다

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ⑤ ★★★ **`cfg!(feature = …)` 를 찍는 라이브러리** + 빌드 스크립트의 `cargo:warning=` | 그 빌드에서 gear 가 **실제로 어떤 feature 로** 컴파일됐나 | ★ **본체**((1)·(3)·(4)) |
| ⑥ ★★ **`cargo tree -e features`** | 누가 어떤 feature 를 **요청했나**(그래프) | 쓴다((1)) — ★ 요청의 그래프이지 **빌드된 벌**이 아니다 |
| ② ★★ **컴파일러 진단** | 합쳐진 벌에서 **무엇이 사라졌나**(E0425 + `configured out`) | 쓴다((2)) |
| ⑦ ★ **`cargo metadata`** | 요구 문자열이 **무엇으로 기록됐나**(`^0.1.0`·`*`) | 쓴다((6)) |
| 레지스트리의 판 선택(「범위 안의 최신」) | — | ★ **못 잰 것** — 네트워크 금지 · 경로 의존성은 후보가 하나뿐. [Go 41번](../../../go/syntax/41-modules-go-mod-version-selection-and-workspaces/) (8)을 인용 |
| 실행 시간 · 바이너리 크기 | — | ★ **부적용** — feature 는 무엇이 **컴파일되나**를 바꾸는 것이라, 이 주제의 질문에는 시간이 답하지 않는다 |

★★ **제5의 상태 — 「같은 질문을 다른 창으로」.** 「gear 는 어떤 feature 로 빌드됐나」를 ⑥ `cargo tree` 로만 물으면 **요청의 그래프**가 나올 뿐, 그 요청들이 **한 벌로 합쳐졌다는 사실**은 안 보인다(트리의 `-p app1` 은 `a` 만 보여 주고, `--workspace` 트리는 요청자별로 갈라 보여 준다). 그래서 **바이너리에게 직접 물었다**(⑤) — `ws/target/debug/app1` 이 `b=true` 를 답한 것이 합쳐졌다는 증거다.

### (1) ★★★ feature 통합 — 같은 실행 파일을 세 번

**언제 쓰나** — 한 워크스페이스(또는 한 의존성 그래프)에서 두 패키지가 같은 라이브러리를 **다른 feature 로** 쓸 때마다.

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

- ★★★ **`-p app1` → `a=true b=false` · `--workspace` 뒤 app1 → `a=true b=true`** — app1 은 `b` 를 요청한 적이 없다. **함께 선택된 app2 의 요청이 app1 의 실행 파일에 들어갔다.**
- ★★★ **마지막 `-p app1` → 다시 `b=false`** — 통합의 범위는 **「이번 명령이 선택한 패키지들」** 이다. 그래서 **같은 경로의 같은 실행 파일이 「마지막에 무엇과 함께 빌드됐나」에 따라 동작이 다르다.**
- ★ cargo 문서의 표현 — 「foo 가 `std`·`winnt` 를, bar 가 다른 둘을 켜면 winapi 는 **넷 다 켜진 채** 빌드된다. **그래서 feature 는 가산적이어야 한다.**」

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

- ★★ `cargo tree -e features --workspace -i gear` 가 **요청자별**로 보여 준다 — `a` ← app1 · `b` ← app2.

### (2) ★★★ 「끄는 feature」가 깨지는 자리 — 요청하지 않은 쪽이 깨진다

**언제 쓰나** — `#[cfg(not(feature = "…"))]` 를 쓰고 싶어질 때(「이걸 켜면 무거운 기능을 뺀다」).

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

- ★★★ **app1 혼자 통과 · app2 혼자 통과 · 함께면 app1 이 E0425.** app1 은 `minimal` 을 켠 적이 없는데, 합쳐진 한 벌에서 `extra` 가 **빠졌다.**
- ★★★ **각 패키지의 CI 로는 안 잡힌다** — 둘을 **같은 그래프에 넣는 순간** 드러난다. 라이브러리라면 그 「둘」이 **서로 모르는 두 사용자**일 수 있다.
- ★★ rustc 가 `note: found an item that was configured out` 로 **cfg 로 빠진 항목**을 짚어 준다.

### (3) ★★ `default-features = false` — 「요청 안 함」이지 「끔」이 아니다

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

- ★★ **혼자면 `a=false`, app2 와 함께면 `a=true`** — app2 가 기본(`default = ["a"]`)을 요청했다.
- ★★ **feature 요청에는 「켜라」만 있고 「끄라」가 없다.** `default-features = false` 는 **내 요청에서 기본을 뺄** 뿐이다.

### (4) ★★★ resolver 1 대 2 — 빌드 스크립트의 feature 가 본체로 새나

**언제 쓰나** — `[build-dependencies]`·proc-macro·dev-의존성에서 같은 크레이트를 **다른 feature 로** 쓸 때. 특히 빌드 스크립트가 `std` 를 켜고 본체는 `no_std` 일 때.

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

- ★★★ **resolver 2 — 빌드 스크립트 `a=false b=true` · 본체 `a=true b=false`**: gear 가 **두 벌** 빌드됐다.
- ★★★ **resolver 1 — 둘 다 `a=true b=true`**: 한 벌로 합쳐져 **빌드 스크립트용 `b` 가 실행 파일로 샜다.**
- ★ cargo 문서 — resolver 2 가 합치지 않는 자리 셋(플랫폼 전용 · **빌드 의존성/proc-macro** · 테스트를 안 빌드할 때의 dev-의존성) 중 **이 블록은 둘째만** 쟀다.

**`resolver` 를 안 적으면.**

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

- ★★★ **가상 워크스페이스는 `resolver` 를 안 적으면 `"1"`** — 멤버가 2021 이어도(경고가 「2021 은 2 를 뜻하는데 1 로 떨어진다」고 말한다). 빌드 스크립트가 `a=true b=true` 를 본 것이 **실제로 1 이 쓰였다**는 증거다.
- ★★ 멤버가 2024 면 경고가 **`implies resolver = "3"`** 으로 바뀐다(3 의 동작 — `rust-version` 에 맞는 판을 고르는 기본값 — 은 **재지 않았다**).

```text
   resolver 를 정하는 곳 (cargo 문서 · 이 블록)

   루트가 [package] 가 있는 패키지   → 그 패키지의 edition 이 기본값을 정한다 (2021 → 2, 2024 → 3)
   루트가 가상 워크스페이스           → [workspace] resolver = "…" 에 적어야 한다 — 안 적으면 1 + 경고
   멤버 · 의존성 쪽에 적은 값         → 무시된다 (워크스페이스 전체에 하나)
```

★ 위 그림의 첫 줄(루트가 패키지인 경우)은 **cargo 문서의 서술**이고 이 편은 가상 워크스페이스만 던졌다.

### (5) ★★ 워크스페이스가 공유하는 것 — `Cargo.lock` 과 `target/`

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

- ★★★ **멤버 디렉토리(`ws/app1`)에서 빌드해도 `Cargo.lock` 과 `target/` 은 루트 `ws/` 에 생긴다.** cargo 가 위로 올라가 워크스페이스 루트를 찾는다.
- ★ 그래서 (1)의 두 앱이 **같은 `ws/target/debug/`** 를 쓰고 gear 빌드를 나눠 가졌다 — 그 공유가 곧 **통합의 무대**다.

### (6) ★★ 의존성 요구 — 경로 의존성의 `version` 과 `[workspace.dependencies]`

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

- ★★★ **경로 의존성에도 `version` 을 적으면 검사한다** — `"0.2"` 는 `^0.2` 로 읽혀 `0.1.0` 을 거부했다(`failed to select a version`).
- ★★★ **`"0.1.0"` → `^0.1.0` · `version` 없음 → `*`** — 기본 요구는 **캐럿**이다(문서: 가장 왼쪽의 0 아닌 자리가 같으면 호환 — `^0.1.0` = `0.1.x`, `^1.2.3` = `<2.0.0`).
- ★ 경로와 판을 **함께** 적는 모양은 「로컬에서는 경로, 배포하면 레지스트리의 그 판」으로 쓰는 관용구다(cargo 문서의 multiple locations) — **배포 쪽은 재지 않았다.**

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

- ★★ **`workspace = true` 는 루트의 한 줄을 물려받고, 멤버의 `features` 는 거기에 더해진다**(app2 `a`+`b`). **뺄 수는 없다.**
- ★★★ **멤버의 `default-features = false` 는 무시된다** — 루트가 `default-features` 를 안 적었으면(경고 · 「hard error 가 될 수 있다」). 끄려면 **루트에** 적는다. `-q` 로 돌리면 이 경고가 **안 보인다.**

## 문법 — 형태와 규칙

```text
   [features]
   default = ["std"]          ← 아무것도 안 적은 사용자가 받는 것
   std = []                   ← 켜면 기능이 「늘어나는」 스위치로 설계한다
   a = ["dep:other"]          ← 켜면 선택적 의존성도 켠다 (이 편은 던지지 않았다)

   [dependencies]
   gear = { path = "../gear", version = "0.1", features = ["a"], default-features = false }

   [build-dependencies]       ← resolver 2 부터 일반 의존성과 feature 가 안 섞인다
   gear = { path = "../gear", features = ["b"] }

   [workspace]                ← 루트(가상 워크스페이스)
   members = ["gear", "app1"]
   resolver = "2"             ← 가상 워크스페이스는 안 적으면 1
   [workspace.dependencies]
   gear = { path = "gear" }   ← 멤버는 gear = { workspace = true, features = [...] }
```

- ★★★ **한 빌드 · 한 크레이트 · 한 벌 · feature 는 합집합**((1)).
- ★★★ **feature 는 더하기만** — 끄는 것은 `cfg(not(…))` 가 아니라 **기본 feature 에서 빼는 것**((2)·(3)).
- ★★ **resolver 는 워크스페이스에 하나**, 가상 워크스페이스는 **직접 적는다**((4)).
- ★★ **`"x.y.z"` = `^x.y.z`**((6)).

## 어디서 틀리나

### 1. ★★★ 「`cargo run -p app1` 이 통과했으니 app1 은 괜찮다」

(1)·(2) — **함께 빌드되는 순간 feature 가 합쳐진다.** 워크스페이스 CI 는 `--workspace` 빌드와 **패키지별** 빌드를 **둘 다** 돌려야 두 모양의 결함이 다 보인다.

### 2. ★★★ 「`default-features = false` 로 껐다」

(3) — **요청을 뺐을 뿐**이다. 그래프의 누가 기본을 요청하면 켜진다. 상속(`workspace = true`)에서는 **아예 무시**된다((6)).

### 3. ★★ 「feature 로 기능을 끌 수 있다」(`#[cfg(not(feature = "minimal"))]`)

(2) — **요청하지 않은 쪽이 깨진다.** 끄고 싶은 것은 **반대 이름의 켜는 feature**(`std`·`full`)로 뒤집는다.

### 4. ★★ 「edition 2021 이니까 resolver 2 겠지」

(4) — **가상 워크스페이스는 안 적으면 1** 이다(경고가 나오지만 `-q` 면 안 보인다). 루트에 `resolver = "2"`(2024 면 `"3"`)를 적는다.

### 5. ★★ 「`cargo tree` 에 `a` 만 있으니 `a` 만 켜졌다」

(0)·(1) — 트리는 **이번 선택의 요청 그래프**다. `-p app1` 트리와 `--workspace` 빌드의 실제 벌은 **다르다.**

### 6. ★ 「`path` 를 적었으니 `version` 은 상관없다」

(6) — **검사한다.** 안 맞으면 판 선택 실패다.

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| feature 통합 · 통합의 범위(선택된 패키지들) | ★ **cargo 의 규칙**(Cargo Book) — 언어(rustc)는 `--cfg` 를 받을 뿐이다 | (1) |
| 「feature 는 가산적이어야 한다」 | ★ **cargo 문서의 권고** — 아무도 강제하지 않는다(2번이 통과한 채 배포될 수 있다) | (2) |
| resolver 1/2/3 의 기본값 · 가상 워크스페이스의 1 | ★ **cargo 의 규칙** — 판에 매인다 | (4) |
| `Cargo.lock`·`target/` 공유 | ★ **cargo 의 규칙** | (5) |
| `"x.y.z"` = 캐럿 요구 | ★ **cargo 의 규칙** | (6) |
| `default-features` 무시 경고 | ★ **cargo 판**(1.92) — 「hard error 가 될 수 있다」 | (6) |
| `cfg!(feature = "a")` 가 `--cfg` 로 정해진다 | ★ **언어**(`cfg` 는 rustc 의 조건부 컴파일) + **cargo** 가 넘기는 값 | (0) |

★★ **이 주제의 사실은 거의 전부 cargo 의 것이다** — 「Rust 는 feature 를 합친다」가 아니라 **「cargo 1.92 가 합친다」** 로 읽는다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 근거 |
|---|---|---|
| 선택 기능을 준다 | **켜는 feature** — 켜면 늘기만 | (1)·(2) |
| `no_std` 를 지원한다 | **`std` feature**(흔히 기본에 넣는다) — `no_std` feature 는 쓰지 않는다 | cargo 문서 · (2) |
| 두 feature 가 정말 공존 불가 | **`compile_error!` 로 동시 활성화를 막는다** | cargo 문서 |
| 여러 크레이트를 한 저장소에서 | **워크스페이스** — 잠금·출력 공유 | (5) |
| 가상 워크스페이스를 만든다 | **루트에 `resolver = "2"`/`"3"` 를 적는다** | (4) |
| 멤버마다 같은 의존성 줄을 반복한다 | **`[workspace.dependencies]` + `workspace = true`** — 기본 feature 를 끌 거면 **루트에** | (6) |
| 워크스페이스 CI | **`--workspace` 빌드 + 패키지별 빌드 둘 다** | (1)·(2) |

## 핵심 문장

- ★★★ **한 빌드에서 한 크레이트는 한 벌만 빌드되고, feature 는 함께 선택된 패키지들의 요청을 합친다 — app1 은 요청하지 않은 `b` 를 받았다.**
- ★★★ **그래서 feature 는 더하기만 해야 한다 — 끄는 feature 는 요청하지 않은 쪽을 깨뜨린다(E0425).**
- ★★ **`default-features = false` 는 「끔」이 아니라 「요청 안 함」이다.**
- ★★ **resolver 2 는 빌드 스크립트용 feature 를 본체와 섞지 않는다 — 가상 워크스페이스는 안 적으면 1 이다.**
- ★★ **워크스페이스는 루트에 `Cargo.lock` 하나 · `target/` 하나 — `"0.1.0"` 은 `^0.1.0` 이다.**

## 관련 자료

- [**01번 주제**](../01-cargo-crates-and-modules/) — `Cargo.toml`·`Cargo.lock` 의 첫 모습 · `cargo build -v`. **그쪽은 「패키지 하나」, 여기는 「여럿이 묶일 때」.**
- [**45번 주제**](../45-module-system-mod-use-pub-crate-and-file-layout/) — 크레이트 **안**의 경계(모듈·가시성). 여기는 크레이트 **사이**.
- [**47번 주제**](../47-editions-2021-vs-2024-and-cargo-fix/) — 에디션이 resolver 기본값을 바꾼다(2021 → 2 · 2024 → 3).
- [`history/rust/05-생태계-도구.md`](../../../../history/rust/05-생태계-도구.md) — Cargo·crates.io 의 **역사**. 여기는 **지금 cargo 1.92 가 어떻게 합치나**로 좁힌다.
- Go 갈래 [`41-modules-go-mod-version-selection-and-workspaces`](../../../go/syntax/41-modules-go-mod-version-selection-and-workspaces/) — **MVS 대 캐럿 범위의 최신**(그 편 (8)이 Cargo 를 디렉토리 레지스트리로 쟀다) · Go 의 워크스페이스(`go.work`).

## 용어 풀이

- **패키지(package)** — `Cargo.toml` 하나가 기술하는 단위. 크레이트를 하나 이상 담는다.
- **크레이트(crate)** — rustc 가 한 번에 컴파일하는 단위(라이브러리·바이너리).
- **워크스페이스(workspace)** — 여러 패키지를 한 `Cargo.lock`·`target/` 아래 묶은 것. 루트에 `[package]` 가 없으면 **가상 워크스페이스**.
- **feature** — `[features]` 의 조건부 컴파일 스위치. 켜지면 `--cfg feature="…"`.
- **기본 feature(`default`)** — 사용자가 아무것도 안 적으면 켜지는 목록. `default-features = false` 로 요청에서 뺀다.
- **feature 통합** — 한 벌에 요청들의 합집합이 켜지는 것.
- **resolver** — 의존성·feature 를 고르는 cargo 의 알고리즘 판(`"1"`·`"2"`·`"3"`).
- **캐럿 요구** — `"1.2.3"` = `>=1.2.3, <2.0.0`(가장 왼쪽의 0 아닌 자리가 같은 범위).
- **빌드 의존성** — 빌드 스크립트(`build.rs`)만 쓰는 의존성. `[build-dependencies]`.

## 더 들어가면

- `dep:` 문법의 선택적 의존성 · `?` 가 붙은 약한 의존성 feature(`"other?/x"`) — **던지지 않았다.**
- `cargo build --features app1/x` 처럼 명령행에서 멤버의 feature 를 켜는 것(resolver 2 에서 넓어졌다 — cargo 문서) — **던지지 않았다.**
- `[patch]` 로 의존성을 로컬 경로로 갈아 끼우기 — **던지지 않았다.**
- 레지스트리의 판 선택과 `cargo update` — Go 41번 (8)의 디렉토리 레지스트리 방법이면 **네트워크 없이** 잴 수 있다.

## 실행 환경

**기준 소스** — [Cargo Book — Features](https://doc.rust-lang.org/cargo/reference/features.html)(「**feature 는 가산적이어야 한다** — 켜는 것이 기능을 끄면 안 된다」 · Feature unification · 「`no_std` feature 대신 `std` feature」 · 배타적 feature 는 `compile_error!`) ·
[Cargo Book — Resolver](https://doc.rust-lang.org/cargo/reference/resolver.html)(「`"1"`(기본) · `"2"`(edition 2021 기본) · `"3"`(edition 2024 기본)」 · 「resolver 는 워크스페이스 전체의 전역 옵션」) ·
[Cargo Book — Workspaces](https://doc.rust-lang.org/cargo/reference/workspaces.html)(「루트의 `Cargo.lock` 하나 · `target` 하나를 공유」) ·
[Cargo Book — Specifying Dependencies](https://doc.rust-lang.org/cargo/reference/specifying-dependencies.html)(기본 요구 = 캐럿).
★ Cargo Book 은 **이 머신의 `rust-docs`(1.92.0) 로컬 사본**을 열어 읽었다.
**실행 검증** — 이 문서의 모든 출력·에러는 `cargo 1.92.0 (344c4567c 2025-10-21)` · `rustc 1.92.0` · `x86_64-unknown-linux-gnu` 에서
블록 배너의 명령으로 돌려 받은 것이다. ★★★ **네트워크 없이** — `CARGO_NET_OFFLINE=true` · `CARGO_HOME` 을 작업 디렉토리 안에 두고, **의존성은 전부 로컬 경로(`path = …`)** 다.\
★★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다. 소스 펜스도 캡처가 찍었다.\
★ **속도·메모리는 재지 않았다.**
