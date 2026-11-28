# rust/rust-io/12 — 임시 파일 패턴 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 안에서는 `true`, 밖에서는 `false`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
안: true
밖: false
```

**왜 그런가**
`TempDir::new` 는 경로가 없을 때 `create_dir_all` 로 만든 뒤 돌려주므로 블록 안에서는 디렉토리가 있다.
블록의 `}` 에서 `tmp` 가 버려지며 `drop` 이 `remove_dir_all` 을 부르므로, 블록 밖에서는 같은 경로가 사라진다.
`kept` 는 경로의 복사본(`PathBuf`)일 뿐이라 디렉토리를 붙잡아 두지 않는다.
근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (2)」.

### 2. `output_0.tmp` · `output_1.tmp`, 그리고 다시 `output_0.tmp`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`a` 는 `output_0.tmp`, `b` 는 `output_1.tmp` 다.
`c` 는 `output_0.tmp` 다.

**왜 그런가**
`TempFile::new` 는 `counter = 0` 부터 `{prefix}_{counter}.tmp` 가 이미 있는지 보고, 있으면 하나씩 올린다.
`b` 를 만들 때는 `output_0.tmp` 가 `a` 때문에 있으므로 `output_1.tmp` 로 넘어간다.
`drop(a)` 로 `a` 의 `drop` 이 돌면 `output_0.tmp` 가 지워지므로, `c` 는 다시 0 번 이름을 얻는다.
근거: 2-summary 「동작 방식 (3)」 · 「문법 — 형태와 규칙」(`drop(값)`).

### 3. `.config.json.tmp` 에 먼저 쓰고, 끝나면 그 이름은 사라진다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
먼저 쓰이는 파일은 `config.json` 과 같은 디렉토리의 `.config.json.tmp` 다.
`safe_write` 가 끝나면 `.config.json.tmp` 는 남아 있지 않다.

**왜 그런가**
`safe_write` 는 `target.parent()` 를 디렉토리로 잡고 `format!(".{}.tmp", 파일이름)` 으로 임시 경로를 만든다.
`fs::write` 로 그 임시 파일에 다 쓴 뒤 `fs::rename` 으로 `config.json` 자리로 옮기므로, 임시 이름은 없어지고 내용은 `config.json` 이 된다.
근거: 2-summary 「동작 방식 (4)」.

### 4. 둘 다 남지 않는다 — `parent` 와 함께 지워진다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`main` 이 끝난 뒤 `permanent.txt` 와 `config.json` 은 디스크에 없다.

**왜 그런가**
두 파일은 모두 `parent.child(..)` 로 만든 경로, 곧 `parent` 임시 디렉토리 **안**에 있다.
`parent` 는 `main` 의 지역 변수라 `main` 이 끝날 때 버려지고, 그 `drop` 이 `remove_dir_all` 로 트리 전체를 지운다.
「persist」는 임시 이름에서 정식 이름으로 옮긴 것일 뿐, 정리될 디렉토리 바깥으로 꺼낸 것이 아니다.
근거: 2-summary 「어디서 틀리나 5」 · 「동작 방식 (5)」.

### 5. 열린 핸들을 먼저 닫으려고 — `Option` 이어야 꺼낼 수 있다

원본은 「파일 먼저 닫기」를 정리 순서로 정해 두었다 — 열린 채로 지우면 문제가 되는 환경이 있기 때문이다.
`drop(&mut self)` 은 `self` 를 빌려 받을 뿐이라 필드 `File` 을 그냥 꺼내 버릴 수 없다.
`Option<fs::File>` 이면 `take()` 가 필드를 `None` 으로 바꾸고 `File` 을 꺼내 주므로, 꺼낸 값이 그 자리에서 버려지며 핸들이 닫힌다.
그 다음에 `remove_file` 을 부르면 「닫고 나서 지우기」 순서가 지켜진다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 3」. 「열린 파일 삭제가 막히는 환경」은 2-summary 「구현 세부사항 대 언어 보장」의 (확인 필요) 항목에 기댄다.

### 6. `rename` 이 원자적이려면 같은 파일시스템이어야 해서

`safe_write` 의 핵심은 마지막 `rename` 한 번으로 옛 파일을 새 파일로 바꿔치기하는 것이다.
원본 주석에 따르면 이 교체는 같은 파일시스템(같은 디렉토리)일 때 원자적이다.
`temp_dir()` 은 대상과 다른 파일시스템에 있을 수 있어서, 그곳에 쓰면 원자적 교체를 기대할 수 없다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 6」.

### 7. 돌려줄 길이 없고, 이미 지워졌을 수도 있어서

`drop` 은 반환형이 `()` 라 `?` 로 오류를 위에 넘길 수 없다.
원본 주석대로 디렉토리는 다른 곳에서 이미 지웠을 수도 있으므로, 실패를 무시해도 대부분 괜찮다.
대가는 「지우지 못해도 아무도 모른다」는 점이다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 4」 · 「문법 — 형태와 규칙」.

### 8. 확인과 생성 사이에 다른 프로세스가 끼어들 때 깨진다

`exists()` 가 `false` 를 돌려준 다음, 실제로 만들기 전 사이에 다른 프로세스가 같은 이름을 먼저 만들 수 있다.
그러면 두 쪽이 같은 경로를 각자의 임시 자원으로 여기게 된다.
원본은 이런 경쟁 방지를 실제 tempfile 크레이트가 OS 차원에서 처리해 준다고 적는다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 1」 · 「동작 방식 (6)」.

### 9. `TempDir::new` 는 1000 을 넘으면 `Err`, `TempFile::new` 는 빈 이름이 나올 때까지 돈다

`TempDir::new` 는 `counter > 1000` 에서 `ErrorKind::Other` 와 "임시 디렉토리 생성 실패" 로 `Err` 를 돌려준다.
`TempFile::new` 에는 상한이 없어 이름이 빌 때까지 `counter` 를 계속 올린다.
`TempFile::new` 가 오류로 끝나는 것은 `File::create` 가 실패해 `?` 가 오류를 넘길 때다.
근거: 2-summary 「어디서 틀리나 2」.

### 10. 둘 다 「임시 이름에 쓰고 `rename` 으로 정식 이름에 옮긴다」

원본은 「persist = rename」이라고 적는다 — 임시 파일을 영구 위치로 옮기는 것이 persist 다.
`safe_write` 도 `.{이름}.tmp` 에 다 쓴 뒤 `rename` 으로 대상 이름에 옮긴다.
다른 점은 목적이다 — `safe_write` 는 옛 파일을 반쪽 상태 없이 바꾸는 데, `persist()` 는 자동 삭제될 임시 파일을 조건에 따라 남기는 데 쓴다.
근거: 2-summary 「동작 방식 (4)」 · 「동작 방식 (5)」 · 「핵심 문장 5」.

## 실습 정답

### 실습 1. 자동 정리되는 임시 디렉토리 · 파일과 안전한 쓰기 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. `PathBuf` 경로 필드 | `struct TempDir { path: PathBuf }` |
| 2. `{prefix}_{PID}_{counter}` 를 temp_dir 아래에, 없으면 생성 | `TempDir::new` 의 `format!` · `std::env::temp_dir().join` · `if !path.exists()` · `fs::create_dir_all` |
| 3. 겹치면 카운터 증가, 1000 초과 시 `Err` | `counter += 1` · `if counter > 1000 { return Err(io::Error::new(io::ErrorKind::Other, …)) }` |
| 4. `path()` · `child()` | `fn path(&self) -> &Path` · `fn child(&self, name) -> PathBuf { self.path.join(name) }` |
| 5. Drop 에서 트리 삭제, 실패 무시 | `impl Drop for TempDir` 의 `let _ = fs::remove_dir_all(&self.path)` |
| 6. 경로 + `Option<File>` 필드 | `struct TempFile { path, file: Option<fs::File> }` |
| 7. `{prefix}_{counter}.tmp`, 상한 없이, 핸들 보관 | `TempFile::new` 의 `format!("{}_{}.tmp", …)` · `fs::File::create` · `file: Some(file)` |
| 8. `path()` · `file_mut()` | `fn file_mut(&mut self)` 의 `self.file.as_mut().unwrap()` |
| 9. 먼저 닫고 삭제 | `impl Drop for TempFile` 의 `self.file.take();` → `let _ = fs::remove_file(..)` |
| 10. 같은 디렉토리 `.{이름}.tmp` 에 쓰고 rename | `safe_write` 의 `target.parent().unwrap_or(Path::new("."))` · `fs::write(&temp_path, …)` · `fs::rename(&temp_path, target)` |
| 11. 섹션 1 | 첫 블록의 `TempDir::new("rust_demo")` · `tmp.child("data.txt")` · `tmp.child("sub")` · `fs::read_to_string` |
| 12. 섹션 2 | 블록 밖 `let parent = TempDir::new("rust_tempfile")?` · `TempFile::new(parent.path(), "output")` · `writeln!` 두 번 · `flush()` · `BufReader::new(fs::File::open(..))` · `reader.lines()` |
| 13. 섹션 3 | `parent.child("config.json")` · `safe_write(&target, r#"{"key": "value"}"#)` |
| 14. 섹션 4 | `parent.child("persist_temp.tmp")` 에 `fs::write` · `fs::rename(&tmp_path, &persist_target)` |
| 15. 섹션 5 | `=== 실제 tempfile 크레이트 ===` 아래의 `println!` 줄들 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`rust/rust-io/reference/tempfile.rs`

```rust
// [입출력 & 직렬화] 임시 파일 패턴
// 설명: 임시 파일/디렉토리 생성, 자동 정리, tempfile 크레이트 패턴
// 팁: 임시 파일/디렉토리는 Drop 트레이트로 자동 정리된다. 안전한 파일 업데이트는 '임시에 쓰고 rename' 패턴이 표준이다. tempfile 크레이트의 NamedTempFile::persist()로 조건부 영구 보관이 가능하다.

// fs: 파일/디렉토리 조작
use std::fs;
// Write: writeln! 사용, BufRead/BufReader: 줄 단위 읽기
use std::io::{self, Write, BufRead, BufReader};
// Path: 빌림 경로(슬라이스), PathBuf: 소유 경로
use std::path::{Path, PathBuf};

// === tempfile 크레이트 패턴을 순수 Rust로 구현 ===

// 자동 정리되는 임시 디렉토리
// Drop 시 디렉토리 트리 전체를 삭제
struct TempDir {
    // 생성된 디렉토리의 절대 경로 (소유)
    path: PathBuf,
}

impl TempDir {
    // 시스템 temp 디렉토리 아래에 충돌 없는 이름으로 생성
    fn new(prefix: &str) -> io::Result<Self> {
        // 카운터로 충돌 회피 (PID + 카운터)
        let mut counter = 0u64;
        loop {
            // 후보 이름 만들기
            let name = format!("{}_{}_{}", prefix, std::process::id(), counter);
            // std::env::temp_dir(): OS의 임시 디렉토리 (예: /tmp)
            let path = std::env::temp_dir().join(name);
            // 비어 있으면 생성 후 반환
            if !path.exists() {
                fs::create_dir_all(&path)?;
                return Ok(TempDir { path });
            }
            counter += 1;
            // 안전장치: 무한 루프 방지
            if counter > 1000 {
                return Err(io::Error::new(io::ErrorKind::Other, "임시 디렉토리 생성 실패"));
            }
        }
    }

    // 생성된 경로의 빌림(&Path) 노출
    fn path(&self) -> &Path {
        &self.path
    }

    // 자식 경로 합성 (소유 PathBuf 반환)
    fn child(&self, name: &str) -> PathBuf {
        self.path.join(name)
    }
}

// Drop: 객체가 스코프를 벗어나면 자동 호출 → 자원 해제 표준 패턴
impl Drop for TempDir {
    fn drop(&mut self) {
        // 실패는 무시 (이미 다른 곳에서 지웠을 수 있음)
        let _ = fs::remove_dir_all(&self.path);
    }
}

// 자동 정리되는 임시 파일
// 파일 핸들과 경로 보유, Drop 시 파일 삭제
struct TempFile {
    path: PathBuf,
    // Option으로 감싸 Drop 시 명시적으로 닫기 가능
    file: Option<fs::File>,
}

impl TempFile {
    // 주어진 디렉토리 내에 충돌 없는 이름으로 임시 파일 생성
    fn new(dir: &Path, prefix: &str) -> io::Result<Self> {
        let mut counter = 0u64;
        loop {
            // 이름 후보
            let name = format!("{}_{}.tmp", prefix, counter);
            let path = dir.join(name);
            if !path.exists() {
                // 파일 생성하여 핸들 보관
                let file = fs::File::create(&path)?;
                return Ok(TempFile { path, file: Some(file) });
            }
            counter += 1;
        }
    }

    // 경로 빌림
    fn path(&self) -> &Path {
        &self.path
    }

    // 파일 핸들 가변 빌림 (writeln! 등에 사용)
    fn file_mut(&mut self) -> &mut fs::File {
        // 항상 Some을 가정 (Drop에서만 take)
        self.file.as_mut().unwrap()
    }
}

// Drop: 핸들 닫고 파일 삭제
impl Drop for TempFile {
    fn drop(&mut self) {
        // take로 Option에서 파일을 꺼내 즉시 Drop → 핸들 닫힘
        self.file.take(); // 파일 먼저 닫기
        let _ = fs::remove_file(&self.path);
    }
}

// === 실용: 안전한 파일 쓰기 (write-then-rename) ===
// 부분 쓰기 중 크래시해도 기존 파일이 손상되지 않도록 임시 파일에 쓴 뒤 원자적 rename
fn safe_write(target: &Path, content: &str) -> io::Result<()> {
    // 같은 디렉토리에 임시 파일 (rename 원자성 보장 위해 동일 FS 필요)
    let dir = target.parent().unwrap_or(Path::new("."));
    let temp_path = dir.join(format!(".{}.tmp", target.file_name().unwrap().to_string_lossy()));

    // 임시 파일에 쓰기
    fs::write(&temp_path, content)?;

    // 원자적 교체 (같은 파일시스템이면 원자적)
    // POSIX: rename은 같은 디렉토리/FS에서 원자적으로 보장
    fs::rename(&temp_path, target)?;

    Ok(())
}

fn main() -> io::Result<()> {
    // === 1. TempDir 사용 ===
    println!("=== TempDir ===");
    {
        // 새 임시 디렉토리. 블록 종료 시 자동 삭제
        let tmp = TempDir::new("rust_demo")?;
        println!("임시 디렉토리: {}", tmp.path().display());
        println!("존재: {}", tmp.path().exists());

        // 임시 디렉토리 내 파일 생성
        let file_path = tmp.child("data.txt");
        fs::write(&file_path, "임시 데이터")?;
        println!("파일 생성: {}", file_path.display());

        // 하위 디렉토리도 만들고 그 안에 파일 작성
        let sub_dir = tmp.child("sub");
        fs::create_dir(&sub_dir)?;
        fs::write(sub_dir.join("nested.txt"), "중첩 파일")?;
        println!("중첩 파일 생성");

        // 스코프 내에서 활용
        let content = fs::read_to_string(&file_path)?;
        println!("읽기: {}", content);
    } // Drop -> 자동 삭제
    println!("스코프 벗어남 -> 자동 삭제됨");

    // === 2. TempFile 사용 ===
    println!("\n=== TempFile ===");
    // 부모 임시 디렉토리 (이 변수의 Drop 시점까지 유지)
    let parent = TempDir::new("rust_tempfile")?;
    {
        // 부모 디렉토리 안에 임시 파일
        let mut tmp = TempFile::new(parent.path(), "output")?;
        println!("임시 파일: {}", tmp.path().display());

        // 파일 핸들로 직접 쓰기
        writeln!(tmp.file_mut(), "테스트 데이터")?;
        writeln!(tmp.file_mut(), "두 번째 줄")?;
        // 디스크에 즉시 반영
        tmp.file_mut().flush()?;

        // 읽기 위해 별도로 열기
        // BufReader로 줄 단위 읽기 (버퍼링 효과로 시스콜 감소)
        let reader = BufReader::new(fs::File::open(tmp.path())?);
        for line in reader.lines() {
            println!("  {}", line?);
        }

        println!("파일 존재: {}", tmp.path().exists());
    } // Drop -> 자동 삭제
    println!("파일 자동 삭제됨");

    // === 3. 안전한 파일 쓰기 ===
    println!("\n=== 안전한 파일 쓰기 (write-then-rename) ===");
    let target = parent.child("config.json");
    safe_write(&target, r#"{"key": "value"}"#)?;
    println!("안전하게 쓰기 완료: {}", target.display());
    println!("내용: {}", fs::read_to_string(&target)?);
    println!("장점: 쓰기 중 크래시해도 기존 파일 손상 없음");

    // === 4. persist 패턴 ===
    println!("\n=== persist 패턴 ===");
    // tempfile 크레이트의 persist(): 임시 파일을 영구 보관
    // 직접 구현 시: 임시 파일에 쓴 뒤 rename으로 영구 위치로 이동
    let persist_target = parent.child("permanent.txt");
    {
        let tmp_path = parent.child("persist_temp.tmp");
        fs::write(&tmp_path, "영구 보관할 데이터")?;
        // persist = rename
        fs::rename(&tmp_path, &persist_target)?;
    }
    println!("persist된 파일: {}", fs::read_to_string(&persist_target)?);

    // === 5. 실제 tempfile 크레이트 사용법 ===
    println!("\n=== 실제 tempfile 크레이트 ===");
    // 실제 크레이트는 OS 차원 보안 (권한, 경쟁 방지) 처리도 해줌
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

**실행 결과** — 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다).

**풀이 요점**
- 정리 코드는 `Drop` 하나에 모았다 — 호출하는 쪽은 블록만 잘 나누면 된다.
- `parent` 를 블록 밖에 둔 것은 섹션 2~4 내내 디렉토리를 살려 두기 위해서다 — 그 대가로 `main` 끝에서 `config.json` · `permanent.txt` 도 함께 지워진다.
- `TempFile` 이 `Option<fs::File>` 을 쓰는 까닭은 `drop` 에서 `take()` 로 핸들을 먼저 닫기 위해서다.
- `safe_write` 는 임시 파일을 대상과 같은 디렉토리에 두어 `rename` 의 원자성 조건(같은 파일시스템)을 맞춘다.
- persist 는 따로 있는 기능이 아니라 `rename` 한 번이다.
- 이름 고르기의 `exists()` → 생성 사이 틈은 남아 있다 — 실무에서는 tempfile 크레이트에 맡긴다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
