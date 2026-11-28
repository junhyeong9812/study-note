# rust/rust-testing-security/15 — unsafe 코드 감사 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. `Some(5)` · `None` · `[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
Some(5)
None
[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
```

**왜 그런가**
- `push` 가 0 부터 9 까지를 차례로 `data[0]` ~ `data[9]` 에 쓰고 `len` 은 10 이 된다.
- `get(5)` 는 `5 < 10` 이므로 `Some(data[5])`, 곧 `Some(5)` 다.
- `get(100)` 은 `100 < 10` 이 거짓이라 `None` 이다 — 배열 길이 256 안이어도 `len` 밖이면 `None` 이다.
- `as_slice()` 는 `&data[..10]` 이므로 넣은 열 개만 보인다.
- 근거: 2-summary 「동작 방식 (1)」.

### 2. 세 줄 — 첫 줄에 `[미검증]`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
ffi.rs:15 [미검증]
  이유: C 라이브러리 FFI 호출
  불변량: 포인터가 유효하고 null이 아님
```

**왜 그런가**
- `Display` 의 형식 문자열이 `"{}:{} [{}]\n  이유: {}\n  불변량: {}"` 이라 `\n` 두 개로 세 줄이 된다.
- `verified` 가 `false` 이므로 `if` 가 「미검증」을 고른다.
- 둘째 · 셋째 줄 앞의 공백 두 칸은 형식 문자열에 들어 있는 것이다.
- 근거: 2-summary 「동작 방식 (5)」.

### 3. `Err("버퍼가 가득 찼습니다")` — `unwrap` 을 붙이면 패닉

- `push` 는 `len >= 256` 이면 아무것도 쓰지 않고 `Err("버퍼가 가득 찼습니다")` 를 돌려준다.
- `push` 자체는 패닉을 내지 않는다 — 실패를 값으로 알린다.
- 하지만 호출자가 `.unwrap()` 을 붙였다면 `Err` 를 만난 `unwrap` 이 패닉을 낸다 (원본에 근거 없음 — 추론: `Result::unwrap` 의 일반 동작).
- 어느 쪽이든 배열 밖에 쓰는 일은 없으므로 메모리는 안전하다.
- 근거: 2-summary 「동작 방식 (1)」.

### 4. 검사를 빼서 안전 책임이 호출자에게 넘어가기 때문이다

- `get` 은 스스로 `index < len` 을 검사하므로 어떤 값을 넣어도 안전하다.
- `get_unchecked` 는 그 검사를 생략하고 바로 읽으므로, 범위 밖 값이 들어오면 UB 가 될 수 있다.
- 함수가 막지 못하는 조건이 있으니 그것을 지킬 책임은 호출자에게 있다.
- `unsafe fn` 표시는 그 책임 이전을 타입에 새겨, 호출자가 `unsafe` 블록 없이는 부를 수 없게 만든다.
- 근거: 2-summary 「동작 방식 (2)」.

### 5. `# Safety` 는 함수 정의 쪽의 계약, `// SAFETY:` 는 호출 블록 쪽의 이행 기록이다

- `/// # Safety` 는 `unsafe fn` 의 문서 주석에 달아 「이 함수를 부르려면 무엇을 지켜야 하나」를 적는다.
- `// SAFETY:` 는 `unsafe` 블록 바로 위에 달아 「이 자리에서는 그 조건이 왜 성립하나」를 적는다.
- 계약만 있으면 각 호출 자리가 정말 지켰는지 알 수 없고, 이행 기록만 있으면 무엇을 지켜야 했는지 알 수 없다.
- 둘이 짝을 이뤄야 감사하는 사람이 「계약 → 이행」을 한 자리씩 대조할 수 있다.
- 근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 3」.

### 6. 막지 못한다 — 릴리스에서는 검사가 사라진다

- `debug_assert!` 는 디버그 빌드에서만 조건을 검사한다.
- 릴리스 빌드에서는 검사 코드가 빠지므로 `get_unchecked(300)` 은 아무 확인 없이 배열 밖을 읽으려 하고, 이는 UB 다.
- 그래서 `debug_assert!` 는 개발 중의 그물이고, 진짜 안전은 `# Safety` 계약과 호출자의 확인에 달려 있다.
- 근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 4」 · 「구현 세부사항 대 언어 보장」.

### 7. `cargo audit` 이다 (라이선스까지 보려면 `cargo deny check`)

- Miri 는 내 코드를 실행하며 use-after-free · 범위 밖 접근 · 정렬 · 데이터 레이스 · 미초기화 읽기 같은 UB 를 찾는다.
- 의존성 크레이트의 「알려진 취약점」을 보는 것은 `cargo audit` 이다.
- `cargo deny check` 는 라이선스와 보안을 함께 검사한다.
- 보는 대상이 다르므로 서로를 대신하지 못한다.
- 근거: 2-summary 「동작 방식 (7)」 · 「어디서 틀리나 8」.

### 8. 자동 도출이 「T 가 Send 일 때만」 붙여 주는 조건을 지워 버리기 때문이다

- 컴파일러는 필드가 모두 `Send` 일 때만 `SafeWrapper<T>` 에 `Send` 를 자동으로 붙인다.
- 바운드 없는 `unsafe impl<T> Send` 는 그 조건을 없애고 「어떤 `T` 든 보내도 된다」고 약속한다.
- 스레드 안전하지 않은 `T` 를 감싸도 래퍼가 `Send` 가 되어 다른 스레드로 넘어갈 수 있다.
- 그래서 기본은 자동 도출에 맡기고, 꼭 명시하려면 `unsafe impl<T: Send> Send` 처럼 바운드를 붙인다.
- 근거: 2-summary 「동작 방식 (6)」 · 「어디서 틀리나 7」.

### 9. 전역 상태 → `OnceCell`·`LazyLock`, 내부 가변성 → `Cell`·`RefCell`·`Mutex`, 원시 포인터 → 참조·`Box`·`Rc`·`Arc`

- 원본의 대안 표가 그대로 답이다.
- 그 밖에 경계 검사 제거 → `get()` + `unwrap`, FFI → `bindgen` + 안전 래퍼, `transmute` → `From`/`Into`, `as` 캐스트가 있다.
- 원본 팁의 결론은 「대부분의 경우 unsafe 없이도 해결할 수 있는 안전한 대안이 있다」이다.
- 근거: 2-summary 「어디서 틀리나 9」.

### 10. `count` 가 두 슬라이스 길이를 넘지 않는다는 조건 하나다

- 인자가 `&[u8]` 과 `&mut [u8]` 이므로 빌림 규칙이 이미 「둘 다 유효하다」와 「둘은 겹치지 않는다」를 보장한다.
- 호출자가 스스로 지켜야 남는 것은 `count <= src.len()` 과 `count <= dst.len()` 뿐이다.
- 원본은 이 둘을 `debug_assert!` 로 검사하지만 릴리스에서는 빠지므로, 계약으로 남아 있어야 한다.
- 이 분석은 원본 계약에 대한 의문으로 정리에 적은 것이다 (원본에 근거 없음 — 추론).
- 근거: 2-summary 「어디서 틀리나 6」 · 「구현 세부사항 대 언어 보장」.

## 실습 정답

### 실습 1. 안전한 추상화 버퍼와 unsafe 감사 데모 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 256 바이트 배열 + `len`, 0 으로 초기화 | `struct FixedBuffer { data: [u8; 256], len: usize }` · `FixedBuffer::new` |
| 2. 가득 차면 `Err`, 아니면 쓰고 `len` 증가 | `FixedBuffer::push` 의 `if self.len >= 256` |
| 3. 범위 안이면 `Some`, 밖이면 `None` | `FixedBuffer::get` 의 `if index < self.len` |
| 4. `unsafe fn` + 조건 주석 + `debug_assert!` + 배열 `get_unchecked` | `pub unsafe fn get_unchecked` · `// SAFETY: caller는 …` · `debug_assert!(index < self.len, …)` · `*self.data.get_unchecked(index)` |
| 5. 길이와 사용 영역 슬라이스 | `FixedBuffer::len` · `as_slice` 의 `&self.data[..self.len]` |
| 6. 격리 모듈의 두 unsafe 함수 + `# Safety` | `mod raw_utils` · `bytes_to_str_unchecked` · `copy_nonoverlapping` |
| 7. 검증하는 안전한 변환 | `safe_bytes_to_str` 의 `std::str::from_utf8(bytes)` |
| 8. 감사 기록 다섯 필드 + Display 세 줄 | `struct UnsafeAudit` · `impl fmt::Display for UnsafeAudit` 의 `write!` |
| 9. `unsafe impl` 없는 래퍼, 잘못된 꼴은 주석 | `struct SafeWrapper<T>` 와 그 아래 주석 세 줄 |
| 10. 0..10 push 후 `get(5)` · `get(100)` · 슬라이스 출력 | `main` 의 `for i in 0..10` 과 `println!` 세 줄 |
| 11. `unsafe` 블록 + SAFETY 주석 + `get_unchecked(5)` | `main` 의 `unsafe { // SAFETY: … }` |
| 12. `b"Hello, Rust!"` 를 `match` | `match safe_bytes_to_str(bytes)` |
| 13. 감사 기록 출력 + 빈 줄 | `for audit in &audits { println!("{}", audit); println!(); }` |
| 14. 규칙 · Miri · 대안 표 · 의존성 감사 안내 | `main` 뒤쪽 `println!` 묶음 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`rust/rust-testing-security/reference/unsafe-audit.rs`

```rust
// [테스팅 & 보안] unsafe 코드 감사
// 설명: unsafe 코드 감사, Miri, 안전한 추상화 패턴, unsafe 최소화
// 팁: unsafe 코드는 최소한으로, 안전한 API로 감싸서 노출한다. 모든 unsafe 블록에 // SAFETY: 주석을 달아 불변량을 명시한다. Miri(cargo +nightly miri test)로 정의되지 않은 동작을 감지하고, cargo audit로 의존성 취약점을 검사한다. 대부분의 경우 unsafe 없이도 해결할 수 있는 안전한 대안이 있다.

// === unsafe 코드 감사 & 안전한 추상화 패턴 ===

// Display 구현을 위한 fmt 모듈
use std::fmt;

// === 1. unsafe가 필요한 상황과 대안 ===

// 예시: 안전한 추상화로 감싼 unsafe
// 256바이트 고정 크기 버퍼 - 내부 표현은 배열이지만 안전한 API 제공
pub struct FixedBuffer {
    // 고정 크기 백킹 배열
    data: [u8; 256],
    // 현재 사용 중인 길이 - 길이 추적으로 안전한 인덱싱 가능
    len: usize,
}

impl FixedBuffer {
    // 빈 버퍼 생성 - 모든 바이트 0
    pub fn new() -> Self {
        FixedBuffer {
            data: [0u8; 256],
            len: 0,
        }
    }

    // 안전한 public API
    // 가득 차면 에러 반환 - 패닉 없음
    pub fn push(&mut self, byte: u8) -> Result<(), &'static str> {
        if self.len >= 256 {
            return Err("버퍼가 가득 찼습니다");
        }
        self.data[self.len] = byte;
        self.len += 1;
        Ok(())
    }

    // 안전한 인덱스 접근 - 범위 밖이면 None
    pub fn get(&self, index: usize) -> Option<u8> {
        if index < self.len {
            Some(self.data[index])
        } else {
            None
        }
    }

    // unsafe 사용이 필요한 경우: 성능 최적화
    // SAFETY: caller는 index < self.len을 보장해야 함
    // 경계 검사 없는 인덱싱 - 호출자가 안전성 책임
    pub unsafe fn get_unchecked(&self, index: usize) -> u8 {
        // 디버그 빌드에서는 불변량 검증
        debug_assert!(index < self.len, "인덱스 범위 초과: {} >= {}", index, self.len);
        // 표준 라이브러리의 unsafe 메서드 호출
        *self.data.get_unchecked(index)
    }

    pub fn len(&self) -> usize {
        self.len
    }

    // 사용 중인 영역만 슬라이스로 노출 (안전)
    pub fn as_slice(&self) -> &[u8] {
        &self.data[..self.len]
    }
}

// === 2. unsafe 블록 최소화 + 문서화 ===

/// 안전하지 않은 코드를 최소한으로 격리하는 패턴
// unsafe 함수들을 한 곳에 모아 감사 영역을 줄임
mod raw_utils {
    /// 바이트 슬라이스를 &str로 변환 (UTF-8 검증 없이)
    ///
    /// # Safety
    /// - `bytes`는 유효한 UTF-8이어야 합니다.
    // UTF-8 검증을 건너뛰는 빠른 변환 - 위배 시 UB
    pub unsafe fn bytes_to_str_unchecked(bytes: &[u8]) -> &str {
        std::str::from_utf8_unchecked(bytes)
    }

    /// 두 슬라이스를 겹치지 않게 복사
    ///
    /// # Safety
    /// - src와 dst는 겹치지 않아야 합니다.
    /// - 두 포인터 모두 유효해야 합니다.
    /// - count는 두 슬라이스의 길이를 초과하지 않아야 합니다.
    // 메모리 복사 - 겹치면 UB
    pub unsafe fn copy_nonoverlapping(src: &[u8], dst: &mut [u8], count: usize) {
        // 디버그 빌드에서 길이 불변량 검증
        debug_assert!(count <= src.len());
        debug_assert!(count <= dst.len());
        std::ptr::copy_nonoverlapping(src.as_ptr(), dst.as_mut_ptr(), count);
    }
}

// 안전한 래퍼
// UTF-8 검증을 수행하는 안전한 변환 - 항상 이쪽을 우선 사용
fn safe_bytes_to_str(bytes: &[u8]) -> Result<&str, std::str::Utf8Error> {
    std::str::from_utf8(bytes) // 안전한 버전
}

// === 3. unsafe 감사 체크리스트 ===

// unsafe 블록 감사 기록 - 코드 리뷰 추적용
struct UnsafeAudit {
    file: String,
    line: u32,
    // unsafe가 필요한 이유
    reason: String,
    // 호출자가 지켜야 할 불변량
    safety_invariant: String,
    // 코드 리뷰에서 검증 완료 여부
    verified: bool,
}

// 감사 기록을 사람이 읽기 좋게 출력
impl fmt::Display for UnsafeAudit {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}:{} [{}]\n  이유: {}\n  불변량: {}",
            self.file, self.line,
            if self.verified { "검증됨" } else { "미검증" },
            self.reason, self.safety_invariant)
    }
}

// === 4. Send/Sync 안전성 ===

// 일반 래퍼 - T의 Send/Sync 자동 도출
struct SafeWrapper<T> {
    inner: T,
}

// 이렇게 하면 안 됨 (unsafe impl은 신중하게):
// unsafe impl<T> Send for SafeWrapper<T> {}
// unsafe impl<T> Sync for SafeWrapper<T> {}

// 올바른 방법: T가 Send/Sync면 자동으로 됨
// 또는 명시적 바운드:
// unsafe impl<T: Send> Send for SafeWrapper<T> {}

// 메인: FixedBuffer 사용/안전한 대안/감사 체크리스트/Miri/대안 표 출력
fn main() {
    // === FixedBuffer 사용 ===
    println!("=== 안전한 추상화 ===");
    let mut buf = FixedBuffer::new();
    // 0~9 푸시
    for i in 0..10 {
        buf.push(i).unwrap();
    }

    // 안전한 접근 - 범위 밖은 None
    println!("안전한 get(5): {:?}", buf.get(5));
    println!("안전한 get(100): {:?}", buf.get(100)); // None
    println!("슬라이스: {:?}", buf.as_slice());

    // unsafe 접근 (성능 최적화가 정말 필요할 때만)
    unsafe {
        // SAFETY: 0..10까지 push했으므로 인덱스 5는 유효
        let val = buf.get_unchecked(5);
        println!("unsafe get_unchecked(5): {}", val);
    }

    // === safe 대안 ===
    println!("\n=== 안전한 대안 ===");
    let bytes = b"Hello, Rust!";
    // UTF-8 검증을 거치는 안전한 경로
    match safe_bytes_to_str(bytes) {
        Ok(s) => println!("안전한 변환: {}", s),
        Err(e) => println!("UTF-8 에러: {}", e),
    }

    // === unsafe 감사 로그 ===
    println!("\n=== unsafe 감사 체크리스트 ===");
    // 두 가지 unsafe 사용 사례 기록
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

    // 감사 결과 출력
    for audit in &audits {
        println!("{}", audit);
        println!();
    }

    // === unsafe 사용 규칙 ===
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

    // === cargo audit ===
    println!("\n=== 의존성 보안 감사 ===");
    println!("cargo install cargo-audit");
    println!("cargo audit              -> 알려진 취약점 검사");
    println!("cargo install cargo-deny");
    println!("cargo deny check         -> 라이선스 + 보안 검사");
}
```

**실행 결과** — 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다).

**풀이 요점**
- 안전성의 중심은 `len` 필드다 — `push` · `get` · `as_slice` 가 모두 이것으로 경계를 지킨다.
- `get_unchecked` 를 `unsafe fn` 으로 둔 덕분에 `main` 은 `unsafe` 블록과 `// SAFETY:` 주석 없이는 그것을 부를 수 없다.
- `debug_assert!` 는 디버그 빌드에서만 조건을 확인하므로 계약 주석을 대신하지 않는다.
- 위험한 변환 · 복사는 `raw_utils` 한 곳에 모았고, 실제로 쓰는 것은 검증하는 `safe_bytes_to_str` 이다.
- `SafeWrapper<T>` 는 아무것도 직접 구현하지 않아 `T` 에 따라 `Send`/`Sync` 가 자동으로 정해진다.
- `UnsafeAudit` 의 `Display` 는 형식 문자열의 `\n` 과 들여쓰기로 한 기록을 세 줄로 만든다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
