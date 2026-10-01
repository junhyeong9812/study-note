# database/41-sorting-and-aggregation — 외부 정렬·해시 집계·디스크 스필 — 정리 (힌트)

## 해결하는 문제

`ORDER BY`, `GROUP BY`, `DISTINCT`, 병합 조인은 모두 "같은 값끼리 모으기" 또는 "순서대로 줄 세우기"가 필요하다.\
데이터가 메모리에 다 들어가면 쉽다. 들어가지 않으면 문제가 된다.

- 1억 행을 정렬하려고 1억 행을 메모리에 올릴 수는 없다.
- 그렇다고 한 쿼리가 메모리를 무한정 쓰게 두면, 동시에 돌던 다른 쿼리와 서버 전체가 위험하다.

그래서 DB는 연산마다 **메모리 한도**를 주고, 넘으면 **디스크 임시 파일로 넘긴다(스필, spill)**.\
정렬은 *외부 병합 정렬*, 집계는 *해시 분할*로 메모리보다 큰 입력을 처리한다.

쉬운 예: 시험지 1,000장을 번호순으로 정리하는데 책상에는 100장만 펼칠 수 있다.

```text
  ① 100장씩 가져와 책상에서 정렬 → 정렬된 묶음 10개를 바닥에 쌓는다   (런 만들기)
  ② 10묶음의 맨 위 장만 책상에 올리고, 가장 작은 번호를 집어 내보낸다   (k-way 병합)
     집은 묶음에서 다음 장을 올린다 → 반복
```

똑같은 구조다.\
실무 예: 대시보드 쿼리의 `EXPLAIN ANALYZE`에 `Sort Method: external merge  Disk: 26936kB`가 보인다. 정렬이 `work_mem`(PostgreSQL 17 기본 4MB)을 넘어 디스크를 썼다는 뜻이다.

## 동작·원리

### 1. 메모리 안 정렬 → 넘치면 외부 병합 정렬

```text
  입력 N 페이지, 쓸 수 있는 버퍼 B 페이지

  단계 1 (런 만들기)                          단계 2 (병합)
  ┌─B─┐┌─B─┐┌─B─┐ ... ⌈N/B⌉개                 런들의 맨 앞 행만 힙에 넣는다
  │정렬││정렬││정렬│  → 임시 파일에 "런"으로       힙에서 최솟값을 꺼내 출력하고,
  └───┘└───┘└───┘                              그 런의 다음 행을 힙에 넣는다
                                              한 번에 최대 B−1개 런을 병합

  통과 횟수 = 1 + ⌈log_(B−1) ⌈N/B⌉⌉       I/O = 2N × 통과 횟수   (CMU 15-445 L11)
```

- *런(run)*: 정렬된 한 덩어리다. 메모리에 들어가는 만큼 정렬해 임시 파일에 쓴다.
- *k-way 병합*: k개 런의 맨 앞만 보고 가장 작은 것을 고르는 병합이다. 최소 힙을 쓰면 한 번에 O(log k)다.
- 계산 예 (예시): N = 3,367페이지(8KB 페이지로 약 26MB), B = 512페이지(4MB).
  - 런 = ⌈3,367 / 512⌉ = 7개.
  - 7 ≤ 511이므로 병합 한 번이면 끝난다 → 통과 2회, 이론 I/O = 2 × 3,367 × 2.

PostgreSQL 17의 실제 구현(`tuplesort.c` 머리 주석):

- 처음에는 정렬하지 않은 배열에 행을 모은다. 끝까지 `work_mem` 안이면 **퀵소트**로 끝낸다.
- 넘으면 퀵소트로 런을 만들어 임시 "테이프"에 쓴다. 병합은 **균형 k-way 병합**이다. PostgreSQL 15 전에는 polyphase 병합을 썼다.
- 결과를 임의 접근할 필요가 없으면, **마지막 병합은 디스크에 쓰지 않고** 호출자에게 행을 넘기며 바로 한다. 한 번의 쓰기·읽기를 아낀다.
- 각 테이프에서 `workMem / M`만큼씩 미리 읽어, 임시 파일 접근을 순차적으로 만든다.

### 2. LIMIT이 붙으면 — Top-N 힙 정렬

```text
  ORDER BY note LIMIT 10

  크기 10의 힙만 유지: 새 행이 힙의 최악보다 좋으면 교체
    (오름차순이면 "최악" = 가장 큰 값을 루트에 두는 힙 — 병합의 최소 힙과 방향이 반대)
  메모리 = 10행분 → 스필 없음 (LIMIT이 작아 한도 안에서 힙으로 바뀔 때)

  로컬 재현 (예시, PostgreSQL 17.11, 50만 행):
    Sort Method: top-N heapsort  Memory: 26kB
```

- PostgreSQL은 모은 행 수가 필요한 개수(LIMIT)의 두 배를 넘거나, `work_mem`이 찼고 필요한 개수 이상을 모았으면 *한정 힙(bounded heap)*으로 전환한다(`tuplesort.c`의 `TSS_BOUNDED` 주석: 힙 정렬이 퀵소트보다 싸지는 지점의 휴리스틱).
  - 조건이 있다. 정렬에 맞는 인덱스를 읽으면 정렬 자체가 없다(11.4). LIMIT이 커서 필요한 개수를 다 모으기 전에 `work_mem`이 차면 힙으로 못 바뀌고 디스크 런을 만든다(`tuplesort_puttuple_common`). 한정 힙은 루트에 가장 큰 값을 두도록 비교 방향을 뒤집는다(`make_bounded_heap` 주석).
- MySQL 8.4도 같은 최적화가 있다. 옵티마이저 트레이스의 `filesort_summary`에 `"using_priority_queue"`로 나온다(로컬 재현: `LIMIT 10`에서 최대 메모리 7,381바이트).

### 3. 집계 — 정렬 기반 vs 해시 기반

```text
  GROUP BY user_id

  정렬 집계 (GroupAggregate)              해시 집계 (HashAggregate)
  입력을 user_id로 정렬                   해시 테이블 {user_id → 누적값}
  → 같은 키가 붙어 나온다                   행마다: 있으면 누적, 없으면 새 항목
  → 키가 바뀔 때마다 한 그룹 출력             → 끝나면 테이블을 훑어 출력
  출력이 정렬돼 있다                       출력 순서 없음
  메모리: 정렬 한도(work_mem)               메모리: 그룹 수 × 항목 크기
```

- 입력이 이미 정렬돼 있으면(인덱스 순서 등) 정렬 집계가 정렬 비용 없이 된다. 아니면 보통 해시 집계가 싸다(CMU L11).
- 누적값은 함수마다 다르다. `AVG`는 (합, 개수)를 들고 다닌다(CMU L11).

**해시 집계가 넘칠 때** — 두 방식

```text
  CMU 교과서 방식 (분할 → 재해시)
    1) h1(키)로 B−1개 분할 파일에 나눠 쓴다 (같은 키는 같은 파일로)
    2) 분할 파일 하나씩 읽어 h2로 해시 테이블을 만들고 집계

  PostgreSQL 17 (nodeAgg.c "Spilling To Disk")
    1) 해시 테이블이 한도에 닿으면 "스필 모드"
    2) 이미 테이블에 있는 그룹은 계속 누적
    3) 새 그룹이 될 행만 해시 상위 비트로 분할 파일에 쓴다
    4) 나중에 분할 파일을 하나씩 다시 집계 (또 넘치면 재귀적으로 다시 분할)
```

- 분할 수는 추정 그룹 수로 정하고 최소 4, 최대 1024개다(`HASHAGG_MIN_PARTITIONS`, `HASHAGG_MAX_PARTITIONS`). 스필된 행의 서로 다른 키 수는 HyperLogLog로 추정한다(`nodeAgg.c`).
- 해시 연산의 한도는 `work_mem × hash_mem_multiplier`다. 기본 4MB × 2.0 = 8MB(PostgreSQL 19.4.1).

### 4. 메모리 한도 — 제품별

```text
  PostgreSQL 17
    work_mem            4MB   정렬·해시 "연산 하나"의 기본 한도
    hash_mem_multiplier 2.0   해시 연산은 work_mem × 2
    temp_file_limit     -1    프로세스 하나의 임시 파일 총량 상한 (-1 = 무제한)
    log_temp_files      -1    임시 파일을 지울 때 이름·크기를 로그로 (-1 = 끔)
    ※ 한 쿼리에 정렬·해시 노드가 여러 개면 각자 한도만큼 쓴다.
      세션이 여럿이면 또 곱해진다. 총 메모리는 work_mem의 몇 배가 될 수 있다.

  MySQL 8.4
    sort_buffer_size        262144 (256KB)   filesort 한 번의 버퍼
    tmp_table_size          16MiB            메모리 내부 임시 테이블 하나의 상한 → 넘으면 InnoDB 디스크 임시 테이블
    temptable_max_ram       미설정 시 서버 메모리의 3% (최소 1GB, 최대 4GB)   TempTable 엔진 전체 RAM 상한
    temptable_max_mmap      0 (메모리 매핑 파일 안 씀 → 넘치면 InnoDB 디스크 임시 테이블)
    Sort_merge_passes       상태 변수 — 정렬 병합 통과 횟수
```

- PostgreSQL 문서: 정렬은 `ORDER BY`, `DISTINCT`, 병합 조인에 쓰고, 해시 테이블은 해시 조인, 해시 집계, memoize, 해시 기반 `IN` 서브쿼리에 쓴다(19.4.1).

### 5. 로컬 재현 — 스필이 곧 느림은 아니었다

```text
  (예시, PostgreSQL 17.11, 병렬 끔) ev 50만 행, ORDER BY note (md5 문자열, en_US.utf8 정렬 규칙)

  work_mem = 4MB   → Sort Method: external merge  Disk: 26936kB   Execution Time: 855 ms (다시 돌려 929·933 ms)
  work_mem = 128MB → Sort Method: quicksort  Memory: 43539kB      Execution Time: 1033 ms (1073·1043 ms)
  ORDER BY note COLLATE "C"
    4MB   → external merge  Disk: 43120kB   323 ms
    128MB → quicksort  Memory: 59164kB     342 ms

  GROUP BY user_id (30만 그룹)
  4MB  → HashAggregate  Planned Partitions: 4  Batches: 5  Memory Usage: 8241kB  Disk Usage: 11368kB  256 ms
  64MB → HashAggregate  Batches: 1  Memory Usage: 32785kB                                            224 ms
  enable_hashagg=off, 4MB → GroupAggregate ← Sort (external merge Disk: 8848kB)                     259 ms
```

- 이 환경에서는 스필한 정렬이 메모리 정렬보다 **느리지 않았다.** 이유 후보:
  - 임시 파일이 OS 페이지 캐시에 머물러 실제 디스크 I/O가 거의 없었다([os/14-mmap-and-page-cache](../../os/14-mmap-and-page-cache/2-summary.md)).
  - 런이 7개 정도라 병합 한 번이면 되고, 마지막 병합은 디스크에 쓰지 않는다.
  - 비용의 대부분이 문자열 비교였다. `COLLATE "C"`(바이트 비교)로 바꾸자 3배 빨라졌다.
- 그러니 `external merge`는 **메모리를 넘었다는 신호**다. 그것만으로 병목이라는 증거는 아니다. 임시 파일이 캐시를 넘고 저장장치가 느리거나 바쁘면, 또는 병합 통과가 여러 번이면 크게 느려질 수 있다. 몇 배 느려지는지는 저장장치·동시 부하에 달렸다.

MySQL 8.4 (로컬 재현, 20만 행, `ORDER BY note`, `char(32)`):

```text
  sort_buffer_size = 256KB(기본):  "num_initial_chunks_spilled_to_disk": 101, Sort_merge_passes = 15
  sort_buffer_size = 64MB:         "num_initial_chunks_spilled_to_disk": 0,   peak_memory_used 30,729,430
  GROUP BY user_id (10만 그룹):    -> Aggregate using temporary table
```

## 쓰이는 자료구조·알고리즘

- **외부 병합 정렬 · k-way 병합** — 런을 만들고 최소 힙으로 병합한다. [algorithm/02-merge-sort](../../algorithm/02-merge-sort/2-summary.md), algorithm `11-external-sort-and-k-way-merge`(미작성, [algorithm/curriculum](../../algorithm/curriculum.md))
- **힙** — 병합의 "다음 최솟값"은 최소 힙. Top-N의 한정 힙은 반대로 "지금까지의 N개 중 최악"을 루트에 둔다(오름차순이면 최대 힙, `make_bounded_heap`). [data-structure/07-heap](../../data-structure/07-heap/2-summary.md), [algorithm/04-heap-sort](../../algorithm/04-heap-sort/2-summary.md)
- **퀵소트** — PostgreSQL은 메모리 안 정렬과 런 만들기 모두 퀵소트다(`tuplesort.c`). 예전의 대체 선택(replacement selection, 힙)은 쓰지 않는다.
- **해시 테이블** — 해시 집계의 {키 → 누적 상태}. [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- **해시 분할(재귀)** — 해시 값의 비트 일부로 분할을 고르고, 재귀할 때는 아직 안 쓴 비트를 쓴다(`nodeAgg.c`).
- **HyperLogLog** — 스필된 행의 서로 다른 키 수를 작은 메모리로 추정해 다음 분할 수를 정한다. [data-structure/19-probabilistic-counting](../../data-structure/19-probabilistic-counting/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 스필을 찾는다

```sql
-- PostgreSQL: 계획에서
EXPLAIN (ANALYZE, BUFFERS) SELECT ... ORDER BY ...;
--   Sort Method: external merge  Disk: …kB
--   HashAggregate … Batches: N (N > 1)  Disk Usage: …kB
--   Buffers: … temp read=… written=…

-- 데이터베이스 누적
SELECT datname, temp_files, temp_bytes FROM pg_stat_database;

-- 로그로 (슈퍼유저 또는 권한 있는 역할)
SET log_temp_files = 0;
--   LOG:  temporary file: path "base/pgsql_tmp/pgsql_tmp7939.0", size 21602304   (로컬 재현)
```

```sql
-- MySQL 8.4
SHOW SESSION STATUS LIKE 'Sort_merge_passes';
SET optimizer_trace = 'enabled=on';
SELECT ...;
SELECT JSON_EXTRACT(trace, '$**.filesort_summary') FROM information_schema.OPTIMIZER_TRACE;
EXPLAIN ANALYZE SELECT ... GROUP BY ...;    -- "Aggregate using temporary table"
```

### 2. 고르는 순서 — 메모리를 올리기 전에

1. **정렬 자체를 없앤다.** `ORDER BY`·`GROUP BY` 컬럼 순서에 맞는 인덱스가 있으면 인덱스 순서로 읽어 정렬을 건너뛸 수 있다. MySQL은 `EXPLAIN`의 `Extra`에 `Using filesort`가 없으면 인덱스로 해결한 것이다(10.2.1.16).
2. **정렬할 양을 줄인다.** 필터를 먼저 하고, 필요한 컬럼만 고른다(`SELECT *` 대신). 넓은 행은 정렬 메모리를 빨리 채운다.
3. **LIMIT을 쓴다.** LIMIT이 작으면 Top-N 힙 정렬로 바뀌어 메모리가 작아진다.
4. 문자열 정렬이면 **정렬 규칙 비용**을 본다. 바이트 순서로 충분한 곳(내부 키 등)은 `COLLATE "C"`를 검토한다. 단 결과 순서가 바뀐다(10번).
5. 그래도 필요하면 **그 쿼리·역할에만** 메모리를 올린다.

```sql
-- PostgreSQL: 트랜잭션 하나에만
BEGIN; SET LOCAL work_mem = '256MB'; SELECT ...; COMMIT;
-- 배치 전용 역할에만
ALTER ROLE batch_user SET work_mem = '256MB';
-- 해시만 부족할 때
SET hash_mem_multiplier = 4.0;

-- MySQL: 문장 하나에만
SELECT /*+ SET_VAR(sort_buffer_size = 16777216) */ ... ORDER BY ...;
```

- 전역 `work_mem`을 크게 올리지 않는다. 노드 수 × 동시 세션 수만큼 곱해져 메모리 부족(OOM)으로 번질 수 있다(19.4.1 경고). 해시가 자주 넘치면 `work_mem` 대신 `hash_mem_multiplier`를 올리라고 문서가 권한다.

### 3. 임시 파일에 울타리를 친다

```sql
SET temp_file_limit = '1MB';   -- (로컬 재현용으로 작게)
SELECT count(*) FROM (SELECT * FROM ev ORDER BY note) x;
-- ERROR:  53400: temporary file size exceeds temp_file_limit (1024kB)
```

- 운영에서는 디스크를 다 채우기 전에 한 쿼리를 끊는 안전장치로 쓴다. 넘으면 그 트랜잭션이 취소된다(19.4.2).
- MySQL은 `tmpdir`을 넉넉한 전용 파일 시스템으로 두라고 문서가 권한다(10.2.1.16).

## 장애 시나리오와 대처

### 1. 대시보드 쿼리가 느리고 계획에 `external merge`가 보인다 (⚠ work_mem 초과 → 디스크 스필)

- **현상**: 특정 리포트가 평소보다 수 배 느리다. 데이터가 늘어난 뒤부터다.
- **보이는 형태**: `Sort Method: external merge  Disk: …kB`, `Buffers: temp read=… written=…`. `pg_stat_database.temp_bytes`가 늘어난다. 저장장치 지표에 쓰기 급증.
- **원인**: 정렬 입력이 `work_mem`(4MB)을 넘었다. 임시 파일이 캐시를 넘어 실제 디스크 I/O가 되면 느려진다. 동시에 여러 쿼리가 스필하면 디스크를 두고 경쟁한다.
- **대처**
  - 먼저 확인: 정말 스필이 원인인가? `SET LOCAL work_mem`을 올려 같은 쿼리를 다시 재 본다. 로컬 재현처럼 차이가 없으면 병목은 다른 곳(비교 비용, 스캔)이다.
  - 원인이면 위 「고르는 순서」대로: 인덱스로 정렬 제거 → 컬럼·행 줄이기 → 쿼리 단위 메모리 증가.

### 2. `work_mem`을 전역으로 올렸더니 DB가 죽었다

- **현상**: 스필을 없애려고 `work_mem = 512MB`로 올렸다. 트래픽이 몰린 시간에 PostgreSQL 백엔드가 죽고 전체가 재시작된다.
- **보이는 형태**: 서버 로그에 `server process (PID …) was terminated by signal 9: Killed`(`postmaster.c`의 "was terminated by signal" 형식)와 `Failed process was running: …`. 커널 로그(`dmesg`)에 OOM killer 기록. 이어서 postmaster가 다른 세션을 끊고 복구를 시작한다.
- **원인**: 한도는 **연산 하나**에 대한 것이다. 조인·정렬·집계 노드가 5개인 쿼리를 100 세션이 동시에 돌리면 이론상 수백 배를 쓸 수 있다. 해시 노드는 그 2배(`hash_mem_multiplier`)까지다.
- **대처**: 전역값은 작게 두고 무거운 쿼리·역할에만 올린다. 커넥션 수를 풀로 제한한다(21번). 컨테이너 메모리 한도와 OOM 동작은 [os/13-oom-and-memory-limits](../../os/13-oom-and-memory-limits/2-summary.md).

### 3. 임시 파일이 디스크를 채웠다

- **현상**: 한 분석 쿼리가 돌던 중 DB 디스크 사용률이 치솟고, 다른 쓰기까지 실패한다.
- **보이는 형태**: `pgsql_tmp` 디렉터리가 커진다. 디스크가 차면 임시 파일 쓰기가 `could not write to file "…": No space left on device`로 실패한다(`buffile.c`의 메시지 형식 + ENOSPC).
- **원인**: 거대한 정렬·해시(예: 조인 폭발 후 `DISTINCT`)가 임시 파일을 끝없이 썼다. `temp_file_limit`은 기본 무제한이다.
- **대처**: `temp_file_limit`을 설정해 그 쿼리만 `53400`으로 취소되게 한다. `log_temp_files`로 큰 임시 파일을 쓰는 쿼리를 평소에 찾아 둔다.

### 4. 추정이 틀려 해시 집계가 여러 배치로 쪼개진다

- **현상**: 그룹 수를 적게 추정한 집계가 느리다.
- **보이는 형태**: `HashAggregate … Planned Partitions: 4  Batches: 5  Disk Usage: …`. 추정 그룹 수(`rows=`)와 실제가 크게 다르다.
- **원인**: 옵티마이저가 그룹 수(`n_distinct`)를 적게 봐서 해시 집계를 골랐는데, 실제로는 한도를 넘어 스필했다. 너무 적게 잡으면 재귀 분할까지 간다.
- **대처**: 통계 개선(12번: `ANALYZE`, `SET STATISTICS`, 확장 통계의 `ndistinct`). 필요하면 `hash_mem_multiplier`를 올린다.

### 5. MySQL `GROUP BY`가 느리고 `Using temporary`가 보인다

- **현상**: `GROUP BY`·`DISTINCT` 쿼리가 데이터가 커지며 급격히 느려진다.
- **보이는 형태**: `EXPLAIN`의 `Extra`에 `Using temporary`(또는 `Using filesort`), `EXPLAIN ANALYZE`에 `Aggregate using temporary table`. 디스크 임시 테이블이 만들어지면 상태 변수 `Created_tmp_disk_tables`가 는다. 문서는 메모리 매핑 파일로 넘친 경우는 이 값에 안 잡힌다는 알려진 한계를 적는다(10.4.4). 다만 MySQL 8.4 기본값(`temptable_max_mmap` = 0, `temptable_use_mmap` = OFF)에서는 메모리 매핑 파일을 쓰지 않고 곧바로 InnoDB 디스크 임시 테이블로 넘긴다(7.1.8, 로컬 재현 `@@temptable_max_mmap = 0`). TempTable의 RAM 사용량은 Performance Schema `memory/temptable/physical_ram`으로 본다. `physical_disk`는 메모리 매핑 파일로 넘칠 때의 공간만 세므로, 기본값(mmap 안 씀)에서는 InnoDB 디스크 임시 테이블 사용량이 아니다(10.4.4).
- **원인**: `Using temporary` 자체는 "내부 임시 테이블을 쓴다"는 뜻일 뿐이다. 메모리 TempTable만 써도 나온다. 느린 원인이 디스크라면 내부 임시 테이블이 `tmp_table_size`(16MiB) 또는 TempTable 전체 한도를 넘어 InnoDB 디스크 임시 테이블로 넘어간 경우다(10.4.4). `Created_tmp_disk_tables` 증가로 확인한다.
- **대처**: `GROUP BY` 컬럼 순서의 인덱스로 임시 테이블을 없앤다(MySQL `GROUP BY` 최적화, 10.2.1.17). 안 되면 세션·문장 단위로 `tmp_table_size`를 올린다.

## 핵심 문장

- 정렬·집계는 연산마다 메모리 한도가 있고, 넘으면 디스크 임시 파일로 스필한다(PostgreSQL `work_mem` 4MB, 해시는 ×2; MySQL `sort_buffer_size` 256KB, 내부 임시 테이블 16MiB).
- 외부 병합 정렬은 메모리 크기의 런을 만든 뒤 최소 힙으로 k-way 병합한다. 통과 횟수는 1 + ⌈log_(B−1)⌈N/B⌉⌉이다.
- 해시 집계가 넘치면 PostgreSQL은 기존 그룹은 계속 누적하고 새 그룹이 될 행만 해시 분할해 스필한 뒤 나중에 다시 집계한다.
- `external merge`는 한도를 넘었다는 신호이지 병목의 증거가 아니다. 로컬 재현에서는 페이지 캐시 덕에 느려지지 않았다. 확인은 메모리를 올려 다시 재 보는 것이다.
- 고치는 순서는 정렬 제거(인덱스) → 양 줄이기(필터·컬럼·LIMIT) → 쿼리·역할 단위 메모리 증가다. 전역 `work_mem`을 크게 올리면 노드 × 세션만큼 곱해져 OOM으로 번진다.

## 관련 주제·근거

- 선행
  - database `07-buffer-pool` — 버퍼와 페이지 → [../07-buffer-pool/2-summary.md](../07-buffer-pool/2-summary.md)
  - algorithm `11-external-sort-and-k-way-merge` — 미작성, [algorithm/curriculum](../../algorithm/curriculum.md) · 기존 [algorithm/02-merge-sort](../../algorithm/02-merge-sort/2-summary.md)
- 후속·연결
  - database `11-join-algorithms` — 병합 조인(정렬 재사용)과 해시 조인(같은 해시 분할) → [../11-join-algorithms/2-summary.md](../11-join-algorithms/2-summary.md)
  - database `12-query-optimizer-and-explain` — 그룹 수 추정과 계획 선택 → [../12-query-optimizer-and-explain/2-summary.md](../12-query-optimizer-and-explain/2-summary.md)
  - database `54-query-execution-models` — 정렬·해시는 파이프라인 차단 연산자 → [../54-query-execution-models/2-summary.md](../54-query-execution-models/2-summary.md)
  - 문법 쪽: [sql/59 스캔·조인·정렬 연산자](../../../languages/sql/syntax/59-scan-join-sort-operators/2-summary.md)
- 교재
  - CMU 15-445/645 Fall 2024 Lecture #11 "Sorting & Aggregation Algorithms" — 외부 병합 정렬(통과 횟수·I/O 식), 이중 버퍼링, B+트리로 정렬, 정렬 집계 vs 해시 집계, 분할 → 재해시 <https://15445.courses.cs.cmu.edu/fall2024/>
- PostgreSQL 17 문서·소스
  - 19.4 Resource Consumption(`work_mem` 4MB, `hash_mem_multiplier` 2.0, `temp_file_limit` -1) <https://www.postgresql.org/docs/17/runtime-config-resource.html>
  - 19.8 Error Reporting and Logging(`log_temp_files` -1) <https://www.postgresql.org/docs/17/runtime-config-logging.html> · 27.2 `pg_stat_database`(`temp_files`, `temp_bytes`) <https://www.postgresql.org/docs/17/monitoring-stats.html>
  - `src/backend/utils/sort/tuplesort.c` 머리 주석(퀵소트 런, 균형 k-way 병합, PG15 전 polyphase, 마지막 병합 즉석 수행, 선읽기), `TSS_BOUNDED` "top-N heapsort" <https://github.com/postgres/postgres/blob/REL_17_STABLE/src/backend/utils/sort/tuplesort.c>
  - `src/backend/executor/nodeAgg.c` "Spilling To Disk"(스필 모드, 분할 4~1024, HyperLogLog) <https://github.com/postgres/postgres/blob/REL_17_STABLE/src/backend/executor/nodeAgg.c>
- MySQL 8.4 Reference Manual
  - 10.2.1.16 ORDER BY Optimization(`Using filesort`, `sort_buffer_size`, `Sort_merge_passes`, `filesort_summary`, `tmpdir`) <https://dev.mysql.com/doc/refman/8.4/en/order-by-optimization.html>
  - 10.2.1.17 GROUP BY Optimization <https://dev.mysql.com/doc/refman/8.4/en/group-by-optimization.html>
  - 10.4.4 Internal Temporary Table Use(`tmp_table_size` 16MiB, `temptable_max_ram` 3%·1~4GB, InnoDB 디스크 임시 테이블로 전환) <https://dev.mysql.com/doc/refman/8.4/en/internal-temporary-tables.html>
  - 7.1.8 Server System Variables(`sort_buffer_size` 262144)
- 로컬 재현(PostgreSQL 17.11, MySQL 8.4.10, 전용 DB `w12`): 50만 행 정렬의 external merge vs quicksort 시간 비교(스필 쪽이 느리지 않음), `COLLATE "C"` 효과, top-N heapsort 26kB, 해시 집계 5배치 스필, `temp_file_limit` 53400, `log_temp_files` 로그 형식, MySQL filesort 101청크 스필·`Sort_merge_passes` 15, 우선순위 큐 Top-N, 임시 테이블 집계
