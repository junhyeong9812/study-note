# database/05-window-functions-and-cte — 윈도 함수·CTE·재귀 CTE: 행을 접지 않는 계산과 반복 — 정리 (힌트)

## 해결하는 문제

`GROUP BY`(04번)는 여러 행을 **한 줄로 접는다**. 그런데 이런 질문은 행을 그대로 둔 채 옆에 값을 붙여야 한다.

- 날짜별 매출 옆에 "그날까지의 누계"
- 사원마다 "부서 안 급여 순위"
- 주문마다 "직전 주문과의 간격"
- 고객별 "가장 최근 주문 한 건"

윈도 함수가 없으면 자기 조인으로 푼다. 행마다 앞의 행 전부와 조인하니 행 수의 제곱에 비례해 커진다. 앱에서 루프를 돌면 DB에서 모든 행을 가져와야 한다.

그리고 계층 데이터가 있다.

- 조직도: 사장 → 본부장 → 팀장 → 팀원. 깊이를 미리 모른다.
- 카테고리 트리, 댓글 스레드, 부품 명세(BOM).

조인을 몇 번 할지 미리 모르면 보통 SQL로는 못 쓴다. 재귀 CTE가 "결과가 안 늘어날 때까지 반복"을 SQL 안에 넣는다.

쉬운 예: 성적표에 "반 평균"을 한 줄로 받는 것(GROUP BY)과, 학생마다 "내 점수, 반 평균, 반 등수"를 같이 적는 것(윈도 함수)은 다르다.

똑같은 구조다.\
윈도 함수는 **각 행마다 그 행과 관련된 행들의 창(window)**을 정하고, 그 창 위에서 계산한 값을 그 행에 붙인다.

실무 예:
- 일별 누계 차트가 같은 날짜의 두 거래에서 같은 값으로 두 번 찍힌다(기본 프레임 함정).
- 조직도에 순환(A의 상사가 B, B의 상사가 A)이 생긴 뒤 재귀 쿼리가 끝나지 않는다.

## 동작·원리

### 1. GROUP BY vs 윈도 함수

```text
  sales                       GROUP BY d                   SUM(amt) OVER (PARTITION BY d)
  d      amt                  d      sum                   d      amt  sum
  09-01  10                   09-01  10                    09-01  10   10
  09-02  20        ──►        09-02  50          vs        09-02  20   50
  09-02  30                   09-03  40                    09-02  30   50     <- 행이 그대로 남는다
  09-03  40                   (행이 접힌다)                  09-03  40   40
```

- *윈도 함수(window function)*: 현재 행과 관련된 행 집합(창) 위에서 값을 계산해, 행을 접지 않고 붙이는 함수.
- `OVER (…)`가 붙으면 `SUM` 같은 집계 함수도 윈도 함수가 된다(PostgreSQL 17 3.5).

### 2. OVER 절의 세 부분

```text
  SUM(amt) OVER ( PARTITION BY dept   ORDER BY d   ROWS BETWEEN 2 PRECEDING AND CURRENT ROW )
                  └── 어느 행끼리 ──┘ └ 창 안 순서 ┘ └──────── 프레임: 창 중 어디까지 ──────────┘
```

- *파티션(partition)*: 같은 값끼리 묶은 행 집합. 창은 파티션을 넘지 않는다. 생략하면 전체가 한 파티션이다.
- *피어(peer)*: 창의 `ORDER BY` 값이 현재 행과 같은 행들.
- *프레임(frame)*: 파티션 안에서 현재 행 기준으로 실제 계산에 쓰는 범위. 집계 함수와 `first_value`·`last_value`·`nth_value`는 프레임만 본다. `row_number`·`rank`는 파티션 전체를 본다(PostgreSQL 17 9.22).

CMU L2가 적은 개념적 실행 순서: ① 파티션으로 나눈다 → ② 파티션마다 정렬 → ③ 행마다 창을 정한다 → ④ 창 위에서 계산.

### 3. 기본 프레임 — `ORDER BY`가 있으면 `RANGE … CURRENT ROW`

```text
  (예시, PostgreSQL 17.11 — MySQL 8.4.10도 같은 값)
  d      amt  SUM() OVER (ORDER BY d)   SUM() OVER (ORDER BY d ROWS UNBOUNDED PRECEDING)
  09-01  10   10                        10
  09-02  20   60   <- 같은 날짜(피어)      30
  09-02  30   60      를 모두 포함         60
  09-03  40   100                       100
```

- 기본 프레임은 `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`다. `ORDER BY`가 있으면 파티션 시작부터 **현재 행의 마지막 피어까지**다. `ORDER BY`가 없으면 파티션 전체다(PostgreSQL 17 4.2.8, MySQL 8.4 14.20.3).
- 그래서 같은 날짜 두 행이 누계 60을 **함께** 받는다. "행 단위 누계"를 원하면 `ROWS`를 명시하고, 정렬 키를 유일하게 만든다(`ORDER BY d, id`).
- 세 가지 단위

```text
  ROWS    : 물리적인 행 개수로 센다          (2 PRECEDING = 앞 2행)
  RANGE   : ORDER BY 값의 차이로 센다        (INTERVAL '1 day' PRECEDING = 값이 하루 이내)
  GROUPS  : 피어 그룹 개수로 센다            (1 PRECEDING = 앞 피어 그룹 하나)   — PostgreSQL 지원. MySQL 8.4는 `frame_units: {ROWS | RANGE}`만 있고(14.20.3), 로컬 재현에서 `ERROR 1235 … doesn't yet support 'GROUPS'`
```

- 로컬 재현(예시, PostgreSQL 17.11): `RANGE BETWEEN INTERVAL '1 day' PRECEDING AND CURRENT ROW`에서 09-03 행의 합은 20 + 30 + 40 = 90이었다(09-02와 09-03만 포함).

### 4. `last_value`의 함정 — 프레임이 현재 행에서 끝난다

```text
  (예시, PostgreSQL 17.11) ORDER BY d, amt 로 정렬
  amt  last_value(amt) OVER (ORDER BY d, amt)    … ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
  10   10                                        40
  20   20                                        40
  30   30                                        40
  40   40                                        40
```

- 기본 프레임이 현재 행(의 마지막 피어)에서 끝나므로 "마지막 값"이 곧 현재 행이다. PostgreSQL 문서도 이것이 `last_value`에 "도움이 안 되는 결과"를 낸다고 적는다(9.22). 프레임을 `UNBOUNDED FOLLOWING`까지 넓힌다.

### 5. 순위 함수 셋

```text
  (예시, PostgreSQL 17.11) ORDER BY d
  d      row_number  rank  dense_rank
  09-01  1           1     1
  09-02  2           2     2
  09-02  3           2     2      <- 동률
  09-03  4           4     3      <- rank는 건너뛰고, dense_rank는 안 건너뜀
```

- `row_number`는 동률에서도 번호를 다르게 준다. **동률끼리 누가 먼저인지는 정해지지 않는다.** 정렬 키를 유일하게 해야 매번 같은 행이 1번이 된다.

### 6. 평가 시점 — WHERE보다 뒤

- 윈도 함수는 WHERE·GROUP BY·HAVING이 끝난 뒤 SELECT 단계에서 계산된다(04번 논리 순서, PostgreSQL 17 7.2.5).
- 그래서 `WHERE row_number() OVER (…) = 1`은 `42P20` 오류다. 서브쿼리나 CTE로 감싸고 바깥에서 거른다.
- PostgreSQL 15+는 이런 바깥 조건을 `WindowAgg`의 `Run Condition`으로 당겨 와 필요한 만큼만 계산한다. 로컬 재현(PostgreSQL 17.11)에서 `WHERE rn <= 2`가 `Run Condition: (row_number() OVER (?) <= 2)`로 보였다(PostgreSQL 15 릴리스 노트 "Improve the performance of window functions that use row_number(), rank(), dense_rank() and count()". EXPLAIN의 `Run Condition` 출력은 `src/backend/commands/explain.c`에 REL_15_STABLE부터 있고 REL_14_STABLE에는 없다).

### 7. CTE — 쿼리 안의 이름 붙은 임시 결과

```sql
WITH recent AS (                                  -- 이름 붙은 부분 쿼리
  SELECT * FROM orders WHERE created_at >= now() - interval '7 days'
)
SELECT customer_id, count(*) FROM recent GROUP BY customer_id;
```

- *CTE(Common Table Expression)*: `WITH` 절로 정의해 그 쿼리 안에서만 쓰는 임시 결과. 한 쿼리 범위의 임시 테이블처럼 생각하면 된다(CMU L2 §12).
- 인라인이냐 구체화냐
  - PostgreSQL 12+: 부작용이 없고, 재귀가 아니고, **한 번만** 참조되는 CTE는 바깥 쿼리에 녹여 넣는다(인라인). 두 번 이상 참조되면 한 번 계산해 저장한다(구체화). `MATERIALIZED`·`NOT MATERIALIZED`로 강제할 수 있다(PostgreSQL 17 7.8.3, PostgreSQL 12 릴리스 노트).
  - 로컬 재현(예시, PostgreSQL 17.11): 기본은 `Seq Scan on item, Filter: (id = 3)`(녹아 들어감), `MATERIALIZED`면 `CTE Scan on w, Filter: (id = 3)` 아래 `CTE w -> Seq Scan on item`(전체를 먼저 만들고 거름).
  - MySQL 8.4: 비재귀 CTE는 파생 테이블·뷰와 똑같이 다룬다. 바깥 쿼리에 병합하거나 내부 임시 테이블로 구체화한다. 재귀 CTE는 항상 구체화한다(10.2.2.4).

### 8. 재귀 CTE — 결과가 안 늘 때까지 반복

```text
  WITH RECURSIVE t(id, depth) AS (
      SELECT id, 1 FROM emp WHERE boss IS NULL          -- ① 비재귀 항: 시작점
    UNION ALL
      SELECT e.id, t.depth + 1 FROM emp e JOIN t ON e.boss = t.id   -- ② 재귀 항: 직전 결과로 한 단계
  )
  SELECT * FROM t;

  실행 (PostgreSQL 17 7.8.2 "Recursive Query Evaluation")
  작업 테이블 W ← ① 결과                           결과 R ← W
  반복: W가 비지 않는 동안
        N ← ②를 W에 대해 계산 (자기 참조 = W)
        (UNION이면 N에서 중복과 R에 이미 있는 행 제거)
        R ← R ∪ N ;  W ← N
```

```text
  조직도 emp: ceo(1) ← cto(2) ← dev(3), ops(4)

  1회차 W = {ceo}             depth 1
  2회차 W = {cto}             depth 2
  3회차 W = {dev, ops}        depth 3
  4회차 W = {}                → 종료
```

- 이름은 "재귀"지만 실제로는 **반복**이다(PostgreSQL 7.8.2 Note). 한 회차가 BFS의 한 층과 같다.
- 종료 조건은 "재귀 항이 새 행을 하나도 안 낼 때"뿐이다. 순환이 있으면 `UNION ALL`은 끝나지 않는다.

```text
  순환 추가: UPDATE emp SET boss = 3 WHERE id = 1  (ceo의 상사 = dev)
  이제 boss IS NULL인 행이 없어 위 ①은 0행 → 결과도 0행 (순환이 안 보인다)
  시작을 ① WHERE id = 1 로 고정하면:
  ceo → cto → dev → ceo → cto → …   depth만 계속 늘어난다 (행이 매번 "새 행")
```

- 로컬 재현(예시)
  - PostgreSQL 17.11: `SET statement_timeout = '2s'` 아래에서 `ERROR 57014 canceling statement due to statement timeout`. 시간 제한이 없으면 끝나지 않는다.
  - MySQL 8.4.10: `ERROR 3636 (HY000): Recursive query aborted after 1001 iterations. Try increasing @@cte_max_recursion_depth to a larger value.` 기본 `cte_max_recursion_depth = 1000`이다(15.2.20).
- 끝내는 방법 세 가지

```sql
-- (가) 깊이 상한: 재귀 항에 조건
… JOIN t ON e.boss = t.id WHERE t.depth < 10
-- (나) PostgreSQL 14+ CYCLE 절: 경로를 기록해 같은 id가 다시 나오면 멈춘다
WITH RECURSIVE t(id, depth) AS (…)
  CYCLE id SET is_cycle USING path
SELECT * FROM t;
-- (다) UNION(중복 제거): 방문한 "행"을 다시 넣지 않는다 — depth 같은 변하는 열이 없을 때만 효과
WITH RECURSIVE t(id) AS (SELECT 1 UNION SELECT e.id FROM emp e JOIN t ON e.boss = t.id) SELECT * FROM t;
```

- 로컬 재현(예시, PostgreSQL 17.11): (가) 13행·최대 depth 10에서 멈춤. (나) `1 | 4 | t | {(1),(2),(3),(1)}` 행에서 `is_cycle = t`로 표시하고 멈춤. (다) 1, 2, 3, 4 네 행.

## 쓰이는 자료구조·알고리즘

- **정렬 + 한 번 훑기**: 윈도 함수는 파티션·정렬 키로 정렬한 뒤, 정렬된 행을 앞에서부터 훑으며 창을 옮긴다. 다만 `lead`·`FOLLOWING` 프레임처럼 뒤 행이 필요한 경우를 위해 PostgreSQL 17 `WindowAgg`는 현재 파티션의 행을 tuplestore에 모아 두고 필요한 행에 접근한다(`src/backend/executor/nodeWindowAgg.c` 머리 주석). 계획에 `WindowAgg` 위 `Sort`가 보인다(로컬 재현). [algorithm/02-merge-sort](../../algorithm/02-merge-sort/2-summary.md)
- **슬라이딩 윈도**: `ROWS BETWEEN 2 PRECEDING AND CURRENT ROW` 같은 이동 프레임은 창이 한 칸 움직일 때 들어온 값과 나간 값만 반영할 수 있다. [algorithm/09-sliding-window](../../algorithm/09-sliding-window/2-summary.md) · 누계는 [algorithm/10-prefix-sum](../../algorithm/10-prefix-sum/2-summary.md)
- **재귀 CTE = 층별 BFS(고정점 반복)**: 작업 테이블이 BFS의 프런티어다. `UNION`의 중복 제거가 방문 집합 역할을 한다. [algorithm/11-bfs](../../algorithm/11-bfs/2-summary.md), [data-structure/08-graph](../../data-structure/08-graph/2-summary.md)
- **경로 기반 순환 탐지**: `CYCLE` 절은 행마다 지나온 경로 배열을 들고 다니며 "이 id가 경로에 있나"를 본다. DFS의 "현재 경로 위 노드" 검사와 같은 생각이다. [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 자주 쓰는 모양

```sql
-- 행 단위 누계: 프레임과 유일 정렬 키를 명시
SELECT d, id, amt,
       SUM(amt) OVER (ORDER BY d, id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running
FROM sales;

-- 그룹별 상위 N (고객별 최근 주문 1건)
SELECT * FROM (
  SELECT o.*, row_number() OVER (PARTITION BY customer_id ORDER BY created_at DESC, id DESC) AS rn
  FROM orders o
) t WHERE rn = 1;

-- 직전 행과 비교
SELECT id, created_at,
       created_at - lag(created_at) OVER (PARTITION BY customer_id ORDER BY created_at, id) AS gap
FROM orders;
```

### 2. 계층 조회는 상한과 순환 대비를 같이

```sql
WITH RECURSIVE org(id, name, depth, path) AS (
  SELECT id, name, 1, ARRAY[id] FROM emp WHERE boss IS NULL
  UNION ALL
  SELECT e.id, e.name, o.depth + 1, o.path || e.id
  FROM emp e JOIN org o ON e.boss = o.id
  WHERE o.depth < 20                      -- 깊이 상한
    AND NOT e.id = ANY(o.path)            -- 순환 차단 (PostgreSQL 배열; 14+면 CYCLE 절)
)
SELECT * FROM org ORDER BY path;
```

- MySQL: 배열이 없으므로 경로를 문자열로 들고 다니며 `FIND_IN_SET`·`LOCATE`로 검사하거나 깊이 상한을 둔다. 문자열 열의 폭은 **비재귀 항**이 정하므로 `CAST(id AS CHAR(1000))`처럼 넉넉히 잡는다(아래 장애 4).

### 3. 진단

```sql
-- PostgreSQL: 정렬이 디스크로 넘치는지, 재귀가 몇 행을 만들었는지
EXPLAIN (ANALYZE, BUFFERS) SELECT …;      -- WindowAgg / Sort Method: external merge / Recursive Union / WorkTable Scan
SET statement_timeout = '5s';             -- 세션 단위 안전장치
-- MySQL
EXPLAIN ANALYZE SELECT …;
SET SESSION cte_max_recursion_depth = 100;
SELECT /*+ MAX_EXECUTION_TIME(1000) */ …;
```

- 문법 세부는 [sql/26 윈도 vs 집계](../../../languages/sql/syntax/26-window-functions-vs-aggregates/2-summary.md) · [sql/28 프레임](../../../languages/sql/syntax/28-window-frames-rows-range-groups/2-summary.md) · [sql/29 순위 함수](../../../languages/sql/syntax/29-ranking-functions/2-summary.md) · [sql/31 평가 시점](../../../languages/sql/syntax/31-window-evaluation-timing/2-summary.md) · [sql/32 CTE](../../../languages/sql/syntax/32-cte-with-clause/2-summary.md) · [sql/33 재귀 CTE](../../../languages/sql/syntax/33-recursive-cte/2-summary.md).

## 장애 시나리오와 대처

### 1. 기본 `RANGE` 프레임 → 동률 행이 같은 누계 (⚠ 커리큘럼)

- **현상**: 일별 누계 그래프가 계단처럼 튄다. 같은 시각 거래 두 건이 같은 누계를 받아, 첫 건의 누계가 실제보다 크다.
- **보이는 형태**: 에러 없음. 로컬 재현(예시, 두 제품 동일): 09-02의 20원·30원 행이 모두 60.
- **원인**: `ORDER BY`만 쓰면 프레임이 `RANGE … CURRENT ROW`라 피어(같은 정렬 값)를 전부 포함한다.
- **대처**: `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`를 명시하고, 정렬 키에 유일 키를 더한다. 날짜별 누계가 목적이면 먼저 날짜로 집계한 뒤 누계를 낸다.

### 2. 재귀 CTE 종료 조건 누락 → 끝나지 않는다 (⚠ 커리큘럼)

- **현상**: 조직도·카테고리 API가 응답하지 않는다. DB CPU와 임시 파일 사용량이 오른다.
- **보이는 형태**
  - PostgreSQL: 제한이 없으면 계속 돈다. `statement_timeout`이 있으면 `ERROR 57014 canceling statement due to statement timeout`. `pg_stat_activity`에 오래 도는 `WITH RECURSIVE` 쿼리.
  - MySQL: `ERROR 3636 … Recursive query aborted after 1001 iterations`(기본 `cte_max_recursion_depth = 1000`).
- **원인**: 데이터에 순환이 생겼다(잘못된 상사 지정, 카테고리를 자기 하위로 이동). `UNION ALL` + 매번 바뀌는 열(depth·path) 때문에 모든 행이 "새 행"이다.
- **대처**
  - 깊이 상한, 경로 검사, PostgreSQL 14+ `CYCLE` 절 중 하나를 쿼리에 넣는다.
  - 서버 쪽 시간 한도를 역할별로 둔다([22-database-side-timeouts](../22-database-side-timeouts/2-summary.md)).
  - 근본: 쓰기 때 순환을 막는다(이동 시 대상이 자기 하위인지 검사).

### 3. `row_number() = 1` 중복 제거가 매번 다른 행을 고른다

- **현상**: "고객별 최신 주소"가 조회할 때마다 바뀐다.
- **보이는 형태**: 에러 없음. 같은 `created_at`을 가진 두 행이 번갈아 뽑힌다.
- **원인**: 창의 `ORDER BY`에 동률이 있으면 `row_number`가 누구에게 1을 줄지 정해지지 않는다(01번의 "순서는 약속이 아니다"와 같은 이유).
- **대처**: `ORDER BY created_at DESC, id DESC`처럼 유일 키를 끝에 둔다.

### 4. MySQL 재귀 CTE가 `Data too long`으로 실패

- **현상**: 경로 문자열을 쌓는 재귀 쿼리가 MySQL에서만 실패한다.
- **보이는 형태**: `ERROR 1406 (22001): Data too long for column 'n' at row 1`(로컬 재현, MySQL 8.4.10). 엄격 모드가 아니면 오류 대신 잘린 값이 나온다(MySQL 8.4 15.2.20).
- **원인**: MySQL은 CTE 결과 열의 타입을 **비재귀 항만** 보고 정한다. 비재귀 항이 `'a'`(길이 1)면 그 폭으로 고정된다.
- **대처**: 비재귀 항에서 `CAST(… AS CHAR(1000))`처럼 폭을 넉넉히 준다.

### 5. CTE 구체화로 인덱스를 못 탄다

- **현상**: CTE로 정리한 쿼리가 서브쿼리 버전보다 훨씬 느리다.
- **보이는 형태**: PostgreSQL 계획에 `CTE Scan` + `Filter`가 있고, 원본 테이블 인덱스가 안 쓰인다. 로컬 재현에서 `MATERIALIZED`를 붙이자 `CTE w -> Seq Scan` 뒤에 필터가 걸렸다.
- **원인**: CTE가 두 번 이상 참조됐거나 `MATERIALIZED`로 지정돼 먼저 전체를 만든다. 바깥 조건이 안으로 내려가지 않는다(PostgreSQL 17 7.8.3의 `big_table` 예). PostgreSQL 11 이하는 CTE를 항상 구체화했다(12 릴리스 노트).
- **대처**: 한 번만 쓰는 CTE는 그대로 두고(자동 인라인), 여러 번 쓰는데 각자 일부만 필요하면 `NOT MATERIALIZED`를 검토한다. 반대로 비싼 계산을 한 번만 하려면 `MATERIALIZED`를 쓴다.

## 핵심 문장

- 윈도 함수는 행을 접지 않고, 각 행마다 창(파티션 + 순서 + 프레임)을 정해 그 위에서 계산한 값을 붙인다.
- `ORDER BY`만 쓴 기본 프레임은 `RANGE … CURRENT ROW`라 동률 행을 함께 포함한다. 행 단위 누계는 `ROWS`와 유일 정렬 키를 명시한다.
- 윈도 함수는 WHERE 뒤 SELECT 단계에서 계산되므로, 그 결과로 거르려면 한 겹 감싼다.
- CTE는 쿼리 안의 이름 붙은 결과다. PostgreSQL 12+는 한 번 쓰는 CTE를 녹여 넣고, `MATERIALIZED`로 이를 바꿀 수 있다.
- 재귀 CTE는 "새 행이 없을 때까지"의 층별 반복(BFS)이다. 순환 데이터에는 깊이 상한·경로 검사·`CYCLE`과 서버 시간 한도가 필요하다.

## 관련 주제·근거

- 선행: [04-sql-joins-and-aggregation](../04-sql-joins-and-aggregation/2-summary.md)
- 연결
  - [01-relational-model-and-algebra](../01-relational-model-and-algebra/2-summary.md) — 유일 정렬 키
  - [36-data-models-document-graph](../36-data-models-document-graph/2-summary.md) — 재귀 CTE로 그래프 질의
  - [22-database-side-timeouts](../22-database-side-timeouts/2-summary.md) · [41-sorting-and-aggregation](../41-sorting-and-aggregation/2-summary.md)
  - data-analysis `17-sql-for-analysis`(코호트·퍼널·세션화) — 미작성, [data-analysis/README](../../data-analysis/README.md)
- 문법 세부(languages/sql): [sql/26](../../../languages/sql/syntax/26-window-functions-vs-aggregates/2-summary.md) · [sql/28](../../../languages/sql/syntax/28-window-frames-rows-range-groups/2-summary.md) · [sql/29](../../../languages/sql/syntax/29-ranking-functions/2-summary.md) · [sql/31](../../../languages/sql/syntax/31-window-evaluation-timing/2-summary.md) · [sql/32](../../../languages/sql/syntax/32-cte-with-clause/2-summary.md) · [sql/33](../../../languages/sql/syntax/33-recursive-cte/2-summary.md)
- 교재: CMU 15-445 Fall 2024 Lecture #02 "Modern SQL" §9 Window Functions(개념적 실행 4단계), §12 CTE(재귀 CTE로 SQL은 튜링 완전) <https://15445.courses.cs.cmu.edu/fall2024/notes/02-modernsql.pdf> · Silberschatz 7판 5장 슬라이드 "Recursive Queries"
- PostgreSQL 17
  - 3.5 Window Functions(튜토리얼, 기본 프레임) <https://www.postgresql.org/docs/17/tutorial-window.html>
  - 4.2.8 Window Function Calls(기본 프레임 `RANGE UNBOUNDED PRECEDING`, ROWS/RANGE/GROUPS) <https://www.postgresql.org/docs/17/sql-expressions.html>
  - 9.22 Window Functions(`last_value`는 프레임만 봄) <https://www.postgresql.org/docs/17/functions-window.html>
  - 7.8 WITH Queries — 7.8.2(재귀 평가 절차, `CYCLE`), 7.8.3(인라인·`MATERIALIZED`) <https://www.postgresql.org/docs/17/queries-with.html>
  - 릴리스 노트 12(CTE 자동 인라인) · 14(SEARCH·CYCLE) · 15(`row_number()` 등 윈도 함수 성능) <https://www.postgresql.org/docs/release/>
- MySQL 8.4
  - 14.20.2 Window Function Concepts and Syntax · 14.20.3 Frame Specification(기본 프레임) <https://dev.mysql.com/doc/refman/8.4/en/window-functions-frames.html>
  - 15.2.20 WITH(`cte_max_recursion_depth` 기본 1000, `MAX_EXECUTION_TIME`, 열 타입은 비재귀 항이 결정, 엄격 모드 1406) <https://dev.mysql.com/doc/refman/8.4/en/with.html>
  - 10.2.2.4 Optimizing Derived Tables, View References, and Common Table Expressions(병합 vs 구체화) <https://dev.mysql.com/doc/refman/8.4/en/derived-table-optimization.html>
- 로컬 재현(PostgreSQL 17.11, MySQL 8.4.10): 기본 프레임 vs ROWS 누계(두 제품), 순위 함수 3종, `GROUPS`·`RANGE INTERVAL` 프레임, `last_value` 기본/전체 프레임, WHERE의 윈도 함수 42P20, `Run Condition`, CTE 인라인 vs `MATERIALIZED` 계획, 재귀 조직도, 순환 시 PG 57014·MySQL 3636, MySQL `GROUPS` 미지원 1235, 깊이 상한·`CYCLE`·`UNION` 종료, MySQL 재귀 열 폭 1406
