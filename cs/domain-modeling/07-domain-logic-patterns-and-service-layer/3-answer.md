# domain-modeling/07-domain-logic-patterns-and-service-layer — 정답

## 정답

### 1. 세 패턴의 단위

- Transaction Script: "Organizes business logic by procedures where each procedure handles a single request from the presentation." — 요청 하나 = 프로시저 하나.
- Table Module: "A single instance that handles the business logic for all rows in a database table or view." — 테이블(또는 뷰) 하나 = 인스턴스 하나.
- Domain Model: "An object model of the domain that incorporates both behavior and data." — 의미 있는 개체마다 객체, 행위와 데이터를 함께.

### 2. 기준선이 없는 이유와 성장 방식

- 도메인 로직의 복잡도는 정량적으로 잴 수 없다(PoEAA 2장, 요약으로 확인). 그래서 교차점은 판단이다.
- 규칙이 늘 때
  - Transaction Script: 스크립트의 조건문이 늘고, 여러 스크립트에 같은 검증이 복사된다.
  - Domain Model: 전략 객체 같은 새 객체를 더해 규칙을 정돈된 방식으로 담는다. 처음 비용(학습·매핑)은 더 높다.

### 3. 실험 A·B

- VIP 한도 추가: Transaction Script 3파일(`PlaceOrderScript`·`AddItemScript`·`ChangeQtyScript`), Domain Model 1파일(`Order.java`의 `limit()`). 합계 4 files changed.
- 공지 제목 수정: 스크립트 1파일 5줄, 도메인 모델 구조(`Notice`·`NoticeRepository`·`NoticeRow`·`InMemoryNoticeRepository`·`RenameNoticeService`) 5파일 23줄.
- 결론: 공유 규칙이 있는 곳은 Domain Model이, 불변식 없는 CRUD는 스크립트가 적게 든다. 축소 모델의 값이다.

### 4. Stafford의 구분

- domain logic: 순수하게 문제 영역에 관한 로직. application logic: 애플리케이션 책임에 관한 로직(workflow logic이라고도 함, 알림·통합 응답 조율 등).
- 분리 이유: 애플리케이션 고유 로직을 도메인 객체에 넣으면 도메인 객체를 다른 애플리케이션에서 재사용하기 어렵다.
- domain facade: Domain Model 위의 얇은 파사드. 업무 로직을 구현하지 않는다.
- operation script: 더 두꺼운 클래스가 애플리케이션 로직을 직접 구현하고 도메인 로직은 도메인 객체에 맡긴다.

### 5. Service Layer가 필요할 때

- 필요: 업무 로직의 클라이언트가 여러 종류이고, 유스케이스 응답이 여러 트랜잭션 자원에 걸칠 때.
- 아마 불필요: 클라이언트가 한 종류(예: UI 하나)이고 응답이 여러 트랜잭션 자원에 걸치지 않을 때.
- 웹 UI 하나뿐인 사내 도구: 다른 진입점(배치·메시지)과 여러 자원에 걸친 응답이 없다면 별도 계층의 이득이 작다. 다만 이 경우에도 트랜잭션 경계는 유스케이스 단위로 한 곳에서 잡는다(실험 C의 문제는 계층 유무가 아니라 경계 위치다).

### 6. 실험 C

- 자동 커밋 3회: 1회차 `A=900 B=100`, 2회차는 로그 INSERT가 `23505`로 실패했지만 출금·입금이 이미 커밋돼 `A=800 B=200`.
- 한 트랜잭션: 1회차 `A=900 B=100`, 2회차 실패 시 셋이 함께 롤백돼 `A=900 B=100`.

### 7. Spring Data JPA의 트랜잭션

- 기본: `CrudRepository`에서 상속한 메서드는 `SimpleJpaRepository`의 설정을 따른다. 읽기는 `readOnly = true`, 나머지는 평범한 `@Transactional`. 직접 선언한 쿼리 메서드(default 메서드 포함)에는 기본 트랜잭션 설정이 없다.
- 여러 리포지토리에 걸친 경계: 여러 리포지토리를 다루는 "facade or service" 구현이 정한다.
- 바깥 `@Transactional`이 있으면 리포지토리의 트랜잭션 설정은 무시되고 바깥 설정이 실제로 쓰인다(기존 트랜잭션에 참여).

### 8. 실험 D

- debug를 켜면 2/5만 처리된다. 로그 식의 `poll()`이 j1·j3·j5를 꺼내 버리고, 루프 본문의 `poll()`은 j2·j4만 처리한다.
- 위반: CQS. 값을 돌려주는 조회처럼 쓰인 메서드가 상태도 바꿨다.
- 고침: 로그에는 상태를 바꾸지 않는 `peek()`를 쓴다(실험: 5/5). 일반적으로 조회와 명령을 나누고, 합쳐야 하면 이름에 동작을 드러낸다.

### 9. 권한 검사 우회

- 가능성이 큰 위치: 컨트롤러나 URL 패턴 설정에만 있었다. 소비자 경로는 그 진입점을 지나지 않는다.
- Spring Security 7.1 문서: 메서드 보안의 용도로 "Enforcing security at the service layer"를 든다. 어노테이션 기반 메서드 보안을 쓰면 어노테이션이 없는 메서드는 보호되지 않으므로, `HttpSecurity`에 catch-all 인가 규칙을 두라고 권한다.
- 대처: 권한 검사를 Service Layer 연산에 두고, 진입점 × 권한 없는 사용자 테스트를 둔다. `HttpSecurity`의 catch-all 규칙은 HTTP 요청만 덮으므로 메시지 소비자 경로는 막아 주지 않는다.

### 10. 시작 구조를 정하는 기준

- 지금 공유 규칙·불변식이 있는 영역(결제·정산·상태 전이)은 처음부터 Domain Model.
- 규칙이 거의 없는 영역(공지·코드 테이블)은 스크립트나 프레임워크 CRUD.
- 불확실하면 스크립트로 시작하되 신호를 정해 둔다: 같은 검증이 두 번째 유스케이스에 복사되는 순간, 또는 상태 전이 규칙이 생기는 순간 그 부분을 도메인 객체로 옮긴다.
- 어느 경우든 유스케이스마다 트랜잭션·권한 경계는 한 곳(Service Layer 연산·명령 핸들러)에 둔다.
