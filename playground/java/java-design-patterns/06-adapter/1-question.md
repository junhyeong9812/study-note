# java/java-design-patterns/06 — Adapter (어댑터) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 소수점이 있는 금액을 레거시 어댑터에 넘기면 (예측)

```java
// 질문용 발췌
PaymentProcessor p = new LegacyCardAdapter(new LegacyCardPayment());
boolean ok = p.pay("ORD-002", 50000.9);
```

- 콘솔에 찍히는 한 줄은 무엇인가?
- `ok` 의 값은 무엇인가?

### 2. 데모의 `main` 을 끝까지 돌리면 (예측)

```java
// 질문용 발췌
List<PaymentProcessor> processors = List.of(
    new LegacyCardAdapter(new LegacyCardPayment()),
    new PayPalAdapter(new PayPalSDK())
);
for (PaymentProcessor processor : processors) {
    processOrder(processor, "ORD-001", 50000);
}
```

- 콘솔에 찍히는 줄들을 차례대로 적으면 어떻게 되나?

### 3. PayPal 의 트랜잭션 ID 를 레거시 어댑터로 환불하면 (예측)

```java
// 질문용 발췌
PaymentProcessor p = new LegacyCardAdapter(new LegacyCardPayment());
p.refund("PP-1700000000000", 50000);
```

- 이 호출은 어떻게 끝나나?

### 4. `processOrder` 는 결제 시스템이 늘어도 고칠 일이 없다 (왜)

- 새 결제 시스템을 붙일 때 `processOrder` 를 건드리지 않아도 되는 까닭은 무엇인가?

### 5. 객체 어댑터가 클래스 어댑터보다 유연하다 (왜)

- 위임으로 만든 어댑터가 상속으로 만든 어댑터보다 유연한 까닭은 무엇인가?

### 6. 어댑터를 거치면 사라지는 정보 (경계)

- 이 예제의 `PaymentProcessor` 로는 표현할 수 없어 변환 중에 버려지는 정보는 무엇인가?

### 7. 어댑터를 쓰지 않아도 되는 때와 지나치게 쓰는 때 (경계)

- 어댑터 층을 두는 것이 이득이 아닌 경우는 어떤 경우인가?

### 8. `Arrays.asList()` 는 어댑터다 (연결)

- `Arrays.asList()` 에서 Target 과 Adaptee 는 각각 무엇인가?

### 9. 어댑터의 생성자와 인터페이스 다형성 (연결)

- 서로 다른 두 어댑터가 한 `List<PaymentProcessor>` 에 담기고, Adaptee 를 생성자로 받는 구조는 어떤 객체 지향 개념과 이어지나?

## 실습

### 실습 1. 두 결제 시스템을 하나의 결제 인터페이스로 통합하기

**만들 것** — 시그니처가 다른 레거시 카드 결제 클래스와 PayPal SDK 를 고치지 않고, 각각 어댑터로 감싸 하나의 `PaymentProcessor` 인터페이스로 결제하는 데모를 만든다.

**요구 조건**

1단계 — Target

1. `PaymentProcessor` 인터페이스에 `pay(String orderId, double amount)` · `refund(String transactionId, double amount)`(둘 다 `boolean` 반환) · `getName()`(`String` 반환) 세 메서드를 선언한다.

2단계 — 레거시 카드 어댑터

2. `LegacyCardAdapter` 는 `PaymentProcessor` 를 구현하고, `LegacyCardPayment` 를 상속하지 않고 `final` 필드로 품는다.
3. Adaptee 는 생성자로 받는다.
4. `pay` 는 금액을 `int` 로 바꾸고 `orderId` 를 카드 토큰 자리에 넣어 `processCard` 를 부른다.
5. `processCard` 가 돌려준 트랜잭션 번호를 필드 `lastTransactionNumber` 에 저장하고, 그 값이 0 보다 크면 `true` 를 돌려준다.
6. `refund` 는 문자열 트랜잭션 ID 를 정수로 파싱해 `cancelPayment` 에 넘기고 그 결과를 돌려준다.

3단계 — PayPal 어댑터

7. `PayPalAdapter` 는 `PaymentProcessor` 를 구현하고 `PayPalSDK` 를 `final` 필드로 품으며 생성자로 받는다.
8. `pay` 는 금액에 환율 상수를 곱해 달러로 바꾸고, `orderId` 를 이메일 자리에 넣어 `authorize` 를 부른다.
9. `authorize` 가 돌려준 트랜잭션 ID 가 `null` 이 아니고 비어 있지 않으면 `true` 를 돌려준다.
10. `refund` 는 `voidTransaction` 을 부른 뒤 `true` 를 돌려준다.

4단계 — 클라이언트

11. `processOrder(PaymentProcessor, String, double)` 는 처리기 이름과 주문 번호를 찍고, `pay` 를 부른 뒤 성공/실패와 빈 줄을 찍는다 — `PaymentProcessor` 의 메서드만 쓴다.
12. `main` 은 두 어댑터를 `List.of` 로 한 목록에 담고, 각각에 대해 `processOrder(processor, "ORD-001", 50000)` 을 부른다.

**시작 코드**

```java
import java.util.List;

interface PaymentProcessor {
    // TODO: pay, refund, getName 세 메서드를 선언한다
}

// Adaptee 1 — 고치지 않는다
class LegacyCardPayment {
    public int processCard(String cardToken, int amountInCents) {
        System.out.println("  [레거시카드] 결제 처리: " + amountInCents + "원");
        return 1001;
    }
    public boolean cancelPayment(int transactionNumber) {
        System.out.println("  [레거시카드] 결제 취소: txn=" + transactionNumber);
        return true;
    }
}

// Adaptee 2 — 고치지 않는다
class PayPalSDK {
    public String authorize(String email, double usdAmount) {
        System.out.println("  [PayPal] 인증 및 결제: $" + usdAmount);
        return "PP-" + System.currentTimeMillis();
    }
    public void voidTransaction(String paypalTxnId) {
        System.out.println("  [PayPal] 트랜잭션 무효화: " + paypalTxnId);
    }
}

class LegacyCardAdapter /* TODO: Target 을 구현한다 */ {
    // TODO: Adaptee 필드와 lastTransactionNumber 필드
    // TODO: 생성자

    // TODO: pay — 금액 변환 → processCard 호출 → 결과를 boolean 으로
    // TODO: refund — 문자열 ID 파싱 → cancelPayment 호출

    public String getName() { return "레거시 카드 결제"; }
}

class PayPalAdapter /* TODO: Target 을 구현한다 */ {
    private static final double EXCHANGE_RATE = 0.00075; // KRW → USD
    // TODO: Adaptee 필드와 생성자

    // TODO: pay — 달러로 변환 → authorize 호출 → 결과를 boolean 으로
    // TODO: refund — voidTransaction 호출

    public String getName() { return "PayPal"; }
}

public class AdapterDemo {
    static void processOrder(PaymentProcessor processor, String orderId, double amount) {
        // TODO: "[이름] 주문 <orderId> 처리" 를 찍는다
        // TODO: pay 를 부르고 "  결제 결과: 성공/실패" 를 찍은 뒤 빈 줄을 찍는다
    }

    public static void main(String[] args) {
        // TODO: 두 어댑터를 List.of 로 담고 각각 processOrder(processor, "ORD-001", 50000)
    }
}
```

**확인 방법** — `javac AdapterDemo.java && java AdapterDemo` 로 돌려, 레거시 카드와 PayPal 이 차례로 「주문 ORD-001 처리 → 각 시스템의 결제 줄 → 결제 결과: 성공」을 찍는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
