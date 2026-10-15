# issue/concurrency/capture-context-at-request-time — 정답

태그: `race-condition`

## 정답
<!-- 질문 1:1 대응 -->

1. **다른 프로젝트의 대상이 지워지거나 조용히 실패한다.** 패널은 자기 프로젝트의 세션을 보여 주지만, 요청은 "현재 활성 프로젝트"로 가서 그 프로젝트 기준으로 대상을 찾는다.\
   같은 id가 있으면 엉뚱한 것이 삭제되고, 없으면 아무 일도 없이 실패한다.\
   스레드가 하나여도 "요청 생성 시점"과 "처리 시점" 사이에 전역 상태가 바뀔 수 있고(혹은 처음부터 다른 문맥의 객체일 수 있고), 이것이 순서 의존 경합이다.\
   해결은 요청에 `project`를 실어 패널 자신의 문맥을 쓰는 것이다.
   > **앰비언트(ambient) 문맥** — 인자로 받지 않고 주변 전역 상태에서 암묵적으로 읽는 문맥. 읽는 시점에 따라 값이 다르다.

2. **다른 프로젝트에 적용된다.** await는 제어를 양보하므로 그 사이 사용자 입력이 처리될 수 있고, await 뒤에 읽은 "현재 프로젝트"는 클릭한 프로젝트가 아닐 수 있다.\
   그래서 첫 await **전**에 대상을 캡처하고, 되돌릴 수 없는 전이(모드 전환·다른 세션으로 요청 전송) 직전에 "캡처값 == 현재값 && 올바른 창"을 다시 확인한다.\
   불일치면 작업(저장)만 끝내고 전이는 하지 않은 채 안내한다.\
   가드가 "현재값 == 현재값" 같은 동어반복이면 아무것도 막지 못한다 — 비교 한쪽은 반드시 캡처값이어야 한다.
   > **TOCTOU(time-of-check to time-of-use)** — 확인한 시점과 사용하는 시점 사이에 상태가 바뀌어 확인이 무효가 되는 경합.

3. **복원 데이터가 새 사건으로 승격된다.** 디바운스 배치나 홀드 타이머가 실행될 때 공유 변수의 "최신 origin"을 읽으면, 대기 중 도착한 live 이벤트 하나가 배치 전체를 live로 바꾼다.\
   그 결과 재시작·재열람 때 이미 알던 상태(snapshot)가 "새로 발생"으로 알림을 울렸다(3라운드에 걸쳐 지연 지점마다 재발).\
   origin을 파생 시점부터 배치(전부 snapshot일 때만 snapshot)·타이머까지 값으로 운반하고, snapshot은 알림 없이 기준선으로만 시드한다.

4. **전이는 계속 생긴다.** 목적지가 "지금 활성인 대상"이면, 발행~소비 사이의 모든 상태 전이(대상 닫힘과 재인덱스, 가시성, 오버레이 계층, 마운트 수명)가 각각 경합 창이다.\
   전이마다 정규화나 catch-all 소비 규칙을 붙이면, 아직 고려하지 않은 전이(예: "보이지 않지만 마운트는 유지")가 다음 라운드의 구멍이 된다.\
   먼저 목적지 라우팅 자체를 걷어내 원래 동작(diff 0)으로 되돌린 뒤, 각 발행자가 자기를 감싼 컨텍스트의 정체성(컴포넌트 트리상 위치로 정해져 마운트 동안 바뀌지 않는 값)을 스탬프하고 소비자는 `target === mine`만 받게 바꿨다 — 보정 로직이 필요 없어졌다.
   > **렉시컬(구조적) 바인딩** — 값이 실행 시점의 전역 상태가 아니라 코드·트리 구조(어디에 선언·배치됐나)로 정해지는 것. 엄밀한 의미의 렉시컬 스코프(컴파일 시 고정)와 달리 React Provider 값은 트리 위치로 런타임에 정해지지만, 한 발행자에게는 마운트 동안 고정이라 발행~소비 사이에 바뀌지 않는다.

5. **경계에서 오귀속된다.** 다중 소스 `select`는 동시에 준비된 이벤트의 처리 순서가 보장되지 않는다(예: tokio `select!`는 `biased` 없이 쓰면 준비된 분기를 무작위로 고른다). 채널이 다르면 채널 간 도착 순서도 보장되지 않는다.\
   완료(done)가 먼저 처리돼 "현재 turn"이 다음 turn으로 넘어간 뒤 직전 turn의 업데이트가 처리되면, 그 업데이트가 다음 turn에 붙는다.\
   귀속 키(`turn`, `session_id`)는 이벤트 자체에 실려야 하고, 한 번 정한 귀속은 첫 관측 시 고정한다.

6. **속성 기반 근사 상관.** 두 메시지 흐름을 이을 공통 식별자가 없으면, 경로 같은 속성으로 "그 경로를 참조하는 가장 최근 항목"에 귀속하는 수밖에 없다.\
   한계: 같은 경로를 참조하는 항목이 여럿이면 최신에만 붙고, 매칭 항목이 없으면 어디에도 귀속되지 않는다 — 모호성이 구조적으로 남는다.

7. **세 방안이 고정하는 것.** (a) 이름(`HEAD`, 브랜치, 짧은 해시)이 아니라 한 번 해석한 **불변 식별자 스냅샷**을 고정하고, 최종 반영은 그 스냅샷에 대한 compare-and-swap으로 한다.\
   (b) 메서드 간에 인스턴스 속성으로 넘기던 **요청 문맥**을 인자로 고정해, "속성을 먼저 설정해야 한다"는 암묵적 호출 순서 계약을 없앤다.\
   (c) 다른 스레드로 넘기는 **데이터**를 제출 시점 복사본으로 고정해 이후 원본 재사용(clear)이 작업에 새지 않게 하고, 생산 속도는 in-flight 상한으로 묶는다.\
   자세한 비교는 아래 「방안 비교」.

## 문제 구조 (추상화 코드)

### 변형 A — 실행 대상을 전역 "현재"에서 유추
```ts
// ① 문제
requestClose({ id });
// ... 처리부
const project = store.getState().activeProject;   // 요청 시점의 프로젝트가 아님
deleteSession(project, req.id);

// ② 고침
requestClose({ id, project: panel.params.project });   // 요청이 문맥을 들고 감
deleteSession(req.project, req.id);
```
무엇이 깨졌나: 다른 문맥에서 만든 요청이 처리 시점의 활성 문맥에 적용됐다.\
같은 구조: 실행 요청의 `project`가 패널 생성 시 버려지고 터미널이 전역 활성 프로젝트를 cwd로 재조회 → `params.cwd`로 운반, `params.cwd ?? active`는 폴백만.

### 변형 B — await를 사이에 둔 확인·사용
```ts
// ① 문제
async function onConfirm() {
  await writeFile(path, text);
  enableMode(store.getState().activeProject);          // await 동안 전환됐으면 다른 곳에 적용
}

// ② 고침
async function onConfirm() {
  const project = store.getState().activeProject;      // 첫 await 전에 캡처
  await writeFile(path, text);
  const ok = windowLabel() === "main" && project === store.getState().activeProject;
  if (!ok) { notify("저장만 했습니다"); return; }       // 전이는 재검증 통과 시에만
  enableMode(project);
}
```
무엇이 깨졌나: 확인과 사용 사이의 await가 대상을 바꿨고, 첫 가드는 비교 대상이 둘 다 현재값이라 무력했다.

### 변형 C — 지연 지점이 트리거 시점 메타데이터를 잃음
```ts
// ① 문제
let prevOrigin: "snapshot" | "live";
function onItems(items, origin) { prevOrigin = origin; debounceScan(items); }
function scan(batch) { if (prevOrigin === "live") notifyNew(batch); }   // 대기 중 온 live가 오염

// ② 고침
function onItems(items, origin) { debounceScan(items.map(i => ({ ...i, origin }))); }
function scan(batch) {
  const origin = batch.every(i => i.origin === "snapshot") ? "snapshot" : "live";
  if (origin === "snapshot") seedBaseline(batch); else notifyNew(batch);
}
```
무엇이 깨졌나: 실행 시점의 공유 변수가 트리거 시점 출처를 덮어, 복원 데이터가 새 사건으로 알림됐다.

### 변형 D — 목적지를 동적 "활성 대상"으로 결정
```tsx
// ① 문제
requestOpen: (req) => set({ openReq: { ...req, target: activeSurfaceId() } });   // 발행 시점 동적 값
// + 전이마다 reconcileActive(), 소비자 catch-all: target === mine || (mine === "primary" && !visible(target))

// ② 고침
const surfaceId = useSurfaceId();                       // 감싼 Provider가 정한 렉시컬 값
requestOpen(req, surfaceId);                            // 발행자 자신의 정체성을 스탬프
// 소비자
if (req.target !== mySurfaceId) return;                 // reconcile·catch-all 없음
```
무엇이 깨졌나: 닫힘 재인덱스·가시성·오버레이·"보이지 않지만 마운트됨" 전이마다 요청이 없는 소비자로 가거나 이중 소비되어 무음 유실됐다.\
같은 구조: 같은 흐름이 여러 기록에 걸쳐 5라운드 반복됐고, 목적지 라우팅을 먼저 제거(원래 파일 diff 0 복원)한 뒤 렉시컬 스탬프로 재도입했다.

### 변형 E — 귀속·상관 키가 이벤트에 없음
```rust
// ① 문제
match event { Update(u) => attach(u, self.current_turn), Done => self.current_turn += 1 }
// select 처리 순서에 따라 직전 turn의 Update가 다음 turn에 붙음

// ② 고침
match event { Update { turn, session_id, .. } => attach_to(turn, session_id, u) }
// 표시 항목은 첫 관측 시 turn 고정: turn_of.entry(seq).or_insert(turn)
```
무엇이 깨졌나: 가변 "현재 turn"이 이벤트의 소속을 대신해 경계에서 오귀속됐다(프롬프트 직렬화로 실무상 완화, 관측 시 seq 고정 예정으로 기록).\
같은 구조: 쓰기 요청에 상관 id가 없어 `items.rev().find(|it| it.refers(path))`로 가장 최근 항목에 귀속 — 동일 경로 다중 항목·무매칭 시 귀속 불가라는 한계가 남는다.

## 검증 기록
- 2026-09-24: 사건 기록 대조·추상화(Claude 초안)

## 방안 비교

같은 원리("실행 시점에 다시 읽지 말고 요청 시점 값을 고정")를 무엇을 고정하느냐에 따라 다르게 푼 세 방안.

### 방안 1 — 요청에 문맥 값을 실어 운반 (본문 변형 A~E)
```ts
const req = { op, project, origin, target: mySurfaceId };   // 발행 시점 캡처
handle(req);                                                // 실행부는 req만 본다
```

### 방안 2 — 이름을 불변 식별자로 1회 해석 + CAS 반영
```rust
// ① 문제: 검사·자손 목록·반영이 매번 "HEAD"를 다시 해석 → 검증한 집합 ≠ 실행한 집합
// ② 고침
let orig_head = resolve(repo, "HEAD")?;                    // 단일 스냅샷 (전체 해시)
let target = resolve(repo, user_ref)?;                     // 검증된 해시로 실행
check_is_ancestor(&target, &orig_head)?;
let new_head = rewrite(&target, &orig_head)?;              // 모든 그래프 연산은 target..orig_head
update_ref(branch, &new_head, /* expected */ &orig_head)?; // 3인자 CAS: 그사이 움직였으면 실패
```
무엇이 깨졌나: 외부에서 ref가 움직이면 검증한 대상·재작성한 대상·반영한 ref가 서로 달랐다.

### 방안 3 — 인스턴스 속성 대신 인자로 문맥 전달
```python
# ① 문제
class Builder:
    def build(self, req):
        q = self._name_query(req.name)   # 내부에서 self._current 를 읽음 — 아직 설정 전
        self._add_conditions(req)        # 여기서 self._current = req
# ② 고침 (이 사례는 설정 직후로 호출을 옮겨 순서를 맞춤 — 인자 전달이 계약을 없애는 일반형)
    def _add_conditions(self, req):
        self._current = req
        q = self._name_query(req.name)
```
무엇이 깨졌나: 한 하위 클래스만 호출 순서를 바꿔 "설정 전 읽기"가 났다 — 속성 전달은 호출 순서를 암묵적 계약으로 만든다.

### 방안 4 — 비동기 제출 시점 복사본 + in-flight 상한
```java
// ① 문제
batch.add(doc); if (batch.size() == N) { pool.submit(() -> bulk(batch)); batch.clear(); }  // 워커가 비워진/섞인 리스트를 봄
// ② 고침
Semaphore permits = new Semaphore(workers * 2);
List<Doc> snapshot = new ArrayList<>(batch);  batch.clear();
permits.acquire();                             // in-flight 상한 — 생산자 블록
try {
    pool.submit(() -> { try { bulk(snapshot); } finally { permits.release(); } });
} catch (RejectedExecutionException e) { permits.release(); throw e; }   // 제출 실패 시 허가 반납
```
무엇이 깨졌나: 가변 컬렉션 참조를 넘겨 소유권이 공유됐고, 생산자가 소비자를 앞지르면 메모리가 무한히 쌓인다(이 사례는 사고 기록이 아니라 설계 규칙으로 기록됨).

| | 방안 1 문맥 운반 | 방안 2 불변 해석+CAS | 방안 3 인자 전달 | 방안 4 복사본+상한 |
|---|---|---|---|---|
| 고정 대상 | 대상·출처·귀속 | 이름이 가리키는 객체 | 호출 간 문맥 | 넘기는 데이터 |
| 전제 | 요청 생성 지점이 문맥을 안다 | 불변 식별자(해시)와 CAS 연산이 존재 | 호출 경로를 바꿀 수 있다 | 데이터 복사 비용 감당 가능 |
| 비용 | 메시지 필드 증가 | 반영 실패 시 재시도 처리 | 시그니처 변경 | 복사 메모리 + 생산자 대기 |
| 남는 실패 모드 | 캡처 누락 경로, 되돌릴 수 없는 전이는 재검증 필요 | 외부 변경 시 작업 전체 실패(정상) | 호출 순서 계약에 의한 실패는 제거(인자로 넘긴 값 자체가 틀리는 경우는 별개) | 상한이 너무 크면 메모리, 작으면 처리량 |
| 맞는 조건 | UI 이벤트·메시지 버스·지연 실행 | 외부가 같은 자원을 바꿀 수 있는 저장소 조작 | 같은 객체의 메서드 간 문맥 | 스레드 간 배치 전달 |

**결론**: 네 방안은 경쟁 관계가 아니라 "무엇이 바뀔 수 있나"에 따라 고른다.\
대상 선택이 전역 상태에 기대면 방안 1, 대상 자체가 외부에서 바뀔 수 있는 이름이면 방안 2(검증과 반영 사이를 CAS로 닫음), 한 객체 안에서 순서 계약이 생기면 방안 3, 데이터가 스레드 경계를 넘으면 방안 4다.\
여러 조건이 겹치면 함께 쓴다(예: 방안 1로 대상을 운반하고, 되돌릴 수 없는 전이 직전에만 현재값과 재검증).

## 방안 비교 — "지금"을 두 번 읽는다: 판정 시각과 뒤 단계의 기준 시각

같은 원리("실행 시점의 전역 '현재'를 다시 읽지 말고 판정 시점 값을 고정해 운반")가 **시각**이라는 앰비언트 문맥에서 나타난 사례.\
쓰기 요청 하나가 한 트랜잭션 안에서 ① 앱이 그룹 시작 시각과 "지금"을 비교해 마감 여부를 판정하고 ② 뒤 단계(DB 트리거)가 같은 기준으로 "열린 그룹이면 사용자별 집계를 +1, 마감 그룹이면 건너뜀"을 정했다.\
처음에는 두 단계의 시각 출처가 달랐다 — 판정은 앱 시계, 트리거는 DB `now()`(트랜잭션 시작 시각).\
그래서 앱이 트랜잭션마다 자기 시계 값을 트랜잭션 범위 세션 설정으로 넣고, 트리거는 그 값을(없으면 `now()`를) 쓰게 바꿨다.\
그다음 리뷰에서, 출처는 하나가 됐지만 앱이 시계를 **두 번** 읽는다는 점이 지적됐다 — 판정 때 한 번, 세션 설정을 넣을 때 한 번.\
그 사이에 마감 경계를 넘으면 "판정은 열림(요청 수락) · 트리거는 마감(집계 건너뜀)"이 되고, 같은 사용자의 동시 요청은 한도 판정에서 이 점유를 보지 못해 한도를 넘을 수 있었다(창은 작지만 실제 점유가 생긴다).\
결과의 모양은 [denormalized-counter-drift](../../data/denormalized-counter-drift/)의 "카운터 < 실제 → 한도 초과 허용"과 같지만, 원인은 사본 유지 경로의 누락이 아니라 한 결정 안에서 시각을 두 번 읽은 것이다.

```text
요청 트랜잭션
  판정: now₁ < 시작 → 열림 → 수락          ┐ 사이에 경계를 넘으면
  기준 시각 설정: now₂ ≥ 시작               ┘
  트리거: 기준 시각으로 보니 마감 → 집계 +1 건너뜀
  ⇒ 점유는 생겼는데 집계에 없음 → 동시 요청의 한도 판정이 이를 못 본다
```

### 방안 5 — 출처 단일화: DB도 앱 시각을 받는다 (첫 수정)
```sql
-- 앱: 트랜잭션 안 첫 단계
SELECT set_config('app.decision_now', :app_now, true);          -- true = 트랜잭션 범위(SET LOCAL)
-- 트리거 쪽 기준 시각
CREATE FUNCTION decision_now() RETURNS timestamptz LANGUAGE sql STABLE AS
$$ SELECT coalesce(nullif(current_setting('app.decision_now', true), '')::timestamptz, now()) $$;
-- 앱을 거치지 않는 직접 쓰기는 설정이 없어 now()로 판정한다
```

### 방안 6 — 판정 시각을 한 번 채집해 뒤 단계로 운반 (이 사례에서 적용)
```kotlin
class CloseGate(private val clock: Clock) {
    private val decision = ThreadLocal<Instant>()
    fun decisionInstant(): Instant? = decision.get()
    fun clearDecision() = decision.remove()
    fun assertOpenLocked(groupId: Long) {
        val startsAt = lockGroupForShare(groupId)
        val now = clock.instant()                 // 이 요청의 판정 시각 — 한 번만 읽는다
        decision.set(now)
        if (!now.isBefore(startsAt)) throw Closed()
    }
}
// 뒤 단계: 판정이 쓴 값을 그대로 기준 시각으로
setDecisionNow(gate.decisionInstant() ?: clock.instant())
// 요청 처리 진입점
try { return process(cmd) } finally { gate.clearDecision() }   // 풀 스레드에 다음 요청까지 남지 않게
```
테스트는 "다음 한 번의 읽기는 경계 직전, 그 뒤 읽기는 경계 뒤"를 돌려주는 시계로 두 읽기 사이에 경계를 넣어, 판정이 열림이면 집계도 +1인지 확인했다.

| | 방안 5 출처 단일화 | 방안 6 한 번 채집 + 스레드 국한 운반 | (참고) 인자 전달 — 위 방안 3 |
|---|---|---|---|
| 없애는 것 | 앱 시계와 DB 시계의 차이 | 같은 출처를 두 번 읽는 사이의 경계 통과 | 같음 + 호출 순서 계약 |
| 전제 | DB가 트랜잭션 범위 설정을 지원 | 판정과 뒤 단계가 같은 스레드에서 돈다 | 중간 계층의 시그니처를 바꿀 수 있다 |
| 비용 | 트랜잭션마다 문장 1개 | 진입점의 `finally` 해제 | 전략 인터페이스 등 여러 시그니처 변경 |
| 남는 실패 모드 | 두 번 읽기는 그대로 남는다 | 해제를 빠뜨리면 풀 스레드에 옛 값이 남고, 값이 없을 때의 폴백(`?: clock`)이 채집 누락을 조용히 덮는다, 비동기로 스레드를 넘기면 사라진다 | 넘긴 값 자체가 틀리는 경우는 별개 |

**결론**: 시각처럼 "읽을 때마다 바뀌는" 값은 출처를 하나로 모으는 것(5)만으로는 부족하다 — 한 결정에 쓰인 값은 **한 번 읽어** 그 결정의 모든 단계가 같은 값을 쓰게 해야 한다(6).\
운반 수단은 호출 경로를 바꿀 수 있으면 인자 전달이 계약이 가장 드러나고, 여러 계층을 지나며 바꾸기 어려우면 스레드 국한 운반이 현실적이다 — 단 진입점 `finally` 해제와 폴백이 누락을 숨기지 않는지를 함께 확인한다(폴백 쪽 판단은 일반론).

검증 기록: 2026-10-15 사건 기록·코드(수정 전후)·테스트 대조·추상화(Claude 초안).
