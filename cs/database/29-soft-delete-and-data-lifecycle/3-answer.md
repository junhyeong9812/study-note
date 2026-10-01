# database/29-soft-delete-and-data-lifecycle — 정답

## 정답

### 1. 이유와 비용

- 이유: 실수 삭제 되살리기, 탈퇴 후에도 과거 거래 이력 보존, 누가 언제 지웠는지 감사.
- 비용
  1. 모든 읽기에 `deleted_at IS NULL`이 필요하다. 하나라도 빠지면 삭제된 행이 조용히 섞인다.
  2. 제약이 삭제된 행까지 본다. UNIQUE는 재가입을 막고, FK는 삭제된 부모를 가리키는 자식을 막지 못한다.
  3. 행이 지워지지 않으니 보관 기한 뒤 하드 삭제가 따로 필요하다. 없으면 법정 파기 의무를 어긴다.

### 2. 세 가지 유일성 설계

| | 재가입(삭제 행 존재) | 살아 있는 중복 추가 |
|---|---|---|
| (a) `UNIQUE(email)` | ✘ 23505 / 1062 | ✘ |
| (b) `UNIQUE(email, deleted_at)` | ✔ | **✔ 들어가 버림** — 살아 있는 행은 `deleted_at`이 NULL, NULL끼리는 같지 않다 |
| (c) 부분 유니크 인덱스 | ✔ | ✘ `users_email_live` 위반 |

- 로컬 재현: (a)는 PostgreSQL 17.11 `u2_email_key` 위반, (b)는 MySQL 8.4.10에서 살아 있는 `c@x.com` 두 행이 모두 들어갔다, (c)는 PostgreSQL 17.11에서 재가입 성공·중복 거절.
- (b)는 PostgreSQL에서도 같다(로컬 재현, PostgreSQL 17.11에서 두 행 모두 들어감). 유니크 제약에서 NULL은 같지 않다고 보기 때문이다. `NULLS NOT DISTINCT`(15+)를 주면 달라진다.

### 3. MySQL에서 살아 있는 행끼리만 유일

```sql
ALTER TABLE users
  ADD COLUMN email_live VARCHAR(255)
      GENERATED ALWAYS AS (IF(deleted_at IS NULL, email, NULL)) VIRTUAL,
  ADD UNIQUE KEY uq_email_live (email_live);
-- 또는
CREATE UNIQUE INDEX uq_email_live2 ON users ((IF(deleted_at IS NULL, email, NULL)));
```

- 동작 이유: 살아 있는 행은 식의 값이 email, 삭제된 행은 NULL이다. 유니크 인덱스는 NULL을 여러 개 허용한다(문서 15.1.15). 그래서 삭제된 행은 유일성 검사에서 빠지고, 살아 있는 행끼리만 비교된다.
- 로컬 재현(MySQL 8.4.10): 두 방식 모두 재가입 성공, 살아 있는 중복은 `ERROR 1062 ... for key 'users.uq_email_live'`.

### 4. 부분 인덱스와 실행 계획

```text
  WHERE email='u5@x.com'                         → Seq Scan on users
  WHERE email='u5@x.com' AND deleted_at IS NULL  → Index Scan using users_email_live
```

- 부분 인덱스에는 살아 있는 행만 들어 있다. 조건 없는 쿼리는 삭제된 행도 원하므로 이 인덱스로는 답할 수 없다. 플래너는 쿼리 조건이 술어를 함의한다고 인식할 때만 쓴다(문서 11.8).
- 로컬 재현(PostgreSQL 17.11, 10만 행)에서 위 두 계획이 그대로 나왔다. 조건 누락은 결과 오류와 성능 저하를 동시에 부른다.

### 5. FK와 소프트 삭제

- 막지 못한다. FK는 "부모 행이 있느냐"만 본다. 소프트 삭제된 부모도 행은 있다. 조인하면 삭제된 회원이 그대로 나온다(로컬 재현).
- 하드 삭제 시: 자식이 남아 있으면 FK 위반으로 실패한다(PG `23503 ... violates foreign key constraint "orders_user_id_fkey"`, MySQL 1451). 자식부터 지우거나 자식의 참조를 끊어야 한다(`user_id`를 NULL로, 또는 `ON DELETE SET NULL`). 자식의 개인정보 열만 익명화하면 `user_id`가 그대로라 여전히 FK 위반이다. `ON DELETE CASCADE`는 의도치 않게 넓게 지울 수 있어 신중히 쓴다.

### 6. 개인정보 보호법 제21조

1. ① 보유기간 경과, 처리 목적 달성 등으로 불필요해지면 **지체 없이** 파기한다. 다른 법령으로 보존해야 하는 경우는 예외다.
2. ② 파기는 **복구·재생되지 않도록** 한다.
3. ③ ①의 예외로 보존하면 다른 개인정보와 **분리해 저장·관리**한다.

- (2023-09-15 시행본 기준, 국가법령정보센터 본문 확인)
- `deleted_at`은 "안 보이게"일 뿐 데이터는 그대로다. 되살리기가 가능하다는 것 자체가 ②와 반대다. 백업·복제본·DW·검색 인덱스의 사본도 남아 있다.

### 7. 삭제 행을 보관 테이블로

```sql
WITH deleted AS (
  DELETE FROM customer WHERE id = $1 RETURNING *
)
INSERT INTO deleted_record (original_table, original_id, data)
SELECT 'customer', id, to_jsonb(deleted.*) FROM deleted;
```

- 얻는 것: 원본 테이블엔 살아 있는 행만 남는다. 필터 누락, 부분 유니크, "소프트 삭제된 부모를 자식이 가리키는" 문제가 사라진다. 한 문장이라 삭제와 보관이 원자적이다.
- 잃는 것: 되살리기가 수작업이다(JSON → 원래 컬럼). 보관 테이블도 보관 기한 뒤 지워야 한다. FK 자식은 여전히 먼저 처리해야 한다. 참조 중인 자식이 있으면 이 `DELETE` 자체가 FK 위반으로 실패한다.

### 8. 통계 12% 과다

- 원인 후보: 통계 쿼리가 `deleted_at IS NULL`을 빠뜨렸다. 또는 ORM 필터가 없는 네이티브 SQL·BI 도구가 원본 테이블을 직접 읽는다.
- 찾기:

```sql
SELECT count(*) FILTER (WHERE deleted_at IS NULL)     AS live,
       count(*) FILTER (WHERE deleted_at IS NOT NULL) AS deleted
FROM users;                                    -- 차이가 12%와 맞는지
SELECT query, calls FROM pg_stat_statements
WHERE query ILIKE '%from users%' AND query NOT ILIKE '%deleted_at%';
```

- 재발 방지: 통계·관리 도구가 뷰(`active_users`)만 읽게 권한을 나누고, 원본 직접 조회를 리뷰에서 막는다. 필요하면 원본에서 진짜로 지우는 방식(7번)으로 바꾼다.

### 9. Hibernate 6.6

- `@SoftDelete`(6.4 신설): 삭제를 표시 컬럼 UPDATE로 바꾸고 조회에 조건을 붙인다. 표시 값은 참/거짓이다(`ACTIVE`/`DELETED` 전략, 기본 컬럼 `active`/`deleted`). `@OneToMany`에 달면 예외다.
- `@SQLRestriction("deleted_at is null")`: 엔티티·컬렉션 조회 SQL에 조건만 붙인다. 삭제 동작은 바꾸지 않는다.
- 둘 다 **Hibernate가 생성하는 SQL에만** 적용된다. 직접 쓴 SQL, JDBC 템플릿, 다른 서비스, BI 도구, DB 콘솔은 막지 못한다. 그래서 DB 쪽 장치(뷰, 부분 인덱스, 권한)를 함께 둔다.
