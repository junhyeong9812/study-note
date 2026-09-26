# rust/syntax/01 — `cargo` 프로젝트 구조·`main`·크레이트·모듈 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [The Rust Reference](https://doc.rust-lang.org/reference/) 의 Crates and source files · Modules · Visibility 절 ·
> [The Cargo Book](https://doc.rust-lang.org/cargo/) 의 Package Layout · Manifest 절. 이 머신에 설치된 `rust-docs` 판(1.92.0)을 열어 확인했다.
> **실행 검증** — 이 문서의 모든 출력·에러는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `cargo 1.92.0 (344c4567c 2025-10-21)` 에서\
> 실제로 돌려 얻은 것이다. `x86_64-unknown-linux-gnu`. 이 주제만 `cargo` 가 필요하고, 02\~04는 `rustc` 단독으로 검증했다.
> **버전** — 에디션 2024는 1.85.0(2025-02-20)부터 안정. **`cargo 1.92.0`의 `cargo new` 기본 에디션은 2024**이고\
> **`rustc` 를 `--edition` 없이 부르면 2015**다(둘 다 실측). 이 묶음의 본문 기준 에디션은 **2021**이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**크레이트는 책 한 권이고, 모듈은 그 책의 장·절이고, 패키지는 그 책을 내는 출판 계약서다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 출판 계약서 한 장 | `Cargo.toml` — 패키지 하나의 이름·판(에디션)·의존성 |
| 책 한 권 | **크레이트** — `rustc` 가 한 번에 통째로 읽어 결과물 하나를 내는 단위 |
| 책의 첫 장 | **크레이트 루트** — `src/main.rs`(바이너리) 또는 `src/lib.rs`(라이브러리) |
| 책의 장·절 | **모듈** — `mod` 로 만든 이름 공간. 파일로 나뉘어도 같은 책이다 |
| 목차에 장 제목을 올리는 것 | `mod 이름;` — **목차에 안 올린 원고는 책에 안 들어간다** |
| 장을 공개할지 말지 | `pub` · `pub(crate)` — 기본은 비공개 |

- 출판사에 넘기는 것은 **원고 뭉치가 아니라 「첫 장」 하나**다.\
  `cargo` 는 `rustc` 에게 `src/main.rs` **한 파일만** 건넨다.
- 나머지 원고는 첫 장의 목차(`mod`)를 따라 **컴파일러가 스스로 찾아 읽는다.**
- 그래서 `src/` 에 원고를 놔둬도 **목차에 안 올렸으면 그 파일은 존재하지 않는 것과 같다.**\
  문법이 완전히 깨진 파일을 놔둬도 빌드가 통과한다(「어디서 틀리나」 1번 — 실측).

```text
패키지 (Cargo.toml 한 장)
   |
   +-- 크레이트 A : src/main.rs  --> 실행 파일 target/debug/이름
   |        |
   |        +-- mod greet;          --> src/greet.rs 를 찾아 읽는다
   |                 |
   |                 +-- pub mod polite;  --> src/greet/polite.rs
   |
   +-- 크레이트 B : src/lib.rs   --> 라이브러리 target/debug/lib이름.rlib
```

**언어도 똑같은 구조다.** 한 패키지 안에 책이 둘일 수 있고(A·B), 둘은 **서로 다른 크레이트**라
A가 B의 `pub(crate)` 를 못 본다(「어디서 틀리나」 3번 — 실측으로 확인했다).

> **크레이트(crate)** — `rustc` 호출 한 번이 처리하는 소스 전체이자 결과물 하나의 단위.\
> 예: `src/main.rs` 와 거기서 `mod` 로 딸려 온 파일 전부가 합쳐서 크레이트 하나다.

> **패키지(package)** — `Cargo.toml` 하나가 관리하는 단위. 크레이트를 **여럿** 담을 수 있다.\
> 예: `src/main.rs` 와 `src/lib.rs` 가 같이 있으면 패키지는 하나, 크레이트는 둘이다.

> **모듈(module)** — 크레이트 **안**의 이름 공간. 파일과 1:1일 필요도 없다.\
> 예: `mod greet { ... }` 처럼 중괄호로 그 자리에서 만들 수도 있다.

> **에디션(edition)** — 같은 컴파일러가 소스를 읽는 「판」. 2015·2018·2021·2024가 있다.\
> 예: `gen` 은 2021에서는 변수 이름이지만 2024에서는 예약어다(실측).

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. `cargo new` 가 만든 파일 넷 중 **무엇이 컴파일러에게 가고 무엇이 안 가는가.**
2. `mod greet;` 한 줄은 **어느 파일을 어떤 규칙으로 찾는가** — 못 찾거나 둘 다 있으면 무슨 말을 하는가.
3. **크레이트 경계는 어디인가** — `pub`/`pub(crate)`·`crate::`·에디션이 전부 그 경계 위에서 정해진다.

## 동작 방식

### (1) `cargo new` 가 만드는 것 — 그리고 안 만드는 것

**언제 쓰나** — 새 프로젝트를 시작할 때. 딱 한 번이지만 여기서 정해진 것이 계속 따라다닌다.

```text
$ cargo new hello
    Creating binary (application) `hello` package

hello/
  +-- .git/          <- git 저장소까지 만든다 (--vcs none 으로 끌 수 있다)
  +-- .gitignore     <- 내용은 "/target" 한 줄
  +-- Cargo.toml     <- 계약서
  +-- src/
        +-- main.rs  <- 크레이트 루트

여기에 없는 것:  Cargo.lock 과 target/   <- 아직 빌드를 안 했으니 없다
```

`cargo build` 나 `cargo run` 을 한 번 돌리면 그때 생긴다.

```text
빌드 전                       빌드 후
  Cargo.toml                   Cargo.toml
  src/main.rs                  src/main.rs
                               Cargo.lock    <- 의존성이 0개여도 생긴다
                               target/       <- 산출물. .gitignore 로 이미 제외돼 있다
```

그림 해설 (한 단계씩):

- `Cargo.toml` 은 **내가 쓰는 것**이고 `Cargo.lock` 은 **cargo 가 쓰는 것**이다.
- 의존성이 하나도 없어도 `Cargo.lock` 은 생긴다 — 자기 자신(`name = "hello"`)이 첫 항목이다(실측).
- `target/` 은 **저장소에 넣지 않는다.** `cargo new` 가 만든 `.gitignore` 가 이미 막고 있다.

비용 — `cargo new` 자체는 파일 몇 개 쓰는 것뿐. 첫 `cargo build` 에서 `target/` 이 생기며 용량을 먹는다.

### (2) `mod` 가 파일을 찾는 규칙 — 후보는 정확히 둘이다

**언제 쓰나** — 코드를 파일로 쪼갤 때마다.

```text
크레이트 루트 src/main.rs 에서  mod greet;  라고 쓰면

   후보 1 : src/greet.rs
   후보 2 : src/greet/mod.rs

  둘 다 없다  ->  error[E0583] file not found for module `greet`
  둘 다 있다  ->  error[E0761] found at both ...
  하나만 있다 ->  그 파일이 greet 모듈의 본문이 된다
```

모듈 안에서 또 `mod` 를 쓰면 **그 모듈 이름의 폴더** 밑을 본다.

```text
src/main.rs         mod greet;            -> src/greet.rs
src/greet.rs        pub mod polite;       -> src/greet/polite.rs
                                             (greet.rs 와 greet/ 폴더가 나란히 있다)
```

그림 해설 (한 단계씩):

- 파일 이름이 곧 모듈 이름이다 — 파일 안에 모듈 이름을 다시 적지 않는다.
- `mod` 를 **안 쓰면 그 파일은 컴파일되지 않는다.** 경고도 없다(「어디서 틀리나」 1번).
- 2018 에디션부터 `greet.rs` 쪽이 권장 형태다. `greet/mod.rs` 도 여전히 되지만 **같이 두면 E0761**이다.

비용 — 없음. 규칙이다. 다만 **파일 배치가 곧 모듈 트리**라 나중에 옮기면 경로가 전부 바뀐다.

### (3) 경로 — `crate::` · `super::` · `self::`

**언제 쓰나** — 다른 모듈의 것을 부를 때마다.

```text
크레이트 루트 (= crate)
   |
   +-- fn top()                 crate::top
   |
   +-- mod greet                crate::greet
           |
           +-- fn hello()       crate::greet::hello   =  self::hello  (greet 안에서 보면)
           |                                          =  super::greet::hello (polite 안에서 보면)
           +-- mod polite
                   |
                   +-- fn hello()   crate::greet::polite::hello
                                 =  self::hello        (polite 안에서)
                                 =  super::polite::hello (greet 안에서)
```

실행으로 확인한 것 — `greet::hello` 안에서 `super::top()` 과 `self::polite::hello()` 가 둘 다 불렸다(3-answer 3번).

그림 해설 (한 단계씩):

- `crate::` 는 **이 크레이트의 루트**에서 시작하는 절대 경로다. 파일 위치와 무관하다.
- `super::` 는 부모 모듈 한 칸 위. `self::` 는 지금 이 모듈.
- `use` 는 **경로에 별명을 붙이는 것**일 뿐이다 — 없어도 전체 경로로 다 부를 수 있다.

비용 — 없음. `use` 는 컴파일 타임 이름 해석이고 런타임에 아무 일도 안 한다.

### (4) 크레이트가 컴파일 단위라는 것 — `cargo build -v` 가 증거다

**언제 쓰나** — 「이 파일은 왜 다시 컴파일되지?」·「왜 이건 안 보이지?」를 판단할 때.

```text
$ cargo build -v
 Running `.../rustc --crate-name modtest --edition=2024 src/main.rs
          --crate-type bin --emit=dep-info,link -C debuginfo=2 ...`
                                 ^^^^^^^^^^^
                     넘긴 소스 파일은 이것 하나뿐이다

(원래 한 줄인 것을 읽기 쉽게 접었고, 긴 절대 경로는 ... 로 줄였다)
```

`src/greet.rs` 도 `src/greet/polite.rs` 도 **명령줄에 없다.**
컴파일러가 `mod` 를 따라 스스로 열어 읽는다.

```text
  cargo 가 하는 일                     rustc 가 하는 일
  +--------------------------+        +-----------------------------+
  | Cargo.toml 을 읽는다      |  --->  | src/main.rs 를 연다          |
  | 에디션을 --edition 로 준다 |        | mod 를 만나면 파일을 더 연다  |
  | 의존성을 -L 로 붙인다      |        | 전부 합쳐 크레이트 하나로 낸다 |
  +--------------------------+        +-----------------------------+
```

그림 해설 (한 단계씩):

- **에디션은 컴파일러 플래그**다. `Cargo.toml` 의 `edition` 은 그 플래그로 번역될 뿐이다.
- 그래서 `cargo` 없이 `rustc --edition 2021 src/main.rs` 로도 **같은 결과**가 나온다(실측).
- 반대로 `rustc src/main.rs` 처럼 플래그를 빼면 **에디션 2015로 읽힌다** — cargo 로 돌던 코드가 깨질 수 있다.

비용 — 크레이트가 컴파일 단위이므로 **한 글자만 고쳐도 그 크레이트는 통째로 다시 컴파일된다.**\
큰 프로젝트를 여러 크레이트로 쪼개는 이유가 이것이다(자세한 것은 목록의 **46번 주제**).

### (5) `fn main` 의 반환 타입 — `()` 말고 `Result` 도 된다

**언제 쓰나** — `?` 를 `main` 에서 쓰고 싶을 때.

```text
fn main() { ... }                        반환 타입 생략 = -> ()
fn main() -> Result<(), E> { ... }       E 가 Debug 를 구현하면 된다
fn main() -> i32 { 7 }                   error[E0277] Termination 미구현

  Ok(())  로 끝나면   ->  종료 코드 0, 아무것도 안 찍는다
  Err(e)  로 끝나면   ->  표준 에러에 "Error: {e:?}" 를 찍고 종료 코드 1
```

실측 출력(`ex.rs 01-c`) — 표준 출력과 표준 에러가 갈린다.

```text
$ ./ex
n = 42                                          <- 표준 출력
Error: ParseIntError { kind: InvalidDigit }     <- 표준 에러
$ echo $?
1
```

그림 해설 (한 단계씩):

- 찍히는 형식은 `Display` 가 아니라 **`Debug`**(`{:?}`)다 — `ParseIntError { kind: InvalidDigit }` 가 그 증거다.
- 그래서 사용자에게 보여 줄 메시지를 `main` 의 `Err` 로 흘리면 **개발자용 형식**이 그대로 나간다.
- 반환 가능한 타입은 `Termination` 을 구현한 것뿐이다 — `()`·`Result<T, E>`·`ExitCode`.

비용 — 없음. 편의 문법이고, `?` 를 `main` 에서 쓸 수 있게 해 준다(정본은 [목록의 **22번 주제**](../22-result-question-mark-and-from/)).

## 문법 — 형태와 규칙

직접 쓴 최소 예제다. 묻는 것 하나만 남겼다.

### 파일 배치와 모듈 트리

```text
src/main.rs          mod greet;   use greet::polite::hello;   fn main() { hello(); }
src/greet.rs         pub mod polite;   pub(crate) fn internal() {}
src/greet/polite.rs  pub fn hello() {}
```

- `mod` = **이 모듈을 이 크레이트에 편입한다**(목차 등재).
- `use` = **긴 경로에 짧은 이름을 준다**(편입이 아니다). `use ... as p;` 로 별칭도 된다.
- `pub` 은 **한 칸씩만** 연다 — `polite` 가 `pub` 이어도 그 안의 `hello` 가 `pub` 이 아니면 밖에서 못 쓴다.

### 가시성 네 단계

| 표기 | 어디까지 보이나 |
|---|---|
| (없음) | 정의된 모듈과 **그 자손** 모듈 |
| `pub(crate)` | 이 **크레이트** 전체. 다른 크레이트에서는 안 보인다 |
| `pub(super)` | 부모 모듈까지 |
| `pub` | 이 크레이트를 쓰는 **다른 크레이트**까지 |

### `cargo` 하위 명령 — 무엇을 만드나

| 명령 | 만드는 것 | 언제 |
|---|---|---|
| `cargo check` | `target/debug/deps/*.rmeta` — **실행 파일 없음** | 타입·빌림 오류만 빨리 보고 싶을 때 |
| `cargo build` | `target/debug/<이름>` · `lib<이름>.rlib` | 실제로 돌릴 것을 만들 때 |
| `cargo run` | build + 곧바로 실행 | 개발 중 대부분 |
| `cargo build --release` | `target/release/<이름>` | 최적화 빌드. **오버플로 동작이 바뀐다**([03번](../03-primitive-types-and-integer-overflow/)) |
| `cargo test` | 테스트 바이너리 | 정본은 목록의 **58번 주제** |

실측 — `cargo check` 뒤 `target/debug/` 에 실행 파일이 없고 `.rmeta` 만 있었다(3-answer 2번).

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다. 넷 중 둘은 **에러 없이 조용히 지나간다.**

### 1. `mod` 에 안 올린 파일은 컴파일되지 않는다 — 경고도 없다

```text
src/
  main.rs      mod greet;   만 있다
  greet.rs
  greet/polite.rs
  orphan.rs    <- 내용: "이것은 러스트 문법이 아니다 @@@ !!! ((("

$ cargo build
   Compiling modtest v0.1.0 (...)
    Finished `dev` profile [unoptimized + debuginfo] target(s) in 0.08s
```

- **문법이 통째로 깨진 파일이 `src/` 에 있는데 빌드가 성공한다.**
- 컴파일러는 `orphan.rs` 를 **열어 보지도 않았다.** `mod orphan;` 이 없으니 존재를 모른다.
- 반대 방향의 사고가 더 흔하다 — **파일을 만들었는데 왜 안 불리지?** `mod` 한 줄을 안 썼기 때문이다.
- 파일 이름만 보고 「자동으로 잡히겠지」라고 읽으면 여기서 막힌다. Rust 에는 **자동 수집이 없다.**

### 2. `rustc` 와 `cargo` 의 기본 에디션이 다르다

```text
$ cargo new hello                 -> Cargo.toml 에 edition = "2024"
$ rustc ex.rs                     -> 에디션 2015 로 읽는다
```

실측으로 가른 방법 — `dyn` 은 2015에서 식별자고 2018부터 키워드다.

```text
$ rustc ex.rs        # let dyn = 3;
3                                         <- 통과했다 = 2015 다

$ rustc --edition 2018 ex.rs
error: expected identifier, found keyword `dyn`
```

- 그래서 **`cargo` 로 돌던 코드를 `rustc` 로 옮기면 깨질 수 있다.** 반대도 마찬가지다.
- 이 묶음의 02\~04는 전부 `rustc --edition 2021` 로 돌렸다. 플래그를 빼면 같은 결과를 보증하지 않는다.

### 3. 같은 패키지의 `main.rs` 와 `lib.rs` 는 **다른 크레이트**다

```text
src/lib.rs    pub fn twice(n: i32) -> i32 { n * 2 }
              pub(crate) fn thrice(n: i32) -> i32 { n * 3 }
src/main.rs   fn main() { println!("{}", both::thrice(14)); }
```

```text
warning: function `thrice` is never used
 --> src/lib.rs:3:15
  = note: `#[warn(dead_code)]` (part of `#[warn(unused)]`) on by default

error[E0603]: function `thrice` is private
 --> src/main.rs:3:26
```

- `main.rs` 에서 라이브러리를 부를 때 **`crate::` 가 아니라 패키지 이름**(`both::`)을 쓴다.\
  `crate::` 는 **지금 컴파일 중인 크레이트**를 가리키는데, `main.rs` 의 크레이트는 라이브러리가 아니다.
- `pub(crate)` 는 라이브러리 크레이트 안까지만이므로 **바이너리 쪽에서는 안 보인다**(E0603).
- 경고가 하나 더 붙은 것이 증거다 — 라이브러리를 혼자 컴파일하는 동안 `thrice` 를 아무도 안 쓰므로 `dead_code` 가 뜬다.\
  **「다른 크레이트가 쓰고 있다」를 컴파일러가 모른다**는 뜻이고, 그게 곧 컴파일 단위가 갈렸다는 증거다.

### 4. `Cargo.toml` 의 `edition` 한 줄이 코드를 깨뜨린다

```text
$ grep edition Cargo.toml
edition = "2024"
$ cargo build
error: expected identifier, found reserved keyword `gen`
 --> src/main.rs:2:9
  |
2 |     let gen = 3;
  |         ^^^ expected identifier, found reserved keyword
```

```text
$ grep edition Cargo.toml
edition = "2021"
$ cargo run -q
gen = 3
```

- 소스는 **한 글자도 안 바꿨다.** 계약서 한 줄만 바꿨다.
- 더 위험한 쪽은 **에러가 안 나면서 의미가 바뀌는 것**이다(「구현 세부사항 대 언어 보장」 참조).

## 구현 세부사항 대 언어 보장

이 갈래에서 「구현 세부사항」은 **에디션·툴체인 버전·플랫폼에 달린 것**이다.

| 사실 | 누가 정하나 | 확인 방법 |
|---|---|---|
| `mod x;` 가 `x.rs` 와 `x/mod.rs` 를 본다 | **언어**(Reference, Modules) | E0583 메시지가 두 후보를 그대로 말한다 |
| `crate::`·`super::`·`self::` 의 뜻 | **언어** | 실행으로 확인 |
| `pub`/`pub(crate)` 의 경계 | **언어** | E0603 |
| **`cargo new` 의 기본 에디션이 2024** | **cargo 버전**(1.92.0) | `cargo new` 뒤 `Cargo.toml` 을 읽는다 |
| **`rustc` 의 기본 에디션이 2015** | **하위 호환 약속** | `--edition` 없이 `dyn` 을 식별자로 써 본다 |
| `target/` 의 내부 배치·해시 파일명 | **cargo 구현** | 버전이 바뀌면 바뀐다. 의존하지 않는다 |
| `cargo new` 가 `.git/` 을 만드는 것 | **cargo 구현** | `--vcs none` 으로 끌 수 있다 |
| `Cargo.lock` 의 `version = 4` | **cargo 구현** | 포맷 판번호다. 손으로 고치지 않는다 |

★ **「내 머신에서 됐다」가 「에디션 무관하게 된다」가 아니다.**\
이 묶음이 에디션을 머리말에 못박는 이유다. 에디션이 실제로 무엇을 바꾸는지는 목록의 **47번 주제**가 정본이다.

## 언제 쓰고 언제 안 쓰나

| 상황 | `cargo` | `rustc` 단독 |
|---|---|---|
| 의존성이 하나라도 있다 | 쓴다 | 못 쓴다(`-L`·`--extern` 을 손으로 줘야 한다) |
| 에디션을 고정하고 싶다 | `Cargo.toml` 한 줄 | 매번 `--edition` |
| 한 파일짜리 실험·이 노트의 예제 | 과하다 | **이쪽이 낫다** |
| 디버그/릴리스를 오가며 대조 | `--release` | `-O`·`-C overflow-checks=…` 로 더 잘게 |
| 테스트·문서 테스트 | 쓴다 | 사실상 못 쓴다 |

판단 규칙 두 줄.

- **의존성이 생기는 순간 `cargo`** 로 간다. 그 전까지 `rustc` 단독이 빠르고 통제가 쉽다.
- **`rustc` 로 갈 때는 `--edition` 을 반드시 명시한다.** 기본값이 2015라서 조용히 다르게 읽힌다.

## 핵심 문장

- 컴파일 단위는 파일이 아니라 **크레이트**다 — `cargo build -v` 가 `rustc` 에게 넘기는 소스는 **크레이트 루트 한 파일**뿐이다.
- `mod x;` 는 목차 등재이고 후보 파일은 **정확히 둘**(`x.rs`·`x/mod.rs`)이다. 둘 다 없으면 E0583, 둘 다 있으면 E0761.
- **`mod` 로 안 올린 `.rs` 파일은 컴파일되지 않는다** — 경고도 에러도 없다. Rust 에 자동 수집은 없다.
- 한 패키지 안의 `main.rs` 와 `lib.rs` 는 **다른 크레이트**이고, 그래서 `pub(crate)` 가 서로 안 보인다.
- `fn main` 은 `()` 말고 `Result` 도 돌려줄 수 있고, `Err` 는 **`Debug` 형식**으로 표준 에러에 찍히며 종료 코드는 1이다.
- **에디션은 컴파일러 플래그**다. `cargo new` 는 2024, `rustc` 기본은 2015 — 두 값이 다르다.

## 관련 자료

- [`../README.md`](../README.md) — Rust 문법·API 주제 목록(이 주제는 01번)
- [`../../언어-특성/README.md`](../../언어-특성/README.md) — **그쪽은 「왜 Rust 를 고르는가」**(소유권 모델의 논증과 청구서)까지,\
  **여기는 「그 코드를 어느 파일에 두고 컴파일러가 어떻게 읽는가」부터**다. 소유권은 이 문서에 한 줄도 없다.
- [`../../../../../history/rust/05-생태계-도구.md`](../../../../../../history/rust/05-생태계-도구.md) — **그쪽은 cargo·crates.io 가 왜 그렇게 생겼나의 연혁**,\
  **여기는 지금 내 손에서 무엇이 만들어지나**다.
- [`../../../../../history/rust/02-에디션.md`](../../../../../../history/rust/02-에디션.md) — 에디션 제도가 **왜** 생겼나는 거기. 여기는 **기본값이 다르다는 실측**만.
- [**02번 주제**](../02-bindings-mut-and-shadowing/)(변수 바인딩·`mut`·섀도잉) — 이 주제 다음에 온다
- 목록의 **45번 주제**(모듈 시스템 전수) — `pub(in path)`·재수출(`pub use`)·가시성 설계는 거기가 정본
- 목록의 **46번 주제**(크레이트·feature·워크스페이스) · 목록의 **47번 주제**(에디션 2021 대 2024)
- [목록의 **22번 주제**](../22-result-question-mark-and-from/)(`Result` 와 `?`) — `main` 이 `Result` 를 돌려주는 이유의 정본
- 목록의 **58번 주제**(테스트) — `cargo test` 와 파일 배치

## 용어 풀이

- **크레이트(crate)** — `rustc` 호출 한 번이 처리하는 소스 전체이자 결과물 하나. 바이너리 크레이트와 라이브러리 크레이트가 있다.
- **크레이트 루트(crate root)** — 그 크레이트의 첫 파일. `src/main.rs` 또는 `src/lib.rs`.
- **패키지(package)** — `Cargo.toml` 하나가 관리하는 단위. 크레이트를 여럿 담을 수 있다.
- **모듈(module)** — 크레이트 안의 이름 공간. `mod` 로 만든다.
- **매니페스트(manifest)** — `Cargo.toml`. 이름·버전·에디션·의존성을 사람이 적는 파일.
- **잠금 파일(lock file)** — `Cargo.lock`. 실제로 고른 의존성 버전을 cargo 가 적는 파일.
- **에디션(edition)** — 같은 컴파일러가 소스를 읽는 판. 2015·2018·2021·2024.
- **가시성(visibility)** — 어느 범위에서 이름이 보이는가. 기본은 비공개.
- **`rlib`** — 라이브러리 크레이트의 컴파일 산출물. `target/debug/lib이름.rlib`.
- **`rmeta`** — 타입 정보만 담은 산출물. `cargo check` 가 이것만 만든다.
- **바이너리 크레이트 / 라이브러리 크레이트** — `fn main` 이 있어 실행되는 쪽 / 남이 `use` 해 쓰는 쪽.

---

## 더 들어가면

- `cargo new --lib` 는 `src/lib.rs` 를 만들고, 그 안에 `#[cfg(test)] mod tests` 예제까지 넣는다(실측).\
  이 패키지에서 `cargo run` 을 하면 `error: a bin target must be available for cargo run` 이다.
- `cargo new --edition 2021` 로 처음부터 판을 고를 수 있다(실측으로 `edition = "2021"` 확인).
- `Cargo.lock` 의 `version = 4` 는 **잠금 파일 포맷의 판번호**이지 패키지 버전이 아니다.
- `mod` 는 파일 없이 중괄호로도 만든다 — `mod greet { pub fn hello() {} }`.\
  이때는 파일 탐색 자체가 일어나지 않으므로 E0583·E0761 이 성립하지 않는다.
- `target/` 을 저장소에 넣지 않는 이유는 용량만이 아니다. 절대 경로와 툴체인 해시가 박혀 있어 **다른 머신에서 재사용되지 않는다**.
