# issue/concurrency/critical-section-design — 정답

태그: `race-condition`

## 정답
<!-- 질문 1:1 대응 -->

1. **조회와 행동이 다른 임계구역에 있다.** 조회 락을 푼 순간부터 등록 락을 잡기까지 다른 스레드가 같은 조회를 끝낼 수 있어, 두 쪽 모두 "없음"을 근거로 행동한다.\
   고침은 조회·등록을 한 락 구간에서 하는 원자 연산(`open_or_attach`)이다 — 락 안에서 "있으면 attach, 없으면 등록"까지 결정한다.\
   이 사례에서는 spawn 자체도 TOCTOU 방지를 위해 의도적으로 락 안에 남겼고(지연 위험은 기록, 예약 패턴은 후속), 구독 실패 시 만든 프로세스를 제거해 고아를 막았다.
   > **check-then-act** — 상태를 확인한 결과에 따라 행동하는 코드. 확인과 행동이 한 원자 구간이 아니면 그 사이 변화가 확인을 무효로 만든다.

2. **복합 불변식은 개별 락으로 보호되지 않는다.** 각 맵의 연산은 원자적이어도 "세 맵이 서로 일치한다"는 불변식은 여러 맵을 동시에 바꿀 때만 유지된다.\
   락이 따로면 한 맵만 갱신된 중간 상태를 다른 스레드가 보거나, 두 스레드의 갱신이 맵마다 다른 순서로 섞인다(tear).\
   정리 경로에서 한 맵만 지우고 다른 맵을 빠뜨리면 유령 항목도 남는다.\
   함께 일관돼야 하는 자료구조는 하나의 Mutex 아래 한 구조체로 둔다.

3. **새로 추가된 세션이 키째 사라진다.** 제거 쪽이 "원소 제거 → 비었나 확인 → 키 삭제"를 따로 하면, "비었다"고 판단한 직후 다른 스레드가 같은 집합에 새 세션을 추가하고, 이어서 키 삭제가 그 새 원소가 든 집합을 통째로 날린다.\
   추가 쪽도 "없으면 집합 생성" 뒤의 `add`가 원자 구간 밖이면 같은 창이 생긴다.\
   per-key 원자 갱신으로 바꾼다 — 추가는 `compute` 람다 안에서 add, 제거는 `computeIfPresent` 람다 안에서 remove 후 비었으면 `null`을 반환해 원자적으로 키를 지운다.\
   (주입된 맵 구현의 `compute`가 원자적이라는 가정은 기존 블로킹 구현과 같은 가정으로 유지됐다.)
   > **per-key 직렬화** — 동시 맵이 같은 키에 대한 람다 실행을 직렬화해, 그 키의 check-then-act를 한 구간에서 끝내게 하는 것. `ConcurrentHashMap`의 `compute` 류는 이를 보장하지만, `ConcurrentMap` 인터페이스의 기본 구현이나 `ConcurrentSkipListMap`처럼 원자 1회 적용을 보장하지 않는 구현도 있으므로 구현 문서를 확인해야 한다. 또 집합을 람다 밖에서 읽는 경로가 있으면 집합 자체도 스레드 안전해야 한다.

4. **락이 전역 직렬화 지점이 된다.** 락 보유 시간 = 가장 느린 I/O 시간이므로, 한 호스트의 30초 원격 호출이 모든 호스트의 폴링·attach·detach를 멈추고, 한 세션의 join 대기가 다른 세션의 write·close를 막는다.\
   "맵은 큐가 아니라 색인"이란, 맵 락은 **항목을 찾는 동안만** 필요하다는 뜻이다.\
   항목을 `Arc`로 보관해 핸들만 복제하거나 맵에서 꺼낸 뒤 락을 풀고, 느린 작업은 락 밖에서 한다.\
   목록 조회도 락 안에서는 필요한 값만 복제하고, 서브프로세스 실행은 락 밖에서 한다.

5. **shutdown은 그 소켓의 대기만 깨운다.** 상대가 입력을 읽지 않으면 pty로의 `write_all`이 블록되는데, 이 스레드는 공유 Mutex를 쥔 채 멈춘다.\
   소켓 shutdown은 그 소켓에서 파킹된 read(·write)를 깨울 뿐, 다른 fd(pty)에서 블록된 write는 풀지 못한다.\
   그래서 같은 세션의 다른 뷰어는 `lock()`에서 얼고, 연결 스레드가 반환하지 않아 최대 연결 슬롯(32)이 반납되지 않고, 결국 health·목록 요청까지 거부됐다(사용자에게는 "말없이 사라지는 타이핑").\
   세션당 전용 writer 스레드가 **아무 락도 쥐지 않고** 블로킹 write를 하고, 호출자는 유계 큐(64KiB)에 바이트를 넘긴다.\
   큐가 대기 상한(1초) 안에 비지 않으면 "정체된 터미널" 에러를 알리고 attach를 끝낸다(20초 무응답·통지 0 → 1초 에러 통지).
   > **역압(backpressure)** — 소비자가 느릴 때 그 지연이 생산자 쪽으로 전달되는 것. 락을 거치면 무관한 경로까지 전달된다.

6. **poison.** Rust Mutex는 락을 쥔 스레드가 패닉하면 poisoned 표시가 되고, 이후 `lock()`은 `Err`를 돌려준다.\
   곳곳의 `unwrap()`이 그 `Err`에서 다시 패닉하므로, 한 세션 스레드의 패닉이 공유 맵 락을 타고 모든 세션으로 번진다.\
   회수(`into_inner`)를 한 곳(`sessions_lock()`)에 캡슐화하고 최초 1회만 경고한다.\
   안전 근거는 "상태가 세션별이라서"가 아니라(오염될 수 있는 것은 맵이다) "락 아래 임계구역이 실질적으로 패닉하지 않는다"여야 한다고 리뷰에서 정정됐다.\
   예외적으로 존재 확인은 poison 시 보수적으로 `false`를 돌려, 죽은 세션이 살아 있는 것처럼 보이지 않게 했다.
   > **poison** — 패닉으로 중단된 임계구역이 불변식을 깬 채 남았을 수 있음을 다음 사용자에게 알리는 Mutex 표식.

7. **임계구역의 위치.** single-flight는 "같은 작업"을 하나의 진행 중 작업으로 합쳐 임계구역을 **작업 단위**에 둔다.\
   요청 정체성 in-flight 가드는 임계구역을 **실제 부작용 호출**과 요청 키(인자 포함)에 둔다.\
   외부 저장소 원자 스크립트는 임계구역을 **저장소 서버 한 번의 실행** 안에 둔다.\
   파일 락 check-and-set은 임계구역을 **프로세스 경계 밖**(파일 시스템 락)으로 옮긴다.\
   자세한 비교는 아래 「방안 비교」.

## 문제 구조 (추상화 코드)

### 변형 A — check-then-act와 쪼개진 락
```rust
// ① 문제
struct Runtime { live: Mutex<HashMap<Key, Id>>, by_id: Mutex<HashMap<Id, Sess>>, attached: Mutex<..> }
fn open(&self, k: Key) {
    if self.live.lock().get(&k).is_none() {       // 조회 (락 해제)
        let id = spawn();                          // 다른 스레드도 여기 도달 → 이중 spawn
        self.live.lock().insert(k, id);
        self.by_id.lock().insert(id, sess);        // 두 맵 사이 tear
    }
}

// ② 고침
struct Runtime { live: HashMap<Key, Id>, by_id: HashMap<Id, Sess>, attached: /* ... */ }
fn open_or_attach(rt: &Mutex<Runtime>, k: Key) {
    let effects = {
        let mut rt = rt.lock();
        match rt.live.get(&k) { Some(id) => attach(&mut rt, *id), None => register(&mut rt, k) }
        // 락 안: 상태 변경 + "해제 후 실행할 부작용" 목록 계산
    };
    for e in effects { e.run(); }                  // emit·remove 등은 락 밖
}
```
무엇이 깨졌나: 조회와 등록 사이 창에서 이중 spawn이, 맵별 락 사이에서 불일치가 생겼다.\
같은 구조: stale 정리가 한 맵만 지워 유령 항목이 남음 → 같은 구역에서 모든 맵 정리.\
같은 구조: 동시 맵에서 `remove → isEmpty → remove(key)` 연쇄
```java
// ① set = map.get(p); set.remove(s); if (set.isEmpty()) map.remove(p);   // 사이에 add된 원소가 키째 소실
// ② map.computeIfPresent(p, (k, set) -> { set.remove(s); return set.isEmpty() ? null : set; });
//    map.compute(p, (k, set) -> { var x = set != null ? set : newSet(); x.add(s); return x; });
```

### 변형 B — 락 안의 느린 작업 (원격 호출·join·서브프로세스)
```rust
// ① 문제
fn call(&self, host: HostId, cmd: Cmd) -> Reply {
    let map = self.map.lock();
    map[&host].exec(cmd)                       // 최대 30s — 모든 호스트가 이 락에서 대기
}
fn remove(&self, id: Id) { let mut m = self.map.lock(); let s = m.remove(&id); s.join(); }

// ② 고침
struct Registry { map: Mutex<HashMap<HostId, Arc<Link>>> }
fn call(&self, host: HostId, cmd: Cmd) -> Reply {
    let link = self.map.lock().get(&host).cloned();   // 핸들만 꺼냄
    link?.exec(cmd)                                    // 락 밖
}
fn remove(&self, id: Id) {
    let s = self.map.lock().remove(&id);               // 꺼내기만
    if let Some(s) = s { s.set_dead(); s.join(); }     // 락 밖에서 정리
}
```
무엇이 깨졌나: 한 항목의 지연이 락을 통해 컬렉션 전체의 지연이 됐다.\
같은 구조: 목록 조회가 락 안에서 항목마다 서브프로세스 실행 → 락 안에서는 `(id, cwd)`만 복제, 실행은 락 밖.\
같은 구조: 맵 락을 write·resize·snapshot I/O 내내 보유 — 분석에서 지적됐으나 write 직렬화 승계를 검증할 수 없어 이 범위에서는 적용하지 않음(권고: 항목 `Arc` 복제 후 락 해제).

### 변형 C — 블로킹 write가 공유 Mutex를 쥔 채 정지
```rust
// ① 문제
struct Session { writer: Mutex<Box<dyn Write>> }
fn input(&self, bytes: &[u8]) { self.writer.lock().write_all(bytes); }   // 상대가 안 읽으면 락 보유 채 무기한

// ② 고침
struct Session { input: SyncSender<Vec<u8>> /* 유계 큐 */ }
// 세션당 writer 스레드: 아무 락도 없이 블로킹 write
thread::spawn(move || for chunk in rx { pty.write_all(&chunk)?; });
fn input(&self, bytes: Vec<u8>) -> Result<(), SendError> {
    self.input.send_timeout(bytes, INPUT_WAIT).map_err(|_| SendError::Stalled)   // 상한 초과 → 에러로 알림
    // (std SyncSender에는 send_timeout이 없다 — crossbeam 채널 등 시간 제한 send를 지원하는 유계 채널 전제)
}
// 세션 정리(drop)가 큐를 닫아 writer 스레드 종료
```
무엇이 깨졌나: 상대의 역압이 락을 타고 다른 뷰어·정리 경로·연결 슬롯으로 번졌고, shutdown은 다른 fd의 블록된 write를 풀지 못했다.

### 변형 D — poison을 unwrap으로 받아 장애 전파
```rust
// ① 문제
let s = self.sessions.lock().unwrap();                  // 12곳 — 한 번 poison되면 전부 패닉

// ② 고침
fn sessions_lock(&self) -> MutexGuard<'_, Map> {
    self.sessions.lock().unwrap_or_else(|p| {
        if !WARNED.swap(true, Relaxed) { log_warn("poisoned lock recovered"); }
        p.into_inner()
    })
}
fn exists(&self, id: Id) -> bool {
    match self.sessions.lock() { Ok(m) => m.contains_key(&id), Err(_) => false }   // 보수적 예외
}
```
무엇이 깨졌나: 한 스레드의 패닉이 공유 락을 통해 다른 모든 스레드의 패닉이 됐다(poison 관용 정책도 한 곳에만 있어 불일치).

## 검증 기록
- 2026-09-24: 사건 기록 대조·추상화(Claude 초안)

## 방안 비교

"하나의 불변식 = 하나의 임계구역"을 락 하나로 풀 수 없을 때의 방안들.

### 방안 1 — 요청 정체성 단위 in-flight 가드
```ts
// ① 문제: 가드와 부작용이 형제 문장 — 가드가 호출을 막지 못함, 키에 인자가 없어 다른 요청을 삼킴
setFetching(prev => prev ? prev : true);
void invoke(addr);                                   // 가드와 무관하게 항상 실행

// ② 고침
const key = `${addr}|${JSON.stringify(args)}`;
if (inflight.has(key)) return inflight.get(key);     // 같은 주소·같은 인자 → 합침
if (inflightFor(addr)) generation[addr]++;           // 인자가 다르면 교체(나중 요청이 이김)
inflight.set(key, invoke(addr, args).finally(() => inflight.delete(key)));   // 완료 시 제거 — 안 하면 이후 같은 요청이 영구히 옛 결과에 합쳐짐
```
```rust
// 같은 방안(프로토콜 측): 대상당 한 turn만 in-flight, 나머지는 FIFO
Some(Prompt(t)) => if in_flight { queue.push_back(t) } else { in_flight = true; spawn_turn(t, done_tx) }
_ = done_rx.recv() => match queue.pop_front() { Some(n) => spawn_turn(n, done_tx), None => in_flight = false }
```

### 방안 2 — single-flight (리밋은 작업에, 결과는 공유)
```rust
// ① 문제: 공유 락 안 재스캔(3.4s) → 전부 직렬화 / 락 밖+쿨다운 → 쿨다운 중 "없음"이라는 사실 아닌 답
// ② 고침
fn lookup(&self, root: &Path) -> Result<Project, Error> {
    if let Some(p) = self.cache.fresh(root) { return Ok(p); }     // 게이트 전 캐시 확인 (4.76s → 0.00s)
    let asked_at = now();
    let _g = self.scan_gate.lock();                                // 스캔 직렬화
    if self.last_scan_started() < asked_at {                       // 질문 이후 시작된 스캔이 없을 때만
        self.wait_cooldown(); self.rescan();                       // 리밋은 스캔에 — 답을 거부하지 않고 기다림
    }                                                               // 줄 선 호출자는 앞선 스캔 결과 공유
    self.cache.get(root).ok_or(Error::NotAProject)                 // 에러 문구는 사실대로
}
```

### 방안 3 — 외부 저장소의 원자 스크립트
```python
# ① 문제: 두 명령 사이 실패·경쟁 → TTL 없는 카운터 잔존
n = await store.incr(key)
if n == 1: await store.expire(key, ttl)
# ② 고침: 증가와 만료 설정을 서버 측 스크립트 한 번으로 (스크립트 본문은 기록에 없음)
n = await store.eval(SCRIPT, 1, key, limit, ttl)
# 저장소 장애 시 요청을 막지 않음(fail-open) — 보조 방어 인프라가 서비스를 멈추지 않게
```

### 방안 4 — 프로세스 경계를 넘는 파일 락 + 원자 check-and-set
```python
# ① 문제: 프로세스 내부 asyncio.Lock — 락 밖 단계(승인 대기)·다른 프로세스·재시작을 보호 못함
# ② 고침
def create(state, done_states):
    with file_lock():                          # flock (타임아웃·실패 전파)
        existing = read()                      # 손상 시 "없음" 간주 금지 → 진행 거부(fail-closed)
        if existing and existing["phase"] not in done_states:
            return existing                    # 진행 중 1건 불변식
        write_atomic(state)                    # tmp + rename
        return None
```
같은 방안: 파일 상태 저장소 — 존재검사·생성·교체를 한 임계구역에, 락 획득 실패는 오류로 전파(성공 위장 금지), 락 파일은 정리 대상에서 제외(두 writer가 다른 락을 쓰는 split-lock 방지), 손상 파일은 삭제가 아니라 격리 rename.

| | 방안 1 in-flight 가드 | 방안 2 single-flight | 방안 3 원자 스크립트 | 방안 4 파일 락 CAS |
|---|---|---|---|---|
| 임계구역 | 요청 키(인자 포함)·실제 호출 | 비싼 작업 1회 | 저장소 서버 1회 실행 | 파일 시스템 락 |
| 전제 | 요청 정체성을 정의할 수 있음 | 결과를 호출자끼리 공유해도 됨 | 저장소가 서버 측 스크립트 지원 | 락 의미가 보장되는 파일 시스템(같은 호스트의 로컬 FS가 안전 — NFS 등 네트워크 FS의 flock은 환경마다 다름), 모든 writer가 같은 락 |
| 비용 | 키 설계, 세대 관리 | 뒤 호출자 대기 | 스크립트 관리 | 락 대기, 손상 처리 절차 |
| 실패 모드 | 가드와 호출이 분리되면 무력 | 쿨다운을 "답"에 걸면 사실 아닌 거부 | 장애 시 fail-open 선택의 보안 트레이드오프 | 락 파일 삭제·실패 위장 시 split-lock |
| 맞는 조건 | 같은 대상에 중복·경쟁 요청 | 비싼 조회에 동시 miss 폭주 | 다중 인스턴스가 공유하는 카운터 | 다중 프로세스·재시작을 넘는 불변식 |

**결론**: 불변식이 한 프로세스 안에 있으면 본문 변형처럼 한 락 + 락 밖 부작용이 기본이다.\
요청이 겹치는 것이 문제면 방안 1(같은 요청 합치기) 또는 방안 2(같은 작업 합치기)를 고르되, 결과를 공유해도 되는지가 갈림길이다.\
불변식이 프로세스 밖(여러 인스턴스·재시작)으로 나가면 임계구역도 밖으로 옮겨야 한다 — 공유 저장소가 있으면 방안 3, 파일 기반 상태면 방안 4.

## 방안 비교 — DB의 check-then-act: 한 문장의 존재 확인은 커밋 전 쓰기를 보지 못한다

같은 원리("확인과 행동이 한 원자 구간이 아니면 그 사이 변화가 확인을 무효로 만든다")가 **프로세스 락이 닿지 않는 DB 트랜잭션 사이**에서 나타난 사례.\
그룹(부모 행) 아래에 점유 행(자식)이 생길 때마다 사용자별 집계 행을 함께 늘리는 구조였다.\
그룹이 닫힌 뒤 "그 그룹에 점유가 하나도 없으면 그룹의 집계 행을 전부 지운다"는 정리 작업을 설계했고, 불변식은 **그룹 단위**였다(점유가 하나라도 남으면 그 그룹의 집계 행은 지우지 않는다 — 남은 점유가 나중에 집계를 줄일 때 행이 있어야 한다).\
설계 단계에서 PostgreSQL(READ COMMITTED)로 실험했다.\
정리를 한 문장 `DELETE … WHERE NOT EXISTS (점유)`로 쓰면, 닫히기 직전에 시작해 **아직 커밋되지 않은** 점유 트랜잭션의 행을 보지 못하고 집계 행을 지웠다.\
"집계 행을 잠근 뒤 다시 확인"하는 쌍 단위 방식은 그 쌍은 지켰지만, 같은 그룹의 **다른 사용자**가 진행 중일 때 나머지 쌍을 지워 그룹 단위 불변식을 깼다(설계 교차 검증에서 반례로 지적).\
이 집계 행은 원본(점유 행)의 사본인 카운터다 — 정리가 진행 중 점유의 집계 행을 지우면 [denormalized-counter-drift](../../data/denormalized-counter-drift/)의 "카운터 행 없음" 어긋남이 되고, 이 정리 작업 자체는 [rolled-back-write-cost](../../database/rolled-back-write-cost/) 변형 B가 후속으로 넘긴 "감소만 하고 지우지 않는 카운터 행"의 정리 주체다.

```text
점유 트랜잭션 W                         정리 트랜잭션 C
BEGIN; 열림 확인(열림)
INSERT 점유 행 (커밋 전)
                                       그룹 닫힘 확인(닫힘)
                                       DELETE 집계 WHERE NOT EXISTS(점유)
                                         └─ 커밋 전 점유 행은 보이지 않음 → 삭제
COMMIT ── 점유는 남았는데 집계 행이 없다
```

### 방안 5 — 한 문장 가드 (동시 쓰기가 같은 대상 행을 건드릴 때만 안전)
```sql
-- 같은 작업의 다른 정리(집계 0인 행 삭제)는 이 형태로 남겼다
DELETE FROM agg a
 WHERE a.group_id = :g AND a.cnt = 0
   AND NOT EXISTS (SELECT 1 FROM item i WHERE i.group_id = a.group_id AND i.user_id = a.user_id);
```
진행 중인 점유가 **같은 집계 행**을 먼저 1로 올리는 중이면, DELETE는 그 행 잠금을 기다렸다가 새 버전으로 `cnt = 0`을 다시 보고 건너뛴다(설계 실험·코드 주석 기준).\
반대로 진행 중인 쓰기가 **다른 테이블에만** 행을 넣으면 이 문장은 그것을 볼 방법이 없다 — 위 사례가 이 경우다.\
곁가지(같은 설계 기록): 커밋 전 **삭제**는 아직 행이 보이므로 정리가 "남아 있음"으로 보고 건너뛴다 — 보이지 않는 쪽이 삽입이라 위험 방향이 정해진다.

### 방안 6 — 공통 부모 행을 양쪽이 잠그고, 잠근 뒤 새 문장으로 재확인 (이 사례에서 적용)
```sql
-- 점유 트랜잭션: 첫 문장에서 부모 행 공유 잠금 + 열림 판정
SELECT opens_at FROM grp WHERE id = :g FOR SHARE;
-- ... 점유 INSERT · 집계 갱신 ... COMMIT

-- 정리 트랜잭션
SELECT opens_at FROM grp WHERE id = :g FOR UPDATE;            -- 진행 중 점유의 커밋을 기다린다
-- (잠근 뒤 다시 닫힘 확인 — 그 사이 다시 열렸으면 건너뜀)
SELECT EXISTS (SELECT 1 FROM item WHERE group_id = :g);        -- 새 문장 = 새 스냅숏 → 방금 커밋된 점유가 보인다
DELETE FROM agg WHERE group_id = :g;                           -- EXISTS가 거짓일 때만
```
실험 결과: 진행 중 점유가 있으면 정리는 부모 행에서 막혔다가 커밋 뒤 점유 1건을 보고 **0행 삭제**했다.\
정리가 부모 행을 쥔 동안 들어온 점유는 공유 잠금에서 기다렸다가 정리 커밋 뒤의 "닫힘"을 읽고 거절됐다(행을 다시 만들지 않음).\
공유 잠금끼리는 서로 막지 않아 점유끼리는 직렬화되지 않았다.
> **잠금 단위 = 불변식 단위** — 불변식이 그룹 단위면 쌍(행) 단위 잠금으로는 같은 그룹의 다른 진행 중 쓰기를 보지 못한다. 양쪽이 같은 그룹 행을 잡아야 확인과 행동 사이가 닫힌다.

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 5. 한 문장 가드 | 동시 쓰기가 **지울 그 행**을 먼저 잠근다 | 문장 1개 | 다른 테이블에만 쓰는 커밋 전 트랜잭션은 보이지 않아 지운다 | 조건이 대상 행 자신의 값(`cnt = 0`)으로 닫힐 때 |
| 쌍 단위 잠금 후 재확인 | 불변식이 그 행 안에 있다 | 행마다 잠금 | 불변식이 상위 단위면 다른 구성원의 진행 중 쓰기를 놓친다 | 행 단위 불변식 |
| 6. 공통 부모 행 공유/배타 잠금 + 새 문장 재확인 | 모든 쓰기 경로가 트랜잭션 앞에서 부모 행 공유 잠금을 잡는다, 문장마다 새 스냅숏(READ COMMITTED) | 쓰기마다 잠금 1문장, 정리가 부모 행을 쥔 동안 그 그룹 쓰기 대기 | 잠금을 안 잡는 경로가 하나라도 있으면 샌다, 트랜잭션 스냅숏 격리에서는 새 문장도 같은 스냅숏이라 재확인이 무의미하다(일반론) | 여러 행·테이블에 걸친 그룹 단위 불변식 |
| 프로세스 락 + 단일 인스턴스 ([single-writer-ownership](../single-writer-ownership/) 방안 6) | 실행 인스턴스가 하나 | 설정 규칙 | 인스턴스가 늘면 다시 샌다 | DB 잠금을 걸기 어려운 워커 |

**결론**: 지우려는 행 자체의 조건으로 닫히는 정리는 한 문장 가드(5)가 가장 싸다 — DB가 그 행을 두고 직렬화해 준다.\
조건이 **다른 테이블의 존재**에 걸리면 한 문장은 커밋 전 쓰기를 원리적으로 못 보므로, 불변식과 같은 단위의 공통 행을 모든 경로가 잠그게 하고(6) 잠근 뒤 새 문장으로 다시 확인한다.\
6은 "모든 쓰기 경로가 같은 잠금을 잡는다"는 전제에 기대므로, 잠금을 거치지 않는 경로(직접 쓰기·다른 서비스)가 있는지 함께 확인한다.

검증 기록: 2026-10-15 사건 기록·설계 실험 원문·코드 대조·추상화(Claude 초안).

## 방안 비교 — 잠금을 기다린 한 문장은 잠근 행만 다시 본다 · 트랜잭션 시작 시각은 커밋 순서와 뒤집힌다

같은 원리("확인과 행동이 한 원자 구간이 아니면 그 사이 변화가 확인을 무효로 만든다")가 **자원 행(대상) + 점유 행(만료 시각이 있는 자식)** 구조에서 두 번 더 나타났다.\
앞 절의 방안 6("잠근 뒤 새 문장으로 재확인")이 왜 필요한지를 PostgreSQL READ COMMITTED의 재평가 규칙으로 보이는 경우(방안 7)와, 새 문장으로도 막지 못하는 **시각 비교의 역전**(방안 8)이다.\
만료 판정은 모든 경로가 DB 한 시계(`now()` — 트랜잭션 시작 시각)로 한다 — 앱 인스턴스마다 시계가 다르면 빠른 인스턴스가 갓 만든 점유를 만료로 볼 수 있어서다.

### 방안 7 — 잠금과 판정을 한 문장으로 (문제 — 선택하지 않은 방법)
```sql
-- Y: 자원 행을 잠그면서 같은 문장에서 "활성 점유 없음"을 본다
SELECT EXISTS (SELECT 1 FROM claim c WHERE c.res_id = r.id AND c.expires_at > now()) AS active
  FROM res r WHERE r.id = :id FOR UPDATE;
```
```text
X: SELECT … FROM res WHERE id = :id FOR UPDATE      ← 행을 잠그기만 하고 쓰지 않는다
X: INSERT INTO claim (res_id, expires_at …)          (커밋 전)
                                      Y: 위 한 문장 → res 행 잠금에서 X를 기다림
X: COMMIT
                                      Y: 잠금 획득 → 재평가(EPQ)는 res 행의 조건만 최신 버전으로 다시 본다
                                         하위 질의는 문장 시작 스냅숏 그대로 → X의 점유를 못 봄 → active = false
                                      Y: 새 문장으로 같은 질의 → active = true   (재현 테스트 결과)
```
X가 자원 행을 **쓰지 않고 잠그기만** 했으므로 그 행 버전이 바뀌지 않는다 — 재평가가 돌더라도 하위 질의가 보는 다른 테이블의 새 행은 들어오지 않는다.\
이 판정을 그대로 쓰면 Y는 "활성 없음"으로 보고 두 번째 활성 점유를 만든다 — 재현 테스트는 이 판정값의 차이(한 문장 false · 새 문장 true)까지 확인했다.
> **EPQ(EvalPlanQual)** — READ COMMITTED에서 `UPDATE`·`DELETE`·`SELECT … FOR UPDATE`가 잠긴 행을 기다린 뒤, 그 행의 최신 버전으로 WHERE 조건을 다시 평가하는 절차. 다시 보는 것은 대상 행이지 문장의 다른 테이블 스냅숏이 아니다.

### 방안 6 재적용 — 잠근 뒤 새 문장으로 판정 (이 사례의 선택)
```sql
SELECT id FROM res WHERE id = :id FOR UPDATE NOWAIT;                       -- 잠금만
SELECT r.status, EXISTS (SELECT 1 FROM claim c WHERE c.res_id = r.id AND c.expires_at > now()) AS active
  FROM res r WHERE r.id = :id;                                             -- 새 문장 = 새 스냅숏(앞 잠금 주인의 커밋 포함)
```
같은 이유로(설계 근거) 배치의 "자원 상태 되돌리기"도 `UPDATE … WHERE status = 'HELD' AND NOT EXISTS (활성 점유)` 한 문장으로 하지 않고, 먼저 `FOR UPDATE SKIP LOCKED`로 잠근 뒤 새 문장으로 되돌린다 — 한 문장이면 재평가가 `status`만 다시 보고 막 커밋된 재점유를 못 봐 자원을 비어 있음으로 되돌릴 수 있다.

### 방안 8 — 시각이 아니라 행으로: 잠근 자원의 최신 상태를 먼저, 그다음 "다른 활성 점유 없음" (이 사례의 선택)
```text
시각 역전: 나중에 시작한 Y(now() 큼)가 먼저 시작한 X(now() 작음)보다 먼저 커밋한다
 ① X: 확정 시작 t0 < 만료 te (X의 now() = t0) — 자원 잠금 앞에서 늦어짐
 ② Y: te 뒤 재점유 — Y 기준 X의 점유는 만료 → 새 점유
 ③ Y: 확정 — 자원 RESERVED · Y 점유 삭제 · 결과 행 INSERT · COMMIT
 ④ X: 자원 잠금 획득
    "내 점유 활성?"을 먼저 보면: X 기준(t0) 활성 · Y 점유는 지워져 "다른 활성 없음" → 통과 → 확정 둘(이중 판매)
    잠근 자원의 최신 status를 먼저 보면: RESERVED → 거부                  ← 고친 순서
```
```sql
SELECT status FROM res WHERE id = :id FOR UPDATE;            -- ① 기다린다 · 잠금 뒤 최신 커밋 버전을 받는다
-- status = 'RESERVED' → 거부(여기서 끝)
SELECT c.expires_at > now() AS mine_active,
       EXISTS (SELECT 1 FROM claim o WHERE o.res_id = c.res_id AND o.id <> c.id AND o.expires_at > now()) AS other_active
  FROM claim c WHERE c.id = :mine FOR UPDATE;                -- ② 잠근 뒤 새 문장 + 내 점유 행 잠금(정리·회수가 이 행을 기다리게)
-- 행 없음 → 이미 회수됨 · mine_active = false 또는 other_active = true → 만료로 거부
```
무엇이 깨졌나: "내 점유가 내 시각으로 활성"은 다른 트랜잭션이 더 늦은 시각으로 이미 내린 결론(만료 → 재점유 → 확정)을 보지 못한다 — 시각은 트랜잭션마다 고정이라 커밋 순서와 어긋난다.\
두 역전 시나리오(남의 확정 · 남의 재점유)를 동시성 테스트로 두었고, 고친 순서에서 각각 "자원 상태로 거부" · "다른 활성 점유로 거부"가 됐다.\
판정 시각 오차(트랜잭션 시작 vs 판정 순간)는 부하 중 실측 최대 12.9ms였다 — 오차는 보수 쪽(막 만료된 점유를 아직 활성으로 봄)으로만 작용하게 두고, 정확성은 행 판정에 맡겼다.

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 7. 잠금 + 하위 질의 한 문장 | 동시 쓰기가 **잠그는 그 행**을 바꾼다(그래야 재평가가 본다) | 문장 1개 | 다른 테이블에 쓰거나 잠그기만 한 동시 트랜잭션의 커밋을 못 본다 — 조용한 이중 점유 | 조건이 잠근 행 자신의 열로 닫힐 때(방안 5와 같은 조건) |
| 6. 잠근 뒤 새 문장 | READ COMMITTED(문장마다 새 스냅숏), 모든 쓰기 경로가 같은 행을 먼저 잠근다 | 문장 1개 추가 | 시각 비교가 남아 있으면 커밋 순서 역전은 여전히 통과한다(방안 8의 몫) | 다른 테이블의 존재로 판정할 때 |
| 8. 행 판정 + 판정 순서 | 잠금이 최신 커밋 버전을 돌려준다(`FOR UPDATE` 재평가), 확정이 자기 점유를 지우는 구조를 안다 | 판정 질의 확장 · 순서 계약(응답 코드가 달라질 수 있다) | 순서를 바꾸면(내 점유 먼저) 역전이 다시 통과한다 — 순서가 계약이다 | 트랜잭션 시작 시각으로 만료를 판정하는 모든 확정 경로 |

**결론**: 잠금을 기다린 문장의 재평가는 **잠근 행만** 최신으로 본다 — 다른 테이블의 존재로 판정하면 판정은 잠근 **뒤의 새 문장**으로 한다(방안 6).\
트랜잭션 시작 시각으로 만료를 판정하면 커밋 순서와 시각 순서가 뒤집힐 수 있으므로, 최종 판정은 시각 비교가 아니라 **잠근 자원 행의 최신 상태 → 다른 활성 점유 없음** 순서의 행 판정으로 한다(방안 8).\
한 문장 판정(방안 7)은 조건이 잠근 행 자신의 열로 닫힐 때만 안전하다 — 앞 절 방안 5와 같은 경계다.\
검증 기록: 2026-11-04 설계 기록·재현 테스트·동시성 테스트 대조·추상화(Claude 초안) — 방안 7의 "한 문장은 못 보고 새 문장은 본다"는 재현 테스트로 확인(이중 점유 자체는 판정값에서 추론), 배치 되돌리기는 설계 근거, 방안 8의 두 역전 시나리오는 동시성 테스트로 확인, EPQ 동작 설명은 PostgreSQL 문서의 READ COMMITTED 절(일반 근거).
