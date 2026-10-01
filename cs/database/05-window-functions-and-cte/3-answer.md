# database/05-window-functions-and-cte — 정답

## 정답

### 1. GROUP BY vs 윈도 함수

- `GROUP BY`는 그룹마다 한 행으로 접는다. 윈도 함수는 입력 행 수를 그대로 두고 값을 옆에 붙인다.
- 윈도 함수 없이 행마다 누계를 구하면 자기 조인(`s2.d <= s1.d`인 행을 모두 붙여 합)이나 상관 서브쿼리가 된다. 행마다 앞의 행 전부를 보므로 비교 횟수가 행 수의 제곱에 비례한다.
- 윈도 함수는 한 번 정렬한 뒤 앞에서부터 훑으며 누계를 이어 간다(누계처럼 앞 행만 필요한 경우. 뒤 행이 필요한 프레임은 파티션을 버퍼에 모아 두고 읽는다).

### 2. 기본 프레임 vs ROWS

| d | amt | `ORDER BY d` (기본 RANGE) | `ROWS UNBOUNDED PRECEDING` |
|---|---|---|---|
| 09-01 | 10 | 10 | 10 |
| 09-02 | 20 | 60 | 30 |
| 09-02 | 30 | 60 | 60 |
| 09-03 | 40 | 100 | 100 |

- 기본 프레임은 `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`다. 현재 행의 **마지막 피어**(같은 d)까지 포함하므로 09-02 두 행이 모두 60이다(PostgreSQL 4.2.8, MySQL 14.20.3). 로컬 재현에서 PostgreSQL 17.11과 MySQL 8.4.10이 같은 값을 냈다.
- `ROWS`는 물리 행 단위라 행마다 다르다. 단 09-02 두 행 중 어느 것이 먼저인지는 정렬 키가 유일해야 정해진다.

### 3. 순위 함수

| d | row_number | rank | dense_rank |
|---|---|---|---|
| 09-01 | 1 | 1 | 1 |
| 09-02 | 2 | 2 | 2 |
| 09-02 | 3 | 2 | 2 |
| 09-03 | 4 | 4 | 3 |

- `row_number`는 동률 두 행에 2와 3을 준다. 어느 행이 2인지는 **정해지지 않는다.** 계획이나 물리 순서에 따라 바뀔 수 있다. 정렬 키에 유일 키를 더해야 고정된다.

### 4. `last_value`

- 기본 프레임이 현재 행(의 마지막 피어)에서 끝난다. `ORDER BY d, amt`는 행마다 유일해 피어가 없으므로 프레임의 마지막 행 = 현재 행이다. 로컬 재현: 10, 20, 30, 40.
- 고치기: `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING`으로 프레임을 넓힌다 → 모두 40.
- `row_number`·`rank`는 프레임이 아니라 파티션 전체를 기준으로 계산하는 함수라 영향이 없다(PostgreSQL 9.22: `first_value`·`last_value`·`nth_value`와 집계 함수가 프레임을 본다).

### 5. 윈도 함수로 거르기

- 윈도 함수는 WHERE·GROUP BY·HAVING 뒤 SELECT 단계에서 계산된다. WHERE 시점에는 값이 없다. PostgreSQL은 `42P20 window functions are not allowed in WHERE`.

```sql
SELECT * FROM (
  SELECT o.*, row_number() OVER (PARTITION BY customer_id ORDER BY created_at DESC, id DESC) AS rn
  FROM orders o
) t
WHERE rn = 1;
```

- PostgreSQL 17.11 계획에 `WindowAgg` 아래 `Run Condition: (row_number() OVER (?) <= 2)`가 보였다(로컬 재현, `rn <= 2`). 바깥 조건을 윈도 계산 쪽으로 당긴 최적화다. 조건이 거짓이 되면 `PARTITION BY`가 없는 최상위 `WindowAgg`는 실행을 끝내고, 파티션이 있으면 그 파티션의 남은 행을 계산 없이 건너뛰는(pass-through) 모드로 들어간다(`src/backend/executor/nodeWindowAgg.c`, PostgreSQL 15+).

### 6. CTE 인라인과 구체화

- PostgreSQL 12+: 부작용이 없고, 재귀가 아니고, 한 번만 참조되는 CTE는 바깥 쿼리에 녹아 들어간다. 두 번 이상 참조되면 한 번 계산해 저장한다. `MATERIALIZED` / `NOT MATERIALIZED`로 바꿀 수 있다(7.8.3).
- 먼저 계산되면 바깥 조건이 안으로 내려가지 않는다. 원본 전체를 복사해 두고 거르므로 원본 인덱스를 쓸 수 없다. 로컬 재현: 기본은 `Seq Scan on item Filter: (id = 3)`, `MATERIALIZED`는 `CTE Scan on w Filter: (id = 3)`.
- 반대로 비싼 계산을 여러 번 참조하면 구체화가 이득이다.
- MySQL 8.4: 비재귀 CTE는 파생 테이블·뷰와 똑같이 다룬다. 가능하면 바깥 쿼리에 병합하고, 아니면 내부 임시 테이블로 구체화한다. 재귀 CTE는 항상 구체화한다(10.2.2.4).

### 7. 재귀 CTE 실행

```text
  W ← 비재귀 항 결과, R ← W
  W가 비지 않는 동안: N ← 재귀 항(W), (UNION이면 중복·기존 행 제거), R ← R ∪ N, W ← N

  1회차 W = {ceo}         (depth 1)
  2회차 W = {cto}         (depth 2)
  3회차 W = {dev, ops}    (depth 3)
  4회차 W = {}            → 종료
```

- 회차 하나가 한 층이다. **BFS**와 같다. 작업 테이블은 BFS의 프런티어, `UNION`의 중복 제거는 방문 집합이다.
- 이름과 달리 내부는 반복이다(PostgreSQL 7.8.2 Note).

### 8. 조직도 무한 반복

- 보이는 형태
  - PostgreSQL: 시간 한도가 없으면 끝나지 않는다. `statement_timeout`이 있으면 `ERROR 57014 canceling statement due to statement timeout`(로컬 재현, 2초). `pg_stat_activity`에 오래 도는 쿼리.
  - MySQL: `ERROR 3636 … Recursive query aborted after 1001 iterations`(기본 `cte_max_recursion_depth = 1000`).
- 원인: 데이터에 순환이 생겼다(예: ceo의 상사를 dev로). `UNION ALL`에 depth처럼 매번 바뀌는 열이 있어 행이 계속 "새 행"이다.
- 대처
  - 쿼리: 깊이 상한(`WHERE depth < 20`), 경로 검사(`NOT e.id = ANY(path)`), PostgreSQL 14+ `CYCLE id SET is_cycle USING path`.
  - 서버: 역할별 `statement_timeout`(PostgreSQL), `MAX_EXECUTION_TIME` 힌트·`cte_max_recursion_depth`(MySQL).
  - 쓰기 경로: 상사·부모를 바꿀 때 새 부모가 자기 하위인지 검사해 순환을 애초에 막는다.

### 9. MySQL 재귀 열 폭

- 원인: MySQL은 CTE 결과 열의 타입을 **비재귀 항만** 보고 정한다. 비재귀 항이 짧은 문자열이면 그 폭으로 고정되고, 재귀 항이 만든 긴 값은 엄격 모드에서 1406 오류, 엄격 모드가 아니면 잘린다(MySQL 8.4 15.2.20).
- 해결: 비재귀 항에서 `CAST(id AS CHAR(1000))`처럼 충분한 폭을 준다.
- PostgreSQL은 로컬 재현에서 `text`·배열로 경로를 쌓아 문제가 없었다.
