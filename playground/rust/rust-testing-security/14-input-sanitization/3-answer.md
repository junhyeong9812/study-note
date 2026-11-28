# rust/rust-testing-security/14 — 입력 검증 & 살균 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 유효는 첫 줄 하나뿐이다 — 나머지는 각기 다른 단계에서 걸린다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
  'user@example.com' -> 유효
  'invalid' -> @ 기호가 정확히 하나 있어야 합니다
  '@example.com' -> @ 앞뒤가 비어있습니다
  'user@' -> @ 앞뒤가 비어있습니다
  'user@domain' -> 도메인에 . 이 없습니다
  '' -> 이메일이 비어있습니다
```

**왜 그런가**
- `"invalid"` 는 `split('@')` 결과가 한 조각이라 「정확히 하나」 검사에 걸린다.
- `"@example.com"` 은 `["", "example.com"]`, `"user@"` 는 `["user", ""]` 로 갈라져 둘 다 빈 조각 검사에 걸린다.
- `"user@domain"` 은 앞의 검사를 모두 통과하고 도메인에 `.` 이 없어 걸린다.
- 빈 문자열은 맨 처음의 빈 문자열 검사에서 걸린다.
- 근거: 2-summary 「동작 방식 (1)」.

### 2. 위험한 쿼리는 문장이 둘로 갈리고, 이스케이프는 `'` 만 두 배가 된다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
SELECT * FROM users WHERE name = ''; DROP TABLE users; --'
''; DROP TABLE users; --
```

**왜 그런가**
- `unsafe_query` 는 입력을 `'...'` 사이에 그대로 끼운다. 입력의 첫 `'` 가 리터럴을 닫아 `name = ''` 이 되고, `;` 뒤의 `DROP TABLE users` 가 새 명령이 된다. 끝의 `--` 는 남은 `'` 를 주석으로 만든다.
- DB 가 여러 문장 실행을 허용하면 `users` 테이블이 삭제될 수 있다. 이것이 SQL 인젝션이다.
- `escape_sql_string` 에서 페이로드에 든 특별 문자는 `'` 하나뿐이라 `''` 로 바뀐다. `\` · `"` · 널 바이트 · 줄바꿈은 없어 나머지는 그대로다.
- 근거: 2-summary 「동작 방식 (3)」.

### 3. 16바이트 제한은 15바이트에서 멈춘다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
가나다라마 (15 bytes)
```

**왜 그런가**
- 한글 한 글자는 UTF-8 3바이트라 글자 경계는 0, 3, 6, 9, 12, 15, 18 … 이다.
- 문자열 전체는 42바이트로 16 을 넘으므로 자르기에 들어간다.
- `end = 16` 은 경계가 아니므로 한 칸 물러나 15 가 되고, 15 는 경계라 멈춘다.
- `&long[..15]` 는 앞 다섯 글자다.
- 근거: 2-summary 「동작 방식 (6)」.

### 4. 나중에 바꾸면 앞 단계가 만든 엔티티의 `&` 까지 다시 바뀐다

`<` 가 먼저 `&lt;` 로 바뀐 뒤 `&` → `&amp;` 단계가 돌면, 그 `&` 도 바뀌어 `&amp;lt;` 가 된다.
브라우저는 이것을 `<` 가 아니라 글자 `&lt;` 로 보여 준다(이중 이스케이프).
`&` 를 맨 먼저 바꾸면 그 시점의 `&` 는 모두 원래 입력의 것이라 이 문제가 없다.
근거: 2-summary 「동작 방식 (5)」 · 「문법 — 형태와 규칙」.

### 5. 파라미터는 쿼리와 따로 넘어가 언제나 「값」이기 때문이다

- 파라미터화된 쿼리는 쿼리 틀(`$1`)과 값 목록을 나눠 넘기고, DB 드라이버가 값을 자리에 바인딩한다. 값은 SQL 문법으로 해석되지 않으므로 `'` · `;` 가 들어 있어도 쿼리 구조가 바뀌지 않는다.
- 손 이스케이프는 바꿀 문자를 하나라도 빠뜨리거나 순서를 틀리면 뚫린다. 예제의 `escape_sql_string` 은 `'` → `''`(SQL 표준 관례)와 `\` → `\\` · `"` → `\"`(백슬래시 방식)를 섞어 써서, 백슬래시를 특별히 다루지 않는 DB 설정에서는 결과가 달라질 수 있다.
- 근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 2」 · 「구현 세부사항 대 언어 보장」.

### 6. `..` 검사는 정상 이름도 막고, 접두사 검사는 절대 경로를 잡는다

- `"report..txt"` 는 `contains("..")` 에 걸려 「경로에 '..'를 사용할 수 없습니다」로 거부된다. 상위 디렉토리 이동이 아닌데도 막히는 오탐이다.
- 절대 경로 검사를 지우면 `"/etc/shadow"` 는 1단계를 통과한다. `Path::join` 은 절대 경로를 받으면 base 를 버리므로 이은 결과가 `/etc/shadow` 가 된다. 3단계에서 이 문자열이 `/var/www/uploads` 로 시작하지 않아 「기본 경로를 벗어났습니다」로 거부된다.
- 근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 4」.

### 7. 둘 다 통과한다 — 「3자」는 바이트, 「문자로 시작」은 `-` · `_` 만 막는다

- `"가나"` 는 `len()` 이 6바이트라 3 미만 검사를 통과한다. `is_alphanumeric()` 은 유니코드 글자를 참으로 보므로 문자 검사도 통과하고, `-` · `_` 로 시작하지 않으므로 `Ok` 다.
- `"123abc"` 는 6바이트, 모두 영숫자, `-` · `_` 로 시작하지 않으므로 `Ok` 다. 메시지는 「문자로 시작해야」라고 말하지만 코드는 숫자 시작을 막지 않는다.
- 근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 5 · 6」.

### 8. `u16` 파싱이 숫자 여부와 0..=65535 범위를 맡고, 0 금지만 남는다

`u16` 은 0 부터 65535 까지만 담으므로, 숫자가 아닌 입력 · 음수 · 65535 초과는 파싱 단계에서 `Err` 가 된다.
코드는 이 실패를 `map_err` 로 「유효한 숫자가 아닙니다」 하나로 바꿔 `?` 로 돌려준다.
타입이 표현할 수 있지만 쓰면 안 되는 값, 곧 0 만 따로 검사한다.
타입의 범위를 검사로 쓰는 생각은 newtype 패턴이 「검증됨」을 타입에 담는 것과 같은 줄기다.
근거: 2-summary 「동작 방식 (2) · (7)」.

### 9. 검증을 건너뛴 값을 넘기는 실수를 막는다

`validate_username` 의 `Ok` 값은 다시 평범한 `&str` 이라, 검증된 값과 검증 안 된 값이 같은 타입으로 섞인다.
누군가 검증을 빼먹고 원래 문자열을 넘겨도 컴파일러는 알 수 없다.
newtype 은 `Username` 같은 새 타입을 검증 함수로만 만들 수 있게 하고, 다른 함수가 `Username` 을 받게 한다.
그러면 검증 없이 `&str` 을 넘기는 호출은 타입이 맞지 않아 컴파일 오류가 된다.
근거: 2-summary 「동작 방식 (7)」 · 「어디서 틀리나 7」.

## 실습 정답

### 실습 1. 입력 검증 · 살균 도구 모음 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 이메일 검증 | `InputValidator::validate_email` — `trim` · `is_empty` · `len() > 254` · `split('@')` · `parts[1].contains('.')` |
| 2. 사용자명 검증 | `InputValidator::validate_username` — `len() < 3` · `len() > 30` · `chars().all(...)` · `starts_with('-')` |
| 3. 포트 검증 | `InputValidator::validate_port` — `parse()` 의 `u16` + `map_err(...)?` · `port == 0` |
| 4. 위험한 쿼리 | `SafeQuery::unsafe_query` — `format!("... name = '{}'", name)` |
| 5. 파라미터화 | `SafeQuery::parameterized_query` — `"... name = $1"` 과 `vec![name.to_string()]` 튜플 |
| 6. SQL 이스케이프 | `SafeQuery::escape_sql_string` — `replace('\\', ...)` 부터 이어지는 `replace` 사슬 |
| 7. 경로 순회 방지 | `safe_path_join` — `contains("..")` · `starts_with('/')` · `contains('\0')` · `base.join` · `joined_str.starts_with(...)` |
| 8. HTML 이스케이프 | `escape_html` — `replace('&', "&amp;")` 를 맨 앞에 둔 사슬 |
| 9. 길이 제한 | `limit_input` — `while end > 0 && !input.is_char_boundary(end)` · `&input[..end]` |
| 10. 이메일 · 사용자명 찍기 | `main` 의 `for email in emails` · `for name in names` 와 `match` |
| 11. SQL 세 방식 찍기 | `main` 의 `malicious` 와 세 `println!` 묶음 |
| 12. 경로 다섯 개 찍기 | `main` 의 `for p in paths` 와 `path.display()` |
| 13. XSS 찍기 | `main` 의 `for input in inputs` — `원본:` · `이스케이프:` |
| 14. 길이 제한 찍기 | `main` 의 `limit_input(long, 15)` 와 `len()` 출력 |
| 15. 체크리스트 | `main` 끝의 `println!` 여섯 줄 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`rust/rust-testing-security/reference/input-sanitization.rs`

```rust
// [테스팅 & 보안] 입력 검증 & 살균
// 설명: 입력 검증, SQL 파라미터화, 경로 순회 방지, XSS 방지
// 팁: 입력 검증은 화이트리스트(허용 목록) 방식이 블랙리스트보다 안전하다. SQL은 반드시 파라미터화된 쿼리를 사용하고, HTML 출력은 이스케이프한다. 경로 입력은 '..'를 차단하고 base 디렉토리 밖을 접근할 수 없게 한다. Rust의 타입 시스템으로 검증된 입력과 미검증 입력을 구분하는 newtype 패턴도 유용하다.

// 경로 처리에 필요한 Path/PathBuf 타입을 가져온다
use std::path::{Path, PathBuf};

// === 1. 문자열 입력 검증 ===

// 검증 메서드를 묶는 빈 네임스페이스 struct
struct InputValidator;

impl InputValidator {
    // 이메일 기본 검증 - 화이트리스트 기반 형식 검사
    fn validate_email(email: &str) -> Result<&str, String> {
        // 양옆 공백 제거 (사용자 실수 보정)
        let email = email.trim();
        if email.is_empty() {
            return Err("이메일이 비어있습니다".to_string());
        }
        // RFC 길이 제한
        if email.len() > 254 {
            return Err("이메일이 너무 깁니다".to_string());
        }
        // @ 정확히 1개를 위해 split으로 두 부분 보장
        let parts: Vec<&str> = email.split('@').collect();
        if parts.len() != 2 {
            return Err("@ 기호가 정확히 하나 있어야 합니다".to_string());
        }
        // local-part와 domain 모두 비어있으면 안 됨
        if parts[0].is_empty() || parts[1].is_empty() {
            return Err("@ 앞뒤가 비어있습니다".to_string());
        }
        // 도메인은 최소 한 개의 점 필요
        if !parts[1].contains('.') {
            return Err("도메인에 . 이 없습니다".to_string());
        }
        Ok(email)
    }

    // 사용자명 검증 - 화이트리스트로 허용 문자 제한
    fn validate_username(name: &str) -> Result<&str, String> {
        let name = name.trim();
        if name.len() < 3 {
            return Err("사용자명은 최소 3자입니다".to_string());
        }
        if name.len() > 30 {
            return Err("사용자명은 최대 30자입니다".to_string());
        }
        // 영숫자/밑줄/하이픈만 허용 (화이트리스트)
        if !name.chars().all(|c| c.is_alphanumeric() || c == '_' || c == '-') {
            return Err("사용자명은 영숫자, _, -만 허용됩니다".to_string());
        }
        // 특수문자로 시작하는 것 차단
        if name.starts_with('-') || name.starts_with('_') {
            return Err("사용자명은 문자로 시작해야 합니다".to_string());
        }
        Ok(name)
    }

    // 포트 검증 - 타입 파싱으로 1차 검증, 범위 추가 검사
    fn validate_port(input: &str) -> Result<u16, String> {
        // u16 파싱 자체가 범위 0..=65535 검증을 겸함
        let port: u16 = input.trim().parse()
            .map_err(|_| "유효한 숫자가 아닙니다".to_string())?;
        if port == 0 {
            return Err("포트 0은 사용할 수 없습니다".to_string());
        }
        Ok(port)
    }
}

// === 2. SQL 인젝션 방지 ===

// 안전/위험 SQL 패턴을 보여주는 네임스페이스
struct SafeQuery;

impl SafeQuery {
    // 위험: 문자열 직접 삽입 - 인젝션 발생 가능
    fn unsafe_query(name: &str) -> String {
        // ' 등이 그대로 들어가면 쿼리 구조 변조 가능
        format!("SELECT * FROM users WHERE name = '{}'", name)
    }

    // 안전: 파라미터화된 쿼리 (실제 DB 드라이버가 처리)
    fn parameterized_query(name: &str) -> (String, Vec<String>) {
        // $1 같은 placeholder는 드라이버가 안전하게 바인딩
        (
            "SELECT * FROM users WHERE name = $1".to_string(),
            vec![name.to_string()],
        )
    }

    // 안전: 이스케이프 (최후의 수단 - 가능하면 파라미터화 사용)
    fn escape_sql_string(input: &str) -> String {
        // 백슬래시, 작은따옴표, 큰따옴표, 널바이트, 줄바꿈 모두 이스케이프
        input.replace('\\', "\\\\")
            .replace('\'', "''")
            .replace('"', "\\\"")
            .replace('\0', "")
            .replace('\n', "\\n")
            .replace('\r', "\\r")
    }
}

// === 3. 경로 순회 방지 ===

// base 디렉토리 안으로만 결합되도록 검증
fn safe_path_join(base: &Path, user_input: &str) -> Result<PathBuf, String> {
    // 1. 위험한 문자/패턴 확인
    // .. 로 상위 디렉토리 탈출 시도 차단
    if user_input.contains("..") {
        return Err("경로에 '..'를 사용할 수 없습니다".to_string());
    }
    // 절대경로 차단 (Unix /, Windows \\)
    if user_input.starts_with('/') || user_input.starts_with('\\') {
        return Err("절대 경로는 허용되지 않습니다".to_string());
    }
    // 널 바이트는 C 문자열 종료자로 해석되어 우회 가능
    if user_input.contains('\0') {
        return Err("널 바이트 포함".to_string());
    }

    // 2. 경로 결합
    let joined = base.join(user_input);

    // 3. 정규화 후 base 내에 있는지 확인
    // (canonicalize는 파일이 존재해야 하므로 문자열 비교로 대체)
    let joined_str = joined.to_string_lossy();
    let base_str = base.to_string_lossy();

    // base prefix를 유지하지 않으면 거부
    if !joined_str.starts_with(base_str.as_ref()) {
        return Err("기본 경로를 벗어났습니다".to_string());
    }

    Ok(joined)
}

// === 4. XSS 방지: HTML 이스케이프 ===

// HTML 출력 시 메타문자를 엔티티로 치환
fn escape_html(input: &str) -> String {
    input
        // & 먼저 처리 (다른 엔티티의 & 보호)
        .replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
        .replace('\'', "&#x27;")
}

// === 5. 입력 크기 제한 ===

// UTF-8 경계를 보존하며 max_bytes까지 자름
fn limit_input(input: &str, max_bytes: usize) -> &str {
    if input.len() <= max_bytes {
        input
    } else {
        // UTF-8 경계를 존중하며 자르기 (멀티바이트 문자 중간 분할 방지)
        let mut end = max_bytes;
        // is_char_boundary는 해당 인덱스가 안전한 분할점인지 확인
        while end > 0 && !input.is_char_boundary(end) {
            end -= 1;
        }
        &input[..end]
    }
}

// 메인: 각 검증/이스케이프 패턴을 다양한 입력에 적용해 보여줌
fn main() {
    // === 이메일 검증 ===
    println!("=== 이메일 검증 ===");
    // 다양한 정상/이상 이메일 케이스
    let emails = vec![
        "user@example.com",
        "invalid",
        "@example.com",
        "user@",
        "user@domain",
        "",
    ];
    for email in emails {
        match InputValidator::validate_email(email) {
            Ok(e) => println!("  '{}' -> 유효", e),
            Err(e) => println!("  '{}' -> {}", email, e),
        }
    }

    // === 사용자명 검증 ===
    println!("\n=== 사용자명 검증 ===");
    let names = vec!["alice", "ab", "alice_bob", "alice!bob", "-invalid", "valid-name-123"];
    for name in names {
        match InputValidator::validate_username(name) {
            Ok(n) => println!("  '{}' -> 유효", n),
            Err(e) => println!("  '{}' -> {}", name, e),
        }
    }

    // === SQL 인젝션 ===
    println!("\n=== SQL 인젝션 방지 ===");
    // 클래식한 인젝션 페이로드
    let malicious = "'; DROP TABLE users; --";

    println!("  위험한 쿼리:");
    println!("    {}", SafeQuery::unsafe_query(malicious));

    println!("  안전한 쿼리 (파라미터화):");
    let (query, params) = SafeQuery::parameterized_query(malicious);
    println!("    쿼리: {}", query);
    println!("    파라미터: {:?}", params);

    println!("  이스케이프:");
    println!("    {}", SafeQuery::escape_sql_string(malicious));

    // === 경로 순회 ===
    println!("\n=== 경로 순회 방지 ===");
    // 업로드 디렉토리를 base로 하여 다양한 경로 시도
    let base = Path::new("/var/www/uploads");
    let paths = vec![
        "image.png",
        "../../etc/passwd",
        "/etc/shadow",
        "sub/file.txt",
        "..\\windows\\system32",
    ];
    for p in paths {
        match safe_path_join(base, p) {
            Ok(path) => println!("  '{}' -> {}", p, path.display()),
            Err(e) => println!("  '{}' -> 거부: {}", p, e),
        }
    }

    // === XSS 방지 ===
    println!("\n=== XSS 방지 ===");
    // 스크립트 페이로드와 정상 텍스트가 어떻게 변환되는지 비교
    let inputs = vec![
        "Hello, World!",
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert(1)>",
        "normal & safe text",
    ];
    for input in inputs {
        println!("  원본: {}", input);
        println!("  이스케이프: {}", escape_html(input));
    }

    // === 입력 크기 제한 ===
    println!("\n=== 입력 크기 제한 ===");
    // 한글은 1자=3바이트(UTF-8)이므로 경계 처리가 중요
    let long = "가나다라마바사아자차카타파하";
    let limited = limit_input(long, 15);
    println!("  원본: {} ({} bytes)", long, long.len());
    println!("  제한(15b): {} ({} bytes)", limited, limited.len());

    // === 체크리스트 ===
    println!("\n=== 보안 입력 처리 체크리스트 ===");
    println!("1. 모든 사용자 입력을 검증한다 (화이트리스트 선호)");
    println!("2. SQL은 항상 파라미터화된 쿼리 사용");
    println!("3. HTML 출력은 이스케이프");
    println!("4. 경로는 base 디렉토리 내로 제한");
    println!("5. 입력 크기를 제한한다");
    println!("6. 널 바이트, 제어 문자를 제거한다");
}
```

**실행 결과** — 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다).

**풀이 요점**
- 검증 함수는 조건을 하나씩 검사해 걸리면 바로 `Err` 를 돌려주는 이른 반환 꼴이다.
- 사용자명의 문자 검사는 `chars().all(...)` 화이트리스트이고, 길이 검사는 바이트 기준이다.
- SQL 은 파라미터화가 정답이고, `escape_sql_string` 은 `\` 를 먼저 바꾸는 순서가 핵심인 최후의 수단이다.
- 경로는 금지 패턴 차단 → `join` → base 접두사 확인의 세 단계다. `join` 이 절대 경로에서 base 를 버린다는 점이 1 · 3 단계의 까닭이다.
- HTML 이스케이프는 `&` 를 먼저 바꿔야 이중 이스케이프가 없다.
- `limit_input` 은 `is_char_boundary` 로 물러나 UTF-8 글자 중간에서 자르는 패닉을 피한다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
