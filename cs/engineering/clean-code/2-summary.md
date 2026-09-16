# engineering/clean-code — 정리 (힌트)

> 복습은 [1-question.md](1-question.md)에서 시작하고, 막힐 때만 이 파일을 힌트로 연다.\
> 원고 출처: `jun-bank/docs/study/02-clean-code/README.md` (따라 친 원본 노트) · 이관일 2026-09-16.\
> 본문 5속성 절(C·L·E·A·N)과 「긴장 관계」는 **원고**를 고쳐 쓴 것이다(문체·순서 유지).\
> 「한눈에」·「전체 흐름」의 그림과 사다리 도식은 **Claude가 원고 이해를 돕기 위해 새로 그린 것**이며, 원고에 없던 지식은 맨 끝 `[Claude 추가]`에만 둔다.

**CLEAN** = **C**ohesive · **L**oosely Coupled · **E**ncapsulated · **A**ssertive · **N**onredundant.\
좋은 코드가 가져야 할 다섯 속성을 묶은 두문자어다.

---

## 한눈에 — 쉽게 말하면

잘 정리된 **공구함 한 칸**을 떠올리면 된다. *(Claude 보강 — 원고에 없는 비유)*

```text
잘 정리된 공구함 한 칸
+-------------------------------+
| [렌치 서랍] 렌치만 들어 있다     |  ← C 한 서랍은 한 목적
| 서랍끼리 안 걸린다              |  ← L 하나 빼도 옆 서랍 안 흔들림
| 손잡이만 잡으면 쓴다            |  ← E 내부 스프링 구조는 몰라도 됨
| 렌치가 스스로 조인다            |  ← A 내가 계산 말고, 시키면 한다
| 같은 렌치가 딴 서랍에 없다       |  ← N 한 물건은 한 자리에만
+-------------------------------+
```

**코드도 똑같은 구조다.** 한 클래스는 한 목적을 향하고(C), 하나를 바꿔도 옆이 안 딸려 바뀌고(L), 내부를 어떻게 저장하는지 밖에서 몰라도 되고(E), 데이터를 꺼내가서 남이 판단하는 대신 객체가 스스로 판단하고(A), 같은 지식이 여기저기 복사돼 있지 않다(N).

쉽게 말하면 이렇다.\
**SOLID가 "어떻게 설계할 것인가"라는 수단이라면, CLEAN은 "그래서 결과물이 어떤 성질을 가져야 하는가"라는 상태다.** SOLID는 만드는 법, CLEAN은 다 만든 물건의 품질 검사표에 가깝다.

---

## 문제 — 이 개념이 답하려는 질문

이 주제에는 풀어야 할 코드 과제가 없다(개념 정리다). 대신 다섯 속성 각각이 하나의 질문에 답한다.

```text
C 응집성    "이 덩어리 안의 것들이 하나의 목적을 향해 함께 일하는가?"
L 느슨한결합 "A를 바꿀 때 B까지 함께 바꿔야 하는 정도가 낮은가?"
E 캡슐화    "어떻게 저장돼 있는지를 밖에서 몰라도 되게 감췄는가?"
A 단정적    "객체가 자기 데이터를 스스로 판단하는가, 남이 꺼내가 판단하는가?"
N 비중복    "같은 '지식'이 시스템 안에 한 번만 표현돼 있는가?"
```

아래 서머리는 이 다섯 질문을 하나씩 분석·정리한 것이다.

---

## 전체 흐름

다섯 속성은 따로 노는 규칙이 아니라, 마지막에 서로 **당긴다**(긴장 관계).

```text
SOLID = 어떻게 설계할까 (수단)
   │
   ▼
CLEAN = 그 결과물이 가져야 할 성질 (상태)
   │
   ├─ C 응집성     한 덩어리가 한 목적을 향하는가
   ├─ L 느슨한 결합  바꿀 때 딸려 바뀌는 게 적은가
   ├─ E 캡슐화      내부 표현을 감추고 의미 있는 조작만 여는가
   ├─ A 단정적      객체가 스스로 판단하는가 (묻지 말고 시켜라)
   └─ N 비중복      같은 '지식'이 한 곳에만 있는가
   │
   ▼
이 다섯은 서로 충돌한다 (N↔L, C↔N, E↔편의성, A↔계층분리)
   → 「5속성 간의 긴장 관계」 절에서 판정 기준을 본다
```

---

## C — 응집성 (Cohesive)

> 출처: `jun-bank/docs/study/02-clean-code/README.md` — C 절

### 정의

> **한 덩어리 안의 요소들이 하나의 목적을 향해 함께 작동하는 정도.**

높은 응집도란 "이 클래스에서 아무거나 하나 골라도 다른 것들과 명백히 관련 있다"는 상태다.

> **응집도(cohesion)** — 한 덩어리 안의 요소들이 서로 얼마나 관련 있는가. 높을수록 좋다.\
> 예: 카드번호 클래스 안에 "검증·마스킹·앞 6자리 추출"만 있으면, 셋 다 카드번호라는 한 가지를 다루므로 응집도가 높다.

### 응집도의 등급 — 아래로 갈수록 좋다

전통적으로 7단계로 분류한다. 사다리 아래쪽(기능적)이 목표다.

```text
낮음 (나쁨)
 │  우연적    아무 관련 없이 그냥 모임          예) CommonUtils, Helper
 │  논리적    비슷한 범주라 모음(협력 없음)      예) 온갖 입력 검증을 한 클래스에
 │  시간적    같은 시점에 실행돼서 모음          예) initialize() 안에 온갖 초기화
 │  절차적    정해진 순서로 실행돼서 모음
 │  통신적    같은 데이터를 다뤄서 모음          예) 같은 테이블을 읽고 쓰는 메서드들
 │  순차적    앞의 출력이 뒤의 입력이 됨
 ▼  기능적 ★  하나의 잘 정의된 작업만 수행       ← 목표
높음 (좋음)
```

### 나쁜 예 — 우연적 응집

```java
public class CommonUtils {
    public static String formatDate(LocalDate date) { ... }
    public static boolean isValidEmail(String email) { ... }
    public static Money calculateFee(Money amount) { ... }
    public static String maskCardNumber(String pan) { ... }
    public static byte[] compress(byte[] data) { ... }
}
```

이 다섯은 **서로 아무 관계가 없다.** "공통이라서" 모였을 뿐이다.\
이런 클래스는 시간이 지나면 무한히 커지고, 모든 코드가 여기에 의존하게 되어 **결합의 허브**가 된다.

### 좋은 예 — 기능적 응집

```java
// 카드번호에 관한 모든 것이 한 곳에, 그리고 그것만
public record CardNumber(String value) {

    private static final Pattern PATTERN = Pattern.compile("\\d{16}");

    public CardNumber {
        if (value == null || !PATTERN.matcher(value).matches()) {
            throw CardException.invalidCardNumber(value);
        }
    }

    /** 화면 표시용 마스킹: 1234-****-****-5678 */
    public String masked() {
        return value.substring(0, 4) + "-****-****-" + value.substring(12);
    }

    /** 카드사 식별을 위한 앞 6자리 (BIN) */
    public String bin() {
        return value.substring(0, 6);
    }
}
```

### 감지 방법

- **클래스 이름으로 설명해 보기**: "이 클래스는 ○○을 한다"를 **접속사 없이** 말할 수 있는가?
- **필드 사용률 보기**: 메서드 A는 필드 1·2만, 메서드 B는 필드 3·4만 쓴다면 → **두 클래스로 나눌 신호**.
- **테스트 준비 코드 보기**: 한 메서드를 테스트하려는데 관계없는 것까지 준비해야 한다면 응집도가 낮다.

### 현장에서 만나는 상황

한 서비스 안에 성격이 다른 두 도메인이 함께 사는 경우가 흔하다(예: "카드 발급·관리"와 "결제"가 한 서비스에).\
점검 질문은 하나다 — **이 둘은 함께 변하는가?** 카드 발급 규칙이 바뀔 때 결제 로직도 바뀌는가.\
아니라면 응집도가 낮은 것이고, 그게 곧 **서비스를 나눌 근거**가 된다.

---

## L — 느슨한 결합 (Loosely Coupled)

> 출처: `jun-bank/docs/study/02-clean-code/README.md` — L 절

### 정의

> **A를 바꿀 때 B를 함께 바꿔야 하는 정도가 낮은 상태.**

결합 자체를 없앨 수는 없다. 협력하려면 어느 정도는 알아야 한다.\
목표는 **"얼마나 아는가"를 최소화**하는 것이다.

> **결합도(coupling)** — A를 바꿀 때 B도 바꿔야 하는 정도. 낮을수록 좋다.\
> 예: 수수료 계산 함수가 주문 전체를 받으면 주문 구조가 바뀔 때 같이 깨지지만, 금액·카드종류만 받으면 주문이 바뀌어도 무사하다.

### 결합의 등급 — 아래로 갈수록 좋다

```text
나쁨
 │  내용 결합    다른 모듈의 내부를 직접 건드림      금지
 │  공통 결합    전역 변수를 공유                    금지
 │  외부 결합    외부 포맷·프로토콜을 공유           최소화
 │  제어 결합    플래그를 넘겨 상대의 동작을 지시     피할 것
 │  스탬프 결합  필요 이상의 큰 구조체를 넘김        줄일 것
 ▼  데이터 결합 ★ 필요한 값만 인자로 넘김           ← 목표
좋음
```

### 나쁜 예 — 제어 결합

```java
// 호출자가 상대의 내부 동작을 지시한다
public void processPayment(Payment payment, boolean isRefund, boolean skipValidation) {
    if (!skipValidation) { validate(payment); }
    if (isRefund) {
        reverseLedger(payment);
    } else {
        postLedger(payment);
    }
}

// 호출부: 이게 무슨 뜻인지 읽을 수 없다
processPayment(payment, true, false);
```

**플래그 인자(boolean parameter)** 는 "이 메서드는 사실 두 가지 일을 한다"는 자백이다.

### 좋은 예 — 동작마다 이름을 준다

```java
public void postPayment(Payment payment) {
    validate(payment);
    postLedger(payment);
}

public void refundPayment(Payment payment) {
    validate(payment);
    reverseLedger(payment);
}

// 호출부가 스스로 설명된다
refundPayment(payment);
```

### 나쁜 예 — 스탬프 결합

```java
// 수수료 계산에 필요한 건 금액과 카드 종류뿐인데 주문 전체를 받는다
public Money calculateFee(Order order) {
    return order.getPayment().getAmount().multiply(rateOf(order.getCard().getType()));
}
```

`Order`의 구조가 바뀌면 이 메서드가 깨진다. 실제로 필요한 것은 두 개뿐인데.

```java
// 좋은 예 — 데이터 결합
public Money calculateFee(Money amount, CardType cardType) {
    return amount.multiply(rateOf(cardType));
}
```

### 결합을 줄이려다 오히려 복잡해지는 지점

**모든 결합을 없애려 하면 안 된다.** 흔한 과잉은 이렇다.

- 두 클래스 사이에 **이벤트 버스를 넣어** 직접 호출을 없앴는데, 이제 흐름을 따라갈 수 없다.
- **인터페이스를 남발**해서 구현체가 하나뿐인 인터페이스가 수십 개 생겼다.
- 서비스를 잘게 쪼개서 **네트워크 홉이 늘고** 디버깅이 불가능해졌다.

> 판단 기준: **결합을 줄인 대가로 무엇을 잃었는가?** 흐름의 가시성을 잃었다면 대개 손해다.

### 현장에서 만나는 상황

한 서비스가 다른 서비스를 **동기 호출**(예: HTTP/Feign)로 부르는 구조가 흔하다.\
이건 **시간적 결합(temporal coupling)** 이다 — 상대가 죽으면 이쪽 기능도 멈춘다(예: 인증 서버가 죽으면 회원가입이 안 된다).\
이벤트로 바꾸면 결합은 줄지만 **결과적 일관성**을 감수해야 한다.\
**무엇을 잃고 무엇을 얻는지**가 이 판단의 핵심이다.

> **결과적 일관성(eventual consistency)** — 지금 당장은 두 쪽 데이터가 다를 수 있어도, 시간이 지나면 결국 같아지는 것.\
> 예: 이벤트로 "가입됨"을 알린 뒤 인증 서버가 조금 늦게 반영하면, 그 사이 잠깐은 불일치 상태다.

---

## E — 캡슐화 (Encapsulated)

> 출처: `jun-bank/docs/study/02-clean-code/README.md` — E 절

### 정의

> **내부 표현을 감추고, 외부에는 의미 있는 조작만 노출하는 것.**

단순히 필드를 `private`으로 하는 게 아니다.\
**"어떻게 저장되어 있는가"를 밖에서 몰라도 되게 만드는 것**이 핵심이다.

### getter/setter를 열면 캡슐화가 깨지는가

**setter는 대체로 깨뜨린다. getter는 경우에 따라 다르다.**

setter가 위험한 이유: 객체가 **불변식을 지킬 기회를 잃는다.**

> **불변식(invariant)** — 객체가 살아 있는 동안 항상 참이어야 하는 조건.\
> 예: "가용잔액을 넘겨 점유할 수 없다", "계좌 잔액은 음수가 아니다".

```java
// 나쁜 예 — 캡슐화 없음
public class Account {
    private Money balance;
    public Money getBalance() { return balance; }
    public void setBalance(Money balance) { this.balance = balance; }
}

// 호출부가 규칙을 직접 구현한다 — 여러 곳에 흩어지고, 하나만 빠뜨려도 데이터가 깨진다
Money newBalance = account.getBalance().minus(amount);
if (newBalance.isNegative()) throw new InsufficientBalanceException();
account.setBalance(newBalance);
```

```java
// 좋은 예 — 규칙이 객체 안에 있다
public class Account {
    private Money balance;
    private Money holdAmount;   // 승인으로 점유된 금액

    /** 가용잔액 = 계좌잔액 − 홀딩 */
    public Money availableBalance() {
        return balance.minus(holdAmount);
    }

    /** 결제 승인을 위해 금액을 점유한다 */
    public void hold(Money amount) {
        if (amount.isGreaterThan(availableBalance())) {
            throw AccountException.insufficientAvailableBalance(availableBalance(), amount);
        }
        this.holdAmount = this.holdAmount.plus(amount);
    }

    /** 홀딩 해제 (승인취소·만료) */
    public void releaseHold(Money amount) {
        if (amount.isGreaterThan(holdAmount)) {
            throw AccountException.holdExceeded(holdAmount, amount);
        }
        this.holdAmount = this.holdAmount.minus(amount);
    }
}
```

이제 **"가용잔액을 넘겨 점유할 수 없다"는 불변식이 한 곳에서만 지켜진다.**\
밖에서는 `balance`와 `holdAmount`가 어떻게 저장되는지 알 필요가 없다.

### getter가 위험해지는 경우 — 가변 객체 반환

```java
// 나쁜 예
public class Transfer {
    private final List<TransferStep> steps = new ArrayList<>();
    public List<TransferStep> getSteps() { return steps; }   // 내부 리스트를 그대로 준다
}

// 밖에서 마음대로 바꿀 수 있다
transfer.getSteps().clear();   // 캡슐화 붕괴
```

```java
// 좋은 예 — 방어적 복사 또는 불변 뷰
public List<TransferStep> getSteps() {
    return List.copyOf(steps);          // 불변 복사본
}
// 또는
public List<TransferStep> getSteps() {
    return Collections.unmodifiableList(steps);
}
```

> **방어적 복사(defensive copy)** — 내부 컬렉션을 그대로 주지 않고 복사본·불변 뷰를 주는 것.\
> 예: `getSteps()`가 원본 리스트 대신 `List.copyOf(steps)`를 돌려주면, 밖에서 `.clear()`해도 원본은 안전하다.

### 영속화 프레임워크(JPA)와의 현실적 타협

JPA 같은 ORM은 기본 생성자와 필드 접근을 요구한다. 그래서 흔히 이렇게 한다.

```java
@Entity
@NoArgsConstructor(access = AccessLevel.PROTECTED)   // 프레임워크만 쓸 수 있게
@Getter                                              // 필요한 것만 열어도 된다
public class AccountEntity extends BaseEntity {
    // setter는 만들지 않는다
}
```

> **핵심 판단**: **도메인 모델과 영속화 엔티티를 분리**하면 이 타협을 도메인까지 끌고 들어오지 않아도 된다.\
> 도메인 모델은 순수하게 두고, 별도의 엔티티 클래스와 매퍼(Mapper)로 변환하는 구조가 그 방법이다.

### 현장에서 만나는 상황

도메인 모델에 클래스 레벨 `@Getter`가 붙어 **모든 필드가 통째로 노출**되는 경우가 많다.\
점검 대상은 하나다 — 이게 **필요한 노출인지, 그냥 관성인지.**\
필요 없는 getter는 나중에 누군가가 내부 표현에 기대는 통로가 된다.

---

## A — 단정적 (Assertive)

> 출처: `jun-bank/docs/study/02-clean-code/README.md` — A 절

### 정의

> **객체가 자기 데이터에 대한 판단을 스스로 내리는가, 아니면 남이 데이터를 꺼내가서 대신 판단하는가.**

"Assertive"는 "단호한, 자기주장이 있는"이라는 뜻이다.\
객체가 수동적인 데이터 가방이 아니라 **행위의 주체**여야 한다는 속성이다.

### Tell, Don't Ask

이 속성을 실천하는 원칙이 **"묻지 말고 시켜라(Tell, Don't Ask)"** 다.

```java
// Ask — 물어보고 내가 판단한다 (비단정적)
if (card.getStatus() == CardStatus.ACTIVE
        && card.getExpiryDate().isAfter(LocalDate.now())
        && !card.isBlocked()) {
    approve();
}
```

```java
// Tell — 시킨다 (단정적)
if (card.isUsable()) {
    approve();
}

// Card 안에
public boolean isUsable() {
    return status == CardStatus.ACTIVE
        && expiryDate.isAfter(LocalDate.now())
        && !blocked;
}
```

**왜 중요한가**: 첫 번째 방식은 같은 조건식이 코드 여러 곳에 복사된다.\
카드 사용 가능 조건이 하나 늘면 **모든 복사본을 찾아 고쳐야 한다.** 하나라도 빠뜨리면 버그다.

### 빈약한 도메인 모델 (Anemic Domain Model)

데이터만 있고 행위가 없는 도메인 객체를 말한다. 마틴 파울러(Martin Fowler)가 **안티패턴**으로 지목했다.

> **빈약한 도메인 모델(anemic domain model)** — 데이터(필드+getter/setter)만 있고 규칙(행위)이 없는 도메인 객체.\
> 예: `Payment`에 getter/setter만 30줄 있고, 승인 규칙은 전부 `PaymentService`에 있는 상태.

```java
// 빈약한 모델 — 사실상 DTO
public class Payment {
    private Long id;
    private Long amount;
    private String status;
    // getter/setter만 30줄
}

// 로직은 전부 서비스에
public class PaymentService {
    public void approve(Payment payment, Long availableBalance) {
        if (!"PENDING".equals(payment.getStatus())) throw ...;
        if (payment.getAmount() > availableBalance) throw ...;
        payment.setStatus("APPROVED");
    }
}
```

**무엇이 문제인가**: 규칙이 객체 밖에 있으므로 **누구든 규칙을 우회할 수 있다.**\
`payment.setStatus("APPROVED")`를 아무 데서나 호출하면 끝이다. 상태 전이 규칙이 강제되지 않는다.

### 다만 — 항상 나쁜가?

**아니다.** 다음 경우엔 빈약한 모델이 합리적이다.

- **CRUD만 하는 단순 영역**(설정값 관리 등) — 규칙이 없는데 억지로 만들 필요 없다.
- **조회 전용 모델(Read Model)** — CQRS에서 조회 측은 데이터 그 자체가 목적이다.
- **DTO·계약 객체** — 경계를 넘나드는 데이터 운반체는 원래 데이터 가방이 맞다.

> 판단 기준: **지켜야 할 불변식이 있는가?** 있으면 객체 안에 넣는다. 없으면 억지로 만들지 않는다.

### 현장에서 만나는 상황

도메인 모델이 상태 전이 규칙을 스스로 가지고 있으면 비교적 단정적이다.\
반면 "이메일 중복 검사" 같은 판단은 서비스가 한다 — 이건 **DB 조회가 필요해서 불가피한 경우**다.\
즉 단정적이지 않은 게 전부 잘못은 아니다. 인프라가 있어야만 답할 수 있는 판단은 서비스 계층으로 나가는 게 맞다.

---

## N — 비중복 (Nonredundant)

> 출처: `jun-bank/docs/study/02-clean-code/README.md` — N 절

### 정의

> **같은 지식이 시스템 안에 두 번 이상 표현되지 않는 상태.**

### DRY와 같은 말인가?

거의 같지만 **DRY의 정의가 더 정확하다.** DRY(Don't Repeat Yourself)의 원문은 이렇다.

> "모든 지식은 시스템 내에서 **단일하고 모호하지 않은, 권위 있는 표현**을 가져야 한다."

주목할 점: **"코드"가 아니라 "지식"**이다.\
겉모양이 같은 코드가 두 개 있어도, **표현하는 지식이 다르면 중복이 아니다.**

### 우연한 중복 vs 진짜 중복

```java
// A: 카드 결제 수수료
public Money calculateCardFee(Money amount) {
    return amount.multiply(new BigDecimal("0.025"));
}

// B: 정산 수수료
public Money calculateSettlementFee(Money amount) {
    return amount.multiply(new BigDecimal("0.025"));
}
```

코드가 똑같다. 합쳐야 할까?

**아니다.** 이 둘은 **우연히 같은 값**일 뿐 서로 다른 지식이다.\
카드 수수료가 3%로 오르면 정산 수수료는 그대로여야 한다.\
합쳐두면 하나를 바꿀 때 다른 하나가 딸려 바뀐다 — **더 위험한 버그**다.

> 판단 기준: **"이 둘은 항상 함께 바뀌는가?"** 함께 바뀌면 중복이고, 따로 바뀌면 우연이다.

### 진짜 중복의 예

```java
// 세 곳에 흩어진 "가용잔액" 계산 — 같은 지식의 중복
// AccountService
Money available = account.getBalance().minus(account.getHoldAmount());
// AuthorizationService
Money available = account.getBalance().minus(account.getHoldAmount());
// BalanceQueryService
Money available = account.getBalance().minus(account.getHoldAmount());
```

"가용잔액이란 무엇인가"는 **하나의 지식**이다.\
지급정지액을 빼는 규칙이 추가되면 세 곳을 다 고쳐야 하고, 하나만 빠뜨리면 조회 화면과 승인 판단이 어긋난다.

```java
// 지식을 한 곳으로
public class Account {
    public Money availableBalance() {
        return balance.minus(holdAmount).minus(suspendedAmount);
    }
}
```

### 의도적 중복이 정당한 경우 — 서비스 경계

마이크로서비스에서는 **중복이 오히려 권장**되는 경우가 있다.

```java
// account-service 의 Money
public record Money(long amount, Currency currency) { ... }

// ledger-service 의 Money
public record Money(long amount, Currency currency) { ... }
```

이걸 공유 라이브러리로 합치면 이런 맞교환이 생긴다.

```text
공유 라이브러리로 합침                   서비스마다 복제
+---------------------------+          +---------------------------+
| 정의가 한 곳 (중복 0)        |          | 정의가 N곳 (중복 있음)      |
| 두 서비스가 같은            |          | 각자 독립 배포 가능         |
|   라이브러리 버전에 묶임      |          | 각자 다르게 진화 가능       |
+---------------------------+          +---------------------------+
  → N(비중복)은 지킨다                   → L(느슨한 결합)은 지킨다
  → 한쪽 요구로 바꾸면                    → 정의가 어긋날 위험은 감수
     양쪽 다 재배포해야 한다
```

> 이것이 **N(비중복) ↔ L(느슨한 결합)의 정면 충돌**이다. 정답은 상황마다 다르다.

### 현장에서 만나는 상황

하나의 값 객체(예: `Money`)가 여러 서비스에 **복붙**되어 있는 상황을 자주 만난다. 이게

- **N 위반**인가(같은 지식의 중복) — 그렇다면 공유 라이브러리로 옮긴다.
- **L을 지키기 위한 정당한 중복**인가 — 그렇다면 그대로 둔다.

**이 질문의 답이 곧 아키텍처 결정 기록(ADR)이다.**

판단 재료는 이렇다.

- 복제본들이 **실제로 같은가?** 정밀도·통화·반올림 규칙이 서비스마다 달라야 할 이유가 있는가?
- 공유 라이브러리가 이미 **외부 저장소로 배포**되고 있다면, 버전을 올릴 때마다 여러 서비스를 반영해야 하는 비용은 얼마인가?

> **ADR(Architecture Decision Record)** — "왜 이렇게 결정했는가"를 남기는 짧은 문서.\
> 예: "Money를 서비스마다 복제하기로 함 — 독립 배포를 지키기 위해. 대가: 정의 불일치 위험."

---

## 5속성 간의 긴장 관계

다섯 속성은 서로 당긴다. 부딪히는 자리가 정해져 있고, 판정 기준도 정해져 있다.

| 긴장 | 내용 | 판단 |
|---|---|---|
| **N ↔ L** | 중복을 없애려 공유하면 결합이 생긴다 | **서비스 경계를 넘는 공유는 신중히.** 경계 안에서는 N 우선 |
| **C ↔ N** | 응집을 위해 함께 두면 다른 곳과 중복될 수 있다 | 함께 변하는 것이 더 중요 → C 우선 |
| **E ↔ 편의성** | 캡슐화하면 매번 메서드를 만들어야 한다 | **불변식이 있으면 E 우선**, 없으면 완화 가능 |
| **A ↔ 계층 분리** | 도메인에 로직을 넣으려는데 인프라가 필요하다 | 도메인 서비스 또는 애플리케이션 계층으로 |

---

## 핵심 문장

- **SOLID는 수단(어떻게 설계하나), CLEAN은 상태(결과물이 어떤 성질인가)다.**
- **캡슐화의 핵심은 `private`이 아니라 "어떻게 저장되는지 밖에서 몰라도 되게" 하는 것이다.**
- **단정적 = 묻지 말고 시켜라 — 판단을 객체 안에 두면 같은 조건식이 한 곳에만 산다.**
- **비중복은 "코드"가 아니라 "지식"의 중복이다 — 겉이 같아도 함께 안 바뀌면 우연이다.**
- **N(비중복)과 L(느슨한 결합)은 정면충돌하며, 정답은 서비스 경계에 따라 갈린다.**

---

## 관련 자료

- 같은 폴더의 형제 주제: [`../solid-principles/`](../solid-principles/) — CLEAN이 "상태"라면 SOLID는 그 상태를 만드는 "수단"이다.
- 마틴 파울러(Martin Fowler), "Anemic Domain Model"(2003) — 빈약한 도메인 모델을 안티패턴으로 정리한 원 출처. *(Claude 보강 — 실명 인용 근거 보완)*
- DRY 원칙의 원 출처: Andrew Hunt · David Thomas, *The Pragmatic Programmer* — 위에 인용한 "단일하고 모호하지 않은, 권위 있는 표현" 정의가 여기서 나왔다. *(Claude 보강)*

---

## 용어 풀이

- **코드 냄새(Code Smell)** — 버그는 아니지만 설계에 문제가 있음을 시사하는 징후. 예: 이름에 `Util`이 붙은 거대 클래스.
- **리팩토링(Refactoring)** — 겉보기 동작을 바꾸지 않으면서 내부 구조를 개선하는 것.
- **부수 효과(Side Effect)** — 메서드가 반환값 말고 다른 것을 바꾸는 것(필드 변경, 파일 쓰기 등).
- **불변 객체(Immutable Object)** — 생성 후 상태가 바뀌지 않는 객체. `record`, `final` 필드로 만든다.
- **방어적 복사(Defensive Copy)** — 내부 컬렉션을 그대로 주지 않고 복사본을 주는 것.
- **빈약한 도메인 모델(Anemic Domain Model)** — 데이터만 있고 행위가 없는 도메인 객체. getter/setter 덩어리.
- **응집도(Cohesion)** — 한 덩어리 안의 요소들이 서로 얼마나 관련 있는가. 높을수록 좋다.
- **결합도(Coupling)** — A를 바꿀 때 B도 바꿔야 하는 정도. 낮을수록 좋다.
- **불변식(Invariant)** — 객체가 살아 있는 동안 항상 참이어야 하는 조건. 예: 계좌 잔액은 음수가 아니다.
- **플래그 인자(Flag/Boolean Parameter)** — `f(x, true, false)`처럼 상대의 내부 동작을 지시하는 boolean 인자. "이 메서드는 두 일을 한다"의 자백.
- **Tell, Don't Ask** — 데이터를 꺼내 밖에서 판단하지 말고(Ask), 객체에게 시켜라(Tell)는 원칙.
- **시간적 결합(Temporal Coupling)** — 상대가 지금 살아 있어야만 내가 동작하는 결합. 예: 동기 호출 상대가 죽으면 나도 멈춘다.
- **결과적 일관성(Eventual Consistency)** — 지금은 달라도 시간이 지나면 결국 같아지는 상태.
- **DRY(Don't Repeat Yourself)** — 모든 지식은 시스템 내에서 단일하고 권위 있는 표현을 가져야 한다.
- **CQRS** — 명령(쓰기)과 조회(읽기) 모델을 분리하는 설계. 조회 측은 빈약한 모델이 자연스럽다.
- **ADR(Architecture Decision Record)** — "왜 이렇게 결정했는가"를 남기는 짧은 문서.

---

## [Claude 추가] 더 알면 좋은 것

> 아래는 원고에 없던 배경 지식이다. 복습 시 본문(원고)과 섞어 인출하지 않는다.

- **응집도·결합도 7등급의 출처.** 위 사다리(우연적~기능적, 내용~데이터)는 래리 콘스탄틴(Larry Constantine)과 에드워드 요던(Edward Yourdon)의 *Structured Design*(1970년대)에서 정립된 분류다. CLEAN이 새로 만든 것이 아니라, 오래된 구조적 설계 이론을 다섯 속성 중 둘로 흡수한 것이다.
- **CLEAN이라는 두문자어.** C·L·E·A·N 다섯 속성을 이 이름으로 묶은 것은 비교적 근래의 정리다(제프 랭어(Jeff Langr)의 클린 코드 관련 저술에서 쓰인 것으로 알려져 있으나, 두문자어의 원 창안자 표기는 자료마다 갈린다 — *(확인 필요)*). 중요한 건 이름이 아니라, SOLID(수단)와 짝을 이루는 "결과물의 성질"이라는 관점이다.
- **Law of Demeter(최소 지식 원칙).** L(느슨한 결합)을 코드 레벨에서 실천하는 구체 규칙이다. "낯선 사람에게 말 걸지 마라" — `a.getB().getC().doD()`처럼 점(.)을 타고 남의 내부로 들어가지 말라는 것. 스탬프 결합·내용 결합이 이 규칙을 어긴 형태다.
- **왜 setter만 콕 집어 위험하다고 하나.** getter는 "읽기"라 불변식을 깨지 않지만(가변 객체를 반환하지 않는 한), setter는 "쓰기"라 객체가 검증할 틈 없이 상태를 갈아끼운다. 그래서 불변 객체(`record`, `final`)로 만들면 setter 문제 자체가 사라진다 — E와 A를 한 번에 밀어 올리는 방법이다.
