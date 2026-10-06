# database/29-soft-delete-and-data-lifecycle — 소프트 삭제와 데이터 수명 주기 — 정리 (힌트)

## 해결하는 문제

`DELETE`는 커밋되면 행이 조회에서 사라지고, 보통의 SQL로는 되살릴 수 없다.
- 디스크에서 물리적으로 치우는 일은 나중이다(PostgreSQL `VACUUM`, InnoDB purge). 백업 사본은 따로 남는다.

그런데 현업은 자주 이렇게 말한다.
- "실수로 지운 걸 되살려 주세요."
- "탈퇴한 회원의 과거 주문 내역은 남아야 합니다."
- "누가 언제 지웠는지 감사 기록이 필요합니다."

그래서 행을 지우지 않고 `deleted_at`에 시각만 적는 **소프트 삭제**가 생겼다.

```text
  하드 삭제:   DELETE FROM users WHERE id = 7;              → 행이 없다
  소프트 삭제: UPDATE users SET deleted_at = now() WHERE id = 7; → 행은 있고, "지워졌다"는 표시만
```

쉬운 예: 휴지통이다.
- 파일을 지우면 휴지통으로 간다. 되살릴 수 있다.
- 하지만 휴지통의 파일도 디스크를 차지하고, 검색에 걸리고, 비우지 않으면 영원히 남는다.

똑같은 구조다.\
소프트 삭제는 "지웠다"를 **모든 쿼리·제약·보관 정책이 알아야 하는 상태**로 바꾼다.\
하나라도 모르면 삭제된 데이터가 보이거나, 새 데이터가 막히거나, 지워야 할 데이터가 남는다.

실무 예:
- 탈퇴한 회원이 같은 이메일로 재가입하려 하자 `duplicate key` 에러가 난다.
- 관리자 통계 화면 하나가 `deleted_at IS NULL`을 빠뜨려 탈퇴 회원 수까지 센다.
- 개인정보 파기 요청을 처리했다고 답했는데, 원본 행은 `deleted_at`만 찍힌 채 3년째 남아 있다.

## 동작·원리

### 1. 소프트 삭제 = 모든 읽기에 붙는 조건

```text
  users
  id | email     | deleted_at
   1 | a@x.com   | 2026-09-01   ← 삭제됨
   2 | a@x.com   | NULL         ← 같은 이메일로 재가입
   3 | b@x.com   | NULL

  "살아 있는 회원"을 뜻하는 모든 곳에  WHERE deleted_at IS NULL
     목록 · 검색 · 로그인 · 통계 · 조인 대상 · 유일성 검사 · 배치 · 관리자 SQL
```

- 한 곳이라도 빠뜨리면 삭제된 행이 섞인다. 에러는 나지 않는다.
- Brandur(2022-07-19, "Soft deletion probably isn't worth it")는 이 "빠뜨린 조건" 문제와, ORM이 조건을 자동으로 붙여도 DB를 직접 조회하는 운영자는 여전히 빠뜨린다는 점을 첫 번째 비용으로 든다.

### 2. UNIQUE 제약과 부딪힌다

```text
  UNIQUE(email)                     → 1번(삭제됨)이 a@x.com을 쥐고 있어 2번 INSERT 실패
  UNIQUE(email, deleted_at)         → 살아 있는 행은 deleted_at이 NULL.
                                      NULL끼리는 서로 다르다고 보므로 a@x.com 살아 있는 행이 둘 들어감 ✘
  부분 유니크 인덱스(PG)             → 살아 있는 행끼리만 유일  ✔
     CREATE UNIQUE INDEX ... ON users(email) WHERE deleted_at IS NULL;
```

로컬 재현(예시):
- PostgreSQL 17.11, `UNIQUE(email)`: 삭제된 행이 있는데 재가입 → `duplicate key value violates unique constraint "u2_email_key"`.
- PostgreSQL 17.11, 부분 유니크 인덱스: 삭제된 행이 있어도 재가입 성공. 살아 있는 행이 둘이 되려 하면 `duplicate key value violates unique constraint "users_email_live"`.
- MySQL 8.4.10, `UNIQUE(email, deleted_at)`: 살아 있는 `c@x.com` 두 행이 **둘 다 들어갔다.** 유니크 인덱스는 NULL을 여러 개 허용하기 때문이다.

  - *부분 인덱스(partial index)*: 조건(술어)을 만족하는 행만 담는 인덱스. PostgreSQL 문서 11.8은 "조건을 만족하는 행 사이에서만 유일성을 강제하는" 부분 유니크 인덱스를 예제 11.3으로 든다.

MySQL 8.4에는 부분 인덱스가 없다. 대신 "살아 있을 때만 값, 삭제되면 NULL"인 식을 인덱싱한다.

```sql
-- MySQL 8.4: 생성 컬럼 + UNIQUE
ALTER TABLE users
  ADD COLUMN email_live VARCHAR(255)
      GENERATED ALWAYS AS (IF(deleted_at IS NULL, email, NULL)) VIRTUAL,
  ADD UNIQUE KEY uq_email_live (email_live);

-- 또는 함수 키 파트(문서 15.1.15 "Functional Key Parts")
CREATE UNIQUE INDEX uq_email_live2 ON users ((IF(deleted_at IS NULL, email, NULL)));
```

- 로컬 재현(MySQL 8.4.10): 두 방식 모두 삭제된 행이 있을 때 재가입은 성공했다. 살아 있는 중복은 `ERROR 1062 (23000): Duplicate entry 'a@x.com' for key 'users.uq_email_live'`로 막았다.
- 참고: PostgreSQL 15+는 `UNIQUE NULLS NOT DISTINCT`로 NULL끼리도 같다고 볼 수 있다(문서 CREATE TABLE). 하지만 소프트 삭제에는 부분 인덱스가 더 직접적이다.

### 3. 부분 인덱스는 조건이 쿼리에 있어야 쓰인다

```text
  (예시, PostgreSQL 17.11, 10만 행, 인덱스는 users_email_live 하나뿐)
  WHERE email='u5@x.com' AND deleted_at IS NULL  →  Index Scan using users_email_live
  WHERE email='u5@x.com'                         →  Seq Scan on users   ← 조건을 빠뜨리면 풀스캔
```

- 플래너는 쿼리 조건이 인덱스 술어를 **함의**한다고 인식할 때만 부분 인덱스를 쓴다(문서 11.8). 인식은 계획 시점에 한다. 그래서 술어 조건을 바인드 파라미터로 바꾸면(문서 예: `x < ?`는 `x < 2`를 함의하지 못함) 쓰이지 않는다. `deleted_at IS NULL`은 SQL에 글자 그대로 적는다.
- 조건을 빠뜨리면 삭제된 행이 섞이는 것에 더해 **느려지기도** 한다.

### 4. FK는 소프트 삭제를 모른다

```text
  users(id=1, deleted_at=2026-09-01)  ◀── orders(user_id=1)
  FK 검사: users에 id=1이 "있다" → 통과. 조인하면 삭제된 회원이 그대로 나온다.
  하드 삭제 시도: DELETE FROM users WHERE id=1 → FK 위반(PG 23503)
```

- 로컬 재현(PostgreSQL 17.11): 소프트 삭제된 회원을 가리키는 주문이 조인에서 그대로 나왔다. 그 회원을 하드 삭제하려 하자 `violates foreign key constraint "orders_user_id_fkey"`로 막혔다.
- 참조 무결성은 "행이 있느냐"만 본다. "살아 있느냐"는 앱이 챙겨야 한다. Brandur는 이를 "foreign keys are effectively lost"라고 표현한다.
- 나중에 보관 기한이 지나 하드 삭제하려 하면, 이번엔 FK 때문에 **자식부터** 지워야 한다.

### 5. 수명 주기 — 소프트 삭제는 중간 정거장이다

```text
  활성 ──(탈퇴·삭제 요청)──▶ 소프트 삭제 ──(유예·보관 기한 경과)──▶ 하드 삭제 또는 익명화
   │                          │                                     │
   │                          ├ 조회 필터, 부분 유니크               ├ 복구 불가하게(백업·복제본·검색 인덱스·캐시 포함)
   │                          └ 되살리기 가능 기간                   └ 다른 법령상 보존 대상은 분리 보관
```

- 개인정보 보호법 제21조(2023-09-15 시행본): 보유기간 경과·처리 목적 달성 등으로 불필요해지면 **지체 없이** 파기해야 한다(①). 파기는 복구·재생되지 않게 해야 한다(②). 다른 법령으로 보존해야 하면 다른 개인정보와 **분리해 저장·관리**해야 한다(③).
- GDPR 제17조: 삭제권 요건에 해당하면 "without undue delay" 삭제. 제12조(3): 요청에 대한 조치 정보는 지체 없이, 늦어도 수령 후 1개월 안에(필요 시 2개월 연장) 제공.
- 즉 `deleted_at`만 찍고 끝내면, 법이 말하는 "파기"가 아니다. 소프트 삭제 뒤에 **하드 삭제 배치**가 반드시 있어야 한다.

### 6. 대안 — 삭제 행을 다른 테이블로 옮긴다

Brandur의 제안: 원본 테이블에서는 진짜로 지우고, 지운 행은 범용 보관 테이블에 JSON으로 옮긴다.

```sql
-- PostgreSQL: 지우면서 옮기기 (한 문장, 한 트랜잭션)
WITH deleted AS (
  DELETE FROM customer WHERE id = $1 RETURNING *
)
INSERT INTO deleted_record (original_table, original_id, data)
SELECT 'customer', id, to_jsonb(deleted.*) FROM deleted;
```

- 원본 테이블은 살아 있는 행만 가진다. 필터 누락·부분 인덱스 문제, 그리고 "소프트 삭제된 부모를 자식이 계속 가리키는" 문제가 사라진다.
- 단 `DELETE`는 원본 부모를 실제로 지우므로, 자식이 참조 중이면(기본 `NO ACTION`) FK 위반으로 실패한다. 자식 처리가 먼저다.
- 대가: 되살리기가 쉽지 않다. 그리고 보관 테이블도 보관 기한 뒤 지워야 한다.

## 쓰이는 자료구조·알고리즘

- **부분 인덱스(술어 인덱스)**: B+Tree에 조건을 만족하는 행만 넣는다. 인덱스가 작아지고, 조건 안에서의 유일성을 강제할 수 있다. 플래너는 쿼리 조건이 술어를 함의하는지 증명해야 쓴다. 부분·표현식 인덱스는 [09-index-design](../09-index-design/2-summary.md).
- **NULL을 구별하는 UNIQUE**: SQL 유니크 제약에서 NULL은 서로 같지 않다. 그래서 "삭제되면 NULL"로 바꾼 식을 인덱싱하면 삭제된 행은 유일성 검사에서 빠진다.
- **생성 컬럼·함수 인덱스**: 행 값으로 계산한 식을 인덱스 키로 쓴다(MySQL 8.4 생성 컬럼, 함수 키 파트).
- **시간 파티션**: 보관 기한 삭제가 잦으면 시각으로 파티션을 나누고 오래된 파티션을 통째로 떼어 낸다. 행 단위 `DELETE`보다 싸다.
  - 조건: 그 파티션의 **모든 행**이 파기 대상일 때만 된다. 기한이 `deleted_at` 기준인데 `created_at`으로 나눴다면, 오래된 파티션에도 살아 있는 행이 있어 통째로 뗄 수 없다. 분할은 33번 노트.

## 적용 — 풀어나가는 법

**1) 소프트 삭제가 정말 필요한지 먼저 묻는다.**

```text
  되살리기가 실제로 필요한가?        → 아니면 하드 삭제 + 보관 테이블(6절)
  감사가 목적인가?                  → 감사 로그 테이블이 더 맞다
  탈퇴 후에도 주문을 보여야 하나?     → 회원 행 소프트 삭제 + 개인정보 컬럼 익명화
```

**2) 쓰기로 했다면 세 가지를 한 세트로 넣는다.**

```sql
-- PostgreSQL 17
ALTER TABLE users ADD COLUMN deleted_at timestamptz;
CREATE UNIQUE INDEX users_email_live ON users (email) WHERE deleted_at IS NULL;  -- ① 유일성
CREATE VIEW active_users AS SELECT * FROM users WHERE deleted_at IS NULL;        -- ② 기본 조회 경로
-- ③ 보관 기한 뒤 하드 삭제 배치(아래 4)
```

**3) ORM에서 기본 필터를 건다 (Hibernate 6.6).**

```java
@Entity
@SoftDelete(columnName = "deleted", strategy = SoftDeleteType.DELETED)  // 6.4+, boolean 표시 컬럼
public class Member { ... }

// 또는 deleted_at 타임스탬프를 유지하려면: 조회 조건만 붙인다
@Entity
@SQLRestriction("deleted_at is null")
public class Member { ... }
```

- `@SoftDelete`는 Hibernate 6.4에서 새로 생겼다. 6.6 문서 기준 표시 컬럼은 참/거짓 값이다(`ACTIVE`/`DELETED` 전략). `@OneToMany`에 달면 예외다(문서).
- 두 방식 모두 **Hibernate가 만드는 SQL에만** 붙는다. 직접 쓴 SQL, 다른 서비스, DB 직접 조회에는 붙지 않는다. 그래서 2의 뷰·부분 인덱스처럼 DB 쪽 장치도 함께 둔다.

**4) 하드 삭제 배치는 작게 나눠, 자식부터.**

```sql
-- PostgreSQL: 보관 기한(예시 30일) 지난 회원을 1000명씩
WITH victims AS (
  SELECT id FROM users
  WHERE deleted_at < now() - interval '30 days'
  ORDER BY id LIMIT 1000
)
DELETE FROM users u USING victims v
WHERE u.id = v.id
  AND u.deleted_at < now() - interval '30 days';   -- 지우는 순간 다시 확인
-- FK 자식은 먼저 지우거나 참조를 끊는다(user_id NULL 등). 개인정보 열만 익명화해도 참조가 남으면 FK 위반.
-- 청크마다 커밋, 복제 지연 확인(34번 노트)
```

- 마지막 조건이 없으면, `victims`를 고른 뒤 다른 트랜잭션이 그 회원을 복구해도 `id`만 맞으면 지운다. 로컬 재현(PostgreSQL 17.11, READ COMMITTED): 복구 `UPDATE`가 행을 잡고 있는 동안 배치를 돌리고 이어서 복구를 커밋하자, 조건이 없을 때는 복구된 회원도 삭제됐고, 조건을 넣자 남았다. READ COMMITTED는 경합한 행의 새 버전에 **대상 테이블의 WHERE 조건**을 다시 평가하기 때문이다(문서 13.2.1).

**5) 점검 SQL**

```sql
-- 필터 누락 탐지: 소프트 삭제 대상 테이블을 조건 없이 읽는 쿼리 찾기
SELECT query, calls FROM pg_stat_statements
WHERE query ILIKE '%from users%' AND query NOT ILIKE '%deleted_at%' ORDER BY calls DESC LIMIT 20;
-- 파기 누락 탐지: 보관 기한을 넘긴 소프트 삭제 행 수
SELECT count(*) FROM users WHERE deleted_at < now() - interval '30 days';
```

- `pg_stat_statements`는 확장이라 `shared_preload_libraries` 설정과 `CREATE EXTENSION`이 필요하다.

## 장애 시나리오와 대처

**① 재가입 시 UNIQUE 위반 (커리큘럼 ⚠)**
- 현상: 탈퇴 회원이 같은 이메일로 가입하면 500 에러.
- 보이는 형태: PG `duplicate key value violates unique constraint` (23505), MySQL `ERROR 1062 (23000): Duplicate entry`.
- 원인: 유일성 제약이 삭제된 행까지 포함한다.
- 대처: PG 부분 유니크 인덱스, MySQL 생성 컬럼/함수 인덱스로 "살아 있는 행끼리만 유일"로 바꾼다. `UNIQUE(email, deleted_at)`은 NULL 때문에 살아 있는 중복을 허용하므로 쓰지 않는다.

**② `deleted_at IS NULL` 누락 → 삭제된 데이터 노출 (커리큘럼 ⚠)**
- 현상: 검색 결과에 탈퇴 회원이 나온다. 통계 숫자가 앱 화면과 다르다.
- 보이는 형태: 에러 없음. 부분 인덱스만 있는 테이블이면 해당 쿼리가 Seq Scan으로 바뀌어 느려지기도 한다(3절).
- 원인: 조회 경로가 여러 개이고, 그중 하나가 조건을 몰랐다(직접 쓴 SQL, 새 API, 관리자 도구, 다른 서비스).
- 대처: 기본 조회 경로를 뷰(`active_users`)나 ORM 필터로 강제하고, 원본 테이블 직접 조회를 리뷰에서 막는다. PostgreSQL이면 행 수준 보안으로 앱 역할에서 삭제 행을 숨기는 방법도 있다(43번 노트). 근본적으로는 6절처럼 원본에서 진짜로 지운다.

**③ FK가 소프트 삭제 행을 가리킴 → 고아 참조 (커리큘럼 ⚠)**
- 현상: 주문 화면의 "담당 판매자"가 이미 탈퇴한 판매자인데 링크를 누르면 404. 반대로 판매자 하드 삭제 배치는 FK 위반으로 멈춘다.
- 보이는 형태: 조인 결과에 `deleted_at`이 찍힌 부모. 하드 삭제 시 PG 23503, MySQL `ERROR 1451`.
- 원인: FK는 부모 행의 존재만 검사한다. 소프트 삭제는 존재를 바꾸지 않는다.
- 대처: 부모를 소프트 삭제할 때 자식을 어떻게 할지(같이 소프트 삭제, 익명화, 참조 해제)를 정책으로 정하고 같은 트랜잭션에서 처리한다. 하드 삭제는 자식부터 지우거나 참조를 끊는다(`user_id` NULL, `ON DELETE SET NULL`). 자식의 개인정보 열만 익명화하면 참조가 남아 여전히 막힌다.

**④ 삭제 요청의 법정 기한을 넘겨도 원본이 남음 (커리큘럼 ⚠)**
- 현상: 개인정보 열람 요청에 "삭제된 회원"의 원본 정보가 그대로 조회된다. 감사에서 파기 미이행이 지적된다.
- 보이는 형태: `deleted_at`이 오래전인 행이 대량으로 존재. 백업·분석 DW·검색 인덱스에도 사본이 있다.
- 원인: 소프트 삭제를 "파기"로 간주했다. 하드 삭제·익명화 배치가 없거나 실패를 아무도 몰랐다.
- 대처: 보관 기한별 하드 삭제 배치를 두고, 처리 건수와 "기한 초과 잔존 행 수"를 지표로 감시한다. 다른 법령상 보존 대상은 분리 저장한다(개인정보 보호법 제21조③). 백업·복제본·캐시·검색 인덱스의 사본 처리도 절차에 넣는다(보안 영역 27번 노트).

## 핵심 문장

- 소프트 삭제는 "지웠다"를 모든 쿼리·제약·보관 정책이 알아야 하는 상태로 바꾼다.
- 유일성은 "살아 있는 행끼리만"이어야 한다. PostgreSQL은 부분 유니크 인덱스, MySQL은 "삭제되면 NULL"인 식을 인덱싱한다.
- `UNIQUE(email, deleted_at)`은 NULL끼리 다르다는 규칙 때문에 살아 있는 중복을 허용한다.
- FK는 행의 존재만 본다. 소프트 삭제된 부모를 가리키는 자식은 막지 못한다.
- `deleted_at`은 파기가 아니다. 보관 기한 뒤의 하드 삭제·익명화 배치가 있어야 수명 주기가 닫힌다.

## 관련 주제·근거

- 선행
  - [02-keys-and-constraints](../02-keys-and-constraints/2-summary.md) — UNIQUE·FK·NULL
  - [09-index-design](../09-index-design/2-summary.md) — 부분·표현식 인덱스
- 연결
  - [26-schema-migration](../26-schema-migration/2-summary.md) — 기존 UNIQUE를 부분 인덱스로 바꾸는 절차
  - [28-key-strategy-surrogate-natural-public-id](../28-key-strategy-surrogate-natural-public-id/2-summary.md) — 자연키 UNIQUE
  - [34-large-backfill-and-batch-dml](../34-large-backfill-and-batch-dml/2-summary.md) — 하드 삭제 배치의 청크·스로틀
  - `33-partitioning-and-sharding` — 초안 [systems/partitioning-vs-sharding](../../systems/partitioning-vs-sharding/)
  - [43-row-level-security](../43-row-level-security/2-summary.md) — 원고 [systems/postgres-rls](../../systems/postgres-rls/)
  - [security/27-pii-classification-masking-retention](../../security/27-pii-classification-masking-retention/2-summary.md)
- 글·문서
  - Brandur Leach, "Soft deletion probably isn't worth it", 2022-07-19 <https://brandur.org/soft-deletion>
  - PostgreSQL 17 문서 13.2.1 Read Committed(경합 행 재평가) <https://www.postgresql.org/docs/17/transaction-iso.html> · 24.1 Routine Vacuuming <https://www.postgresql.org/docs/17/routine-vacuuming.html> · 5.5.5 Foreign Keys(참조 동작) <https://www.postgresql.org/docs/17/ddl-constraints.html>
  - PostgreSQL 17 문서 11.8 Partial Indexes(예제 11.3 부분 유니크 인덱스) <https://www.postgresql.org/docs/17/indexes-partial.html> · CREATE TABLE(`NULLS NOT DISTINCT`) <https://www.postgresql.org/docs/17/sql-createtable.html> · PostgreSQL 15 Release Notes(`UNIQUE NULLS NOT DISTINCT` 도입) <https://www.postgresql.org/docs/release/15.0/>
  - MySQL 8.4 Reference Manual 17.8.9 Purge Configuration(삭제 표시 행의 나중 제거) <https://dev.mysql.com/doc/refman/8.4/en/innodb-purge-configuration.html>
  - MySQL 8.4 Reference Manual 15.1.15 CREATE INDEX(함수 키 파트) <https://dev.mysql.com/doc/refman/8.4/en/create-index.html> · 15.1.20.8 CREATE TABLE and Generated Columns <https://dev.mysql.com/doc/refman/8.4/en/create-table-generated-columns.html> — 유니크 인덱스는 NULL을 여러 개 허용(15.1.15)
  - Hibernate ORM 6.6 User Guide §3.12 Soft Delete(`@SoftDelete`, 6.4 신설), §6.9.1 `@SQLRestriction` <https://docs.hibernate.org/orm/6.6/userguide/html_single/Hibernate_User_Guide.html>
  - 개인정보 보호법 제21조(개인정보의 파기), 법률 제19234호, 2023-09-15 시행본 — 국가법령정보센터 <https://www.law.go.kr/법령/개인정보보호법>
  - GDPR Art. 17, Art. 12(3) — 조문 사본 <https://gdpr-info.eu/art-17-gdpr/>
- 로컬 재현(PostgreSQL 17.11, MySQL 8.4.10): UNIQUE vs 부분 유니크 재가입, 부분 인덱스 사용·미사용 EXPLAIN, 소프트 삭제 부모 조인·하드 삭제 FK 위반, MySQL 생성 컬럼·함수 인덱스 유니크, `UNIQUE(email, deleted_at)` 중복 허용, 하드 삭제 배치와 복구의 경합(READ COMMITTED)
