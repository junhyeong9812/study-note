# java/java-design-patterns/06 — Adapter (어댑터) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. `50000원` 이 찍히고 `ok` 는 `true` — 소수점은 버려진다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
  [레거시카드] 결제 처리: 50000원
```

`ok` 는 `true` 다.

**왜 그런가**

- `LegacyCardAdapter.pay` 는 `(int) amount` 로 금액을 바꾼다 — `50000.9` 의 소수점 아래가 버려져 `50000` 이 된다.
- `processCard` 가 그 값을 찍고 `1001` 을 돌려준다.
- `1001 > 0` 이므로 `true` 다.
- 근거: 2-summary 「동작 방식 (4)」, 「어디서 틀리나 4」.

### 2. 레거시가 먼저, PayPal 이 다음 — 각 블록 끝에 빈 줄

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
[레거시 카드 결제] 주문 ORD-001 처리
  [레거시카드] 결제 처리: 50000원
  결제 결과: 성공

[PayPal] 주문 ORD-001 처리
  [PayPal] 인증 및 결제: $37.5
  결제 결과: 성공

```

**왜 그런가**

- `List.of` 는 넣은 차례를 지키므로 레거시 어댑터가 먼저 처리된다.
- `processOrder` 는 이름 줄 → `pay` 안의 Adaptee 출력 줄 → 결과 줄 → 빈 줄을 찍는다.
- 레거시: `(int) 50000.0` → `50000`, 트랜잭션 번호 `1001 > 0` 이라 성공이다.
- PayPal: `50000 * 0.00075` 는 약 `37.5` 이고, `"PP-<밀리초>"` 는 비어 있지 않으니 성공이다.
- 달러 금액이 정확히 `37.5` 로 찍히는지는 부동소수점 표기에 달려 있다(확인 필요).
- 근거: 2-summary 「동작 방식 (4)」 · 「(5)」, 「구현 세부사항 대 언어 보장」.

### 3. `NumberFormatException` 으로 끝난다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

`cancelPayment` 는 불리지 않고 `NumberFormatException` 이 던져진다.
아무 줄도 찍히지 않는다.

**왜 그런가**

- `LegacyCardAdapter.refund` 는 `Integer.parseInt(transactionId)` 로 먼저 문자열을 정수로 바꾼다.
- `"PP-1700000000000"` 은 숫자가 아니라 파싱이 실패한다.
- 예외가 `cancelPayment` 호출 전에 나므로 취소 메시지도 찍히지 않는다.
- 근거: 2-summary 「어디서 틀리나 4」.

### 4. 클라이언트는 Target 인터페이스에만 의존하기 때문이다

- `processOrder` 는 `PaymentProcessor` 의 `getName` · `pay` 만 부른다.
- 시스템마다 다른 이름 · 타입 · 단위 차이는 어댑터 안에서 흡수된다.
- 그래서 새 시스템이 오면 `PaymentProcessor` 를 구현하는 어댑터 하나만 더 만들면 된다.
- 근거: 2-summary 「동작 방식 (5)」, 「핵심 문장 2」.

### 5. 위임은 품는 객체를 갈아 끼울 수 있고 상속은 한 클래스에 고정되기 때문이다

- 클래스 어댑터는 `extends Adaptee` 로 컴파일 시점에 Adaptee 하나에 묶인다.
- Java 는 클래스를 하나만 상속하므로 여러 Adaptee 를 한 어댑터에 묶을 수 없다.
- 상속하면 Adaptee 의 공개 메서드가 어댑터 바깥으로도 드러난다.
- 객체 어댑터는 필드에 무엇을 넣느냐로 바뀌므로 Adaptee 의 하위 클래스 인스턴스도 넣을 수 있다.
- 근거: 2-summary 「동작 방식 (6)」, 「어디서 틀리나 2」.

### 6. 트랜잭션 번호 · 환불 금액 · 소수점 · 환불 성공 여부가 사라진다

- `pay` 가 `boolean` 만 돌려주므로 Adaptee 가 만든 트랜잭션 번호(`1001`, `"PP-..."`)를 클라이언트가 받지 못한다 — 그런데 `refund` 는 그 ID 를 요구한다.
- 두 어댑터의 `refund` 는 `amount` 를 무시한다 — 부분 환불을 표현하지 못한다.
- `(int)` 변환으로 금액의 소수점 아래가 버려진다.
- PayPal 의 `voidTransaction` 은 `void` 라 결과를 모르는데도 `refund` 는 무조건 `true` 를 돌려준다.
- `orderId` 를 `email` 자리에 넣어 뜻이 맞지 않는다.
- 근거: 2-summary 「어디서 틀리나 4 · 5 · 6」.

### 7. 인터페이스가 이미 맞을 때, 그리고 어댑터가 너무 많아져 복잡도가 이득을 넘을 때다

- 인터페이스가 이미 맞으면 어댑터는 쓸데없는 층일 뿐이다.
- 어댑터는 시스템마다 하나씩 생기므로 많아지면 변환 규칙이 여러 곳에 흩어져 복잡도가 오른다.
- Adaptee 소스를 고치는 것도 어댑터의 답이 아니다 — 고치면 그것은 통합이 아니라 개조다.
- 근거: 2-summary 「어디서 틀리나 1 · 7」, 「언제 쓰고 언제 안 쓰나」.

### 8. Target 은 `List` 인터페이스, Adaptee 는 배열이다

- `Arrays.asList()` 는 배열을 `List` 인터페이스로 변환해 준다.
- 배열(이미 있는 것)을 고치지 않고 `List` 를 원하는 코드에 넘길 수 있게 한다.
- 근거: 2-summary 「문법 — 형태와 규칙」의 마지막 규칙, 원본 팁.

### 9. 인터페이스를 통한 다형성과 구성(composition) · 생성자 주입이다

- 두 어댑터가 모두 `PaymentProcessor` 를 구현하므로 같은 타입으로 한 목록에 담기고, 같은 호출이 각자 다르게 동작한다 — 인터페이스 다형성이다.
- Adaptee 를 상속하지 않고 `final` 필드로 품는 것은 구성(composition)이다.
- 그 필드를 생성자로 받아 바깥에서 무엇을 넣을지 정하는 것은 생성자 주입이다.
- 근거: 2-summary 「동작 방식 (3)」 · 「(5)」.

## 실습 정답

### 실습 1. 두 결제 시스템을 하나의 결제 인터페이스로 통합하기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. Target 세 메서드 선언 | `interface PaymentProcessor` 의 `pay` · `refund` · `getName` |
| 2. 레거시 어댑터가 Target 구현 · Adaptee 를 final 필드로 | `class LegacyCardAdapter implements PaymentProcessor`, `private final LegacyCardPayment legacySystem` |
| 3. 생성자로 Adaptee 받기 | `public LegacyCardAdapter(LegacyCardPayment legacySystem)` |
| 4. 금액을 int 로 · orderId 를 토큰 자리에 | `int amountInCents = (int) amount;`, `legacySystem.processCard(orderId, amountInCents)` |
| 5. 번호 저장 · 0 초과면 true | `lastTransactionNumber = ...`, `return lastTransactionNumber > 0;` |
| 6. 문자열 ID 파싱 후 취소 | `legacySystem.cancelPayment(Integer.parseInt(transactionId))` |
| 7. PayPal 어댑터가 Target 구현 · SDK 를 final 필드 · 생성자 | `class PayPalAdapter implements PaymentProcessor`, `private final PayPalSDK paypal`, `public PayPalAdapter(PayPalSDK paypal)` |
| 8. 달러 변환 · orderId 를 이메일 자리에 | `double usdAmount = amount * EXCHANGE_RATE;`, `paypal.authorize(orderId, usdAmount)` |
| 9. ID 가 null 아니고 비어 있지 않으면 true | `return txnId != null && !txnId.isEmpty();` |
| 10. 무효화 후 true | `paypal.voidTransaction(transactionId); return true;` |
| 11. 클라이언트가 Target 메서드만 씀 | `processOrder` 의 `processor.getName()` · `processor.pay(...)` |
| 12. 두 어댑터를 한 목록에 담아 처리 | `main` 의 `List.of(...)` 와 `for` 문 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`java/java-design-patterns/reference/adapter.java`

```java
// [디자인 패턴] Adapter (어댑터)
// 설명: 호환되지 않는 인터페이스를 가진 클래스들을 함께 동작하도록 변환하는 패턴. 레거시 코드 통합에 유용
// 팁: 어댑터는 기존 코드를 수정하지 않고 새로운 인터페이스에 맞추는 것이 핵심이다. Java의 Arrays.asList()는 배열을 List 인터페이스로 변환하는 어댑터이다. 객체 어댑터(위임)가 클래스 어댑터(상속)보다 유연하다.

// === Adapter 패턴 ===
// 해결 문제: 우리 시스템 인터페이스(Target)와 외부/레거시 API(Adaptee)의 시그니처 불일치
// 참여자: Target(원하는 인터페이스), Adaptee(기존 클래스), Adapter(둘을 이어주는 변환기), Client
// 장점: 기존 코드 수정 없이 통합. 단점: 어댑터가 많아지면 복잡도 증가
// 서로 다른 결제 시스템을 통합 인터페이스로 변환

// java.util.List: 여러 결제 처리기를 컬렉션으로 다루기 위해 import
import java.util.List;

// === Target: 우리 시스템이 사용하는 통합 결제 인터페이스 ===
// Target: 클라이언트가 의존하는 표준 인터페이스
interface PaymentProcessor {
    // 결제 실행: orderId와 금액으로 통일
    boolean pay(String orderId, double amount);
    // 환불 실행
    boolean refund(String transactionId, double amount);
    // 사람이 읽을 수 있는 처리기 이름
    String getName();
}

// === Adaptee 1: 레거시 카드 결제 시스템 (다른 메서드 시그니처) ===
// Adaptee 1: 기존에 존재하는, 우리가 수정할 수 없는 레거시 시스템
class LegacyCardPayment {
    // 카드 토큰과 센트 단위 정수 금액을 받음 (시그니처가 Target과 다름)
    public int processCard(String cardToken, int amountInCents) {
        System.out.println("  [레거시카드] 결제 처리: " + amountInCents + "원");
        return 1001; // 트랜잭션 번호 반환
    }

    // 트랜잭션 번호로 취소
    public boolean cancelPayment(int transactionNumber) {
        System.out.println("  [레거시카드] 결제 취소: txn=" + transactionNumber);
        return true;
    }
}

// === Adaptee 2: 외부 페이팔 SDK (완전히 다른 API) ===
// Adaptee 2: 서드파티 SDK - email/USD 단위/문자열 트랜잭션ID 사용
class PayPalSDK {
    // 이메일과 USD 금액으로 인증 후 트랜잭션 ID 문자열 반환
    public String authorize(String email, double usdAmount) {
        System.out.println("  [PayPal] 인증 및 결제: $" + usdAmount);
        return "PP-" + System.currentTimeMillis();
    }

    // PayPal 트랜잭션 ID로 무효화
    public void voidTransaction(String paypalTxnId) {
        System.out.println("  [PayPal] 트랜잭션 무효화: " + paypalTxnId);
    }
}

// === Adapter 1: 레거시 카드 → PaymentProcessor ===
// Adapter 1: Adaptee를 위임 보유하고 Target 인터페이스로 변환 (객체 어댑터)
class LegacyCardAdapter implements PaymentProcessor {
    // Adaptee 인스턴스를 보유 (composition)
    private final LegacyCardPayment legacySystem;
    // 환불 시 사용할 마지막 트랜잭션 번호 캐시
    private int lastTransactionNumber;

    // 생성자: 레거시 시스템을 주입받음
    public LegacyCardAdapter(LegacyCardPayment legacySystem) {
        this.legacySystem = legacySystem;
    }

    @Override
    public boolean pay(String orderId, double amount) {
        // 인터페이스 변환: double → int (원 단위), orderId를 cardToken으로 매핑
        int amountInCents = (int) amount;
        // Adaptee 호출 후 결과를 Target 시그니처에 맞게 변환
        lastTransactionNumber = legacySystem.processCard(orderId, amountInCents);
        // 정수 트랜잭션 번호 > 0 이면 성공
        return lastTransactionNumber > 0;
    }

    @Override
    public boolean refund(String transactionId, double amount) {
        // 문자열 트랜잭션ID -> 정수로 파싱하여 Adaptee 호출
        return legacySystem.cancelPayment(Integer.parseInt(transactionId));
    }

    // Target에서 요구하는 이름 제공
    @Override
    public String getName() { return "레거시 카드 결제"; }
}

// === Adapter 2: PayPal → PaymentProcessor ===
// Adapter 2: PayPal SDK를 PaymentProcessor로 변환
class PayPalAdapter implements PaymentProcessor {
    // PayPal SDK 인스턴스 보유
    private final PayPalSDK paypal;
    // 통화 단위 변환 상수: KRW -> USD
    private static final double EXCHANGE_RATE = 0.00075; // KRW → USD

    // 생성자: PayPal SDK 주입
    public PayPalAdapter(PayPalSDK paypal) {
        this.paypal = paypal;
    }

    @Override
    public boolean pay(String orderId, double amount) {
        // KRW 금액을 USD로 변환하여 SDK에 전달
        double usdAmount = amount * EXCHANGE_RATE;
        // orderId를 email 자리에 매핑(데모 단순화)
        String txnId = paypal.authorize(orderId, usdAmount);
        // 트랜잭션 ID가 비어있지 않으면 성공으로 간주
        return txnId != null && !txnId.isEmpty();
    }

    @Override
    public boolean refund(String transactionId, double amount) {
        // PayPal SDK의 voidTransaction 호출로 변환
        paypal.voidTransaction(transactionId);
        return true;
    }

    @Override
    public String getName() { return "PayPal"; }
}

// 데모 클라이언트: Target 인터페이스만 알면 모든 결제 시스템 사용 가능
public class AdapterDemo {
    // 클라이언트 코드: PaymentProcessor 인터페이스만 알면 됨
    static void processOrder(PaymentProcessor processor, String orderId, double amount) {
        System.out.println("[" + processor.getName() + "] 주문 " + orderId + " 처리");
        // Target 메서드만 호출 - 내부 구현 차이는 어댑터가 흡수
        boolean success = processor.pay(orderId, amount);
        System.out.println("  결제 결과: " + (success ? "성공" : "실패"));
        System.out.println();
    }

    public static void main(String[] args) {
        // 서로 다른 시스템을 통합 인터페이스로 사용
        // 레거시와 PayPal을 같은 PaymentProcessor 타입으로 묶을 수 있음
        List<PaymentProcessor> processors = List.of(
            new LegacyCardAdapter(new LegacyCardPayment()),
            new PayPalAdapter(new PayPalSDK())
        );

        // 동일한 클라이언트 코드로 모두 처리
        for (PaymentProcessor processor : processors) {
            processOrder(processor, "ORD-001", 50000);
        }
    }
}
```

**실행 결과** — 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다).

**풀이 요점**

- 두 Adaptee 클래스는 한 줄도 고치지 않는다 — 고칠 것은 어댑터와 클라이언트뿐이다.
- 어댑터 메서드는 「인자 변환 → Adaptee 호출 → 결과 변환」의 세 단계로 읽으면 된다.
- 두 어댑터 모두 상속이 아니라 `final` 필드로 품는 객체 어댑터다.
- `processOrder` 는 어떤 어댑터가 들어오는지 모른다 — 그래서 목록에 어댑터를 더해도 그대로 돈다.
- `lastTransactionNumber` 는 저장만 되고 `refund` 에서 쓰이지 않는다 — 원본 그대로이며, 트랜잭션 번호가 클라이언트에 전달되지 않는 한계를 보여 준다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
