# cs/issue/concurrency/out-of-order-completion — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 사건 기록 대조·추상화. 복습 전 읽지 말 것.

태그: `race-condition`

## 정답
<!-- 질문 1:1 대응 -->

1. **적용 시점에 최신인지 확인하지 않았다.** 두 요청은 서로 다른 시간에 끝나며, 네트워크·서버 부하에 따라 먼저 보낸 A가 나중에 도착할 수 있다.\
   응답 핸들러가 무조건 `setResults(r)`를 하면 도착 순서대로 덮어쓰므로 마지막에 도착한 옛 A가 최종 상태가 된다 — 에러 없이 틀린 데이터가 정상처럼 보이는 무음 오류다.\
   게다가 옛 요청의 `finally`가 무조건 로딩을 끄면, 최신 요청이 아직 진행 중이어도 스피너가 사라져 "진행 중"이라는 사실까지 숨긴다.
   > **stale overwrite(늦은 결과 덮어쓰기)** — 늦게 도착한 옛 결과가 최신 결과를 덮는 것. 결과가 사라진다는 점은 lost update와 닮았지만, 고전적 lost update(두 read-modify-write가 같은 값을 읽고 서로 덮음)와 달리 원인은 적용 순서다.

2. **조기 return 경로의 in-flight가 살아남는다.** 쿼리를 비우면 토큰을 올리기 전에 return하므로, 이미 날아간 이전 요청의 토큰이 여전히 "최신"이다.\
   그 응답이 늦게 도착하면 빈 목록에 옛 결과가 다시 나타난다.\
   토큰 증가는 effect 진입 즉시, 모든 분기보다 먼저 해야 한다.\
   확인은 await가 끝날 때마다 필요하다 — await 하나당 그 사이 새 요청이 생겼을 수 있으므로(한 사례에서는 모든 await 지점 + `finally`).
   > **세대(generation) 토큰** — 요청마다 증가하는 번호를 캡처해 두고, 결과 적용 직전에 현재 번호와 같을 때만 반영하는 가드.

3. **편집분이 저장되지 않았는데 clean으로 표시된다.** 저장이 시작된 뒤 추가된 편집은 이번 저장에 포함되지 않았는데, 늦게 끝난 저장 성공이 dirty 플래그를 지운다.\
   편집마다 버전을 올리고, 저장 시작 때 버전을 캡처해, 완료 시 버전이 그대로일 때만 clean으로 바꾼다 — 그사이 편집이 있었으면 dirty가 유지된다.

4. **끝난 작업이 영구 RUNNING이 된다.** 두 채널의 도착 순서가 보장되지 않으므로, 이미 FAILED로 끝난 뒤 202 처리가 RUNNING을 무조건 대입해 종결 상태를 과거 전이로 덮는다.\
   상태 전이를 도메인 가드로 통일한다 — 종결 상태면 no-op, 콜백 결과는 적용/반복/충돌을 구분하는 멱등 규칙.\
   그러나 가드는 "읽은 시점의 상태"만 근거로 하므로 두 트랜잭션이 동시에 읽으면 둘 다 통과할 수 있어, 행 단위 비관적 잠금(`SELECT ... FOR UPDATE`)으로 DB 수준 경합을 막았다(경합 재현 테스트 포함).
   > **단조(forward-only) 전이** — 상태가 정해진 순서로만 앞으로 가고 뒤로 돌아가지 않게 제한하는 것. 늦은 이벤트가 최종 상태를 덮지 못한다.

5. **중복 발행.** 세대 토큰은 늦은 결과를 **버릴** 뿐, 요청이 동시에 여러 개 발행되는 것 자체는 막지 않는다.\
   폴링·포커스·수동 새로고침이 겹치면 매번 서브프로세스가 떠 폭주한다.\
   그래서 세 가드를 함께 쓴다 — 토큰(늦은 결과 폐기), in-flight 플래그(진행 중이면 새 요청 skip), busy 플래그(자기 조작 중 tick skip).

6. **새 소켓이 끊긴 것으로 처리된다.** `close()`의 `onclose`는 비동기로 나중에 발화하므로, 동기 블록에서 `ws`를 새 소켓으로 바꾼 뒤 옛 소켓의 핸들러가 `ws = null`을 실행한다.\
   화면은 "연결됨"인데 입력이 전부 버려지고 alive 플래그가 영구 false가 되어, 다음 시작 때 또 재연결하는 영구 재발로 이어졌다.\
   핸들러가 자기 소켓을 지역 변수로 잡고 `if (ws === sock)`일 때만 공유 상태를 건드리게 한다(옛 소켓의 `onclose = null`은 이중 방어).

7. **축을 더 비교해야 하는 경우.** (a) 캐시를 채우는 비동기 작업은 다른 writer·축출(close)까지 고려해 **시작 시점 스냅샷·epoch·소유** 검사가 필요하다(세대 하나로는 발주 전/후 두 경우를 다 못 막음).\
   (b) lazy 조회 응답은 **요청 토큰·대상 세션·데이터 서명** 셋이 모두 같을 때만 반영한다(한 축이 빠지면 그 축으로 stale write가 들어옴).\
   (c) 낙관적 갱신의 비교 기준선은 "보낸 값"이 아니라 **상대가 확인한(ack) 값**이어야 한다.\
   (d) 부모 생성 이벤트는 자식 이벤트를 낼 수 있는 주체를 기동하기 **전에** 발행해 인과 순서를 보장한다.\
   자세한 비교는 아래 「방안 비교」.

## 문제 구조 (추상화 코드)

### 변형 A — 늦은 응답이 최신 상태를 덮음 (세대 토큰)
```ts
// ① 문제
async function search(cond) {
  setLoading(true);
  try { setRows(await api.search(cond)); }
  finally { setLoading(false); }                    // 옛 요청이 최신 요청의 스피너를 끔
}

// ② 고침
async function search(cond) {
  const my = ++seqRef.current;                       // 모든 분기보다 먼저
  const isLatest = () => my === seqRef.current;
  setLoading(true);
  try {
    const rows = await api.search(cond);
    if (!isLatest()) return;                          // await 지점마다
    setRows(rows);
  } finally { if (isLatest()) setLoading(false); }
}
```
무엇이 깨졌나: 늦게 도착한 옛 조건의 결과가 최신 조건 아래 정상처럼 표시됐다.\
같은 구조: 조기 return(빈 쿼리) 분기가 토큰 증가보다 앞 → 비운 목록에 옛 결과 재등장.\
같은 구조: 프로젝트 전환 중 이전 대상의 목록·상태 응답이 새 화면을 덮음 → 응답에 대상 키도 바인딩, 전환 effect 진입 즉시 파생 상태 비우기.\
같은 구조: 저장 중 편집 → `const v = version; await save(); if (v === version) markDirty(false)`.\
같은 구조: 폴링 정리 규칙("연속 두 번 없으면 삭제")이 완료 순서를 셈 → 낡은 응답 둘이 살아 있는 데이터 삭제, 세대로 늦은 답 폐기.\
같은 구조: 조회 실패를 `.catch(() => [])`로 삼켜 "없음"과 "실패"가 구분 불가 → 중복 생성 요청(늦은 응답 덮어쓰기와 함께 보고됨).

### 변형 B — 늦은 과거 전이가 종결 상태를 덮음 (단조 전이)
```java
// ① 문제
void onAccepted(Job j) { j.setStatus(RUNNING); }     // 완료 콜백이 먼저 왔으면 FAILED → RUNNING

// ② 고침
boolean setRunning() {
    if (status.isTerminal()) return false;            // 종결 후엔 no-op
    status = RUNNING; return true;
}
Job j = repo.findWithLockById(id);                    // SELECT ... FOR UPDATE — 가드의 읽기-쓰기 사이 경합 차단
```
무엇이 깨졌나: 도착 순서가 보장되지 않는 두 채널에서 늦은 "수락"이 "완료"를 덮었다.\
같은 구조(스트림 재조립):
```rust
// ① item.status = InProgress;                               // 늦게/중복 온 요청 이벤트가 Completed를 강등
// ② if item.status == Pending { item.status = InProgress; } // Pending일 때만 승격
//    if is_new { item.turn = turn; item.cwd = cwd; }         // 첫 등장 값 고정 — 엔티티를 만들 수 있는 모든 진입점(요청·결과)에서 같은 규칙
```

### 변형 C — 비동기 등록/해제 교차 (세 지점 세대 검사)
```ts
// ① 문제
let disposed = false;
listen(evt, h).then(un => { if (disposed) un(); else unlisteners.push(un); });   // init A→dispose→init B→A resolve 교차 미방어

// ② 고침
let generation = 0;
function init() {
  const gen = ++generation;
  listen(evt, e => { if (gen !== generation) return; /* ... */ })   // 핸들러
    .then(un => { if (gen !== generation) { un(); return; } unlisteners.push(un); });  // 등록 완료
  return () => disposeGeneration(gen);                               // disposer도 자기 세대에 바인딩
}
```
무엇이 깨졌나: 옛 세대 리스너가 새 세대 목록에 섞이고, 옛 disposer가 다음 세대를 해제했다.

### 변형 D — 늦은 핸들러가 교체된 공유 참조를 지움 (인스턴스 동일성)
```js
// ① 문제
function connect() {
  ws = new WebSocket(url);
  ws.onclose = () => { ws = null; setStatus("끊김"); };   // 옛 소켓의 onclose가 새 ws를 지움
}

// ② 고침
function connect() {
  const sock = new WebSocket(url);
  ws = sock;
  sock.onmessage = e => { if (ws === sock) render(e.data); };
  sock.onclose   = () => { if (ws === sock) { ws = null; setStatus("끊김"); } };
}
function reconnect() { if (ws) { ws.onclose = null; ws.close(); } connect(); }   // 이중 방어
```
무엇이 깨졌나: 교체 후 발화한 옛 핸들러가 새 연결을 끊긴 것으로 만들었다.\
같은 구조: 순서가 뒤바뀐 이벤트(예: 소유자 변경 알림)는 단조 `rev`가 현재보다 클 때만 적용.

### 변형 E — 늦은 결과는 버리지만 중복 발행은 계속됨 (in-flight 가드)
```ts
// ① 문제: 토큰만 — 폴링·포커스·수동 새로고침이 겹쳐 서브프로세스 폭주
// ② 고침
function reload() {
  if (loadingRef.current || busyRef.current) return;   // 진행 중·자기 조작 중이면 skip
  loadingRef.current = true;
  const my = ++latestReq.current;
  api.status().then(r => { if (my === latestReq.current) setStatus(r); })
             .finally(() => { loadingRef.current = false; });
}
```
무엇이 깨졌나: 늦은 결과 폐기만으로는 동시 발행 수가 줄지 않았다.

## 검증 기록
- 2026-09-24: 사건 기록 대조·추상화(Claude 초안)

## 방안 비교

본문은 "요청 순번 하나 + 단조 전이"로 충분한 경우다. 전제 축이 여럿이거나 비교 기준 자체가 틀리는 경우의 방안들.

### 방안 1 — 캐시 채우기: 시작 스냅샷 + epoch + 소유 3중 가드
```ts
// ① 문제: 폴링 배치가 읽는 사이 사용자 삭제·축출(close) → 옛 목록으로 덮어 삭제 파일이 되살아남
cache[dir] = await readDir(dir);

// ② 고침
const before = cache[dir], epochAtStart = epoch;
const list = await readDir(dir);
if (epochAtStart !== epoch || !writeAllowed(dir) || cache[dir] !== before) return;
cache[dir] = list;
// close·축출마다 epoch++ (발주 전 요청 차단), writeAllowed = 열린 루트인가 (발주 후 요청 차단)
// + 사이클 세대, dir별 in-flight 1건, 종료 후 1회 재실행 비트, 가드 점유 상한
```

### 방안 2 — 다축 CAS: 요청 토큰 + 세션 + 데이터 서명
```ts
function isCurrent(token, latest, uuid, curUuid, sig, curSig) {
  return token === latest && uuid === curUuid && sig === curSig;   // 하나라도 다르면 폐기
}
// 순수 함수로 추출해 세션 전환·요청 겹침·재활성 시나리오를 테스트
```

### 방안 3 — 낙관적 갱신의 기준선 = ack된 값
```ts
// ① 문제: 요청 해소 전에 lastSent = size → 실패한 요청이 그 값을 "보낸 것"으로 영구 봉인
//        (서버 측도 stdout이 비었을 때만 실패로 봐 에러 응답이 성공으로 보고됨)
// ② 고침
const base = inFlight ?? acked;                      // 비교 기준 = 상대가 확인해 준 값
if (!shouldSend(size, base)) return;
const my = ++seq; inFlight = size;                   // 진행 중 값은 중복 전송 억제용일 뿐 — 확정 기준선은 acked
try {
  const reply = await resize(size);                  // 응답이 실제 적용된 크기를 돌려줌
  if (my !== seq) return;                            // 늦은 답 폐기
  acked = reply.size;
} finally {
  if (my === seq) inFlight = null;                   // 실패해도 해제 — 기준선이 acked로 복귀(안 하면 실패값이 다시 봉인됨)
}
```

### 방안 4 — 인과 순서: 부모 이벤트를 자식 발행 주체 기동 전에
```rust
// ① 문제
registry.insert(sess);
spawn_waiter(&sess); spawn_tailer(&sess);          // 빠른 자식이 Exited·Located를 먼저 발행
publish(Event::Spawned(view));                      // 뷰어는 자식 이벤트를 먼저 받고, 늦은 Starting이 상태를 역주행

// ② 고침
registry.insert(sess);
publish(Event::Spawned(view));                      // 레지스트리 락 밖, 발행 가능한 스레드 기동 전
spawn_waiter(&sess); spawn_tailer(&sess);
```

| | 본문(순번+단조) | 방안 1 3중 가드 | 방안 2 다축 CAS | 방안 3 ack 기준선 | 방안 4 인과 순서 |
|---|---|---|---|---|---|
| 막는 것 | 늦은 응답·과거 전이 | 다른 writer·축출 후 부활 | 세션 전환·데이터 버전 교체 | 실패 요청의 기준선 오염 | 자식이 부모를 앞지름 |
| 전제 | 요청 발행자 하나 | 같은 캐시에 쓰는 경로가 여럿 | 전제 축을 식별 가능 | 상대가 적용 결과를 응답 | 발행 순서를 통제 가능 + 이벤트 채널이 발행 순서를 보존(FIFO) |
| 비용 | 토큰 1개 | 가드·세대 상태 여러 개 | 축마다 저장·비교 | 응답 형식 확장 | 기동 순서 제약 |
| 실패 모드 | 축이 더 있으면 새 경로로 stale write | 가드 하나라도 빠지면 부활 | 빠진 축 | 늦은 답 폐기 누락 | 새 발행 주체 추가 시 순서 재검토 |

**결론**: 요청 발행자가 하나고 전제가 "최신 요청인가"뿐이면 본문의 순번 토큰 + 단조 전이로 충분하다.\
같은 상태에 쓰는 경로가 여럿(폴링·사용자 조작·축출)이면 방안 1, 응답의 유효성이 여러 문맥(세션·데이터 버전)에 걸리면 방안 2로 축을 모두 비교한다.\
보낸 값을 기준으로 다음 전송을 판단하는 낙관적 갱신이면 방안 3이 필수이고, 가드로 순서를 교정하기 전에 발행 순서 자체를 바로잡을 수 있으면 방안 4가 가장 싸다.
