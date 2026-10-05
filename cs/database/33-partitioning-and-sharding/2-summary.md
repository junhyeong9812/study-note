# database/33-partitioning-and-sharding — 분할과 샤딩: 키 범위·해시, 보조 인덱스, 재조정 — 정리 (힌트)

## 해결하는 문제

복제(32번)는 읽기와 가용성을 늘린다. 그러나 **쓰기와 데이터 크기**는 그대로다. 모든 노드가 전체 데이터를 갖고, 리더가 받은 모든 쓰기를 똑같이 재생한다.\
데이터를 **조각(파티션)으로 나눠 여러 노드에 일부씩** 맡기면(샤딩) 쓰기·크기를 노드 수에 가깝게 늘릴 수 있다. 부하가 고르게 나뉠 때의 이야기다(핫 키가 있으면 못 미친다). 한 인스턴스 안의 분할은 노드를 늘리지 않는다. 그쪽 이득은 관리(`DROP PARTITION`)와 가지치기다(§3).

기초는 원본 두 곳에 있다.
- 용어(파티셔닝 = 한 인스턴스 안, 샤딩 = 여러 인스턴스), 수평/수직 분할, 장단점: [systems/partitioning-vs-sharding](../../systems/partitioning-vs-sharding/2-summary.md) 1~2절.
- 샤딩 방식 표, 샤드 키 3조건, 리샤딩 기법, 크로스 샤드 해법 표: [server-design/03-data-layer.md](../../systems/server-design/03-data-layer.md) §2.

이 노트는 그 아래를 판다. **키를 어떻게 파티션에 대응시키나, 보조 인덱스는 어디에 두나, 노드가 늘 때 무엇이 얼마나 움직이나, 그 사이에 무엇이 깨지나.**

쉬운 예: 도서관 서가 배치.
- 저자 이름 가나다 순으로 서가를 나누면(키 범위), "김"씨 서가만 붐빈다.
- 책 번호를 해시해 서가에 흩으면 고르게 찬다. 대신 "김씨 저자 전부"를 찾으려면 모든 서가를 봐야 한다.
- 서가를 하나 늘릴 때 모든 책을 다시 꽂느냐, 옆 서가 일부만 옮기느냐가 재조정 방식의 차이다.

똑같은 구조다. 실무 예
- 주문 테이블을 `user_id`로 샤딩했는데 `WHERE email = ?` 조회가 모든 샤드로 퍼진다.
- 시간 순 ID로 범위 샤딩했더니 쓰기가 마지막 샤드에만 몰린다.
- 샤드를 4 → 5개로 늘리며 `hash % N`을 바꿨더니 데이터의 80%가 움직였다.

## 동작·원리

### 1. 키 → 파티션 대응 두 가지

```text
  키 범위(range)                              해시(hash)
  [a ~ f) → P1                                hash(key) = 0x3A..  ─┐
  [f ~ m) → P2                                                     ├→ 해시값 범위 또는 mod로 파티션
  [m ~ z] → P3                                hash(key) = 0xC1..  ─┘
  + 범위 조회가 파티션 몇 개로 끝난다           + 고르게 퍼진다
  − 키가 단조 증가(시간·순번)면 최신 파티션에     − 범위 조회는 보통 모든 파티션을 본다
    쓰기가 몰린다(핫 파티션)                     − 같은 키에 몰리는 쏠림(유명인)은 못 푼다
```

- *파티션 키(샤드 키)*: 행을 어느 파티션에 둘지 정하는 컬럼. 원본 §2의 3조건(카디널리티·균등·쿼리 패턴 일치)을 따른다.
- 해시는 **키의 분포**를 고르게 할 뿐이다. 한 키에 요청이 몰리는 것(핫 키)은 그대로다. 핫 키는 키 뒤에 난수 접미사를 붙여 여러 파티션으로 쪼개고, 읽을 때 모아야 한다(DDIA 6장 "Skewed Workloads").

> 참고: 원본 §2 표의 해시 기반 "범위 쿼리 불가"는 "한 파티션으로 좁힐 수 없어 전 파티션을 훑는다"가 정확하다. 아래 로컬 재현에서 PostgreSQL은 해시 분할 테이블의 `BETWEEN` 조회를 4개 파티션 모두로 보냈다. 예외로 MySQL 8.4는 정수 컬럼의 **파티션 수보다 짧은 범위**를 `IN (값 목록)`으로 바꿔 가지치기한다(26.4 Partition Pruning). 로컬 재현(MySQL 8.4.10, `HASH(id) PARTITIONS 4`): `id BETWEEN 1 AND 2` → `partitions: p1,p2`, `id BETWEEN 1 AND 10` → `p0,p1,p2,p3`.

로컬 재현(예시, PostgreSQL 17.11): 해시 분할(`modulus 4`) 테이블에 1~100000을 넣었다.

```text
   tableoid | count            EXPLAIN WHERE id = 42          EXPLAIN WHERE id BETWEEN 1 AND 10
   hp0      | 25126            Seq Scan on hp2                Append
   hp1      | 24978            (파티션 하나로 가지치기)          -> Seq Scan on hp0 … hp1 … hp2 … hp3
   hp2      | 24971                                            (4개 전부)
   hp3      | 24925
```

로컬 재현(예시, MySQL 8.4.10): `PARTITION BY HASH(id) PARTITIONS 4`는 파티션 번호 = `MOD(id, 4)`다(26.2.4). id 1, 2, 5, 9를 넣었더니 `p1`에 3행, `p2`에 1행이었다.
- `MOD`는 키에 규칙이 있으면(예: 4씩 증가) 쏠린다. 해시 함수가 섞어 주는 PostgreSQL과 다르다.

### 2. 보조 인덱스 — 로컬 vs 글로벌

```text
  로컬 인덱스(문서 기준 분할)                     글로벌 인덱스(용어 기준 분할)
  P1: 행들 + P1 행에 대한 color 인덱스             P1: 행들 | 인덱스 조각 color:a~m (모든 파티션의 행을 가리킴)
  P2: 행들 + P2 행에 대한 color 인덱스             P2: 행들 | 인덱스 조각 color:n~z
  읽기: WHERE color='red' → 모든 파티션에 질의      읽기: 인덱스 조각 하나만 본다
        (scatter-gather)                        쓰기: 행 하나 쓰는데 다른 파티션의 인덱스도 고쳐야 한다
  쓰기: 자기 파티션만                                   → 분산 트랜잭션이거나 비동기(잠깐 틀림)
```

- 이 두 방식의 이름과 저울은 DDIA 6장 "Partitioning and Secondary Indexes"의 분류다.
- PostgreSQL 17 선언적 분할의 인덱스는 **파티션별(로컬)**이다. 로컬 재현: `user_id` 인덱스로 조회하면 `Append` 아래 파티션마다 `Bitmap Index Scan on ev_2026_08_user_id_idx`, `… ev_2026_09_user_id_idx`가 돈다.
- 그래서 **전역 유니크 인덱스가 없다.**
  - PostgreSQL 17: 유니크·PK 제약은 파티션 키 컬럼을 모두 포함해야 한다. 파티션마다의 인덱스는 자기 파티션 안에서만 유일성을 보장하기 때문이다(5.12.2 Declarative Partitioning — Limitations). 로컬 재현: `ERROR: unique constraint on partitioned table must include all partitioning columns` / `DETAIL: PRIMARY KEY constraint on table "ev" lacks column "created" which is part of the partition key.`
  - MySQL 8.4: 테이블의 **모든 유니크 키**가 분할 식의 모든 컬럼을 써야 한다(26.6.1). 로컬 재현: `ERROR 1503 (HY000): A UNIQUE INDEX must include all columns in the table's partitioning function`.
- 샤딩(여러 DB)에서도 같다. 각 샤드는 자기 행만 안다. 전역 유일성(이메일 중복 금지 등)은 **그 값 자체를 키로 한** 별도 조회 테이블(예: `email`에 유니크)로 푼다(원본 §2 "전역 유니크"). 전역 ID 발급은 ID의 유일성만 준다. 다른 ID 두 개에 같은 이메일이 들어가는 것은 막지 못한다.

### 3. 파티션 가지치기(pruning) — 키가 조건에 있어야 한다

로컬 재현(예시, PostgreSQL 17.11): `created`로 월 단위 범위 분할한 `ev`.

```text
  EXPLAIN SELECT count(*) FROM ev WHERE created >= '2026-09-10'
    Aggregate
      -> Seq Scan on ev_2026_09 ev            ← 8월 파티션은 아예 안 본다

  EXPLAIN SELECT * FROM ev WHERE user_id = 7   ← 파티션 키가 조건에 없음
    Append
      -> Bitmap Heap Scan on ev_2026_08 …
      -> Bitmap Heap Scan on ev_2026_09 …     ← 모든 파티션
```

- 범위 경계는 **아래 포함, 위 제외**다(`FROM ('2026-09-01') TO ('2026-10-01')`)(5.12.1).
- 어느 파티션에도 안 맞는 값을 넣으면 오류다. 로컬 재현: `ERROR: no partition of relation "ev" found for row` / `DETAIL: Partition key of the failing row contains (created) = (2026-10-05).` → 다음 달 파티션을 미리 만드는 작업이 필요하다(또는 `DEFAULT` 파티션).
- 한 인스턴스 안 분할의 가장 큰 이득은 `DROP`·`DETACH PARTITION`으로 오래된 데이터를 지우는 것이다. 대량 `DELETE`보다 훨씬 빠르고 `VACUUM` 부담이 없다(5.12.1).
- 파티션이 너무 많으면 계획 시간과 메모리가 는다(5.12.6 Best Practices).

### 4. 재조정 — 노드가 늘 때 무엇이 움직이나

```text
  hash % N                  고정 파티션 수(사전 분할)            동적 분할                  일관 해싱 + 가상 노드
  N=4 → 5면 대부분 이동       파티션 1024개를 노드에 배치           파티션이 커지면 둘로 쪼갬     링 위 구간을 노드에 배정
  (키 → 파티션이 바뀜)        노드 추가 = 파티션 몇 개를 통째 이동    쪼갠 조각을 다른 노드로       새 노드는 인접 구간만 가져감
                            파티션 수를 안 바꾸면 키 → 파티션 고정   키 범위 분할에 잘 맞음        vnode가 많을수록 고르게
```

로컬 재현(예시, Python 시뮬레이션, 키 10만 개, MD5 해시):

```text
  hash % 4 → hash % 5 : 79.7% 이동
  링, 노드당 vnode 1개,  4 → 5 노드 : 54.5% 이동,  5노드 부하 = [20215, 3851, 8062, 13384, 54488]
  링, 노드당 vnode 100개, 4 → 5 노드 : 19.7% 이동,  5노드 부하 = [19879, 19325, 22202, 18938, 19656]
  (두 링 모두 "새 노드가 아닌 곳으로 옮겨진 키" = 0)
```

- `hash % N`: N이 N+1이 되면 키가 제자리에 남을 확률은 대략 1/(N+1)이다. 4 → 5면 약 80%가 움직인다.
- *일관 해싱(consistent hashing)*: 노드와 키를 같은 링에 놓고, 키는 시계 방향 다음 노드가 맡는다. 노드를 더하면 그 노드가 끼어든 구간의 키만 옮긴다. 이상적으로는 약 1/n(CMU 15-445 L22). 자세한 구조는 [data-structure/31-consistent-hashing](../../data-structure/31-consistent-hashing/2-summary.md).
- vnode가 1개면 구간 길이가 제멋대로라 부하가 크게 치우친다(위 54488 vs 3851). vnode를 늘리면 이동량도 부하도 1/n에 가까워진다.
- 원본 §2는 **고정 파티션 수(사전 분할)**를 "실무에서 가장 실용적"이라고 적고, "처음부터 논리 샤드를 많이" 만들라고 권한다. 키 → 파티션 대응이 바뀌지 않으니 이동 단위가 "파티션 통째"로 단순하다.

### 5. 요청 라우팅 — 누가 "어느 샤드인가"를 아나

```text
  ① 클라이언트가 안다        ② 라우팅 계층이 안다              ③ 아무 노드나 받아 전달
  앱 ──▶ 샤드 3             앱 ──▶ 라우터 ──▶ 샤드 3          앱 ──▶ 노드 1 ──▶ 노드 3
  (샤드 맵을 앱에 배포)       (프록시·코디네이터)                (노드끼리 맵을 공유)
```

- 어느 방식이든 **샤드 맵(키 → 파티션 → 노드)**을 일관되게 갱신·전파하는 방법이 있어야 한다. 중앙 정본(코디네이터·설정 저장소)을 두는 방식이 흔하고, Cassandra처럼 노드끼리 gossip으로 맵을 퍼뜨리는 방식도 있다(DDIA 6장 "Request Routing"). 재조정 중에는 그 맵이 바뀐다. 맵이 갈린 순간이 아래 장애 3의 위험 구간이다.
- 예: Citus(PostgreSQL 확장)는 코디네이터 노드가 분산 테이블을 샤드로 나눠 워커에 두고, 작은 테이블은 모든 노드에 복제하는 *reference table*로 둔다. 같은 분산 컬럼으로 나눈 테이블을 같은 노드에 모으는 것을 *co-location*이라 부른다(Citus 문서).

## 쓰이는 자료구조·알고리즘

- **해시 함수와 모듈러** — 균등 분포의 기반. `mod N`은 N이 바뀌면 대응이 거의 전부 바뀐다([data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)의 리해시와 같은 문제).
- **일관 해싱 링 + 가상 노드** — 정렬된 해시 위치 배열에서 이진 탐색으로 "다음 노드"를 찾는다([data-structure/31-consistent-hashing](../../data-structure/31-consistent-hashing/2-summary.md), [algorithm/06-binary-search](../../algorithm/06-binary-search/2-summary.md)).
- **범위 맵(정렬된 경계 목록)** — 키 범위 분할과 동적 분할은 "경계값 배열 + 이진 탐색"으로 파티션을 찾는다. PostgreSQL의 범위 파티션 가지치기도 경계와 조건을 비교한다.
- **scatter-gather + 병합** — 전 파티션 질의 결과를 모은다. `ORDER BY … LIMIT k`는 파티션마다 상위 k를 받아 k-way 병합한다(힙).
- **B+Tree 로컬 인덱스** — 파티션마다 따로 있는 인덱스([08-btree-indexes](../08-btree-indexes/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 순서: 한 인스턴스 안 분할 → 기능별 분리 → 샤딩

- 원본 §"확장 사다리"대로, 샤딩은 마지막이다. 먼저 **한 DB 안의 선언적 분할**로 보관 기간 관리(`DROP PARTITION`)와 가지치기를 얻는다.

```sql
-- PostgreSQL 17: 월 단위 범위 분할 + 보관 기간 관리
CREATE TABLE ev (id bigint, user_id int, created date, v int) PARTITION BY RANGE (created);
CREATE TABLE ev_2026_09 PARTITION OF ev FOR VALUES FROM ('2026-09-01') TO ('2026-10-01');
ALTER TABLE ev ADD PRIMARY KEY (id, created);         -- 파티션 키 포함 필수
ALTER TABLE ev DETACH PARTITION ev_2026_03 CONCURRENTLY;   -- 떼어 내 보관 후
DROP TABLE ev_2026_03;
```

```sql
-- MySQL 8.4: EXPLAIN의 partitions 열로 가지치기 확인
EXPLAIN SELECT * FROM hp WHERE id = 5;        -- partitions: p1
EXPLAIN SELECT * FROM hp WHERE email = 'c';   -- partitions: p0,p1,p2,p3
```

### 2. 샤드 키를 쿼리 목록으로 검증한다

```text
  상위 쿼리 20개(pg_stat_statements / performance_schema)를 뽑아
  ┌ 샤드 키 값이 WHERE에서 하나로 정해진다 → 단일 샤드 (범위·여러 값 IN이면 여러 샤드일 수 있다)
  ├ 샤드 키가 없다                    → 전 샤드(scatter-gather) — 빈도·지연 예산 확인
  └ 두 샤드 키를 오간다(이체 A→B)      → 크로스 샤드 트랜잭션(55번, distributed/14 2PC)
```

- 전 샤드 쿼리가 핵심 경로에 있으면 키를 바꾸거나, 그 쿼리용 **조회 테이블**(예: `email → user_id`)을 따로 둔다. 조회 테이블은 글로벌 인덱스를 손으로 만든 것이라 동기화 방식(같은 트랜잭션·비동기)을 정해야 한다.
- 거대 테넌트는 전용 샤드로 떼거나 `tenant_id + 하위 키` 복합 키로 쪼갠다(원본 §2 "흔한 실수").

### 3. 재샤딩 절차 — 복사, 따라잡기, 전환, 검증

```text
  1 스냅숏 복사(백필)  ─┐  스냅숏을 뜬 시점의 로그 위치(LSN·binlog 좌표)를 함께 기록
  2 변경 따라잡기       ├─ 그 위치부터 원본의 변경 로그(WAL·binlog)를 순서대로 새 샤드에 적용
  3 읽기 비교(그림자)    │  두 쪽 결과를 비교만 하고 응답은 원본
  4 쓰기 잠깐 멈춤 → 로그 끝까지 적용 → 샤드 맵 전환 → 쓰기 재개
  5 행 수·체크섬 대조, 원본 보관 후 정리
```

- 핵심은 "백필 + 앱의 이중 쓰기"보다 **원본의 변경 로그를 한 순서로 따라가는 것**이다. 순서가 하나면 옛 값이 새 값을 덮는 경쟁이 없다(아래 장애 3).
  - 조건이 하나 붙는다. 스냅숏은 일관된 한 시점이어야 하고, 로그는 **바로 그 시점의 위치부터** 적용해야 한다. 위치가 어긋나면 빈틈(빠진 변경)이나 늦게 쓰인 스냅숏 행이 새 값을 덮는 일이 생긴다(Debezium의 초기 스냅숏이 이 방식).
- 이 절차에서는 전환 순간에 짧은 쓰기 정지를 둔다. 그 시간을 재고 공지한다. (노드 추가를 온라인으로 처리하는 시스템도 있다 — 모든 재샤딩의 필수 단계는 아니다.)

## 장애 시나리오와 대처

### 1. 핫 파티션 → 한 샤드만 CPU 100%

- **현상**: 전체 부하는 낮은데 한 샤드만 느리고 타임아웃이 난다.
- **보이는 형태**: 샤드별 QPS·CPU·락 대기 그래프에서 하나만 튄다. 그 샤드의 슬로 쿼리 로그에 같은 키가 반복된다. PostgreSQL이면 그 샤드의 `pg_stat_statements` 상위에 한 쿼리 형태가 몰린다. 다만 이 뷰는 상수를 `$1`처럼 정규화해 모으므로 **어느 키인지는 안 보인다**. 키는 슬로 쿼리 로그(바인드 값)나 앱 지표로 찾는다.
- **원인**
  - 단조 증가 키(시간·순번)로 범위 분할 → 최신 파티션에 모든 쓰기.
  - 해시 분할이라도 한 키가 압도적(유명 사용자·거대 테넌트).
  - MySQL `HASH`의 `MOD`처럼 섞지 않는 함수 + 규칙적인 키.
- **대처**
  - 범위 → 해시(또는 `시간 + 해시` 복합).
  - 핫 키는 접미사로 쪼개 쓰고 읽을 때 모은다. 거대 테넌트는 전용 샤드.
  - 샤드별 지표를 평소에 둔다. 평균만 보면 안 보인다.

### 2. 크로스 샤드 쿼리 폭증 → 샤드를 늘릴수록 느려진다

- **현상**: 샤드를 8 → 16으로 늘렸는데 특정 화면의 p99가 오히려 늘었다.
- **보이는 형태**: 라우터·코디네이터에서 쿼리 하나가 샤드 수만큼 하위 쿼리로 퍼진다. 가장 느린 샤드가 전체 지연을 정한다. 커넥션 수도 샤드 수에 비례해 는다.
- **원인**: 샤드 키 없는 조회(`WHERE email = ?`, 전역 정렬·페이지네이션)가 핵심 경로에 있다. scatter-gather는 샤드가 늘수록 꼬리 지연이 커진다.
- **대처**
  - 조회 테이블(수동 글로벌 인덱스)로 샤드를 먼저 찾는다.
  - 자주 함께 쓰는 테이블은 같은 키로 co-location, 작은 참조 테이블은 전 샤드 복제.
  - 전역 집계·검색은 분석 DB·검색 엔진으로 복제해서 푼다(원본 §2 표).
  - 깊은 페이지네이션은 커서 기반으로 바꾼다.

### 3. 리샤딩 중 이중 쓰기 불일치 → 에러 없이 옛 값이 남는다

- **현상**: 샤드 이전을 마쳤는데, 이전 기간에 바뀐 일부 행이 옛 값이다. 에러는 없었다.
- **보이는 형태**: 원본과 새 샤드의 행 수는 같은데 체크섬이 다르다. 이전 중에 갱신된 행에서만 차이가 난다.
- **원인**(앱 이중 쓰기 + 백필이 경쟁)

```text
  시간 →
  백필:   행 R 읽음(v1) ─────────────────────────── 새 샤드에 v1 씀   ← 늦게 도착
  앱:            원본에 v2 씀 → 새 샤드에 v2 씀                           
  결과:  원본 v2, 새 샤드 v1  (옛 값이 새 값을 덮음)
```

  - 두 쓰기 경로(백필, 앱)의 순서를 맞추는 장치가 없다. 앱의 이중 쓰기는 한쪽만 성공할 수도 있다(원본 성공, 새 샤드 실패).
- **대처**
  - 이중 쓰기 대신 원본의 **변경 로그(binlog·WAL 논리 복제·CDC)**를 한 순서로 적용한다. 스냅숏 시점의 로그 위치부터 이어 붙인다.
  - 꼭 이중 쓰기라면 행에 버전(또는 갱신 시각)을 두고 "더 새 버전만 쓴다"는 조건부 쓰기를 한다.
  - 전환 전 **행 단위 체크섬 대조**를 필수로 한다. 행 수만 보면 못 잡는다.
  - 관련: 이중 쓰기 문제 일반은 [distributed/16-outbox-and-dual-write](../../distributed/16-outbox-and-dual-write/2-summary.md).

### 4. 파티션이 없어 INSERT 실패

- **현상**: 월초 0시에 이벤트 적재가 전부 실패한다.
- **보이는 형태**: `ERROR: no partition of relation "ev" found for row`(로컬 재현). MySQL은 `ERROR 1526 (HY000): Table has no partition for value 2027`(로컬 재현, MySQL 8.4.10, `PARTITION BY RANGE (YEAR(d))`).
- **원인**: 다음 달 파티션을 미리 만들지 않았다.
- **대처**: 파티션을 몇 달치 앞서 만드는 작업을 스케줄러에 두고, "남은 미래 파티션 수"를 경보한다. 필요하면 `DEFAULT` 파티션으로 받되, 나중에 새 파티션을 붙일 때 `DEFAULT` 파티션을 스캔해 옮겨야 할 행이 없는지 검사한다. 그동안 `DEFAULT` 파티션에 `ACCESS EXCLUSIVE` 락을 쥔다(5.12.2 — 미리 `CHECK` 제약을 두면 피할 수 있다).

## 핵심 문장

- 여러 노드로 나누는 샤딩의 목적은 쓰기와 크기의 확장이다(한 인스턴스 안 분할은 관리·가지치기). 키 범위는 범위 조회에, 해시는 균등 분포에 유리하고, 둘 다 핫 키는 못 푼다.
- 파티션별 인덱스는 로컬이라 전역 유일성을 보장하지 못한다. PostgreSQL·MySQL 모두 유니크 키가 파티션 키를 포함해야 한다.
- 파티션 키가 조건에 없으면 가지치기가 안 되고 모든 파티션(샤드)으로 퍼진다. 샤드 키는 상위 쿼리 목록으로 검증한다.
- `hash % N`은 N이 바뀌면 거의 모든 키가 움직인다. 고정 파티션 수, 동적 분할, 일관 해싱 + 가상 노드는 이동량을 약 1/n으로 줄인다.
- 재샤딩의 위험은 복사가 아니라 복사 중의 쓰기다. 원본 변경 로그를 한 순서로 적용하고, 전환 전 체크섬으로 대조한다.

## 관련 주제·근거

- 원본(기초): [systems/partitioning-vs-sharding](../../systems/partitioning-vs-sharding/2-summary.md) · [systems/server-design/03-data-layer.md](../../systems/server-design/03-data-layer.md) §2 쓰기·용량 확장
- 선행: [32-replication-leader-follower](../32-replication-leader-follower/2-summary.md) — 파티션마다 복제가 붙는다
- 연결
  - [55-distributed-databases](../55-distributed-databases/2-summary.md) — 크로스 샤드 트랜잭션, 자동 분할하는 분산 DB
  - [data-structure/31-consistent-hashing](../../data-structure/31-consistent-hashing/2-summary.md) · [systems/kafka-why-fast](../../systems/kafka-why-fast/2-summary.md) §4 파티션(같은 핫 파티션·재배치 문제)
  - [08-btree-indexes](../08-btree-indexes/2-summary.md) · [34-large-backfill-and-batch-dml](../34-large-backfill-and-batch-dml/2-summary.md)
  - [distributed/14-two-phase-commit](../../distributed/14-two-phase-commit/2-summary.md)·[distributed/16-outbox-and-dual-write](../../distributed/16-outbox-and-dual-write/2-summary.md) · [ops-patterns/08-saga](../../ops-patterns/08-saga/2-summary.md) · [ops-patterns/13-snowflake](../../ops-patterns/13-snowflake/2-summary.md)(전역 ID)
- 교재·강의
  - DDIA 1판 6장 Partitioning — 키 범위/키 해시, Skewed Workloads, 보조 인덱스(문서 기준·용어 기준), 재조정 전략, 요청 라우팅
  - CMU 15-445 Fall 2024 Lecture #22 Introduction to Distributed Databases(수평 분할·분할 키, 해시 분할의 재배치 문제와 일관 해싱 1/n) <https://15445.courses.cs.cmu.edu/fall2024/notes/22-distributed.pdf>
- PostgreSQL 17: 5.12 Table Partitioning(범위 경계 포함/제외, 해시 modulus/remainder, 유니크 제약 제한, `DETACH … CONCURRENTLY`, 파티션 수 주의) <https://www.postgresql.org/docs/17/ddl-partitioning.html>
- MySQL 8.4: 26.2.4 HASH Partitioning(`MOD(expr, num)`) <https://dev.mysql.com/doc/refman/8.4/en/partitioning-hash.html> · 26.2.4.1 LINEAR HASH(분할·병합이 빠른 대신 분포가 덜 고름) · 26.6.1 Partitioning Keys, Primary Keys, and Unique Keys <https://dev.mysql.com/doc/refman/8.4/en/partitioning-limitations-partitioning-keys-unique-keys.html>
- MySQL 8.4: 26.4 Partition Pruning(HASH/KEY의 짧은 정수 범위 → `IN` 변환, 범위가 파티션 수보다 작을 때만) <https://dev.mysql.com/doc/refman/8.4/en/partitioning-pruning.html>
- PostgreSQL 17: F.30 pg_stat_statements(상수를 `$1`로 정규화) <https://www.postgresql.org/docs/17/pgstatstatements.html>
- Debezium PostgreSQL 커넥터 "Initial snapshots"(스냅숏 트랜잭션에서 로그 위치를 읽고, 스냅숏 뒤 그 위치부터 스트리밍) <https://debezium.io/documentation/reference/stable/connectors/postgresql.html>
- Citus 문서 — Choosing Distribution Column, Table Co-Location, 테이블 유형(distributed·reference) <https://docs.citusdata.com/en/stable/sharding/data_modeling.html>
- 로컬 재현(PostgreSQL 17.11, MySQL 8.4.10, Python): 범위 분할 가지치기와 비가지치기 `EXPLAIN`, 파티션 키 없는 PK 거부, 범위 밖 INSERT 거부, 해시 분할 분포와 `=`/`BETWEEN` 계획, MySQL `ERROR 1503`과 `EXPLAIN partitions`·`MOD` 분포, `hash % N` vs 일관 해싱(vnode 1·100) 이동량·부하 시뮬레이션, MySQL HASH 테이블의 짧은 범위 가지치기(`BETWEEN 1 AND 2` → p1,p2)
