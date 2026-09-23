# cs/issue/cross-cutting/reliability/edge-detection-on-raw-signals — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 사건 기록 원문 대조 작성. 복습 전 읽지 말 것.

태그: —

## 정답
<!-- 질문 1:1 대응 -->

1. **level vs edge.** level은 "지금 어떤 상태인가"이고 edge는 "방금 그 상태로 들어왔다"는 사건이다.\
   알림은 사람에게 "새 일이 생겼다"를 전하는 것이므로 edge에 걸어야 한다 — level에 걸면 상태가 유지되는 동안 계속 울리거나, 반대로 이미 알린 상태로 돌아올 때 다시 울린다.
   > **rising edge** — 신호가 거짓에서 참으로 바뀌는 순간. `next && !prev`로 판정한다.

2. **스칼라가 원인을 지운다.** `max(3, 2)`는 blocked가 풀리는 순간 다시 2가 된다 — 스칼라 관점에서는 "2로 상승"과 구별되지 않아 **done 알림이 재발화**한다.\
   스칼라는 "왜 그 값이 됐나"(새 완료인가, 상위 상태의 해제인가)를 담지 못하므로, 스칼라 위에 어떤 비교를 얹어도 두 경우를 가를 수 없다.\
   교정: 기저 신호마다 rising edge를 따로 계산하고 조합 규칙표로 우선순위를 정한다(blocked↑면 blocked, `unseen↑ && !blocked`일 때만 done). 순수 함수로 만들어 조합 5가지를 테스트로 고정했다.

3. **덮어쓰기가 일회성 사건을 지운다.** 홀드 구간 동안 값은 매 tick 현재값으로 덮이므로, 확정 시점에는 "홀드 중 한 번 봤다"는 사실이 남지 않는다 — 이미 본 완료가 unseen(미확인)으로 표시된다.\
   교정: `seenInWindow` **래치**를 두고 한 번이라도 참이면 확정 때까지 유지한다. 확정 시 `unseen = !(seen || seenInWindow)`. working으로 복귀하면 래치를 리셋한다. 홀드 999/1000ms 경계와 홀드 중 복귀 시 done 미발화를 가짜 타이머로 검증했다.
   > **래치(latch)** — 한 번 참이 되면 명시적으로 리셋할 때까지 참을 유지하는 기억 소자.

4. **샘플링 정리.** 2.5초마다 한 번 보는 관찰자는 두 샘플 사이에서 시작하고 끝난 1초짜리 다운을 **볼 방법이 없다**. 재배포는 성공(1초 안에 재연결)했는데 UI는 "down을 못 봤으니 재시작이 안 됐다"로 판단해 90초 뒤 "완료 확인 실패"를 냈다.\
   폴링 간격을 줄이면 확률만 낮아질 뿐, 펄스가 더 짧아지면 다시 놓친다 — 근본 해법이 아니라 임시방편이다(선택하지 않은 방법).

5. **세대 ID.** 연결마다 새 UUID(`sessionId`)와 pid를 인사 메시지에 싣고, UI는 재배포 **직전의** sessionId를 캡처해 둔다. 이후 판정은 "down을 봤나"가 아니라 "sessionId가 **바뀌었나**"다 — 바뀐 값은 계속 남아 있으므로 폴링이 아무리 늦어도 잡힌다.\
   한계: 재배포가 아닌 순간 재연결도 sessionId를 바꾸므로 오인할 수 있다(pid 동시 비교로 보완 가능). 구버전 에이전트가 sessionId를 안 보내면 첫 사이클은 옛 방식으로 fallback한다.
   > **세대(generation) ID** — 인스턴스가 새로 생길 때마다 바뀌는 식별자. "같은 것인가"를 값 비교로 답하게 한다.

6. **너무 민감한 edge.** 순간값 1개로 경보를 내자, 매일 같은 시각 도는 OS 정기 업데이트 작업의 짧은 CPU 스파이크 한 샘플에 CPU 100% 경보가 나갔다(구간 전체로는 거의 idle).\
   교정: **N회 연속**(3회 ≈ 90초, 폴링 30초) 초과일 때만 발화하고, 폴링 실패·샘플 누락은 연속으로 치지 않고 **카운터를 리셋**한다(빈 샘플을 "여전히 높음"으로 이으면 다시 오경보).\
   반대로 지속 이상에 30분 고정 쿨다운으로 재발송하면 수 일간 수백 통이 쌓여 사람이 경보를 무시하게 된다 — 경보가 다시 무음이 되는 것이다. 재알림은 점증 백오프(30분→2시간→6시간), 해소 시 복구 통지 1통, 배포 중 억제 스위치를 둔다.

7. **무엇을 기억하나.** 신호별 edge = 각 신호의 **이전 값**. 래치 = **구간 안에 한 번이라도** 일어났는가. 세대 ID = **어느 인스턴스를 봤는가**(사건의 영구 흔적). 연속 카운터 = **얼마나 오래** 이상이었는가.\
   공통점: 관찰값을 가공하는 순간(접기·덮어쓰기·샘플링) 잃는 정보를, 가공 전에 별도 상태로 보존한다.

## 문제 구조 (추상화 코드)

### 변형 A — 여러 신호를 우선순위 스칼라로 접은 뒤 상승 판정
① 문제 코드
```ts
const level = (s: State) => s.blocked ? 3 : s.unseen ? 2 : 0;
function edge(prev: State, next: State) {
  if (level(next) > level(prev)) return kindOf(level(next));   // 3→2 뒤 2→3→2 도 "2로 옴"
  // ...
}
```
② 고친 코드
```ts
function edge(prev: State, next: State) {
  const blockedRising = next.blocked && !prev.blocked;
  const unseenRising  = next.unseen && !prev.unseen;
  if (blockedRising) return "blocked";
  if (unseenRising && !next.blocked) return "done";      // 해제는 사건이 아님
  return null;
}
```
무엇이 깨졌나: 스칼라가 "새 완료"와 "상위 상태 해제"를 같은 값으로 만들었다.

### 변형 B — 지연 확정 구간의 일회성 사건을 현재값으로 덮음
① 문제 코드
```ts
onTick(now) {
  this.seen = seenNow();                       // 매 tick 덮어씀
  if (holdExpired(now)) commit({ unseen: !this.seen });
}
```
② 고친 코드
```ts
onTick(now) {
  this.seen = seenNow();
  this.seenInWindow ||= this.seen;           // 래치
  if (holdExpired(now)) commit({ unseen: !(this.seen || this.seenInWindow) });
}
onWorkingResumed() { this.seenInWindow = false; }
```
무엇이 깨졌나: 확정 시점 한 점의 값만 보고 구간 안의 사건을 버렸다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log

## 방안 비교

기본 방안(변형 A·B)은 "가공 전 기저 신호에서 edge를 판정하고, 사라질 사건은 래치로 기억한다"이다. 같은 원리(가공이 사건을 지우거나 만들어냄)에 다른 방안이 쓰인 사례:

### 방안 1 — 주기 샘플링 대신 세대 ID 비교
```js
// 문제: 스냅샷 폴링으로 down → up 전이를 잡으려 함 (펄스 < 폴링 주기면 못 봄)
let sawDown = false;
poll(() => { if (!s.connected) sawDown = true; if (sawDown && s.connected) done(); });

// 고친: 재시작 직전 세대 캡처 → 값이 바뀌었는지만 본다
const before = (await status()).sessionId;
await redeploy();
poll(s => {
  if (s.connected && before && s.sessionId && s.sessionId !== before) return done();
  if (!before) { /* 구버전 fallback: sawDown 방식 */ }
});
```

### 방안 2 — 지속 조건으로 발화 + 재알림 간격 설계
```kotlin
// 문제: 1샘플 초과 = 즉시 경보 / 지속 이상 = 고정 30분 간격 무한 재발송
if (value >= threshold) alert(host, metric, value)

// 고친
val n = consecutive.merge(key, 1, Int::plus) ?: 1
if (n >= props.alertConsecutive) alerter.alertWithBackoff(key, host, metric, value) // 30m→2h→6h
// 샘플 실패·누락 시: consecutive.remove(key)
// 해소 시: 복구 통지 1통, 배포 중: mute 스위치
```

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 기본: 신호별 edge + 래치 | 기저 신호를 직접 볼 수 있다 | 신호별 이전 값·래치 상태 | 조합 규칙표 누락 시 새 조합에서 오판 | 한 프로세스 안의 상태 머신·알림 |
| 1. 세대 ID 비교 | 관찰 대상이 인스턴스마다 새 ID를 낼 수 있다 | 프로토콜에 필드 추가 | 순간 재연결도 세대를 바꿔 오인 가능 | 짧은 재시작을 원격에서 확인 |
| 2. 지속 조건 + 백오프 재알림 | 잡음 스파이크가 실제 이상보다 흔하다 | 감지 지연(N×주기) | 주기보다 짧은 진짜 이상은 못 봄 | 주기 샘플 기반 운영 경보 |

**결론**: 기저 신호에 접근할 수 있으면 가공 전 edge 판정이 가장 정확하다(기본).\
관찰자가 원격이고 샘플링밖에 할 수 없으면, 순간을 잡으려 하지 말고 **영구 흔적(세대 ID)**을 비교한다(1).\
잡음이 많은 수치 경보는 오히려 edge를 둔하게 만들어야 한다 — 지속 조건과 백오프가 경보에 대한 신뢰를 지킨다(2).
