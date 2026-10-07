# data-engineering/01-system-of-record-and-derived-data — 원천과 파생: 어느 쪽이 정답인지 정해 두기 — 정리 (힌트)

## 해결하는 문제

같은 주문 금액이 여러 곳에 있다. 운영 DB, 캐시, 검색 인덱스, 대시보드용 집계 테이블.
값이 서로 다를 때 "어느 쪽이 맞나"를 정해 두지 않으면 판정할 방법이 없다.

```text
  주문 7의 금액 (예시)
  운영 DB         1,077
  검색 인덱스         0     ← 누가 직접 고쳤다
  목록 화면 사본   1,077
  대시보드 집계    1,577     ← 갱신 경로가 따로 돈다
  → "어느 것이 진짜냐"는 질문에 답하는 규칙이 없다
```

- 해법: 저장소마다 역할을 하나 정한다. **원천**은 하나, 나머지는 원천에서 계산한 **파생**이다.
  - *기록 시스템(system of record, 원천)*: 어떤 사실의 정본을 가진 저장소. 새 사실은 여기에 먼저 기록된다. 다른 곳과 값이 다르면 여기가 맞다고 정의한다.
  - *파생 데이터(derived data)*: 원천을 변환·집계·색인해 만든 사본. 잃어버려도 원천에서 다시 만들 수 있다. 캐시·검색 인덱스·집계 테이블·읽기 모델이 여기 든다.
    - 흔한 오해: "파생 데이터는 덜 중요하다". 검색·목록·대시보드 화면은 흔히 파생본을 읽는다. 중요도가 아니라 **다시 만들 수 있다**는 점이 다르다.

쉬운 예: 가계부와 월말 요약표.
- 가계부(영수증 목록)가 원천이다. 요약표는 가계부를 더해서 만든다.
- 요약표 숫자를 손으로 고치면, 다음 달에 가계부로 요약표를 새로 만들 때 그 수정이 사라진다.
- 고칠 일이 있으면 가계부에 "환불 영수증"을 한 줄 더 적는다.

똑같은 구조다.\
DDIA 1판 3부의 제목이 'Derived Data'다(출판사 목차로 확인). 3부 서론에 "Systems of Record and Derived Data"라는 소제목이 있고, 데이터를 저장·처리하는 시스템을 기록 시스템과 파생 데이터 시스템 두 갈래로 나눈다(출판사 3부 미리보기 첫 문단으로 확인 — 그 뒤 본문은 열지 못했다).

실무 예:
- 주문 DB가 원천, Elasticsearch 상품 검색 인덱스가 파생이다([database/48](../../database/48-search-index-sync-and-reindexing/2-summary.md)).
- 쓰기 모델이 원천, CQRS 조회 모델이 파생이다([domain-modeling/21](../../domain-modeling/21-cqrs/2-summary.md)).
- 이벤트 소싱에서는 이벤트 로그가 원천, 현재 상태 테이블이 파생이다([distributed/22](../../distributed/22-event-sourcing/2-summary.md)).

## 동작·원리

### 1. 원천 → 파생 흐름

```text
                                         ┌──► 캐시          (key → 값)
  쓰기 ──► [원천: 운영 DB] ──► 변경 로그 ──┼──► 검색 인덱스    (단어 → 문서)
                              WAL·outbox ├──► 집계 테이블    (일·지역 → 합계)
                              ·이벤트     └──► 읽기 모델      (화면 모양)

  화살표는 한 방향이다. 파생본에서 원천으로 거꾸로 쓰지 않는다.
```

- 파생본마다 "원천의 어떤 변화를, 어떤 함수로 반영하나"가 정해져 있다. 그 함수가 바뀌면 파생본을 다시 만든다.
- 원천에서 파생으로 변화를 옮기는 길은 여러 가지다.
  - 같은 트랜잭션에 쓰는 outbox, DB 로그를 읽는 CDC([distributed/16](../../distributed/16-outbox-and-dual-write/2-summary.md), 이 영역 [05](../05-change-data-capture/2-summary.md)).
  - 주기적 배치 재계산(이 영역 [08](../08-idempotent-pipelines-and-backfill/2-summary.md)).
- DDIA 1판 11장 "Keeping Systems in Sync"·"Change Data Capture"와 12장 "Combining Specialized Tools by Deriving Data"가 이 흐름을 다룬다(절 제목은 출판사 목차로 확인).

### 2. 파생 = 원천 로그의 폴드

```text
  원천 로그 (append-only)                       파생 상태
  seq  order  kind         amount
   1     7    placed           0      ──┐
   2     7    item_added     359        │  fold(apply, 빈 상태, 로그)
   3     7    item_added     359        ├────────────────────────────►  order 7: total=1077, placed
   4     7    item_added     359      ──┘
   5     7    refunded     -1077      ──────────────────────────────►  order 7: total=0, refunded
```

- *폴드(fold)*: 목록의 원소를 하나씩 넣으며 누적값을 갱신하는 연산. `state = apply(state, event)`를 처음부터 끝까지 반복한다.
- 같은 로그와 같은 `apply`면 결과가 같다. 그래서 파생본을 버리고 다시 만들 수 있다.
  - 조건: `apply`가 결정적이어야 한다. 현재 시각·난수·외부 API 값을 읽으면 다시 만들 때 결과가 달라진다([distributed/22](../../distributed/22-event-sourcing/2-summary.md) §4 재생과 외부 세계 — 핵심 문장 "재생은 순수해야 한다").
- 수정은 원천에 **사건을 하나 더 붙여서** 한다. 파생본을 직접 고치면 다음 재구축에서 사라진다.

### 실험: 재구축은 같은 답, 파생본 직접 수정은 사라진다

환경: 이 호스트(i7-13700HX), `postgres:17`(PostgreSQL 17.11) 일회용 컨테이너 `--cpus=2 --network none`, psql. 주문 1,000건, 이벤트 4,100건(placed 1,000 + item_added 3,000 + cancelled 100). 파생 테이블 `order_view`는 `TRUNCATE` 후 `INSERT … SELECT … GROUP BY order_id`로 다시 만든다.

```sql
CREATE FUNCTION rebuild_view() RETURNS void LANGUAGE sql AS $$
  TRUNCATE order_view;
  INSERT INTO order_view
  SELECT order_id, sum(amount),
         CASE WHEN bool_or(kind='cancelled') THEN 'cancelled' ELSE 'placed' END
  FROM order_event GROUP BY order_id;
$$;
```

```text
  A. 첫 구축           orders 1000  revenue 1644900  cancelled 100  digest d95f1a566dc2f5d20484c758d8d9903a
  B. 버리고 재구축      orders 1000  revenue 1644900  cancelled 100  digest d95f1a566dc2f5d20484c758d8d9903a
  C. view만 수정        order 7 → total 0, refunded
     재구축 뒤          order 7 → total 1077, placed          ← 수정이 사라졌다
  D. 원천에 refunded 이벤트(-1077) 추가 후 재구축 2번
                       order 7 → total 0, refunded           ← 남는다
```

- D에서는 위 `rebuild_view()`의 `CASE` 맨 앞에 `WHEN bool_or(kind='refunded') THEN 'refunded'`를 더해 다시 정의했다. 위 정의 그대로면 상태는 `cancelled`·`placed` 둘뿐이다.
- A·B의 `digest`(전 행을 이어 붙인 md5)가 같다. 같은 원천에서 같은 파생본이 나왔다.
- C는 커리큘럼 ⚠의 "검색 인덱스를 직접 수정한다 → 재색인하는 순간 수정분이 사라진다"와 같은 모양이다.
- 같은 폴드를 Java 21(`eclipse-temurin:21-jdk`, JDK만)로도 돌렸다. `revenue=1644900`, `rebuild1.equals(rebuild2)=true`, 직접 수정한 order 7은 재구축 뒤 `total=1077, status=placed`로 돌아왔다.

## 쓰이는 자료구조·알고리즘

- **폴드(fold, reduce)** — 파생 상태 = 원천 로그를 순서대로 접은 값. 이벤트 소싱 재생([distributed/22](../../distributed/22-event-sourcing/2-summary.md)), CQRS 프로젝션([domain-modeling/21](../../domain-modeling/21-cqrs/2-summary.md))이 같은 연산이다.
- **append-only 로그** — 원천을 지우지 않고 붙이기만 하면 "언제든 처음부터 다시 접기"가 가능하다. 로그와 오프셋은 [distributed/17](../../distributed/17-queues-logs-and-delivery-semantics/2-summary.md).
- **해시 집계** — SQL 재구축의 `GROUP BY order_id`는 플래너가 `HashAggregate`를 고르면 키별 해시 버킷에 누적한다. 정렬 뒤 묶는 `GroupAggregate`를 고를 수도 있다(어느 쪽인지는 `EXPLAIN`으로 본다 — 이 실험에서는 확인하지 않았다)([database/41](../../database/41-sorting-and-aggregation/2-summary.md), [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)).
- **집합 차(EXCEPT)** — "원천에서 다시 접은 값"과 "파생본"의 차이를 구해 어긋난 행을 찾는다.
  - `A EXCEPT B`는 A에만 있는 행만 보인다. 파생본에만 남은 행을 찾으려면 반대 방향도 돌린다.
  - `EXCEPT`는 중복 행을 없앤다. 중복 자체가 어긋남이면 `EXCEPT ALL`을 쓴다(PostgreSQL 17 문서 7.4).

## 적용 — 풀어나가는 법

### 1. 저장소마다 역할표를 만든다

| 데이터 | 원천 | 파생본 | 갱신 경로 | 재구축 방법 |
|---|---|---|---|---|
| 주문 금액 | 주문 DB `order_event` | `order_view`, 목록 사본, 검색 인덱스 | outbox → 프로젝터 | `rebuild_view()` |
| 상품 검색 | 상품 DB | 검색 인덱스 | CDC | 새 인덱스 + 별칭 교체(database/48) |

- 칸이 비면 그 파생본은 "다시 만들 수 없는 두 번째 원천"이 된 상태다.
- 파생본을 고쳐야 하는 운영 요청이 오면 원천에 보정 사건(보정 행)을 기록하고 다시 계산한다.

### 2. 비정규화는 "파생본을 하나 더 두는 결정"이다

- 정규화는 한 사실을 한 곳에 둔다([database/03](../../database/03-normalization/2-summary.md)). 비정규화는 그 사실의 사본을 하나 더 만든다.
- 사본을 만들 때 같이 정한다.
  - 누가 원천인가.
  - 원천이 바뀌면 사본은 어떤 경로로, 얼마 뒤에 바뀌나.
  - 어긋남을 무엇으로 발견하나(대조 쿼리).
- 갱신 경로를 하나 빠뜨리면 화면마다 값이 다르다. 아래 실험이 그 모양이다.

### 실험: 목록 사본의 갱신 경로 누락

같은 환경. `order_list`(목록 화면용 사본)를 만든 뒤, 주문 1~50에 500원짜리 상품 추가 이벤트를 넣었다. 상세(`order_view`)만 재구축하고 목록 사본 갱신은 빠뜨렸다.

```sql
SELECT count(*) AS mismatched, sum(v.total - l.total) AS diff_sum
FROM order_view v JOIN order_list l USING (order_id)
WHERE v.total IS DISTINCT FROM l.total;
--  mismatched | diff_sum
--          50 |    25000

-- 원천에서 다시 접은 값과 목록 사본의 차이
SELECT order_id, sum(amount)::int FROM order_event GROUP BY order_id
EXCEPT
SELECT order_id, total FROM order_list;
--  1 | 911,  2 | 1022,  3 | 1133, ...   (50행)
```

- 에러는 없다. 목록 화면과 상세 화면의 숫자가 다를 뿐이다(커리큘럼 ⚠).
- 대조 기준은 원천이다. 파생본끼리 비교하면 어느 쪽이 틀렸는지 모른다.

### 3. 재구축 코드의 모양 (Java 21)

```java
record Event(long seq, int orderId, String kind, int amount) {}
record OrderView(int total, String status) {}

static Map<Integer, OrderView> rebuild(List<Event> log) {
    Map<Integer, OrderView> view = new TreeMap<>();
    for (Event e : log) {
        view.merge(e.orderId(), apply(new OrderView(0, "placed"), e),
                   (old, ignored) -> apply(old, e));
    }
    return view;
}

static OrderView apply(OrderView s, Event e) {   // 결정적이어야 한다: 시각·난수·외부 호출 금지
    return switch (e.kind()) {
        case "item_added" -> new OrderView(s.total() + e.amount(), s.status());
        case "cancelled"  -> new OrderView(s.total(), "cancelled");
        case "refunded"   -> new OrderView(s.total() + e.amount(), "refunded");
        default           -> s;
    };
}
```

- 운영에서는 재구축을 "새 테이블에 만들고 → 대조하고 → 이름(별칭)을 바꾼다" 순서로 한다. 읽는 쪽이 반쯤 빈 테이블을 보지 않게 한다(database/48의 별칭 교체와 같은 생각).

## 장애 시나리오와 대처

### 1. 두 저장소가 서로 원천이라고 주장한다 (⚠ 커리큘럼)

- **현상**: CRM과 주문 DB의 고객 등급이 다르다. 두 팀 모두 자기 쪽이 맞다고 한다.
- **보이는 형태**: 대조 쿼리에서 같은 고객 키의 값이 다르다. 양쪽 다 "직접 수정" 화면이 있다. 양방향 동기화 잡이 서로의 값을 덮어쓴다. 어느 값이 남는지는 그 동기화의 충돌 규칙(나중 쓰기 우선·우선순위 등)에 달려 있어, 값이 왔다 갔다 할 수 있다.
- **원인**: 같은 사실에 쓰기 경로가 둘이다. 원천이 정해져 있지 않으니 판정 규칙이 없다.
- **대처**: 사실(컬럼) 단위로 원천을 하나 정한다. 다른 쪽의 쓰기 화면은 원천으로 요청을 보내게 바꾼다. 역할표(적용 §1)를 문서로 남긴다.

### 2. 검색 인덱스를 직접 고쳤더니 재색인 뒤 되돌아왔다 (⚠ 커리큘럼)

- **현상**: 운영자가 잘못 노출된 상품을 인덱스에서 직접 숨겼다. 다음 주 전체 재색인 뒤 다시 보인다.
- **보이는 형태**: 원천 DB에는 상품이 여전히 `visible=true`다. 재색인 잡은 성공했다.
- **원인**: 파생본만 고쳤다. 재구축은 원천을 다시 접으므로 수정이 사라진다(실험 C).
- **대처**: 수정은 원천에 기록한다(`visible=false` 또는 보정 이벤트). 파생본 직접 수정 권한을 막는다.

### 3. 비정규화 사본의 갱신 경로 누락 → 목록과 상세 값이 다르다 (⚠ 커리큘럼)

- **현상**: 목록 화면 금액과 상세 화면 금액이 다르다.
- **보이는 형태**: 적용 §2의 실험처럼 `mismatched 50, diff_sum 25000`. 새로 추가된 기능(상품 추가)의 경로에서만 어긋난다.
- **원인**: 사본을 만드는 갱신 경로가 여럿인데, 새 쓰기 경로에 사본 갱신을 넣지 않았다.
- **대처**: 사본 갱신을 쓰기 경로마다 넣는 대신, 원천 변경 로그 하나에서 사본을 만든다(outbox·CDC). 원천과 사본의 정기 대조(`EXCEPT`, 행 수·합계)를 잡으로 돌린다.

### 4. 파생본을 다시 만들 수 없다

- **현상**: 프로젝터 버그를 고쳤는데 조회 모델을 재구축할 수 없다.
- **보이는 형태**: 원천 이벤트가 보존 기간(예시: 7일) 뒤 지워졌다. 또는 조회 모델이 과거 변화(이력·기간별 합계)를 필요로 하는데 원천에는 "현재 상태"만 있다. 현재 상태만으로 계산되는 파생본(검색 인덱스 등)은 현재 테이블을 다시 읽어 재구축할 수 있다.
- **원인**: 파생본이 사실상 유일한 기록이 되었다. 원천 보존 기간이 재구축 요구보다 짧다.
- **대처**: 재구축에 필요한 원천 기간을 정해 보존한다. 지울 수밖에 없다면 파생본을 "원천"으로 승격하고 그 사실을 역할표에 적는다. 보존과 재처리는 이 영역 [07](../07-batch-stream-architectures/2-summary.md)·[12](../12-data-retention-and-erasure/2-summary.md).

## 핵심 문장

- 원천(기록 시스템)은 사실의 정본이고, 파생 데이터는 원천에서 계산한 사본이다. 값이 다르면 원천이 맞다고 정의해 둔다.
- 파생은 원천 로그의 폴드다. 같은 로그·같은 결정적 함수면 같은 결과가 나와서, 버리고 다시 만들 수 있다(실험: digest 동일).
- 파생본을 직접 고치면 다음 재구축에서 사라진다. 수정은 원천에 보정 사건으로 기록한다.
- 비정규화는 파생본을 하나 더 두는 결정이다. 원천·갱신 경로·대조 방법을 같이 정해야 화면마다 값이 달라지지 않는다.
- 어긋남은 에러로 보이지 않는다. 원천을 기준으로 한 정기 대조(`EXCEPT`·행 수·합계)로 찾는다.

## 관련 주제·근거

- 선행
  - [database/03-normalization](../../database/03-normalization/2-summary.md) — 한 사실은 한 곳에, 반정규화의 동기화
  - [distributed/17-queues-logs-and-delivery-semantics](../../distributed/17-queues-logs-and-delivery-semantics/2-summary.md) — 로그·오프셋·재생
- 연결
  - [domain-modeling/21-cqrs](../../domain-modeling/21-cqrs/2-summary.md) — 조회 모델 = 폴드, 재구축 + `EXCEPT` 대조
  - [database/30-caching-with-databases](../../database/30-caching-with-databases/2-summary.md) — 캐시도 파생본, 삭제로 무효화
  - [database/48-search-index-sync-and-reindexing](../../database/48-search-index-sync-and-reindexing/2-summary.md) — 검색 인덱스 동기화와 별칭 교체
  - [distributed/16-outbox-and-dual-write](../../distributed/16-outbox-and-dual-write/2-summary.md) · [distributed/22-event-sourcing](../../distributed/22-event-sourcing/2-summary.md)
- 후속
  - [02-oltp-olap-and-warehouse](../02-oltp-olap-and-warehouse/2-summary.md) — 분석 저장소도 파생본이다
  - [05-change-data-capture](../05-change-data-capture/2-summary.md) · [08-idempotent-pipelines-and-backfill](../08-idempotent-pipelines-and-backfill/2-summary.md) · [12-data-retention-and-erasure](../12-data-retention-and-erasure/2-summary.md)
- 문헌
  - Kleppmann, *Designing Data-Intensive Applications* 1판(O'Reilly, 2017) — 3부 "Derived Data" 서론, 11장 "Keeping Systems in Sync"·"Change Data Capture"·"Event Sourcing"·"State, Streams, and Immutability", 12장 "Combining Specialized Tools by Deriving Data"·"Unbundling Databases"·"Observing Derived State". 절 제목은 출판사 목차(Internet Archive 2025-01-05 사본 <https://web.archive.org/web/20250105115631/https://www.oreilly.com/library/view/designing-data-intensive-applications/9781491903063/>)로 확인. 3부 서론의 소제목 "Systems of Record and Derived Data"는 목차에 없고, 출판사 3부 미리보기(Internet Archive 2025-03-04 사본 <https://web.archive.org/web/20250304091224/https://www.oreilly.com/library/view/designing-data-intensive-applications/9781491903063/part03.html>)의 첫 문단으로 확인("A system of record, also known as source of truth, holds the authoritative version …").
- 실험(이 호스트 i7-13700HX, `--cpus=2`, `--network none`)
  - PostgreSQL 17.11(`postgres:17`): 주문 이벤트 4,100건 → `order_view` 재구축 2회 digest 동일, 파생본 직접 수정이 재구축 뒤 사라짐, 원천 보정 이벤트는 유지, 목록 사본 갱신 누락 50행·차이 25,000.
  - Java 21.0.12(`eclipse-temurin:21-jdk`, JDK만): 같은 폴드, `rebuild1.equals(rebuild2)=true`, 직접 수정 소실 재현.
