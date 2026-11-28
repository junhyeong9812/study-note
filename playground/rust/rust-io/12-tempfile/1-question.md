# rust/rust-io/12 — 임시 파일 패턴 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 블록 안과 밖에서 본 임시 디렉토리 (예측)

```rust
// 질문용 발췌
let kept;
{
    let tmp = TempDir::new("rust_demo")?;
    kept = tmp.path().to_path_buf();
    println!("안: {}", kept.exists());
}
println!("밖: {}", kept.exists());
```

- 두 줄에 찍히는 `true` / `false` 는 각각 무엇인가?

### 2. 같은 접두사로 임시 파일을 여러 개 만들면 (예측)

```rust
// 질문용 발췌
let parent = TempDir::new("rust_tempfile")?;
let a = TempFile::new(parent.path(), "output")?;
let b = TempFile::new(parent.path(), "output")?;
drop(a);
let c = TempFile::new(parent.path(), "output")?;
```

- `a` 와 `b` 의 파일 이름은 각각 무엇인가?
- `a` 를 버린 뒤 만든 `c` 의 파일 이름은 무엇인가?

### 3. `safe_write` 가 거쳐 가는 파일 (예측)

```rust
// 질문용 발췌
let target = parent.child("config.json");
safe_write(&target, r#"{"key": "value"}"#)?;
```

- `safe_write` 안에서 먼저 내용이 쓰이는 파일의 이름은 무엇인가?
- `safe_write` 가 끝난 뒤 그 파일은 디렉토리에 남아 있는가?

### 4. 원본 `main` 이 끝난 뒤의 `permanent.txt` (예측)

- 원본 예제의 `main` 이 `Ok(())` 를 돌려준 뒤, `permanent.txt` 와 `config.json` 은 디스크에 남아 있는가?

### 5. `TempFile::drop` 이 `take()` 부터 부르는 까닭 (왜)

- `TempFile` 의 `drop` 은 왜 `remove_file` 보다 `self.file.take()` 를 먼저 부르는가?
- 그 일을 하려고 `file` 필드를 왜 `Option<fs::File>` 로 두었는가?

### 6. 임시 파일을 대상과 같은 디렉토리에 두는 까닭 (왜)

- `safe_write` 는 왜 임시 파일을 `std::env::temp_dir()` 이 아니라 대상 파일과 같은 디렉토리에 만드는가?

### 7. `drop` 안에서 오류를 버리는 까닭 (왜)

- `TempDir::drop` 은 왜 `fs::remove_dir_all` 의 실패를 `?` 로 넘기지 않고 `let _ =` 로 버리는가?

### 8. 「없으면 만든다」 방식의 한계 (경계)

- `if !path.exists()` 로 확인한 다음 만드는 방식은 어떤 상황에서 깨지는가?

### 9. 이름이 계속 겹칠 때 두 생성자의 끝 (경계)

- 후보 이름이 계속 이미 있다면 `TempDir::new` 와 `TempFile::new` 는 각각 어떻게 끝나는가?

### 10. `persist()` 와 `safe_write` 의 공통점 (연결)

- tempfile 크레이트의 `NamedTempFile::persist()` 는 이 문서의 `safe_write` 와 어떤 점에서 같은 일을 하는가?

## 실습

### 실습 1. 자동 정리되는 임시 디렉토리 · 파일과 안전한 쓰기 만들기

**만들 것** — tempfile 크레이트의 패턴(`TempDir` · `TempFile` · write-then-rename · persist)을 표준 라이브러리만으로 구현하고, `main` 에서 다섯 섹션으로 차례로 시연한다.

**준비물** — 외부 크레이트는 필요 없다. tempfile 크레이트를 `std` 만으로 흉내 낸 구현이다(섹션 5 는 실제 크레이트의 사용법을 글로만 찍는다).

**요구 조건**

1단계 — `TempDir`

1. `TempDir` 은 디렉토리 경로를 `PathBuf` 필드 `path` 로 가진다.
2. `TempDir::new(prefix)` 는 `std::env::temp_dir()` 아래에 `{prefix}_{PID}_{counter}` 이름을 붙이고, 그 경로가 없으면 `fs::create_dir_all` 로 만들어 돌려준다.
3. 경로가 이미 있으면 `counter` 를 1 올려 다시 시도하고, `counter` 가 1000 을 넘으면 `io::ErrorKind::Other` 와 "임시 디렉토리 생성 실패" 로 `Err` 를 돌려준다.
4. `path()` 는 `&Path` 를, `child(name)` 은 디렉토리 아래 자식 경로 `PathBuf` 를 돌려준다.
5. `Drop` 에서 `fs::remove_dir_all` 로 디렉토리 트리를 지우고, 실패는 무시한다.

2단계 — `TempFile`

6. `TempFile` 은 `path: PathBuf` 와 `file: Option<fs::File>` 을 가진다.
7. `TempFile::new(dir, prefix)` 는 `dir` 안에 `{prefix}_{counter}.tmp` 이름이 없을 때까지 `counter` 를 올리고(상한 없음), `fs::File::create` 로 만든 핸들을 `Some` 으로 담아 돌려준다.
8. `path()` 는 `&Path` 를, `file_mut()` 은 안의 `File` 을 `&mut` 로 빌려준다.
9. `Drop` 에서 `take()` 로 핸들을 먼저 닫고, 그다음 `fs::remove_file` 로 지운다(실패는 무시).

3단계 — `safe_write`

10. 대상의 부모 디렉토리(없으면 `"."`) 안에 `.{파일이름}.tmp` 임시 파일을 만들어 `fs::write` 로 내용을 쓰고, `fs::rename` 으로 대상과 바꿔치기한다.

4단계 — `main` (`io::Result<()>` 를 돌려준다)

11. 섹션 1: 블록 안에서 `TempDir::new("rust_demo")` 로 만든 경로와 존재 여부를 찍고, `data.txt` 에 "임시 데이터" 를, `sub/nested.txt` 에 "중첩 파일" 을 쓴 뒤, `data.txt` 를 읽어 찍는다. 블록이 끝난 뒤 자동 삭제를 알리는 줄을 찍는다.
12. 섹션 2: 블록 **밖**에 `TempDir::new("rust_tempfile")` 로 `parent` 를 만든다. 블록 안에서 `parent` 안에 `"output"` 임시 파일을 만들어 경로를 찍고, "테스트 데이터" · "두 번째 줄" 두 줄을 `writeln!` 으로 쓰고 `flush` 한 다음, 파일을 따로 열어 `BufReader` 로 줄마다 앞에 공백 두 칸을 붙여 찍고, 존재 여부를 찍는다. 블록이 끝난 뒤 자동 삭제를 알리는 줄을 찍는다.
13. 섹션 3: `parent.child("config.json")` 에 `safe_write` 로 `{"key": "value"}` 를 쓰고, 경로 · 읽은 내용 · 장점 문장을 찍는다.
14. 섹션 4: `parent` 안의 `persist_temp.tmp` 에 "영구 보관할 데이터" 를 쓰고 `rename` 으로 `permanent.txt` 로 옮긴 뒤, 읽어서 찍는다.
15. 섹션 5: 실제 tempfile 크레이트 사용법 안내 줄을 찍는다(시작 코드에 채워 둠).

**시작 코드**

```rust
use std::fs;
use std::io::{self, Write, BufRead, BufReader};
use std::path::{Path, PathBuf};

// 자동 정리되는 임시 디렉토리
struct TempDir {
    // TODO: 경로 필드
}

impl TempDir {
    fn new(prefix: &str) -> io::Result<Self> {
        // TODO: prefix_PID_counter 이름 고르기 → 없으면 만들고 반환, 1000 넘으면 Err
        todo!()
    }

    fn path(&self) -> &Path {
        todo!()
    }

    fn child(&self, name: &str) -> PathBuf {
        todo!()
    }
}

// TODO: impl Drop for TempDir — 디렉토리 트리 삭제, 실패 무시

// 자동 정리되는 임시 파일
struct TempFile {
    // TODO: 경로 필드, 닫을 수 있게 담은 파일 핸들 필드
}

impl TempFile {
    fn new(dir: &Path, prefix: &str) -> io::Result<Self> {
        // TODO: prefix_counter.tmp 이름 고르기 → 파일 만들고 핸들 보관
        todo!()
    }

    fn path(&self) -> &Path {
        todo!()
    }

    fn file_mut(&mut self) -> &mut fs::File {
        todo!()
    }
}

// TODO: impl Drop for TempFile — 핸들 먼저 닫고 파일 삭제

// 안전한 파일 쓰기 (write-then-rename)
fn safe_write(target: &Path, content: &str) -> io::Result<()> {
    // TODO: 같은 디렉토리의 .{이름}.tmp 에 쓰고 rename
    todo!()
}

fn main() -> io::Result<()> {
    println!("=== TempDir ===");
    // TODO: 섹션 1
    println!("스코프 벗어남 -> 자동 삭제됨");

    println!("\n=== TempFile ===");
    // TODO: 섹션 2 (parent 는 블록 밖)
    println!("파일 자동 삭제됨");

    println!("\n=== 안전한 파일 쓰기 (write-then-rename) ===");
    // TODO: 섹션 3
    println!("장점: 쓰기 중 크래시해도 기존 파일 손상 없음");

    println!("\n=== persist 패턴 ===");
    // TODO: 섹션 4

    println!("\n=== 실제 tempfile 크레이트 ===");
    println!("// Cargo.toml: tempfile = \"3\"");
    println!("// ");
    println!("// 임시 파일 (이름 있음):");
    println!("// let mut file = tempfile::NamedTempFile::new()?;");
    println!("// writeln!(file, \"data\")?;");
    println!("// file.path()  // 경로 접근");
    println!("// file.persist(\"target.txt\")?;  // 영구 보관");
    println!("// ");
    println!("// 임시 파일 (이름 없음, 더 안전):");
    println!("// let mut file = tempfile::tempfile()?;");
    println!("// writeln!(file, \"data\")?;");
    println!("// ");
    println!("// 임시 디렉토리:");
    println!("// let dir = tempfile::tempdir()?;");
    println!("// dir.path().join(\"file.txt\")");
    println!("// Drop 시 자동 삭제");

    Ok(())
}
```

**확인 방법** — `rustc tempfile.rs && ./tempfile` 로 돌려 다섯 섹션 제목 아래에 경로 · 존재 여부 · 읽은 내용이 차례로 찍히는지 본다. 끝난 뒤 OS 임시 디렉토리에 `rust_demo_` · `rust_tempfile_` 로 시작하는 디렉토리가 남아 있지 않은지 확인한다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
