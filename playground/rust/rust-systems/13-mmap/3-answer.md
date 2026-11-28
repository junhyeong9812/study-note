# rust/rust-systems/13 — 메모리 매핑 파일 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 두 줄로 찍힌다 — 0번 줄 전체(43바이트)와 1번 줄의 앞 7바이트

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
처음 50바이트: Line 0: Hello, memory-mapped world! ABCDEF
Line 1:
```

**왜 그런가**
0번 줄은 `"Line 0: Hello, memory-mapped world! ABCDEF\n"` 으로 42 + 1 = 43바이트다.
50바이트를 읽으면 그 43바이트에 이어 1번 줄의 앞 7바이트 `"Line 1:"` 가 따라온다.
43바이트째가 줄바꿈이므로 화면에서는 두 줄로 나뉜다.
근거: 2-summary 「동작 방식 (2)」(seek + read) · 「동작 방식 (6)」(줄 길이 42 + d).

### 2. 2번 줄의 14번째 바이트부터 줄 끝까지 29바이트 + 3번 줄의 `L`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
100~130 바이트:  memory-mapped world! ABCDEF
L
```

**왜 그런가**
0~9번 줄은 43바이트씩이라 2번 줄은 오프셋 86 에서, 3번 줄은 129 에서 시작한다.
오프셋 100 은 2번 줄 안의 14번째 자리로, `"Hello,"` 뒤의 공백이다.
그 공백부터 줄 끝 줄바꿈까지 `" memory-mapped world! ABCDEF\n"` 이 29바이트이고, 30번째 바이트는 3번 줄의 첫 글자 `L` 이다.
형식 문자열의 `": "` 뒤 공백과 데이터의 공백이 겹쳐 콜론 뒤에 공백이 둘 찍힌다.
근거: 2-summary 「동작 방식 (2)」 · 「동작 방식 (6)」.

### 3. 1000 곳, 처음 세 위치는 36 · 79 · 122

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
'ABCDEF' 발견 위치: 1000 곳
처음 3개: [36, 79, 122]
```

**왜 그런가**
각 줄에 `ABCDEF` 가 한 번씩 있어 1000줄이면 1000 곳이다.
한 자리 줄에서 `ABCDEF` 는 줄 시작에서 36 에 있고, 줄 시작은 0 · 43 · 86 이므로 36 · 79 · 122 다.
마지막 등장은 파일 끝의 줄바꿈 바로 앞(44890 − 7 = 44883)이라, 반복 범위 `0..44884` 안에 들어 빠지지 않는다.
근거: 2-summary 「동작 방식 (3)」 · 「동작 방식 (6)」 · 「어디서 틀리나 2」.

### 4. `read` 가 버퍼를 다 채운다는 보장이 없고, 뒤쪽에는 이전 청크가 남아 있어서다

`read` 는 최대 8192바이트를 읽고 실제로 읽은 길이 `n` 을 돌려준다.
마지막 청크처럼 `n` 이 8192 보다 작으면 `buffer[n..]` 에는 앞 청크의 바이트가 그대로 남아 있다.
버퍼 전체를 세면 그 바이트가 두 번 세어져 빈도가 틀린다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 1」.

### 5. 다른 프로세스가 파일을 바꾸면 Rust 의 참조 전제가 깨져 UB 가 될 수 있어서다

매핑은 파일을 `&[u8]` 처럼 보이게 하고, Rust 는 공유 참조가 살아 있는 동안 값이 바뀌지 않는다고 전제한다.
그런데 매핑된 파일은 내 프로그램 바깥에서 수정되거나 잘릴 수 있고, 컴파일러는 그것을 막지 못한다.
그래서 「아무도 이 파일을 건드리지 않는다」는 약속을 호출하는 쪽이 `unsafe` 로 진다.
읽기 전용이라는 것은 「내가 쓰지 않는다」일 뿐 「남도 쓰지 않는다」가 아니다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 3」.

### 6. 찾지 못한다 — 범위가 마지막 시작 위치를 빼먹는다

파일 길이 8, 패턴 길이 6 이면 범위는 `0..8.saturating_sub(6)` = `0..2` 로, `i = 0, 1` 만 검사한다.
패턴이 시작할 수 있는 마지막 위치 2 는 `..` 범위의 끝이라 포함되지 않는다.
`0..=len - plen` 처럼 끝을 포함해야 하는데, 원본은 이 위치를 놓친다.
예제의 파일은 `ABCDEF` 뒤에 줄바꿈이 있어 이 빈틈에 걸리지 않았을 뿐이다.
근거: 2-summary 「어디서 틀리나 2」.

### 7. 순차 읽기는 buffered I/O 로도 충분히 빠르고, 작은 파일에서는 매핑을 세우는 비용이 크기 때문이다

mmap 의 큰 이득은 랜덤 액세스가 슬라이스 인덱싱이 된다는 데 있다.
처음부터 끝까지 한 번 훑는 일에서는 일반 청크 읽기도 충분히 빠르다.
작은 파일에서는 매핑을 세우는 오버헤드가 복사를 아낀 몫보다 크다.
게다가 `unsafe` 와 신호 오류라는 대가는 그대로 남는다.
근거: 2-summary 「어디서 틀리나 5 · 6」 · 「언제 쓰고 언제 안 쓰나」.

### 8. `&mmap[offset..offset + len]` 슬라이스 하나로 바뀌고, 커널에서 버퍼로 복사하는 일이 사라진다

일반 I/O 는 커서를 옮기고(`seek`), 버퍼에 복사하고(`read`), 짧게 읽은 만큼 잘라 낸다(`truncate`).
mmap 에서는 파일이 이미 주소 공간에 붙어 있으므로 범위를 잘라 보는 슬라이스 인덱싱이면 된다.
새 `Vec` 할당과 커널 ↔ 유저 복사가 없어지는 것이 zero-copy 다.
근거: 2-summary 「동작 방식 (2)」 · 「동작 방식 (4)」 · 「문법 — 형태와 규칙」.

### 9. mmap 의 읽기는 함수 호출이 아니라 메모리 접근이라, 오류가 `Result` 대신 OS 신호로 오기 때문이다

일반 I/O 는 `read` 가 `io::Result` 를 돌려주므로 실패를 `?` 로 넘길 수 있다.
mmap 에서 바이트를 읽는 것은 `mmap[i]` 같은 평범한 인덱싱이라 돌려줄 `Result` 가 없다.
매핑 뒤 파일이 잘리는 등 접근이 잘못되면 SIGBUS/SIGSEGV 신호가 프로세스에 온다.
`Mmap::map(&file)?` 의 `?` 는 매핑을 만드는 순간의 오류만 잡는다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 4」.

## 실습 정답

### 실습 1. 일반 I/O 로 mmap 이 할 일을 흉내 내기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 테스트 파일에 1000줄 쓰기 | `fs::File::create(test_path)` · `for i in 0..1000` · `writeln!(f, "Line {}: …", i)` |
| 2. 블록 안에서 만들어 닫기 | `main` 의 `{ let mut f = …; … }` 블록 |
| 3. 파일 크기 | `fs::metadata(test_path)?` · `metadata.len()` |
| 4. 8KB 스택 버퍼 | `count_bytes_regular` 의 `let mut buffer = [0u8; 8192];` |
| 5. `read` 반복, 0 이면 멈춤 | `loop { let n = file.read(&mut buffer)?; if n == 0 { break; } … }` |
| 6. 읽은 부분만 누적 | `for &byte in &buffer[..n] { freq[byte as usize] += 1; }` · `[0u64; 256]` |
| 7. 세 빈도 찍기 | `freq[b'H' as usize]` · `freq[b'\n' as usize]` · `freq[b'A' as usize]` |
| 8. 시작 기준 `seek` | `file.seek(SeekFrom::Start(offset))?` |
| 9. `read` 후 `truncate` | `vec![0u8; len]` · `file.read(&mut buf)?` · `buf.truncate(n)` |
| 10. 두 조각 찍기 | `read_at_offset(test_path, 0, 50)` · `read_at_offset(test_path, 100, 30)` · `String::from_utf8_lossy` |
| 11. 파일 전체 읽기 | `search_in_file` 의 `fs::read(path)?` |
| 12. 범위와 슬라이스 비교 | `0..data.len().saturating_sub(pattern.len())` · `&data[i..i + pattern.len()] == pattern` · `positions.push(i as u64)` |
| 13. 개수와 처음 3개 | `positions.len()` · `if positions.len() > 3` · `&positions[..3]` |
| 14. 사용 패턴과 장단점 | `println!(r#"// Cargo.toml: memmap2 = "0.9" …"#)` · `mmap 장점:` · `mmap 단점:` 줄들 |
| 15. 파일 지우고 끝내기 | `fs::remove_file(test_path)?` · `Ok(())` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`rust/rust-systems/reference/mmap.rs`

```rust
// [시스템 프로그래밍] 메모리 매핑 파일
// 설명: 메모리 매핑 파일(mmap) 개념과 memmap2 크레이트 패턴
// 팁: mmap은 파일을 가상 메모리에 매핑하여 슬라이스처럼 접근한다. 커널-유저 공간 복사를 제거(zero-copy)하여 대용량 파일 처리에 유리하다. memmap2 크레이트의 Mmap::map()은 unsafe인데, 다른 프로세스가 파일을 수정하면 UB가 발생할 수 있기 때문이다. 순차 읽기에서는 buffered I/O도 충분히 빠르므로, 랜덤 액세스가 많을 때 mmap이 특히 유리하다.

// I/O 트레이트와 시킹
use std::io::{Read, Write, Seek, SeekFrom};
use std::fs;

// mmap 개념을 표준 라이브러리로 시뮬레이션
// 실제로는 memmap2 크레이트를 사용

/// 대용량 파일에서 바이트 빈도 분석 (일반 I/O)
// 8KB 청크 단위로 read하면서 빈도 누적
fn count_bytes_regular(path: &str) -> std::io::Result<[u64; 256]> {
    let mut file = fs::File::open(path)?;
    // 스택 버퍼 - 힙 할당 없음
    let mut buffer = [0u8; 8192]; // 8KB 버퍼
    // 256바이트 값별 빈도 배열
    let mut freq = [0u64; 256];

    loop {
        // read는 버퍼에 채울 만큼 읽고 그 길이 반환
        let n = file.read(&mut buffer)?;
        // EOF면 종료
        if n == 0 { break; }
        // 실제 읽은 부분만 집계
        for &byte in &buffer[..n] {
            freq[byte as usize] += 1;
        }
    }
    Ok(freq)
}

/// 파일의 특정 오프셋 읽기 (random access)
// seek + read 조합 - mmap이라면 직접 슬라이스 인덱싱
fn read_at_offset(path: &str, offset: u64, len: usize) -> std::io::Result<Vec<u8>> {
    let mut file = fs::File::open(path)?;
    // SeekFrom::Start(n): 파일 시작에서 n바이트
    file.seek(SeekFrom::Start(offset))?;
    let mut buf = vec![0u8; len];
    let n = file.read(&mut buf)?;
    // 실제 읽은 만큼만 잘라냄 (EOF 근접 시)
    buf.truncate(n);
    Ok(buf)
}

/// 파일 내 패턴 검색
// 전체를 메모리에 로드 후 선형 검색 (mmap이면 zero-copy)
fn search_in_file(path: &str, pattern: &[u8]) -> std::io::Result<Vec<u64>> {
    // fs::read: 파일 전체를 Vec<u8>로 읽기
    let data = fs::read(path)?;
    let mut positions = Vec::new();
    // saturating_sub: 언더플로 방지
    for i in 0..data.len().saturating_sub(pattern.len()) {
        // 슬라이스 비교
        if &data[i..i + pattern.len()] == pattern {
            positions.push(i as u64);
        }
    }
    Ok(positions)
}

fn main() -> std::io::Result<()> {
    // 테스트 파일 생성
    let test_path = "/tmp/rust_mmap_test.txt";
    {
        let mut f = fs::File::create(test_path)?;
        // 1000줄 쓰기 (충분히 큰 테스트 데이터)
        for i in 0..1000 {
            writeln!(f, "Line {}: Hello, memory-mapped world! ABCDEF", i)?;
        }
    }

    // 파일 크기 확인
    let metadata = fs::metadata(test_path)?;
    println!("=== 메모리 매핑 파일 ===");
    println!("파일 크기: {} bytes", metadata.len());

    // 바이트 빈도 분석
    println!("\n=== 바이트 빈도 분석 (일반 I/O) ===");
    let freq = count_bytes_regular(test_path)?;
    println!("'H' 빈도: {}", freq[b'H' as usize]);
    println!("'\\n' 빈도: {}", freq[b'\n' as usize]);
    println!("'A' 빈도: {}", freq[b'A' as usize]);

    // 랜덤 액세스
    println!("\n=== 오프셋 읽기 ===");
    let data = read_at_offset(test_path, 0, 50)?;
    // from_utf8_lossy: 잘못된 바이트는 �로 대체
    println!("처음 50바이트: {}", String::from_utf8_lossy(&data));

    let data2 = read_at_offset(test_path, 100, 30)?;
    println!("100~130 바이트: {}", String::from_utf8_lossy(&data2));

    // 패턴 검색
    println!("\n=== 패턴 검색 ===");
    let positions = search_in_file(test_path, b"ABCDEF")?;
    println!("'ABCDEF' 발견 위치: {} 곳", positions.len());
    if positions.len() > 3 {
        println!("처음 3개: {:?}", &positions[..3]);
    }

    // memmap2 사용법 (코드 참고)
    // 실제 mmap은 외부 크레이트 필요 - 사용 패턴만 문자열로 보여줌
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

    // mmap의 트레이드오프 요약
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

    // 정리
    fs::remove_file(test_path)?;
    Ok(())
}
```

**실행 결과** — 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다).

**풀이 요점**
- `read` 의 반환값 `n` 이 전부다 — 빈도는 `&buffer[..n]` 만, 오프셋 읽기는 `truncate(n)` 으로 실제 읽은 만큼만 쓴다.
- `seek` + `read` + `truncate` 세 단계가 mmap 이라면 슬라이스 하나가 되는 자리라는 점을 주석과 함께 대비해 둔다.
- `saturating_sub` 는 짧은 파일의 언더플로를 막지만, `..` 범위 때문에 마지막 시작 위치를 빼먹는다 — 끝을 포함하려면 `..=` 를 따져야 한다.
- 원시 문자열이라도 `println!` 의 형식 문자열이므로 중괄호는 `{{` · `}}` 로 적어야 그대로 찍힌다.
- 쓰기 파일을 블록으로 닫고 나서 다시 열어 읽는 차례가 중요하다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
