# rust/rust-testing-security/15 — unsafe 코드 감사 — 정리 (힌트)

> 출처 — study-site 항목 `rust/unsafe-audit`(항목 데이터 `data/rust/testing-security.json`) · 정답 코드 study-practice `rust/rust-testing-security/reference/unsafe-audit.rs`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다).

## 한눈에 — 쉽게 말하면

**`unsafe` 코드는 「집 안의 배전반」이다.**
식구들은 콘센트(안전한 API)만 쓰고, 배전반 뚜껑(`unsafe`)은 자격 있는 사람만 연다.
뚜껑을 열 때마다 작업 일지(`// SAFETY:` 주석)에 「무엇을 왜 건드렸고 어떤 조건을 지켰나」를 적는다.
정기 점검원(Miri)이 배선을 실제로 돌려 보며 위험을 찾고, 부품 리콜 목록(`cargo audit`)으로 사다 쓴 부품을 확인한다.
Rust 의 `unsafe` 감사도 똑같은 구조다.

> **unsafe** — 컴파일러가 확인하지 못하는 안전 조건을 프로그래머가 대신 책임지겠다고 표시하는 키워드다.\
> 예: `unsafe { buf.get_unchecked(5) }` 는 「5 가 범위 안이라는 것은 내가 보장한다」는 뜻이다.

| 비유 | 실체 |
|---|---|
| 콘센트 | 안전한 public API (`push` · `get` · `as_slice`) |
| 배전반 뚜껑 | `unsafe` 블록 · `unsafe fn` |
| 작업 일지 | `// SAFETY:` 주석 · `/// # Safety` 문서 |
| 점검원 | Miri (`cargo +nightly miri test`) |
| 리콜 목록 확인 | `cargo audit` · `cargo deny check` |
| 배전반 위치를 한 곳에 모음 | `mod raw_utils` 처럼 unsafe 를 한 모듈에 격리 |

```text
   사용자 코드 (안전)
        │  push / get / as_slice
        ▼
 ┌─────────────────────────┐
 │  안전한 API 껍데기        │  ← 여기서 경계 검사 · Result · Option
 │   ┌──────────────────┐  │
 │   │ unsafe 알맹이     │  │  ← SAFETY 주석 + debug_assert!
 │   └──────────────────┘  │
 └─────────────────────────┘
        ▲
   Miri 로 실행하며 UB 탐지 · cargo audit 로 의존성 검사
```

## 이 주제가 답하려는 질문

1. `unsafe` 를 써야 할 때, 그 위험이 바깥 코드로 새지 않게 하려면 어떻게 감싸야 하나?
2. `unsafe` 가 지켜야 하는 조건(불변량)을 어디에, 어떻게 남겨야 감사할 수 있나?
3. 사람이 놓친 정의되지 않은 동작과 의존성의 알려진 취약점은 어떤 도구로 찾나?
4. 애초에 `unsafe` 없이 같은 일을 하는 안전한 대안은 무엇인가?

## 동작 방식

### (1) 안전한 추상화 — 내부는 배열, 바깥은 검사된 API

**언언 쓰나** — 고정 크기 저장소처럼 내부 표현을 직접 다루지만, 쓰는 쪽에는 잘못 쓸 길을 주고 싶지 않을 때.

```text
입력 코드                        무엇이 일어나나                       결과
---------------------------------------------------------------------------------
FixedBuffer::new()          data = [0u8; 256], len = 0             빈 버퍼
buf.push(7)                 len < 256 ? data[len]=7, len+=1        Ok(())
(256개 찬 뒤) buf.push(1)   len >= 256 → 바로 반환                 Err("버퍼가 가득 찼습니다")
buf.get(i)                  i < len ? Some(data[i]) : None         Option<u8>
buf.as_slice()              &data[..len]                           쓴 부분만 보이는 슬라이스
```

- `len` 필드가 「어디까지 유효한 데이터인가」를 추적한다.
- `push` 는 가득 찼을 때 패닉 대신 `Err` 를 돌려준다.
- `get` 은 범위 밖 인덱스에 `None` 을 돌려준다.
- `as_slice` 는 아직 쓰지 않은 뒤쪽 바이트(`len` 이후)를 바깥에 보여 주지 않는다.
- 이 네 함수는 어떻게 불러도 메모리를 망가뜨리지 않는다 — 이것이 「안전한 API 로 감싸서 노출한다」의 뜻이다.

> **안전한 추상화** — 내부에서 위험한 연산을 하더라도, 공개된 API 를 어떤 순서 · 어떤 값으로 불러도 정의되지 않은 동작이 생기지 않게 만든 타입이다.\
> 예: `FixedBuffer::get` 은 범위를 검사하고 `Option` 을 돌려주므로 아무 인덱스나 넣어도 안전하다.

### (2) `unsafe fn` 과 `unsafe` 블록 — 책임을 누구에게 넘기나

**언제 쓰나** — 경계 검사처럼 「호출자가 이미 확인한 일」을 한 번 더 하지 않으려는 성능 최적화가 정말 필요할 때.

```text
입력 코드                                  무엇이 일어나나                              결과
--------------------------------------------------------------------------------------------------
pub unsafe fn get_unchecked(&self, i)      「i < len 은 호출자가 지킨다」를 타입에 표시     호출하려면 unsafe 블록이 필요
unsafe {                                    호출자가 조건을 떠안는다고 선언
  // SAFETY: 0..10 을 push 했으므로 5 는 유효  왜 조건이 성립하는지 기록
  buf.get_unchecked(5)                      경계 검사 없이 data 에서 바로 읽음          u8 값
}
```

- `unsafe fn` 은 「이 함수에는 호출자가 지켜야 할 조건이 있다」는 표시다.
- 그래서 `get_unchecked` 를 부르는 쪽은 반드시 `unsafe { … }` 안에서 불러야 한다.
- 호출자는 그 블록 바로 위에 `// SAFETY:` 로 조건이 왜 지켜지는지 적는다.
- 안쪽에서는 표준 라이브러리의 `<[T]>::get_unchecked` 가 경계 검사 없이 값을 읽는다.

> **불변량** — 코드가 올바르게 동작하려면 언제나 참이어야 하는 조건이다.\
> 예: 「`get_unchecked` 에 넘기는 `index` 는 `self.len` 보다 작다」.

> **UB (정의되지 않은 동작)** — 언어가 결과를 전혀 약속하지 않는 동작이다. 프로그램이 멀쩡해 보여도, 컴파일러가 「일어나지 않는다」고 가정하고 최적화하므로 무슨 일이든 생길 수 있다.\
> 예: 범위 밖 인덱스로 `get_unchecked` 를 부르는 것.

### (3) 불변량을 글과 검사로 남기기 — `# Safety` · `// SAFETY:` · `debug_assert!`

**언제 쓰나** — `unsafe` 가 들어간 모든 자리. 감사하는 사람이 「이 조건이 지켜지나」를 하나씩 확인할 수 있게 한다.

```text
자리                         쓰는 것                               무엇을 적나
------------------------------------------------------------------------------------------
unsafe fn 의 문서 주석       /// # Safety                          호출자가 지켜야 할 조건 목록
unsafe 블록 바로 위          // SAFETY: …                          그 조건이 여기서 왜 성립하는가
unsafe fn 몸통의 첫 줄       debug_assert!(조건, "메시지", …)      디버그 빌드에서 조건을 실제로 검사
```

- `# Safety` 는 계약서다 — 「이 함수를 부르려면 이것을 지켜라」.
- `// SAFETY:` 는 계약 이행 기록이다 — 「여기서는 이래서 지켜졌다」.
- `debug_assert!` 는 디버그 빌드에서 조건을 확인하고 어기면 패닉을 낸다.
- 릴리스 빌드에서는 `debug_assert!` 가 사라지므로 마지막 안전망은 결국 글로 남긴 계약과 호출자의 확인이다.

> **debug_assert!** — 디버그 빌드에서만 조건을 검사하는 단언 매크로다. 릴리스 빌드에서는 검사 코드가 빠진다.\
> 예: `debug_assert!(index < self.len, "인덱스 범위 초과: {} >= {}", index, self.len);`

### (4) unsafe 를 한 곳에 모으고, 안전한 쌍둥이를 함께 둔다

**언제 쓰나** — 위험한 저수준 함수가 여러 개일 때. 감사할 범위를 한 모듈로 줄인다.

```text
mod raw_utils (격리 구역)
 ├─ unsafe fn bytes_to_str_unchecked(&[u8]) -> &str
 │     └ std::str::from_utf8_unchecked   ← UTF-8 검증 생략. 잘못된 UTF-8 이면 UB
 └─ unsafe fn copy_nonoverlapping(src, dst, count)
       ├ debug_assert!(count <= src.len())
       ├ debug_assert!(count <= dst.len())
       └ std::ptr::copy_nonoverlapping(...)  ← 겹치면 UB

바깥 (안전)
 └─ fn safe_bytes_to_str(&[u8]) -> Result<&str, Utf8Error>
       └ std::str::from_utf8               ← 검증하고, 잘못되면 Err
```

- `raw_utils` 모듈 하나만 보면 이 파일의 위험한 변환 · 복사를 전부 감사할 수 있다.
- 각 함수의 `# Safety` 문서가 「무엇을 어기면 UB 인가」를 적는다.
- `safe_bytes_to_str` 은 같은 일을 검증과 함께 하는 안전한 버전이다 — 기본은 이쪽을 쓴다.
- 예제에서 `b"Hello, Rust!"` 를 넘기면 모두 ASCII 라 올바른 UTF-8 이므로 `Ok` 갈래로 간다.

### (5) 감사 기록 — 사람이 하는 검토를 데이터로 남기기

**언제 쓰나** — 코드 리뷰에서 `unsafe` 자리를 하나씩 확인하고 그 결과를 추적할 때.

```text
UnsafeAudit { file, line, reason, safety_invariant, verified }
        │ Display
        ▼
"{file}:{line} [검증됨|미검증]"
"  이유: {reason}"
"  불변량: {safety_invariant}"
```

- 다섯 칸은 「어디(파일 · 줄) · 왜 unsafe 인가 · 무엇을 지켜야 하나 · 검토가 끝났나」다.
- `fmt::Display` 구현이 `verified` 를 `if` 로 골라 「검증됨」 또는 「미검증」을 적는다.
- 문자열 안의 `\n` 과 앞의 공백 두 칸 때문에 한 기록이 세 줄로 찍힌다.
- 예제의 `main` 은 기록마다 `println!()` 을 한 번 더 불러 기록 사이에 빈 줄을 둔다.

### (6) `Send` · `Sync` — 직접 `unsafe impl` 하지 않는 것이 기본

**언제 쓰나** — 다른 타입을 감싸는 래퍼를 만들 때.

```text
struct SafeWrapper<T> { inner: T }

T 가 Send  ──자동──▶ SafeWrapper<T> 도 Send
T 가 Sync  ──자동──▶ SafeWrapper<T> 도 Sync

unsafe impl<T> Send for SafeWrapper<T> {}         ✗  T 가 무엇이든 Send 라고 거짓 약속
unsafe impl<T: Send> Send for SafeWrapper<T> {}   △  조건을 붙인 명시 꼴 (자동 도출과 같은 뜻)
```

- `Send` · `Sync` 는 필드가 모두 그렇다면 컴파일러가 알아서 붙여 준다.
- 바운드 없이 `unsafe impl<T> Send` 를 쓰면 스레드 사이로 보내면 안 되는 `T` 를 감싸도 「보내도 된다」고 약속하게 된다.
- 그래서 원본의 규칙은 「unsafe impl Send/Sync 은 매우 신중하게」다.

> **Send / Sync** — `Send` 는 값을 다른 스레드로 옮겨도 된다는 표시, `Sync` 는 공유 참조를 여러 스레드가 동시에 가져도 된다는 표시다.\
> 예: `SafeWrapper<i32>` 는 `i32` 가 둘 다이므로 둘 다 자동으로 붙는다.

### (7) 도구 — Miri 와 cargo audit / cargo deny

**언제 쓰나** — 테스트 단계에서 UB 를 찾을 때(Miri), 의존성을 점검할 때(audit · deny).

```text
명령                                       보는 것
-----------------------------------------------------------------------------------
rustup +nightly component add miri         Miri 설치 (nightly 도구)
cargo +nightly miri test                   테스트를 Miri 위에서 돌려 UB 탐지
                                            - 해제된 메모리 접근 (use-after-free)
                                            - 범위 밖 접근 (out-of-bounds)
                                            - 유효하지 않은 정렬
                                            - 데이터 레이스
                                            - 미초기화 메모리 읽기
cargo install cargo-audit / cargo audit    의존성의 알려진 취약점
cargo install cargo-deny / cargo deny check 라이선스 + 보안 검사
```

- Miri 는 내 코드(와 테스트)가 실제로 UB 를 일으키는지 본다.
- `cargo audit` 은 내가 가져다 쓰는 크레이트에 알려진 취약점이 있는지 본다.
- `cargo deny check` 는 거기에 라이선스 검사까지 더한다.
- 셋은 보는 대상이 다르므로 서로를 대신하지 않는다.

> **Miri** — Rust 프로그램을 해석하며 실행해 정의되지 않은 동작을 감지하는 nightly 도구다.\
> 예: `cargo +nightly miri test`.

> **cargo audit** — 프로젝트 의존성에 알려진 보안 취약점이 있는지 검사하는 Cargo 하위 명령이다.\
> 예: `cargo install cargo-audit` 뒤 `cargo audit`.

## 문법 — 형태와 규칙

```rust
pub struct Bytes { data: [u8; 4], len: usize }

impl Bytes {
    /// # Safety
    /// - `i` 는 `self.len` 보다 작아야 한다.
    pub unsafe fn at_unchecked(&self, i: usize) -> u8 {
        debug_assert!(i < self.len);
        *self.data.get_unchecked(i)
    }
}

fn first(b: &Bytes) -> Option<u8> {
    if b.len == 0 { return None; }
    // SAFETY: 바로 위에서 len > 0 을 확인했으므로 0 < len 이다.
    Some(unsafe { b.at_unchecked(0) })
}
```

- `unsafe fn` 을 부르는 자리는 `unsafe { … }` 블록 안이어야 한다.
- `unsafe fn` 에는 `/// # Safety` 문서로 호출 조건을 적는다.
- `unsafe` 블록 바로 위에는 `// SAFETY:` 로 조건이 성립하는 이유를 적는다.
- `unsafe` 블록은 위험한 호출 한두 줄만 감쌀 만큼 좁게 잡는다.
- 공개 API 는 안전한 함수(`Result` · `Option` 으로 실패를 알림)로 내놓고, 위험한 함수는 모듈 안에 모은다.
- `unsafe impl Send/Sync` 는 꼭 필요할 때만, 필요하면 `T: Send` 같은 바운드를 붙인다.

## 어디서 틀리나

### 1. unsafe 를 넓게 쓴다
원본의 첫 팁은 「unsafe 코드는 최소한으로」다.
함수 전체를 `unsafe` 블록으로 감싸면 감사할 줄이 늘고, 어느 줄이 위험한지 흐려진다.
위험한 호출만 감싸고 나머지는 안전한 코드로 둔다.

### 2. unsafe 를 그대로 바깥에 내놓는다
원본 팁: 「안전한 API 로 감싸서 노출한다」.
`get_unchecked` 만 있고 `get` 이 없다면 쓰는 사람 모두가 조건을 떠안는다.
`FixedBuffer` 처럼 검사하는 `get` · `as_slice` 를 기본으로 주고, `unsafe fn` 은 성능이 정말 필요한 사람만 고르게 한다.

### 3. SAFETY 주석을 빼먹는다
원본 팁: 「모든 unsafe 블록에 `// SAFETY:` 주석을 달아 불변량을 명시한다」.
주석이 없으면 감사하는 사람이 조건을 거꾸로 추리해야 한다.
원본 예제에서는 `get_unchecked` 정의 위에도 `// SAFETY: caller는 …` 를 달았다.
**원본의 주장 → 왜 의심스러운가**: 정의 쪽 조건은 「호출자가 지킬 계약」이라 `raw_utils` 처럼 `/// # Safety` 문서 절로 적는 편이 문서에 드러나고 일관된다. `// SAFETY:` 는 보통 「이 블록에서 왜 지켜졌나」를 적는 자리로 쓴다 (원본에 근거 없음 — 추론).

### 4. debug_assert! 를 안전망으로 믿는다
원본 규칙 3 은 「debug_assert! 로 불변량 검증」이다.
그러나 `debug_assert!` 는 릴리스 빌드에서 빠진다.
릴리스에서 잘못된 인덱스가 들어오면 검사 없이 UB 로 간다.
`debug_assert!` 는 개발 중에 실수를 일찍 잡는 도구일 뿐, 계약을 대신하지 않는다.

### 5. 계약이 실제로 막는 것을 헷갈린다
`get_unchecked` 의 조건은 `index < self.len` 이다.
메모리 안전만 보면 배열 길이는 256 이고 전부 0 으로 초기화돼 있어 `len` 이상 256 미만을 읽어도 메모리가 깨지지는 않는다.
그 구간을 읽는 것은 「아직 넣지 않은 값」을 읽는 논리 오류이고, 256 이상을 읽는 것이 UB 다.
계약을 더 엄격하게 잡는 것은 괜찮지만, 감사할 때는 「어긴 결과가 UB 인가, 논리 오류인가」를 구분해 적는 것이 좋다 (원본에 근거 없음 — 추론).

### 6. 타입이 이미 보장하는 조건을 계약에 다시 적는다
원본 `copy_nonoverlapping` 의 `# Safety` 는 「src 와 dst 는 겹치지 않아야」 · 「두 포인터 모두 유효해야」를 요구한다.
**원본의 주장 → 왜 의심스러운가**: 인자가 `&[u8]` 과 `&mut [u8]` 이므로 빌림 규칙이 이미 「둘은 유효하고 겹치지 않는다」를 보장한다. 호출자가 실제로 지켜야 할 것은 `count` 가 두 길이를 넘지 않는다는 조건 하나다. 그렇다면 길이를 검사하는 안전한 함수로 만들 수도 있다 (원본에 근거 없음 — 추론).

### 7. 바운드 없는 unsafe impl Send/Sync
`unsafe impl<T> Send for SafeWrapper<T> {}` 는 원본이 「이렇게 하면 안 됨」으로 표시한 꼴이다.
스레드 안전하지 않은 `T` 를 감싸도 래퍼가 `Send` 가 되어 버린다.
기본은 자동 도출에 맡기고, 꼭 쓰려면 `T: Send` 바운드를 붙인다.

### 8. 도구 하나로 다 된다고 여긴다
원본 팁은 「Miri 로 UB 를 감지하고, cargo audit 로 의존성 취약점을 검사한다」로 둘을 나눈다.
Miri 는 의존성의 알려진 취약점 목록을 보지 않고, `cargo audit` 은 내 코드의 UB 를 실행해 보지 않는다.

### 9. 안전한 대안을 먼저 찾지 않는다
원본 팁: 「대부분의 경우 unsafe 없이도 해결할 수 있는 안전한 대안이 있다」.

| unsafe 가 필요해 보이는 경우 | 안전한 대안 (원본 표) |
|---|---|
| 경계 검사 제거 | `get()` + `unwrap` |
| FFI | `bindgen` + 안전 래퍼 |
| 전역 상태 | `OnceCell`, `LazyLock` |
| 내부 가변성 | `Cell`, `RefCell`, `Mutex` |
| 원시 포인터 | 참조, `Box`, `Rc`, `Arc` |
| `transmute` | `From`/`Into`, `as` 캐스트 |

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `unsafe fn` 은 `unsafe` 블록 안에서만 부를 수 있다 | 언어 |
| 필드가 모두 `Send`/`Sync` 이면 구조체도 자동으로 `Send`/`Sync` | 언어 (auto trait 규칙) |
| `&[u8]` 과 `&mut [u8]` 은 겹치지 않는다 | 언어 (빌림 규칙) |
| `from_utf8_unchecked` 에 잘못된 UTF-8 을 주면 UB | 표준 라이브러리 함수의 계약 |
| `ptr::copy_nonoverlapping` 에 겹치는 영역을 주면 UB | 표준 라이브러리 함수의 계약 |
| `debug_assert!` 는 디버그 빌드에서만 검사한다 | 표준 매크로 정의 + 빌드 설정 (릴리스 프로필 기본값에 기댄다) |
| Miri 가 use-after-free · 범위 밖 · 정렬 · 데이터 레이스 · 미초기화 읽기를 감지한다 | Miri 도구의 구현 — 언어 보장 아님, nightly 에서만 쓴다 |
| `cargo audit` 이 알려진 취약점을 알려 준다 | 외부 도구 `cargo-audit` (알려진 목록에 있는 것만) |
| `cargo deny check` 가 라이선스 + 보안을 검사한다 | 외부 도구 `cargo-deny` |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 인덱스로 값을 꺼낸다 | `get()` → `Option` | 측정 없이 `get_unchecked` |
| 바이트를 문자열로 바꾼다 | `std::str::from_utf8` | 검증 안 된 입력에 `from_utf8_unchecked` |
| 슬라이스를 복사한다 | 길이를 검사하는 안전한 복사 | 이유 없는 `ptr::copy_nonoverlapping` |
| 래퍼를 스레드 사이로 보낸다 | 자동 도출되는 `Send`/`Sync` | 바운드 없는 `unsafe impl` |
| 위험한 함수가 여러 개다 | 한 모듈로 격리 + `# Safety` 문서 | 파일 곳곳에 흩어진 `unsafe` |
| unsafe 코드를 검증한다 | `debug_assert!` + Miri 테스트 | 릴리스에서도 검사된다는 믿음 |
| 의존성을 점검한다 | `cargo audit` · `cargo deny check` | Miri 로 대신하기 |

## 핵심 문장

1. **unsafe 는 작게, 안전한 API 안에 넣어서 내놓는다** — 바깥에서는 어떻게 불러도 UB 가 생기지 않아야 한다.
2. **조건은 두 군데에 남긴다** — `unsafe fn` 의 `# Safety` 는 계약, `unsafe` 블록 위의 `// SAFETY:` 는 이행 기록이다.
3. **`debug_assert!` 는 개발 중의 그물이다** — 릴리스에서는 사라지므로 계약을 대신하지 못한다.
4. **도구는 나눠 쓴다** — Miri 는 내 코드의 UB, `cargo audit`/`cargo deny` 는 의존성의 취약점 · 라이선스다.
5. **먼저 안전한 대안을 찾는다** — `get`, `from_utf8`, `Cell`/`RefCell`/`Mutex`, `OnceCell`/`LazyLock`, `Box`/`Rc`/`Arc`, `From`/`Into`.

## 관련 자료

- [input-sanitization](../14-input-sanitization/2-summary.md)
- [encryption](../11-encryption/2-summary.md)
- `hashing` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/rust/testing-security.json` 의 `unsafe-audit`

## 용어 풀이

- **unsafe** — 컴파일러가 확인 못 하는 안전 조건을 프로그래머가 책임진다고 표시하는 키워드.
- **unsafe fn** — 호출자가 지켜야 할 조건이 있는 함수. `unsafe` 블록에서만 부를 수 있다.
- **unsafe 블록** — `unsafe { … }`. 그 안에서 unsafe 연산을 하겠다는 선언.
- **UB (정의되지 않은 동작)** — 언어가 결과를 약속하지 않는 동작.
- **불변량** — 늘 참이어야 하는 조건.
- **안전한 추상화** — 위험한 내부를 감추고 어떻게 불러도 UB 가 없는 API 를 주는 타입.
- **`# Safety`** — `unsafe fn` 문서 주석 안에서 호출 조건을 적는 절.
- **`// SAFETY:`** — `unsafe` 블록 위에 조건이 왜 지켜졌는지 적는 주석.
- **debug_assert!** — 디버그 빌드에서만 검사하는 단언.
- **Miri** — 실행하며 UB 를 감지하는 nightly 도구.
- **cargo audit** — 의존성의 알려진 취약점 검사 도구.
- **cargo deny** — 의존성의 라이선스 + 보안 검사 도구.
- **Send / Sync** — 스레드 사이로 옮겨도 되는가 / 여러 스레드가 공유 참조를 가져도 되는가를 나타내는 트레이트.
- **FFI** — 다른 언어(C 등)의 함수를 부르는 경계.
- **transmute** — 값의 비트를 다른 타입으로 그대로 재해석하는 unsafe 함수.
- **use-after-free** — 해제한 메모리에 접근하는 오류.
- **데이터 레이스** — 여러 스레드가 동기화 없이 같은 메모리에 접근하고 그중 하나가 쓰기인 상황.

## 더 들어가면

- Rust 2024 에디션에서는 `unsafe fn` 몸통 안에서도 unsafe 연산을 `unsafe { }` 블록으로 감싸라는 경고(`unsafe_op_in_unsafe_fn`)가 기본으로 켜진다고 알려져 있다. 이전 에디션에서는 몸통 전체가 암묵적으로 unsafe 였다 (확인 필요).
- Miri 는 실제로 실행된 경로만 검사한다. 테스트가 지나가지 않은 분기의 UB 는 잡지 못한다 (확인 필요).
- `cargo audit` 이 참고하는 취약점 목록은 RustSec 권고 데이터베이스로 알려져 있다 (확인 필요).
- `LazyLock` 은 비교적 최근 안정화된 표준 타입이라 오래된 툴체인에는 없을 수 있다 (확인 필요).
- 예제에서 `raw_utils` 함수와 `SafeWrapper` 는 쓰이지 않으므로 컴파일할 때 `dead_code` 경고가 날 수 있다 (확인 필요).
- 원본 `copy_nonoverlapping` 은 `dst[..count].copy_from_slice(&src[..count])` 같은 안전한 코드로 바꿀 수 있어 보인다. 이 경우 길이가 맞지 않으면 패닉이 난다 (확인 필요).
- 표준 라이브러리 문서에서 많은 `_unchecked` 함수가 짝이 되는 검사 버전과 나란히 있는 것도 같은 설계 철학으로 볼 수 있다 (확인 필요).
