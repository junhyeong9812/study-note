# cs/issue/concurrency/single-writer-ownership — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 사건 기록 대조·추상화. 복습 전 읽지 말 것.

태그: `race-condition`

## 정답
<!-- 질문 1:1 대응 -->

1. **왜 조용히 사라지나.** read-modify-write는 "읽기"와 "쓰기" 사이에 틈이 있다.\
   A와 B가 같은 옛 값을 읽고 각자 계산해 전체를 쓰면, 저장소에는 나중에 도착한 쓰기만 남는다.\
   두 쓰기 모두 각자의 관점에서는 정상 완료라서 예외도 로그도 없다 — 결함이 "그냥 값이 옛날로 돌아감"으로만 보인다.
   > **lost update** — 동시 read-modify-write에서 한쪽 갱신이 다른 쪽 쓰기에 덮여 흔적 없이 사라지는 것.

2. **주기 overwrite 스레드 예측.** 폴링 스레드는 자기 메모리 모델(그 필드를 모름 = None)로 본문 전체를 다시 쓴다.\
   그래서 추가된 필드는 **다음 tick(최대 150ms 뒤)에 지워지고**, 사용자는 "방금 바꾼 이름이 되돌아감", "핸드오프 직후 이전 링크가 안 보임"을 본다.\
   "저장 전에 기존 값을 load해 보존"은 창을 좁힐 뿐이다 — load와 save 사이에 다른 writer의 쓰기가 끼면 여전히 옛 값으로 덮인다.

3. **분리 vs 직렬화.** 분리는 writer마다 **서로 다른 저장 단위**(본문 파일 / 이름 사이드카 / 링크 사이드카, 세션별 상태 파일)를 주고, 읽기 쪽(load)이 합친다.\
   각 단위의 writer가 실제로 하나뿐이라면 두 writer가 같은 바이트를 쓸 일이 없으니 락 없이도 덮어쓰기가 **불가능**하다 — 이것이 "구조적" 보장이다(같은 단위를 쓰는 인스턴스가 둘 이상 뜨면 이 전제가 깨지고, 여러 단위에 걸친 정합성은 따로 보장되지 않는다).\
   직렬화는 저장 단위를 공유한 채 락(flock·프로세스 락) 안에서 "쓰기 직전 신선 읽기 → 자기 몫만 병합 → 원자 교체"를 한다. 락 범위 밖의 writer(다른 프로세스·다른 인스턴스)가 있으면 보장이 새므로, 락이 닿는 범위를 알아야 한다.
   > **사이드카 파일** — 본문 옆에 두는 작은 별도 파일. 특정 writer만 쓰고, 읽을 때 본문 위에 덮어 적용(override)한다.

4. **앱 계산 UPDATE vs 조건부 UPDATE.** 앞의 것은 두 트랜잭션이 같은 잔액을 읽어 각자 뺀 절대값을 쓰므로 한쪽 차감이 사라진다(READ COMMITTED에서는 그대로 통과 — 격리 수준·`SELECT ... FOR UPDATE` 여부에 따라 abort·대기로 바뀔 수 있다).\
   뒤의 것은 DB가 행을 잠근 상태에서 "현재 값 기준 계산 + 조건 검사 + 쓰기"를 한 문장으로 하므로 끼어들 틈이 없다.\
   `WHERE ... AND balance >= ?`가 거짓이면 아무 행도 안 바뀌고 **영향 행 수 0**이 반환된다 — 이것을 "잔액 부족"·"이미 누가 선점함"·"그 사이 삭제됨"의 신호로 쓴다.
   > **TOCTOU** (time-of-check to time-of-use) — 확인한 시점과 사용하는 시점 사이에 상태가 바뀌어 확인 결과가 무효가 되는 경쟁.

5. **재확인이 안 닫히는 이유.** "확인"과 "삽입"이 여전히 두 단계이므로 재확인도 같은 틈을 갖는다.\
   MVCC 스냅숏 기반 REPEATABLE READ에서는 스냅숏 이후 커밋된 상대 트랜잭션의 행이 **아예 보이지도 않아** 재확인이 무의미할 수 있다.\
   마지막 방어선은 구조에 따라 다르다. 중복 **삽입**(존재 확인 후 삽입·`MAX()+1`)은 DB의 **unique/PK 제약**(또는 upsert)이 동시에 들어온 두 번째 삽입을 원자적으로 거부한다. 반면 **이미 있는 행의 claim**은 unique 제약이 막지 못한다 — 조건부 UPDATE/CAS(`WHERE status='READY'` + 영향 행 수)로 선점한다.\
   제약 위반은 성격을 구분한다: 동시 create-if-absent 경쟁에서의 충돌은 **예상된 결과**라 "이미 있음"으로 처리하거나 새 트랜잭션에서 재시도할 수 있고, 일어나선 안 되는 경로의 위반은 재시도로 가리지 말고 불변식 위반(버그) 신호로 둔다. (JPA처럼 제약 위반이 트랜잭션을 rollback-only로 만드는 환경에선 **같은** 트랜잭션 안의 재시도는 불가능하다.)

6. **ORM 전체 컬럼 UPDATE.** 변경 컬럼만 쓰는 옵션이 없으면 ORM은 엔티티의 **모든 컬럼**을 로드 시점 값 그대로 UPDATE 문에 넣는다.\
   내가 이름만 고쳤어도, 그 사이 다른 트랜잭션이 바꾼 정렬 순서 컬럼이 내가 로드했던 옛 값으로 **되돌아간다**.\
   내 코드에 그 컬럼이 안 보여도 lost update의 writer가 된다는 점이 함정이다.

7. **같은 뿌리.** 둘 다 "한 저장 단위(상태·파일)에 소유자가 여럿"이다.\
   두 핸들러가 같은 상태를 설정·리셋하면 실행 순서에 따라 한쪽 결과가 지워진다(고른 값이 곧바로 리셋되는 식).\
   여러 프로세스의 `>>` append도 한 레코드가 여러 `write()`로 나뉘거나(버퍼 크기 초과·여러 번 printf) O_APPEND 원자성이 보장되지 않는 파일시스템(NFS 등)이면 쓰기 단위가 섞여 행이 깨질 수 있다(레코드당 `write()` 한 번 + 로컬 파일시스템이면 대개 섞이지 않는다 — 환경마다 다름).\
   해법도 같다 — 상태 전이의 소유자를 하나로 정하거나, 락 안에서 원자 교체로 쓴다.

## 문제 구조 (추상화 코드)

### 변형 A — 주기 전체 overwrite 스레드 vs 필드 writer

```rust
// 문제: 폴링 스레드가 매 tick 본문 전체를 자기 모델로 덮는다
loop {
    let snap = build_snapshot();          // name / link 필드는 모름(None)
    save(&dir, &id, &snap);               // 다른 writer가 쓴 name/link 소실
    sleep(150ms);
}
fn rename(id, name) { let mut s = load(id); s.name = name; save(id, &s); }
```

```rust
// 고침: writer별 저장 단위 분리 — 본문은 폴링 단독, 메타는 사이드카
fn rename(id, name)      { write_atomic(dir.join(format!("{id}.name")), name); }
fn set_link(id, meta)    { write_atomic(dir.join(format!("{id}.meta")), meta); }
fn load(id) -> Snapshot {
    let mut s = read_body(id);             // 본문의 해당 필드는 신뢰하지 않음
    if let Some(n) = read_name(id) { s.name = n; }
    if let Some(m) = read_meta(id) { s.prev_id = m.prev_id; }
    s
}
```
무엇이 깨졌나: 본문 전체를 쓰는 writer가 있는 한, 같은 파일의 다른 필드는 다음 tick에 사라졌다.\
같은 구조: 요약·제목을 본문에 두었다가 폴링 쓰기에 None으로 덮임 → 각자 사이드카 파일로 분리(개별 파일은 temp+rename 원자 저장).

### 변형 B — 창(또는 호출)별 메모리 사본으로 공유 맵 전체 저장

```ts
// 문제: 각 창이 자기 사본(자기 항목만 앎)으로 공유 키 전체를 쓴다
function persist(byLabel: Record<string, Layout>) {
  storage.set(KEY, byLabel);            // 창 A가 {A}, 이어서 창 B가 {B} → A 소실
}
```

```ts
// 고침 1(권장): writer별 키 분리 — 창마다 자기 키만 쓰고, 읽는 쪽이 합친다
function persist(label: string, mine: Layout) {
  storage.set(`${KEY}:${label}`, mine);         // 다른 창의 키는 건드리지 않음
}
function loadAll(): Record<string, Layout> {
  return Object.fromEntries(storage.keysWithPrefix(`${KEY}:`).map(k => [k.slice(KEY.length + 1), storage.get(k)]));
}

// 고침 2(키를 나눌 수 없을 때): 모든 writer가 잡는 공통 잠금 안에서 신선 읽기 → 병합 → 저장
async function persistShared(label: string, mine: Layout) {
  await withLock(KEY, async () => {              // 예: 브라우저 Web Locks, 프로세스 간 파일 락
    const fresh = storage.get(KEY) ?? {};
    fresh[label] = mine;
    storage.set(KEY, fresh);
  });
}
// 주의: 잠금 없이 "신선 읽기 → 병합 → 저장"만 하면 창을 좁힐 뿐 여전히 lost update다
```
무엇이 깨졌나: 창 둘을 띄운 채 재시작하면 한쪽만 복원됐다(원문의 1차 교정은 신선 읽기 병합이었고, 이는 동시 저장이 드문 조건에서 창을 좁히는 대응이다 — 완전한 해결은 키 분리나 공통 잠금).\
같은 구조: 고아 항목 정리가 메모리 사본 전체를 써서 다른 창 엔트리 소실 → 신선 읽기 후 고아만 삭제(같은 한계).\
같은 구조: 목록 파일에서 두 요청이 동시에 항목을 지우면 마지막 writer만 생존 → 파일 `flock` 아래 read-modify-write.

### 변형 C — 클라이언트가 전체 상태를 "재구성"해 저장

```ts
// 문제: 알고 있는 필드만 나열해 전체 상태를 다시 만들어 저장
persist() {
  save({ projects: s.projects, active: s.active /* newField 누락 */ });
}   // 서버에 새 필드가 추가돼도 다음 persist에서 삭제된다
setA(v) { ...; persist(); }  setB(v) { ...; persist(); }
await Promise.all([setA(x), setB(y)]);   // 완료 순서 역전 → 옛 스냅샷이 마지막에 도착
```

```ts
// 고침: 단일 조립점 + 순차 await + 실패 반환
function savePersisted() { return save({ projects, active, newField /* 왕복 필수 */ }); }
const ok = await setConfig({ a: x, b: y });  // 한 번의 awaited 저장
if (!ok) keepFormAndNotify();                // 무음 실패 금지
```
무엇이 깨졌나: 역직렬화의 기본값(default)은 "읽기 호환"만 준다. 전체를 다시 쓰는 클라이언트가 모르는 필드는 곧 삭제되고, 전체 스냅샷 저장을 병렬로 두 번 하면 마지막 도착분이 이긴다.

### 변형 D — 목록 시점 스냅샷을 들고 나중에 쓰기

```rust
// 문제
let items = list();                    // 이 시점의 meta를 들고
for it in items { backfill(it.meta); } // 나중에 씀 → 그 사이 다른 writer의 최신 meta를 덮음
```

```rust
// 고침: 락 + 쓰기 직전 재독 + 없을 때만 채움(멱등)
let _g = WRITE_LOCK.lock();
let cur = read_meta(id);
if cur.field.is_none() { cur.field = compute(); write_meta(id, &cur); }
```
무엇이 깨졌나: check(목록)와 act(기록) 사이에 재검증이 없었다. 프로세스 내 락은 다른 프로세스의 병행 실행까지는 막지 못한다(그 경우 lock 파일로 대체).

### 변형 E — 파일 수명(생성·삭제)을 두 주체가 경쟁

```ts
// 문제: 닫기와 삭제를 각각 fire-and-forget
close(id);            // 주기 flusher는 아직 snapshot → save 중일 수 있음
deleteFile(id);       // 삭제 뒤 flusher가 파일을 재생성
```

```rust
// 고침: flusher가 파일의 단독 소유자 — 세션이 사라지면 자기가 지우고 종료
match sessions.snapshot(id) {
    Ok((bytes, seq)) => if seq != last { save(&key, &bytes); last = seq; },
    Err(_)           => { delete(&key); break; }
}
```
무엇이 깨졌나: 생성과 삭제의 순서가 비결정적이라 "종료 시 파일 제거" 계약이 깨졌다.

### 변형 F — 여러 프로세스가 공유 상태 파일을 read-modify-write

```sh
# 문제: 프로젝트당 상태 파일 하나, 읽고-판단-쓰기가 비원자, in-place 편집
v=$(grep KEY state); [ "$v" = 0 ] && run_action
sed -i 's/^KEY=.*/KEY=1/' state      # grep→판단→sed 사이가 비원자라 동시 실행이 판단을 덮음
```

```sh
# 고침: 세션별 파일로 분리 + flock 임계구역 + temp+mv 원자 교체 + 단일 기록 주체
state=".state/$SESSION_ID"
(
  flock 9 || exit 1                                  # 임계구역: 읽기·판단·쓰기 전부 이 안에서
  tmp=$(mktemp "$state.XXXXXX") || exit 1            # 호출마다 고유 임시 파일(같은 디렉토리 → mv가 원자 rename)
  build_new "$state" > "$tmp" && mv "$tmp" "$state" || { rm -f "$tmp"; exit 1; }
) 9>"$state.lock"
# 서브셸 ( ... ) 이라 $state·셸 함수가 그대로 보인다.
# `flock file sh -c '...'` 형태를 쓰려면 변수를 인자로 넘겨야 한다: sh -c '... "$1" ...' _ "$state"
```
무엇이 깨졌나: 두 세션이 서로의 값을 덮었고, 병렬 실행 여러 건이 "0"을 함께 읽어 게이트 한 번으로 합쳐졌다.\
같은 구조: 병렬 실행을 막지 않는 대신 플래그를 카운터가 아닌 멱등 boolean으로 정의해 "병렬 배치 = 게이트 1회"를 의미론으로 문서화.

### 변형 G — DB의 check-then-act (카운터·채번·존재 확인)

```java
// 문제
int cnt = repo.failCount(user); repo.setFailCount(user, cnt + 1); // lost update
long next = repo.selectMax() + 1; repo.insert(next, ...);         // 동시 insert가 같은 max
if (!repo.exists(key)) repo.save(new Row(key));                   // 중복 행
```

```sql
-- 고침: 원자 갱신 + 제약
UPDATE counter SET cnt = cnt + 1 WHERE user_id = ?;
-- 채번은 원자 채번기(시퀀스/블록 발급)로, 존재 확인 대신 unique 제약
```
무엇이 깨졌나: 동시 로그인 실패 카운트가 유실되고, `MAX()+1`이 PK 충돌을 냈으며, unique 제약 없는 "확인 후 삽입"이 여러 도메인에서 중복 행을 반복했다.\
같은 구조: 캐시 미스 동시 요청이 외부 API를 중복 호출(캐시 채우기가 동기화되지 않음).\
곁가지: `INSERT ... ON DUPLICATE KEY UPDATE cnt = cnt + 1, locked = (cnt + 1 >= th)`처럼 upsert 뒤 조건식은 이미 증가된 값을 볼 수 있어 한 번 일찍 잠겼다 → 조건을 `cnt >= th`로.

## 검증 기록
- 2026-09-24: 사건 기록 대조·추상화(Claude 초안)

## 방안 비교

같은 원리("한 저장 단위에 writer 하나")를 서로 다른 방법으로 강제한 사례들.

### 방안 1 — 저장 단위 분리 / 락 안의 신선 RMW (위 변형 A~F)
위 코드 참조. 파일·로컬 저장소처럼 DB 원자 연산이 없는 곳의 기본 해법.

### 방안 2 — 조건부 UPDATE(원자 갱신)로 판정과 쓰기를 한 문장에

```kotlin
val updated = exec("""
  UPDATE account SET balance = balance - ?
   WHERE id = ? AND balance >= ?""", amt, id, amt)
if (updated == 0) throw InsufficientBalance()
```
재현 박스에서 앱 계산 RMW는 100라운드 중 100라운드 불변식 위반(잔액 ≠ 원장 합계), 조건부 UPDATE는 0/100.\
격리 수준 주의(엔진마다 다름): 스냅숏 격리(SI)를 구현한 RR(예: PostgreSQL)은 같은 트랜잭션 안의 읽기→같은 행 갱신이 동시에 일어나면 한쪽을 serialization failure로 abort시키지만, MySQL InnoDB의 RR이나 READ COMMITTED는 앱 계산 RMW를 그대로 통과시킨다. 읽기와 쓰기가 서로 다른 트랜잭션이면 격리 수준과 무관하게 통과하고, 서로 다른 행을 쓰는 write skew는 SI로도 못 막는다.

### 방안 3 — 조건부 쓰기 + 영향 행 수로 성공 판정

```sql
UPDATE comment SET deleted = 'Y'
 WHERE id = ? AND room_id = ? AND post_id = ? AND deleted = 'N';
-- 반환 int: 1이 아니면 NOT_FOUND
```
검증과 쓰기 사이에 대상이 삭제·이동될 수 있으므로, 검증 조건을 쓰기 문에 다시 넣고 결과 행 수로 판정한다.\
곁가지: 존재 조회를 인가 검사보다 먼저 하면 404/403 차이가 "존재 여부 오라클"이 된다 → 인가 먼저.

### 방안 4 — 원자 채번 / 발급 직렬화 (사전 검증은 TOCTOU)

```java
long id = idGenerator.next();          // 블록 발급 채번기: gap 허용, 유일성만 보장
row.setSortOrder(id);                  // 유일한 정렬 키로 재사용 — 인스턴스별 블록이라 발급 시각 순서 ≠ 숫자 순서
// 그룹 내 순번이 필요한 경로만 그룹 행 비관락(PESSIMISTIC_WRITE)
repo.lockGroupForUpdate(groupId);
// 조회수: UPDATE t SET views = views + 1
```
블록 발급 채번기는 **유일성**과 **인스턴스 내 증가**만 준다 — 여러 인스턴스가 서로 다른 블록을 쓰면 늦게 발급된 값이 더 작을 수 있어 **전역 실시간 순서**는 보장되지 않는다. 정렬 계약이 "대략 생성 순 + 동률 없음"이면 충분하고, 엄격한 발급 순서가 필요하면 단일 시퀀스나 그룹 락 순번을 쓴다.\
채번기 자체가 `SELECT next`(잠금 없음) → `UPDATE next = 절대값`(CAS 아님)이면 JVM 내부 `synchronized`로만 안전하고 다중 인스턴스에선 다시 경쟁한다 — 스케일아웃 시 원자 증가 문으로 바꿔야 한다.

### 방안 5 — check-then-insert 대신 원자 upsert (제안 단계)

```sql
INSERT INTO blocklist(key, active) VALUES (?, true)
ON CONFLICT (key) WHERE active DO NOTHING;   -- partial unique index 전제
```
동시 요청 둘 다 "active 없음"을 보고 삽입해 제약 위반이 났다. upsert 또는 분산 락(SETNX)이 제안됐고, 원문 기준 미해결로 남아 있다.

### 방안 6 — 조건부 UPDATE claim-first (스케줄 워커)

```java
// 영향 0행 = 선점 실패 → 건너뜀. 외부 자원 launch 전에 행부터 선점
if (!repo.claim(id /* WHERE id=? AND status='READY' AND NOT EXISTS(진행중) */)) continue;
try { var job = startExternal(id); repo.setJobId(id, job.id()); } catch (...) { ... }
```
스케줄러 풀 크기가 1보다 크면 서로 다른 스케줄 메서드가 동시에 돈다 — "조회 후 claim"은 TOCTOU.\
교차 행 조건(NOT EXISTS)은 스냅숏 읽기로 완전 원자화되지 않아, 단일 인스턴스 전제의 프로세스 내 락과 "워커는 한 대에서만 켬" 설정을 함께 두고, 콜백 + 저빈도 sweep으로 유실을 복구했다.

### 방안 7 — 변경 컬럼만 UPDATE vs 같은 행 수정 경로 전부 비관락

```java
// 문제: 전체 컬럼 정적 UPDATE — 이름만 고쳐도 position을 로드 시점 값으로 되돌림
entity.setName(n);   // commit → UPDATE t SET name=?, position=<옛값>, ... WHERE id=?
// 선택지 1: 변경 컬럼만 UPDATE(@DynamicUpdate)
// 선택지 2(채택): 같은 행을 수정하는 모든 경로를 그룹 행 비관락으로 직렬화
repo.lockGroupForUpdate(groupId); entity.setName(n);
```
정렬 경로만 잠그면 부족하다 — 같은 행을 쓰는 **모든** 경로가 같은 락을 잡아야 한다.\
변경 컬럼만 UPDATE(선택지 1)는 "안 바꾼 컬럼"의 되돌림만 없앤다 — **같은 컬럼**을 두 트랜잭션이 동시에 바꾸면 여전히 lost update이므로, 그 경우엔 락이나 버전 컬럼 낙관락(`@Version`)이 필요하다.\
곁가지: bulk UPDATE는 DB만 바꾸고 영속성 컨텍스트(1차 캐시)는 갱신하지 않으므로, 이미 로드된 엔티티는 stale하다.

### 방안 8 — check-then-act 제거: 대기 후 stop 재확인 + 멈춘 뒤 삭제

```rust
loop {
    if stop.load() { break; }
    sleep(interval);
    if stop.load() { break; }   // 추가: 대기 중 들어온 종료 신호를 부작용 직전에 재확인
    save(snapshot());
}
// 호출 측: await close(id);  그 다음에 delete(id)
```
루프 초입에서만 stop을 보면 sleep 중 들어온 close 뒤에도 한 번 더 저장해, 삭제한 파일을 되살렸다.

### 방안 9 — 상태 전이 소유자 단일화 (같은 이벤트의 두 핸들러)

```sh
# 문제: 핸들러 X는 "먼저 모드를 고르라"며 쓰기를 막고, 핸들러 Y는 같은 쓰기에서 모드를 리셋
# 고침: 그 문서 쓰기는 X의 검사 대상에서 면제 → 리셋·안내 책임은 Y 하나만
case "$FILE" in */plans/*) exit 0 ;; esac
# 같은 문서의 재작성(갱신)은 경로 비교로 리셋하지 않음 — 생성과 갱신을 구분
```
고른 값이 곧바로 리셋되는 이중 질문이 실제 재현됐다.\
리셋 실패 시 이전 허가 상태가 남는 fail-open은 "리셋 대기 마커"로 다음 판정자에게 인계했고, 병행 세션의 check-write TOCTOU는 "단일 메인 흐름" 운영 불변식으로 수용했다(선택하지 않은 방법: 셸 락 기반 강제).

### 방안 10 — 동시 append는 락 안의 원자 재작성 + 제어문자 제거

```sh
san() { printf '%s' "$1" | tr '\n\t|' '   ' | tr -d '\000-\010\013-\037\177'; }
line=$(san "$msg")
(
  flock -w 1 9 || exit 1                                     # 1초 안에 못 잡으면 실패
  tmp=$(mktemp "$f.XXXXXX") || exit 1                        # 고유 임시 파일, 같은 디렉토리
  { if [ -e "$f" ]; then cat "$f" || exit 1; fi; printf '%s\n' "$line"; } > "$tmp" && mv "$tmp" "$f" || { rm -f "$tmp"; exit 1; }   # 최초 부재만 허용, 기존 파일 읽기 실패면 교체 중단
) 9>"$f.lock" || drop                                         # 실패=드롭(수용한 정책)
```
동시 발화한 프로세스들의 `>>`가 섞여 첫 줄이 손상됐다(실측).\
일반론(환경마다 다름): 로컬 파일시스템에서 O_APPEND 파일에 대한 `write()` 한 번은 끝에 원자적으로 붙으므로, 한 행을 `write()` 한 번으로 쓰면 대개 섞이지 않는다. 섞임은 한 행이 여러 `write()`로 쪼개질 때(여러 번 출력·버퍼 초과), NFS처럼 O_APPEND 원자성이 없는 파일시스템일 때 생긴다 — "쓰기 원자성"과 "행 단위 원자성"은 다르다. `>>`는 크래시·디스크풀 때 부분 행을 남길 수도 있다.\
위 고침은 전체 재작성이라 파일이 커질수록 비싸다 — 행 단위 원자성만 필요하면 락 안에서 `printf '%s\n' "$line" >> "$f"` 한 번으로 충분하다.\
곁가지(별개 원리): 제어문자(CR·ESC)를 거르지 않은 로그는 표시 단계에서 다른 행처럼 위조될 수 있다.

### 비교

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 저장 단위 분리 | 필드를 writer별로 나눌 수 있음 | 파일 수 증가, load가 합치는 책임 | 여러 사이드카 동시 저장은 원자적이지 않음(한쪽만 갱신 가능) | 로컬 파일·키-값 저장, writer가 필드 단위로 갈림 |
| 락 안 신선 RMW | 모든 writer가 같은 락을 잡음 | 락 대기, 락 범위 관리 | 락 밖 writer(다른 프로세스·인스턴스)는 못 막음 | 같은 단위를 여럿이 반드시 공유 |
| 조건부 UPDATE / 영향 행 수 | DB가 행 단위 원자성 제공 | 조건을 SQL로 표현해야 함 | 영향 행 수를 안 보면 실패가 무음 | 카운터·잔액·상태 전이·claim |
| 원자 채번·unique 제약 | 시퀀스/채번기·제약을 둘 수 있음 | gap 발생, 스키마 변경 | 채번기 자체가 비원자면 다중 인스턴스에서 재발 | 식별자 발급·중복 방지 |
| 비관락 직렬화 | 같은 행을 쓰는 모든 경로가 락을 잡음 | 처리량 감소, 데드락 순서 관리 | 한 경로라도 빠지면 lost update 재발 | ORM 전체 컬럼 UPDATE가 끼는 행 |
| 소유자 단일화·재확인 | 상태 전이 경계를 설계로 정할 수 있음 | 책임 재배치 | 병행 흐름이 생기면 TOCTOU 창이 남음 | 이벤트 핸들러·백그라운드 루프 |

**결론**(조건부): 불변식이 **한 행·한 문장**으로 표현되는 DB 값(카운터·잔액·단일 행 상태 전이·claim)이면 조건부 UPDATE·upsert·unique 제약이 대개 가장 싸고 확실하다 — 판정과 쓰기를 한 문장에 넣고 영향 행 수를 반드시 본다. 여러 행·테이블에 걸친 불변식(교차 행 조건·write skew)은 한 문장 UPDATE로 보장되지 않으므로 트랜잭션 + 적절한 격리 수준(SERIALIZABLE)이나 명시적 락이 필요하다.\
DB 원자 연산이 없는 파일·로컬 저장소에서는, 각 저장 단위의 writer를 **실제로 하나로** 만들 수 있을 때 writer별 분리가 락보다 견고하다(락을 안 잡는 writer가 있어도 서로의 단위를 건드리지 않음). 같은 단위를 쓰는 인스턴스가 여럿 뜰 수 있거나, 여러 단위를 함께 원자적으로 바꿔야 한다면 분리만으로는 부족하다 — 그때는 모든 writer가 같은 락을 잡는 락 안의 신선 RMW를 쓴다.\
ORM이 끼면 "내가 안 바꾼 컬럼"도 쓰기에 포함되는지 먼저 확인하고, 락으로 막을 거면 같은 행을 쓰는 모든 경로를 잠근다.
