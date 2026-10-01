# database/12-query-optimizer-and-explain — 정답

## 정답

### 1. 옵티마이저가 최소화하는 것

- 옵티마이저는 **추정 비용**이 가장 낮은 계획을 고른다. 실제 실행 시간을 재 보고 고르는 것이 아니다.
- 비용 = 비용 상수(`seq_page_cost`, `random_page_cost`, `cpu_tuple_cost` …) × 추정한 페이지 수·행 수다.
- 추정 행 수는 통계(`reltuples`, `relpages`, `pg_stats`의 MCV·히스토그램)와 가정(균등·독립·포함)으로 만든다.
- 그래서 통계가 낡았거나 가정이 깨지면, 옵티마이저는 "싸다고 믿은" 느린 계획을 고른다.
- 탐색 자체도 완전하지 않을 수 있다. PostgreSQL은 `geqo`가 켜져 있고(기본) FROM 항목이 12개 이상이면 GEQO로 일부만 탐색한다.

### 2. Seq Scan 비용

```text
  (페이지 × seq_page_cost) + (행 × cpu_tuple_cost)
  = 4,673 × 1.0 + 500,000 × 0.01
  = 4,673 + 5,000 = 9,673
  → Seq Scan on ev  (cost=0.00..9673.00 rows=500000 ...)
```

- 단위는 시간이 아니다. 순차 페이지 읽기 하나를 1로 둔 **상대 점수**다(PostgreSQL 14.1, 19.7.2).
- 시작 비용이 0.00인 것은 Seq Scan이 첫 행을 곧바로 낼 수 있어서다.

### 3. 상관된 두 조건

- 독립 가정: sel(city) × sel(country) = 0.005 × 0.05 = 0.00025 → 20만 × 0.00025 = **약 50행**.
  - 로컬 재현(PostgreSQL 17.11)에서는 `Gather`가 `rows=58`로 추정했다. 통계가 표본에서 나온 근사값이라 50과 조금 다르다.
- 실제: c11이면 country는 이미 k1이다. country 조건은 아무것도 더 거르지 않으므로 선택도는 sel(city) = 0.5% → **1,000행**.
- 수십 배 과소추정이다. 이 결과가 조인의 바깥 입력이 되면 중첩 루프가 뽑힌다.
- 고치는 법: `CREATE STATISTICS … (dependencies) ON city, country FROM orders; ANALYZE orders;` → 재현에서 추정 1,060, 실제 1,000.

### 4. 조인 순서 DP

```text
  크기 1:  best{A}  best{B}  best{C}               (스캔 방법별 최선)
  크기 2:  best{A,B} = 가장 싼 (A⋈B | B⋈A) × (NL|Hash|Merge)
           best{A,C}, best{B,C}                     (조인 조건 있는 쌍 우선)
  크기 3:  best{A,B,C} = min( best{A,B}⋈C, best{A,C}⋈B, best{B,C}⋈A )
```

- 나은 점: 부분집합마다 최선 하나만 남기고 재사용한다. 같은 부분 계획을 다시 계산하지 않는다. 순서를 다 나열하면 n!에 조인 방법 조합까지 곱해진다.
- 정렬 순서처럼 위에서 쓸모 있는 성질이 다른 계획은 따로 남긴다(병합 조인이 정렬을 재사용할 수 있으므로).
- PostgreSQL은 `geqo`(기본 on)가 켜져 있고 FROM 항목이 `geqo_threshold`(기본 12)개 이상이면 유전 알고리즘으로 넘어간다. `FULL OUTER JOIN` 구문은 FROM 항목 하나로 센다(19.7.3).

### 5. 계획 읽기

- 출발점은 **`Index Scan on o2 (rows=6) (actual rows=100010)`**다. 가장 아래에서 추정과 실제가 처음 크게 어긋난다.
- 위의 `Nested Loop`의 어긋남은 이 노드의 결과다.
- `Index Only Scan on cust`는 `loops=100010`이다. 한 번에 1행씩이지만 10만 번 인덱스를 내려갔다.
- 한 문장: "옵티마이저가 o2에서 6행만 나온다고 믿고 중첩 루프를 골랐는데, 실제로는 10만 행이 나와 cust 인덱스를 10만 번 찔렀다."

### 6. 배치 뒤 느려진 조회

1. `EXPLAIN (ANALYZE, BUFFERS)`로 추정과 실제가 어긋나는 가장 아래 노드와 그 테이블을 찾는다.
2. `pg_stat_user_tables`에서 그 테이블의 `n_mod_since_analyze`, `last_analyze`, `last_autoanalyze`를 본다.
3. `pg_stats`에서 조건 컬럼의 MCV 빈도가 현재 분포와 맞는지 본다.

- 긴급: `ANALYZE <테이블>` 후 다시 `EXPLAIN ANALYZE`. 로컬 재현에서는 중첩 루프(152ms)가 해시 조인(82ms)으로 바뀌었다. 데이터가 메모리에 있어 2배였고, 디스크 임의 읽기가 끼면 차이가 더 커진다.
- 재발 방지: 배치 마지막 단계에 `ANALYZE`. 자주 크게 바뀌는 테이블은 테이블 단위로 `autovacuum_analyze_scale_factor`를 낮춘다.
- PostgreSQL 17 문턱: 바뀐 행 수 > `autovacuum_analyze_threshold`(50) + `autovacuum_analyze_scale_factor`(0.1) × reltuples.

### 7. MySQL 히스토그램

- 히스토그램이 없을 때: `filtered = 10.00`. 인덱스가 없는 컬럼의 등호 조건에 통계가 없어 고정값으로 추정했다(로컬 재현, MySQL 8.4.10).
- `ANALYZE TABLE o2 UPDATE HISTOGRAM ON status WITH 16 BUCKETS` 뒤: `filtered = 0.10`, 반복자 추정 `rows=100`으로 실제 100과 같아졌다. 값이 2종류라 singleton 히스토그램이 만들어졌다.
- 자동 갱신: 기본(`MANUAL UPDATE`)이면 **안 된다.** 다시 `ANALYZE TABLE … UPDATE HISTOGRAM` 해야 한다. MySQL 8.4 문서의 `AUTO UPDATE` 절로 만들면 `ANALYZE TABLE`과 InnoDB 자동 통계 재계산 때 함께 갱신된다.

### 8. 준비된 문장의 일반 계획

- 의심: 서버 측 준비된 문장이 **일반 계획**으로 바뀌었다.
  - PostgreSQL은 처음 5번은 값을 넣은 맞춤 계획을 쓴다. 그다음 일반 계획의 추정 비용이 맞춤 계획 평균보다 크게 나쁘지 않으면 일반 계획을 쓴다(PREPARE 문서).
  - 일반 계획은 값을 모른 채 만든다. 흔한 값과 드문 값의 최적 계획이 다르면 한쪽이 느리다.
- 확인: `auto_explain` 로그에서 조건이 상수 대신 `$1`로 보이는지 본다. psql에서 `PREPARE`한 뒤 6번 넘게 `EXECUTE`하며 `EXPLAIN`을 비교해 재현한다.
- 대처: 그 역할·세션에 `plan_cache_mode = force_custom_plan`. 또는 드라이버의 서버 측 준비 사용을 조절한다. pgJDBC는 `prepareThreshold`(기본 5)번째 실행부터 서버 측 준비 문장을 쓰고, `0`이면 쓰지 않는다(pgJDBC 문서). 그래서 pgJDBC에서는 psql `PREPARE`보다 늦게 느려지기 시작한다.

### 9. EXPLAIN vs EXPLAIN ANALYZE

- `EXPLAIN`: 계획과 **추정**만 보여 준다. 실행하지 않는다.
- `EXPLAIN ANALYZE`: 쿼리를 **실제로 실행**하고, 노드마다 실제 행 수·시간·loops를 덧붙인다.
- `UPDATE`·`DELETE`에 쓰면 실제로 바뀐다. `BEGIN; EXPLAIN ANALYZE UPDATE …; ROLLBACK;`으로 감싼다. MySQL 8.4의 `EXPLAIN ANALYZE`도 실제로 실행한다.
- `loops=100010`, `actual rows=1`: 한 번 실행당 평균 1행이다. 이 노드는 총 약 100,010행을 냈고, 시간도 loops를 곱해 총량을 본다(PostgreSQL 14.1).
