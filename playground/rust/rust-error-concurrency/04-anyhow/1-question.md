# rust/rust-error-concurrency/04 — anyhow 크레이트 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 숫자가 아닌 나이 문자열 (예측)

```rust
// 질문용 발췌
fn parse_age(s: &str) -> Result<u32> {
    let age: u32 = s.parse()
        .context("나이 파싱 실패")?;
    ensure!(age > 0, "나이는 0보다 커야 합니다: {}", age);
    ensure!(age < 200, "나이가 비현실적입니다: {}", age);
    Ok(age)
}
// parse_age("abc") 의 Err 를 {} 로 찍는다
```

- `parse_age("abc")` 의 에러 메시지는 어떤 꼴인가?
- 두 `ensure!` 중 실행되는 것이 있는가?

### 2. `"0"` 과 `"-5"` 를 넣으면 (예측)

```rust
// 질문용 발췌 — 위의 parse_age 그대로
let a = parse_age("0");
let b = parse_age("-5");
```

- `a` 와 `b` 는 각각 어느 단계에서 실패하고, 메시지는 무엇으로 시작하나?

### 3. Charlie 를 찾지 못한 뒤 (예측)

```rust
// 질문용 발췌
fn process_users() -> Result<()> {
    // ... Alice, Bob 생성 성공 ...
    let found = find_user(&users, "Alice")?;
    println!("  검색 결과: {}", found);
    let _not_found = find_user(&users, "Charlie");
    Ok(())
}
// main:
match process_users() {
    Ok(()) => println!("  완료"),
    Err(e) => println!("  에러: {}", e),
}
```

- `main` 이 이 `match` 에서 찍는 줄은 「완료」 쪽인가, 「에러」 쪽인가?

### 4. `with_context` 가 문자열 대신 클로저를 받는 까닭 (왜)
- 설명을 문자열이 아니라 `|| format!(…)` 클로저로 넘기면 무엇이 아껴지는가?

### 5. `bail!` 이 함수가 아니라 매크로인 까닭 (왜)
- `bail!` 을 보통 함수로 만들면 할 수 없는 일은 무엇인가?

### 6. `bail!` · `ensure!` 를 쓸 수 있는 자리 (경계)
- 반환 타입이 `()` 인 `main` 안에서 `ensure!` 를 쓰면 왜 맞지 않는가?

### 7. 한글 이름과 `name.len() <= 50` (경계)
- 한글 20글자 이름을 넣으면 이 검사를 통과하는가?

### 8. `Option` 을 `?` 로 흘려보내기 (연결)
- `find` 가 돌려준 `Option` 을 `Result` 를 돌려주는 함수에서 `?` 로 올리려면 무엇이 필요한가?

### 9. anyhow 와 thiserror 의 자리 (연결)
- 라이브러리의 공개 함수가 `anyhow::Result` 를 돌려주면 사용자 쪽에서 무엇이 불편한가?

## 실습

### 실습 1. 표준 라이브러리로 anyhow 스타일 에러 처리 흉내 내기

**만들 것** — 외부 크레이트 없이 anyhow 의 `Result` 별칭 · `Context` 트레이트 · `bail!` · `ensure!` 를 직접 만들고, 사용자 생성 · 검색 예제로 각 패턴을 보여 주는 프로그램을 만든다.

**준비물** — 외부 크레이트는 필요 없다. 실제 `anyhow` 크레이트(`cargo add anyhow`)를 표준 라이브러리로 흉내 낸 것이다.

**요구 조건**

1단계 — 에러 통과 확장 트레이트
1. `AnyError` 를 `Box<dyn Error>` 의 별칭으로, `Result<T>` 를 에러 쪽이 `AnyError` 인 `std::result::Result` 의 별칭으로 둔다.
2. `Context<T>` 트레이트에 `context(self, msg: &str)` 와 `with_context(self, f)`(`f` 는 `String` 을 돌려주는 `FnOnce` 클로저) 두 메서드를 둔다. 둘 다 `Result<T>` 를 돌려준다.
3. `E: Error + 'static` 인 `std::result::Result<T, E>` 에 `Context` 를 구현한다 — 에러이면 `"{메시지}: {원래 에러}"` 꼴 문자열을 에러로 바꾸고, `with_context` 는 클로저를 에러일 때만 부른다.
4. `Option<T>` 에 `Context` 를 구현한다 — `None` 이면 메시지(또는 클로저가 만든 문자열) 자체를 에러로 만든다.

2단계 — 매크로
5. `bail!(…)` 은 `format!` 과 같은 인자를 받아 그 문자열을 에러로 담아 즉시 `return Err(…)` 한다.
6. `ensure!(조건, …)` 은 조건이 거짓일 때 `bail!(…)` 한다.

3단계 — 사용 예
7. `User`(이름 `String`, 나이 `u32`)를 두고, `Debug` 를 derive 하며, `Display` 로 `이름(나이세)` 꼴로 보이게 한다.
8. `parse_age(s)` — 문자열을 `u32` 로 파싱하며 실패하면 `"나이 파싱 실패"` 맥락을 붙이고, 나이가 0 보다 커야 하며 200 보다 작아야 한다고 `ensure!` 로 검사한다(각 메시지에 나이를 넣는다).
9. `create_user(name, age_str)` — 이름이 비어 있지 않은지, 이름 길이가 50 이하인지 `ensure!` 로 검사한 뒤, `parse_age` 결과에 `with_context` 로 `"'{이름}' 사용자 생성 중"` 을 붙여 `User` 를 만든다.
10. `find_user(users, name)` — 이름이 같은 사용자를 찾고, 없으면 `context` 로 `"사용자를 찾을 수 없음"` 에러를 만든다.
11. `process_users()` — Alice(30) · Bob(25) 를 `?` 로 만들어 목록을 찍고, Alice 를 `?` 로 찾아 찍고, Charlie 검색 결과는 `?` 없이 받아 무시한 뒤 `Ok(())` 를 돌려준다.

4단계 — `main`
12. 정상(`"Alice"`, `"30"`) · 빈 이름(`""`, `"30"`) · 비현실적 나이(`"Alice"`, `"300"`) · 파싱 실패(`"Bob"`, `"abc"`) 네 경우를 차례로 `create_user` 에 넣고 `match` 로 성공 · 실패 메시지를 찍는다.
13. `vec!["apple", "banana"]` 의 `get(5)` 에 `context("인덱스 범위 초과")` 를 붙여 `{:?}` 로 찍는다.
14. `process_users()` 를 `match` 로 실행해 완료 · 에러를 찍고, 마지막에 anyhow 요약 줄들을 찍는다.

**시작 코드**

```rust
use std::fmt;
use std::error::Error;

// TODO: AnyError, Result<T> 별칭

trait Context<T> {
    // TODO: context, with_context 시그니처
}

impl<T, E: Error + 'static> Context<T> for std::result::Result<T, E> {
    // TODO: map_err 로 "{msg}: {e}" 를 에러로
}

impl<T> Context<T> for Option<T> {
    // TODO: None 을 메시지 에러로
}

macro_rules! bail {
    // TODO: format! 결과를 Err 로 즉시 반환
}

macro_rules! ensure {
    // TODO: 조건이 거짓이면 bail!
}

#[derive(Debug)]
struct User {
    name: String,
    age: u32,
}

impl fmt::Display for User {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}({}세)", self.name, self.age)
    }
}

fn parse_age(s: &str) -> Result<u32> {
    // TODO: parse + context, ensure 두 번
    todo!()
}

fn create_user(name: &str, age_str: &str) -> Result<User> {
    // TODO: ensure 두 번, parse_age + with_context
    todo!()
}

fn find_user(users: &[User], name: &str) -> Result<&User> {
    // TODO: iter().find(...) + context
    todo!()
}

fn process_users() -> Result<()> {
    // TODO: Alice, Bob 생성(?), 목록 출력, Alice 검색(?), Charlie 검색(무시)
    todo!()
}

fn main() {
    println!("=== anyhow 스타일 에러 처리 ===");
    println!();

    println!("=== 정상 케이스 ===");
    // TODO: create_user("Alice", "30") 을 match 로

    println!();
    println!("=== bail! 패턴 ===");
    // TODO: create_user("", "30")

    println!();
    println!("=== ensure! 패턴 ===");
    // TODO: create_user("Alice", "300")

    println!();
    println!("=== context() 패턴 ===");
    // TODO: create_user("Bob", "abc")

    println!();
    println!("=== Option에 context() ===");
    // TODO: items.get(5).context(...) 를 {:?} 로

    println!();
    println!("=== process_users ===");
    // TODO: process_users() 를 match 로

    println!();
    println!("=== anyhow 요약 ===");
    println!("  anyhow::Result<T> = Result<T, anyhow::Error>");
    println!("  .context('메시지'): 에러에 맥락 추가");
    println!("  bail!('메시지'): 즉시 에러 반환");
    println!("  ensure!(조건, '메시지'): 조건 불만족 시 에러");
    println!("  anyhow는 애플리케이션용, thiserror는 라이브러리용");
    println!("  anyhow::Error는 모든 Error를 감싸므로 패턴 매칭 불가");
    println!("  downcast_ref::<T>()로 원래 타입 복원 가능");
}
```

**확인 방법** — `rustc anyhow.rs && ./anyhow` 로 컴파일해 돌리고, 네 경우의 성공 · 실패 메시지와 `process_users` 의 흐름이 요구 조건대로 나오는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
