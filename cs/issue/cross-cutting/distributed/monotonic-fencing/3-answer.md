# cs/issue/distributed/monotonic-fencing — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 사건 기록 대조·추상화. 복습 전 읽지 말 것.

태그: `race-condition`

## 정답
<!-- 질문 1:1 대응 -->

1. **v1 INSERT는 성공하고, 토글은 무시된다.**\
   `UNIQUE(target, version)`은 같은 `(target, version)` 쌍이 두 번 들어오는 것만 막는다.\
   v2가 있는 상태에서 v1은 중복이 아니므로 삽입된다.\
   그런데 "현재 = 최댓값 행"으로 읽으므로 현재는 계속 v2다 — 방금 성공한 변경이 반영되지 않는다.\
   유일성은 집합의 성질이고 단조성은 순서의 성질이라, 앞의 것은 뒤의 것을 보장하지 않는다.
   > **high-water mark(최고수위)** — 지금까지 수락된 값 중 가장 큰 값. 이보다 작은 값은 "과거"로 취급한다.

2. **UNIQUE 제약이 한쪽을 거부한다 — 두 계층 강제.**\
   저장소가 `INSERT ... SELECT COALESCE(MAX(version),0)+1`을 한 문장으로 계산하면 호출자는 번호를 고를 수 없다.\
   두 호출이 동시에 같은 `MAX+1`을 계산하면, 뒤따른 쪽이 `UNIQUE(target, version)`에 걸려 실패한다(엔진·격리 수준에 따라 선행 트랜잭션 커밋까지 대기 후 중복 키 오류, 또는 교착 감지로 한쪽 롤백).\
   실패한 쪽은 호출자가 재시도해야 한다 — 제약은 "틀린 번호의 커밋"을 막을 뿐 요청을 대신 성공시켜 주지 않는다.\
   즉 "번호 계산은 저장소", "동시 충돌은 제약"이 나눠 막는다.\
   (검증과 토글 사이의 TOCTOU는 이것만으로는 닫히지 않아 락·단일 트랜잭션 과제로 남았다.)

3. **stale 요청이 수락된다.**\
   스냅샷 복구가 `lastAcceptedToken`까지 이전 값으로 되돌리면 최고수위가 후퇴한다.\
   그 사이 이미 거절됐어야 할 낮은 token이 "아직 수위보다 크다"로 판정돼 다시 수락된다 — fencing이 무력화된다.\
   교정: 롤백은 slot(라우팅 상태)만 되돌리고 token은 `max(before, current)`를 유지한다.

4. **명령 측 검증은 "확인 → 실행" 사이 창을 남긴다.**\
   실행자가 락을 재확인한 뒤 실제 write까지 사이에 lease를 잃을 수 있고, 그 write가 최종 상태로 남는다.\
   자원(sink)이 요청에 실린 token을 자기 최고수위와 비교해 작으면 거절하면, 실행자가 무엇을 믿든 늦은 write는 버려진다 — 단 sink 안에서 "비교 → 쓰기"가 원자적(락·단일 트랜잭션)이어야 한다.\
   실행자가 설정 파일을 직접 쓰는 구조는 쓰는 주체가 곧 실행자라 **거부할 지점(sink)이 없다** — 그래서 그 안은 선택하지 않은 방법이 됐다.
   > **fencing token** — 락을 얻을 때마다 증가하는 번호. 자원은 본 적 있는 가장 큰 번호보다 작은 번호의 요청을 거절한다.

5. **같은 입력이면 같은 서명이 나오기 때문이다.**\
   응답 canonical이 `requestId + digest`만 결박하면, 락을 잃기 전에 받은 "HELD" 응답을 나중에 그대로 재사용해도 서명이 맞는다.\
   요청마다 CSPRNG로 새 `confirmId`를 만들어 요청과 응답 양쪽에 결박하면, 과거 응답은 새 confirmId와 불일치해 무효가 된다.
   > **replay(재생) 공격** — 과거에 유효했던 메시지를 그대로 다시 보내 현재의 권한처럼 쓰는 것.

6. **권리 없이 파괴적 부작용이 난다.**\
   `Up`이 첫 확인 실패로 오류를 내면 실패 정리 경로가 `Down`을 호출하고, 그 `Down`의 확인이 우연히 성공하면 — 실행되지 않은 `Up` 뒤에 기존 자원이 내려간다.\
   "sticky" = 확인이 한 번 실패한 순간 그 dispatch 세션을 영구 `denied`로 고정해, 이후의 모든 Up/Down이 RPC도 mutation도 없이 같은 오류를 내게 하는 것이다.\
   실패가 풀리는 경로가 하나라도 있으면 정리 코드가 그 구멍이 된다.

7. **두 시계의 편차가 곧 권리 오판이 된다.**\
   holder·token·만료시각을 DB에서 읽어 와 앱 프로세스 시계로 비교하면, DB와 앱의 시계 차이만큼 만료된 lease가 유효로 판정된다.\
   `SELECT EXISTS(... token=? AND lease_expires_at >= NOW(6))`처럼 DB 시각으로 한 문장에서 판정하면 시계가 하나다.\
   1~3번과 같은 뿌리: 권리 판정의 기준(번호·수위·시계)은 **한 곳에서, 뒤로 가지 않게** 정해야 한다.\
   다만 이 확인은 "완화이지 봉쇄가 아니다" — 판정 직후 lease를 잃거나 이미 시작된 명령은 막지 못하고, fencing을 이해하지 못하는 자원(sink)은 여전히 거부 지점이 없다.

## 문제 구조 (추상화 코드)

### 변형 A — 번호 결정권이 호출자에게 있음
① 문제 코드
```sql
-- 호출자가 version을 넘긴다
INSERT INTO mode_history(target, mode, version, actor)
VALUES (:target, :mode, :version, :actor);   -- UNIQUE(target, version)
-- 읽기: 현재 = MAX(version) 행
```
② 고친 코드
```sql
INSERT INTO mode_history(target, mode, version, actor)
SELECT :target, :mode, COALESCE(MAX(version), 0) + 1, :actor
FROM mode_history WHERE target = :target;    -- 동시 충돌은 UNIQUE가 거부 → 호출자 재시도
```
깨진 것: 유일성 제약만 믿고 단조성을 호출자에게 맡겨, 낮은 version의 성공 쓰기가 "현재"가 되지 못했다.

### 변형 B — 롤백이 최고수위를 되돌림 + 명령 측 검증
① 문제 코드
```kotlin
fun switch(req: SwitchRequest) {
    val before = state.snapshot()          // {slot, lastAcceptedToken}
    try { apply(req) }
    catch (e: Exception) { state.restore(before) }   // token까지 후퇴
}
```
② 고친 코드
```kotlin
fun switch(req: SwitchRequest): Result = synchronized(writeLock) {
    if (req.token < state.lastAcceptedToken) return Stale(req.token)  // sink 측 검증
    if (req.token == state.lastAcceptedToken && req.slot == state.slot) return Ok  // 멱등
    val before = state.snapshot()
    try { apply(req) }
    catch (e: Exception) {
        state.slot = before.slot                                      // 슬롯만 복원
        state.lastAcceptedToken = maxOf(before.lastAcceptedToken, state.lastAcceptedToken)
    }
    // ...
}
```
깨진 것: 상태 복원이 fencing 수위까지 되돌려 stale token이 재수락됐다. 조회 경로도 같은 락으로 직렬화해 전환 중 잠정 상태를 노출하지 않게 했다.

### 변형 C — 권리 확인 절차의 구멍(replay · 끈적하지 않은 실패 · 두 시계)
① 문제 코드
```go
resp := confirm(requestID, digest)            // 응답 서명이 입력에만 결정됨 → 재생 가능
if err != nil { cleanupAfterFailure() }       // cleanup이 다시 confirm → 성공하면 Down 실행
lease := store.Read()
if time.Now().Before(lease.ExpiresAt) { ... } // 앱 시계로 만료 비교
```
② 고친 코드
```go
confirmID := randomBytes(16)                  // 요청마다 새 nonce, 요청·응답 양쪽에 결박
resp := confirm(requestID, digest, confirmID)
if !verify(resp, confirmID) { session.Deny() } // 실패는 세션에 영구 고정(sticky)
if session.Denied() { return ErrFenced }      // 이후 Up/Down 전부 차단

// 만료 판정은 DB 시각으로 한 문장
// SELECT EXISTS(SELECT 1 FROM lock
//   WHERE holder_id=? AND fencing_token=? AND lease_expires_at >= NOW(6))
```
깨진 것: 확인 응답이 재생 가능했고, 실패 후 정리 경로가 권리 없이 부작용을 낼 수 있었고, 만료 판정이 두 시계를 섞었다.

## 검증 기록
- 2026-09-24: 사건 기록 대조·추상화(Claude 초안)
