# database/50-temporal-and-bitemporal-tables — 시간 테이블: 유효 시간과 기록 시간 — 정리 (힌트)

## 해결하는 문제

보통 테이블은 **지금** 값 하나만 가진다. `UPDATE`는 옛 값을 덮어쓴다.

```text
  1/10  INSERT  고객 1, 주소 서울
  3/10  UPDATE  고객 1, 주소 부산        ← 서울은 사라졌다

  질문 A: "2월 20일에 고객 1은 어디 살았나?"            → 모른다 (이사한 날을 기록하지 않았다)
  질문 B: "3월 1일에 발송한 고지서에는 어느 주소를 썼나?"  → 모른다 (그때 시스템이 알던 값이 없다)
```

두 질문은 다른 질문이다.
- A는 **현실**의 시간을 묻는다. 언제부터 언제까지 그 사실이 참이었나.
- B는 **시스템의 앎**의 시간을 묻는다. 언제부터 언제까지 DB가 그렇게 믿었나.

쉬운 예: 일기장과 정정 기사다.
- 2월 10일 일기에 "아이스크림 1,000원"이라고 썼다.
- 3월 15일에 가게가 "사실 2월부터 1,100원이었다"고 정정했다.
- 일기(그때 안 값)도, 정정(지금 아는 값)도 지우면 안 된다. 질문에 따라 답이 다르다.

똑같은 구조다.\
사실의 시간축과 앎의 시간축을 둘 다 기록하면 두 질문에 모두 답할 수 있다.

실무 예:
- 급여가 2/15부터 올랐다는 통보가 3/15에 온다. 2/25 급여 명세서를 "그때 계산한 그대로" 재현해야 한다(Fowler "Bitemporal History"의 Sally 예).
- 보험·세금·요율표처럼 소급 정정이 잦은 도메인.
- 감사(audit): "이 값이 언제 누구의 입력으로 바뀌었나".

## 동작·원리

### 1. 두 시간축

```text
  용어 (SQL:2011 / Snodgrass)      Fowler 용어     누가 정하나            무엇을 뜻하나
  valid time (application time)   actual time     사용자(앱)가 넣는다     그 사실이 현실에서 참이던 기간
  transaction time (system time)  record time     DB가 자동으로 넣는다    DB가 그 사실을 알고 있던 기간
```

- *유효 시간(valid time)*: 현실에서 사실이 참이던 기간이다. 과거로도, 미래로도 쓸 수 있다(예: 다음 달 발효 요금).
- *기록 시간(transaction time)*: DB에 그 행이 "현재 값"으로 있었던 기간이다. 현재 트랜잭션 시각에 시작하며, 과거로 고칠 수 없다.
- *바이템포럴(bitemporal)*: 두 시간을 모두 가진 테이블이다. Fowler는 valid/transaction이라는 이름이 헷갈린다며 actual/record를 쓴다.

### 2. 한 사실의 일생 — 소급 정정

```text
  고객 1의 주소. 1/10에 "1/1부터 서울"을 기록. 3/10에 "사실 2/15에 부산으로 이사"라는 정정이 도착.

  기록 시간 ↑
            │
   3/10 이후 │ [서울 1/1 ──── 2/15) [부산 2/15 ─────────────→
            │
   1/10~3/10 │ [서울 1/1 ──────────────────────────────────→
            │
            └──────┬──────────┬──────────┬──────────────→ 유효 시간
                  1/1       2/15       3/1

  "2/20에 어디 살았나?"
    지금 아는 것으로        (기록 = now,  유효 = 2/20)  → 부산
    3/1에 시스템이 알던 것  (기록 = 3/1,  유효 = 2/20)  → 서울
```

- 정정은 행을 **덮어쓰지 않는다**. 옛 행의 기록 시간을 3/10에서 닫는다. 그리고 새 행 둘(서울 1/1~2/15, 부산 2/15~)을 3/10부터 연다.
- 그래서 "3/1 기준 리포트"를 언제든 다시 뽑을 수 있다.

로컬 재현(예시, PostgreSQL 17.11):

```text
   city |          valid          |                      recorded
  ------+-------------------------+-----------------------------------------------------
   서울 | [2026-01-01,)           | ["2026-01-10 09:00:00+09","2026-03-10 14:00:00+09")
   서울 | [2026-01-01,2026-02-15) | ["2026-03-10 14:00:00+09",)
   부산 | [2026-02-15,)           | ["2026-03-10 14:00:00+09",)

  valid @> '2026-02-20' AND recorded @> now()                    → 부산
  valid @> '2026-02-20' AND recorded @> '2026-03-01 00:00+09'    → 서울
```

### 3. 기간은 반열린 구간 `[시작, 끝)`

```text
  [1/1, 3/1)   서울       3/1 자정은 포함 안 함
  [3/1, ∞)     부산       3/1 자정부터 포함
  → 두 기간은 맞닿지만 겹치지 않는다
```

- SQL:2011은 기간에 *closed-open* 모델을 쓴다(Kulkarni·Michels 2012). 시작은 포함, 끝은 제외다.
- PostgreSQL 범위 타입도 인자 두 개짜리 생성자가 `[)`를 만들고, `daterange` 같은 이산 범위는 `[)`로 정규화한다(PostgreSQL 17 8.17.6·8.17.7). 로컬 재현에서 `tstzrange('2026-01-01','2026-03-01') && tstzrange('2026-03-01',NULL)`은 false였다. `&&`는 "겹친다"는 연산자다.
- 닫힌 구간 `[시작, 끝]`으로 저장하면 경계 시각에 두 행이 모두 유효해진다. 그러면 "끝 = 다음 시작 − 1초" 같은 계산이 필요하다.

### 4. SQL:2011의 문법과 제품 지원

```sql
-- SQL:2011 표준 문법 (Kulkarni·Michels 2012의 예) — PostgreSQL 17, MySQL 8.4 모두 지원하지 않는다
CREATE TABLE Emp(
  ENo INTEGER, EStart DATE, EEnd DATE, EDept INTEGER,
  PERIOD FOR EPeriod (EStart, EEnd),                               -- application-time
  Sys_start TIMESTAMP(12) GENERATED ALWAYS AS ROW START,
  Sys_end   TIMESTAMP(12) GENERATED ALWAYS AS ROW END,
  PERIOD FOR SYSTEM_TIME (Sys_start, Sys_end),                     -- system-time
  PRIMARY KEY (ENo, EPeriod WITHOUT OVERLAPS)                      -- 기간 겹침 금지 키
) WITH SYSTEM VERSIONING;

UPDATE Emp FOR PORTION OF EPeriod FROM DATE '2011-02-03' TO DATE '2011-09-10'
   SET EDept = 4 WHERE ENo = 22217;                                -- 기간 일부만 수정 → 행이 최대 3개로 쪼개진다
SELECT * FROM Emp FOR SYSTEM_TIME AS OF TIMESTAMP '2011-01-02 00:00:00';  -- 그때 DB가 알던 행
```

- application-time 테이블: 사용자가 기간 값을 넣고 고친다. `FOR PORTION OF`로 기간 일부만 바꾸면, DBMS가 겹친 행을 앞·가운데·뒤로 쪼갠다.
- system-versioned 테이블
  - `UPDATE`·`DELETE`가 옛 행을 자동으로 역사 행으로 남긴다.
  - 사용자는 시스템 기간을 바꿀 수 없다.
  - `FOR SYSTEM_TIME` 없는 조회는 현재 행만 본다.
  - 시작 시각은 **트랜잭션 타임스탬프**다. 표준은 그 값이 트랜잭션 동안 고정되기를 요구한다.
- 제품 지원(버전 한정)

| | application-time (`WITHOUT OVERLAPS`·`PERIOD` FK) | system-versioned (`WITH SYSTEM VERSIONING`) |
|---|---|---|
| PostgreSQL 17 | 없음(부록 D.2: T181 미지원). 대신 범위 타입 + `EXCLUDE` 제약 | 없음(T180 미지원). 트리거 + 이력 테이블로 흉내 |
| PostgreSQL 18 | `PRIMARY KEY`/`UNIQUE (… , col WITHOUT OVERLAPS)`, `FOREIGN KEY (…, PERIOD col)` 추가(18 릴리스 노트). 기간은 범위 타입 컬럼이다. 18 문서 부록 D.2에도 T181은 여전히 미지원으로 남아 있다(`PERIOD FOR` 등 표준 전체는 아님) | 없음(18 부록 D.2: T180 미지원) |
| MySQL 8.4 | 없음. 겹침 금지는 락 + 검사로 직접 | 없음. 로컬 재현: `WITH SYSTEM VERSIONING` → `ERROR 1064 (42000)` 구문 오류 |

- PostgreSQL 18의 `UNIQUE (id, valid_at WITHOUT OVERLAPS)`는 내부적으로 `EXCLUDE USING GIST (id WITH =, valid_at WITH &&)`처럼 동작한다(PostgreSQL 18 CREATE TABLE 문서). 단 빈 범위(`empty`)는 거부한다(같은 문서). PostgreSQL 17에서는 `EXCLUDE`를 직접 쓴다.

### 5. PostgreSQL 17 — 기간 겹침 제약

```sql
CREATE EXTENSION IF NOT EXISTS btree_gist;          -- 정수 '=' 를 GiST 인덱스에 넣기 위해
CREATE TABLE addr(
  cust_id int NOT NULL,
  city    text NOT NULL,
  valid   tstzrange NOT NULL,
  EXCLUDE USING gist (cust_id WITH =, valid WITH &&)   -- 같은 고객의 기간이 겹치면 거부
);
INSERT INTO addr VALUES (1,'서울', tstzrange('2026-01-01','2026-03-01'));
INSERT INTO addr VALUES (1,'부산', tstzrange('2026-03-01', NULL));      -- 맞닿음: 허용
INSERT INTO addr VALUES (1,'대전', tstzrange('2026-02-15','2026-04-01'));
-- ERROR:  conflicting key value violates exclusion constraint "addr_cust_id_valid_excl"   (로컬 재현)
```

- *제외 제약(exclusion constraint)*: "어떤 두 행을 지정한 연산자로 비교했을 때, 모두 참이 되면 안 된다"는 제약이다. 연산자가 전부 `=`이면 UNIQUE와 같다. `&&`를 섞으면 기간 겹침 금지가 된다(PostgreSQL 17 CREATE TABLE `EXCLUDE`).
- 바이템포럴 테이블에서는 `(cust_id WITH =, valid WITH &&, recorded WITH &&)`로 건다. 같은 기록 시점에 같은 유효 시점을 가진 두 행을 막는다. 로컬 재현에서 "기록 중인 부산 [2/15,∞)"와 겹치는 대전 행이 거부되었다.

### 6. 시스템 시간 흉내 — 트리거 + 이력 테이블

```sql
-- PostgreSQL 17: UPDATE/DELETE 직전에 옛 행을 이력 테이블에 복사
CREATE TABLE emp (id int PRIMARY KEY, dept text NOT NULL,
                  sys_period tstzrange NOT NULL DEFAULT tstzrange(now(), NULL));
CREATE TABLE emp_history (LIKE emp);
CREATE FUNCTION emp_versioning() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  INSERT INTO emp_history VALUES (OLD.id, OLD.dept, tstzrange(lower(OLD.sys_period), now()));
  IF TG_OP = 'UPDATE' THEN NEW.sys_period := tstzrange(now(), NULL); RETURN NEW; END IF;
  RETURN OLD;
END $$;
CREATE TRIGGER emp_ver BEFORE UPDATE OR DELETE ON emp
  FOR EACH ROW EXECUTE FUNCTION emp_versioning();
```

- `now()`는 **현재 트랜잭션의 시작 시각**이다(PostgreSQL 17 9.9.5). SQL:2011의 "트랜잭션 동안 고정된 타임스탬프"와 같은 성질이다.
- 그래서 한 트랜잭션 안에서 같은 행을 두 번 바꾸면, 가운데 버전의 기간이 `[t, t)`, 즉 **빈 구간**이 된다. 로컬 재현: 이력에 `기획 | empty`가 남았다. 어떤 AS OF 질의에도 나오지 않는다. 커밋되기 전의 중간 상태는 "DB가 안 적이 없다"는 뜻이니 올바른 결과다.

## 쓰이는 자료구조·알고리즘

- **구간 질의 = 구간 트리의 문제**: "시점 t를 포함하는 기간", "이 기간과 겹치는 기간"을 빨리 찾아야 한다. 메모리에서는 구간 트리가 이 질의를 푼다. [data-structure/30-interval-tree](../../data-structure/30-interval-tree/2-summary.md)
- **GiST 인덱스**: PostgreSQL은 범위 타입의 `&&`·`@>`를 GiST로 색인한다. 각 노드가 "아래 범위들을 모두 덮는 범위"를 들고 있어 겹칠 수 없는 가지를 건너뛴다. 제외 제약도 이 인덱스로 검사한다. 로컬 재현에서 `valid @> date '2026-02-20' AND recorded @> now()`가 제외 제약의 GiST 인덱스로 `Index Scan`되었다.
- **B+Tree + 범위 조건**: MySQL처럼 GiST가 없으면 `(item_id, valid_from)` 복합 인덱스와 `valid_from < :end AND :start < valid_to` 조건으로 찾는다. 겹침 조건 두 개 중 하나만 인덱스 범위로 쓴다.
- **추가 전용 로그(append-only)에 가까운 구조**: 기록 시간 쪽은 "닫고 새로 연다"만 한다. 옛 행의 값은 고치지 않고, 기록 기간의 끝만 닫는다(이 한 칸은 UPDATE다). 완전한 추가 전용이 필요하면 변경 이벤트만 쌓고 기간은 읽을 때 계산한다. 이벤트 소싱·감사 로그와 같은 구조다.

## 적용 — 풀어나가는 법

### 1. 먼저 어떤 질문에 답해야 하는지 고른다

```text
  "지금 값만"                                   → 보통 테이블
  "그 날짜에 유효하던 값" (요율표, 가격표)          → 유효 시간만 (application-time)
  "누가 언제 바꿨나", "그때 DB에 뭐가 있었나"       → 기록 시간만 (system-versioned / 감사 로그)
  "그때 알던 기준으로 과거 리포트 재현" + 소급 정정  → 바이템포럴
```

- 두 축은 비용이 크다. 행이 늘고, 모든 조회에 시간 조건이 붙고, 정정 로직이 복잡해진다. 필요한 축만 둔다.

### 2. 질의 네 종류

```sql
-- 현재 사실 (지금 아는 것, 지금 유효한 것)
SELECT city FROM cust_addr WHERE cust_id = 1 AND valid @> current_date AND recorded @> now();
-- 과거 사실을 지금 아는 대로
SELECT city FROM cust_addr WHERE cust_id = 1 AND valid @> date '2026-02-20' AND recorded @> now();
-- 과거 사실을 그때 알던 대로 (리포트 재현)
SELECT city FROM cust_addr WHERE cust_id = 1 AND valid @> date '2026-02-20'
                                         AND recorded @> timestamptz '2026-03-01 00:00+09';
-- 이력 전체 (감사)
SELECT * FROM cust_addr WHERE cust_id = 1 ORDER BY lower(recorded), lower(valid);
```

- 조회마다 시간 조건 둘을 빠뜨리지 않게 뷰를 둔다(예: `cust_addr_current`).

### 3. MySQL 8.4 — 겹침 금지를 직접 지킨다

```sql
-- 부모 행을 먼저 잠가 같은 item의 기간 쓰기를 직렬화한다
START TRANSACTION;
SELECT id FROM item WHERE id = 7 FOR UPDATE;
SELECT count(*) FROM price
 WHERE item_id = 7 AND valid_from < :new_to AND :new_from < valid_to;   -- 0이 아니면 거부
INSERT INTO price (item_id, amount, valid_from, valid_to) VALUES (7, :amt, :new_from, :new_to);
COMMIT;
```

- 부모 행 잠금 없이 "검사 후 삽입"만 하면 두 트랜잭션이 동시에 0을 보고 둘 다 넣는다(장애 시나리오 3).

### 4. 앱 코드 쪽

```java
// 조회 API는 두 시각을 명시적으로 받는다 — 기본값을 숨기지 않는다
record AsOf(LocalDate validAt, Instant knownAt) {
    static AsOf now(Clock c) { return new AsOf(LocalDate.now(c), c.instant()); }
}
Optional<String> cityOf(long custId, AsOf at);   // WHERE valid @> ? AND recorded @> ?
```

- 도메인 모델 쪽(가격 이력, `asOf` 커서)은 [domain-modeling/advanced/10-price-history](../../domain-modeling/advanced/10-price-history/2-summary.md)에서 다룬다.

## 장애 시나리오와 대처

### 1. UPDATE로 덮어써 "그때 시스템이 알던 값"을 잃음

- **현상**: 세무·감사 요청으로 "3월 1일 발송 고지서의 주소"를 묻는데 답할 수 없다.
- **보이는 형태**: 오류는 없다. 테이블에 현재 값 한 줄만 있다. `updated_at`은 마지막 변경 시각만 준다.
- **원인**: 기록 시간 축이 없다. `UPDATE`가 옛 값을 지운다.
- **대처**
  - 필요한 테이블에 이력 테이블과 트리거(PostgreSQL 17), 또는 CDC·감사 로그를 둔다.
  - 이미 잃은 과거는 복구 못 한다. 백업·WAL에서 부분 복원하는 것은 비싸다. 그래서 **요구가 확인되는 시점에 바로** 켠다.
  - 발송 시점의 값을 발송 레코드에 스냅숏으로 함께 남기는 것도 방법이다.

### 2. 소급 정정 뒤 과거 리포트를 재현하지 못함

- **현상**: 2월 매출 리포트를 다시 뽑았더니 2월에 제출한 숫자와 다르다.
- **보이는 형태**: 같은 쿼리, 다른 결과. 차이를 설명할 행이 없다.
- **원인**
  - 유효 시간만 있고 정정을 **덮어쓰기**로 반영했다.
  - 또는 리포트 쿼리가 `recorded @> now()`(지금 아는 것)로 돌았다.
- **대처**
  - 정정은 기록 시간을 닫고 새 행을 추가한다(동작·원리 2).
  - 제출한 리포트에는 "기록 기준 시각(knownAt)"을 함께 저장한다. 재현할 때 그 시각으로 조회한다.
  - 도메인에서는 "재발행(그때 기준)"과 "재정산(지금 기준)"을 다른 기능으로 나눈다.

### 3. 기간 겹침 제약이 없어 같은 시점에 유효한 행이 둘

- **현상**: 같은 상품의 가격 조회가 가끔 두 행을 돌려준다. `LIMIT 1`이 둘 중 아무거나 골라 금액이 흔들린다. 또는 앱 코드가 `IncorrectResultSizeDataAccessException`처럼 "하나를 기대했는데 둘"이라는 오류를 던진다.
- **보이는 형태** (로컬 재현, MySQL 8.4.10): 두 세션이 각자 겹침 검사에서 `0`을 본 뒤 둘 다 INSERT했다.

```text
  item_id  amount  valid_from  valid_to
  7        1200    2026-03-01  2026-09-30
  7        1000    2026-06-01  2026-12-31      ← 6/1~9/30이 겹친다
```

- **원인**
  - "검사 후 삽입"이 원자적이지 않다.
  - InnoDB REPEATABLE READ의 일반 `SELECT`는 잠그지 않는 일관 읽기다(MySQL 8.4 17.7.2.3). 그래서 서로의 미커밋 삽입을 보지 못하고, 서로를 막지도 않는다.
- **대처**
  - PostgreSQL 17: `EXCLUDE USING gist (… WITH =, period WITH &&)`. PostgreSQL 18: `WITHOUT OVERLAPS`.
  - MySQL 8.4: 부모 행 `SELECT … FOR UPDATE`로 직렬화한 뒤 검사한다. 로컬 재현에서 두 번째 세션이 첫 세션 커밋까지 기다린 뒤 `1`을 보았다.
  - 기존 데이터는 자기 조인으로 겹침을 찾아 정리한다.

```sql
SELECT a.item_id, a.valid_from, b.valid_from FROM price a JOIN price b
  ON a.item_id = b.item_id AND a.valid_from < b.valid_from AND b.valid_from < a.valid_to;
```

### 4. 경계 시각에서 두 행이 모두 유효 / 아무 행도 없음

- **현상**: 월초 0시에 가격이 두 개 나오거나, 23:59:59.5에 가격이 없다.
- **보이는 형태**: `BETWEEN valid_from AND valid_to` 조회가 경계에서 행 2개 또는 0개를 돌려준다.
- **원인**
  - 닫힌 구간 `[from, to]`로 저장했다(끝 = 다음 시작이면 경계에서 둘).
  - 또는 "끝 = 다음 시작 − 1초"로 저장했다(초 미만 시각이 빈다).
  - 날짜와 시각 타입을 섞었다.
- **대처**
  - 반열린 구간 `[from, to)`로 저장하고 `from <= t AND t < to`(PG: `@>`)로 조회한다.
  - 유효 시간을 날짜로만 다루면 `daterange`로 둔다. 시간대가 끼면 `tstzrange`로 둔다(시간대 문제는 [27-temporal-types-and-session-timezone](../27-temporal-types-and-session-timezone/2-summary.md)).

### 5. 트리거 이력의 기간이 비거나 순서가 뒤집힘

- **현상**: 이력 테이블에 `empty` 기간이 있다. 또는 긴 트랜잭션의 변경이 나중 커밋인데도 기록 시작 시각이 더 이르다.
- **보이는 형태**
  - `sys_period`가 `empty`인 행(로컬 재현). 이 중간 버전만 어떤 AS OF 조회에도 안 나온다. 앞뒤 버전 `[a, t)`·`[t, ∞)`는 맞닿아 있어 시간 틈은 없다.
  - 먼저 시작한 트랜잭션이, 나중에 시작해 먼저 커밋한 트랜잭션의 행을 고치면 UPDATE가 실패한다. `ERROR: range lower bound must be less than or equal to range upper bound`(로컬 재현, READ COMMITTED). `now()`가 그 행의 기록 시작 시각보다 이르기 때문이다.
- **원인**
  - `now()`는 트랜잭션 **시작** 시각이다. 한 트랜잭션 안의 두 번째 변경은 같은 시각을 받는다.
  - 먼저 시작해 늦게 커밋한 트랜잭션은 **커밋 순서와 다른** 시각을 기록한다. 그 시각이 고칠 행의 시작보다 이르면 범위 생성 자체가 오류다.
- **대처**
  - 빈 구간은 "중간 상태"이므로 무시해도 된다. 필요하면 트리거에서 `isempty` 검사로 이력을 건너뛴다.
  - 위 예시 트리거는 학습용이다. 실제로 쓰려면 `now() < lower(OLD.sys_period)`인 경우를 처리해야 한다(예: 오류로 재시도시키기, 또는 시작 시각을 `lower(OLD.sys_period)`로 끌어올리기).
  - 커밋 순서가 중요하면 기록 시간을 앱이 넣지 말고, 짧은 트랜잭션을 쓴다. 엄밀한 순서가 필요하면 CDC(WAL 순서)로 이력을 만든다.
  - `clock_timestamp()`(실제 현재 시각)로 바꾸면 한 트랜잭션 안에서도 시각이 달라진다. 대신 SQL:2011의 "트랜잭션 동안 고정" 의미에서 벗어난다.

## 핵심 문장

- 유효 시간은 "현실에서 언제 참이었나", 기록 시간은 "DB가 언제 그렇게 알았나"다. 둘 다 가진 테이블이 바이템포럴이다.
- 소급 정정은 덮어쓰지 않는다. 옛 행의 기록 기간을 닫고 새 행을 연다. 그래야 "그때 알던 기준"의 리포트를 다시 뽑을 수 있다.
- 기간은 반열린 구간 `[시작, 끝)`으로 둔다. SQL:2011과 PostgreSQL 범위 타입의 기본이다.
- 같은 대상의 기간 겹침 금지는 DB 제약으로 건다. PostgreSQL 17은 `EXCLUDE USING gist`, 18은 `WITHOUT OVERLAPS`다. MySQL 8.4에는 없어 부모 행 락으로 직렬화한다.
- SQL:2011 system-versioned 테이블은 PostgreSQL 17·18과 MySQL 8.4 모두 지원하지 않는다. 트리거·이력 테이블로 흉내 내며, `now()`가 트랜잭션 시작 시각이라는 점을 기억한다.

## 관련 주제·근거

- 선행
  - [16-mvcc](../16-mvcc/2-summary.md) — 행 버전과 가시성
  - [02-keys-and-constraints](../02-keys-and-constraints/2-summary.md) — 제약
- 연결
  - [data-structure/30-interval-tree](../../data-structure/30-interval-tree/2-summary.md) — 겹치는 구간 질의
  - [domain-modeling/advanced/10-price-history](../../domain-modeling/advanced/10-price-history/2-summary.md) — 유효 시각 + 기록 시각의 도메인 모델, 재발행 vs 재정산
  - [domain-modeling/advanced/16-audit-replay](../../domain-modeling/advanced/16-audit-replay/2-summary.md) — 발생 시각과 수신 시각이 다른 이벤트
  - [domain-modeling/23-versioned-rules-and-effective-dating](../../domain-modeling/23-versioned-rules-and-effective-dating/2-summary.md)
  - [data-engineering/04-slowly-changing-dimensions](../../data-engineering/04-slowly-changing-dimensions/2-summary.md)
  - [27-temporal-types-and-session-timezone](../27-temporal-types-and-session-timezone/2-summary.md) — `timestamptz`와 세션 시간대
- 표준·논문·책
  - K. Kulkarni, J.-E. Michels, "Temporal features in SQL:2011", SIGMOD Record 41(3), 2012 — `PERIOD FOR`, closed-open 모델, `FOR PORTION OF`의 행 분할, `WITH SYSTEM VERSIONING`, 트랜잭션 타임스탬프 고정, `FOR SYSTEM_TIME AS OF / FROM…TO / BETWEEN`, 바이템포럴 예 <https://cs.ulb.ac.be/public/_media/teaching/infoh415/tempfeaturessql2011.pdf>
  - SQL:2011 표준 본문(ISO/IEC 9075-2:2011)은 유료라 직접 열람하지 않았다. 위 논문 경유다.
  - R. T. Snodgrass, 『Developing Time-Oriented Database Applications in SQL』, Morgan Kaufmann, 2000 — 5장 Defining State Tables, 7장 Modifying State Tables, 9장 Transaction-Time State Tables, 10장 Bitemporal Tables(저자 공개 PDF 목차 확인) <https://www2.cs.arizona.edu/~rts/tdbbook.pdf>
  - Martin Fowler, "Bitemporal History"(2021-04-07) — actual/record 용어, Sally 급여 예 <https://martinfowler.com/articles/bitemporal-history.html>
- 제품 문서
  - PostgreSQL 17 부록 D.2 Unsupported Features — T180 System-versioned tables, T181 Application-time period tables, T502 Period predicates <https://www.postgresql.org/docs/17/unsupported-features-sql-standard.html>
  - PostgreSQL 17 CREATE TABLE `EXCLUDE` · 8.17 Range Types · 9.9.5 Current Date/Time(`now()` = 트랜잭션 시작) <https://www.postgresql.org/docs/17/sql-createtable.html>
  - MySQL 8.4 17.7.2.3 Consistent Nonlocking Reads <https://dev.mysql.com/doc/refman/8.4/en/innodb-consistent-read.html>
  - PostgreSQL 18 CREATE TABLE `WITHOUT OVERLAPS`·`PERIOD`, PostgreSQL 18 릴리스 노트 <https://www.postgresql.org/docs/18/sql-createtable.html> · <https://www.postgresql.org/docs/18/release-18.html>
- 로컬 재현(PostgreSQL 17.11, MySQL 8.4.10): PG 17의 `WITHOUT OVERLAPS`·`WITH SYSTEM VERSIONING` 구문 오류, `EXCLUDE` 겹침 거부와 맞닿음 허용, 바이템포럴 소급 정정과 두 AS OF 질의, 트리거 이력의 빈 구간, MySQL `WITH SYSTEM VERSIONING` 1064, MySQL 검사 후 삽입 경쟁으로 겹친 두 행과 부모 행 `FOR UPDATE`로 막기
