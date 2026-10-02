# software-design/40-codebase-structure — 정답

## 정답

### 1. 그림은 규칙이 아니다

- 다이어그램은 의도일 뿐이다. 타입이 `public`이면 어느 패키지에서든 쓸 수 있고 컴파일러는 막지 않는다.
- 급한 신규 기능에서 "이미 있는 리포지토리를 주입하면 된다"는 선택이 자연스럽게 나온다(Brown이 든 예).
- Brown: 모든 타입이 `public`이면 패키지는 캡슐화가 아니라 정리(폴더)일 뿐이고, 네 가지 배치의 의존 화살표가 모두 같아진다.

### 2. 세 배치와 꼭 필요한 public

```text
 by layer     web/OrdersController → service/OrdersService(i) → repository/OrdersRepository(i)
 by feature   orders/{OrdersController, OrdersService, OrdersRepository, ...}
 by component web/OrdersController → orders/OrdersComponent(i) [나머지 orders/* 숨김]
```

- by layer: 다른 패키지에서 쓰는 서비스·리포지토리 **인터페이스**는 `public`. 구현은 숨길 수 있다.
- by feature: 컨트롤러만 `public`. 대신 다른 기능은 이 기능 데이터에 컨트롤러로만 닿는다.
- by component: `OrdersComponent`(와 주고받는 값 타입)만 `public`. 리포지토리는 밖에서 보이지 않는다.

### 3. 같은 우회, 다른 결과

(실험 A, JDK 21.0.12, 2026-10-02)

```text
javac 성공
서비스 경유: 거절 — 남의 주문은 볼 수 없다
우회 경로  : [Order[id=2, owner=bob, amount=2000]]
...
component/src/com/shop/web/OrderHistoryController.java:2: error: JdbcOrdersRepository is not public in com.shop.orders; cannot be accessed from outside package
4 errors
```

- by layer: 컴파일된다. 실행하면 서비스에 있던 권한 검사가 빠져 alice 요청으로 bob의 주문이 나온다.
- by component: 컴파일 오류 4개. 우회 경로 자체가 만들어지지 않는다.

### 4. 줄 수는 같고 흩어짐이 다르다

(실험 B)

- by layer: 4파일, 4줄, 디렉터리 4곳(`domain`·`dto`·`repository`·`service` 각 25%).
- by component: 4파일, 4줄, 디렉터리 1곳(`orders` 100%).
- 배치는 변경량을 줄이지 않았다. 변경이 한 곳에 모이고 숨길 수 있는 것이 늘어난다. Brown도 IDE 탐색 때문에 "한 폴더에 모인다"는 이점은 덜 중요하다고 적는다.

### 5. package-private의 한계와 JPMS

- package-private은 패키지 **하나**가 단위다. 컴포넌트 안을 `api`·`internal` 등 여러 패키지로 나누면, 패키지끼리 쓰려고 내부 타입도 `public`이 되어 다시 새어 나간다.
- JPMS(Java 9, JEP 261)는 모듈이 `exports`한 패키지의 `public` 타입만 다른 모듈에 보이게 한다. "public"과 "공개(published)"를 나눈다.

(실험, 같은 환경)

```text
./jpms/web/com/shop/web/Page.java:2: error: package com.shop.orders.internal is not visible
  (package com.shop.orders.internal is declared in module orders, which does not export it)
```

### 6. 소리치는 아키텍처의 범위

- 요구: 최상위 구조가 프레임워크("Spring/Hibernate")가 아니라 업무·유스케이스("회계 시스템")를 말할 것. 프레임워크는 도구로 팔 길이만큼 떨어뜨린다(Martin 2011).
- 요구하지 않는 것: 폴더 이름만으로 경계가 생기지는 않는다. 전부 `public`이면 기능별 폴더도 같은 그래프다(1번). 경계는 가시성·모듈·테스트로 만든다.

### 7. 일부 화면만 권한 검사가 빠질 때

- 의심: 컨트롤러가 서비스(권한 검사 위치)를 건너뛰고 리포지토리를 직접 쓰는 경로.
- 확인: `jdeps -verbose:package`에서 `web -> repository` 간선을 찾는다(실험에서 실제로 보였다). 또는 ArchUnit 계층 규칙을 돌린다(41).
- 대처: 리포지토리를 컴포넌트 안 package-private으로 옮기거나, 당장은 규칙으로 막고 기존 위반을 동결한다.

### 8. util의 함정

- 원인: `util`은 함께 바뀌는 것이 아니라 "둘 곳을 몰랐던 것"을 모은다. 응집이 없고 모두가 의존(fan-in 최대)하므로 한 줄 변경이 의존하는 모듈 전체로 퍼질 수 있다.
- 정리: 쓰는 곳이 하나면 그 기능 안으로 옮긴다. 진짜 공통은 이름 있는 작은 모듈(`money`, `clock`)로 쪼갠다. 함께 재사용되는 것끼리 묶는 원칙은 [39 component-principles](../39-component-principles/2-summary.md).

### 9. 순환과 모듈

- JPMS에서 두 모듈이 서로 `requires`하면 컴파일 오류다.

(실험, JDK 21)

```text
./b/module-info.java:1: error: cyclic dependence involving a
./a/module-info.java:1: error: cyclic dependence involving b
2 errors
```

- 같은 컴파일 단위에서는 패키지 순환이 드러나지 않다가 모듈로 떼는 순간 막힌다. 순환 탐지(ArchUnit `beFreeOfCycles`, dependency-cruiser `no-circular`)와 제거 기법은 41이 다룬다.
