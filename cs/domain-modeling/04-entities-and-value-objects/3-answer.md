# domain-modeling/04-entities-and-value-objects — 정답

## 정답

### 1. 두 종류의 같음

- 엔티티: **식별자**로 판단한다. 속성이 바뀌어도 같은 것으로 이어지고, 속성이 다 같아도 식별자가 다르면 다른 것이다.
- 값 객체: **모든 속성**으로 판단한다. 속성이 같으면 같은 것이다.
- 어느 쪽인지는 그 도메인이 "같음"을 어떻게 정의하느냐로 정한다.
  - 쇼핑몰의 주문 배송지: 문자열이 같으면 같은 주소 → 값.
  - 주소 자체를 등록·변경·폐지하며 추적하는 시스템: 주소가 수명 주기를 가진다 → 엔티티(예시).
- Evans 『DDD Reference』 Entities 항목: "모델이 같은 것이란 무엇인지 정의해야 한다."

### 2. 값 객체의 성질과 별칭 버그

- 『DDD Reference』 Value Objects 항목
  1. 불변으로 다룬다.
  2. 모든 연산을 가변 상태에 기대지 않는 부수 효과 없는 함수로 만든다.
  3. 식별성을 주지 않는다(속성의 뜻을 표현하고 관련 기능을 담는다).

```text
  가변 Money
  cart.total ──┐
               ├──> Money{amount=1000}      m.amount += 500
  m ───────────┘                            → cart.total도 1500 (같은 객체)

  불변 Money
  cart.total ───> Money{1000}
  m2 ───────────> Money{1500}   ← plus가 새 값을 만든다
```

### 3. equals 없는 값 vs record

- `equals` 없음: `size=2`, `contains(같은 값)=false`. `List.remove(같은 값)`도 `false`.
- record: `size=1`, `contains=true`. record의 자동 `equals`는 구성 요소를 비교한다(JDK 21 `Record.equals`).
- 근거: 실험 A(JDK 21.0.12, 3회 같은 결과).

### 4. 생성 ID 기반 equals와 Set

- 실험 C 출력(Hibernate 6.6.29 + H2 2.3.232)

```text
저장 전 id=null, contains=true
저장 후 id=1, contains=false, size=1, remove=false
```

- `contains=false`, `remove=false`, `size=1`.
- 이유: `hashCode = Objects.hash(id)`가 저장 전에는 `null`의 hash, 저장 뒤에는 `1`의 hash다. 원소는 옛 버킷에 있는데 조회는 새 버킷을 본다. `Set`은 원소가 들어 있는 동안 equals/hash가 바뀌지 않는다고 가정한다(Hibernate 가이드 Example 142의 설명).

### 5. Hibernate 가이드의 입장

- 가이드가 "절대적"이라고 부르는 경우: **식별자로 쓰는 클래스**(복합 키 등)는 id 값 기반 `equals`/`hashCode`를 구현해야 한다.
- 이 경우와 이어서 다루는 몇 가지 경우 밖에서는 구현하지 않는 것도 고려하라고 한다. 세션 밖(transient·detached)에서 컬렉션에 넣는다면 구현을 고려한다.
- 생성 ID 엔티티의 대안
  - natural-id(업무 키, 예: ISBN) 기반 `equals`/`hashCode` — 가이드가 "best"라고 적는다. 대가: 업무 키가 있어야 하고, 그 키가 바뀌면 같은 문제가 생긴다.
  - `hashCode`는 상수, `equals`는 비일시 엔티티끼리만 id 비교 — 실험에서 저장 뒤에도 `contains=true`. 대가: 그 타입이 모두 한 버킷에 모여 큰 집합에서 조회가 느려진다(해석).
- 그 밖에 저장(flush)을 먼저 해 id를 받은 뒤 넣는 방법도 가이드에 있지만, 가이드는 "자주 실현 불가능하다"고 적는다.

### 6. 공유된 가변 임베더블

- 원인: 같은 `Address` 인스턴스를 두 엔티티가 참조하는 상태에서 필드를 고쳤다. 플러시할 때 두 엔티티 모두 바뀐 상태로 보여 두 행이 갱신됐다. 실험 D(Hibernate 6.6.29)에서 kim만 이사시켰는데 lee도 `city=Busan`.
- JPA 3.1 §2.6: 임베디드 객체는 소유 엔티티에 엄격히 속하고 공유할 수 없으며, 공유를 시도한 결과는 정의되지 않는다.
- 대처
  - 임베더블을 불변(record·final 필드)으로 만들고 교체로만 바꾼다. record 임베더블 실험에서는 lee가 `Seoul` 그대로였다.
  - 다른 엔티티의 값을 쓸 때는 복사한다.

### 7. `long` 금액

- 컴파일러가 막지 못한 이유: `long + long`은 타입 검사에 걸리지 않는다(오버플로는 별개 문제). 통화가 타입에 없으니 섞는 순간을 검사할 자리가 없다. 실험 B에서 1000 + 5 = 1005가 아무 경고 없이 나왔다.
- 테스트가 막지 못한 이유: 단일 통화 데이터로만 테스트했다면 혼합 경로가 실행되지 않는다(해석).
- 값 객체: `Money(amount, currency)`의 `plus`가 통화 일치를 검사한다 → `IllegalArgumentException: 통화 불일치: KRW + USD`. DB에도 금액·통화를 짝으로 저장한다.

### 8. BigDecimal scale

- 다르다. `BigDecimal.equals`는 값과 scale을 모두 비교한다(JDK 21 문서). 그래서 record의 자동 `equals`도 `1.0`과 `1.00`을 다르다고 본다.
- 생성자에서 통화의 기본 소수 자릿수로 scale을 정규화한다.
  - `Currency.getDefaultFractionDigits()`: JDK 21.0.12에서 KRW 0·USD 2·JPY 0·KWD 3.
  - `setScale(digits, RoundingMode.UNNECESSARY)`는 자릿수를 넘는 값에 `ArithmeticException`을 내므로, 반올림이 필요한 입력을 조용히 바꾸지 않고 거절한다.

### 9. 배송지: 복사 vs 참조

- 값으로 복사(주문 시점 스냅숏)
  - 장점: 주소록을 고쳐도 과거 주문의 배송지는 그대로다.
  - 답할 수 없게 되는 요구: "주소록 항목 A를 쓴 주문들"처럼 주소록 항목 단위로 묶는 질문(묶을 식별자가 없다). 필요하면 원본 주소록 id를 함께 기록한다.
- 주소록 엔티티를 참조
  - 답할 수 없게 되는 요구: "주문 당시 어디로 보냈나" — 주소록이 바뀌면 과거 주문도 바뀐 것처럼 보인다.
- 흔한 선택: 주문에는 값으로 복사하고, 주소록은 엔티티로 둔다. 한 개념이 두 역할을 맡는다.
