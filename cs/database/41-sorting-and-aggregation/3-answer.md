# database/41-sorting-and-aggregation — 정답

## 정답

### 1. 외부 병합 정렬

```text
  단계 1: B페이지씩 읽어 메모리에서 정렬 → 런 ⌈N/B⌉개를 임시 파일에 쓴다
  단계 2: 런을 한 번에 최대 B−1개씩 병합 (버퍼 1개는 출력용) → 런이 하나가 될 때까지

  통과 횟수 = 1 + ⌈log_(B−1) ⌈N/B⌉⌉
  I/O      = 2N × 통과 횟수   (통과마다 모든 페이지를 한 번 읽고 한 번 쓴다)
```

- N = 3,367, B = 512: 런 = ⌈3,367/512⌉ = 7개. 7 ≤ 511이므로 병합 1회. 통과 = 1 + 1 = **2회**. 이론 I/O = 2 × 3,367 × 2 = 13,468페이지 (CMU L11 식).

### 2. 병합의 자료구조

- **최소 힙**(오름차순 병합 기준). 각 런의 맨 앞 행만 힙에 넣고, 최솟값을 꺼내 출력한 뒤 그 런의 다음 행을 넣는다.
- 행 하나당 O(log k).
- `LIMIT 10`: 크기 10짜리 힙만 유지하는 **Top-N 힙 정렬**이 된다. 새 행이 힙의 최악보다 좋으면 교체한다. 그래서 이 힙은 방향이 반대다(오름차순이면 가장 큰 값이 루트, `tuplesort.c` `make_bounded_heap`). LIMIT이 작아 한도 안에서 힙으로 바뀌면 메모리가 10행분이라 스필이 없다. 정렬에 맞는 인덱스가 있으면 힙 정렬도 없이 인덱스 순서로 10행만 읽는다. 로컬 재현(PostgreSQL 17.11): `Sort Method: top-N heapsort  Memory: 26kB`. MySQL 8.4는 트레이스에 `using_priority_queue`로 나온다.

### 3. PostgreSQL tuplesort의 특징 (`tuplesort.c` 머리 주석)

- 런 만들기: **퀵소트**. 예전의 대체 선택(힙으로 긴 런 만들기)은 더 이상 쓰지 않는다.
- 병합: PostgreSQL 15부터 **균형 k-way 병합**. 그 전에는 테이프 수가 적다고 가정한 polyphase 병합(Knuth 5.4.2D)이었다. 현대 하드웨어에서 "테이프"는 메모리 버퍼 몇 KB라 많이 둘 수 있어서 바꿨다.
- 마지막 병합: 결과를 임의 접근할 필요가 없으면 디스크에 쓰지 않고, 호출자가 행을 달라고 할 때마다 즉석으로 병합해 넘긴다. 쓰기·읽기 한 번을 아낀다.
- 덤: 각 테이프에서 `workMem/M`씩 미리 읽어 임시 파일 접근을 순차적으로 만든다.

### 4. 정렬 집계 vs 해시 집계

| | 정렬 집계(GroupAggregate) | 해시 집계(HashAggregate) |
|---|---|---|
| 동작 | 키로 정렬 → 같은 키가 연달아 옴 → 키가 바뀔 때 그룹 출력 | {키 → 누적값} 해시 테이블에 행마다 누적 → 끝나고 훑어 출력 |
| 메모리 | 정렬 한도(스필 시 외부 정렬) | 그룹 수 × 항목 크기(한도는 `work_mem × hash_mem_multiplier`) |
| 출력 순서 | 키 순서로 정렬됨 | 순서 없음 |

- 입력이 이미 키 순서면(인덱스 순서 스캔 등) 정렬 비용이 없으므로 **정렬 집계**가 유리하다. 아니면 보통 해시 집계가 싸다(CMU L11).

### 5. PostgreSQL 해시 집계 스필

- 한도에 닿으면 "스필 모드"로 들어간다.
  - 이미 해시 테이블에 있는 그룹 → 계속 누적한다.
  - 새 그룹을 만들어야 하는 행 → 해시 값의 비트로 분할을 골라 임시 파일(논리 테이프)에 쓴다.
  - 나중에 분할 파일을 하나씩 다시 집계한다. 또 넘치면 재귀적으로 다시 분할한다.
- CMU 방식과의 차이: CMU는 처음부터 **모든 행**을 h1로 분할해 쓰고, 분할마다 h2로 재해시한다. PostgreSQL은 메모리가 찰 때까지는 그냥 해시 집계를 하고, 넘친 뒤에도 **이미 있는 그룹의 행은 쓰지 않는다.** 스필 양이 줄어든다.
- 분할 수는 4~1024개(`HASHAGG_MIN/MAX_PARTITIONS`), 스필된 키 수 추정에 HyperLogLog를 쓴다.
- 기본 한도: `work_mem`(4MB) × `hash_mem_multiplier`(2.0) = **8MB**.
- 계획에서는 `Planned Partitions: 4  Batches: 5  Memory Usage: 8241kB  Disk Usage: 11368kB`처럼 보인다(로컬 재현, 30만 그룹).

### 6. `work_mem`을 올리면 항상 빨라지나

- **아니다.** 로컬 재현(PostgreSQL 17.11, 병렬 끔, 50만 행, en_US.utf8):
  - 4MB: external merge, 855 ms(재실행 929·933 ms)
  - 128MB: quicksort 43,539kB, 1,033 ms(재실행 1,073·1,043 ms) — 오히려 느렸다.
- 이유 후보
  - 임시 파일이 OS 페이지 캐시에 있어 실제 디스크 I/O가 거의 없었다.
  - 런 7개 → 병합 1회, 마지막 병합은 디스크에 쓰지 않는다.
  - 시간 대부분이 정렬 규칙(en_US.utf8) 문자열 비교였다. `COLLATE "C"`로 바꾸자 323~342 ms로 3배 빨라졌다.
- 결론: `external merge`는 "한도를 넘었다"는 신호다. 병목인지는 `SET LOCAL work_mem`으로 올려 **다시 재 봐야** 안다. 캐시를 넘는 임시 파일, 느리거나 바쁜 저장장치, 여러 번의 병합 통과가 있으면 크게 느려질 수 있다.

### 7. 전역 work_mem 증가 → 프로세스 사망

- 로그: `server process (PID …) was terminated by signal 9: Killed`, `Failed process was running: …`. 커널 로그에 OOM killer 기록. 이후 postmaster가 다른 세션을 끊고 복구한다.
- 원인: `work_mem`은 **연산 하나당** 한도다. 한 쿼리의 정렬·해시 노드 수 × 동시 세션 수만큼 곱해진다. 해시 노드는 `hash_mem_multiplier`배까지 쓴다. 피크에 합이 물리 메모리를 넘었다.
- 올바른 조정
  - 전역값은 작게 둔다.
  - 무거운 쿼리에 `SET LOCAL work_mem`, 배치 역할에 `ALTER ROLE … SET work_mem`.
  - 해시만 자주 넘치면 `hash_mem_multiplier`를 올린다(문서 권고).
  - 커넥션 수를 풀로 제한한다.

### 8. 임시 파일로 디스크가 참

- 평소에 찾기
  - `log_temp_files = 0`(또는 크기 문턱): 임시 파일을 지울 때 `LOG: temporary file: path "base/pgsql_tmp/…", size …`를 남긴다. 기본은 -1(끔).
  - `pg_stat_database.temp_files`, `temp_bytes`: DB별 누적.
  - `EXPLAIN (ANALYZE, BUFFERS)`의 `temp read/written`.
- 안전장치: `temp_file_limit`(기본 -1 = 무제한). 한 프로세스의 임시 파일 총량이 넘으면 그 트랜잭션을 취소한다.
- 오류: `ERROR: temporary file size exceeds temp_file_limit (1024kB)`, SQLSTATE `53400`(configuration_limit_exceeded). 로컬 재현에서 `temp_file_limit = '1MB'`로 확인했다.

### 9. MySQL 8.4

- 정렬 스필 확인
  - 상태 변수 `Sort_merge_passes`(로컬 재현: 기본 버퍼에서 15).
  - 옵티마이저 트레이스의 `filesort_summary`: `num_initial_chunks_spilled_to_disk`(재현: 101 → 버퍼 64MB에서 0), `peak_memory_used`.
  - `EXPLAIN`의 `Extra`에 `Using filesort`가 있으면 인덱스 대신 filesort를 한다.
- 내부 임시 테이블: 메모리 TempTable 테이블 하나가 `tmp_table_size`(기본 16MiB)를 넘으면 InnoDB 디스크 임시 테이블로 바뀐다. TempTable 전체는 `temptable_max_ram`(미설정 시 서버 메모리 3%, 1~4GB)이 상한이다.
- `sort_buffer_size` 기본: **262,144바이트(256KB)**.
