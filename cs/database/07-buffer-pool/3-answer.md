# database/07-buffer-pool — 정답

## 정답

### 1. 페이지 요청의 흐름

```text
  get_page(p)
    page table에서 p 찾기
    hit  → pin++, 사용 기록(usage_count·LRU 위치) 갱신 → 반환
    miss → 빈 프레임 또는 희생자 v 선택 (pin > 0 제외)
           v가 dirty면: (WAL을 먼저 flush) → v를 디스크에 쓰기
           p를 디스크에서 v로 읽기 → page table 갱신 → pin++ → 반환
  release: pin--, 고쳤으면 dirty 표시
```

- *page table*: (파일, 블록) → 버퍼 프레임을 담은 **메모리 해시 테이블**이다. 지금 메모리에 있는 페이지만 담는다.
- *page directory*: 페이지 ID → 디스크 파일 위치다. 디스크에 있고, 바뀌면 영속화해야 한다(CMU L6).

### 2. 핀 vs 락

- 핀: "이 프레임을 **다른 페이지로 재활용하지 마라**"다. 핀 수가 0보다 크면 교체 대상이 아니다.
- 락(latch, content lock): 페이지 **내용**을 동시에 읽고 쓰는 순서를 정한다. 공유/배타 모드가 있다.
- 핀은 동시 접근을 막지 않는다. 여러 스레드가 같은 페이지에 동시에 핀을 잡고 공유 락으로 함께 읽을 수 있다.
- PostgreSQL 규칙: 락을 잡으려면 핀이 먼저다. 핀 없이 버퍼를 만지면 그 사이 다른 페이지로 바뀔 수 있다(버퍼 README).

### 3. write-back과 그 안전 근거

- 미루는 이유
  - 같은 페이지를 여러 번 고치면 한 번만 쓰면 된다.
  - 쓰기를 모아 배경 작업(체크포인트, background writer, 페이지 클리너)으로 넘겨 요청 지연에서 뺀다.
- 안전 근거: WAL(19번). 커밋 때는 **로그**만 디스크에 확실히 있으면 된다. 장애 뒤 로그로 페이지를 다시 만든다.
- 순서: WAL로 기록된 변경을 담은 dirty 페이지를 디스크에 쓰기 **전에** 그 페이지를 고친 로그 레코드가 먼저 디스크에 있어야 한다(PG unlogged 테이블은 WAL이 없어 해당 없음). PostgreSQL 버퍼 README도 "링 버퍼가 dirty이고 LSN이 갱신됐으면 보통은 재사용 전에 WAL을 쓰고 flush해야 한다"고 적는다(그래서 순차 스캔 링은 그 버퍼를 flush하지 않고 링에서 빼 버리고, VACUUM 링은 필요하면 WAL을 flush한다).

### 4. CLOCK과 clock sweep

```text
  프레임을 원형으로 놓고 바늘이 돈다
  참조 비트 1 → 0으로 내리고 다음 칸
  참조 비트 0 → 희생자
```

- PostgreSQL이 더한 것
  - 참조 비트 대신 **usage_count**(0..5, `BM_MAX_USAGE_COUNT = 5`). 백엔드가 그 버퍼에 처음 핀을 잡을 때 1씩 오른다(이미 핀을 가진 백엔드의 재핀은 안 올림, 링 전략으로 읽을 때는 0일 때만 1로).
  - 바늘이 지나갈 때 1씩 내린다. 0이고 핀이 없으면 희생자다. 자주 쓰인 버퍼는 여러 바퀴를 버틴다. 빈도를 조금 반영한 셈이다.
  - free list를 먼저 본다. 바늘 위치는 `buffer_strategy_lock`으로 지킨다.
  - 큰 스캔·VACUUM·대량 쓰기는 **링 버퍼**를 쓴다.

### 5. 두 테이블 스캔 뒤 남는 페이지

- 조건: 테이블 블록 수 > `NBuffers / 4`이면 순차 스캔이 `BAS_BULKREAD` 링(256KB)을 쓴다(`heapam.c` `initscan`, `freelist.c`). 임시 테이블은 제외되고, 링 크기는 `shared_buffers/8`이 상한이다(128MB면 16MB라 256KB 그대로).
- 128MB = 16384 버퍼, 1/4 = 4096.
- 6667페이지 테이블: 4096보다 크다 → 링 사용 → 스캔 뒤 **약 32개**(256KB / 8KB)만 남는다. 로컬 재현(예시, PostgreSQL 17.11)에서 32개였다.
- 443페이지 테이블: 4096보다 작다 → 일반 clock sweep → **443개 전부** 남는다. 두 번째 스캔은 `shared hit=443`.
- 결과: 큰 테이블 풀 스캔이 버퍼 풀 전체를 밀어내지 않는다.

### 6. InnoDB 중간점 삽입

- 처음 읽힌 페이지: 리스트의 **중간점 = old 하위 리스트의 머리**에 들어간다. old는 풀의 3/8(`innodb_old_blocks_pct` 37)이다.
- 0.5초 뒤 재접근: 첫 접근 후 `innodb_old_blocks_time`(1000ms) 안이다 → **승격되지 않는다**. old에 머문다.
- 3초 뒤 재접근: 1초를 넘었다 → new(young) 하위 리스트의 머리로 **승격된다**.
- 의도: 스캔은 한 페이지를 짧은 시간에 몰아서 읽고 떠난다. 그런 페이지가 young을 차지하지 못하게 한다(MySQL 8.4 17.8.3.3).
- 경계: 이미 풀에 있던 페이지를 1초 뒤 다시 스캔하면 그 스캔이 young으로 올린다. 로컬 재현에서 `PAGES_MADE_YOUNG`이 +3735.

### 7. 25% vs 80%

- PostgreSQL은 테이블 파일을 보통의 read/write로 읽는다. 커널 **페이지 캐시에도 같은 페이지가** 들어간다. `shared_buffers`를 너무 키우면 같은 데이터를 두 번 담는 셈이고 OS 캐시 몫이 준다. 문서도 "OS 캐시에 기대므로 40% 넘게는 더 낫기 어렵다"고 적는다(19.4.1).
- InnoDB는 유닉스 기본 `innodb_flush_method = O_DIRECT`(지원 시, 아니면 `fsync`)로 OS 캐시를 비켜 간다. 버퍼 풀이 사실상 **유일한 캐시**라서 가능한 한 크게 잡는다(17.5.1 "up to 80%").
- 둘 다 연결별 메모리·OS 몫은 남겨야 한다.

### 8. 버퍼 풀 오염 진단과 대책

- 확인할 지표
  - MySQL: `SHOW ENGINE INNODB STATUS`의 `Buffer pool hit rate`, `Pages made young`·`not young` 증가량, 디스크 읽기 IOPS. 배치 시간대와 겹치는지 본다.
  - PostgreSQL: `pg_stat_database.blks_read` 증가, 느린 쿼리의 `EXPLAIN (ANALYZE, BUFFERS)`에서 `read=` 증가, `pg_buffercache`로 어떤 테이블이 풀을 차지하는지.
- 원인: 한 번 쓰고 버릴 페이지가 자주 쓰던 페이지를 밀어냈다.
- 대책
  - 공통: 배치를 복제본으로 보낸다. keyset으로 잘라 읽는다. 버퍼 풀 크기를 늘린다.
  - MySQL: 배치 시간대에 `innodb_old_blocks_time`을 늘린다(문서가 제안하는 방법, 전역 변수).
  - PostgreSQL: 큰 테이블 순차 스캔은 이미 링에 갇힌다. 문제는 `shared_buffers`의 1/4 이하 크기 테이블 스캔 여러 개나 대량 인덱스 스캔이다. 그런 쿼리를 줄이거나 복제본으로 옮긴다.

### 9. exit code 137

- 137 = 128 + 9(SIGKILL). 137 자체는 "SIGKILL로 죽었다"까지만 말한다(수동 `docker kill`도 같다).
- 버퍼 풀을 키운 직후 반복된다면 컨테이너 메모리 한도를 넘어 OOM killer가 죽였을 가능성이 가장 크다. `docker inspect`의 `State.OOMKilled`나 커널 로그 `Out of memory: Killed process`로 확정한다([os/13](../../os/13-oom-and-memory-limits/2-summary.md)).
- 원인: 버퍼 풀 + 연결별 메모리(PG `work_mem`은 정렬·해시 노드마다, MySQL 세션 버퍼) + 운영체제 몫이 한도를 넘었다. 호스트 RAM 기준 비율을 컨테이너에 그대로 쓴 경우가 흔하다.
- 크기 정하기
  - 한도는 컨테이너 한도 기준으로 계산한다.
  - PostgreSQL: 25%에서 시작한다. OS 캐시가 나머지를 쓴다.
  - InnoDB: 크게 잡되 연결 수 × 세션 메모리와 OS 몫을 빼고 잡는다.
  - 바꾼 뒤 재시작 직후와 부하 최고점의 RSS를 확인한다.
