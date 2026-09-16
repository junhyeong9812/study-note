# domain-modeling/도메인 로직 vs 애플리케이션 로직 — 정리 (힌트)

> 복습은 [1-question.md](1-question.md)에서 시작하고, 막힐 때만 이 파일을 힌트로 연다.\
> 원고 출처: `jun-bank/docs/study/03-domain-vs-application-logic/README.md` (직접 쓴 원본 노트) · 이관일 2026-09-16.\
> 본문 절(두 로직의 차이 · 도메인 로직 · 애플리케이션 서비스 · 회색지대 · 계층 배치)은 **원고**를 고쳐 쓴 것이다(문체·순서 유지).\
> 「한눈에」의 식당 비유와 「전체 흐름」 그림은 **Claude가 원고 이해를 돕기 위해 새로 그린 것**이며, 원고에 없던 지식은 맨 끝 `[Claude 추가]`에만 둔다.

**한 문장으로**: **도메인 로직은 "무엇이 옳은가"를 알고, 애플리케이션 로직은 "무슨 순서로 할 것인가"를 안다.**\
이 구분이 무너지면 헥사고날이든 클린 아키텍처든 껍데기만 남는다 — 폴더는 `domain/`·`application/`·`infrastructure/`로 예쁘게 나눠져 있는데 정작 비즈니스 규칙은 서비스에 다 들어 있는 상태가 가장 흔한 실패다.

---

## 한눈에 — 쉽게 말하면

잘 굴러가는 **식당 한 곳**을 떠올리면 된다. *(Claude 보강 — 원고에 없는 비유)*

```text
식당 한 곳
+--------------------------------------------------+
| [주방장]  "이 재료로 이 요리가 되는가"를 안다      |  ← 도메인: 무엇이 옳은가
|           상한 재료는 안 쓴다 (규칙을 스스로 지킴)  |
|                                                  |
| [홀 매니저] "주문받기 → 주방에 전달 → 서빙 → 결제" |  ← 애플리케이션: 무슨 순서로
|           순서만 조율한다. 요리 판단은 주방장에게  |
|           시킨다 (꺼내서 직접 판단하지 않는다)      |
+--------------------------------------------------+
  매니저가 재료 신선도를 직접 판정하기 시작하면
  → 주방장은 빈 껍데기가 된다 (= 빈약한 도메인 모델)
```

**코드도 똑같은 구조다.** 도메인 객체(주방장)는 자기 상태에 대한 규칙을 스스로 판단하고(A, 단정적), 애플리케이션 서비스(홀 매니저)는 유스케이스 흐름을 순서대로 엮기만 한다.\
매니저가 주방장의 재료를 꺼내와 스스로 신선도를 판정하면 — 즉 서비스가 도메인 객체에서 값을 꺼내 직접 판단하면 — 같은 판정이 다른 매니저에게도 복사되고, 규칙 하나가 바뀔 때마다 흩어진 복사본을 전부 찾아 고쳐야 한다.

쉽게 말하면 이렇다.\
**도메인 로직은 "시스템을 안 만들어도 업무에 존재하는 규칙"이고, 애플리케이션 로직은 "시스템이 있어서 생긴 절차"다.** 이 한 문장이 이 주제 전체의 감별 기준이다.

---

## 문제 — 이 개념이 답하려는 질문

이 주제에는 풀어야 할 코드 과제가 없다(개념 정리다). 대신 실무에서 매번 갈리는 배치 판단에 답한다.

```text
핵심 감별법 하나로 시작한다:
  "이 규칙은 우리가 시스템을 안 만들어도 업무에 존재하는가?"

  "정산 완료된 거래는 취소할 수 없다"
     → 업무에 존재한다        → 도메인 로직
  "취소 요청이 오면 먼저 원거래를 조회하고, 없으면 404를 반환한다"
     → 시스템이 있어서 생긴 절차 → 애플리케이션 로직
```

이 감별법으로도 안 갈리는 **회색지대**들이 있고, 서머리 후반이 그것들을 하나씩 판정한다.

```text
Q1  "이메일은 유일해야 한다" — 도메인 규칙인데 판단에 DB가 필요하다. 어디에 두나?
Q2  겉이 같은 코드 두 조각 — 합쳐도 되나(진짜 중복), 두어야 하나(우연)?
Q3  여러 애그리게이트를 한 번에 바꿔야 한다 — 한 트랜잭션에 묶어도 되나?
Q4  조회(Query)도 도메인 모델을 거쳐야 하나?
Q5  도메인 이벤트는 누가 만들고 누가 발행하나? 그 사이 트랜잭션은?
```

아래 서머리는 이 감별법과 다섯 회색지대를 하나씩 분석·정리한 것이다.

---

## 전체 흐름

애플리케이션 서비스가 유스케이스 하나를 처리하는 순서는 정해져 있다. 세로로 내려가며, 오른쪽이 그 단계가 **어느 계층의 일**인지다.

```text
① 입력 받기 (Command 객체)              애플리케이션
        ↓
② 트랜잭션 경계 열기                     애플리케이션  ← 경계는 여기서 잡는다
        ↓
③ 필요한 객체 불러오기 (포트를 통해)      애플리케이션
        ↓
④ 도메인에 시키기                        도메인       ← 판단은 전부 여기
   (card.assertUsable / account.hold …)
        ↓
⑤ 결과 저장하기 (포트를 통해)            애플리케이션
        ↓
⑥ 부수 작업 (이벤트 발행·알림)           애플리케이션
        ↓
⑦ 결과 반환 (Result 객체)               애플리케이션
```

- ④만 도메인의 일이고 나머지는 전부 조율(오케스트레이션)이다.\
- 서비스에 **조건문·계산식이 쌓이면** ④가 서비스로 새어 나왔다는 신호다 — 판단을 도메인으로 돌려보내야 한다.

---

## 두 로직의 차이

> 출처: `03-domain-vs-application-logic/README.md` — §1

| | 도메인 로직 | 애플리케이션 서비스 로직 |
|---|---|---|
| 답하는 질문 | 이 상태에서 이 조작이 **허용되는가?** | 이 유스케이스를 **어떤 순서로** 처리하는가? |
| 예 | "정산된 거래는 승인취소할 수 없다" | "카드 조회 → 승인 판단 → 홀딩 → 이벤트 발행" |
| 외부 의존 | **없어야 한다** (DB·HTTP·시간·랜덤 모두) | 있다 (포트를 통해) |
| 트랜잭션 | 모른다 | **경계를 여기서 잡는다** |
| 테스트 | 순수 단위 테스트 (Mock 불필요) | Mock으로 포트를 대체 |
| 재사용 | 여러 유스케이스에서 재사용됨 | 유스케이스 하나에 1:1 |

핵심 감별법은 하나다.

> **"이 규칙은 우리가 시스템을 안 만들어도 업무에 존재하는가?"**

- "정산 완료된 거래는 취소할 수 없다" → 업무에 존재한다 → 도메인 로직
- "취소 요청이 오면 먼저 원거래를 조회하고, 없으면 404를 반환한다" → 시스템이 있어서 생긴 절차 → 애플리케이션 로직

---

## 도메인 로직 — 어디에 사는가

> 출처: `03-domain-vs-application-logic/README.md` — §2

```text
도메인 로직
├── 엔티티 / 애그리게이트 루트   ← 자기 상태에 대한 규칙
├── 값 객체                      ← 값 자체의 유효성·연산
└── 도메인 서비스                ← 엔티티 하나에 담기 어려운 규칙
```

> **엔티티(entity)** — 식별자(ID)로 구분되는 객체. 값이 바뀌어도 같은 것.\
> 예: 계좌는 잔액이 바뀌어도 계좌번호가 같으면 같은 계좌다.
>
> **값 객체(value object)** — 값 자체로 구분되는 객체. 식별자가 없고 보통 불변.\
> 예: 1,000원은 어느 1,000원이든 같은 1,000원이다.

### 엔티티에 넣는 규칙 — 자기 상태에 대한 판단

```java
public class Authorization {   // 승인 (애그리게이트 루트)

    private AuthorizationId id;
    private Money amount;
    private Money cancelledAmount;      // 누적 취소액
    private AuthorizationStatus status;

    /**
     * 부분취소 가능 여부를 스스로 판단한다.
     * 도메인 규칙: 누적 취소액은 원거래 금액을 초과할 수 없다.
     */
    public void cancelPartially(Money requestAmount) {
        if (status == AuthorizationStatus.SETTLED) {
            throw AuthorizationException.alreadySettled(id);
        }
        Money afterCancel = cancelledAmount.plus(requestAmount);
        if (afterCancel.isGreaterThan(amount)) {
            throw AuthorizationException.cancelAmountExceeded(amount, afterCancel);
        }
        this.cancelledAmount = afterCancel;
        if (cancelledAmount.equals(amount)) {
            this.status = AuthorizationStatus.CANCELLED;   // 전액 취소되면 상태 전이
        }
    }
}
```

**이 규칙이 도메인인 이유**: 시스템이 없어도 "취소 금액이 원거래를 넘을 수 없다"는 규칙은 존재한다.\
그리고 이 판단에 **DB도 외부 API도 필요 없다** — 객체가 가진 정보만으로 판단된다.

### 값 객체에 넣는 규칙 — 값 자체의 유효성과 연산

```java
public record Money(long amount, Currency currency) implements Comparable<Money> {

    public Money {
        if (currency == null) throw new IllegalArgumentException("통화는 필수입니다");
        // 최소단위 정수로만 다룬다. 부동소수 금지
    }

    public Money plus(Money other) {
        requireSameCurrency(other);
        return new Money(Math.addExact(this.amount, other.amount), currency);
    }

    public Money minus(Money other) {
        requireSameCurrency(other);
        return new Money(Math.subtractExact(this.amount, other.amount), currency);
    }

    public boolean isGreaterThan(Money other) {
        requireSameCurrency(other);
        return this.amount > other.amount;
    }

    public boolean isNegative() { return amount < 0; }

    private void requireSameCurrency(Money other) {
        if (this.currency != other.currency) {
            throw new CurrencyMismatchException(this.currency, other.currency);
        }
    }

    @Override public int compareTo(Money o) { requireSameCurrency(o); return Long.compare(amount, o.amount); }
}
```

**값 객체의 이점**: `long amount`로 다니면 원화인지 달러인지, 원 단위인지 전 단위인지 아무도 모른다.\
값 객체로 감싸면 **타입이 곧 문서**가 되고, 통화 불일치 같은 실수를 컴파일·실행 시점에 잡는다.

### 도메인 서비스 — 언제 필요한가

**한 엔티티에 넣으면 어색한 규칙**이 있을 때만 쓴다. 남용하면 로직이 다시 엔티티 밖으로 새어나간다.

필요한 전형적 상황: **여러 애그리게이트에 걸친 규칙**

```java
/**
 * 이체 가능 여부 판단 — 출금 계좌와 입금 계좌 둘 다 봐야 한다.
 * 어느 한쪽 Account 에 넣으면 그 계좌가 상대 계좌를 아는 이상한 구조가 된다.
 */
public class TransferPolicy {   // 도메인 서비스 — 인프라 의존 없음

    public void validate(Account from, Account to, Money amount) {
        if (from.id().equals(to.id())) {
            throw TransferException.sameAccount(from.id());
        }
        if (!from.isWithdrawable()) {
            throw TransferException.notWithdrawable(from.id());
        }
        if (!to.isDepositable()) {
            throw TransferException.notDepositable(to.id());
        }
        if (amount.isGreaterThan(from.availableBalance())) {
            throw TransferException.insufficientBalance(from.availableBalance(), amount);
        }
    }
}
```

> **주의**: 도메인 서비스는 `@Service`를 붙이지 않아도 된다. **인프라 의존이 없는 순수 객체**여야 한다.\
> 스프링 빈으로 등록하는 순간 스프링 없이 테스트할 수 없게 되는 것은 아니지만, "인프라를 주입받아도 되는 곳"으로 오인되기 쉽다.

---

## 도메인이 인프라를 몰라야 하는 이유

> 출처: `03-domain-vs-application-logic/README.md` — §2.4

```java
// 나쁜 예 — 도메인이 시간과 DB를 안다
public class Authorization {
    public boolean isExpired() {
        return LocalDateTime.now().isAfter(createdAt.plusDays(7));   // now() = 숨은 의존
    }
}
```

`LocalDateTime.now()`는 **테스트할 수 없는 코드**를 만든다.\
"8일 뒤에 만료되는가"를 검증하려면 시스템 시계를 조작해야 한다.

```java
// 좋은 예 — 시간을 주입받는다
public class Authorization {
    public boolean isExpiredAt(LocalDateTime now) {
        return now.isAfter(createdAt.plusDays(HOLD_EXPIRY_DAYS));
    }
}

// 테스트가 자유로워진다
assertThat(auth.isExpiredAt(createdAt.plusDays(8))).isTrue();
```

> 시간·랜덤·현재 로그인 사용자처럼 **바깥세상에서 오는 값**은 전부 인자로 주입받는다. 그래야 도메인이 순수해지고 테스트가 값싸진다.

---

## 애플리케이션 서비스 로직 — 오케스트레이션

> 출처: `03-domain-vs-application-logic/README.md` — §3

애플리케이션 서비스가 하는 일은 「전체 흐름」의 ①~⑦로 정해져 있다. 판단은 도메인이, 조율은 서비스가 한다.

```java
@Service
@RequiredArgsConstructor
@Transactional                                  // ② 트랜잭션 경계
public class AuthorizePaymentService implements AuthorizePaymentUseCase {

    private final CardRepository cardRepository;              // 포트
    private final AccountRepository accountRepository;        // 포트
    private final AuthorizationRepository authorizationRepository;
    private final PaymentEventPublisher eventPublisher;       // 포트
    private final IdempotencyStore idempotencyStore;          // 포트

    @Override
    public AuthorizationResult authorize(AuthorizeCommand command) {   // ① 입력

        // 멱등성 — 시스템이 있어서 생긴 절차이므로 애플리케이션 로직
        Optional<AuthorizationResult> previous =
            idempotencyStore.find(command.idempotencyKey());
        if (previous.isPresent()) {
            return previous.get();                          // 재처리하지 않고 최초 결과 반환
        }

        // ③ 불러오기
        Card card = cardRepository.findById(command.cardId())
            .orElseThrow(() -> CardException.notFound(command.cardId()));
        Account account = accountRepository.findByIdForUpdate(card.accountId())
            .orElseThrow(() -> AccountException.notFound(card.accountId()));

        // ④ 시키기 — 판단은 전부 도메인이 한다
        card.assertUsable(command.requestedAt());            // 도메인 규칙
        Authorization authorization = Authorization.create(command.toAuthorizeSpec());
        account.hold(command.amount());                      // 도메인 규칙 (가용잔액 검증 포함)

        // ⑤ 저장
        accountRepository.save(account);
        Authorization saved = authorizationRepository.save(authorization);

        // ⑥ 부수 작업
        eventPublisher.publishAuthorized(saved);

        AuthorizationResult result = AuthorizationResult.from(saved);
        idempotencyStore.save(command.idempotencyKey(), result);
        return result;                                        // ⑦
    }
}
```

> **멱등성(idempotency)** — 같은 요청을 여러 번 보내도 결과가 한 번 보낸 것과 같도록 보장하는 성질.\
> 예: 결제 승인 요청이 네트워크 재시도로 두 번 와도, 키가 같으면 최초 결과를 그대로 돌려주고 두 번 승인하지 않는다.

### 여기에 비즈니스 규칙이 새어나오는 신호

```java
// 나쁜 신호들
if (account.getBalance() - account.getHoldAmount() < command.getAmount()) { ... }   // 가용잔액 계산이 서비스에
if (card.getStatus() != CardStatus.ACTIVE) { throw ...; }                           // 사용 가능 판단이 서비스에
authorization.setStatus(AuthorizationStatus.APPROVED);                              // 상태 전이를 서비스가 직접
```

**공통점**: 서비스가 도메인 객체에서 **값을 꺼내 스스로 판단**하고 있다.\
이건 「단정적(Assertive)」 위반이며, 같은 판단이 다른 서비스에도 복사될 것이다. *(형제 주제 clean-code의 A 속성)*

### 얼마나 얇아야 하나

목표는 **"읽으면 유스케이스 흐름이 그대로 보이는 것"**이다.

- 조건문이 거의 없다 (있다면 흐름 분기이지 비즈니스 판단이 아니다)
- 계산식이 없다
- `for` 루프 안에 복잡한 로직이 없다

너무 얇아서 문제인 경우는 드물다.\
다만 **아무 일도 하지 않고 리포지토리만 호출하는 서비스**(pass-through)가 많다면, 그건 계층이 하나 남는다는 신호일 수 있다.

---

## 경계의 회색지대 — 판단이 갈리는 곳

> 출처: `03-domain-vs-application-logic/README.md` — §4

### 회색지대 1 — 유효성 검증의 3분법

**"검증"이라는 한 단어에 세 가지가 섞여 있다.** 나누면 어디에 둘지 자명해진다.

| 종류 | 예 | 위치 | 이유 |
|---|---|---|---|
| **입력 형식 검증** | 이메일이 `@`를 포함하는가, 필수값이 비었는가 | **프레젠테이션** (`@Valid`) | 도메인까지 갈 필요 없는 쓰레기 입력 |
| **도메인 불변식** | 금액이 음수가 아니다, 취소액이 원거래를 넘지 않는다 | **도메인** | 업무 규칙이며 외부 조회 불필요 |
| **컨텍스트 의존 규칙** | 이메일이 이미 가입되어 있는가 | **애플리케이션** | 판단에 **저장소 조회가 필요**하다 |

> **불변식(invariant)** — 객체가 살아 있는 동안 항상 참이어야 하는 조건.\
> 예: "가용잔액을 넘겨 점유할 수 없다", "취소 누적액은 원거래를 넘지 않는다".

```java
// ① 입력 형식 — 프레젠테이션
public record CreateUserRequest(
    @NotBlank @Email String email,
    @NotBlank @Size(min = 2, max = 50) String name
) {}

// ② 도메인 불변식 — 값 객체
public record Email(String value) {
    private static final Pattern PATTERN = Pattern.compile("^[\\w.-]+@[\\w.-]+\\.[a-z]{2,}$");
    public Email {
        if (value == null || !PATTERN.matcher(value).matches()) {
            throw UserException.invalidEmail(value);
        }
    }
}

// ③ 컨텍스트 의존 — 애플리케이션
if (userRepository.existsByEmail(command.email())) {
    throw UserException.emailAlreadyExists(command.email());
}
```

### 회색지대 2 — 중복 검사는 도메인인가 애플리케이션인가

**"이메일은 유일해야 한다"는 도메인 규칙이 맞다.** 그런데 그 판단에는 저장소 전체를 봐야 한다 — 즉 **인프라가 필요**하다.\
도메인은 인프라를 몰라야 하므로 충돌한다. 실무적 해법 셋이 있다.

```java
// 해법 A — 애플리케이션 서비스에서 검사 (가장 흔함)
if (userRepository.existsByEmail(command.email())) throw UserException.emailAlreadyExists(...);
```
- 장점: 단순
- 단점: **TOCTOU 문제** — 검사(Time Of Check)와 저장(Time Of Use) 사이에 다른 요청이 끼어들 수 있다. **DB 유니크 제약이 최후의 방어선**이어야 한다

```java
// 해법 B — 도메인 서비스에 규칙을 두되 조회는 포트로 주입
public class UserRegistrationPolicy {
    private final UserExistenceChecker checker;   // 도메인이 정의한 인터페이스

    public void validateNewUser(Email email) {
        if (checker.existsByEmail(email)) throw UserException.emailAlreadyExists(email);
    }
}
```
- 장점: 규칙이 도메인 어휘로 표현됨
- 단점: 간접 계층 증가

```java
// 해법 C — DB 제약에 맡기고 예외를 도메인 예외로 번역
try {
    return userRepository.save(user);
} catch (DataIntegrityViolationException e) {
    throw UserException.emailAlreadyExists(user.email());
}
```
- 장점: 경쟁 조건에 안전 (DB가 원자적으로 보장)
- 단점: 예외 기반 흐름 제어, DB 오류 메시지 파싱 의존

> **실전 조합**: A + C. 평상시엔 A로 친절한 메시지를, 경쟁 상황에서는 C가 잡는다.
>
> **TOCTOU(Time Of Check to Time Of Use)** — "확인한 시점"과 "쓰는 시점" 사이에 상태가 바뀌어 생기는 결함.\
> 예: 중복 없음을 확인한 직후, 저장 전에 다른 요청이 같은 이메일을 먼저 저장해 버린다.

### 회색지대 3 — 여러 애그리게이트에 걸친 규칙

**원칙: 하나의 트랜잭션은 하나의 애그리게이트만 변경한다.** 이건 DDD의 권장 규칙이다.

이유: 애그리게이트가 **정합성의 단위**이기 때문이다.\
여러 개를 한 트랜잭션에서 바꾸면 락 범위가 커지고, 결국 분산 환경에서 불가능해진다.

여러 개를 바꿔야 한다면:
- **같은 서비스 안**: 도메인 이벤트로 이어붙이거나, 정말 필요하면 한 트랜잭션에 묶되 의식적으로 결정
- **다른 서비스**: Saga (분산 트랜잭션 조율 패턴)

> **애그리게이트(aggregate)** — 함께 변경되어야 하는 객체들의 묶음. 트랜잭션·정합성의 단위다.\
> 예: 승인 1건과 그에 딸린 취소 이력은 함께 바뀌므로 한 애그리게이트다.

### 회색지대 4 — 조회(Query) 로직은 어디에

**조회는 도메인 모델을 거치지 않아도 된다.** 이게 **CQRS**(명령·조회 책임 분리)의 출발점이다.

| | 명령 (Command) | 조회 (Query) |
|---|---|---|
| 목적 | 상태 변경 | 데이터 표시 |
| 불변식 | 지켜야 함 | 없음 |
| 경로 | 애플리케이션 → 도메인 → 저장소 | **애플리케이션 → 저장소 (도메인 우회 가능)** |

```java
// 조회는 도메인 모델을 만들지 않고 바로 DTO로
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class TransactionHistoryQueryService {
    private final TransactionQueryRepository queryRepository;   // QueryDSL 등

    public PageResponse<TransactionHistoryView> search(TransactionSearchCondition cond) {
        return queryRepository.search(cond);   // 엔티티 → 도메인 → DTO 변환 없이 바로 프로젝션
    }
}
```

> 도메인 객체를 만들었다가 다시 DTO로 바꾸는 것은 **조회에서는 순수 낭비**다.\
> 다만 **명령 경로에서는 절대 이렇게 하지 않는다** — 불변식을 건너뛰게 되기 때문이다.

### 회색지대 5 — 도메인 이벤트는 누가 만들고 누가 발행하는가

| 단계 | 주체 | 이유 |
|---|---|---|
| **생성** | 도메인 | "무슨 일이 일어났는가"는 도메인 사실이다 |
| **발행** | 애플리케이션 (또는 인프라) | Kafka·트랜잭션은 인프라 관심사 |

```java
// 도메인이 이벤트를 만든다
public class Authorization {
    private final List<DomainEvent> events = new ArrayList<>();

    public static Authorization create(AuthorizeSpec spec) {
        Authorization auth = new Authorization(spec);
        auth.events.add(new AuthorizationApprovedEvent(auth.id, auth.amount, spec.requestedAt()));
        return auth;
    }

    public List<DomainEvent> pullEvents() {          // 꺼내면 비운다
        List<DomainEvent> copy = List.copyOf(events);
        events.clear();
        return copy;
    }
}

// 애플리케이션이 발행한다
Authorization saved = authorizationRepository.save(authorization);
saved.pullEvents().forEach(eventPublisher::publish);
```

> ⚠️ **주의**: 여기서 그냥 Kafka로 보내면 **DB 커밋과 발행이 원자적이지 않다.**\
> 커밋 후 발행 실패 시 이벤트가 유실된다. 해법이 **Outbox 패턴**이다.
>
> **Outbox 패턴** — 이벤트를 같은 DB 트랜잭션 안의 별도 테이블(outbox)에 함께 저장해 두고, 별도 프로세스가 그 테이블을 읽어 발행하는 방식. 커밋과 발행 기록을 원자적으로 묶는다.

---

## 계층별 배치

> 출처: `03-domain-vs-application-logic/README.md` — §5

```text
presentation/          ← 입력 형식 검증, HTTP↔Command 변환
    │
    ▼
application/
    ├── port/in/       ← 유스케이스 인터페이스
    ├── port/out/      ← 저장소·외부 시스템 인터페이스 (애플리케이션이 소유 = DIP)
    ├── dto/           ← Command / Result
    └── service/       ← 오케스트레이션, 트랜잭션 경계, 멱등성, 이벤트 발행
    │
    ▼
domain/                ← 인프라 의존 0. 순수 자바만
    ├── model/         ← 엔티티, 값 객체, 애그리게이트
    ├── event/         ← 도메인 이벤트
    ├── exception/     ← 도메인 예외
    └── service/       ← 도메인 서비스 (여러 애그리게이트 규칙)
    ▲
    │  (구현)
infrastructure/        ← JPA, Feign, Kafka 어댑터. 의존 방향이 안쪽을 향한다
```

**의존 방향은 항상 안쪽(도메인)을 향한다.** `domain/` 패키지의 import 문에 스프링·JPA가 하나도 없어야 한다.\
이게 지켜지는지 확인하는 가장 쉬운 방법은 **도메인 테스트를 스프링 없이 돌려보는 것**이다.

> **DIP(의존성 역전 원칙)** — 포트(인터페이스)를 안쪽 계층이 소유하고, 바깥 계층이 그것을 구현하게 해 의존 방향을 뒤집는 것.\
> 예: 저장소 인터페이스를 `application/port/out`이 정의하고, JPA 어댑터가 그걸 구현하면 도메인이 JPA를 몰라도 된다.

---

## 현장에서 만나는 상황 — 롤백 필드와 트랜잭션 경계

실제 서비스에서 자주 보이는, 두 로직이 뒤섞인 흔한 형태다.

- **도메인 모델에 롤백용 필드가 있다** (예: `previousStatus` — 실패 시 되돌릴 이전 상태를 도메인 객체가 기억).
- **트랜잭션 경계 안에서 외부 API를 호출한다** (예: 가입 서비스가 로컬 DB 트랜잭션 안에서 인증 서버를 부른다).

이 둘은 별개처럼 보이지만 **같은 원인**에서 나온다 — **분산 트랜잭션(외부 시스템 + 로컬 DB)을 로컬 트랜잭션 하나처럼 다루려 한 것**이다.\
외부 호출이 성공하고 로컬 커밋이 실패하면(또는 그 반대), 두 시스템의 상태가 어긋난다. 그걸 도메인 필드로 수동 롤백하려다 롤백 로직이 도메인에 스며든 것이다.\
바른 방향은 외부 호출을 트랜잭션 경계 밖으로 빼고, 두 시스템 사이의 정합성은 Saga·Outbox 같은 **분산 조율 패턴**으로 다루는 것이다 — 그러면 도메인에서 롤백 필드가 사라진다.

---

## 핵심 문장

- **도메인 로직은 "무엇이 옳은가", 애플리케이션 로직은 "무슨 순서로 할 것인가"를 안다.**
- **감별법 한 줄: "이 규칙은 시스템을 안 만들어도 업무에 존재하는가?" — 있으면 도메인, 시스템 때문에 생긴 절차면 애플리케이션.**
- **애플리케이션 서비스가 값을 꺼내 스스로 판단하기 시작하면 도메인이 빈 껍데기가 되고, 같은 판단이 서비스마다 복사된다.**
- **"검증"은 세 가지다 — 입력 형식(프레젠테이션)·불변식(도메인)·컨텍스트 의존(애플리케이션).**
- **하나의 트랜잭션은 하나의 애그리게이트만 바꾼다. 조회는 도메인을 우회해도 되지만, 명령은 절대 안 된다.**
- **도메인 이벤트는 도메인이 만들고 애플리케이션이 발행한다 — 그 사이의 원자성은 Outbox가 지킨다.**

---

## 관련 자료

- 형제 주제: [`../clean-code/`](../clean-code/) — 「단정적(Assertive)」·「캡슐화」·「비중복」 속성이 이 주제의 배치 판단과 직접 이어진다. "서비스가 값을 꺼내 판단"은 곧 A 위반이다.
- SOLID의 **DIP(의존성 역전)** — 포트를 애플리케이션이 소유하는 구조의 근거. (형제 주제 `solid-principles` 후보)
- **Saga · Outbox 패턴** — 여러 애그리게이트/서비스에 걸친 정합성과 이벤트 발행의 원자성 문제. (별도 주제로 승격 후보 — 아직 이관 전)
- Eric Evans, *Domain-Driven Design*(2003) — 엔티티·값 객체·애그리게이트·도메인 서비스 용어의 원 출처. *(Claude 보강 — 실명 인용 근거 보완)*

---

## 용어 풀이

- **도메인(Domain)** — 소프트웨어가 다루는 업무 영역 그 자체. 예: 결제·계좌·원장 같은 영역.
- **도메인 모델(Domain Model)** — 그 업무의 개념과 규칙을 코드로 표현한 것.
- **엔티티(Entity)** — 식별자(ID)로 구분되는 객체. 값이 바뀌어도 같은 것. 예: 계좌.
- **값 객체(Value Object, VO)** — 값 자체로 구분되는 객체. 식별자가 없고 보통 불변. 예: 금액, 이메일.
- **애그리게이트(Aggregate)** — 함께 변경되어야 하는 객체들의 묶음. 트랜잭션·정합성의 단위.
- **애그리게이트 루트(Aggregate Root)** — 애그리게이트의 대표 엔티티. 외부는 반드시 루트를 통해서만 접근한다.
- **도메인 서비스(Domain Service)** — 엔티티 하나에 담기 어려운 도메인 규칙을 담는 순수 객체. 인프라 의존 없음.
- **애플리케이션 서비스(Application Service)** — 유스케이스 하나를 처리하는 진입점. 흐름을 조율한다.
- **유스케이스(Use Case)** — 사용자가 시스템으로 달성하려는 목표 하나. 예: "결제를 승인한다".
- **포트(Port)** — 애플리케이션이 외부와 대화하기 위해 스스로 정의한 인터페이스.
- **어댑터(Adapter)** — 포트를 실제 기술로 구현한 것(JPA, Feign, Kafka).
- **오케스트레이션(Orchestration)** — 여러 객체·포트를 정해진 순서로 엮어 유스케이스를 완성하는 것. 애플리케이션 서비스의 일.
- **불변식(Invariant)** — 객체가 살아 있는 동안 항상 참이어야 하는 조건. 예: 취소 누적액은 원거래를 넘지 않는다.
- **멱등성(Idempotency)** — 같은 요청을 여러 번 보내도 결과가 한 번과 같도록 보장하는 성질.
- **TOCTOU(Time Of Check to Time Of Use)** — 확인 시점과 사용 시점 사이에 상태가 바뀌어 생기는 결함.
- **트랜잭션 경계(Transaction Boundary)** — 어디서 커밋/롤백 단위가 시작하고 끝나는가. 애플리케이션 서비스가 잡는다.
- **CQRS(Command Query Responsibility Segregation)** — 명령(쓰기)과 조회(읽기) 모델을 분리하는 설계. 조회는 도메인을 우회할 수 있다.
- **프로젝션(Projection)** — 조회에서 엔티티 전체 대신 화면에 필요한 필드만 골라 DTO로 바로 뽑는 것.
- **도메인 이벤트(Domain Event)** — "무슨 일이 일어났는가"를 나타내는 도메인 사실. 도메인이 만들고 애플리케이션이 발행한다.
- **Saga** — 여러 서비스에 걸친 트랜잭션을 보상(compensation)으로 조율하는 패턴.
- **Outbox 패턴** — 이벤트를 같은 트랜잭션의 별도 테이블에 저장하고 별도 프로세스가 발행해, 커밋과 발행을 원자적으로 묶는 패턴.
- **DIP(의존성 역전 원칙)** — 안쪽 계층이 포트를 소유하고 바깥이 구현해 의존 방향을 뒤집는 것.
- **빈약한 도메인 모델(Anemic Domain Model)** — 데이터만 있고 행위(규칙)가 없는 도메인 객체. 로직이 서비스로 새어 나간 상태.

---

## [Claude 추가] 더 알면 좋은 것

> 아래는 원고에 없던 배경 지식이다. 복습 시 본문(원고)과 섞어 인출하지 않는다.

- **용어의 출처는 DDD다.** 엔티티·값 객체·애그리게이트·도메인 서비스·유스케이스는 에릭 에반스(Eric Evans)의 *Domain-Driven Design*(2003)에서 정립된 어휘다. 이 주제는 그 어휘를 헥사고날(포트·어댑터) 아키텍처의 계층 배치에 얹은 것이다.
- **"묻지 말고 시켜라(Tell, Don't Ask)"가 감별의 코드 레벨 실천이다.** 서비스가 `getStatus()`로 꺼내 판단하면 Ask(빈약한 모델), 도메인에 `isUsable()`을 물어 시키면 Tell(단정적). 「새어나오는 신호」 절의 나쁜 예가 전부 Ask 형태다 — clean-code의 A 속성과 같은 이야기다.
- **불변식이 있느냐가 도메인/DTO를 가른다.** 지켜야 할 불변식이 있으면 규칙을 객체 안에 넣어 도메인 모델로, 없으면(설정값 CRUD·조회 전용 Read Model·경계를 넘는 DTO) 데이터 가방으로 두는 게 맞다. 빈약한 모델이 항상 나쁜 것은 아니다.
- **트랜잭션 안의 외부 호출은 그 자체로 냄새다.** 원격 호출은 느리고 실패하며 롤백되지 않는다. DB 트랜잭션이 그 호출이 끝날 때까지 커넥션·락을 붙잡고 있으면 처리량이 무너진다 — 「현장」 절의 롤백 필드 문제와 같은 뿌리다.
