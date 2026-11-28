# rust/rust-io/02 — BufReader & BufWriter — 정리 (힌트)

> 출처 — study-site 항목 `rust/bufread-bufwrite`(항목 데이터 `data/rust/io-serde.json`) · 정답 코드 study-practice `rust/rust-io/reference/bufread-bufwrite.rs`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다).

## 한눈에 — 쉽게 말하면

**`BufReader` · `BufWriter` 는 「장바구니」다.**
마트에서 물건 하나를 살 때마다 계산대에 줄을 서면 하루가 다 간다.
장바구니에 모았다가 계산대에 한 번 가면 줄 서는 횟수가 확 준다.
파일 입출력도 똑같은 구조다.
`File` 에 직접 쓰고 읽으면 호출마다 운영체제에 부탁(시스템 콜)을 한다.
`BufWriter` 는 쓸 것을 메모리에 모았다가 한꺼번에 넘긴다.
`BufReader` 는 큰 덩어리를 한 번에 받아 두고 거기서 조금씩 꺼내 준다.

> **시스템 콜** — 프로그램이 파일 · 네트워크 같은 일을 운영체제에 맡기는 호출이다. 일반 함수 호출보다 비싸다.\
> 예: `File::read()` 를 한 번 부르면 운영체제의 읽기 호출이 한 번 일어난다.

> **버퍼** — 데이터를 잠시 모아 두는 메모리 영역이다.\
> 예: `BufWriter::new` 가 만드는 기본 8KB 공간.

| 비유 | 실체 |
|---|---|
| 물건 하나 | `writeln!` 한 번, 줄 하나 |
| 장바구니 | 버퍼(기본 8KB) |
| 계산대에 가기 | 시스템 콜 |
| 장바구니 비우고 계산 | `flush()` |
| 장바구니 크기 | `with_capacity(64 * 1024, …)` |

```text
버퍼 없이:  write → 시스콜 │ write → 시스콜 │ write → 시스콜 …   (100줄 = 100번)

BufWriter:  write ┐
            write ├─▶ [ 메모리 버퍼 ] ──(가득 차거나 flush)──▶ 시스콜 1번
            write ┘
```

## 이 주제가 답하려는 질문

1. 파일을 줄마다 읽고 쓸 때 왜 `File` 을 그대로 쓰지 않고 버퍼로 감싸는가?
2. 버퍼에 남은 데이터는 언제 파일로 가고, 쓰기 에러는 어디서 잡는가?
3. 줄 · 구분 바이트 · 고정 크기 청크로 나눠 읽는 방법은 각각 무엇이고 무엇을 돌려주는가?
4. 큰 파일을 메모리에 다 올리지 않고 처리하려면 어떻게 하는가?

## 동작 방식

### (1) `BufWriter` — 모았다가 한 번에 쓴다

**언제 쓰나** — 작은 쓰기를 여러 번 할 때 쓴다.
줄 100개를 `writeln!` 으로 하나씩 쓰는 경우가 전형이다.

```text
File::create(path)  ──▶  BufWriter::new(file)          (기본 버퍼 8KB)
writeln!(writer, …) ×100 ──▶ 버퍼에 차곡차곡 쌓임         (시스콜 없음)
버퍼가 가득 참      ──▶ 그때 한 번 파일로 보냄
writer.flush()?    ──▶ 남은 것을 강제로 보냄             → 파일에 100줄 완성
```

- `File::create` 는 파일을 만들고, 이미 있으면 내용을 비우고 덮어쓴다.
- `BufWriter::new(file)` 는 파일 핸들을 기본 8KB 버퍼로 감싼다.
- `writeln!` 은 서식을 적용해 쓰고 끝에 `\n` 을 붙인다. 이 데이터는 일단 버퍼로만 간다.
- 버퍼가 차면 그때 파일로 내보낸다.
- 마지막에 `flush()` 가 아직 버퍼에 남은 부분을 파일로 밀어낸다.

`BufWriter::with_capacity(64 * 1024, file)` 로 버퍼 크기를 직접 정할 수 있다.
버퍼가 크면 시스템 콜이 더 드물어지지만 메모리를 그만큼 더 쓴다.

> **flush** — 버퍼에 남은 데이터를 실제 목적지로 강제로 내보내는 일이다.\
> 예: `writer.flush()?;` 로 마지막 몇 줄까지 파일에 쓴다.

### (2) `flush` 와 `Drop` — 에러를 잡으려면 직접 부른다

**언제 쓰나** — `BufWriter` 를 다 쓰고 나서 언제나 쓴다.

```text
{                                   
    let mut writer = BufWriter::new(file);
    writeln!(writer, …)?;           
    writer.flush()?;      ──▶ 실패하면 Err 가 ? 로 위로 전파됨
}                         ──▶ 블록 끝: writer 가 버려짐(Drop) → 남은 게 있으면 여기서도 flush
                              하지만 이때 난 에러는 받을 곳이 없다
```

- 블록 `{ … }` 이 끝나면 `writer` 가 버려지고(`Drop`), 이때도 버퍼가 비워진다.
- 그런데 `Drop` 은 값을 돌려줄 수 없어서 그때 난 쓰기 에러를 호출자가 받지 못한다.
- 그래서 에러를 잡으려면 `flush()?` 를 직접 부른다.
- 블록은 파일 핸들을 일찍 닫아, 뒤에서 같은 파일을 다시 여는 코드와 섞이지 않게 해 준다.

> **Drop** — 값이 범위를 벗어날 때 자동으로 실행되는 정리 단계다.\
> 예: `}` 에서 `BufWriter` 가 사라지며 버퍼를 비우고 파일을 닫는다.

### (3) `BufReader` + `lines()` — 줄 단위 스트리밍

**언제 쓰나** — 텍스트 파일을 줄마다 처리할 때 쓴다. 가장 흔한 읽기 방식이다.

```text
File::open(path) ──▶ BufReader::new(file)
                      │ 시스콜 1번으로 큰 덩어리(최대 8KB)를 버퍼에 받음
                      ▼
reader.lines()   ──▶ 버퍼 안에서 '\n' 을 찾아 줄을 잘라 냄
                      Item = io::Result<String>   (줄바꿈은 빠짐)
                      ▼
for (i, line) in … .enumerate() { let line = line?; if i >= 5 { break; } … }
                 ──▶ 처음 5줄만 출력하고 멈춤
```

- `File::open` 은 읽기용으로 연다.
- `BufReader::new` 가 한 번의 시스템 콜로 큰 덩어리를 읽어 두고 메모리에서 줄을 나눈다.
- `lines()` 는 `io::Result<String>` 을 내놓는 이터레이터다. 각 줄 끝의 줄바꿈은 지워진다.
- 줄마다 `Result` 라서 `line?` 로 에러를 위로 넘긴다.
- 한 번에 한 줄만 메모리에 들고 있으므로 파일 전체를 올리지 않는다. 이것이 「스트리밍」이다.
- 위 코드에서는 `line?` 를 먼저 하고 `i >= 5` 를 검사하므로, 멈추기 전에 6번째 줄까지는 읽힌다(출력은 5줄).

> **스트리밍** — 데이터를 통째로 메모리에 올리지 않고 조금씩 흘려 가며 처리하는 방식이다.\
> 예: 10GB 로그를 `lines()` 로 한 줄씩 훑는다.

### (4) `read_line` — 붙여 넣는 읽기

**언제 쓰나** — 줄 하나씩 직접 제어하며 읽을 때, `String` 하나를 다시 써서 할당을 아끼고 싶을 때 쓴다.

```text
let mut line = String::new();          line = ""
reader.read_line(&mut line)?   ──▶   line = "라인 0001: 데이터_7\n"   반환값 = 읽은 바이트 수
line.clear();                  ──▶   line = ""
reader.read_line(&mut line)?   ──▶   line = "라인 0002: 데이터_14\n"
```

- `read_line` 은 줄바꿈까지 **포함해** 읽은 내용을 `String` 의 끝에 **덧붙인다**.
- 돌려주는 값은 이번에 읽은 바이트 수다.
- 덧붙이기 때문에 같은 `String` 을 다시 쓰려면 반드시 먼저 `clear()` 를 부른다.
- `clear()` 를 빼먹으면 앞 줄 뒤에 새 줄이 이어 붙는다.
- `line.trim()` 은 양 끝의 공백 · 줄바꿈만 지운다. 가운데의 `\n` 은 남는다.
- `{:?}` 로 찍으면 문자열이 따옴표로 감싸이고 `\n` 은 `\n` 글자로 이스케이프되어 보인다.

### (5) `split` 과 `read_until` — 바이트 구분자로 자르기

**언제 쓰나** — 줄바꿈이 아닌 다른 바이트(`:` 등)로 나눌 때, 또는 UTF-8 이 아닐 수도 있는 데이터를 바이트로 다룰 때 쓴다.

```text
첫 줄 바이트:  라 인 ␠ 0 0 0 1 : ␠ 데 이 터 _ 7 \n

reader.read_until(b':', &mut buf)   ──▶ buf = "라인 0001:"     (구분자 포함)
reader.split(b'\n')                 ──▶ Vec<u8> 조각들          (구분자 미포함)
                                        "라인 0001: 데이터_7", "라인 0002: 데이터_14", …
```

- `split(b'\n')` 은 구분 바이트로 나눈 `Vec<u8>` 조각을 차례로 내놓는다. 조각에는 구분자가 들어가지 않는다.
- 조각도 `io::Result` 라서 `segment?` 로 꺼낸다.
- `read_until(b':', &mut buf)` 은 구분 바이트를 만날 때까지 읽어 `buf` 에 붙인다. 구분자도 **포함한다**.
- `read_until` 이 돌려주는 값은 읽은 바이트 수다.
- `String::from_utf8_lossy(&bytes)` 는 바이트를 UTF-8 로 해석하고, 해석할 수 없는 부분은 대체 문자로 바꾼다.

### (6) `read` — 고정 크기 청크로 읽기

**언제 쓰나** — 줄 개념이 없는 바이너리 파일을 읽을 때, 전체 크기만 세거나 덩어리째 옮길 때 쓴다.

```text
let mut buffer = [0u8; 64];
loop {
    n = reader.read(&mut buffer)?   ──▶ 0 ~ 64 바이트가 buffer 앞쪽에 채워짐
    n == 0 이면 break               ──▶ 파일 끝(EOF)
    total += n; chunks += 1
}
```

- `read` 는 `0` 부터 `buffer.len()` 사이의 바이트 수를 읽고 그 수를 돌려준다.
- `0` 이 돌아오면 파일 끝(EOF)이다.
- 줄이나 문자를 해석하지 않으므로 바이너리에도 안전하다.
- 64보다 적게 돌아왔다고 해서 끝이라는 뜻은 아니다. 끝은 오직 `0` 이다.

> **EOF** — End Of File, 더 읽을 데이터가 없는 상태다.\
> 예: `reader.read(&mut buffer)?` 가 `0` 을 돌려준다.

### (7) 이터레이터로 거르기 — 로그 분석

**언제 쓰나** — 큰 텍스트 파일에서 조건에 맞는 줄만 골라낼 때 쓴다.

```text
app.log ──▶ reader.lines()                   io::Result<String> 6개
        ──▶ .filter_map(|line| line.ok())    Ok 만 통과 (Err 는 조용히 버림)
        ──▶ .filter(|l| l.starts_with("[ERROR]"))
        ──▶ .collect::<Vec<String>>()        조건에 맞는 줄만, 원래 차례대로
```

- `lines()` 가 줄을 하나씩 흘려보낸다.
- `filter_map(|line| line.ok())` 는 `Ok` 인 줄만 꺼내고 `Err` 는 버린다.
- `filter(… starts_with("[ERROR]"))` 는 그 접두사로 시작하는 줄만 남긴다.
- `collect()` 가 남은 줄을 원래 차례대로 `Vec<String>` 에 담는다.
- 걸러진 결과만 메모리에 남고 파일 전체는 올라오지 않는다.

### (8) 네 가지 읽기 방식 비교

| 방법 | 특성 |
|---|---|
| `fs::read_to_string()` | 전체를 메모리에 로드 |
| `BufReader` + `lines()` | 줄 단위 스트리밍 |
| `BufReader` + `read()` | 청크 단위 스트리밍 |
| `File::read()` 직접 | 매 호출마다 시스콜 |

- `BufReader` · `BufWriter` 는 시스템 콜 횟수를 줄여 성능을 높인다.
- `File` 을 직접 쓰며 1바이트씩 `read` 하면 1바이트마다 시스템 콜이 일어나 매우 느리다.

## 문법 — 형태와 규칙

```rust
use std::fs::File;
use std::io::{self, BufRead, BufReader, BufWriter, Write};

fn copy_upper(src: &str, dst: &str) -> io::Result<()> {
    let reader = BufReader::new(File::open(src)?);
    let mut writer = BufWriter::new(File::create(dst)?);
    for line in reader.lines() {
        let line = line?;                       // 줄바꿈 없는 String
        writeln!(writer, "{}", line.to_uppercase())?;
    }
    writer.flush()?;                            // 에러를 여기서 받는다
    Ok(())
}
```

- 줄 · 구분자 메서드(`lines` · `read_line` · `split` · `read_until`)를 쓰려면 `BufRead` 트레이트를 `use` 한다.
- `read` 를 쓰려면 `Read`, `writeln!` · `flush` 를 쓰려면 `Write` 를 `use` 한다.
- 만들기: `BufReader::new(file)` · `BufWriter::new(file)` 는 기본 8KB 버퍼, `with_capacity(크기, file)` 는 크기를 직접 정한다.
- 거의 모든 호출이 `io::Result` 를 돌려주므로 `main` 을 `fn main() -> io::Result<()>` 로 두고 `?` 로 전파한다.
- `fs::create_dir_all(dir)` 은 부모 디렉터리까지 한꺼번에 만들고, 이미 있어도 에러가 아니다.
- `fs::remove_dir_all(dir)` 은 디렉터리 트리를 통째로 지운다.

| 메서드 | 단위 | 구분자 포함? | 돌려주는 것 |
|---|---|---|---|
| `lines()` | 줄 | 아니오(줄바꿈 제거) | `io::Result<String>` 이터레이터 |
| `read_line(&mut s)` | 줄 | 예(`\n` 포함, 덧붙임) | 읽은 바이트 수 |
| `split(b)` | 구분 바이트 | 아니오 | `io::Result<Vec<u8>>` 이터레이터 |
| `read_until(b, &mut v)` | 구분 바이트 | 예(덧붙임) | 읽은 바이트 수 |
| `read(&mut buf)` | 최대 `buf.len()` 바이트 | 해당 없음 | 읽은 바이트 수, `0` 이면 EOF |

## 어디서 틀리나

### 1. `read_line` 을 다시 쓰면서 `clear()` 를 빼먹는다
`read_line` 은 덮어쓰지 않고 덧붙인다.
`clear()` 없이 반복하면 `String` 에 지금까지 읽은 모든 줄이 쌓인다.
재사용할 때는 매번 `clear()` 를 부른다.

### 2. `flush()` 를 `Drop` 에 맡긴다
`Drop` 에서도 버퍼는 비워지지만, 그때 난 쓰기 에러는 받을 곳이 없다.
디스크가 가득 차는 등의 실패를 놓치지 않으려면 직접 `flush()?` 를 부른다.

### 3. `lines()` 와 `read_line` 의 줄바꿈을 섞어 생각한다
`lines()` 는 줄바꿈을 지우고, `read_line` 은 남긴다.
`read_line` 결과를 비교하거나 출력할 때는 `trim()` 등으로 끝을 다듬는다.

### 4. `read` 가 버퍼를 다 채운다고 믿는다
`read` 는 0 ~ `buffer.len()` 사이 어느 만큼이든 돌려줄 수 있다.
반드시 돌려받은 수 `n` 만큼만 `buffer[..n]` 을 쓰고, 끝은 `n == 0` 으로만 판단한다.

### 5. 에러를 조용히 삼킨다
`filter_map(|line| line.ok())` 는 읽기 에러가 난 줄을 말없이 버린다.
로그 훑기처럼 몇 줄 빠져도 되는 경우에만 쓰고, 빠지면 안 되는 처리에는 `line?` 로 전파한다.

### 6. 「대용량 파일은 항상 `BufReader`」를 문자 그대로 따른다
원본의 주장: 대용량 파일은 항상 `BufReader` 를 쓰자.
의심스러운 점: `BufReader` 의 이득은 작은 읽기를 여러 번 할 때 시스템 콜을 줄이는 데서 온다.
이미 큰 덩어리로 한 번에 읽는 코드라면 버퍼가 끼어들어도 얻는 것이 적다.
줄 · 구분자 단위로 읽는다면 `BufRead` 가 필요하므로 그때는 거의 언제나 맞는 선택이다.

### 7. 「매우 느림」「크게 향상」을 수치로 받아들인다
원본은 성능 차이를 말로만 설명한다.
얼마나 빨라지는지는 파일 크기 · 읽기 크기 · 운영체제에 따라 다르다(확인 필요).

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `BufReader::new` · `BufWriter::new` 의 기본 버퍼가 8KB 다 | 표준 라이브러리의 현재 구현값이다. 바뀔 수 있다(확인 필요) |
| `read` 가 `0` 을 돌려주면 EOF 다 | `Read` 트레이트의 계약(표준 라이브러리 문서) |
| `lines()` 는 줄바꿈을 지우고 `read_line` 은 남긴다 | `BufRead` 의 문서화된 동작 |
| `BufWriter` 는 `Drop` 때 버퍼를 비우지만 에러는 전달하지 못한다 | `BufWriter` 의 문서화된 동작 |
| `File::read` 한 번이 시스템 콜 한 번이다 | 표준 라이브러리 구현과 운영체제. 언어가 보장하는 것은 아니다 |
| `/tmp/rust_buf_demo` 경로를 쓸 수 있다 | 유닉스 계열 운영체제의 관례. 다른 운영체제에서는 다르다 |
| 버퍼가 시스템 콜을 줄여 빨라진다 | 일반적인 경향이다. 얼마나 빨라지는지는 보장되지 않는다 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 줄 단위로 큰 텍스트 처리 | `BufReader` + `lines()` | `fs::read_to_string()` 으로 전부 올리기 |
| 작은 쓰기를 여러 번 | `BufWriter` + 끝에 `flush()?` | `File` 에 `writeln!` 직접 반복 |
| `String` 하나를 재사용하며 줄 읽기 | `read_line` + 매번 `clear()` | `clear()` 없는 반복 |
| `:` · `,` 같은 바이트로 자르기 | `split` · `read_until` | 줄로 읽어 다시 쪼개기(줄바꿈이 없는 데이터) |
| 바이너리 · 크기 세기 | `read` 로 청크 읽기 | `lines()`(UTF-8 이 아니면 에러) |
| 작은 설정 파일 하나 통째로 | `fs::read_to_string()` | 굳이 줄마다 스트리밍 |

## 핵심 문장

1. **`BufReader` · `BufWriter` 는 메모리 버퍼로 시스템 콜 횟수를 줄인다** — 작은 읽기 · 쓰기가 많을수록 효과가 크다.
2. **`BufWriter` 는 끝에 `flush()?` 를 직접 부른다** — `Drop` 의 flush 는 에러를 알려 주지 못한다.
3. **`lines()` 는 줄을 하나씩 흘려 메모리를 아낀다** — 각 줄은 `io::Result<String>`, 줄바꿈은 빠진다.
4. **`read_line` · `read_until` 은 덧붙인다** — 버퍼를 다시 쓰려면 `clear()` 부터.
5. **`read` 의 끝은 `0`** — 돌려받은 수만큼만 유효하다.

## 관련 자료

- `file-read-write` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- [stdin-stdout](../05-stdin-stdout/2-summary.md)
- `error-io` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/rust/io-serde.json` 의 `bufread-bufwrite`

## 용어 풀이

- **시스템 콜** — 프로그램이 운영체제에 일을 맡기는 호출. 비싸다.
- **버퍼** — 데이터를 잠시 모아 두는 메모리 영역.
- **`BufReader`** — 읽기 핸들을 버퍼로 감싸 큰 덩어리로 읽어 두는 어댑터.
- **`BufWriter`** — 쓰기 핸들을 버퍼로 감싸 모았다가 한꺼번에 쓰는 어댑터.
- **`BufRead`** — `lines` · `read_line` · `split` · `read_until` 을 주는 트레이트.
- **`Read` / `Write`** — 바이트 단위 읽기 · 쓰기 트레이트.
- **flush** — 버퍼에 남은 데이터를 목적지로 강제로 내보내는 일.
- **Drop** — 값이 범위를 벗어날 때 자동으로 실행되는 정리.
- **스트리밍** — 통째로 올리지 않고 조금씩 처리하는 방식.
- **청크** — 한 번에 읽는 고정 크기의 덩어리.
- **EOF** — 더 읽을 데이터가 없는 상태.
- **`from_utf8_lossy`** — 바이트를 UTF-8 로 해석하고 깨진 부분은 대체 문자로 바꾸는 함수.

## 더 들어가면

- `BufWriter::into_inner()` 는 버퍼를 비운 뒤 안쪽 `File` 을 돌려주며, 비우기 실패를 에러로 알려 준다(확인 필요).
- `lines()` 는 `\r\n` 으로 끝나는 줄에서 `\r` 까지 지운다고 문서에 적혀 있다(확인 필요).
- 요청한 읽기 크기가 `BufReader` 의 버퍼보다 크고 내부 버퍼가 비어 있으면, 내부 버퍼를 거치지 않고 바로 읽는다(확인 필요).
- 표준 출력도 버퍼링된다. 많은 줄을 찍을 때 `io::stdout().lock()` 을 `BufWriter` 로 감싸는 방법이 쓰인다(확인 필요).
- `lines()` 는 줄마다 새 `String` 을 할당한다. 할당을 아끼려면 `read_line` + `clear()` 로 하나를 재사용한다(확인 필요).
