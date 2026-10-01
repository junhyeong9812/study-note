# database/08-btree-indexes — B+트리 인덱스: 구조·분할/병합·클러스터드 vs 보조 — 정리 (힌트)

## 해결하는 문제

인덱스가 없으면 `WHERE email = ?` 하나에도 테이블의 모든 페이지를 읽어야 한다(06번의 풀 스캔).\
정렬된 배열이면 이진 탐색이 되지만, 디스크 위의 정렬 배열은 중간에 끼워 넣을 때마다 뒤를 통째로 밀어야 한다.\
**B+트리**는 두 요구를 함께 푼다. 찾기는 몇 번의 페이지 읽기로, 끼워 넣기는 보통 잎 페이지 하나를 고치는 것으로(분할이 나면 새 잎·부모 등 몇 개 더).

```text
  "email = 'User777@ex.com'" 을 찾는 비용 (로컬 재현, 예시 PostgreSQL 17.11, 20만 행)
  인덱스 없음 : 테이블 전체 페이지 읽기 (Parallel Seq Scan)
  B+트리      : 루트 → 내부 → 잎 → 힙 = 페이지 4개  (Buffers: shared hit=1 read=3)
```

쉬운 예: 두꺼운 사전의 **엄지 색인**이다.
- 옆면 색인(루트)에서 "ㅂ"을 찾는다. 그 구간 첫 쪽의 머리글(내부 노드)로 범위를 좁힌다. 해당 쪽(잎)에서 단어를 찾는다.
- 다음 단어가 궁금하면 다음 쪽으로 넘기면 된다(잎끼리 연결).

똑같은 구조다.\
트리의 노드 하나 = 디스크 페이지 하나다. 노드가 수백 갈래로 갈라지므로 수천만 행도 3~4층이면 닿는다.

실무 예:
- `EXPLAIN`에 `Index Scan using users_email`이 뜨면 B+트리를 탄 것이다.
- `WHERE lower(email) = ?`로 바꾸자 같은 인덱스를 못 타고 풀 스캔으로 돌아간다.
- PK를 UUIDv4로 바꾸자 인덱스가 커지고 쓰기가 느려진다.

## 동작·원리

### 1. 모양

```text
                         [ 루트  |  K=100  |  K=200  | ]                 ← 내부 노드: 구분 키 + 자식 포인터
                        /            |              \
        [ 30 | 60 | ]        [ 130 | 160 | ]        [ 230 | 260 | ]      ← 내부 노드
        /    |    \           ...                     ...
  [1 2 … 29] ⇄ [30 … 59] ⇄ [60 … 99] ⇄ [100 …] ⇄ … ⇄ [260 … ]              ← 잎: 키 + (행 주소 또는 행 자체)
                                                                         ⇄ = 형제 포인터(범위 스캔용)
```

- *B+트리*: 모든 값(또는 행 주소)이 **잎**에만 있다. 내부 노드는 길 안내용 구분 키만 가진다(CMU 15-445 L8).
- 루트에서 잎까지의 거리가 모든 잎에서 같다(균형). 루트를 뺀 내부 노드는 적어도 반쯤 찬다는 것이 교과서 규칙이다(L8).
- 잎끼리는 형제 포인터로 이어진다. 그래서 `BETWEEN`·`ORDER BY`·`>` 같은 **범위 조회**가 잎을 옆으로 걷는 일이 된다. 해시 인덱스(39번)가 못 하는 일이다.
- 교과서 B-트리와의 차이·기본 연산은 [data-structure/15 b-tree](../../data-structure/15-b-tree/2-summary.md)에 있다. 여기서는 DB 페이지 위의 모습에 집중한다.

**높이 감각.** 로컬 재현(예시, PostgreSQL 17.11): `bigint` PK 20만 개 → 잎 547페이지(잎당 약 366개, 밀도 90%), 내부 3페이지, `tree_level = 2`(루트 → 내부 → 잎, 3층).

```text
  예시 계산 (bigint 키, 8KB 페이지, 갈래 수를 약 400으로 가정)
  3층: 400 × 400 × 366  ≈ 5,800만 행
  4층: 400 × 5,800만    ≈ 230억 행
  → 행 수가 수백 배 늘어도 층은 1씩 는다. 루트·내부는 작아서 거의 늘 버퍼 풀에 있다(07번).
```

### 2. 삽입과 분할

```text
  잎이 꽉 찼는데 45를 넣어야 한다
  [30 35 40 50 55]  →  [30 35 40] [45 50 55]     절반씩 나눈다 (분할점은 구현이 고른다)
                                  ^
                     부모에 구분 키 45와 새 잎 포인터 추가
  부모도 꽉 찼으면 부모도 분할 → 위로 번진다 → 루트가 분할되면 새 루트, 높이 +1
```

- PostgreSQL: 분할은 위로 연쇄되고, 루트가 못 버티면 새 루트가 생겨 층이 하나 는다(PG 17 문서 64.1.4.1).
- **오른쪽 끝 삽입은 특별하다.** 키가 계속 커지는 삽입(시퀀스, 시간)은 늘 가장 오른쪽 잎에 들어간다.
  - PostgreSQL: 인덱스를 오른쪽으로 늘릴 때는 잎을 `fillfactor`(B-트리 기본 **90**)까지 채우고 넘긴다(CREATE INDEX 문서).
  - InnoDB: 클러스터드 인덱스에 새 레코드를 넣을 때 페이지의 1/16을 비워 두려 한다. 순차 삽입이면 페이지가 약 15/16 차고, 무작위 순서면 1/2 ~ 15/16 찬다(MySQL 8.4 17.6.2.2).
- 무작위 키(UUIDv4)는 아무 잎에나 떨어진다. 잎마다 반쯤 찬 채 계속 쪼개진다.

```text
  로컬 재현 — 20만 행 적재 직후 PK 인덱스
                        PostgreSQL 17.11 (pgstatindex)                  MySQL 8.4.10 (data_length/16KB)
  순차 키               bigint: 잎 547, 밀도 90%, 조각화 0%              BIGINT AUTO_INCREMENT: 1764페이지
  UUID 무작위           uuid:   잎 1052, 밀도 65.69%, 조각화 49.71%     BINARY(16) RANDOM_BYTES: 3049페이지
  같은 UUID 재구성 후   REINDEX: 잎 767, 밀도 89.96%, 조각화 0%          OPTIMIZE(재생성): 2149페이지
```

- 키 크기(8 vs 16바이트) 차이를 빼고 보려면 **같은 UUID의 재구성 전후**를 비교한다. PG 잎 1052 → 767, InnoDB 3049 → 2149. 무작위 삽입만으로 약 1.4배 부풀었다.
  - bigint와 그대로 비교하면 키 크기 차이까지 섞인다. PG 잎 547 → 1052(약 1.9배), InnoDB 1764 → 3049페이지(약 1.7배)다. 28번의 "bigint의 약 2배"는 이 비교다.
  - *leaf_fragmentation*: 잎의 논리 순서와 물리 블록 순서가 어긋난 비율이다. 순차 삽입은 새 잎이 파일 끝에 순서대로 붙어 0%다.
- 쓰기 비용도 다르다. 로컬 재현(예시, PostgreSQL 17.11): 이미 20만 행이 든 테이블에 10만 행을 더 넣었다.

```text
                    WAL 바이트       full-page image   dirtied 버퍼
  bigint 순차       12,926,062        4                  721
  uuid 무작위       21,313,518        1,064              1,963
```

- 무작위 삽입은 매번 다른 잎을 건드린다. `full_page_writes = on`(기본값)이면 체크포인트 뒤 처음 고치는 페이지마다 전체 페이지 이미지(FPI)가 WAL에 실린다(PG 17 문서 19.5). 그래서 WAL이 1.6배, 건드린 버퍼가 2.7배였다.

### 3. 삭제와 병합

- 교과서: 잎이 반보다 비면 형제에게 빌리거나 합친다(L8).
- 실제 엔진은 게으르다.
  - PostgreSQL: **완전히 빈 페이지만** VACUUM 때 지운다. 반쯤 빈 페이지끼리 합치지 않는다. 반대 방향으로 가는 스캔이 항목을 놓칠 수 있어서다(`src/backend/access/nbtree/README`).
  - InnoDB: 페이지 채움이 `MERGE_THRESHOLD`(기본 50%) 아래로 떨어지면 이웃과 합치려 한다(17.6.2.2, 17.8.11).
- PostgreSQL은 쪼개지기 직전에 먼저 청소를 시도한다(64.1.4.2).
  - *bottom-up index deletion*: 인덱스 칼럼을 안 바꾸는 UPDATE가 만든 옛 버전 항목을 그 잎에서 골라 지운다.
  - *deduplication*: 같은 키 항목들을 키 한 번 + TID 목록으로 합친다(기본 켜짐, 64.1.4.3).

### 4. 클러스터드 vs 보조 인덱스

```text
  MySQL InnoDB                                         PostgreSQL
  PK 트리(클러스터드) 잎 = 행 전체*                     힙(순서 없음) = 행
  [PK=1: 행] [PK=2: 행] …                               (0,1) (0,2) … (6666,15)

  보조 인덱스 잎 = (email, PK)                          B-트리 인덱스 잎 = (키, ctid)
  email로 찾기: 보조 트리 → PK → PK 트리 → 행            email로 찾기: 인덱스 → ctid → 힙 페이지
               (두 번 내려간다)                                      (힙 페이지 한 번)
  * 긴 가변 길이 값은 오버플로 페이지로 나가고 잎에는 포인터만 남을 수 있다(06번)
```

- InnoDB
  - PK가 곧 클러스터드 인덱스다. PK가 없으면 NOT NULL 칼럼으로만 된 첫 UNIQUE 인덱스, 그것도 없으면 숨은 6바이트 row ID로 `GEN_CLUST_INDEX`를 만든다(17.6.2.1).
  - 보조 인덱스 레코드에는 **PK 칼럼**이 들어 있다. 그래서 PK가 길면 모든 보조 인덱스가 커진다(17.6.2.1).
  - 이득: PK 범위 조회는 잎을 옆으로 읽기만 하면 행이 나온다.
- PostgreSQL
  - 테이블은 힙이고, 모든 인덱스가 동등한 "보조" 인덱스다. B-트리 인덱스 잎에는 `ctid`(06번의 페이지, 슬롯)가 있다(BRIN처럼 블록 범위 요약만 담는 인덱스는 예외, PG 17 문서 64.5).
  - `CLUSTER` 명령은 한 번 인덱스 순서로 다시 쓸 뿐, 이후 삽입의 순서를 유지하지 않는다.
- *커버링 인덱스*: 필요한 칼럼이 모두 인덱스에 있으면 행을 보러 가지 않는다.
  - MySQL: `SELECT id FROM users WHERE email = ?` → `Covering index lookup on users using ix_email`(로컬 재현). 보조 인덱스에 PK `id`가 이미 있어서다.
  - PostgreSQL: `Index Only Scan … Heap Fetches: 0`(로컬 재현, VACUUM 뒤). 가시성 지도(VM)로 "이 페이지는 모두에게 보인다"가 확인될 때만 힙을 건너뛴다.

### 5. 인덱스를 못 타는 조건 — 칼럼에 무엇을 씌우면

B+트리는 **칼럼 값 그 자체의 순서**로 정렬돼 있다. 조건이 그 순서를 쓸 수 없는 모양이면 트리를 탈 수 없다.

```text
  로컬 재현 (PostgreSQL 17.11 / MySQL 8.4.10) — users(email, created_at)에 각각 인덱스
  WHERE email = 'User777@ex.com'                     Index Scan / Index lookup        ✓
  WHERE lower(email) = 'user777@ex.com'              Seq Scan (PG)                     ✗  lower() 순서 ≠ email 순서
  WHERE date(created_at) = '2026-03-01'              Seq Scan / Table scan             ✗
  WHERE created_at >= '2026-03-01'
    AND created_at <  '2026-03-02'                   Index Scan / Index range scan     ✓  같은 뜻, 칼럼은 맨몸
  WHERE email = 777  (MySQL, 문자열 칼럼에 숫자)      Table scan                        ✗  칼럼 쪽이 숫자로 변환됨
  WHERE email LIKE '%777@ex.com'  (MySQL)             Table scan                        ✗  앞이 정해지지 않은 패턴
```

- 해법 두 가지
  - 조건을 칼럼이 맨몸이 되게 고쳐 쓴다(날짜 → 반열린 범위).
  - 식 자체에 인덱스를 만든다. PG `CREATE INDEX ON users (lower(email))` → `Index Scan using users_lower_email`. MySQL 8.4 `CREATE INDEX ix ON users ((lower(email)))` → `Index lookup … using ix_lower_email`(로컬 재현).
- 경계: PG에서 `timestamptz`의 `created_at::date`에는 식 인덱스를 만들 수 없다. `ERROR: functions in index expression must be marked IMMUTABLE`(로컬 재현). 날짜 변환이 세션 시간대에 따라 달라서다(27번). 이때는 범위로 고쳐 쓴다.

## 쓰이는 자료구조·알고리즘

- **B+트리**: 노드 = 페이지, 잎 연결, 분할·병합. → [data-structure/15 b-tree](../../data-structure/15-b-tree/2-summary.md)
- **이진 탐색**: 노드 하나 안에서 키를 찾는다. InnoDB는 페이지 디렉터리 슬롯으로 이진 탐색 후 연결 리스트를 몇 칸 따라간다(06번).
- **Lehman–Yao B-link 트리**: PostgreSQL nbtree는 페이지마다 오른쪽 형제 링크와 high key를 둔다. 분할 중에도 읽는 쪽이 오른쪽으로 따라가 키를 찾는다(nbtree README). 동시성은 53번에서 다룬다.
- **접미사 절단(suffix truncation)**: 내부 노드 구분 키를 필요한 만큼만 남겨 갈래 수를 늘린다(nbtree README).
- **게시 목록(posting list)**: 중복 키를 키 한 번 + 정렬된 TID 배열로 담는 deduplication.
- **정렬 후 아래에서 위로 쌓기(sorted index build)**: `CREATE INDEX`·`REINDEX`·InnoDB 정렬 인덱스 빌드는 데이터를 정렬해 잎부터 채운다. 그래서 재구성 직후 밀도가 fillfactor 근처다(MySQL 17.6.2.3 `innodb_fill_factor`).

## 적용 — 풀어나가는 법

**1) 쿼리가 인덱스를 타는지 본다.**

```sql
-- PostgreSQL 17
EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM users WHERE lower(email) = 'user777@ex.com';
-- MySQL 8.4
EXPLAIN FORMAT=TREE SELECT * FROM users WHERE DATE(created_at) = '2026-03-01';
EXPLAIN ANALYZE     SELECT * FROM users WHERE email = 'User777@ex.com';
```

- `Seq Scan`/`Table scan` + `Filter:`에 칼럼을 감싼 식이 보이면 5절의 경우다.

**2) 인덱스의 건강을 본다.**

```sql
-- PostgreSQL: pgstattuple 확장
SELECT tree_level, internal_pages, leaf_pages, avg_leaf_density, leaf_fragmentation
FROM pgstatindex('k_uuid_pkey');
SELECT pg_size_pretty(pg_relation_size('k_uuid_pkey'));

-- MySQL: 인덱스별 페이지 수(통계, 추정값)
SELECT index_name, stat_name, stat_value
FROM mysql.innodb_index_stats
WHERE database_name = 'w06' AND table_name = 'o_rnd' AND stat_name IN ('size', 'n_leaf_pages');
```

- 밀도가 계속 낮고 크기가 커지면 재구성을 검토한다. PG `REINDEX INDEX CONCURRENTLY`(락을 짧게), MySQL `OPTIMIZE TABLE`(InnoDB는 재생성 + 분석으로 바뀐다, 로컬 재현 메시지 "doing recreate + analyze instead").

**3) PK를 고른다.**
- 삽입이 많은 테이블은 **단조 증가 키**(bigint 시퀀스, 시간 순 ID)가 오른쪽 끝 삽입이 되어 분할·쓰기 증폭이 적다.
- 외부에 노출할 무작위 ID가 필요하면 내부 PK와 분리하거나, 시간 순으로 정렬되는 UUID(RFC 9562의 UUIDv7)를 쓴다. 자세한 선택은 28번.
- InnoDB는 PK가 모든 보조 인덱스에 복사되므로 **짧은 PK**가 더 중요하다.

**4) 앱에서 (Java / JPA).** 인덱스를 못 타게 만드는 코드는 대개 앱에 있다.

```java
// ✗ 칼럼에 함수를 씌운 JPQL → SQL에도 그대로 나간다
em.createQuery("select u from User u where function('date', u.createdAt) = :d", User.class);

// ✓ 반열린 범위로 — 칼럼은 맨몸, 인덱스 범위 스캔
Instant from = day.atStartOfDay(zone).toInstant();
Instant to   = day.plusDays(1).atStartOfDay(zone).toInstant();
em.createQuery("select u from User u where u.createdAt >= :from and u.createdAt < :to", User.class)
  .setParameter("from", from).setParameter("to", to);

// ✗ 문자열 칼럼에 숫자 바인딩 (MySQL은 칼럼 쪽을 숫자로 변환 → 풀 스캔)
ps.setLong(1, 777L);      // WHERE email = ?
// ✓ 타입을 칼럼에 맞춘다
ps.setString(1, "777");
```

## 장애 시나리오와 대처

**1) 랜덤 UUID PK → 페이지 분할·쓰기 증폭 (⚠)**
- 현상: PK를 UUIDv4로 바꾼 뒤 삽입 처리량이 떨어지고, 인덱스·WAL·복제 트래픽이 커진다. 데이터가 버퍼 풀보다 커지면 삽입 지연이 튄다.
- 보이는 형태
  - PG: `pgstatindex`의 `avg_leaf_density` 약 66%, `leaf_fragmentation` 약 50%(로컬 재현 65.69 / 49.71). `EXPLAIN (ANALYZE, WAL)`의 `fpi`가 많다(재현 1,064 vs 4).
  - MySQL: `data_length`가 재생성 후보다 약 1.4배(재현 3049 vs 2149페이지).
- 원인: 무작위 키는 모든 잎에 흩어져 들어간다. 잎이 반쯤 찬 채 쪼개지고, 매 삽입이 다른 페이지를 dirty로 만든다. 그 페이지들이 버퍼 풀에 다 못 들어가면 삽입마다 디스크 읽기가 붙는다(07번).
- 대처: 단조 증가 PK를 쓰고 외부 ID는 따로 둔다. UUID가 필요하면 시간 순 UUIDv7. 이미 부푼 인덱스는 재구성한다.

**2) 인덱스 칼럼에 함수 적용 → 인덱스 미사용 (⚠)**
- 현상: 대소문자 무시 로그인, 날짜별 조회를 넣은 뒤 그 API만 느리다. 데이터가 늘수록 선형으로 나빠진다.
- 보이는 형태: `Seq Scan … Filter: (lower(email) = …)`, MySQL `Table scan` + `Filter: (cast(users.created_at as date) = …)`. 슬로 쿼리 로그의 `Rows_examined`가 테이블 행 수만큼.
- 원인: 인덱스는 칼럼 값의 순서로 정렬돼 있다. `lower(email)`·`date(created_at)`의 순서가 아니다. 암묵적 형변환(문자열 칼럼 = 숫자)도 칼럼에 함수를 씌운 것과 같다.
- 대처: 범위로 고쳐 쓰거나 식 인덱스를 만든다. 대소문자 무시는 식 인덱스 또는 collation(10번)으로 푼다. 바인딩 타입을 칼럼 타입에 맞춘다.

**3) 인덱스가 너무 많아 쓰기가 느리다**
- 현상: INSERT·UPDATE 지연이 점점 는다. 테이블보다 인덱스 총량이 크다.
- 보이는 형태: PG `pg_stat_user_indexes.idx_scan = 0`인 인덱스가 여럿. `pg_relation_size`의 인덱스 합 > 테이블.
- 원인: INSERT와 HOT이 아닌 UPDATE는 그 행을 담는 인덱스마다 항목을 넣는다. PG는 인덱스 칼럼(BRIN 같은 요약 인덱스 제외)이 하나라도 바뀌거나 같은 페이지에 자리가 없으면 HOT이 안 된다(06번, 65.7).
- 대처: 안 쓰는 인덱스를 지운다. 비슷한 인덱스를 복합 인덱스 하나로 합친다(09번).

**4) 대량 삭제 뒤에도 인덱스가 줄지 않는다**
- 현상: 오래된 행을 절반 지웠는데 인덱스 크기가 그대로다.
- 보이는 형태: `pgstatindex`의 `avg_leaf_density`가 낮다. 인덱스 범위 스캔이 읽는 페이지 수가 줄지 않는다.
- 원인: PostgreSQL은 완전히 빈 잎만 회수하고 반쯤 빈 잎은 합치지 않는다(nbtree README). 오래된 키가 흩어져 지워졌으면 빈 페이지가 거의 안 생긴다.
- 대처: `REINDEX INDEX CONCURRENTLY`. 시간 순 대량 삭제가 반복되면 시간 파티션으로 바꿔 파티션째 떼어 낸다(33번).

## 핵심 문장

- B+트리는 노드 하나 = 페이지 하나인 다갈래 균형 트리다. 값은 잎에만 있고 잎끼리 이어져 범위 조회가 된다.
- 갈래가 수백이라 수천만 행도 3~4층이다. 루트·내부 노드는 거의 늘 버퍼 풀에 있다.
- 꽉 찬 노드는 반으로 쪼개지고 분할은 위로 번질 수 있다. 오른쪽 끝 삽입은 잎을 꽉 채우고(PG fillfactor 90, InnoDB 클러스터드 15/16) 무작위 삽입은 반쯤 찬 잎을 남긴다.
- InnoDB는 테이블이 곧 PK 트리이고 보조 인덱스는 PK를 담는다. PostgreSQL은 테이블이 힙이고 B-트리 인덱스는 ctid를 담는다.
- 인덱스는 칼럼 값의 순서로 정렬돼 있어서, 칼럼에 함수나 형변환을 씌우면 그 순서를 쓸 수 없다. 범위로 고쳐 쓰거나 식 인덱스를 만든다.
- 랜덤 UUID PK는 잎 밀도를 낮추고(재현 66%) WAL·dirty 페이지를 늘린다. 단조 증가 키가 B+트리에 맞는 키다.

## 관련 주제·근거

- 선행
  - [07-buffer-pool](../07-buffer-pool/2-summary.md) — 노드 = 페이지가 버퍼 풀에 올라오는 방식
  - [06-pages-and-tuple-layout](../06-pages-and-tuple-layout/2-summary.md) — 인덱스가 가리키는 행 주소(ctid)와 클러스터드 저장
  - [data-structure/15 b-tree](../../data-structure/15-b-tree/2-summary.md) — B-트리 자료구조 자체
- 후속·연결
  - [09-index-design](../09-index-design/2-summary.md) — 복합·커버링·부분·식 인덱스, 선택도
  - [28-key-strategy-surrogate-natural-public-id](../28-key-strategy-surrogate-natural-public-id/2-summary.md) — bigint vs UUIDv4/v7
  - database [53-index-concurrency-control](../53-index-concurrency-control/2-summary.md) — 래치 크래빙, B-link 트리.
  - [38-lsm-storage-engine](../38-lsm-storage-engine/2-summary.md) — 제자리 갱신(B+트리) vs 덧붙이기(LSM)
- 문서·소스
  - PostgreSQL 17 문서 64.1 B-Tree Indexes — 64.1.4.1 분할의 위쪽 연쇄, 64.1.4.2 bottom-up deletion, 64.1.4.3 deduplication <https://www.postgresql.org/docs/17/btree.html>
  - PostgreSQL 17 문서 CREATE INDEX — B-트리 fillfactor 기본 90, 오른쪽 확장 시 적용 <https://www.postgresql.org/docs/17/sql-createindex.html>
  - PostgreSQL 17 문서 64.5 BRIN Indexes <https://www.postgresql.org/docs/17/brin.html> · 19.5 Write Ahead Log(`full_page_writes`) <https://www.postgresql.org/docs/17/runtime-config-wal.html>
  - PostgreSQL 17 문서 11.9 Index-Only Scans and Covering Indexes · F.31 pgstattuple(`pgstatindex`) <https://www.postgresql.org/docs/17/pgstattuple.html>
  - PostgreSQL `src/backend/access/nbtree/README`(REL_17_STABLE) — Lehman & Yao, 빈 페이지만 삭제, 접미사 절단 <https://github.com/postgres/postgres/blob/REL_17_STABLE/src/backend/access/nbtree/README>
  - MySQL 8.4 Reference Manual 17.6.2.1 Clustered and Secondary Indexes · 17.6.2.2 Physical Structure(16KB, 1/16 여유, 15/16 vs 1/2~15/16, MERGE_THRESHOLD 50%) · 17.6.2.3 Sorted Index Builds <https://dev.mysql.com/doc/refman/8.4/en/innodb-index-types.html>
  - MySQL 8.4 15.1.15 CREATE INDEX — Functional Key Parts <https://dev.mysql.com/doc/refman/8.4/en/create-index.html>
- 강의: CMU 15-445 Fall 2024 L8 Indexes & Filters I(B+트리 성질, 삽입·삭제, 클러스터드 인덱스) · L9 Indexes & Filters II
- 로컬 재현(PostgreSQL 17.11, MySQL 8.4.10): bigint vs uuid PK 20만 행의 `pgstatindex`와 REINDEX, 추가 10만 행의 `EXPLAIN (ANALYZE, WAL, BUFFERS)`, InnoDB BIGINT vs BINARY(16) `data_length`와 OPTIMIZE, `lower()`·`date()`·범위·암묵 변환·`LIKE '%…'`의 실행 계획, 식 인덱스(양쪽), `timestamptz::date` 식 인덱스 오류, 커버링 조회
