# ops-patterns/08-saga — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 작성 방식: **2-summary를 닫고 기억만으로** 쓴다 → 실제 코드/원전으로 검증 → 틀린 부분만 수정.
> 기준 소스는 문서가 아니라 코드다 (`/home/jun/project/myway/ops-patterns/08-saga/impl/`).

⚠️ 정답은 Claude 초안(2026-09-14) — 원본 impl 코드·README 기준. 본인 검토 후 이 줄 삭제

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. -->

### A. 문제 (NaiveRunner · Saga 의 TODO)

#### 1. TODO 1 — NaiveRunner.run (기준선: 보상 없음)

정답 코드 (impl/NaiveRunner.java):

```java
public SagaResult run() {
    List<String> executed = new ArrayList<>();
    for (SagaStep step : steps) {
        try {
            step.execute();
        } catch (RuntimeException e) {
            // 되돌리지 않는다. 한 것은 한 채로 남는다.
            return SagaResult.compensated(executed, step.name(), List.of());
        }
        executed.add(step.name());
    }
    return SagaResult.success(executed);
}
```

- 존재 이유: **"보상이 없으면 무엇이 남는가"를 보여주는 기준선**이다.\
  되돌리는 코드가 없어서 짧고, 읽으면 맞는 것 같고, 정상 경로에서는 실제로 맞는다 — 그래서 위험하다.

> **사가(saga)** — 여러 서비스에 걸친 작업을 걸음의 연속으로 하고, 실패하면 한 걸음들을 거꾸로 보상하는 패턴.\
> 예: 재고 차감 → 결제 승인 → 배송 예약에서 배송이 실패하면 결제 취소 → 재고 복구로 되돌린다.

- 남는 것: 재고는 빠졌고, 돈은 받았고, 배송은 안 나간다.\
  고객은 돈을 냈는데 물건을 못 받고, 재고는 아무도 안 쓰는데 잠겨 있다.\
  **예외는 한 번 났고 그걸로 끝 — 어긋난 상태는 아무도 안 신고한다.**
- 되돌리는 코드를 쓰면 안 되는 이유: 그러면 이 클래스가 Saga 와 같아져서 기준선의 존재 이유(비교 대상)가 사라진다.
- 예외를 안 던지는 이유: 실패도 정상적인 결과이기 때문이다.\
  결과 객체로 돌려줘야 부르는 쪽이 상태를 판정할 수 있다.
- 실패한 걸음 이름: `SagaResult.compensated(executed, step.name(), List.of())` 의 두 번째 인자, 즉 `failedAt` 에 담긴다.\
  보상 목록은 빈 리스트다(되돌린 것이 없으니까).

#### 2. TODO 2 — Saga.run

정답 코드 (impl/Saga.java):

```java
public SagaResult run() {
    List<String> executed = new ArrayList<>();
    for (SagaStep step : steps) {
        try {
            step.execute();
        } catch (RuntimeException e) {
            // 이 걸음은 안 한 것이다. executed 에 안 넣는다.
            return compensate(executed, step.name());
        }
        executed.add(step.name());
    }
    return SagaResult.success(executed);
}
```

- executed 에 넣는 시점: **execute 가 성공한 뒤**다.\
  `try` 블록 다음 줄에 `executed.add(step.name())` 가 있다 — 던지면 이 줄에 도달하지 않는다.

> **걸음(step)** — 사가를 이루는 한 단위 작업(재고 차감, 결제 승인, ...).\
> 예: execute 와 compensate 한 쌍이 계약이다.

- 실패한 걸음을 executed 에 넣으면: compensate 가 그 걸음의 보상까지 부른다 — **하지도 않은 일을 취소**하게 된다(예: 차감 안 된 재고를 복구해서 재고가 불어난다).\
  원본 주석이 "이 상자에서 제일 흔한 실수"라고 지목한 지점이다.
- 예외를 던지면: 부르는 쪽이 "그래서 되돌려졌나(compensated)" vs "어긋난 채 막혔나(stuck)"를 알 방법이 없다.\
  둘은 후속 조치가 완전히 다르다.
- 반환: 전부 성공 → `SagaResult.success(executed)`.\
  중간 실패 → `compensate(executed, step.name())` 의 결과(compensated 또는 stuck).

#### 3. TODO 3 — Saga.compensate

정답 코드 (impl/Saga.java):

```java
private SagaResult compensate(List<String> executed, String failedAt) {
    List<String> compensated = new ArrayList<>();
    List<String> failures = new ArrayList<>();

    for (int i = executed.size() - 1; i >= 0; i--) {
        SagaStep step = stepNamed(executed.get(i));
        try {
            step.compensate();
            compensated.add(step.name());
        } catch (RuntimeException e) {
            // 멈추지 않는다. 나머지도 되돌려야 손으로 고칠 것이 준다.
            failures.add(step.name());
        }
    }

    return failures.isEmpty()
            ? SagaResult.compensated(executed, failedAt, compensated)
            : SagaResult.stuck(executed, failedAt, compensated, failures);
}
```

처리 과정 (재고✓ → 결제✓ → 배송✗):

```text
executed = [재고 차감, 결제 승인]   failedAt = 배송 예약

i=1  결제 승인.compensate()  -> 결제 취소   (뒤부터)
i=0  재고 차감.compensate()  -> 재고 복구

전부 성공  -> SagaResult.compensated   (값은 처음 상태)
일부 실패  -> SagaResult.stuck         (needsHumanHelp() == true)
```

- 거꾸로인 이유: **뒤 걸음이 앞 걸음에 기대고 있다.**\
  결제는 재고가 잡혀 있다는 전제로 돌았다.\
  실행의 역순으로 풀어야 전제가 깨진 상태가 생기지 않는다.

> **보상(compensation)** — 이미 한 일의 반대되는 일을 새로 해서 효과를 상쇄하는 것.\
> 예: 재고 차감↔재고 복구, 결제 승인↔결제 취소 — 롤백이 아니다.

- 앞에서부터 풀면: 잠깐 동안 "앞은 풀렸는데 뒤는 안 풀린" 상태가 생긴다.\
  그 창에서 다른 요청이 끼어든다 — 풀린 재고를 남이 가져가는데 결제 취소는 아직 도는 중.
- 멈추면 나빠지는 것: 하나가 안 됐다고 나머지를 포기하면 **손으로 고칠 것이 늘어나기만 한다.**\
  그래서 catch 안에서 failures 에 담고 루프를 계속 돈다.
- 조용히 넘기면: 데이터가 어긋난 채로 남고 아무도 모른다.\
  그래서 `compensationFailures` 에 담아 시끄럽게 만든다.
- 구분: 보상 전부 성공 = `compensated(...)` (compensationFailures 빈 목록), 일부 실패 = `stuck(...)` (failures 담김, `needsHumanHelp()` 가 참).

> **stuck(막힘)** — 보상마저 실패한 상태.\
> 예: 데이터가 어긋난 채이고 사람이 손으로 고쳐야 한다.

> **needsHumanHelp()** — 결과가 stuck 인지 묻는 판정.\
> 예: 참이면 조용히 넘기지 말고 알려야 한다.

### B. 개념

#### 4. 왜 사가인가

- 롤백이 없는 이유: 트랜잭션은 **한 저장소 안**의 보장이다.\
  07번은 저장소가 하나여서 DB가 롤백을 해줬지만, 여러 서비스에 걸치면 각 서비스가 자기 저장소를 따로 가진다 — 걸쳐 있는 트랜잭션이 없다.

> **트랜잭션(transaction)** — 한 저장소 안에서 "전부 되거나 전부 안 되거나"를 보장하는 단위.\
> 예: 서비스 여럿에 걸쳐서는 없다.

> **롤백(rollback)** — DB 트랜잭션이 커밋 전 변경을 없던 일로 만드는 것.\
> 예: 기록도 안 남는다 — 보상과 다른 점이 이것이다.

- "서로를 모른다": 결제 서비스와 재고 서비스는 서로의 저장소에 접근할 수 없으니, 둘을 묶어 "전부 되거나 전부 안 되거나"를 해줄 주체가 없다는 뜻이다.
- execute/compensate 가 짝인 이유: 롤백을 해줄 DB가 없으니 **되돌리는 일을 걸음마다 직접 써야 한다.**\
  그 쌍이 SagaStep 인터페이스의 계약이다(재고 차감↔재고 복구, 결제 승인↔결제 취소).

#### 5. 실패한 걸음 자신은 되돌리지 않는다

- 이유: execute 가 던졌으면 그 걸음은 아무것도 안 한 것이다.\
  되돌릴 것이 없는데 보상을 부르면 반대 방향의 효과만 새로 생긴다(안 차감된 재고가 복구로 불어난다).
- 전제: 각 걸음이 **all-or-nothing**(전부 하거나 아무것도 안 하거나)이어야 한다.

> **all-or-nothing** — 걸음 하나는 전부 하거나 아무것도 안 해야 한다는 전제.\
> 예: 이게 깨지면 "실패한 걸음은 안 되돌린다"가 무너진다.

- 절반쯤 하고 던지면: "안 한 것"이라는 전제가 깨져 절반이 어긋난 채 안 되돌려진다.\
  막는 수단: 각 걸음 안에서는 저장소가 하나이므로 **07번의 트랜잭션**을 쓴다.

#### 6. 보상의 멱등

- 이유: **보상 도중에 죽으면 다시 보상하기 때문**이다.\
  재시도가 전제이므로 두 번 불려도 결과가 같아야 한다.

> **멱등(idempotent)** — 여러 번 불려도 결과가 같은 성질.\
> 예: 보상은 재시도되므로 상대값이 아니라 절대값으로 써야 한다.

- 차이: "재고를 1 늘린다"는 상대값 — 두 번 부르면 재고가 11이 되어 없던 재고가 생긴다.\
  "재고를 원래 값으로"는 절대값 — 몇 번을 불러도 10이다.
- 주체: 06번에서는 **받는 쪽**(서버)이 중복 요청을 막아줬다.\
  여기서는 **내가**(보상을 쓰는 쪽이) 멱등하게 써야 한다.

#### 7. 보상 실패의 처리

- 멈추지 않는 이유: 남은 보상까지 포기하면 손으로 고칠 범위가 커지기만 한다.\
  끝까지 되돌리고, 안 된 것만 남긴다.
- needsHumanHelp() 참 = **stuck**: 보상마저 실패해 데이터가 어긋난 채이고, 자동으로는 못 고친다 — 사람이 손댈 차례라는 신호다.\
  구현은 `!compensationFailures.isEmpty()`.
- 예외로 던지지 않는 이유: 던지면 부르는 쪽이 "되돌려졌나"를 모른다.\
  실패도 결과다.
- 후속 조치 차이: compensated = 데이터는 처음 상태 — 재시도하거나 사용자에게 실패를 알리면 끝.\
  stuck = 데이터가 어긋나 있다 — 사람이 조사·수동 복구해야 한다.

#### 8. 보상은 롤백이 아니다

- 한 문장: **롤백은 없던 일로 만들고(기록도 안 남는다), 보상은 반대되는 일을 새로 해서(기록이 하나 더 남는다) 효과를 상쇄한다.**
- "없던 일"이 아닌 이유: 원장(Ledger)에는 `결제 승인 5000 / 결제 취소 5000` 이 둘 다 남는다.\
  값만 처음으로 돌아왔을 뿐 일어난 일은 일어난 것이다.\
  이미 나간 메일은 아예 못 되돌리고 정정 메일을 또 보낼 뿐이다.
- 본질이다: 명세서에 승인·취소가 둘 다 찍히는 것은 버그가 아니라 **사가를 선택한 순간 받아들인 것**이다.\
  "트랜잭션처럼 쓰되 느슨하게"가 아니라 다른 물건이다.

#### 9. 대가와 한계

- 코드량: 걸음이 n개면 되돌리는 코드도 n개 — **코드가 두 배**가 된다.
- 보상을 비워두면: 그 걸음만 안 되돌려지는데 **그 사실이 조용하다** — 컴파일도 되고 테스트도 그 경로를 안 밟으면 통과한다.
- 중간 상태: **보인다.**\
  결제까지 끝나고 배송 실패 직전에 밖에서 조회하면 재고가 줄고 돈이 빠져 있다.\
  트랜잭션은 커밋 전까지 안 보이는데 사가는 보인다.

> **중간 상태 노출** — 사가 진행 중의 어중간한 상태가 바깥 조회에 보이는 것.\
> 예: 트랜잭션과의 결정적 차이다.

- 되돌릴 수 없는 걸음(메일 발송, 물리 배송): **가능한 한 뒤에** 둔다.\
  먼저 해버리면 그 뒤에서 실패했을 때 보상이 불가능해 전부 손으로 고쳐야 한다.

> **되돌릴 수 없는 걸음** — 메일 발송·물리 배송처럼 보상이 불가능한 일.\
> 예: 가능한 한 뒤에 둔다.

#### 10. 연결

- 걸음 안의 all-or-nothing: **07-outbox 의 (단일 저장소) 트랜잭션**으로 보장한다.
- 보상 도중에 죽으면: 재시도가 필요하고, 그래서 **보상의 멱등(06-idempotency-store 의 성질)** 이 다시 필요해진다.
- 확장 순서: 06 = 한 요청이 두 번 와도 한 번만 처리(받는 쪽 멱등) → 07 = 저장과 발행을 한 트랜잭션처럼(단일 저장소의 원자성) → 08 = 저장소 여럿에 걸친 작업의 원자성 흉내(보상).\
  **"한 번만, 전부-아니면-말고"를 점점 넓은 범위로 끌고 가는 순서**다.\
  (원본에 근거 있는 연결 — 09는 "여럿이 같은 것을 원할 때"로 문제가 바뀐다.)

## 근거

- 기준 소스: `/home/jun/project/myway/ops-patterns/08-saga/impl/NaiveRunner.java`, `impl/Saga.java`
- 계약: `src/main/java/com/ops/saga/SagaStep.java`, `SagaResult.java`
- 문제 원문: `src/main/java/com/ops/saga/NaiveRunner.java`(TODO 1), `Saga.java`(TODO 2·3), `README.md` "특히 생각해볼 것" 1~9
