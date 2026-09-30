# Rust — 그 뒤 (2026-09 기준)

> 이 문서는 **재서술이 아니라 새로 쓴 것**이다.\
> 앞의 01~06편은 `~/project/rust-history/`의 원문을 정본으로 두고 옮긴 것이지만, 이 편에는 대조할 원문이 없다.\
> 그래서 원문 대조가 하던 자리를 **출처**가 대신한다 — 아래 모든 사실 주장에는 출처가 붙어 있고, 확인하지 못한 것은 적지 않았다.\
> 기준일은 **2026-09-20**이다. 이 날 이후의 일은 담기지 않았다.

---

## 원본이 멈춘 자리

원문에서 **릴리스로 서술된 마지막 사건은 Rust 1.85.0 / Rust 2024 에디션**(2025년 2월 20일)이다.

| 갈래 | 원문이 다룬 마지막 사건 | 원문 위치 |
|------|------------------------|-----------|
| 릴리스·에디션 | **Rust 1.85 + 2024 에디션**(2025-02-20). `unsafe extern`·`if let` 임시값 수명·RPIT `use<>`·`gen` 예약·resolver v3 | `02-에디션.md` 229·235·296·307행 (resolver v3은 296행, 나머지는 307행 표) |
| 빌림 검사기 | **Polonius**가 나이틀리에서 `-Zpolonius` 플래그로 실험 가능, Project Goals 2025 H1/H2로 "진행 중" | `03-소유권-시스템.md` 196행 |
| async | **Rust 1.75**(2023-12-21) AFIT/RPITIT 안정화. `dyn` 호환 불가와 `Send` 경계 전파는 **미완**으로 남김 | `04-비동기-동시성.md` 19·258~262행 |
| 생태계 | 2026년 3월 OpenAI의 Astral 인수, 2025년 11월 Android 보안 블로그, 2025 Stack Overflow 설문 | `05-생태계-도구.md` 170·185·194행 (Android 170·200행과 215행 링크, Stack Overflow 185행, Astral 194행) |

그러니까 원문은 **생태계 쪽 곁가지는 2026년 초까지 닿아 있지만, 언어 본체의 서술은 1.85에서 멈춰 있다.**
이 문서가 메우는 간격은 주로 **Rust 1.86(2025-04-03) ~ 1.98.1(2026-09-03)** 구간이다.

### 먼저 갈라 놓을 두 가지 — 에디션과 릴리스

원문 02편이 이미 적은 구분이지만, 이 문서에서 특히 중요하므로 다시 세운다.

| | 릴리스 | 에디션 |
|---|--------|--------|
| 주기 | 6주 | 약 3년 |
| 정하는 것 | 언제 쓸 수 있게 되는가 | 이 크레이트의 소스를 어느 규칙으로 읽는가 |
| 고르는 곳 | 설치한 툴체인 | `Cargo.toml`의 `edition` |
| 이 문서의 범위 | 1.86 ~ 1.98.1 | 2024 (변동 없음) |

**둘이 만나는 자리가 있다.** 어떤 기능은 *릴리스*에서 안정화되면서 *특정 에디션에서만* 켜진다 — 아래 `let` 체인이 그 예다.

**2026-09-20 현재 최신 에디션은 여전히 Rust 2024다.** 그 다음 에디션에 대한 공식 발표는 확인하지 못했다.

---

## 그 뒤 무슨 일이 있었나

### 1. 릴리스 — 1.86부터 1.98.1까지

6주 주기가 그대로 지켜졌다. 원문이 멈춘 1.85 이후의 정식 릴리스는 이렇다.

| 버전 | 날짜 | 버전 | 날짜 |
|------|------|------|------|
| 1.86.0 | 2025-04-03 | 1.93.0 | 2026-01-22 |
| 1.87.0 | 2025-05-15 | 1.94.0 | 2026-03-05 |
| 1.88.0 | 2025-06-26 | 1.95.0 | 2026-04-16 |
| 1.89.0 | 2025-08-07 | 1.96.0 | 2026-05-28 |
| 1.90.0 | 2025-09-18 | 1.97.0 | 2026-07-09 |
| 1.91.0 | 2025-10-30 | 1.98.0 | 2026-08-20 |
| 1.92.0 | 2025-12-11 | **1.98.1** | **2026-09-03** |

(그 사이 패치 릴리스 1.91.1·1.93.1·1.94.1·1.96.1·1.97.1이 있었다. 출처: [rust-lang/rust — RELEASES.md](https://github.com/rust-lang/rust/blob/master/RELEASES.md), 1차)

**2026-09-20 기준 최신 stable은 1.98.1이다.**\
1.98.1은 기능 릴리스가 아니라 **버그 수정 한 건짜리 패치**다 — RELEASES.md의 항목은 "rustc: fix miscompilation in generating vtables" 한 줄뿐이다.\
무엇이 잘못됐었나 — 공지의 표현으로 "In Rust 1.98.0, in some circumstances, rustc would incorrectly generate a trait object vtable with a null pointer where a function pointer should be"이고, 그 결과는 **정의되지 않은 동작**(UB)이다("This leads to undefined behavior in the emitted code"). (출처: [Rust 1.98.1](https://blog.rust-lang.org/2026/09/03/Rust-1.98.1/), 2026-09-03, 1차)

#### 그중 눈에 띄는 안정화 항목

모두 **stable로 안정화된 것**이다 — 나이틀리 전용 항목은 아래 「아직 안 끝난 것」에 따로 모았다.

| 릴리스 | 안정화된 것 | 한 줄 |
|--------|------------|-------|
| 1.86.0 | **트레이트 객체 업캐스팅** | `dyn Sub`를 `dyn Super`로 올려 쓸 수 있다 |
| 1.86.0 | 안전한 함수에 `#[target_feature]` | |
| 1.87.0 | `asm_goto` | 인라인 어셈블리에서 레이블로 분기 |
| 1.87.0 | 트레이트 안 RPIT의 `use<...>` 한정 | `use<...>` 자체는 1.82.0에서 에디션과 무관하게 안정화됐고, 여기서 **쓸 수 있는 자리가 트레이트 안까지** 넓어졌다 |
| **1.88.0** | **`let` 체인** | `if`·`while` 안에서 `let`을 `&&`로 이어 쓸 수 있다 — **2024 에디션에서만** |
| 1.88.0 | naked 함수(`feature(naked_functions)`) | 컴파일러가 만드는 앞뒤 코드 없이 어셈블리를 직접 씀 |
| 1.88.0 | `cfg` 조건에 불리언 리터럴(`#[cfg(true)]`) | |
| 1.89.0 | `#[repr(u128)]`·`#[repr(i128)]`, avx512 타깃 기능 | |
| 1.91.0 | `sysv64`·`win64`·`efiapi`·`aapcs` ABI의 C 가변 인자 **선언** | 선언만 되고 정의는 안 된다 — C ABI와 같은 규칙 |
| 1.94.0 | 유니코드 17 반영 | |
| 1.95.0 | **`if let` guard** — `match` 팔의 가드에 `if let` | |
| 1.97.0 | 심볼 맹글링 기본값이 **v0**로 | 디버거·프로파일러가 옛 버전이면 심볼을 못 풀 수 있다(호환성 주의로 명시됨) |
| 1.98.0 | `String::from_utf16le`/`be` 계열, `bool::ok_or` 등 | |

(출처: [rust-lang/rust — RELEASES.md](https://github.com/rust-lang/rust/blob/master/RELEASES.md)의 각 버전 Language·Stabilized APIs·Compatibility Notes 절, 1차)

> **`use<>`는 에디션 기능이 아니다** — 여기서 갈라 둘 것이 있다.\
> 정밀 캡처 문법 `use<...>` 자체는 **1.82.0(2024-10-17)에서 에디션과 무관하게** 안정화됐다 — RELEASES.md의 항목은 "Stabilize `+ use<'lt>` opaque type precise capturing (RFC 3617)"이다.\
> 2024 에디션이 바꾼 것은 그 문법이 아니라 **RPIT의 기본 캡처 규칙**이고, 1.87.0이 더한 것은 그 문법을 **트레이트 안 RPIT에서도** 쓸 수 있게 한 것이다("Stabilize `feature(precise_capturing_in_traits)` allowing `use<...>` bounds on return position `impl Trait` in `trait`s").\
> 원문 02편의 표현을 그대로 이어받으면 "`use<>`가 2024 에디션 기능"으로 읽히기 쉬우므로 여기서 구분해 둔다. (출처: 같은 곳, 1차)

#### `let` 체인 — 에디션과 릴리스가 만나는 자리

릴리스 노트의 문장은 "**Stabilize `#![feature(let_chains)]` in the 2024 edition**"이다.
즉 **Rust 1.88.0(릴리스)에서 안정화됐지만, 2024 에디션(에디션)에서만 켜진다.**

```rust
// Rust 1.88+, edition = "2024" 에서만
if let Some(x) = opt && x > 3 {
    // ...
}
```

같은 1.88.0 컴파일러를 쓰더라도 `edition = "2021"` 크레이트에서는 이 문법이 안 된다.
**"컴파일러를 올렸는데 왜 안 되지"의 답이 여기 있다** — 올려야 할 것이 하나 더 있다.

(출처: [RELEASES.md — Version 1.88.0](https://github.com/rust-lang/rust/blob/master/RELEASES.md), 1차)

> **`let` 체인(let chains)** — `if`/`while`의 조건 안에서 `let` 패턴 매칭과 불리언 조건을 `&&`로 이어 쓰는 문법.\
> 예: `if let Some(x) = opt && x > 3 { ... }` — 예전에는 `if let` 안에 `if`를 한 겹 더 써야 했다.

---

### 2. 빌림 검사기 — Polonius가 나이틀리 기본값이 됐다 (아직 stable 아님)

원문 03편은 Polonius를 "나이틀리에서 `-Zpolonius` 플래그로 실험 가능"하고 "안정화 가능한 수준으로 끌어올리는 작업이 진행 중"이라고 적었다.
**그 작업이 한 칸 나아갔다 — 하지만 stable에는 아직 오지 않았다.**

**2026년 8월 4일, Polonius Alpha가 나이틀리에서 기본으로 켜졌다.** 끄려면 `-Zpolonius=off`를 준다.
글의 저자는 Jack Huey이고, Polonius working area를 대표해 썼다. (출처: [Enabling the next iteration of the borrow checker on nightly](https://blog.rust-lang.org/2026/08/04/enabling-polonius-alpha-on-nightly/), 2026-08-04, 1차)

무엇이 달라지는가 — Polonius Alpha는 수명 관계를 **흐름 민감(flow-sensitive)** 하게 본다.
글이 드는 대표 예가 `HashMap::get_mut()`을 쓴 `match`다: NLL은 빌림의 범위를 모든 갈래로 늘려 잡아 거절했지만, Polonius Alpha는 관련 있는 갈래로만 좁힌다.

**"정식이 됐다"로 읽으면 안 되는 이유가 셋 있다.**

1. **나이틀리 전용**이다. stable 채널에는 없다.
2. **이름이 Alpha인 이유가 있다** — 원래 Polonius 구현에서는 컴파일되던 프로그램 중 일부가 Polonius Alpha에서는 컴파일되지 않는다고 글이 직접 적는다.
3. **성능 작업이 남았다** — 상위 1만 크레이트 기준으로 큰 회귀는 드물었지만, 최악의 경우 2~3배 느려지는 사례가 있다고 적는다. 안정화 전에 최적화하겠다는 계획이다.

안정화 목표는 **2026년 말**로 적혀 있다 — 즉 **예정**이다. (출처: 같은 글, 1차)\
같은 방향이 프로젝트 목표 쪽에도 있다 — 2026년 목표 목록에 "**Stabilize and model Polonius Alpha**"가 **Large**로 올라 있다. (출처: [Rust Project Goals 2026 — Goals](https://goals.rust-lang.org/2026/goals.html), 1차)

---

### 3. 트레이트 해결기 — "컴파일러 출시 이래 가장 큰 단일 변경"이 나이틀리에 들어갔다

원문에 없는 갈래이고, 위 Polonius와 **별개의** 작업이다.

**2026년 8월 21일, 차세대 트레이트 해결기(next-generation trait solver)가 나이틀리에서 기본으로 켜졌다.**
글은 이것을 "the largest single change to the Rust compiler since its initial release"라고 적고, where 절 증명과 연관 타입 정규화를 **완전히 교체**한다고 설명한다. 약 4년의 개발을 거쳤다.

- **아직 stable이 아니다.** 나이틀리에 기본으로 켜 남은 문제를 드러내는 단계이고, 글은 "plan to stabilize it in the next months"라고 적는다 — **예정**이다.\
  2026년 목표 목록에도 "**Stabilize the next-generation trait solver**"가 **Large**로 올라 있다. (출처: [Rust Project Goals 2026 — Goals](https://goals.rust-lang.org/2026/goals.html), 1차)
- GitHub 이슈 **200건 이상**이 이 변경으로 고쳐진다고 적는다.
- 옛 구현이 빠지면 **Type Alias Impl Trait**과 **Return Type Notation** 같은 기능이 풀리고, `Move`·`Forget` 같은 새 암묵 기본 트레이트 경계를 넣을 길이 열리며, 남은 타입 시스템 unsoundness를 고칠 수 있다고 적는다.
- 컴파일 시간 효과의 예로 `datafusion` 크레이트가 **8배 이상 빠르게 컴파일된다**고 적는다. 이 값은 **그 크레이트 하나를 잰 것**이므로, 일반적인 배수로 읽으면 안 된다.

(출처: [Enabling the next-generation trait solver on nightly](https://blog.rust-lang.org/2026/08/21/enabling-next-solver-on-nightly/), 2026-08-21, lcnr / The Rustc Trait System Refactor Initiative, 1차)

> **unsoundness(불건전성)** — 타입 검사를 통과했는데도 안전하지 않은 코드가 만들어질 수 있는 구멍.\
> 예: 컴파일러가 "이 코드는 안전하다"고 보증했는데 실제로는 메모리 규칙을 깰 수 있는 경우.

---

### 4. async — 원문이 「미완」이라 적은 것은 아직 미완이다

원문 04편은 Rust 1.75의 AFIT 이후에도 두 가지가 남았다고 적었다 — **`dyn` 호환 불가**와 **`Send` 경계 전파**.

**1.86부터 1.98.1까지의 릴리스 노트에서 이 둘을 푸는 안정화 항목을 찾지 못했다.**
그리고 Rust 프로젝트의 2026년 목표 목록에는 "**Native async fn dynamic dispatch in traits**"가 아직 *목표*로 올라 있고, 분류는 **Medium**이다.\
2026년 목표 페이지는 목표를 **Large / Medium / Small** 셋으로만 나눈다 — Large는 팀 전체의 관여가 필요한 것, Medium은 팀 챔피언 한 사람의 지원이 필요한 것, Small은 팀의 평상시 절차로 감당되는 것이다. (출처: [Rust Project Goals 2026 — Goals](https://goals.rust-lang.org/2026/goals.html), 1차)

즉 **"트레이트의 `async fn`을 `dyn`으로 쓰는 것"은 2026-09 현재도 stable에 없다.** 원문이 적은 대로 동적 디스패치가 필요하면 여전히 박싱(`async-trait`)이 필요하다.

같은 목록에 async 관련 목표가 둘 더 있다 — "Async Future Memory Optimisation", "Async statemachine optimisation". 둘 다 *목표*이지 완료가 아니다. (출처: 같은 곳, 1차)

---

### 5. 생태계 — 공급망 공격이 실제로 일어났다

원문 05편은 crates.io를 "처음부터 통합된" 도구 사슬의 성공 사례로 적었다. 그 사슬에 **실제 공격**이 왔다.

#### arrayref 공급망 공격 (2026-08-20)

- 유지보수자의 자격 증명이 탈취된 것으로 보이며, 악성 크레이트가 crates.io에 올라왔다.
- 악성 버전과 그 노출 시간이 공지에 적혀 있다 — `arrayref@0.3.10`(86분), `internment@0.8.7`(90분), `append-only-vec@0.1.9`(107분). 그 밖에 `proc-macro1`·`proc-macro-en`·`aovine`·`arone`·`aronenao`·`tinymember`는 전 버전이 대상이다.
- 수법은 **빌드 스크립트**였다 — `proc-macro1`이라는 악성 크레이트의 build script가 악성 페이로드를 내려받았고, `arrayref`가 그 크레이트에 의존하도록 재발행됐다.
- 대응: 악성 버전 삭제, 정당하게 yank된 버전 복원, 해당 계정 잠금.

(출처: [Supply chain attack on arrayref](https://blog.rust-lang.org/2026/08/20/supply-chain-attack-on-arrayref/), 2026-08-20, 1차)

> **빌드 스크립트(build script, `build.rs`)** — 크레이트를 빌드하기 전에 **빌드 머신에서 실행되는** Rust 코드.\
> 예: C 라이브러리를 찾아 링크 설정을 내보내는 용도로 쓰인다 — 그래서 악성 크레이트가 있으면 `cargo build`만으로 코드가 실행된다.

공지가 적는 사실만 따로 떼면 이렇다 — **`build.rs`는 `cargo build`를 돌리는 것만으로 빌드 머신에서 실행되고**, 이번 사건에서는 악성 크레이트의 build script가 페이로드를 내려받았으며, `arrayref`가 그 크레이트에 의존하도록 재발행됐다.

여기서 원문의 한 문장이 다시 읽힌다.\
원문은 Cargo가 "빌드·의존성·테스트·문서·배포를 하나의 명령으로" 통합한 것을 장점으로 적었다.\
이번 사건은 **원문이 장점으로 적은 그 통합 안에서** 일어났다 — 다만 "통합이 곧 공격 표면"이라는 일반 명제는 공지에 없는 말이므로, 여기서는 그 대비만 적어 둔다.

#### 유지보수자를 노린 사회공학 (2026-09-17)

기준일 사흘 전의 공지다.\
Rust 언어 유지보수자와 인기 크레이트 소유자를 노려, **화상 통화로 접근해 악성 프로그램 설치나 명령 실행을 유도**하는 수법이 보고됐다.\
가짜 LinkedIn 프로필로 회사를 사칭한다.\
공지는 2026년 6월에도 비슷한 시도가 있었고 8월 `arrayref` 사건이 있었다고 적으며, 이들이 하나의 캠페인인지는 **단정하지 않는다**.\
권고는 먼저 연락받은 통화에 응하지 말 것, 신뢰하는 플랫폼에서 직접 통화를 걸 것, MFA를 켜고 로그인 기록을 확인할 것이다. (출처: [Be alert: targeted attacks on prominent Rustaceans](https://blog.rust-lang.org/2026/09/17/targeted-attacks/), 2026-09-17, 1차)

#### 그 밖에

- **Maintainers in Residence** — 2026년 8월 26일, Rust 프로젝트가 첫 "Maintainers in Residence"를 발표했다. (출처: [Rust Blog 피드](https://blog.rust-lang.org/feed.xml), 1차. 제목·날짜만 확인했고 본문은 열지 않았다.)
- **Cargo** — 1.94.0에서 설정 `include` 키와 레지스트리 인덱스의 `pubtime` 필드가 안정화됐고, Cargo가 매니페스트·설정 파일을 **TOML v1.1**로 파싱하게 됐다.\
  1.97.0에서는 `build.warnings`와 `resolver.lockfile-path` 설정이 안정화됐다. (출처: [RELEASES.md](https://github.com/rust-lang/rust/blob/master/RELEASES.md)의 해당 Cargo 절, 1차)

---

## 원문이 「예정」·「진행 중」이라 한 것은 어떻게 됐나

| 원문의 서술 | 원문 위치 | 그 뒤 |
|------------|-----------|-------|
| Polonius가 나이틀리 `-Zpolonius` 플래그로 실험 가능, 안정화 가능 수준으로 끌어올리는 작업 **진행 중** | `03-소유권-시스템.md` 196행 | **한 칸 나아갔다.** 2026-08-04 Polonius Alpha가 **나이틀리 기본값**. 여전히 **stable 아님**, 안정화 목표는 2026년 말(예정) |
| 트레이트의 `async fn`을 `dyn`으로 못 쓴다 — **미완** | `04-비동기-동시성.md` 259행 | **여전히 미완이다.** 2026 프로젝트 목표에 "Native async fn dynamic dispatch in traits"로 올라 있다 |
| `Send` 경계 전파가 까다롭다 — **미완** | `04-비동기-동시성.md` 260행 | 1.86~1.98.1 릴리스 노트에서 이를 푸는 안정화 항목을 **찾지 못했다** |
| 2024 에디션이 `gen`을 **예약**했다(미래 문법 공간 확보) | `02-에디션.md` 307행 | 1.86~1.98.1에서 `gen` 블록의 stable 안정화 항목을 **찾지 못했다** — 예약된 채로 남아 있다 |
| RPIT `use<>`(2024 에디션) | `02-에디션.md` 307행 | **확장됐다.** 1.87.0에서 트레이트 안 RPIT에도 `use<...>`를 쓸 수 있게 안정화 |

---

## 아직 안 끝난 것

「정식이 됐다」로 읽히면 안 되는 것들이다. **나이틀리에 있는 것과 stable에 있는 것을 섞지 마라.**

| 항목 | 지금 어디까지 | 다음 |
|------|--------------|------|
| **Polonius Alpha** | 나이틀리 **기본값**(2026-08-04). stable 아님 | 안정화 목표 2026년 말 — **예정**. 2026 프로젝트 목표 "Stabilize and model Polonius Alpha"(**Large**) |
| **차세대 트레이트 해결기** | 나이틀리 **기본값**(2026-08-21). stable 아님 | "next months"에 안정화 계획 — **예정**. 2026 프로젝트 목표 "Stabilize the next-generation trait solver"(**Large**) |
| **트레이트의 `async fn` 동적 디스패치** | stable 없음 | 2026 프로젝트 목표 "Native async fn dynamic dispatch in traits"(**Medium**) |
| **`gen` 블록** | 2024 에디션이 키워드를 **예약**만 함 | stable 안정화 항목 확인 못 함 |
| **Type Alias Impl Trait · Return Type Notation** | 트레이트 해결기 교체가 풀어 줄 것이라고 적힘 | 해결기 안정화 뒤 — **예정** |
| **다음 에디션** | 최신은 여전히 **2024** | 공식 발표 **확인하지 못했다** |

- Polonius Alpha에는 **되돌림도 있다** — 원래 Polonius에서는 통과하던 일부 프로그램이 Alpha에서는 통과하지 않는다. 그래서 "NLL의 모든 한계가 풀렸다"로 읽으면 안 된다.
- 위 두 나이틀리 항목은 **서로 다른 작업**이다. 하나는 빌림 검사기(수명), 하나는 트레이트 해결기(where 절·연관 타입). 같은 날짜 근처에 발표됐다는 이유로 묶으면 안 된다.

---

## 용어 풀이

본문에서 처음 쓴 말 중, 그 자리에서 풀지 않은 것만 모았다.

> **stable / beta / nightly** — Rust의 세 배포 채널. 기능은 nightly에서 실험되고 beta를 거쳐 stable에 도착한다.\
> 예: Polonius Alpha는 2026-09 현재 nightly에만 있고, `rustup default stable`로 쓰는 컴파일러에는 없다.

> **안정화(stabilize)** — 실험 플래그 뒤에 있던 기능을 stable 채널에서 플래그 없이 쓸 수 있게 여는 일.\
> 예: `let` 체인은 Rust 1.88.0에서 안정화됐다 — 단, 2024 에디션에서만 켜진다.

> **흐름 민감(flow-sensitive)** — 프로그램의 실행 경로(분기·반복)를 구분해서 분석하는 성질.\
> 예: `match`의 어느 갈래로 갔느냐에 따라 빌림이 살아 있는지를 따로 보는 것 — Polonius Alpha가 하는 일이다.

> **공급망 공격(supply chain attack)** — 내가 쓰는 라이브러리·빌드 도구를 오염시켜, 그것을 쓰는 쪽까지 감염시키는 공격.\
> 예: `arrayref`가 악성 크레이트에 의존하도록 재발행된 2026년 8월 사건.

> **yank** — crates.io에서 이미 발행한 버전을 "새로 쓰지 말라"고 표시하는 일. 파일 자체를 지우는 것은 아니다.\
> 예: 공지는 악성 버전은 **삭제**했고, 정당하게 yank돼 있던 버전은 **복원**했다고 적는다.

---

## 출처

### 1차 출처 (릴리스 노트 · 공식 블로그 · 프로젝트 문서)

| # | 제목 | URL | 발행일 |
|---|------|-----|--------|
| 1 | rust-lang/rust — RELEASES.md (1.86.0 ~ 1.98.1) | https://github.com/rust-lang/rust/blob/master/RELEASES.md | 상시 갱신 (2026-09-20 열람) |
| 2 | Rust Blog — Enabling the next iteration of the borrow checker on nightly (Polonius Alpha) | https://blog.rust-lang.org/2026/08/04/enabling-polonius-alpha-on-nightly/ | 2026-08-04 |
| 3 | Rust Blog — Enabling the next-generation trait solver on nightly | https://blog.rust-lang.org/2026/08/21/enabling-next-solver-on-nightly/ | 2026-08-21 |
| 4 | Rust Blog — Supply chain attack on arrayref | https://blog.rust-lang.org/2026/08/20/supply-chain-attack-on-arrayref/ | 2026-08-20 |
| 5 | Rust Blog — Be alert: targeted attacks on prominent Rustaceans | https://blog.rust-lang.org/2026/09/17/targeted-attacks/ | 2026-09-17 |
| 6 | Rust Blog 피드 (릴리스·공지 목록과 날짜) | https://blog.rust-lang.org/feed.xml | 2026-09-20 열람 |
| 7 | Rust Project Goals 2026 — Goals | https://goals.rust-lang.org/2026/goals.html | 2026-09-20 열람 |
| 8 | Rust Project Goals 2026 — 개요(81개 목표) | https://goals.rust-lang.org/2026/index.html | 2026-09-20 열람 |
| 9 | Rust Blog — Rust 1.98.1 (vtable miscompile 수정) | https://blog.rust-lang.org/2026/09/03/Rust-1.98.1/ | 2026-09-03 |

### 2차 출처

본문의 사실 주장에 쓴 2차 출처는 **없다**. 검색은 1차로 가는 길잡이로만 썼다.

### 확인하지 못해 뺀 것

- **2024 다음 에디션** — `doc.rust-lang.org/edition-guide`에서 2024 이후 에디션의 챕터나 일정 서술을 찾지 못했다. 그래서 "다음 에디션은 2027"이라고 적지 않았다.
- **`gen` 블록·`Send` 경계 전파의 안정화 여부** — 1.86~1.98.1 릴리스 노트에서 해당 항목을 찾지 못했다. "아직 안 됐다"가 아니라 "**찾지 못했다**"로 적어 둔다.
- **Maintainers in Residence 본문** — 제목과 날짜만 피드에서 확인했고 글을 열지 않았다. 그래서 누가·무엇을 맡는지는 적지 않았다.
- **2025~2026년의 채택률·설문 수치** — 원문 05편이 적은 Stack Overflow 2025 설문 이후의 값은 1차로 확인하지 못해 적지 않았다.
- **Rust Foundation·Linux 커널 쪽 진행** — 이 기간의 1차 자료를 확인하지 못해 적지 않았다.

---

> 이 문서는 여기서 멈춘다. 2026-09-20 이후의 일은 다시 「그 뒤」가 필요하다.
