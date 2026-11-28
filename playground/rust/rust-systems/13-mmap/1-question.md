# rust/rust-systems/13 — 메모리 매핑 파일 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 오프셋 0 에서 50바이트를 읽어 찍으면 (예측)

```rust
// 질문용 발췌 — 파일은 "Line {i}: Hello, memory-mapped world! ABCDEF\n" 이 i=0..1000 으로 이어진 것
let data = read_at_offset(test_path, 0, 50)?;
println!("처음 50바이트: {}", String::from_utf8_lossy(&data));
```

- 화면에 무엇이 몇 줄로 찍히나?

### 2. 오프셋 100 에서 30바이트를 읽어 찍으면 (예측)

```rust
// 질문용 발췌 — 같은 파일
let data2 = read_at_offset(test_path, 100, 30)?;
println!("100~130 바이트: {}", String::from_utf8_lossy(&data2));
```

- 30바이트는 어느 줄의 어디부터 어디까지이고, 화면에는 어떻게 찍히나?

### 3. `ABCDEF` 를 찾아 개수와 처음 세 위치를 찍으면 (예측)

```rust
// 질문용 발췌 — 같은 파일
let positions = search_in_file(test_path, b"ABCDEF")?;
println!("'ABCDEF' 발견 위치: {} 곳", positions.len());
if positions.len() > 3 {
    println!("처음 3개: {:?}", &positions[..3]);
}
```

- 개수와 처음 세 위치는 무엇인가?

### 4. 빈도를 셀 때 `&buffer[..n]` 만 도는 까닭 (왜)

- `count_bytes_regular` 가 버퍼 전체가 아니라 `&buffer[..n]` 만 세는 까닭은 무엇인가?

### 5. `Mmap::map()` 이 `unsafe` 인 까닭 (왜)

- 파일을 읽기 전용으로 매핑할 뿐인데 왜 `unsafe` 블록이 필요한가?

### 6. 파일이 패턴으로 딱 끝날 때 (경계)

- 파일 내용이 `"xxABCDEF"`(줄바꿈 없음)일 때 `search_in_file(path, b"ABCDEF")` 는 위치 2 를 찾아내나?

### 7. mmap 의 이득이 작은 자리 (경계)

- 파일을 처음부터 끝까지 한 번 읽거나 파일이 작을 때, mmap 이 일반 I/O 보다 낫지 않은 까닭은 무엇인가?

### 8. `seek` + `read` 와 슬라이스 인덱싱 (연결)

- `read_at_offset` 의 `seek` · `read` · `truncate` 세 단계는 mmap 에서 무엇으로 바뀌고, 그때 사라지는 일은 무엇인가?

### 9. `Result` 와 SIGBUS (연결)

- 일반 I/O 에서 `?` 로 처리하던 읽기 오류가 mmap 에서는 왜 `?` 로 잡히지 않을 수 있나?

## 실습

### 실습 1. 일반 I/O 로 mmap 이 할 일을 흉내 내기

**만들 것** — 테스트 파일을 만들고, 일반 I/O 로 바이트 빈도 · 오프셋 읽기 · 패턴 검색을 한 뒤, `memmap2` 사용 패턴과 mmap 의 장단점을 찍는 프로그램.

**준비물** — Rust 표준 라이브러리만 쓴다. `memmap2` 크레이트는 필요 없다 — 사용법은 문자열로만 찍어 흉내 낸다.

**요구 조건**

1단계 — 테스트 파일
1. `/tmp/rust_mmap_test.txt` 를 만들고 `i = 0..1000` 동안 `"Line {i}: Hello, memory-mapped world! ABCDEF"` 를 한 줄씩 쓴다.
2. 쓰기용 파일은 블록 안에서 만들어 블록이 끝날 때 닫히게 한다.
3. `fs::metadata` 로 파일 크기를 구해 찍는다.

2단계 — `count_bytes_regular`
4. 파일을 열고 8192바이트 스택 배열을 버퍼로 쓴다.
5. `read` 를 반복하고, 0 을 받으면 멈춘다.
6. 실제로 읽은 `n` 바이트만 256칸 `u64` 빈도 배열에 누적해 돌려준다.
7. `main` 에서 `'H'` · `'\n'` · `'A'` 의 빈도를 찍는다.

3단계 — `read_at_offset`
8. 파일 시작에서 `offset` 바이트로 `seek` 한다.
9. `len` 크기의 `Vec<u8>` 에 `read` 하고, 실제로 읽은 길이로 `truncate` 해 돌려준다.
10. `main` 에서 (0, 50) 과 (100, 30) 을 읽어 `String::from_utf8_lossy` 로 찍는다.

4단계 — `search_in_file`
11. `fs::read` 로 파일 전체를 읽는다.
12. `saturating_sub` 로 반복 범위를 정하고, 위치마다 패턴 길이의 슬라이스를 패턴과 비교해 맞는 위치(`u64`)를 모은다.
13. `main` 에서 `b"ABCDEF"` 의 발견 개수를 찍고, 3개보다 많으면 처음 3개를 `{:?}` 로 찍는다.

5단계 — 마무리
14. 시작 코드에 채워 둔 `memmap2` 사용 패턴 문자열과 mmap 장단점 목록을 찍는다.
15. 테스트 파일을 지우고 `Ok(())` 로 끝낸다.

**시작 코드**

```rust
use std::io::{Read, Write, Seek, SeekFrom};
use std::fs;

/// 대용량 파일에서 바이트 빈도 분석 (일반 I/O)
fn count_bytes_regular(path: &str) -> std::io::Result<[u64; 256]> {
    let mut file = fs::File::open(path)?;
    // TODO: 8KB 스택 버퍼와 256칸 빈도 배열
    // TODO: read 를 반복, 0 이면 멈춤, 읽은 부분만 집계
    todo!()
}

/// 파일의 특정 오프셋 읽기 (random access)
fn read_at_offset(path: &str, offset: u64, len: usize) -> std::io::Result<Vec<u8>> {
    let mut file = fs::File::open(path)?;
    // TODO: 시작 기준으로 offset 만큼 이동
    // TODO: len 크기 버퍼에 read, 읽은 만큼만 남기기
    todo!()
}

/// 파일 내 패턴 검색
fn search_in_file(path: &str, pattern: &[u8]) -> std::io::Result<Vec<u64>> {
    // TODO: 파일 전체를 읽기
    // TODO: 언더플로 없이 범위를 정하고 슬라이스 비교로 위치 모으기
    todo!()
}

fn main() -> std::io::Result<()> {
    let test_path = "/tmp/rust_mmap_test.txt";
    // TODO: 블록 안에서 파일을 만들고 1000줄 쓰기

    // TODO: 파일 크기
    println!("=== 메모리 매핑 파일 ===");

    println!("\n=== 바이트 빈도 분석 (일반 I/O) ===");
    // TODO: 'H', '\n', 'A' 빈도

    println!("\n=== 오프셋 읽기 ===");
    // TODO: (0, 50), (100, 30)

    println!("\n=== 패턴 검색 ===");
    // TODO: b"ABCDEF" 개수와 처음 3개

    println!("\n=== memmap2 사용법 ===");
    println!(r#"// Cargo.toml: memmap2 = "0.9"
use memmap2::{{Mmap, MmapMut}};

// 읽기 전용 매핑
let file = File::open("data.bin")?;
let mmap = unsafe {{ Mmap::map(&file)? }};
// mmap[0..100] 처럼 슬라이스로 접근 (복사 없음!)

// 쓰기 매핑
let file = OpenOptions::new().read(true).write(true).open("data.bin")?;
let mut mmap = unsafe {{ MmapMut::map_mut(&file)? }};
mmap[0] = 42; // 직접 쓰기
mmap.flush()?; // 디스크에 반영"#);

    println!("\n=== mmap vs 일반 I/O ===");
    println!("mmap 장점:");
    println!("  - 커널 ↔ 유저 공간 복사 없음 (zero-copy)");
    println!("  - OS의 페이지 캐시를 활용");
    println!("  - 랜덤 액세스에 매우 효율적");
    println!("  - 여러 프로세스가 같은 매핑 공유 가능");
    println!("mmap 단점:");
    println!("  - 작은 파일에는 오버헤드");
    println!("  - unsafe 필요 (파일이 변경될 수 있음)");
    println!("  - 에러 처리가 SIGBUS/SIGSEGV로 올 수 있음");

    // TODO: 테스트 파일 지우기
    Ok(())
}
```

**확인 방법** — `rustc mmap.rs && ./mmap` 로 돌려, 파일 크기 · 세 빈도 · 두 오프셋 조각 · 패턴 개수와 처음 3개 위치가 2-summary 「동작 방식 (6)」에서 센 값과 맞는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
