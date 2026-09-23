# cs/issue/database/sql-dialect-and-driver-traps — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 사건 기록 원문 대조 작성. 복습 전 읽지 말 것.

태그: —

## 정답
<!-- 질문 1:1 대응 -->

1. **NULL 은 같다고 판정되지 않는다(이 사례: MySQL).** SQL 에서 `NULL = NULL` 은 참이 아니라 UNKNOWN 이다. MySQL(InnoDB)·PostgreSQL(기본 `NULLS DISTINCT`) 등은 UNIQUE 판정에서 NULL 끼리를 서로 다른 값으로 취급하므로 `(NULL, 'a')` 행이 몇 개든 들어간다 — 루트(`parent_id` NULL) 유일성이 무력화됐다.\
   단 **엔진마다 다르다**: SQL Server 의 UNIQUE 는 NULL 을 같은 값으로 봐 하나만 허용하고, Oracle 은 키 전체가 NULL 인 행만 색인에서 빠진다(부분 NULL 복합 키는 비NULL 부분이 같으면 중복으로 거부), PostgreSQL 15+ 는 `NULLS NOT DISTINCT` 옵션을 준다 — 대상 엔진·버전으로 확인한다.\
   같은 원리로, 멱등 키에 NULL 가능 컬럼이 섞인 `UNIQUE (...) + ON CONFLICT DO NOTHING` 은 NULL 행의 재적재 중복을 막지 못한다(그 사례는 1차 버전에서 위험을 수용했다).\
   대안(엔진별): 이 사례(MySQL 8.0.13+)는 컬럼 대신 식을 인덱싱하는 **식(functional) 유니크 인덱스**로 유일성을 다시 걸었다 — 이때 NULL 대체값(센티널)은 실제 값과 절대 겹치지 않아야 한다(겹치면 루트와 실제 부모가 거짓 충돌). PostgreSQL 이면 `NULLS NOT DISTINCT`(15+)나 `WHERE parent_id IS NULL` 부분 유니크 인덱스가 더 직접적이다. 또 제약 위반 예외는 일괄 변환 대신 **제약 이름으로 판별**하도록 했다.
   > **3값 논리** — SQL 비교 결과가 TRUE/FALSE/UNKNOWN 셋인 체계. NULL 이 끼면 UNKNOWN 이 된다.

2. **방언·파서는 실제 엔진이 정한다.** ① `DROP COLUMN IF EXISTS` 는 다른 방언(MariaDB 등) 문법이라 MySQL 8.4 에서 1064 문법 오류가 났다. ② `INSERT … SELECT … FROM a JOIN b ON … ON DUPLICATE KEY UPDATE` 마이그레이션이 MySQL 8.4 실적용에서 1064 로 실패했고, 조인 SELECT 를 파생 테이블로 감싸자 통과했다. 사례 기록은 이를 "JOIN 의 `ON` 과 ON DUPLICATE 의 `ON` 모호성"으로 해석했지만, 명시적 조인 조건 뒤의 `ON DUPLICATE KEY UPDATE` 는 일반적으로 허용되는 형태라 **정확한 실패 문장을 재현하기 전엔 파서 원인을 단정할 수 없다**(모호성이 문제 되는 전형은 조건 없는 JOIN·UNION 등이 앞에 오는 경우). 이와 별개로 `VALUES(col)` 참조는 8.0.20+ 에서 폐기 예정(deprecated) 경고가 나므로 행 별칭·파생 테이블 컬럼 참조로 옮기는 게 맞다. ③ 예약어(`window`)를 컬럼명으로 쓰면 인용 없이는 식별자가 될 수 없다. ④ 수정 대상 테이블을 같은 문장의 서브쿼리에서 직접 재참조하는 것도 MySQL 이 문장 형태에 따라 제한한다(INSERT…SELECT 의 FROM 절 자체는 허용되나 서브쿼리 재참조는 제한 — 에러 1093 계열).\
   대체 DB(H2 등)·ORM 매핑·단위 테스트는 이 엔진의 파서와 제약을 흉내 내지 않으므로 초록이 된다.\
   교정: 대상과 같은 버전의 일회용 컨테이너에 마이그레이션을 **실제로 적용**해 본다 — 여기에 재적용과 결과 행 수 검증까지 붙인다(단 마이그레이션 도구를 두 번 돌려 두 번째가 no-op 인 것은 **이력 테이블이 동작한다**는 증거일 뿐, SQL 문 자체를 다시 실행해도 안전하다는 멱등성 증명은 아니다 — 후자는 이력과 무관하게 같은 SQL 을 재실행해 결과를 대조해야 한다)(이름 JOIN 오타 1자로 행이 조용히 빠진 것을 행 수로 잡았다).\
   부수: 빌드 도구 라이프사이클이 단위 테스트 단계 실패 시 통합 테스트 단계를 **아예 실행하지 않아** 문제의 마이그레이션이 미검증 상태로 남았던 적도 있다 — "IT 가 실제로 돌았는지"를 결과로 확인해야 한다.

3. **서버 설정 차이.** 서버는 단일 패킷 크기 상한(`max_allowed_packet`)을 두는데(클라이언트·드라이버 쪽에도 별도 상한이 있다), 이 사례의 테스트 컨테이너는 실효 값이 1MB 로 운영보다 작아 2.8MB 단일 INSERT 가 **테스트에서만** 실패했다 → 테스트 컨테이너 설정을 운영과 맞췄다(64MB). 기본값은 버전·이미지·설정 파일마다 다르므로(예: MySQL 8.0 서버 기본은 64MB) "컨테이너 기본 = 1MB"로 일반화하지 말고 `SHOW VARIABLES` 로 양쪽 실효 값을 대조한다.\
   테이블명 대소문자 구분(`lower_case_table_names`)은 Linux 에서 기본 구분이며 MySQL 8 은 **데이터 디렉토리 초기화 때만** 정할 수 있다 — 대문자 DDL 과 소문자 쿼리가 섞인 코드가 "Table doesn't exist" 로 기동 실패 → 컨테이너 생성 시 옵션으로 지정.\
   MySQL FK 는 문자열 양쪽 컬럼의 charset **과 collation** 이 같아야 하는데, 기존 테이블은 charset 을 명시하고 신규 테이블은 서버 기본값을 따라 갈라져 FK 생성이 **incompatible** 로 거부됐다 → 신규 FK 컬럼에 charset 을 명시해 해결했다. 단 charset 만 맞추면 collation 은 그 charset 의 기본값이 되므로 참조 컬럼 collation 과 다를 수 있다 — 양쪽 `SHOW CREATE TABLE` 로 charset·collation 을 함께 확인하고 필요하면 COLLATE 까지 명시한다.

4. **가장 좁은 곳이 잠복 상한.** 평소 채번이 20자라 좁은 `VARCHAR(20)` 컬럼에도 들어가므로 아무 문제가 없다.\
   그런데 다른 경로(직접 적재·외부 인증 연동·UUID 36자 시드)로 **20자를 넘는 값이 한 번 들어오는 순간** 좁은 쪽에서 잘림 오류(1406)나 500 이 난다.\
   같은 값이 흐르는 경로 전체의 수용 한도는 가장 좁은 컬럼이 결정하는데, 그 한도는 평소 데이터로는 드러나지 않는다 → 관련 컬럼 폭을 식별자 원천과 같게 통일(`VARCHAR(100)`).\
   같은 계열: 엔티티 매핑 `TEXT` 와 DDL `MEDIUMTEXT` 불일치 사례에서 큰 콘텐츠 절단(매핑 차이만으로 절단되는 건 아니다 — 실제로 적용된 DDL 이 `TEXT`(64KB)였는지, 드라이버 바인딩·검증 경로가 길이를 자르는지 원인별로 확인해야 한다), `VARCHAR(16)` 컬럼 오버플로로 배치 대부분 실패, 외부 URL 을 `VARCHAR(1000)` 에 넣어 절단(외부 입력 길이는 상한을 예측할 수 없어 `TEXT` 로).

5. **온라인 DDL 도 락을 잡는다.** `INPLACE, LOCK=NONE` 은 실행 **도중** 읽기·쓰기를 허용한다는 뜻일 뿐, 시작과 끝에는 짧은 **배타 메타데이터 락(MDL)** 이 필요하다.\
   같은 테이블에 장기 SELECT(트랜잭션)가 진행 중이면 DDL 은 그게 끝날 때까지 MDL 대기에 걸리고, **그 뒤에 들어온 요청들도 DDL 뒤에 줄을 서** 줄줄이 막힌다.\
   대응: 대형 테이블은 읽기 작업(적재 리더)을 멈춘 뒤 인덱스를 거는 편이 빠르다. 진단은 processlist 의 state·time.\
   SQLite 는 WAL 모드에서도 **동시 writer 를 하나만** 허용한다(WAL 은 reader 와 writer 의 공존을 허용할 뿐) — 5,000건을 한 트랜잭션으로 쓰는 15~20초 동안 다른 writer 는 busy_timeout 을 소진하고 `database is locked` 로 실패했다. 커밋 간격을 50건으로 줄이고(잠금 0.3초), 쓰기를 한 프로세스로 몰고, 최종적으로 OS 파일 락으로 상호배제했다. 같은 이유로 그 사례의 워크플로 도구는 SQLite 메타 DB 와 병렬 실행기 조합을 지원하지 않아 순차 실행기로 전환했다 — 이는 그 도구의 제약이며, 일반적으로는 병렬 계산과 짧게 직렬화된 쓰기가 공존할 수 있다(동시 쓰기를 가정하는 구성이 문제).
   > **MDL(metadata lock)** — 테이블 구조가 쓰는 도중 바뀌지 않도록 보호하는 락. DDL 은 이를 배타로 잡아야 한다.

6. **SQL 문면에 안 보이는 부수 의미.** ① 지연 모드로 둔 제약(`DEFERRABLE INITIALLY DEFERRED`, 또는 트랜잭션 안에서 `SET CONSTRAINTS … DEFERRED`)은 문장 실행 시가 아니라 **커밋 시점**에 검사되므로(`DEFERRABLE` 만 붙이고 `INITIALLY IMMEDIATE` 면 여전히 문장마다 검사 — "지연 가능"일 뿐), 콜백 안의 try 로는 못 잡고 트랜잭션 실행 전체를 감싸야 한다. ② 트리거는 마이그레이션의 `UPDATE` 에도 **발화**한다 — 무조건 UPDATE 가 `updated_at` 을 전 행 갱신해 백필 값을 망가뜨릴 뻔했다 → 백필 먼저, 정규화는 `IS DISTINCT FROM` 조건으로 실제로 바뀌는 행만. ③ REPLACE 계열 upsert 는 충돌 행을 **DELETE 한 뒤 INSERT** 하므로 FK 가 활성화돼 있으면(SQLite 는 `foreign_keys=ON` 일 때) `ON DELETE CASCADE` 자식이 전부 지워진다 → 단일문 `INSERT … ON CONFLICT DO UPDATE`.\
   `SET FOREIGN_KEY_CHECKS=0` 은 트랜잭션이 아니라 **세션 상태**라 롤백으로 원복되지 않고, 끈 동안의 무결성은 보증되지 않는다. 그래서 자기참조 FK 테이블 재시드는 제약을 끄는 대신 **FK 역순 삭제**(자식 → 하위 레벨 → 상위 레벨)로도 풀었다.

7. **세션 상태는 물리 커넥션에 귀속된다.** 사용자 변수(`@ok`)·임시 테이블 같은 세션 상태는 그 문장을 실행한 **물리 커넥션**에만 존재한다.\
   커넥션 풀은 문장마다 다른 커넥션을 빌려줄 수 있으므로, `CALL sp(..., @ok)` 와 `SELECT @ok` 가 서로 다른 커넥션에서 실행되면 두 번째는 **다른 세션의 변수**(비어 있거나, 그 커넥션을 앞서 쓴 요청이 남긴 값)를 읽는다 — 오류 없이 조용히 틀린다.\
   교정: 두 문장을 **하나의 고정 커넥션**에 묶어 실행한다(아래 방안 비교).

## 문제 구조 (추상화 코드)

### 변형 A — NULL 포함 UNIQUE
```sql
-- ① 문제
CREATE UNIQUE INDEX uq_node ON node (parent_id, name);     -- parent_id NULL 행은 중복 허용

-- ② 고친 코드 (MySQL 8.0.13+ 식 인덱스)
CREATE UNIQUE INDEX uq_node ON node ((<parent_id 를 NULL 없이 표현하는 식>), name);   -- 식의 형태는 예시, NULL 대체값은 실제 값과 겹치면 안 됨
-- (PostgreSQL 15+ 대안) CREATE UNIQUE INDEX uq_node ON node (parent_id, name) NULLS NOT DISTINCT;
```
무엇이 깨졌나: 루트 유일성 무력화.\
같은 구조: NULL 가능 컬럼을 포함한 멱등 키 + `ON CONFLICT DO NOTHING` → NULL 행 재적재 중복(위험 수용 기록).

### 변형 B — 방언·파서
```sql
-- ① 문제
INSERT INTO t (k, v)
SELECT a.k, b.v FROM a JOIN b ON a.id = b.a_id
ON DUPLICATE KEY UPDATE v = VALUES(v);          -- 사례에선 MySQL 8.4 실적용 1064(파서 원인은 미재현 — 본문 참조), VALUES() 는 deprecated

-- ② 고친 코드
INSERT INTO t (k, v)
SELECT x.k, x.v FROM (SELECT a.k, b.v FROM a JOIN b ON a.id = b.a_id) x
ON DUPLICATE KEY UPDATE v = x.v;                -- 파생 테이블로 분리, VALUES() 대신 x.v
```
```sql
-- ① 문제: 대상 테이블을 같은 문장 서브쿼리에서 재참조
INSERT INTO items (...) SELECT ... WHERE NOT EXISTS (SELECT 1 FROM items WHERE id = 'X');
-- ② 고친 코드: 파생 테이블로 감쌈 — 물질화될 때만 제한을 피한다
INSERT INTO items (...) SELECT ... WHERE NOT EXISTS
  (SELECT 1 FROM (SELECT id FROM items) m WHERE m.id = 'X');
-- 옵티마이저가 파생 테이블을 바깥 쿼리로 병합(derived_merge)하면 제한이 다시 걸릴 수 있다
-- → 실제 엔진에서 통과를 확인하고, 필요하면 NO_MERGE 힌트 등으로 물질화를 강제한다
```
무엇이 깨졌나: 대체 DB·단위 테스트에서 통과한 문장이 실제 엔진 파서에서 실패.\
같은 구조: `DROP COLUMN IF EXISTS`(타 방언 문법) 1064 → 정보 스키마 조회 가드로 멱등 ALTER.\
같은 구조: 예약어 컬럼명 `window` → `time_window` 로 개명(모델·쿼리·API 동시).

### 변형 C — 서버 설정·초기화 파라미터
```java
// ① 문제: 테스트 컨테이너 실효 설정(이 사례 패킷 1MB — 기본값은 이미지·버전마다 다름) ≠ 운영
new DbContainer("engine:8");

// ② 고친 코드: 운영과 정합
new DbContainer("engine:8").withCommand("--max-allowed-packet=67108864");
```
무엇이 깨졌나: 같은 마이그레이션이 테스트에서만 실패.\
같은 구조: 테이블명 대소문자 설정은 초기화 시에만 결정 → 컨테이너 생성 시 `--lower-case-table-names=1`.\
같은 구조: 기존 테이블 charset 명시 vs 신규 테이블 서버 기본 collation → FK incompatible → 신규 FK 컬럼 charset(필요 시 collation 까지) 명시.

### 변형 D — 폭·타입 계약
```sql
-- ① 문제
users.user_id        VARCHAR(100)     -- 원천
post.writer_id       VARCHAR(20)      -- 참조: 평소 20자 채번이라 통과, UUID(36)·외부 유입 시 잘림

-- ② 고친 코드
ALTER TABLE post MODIFY writer_id VARCHAR(100);   -- 원천과 같은 폭으로 통일
```
```python
# ① 문제: 드라이버가 서버측 prepared statement 타입을 엄격 적용
await conn.fetch("SELECT ... WHERE created_at >= $1", "2026-03-01")   # str ≠ timestamp → 500

# ② 고친 코드
await conn.fetch("SELECT ... WHERE created_at >= $1", parse_date("2026-03-01"))
```
무엇이 깨졌나: 경로 중 가장 좁은/엄격한 지점이 평소엔 안 보이다 특정 입력에서 실패.\
같은 구조: 매핑 `TEXT` ≠ DDL `MEDIUMTEXT` → 큰 콘텐츠 절단(실제 적용 DDL·바인딩 경로 확인); `VARCHAR(16)` 오버플로 → 배치 대부분 실패(→ 255); 외부 URL `VARCHAR(1000)` 절단 → `TEXT`.

### 변형 E — 잠금·동시 writer
```sql
-- ① 문제: 같은 테이블에 장기 SELECT 진행 중
ALTER TABLE big ADD INDEX idx (col), ALGORITHM=INPLACE, LOCK=NONE;  -- 시작 MDL 대기 → 후속 요청 줄줄이 대기

-- ② 고친 절차
-- 읽기 작업(리더) 중지 → 인덱스 생성 → 재개 ; 진단: processlist(state, time)
```
```python
# ① 문제: SQLite, 긴 쓰기 트랜잭션
with db:                                    # 5,000건 / 15~20초 동안 writer 독점
    for row in rows: db.execute(INSERT, row)

# ② 고친 코드
for chunk in chunks(rows, 50):              # 잠금 보유 0.3초
    with file_lock(LOCK_EX), db:            # OS 수준 상호배제 + busy_timeout 60s
        db.executemany(INSERT, chunk)
```
무엇이 깨졌나: "온라인"·"WAL"이라는 이름이 동시성을 보장하지 않음.\
같은 구조: (그 도구에서) SQLite 메타 DB 와 병렬 실행기 조합 미지원 → 순차 실행기로 전환.

### 변형 F — 부수 의미(지연 제약 · 트리거 · REPLACE · 세션 변수)
```sql
-- ① 문제
UPDATE t SET x = normalize(x);                          -- updated_at 트리거가 전 행 발화
REPLACE INTO parent (...) VALUES (...);                 -- DELETE+INSERT → CASCADE 자식 삭제
SET FOREIGN_KEY_CHECKS = 0; DELETE ...; SET FOREIGN_KEY_CHECKS = 1;   -- 세션 상태, 롤백 비대상

-- ② 고친 코드
UPDATE t SET x = normalize(x) WHERE x IS DISTINCT FROM normalize(x);  -- 바뀌는 행만(백필 후)
INSERT INTO parent (...) VALUES (...) ON CONFLICT (id) DO UPDATE SET ...;
DELETE FROM child_link WHERE ...;  DELETE FROM node WHERE level = 2 ...;  DELETE FROM node WHERE level = 1 ...;  -- FK 역순
```
```java
// 지연 모드(INITIALLY DEFERRED) 제약: 콜백 안 try 로는 커밋 시점 위반을 못 잡음
try { tx.execute(status -> { repo.save(...); return null; }); }   // 트랜잭션 실행 전체를 감쌈
catch (DataIntegrityViolationException e) { ... }
```
무엇이 깨졌나: SQL 문면대로가 아닌 엔진 의미(커밋 시 검사·트리거 발화·삭제 후 삽입·세션 귀속)가 결과를 바꿈.

### 변형 G — 이식한 SQL 의 스키마 가정
```xml
<!-- ① 문제: 원형 SQL 이 대상 DB 에 없는 테이블을 조인 -->
SELECT a.*, u.user_name FROM post a LEFT JOIN legacy_user_master u ON ...
<!-- ② 고친 코드 -->
SELECT a.*, COALESCE(NULLIF(a.writer_name, ''), a.writer_id) AS writer_name FROM post a
```
무엇이 깨졌나: 문자열 SQL 은 컴파일 검증 대상이 아니라 런타임 500 으로만 드러남(검색 조건 의미 변경은 회귀 주의로 기록).

## 검증 기록
- 2026-09-24: 사건 기록 대조·추상화(Claude 초안)

## 방안 비교

같은 원리(엔진이 실제로 어떻게 동작하는지는 실제 엔진이 정한다)에 대해 두 가지 대응이 있었다.

### 방안 1 — 실제 엔진으로 검증 (변형 A~G)
```sh
# 대상과 같은 버전·같은 서버 설정의 일회용 DB 에 실제 적용 → 재실행 → 행 수 대조
run db-container:8.4 --max-allowed-packet=... &
migrate --target fresh-db && migrate --target fresh-db   # 두 번째 no-op = 이력 관리 검증(SQL 멱등성 증명 아님)
apply_sql_again V_n.sql --target fresh-db               # SQL 재적용 멱등성은 이력과 무관하게 따로 시험
count_by_group(...) == expected
```

### 방안 2 — 세션 상태를 쓰는 문장들을 한 물리 커넥션에 고정
```go
// ① 문제: 풀이 문장마다 다른 커넥션을 줄 수 있음
db.Exec("CALL sp(?, @ok)", arg)
db.QueryRow("SELECT @ok").Scan(&ok)        // 다른 세션의 변수를 읽을 수 있음

// ② 고친 코드
conn, err := db.Conn(ctx)                  // 물리 커넥션 1개 고정
if err != nil { return err }
defer conn.Close()                         // 풀로 반납 — 세션 변수는 남아 있으므로
if _, err := conn.ExecContext(ctx, "SET @ok = NULL"); err != nil { return err }  // 이전 사용자의 잔존 값 초기화
if _, err := conn.ExecContext(ctx, "CALL sp(?, @ok)", arg); err != nil { return err }
if err := conn.QueryRowContext(ctx, "SELECT @ok").Scan(&ok); err != nil { return err }
```

| | 방안 1: 실제 엔진 검증 | 방안 2: 커넥션 고정 |
|---|---|---|
| 전제 | 대상 엔진·버전·설정을 재현할 수 있음 | 세션 상태 의존 구간이 코드에서 식별됨 |
| 비용 | 테스트 시간·컨테이너 설정 정합 유지 | 풀 효율 약간 감소, 헬퍼 도입 |
| 실패 모드 | 테스트 설정이 운영과 다르면 여전히 "한쪽만 실패" | 헬퍼를 거치지 않는 호출이 새로 생기면 재발 |
| 맞는 조건 | 방언·설정·폭·파서처럼 **발견**이 문제인 경우 | 발견은 됐고 **구조적으로 막아야** 하는 경우 |

결론: 방안 1 은 "무엇이 다른가"를 찾아내는 수단이고, 방안 2 는 찾아낸 차이 중 코드 구조로 봉인할 수 있는 것(세션 귀속)을 봉인하는 수단이다.\
세션 변수 문제는 풀의 커넥션 배정이 비결정적이라 방안 1 의 테스트로도 재현이 불안정할 수 있으므로, 해당 구간은 방안 2 로 구조를 고정하는 편이 확실하다 — 이 사례도 사고 발생 전 배선 단계에서 방안 2 를 택했다.
