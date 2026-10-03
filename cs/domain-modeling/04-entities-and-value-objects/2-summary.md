# domain-modeling/04-entities-and-value-objects — 엔티티와 값 객체: 식별성 vs 값 동등성 — 정리 (힌트)

## 해결하는 문제

"이 둘은 같은 것인가?"에 답하는 규칙이 모델에 없으면, 같은 것을 둘로 세거나 다른 것을 하나로 합친다.

```text
  질문: 두 객체가 "같다"는 무슨 뜻인가?

  회원 kim(id=7, 이름 "김철수")  vs  회원(id=9, 이름 "김철수")   → 이름이 같아도 다른 사람
  회원 kim(id=7, 주소 서울)      vs  회원 kim(id=7, 주소 부산)    → 주소가 바뀌어도 같은 사람
  1000원                        vs  1000원                       → 어느 지폐인지 상관없이 같은 값
```

- 앞의 두 줄은 **식별성(identity)** 으로 같음을 판단한다. 속성이 바뀌어도 같은 것으로 이어진다.
- 마지막 줄은 **값(attribute)** 으로 같음을 판단한다. 속성이 같으면 같은 것이다.
- 이 차이를 코드에 적어 두지 않으면 두 종류의 사고가 난다.
  - 값이어야 할 것에 `equals`가 없다 → 같은 1000원이 `HashSet`에 둘 들어간다.
  - 엔티티의 `equals`를 바뀌는 값으로 정했다 → 저장한 뒤 컬렉션에서 그 엔티티를 못 찾는다.

쉬운 예: 은행 창구.
- 통장(계좌)은 번호로 구분한다. 잔액·주소가 바뀌어도 같은 통장이다.
- 창구에서 받은 1만 원권은 어느 지폐인지 신경 쓰지 않는다. 금액과 통화만 맞으면 된다.

똑같은 구조다.\
실무 예: `Order`·`Member`·`Account`는 엔티티로, `Money`·`Address`·`DateRange`·`Email`은 값 객체로 두는 경우가 많다. 다만 **어느 쪽인지는 그 도메인이 "같음"을 어떻게 판단하느냐로 정해진다.** 같은 "주소"도 쇼핑몰에서는 값이고, 주소 자체를 관리하는 시스템(예: 우편번호 관리)에서는 엔티티일 수 있다(예시).

## 동작·원리

### 1. 두 종류의 "같음"

```text
                  엔티티(Entity)                         값 객체(Value Object)
  같음의 기준     식별자(id)                              모든 속성
  속성 변경       같은 객체가 상태를 바꾼다(수명 주기)       새 값을 만든다(불변)
  equals/hash     id 기반이거나 기본(참조) 그대로           속성 기반으로 재정의
  예              Order#42, Member#7                     Money(1000, KRW), Address("서울", ...)
  공유            공유하면 같은 것을 가리킨다               불변이면 공유해도 안전
```

- *엔티티*: 속성이 바뀌어도 이어지는 "정체성의 실(thread of identity)"을 가진 객체. Evans 『DDD Reference』(2015) Entities 항목은 "모델이 같은 것이란 무엇인지 정의해야 한다"고 적고, 각 객체를 형태·이력과 무관하게 구분할 수단(유일한 결과를 내는 연산, 고유 기호 부여)을 정의하라고 권한다. 별칭은 Reference Object.
- *값 객체*: 속성과 그 속성에 관한 로직만 중요한 요소. 같은 문서의 Value Objects 항목은 값 객체를 **불변으로 다루고**, 모든 연산을 가변 상태에 기대지 않는 부수 효과 없는 함수(Side-Effect-Free Functions)로 만들고, 식별성을 주지 말라고 권한다.
- Fowler "EvansClassification"(2005-12-14): 값은 `equals`(그래서 hash도)를 재정의하고 엔티티는 대개 하지 않는다는 것이 둘을 가르는 분명한 차이 중 하나라고 적는다.

### 2. 엔티티 — 식별자가 수명 주기를 잇는다

```text
  시간 →
  Member#7  [이름 김철수, 주소 서울, 등급 BASIC] ── 이사 ──> [주소 부산] ── 승급 ──> [등급 VIP]
            └───────────────── 같은 Member#7 (id가 이어 준다) ─────────────────┘

  식별자를 정하는 곳
   외부에서 받음      주민번호·ISBN·사업자번호 (자연 키)
   시스템이 만듦      DB 시퀀스·UUID (대리 키)
   생성 시점          생성자(앱이 할당) vs 저장할 때(DB가 할당)  ← equals 설계를 가른다
```

- *자연 키(natural key)*: 도메인에 원래 있는 고유 값(ISBN 등). 바뀔 수 있는지·재사용되는지 확인해야 한다.
- *대리 키(surrogate key)*: 의미 없이 시스템이 만든 값(시퀀스·UUID). 키 선택은 [database/28](../../database/28-key-strategy-surrogate-natural-public-id/2-summary.md)에서 다룬다.
- **식별자가 언제 생기느냐**가 `equals`를 정한다.
  - 생성자에서 할당(UUID 등) → 처음부터 `id`가 있으니 `id` 기반 `equals`가 안전하다.
  - DB가 저장 시점에 할당(`@GeneratedValue`) → 저장 전에는 `id == null`이다. `id` 기반 `hashCode`가 저장 전후로 바뀐다(실험 C).

### 3. 값 객체 — 속성이 곧 정체

```text
  가변 "값"                                  불변 값 객체
  Money m = cart.total();                    Money m = cart.total();
  m.amount += 500;   ← cart 안의 값도 바뀜    Money m2 = m.plus(won(500));   ← cart는 그대로
       (별칭 버그: 같은 객체를 두 곳이 공유)       (바꾸려면 새 값으로 교체)
```

- 값 객체가 해 주는 것
  - **동등성**: 속성 기반 `equals`/`hashCode` → 컬렉션·캐시 키·중복 제거가 의도대로 된다.
  - **불변성**: 공유해도 한쪽 수정이 다른 쪽으로 새지 않는다. 불변 규칙 자체는 [software-design/19](../../software-design/19-immutability-and-value-objects/2-summary.md)에서 다룬다.
  - **자기 검증**: 생성할 때 불변식을 검사한다(음수 금액 금지, 통화 필수). 만들어졌다면 유효하다.
  - **연산을 담는다**: `Money.plus`가 통화 일치를 검사한다. 원시값 `long`은 이 자리를 갖지 못한다.
- *원시값 집착(primitive obsession)*: 금액을 `long`, 이메일을 `String`처럼 원시 타입으로 들고 다니는 것. 단위·통화·형식 규칙이 타입에 없어 호출하는 곳마다 다시 검사해야 한다. 타입으로 막는 방법은 [software-design/24](../../software-design/24-types-as-invariants/2-summary.md).

### 실험 A·B: equals 없는 값, 통화 없는 금액

```java
static final class MoneyNoEq {                     // equals/hashCode 없음 → Object 기본(참조 동일성)
    final long amount; final String currency;
    MoneyNoEq(long a, String c) { amount = a; currency = c; }
}
record Money(long amount, String currency) {        // record → 구성 요소 기반 equals/hashCode
    Money { Objects.requireNonNull(currency); }
    Money plus(Money o) {
        if (!currency.equals(o.currency)) throw new IllegalArgumentException("통화 불일치: " + currency + " + " + o.currency);
        return new Money(amount + o.amount, currency);
    }
}
// A: HashSet에 같은 값을 두 번 add, List.remove(같은 값)
// B: long krwPrice = 1000; long usdPrice = 5; krwPrice + usdPrice  vs  Money.plus
```

(실험, JDK 21.0.12 eclipse-temurin `--cpus=2`, 2026-10-03, 3회 같은 결과)

```text
== A. 값 객체 equals 누락 → 컬렉션 중복
equals 없음: size=2, contains(같은 값)=false
record:     size=1, contains(같은 값)=true
equals 없음: list.remove(같은 값)=false, 남은 원소=1
== B. 원시값 집착(long) → 통화 혼합
long 합계 = 1005  (단위 없음, 컴파일·실행 모두 통과)
Money.plus → IllegalArgumentException: 통화 불일치: KRW + USD
```

- 관찰
  - `equals`가 없으면 같은 1000원이 집합에 둘 들어가고, 장바구니에서 500원짜리 줄을 지우지 못한다. 예외도 로그도 없다.
  - `long` 합계 1005는 아무 단위도 아니다. 컴파일러도 런타임도 막지 않는다. `Money.plus`는 섞는 순간 예외를 낸다.
- record의 자동 `equals`는 구성 요소를 각각 비교한다(JDK 21 `java.lang.Record.equals` 문서). 구성 요소가 `BigDecimal`이면 `BigDecimal.equals`가 scale까지 비교하므로 `1.0`과 `1.00`이 다르다(JDK 21 `BigDecimal.equals` 문서, [software-design/19](../../software-design/19-immutability-and-value-objects/2-summary.md) 실험). 금액 값 객체는 생성자에서 scale을 정규화한다.

### 4. JPA에서 엔티티와 값 객체

```text
  도메인 개념        JPA 매핑                  같음                      주의
  엔티티             @Entity + @Id             세션 안: 같은 행 = 같은 인스턴스   세션 밖·Set: equals 설계 필요
  값 객체(단일)      @Embeddable / @Embedded    소유 엔티티의 일부          엔티티끼리 공유 금지(JPA 3.1 §2.6)
  값 객체(여러 개)   @ElementCollection         소유 엔티티의 일부          식별자 없음, 통째 교체가 자연스러움
```

- Hibernate 6.6 User Guide "Implementing equals() and hashCode()"
  - 한 세션 안에서는 같은 DB 행을 여러 번 `find`해도 **같은 인스턴스**를 돌려준다(영속 식별성 = Java 식별성).
  - "절대적인 경우"는 하나라고 적는다: 식별자로 쓰는 클래스(복합 키 등)는 id 값 기반 `equals`/`hashCode`를 구현해야 한다.
  - 이 경우와 이어서 다루는 몇 가지 경우 밖에서는 구현하지 않는 것도 고려하라고 한다. 세션 밖(transient·detached)에서 Java 컬렉션에 넣는다면 구현을 고려하라고 한다.
  - **생성 ID 기반 `equals`/`hashCode`는 `Set`에서 깨진다.** ID가 저장할 때 채워지면서 hash가 바뀌기 때문이다. 대안으로 natural-id(업무 키) 기반, 또는 "hashCode는 상수, equals는 비일시(non-transient) 엔티티끼리만 id 비교"를 제시한다.
- Jakarta Persistence 3.1 §2.6: 임베디드 객체는 소유 엔티티에 엄격히 속하고, 엔티티 사이에 공유할 수 없다. **공유를 시도한 결과는 정의되지 않는다(undefined semantics).**

### 실험 C·D: Hibernate 6.6에서 엔티티 equals와 공유된 임베더블

```java
@Entity class BookById {                      // 생성 ID 기반 equals/hashCode (Hibernate 가이드의 "naive" 구현)
    @Id @GeneratedValue Long id; String isbn;
    public boolean equals(Object o) { return o instanceof BookById b && Objects.equals(id, b.id); }
    public int hashCode() { return Objects.hash(id); }
}
@Entity class BookConstHash {                 // 가이드의 우회: hashCode 상수 + 비일시 엔티티만 id 비교
    @Id @GeneratedValue Long id; String isbn;
    public boolean equals(Object o) { return o instanceof BookConstHash b && id != null && id.equals(b.id); }
    public int hashCode() { return getClass().hashCode(); }
}
@Embeddable class Address { String city; }   // 가변 임베더블
@Entity class Customer { @Id Long id; String name; @Embedded Address address; }

// C: set.add(book) → persist + commit → set.contains(book)
// D: lee.address = kim.address;  kim.address.city = "Busan";  → 커밋 후 두 행 조회
```

(실험, JDK 21.0.12 eclipse-temurin `--cpus=2`, Hibernate ORM 6.6.29.Final, H2 2.3.232 메모리 DB, 2026-10-03, 3회 같은 결과. Hibernate 로그 줄은 뺐다)

```text
== C. 엔티티 equals/hashCode를 생성 ID로 → 저장 후 Set에서 못 찾음
저장 전 id=null, contains=true
저장 후 id=1, contains=false, size=1, remove=false
상수 hashCode: 저장 후 id=1, contains=true
다른 세션에서 두 번 로드: ==false, equals=true
== D. 가변 @Embeddable 인스턴스 공유 → 한 엔티티만 고쳤는데 두 행이 바뀜
customer 1 kim city=Busan
customer 2 lee city=Busan
```

- C 관찰
  - 저장 뒤 `id`가 `null → 1`로 바뀌면서 hash 버킷이 어긋났다. 원소는 집합에 있는데(`size=1`) 찾지도(`contains=false`) 지우지도(`remove=false`) 못한다.
  - 상수 `hashCode` 우회는 저장 뒤에도 찾는다. 대가로 그 클래스의 원소가 모두 한 버킷에 모인다(큰 집합에서 조회가 느려진다 — 가이드가 "workaround"라고 부르는 이유로 해석).
  - 서로 다른 세션에서 읽은 두 인스턴스는 `==`로는 다르지만 `id` 기반 `equals`로는 같다. 세션 밖에서 엔티티를 비교할 때 `equals`가 필요한 이유다.
- D 관찰: 같은 `Address` 인스턴스를 두 엔티티가 공유한 상태에서 kim만 이사시켰는데, lee의 행도 부산으로 저장됐다. JPA 3.1에서는 정의되지 않은 동작이고, 위 결과는 Hibernate 6.6.29에서 관찰한 것이다.

같은 실험을 불변 record 임베더블로 바꾸면(Hibernate 6.6.29, 같은 환경):

```java
@Embeddable public record Address(String city) {}
// kim.moveTo(new Address("Busan"))   ← 바꾸는 방법이 "교체"뿐
```

```text
customer 1 kim city=Busan
customer 2 lee city=Seoul
```

- 불변이면 공유해도 바꿀 수 있는 길이 교체뿐이다. 그래서 lee는 영향을 받지 않는다.

## 쓰이는 자료구조·알고리즘

- **해시 테이블**: `HashSet`·`HashMap`은 `hashCode`로 버킷을 고르고 `equals`로 확인한다. 키의 hash가 넣은 뒤 바뀌면 원소가 "보이지 않게" 된다 — [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md), `equals`/`hashCode` 계약은 [java/syntax/27](../../../languages/java/syntax/27-equals-hashcode-contract/2-summary.md).
- **식별자 맵(Identity Map)**: Hibernate 세션이 같은 행을 같은 인스턴스로 돌려주는 장치(PoEAA Identity Map). 세션 범위 안에서만 성립한다.
- **구조적 동등성 비교**: record의 자동 `equals`는 모든 구성 요소가 같을 때만 true다. 비교 순서와 구체 알고리즘은 명세되지 않았다(JDK 21 `Record.equals` 문서). 컬렉션 구성 요소가 있으면 그 컬렉션의 `equals`(순서 포함 여부)도 따라온다.
- **ID 생성**: DB 시퀀스·IDENTITY(저장 때 할당) vs UUID·Snowflake류(앱에서 할당) — [distributed/13](../../distributed/13-distributed-id-generation/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 엔티티인가 값인가 — 묻는 순서

```text
  1) 속성이 다 같은 두 개를 "둘"로 세야 하나?        예 → 엔티티 후보
  2) 속성이 바뀌어도 "같은 것"으로 추적해야 하나?    예 → 엔티티
  3) 둘 다 아니고, 속성과 그 계산만 중요한가?        예 → 값 객체 (기본값으로 먼저 의심)
  4) 엔티티라면: 식별자는 누가 언제 만드나?          → equals/hashCode 방식 결정
```

- 기본값을 값 객체로 두고, 추적이 필요할 때만 엔티티로 올리는 쪽이 단순하다. Evans 『DDD Reference』도 식별성을 붙이면 성능·분석 작업·모델 혼란의 비용이 든다고 적는다.

### 2. 코드 (Java 21)

```java
// 값 객체: 불변 + 자기 검증 + 연산
public record Money(BigDecimal amount, Currency currency) {
    public Money {
        Objects.requireNonNull(amount); Objects.requireNonNull(currency);
        if (amount.signum() < 0) throw new IllegalArgumentException("음수 금액");
        amount = amount.setScale(currency.getDefaultFractionDigits(), RoundingMode.UNNECESSARY); // scale 정규화(자릿수 초과면 ArithmeticException)
    }
    public Money plus(Money o) {
        if (!currency.equals(o.currency)) throw new IllegalArgumentException("통화 불일치");
        return new Money(amount.add(o.amount), currency);
    }
}

// 엔티티: 식별자를 생성자에서 할당 → 처음부터 id 기반 equals가 안전
public class Order {
    private final OrderId id;                 // 값 객체로 감싼 식별자
    private OrderStatus status;
    public Order(OrderId id) { this.id = Objects.requireNonNull(id); this.status = OrderStatus.CREATED; }
    @Override public boolean equals(Object o) { return o instanceof Order other && id.equals(other.id); }
    @Override public int hashCode() { return id.hashCode(); }
}
public record OrderId(UUID value) { public static OrderId newId() { return new OrderId(UUID.randomUUID()); } }
```

- `Currency.getDefaultFractionDigits()`는 통화의 기본 소수 자릿수를 준다. JDK 21.0.12에서 KRW 0·USD 2·JPY 0·KWD 3으로 출력됐다(ISO 4217 표의 minor unit과 같은 값 — SIX `list-one.xml` 2026-09-17 공표판에서 KRW 0·USD 2·JPY 0·KWD 3 확인). 자릿수를 넘는 금액은 `setScale(…, UNNECESSARY)`가 `ArithmeticException: Rounding necessary`를 낸다(같은 환경에서 실행 확인, `Cur.java`). 통화별 반올림·배분은 [12-time-money-and-units](../12-time-money-and-units/2-summary.md)·[14-money-arithmetic-rounding-allocation](../14-money-arithmetic-rounding-allocation/2-summary.md).
- JPA에서 `@GeneratedValue`를 꼭 써야 하면: 업무 키(natural id) 기반 `equals`, 또는 Hibernate 가이드의 상수 `hashCode` 우회(실험 C)를 쓴다. 저장 전 엔티티를 `Set`에 넣는 코드가 있는지 먼저 찾는다. 위 `Order`·실험 C 코드는 상대의 `id`를 필드로 읽는데, 상대가 Hibernate 지연 프록시면 그 필드는 `null`이다 — JPA 엔티티에서는 `instanceof` + getter로 비교한다([02](../02-pojo-and-persistence-ignorance/2-summary.md) 실험 2).
- `@Embeddable` 값 객체는 불변(record 또는 final 필드)으로 만들고, 바꿀 때는 교체한다(실험 D).

### 3. 진단

```bash
# setter가 있는 "값" 클래스 후보
grep -rn --include=*.java -E 'class (Money|Address|Amount|Price|.*Range)\b' src | cut -d: -f1 | xargs grep -ln 'void set'
# @GeneratedValue 엔티티 중 equals가 id만 쓰는 곳
grep -rln --include=*.java '@GeneratedValue' src | xargs grep -ln 'Objects.hash(id)'
# 금액을 원시 타입으로 들고 다니는 필드
grep -rn --include=*.java -E '(long|int|double) +(price|amount|fee|total)\w*' src
```

```java
// 값 객체 동등성 테스트: 같은 값의 서로 다른 인스턴스 둘이 집합에 하나만 남는다
// (Set.of는 원소 하나면 항상 size 1, 같은 값 둘이면 IllegalArgumentException — 검증이 안 된다)
assertEquals(Money.won(1000), Money.won(1000));
Set<Money> s = new HashSet<>(); s.add(Money.won(1000)); s.add(Money.won(1000));
assertEquals(1, s.size());
// 엔티티 equals 회귀 테스트: 저장 전후로 Set에서 찾을 수 있다
Set<Book> set = new HashSet<>(); set.add(book); em.persist(book); em.flush();
assertTrue(set.contains(book));
```

## 장애 시나리오와 대처

### 1. 값 객체 equals 누락 → 컬렉션 중복 (⚠ 커리큘럼)

- **현상**: 쿠폰 목록에 같은 쿠폰이 두 번 보인다. 장바구니에서 항목 삭제가 안 된다.
- **보이는 형태**: 에러 없음. `Set.size()`가 기대보다 크고, `remove`가 `false`를 돌려준다(실험 A). 캐시 히트율이 0에 가깝다(키가 매번 새 객체라 다른 키로 취급).
- **원인**: 값처럼 쓰는 클래스가 `Object`의 참조 동일성을 그대로 쓴다.
- **대처**: record로 바꾸거나 모든 속성 기반 `equals`/`hashCode`를 구현한다. 집합·맵 키로 쓰는 타입에 동등성 테스트를 둔다.

### 2. 원시값 집착 — 금액을 `long`으로 → 통화 혼합 (⚠ 커리큘럼)

- **현상**: 해외 결제가 섞인 정산에서 합계가 터무니없다(원화 1000 + 달러 5 = 1005).
- **보이는 형태**: 컴파일·실행 모두 통과(실험 B). 정산 대사에서 차이가 나거나 고객 문의로 발견된다.
- **원인**: 금액에 통화가 붙어 있지 않아서, 섞는 순간을 막을 자리가 없다.
- **대처**: `Money(amount, currency)` 값 객체를 두고 연산에서 통화 일치를 검사한다. DB에도 금액·통화 컬럼을 짝으로 둔다. 표준 API로는 JSR 354(`javax.money.MonetaryAmount`)가 금액과 통화를 한 값으로 묶는다.

### 3. 생성 ID 기반 equals → 저장 후 Set에서 엔티티를 못 찾음

- **현상**: 새 주문 줄을 `Set`에 넣고 저장했더니, 같은 요청 안에서 그 줄을 지울 수 없다. 중복 줄이 생긴다.
- **보이는 형태**: `contains=false`, `remove=false`인데 `size`는 그대로(실험 C). 예외 없음.
- **원인**: `@GeneratedValue` id가 저장 시점에 `null → 값`으로 바뀌면서 `hashCode`가 바뀌었다. `Set`의 계약(원소의 equals/hash가 집합 안에 있는 동안 바뀌면 안 된다)을 어겼다(Hibernate 6.6 가이드 Example 142).
- **대처**: 앱에서 ID를 미리 할당(UUID)하거나, 업무 키 기반 `equals`, 또는 상수 `hashCode` 우회. `List`로 바꾸는 것은 중복 검사 의미가 사라지므로 주의한다.

### 4. 가변 임베더블 공유 → 한 엔티티 수정이 다른 행에 저장

- **현상**: 고객 한 명의 주소를 바꿨는데 다른 고객 주소도 바뀌었다.
- **보이는 형태**: 감사 로그에 요청하지 않은 고객의 UPDATE가 찍힌다(실험 D: 두 행 모두 `city=Busan`).
- **원인**: 같은 `@Embeddable` 인스턴스를 두 엔티티가 참조한 채 그 필드를 고쳤다. JPA 3.1 §2.6은 이 공유를 정의되지 않은 동작으로 둔다.
- **대처**: 임베더블을 불변으로 만들고 교체로만 바꾼다(record 임베더블 실험에서 lee는 그대로). 복사해서 넘기는 코드(`new Address(other.city)`)를 쓴다.

### 5. 엔티티여야 할 것을 값으로 모델링 → 이력·추적 불가

- **현상**: "배송지 A를 쓰던 주문들을 찾아 달라"는 요구에 답할 수 없다. 배송지를 수정하면 과거 주문의 배송지도 바뀐 것처럼 보인다.
- **보이는 형태**: 과거 주문 화면이 현재 주소를 보여 준다(값이 아니라 참조로 연결했을 때). 또는 주소 행이 복사되어 "같은 배송지"를 묶을 키가 없다.
- **원인**: 도메인에서 그 개념이 추적 대상(수명 주기)인지 묻지 않았다.
- **대처**: 주문 시점의 배송지는 **값으로 복사**(스냅숏)하고, 주소록 항목처럼 추적이 필요한 것은 엔티티로 둔다. 한 개념이 두 역할을 할 수 있다.

## 핵심 문장

- 엔티티는 식별자로, 값 객체는 속성으로 같음을 판단한다. 어느 쪽인지는 도메인이 "같음"을 어떻게 정의하느냐로 정한다.
- 값 객체는 불변·속성 기반 동등성·자기 검증·연산을 함께 갖는다. `equals`가 없으면 컬렉션이 조용히 중복을 받아들인다.
- 금액을 `long`으로 들고 다니면 통화를 섞는 순간을 막을 자리가 없다.
- 엔티티 `equals`는 식별자가 언제 생기는지에 달려 있다. DB가 저장할 때 id를 채우면, id 기반 hash는 `Set` 안에서 바뀐다(Hibernate 6.6 가이드·실험).
- JPA 임베더블은 엔티티끼리 공유하지 않는다. 불변으로 두면 공유해도 교체만 가능해 새지 않는다.

## 관련 주제·근거

- 선행
  - [03-ubiquitous-language](../03-ubiquitous-language/2-summary.md) — "같은 주문"·"같은 회원"의 뜻을 용어로 정한다
  - [software-design/19-immutability-and-value-objects](../../software-design/19-immutability-and-value-objects/2-summary.md) — 불변 규칙, 해시 키 변이, record 얕은 불변, `BigDecimal` scale
- 후속·연결
  - [05-aggregates-and-invariants](../05-aggregates-and-invariants/2-summary.md) — 엔티티·값 객체를 묶는 일관성 경계
  - [12-time-money-and-units](../12-time-money-and-units/2-summary.md) · [14-money-arithmetic-rounding-allocation](../14-money-arithmetic-rounding-allocation/2-summary.md) — 금액 값 객체 심화
  - [software-design/24-types-as-invariants](../../software-design/24-types-as-invariants/2-summary.md) — 원시 타입 집착 제거
  - [database/28-key-strategy-surrogate-natural-public-id](../../database/28-key-strategy-surrogate-natural-public-id/2-summary.md) · [database/51-object-relational-structural-mapping](../../database/51-object-relational-structural-mapping/2-summary.md)
  - [java/syntax/27-equals-hashcode-contract](../../../languages/java/syntax/27-equals-hashcode-contract/2-summary.md) · [java/syntax/14-records](../../../languages/java/syntax/14-records/2-summary.md)
  - 연습: [basic/01-parking-fee](../basic/01-parking-fee/2-summary.md)(요금 정책 값) · [basic/25-org-chart](../basic/25-org-chart/2-summary.md)(값 객체가 막는 규칙 vs 컬렉션이 막는 규칙)
- 글·문서
  - Eric Evans, 『Domain-Driven Design Reference』(2015, CC BY 4.0) "Entities"·"Value Objects" 항목 <https://www.domainlanguage.com/ddd/reference/>
  - Eric Evans, 『Domain-Driven Design』(2003) 5장 "A Model Expressed in Software" — ENTITIES·VALUE OBJECTS 절(InformIT 목차로 확인, 본문 미열람)
  - Vaughn Vernon, 『Implementing Domain-Driven Design』(2013) 5장 Entities·6장 Value Objects(목차 확인, 본문 미열람)
  - Martin Fowler, "EvansClassification"(2005-12-14) <https://martinfowler.com/bliki/EvansClassification.html> · "ValueObject"(2016-11-14) <https://martinfowler.com/bliki/ValueObject.html>
  - Hibernate ORM 6.6 User Guide "Implementing equals() and hashCode()"(Example 136~145) <https://docs.hibernate.org/orm/6.6/userguide/html_single/Hibernate_User_Guide.html>
  - Jakarta Persistence 3.1 §2.6 Embeddable Classes <https://jakarta.ee/specifications/persistence/3.1/jakarta-persistence-spec-3.1.html>
  - JDK 21 API `java.lang.Record`·`java.math.BigDecimal`·`java.util.Currency`
- 실험 목록 (코드: scratchpad `dm/04/e04/Ev.java`·`Ev2.java`, JDK 21.0.12 eclipse-temurin `--cpus=2`, Hibernate ORM 6.6.29.Final + H2 2.3.232 메모리 DB, `javac -cp 'libs/*' -d out Ev.java && java -cp 'out:libs/*' Ev`, 3회)
  - A `equals` 없는 값 vs record — `HashSet` 크기·`contains`·`List.remove`
  - B `long` 합계 vs `Money.plus` 통화 검사
  - C 생성 ID 기반 `equals` vs 상수 `hashCode` — 저장 전후 `Set` 조회, 다른 세션 두 인스턴스 비교
  - D 가변 `@Embeddable` 공유 vs record 임베더블 교체(`Ev2.java`)
  - 통화 기본 소수 자릿수·`setScale(UNNECESSARY)` — `java Cur.java`
