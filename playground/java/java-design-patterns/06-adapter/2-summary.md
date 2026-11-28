# java/java-design-patterns/06 — Adapter (어댑터) — 정리 (힌트)

> 출처 — study-site 항목 `java/adapter`(항목 데이터 `data/java/design-patterns.json`) · 정답 코드 study-practice `java/java-design-patterns/reference/adapter.java`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다).

## 한눈에 — 쉽게 말하면

**어댑터는 「해외여행용 전원 변환 플러그」다.**
한국 충전기(우리 코드)는 그대로 두고, 벽 콘센트(외부 시스템)도 그대로 둔다.
사이에 변환 플러그 하나만 끼우면 둘이 맞물린다.
Adapter 패턴도 똑같은 구조다.
클라이언트가 원하는 인터페이스와 이미 있는 클래스의 메서드 모양이 다를 때, 그 사이에 변환용 클래스를 하나 끼운다.

| 비유 | 실체 |
|---|---|
| 한국 충전기의 플러그 모양 | Target — 클라이언트가 의존하는 인터페이스(`PaymentProcessor`) |
| 해외 콘센트 | Adaptee — 이미 있고 고칠 수 없는 클래스(`LegacyCardPayment` · `PayPalSDK`) |
| 변환 플러그 | Adapter — 둘을 잇는 클래스(`LegacyCardAdapter` · `PayPalAdapter`) |
| 충전기를 꽂는 사람 | Client — Target 만 아는 코드(`processOrder`) |

```text
 Client ──pay()──▶ [ Adapter ] ──processCard()──▶ Adaptee
 (Target만 앎)      모양을 바꿔 줌                 (고치지 않음)
```

> **Adapter 패턴** — 호환되지 않는 인터페이스를 가진 클래스들을 함께 동작하도록 변환하는 디자인 패턴이다.\
> 예: 레거시 카드 결제 클래스를 새 `PaymentProcessor` 인터페이스로 감싸 쓴다.

## 이 주제가 답하려는 질문

1. 메서드 이름 · 매개변수 · 반환 타입이 다른 두 시스템을 클라이언트 코드 하나로 어떻게 다루나?
2. 고칠 수 없는 레거시 코드나 외부 SDK 를 어떻게 우리 인터페이스에 끼워 넣나?
3. 어댑터를 「상속」으로 만들 때와 「위임」으로 만들 때 무엇이 다르나?
4. 변환 과정에서 무엇이 바뀌고, 무엇이 사라질 수 있나?

## 동작 방식

### (1) Target 을 먼저 정한다

**언제 쓰나** — 여러 시스템을 하나의 모양으로 부르고 싶을 때 그 「하나의 모양」을 인터페이스로 못 박는다.

```text
interface PaymentProcessor
  ├─ boolean pay(String orderId, double amount)
  ├─ boolean refund(String transactionId, double amount)
  └─ String  getName()
          │
          ▼
Client(processOrder)는 이 세 메서드만 안다
```

- 클라이언트가 의존하는 표준이 `PaymentProcessor` 하나로 정해진다.
- 결제는 「주문 번호 + 금액(double)」으로, 환불은 「트랜잭션 ID(String) + 금액」으로 통일된다.
- 클라이언트는 그 뒤에 어떤 시스템이 있는지 모른다.

> **Target** — 클라이언트가 원하는(의존하는) 인터페이스다.\
> 예: `PaymentProcessor`.

### (2) Adaptee 는 모양이 다르다 — 그리고 고치지 않는다

**언제 쓰나** — 이미 운영 중인 레거시 코드나 소스를 고칠 수 없는 서드파티 SDK 를 통합할 때다.

```text
Target 이 원하는 것           LegacyCardPayment 가 가진 것
pay(String, double)→boolean   processCard(String cardToken, int amountInCents)→int
refund(String, double)→bool   cancelPayment(int transactionNumber)→boolean

                              PayPalSDK 가 가진 것
                              authorize(String email, double usdAmount)→String
                              voidTransaction(String paypalTxnId)→void
```

- 메서드 이름이 다르다(`pay` 대 `processCard` 대 `authorize`).
- 금액 타입이 다르다(`double` 대 `int`).
- 통화가 다르다(원 대 달러).
- 결과의 모양이 다르다(`boolean` 대 `int` 트랜잭션 번호 대 `String` 트랜잭션 ID 대 `void`).
- 어댑터 패턴의 핵심은 이 클래스들을 **수정하지 않는** 것이다.

> **Adaptee** — 변환당하는 쪽, 이미 존재하는 클래스다.\
> 예: `LegacyCardPayment`, `PayPalSDK`.

### (3) Adapter 가 Target 을 구현하고 Adaptee 를 품는다 (객체 어댑터)

**언제 쓰나** — 이 예제처럼 Adaptee 인스턴스를 필드로 들고 호출을 넘기는(위임) 방식이 기본이다.

```text
new LegacyCardAdapter(new LegacyCardPayment())
        │ 생성자로 Adaptee 를 받아 final 필드에 저장
        ▼
LegacyCardAdapter implements PaymentProcessor
   └─ private final LegacyCardPayment legacySystem   ← 위임 대상
```

- `implements PaymentProcessor` 로 Target 의 모양을 갖춘다.
- Adaptee 는 상속하지 않고 필드로 갖는다(composition).
- Adaptee 를 생성자로 받으므로 바깥에서 무엇을 넣을지 정할 수 있다(생성자 주입).

> **객체 어댑터** — Adaptee 를 필드로 품고 호출을 위임하는 어댑터다.\
> 예: `LegacyCardAdapter` 가 `legacySystem.processCard(...)` 를 부른다.

> **위임(delegation)** — 받은 요청을 직접 처리하지 않고 다른 객체의 메서드에 넘기는 것이다.\
> 예: `pay` 안에서 `legacySystem.processCard` 를 부른다.

### (4) 메서드 안에서 무엇을 변환하나

**언제 쓰나** — Target 메서드 하나가 불릴 때마다 인자를 Adaptee 모양으로 바꾸고, 결과를 Target 모양으로 되돌린다.

```text
LegacyCardAdapter.pay("ORD-001", 50000.0)
  ├─ (int) amount              → 50000        double → int
  ├─ orderId 를 cardToken 자리에
  ├─ processCard("ORD-001", 50000) → 1001     Adaptee 호출
  └─ 1001 > 0                  → true         int → boolean

PayPalAdapter.pay("ORD-001", 50000.0)
  ├─ 50000.0 * 0.00075         → 약 37.5      원 → 달러
  ├─ orderId 를 email 자리에(데모 단순화)
  ├─ authorize(...)            → "PP-<밀리초>"
  └─ txnId != null && !isEmpty → true         String → boolean
```

- `(int) amount` 는 소수점 아래를 버린다(반올림하지 않는다).
- 레거시는 정수 트랜잭션 번호가 0 보다 크면 성공으로 본다.
- PayPal 은 `EXCHANGE_RATE = 0.00075` 를 곱해 달러로 바꾼다.
- PayPal 의 트랜잭션 ID 는 `"PP-" + System.currentTimeMillis()` 라서 부를 때마다 값이 다르다.
- 환불도 같은 식이다: 레거시는 `Integer.parseInt(transactionId)` 로 문자열을 정수로 바꿔 `cancelPayment` 에 넘기고, PayPal 은 `voidTransaction` 을 부른 뒤 무조건 `true` 를 돌려준다.

### (5) 클라이언트는 Target 만 부른다

**언제 쓰나** — 서로 다른 시스템을 같은 목록에 담아 같은 코드로 처리할 때다.

```text
List<PaymentProcessor> processors = List.of(레거시어댑터, 페이팔어댑터)
            │
            ▼ for 문
processOrder(processor, "ORD-001", 50000)
  ├─ "[" + getName() + "] 주문 ORD-001 처리" 를 찍는다
  ├─ processor.pay(...)      ← 어느 어댑터인지 모르고 부른다
  └─ "  결제 결과: 성공/실패" 와 빈 줄을 찍는다
```

- 두 어댑터 모두 `PaymentProcessor` 타입이라 한 `List` 에 담긴다.
- `processOrder` 는 `PaymentProcessor` 의 메서드만 부른다 — 내부 차이는 어댑터가 흡수한다.
- 새 결제 시스템이 생겨도 어댑터 하나만 더 만들면 되고 `processOrder` 는 그대로다.
- `List.of` 로 만든 목록은 넣은 차례대로 돈다 — 레거시가 먼저, PayPal 이 다음이다.

> **Client** — Target 인터페이스만 알고 쓰는 코드다.\
> 예: `processOrder`.

### (6) 클래스 어댑터 — 상속으로 만드는 다른 길

**언제 쓰나** — Adaptee 를 상속해 그 메서드를 바로 물려받는 방식이다.
원본 팁은 객체 어댑터(위임)가 클래스 어댑터(상속)보다 유연하다고 말한다.

```text
class LegacyCardClassAdapter extends LegacyCardPayment implements PaymentProcessor
        │ extends — Adaptee 하나에 묶인다(Java 클래스는 하나만 상속)
        ▼
pay(...) 안에서 this.processCard(...) 를 바로 부른다
```

- 상속은 컴파일 시점에 Adaptee 클래스 하나로 고정된다.
- Java 는 클래스를 하나만 상속할 수 있어서 Adaptee 둘을 한 어댑터에 묶을 수 없다.
- 위임은 필드에 무엇을 넣느냐로 바꿀 수 있다 — Adaptee 의 하위 클래스 인스턴스도 넣을 수 있다.
- 상속하면 Adaptee 의 공개 메서드(`processCard` 등)가 어댑터 바깥으로도 그대로 드러난다.

> **클래스 어댑터** — Adaptee 를 상속하고 Target 을 구현해서 만든 어댑터다.\
> 예: `extends LegacyCardPayment implements PaymentProcessor`.

## 문법 — 형태와 규칙

```java
interface Target { String request(); }                 // 클라이언트가 원하는 모양

class Adaptee { String specificRequest() { return "old"; } }  // 고치지 않는 기존 클래스

class ObjectAdapter implements Target {                 // 객체 어댑터
    private final Adaptee adaptee;                      // 위임 대상을 품는다
    ObjectAdapter(Adaptee adaptee) { this.adaptee = adaptee; }
    public String request() { return adaptee.specificRequest().toUpperCase(); }
}

class ClassAdapter extends Adaptee implements Target {  // 클래스 어댑터
    public String request() { return specificRequest().toUpperCase(); }
}
```

- 어댑터는 Target 을 `implements` 한다 — 그래야 클라이언트가 Target 타입으로 받을 수 있다.
- 객체 어댑터는 Adaptee 를 `private final` 필드로 두고 생성자로 받는다.
- 클래스 어댑터는 Adaptee 를 `extends` 한다 — 클래스는 하나만 상속할 수 있다.
- Target 메서드 몸체는 「인자 변환 → Adaptee 호출 → 결과 변환」 세 단계다.
- Adaptee 의 소스는 건드리지 않는다.
- Java 표준 라이브러리의 `Arrays.asList()` 는 배열을 `List` 인터페이스로 변환하는 어댑터다 — 배열이 Adaptee, `List` 가 Target 이다.

## 어디서 틀리나

### 1. 기존 코드를 고치기 시작하면 어댑터가 아니다

어댑터의 핵심은 기존 코드를 **수정하지 않고** 새 인터페이스에 맞추는 것이다.
`LegacyCardPayment` 에 `pay` 메서드를 추가하는 순간 그것은 통합이 아니라 개조다.
레거시나 서드파티 SDK 는 고칠 권한이 없거나, 고치면 다른 사용처가 깨질 수 있다.

### 2. 상속(클래스 어댑터)을 먼저 고르는 것

객체 어댑터(위임)가 클래스 어댑터(상속)보다 유연하다.
상속은 Adaptee 하나에 고정되고, Adaptee 의 메서드가 어댑터 바깥으로 새어 나간다.
특별한 까닭이 없으면 위임을 고른다.

### 3. 변수 이름과 실제 단위가 어긋난다

원본은 매개변수를 `amountInCents`(센트 단위)라고 부르고 주석도 「센트 단위 정수 금액」이라 하지만, 출력은 `"원"` 을 붙이고 어댑터 주석은 「원 단위」라고 한다.
원본의 주장(센트) → 의심스러운 까닭: 같은 값을 출력에서는 원으로 다루므로 이름과 쓰임이 맞지 않는다.
단위 변환이 어댑터의 일인데 단위 이름이 어긋나면 변환이 맞는지 검증할 수 없다.

### 4. 타입 변환이 값을 잃는다

`(int) amount` 는 소수점 아래를 버린다 — `50000.9` 는 `50000` 이 된다.
`Integer.parseInt(transactionId)` 는 숫자가 아닌 문자열(예: `"PP-..."`)을 받으면 `NumberFormatException` 을 던진다.
어댑터는 변환이 깨질 수 있는 지점을 직접 처리해야 한다.

### 5. Target 이 담지 못하는 정보는 사라진다

`pay` 가 `boolean` 만 돌려주므로 Adaptee 가 만든 트랜잭션 번호(`1001`, `"PP-..."`)를 클라이언트가 받을 길이 없다.
그런데 `refund` 는 그 트랜잭션 ID 를 요구한다.
`LegacyCardAdapter` 는 `lastTransactionNumber` 를 「환불 시 사용할 캐시」로 저장하지만, `refund` 는 그 필드를 쓰지 않고 넘어온 문자열을 파싱한다.
두 어댑터 모두 `refund` 의 `amount` 를 무시한다 — 부분 환불은 표현되지 않는다.
PayPal 어댑터의 `refund` 는 `voidTransaction` 이 `void` 라서 결과를 모르고 무조건 `true` 를 돌려준다.

### 6. 의미가 다른 자리에 값을 끼워 넣는다

`PayPalAdapter` 는 `orderId` 를 `email` 자리에 넣는다(주석이 「데모 단순화」라고 밝힌다).
타입이 둘 다 `String` 이라 컴파일은 되지만 뜻은 맞지 않는다.

### 7. 어댑터가 많아지면 복잡해진다

장점은 기존 코드 수정 없이 통합하는 것이고, 단점은 어댑터 수가 늘수록 복잡도가 오른다는 것이다.
시스템마다 어댑터가 하나씩 생기므로 변환 규칙이 여러 곳에 흩어진다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `(int) amount` 가 소수점 아래를 버린다 | Java 언어 명세(double → int 축소 변환) |
| `List.of` 로 만든 목록을 넣은 차례대로 돈다 | `List` 인터페이스 계약(표준 API) |
| `Integer.parseInt` 가 숫자가 아닌 문자열에 `NumberFormatException` 을 던진다 | 표준 API 문서 |
| 클래스는 하나만 상속할 수 있다 | Java 언어 명세 |
| `"PP-" + currentTimeMillis()` 가 부를 때마다 다르다 | 보장 없음 — 같은 밀리초에 두 번 부르면 같을 수 있다(원본에 근거 없음 — 추론) |
| `50000 * 0.00075` 를 문자열로 찍은 모양 | `Double.toString` 규칙에 따르지만 부동소수점 오차로 정확히 `37.5` 로 찍히는지는 (확인 필요) |
| 환율 `0.00075` | 예제의 상수일 뿐 실제 환율이 아니다 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 고칠 수 없는 레거시 · 서드파티를 우리 인터페이스에 맞출 때 | 객체 어댑터 | Adaptee 소스 수정 |
| 같은 역할의 시스템이 여럿이고 클라이언트를 하나로 두고 싶을 때 | Target 인터페이스 + 시스템마다 어댑터 | 클라이언트 안의 `if` 분기 |
| Adaptee 하위 클래스까지 갈아 끼우고 싶을 때 | 위임(필드로 품기) | 상속(클래스 어댑터) |
| 배열을 `List` 로 다루고 싶을 때 | `Arrays.asList()` | 손으로 복사하는 루프 |
| 인터페이스가 이미 맞을 때 | 그대로 쓴다 | 쓸데없는 어댑터 층 |

## 핵심 문장

1. **어댑터는 Target 을 구현하고 Adaptee 를 감싸서 모양을 바꾼다** — Adaptee 는 고치지 않는다.
2. **클라이언트는 Target 만 안다** — 새 시스템이 와도 어댑터만 추가하면 클라이언트는 그대로다.
3. **변환은 인자 → 호출 → 결과의 세 단계다** — 이름 · 타입 · 단위 · 반환 모양을 바꾼다.
4. **객체 어댑터(위임)가 클래스 어댑터(상속)보다 유연하다.**
5. **Target 이 담지 못하는 정보는 변환 중에 사라진다** — 반환값 · 단위 · 실패 신호를 챙겨야 한다.

## 관련 자료

- `decorator` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `facade` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `proxy` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `bridge` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/java/design-patterns.json` 의 `adapter`

## 용어 풀이

- **Adapter 패턴** — 호환되지 않는 인터페이스를 맞물리게 변환하는 디자인 패턴.
- **Target** — 클라이언트가 의존하는 인터페이스.
- **Adaptee** — 변환당하는, 이미 있는 클래스.
- **Adapter** — Target 을 구현하고 Adaptee 를 호출해 둘을 잇는 클래스.
- **Client** — Target 만 알고 쓰는 코드.
- **객체 어댑터** — Adaptee 를 필드로 품고 위임하는 어댑터.
- **클래스 어댑터** — Adaptee 를 상속해 만든 어댑터.
- **위임(delegation)** — 요청을 다른 객체의 메서드에 넘기는 것.
- **composition(구성)** — 다른 객체를 필드로 가져 기능을 얻는 것.
- **래퍼(wrapper)** — 다른 객체를 감싸 다른 모양으로 내보이는 객체, 어댑터의 다른 이름으로도 쓴다.
- **레거시 코드** — 이미 운영 중이라 고치기 어려운 옛 코드.
- **시그니처** — 메서드 이름과 매개변수 타입의 조합.
- **생성자 주입** — 필요한 객체를 생성자 인자로 받는 것.

## 더 들어가면

- `Arrays.asList()` 가 돌려주는 목록은 원래 배열을 그대로 바라보는 고정 크기 목록이라 `add` · `remove` 를 부르면 `UnsupportedOperationException` 이 난다(확인 필요).
- 같은 이유로 그 목록의 `set` 은 원래 배열의 값도 바꾼다(확인 필요).
- 표준 라이브러리의 `InputStreamReader` 는 바이트 스트림을 문자 스트림으로 바꾸는 어댑터의 예로 자주 든다(확인 필요).
- 비슷한 「감싸기」 패턴으로 Decorator(같은 인터페이스에 기능 추가) · Facade(여러 클래스를 단순한 창구로) · Proxy(같은 인터페이스로 접근 제어)가 있다 — Adapter 는 「인터페이스를 바꾼다」는 점이 다르다(확인 필요).
- 돈을 `double` 로 다루면 오차가 생기므로 실무에서는 `BigDecimal` 이나 최소 단위 정수(`long`)를 쓰는 경우가 많다(확인 필요).
