# domain-modeling/07-domain-logic-patterns-and-service-layer — 도메인 로직 패턴 3택과 Service Layer, CQS — 정리 (힌트)

## 해결하는 문제

업무 로직을 담는 구조는 하나가 아니다. 규칙이 적을 때 좋은 구조는 규칙이 늘면 같은 검증을 여러 벌 복사하게 만들고, 규칙이 많을 때 좋은 구조는 단순 CRUD에서는 파일과 매핑만 늘린다. 그리고 유스케이스의 경계(트랜잭션·권한)를 정하는 곳이 없으면 요청마다 경계가 달라진다.

쉬운 예: 동네 가게의 장부.

```text
  손님 몇 명, 규칙 몇 개      → 주문마다 메모 한 장에 다 적는다(빠르다)
  손님 수백, 할인·포인트·등급 → 메모마다 "VIP는 한도 2배" 같은 조건을 다시 적는다
                                 규칙 하나 바뀌면 메모 양식을 전부 고친다
  반대로                     → 메모 한 장이면 될 "전화번호 변경"에 서류 다섯 장을 쓴다
```

똑같은 구조다.\
주문 생성·줄 추가·수량 변경 세 유스케이스가 각자 "주문 한도 100만 원"을 검사하는 스크립트다. "VIP 한도 200만 원"이 추가되면 세 스크립트를 고친다. 반대로 공지 제목 수정 같은 단순 기능을 엔티티·리포지토리·매퍼로 짜면 5파일 23줄이 된다(아래 실험 A·B). 또 컨트롤러가 리포지토리 세 개를 각자 부르면, 하나가 실패해도 앞의 둘은 이미 커밋돼 있다(실험 C).

## 동작·원리

### 1. 세 패턴 — 같은 "주문 줄 추가"를 어떻게 짜나

| 패턴 | PoEAA 카탈로그 정의 | 모양 |
|---|---|---|
| Transaction Script | "Organizes business logic by procedures where each procedure handles a single request from the presentation." | 요청 하나 = 프로시저 하나. DB를 직접(또는 얇은 래퍼로) 부른다. 공통 부분은 하위 프로시저로 뺀다 |
| Table Module | "A single instance that handles the business logic for all rows in a database table or view." | 테이블 하나 = 클래스 하나, 인스턴스 하나가 모든 행을 다룬다 |
| Domain Model | "An object model of the domain that incorporates both behavior and data." | 의미 있는 개체마다 객체 하나, 객체들이 서로 연결된 망 |

```text
  Transaction Script            Table Module                    Domain Model
  addItem(orderId, …) {         orders = new OrderTable(rows)   order = repo.find(id)
    lines = db.select(…)        orders.addItem(orderId, …)      order.addItem(price, qty)
    if (lines.size >= 10) …       // 내부에서 rows 중 해당 행을    // 규칙은 Order 안
    total = Σ …                   //  찾아 규칙 적용               repo.save(order)
    if (total > 한도) …
    db.insert(…)
  }
```

- Table Module은 레코드 셋(테이블 모양 데이터 구조)을 잘 지원하는 환경(.NET·COM)에서 강하고, 도구 지원이 없으면 구현이 어렵다고 PoEAA 2장이 쓴다(2장 요약 블로그로 확인, 원문 쪽수 `[?]`).

### 2. 복잡도 곡선 — 언제 무엇이 이기나

```text
  변경 노력
    ▲                        Transaction Script
    │                      ╱
    │                   ╱        ← 규칙이 늘면 조건문·복사가 빠르게 쌓인다
    │                ╱   ___────  Table Module
    │      ___────╱───
    │ ___──    ╱         ________ Domain Model
    │───── ╱_____────────          ← 처음 비용(학습·매핑)은 높고 기울기는 완만
    └──────────────────────────────▶ 도메인 로직 복잡도
          ↑ 이 교차점은 측정할 수 없다 — 판단이다
```

- PoEAA 2장 「Making a Choice」의 정성 그림을 이 노트가 다시 그린 것이다(원 그림의 축 배치·번호는 확인 못 함 `[?]`).
- Fowler의 논지(2장, 요약 블로그와 카탈로그로 확인한 범위)
  - Domain Model의 가치는 익숙해지면 점점 복잡해지는 로직을 잘 정돈된 방식으로 다룰 기법이 많다는 데 있다. 수익 인식 규칙이 늘면 Domain Model은 전략 객체를 더하고, Transaction Script는 스크립트의 조건문을 늘린다.
  - 도메인 로직의 복잡도는 정량적으로 잴 수 없다. 그래서 교차점은 경험 많은 사람의 판단이다.
- Evans 4장 「Smart UI」도 같은 방향이다. 업무 규칙이 적고 입력·표시가 대부분인 단순 프로젝트에서는 모든 로직을 UI에 두는 접근이 생산성이 높다. 대신 복잡도가 쌓이면 더 풍부한 동작으로 가는 매끄러운 길이 없다(Evans가 든 단점).

### 3. Service Layer — 유스케이스의 경계

```text
   웹 컨트롤러   배치   메시지 소비자   관리 도구         ← 여러 종류의 클라이언트
        └─────────┴──────────┴──────────┘
                       ▼
   ┌──────────── Service Layer ─────────────┐
   │ placeOrder(cmd) / addItem(cmd) / …     │  유스케이스 = 연산 하나
   │  · 트랜잭션 시작·커밋                    │  ← 경계는 여기
   │  · 권한 검사                             │
   │  · 불러오기 → 도메인에 시키기 → 저장     │
   │  · 여러 응답 조율(알림·메시지)           │
   └────────────────────────────────────────┘
                       ▼
              Domain Model / 스크립트
```

- 정의(PoEAA, Randy Stafford): "Defines an application's boundary with a layer of services that establishes a set of available operations and coordinates the application's response in each operation."
- 두 구현 방식(Stafford)
  - *domain facade*: Domain Model 위의 얇은 파사드. 업무 로직을 구현하지 않는다.
  - *operation script*: 더 두꺼운 클래스가 애플리케이션 로직을 직접 구현하고, 도메인 로직은 도메인 객체에 맡긴다.
- 언제 필요한가(Stafford "When to Use It"): 업무 로직의 클라이언트가 여러 종류이고, 유스케이스 응답이 여러 트랜잭션 자원에 걸칠 때. 클라이언트가 한 종류(예: UI 하나)이고 응답이 여러 트랜잭션 자원에 걸치지 않으면 아마 필요 없다.
- 두께: Fowler는 2장에서 Service Layer를 두더라도 얇게 두는 쪽을 선호한다고 쓴다(2장 요약 블로그로 확인). 01번의 Evans 애플리케이션 계층 정의("얇게, 업무 규칙 없음")와 같은 방향이다.
- 권한 검사: Spring Security 7.1 문서는 메서드 보안의 용도로 "Enforcing security at the service layer"를 들고, 어노테이션 기반 메서드 보안을 쓰면 어노테이션이 없는 메서드는 보호되지 않는다고 경고한다.
- 트랜잭션: Spring Data JPA 4.1 문서는 리포지토리 CRUD 메서드가 각자 `@Transactional`(읽기는 `readOnly`)을 갖고, 여러 리포지토리에 걸친 트랜잭션 경계는 "facade or service"가 정한다고 쓴다. 바깥 트랜잭션이 있으면 리포지토리의 설정은 무시되고 바깥 설정이 쓰인다. 직접 선언한 쿼리 메서드에는 기본 트랜잭션 설정이 없다.

### 4. CQS — 명령과 조회를 나눈다

- *CQS(Command Query Separation)*: 메서드를 두 종류로 나눈다(Fowler bliki "CommandQuerySeparation", 2005-12-05).
  - 조회(query): 결과를 돌려주고 관찰 가능한 상태를 바꾸지 않는다.
  - 명령(command): 상태를 바꾸고 값을 돌려주지 않는다.
- 용어는 Bertrand Meyer가 『Object-Oriented Software Construction』에서 만들었다(같은 글). Fowler는 스택 `pop`처럼 상태를 바꾸는 조회가 유용한 관용구인 예외도 있다고 쓴다. 함수 수준의 상세는 [software-design/08-function-design](../../software-design/08-function-design/2-summary.md) §3.
- 유스케이스 수준으로 올리면: Service Layer의 연산도 "상태를 바꾸는 명령 유스케이스"와 "보여 주기만 하는 조회 유스케이스"로 나눈다. 조회는 도메인 모델을 거치지 않고 DTO로 바로 읽어도 된다(원본 [domain-vs-application-logic](../domain-vs-application-logic/2-summary.md) 회색지대 4). 모델 자체를 둘로 나누는 것이 CQRS(21번)다.

### 실험 A: 규칙 하나 추가 — Transaction Script vs Domain Model

- 환경: JDK 21(`eclipse-temurin:21-jdk`, openjdk 21.0.12, `--cpus=2`, 네트워크 없음), 실험용 git 저장소, 2026-10-03.
- `ts/`: `PlaceOrderScript`·`AddItemScript`·`ChangeQtyScript`가 각자 합계를 계산해 "한도 100만 원"을 검사한다.
- `dm/`: `Order.addItem`·`changeQty`가 `check()` → `limit()` 하나를 지난다. `OrderService`는 불러오기·시키기만 한다.
- 새 규칙: "VIP 고객은 한도 200만 원".

(실험, git 2.43 + `grep -l`, 두 변형 모두 JDK 21 `javac` 컴파일 확인, 2026-10-03)

```text
== 규칙 1개(주문 한도) 사본 수
ts   3
dm   1
== git diff --stat (VIP 한도 추가)
 dm/Order.java            | 2 +-
 ts/AddItemScript.java    | 3 ++-
 ts/ChangeQtyScript.java  | 3 ++-
 ts/PlaceOrderScript.java | 3 ++-
 4 files changed, 7 insertions(+), 4 deletions(-)
```

### 실험 B: 단순 CRUD 하나 — 같은 기능의 코드 양

- 기능: 공지 제목 수정. 지켜야 할 불변식이 없다.
- `crud_ts/`: 스크립트 1개(테이블 흉내 맵에 바로 쓴다).
- `crud_dm/`: `Notice`(엔티티)·`NoticeRepository`(포트)·`NoticeRow`(저장 형식 매핑)·`InMemoryNoticeRepository`(어댑터)·`RenameNoticeService`.

(실험, 2026-10-03) `wc -l crud_ts/*.java` · `wc -l crud_dm/*.java | tail -1` · 폴더별 파일 수

```text
5 crud_ts/RenameNoticeScript.java
  23 합계
files ts=1 dm=5
```

- 출력 읽는 법: 스크립트는 1파일 5줄, 도메인 모델 구조는 5파일 23줄(`합계`는 `crud_dm` 다섯 파일의 줄 수 합).
- 관찰(A·B 함께)
  - 규칙이 여러 유스케이스에 걸린 곳에서는 Domain Model이 변경 파일 수를 줄였다(TS 3 vs DM 1).
  - 불변식이 없는 기능에서는 Domain Model 구조가 코드만 늘렸다(5파일 23줄 vs 1파일 5줄). `Notice.rename()`은 setter와 하는 일이 같다.
  - 축소 모델이다. 줄 수·파일 수는 이 코드의 값이지 일반 법칙이 아니다. 같은 저장소에서 두 패턴을 기능별로 섞어 쓸 수도 있다.

### 실험 C: 트랜잭션 경계 — 컨트롤러가 리포지토리를 각각 부를 때 (PostgreSQL 17)

- 환경: PostgreSQL 17.11 전용 일회용 컨테이너(`postgres:17`, 포트 미개방, 전용 네트워크), PostgreSQL JDBC 42.7.3, JDK 21, 2026-10-03.
- 이체: `debit(A, 100)` → `credit(B, 100)` → `insert transfer_log(request_id)`. `request_id`는 기본 키다. 클라이언트가 같은 `req-1`로 두 번 보낸다(재시도).

```java
// (1) 서비스 계층 없음 — 리포지토리 호출마다 자기 커넥션·자동 커밋
try (var c = conn()) { debit(c, "A", 100); }
try (var c = conn()) { credit(c, "B", 100); }
try (var c = conn()) { log(c, reqId); }

// (2) 서비스 계층 — 유스케이스 = 트랜잭션 하나
try (var c = conn()) {
    c.setAutoCommit(false);
    try { debit(c, "A", 100); credit(c, "B", 100); log(c, reqId); c.commit(); }
    catch (SQLException e) { c.rollback(); throw e; }
}
```

(실험, PostgreSQL 17.11 + JDBC 42.7.3, 2026-10-03) 시작 잔액 `A=1000 B=0`

```text
## (1) 컨트롤러가 리포지토리를 각각 호출 (호출마다 자동 커밋)
  시도1: 성공  → A=900 B=100
  시도2: 실패 SQLState 23505 → A=800 B=200
## (2) 서비스 계층 한 트랜잭션
  시도1: 성공  → A=900 B=100
  시도2: 실패 SQLState 23505 → A=900 B=100
```

- 관찰: 두 번째 시도는 두 경우 모두 `23505`(unique_violation)로 실패했다. (1)에서는 실패한 요청의 출금·입금이 이미 커밋돼 돈이 두 번 옮겨졌다. (2)에서는 셋이 함께 롤백됐다.
- Spring으로 옮기면: `CrudRepository`에서 상속한 메서드(`save`·`findById` 등)는 각자 트랜잭션을 가지므로, 바깥 `@Transactional`이 없는 컨트롤러에서 연달아 부르면 (1)과 같은 모양이 된다. 직접 선언한 쿼리 메서드(default 메서드 포함)는 기본 트랜잭션 설정이 없어서, 리포지토리 인터페이스나 서비스에 `@Transactional`을 붙여야 한다(Spring Data JPA 4.1 문서의 기본 동작 서술에서 끌어낸 해석, 이 실험은 JDBC로 재현).

### 실험 D: 조회처럼 생긴 명령 — CQS 위반

```java
if (debug) System.out.println("    debug: next=" + jobs.poll());   // 로그를 남기려다 하나를 꺼낸다
String j = jobs.poll();
```

(실험, JDK 21 temurin, 2026-10-03) 작업 5개짜리 큐

```text
poll 로그, debug=false → 처리 5/5
poll 로그, debug=true:
    debug: next=j1
    debug: next=j3
    debug: next=j5
  → 처리 2/5
peek 로그, debug=true:
    debug: next=j1
    debug: next=j2
    debug: next=j3
    debug: next=j4
    debug: next=j5
  → 처리 5/5
```

- 관찰: 값을 돌려주면서 상태를 바꾸는 `poll()`을 로그 식에 넣자, 디버그 로그를 켜는 것만으로 작업 3개가 처리되지 않았다. 상태를 바꾸지 않는 `peek()`로는 5/5다.

## 쓰이는 자료구조·알고리즘

- **명령 핸들러 = 입력 → 결과 함수** — 유스케이스 하나를 `Command`(입력 값 객체)와 `Result`로 감싼 함수로 본다. 핸들러를 고르는 디스패치는 `명령 타입 → 핸들러` 맵이다. [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- **트랜잭션 = 전부 아니면 전무** — 실험 C의 (2)는 원자성(atomicity)을 앱 경계에 맞춘 것이다. DB 내부 구현(로그·롤백)은 [database/13-transactions-acid](../../database/13-transactions-acid/2-summary.md), 앱 코드에서 경계를 정하는 법은 [database/24-transaction-boundaries-in-app-code](../../database/24-transaction-boundaries-in-app-code/2-summary.md).
- **유일 제약 = 멱등 키** — `transfer_log.request_id` 기본 키가 재시도를 막았다. 막힌 요청을 어떻게 응답할지는 [reliability/13-idempotency](../../reliability/13-idempotency/2-summary.md).
- **Table Module의 레코드 셋** — 행 배열(또는 데이터 테이블) 위에서 반복·필터로 규칙을 적용한다. 행 단위 객체가 없다.
- **큐의 `poll`·`peek`** — 같은 자료구조의 명령·조회 쌍. [data-structure/04-queue-deque](../../data-structure/04-queue-deque/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 패턴을 고르는 질문

| 질문 | 기울면 |
|---|---|
| 같은 규칙이 둘 이상의 유스케이스에 걸리나? (실험 A) | Domain Model |
| 상태 전이·필드 사이 불변식이 있나? | Domain Model (06번) |
| 기능 대부분이 입력·저장·표시이고 규칙이 거의 없나? (실험 B) | Transaction Script, 또는 프레임워크 CRUD |
| 팀·플랫폼이 레코드 셋 중심인가? | Table Module |
| 규칙이 지금 적지만 늘 것이 확실한가? | 처음엔 스크립트, 같은 검증이 두 번째 복사될 때 그 부분을 도메인 객체로 옮긴다 |

- 한 시스템 안에서도 기능별로 다르게 고를 수 있다. 결제·정산은 Domain Model, 공지·코드 테이블은 스크립트.

### 2. Service Layer — 명령 핸들러로 쓰기 (Spring 예)

```java
public record AddItemCommand(long orderId, long price, long qty) {}

@Service
public class AddItemHandler {
    private final OrderRepository orders;
    public AddItemHandler(OrderRepository orders) { this.orders = orders; }

    @Transactional                                       // 유스케이스 = 트랜잭션 하나
    @PreAuthorize("hasRole('SELLER')")                   // 권한 검사도 이 경계에서
    public OrderSummary handle(AddItemCommand cmd) {     // 입력 → 결과
        Order order = orders.findById(cmd.orderId()).orElseThrow();
        order.addItem(cmd.price(), cmd.qty());           // 판단은 도메인
        return OrderSummary.from(order);                 // 저장은 더티 체킹(02번) 또는 명시 save
    }
}
```

- 컨트롤러·배치·메시지 소비자는 모두 이 핸들러를 부른다. 경계(트랜잭션·권한)가 진입점마다 달라지지 않는다.
- 조회 유스케이스는 `@Transactional(readOnly = true)`와 DTO 프로젝션으로 따로 둔다.
- 기본 프록시 모드에서는 `@Transactional`·`@PreAuthorize`가 프록시로 동작하므로 같은 클래스 안에서 자기 메서드를 부르면 적용되지 않는다. AspectJ 위빙 모드(`mode = AdviceMode.ASPECTJ`)는 자기 호출에도 적용된다(Spring Framework 「Using @Transactional」, 원본 [pojo](../pojo/2-summary.md) 「스프링과 POJO」의 self-invocation).

### 3. 진단

```bash
# 리포지토리를 둘 이상 직접 주입받은 컨트롤러 (경계가 컨트롤러에 있다는 신호)
grep -rlE "@(Rest)?Controller" src/main/java | xargs grep -cE "private final \w+Repository" | grep -vE ":(0|1)$"
# 같은 검증식의 사본 (예: 한도 상수)
grep -rn "1_000_000" src/main/java
```

```sql
-- PostgreSQL: 부분 커밋 흔적 — 이체 로그 없이 잔액만 움직인 건이 있나 (예시 스키마)
SELECT e.account_id, e.request_id FROM account_entry e
LEFT JOIN transfer_log t ON t.request_id = e.request_id
WHERE t.request_id IS NULL;
```

## 장애 시나리오와 대처

### 1. 규칙이 늘었는데 Transaction Script 유지 → 같은 검증 N벌 (⚠ 커리큘럼)

- **현상**: 규칙 하나 바꾸는 PR이 스크립트 여러 개를 건드린다. 어떤 유스케이스는 옛 한도로 동작한다.
- **보이는 형태**: 같은 상수·조건식이 여러 스크립트에 있다(실험 A: 사본 3). VIP 고객이 "줄 추가는 되는데 수량 변경은 한도 초과로 막힌다"고 문의한다.
- **원인**: 처음 규칙이 적을 때 고른 구조를 규칙이 늘어난 뒤에도 유지했다.
- **대처**: 사본이 두 번째로 생기는 시점에 그 규칙을 도메인 객체로 옮긴다. 스크립트는 "불러오기 → 시키기 → 저장"으로 줄인다(실험 A의 `dm/` 모양).

### 2. 단순 CRUD에 풍부한 모델 → 매핑 비용만 증가 (⚠ 커리큘럼)

- **현상**: 필드 하나 추가에 엔티티·DTO·매퍼·리포지토리·테스트를 고친다. 리뷰가 형식 검토로 끝난다.
- **보이는 형태**: 엔티티 메서드가 setter와 같은 일을 한다. 실험 B에서 5파일 23줄 vs 1파일 5줄.
- **원인**: 불변식이 없는 기능에 Domain Model 구조를 씌웠다.
- **대처**: 불변식이 없는 기능은 스크립트나 프레임워크 CRUD로 둔다. 규칙이 생기면 그 기능만 옮긴다.

### 3. 서비스 계층 없이 컨트롤러가 여러 리포지토리 호출 → 트랜잭션 경계가 요청마다 다름 (⚠ 커리큘럼)

- **현상**: 실패한 요청인데 일부 변경이 남는다. 재시도하면 돈·재고가 두 번 움직인다.
- **보이는 형태**: 오류 응답(예: SQLState `23505` 중복 키) 뒤에도 잔액이 바뀌어 있다(실험 C: `A=800 B=200`). 대사 쿼리에서 로그 없는 잔액 변동이 나온다.
- **원인**: 리포지토리 호출마다 트랜잭션이 따로 커밋됐다. 유스케이스 단위로 경계를 잡는 곳이 없었다.
- **대처**: 유스케이스마다 Service Layer 연산(명령 핸들러) 하나를 두고 거기서 트랜잭션을 연다. 컨트롤러는 그 연산 하나만 부른다. 이미 생긴 부분 커밋은 원장·로그로 찾아 정정한다(24·25번).

### 4. 조회가 상태를 바꾼다 — CQS 위반

- **현상**: 디버그 로그를 켜거나 모니터링이 조회 API를 부르면 데이터가 사라지거나 카운터가 오른다.
- **보이는 형태**: 로그 수준에 따라 처리 건수가 다르다(실험 D: 5/5 vs 2/5). GET 요청 재시도로 쿠폰이 두 번 발급된다.
- **원인**: 값을 돌려주는 메서드가 상태도 바꿨다(`poll`, `getAndIncrement`, "조회하면서 만료 처리").
- **대처**: 조회와 명령을 나눈다(`peek` + `poll`, `findCoupon` + `issueCoupon`). 꼭 합쳐야 하면 이름에 동작을 드러낸다(`popNext`). HTTP에서는 상태를 바꾸는 동작을 GET에 두지 않는다.

### 5. 권한 검사를 컨트롤러에만 → 다른 진입점이 우회

- **현상**: 웹에서는 막히는 작업이 배치·메시지 소비자·내부 API로는 실행된다.
- **보이는 형태**: 권한 검사 코드가 `@RestController`·URL 패턴 설정에만 있다. 메서드 보안을 쓰는데 새 메서드에 어노테이션을 빠뜨렸다(Spring Security 문서: 어노테이션 없는 메서드는 보호되지 않는다).
- **원인**: 경계를 진입점마다 따로 지켰다.
- **대처**: 권한 검사를 Service Layer 연산에 둔다. 메서드 보안을 쓰면 `HttpSecurity`에도 모든 요청을 덮는(catch-all) 인가 규칙을 둔다(같은 문서의 권고). 이 규칙은 HTTP 요청만 덮으므로 배치·메시지 소비자 경로는 Service Layer 연산의 메서드 보안이나 명시 검사로 지킨다. 진입점 × 권한 없는 사용자 테스트를 둔다.

## 핵심 문장

- Transaction Script는 요청 하나를 프로시저 하나로, Table Module은 테이블 하나를 인스턴스 하나로, Domain Model은 행위와 데이터를 함께 가진 객체 망으로 업무 로직을 짠다(PoEAA).
- 어느 쪽이 이기는지는 도메인 로직 복잡도에 달렸고, Fowler는 그 복잡도를 정량적으로 잴 수 없다고 본다. 실험에서는 공유 규칙 추가에 TS 3파일 vs DM 1파일, 불변식 없는 CRUD에 TS 1파일 5줄 vs DM 5파일 23줄이었다.
- Service Layer는 애플리케이션의 경계다. 유스케이스 연산마다 트랜잭션과 권한 검사를 여기서 정하고, 판단은 도메인에 맡긴다.
- PostgreSQL 17 실험에서 리포지토리마다 자동 커밋하면 실패한 재시도가 잔액을 한 번 더 옮겼고, 한 트랜잭션으로 묶으면 함께 롤백됐다.
- CQS는 조회는 상태를 바꾸지 않고 명령은 값을 돌려주지 않게 나눈다. 조회처럼 생긴 명령은 로그 하나로 데이터를 잃게 할 수 있다.

## 관련 주제·근거

- 선행: [01-domain-vs-application-logic](../01-domain-vs-application-logic/2-summary.md) · [06-anemic-vs-rich-model](../06-anemic-vs-rich-model/2-summary.md)
- 연결
  - [02-pojo-and-persistence-ignorance](../02-pojo-and-persistence-ignorance/2-summary.md) — 더티 체킹, 프록시
  - [21-cqrs](../21-cqrs/2-summary.md) · [24-double-entry-ledger](../24-double-entry-ledger/2-summary.md) · [25-reconciliation](../25-reconciliation/2-summary.md)
  - 원본 [domain-vs-application-logic](../domain-vs-application-logic/2-summary.md) 「애플리케이션 서비스 로직」·회색지대 4(조회)
  - [software-design/08-function-design](../../software-design/08-function-design/2-summary.md)(CQS) · [software-design/12-simple-design-and-yagni](../../software-design/12-simple-design-and-yagni/2-summary.md) · [software-design/33-aop-and-proxies](../../software-design/33-aop-and-proxies/2-summary.md)
  - [database/25-data-source-patterns](../../database/25-data-source-patterns/2-summary.md) — 데이터 소스 패턴(Table Data Gateway·Row Data Gateway·Active Record·Data Mapper)과 도메인 로직 패턴의 짝
  - [database/13-transactions-acid](../../database/13-transactions-acid/2-summary.md) · [database/24-transaction-boundaries-in-app-code](../../database/24-transaction-boundaries-in-app-code/2-summary.md) · [reliability/13-idempotency](../../reliability/13-idempotency/2-summary.md)
- 근거
  - Fowler 『PoEAA』(2002) 9장 Domain Logic Patterns — 카탈로그 <https://martinfowler.com/eaaCatalog/transactionScript.html> · <https://martinfowler.com/eaaCatalog/tableModule.html> · <https://martinfowler.com/eaaCatalog/domainModel.html> · <https://martinfowler.com/eaaCatalog/serviceLayer.html>
  - 『PoEAA』 2장 Organizing Domain Logic(Making a Choice, Service Layer) — 원문 대신 요약으로 확인한 범위만 단정 <https://wand-ta.hatenablog.com/entry/2019/02/02/202542>
  - 『PoEAA』 「Service Layer」(Randy Stafford) — domain logic vs application logic, domain facade vs operation script, When to Use It <https://www.informit.com/articles/article.aspx?p=1398617&seqNum=4>
  - Evans 『DDD』 4장 Smart UI "Anti-Pattern"(장점·단점) — 2003 최종 원고 PDF 대조
  - Fowler bliki "CommandQuerySeparation"(2005-12-05) <https://martinfowler.com/bliki/CommandQuerySeparation.html> · Meyer 『Object-Oriented Software Construction』(CQS 용어 출처, 판·장 번호 `[?]`)
  - Spring Data JPA 4.1 Reference "Transactionality" <https://docs.spring.io/spring-data/jpa/reference/jpa/transactions.html>
  - Spring Security 7.1 Reference "Method Security" <https://docs.spring.io/spring-security/reference/servlet/authorization/method-security.html>
- 실험 목록
  - A. 공유 규칙(VIP 한도) 추가 `git diff --stat`: TS 3파일 vs DM 1파일, 사본 수 3 vs 1 — JDK 21.0.12
  - B. 단순 CRUD(공지 제목 수정) 코드 양: 1파일 5줄 vs 5파일 23줄
  - C. 트랜잭션 경계: 같은 요청 ID 재시도, 자동 커밋 3회 `A=800 B=200` vs 한 트랜잭션 `A=900 B=100`(둘 다 SQLState 23505) — PostgreSQL 17.11 전용 컨테이너(포트 미개방), JDBC 42.7.3
  - D. CQS 위반 `poll` 로그: 처리 2/5 vs `peek` 5/5
  - 공통: `--cpus=2`
