# database/43-row-level-security — 행 수준 보안: 정책 술어로 테넌트를 DB가 가른다 — 정리 (힌트)

## 해결하는 문제

여러 테넌트(고객사)의 행이 한 테이블에 섞여 있다.\
격리는 쿼리마다 붙는 `WHERE tenant_id = ?` 한 줄에 달려 있다.\
이 한 줄이 빠진 쿼리 하나가 전체 테넌트의 데이터를 돌려준다.

```text
  orders
  ┌────┬───────────┬────────┐
  │ id │ tenant_id │ amount │     SELECT * FROM orders WHERE tenant_id = 1;   → 2행 (정상)
  ├────┼───────────┼────────┤
  │ 1  │ 1         │ 100    │     SELECT * FROM orders;                        → 3행 (누출)
  │ 2  │ 1         │ 200    │       └ 조건을 빠뜨린 한 줄. 에러도 경고도 없다
  │ 3  │ 2         │ 300    │
  └────┴───────────┴────────┘
```

쉬운 예: 아파트 우편함이 하나로 합쳐져 있다. 관리인이 "몇 호 것만 달라"는 말을 매번 정확히 들어야 남의 편지가 안 섞인다.\
똑같은 구조다. 조건을 사람(코드)이 매번 붙이면 언젠가 빠진다.\
**행 수준 보안(RLS)**은 조건을 테이블 쪽에 붙여 둔다. 쿼리가 무엇이든 DB가 그 조건을 더한다.

실무 예:
- SaaS의 공유 스키마(pool 모델) 테이블. 관리 화면·배치·네이티브 쿼리에서 테넌트 조건이 빠진다.
- 이 기능의 기초(왜 필요한가, USING/WITH CHECK, 풀 함정, ORM 이중 방어)는 원고 [systems/postgres-rls](../../systems/postgres-rls/2-summary.md)에 있다. 이 노트는 **엔진이 정책을 어떻게 끼워 넣는지**, **어디서 우회되는지**, **운영에서 어떻게 깨지는지**를 채운다.
- 격리 모델 전체(사일로·풀·브리지)는 [systems/multi-tenancy](../../systems/multi-tenancy/2-summary.md)에 있다.

> 제품 한정: 이 노트의 RLS는 **PostgreSQL 17** 기능이다. MySQL 8.4에는 `CREATE POLICY` 같은 행 수준 정책 문법이 없다(8.4 매뉴얼 15.1 Data Definition Statements 목록에 정책 문이 없다). MySQL에서는 뷰·저장 프로그램·애플리케이션 필터로 대신한다.

## 동작·원리

### 1. 정책은 쿼리에 붙는 술어다

```text
  사용자 쿼리                          플래너가 실제로 실행하는 것
  SELECT * FROM orders           →   SELECT * FROM orders
  WHERE amount > 150                   WHERE (tenant_id = current_setting('app.tenant_id', true)::bigint)  ← 정책 술어 (먼저)
                                         AND (amount > 150)                                                ← 사용자 조건 (나중)
```

- *정책(policy)*: `CREATE POLICY`로 테이블에 거는 불리언 식. 행마다 참이어야 그 행이 보이거나 쓰인다.
- *술어(predicate)*: 참·거짓을 돌려주는 조건식. 플래너 용어로는 qual이다.
- 문서: 정책 식은 **사용자 쿼리의 조건·함수보다 먼저** 행마다 평가된다. 예외는 leakproof 함수뿐이다(PostgreSQL 17 5.9).
- 로컬 재현(예시, PostgreSQL 17.11): 정책이 걸린 20만 행 테이블에서 `ORDER BY created_at DESC LIMIT 20`의 계획은 `Index Scan Backward using ev_t_c`, `Index Cond: (tenant_id = (current_setting('app.tenant_id'::text, true))::bigint)`였다. 정책 술어가 인덱스 조건으로 들어갔다.
  - `current_setting`은 STABLE 함수다(`pg_proc.provolatile = 's'`). 한 문장 안에서 값이 바뀌지 않으므로 인덱스 스캔 키로 쓸 수 있다.

### 2. 누가 정책을 적용받나

```text
  접속 롤                                   정책 적용?    로컬 재현 (orders 3행, 테넌트 1 = 2행)
  슈퍼유저                                  ✗ 항상 우회   3행
  BYPASSRLS 속성 롤                          ✗ 항상 우회   (문서)
  테이블 소유자 (FORCE 없음)                  ✗ 우회        3행 — 정책이 없어도 3행
  테이블 소유자 + FORCE ROW LEVEL SECURITY    ○             정책 적용
  일반 롤 + 정책 없음                        ○ 기본 거부    0행 (default-deny)
  일반 롤 + 정책                            ○             2행
```

- *BYPASSRLS*: RLS를 건너뛰는 롤 속성. 슈퍼유저는 이것 없이도 건너뛴다.
- *FORCE ROW LEVEL SECURITY*: 소유자에게도 정책을 적용하게 하는 테이블 설정.
- *default-deny*: RLS를 켰는데 정책이 하나도 없으면 아무 행도 보이거나 바뀌지 않는다(문서 5.9).
- 문서의 말: 소유자는 "보통(typically)" 정책을 받지 않는다. RLS를 켜고 끄는 것과 정책 추가는 소유자만 할 수 있다.
- 그래서 **앱이 소유자 롤로 접속하면 RLS는 없는 것과 같다.** 마이그레이션 롤(소유자)과 런타임 롤을 나눈다.

### 3. USING과 WITH CHECK — 명령별로 다르다

```text
                 기존 행을 고를 때 (USING)     새 행·바뀐 행을 넣을 때 (WITH CHECK)
  SELECT          ○                             —
  INSERT          —                             ○   실패 시 에러
  UPDATE          ○ (안 보이면 조용히 0행)        ○   실패 시 에러
  DELETE          ○ (안 보이면 조용히 0행)        —
```

- USING이 거짓인 행은 **에러 없이 안 보인다.** (예외: `INSERT … ON CONFLICT DO UPDATE`의 기존 행이 UPDATE 정책 USING을 통과 못 하면 에러다. `MERGE`의 UPDATE 동작도 갱신된 행이 SELECT 정책을 어기면 에러다 — CREATE POLICY 문서.) WITH CHECK가 거짓이면 **에러**다: `new row violates row-level security policy for table "orders"`(로컬 재현).
- `FOR ALL`·`FOR UPDATE` 정책에 WITH CHECK를 안 쓰면 **USING 식을 WITH CHECK로도 쓴다**(CREATE POLICY 문서).
  - 로컬 재현: `FOR ALL USING (tenant_id = 설정값)`만 건 상태에서 테넌트 1 세션의 `INSERT (…, tenant_id=2, …)`와 `UPDATE … SET tenant_id = 2`가 모두 위 에러로 거부됐다.
  - > 참고: 원본 「기본 사용법 — USING vs WITH CHECK」의 "`USING`만 있으면 남의 테넌트 ID로 INSERT가 가능하다"는 명령별 정책을 따로 나눴을 때의 이야기다. `FOR ALL` 정책 하나라면 USING이 쓰기에도 적용된다(CREATE POLICY 문서, 로컬 재현).
- 구멍이 실제로 생기는 모양은 **명령별로 쪼갠 정책**이다.
  - 로컬 재현: `FOR SELECT USING (tenant=설정값)` + `FOR INSERT WITH CHECK (true)`. 테넌트 1 세션이 `tenant_id = 2` 행을 넣었다. 자기는 그 행을 못 보지만 테넌트 2 세션에서는 그 행이 보였다(남의 테넌트에 데이터 심기).

### 4. 정책 여러 개 — PERMISSIVE는 OR, RESTRICTIVE는 AND

```text
  최종 조건 = (PERMISSIVE₁ OR PERMISSIVE₂ OR …) AND RESTRICTIVE₁ AND RESTRICTIVE₂ …
             PERMISSIVE가 하나도 없으면 → 거부
```

- *PERMISSIVE*(기본값): 볼 수 있는 행을 **넓힌다.** 여러 개면 OR.
- *RESTRICTIVE*: 볼 수 있는 행을 **좁힌다.** 여러 개면 AND.
- 로컬 재현(예시): 테넌트 정책 옆에 `AS PERMISSIVE USING (current_setting('app.role', true) = 'admin')`을 더하자 admin 세션에서 3행 전부가 보였다. 대신 `AS RESTRICTIVE USING (amount < 250)`을 더하면 테넌트 1은 2행, 테넌트 2는 0행이었다.
- "관리자 예외" 정책을 PERMISSIVE로 더하면 그 조건 하나로 **모든 테넌트가 열린다.** 좁히는 조건은 RESTRICTIVE로 쓴다.

### 5. 세션 변수의 수명 — NULL이 아니라 빈 문자열이 남는다

```text
  같은 커넥션(세션)의 시간 흐름                      current_setting('app.tenant_id', true)
  ① 새 세션, 한 번도 설정 안 함                      NULL
  ② BEGIN; SET LOCAL app.tenant_id = '1'; …        '1'
  ③ COMMIT (SET LOCAL 효과 끝)                      ''   ← 빈 문자열. NULL이 아니다
  ④ DISCARD ALL                                    ''   ← 그대로
     정책의 ''::bigint                              ERROR: invalid input syntax for type bigint: ""
```

- `missing_ok = true`는 "그런 설정이 **없을 때**" NULL을 준다(함수 문서). ② 이후에는 설정이 세션에 생겨 있으므로 기본값 `''`가 나온다(로컬 재현).
- 트랜잭션 밖의 `SET LOCAL`은 "경고를 내고 아무 효과가 없다"(SET 문서). 로컬 재현에서는 `WARNING: SET LOCAL can only be used in transaction blocks` 뒤에 값이 `''`였다.
- 그래서 캐스트가 있는 정책은 풀 커넥션 위에서 "조용한 빈 결과"가 아니라 **에러**로 닫힌다. 둘 다 fail-closed다. 어느 쪽이 될지는 그 세션의 이력에 달렸다.
  - *fail-closed*: 설정이 없거나 틀리면 "막힘" 쪽으로 떨어지는 것.
- 한 가지로 맞추려면 `NULLIF(current_setting('app.tenant_id', true), '')::bigint`로 쓴다. 로컬 재현에서 ③ 상태가 에러 대신 0행이 됐다.
- 반대로 **세션 범위 `SET`**은 트랜잭션이 끝나도 남는다.
  - 로컬 재현: 요청 A가 `SET app.tenant_id = '1'` 후 반납. 같은 커넥션을 받은 요청 B가 설정을 빠뜨리자 테넌트 1의 2행을 그대로 봤다. 에러는 없었다.

### 6. 뷰와 무결성 검사 — 정책을 비켜 가는 길

```text
  w31_app ──SELECT──> v_orders (소유자 w31_owner) ──> orders
                       │
                       └ 기본: 뷰 소유자의 권한·정책으로 orders를 읽는다
                         소유자는 RLS 우회(FORCE 없음) → 3행 전부      (로컬 재현)
                         security_invoker = true 뷰 → 호출자 기준 → 2행 (로컬 재현)
                         FORCE를 걸면 소유자 뷰도 2행                    (로컬 재현)
```

- CREATE VIEW 문서: 기반 테이블에 RLS가 있으면 기본으로 **뷰 소유자의** 정책이 적용된다. `security_invoker`를 켜면 호출자의 정책이 적용된다.
- 문서 5.9: **참조 무결성 검사**(유니크·PK·FK)는 항상 RLS를 우회한다. 존재 여부가 "covert channel"로 샐 수 있다.
  - *covert channel*: 정식 결과가 아닌 부수 신호(에러, 시간)로 정보가 새는 통로.
  - 로컬 재현: 테넌트 1 세션이 테넌트 2의 행 id 3으로 INSERT하자 `duplicate key value violates unique constraint "orders_pkey"`. 테넌트 1은 "id 3이 어딘가 있다"를 알게 된다.
- `TRUNCATE`·`REFERENCES`처럼 테이블 전체에 대한 작업도 RLS 대상이 아니다(문서 5.9).

## 쓰이는 자료구조·알고리즘

- **정책 술어 = 쿼리 트리의 필터 삽입**
  - 플래너는 정책 식을 보안 조건으로 먼저 붙이고, 사용자 조건은 그 뒤에 둔다.
  - 사용자 조건을 먼저 평가해도 되는 것은 leakproof 연산자·함수뿐이다(`pg_proc.proleakproof`).
  - 로컬 재현: `int8eq`는 leakproof `t`, `textlike`는 `f`였다.
  - `RAISE NOTICE`로 인자를 찍는 비-leakproof 함수(COST 0.0001)를 WHERE에 넣어도, 찍힌 것은 자기 테넌트 행 2개뿐이었다.
- **B+트리 복합 인덱스 `(tenant_id, …)`** — 정책 술어가 모든 쿼리의 등호 조건이 되므로 선두 컬럼에 둔다. 로컬 재현 계획이 `Index Cond`로 정책 술어를 탔다. [data-structure/15-b-tree](../../data-structure/15-b-tree/2-summary.md)
- **파티션 프루닝** — `tenant_id`가 파티션 키면 정책 술어로 파티션을 거를 수 있다(원본 「함정 ② 정책 평가 비용」). 분할은 [33-partitioning-and-sharding](../33-partitioning-and-sharding/2-summary.md)(원고: [systems/partitioning-vs-sharding](../../systems/partitioning-vs-sharding/2-summary.md)).
- **정책 결합 = 불리언 식 조립** — `(P₁ ∨ P₂ …) ∧ R₁ ∧ R₂ …`. PERMISSIVE가 비면 거짓.

## 적용 — 풀어나가는 법

### 1. 켜는 순서 (PostgreSQL 17)

```sql
-- 마이그레이션 롤(소유자)로
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders FORCE  ROW LEVEL SECURITY;            -- 소유자도 적용
CREATE POLICY tenant_isolation ON orders
  USING      (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::bigint)
  WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::bigint);
GRANT SELECT, INSERT, UPDATE, DELETE ON orders TO app_rw; -- 런타임 롤: 소유자 아님, BYPASSRLS 없음
```

- 캐스트 `::bigint`를 빼면 계획이 나빠지는 것이 아니라 **정책 생성이 실패한다**: `ERROR: operator does not exist: bigint = text`(로컬 재현).
  - > 참고: 원본 「함정 ② 정책 평가 비용」의 "캐스팅을 빠뜨리면 text와 bigint 비교로 남아 인덱스를 못 탈 수 있다"는 PostgreSQL 17에서 재현되지 않았다. `bigint = text` 연산자가 없어 `CREATE POLICY`가 거부됐다.

### 2. 요청마다 트랜잭션 안에서 주입 (Java)

```java
// Spring: @Transactional 메서드 안, 첫 쿼리 전에. 같은 트랜잭션·같은 커넥션이어야 한다
@Transactional
public List<Order> list(long tenantId) {
    jdbc.queryForObject("SELECT set_config('app.tenant_id', ?, true)",   // true = 트랜잭션 범위
                        String.class, Long.toString(tenantId));
    return jdbc.query("SELECT * FROM orders ORDER BY created_at DESC LIMIT 20", mapper);
}
```

- HikariCP는 반납 시 JDBC 표준 상태만 되돌린다. 소스의 dirty bit는 readOnly·autoCommit·isolation·catalog·networkTimeout·schema 여섯이다(`ProxyConnection.java`). **커스텀 GUC는 되돌리지 않는다.** 세션 범위 `SET`이 남는 이유다.
- PgBouncer 트랜잭션 풀링은 세션 범위 `SET/RESET`을 "Never" 호환으로 표시한다(PgBouncer features). `SET LOCAL`·`set_config(…, true)`만 쓴다.
- ORM 필터(`@TenantId`·`@Filter`)는 원본 「이중 방어선 — ORM 레벨 (Hibernate)」. Hibernate 6.6 가이드: 필터는 엔티티 쿼리에 적용되고, **직접 조회(find by id)에는 `applyToLoadByKey`를 켜지 않으면 적용되지 않는다.**

### 3. 감사 쿼리 — 빠진 곳을 찾는다

```sql
-- RLS가 꺼진 테이블 (테넌트 컬럼이 있는데 여기 나오면 누출 후보)
SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
 WHERE n.nspname = 'public' AND c.relkind IN ('r','p') AND NOT c.relrowsecurity;
-- FORCE 여부와 소유자
SELECT relname, relrowsecurity, relforcerowsecurity, pg_get_userbyid(relowner) FROM pg_class WHERE relname = 'orders';
-- 정책 목록: PERMISSIVE/RESTRICTIVE, 명령, 식
SELECT policyname, permissive, roles, cmd, qual, with_check FROM pg_policies WHERE tablename = 'orders';
-- 우회 가능한 롤
SELECT rolname FROM pg_roles WHERE rolsuper OR rolbypassrls;
-- 기본 뷰(security_invoker 없음) 목록
SELECT relname, reloptions FROM pg_class WHERE relkind = 'v';
```

- 로컬 재현: `invoices` 테이블을 만들고 RLS를 빠뜨리자 테넌트 1 세션에서 2행(두 테넌트 전부)이 보였다. 첫 감사 쿼리가 `invoices`를 찾아냈다.

### 4. 테스트 — "옆집"으로 4종 연산

```text
  테넌트 A 세션에서 B의 행에 대해:
  SELECT  → 0행            UPDATE → UPDATE 0      DELETE → DELETE 0
  INSERT (tenant_id = B)   → ERROR new row violates row-level security policy
  + 설정 없는 세션 → 0행 또는 에러 (둘 중 무엇인지 팀이 정한다)
  + 소유자 롤·뷰 경유 경로도 같은 시험
```

### 5. 백업·배치 — 정책이 조용히 행을 빼지 않게

- `SET row_security = off`는 RLS를 끄는 것이 아니다. **정책 때문에 결과가 걸러질 쿼리면 에러를 낸다**(문서 5.9). 로컬 재현: `ERROR: query would be affected by row-level security policy for table "orders"`.
- 백업·전체 집계 배치가 RLS에 걸려 일부 행만 담는 사고를 에러로 바꾼다.

## 장애 시나리오와 대처

### 1. 정책을 빠뜨린 테이블 → 테넌트 간 누출

- **현상**: 새로 만든 테이블의 목록 API가 다른 회사 데이터를 섞어 보여 준다.
- **보이는 형태**: 에러 없음. 테넌트 1 세션의 `SELECT count(*) FROM invoices`가 전체 행 수를 돌려준다(로컬 재현 2행).
- **원인**: 마이그레이션에서 `ENABLE ROW LEVEL SECURITY`와 `CREATE POLICY`를 빠뜨렸다. RLS는 켠 테이블에만 적용된다.
- **대처**
  - 긴급: 해당 테이블에 RLS와 정책을 걸고, 노출 기간의 접근 로그로 영향 범위를 확인한다.
  - 근본: 위 감사 쿼리를 CI나 배포 후 점검에 넣는다. `tenant_id` 컬럼이 있는데 `relrowsecurity = false`면 실패시킨다.

### 2. 소유자 롤로 접속 → RLS 우회

- **현상**: 정책도 있고 테스트도 통과했는데 운영에서 전체가 보인다.
- **보이는 형태**: `pg_policies`에 정책이 있다. 앱 롤 = 테이블 소유자이고 `relforcerowsecurity = f`다. 로컬 재현에서 소유자는 정책 유무와 상관없이 3행을 봤다.
- **원인**: 소유자는 기본으로 RLS를 받지 않는다. 슈퍼유저·BYPASSRLS 롤은 항상 우회한다(문서 5.9).
- **대처**
  - 런타임 롤을 분리한다(소유자 아님, BYPASSRLS 없음).
  - `FORCE ROW LEVEL SECURITY`를 건다. 로컬 재현에서 FORCE 뒤 소유자 뷰 경유도 2행이 됐다.
  - 테스트는 **운영과 같은 롤**로 돌린다.

### 3. 풀 커넥션에 남은 세션 변수 → 다른 테넌트로 보인다

- **현상**: 간헐적으로 A사 사용자 화면에 B사 데이터가 나온다. 재현이 어렵다.
- **보이는 형태**: 에러 없음. 해당 요청 경로에 테넌트 주입 코드가 빠져 있다. 같은 커넥션의 직전 요청이 세션 범위 `SET`을 썼다.
- **원인**: 세션 범위 `SET`은 커밋 후에도 남는다. 풀은 커스텀 GUC를 되돌리지 않는다(HikariCP dirty bit 목록).
- **대처**
  - `SET LOCAL`/`set_config(…, true)`만 쓴다. 트랜잭션 시작 훅에서 강제로 넣는다.
  - 주입이 빠진 경우를 "0행/에러"로 만든다. `NULLIF(…, '')` 정책은 0행, 캐스트만 쓴 정책은 `invalid input syntax for type bigint: ""` 에러다.
  - 단 이 안전망은 세션에 남은 값이 `''`일 때만 작동한다. 어딘가 세션 범위 `SET`이 남아 있으면 `NULLIF`는 그 값(`'1'`)을 그대로 통과시켜 교차 노출이 된다. 그래서 첫 항목(세션 `SET` 금지)이 먼저다.

### 4. 설정이 빈 문자열이 되어 전 요청이 500

- **현상**: 배포 뒤 일부 인스턴스에서만 `500`이 급증한다. 새 커넥션에서는 괜찮다.
- **보이는 형태**: `ERROR: invalid input syntax for type bigint: ""`(SQLSTATE 22P02). 스택은 정책이 걸린 테이블의 평범한 SELECT다.
- **원인**: 그 커넥션에서 한 번 `SET LOCAL`을 한 뒤, 주입 없이 쿼리가 나갔다. 설정이 `''`로 남아 캐스트가 실패했다(위 5절).
- **대처**: 정책 식을 `NULLIF(current_setting(…, true), '')::bigint`로 바꾸고, 주입 누락은 앱에서 먼저 막는다. 에러 쪽을 원하면 팀 규칙으로 명시한다.

### 5. 뷰·무결성 검사로 새는 정보

- **현상**: 테이블 직접 조회는 막히는데 리포트 뷰에서는 전체가 보인다. 또는 회원 가입에서 "이미 있는 ID"로 다른 테넌트의 존재가 드러난다.
- **보이는 형태**: 뷰 조회 3행(로컬 재현). `duplicate key value violates unique constraint "orders_pkey"`.
- **원인**: 기본 뷰는 뷰 소유자 기준으로 정책을 적용한다. 유니크·PK·FK 검사는 항상 RLS를 우회한다.
- **대처**
  - 뷰에 `security_invoker = true`를 쓴다(CREATE VIEW 문서).
  - 전역 유니크 대신 `(tenant_id, 자연키)` 복합 유니크를 쓴다. 외부 노출 ID는 추측할 수 없는 값으로 둔다.

## 핵심 문장

- RLS는 정책 식을 모든 쿼리의 조건으로 **먼저** 끼워 넣는다. 조건을 빠뜨린 쿼리도 DB가 거른다.
- 슈퍼유저·BYPASSRLS는 항상, 테이블 소유자는 FORCE가 없으면 우회한다. 앱은 소유자가 아닌 롤로 접속한다.
- `FOR ALL` 정책의 USING은 WITH CHECK가 없으면 쓰기에도 쓰인다. 구멍은 명령별로 쪼갠 정책에서 생긴다.
- PERMISSIVE는 OR로 넓히고 RESTRICTIVE는 AND로 좁힌다. 예외 정책을 PERMISSIVE로 더하면 전체가 열린다.
- 커스텀 설정은 한 번 쓰면 세션에 `''`로 남는다. 세션 `SET`은 풀에서 다음 요청으로 샌다. `SET LOCAL` + `NULLIF`로 닫는다.
- 뷰(기본 소유자 기준)와 무결성 검사(항상 우회)는 정책을 비켜 간다. 감사 쿼리와 "옆집 4종 연산" 테스트로 막는다.

## 관련 주제·근거

- 선행
  - [02-keys-and-constraints](../02-keys-and-constraints/2-summary.md) — 유니크·FK 검사가 RLS를 우회하는 이유의 바탕
  - [security/15-access-control-models](../../security/15-access-control-models/2-summary.md) — 객체 수준 인가.
- 원고·연결
  - [systems/postgres-rls](../../systems/postgres-rls/2-summary.md) — 기초(USING/WITH CHECK, 풀 함정, ORM 이중 방어, 체크리스트)
  - [systems/multi-tenancy](../../systems/multi-tenancy/2-summary.md) — 격리 모델, 권한 누수 L1~L8
  - [21-connection-pooling](../21-connection-pooling/2-summary.md) — 풀과 세션 상태
  - [12-query-optimizer-and-explain](../12-query-optimizer-and-explain/2-summary.md) — 정책 술어가 들어간 계획 읽기
- PostgreSQL 17 문서
  - 5.9 Row Security Policies(소유자·BYPASSRLS·default-deny·정책 평가 순서·무결성 검사 우회·`row_security`) <https://www.postgresql.org/docs/17/ddl-rowsecurity.html>
  - CREATE POLICY(PERMISSIVE/RESTRICTIVE 결합, USING을 WITH CHECK로 재사용, 명령별 적용 표) <https://www.postgresql.org/docs/17/sql-createpolicy.html>
  - CREATE VIEW(`security_invoker`·`security_barrier`) <https://www.postgresql.org/docs/17/sql-createview.html>
  - SET(`SET LOCAL`의 범위, 트랜잭션 밖 경고) <https://www.postgresql.org/docs/17/sql-set.html>
  - 9.28 시스템 관리 함수 `current_setting(…, missing_ok)`·`set_config(…, is_local)` <https://www.postgresql.org/docs/17/functions-admin.html>
- 풀·ORM
  - HikariCP `src/main/java/com/zaxxer/hikari/pool/ProxyConnection.java`(DIRTY_BIT 6종) <https://github.com/brettwooldridge/HikariCP>
  - PgBouncer Features — SQL feature map(트랜잭션 풀링에서 SET/RESET "Never") <https://www.pgbouncer.org/features.html>
  - MySQL 8.4 15.1 Data Definition Statements(행 수준 정책 문 없음) <https://dev.mysql.com/doc/refman/8.4/en/sql-data-definition-statements.html>
  - Hibernate ORM 6.6 User Guide — Filters("not to direct fetching … applyToLoadByKey"), 23.3.1 `@TenantId`
- 로컬 재현(PostgreSQL 17.11, DB `w31`): 롤별 가시성(슈퍼유저·소유자·앱 롤·default-deny), FOR ALL USING의 쓰기 거부, 명령별 정책의 INSERT 구멍, PERMISSIVE/RESTRICTIVE 결합, 세션 변수 수명(NULL → `''` → 캐스트 에러, DISCARD ALL 후 `''`), 세션 SET의 요청 간 누출, 캐스트 누락 시 `CREATE POLICY` 실패, 소유자 뷰·`security_invoker` 뷰·FORCE, 유니크 위반 covert channel, `row_security = off` 에러, 정책 술어 인덱스 계획, 비-leakproof 함수의 평가 순서, RLS 누락 테이블 감사
