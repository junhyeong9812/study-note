# cs/issue/reliability/cleanup-on-every-exit-path — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 이슈 원문 기준. 복습 전 읽지 말 것.

태그: `resource-bounding`

## 정답
<!-- 질문 1:1 대응 -->

1. **경로마다 정리는 샌다.** 종료 경로는 코드가 자랄수록 늘어난다(새 에러 분기·`?` 조기 반환·취소·패닉 unwinding). 각 경로에 정리 줄을 복사하면 하나만 빠져도 상태가 거짓이 된다(죽었는데 `is_alive = true`라 쓰기 거부가 안 됨).\
RAII Drop·`try/finally`·`trap`은 **"스코프를 떠나는 모든 방법"에 정리를 한 번 붙인다** — early return·future drop·예외·패닉까지 포함해 정리가 반드시, 한 번 실행된다.\
단, 가드를 만들기 **전에** 실패하는 경로(예: 런타임 생성 실패)는 가드가 없으므로 따로 처리해야 한다.\
또 이 보장은 "프로세스가 살아서 스코프를 빠져나갈 때"까지다 — `SIGKILL`·전원 차단·`os._exit`/`std::process::exit`·Rust `panic = "abort"`·`mem::forget`처럼 unwinding 없이 끝나면 Drop·finally·trap도 돌지 않는다(그 몫은 기동 시 복구·lease 만료 같은 바깥 장치).
   > **RAII** — 자원 획득을 객체 생성에, 해제를 객체 소멸(스코프 종료)에 묶는 관용구.

2. **permit 회계의 두 방향.** ① **획득 없이 반납**: 즉시 실행 경로가 permit을 안 받고도 `finally`에서 반납 → 카운터가 음수로 내려가 동시성 한도가 사실상 없어진다.\
② **예외 경로 반납 누락**: 취소 검사 같은 던질 수 있는 호출이 `try` **밖**에 있어, 거기서 던지면 `finally`가 안 돈다 → permit이 새어 한도가 0으로 수렴하고 실행기가 멈춘다.\
둘 다 예외를 밖으로 내지 않고 카운터 숫자만 틀어지므로 조용하다 — 증상은 한참 뒤 "동시성 제한이 안 먹음"이나 "작업이 안 돈다"로 나타난다.\
교정: 획득 여부를 **생성 시 확정되는 플래그**로 기억해 그때만 반납하고, 던질 수 있는 호출까지 `try` 범위를 넓힌다.
   > **permit** — 세마포어가 동시 실행 수를 세기 위해 나눠 주는 허가 토큰.

3. **spawn 실패 분기.** 회수 담당(waiter 스레드·워커)이 없으면 아무도 회수하지 않는다 — 자식 프로세스는 좀비로, 용량 카운터는 영구 감소 안 된 채로, openpty로 만든 fd는 열린 채로 남는다.\
"자원 먼저 확보 → 회수 담당 띄우기" 구조에서는 **띄우기 실패 분기가 확보한 자원을 직접 되돌려야** 한다(kill+wait, 카운터 감소, fd close) — 그리고 실패를 알린다.\
이 분기는 평소 안 타므로 테스트에서 실패를 **주입**해 "회수를 지우면 테스트가 잡는다"를 확인한다.

4. **가로챈 닫기.** `preventDefault()`를 부르는 순간 창을 닫을 책임이 전부 이쪽 코드로 넘어온다. 이후 비동기 정리가 예외를 던지면 `destroy()`에 도달하지 못한다 → `finally`에서 반드시 `destroy()`.\
그러나 정리가 **예외 없이 멈추면**(ack를 영원히 기다림) `finally`도 오지 않는다 → **watchdog 타이머**(일정 시간 뒤 강제 destroy)가 필요하다. destroy가 두 번 불려도 무해하게 만든다.\
한계: 이벤트 루프 자체가 멈추면 `finally`도 watchdog도 돌지 않는다 — 그 경우는 바깥(네이티브 쪽) 보완이 필요하다.
   > **watchdog** — 정해진 시간 안에 완료 신호가 없으면 강제 조치를 하는 감시 타이머.

5. **유일한 종료 문.** 경로마다 규칙을 복사하면 새 경로(적용 성공 후 닫힘·동반 닫힘·다른 창으로 전송)가 생길 때마다 우회가 생긴다.\
교정: 종료 사유(reason)별 동작을 **정책표** 하나로 정의하고, 모든 경로가 **유일한 종료 함수**(`exit(reason)`)를 거치게 한다.\
마무리 실패는 성공으로 삼키지 않고 오류로 올려 닫기를 막는다(fail-closed). "비었다" 같은 판정은 불완전한 로컬 상태(아직 도착 안 한 스냅샷) 대신 정본을 가진 쪽에 맡긴다.

6. **정리용 context.** 취소 가능한 요청 context를 정리에 넘기면 **취소 신호가 정리까지 막는다** — 요청이 끊긴 순간 `unlock(ctx)`가 즉시 실패하고, 락은 lease 만료까지 샌다.\
정리는 요청 context와 분리된 **별도 context(자체 타임아웃)**로 한다.\
반대로 "수락(내구 기록)까지 끝난 작업의 실행"을 요청 context에 묶으면 클라이언트 단절이 실행을 죽인다 → 수락 뒤에는 **bounded background context**로 떼어 낸다.\
부가 함정: 취소 전파를 끊은 context(Go 1.21+ `context.WithoutCancel`)의 `Done()`은 nil이라 `select`의 그 가지는 영원히 안 걸리는 죽은 코드다.

7. **정리 주체 부재와 trap 재진입.** 감시 스레드가 없는 프로세스는 작업 종료를 **누가 조회할 때** 비로소 회수(lazy reap)하므로, 그 전까지 락이 남아 다음 요청이 "사용 중"으로 거부된다.\
시간 기반 정책(승인 대기 TTL)을 UI 연결이나 첫 API 호출에 매달면, 연결·접근이 없을 때 감시 자체가 존재하지 않아 대기 자원이 무기한 방치된다 → **서버 기동 시점에 복구·무장**한다.\
셸에서 `trap 'rollback; exit 1' INT TERM`과 `trap rollback EXIT`를 같이 걸면, 신호 핸들러의 `exit`가 EXIT 트랩을 다시 발화시켜 **rollback이 두 번** 돈다(두 번째가 방금 복원한 백업을 지움) → 핸들러 첫 줄에서 `trap - EXIT INT TERM`으로 재진입을 차단한다.
   > **lazy reap** — 종료된 작업의 정리를 즉시 하지 않고, 다음 조회·접근 시점에 미뤄서 하는 방식.

## 문제 구조 (추상화 코드)

### 변형 A — 상태 플래그·in-flight 등록을 RAII 가드로
① 문제 코드
```rust
fn run(shared: Arc<Shared>) -> Result<()> {
    let s = connect()?;            // 실패 → alive=false 누락
    auth(&s)?;                     // 실패 → 누락
    loop { /* ... 취소·패닉 → 누락 */ }
    shared.set_dead(); Ok(())
}
```
② 고친 코드
```rust
struct AliveGuard { shared: Arc<Shared>, status_tx: Sender<Status> }
impl Drop for AliveGuard {
    fn drop(&mut self) { self.shared.set_dead(); let _ = self.status_tx.send(Status::Closed); }
}
fn run(shared: Arc<Shared>, tx: Sender<Status>) -> Result<()> {
    let _g = AliveGuard { shared, status_tx: tx };   // 첫 줄에서 생성
    let s = connect()?; auth(&s)?; loop { /* ... */ }
}
// 가드 생성 이전의 실패(런타임 생성 실패)는 별도로 set_dead
```
무엇이 깨졌나: 종료 경로 수만큼 정리 줄이 필요했고 하나씩 빠졌다.\
같은 구조: 동시 실행 방지용 in-flight 집합에 수동 insert/remove → 취소·패닉 시 항목 잔류로 영원히 "진행 중" → `if !set.insert(key) { return Busy }` 로 판정+삽입 원자화, 제거는 가드의 Drop.

### 변형 B — 예외 경로에서 해제 누락 (try/finally)
① 문제 코드
```python
master, slave = os.openpty()
self.proc = subprocess.Popen(cmd, stdin=slave, stdout=slave, stderr=slave)   # 실패 → fd 2개 누수
session.attach(client)
await pump(client)            # 예외 → detach 안 됨 → 죽은 클라이언트 큐 누적
session.detach(client)
```
② 고친 코드
```python
master, slave = os.openpty()
try:
    self.proc = subprocess.Popen(cmd, stdin=slave, stdout=slave, stderr=slave, close_fds=True)
except Exception:
    os.close(master); os.close(slave); raise
os.close(slave)                       # 부모 쪽 slave도 닫는다 — 안 닫으면 누수 + 자식 종료 후에도 master에 EOF/EIO가 안 옴
pump = None
try:
    session.attach(client)
    pump = start_pump(client)
    await pump
finally:
    session.detach(client)            # pump 미생성이어도 안전하게
```
무엇이 깨졌나: 획득 뒤 예외 경로에 해제가 없었다.\
같은 구조: 컨테이너 종료 콜백이 정리 스크립트 실행 후 DB shutdown — 스크립트가 던지면 shutdown에 도달 못 하고, 예외는 경고 한 줄로 삼켜지며, JVM 수명 인메모리 DB가 남아 **다음 테스트 컨텍스트**가 "table already exists"를 만남 → `try { runCleaner(); } finally { shutdownDatabase(); }` (초기화 경로는 이미 실패 시 shutdown하는데 종료 경로만 비대칭이었다).\
같은 구조: `preventDefault()`로 가로챈 닫기 → 아래.
```ts
const watchdog = setTimeout(() => { void win.destroy().catch(() => {}) }, 4000)   // 멈춤 대비
try { /* 종료 이벤트 발행, ack 대기, 보조 창 정리 */ }
catch (err) { console.error("teardown failed; closing anyway", err) }
finally { clearTimeout(watchdog); await win.destroy().catch(() => {}) }           // 예외 대비
```

### 변형 C — permit 회계: 획득했을 때만, 정확히 한 번
① 문제 코드
```java
// 즉시 실행 경로: permit 획득 안 함
void run() {
    checkCancelled(future);                 // try 밖 — 여기서 던지면 반납 누락
    try { task.run(); }
    finally { throttle.afterAccess(); }     // 획득 안 한 경로도 반납 → 카운트 음수
}
```
② 고친 코드
```java
final boolean releaseThrottle;             // 생성 시 확정: 획득 경로=true, 즉시 경로=false
void run() {
    try {
        checkCancelled(future);            // 보호 범위 안으로
        task.run();
    } finally {
        if (releaseThrottle) throttle.afterAccess();
    }
}
```
무엇이 깨졌나: 반납 여부를 기억하는 상태가 없었고, 던지는 호출이 보호 범위 밖에 있었다.

### 변형 D — 회수 담당 spawn 실패 분기
① 문제 코드
```rust
let child = spawn_process()?;
live_slots.fetch_add(1);
thread::Builder::new().spawn(move || waiter(child))?;   // 실패 → child 좀비, 슬롯 영구 점유
```
② 고친 코드
```rust
// child를 클로저로 move하면 spawn 실패 시 클로저와 함께 drop돼(Child의 drop은 kill·wait 안 함) 회수할 손잡이가 사라진다 → 공유 슬롯에 둔다
let slot = Arc::new(Mutex::new(Some(spawn_process()?)));
live_slots.fetch_add(1);
notify(SessionSpawned);                                  // 상태 역행 방지: 스레드 기동 앞으로
let s2 = Arc::clone(&slot);
if let Err(e) = thread::Builder::new().spawn(move || { if let Some(c) = s2.lock().unwrap().take() { waiter(c) } }) {
    if let Some(mut c) = slot.lock().unwrap().take() { let _ = c.kill(); let _ = c.wait(); }   // 직접 회수
    live_slots.fetch_sub(1);
    notify(Notice("spawn failed")); notify(SessionExited);
    return Err(Internal(e));
}
// 테스트: 스레드 생성 실패를 주입해 "회수 제거 시 pid가 남는다"를 확인
```
무엇이 깨졌나: 회수를 맡을 주체가 생기지 못한 분기에서 확보한 자원이 주인을 잃었다.

### 변형 E — `?` 조기 반환이 teardown을 건너뜀 + raw 구간 전환 뒤 실패
① 문제 코드
```rust
write_line(sock, "Attached")?;         // 이후는 raw 바이트 구간
let pump = start_input_pump()?;        // 실패를 여기서 보고 → 터미널에 JSON 쓰레기
write_replay(sock)?;                   // 조기 return → pump 스레드 teardown 건너뜀
run_raw(sock, pump); pump.teardown();
```
② 고친 코드
```rust
let pump = start_input_pump().map_err(reject_before_raw)?;   // 실패 가능 작업은 전환 전에
let res = (|| { write_line(sock, "Attached")?; write_replay(sock)?; run_raw(sock, &pump) })();
pump.teardown();                                             // 클로저 밖 — 모든 경로
res
```
무엇이 깨졌나: 조기 반환이 정리 코드를 우회했고, 프로토콜 전환 뒤에는 구조화된 에러를 낼 방법이 없었다.

### 변형 F — 여러 종료 경로가 마무리를 우회
① 문제 코드
```ts
onTabClose = () => archiveThenClose()      // 규칙이 × 버튼에만
onApplySuccess = () => closeTab()          // 우회
onParentClosed = () => closeTab()          // 우회
onMoveToWindow = () => detach()            // 우회
```
② 고친 코드
```ts
const EXIT_POLICY: Record<ExitReason, "archive" | "detach"> = { /* 경로별 정책표 */ }
async function exit(reason: ExitReason) {            // 유일한 종료 문
  if (EXIT_POLICY[reason] === "archive") {
    const r = await archive()                        // "비었다" 판정은 정본(백엔드)에 위임
    if (r.errors.length) throw r.errors              // 부분 실패를 성공으로 삼키지 않음
  }
  close()
}
```
무엇이 깨졌나: 종료 경로마다 마무리를 따로 구현해 새 경로가 생길 때마다 우회가 생겼다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log

## 방안 비교

기본 방안(위 변형 A~F)은 "정리를 스코프 소멸에 묶어 모든 경로에서 한 번 실행"이다. 같은 원리에 정리의 **주체·시점·도구**가 달라 다른 방안이 쓰인 사례:

### 방안 1 — 인수(adopt)한 레코드에도 종료 관측·정리 주체 연결
```rust
// 문제: 정리 경로(waiter·prune)가 자기가 spawn한 레코드에만 연결
fn on_spawn(r: Rec)  { registry.insert(r.id, Running); spawn_waiter(r) }   // 종료 관측 O
fn on_adopt(r: Rec)  { registry.insert(r.id, Running) }                    // 종료 관측 X
fn prune_exited()    { registry.retain(|_, s| *s != Exited) }              // Running은 안 지움
// → 인수 프로세스가 죽어도 id 예약이 데몬 수명 내내 유지, 끝난 tail도 계속 폴링
// 필요한 것: adopt 경로에도 종료 관측자(pid watch) + 완료 시 tail 해제 연결
```
원문에서는 미해결 — 알려진 창으로 등재됐다.

### 방안 2 — 정리는 취소되지 않는 별도 context로
```go
// 문제
defer lock.Release(reqCtx, key)             // 요청 취소 → 해제 즉시 실패 → lease 만료까지 누수
// 고친
defer func() {
    ctx, cancel := context.WithTimeout(context.Background(), releaseTimeout)
    defer cancel()
    lock.Release(ctx, key)
}()
// 수락(내구 기록) 뒤 실행도 요청 ctx가 아니라 bounded background ctx로
```

### 방안 3 — 종료 감시 주체가 없을 때: lazy reap을 알고 우회 → watch로
```text
문제: 작업 완료 후에도 락 유지 → 다음 작업 409 "락 사용 중"
원인: 완료를 감시하는 스레드가 없고, 작업 목록 조회(GET /jobs)가 회수(reap)의 유일한 트리거
실제 대응: 작업 사이에 목록 조회를 끼워 넣도록 런북화
근본 대응: 완료를 능동 관측(watch)하는 주체를 둔다
```

### 방안 4 — 시간 기반 감시는 서버 기동 시 무장
```python
# 문제: 복구·TTL 감시가 API 첫 호출 때 lazy 실행 / 대기 단계 감시가 UI heartbeat에 매달림
#       → 재시작 후 접근이 없으면, 또는 UI가 끊기면 대기 자원 무기한 방치
@asynccontextmanager
async def lifespan(app):
    recover_on_boot()          # 기동 즉시 상태 복원 + TTL 재무장 (deadline 없으면 보정)
    yield
def heartbeat_should_cancel():
    return current.phase in ACTIVE_STATES      # heartbeat 취소는 실행 단계만, 대기는 TTL이 담당
def approval_ttl_min():                        # import 시점(모듈 최상위)이 아니라 사용 시점에 읽음
    return int(os.environ.get("APPROVAL_TTL_MIN", 60))
```

### 방안 5 — 셸: trap 재진입 차단 + staging 후 mv
```bash
# 문제
trap 'rollback; exit 1' INT TERM
trap rollback EXIT                   # 신호 → rollback → exit → EXIT trap → rollback 한 번 더
cp -r "$DEST" "$BACKUP"              # 부분 실패 시 백업 자체가 반쪽
# 고친
cleanup_fail() {
  trap - EXIT INT TERM               # 재진입 차단
  set +e                             # 원복 하나 실패해도 나머지 전부 시도
  # ... 백업 복원
  exit 1
}
trap cleanup_fail EXIT INT TERM
mv "$DEST" "$BACKUP"                 # 백업은 mv (부분 파괴 없음)
mv "$STAGING" "$DEST"                # staging 검증 후 교체 (mv가 원자 rename이려면 같은 파일시스템)
trap - EXIT INT TERM                 # 성공 경로에서 해제 — 안 하면 정상 종료의 EXIT도 원복을 부른다
# 함수 마지막 문장 `[ -e x ] && cmd` 는 거짓일 때 rc 1 → set -e 즉사 → if 문 + return 0
```

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 기본: 스코프 소멸에 정리 | 자원 소유자가 한 스코프다 | 가드 타입·finally | 가드 생성 전 실패는 별도 처리 | 연결·락·fd·permit |
| 1. 인수 레코드에 관측자 | 남이 만든 자원을 넘겨받는다 | pid watch 추가 | 관측자 없으면 id·tail 영구 점유 | 데몬 재시작 후 인수 |
| 2. 정리용 별도 ctx | 정리가 취소 가능한 호출이다 | ctx 생성 | 타임아웃 없으면 정리가 매달림 | Go·취소 전파 런타임 |
| 3. watch로 종료 관측 | 종료를 알릴 주체가 없다 | 감시 스레드 | lazy reap이면 조회 전까지 락 유지 | 장기 작업 서버 |
| 4. 기동 시 무장 | 시간 기반 정책이다 | 기동 복구 코드 | 연결·요청 의존 시 감시 공백 | TTL·자동 취소 |
| 5. trap 재진입 차단 | 셸 스크립트 원복 | 규율(첫 줄 trap -) | 이중 원복·set -e 조기 중단 | 배포·설치 스크립트 |

**결론**: 자원을 한 스코프가 소유하면 **RAII·finally**로 충분하다.\
정리가 스코프를 벗어나 **시간·다른 프로세스·재시작**에 걸쳐 있으면 "누가 종료를 관측하는가"를 먼저 정한다 — 관측 주체(watch·기동 시 무장)를 두고, 정리 호출 자체는 취소 전파와 분리한다.\
셸처럼 정리 도구가 재진입하는 환경에서는 **정리 핸들러가 스스로를 해제**해 정확히 한 번을 지킨다.
