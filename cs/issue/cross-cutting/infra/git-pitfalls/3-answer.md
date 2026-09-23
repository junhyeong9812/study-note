# cs/issue/infra/git-pitfalls — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-23) — 이슈 README·코드 기준. 복습 전 읽지 말 것.

태그: —

## 정답
<!-- 질문 1:1 대응 -->

1. **git 바이너리 자체의 검사**다(도커가 아니다). git 2.35.2부터, repo 디렉토리의 **소유자와 git을 실행한 사용자가 다르면** 거부한다. 컨테이너 프로세스는 root(uid 0)로 돌고, 마운트된 호스트 디렉토리의 소유자는 호스트 사용자(uid 1000)다. 도커는 기본 설정에서 uid를 격리하지 않으므로(호스트와 같은 숫자 uid를 그대로 씀) 이 소유자≠실행자 비교가 **컨테이너 안에서도 그대로 성립**한다.
   > **dubious ownership** — git이 "이 repo는 실행자 소유가 아니다"라고 판단해 작업을 거부하는 안전 검사.

2. 위협은 **공유 머신**에서 남이 만들어둔 repo에 악성 설정(예: `core.fsmonitor`에 임의 명령)을 심어두면, 그 폴더에서 git을 실행한 **다른 사용자의 권한으로** 그 명령이 실행되는 것(CVE-2022-24765). 끌지 판단하는 기준 = "그 위협 모델의 전제(신뢰 불가한 타인의 repo)가 우리 상황에서 성립하는가". 이 컨테이너는 ① 우리가 빌드한 배포 전용이고 ② 접근 가능한 디렉토리가 마운트로 고정된 3개뿐이며 ③ 실행 명령도 allowlist로 고정 — 신뢰 경계가 이미 컨테이너 바깥에서 그어져 있어 전제가 불성립한다. 그래서 `git config --global --add safe.directory '*'`로 끄는 게 정당했다.
   > **CVE-2022-24765** — dubious ownership 가드가 생긴 원인이 된 취약점(공유 머신의 악성 repo 설정 실행).

3. git은 빈 디렉토리를 추적하지 않으므로, 브랜치를 새로 checkout하면 빈 `src/app/api`가 **사라진다**. 그 상태에서 `> src/app/api/search/route.ts` 리다이렉션은 없는 디렉토리를 만들어주지 않아 **쓰기 실패**한다(`그런 파일이나 디렉터리가 없습니다`). 그런데 Next 빌드는 "없는 라우트"를 오류로 보지 않아 `✓ Compiled successfully`로 **통과** — 파일이 안 생겼는데 빌드는 초록불이 되는 조용한 실패다. 조합 = (빈 디렉토리 미추적) × (관대한 리다이렉션 실패) × (관대한 빌드).
   > **리다이렉션 `> 경로`** — 셸에서 출력을 파일로 보내는 것. 대상 디렉토리가 없으면 만들지 않고 그냥 실패한다.

4. git 기본값 `core.quotepath=true`는 비ASCII 경로를 사람이 보기 "안전하게" 이스케이프해 출력한다 — 한글이 `\352\267\270…`(8진수)로 바뀌고 경로 전체가 따옴표로 감싸인다. 이 **사람용 출력**을 그대로 **파일 경로**(기계용 입력)로 쓰면, 실제로는 존재하지 않는 이름이 되어 `No such file or directory`가 난다. `git -c core.quotepath=off ...`로 이스케이프를 끄면 원래 UTF-8 경로가 나온다.
   > **core.quotepath** — git이 비ASCII 파일명을 8진수로 이스케이프해 출력할지 정하는 설정(기본 켜짐).

5. **git의 기본값은 "사람이 공유 머신에서, 눈으로 보며" 쓰는 것을 안전하게 하도록** 맞춰져 있다 — 소유자 검사(남의 repo 조심), 빈 디렉토리 미추적(내용 없는 폴더는 무의미), 경로 이스케이프(터미널에서 안 깨지게). 배포/CI 자동화는 그 전제(사람·공유·눈)와 정반대다 — 통제된 단독 실행자, 디렉토리 구조가 의미, 출력을 기계가 파싱. 그래서 늘 이 세 지점에서 부딪힌다.

6. "그 기본값/가드가 막으려는 위협이 **내 통제된 환경에서 성립하지 않는다**"고 논증할 수 있으면 끈다(safe.directory·quotepath=off — 위협 전제 불성립, 또는 기계용 입력엔 부적절). 반대로 그 함정이 "**내 습관/구조가 git의 성질과 어긋난 것**"이면 습관을 바꾼다(빈 디렉토리는 `.gitkeep`을 넣어 추적하거나 스크립트에 `mkdir -p`를 선행 + 산출물 grep 확인).
   > **.gitkeep** — 빈 디렉토리를 git이 추적하게 하려고 넣는 관습적 빈 파일(git 공식 기능은 아님).

7. **인덱스는 작업트리(체크아웃)에 속한다.** \
   한 작업트리에는 인덱스·HEAD가 하나뿐이다. 작업자 둘이 서로 다른 파일을 고쳐도 `commit -a`/`add -A`/`add .`는 "지금 작업트리의 모든 변경"을 스테이징하므로 상대의 파일까지 담는다. \
   같은 이유로 새 브랜치를 checkout해도 staged 변경이 따라오고, `commit`은 방금 add한 파일이 아니라 **인덱스 전체**를 기록한다. \
   격리 단위는 파일이 아니라 **공유 도구 상태(작업트리)**다 — 병렬 작업은 작업트리를 나누거나(`git worktree`), 순차로 하거나, 최소한 경로를 지정해 스테이징(`git add <경로>`)한다.
   > **인덱스(staging area)** — 다음 커밋의 스냅샷을 담는 파일. 작업트리마다 하나이며 브랜치를 바꿔도 유지된다.

8. **안 된다 — ref는 커밋 객체만 되살린다.** \
   백업 ref와 reflog는 커밋을 가리킬 뿐이다. 커밋되지 않은 tracked 변경은 object DB에 없으므로 어떤 ref로도 복구할 수 없고, 대상 커밋의 tracked 경로와 겹치는 untracked 파일은 hard reset이 덮어 지운다. \
   그래서 hard reset 전에 작업트리가 dirty면 `stash push --include-untracked`로 먼저 객체 DB에 넣고, 안내 문구는 "복구 가능" 대신 "reset 전 HEAD = <백업 ref>, stash 여부"라는 **사실**로 바꾼다. 복구 명령으로 `reset --hard <ref>`를 제시하면 오히려 보존된 변경을 버리게 유도한다.

9. **untracked 신규 파일이 빠졌다.** \
   `git diff`는 **추적 중인 파일의 변경**만 보인다. 새로 만든 테스트 파일은 아직 untracked라 diff에 없고, 리뷰어는 받은 입력만 보고 "테스트 없음"을 지적한다(오탐). \
   `git add -N`(intent-to-add)을 쓰면 diff에 나타나긴 하지만 **사용자의 인덱스를 바꾼다** — 읽기 목적의 조회가 공유 상태를 변경해서는 안 된다. 대신 untracked 파일을 `git diff --no-index /dev/null <파일>`처럼 인덱스를 건드리지 않는 방법으로 따로 포함한다.
   > **untracked** — 작업트리에 있지만 인덱스에 한 번도 들어간 적 없는 파일. `git diff`·`git restore`·`commit -a`의 대상이 아니다.

## 문제 구조 (추상화 코드)

### 변형 A — 소유자 ≠ 실행자 (dubious ownership · sudo 잔재)

① 문제 구조
```dockerfile
# 배포 컨테이너: root(uid 0) 로 실행, 호스트 사용자(uid 1000) 소유 repo 를 마운트
RUN apt-get install -y git
# → git fetch: fatal: detected dubious ownership
```
```bash
sudo git pull          # .git/objects 에 root 소유 객체 생성
git pull               # 일반 사용자: insufficient permission for adding an object ...
```
② 고친 코드
```dockerfile
RUN git config --global --add safe.directory '*'   # 위협 전제(신뢰 불가한 타인 repo) 불성립을 논증한 뒤에만
```
```bash
sudo chown -R <user>:<user> .git/objects <sudo 로 생긴 디렉토리>   # 소유권 복구
# 규칙: git 에 sudo 금지
```
무엇이 깨졌나: git은 저장소 소유 UID와 실행 UID를 비교하고, 과거 root로 만든 파일은 이후 일반 사용자의 쓰기를 막았다.\
같은 구조: 같은 운영 서버의 다른 기록 — root 컨테이너가 남긴 파일 때문에 pull이 `Permission denied`, 동일하게 chown으로 복구.

### 변형 B — git은 빈 디렉토리를 추적하지 않는다

① 문제 코드
```bash
git checkout -b feature           # 빈 src/app/api 는 추적되지 않아 사라짐
cat > src/app/api/search/route.ts <<'X'   # 없는 디렉토리 → 쓰기 실패
...
X
npm run build                     # 없는 라우트는 오류가 아님 → 초록불
```
② 고친 코드
```bash
mkdir -p src/app/api/search && cat > src/app/api/search/route.ts <<'X'
...
X
npm run build | grep -q '/api/search'   # 산출물(라우트 표)로 확인
```
무엇이 깨졌나: 디렉토리 존재를 전제한 스크립트가 새 checkout에서 조용히 실패했고, 관대한 빌드가 그 실패를 초록불로 덮었다.

### 변형 C — 사람용 출력을 기계용 입력으로 사용 (quotepath)

① 문제 코드
```kotlin
val paths = run("git", "ls-files").lines()     // "docs/\352\267\270..." (8진수 이스케이프 + 따옴표)
paths.forEach { File(it).readText() }          // No such file or directory
```
② 고친 코드
```kotlin
val paths = run("git", "-c", "core.quotepath=off", "ls-files").lines()   // UTF-8 원래 경로
```
무엇이 깨졌나: 터미널 표시용 기본 이스케이프가 켜진 출력을 파일 경로로 그대로 썼다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log

## 방안 비교

같은 원리(git은 인덱스·ref·시퀀서 상태·출력 인용·소유권·ignore 규칙을 암묵 입력으로 쓴다)에서, 위 변형들의 방안은 "가드/기본값을 논증 후 끄기 · 습관 바꾸기"였다. 다른 사건들은 아래 방안들로 대응했다. 멤버가 많아 방안마다 대표만 코드로 보이고 나머지는 한 줄로 적는다.

### 방안 A — 암묵 상태를 선검사하고, 진행 중 상태엔 탈출구를 준다 (도구 래퍼)

① 문제 코드
```ts
const canCommit = staged > 0;                                   // 머지 중(MERGE_HEAD)에도 일반 커밋 가능
const isHead = refs.includes("HEAD");                           // "origin/HEAD" 에도 참 → HEAD 아닌 커밋에 amend 메뉴
```
```rust
fn amend_message(msg) { run_git(&["commit", "--amend", "-m", msg]) }   // 인덱스의 staged 변경까지 흡수
fn uncommit() { run_git(&["reset", "--soft", "HEAD~1"]) }             // revert/rebase 진행 중에도 실행
fn replay(target) { /* target..HEAD 를 "target 의 자손"으로 가정 */ }    // A..B = ^A B (도달 차집합)
```
② 고친 코드
```ts
const canCommit = !status.merging && staged > 0;   // 계속 = commit --no-edit, 중단 = merge --abort
const isHead = refs.some(r => r === "HEAD" || r.startsWith("HEAD -> "));
```
```rust
fn op_in_progress(cwd) -> bool {                   // 시퀀서 상태 파일 검사
    ["MERGE_HEAD", "REVERT_HEAD", "CHERRY_PICK_HEAD"].iter().any(|r| rev_parse_ok(cwd, r))
        || git_path_exists(cwd, "rebase-merge") || git_path_exists(cwd, "rebase-apply")
}
if op_in_progress(cwd) { return Err("진행 중인 작업이 있습니다 — 중단/계속을 먼저".into()); }
if resolve_commit(cwd, "HEAD")? != resolve_commit(cwd, hash)? { return Err("HEAD 커밋만".into()); }
if run_git(cwd, &["diff", "--cached", "--quiet"]).is_err() { return Err("staged 변경 있음".into()); }
if !is_ancestor(cwd, target, orig_head) { return Err("조상이 아님".into()); }   // merge-base --is-ancestor
let r = run_git(cwd, &["rev-parse", "--verify", &format!("{r}^{{commit}}")])?;   // range·revspec 거부, 단일 커밋만
```
무엇이 깨졌나: git의 모드(머지·되돌리기 진행 중)와 명령의 실제 정의(amend = 인덱스 포함, A..B = 도달 차집합)를 래퍼가 모델링하지 않아, 허용되면 안 되는 전이가 열리거나 사용자가 갇혔다.\
같은 구조: 되돌리기 충돌 시 REVERT_HEAD가 남는데 UI가 몰라 빠져나올 수 없음 → reverting 상태 + abort/continue 배너 · 한 줄 입력으로 amend하면 본문·trailer가 사라짐 → 본문이 있으면 전체 편집기로.

### 방안 B — 유실 범위를 명시하고, 복구점을 조작 전에 영속한다

① 문제 코드
```rust
backup_ref(cwd)?;                                  // "이 ref 로 복구 가능" 안내
run_git(cwd, &["reset", "--hard", target])?;       // 미커밋 변경 · 충돌 untracked 는 ref 로 못 되살림
```
```bash
# 롤백 스크립트
git restore -- <files>        # "이번 변경분"이 아니라 HEAD 와의 전체 차이 → 작업 전 사용자 미커밋 변경도 삭제
git diff --quiet && echo ok   # "HEAD 와 같다"만 증명 — 무엇이 사라졌는지는 모름
```
② 고친 코드
```rust
let head = resolve_commit(cwd, target)?;
if op_in_progress(cwd) { return Err(..); }
let backup = backup_ref(cwd)?;                                         // 커밋 복구용
if mode == Hard && !porcelain_status(cwd)?.is_empty() {
    run_git(cwd, &["stash", "push", "--include-untracked", "-m", "pre-reset (auto)"])?;
    stashed = true;
}
run_git(cwd, &["reset", mode.flag(), &head]).map_err(|e| with_note(e, stashed))?;   // 실패해도 "stash됨" 통지
prune_backup_refs(cwd, KEEP /*20*/, &backup);    // best-effort · 방금 만든 ref 보호 · 자기 포맷만 삭제 후보
```
```bash
# 롤백: 착수 전 clean baseline 확인 + 생성 파일 목록 기록
[ -z "$(git status --porcelain)" ] || { echo "dirty — 커밋/stash 먼저"; exit 1; }
# ... 작업 ...
git restore -- <modified>; rm -- <created>      # git clean 금지
```
```python
# 커밋 기반 롤백: 되돌아갈 지점을 작업 전에 영속, tracked 만 원복
persist(prev_sha, prev_branch)
code, _ = await git(repo, "checkout", "-B", branch, sha)   # 로컬 변경 있으면 git 이 거부(fail-closed), untracked .env 보존
if await head(repo) != sha: return error()
```
무엇이 깨졌나: ref·복원 명령이 되살리거나 지우는 범위를 과대/과소평가했고, 되돌아갈 지점을 조작 뒤에야(또는 메모리에만) 알았다.\
같은 구조: 백업 ref가 무한히 쌓여 gc를 막음 → 최근 N개만 best-effort 정리, 타임스탬프 정렬은 시계 역행 시 새 ref를 지울 수 있어 방금 만든 ref는 무조건 보호 · 커밋 전 수정을 확인하려 원본으로 덮어쓴 뒤 `git restore` → HEAD(버그)로 복원돼 수정 소실 — 검증은 수정 커밋 후.

### 방안 C — 워킹트리를 거치지 않는 재생성 + ref CAS (히스토리 재작성)

① 문제 구조
```text
과거 커밋 메시지 수정 = checkout/detach → stash → cherry-pick 리플레이 → checkout -B
 → 충돌·빈 커밋 실패·auto-stash 비원자성·최종 checkout TOCTOU·hook 이 메시지 변경
```
② 고친 코드
```bash
# 가드: 단일 커밋 · 조상 관계 · 범위 안 머지 커밋 없음 · replace refs 없음 · orig_head 스냅샷
new=$(git commit-tree "$target^{tree}" -p "$parent" -F msg.txt)        # 트리 불변, 메시지만 새 객체
for c in $(git rev-list --reverse "$target..$orig_head"); do
  new=$(git commit-tree "$c^{tree}" -p "$new" -F <(git cat-file commit "$c" | sed '1,/^$/d'))
done
git update-ref "refs/heads/$branch" "$new" "$orig_head"   # CAS 한 번: 그 사이 브랜치가 움직였으면 거부
```
무엇이 깨졌나: 메시지만 바꾸면 모든 트리가 같아 패치 재적용이 불필요한데, porcelain 리플레이가 불필요한 경로에서 충돌·부분 실패·경합 창을 만들었다. 커밋은 불변 객체라 "수정" = 새 객체 + ref 이동이다(대가: 서명·hook 미실행, committer 변경).\
같은 구조: 같은 기능의 후속 기록 — 읽기와 ref 갱신 사이 변경(TOCTOU)·비UTF-8 메시지는 원 바이트 그대로 보존.

### 방안 D — 공유 인덱스를 격리하거나 경로를 지정해 스테이징한다

① 문제 코드
```bash
cd ../other-wt && run_tests ; git add -A && git commit -m "..."   # 앞 명령의 cd 가 남아 엉뚱한 체크아웃에 커밋
git add -A                                                          # 런타임 상태 파일·빌드 산출물·남의 작업까지
git add file1 && git commit                                         # 이전부터 staged 된 삭제 수십 건도 함께
```
② 고친 코드
```bash
git -C /abs/repo status -sb                 # 커밋 직전: 어느 트리·브랜치·인덱스인가 재확인
git -C /abs/repo add -- path/a path/b       # 경로 지정 (-a / -A / . 금지)
git -C /abs/repo diff --cached --stat       # 수치가 예상과 다르면 중단
git -C /abs/repo commit -m "..."
# 병렬 작업 = 작업트리당 작업자 1명 (git worktree add) 또는 순차
# 도구의 런타임 상태 디렉토리는 .gitignore
```
무엇이 깨졌나: 인덱스·HEAD·셸 cwd가 작업트리 단위 공유 가변 상태인데, 광역 스테이징과 상대경로 명령이 "지금 어디인가"를 암묵 가정했다.\
같은 구조: 같은 작업트리의 병렬 작업자가 `commit -a`로 서로의 파일을 쓸어 담음(유실 0, 커밋 분리 파괴; 여러 기록) · 셸 cwd 잔류로 본 체크아웃의 개발 브랜치에 오커밋 · 도구가 상태 파일을 "조상에 없으면 현재 cwd에" 만들어 곳곳에 생긴 파일이 `add -A`로 외부 PR 커밋에 유출 → 인덱스만 재작성(filter-branch --index-filter, 스크래치 클론에서 먼저 검증) · 컨테이너가 만든 root 소유 캐시 파일을 `add -A`가 커밋 → 이후 checkout 충돌 · 출처 불명 로컬 변경 일괄 커밋으로 테스트용 설정값이 운영 유입 · 브랜치 파생 시 staged 삭제가 상속돼 함께 커밋.

### 방안 E — untracked를 가시화한다 (diff 기반 입력)

① 문제 코드
```bash
git diff "$BASE" > review_packet.txt        # 신규 파일(untracked) 누락 → "테스트 없음" 오탐
git add -N new_test.py && git diff ...      # 보이긴 하나 사용자 인덱스를 변경
```
② 고친 코드
```bash
git diff --binary "$BASE" -- > packet
git ls-files --others --exclude-standard -z |
  while IFS= read -r -d '' f; do
    [ -L "$f" ] && continue                          # 심링크 분기
    git diff --no-index /dev/null "$f" >> packet     # rc 1 = 차이 있음(정상), rc ≥ 2 = 오류로 기록
  done
```
무엇이 깨졌나: `git diff`는 추적 파일만 보여 "작업트리 변경 전체"와 달랐고, 이를 메우려는 `add -N`은 조회가 공유 상태를 바꾸는 부작용이었다.\
같은 구조: 신규 모듈이 untracked라 로컬에선 동작하고 배포본에선 `ModuleNotFoundError`(작업트리 존재 ≠ 저장소 존재) · 리뷰 입력에서 신규 파일이 빠져 강제 `git add`로 커밋 · 커밋 전 create mode 확인 · 여러 리뷰 입력에서 같은 누락이 반복된 기록.

### 방안 F — ignore 규칙을 명시한다 (앵커 · 추적 중 무효 · 판정 문맥)

① 문제 코드
```gitignore
docs/        # 의도: 루트 문서 폴더 → 실제: 모든 깊이의 docs/ (소스 라우트 디렉토리까지)
uploads/
```
② 고친 코드
```gitignore
/docs/       # 선행 / 로 루트에 앵커
/uploads/
```
```bash
git rm -r --cached docs/     # 이미 추적 중인 파일에는 .gitignore 가 효과 없음
```
무엇이 깨졌나: 앵커 없는 패턴이 트리 전체 깊이에 매칭돼 소스 파일이 한 번도 추적되지 않았고, 로컬에선 동작하다 새 clone 배포에서만 404·크래시가 났다.\
같은 구조: 비앵커 파일 패턴이 라우트 파일을 무시해 새 clone에서만 404 · ignore 판정 라이브러리는 git 저장소 안에서만, 걸어 들어간 루트부터 누적한 규칙으로 판정 → 테스트 temp에 `.git` 필요, ignored 디렉토리 안을 새 루트로 나열하면 자식이 non-ignored로 보여 부모 상태를 자식에 상속.

### 방안 G — 내부 파일 직독 최적화는 불확실하면 원 명령으로 폴백한다

① 문제 코드
```rust
fn head_branch(gitdir) -> String {
    read(gitdir.join("HEAD")).strip_prefix("ref: refs/heads/").to_string()   // 커밋 0개(unborn)에도 "main"
}   // 원 계약: rev-parse 실패(exit 128) → 빈 라벨
```
② 고친 코드
```rust
fn head_branch(gitdir) -> Option<String> {
    let name = symbolic_ref(gitdir)?;
    let common = resolve_commondir(gitdir);              // 링크드 워크트리는 commondir 에 ref 가 있음
    if loose_ref_exists(&common, &name) || packed_refs_contains(&common, &name) { Some(name) }
    else { None }                                        // 확신 없음 → spawn(rev-parse) 폴백
}
// 특성 테스트: unborn HEAD → spawn 폴백 = 원 계약 보존
```
무엇이 깨졌나: 외부 도구 출력을 내부 파일 직독으로 대체하면서 도구가 처리하던 엣지(unborn ref·packed-refs·commondir)를 재현하지 않아 계약이 바뀌었다.\
같은 구조: 링크드 워크트리 폴더를 독립 repo로 세어 중복 → `worktree list`의 첫 항목(main)을 기준으로 dedup.

### 방안 H — 히스토리·머지 판단은 3-way와 SHA의 의미로 한다

```bash
# stale 브랜치 통합 전: 두 팁 비교(2-way)가 아니라 merge-base 기준
base=$(git merge-base develop feature/x)
git diff --stat "$base"..develop --diff-filter=D     # 그 사이 develop 이 지운 파일 수 → "부활" 착시 판별
```
무엇이 깨졌나: 3-way 머지는 merge-base 대비 양쪽 변경을 보는데, 두 팁만 비교해 삭제된 파일이 부활하는 것처럼 오판했다.\
같은 구조: rebase는 같은 변경을 새 SHA로 만들어 옛 SHA와 공존 시 중복·충돌 → 필요한 커밋만 최신 main 위로 cherry-pick, 롤백 대상은 "산출물이 빌드된 커밋"만 · 스택 PR을 squash 머지하며 base 브랜치를 지워 하위 PR 자동 종료 → `rebase --onto`로 자기 커밋만 replay · 독립 브랜치가 같은 경로에 새 파일을 각각 만들면 공통 조상이 없어 add/add 충돌 · trailer(sign-off) 추가 amend는 SHA를 바꿔 기존 참조를 갱신해야 함.

### 방안 I — 기본값·순서 의존을 명시 설정·명시 단계로 고정한다

```bash
git config pull.rebase false && git pull origin "$(git branch --show-current)"   # 전략 미설정 시 비-ff 거부
git stash push ... ; git pull ... ; git stash pop ...                            # 한 줄에 붙이지 말고 단계별 확인
git -c credential.helper= -c credential.helper='!<cli> auth git-credential' push   # 헬퍼 목록 리셋 후 하나만
mkdir -p "$(dirname "$dst")" && git mv "$src" "$dst"                              # 대상 디렉토리 선생성
git diff > keep.patch && git apply keep.patch                                    # 부분 보존: pathspec stash 대신 patch
```
무엇이 깨졌나: 설정 체인의 순서(먼저 응답한 만료 자격증명)·명령 사이의 전제(대상 경로 존재·앞 단계 성공)에 암묵 의존해, 전제가 어긋나면 에러 없이 다른 일을 했다.\
같은 구조: 줄바꿈 정규화 설정이 없어 CRLF가 섞여 diff가 부풀었고 정리는 별도 변경으로 분리 · 대량 이동 시 문자열 치환은 긴(구체) 패턴부터.

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|---|---|---|---|---|
| (기존) 가드 끄기 / 습관 바꾸기 | 가드의 위협 전제가 내 환경에서 불성립함을 논증 가능 | 설정 1줄 · 습관 | 논증 없이 끄면 보호 상실 | 통제된 단독 실행 환경의 자동화 |
| A 선검사+탈출구 | 도구의 상태 파일·정의를 래퍼가 안다 | 명령마다 가드 | 새 상태(REVERT_HEAD 등) 누락 시 갇힘 | git 위에 UI·자동화를 얹을 때 |
| B 유실 범위 명시·복구점 선영속 | 파괴적 조작 전에 끼어들 수 있다 | stash·ref·영속 기록·정리 정책 | 정리 정책의 시계 가정 · 과장된 안내 | reset·restore·롤백 |
| C plumbing 재생성+CAS | 트리가 불변(메시지·메타만 변경) | 서명·hook 미실행, committer 변경 | 가드 누락 시 머지 부모 손실 | 과거 커밋 메타데이터 수정 |
| D 격리·경로 지정 | 작업 단위를 작업트리로 나눌 수 있다 | 작업트리 추가·절대경로 습관 | 한 번의 `add -A`로 무력화 | 병렬 작업자·에이전트 |
| E untracked 가시화 | 입력을 도구가 조립한다 | 파일별 분기(심링크·바이너리·상한) | 누락 시 리뷰 오탐 | 리뷰·검증 입력 생성 |
| F ignore 명시 | 규칙 의미(깊이·추적 중 무효)를 안다 | 앵커 1자 · `rm --cached` | 앵커 누락 → 소스 미추적 | 저장소 구조가 깊을 때 |
| G 직독+폴백 | 원 명령의 계약을 테스트로 고정 | 엣지 재현 코드 | 폴백 없이 확신하면 계약 변경 | 성능 최적화 |
| H 3-way·SHA 의미 | merge-base·빌드 이력을 조회 가능 | 사전 조사 | 2-way 착시·빌드 안 된 커밋으로 롤백 | 통합·롤백·스택 PR |
| I 명시 설정·단계 | 기본값이 버전·환경마다 다르다 | 설정·단계 분리 | 체인 순서 착오 | 서버·CI의 반복 명령 |

**결론**: 공통 출발점은 "이 명령이 **무엇을 암묵 입력으로 읽는가**"를 먼저 적는 것이다. 사람이 쓰는 한 번의 명령이면 습관(D·F·I)으로 충분하지만, git 위에 도구·자동화를 얹을 때는 그 암묵 입력을 **명시적으로 검사**(A)하고, 되돌릴 수 없는 조작은 **복구점을 먼저 영속**(B)하거나 아예 **워킹트리를 거치지 않는 경로**(C)를 택한다. 병렬 실행이 있다면 격리(D)는 선택이 아니라 전제다. 직독 최적화(G)는 원 명령의 계약을 테스트로 고정할 수 있을 때만 한다.
