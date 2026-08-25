# SOLID 원칙 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 근거는 [2-summary.md](2-summary.md). 1회차 답안 시도 원본은 git 이력(f7a2086)에 보존.

## 정답

**1. 5원칙 사이의 우선순위**

서열이 아니라 **인과 사슬의 상류/하류**다. SRP(책임 하나)와 ISP(경계 얇게)가 상류에서 **계약을 작고 명확하게** 만들면 → LSP가 쉬워지고(약속이 적으면 깨트릴 것도 적다) DIP가 싸진다(포트가 좁으면 구현·가짜 구현이 싸다) → 그 결과 경계가 생겨 → OCP(새 구현체 추가로 확장)가 가능해진다. 앞의 원칙이 뒤의 원칙을 싸게 만들어준다.

**2. 원칙보다 우선하는 것**

원칙은 수단이고 목적은 하나 — **변경에 강한 코드(변경 비용 최소화)**. 그보다 앞서는 것은 동작의 정확성(제대로 동작하지 않는 코드에 설계 원칙은 무의미). 원칙끼리 충돌하면 목적으로 판정한다: **"실제로 변하는 축이 어디인가."** 충돌 해소 4개가 전부 이 축으로 환원된다 — 실제로 확장되는 축에만 열고(OCP↔단순함), 함께 변하는 것은 함께 두고(SRP↔응집도), 경계를 넘는 것에만 포트를 만든다(DIP↔생산성). 가독성·유지보수성은 그 결과이지 판정 기준이 아니다.

**3. SRP의 판정 기준**

**변경 이유(reason to change) = 액터(그 코드의 변경을 요구하는 이해관계자 집단)**. "한 가지 일"의 크기가 아니다 — 메서드 20개여도 액터가 하나면 지킨 것이다. 액터는 코드 안에 없고 코드 바깥의 사람이므로, **SRP는 코드만 읽어서는 판정할 수 없다** — 코드와 조직의 관계를 봐야 한다. (응집도는 코드만 읽고 판정 가능한 내재적 성질이라는 점이 결정적 차이.)

**4. 잘게 나눌수록 부딪히는 것과 해소**

**응집도**와 부딪힌다. 잘게 나눌수록 SRP는 지켜지지만 함께 변하는 것이 흩어져서, 변경 하나에 여러 파일을 동시에 고치게 된다. 해소: **함께 변하는 것은 함께 둔다 — SRP의 기준은 "변경 이유"지 "크기"가 아니다.** 액터가 하나면 뭉쳐 있어도 위반이 아니다.

**5. DIP vs DI**

- **DIP = 설계 원칙.** 관심사는 **의존의 방향** — 정책(도메인)이 세부(인프라)에 의존하지 않도록, 추상(인터페이스)을 도메인이 소유하고 세부가 그것을 구현한다.
- **DI = 구현 기법.** 관심사는 **의존 객체를 누가 넣어주는가** — 직접 new 하지 않고 외부(프레임워크·조립 코드)가 주입한다.

관계: DI는 DIP를 실현하는 흔한 수단이지 동의어가 아니다. DI 없이도 DIP는 가능하고(수동 조립), DIP 없이 DI도 가능하다(구체 클래스를 주입하면 방향은 그대로).

**6. instanceof가 "다형성이 깨진 증거"인 이유와 구별법**

다형성의 값어치 = **호출부가 구체 타입을 몰라도 되고, 새 타입이 추가돼도 호출부가 안 바뀐다.** AreaCalculator는 "넓이를 어떻게 구하나"라는 지식이 타입에서 빠져나와 호출부의 if 목록으로 샌 상태다 — instanceof 자체가 죄가 아니라 **증상**이고, 병은 "추상 타입을 통해 균일하게 다룰 수 없게 된 것"이다. 결정적 문제: 새 도형을 추가하고 분기를 빠트려도 **컴파일은 통과하고 런타임 예외로 발견**된다.

구별 기준은 한 줄: **새 타입을 추가했을 때 분기 개수가 늘어나는가.**

- 나쁜 instanceof — 구체 클래스 검사. 타입 수만큼 분기 증가, 호출부마다 복제, 빠트리면 런타임 예외.

```java
// 나쁨: 구체 클래스를 캐묻는다 — 타입이 늘 때마다 줄이 는다 (2-summary에서 발췌)
void process(Transaction tx) {
    if (tx instanceof SettledTransaction) return;
    if (tx instanceof RefundedTransaction) return;   // 나중에 또 하나 발견
    tx.cancel();
}
```

- 좋은 instanceof — 능력(capability) 인터페이스 검사(`instanceof Cancellable`). 분기 1개 고정, 데이터가 들어오는 **경계에서 한 번만** 좁히고 안쪽엔 없다.

```java
// 좋음: 경계에서 능력으로 한 번만 좁힌다 — 거래 타입이 20개로 늘어도 분기는 하나 (2-summary에서 발췌)
Transaction tx = repository.find(id);
if (tx instanceof Cancellable c) {
    cancelService.cancel(c);   // 이 안쪽에는 instanceof가 없다
} else {
    return Result.reject("정산 완료 거래는 취소할 수 없습니다");
}
```

근본 해법은 검사가 아니라 **행동을 타입 안으로**(`shape.area()`) 또는 **능력 타입으로 받기** — 잘못 넘기면 컴파일 에러가 되게 한다. 주입(DI)은 이 문제의 해법이 아니다 — 그건 5번의 주제.

```java
// 검사 자체를 없앤 형태: 못 취소하는 걸 넘기면 컴파일 에러 (2-summary에서 발췌)
void cancel(Cancellable tx) {
    tx.cancel();
}
```

**7. LogManager replay의 분리는 어떤 원칙인가**

일차로 **SRP**: "저장 포맷·순회"의 변경 이유(파일 형식, 인코딩)와 "복구 정책"의 변경 이유(커밋 판단, 반영 규칙)는 액터가 다르다. 동시에 **DIP의 사례**이기도 하다 — handler(함수 타입 = 추상)를 통해 "무엇을 반영할까"라는 정책을 호출자가 소유하고, LogManager는 그 추상만 안다.

실제 호출자 쪽 코드에서 그 분리가 이렇게 보인다:

```kotlin
// db-engine-lab impl/08-01 §5.4 Recovery.kt 에서 발췌
logManager.replay { rec ->                       // LogManager: 순서대로 읽어 넘겨주기만
    when (rec) {
        is LogRecord.BeginTx -> perTxInserts[rec.txId] = mutableListOf()
        is LogRecord.InsertRow ->
            perTxInserts.getOrPut(rec.txId) { mutableListOf() }
                .add(rec.tableName to rec.tupleBytes)
        is LogRecord.CommitTx -> committed.add(rec.txId)
        is LogRecord.AbortTx -> aborted.add(rec.txId)
        is LogRecord.Checkpoint -> { /* legacy Recovery ignores checkpoints */ }
    }
}

for ((txId, inserts) in perTxInserts) {
    if (txId !in committed || txId in aborted) continue   // ← 커밋 판단은 Recovery의 소유
    // ... heapLookup으로 테이블을 찾아 재반영 ...
}
```

"어떤 레코드를 믿고 반영할까"라는 지식이 전부 Recovery 쪽 자료구조(committed/aborted 집합)에 있고, LogManager에는 흔적도 없다는 점이 핵심이다.

LogManager가 커밋 판단까지 하면:

- **SRP** — 두 변경 이유가 한 파일에 모여, 포맷을 고치다 복구 정책을 깨트릴 수 있다.
- **OCP** — replay의 용도(복구·통계·디버깅·검증)가 늘 때마다 LogManager를 열어 고쳐야 한다. 지금 구조는 핸들러만 갈아끼우면 된다(수정이 아니라 추가로 흡수).
- **DIP** — 정책이 파일 IO라는 세부 안에 박혀, 정책을 테스트하려면 실제 파일이 필요해진다.
