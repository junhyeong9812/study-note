# rust/rust-practical/04 — Regex 정규 표현식 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. `is_ipv4` 에 다섯 입력을 넣으면 (예측)

```rust
// 질문용 발췌
let ips = vec!["192.168.1.1", "256.1.1.1", "10.0.0.1", "1.2.3", "01.02.03.04"];
for ip in &ips {
    println!("  '{}' -> IPv4: {}", ip, SimpleMatcher::is_ipv4(ip));
}
```

- 다섯 입력 각각에 `true` · `false` 중 무엇이 나오고, `false` 라면 어느 검사에서 걸리나?

### 2. `find_numbers` 가 돌려주는 위치와 값 (예측)

```rust
// 질문용 발췌
let text = "가격: 15000원, 할인: -3000원, 최종: 12000원 (VAT 10.5% 포함)";
for (pos, num) in &SimpleMatcher::find_numbers(text) {
    println!("    위치 {}: {}", pos, num);
}
```

- 몇 개의 (위치, 값) 쌍이 나오고, 각각의 위치와 값은 무엇인가?

### 3. 경로가 없거나 `/` 뿐인 URL (예측)

```rust
// 질문용 발췌
let a = SimpleMatcher::parse_url("https://example.com/");
let b = SimpleMatcher::parse_url("http://localhost:3000");
let c = SimpleMatcher::parse_url("localhost:3000/health");
```

- `a` · `b` · `c` 는 각각 `Some(…)` 인가 `None` 인가, `Some` 이라면 `port` 와 `path` 는 무엇인가?

### 4. `Regex::new` 를 한 번만 부르라는 까닭 (왜)

- 왜 `Regex::new` 를 반복문 안이 아니라 `OnceLock` · `lazy_static!` 으로 한 번만 불러야 하나?

### 5. 이름 붙은 캡처를 권하는 까닭 (왜)

- 왜 `(?P<name>...)` 처럼 그룹에 이름을 붙이는 편이 번호 그룹보다 나은가?

### 6. 역추적 없이 선형 시간이라는 성질 (왜)

- `regex` 크레이트가 역추적 없이 선형 시간에 동작한다는 것이 입력이 길 때 왜 중요한가?

### 7. `replace_pattern` 마스킹이 덮지 못하는 입력 (경계)

- 입력에 목록에 없는 전화번호 `010-1111-2222` 가 끼어 있으면 `replace_pattern` 의 마스킹은 어떻게 되고, 정규식 `replace_all` 이면 무엇이 다른가?

### 8. 주석의 이메일 정규식과 `is_email` 의 차이 (경계)

- `"a+b@example.com"` 은 주석의 정규식 `^[\w.+-]+@[\w.-]+\.\w+$` 와 손 구현 `is_email` 에서 각각 어떻게 판정되나?

### 9. 손 구현 함수와 `regex` 메서드의 짝 (연결)

- 예제의 `is_email` · `find_numbers` · `parse_url` · `replace_pattern` 은 각각 `regex` 크레이트의 어느 메서드 역할을 흉내 내나?

### 10. ERROR 로그 필터의 `filter_map` (연결)

- `parse_log_line` 이 `Option<LogEntry>` 를 돌려준다는 것이 ERROR 필터에서 `filter_map` 을 쓰는 까닭과 어떻게 이어지나?

## 실습

### 실습 1. 정규식 없이 정규식 흉내 내기 — 검증 · 캡처 · 찾기 · 교체 · 로그 파싱

**만들 것** — `regex` 크레이트 없이 표준 라이브러리만으로 정규식의 다섯 가지 쓰임(판정 · 캡처 · 전체 찾기 · 교체 · 이름 붙은 캡처)을 흉내 내는 콘솔 프로그램.

**준비물** — Rust 컴파일러만 있으면 된다. `regex` 크레이트는 쓰지 않는다 — 크레이트의 동작을 손 구현으로 흉내 낸 것이다.

**요구 조건**

1단계 — 판정 (`SimpleMatcher`)
1. `is_email` 은 `@` 로 잘라 정확히 두 조각인지 보고, local 이 비지 않았고, domain 에 `.` 이 있되 `.` 으로 시작 · 끝나지 않으며, local 이 영숫자 · `.` · `_` · `-` 로만 되어 있으면 `true` 다.
2. `is_phone` 은 `-` 로 잘라 세 조각이고, 첫 조각이 `"010"`, 나머지 두 조각이 각각 길이 4 의 ASCII 숫자면 `true` 다.
3. `is_ipv4` 는 `.` 으로 잘라 네 조각이고, 모든 조각이 `u8` 로 파싱되며 한 글자이거나 `0` 으로 시작하지 않으면 `true` 다.

2단계 — 캡처
4. `parse_url` 은 `"://"` 에서 scheme 을 떼고(없으면 `None`), 첫 `/` 에서 host·port 부분과 경로를 나누며(없으면 경로는 빈 문자열), `:` 이 있으면 포트를 `u16` 으로 파싱해(실패하면 `None`) `UrlParts` 를 돌려준다.
5. `UrlParts` 는 `scheme` · `host` · `port: Option<u16>` · `path` 필드를 갖고, `path` 는 앞에 `/` 를 붙인 경로다.

3단계 — 전체 찾기와 교체
6. `find_numbers` 는 문자 배열을 한 글자씩 보며, 숫자이거나 「`-` 다음이 숫자」인 자리에서 시작해 숫자와 `.` 이 이어지는 동안 모은 덩어리를 (시작 문자 번호, 문자열) 쌍으로 모두 돌려준다.
7. `replace_pattern` 은 주어진 글자열 목록을 차례로 모두 같은 대체 문자열로 바꾼 새 `String` 을 돌려준다.

4단계 — 로그 파싱
8. `parse_log_line` 은 `[시각] [등급] 메시지` 줄에서 `timestamp` · `level` · `message` 를 꺼내 `LogEntry` 로 돌려주고, `[` 로 시작하지 않거나 `]` 가 없으면 `None` 을 돌려준다.
9. `main` 은 로그 네 줄을 하나씩 파싱해 성공이면 `LogEntry` 를 디버그 형식으로, 실패면 `파싱 실패:` 와 원래 줄을 찍는다.
10. `main` 은 `filter_map` 과 `filter` 로 등급이 `"ERROR"` 인 항목만 모아 개수와 함께 찍는다.

5단계 — 정리
11. 마지막에 실제 `regex` 크레이트의 메서드 꼴(`Regex::new` · `is_match` · `find` · `find_iter` · `captures` · `replace` · `replace_all`)을 안내 문구로 찍는다.

**시작 코드**

```rust
// === Regex 패턴: 순수 Rust 정규 표현식 시뮬레이션 ===
struct SimpleMatcher;

impl SimpleMatcher {
    fn is_email(input: &str) -> bool {
        // TODO: '@' 로 두 조각 → local/domain 조건 검사
        todo!()
    }

    fn is_phone(input: &str) -> bool {
        // TODO: '-' 로 세 조각 → "010" + 숫자 4자리 + 숫자 4자리
        todo!()
    }

    fn is_ipv4(input: &str) -> bool {
        // TODO: '.' 로 네 조각 → u8 파싱 + 앞자리 0 금지
        todo!()
    }

    fn parse_url(url: &str) -> Option<UrlParts> {
        // TODO: split_once("://")? → split_once('/') → split_once(':')
        todo!()
    }

    fn find_numbers(input: &str) -> Vec<(usize, String)> {
        // TODO: Vec<char> 로 바꾸고 숫자 덩어리를 (시작 위치, 문자열) 로 모은다
        todo!()
    }

    fn replace_pattern(input: &str, from: &[&str], to: &str) -> String {
        // TODO: 목록의 글자열을 차례로 to 로 바꾼다
        todo!()
    }
}

#[derive(Debug)]
struct UrlParts {
    // TODO: scheme, host, port(Option<u16>), path
}

#[derive(Debug)]
struct LogEntry {
    timestamp: String,
    level: String,
    message: String,
}

fn parse_log_line(line: &str) -> Option<LogEntry> {
    // 형식: [2026-04-04 15:30:00] [INFO] 메시지
    // TODO: 첫 ']' 까지 timestamp, 다음 '[...]' 가 level, 나머지가 message
    todo!()
}

fn main() {
    println!("=== 1. 패턴 매칭 (is_match 동작) ===");
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
    let urls = vec![
        "https://api.example.com:8443/v1/users",
        "http://localhost:3000/health",
        "https://example.com/",
    ];
    for url in &urls {
        // TODO: parse_url 이 Some 이면 URL 과 scheme/host/port/path 를 찍는다
    }

    println!("\n=== 3. 전체 매치 찾기 (find_all) ===");
    let text = "가격: 15000원, 할인: -3000원, 최종: 12000원 (VAT 10.5% 포함)";
    let numbers = SimpleMatcher::find_numbers(text);
    println!("  텍스트: {}", text);
    for (pos, num) in &numbers {
        println!("    위치 {}: {}", pos, num);
    }

    println!("\n=== 4. 치환 (replace) ===");
    let input = "주문번호: 010-1234-5678, 연락처: 010-9876-5432";
    let masked = SimpleMatcher::replace_pattern(input, &["1234", "5678", "9876", "5432"], "****");
    println!("  원본: {}", input);
    println!("  마스킹: {}", masked);

    println!("\n=== 5. 로그 파싱 ===");
    let logs = vec![
        "[2026-04-04 15:30:00] [INFO] 서버 시작됨",
        "[2026-04-04 15:30:05] [WARN] 메모리 사용량 80%",
        "[2026-04-04 15:31:00] [ERROR] 데이터베이스 연결 실패",
        "잘못된 형식의 로그",
    ];
    for log in &logs {
        // TODO: 성공이면 {:?} 로, 실패면 "파싱 실패: ..." 로 찍는다
    }

    // TODO: filter_map + filter 로 ERROR 만 모아 errors 에 담는다
    // println!("\n  에러 로그 {}건: {:?}", errors.len(), errors);

    println!("\n=== regex 크레이트 사용 시 패턴 ===");
    // TODO: Regex::new, is_match, find, find_iter, captures, replace, replace_all 안내 문구
}
```

**확인 방법** — `rustc regex-rust.rs && ./regex-rust` 로 돌려, 각 절의 판정 · 추출 값 · 마스킹 결과 · 로그 파싱 결과가 퀴즈에서 추론한 것과 맞는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
