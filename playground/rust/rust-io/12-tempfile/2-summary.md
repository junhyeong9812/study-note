# rust/rust-io/12 — 임시 파일 패턴 — 정리 (힌트)

> 출처 — study-site 항목 `rust/tempfile`(항목 데이터 `data/rust/io-serde.json`) · 정답 코드 study-practice `rust/rust-io/reference/tempfile.rs`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다).

## 한눈에 — 쉽게 말하면

**임시 파일 패턴은 「호텔 객실」이다.**
체크인할 때 비어 있는 방 번호를 받고, 머무는 동안 짐을 마음대로 풀어 놓는다.
체크아웃하면 청소부가 방을 통째로 비운다.
손님이 직접 치우겠다고 기억할 필요가 없다.
남기고 싶은 짐은 체크아웃 전에 집으로 옮겨 두면 된다.
Rust 의 임시 디렉토리 · 임시 파일도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 비어 있는 방 번호 받기 | 이름이 겹치지 않는 경로 고르기 (`counter` 를 올려 가며 `exists()` 확인) |
| 체크인 | `TempDir::new` · `TempFile::new` 가 디렉토리 · 파일을 만든다 |
| 방에서 짐 풀기 | 그 경로 안에서 `fs::write` · `fs::read_to_string` 으로 쓰고 읽기 |
| 체크아웃 | 변수가 스코프(`{ }`)를 벗어남 |
| 청소부가 방을 비움 | `Drop::drop` 이 `remove_dir_all` · `remove_file` 을 부른다 |
| 짐을 집으로 옮기기 | `fs::rename` 으로 영구 위치에 옮기기 (persist) |

```text
{
    let tmp = TempDir::new("rust_demo")?;   ── 체크인: <임시 디렉토리>/rust_demo_<PID>_0 생성
    ... tmp.child("data.txt") 에 쓰고 읽기 ...
}                                           ── 체크아웃: drop() → remove_dir_all → 통째로 삭제
```

> **임시 파일** — 작업 중에만 필요하고 끝나면 지워야 하는 파일 · 디렉토리.\
> 예: 변환 중간 결과를 잠깐 적어 두는 `output_0.tmp`.

> **Drop** — 값이 버려질 때 자동으로 불릴 정리 코드를 정하는 Rust 트레이트.\
> 예: `impl Drop for TempDir { fn drop(&mut self) { … } }`.

## 이 주제가 답하려는 질문

1. 임시 디렉토리 · 파일을 어디에, 어떤 이름으로 만들어야 다른 것과 부딪히지 않나?
2. 다 쓴 임시 자원을 지우는 일을 어떻게 잊지 않게 만드나?
3. 이미 있는 파일을 고쳐 쓰다가 프로그램이 죽어도 옛 파일을 어떻게 지키나?
4. 임시로 만든 파일을 조건에 따라 남기고 싶을 때는 어떻게 하나?

## 동작 방식

### (1) 겹치지 않는 이름 고르기 — `TempDir::new`

**언제 쓰나** — 여러 번 실행되거나 여러 프로세스가 동시에 도는 프로그램이 각자 자기만의 임시 디렉토리를 가져야 할 때.

```text
TempDir::new("rust_demo")
   │
   ├─ counter = 0
   ├─ 후보 = temp_dir() / "rust_demo_<PID>_0"
   │     ├─ 없음 → create_dir_all(후보) → Ok(TempDir { path })
   │     └─ 있음 → counter += 1 → 후보 = …_<PID>_1 → 다시 확인
   └─ counter 가 1000 을 넘으면 → Err(ErrorKind::Other, "임시 디렉토리 생성 실패")
```

- 바탕 위치는 `std::env::temp_dir()` 이 알려 주는 OS 의 임시 디렉토리다(예: `/tmp`).
- 이름에 `std::process::id()`(현재 프로세스 번호)를 넣어 다른 프로세스와 겹칠 일을 줄인다.
- 같은 프로세스 안에서 여러 개를 만들면 `counter` 로 구별한다.
- `exists()` 로 비었는지 본 다음에 만들기 때문에, 확인과 생성 사이의 틈이 남는다(「어디서 틀리나 1」).
- `counter > 1000` 은 끝없이 도는 것을 막는 안전장치다.

> **PID** — 운영체제가 실행 중인 프로세스마다 붙이는 번호.\
> 예: `std::process::id()` 가 돌려주는 `u32` 값.

### (2) 스코프가 끝나면 지운다 — `impl Drop for TempDir`

**언제 쓰나** — 「다 쓰면 지운다」를 사람이 기억하지 않고 언어가 대신 챙기게 하고 싶을 때.

```text
fn main() {
    {                                   
        let tmp = TempDir::new(..)?;    ← 디렉토리 생성
        tmp.child("data.txt") 쓰기      
        tmp.child("sub") 만들고 nested.txt 쓰기
    }                                   ← tmp 가 버려짐 → drop(&mut tmp)
                                           → fs::remove_dir_all(path)  (안의 파일·하위 디렉토리까지 전부)
    println!("스코프 벗어남 -> 자동 삭제됨");
}
```

- 변수가 자기 스코프의 `}` 에 닿으면 Rust 가 `drop` 을 자동으로 부른다.
- `drop` 안의 `fs::remove_dir_all` 은 하위 디렉토리와 파일을 모두 지운다.
- 지우기 실패는 `let _ = …` 로 버린다 — 이미 다른 곳에서 지웠을 수도 있기 때문이다.
- `drop` 은 반환값이 `()` 라서 오류를 `?` 로 위에 돌려줄 길이 없다.
- 이렇게 「자원을 쥔 값의 수명 = 자원의 수명」으로 묶는 방식을 RAII 라고 부른다.

> **스코프** — 변수가 살아 있는 코드 구간, 보통 `{` 부터 짝이 되는 `}` 까지.\
> 예: 블록 안에서 선언한 `tmp` 는 블록의 `}` 에서 버려진다.

> **RAII** — 자원을 얻는 일을 값의 생성에, 놓는 일을 값의 소멸에 묶는 설계 방식.\
> 예: `TempDir` 값이 사라지면 디렉토리도 사라진다.

### (3) 핸들을 쥔 임시 파일 — `TempFile`

**언제 쓰나** — 경로만이 아니라 열린 파일 핸들까지 함께 들고 다니며 바로 쓰고 싶을 때.

```text
TempFile::new(parent.path(), "output")
   ├─ 후보 = parent / "output_0.tmp" → 없으면 File::create → TempFile { path, file: Some(file) }
   └─ 있으면 output_1.tmp, output_2.tmp … (상한 없음)

writeln!(tmp.file_mut(), "테스트 데이터")?;   ← file_mut(): Option 안의 File 을 &mut 로 빌려줌
tmp.file_mut().flush()?;

} ← drop:
     1) self.file.take()        → Option 에서 File 을 꺼내 바로 버림 → 핸들 닫힘
     2) fs::remove_file(path)   → 파일 삭제 (실패는 무시)
```

- 필드를 `Option<fs::File>` 으로 둔 까닭은 `drop` 에서 `take()` 로 핸들을 먼저 꺼내 닫기 위해서다.
- `take()` 는 `Option` 을 `None` 으로 바꾸고 안의 값을 꺼내 준다 — 꺼낸 값을 아무 데도 담지 않으므로 그 자리에서 버려지고, 파일이 닫힌다.
- 원본은 「파일 먼저 닫기」를 정리 순서로 정해 둔다 — 열린 채로 지우려 하면 문제가 되는 환경이 있다(「구현 세부사항 대 언어 보장」).
- `file_mut()` 의 `unwrap()` 은 「`drop` 이전에는 늘 `Some`」이라는 가정에 기댄다.
- 이름에 PID 가 없다 — 이미 겹치지 않게 만든 디렉토리(`parent`) 안에 만든다는 전제다.
- 원본 예제는 같은 파일을 `fs::File::open` 으로 따로 열고 `BufReader` 로 감싸 줄 단위로 다시 읽는다.

> **파일 핸들** — 운영체제가 열린 파일을 가리키려고 내주는 손잡이, Rust 에서는 `fs::File` 값.\
> 예: `fs::File::create(&path)?` 가 돌려주는 값.

> **`Option::take`** — `Option` 을 `None` 으로 비우고 원래 들어 있던 값을 돌려주는 메서드.\
> 예: `self.file.take()` 뒤 `self.file` 은 `None` 이다.

### (4) 쓰고 나서 바꿔치기 — `safe_write` (write-then-rename)

**언제 쓰나** — 설정 파일처럼 「반쯤 쓰인 상태」로 남으면 안 되는 파일을 고쳐 쓸 때.

```text
safe_write(".../config.json", 내용)
   │
   ├─ dir       = target.parent()  (없으면 ".")
   ├─ temp_path = dir / ".config.json.tmp"      ← 같은 디렉토리, 앞에 점 · 뒤에 .tmp
   ├─ fs::write(temp_path, 내용)                ← 여기서 죽으면 config.json 은 옛 내용 그대로
   └─ fs::rename(temp_path, target)             ← 한 번에 교체, 임시 파일 이름은 사라짐
```

- 내용을 곧장 `config.json` 에 쓰면, 쓰는 도중에 죽었을 때 파일이 반쯤 잘린 채 남는다.
- 먼저 임시 파일에 다 쓰고, 마지막에 `rename` 한 번으로 바꿔치기하면 바깥에서는 「옛 파일」 아니면 「새 파일」만 보인다.
- 원본은 이 교체가 원자적이라고 본다 — 단 같은 파일시스템 안일 때만이다(POSIX `rename` 의 규약).
- 그래서 임시 파일을 대상과 **같은 디렉토리**에 만든다.
- 원본은 이것을 「안전한 파일 업데이트의 표준」이라 부른다.

> **원자적** — 중간 상태가 바깥에 보이지 않고, 전부 일어났거나 전혀 안 일어났거나 둘 중 하나인 성질.\
> 예: `rename` 직후 `config.json` 은 옛 내용이거나 새 내용이지, 반쪽이 아니다.

### (5) 임시를 영구로 — persist 패턴

**언제 쓰나** — 작업이 성공했을 때만 결과 파일을 남기고, 실패하면 임시 파일째 버리고 싶을 때.

```text
persist_temp.tmp 에 "영구 보관할 데이터" 쓰기
        │
        └─ fs::rename(persist_temp.tmp, permanent.txt)   ← persist = rename
```

- 원본은 tempfile 크레이트의 `NamedTempFile::persist()` 가 하는 일을 `rename` 으로 흉내 낸다.
- 임시 이름에서 정식 이름으로 옮겨 주면 「임시」 딱지가 떨어진다.
- 크레이트의 `persist()` 를 쓰면 그 파일은 `Drop` 때 지워지지 않는다 — 조건부 영구 보관이 된다.
- 다만 원본 예제의 `permanent.txt` 는 `parent`(임시 디렉토리) **안**에 있으므로, `parent` 가 버려질 때 함께 지워진다(「어디서 틀리나 5」).

### (6) 실제 tempfile 크레이트

**언제 쓰나** — 직접 구현 대신 실무 코드에서.

```text
Cargo.toml:  tempfile = "3"

tempfile::NamedTempFile::new()?   이름 있는 임시 파일 → file.path() 로 경로, file.persist("target.txt")? 로 영구 보관
tempfile::tempfile()?             이름 없는 임시 파일 (원본: "더 안전")
tempfile::tempdir()?              임시 디렉토리 → dir.path().join("file.txt"), Drop 시 자동 삭제
```

- 원본 주석에 따르면 실제 크레이트는 OS 차원의 보안(권한, 경쟁 방지)까지 처리해 준다.
- 이 문서의 `TempDir` · `TempFile` 은 그 패턴을 표준 라이브러리만으로 흉내 낸 학습용이다.

## 문법 — 형태와 규칙

```rust
use std::fs;
use std::path::PathBuf;

struct Cleanup { path: PathBuf }

impl Drop for Cleanup {
    fn drop(&mut self) {
        let _ = fs::remove_file(&self.path); // 실패해도 무시
    }
}

fn main() -> std::io::Result<()> {
    let p = std::env::temp_dir().join("demo_cleanup.txt");
    fs::write(&p, "hi")?;
    let _guard = Cleanup { path: p.clone() };
    println!("{}", fs::read_to_string(&p)?);
    Ok(())
} // _guard 가 버려지며 파일 삭제
```

- `impl Drop for 타입 { fn drop(&mut self) { … } }` — 정리 코드는 여기에 쓴다.
- `drop` 은 직접 부르지 않는다. 일찍 버리고 싶으면 `drop(값)` 함수(`std::mem::drop`)로 값을 넘긴다.
- `drop` 은 `()` 를 돌려주므로 안에서 `?` 를 쓸 수 없다 — 실패는 `let _ = …` 로 버리거나 따로 기록한다.
- 경로는 소유하는 `PathBuf` 로 필드에 담고, 바깥에는 `&Path` 로 빌려준다(`fn path(&self) -> &Path`).
- `path.join(name)` 은 새 `PathBuf` 를 돌려준다(`child` 메서드의 몸통).

원본에 나오는 함수 정리:

| 함수 | 하는 일 |
|---|---|
| `std::env::temp_dir()` | OS 임시 디렉토리 경로 |
| `std::process::id()` | 현재 프로세스 번호 |
| `fs::create_dir_all(p)` | 중간 디렉토리까지 만들기 |
| `fs::create_dir(p)` | 디렉토리 하나 만들기 |
| `fs::remove_dir_all(p)` | 디렉토리 트리 전체 삭제 |
| `fs::remove_file(p)` | 파일 삭제 |
| `fs::File::create(p)` | 파일을 만들고 쓰기용 핸들 받기 |
| `fs::File::open(p)` | 읽기용 핸들 받기 |
| `fs::write(p, s)` · `fs::read_to_string(p)` | 한 번에 쓰기 · 읽기 |
| `fs::rename(a, b)` | 이름 바꾸기 · 옮기기 (persist 의 실체) |
| `BufReader::new(f).lines()` | 줄 단위 읽기 |
| `p.display()` | 경로를 출력용으로 |

## 어디서 틀리나

### 1. 확인과 생성 사이에 틈이 있다

`if !path.exists()` 로 확인한 다음 `create_dir_all` · `File::create` 로 만든다.
그 사이에 다른 프로세스가 같은 이름을 먼저 만들면, 두 쪽이 같은 경로를 「내 것」으로 여길 수 있다.
원본이 말하는 「경쟁 방지」는 실제 tempfile 크레이트가 맡는 몫이다.

> **경쟁 조건** — 두 실행 흐름의 순서에 따라 결과가 달라지는 결함.\
> 예: 확인(exists)과 생성(create) 사이에 남이 끼어드는 경우.

### 2. 두 생성자의 「포기 조건」이 다르다

`TempDir::new` 는 `counter` 가 1000 을 넘으면 `Err` 를 돌려준다.
`TempFile::new` 에는 그런 상한이 없다 — 빈 이름이 나올 때까지 계속 돈다.
`File::create` 가 실패하면 그때는 `?` 로 오류가 나간다.

### 3. 열린 핸들을 그대로 두고 지우지 않는다

`TempFile::drop` 은 `self.file.take()` 로 핸들을 먼저 닫고 나서 `remove_file` 을 부른다.
이 순서를 바꾸면 원본이 의도한 「먼저 닫기」가 깨진다.

### 4. 정리 실패는 조용히 묻힌다

`let _ = fs::remove_dir_all(..)` 는 실패해도 아무 말이 없다.
지우지 못한 임시 디렉토리가 남아도 프로그램은 알아채지 못한다.

### 5. 「영구」는 부모보다 오래 살지 못한다

원본 예제의 `config.json` 과 `permanent.txt` 는 `parent`(임시 디렉토리) 안에 있다.
`parent` 는 `main` 끝에서 버려지고, 그때 `remove_dir_all` 이 이 둘까지 지운다.
persist 로 남기려면 대상 경로가 정리될 디렉토리 바깥이어야 한다.

### 6. rename 의 원자성은 같은 파일시스템에서만이다

`safe_write` 가 임시 파일을 대상과 같은 디렉토리에 두는 까닭이 이것이다.
임시 파일을 `std::env::temp_dir()` 같은 다른 곳에 두면 다른 파일시스템일 수 있고, 그러면 원자적 교체를 기대할 수 없다.

### 7. 스코프를 잘못 잡으면 너무 일찍 · 너무 늦게 지워진다

원본은 `parent` 를 블록 **밖**에 두어 섹션 2~4 내내 살려 둔다.
섹션 1 의 `tmp` 는 블록 **안**에 두어 블록이 끝날 때 지운다.
`let _ = TempDir::new(..)?;` 처럼 `_` 에 담으면 값이 그 문장 끝에서 곧바로 버려져 디렉토리도 바로 지워진다 — 살려 두려면 `_guard` 처럼 이름 있는 변수에 담는다.

### 8. `safe_write` 의 `unwrap`

`target.file_name().unwrap()` 은 파일 이름이 없는 경로(예: `..` 로 끝나는 경로)에서 패닉한다.
`target.parent()` 는 `unwrap_or(Path::new("."))` 로 현재 디렉토리를 대신 쓴다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 변수가 스코프를 벗어나면 `drop` 이 불린다 | 언어(Rust) — 정상적으로 스코프를 빠져나갈 때. 프로세스가 강제로 끝나는 경우는 별개다 (확인 필요) |
| `rename` 이 같은 파일시스템에서 원자적이다 | 운영체제 · 파일시스템(원본 주석: POSIX 규약). Rust 언어가 약속하는 것이 아니다 |
| 임시 디렉토리가 `/tmp` 다 | OS · 환경 설정. `/tmp` 는 예일 뿐이다 |
| 열린 파일을 먼저 닫아야 지울 수 있다 | 운영체제마다 다르다 (확인 필요) |
| PID 를 이름에 넣으면 다른 프로세스와 겹치지 않는다 | OS 는 동시에 살아 있는 프로세스끼리만 번호를 다르게 준다. 끝난 프로세스의 번호는 다시 쓰일 수 있다 (확인 필요) |
| 원본 주석 「`flush()` → 디스크에 즉시 반영」 | 의심스럽다 — `fs::File` 은 사용자 공간 버퍼가 없어 `flush` 가 하는 일이 거의 없고, 디스크까지 내려보내는 것은 `sync_all` 의 일로 알려져 있다 (확인 필요) |
| 원본 문구 「쓰기 중 크래시해도 기존 파일 손상 없음」 | 쓰는 도중 프로세스가 죽는 경우에는 맞다. 전원이 나가는 경우에는 `rename` 전에 내용을 디스크에 동기화하지 않으면 새 파일이 비어 있을 수 있다는 지적이 있다 (확인 필요) |
| 권한 · 경쟁 방지 처리 | tempfile 크레이트의 구현(원본 주석). 이 문서의 직접 구현은 하지 않는다 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 테스트마다 깨끗한 작업 공간 | 임시 디렉토리(`tempdir()` · `TempDir`) | 고정 경로 `./test_out` 재사용 |
| 중간 결과를 잠깐 적기 | 임시 파일(`NamedTempFile` · `tempfile()`) | 작업이 끝난 뒤 손으로 지우기 |
| 설정 파일 고쳐 쓰기 | write-then-rename (같은 디렉토리) | 대상 파일에 곧장 덮어쓰기 |
| 성공했을 때만 결과 남기기 | 임시 파일 → `persist` / `rename` | 처음부터 최종 경로에 쓰기 |
| 실무 코드 | tempfile 크레이트 | 학습용 직접 구현(경쟁 처리 없음) |

## 핵심 문장

1. **정리는 `Drop` 에 맡긴다** — 임시 자원을 쥔 값이 스코프를 벗어나면 `drop` 이 지운다.
2. **이름은 겹치지 않게 고른다** — 접두사 + PID + 카운터, 단 확인과 생성 사이의 틈은 남는다.
3. **파일은 닫고 나서 지운다** — `Option` 에 담아 `take()` 로 먼저 닫는다.
4. **고쳐 쓰기는 「임시에 쓰고 rename」** — 같은 디렉토리에 두어야 교체가 원자적이다.
5. **persist 는 rename 이다** — 임시 이름을 정식 이름으로 바꿔 자동 삭제에서 빼낸다.

## 관련 자료

- `file-read-write` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `path-operations` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `error-io` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/rust/io-serde.json` 의 `tempfile`

## 용어 풀이

- **임시 파일** — 작업 중에만 필요하고 끝나면 지울 파일 · 디렉토리.
- **`Drop`** — 값이 버려질 때 불릴 정리 코드를 정하는 트레이트.
- **RAII** — 자원의 획득 · 해제를 값의 생성 · 소멸에 묶는 설계.
- **스코프** — 변수가 살아 있는 코드 구간.
- **`PathBuf` / `Path`** — 소유하는 경로 / 빌린 경로(슬라이스).
- **PID** — 실행 중인 프로세스의 번호, `std::process::id()`.
- **파일 핸들** — 열린 파일을 가리키는 손잡이, `fs::File`.
- **`Option::take`** — `Option` 을 비우고 안의 값을 꺼내는 메서드.
- **원자적** — 중간 상태가 보이지 않는 성질.
- **write-then-rename** — 임시 파일에 다 쓴 뒤 `rename` 으로 대상과 바꿔치기하는 패턴.
- **persist** — 임시 파일을 영구 위치로 옮겨 자동 삭제에서 빼내는 일.
- **경쟁 조건** — 실행 순서에 따라 결과가 갈리는 결함.
- **`flush`** — 쓰기 버퍼에 쌓인 내용을 내보내는 호출.
- **`NamedTempFile`** — tempfile 크레이트의 이름 있는 임시 파일.
- **`tempfile::tempfile()`** — tempfile 크레이트의 이름 없는 임시 파일.
- **`tempfile::tempdir()`** — tempfile 크레이트의 임시 디렉토리.

## 더 들어가면

- `std::process::exit` 로 끝내거나, `panic = "abort"` 로 빌드했거나, 프로세스가 신호로 죽으면 `drop` 이 불리지 않아 임시 파일이 남는다 (확인 필요).
- 확인과 생성 사이의 틈은 `fs::OpenOptions::new().write(true).create_new(true)` 처럼 「없을 때만 만들고, 있으면 실패」하는 호출로 없앨 수 있다. `fs::create_dir` 도 이미 있으면 실패하지만 `create_dir_all` 은 이미 있어도 성공하는 것으로 알려져 있다 (확인 필요).
- 열린 파일을 지우는 일은 Unix 계열에서는 대체로 되지만 Windows 에서는 막히는 경우가 많다 — 원본의 「먼저 닫기」가 의미를 갖는 자리다 (확인 필요).
- write-then-rename 을 전원 장애에도 버티게 하려면 임시 파일에 `sync_all` 을 부른 뒤 `rename` 하고, 디렉토리도 동기화하라는 권고가 있다 (확인 필요).
- 이름 없는 임시 파일은 경로가 없어 다른 프로세스가 이름으로 열 수 없고, 프로그램이 죽어도 OS 가 정리한다는 점에서 더 안전하다고 알려져 있다. 구현은 OS 마다 다르다 (확인 필요).
- tempfile 크레이트의 `TempDir` 에는 자동 삭제를 끄는 메서드가 따로 있다 (이름 · 버전 확인 필요).
