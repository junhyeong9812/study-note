# database/01-relational-model-and-algebra — 정답

## 정답

### 1. 데이터 종속과 데이터 독립성 (Codd 1970 §1.1~1.2, CMU L1)

- **데이터 종속**: 앱 코드가 데이터의 저장 표현(순서, 인덱스, 접근 경로)에 기대는 것. Codd는 순서 종속·인덱스 종속·접근 경로 종속을 들었다. 그중 첫째가 순서 종속이다(§1.2.1).
- 파일 직접 저장이면 앱이 파일을 열고, 자르고, 순서대로 돌며 찾는다. 저장 방식을 바꾸면 모든 앱을 고쳐야 한다.
- **데이터 독립성**: 앱은 릴레이션(순서 없는 튜플 집합)과 선언형 질의만 본다. 저장 방식·인덱스·실행 전략은 DBMS가 정한다. 그래서 인덱스를 추가하거나 저장 배치를 바꿔도 앱 코드는 그대로다.

### 2. 릴레이션 vs SQL 테이블

| | Codd 릴레이션 | SQL 테이블 |
|---|---|---|
| 중복 행 | 없음(집합, "All rows are distinct") | 허용(백) |
| 행 순서 | 의미 없음 | 없음, `ORDER BY`로만 생김 |
| NULL | 원 모델에 없음 | 허용 |

- 대수의 π는 집합 연산이라 결과의 중복을 없앤다. SQL `SELECT`의 기본은 `ALL`이라 중복을 남긴다. π와 같은 것은 `SELECT DISTINCT`다.

### 3. 연산자 트리와 선택 내리기

```text
  (가)   σ b_id=102          (나)      ⋈
            |                        /   \
            ⋈                       R    σ b_id=102
          /   \                             |
         R     S                            S
```

- 결과는 같다. 선택 조건이 S의 속성만 쓰면 조인 아래로 내려도 된다.
- S가 크고 조건에 맞는 행이 적으면 (나)가 빠르다. 조인에 들어가는 행이 크게 준다(CMU L1 Observation: 10억 행 중 1행).
- SQL은 결과만 선언한다. 어떤 트리로 계산할지는 **옵티마이저**가 고른다. 로컬 재현에서도 PostgreSQL이 `WHERE i.qty >= 2`를 조인 아래 `Seq Scan … Filter`로 내렸다.

### 4. PostgreSQL `UPDATE` 뒤 순서

- 처음: 1, 2, 3, 4, 5. 갱신 뒤: **1, 3, 4, 5, 2**(예시, PostgreSQL 17.11).
- PostgreSQL `UPDATE`는 행의 새 버전을 다른 위치에 쓴다. id=2의 새 버전 ctid가 `(0,6)`이 됐다.
- 순차 스캔은 물리 위치 순으로 읽으므로 2가 맨 뒤로 갔다. 문서도 정렬하지 않으면 순서는 계획과 디스크 위치에 달렸고 기대면 안 된다고 적는다(7.5).

### 5. MySQL 커버링 인덱스와 순서

- InnoDB 보조 인덱스 항목에는 PK 값이 들어 있다. `SELECT id`는 `name` 인덱스만 읽어도 답이 나온다(커버링 인덱스 스캔). 결과가 `name` 순서로 나온다.
- `SELECT id, cat`은 `cat`이 보조 인덱스에 없어 그 인덱스만으로는 끝낼 수 없다. 로컬 재현에서는 옵티마이저가 클러스터드 인덱스(PK 순서) 스캔을 골랐다. 보조 인덱스를 읽고 PK로 행을 찾아가는 계획도 가능하므로, 어느 쪽인지는 계획이 정한다(MySQL 8.4 17.6.2.1).
- 로컬 재현(예시, MySQL 8.4.10): 전자는 2, 1, 3, 4, 5(`'changed'`가 `'n1'`보다 앞), 후자는 1~5였다. `EXPLAIN FORMAT=TREE`가 `Covering index scan on item using k_name`을 보였다.

### 6. 페이지 중복·누락

- 원인: `created_at`이 같은 행들의 상대 순서가 정해지지 않았다. 쿼리마다, `LIMIT`·`OFFSET` 값마다 달라질 수 있다(MySQL 8.4 10.2.1.19).
- 수정

```sql
SELECT id, title FROM post
ORDER BY created_at DESC, id DESC      -- 유일 키로 동률을 깬다
LIMIT 20 OFFSET 20;

-- 더 나은 방식: 키셋
SELECT id, title FROM post
WHERE (created_at, id) < (:last_created_at, :last_id)
ORDER BY created_at DESC, id DESC
LIMIT 20;
```

- 이 키셋은 `created_at`이 `NOT NULL`일 때 성립한다. NULL이 있으면 행 비교가 NULL이 되어 경계를 넘지 못하므로, NULL 구간을 따로 조건으로 다뤄야 한다(PostgreSQL 17 9.25.5 Row Constructor Comparison).

- 키셋은 `OFFSET`처럼 앞 행을 세며 버리지 않는다. 그 사이 새 행이 끼어도 경계가 밀리지 않는다.

### 7. `UNION` vs `UNION ALL`, NULL

- `UNION`은 기본이 DISTINCT다. 중복 행을 없앤다. `UNION ALL`은 그대로 붙인다(PostgreSQL SELECT "Description").
- 양쪽에 NULL이 있으면 `UNION`은 NULL 행을 **하나** 남긴다. 중복 제거에서는 NULL끼리 같은 것으로 본다(예시, PostgreSQL 17.11 로컬 재현).
- `=` 비교에서는 `NULL = NULL`이 참이 아니라 NULL(알 수 없음)이다(04번). 같은 NULL이 연산에 따라 "같음"과 "알 수 없음"으로 다르게 취급된다.

### 8. 키 없는 중복 행

- 이유: 두 행의 모든 값이 같다. 값으로 쓰는 조건은 둘을 구별할 수 없다. 관계 모델은 "모든 행은 서로 다르다"를 전제하지만 SQL은 키 없이 강제하지 않는다.
- 복구: 물리 위치나 임시 순번으로 하나만 고른다.

```sql
-- PostgreSQL: ctid로 하나만 남긴다
DELETE FROM dup d
WHERE d.ctid <> (SELECT min(ctid) FROM dup x
                 WHERE x.a IS NOT DISTINCT FROM d.a      -- `=`이면 NULL이 든 중복을 못 잡는다
                   AND x.b IS NOT DISTINCT FROM d.b);
```

- 재발 방지: 기본 키(또는 유일 제약)를 건다. 적재는 키 기준 upsert로 바꾼다(02번, 18번).
