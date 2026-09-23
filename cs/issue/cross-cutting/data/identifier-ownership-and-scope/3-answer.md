# cs/issue/data/identifier-ownership-and-scope — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 사건 기록 대조·추상화. 복습 전 읽지 말 것.

태그: `identity`

## 정답
<!-- 질문 1:1 대응 -->

1. **예측 vs 탐색.**\
   slug 규칙(`/`·`.` → `-`)은 일부만 확인됐고 `_`·공백 같은 특수문자 처리는 미검증이었다 — 문서화되지 않은 외부 규칙을 재구현하면, 규칙이 조금만 달라도 **존재하지 않는 경로**를 가리킨다.\
   실패가 조용한 이유: 틀린 경로는 에러가 아니라 "아직 파일 없음"과 구별되지 않아, 빈 파일을 계속 tail하거나 빈 값을 읽고 진행한다(실측: 상태 경로 slug 계산이 실제 인코딩과 어긋나 "마지막 사용자 메시지"가 빈 값이 되고, 명시적인 승인 요청이 키워드 매칭 실패로 차단됐다).\
   교정: id를 **우리가 정해 넘기고**(세션 생성 플래그), `<state_root>/*/<uuid>.jsonl`을 1단계 스캔으로 **찾는다**. 없으면 `None`을 돌려 호출자가 재시도 — 규칙과 무관하고, 같은 cwd에서 병렬 기동해도 경합이 없다.

2. **placeholder·해시·축약.**\
   record_id가 없을 때 `"?"`로 채우면 `think:?:0`이 **서로 다른 레코드에서 같은 키**가 되어 뒤의 항목이 앞을 덮어쓴다.\
   세 가지가 공통으로 깨뜨리는 성질은 **단사성(injectivity)** — 서로 다른 입력이 서로 다른 키로 가야 한다.\
   짧은 해시는 충돌 시 다른 폴더의 창이 합쳐지고(→ 경로 전체를 hex 인코딩: 가역·무충돌), uuid 앞 8자 접미 매칭은 접두를 공유하는 **다른 세션의 폴더를 무음 삭제**했다(→ 판별은 메타에 기록된 전체 uuid로만).
   > **단사(injective)** — 서로 다른 입력을 서로 다른 출력으로 보내는 함수의 성질. 키 함수가 단사가 아니면 충돌이 곧 정체성 혼동이다.

3. **스코프 없는 키.**\
   두 저장소에 **같은 경로나 같은 커밋 해시**가 있으면 `diff:<hash>` dedupe 키가 충돌해, 이미 열린 다른 저장소의 diff 패널이 다시 활성화된다 → 키에 저장소 cwd를 포함(`diff:<cwd>:<hash>`).\
   재귀 트리에서 `a/common`과 `b/common`은 `depth:name`이 같아 UI key가 충돌한다 → 누적 상대 경로를 key로.\
   원리: 키는 식별 대상이 유일해지는 **네임스페이스 전체**를 포함해야 한다. 단일 컨텍스트를 전제로 만든 키는 컨텍스트가 둘이 되는 순간 깨진다.

4. **정본 하나.**\
   요청에 쓰인 id(파일명 — 검증을 거친 값)를 정본으로 삼고, 로드 시 본문 id를 그것으로 **정규화**한다.\
   정하지 않으면 `u2.json` 안에 `"id":"u1"`이 적힌 파일 하나로 u1과 u2의 정체성이 뒤섞인다.\
   같은 계열: 번호(turn)가 여러 목록에서 중복되는데 번호만으로 선택 상태를 들면, 이전 목록에서 방향키가 엉뚱한 곳으로 점프하고 같은 번호의 다른 목록 항목이 함께 하이라이트된다 → 선택 = (번호, 스코프).

5. **"표식 없음"의 두 의미.**\
   ① 도구가 표식을 **지원하지 않음** ② 우리 산출 파일이 **아직 생성되지 않음**(모든 세션이 지나는 정상 구간 — 실측: 파일은 기동 시가 아니라 첫 메시지 직후 생성).\
   폴백은 ①을 위한 것인데 ② 구간에서도 발동해, 같은 폴더·시각 창에 있던 **외부 세션의 파일**을 집고 sticky claim으로 굳혀 버렸다.\
   교정: 도구가 산출 파일 메타에 기록해 주는 originator 표식을 스폰 환경변수로 심어 **표식 단독 매칭**, 폴백 삭제(없으면 "추측하지 않습니다" 사유와 함께 빈 목록 — 가시적 강등). 후보가 **정확히 1개**일 때만 매칭, 살아 있는 다른 세션과 겹치면 Contested(아무에게도 안 줌), 해제된 claim도 tombstone으로 남겨 이웃이 승계하지 못하게.\
   1급 불변식은 "남의 세션을 보여 주지 않는다" — 미래 호환보다 우선.

6. **복사 가능한 파일 속 마커.**\
   사용자가 마커가 든 파일을 다른 폴더로 복사하면 **같은 uuid가 두 곳**에 생긴다 → 둘째 폴더가 첫째 세션(첫째 폴더 cwd)을 재사용해 격리가 붕괴.\
   해결: 시작 시 마커 uuid가 **다른 cwd에 이미 등록**돼 있으면 이 폴더에 새 uuid를 재발급.\
   파싱 조건: **첫 줄**에 anchor(`^…$`), UUID 8-4-4-4-12 모양 고정, `UUID()` 재검증 통과 — 셋 중 하나라도 실패하면 "마커 없음"으로 보고 새 uuid를 앞에 붙인다(기존 본문 보존). 문서 전체 `search()`와 `[0-9a-f-]{36}`는 하이픈 36개 같은 비-UUID·본문 중간 주석까지 식별자로 인정한다.\
   덧: 외부 CLI의 상태가 cwd에서 도출된 경로에 저장되면 키는 id가 아니라 **(cwd, id) 쌍**이다 — 다른 cwd에서 같은 id로 재개하면 "세션 없음".

7. **구조적 충돌 불가.**\
   발급자마다 **키 범위를 분할**(원격 숫자 id는 2^40부터)하거나 **접두**(`<host>/<session>`)를 붙인다 — 두 발급자가 같은 값을 낼 수 없게 된다.\
   JS로 가는 정수는 **2^53−1 이하**(`Number.MAX_SAFE_INTEGER`, 안전 정수)여야 한다. 2^40 오프셋은 그 안에 있다.\
   앱 채번기와 마이그레이션 정적 시드도 같다: 채번기의 NEXT_ID가 시드 범위와 겹쳐 PK 충돌 위험 → `NEXT_ID = 400 WHERE NEXT_ID < 400` 조건부 상향(기존 행 무변경). 시드의 멱등 판정은 선점될 수 있는 id가 아니라 **자연 키**(경로 + 사이트)로 — id로 판정하면 선점 환경에서 무음 스킵된다.

## 문제 구조 (추상화 코드)

### 변형 A — 외부 명명 규칙 예측 → 발급한 id로 탐색
① 문제 코드
```rust
let slug = cwd.replace('/', "-").replace('.', "-");        // 규칙 일부만 확인됨
let path = state_root.join(slug).join(format!("{id}.jsonl"));  // 틀리면 빈 경로를 조용히 tail
```
② 고친 코드
```rust
// 기동: tool --session-id <our_uuid>   (id를 우리가 발급)
fn find_state_file(root: &Path, id: &str) -> io::Result<Option<PathBuf>> {
    let target = format!("{id}.jsonl");
    for entry in fs::read_dir(root)? {
        let dir = entry?.path();
        if !dir.is_dir() { continue; }
        let c = dir.join(&target);
        if c.is_file() { return Ok(Some(c)); }
    }
    Ok(None)                                                // 아직 없음 → 호출자 재시도
}
// 재개: 파일이 있으면 재개 플래그 + <id>, 없으면(대화 없던 세션) 같은 id로 생성 플래그
```
무엇이 깨졌나: 문서화되지 않은 외부 규칙을 재구현해 경로를 조립했다.

- 같은 구조: 외부 CLI의 "화면 초기화" 명령이 스스로 새 id를 만들어 추적이 끊김 → 앱이 새 uuid를 발급해 재기동.
- 같은 구조: 상태 경로를 slug 계산으로 추정한 훅이 실제 인코딩과 어긋나 빈 입력을 읽음 → 승인 요청 false-block.
- 같은 구조: 외부 CLI 상태가 (cwd, id)에 매여 있음 → 세션 cwd를 고정(신규·재개 동일).

### 변형 B — placeholder·해시·축약 키 (단사성 붕괴)
① 문제 코드
```rust
let key = format!("think:{}:{}", record_id.unwrap_or("?"), idx);   // 없으면 전부 think:?:N
```
② 고친 코드
```rust
let Some(rid) = record_id else { continue };     // 구성 요소가 없으면 항목을 만들지 않음
let key = format!("think:{rid}:{idx}");
```
무엇이 깨졌나: 상수로 빈칸을 채워 서로 다른 엔티티가 한 키로 수렴했다.

- 같은 구조: 창 label = 경로의 짧은 해시 → 충돌 시 다른 폴더 창 병합 → 경로 전체 hex 인코딩(가역).

### 변형 C — 스코프가 빠진 키
① 문제 코드
```ts
const key = spec.hash ? `diff:${spec.hash}` : `diff:${spec.path}`;   // repo가 여럿이면 충돌
<TreeNode key={`${depth}:${name}`} />                                  // a/common vs b/common
```
② 고친 코드
```ts
const key = spec.hash
  ? `diff:${spec.cwd}:${spec.hash}`
  : `diff:${spec.cwd}:${spec.path}:${spec.staged ? 1 : 0}`;
<TreeNode key={"d:" + node.relPath} />                                // 누적 상대 경로
```
무엇이 깨졌나: 단일 컨텍스트를 전제로 만든 키가 컨텍스트가 여럿이 되자 충돌했다.

```kotlin
// 병합(dedup) 키가 진짜 정체성이 아님: 한 절을 여러 청크로 쪼개면 heading이 같다
- val key = "${hit.path}#${hit.heading}"
+ val key = "${hit.path}#${hit.chunkNo}"      // 설계 문서의 청크 정체성 = path#chunk_no
  scores[key] = (existing?.first ?: hit) to ((existing?.second ?: 0.0) + rankScore)
```
- 같은 구조: 여러 에이전트가 모두 같은 이름(`"collector"`)으로 등록 → 단일 저장소에서 마지막 writer만 남음 → 인스턴스 이름 필드 추가 + 저장소 분리.
- 같은 구조: 파일명 id와 본문 id 불일치 → 파일명을 정본으로 `node.id = requested_id` 정규화. 목록 간 중복 번호 → 선택 = (번호 ∧ 스코프). 여러 프로젝트에 걸친 목록의 UI key → `project:uuid`.

### 변형 D — 결정적 상관 키 없이 추론 매칭
① 문제 코드
```rust
fn select(tab: &Tab, files: &[Transcript]) -> Option<PathBuf> {
    let marked = files.iter().filter(|f| f.has_marker()).collect::<Vec<_>>();
    let pool = if marked.is_empty() { files.iter().collect() } else { marked };   // 폴백
    pool.into_iter().find(|f| f.cwd == tab.cwd && in_window(f.opened_at, tab.spawned_at))
        .map(|f| f.path.clone())
}
```
② 고친 코드
```rust
enum MatchOutcome { Matched(PathBuf), NoCandidate, Contested, Multiple }

fn select(tab: &Tab, files: &[Transcript], claimed: &Set, live: &[Tab]) -> MatchOutcome {
    let c: Vec<_> = files.iter()
        .filter(|f| f.has_marker())                                  // 표식 단독 (폴백 없음)
        .filter(|f| !claimed.contains(&f.path))                      // tombstone 포함
        .filter(|f| f.cwd == canonical(&tab.cwd))
        .filter(|f| (tab.spawned_at - SKEW..=tab.spawned_at + WINDOW).contains(&f.opened_at))
        .collect();
    match c.as_slice() {
        [] => MatchOutcome::NoCandidate,                             // "추측하지 않습니다" 사유 표시
        [one] if overlaps_other_live(one, live) => MatchOutcome::Contested,   // 아무에게도 안 줌
        [one] => MatchOutcome::Matched(one.path.clone()),
        _ => MatchOutcome::Multiple,
    }
}
```
무엇이 깨졌나: cwd·시각은 확률적 속성이라 동시 실행된 다른 프로세스와 구분할 근거가 없고, "표식 없음"을 폴백 조건으로 써 정상 구간에서 남의 파일을 잡았다.

### 변형 E — 복사 가능한 파일 속 식별자 마커
① 문제 코드
```python
MARKER_RE = re.compile(r"session: ([0-9a-fA-F-]{36})")
m = MARKER_RE.search(text)                      # 문서 어디든, 모양만 흉내 내도 인정
sid = m.group(1) if m else fresh_id()
```
② 고친 코드
```python
MARKER_RE = re.compile(r"^session: ([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$")

def parse_marker(text):
    m = MARKER_RE.match(text.split("\n", 1)[0].rstrip("\r"))  # 첫 줄 고정 (CRLF 파일 대비)
    if not m: return None
    try: return str(uuid.UUID(m.group(1)))       # 재검증
    except ValueError: return None

# start: 마커 uuid가 다른 cwd에 이미 등록돼 있으면 이 폴더에 새 uuid 재발급
```
무엇이 깨졌나: 비고정 검색·모양 정규식이 위조·오인을 허용했고, 사용자가 복사할 수 있는 파일에 둔 식별자는 유일성이 보장되지 않았다.

## 검증 기록
- 2026-09-24: 사건 기록 대조·추상화(Claude 초안)

## 방안 비교

위 변형들의 기본 방안은 "정본·발급 주체를 정하고 키에 범위를 넣는다"이다. 같은 원리를 다른 방식으로 해결한 사례들은 세 갈래로 묶인다.

### 방안 1 — 키 공간을 구조적으로 분할
```ts
const REMOTE_ID_BASE = 2 ** 40;                   // 로컬 카운터와 겹칠 수 없는 범위 (< 2^53)
const remoteId = REMOTE_ID_BASE + counter.next();
const remoteUuid = `${hostId}/${sessionId}`;      // 접두로 발급자 표시
```
```sql
UPDATE id_sequence SET next_id = 400 WHERE name = 'MENU' AND next_id < 400;   -- 정적 시드 범위 밖으로
-- 시드 멱등 판정: WHERE NOT EXISTS (… url_path = ? AND site_id = ?)            -- id가 아닌 자연 키
```
```yaml
# 병행 스택(V1/V2)을 같은 네트워크에 둘 때: 프로젝트명·서비스명·포트 전부 분리
services:
  search-engine-v2: { ports: ["<v2-transport-port>"] }   # 동명 서비스면 내장 DNS가 두 IP를 번갈아 반환
# .env: ENGINE_HOST=search-engine-v2
```
- 같은 구조: 호스트 포트는 전역 이름공간 — 다른 프로젝트·개별 실행 컨테이너·시스템 서비스가 쥐고 있으면 바인딩 실패이고 오케스트레이터의 정리 범위(자기 프로젝트) 밖이다 → 포트 재할당 + 배포 전 점유 확인.

### 방안 2 — 키를 실제 소유 단위에 맞춘다
```sh
# 넓은 키: 프로젝트당 하나의 상태 파일 → 동시 세션이 서로 덮어씀
state="$CWD/.app-state/mode"
# 소유 단위(세션) 키
state="$CWD/.app-state/$SESSION_ID"
```
```sh
# 논리 작업 상태를 "편집 대상 파일의 repo 루트"에 매단 경우 → 워크트리마다 상태가 갈림
root=$(git -C "$(dirname "$file")" rev-parse --show-toplevel)
state="$root/.app-state/$SESSION_ID"        # 워크트리에서는 별도 UNSET 상태 자동 생성 → 차단
```
```tsx
// 라이브러리 영속 키: 조건부 패널에 안정 id/order, 방향별 저장 버킷 분리
<PanelGroup direction={dir} autoSaveId={`split-${dir}`}>
  <Panel id="sidebar" order={1} />
  {extra ? <Panel id="extra" order={2} /> : null}
  <Panel id="main" order={3} />
</PanelGroup>
```

### 방안 3 — 용도별로 키를 분리
```rust
// 표시용 축약(폴더명 접미 -{uuid8})을 파괴 연산 판별에 쓰지 않는다
if name.ends_with(&suffix) { fs::remove_dir_all(path)?; }        // 문제: 접두 공유 시 남의 폴더 삭제
if read_meta(&path)?.uuid == full_uuid { replace(path)?; }        // 판별은 메타의 전체 uuid 단독
```
```python
uid = fields.get("user_id")
user_id = str(uid) if uid is not None else None   # 연산 대상이 아닌 식별자는 숫자로 바꾸지 않는다 (정수 폭·정밀도) — 없음을 "None" 문자열로 만들지 않는다
```

| | 방안 1 공간 분할 | 방안 2 소유 단위 키 | 방안 3 용도별 키 |
|---|---|---|---|
| 전제 | 발급자 목록이 고정·소수 | 실제 소유 단위(세션·축·패널)를 식별할 수 있음 | 사람용 표시와 기계 판별이 같은 값을 쓰고 있음 |
| 비용 | 범위·접두 규약 관리, 기존 데이터 이관 | 키 변경 시 기존 상태 1회 리셋·마이그레이션 | 메타 저장소 필요(전체 id) |
| 실패 모드 | 범위 고갈·새 발급자 누락 | 논리 단위가 물리 단위(저장소·워크트리)에 걸치면 다시 분열 | 메타 유실 시 판별 불가 — 시끄럽게 실패시켜야 함 |
| 맞는 조건 | 다중 발급자·병행 스택 | 동시 실행 단위가 한 슬롯을 경쟁 | 파괴 연산·외부 전송이 걸린 키 |

**결론**: 충돌이 "두 발급자"에서 오면 방안 1, "키가 소유 단위보다 넓음"에서 오면 방안 2, "한 값이 두 용도를 겸함"에서 오면 방안 3이다.\
방안 2는 소유 단위를 잘못 고르면 문제를 옮길 뿐이다 — 세션 상태를 repo 루트에 매단 경우처럼, 논리적으로 하나인 작업이 여러 체크아웃에 걸치면 상태가 분열한다(이 사례의 근본 수정은 원문에 기록되지 않았고, 모든 경로에 같은 상태를 반복 기록하는 우회만 있었다).
