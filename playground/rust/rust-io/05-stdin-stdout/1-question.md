# rust/rust-io/05 — 표준 입출력 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. `parse_input` 에 세 문자열을 넣으면 (예측)

```rust
// 질문용 발췌
fn parse_input(input: &str) -> Result<i32, String> {
    input.trim()
        .parse::<i32>()
        .map_err(|e| format!("파싱 에러: {}", e))
}
println!("{:?}", parse_input("42"));
println!("{:?}", parse_input("abc"));
println!("{:?}", parse_input("  99  "));
```

- 세 줄은 각각 `Ok` 인가 `Err` 인가?
- `Ok` 줄과 `Err` 줄은 어떤 꼴로 찍히나?

### 2. 섞인 입력을 `filter_map` 으로 모으면 (예측)

```rust
// 질문용 발췌
let a: Vec<i32> = "10 20 x 30".split_whitespace()
    .filter_map(|s| s.parse().ok()).collect();
let b: Vec<i32> = "10,20".split_whitespace()
    .filter_map(|s| s.parse().ok()).collect();
println!("{:?} {:?}", a, b);
```

- `a` 와 `b` 에는 각각 무엇이 들어가나?
- `"x"` 에 대해 에러가 보고되나?

### 3. `validate_age` 에 네 입력을 넣으면 (예측)

```rust
// 질문용 발췌
for input in ["abc", "200", "25", "-3"] {
    match validate_age(input) {   // u32 로 파싱 → 150 초과면 Err
        Ok(age) => println!("'{}' -> 유효: {}", input, age),
        Err(e) => println!("'{}' -> 에러: {}", input, e),
    }
}
```

- 네 입력은 각각 어느 갈래로 가고 어떤 문구가 붙나?

### 4. `read_line` 으로 받은 숫자 문자열에 `trim()` 이 꼭 필요한 까닭 (왜)

- `read_line` 으로 `42` 를 받아 `trim()` 없이 `parse::<i32>()` 하면 왜 실패하나?

### 5. `print!` 프롬프트 뒤에만 `flush()` 를 부르는 까닭 (왜)

- 같은 줄 프롬프트를 `print!` 로 쓰면 왜 `flush()` 없이는 화면에 안 보일 수 있나?
- `println!` 은 왜 따로 `flush()` 를 부르지 않아도 되나?

### 6. `stdin().lock()` 이 이득이 되는 곳 (경계)

- 줄마다 `stdin().read_line()` 을 부르는 것과 `stdin().lock().lines()` 는 잠금 횟수가 어떻게 다른가?
- 이 차이가 실제로 문제가 되는 상황과 거의 상관없는 상황은 각각 무엇인가?

### 7. 원본의 여러 줄 입력 루프가 멈추는 지점 (경계)

- 원본의 `for line in stdin.lock().lines()` 루프는 어떤 두 경우에 끝나나?
- 입력 셋째 줄이 빈 줄이고 넷째 줄에 값이 있으면 넷째 줄은 처리되나?

### 8. `BufWriter` 와 `print!` 의 flush 는 같은 문제의 두 얼굴이다 (연결)

- `BufWriter` 에 `writeln!` 한 내용과 `print!` 한 프롬프트는 어떤 점에서 같은 상태에 있나?
- `BufWriter` 를 쓰면 왜 출력이 빨라지나?

### 9. `validate_age` 에서 `?` 앞에 `map_err` 가 오는 까닭 (연결)

- `?` 연산자는 `Err` 를 만나면 무엇을 하나?
- 함수의 에러 타입이 `String` 일 때 `parse()` 의 에러를 왜 `map_err` 로 먼저 바꾸나?

## 실습

### 실습 1. 표준 입출력 패턴 여덟 가지를 시뮬레이션하는 프로그램

**만들 것** — 실제 키보드 입력 대신 문자열을 입력으로 삼아, 한 줄 · 숫자 · 여러 값 · 여러 줄 입력과 프롬프트 · 잠금 · 검증 루프 · 출력 버퍼링 패턴을 차례로 보여 주는 Rust 프로그램을 만든다. 실제 입력 코드는 각 함수 안에 주석으로 남긴다.

**요구 조건**

1단계 — 입력 받기 패턴

1. `read_line_demo` — 양쪽에 공백이 있는 문자열 `"  Hello, World!  "` 을 입력으로 가정하고, 원래 문자열과 `trim()` 한 문자열을 작은따옴표로 감싸 각각 찍는다.
2. `read_number_demo` — 안쪽 함수 `parse_input(&str) -> Result<i32, String>` 을 만든다. `trim` 후 `parse::<i32>()` 하고, 에러는 `map_err` 로 「파싱 에러: 」 를 앞에 붙인 `String` 으로 바꾼다. `"42"` · `"abc"` · `"  99  "` 에 대한 결과를 `{:?}` 로 찍는다.
3. `read_multiple_demo` — `"10 20 30 40 50"` 을 `split_whitespace` + `filter_map(.. .ok())` 로 `Vec<i32>` 에 모아 입력과 함께 찍고, `"Alice,30,Seoul"` 을 `split(',')` 로 `Vec<&str>` 에 모아 입력과 함께 찍는다.
4. `read_multiline_demo` — 세 줄짜리 문자열을 `lines().enumerate()` 로 돌며 「줄 1: …」처럼 1부터 번호를 붙여 찍는다.

2단계 — 출력과 성능 패턴

5. `prompt_demo` — `print!` 뒤에 `flush` 가 필요한 이유를 두 줄로 찍는다.
6. `stdin_lock_demo` — `read_line` 은 매 호출마다 잠그고 `lock().lines()` 는 한 번 잠근다는 차이와, 그 차이가 경쟁 프로그래밍에서 중요하다는 것을 세 줄로 찍는다.
7. `validation_loop_demo` — 안쪽 함수 `validate_age(&str) -> Result<u32, String>` 을 만든다. `trim` 후 `u32` 로 파싱하고 실패면 「숫자를 입력하세요」, 150 초과면 「나이는 150 이하여야 합니다」, 아니면 `Ok(age)` 다. 파싱 실패는 `map_err` + `?` 로 돌려준다. `"abc"` · `"200"` · `"25"` 를 넣어 `match` 로 「유효」 / 「에러」 를 찍는다.
8. `stdout_buffering_demo` — `io::stdout()` 을 `lock()` 해 `BufWriter` 로 감싸고, `writeln!` 으로 0~4 번 줄 다섯 개를 쓴 뒤 `flush()` 한다. 그다음 `BufWriter` 를 쓴 까닭을 한 줄 찍는다.

3단계 — 묶기

9. `main` 이 여덟 함수를 위 차례대로 부르고, 마지막에 입력 · 파싱 · 출력 · 성능을 한 줄씩 정리해 찍는다.
10. 각 데모 함수(첫 함수 제외)의 제목 줄은 앞에 빈 줄이 오도록 `\n` 으로 시작한다.

**시작 코드**

```rust
// io: stdin/stdout, BufRead: lines()/read_line, Write: flush/writeln!
use std::io::{self, BufRead, Write};

fn read_line_demo() {
    println!("=== 한 줄 입력 패턴 ===");
    // 실제 코드(주석): String::new() → read_line → trim
    let simulated = "  Hello, World!  ";
    // TODO: trim 한 값을 만든다
    // TODO: 원래 값과 trim 후 값을 '…' 로 감싸 찍는다
}

fn read_number_demo() {
    println!("\n=== 숫자 입력 패턴 ===");
    fn parse_input(input: &str) -> Result<i32, String> {
        // TODO: trim → parse::<i32>() → map_err 로 "파싱 에러: {}" 문자열
        todo!()
    }
    // TODO: "42", "abc", "  99  " 결과를 {:?} 로 찍는다
}

fn read_multiple_demo() {
    println!("\n=== 여러 값 입력 패턴 ===");
    let input = "10 20 30 40 50";
    // TODO: 공백으로 나눠 파싱에 성공한 것만 Vec<i32> 로 모은다
    let csv_input = "Alice,30,Seoul";
    // TODO: 쉼표로 나눠 Vec<&str> 로 모은다
    // TODO: 두 입력과 결과를 찍는다
}

fn read_multiline_demo() {
    println!("\n=== 여러 줄 입력 패턴 ===");
    // 실제 코드(주석): stdin.lock().lines() 로 EOF 까지, 빈 줄이면 break
    let input = "첫 번째 줄\n두 번째 줄\n세 번째 줄";
    // TODO: 줄마다 1부터 번호를 붙여 찍는다
}

fn prompt_demo() {
    println!("\n=== 프롬프트 패턴 ===");
    // 실제 코드(주석): print! → io::stdout().flush() → read_line
    // TODO: flush 가 필요한 이유 두 줄
}

fn stdin_lock_demo() {
    println!("\n=== stdin lock 패턴 ===");
    // TODO: read_line 과 lock().lines() 의 잠금 차이, 경쟁 프로그래밍 — 세 줄
}

fn validation_loop_demo() {
    println!("\n=== 입력 유효성 검사 패턴 ===");
    fn validate_age(input: &str) -> Result<u32, String> {
        // TODO: trim → parse (실패: "숫자를 입력하세요") → ?
        // TODO: 150 초과: "나이는 150 이하여야 합니다" / 아니면 Ok
        todo!()
    }
    // 실제 코드(주석): loop { print! → flush → read_line → match … break }
    let test_inputs = vec!["abc", "200", "25"];
    // TODO: 각 입력을 match 로 '…' -> 유효: / '…' -> 에러: 로 찍는다
}

fn stdout_buffering_demo() {
    println!("\n=== stdout 버퍼링 ===");
    // TODO: stdout 을 lock 해 BufWriter 로 감싼다
    // TODO: writeln! 으로 다섯 줄 쓰고 flush
    // TODO: BufWriter 를 쓴 까닭 한 줄
}

fn main() {
    // TODO: 여덟 데모를 차례대로 부른다
    println!("\n=== 정리 ===");
    // TODO: 입력 · 파싱 · 출력 · 성능 정리 네 줄
}
```

**확인 방법** — `rustc stdin-stdout.rs && ./stdin-stdout` (또는 `cargo run`) 으로 돌려, 여덟 제목이 차례대로 나오고 `parse('abc')` 가 `Err`, `'200'` 이 에러, `'25'` 가 유효로 나오며, 버퍼링된 줄 다섯 개가 그다음 설명 줄보다 먼저 나오는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
