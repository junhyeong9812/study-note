# rust/rust-systems/03 — FFI: C 함수 호출 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. `5` 와 `true` — 내부 `\0` 이 든 입력은 래퍼를 패닉시킨다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
5
true
```

`safe_strlen("hello\0world")` 는 `CString::new` 가 `Err(NulError)` 를 돌려주고 `.expect("CString 생성 실패 (내부 null 바이트)")` 가 그 메시지로 패닉한다.

**왜 그런가**
`CString::new("hello")` 는 `h e l l o \0` 을 만들고, `strlen` 은 `\0` 앞까지 세어 5 를 돌려준다.
`"hello\0world"` 는 안에 `\0` 이 있어 `CString::new` 가 에러를 돌려주므로 `is_err()` 는 참이다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 2」.

### 2. `[72, 101, 108, 108, 111]` 와 `16` — `as_bytes` 는 끝 `\0` 을 뺀다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
[72, 101, 108, 108, 111]
16
```

**왜 그런가**
앞 5 바이트는 `H e l l o` 의 바이트 값이다(원본 주석과 같다).
「Hello from Rust!」는 `Hello`(5) + 공백(1) + `from`(4) + 공백(1) + `Rust`(4) + `!`(1) = 16 글자이고, 모두 1 바이트짜리 문자다.
`as_bytes()` 는 끝에 붙은 `\0` 을 빼고 돌려주므로 17 이 아니라 16 이다.
근거: 2-summary 「동작 방식 (3)」.

### 3. `to_str` 은 에러, `to_string_lossy` 는 U+FFFD 로 바꿔 성공

`to_str()` 은 UTF-8 검증에 실패해 에러를 돌려준다 — `.unwrap()` 했다면 패닉한다.
`to_string_lossy()` 는 실패하지 않고, 잘못된 바이트를 대체 문자 U+FFFD 로 바꾼 `Cow<str>` 를 돌려준다.
대신 원래 바이트 값은 결과에서 사라진다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 5」.

### 4. 컴파일러가 바깥 함수의 본문과 선언의 맞음을 확인할 수 없기 때문이다

`extern "C"` 블록은 모양만 적고 본문은 링커가 libc 에서 붙인다.
컴파일러는 그 본문을 볼 수 없으므로 선언한 시그니처가 실제 C 정의와 맞는지, 함수가 메모리를 망가뜨리지 않는지 검증하지 못한다.
함수가 하는 일이 단순한지와 상관없이, 검증할 수 없다는 사실 때문에 호출을 `unsafe` 로 표시하게 한다.
원본 주석도 「extern "C" 함수는 호출 시점에 검증 불가능」이라고 적는다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 8」.

### 5. C 는 첫 `\0` 을 문자열의 끝으로 읽기 때문이다

Rust 의 `String` 은 길이를 따로 저장하므로 `\0` 도 평범한 한 글자다.
C 문자열은 길이 대신 `\0` 으로 끝을 표시하므로, 안에 `\0` 이 있으면 C 쪽은 거기서 문자열이 끝났다고 보고 뒷부분(`world`)을 버린다.
그런 조용한 잘림을 막으려고 `CString::new` 가 `NulError` 로 거부한다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 2」.

### 6. `rust_add` 는 본문을 Rust 로 쓴 함수라서 — 팁은 「선언만 한 바깥 함수」에 맞다

`pub extern "C" fn rust_add` 는 호출 규약만 C 로 맞췄을 뿐 본문은 Rust 이고 컴파일러가 검사했다.
그래서 Rust 안에서는 평범한 함수처럼 `unsafe` 없이 부른다.
「항상 unsafe」는 `extern "C" { … }` 블록에 선언만 한, 본문을 볼 수 없는 바깥 함수를 부를 때의 이야기다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 1」.

### 7. C 의 `abs(INT_MIN)` 은 정의되지 않은 동작이라 safe 함수가 약속을 깬다

`i32::MIN` 의 절댓값은 `i32` 로 표현할 수 없다.
C 표준에서 이때의 `abs` 는 정의되지 않은 동작이다 (원본에 근거 없음 — 추론).
`safe_abs` 는 safe 함수로 공개되어 있어 누구나 `unsafe` 없이 `i32::MIN` 을 넘길 수 있으므로, 래퍼가 「어떤 입력에도 안전하다」는 책임을 다하지 못한다.
래퍼가 그 입력을 미리 걸러야 한다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 6」.

### 8. 임시 `CString` 이 문장 끝에서 해제되어 포인터가 댕글링이 된다

`CString::new(s).unwrap()` 의 결과는 변수에 묶이지 않은 임시 값이라 그 문장이 끝나면 해제된다.
`as_ptr()` 가 준 포인터는 `CString` 이 살아 있는 동안만 유효하므로, 다음 줄에서는 해제된 메모리를 가리킨다.
그 포인터를 C 에 넘기면 해제된 메모리를 읽게 된다.
원본처럼 `let c_string = …;` 로 묶어 두고 그 변수가 살아 있는 동안 써야 한다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 3」.

### 9. `CString` : `CStr` = `String` : `&str` — 소유와 빌림의 짝이다

`String` 이 힙의 문자열을 소유하고 `&str` 가 문자열을 빌려 보듯이, `CString` 은 `\0` 종료 문자열을 힙에 소유하고 `CStr` 은 `\0` 종료 문자열을 빌린다.
그래서 Rust 가 만들어 C 로 보낼 때는 메모리를 책임질 소유 버전(`CString`)을, C 가 가진 것을 읽을 때는 메모리를 소유하지 않는 빌림 버전(`CStr`)을 쓴다.
차이는 `\0` 종료를 보장하는지와, `&str` 와 달리 UTF-8 을 보장하지 않는다는 것이다 — 그래서 `&str` 로 넘어갈 때 `to_str()` 의 검증이 필요하다.
근거: 2-summary 「한눈에」 · 「동작 방식 (3)」 · 「동작 방식 (4)」 · 「문법」 표.

## 실습 정답

### 실습 1. libc 함수 부르기와 C 문자열 왕복

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 타입 가져오기 | `use std::ffi::{CStr, CString};` · `use std::os::raw::{c_char, c_int, c_double};` |
| 2. C 함수 선언 | `extern "C" { fn abs…; fn sqrt…; fn strlen…; }` |
| 3. `rust_add` 내보내기 | `#[no_mangle] pub extern "C" fn rust_add` |
| 4. `safe_abs` · `safe_sqrt` | `unsafe { abs(n) }` · `unsafe { sqrt(n) }` |
| 5. `safe_strlen` | `CString::new(s).expect(…)` · `unsafe { strlen(c_string.as_ptr()) }` |
| 6. C 함수 호출 구역 | `safe_abs(-42)` · `safe_sqrt(144.0)` · `safe_strlen("hello")` |
| 7. CString 구역 | `CString::new(rust_string).unwrap()` · `c_string.as_ptr()` · `&c_string.as_bytes()[..5]` |
| 8. 내부 `\0` 시도 | `let result = CString::new("hello\0world");` |
| 9. CStr 구역 | `CStr::from_ptr(c_ptr)` · `c_str.to_str().unwrap()` · `c_str.to_string_lossy()` |
| 10. Rust extern fn 구역 | `rust_add(3, 4)` |
| 11. 바이트에서 CStr | `CStr::from_bytes_with_nul(bytes).unwrap()` · `c_str.to_str().unwrap()` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`rust/rust-systems/reference/ffi-c-calling.rs`

```rust
// [시스템 프로그래밍] FFI: C 함수 호출
// 설명: extern "C"로 C 함수 호출, libc, CStr/CString 문자열 변환
// 팁: CString: Rust 소유 + null 종료 (Rust→C). CStr: 빌린 참조 + null 종료 (C→Rust). CString::new()는 내부에 null 바이트가 있으면 에러를 반환한다. to_str()은 UTF-8 검증, to_string_lossy()는 잘못된 바이트를 대체한다. extern "C" 함수 호출은 항상 unsafe이다. #[no_mangle]로 이름 맹글링을 방지하여 C에서 호출 가능하게 한다.

// CStr: null로 끝나는 C 문자열 슬라이스 (빌림)
// CString: 소유 버전 (힙 할당, null 보장)
use std::ffi::{CStr, CString};
// c_char/c_int/c_double: 플랫폼별 C ABI에 맞는 정확한 타입 별칭
use std::os::raw::{c_char, c_int, c_double};

// C 함수 선언 (링커가 libc에서 찾음)
// extern "C": C 호출 규약(System V AMD64 ABI 등) 사용
extern "C" {
    // 표준 C 라이브러리 함수들 - 링킹 시 libc에서 해결
    fn abs(input: c_int) -> c_int;
    fn sqrt(input: c_double) -> c_double;
    // strlen: null 종료 문자열의 길이 (null 제외)
    fn strlen(s: *const c_char) -> usize;
}

// Rust 함수를 C 호출 규약으로 내보내기
// #[no_mangle]: 심볼 이름 맹글링 비활성화 → C에서 "rust_add"로 직접 호출 가능
// pub extern "C": ABI를 C로 강제, 외부 노출
#[no_mangle]
pub extern "C" fn rust_add(a: c_int, b: c_int) -> c_int {
    a + b
}

// 안전한 래퍼
// FFI 호출의 unsafe를 흡수하여 호출자에게 safe API 제공
fn safe_abs(n: i32) -> i32 {
    // unsafe 이유: extern "C" 함수는 호출 시점에 검증 불가능
    unsafe { abs(n) }
}

fn safe_sqrt(n: f64) -> f64 {
    unsafe { sqrt(n) }
}

// C strlen을 안전하게 감싸는 래퍼
fn safe_strlen(s: &str) -> usize {
    // CString::new: Rust &str → C 문자열로 변환 (null 종료 추가)
    // 내부 null 바이트가 있으면 NulError 반환
    let c_string = CString::new(s).expect("CString 생성 실패 (내부 null 바이트)");
    // as_ptr: *const c_char (CString이 살아있는 동안만 유효)
    unsafe { strlen(c_string.as_ptr()) }
}

fn main() {
    // === C 함수 호출 ===
    println!("=== C 함수 호출 ===");
    println!("abs(-42) = {}", safe_abs(-42));     // 42
    println!("sqrt(144) = {}", safe_sqrt(144.0));  // 12.0
    println!("strlen(\"hello\") = {}", safe_strlen("hello")); // 5

    // === CString (Rust → C) ===
    println!("\n=== CString (Rust -> C) ===");
    let rust_string = String::from("Hello from Rust!");
    // Rust String → CString (null 종료 추가)
    let c_string = CString::new(rust_string).unwrap();
    println!("CString: {:?}", c_string);           // "Hello from Rust!" + null 종료
    // as_ptr: C 함수에 전달할 포인터
    println!("as_ptr: {:?}", c_string.as_ptr());   // *const c_char
    // as_bytes: null 제외 바이트 슬라이스
    println!("as_bytes: {:?}", &c_string.as_bytes()[..5]); // [72, 101, 108, 108, 111]

    // null 바이트가 포함되면 에러 (C에서는 문자열 종료로 해석되므로)
    let result = CString::new("hello\0world");
    println!("null 포함: {:?}", result); // Err(NulError)

    // === CStr (C → Rust) ===
    println!("\n=== CStr (C -> Rust) ===");
    let c_string = CString::new("Hello from C!").unwrap();
    // C 함수가 반환하는 *const c_char를 받았다고 가정
    let c_ptr: *const c_char = c_string.as_ptr();

    // 실제로는 C에서 받은 포인터를 이렇게 변환
    unsafe {
        // CStr::from_ptr: 안전 조건 - ptr은 유효한 null 종료 문자열을 가리켜야 함
        let c_str: &CStr = CStr::from_ptr(c_ptr);
        // to_str: UTF-8 검증 후 &str 반환 (실패 가능)
        let rust_str: &str = c_str.to_str().unwrap();
        println!("C → Rust: {}", rust_str);

        // to_string_lossy: 잘못된 UTF-8을 U+FFFD로 대체 (Cow 반환)
        let lossy: std::borrow::Cow<str> = c_str.to_string_lossy();
        println!("lossy: {}", lossy);
    }

    // === Rust 함수 내보내기 테스트 ===
    println!("\n=== Rust extern fn ===");
    // Rust 내부에서 호출도 가능 (단, ABI는 C)
    println!("rust_add(3, 4) = {}", rust_add(3, 4)); // 7

    // === 바이트 슬라이스에서 CStr ===
    println!("\n=== 바이트에서 CStr ===");
    // 정적 바이트 리터럴, 마지막 \0 필수
    let bytes = b"hello\0";
    // from_bytes_with_nul: null 종료 검증 후 CStr 생성
    let c_str = CStr::from_bytes_with_nul(bytes).unwrap();
    println!("from bytes: {:?}", c_str.to_str().unwrap()); // "hello"
}
```

**실행 결과** — 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다).

**풀이 요점**
- `extern "C"` 블록은 본문 없이 모양만 적고, 호출은 래퍼 안의 `unsafe` 블록에만 둔다.
- `safe_strlen` 에서 `CString` 을 `c_string` 변수에 묶어 두어야 `strlen` 이 도는 동안 포인터가 유효하다.
- `CStr::from_ptr` 은 `unsafe` 이고, `to_str` 은 검증해서 실패할 수 있으며, `to_string_lossy` 는 대체해서 실패하지 않는다.
- `from_bytes_with_nul` 은 끝 `\0` 을 검증하므로 `b"hello\0"` 처럼 `\0` 을 직접 넣어야 한다.
- `rust_add` 는 C 에 이름 그대로 드러나지만, Rust 안에서는 `unsafe` 없이 부른다.
- `as_ptr` 줄의 주소 값은 실행마다 달라지므로 맞히는 대상이 아니다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
