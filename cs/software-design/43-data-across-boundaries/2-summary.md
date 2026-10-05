# software-design/43-data-across-boundaries — DTO·Remote Facade·매퍼: 경계를 넘는 데이터 — 정리 (힌트)

## 해결하는 문제

데이터가 경계를 넘을 때마다 "어떤 모양으로 넘기나"를 정해야 한다.

```text
 HTTP 요청 ──> [웹] ──> [유스케이스] ──> [도메인] ──> [영속(JPA 엔티티)] ──> DB
 HTTP 응답 <── [웹] <──────────────────────────────── 엔티티를 그대로 JSON으로?
```

엔티티(영속 모델)를 그대로 응답으로 내보내면 세 가지가 함께 묶인다.

- DB 스키마 = API 계약. 컬럼을 추가하면 API 응답에도 조용히 나간다(비밀번호 해시 포함).
- 응답을 만드는 동안 지연 로딩이 일어난다. 세션이 닫혔으면 예외, 열려 있으면 화면 그리는 중에 쿼리가 나간다.
- 양방향 연관은 직렬화기가 끝없이 따라간다.

반대로 원격 경계에서는 "몇 번 왕복하나"가 문제다. 객체의 게터를 그대로 원격에 노출하면 화면 하나에 왕복이 수십 번 생긴다.

- *DTO(Data Transfer Object)*: "호출 횟수를 줄이려고 프로세스 사이로 데이터를 실어 나르는 객체"(Fowler PoEAA). 직렬화 가능해야 한다.
- *Remote Facade*: "세밀한(fine-grained) 객체들 위에 거친(coarse-grained) 파사드를 씌워 네트워크 효율을 높인다"(PoEAA).
- *Assembler(매퍼)*: DTO와 도메인 객체 사이에서 데이터를 옮기는 객체. PoEAA는 서버 쪽에 보통 어셈블러를 둔다고 적는다.

쉬운 예: 택배를 보낼 때 집 안 가구를 그대로 들고 가지 않는다. 필요한 것만 상자(DTO)에 담고, 상자 하나로 한 번에 보낸다(거친 입도).\
똑같은 구조다: 경계를 넘는 모양은 안쪽 모델과 따로 정한다.\
실무 예: 회원 엔티티를 `@RestController`에서 그대로 반환했더니, 나중에 추가된 `passwordHash` 컬럼이 API 응답에 섞여 나간다.

## 동작·원리

### 1. 세 가지 모델

```text
 요청 모델           도메인 모델                영속 모델(엔티티)          응답 모델
 SignUpRequest  ──>  Member(규칙·불변식)  <──>  MemberEntity(@Entity)     MemberView
 (입력 검증 형태)     프레임워크 모름            테이블 모양·지연 로딩       (API 계약 형태)
        └─ 웹 경계 ─┘                      └─ 영속 경계 ─┘          └─ 웹 경계 ─┘
```

- 바뀌는 이유가 셋 다 다르다. API 계약은 클라이언트와 합의해서, 테이블은 성능·정규화 때문에, 도메인은 업무 규칙 때문에 바뀐다.
- 셋을 하나로 합치면 한 이유의 변경이 다른 둘을 끌고 간다. 셋으로 나누면 경계마다 매핑 코드가 생긴다. 이 둘 사이의 선택이다.

### 2. 엔티티를 그대로 직렬화하면 — 실험

회원(`Member`)과 주문(`PurchaseOrder`)이 양방향 연관인 JPA 엔티티를 Jackson으로 직렬화했다.

```java
@Entity class Member {
    @Id Long id;  String name;  String passwordHash;
    @OneToMany(mappedBy = "member") List<PurchaseOrder> orders;   // 기본 LAZY
}
@Entity class PurchaseOrder {
    @Id Long id;  int amount;
    @ManyToOne Member member;                                     // 주문 → 회원 (양방향)
}
public record MemberView(long id, String name, int orderCount, int totalAmount) {}   // 응답 DTO
```

(실험, Hibernate ORM 7.4.11.Final + H2 2.5.252 + jackson-databind 2.22.3, JDK 21.0.12 temurin `--cpus=2`, `scratchpad/sd/40/e43/Boundary.java`, 2026-10-02 — 1)의 긴 참조 경로는 400자에서 잘랐다)

```text
== 1) 세션 안에서 엔티티를 그대로 JSON으로 (양방향 연관)
JsonMappingException: Document nesting depth (1001) exceeds the maximum allowed (1000, from `StreamWriteConstraints.getMaxNestingDepth()`) (through reference chain: Boundary$Member["orders"]->org.hibernate.collection.spi.PersistentBag[0]->Boundary$PurchaseOrder["member"]->Boundary$Member["orders"]->org.hibernate.collection.spi.PersistentBag[0]->Boundary$PurchaseOrder["member"]->Boundary$Member["or
== 2) 세션이 닫힌 뒤 엔티티를 JSON으로 (LAZY 컬렉션)
JsonMappingException: Cannot lazily initialize collection of role 'Boundary$Member.orders' with key '1' (no session) (through reference chain: Boundary$Member["orders"])
  cause = org.hibernate.LazyInitializationException
== 3) 컬렉션만 빼고 엔티티를 JSON으로
{"id":1,"name":"kim","passwordHash":"$2a$10$abcdefghijk"}
== 4) 트랜잭션 안에서 DTO로 옮겨 담아 JSON으로
{"id":1,"name":"kim","orderCount":2,"totalAmount":3000}
```

```text
 1) 무한 재귀           Member ──orders──> PurchaseOrder ──member──> Member ──orders──> ...  (깊이 1000에서 중단)
 2) 지연 로딩 예외       세션 닫힘 → orders 프록시(PersistentBag)를 직렬화기가 건드림 → LazyInitializationException
 3) 민감 필드 노출       게터가 있는 필드는 전부 나간다 → passwordHash
 4) DTO                 응답에 필요한 모양(주문 수·합계)을 트랜잭션 안에서 계산해 담는다
```

- 관찰 1 — 이 Jackson 버전(2.22.3)에서는 스택 오버플로가 아니라 **최대 중첩 깊이 1000**(`StreamWriteConstraints`)에서 멈췄다. 어느 쪽이든 응답은 실패다.
- 관찰 2 — 지연 로딩 예외는 직렬화 단계(컨트롤러 밖)에서 난다. 비즈니스 코드는 이미 끝났는데 응답이 깨진다.
- 관찰 3 — 컬렉션 문제를 `@JsonIgnore` 같은 것으로 막아도 `passwordHash`는 그대로 나간다. 엔티티 직렬화는 "새로 생긴 필드는 기본으로 공개"다.
- 관찰 4 — DTO는 화면이 원하는 **다른 모양**(주문 목록 대신 개수·합계)을 줄 수 있다. 1:1 복사만 하는 DTO가 아니다.

참고: Spring Boot 서블릿 웹 앱(Spring MVC)에서는 `spring.jpa.open-in-view`가 기본으로 켜져 있어(`@ConditionalOnWebApplication(type = SERVLET)` + `matchIfMissing = true`) 응답을 그리는 동안에도 영속성 컨텍스트가 열려 있다. 명시하지 않으면 기동 시 "spring.jpa.open-in-view is enabled by default. Therefore, database queries may be performed during view rendering." 경고를 남긴다(Spring Boot `JpaBaseConfiguration` 소스, main·3.5.x 브랜치). 그래서 2)의 예외 대신 **직렬화 중 쿼리**(N+1)로 나타나기도 한다 — [database/23-orm-and-n-plus-one](../../database/23-orm-and-n-plus-one/2-summary.md).

### 3. 원격 경계: Chatty I/O와 Remote Facade

```text
 세밀한 인터페이스(게터를 원격에 노출)          Remote Facade + DTO
 client ─ name() ──────────> server              client ─ summary() ─> server
 client ─ grade() ─────────> server                     <─ MemberSummaryDto(이름, 등급, 주문 목록)
 client ─ orderCount() ────> server
 client ─ orderIdAt(0) ────> server
 client ─ orderAmountAt(0) ─> server ... × N
```

- PoEAA: 한 주소 공간 안에서는 세밀한 상호작용이 잘 맞지만, 프로세스 사이 호출은 비싸서 원격으로 쓰일 객체는 호출 수를 줄이는 거친 인터페이스가 필요하다. Remote Facade는 거친 메서드를 안쪽 세밀한 객체 호출로 번역할 뿐 도메인 로직을 갖지 않는다.

### 실험: 왕복 수

호출마다 5ms를 자는 원격 호출 흉내로 셌다(5ms는 예시 값이다. 실제 네트워크가 아니다).

(실험, JDK 21.0.12 temurin `--cpus=2`, `scratchpad/sd/40/e43/Chatty.java`, 2026-10-02 — 시간은 실행마다 몇 ms씩 다르다. 집필·사실 점검 합쳐 6회: 50건 527~530ms, 파사드 5~6ms)

```text
주문  1건: 세밀한 인터페이스 왕복   5회   26ms | Remote Facade 왕복 1회  5ms
주문 10건: 세밀한 인터페이스 왕복  23회  119ms | Remote Facade 왕복 1회  5ms
주문 50건: 세밀한 인터페이스 왕복 103회  527ms | Remote Facade 왕복 1회  5ms
```

- 세밀한 인터페이스의 왕복은 `3 + 2N`이다(이름·등급·개수 + 주문마다 2번). 데이터가 늘면 지연이 선형으로 는다.
- 파사드는 데이터 양과 무관하게 1회다. 대가는 응답 크기와 "이 화면 전용" 메서드가 늘어나는 것이다.

### 4. 로컬 DTO에 대한 반론

Fowler, "LocalDTO"(bliki, 2004-10-21): DTO의 목적은 비싼 원격 호출에서 데이터를 옮기는 것이다. 로컬 맥락에서는 필요 없을 뿐 아니라 해롭다 — 거친 API는 쓰기 어렵고, 도메인에서 DTO로 옮기는 매핑 일이 생긴다. PoEAA 기고자 Randy Stafford의 말("DTO의 비용은 상당하고 고통스럽다, 아마 ORM 다음으로")도 인용한다.\
같은 글에서 Fowler가 인정하는 예외: 프레젠테이션 모델과 도메인 모델 사이에 큰 불일치가 있으면 화면 전용 파사드·게이트웨이를 두는 것은 가치가 있다.

```text
 해석: 두 주장은 경계의 종류로 맞춰진다
 HTTP API 응답         = 원격 경계 + 클라이언트와의 계약 → DTO(응답 모델)가 제 자리
 같은 프로세스 계층 사이 = 로컬 → 계층마다 1:1 복사 DTO는 Fowler가 비판한 비용 (44의 "의례적 매핑")
```

### 5. 매핑 코드는 필드 추가 때 깨진다

세터식 매퍼와 생성자(레코드)식 매퍼에 같은 변경(필드 `phone` 추가, 매퍼는 아직 안 고침)을 넣었다.

```java
// 세터식                                         // 생성자(레코드)식
MemberDto d = new MemberDto();                      record MemberDto(String name, String phone) {}
d.name = e.name;                                    return new MemberDto(e.name());   // 옛 인자 1개
// d.phone = e.phone;  ← 누락
```

(실험, JDK 21.0.12, `scratchpad/sd/40/e43/mapping/`, 2026-10-02)

```text
== 세터식
MemberDto{name=kim, phone=null}
== 생성자식
ctor/Mapping.java:5: error: constructor MemberDto in record MemberDto cannot be applied to given types;
    static MemberDto toDto(MemberEntity e) { return new MemberDto(e.name()); }   // 아직 옛 인자 1개
                                                    ^
  required: String,String
```

- 세터식은 조용히 `null`을 낸다. 클라이언트가 "전화번호가 비어 있다"고 신고할 때까지 모른다.
- 생성자식은 컴파일이 깨져 누락 자리를 알려 준다. 단 같은 타입 인자가 여럿이면 순서가 바뀌어도 컴파일된다(위치 결합).

## 쓰이는 자료구조·알고리즘

- **필드 대응 표(매퍼)** — 원본 필드 → 대상 필드의 사상. 손으로 쓰거나(위 실험), 컴파일 타임 생성(MapStruct, 35 annotation-and-metadata-programming), 런타임 리플렉션(ModelMapper류)으로 만든다. MapStruct는 매핑 안 된 대상 속성을 기본으로 경고한다(`@Mapper`·`@MapperConfig`의 `unmappedTargetPolicy()` 기본값 `ReportingPolicy.WARN` — MapStruct 소스). `ERROR`로 올리면 누락이 빌드 실패가 된다. 이 노트에서 MapStruct를 실행하지는 않았다.
- **객체 그래프 순회와 순환** — 직렬화기는 객체 그래프를 깊이 우선으로 따라간다. 양방향 연관은 그래프의 고리라 방문 표시 없이는 끝나지 않는다(실험 1: 깊이 1000에서 중단). `@JsonManagedReference`·`@JsonBackReference`, `@JsonIdentityInfo`가 고리를 끊는 Jackson 장치다 — 이 노트에서 실행하지 않았다.
- **프록시(지연 로딩)** — Hibernate는 LAZY 컬렉션 자리에 `PersistentBag` 같은 래퍼를 두고 처음 접근할 때 세션으로 쿼리한다(실험 출력의 클래스 이름). 세션이 없으면 `LazyInitializationException`.
- **거친 입도 파사드** — 여러 세밀한 호출을 하나로 묶는 번역층. 왕복 수를 `O(N)`에서 `O(1)`로 줄이고 응답 크기를 키운다.

## 적용 — 풀어나가는 법

### 1. 순서

1. **경계를 센다**: HTTP·메시지·외부 API는 원격 경계 → 요청·응답 모델을 따로 둔다. 같은 프로세스 계층 사이는 기본 공유하고, 불일치가 클 때만 나눈다(Fowler LocalDTO).
2. **엔티티는 응답으로 내보내지 않는다**: 응답 모델은 트랜잭션 안에서 만든다(실험 4). 지연 로딩이 응답 단계로 새지 않는다.
3. **응답은 화면이 원하는 모양으로**: 1:1 복사가 아니라 집계·평탄화(주문 수·합계). 조회 전용이면 쿼리에서 바로 DTO로 투영하는 것도 방법이다(JPQL 생성자 표현식 등) — 이 노트에서 실행하지 않았다.
4. **원격 인터페이스는 거칠게**: 화면·유스케이스 단위로 한 번에 필요한 것을 준다(Remote Facade). 파사드에는 로직을 두지 않는다.
5. **매핑을 컴파일러가 지키게**: 레코드 생성자·불변 DTO, 또는 생성 도구의 "매핑 안 된 대상 필드" 검사. 매핑 테스트에 "모든 필드가 null 아님" 검사를 둔다.
6. **Spring Boot라면 `spring.jpa.open-in-view`를 명시적으로 정한다**(false를 고르면 지연 로딩 예외가 경계에서 드러난다).

### 2. 코드 (Java, Spring 스타일 — 개념 예시)

```java
public record MemberView(long id, String name, int orderCount, int totalAmount) {
    static MemberView from(Member m) {                       // 어셈블러: 트랜잭션 안에서 호출
        return new MemberView(m.getId(), m.getName(), m.getOrders().size(),
                              m.getOrders().stream().mapToInt(PurchaseOrder::getAmount).sum());
    }
}

@Transactional(readOnly = true)
public MemberView memberView(long id) {                     // 응답 모델은 경계 안에서 완성
    return MemberView.from(members.findById(id).orElseThrow());
}
```

### 3. 진단

```bash
# 컨트롤러가 엔티티를 반환하는가 (@Entity 클래스 이름 목록과 컨트롤러 반환 타입 대조)
grep -rl '@Entity' src/main/java | xargs -n1 basename | sed 's/.java//' > entities.txt
grep -rhoE 'public (ResponseEntity<)?[A-Z][A-Za-z]+' src/main/java/**/web | grep -wFf entities.txt
# 기동 로그에 open-in-view 경고가 있는가
grep 'spring.jpa.open-in-view is enabled by default' app.log
```

## 장애 시나리오와 대처

### 1. 엔티티를 그대로 JSON으로 → `LazyInitializationException` (⚠ 커리큘럼)

- 현상: 서비스 테스트는 통과하는데 API 호출이 500을 낸다.
- 보이는 형태: `JsonMappingException: Cannot lazily initialize collection of role '...orders' ... (no session)`, cause `org.hibernate.LazyInitializationException`(실험 2).
- 원인: 트랜잭션·세션이 끝난 뒤 직렬화기가 LAZY 컬렉션을 건드렸다.
- 대처: 트랜잭션 안에서 응답 DTO를 완성한다(실험 4). open-in-view로 덮으면 예외 대신 직렬화 중 쿼리가 나간다.

### 2. 민감 필드 노출 (⚠ 커리큘럼)

- 현상: 보안 점검에서 회원 API 응답에 비밀번호 해시가 보인다.
- 보이는 형태: `{"id":1,"name":"kim","passwordHash":"$2a$10$..."}`(실험 3).
- 원인: 엔티티 직렬화는 게터가 있는 필드를 기본으로 전부 낸다. 나중에 추가된 컬럼도 자동으로 계약에 들어간다.
- 대처: 응답 모델을 따로 둔다(허용 목록 방식). `@JsonIgnore`(차단 목록)는 새 필드를 막지 못한다.

### 3. 양방향 연관 무한 재귀 (⚠ 커리큘럼)

- 현상: 회원 상세 API가 오래 걸리다 실패한다.
- 보이는 형태: `Document nesting depth (1001) exceeds the maximum allowed (1000 ...)`와 반복되는 참조 경로 `Member["orders"]->...->PurchaseOrder["member"]->Member["orders"]`(실험 1, Jackson 2.22.3). `StreamWriteConstraints`(최대 깊이 기본 1000)는 jackson-core 2.16에서 생겼다(소스 `@since 2.16`). 그 전 버전(예: jackson-databind 2.15)은 `StackOverflowError`를 잡아 `JsonMappingException: Infinite recursion (StackOverflowError)`로 낸다(`BeanSerializerBase` 소스) — 이 노트에서 2.15로 실행하지는 않았다.
- 원인: 객체 그래프의 고리를 직렬화기가 끝없이 따라간다.
- 대처: 응답 모델은 고리가 없는 트리로 설계한다. 엔티티 직렬화를 유지해야 하면 Jackson의 참조 애너테이션으로 한쪽을 끊는다.

### 4. 세밀한 원격 인터페이스 → Chatty I/O (⚠ 커리큘럼)

- 현상: 상세 화면 하나가 느리고, 주문이 많은 회원일수록 더 느리다.
- 보이는 형태: 트레이스에 같은 서비스로의 짧은 호출이 수십~수백 번(실험: 주문 50건에 103회, 527ms).
- 원인: 객체의 게터 수준 메서드를 원격으로 노출했다. 왕복 = `3 + 2N`.
- 대처: 화면 단위 Remote Facade + DTO(실험: 1회, 5ms). 대가는 응답 크기와 화면 전용 메서드 증가다.

### 5. 매핑 코드 폭증 → 필드 추가 시 한 계층 누락 (⚠ 커리큘럼)

- 현상: 새 필드가 API 응답에서 계속 비어 있다. 오류는 없다.
- 보이는 형태: `MemberDto{name=kim, phone=null}`(실험, 세터식).
- 원인: 계층마다 손 매퍼가 있고 하나를 빠뜨렸다. 세터식은 누락을 컴파일러가 모른다.
- 대처: 레코드·생성자 매핑으로 누락을 컴파일 오류로 만든다(실험). 1:1 복사만 하는 계층 DTO는 없앤다(Fowler LocalDTO). 매핑 테스트로 필드 누락을 검사한다.

## 핵심 문장

- 경계를 넘는 모양은 안쪽 모델과 따로 정한다. 요청·도메인·영속·응답 모델은 바뀌는 이유가 다르다.
- 실험에서 엔티티를 그대로 직렬화하자 양방향 연관은 중첩 깊이 1000 초과, 세션 밖에서는 `LazyInitializationException`, 컬렉션을 빼도 `passwordHash` 노출이 나왔다. 트랜잭션 안에서 만든 DTO만 깨끗했다.
- DTO의 본래 목적은 원격 호출 수를 줄이는 것이다. 세밀한 인터페이스는 주문 50건에 왕복 103회, Remote Facade는 1회였다(5ms 흉내 지연).
- 같은 프로세스 계층 사이의 1:1 DTO는 Fowler가 해롭다고 본 매핑 비용이다. HTTP 응답 모델과 구분한다.
- 세터식 매퍼는 필드 누락을 `null`로 숨기고, 레코드 생성자 매핑은 컴파일 오류로 드러낸다.

## 관련 주제·근거

- 선행
  - [38-layered-hexagonal-clean](../38-layered-hexagonal-clean/2-summary.md) · [api-design/08-schema-and-serialization](../../api-design/08-schema-and-serialization/2-summary.md)
- 후속·연결
  - [44-architecture-in-code](../44-architecture-in-code/2-summary.md) — 계층마다 매핑하는 비용을 세 스타일로 비교
  - [42-ui-architecture-patterns](../42-ui-architecture-patterns/2-summary.md) — 뷰모델·Presentation Model
  - [database/23-orm-and-n-plus-one](../../database/23-orm-and-n-plus-one/2-summary.md) — 지연 로딩과 N+1
  - [35-annotation-and-metadata-programming](../35-annotation-and-metadata-programming/2-summary.md) — MapStruct 같은 컴파일 타임 코드 생성
- 글·문서
  - Fowler, PoEAA "Data Transfer Object" <https://martinfowler.com/eaaCatalog/dataTransferObject.html> · "Remote Facade" <https://martinfowler.com/eaaCatalog/remoteFacade.html>
  - Fowler, "LocalDTO", 2004-10-21 <https://martinfowler.com/bliki/LocalDTO.html>
  - jackson-core `StreamWriteConstraints`(`DEFAULT_MAX_DEPTH = 1000`, `@since 2.16`) <https://github.com/FasterXML/jackson-core/blob/2.18/src/main/java/com/fasterxml/jackson/core/StreamWriteConstraints.java> · jackson-databind 2.15 `BeanSerializerBase`("Infinite recursion (StackOverflowError)") <https://github.com/FasterXML/jackson-databind/blob/2.15/src/main/java/com/fasterxml/jackson/databind/ser/std/BeanSerializerBase.java>
  - MapStruct `Mapper.java`·`MapperConfig.java`(`unmappedTargetPolicy() default ReportingPolicy.WARN`) <https://github.com/mapstruct/mapstruct/tree/main/core/src/main/java/org/mapstruct>
  - Spring Boot `JpaBaseConfiguration` — open-in-view 기본 경고 문구(main 브랜치 `module/spring-boot-jpa/...`, 3.5.x 브랜치 `spring-boot-project/spring-boot-autoconfigure/...`) <https://github.com/spring-projects/spring-boot>
- 실험 목록 (코드: scratchpad `sd/40/e43/`, 라이브러리는 Maven Central에서 `sd/40/libs/`로 받음: hibernate-core 7.4.11.Final, h2 2.5.252, jackson-databind 2.22.3, jakarta.persistence-api 3.2.0 / JDK 21.0.12 temurin `--cpus=2 -m 1g`)
  - 엔티티 직렬화 네 경우 — `javac -cp '/w/libs/*' -d out Boundary.java && java -cp 'out:/w/libs/*' Boundary`
  - Chatty vs Remote Facade — `java Chatty.java`(집필 3회 + 사실 점검 3회)
  - 매퍼 누락 — `java setter/Mapping.java`, `java ctor/Mapping.java`
