# rust/rust-practical/04 — Regex 정규 표현식 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. `10.0.0.1` 과 `192.168.1.1` 만 참이다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

| 입력 | 판정 | 까닭 |
|---|---|---|
| `192.168.1.1` | `true` | 네 조각 모두 `u8` 로 파싱되고 앞자리 0 이 없다 |
| `256.1.1.1` | `false` | `256` 은 `u8`(0~255) 파싱에 실패한다 |
| `10.0.0.1` | `true` | `"0"` 은 한 글자라 앞자리 0 검사를 통과한다 |
| `1.2.3` | `false` | 조각이 3개라 첫 검사(`len() != 4`)에서 걸린다 |
| `01.02.03.04` | `false` | `"01"` 은 두 글자인데 `0` 으로 시작한다 |

**왜 그런가**
모양(조각 수) → 범위(`parse::<u8>`) → 앞자리 0 의 세 겹 검사다.
`all` 은 하나라도 거짓이면 거짓이다.
근거: 2-summary 「동작 방식 (2)」.

### 2. 네 쌍 — 위치 4, 16, 28, 40

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

| 위치 | 값 |
|---|---|
| 4 | `15000` |
| 16 | `-3000` |
| 28 | `12000` |
| 40 | `10.5` |

**왜 그런가**
위치는 `Vec<char>` 의 번호라 한글 한 글자도 1 로 센다.
`가격: ` 이 4글자(0~3)라 `15000` 은 4 에서 시작한다.
`-3000` 은 `-` 다음이 숫자라 `-` 자리(16)부터 한 덩어리다.
`10.5` 는 숫자와 `.` 을 이어 모으므로 한 덩어리가 되고, `%` 에서 멈춘다.
근거: 2-summary 「동작 방식 (4)」.

### 3. `a` · `b` 는 `Some`, `c` 는 `None`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- `a` → `Some` — host `example.com`, `port` 는 `None`, `path` 는 `"/"`.
- `b` → `Some` — host `localhost`, `port` 는 `Some(3000)`, `path` 는 `"/"`.
- `c` → `None` — `"://"` 가 없어 첫 `split_once("://")?` 에서 끝난다.

**왜 그런가**
`a` 는 `/` 뒤가 빈 문자열이고, `b` 는 `/` 가 없어 `unwrap_or((rest, ""))` 로 빈 경로가 된다.
둘 다 `format!("/{}", path)` 로 `"/"` 가 되므로 손 구현은 둘을 구분하지 못한다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 4」.

### 4. 컴파일은 비싸고 매칭은 싸서 — 한 번 만든 것을 재사용한다

`Regex::new` 는 비용이 크다(원본 팁).
반복문 안에서 부르면 같은 패턴을 줄마다 다시 컴파일해, 매칭보다 컴파일에 시간을 쓴다.
`OnceLock` 의 `get_or_init` · `lazy_static!` 은 처음 한 번만 초기화하고 이후엔 같은 `Regex` 를 빌려준다.
근거: 2-summary 「동작 방식 (7)」 · 「문법」 · 「어디서 틀리나 1」.

### 5. 꺼내는 쪽 코드가 스스로 설명되기 때문이다

번호 그룹은 `caps[3]` 이 무엇인지 알려면 패턴을 다시 세어 읽어야 한다.
이름을 붙이면 `caps["level"]` 처럼 무엇을 꺼내는지 드러나 가독성이 좋아진다(원본 팁).
예제에서는 `LogEntry` · `UrlParts` 의 필드 이름이 이 이름 역할을 한다.
근거: 2-summary 「동작 방식 (6)」 · 「어디서 틀리나 2」.

### 6. 입력이 길어져도 매칭 시간이 갑자기 폭발하지 않기 때문이다

역추적 엔진은 실패할 때 되돌아가 다른 갈래를 다시 시도하므로, 패턴에 따라 시도 횟수가 폭발할 수 있다.
`regex` 크레이트는 역추적 없이 선형 시간이라, 입력 길이에 비례하는 시간만 든다(원본 팁).
이것은 크레이트의 보장이지 Rust 언어의 보장이 아니다.
근거: 2-summary 「동작 방식 (7)」 · 「구현 세부사항 대 언어 보장」.

### 7. 목록에 없는 번호는 그대로 남는다 — 정규식은 모양으로 덮는다

`replace_pattern` 은 `"1234"` · `"5678"` · `"9876"` · `"5432"` 라는 글자열만 바꾼다.
`010-1111-2222` 는 그 어느 것도 포함하지 않으므로 가려지지 않는다.
정규식 `replace_all` 은 「숫자 넷」 같은 모양으로 찾으므로 어떤 번호든 같은 규칙으로 가린다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 5」.

### 8. 정규식은 받아들이고, `is_email` 은 거절한다

주석의 정규식은 local 에 `[\w.+-]+` 를 쓰므로 `+` 를 허용한다 — 매치된다.
손 구현은 local 의 글자를 영숫자 · `.` · `_` · `-` 로만 허용하므로 `+` 에서 `all` 이 거짓이 되어 `false` 다.
주석의 정규식과 손 구현이 같은 일을 한다고 믿으면 이런 데서 틀린다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 4」.

### 9. 판정 · 전체 찾기 · 캡처 · 전체 교체

- `is_email`(그리고 `is_phone` · `is_ipv4`) → `is_match` — `bool` 하나를 돌려준다.
- `find_numbers` → `find_iter` — 모든 매치를 위치와 함께 모은다.
- `parse_url` → `captures` — 매치 안의 부분을 그룹(필드)으로 나눠 꺼낸다.
- `replace_pattern` → `replace_all` — 찾은 것을 전부 바꾼 새 문자열을 만든다.

근거: 2-summary 「한눈에」 대응표 · 「동작 방식 (1)~(5), (7)」.

### 10. `Option` 을 돌려주는 함수라서 `filter_map` 이 `None` 을 걸러 준다

`parse_log_line` 은 형식이 맞으면 `Some(LogEntry)`, 아니면 `None` 이다.
`filter_map` 은 `Some` 안의 값만 남기므로, `잘못된 형식의 로그` 줄은 저절로 빠지고 `LogEntry` 들만 다음 `filter` 로 넘어간다.
그래서 `filter(|e| e.level == "ERROR")` 는 `Option` 을 다시 풀 필요 없이 등급만 본다 — 결과는 1건이다.
다만 실패가 말없이 버려진다는 점은 알고 써야 한다.
근거: 2-summary 「동작 방식 (6)」 · 「어디서 틀리나 6」.

## 실습 정답

### 실습 1. 정규식 없이 정규식 흉내 내기 — 검증 · 캡처 · 찾기 · 교체 · 로그 파싱

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 이메일 판정 | `SimpleMatcher::is_email` — `split('@')` · `!local.is_empty()` · `domain.contains('.')` · `local.chars().all(...)` |
| 2. 전화번호 판정 | `SimpleMatcher::is_phone` — `split('-')` · `parts[0] == "010"` · `is_ascii_digit` |
| 3. IPv4 판정 | `SimpleMatcher::is_ipv4` — `part.parse::<u8>().is_ok()` · `!part.starts_with('0')` |
| 4. URL 쪼개기 | `SimpleMatcher::parse_url` — `split_once("://")?` · `split_once('/').unwrap_or((rest, ""))` · `p.parse::<u16>().ok()` |
| 5. `UrlParts` | `struct UrlParts { scheme, host, port, path }` · `format!("/{}", path)` |
| 6. 숫자 전부 찾기 | `SimpleMatcher::find_numbers` — `while i < chars.len()` 상태 머신 · `results.push((start, num))` |
| 7. 교체 | `SimpleMatcher::replace_pattern` — `for pattern in from { result = result.replace(pattern, to); }` |
| 8. 로그 한 줄 파싱 | `parse_log_line` — `line.find(']')?` · `rest.find(']')?` · `LogEntry { timestamp, level, message }` |
| 9. 로그 출력 | `main` 의 `match parse_log_line(log)` — `Some(entry)` / `None => 파싱 실패` |
| 10. ERROR 필터 | `logs.iter().filter_map(...).filter(\|entry\| entry.level == "ERROR").collect()` |
| 11. 크레이트 안내 | `main` 끝의 `=== regex 크레이트 사용 시 패턴 ===` 이하 `println!` 들 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`rust/rust-practical/reference/regex-rust.rs`

```rust
// [실전 Rust] Regex 정규 표현식
// 설명: regex 크레이트 패턴 매칭, 캡처 그룹, 교체, 분할
// 팁: Regex::new()은 비용이 크므로 lazy_static! 또는 OnceLock으로 한 번만 컴파일한다. 캡처 그룹에 이름을 붙이면(?P<name>...) 가독성이 좋아진다. regex 크레이트는 기본적으로 유니코드를 지원하며 역추적(backtracking) 없이 선형 시간에 동작한다.

// === Regex 패턴: 순수 Rust 정규 표현식 시뮬레이션 ===
// Cargo.toml: regex = "1"

// regex 크레이트 없이 기본 패턴 매칭을 구현하여 사용 패턴을 보여줍니다.

// ===== 간단한 패턴 매처 =====

// 정규식 대신 수작업 검증 함수 모음 - regex::Regex 패턴의 시뮬레이션
struct SimpleMatcher;

impl SimpleMatcher {
    // 이메일 패턴 검사 - 실제 regex: ^[\w.+-]+@[\w.-]+\.\w+$
    fn is_email(input: &str) -> bool {
        // '@'로 분리하여 정확히 2조각인지 확인
        let parts: Vec<&str> = input.split('@').collect();
        if parts.len() != 2 { return false; }
        let (local, domain) = (parts[0], parts[1]);
        // local은 비어있지 않고, domain은 도트 포함
        !local.is_empty()
            && domain.contains('.')
            && !domain.starts_with('.')
            && !domain.ends_with('.')
            // local 부분의 허용 문자 검사
            && local.chars().all(|c| c.is_alphanumeric() || c == '.' || c == '_' || c == '-')
    }

    // 전화번호 패턴: 010-XXXX-XXXX (regex: ^010-\d{4}-\d{4}$)
    fn is_phone(input: &str) -> bool {
        let parts: Vec<&str> = input.split('-').collect();
        if parts.len() != 3 { return false; }
        // 첫 부분 010 + 4자리 + 4자리 모두 숫자
        parts[0] == "010"
            && parts[1].len() == 4
            && parts[2].len() == 4
            && parts[1].chars().all(|c| c.is_ascii_digit())
            && parts[2].chars().all(|c| c.is_ascii_digit())
    }

    // IP 주소 패턴 - 실제 regex: ^(\d{1,3}\.){3}\d{1,3}$ + 범위 검사
    fn is_ipv4(input: &str) -> bool {
        let parts: Vec<&str> = input.split('.').collect();
        if parts.len() != 4 { return false; }
        // 각 옥텟이 u8 범위(0-255)이고 leading zero 없음
        parts.iter().all(|part| {
            part.parse::<u8>().is_ok() && (part.len() == 1 || !part.starts_with('0'))
        })
    }

    // URL에서 컴포넌트 추출 (캡처 그룹 시뮬레이션) - regex: ^(\w+)://([^:/]+)(?::(\d+))?(/.*)?$
    fn parse_url(url: &str) -> Option<UrlParts> {
        // scheme://rest 분리
        let (scheme, rest) = url.split_once("://")?;
        // host_port와 path 분리
        let (host_port, path) = rest.split_once('/').unwrap_or((rest, ""));
        // host:port 분리 - 콜론 있으면 port 파싱
        let (host, port) = if let Some((h, p)) = host_port.split_once(':') {
            (h.to_string(), p.parse::<u16>().ok())
        } else {
            (host_port.to_string(), None)
        };

        Some(UrlParts {
            scheme: scheme.to_string(),
            host,
            port,
            path: format!("/{}", path),
        })
    }

    // 문자열에서 모든 매치 찾기 (find_iter 시뮬레이션) - regex: -?\d+(\.\d+)?
    fn find_numbers(input: &str) -> Vec<(usize, String)> {
        let mut results = Vec::new();
        let chars: Vec<char> = input.chars().collect();
        let mut i = 0;

        // 상태 머신 방식으로 숫자 시퀀스 추출
        while i < chars.len() {
            // 숫자 시작 또는 음수 부호 + 숫자
            if chars[i].is_ascii_digit() || (chars[i] == '-' && i + 1 < chars.len() && chars[i + 1].is_ascii_digit()) {
                let start = i;
                if chars[i] == '-' { i += 1; }
                // 숫자와 소수점을 모두 수집
                while i < chars.len() && (chars[i].is_ascii_digit() || chars[i] == '.') {
                    i += 1;
                }
                let num: String = chars[start..i].iter().collect();
                results.push((start, num));
            } else {
                i += 1;
            }
        }
        results
    }

    // 치환 (replace_all 시뮬레이션) - 여러 패턴을 동일한 문자열로 교체
    fn replace_pattern(input: &str, from: &[&str], to: &str) -> String {
        let mut result = input.to_string();
        for pattern in from {
            result = result.replace(pattern, to);
        }
        result
    }
}

// URL 파싱 결과 - 캡처 그룹의 명명된 필드
#[derive(Debug)]
struct UrlParts {
    scheme: String,
    host: String,
    port: Option<u16>,
    path: String,
}

// ===== 로그 파서 =====

// 로그 한 줄의 파싱 결과 - regex의 named capture에 해당
#[derive(Debug)]
struct LogEntry {
    timestamp: String,
    level: String,
    message: String,
}

// 로그 파서 - regex: ^\[(?P<ts>[^\]]+)\] \[(?P<level>\w+)\] (?P<msg>.*)$
fn parse_log_line(line: &str) -> Option<LogEntry> {
    // 형식: [2026-04-04 15:30:00] [INFO] 메시지
    let line = line.trim();
    if !line.starts_with('[') { return None; }

    // 첫 번째 ']' 위치 찾기 - timestamp 종료
    let ts_end = line.find(']')?;
    let timestamp = line[1..ts_end].to_string();

    // 그 다음에서 level 추출
    let rest = &line[ts_end + 1..].trim_start();
    if !rest.starts_with('[') { return None; }

    let level_end = rest.find(']')?;
    let level = rest[1..level_end].to_string();
    // 나머지가 메시지
    let message = rest[level_end + 1..].trim().to_string();

    Some(LogEntry { timestamp, level, message })
}

fn main() {
    println!("=== 1. 패턴 매칭 (is_match 동작) ===");
    // 다양한 이메일 케이스
    let emails = vec!["user@example.com", "invalid", "a@b.c", "@bad.com", "good_name@domain.co.kr"];
    for email in &emails {
        println!("  '{}' -> 이메일: {}", email, SimpleMatcher::is_email(email));
    }

    println!("\n전화번호:");
    let phones = vec!["010-1234-5678", "02-123-4567", "010-12345-678", "010-abcd-efgh"];
    for phone in &phones {
        println!("  '{}' -> 전화번호: {}", phone, SimpleMatcher::is_phone(phone));
    }

    println!("\nIP 주소:");
    let ips = vec!["192.168.1.1", "256.1.1.1", "10.0.0.1", "1.2.3", "01.02.03.04"];
    for ip in &ips {
        println!("  '{}' -> IPv4: {}", ip, SimpleMatcher::is_ipv4(ip));
    }

    println!("\n=== 2. 캡처 그룹 (URL 파싱) ===");
    // URL 파싱 - regex의 captures()와 동일한 결과
    let urls = vec![
        "https://api.example.com:8443/v1/users",
        "http://localhost:3000/health",
        "https://example.com/",
    ];
    for url in &urls {
        if let Some(parts) = SimpleMatcher::parse_url(url) {
            println!("  URL: {}", url);
            println!("    scheme={}, host={}, port={:?}, path={}",
                parts.scheme, parts.host, parts.port, parts.path);
        }
    }

    println!("\n=== 3. 전체 매치 찾기 (find_all) ===");
    // 텍스트에서 모든 숫자 패턴 추출
    let text = "가격: 15000원, 할인: -3000원, 최종: 12000원 (VAT 10.5% 포함)";
    let numbers = SimpleMatcher::find_numbers(text);
    println!("  텍스트: {}", text);
    for (pos, num) in &numbers {
        println!("    위치 {}: {}", pos, num);
    }

    println!("\n=== 4. 치환 (replace) ===");
    // 마스킹 - 민감 정보 숨김
    let input = "주문번호: 010-1234-5678, 연락처: 010-9876-5432";
    let masked = SimpleMatcher::replace_pattern(input, &["1234", "5678", "9876", "5432"], "****");
    println!("  원본: {}", input);
    println!("  마스킹: {}", masked);

    println!("\n=== 5. 로그 파싱 ===");
    // 로그 한 줄씩 파싱
    let logs = vec![
        "[2026-04-04 15:30:00] [INFO] 서버 시작됨",
        "[2026-04-04 15:30:05] [WARN] 메모리 사용량 80%",
        "[2026-04-04 15:31:00] [ERROR] 데이터베이스 연결 실패",
        "잘못된 형식의 로그",
    ];

    for log in &logs {
        match parse_log_line(log) {
            Some(entry) => println!("  {:?}", entry),
            None => println!("  파싱 실패: {}", log),
        }
    }

    // ERROR 로그만 필터 - filter_map + filter 체이닝
    let errors: Vec<LogEntry> = logs.iter()
        .filter_map(|line| parse_log_line(line))
        .filter(|entry| entry.level == "ERROR")
        .collect();
    println!("\n  에러 로그 {}건: {:?}", errors.len(), errors);

    // regex 크레이트 사용법
    println!("\n=== regex 크레이트 사용 시 패턴 ===");
    println!("let re = Regex::new(r\"패턴\").unwrap();");
    println!("re.is_match(text)        -> bool");
    println!("re.find(text)            -> Option<Match>");
    println!("re.find_iter(text)       -> 모든 매치 이터레이터");
    println!("re.captures(text)        -> 캡처 그룹");
    println!("re.replace(text, \"대체\") -> 교체");
    println!("re.replace_all(...)      -> 전체 교체");
}
```

**실행 결과** — 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다).

**풀이 요점**
- 판정 함수는 모두 「구분자로 자르기 → 조각 수 확인 → 조각별 조건을 `&&` 로 잇기」의 같은 꼴이다.
- `parse_url` 의 `?` 하나가 「`://` 없으면 전체 실패」를 맡고, `unwrap_or` 와 `.ok()` 는 경로 · 포트가 없거나 틀려도 실패시키지 않는다.
- `find_numbers` 의 위치는 문자 번호다 — `Vec<char>` 로 바꾼 뒤 세기 때문이다.
- `replace_pattern` 은 글자열 목록 교체라, 모양으로 찾는 정규식 `replace_all` 과 덮는 범위가 다르다.
- 로그는 `match` 로 실패를 찍고, ERROR 필터는 `filter_map` 으로 실패를 버린다 — 같은 `Option` 을 두 방식으로 다룬다.
- 실전에서는 각 함수 주석의 정규식을 `OnceLock` 에 한 번만 컴파일해 두고 `is_match` · `captures` · `find_iter` · `replace_all` 로 바꿔 쓸 수 있다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
