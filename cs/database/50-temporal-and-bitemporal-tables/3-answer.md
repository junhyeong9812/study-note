# database/50-temporal-and-bitemporal-tables — 정답

## 정답

### 1. 두 시간축

| | 유효 시간(valid / application / actual) | 기록 시간(transaction / system / record) |
|---|---|---|
| 뜻 | 현실에서 그 사실이 참이던 기간 | DB가 그 사실을 "현재 값"으로 알던 기간 |
| 누가 넣나 | 사용자·앱 | DB(트랜잭션 시각) |
| 과거로 고치기 | 가능(소급 정정, 미래 발효 예약도 가능) | 불가. 닫고 새로 열기만 한다 |

- 유효 시간만 있으면: "3/1에 시스템이 알던 2/20 주소는?"에 답할 수 없다. 정정이 덮어썼다.
- 기록 시간만 있으면: "2/20에 실제로 어디 살았나?"에 답할 수 없다. 이사한 날(2/15)이 아니라 입력한 날(3/10)만 안다.

### 2. 소급 정정 그림

```text
   city | valid              | recorded
   서울 | [1/1, ∞)           | [1/10, 3/10)      ← 정정 전의 믿음 (닫힘)
   서울 | [1/1, 2/15)        | [3/10, ∞)         ← 정정 후
   부산 | [2/15, ∞)          | [3/10, ∞)
```

- 지금 아는 대로(`valid @> 2/20 AND recorded @> now()`) → **부산**.
- 3/1에 알던 대로(`valid @> 2/20 AND recorded @> 3/1`) → **서울**.
- 로컬 재현(PostgreSQL 17.11)에서 두 질의가 각각 부산, 서울을 돌려줬다.

### 3. 반열린 구간

- `[1/1, 3/1)`과 `[3/1, ∞)`는 맞닿지만 겹치지 않는다. 1/1부터는 어느 시각이든 정확히 한 행이 유효하다.
- SQL:2011은 closed-open 모델을 쓴다. PostgreSQL 범위 생성자의 두 인자 형태와 `daterange` 정규형도 `[)`다. 로컬 재현: `[1/1,3/1) && [3/1,∞)` = false.
- 닫힌 구간 `[from, to]`에 끝 = 다음 시작이면 경계 시각에 두 행이 모두 유효하다.
- "끝 = 다음 시작 − 1초"로 저장하면 23:59:59.5 같은 초 미만 시각에 유효한 행이 없다.
- 조회는 `from <= t AND t < to`(PG `@>`)로 한다. `BETWEEN`은 양끝을 포함하므로 쓰지 않는다.

### 4. SQL:2011 두 종류와 제품 지원

- application-time 테이블
  - `PERIOD FOR 이름(시작, 끝)`으로 기간을 정하고, 사용자가 값을 넣는다.
  - `UPDATE … FOR PORTION OF p FROM a TO b`는 그 구간에만 효과를 준다. 걸친 행은 앞·가운데·뒤 최대 3행으로 쪼개고 가운데만 고친다.
- system-versioned 테이블
  - `PERIOD FOR SYSTEM_TIME` + `WITH SYSTEM VERSIONING`.
  - 시작·끝은 DB가 트랜잭션 타임스탬프로 넣고, 사용자는 못 바꾼다.
  - UPDATE·DELETE가 옛 행을 역사 행으로 남긴다.
  - `FOR SYSTEM_TIME AS OF t`는 그 시각에 현재였던 행을 돌려준다. 이 절이 없으면 현재 행만 본다.
- 둘 다 가진 테이블이 바이템포럴이다(Kulkarni·Michels 2012).
- 제품 지원

| | application-time | system-versioned |
|---|---|---|
| PostgreSQL 17 | 없음(D.2 T181). 범위 타입 + `EXCLUDE`로 대신 | 없음(T180). 트리거 + 이력 테이블 |
| PostgreSQL 18 | `WITHOUT OVERLAPS` PK/UNIQUE, `PERIOD` FK 추가. T181 전체는 여전히 미지원 목록 | 없음 |
| MySQL 8.4 | 없음 | 없음(`WITH SYSTEM VERSIONING` → 1064 구문 오류, 로컬 재현) |

### 5. PostgreSQL 17 겹침 제약

```sql
CREATE EXTENSION IF NOT EXISTS btree_gist;
CREATE TABLE addr(
  cust_id int NOT NULL, city text NOT NULL, valid tstzrange NOT NULL,
  EXCLUDE USING gist (cust_id WITH =, valid WITH &&)
);
```

- `btree_gist`는 정수 `=`를 GiST 인덱스에 넣기 위해 필요하다. `&&`(겹침)는 범위 타입의 GiST 연산자다.
- 맞닿은 `[1/1,3/1)`과 `[3/1,∞)`는 `&&`가 false라서 허용된다. 로컬 재현: `[2/15, 4/1)` 대전 행은 `conflicting key value violates exclusion constraint`로 거부되었다.
- 바이템포럴: `EXCLUDE USING gist (cust_id WITH =, valid WITH &&, recorded WITH &&)`. "같은 기록 시점 + 같은 유효 시점"에 두 행을 금지한다.
- PostgreSQL 18이면 `PRIMARY KEY (cust_id, valid WITHOUT OVERLAPS)`가 같은 일을 한다. 단 18의 `WITHOUT OVERLAPS`는 빈 범위(`empty`)를 거부한다. 17의 `EXCLUDE`는 빈 범위를 받아 준다(18 CREATE TABLE: "Empty ranges/multiranges are not permitted").

### 6. MySQL 검사 후 삽입 경쟁

- 로컬 재현(MySQL 8.4.10): 두 세션이 각자 겹침 검사에서 `0`을 보고 둘 다 INSERT했다. 결과로 `[3/1, 9/30)`와 `[6/1, 12/31)`이 같은 상품에 공존했다.
- 원인
  - 검사와 삽입이 원자적이지 않다.
  - InnoDB REPEATABLE READ의 일반 `SELECT`는 잠그지 않는 일관 읽기다. 그래서 서로의 미커밋 삽입을 보지 못하고, 서로를 막지도 않는다.
  - MySQL에는 제외 제약이 없다.
- 고침: 부모 행을 `SELECT id FROM item WHERE id = 7 FOR UPDATE`로 먼저 잠가 같은 상품의 쓰기를 직렬화한다. 그다음 검사하고 삽입한다. 로컬 재현에서 두 번째 세션은 첫 세션 커밋까지 기다린 뒤 `1`을 보았다(앱이 거부하면 된다).
- 기존 겹침 찾기

```sql
SELECT a.item_id, a.valid_from, b.valid_from FROM price a JOIN price b
  ON a.item_id = b.item_id AND a.valid_from < b.valid_from AND b.valid_from < a.valid_to;
```

### 7. 트리거 이력과 `now()`

- `now()`는 트랜잭션 시작 시각이라 트랜잭션 동안 변하지 않는다(PostgreSQL 17 9.9.5).
- 두 번째 UPDATE에서 첫 UPDATE가 만든 중간 버전이 이력으로 간다. 그 기간은 `tstzrange(t, t)` = **empty**다. 로컬 재현: `기획 | empty`.
- 버그가 아니다. 커밋 전 중간 상태는 다른 누구도 본 적 없는 상태다. 그래서 어떤 AS OF 질의에도 나오지 않는 것이 맞다. SQL:2011도 트랜잭션 타임스탬프가 트랜잭션 동안 고정되기를 요구한다.
- 원치 않으면 트리거에서 `isempty` 이력은 건너뛴다.
- 주의: 먼저 시작해 늦게 커밋한 트랜잭션은 커밋 순서와 다른 시작 시각을 기록한다. 그 트랜잭션이 나중에 커밋된 행을 고치면 `now()`가 행의 시작보다 일러 `range lower bound must be less than or equal to range upper bound` 오류가 난다(로컬 재현). 예시 트리거는 이 경우를 따로 처리해야 한다.

### 8. 과거 리포트 재현 실패

- 원인 1: 유효 시간만 있고, 소급 정정을 **덮어쓰기**로 반영했다. 2월에 쓰던 값이 사라졌다.
- 원인 2: 기록 시간은 있지만, 리포트 쿼리가 `recorded @> now()`(지금 아는 것)로 돌았다.
- 방법
  - 정정은 기록 기간을 닫고 새 행을 연다.
  - 제출한 리포트에 기준 시각(knownAt)을 함께 저장한다. 재현할 때 `recorded @> knownAt`으로 조회한다.
  - "재발행(그때 기준)"과 "재정산(지금 기준)"을 기능으로 나눈다.

### 9. 축 고르기

| 대상 | 필요한 축 | 이유 |
|---|---|---|
| 요율표 | 유효 시간 | "주문일에 유효한 요율"이 핵심. 미래 발효 예약도 유효 시간 |
| 감사 로그 | 기록 시간 | "언제 무엇으로 바뀌었나". 과거 조작 금지 |
| 급여 소급 인상 | 바이템포럴 | 2/15부터 유효(현실) + 3/15에 앎(기록). 2/25 명세서 재현과 재정산이 모두 필요 |

- 비용
  - 행 수가 늘어난다(정정마다 닫고 연다).
  - 모든 조회에 시간 조건 둘이 붙는다(빠뜨리면 중복 행).
  - 정정 로직(쪼개기·닫기)이 복잡하다.
  - 겹침 제약·인덱스(GiST)가 필요하다.
- 그래서 필요한 축만 둔다.
