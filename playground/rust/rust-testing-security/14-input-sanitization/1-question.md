# rust/rust-testing-security/14 — 입력 검증 & 살균 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 여섯 이메일이 검증을 거치면 (예측)

```rust
// 질문용 발췌
let emails = vec!["user@example.com", "invalid", "@example.com", "user@", "user@domain", ""];
for email in emails {
    match InputValidator::validate_email(email) {
        Ok(e) => println!("  '{}' -> 유효", e),
        Err(e) => println!("  '{}' -> {}", email, e),
    }
}
```

- 여섯 줄은 각각 어떤 메시지로 끝나는가?

### 2. 인젝션 페이로드를 세 방식에 넣으면 (예측)

```rust
// 질문용 발췌
let malicious = "'; DROP TABLE users; --";
println!("{}", SafeQuery::unsafe_query(malicious));
println!("{}", SafeQuery::escape_sql_string(malicious));
```

- 두 줄은 각각 어떤 문자열이 되는가?
- 첫 줄의 쿼리를 DB 가 그대로 받으면 무슨 일이 생기는가?

### 3. 한글 문자열을 16바이트로 자르면 (예측)

```rust
// 질문용 발췌
let long = "가나다라마바사아자차카타파하";
let limited = limit_input(long, 16);
println!("{} ({} bytes)", limited, limited.len());
```

- 어떤 글자들이 남고, 몇 바이트인가?

### 4. `escape_html` 이 `&` 를 맨 먼저 바꾸는 까닭 (왜)
- `&` 를 바꾸는 줄을 맨 뒤로 옮기면 `"<"` 의 이스케이프 결과는 왜 망가지는가?

### 5. 파라미터화를 앞세우고 이스케이프를 「최후의 수단」으로 두는 까닭 (왜)
- 파라미터화된 쿼리는 왜 입력이 어떤 글자를 담든 쿼리 구조를 바꾸지 못하는가?
- `escape_sql_string` 같은 손 이스케이프는 어디서 어긋날 수 있는가?

### 6. `safe_path_join` 이 막는 것과 못 막는 것 (경계)
- `"report..txt"` 는 받아들여지는가?
- 절대 경로 검사(`starts_with('/')`)를 지우면 `"/etc/shadow"` 는 어느 단계에서 어떻게 되는가?

### 7. `validate_username` 의 「3자」와 「문자로 시작」 (경계)
- `"가나"` 와 `"123abc"` 는 각각 통과하는가?

### 8. 포트 검증과 정수 타입 (연결)
- `validate_port` 에서 `u16` 으로 파싱하는 일은 어떤 검사를 대신하고, 무엇이 따로 남는가?

### 9. 검증 함수와 newtype 패턴 (연결)
- `validate_username` 이 `Result<&str, String>` 을 돌려주는 설계와 비교해, newtype 은 어떤 실수를 컴파일 단계에서 막는가?

## 실습

### 실습 1. 입력 검증 · 살균 도구 모음 만들기

**만들 것** — 이메일 · 사용자명 · 포트 검증, SQL 쿼리 세 방식, 경로 순회 방지, HTML 이스케이프, UTF-8 경계를 지키는 길이 제한을 한 파일에 만들고, `main` 에서 여러 입력에 적용해 결과를 찍는다.

**요구 조건**

1단계 — 검증기 (`InputValidator`)
1. `validate_email(&str) -> Result<&str, String>` 은 양옆 공백을 걷어 낸 뒤, 빈 문자열 · 254바이트 초과 · `@` 가 정확히 하나가 아님 · `@` 앞뒤 중 빈 쪽이 있음 · 도메인에 `.` 이 없음을 차례로 거부하고, 통과하면 걷어 낸 문자열을 `Ok` 로 돌려준다.
2. `validate_username(&str) -> Result<&str, String>` 은 공백을 걷어 낸 뒤 3바이트 미만 · 30바이트 초과 · 영숫자/`_`/`-` 밖의 문자 · `-` 나 `_` 로 시작함을 차례로 거부한다.
3. `validate_port(&str) -> Result<u16, String>` 은 공백을 걷어 내 `u16` 으로 파싱하고, 실패하면 「유효한 숫자가 아닙니다」, 0 이면 「포트 0은 사용할 수 없습니다」를 돌려준다.

2단계 — SQL (`SafeQuery`)
4. `unsafe_query` 는 이름을 `'...'` 안에 직접 끼워 넣은 `SELECT` 문을 돌려준다.
5. `parameterized_query` 는 `$1` 자리표시가 든 쿼리 문자열과, 이름 하나를 담은 파라미터 벡터를 튜플로 돌려준다.
6. `escape_sql_string` 은 `\` → `\\`, `'` → `''`, `"` → `\"`, 널 바이트 제거, 줄바꿈 `\n` · `\r` → 글자 `\n` · `\r` 을 이 순서로 바꾼다.

3단계 — 경로 · HTML · 길이
7. `safe_path_join(base, input) -> Result<PathBuf, String>` 은 `..` 포함, `/` 나 `\` 로 시작, 널 바이트 포함을 거부하고, base 에 이은 결과가 base 문자열로 시작하지 않으면 「기본 경로를 벗어났습니다」로 거부한다.
8. `escape_html` 은 `&` `<` `>` `"` `'` 를 `&amp;` `&lt;` `&gt;` `&quot;` `&#x27;` 로, `&` 를 맨 먼저 바꾼다.
9. `limit_input(input, max_bytes) -> &str` 은 길이가 넘지 않으면 그대로, 넘으면 `is_char_boundary` 가 참인 자리까지 물러나 자른 조각을 돌려준다.

4단계 — `main`
10. 이메일 여섯 개와 사용자명 여섯 개를 검증해, 유효하면 `'값' -> 유효`, 아니면 `'값' -> 이유` 를 찍는다.
11. 페이로드 `'; DROP TABLE users; --` 를 위험한 쿼리 · 파라미터화(쿼리와 파라미터를 따로) · 이스케이프로 찍는다.
12. base `/var/www/uploads` 에 다섯 경로를 이어 보고, 성공은 이은 경로를, 실패는 `거부: 이유` 를 찍는다.
13. 네 입력의 원본과 HTML 이스케이프 결과를 나란히 찍는다.
14. 한글 14자 문자열을 15바이트로 제한해, 원본과 결과를 바이트 수와 함께 찍는다.
15. 마지막에 보안 입력 처리 체크리스트 여섯 줄을 찍는다.

**시작 코드**

```rust
use std::path::{Path, PathBuf};

struct InputValidator;

impl InputValidator {
    fn validate_email(email: &str) -> Result<&str, String> {
        // TODO: trim → 비었나 → 254 초과 → '@' 로 나눠 두 조각인가 → 앞뒤 비었나 → 도메인에 '.' 있나
        todo!()
    }

    fn validate_username(name: &str) -> Result<&str, String> {
        // TODO: trim → 길이 3..=30 (바이트) → 허용 문자만 (화이트리스트) → '-' '_' 로 시작 금지
        todo!()
    }

    fn validate_port(input: &str) -> Result<u16, String> {
        // TODO: u16 으로 파싱 (실패 메시지 바꾸기) → 0 거부
        todo!()
    }
}

struct SafeQuery;

impl SafeQuery {
    fn unsafe_query(name: &str) -> String {
        // TODO: 이름을 직접 끼워 넣은 SELECT (위험한 예)
        todo!()
    }

    fn parameterized_query(name: &str) -> (String, Vec<String>) {
        // TODO: "$1" 자리표시 쿼리 + 파라미터 벡터
        todo!()
    }

    fn escape_sql_string(input: &str) -> String {
        // TODO: 백슬래시를 가장 먼저, 그다음 ' " \0 \n \r
        todo!()
    }
}

fn safe_path_join(base: &Path, user_input: &str) -> Result<PathBuf, String> {
    // TODO: 1) ".." · 절대 경로 · 널 바이트 거부
    // TODO: 2) base 에 잇기
    // TODO: 3) 이은 결과가 base 문자열로 시작하는지 확인
    todo!()
}

fn escape_html(input: &str) -> String {
    // TODO: & 를 맨 먼저, 그다음 < > " '
    todo!()
}

fn limit_input(input: &str, max_bytes: usize) -> &str {
    // TODO: 넘으면 문자 경계까지 물러나 자르기
    todo!()
}

fn main() {
    println!("=== 이메일 검증 ===");
    let emails = vec!["user@example.com", "invalid", "@example.com", "user@", "user@domain", ""];
    // TODO: 각 이메일 검증 결과 찍기

    println!("\n=== 사용자명 검증 ===");
    let names = vec!["alice", "ab", "alice_bob", "alice!bob", "-invalid", "valid-name-123"];
    // TODO: 각 사용자명 검증 결과 찍기

    println!("\n=== SQL 인젝션 방지 ===");
    let malicious = "'; DROP TABLE users; --";
    // TODO: 위험한 쿼리 · 파라미터화 · 이스케이프 찍기

    println!("\n=== 경로 순회 방지 ===");
    let base = Path::new("/var/www/uploads");
    let paths = vec!["image.png", "../../etc/passwd", "/etc/shadow", "sub/file.txt", "..\\windows\\system32"];
    // TODO: 각 경로 결합 결과 찍기

    println!("\n=== XSS 방지 ===");
    let inputs = vec![
        "Hello, World!",
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert(1)>",
        "normal & safe text",
    ];
    // TODO: 원본과 이스케이프 결과 찍기

    println!("\n=== 입력 크기 제한 ===");
    let long = "가나다라마바사아자차카타파하";
    // TODO: 15바이트로 제한하고 원본/결과를 바이트 수와 함께 찍기

    println!("\n=== 보안 입력 처리 체크리스트 ===");
    // TODO: 체크리스트 여섯 줄
}
```

**확인 방법** — 아래처럼 컴파일해 돌리고, 각 절의 줄이 요구 조건대로 유효 · 거부 · 변환되는지 본다.

```bash
rustc input-sanitization.rs && ./input-sanitization
```

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
