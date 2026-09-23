# cs/issue/rust/cargo/crate-module-boundary-rules — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 사건 기록 대조·추상화. 복습 전 읽지 말 것.

태그: —

## 정답
<!-- 질문 1:1 대응 -->

1. **크레이트는 링크 단위라서, 테스트 바이너리도 그 크레이트의 의존성 전체에 링크되기 때문이다.** 순수 함수가 GUI 프레임워크를 의존하는 크레이트 안에 있으면, 그 함수를 테스트하는 바이너리도 GUI 프레임워크가 링크하는 **시스템 GUI 라이브러리**를 요구한다. 함수가 GUI를 한 줄도 안 써도 빌드 단위가 같으면 요구 조건도 같다. 그래서 "존재하지 않는 경로를 panic 없이 `Err`로 돌려주는가" 같은 에러 경로를 헤드리스 테스트로 고정하지 못했고, 회고에서 "테스트 공백"으로 기록됐다. 교정은 순수 로직을 GUI 의존이 없는 `core` 크레이트로 옮기고(`core`는 직렬화 라이브러리만 의존), 앱 크레이트는 호출과 에러 매핑만 하는 얇은 래퍼로 두는 것이다.
   > **링크 단계** — 컴파일된 코드와 의존 라이브러리를 하나의 실행 파일로 묶는 단계. 테스트 바이너리도 실행 파일이라, 크레이트가 링크하는 모든 것을 요구한다.

2. **mock은 링크를 없애지 못한다.** 같은 파일에 두고 호출 대상을 mock해도 테스트 바이너리는 여전히 그 크레이트의 링크 의존(시스템 GUI 라이브러리)을 요구한다. mock은 실행 시점의 행동을 바꾸는 도구이고, 링크는 빌드 시점의 요구다. **feature-gated 모듈**은 순수 크레이트 안에 조건부 모듈을 두는 방식이다. 선택 의존(optional dependency)은 feature가 꺼진 빌드에선 컴파일·링크되지 않으므로 기술적으로는 링크 요구를 피할 수 있지만, 그 의존(비동기 런타임 등)과 feature 조합 관리가 순수 크레이트의 매니페스트에 들어와 "의존 없는 core"라는 성질이 흐려지고, 워크스페이스에서 다른 멤버가 feature를 켜면 합쳐진다(feature unification). 그래서 같은 원칙으로 이후 비동기 프로토콜 코드도 별도 크레이트에 격리했다. **크레이트 분리**가 빌드 단위 자체를 나눠 테스트의 링크 요구를 가장 직접적으로 없앤다.

3. 모듈 privacy는 방향이 있다.
   - (a) **부모 → 자식 private: 컴파일 실패.** 자식은 조상의 private 항목에 접근할 수 있지만, 부모는 자식의 private 항목에 접근하지 못한다 → 부모가 부르는 헬퍼만 `pub(super)`로 연다.
   - (b) **형제 → 형제의 private 필드 struct 생성: 컴파일 실패.** 형제는 서로의 private에 접근할 수 없다 → 여러 하위 모듈이 함께 쓰는 struct는 **공통 조상(모듈 루트)**에 남긴다.
   - (c) **외부 경로: 그대로 두면 깨진다.** 항목이 하위 모듈로 옮겨지면 경로가 `crate::big::sub::Item`이 된다 → 원래 파일을 모듈 루트로 유지하고 `mod sub; pub use sub::*;`로 **글롭 재노출**해 외부 경로를 보존한다.
   > **모듈 privacy 규칙** — Rust에서 private 항목은 정의된 모듈과 그 자손에게만 보인다. 가시성은 트리를 "아래로" 내려갈 뿐 "위로"·"옆으로" 가지 않는다.

4. 세 증거는 서로 다른 것을 보장한다.
   - **공개 항목·커맨드 이름 집합 diff 0** — 외부에서 보이는 표면이 한 항목도 사라지거나 늘지 않았다.
   - **테스트 개수 패리티** — 테스트가 이동 중에 빠지거나(모듈 선언 누락으로 컴파일에서 제외) 중복되지 않았다. 통과 여부만 보면 "테스트가 사라져서 통과"를 놓친다.
   - **전 경로를 참조하는 매크로 컴파일** — 핸들러 등록 매크로가 79개 커맨드 경로를 전부 이름으로 참조하므로, 컴파일이 성공하면 모든 경로가 여전히 해석된다는 뜻이다.
   셋을 합쳐 "이동만 했고 의미는 바뀌지 않았다"를 기계적으로 증명한다.

5. **로컬 `core`가 표준 `core`를 가린다.** `core`는 extern prelude에 이미 있는 이름(`core`·`std` — `alloc`은 `extern crate alloc;`을 선언했을 때만)이라, 같은 이름의 로컬 크레이트를 의존하면(Cargo가 `--extern core=...`로 넘겨 sysroot의 core를 덮는다) `use core::...`가 표준 대신 로컬 크레이트로 해석된다 — 표준 `core`가 가려진다. 더 까다로운 것은 **절차 매크로**다. serde/clap derive나 `async-trait`은 위생을 위해 `::core::marker::Send`, `::core::option::Option` 같은 **절대경로**를 생성하는데, 의존성에 `core`라는 크레이트가 있으면 그 절대경로가 표준 라이브러리 대신 로컬 크레이트로 해석된다. 그래서 내 코드는 멀쩡한데 매크로 확장 결과가 "could not find marker/option in core"로 깨지고, 한 번 고친 뒤에도 derive를 쓰는 새 바이너리에서 다시 깨졌다. `core` 크레이트 자신의 doctest도 `use core::…`로 깨져 `cargo test` 전체가 실패했다(`--lib`만 통과).
   > **extern prelude** — 모든 모듈에서 `use` 없이 이름으로 접근 가능한 외부 크레이트 목록. 표준 `core`·`std`와 의존 크레이트 이름이 여기에 함께 들어가므로 이름이 겹치면 해석이 충돌한다.

6. 효과 범위가 다르다.
   - **`[lib] name = "core_lib"`** — 라이브러리 **타깃 자체의 이름**을 바꾼다. 패키지 이름은 `core`로 두어도 코드상 이름이 `core_lib`가 되므로, 이 라이브러리를 참조하는 **모든 곳**(같은 패키지의 bin 포함)에 효과가 있다. 같은 패키지의 bin은 lib를 lib 타깃 이름(기본값 = 패키지 이름)으로 참조하므로 Cargo.toml 의존 항목처럼 별칭을 걸 자리가 없다 — 이 경우는 타깃 이름 변경으로 해결했다.
   - **`core_lib = { path = "../core", package = "core" }`** — **의존하는 쪽에서** 들여오는 이름만 바꾼다. 소비자마다 따로 걸어야 하지만 라이브러리 쪽을 건드리지 않는다.
   두 방법을 함께 쓰면 타깃 이름과 외부 별칭을 같은 이름(`core_lib`)으로 맞출 수 있다. (방안 비교 참고)

7. **빌드 규칙을 설계 신호로 읽는다.** 링크 의존은 "테스트할 로직을 무거운 의존에서 떼라"(순수 core + 얇은 어댑터), 모듈 privacy는 "공유 타입은 공통 조상에, 공개 표면은 루트에서 재노출"(트리 구조가 곧 가시성 설계), extern prelude는 "크레이트 이름은 전역 네임스페이스다"(표준 이름·흔한 이름을 피하거나 타깃 이름으로 분리)라고 말한다. 셋 다 컴파일러가 강제하므로, 규칙과 싸우는 우회(mock·feature 게이트·전부 pub)보다 **규칙이 권하는 모양으로 구조를 바꾸는 편**이 싸다.

## 문제 구조 (추상화 코드)

### 변형 A — GUI 링크 크레이트 안의 순수 로직 (헤드리스 테스트 불가)
① 문제 코드
```rust
// app/Cargo.toml : [dependencies] gui-framework = "..."   → 시스템 GUI 라이브러리 링크
// app/src/commands.rs
#[command]
pub fn read_dir(path: String) -> Result<Vec<Entry>, AppError> {
    let entries = std::fs::read_dir(&path)?;   // 순수 로직이지만 테스트 바이너리가 GUI 링크를 요구
    // ...
}
```
② 고친 코드
```toml
# Cargo.toml
[workspace]
members = ["core", "app"]
# core/Cargo.toml — serde, serde_json 만
```
```rust
// core/src/lib.rs — 헤드리스 테스트 가능
pub fn list_dir(path: &Path) -> Result<Vec<Entry>, CoreError> { /* ... */ }

// app/src/commands.rs — 얇은 래퍼: 호출 + 에러 매핑만
#[command]
pub fn read_dir(path: String) -> Result<Vec<Entry>, AppError> {
    core_lib::list_dir(Path::new(&path)).map_err(AppError::from)
}
```
무엇이 깨졌나: 테스트하고 싶은 로직과 무거운 링크 의존이 같은 빌드 단위에 있었다.

### 변형 B — 모듈 분할이 privacy 규칙에 막힘
① 문제 코드
```rust
// big.rs 를 big/a.rs, big/b.rs 로 쪼갬
// big/mod.rs
fn run() { a::helper(); }                      // 부모 → 자식 private: 컴파일 실패
// big/b.rs
let s = super::a::Output { buf: vec![] };      // 형제의 private 필드 struct 생성: 컴파일 실패
// 외부
use crate::big::Item;                          // Item 이 big::a 로 이동 → 경로 깨짐
```
② 고친 코드
```rust
// big.rs (원래 파일을 모듈 루트로 유지)
mod a;
mod b;
pub use a::*;                                  // 글롭 재노출 — 외부 경로 보존
pub use b::*;
pub(crate) struct Output { buf: Vec<u8> }      // 형제 공유 타입은 공통 조상(루트)에

// big/a.rs
pub(super) fn helper() { /* ... */ }           // 부모가 부르는 헬퍼만 pub(super)
```
```text
동작 보존 증거: 공개 항목·커맨드 이름 집합 diff 0 + 테스트 개수 패리티 + 핸들러 등록 매크로 컴파일(전 경로 참조)
```
무엇이 깨졌나: 파일 분할을 "텍스트 이동"으로 봤지만, 모듈 경계는 가시성 경계라서 이동만으로 접근 관계가 바뀌었다.

### 변형 C — 로컬 크레이트 이름 `core`가 표준 `::core`를 가림
① 문제 코드
```toml
# core/Cargo.toml
[package]
name = "core"
[[bin]]
name = "tool"                                  # bin 에서 자기 lib 를 `core` 로 참조 → 내장 core 와 충돌

# server/Cargo.toml
[dependencies]
core = { path = "../core" }                    # extern prelude 의 core 를 가림
```
```rust
#[derive(Serialize, Parser)]                   // 매크로 생성 코드: ::core::marker::..., ::core::option::...
struct Args { /* ... */ }                      // → could not find `marker` in `core`
#[async_trait]
trait Store { /* ... */ }                      // 같은 실패
```
② 고친 코드
```toml
# core/Cargo.toml
[lib]
name = "core_lib"                              # 타깃 이름 변경 — 자기 bin 포함 모든 참조에 적용

# server/Cargo.toml
[dependencies]
app_core = { package = "core", path = "../core" }   # 의존하는 쪽 별칭 — ::core 는 다시 표준을 가리킴
```
```rust
// core 자신의 doctest: use core::… 가 깨짐 → import/setup 보강, no_run, fn main() -> Result 로 감싸기
```
무엇이 깨졌나: 크레이트 이름이 전역 네임스페이스(extern prelude)에 들어간다는 사실을 몰랐고, 매크로가 생성한 절대경로가 그 이름을 그대로 따라갔다.\
같은 구조: 라이브러리 타깃 이름을 `core_lib`로 바꾸고 외부 의존도 `core_lib = { package = "core" }`로 맞춰 코드상 이름을 하나로 통일.

## 검증 기록
- 2026-09-24: 사건 기록 대조·추상화(Claude 초안)

## 방안 비교

기본 방안(변형 C의 `[lib] name` 변경)은 "라이브러리 타깃 이름을 바꿔 충돌을 원천에서 없앤다"이다. 같은 원리(extern prelude 이름 충돌)에 다른 방안이 쓰인 사례:

### 방안 1 — 의존하는 쪽에서 import 이름만 바꿈
```toml
# 앱 크레이트 Cargo.toml
[dependencies]
core_lib = { path = "../core", package = "core" }   # 패키지 이름은 core 그대로
```
```rust
use core_lib::list_dir;       // 로컬 크레이트
use core::fmt;                // 표준 core — 충돌 없음
// 문제였던 형태: `use core::list_dir;` → 표준 core 를 가리켜 컴파일 에러
```

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 기본: `[lib] name` 변경 | 라이브러리 쪽 Cargo.toml 을 고칠 수 있다 | 한 곳 | 코드상 이름이 모든 참조처에서 `core_lib`로 바뀜(기존 참조 수정 필요) | 같은 패키지에 bin 이 있어 별칭 자리가 없을 때 |
| 1. 의존 쪽 별칭 | 소비자마다 Cargo.toml 을 고칠 수 있다 | 소비자 수만큼 | 별칭을 잊은 소비자에서 매크로 경로가 깨짐 | 라이브러리를 건드리기 어렵거나 소비자가 적을 때 |

**결론**: 같은 패키지의 bin이 자기 lib를 참조해야 하면 별칭을 걸 자리가 없으므로 **타깃 이름 변경**이 유일한 선택이다.\
외부 소비자만 있으면 별칭으로 충분하지만, 소비자가 늘 때마다 같은 설정을 반복해야 한다.\
두 방법을 같은 이름으로 함께 쓰면 코드 어디서든 이름이 하나로 보인다. 가장 싼 예방은 처음부터 표준 이름(`core`/`std`/`alloc`)을 패키지 이름으로 쓰지 않는 것이다.
