# rust/rust-io/02 — BufReader & BufWriter — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 두 줄이 이어 붙은 문자열이 찍힌다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
"라인 0001: 데이터_7\n라인 0002: 데이터_14"
```

**왜 그런가**
`read_line` 은 줄바꿈까지 포함해 `String` 끝에 덧붙인다.
`clear()` 가 없으니 두 번째 줄이 첫 줄 뒤에 붙어 `line` 은 `"라인 0001: 데이터_7\n라인 0002: 데이터_14\n"` 이 된다.
`trim()` 은 양 끝만 다듬으므로 맨 끝 `\n` 만 지워지고 가운데 `\n` 은 남는다.
`{:?}` 는 따옴표를 붙이고 가운데 줄바꿈을 `\n` 글자로 보여 준다.
근거: 2-summary 「동작 방식 (4)」, 「어디서 틀리나 1」.

### 2. `[ERROR]` 두 줄이 원래 차례대로 담기고 에러 수는 2다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

`errors` 는 `["[ERROR] DB 연결 실패", "[ERROR] 타임아웃"]` 이고, `에러 수: 2` 가 찍힌다.

**왜 그런가**
`lines()` 가 여섯 줄을 줄바꿈 없이 차례로 내놓는다.
`filter_map(|line| line.ok())` 는 읽기 에러가 없으니 여섯 줄을 모두 통과시킨다.
`starts_with("[ERROR]")` 를 만족하는 줄은 둘째 줄과 다섯째 줄뿐이다.
`collect()` 는 걸러진 줄을 들어온 차례 그대로 담는다.
근거: 2-summary 「동작 방식 (7)」.

### 3. `"라인 0001:"` — 구분자 `:` 까지 들어 있다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
"라인 0001:"
```

`split(b':')` 의 첫 조각이었다면 `:` 가 빠진 `"라인 0001"` 이 된다.

**왜 그런가**
`read_until` 은 구분 바이트를 만날 때까지 읽고 그 구분 바이트도 포함해 `buf` 에 붙인다.
`split` 은 구분 바이트로 나누되 조각에 구분자를 넣지 않는다.
근거: 2-summary 「동작 방식 (5)」, 「문법」의 메서드 표.

### 4. `Drop` 의 flush 는 실패를 알려 줄 수 없기 때문이다

`Drop` 은 값을 돌려줄 수 없어서, 블록 끝에서 버퍼를 비우다 쓰기 에러가 나도 호출자에게 전달되지 않는다.
`flush()?` 를 직접 부르면 실패가 `Err` 로 돌아와 `?` 로 위로 전파된다.
그래서 마지막 데이터가 정말 써졌는지 확인하려면 직접 부른다.
근거: 2-summary 「동작 방식 (2)」, 「어디서 틀리나 2」.

### 5. 시스템 콜 횟수가 줄기 때문이다

`File::read()` 를 직접 쓰면 호출마다 운영체제에 읽기를 부탁하는 시스템 콜이 일어나고, 1바이트씩 읽으면 1바이트마다 시스템 콜이 된다.
`BufReader` 는 한 번의 시스템 콜로 큰 덩어리(기본 8KB)를 받아 두고, 이후의 작은 읽기와 줄 나누기를 메모리 안에서 처리한다.
비싼 호출이 덩어리 수만큼으로 줄어든다.
근거: 2-summary 「한눈에」, 「동작 방식 (3)」, 「동작 방식 (8)」.

### 6. 판단하면 안 된다 — 끝은 `0` 이 돌아올 때뿐이다

`read` 는 0 부터 `buffer.len()` 사이 어느 만큼이든 돌려줄 수 있다.
40은 「이번에 40바이트를 읽었다」는 뜻일 뿐이며, 다음 호출에서 더 읽힐 수 있다.
EOF 는 `read` 가 `0` 을 돌려줄 때다.
또 40이 돌아왔다면 `buffer[..40]` 만 유효하다.
근거: 2-summary 「동작 방식 (6)」, 「어디서 틀리나 4」.

### 7. 시스템 콜을 더 줄이는 대신 메모리를 더 쓴다

버퍼가 크면 가득 찰 때까지 더 많이 모을 수 있어 파일로 내보내는 횟수(시스템 콜)가 더 드물어진다.
대신 그 크기(64KB)만큼 메모리를 차지한다.
얼마나 빨라지는지는 보장되지 않는다.
근거: 2-summary 「동작 방식 (1)」, 「어디서 틀리나 7」.

### 8. 파일 전체를 메모리에 올리지 않기 때문이다

`fs::read_to_string()` 은 파일 전체를 한 `String` 으로 메모리에 올리므로, 수 GB 파일이면 그만큼 메모리가 필요하다.
`BufReader` + `lines()` 는 버퍼 하나와 지금 줄 하나만 들고 다음 줄로 흘러가는 스트리밍이다.
에러 줄을 세는 일은 한 줄씩 보면 충분하므로 스트리밍이 맞다.
근거: 2-summary 「동작 방식 (3)」, 「동작 방식 (8)」, 「언제 쓰고 언제 안 쓰나」.

### 9. `?` 는 멈추고 에러를 전파하고, `filter_map(ok)` 는 그 줄을 말없이 버린다

`lines()` 의 각 항목은 `io::Result<String>` 이다.
`let line = line?;` 은 `Err` 를 만나면 함수를 끝내고 에러를 호출자에게 넘긴다.
`filter_map(|line| line.ok())` 는 `Err` 를 `None` 으로 바꿔 걸러 내므로, 에러가 난 줄은 결과에서 조용히 빠진다.
몇 줄 빠져도 되는 훑기에는 뒤쪽이, 빠지면 안 되는 처리에는 앞쪽이 맞다.
근거: 2-summary 「동작 방식 (3)」, 「동작 방식 (7)」, 「어디서 틀리나 5」.

## 실습 정답

### 실습 1. 버퍼링된 쓰기 · 읽기 일곱 가지를 한 프로그램에 모으기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 디렉터리 만들기 | `fs::create_dir_all(dir)?` |
| 2. 100줄 쓰고 직접 flush | `File::create(&path)?` · `BufWriter::new(file)` · `for i in 1..=100` 의 `writeln!` · `writer.flush()?` |
| 3. 64KB 버퍼로 1000줄 | `BufWriter::with_capacity(64 * 1024, file)` · `for i in 0..1000` · `writer.flush()?` |
| 4. 처음 5줄 | `BufReader::new(file)` · `reader.lines().enumerate()` · `let line = line?;` · `if i >= 5 { break; }` |
| 5. `read_line` 두 번 | `let mut line = String::new()` · `reader.read_line(&mut line)?` · `line.trim()` · `line.clear()` |
| 6. `split` 조각 세기 | `reader.split(b'\n')` · `count += 1` · `if count <= 3` · `String::from_utf8_lossy(&segment)` |
| 7. `read_until` | `reader.read_until(b':', &mut buf)?` |
| 8. 성능 비교 표 | `=== 성능 비교 ===` 아래 `println!` 들 |
| 9. 64바이트 청크 | `let mut buffer = [0u8; 64]` · `loop` 의 `reader.read(&mut buffer)?` · `if bytes_read == 0 { break; }` |
| 10. 로그 쓰기와 에러 거르기 | `BufWriter::new(File::create(&log_path)?)` · 여섯 `writeln!` · `reader.lines().filter_map(\|line\| line.ok()).filter(\|line\| line.starts_with("[ERROR]")).collect()` |
| 11. 정리와 반환형 | `fs::remove_dir_all(dir)?` · `fn main() -> io::Result<()>` · `Ok(())` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`rust/rust-io/reference/bufread-bufwrite.rs`

```rust
// [입출력 & 직렬화] BufReader & BufWriter
// 설명: BufReader, BufWriter, lines(), 성능 차이, 대용량 파일 처리
// 팁: BufReader/BufWriter는 시스템 콜 횟수를 줄여 I/O 성능을 크게 향상시킨다. lines()는 줄 단위 스트리밍으로 메모리 효율적이다. read_line 재사용시 반드시 clear()를 호출해야 한다. 대용량 파일은 항상 BufReader를 쓰자.

// fs: 파일시스템 함수, File: 파일 핸들
use std::fs::{self, File};
// BufRead: 줄/구분자 단위 읽기 트레이트, BufReader/BufWriter: 버퍼링 어댑터
// Read/Write: 저수준 바이트 I/O 트레이트
use std::io::{self, BufRead, BufReader, BufWriter, Read, Write};

fn main() -> io::Result<()> {
    // 데모용 임시 디렉토리
    let dir = "/tmp/rust_buf_demo";
    // 부모까지 한 번에 생성. 이미 있어도 에러 없음
    fs::create_dir_all(dir)?;

    // === 1. BufWriter: 버퍼링된 쓰기 ===
    println!("=== BufWriter ===");
    // 출력 파일 경로 (포맷 매크로로 합성)
    let path = format!("{}/buffered.txt", dir);
    {
        // 파일 생성 (있으면 덮어씀)
        let file = File::create(&path)?;
        // 기본 버퍼 크기: 8KB (BufWriter::new)
        // BufWriter: 매 write를 시스콜로 보내지 않고 메모리에 모았다가 한 번에 flush
        let mut writer = BufWriter::new(file);

        // 100줄 작성
        for i in 1..=100 {
            // writeln!: write_fmt + 개행. 끝에 \n 자동 추가
            writeln!(writer, "라인 {:04}: 데이터_{}", i, i * 7)?;
        }
        // 명시적 flush. Drop 시점에도 flush되지만 에러를 잡으려면 직접 호출
        writer.flush()?; // 남은 버퍼 강제 쓰기
    }
    println!("100줄 쓰기 완료: {}", path);

    // 커스텀 버퍼 크기
    // 큰 버퍼는 시스콜 빈도를 더 줄이지만 메모리 사용량은 증가
    let path2 = format!("{}/large_buf.txt", dir);
    {
        let file = File::create(&path2)?;
        // with_capacity로 명시적으로 64KB 버퍼 지정
        let mut writer = BufWriter::with_capacity(64 * 1024, file); // 64KB 버퍼
        for i in 0..1000 {
            writeln!(writer, "big data line {}", i)?;
        }
        writer.flush()?;
    }
    println!("64KB 버퍼로 1000줄 쓰기 완료");

    // === 2. BufReader: 버퍼링된 읽기 ===
    println!("\n=== BufReader ===");

    // lines(): 줄 단위 이터레이터 (가장 일반적)
    {
        // 읽기 모드로 파일 열기
        let file = File::open(&path)?;
        // 8KB 버퍼로 감싸기. 한 시스콜로 큰 덩어리를 읽고 메모리에서 줄 분리
        let reader = BufReader::new(file);

        println!("처음 5줄:");
        // lines(): Iterator<Item = io::Result<String>>. 줄바꿈 자동 제거
        for (i, line) in reader.lines().enumerate() {
            // 각 줄은 io::Result라 ?로 에러 전파
            let line = line?;
            if i >= 5 { break; }
            println!("  {}", line);
        }
    }

    // read_line: 한 줄씩 수동 읽기
    println!("\nread_line:");
    {
        let file = File::open(&path)?;
        let mut reader = BufReader::new(file);
        // 줄을 누적할 가변 String
        let mut line = String::new();

        // 첫 줄 읽기
        // read_line: 줄바꿈 포함하여 String에 추가. 읽은 바이트 수 반환
        let bytes_read = reader.read_line(&mut line)?;
        println!("  읽은 바이트: {}, 내용: {:?}", bytes_read, line.trim());

        // 핵심: 재사용 전 반드시 clear() — 그렇지 않으면 이전 줄 뒤에 덧붙여짐
        line.clear(); // 재사용시 반드시 clear!
        reader.read_line(&mut line)?;
        println!("  두 번째 줄: {:?}", line.trim());
    }

    // === 3. split: 특정 바이트로 분할 ===
    println!("\n=== split ===");
    {
        let file = File::open(&path)?;
        let reader = BufReader::new(file);

        // '\n' (0x0A) 기준 분할
        // split(byte): 구분 바이트 기준으로 Vec<u8> 이터레이터 (구분자 미포함)
        let mut count = 0;
        for segment in reader.split(b'\n') {
            let segment = segment?;
            count += 1;
            if count <= 3 {
                // 바이트를 UTF-8로 해석 (실패 시 대체 문자)
                println!("  세그먼트 {}: {:?}", count,
                    String::from_utf8_lossy(&segment));
            }
        }
        println!("  총 세그먼트 수: {}", count);
    }

    // === 4. read_until: 구분자까지 읽기 ===
    println!("\n=== read_until ===");
    {
        let file = File::open(&path)?;
        let mut reader = BufReader::new(file);
        // 누적용 바이트 버퍼
        let mut buf = Vec::new();

        // ':' 까지 읽기
        // read_until: 구분 바이트를 만날 때까지(포함) 읽어서 buf에 붙임
        let bytes = reader.read_until(b':', &mut buf)?;
        println!("  ':' 까지: {} bytes -> {:?}",
            bytes, String::from_utf8_lossy(&buf));
    }

    // === 5. 성능 비교 설명 ===
    println!("\n=== 성능 비교 ===");
    // 시각적 비교 표
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

    // === 6. 청크 단위 읽기 (바이너리 안전) ===
    println!("\n=== 청크 단위 읽기 ===");
    {
        let file = File::open(&path)?;
        let mut reader = BufReader::new(file);
        // 64바이트 고정 청크. 텍스트가 아닌 바이너리도 안전
        let mut buffer = [0u8; 64]; // 64바이트 청크
        let mut total_bytes = 0;
        let mut chunk_count = 0;

        // EOF까지 반복
        loop {
            // read: 0~buffer.len() 사이 읽음. 0이면 EOF
            let bytes_read = reader.read(&mut buffer)?;
            if bytes_read == 0 { break; } // EOF
            total_bytes += bytes_read;
            chunk_count += 1;
        }
        println!("  총 {}바이트, {}개 청크로 읽음", total_bytes, chunk_count);
    }

    // === 7. 파일 처리 실용 패턴 ===
    println!("\n=== 실용: 로그 파일 분석 ===");
    // 로그 파일 생성
    let log_path = format!("{}/app.log", dir);
    {
        // 한 번에 묶어 쓰기 위해 BufWriter 사용
        let mut writer = BufWriter::new(File::create(&log_path)?);
        writeln!(writer, "[INFO] 서버 시작")?;
        writeln!(writer, "[ERROR] DB 연결 실패")?;
        writeln!(writer, "[INFO] 재연결 성공")?;
        writeln!(writer, "[WARN] 메모리 사용량 높음")?;
        writeln!(writer, "[ERROR] 타임아웃")?;
        writeln!(writer, "[INFO] 요청 처리 완료")?;
        writer.flush()?;
    }

    // 에러 라인만 추출
    // 줄 단위 스트리밍 + 이터레이터 어댑터로 필터링
    let file = File::open(&log_path)?;
    let reader = BufReader::new(file);
    let errors: Vec<String> = reader.lines()
        // 에러난 줄은 버리고 Ok만 통과
        .filter_map(|line| line.ok())
        // [ERROR] 접두사로 필터
        .filter(|line| line.starts_with("[ERROR]"))
        .collect();
    println!("에러 로그:");
    for err in &errors {
        println!("  {}", err);
    }
    println!("에러 수: {}", errors.len());

    // 정리
    // 디렉토리 트리 통째 삭제
    fs::remove_dir_all(dir)?;
    println!("\n정리 완료");

    Ok(())
}
```

**실행 결과** — 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다).

**풀이 요점**
- `BufWriter` 를 쓰는 블록마다 끝에 `flush()?` 를 직접 불러 쓰기 에러를 놓치지 않는다.
- `lines()` · `split` 은 구분자를 빼고, `read_line` · `read_until` 은 구분자를 넣고 덧붙인다 — 재사용 전 `clear()`.
- 블록 `{ … }` 으로 파일 핸들의 수명을 짧게 잡아, 같은 파일을 다시 여는 다음 단계와 겹치지 않게 한다.
- 청크 읽기의 끝은 `read` 가 `0` 을 돌려줄 때뿐이다.
- 로그 필터는 이터레이터 어댑터를 이어 붙인 스트리밍이라, 걸러진 결과만 메모리에 남는다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
