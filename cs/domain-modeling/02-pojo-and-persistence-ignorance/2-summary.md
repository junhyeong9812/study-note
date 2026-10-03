# domain-modeling/02-pojo-and-persistence-ignorance — 프레임워크 독립 도메인 객체와 영속성 무지 — 정리 (힌트)

## 해결하는 문제

업무 규칙을 담은 객체가 저장 기술에 묶이면, 규칙 하나를 확인하는 데도 그 기술을 통째로 띄워야 한다. 저장 기술의 동작(지연 로딩·프록시·자동 UPDATE)이 규칙 코드의 결과를 바꾸기도 한다.

쉬운 예: 요리법 카드.

```text
  요리법 카드 A                          요리법 카드 B
  "소금 5g, 3분 끓인다"                   "소금 5g, 3분 끓인다
                                          (단, X사 인덕션 3단에서만.
                                           전원 켜기 전엔 카드를 읽을 수 없음)"
     → 어느 부엌에서든 읽고 따라 한다        → X사 인덕션이 있는 부엌에서만 확인 가능
```

- 요리법(규칙)과 조리 기구(저장 기술)가 섞이면, 기구가 없는 곳에서는 요리법이 맞는지도 확인할 수 없다.

똑같은 구조다.\
`Order.approve()`의 규칙("대기 중일 때만 승인")을 확인하려는데, 그 클래스가 JPA 어노테이션과 Hibernate 지연 로딩에 기대고 있다. 테스트는 `SessionFactory`(또는 스프링 컨텍스트)를 띄워야 하고, 트랜잭션 밖에서 연관 컬렉션을 읽으면 `LazyInitializationException`이 난다.

- *POJO(Plain Old Java Object)*: 특정 프레임워크 인터페이스를 구현하거나 클래스를 상속하지 않은 평범한 자바 객체. 이름의 유래·JavaBean·DTO와의 구분은 원본 [pojo](../pojo/2-summary.md) 「문제」·「혼동하기 쉬운 용어」.
- *영속성 무지(persistence ignorance)*: 도메인 객체가 자기가 어떻게 저장·복원되는지 모르는 성질. 용어를 처음 쓴 사람·문헌은 확인하지 못했다 `[?]`. 같은 생각을 Evans 4장은 "도메인 객체는 자기를 표시하고 저장하고 애플리케이션 작업을 관리하는 책임에서 벗어나 모델 표현에 집중한다"로 적는다.

## 동작·원리

### 1. POJO의 유래 — 이름을 붙여 평범한 객체를 되살림

- Fowler bliki "POJO"(2003-12-08): Rebecca Parsons, Josh MacKenzie, Fowler가 2000년 9월 컨퍼런스 발표를 준비하며 만든 말이다. 엔티티 빈 대신 평범한 자바 객체에 업무 로직을 담자는 주장이었다.
  - 원문 취지: 사람들이 평범한 객체를 꺼리는 이유가 "멋진 이름이 없어서"라고 보고 이름을 붙였더니 잘 퍼졌다.
- 핵심은 형태(getter·setter 유무)가 아니라 **무엇에 의존하지 않는가**다. 판별 질문은 원본의 "컨테이너 없이 `new`로 만들어 테스트할 수 있는가".

### 2. 침투 정도의 사다리 — 어디까지 묶였나

```text
  순수 클래스        어노테이션만            ORM이 요구하는 모양까지         프레임워크 상속·구현
  (import 0)        (@Entity, @Id)         (인자 없는 생성자, non-final,   (EJB 2 SessionBean 등)
                                            프록시·지연 로딩에 기댐)
     │                   │                           │                          │
  javac만으로         jar 없이는                 실행 결과가 세션·프록시      컨테이너 없이는
  컴파일·테스트       컴파일 안 됨                상태에 따라 달라짐           실행 안 됨
```

- 원본 「애노테이션이 붙으면 POJO가 아닌가」의 스펙트럼을 한 칸 더 나눴다. 어노테이션은 컴파일 의존이고, ORM 동작 규약은 **실행 의미 의존**이다. 후자가 더 깊다.

### 3. ORM이 도메인 객체에 요구하는 것 (Hibernate 6.6 사용자 가이드 §3.4)

| 요구 | Jakarta Persistence | Hibernate 6.6 |
|---|---|---|
| 인자 없는 생성자 | public 또는 protected 필수 | 필수. public·protected·package 가능. 런타임 프록시를 쓰려면 최소 package |
| final 금지 | 엔티티 클래스·영속 필드·메서드 final 금지 | final도 저장은 되지만 지연 로딩용 프록시를 만들 수 없다 |
| getter·setter | 필드 접근이면 불필요. 프로퍼티 접근일 때만 접근자가 public·protected여야 한다. 클라이언트는 필드 대신 메서드(접근자 또는 업무 메서드)로 상태를 본다(§2.1·§2.2) | 요구하지 않음. 필드 직접 접근 가능, 가시성 무관 |

- 접근 방식: `@Id`를 필드에 두면 필드 접근, getter에 두면 프로퍼티 접근이다. 필드 접근이면 setter 없이도 저장·복원된다(06번 실험).

### 4. 영속성 컨텍스트 안에서 객체가 겪는 일

```text
  트랜잭션(세션) 열림 ─────────────────────────────────────────── 커밋 ─── 닫힘
     │ find(Order,10)                                             │
     │   ├─ 1차 캐시: {Order#10 → 객체}, 로드 시점 스냅숏 저장     │ flush: 스냅숏과 현재 값 비교
     │   ├─ customer = Customer$HibernateProxy (id만 앎, 미초기화) │   → 바뀐 필드가 있으면 UPDATE
     │   └─ lines   = 지연 컬렉션(아직 SELECT 안 함)              │
     │ order.approve()   ← 도메인 메서드. save() 호출 없음          │
                                                                  ▼
  세션 밖에서 order.lines.size()  →  LazyInitializationException ("no Session")
```

- *프록시(proxy)*: Hibernate가 실행 중에 만든 엔티티의 하위 클래스. 식별자만 알고 있다가 메서드 호출 때 진짜 데이터를 읽는다.
- *지연 로딩(lazy loading)*: 연관 객체를 처음 쓸 때 읽는 방식. 세션이 열려 있어야 읽을 수 있다.
- *더티 체킹(dirty checking)*: flush 때 로드 시점 스냅숏과 현재 값을 비교해 바뀐 엔티티에 UPDATE를 내는 동작(기본 설정 기준. 바이트코드 향상의 in-line dirty tracking을 켜면 엔티티가 바뀐 속성을 스스로 기록한다 — 가이드 §6.2.2).
- 도메인 코드는 이 그림을 모르는 채로 짜이는데, 결과는 이 그림에 따라 달라진다. 그래서 "어노테이션만 붙였으니 POJO다"로 끝나지 않는다.

### 실험: 순수 객체 vs Hibernate 6.6 엔티티

- 환경: JDK 21(`eclipse-temurin:21-jdk`, `--cpus=2`, `-m 1g`, 네트워크 없음), Hibernate ORM 6.6.29.Final, H2 2.3.232 인메모리, 2026-10-03.
- 엔티티: `Customer`(id, name), `PurchaseOrder`(`@ManyToOne(fetch = LAZY) customer`, `@ElementCollection(fetch = LAZY) lines`, `approve()`), 인자 없는 생성자를 일부러 뺀 `Coupon`.

```java
// Customer의 equals 세 가지
@Override public boolean equals(Object o) {                 // ① getClass 비교 + 필드 직접 접근
    if (this == o) return true;
    if (o == null || getClass() != o.getClass()) return false;
    return Objects.equals(id, ((Customer) o).id);
}
public boolean sameAsField(Object o) {                       // ② instanceof + 필드 직접 접근
    return this == o || (o instanceof Customer c && id != null && id.equals(c.id));
}
public boolean sameAs(Object o) {                            // ③ instanceof + getter
    return this == o || (o instanceof Customer c && getId() != null && getId().equals(c.getId()));
}
```

(실험, JDK 21 temurin, 2026-10-03) (a) 순수 도메인 `Order`(import 0개)를 클래스패스 없이 `javac`·`java`로 실행

```text
순수 테스트 통과: 승인 불가: APPROVED
```

(실험, JDK 21 temurin, 2026-10-03) (a') JPA 어노테이션이 붙은 소스를 jar 없이 `javac` (앞부분)

```text
src/jpa/Main.java:3: error: package org.hibernate.cfg does not exist
import org.hibernate.cfg.Configuration;
                        ^
src/jpa/Main.java:6: error: cannot find symbol
@Entity @Table(name = "customer")
 ^
  symbol: class Entity
```

(실험, JDK 21 temurin + Hibernate 6.6.29 + H2 2.3.232, 2026-10-03) (b)~(e). `[after initialize]` 줄은 `Hibernate.initialize(proxy)`를 부른 뒤 다시 찍은 것이다

```text
== 1. 세션 밖에서 지연 컬렉션 접근
  LazyInitializationException: failed to lazily initialize a collection of role: PurchaseOrder.lines: could not initialize proxy - no Session
== 2. 지연 @ManyToOne 프록시와 equals
  proxy.getClass()      = Customer$HibernateProxy
  Hibernate.isInitialized(proxy) = false
  proxy.id (필드 직접)    = null
  proxy.getId()         = 1
  real.equals(proxy)    = false   (getClass 비교 + 필드 접근)
  proxy.getClass().getName() = Customer$HibernateProxy
  real.sameAsField(proxy) = false  (instanceof + 필드 접근)
  real.sameAs(proxy)    = true    (instanceof + getter)
  [after initialize] isInitialized=true proxy.id(field)=null sameAsField=false equals=false sameAs=true
== 3. 도메인 메서드만 불렀는데 UPDATE가 나간다(더티 체킹)
  DB status = APPROVED
== 4. 인자 없는 생성자가 없는 엔티티 조회
  org.hibernate.InstantiationException: No default constructor for entity 'Coupon'
```

(실험, 같은 환경, 3회 실행) 같은 규칙 검사("잔액보다 많이 출금하면 거절")를 `new`로 만든 객체로 할 때와 `SessionFactory`를 띄워 할 때의 경과 시간

```text
규칙 검사(new로 만든 객체) 0.78 ms | SessionFactory 기동+같은 검사 3911 ms
규칙 검사(new로 만든 객체) 1.44 ms | SessionFactory 기동+같은 검사 3808 ms
규칙 검사(new로 만든 객체) 0.83 ms | SessionFactory 기동+같은 검사 4117 ms
```

- 관찰
  - 지연 컬렉션은 세션이 닫힌 뒤 읽으면 예외다. 도메인 메서드가 그 컬렉션을 쓰면, 같은 메서드가 호출 위치(트랜잭션 안/밖)에 따라 성공하거나 실패한다.
  - 프록시는 `Customer`의 하위 클래스이고, 필드 `id`가 `null`이다. 초기화 뒤에도 `null`이었다(초기화는 별도의 실제 객체를 채우고, 프록시는 메서드 호출을 그 객체에 넘긴다). getter `getId()`는 1을 돌려줬다. 그래서 `getClass()` 비교(①)와 필드 직접 접근(②)은 같은 id여도 초기화 전후 모두 `false`, `instanceof` + getter(③)만 `true`였다.
  - `approve()`만 불렀고 `save`·`merge`는 없었는데 커밋 뒤 DB 값이 `APPROVED`다. 관리 상태 엔티티의 변경은 더티 체킹으로 저장된다.
  - 인자 없는 생성자가 없으면 조회에서 `InstantiationException`이 난다. ORM 요구가 생성자 설계를 끌어당긴다.
  - 경과 시간은 이 제한 환경(`--cpus=2`, 첫 실행·JIT 전)의 값이고 실행마다 다르다(위 3회: 0.78~1.44 ms vs 3808~4117 ms, 같은 조건 재실행 3회: 0.72~0.87 ms vs 4294~4656 ms). 차이의 크기 자릿수만 본다.

## 쓰이는 자료구조·알고리즘

- **식별자 맵(identity map)** — 영속성 컨텍스트의 1차 캐시는 `(엔티티 타입, id) → 객체` 해시 맵이다. 한 세션 안에서 같은 행은 같은 자바 객체로 돌려준다(Hibernate 6.6 가이드 §3.4.7). [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- **스냅숏 비교** — 기본 설정(바이트코드 향상 없음)에서 더티 체킹은 로드 시점 값 배열과 flush 시점 값 배열을 필드별로 비교한다. 엔티티 수 × 필드 수만큼 비교가 든다. in-line dirty tracking을 켜면 flush가 엔티티에 바뀐 속성을 묻는다(가이드 §6.2.2).
- **가상 프록시(virtual proxy)** — 하위 클래스를 실행 중에 생성해(Hibernate 6.6은 Byte Buddy를 런타임 의존으로 씀) 메서드 호출을 가로챈다. [software-design/33-aop-and-proxies](../../software-design/33-aop-and-proxies/2-summary.md)
- **지연 로딩(Lazy Load, PoEAA)** — 처음 접근할 때 읽는다. 컬렉션 하나마다 SELECT가 따로 나가면 N+1이 된다. [database/23-orm-and-n-plus-one](../../database/23-orm-and-n-plus-one/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 선택지 셋 — 묶임 정도와 비용을 고른다

| 선택 | 도메인 클래스 | 비용 | 맞는 경우 |
|---|---|---|---|
| A. 도메인 = JPA 엔티티 | 어노테이션 허용, 아래 규칙 지킴 | ORM 규약이 설계에 스며든다 | 대부분의 스프링 서비스. 매핑 코드를 따로 둘 만큼 모델이 복잡하지 않을 때 |
| B. XML 매핑(`orm.xml`) | 어노테이션 0, 매핑은 XML | 매핑이 코드와 떨어져 리팩터링 때 같이 고쳐야 한다 | 도메인 jar를 저장 기술 없이 배포·재사용해야 할 때 |
| C. 도메인 모델 + 영속 모델 분리 | 순수 클래스, 매퍼로 변환 | 매퍼·중복 필드·변환 테스트 | 도메인이 복잡하고 저장 구조가 크게 다를 때. 원본은 "작은 프로젝트에서는 과잉"이라고 적는다 |

- 어느 쪽이든 판단 기준은 원본과 같다. **규칙을 `new`로 만든 객체로 테스트할 수 있는가.**

### 2. A를 고를 때 지키는 규칙

```java
@Entity
@Table(name = "orders")
public class Order {
    @Id private Long id;                                     // 필드 접근 → setter 불필요
    @Enumerated(EnumType.STRING) private Status status = Status.PENDING;
    @OneToMany(mappedBy = "order", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<OrderLine> lines = new ArrayList<>();

    protected Order() {}                                     // JPA용. 외부 생성은 정적 팩토리·생성자로
    public Order(Long id) { this.id = id; }

    public void approve() {                                  // 규칙. 세션·프록시를 모른다
        if (status != Status.PENDING) throw new IllegalStateException("승인 불가: " + status);
        status = Status.APPROVED;
    }
    public Long getId() { return id; }

    @Override public boolean equals(Object o) {              // 프록시를 견디는 동등성
        if (this == o) return true;
        if (!(o instanceof Order other)) return false;
        return getId() != null && getId().equals(other.getId());
    }
    @Override public int hashCode() { return Order.class.hashCode(); }   // id 생성 전후로 바뀌지 않게
}
```

- 클래스·메서드에 `final`을 붙이지 않는다(프록시가 필요하면).
- `equals`는 `instanceof` + getter로 쓴다. 실험에서 `getClass()`·필드 직접 접근은 프록시와 비교할 때 틀렸다.
- 도메인 메서드가 지연 연관을 읽는다면, 그 메서드는 트랜잭션 안에서만 부른다고 애플리케이션 서비스가 보장한다. 또는 필요한 데이터를 조회 시점에 함께 읽는다(fetch join·엔티티 그래프).
- 조회 전용 경로에서는 엔티티 상태를 바꾸지 않는다. 바꾸면 더티 체킹으로 저장된다. 스프링이면 `@Transactional(readOnly = true)`를 쓴다(이 설정이 Hibernate flush에 주는 영향은 버전별 문서로 확인 `[?]`).

### 3. 진단

```bash
# 도메인 패키지가 무엇을 import 하나 (패키지 경로에 /domain/ 이 있다고 가정)
find src/main/java -path "*/domain/*" -name "*.java" \
  | xargs grep -hoE "^import (jakarta|javax|org\.springframework|org\.hibernate)[^;]*" | sort | uniq -c
# 도메인 단위 테스트가 스프링·DB를 띄우는가
find src/test/java -path "*/domain/*" -name "*.java" | xargs grep -lE "@SpringBootTest|@DataJpaTest"
```

- 도메인 규칙 테스트에 `@DataJpaTest`가 붙어 있다면, 그 규칙이 저장 동작에 기대고 있지 않은지 본다.

## 장애 시나리오와 대처

### 1. 도메인 규칙 테스트에 컨텍스트가 필요하다 (⚠ 커리큘럼 "단위 테스트 불가")

- **현상**: 규칙 하나 확인하는 테스트가 수 초씩 걸려 개발자가 잘 안 돌린다. CI 시간이 늘어난다.
- **보이는 형태**: 도메인 테스트 클래스마다 `@SpringBootTest`·`@DataJpaTest`. 실험에서 같은 검사가 `new` 객체로는 1 ms 안팎, `SessionFactory` 기동을 포함하면 약 4~5초(제한 환경 값, 6회 3808~4656 ms).
- **원인**: 규칙이 지연 연관·리포지토리 호출·스프링 빈에 기대어 저장 기술 없이는 실행되지 않는다.
- **대처**: 규칙을 엔티티·값 객체 메서드로 모으고, 필요한 값은 인자로 받는다. 저장 동작 검증(매핑·쿼리)은 별도 통합 테스트로 나눈다.

### 2. `LazyInitializationException` (⚠ 커리큘럼 "지연 로딩 예외")

- **현상**: 같은 도메인 메서드가 서비스 안에서는 되고, 컨트롤러·이벤트 리스너·비동기 스레드에서는 실패한다.
- **보이는 형태**: `failed to lazily initialize a collection of role: <엔티티>.<필드>: could not initialize proxy - no Session`(실험 출력과 같은 문구, Hibernate 6.6.29).
- **원인**: 트랜잭션(세션)이 끝난 뒤 지연 컬렉션·프록시에 처음 접근했다.
- **대처**: 도메인 메서드 호출을 트랜잭션 경계 안으로 옮긴다. 화면용 데이터는 조회 시점에 DTO로 만들어 내보낸다(원본 01 회색지대 4). 연관을 꼭 함께 써야 하면 fetch join으로 같이 읽는다. 세션을 뷰까지 열어 두는 방식은 지연 로딩 SELECT가 요청 끝까지 흩어지게 하므로 쓰기 전에 N+1 비용을 잰다([database/23](../../database/23-orm-and-n-plus-one/2-summary.md)).

### 3. 프록시와 비교한 `equals`가 `false` — 중복 판정·`contains` 실패

- **현상**: `Set<Customer>`에 같은 고객이 두 번 들어가거나, `list.contains(customer)`가 `false`다. 연관으로 얻은 고객과 직접 조회한 고객이 "다른 사람"으로 판정된다.
- **보이는 형태**: 디버거에서 클래스 이름이 `Customer$HibernateProxy`. 필드를 보면 `id = null`.
- **원인**: `equals`가 `getClass()`를 비교하거나 상대의 필드를 직접 읽었다. 실험에서 두 방식 모두 `false`, `instanceof` + getter만 `true`였다.
- **대처**: `instanceof` + getter로 고친다. 실제 객체가 필요하면 `Hibernate.unproxy`로 꺼낸다. `Hibernate.initialize`·`isInitialized`는 해결책이 아니다 — 초기화 뒤에도 프록시 필드는 `null`이었다(실험 2). 값 동등성이 필요한 개념은 값 객체로 뺀다(04번).

### 4. 저장 호출이 없는데 UPDATE가 나간다

- **현상**: 조회 API인데 DB 행이 바뀐다. 감사 로그에 예상 밖 수정 시각이 찍힌다.
- **보이는 형태**: SQL 로그에 `update ...`가 커밋 직전에 찍힌다. 코드에는 `save()`가 없다.
- **원인**: 관리 상태 엔티티에서 도메인 메서드(또는 setter)를 불렀고, 더티 체킹이 변경을 저장했다(실험 3).
- **대처**: 조회 경로는 DTO 프로젝션으로 엔티티를 거치지 않게 하거나, 읽기 전용 트랜잭션을 쓴다. 상태를 바꾸는 도메인 메서드는 명령 유스케이스에서만 부른다(07번 CQS).

### 5. 생성자·final 제약 위반

- **현상**: 배포 직후 특정 엔티티 조회가 실패한다. 또는 지연 로딩이 걸리지 않아 연관을 매번 즉시 읽는다(점검 재실행, Hibernate 6.6.29: `final` 엔티티를 가리키는 `@ManyToOne(LAZY)`가 조회 직후 프록시가 아닌 실제 클래스, `isInitialized = true`였다).
- **보이는 형태**: `org.hibernate.InstantiationException: No default constructor for entity '<이름>'`(실험 4). final 엔티티는 프록시를 못 만든다(Hibernate 6.6 가이드 §3.4.2).
- **원인**: 불변 객체로 만들려고 인자 없는 생성자를 없애거나 클래스를 `final`로 만들었다.
- **대처**: `protected` 인자 없는 생성자를 두고, 외부 생성 경로는 검증하는 생성자·팩토리로만 연다. 불변으로 만들고 싶은 개념은 엔티티가 아닌 값 객체(`@Embeddable`)로 뺀다.

## 핵심 문장

- POJO는 형태가 아니라 의존의 문제다. 판별 질문은 "컨테이너 없이 `new`로 만들어 규칙을 테스트할 수 있는가".
- 어노테이션은 컴파일 의존이고, 프록시·지연 로딩·더티 체킹은 실행 의미 의존이다. 후자가 도메인 결과를 바꾼다.
- Hibernate 6.6.29 실험에서 프록시의 필드 `id`는 초기화 전후 모두 `null`이었다. `getClass()`나 필드 직접 접근으로 쓴 `equals`는 같은 id에도 `false`를 냈다.
- 관리 상태 엔티티는 도메인 메서드만 불러도 커밋 때 UPDATE된다. 조회 경로에서 엔티티 상태를 바꾸지 않는다.
- 도메인을 JPA 엔티티로 쓸지, 모델을 분리할지는 매핑 비용과 묶임 위험을 비교해 고른다. 어느 쪽이든 규칙은 `new`로 테스트할 수 있어야 한다.

## 관련 주제·근거

- 원본(이어받음): [domain-modeling/pojo](../pojo/2-summary.md) — POJO 유래, 판별법, JavaBean·DTO·VO 구분, 스프링 IoC·AOP와 POJO, 침투 스펙트럼, record·Lombok, 빈약 모델
  - 참고: 원본 「현대 자바에서의 모습」의 "record는 JPA 엔티티로 못 쓴다(기본 생성자·가변 필드 필요)"는 맞지만 이유를 더 정확히 하면, Jakarta Persistence가 엔티티 클래스의 final을 금지하고 인자 없는 생성자를 요구하기 때문이다(record는 암묵적 final이고 컴포넌트 필드도 final이다). Hibernate 6.6 가이드 §3.3.11 Aggregate embeddable mapping은 **임베더블(값 타입)** 을 record로 정의하는 예를 든다.
- 선행: [01-domain-vs-application-logic](../01-domain-vs-application-logic/2-summary.md)
- 연결
  - [06-anemic-vs-rich-model](../06-anemic-vs-rich-model/2-summary.md) — setter 없는 풍부 엔티티를 Hibernate가 필드 접근으로 저장하는 실험
  - [07-domain-logic-patterns-and-service-layer](../07-domain-logic-patterns-and-service-layer/2-summary.md) — 트랜잭션 경계, CQS
  - [04-entities-and-value-objects](../04-entities-and-value-objects/2-summary.md) · [10-repositories-and-factories](../10-repositories-and-factories/2-summary.md)
  - [software-design/38-layered-hexagonal-clean](../../software-design/38-layered-hexagonal-clean/2-summary.md) — 도메인이 프레임워크에 의존할 때의 테스트·교체 실험, ArchUnit
  - [software-design/33-aop-and-proxies](../../software-design/33-aop-and-proxies/2-summary.md) · [software-design/25-dependency-injection-and-composition-root](../../software-design/25-dependency-injection-and-composition-root/2-summary.md)
  - [database/23-orm-and-n-plus-one](../../database/23-orm-and-n-plus-one/2-summary.md) · [database/25-data-source-patterns](../../database/25-data-source-patterns/2-summary.md) · [database/51-object-relational-structural-mapping](../../database/51-object-relational-structural-mapping/2-summary.md)
  - [languages/java/syntax/27-equals-hashcode-contract](../../../languages/java/syntax/27-equals-hashcode-contract/2-summary.md) · [languages/java/syntax/14-records](../../../languages/java/syntax/14-records/2-summary.md)
- 근거
  - Fowler bliki "POJO"(2003-12-08) <https://martinfowler.com/bliki/POJO.html>
  - Evans 『DDD』 4장 Layered Architecture — 도메인 객체가 표시·저장·작업 관리 책임에서 벗어난다(2003 최종 원고 PDF 대조)
  - Hibernate ORM 6.6 User Guide §3.4 Implementing entities(3.4.2 Prefer non-final classes, 3.4.3 Implement a no-argument constructor, 3.4.4 getters/setters, 3.4.7 equals()/hashCode()) <https://docs.hibernate.org/orm/6.6/userguide/html_single/Hibernate_User_Guide.html>
  - Fowler 『PoEAA』 Lazy Load·Identity Map <https://martinfowler.com/eaaCatalog/>
- 실험 목록
  - 순수 클래스 vs 어노테이션 클래스 컴파일(jar 없이), Hibernate 6.6.29 + H2 2.3.232: 세션 밖 지연 컬렉션 예외, `@ManyToOne(LAZY)` 프록시의 클래스 이름·초기화 여부·필드 `id` null(`Hibernate.initialize` 뒤에도)·`equals` 세 방식, 저장 호출 없는 더티 체킹 UPDATE, 인자 없는 생성자 누락 예외, `new` 객체 vs `SessionFactory` 기동 경과 시간(3회) — JDK 21.0.12(temurin), `--cpus=2`·`-m 1g`·네트워크 없음
