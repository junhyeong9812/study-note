# cs/issue/concurrency/aba-reusable-identifier — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 출처 원문 대조. 복습 전 읽지 말 것.

태그: `race-condition`

## 정답
<!-- 질문 1:1 대응 -->

1. **ABA 문제.** 어떤 값을 읽은 뒤 다시 봤을 때 같은 값(A)이라 "그동안 아무 일도 없었다"고 판단하지만, 실제로는 A→B→A로 바뀌어 다른 대상이 된 상황이다.\
   식별자가 재사용되면 이름은 같아도 가리키는 실체(세대)가 다르다.\
   pid는 프로세스가 reap된 뒤 커널이 재발급하고, 세션 id는 사용자가 같은 값으로 재개할 수 있고, 재시작마다 1부터 세는 카운터는 이전 인스턴스의 값과 겹친다.\
   이름은 "지금 이 이름을 가진 것"만 말할 뿐 "내가 처음 본 그것"을 보증하지 않는다.
   > **ABA 문제** — 같은 값으로 되돌아온 식별자를 "변화 없음"으로 오인해, 다음 세대 대상에 옛 세대용 조작을 적용하는 경합.

2. **옛 waiter가 새 세션을 파괴한다.** waiter는 `id`만 들고 있으므로, 종료 직후 같은 id로 새 세션이 등록되면 `remove(id)`가 새 세션의 핸들을 지운다.\
   핸들 drop이 pty master를 닫으면 새 프로세스가 SIGHUP을 받고, 몇 초 뒤 실행되는 토큰 해제는 새 세션의 토큰을 무효화하고, 파일 정리는 새 헤더 파일을 지운다.\
   늦게 도착하는 모든 비동기 정리 경로가 같은 구멍을 가진다.

3. **비교를 덧붙이기 vs 주소를 바꾸기.** 세대 토큰 방식은 "모든 정리 경로가 세대를 들고 불일치면 no-op"을 요구한다 — 예약 집합, 이벤트 payload, 회수 주소, 파일명 등 한 곳이라도 세대를 안 들면 그 자리가 다음 라운드의 경합이 된다(실제로 부분 적용 후 새 구멍이 계속 나왔다).\
   반면 맵·토큰·파일명·이벤트·명령 주소를 전부 재사용 불가 키로 바꾸면, 옛 정리가 들고 있는 키는 새 세션과 **절대 같지 않으므로** 비교할 필요 자체가 사라진다.\
   원래 id는 레코드의 속성으로 강등돼 같은 id의 종료 레코드와 후속 레코드가 공존할 수 있다.\
   "비교를 잊을 자리가 없어진다"가 핵심이다.
   > **불투명 키(opaque key)** — 산술·대소 비교·파싱으로 의미를 끌어낼 수 없게 만든 식별자(예: `"k<n>"`, `k0` 거부). 기본값·0으로 채워진 키가 실재 대상을 가리키지 못하게 한다.

4. **재시작을 넘는 키.** 프로세스 안에서 단조인 카운터도 재기동하면 다시 k1부터 시작한다.\
   옛 k1을 든 소비자가 재기동 후 `Kill k1`을 보내면 무관한 프로세스 트리를 **정상 명령으로** 종료한다(검사를 무력화한 뮤테이션에서 실제로 살아 있는 다른 세션이 SIGKILL됐다).\
   epoch을 키 옆 선택 필드로 두면 역직렬화 기본값·누락으로 빠질 수 있어 "epoch 없는 키"가 여전히 존재 가능하다.\
   `"<epoch>:k<n>"` 한 값 타입이면 두 반쪽 없이는 값 자체가 만들어지지 않고, 해석 시 epoch 불일치를 거부(fail-closed)한다.\
   같은 원리로 연결마다 0부터 세는 알림 seq는 `host#incarnation`처럼 세대를 키에 넣어야 "이미 봤음" 기억과 충돌하지 않는다.
   > **epoch / incarnation** — 한 인스턴스(프로세스 기동·연결)의 수명을 구별하는 값. 그 인스턴스가 발급한 번호는 같은 epoch 안에서만 비교 가능하다.

5. **pid 재사용.** 시그널 직전 `(pid, 시작 시각)`을 기록값과 대조해 같은 프로세스인지 재확인한다(시작 시각은 살아 있을 때 미리 기록).\
   시작 시각을 못 읽었을 때 `None`이면 검사를 건너뛰는 구조는 fail-open이라, 정확히 확인이 가장 필요한 상황에서 검사가 사라진다 → 기록 없음·현재값 못 읽음·불일치 모두 **거부**.\
   그룹 kill 실패 시의 단일 kill 같은 대체 경로도 "조준 없이 쏘는" 경로가 되지 않도록 직전에 재검증해야 한다.\
   검사~시그널 사이 재사용 창은 pidfd(Linux) 같은 커널 핸들 없이 user space에서 완전히 닫을 수 없어 남은 창으로 명시한다.\
   (참고: 대상이 자신의 자식이고 아직 wait로 reap하지 않았다면 좀비가 pid를 점유하므로 그 pid는 재사용되지 않는다 — 창은 reap 이후 또는 자식이 아닌 프로세스에서 생긴다.)
   > **fail-open / fail-closed** — 판정 불가 시 허용하느냐 거부하느냐. 안전 검사는 거부 쪽이 기본값이다.

6. **txId 리셋.** WAL 복구는 로그의 txId로 "이 트랜잭션이 커밋됐나"를 판정한다.\
   메모리 카운터가 기동마다 1부터면 새 tx1이 이전 실행의 커밋된 tx1과 같은 번호를 달아, 복구가 두 기록을 구별하지 못하고 커밋 여부를 오판한다.\
   카운터는 기동 시 로그를 스캔해 최대 txId를 구하고 `max+1`부터 시작한다.\
   단 이 복원은 "발급된 txId가 남은 로그에 모두 나타난다"는 전제에 기대므로, 체크포인트 등으로 로그가 잘리는 구조라면 잘린 구간의 최대값을 놓칠 수 있다 — 그래서 최대 txId(또는 다음 txId)를 체크포인트 같은 영속 메타데이터에 함께 기록하는 것이 일반형이다(이 사례에서는 후속 과제).
   > **WAL(Write-Ahead Log)** — 변경된 데이터를 디스크에 반영하기 전에 그 변경의 로그를 먼저 영속화해, 장애 후 로그 재생으로 커밋된 변경을 복구하는 방식.

7. **정체성 ≠ 상호배제.** 키는 "어느 세대인가"를 구별할 뿐, 같은 id로 두 요청이 동시에 spawn하는 TOCTOU는 막지 못한다 — 둘 다 새 키를 받아 프로세스가 둘 뜬다.\
   그래서 예약(claim)은 남기되, 예약 해제는 `(id, key)` 소유권으로 **자기 claim만** 해제하게 한다(무소유 집합이면 남의 claim을 풀었다).\
   파일명이 id 자체라 같은 파일에 이어 쓰는 자원(재개 시 같은 트랜스크립트)은 키로 격리할 수 없으므로, id당 현재 리더 하나를 리스로 두고 이전 리더가 멈출 때까지 대기(상한 초과 시 기동 거부)하는 **시간 분리**를 쓴다.

## 문제 구조 (추상화 코드)

### 변형 A — 수명 조작 맵을 재사용 id로 키잉
```rust
// ① 문제
struct Registry { handles: HashMap<SessionId, Handles> }
fn waiter(reg: &Registry, id: SessionId) {
    child.wait();
    reg.handles.lock().remove(&id);          // 같은 id의 새 세션 핸들까지 지움
    // ... 5초 뒤 unregister_token(id), remove_file(format!("{id}.hdr"))
}

// ② 고침
struct Key(u64);                              // 단조, "k<n>", k0 파싱 거부
struct Record { key: Key, session_id: SessionId, /* 속성으로 강등 */ }
struct Registry { handles: HashMap<Key, Handles> }
fn waiter(reg: &Registry, key: Key) {
    child.wait();
    reg.handles.lock().remove(&key);          // 옛 key는 새 세션과 절대 같지 않음
    // ... unregister_token(key), remove_file(format!("{key}.hdr"))
}
```
무엇이 깨졌나: 늦은 정리가 이름만 보고 다음 세대 자원(핸들·토큰·파일)을 파괴했다.\
같은 구조: 세대 토큰을 경로마다 덧붙인 중간 수정은 예약 집합·이벤트 payload·회수 주소에서 누락돼 다음 라운드 경합이 됐다 — 주소 교체로만 종결.\
같은 구조: 예약을 무소유 `Set<Id>`로 두면 Drop이 남의 claim을 해제 → `(id, key)` 소유권으로 자기 것만 해제.

### 변형 B — 인스턴스 스코프 번호를 인스턴스 밖에서 사용
```rust
// ① 문제
enum Command { Kill { key: Key } }            // 재기동 후 k1 재발급
fn resolve(&self, key: Key) -> Option<&Session> { self.sessions.get(&key) }

// ② 고침
struct Addr { epoch: String, key: Key }       // 와이어: "<epoch>:k<n>" 한 문자열
enum Command { Kill { addr: Addr } }
fn resolve(&self, addr: &Addr) -> Result<&Session, Error> {
    if addr.epoch != self.epoch { return Err(Error::BadRequest); }   // 다른 인카네이션 거부
    self.sessions.get(&addr.key).ok_or(Error::NotFound)
}
```
무엇이 깨졌나: 재시작 전 주소가 재시작 후의 무관한 대상을 "번호는 맞게" 가리켰다.\
같은 구조: 이벤트 커서 `"<epoch>:<seq>"` — epoch이 바뀌면 키·커서를 함께 폐기하고 재부착은 커서 대신 전체 재읽기.\
같은 구조(클라이언트 측):
```ts
// ① seen[hostId] = lastSeq            // 연결마다 seq가 0부터 → 재접속 후 알림이 영구히 "이미 봄"
// ② seen[`${hostId}#${incarnation}`]  // attach마다 전역 단조 incarnation — 다른 연결이면 칸 자체가 다름
```

### 변형 C — 재사용되는 OS pid에 시그널
```rust
// ① 문제
fn kill_session(s: &Session) {
    if let Some(t) = read_start_time(s.pid) {       // 못 읽으면 None → 검사 통째 skip (fail-open)
        if t != s.start_time { return; }
    }
    if killpg(s.pid, SIGKILL) == ESRCH { kill(s.pid, SIGKILL); }  // 폴백은 무검증
}

// ② 고침
fn kill_session(s: &Session) -> Result<(), Error> {
    let recorded = s.start_time.ok_or(Error::Internal)?;        // spawn 직후 기록, 없으면 거부
    let now = read_start_time(s.pid).ok_or(Error::BadRequest)?; // 현재값 못 읽으면 거부
    if now != recorded { return Err(Error::Mismatch); }
    kill_group(s.pid, SIGKILL, recorded)                         // 폴백 직전에도 재검증
}
```
무엇이 깨졌나: 신원 확인 불가를 통과로 처리하고, 대체 경로가 재사용 pid를 무검증으로 쐈다.

### 변형 D — 영속 기록과 비교되는 id를 메모리에서 리셋
```kotlin
// ① 문제
class TxManager { private val nextTxId = AtomicLong(1) }   // 기동마다 1

// ② 고침
class LogManager {
    fun maxTxId(): Long { /* 로그 레코드 헤더를 순회하며 최대 txId */ }
}
class TxManager(log: LogManager) { private val nextTxId = AtomicLong(log.maxTxId() + 1) }
// 테스트: 1차 실행 commit(tx1) → 재시작 → begin()은 2
```
무엇이 깨졌나: 새 트랜잭션이 과거의 커밋된 트랜잭션과 같은 번호를 달아 복구가 둘을 구별하지 못했다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log
