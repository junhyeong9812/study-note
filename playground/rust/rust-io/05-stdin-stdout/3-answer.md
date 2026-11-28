# rust/rust-io/05 — 표준 입출력 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. `Ok(42)` · `Err("파싱 에러: …")` · `Ok(99)`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
Ok(42)
Err("파싱 에러: invalid digit found in string")
Ok(99)
```

둘째 줄의 「파싱 에러: 」 뒤 문구는 표준 라이브러리 `ParseIntError` 의 문구로 추론한 것이다(확인 필요).

**왜 그런가**
- `"42"` 는 `trim` 해도 그대로이고 `i32` 로 바뀐다.
- `"abc"` 는 숫자가 아니라 `parse` 가 `Err` 를 내고, `map_err` 가 「파싱 에러: 」 를 붙인 `String` 으로 바꾼다.
- `"  99  "` 는 `trim` 이 공백을 걷어 `"99"` 가 되므로 성공한다.
- `{:?}` 는 `Result` 를 `Ok(..)` / `Err(..)` 꼴로, `String` 을 따옴표에 싸서 찍는다.
- 근거: 2-summary 「동작 방식 (2)」.

### 2. `a` 는 `[10, 20, 30]`, `b` 는 빈 벡터 — 에러는 없다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
[10, 20, 30] []
```

**왜 그런가**
- `"x"` 는 `parse` 에 실패해 `.ok()` 가 `None` 을 내고, `filter_map` 이 그것을 버린다 — 보고 없이 사라진다.
- `"10,20"` 에는 공백이 없어 조각이 하나뿐이고, 그 조각은 숫자가 아니라 버려진다.
- 근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 5」.

### 3. `abc`·`-3` 은 숫자 에러, `200` 은 범위 에러, `25` 만 유효

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
'abc' -> 에러: 숫자를 입력하세요
'200' -> 에러: 나이는 150 이하여야 합니다
'25' -> 유효: 25
'-3' -> 에러: 숫자를 입력하세요
```

**왜 그런가**
- `"abc"` 는 `u32` 파싱에 실패해 `map_err` 문구가 `?` 로 바로 돌아온다.
- `"200"` 은 파싱은 되지만 150 을 넘어 범위 검사에서 `Err` 다.
- `"-3"` 은 부호 없는 `u32` 가 음수를 담지 못해 파싱 단계에서 실패한다.
- 근거: 2-summary 「동작 방식 (7)」.

### 4. `read_line` 이 줄 끝 개행까지 버퍼에 넣기 때문이다

버퍼에는 `"42\n"` 이 들어가고, 개행이 섞인 문자열은 정수 형식이 아니라 `parse` 가 실패한다.
`trim()` 이 개행과 앞뒤 공백을 걷어 `"42"` 로 만든다.
근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (2)」.

### 5. stdout 이 줄 버퍼링이라 개행이 와야 내보내기 때문이다

`print!` 는 개행을 붙이지 않으므로 프롬프트가 버퍼에 남은 채 `read_line` 이 입력을 기다릴 수 있다.
`flush()` 가 버퍼를 지금 바로 화면으로 내보낸다.
`println!` 은 끝에 개행을 붙이므로 줄 버퍼링이 그 줄을 내보낸다 — 그래서 「자동 flush」 처럼 보인다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 8」.

### 6. N 번 대 1 번 — 대량 입력에서만 의미가 있다

`stdin().read_line()` 은 부를 때마다 잠그고 풀어 N 줄이면 N 번 잠근다.
`stdin().lock().lines()` 는 한 번 잡은 잠금으로 모든 줄을 읽는다.
경쟁 프로그래밍처럼 수많은 줄을 빨리 읽어야 할 때 차이가 드러나고, 사람이 몇 줄 치는 대화형 프로그램에서는 거의 상관없다.
얼마나 빨라지는지의 수치는 원본에 없다.
근거: 2-summary 「동작 방식 (6)」 · 「언제 쓰고 언제 안 쓰나」.

### 7. EOF 이거나 빈 줄을 만나면 끝난다 — 넷째 줄은 처리되지 않는다

`lines()` 는 EOF 에서 끝나 `for` 가 끝난다.
그 전이라도 `line.is_empty()` 이면 `break` 한다.
셋째 줄이 빈 줄이면 거기서 멈추므로 넷째 줄은 읽지 않는다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 6」.

### 8. 둘 다 「버퍼에 있고 아직 내보내지지 않은」 상태다

`print!` 의 프롬프트는 stdout 의 줄 버퍼에, `writeln!` 의 줄들은 `BufWriter` 의 메모리 버퍼에 머문다.
그래서 둘 다 `flush()` 로 내보낸다.
`BufWriter` 는 쓰기를 메모리에 모아 한꺼번에 내보내므로 실제 출력 시스템 호출 횟수가 줄어 빨라진다.
근거: 2-summary 「동작 방식 (5)」 · 「동작 방식 (8)」.

### 9. `?` 는 받은 `Err` 를 그대로 돌려주므로 타입을 먼저 맞춰야 한다

`?` 는 `Err` 를 만나면 그 자리에서 함수를 끝내고 그 에러를 돌려준다.
`validate_age` 의 에러 타입은 `String` 인데 `parse()` 의 에러는 `ParseIntError` 라, `map_err` 로 「숫자를 입력하세요」 `String` 으로 바꾼 뒤에야 `?` 로 돌려줄 수 있다.
근거: 2-summary 「동작 방식 (7)」.

## 실습 정답

### 실습 1. 표준 입출력 패턴 여덟 가지를 시뮬레이션하는 프로그램

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 원래 값과 `trim` 값 찍기 | `read_line_demo` 의 `simulated.trim()` · 두 `println!` |
| 2. `parse_input` 과 세 결과 | `read_number_demo` 안 `fn parse_input` 의 `trim().parse::<i32>().map_err(..)` |
| 3. 공백 구분 · 쉼표 구분 | `read_multiple_demo` 의 `split_whitespace().filter_map(..).collect()` · `split(',').collect()` |
| 4. 줄 번호 붙여 찍기 | `read_multiline_demo` 의 `input.lines().enumerate()` 와 `i + 1` |
| 5. flush 이유 두 줄 | `prompt_demo` 의 두 `println!` |
| 6. 잠금 차이 세 줄 | `stdin_lock_demo` 의 세 `println!` |
| 7. `validate_age` 와 세 입력 | `validation_loop_demo` 안 `fn validate_age` 의 `map_err(..)?` · `age > 150` · `match` |
| 8. `BufWriter` 다섯 줄 + flush | `stdout_buffering_demo` 의 `io::BufWriter::new(stdout.lock())` · `writeln!` · `handle.flush()` |
| 9. 차례대로 부르고 정리 | `main` 의 여덟 호출과 「정리」 네 줄 |
| 10. 제목 앞 빈 줄 | 각 함수 첫 `println!("\n=== … ===")` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`rust/rust-io/reference/stdin-stdout.rs`

```rust
// [입출력 & 직렬화] 표준 입출력
// 설명: std::io::stdin, BufRead, 입력 파싱, 출력 버퍼링
// 팁: stdin은 기본적으로 줄 버퍼링된다. print!는 flush가 필요하고 println!은 자동 flush된다. 성능이 중요하면 stdin().lock()으로 한 번만 잠그자. 입력 파싱은 항상 trim() 후 parse()하고 에러를 처리해야 한다.

// io: stdin/stdout, BufRead: lines()/read_line, Write: flush/writeln!
use std::io::{self, BufRead, Write};

// === stdin/stdout 패턴 시뮬레이션 ===
// 실제로는 사용자 입력을 받지만, 여기서는 패턴만 보여줍니다.

// 패턴 1: 한 줄 입력 받기
// 한 줄을 String으로 받고 trim하여 사용하는 표준 패턴
fn read_line_demo() {
    println!("=== 한 줄 입력 패턴 ===");
    // 실제 코드:
    // let mut input = String::new();
    // io::stdin().read_line(&mut input).expect("입력 실패");
    // let input = input.trim();

    // 시뮬레이션: 양쪽 공백 + 개행 제거 효과 보여주기
    let simulated = "  Hello, World!  ";
    let trimmed = simulated.trim();
    println!("  입력 시뮬레이션: '{}'", simulated);
    println!("  trim 후: '{}'", trimmed);
}

// 패턴 2: 숫자 입력 받기
// trim 후 parse + 에러 처리
fn read_number_demo() {
    println!("\n=== 숫자 입력 패턴 ===");
    // 실제 코드:
    // let mut input = String::new();
    // io::stdin().read_line(&mut input).expect("입력 실패");
    // let number: i32 = input.trim().parse().expect("숫자가 아님");

    // 안전한 버전:
    // 에러를 String으로 매핑한 안전 변환
    fn parse_input(input: &str) -> Result<i32, String> {
        input.trim()
            .parse::<i32>()
            .map_err(|e| format!("파싱 에러: {}", e))
    }

    println!("  parse('42'): {:?}", parse_input("42"));
    println!("  parse('abc'): {:?}", parse_input("abc"));
    println!("  parse('  99  '): {:?}", parse_input("  99  "));
}

// 패턴 3: 여러 값 한 줄에 입력
// 공백 구분 다중 값 파싱
fn read_multiple_demo() {
    println!("\n=== 여러 값 입력 패턴 ===");
    let input = "10 20 30 40 50";
    // split_whitespace: 어떤 공백이든 분리. filter_map으로 파싱 실패는 제외
    let numbers: Vec<i32> = input
        .split_whitespace()
        .filter_map(|s| s.parse().ok())
        .collect();
    println!("  입력: '{}'", input);
    println!("  파싱: {:?}", numbers);

    // 쉼표 구분
    let csv_input = "Alice,30,Seoul";
    let fields: Vec<&str> = csv_input.split(',').collect();
    println!("  CSV 입력: '{}'", csv_input);
    println!("  필드: {:?}", fields);
}

// 패턴 4: 여러 줄 입력 (EOF까지)
// stdin().lock().lines()로 EOF까지 반복
fn read_multiline_demo() {
    println!("\n=== 여러 줄 입력 패턴 ===");
    // 실제 코드:
    // let stdin = io::stdin();
    // for line in stdin.lock().lines() {
    //     let line = line.expect("읽기 실패");
    //     if line.is_empty() { break; }
    //     println!("입력: {}", line);
    // }

    // 시뮬레이션: 문자열의 lines() 이터레이터로
    let input = "첫 번째 줄\n두 번째 줄\n세 번째 줄";
    for (i, line) in input.lines().enumerate() {
        println!("  줄 {}: {}", i + 1, line);
    }
}

// 패턴 5: 프롬프트 출력 후 입력
// print! + flush가 필요한 이유
fn prompt_demo() {
    println!("\n=== 프롬프트 패턴 ===");
    // 실제 코드:
    // print!("이름을 입력하세요: ");
    // io::stdout().flush().unwrap(); // print!는 줄바꿈이 없어 flush 필요
    // let mut name = String::new();
    // io::stdin().read_line(&mut name).unwrap();

    // flush가 필요한 이유:
    // stdout이 줄 버퍼링이라 \n 없이는 화면에 즉시 보이지 않음
    println!("  print!()는 줄바꿈이 없으므로 버퍼에 남아있을 수 있다");
    println!("  io::stdout().flush()로 즉시 출력해야 프롬프트가 보인다");
}

// 패턴 6: stdin lock (성능)
// 매 read_line마다 lock 비용 → 한 번 lock으로 줄이기
fn stdin_lock_demo() {
    println!("\n=== stdin lock 패턴 ===");
    // 성능 중요시 stdin.lock()으로 매번 lock하지 않게
    // let stdin = io::stdin();
    // let locked = stdin.lock(); // 한 번만 lock
    // for line in locked.lines() {
    //     process(line?);
    // }

    println!("  stdin().read_line(): 매 호출마다 lock/unlock");
    println!("  stdin().lock().lines(): 한 번 lock, 반복 사용 (빠름)");
    println!("  경쟁 프로그래밍에서 중요한 차이");
}

// 패턴 7: 입력 유효성 검사 루프
// 잘못된 입력은 다시 받는 표준 패턴
fn validation_loop_demo() {
    println!("\n=== 입력 유효성 검사 패턴 ===");

    // 파싱 + 도메인 검증을 한 함수에 모음
    fn validate_age(input: &str) -> Result<u32, String> {
        let age: u32 = input.trim().parse()
            .map_err(|_| "숫자를 입력하세요".to_string())?;
        if age > 150 {
            Err("나이는 150 이하여야 합니다".to_string())
        } else {
            Ok(age)
        }
    }

    // 실제 코드:
    // loop {
    //     print!("나이: ");
    //     io::stdout().flush().unwrap();
    //     let mut input = String::new();
    //     io::stdin().read_line(&mut input).unwrap();
    //     match validate_age(&input) {
    //         Ok(age) => { println!("나이: {}", age); break; }
    //         Err(e) => println!("오류: {}", e),
    //     }
    // }

    // 시뮬레이션: 다양한 입력 결과
    let test_inputs = vec!["abc", "200", "25"];
    for input in test_inputs {
        match validate_age(input) {
            Ok(age) => println!("  '{}' -> 유효: {}", input, age),
            Err(e) => println!("  '{}' -> 에러: {}", input, e),
        }
    }
}

// 패턴 8: stdout 버퍼링
// 대량 출력 시 BufWriter로 시스콜 줄이기
fn stdout_buffering_demo() {
    println!("\n=== stdout 버퍼링 ===");
    // stdout 핸들 획득
    let stdout = io::stdout();
    // lock한 stdout을 BufWriter로 감쌈 → write 비용 최소화
    let mut handle = io::BufWriter::new(stdout.lock());

    for i in 0..5 {
        // BufWriter에 쓰기 (메모리 버퍼)
        writeln!(handle, "  버퍼링된 출력 {}", i).unwrap();
    }
    // 모아둔 데이터를 한 번에 stdout으로 flush
    handle.flush().unwrap();
    println!("  BufWriter<Stdout>로 대량 출력 성능 향상");
}

fn main() {
    // 모든 데모 순차 실행
    read_line_demo();
    read_number_demo();
    read_multiple_demo();
    read_multiline_demo();
    prompt_demo();
    stdin_lock_demo();
    validation_loop_demo();
    stdout_buffering_demo();

    // 요약
    println!("\n=== 정리 ===");
    println!("입력: stdin().read_line() 또는 stdin().lock().lines()");
    println!("파싱: .trim().parse::<T>() + 에러 처리");
    println!("출력: println!(자동 flush), print!(수동 flush 필요)");
    println!("성능: stdin().lock(), BufWriter::new(stdout())");
}
```

**실행 결과** — 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다).

**풀이 요점**
- 실제 입력 코드는 주석으로 두고, 입력을 문자열로 흉내 내어 결과가 늘 같게 만든다.
- 숫자 입력은 `trim` → `parse` → `Result` 로 돌려주기가 기본 꼴이다.
- `filter_map(|s| s.parse().ok())` 는 실패를 버리므로 형식이 확실한 입력에만 쓴다.
- `validate_age` 는 `map_err` 로 에러 타입을 `String` 에 맞춘 뒤 `?` 를 쓴다.
- `BufWriter` 에 쓴 줄은 `flush()` 해야 확실히 나가고, 그래서 뒤의 `println!` 보다 먼저 보인다.
- `use std::io::{self, BufRead, Write};` 가 `lines()` · `flush()` · `writeln!` 을 쓸 수 있게 한다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
