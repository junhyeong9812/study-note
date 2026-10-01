# database/43-row-level-security — 정답

## 정답

### 1. 조건 한 줄에 격리를 맡기는 문제

- 조건이 빠진 쿼리 하나가 전체 테넌트 행을 돌려준다. 에러도 경고도 없다. 관리 화면·배치·네이티브 쿼리 모두가 매번 지켜야 한다.
- RLS는 정책 식을 쿼리의 조건으로 끼워 넣는다. 정책 식은 **사용자 조건·함수보다 먼저** 행마다 평가된다. 예외는 leakproof 함수뿐이다(PostgreSQL 17 5.9).

```text
  SELECT * FROM orders WHERE amount > 150
  → WHERE (정책: tenant_id = 설정값)  AND  (amount > 150)
            먼저                           나중
```

### 2. 누가 받나, 정책이 없으면

| 롤 | 정책 적용 |
|---|---|
| 슈퍼유저 | 항상 우회 |
| BYPASSRLS | 항상 우회 |
| 테이블 소유자 | FORCE가 없으면 우회 |
| 일반 롤 | 적용 |

- 정책 없이 RLS만 켜면 default-deny다. 일반 롤은 **0행**이다.
- 소유자는 FORCE가 없으면 RLS 자체를 받지 않으므로 **전체 행**이 보인다(로컬 재현: 일반 롤 0행, 소유자 3행).

### 3. FOR ALL + USING만

- `FOR ALL`(또는 `FOR UPDATE`) 정책에 WITH CHECK가 없으면 USING을 WITH CHECK로도 쓴다(CREATE POLICY 문서).
- 그래서 INSERT는 `ERROR: new row violates row-level security policy for table "orders"`로 **거부된다.** `UPDATE … SET tenant_id = 2`도 같은 에러다(로컬 재현).
- 구멍은 **명령별로 쪼갠 정책**에서 생긴다.
  - 예: `FOR SELECT USING (tenant = 설정값)` + `FOR INSERT WITH CHECK (true)`.
  - 테넌트 1이 `tenant_id = 2` 행을 넣을 수 있다. 자기는 못 보지만 테넌트 2에게는 보인다(로컬 재현).
- 원본 「기본 사용법 — USING vs WITH CHECK」의 "USING만 있으면 INSERT 가능"은 이 경우로 한정해야 맞다.

### 4. PERMISSIVE 예외 정책

- 기본값은 PERMISSIVE다. PERMISSIVE끼리는 **OR**로 합쳐진다.
- `admin이면 통과`를 더하면 admin 세션은 테넌트 조건과 무관하게 **전체**를 본다(로컬 재현: 3행).
- 좁히려면 `AS RESTRICTIVE`로 만든다. RESTRICTIVE끼리는 AND이고, PERMISSIVE 묶음과도 AND다.
- PERMISSIVE가 하나도 없고 RESTRICTIVE만 있으면 아무것도 안 보인다(CREATE POLICY 문서).

### 5. 세션 변수의 수명

```text
  ① 새 세션                 NULL
  ② SET LOCAL 트랜잭션 안    '1'
  ③ 커밋 뒤                  ''   (빈 문자열)
```

- `missing_ok = true`는 설정이 **존재하지 않을 때만** NULL이다. ②에서 설정이 세션에 생긴 뒤에는 기본값 `''`가 나온다. `DISCARD ALL` 뒤에도 `''`였다(로컬 재현).
- ③에서 캐스트 정책은 `ERROR: invalid input syntax for type bigint: ""`를 낸다. 0행이 아니라 에러로 닫힌다.
- 한 가지로 맞추려면 `NULLIF(current_setting('app.tenant_id', true), '')::bigint`. ③이 0행이 됐다(로컬 재현).

### 6. 간헐적 교차 노출

- 의심: 어떤 경로가 세션 범위 `SET app.tenant_id = …`를 쓰고, 다른 경로는 주입을 빠뜨렸다. 풀이 커넥션을 재사용한다.
  - HikariCP는 반납 시 readOnly·autoCommit·isolation·catalog·networkTimeout·schema만 되돌린다. 커스텀 GUC는 남는다(`ProxyConnection.java`).
  - 로컬 재현: `SET` 후 설정을 빠뜨린 다음 "요청"이 직전 테넌트의 2행을 봤다.
- 막기
  - `SET LOCAL` 또는 `set_config(…, true)`만 쓴다. 트랜잭션 시작 훅에서 강제로 넣는다.
  - PgBouncer 트랜잭션 풀링에서는 세션 `SET`이 호환되지 않는다(features 표 "Never").
  - 주입 누락은 0행이나 에러가 되게 정책을 쓴다(5번). 단 세션 범위 `SET` 값이 남아 있으면 `NULLIF`는 그 값을 통과시키므로, 세션 `SET`을 없애는 것이 먼저다.

### 7. 뷰만 3행

- 기본 뷰는 기반 테이블의 RLS를 **뷰 소유자** 기준으로 적용한다(CREATE VIEW 문서). 뷰 소유자가 테이블 소유자이고 FORCE가 없으면 우회한다.
- 고치는 법
  - 뷰를 `WITH (security_invoker = true)`로 만든다. 호출자 기준이 된다(로컬 재현: 2행).
  - 테이블에 `FORCE ROW LEVEL SECURITY`를 건다. 소유자 기준 뷰도 정책을 받는다(로컬 재현: 2행).

### 8. 존재가 드러나는 경로

- **유니크·PK·FK 검사**는 항상 RLS를 우회한다(문서 5.9). 다른 테넌트의 id로 INSERT하면 `duplicate key value violates unique constraint`가 난다(로컬 재현).
- **FK 참조 성공/실패**도 같은 원리다. 남의 행을 참조하는 INSERT가 통과하면 그 행이 있다는 뜻이다.
- 정책으로 못 막는 이유: 무결성 검사는 데이터 정합성을 위해 정책 밖에서 전체 테이블을 본다. 스키마로 줄인다. `(tenant_id, 키)` 복합 유니크를 쓰고, 외부 ID는 추측할 수 없게 둔다.

### 9. `invoices` 누출 점검

```sql
-- ① RLS가 켜져 있나
SELECT relname, relrowsecurity, relforcerowsecurity, pg_get_userbyid(relowner)
  FROM pg_class WHERE relname = 'invoices';
-- ② 정책이 있나, 무엇인가
SELECT policyname, permissive, cmd, qual, with_check FROM pg_policies WHERE tablename = 'invoices';
-- ③ 앱 롤이 우회 롤인가
SELECT rolname, rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user;
```

- 확인 순서: RLS 꺼짐(`relrowsecurity = f`) → 정책 없음 → 앱 롤 = 소유자 + FORCE 없음 → 슈퍼유저·BYPASSRLS → 뷰 경유.
- 로컬 재현: RLS를 빠뜨린 `invoices`는 테넌트 1 세션에서 두 테넌트 행 전부를 돌려줬다. `NOT relrowsecurity` 감사 쿼리가 찾아냈다.
- 재발 방지: 테넌트 컬럼이 있는 테이블의 `relrowsecurity`를 CI에서 검사한다.

### 10. 캐스트 누락과 인덱스 확인

- PostgreSQL 17에는 `bigint = text` 연산자가 없다. 그래서 `CREATE POLICY` 자체가 `ERROR: operator does not exist: bigint = text`로 실패한다(로컬 재현). 계획이 나빠지는 단계까지 가지 않는다.
- 확인: 앱과 같은 롤·같은 설정으로 `EXPLAIN (ANALYZE, BUFFERS)`를 본다.
  - 정책 술어가 `Index Cond: (tenant_id = (current_setting('app.tenant_id'::text, true))::bigint)`로 나오면 인덱스를 탄 것이다(로컬 재현).
  - `current_setting`이 STABLE이라 인덱스 키로 쓸 수 있다.
  - 인덱스는 `(tenant_id, 정렬 컬럼)`처럼 테넌트를 선두에 둔다.
