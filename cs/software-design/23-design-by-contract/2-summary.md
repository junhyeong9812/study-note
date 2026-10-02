# software-design/23-design-by-contract — 사전조건·사후조건·클래스 불변식 — 정리 (힌트)

## 해결하는 문제

"이 값이 유효한지 누가 확인하나"가 정해져 있지 않으면 두 가지 중 하나가 된다. 둘 다 안 하거나, 둘 다 한다.

```text
 계약 없음 (서로 미룸)                       방어적 프로그래밍 (둘 다 검사)
 호출자: "재고 쪽이 막겠지"                   호출자: if (qty < n) 거절
 재고:   "호출자가 확인했겠지"                 재고:   if (qty < n) 거절   ← 같은 검사 2벌
    → 아무도 안 막음 → qty = -3 저장            → 규칙이 바뀌면 2곳을 고쳐야 하고, 한 곳만 고치면 어긋난다

 계약 (책임을 한쪽에)
 재고.decrease(n)  사전조건: 1 <= n <= qty   ← 호출자의 의무
                   사후조건: qty == old(qty) - n   ← 재고의 의무
                   불변식:   qty >= 0        ← 공개 메서드 전후마다 재고가 지킴
```

- *계약에 의한 설계(Design by Contract, DbC)*: 루틴마다 호출자와 공급자의 의무·이익을 명시하는 방법. Bertrand Meyer가 Eiffel과 함께 제시했다(Meyer 1992 "Applying 'Design by Contract'", IEEE Computer 25(10)).
- *사전조건(precondition)*: 호출 전에 참이어야 하는 조건. **호출자의 의무**, 공급자의 이익.
- *사후조건(postcondition)*: 정상 종료 뒤 참이어야 하는 조건. **공급자의 의무**, 호출자의 이익.
- *클래스 불변식(class invariant)*: 객체가 바깥에 보이는 시점(생성 직후, 공개 메서드 호출 전후)마다 참이어야 하는 조건.
- *방어적 프로그래밍(defensive programming)*: 각 모듈이 가능한 모든 검사를 넣는 방식. Meyer는 이것이 중복 검사로 복잡도를 키운다고 비판했다.

쉬운 예: 택배 계약이다. 고객은 무게 제한을 지켜 포장하고(사전조건), 택배사는 하루 안에 배달한다(사후조건). 고객이 제한을 어기면 택배사는 책임이 없다.\
똑같은 구조다.\
실무 예: 재고 차감, 포인트 사용, 좌석 예약. "음수 재고", "합이 안 맞는 좌석 수"는 계약이 비어 있다는 신호다.

## 동작·원리

### 1. 계약의 세 조각과 검사 시점

```text
            ┌─ 불변식 참 ─┐
 호출 ──> [사전조건 검사] ──> 본문 ──> [사후조건 검사] ──> 반환
            호출자 책임          공급자 책임
                               └─ 불변식 참 ─┘  (공개 메서드 끝마다)
 생성자 ──────────────────────────> [불변식 참]      (생성 직후)
```

- Eiffel 문서: 불변식은 "true before and after the execution of every exported routine"이어야 한다. 요구 시점이 "실행 전후"이므로, 루틴 **실행 도중**에는 잠시 깨져도 된다고 읽는다(해석 — 문서 문장은 전후 시점만 말한다).
- 위반의 책임(Eiffel 문서 "whose fault it is"): 사전조건 위반 = 호출자 버그. 사후조건·불변식 위반 = 공급자 버그.

### 2. 누가 검사하나 — Meyer의 규칙 (저자 주장)

- Meyer 1992: "Either you have the condition in the Require, or you have it in an If instruction in the body of the routine, but never in both." 조건은 사전조건(호출자 책임)이거나 본문 처리(공급자 책임) **둘 중 하나**다.
- 어느 쪽에 둘지는 정해진 답이 없다. 사전조건이 강한 "demanding" 루틴부터 약한 "tolerant" 루틴까지 가능하고, 기준은 "maximize the overall simplicity of the architecture"(Meyer 1992).
- 해석: "둘 다 검사"도 "둘 다 미룸"도 계약이 없다는 같은 병의 두 증상이다.

### 실험 A: 계약 없음 vs 계약 명시 vs `assert`만

```java
static class StockNoContract {                    // (1) 계약 없음 — 아무도 검사 안 함
    int qty;
    void decrease(int n) { qty -= n; }
}
static class Stock {                               // (2) 계약 명시
    private int qty;                               // 클래스 불변식: qty >= 0
    /** 사전조건: 1 <= n <= qty.  사후조건: qty == old(qty) - n. */
    void decrease(int n) {
        if (n < 1 || n > qty) throw new IllegalArgumentException("사전조건 위반: 1 <= n <= " + qty + ", n=" + n);
        int old = qty;
        qty -= n;
        assert qty == old - n : "사후조건 위반";
        assert invariant() : "불변식 위반";
    }
    private boolean invariant() { return qty >= 0; }
}
static class StockAssertOnly {                     // (3) 사전조건을 assert로만
    int qty;
    void decrease(int n) { assert n >= 1 && n <= qty : "사전조건 위반 n=" + n; qty -= n; }
}
// 셋 다 qty=2에서 decrease(5)
```

(실험, JDK 21.0.12 temurin `--cpus=2`, `scratchpad/sd/20/e23/Contract.java`, 2026-10-02)

```text
== java Contract.java (기본)
assertions enabled = false
(1) 계약 없음      : qty=-3  ← 무효 상태가 그대로 저장된다
(2) 계약 명시      : 사전조건 위반: 1 <= n <= 2, n=5, qty=2
(3) assert만       : qty=-3
== java -ea Contract.java
assertions enabled = true
(1) 계약 없음      : qty=-3  ← 무효 상태가 그대로 저장된다
(2) 계약 명시      : 사전조건 위반: 1 <= n <= 2, n=5, qty=2
(3) assert만       : AssertionError: 사전조건 위반 n=5, qty=2
```

- (1) 무효 상태(-3)가 조용히 들어갔다 — 커리큘럼 ⚠ 칸의 "서로 검증 미룸 → 무효 상태 진입".
- (3) `assert`로만 쓴 사전조건은 `-ea` 없이는 **실행되지 않았다**. JVM 기본값에서 assertion은 꺼져 있다(Oracle "Programming With Assertions": "disabled by default").
- (2) 공개 메서드의 사전조건을 예외로 검사하면 플래그와 무관하게 막힌다. Oracle 문서도 "Do not use assertions for argument checking in public methods"라고 하고, 사후조건·불변식에는 `assert`를 쓸 수 있다고 적는다.

### 3. 예외가 중간에 나면 불변식이 깨진 채 남는다

```text
 reserveBroken:  available -= n  →  (검사 실패, 예외)  →  reserved += n  (실행 안 됨)
 reserveSafe:    모든 검사 먼저   →  available -= n; reserved += n  (한꺼번에)
```

### 실험 D: 검사 위치와 불변식

(실험, JDK 21.0.12, `scratchpad/sd/20/e23/Partial.java`, 불변식 `reserved + available == total`)

```text
broken: 예외(user) 뒤 available=7 reserved=0 invariant=false
safe  : 예외(user) 뒤 available=10 reserved=0 invariant=true
```

- 공개 메서드가 예외로 끝나도 객체는 바깥에 다시 보인다. 그때도 불변식이 참이어야 한다.
- 대처 순서: **검사 → 계산 → 상태 변경**. 상태를 여러 필드에 걸쳐 바꾸면 마지막에 한꺼번에 바꾸거나, 새 값 객체를 만들어 한 번에 교체한다(불변 객체는 [19-immutability-and-value-objects](../19-immutability-and-value-objects/2-summary.md)).

### 4. 상속과 계약 — 하청(subcontract) 규칙

```text
 부모 계약      require: amount >= 1      ensure: 결과 != null
 자식이 해도 됨  require: 더 약하게(OR)     ensure: 더 강하게(AND)     = 일을 더 잘하는 하청
 자식이 하면 안 됨 require: 더 강하게        ensure: 더 약하게          = 호출자를 속이는 하청
```

- Meyer 1992: 동적 바인딩은 일을 하청 주는 것이고, 하청은 원청의 약속을 지켜야 한다. 하청이 사전조건을 강화하거나 사후조건을 약화하면 "fooling" 호출자가 된다.
- Eiffel은 이를 문법으로 강제한다: 재정의에서 `require else`로 붙인 조건은 원래 사전조건과 **or**, `ensure then`은 원래 사후조건과 **and** 된다(Eiffel 문서). 그래서 재정의가 사전조건을 강화할 수 없다.
- 자바에는 이 강제가 없다. LSP([22-solid](../22-solid/2-summary.md))가 같은 규칙을 원칙으로 말한다.

### 실험 B: 자바에서 하위 타입이 계약을 바꾸면

```java
static class Gateway {                                  /** 계약: amount >= 1 이면 승인 코드(null 아님) */
    String approve(long amount) { if (amount < 1) throw new IllegalArgumentException("amount >= 1"); return "APPROVED-" + amount; }
}
static class StrictGateway extends Gateway {            // 사전조건 강화
    @Override String approve(long amount) { if (amount < 100) throw new IllegalArgumentException("amount >= 100 (하위 타입이 강화한 사전조건)"); return super.approve(amount); }
}
static class LenientGateway extends Gateway {           // 사후조건 약화
    @Override String approve(long amount) { return amount > 1_000_000 ? null : super.approve(amount); }
}
// 호출자: g.approve(amount).toLowerCase()
```

(실험, JDK 21.0.12, `scratchpad/sd/20/e23/Subcontract.java`)

```text
Gateway -> approved-50
StrictGateway -> IllegalArgumentException: amount >= 100 (하위 타입이 강화한 사전조건)
Gateway -> approved-2000000
LenientGateway -> NullPointerException: Cannot invoke "String.toLowerCase()" because the return value of "Subcontract$Gateway.approve(long)" is null
```

- 둘 다 컴파일은 통과했다. 부모 계약만 믿은 호출자가 실행 중에 깨졌다. NPE 메시지(JEP 358 "Helpful NullPointerExceptions")는 `Gateway.approve`의 반환값을 가리켜, 하위 타입이 원인이라는 것은 드러나지 않는다.

### 5. 자바에서 계약을 표현하는 수단

| 무엇 | 수단 | 꺼질 수 있나 |
|---|---|---|
| 공개 메서드 사전조건 | `IllegalArgumentException`·`IllegalStateException`·`Objects.requireNonNull`, javadoc `@throws` | 아니오 |
| 사후조건·내부 불변식 | `assert` | 예 (`-ea` 없으면 꺼짐) |
| 값의 불변식(생성 시점) | `record` 간결 생성자(compact constructor), 정적 팩토리 | 아니오 |
| 상속 시 자기 호출 계약 | javadoc `@implSpec` (JDK 소스 관례) | — |

### 실험 C: record 간결 생성자로 값 불변식

```java
record Money(long won) {
    Money { if (won < 0) throw new IllegalArgumentException("won >= 0: " + won); }   // 모든 생성 경로가 지나간다
    Money minus(Money o) { return new Money(won - o.won); }
}
```

(실험, JDK 21.0.12, `scratchpad/sd/20/e23/MoneyRec.java`)

```text
1000-300 = Money[won=700]
1000-3000 -> won >= 0: -2000
```

- 연산 결과도 생성자를 지나므로, 음수 금액 값은 만들어지지 않는다. 생성 시점에 불변식을 확보하는 쪽으로 더 나가면 [24-types-as-invariants](../24-types-as-invariants/2-summary.md).

## 쓰이는 자료구조·알고리즘

- **호어 삼중항(Hoare triple)** `{P} S {Q}`(지금 쓰는 표기, Hoare 1969 원문은 `P {S} Q`): "P가 참일 때 S를 실행해 **끝난다면** Q가 참". 종료 자체는 따로 증명한다(부분 정확성). 사전조건 = P, 사후조건 = Q. Hoare 1969 "An axiomatic basis for computer programming". Meyer 1992도 클래스 불변식이 Hoare의 data invariant에서 왔다고 적는다.
- **불변식 검사 = 술어 평가**: `invariant()`는 객체 상태에 대한 불리언 함수. 공개 메서드 끝마다 평가하면 비용은 술어의 복잡도에 비례한다(예: 항목 합 검사는 O(항목 수)). 그래서 운영에서는 끄거나 가벼운 것만 남긴다.
- **상태 기계의 가드**: 상태 전이의 사전조건이 가드다. "PAID에서만 refund 가능"은 `refund`의 사전조건이자 상태 기계의 전이 가드(domain-modeling 11 state-machines-in-domain — 미작성, [domain-modeling/curriculum](../../domain-modeling/curriculum.md)).
- **스냅숏(old 값)**: 사후조건 `qty == old(qty) - n`을 검사하려면 호출 전 값을 저장해야 한다. Eiffel `old` 식, 자바는 지역 변수(실험 A의 `int old`). Oracle 문서는 상태를 저장하는 내부 클래스 방법을 보인다.

## 적용 — 풀어나가는 법

1. **공개 메서드마다 계약을 한 줄씩 적는다**(javadoc). 사전조건 / 사후조건 / 던지는 예외.
2. **각 조건의 책임자를 하나로 정한다.** 사전조건이면 호출자가 지키고 공급자는 입구에서 예외로 거절(빠른 실패). 공급자가 처리할 것이면 사전조건에서 빼고 본문에서 처리. 두 곳에 같은 검사를 두지 않는다.
3. **신뢰 경계 입력은 계약이 아니라 입력 검증이다.** 사용자·외부 시스템 입력은 경계에서 검증해 도메인 타입으로 바꾼다(24 parse, don't validate). 안쪽 메서드의 사전조건은 그 타입이 이미 보장한다.
4. **검사 → 계산 → 상태 변경** 순서(실험 D).
5. **불변식은 한 메서드로 모아 테스트에서 호출한다.** 운영에서는 `assert`(꺼짐)나 비용이 작은 것만.
6. **하위 타입은 부모 계약 테스트를 통과해야 한다**(실험 B의 두 위반은 부모 계약 테스트로 잡힌다).

```java
/**
 * 포인트를 사용한다.
 * 사전조건: amount >= 1, amount <= balance()  (위반 시 IllegalArgumentException)
 * 사후조건: balance() == old(balance()) - amount
 * 불변식:   balance() >= 0
 */
public void use(long amount) {
    if (amount < 1 || amount > balance)
        throw new IllegalArgumentException("1 <= amount <= " + balance + ", amount=" + amount);
    long old = balance;
    balance -= amount;
    assert balance == old - amount && balance >= 0;
}
// 호출자: 사전조건을 지킬 책임 — 같은 검사를 또 하지 않고, 필요하면 조회로 확인
if (points.balance() >= price) points.use(price); else return Result.reject("포인트 부족");
```

진단 — 계약이 비었거나 겹친 곳 찾기:

```bash
# 공개 메서드 사전조건을 assert로만 하는 곳 (운영에서 꺼짐)
grep -rnE '^\s*assert ' src/main/java | head
# 같은 검사식이 여러 파일에 반복 (방어적 중복 후보)
grep -rhoE 'if \([a-zA-Z.()]+ ?[<>]=? ?[0-9]+\)' src/main/java | sort | uniq -c | sort -rn | head
```

## 장애 시나리오와 대처

### 1. 계약 미명시 → 서로 검증을 미뤄 무효 상태 진입

- 현상: 재고가 음수인 상품, 사용 가능 포인트가 음수인 회원이 DB에 있다.
- 보이는 형태: 에러 로그 없음. 정합성 점검 쿼리(`WHERE qty < 0`)나 정산 불일치로 발견. 실험 A (1)의 `qty=-3`.
- 원인: 호출자는 공급자가, 공급자는 호출자가 검사한다고 가정했다.
- 대처: 공급자 공개 메서드 입구에 사전조건 검사(예외)를 둔다. DB 제약(`CHECK (qty >= 0)`)을 마지막 방어선으로 추가할 수 있다. 이미 저장된 무효 데이터는 따로 찾아 보정한다.

### 2. 사전조건을 `assert`로만 → 운영에서 검사가 꺼져 있다

- 현상: 테스트에서는 `AssertionError`로 잡히던 잘못된 호출이 운영에서 통과해 무효 상태가 된다.
- 보이는 형태: 실험 A (3) — 기본 실행 `qty=-3`, `-ea` 실행 `AssertionError`. 로컬·CI만 `-ea`를 켜 둔 경우 환경별로 동작이 다르다.
- 원인: JVM 기본값에서 assertion은 꺼져 있다.
- 대처: 공개 메서드의 인자 검사는 예외로(Oracle 문서 권고). `assert`는 내부 불변식·사후조건 확인용으로만.

### 3. 방어적 중복 검사 → 규칙 변경 때 한 곳만 바뀌어 어긋난다

- 현상: 최소 주문 금액이 1,000원에서 5,000원으로 바뀌었는데 일부 경로에서 3,000원 주문이 통과한다.
- 보이는 형태: 같은 검사식이 컨트롤러·서비스·도메인에 각각 있고 값이 다르다(위 grep으로 확인).
- 원인: 책임자를 정하지 않고 "혹시 몰라" 여러 곳에 검사했다. Meyer가 방어적 프로그래밍을 비판한 이유다.
- 대처: 조건마다 책임자 하나. 규칙은 공급자(도메인 메서드 또는 값 타입 생성자)에 한 번만 두고, 바깥은 그 결과(예외·Result)를 처리한다.

### 4. 하위 타입이 사전조건을 강화·사후조건을 약화 → 부모 계약만 믿은 호출자가 깨진다

- 현상: 새 결제 게이트웨이 구현으로 바꾼 뒤 소액 결제가 실패하거나, 승인 코드 처리에서 NPE.
- 보이는 형태: 실험 B의 `IllegalArgumentException: amount >= 100`, `NullPointerException ... return value of "Subcontract$Gateway.approve(long)" is null`.
- 원인: 하청 규칙 위반. 자바 컴파일러는 계약을 검사하지 않는다.
- 대처: 부모 타입 계약 테스트를 모든 구현에 돌린다. 사전조건이 다르면 다른 타입(다른 인터페이스)으로 나눈다.

### 5. 예외로 중간 종료 → 불변식이 깨진 객체가 남는다

- 현상: 예약 실패 응답을 받았는데 잔여 좌석이 줄어 있다.
- 보이는 형태: 실험 D의 `available=7 reserved=0 invariant=false`.
- 원인: 상태 일부를 바꾼 뒤 검사가 실패했다.
- 대처: 검사를 모두 먼저, 상태 변경은 마지막에 한꺼번에. DB까지 걸치면 트랜잭션으로 묶는다.

## 핵심 문장

- 계약은 "누가 무엇을 확인하나"를 정한다. 사전조건은 호출자의 의무, 사후조건과 불변식은 공급자의 의무다.
- Meyer의 규칙: 한 조건은 사전조건이거나 본문 처리 둘 중 하나 — 둘 다(방어적 중복)도, 둘 다 아님(서로 미룸)도 계약이 없다는 신호다.
- 자바 `assert`는 기본으로 꺼져 있다. 공개 메서드의 인자 검사는 예외로 하고, `assert`는 사후조건·내부 불변식에 쓴다.
- 불변식은 공개 메서드가 예외로 끝날 때도 지켜져야 한다 — 검사 먼저, 상태 변경은 마지막에.
- 하위 타입은 사전조건을 약하게, 사후조건을 강하게만 바꿀 수 있다. Eiffel은 문법으로 강제하고, 자바에서는 계약 테스트로 지킨다.

## 관련 주제·근거

- 선행
  - [22-solid](../22-solid/2-summary.md) — LSP(계약 호환성)
- 후속·연결
  - [24-types-as-invariants](../24-types-as-invariants/2-summary.md) — 계약을 타입으로 옮겨 생성 시점에 확보
  - [19-immutability-and-value-objects](../19-immutability-and-value-objects/2-summary.md) — 불변 값으로 불변식 유지
  - [15-error-handling-design](../15-error-handling-design/2-summary.md) — 계약 위반을 어떤 오류로 알리나
  - [20-oop-fundamentals](../20-oop-fundamentals/2-summary.md) — 캡슐화(불변식을 지킬 문을 좁히기)
  - [engineering/solid-principles](../../engineering/solid-principles/2-summary.md) 「L — 계약 관점의 정확한 규칙」
- 글·문서
  - Bertrand Meyer, "Applying 'Design by Contract'", IEEE Computer 25(10):40–51, 1992-10. doi:10.1109/2.161279 · 저자 PDF <https://se.inf.ethz.ch/~meyer/publications/computer/contract.pdf>
  - Eiffel 문서 "Design by Contract and Assertions"(불변식 시점, 책임 소재, `require else`·`ensure then`) <https://www.eiffel.org/doc/solutions/Design_by_Contract_and_Assertions>
  - C. A. R. Hoare, "An axiomatic basis for computer programming", CACM 12(10):576–580, 1969. doi:10.1145/363235.363259
  - Oracle, "Programming With Assertions"(기본 비활성, 공개 메서드 인자 검사에 쓰지 말 것, 사후조건·클래스 불변식) <https://docs.oracle.com/javase/8/docs/technotes/guides/language/assert.html>
  - JEP 395 Records(JDK 16) <https://openjdk.org/jeps/395>
- 실험 목록 (JDK 21.0.12 temurin 컨테이너 `--cpus=2 --network none`, 2026-10-02)
  - A `scratchpad/sd/20/e23/Contract.java` — 계약 없음/명시/assert만, `-ea` 유무
  - B `scratchpad/sd/20/e23/Subcontract.java` — 하위 타입의 사전조건 강화·사후조건 약화
  - C `scratchpad/sd/20/e23/MoneyRec.java` — record 간결 생성자 불변식
  - D `scratchpad/sd/20/e23/Partial.java` — 예외 중간 종료와 불변식
