# issue/cross-cutting/reliability/edge-detection-on-raw-signals — 정답

태그: —

## 정답
<!-- 질문 1:1 대응 -->

1. **level vs edge.** level은 "지금 어떤 상태인가"이고 edge는 "방금 그 상태로 들어왔다"는 사건이다.\
   알림은 사람에게 "새 일이 생겼다"를 전하는 것이므로 edge에 걸어야 한다 — level에 걸면 상태가 유지되는 동안 계속 울리거나, 반대로 이미 알린 상태로 돌아올 때 다시 울린다.
   > **rising edge** — 신호가 거짓에서 참으로 바뀌는 순간. `next && !prev`로 판정한다.

2. **스칼라가 원인을 지운다.** `max(3, 2)`는 blocked가 풀리는 순간 다시 2가 된다 — 스칼라 관점에서는 "2(done)로 바뀜"이라 새 완료와 구별되지 않아 **done 알림이 재발화**한다.\
   스칼라 3은 그 아래의 unseen 여부를 숨기므로, 이전·현재 스칼라 값을 어떻게 비교해도 "왜 그 값이 됐나"(blocked 중에 새로 완료됐나, 원래 있던 완료가 상위 상태 해제로 드러났나)를 가를 수 없다.\
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
  const a = level(prev), b = level(next);
  if (b !== a && b > 0) return kindOf(b);   // 2→3→2 의 마지막 3→2 도 "done(2)으로 바뀜" → 재알림
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
onMarkSeen() { this.seen = true; }            // 홀드 중 사용자가 봄
onTick(now) {
  this.seen = seenNow();                       // 다음 tick이 덮어씀 → 본 사실 소실
  if (holdExpired(now)) commit({ unseen: !this.seen });
}
```
② 고친 코드
```ts
onMarkSeen() { this.seen = true; this.seenInWindow = true; }   // 사건 시점에 래치 (tick에서 래치하면 덮인 뒤라 늦다)
onTick(now) {
  this.seen = seenNow();
  if (holdExpired(now)) commit({ unseen: !(this.seen || this.seenInWindow) });
}
onWorkingResumed() { this.seenInWindow = false; }
```
무엇이 깨졌나: 확정 시점 한 점의 값만 보고 구간 안의 사건을 버렸다.

## 검증 기록
- 2026-09-24: 사건 기록 대조·추상화(Claude 초안)

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
| 2. 지속 조건 + 백오프 재알림 | 잡음 스파이크가 실제 이상보다 흔하다 | 감지 지연(N×주기) | N×주기보다 짧게 지속된 진짜 이상은 못 봄 | 주기 샘플 기반 운영 경보 |

**결론**: 기저 신호에 접근할 수 있으면 가공 전 edge 판정이 가장 정확하다(기본).\
관찰자가 원격이고 샘플링밖에 할 수 없으면, 순간을 잡으려 하지 말고 **영구 흔적(세대 ID)**을 비교한다(1).\
잡음이 많은 수치 경보는 오히려 edge를 둔하게 만들어야 한다 — 지속 조건과 백오프가 경보에 대한 신뢰를 지킨다(2).

## 방안 비교 — 끝 상태 판정기는 만료가 지운 일시 위반을 놓친다

같은 원리("관찰값을 가공하는 순간 사건이 사라진다" — 여기서는 **덮어쓰기**와 **한 번의 샘플**)가 동시성 부하 시험의 **정합성 판정**에서 나타난 사례.\
판정기는 부하가 끝난 뒤 DB 최종 상태에서 불변식(좌석마다 유효한 점유는 최대 1개 등)을 검사했다 — 실행 전체에서 **끝에 한 번 찍은 스냅샷**이다.\
점유에는 만료(TTL)가 있고, 만료 배치가 지난 점유를 지운다. 같은 좌석에 점유가 둘 생긴 뒤 하나가 확정되면 다른 하나는 판정 전에 만료로 사라졌다 — 위반은 실제로 있었지만 끝 상태에는 남지 않는다.

```text
t0  점유 A(좌석 s) ─┐
t1  점유 B(좌석 s) ─┤  ← 일시 중복 (사건)
t2  A 확정          │
t3  B 만료·삭제 ────┘
t_end  판정기: 좌석 s 점유 ≤ 1  → 위반 0   (사건이 덮어써진 뒤의 상태만 봄)
```

### 방안 1 — 끝 상태 불변식 검사 (기존)
```sql
SELECT count(*) FROM (SELECT item_id FROM holds GROUP BY item_id HAVING count(*) > 1) d;   -- 끝에 한 번
```

### 방안 2 — 사건 기록(요청 로그)으로 판정 (이 사례에서 추가)
```python
# 성공 응답마다 (좌석, 점유 시각, 만료 시각)을 기록해 두고, 같은 좌석에서 유효 구간이 겹친 점유를 센다
wins = [(r.item, r.held_at, r.expires_at) for r in responses if r.status == 201]
dup = 0
for item, holds in group_by(wins, key=item).items():
    live = sorted(holds, key=held_at)
    dup += count_overlaps(live)          # 앞 점유가 아직 유효한 동안 생긴 점유 = 초과 점유 1건
report(end_state_violations=..., transient_duplicates=dup)   # 둘을 나란히, 다른 이름으로
```

관측(같은 하네스): TTL 300초 시나리오에서 요청 기록 기반 일시 중복은 회차당 0~3건, 끝 상태 판정기는 0건.\
TTL 60분·실행 약 3분이라 **만료가 없는** 시나리오에서는 두 값이 모든 셀에서 같았다 — 덮어쓰기(만료)가 없으면 끝 상태가 사건을 그대로 담는다. 처음엔 이 시나리오에서도 판정기가 놓친다고 읽었는데, 그것은 단위가 다른 두 지표를 비교한 오류였다(→ [aggregation-semantics](../../data/aggregation-semantics/) 방안 비교).

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 1. 끝 상태 검사 | 위반이 끝까지 남는다(덮어쓰기·만료·정리가 없다) | 쿼리 한 번 | 만료·정리·보상이 위반을 지우면 원리적으로 0 — 오류 없이 "정합"으로 보인다 | 만료 없는 시나리오, 최종 결과 자체가 계약일 때 |
| 2. 사건 기록 판정 | 성공 응답을 요청 단위로 남긴다, 응답에 판정에 필요한 값(좌석·만료 시각)이 있다 | 요청 단위 기록·후처리 | 응답을 못 받은 성공(클라이언트 포기 후 처리)은 기록에 없다 — 저장소 대조가 따로 필요하다 | 만료·정리가 끼는 시나리오, 일시 위반 자체가 결함일 때 |

**결론**: 끝 상태 판정은 "끝에 남은 것"만 증명한다 — 시스템이 위반을 **스스로 지우는** 경로(만료·정리)가 있으면, 사건을 지워지기 전에 기록하는 판정(2)을 함께 둔다.\
둘은 대체 관계가 아니다 — 끝 상태는 저장소의 최종 계약을, 사건 기록은 과정의 위반을 본다. 만료가 없는 조건에서 두 값이 일치하는지 확인하면 사건 기록 판정기 자체의 검증도 된다.\
응답을 받지 못한 처리까지 보려면 응답 ↔ 저장소 대조가 필요하다(→ [abandoned-request-late-processing](../abandoned-request-late-processing/)).\
검증 기록: 2026-10-06 사건 기록 대조·추상화(Claude 초안).
