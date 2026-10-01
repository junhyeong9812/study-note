# database/01-relational-model-and-algebra — 관계 모델과 관계 대수: 표는 순서 없는 집합이다 — 정리 (힌트)

## 해결하는 문제

데이터를 파일에 직접 쓰면, 프로그램이 **저장 방식**을 알아야 읽을 수 있다.

```text
  artists.csv                         앱 코드
  "Wu-Tang Clan",1992,"USA"    <---   파일을 열고, 쉼표로 자르고, 줄마다 돌며 찾는다
  "GZA",1990,"USA"                    정렬 순서·파일 위치·인덱스 모양을 코드가 안다
```

- 이 방식에서는 저장 방식이 바뀌면(파일 분할, 인덱스 추가, 정렬 변경) **모든 앱 코드**를 고쳐야 한다(CMU 15-445 L1 "Flat File Strawman", "Early DBMSs").
- 무결성(같은 가수를 두 번 다르게 적음), 동시 쓰기, 장애 중 쓰기도 앱이 전부 떠안는다.

쉬운 예: 엑셀 시트를 여러 사람이 각자 "3번째 줄이 김 과장"이라고 외워 두고 쓰는 상황이다. 누가 정렬 한 번 하면 모두의 기억이 틀린다.

똑같은 구조다.\
Codd(1970)는 이것을 **데이터 종속(data dependence)**이라 불렀다. 그중 첫째가 **순서 종속(ordering dependence)**이다. 해법은 두 가지다.

1. 데이터를 **릴레이션**(순서 없는 튜플 집합)이라는 단순한 구조로만 보여 준다.
2. 앱은 "무엇을 원하는지"만 말하고, "어떻게 찾을지"는 DBMS가 정한다.

- *데이터 독립성(data independence)*: 저장 표현이 바뀌어도 앱 코드는 그대로인 성질(Codd 1970 §1.1, CMU L1 §4).

실무 예:
- `ORDER BY` 없이 `SELECT … LIMIT 20`으로 목록을 만든 화면이 있다. 어느 날 인덱스가 하나 추가되자 목록 순서가 바뀐다. 코드는 한 줄도 안 바뀌었다.
- 이것은 버그가 아니라 관계 모델의 약속 그대로다. **순서는 약속한 적이 없다.**

## 동작·원리

### 1. 릴레이션 = 이름 붙은 표, 그러나 순서가 없다

```text
  릴레이션 artist(name, year, country)          <- 스키마: 이름 + 속성 목록
  ┌───────────────┬──────┬─────────┐
  │ name          │ year │ country │           <- 속성(attribute) 3개 = 차수(degree) 3
  ├───────────────┼──────┼─────────┤
  │ Wu-Tang Clan  │ 1992 │ USA     │  <- 튜플(tuple) 하나
  │ GZA           │ 1990 │ USA     │
  │ Notorious BIG │ 1992 │ USA     │
  └───────────────┴──────┴─────────┘
    year의 도메인 = 정수                        튜플 3개 = 카디널리티 3
```

- *릴레이션(relation)*: 같은 속성들을 가진 튜플의 집합. 표(table)와 같은 뜻으로 쓴다.
- *튜플(tuple)*: 표의 한 행. 속성마다 값이 하나씩 있다.
- *도메인(domain)*: 한 속성이 가질 수 있는 값의 집합(예: 정수, 날짜).
- *스키마(schema)*: 릴레이션의 이름과 속성 목록. "데이터의 구조"에 대한 설명이다.

Codd 1970(§1.3)이 적은 릴레이션의 성질은 이렇다.

```text
  (1) 행 하나 = n-튜플 하나
  (2) 행의 순서는 의미가 없다          <- 이 노트의 핵심
  (3) 모든 행은 서로 다르다            <- 집합(set)
  (4) 열의 순서는 의미가 있다(도메인 순서) — 단, Codd는 이어서 열을 이름으로 부르는 "도메인 비순서" 형태를 권한다
  (5) 각 열의 의미는 해당 도메인 이름을 열 이름으로 붙여 일부 전달한다
```

### 2. 수학의 집합 vs SQL 테이블 — 집합이 아니라 백(bag)

| | 관계 모델(Codd) | SQL 테이블 |
|---|---|---|
| 중복 행 | 없음 (집합) | **허용** (백·다중집합) |
| 행 순서 | 없음 | 없음 (`ORDER BY`로만 생김) |
| 빈 값 | 원래 모델에 없음 | `NULL` 허용 |

- *백(bag, multiset)*: 같은 원소가 여러 번 들어갈 수 있는 집합.
- CMU L1도 "릴레이션은 순서 없는 집합… 중복 원소가 있을 수 있다"고 적어, 실제 DBMS가 백 의미론을 쓴다는 점을 인정한다.
- SQL은 중복 제거를 **명시할 때만** 한다. `SELECT DISTINCT`, `UNION`(기본 DISTINCT), `INTERSECT`, `EXCEPT`가 그렇다. `GROUP BY`도 같은 값의 행을 그룹 하나로 합친다. `SELECT`의 기본은 `ALL`이다(PostgreSQL 17 SELECT 레퍼런스 "Description", "GROUP BY Clause").

### 3. 관계 대수 — 릴레이션을 받아 릴레이션을 내는 연산자

```text
  연산        기호          뜻                                   SQL
  선택        σ_p(R)        조건 p를 만족하는 튜플만               WHERE p
  사영        π_A,B(R)      속성 A, B만 남김                       SELECT A, B   (집합이면 중복 제거)
  합집합      R ∪ S         둘 중 하나에 있는 튜플                  UNION
  교집합      R ∩ S         둘 다에 있는 튜플                       INTERSECT
  차집합      R − S         R에만 있는 튜플                         EXCEPT
  곱          R × S         모든 조합                              CROSS JOIN
  조인        R ⋈ S         같은 이름 속성 값이 같은 조합             JOIN … USING(…) / NATURAL JOIN
  개명        ρ_S(R)        이름 바꾸기                            AS
```

- 합·교·차는 두 입력의 속성이 같아야 한다(CMU L1 §6, "same attributes").
- 조인은 기본 연산의 조합이다: `R ⋈_θ S = σ_θ(R × S)`.
- **닫힘(closure)**: 모든 연산의 출력이 다시 릴레이션이다. 그래서 연산자를 트리로 쌓을 수 있다.

### 4. 연산자 트리와 동치 변환 — 옵티마이저가 설 자리

```text
  질의: "S에서 b_id = 102인 것과 R을 조인"

  (가) σ_{b_id=102}(R ⋈ S)          (나) R ⋈ σ_{b_id=102}(S)

          σ b_id=102                         ⋈
             |                             /   \
             ⋈                            R    σ b_id=102
           /   \                                  |
          R     S                                 S

  결과는 같다. S가 10억 행이고 b_id=102가 1행이면 (나)가 압도적으로 빠르다(CMU L1 §6 Observation).
```

- 관계 대수는 **절차**(어떤 순서로 계산할지)를 담는다.
- SQL은 **결과**만 선언한다. 어떤 트리로 계산할지는 옵티마이저가 고른다.
  - *선언형(declarative)*: 무엇을 원하는지만 말한다.
  - *절차형(procedural)*: 어떻게 구할지를 말한다(CMU L1 §5).
- 실제 실행 계획도 같은 모양의 트리다(예시, PostgreSQL 17.11, 로컬 재현).

```text
  EXPLAIN (COSTS OFF)
  SELECT o.customer, i.sku FROM ord o JOIN ord_item i ON i.order_id = o.id WHERE i.qty >= 2;

   Hash Join                            <- ⋈
     Hash Cond: (i.order_id = o.id)
     ->  Seq Scan on ord_item i         <- σ_{qty>=2}(ord_item): 선택을 조인 아래로 내렸다
           Filter: (qty >= 2)
     ->  Hash
           ->  Seq Scan on ord o
```

### 5. 순서가 없다는 것의 실제 — 결과 순서는 계획과 저장 위치가 정한다

PostgreSQL 17 문서(7.5 Sorting Rows): 정렬을 고르지 않으면 행은 **정해지지 않은 순서**로 나온다. 실제 순서는 스캔·조인 계획과 디스크 위치에 달렸고, 기대면 안 된다.

```text
  (예시, PostgreSQL 17.11, 로컬 재현) 같은 SELECT id FROM item; 인데 순서가 바뀐다

  INSERT 1..5 직후             UPDATE item SET name='changed' WHERE id=2 직후
  id  ctid                      id  ctid
  1   (0,1)                     1   (0,1)
  2   (0,2)                     3   (0,3)
  3   (0,3)                     4   (0,4)
  4   (0,4)                     5   (0,5)
  5   (0,5)                     2   (0,6)    <- 새 버전이 페이지 끝에 써졌다
```

- PostgreSQL의 `UPDATE`는 행의 새 버전을 새 위치에 쓴다(MVCC, [16-mvcc](../16-mvcc/2-summary.md)). 순차 스캔은 물리 위치 순서로 읽으므로 2가 맨 뒤로 갔다.
  - *ctid*: 행의 물리 위치(페이지 번호, 페이지 안 슬롯 번호).
- 계획이 바뀌어도 순서가 바뀐다.

```text
  (예시, MySQL 8.4.10 InnoDB, 로컬 재현) 테이블 item(id PK, name, cat, KEY k_name(name))

  SELECT id FROM item;          SELECT id, cat FROM item;
  -> Covering index scan         (클러스터드 인덱스 = PK 순서로 읽음)
     on item using k_name
  2   ('changed')                1
  1   ('n1')                     2
  3                              3
  4                              4
  5                              5
```

- InnoDB 보조 인덱스에는 PK 값이 함께 들어 있다. 그래서 `SELECT id`는 더 작은 `k_name` 인덱스만 읽고 끝낸다(커버링). 결과는 `name` 순서로 나온다.
- 열 하나(`cat`)를 더 달라고 하자 계획이 PK 순서 스캔으로 바뀌고, 결과 순서도 바뀌었다.
- PostgreSQL의 `synchronize_seqscans`(기본 켜짐)는 큰 테이블의 순차 스캔을 **중간부터** 시작해 한 바퀴 돌 수 있게 한다. 문서가 직접 "ORDER BY 없는 쿼리의 행 순서가 예측 불가하게 바뀔 수 있다"고 적는다(PostgreSQL 17 19.13.1).

## 쓰이는 자료구조·알고리즘

- **집합 연산 = 중복 제거 문제**: `UNION`·`INTERSECT`·`EXCEPT`·`DISTINCT`는 "같은 튜플인가"를 가려야 한다. 해시 테이블에 넣어 보거나([data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)), 정렬한 뒤 이웃끼리 비교한다([algorithm/02-merge-sort](../../algorithm/02-merge-sort/2-summary.md)). 로컬 재현의 `UNION` 계획은 `Append` → `HashAggregate`였다(해시로 중복 제거).
- **연산자 트리**: 관계 대수식은 트리(또는 DAG)다. 실행 계획도 트리이고, 각 노드는 자식이 내준 튜플을 받아 가공한다(실행 모델은 [54-query-execution-models](../54-query-execution-models/2-summary.md)).
- **동치 규칙(rewrite rules)**: `σ_p(R ⋈ S) = R ⋈ σ_p(S)`(p가 S 속성만 쓸 때), `R ⋈ S = S ⋈ R` 같은 규칙으로 트리를 바꿔 가며 싼 것을 찾는다([12-query-optimizer-and-explain](../12-query-optimizer-and-explain/2-summary.md)).
- **집합·관계의 수학**: 릴레이션은 도메인들의 데카르트 곱의 부분집합이다(Codd 1970 §1.3). 수학 선행 노트 `math/03-sets-relations-orders`는 미작성이다([math/README](../../math/README.md)).

## 적용 — 풀어나가는 법

### 1. SQL을 대수로 읽기

```sql
-- π_{customer}( σ_{total >= 70}(ord) )   — π는 중복을 없애므로 DISTINCT
SELECT DISTINCT customer FROM ord WHERE total >= 70;

-- π_{customer, sku}( ord ⋈_{ord.id = ord_item.order_id} ord_item )
SELECT DISTINCT o.customer, i.sku FROM ord o JOIN ord_item i ON i.order_id = o.id;

-- R − S : 블랙리스트가 아닌 고객 (NULL 함정은 04번)
SELECT customer FROM ord EXCEPT SELECT customer FROM blacklist;
```

- `SELECT`는 π가 아니다. 대수의 π는 집합이라 중복을 없애지만, SQL `SELECT`는 백이라 없애지 않는다. π와 같은 것은 `SELECT DISTINCT`다.

### 2. 순서가 필요하면 반드시 `ORDER BY` — 그리고 유일하게

```sql
-- 나쁨: 순서 미지정
SELECT id, title FROM post LIMIT 20;

-- 부족: created_at이 같은 행끼리는 순서가 정해지지 않는다
SELECT id, title FROM post ORDER BY created_at DESC LIMIT 20;

-- 좋음: 동률을 깨는 유일 키를 마지막에 둔다
SELECT id, title FROM post ORDER BY created_at DESC, id DESC LIMIT 20;
```

- MySQL 8.4 문서(10.2.1.19 LIMIT Query Optimization): `ORDER BY` 열 값이 같은 행들은 서버가 **아무 순서로나** 돌려줄 수 있고, 실행 계획에 따라 달라질 수 있다. `LIMIT` 유무만으로도 순서가 달라질 수 있다.
- 키셋 페이지네이션(`WHERE (created_at, id) < (?, ?)`)도 유일한 정렬 키가 있어야 성립한다. 문법 세부는 [sql/09 LIMIT·OFFSET·키셋](../../../languages/sql/syntax/09-limit-offset-keyset-pagination/2-summary.md).

### 3. `UNION` vs `UNION ALL`을 의도대로

```text
  (예시, PostgreSQL 17.11)
  SELECT count(*) FROM (SELECT 'lee' UNION ALL SELECT 'lee') t;   -> 2
  SELECT count(*) FROM (SELECT 'lee' UNION     SELECT 'lee') t;   -> 1
```

- 중복을 없애려는 뜻이 없으면 `UNION ALL`을 쓴다. `UNION`은 중복 제거 단계(해시·정렬)가 추가된다.
- 중복 제거에서는 `NULL`끼리 **같은 것으로** 본다. 로컬 재현에서 `ord.customer ∪ blacklist.customer`에 NULL 행이 하나만 남았다. `=` 비교에서는 NULL끼리 같지 않다(04번). 규칙이 연산마다 다르다.

### 4. 진단 — "왜 순서가 바뀌었나"

```sql
-- PostgreSQL: 어떤 계획으로 읽었나, 행이 어디 있나
EXPLAIN (ANALYZE, BUFFERS) SELECT id FROM item LIMIT 20;
SELECT ctid, id FROM item LIMIT 20;
-- MySQL
EXPLAIN FORMAT=TREE SELECT id FROM item LIMIT 20;
```

- 계획 노드가 `Seq Scan` ↔ `Index Scan`(PG), `Covering index scan` ↔ `Table scan`(MySQL)으로 바뀌었으면 순서가 바뀐 이유다. 고치는 곳은 계획이 아니라 쿼리의 `ORDER BY`다.

## 장애 시나리오와 대처

### 1. `ORDER BY` 없는 목록이 배포 뒤 뒤섞임 (⚠ 커리큘럼)

- **현상**: 관리자 화면 목록, 배치 처리 순서, "첫 번째 행" 선택 결과가 어느 날 바뀐다. 코드 변경은 없었다.
- **보이는 형태**: 에러는 없다. 테스트 스냅샷 불일치, "어제랑 순서가 다르다"는 문의, `LIMIT 1`로 고른 대표 행이 바뀌어 생긴 데이터 오류.
- **원인**: 결과 순서는 실행 계획과 물리 배치의 부산물이다. 인덱스 추가, 통계 갱신, `UPDATE`로 행 이동, VACUUM, 동기화된 순차 스캔, 버전 업그레이드 중 무엇이든 순서를 바꾼다.
- **대처**
  - 순서가 의미 있는 모든 쿼리에 `ORDER BY`를 넣는다. 마지막 키는 유일해야 한다.
  - "대표 행 하나"도 기준을 명시한다(`ORDER BY created_at, id LIMIT 1`).
  - 테스트에서 결과 비교는 정렬 후 하거나 집합으로 비교한다.

### 2. 페이지를 넘기면 같은 행이 또 나오거나 빠진다

- **현상**: `ORDER BY created_at LIMIT 20 OFFSET 20`으로 넘기는데 1쪽의 행이 2쪽에 또 나온다. 어떤 행은 어느 쪽에도 없다.
- **보이는 형태**: 에러 없음. 사용자 신고, 내보내기 파일의 중복·누락.
- **원인**: `created_at`이 같은 행들의 상대 순서가 쿼리마다 다를 수 있다. `LIMIT` 값이 달라지면 계획도 달라질 수 있다(MySQL 8.4 10.2.1.19).
- **대처**: `ORDER BY created_at, id`처럼 유일 키로 동률을 깬다. 큰 목록은 키셋 페이지네이션으로 바꾼다.

### 3. `UNION`이 행을 삼킨다

- **현상**: 두 기간의 거래를 `UNION`으로 합쳤더니 건수가 합보다 적다.
- **보이는 형태**: 에러 없음. 합계 불일치.
- **원인**: `UNION`은 기본이 `DISTINCT`다. 금액·날짜가 우연히 같은 거래가 하나로 합쳐졌다. 반대로 중복 제거가 목적이 아닌데 `UNION`을 쓰면 해시·정렬 비용만 는다.
- **대처**: 기본은 `UNION ALL`. 중복 제거가 필요하면 무엇을 같은 행으로 볼지(키) 먼저 정한다.

### 4. 키 없는 테이블의 똑같은 행 — 하나만 지울 수 없다

- **현상**: 적재 오류로 같은 행이 두 번 들어갔다. 하나만 지우려고 조건을 걸었는데 둘 다 지워진다.
- **보이는 형태**: `DELETE 2`(예시, PostgreSQL 17.11: `dup(a, b)`에 `(1,'x')` 두 행, `DELETE … WHERE a=1 AND b='x'`).
- **원인**: 관계 모델에서는 모든 튜플이 달라야 한다. SQL은 이를 강제하지 않는다. 값으로 구분할 수 없는 두 행은 값으로 지목할 수도 없다.
- **대처**
  - 모든 테이블에 기본 키를 둔다(02번).
  - 이미 생긴 중복은 물리 위치(PostgreSQL `ctid`)나 임시 순번으로 하나만 골라 지운다. 그 뒤 유일 제약을 건다.

## 핵심 문장

- 관계 모델은 데이터를 순서 없는 튜플 집합(릴레이션)으로만 보여 주고, 저장 방식은 DBMS에 맡긴다. 이것이 데이터 독립성이다.
- 관계 대수의 연산(σ·π·∪·∩·−·×·⋈)은 릴레이션을 받아 릴레이션을 내므로 트리로 쌓을 수 있다. 실행 계획이 바로 그 트리다.
- SQL은 결과만 선언하고, 같은 결과를 내는 여러 트리 중 무엇을 쓸지는 옵티마이저가 고른다.
- SQL 테이블은 집합이 아니라 백이다. 중복 제거는 `DISTINCT`·`UNION`·`GROUP BY` 등으로 명시할 때만 일어난다.
- 결과 순서는 `ORDER BY`로만 보장되고, 동률은 유일 키로 깨야 한다. 그 밖의 순서는 계획과 물리 배치의 우연이다.

## 관련 주제·근거

- 선행: `math/03-sets-relations-orders` — 미작성, [math/README](../../math/README.md)
- 후속
  - [02-keys-and-constraints](../02-keys-and-constraints/2-summary.md) — 튜플을 구별하는 키, 무결성
  - [04-sql-joins-and-aggregation](../04-sql-joins-and-aggregation/2-summary.md) — 조인·집계·NULL 3치 논리
  - [36-data-models-document-graph](../36-data-models-document-graph/2-summary.md) — 관계 외의 데이터 모델
  - [11-join-algorithms](../11-join-algorithms/2-summary.md) · [12-query-optimizer-and-explain](../12-query-optimizer-and-explain/2-summary.md) · [16-mvcc](../16-mvcc/2-summary.md)
  - [54-query-execution-models](../54-query-execution-models/2-summary.md)
- 문법 세부(languages/sql)
  - [sql/01 논리 처리 순서](../../../languages/sql/syntax/01-logical-query-processing-order/2-summary.md) · [sql/08 ORDER BY·NULL 위치·안정성](../../../languages/sql/syntax/08-order-by-null-position-stability/2-summary.md) · [sql/34 집합 연산](../../../languages/sql/syntax/34-set-operations-union-intersect-except/2-summary.md)
- 교재·논문
  - E. F. Codd, "A Relational Model of Data for Large Shared Data Banks", CACM 13(6), 1970 — §1.1 데이터 독립성, §1.2.1 순서 종속, §1.3 릴레이션의 다섯 성질
  - CMU 15-445/645 Fall 2024 Lecture #01 "Relational Model & Algebra" 노트 — flat file 문제, 데이터 모델, σ·π·∪·∩·−·×·⋈, 선언형 vs 절차형 <https://15445.courses.cs.cmu.edu/fall2024/notes/01-relationalmodel.pdf>
  - Kleppmann, 『Designing Data-Intensive Applications』 1판 2장 — 관계 모델의 목표(구현 세부를 인터페이스 뒤로 숨김), 선언형 질의
- 공식 문서
  - PostgreSQL 17 7.5 Sorting Rows(정렬 안 하면 순서 미지정) <https://www.postgresql.org/docs/17/queries-order.html>
  - PostgreSQL 17 SELECT "Description"(처리 순서, `ALL`이 기본, 집합 연산은 기본 DISTINCT) <https://www.postgresql.org/docs/17/sql-select.html>
  - PostgreSQL 17 19.13.1 `synchronize_seqscans` <https://www.postgresql.org/docs/17/runtime-config-compatible.html>
  - MySQL 8.4 10.2.1.19 LIMIT Query Optimization(동률 행 순서 비결정) <https://dev.mysql.com/doc/refman/8.4/en/limit-optimization.html>
- 로컬 재현(PostgreSQL 17.11, MySQL 8.4.10): PG `UPDATE` 뒤 순차 스캔 순서·ctid 변화, MySQL 커버링 인덱스 스캔 vs PK 스캔의 순서 차이, PG 조인 계획 트리, `UNION`/`UNION ALL` 건수와 NULL 중복 제거, 키 없는 중복 행 `DELETE 2`
