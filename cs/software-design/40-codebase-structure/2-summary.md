# software-design/40-codebase-structure — 패키지 배치와 가시성으로 경계 만들기 — 정리 (힌트)

## 해결하는 문제

계층 다이어그램은 "컨트롤러는 서비스만 부른다"고 말한다.\
그런데 코드의 모든 클래스가 `public`이면, 컨트롤러가 리포지토리를 바로 불러도 컴파일러는 막지 않는다.

```text
 그림(의도)                       코드(실제, 전부 public)
 web ──> service ──> repository   web ──> service ──> repository
                                    └──────────────────^   ← 서비스 우회. 컴파일 OK
```

- *패키지 배치(package structure)*: 클래스를 어느 패키지(폴더)에 두는지에 대한 규칙.
- *가시성(visibility)*: 다른 패키지에서 이 타입을 볼 수 있는지. Java에서는 `public`, `protected`, 아무것도 안 붙인 package-private, `private`가 있다.

쉬운 예: 사무실 출입문이 전부 열려 있으면 "고객 응대는 안내 데스크를 거친다"는 규칙은 벽보일 뿐이다. 문을 잠가야 규칙이 된다.\
똑같은 구조다: 패키지는 방, 가시성은 문이다.\
실무 예: 신규 기능을 급히 만들던 사람이 `OrdersController`에 `OrdersRepository`를 바로 주입한다. 서비스 계층의 권한 검사(남의 주문 조회 금지)가 그 경로에서만 빠진다.

이 노트가 다루는 것은 두 가지다.

1. **무엇을 기준으로 묶나** — 계층별(by layer), 기능별(by feature), 컴포넌트별(by component).
2. **묶은 경계를 무엇으로 지키나** — 가시성(package-private), 모듈 시스템(JPMS). 규칙을 테스트로 검사하는 방법은 [41-architecture-fitness-rules](../41-architecture-fitness-rules/2-summary.md)로 넘긴다.

## 동작·원리

### 1. 세 가지 배치

Simon Brown은 "주문 상태 보기" 기능 하나로 배치들을 비교한다(Brown, "Package by component", simonbrown.je 재게시본. 『Clean Architecture』의 "The Missing Chapter"로도 실렸다고 본인이 적는다).

```text
 by layer (수평)            by feature (수직)          by component
 com.shop.web               com.shop.orders            com.shop.web
   OrdersController           OrdersController           OrdersController ──┐
 com.shop.service             OrdersService                                 │ (공개 인터페이스만)
   OrdersService              OrdersServiceImpl        com.shop.orders      v
   OrdersServiceImpl          OrdersRepository           OrdersComponent  (public)
 com.shop.repository          JdbcOrdersRepository       OrdersComponentImpl
   OrdersRepository                                      OrdersRepository
   JdbcOrdersRepository                                  JdbcOrdersRepository
                                                         (나머지 package-private)
```

- *by layer*: 기술 역할(웹·업무·영속)로 나눈다. 시작이 쉽고 튜토리얼이 대부분 이 모양이다.
- *by feature*: 도메인 개념·기능으로 나눈다. 최상위 폴더가 업무를 말한다.
- *by component*: 업무 로직과 영속을 하나의 거친 단위(컴포넌트)로 묶고, 그 입구 인터페이스 하나만 `public`으로 둔다. UI(웹)는 바깥에 따로 둔다. Brown의 정의에서 컴포넌트는 "잘 정의된 인터페이스 뒤에 묶인 관련 기능 묶음"이다(C4 모델의 정의).

### 2. 전부 `public`이면 배치는 폴더일 뿐이다

Brown의 핵심 주장: 모든 타입이 `public`이면 패키지는 캡슐화가 아니라 정리(폴더)일 뿐이다. 그러면 네 가지 배치는 의존 화살표가 똑같아진다.

```text
 가시성으로 줄일 수 있는 것 (Brown의 표를 요약)
 by layer      : 서비스·리포지토리 "인터페이스"는 public 이어야 한다(다른 패키지에서 쓰므로). 구현은 숨길 수 있다.
 by feature    : 컨트롤러만 public. 대신 다른 기능은 이 기능의 데이터에 컨트롤러로만 접근 가능.
 ports&adapters: 포트 인터페이스는 public. 구현은 숨길 수 있다.
 by component  : OrdersComponent 하나만 public. 리포지토리는 패키지 밖에서 보이지 않는다.
```

- *package-private*: 접근 제한자를 안 붙인 상태. 같은 패키지 안에서만 보인다.
- 남는 `public` 타입이 적을수록 가능한 의존 경로가 적다. 경계를 **컴파일러가** 지킨다.

### 실험 A: 같은 "서비스 우회" 코드를 두 배치에 넣어 본다

두 프로젝트에 똑같이 `OrderHistoryController`(리포지토리를 직접 쓰는 신규 컨트롤러)를 추가했다.

```java
// web/OrderHistoryController.java — 두 배치에 같은 코드
public class OrderHistoryController {
    private final OrdersRepository repo = new JdbcOrdersRepository();
    public String history(String owner, String requester) { return repo.findByOwner(owner).toString(); }
}
// by component 쪽 orders 패키지: interface OrdersRepository, class JdbcOrdersRepository — 둘 다 접근 제한자 없음
```

(실험, JDK 21.0.12 temurin, `--cpus=2`, `scratchpad/sd/40/e40/run.sh`, 2026-10-02)

```text
== by-layer (전부 public): 우회 컨트롤러 컴파일·실행
javac 성공
서비스 경유: 거절 — 남의 주문은 볼 수 없다
우회 경로  : [Order[id=2, owner=bob, amount=2000]]

== by-component (package-private): 같은 우회 컴파일
component/src/com/shop/web/OrderHistoryController.java:2: error: JdbcOrdersRepository is not public in com.shop.orders; cannot be accessed from outside package
import com.shop.orders.JdbcOrdersRepository;
                      ^
component/src/com/shop/web/OrderHistoryController.java:3: error: OrdersRepository is not public in com.shop.orders; cannot be accessed from outside package
...
4 errors
javac exit=1
```

- 관찰 1 — by layer에서는 우회가 조용히 컴파일되고, alice가 bob의 주문을 봤다. 서비스에 있던 권한 검사가 그 경로에서만 빠졌다.
- 관찰 2 — by component에서는 같은 코드가 **컴파일 오류**다. 리뷰어가 잡을 필요가 없다.

### 3. 모듈 시스템: `public`과 "공개(published)"를 나눈다

package-private은 패키지 하나 단위다. 컴포넌트 안을 여러 패키지로 나누고 싶으면 내부 타입도 `public`이어야 해서 다시 새어 나간다.\
Java 9의 모듈 시스템(JPMS, JEP 261)은 모듈이 `exports`한 패키지의 `public` 타입만 다른 모듈에 보이게 한다.

```text
 module orders                         module web (requires orders)
   com.shop.orders.api      exports ──>   import com.shop.orders.api.*       OK
   com.shop.orders.internal (public 클래스) import com.shop.orders.internal.* ✗ 컴파일 오류
```

(실험, 같은 환경, `scratchpad/sd/40/e40/run2.sh`, 2026-10-02)

```text
./jpms/web/com/shop/web/Page.java:2: error: package com.shop.orders.internal is not visible
import com.shop.orders.internal.OrdersTable;
                      ^
  (package com.shop.orders.internal is declared in module orders, which does not export it)
1 error
```

- Brown도 모듈 시스템(OSGi·JPMS)으로 "public인 타입"과 "공개된 타입"을 구분할 수 있다고 적는다.
- 빌드 도구 모듈(Maven·Gradle 다중 모듈)로 소스 트리를 나누는 방법도 있다. 다만 Brown은 "인프라 코드를 한 트리에 몰면 웹 코드가 도메인을 거치지 않고 DB 코드를 부를 수 있다"는 함정(그의 표현으로 Périphérique 안티패턴)을 지적한다.

### 4. 소리치는 아키텍처

Robert C. Martin, "Screaming Architecture"(2011-09-30 블로그): 최상위 디렉터리를 봤을 때 "의료 시스템", "회계 시스템"이라고 외쳐야지 "Rails", "Spring/Hibernate"라고 외치면 안 된다는 주장이다. 프레임워크는 도구이고 아키텍처는 유스케이스를 중심에 둔다는 것.

```text
 프레임워크가 외치는 트리         업무가 외치는 트리
 src/                             src/
   controller/                      orders/
   service/                         payments/
   repository/                      shipping/
   dto/                             web/   (전달 수단은 바깥)
```

### 실험 B: 기능 하나 바꾸기 — 몇 폴더를 오가나

같은 요구 "주문 조회 응답에 배송 메모 추가"를 두 배치에 적용하고 `git diff`로 쟀다.

(실험, 같은 환경, `scratchpad/sd/40/e40` git 저장소, 2026-10-02)

```text
 layer/src/com/shop/domain/Order.java                    | 2 +-
 layer/src/com/shop/dto/OrderView.java                   | 2 +-
 layer/src/com/shop/repository/JdbcOrdersRepository.java | 2 +-
 layer/src/com/shop/service/OrdersServiceImpl.java       | 2 +-
 4 files changed, 4 insertions(+), 4 deletions(-)
  25.0% layer/src/com/shop/domain/
  25.0% layer/src/com/shop/dto/
  25.0% layer/src/com/shop/repository/
  25.0% layer/src/com/shop/service/

 component/src/com/shop/orders/JdbcOrdersRepository.java | 2 +-
 component/src/com/shop/orders/Order.java                | 2 +-
 component/src/com/shop/orders/OrderView.java            | 2 +-
 component/src/com/shop/orders/OrdersComponentImpl.java  | 2 +-
 4 files changed, 4 insertions(+), 4 deletions(-)
 100.0% component/src/com/shop/orders/
```

- 바뀐 파일 수·줄 수는 **같다**(4파일, 4줄). 배치가 변경량을 줄이지는 않았다.
- 다른 것은 흩어짐이다. by layer는 디렉터리 4곳, by component는 1곳. 리뷰·소유권(CODEOWNERS)·"이 기능은 어디까지인가"가 한 폴더로 모인다.
- 반대 측면: Brown 스스로 "현대 IDE의 탐색 기능으로 이 이점은 훨씬 덜 중요하다"고 적는다. 배치의 주된 이득은 탐색보다 **가시성으로 경계를 강제할 수 있다**는 데 있다(실험 A).

### 5. `common`·`util` 폴더의 함정

```text
            orders ──┐
          payments ──┼──> util (3,000줄: 날짜·금액·문자열·HTTP·엑셀...)
          shipping ──┘        ↑ 모두가 의존 → util 한 줄 수정이 모든 모듈의 재빌드·재테스트
```

- 해석: `util`은 "함께 바뀌는 것"이 아니라 "어디 둘지 몰랐던 것"을 모은다. 그래서 응집이 없고, 모두가 의존하므로 바꾸기 가장 어렵다.
- 대처 방향(원칙): 쓰는 곳이 하나면 그 기능 안으로 옮긴다. 진짜 공통이면 이름 있는 작은 모듈(`money`, `clock`)로 쪼갠다. 함께 재사용되는 것끼리 묶는 원칙(CRP)은 [39 component-principles](../39-component-principles/2-summary.md).
- 이 함정을 실험으로 재지는 않았다. 위 그림의 3,000줄은 커리큘럼의 증상 예시다.

## 쓰이는 자료구조·알고리즘

- **패키지 의존 그래프(유향 그래프)** — 정점 = 패키지, 간선 = "A의 클래스가 B의 타입을 쓴다". `jdeps -verbose:package`가 바이트코드에서 뽑는다. 우회 경로는 이 그래프의 간선 하나로 보인다.

(실험, 같은 환경, by layer + 우회 컨트롤러, `run2.sh`, 2026-10-02 — `java.base`로 가는 간선과 `Main` 패키지(`com.shop`) 줄은 뺐다)

```text
   com.shop.repository                                -> com.shop.domain                                    layer
   com.shop.repository                                -> com.shop.repository                                layer
   com.shop.service                                   -> com.shop.domain                                    layer
   com.shop.service                                   -> com.shop.dto                                       layer
   com.shop.service                                   -> com.shop.repository                                layer
   com.shop.service                                   -> com.shop.service                                   layer
   com.shop.web                                       -> com.shop.repository                                layer
   com.shop.web                                       -> com.shop.service                                   layer
```

- 마지막에서 두 번째 줄 `com.shop.web -> com.shop.repository`가 우회 간선이다. 자기 자신으로 가는 줄(`service -> service`)은 같은 패키지 안의 참조다.

- **가시성 = 그래프에 넣을 수 있는 간선의 제한** — `public` 타입 수가 "들어올 수 있는 간선의 끝점" 수다. package-private은 패키지 밖에서 들어오는 간선을 컴파일 단계에서 막는다.
- **모듈 그래프(JPMS)** — `requires`가 가독성(readability) 간선, `exports`가 그 간선으로 볼 수 있는 패키지 집합이다(JEP 261).
- **순환 탐지(SCC)** — 패키지 그래프에 순환이 생기면 모듈로 떼어낼 수 없다. 탐지와 제거는 [41](../41-architecture-fitness-rules/2-summary.md), 알고리즘은 [algorithm/18-scc](../../algorithm/18-scc/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 순서

1. **최상위는 업무로**: `orders/`, `payments/`처럼 컴포넌트(또는 바운디드 컨텍스트) 단위로 나눈다. 웹·메시지 같은 전달 수단은 바깥에 둔다.
2. **입구만 `public`**: 컴포넌트마다 공개 인터페이스(`OrdersComponent`)와 그것이 주고받는 값 타입만 `public`. 구현·리포지토리·엔티티는 접근 제한자를 지운다.
3. **조립은 입구에서**: 구현이 숨겨져 있으면 바깥에서 `new`할 수 없다. 정적 팩토리(`OrdersComponent.create()`)나 같은 패키지의 설정 클래스가 조립한다. Spring이라면 같은 패키지의 `@Configuration`이 package-private 빈을 만들 수 있다 — Spring 버전별 세부는 이 노트에서 확인하지 않았다 [?].
4. **패키지 하나로 부족하면 모듈로**: JPMS `exports`, 또는 Gradle·Maven 다중 모듈로 `api`와 `internal`을 나눈다.
5. **남는 규칙은 테스트로**: 가시성으로 못 막는 규칙(도메인이 웹을 import하지 않기, 순환 금지)은 ArchUnit 등으로 검사한다 → [41](../41-architecture-fitness-rules/2-summary.md).

### 2. 코드 (Java)

```java
package com.shop.orders;

public interface OrdersComponent {                                  // 유일한 입구
    List<OrderView> ordersOf(String owner, String requester);
    static OrdersComponent create() { return new OrdersComponentImpl(new JdbcOrdersRepository()); }
}
public record OrderView(long id, int amount) {}                     // 내보내는 값
record Order(long id, String owner, int amount) {}                  // 내부 모델
interface OrdersRepository { List<Order> findByOwner(String owner); }
class JdbcOrdersRepository implements OrdersRepository { ... }
class OrdersComponentImpl implements OrdersComponent { ... }        // 권한 검사는 여기 한 곳
```

### 3. 진단

```bash
# 패키지 의존 그래프 (JDK 동봉)
jdeps -verbose:package -filter:none build/classes/java/main | grep -v java.base
# public 타입이 몇 개인가 (대략치: 한 파일 한 최상위 타입 가정)
grep -rlE '^public (final )?(class|interface|record|enum)' src/main/java | wc -l
# 한 기능 변경이 몇 디렉터리에 걸쳤나
git diff --dirstat=files,0 HEAD~1
```

## 장애 시나리오와 대처

### 1. 서비스 계층 우회가 조용히 누적된다 (⚠ 커리큘럼)

- 현상: 권한 검사·감사 로그가 일부 화면에서만 빠진다. 보안 점검에서 "다른 사용자 주문 조회 가능"이 나온다.
- 보이는 형태: 컴파일·테스트는 다 통과한다. `jdeps`에서 `web -> repository` 간선이 보인다(위 출력).
- 원인: 계층별 패키지 + 전부 `public`. 가시성이 아무것도 막지 않는다(실험 A).
- 대처: 리포지토리를 컴포넌트 안에 넣고 package-private으로. 당장 옮기기 어려우면 ArchUnit 계층 규칙으로 막고 기존 위반은 동결한다([41](../41-architecture-fitness-rules/2-summary.md)).
- 예외: 모든 우회가 사고는 아니다. Brown도 CQRS처럼 계층 건너뛰기("relaxed layered architecture")가 의도된 경우가 있다고 적는다. 문제는 권한 검사 같은 업무 규칙이 서비스에만 있을 때의 우회다.

### 2. 기능 하나 수정에 네 폴더를 오간다 (⚠ 커리큘럼)

- 현상: 작은 요구에도 `controller/`·`service/`·`repository/`·`dto/`를 다 연다. PR 리뷰어가 여러 팀이다.
- 보이는 형태: `git diff --dirstat`이 4곳으로 갈린다(실험 B).
- 원인: 기술 역할로 묶어서 "함께 바뀌는 것"이 흩어졌다.
- 대처: 기능·컴포넌트 단위로 다시 묶는다. 실험 B처럼 줄 수는 같아도 변경이 한 폴더에 모이고, 숨길 수 있는 것이 늘어난다.

### 3. `util` 패키지가 3천 줄로 커져 모든 모듈이 의존한다 (⚠ 커리큘럼)

- 현상: `util`의 날짜 함수 하나를 고쳤더니 무관한 모듈 테스트가 깨진다. 아무도 `util`을 정리하지 못한다.
- 보이는 형태: 의존 그래프에서 `util`의 들어오는 간선(fan-in)이 압도적이다. `git log`에서 `util`이 거의 모든 기능 커밋에 끼어 있다.
- 원인: 응집 기준 없이 "공통"을 모았다.
- 대처: 쓰는 곳이 하나인 코드는 그 기능 안으로 되돌린다. 나머지는 이름 있는 작은 모듈로 쪼갠다. 변경 빈도는 [53-code-forensics-hotspots](../53-code-forensics-hotspots/2-summary.md)에서 다룬다.

### 4. 순환 의존으로 모듈을 떼어낼 수 없다 (⚠ 커리큘럼 → 41)

- 현상: `orders`를 별도 모듈로 떼려니 `payments`가 따라오고, `payments`는 다시 `orders`를 부른다.
- 보이는 형태: 모듈로 나누는 순간 순환이 컴파일 오류가 된다. JPMS에서 `a requires b`, `b requires a`를 주면 javac가 `error: cyclic dependence involving a`를 낸다(실험, JDK 21, `scratchpad/sd/40/e40/jpms-cycle`).
- 원인: 패키지 수준에서 이미 순환이 있었는데 같은 컴파일 단위라 드러나지 않았다.
- 대처: 순환 탐지·제거 기법은 [41](../41-architecture-fitness-rules/2-summary.md).

### 5. "헥사고날" 폴더는 있는데 경계가 없다

- 현상: `adapter/`, `domain/` 폴더가 있지만 컨트롤러가 JPA 리포지토리를 바로 쓴다.
- 원인: 폴더명은 배치일 뿐이다. 전부 `public`이면 Brown 말대로 모든 배치가 같은 그래프가 된다.
- 대처: 폴더명이 아니라 가시성·모듈·테스트로 강제한다. 세 스타일의 실제 비교는 [44-architecture-in-code](../44-architecture-in-code/2-summary.md).

## 핵심 문장

- 모든 타입이 `public`이면 패키지는 폴더일 뿐이고, 계층·기능·헥사고날 배치가 모두 같은 의존 그래프가 된다(Brown).
- 실험에서 같은 서비스 우회 코드가 by layer(전부 public)에서는 컴파일되어 권한 검사를 건너뛰었고, by component(package-private)에서는 컴파일 오류 4개로 막혔다.
- 배치를 바꿔도 한 기능 변경의 파일·줄 수는 같았다(4파일 4줄). 달라진 것은 흩어진 디렉터리 수(4 → 1)다.
- package-private은 패키지 하나가 단위다. 더 큰 경계는 JPMS `exports`나 빌드 모듈로 만든다.
- 최상위 폴더는 프레임워크가 아니라 업무를 말해야 한다(Martin, "Screaming Architecture").

## 관련 주제·근거

- 선행
  - [38-layered-hexagonal-clean](../38-layered-hexagonal-clean/2-summary.md) — 의존 방향 규칙
  - [39 component-principles](../39-component-principles/2-summary.md)
  - [25-dependency-injection-and-composition-root](../25-dependency-injection-and-composition-root/2-summary.md) — 숨긴 구현을 어디서 조립하나
- 후속·연결
  - [41-architecture-fitness-rules](../41-architecture-fitness-rules/2-summary.md) — 가시성으로 못 막는 규칙을 테스트로
  - [44-architecture-in-code](../44-architecture-in-code/2-summary.md) — 계층형·헥사고날·클린을 같은 유스케이스로 비교
  - [systems/architecture-styles](../../systems/architecture-styles/2-summary.md) — 아키텍처 스타일 개관
  - [algorithm/18-scc](../../algorithm/18-scc/2-summary.md) — 순환 탐지
- 글·문서
  - Simon Brown, "Package by component" 재게시본(원래 2016 Coding the Architecture 블로그, 『Clean Architecture』 "The Missing Chapter"로도 실렸다고 본인 페이지에 적음) <https://simonbrown.je/modular-monolith>
  - Robert C. Martin, 『Clean Architecture』(2017) — 장 번호(21장 Screaming Architecture, 34장 The Missing Chapter)는 독자 요약 저장소 목차로만 확인, 본문 미열람 [?] <https://github.com/serodriguez68/clean-architecture>
  - Robert C. Martin, "Screaming Architecture", 2011-09-30 <https://blog.cleancoder.com/uncle-bob/2011/09/30/Screaming-Architecture.html>
  - JEP 261: Module System (Java 9 전달, `exports`·`requires`·readability) <https://openjdk.org/jeps/261>
- 실험 목록 (코드: scratchpad `sd/40/e40/`, JDK 21.0.12 temurin 컨테이너 `--cpus=2`)
  - A 서비스 우회 — `run.sh`: by layer 컴파일·실행 vs by component 컴파일 오류
  - JPMS `exports` — `run2.sh`의 두 번째 단계: 내보내지 않은 패키지 import 오류
  - JPMS 모듈 순환 — `jpms-cycle/`에서 `javac --module-source-path . -m a,b` → `cyclic dependence` 오류 2개
  - jdeps 패키지 그래프 — `run2.sh`의 첫 단계(우회 간선 확인)
  - B 배송 메모 추가 — git 저장소 `e40`에서 `git diff --stat`·`--dirstat=files,0`
