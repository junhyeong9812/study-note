# software-design/19-immutability-and-value-objects — 불변 객체와 값 의미론: 공유해도 새지 않게 — 정리 (힌트)

## 해결하는 문제

객체 하나를 여러 곳이 가리키면, 한 곳의 변경이 다른 곳에 보인다. 그 객체가 "값"(금액·날짜·기간·좌표)이라면 이것은 대개 버그다.

```text
 가변 Money를 캐시가 공유             불변 Money를 캐시가 공유
 cache["basic"] ─┐                  cache["basic"] ──> Money(3000)  (그대로)
                 ▼                         │ add(500)
 요청 A ──> [3000 → 3500]  add(500)        └──────────> Money(3500)  새 객체 → 요청 A만
 요청 B ──> [   3500    ]  기본 요금?        요청 B ──> Money(3000)
           (A의 할증이 B에 샜다)
```

- *불변 객체(immutable object)*: 만들어진 뒤 관측 가능한 상태가 바뀌지 않는 객체. 바꾸고 싶으면 새 객체를 만든다(`String`·`LocalDate`·`BigDecimal`).
- *값 객체(value object)*: 식별자가 아니라 **값으로 같음을 판단**하는 객체. 3000원은 어느 3000원이든 같다. Fowler는 값 객체의 동등성이 값에 기반하고, 별칭 버그(aliasing bug)를 피하려면 값 객체는 불변이어야 한다고 적는다(bliki "ValueObject", 2016-11-14).
- *별칭(aliasing)*: 같은 객체를 두 이름(참조)이 가리키는 것. 한쪽을 통해 바꾸면 다른 쪽에도 보인다.

쉬운 예: 지폐는 불변이다. 1만 원권에 "+5천"이라고 써도 1만5천 원권이 되지 않는다. 거스름돈은 새 지폐로 받는다. 반면 공유 화이트보드의 숫자는 누군가 고쳐 쓰면 모두에게 바뀐다.\
똑같은 구조다.\
실무 예: 요금 정책 캐시가 가변 `Money`를 돌려줘서, 야간 할증을 계산하던 요청이 캐시 안의 값 자체를 바꿨다. 이후 요청들이 할증 요금을 냈다. 또 `HashSet`에 넣은 주문 키 객체의 필드를 나중에 바꾸자 그 주문을 다시는 찾지도 지우지도 못했다.

불변 클래스를 **만드는 문법**(final 필드·final 클래스·방어 복사 들어올 때·나갈 때·`this` 유출·record의 compact 생성자)은 [java/syntax/59-immutable-objects](../../../languages/java/syntax/59-immutable-objects/2-summary.md)에 자세히 있다. 이 노트는 **언제 불변으로 설계하나, 무엇이 깨지나, 비용은 얼마인가**를 본다.

## 동작·원리

### 1. 불변 객체의 규칙 (Oracle Java Tutorial)

Oracle Java Tutorial "A Strategy for Defining Immutable Objects"의 규칙(요약):

```text
 1. setter 없음 — 필드나 필드가 가리키는 객체를 바꾸는 메서드를 두지 않는다
 2. 필드는 private final
 3. 하위 클래스가 메서드를 재정의하지 못하게 (final 클래스, 또는 private 생성자 + 팩토리)
 4. 필드가 가변 객체를 가리키면:
      그 객체를 바꾸는 메서드를 두지 않는다
      생성자로 받은 가변 객체는 복사해서 저장하고, 내보낼 때도 복사본을 준다
```

- Bloch 『Effective Java』 3판 Item 17 제목이 "Minimize mutability"다(Pearson 목차). 예제 `Complex`(불변 복소수, 81~82쪽)와 Item 50 "Make defensive copies when needed"의 깨진 `Period`(231~233쪽)가 저자 GitHub에 있다(쪽 번호는 GitHub 예제 주석 기준). `Period`는 `final Date` 필드를 가졌지만 생성자에 넘긴 `Date`를 밖에서 `setYear`로 바꿔 내부를 공격한다.
- 튜토리얼도 "Not all classes documented as "immutable" follow these rules"라고 적는다. 규칙은 충분조건에 가까운 단순한 전략이다.

### 2. 값 의미론: 같음을 무엇으로 판단하나

```text
 동일성(identity)  a == b          같은 객체인가 (주소)
 동등성(equality)  a.equals(b)     같은 값인가  (record는 모든 구성 요소로 자동 생성)

 값 객체:  equals = 값 비교, hashCode = 값에서 계산, 상태 변경 없음
           → 같은 값이면 어느 인스턴스를 써도 된다 → 마음껏 공유·캐시·해시 키로 쓴다
```

- 값 의미론의 전제가 **불변**이다. `hashCode`가 값에서 계산되는데 값이 바뀌면 해시 자료구조가 깨진다(실험 B).
- Java `record`(JDK 16, JEP 395)는 값 객체를 짧게 쓰게 해 준다. `equals`·`hashCode`·`toString`·접근자를 구성 요소로 만든다. 단 JDK 21 `Record` API 문서 표현으로 record는 "shallowly immutable"이다(실험 C).

### 실험 A: 공유 가변 객체가 요청 사이로 샌다

```java
static class MutableMoney { long amount; MutableMoney add(long x) { amount += x; return this; } ... }
record Money(long amount, String currency) { Money add(long x) { return new Money(amount + x, currency); } }

MutableMoney feeA = feeCacheMut.get("basic").add(500);   // 요청 A: 야간 할증
MutableMoney feeB = feeCacheMut.get("basic");            // 요청 B: 기본 요금
```

(실험, JDK 21.0.12 eclipse-temurin `--cpus=2`, `scratchpad/sd/15/e19/Immut.java`, 2026-10-01)

```text
== 1. 공유 가변 객체: 요청 A의 할증이 요청 B로 샌다
  가변: A=3500 KRW, B=3500 KRW, 캐시=3500 KRW, A==B 같은 객체? true
  불변: A=3500 KRW, B=3000 KRW, 캐시=3000 KRW
```

- 가변판의 `add`는 `this`를 바꾸고 돌려줬다. A와 B와 캐시가 **같은 객체**다.
- 불변판의 `add`는 새 객체를 돌려줬다. 캐시 값은 3000 그대로다.

### 실험 B: 해시 키를 넣은 뒤 바꾸면

```text
 HashSet 버킷(해시 "A" 자리)  ── [Key code="A" → 나중에 "B"로 바뀜]
 contains(k)        → 해시 "B" 자리를 본다 → 없다
 contains(Key "A")  → 해시 "A" 자리를 본다 → 객체는 있지만 equals("A")가 거짓 → 없다
```

(실험, 같은 환경)

```text
== 2. HashSet에 넣은 뒤 키를 바꾸면
  size=1, contains(k)=false, contains(new Key("A"))=false, contains(new Key("B"))=false
  remove(k) 후 size=1  (지울 수도 없다)
```

- 원소는 그대로 있는데(`size=1`) 어떤 방법으로도 찾을 수 없고 지울 수도 없다. 반복 실행되면 메모리 누수처럼 쌓인다.
- JDK 21 `Set` API 문서: 원소로 넣은 가변 객체의 값이 `equals` 비교에 영향을 주게 바뀌면 집합의 동작은 명세되지 않는다("The behavior of a set is not specified…"). `Map`의 키도 같은 주의가 있다.

### 실험 C: record는 얕게 불변

```java
record OrderShallow(String id, List<String> items) {}
record OrderDeep(String id, List<String> items) { OrderDeep { items = List.copyOf(items); } }
```

(실험, 같은 환경)

```text
== 3. record는 얕게 불변
  OrderShallow.items=[pen, SECRET-ITEM], OrderDeep.items=[pen]
  OrderDeep.items().add -> UnsupportedOperationException
== 4. unmodifiableList(뷰) vs List.copyOf(복사)
  원본에 b 추가 후 view=[a, b], copy=[a]
```

- `OrderShallow`는 생성자에 넘긴 리스트를 그대로 붙잡아, 밖에서 추가한 항목이 주문 안에 들어왔다.
- compact 생성자에서 `List.copyOf`로 복사하면 바깥 변경이 안 들어오고, 꺼낸 리스트도 수정할 수 없다.
- `Collections.unmodifiableList`는 **뷰**다(API 문서 "an unmodifiable view of the specified list"). 원본이 바뀌면 뷰에도 보인다. 스냅샷이 필요하면 `List.copyOf`.

### 3. 불변이 동시성에 주는 것과 주지 않는 것

```text
 불변 값 공유 ── 여러 스레드가 읽기만 → 락 없이 안전 (바뀌는 것이 없으므로)
 "현재 값" 교체 ── 참조를 새 객체로 바꾸는 일 → 이것은 여전히 경쟁 → 원자적 교체(CAS)나 락이 필요
```

(실험, 같은 환경 — 스레드 4개 × 5만 번 증가, 아래는 집필 1회차 출력)

```text
== 5. 동시 공유: 가변 카운터 vs 불변 값 + 원자 교체
  기대=200000, 가변 long[] 합=197936, 불변 Money+AtomicReference=200000
```

- 집필 3회 실행에서 가변 `long[]`의 합은 197936·194596·195416이었고, 사실 점검 재실행 5회(같은 환경)는 197162~198092였다. 실행마다 다르고 8회 모두 200000에 못 미쳤다. 증가가 경쟁으로 유실됐다.
- `AtomicReference<Money>`의 `updateAndGet(m -> m.add(1))`는 8회 모두 200000이었다. 정확성은 **CAS 재시도**가 만든다. 불변이 하는 일은 "읽는 쪽이 반쯤 바뀐 객체를 보지 않게" 하는 것이다. 불변만으로 "갱신"이 안전해지지는 않는다.
- final 필드의 안전 공개(생성자가 끝난 뒤 다른 스레드가 final 필드를 초기값으로 본다)는 [java/syntax/59](../../../languages/java/syntax/59-immutable-objects/2-summary.md) 「안전 공개」 절. 락·CAS 일반은 [os/16-locks-and-spinlocks](../../os/16-locks-and-spinlocks/2-summary.md).

### 4. 비용과 영속 자료구조

- 불변은 변경마다 새 객체를 만든다. 필드 몇 개짜리 값 객체는 싸지만, 원소 100만 개 리스트에 하나를 더하려고 전체를 복사하면 비싸다.
- *영속 자료구조(persistent data structure)*: 변경해도 옛 버전이 그대로 남고, 새 버전이 옛 버전의 대부분을 **공유**하는 구조. 복사 비용을 바뀐 경로만큼으로 줄인다.

```text
 v1:        [b] -> [c]
 v2: [a] ->  ↑ (v1을 그대로 가리킨다 — 복사 없음)
```

(실험, 같은 환경)

```text
== 6. 영속 리스트: 구조 공유
  v1=[b,c], v2=[a,b,c], v2.tail()==v1? true
```

- 단방향 연결 리스트 앞에 붙이기는 O(1)이고 꼬리를 공유한다. 트리 기반 영속 구조(경로 복사)는 [data-structure/26-persistent](../../data-structure/26-persistent/2-summary.md).
- JDK의 `List.copyOf`·`List.of`는 영속 구조가 아니다. 수정 연산이 없고, 변경하려면 새로 복사한다.

### 실험 D: 불변 API의 반대쪽 함정 — 결과를 버리기

(실험, 같은 환경)

```text
== 7. BigDecimal은 불변 — 결과를 버리면 아무 일도 없다
  total.add(5) 후 total=100, 대입하면=105
```

- 불변 객체의 "변경" 메서드는 새 객체를 돌려준다. 돌려받은 값을 버리면 아무 일도 안 일어난다. 에러도 없다.

## 쓰이는 자료구조·알고리즘

- **해시 테이블과 키 불변식** — 원소의 버킷 위치는 넣을 때의 `hashCode`로 정해진다. 키가 바뀌면 위치와 값이 어긋나 조회·삭제가 실패한다(실험 B). 구조는 [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md).
- **영속 자료구조(구조 공유)** — 새 버전이 옛 버전의 노드를 가리킨다. 연결 리스트는 꼬리 공유, 트리는 경로 복사로 O(log n) 노드만 새로 만든다. [data-structure/26-persistent](../../data-structure/26-persistent/2-summary.md).
- **CAS 루프** — "현재 값 읽기 → 새 불변 값 계산 → 비교 후 교체, 실패하면 다시". 불변 값과 짝을 이루는 갱신 방법(실험 5절).
- **값 동등성 = 구성 요소별 비교** — record의 `equals`·`hashCode`는 구성 요소 전부로 계산된다. 구성 요소가 가변이면 동등성도 시간에 따라 바뀐다.

## 적용 — 풀어나가는 법

### 1. 무엇을 불변으로 만드나

1. **값**(금액·수량·기간·주소·좌표·ID·이메일)은 불변 값 객체로. 생성 시점에 검증하고 null을 거절한다([18](../18-absence-and-null-design/2-summary.md)).
2. **공유되는 것**(캐시 값·설정·상수·이벤트·메시지)은 불변으로. 공유하는 순간 별칭이 생긴다.
3. **해시 키·정렬 키**로 쓰는 것은 불변으로(실험 B).
4. **엔티티**(식별자가 있고 생애 동안 상태가 바뀌는 것: 주문·회원)는 가변일 수 있다. 대신 상태 변경 메서드로만 바꾸고, 엔티티가 가진 값들은 불변 값 객체로 둔다. 엔티티와 값 객체의 구분은 domain-modeling 04 entities-and-value-objects — 미작성([domain-modeling 커리큘럼](../../domain-modeling/curriculum.md)).

### 2. 코드 (Java 21)

```java
public record Money(BigDecimal amount, Currency currency) {
    public Money {
        Objects.requireNonNull(amount, "amount");
        Objects.requireNonNull(currency, "currency");
        if (amount.scale() > currency.getDefaultFractionDigits())
            throw new IllegalArgumentException("scale=" + amount.scale());
    }
    public Money plus(Money other) {
        if (!currency.equals(other.currency)) throw new IllegalArgumentException("currency mismatch");
        return new Money(amount.add(other.amount), currency);       // 새 객체
    }
}

public record Period(Instant start, Instant end) {                 // Instant는 불변 — Date 대신
    public Period { if (start.isAfter(end)) throw new IllegalArgumentException(start + " > " + end); }
}

public record Order(OrderId id, List<OrderLine> lines) {
    public Order { lines = List.copyOf(lines); }                    // 들어올 때 복사 = 나갈 때도 안전
}
```

- `Date` 같은 가변 JDK 타입 대신 `java.time`의 불변 타입(`Instant`·`LocalDate`)을 쓴다. Bloch의 깨진 `Period` 예가 `Date` 때문이었다.
- `BigDecimal`의 `equals`는 scale까지 비교한다. 그래서 `BigDecimal`을 담은 record의 자동 `equals`도 `2.0`원과 `2.00`원을 다르다고 본다. 업무에서 같은 금액이라면 생성자에서 scale을 정규화한다(위 `Money`는 통화의 소수 자릿수를 넘는 scale을 거절만 한다 — `setScale`로 맞추는 것까지 필요할 수 있다).

(실험, 같은 환경, `scratchpad/sd/15/e19/BdEq.java`)

```text
equals=false compareTo=0 hash=621/6202
record Money(2.0).equals(Money(2.00))=false
```

### 3. 진단

```bash
# setter가 있는 "값" 클래스 후보 (이름으로 거르기)
grep -rlE 'class (Money|Amount|Price|Period|Address|Email)\b' --include=*.java src/main/ | xargs grep -l 'void set'

# record인데 가변 컬렉션 구성 요소를 복사하지 않는 곳
grep -rnE 'record \w+\([^)]*(List|Set|Map)<' --include=*.java src/main/ | head

# 해시 키로 쓰이는 클래스의 equals/hashCode가 가변 필드를 쓰는지 리뷰 대상 뽑기
grep -rnE 'new Hash(Map|Set)<\w+' --include=*.java src/main/ | head
```

- 테스트: 값 객체마다 "같은 값 두 인스턴스가 `equals`·`hashCode` 같음", "연산 후 원래 객체 그대로" 두 가지를 넣는다.

## 장애 시나리오와 대처

### 1. 공유 가변 객체 → 한 곳 수정이 다른 요청에 누출 (⚠ 커리큘럼)

- 현상: 어느 시점부터 모든 고객에게 할증 요금이 붙는다. 재시작하면 잠시 정상.
- 보이는 형태: 캐시·싱글턴·static 상수가 가진 값이 처음과 다르다. 에러 로그 없음. 실험 A: `A==B 같은 객체? true`.
- 원인: 가변 값 객체를 공유하고, 한 호출자가 그 객체 자체를 바꿨다.
- 대처: 값 객체를 불변으로(`add`가 새 객체 반환). 당장은 캐시가 복사본을 돌려주게 막는다.

### 2. 해시 키 변이 → 찾을 수도 지울 수도 없는 원소 (⚠ 커리큘럼)

- 현상: 맵에 넣은 주문을 `get`하면 null, `remove`도 안 된다. 맵 크기만 계속 는다.
- 보이는 형태: `size=1, contains(k)=false`(실험 B). 힙 덤프에서 맵 원소 수가 계속 증가.
- 원인: 키 객체의 `equals`·`hashCode`에 쓰이는 필드를 넣은 뒤 바꿨다.
- 대처: 키는 불변(record·final 필드). 가변 엔티티를 키로 쓰지 말고 불변 ID를 키로 쓴다.

### 3. record니까 불변이라고 믿었다 → 얕은 불변 누출

- 현상: 주문을 만든 뒤 요청 DTO의 리스트를 재사용했더니 저장된 주문 항목이 바뀌었다.
- 보이는 형태: 실험 C `OrderShallow.items=[pen, SECRET-ITEM]`.
- 원인: record는 참조만 고정한다("shallowly immutable").
- 대처: compact 생성자에서 `List.copyOf`. 뷰(`unmodifiableList`)를 스냅샷으로 쓰지 않는다.

### 4. 불변 값이라 스레드 안전하다고 믿었다 → 갱신 유실

- 현상: 동시 요청에서 누적 금액이 모자란다.
- 보이는 형태: 기대 200000, 실제 194596~198092(실험 5절, 8회 실행). 실행마다 다르다.
- 원인: 값은 불변이어도 "현재 값을 새 값으로 바꾸는" 일은 경쟁이다. 공유 참조를 읽고 쓰는 사이에 다른 스레드가 끼었다.
- 대처: `AtomicReference.updateAndGet`(CAS)·락·DB 원자 갱신. 불변은 읽기 안전, 갱신 안전은 따로.

### 5. 불변 API 결과를 버림 → 아무 일도 안 일어남

- 현상: 합계에 할인이 적용되지 않았는데 에러가 없다.
- 보이는 형태: `total.add(...)` 줄이 있는데 `total`이 그대로(실험 D).
- 원인: 불변 객체의 연산 결과를 대입하지 않았다.
- 대처: `total = total.add(x)`. 정적 분석으로 막는다. Error Prone의 `ReturnValueIgnored`(심각도 ERROR)는 `java.math.BigDecimal`·`BigInteger`·`java.nio.file.Path` 등 반환값을 써야 하는 JDK 메서드의 결과 무시를 잡는다(errorprone.info, 소스 `ReturnValueIgnored.java`).

## 핵심 문장

- 값을 공유하면 별칭이 생긴다. 값 객체가 가변이면 한 곳의 수정이 다른 곳에 샌다. 실험에서 요청 A의 할증이 요청 B와 캐시에 그대로 보였다.
- 값 객체는 값으로 같음을 판단한다. 그 전제가 불변이다. 해시 키를 넣은 뒤 바꾸면 원소를 찾지도 지우지도 못한다.
- Java record는 얕게 불변이다. 가변 컬렉션 구성 요소는 compact 생성자에서 `List.copyOf`로 복사한다.
- 불변은 읽기를 안전하게 하지만 "현재 값 교체"는 여전히 경쟁이다. 갱신은 CAS·락으로 지킨다.
- 불변의 비용은 변경마다 새 객체다. 큰 컬렉션은 구조를 공유하는 영속 자료구조로 비용을 줄인다.

## 관련 주제·근거

- 선행
  - [15-error-handling-design](../15-error-handling-design/2-summary.md) — 생성 시점 fail-fast
  - language/06 values-references-passing — 원고 [foundations/variables-and-memory](../../foundations/variables-and-memory/README.md)(값/참조, 얕은/깊은 복사)
- 연결
  - [java/syntax/59-immutable-objects](../../../languages/java/syntax/59-immutable-objects/2-summary.md) — 불변 클래스 문법·방어 복사·record·뷰 vs 복사·안전 공개
  - [18-absence-and-null-design](../18-absence-and-null-design/2-summary.md) — 값 객체가 null을 거절한다
  - [data-structure/26-persistent](../../data-structure/26-persistent/2-summary.md) · [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
  - [os/16-locks-and-spinlocks](../../os/16-locks-and-spinlocks/2-summary.md)
  - [24 types-as-invariants](../24-types-as-invariants/2-summary.md) · domain-modeling 04 entities-and-value-objects — 미작성([domain-modeling 커리큘럼](../../domain-modeling/curriculum.md))
- 글·문서
  - Joshua Bloch, 『Effective Java』 3판 Item 17 "Minimize mutability", Item 50 "Make defensive copies when needed" — 제목은 Pearson 목차, 예제(`Complex` 81~82쪽, `Period`·`Attacks` 231~233쪽)는 저자 GitHub에서 확인, 본문 미열람 <https://github.com/jbloch/effective-java-3e-source-code>
  - Oracle Java Tutorial "A Strategy for Defining Immutable Objects" <https://docs.oracle.com/javase/tutorial/essential/concurrency/imstrat.html>
  - Martin Fowler, "ValueObject"(2016-11-14) — 값 기반 동등성, aliasing bug, 값 객체는 불변 <https://martinfowler.com/bliki/ValueObject.html>
  - JDK 21 API 문서: `java.lang.Record`("shallowly immutable"), `java.util.Set`(가변 원소 주의), `Collections.unmodifiableList`(view), `List.copyOf` <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Record.html>
  - Error Prone `ReturnValueIgnored` <https://errorprone.info/bugpattern/ReturnValueIgnored>
  - JEP 395 Records(JDK 16) <https://openjdk.org/jeps/395>
- 실험 목록 (코드: scratchpad `sd/15/e19/Immut.java`, JDK 21.0.12 eclipse-temurin `--cpus=2`, 호스트 24코어, `java Immut.java` 3회)
  - A 공유 가변 `Money` vs 불변 `Money`
  - B `HashSet` 키 변이 — 조회·삭제 불가
  - C record 얕은 불변, `unmodifiableList` 뷰 vs `List.copyOf`
  - 5절 스레드 4 × 5만 증가 — 가변 194596~198092(집필 3회 + 점검 5회), `AtomicReference<Money>` 200000(8회)
  - 6절 영속 리스트 꼬리 공유
  - D `BigDecimal.add` 결과 버리기
  - `BigDecimal` scale과 record `equals` — `java BdEq.java`
