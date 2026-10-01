# database/11-join-algorithms — 조인 알고리즘: 중첩 루프·해시 조인·정렬 병합 조인 — 정리 (힌트)

## 해결하는 문제

SQL의 `JOIN`은 "무엇을 합칠지"만 말한다. **어떻게 합칠지**는 DB가 고른다.\
방법은 크게 셋이고, 같은 쿼리라도 방법에 따라 수 밀리초와 수 분이 갈린다.

쉬운 예: 반 명단(30명)과 전교 성적표(1000장)를 학생 번호로 맞춘다.
- 방법 1: 명단의 한 명마다 성적표 1000장을 처음부터 넘긴다. 30 × 1000번 본다.
- 방법 2: 성적표가 번호순 색인 카드로 정리돼 있으면, 한 명마다 카드로 바로 찾는다. 30번 찾는다.
- 방법 3: 명단 30명을 번호별 칸이 있는 상자에 넣는다. 성적표를 한 번 넘기며 상자 칸을 본다. 1000번 본다.
- 방법 4: 둘 다 번호순으로 정렬해 두 줄을 나란히 내려가며 맞춘다.

똑같은 구조다.\
방법 1·2는 **중첩 루프 조인**, 방법 3은 **해시 조인**, 방법 4는 **정렬 병합 조인**이다. 어느 것이 빠른지는 **양쪽 크기**, **인덱스 유무**, **메모리**, **정렬돼 있는가**에 달렸다.

실무 예:
- 통계가 틀려 옵티마이저가 "몇 행뿐"이라고 믿고 중첩 루프를 골랐다. 실제로는 수십만 행이라 야간 리포트가 수 분 걸린다.
- 해시 조인의 해시 테이블이 `work_mem`을 넘어 디스크로 나뉘어(`Batches: 32`) 느려진다.

## 동작·원리

### 1. 비용을 세는 기호 (CMU 15-445 L12)

```text
  R(바깥, outer): M 페이지, m 행        S(안쪽, inner): N 페이지, n 행
  B = 조인에 쓸 수 있는 버퍼 페이지 수
  비용 = 디스크 I/O 페이지 수 (결과 출력 비용은 빼고 센다)
```

- *바깥 테이블(outer)*: 루프의 바깥에서 한 번 훑는 쪽. *안쪽 테이블(inner)*: 바깥 행마다 찾아보는 쪽.
- 아래 비용식은 CMU 강의 노트의 디스크 I/O 모델이다. 실제 DB의 비용 모델은 CPU·캐시까지 넣어 다르다.

### 2. 중첩 루프 조인 (Nested Loop Join)

```text
  for r in R:                      단순:      M + m × N
      for s in S:                  블록 단위:  M + ⌈M / (B−2)⌉ × N
          if r.k == s.k: emit      인덱스:    M + m × C     (C = 인덱스 탐색 1회 비용)

  R ──행 1개──> S 전체를 훑는다        R ──행 1개──> S의 인덱스로 바로 찾는다
      (안쪽에 인덱스 없음)                 (안쪽에 인덱스 있음)
```

- 조건이 등호가 아니어도(`<`, `LIKE`) 쓸 수 있는 유일한 기본형이다.
- **안쪽에 인덱스가 있고 바깥이 작을 때** 가장 빠르다. 바깥 행 수만큼 인덱스 탐색을 한다.
- 바깥이 크고 안쪽에 인덱스가 없으면 최악이다. 바깥 행 수 × 안쪽 전체다.
- 로컬 재현(예시, PostgreSQL 17.11): 고객 5명의 주문 조회는 `Nested Loop` → 안쪽 `Bitmap Index Scan on orders_cust (loops=5)`, 0.09 ms.
- PostgreSQL 14부터 **Memoize** 노드가 안쪽 결과를 키별로 캐시한다. 같은 키가 반복되면 안쪽 탐색을 건너뛴다. 로컬 재현에서 `Hits: 110230 Misses: 49055`가 보였다.

### 3. 해시 조인 (Hash Join)

```text
  1) 빌드: 작은 쪽을 읽어 조인 키로 해시 테이블을 만든다
        customers(5만 행) ──h(id)──> [버킷0][버킷1] ... [버킷65535]

  2) 프로브: 큰 쪽을 한 번 읽으며 같은 해시 버킷을 찾아 키를 비교한다
        orders(30만 행) ──h(customer_id)──> 버킷 → 일치하면 출력

  메모리를 넘으면 (Grace / 분할 해시 조인):
        두 테이블을 같은 해시 함수로 k개 파티션에 나눠 디스크에 쓴다
        파티션 i끼리만 다시 읽어 조인한다          비용 ≈ 3 × (M + N)
```

- 해시로 짝을 좁히려면 **등호 조건**이 필요하다(CMU L12). 해시는 같은 값만 같은 버킷에 보내기 때문이다. (MySQL 8.4의 예외는 아래)
- 빌드 쪽은 보통 작은 쪽이다. 해시 테이블이 메모리에 들어가야 빠르다.
- 로컬 재현(예시, PostgreSQL 17.11, 주문 30만 × 고객 5만)

```text
  work_mem 4MB(기본)   Hash  Buckets: 65536  Batches: 1   Memory Usage: 2466kB
  work_mem 64kB        Hash  Buckets: 4096   Batches: 32  Memory Usage: 95kB
                       → 해시 테이블을 32개 배치로 나눠 임시 파일을 오간다
```

- PostgreSQL 17의 해시 테이블 한도는 `work_mem × hash_mem_multiplier`다. 기본값은 `work_mem` 4MB, `hash_mem_multiplier` 2.0이다(PostgreSQL 17 19.4). 이 한도는 **연산 하나당**이라서, 한 쿼리가 여러 해시·정렬을 동시에 쓰면 몇 배가 된다.
- MySQL 8.4는 등호 조인에 쓸 인덱스가 없으면 해시 조인을 쓴다. 메모리 한도는 `join_buffer_size`(로컬 확인 262144 = 256KB)이고, 넘으면 디스크 파일을 쓴다. 파일 수가 `open_files_limit`을 넘으면 조인이 실패할 수 있다(MySQL 8.4 10.2.1.4).
- MySQL 8.4는 등호 조건이 없는 조인에도 `Inner hash join (no condition)`을 쓴다. 로컬 재현에서 `ON i.customer_id < c.region` 조인이 그렇게 나왔다. 등호가 아닌 조건은 조인 뒤 필터로 적용된다(10.2.1.4).

### 4. 정렬 병합 조인 (Sort-Merge Join)

```text
  R 정렬: 1 1 3 5 5 7          S 정렬: 1 3 3 4 5 8
          ^                            ^
  두 커서를 작은 쪽부터 전진시키며 같은 키를 만나면 출력한다

  비용 = (R 정렬) + (S 정렬) + (M + N)      정렬이 이미 돼 있으면 M + N
  최악(모든 키가 같은 값) = M × N
```

- 양쪽이 조인 키로 **이미 정렬돼 있을 때**(인덱스 순서, 앞 단계의 정렬) 강하다. 결과도 키 순서로 나오므로 `ORDER BY`가 같으면 정렬을 한 번 줄인다(CMU L12).
- 정렬이 필요하면 외부 정렬 비용을 낸다. 외부 정렬은 41번에서 다룬다.
- 로컬 재현(예시, PostgreSQL 17.11): `ORDER BY c.id` 전체 조인은 `Merge Join` ← 양쪽 `Index Scan`(customers_pkey, orders_cust)으로 나왔다.
- MySQL 8.4는 조인을 중첩 루프 계열(10.2.1.7)과 해시 조인(10.2.1.4)으로 실행한다. 정렬 병합 조인 연산자는 없다.

### 5. 한눈에 비교

```text
                    중첩 루프(인덱스)      해시 조인               정렬 병합 조인
  조건              아무 조건              등호만                   등호만(PostgreSQL 기준)
  잘 맞는 경우       바깥 작음 + 안쪽 인덱스  둘 다 크고 인덱스 없음      둘 다 이미 정렬
  메모리            거의 없음              빌드 쪽 해시 테이블         정렬 버퍼
  첫 행까지 시간     짧다                   빌드가 끝나야 나온다         정렬이 필요하면 정렬 뒤(이미 정렬된 입력이면 짧다)
  망가지는 경우       바깥 행 수 추정이 틀림   메모리 초과 → 배치 분할     키 쏠림(같은 값 대량)
```

- CMU L12의 예(M=1000, N=500, B=100, I/O 0.1 ms): 단순 중첩 루프 1.4시간, 블록 중첩 루프 50초, 정렬 병합 0.75초, 해시 조인 0.45초.
  - 표의 블록 중첩 루프 50초는 바깥 블록을 한 페이지씩 쓰는 M + M × N 식이다. B − 2개 버퍼를 바깥에 쓰는 식으로는 6,500 I/O(약 0.65초)다.
- PostgreSQL에서 병합 조인·해시 조인은 **등호 연산자**에만 쓰인다. 연산자 정의의 `MERGES`·`HASHES` 절은 "실제로는 어떤 타입의 등호를 나타내야 한다"고 문서가 적는다(PostgreSQL 17 36.15).

## 쓰이는 자료구조·알고리즘

- **해시 테이블** — 해시 조인의 빌드 쪽. 충돌은 키를 다시 비교해 거른다. [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md), 디스크 기반 해시는 [39-hash-indexes](../39-hash-indexes/2-summary.md)
- **분할(partitioning)** — Grace 해시 조인은 같은 해시 함수로 양쪽을 나눠 "같은 키는 같은 파티션"을 보장한다. 파티션이 여전히 크면 다른 해시 함수로 재귀 분할한다(CMU L12).
- **블룸 필터** — 빌드할 때 함께 만들어 프로브 쪽 행을 미리 거르는 최적화(CMU L12, sideways information passing). [data-structure/11-bloom-filter](../../data-structure/11-bloom-filter/2-summary.md)
- **병합** — 정렬된 두 스트림을 커서로 전진시키는 병합 정렬의 병합 단계. [algorithm/02-merge-sort](../../algorithm/02-merge-sort/2-summary.md)
- **B+Tree 탐색** — 인덱스 중첩 루프의 안쪽 탐색. [data-structure/15-b-tree](../../data-structure/15-b-tree/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 계획에서 조인 노드와 "추정 vs 실제"를 먼저 본다

```sql
-- PostgreSQL 17
EXPLAIN (ANALYZE, BUFFERS)
SELECT c.region, sum(o.amount)
FROM orders o JOIN customers c ON c.id = o.customer_id
GROUP BY c.region;
-- 볼 곳: Hash Join / Nested Loop / Merge Join, rows=(추정) vs actual rows,
--        loops=, Hash의 Batches, Memoize의 Hits/Misses

-- MySQL 8.4
EXPLAIN ANALYZE SELECT ... ;       -- Nested loop inner join / Inner hash join
```

- 중첩 루프의 안쪽 노드는 `loops=`로 반복 횟수를 보여 준다. PostgreSQL에서 안쪽 `actual rows`는 **한 번당 평균**이다. 총량은 `rows × loops`다(PostgreSQL 17 14.1).
- 조인이 느리면 순서대로 본다.
  1. 바깥 쪽 추정 행 수가 실제와 크게 다른가(카디널리티 오류)
  2. 안쪽 조인 키에 인덱스가 있는가
  3. 해시의 `Batches`가 1보다 큰가(메모리 부족)
  4. 정렬 노드가 `external merge`인가(41번)

### 2. 추정 오류를 고친다

```text
  customers: region = id % 100, grade = id % 100  → 두 컬럼이 완전히 같이 움직인다

  WHERE region = 1 AND grade = 1
    추정 rows=5   (0.01 × 0.01 × 50000, 독립 가정)
    실제 rows=500

  CREATE STATISTICS cust_rg (dependencies) ON region, grade FROM customers; ANALYZE customers;
    추정 rows=513                                   (로컬 재현, 예시, PostgreSQL 17.11)
```

- PostgreSQL 플래너는 기본적으로 컬럼 조건들을 **독립**으로 보고 선택도를 곱한다. 상관된 컬럼이면 크게 과소 추정한다.
- 확장 통계(`CREATE STATISTICS`)로 컬럼 간 의존성을 알려 주면 추정이 맞아진다. 통계 자체는 12번에서 다룬다.
- 과소 추정된 쪽이 중첩 루프의 바깥이 되면 안쪽 반복이 폭증한다. 아래 장애 1이 그 모양이다.

### 3. 앱 코드 쪽

```java
// N+1은 "앱이 직접 하는 중첩 루프 조인"이다 — 바깥 루프가 앱, 안쪽 탐색이 쿼리 1회
for (Order o : orders) {                       // 바깥: 1000행
    Customer c = customerRepo.findById(o.getCustomerId()).orElseThrow(); // 안쪽: 최대 쿼리 1000번(같은 고객 ID는 영속성 컨텍스트가 재사용)
}
// DB에 조인을 맡기면 DB가 해시·병합 조인을 고를 수 있다
// select o, c from Order o join fetch o.customer c where ...
```

- 앱에서 루프를 돌면 DB는 조인 알고리즘을 고를 기회가 없다. DB에 가는 반복마다 네트워크 왕복이다. N+1은 23번에서 다룬다.

## 장애 시나리오와 대처

### 1. 추정 오류로 대형 테이블에 중첩 루프 → 쿼리 수 분

- **현상**: 평소 수십 ms이던 리포트 쿼리가 데이터가 늘거나 배치 직후 수 분 걸린다.
- **보이는 형태**: `EXPLAIN ANALYZE`에 `Nested Loop`, 바깥 노드의 `rows=5`(추정) vs `actual rows=500` 같은 큰 차이, 안쪽 노드 `loops=` 수만~수십만. 안쪽에 인덱스가 없으면 `Rows Removed by Join Filter`가 억 단위로 찍힌다.
- **로컬 재현(예시, PostgreSQL 17.11)**: 위 추정 오류 쿼리를 해시·병합 조인을 끄고 중첩 루프로 강제하자 `Rows Removed by Join Filter: 49749500`, 3292 ms였다. 같은 쿼리를 해시 조인으로 돌리면 15.6 ms였다. (이 재현에서 플래너는 원래 해시 조인을 골랐다. 강제는 비용을 보이기 위한 것이다.)
- **원인**: 상관 컬럼·오래된 통계·함수 조건 때문에 행 수를 과소 추정했다. 옵티마이저는 "바깥이 몇 행뿐이니 중첩 루프가 싸다"고 판단한다.
- **대처**
  - `ANALYZE`로 통계를 새로 고친다. 상관 컬럼에는 확장 통계를 만든다.
  - 안쪽 조인 키에 인덱스를 둔다. 추정이 틀려도 반복당 비용이 작아진다.
  - 긴급하면 세션 단위로 `SET enable_nestloop = off`를 걸고 해당 쿼리만 돌린다. 전역으로 끄지 않는다.

### 2. 해시 조인이 메모리를 넘음 → 배치 분할·디스크 I/O

- **현상**: 대량 조인이 데이터가 늘자 급격히 느려진다. 디스크 쓰기가 튄다.
- **보이는 형태**: PostgreSQL `Hash … Batches: 32`(1보다 큼). `log_temp_files`를 켜 두면 서버 로그에 임시 파일이 찍힌다. MySQL은 조인 중 임시 파일을 쓰고, 파일이 너무 많으면 `open_files_limit` 때문에 실패할 수 있다(10.2.1.4).
- **원인**: 빌드 쪽이 `work_mem × hash_mem_multiplier`(MySQL은 `join_buffer_size`)를 넘었다. 또는 빌드 쪽이 작다고 잘못 추정해 큰 쪽으로 해시 테이블을 만들었다.
- **대처**
  - 조인 전에 필터·집계로 빌드 쪽을 줄인다.
  - 세션 단위로 `SET work_mem`을 올린다. 동시 세션 수 × 연산 수만큼 곱해진다는 점을 계산한다.
  - PostgreSQL은 `hash_mem_multiplier`만 올려 해시 연산만 더 쓰게 할 수 있다(19.4).

### 3. 조인 키 타입·collation 불일치 → 인덱스 중첩 루프가 불가능

- **현상**: 조인 키에 인덱스가 있는데 쓰이지 않는다. 풀스캔 + 해시 조인이거나, 큰 쪽을 통째로 훑는다.
- **보이는 형태** (로컬 재현, 예시)
  - PostgreSQL 17.11: `int = varchar` 비교는 `ERROR: operator does not exist: integer = character varying`로 거부된다. 그래서 개발자가 캐스트를 붙인다. 인덱스 쪽을 캐스트하면(`c.id::text = e.code`) `Hash Cond: ((c.id)::text = (e.code)::text)` + 양쪽 `Seq Scan`이다. 반대쪽을 캐스트하면(`c.id = e.code::integer`) `Index Only Scan using customers_pkey`를 쓰는 중첩 루프가 된다.
  - MySQL 8.4.10: `varchar` 컬럼 `e.code`와 `int` 컬럼을 비교하자 조건이 `cast(e.code as double) = cast(c.id as double)`로 바뀌었다. `code` 인덱스로는 탐색하지 못하고 인덱스 전체를 훑었다(`Covering index scan on e using code`).
- **원인**: 조인 키의 타입이 다르다. 변환이 인덱스 쪽 컬럼에 걸리면 그 인덱스 순서를 쓸 수 없다(09번의 "컬럼에 함수 적용"과 같은 이유).
- **대처**: 조인 키의 타입·collation을 스키마에서 일치시킨다. PostgreSQL은 타입이 호환되지 않는 FK를 거부한다(로컬 재현: `foreign key constraint … cannot be implemented`, `incompatible types: character varying and integer`). FK를 걸어 두면 불일치를 설계 단계에서 잡는다.

### 4. 조인 팬아웃 → 결과 폭증

- **현상**: 조인 결과 행 수가 기대보다 훨씬 많고, 합계가 부풀려진다.
- **보이는 형태**: 조인 노드의 `actual rows`가 양쪽 입력보다 크다. `SUM`이 실제의 몇 배다.
- **원인**: 알고리즘 문제가 아니라 1:N:N 관계를 한 번에 조인했다. 어떤 알고리즘이든 결과는 같다. 정렬 병합 조인은 같은 키가 많으면 비용도 M × N 쪽으로 커진다(CMU L12).
- **대처**: N쪽을 먼저 집계한 뒤 조인한다. 팬아웃은 04번과 [sql/25](../../../languages/sql/syntax/25-join-fan-out/2-summary.md)에서 다룬다.

## 핵심 문장

- 조인 알고리즘은 셋이다. 중첩 루프(인덱스), 해시 조인, 정렬 병합 조인. 어느 것이 빠른지는 크기·인덱스·메모리·정렬 여부로 정해진다.
- 인덱스 중첩 루프는 바깥이 작고 안쪽에 인덱스가 있을 때 최고다. 바깥 행 수를 과소 추정하면 최악이 된다.
- 해시 조인은 등호 조건이 있어야 해시로 짝을 좁힌다(MySQL 8.4의 `no condition` 해시 조인은 예외로, 비등호 조건을 뒤에서 필터로 거른다). 작은 쪽으로 해시 테이블을 만들고 큰 쪽을 한 번 훑는다. 메모리를 넘으면 파티션으로 나눠 디스크를 오간다.
- 정렬 병합 조인은 양쪽이 이미 정렬돼 있을 때 강하다. MySQL 8.4에는 없고, PostgreSQL은 쓴다.
- 조인 성능 문제의 대부분은 알고리즘보다 **추정 행 수 오류**에서 시작한다. `EXPLAIN ANALYZE`의 추정 vs 실제부터 본다.

## 관련 주제·근거

- 선행: [41-sorting-and-aggregation](../41-sorting-and-aggregation/2-summary.md)
- 후속·연결
  - [12-query-optimizer-and-explain](../12-query-optimizer-and-explain/2-summary.md)(조인 순서·카디널리티 추정) · [04-sql-joins-and-aggregation](../04-sql-joins-and-aggregation/2-summary.md)(논리 조인과 팬아웃) · [23-orm-and-n-plus-one](../23-orm-and-n-plus-one/2-summary.md)
  - database [54-query-execution-models](../54-query-execution-models/2-summary.md)(반복자 모델)
  - [09-index-design](../09-index-design/2-summary.md) — 안쪽 조인 키 인덱스
  - SQL 문법 노트: [sql/59 스캔·조인·정렬 연산자](../../../languages/sql/syntax/59-scan-join-sort-operators/2-summary.md) · [sql/25 조인 팬아웃](../../../languages/sql/syntax/25-join-fan-out/2-summary.md)
- 강의·문서
  - CMU 15-445 Fall 2024 L12 "Join Algorithms"(비용식 M·N·B, 블록 중첩 루프, 인덱스 중첩 루프, 정렬 병합, 기본·Grace·하이브리드 해시 조인, 비교표) <https://15445.courses.cs.cmu.edu/fall2024/notes/12-joins.pdf>
  - PostgreSQL 17: 36.15 Operator Optimization Information(`MERGES`·`HASHES`는 등호 연산자) · 50.5 Planner/Optimizer(세 조인 방식) · 14.1 Using EXPLAIN(`loops`와 평균 행 수, Merge Join) · 19.4 Resource Consumption(`work_mem` 4MB, `hash_mem_multiplier` 2.0) · 19.7 Query Planning(`enable_nestloop` 등) <https://www.postgresql.org/docs/17/planner-optimizer.html> · <https://www.postgresql.org/docs/17/runtime-config-resource.html>
  - MySQL 8.4: 10.2.1.4 Hash Join Optimization(`join_buffer_size`, 디스크 파일, `open_files_limit`, no condition) · 10.2.1.7 Nested-Loop Join Algorithms <https://dev.mysql.com/doc/refman/8.4/en/hash-joins.html>
- 로컬 재현(PostgreSQL 17.11, MySQL 8.4.10): 주문 30만 × 고객 5만 — PG 해시 조인(`Batches` 1 vs 32), 인덱스 중첩 루프 + Memoize, 병합 조인, 상관 컬럼 추정 오류(5 vs 500)와 확장 통계, 강제 중첩 루프 3292 ms vs 해시 15.6 ms; MySQL `Nested loop inner join`(PK 조회), `Inner hash join`, `Inner hash join (no condition)`, `join_buffer_size` 262144
