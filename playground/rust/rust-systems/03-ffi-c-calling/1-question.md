# rust/rust-systems/03 — FFI: C 함수 호출 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 래퍼로 길이를 재고 내부 `\0` 을 넣어 보면 (예측)

```rust
// 질문용 발췌
println!("{}", safe_strlen("hello"));
let result = CString::new("hello\0world");
println!("{}", result.is_err());
```

- 두 `println!` 은 각각 무엇을 찍겠는가?
- `safe_strlen("hello\0world")` 를 부르면 어떻게 되겠는가?

### 2. `CString` 의 바이트를 들여다보면 (예측)

```rust
// 질문용 발췌
let c_string = CString::new(String::from("Hello from Rust!")).unwrap();
println!("{:?}", &c_string.as_bytes()[..5]);
println!("{}", c_string.as_bytes().len());
```

- 두 `println!` 은 각각 무엇을 찍겠는가?

### 3. 잘못된 UTF-8 이 든 C 문자열을 읽을 때 (경계)

- C 가 준 문자열에 올바르지 않은 UTF-8 바이트가 섞여 있으면 `to_str()` 과 `to_string_lossy()` 는 각각 어떻게 되는가?

### 4. 아무 해도 없어 보이는 `abs` 호출에도 `unsafe` 가 필요한 까닭 (왜)

- 절댓값만 구하는 `abs` 를 부르는데 왜 `unsafe` 블록이 있어야 하는가?

### 5. `CString::new` 가 내부 `\0` 을 거부하는 까닭 (왜)

- Rust 의 `String` 에는 `\0` 이 들어가도 문제없는데, 왜 `CString` 으로 바꿀 때는 에러가 되는가?

### 6. `rust_add` 는 `unsafe` 없이 부른다 (경계)

- 원본 팁은 「`extern "C"` 함수 호출은 항상 unsafe」라는데, `main` 이 `rust_add(3, 4)` 를 `unsafe` 없이 부를 수 있는 까닭은 무엇이고 팁은 어디까지 맞는가?

### 7. `safe_abs` 는 모든 `i32` 에 안전한가 (경계)

- `safe_abs` 에 `i32::MIN` 을 넘기면 무엇이 문제가 되는가?

### 8. 한 줄로 쓴 `CString::new(s).unwrap().as_ptr()` (경계)

- 이 한 줄로 얻은 포인터를 다음 줄에서 C 함수에 넘기면 무엇이 잘못되는가?

### 9. `CString`/`CStr` 과 `String`/`&str` 의 짝 (연결)

- `CString` 과 `CStr` 의 관계는 Rust 의 `String` 과 `&str` 의 관계와 어떻게 맞물리는가?

## 실습

### 실습 1. libc 함수 부르기와 C 문자열 왕복

**만들 것** — libc 의 `abs` · `sqrt` · `strlen` 을 선언해 안전한 래퍼로 감싸 부르고, `CString` · `CStr` 로 문자열을 Rust ↔ C 로 바꿔 보며, Rust 함수 하나를 C 규약으로 내보내는 프로그램을 만든다.

**준비물** — Rust 컴파일러(`rustc`) 하나면 된다. 외부 크레이트는 쓰지 않고, C 함수는 시스템의 C 표준 라이브러리에서 링크된다.

**요구 조건**

1단계 — 선언과 내보내기
1. `std::ffi` 에서 `CStr` · `CString` 을, `std::os::raw` 에서 `c_char` · `c_int` · `c_double` 을 가져온다.
2. `extern "C"` 블록에 `abs(c_int) -> c_int` · `sqrt(c_double) -> c_double` · `strlen(*const c_char) -> usize` 를 선언한다.
3. 두 `c_int` 를 더해 돌려주는 `rust_add` 를 이름 맹글링 없이 C 호출 규약으로 공개한다.

2단계 — 안전한 래퍼
4. `safe_abs(i32) -> i32` 와 `safe_sqrt(f64) -> f64` 는 안에서만 `unsafe` 로 C 함수를 부른다.
5. `safe_strlen(&str) -> usize` 는 입력을 `CString` 으로 바꾸되 실패하면 「CString 생성 실패 (내부 null 바이트)」 메시지로 패닉하고, 그 포인터로 `strlen` 을 부른다.

3단계 — `main`
6. 「C 함수 호출」 구역: `abs(-42)` · `sqrt(144)` · `strlen("hello")` 의 결과를 래퍼로 구해 찍는다.
7. 「CString (Rust -> C)」 구역: `String` 「Hello from Rust!」를 `CString` 으로 바꿔 Debug 꼴로 찍고, `as_ptr()` 의 포인터와 `as_bytes()` 의 앞 5 바이트를 찍는다.
8. 같은 구역에서 `"hello\0world"` 로 `CString::new` 를 시도한 `Result` 를 그대로 Debug 꼴로 찍는다.
9. 「CStr (C -> Rust)」 구역: 「Hello from C!」로 만든 `CString` 의 포인터를 C 에서 받은 포인터로 여기고, `unsafe` 블록에서 `CStr` 로 바꾼 뒤 `to_str()` 결과와 `to_string_lossy()` 결과를 각각 찍는다.
10. 「Rust extern fn」 구역: `rust_add(3, 4)` 의 결과를 찍는다.
11. 「바이트에서 CStr」 구역: 바이트 리터럴 `b"hello\0"` 에서 `\0` 종료를 검증해 `CStr` 을 만들고, `to_str()` 결과를 Debug 꼴로 찍는다.

**시작 코드**

```rust
use std::ffi::{CStr, CString};
use std::os::raw::{c_char, c_int, c_double};

// TODO: extern "C" 블록 — abs, sqrt, strlen 선언

// TODO: 맹글링 없이 C 규약으로 공개하는 속성과 함수 머리
fn rust_add(a: c_int, b: c_int) -> c_int {
    a + b
}

fn safe_abs(n: i32) -> i32 {
    // TODO: abs 호출
    todo!()
}

fn safe_sqrt(n: f64) -> f64 {
    // TODO: sqrt 호출
    todo!()
}

fn safe_strlen(s: &str) -> usize {
    // TODO: s 를 CString 으로 (실패 시 "CString 생성 실패 (내부 null 바이트)")
    // TODO: 그 포인터로 strlen 호출
    todo!()
}

fn main() {
    println!("=== C 함수 호출 ===");
    println!("abs(-42) = {}", safe_abs(-42));
    println!("sqrt(144) = {}", safe_sqrt(144.0));
    println!("strlen(\"hello\") = {}", safe_strlen("hello"));

    println!("\n=== CString (Rust -> C) ===");
    let rust_string = String::from("Hello from Rust!");
    let c_string = todo!(); // TODO: rust_string → CString
    println!("CString: {:?}", c_string);
    println!("as_ptr: {:?}", /* TODO: 포인터 */ ());
    println!("as_bytes: {:?}", /* TODO: 앞 5 바이트 */ ());

    let result = todo!(); // TODO: "hello\0world" 로 CString 시도
    println!("null 포함: {:?}", result);

    println!("\n=== CStr (C -> Rust) ===");
    let c_string = CString::new("Hello from C!").unwrap();
    let c_ptr: *const c_char = c_string.as_ptr();

    // TODO: unsafe 블록에서 c_ptr → &CStr
    //       to_str 결과를 "C → Rust: {}" 로 찍기
    //       to_string_lossy 결과를 "lossy: {}" 로 찍기

    println!("\n=== Rust extern fn ===");
    println!("rust_add(3, 4) = {}", rust_add(3, 4));

    println!("\n=== 바이트에서 CStr ===");
    let bytes = b"hello\0";
    // TODO: bytes 에서 \0 종료를 검증해 CStr 만들기
    // TODO: "from bytes: {:?}" 로 to_str 결과 찍기
}
```

**확인 방법** — `rustc ffi-c-calling.rs` 로 컴파일하고 만든 실행 파일을 돌린다. 구역 다섯 개가 차례로 찍히는지, `abs` 줄에 42, `strlen` 줄에 5, `rust_add` 줄에 7, `as_bytes` 줄에 `[72, 101, 108, 108, 111]` 이 나오는지, 내부 `\0` 줄이 `Err(…)` 꼴인지 본다. `as_ptr` 줄의 주소 값은 실행마다 달라도 된다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
