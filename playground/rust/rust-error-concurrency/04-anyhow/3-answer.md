# rust/rust-error-concurrency/04 — anyhow 크레이트 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. `"나이 파싱 실패: <ParseIntError 메시지>"` — `ensure!` 는 하나도 실행되지 않는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

에러 메시지는 `나이 파싱 실패: ` 뒤에 `ParseIntError` 의 메시지가 붙은 한 줄이다.
`ParseIntError` 의 메시지는 `invalid digit found in string` 으로 안다(확인 필요).
두 `ensure!` 는 실행되지 않는다.

**왜 그런가**

`"abc"` 는 `u32` 로 파싱할 수 없어 `Err(ParseIntError)` 가 된다.
`.context("나이 파싱 실패")` 가 `map_err` 로 `"나이 파싱 실패: <원래 에러>"` 문자열 에러를 만든다.
`?` 가 그 자리에서 `parse_age` 를 끝내므로 아래 `ensure!` 줄까지 가지 않는다.
근거: 2-summary 「동작 방식 (3)」 · 「동작 방식 (2)」.

### 2. `"0"` 은 첫 `ensure!` 에서, `"-5"` 는 파싱 단계에서 실패한다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

`a` 는 `나이는 0보다 커야 합니다: 0` 이다.
`b` 는 `나이 파싱 실패: ` 로 시작한다.

**왜 그런가**

`"0"` 은 `u32` 로 파싱이 성공해 `age = 0` 이 되고, `ensure!(age > 0, …)` 가 거짓이라 `bail!` 이 그 메시지로 반환한다.
`"-5"` 는 부호 없는 `u32` 로 파싱할 수 없으므로 `context` 를 거쳐 파싱 실패 에러가 된다.
그래서 음수는 「0보다 커야」 검사에 닿지 못한다.
근거: 2-summary 「어디서 틀리나 7」 · 「동작 방식 (7)」.

### 3. 「완료」 쪽이 찍힌다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

`main` 은 `  완료` 를 찍는다.

**왜 그런가**

`find_user(&users, "Charlie")` 는 `None` 을 `context` 로 바꾼 `Err` 를 돌려준다.
하지만 `?` 를 붙이지 않고 `_not_found` 에 받기만 하므로 함수가 끝나지 않는다.
그다음 `Ok(())` 가 반환되어 `match` 의 `Ok(())` 갈래가 실행된다.
근거: 2-summary 「어디서 틀리나 6」 · 「동작 방식 (8)」.
(단, 이 흐름은 「어디서 틀리나 4」의 컴파일 문제가 없다는 전제 위에 있다.)

### 4. 성공할 때 설명 문자열을 만드는 비용

클로저는 `map_err` 안에서, 즉 에러일 때만 불린다.
그래서 `Ok` 일 때는 `format!` 으로 문자열을 만드는 일 자체가 일어나지 않는다.
이것이 지연 평가이고, 변수(사용자 이름)를 섞은 설명에 특히 쓸모 있다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 2」.

### 5. 자기를 쓴 함수를 그 자리에서 끝내는 일

`bail!` 은 `return Err(format!(…).into())` 로 펼쳐진다.
펼친 코드가 호출한 함수 본문 안에 들어가므로 `return` 이 **그 함수**를 끝낸다.
보통 함수는 자기 자신만 반환할 수 있을 뿐, 자기를 부른 함수를 대신 끝낼 수 없다.
`format!` 과 같은 가변 인자를 받는 것도 매크로이기에 쉽다.
근거: 2-summary 「동작 방식 (6)」.

### 6. 펼쳐진 `return Err(…)` 가 `()` 반환 타입과 맞지 않아서다

`ensure!` 는 `if !조건 { return Err(…); }` 로 펼쳐진다.
`main` 의 반환 타입이 `()` 이면 `Err(…)` 를 돌려줄 수 없어 타입이 맞지 않는다.
그래서 `bail!` · `ensure!` 는 `Result` 를 돌려주는 함수 안에서만 쓴다 — 원본이 `main` 에서는 `match` 로 결과를 받는 까닭이다.
팁처럼 `main` 이 `anyhow::Result` 를 돌려주게 하면 `main` 안에서도 쓸 수 있다.
근거: 2-summary 「문법 — 형태와 규칙」.

### 7. 통과하지 못한다

`len()` 은 글자 수가 아니라 UTF-8 바이트 수다.
한글 한 글자는 3바이트이므로 20글자는 60바이트이고, 60 > 50 이라 `ensure!` 가 거짓이 된다.
메시지는 `이름이 너무 깁니다: 60 글자` 처럼 바이트 수를 「글자」라고 적는다.
근거: 2-summary 「어디서 틀리나 5」.

### 8. `None` 을 에러로 바꾸는 단계 — `Option` 용 `context`

`?` 를 `Result` 반환 함수 안에서 쓰려면 올릴 값이 에러를 가진 `Result` 여야 한다.
`Option` 용 `context` 는 `ok_or_else` 로 `Some(v)` 를 `Ok(v)` 로, `None` 을 `Err("메시지")` 로 바꾼다.
그 뒤에 `?` 를 붙이면 된다.
감쌀 원래 에러가 없으므로 메시지 자체가 에러가 된다.
근거: 2-summary 「동작 방식 (5)」.

### 9. 에러 종류로 갈라 처리할 수 없다

`anyhow::Error` 는 모든 `Error` 를 감싸므로 사용자가 `match` 로 에러 종류를 가를 수 없다.
원래 타입을 꺼내려면 `downcast_ref::<T>()` 처럼 타입을 짐작해 되돌려야 한다.
그래서 라이브러리는 종류가 드러나는 에러(thiserror)를, 그 라이브러리를 쓰는 애플리케이션은 anyhow 를 쓰는 것이 관례다.
근거: 2-summary 「어디서 틀리나 1」 · 「언제 쓰고 언제 안 쓰나」.

## 실습 정답

### 실습 1. 표준 라이브러리로 anyhow 스타일 에러 처리 흉내 내기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 에러 통 별칭 | `type AnyError = Box<dyn Error>;` · `type Result<T> = …` |
| 2. 두 메서드를 가진 트레이트 | `trait Context<T>` 의 `context` · `with_context` |
| 3. `Result` 용 구현 | `impl<T, E: Error + 'static> Context<T> for std::result::Result<T, E>` 의 `map_err` · `format!("{}: {}", …)` |
| 4. `Option` 용 구현 | `impl<T> Context<T> for Option<T>` 의 `ok_or_else` |
| 5. 즉시 반환 매크로 | `macro_rules! bail` → `return Err(format!(…).into())` |
| 6. 조건 매크로 | `macro_rules! ensure` → `if !$cond { bail!(…); }` |
| 7. 사용자 모델 | `struct User` · `#[derive(Debug)]` · `impl fmt::Display for User` |
| 8. 나이 파싱 | `fn parse_age` 의 `.context("나이 파싱 실패")?` · `ensure!` 두 줄 |
| 9. 사용자 생성 | `fn create_user` 의 `ensure!` 두 줄 · `.with_context(|| format!("'{}' 사용자 생성 중", name))?` |
| 10. 사용자 검색 | `fn find_user` 의 `.find(…)` · `.context("사용자를 찾을 수 없음")` |
| 11. 여러 단계 흐름 | `fn process_users` 의 `create_user(…)?` · `find_user(&users, "Alice")?` · `let _not_found = …` |
| 12. 네 경우 시연 | `main` 의 `match create_user(…)` 네 블록 |
| 13. `Option` 시연 | `items.get(5).context("인덱스 범위 초과")` · `result.map(|v| *v)` |
| 14. 흐름 실행과 요약 | `match process_users()` · 요약 `println!` 들 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`rust/rust-error-concurrency/reference/anyhow.rs`

```rust
// [에러 처리 & 동시성] anyhow 크레이트
// 설명: anyhow 크레이트 패턴, Context, bail!, ensure!
// 팁: anyhow는 애플리케이션 코드에, thiserror는 라이브러리 코드에 적합하다. context()는 에러에 설명을 추가하여 디버깅을 쉽게 만든다. bail!은 Err(anyhow!(...))의 축약, ensure!는 조건 + bail의 축약이다. 실제 프로젝트에서는 main 함수에 anyhow::Result를 반환하게 하면 모든 에러가 깔끔하게 처리된다.

// anyhow 크레이트는 애플리케이션 수준 에러 처리를 간소화한다.
// 실제 사용 시: cargo add anyhow
// 여기서는 anyhow의 핵심 패턴을 표준 라이브러리로 시연한다.

// Display 구현용
use std::fmt;
// Error 트레이트 (모든 표준 에러의 베이스)
use std::error::Error;

// === anyhow::Error 역할을 하는 간단한 구현 ===
// 실제 anyhow는 Box<dyn Error + Send + Sync>를 감싸며 더 정교하다.
// 모든 Error를 동적 디스패치로 감싸는 별칭
type AnyError = Box<dyn Error>;
// anyhow::Result<T> = Result<T, anyhow::Error> 역할
type Result<T> = std::result::Result<T, AnyError>;

// === Context 패턴: 에러에 맥락 추가 ===
// Result/Option에 .context()를 붙일 수 있는 확장 트레이트
trait Context<T> {
    // 정적 메시지 추가
    fn context(self, msg: &str) -> Result<T>;
    // 동적 메시지 추가 (lazy 평가)
    fn with_context<F: FnOnce() -> String>(self, f: F) -> Result<T>;
}

// Result<T, E>에 대한 Context 구현 (E는 Error 트레이트 구현 필요)
impl<T, E: Error + 'static> Context<T> for std::result::Result<T, E> {
    fn context(self, msg: &str) -> Result<T> {
        // map_err로 에러를 변환: 메시지를 앞에 붙임
        self.map_err(|e| {
            let msg = format!("{}: {}", msg, e);
            // String을 Box<dyn Error>로 자동 변환
            msg.into()
        })
    }

    fn with_context<F: FnOnce() -> String>(self, f: F) -> Result<T> {
        // 클로저로 메시지 생성: 에러 발생 시에만 호출되어 비용 절약
        self.map_err(|e| {
            let msg = format!("{}: {}", f(), e);
            msg.into()
        })
    }
}

// Option<T>에 대한 Context: None을 에러로 변환
impl<T> Context<T> for Option<T> {
    fn context(self, msg: &str) -> Result<T> {
        // None이면 메시지를 에러로 만들어 Err 반환
        self.ok_or_else(|| msg.into())
    }

    fn with_context<F: FnOnce() -> String>(self, f: F) -> Result<T> {
        self.ok_or_else(|| f().into())
    }
}

// === bail! 패턴 ===
// Err(...)를 즉시 반환하는 매크로 (anyhow::bail!과 동등)
macro_rules! bail {
    ($($arg:tt)*) => {
        // format! 결과를 Err로 감싸 반환
        return Err(format!($($arg)*).into())
    };
}

// === ensure! 패턴 ===
// 조건이 거짓이면 bail! (assert와 비슷하지만 패닉 대신 Err 반환)
macro_rules! ensure {
    ($cond:expr, $($arg:tt)*) => {
        if !$cond {
            bail!($($arg)*);
        }
    };
}

// === 사용 예시 ===
// 사용자 도메인 모델
#[derive(Debug)]
struct User {
    name: String,
    age: u32,
}

// 사용자 친화적 표시 형식
impl fmt::Display for User {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}({}세)", self.name, self.age)
    }
}

// 나이 파싱: context와 ensure 패턴 시연
fn parse_age(s: &str) -> Result<u32> {
    // ?로 ParseIntError를 받고, context로 의미 부여
    let age: u32 = s.parse()
        .context("나이 파싱 실패")?;

    // 0 검증: 거짓이면 즉시 Err 반환
    ensure!(age > 0, "나이는 0보다 커야 합니다: {}", age);
    // 상한 검증
    ensure!(age < 200, "나이가 비현실적입니다: {}", age);

    Ok(age)
}

// 사용자 생성: 여러 ensure와 with_context 결합
fn create_user(name: &str, age_str: &str) -> Result<User> {
    // 이름 비어있는지 검증
    ensure!(!name.is_empty(), "이름이 비어있습니다");
    // 이름 길이 검증
    ensure!(name.len() <= 50, "이름이 너무 깁니다: {} 글자", name.len());

    // with_context: 에러에 동적 컨텍스트 (사용자 이름) 추가
    let age = parse_age(age_str)
        .with_context(|| format!("'{}' 사용자 생성 중", name))?;

    Ok(User {
        name: name.to_string(),
        age,
    })
}

// 사용자 검색: Option -> Result 변환에 context 사용
fn find_user(users: &[User], name: &str) -> Result<&User> {
    users.iter()
        .find(|u| u.name == name)
        // None이면 "사용자를 찾을 수 없음" 에러로 변환
        .context("사용자를 찾을 수 없음")
}

// 여러 작업을 ?로 결합한 흐름
fn process_users() -> Result<()> {
    // ?로 에러 발생 시 즉시 반환되는 흐름
    let users = vec![
        create_user("Alice", "30")?,
        create_user("Bob", "25")?,
    ];

    println!("  생성된 사용자:");
    for user in &users {
        println!("    {}", user);
    }

    // Alice 검색 (성공)
    let found = find_user(&users, "Alice")?;
    println!("  검색 결과: {}", found);

    // 실패 케이스
    // Charlie는 없으므로 Err이지만 ?를 안 붙여 무시
    let _not_found = find_user(&users, "Charlie");

    Ok(())
}

// 프로그램 진입점: anyhow 스타일 패턴 시연
fn main() {
    println!("=== anyhow 스타일 에러 처리 ===");
    println!();

    println!("=== 정상 케이스 ===");
    // 정상 입력
    match create_user("Alice", "30") {
        Ok(user) => println!("  성공: {}", user),
        Err(e) => println!("  실패: {}", e),
    }

    println!();
    println!("=== bail! 패턴 ===");
    // 빈 이름 -> ensure!가 bail! 발동
    match create_user("", "30") {
        Ok(user) => println!("  성공: {}", user),
        Err(e) => println!("  실패: {}", e),
    }

    println!();
    println!("=== ensure! 패턴 ===");
    // 비현실적 나이 -> ensure! 실패
    match create_user("Alice", "300") {
        Ok(user) => println!("  성공: {}", user),
        Err(e) => println!("  실패: {}", e),
    }

    println!();
    println!("=== context() 패턴 ===");
    // "abc"는 파싱 실패 -> context로 메시지가 누적되어 출력
    match create_user("Bob", "abc") {
        Ok(user) => println!("  성공: {}", user),
        Err(e) => println!("  실패: {}", e),
    }

    println!();
    println!("=== Option에 context() ===");
    // Vec에 인덱스 5 접근 -> None
    let items = vec!["apple", "banana"];
    // None을 context로 Err로 변환
    let result: Result<&&str> = items.get(5).context("인덱스 범위 초과");
    println!("  items.get(5): {:?}", result.map(|v| *v));

    println!();
    println!("=== process_users ===");
    // 여러 단계의 흐름 실행
    match process_users() {
        Ok(()) => println!("  완료"),
        Err(e) => println!("  에러: {}", e),
    }

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

**실행 결과** — 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다).

**풀이 요점**
- 모든 에러를 `Box<dyn Error>` 한 통에 담고, 문자열은 `.into()` 로 그 통에 들어간다.
- `context` 는 `map_err`, `Option` 용은 `ok_or_else` 로 만든다 — 메시지는 바깥 맥락이 앞, 원인이 뒤에 붙는다.
- `with_context` 의 클로저는 에러일 때만 불린다.
- `bail!` 은 펼치면 `return Err(…)` 이고, `ensure!` 는 그 앞에 `if !조건` 을 둔 것이다.
- `_not_found` 처럼 `?` 없이 받은 `Err` 는 흐름을 멈추지 않는다.
- 주의: `parse_age(…)` 의 에러 타입은 이미 `Box<dyn Error>` 인데, 이것이 `E: Error` 조건을 만족하지 않으면 `create_user` 의 `with_context` 줄은 컴파일되지 않는다(확인 필요) — 그럴 때는 그 줄을 `map_err(|e| format!("'{}' 사용자 생성 중: {}", name, e))?` 로 바꾸면 같은 메시지를 얻는다(원본에 근거 없음 — 추론).

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
