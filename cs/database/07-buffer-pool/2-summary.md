# database/07-buffer-pool — 버퍼 풀: 핀·dirty·교체 정책·순차 스캔 오염 — 정리 (힌트)

## 해결하는 문제

06번에서 테이블은 페이지의 모음이었다.\
쿼리가 행 하나를 읽을 때마다 디스크에서 페이지를 읽으면 너무 느리다.\
그래서 DB는 메모리에 **페이지 칸(frame)** 을 잔뜩 잡아 두고, 읽은 페이지를 거기 담아 재사용한다. 이것이 **버퍼 풀**이다.

```text
  쿼리 실행기          "3번 테이블 17번 페이지 줘"
       |
       v
  +---------------- 버퍼 풀 (메모리) ----------------+
  | page table: (파일, 블록) → 프레임 번호  [해시]   |
  |  frame0   frame1   frame2   ...   frameN          |
  |  [p17]    [p3 *]   [빈칸]         [p99]    * = dirty
  +---------------------------------------------------+
       | 없으면 읽기(miss)                ^ 고친 페이지는 나중에 쓰기(write-back)
       v                                  |
  디스크 파일
```

풀어야 할 질문이 세 개 생긴다.
- 지금 누가 쓰고 있는 페이지를 내쫓으면 안 된다 → **핀(pin)**.
- 고친 페이지를 언제 디스크에 쓰나 → **dirty 표시**와 쓰기 시점.
- 칸이 다 찼을 때 무엇을 내쫓나 → **교체 정책**(LRU·CLOCK 계열).

쉬운 예: 도서관 열람실 책상(프레임)과 서고(디스크)다.
- 자주 보는 책은 책상에 둔다. 누가 펼쳐 읽는 중인 책(핀)은 치우지 않는다.
- 메모를 적은 책(dirty)은 치우기 전에 서고의 원본에 옮겨 적어야 한다.
- 책상이 차면 한동안 아무도 안 본 책부터 서고로 돌려보낸다.

똑같은 구조다.\
운영체제의 페이지 캐시·페이지 교체와 같은 문제를 DB가 **자기 손으로** 한 번 더 푼다([os/12](../../os/12-swapping-and-page-replacement/2-summary.md), [os/14](../../os/14-mmap-and-page-cache/2-summary.md)).

실무 예:
- `EXPLAIN (ANALYZE, BUFFERS)`의 `shared hit=443`(버퍼 풀에서 찾음)과 `read=443`(디스크나 OS 캐시에서 읽음).
- `SHOW ENGINE INNODB STATUS`의 `Buffer pool hit rate 1000 / 1000`.
- 밤마다 도는 풀 스캔 배치 뒤로 아침 OLTP 응답이 느려지는 현상(순차 스캔 오염).

## 동작·원리

### 1. 페이지 요청 한 번의 흐름

```text
  get_page(p):
    1. page table(해시)에서 p를 찾는다
       ├─ 있음(hit)  → pin++ , 사용 기록 갱신 → 프레임 반환
       └─ 없음(miss) → 2로
    2. 빈 프레임이 있나? 없으면 교체 정책으로 희생자 v를 고른다 (pin > 0 인 프레임은 후보 아님)
    3. v가 dirty면 먼저 디스크에 쓴다 (WAL 규칙: 그 페이지의 로그가 먼저 디스크에 있어야 한다)
    4. p를 디스크에서 v 자리로 읽고, page table을 고친다 → pin++ → 반환
  release_page(p, 고쳤나):
    pin-- ; 고쳤으면 dirty = true
```

- *page table*: (파일, 블록 번호) → 프레임 위치를 담은 **메모리 해시 테이블**이다(CMU 15-445 L6). 디스크의 "page directory"(페이지 ID → 파일 위치)와 다르다.
- *핀(pin, 참조 카운트)*: 이 페이지를 쓰는 중인 스레드 수다. 0보다 크면 내쫓지 못한다. 핀은 다른 스레드의 동시 접근을 막지 않는다. 막는 것은 별도의 페이지 락(latch)이다.
  - PostgreSQL 버퍼 README: 버퍼로 무엇이든 하려면 먼저 핀을 잡는다. 핀 없는 버퍼는 언제든 다른 페이지로 재활용될 수 있다. 락을 잡으려면 핀이 먼저다.
- *dirty*: 메모리에서 고쳐졌지만 아직 디스크에 안 쓴 페이지다. 버퍼 풀은 write-back 캐시다.
- 3번의 "로그 먼저"는 19번 WAL의 규칙이다. 여기서는 "dirty 페이지를 쓰기 전에 WAL을 flush해야 할 수 있다"만 기억한다.

### 2. 교체 정책 — LRU, CLOCK, 그리고 스캔 저항

```text
  LRU   : 가장 오래 안 쓴 것을 내쫓는다. 접근마다 리스트 맨 앞으로 옮긴다.
  CLOCK : 프레임을 원형으로 놓고 시계바늘이 돈다. 참조 비트가 1이면 0으로 내리고 지나가고, 0이면 내쫓는다.
          → LRU의 근사. 접근 때 리스트를 옮기지 않아도 된다.

        +---+     바늘
        | 1 |<----+          바늘이 1을 만나면 0으로 바꾸고 다음으로
    +---+   +---+ |          0을 만나면 그 프레임이 희생자
    | 0 |   | 1 | |
    +---+   +---+
        | 0 |  ← 희생자
        +---+
```

- 둘 다 약점이 같다. **순차 스캔 오염(sequential flooding)**: 큰 테이블을 한 번 쭉 읽으면, 다시 안 쓸 페이지가 "최근 사용"으로 풀을 가득 채운다. 자주 쓰던 페이지가 밀려난다(CMU L6).
- 대책 계열(CMU L6)
  - *LRU-K*: 마지막 K번 접근 시각을 보고 다음 접근을 예측한다. 한 번만 본 페이지는 불리하다.
  - *쿼리별 국소화*: 스캔 하나가 쓸 칸을 따로 준다.
  - *우선순위 힌트*: 실행기가 "이 페이지는 다시 안 본다"를 알려 준다.

실제 두 엔진은 이렇게 한다.

**PostgreSQL 17 — clock sweep + usage_count + 링 버퍼**

```text
  버퍼마다 usage_count (0..5, BM_MAX_USAGE_COUNT = 5)
  백엔드가 그 버퍼에 처음 핀을 잡을 때 usage_count++ (최대 5, 이미 핀을 가진 백엔드의 재핀은 안 올림,
  링 전략 스캔은 0일 때만 1로 — bufmgr.c PinBuffer)

  희생자 찾기 (src/backend/storage/buffer/README):
    free list가 있으면 거기서
    없으면 nextVictimBuffer(시계바늘)가 가리키는 버퍼:
       핀 있음                       → 다음 칸 (README는 이때도 내린다고 적지만 freelist.c 코드는 핀 없는 버퍼만 내린다)
       핀 없고 usage_count > 0      → usage_count-- 하고 다음 칸
       핀 없고 usage_count == 0     → 희생자

  큰 순차 스캔 (테이블 블록 수 > shared_buffers / 4)  → BAS_BULKREAD 링 256KB
       (임시 테이블 제외·호출자가 끌 수 있음, 링 크기 상한 = shared_buffers의 1/8)
       링 안의 버퍼만 돌려 쓴다 → 풀 전체를 밀어내지 않는다
  VACUUM → 링 (vacuum_buffer_usage_limit, 기본 2MB)
  COPY IN · CREATE TABLE AS → 링 16MB (shared_buffers의 1/8 이하)
```

- usage_count는 "몇 바퀴를 버틸 수 있나"다. 자주 쓰인 버퍼는 바늘이 여러 번 지나가야 쫓겨난다. LRU보다 **빈도**를 조금 반영한다.
- 링 버퍼 조건은 `heapam.c`의 `scan->rs_nblocks > NBuffers / 4`다(REL_17_STABLE).
  - 로컬 버퍼를 쓰는 임시 테이블은 제외되고, 호출자가 `SO_ALLOW_STRAT`를 끄면 쓰지 않는다. 링 크기는 `min(256KB, shared_buffers/8)`이다(`freelist.c` `GetAccessStrategyWithSize`).

```text
  로컬 재현 (예시, PostgreSQL 17.11, shared_buffers = 128MB = 16384 버퍼)
  wide 6667페이지 (> 16384/4 = 4096)  → 스캔 뒤 버퍼 풀에 남은 wide 페이지  32개 = 256KB / 8KB
  두 번째 스캔: shared hit=32 read=6635  → 스캔 뒤 64개
  narrow 443페이지 (< 4096)           → 스캔 뒤 443개 전부 남음, 두 번째 스캔 hit=443
                                        usagecount 1 → 두 번째 스캔 뒤 2
```

- 즉 PG는 **작은 테이블은 그대로 캐시하고, 큰 테이블 풀 스캔은 256KB 링에 가둔다.**
- PG는 운영체제 페이지 캐시에도 기댄다. 그래서 `read=`는 "디스크"가 아니라 "버퍼 풀 밖"이다. 커널 캐시에서 왔을 수도 있다. 문서는 전용 서버에서 `shared_buffers` 시작값으로 RAM의 25%를 권하고, OS 캐시에 기대므로 40% 넘게는 효과가 적을 것이라 적는다(PG 17 문서 19.4.1).

**MySQL 8.4 InnoDB — 중간점 삽입 LRU (young / old)**

```text
  머리(MRU)                                             꼬리(LRU) → 여기서 내쫓김
  [ new(young) 하위 리스트 5/8 ][ old 하위 리스트 3/8 ]
                               ^ 중간점: 새로 읽은 페이지는 여기(old의 머리)에 들어간다

  old에 있는 페이지에 다시 접근하면 → new의 머리로 (young으로 승격)
  단, 처음 접근 후 innodb_old_blocks_time(기본 1000ms) 안의 접근은 승격시키지 않는다
```

- `innodb_old_blocks_pct` 기본 37(= 3/8), `innodb_old_blocks_time` 기본 1000ms(MySQL 8.4 17.5.1, 17.8.3.3). 로컬 확인 `37`, `1000`.
- 스캔은 페이지 하나를 짧은 시간에 여러 번 읽고 끝난다. 그 접근이 1초 안에 몰리면 old에 머물다 쫓겨난다. 이것이 InnoDB의 스캔 저항이다. 운영자가 고를 수 있는 두 개의 손잡이다.
- 경계: 이미 풀에 있던 페이지를 1초 **지나서** 다시 스캔하면 young으로 올라간다.
  - 로컬 재현(예시, MySQL 8.4.10): 방금 넣어 풀에 있던 `wide`(3813페이지)를 스캔하자 `PAGES_MADE_YOUNG`이 8469 → 12204(+3735)로 늘었다. 스캔 뒤 `INNODB_BUFFER_PAGE_LRU`에서 wide 페이지 3780개가 모두 `IS_OLD = NO`였다.
- 기본 크기 `innodb_buffer_pool_size` = 128MB(134217728). 전용 서버는 흔히 물리 메모리의 80%까지 준다(17.5.1). 로컬 `POOL_SIZE 8192`페이지 = 128MB / 16KB.
- 기본 `innodb_flush_method`는 유닉스에서 `O_DIRECT`(지원 시). OS 캐시를 거치지 않으므로 InnoDB 버퍼 풀이 사실상 유일한 캐시다. PG와 반대다.

### 3. dirty 페이지는 언제 디스크로 가나

```text
  PostgreSQL                                  InnoDB
  체크포인트(checkpoint_timeout 기본 5분 등)   flush list(수정 순서) 기준 페이지 클리너
   → 시작 시점의 dirty 전부(unlogged 제외)    dirty 비율 innodb_max_dirty_pages_pct(기본 90) 근처면 공격적으로
  background writer (bgwriter_delay 200ms)     _lwm(기본 10)부터 미리 조금씩
   → 곧 희생될 dirty를 미리
  백엔드 스스로 (희생자가 dirty일 때)           LRU 꼬리 쪽 dirty도 페이지 클리너가 씀
```

- PG의 일반 체크포인트는 unlogged 테이블 버퍼를 건너뛴다. 종료·복구 종료 체크포인트에서만 그것까지 쓴다(`bufmgr.c` `BufferSync`).
- 쓰기를 "나중으로" 미루는 이유: 같은 페이지를 여러 번 고치면 한 번만 쓰면 된다. 무작위 쓰기를 모아 쓸 수도 있다.
- 미뤄도 안전한 이유는 WAL이다. 커밋 시점에는 **로그만** 디스크에 있으면 된다(no-force). 19번이 다룬다.

### 4. 왜 운영체제 캐시(mmap)에 맡기지 않나

CMU L6은 mmap에 맡길 때의 문제를 이렇게 정리한다.
- OS가 dirty 페이지를 아무 때나 디스크에 쓴다. WAL 순서를 지킬 수 없다.
- DB는 어떤 페이지가 메모리에 있는지 모른다. 스레드가 페이지 폴트로 멈춘다.
- I/O 오류가 아무 메모리 접근에서나 `SIGBUS`로 튀어나온다.
- DB가 직접 하면 쓰기 순서, 전용 선읽기, 더 나은 교체 정책을 쓸 수 있다.

PostgreSQL은 자기 버퍼 풀 + OS 페이지 캐시를 **함께** 쓴다(read/write 시스템 콜). InnoDB는 기본 `O_DIRECT`(지원 시)로 OS 캐시를 비켜 간다. 둘 다 mmap으로 테이블을 매핑하지는 않는다.

## 쓰이는 자료구조·알고리즘

- **해시 테이블(page table)**: (파일, 블록) → 프레임. PostgreSQL은 이 매핑을 `NUM_BUFFER_PARTITIONS`개로 나눈 락으로 지킨다(버퍼 README "BufMappingLock"). → [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- **LRU 리스트(이중 연결 리스트 + 해시)**: InnoDB의 young/old 두 구간 리스트. → [data-structure/10-lru-cache](../../data-structure/10-lru-cache/2-summary.md)
- **CLOCK(원형 배열 + 참조 카운터)**: PostgreSQL clock sweep. 접근 때 리스트를 옮기지 않아 전역 락이 필요 없다(버퍼 README).
- **LRU-K / 2Q 계열**: InnoDB 중간점 삽입은 "두 리스트, old에서만 쫓는다"는 LRU-2 근사로 CMU L6이 소개한다.
- **링 버퍼**: PG의 스캔 전용 256KB 고리. 큐처럼 돌려 쓴다.
- **참조 카운트(핀)**: 내쫓기 금지 표시. 락과 별개다.

## 적용 — 풀어나가는 법

**1) 적중률을 본다.**

```sql
-- PostgreSQL 17: DB 단위 누적 적중률 (OS 캐시 적중은 read로 셈)
SELECT datname, blks_hit, blks_read,
       round(blks_hit * 100.0 / nullif(blks_hit + blks_read, 0), 1) AS hit_pct
FROM pg_stat_database WHERE datname = current_database();

-- PostgreSQL 17: 컨텍스트별 I/O (bulkread = 링 버퍼 스캔)
SELECT backend_type, context, reads, hits, evictions, reuses
FROM pg_stat_io WHERE object = 'relation' AND backend_type = 'client backend';
```

```sql
-- MySQL 8.4
SHOW ENGINE INNODB STATUS\G      -- BUFFER POOL AND MEMORY 절
SELECT POOL_SIZE, FREE_BUFFERS, DATABASE_PAGES, OLD_DATABASE_PAGES,
       PAGES_MADE_YOUNG, PAGES_NOT_MADE_YOUNG, HIT_RATE
FROM information_schema.INNODB_BUFFER_POOL_STATS;
```

```text
  SHOW ENGINE INNODB STATUS 발췌 (예시, MySQL 8.4.10)
  Buffer pool size   8192
  Free buffers       1
  Database pages     8191
  Old database pages 3003
  Modified db pages  2179
  Pages made young 14009, not young 600608
  Buffer pool hit rate 1000 / 1000, young-making rate 0 / 1000 not 157 / 1000
```

- `not young`이 크게 오르면 old 구간에 머물며 young으로 승격되지 않은 페이지(스캔 등)가 많다는 뜻이다(17.5.1). 축출된 수를 세는 값은 아니다.
- 적중률 하나만 보지 않는다. 느린 쿼리의 `Buffers: read=`를 본다.

**2) 한 쿼리가 버퍼를 얼마나 쓰는지 본다.**

```sql
-- PostgreSQL
EXPLAIN (ANALYZE, BUFFERS) SELECT sum(v) FROM wide;
--   Buffers: shared hit=32 read=6635   ← hit은 버퍼 풀, read는 그 밖(OS 캐시 또는 디스크)
-- 버퍼 풀 안의 페이지를 테이블별로 (pg_buffercache 확장)
SELECT count(*), max(usagecount) FROM pg_buffercache
WHERE relfilenode = pg_relation_filenode('narrow')
  AND reldatabase = (SELECT oid FROM pg_database WHERE datname = current_database());   -- 다른 DB 버퍼 제외
```

**3) 크기를 정한다.**
- PostgreSQL: `shared_buffers`는 서버 재시작이 필요하다. 전용 서버에서 RAM 25%에서 시작한다(문서 권고). 늘리면 `max_wal_size`도 함께 본다(19.4.1).
- MySQL: `innodb_buffer_pool_size`는 동적으로 바꿀 수 있고, 청크 크기 × 인스턴스 수의 배수로 맞춰진다(17.8.3.1). 17.5.1은 전용 서버에서 물리 메모리의 최대 80%까지 버퍼 풀에 준다고 적는다.

**4) 재시작 직후 차가운 캐시를 데운다.**
- MySQL: `innodb_buffer_pool_dump_at_shutdown`·`load_at_startup`이 기본 ON이다(로컬 확인 1, 1). 종료 때 페이지 목록을 저장하고 시작 때 다시 읽는다.
- PostgreSQL: contrib `pg_prewarm`(autoprewarm 워커)로 같은 일을 한다.

**5) 앱 쪽에서 할 일 (Java).** 버퍼 풀은 DB 안에 있지만, 풀을 오염시키는 쿼리는 앱이 보낸다.

```java
// 대량 내보내기는 한 번에 다 읽지 말고 keyset으로 나눠 읽는다 → 스캔 폭과 시간이 줄어든다
String sql = "SELECT id, amount FROM orders WHERE id > ? ORDER BY id LIMIT 1000";
long last = 0;
while (true) {
    try (PreparedStatement ps = conn.prepareStatement(sql)) {
        ps.setLong(1, last);
        try (ResultSet rs = ps.executeQuery()) {
            int n = 0;
            while (rs.next()) { last = rs.getLong(1); n++; /* write out */ }
            if (n == 0) break;
        }
    }
}
// 분석성 풀 스캔은 복제본(읽기 전용 서버)으로 보낸다
```

## 장애 시나리오와 대처

**1) 대형 순차 스캔이 버퍼 풀을 오염 → OLTP 적중률 급락 (⚠)**
- 현상: 새벽 리포트·`mysqldump`·백필 배치가 돈 뒤 OLTP p99가 뛴다. 배치가 끝나도 한동안 느리다.
- 보이는 형태
  - MySQL: `Buffer pool hit rate`가 떨어지고 `Pages made young`이 급증, 디스크 읽기 IOPS 증가. 느린 쿼리 로그에 평소 빠르던 PK 조회가 보인다.
  - PostgreSQL: `pg_stat_database.blks_read` 증가, 느린 쿼리의 `Buffers: read=` 증가.
- 원인: LRU·CLOCK은 "최근에 읽었다"를 "곧 또 읽는다"로 착각한다. 한 번 쓰고 버릴 페이지가 자주 쓰던 페이지를 밀어낸다.
  - InnoDB: 스캔 접근이 `innodb_old_blocks_time`(1초)을 넘겨 다시 오면 young으로 올라간다. 긴 스캔 안의 반복 접근, 같은 테이블을 여러 번 도는 배치가 그렇다.
  - PostgreSQL: 테이블이 `shared_buffers`의 1/4 이하면 링을 쓰지 않는다. 그 정도 크기의 스캔 여러 개가 동시에 돌면 풀을 채운다. 링 결정은 테이블 순차 스캔 초기화(`initscan`)에 있으므로, 일반 인덱스 스캔으로 많은 페이지를 읽을 때는 링이 없다.
- 대처
  - 배치·분석은 복제본으로 보낸다.
  - 한 번에 다 읽지 않고 keyset으로 나눠 읽는다.
  - MySQL: 배치 시간대에 `innodb_old_blocks_time`을 늘리는 방법이 문서에 있다(17.8.3.3). 전역 변수이므로 운영 합의가 필요하다.
  - 크기가 부족하면 버퍼 풀을 늘린다.

**2) 재시작·페일오버 직후 한동안 느리다 (차가운 캐시)**
- 현상: 배포·재시작 뒤 수 분에서 수십 분 동안 응답이 느리다.
- 보이는 형태: 디스크 읽기 IOPS 포화, `blks_read` 급증. InnoDB `Free buffers`가 크다.
- 원인: 버퍼 풀이 비었다. 모든 요청이 miss다. 복제본으로 페일오버해도 그 서버의 풀이 차가우면 같다.
- 대처: MySQL 버퍼 풀 덤프/로드(기본 ON) 확인, PG `pg_prewarm`. 트래픽을 점진적으로 넣는다.

**3) 버퍼 풀을 너무 크게 잡아 OOM·스왑**
- 현상: DB 프로세스가 죽거나(OOM killer), 스왑으로 모든 게 느려진다.
- 보이는 형태: 커널 로그 `Out of memory: Killed process … (mysqld)`, 컨테이너 exit code 137. `vmstat`의 si/so 증가.
- 원인: 버퍼 풀 + 연결당 메모리(PG `work_mem` × 정렬 노드 수, MySQL 세션 버퍼) + OS가 필요한 양을 넘겼다. 컨테이너 메모리 한도를 모르고 호스트 기준으로 잡은 경우가 흔하다([os/13-oom-and-memory-limits](../../os/13-oom-and-memory-limits/2-summary.md)).
- 대처: 버퍼 풀을 한도 안에서 잡는다(PG 25% 시작, InnoDB는 연결 수를 고려). PostgreSQL은 OS 캐시에도 기대므로 `shared_buffers`를 무작정 키우는 것이 이득이 아닐 수 있다(40% 문구).

**4) 체크포인트·flush 폭주로 쓰기 지연이 튄다**
- 현상: 몇 분마다 쓰기 지연이 주기적으로 튄다.
- 보이는 형태: PG 로그 `checkpoints are occurring too frequently`(`checkpoint_warning`), `pg_stat_checkpointer`의 요청 체크포인트 증가. InnoDB `Modified db pages`가 풀의 큰 비율.
- 원인: dirty 페이지가 한꺼번에 디스크로 나간다. 버퍼 풀이 클수록 한 번에 쓸 양도 크다.
- 대처: PG는 `max_wal_size`·`checkpoint_completion_target`으로 쓰기를 펼친다. InnoDB는 `innodb_io_capacity`와 `_lwm`으로 미리 조금씩 쓴다. 자세한 조정은 19번.

## 핵심 문장

- 버퍼 풀은 디스크 페이지를 담는 DB 자신의 캐시다. page table(해시) → 프레임, 프레임마다 핀과 dirty가 있다.
- 핀이 잡힌 페이지는 내쫓지 못한다. WAL로 기록된 변경을 담은 dirty 페이지는 쓰기 전에 그 WAL이 먼저 디스크에 있어야 한다(PG unlogged 테이블처럼 WAL이 없는 페이지는 해당 없음).
- LRU·CLOCK은 순차 스캔에 약하다. 한 번 읽고 버릴 페이지가 자주 쓰던 페이지를 밀어낸다.
- PostgreSQL 17은 clock sweep(usage_count 최대 5)에 더해, `shared_buffers`의 1/4보다 큰 테이블의 순차 스캔을 256KB 링 버퍼에 가둔다.
- MySQL 8.4 InnoDB는 새 페이지를 LRU 중간점(old 3/8의 머리)에 넣고, 1초(`innodb_old_blocks_time`) 안의 재접근은 승격하지 않는다.
- PostgreSQL은 OS 페이지 캐시를 함께 쓰고, InnoDB는 기본 `O_DIRECT`(지원되는 유닉스)로 OS 캐시를 비켜 간다. 그래서 권장 크기가 다르다.

## 관련 주제·근거

- 선행
  - [06-pages-and-tuple-layout](../06-pages-and-tuple-layout/2-summary.md) — 버퍼 풀이 담는 단위인 페이지
  - [data-structure/10 lru-cache](../../data-structure/10-lru-cache/2-summary.md) — 해시맵 + 이중 연결 리스트, LRU/CLOCK 계열
- 연결
  - [os/12-swapping-and-page-replacement](../../os/12-swapping-and-page-replacement/2-summary.md) — 같은 교체 문제의 OS 판
  - [os/14-mmap-and-page-cache](../../os/14-mmap-and-page-cache/2-summary.md) — OS 페이지 캐시와 이중 캐싱
  - [os/24-fsync-and-durability](../../os/24-fsync-and-durability/2-summary.md) — dirty 페이지와 내구성
  - [08-btree-indexes](../08-btree-indexes/2-summary.md) — 무작위 키 삽입이 버퍼 풀 적중률에 미치는 영향
  - database [19-wal-and-logging](../19-wal-and-logging/2-summary.md) — dirty 페이지를 쓰기 전 로그 flush, no-force/steal.
- 문서·소스
  - PostgreSQL `src/backend/storage/buffer/README`(REL_17_STABLE) — 핀, clock sweep, 링 버퍼(256KB·VACUUM·16MB bulk write), background writer <https://github.com/postgres/postgres/blob/REL_17_STABLE/src/backend/storage/buffer/README>
  - PostgreSQL `src/backend/storage/buffer/freelist.c` `GetAccessStrategy`(256 / 16×1024 / 2048 KB) · `src/include/storage/buf_internals.h` `BM_MAX_USAGE_COUNT 5` · `src/backend/access/heap/heapam.c` `initscan`(`rs_nblocks > NBuffers / 4`)
  - PostgreSQL 17 문서 19.4.1 Memory(`shared_buffers` 기본 128MB, 25%·40% 문구) · 19.4.5 Background Writer <https://www.postgresql.org/docs/17/runtime-config-resource.html>
  - PostgreSQL 17 문서 F.25 pg_buffercache(`usagecount`, `pg_buffercache_evict`) · 27.2.13 `pg_stat_io` <https://www.postgresql.org/docs/17/pgbuffercache.html>
  - PostgreSQL 17 문서 14.1 Using EXPLAIN(`BUFFERS`) <https://www.postgresql.org/docs/17/using-explain.html>
  - MySQL 8.4 Reference Manual 17.5.1 Buffer Pool(중간점 삽입, 3/8, 80%, 모니터 출력) <https://dev.mysql.com/doc/refman/8.4/en/innodb-buffer-pool.html>
  - MySQL 8.4 17.8.3.3 Making the Buffer Pool Scan Resistant(`innodb_old_blocks_pct` 37, `innodb_old_blocks_time` 1000) <https://dev.mysql.com/doc/refman/8.4/en/innodb-performance-midpoint_insertion.html>
  - MySQL 8.4 17.14 InnoDB Startup Options and System Variables(`innodb_buffer_pool_size` 134217728, `innodb_flush_method` O_DIRECT, `innodb_max_dirty_pages_pct` 90, `_lwm` 10, 덤프/로드 ON) <https://dev.mysql.com/doc/refman/8.4/en/innodb-parameters.html>
- 강의: CMU 15-445 Fall 2024 L6 Memory Management(강의 노트 제목 "Buffer Pools" — page table vs page directory, 핀·dirty, LRU·CLOCK, sequential flooding, LRU-K, mmap을 쓰지 않는 이유)
- 로컬 재현(PostgreSQL 17.11, MySQL 8.4.10): `pg_buffercache_evict` 후 wide(6667페이지)·narrow(443페이지) 스캔 전후 버퍼 수와 usagecount, `pg_stat_io`, InnoDB `INNODB_BUFFER_POOL_STATS`·`INNODB_BUFFER_PAGE_LRU`로 재스캔 시 young 승격, 설정값 확인
