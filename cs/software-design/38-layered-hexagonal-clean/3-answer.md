# software-design/38-layered-hexagonal-clean — 정답

## 정답

### 1. 업무 규칙이 DB를 알 때

- 규칙 하나를 시험하려 해도 DB·프레임워크가 떠야 한다. DB를 바꾸면 업무 코드도 바뀐다.
- Cockburn(2005): 애플리케이션이 사용자·프로그램·자동 테스트·배치에 의해 똑같이 구동되고, 실행 시 장치·DB와 떨어져 개발·시험될 수 있게 한다.

### 2. 세 그래프와 의존 규칙

```text
 계층형:   Controller → Service → Persistence → DB
 헥사고날: web 어댑터 → [유스케이스·«port»·도메인] ← jdbc 어댑터(implements)
 클린:     프레임워크·드라이버 → 인터페이스 어댑터 → 유스케이스 → 엔티티  (안쪽으로만)
```

- 의존 규칙(Martin 2012): 소스 코드 의존은 안쪽으로만 향한다. 안쪽 원은 바깥 원의 이름을 언급하지 않는다.

### 3. 흐름과 의존의 분리

- 출력 포트(`OrderRepository`)를 **안쪽(애플리케이션)이 소유**하고, 바깥 어댑터가 그것을 구현한다. 호출은 안 → 바깥이어도 소스 의존은 바깥 → 안(DIP).
- 구현을 고르는 곳은 컴포지션 루트(실험의 `shop.config.Wiring`, 『Clean Architecture』 26장 "The Main Component" — 장 제목만 확인).

### 4. DB 없는 단위 테스트

(실험 A, JDK 21.0.12, 2026-10-02)

```text
v1 단위 테스트 실패: java.lang.IllegalStateException: DB 연결 실패: jdbc:postgresql://db/shop
placed o1, 저장 수=1
규칙 확인: 금액은 양수
```

- v1: 서비스 생성자에서 저장소 구현이 DB에 연결하려다 실패. 규칙까지 가지도 못한다.
- v2: 메모리 어댑터로 저장 1건, 음수 금액 규칙 확인.

### 5. DB 교체

```text
== v1 DB 교체
 src/shop/controller/OrderController.java       | 4 ++--
 src/shop/persistence/MongoOrderRepository.java | 5 +++++
 src/shop/service/OrderService.java             | 4 ++--
 3 files changed, 9 insertions(+), 4 deletions(-)
== v2 DB 교체
 src/shop/adapter/out/MongoOrderRepository.java | 7 +++++++
 src/shop/config/Wiring.java                    | 4 ++--
 2 files changed, 9 insertions(+), 2 deletions(-)
```

- v1: 새 구현 + 업무 서비스·컨트롤러 수정.
- v2: 새 어댑터 + 조립 한 곳. 도메인·유스케이스는 그대로.

### 6. 헥사고날이 손해인 경우

- 같은 기능에 v1은 Java 파일 4개·33줄, v2는 7개·45줄. 포트·조립·매핑 간접층만큼 늘었다.
- 기술 교체도 격리 시험도 필요 없는 단순 CRUD, 바뀌지 않을 바깥까지 포트로 감싼 경우는 간접층 비용이 이득보다 클 수 있다. 필드 추가 같은 변경이 여러 층의 매핑을 건드린다.

### 7. v1 계층 규칙

(실험 B, ArchUnit 1.4.1)

- 계층 규칙 위반 3건: `OrderController`가 `JdbcOrderRepository`를 생성(6행)·필드로 보유·`count()` 호출(8행). 업무 → 영속 구현 규칙도 위반 3건(`OrderService` 4·7행).
- ⚠ "계층 건너뛰기 누적"(컨트롤러 → 저장소 직접)과 "도메인이 DB에 의존"을 둘 다 잡았다.

### 8. v2 양파 규칙과 컴포지션 루트

- 예외 없이: 위반 4건, 전부 `shop.config.Wiring`(어댑터·유스케이스 생성자 호출, 반환 타입). 이 실험에서는 층 밖 클래스의 접근도 위반으로 셌다.
- `ignoreDependency(resideInAPackage("shop.config.."), DescribedPredicate.alwaysTrue())`로 조립 패키지만 빼자 통과.
- 정당한 이유: 컴포지션 루트는 정의상 모든 원을 알아야 구현을 고를 수 있는 가장 바깥 원이다. 규칙 전체를 끄는 대신 그 패키지만 명시적으로 뺀다.

### 9. 유스케이스가 어댑터를 직접 부름

- 컴파일: 성공(같은 모듈이라 막을 장치가 없다). 실행: `DB_URL`이 없으면 그 경로에서 실패, 있으면 그냥 동작.
- ArchUnit: 위반 2건 — `PlaceOrder.place`가 `shop.adapter.out.Db.connect`·`exec`를 호출(`PlaceOrder.java:8`). 규칙을 빌드 테스트에 넣어 두면 병합 전에 드러난다.

### 10. jdeps 그래프

```text
v1: shop.controller -> shop.persistence, shop.controller -> shop.service, shop.service -> shop.persistence
v2: shop.adapter.in -> shop.application, shop.adapter.out -> shop.application, shop.adapter.out -> shop.domain,
    shop.application -> shop.domain, shop.config -> (adapter.in, adapter.out, application)
```

- v1 업무(`service`) → `persistence` 간선이 있다(바깥 구현 방향).
- v2 `application`에서 나가는 간선은 `domain`뿐, `domain`은 나가는 간선이 없다. 모든 바깥 간선이 안쪽을 향한다.
