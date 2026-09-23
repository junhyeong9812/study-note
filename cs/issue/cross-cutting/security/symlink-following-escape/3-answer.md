# cs/issue/security/symlink-following-escape — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 사건 기록 원문 대조 작성. 복습 전 읽지 말 것.

태그: `least-privilege`

## 정답
<!-- 질문 1:1 대응 -->

1. **stat vs lstat.** `stat`류(`metadata`, `exists`, `is_file`)는 링크를 **따라가** 링크가 가리키는 대상의 정보를 돌려준다.\
`lstat`류(`symlink_metadata`, `is_symlink`)는 링크를 따라가지 않고 **링크 자체**를 본다.\
디렉터리를 가리키는 링크를 `metadata`로 판정하면 "디렉터리"로 보고되고, 그대로 재귀 삭제하면 **링크가 아니라 링크 너머의 실제 폴더 내용**이 지워진다.\
그래서 삭제 판정은 `symlink_metadata`로 하고, 링크면 링크만 제거(`remove_file`), 진짜 디렉터리일 때만 재귀 삭제한다.
   > **lstat** — 경로의 마지막 성분이 심볼릭 링크여도 따라가지 않고 링크 자체의 메타데이터를 돌려주는 시스템 호출.

2. **dangling 링크 이중 탈출.** `exists()`는 링크를 따라가 대상을 찾는데 대상이 없으니 **False**("없음")를 돌려준다 → 중복 검사 통과.\
그다음 `write_text()`는 링크를 따라가 **대상 위치(`/outside/new.txt`)에 파일을 만든다** → 경로 한정도 뚫린다.\
검사는 "대상 없음"을 봤고 쓰기는 "대상 위치"에 썼다 — 같은 링크를 두 연산이 다르게 해석했기 때문에 불변식 두 개가 한 번에 무너진다.\
교정은 존재 판정을 `is_symlink() or exists()`로(링크 = 존재) 바꾸는 것이다.
   > **dangling symlink** — 가리키는 대상이 존재하지 않는 심볼릭 링크.

3. **O_EXCL이 더 강한 이유.** "`is_symlink()` 검사 → 생성"은 두 단계라 그 사이에 누군가 링크를 만들면 뚫린다(TOCTOU).\
`open(path, "x")`는 O_CREAT|O_EXCL로 **"없을 때만 만든다"를 커널이 한 syscall로 원자적으로** 판정하고, 경로가 dangling 링크를 포함해 어떤 형태로든 존재하면 `FileExistsError`를 낸다.\
그래서 사전 검사는 친절한 오류 메시지용으로 남기고, 실제 방어는 O_EXCL이 맡는다("검사만" 방식은 경쟁 창 잔존으로 선택하지 않은 방법).
   > **TOCTOU** — time-of-check to time-of-use. 검사 시점과 사용 시점 사이에 상태가 바뀌어 검사가 무의미해지는 경쟁 조건.

4. **최종 성분만 검사.** `base/<오늘날짜>/<이름>`에서 `<이름>`만 링크·존재 검사를 하면, 중간의 `<오늘날짜>` 디렉터리가 ROOT 밖을 가리키는 링크일 때 최종 경로는 "링크 아님·없음"으로 멀쩡해 보인다.\
그러나 `mkdir(parents=True)`는 중간 링크를 따라가 **ROOT 밖에 폴더와 파일을 만든다**.\
포함 여부는 이름 문자열이 아니라 **실제로 쓰게 될 위치**의 성질이므로, 전체 경로를 `resolve()`해(중간 링크를 모두 풀고) 그 실경로가 ROOT 아래인지 본다.\
이때도 문자열 `startswith`는 `/root-evil` 같은 형제 경로를 통과시키므로 `root in resolved.parents`처럼 경로 성분 단위로 비교한다.

5. **분기 패리티.** 생성 분기가 O_EXCL로 링크를 막아도, 갱신 분기의 `is_file()/read_text/write_text`는 링크를 따라간다.\
검증된 폴더 안에 `doc.md -> /외부/파일`을 두면 폴더 경로 검증은 통과하고, 갱신 분기가 **ROOT 밖 파일을 읽고 내용을 덧붙인다**.\
경로 검증을 "디렉터리까지만" 하고 그 안의 파일 이름을 따라 열면 파일 자체가 링크인 경우를 놓친다.\
패리티란 생성·읽기·갱신·이동 **모든 분기가 같은 링크 정책**(여기선 "기존 파일이 링크면 거절")을 갖는 것이다.

6. **move의 두 얼굴.** 같은 파일시스템에서 `move`는 `rename`이라 대상 경로의 디렉터리 엔트리를 원자적으로 교체한다(대상 링크를 따라가지 않음).\
다른 파일시스템(예: `/tmp`가 tmpfs)에서는 rename이 불가능해 **copy + 삭제로 폴백**하고, copy는 대상이 링크면 **링크를 따라가 대상 위치에 쓴다**.\
코드는 한 줄 그대로인데 배포 환경의 마운트 구성에 따라 보안 성질이 바뀌므로, 대상에 링크 검사를 따로 두고 덮어쓰기면 기존 대상을 먼저 `unlink`한다.

7. **고정 /tmp 경로 선점.** world-writable 디렉터리의 **예측 가능한 이름**은 공격자가 먼저 같은 이름의 링크를 만들어 둘 수 있다.\
`create_dir_all`은 이미 있는 경로(링크 포함)를 성공으로 통과하므로, 이후 작업이 공격자가 가리킨 곳에서 일어난다.\
원자적 `create_dir`은 "이미 있으면 실패"로 선점을 드러내고, `symlink_metadata` 재검사는 링크를 거절하며, 소유자 확인은 남이 만든 디렉터리를 거절하고, 0700은 다른 계정의 접근을 막는다(권한 설정 실패도 전파).\
실행별 임의 이름이 더 강하지만 고정 경로가 기능상 필요한 경우 이 3중 하드닝으로 대신한다.
   > **world-writable** — 모든 사용자가 쓸 수 있는 디렉터리(`/tmp` 등). 여기서 만든 이름은 다른 사용자와 경쟁한다.

## 문제 구조 (추상화 코드)

### 변형 A — 존재 검사는 링크 비추종, 쓰기는 링크 추종 (dangling 링크)
① 문제 코드
```python
target = resolve_under_root(root, rel)
if target.exists():                     # dangling 링크 → False
    raise Conflict()
target.write_text(content)              # 링크를 따라가 ROOT 밖에 생성
```
② 고친 코드
```python
if target.is_symlink() or target.exists():          # 링크 자체도 "존재"
    raise Conflict()
try:
    with open(target, "x", encoding="utf-8") as f:   # O_CREAT|O_EXCL — 원자적, 링크 비추종
        f.write(content)
except FileExistsError:
    raise Conflict()                                  # 같은 실패 유형은 같은 응답
# 테스트: 상태코드뿐 아니라 assert not outside_path.exists() 로 부작용 부재를 단언
```
무엇이 깨졌나: 한 경로를 검사와 쓰기가 다르게 해석해 중복 검사와 경로 한정이 동시에 무력화됐다.\
같은 구조: rename의 덮어쓰기 금지 검사가 `to.exists()`라 dangling 링크를 덮어씀 → `symlink_metadata(to).is_ok()`로 판정, 새 파일 생성은 `create_new(true)`.\
같은 구조: 파일 검색이 `file_type()`(링크 자체 타입)으로 거른 결과에 디렉터리를 가리키는 링크가 섞여 파일처럼 열릴 위험 → `is_file()`만 결과에 포함.

### 변형 B — 재귀 삭제가 디렉터리 링크를 따라감
① 문제 코드
```rust
let md = std::fs::metadata(p)?;          // 링크 추종 → 대상 디렉터리로 판정
if md.is_dir() { std::fs::remove_dir_all(p)? }   // 링크 너머 실제 폴더를 비움
```
② 고친 코드
```rust
let md = std::fs::symlink_metadata(p)?;  // 링크 자체를 본다
if md.is_dir() { std::fs::remove_dir_all(p)? }   // 진짜 디렉터리만 (UI 확인 필수)
else { std::fs::remove_file(p)? }                // 링크는 링크만 제거
```
무엇이 깨졌나: "링크"와 "링크가 가리키는 것"을 구분하지 않아 삭제 범위가 경계 밖으로 번질 수 있었다(설계 단계 방어).

### 변형 C — 최종 성분만 검사 (중간 디렉터리 링크)
① 문제 코드
```python
base = root / "items" / today           # today 디렉터리가 ROOT 밖 링크일 수 있음
target = base / validate_name(name)     # 이름 성분만 검증
if target.is_symlink() or target.exists():
    raise Conflict()
target.mkdir(parents=True)              # 중간 링크를 따라 ROOT 밖에 생성
```
② 고친 코드
```python
target = resolve_safe_path(root, f"items/{today}/{name}")   # 전체 경로 resolve(strict=False)
#   내부: p = (root / rel).resolve(); if root.resolve() not in p.parents: raise BadRequest
if target.is_symlink() or target.exists():
    raise Conflict()
target.mkdir(parents=True)
```
무엇이 깨졌나: 포함 검사를 이름 문자열로 했고, 실제 쓰기 위치를 결정하는 중간 성분을 보지 않았다.

### 변형 D — 생성 분기와 갱신 분기의 링크 정책 비대칭
① 문제 코드
```python
folder = resolve_safe_path(root, rel_folder)   # 폴더까지만 검증
doc = folder / "doc.md"
if doc.is_file():                               # 링크 추종
    doc.write_text(marker + doc.read_text())    # ROOT 밖 파일을 읽고 덧붙임
else:
    with open(doc, "x") as f: f.write(seed)     # 생성 분기만 링크 비추종
```
② 고친 코드
```python
doc = folder / "doc.md"
if doc.is_symlink():
    raise BadRequest()                          # 모든 분기 앞에서 같은 정책
if doc.exists():
    doc.write_text(marker + doc.read_text())
else:
    with open(doc, "x") as f: f.write(seed)
# 테스트: 링크 대상(ROOT 밖 파일) 내용이 변하지 않았음을 단언
```
무엇이 깨졌나: 한 분기만 막고 다른 분기를 열어 두어 검증 경계가 파일 수준에서 우회됐다.

### 변형 E — 이동 유틸이 다른 파일시스템에서 copy로 폴백
① 문제 코드
```python
with TemporaryDirectory() as td:            # /tmp 가 다른 FS(tmpfs)일 수 있음
    out = render_to(td)
    shutil.move(out, target)                # 다른 FS → copy → 대상 링크 추종
```
② 고친 코드
```python
if target.is_symlink():
    raise BadRequest()
with TemporaryDirectory() as td:
    out = render_to(td)
    if proc.returncode != 0 or not out.is_file():
        raise ServerError()                 # 성공 확인 전엔 최종 위치에 아무것도 두지 않음
    if overwrite and target.exists():
        target.unlink()                     # 기존 대상 제거 후 생성
    shutil.move(out, target)
```
무엇이 깨졌나: 같은 코드의 링크 추종 여부가 마운트 구성에 따라 조용히 바뀌었다.

### 변형 F — 공유 쓰기 디렉터리의 고정 경로 선점
① 문제 코드
```rust
const WORKDIR: &str = "/tmp/app-work";      // 예측 가능한 이름
std::fs::create_dir_all(WORKDIR)?;          // 선점된 링크도 "성공"으로 통과
```
② 고친 코드
```rust
fn harden_workdir(p: &Path) -> Result<()> {
    if let Err(e) = std::fs::create_dir(p) {                // 원자적 생성
        if e.kind() != ErrorKind::AlreadyExists { return Err(e.into()); }
    }
    let md = std::fs::symlink_metadata(p)?;                 // 링크 거절
    ensure!(md.file_type().is_dir() && !md.file_type().is_symlink());
    ensure!(md.uid() == current_uid());                     // 남이 만든 디렉터리 거절
    std::fs::set_permissions(p, Permissions::from_mode(0o700))?;   // 실패 전파
    ensure!(!std::fs::symlink_metadata(p)?.file_type().is_symlink()); // 재검사
    Ok(())
}
// 임시 디렉터리 경로도 환경변수 가정 대신 고정하고 테스트로 못박음
```
무엇이 깨졌나: 공유 디렉터리의 이름을 먼저 차지한 쪽이 이기는 경쟁에서, 기존 경로를 무조건 받아들였다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log
