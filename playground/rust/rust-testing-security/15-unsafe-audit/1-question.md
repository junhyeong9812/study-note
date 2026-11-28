# rust/rust-testing-security/15 — unsafe 코드 감사 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 0 부터 9 까지 넣은 FixedBuffer 를 읽으면 (예측)

```rust
// 질문용 발췌
let mut buf = FixedBuffer::new();
for i in 0..10 { buf.push(i).unwrap(); }
println!("{:?}", buf.get(5));
println!("{:?}", buf.get(100));
println!("{:?}", buf.as_slice());
```

- 세 `println!` 은 각각 무엇을 찍는다고 예상하나?

### 2. 감사 기록 하나를 Display 로 찍으면 (예측)

```rust
// 질문용 발췌
let a = UnsafeAudit {
    file: "ffi.rs".to_string(),
    line: 15,
    reason: "C 라이브러리 FFI 호출".to_string(),
    safety_invariant: "포인터가 유효하고 null이 아님".to_string(),
    verified: false,
};
println!("{}", a);
```

- 몇 줄이 어떤 모양으로 찍힌다고 예상하나?

### 3. 가득 찬 버퍼에 한 번 더 넣기 (경계)
- 256 바이트를 다 채운 `FixedBuffer` 에 `push` 를 한 번 더 부르면 무엇이 돌아오나?
- 거기에 `.unwrap()` 까지 붙여 두었다면 프로그램은 어떻게 되나?

### 4. `get_unchecked` 가 `unsafe fn` 인 까닭 (왜)
- 같은 일을 하는 `get` 은 안전한 함수인데, `get_unchecked` 는 왜 `unsafe fn` 으로 표시해야 하나?

### 5. 조건을 두 군데에 적는 까닭 (왜)
- `/// # Safety` 문서와 `// SAFETY:` 주석은 각각 어디에 달리고, 왜 둘 다 필요한가?

### 6. 릴리스 빌드의 `debug_assert!` (경계)
- 릴리스 빌드에서 `get_unchecked(300)` 처럼 조건을 어긴 호출이 들어오면 `debug_assert!` 가 막아 주나?

### 7. Miri 와 cargo audit 이 보는 범위 (경계)
- 의존성 크레이트의 알려진 취약점을 찾고 싶다면 Miri 와 `cargo audit` 중 무엇을 돌려야 하나?

### 8. 바운드 없는 `unsafe impl Send` 와 자동 도출 (연결)
- `unsafe impl<T> Send for SafeWrapper<T> {}` 가 위험한 것은 auto trait 의 자동 도출 규칙과 어떻게 이어지나?

### 9. unsafe 를 대신할 안전한 도구 (연결)
- 전역 상태 · 내부 가변성 · 원시 포인터가 필요해 보일 때 각각 어떤 안전한 도구로 바꿀 수 있나?

### 10. `copy_nonoverlapping` 의 계약과 빌림 규칙 (경계)
- 원본 `raw_utils::copy_nonoverlapping` 의 세 가지 `# Safety` 조건 가운데 호출자가 실제로 지켜야 하는 것은 무엇인가?

## 실습

### 실습 1. 안전한 추상화 버퍼와 unsafe 감사 데모 만들기

**만들 것** — 경계 검사를 하는 안전한 API 안에 `unsafe` 읽기를 감춘 256 바이트 버퍼, 위험한 함수를 모은 모듈, 감사 기록 타입을 만들고, `main` 에서 이것들을 써 본 뒤 unsafe 규칙 · Miri · 대안 표 · 의존성 감사 안내를 출력한다.

**요구 조건**

1단계 — 안전한 추상화 `FixedBuffer`

1. `FixedBuffer` 는 256 바이트 배열 `data` 와 사용 중인 길이 `len` 을 가진다. `new()` 는 모든 바이트를 0, `len` 을 0 으로 만든다.
2. `push(byte)` 는 `len` 이 256 이상이면 `Err("버퍼가 가득 찼습니다")` 를 돌려주고, 아니면 `data[len]` 에 쓰고 `len` 을 1 늘린 뒤 `Ok(())` 를 돌려준다.
3. `get(index)` 는 `index < len` 이면 `Some(값)`, 아니면 `None` 을 돌려준다.
4. `get_unchecked(index)` 는 `unsafe fn` 이다. 호출자가 `index < self.len` 을 보장해야 한다는 조건을 주석으로 적고, `debug_assert!` 로 그 조건을 검사(메시지에 `index` 와 `len` 을 넣는다)한 뒤 배열의 `get_unchecked` 로 값을 읽어 돌려준다.
5. `len()` 은 길이를, `as_slice()` 는 `data` 의 앞쪽 `len` 개만 슬라이스로 돌려준다.

2단계 — unsafe 격리와 안전한 쌍둥이

6. `mod raw_utils` 안에 `unsafe fn bytes_to_str_unchecked(&[u8]) -> &str`(`std::str::from_utf8_unchecked` 사용)과 `unsafe fn copy_nonoverlapping(src, dst, count)`(`count` 가 두 길이를 넘지 않음을 `debug_assert!` 두 개로 검사한 뒤 `std::ptr::copy_nonoverlapping` 호출)을 두고, 각각 `/// # Safety` 문서로 조건을 적는다.
7. 안전한 함수 `safe_bytes_to_str(&[u8]) -> Result<&str, std::str::Utf8Error>` 는 `std::str::from_utf8` 의 결과를 그대로 돌려준다.

3단계 — 감사 기록과 Send/Sync

8. `UnsafeAudit` 는 `file` · `line` · `reason` · `safety_invariant` · `verified` 다섯 필드를 가진다. `fmt::Display` 를 구현해 「`파일:줄 [검증됨|미검증]`」, 다음 줄 「`  이유: …`」, 다음 줄 「`  불변량: …`」 꼴로 쓴다(`verified` 가 참이면 검증됨).
9. `SafeWrapper<T>` 는 `inner: T` 하나만 가지며 `unsafe impl` 을 쓰지 않는다. 잘못된 꼴(바운드 없는 `unsafe impl`)과 바운드를 붙인 꼴은 주석으로만 남긴다.

4단계 — `main`

10. 버퍼에 0 부터 9 까지 `push` 하고, `get(5)` · `get(100)` · `as_slice()` 를 출력한다.
11. `unsafe` 블록 안에서 `// SAFETY:` 주석과 함께 `get_unchecked(5)` 를 불러 출력한다.
12. `b"Hello, Rust!"` 를 `safe_bytes_to_str` 에 넘겨 `match` 로 `Ok` 면 변환 결과를, `Err` 면 에러를 출력한다.
13. 시작 코드에 있는 감사 기록 두 개를 `for` 로 돌며 `Display` 로 출력하고, 기록마다 빈 줄을 하나 더 찍는다.
14. 시작 코드에 채워 둔 규칙 · Miri · 대안 표 · 의존성 감사 안내 출력을 그대로 둔다.

**시작 코드**

```rust
// unsafe 코드 감사 & 안전한 추상화 패턴 — 연습 파일

use std::fmt;

pub struct FixedBuffer {
    data: [u8; 256],
    len: usize,
}

impl FixedBuffer {
    pub fn new() -> Self {
        // TODO: 모든 바이트 0, len 0
        todo!()
    }

    pub fn push(&mut self, byte: u8) -> Result<(), &'static str> {
        // TODO: 가득 차면 Err("버퍼가 가득 찼습니다"), 아니면 쓰고 len 증가
        todo!()
    }

    pub fn get(&self, index: usize) -> Option<u8> {
        // TODO: index < len 이면 Some, 아니면 None
        todo!()
    }

    // TODO: get_unchecked — 경계 검사 없는 읽기
    //   - 호출자에게 책임을 넘기는 함수로 선언
    //   - 조건(index < self.len)을 주석으로 적기
    //   - debug_assert! 로 조건 검사 (메시지: "인덱스 범위 초과: {} >= {}")
    //   - 배열의 get_unchecked 로 읽기

    pub fn len(&self) -> usize {
        self.len
    }

    pub fn as_slice(&self) -> &[u8] {
        // TODO: 사용 중인 영역만
        todo!()
    }
}

/// 안전하지 않은 코드를 최소한으로 격리하는 패턴
mod raw_utils {
    // TODO: bytes_to_str_unchecked — # Safety 문서 + from_utf8_unchecked
    // TODO: copy_nonoverlapping — # Safety 문서 + debug_assert! 두 개 + ptr::copy_nonoverlapping
}

fn safe_bytes_to_str(bytes: &[u8]) -> Result<&str, std::str::Utf8Error> {
    // TODO: 검증하는 안전한 변환
    todo!()
}

struct UnsafeAudit {
    file: String,
    line: u32,
    reason: String,
    safety_invariant: String,
    verified: bool,
}

impl fmt::Display for UnsafeAudit {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        // TODO: "파일:줄 [검증됨|미검증]\n  이유: …\n  불변량: …"
        todo!()
    }
}

struct SafeWrapper<T> {
    inner: T,
}
// TODO: 잘못된 unsafe impl 꼴과 바운드를 붙인 꼴을 주석으로만 남긴다

fn main() {
    println!("=== 안전한 추상화 ===");
    // TODO: 버퍼에 0..10 push
    // TODO: get(5), get(100), as_slice 출력
    //   "안전한 get(5): {:?}" / "안전한 get(100): {:?}" / "슬라이스: {:?}"

    // TODO: unsafe 블록 + SAFETY 주석 + get_unchecked(5)
    //   "unsafe get_unchecked(5): {}"

    println!("\n=== 안전한 대안 ===");
    let bytes = b"Hello, Rust!";
    // TODO: safe_bytes_to_str 를 match
    //   Ok → "안전한 변환: {}" / Err → "UTF-8 에러: {}"

    println!("\n=== unsafe 감사 체크리스트 ===");
    let audits = vec![
        UnsafeAudit {
            file: "buffer.rs".to_string(),
            line: 42,
            reason: "경계 검사 없는 인덱스 접근 (성능)".to_string(),
            safety_invariant: "호출자가 index < self.len 보장".to_string(),
            verified: true,
        },
        UnsafeAudit {
            file: "ffi.rs".to_string(),
            line: 15,
            reason: "C 라이브러리 FFI 호출".to_string(),
            safety_invariant: "포인터가 유효하고 null이 아님".to_string(),
            verified: true,
        },
    ];
    // TODO: 기록마다 Display 로 출력하고 빈 줄 하나

    println!("=== unsafe 사용 규칙 ===");
    println!("1. unsafe는 최소한으로 사용한다");
    println!("2. unsafe 블록마다 // SAFETY: 주석 필수");
    println!("3. debug_assert!로 불변량 검증");
    println!("4. 안전한 public API로 감싸서 노출");
    println!("5. unsafe impl Send/Sync은 매우 신중하게");

    println!("\n=== Miri: 정의되지 않은 동작 감지 ===");
    println!("설치: rustup +nightly component add miri");
    println!("실행: cargo +nightly miri test");
    println!();
    println!("Miri가 감지하는 것:");
    println!("  - 해제된 메모리 접근 (use-after-free)");
    println!("  - 범위 밖 접근 (out-of-bounds)");
    println!("  - 유효하지 않은 정렬");
    println!("  - 데이터 레이스");
    println!("  - 미초기화 메모리 읽기");

    println!("\n=== unsafe 대안 ===");
    println!("┌──────────────────────┬──────────────────────┐");
    println!("│ unsafe가 필요한 경우 │ 안전한 대안           │");
    println!("├──────────────────────┼──────────────────────┤");
    println!("│ 경계 검사 제거       │ get() + unwrap       │");
    println!("│ FFI                  │ bindgen + 안전 래퍼  │");
    println!("│ 전역 상태            │ OnceCell, LazyLock   │");
    println!("│ 내부 가변성          │ Cell, RefCell, Mutex │");
    println!("│ 원시 포인터          │ 참조, Box, Rc, Arc   │");
    println!("│ transmute            │ From/Into, as 캐스트 │");
    println!("└──────────────────────┴──────────────────────┘");

    println!("\n=== 의존성 보안 감사 ===");
    println!("cargo install cargo-audit");
    println!("cargo audit              -> 알려진 취약점 검사");
    println!("cargo install cargo-deny");
    println!("cargo deny check         -> 라이선스 + 보안 검사");
}
```

**확인 방법** — `rustc unsafe-audit.rs && ./unsafe-audit` (또는 Cargo 프로젝트의 `src/main.rs` 에 두고 `cargo run`)로 돌려 `get(5)` · `get(100)` · 슬라이스 · `get_unchecked(5)` · 변환 결과 · 감사 기록 두 개가 요구 조건대로 찍히는지 본다. 테스트를 붙였다면 `cargo +nightly miri test` 로 UB 가 보고되지 않는지도 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
