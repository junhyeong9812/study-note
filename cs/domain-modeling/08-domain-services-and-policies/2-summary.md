# domain-modeling/08-domain-services-and-policies — 도메인 서비스와 정책 객체: 엔티티에 안 맞는 규칙 — 정리 (힌트)

## 해결하는 문제

어떤 규칙은 특정 엔티티 하나의 책임이 아니다. 억지로 엔티티에 넣으면 모델이 뒤틀리고, 아무 서비스에나 넣으면 서비스가 엔티티의 일까지 빼앗는다.

```text
  "계좌 A에서 B로 이체"              → A의 일인가? B의 일인가?   둘 다 아니다
  "환불 수수료 = 상품 유형별 규칙"    → Order의 일인가?           유형마다 갈리고, 자주 바뀐다
  "배송비 = 무게 × 지역 × 등급"       → Parcel의 일인가?          여러 값과 외부 요율표가 필요하다
```

- 엔티티에 억지로 넣으면: `Account.transferTo(other)`가 상대 계좌의 상태까지 고친다. 어느 쪽이 주인인지 흐려진다.
- 서비스에 다 넣으면: 서비스가 엔티티의 setter를 불러 상태를 직접 바꾼다. 엔티티는 데이터 그릇이 되고(빈약한 모델), 같은 규칙이 서비스마다 복제된다.
- *도메인 서비스(domain service)*: 엔티티나 값 객체의 자연스러운 책임이 아닌 도메인 연산을 독립된 인터페이스로 둔 것. 상태를 갖지 않는다.
- *정책 객체(policy)*: 바뀌거나 갈라지는 규칙 하나를 객체로 꺼낸 것. 같은 인터페이스의 구현을 갈아 끼운다(Strategy 패턴).

쉬운 예: 은행 창구 직원.
- 통장은 "내 잔액보다 많이 못 뺀다"를 스스로 안다(엔티티 규칙).
- 이체는 직원이 두 통장 사이에서 진행한다. 직원은 통장 규칙을 대신 판단하지 않고, 각 통장에 "빼라"·"넣어라"를 시킨다(도메인 서비스).
- 수수료표는 창구 옆에 붙어 있다. 표가 바뀌면 직원은 그대로고 표만 바꾼다(정책).

똑같은 구조다.\
실무 예: 이체(`TransferService`), 환율 적용, 배송비·환불 수수료·할인 정책, 신용 점수 산정, 중복 가입 판정(여러 회원을 봐야 함).

## 동작·원리

### 1. 규칙을 어디에 둘까 — 결정 흐름

```text
  규칙 하나
    │
    ├─ 한 객체의 상태만으로 판단·변경?          → 그 엔티티의 메서드 (Account.withdraw)
    ├─ 상태 없이 값만으로 계산?                → 값 객체의 연산 (Money.plus, DateRange.overlaps)
    ├─ 여러 애그리거트·외부 정보가 필요한 도메인 연산? → 도메인 서비스 (TransferService)
    ├─ 같은 자리에서 규칙이 유형·시기마다 갈림?   → 정책 객체 (RefundPolicy 구현들)
    └─ 트랜잭션·권한·조회·발행 같은 흐름 조율?     → 애플리케이션 서비스 (도메인 규칙 없음)
```

### 2. 도메인 서비스 — Evans의 정의

- Evans 『DDD Reference』(2015) Services 항목
  - 도메인의 중요한 과정·변환이 엔티티나 값 객체의 자연스러운 책임이 아니면, 그 연산을 **서비스로 선언한 독립 인터페이스**로 모델에 추가한다.
  - 서비스 계약(상호작용에 대한 단언)을 정의하고, 그 단언을 특정 바운디드 컨텍스트의 유비쿼터스 언어로 적는다.
  - 서비스에 이름을 준다. 그 이름도 유비쿼터스 언어의 일부가 된다.
  - 억지로 엔티티·값에 넣으면 모델 기반 객체의 정의가 뒤틀리거나 의미 없는 인공 객체가 생긴다고 적는다.
- Evans 『DDD』(2003) 5장 SERVICES 절: 좋은 서비스의 세 가지 특징 — ① 연산이 엔티티·값 객체의 자연스러운 일부가 아닌 도메인 개념과 관련된다 ② 인터페이스가 도메인 모델의 다른 요소로 정의된다 ③ **연산이 상태를 갖지 않는다(stateless)**. (Goodreads 독자 발췌로 확인, 본문 미열람)
- 같은 절에서 서비스를 애플리케이션·도메인·인프라 계층으로 나눠 예를 든다(이체 예) [?] — 목차의 "SERVICES and the Isolated Domain Layer" 절 제목만 확인했다.

```text
  계층          서비스 예                       하는 일
  애플리케이션   TransferApplicationService     요청 해석, 트랜잭션 시작, 리포지토리로 로드·저장, 알림 요청
  도메인        TransferService                두 계좌를 조율: from.withdraw → to.deposit (규칙은 계좌가)
  인프라        이메일 발송, 환율 API 클라이언트   기술 세부
```

- Fowler "AnemicDomainModel"(2003-11-25): Evans의 애플리케이션 계층(서비스 계층)은 **얇게 유지되고, 업무 규칙이나 지식을 담지 않으며**, 작업을 조율해 아래 도메인 객체들에 위임한다는 대목을 인용한다. 이 인용은 애플리케이션 계층에 대한 것이다. 도메인 서비스가 엔티티의 규칙까지 빨아들여도 같은 결과(빈약한 모델)로 간다는 것은 이 노트의 해석이다(실험 A가 그 모양을 보인다).

### 3. 비대한 서비스 vs 얇은 도메인 서비스

```text
  비대한 서비스                                   얇은 도메인 서비스
  TransferService                                 TransferService
    if (from.getBalance() < amt) throw            from.withdraw(amt)   ← 규칙은 Account가
    from.setBalance(from.getBalance() - amt)      to.deposit(amt)
    to.setBalance(to.getBalance() + amt)
  FeeService                                      FeeService
    a.setBalance(a.getBalance() - fee) ← 검사 누락   a.withdraw(fee)       ← 같은 규칙을 탄다
  AdminService                                    AdminService
    a.setBalance(a.getBalance() + delta) ← 누락      delta<0 ? a.withdraw(-delta) : a.deposit(delta)
```

### 실험 A: 규칙을 우회하는 경로 수

```java
// A: 엔티티는 getter/setter, "잔액 ≥ 0" 검사는 TransferServiceA에만 있다
static class AccountA { long balance; long getBalance() { return balance; } void setBalance(long b) { balance = b; } }
static class FeeServiceA   { void charge(AccountA a, long fee)  { a.setBalance(a.getBalance() - fee); } }
static class AdminServiceA { void adjust(AccountA a, long delta) { a.setBalance(a.getBalance() + delta); } }
// B: 규칙은 엔티티, 서비스는 조율만
static class AccountB {
    private long balance;
    void withdraw(long amt) { if (amt <= 0 || balance < amt) throw new IllegalStateException("잔액 부족"); balance -= amt; }
    void deposit(long amt)  { if (amt <= 0) throw new IllegalArgumentException("금액 오류"); balance += amt; }
}
static class TransferServiceB { void transfer(AccountB from, AccountB to, long amt) { from.withdraw(amt); to.deposit(amt); } }
// 세 진입점(transfer·fee·admin) 각각으로 잔액 100에서 150을 빼 본다
```

(실험, JDK 21.0.12 eclipse-temurin `--cpus=2`, 2026-10-03, 3회 같은 결과)

```text
== A 비대한 서비스 (잔액 100에서 150 차감 시도)
  transfer → 잔액 100
  fee      → 잔액 -50
  admin    → 잔액 -50
  음수가 된 경로 = 2 / 3
== B 엔티티 규칙 + 얇은 도메인 서비스 (잔액 100에서 150 차감 시도)
  transfer → 잔액 100
  fee      → 잔액 100
  admin    → 잔액 100
  음수가 된 경로 = 0 / 3
```

- 관찰: A에서 규칙은 "이체" 서비스에만 있어서, 같은 엔티티를 고치는 다른 두 서비스가 그 규칙을 모른 채 잔액을 음수로 만들었다. B에서는 어떤 서비스든 `withdraw`를 지나야 하므로 세 경로 모두 막혔다.
- 해석: 도메인 서비스가 필요한 이유("두 계좌에 걸친 절차")와, 서비스가 엔티티 규칙까지 가져가면 안 되는 이유가 한 실험에 같이 보인다. 경로 수는 이 예의 값이고, 서비스가 늘수록 A의 우회 경로도 늘 수 있다.

### 4. 정책 객체 — Strategy(A.K.A. Policy)

```text
  if 방식 (서비스 안 분기)                        정책 방식 (Strategy)
  RefundService.fee(o):                          interface RefundPolicy { refundable(o); fee(o); notice(); }
    if PROMO → 예외                               StandardRefundPolicy   NoRefundPolicy   SubscriptionRefundPolicy
    if SUB   → 일할                               RefundPolicies: type → policy (조립 지점 한 곳)
    else     → 7일 무료, 이후 10%   ← 모르는 유형도 여기로
  NoticeService.text(o):  같은 분기 한 벌 더
```

- Evans 『DDD』 12장 "Relating Design Patterns to the Model"에 STRATEGY (A.K.A. POLICY) 절이 있다(InformIT 목차로 확인, 본문 미열람). GoF의 Strategy를 도메인 개념(정책)으로 읽는 관점이다. 패턴 자체는 [software-design/27](../../software-design/27-design-patterns-gof/2-summary.md), 분기 정리는 [software-design/28](../../software-design/28-taming-conditionals/2-summary.md).
- 참/거짓 판정 규칙(조건 충족 여부)은 같은 책 9장의 SPECIFICATION으로 꺼낼 수 있다 — 조회에 쓰는 법은 [10-repositories-and-factories](../10-repositories-and-factories/2-summary.md).

### 실험 B: 정책 하나 추가 — 어느 쪽이 싸고, 어느 쪽이 안전한가

시나리오 1(분기를 읽는 곳이 `RefundService` 한 곳)과 시나리오 2(안내 문구 `NoticeService`도 같은 분기를 가짐)에서, 구독 상품 `SUB`(30일 이내, 사용 일수 일할) 정책을 추가했다. 크기는 `git diff --no-index --stat`(실험 구동용 `Main.java` 변경 포함 여부는 표에 적었다).

(실험, JDK 21.0.12 eclipse-temurin `--cpus=2`, git 2.43.0 `diff --no-index --stat`, 2026-10-03. `###` 줄은 구분용 echo)

```text
### s1/if v1→v2
 policy/s1/if/{v1 => v2}/Main.java          | 2 +-
 policy/s1/if/{v1 => v2}/RefundService.java | 2 ++
 2 files changed, 3 insertions(+), 1 deletion(-)
### s1/strat v1→v2
 policy/s1/strat/{v1 => v2}/Main.java                          | 2 +-
 policy/s1/strat/{v1 => v2}/RefundPolicies.java                | 3 ++-
 /dev/null => policy/s1/strat/v2/SubscriptionRefundPolicy.java | 4 ++++
 3 files changed, 7 insertions(+), 2 deletions(-)
### s2/if v1→v2full
 policy/s2/if/{v1 => v2full}/NoticeService.java | 1 +
 policy/s2/if/{v1 => v2full}/RefundService.java | 2 ++
 2 files changed, 3 insertions(+)
### s2/strat v1→v2full
 policy/s2/strat/{v1 => v2full}/RefundPolicies.java                | 3 ++-
 /dev/null => policy/s2/strat/v2full/SubscriptionRefundPolicy.java | 5 +++++
 2 files changed, 7 insertions(+), 1 deletion(-)
```

- 시나리오 1의 `Main.java` 변경은 실험 구동용 주문 목록 추가다. 시나리오 2는 `Main`이 처음부터 `SUB` 주문을 넣어 둔다(v1에서 "규칙 없을 때"를 보려고).
- 각 폴더를 `javac`·실행한 출력에서, 시나리오 2의 차이만 표로 옮겼다.

| | 바꾼 파일(Main 제외) | 줄 | 새 유형을 등록 전에 넣으면 | 한 곳을 빠뜨리면 |
|---|---|---|---|---|
| if (시나리오 2) | 2 | +3 | `SUB d10 → 수수료 900`(일반 규칙으로 조용히 계산) | `안내: 7일 이내 무료 환불, 이후 10%`(틀린 안내, 오류 없음) |
| 정책 (시나리오 2) | 2(새 파일 1) | +7 −1 | `SUB → 정책 없음(등록 누락)` | 컴파일 오류: `does not override abstract method notice() in RefundPolicy` |

- 관찰(실제 출력에서 옮김)
  - **크기만 보면 if 방식이 작다.** 두 시나리오 모두 if 쪽 diff가 더 작았다(시나리오 1: `Main` 포함 +3−1 vs +7−2, 시나리오 2: +3 vs +7−1). 분기가 적고 정책이 잘 안 바뀌면 정책 객체는 파일과 간접만 늘린다.
  - **누락에는 정책 방식이 강하다.** if 방식은 `NoticeService` 수정을 빠뜨려도 컴파일·실행이 통과하고 틀린 안내를 냈다. 정책 방식은 같은 누락이 컴파일 오류가 됐다. 모르는 유형을 if는 `else`로 조용히 처리했고, 정책 방식은 "정책 없음"으로 드러났다(이 실험의 `Main`이 null을 검사해 출력한 것이다 — 검사하지 않으면 NPE).
- 해석: 정책 객체의 이득은 "변경 줄 수"가 아니라 "같은 분기가 여러 곳에 흩어질 때 빠뜨림을 컴파일러가 잡게 하는 것"이다. 분기가 한 곳뿐이면 누락될 다른 곳이 없으니 if가 더 싸다(YAGNI 쪽 근거, 해석). Java 21이면 `sealed` 인터페이스 + `switch` 패턴 매칭으로도 누락을 컴파일 오류로 만들 수 있다 — [software-design/24](../../software-design/24-types-as-invariants/2-summary.md).

## 쓰이는 자료구조·알고리즘

- **디스패치 표(맵)**: `Map<유형, 정책>` — 분기를 데이터로 바꾼다. 조회 O(1). 등록 누락은 `null`로 나타나므로 시작 시점에 "모든 유형에 정책이 있나"를 검사한다(`EnumMap` + 전체 enum 순회).
- **가상 메서드 디스패치**: 인터페이스 호출이 구현을 고른다. 추상 메서드 추가 = 모든 구현의 컴파일 의무.
- **규칙 체인(Chain of Responsibility)**: 할인처럼 여러 정책을 순서대로 적용할 때. 적용 순서가 결과를 바꾸므로(정률 후 정액 vs 정액 후 정률) 순서를 명시한다 — [14-money-arithmetic-rounding-allocation](../14-money-arithmetic-rounding-allocation/2-summary.md).
- **버전·유효 기간 표**: 정책이 시기마다 바뀌면 "어느 판을 적용했나"를 남긴다 — [23-versioned-rules-and-effective-dating](../23-versioned-rules-and-effective-dating/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 실무 순서

```text
  1) 규칙을 유비쿼터스 언어로 한 문장: "구독 상품은 30일 이내 일할 환불"
  2) 결정 흐름(동작·원리 1절)으로 자리를 정한다 — 엔티티·값 객체가 먼저
  3) 도메인 서비스라면: 이름을 도메인 용어로(TransferService, not AccountManager), 상태 없음, 인자·반환은 도메인 타입
  4) 외부 정보(환율·요율표)가 필요하면: 인터페이스는 도메인에, 구현은 인프라에
  5) 같은 분기가 두 곳 이상 → 정책 객체 + 등록 검사. 한 곳뿐 → if/switch로 두고 기다린다
  6) 트랜잭션·리포지토리·발행은 애플리케이션 서비스로
```

### 2. 코드 (Java 21)

```java
// 도메인 서비스: 상태 없음, 도메인 타입만 다룸, 규칙은 엔티티에 위임
public final class TransferService {
    private final ExchangeRates rates;                       // 도메인이 정의한 인터페이스
    public TransferService(ExchangeRates rates) { this.rates = rates; }
    public void transfer(Account from, Account to, Money amount) {
        Money credited = from.currency().equals(to.currency()) ? amount : rates.convert(amount, to.currency());
        from.withdraw(amount);                               // "잔액 ≥ 0"은 Account가 지킨다
        to.deposit(credited);
    }
}
public interface ExchangeRates { Money convert(Money m, Currency to); }   // 구현(HTTP 클라이언트)은 인프라 모듈

// 정책 객체: 유형마다 갈리는 규칙
public sealed interface RefundPolicy permits StandardRefund, NoRefund, SubscriptionRefund {
    boolean refundable(Order o, LocalDate today);
    Money fee(Order o, LocalDate today);
}

// 애플리케이션 서비스: 흐름만
@Transactional
public void transfer(TransferCommand c) {
    Account from = accounts.byId(c.from()), to = accounts.byId(c.to());
    transferService.transfer(from, to, c.amount());
    // 저장은 영속성 컨텍스트가(또는 accounts.save), 알림은 이벤트로
}
```

- 이체는 두 애그리거트(계좌 두 개)를 한 트랜잭션에서 고친다. [05](../05-aggregates-and-invariants/2-summary.md)의 Vernon 기본값("트랜잭션당 애그리거트 하나")과 충돌하므로, 즉시 일관성이 필요한지(이체는 보통 그렇다) 판단하고 기록한다. 결과적 일관성을 택하면 원장·보상 설계가 따라온다 — [24-double-entry-ledger](../24-double-entry-ledger/2-summary.md).
- 도메인 서비스가 리포지토리를 직접 부를지는 저자·팀마다 다르다. Vernon(2011, 2부)은 애플리케이션 서비스가 의존 객체를 풀어 애그리거트에 넘기면 애그리거트가 리포지토리·도메인 서비스에 기대지 않아도 된다고 적는다.

### 3. 진단

```bash
# 서비스가 엔티티 상태를 직접 바꾸는 곳 (비대 신호)
grep -rn --include=*Service.java -E '\.set[A-Z]\w*\(' src | wc -l
# 같은 유형 분기가 몇 곳에 흩어졌나 (정책 추출 후보)
grep -rn --include=*.java -E 'equals\("(PROMO|SUB|NORMAL)"\)|case (PROMO|SUB|NORMAL)' src | cut -d: -f1 | sort | uniq -c
```

```java
// 정책 등록 누락을 시작 시점에 잡는 테스트
for (ProductType t : ProductType.values()) assertNotNull(policies.of(t), "정책 없음: " + t);
// 우회 경로 테스트: 잔액을 바꾸는 모든 공개 진입점에 같은 불법 입력을 넣는다 (실험 A)
```

## 장애 시나리오와 대처

### 1. 서비스 비대 → 빈약한 모델로 회귀 (⚠ 커리큘럼)

- **현상**: 잔액이 음수인 계좌가 생겼다. 이체 화면에서는 막히는데 수수료 배치·관리자 조정에서 뚫린다.
- **보이는 형태**: 예외 없음. 정합성 점검 쿼리(`WHERE balance < 0`)나 정산 차이로 발견(실험 A: 3경로 중 2경로 음수).
- **원인**: 규칙이 엔티티가 아니라 한 서비스 안에 있다. 엔티티는 setter를 열어 두었고, 다른 서비스들은 그 규칙을 모른다. Fowler가 말한 "업무 규칙을 담은 두꺼운 서비스 계층 + 데이터 그릇 엔티티"다.
- **대처**: 상태 변경을 의도 있는 엔티티 메서드(`withdraw`)로 모으고 setter를 닫는다. 도메인 서비스에는 여러 객체에 걸친 절차만 남긴다. 우회 경로 테스트를 둔다.

### 2. 유형 분기 복제 → 새 유형 추가 때 한 곳 누락

- **현상**: 새 구독 상품의 환불 수수료는 맞는데, 안내 문구가 일반 상품 기준이다. 또는 새 유형이 일반 규칙으로 계산된다.
- **보이는 형태**: 오류 없음. 고객 문의·CS 로그로 발견(실험 B: `안내: 7일 이내 무료 환불, 이후 10%`, `SUB d10 → 수수료 900`).
- **원인**: 같은 `if (type == …)` 분기가 서비스 여러 곳에 있고, 모르는 유형이 `else`로 흘러간다.
- **대처**: 분기를 정책 인터페이스로 모아 추상 메서드로 누락을 컴파일 오류로 만든다(실험 B). 또는 `sealed` + 패턴 매칭 `switch`(default 없이). `else`에서 모르는 유형은 예외로 거절한다.

### 3. 정책 등록 누락 → NPE 또는 "정책 없음"

- **현상**: 새 상품 유형으로 주문하면 500 에러.
- **보이는 형태**: `NullPointerException`(정책 맵 조회 결과가 null). 실험 B의 정책 방식 v1에서 `SUB → 정책 없음(등록 누락)`.
- **원인**: 정책 클래스는 만들었거나 유형은 추가했는데, 조립 지점(맵·DI 등록)에 넣지 않았다.
- **대처**: 맵 조회를 `orElseThrow`(유형 이름 포함)로 바꾸고, 모든 유형에 정책이 있는지 시작 시점·테스트에서 검사한다. `EnumMap`과 전체 enum 순회가 쉽다.

### 4. 도메인 서비스가 인프라를 직접 다룸 → 느린 테스트·숨은 부수 효과

- **현상**: 이체 규칙 단위 테스트가 DB·HTTP 없이는 안 돌아간다. 테스트 하나가 수 초.
- **보이는 형태**: 도메인 패키지가 `RestTemplate`·`EntityManager`·`@Transactional`을 import한다.
- **원인**: 도메인 서비스가 트랜잭션·외부 호출·저장까지 맡았다. 애플리케이션 서비스와 도메인 서비스가 섞였다.
- **대처**: 외부 정보는 도메인 인터페이스(`ExchangeRates`)로 받고 구현은 인프라에 둔다. 트랜잭션·저장·발행은 애플리케이션 서비스로 옮긴다. 의존 방향 검사는 [software-design/41](../../software-design/41-architecture-fitness-rules/2-summary.md).

## 핵심 문장

- 도메인 서비스는 엔티티·값 객체의 자연스러운 책임이 아닌 도메인 연산을 담는 상태 없는 인터페이스다. 이름도 유비쿼터스 언어다.
- 도메인 서비스는 여러 객체에 걸친 절차를 조율하고, 각 객체의 규칙은 그 객체에 맡긴다. 서비스가 setter로 상태를 바꾸기 시작하면 빈약한 모델로 돌아간다(실험: 우회 경로 2/3 vs 0/3).
- 정책 객체는 유형·시기마다 갈리는 규칙을 갈아 끼우는 Strategy다. 이득은 diff 크기가 아니라 흩어진 분기의 누락을 컴파일러가 잡게 하는 데 있다.
- 변경 줄 수는 if가 더 작았다(실험: +3 vs +7). 같은 분기가 두 곳 이상 흩어지면 누락 위험 때문에 정책으로 꺼낼 이유가 생기고, 한 곳뿐이면 if/switch로 두고 기다린다.
- 트랜잭션·저장·발행은 애플리케이션 서비스, 도메인 규칙은 도메인 계층에 둔다.

## 관련 주제·근거

- 선행
  - [05-aggregates-and-invariants](../05-aggregates-and-invariants/2-summary.md)
  - [01-domain-vs-application-logic](../01-domain-vs-application-logic/2-summary.md) · 원고 [domain-vs-application-logic](../domain-vs-application-logic/2-summary.md)
- 후속·연결
  - [06-anemic-vs-rich-model](../06-anemic-vs-rich-model/2-summary.md) · [07-domain-logic-patterns-and-service-layer](../07-domain-logic-patterns-and-service-layer/2-summary.md)
  - [10-repositories-and-factories](../10-repositories-and-factories/2-summary.md)(Specification) · [23-versioned-rules-and-effective-dating](../23-versioned-rules-and-effective-dating/2-summary.md)
  - [software-design/27-design-patterns-gof](../../software-design/27-design-patterns-gof/2-summary.md) · [software-design/28-taming-conditionals](../../software-design/28-taming-conditionals/2-summary.md) · [software-design/12-simple-design-and-yagni](../../software-design/12-simple-design-and-yagni/2-summary.md)
  - 연습: [basic/18-shipping-fee](../basic/18-shipping-fee/2-summary.md)(정책 값으로 끌어올리기) · [advanced/04-refund](../advanced/04-refund/2-summary.md)(`RefundPolicy`) · [advanced/09-policy-version](../advanced/09-policy-version/2-summary.md)
- 글·문서
  - Eric Evans, 『Domain-Driven Design Reference』(2015) "Services" 항목 <https://www.domainlanguage.com/ddd/reference/>
  - Eric Evans, 『Domain-Driven Design』(2003) 5장 SERVICES 절, 9장 SPECIFICATION, 12장 STRATEGY (A.K.A. POLICY) — InformIT 목차 <https://www.informit.com/store/domain-driven-design-tackling-complexity-in-the-heart-9780321125217>; "좋은 서비스의 세 특징" 문장은 Goodreads 독자 발췌로 확인, 본문 미열람
  - Vaughn Vernon, 『Implementing Domain-Driven Design』(2013) 7장 Services(목차 확인, 본문 미열람) · "Effective Aggregate Design" Part II(2011) <https://www.dddcommunity.org/library/vernon_2011/>
  - Martin Fowler, "AnemicDomainModel"(2003-11-25) <https://martinfowler.com/bliki/AnemicDomainModel.html> · "EvansClassification"(2005-12-14) — Service 정의 <https://martinfowler.com/bliki/EvansClassification.html>
- 실험 목록 (코드: scratchpad `dm/04/e08/`, JDK 21.0.12 eclipse-temurin `--cpus=2`)
  - A 비대한 서비스 vs 얇은 도메인 서비스 — 우회 경로 수, `java Bypass.java`, 3회: 2/3 vs 0/3
  - B 정책 추가 비용과 누락 — `policy/s1`·`policy/s2`의 `{if,strat}/{v1,v2…}`, `git diff --no-index --stat`, 각 폴더 `javac -d /tmp/o *.java && java -cp /tmp/o Main`: diff +3 vs +7, 누락 시 조용한 오답 vs 컴파일 오류
