# rust/syntax/01 — `cargo` 프로젝트 구조·`main`·크레이트·모듈 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **컴파일러가 무엇을 말하는지**를 맞힐 수 있는지 묻는다.
> 답을 모르겠으면 **던져 보라.** `cargo new /tmp/p && cargo run --manifest-path /tmp/p/Cargo.toml` 이면 된다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `cargo new` 직후의 폴더에 무엇이 있는가 (예측)

```bash
cargo new hello
```

- 이 명령이 만든 파일·폴더를 전부 셀 수 있는가?
- `Cargo.lock` 은 이 시점에 있는가, 없는가?
- `target/` 은 이 시점에 있는가, 없는가 — 그리고 언제 생기는가?
- `Cargo.toml` 의 `edition` 값은 무엇인가?

### 2. `mod greet;` 는 어느 파일을 찾는가 (예측)

```rust
// src/main.rs
mod greet;

fn main() { greet::hello(); }
```

- `src/` 에 아무 파일도 더 없을 때 컴파일러는 무슨 에러를 내는가 — **에러 번호와 도움말 문구**까지?
- 그 에러가 말하는 **후보 파일 경로 두 개**는 각각 무엇인가?
- `src/greet.rs` 와 `src/greet/mod.rs` 를 **둘 다** 만들면 무슨 일이 일어나는가?
- `src/greet.rs` 안에서 `pub mod polite;` 를 쓰면 컴파일러는 어느 경로를 보는가?

### 3. 이 프로젝트는 빌드에 성공하는가 (예측)

```text
src/main.rs        mod greet;  fn main() { greet::polite::hello(); }
src/greet.rs       pub mod polite;
src/greet/polite.rs  pub fn hello() { println!("hi"); }
src/orphan.rs      이것은 러스트 문법이 아니다 @@@ !!! (((
```

- `cargo build` 는 성공하는가, 실패하는가?
- 성공한다면 `orphan.rs` 에 대해 **경고라도** 나오는가?
- 이 결과에서 "Rust 가 소스 파일을 수집하는 방식"에 대해 무엇을 말할 수 있는가?
- 반대 방향의 사고 — "파일을 만들었는데 안 불린다"는 무엇을 빼먹은 것인가?

### 4. 이 프로그램의 출력을 예측하라 (예측)

```rust
// src/main.rs
mod greet;
pub fn top() { println!("  crate::top"); }
fn main() { greet::hello(); crate::top(); }

// src/greet.rs
pub mod polite;
pub fn hello() {
    println!("greet::hello");
    polite::hello();
    super::top();
    self::polite::hello();
}

// src/greet/polite.rs
pub fn hello() { println!("  greet::polite::hello"); }
```

- 출력은 몇 줄이고 무슨 순서인가?
- `greet.rs` 안에서 `super::` 는 어디를 가리키는가?
- `self::polite::hello()` 와 `polite::hello()` 는 다른 것인가?
- `crate::` 로 시작하는 경로는 무엇을 기준으로 삼는가 — 파일 위치인가, 모듈 트리인가?

### 5. `fn main` 이 `Result` 를 돌려주면 (예측)

```rust
use std::num::ParseIntError;

fn main() -> Result<(), ParseIntError> {
    let n: i32 = "42".parse()?;
    println!("n = {n}");
    let m: i32 = "사십이".parse()?;
    println!("m = {m}");
    Ok(())
}
```

- 표준 출력에 무엇이 찍히고 표준 에러에 무엇이 찍히는가 — **문자 그대로**?
- 종료 코드는 무엇인가?
- 찍히는 형식은 `Display`(`{}`)인가 `Debug`(`{:?}`)인가, 그 근거는 출력의 어느 부분인가?
- `fn main() -> i32 { 7 }` 은 컴파일되는가, 안 된다면 컴파일러가 요구하는 트레이트 이름은 무엇인가?

### 6. 크레이트 경계는 어디인가 (경계)

```rust
// src/lib.rs
pub fn twice(n: i32) -> i32 { n * 2 }
pub(crate) fn thrice(n: i32) -> i32 { n * 3 }

// src/main.rs
fn main() {
    println!("{}", both::twice(21));
    println!("{}", both::thrice(14));
}
```

- 이 패키지에 크레이트는 몇 개인가?
- `main.rs` 에서 라이브러리를 부를 때 왜 `crate::` 가 아니라 `both::` 인가?
- 둘째 줄은 컴파일되는가 — 안 된다면 **에러 번호**는?
- 이때 라이브러리 쪽에 **경고가 하나 더** 붙는데 무엇이고, 그 경고가 무엇을 증명하는가?

### 7. 컴파일 단위는 무엇인가 (왜)

- `cargo build -v` 가 보여 주는 `rustc` 명령줄에는 소스 파일이 **몇 개** 적혀 있는가?
- `src/greet.rs` 는 그 명령줄에 왜 없는가?
- 한 글자만 고쳤는데 프로젝트 전체가 다시 컴파일되는 현상은 이 사실과 어떻게 이어지는가?
- 큰 프로젝트를 여러 크레이트로 쪼개는 동기를 한 문장으로 말할 수 있는가?

### 8. 에디션의 기본값 (경계)

- `cargo 1.92.0` 의 `cargo new` 가 넣는 `edition` 값은 무엇인가?
- `rustc` 를 `--edition` 없이 부르면 어느 에디션으로 읽는가?
- 그 둘이 다르다는 것을 **한 줄짜리 프로그램으로** 증명하려면 무엇을 쓰겠는가?
- `Cargo.toml` 의 `edition` 한 줄만 바꿔서 깨지는 코드의 예를 하나 들 수 있는가?

### 9. `cargo check` 는 무엇을 만드는가 (왜)

- `cargo check` 뒤 `target/debug/` 에 실행 파일이 있는가?
- 대신 무엇이 만들어지며, 그 확장자는 무엇인가?
- `cargo check` 가 `cargo build` 보다 빠른 이유를 한 문장으로 말할 수 있는가?
- `cargo check` 로는 못 잡는 문제를 하나 들 수 있는가?

### 10. 다른 주제와 잇기 (연결)

- 이 노트의 02\~04번 예제는 `cargo` 를 안 쓰고 `rustc` 단독으로 돌렸다. 그때 **반드시 붙여야 하는 플래그**는 무엇인가?
- `cargo build --release` 가 바꾸는 것 중 **이 노트 03번에서 다루는 것**은 무엇인가?
- `pub`·`pub(crate)` 를 더 깊이 다루는 주제는 목록의 몇 번인가?
- 소유권·빌림은 이 주제에 한 줄도 안 나온다 — 그것을 다루는 두 자리는 각각 어디인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
