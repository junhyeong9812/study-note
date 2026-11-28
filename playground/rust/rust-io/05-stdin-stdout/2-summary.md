# rust/rust-io/05 — 표준 입출력 — 정리 (힌트)

> 출처 — study-site 항목 `rust/stdin-stdout`(항목 데이터 `data/rust/io-serde.json`) · 정답 코드 study-practice `rust/rust-io/reference/stdin-stdout.rs`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다).

## 한눈에 — 쉽게 말하면

**표준 입출력은 「은행 창구의 번호표 기계와 우편함」이다.**
손님(사용자)이 창구에 말을 하면 직원은 말이 끝날 때까지(엔터) 기다렸다가 한 줄을 받아 적는다.
직원이 내보내는 서류는 바로 나가지 않고 우편함(버퍼)에 모였다가 한꺼번에 나간다.
그래서 「이름을 말씀하세요」라는 안내문을 우편함에만 넣고 내보내지 않으면 손님은 안내문을 못 본 채 멍하니 서 있게 된다.
Rust 의 `stdin` 과 `stdout` 도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 손님이 말하는 한 줄 | `read_line` 이 받는 한 줄(끝에 개행 포함) |
| 받아 적은 종이 | `String` 버퍼 |
| 말 앞뒤의 군더더기 | 공백 · 개행 → `trim()` 으로 걷어낸다 |
| 우편함 | 출력 버퍼 |
| 우편함 비우기 | `flush()` |
| 창구를 잠그고 한 손님만 받기 | `stdin().lock()` |
| 서류를 한 상자에 모아 보내기 | `BufWriter` |

```text
키보드 ──한 줄──▶ [stdin] ──read_line──▶ String "  42\n"
                                          │ trim()
                                          ▼
                                        "42" ──parse::<i32>()──▶ Ok(42) / Err(..)

프로그램 ──print!/println!──▶ [stdout 버퍼] ──flush──▶ 화면
```

## 이 주제가 답하려는 질문

1. 키보드에서 한 줄 · 여러 값 · 여러 줄을 받아 원하는 타입의 값으로 바꾸려면 어떻게 하나?
2. 사용자가 엉뚱한 값을 넣었을 때 프로그램이 죽지 않게 하려면 어떻게 하나?
3. `print!` 로 쓴 프롬프트가 화면에 안 보이는 까닭은 무엇이고 어떻게 고치나?
4. 입력 · 출력이 많을 때 느려지지 않게 하려면 무엇을 하나?

## 동작 방식

이 항목의 예제는 실제 키보드 입력 대신 문자열을 「입력이 이렇게 들어왔다」고 가정해 패턴을 보인다.
실제 입력 코드는 주석으로 함께 적혀 있다.

### (1) 한 줄 받기 — `read_line`

**언제 쓰나** — 사용자에게서 한 줄(이름, 명령 하나)을 받을 때.

```text
let mut input = String::new();
io::stdin().read_line(&mut input).expect("입력 실패");
        │
        ▼   사용자가 "  Hello, World!  " 치고 엔터
input == "  Hello, World!  \n"      ← 끝의 개행까지 들어 있다
        │ input.trim()
        ▼
"Hello, World!"                     ← 양쪽 공백과 개행이 빠진다
```

- 빈 `String` 을 먼저 만들고 그 가변 참조를 `read_line` 에 넘긴다.
- `read_line` 은 엔터까지의 한 줄을 버퍼에 넣는데, 끝의 개행 문자도 함께 넣는다.
- `read_line` 은 `Result` 를 돌려주므로 `expect` 로 실패를 처리한다.
- `trim()` 은 앞뒤의 공백과 개행을 걷어낸 `&str` 을 돌려준다.

> **`trim()`** — 문자열 앞뒤의 공백 문자(스페이스 · 탭 · 개행)를 뺀 조각을 돌려주는 메서드.\
> 예: `"  hi \n".trim()` 은 `"hi"`.

### (2) 숫자로 바꾸기 — `trim` → `parse` → 에러 처리

**언제 쓰나** — 입력을 `i32` · `u32` 같은 숫자로 써야 할 때.

```text
"  99  " ──trim──▶ "99" ──parse::<i32>──▶ Ok(99)
"42"     ──trim──▶ "42" ──parse::<i32>──▶ Ok(42)
"abc"    ──trim──▶ "abc"──parse::<i32>──▶ Err(ParseIntError)
                                             │ map_err(|e| format!("파싱 에러: {}", e))
                                             ▼
                                         Err("파싱 에러: …")
```

- `parse::<i32>()` 는 문자열을 `i32` 로 바꾸려 하고 `Result<i32, ParseIntError>` 를 돌려준다.
- `trim()` 을 빼면 `read_line` 이 남긴 개행 때문에 멀쩡한 숫자도 파싱에 실패한다.
- 빠른 길은 `.expect("숫자가 아님")` 이지만, 숫자가 아니면 프로그램이 패닉으로 끝난다.
- 안전한 길은 `Result` 를 그대로 돌려주는 것이다 — 원본은 `map_err` 로 에러를 `String` 으로 바꿔 `Result<i32, String>` 을 돌려준다.
- `{:?}` 로 `Result` 를 찍으면 `Ok(42)` 나 `Err("…")` 꼴로 나온다(`String` 은 따옴표에 싸인다).
- `Err` 안의 문구 중 「파싱 에러: 」 뒤는 표준 라이브러리의 `ParseIntError` 가 내는 문구다.

> **`map_err`** — `Result` 가 `Err` 일 때만 안의 에러 값을 다른 값으로 바꾸는 메서드.\
> 예: `r.map_err(|e| e.to_string())` 은 `Result<T, ParseIntError>` 를 `Result<T, String>` 으로 바꾼다.

### (3) 한 줄에 여러 값 — `split_whitespace` · `split(',')`

**언제 쓰나** — `10 20 30` 이나 `Alice,30,Seoul` 처럼 한 줄에 값이 여럿일 때.

```text
"10 20 30 40 50"
   │ split_whitespace()      → "10","20","30","40","50"
   │ filter_map(|s| s.parse().ok())
   │                          → 파싱에 성공한 것만 남긴다
   │ collect::<Vec<i32>>()
   ▼
[10, 20, 30, 40, 50]

"Alice,30,Seoul" ──split(',')──▶ ["Alice", "30", "Seoul"]   (Vec<&str>)
```

- `split_whitespace()` 는 공백이 몇 칸이든, 탭이든 상관없이 공백을 기준으로 자른다.
- `s.parse().ok()` 는 `Result` 를 `Option` 으로 바꾼다 — 성공은 `Some`, 실패는 `None`.
- `filter_map` 은 `None` 을 버리고 `Some` 안의 값만 모은다.
- 그래서 파싱에 실패한 조각은 **에러 없이 조용히 사라진다**.
- `parse()` 의 대상 타입은 `Vec<i32>` 라는 타입 표기에서 추론된다.
- `split(',')` 는 정확히 쉼표에서 자르고, 조각은 원본을 빌린 `&str` 이다.

### (4) 여러 줄 받기 — `stdin.lock().lines()`

**언제 쓰나** — 입력이 몇 줄일지 모르고 끝(EOF)까지 다 읽어야 할 때.

```text
let stdin = io::stdin();
for line in stdin.lock().lines() {   ← 줄마다 Result<String> 이 나온다
    let line = line.expect("읽기 실패");
    if line.is_empty() { break; }    ← 빈 줄이면 멈춘다
    println!("입력: {}", line);
}
        │
        ▼
EOF 가 오면 lines() 가 끝나 for 가 끝난다
빈 줄이 오면 break 로 그 전에 끝난다
```

- `lines()` 는 `BufRead` 트레이트의 메서드라 `use std::io::BufRead` 가 필요하다.
- `lines()` 가 내놓는 한 줄에는 개행이 붙어 있지 않다.
- 각 줄은 읽기가 실패할 수 있어 `Result` 로 나온다.
- 원본의 실제 코드는 빈 줄에서 `break` 하므로, 중간에 빈 줄이 있으면 그 뒤 줄은 읽지 않는다.
- 예제는 이 흐름을 문자열의 `lines()` 와 `enumerate()` 로 흉내 내어 「줄 1: …」처럼 번호를 붙여 찍는다(`enumerate` 는 0부터 세므로 `i + 1`).

> **EOF** — End Of File, 더 읽을 입력이 없다는 신호.\
> 예: 파일을 끝까지 읽었거나, 터미널에서 입력 끝 키를 눌렀을 때.

### (5) 프롬프트와 `flush` — `print!` 대 `println!`

**언제 쓰나** — 「이름을 입력하세요: 」처럼 같은 줄에서 입력을 받으려 할 때.

```text
print!("이름을 입력하세요: ");   ── 버퍼에 들어감, 개행 없음 → 아직 화면에 없을 수 있다
io::stdout().flush().unwrap();   ── 버퍼를 비움 → 이제 화면에 보인다
io::stdin().read_line(&mut name) ── 사용자 입력 기다림

println!("…")                    ── 끝에 \n → 줄 단위로 버퍼가 비워져 바로 보인다
```

- stdout 은 줄 버퍼링이라 개행이 와야 버퍼를 화면으로 내보낸다(원본 정답 코드의 주석).
- `print!` 는 개행을 붙이지 않으므로 프롬프트가 버퍼에 남을 수 있다.
- 그 상태로 `read_line` 이 입력을 기다리면 사용자는 프롬프트 없이 빈 화면을 보게 된다.
- `flush()` 는 `Write` 트레이트의 메서드라 `use std::io::Write` 가 필요하다.

> **flush** — 버퍼에 모아 둔 데이터를 지금 바로 목적지로 내보내는 일.\
> 예: `io::stdout().flush()`.

### (6) `lock` 으로 한 번만 잠그기

**언제 쓰나** — 입력 줄이 아주 많아 속도가 중요할 때(원본: 경쟁 프로그래밍).

```text
stdin().read_line() × N 번   → 잠금/풀기 N 번
stdin().lock().lines()       → 잠금 1 번, 그 잠금으로 N 줄 읽기
```

- 표준 입력은 프로그램 전체가 함께 쓰는 하나의 자원이라 읽을 때마다 잠금이 걸린다.
- `stdin().read_line()` 은 부를 때마다 잠그고 푼다.
- `stdin().lock()` 은 잠금을 한 번 잡아 둔 핸들을 돌려주고, 그 핸들로 계속 읽는다.

> **lock(잠금)** — 여러 곳이 같은 자원을 동시에 건드리지 못하게 한 번에 하나만 쓰도록 막는 장치.\
> 예: `let locked = io::stdin().lock();`.

### (7) 입력 검증 루프 — 파싱 + 도메인 검사

**언제 쓰나** — 「0~150 사이 나이」처럼 숫자이기만 해서는 부족하고, 틀리면 다시 물어야 할 때.

```text
validate_age(input)
  │ input.trim().parse::<u32>()
  │   실패 → map_err → Err("숫자를 입력하세요")  ── ? 가 여기서 바로 돌려준다
  ▼ 성공 age
  age > 150 ? → Err("나이는 150 이하여야 합니다")
            : → Ok(age)

loop { 프롬프트 → flush → read_line → match validate_age
         Ok  → 출력하고 break
         Err → 오류 출력하고 다시 반복 }
```

- `u32` 는 부호 없는 정수라 음수 문자열(`"-3"`)은 파싱 단계에서 실패한다.
- `?` 는 `Err` 면 그 자리에서 함수를 끝내고 그 `Err` 를 돌려준다.
- 함수의 에러 타입이 `String` 이므로, `ParseIntError` 를 `map_err` 로 `String` 으로 바꾼 뒤에 `?` 를 쓴다.
- 파싱 검사와 범위 검사를 한 함수에 모아 두면 루프 쪽은 `Ok` / `Err` 만 보면 된다.
- 예제는 `"abc"` · `"200"` · `"25"` 세 입력을 넣어 각각 어떤 갈래로 가는지 보인다.

### (8) `BufWriter` 로 출력 모으기

**언제 쓰나** — 줄을 아주 많이 찍어야 할 때.

```text
let stdout = io::stdout();
let mut handle = io::BufWriter::new(stdout.lock());
for i in 0..5 { writeln!(handle, "…{}", i).unwrap(); }   ── 메모리 버퍼에 쌓임
handle.flush().unwrap();                                   ── 한 번에 stdout 으로
```

- `stdout.lock()` 으로 잠금을 한 번 잡고, 그것을 `BufWriter` 로 감싼다.
- `writeln!` 은 `println!` 과 같은 꼴이지만 첫 인자로 받은 대상에 쓰고, `Result` 를 돌려준다.
- 쓰기가 메모리 버퍼에 모이므로 실제 출력 시스템 호출 횟수가 줄어든다.
- 마지막에 `flush()` 로 모은 내용을 내보낸다.

> **`BufWriter`** — 쓰기를 메모리에 모았다가 한꺼번에 내보내는 래퍼.\
> 예: `io::BufWriter::new(io::stdout().lock())`.

## 문법 — 형태와 규칙

```rust
use std::io::{self, BufRead, Write};

fn main() {
    print!("수 두 개: ");
    io::stdout().flush().unwrap();

    let mut line = String::new();
    io::stdin().read_line(&mut line).expect("입력 실패");

    let nums: Vec<i64> = line
        .split_whitespace()
        .filter_map(|s| s.parse().ok())
        .collect();
    println!("합: {}", nums.iter().sum::<i64>());
}
```

- `use std::io::{self, BufRead, Write};` — `io` 모듈, `lines()` 용 `BufRead`, `flush` · `writeln!` 용 `Write` 를 한 번에 가져온다.
- `read_line(&mut s)` — 가변 참조를 넘긴다. 결과는 `Result` 다.
- `.trim().parse::<T>()` — 타입은 터보피시(`::<T>`)나 변수 타입 표기(`let n: i32 = …`)로 정한다.
- 파싱 실패 처리는 `expect`(패닉) · `match` · `map_err` + `?` · `.ok()` 중에서 고른다.
- `print!` 뒤에 입력을 받는다면 `io::stdout().flush()` 를 부른다.
- 많이 읽을 때는 `io::stdin().lock().lines()`, 많이 쓸 때는 `io::BufWriter::new(io::stdout().lock())` + `writeln!`.

| 할 일 | 쓰는 것 | 돌려주는 것 |
|---|---|---|
| 한 줄 읽기 | `io::stdin().read_line(&mut s)` | `Result` (s 에 개행 포함 한 줄) |
| 여러 줄 읽기 | `io::stdin().lock().lines()` | 줄마다 `Result<String>` (개행 없음) |
| 공백 정리 | `s.trim()` | `&str` |
| 숫자로 | `s.parse::<i32>()` | `Result<i32, ParseIntError>` |
| 공백 구분 | `s.split_whitespace()` | `&str` 이터레이터 |
| 쉼표 구분 | `s.split(',')` | `&str` 이터레이터 |
| 즉시 출력 | `io::stdout().flush()` | `Result` |
| 모아 출력 | `BufWriter` + `writeln!` + `flush` | `Result` |

## 어디서 틀리나

### 1. `trim()` 없이 `parse()`

`read_line` 이 넣은 개행 때문에 `"42\n"` 은 숫자가 아니다.
원본 팁: 입력 파싱은 항상 `trim()` 후 `parse()` 하고 에러를 처리해야 한다.

### 2. `parse()` 실패를 `expect` 로 덮기

`expect("숫자가 아님")` 은 짧지만 사용자가 오타 하나만 내도 프로그램이 패닉으로 끝난다.
사용자 입력이라면 `Result` 를 돌려주고 검증 루프로 다시 물어야 한다.

### 3. `print!` 프롬프트가 안 보임

원본 팁: `print!` 는 flush 가 필요하고 `println!` 은 자동 flush 된다.
`print!` 다음, 입력을 기다리기 전에 `io::stdout().flush()` 를 부른다.
`Write` 를 `use` 하지 않으면 `flush` 메서드를 찾지 못한다.

### 4. 매 줄 `stdin().read_line()` 으로 대량 입력

원본 팁: 성능이 중요하면 `stdin().lock()` 으로 한 번만 잠그자.
줄이 적은 대화형 프로그램에서는 차이가 드러나지 않는다.

### 5. `filter_map(.. .ok())` 가 잘못된 값을 삼킴

`"10 20 x 30"` 에서 `"x"` 는 에러 없이 사라진다.
값 개수가 정해진 입력이라면 개수를 확인하거나 실패를 에러로 다뤄야 한다.
쉼표로 구분된 `"10,20"` 을 `split_whitespace` 로 자르면 조각이 하나(`"10,20"`)이고 그것은 파싱에 실패해 결과가 빈다.

### 6. 빈 줄에서 `break` 하는 여러 줄 루프

원본의 실제 코드는 빈 줄을 만나면 멈춘다.
입력 중간에 빈 줄이 있는 형식이면 그 뒤를 놓친다.

### 7. 원본 팁의 「stdin 은 기본적으로 줄 버퍼링된다」

원본의 주장 → stdin 은 기본적으로 줄 버퍼링된다.
왜 의심스러운가 → 원본 정답 코드의 주석은 「stdout 이 줄 버퍼링」이라고 쓴다.
flush 이야기와 이어지는 것도 stdout 쪽이다.
입력이 한 줄씩 들어오는 듯 보이는 것은 터미널이 엔터 전까지 입력을 넘기지 않기 때문일 수 있고, Rust stdin 자체의 버퍼 방식과는 따로 봐야 한다(확인 필요).

### 8. 「`println!` 은 자동 flush」의 뜻

`println!` 이 따로 `flush` 를 부르는 것이 아니라, 끝에 붙는 개행이 줄 버퍼링된 stdout 을 비우게 만든다고 읽는 편이 정확하다(원본 정답 코드 주석의 「줄 버퍼링이라 \n 없이는 화면에 즉시 보이지 않음」에 기댄 해석).

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `read_line` 이 줄 끝 개행을 버퍼에 남긴다 | 표준 라이브러리 API 동작 |
| `lines()` 의 각 줄에는 개행이 없다 | 표준 라이브러리 API 동작 |
| stdout 이 줄 버퍼링이다 | 표준 라이브러리의 현재 구현(문서화된 동작인지 버전별로 확인 필요) |
| stdin 이 줄 버퍼링이다(원본 팁) | 의심스러운 주장 — 터미널(OS) 동작과 섞였을 수 있다(확인 필요) |
| `read_line` 이 부를 때마다 잠근다 | 표준 라이브러리 구현 |
| `lock()` 이 반복 `read_line` 보다 빠르다 | 성능 경향일 뿐 보장 아님, 수치 없음 |
| `ParseIntError` 의 문구 | 표준 라이브러리 구현 — 문구는 바뀔 수 있다 |
| `u32` 로 `"-3"` 파싱 실패 | 타입 규칙 — 부호 없는 정수는 음수를 못 담는다 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 대화형으로 한 줄 받기 | `read_line` + `trim` | `lock().lines()` 루프로 한 줄만 받기(필요 이상) |
| 같은 줄에 프롬프트 | `print!` + `flush` | `print!` 만 쓰고 바로 `read_line` |
| 입력이 수만 줄 | `stdin().lock().lines()` | 줄마다 `stdin().read_line()` |
| 출력이 수만 줄 | `BufWriter` + `writeln!` + `flush` | 줄마다 `println!` |
| 사용자 입력 숫자 | `parse` + `Result` 처리 · 검증 루프 | `parse().expect(..)` |
| 형식이 확실한 공백 구분 값 | `split_whitespace` + `filter_map` | 개수가 중요한데 `filter_map` 으로 실패를 버리기 |

## 핵심 문장

1. **입력은 「`read_line` → `trim` → `parse` → 에러 처리」 네 단계다** — 넷 중 하나라도 빼면 어딘가에서 깨진다.
2. **stdout 은 줄 단위로 버퍼링된다** — 개행 없는 `print!` 뒤에는 `flush` 가 필요하다.
3. **잠금과 버퍼링은 한 번에 모아서** — 대량 입력은 `stdin().lock()`, 대량 출력은 `BufWriter`.
4. **파싱과 도메인 검사를 한 함수에 모아 `Result` 로 돌려주면** 검증 루프가 단순해진다.

## 관련 자료

- [bufread-bufwrite](../02-bufread-bufwrite/2-summary.md)
- `file-read-write` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `args-parsing` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/rust/io-serde.json` 의 `stdin-stdout`

## 용어 풀이

- **표준 입력(stdin)** — 프로그램이 기본으로 읽는 입력 통로, 보통 키보드.
- **표준 출력(stdout)** — 프로그램이 기본으로 쓰는 출력 통로, 보통 터미널 화면.
- **버퍼** — 데이터를 바로 보내지 않고 잠시 모아 두는 메모리 공간.
- **줄 버퍼링** — 개행이 올 때마다 버퍼를 내보내는 방식.
- **flush** — 버퍼를 지금 바로 비워 내보내는 일.
- **EOF** — 더 읽을 입력이 없다는 신호.
- **lock(잠금)** — 공유 자원을 한 번에 하나만 쓰게 막는 장치.
- **`BufRead`** — `lines()` · `read_line` 같은 버퍼 기반 읽기 메서드를 주는 트레이트.
- **`Write`** — `flush` · `writeln!` 대상이 되는 쓰기 트레이트.
- **`BufWriter`** — 쓰기를 모았다가 한꺼번에 내보내는 래퍼.
- **`trim()`** — 앞뒤 공백 · 개행을 뺀 조각을 돌려주는 메서드.
- **`parse()`** — 문자열을 지정한 타입으로 바꾸려 하고 `Result` 를 돌려주는 메서드.
- **`map_err`** — `Err` 안의 값만 바꾸는 `Result` 메서드.
- **`?` 연산자** — `Err` 면 그 자리에서 함수를 끝내고 에러를 돌려주는 연산자.
- **`filter_map`** — 클로저가 `Some` 을 낸 것만 모으는 이터레이터 어댑터.
- **`split_whitespace`** — 공백 묶음을 기준으로 자르는 메서드.
- **시스템 호출(시스콜)** — 프로그램이 운영체제에 일을 부탁하는 호출, 출력 한 번도 여기에 든다.

## 더 들어가면

- `read_line` 은 버퍼를 비우지 않고 뒤에 **덧붙인다** — 루프에서 같은 `String` 을 재사용하면 `clear()` 를 먼저 불러야 한다(확인 필요).
- `read_line` 은 EOF 에서 `Ok(0)` 을 돌려준다 — 이 값으로 입력 끝을 알아낼 수 있다(확인 필요).
- `BufWriter` 는 버려질(drop) 때 남은 내용을 flush 하려 하지만, 그때의 에러는 무시된다 — 그래서 명시적 `flush()` 가 권장된다(확인 필요).
- 원본 패턴 8 은 `BufWriter` 가 stdout 잠금을 쥔 채로 `println!` 을 부른다. Rust 의 stdout 잠금은 같은 스레드에서 다시 잡을 수 있는 재진입 잠금이라 멈추지 않는 것으로 안다(확인 필요).
- stdout 은 터미널이 아닐 때(파이프 · 파일)도 Rust 에서는 줄 버퍼링으로 동작하는 것으로 안다 — C 의 stdio 와 다를 수 있다(확인 필요).
- 최근 Rust 에는 `io::read_to_string(io::stdin())` 처럼 입력 전체를 한 번에 읽는 함수가 있다(도입 버전 확인 필요).
- `Stdin::lines()` 를 `lock()` 없이 바로 쓰는 메서드도 최근 버전에 있다(도입 버전 확인 필요).
