# database/09-index-design — 인덱스 설계: 복합·커버링·부분·표현식, 선택도 — 정리 (힌트)

## 해결하는 문제

B+Tree 인덱스(08번)가 무엇인지 알아도, **어떤 인덱스를 만들지**는 따로 정해야 한다.\
인덱스는 쿼리마다 맞는 모양이 다르다. 모양이 안 맞으면 인덱스가 있어도 쓰이지 않는다. 반대로 인덱스를 많이 만들면 쓰기가 느려진다.

쉬운 예: 전화번호부다.
- 전화번호부는 "성 → 이름" 순서로 정렬돼 있다.
- "김씨 중 이름이 민수"는 금방 찾는다.
- "이름이 민수인 사람 전부"는 첫 장부터 끝까지 넘겨야 한다. 정렬의 첫 기준(성)이 빠졌기 때문이다.
- 전화번호부를 "이름순"으로 하나 더 만들면 찾기는 빨라진다. 대신 새 사람이 이사 올 때마다 두 권을 고쳐야 한다.

똑같은 구조다.\
복합 인덱스 `(tenant_id, created_at)`는 "tenant_id → created_at" 순서의 전화번호부다. 인덱스를 하나 더 만들 때마다 `INSERT`·`UPDATE`가 고칠 곳이 하나 는다.

실무 예:
- 멀티 테넌트 서비스에서 `WHERE created_at >= ?`만으로 최근 이벤트를 찾는 배치가 풀스캔을 한다. 인덱스는 `(tenant_id, created_at)` 하나뿐이다.
- "혹시 몰라" 만든 인덱스 여러 개 때문에 적재 배치가 눈에 띄게 느려진다.
- `WHERE lower(email) = ?`로 로그인하는데 인덱스는 `email`에만 있다.

## 동작·원리

### 1. 복합 인덱스 — 정렬 순서가 곧 쓸 수 있는 조건이다

```text
  인덱스 (tenant_id, created_at) 의 리프 = 사전순으로 정렬된 (키, 행 위치) 목록

  (41, 03-07 10:00) ...
  (42, 01-01 00:42) ┐
  (42, 01-01 08:62) │  tenant_id = 42 인 항목은 한 구간에 붙어 있다
  (42, 03-01 ...)   │  그 안에서 created_at 순서다
  (42, 03-07 ...)   ┘
  (43, 01-01 00:43) ...

  WHERE tenant_id = 42 AND created_at BETWEEN a AND b  → 한 구간만 읽는다
  WHERE created_at BETWEEN a AND b                    → 구간이 테넌트마다 흩어져 있다
```

- PostgreSQL 17 문서 11.3의 규칙은 이렇다. **선행 컬럼들의 등호 조건**과, 등호가 없는 **첫 컬럼의 부등호 조건**이 읽을 범위를 줄인다. 그 오른쪽 컬럼의 조건은 인덱스 안에서 걸러 힙 방문만 줄인다. 읽는 범위는 줄이지 못한다.
  - *선행 컬럼*: 복합 인덱스에서 왼쪽에 있는 컬럼. 정렬의 첫 기준이다.
- 선행 컬럼이 빠진 조건은 원칙적으로 인덱스 전체를 훑어야 한다. 그래서 대부분 테이블 순차 스캔이 선택된다(같은 절).
- 로컬 재현(예시, PostgreSQL 17.11, 20만 행, `tenant_id` 500종)

```text
  WHERE tenant_id=42 AND created_at in [03-01, 03-08)
    → Bitmap Index Scan on ev_tenant_created   rows=20   0.24 ms

  WHERE created_at in [03-01, 03-02)
    → Parallel Seq Scan on ev   Rows Removed by Filter: 99280 (워커당)   15.9 ms
```

- **예외 — skip scan**: 선행 컬럼의 값 종류가 적으면, 값마다 "선행 = v AND 뒤 조건"을 반복 검색하는 방법이 있다.
  - MySQL 8.4는 이것을 지원한다(`optimizer_switch`의 `skip_scan`, 기본 on). 조건이 있다. 테이블 하나만 참조하고, `GROUP BY`·`DISTINCT`가 없고, **쿼리가 인덱스 컬럼만 참조**해야 한다(MySQL 8.4 10.2.1.2 Skip Scan).
  - 로컬 재현(예시, MySQL 8.4.10): `SELECT tenant_id, created_at … WHERE created_at …`은 `Covering index skip scan`을 썼다. 같은 조건에 `SELECT *`는 `Table scan`이었다.
  - PostgreSQL 17 B-tree에는 skip scan이 없다. 18 문서 11.3에서 처음 설명된다.

### 2. 커버링 인덱스 — 테이블에 가지 않는다

```text
  보통의 인덱스 스캔                     인덱스 전용 스캔 (index-only scan)
  인덱스 ──(행 위치)──> 힙 페이지         인덱스 ──> 끝
          랜덤 I/O 1회/행                 (PG는 가시성 맵 비트가 켜진 페이지만)
```

- 쿼리가 필요로 하는 컬럼이 모두 인덱스에 있으면 테이블(힙)을 읽지 않아도 된다.
  - *커버링 인덱스*: 특정 쿼리가 쓰는 컬럼을 모두 담은 인덱스.
- PostgreSQL은 `INCLUDE`로 검색 키가 아닌 "짐" 컬럼을 붙인다(PostgreSQL 17 11.9). `UNIQUE`는 키 컬럼에만 적용된다.
- **PostgreSQL의 함정 — 가시성**: 인덱스 항목에는 MVCC 가시성 정보가 없다. 그래서 힙 페이지가 가시성 맵에서 "all-visible"일 때만 힙 방문을 건너뛴다(11.9).
  - *가시성 맵(visibility map)*: 힙 페이지마다 "모든 트랜잭션에 보이는 행만 있다"를 비트 하나로 기록한 지도. VACUUM이 켠다.
- 로컬 재현(예시, PostgreSQL 17.11)

```text
  인덱스 (tenant_id, created_at), SELECT tenant_id, created_at WHERE tenant_id = 42 (400행)
  VACUUM 직후                    Index Only Scan  Heap Fetches: 0     Buffers: hit=4 read=1
  400행 UPDATE 직후(VACUUM 전)    Index Only Scan  Heap Fetches: 800   Buffers: hit=807
  다시 VACUUM                     Index Only Scan  Heap Fetches: 0     Buffers: hit=7

  SELECT ..., amount (인덱스에 없는 컬럼)    → Bitmap Heap Scan  Heap Blocks: exact=400
  INCLUDE (amount) 인덱스 추가 후           → Index Only Scan   Heap Fetches: 0
```

- MySQL InnoDB는 보조 인덱스 레코드마다 **PK 컬럼**을 함께 담는다(MySQL 8.4 17.6.2.1). 그래서 `(tenant_id, created_at)` 인덱스로 `SELECT id, tenant_id …`도 커버된다. 로컬 재현에서 `Covering index lookup`으로 나왔다. MySQL에는 `INCLUDE` 문법이 없다.

### 3. 부분 인덱스 — 필요한 행만 넣는다

```text
  status 분포: done 99% / pending 1%

  전체 인덱스 (status, created_at)     6184 kB   200,000 항목
  부분 인덱스 (created_at) WHERE status='pending'   64 kB   2,000 항목
                                   (로컬 재현, 예시)
```

- `WHERE` 술어를 만족하는 행만 인덱스에 넣는다(PostgreSQL 17 11.8). 작고, 해당 행이 아닌 쓰기는 이 인덱스를 고치지 않는다.
- 쿼리의 `WHERE`가 인덱스 술어를 **함의한다고 플래너가 알아볼 수 있어야** 쓰인다. 단순한 부등호 함의(`x < 1` → `x < 2`) 말고는 술어가 쿼리 조건의 일부와 그대로 일치해야 한다(11.8).
- 매칭은 계획 시점에 한다. 그래서 문서는 `x < ?` 같은 파라미터 절이 부분 인덱스와 맞지 않는다고 적는다(11.8).
  - 단 실제 값을 넣어 계획하는 *custom plan*이면 쓰일 수 있다. 값과 무관한 *generic plan*에서는 못 쓴다(로컬 재현, 예시 PostgreSQL 17.11: `PREPARE … status = $1`이 custom plan에서 `Index Scan using o_p`, `plan_cache_mode = force_generic_plan`에서 `Seq Scan`).
- MySQL 8.4에는 부분 인덱스가 없다. 비슷하게 하려면 생성 컬럼(값이 대상일 때만 non-NULL)에 인덱스를 거는 식으로 우회한다.

### 4. 표현식 인덱스 — 컬럼이 아니라 식을 정렬한다

```text
  인덱스 email:         'User42@Ex.com' 순서로 정렬
  WHERE lower(email)=…  → 인덱스의 정렬 기준과 다르다 → 탐색에 쓸 수 없다 (순차 스캔)

  인덱스 lower(email):  'user42@ex.com' 순서로 정렬
  WHERE lower(email)=…  → Index Scan using ev_email_lower  0.05 ms   (로컬 재현, 예시)
```

- 인덱스는 **저장된 값의 정렬**이다. 쿼리가 컬럼에 함수를 씌우면 그 결과의 순서는 인덱스가 모른다. 그래서 읽을 범위를 좁히는 탐색 조건으로는 쓸 수 없다(인덱스 전체를 훑으며 필터로 거르는 계획은 가능하다).
- 로컬 재현(예시, PostgreSQL 17.11): `date(created_at AT TIME ZONE 'UTC') = …`, `tenant_id::text = '42'`는 모두 `Seq Scan`이었다.
- 고치는 법은 둘이다. 쿼리를 인덱스에 맞추거나(범위 조건으로 다시 쓰기), 인덱스를 쿼리에 맞춘다(표현식 인덱스).
  - PostgreSQL: `CREATE INDEX ON ev (lower(email))`. 쓰기마다 식을 계산하므로 유지 비용이 더 든다(PostgreSQL 17 11.7).
  - MySQL 8.4: 함수 키 파트 `CREATE INDEX … ((lower(email)))` — 괄호를 한 겹 더 쓴다(MySQL 8.4 15.1.15 Functional Key Parts). 로컬 재현에서 `Index lookup on ev using ev_email_lower`로 쓰였다.

### 5. 선택도 — 인덱스가 이기는 구간은 좁다

```text
  선택도 = 조건을 만족하는 행 / 전체 행

  status = 'pending'   1%    → 인덱스 (랜덤 I/O 조금)
  status = 'done'     99%    → Seq Scan (순차 I/O 전부가 더 싸다)

  PG 통계 (pg_stats): status  most_common_vals {done,pending}
                              most_common_freqs {0.990, 0.0098}   (로컬 재현)
```

- 인덱스로 행을 찾으면 행마다 힙 페이지를 따로 방문한다. 많은 행을 가져올수록 그 랜덤 방문이 순차 스캔보다 비싸진다.
- 그래서 **선택도가 낮은(=걸러지는 행이 적은) 조건** 하나만으로는 힙을 방문하는 인덱스 스캔이 보통 쓰이지 않는다(커버링 인덱스의 인덱스 전용 스캔은 다를 수 있다, 11.9). 로컬 재현에서 `status='done'`은 인덱스가 있어도 `Seq Scan`이었다.
- 단, 같은 조건이라도 `ORDER BY created_at LIMIT 10`처럼 앞의 몇 행만 필요하면 인덱스 순서를 타는 쪽이 이긴다. 로컬 재현에서 `status='done' ORDER BY created_at LIMIT 10`은 `Index Scan using ev_status_full`이었다.
- 복합 인덱스 컬럼 순서의 기본 규칙:
  - 등호로 쓰는 컬럼을 앞에, 범위로 쓰는 컬럼을 뒤에 둔다(§1의 규칙에서 나온다).
  - 등호 컬럼들 사이에서는 선택도보다 **어떤 쿼리들이 공유하는가**가 중요하다. 선행 컬럼만 쓰는 쿼리도 이 인덱스를 쓸 수 있기 때문이다.

### 6. 인덱스의 비용 — 쓰기마다 전부 고친다

```text
  같은 20만 행 INSERT … SELECT (로컬 재현, 예시, PostgreSQL 17.11)

  테이블 w0: PK 1개                      WAL  34 MB    0.26 s
  테이블 w5: PK + 보조 인덱스 5개          WAL 121 MB    2.73 s
```

- 행 하나를 넣으면 그 행을 담는 인덱스마다 항목 하나를 넣는다(부분 인덱스는 술어를 만족하는 행만, 11.8). 인덱스가 늘면 WAL과 디스크 쓰기도 는다.
- PostgreSQL의 UPDATE는 새 행 버전을 만든다. 인덱스 컬럼이 안 바뀌고 같은 페이지에 자리가 있으면 **HOT 갱신**으로 인덱스를 건드리지 않는다(PostgreSQL 17 65.7). 인덱스 컬럼을 하나라도 바꾸면 HOT가 깨지고 **모든 인덱스**(부분 인덱스는 새 버전이 술어를 만족할 때만)에 새 항목이 들어간다. 단 BRIN 같은 요약(summarizing) 인덱스의 컬럼만 바뀐 경우는 HOT가 유지되고, 요약 인덱스만 갱신될 수 있다(PostgreSQL 17 65.7).
  - *HOT(Heap-Only Tuple)*: 인덱스 항목을 새로 만들지 않고 힙 안에서만 새 버전을 잇는 최적화.
- 인덱스는 버퍼 풀도 나눠 쓴다. 쓰지 않는 인덱스는 메모리와 쓰기만 먹는다.

## 쓰이는 자료구조·알고리즘

- **B+Tree의 사전순 정렬** — 복합 키 `(a, b)`는 a로 먼저, 같은 a 안에서 b로 정렬된다. "선행 컬럼 규칙"은 이 정렬에서 바로 나온다. [data-structure/15-b-tree](../../data-structure/15-b-tree/2-summary.md)
- **범위 스캔 = 한 번의 하강 + 리프 순회** — 시작 키까지 트리를 한 번 내려가고, 리프의 형제 링크를 따라 끝 키까지 읽는다. 연속 구간일 때만 한 번에 된다.
- **비트맵 힙 스캔** — 인덱스에서 모은 행 위치를 페이지 순서 비트맵으로 정렬한 뒤 힙을 한 번씩만 읽는다. 여러 인덱스의 결과를 AND/OR로 합칠 수도 있다(PostgreSQL 17 11.5).
- **통계(최빈값·히스토그램)** — 플래너가 선택도를 추정하는 재료다. 추정은 12번에서 다룬다.

## 적용 — 풀어나가는 법

### 1. 쿼리에서 출발한다

```text
  1) 느린 쿼리 목록을 뽑는다      pg_stat_statements / MySQL 슬로 쿼리 로그
  2) 쿼리마다 WHERE·JOIN·ORDER BY·SELECT 컬럼을 적는다
  3) 등호 컬럼 → 범위·정렬 컬럼 순으로 복합 인덱스 후보를 만든다
  4) SELECT 컬럼까지 담을지(커버링) 판단한다 — 쓰기가 잦으면 PG에선 이득이 줄어든다
  5) 기존 인덱스의 선행 부분과 겹치면 합친다  (a) 와 (a,b) → (a,b) 하나
     (단 (a)가 UNIQUE·PK면 (a,b)로 대신 못 한다 — 제약이 달라진다)
  6) EXPLAIN으로 확인하고, 쓰기 비용을 잰다
```

### 2. 확인 SQL

```sql
-- PostgreSQL 17: 계획과 실제 읽은 페이지
EXPLAIN (ANALYZE, BUFFERS)
SELECT tenant_id, created_at FROM ev WHERE tenant_id = 42;

-- 쓰이지 않는 인덱스 찾기 (통계 리셋 이후 누적)
SELECT indexrelname, idx_scan, pg_size_pretty(pg_relation_size(indexrelid))
FROM pg_stat_user_indexes WHERE relname = 'ev' ORDER BY idx_scan;

-- 운영 중 인덱스 추가 — 쓰기를 막지 않는다 (트랜잭션 블록 안에서는 불가)
CREATE INDEX CONCURRENTLY ev_pending ON ev (created_at) WHERE status = 'pending';
```

```sql
-- MySQL 8.4
EXPLAIN FORMAT=TREE SELECT * FROM ev WHERE tenant_id = 42 AND created_at >= '2026-03-01';
EXPLAIN ANALYZE     SELECT tenant_id, created_at FROM ev WHERE created_at >= '2026-03-01';

-- 지우기 전에 안 보이게 해 본다 (기본 설정에서 옵티마이저만 무시, 유지는 계속)
ALTER TABLE ev ALTER INDEX ev_email INVISIBLE;
SELECT * FROM sys.schema_unused_indexes WHERE object_schema = 'app';
```

- `CREATE INDEX CONCURRENTLY`는 테이블을 두 번 훑고, 기존 트랜잭션이 끝나기를 기다린다. 실패하면 **INVALID 인덱스가 남는다**. 이 인덱스는 조회에 안 쓰이지만 갱신 비용은 계속 낸다(PostgreSQL 17 CREATE INDEX). 지우고 다시 만든다.
- 보이지 않는 인덱스(invisible)는 MySQL 8.4 10.3.12. 기본 설정(`optimizer_switch`의 `use_invisible_indexes=off`)에서 옵티마이저가 무시할 뿐 쓰기 때마다 유지는 된다. 이 플래그를 켜면(`SET_VAR` 힌트 포함) 다시 계획 후보가 된다.

### 3. 앱 코드에서 인덱스를 깨는 흔한 모양

```java
// JPA: 인덱스는 email 컬럼인데 쿼리가 함수를 씌운다 → 순차 스캔
@Query("select u from User u where lower(u.email) = lower(:email)")
Optional<User> findByEmailIgnoreCase(String email);
// 해결 1) 저장 시 소문자로 정규화하고 where u.email = :email
// 해결 2) PG: CREATE INDEX ON users (lower(email))
```

- 타입이 다른 비교도 조심한다. 로컬 재현에서 `tenant_id::text = '42'`는 순차 스캔이었다. 드라이버가 숫자를 문자열로 바인딩하면 DB가 어느 쪽을 변환하는지에 따라 같은 일이 생길 수 있다. 실제 변환 방향은 제품·타입 조합마다 다르다 [?].

## 장애 시나리오와 대처

### 1. 복합 인덱스 선행 컬럼 누락 → 풀스캔

- **현상**: 관리자 화면의 "최근 1일 이벤트" 조회가 테이블이 커질수록 느려진다.
- **보이는 형태**: PostgreSQL `EXPLAIN`에 `Seq Scan` 또는 `Parallel Seq Scan`과 큰 `Rows Removed by Filter`. MySQL은 `Table scan on ev`. 슬로 쿼리 로그에 `Rows_examined`가 테이블 행 수만큼 찍힌다.
- **원인**: 인덱스는 `(tenant_id, created_at)`인데 쿼리에 `tenant_id` 조건이 없다. `created_at` 구간이 테넌트마다 흩어져 있다.
- **대처**
  - 이 쿼리가 자주 돈다면 `(created_at)` 인덱스를 따로 둔다.
  - MySQL 8.4에서는 선택 컬럼을 인덱스 컬럼으로 줄이면 skip scan이 될 수 있다. 조건이 까다로우니 `EXPLAIN`으로 확인한다.
  - 테넌트 목록이 짧으면 `tenant_id IN (…)`을 붙여 선행 컬럼을 채운다.

### 2. 인덱스 과다 → 쓰기가 느려진다

- **현상**: 적재 배치·주문 생성이 느리다. 읽기는 빠르다.
- **보이는 형태**: 같은 `INSERT`가 인덱스 수에 비례해 느려진다. 로컬 재현에서 보조 인덱스 5개를 더하자 WAL이 34 MB → 121 MB, 시간이 약 10배였다(예시). `pg_stat_user_indexes.idx_scan = 0`인 인덱스가 보인다.
- **원인**: 행마다 그 행을 담는 모든 인덱스에 항목을 넣는다. PostgreSQL에서는 인덱스 컬럼을 바꾸는 UPDATE가 HOT를 깨서 모든 인덱스(부분 인덱스는 술어를 만족할 때만)에 새 항목을 넣는다.
- **대처**
  - 안 쓰는 인덱스를 찾는다. 통계는 리셋 이후 누적값이고, 복제본에서 도는 쿼리는 그 서버의 통계에만 잡힌다는 점을 확인한 뒤 지운다.
  - `(a)`와 `(a, b)`처럼 선행이 겹치는 인덱스는 하나로 합친다. 단 `(a)`가 UNIQUE·PK면 제약 때문에 남긴다.
  - 대량 적재는 인덱스를 지우고 적재한 뒤 다시 만드는 편이 빠를 수 있다.

### 3. 컬럼에 함수 적용 → 인덱스 미사용

- **현상**: 로그인이 느리다. 이메일 대소문자 무시 비교를 넣은 뒤부터다.
- **보이는 형태**: `EXPLAIN`에 `Filter: (lower(email) = …)`와 `Seq Scan`.
- **원인**: 인덱스는 `email`의 정렬인데 쿼리는 `lower(email)`의 순서가 필요하다.
- **대처**: 저장 시 정규화하거나 표현식 인덱스를 만든다. PostgreSQL은 비교 규칙 자체를 바꾸는 `citext`·비결정 collation도 있다. collation은 10번에서 다룬다.

### 4. 커버링인데 힙을 읽는다 (PostgreSQL)

- **현상**: `Index Only Scan`인데 기대만큼 빠르지 않다.
- **보이는 형태**: `Heap Fetches:` 값이 반환 행 수와 비슷하거나 크다. 로컬 재현에서 UPDATE 직후 400행 조회에 `Heap Fetches: 800`이 나왔다.
- **원인**: 최근에 바뀐 페이지는 가시성 맵 비트가 꺼져 있다. 그래서 힙에서 가시성을 확인한다.
- **대처**: autovacuum이 따라가는지 본다(`pg_stat_user_tables.last_autovacuum`, `n_dead_tup`). 쓰기가 아주 잦은 테이블에는 `INCLUDE` 커버링의 이득이 작다고 보고 설계한다.

### 5. 운영 중 인덱스 생성 → 쓰기 정지 또는 INVALID 인덱스

- **현상**: 배포 중 `CREATE INDEX` 동안 주문 API가 멈춘다. 또는 `CONCURRENTLY`로 만들었는데 인덱스가 안 쓰인다.
- **보이는 형태**: PostgreSQL 일반 `CREATE INDEX`는 테이블에 `SHARE` 락을 잡아 쓰기를 막는다. `pg_locks`에 대기 행이 쌓인다. `CONCURRENTLY` 실패 후에는 `\d`에 `INVALID`가 보인다.
- **원인**: 일반 생성은 쓰기를 막는다. `CONCURRENTLY`는 교착·유일성 위반 등으로 실패하면 무효 인덱스를 남긴다(PostgreSQL 17 CREATE INDEX).
- **대처**: 운영 중에는 `CONCURRENTLY`를 쓰고, 실패하면 `DROP INDEX CONCURRENTLY` 후 다시 만든다.
  - PostgreSQL 17은 파티션 테이블(부모)에 `CONCURRENTLY`를 지원하지 않는다. 파티션마다 `CONCURRENTLY`로 만든 뒤 부모 인덱스를 일반 `CREATE INDEX`로 만든다(이때는 메타데이터만 바뀐다, CREATE INDEX). 무중단 스키마 변경 전반은 26번에서 다룬다.

## 핵심 문장

- 복합 인덱스는 사전순 정렬이다. 선행 컬럼의 등호 조건과 첫 범위 조건까지만 읽을 범위를 줄인다.
- 선행 컬럼이 빠지면 대체로 풀스캔이다. MySQL 8.4의 skip scan은 인덱스 컬럼만 조회하는 등 조건이 맞을 때의 예외다.
- 커버링 인덱스는 힙 방문을 없앤다. PostgreSQL에서는 가시성 맵이 켜진 페이지에서만 그렇다.
- 컬럼에 함수를 씌우면 그 컬럼의 인덱스로 범위를 좁히는 탐색을 못 한다. 쿼리를 고치거나 표현식 인덱스를 만든다.
- 선택도가 낮은 조건 하나로는 힙을 방문하는 인덱스 스캔이 대개 순차 스캔을 못 이긴다. 정렬+LIMIT처럼 앞 몇 행만 필요할 때는 다르다.
- 인덱스는 쓰기마다 고쳐야 하는 사본이다(HOT 갱신·술어 밖 행의 부분 인덱스는 예외). 안 쓰는 인덱스는 비용만 낸다.

## 관련 주제·근거

- 선행: [08-btree-indexes](../08-btree-indexes/2-summary.md)
- 후속·연결
  - [10-collation-and-text-comparison](../10-collation-and-text-comparison/2-summary.md)(비교 규칙과 인덱스) · [12-query-optimizer-and-explain](../12-query-optimizer-and-explain/2-summary.md)(선택도 추정) · [29-soft-delete-and-data-lifecycle](../29-soft-delete-and-data-lifecycle/2-summary.md)(부분 유니크 인덱스) · [26-schema-migration](../26-schema-migration/2-summary.md)(운영 중 인덱스 추가)
  - [40-filters-and-specialized-indexes](../40-filters-and-specialized-indexes/2-summary.md) — B+Tree로 안 되는 검색(`LIKE '%x%'`, 공간, BRIN)
  - [39-hash-indexes](../39-hash-indexes/2-summary.md) — 등호 전용 인덱스
  - SQL 문법 노트: [sql/46 인덱스 정의](../../../languages/sql/syntax/46-index-definition-composite-partial-expression/2-summary.md) · [sql/47 인덱스를 언제 타나](../../../languages/sql/syntax/47-when-indexes-are-used/2-summary.md)
  - [data-structure/15-b-tree](../../data-structure/15-b-tree/2-summary.md)
- 문서
  - PostgreSQL 17: 11.3 Multicolumn Indexes · 11.5 Combining Multiple Indexes · 11.7 Indexes on Expressions · 11.8 Partial Indexes · 11.9 Index-Only Scans and Covering Indexes · 65.7 Heap-Only Tuples · CREATE INDEX(`CONCURRENTLY`, INVALID) <https://www.postgresql.org/docs/17/indexes.html> · <https://www.postgresql.org/docs/17/sql-createindex.html>
  - PostgreSQL 18: 11.3 Multicolumn Indexes(B-tree skip scan 설명) <https://www.postgresql.org/docs/18/indexes-multicolumn.html>
  - MySQL 8.4: 10.3.6 Multiple-Column Indexes · 10.2.1.2 Range Optimization(Skip Scan 조건) · 10.3.12 Invisible Indexes · 15.1.15 CREATE INDEX(Functional Key Parts) · 17.6.2.1 Clustered and Secondary Indexes <https://dev.mysql.com/doc/refman/8.4/en/range-optimization.html>
  - CMU 15-445 Fall 2024 L8 "Indexes & Filters I"(복합 인덱스·선택 조건) <https://15445.courses.cs.cmu.edu/fall2024/notes/08-indexes1.pdf>
  - Markus Winand 『SQL Performance Explained』 — 커리큘럼 지정 교재, 이 노트 작성 중 열람하지 않음 [?]
- 로컬 재현(PostgreSQL 17.11, MySQL 8.4.10): 20만 행 `ev` 테이블 — 선행 컬럼 유무별 계획, skip scan(MySQL), INCLUDE·가시성 맵과 `Heap Fetches`, 부분 인덱스 크기, 표현식 인덱스, 선택도별 계획, 인덱스 5개 추가 시 WAL·시간
