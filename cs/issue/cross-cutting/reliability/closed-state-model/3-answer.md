# cs/issue/reliability/closed-state-model — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 이슈 원문 기준. 복습 전 읽지 말 것.

태그: —

## 정답
<!-- 질문 1:1 대응 -->

1. **optional 쌍 vs 판별 유니온.** optional 두 개는 네 조합(둘 다 없음·path만·files만·둘 다 있음)을 허용하는데 도메인은 둘 중 정확히 하나만 원한다 — 나머지 두 조합이 불법 상태로 컴파일을 통과한다.\
판별 유니온 `{ kind: "path"; path } | { kind: "memory"; files }`는 합법 조합만 표현 가능하게 만들고, 소비 쪽에 `never` 완전성 검사(모든 kind를 처리했는지 컴파일러가 확인)를 두면 분기 누락도 컴파일 에러가 된다.\
`kind: string`이면 리터럴 유니온이 사라져 kind 이름을 바꿔도 컴파일러가 모른다 — "삭제" 분기가 조용히 기본 분기("닫기")로 떨어진다.
   > **판별 유니온(discriminated union)** — 공통 태그 필드 값으로 변형을 구분하는 합 타입. 태그를 보면 나머지 필드의 존재가 확정된다.

2. **optional 필드가 버전 계약을 깬다.** `Option + default`면 그 필드가 없는 v1 payload도 v2 타입으로 **역직렬화에 성공**한다 — 필드는 None으로 채워지고 오류는 없다.\
"모든 v2 이벤트는 key를 가진다"·"v1은 거부한다"는 계약이 타입 수준에서 이미 거짓이 된다.\
교정: 버전 경계를 긋는 필드는 **필수 타입**으로 두어 파싱 단계에서 거부되게 하고, "v1 라인이 v2로 파싱되면 실패"하는 테스트를 둔다(정말 없을 수 있는 필드만 optional로 남긴다).

3. **불리언이 pending과 dead를 합친다.** 지연 기동 객체는 pending(등록만, 프로세스 없음)·running·dead 세 상태인데, `alive = proc.poll() is None`류 판정은 **프로세스가 없는 pending도 False**다.\
"alive가 아니면 재생성"이면 pending 객체에 온 두 번째 요청이 새 객체를 만들어 같은 키에 둘이 생긴다 — 연결은 한쪽, 레지스트리는 다른 쪽을 가리키는 split-brain.\
교정: 재사용 조건을 `proc is None or alive`(pending·running 재사용, dead만 재생성)로, 접속 거절 조건은 `proc is not None and not alive`로 **세 상태를 명시적으로** 가른다.
   > **split-brain** — 하나여야 할 실체가 둘로 갈라져 각자 다른 쪽을 진실로 여기는 상태.

4. **곱집합 누락과 pid 재사용.** 독립 조건 둘(프로세스 생존 × 기록 존재)은 네 조합을 만든다. 결과 enum이 셋만 덮으면 네 번째 조합은 **인접한 값으로 오표기**된다("프로세스도 기록도 없음"이 "복구 중"으로 보고됨).\
id 충돌 같은 예외 결과도 레코드를 만들지 않으면 뷰어에서 사라진다 → 모든 결과에 **이름과 레코드**를 준다.\
pid는 재사용되므로 pid 하나로 "살아 있음"을 판정하면 **다른 프로세스**를 자기 것으로 오인한다 → 신원은 `(pid, start_time)`으로 확인한다.\
반대로 확인 없이 "죽었다"고 단언하고 pid를 지우면 살아 있는 프로세스를 멈출 수단까지 잃는다.

5. **종단 재전이.** 축출 경로와 remove 경로가 **순차로** 같은 노드를 처리할 때, 매번 `current`를 새로 읽고 `REMOVED` 엔트리로 CAS하므로 두 번째 CAS도 성공한다(REMOVED→REMOVED가 금지돼 있지 않다).\
성공할 때마다 크기 카운터를 1 감산하므로 **노드 하나에 두 번 감산** → 카운터가 실제보다 작아져 용량이 조용히 초과되고(capacity 2에 size 3 고착), 드리프트는 경합마다 누적된다.\
교정: 루프 진입 시 `if (current.state == REMOVED) return;` — 종단 상태에서의 전이를 거부해 감산을 노드당 정확히 1회로.\
원형 구현은 죽은 엔트리의 가중치를 0으로 두어 방어했는데, 단순화 이식에서 그 불변식이 사라진 것이 원인이었다.
   > **CAS(compare-and-swap)** — 현재 값이 기대값과 같을 때만 새 값으로 바꾸는 원자 연산.

6. **검사 없는 set.** 전이 헬퍼가 현재 상태·소유자를 확인하지 않으면, 취소 요청이 `cancelling`으로 바꾼 직후 실행 중 코루틴이 `awaiting`으로 덮어써 **취소와 승인 둘 다 효력**을 갖는 상태가 된다. 승인 연타는 배포를 두 번 만든다.\
협조적 취소는 실행 중 작업이 **매 단계 경계에서 "내가 아직 이 작업의 소유자인가, 선행 상태가 맞는가"를 검사**해야만 동작한다 — 검사가 없으면 취소는 플래그일 뿐 작업은 계속된다(고아 리소스·거짓 "준비 완료").\
교정: 락 안에서 check-and-set(소유 객체 identity + 선행 상태 검증), 위반 시 취소 예외로 중단 + 정리. 승인·취소는 각각 원자 **선점**으로 한 번만 효력. 모든 진입점(REST·WS)이 같은 전이 함수를 쓴다.
   > **협조적 취소** — 강제로 죽이지 않고, 실행 중 코드가 스스로 취소 여부를 확인해 멈추는 방식.

7. **비단조 guard와 겹친 확인창.** 전이 조건이 `쿨다운 만료 AND 메트릭 정상`이면 메트릭이 계속 나쁠 때 **다음 상태에 영원히 도달하지 못한다** — "언젠가는 진행한다"는 liveness가 깨진다(남은 시간이 음수로 찍히는 로그만 반복).\
게다가 메트릭 악화(고부하)가 바로 재시작이 해소해야 할 증상이면, 복구가 필요할수록 복구가 막히는 **역설적 교착**이다.\
교정: 전이는 **시간(단조 입력)만으로** 하고, 메트릭은 새 상태 안에서 "이번 차례 행동을 보류"하는 행동 레이어에만 적용한다(시도 횟수도 올리지 않음).\
확인창도 같은 원리다: 불리언 확인 하나에 "진행할까?"와 "강제로?"를 겹치면 **취소(false)가 "강제 아님"으로 해석돼 진행**된다 — 질문을 분리해 취소는 항상 중단이 되게 하고, 되돌릴 수 없는 덮어쓰기(stash pop·충돌 해결 한쪽 채택)에는 명시 확인을 둔다.
   > **liveness** — "좋은 일이 결국 일어난다"는 성질. 교착·고착은 liveness 위반이다.

## 문제 구조 (추상화 코드)

### 변형 A — 타입이 도메인보다 넓다
① 문제 코드
```ts
type Source = { path?: string; files?: File[] }          // 둘 다 없음/둘 다 있음 표현 가능
type CloseRequest = { kind: string }                      // 리네임 시 "delete"가 기본 분기로
```
```rust
fn contained(root: &str, path: &str) -> bool              // 인자 뒤집어도 컴파일 (root="/"면 봉쇄 무력)
fn delete_path(root: Option<String>, path: String)        // None → 봉쇄 없는 옛 경로
```
② 고친 코드
```ts
type Source = { kind: "path"; path: string } | { kind: "memory"; files: File[] }
type CloseRequest = { kind: "close" | "delete" | "detach" }
if (leaf !== undefined) { /* ... */ }                      // truthiness 대신 명시 비교 (falsy 페이로드)
```
```rust
fn contained(root: &Path, path: &str) -> bool             // 서로 다른 타입 → 뒤집으면 컴파일 에러
fn delete_path(root: String, path: String)                // 필수
```
무엇이 깨졌나: 타입이 허용하는 값 공간이 불변식보다 넓어 잘못된 호출이 컴파일을 통과했다.\
같은 구조: 입력 정규화 함수가 비-total(조기 반환이 위반 입력을 그대로 통과) → 모든 입력을 정규화하는 total 함수 + raw 입력 테스트.

### 변형 B — optional 필드가 구버전을 조용히 수용
① 문제 코드
```rust
#[derive(Deserialize)]
struct Hook { #[serde(default)] key: Option<SessionKey>, /* ... */ }   // v1(키 없음)도 파싱 성공
```
② 고친 코드
```rust
#[derive(Deserialize)]
struct Hook { key: SessionKey, /* ... */ }                             // 필수 → v1은 파싱 실패
// 주의: serde는 Option<T> 필드가 입력에 없으면 #[serde(default)] 없이도 None으로 채운다 — default만 지워서는 안 되고 Option 자체를 빼야 한다
#[test] fn v1_hook_line_is_rejected() { assert!(parse::<Event>(V1_LINE).is_err()); }
```
무엇이 깨졌나: 버전 경계를 긋는 정보가 타입에서 선택 사항이었다.

### 변형 C — 불리언 하나로 세 상태 판정
① 문제 코드
```python
existing = sessions.get(key)
if existing is not None and existing.alive:        # pending(proc None)도 alive=False
    return existing
sessions[key] = Session(cmd)                        # pending 위에 두 번째 생성 → split-brain
```
② 고친 코드
```python
with lock:
    existing = sessions.get(key)
    if existing is not None and (existing.proc is None or existing.alive):   # pending·running 재사용
        return existing, False
    s = Session(cmd); sessions[key] = s                                      # dead만 재생성
    return s, True
# 접속 거절: proc is not None and not alive  (dead만)
```
무엇이 깨졌나: pending과 dead가 같은 값(False)으로 합쳐졌다.

### 변형 D — 결과 enum이 곱집합을 다 덮지 않음 + pid 신원
① 문제 코드
```rust
enum Outcome { Reattached, ProcessGone, TranscriptMissing }   // (없음 ∧ 없음) 조합 누락 → "복구 중"으로 오표기
let alive = pid_exists(rec.pid);                              // pid 재사용 → 남의 프로세스
```
② 고친 코드
```rust
enum Outcome { Reattached, ProcessGone, TranscriptMissing, Lost, IdInUse }  // 모든 조합에 이름·레코드
let alive = process_identity(rec.pid) == Some(rec.start_time);             // (pid, start_time)
let rec = if alive { Running { pid } } else { Exited { /* ... */ } };      // 살아 있으면 pid 유지, 종료 시각 지어내지 않음
```
무엇이 깨졌나: 독립 조건의 조합 하나가 이름 없이 인접 값으로 떨어졌고, 신원 확인이 재사용되는 값에 의존했다.

### 변형 E — 종단 상태 재전이 (이중 감산)
① 문제 코드
```java
void markAsRemoved(Node node) {
    for (;;) {
        Entry cur = node.get();
        Entry removed = new Entry(cur.value, REMOVED);
        if (node.compareAndSet(cur, removed)) { size.decrementAndGet(); return; }   // 두 번째 호출도 성공
    }
}
```
② 고친 코드
```java
for (;;) {
    Entry cur = node.get();
    if (cur.state == REMOVED) return;                 // 종단 상태 재전이 금지
    // ... CAS 성공 시에만 감산 → 노드당 정확히 1회
}
```
무엇이 깨졌나: 종단 → 종단 전이가 허용돼 부수효과(감산)가 두 번 일어났다.

### 변형 F — 검사 없는 set (전이 경쟁·취소 무력)
① 문제 코드
```python
def set_phase(deploy, phase):
    deploy["phase"] = phase                  # 현재 상태·소유자 무검사 → cancelling 위에 awaiting
```
② 고친 코드
```python
async def advance(deploy, phase):
    async with transition_lock:
        if current_deploy is not deploy or deploy["phase"] in PREEMPT_PHASES | DONE_STATES:
            raise CancelledError()           # 협조 중단 → 호출자가 정리
        deploy["phase"] = phase
        persist()
# 승인: awaiting→switching 원자 선점 (연타해도 1회) / 취소: cancelling 선점
# 전환 구간 예외 시 awaiting 복원 / REST·WS가 같은 advance() 사용
```
무엇이 깨졌나: 전이가 선행 상태를 확인하지 않아 경쟁 주체의 전이가 뒤섞였다.

## 검증 기록
- 2026-09-24: 사건 기록 대조·추상화(Claude 초안)

## 방안 비교

기본 방안(위 변형 A~F)은 "타입·전이 검사로 상태 공간을 닫는다"이다. 같은 원리에 닫아야 할 대상이 달라 다른 방안이 쓰인 사례:

### 방안 1 — 파괴 동작: 진행 여부와 옵션을 한 확인창에 겹치지 않음
```ts
// 문제: 한 번의 confirm이 "진행?"과 "강제?"를 겸함 → 취소(false)가 "강제 아님"으로 진행
const force = confirm("강제로 삭제할까요? (취소 = 일반 삭제)")
deleteBranch(name, { force })
// 고친: 질문 분리 — 취소는 언제나 중단
if (!confirm(`'${name}'을 삭제할까요?`)) return
const force = confirm("병합되지 않은 변경이 있으면 강제 삭제할까요?")
deleteBranch(name, { force })
// 되돌릴 수 없는 덮어쓰기(stash 적용, 충돌을 한쪽 버전으로 해결)에도 경고 확인 추가
```
사람의 응답(true/false)도 상태 공간이다 — 한 비트에 두 질문을 싣으면 취소라는 값이 사라진다. undo 경로는 없어 잔여 위험으로 남는다.

### 방안 2 — 전이 guard에 비단조 외부 입력 금지 (liveness)
```python
# 문제: 쿨다운 만료 후에도 메트릭이 나쁘면 전이 안 함 → 영구 고착
if cooldown_expired():
    if metrics_healthy(): state.phase = "phase2"; return "allow"
    return "cooldown_stage"                          # 머무름 — 메트릭이 곧 복구 대상 증상
# 고친: 전이는 시간만으로, 메트릭은 행동 보류로
if state.phase == "cooldown" and cooldown_expired():   # 선행 상태 확인 — 없으면 매 호출마다 attempts가 0으로 리셋돼 open에 도달 못 함
    state.phase = "phase2"; state.attempts = 0        # 단조 전이
if state.phase == "phase2":
    if state.attempts >= THRESHOLD: state.phase = "open"
    if not metrics_healthy(): return "metrics_stage"   # 이번 차례만 보류, attempts 미증가
```
부수 관찰: 상태가 메모리에만 있어 프로세스 재시작이 유일한 탈출구였다.\
같은 사건에서 복구 경로는 평상시 안 돌아 설정 드리프트(대상 서비스 이름 불일치)도 숨어 있었다 — 복구 경로가 한 번도 성공한 적이 없었다.

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 기본: 타입·전이 검사로 닫기 | 상태를 코드가 소유한다 | 타입 설계·check-and-set | 검사 누락 경로 하나로 다시 열림 | 세션·배포·캐시 엔트리 수명 |
| 1. 확인 질문 분리 | 상태 입력이 사람의 불리언 응답이다 | 확인 한 번 더 | 확인 피로 | 파괴·덮어쓰기 동작 |
| 2. 단조 guard | 전이 조건에 외부 관측값이 끼어든다 | 외부 입력을 행동 레이어로 이동 | 보류가 길어도 전이는 진행 → 시도 상한 필요 | 서킷브레이커·재시도 FSM |

**결론**: 불법 **상태**는 타입으로 표현 불가능하게, 불법 **전이**는 check-and-set과 종단 재전이 금지로 막는다.\
사람의 응답처럼 입력 자체가 상태를 만들면 **한 입력 = 한 질문**으로 공간을 닫는다.\
전이가 외부 관측값에 달려 있으면 전이 조건은 단조 입력만 쓰고 외부 값은 **행동을 보류**하는 데만 써서, 상태기계가 언젠가는 진행하도록(liveness) 보장한다.
