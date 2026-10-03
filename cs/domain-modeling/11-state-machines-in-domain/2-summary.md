# domain-modeling/11-state-machines-in-domain — 도메인 상태 기계: 상태·이벤트·가드로 수명 주기를 닫는다 — 정리 (힌트)

## 해결하는 문제

주문·결제·구독·티켓처럼 **수명 주기**가 있는 것은 "지금 어떤 상태인가"에 따라 할 수 있는 일이 달라진다.

```text
  흔한 코드 모양 — 메서드마다 "안 되는 경우"를 떠오르는 대로 막는다
  ship():    if (status == CANCELLED || status == PLACED) throw ...;  status = SHIPPED;
  cancel():  if (status == SHIPPED || status == DELIVERED) throw ...; status = CANCELLED;
  refund():  if (status == PLACED) throw ...;                          status = REFUNDED;
  → 막는 목록에 빠진 상태는 전부 "통과"다. 환불된 주문도 배송된다.
```

- 해법: 허용되는 (상태, 이벤트) 조합을 **한 곳의 표**로 적고, 표에 없는 것은 거부한다.
  - *유한 상태 기계(FSM, finite state machine)*: 유한한 상태 집합, 이벤트(입력), 전이 함수 `(상태, 이벤트) → 다음 상태`로 이루어진 모델.
  - *가드(guard)*: 전이에 붙는 조건. "출고는 주소 검증이 끝났을 때만"처럼 같은 (상태, 이벤트)라도 데이터에 따라 허용 여부가 갈린다.

쉬운 예: 지하철 개찰구다.
- 상태는 "잠김"과 "열림" 둘이다. 카드를 대면(이벤트) 잔액이 있을 때만(가드) 열린다.
- 열림 상태에서 지나가면 다시 잠긴다. 잠김 상태에서 밀면 아무 일도 없다.
- 개찰구 회로에 "잠김에서 밀면 열림"이 없으니, 아무리 밀어도 안 열린다.

똑같은 구조다. 주문의 상태 기계는 개찰구 회로처럼 **허용된 화살표만** 갖고 있어야 한다.

실무 예:
- 환불 완료된 주문에 출고 이벤트가 들어와 택배가 나갔다(커리큘럼 ⚠ "불법 전이").
- 고객 취소와 창고 출고가 같은 순간 들어와 **둘 다** 성공했다. 상태는 마지막에 쓴 쪽이 이기고, 취소 환불과 출고가 함께 실행됐다(커리큘럼 ⚠ "동시 전이 경합").

기초 — 전이 표를 `EnumMap`으로 만들기, 결과 3갈래(APPLIED·IGNORED·REJECTED), BFS 도달성 검사 — 는 연습 문제 [basic/09-order-state](../basic/09-order-state/2-summary.md)에 있다. 이 노트는 그 위에 **가드·이벤트·계층 상태, 동시 전이, 영속화와 이력**을 더한다.

## 동작·원리

### 1. 상태 전이도 — 이 노트의 명세

```text
            PAY            PREPARE           SHIP            DELIVER          REQUEST_RETURN        REFUND
  PLACED ───────> PAID ───────────> PREPARING ─────> SHIPPED ───────> DELIVERED ──────────> RETURN_REQUESTED ─────> REFUNDED
    │               │                  │
    │ CANCEL        │ CANCEL           │ CANCEL
    └───────────────┴──────────────────┴──────────> CANCELLED        (SHIPPED부터는 취소 대신 반품)

  상태 8 × 이벤트 7 = 56칸, 허용 9칸. 나머지 47칸은 거부.
```

- 화살표 하나 = 전이 표의 한 칸이다. 표에 없는 칸은 "거부"로 **기본값을 닫는다.**
  - *허용 목록(allowlist)*: 된다고 적힌 것만 된다. 새 상태가 생겨도 기본은 거부다.
  - *차단 목록(blocklist)*: 안 된다고 적힌 것만 막는다. 새 상태가 생기면 기본이 통과다.

### 2. 전이 = (상태, 이벤트, 가드) → (다음 상태, 효과)

```text
  ┌─────────┐  이벤트 SHIP [가드: 주소 검증됨]  / 효과: ShipmentRequested 발행  ┌─────────┐
  │PREPARING│ ─────────────────────────────────────────────────────────────> │ SHIPPED │
  └─────────┘                                                                └─────────┘
     표에 칸이 없으면 → 거부 (불법 전이)
     칸은 있는데 가드가 거짓 → 거부 (조건 불충족 — 이유를 돌려준다)
```

- 표기 `이벤트 [가드] / 효과`는 Harel statechart와 UML 상태 기계에서 쓰는 모양이다.
- 거부를 둘로 나누면 진단이 쉬워진다. "그런 전이는 없다"(코드·연동 오류)와 "지금은 조건이 안 된다"(정상 업무 흐름)는 대응이 다르다.
- 효과는 전이가 **성공한 뒤에만** 일어나야 한다. 효과를 도메인 이벤트로 남기면 [09-domain-events](../09-domain-events/2-summary.md)의 발행 시점 규칙을 그대로 따른다.

### 3. 계층과 동시 상태 — Harel 1987

```text
  평평한 FSM: "결제 대기 중 보류", "준비 중 보류", ... 상태 × 보류 여부 만큼 상태가 늘어난다

  statechart의 계층(hierarchy):
  ┌─ 진행 중(ACTIVE) ─────────────────────┐
  │  PAID ──> PREPARING                    │ ── CANCEL ──> CANCELLED
  └────────────────────────────────────────┘
     CANCEL 화살표 하나를 바깥 상자에 그리면 안의 상태 전부에 적용된다

  statechart의 직교(orthogonal) 영역:
  ┌─ 주문 ──────────────┬──────────────────┐
  │ 처리: PAID→PREPARING │ 결제: AUTH→CAPTURE│   두 영역이 동시에 각자 상태를 가진다
  └─────────────────────┴──────────────────┘
```

- Harel, "Statecharts: A visual formalism for complex systems", *Science of Computer Programming* 8(3), 1987, pp.231–274. 초록이 "conventional state-transition diagrams with essentially three elements, dealing, respectively, with the notions of hierarchy, concurrency and communication"이라고 적는다(계층·동시성·통신). 예비판은 Weizmann 기술 보고서 CS84-05(1984, 논문 참고문헌 [12]). UML 상태 기계가 이 형식을 받아들였다.
- 도메인 모델링에서 쓰는 법
  - 계층: "배송 전이면 언제든 취소"처럼 여러 상태에 공통인 전이를 한 번만 적는다.
  - 직교 영역: 주문 처리 상태와 결제 상태를 한 enum에 곱하지 않고 따로 둔다. 곱하면 상태 수가 곱으로 늘어난다(예: 처리 8 × 결제 4 = 32).

### 실험: if문 차단 목록 vs 전이 표 — 불법 전이가 몇 칸 새나

- 환경: JDK 21(eclipse-temurin:21-jdk), 단일 파일 `Fsm.java`, 2026-10-03.
- 같은 명세(위 그림, 허용 9칸)를 두 방식으로 구현했다. if문 쪽은 "흔한 모양을 흉내 낸 예시 코드"다. 수치는 이 예시 코드의 성질이지 if문 구현 일반의 성질이 아니다.
- (상태, 이벤트) 쌍을 전부 넣어 명세와 판정을 비교한다. 이어서 새 요구 "결제 후 보류(ON_HOLD)"를 넣어 다시 센다. 상태 ON_HOLD와 이벤트 HOLD가 하나씩 늘어 9 × 8 = 72칸이 되고, 허용 칸은 `PAID--HOLD`·`ON_HOLD--PREPARE`·`ON_HOLD--CANCEL` 3개가 늘어 12칸이다.

```java
// 전이 표: 허용 목록. 없는 칸은 null → 거부
static Optional<S> tableStyle(Map<S, Map<E, S>> t, S st, E e) { return Optional.ofNullable(t.get(st).get(e)); }

// if문: 메서드마다 차단 목록 (예시)
case SHIP:   if (st == S.CANCELLED || st == S.PLACED) return Optional.empty(); return Optional.of(S.SHIPPED);
case CANCEL: if (st == S.SHIPPED || st == S.DELIVERED) return Optional.empty(); return Optional.of(S.CANCELLED);
case REFUND: if (st == S.PLACED) return Optional.empty(); return Optional.of(S.REFUNDED);
```

(실험, JDK 21 temurin, 2026-10-03)

```text
[상태 8개] (상태,이벤트) 쌍 56, 명세가 허용 9
  if문 구현: 명세에 없는데 통과 19, 명세에 있는데 거부 0
  전이 표 구현: 명세와 다른 판정 0
  if문이 통과시킨 불법 전이: [PAID--SHIP-->SHIPPED, PAID--REFUND-->REFUNDED, PREPARING--PREPARE-->PREPARING, PREPARING--REFUND-->REFUNDED, SHIPPED--PREPARE-->PREPARING, SHIPPED--SHIP-->SHIPPED, SHIPPED--REFUND-->REFUNDED, DELIVERED--PREPARE-->PREPARING, DELIVERED--SHIP-->SHIPPED, DELIVERED--REFUND-->REFUNDED, RETURN_REQUESTED--PREPARE-->PREPARING, RETURN_REQUESTED--SHIP-->SHIPPED, RETURN_REQUESTED--CANCEL-->CANCELLED, REFUNDED--PREPARE-->PREPARING, REFUNDED--SHIP-->SHIPPED, REFUNDED--CANCEL-->CANCELLED, REFUNDED--REFUND-->REFUNDED, CANCELLED--CANCEL-->CANCELLED, CANCELLED--REFUND-->REFUNDED]
[ON_HOLD 추가 후] (상태,이벤트) 쌍 72, 명세가 허용 12
  if문 구현: 명세에 없는데 통과 21, 명세에 있는데 거부 0
  전이 표 구현: 명세와 다른 판정 0
  if문이 통과시킨 불법 전이: [... 앞의 19개 ..., ON_HOLD--SHIP-->SHIPPED, ON_HOLD--REFUND-->REFUNDED]
```

- (마지막 줄은 지면상 줄였다. 실제 출력은 앞의 19개를 같은 순서로 다 찍은 뒤 두 개를 붙인다.)

- if문 예시는 **허용해야 할 9칸은 다 맞혔다.** 정상 경로 테스트는 전부 통과한다. 그런데 거부해야 할 47칸 중 19칸을 통과시켰다.
- 커리큘럼 ⚠의 "환불된 주문 배송"이 `REFUNDED--SHIP-->SHIPPED`로 나왔다. 반품 요청 없이 출고 전에 환불하는 칸(`PAID--REFUND`)도 샜다.
- 상태 하나(ON_HOLD)를 더하자 if문은 그 상태에서 2칸을 더 새게 했다. 아무도 ON_HOLD를 막는 줄을 쓰지 않았기 때문이다. 표는 새 칸 3개를 적은 것 외에 바뀐 판정이 없다.
- 해석: 차이는 "if냐 표냐"보다 **기본값이 열려 있나 닫혀 있나**에서 나온다. if문으로도 `if (st != PREPARING) 거부`처럼 허용 목록으로 쓰면 같은 효과다. 표는 그 기본값을 구조로 강제하고, 56칸을 한눈에 검사할 수 있게 한다.

### 4. 동시 전이 — 표가 맞아도 경합하면 깨진다

```text
  T1 고객 취소                          T2 창고 출고
  SELECT status → PREPARING             SELECT status → PREPARING
  (앱에서 검사: 취소 가능 ✓)             (앱에서 검사: 출고 가능 ✓)
  UPDATE status='CANCELLED'; 환불 처리   UPDATE status='SHIPPED'; 출고 지시   ← 행 잠금 대기 후 진행
  COMMIT                                COMMIT
  → 둘 다 "성공". 최종 상태는 나중에 쓴 쪽. 환불과 출고가 둘 다 일어났다.
```

- 전이 표는 "PREPARING에서 둘 다 허용"이라고 맞게 답했다. 문제는 **검사와 쓰기 사이에 상태가 바뀔 수 있다**는 것이다.
  - *검사-후-행동 경합(check-then-act race)*: 읽은 값으로 판단하고 쓰는 사이에 다른 트랜잭션이 값을 바꿔, 판단의 전제가 깨지는 경합.
- 해법은 "기대 상태"를 쓰기 조건에 넣는 것이다.
  - *조건부 UPDATE(compare-and-set)*: `UPDATE ... SET status='CANCELLED' WHERE id=? AND status='PREPARING'` — 영향 행 수가 0이면 그 사이 누가 먼저 바꾼 것이다.
  - 또는 버전 열 낙관적 잠금(JPA `@Version`)·`SELECT ... FOR UPDATE`·더 높은 격리 수준. [database/18-app-level-concurrency-patterns](../../database/18-app-level-concurrency-patterns/2-summary.md)

### 실험: 취소와 출고를 동시에 — 읽고-검사-쓰기 vs 조건부 UPDATE vs REPEATABLE READ

- 환경: 전용 일회용 컨테이너 PostgreSQL 17.11, JDK 21, pgjdbc 42.7.4, 2026-10-03. 주문 200건을 PREPARING으로 두고, 주문마다 두 스레드가 취소·출고를 동시에 시도한다. `CyclicBarrier`로 "둘 다 읽은 뒤 쓰기"를 강제한다. 성공한 쪽은 `side_effect`에 후처리 행을 남긴다.

```java
// A. 읽고-검사-쓰기 (READ COMMITTED, PostgreSQL 기본)
String st = select("select status from orders where id=" + id);
barrier.await();
if (!st.equals("PREPARING")) { rollback(); return false; }
update("update orders set status='" + to + "' where id=" + id);
insertSideEffect(id, to); commit();

// B. 조건부 UPDATE
barrier.await();
int n = update("update orders set status='" + to + "', version=version+1 where id=" + id + " and status='PREPARING'");
if (n == 0) { rollback(); return false; }
insertSideEffect(id, to); commit();

// C. A와 같은 코드 + REPEATABLE READ (직렬화 실패 40001은 패배로 셈)
```

(실험, PostgreSQL 17.11 + JDK 21, 2026-10-03)

```text
[A 읽고-검사-쓰기] 주문 200건: 둘 다 성공 200, 하나만 성공 0 | 취소 후처리와 출고가 둘 다 실행된 주문 200 | 최종 상태 CANCELLED=102 SHIPPED=98 
[B 조건부 UPDATE] 주문 200건: 둘 다 성공 0, 하나만 성공 200 | 취소 후처리와 출고가 둘 다 실행된 주문 0 | 최종 상태 CANCELLED=84 SHIPPED=116 
[C 읽고-검사-쓰기 + REPEATABLE READ] 주문 200건: 둘 다 성공 0, 하나만 성공 200 | 취소 후처리와 출고가 둘 다 실행된 주문 0 | 최종 상태 CANCELLED=97 SHIPPED=103 
  C에서 40001(could not serialize) 받은 쪽: 200
```

- A: 겹침을 강제하자 200건 **전부** 두 전이가 모두 성공했다. PostgreSQL READ COMMITTED에서 두 번째 UPDATE는 첫 번째의 행 잠금을 기다렸다가, `WHERE`에 상태 조건이 없으니 그대로 덮어쓴다.
- B: 정확히 한쪽만 이겼다. 진 쪽은 영향 행 0을 보고 거부한다.
- C: 같은 A 코드라도 REPEATABLE READ에서는 진 쪽이 `could not serialize access due to concurrent update`(40001)를 받았다. 재시도 코드가 필요하다.
- 최종 상태의 CANCELLED/SHIPPED 비율은 실행마다 다르다(집필 3회 + 사실 점검 재실행 3회에서 A의 CANCELLED 100~118, SHIPPED 82~100). 둘 다 성공·한쪽만 성공 건수는 6회 모두 같았다. 실제 운영에서는 겹침이 강제되지 않으므로 A의 사고 빈도는 두 요청이 겹칠 확률에 달린다(이 실험은 그 빈도를 재지 않았다). 대신 나면 오류 로그 없이 조용히 난다.

### 5. 영속화와 이력

```text
  orders                              order_transition (이력, 추가만)
  id | status    | version            order_id | seq | from      | event  | to        | at
  7  | SHIPPED   | 4                  7        | 1   | PLACED    | PAY    | PAID      | 10:00
                                      7        | 2   | PAID      | PREPARE| PREPARING | 10:05
                                      7        | 3   | PREPARING | SHIP   | SHIPPED   | 11:20
```

- 현재 상태 열 하나로는 "언제 왜 이 상태가 됐나"에 답하지 못한다. 전이마다 이력 행(또는 도메인 이벤트)을 같은 트랜잭션에 남긴다.
- DB 쪽 이중 방어: `CHECK (status IN (...))`로 없는 상태값을 막는다. 허용 전이 표를 DB 테이블로 두고 트리거로 검사할 수도 있다(앱 밖의 배치·수작업 SQL까지 막고 싶을 때).
- 상태 enum을 JPA로 저장할 때는 `@Enumerated(EnumType.STRING)`을 쓴다. 기본값 `ORDINAL`은 순서 번호를 저장하므로, enum 중간에 상태를 끼워 넣으면 기존 행의 뜻이 바뀐다(Jakarta Persistence `EnumType` 정의).

## 쓰이는 자료구조·알고리즘

- **유한 상태 기계 = 전이 표** — `Map<상태, Map<이벤트, 다음 상태>>`. enum이면 `EnumMap`이 배열 인덱스로 찾는다. 2차원 배열 `next[state][event]`도 같은 것이다.
- **그래프** — 상태 = 정점, 전이 = 간선. 도달성(닿을 수 없는 상태 = 죽은 코드)·종점 상태(나가는 간선 0)는 그래프 질문이다. [data-structure/08-graph](../../data-structure/08-graph/2-summary.md) · [algorithm/11-bfs](../../algorithm/11-bfs/2-summary.md)
- **전수 검사** — 상태 × 이벤트 칸을 모두 돌며 명세와 비교한다. 위 실험의 56·72칸 검사가 그것이다. 칸 수가 작아서 가능한 테스트다.
- **compare-and-set** — 기대 값이 맞을 때만 바꾸는 원자 연산. DB에서는 조건부 UPDATE·버전 열이다. [database/17-occ-and-timestamp-ordering](../../database/17-occ-and-timestamp-ordering/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 순서

1. 상태를 나열한다. "끝난" 상태(나가는 화살표 0)를 표시한다.
2. 이벤트를 나열한다. 도메인 언어로(`SHIP`, `REQUEST_RETURN`).
3. 상태 × 이벤트 표를 **전부** 채운다. 빈칸은 "거부"로 명시한다. 애매한 칸(배송 중 취소?)은 도메인 전문가에게 묻는다.
4. 가드를 붙인다. 가드가 거짓일 때 돌려줄 이유를 정한다.
5. 서로 독립적인 축(처리 상태·결제 상태)이 섞여 있으면 나눈다(직교 영역).
6. 저장은 조건부 UPDATE나 버전 열로 한다. 전이 이력을 같은 트랜잭션에 남긴다.
7. 전수 검사 테스트를 둔다. 상태를 추가할 때마다 돈다.

### 2. 코드 모양 (Java)

```java
public enum OrderStatus { PLACED, PAID, PREPARING, SHIPPED, DELIVERED, RETURN_REQUESTED, REFUNDED, CANCELLED }
public enum OrderEvent { PAY, PREPARE, SHIP, DELIVER, CANCEL, REQUEST_RETURN, REFUND }

record Transition(OrderStatus to, Predicate<Order> guard, String guardReason) {}

final class OrderLifecycle {
    private static final Map<OrderStatus, Map<OrderEvent, Transition>> T = new EnumMap<>(OrderStatus.class);
    static {
        for (OrderStatus s : OrderStatus.values()) T.put(s, new EnumMap<>(OrderEvent.class));
        on(PLACED, PAY, PAID);           on(PLACED, CANCEL, CANCELLED);
        on(PAID, PREPARE, PREPARING);    on(PAID, CANCEL, CANCELLED);
        T.get(PREPARING).put(SHIP, new Transition(SHIPPED, Order::addressVerified, "주소 미검증"));
        on(PREPARING, CANCEL, CANCELLED);
        on(SHIPPED, DELIVER, DELIVERED); on(DELIVERED, REQUEST_RETURN, RETURN_REQUESTED);
        on(RETURN_REQUESTED, REFUND, REFUNDED);
    }
    private static void on(OrderStatus s, OrderEvent e, OrderStatus to) { T.get(s).put(e, new Transition(to, o -> true, "")); }

    static Decision decide(Order o, OrderEvent e) {
        Transition t = T.get(o.status()).get(e);
        if (t == null) return Decision.illegal(o.status(), e);            // 표에 없음
        if (!t.guard().test(o)) return Decision.blocked(t.guardReason());  // 가드 거짓
        return Decision.go(t.to());
    }
}
```

```java
// 저장: 기대 상태를 WHERE에 (Spring JDBC)
int n = jdbc.update("""
    UPDATE orders SET status = ?, version = version + 1
     WHERE id = ? AND status = ? AND version = ?""", to.name(), id, from.name(), version);
if (n == 0) throw new ConcurrentTransitionException(id, from, to);   // 누가 먼저 바꿨다 → 다시 읽고 재판단
jdbc.update("INSERT INTO order_transition(order_id, from_status, event, to_status, at) VALUES (?,?,?,?,now())",
            id, from.name(), event.name(), to.name());
```

### 3. 진단

```sql
-- 명세에 없는 전이가 이미 저장됐나 (이력 vs 허용 전이 표)
SELECT t.from_status, t.event, t.to_status, count(*)
FROM order_transition t
LEFT JOIN allowed_transition a USING (from_status, event, to_status)
WHERE a.from_status IS NULL
GROUP BY 1, 2, 3;

-- 모순 데이터: 끝난 상태인데 뒤이은 효과가 있다
SELECT o.id FROM orders o JOIN shipments s ON s.order_id = o.id WHERE o.status IN ('REFUNDED', 'CANCELLED');
```

## 장애 시나리오와 대처

### 1. 환불된 주문이 배송됐다 — 불법 전이 (커리큘럼 ⚠)

- 현상: 고객이 환불을 받았는데 택배도 받았다.
- 보이는 형태: 위 진단 쿼리에 `REFUNDED → SHIP → SHIPPED` 이력이 나온다. 애플리케이션 오류 로그는 없다(정상 처리로 기록됨).
- 원인: 차단 목록식 검사에 REFUNDED가 빠졌다. 실험의 if문 예시는 56칸 중 19칸을 새게 했고, 정상 경로 테스트는 전부 통과했다.
- 대처: 허용 목록 전이 표로 바꾼다. 상태 × 이벤트 전수 테스트를 둔다. 이미 나간 건은 회수·재청구 절차.

### 2. 취소와 출고가 동시에 성공했다 — 동시 전이 경합 (커리큘럼 ⚠)

- 현상: 상태는 CANCELLED인데 출고 지시도 나갔다(또는 그 반대).
- 보이는 형태: 같은 주문에 서로 배타적인 효과가 둘. 이력 테이블에 같은 `from_status`에서 출발한 전이가 2개.
- 원인: 앱에서 읽고 검사한 뒤 무조건 UPDATE했다. 실험에서 겹침을 강제하자 200/200건이 둘 다 성공했다.
- 대처: 조건부 UPDATE(`AND status = ?`)나 버전 열. 진 쪽은 다시 읽고 재판단한다. 이력 테이블에 `(order_id, seq)` 유니크 제약을 두고 두 쪽이 모두 "직전 seq + 1"로 넣게 하면 DB가 두 번째를 거절한다.

### 3. 상태를 추가했더니 엉뚱한 전이가 열렸다

- 현상: ON_HOLD를 추가한 뒤, 보류 중 주문이 출고됐다.
- 원인: 기존 메서드의 차단 목록이 새 상태를 모른다. 실험에서 상태 하나 추가로 불법 통과가 19 → 21.
- 대처: 기본 거부 구조(표). 분기를 써야 하면 `default` 없는 **switch 식**(`var next = switch (status) { ... };`)으로 쓴다. Java 14+에서 switch 식은 enum 상수를 다 다루지 않으면 컴파일 오류다(JLS 15.28.1). enum 상수만 쓰는 옛 switch 문에는 이 검사가 없다(패턴·`null`을 쓰는 switch 문은 Java 21에서 망라성 검사를 받는다).

### 4. enum 순서를 바꿨더니 과거 주문 상태가 바뀌었다

- 현상: 배포 후 오래된 주문들이 엉뚱한 상태로 보인다.
- 원인: JPA 기본 `EnumType.ORDINAL`로 저장 중에 enum 중간에 상수를 끼워 넣었다. 저장된 숫자의 뜻이 밀렸다.
- 대처: `@Enumerated(EnumType.STRING)`. 이미 꼬였으면 배포 전후 매핑표로 일괄 보정(되돌릴 수 없는 데이터 작업 — 백업 후).

### 5. 상태 enum이 곱으로 불어났다

- 현상: `PAID_ON_HOLD`, `PREPARING_ON_HOLD`, `PAID_PARTIALLY_REFUNDED` ... 상태가 수십 개.
- 원인: 독립적인 두 축을 한 enum에 곱했다.
- 대처: 축을 나눠 각자 상태 기계로 둔다(statechart의 직교 영역). 축 사이 제약(예: 결제 CAPTURED 전에는 출고 불가)은 가드로 표현한다.

## 핵심 문장

- 상태 기계는 허용된 (상태, 이벤트) 칸만 적고 나머지는 거부하는 **기본 닫힘** 구조다.
- 실험의 if문 예시는 허용 9칸을 다 맞히고도 거부해야 할 47칸 중 19칸을 새게 했다 — 정상 경로 테스트로는 안 보인다.
- 전이 = (상태, 이벤트, 가드) → (다음 상태, 효과). 효과는 전이가 커밋된 뒤의 일이다.
- 표가 맞아도 검사와 쓰기 사이가 열려 있으면 동시 전이가 둘 다 성공한다 — 기대 상태를 `WHERE`에 넣는다.
- 독립적인 축은 한 enum에 곱하지 말고 나눈다(Harel statechart의 직교 영역).

## 관련 주제·근거

- 선행: [06-anemic-vs-rich-model](../06-anemic-vs-rich-model/2-summary.md) · 연습 [basic/09-order-state](../basic/09-order-state/2-summary.md)(전이 표·결과 3갈래·BFS 도달성)
- 함께: [09-domain-events](../09-domain-events/2-summary.md)(전이의 효과를 이벤트로) · [basic/10-payment](../basic/10-payment/2-summary.md) · [database/18-app-level-concurrency-patterns](../../database/18-app-level-concurrency-patterns/2-summary.md) · [database/14-isolation-levels-and-anomalies](../../database/14-isolation-levels-and-anomalies/2-summary.md) · [software-design/24-types-as-invariants](../../software-design/24-types-as-invariants/2-summary.md) · [software-design/28-taming-conditionals](../../software-design/28-taming-conditionals/2-summary.md)
- 후속: [22-decision-log-and-provenance](../22-decision-log-and-provenance/2-summary.md)(전이 이력을 결정 기록으로) · [distributed/15-saga](../../distributed/15-saga/2-summary.md)(서비스 여러 개에 걸친 상태 기계)
- 근거
  - D. Harel, "Statecharts: A visual formalism for complex systems", *Science of Computer Programming* 8(3):231–274, 1987 — 본문 PDF(초록·참고문헌 [12]) https://www.weizmann.ac.il/math/harel/sites/math.harel/files/users/user56/Statecharts.pdf
  - Jakarta Persistence `EnumType`(ORDINAL 기본, STRING) — Jakarta Persistence 3.x API 문서
  - PostgreSQL 17 문서 13.2 "Transaction Isolation"(READ COMMITTED의 UPDATE 재검사, REPEATABLE READ의 40001)
- 실험 목록
  - if문 차단 목록 vs 전이 표, 56칸·72칸 전수 비교: JDK 21 temurin, `Fsm.java`
  - 취소·출고 동시 전이 200건 × 3방식: PostgreSQL 17.11 + JDK 21 + pgjdbc 42.7.4, 일회용 컨테이너, 집필 3회 + 사실 점검 재실행 3회
  - enum switch 식 누락 상수 컴파일 오류(`the switch expression does not cover all possible input values`), 같은 누락의 switch 문은 통과: JDK 21 javac
