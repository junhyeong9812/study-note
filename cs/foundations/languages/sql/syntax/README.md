# SQL — 문법·함수 주제 목록

> **60주제 전부 작성됐다(2026-09-21).** 「주제」 칸의 링크가 각 주제의 3파일(질문·서머리·정답) 폴더다.
> **본문의 모든 출력은 실행 결과다** — PostgreSQL 18.6(도커 `postgres:18`)·MySQL 8.4.10(도커 `mysql:8.4`) 두 서버에 실제로 던져 받은 것이고, **에러와 경고도 출력으로 인용**했다.
> 「미지원」을 단정하기 전에 던져 본다는 규칙이 여러 번 값을 했다 — MySQL 이 `QUALIFY` 를 **파서에서는 안다**는 것(`ERROR 6037`)이 그렇게 나왔다.
> **진행 — 60 / 60 (완료)**. 총 **156파일**.
> ⚠️ **MySQL 에러 표기가 두 형태로 섞여 있다.** `mysql -e "..."` 로 던지면 `ERROR 1054 (42S22) **at line 1**: ...` 이고,
> 대화형에서는 `at line 1` 이 빠진다. 둘 다 실제 출력이며 **호출 방식의 차이**다 — 01·04 편이 후자, 나머지가 전자다.
> 재현할 때 문자열이 안 맞으면 이 차이를 먼저 의심하라.
> **조인 묶음(12 → 13 → 14 → 15 → 16)이 이어졌다** — 카티션곱 12행을 거르고(13) 되살리고(14·16), 조건의 자리로 그것이 무너지는 것(15)까지 한 사슬이다. 여섯 주제가 `study` DB 의 **`emp`·`dept`** 두 표를 01·04·16·52 와 공유한다.
> 기준 소스: [PostgreSQL 18 공식 문서](https://www.postgresql.org/docs/current/) · [MySQL 8.4 Reference Manual](https://dev.mysql.com/doc/refman/8.4/en/) — 두 문서의 목차와 명령·함수 분류를 대조해 축을 잡았다. 표준 SQL(ISO/IEC 9075)은 공개 요약 수준에서만 참조했고 **조항 번호는 확인하지 못했으므로 적지 않는다.**
> 실행 검증(1단계 당시 기록, 2026-09-20): **이 목록 자체에는 없다.** 이 머신에 `psql`·`mysql`·`sqlite3`·`duckdb` 가 전부 없어 한 줄도 돌려보지 못했다. 아래 방언 칸은 **문서 대조로만** 채운 것이다. → 2단계에는 **PostgreSQL 과 MySQL 둘 다** 필요하다(도커 컨테이너면 충분). `sqlite3` 는 설치가 가장 쉽지만 **이 목록의 방언 차이를 확인하는 데는 부적합**하다 — 세 번째 방언이라 PG·MySQL 어느 쪽도 대신하지 못한다. 설치는 하지 않았고 제안만 적는다. → **2026-09-21 에 두 컨테이너가 떴고 검증이 시작됐다**(위 둘째 줄).
> 기준일 2026-09-20(목록) · 2026-09-21(실행 검증 시작).

## 이 언어에서 무엇을 자르는 축

SQL 은 이 폴더의 다른 언어들과 자르는 축이 다르다.
제어 흐름·타입 선언·메모리가 아니라 **"무엇을 원하는지"를 적으면 엔진이 "어떻게"를 정하는** 언어라서, 문법 한 조각이 그대로 *결과 집합의 정의*가 된다.
그래서 다섯 축으로 자른다.

1. **논리적 처리 순서** — `FROM → WHERE → GROUP BY → HAVING → SELECT → DISTINCT → ORDER BY → LIMIT`.
   SQL 에서 나오는 "왜 안 되지"의 대부분이 이 순서 하나로 설명된다. 별칭을 `WHERE` 에서 못 쓰는 것, `WHERE` 와 `HAVING` 이 갈리는 것, 윈도우 함수 결과를 `WHERE` 로 못 거르는 것이 전부 같은 이유다.
   그래서 **01번이 뼈대**이고, 아래 표의 여러 주제가 01을 선행으로 건다.
2. **관계를 붙이는 형태** — 조인을 한 덩어리로 두지 않고 `CROSS`·`INNER`·`LEFT/RIGHT OUTER`·`FULL OUTER`·`SELF`·`USING/NATURAL`·`SEMI/ANTI`·`LATERAL` 형태별로 자른다. 형태마다 *짝 없는 행을 어떻게 다루는가*가 다르고, 틀리는 자리도 거기다.
3. **값의 의미론** — `NULL` 3값 논리, 암시적 캐스팅, collation, 날짜·시간. 문법은 맞는데 답이 틀리는 사고는 대개 여기서 난다.
4. **행을 바꾸는 문과 스키마** — `INSERT`/`UPDATE`/`DELETE`/upsert/`MERGE`, 그리고 제약·인덱스. 제약은 문법이 아니라 **엔진에 맡기는 불변식**이라는 관점으로 자른다.
5. **엔진이 실제로 한 일** — 트랜잭션·격리·잠금, 그리고 `EXPLAIN`. 사용자가 말한 「AST 에서 읽는」 자리가 여기다. 다만 SQL 에서 사람이 읽는 것은 파서의 AST 자체가 아니라 그 뒤의 **계획 트리(plan tree)** 이므로 주제 이름도 그렇게 잡았다.

분류 칸은 5종(`질의`/`DDL·제약`/`함수`/`트랜잭션·동시성`/`실행·최적화`)만 쓴다.
DML(`INSERT`·`UPDATE`·`DELETE`·upsert·`MERGE`)은 전용 칸이 없어 **`질의`** 로 묶었고, 집계·윈도우 함수는 절이면서 함수라 **`함수`** 로 묶되 그 평가 시점만 순서 축(31)에서 다시 다룬다.

## 주제 목록

| # | 주제 | 분류 | 무엇을 인출하게 되나 | 선행 | 기존 주제 | 방언 | 우선 |
|---|------|------|----------------------|------|-----------|------|------|
| 01 | [논리적 질의 처리 순서](01-logical-query-processing-order/) | 질의 | `FROM → WHERE → GROUP BY → HAVING → SELECT → DISTINCT → ORDER BY → LIMIT` 로 각 절이 무엇을 입력받는지 설명하고, 조건 하나를 다른 절로 옮겼을 때 결과가 어떻게 달라지는지 예측할 수 있다 | — | — | 표준 | A |
| 02 | [SELECT 목록과 열 별칭의 유효 범위](02-select-list-column-aliases/) | 질의 | 별칭을 `WHERE` 에서는 못 쓰고 `ORDER BY` 에서는 쓰는 이유를 처리 순서로 설명할 수 있다 | 01 | — | 차이 | B |
| 03 | [WHERE 와 HAVING 의 차이](03-where-vs-having/) | 질의 | 같은 조건을 `WHERE` 에 둘 때와 `HAVING` 에 둘 때 결과·비용이 어떻게 갈리는지 판단할 수 있다 | 01 | — | 차이 | A |
| 04 | [NULL 의 3값 논리](04-null-three-valued-logic/) | 함수 | `TRUE`/`FALSE`/`UNKNOWN` 으로 `AND`·`OR`·`NOT` 을 계산하고, `WHERE` 가 UNKNOWN 행을 버린다는 사실로 "사라진 행"을 설명할 수 있다 | 01 | — | 표준 | A |
| 05 | [NULL 비교 — IS NULL·IS DISTINCT FROM·NULL 안전 등호](05-null-comparison-is-distinct-from/) | 함수 | `= NULL` 이 아무것도 못 맞추는 이유를 설명하고, NULL 을 같은 값으로 보고 비교해야 할 때 무엇을 쓸지 고를 수 있다 | 04 | — | 차이 | A |
| 06 | [조건 식 — CASE·COALESCE·NULLIF·GREATEST/LEAST](06-conditional-expressions-case-coalesce/) | 함수 | 단순 CASE 와 검색 CASE 를 구분하고, NULL 대체와 0 나눗셈 회피를 식 수준에서 처리할 수 있다 | 04 | — | 차이 | B |
| 07 | [DISTINCT 와 중복 제거](07-distinct-and-duplicate-removal/) | 질의 | `DISTINCT` 가 어느 단계에서 무엇을 기준으로 지우는지 설명하고, `GROUP BY`·`DISTINCT ON` 과 언제 갈리는지 판단할 수 있다 | 01, 04 | — | 차이 | B |
| 08 | [ORDER BY — 정렬 키·NULL 위치·동률](08-order-by-null-position-stability/) | 질의 | 정렬이 불안정할 때 페이지마다 행이 섞이는 이유를 설명하고, NULL 을 앞뒤 어디에 둘지 제어할 수 있다 | 01, 04 | — | 차이 | B |
| 09 | [LIMIT·OFFSET·FETCH FIRST 와 키셋 페이지네이션](09-limit-offset-keyset-pagination/) | 질의 | 깊은 `OFFSET` 이 느린 이유와 페이지 경계에서 행이 밀리는 현상을 설명하고, 키셋 방식으로 바꿀 수 있다 | 08 | — | 차이 | B |
| 10 | [FROM 절 — 테이블 별칭·파생 테이블·VALUES 리스트](10-from-clause-aliases-derived-tables/) | 질의 | 서브쿼리를 테이블처럼 쓰는 자리와 그 별칭 규칙을 설명하고, 상수 행 목록을 조인 대상으로 만들 수 있다 | 01 | — | 차이 | B |
| 11 | [서브쿼리 — 스칼라·상관·ANY/ALL](11-subquery-scalar-correlated-any-all/) | 질의 | 스칼라 서브쿼리가 2행을 돌려주면 왜 에러인지, 상관 서브쿼리가 바깥 행마다 다시 도는 구조인지 설명할 수 있다 | 01, 10 | — | 표준 | A |
| 12 | [카티션곱과 CROSS JOIN](12-cartesian-product-cross-join/) | 질의 | 조인을 "모든 짝을 만든 뒤 조건으로 거르는 것"으로 설명하고, 조인 조건을 빠뜨렸을 때 행 수를 예측할 수 있다 | 01, 10 | — | 차이 | B |
| 13 | [INNER JOIN](13-inner-join/) | 질의 | `ON` 조건에 맞는 짝만 남는 규칙과, 한쪽에 짝이 여럿일 때 행이 불어나는 것을 예측할 수 있다 | 12 | — | 차이 | A |
| 14 | [LEFT·RIGHT OUTER JOIN](14-left-right-outer-join/) | 질의 | 짝 없는 행이 NULL 로 채워져 남는 규칙을 설명하고, LEFT 와 RIGHT 를 서로 뒤집어 쓸 수 있다 | 13 | — | 표준 | A |
| 15 | [OUTER JOIN 에서 ON 과 WHERE 의 차이](15-on-vs-where-in-outer-join/) | 질의 | 같은 조건을 `ON` 에 둘 때와 `WHERE` 에 둘 때 외부 조인이 내부 조인으로 무너지는 현상을 예측할 수 있다 | 03, 14 | — | 표준 | A |
| 16 | [FULL OUTER JOIN](16-full-outer-join/) | 질의 | 양쪽의 짝 없는 행이 모두 남는 결과를 예측하고, 지원하지 않는 엔진에서 무엇으로 대신할지 판단할 수 있다 | 01, 04, 14 | — | 차이 | B |
| 17 | [SELF JOIN](17-self-join/) | 질의 | 한 테이블에 두 별칭을 붙여 같은 테이블의 행끼리 비교하는 질의를 설계할 수 있다 | 13 | — | 표준 | C |
| 18 | [USING 과 NATURAL JOIN](18-using-and-natural-join/) | 질의 | `USING` 이 공통 열을 하나로 합치는 것과, `NATURAL` 이 이름만으로 붙어 스키마 변경에 조용히 깨지는 위험을 판단할 수 있다 | 13 | — | 표준 | C |
| 19 | [SEMI·ANTI 조인 — EXISTS·IN·NOT IN·NOT EXISTS](19-semi-anti-join/) | 질의 | "있는지만 보는" 조인을 `EXISTS`/`IN` 으로 쓰고, `NOT IN` 대상에 NULL 이 섞이면 결과가 통째로 비는 이유를 설명할 수 있다 | 05, 11, 13 | — | 표준 | A |
| 20 | [LATERAL 조인](20-lateral-join/) | 질의 | 바깥 행의 값을 참조하는 서브쿼리를 `FROM` 에 놓아 "행마다 상위 N개" 같은 질의를 쓸 수 있다 | 11, 13 | — | 차이 | B |
| 21 | [집계 함수와 COUNT 의 세 형태](21-aggregate-functions-count-forms/) | 함수 | `COUNT(*)`·`COUNT(열)`·`COUNT(DISTINCT 열)` 이 NULL 과 중복을 각각 어떻게 다루는지 설명하고 골라 쓸 수 있다 | 04 | [`19-probabilistic-counting`](../../../../data-structure/19-probabilistic-counting/) — 근사 계수는 거기, 여기선 정확 계수의 문법과 NULL 처리 | 차이 | A |
| 22 | [GROUP BY 와 비집계 열 규칙](22-group-by-nonaggregated-columns/) | 질의 | 그룹 키가 결과 행을 정의한다는 것을 설명하고, 집계되지 않은 열을 SELECT 에 둘 때 엔진이 왜 거부하는지(또는 왜 조용히 허용하는지) 판단할 수 있다 | 01, 21 | — | 차이 | A |
| 23 | [GROUPING SETS·ROLLUP·CUBE 와 GROUPING()](23-grouping-sets-rollup-cube/) | 질의 | 소계·총계를 한 질의로 뽑고, 결과의 NULL 이 "값 없음"인지 "소계 행"인지 구분할 수 있다 | 22 | [`timeseries-resolution-tiers`](../../../../systems/timeseries-resolution-tiers/) — 사전 집계 저장 전략은 거기, 여기선 질의 문법 | 차이 | B |
| 24 | [조건부 집계 — FILTER 와 CASE](24-conditional-aggregation-filter-case/) | 함수 | 한 번의 스캔으로 여러 조건의 합계를 나란히 뽑는 질의를 쓰고, `FILTER` 와 `CASE` 중 무엇을 쓸지 방언에 맞춰 고를 수 있다 | 06, 22 | — | 차이 | B |
| 25 | [조인 팬아웃 — 행 수와 집계가 어긋나는 자리](25-join-fan-out/) | 질의 | 1:N 조인 뒤 `SUM` 이 부풀려지는 현상을 예측하고, 선집계·`EXISTS`·`DISTINCT` 중 어느 처방이 맞는지 판단할 수 있다 | 14, 22 | [`data-access/jpa.md`](../../../../engineering/data-access/jpa.md) — ORM 이 SQL 을 만들어내는 비용은 거기, 여기선 SQL 자체의 행 수 계산 | 표준 | A |
| 26 | [윈도우 함수의 개념 — 집계와 무엇이 다른가](26-window-functions-vs-aggregates/) | 함수 | 그룹으로 접지 않고 행마다 값을 붙이는 계산이라는 점을 설명하고, `GROUP BY` 로 풀 수 없는 요구를 윈도우로 옮길 수 있다 | 21, 22 | — | 차이 | A |
| 27 | [PARTITION BY 와 윈도우 ORDER BY](27-partition-by-and-window-order-by/) | 함수 | 창을 나누는 축과 창 안의 순서가 결과를 어떻게 바꾸는지 예측할 수 있다 | 26 | — | 차이 | B |
| 28 | [프레임 — ROWS·RANGE·GROUPS 와 기본 프레임](28-window-frames-rows-range-groups/) | 함수 | `ORDER BY` 를 쓴 순간 적용되는 기본 프레임을 설명하고, 누적합이 동률 행에서 튀는 이유를 `ROWS`/`RANGE` 차이로 설명할 수 있다 | 27 | — | 차이 | B |
| 29 | [순위 함수 — ROW_NUMBER·RANK·DENSE_RANK·NTILE](29-ranking-functions/) | 함수 | 동률을 각각 어떻게 다루는지 구분하고, "그룹별 1위 한 행"을 뽑는 질의를 쓸 수 있다 | 27 | [`basic/24-leaderboard`](../../../../domain-modeling/basic/24-leaderboard/) · [`advanced/19-leaderboard-recount`](../../../../domain-modeling/advanced/19-leaderboard-recount/) — 랭킹 도메인 규칙은 거기, 여기선 함수의 의미 | 차이 | B |
| 30 | [오프셋·경계 함수 — LAG·LEAD·FIRST_VALUE·LAST_VALUE·NTH_VALUE](30-offset-and-boundary-functions/) | 함수 | 이전/다음 행과의 차이를 계산하고, `LAST_VALUE` 가 기대와 다르게 나오는 이유를 프레임으로 설명할 수 있다 | 28 | — | 차이 | B |
| 31 | [윈도우 함수의 평가 시점과 WINDOW 절](31-window-evaluation-timing/) | 함수 | 윈도우 결과를 `WHERE` 에서 못 거르는 이유를 처리 순서로 설명하고, 서브쿼리·CTE 로 한 겹 감싸 해결할 수 있다 | 01, 26 | — | 표준 | B |
| 32 | [CTE(WITH) — 이름 붙인 서브질의와 가시성](32-cte-with-clause/) | 질의 | CTE 의 범위와 참조 규칙을 설명하고, 중첩 서브쿼리를 CTE 로 펴서 읽히게 만들 수 있다 | 11 | — | 차이 | A |
| 33 | [재귀 CTE](33-recursive-cte/) | 질의 | 앵커 항과 재귀 항의 구조·종료 조건을 설명하고, 계층 전개와 사이클로 인한 무한 반복을 판단할 수 있다 | 32 | [`11-bfs`](../../../../algorithm/11-bfs/) · [`12-dfs`](../../../../algorithm/12-dfs/) — 탐색 알고리즘 자체는 거기, 여기선 재귀 CTE 의 문법과 종료 조건 | 차이 | B |
| 34 | [집합 연산 — UNION·INTERSECT·EXCEPT 와 ALL](34-set-operations-union-intersect-except/) | 질의 | 열 개수·타입 호환 규칙과 `ALL` 유무의 중복 제거 비용을 설명하고, 조인으로 쓸지 집합 연산으로 쓸지 고를 수 있다 | 01, 07 | — | 차이 | B |
| 35 | [타입 체계와 캐스팅 — 명시 변환·암시 변환](35-type-system-and-casting/) | 함수 | 비교·연산에서 어느 쪽 타입으로 맞춰지는지 설명하고, 암시 변환이 인덱스를 못 쓰게 만드는 자리를 예측할 수 있다 | 01 | [`data-representation`](../../../data-representation/) — 비트 수준 표현은 거기, 여기선 SQL 의 타입 규칙 | 차이 | A |
| 36 | [수치 타입과 수치 함수 — 정수 나눗셈·반올림·정밀도](36-numeric-types-and-functions/) | 함수 | 정수끼리 나눌 때 소수가 사라지는 동작, `DECIMAL` 과 부동소수의 차이, 반올림 함수의 경계 동작을 예측할 수 있다 | 35 | [`data-representation`](../../../data-representation/) — 부동소수 표현은 거기, 여기선 SQL 연산의 결과 | 차이 | B |
| 37 | [문자열 함수와 연결 연산](37-string-functions-and-concatenation/) | 함수 | 길이·부분문자열·트림·치환·대소문자 변환을 쓰고, 문자열 연결 연산자가 방언마다 다른 것을 판단할 수 있다 | 35 | — | 차이 | B |
| 38 | [패턴 매칭 — LIKE·ESCAPE·정규식](38-pattern-matching-like-regex/) | 함수 | 와일드카드와 이스케이프 규칙을 설명하고, 앞이 열린 패턴이 인덱스를 못 타는 이유를 예측할 수 있다 | 37 | [`25-string-matching`](../../../../algorithm/25-string-matching/) · [`32-inverted-index`](../../../../data-structure/32-inverted-index/) — 매칭 알고리즘·전문검색 색인은 거기, 여기선 SQL 연산자와 인덱스 사용 여부 | 차이 | B |
| 39 | [collation — 문자열 비교와 정렬의 기준](39-collation/) | 함수 | 같은 데이터가 엔진·설정에 따라 다르게 비교·정렬되는 이유를 설명하고, 대소문자 구분 여부를 의도대로 고정할 수 있다 | 37 | [`data-representation`](../../../data-representation/) — 인코딩은 거기, 여기선 비교·정렬 규칙 | 차이 | B |
| 40 | [날짜·시간 타입과 함수](40-date-time-types-and-functions/) | 함수 | 타임존이 붙은 타입과 안 붙은 타입의 차이를 설명하고, 절단·추출·간격 연산과 경계 조건(`>=`/`<`)을 안전하게 쓸 수 있다 | 35 | — | 차이 | A |
| 41 | [JSON 타입과 함수](41-json-types-and-functions/) | 함수 | 문서를 열로 펴는 연산과 경로 표현을 쓰고, JSON 열에 인덱스를 거는 방법과 한계를 판단할 수 있다 | 35 | — | 차이 | C |
| 42 | [테이블 정의와 변경 — CREATE·ALTER TABLE](42-create-alter-drop-table/) | DDL·제약 | 열 타입·NULL 허용·기본값을 정하고, 운영 중 `ALTER` 가 어떤 잠금을 부르는지 판단할 수 있다 | 35 | [`partitioning-vs-sharding`](../../../../systems/partitioning-vs-sharding/) — 분할 전략은 거기, 여기선 테이블 정의 문법 | 차이 | B |
| 43 | [기본키·UNIQUE 제약과 NULL](43-primary-key-unique-and-null/) | DDL·제약 | 기본키와 UNIQUE 의 차이를 설명하고, UNIQUE 열에 NULL 이 여러 개 들어가는 동작을 예측할 수 있다 | 04, 42 | — | 차이 | B |
| 44 | [외래키와 참조 동작 — ON DELETE·ON UPDATE](44-foreign-key-referential-actions/) | DDL·제약 | 참조 무결성이 막아 주는 것과, `CASCADE`·`SET NULL`·`RESTRICT` 가 각각 무엇을 지우는지 예측할 수 있다 | 43 | — | 차이 | B |
| 45 | [CHECK·NOT NULL·DEFAULT·생성 열·자동 증가](45-check-not-null-default-generated-columns/) | DDL·제약 | 불변식을 애플리케이션이 아니라 엔진에 맡기는 자리를 고르고, 기본값·생성 열·자동 증가 값이 언제 계산되는지 설명할 수 있다 | 42 | — | 차이 | B |
| 46 | [인덱스 정의 — 복합·부분·표현식·커버링](46-index-definition-composite-partial-expression/) | DDL·제약 | 복합 인덱스의 열 순서가 왜 중요한지 설명하고, 부분·표현식 인덱스로 좁힌 인덱스를 설계할 수 있다 | 42 | [`15-b-tree`](../../../../data-structure/15-b-tree/) — 자료구조 자체는 거기, 여기선 인덱스 정의 문법 | 차이 | B |
| 47 | [인덱스를 언제 타고 언제 안 타나](47-when-indexes-are-used/) | 실행·최적화 | 선행 열 누락·열에 함수 적용·암시 변환·낮은 선택도에서 인덱스가 버려지는 것을 예측하고, 질의를 고쳐 다시 타게 만들 수 있다 | 35, 46 | [`15-b-tree`](../../../../data-structure/15-b-tree/) — 탐색 구조는 거기, 여기선 "탈지 말지"의 판단 | 차이 | A |
| 48 | [뷰와 구체화 뷰](48-views-and-materialized-views/) | DDL·제약 | 뷰가 저장하는 것이 결과가 아니라 질의라는 점을 설명하고, 구체화 뷰의 갱신 시점과 낡음을 판단할 수 있다 | 32, 42 | [`timeseries-resolution-tiers`](../../../../systems/timeseries-resolution-tiers/) — 사전 집계 운영은 거기, 여기선 객체 정의 | 차이 | B |
| 49 | [INSERT — 다중 행·INSERT SELECT·기본값](49-insert-multi-row-and-insert-select/) | 질의 | 한 문으로 여러 행을 넣는 형태와 질의 결과를 그대로 적재하는 형태를 쓰고, 기본값·생성 열이 어떻게 채워지는지 설명할 수 있다 | 45 | — | 차이 | B |
| 50 | [UPDATE — 조인·서브쿼리를 쓰는 갱신](50-update-with-join-and-subquery/) | 질의 | 다른 테이블의 값으로 갱신하는 문을 방언에 맞게 쓰고, `WHERE` 를 빠뜨린 갱신의 범위를 예측할 수 있다 | 11, 49 | — | 차이 | B |
| 51 | [DELETE 와 TRUNCATE](51-delete-and-truncate/) | 질의 | 두 문의 롤백 가능성·트리거·자동 증가 초기화 차이를 설명하고, 대량 삭제를 나눠 도는 이유를 판단할 수 있다 | 50 | — | 차이 | B |
| 52 | [UPSERT — ON CONFLICT 와 ON DUPLICATE KEY UPDATE](52-upsert/) | 질의 | 충돌 대상이 되는 제약이 무엇인지 지목하고, "있으면 갱신 없으면 삽입"을 경쟁 조건 없이 한 문으로 쓸 수 있다 | 43, 49 | [`06-idempotency-store`](../../../../ops-patterns/06-idempotency-store/) — 멱등 처리 패턴은 거기, 여기선 문법과 충돌 대상 지정 | 차이 | A |
| 53 | [MERGE](53-merge/) | 질의 | 원본과 대상을 맞춰 삽입·갱신·삭제를 한 문으로 기술하고, upsert 로 대신할 수 있는 경계를 판단할 수 있다 | 52 | — | PG | B |
| 54 | [RETURNING 과 변경문을 품은 CTE](54-returning-and-data-modifying-cte/) | 질의 | 변경한 행을 곧바로 회수하는 문을 쓰고, 한 문 안에서 여러 테이블을 바꿀 때의 가시성을 설명할 수 있다 | 32, 49 | — | PG | C |
| 55 | [트랜잭션 경계 — COMMIT·ROLLBACK·SAVEPOINT](55-transaction-boundaries-commit-rollback-savepoint/) | 트랜잭션·동시성 | 원자성이 지켜지는 범위를 문 단위로 설명하고, 자동 커밋과 명시적 트랜잭션·부분 롤백을 구분해 쓸 수 있다 | 49 | [`07-outbox`](../../../../ops-patterns/07-outbox/) — 메시지 발행 패턴은 거기, 여기선 트랜잭션 문법 | 차이 | A |
| 56 | [격리 수준과 읽기 이상 현상·MVCC](56-isolation-levels-read-phenomena-mvcc/) | 트랜잭션·동시성 | 더티 리드·반복 불가능 읽기·팬텀을 각 수준이 어디까지 막는지 설명하고, 두 엔진의 기본 수준 차이가 코드에 미치는 영향을 판단할 수 있다 | 55 | [`engineering-axes/concurrency.md`](../../../../engineering/engineering-axes/concurrency.md) — 개념·트레이드오프는 거기, 여기선 `SET TRANSACTION` 문법과 엔진별 기본값 | 차이 | A |
| 57 | [명시적 잠금과 교착 — FOR UPDATE·SKIP LOCKED·NOWAIT](57-explicit-locking-and-deadlock/) | 트랜잭션·동시성 | 읽으면서 잠그는 문을 쓰고, 큐 소비·좌석 선점에서 `SKIP LOCKED` 가 푸는 문제와 교착이 생기는 순서를 설명할 수 있다 | 56 | [`11-distributed-lock`](../../../../ops-patterns/11-distributed-lock/) — 분산 락은 거기, 여기선 한 DB 안의 행 잠금 문법 | 차이 | B |
| 58 | [EXPLAIN 읽기 — 계획 트리의 구조](58-explain-plan-tree/) | 실행·최적화 | 계획을 트리로 읽어 어느 노드가 먼저 돌고 행 수가 어디서 불어나는지 짚을 수 있다 | 01, 13 | — | 차이 | A |
| 59 | [스캔·조인·정렬 연산자](59-scan-join-sort-operators/) | 실행·최적화 | 순차 스캔과 인덱스 스캔, 중첩 루프·해시·머지 조인, 정렬·해시 집계가 각각 언제 뽑히는지 설명할 수 있다 | 46, 58 | [`05-hashmap`](../../../../data-structure/05-hashmap/) · [`02-merge-sort`](../../../../algorithm/02-merge-sort/) — 자료구조·알고리즘 자체는 거기, 여기선 계획에 뜨는 연산자의 의미 | 차이 | B |
| 60 | [EXPLAIN ANALYZE — 추정과 실측이 어긋나는 자리](60-explain-analyze-estimates-vs-actuals/) | 실행·최적화 | 추정 행 수와 실제 행 수의 격차를 읽어 통계·선택도 문제를 짚고, 느린 질의의 병목 노드를 지목할 수 있다 | 58 | — | 차이 | B |

**60주제** — 분류별로 질의 29 · 함수 18 · DDL·제약 6 · 트랜잭션·동시성 3 · 실행·최적화 4.
우선순위는 A 21 · B 35 · C 4, 방언은 표준 10 · 차이 48 · PG 2 · MySQL 0 이다.
★ **방언 칸은 「그 주제 자신의 축」이 갈리느냐를 묻는다 — 본문에 방언 이야기가 나오느냐가 아니다.**
01(논리적 처리 순서)과 04(3값 논리)는 본문에 갈림이 나오지만 `표준`으로 둔다.
`HAVING` 에서 별칭을 쓰는 것이 PG ✗ / MySQL ✓ 로 갈리는 것은 **02·03 이 소유**하고(둘 다 `차이`),
`IS NOT DISTINCT FROM` ↔ `<=>` 가 서로를 거부하는 것은 **05 가 소유**한다(`차이`).
축 자체 — 처리 순서와 3값 논리 — 는 두 엔진에서 한 자리도 안 갈린다. **같은 갈림을 두 번 세지 않는다.**

★ **방언 칸은 실행 검증으로 열 번 정정됐다** — 처음 문서 대조만으로 채웠을 때 `표준` 16 이던 것이 **10** 로 줄었다.
`표준` → `차이` 로 바뀐 것: 03 · 12 · 13 · 26 · 27 · 29 · 30 · 43 · 47. `차이` → `PG`: 53(MySQL 에 `MERGE` 가 **키워드 단계에서** 없다 — 54 `RETURNING` 과 같은 기준).
**「문서에 둘 다 있더라」가 「같더라」가 아니다**는 것이 이 숫자가 말하는 전부다.
MySQL 전용 주제가 0인 것은 의도한 결과다 — MySQL 고유 문법(`REPLACE`·`INSERT IGNORE`·`STRAIGHT_JOIN`)은 독립 주제가 될 만큼 크지 않아 해당 주제 안의 방언 메모로 들어간다.

> ⚠️ 방언 칸의 확신도는 균일하지 않다. 아래 「방언 차이가 큰 자리」에 적은 항목은 **공식 문서에서 문장을 확인한 것**이고, 그 밖의 `차이` 표시는 두 문서의 문법 요약·목차 수준에서 다르다고 본 것이라 **3파일을 쓸 때 해당 페이지로 재확인**한다.
>
> ✅ **2026-09-21 실행 검증분 (1차)** — 두 서버에 같은 질의를 던져 확인했고, 두 엔진의 출력을 해당 주제 본문에 나란히 실었다.
> `upsert`(52) · `FULL OUTER JOIN`(16) · `별칭 유효 범위`(02) · `ORDER BY 의 NULL`(08) · `GROUP BY 비집계 열`(22) ·
> `문자열 연결`(37) · `정수 나눗셈`(36) · `NULL 안전 등호`(05).
> 이 중 **정정된 것은 `FULL OUTER JOIN` 의 우회 방법 한 건**이다(아래 표 참조) — 나머지는 표기대로였다.
>
> ✅ **2026-09-21 실행 검증분 (2차 — 조인 묶음 03 · 10 · 12 · 13 · 14 · 15)** — 같은 방식으로 확인했다.
> **새로 발견한 방언 차이 여섯 건**을 아래 표에 추가했다(`HAVING` 조건 내리기 · 파생 테이블 별칭 의무 · `VALUES` 행 생성자 ·
> `CROSS JOIN … ON` · `JOIN` 의 `ON` 누락 · `generate_series`). 그중 **세 주제가 「표준」 표기와 어긋나** 03 · 12 · 13 의 방언 칸을 `차이` 로 정정했다
> (10 은 이미 `차이` 표기였고, 새 항목 둘이 그 근거를 구체화한 것이다).
> 반대로 **14 · 15 는 표기대로 「표준」이었다** — 결과가 두 엔진에서 한 자리도 안 갈렸고, 갈린 것은 실행 계획뿐이다.
>
> ✅ **2026-09-21 실행 검증분 (3차 — 남은 43주제 전부)** — 여섯 묶음을 같은 방식으로 확인해 **60 / 60** 을 채웠다.
> 방언 칸 **일곱 건을 추가 정정**했다(26 · 27 · 29 · 30 · 43 · 47 을 `표준` → `차이`, 53 을 `차이` → `PG`).
> 각 주제 본문에 두 엔진 출력이 나란히 실려 있으므로 여기서는 **새로 드러난 사고 유형**만 적는다 — 전부 실행으로 나왔고 문서 대조로는 안 나왔던 것들이다.
>
> | 유형 | 실측 | 주제 |
> |---|---|---|
> | ★ **선언은 통과하는데 수행되지 않는다** | MySQL 의 열 뒤 `REFERENCES` 가 **제약을 아예 안 만든다**(`foreign_key_checks=1` 인데 고아 행이 들어간다) · `ON DELETE SET DEFAULT` 가 카탈로그에 저장만 된다 · `USING HASH` 가 `BTREE` 가 된다 | 44 · 46 |
> | ★ **경고 한 줄 없이 값이 바뀐다** | `ADD COLUMN … NOT NULL` 이 `0` 으로 채운다 · `INSERT IGNORE` 가 `NOT NULL` 을 **빈 문자열**로 통과시킨다 · 15자를 10자로 자른다 · `SELECT id … UNION SELECT name …` 이 통째로 문자열이 된다 | 42 · 49 · 34 |
> | ★ **같은 문이 두 엔진에서 정반대** | `TRUNCATE` 가 PG 는 롤백되고 MySQL 은 암묵 커밋 · 재귀 CTE 의 `LIMIT` 위치 · `SET a=b, b=a` 가 PG 는 교환 MySQL 은 순차(`300,10` 대 `300,300`) · `EXPLAIN ANALYZE` 가 PG 는 변경문을 **실제로 돌린다** | 51 · 33 · 50 · 60 |
> | ★ **안전장치에 난 구멍** | `sql_safe_updates=1` 이 `DELETE` 는 `ERROR 1175` 로 막는데 **`TRUNCATE` 는 통과시킨다** · `SET FOREIGN_KEY_CHECKS=0` + `TRUNCATE` 가 고아 행을 남기고 `=1` 로 되켜도 재검사하지 않는다 | 50 · 51 |
> | ★ **통설과 다른 것** | MySQL `REPEATABLE READ` 에서 **같은 트랜잭션 안의 일반 읽기와 잠금 읽기가 다른 답**을 낸다(2 대 3) — 「갭 락이 팬텀까지 막는다」는 **범위를 먼저 잠근 경우**만 말한다 | 56 |
> | ★ **문법이 없는 것과 실행 경로가 없는 것** | `ERROR 1064` 는 파서가 낱말을 모르는 것, `ERROR 1235 … doesn't yet support` / `ERROR 6037` 은 **파서는 아는데 실행 경로가 없는 것**이다. 뒤엣것은 **다음 버전에서 다시 찍을 자리**라는 뜻 — `GROUPS`·`EXCLUDE`·`IGNORE NULLS`·`QUALIFY` 넷이 그랬다 | 28 · 30 · 31 |
>
> ⚠️ **계획(`EXPLAIN`)을 근거로 쓴 주제는 제출 직전에 다시 찍었고, 실제로 움직였다.**
> 같은 서버·같은 버전·같은 데이터에서 **비용이 비슷한 두 후보가 맞붙는 지점만** 8판 중 4:4 로 갈렸다(`Bitmap Heap Scan` ↔ `Seq Scan`).
> 그래서 본문은 시간·`cost=`·`rows=` 가 아니라 **`actual rows`·`loops`·연산자 이름·`Index Cond`/`Filter`** 를 근거로 쓴다.
>
> ⚠️ **「돌려 봤다」와 「옮겨 적은 게 맞다」는 다른 검사다.** 문서의 실행 블록을 추출해 **다시 던져 대조**했더니
> 4건이 걸렸고, 넷 다 **손으로 좌우 배치한 블록 또는 그 인접 블록**이었다. 추출기는
> [`reference/tools/extract-exec-blocks.py`](../../../../../reference/tools/extract-exec-blocks.py) 에 있다.
> 이 폴더에서 파서가 잡은 실행 블록은 **1,914개**(그중 **625개가 좌우 배치** — 전부 같은 사고의 후보 자리)이고,
> **배너 없이 실행 흔적만 있는 펜스가 546개 더** 있다. 뒤엣것은 파서가 못 보는 자리라 **사람이 확인해야 한다.**
> ⚠️ 이 도구의 커버리지 검사는 **두 번 「누락 0」이라는 거짓 합격**을 냈다(인용 블록 안의 펜스 · 배너를 안 쓰는 편).
> **「누락 0」은 「전부 봤다」가 아니라 「내가 보는 방식으로는 다 봤다」는 뜻**이라는 것이 이 숫자의 교훈이다.

## 기존 주제와 겹치는 것

전수 대조 결과 **겹치는 주제는 0건**이다 — SQL 은 이 repo 에 언어로서 처음 들어오고, 기존 `cs/**` 에는 SQL 문법을 다룬 문서가 없다.
대신 **인접**해서 좁혀야 하는 자리가 **12건**이고, 모두 위 표의 「기존 주제」 칸에 경로를 적었다. 좁힌 방법은 한 줄로 같다 — **"무엇인가"는 기존 문서에 두고, 여기서는 "SQL 문법으로 어떻게 쓰고 무엇을 예측하나"만 다룬다.**

| 인접한 기존 주제 | 이 목록의 주제 | 어떻게 좁혔나 |
|---|---|---|
| [`data-structure/15-b-tree`](../../../../data-structure/15-b-tree/) | 46 · 47 | 인덱스 **자료구조**는 손대지 않는다. 46은 정의 문법, 47은 **"언제 타고 언제 안 타나"** 로만 좁혔다 |
| [`engineering/data-access/jpa.md`](../../../../engineering/data-access/jpa.md) | 25 | JPA 문서는 ORM 이 SQL 을 만들어내는 비용(N+1·숨은 SQL)을 다룬다. 25는 **SQL 자체의 행 수 계산**만 다룬다 |
| [`engineering/engineering-axes/concurrency.md`](../../../../engineering/engineering-axes/concurrency.md) | 56 | 격리 수준의 **개념과 트레이드오프**는 거기(“격리 수준만으로 lost update 는 안 막힌다”). 56은 `SET TRANSACTION` 문법과 **두 엔진의 기본값 차이**만 |
| [`ops-patterns/11-distributed-lock`](../../../../ops-patterns/11-distributed-lock/) | 57 | 분산 락은 거기. 57은 **한 DB 안의 행 잠금 문법**(`FOR UPDATE`·`SKIP LOCKED`) |
| [`ops-patterns/06-idempotency-store`](../../../../ops-patterns/06-idempotency-store/) | 52 | 멱등 처리 **패턴**은 거기. 52는 upsert **문법과 충돌 대상 지정** |
| [`ops-patterns/07-outbox`](../../../../ops-patterns/07-outbox/) | 55 | 발행 패턴은 거기. 55는 트랜잭션 경계 문법 |
| [`systems/partitioning-vs-sharding`](../../../../systems/partitioning-vs-sharding/) | 42 | 분할·샤딩 전략은 거기. 42는 테이블 정의·변경 문법 |
| [`systems/timeseries-resolution-tiers`](../../../../systems/timeseries-resolution-tiers/) | 23 · 48 | 사전 집계 **운영 전략**은 거기. 여기선 `ROLLUP` 질의 문법과 구체화 뷰 **정의** |
| [`data-structure/19-probabilistic-counting`](../../../../data-structure/19-probabilistic-counting/) | 21 | 근사 계수(HLL 류)는 거기. 21은 **정확 계수** 세 형태의 NULL·중복 처리 |
| [`data-structure/32-inverted-index`](../../../../data-structure/32-inverted-index/) · [`algorithm/25-string-matching`](../../../../algorithm/25-string-matching/) | 38 | 전문검색 색인·매칭 알고리즘은 거기. 38은 `LIKE`·정규식 **연산자**와 인덱스 사용 여부 |
| [`algorithm/11-bfs`](../../../../algorithm/11-bfs/) · [`algorithm/12-dfs`](../../../../algorithm/12-dfs/) | 33 | 그래프 탐색은 거기. 33은 재귀 CTE 의 **구조와 종료 조건** |
| [`data-structure/05-hashmap`](../../../../data-structure/05-hashmap/) · [`algorithm/02-merge-sort`](../../../../algorithm/02-merge-sort/) | 59 | 해시·머지 **알고리즘**은 거기. 59는 계획에 뜨는 **연산자 이름을 읽는 법** |
| [`domain-modeling/basic/24-leaderboard`](../../../../domain-modeling/basic/24-leaderboard/) · [`advanced/19-leaderboard-recount`](../../../../domain-modeling/advanced/19-leaderboard-recount/) | 29 | 랭킹 **도메인 규칙**은 거기. 29는 순위 함수의 동률 처리 |

## 뺀 것과 이유

- **저장 프로시저·트리거·커서**(PL/pgSQL·MySQL 저장 프로그램) — 절차형 확장이라 "SQL 문법" 축이 아니라 **사실상 다른 언어**다. 필요해지면 별도 묶음으로 잡는다.
- **권한·역할·행 수준 보안**(`GRANT`/`REVOKE`/`CREATE POLICY`) — 운영·보안 축이고 [`systems/postgres-rls`](../../../../systems/postgres-rls/) 가 이미 그 자리를 잡고 있다.
- **파티션 테이블 DDL·샤딩** — [`systems/partitioning-vs-sharding`](../../../../systems/partitioning-vs-sharding/) 와 겹친다. 42에서 정의 문법만 스친다.
- **스토리지 엔진 내부**(LSM·MergeTree·WAL·VACUUM) — [`data-structure/24-lsm-tree`](../../../../data-structure/24-lsm-tree/) · [`systems/lsm-tree`](../../../../systems/lsm-tree/) · [`systems/clickhouse-mergetree`](../../../../systems/clickhouse-mergetree/) 가 있다. 문법이 아니라 엔진 구조다.
- **복제·백업·`COPY`/`LOAD DATA`·운영 명령** — 운영 축. 문법 인출 대상이 아니다.
- **PG 전용 비스칼라 타입**(배열·범위·멀티레인지·ENUM·`hstore`) — 한쪽 방언 전용이라 표준 뼈대가 나오지 않는다. 2단계 이후 "PG 보강" 묶음 후보.
- **지리·XML·네트워크 주소·전문검색 타입** — 면적은 크지만 인출 빈도가 낮고, 필요할 때 문서를 보는 편이 낫다.
- **옵티마이저 힌트**(`USE INDEX`·`pg_hint_plan`) — 방언 편차가 너무 커서 공통 주제로 서지 않는다.
- **prepared statement·바인딩·SQL 인젝션** — 드라이버·언어 바인딩 축이다. 보안은 [`foundations/security`](../../../security/) 가 맡는다.
- **집합 연산의 `CORRESPONDING`·`TABLE` 문 같은 주변 문법** — 실무 인출 빈도가 낮아 34 안의 한 줄로 접었다.

## 방언 차이가 큰 자리

아래는 **공식 문서에서 문장을 확인한 것만** 적는다. 3파일에서는 이 항목마다 "PG 는 …, MySQL 은 …" 를 나란히 놓는다.

| 자리 | PostgreSQL 18 | MySQL 8.4 | 주제 |
|---|---|---|---|
| **GROUP BY 비집계 열** | 함수 종속을 **GROUP BY 에 그 표의 기본키가 포함된 경우에만** 인정 — `UNIQUE NOT NULL` 열도, **조인 건너편 열도 거부**한다(2026-09-21 18.6 실행 확인). `ANY_VALUE()` 는 **PG 16+ 에도 있다**(릴리스 노트 확인) | `ONLY_FULL_GROUP_BY` 가 **기본 sql_mode 에 포함**(기본 ON). 종속성 탐지가 **더 넓다** — `UNIQUE NOT NULL` 열과 **조인 건너편**까지 인정(실행 확인). 거부 시 `ERROR 1055`(GROUP BY 있음) / `ERROR 1140`(집계만) | 22 |
| 문자열 비교·정렬 | 기본 collation 은 **결정적**이라 `=` 가 대소문자·악센트를 가린다. 비구분 비교는 `deterministic = false` ICU collation 필요 | 기본이 `utf8mb4` / **`utf8mb4_0900_ai_ci`** — 악센트·대소문자 **무시** | 39 |
| upsert | `INSERT … ON CONFLICT <대상> DO NOTHING \| DO UPDATE SET …` — **충돌 대상을 지목**한다 | `INSERT … AS new ON DUPLICATE KEY UPDATE c = new.a` — 대상을 못 고르고 **아무 유니크 키든** 걸린다. 영향 행 수는 삽입 1 / 갱신 2 / 무변화 0 | 52 |
| MERGE | **PG 15 부터** 지원(`WHEN MATCHED`/`WHEN NOT MATCHED`) | **없다.** 8.4 DML 문 목록에 MERGE 가 없다 | 53 |
| 행 제한 | `LIMIT`/`OFFSET` + 표준형 `FETCH {FIRST\|NEXT} n ROWS {ONLY \| WITH TIES}` | `LIMIT` 만. **`FETCH FIRST` 문법이 없다** | 09 |
| ORDER BY 의 NULL | `NULLS FIRST\|LAST` 지정 가능. 기본은 ASC=LAST / DESC=FIRST (NULL 을 **큰 값**으로 취급) | 지정 문법이 **없다**. ASC 에서 NULL 이 앞 (NULL 을 **작은 값**으로 취급) | 08 |
| 집합 연산 | `UNION`/`INTERSECT`/`EXCEPT` 모두 오래전부터 | `INTERSECT`/`EXCEPT` 는 **8.0.31 부터** 추가됐다 | 34 |
| FULL OUTER JOIN | 있다 | **없다.** `FULL OUTER JOIN`·`FULL JOIN` 둘 다 `ERROR 1064` 문법 오류다(2026-09-21 8.4.10 실행 확인). 우회는 **`UNION` 이 아니라 `UNION ALL` + 반조인**이다 — 단순 `UNION` 은 값이 같은 행을 접어 결과가 줄어든다(실행 확인) | 16 |
| **소계·총계** | `GROUPING SETS`·`ROLLUP`·`CUBE` 셋 다. `WITH ROLLUP` 은 **`syntax error at or near "WITH"`** | `WITH ROLLUP` 과 `ROLLUP(...)` 둘 다 된다(`GROUPING()` 도). **`GROUPING SETS` 는 `ERROR 1064`**(문법 없음). ※ **`CUBE` 는 `ERROR 3889` — "Secondary engine operation failed. No secondary engine defined"** 이다(2026-09-21 8.4.10 실행 확인). **파싱은 되고 실행 경로가 없는 것**이라 「문서 부재」 판단을 실측으로 대체했다 | 23 |
| **조건부 집계** | `agg(...) FILTER (WHERE …)` | FILTER 절이 **집계 함수 문법에 없다** → **`ERROR 1064`**(2026-09-21 8.4.10 실행 확인). `CASE` 로 쓴다 — `FILTER (WHERE c)` ≡ 인자 자리의 `CASE WHEN c THEN … END`(`ELSE` 금지) | 24 |
| 중복 제거 | `SELECT DISTINCT ON (expr)` (맨 앞 ORDER BY 와 일치해야) | **없다** | 07 |
| 윈도우 프레임 | `ROWS`/`RANGE`/**`GROUPS`**(PG 11+) + `EXCLUDE` | `ROWS`/`RANGE` 만 | 28 |
| CTE 부가 문법 | `MATERIALIZED`/`NOT MATERIALIZED`(PG 12+), `SEARCH`/`CYCLE`(PG 14+) | 둘 다 문서에 없다 | 32 · 33 |
| 문자열 연결 | `\|\|` 가 연결 | **`\|\|` 는 기본이 논리 OR**(비표준 동의어, deprecated). `PIPES_AS_CONCAT` 모드에서만 연결이 되고 그 모드는 기본 sql_mode 에 없다 → `CONCAT()` 을 쓴다 | 37 |
| 정수 나눗셈 | `/` 는 정수끼리면 **0 방향으로 잘린다**(`5/2 → 2`, `-5/2 → -2`) | `/` 는 **DECIMAL** 을 돌려준다(`3/5 → 0.6000` — 자릿수는 `피제수 스케일 + div_precision_increment`, 기본 4. 2026-09-21 8.4.10 실행 확인으로 `0.60` 표기를 정정했다). 정수 나눗셈은 `DIV` | 36 |
| 별칭 유효 범위 | `ORDER BY`·`GROUP BY` 에서만 쓸 수 있고 **`WHERE`·`HAVING` 은 안 된다** | `GROUP BY`·`ORDER BY`·**`HAVING` 에서 된다**. `WHERE` 만 안 된다 | 02 |
| 격리 수준 기본값 | **Read Committed** | InnoDB **REPEATABLE READ** (둘 다 `FOR UPDATE` 의 `NOWAIT`·`SKIP LOCKED` 는 지원) | 56 · 57 |
| CHECK 제약 | 처음부터 강제 | **8.0.16 부터** 실제로 강제된다. 그 전 버전은 **파싱하고 무시**했다. `[NOT] ENFORCED` 옵션이 있다 | 45 |
| BOOLEAN | 진짜 1바이트 `boolean` 타입 | `BOOL`/`BOOLEAN` 은 **`TINYINT(1)` 의 동의어**, `TRUE`/`FALSE` 는 1/0 별칭 | 35 |
| 자동 증가 | `GENERATED {ALWAYS\|BY DEFAULT} AS IDENTITY` (`serial` 은 "표기상의 편의"일 뿐 진짜 타입이 아니다) | `AUTO_INCREMENT` 열 속성 — 테이블당 하나, NOT NULL + 인덱스 필수, `LAST_INSERT_ID()` | 45 |
| RETURNING | INSERT/UPDATE/DELETE/MERGE 에 있다(PG 18 은 `OLD`/`NEW` 별칭까지) | **없다** | 54 |
| 구체화 뷰 | `CREATE MATERIALIZED VIEW` + `REFRESH MATERIALIZED VIEW` | 뷰 챕터에 **일반 뷰만** 있다. ※ 이것도 "미지원" 문장이 아니라 **문서 부재**로 판단한 것 | 48 |
| EXPLAIN | `EXPLAIN (ANALYZE, BUFFERS, FORMAT …)` — PG 18 은 ANALYZE 시 BUFFERS 가 **자동 포함** | `EXPLAIN [FORMAT={TRADITIONAL\|JSON\|TREE}]`, `EXPLAIN ANALYZE` 는 **8.0.18 부터**·`FORMAT=TREE` 만 허용 | 58 · 60 |
| LATERAL | **9.3 부터**, 함수 앞에서는 키워드 생략 가능. **조인 종류 제약은 PG 도 같다** — `RIGHT JOIN LATERAL` 에서 왼쪽을 참조하면 `DETAIL: The combining JOIN type must be INNER or LEFT for a LATERAL reference.`(2026-09-21 18.6 실행 확인) | **8.0.14 부터**, `FROM` 안에서 INNER/CROSS/LEFT(및 뒤집은 RIGHT) 에만 | 20 |
| **`HAVING` 의 그룹 키 조건** | 옵티마이저가 **스캔 필터로 내린다** — `WHERE` 버전과 계획이 한 글자도 같다(`EXPLAIN ANALYZE` 확인) | **안 내린다** — `Aggregate using temporary table` 로 그룹을 다 만든 뒤 거른다 | 03 |
| **파생 테이블 별칭** | 별칭 **없어도 통과**한다(18.6 실행 확인) | **필수** — `ERROR 1248 Every derived table must have its own alias` | 10 |
| **`VALUES` 행 생성자** | `VALUES (1,'x'),(2,'y')` — `ROW(...)` 는 **구문 오류** | `VALUES ROW(1,'x'),ROW(2,'y')` — 괄호만 쓰면 **`ERROR 1064`**. 서로를 정확히 거부한다 | 10 · 12 |
| **`CROSS JOIN … ON`** | **구문 오류** — `CROSS` 는 조건을 받지 않는다 | **통과한다** — 내부 조인이 된다(`JOIN`·`INNER JOIN`·`CROSS JOIN` 이 문법적 동의어) | 12 |
| **`JOIN` 에 `ON` 누락** | **구문 오류** — `ON`/`USING` 이 의무다 | **통과한다** — 카티션곱이 조용히 나온다 | 13 |
| **`COUNT(DISTINCT 열1, 열2)`** | **`COUNT(DISTINCT (a, b))`** — 괄호로 묶은 행 값 하나. `COUNT(DISTINCT a, b)` 는 `function count(integer, integer) does not exist`. `emp` 에서 **4** | **`COUNT(DISTINCT a, b)`** — 인자 나열. 괄호로 묶으면 `ERROR 1241 Operand should contain 1 column(s)`. **한 칸이라도 NULL 인 행은 안 센다** → `emp` 에서 **2**. 서로의 문법을 정확히 거부하고 **값도 다르다** | 21 |
| **`ROLLUP` 없는 `GROUPING()`** | **전부 0 을 돌려준다**(접은 열이 없다는 뜻) | **`ERROR 1111 Invalid use of group function`** — 매뉴얼이 `GROUPING()` 을 `WITH ROLLUP` 질의의 함수로 정의한다 | 23 |
| **`generate_series`** | 있다 — `CROSS JOIN generate_series(1,3)` 으로 수 목록을 만든다 | **없다** — `ERROR 1064`. `UNION ALL` 목록이나 재귀 CTE 로 대신한다 | 12 · 33 |

## 버전 기준

- **PostgreSQL 18** — `postgresql.org/docs/current/` 를 기준으로 했고, 페이지 표기는 18.6 이다.
- **MySQL 8.4 LTS** — `dev.mysql.com/doc/refman/8.4/en/`.
- ★ **MySQL 매뉴얼 페이지에는 기능 도입 버전이 거의 적혀 있지 않다.** 위의 도입 버전(8.0.14 LATERAL · 8.0.16 CHECK 강제·`FORMAT=TREE` · 8.0.18 `EXPLAIN ANALYZE` · 8.0.31 INTERSECT/EXCEPT)은 **릴리스 노트**에서 확인한 것이다. 3파일에서도 같은 규칙을 지킨다 — **매뉴얼에 없으면 릴리스 노트로 접지하고, 둘 다 없으면 버전을 적지 않는다.**
- PostgreSQL 쪽 도입 버전은 릴리스 노트로 확인했다 — 9.3 LATERAL · 11 `GROUPS` 프레임 · 12 CTE `MATERIALIZED` · 14 `SEARCH`/`CYCLE` · 15 `MERGE`.
- **표준 SQL(ISO/IEC 9075)** — 공개 요약 수준에서만 참조했다. **조항 번호는 확인하지 못했으므로 이 목록과 3파일 어디에도 적지 않는다.** "표준형"이라는 표현은 PG 문서가 표준으로 소개한 문법(`FETCH FIRST` 등)에 한해 쓴다.
- 방언 칸의 `표준` 은 "ISO 표준에 있다"가 아니라 **"PG·MySQL 두 문서에서 같은 모양으로 확인됐다"** 는 뜻이다.
- 2단계 3파일에서는 버전 의존 기능마다 `PG 15+` / `MySQL 8.0.31+` 형태로 표기한다.
