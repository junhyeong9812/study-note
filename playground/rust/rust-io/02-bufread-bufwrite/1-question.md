# rust/rust-io/02 — BufReader & BufWriter — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. `clear()` 없이 `read_line` 을 두 번 부르면 (예측)

```rust
// 질문용 발췌 — 파일의 첫 두 줄은 "라인 0001: 데이터_7", "라인 0002: 데이터_14"
let mut line = String::new();
reader.read_line(&mut line)?;
reader.read_line(&mut line)?;          // clear() 를 부르지 않았다
println!("{:?}", line.trim());
```

- 찍히는 문자열에는 무엇이 들어 있는가?

### 2. 로그에서 `[ERROR]` 줄 거르기 (예측)

```rust
// 질문용 발췌 — app.log 의 차례: [INFO] 서버 시작 / [ERROR] DB 연결 실패 / [INFO] 재연결 성공
//                               / [WARN] 메모리 사용량 높음 / [ERROR] 타임아웃 / [INFO] 요청 처리 완료
let errors: Vec<String> = reader.lines()
    .filter_map(|line| line.ok())
    .filter(|line| line.starts_with("[ERROR]"))
    .collect();
println!("에러 수: {}", errors.len());
```

- `errors` 에는 어떤 줄이 어떤 차례로 담기는가?
- 마지막 줄에 찍히는 에러 수는 얼마인가?

### 3. `read_until(b':')` 로 첫 줄을 읽으면 (예측)

```rust
// 질문용 발췌 — 파일의 첫 줄은 "라인 0001: 데이터_7"
let mut buf = Vec::new();
reader.read_until(b':', &mut buf)?;
println!("{:?}", String::from_utf8_lossy(&buf));
```

- `buf` 에 담긴 내용은 무엇인가?
- 같은 자리에서 `split(b':')` 의 첫 조각을 꺼냈다면 무엇이 다른가?

### 4. 블록 끝에서 버퍼가 비워지는데도 `flush()?` 를 직접 부르는 까닭 (왜)

- `Drop` 이 버퍼를 비워 주는데 왜 `writer.flush()?` 를 따로 부르는가?

### 5. `BufReader` 로 감싸면 빨라지는 까닭 (왜)

- `File` 을 직접 읽는 것보다 `BufReader` 를 거치는 것이 왜 빠른가?

### 6. `read` 가 64 보다 적은 수를 돌려줄 때 (경계)

- 64바이트 청크로 읽다가 `read` 가 40을 돌려주면 그것이 파일 끝이라고 판단해도 되는가?

### 7. 버퍼를 64KB 로 키우는 것의 득과 실 (경계)

- `BufWriter::with_capacity(64 * 1024, file)` 로 버퍼를 키우면 무엇을 얻고 무엇을 내주는가?

### 8. `fs::read_to_string` 과 `lines()` 스트리밍 (연결)

- 수 GB 짜리 로그에서 에러 줄을 셀 때 `fs::read_to_string()` 보다 `BufReader` + `lines()` 가 맞는 까닭은 무엇인가?

### 9. `line?` 와 `filter_map(|line| line.ok())` (연결)

- 두 방식은 읽기 에러가 난 줄을 각각 어떻게 다루는가?

## 실습

### 실습 1. 버퍼링된 쓰기 · 읽기 일곱 가지를 한 프로그램에 모으기

**만들 것** — 임시 디렉터리에 파일을 만들고, `BufWriter` 로 쓰고, `BufReader` 의 다섯 가지 읽기(`lines` · `read_line` · `split` · `read_until` · `read`)로 다시 읽은 뒤, 로그 파일에서 에러 줄만 골라내고 디렉터리를 지우는 프로그램을 만든다.

**요구 조건**

1. 1단계 — `/tmp/rust_buf_demo` 디렉터리를 (이미 있어도 에러 없이) 만든다.
2. 1단계 — `buffered.txt` 를 만들어 기본 버퍼의 `BufWriter` 로 감싸고, `i` 가 1부터 100까지 `"라인 {:04}: 데이터_{}"` 꼴(`i`, `i * 7`)로 한 줄씩 쓴 뒤 직접 `flush` 하고 완료 메시지를 찍는다.
3. 1단계 — `large_buf.txt` 에는 버퍼 크기를 `64 * 1024` 로 정한 `BufWriter` 로 `"big data line {}"` 를 0부터 999까지 쓰고 `flush` 한다.
4. 2단계 — `buffered.txt` 를 `BufReader` 로 열어 `lines()` 와 `enumerate()` 로 처음 5줄만 찍고 반복을 멈춘다. 각 줄의 에러는 `?` 로 전파한다.
5. 2단계 — 다시 열어 `read_line` 으로 첫 줄을 읽고 읽은 바이트 수와 다듬은 내용을 찍은 뒤, 같은 `String` 을 비우고 두 번째 줄을 읽어 찍는다.
6. 3단계 — `split(b'\n')` 으로 조각을 세며 처음 3조각만 UTF-8 로 해석해 찍고, 끝에 총 조각 수를 찍는다.
7. 4단계 — `read_until(b':')` 로 첫 `:` 까지 읽어 바이트 수와 내용을 찍는다.
8. 5단계 — 성능 비교 표(시작 코드에 채워져 있음)를 그대로 찍는다.
9. 6단계 — 64바이트 배열을 청크로 삼아 `read` 를 `0` 이 나올 때까지 반복하며 총 바이트 수와 청크 수를 센다.
10. 7단계 — `app.log` 에 여섯 줄의 로그를 `BufWriter` 로 쓰고 `flush` 한 뒤, `lines()` 에서 `Ok` 인 줄만 남기고 `[ERROR]` 로 시작하는 줄만 `Vec<String>` 으로 모아 하나씩 찍고 개수를 찍는다.
11. 마무리 — 디렉터리를 통째로 지우고 정리 완료를 찍는다. `main` 은 `io::Result<()>` 를 돌려준다.

**시작 코드**

```rust
use std::fs::{self, File};
use std::io::{self, BufRead, BufReader, BufWriter, Read, Write};

fn main() -> io::Result<()> {
    let dir = "/tmp/rust_buf_demo";
    // TODO: dir 을 (부모까지, 이미 있어도 괜찮게) 만든다

    // === 1. BufWriter ===
    println!("=== BufWriter ===");
    let path = format!("{}/buffered.txt", dir);
    {
        // TODO: path 에 파일을 만들고 기본 버퍼의 BufWriter 로 감싼다
        // TODO: i = 1..=100 마다 "라인 {:04}: 데이터_{}" (i, i * 7) 를 한 줄 쓴다
        // TODO: 남은 버퍼를 직접 비운다
    }
    println!("100줄 쓰기 완료: {}", path);

    let path2 = format!("{}/large_buf.txt", dir);
    {
        // TODO: 64 * 1024 바이트 버퍼의 BufWriter 로 "big data line {}" 를 0..1000 쓰고 비운다
    }
    println!("64KB 버퍼로 1000줄 쓰기 완료");

    // === 2. BufReader ===
    println!("\n=== BufReader ===");
    {
        // TODO: path 를 열어 BufReader 로 감싼다
        println!("처음 5줄:");
        // TODO: lines() + enumerate() 로 처음 5줄만 "  {}" 로 찍고 멈춘다
    }

    println!("\nread_line:");
    {
        // TODO: path 를 열어 BufReader 로 감싸고, 줄을 담을 String 을 만든다
        // TODO: 첫 줄을 읽어 "  읽은 바이트: {}, 내용: {:?}" 로 찍는다 (내용은 trim)
        // TODO: String 을 비운 뒤 두 번째 줄을 읽어 "  두 번째 줄: {:?}" 로 찍는다
    }

    // === 3. split ===
    println!("\n=== split ===");
    {
        let mut count = 0;
        // TODO: '\n' 바이트로 나눈 조각을 돌며 count 를 늘리고,
        //       처음 3개만 "  세그먼트 {}: {:?}" (from_utf8_lossy) 로 찍는다
        println!("  총 세그먼트 수: {}", count);
    }

    // === 4. read_until ===
    println!("\n=== read_until ===");
    {
        // TODO: ':' 까지 Vec<u8> 에 읽어 "  ':' 까지: {} bytes -> {:?}" 로 찍는다
    }

    // === 5. 성능 비교 ===
    println!("\n=== 성능 비교 ===");
    println!("┌────────────────────────┬──────────────────────┐");
    println!("│ 방법                   │ 특성                 │");
    println!("├────────────────────────┼──────────────────────┤");
    println!("│ fs::read_to_string()   │ 전체를 메모리에 로드 │");
    println!("│ BufReader + lines()    │ 줄 단위 스트리밍     │");
    println!("│ BufReader + read()     │ 청크 단위 스트리밍   │");
    println!("│ File::read() 직접      │ 매 호출마다 시스콜   │");
    println!("└────────────────────────┴──────────────────────┘");
    println!("BufReader/BufWriter는 시스템 콜 횟수를 줄여 성능 향상");
    println!("File 직접 사용시 read(1byte)마다 시스콜 → 매우 느림");

    // === 6. 청크 단위 읽기 ===
    println!("\n=== 청크 단위 읽기 ===");
    {
        let mut buffer = [0u8; 64];
        let mut total_bytes = 0;
        let mut chunk_count = 0;
        // TODO: path 를 BufReader 로 열고, read 가 0 을 돌려줄 때까지 반복하며 두 값을 늘린다
        println!("  총 {}바이트, {}개 청크로 읽음", total_bytes, chunk_count);
    }

    // === 7. 로그 분석 ===
    println!("\n=== 실용: 로그 파일 분석 ===");
    let log_path = format!("{}/app.log", dir);
    {
        // TODO: BufWriter 로 아래 여섯 줄을 차례로 쓰고 비운다
        // [INFO] 서버 시작
        // [ERROR] DB 연결 실패
        // [INFO] 재연결 성공
        // [WARN] 메모리 사용량 높음
        // [ERROR] 타임아웃
        // [INFO] 요청 처리 완료
    }
    // TODO: log_path 를 BufReader 로 열고 lines() → Ok 만 → "[ERROR]" 로 시작 → Vec<String> 으로 모은다
    let errors: Vec<String> = Vec::new(); // TODO: 위 결과로 바꾼다
    println!("에러 로그:");
    for err in &errors {
        println!("  {}", err);
    }
    println!("에러 수: {}", errors.len());

    fs::remove_dir_all(dir)?;
    println!("\n정리 완료");
    Ok(())
}
```

**확인 방법** — 유닉스 계열에서 `rustc bufread-bufwrite.rs && ./bufread-bufwrite` 로 돌려, 처음 5줄 · 두 번째 줄 · 총 세그먼트 수(100줄이면 100) · 에러 로그 두 줄이 찍히고 끝에 `/tmp/rust_buf_demo` 가 지워졌는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
