# cs/issue/infra/state-drift-delete-propagation — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-23) — 이슈 README·코드 기준. 복습 전 읽지 말 것.

태그: `silent-failure`

## 정답
<!-- 질문 1:1 대응 -->

1. `rsync -a`는 `--delete` 없이는 "로컬에 있는 것을 서버로 복사"만 하고 "로컬에서 사라진 것을 서버에서 지우기"는 안 한다. 그래서 로컬에서 파일을 옮기거나 지운 뒤 배포하면, 서버에는 **옛 파일이 그대로 남는다**(유령/잔재). 복사는 더하기(존재)만 전파하고 빼기(부재)를 전파하지 못한다.
   > **state drift(상태 표류)** — 정본(로컬/저장소)과 배포 대상(서버)의 상태가 조용히 어긋나 쌓이는 현상.

2. 배포 스크립트가 `rsync -a`(--delete 없음)여서, git mv로 로컬에선 사라진 옛 `common/ sync/ indexing/ search/` 패키지가 **서버 소스 디렉토리에 그대로 남았다**. Docker 빌드의 `COPY src`가 옛 파일과 새 `api/` 파일을 **전부** 컴파일 → Spring이 `common.ErrorHandler`와 `api.ErrorHandler` 두 개의 같은 이름 빈을 보고 `ConflictingBeanDefinitionException`으로 기동을 거부했다.
   > **빈(bean)** — Spring이 관리하는 객체. 컴포넌트 스캔은 기본 빈 이름을 클래스 단순명에서 만들므로(`errorHandler`), 패키지가 달라도 단순명이 같은 두 클래스가 같은 이름을 다투면 `ConflictingBeanDefinitionException`으로 기동을 멈춘다(타입 주입 후보가 둘인 `NoUniqueBeanDefinitionException`과는 다른 오류).

3. `--delete`는 "로컬에 없으면 서버에서도 지운다"이므로, **서버에만 있어야 하는 파일**(예: `.env` 시크릿)까지 지워버릴 수 있다. 그래서 `rsync -a --delete --exclude .env`로 잔재는 지우되 서버 배포 설정은 보호한다.

4. 우리 파이프라인은 "코드"를 이미지에 담아 날랐지만, **compose 파일은 이미지 밖**이다 — compose는 컨테이너를 "밖에서" 정의·기동하는 설정이라, 컨테이너 "안"에 넣어봐야 아무도 읽지 않는다. 그래서 호스트의 compose는 옛 rsync 사본 그대로 남고, 그 이후 GitHub 변경(예: `build:` 제거)과 아무 관계가 없어 "여전히 Skipped"가 반복됐다. 설정을 나르는 채널이 아예 없었던 것이다.

5. agent가 배포 직전에 `git fetch --depth=50 origin main` → `git reset --hard <commit_sha>`를 돌려, **GitHub을 설정의 정본**으로 삼는다. 호스트 디렉토리가 clone이면 배포 때마다 최신 compose·설정이 따라온다(`<commit_sha>`가 얕은 fetch 범위 안에 있어야 reset이 성공한다). 순서가 "설정 동기화 → 컨테이너 갱신(`compose up -d --build`)"이라 compose 변경이 **항상 코드보다 먼저 도착**한다. 이로써 이미지 채널을 없애고 전달 채널을 git 하나로 통일 → **추적 파일에 한해** "배포된 것 = 그 커밋"이 성립한다. `reset --hard`는 미추적 파일을 지우지 않으므로 과거 복사본에서 남은 미추적 잔재는 그대로다(빌드가 디렉토리째 COPY하면 다시 섞일 수 있어 `git clean -n`으로 점검 — `.env` 보호 주의).
   > **단일 정본(single source of truth)** — 상태의 기준이 한 곳(여기선 GitHub main)뿐이라, 대상을 그것으로 재구성하면 재구성 범위 안에서는 drift가 원리적으로 안 생긴다.

6. `git reset --hard`는 **git이 추적하는 파일만** 되돌린다. `.env`(시크릿)는 git 미추적 파일이라 `reset --hard`에도 살아남는다. 즉 "무엇을 정본이 관리하고 무엇을 관리하지 않는가"의 경계가 곧 "무엇을 덮어쓰고 무엇을 보존하는가"의 경계가 되어, 미추적이 안전장치로 작동한다.

7. **복사**는 원본의 "있는 것"만 대상에 더한다(부재는 못 옮긴다). **동기화/재구성**은 대상을 정본과 **일치**시킨다 — 없어진 것은 지우고, 바뀐 것은 갱신한다(`rsync --delete`가 이것이고, `reset --hard`는 추적 파일 범위에서만 이것 — 미추적 파일은 건드리지 않는다). 이번엔 잔재가 Spring 기동 거부라는 **시끄러운 실패**로 즉시 드러나 바로 잡았지만, 충돌 없는 잔재였다면 옛 코드가 **조용히 섞여** 돌며 며칠 뒤에야 발견됐을 것이다 — 그래서 시끄러운 실패가 오히려 고마운 경우다.

## 문제 구조 (추상화 코드)

### 변형 A — 복사 배포가 삭제를 전달하지 못함 (잔재 파일)

① 문제 코드
```bash
# deploy.sh
rsync -a ./src/ server:/app/src/          # 있는 것만 더한다 — 로컬에서 옮긴/지운 파일은 서버에 남음
ssh server 'cd /app && docker compose up -d --build'   # COPY src → 옛 패키지 + 새 패키지 모두 컴파일
# → 같은 이름의 컴포넌트 2개 → 기동 거부
```
② 고친 코드
```bash
rsync -a --delete --exclude .env ./src/ server:/app/src/   # 부재도 전파, 서버 전용 시크릿은 보호
```
무엇이 깨졌나: 복사는 "존재"만 전파하고 "부재"를 전파하지 않아, 옮긴 파일의 옛 사본이 서버에 쌓였다.\
같은 구조(반대 방향): `--delete`를 켜고 `--exclude`를 빠뜨려, 소스에 없는(gitignore된) 서버 `.env`가 배포 때 지워진 기록 — 삭제 전파는 "보존할 것"의 목록과 한 쌍이다.

### 변형 B — 설정을 나르는 채널이 없음 (이미지 밖의 compose)

① 문제 구조
```text
코드   : git push → CI 이미지 빌드 → 레지스트리 → 서버 compose pull   (채널 있음)
compose: (채널 없음) → 서버에는 과거 복사본 그대로
```
② 고친 코드
```go
// 배포 에이전트: 컨테이너 갱신 전에 설정부터 정본에 맞춘다
run("git", "-C", dir, "fetch", "--depth=50", "origin", "main")
run("git", "-C", dir, "reset", "--hard", commitSha)   // 추적 파일만 되돌림 → 미추적 .env 보존 (미추적 잔재도 남음 · commitSha 는 fetch 범위 안이어야 함)
run("docker", "compose", "-f", dir+"/compose.yml", "up", "-d", "--build")
```
무엇이 깨졌나: 코드와 설정의 전달 채널이 갈려, 설정 쪽은 정본(저장소)의 변경을 영영 받지 못했다.

### 변형 C — 비-git 서버: "커밋됨 ≠ 배포됨"을 검출할 수단이 없음

① 문제 구조
```text
repo:   c1 → c2(시크릿 env 외부화) → c3(파일 삭제)
server: rsync 로 c1 시점 복사본 · 버전 모름
장애 복구 배포 → c2·c3 가 의도치 않게 한꺼번에 도착
  - 서버 .env 에 새 키 없음(.env 는 git 밖이라 코드와 함께 이동 안 함) → 배치·DB 인증 파손
  - compose 가 새 env 를 컨테이너에 안 넘김 → 설정 기본값(CHANGE_ME)으로 인증 실패
  - 삭제한 파일 잔존 (변형 A)
```
② 고친 절차
```bash
# 배포 전: 대상 디렉토리 백업 → .env 에 필요한 키 보강 → compose 에 env 전달 추가
# 배포 후: repo ↔ 서버 파일 해시 전수 대조 (불일치 = 드리프트)
diff <(cd repo && find src -type f -exec sha256sum {} + | sort -k2) \
     <(ssh server 'cd /app && find src -type f -exec sha256sum {} + | sort -k2')
# 시크릿 기본값은 동작하는 값이 아니라 CHANGE_ME (빠지면 시끄럽게 실패)
```
무엇이 깨졌나: 대상이 자기 버전을 모르니 커밋과 배포 사이의 격차가 쌓여도 드러나지 않았고, git 밖의 `.env`는 코드 변경을 따라오지 않았다.\
같은 구조: 같은 서버의 기록 — "커밋만 하고 배포 누락 → 서버가 repo보다 오래된 코드"를 해시 대조 습관으로 대응.

### 변형 D — 키 집합만 교체하는 동기화는 사라진 키를 지우지 못함

① 문제 코드
```python
def sync(source_rows):
    for row in source_rows:
        if row.key not in target:           # insert-only: 갱신·상태 전환 미전파
            target.insert(row)

def months_to_replace(months, produced):       # 산출물에 있는 월만 교체
    for m in sorted(set(produced) & set(months)):
        target.delete_month(m); target.insert(produced[m])
    # 원천이 전부 비활성인 월 → 산출물 비어 있음 → DELETE 안 돎 → 옛 행 잔존
```
② 고친 코드
```python
def sync(source_rows):                      # 전량 미러: 없으면 insert, 다르면 update
    for row in source_rows:
        cur = target.get(row.key)
        if cur is None: target.insert(row)
        elif not cur.same_as(row): target.update(row)
    # 불변식 테스트: 변경 없는 재실행 → updated == 0 (멱등)
    # 주의: 원천에서 행 자체가 사라지면 이 루프로는 전파되지 않음 → 필요하면 (target 키 - source 키) 삭제를 별도로

def months_to_plan(months, available):
    if months is None:
        return sorted(available), []                       # 전체 모드: 과거 월 무단 삭제 방지
    target = sorted(set(months))
    return target, sorted(set(target) - available)         # 명시 월은 비어 있어도 DELETE
```
무엇이 깨졌나: "산출물에 있는 키만" 다루는 동기화는 원천에서 사라지거나 바뀐 키를 대상에 반영하지 못했다. 반대로 전량 미러 대상 테이블에 손으로 한 1회성 보정은 다음 동기화가 덮어썼다(보정은 미러되지 않는 지점에서 해야 한다).\
같은 구조: 검색 인덱스를 문서 id upsert로 재색인하면 키 체계가 바뀐 옛 문서가 수십만 건 잔존 — 재색인 전 인덱스 삭제·재생성, 옛 스키마 버전이면 기동 시 fail-fast.

### 변형 E — 정본이 둘: 소스와 배포본을 양쪽에서 고침

① 문제 구조
```text
repo/hooks/*.sh          ← 일부만 존재
~/deployed/hooks/*.sh    ← 배포 경로에서 직접 추가·수정된 훅 존재
→ 어느 쪽을 고쳐도 반쪽 적용
```
② 고친 구조
```text
repo = 단일 정본 선언 → 배포본에만 있던 것 역동기화
이후 변경 경로는 하나뿐: repo 수정 → deploy.sh (manifest diff → 백업 + 원자 교체 → smoke)
```
무엇이 깨졌나: 양방향 수정이 가능한 두 사본은 필연적으로 드리프트한다.\
같은 구조: 설정에 물리 인덱스명을 하드코딩 — 인덱스를 교체하자 설정이 존재하지 않는 대상을 가리켜 404→500(별칭 미사용; 해결 결과는 미기록).

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log

## 방안 비교

같은 원리(사본이 원본의 삭제·변경을 못 따라감)에 대해, 위 변형들은 **"정본에서 대상을 재구성"**(rsync --delete · reset --hard · 전량 미러 · 단일 배포 경로)으로 수렴시켰다. 다른 사건들은 다른 방안을 택했다.

### 방안 1 — 파생 상태를 원본 삭제에 묶는 정리 훅 (키 수명 일괄 관리)

① 문제 코드
```ts
function deletePath(path) { fs.remove(path); tree.refresh(); }   // 열린 탭 목록은 모름 → stale 탭
```
```ts
function register(uuid, slot) {
  const stale = slotToId.get(slot);
  if (stale) idToSlot.delete(stale);      // idToProject / idToLabel 은 남음 → 고아가 집계에 계속 계수
  // ...
}
```
② 고친 코드
```ts
function deletePath(path) { fs.remove(path); store.closeTabsUnder(path); tree.refresh(); }
function evict(uuid) {                          // 키의 수명을 한 함수가 소유
  idToSlot.delete(uuid); idToProject.delete(uuid); idToLabel.delete(uuid);
}
```
무엇이 깨졌나: 같은 엔티티를 가리키는 파생 상태가 여러 곳인데 삭제 경로가 그중 일부만 지웠다.

### 방안 2 — 단일 로드 정본 + write-only 사본 + 삭제는 tombstone

① 문제 코드
```ts
function persist(tree, legacy) {
  localStorage.setItem("tree", JSON.stringify(tree));    // 두 키 동시 기록 — 비원자
  if (legacy) localStorage.setItem("legacy", legacy); else localStorage.removeItem("legacy");
}
function load() {
  const tree = parse(localStorage.getItem("tree")), legacy = localStorage.getItem("legacy");
  return tree && agrees(tree, legacy) ? tree : fromOld(legacy);   // 사후 화해: 누가 최신인지 추론
}
// 한쪽 쓰기 실패 · 다운그레이드 · "null" 문자열 → 닫은 항목 부활, 변경 유실
```
② 고친 코드
```ts
function persist(tree, legacy) {
  localStorage.setItem("tree", JSON.stringify(tree));    // 무조건 첫 줄: 이후가 throw 해도 정본은 기록됨
  try { writeLegacyBreadcrumb(legacy); } catch {}        // 구버전만 읽는 write-only 사본
}
function close() { persist(EMPTY_TREE, null); }          // 삭제 = 키 제거가 아니라 tombstone 기록
function load() {
  const raw = localStorage.getItem("tree");
  if (raw === null) return migrateOnceFromLegacy();      // 키 부재 ⟺ 구버전 데이터 (그 외엔 legacy 안 봄)
  const t = tryParse(raw);
  return isValidCurrent(t) ? t : DEFAULT;                // 손상·미지 버전 = 기본값
}
```
무엇이 깨졌나: 원자적으로 함께 갱신할 수 없는 두 저장소를 로드 때 비교하면 "누가 언제 썼나(provenance)"가 데이터에 없어 판정이 원리적으로 틀릴 수 있고, 삭제를 "키 부재"로 표현하면 부분 실패한 삭제가 "처음부터 없음"과 구분되지 않는다.

### 방안 3 — 사본에 출처를 기록하고 드리프트를 감지

```text
실행 설정 = 실제 배포본에서 추출 (저장소 스냅샷 사본이 존재하지 않는 훅을 참조하고 있었음)
provenance.json = { source_sha: <원본 해시>, removed: [...] }
setup 검증 = 공유 스크립트 바이트 패리티 검사 → 불일치면 알림 → 변경을 읽고 재동기
```
무엇이 깨졌나: 복사본은 원본이 바뀌어도 따라가지 않는데, 사본이 원본인 줄 알고 썼다.

### 방안 4 — 런타임 상태를 영속 정본에 먼저 기록

① 문제 코드
```kotlin
fun switch(target: Slot) { registry.replace(target) }        // 메모리에만 반영
// 재시작 → env 기본값(blue)으로 복원 → 이미 내린 슬롯으로 라우팅 = 전면 장애
val state = runCatching { store.read() }.getOrElse { fromEnv() }   // 손상도 env 로 폴백 (fail-open)
```
```sql
SET GLOBAL innodb_buffer_pool_size = ...;   -- 런타임 변수만 바뀜 → 재시작 시 원복 (MySQL 8.0+ 의 SET PERSIST 는 영속되지만, 설정 파일과 이중 정본이 됨)
```
② 고친 코드
```kotlin
fun switch(target: Slot, token: Long) {
    store.write(State(target, token))       // write-ahead: temp + fsync + atomic move (+ 디렉토리 fsync 로 rename 영속)
    registry.replace(target)
    if (!refreshAndAwait(target)) rollback()
}
val state = when {
    !store.exists() -> fromEnv()                              // 부재만 기본값
    else -> store.read() ?: throw IllegalStateException("state corrupt")   // 손상 = 기동 거절
}
```
```text
튜닝 값은 설정 파일/기동 인자(.env · compose)에 영속 — 런타임 SET 은 정본이 아니다
```
무엇이 깨졌나: 런타임에 바뀐 상태를 정적 설정에서 재구성해 재시작이 과거로 되돌렸고, "부재"와 "손상"을 같은 폴백으로 처리해 손상이 조용히 과거 상태를 열었다.

### 방안 5 — 외부 설정의 사본을 코드에서 없앤다

① 문제 코드
```python
SERVICES = {c: {"search": f"{c}-search"} for c in REGIONS}   # compose 서비스명의 하드코딩 사본
def restart(c, svc):
    run(["docker", "compose", "-f", f"{DIR}/compose.yml", "up", "-d", SERVICES[c][svc]])
# compose 가 "<c>-search-v2" 로 바뀐 뒤 → no such service → 자동 재시작이 한 번도 성공 못 함 (운영자는 수동 우회로 모름)
```
② 고친 방향
```python
SERVICES = {c: {"search": f"{c}-search-v2"} ...}   # hotfix
# 재발 방지 후보: compose 파일에서 서비스명을 파싱(사본 제거)
# 검증: 배포 후 컨테이너 stop 장애 주입 → 자동 재시작 성공 실측
```
무엇이 깨졌나: 원본(compose)이 바뀌자 코드 속 사본이 조용히 어긋났고, 평소 실행되지 않는 복구 경로라 장애 전까지 아무도 몰랐다.

| | 재구성(위 변형들) | 1. 정리 훅 | 2. 단일 정본+tombstone | 3. 출처·드리프트 감지 | 4. 영속 정본 선기록 | 5. 사본 제거 |
|---|---|---|---|---|---|---|
| 전제 | 정본이 명확하고 대상을 통째로 다시 만들 수 있다 | 삭제 경로를 코드가 전부 안다 | 사본을 없앨 수 없다(구버전 호환) | 사본을 당장 없앨 수 없다 | 재시작을 넘어 살아야 하는 런타임 상태 | 원본을 런타임에 읽을 수 있다 |
| 비용 | 보존 목록 관리(`--exclude`·미추적) | 삭제 지점마다 호출 | 로드 규칙·쓰기 순서 계약·테스트 | 해시·패리티 검사 유지 | fsync·원자 교체·손상 처리 | 파싱 의존 |
| 실패 모드 | 보존 목록 누락 시 서버 전용 파일 삭제 | 새 삭제 경로에서 훅 누락 | 규칙 밖 엣지(파싱 성공한 `"null"` 등) | 감지만 하고 수렴은 사람 몫 | 손상을 폴백으로 삼키면 fail-open | 원본 형식 변경 |
| 맞는 조건 | 배포·동기화처럼 대상 = 정본의 사본 | UI·인메모리 파생 상태 | 스키마 이행기의 이중 표현 | 복사가 불가피한 설정 스냅샷 | 전환 상태·튜닝 값 | 외부 이름·설정의 하드코딩 |

**결론**: 대상을 정본에서 통째로 다시 만들 수 있으면 재구성이 대체로 가장 단순하고 강하다(재구성 범위 안에서는 드리프트가 원리적으로 안 생긴다 — 보존 목록·미추적처럼 범위 밖에 둔 것은 별도 점검). 사본을 없앨 수 있으면 없애는 것(방안 5)이 다음이고, 구버전 호환 때문에 사본이 남아야 하면 **읽는 쪽 정본을 하나로 고정하고 사본은 write-only, 삭제는 tombstone**(방안 2)으로 사후 화해를 없앤다. 사본도 재구성도 불가능한 곳에서만 감지(방안 3)로 물러서고, 런타임 상태는 "메모리가 아니라 영속 파일이 정본"(방안 4)이어야 재시작이 과거로 되돌리지 않는다.
