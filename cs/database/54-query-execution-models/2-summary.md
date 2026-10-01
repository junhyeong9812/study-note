# database/54-query-execution-models — 반복자(Volcano)·벡터화·병렬 실행 — 정리 (힌트)

## 해결하는 문제

옵티마이저(12번)가 계획 트리를 골랐다. 이제 누군가 그 트리를 **실제로 돌려야** 한다.\
그 방식을 *처리 모델(processing model)*이라 한다(CMU 15-445 L13). 처리 모델은 두 가지를 정한다.

- *제어 흐름*: 누가 누구를 부르나(위에서 당기나, 아래에서 미나).
- *데이터 흐름*: 연산자 사이에 무엇을 넘기나(행 하나, 행 전부, 행 묶음).

이 선택이 성능의 모양을 바꾼다.

- 행 하나씩 넘기면 `LIMIT 10`에서 10행만 만들고 멈출 수 있다. 대신 행마다 함수 호출이 여러 번 든다.
- 묶음으로 넘기면 호출 수가 줄고 CPU가 한 번에 여러 값을 처리한다. 대신 한 행만 필요할 때 낭비가 생긴다.
- 한 쿼리를 여러 코어로 나누면 빨라지지만, 그만큼 서버 자원을 더 쓴다.

쉬운 예: 공장 조립 라인이다.

```text
  반복자 모델    : 다음 공정이 "하나 줘" 하면 앞 공정이 부품 하나를 만들어 건넨다
  구체화 모델    : 앞 공정이 부품을 전부 만들어 상자째 넘긴다
  벡터화 모델    : 앞 공정이 부품을 한 판(예: 1,000개)씩 넘긴다
  병렬 실행      : 같은 공정을 라인 여러 개가 나눠 하고, 끝에서 한데 모은다
```

똑같은 구조다.\
실무 예: 1억 행 집계 쿼리가 코어 하나를 100% 쓰며 몇십 초 걸린다. 디스크는 한가하다. 병목이 I/O가 아니라 **행마다 드는 CPU 비용**이다. 이때 선택지는 병렬 실행, 표현식 JIT, 또는 벡터화 실행을 하는 컬럼 저장 엔진이다.

## 동작·원리

### 1. 반복자(Volcano) 모델 — 위에서 "다음!"을 부른다

```text
  SELECT * FROM ev WHERE amount = 7 LIMIT 3

        Limit(3)            next() ──┐                 ▲ 행 하나
          │                          ▼                 │
        Filter(amount=7)    next() ──┐   조건 안 맞으면  │
          │                          ▼   계속 다시 부름   │
        SeqScan(ev)         한 행 읽어 반환 ─────────────┘

  Limit은 3행을 받으면 더 부르지 않는다 → 스캔이 멈춘다
```

- *반복자 모델*: 모든 연산자가 `next()`를 구현한다. 부르면 행 하나 또는 "끝"을 돌려준다. 부모의 `next()`가 자식의 `next()`를 부르는 식으로 잎까지 내려간다(CMU L13).
- CMU L13은 이 방식이 거의 모든 행 기반 DB가 쓰는 가장 흔한 모델이라고 쓴다. PostgreSQL 문서는 실행기를 "요구 기반 당김(demand-pull) 파이프라인"이라 부른다. 노드는 불릴 때마다 한 행을 더 내거나 끝났다고 알린다(50.6).
- PostgreSQL 소스에서는 `ExecProcNode()`가 루트 노드를 반복해서 부르고, 노드별 함수(`ExecNestLoop`, `ExecSeqScan` …)가 자식의 `ExecProcNode()`를 부른다(`execProcnode.c` 머리 주석).
- MySQL 8.4의 `EXPLAIN ANALYZE`도 "반복자(iterator)" 단위로 실제 행 수를 보여 준다(15.8.2).

로컬 재현 — `LIMIT`이 스캔을 멈춘다:

```text
  (예시, PostgreSQL 17.11) ev 50만 행
  Limit  (actual rows=3 loops=1)
    ->  Seq Scan on ev  (cost=0.00..10923.00 rows=498) (actual rows=3 loops=1)
          Filter: (amount = 7)
          Rows Removed by Filter: 2004          ← 50만 행 중 2,007행만 읽고 멈춤

  (예시, MySQL 8.4.10) ev 20만 행
  -> Limit: 3 row(s)  (actual ... rows=3 loops=1)
      -> Filter: (ev.amount = 7)  (actual ... rows=3 loops=1)
          -> Table scan on ev  (actual ... rows=2007 loops=1)
```

### 2. 파이프라인과 파이프라인 차단 연산자

```text
  파이프라인:  Scan → Filter → Project → (부모)     행이 중간 저장 없이 흘러간다
  차단 연산자: Sort, Hash(해시 조인의 build 쪽), 해시 집계·전체 집계, 서브쿼리 일부
               (정렬된 입력을 받는 GroupAggregate는 키가 바뀔 때마다 그룹을 내므로 전부 막지는 않는다)
               → 자식의 행을 전부 받아야 첫 행을 낼 수 있다

  SELECT * FROM ev ORDER BY note LIMIT 10
    Limit → Sort → SeqScan      Sort가 50만 행을 다 받아야 첫 행이 나온다
                                (다만 Top-N 힙으로 메모리는 작다 → 41번)
```

- *파이프라인*: 연산자들이 중간 저장 없이 행을 계속 넘기는 구간이다(CMU L13).
- *파이프라인 차단 연산자(pipeline breaker)*: 자식이 모든 행을 내기 전에는 끝낼 수 없는 연산자다. 예: 조인의 build 쪽, 서브쿼리, `ORDER BY`(CMU L13).
- 그래서 `LIMIT 10`이 항상 빠른 것은 아니다. 위에 차단 연산자가 있으면 입력 전체를 읽는다.
- `EXPLAIN ANALYZE`의 `actual time=A..B`에서 A(첫 행까지 시간)가 크면 그 아래에 차단 연산자가 있다는 신호다.

### 3. 구체화 모델과 벡터화 모델

```text
  반복자         next() → 행 1개          호출 수 = 행 수 × 연산자 수
  구체화         output() → 행 전부        호출 수 적음, 중간 결과가 크면 메모리·스필
  벡터화         next() → 행 묶음(벡터)     호출 수 = 행 수/묶음 크기, 묶음 안은 촘촘한 루프
```

- *구체화 모델*: 연산자가 입력을 한 번에 다 처리하고 결과를 통째로 넘긴다. 한 번에 조금만 읽는 OLTP에 맞고, 중간 결과가 큰 OLAP에는 맞지 않는다(CMU L13).
- *벡터화 모델*: 반복자처럼 `next()`를 쓰지만 행 묶음을 넘긴다. 호출 수가 줄고, 묶음 안 루프에 SIMD 명령을 쓰기 쉽다. 많은 행을 훑는 OLAP에 맞다(CMU L13).
  - *SIMD*: 명령 하나로 여러 값을 한꺼번에 계산하는 CPU 기능이다.
- 행 단위 반복의 비용은 "행마다 함수 호출 몇 번 + 분기 + 표현식 해석"이다. 행이 수억 개면 이것이 CPU 시간의 큰 몫이 된다. 컬럼 저장 분석 엔진이 벡터화를 택하는 배경이다([systems/clickhouse-mergetree](../../systems/clickhouse-mergetree/2-summary.md)).
- 방향: 위에서 당기는(pull) 방식은 `LIMIT` 제어가 쉽다. 아래에서 미는(push) 방식은 파이프라인 안에서 캐시·레지스터를 더 잘 쓸 수 있다(CMU L13).

### 4. 표현식 JIT — 반복자 모델 안에서 행 비용 줄이기 (PostgreSQL)

- PostgreSQL은 LLVM으로 식 평가와 튜플 해체(deforming)를 기계어로 컴파일할 수 있다(30장). `jit` 기본값 `on`, `jit_above_cost` 기본 100000이다(19.7).
- 컴파일 자체에 시간이 든다. 계획의 **추정 비용**이 문턱을 넘으면 켜진다. 실제 실행 시간으로 정하지 않는다.

```text
  로컬 재현 (예시, PostgreSQL 17.11): SELECT count(*), sum(amount) FROM ev WHERE amount > 10
  기본 (추정 비용 9307 < 100000 → JIT 안 함)   Execution Time: 29.8 ms
  SET jit_above_cost = 10                    JIT: ... Total 14.677 ms
                                             Execution Time: 58.3 ms   ← 오히려 2배
```

### 5. 병렬 실행 — 한 쿼리를 여러 작업자로

```text
  쿼리 안 병렬의 세 종류 (CMU L14)
  ┌──────────────────────────────────────────────────────────────┐
  │ 연산자 내부(수평)  같은 연산자를 데이터 조각마다 여러 작업자가 실행   │
  │                  → 교환(exchange) 연산자가 모은다                │
  │ 연산자 사이(수직)  연산자 A와 B를 다른 작업자가 동시에(파이프라인)     │
  │ bushy            위 둘의 혼합                                   │
  └──────────────────────────────────────────────────────────────┘
  교환 연산자: Gather(여럿→하나), Distribute(하나→여럿), Repartition(여럿→여럿)
```

PostgreSQL 17은 주로 연산자 내부 병렬을 쓴다. 교환 연산자가 `Gather`·`Gather Merge`다.\
예외로 `Parallel Append`는 서로 다른 자식 계획(예: 파티션별 스캔)에 작업자를 흩어 동시에 돌린다(15.3.4).

```text
  (예시, PostgreSQL 17.11) SELECT count(*), sum(amount) FROM ev WHERE note LIKE '%ab%'

  Finalize Aggregate (actual rows=1 loops=1)          ← 리더: 부분 결과 3개를 합침
    ->  Gather (actual rows=3 loops=1)                ← 교환 연산자
          Workers Planned: 2
          Workers Launched: 2
          ->  Partial Aggregate (actual rows=1 loops=3)       ← 작업자 2 + 리더 1
                ->  Parallel Seq Scan on ev (actual rows=19144 loops=3)
                                             ↑ loops=3의 평균. 총 약 57,432행
  Execution Time: 36.0 ms       (max_parallel_workers_per_gather = 0 이면 68.8 ms)
```

- 작업자는 **별도 프로세스**다. 문서는 작업자 하나가 사용자 세션 하나를 더 띄운 것과 비슷한 부담이라고 쓴다(19.4 `max_parallel_workers_per_gather`).
- 리더 프로세스도 병렬 부분을 함께 실행한다(기본값 `parallel_leader_participation = on`일 때. off면 리더는 모으기만 한다). 단 작업자들이 낸 행을 모두 읽어야 하므로, 병렬 부분이 행을 많이 내면 리더는 모으는 일에 바빠진다(15.1).
- `Gather`는 순서를 섞는다. 각 작업자가 정렬된 행을 내면 `Gather Merge`가 순서를 지키며 병합한다(15.1).
- 집계는 두 단계다. 작업자마다 `Partial Aggregate`, 리더가 `Finalize Aggregate`.

| PostgreSQL 17 설정 | 기본값 | 뜻 |
|---|---|---|
| `max_parallel_workers_per_gather` | 2 | Gather 하나가 쓸 최대 작업자. 0이면 병렬 끔 |
| `max_parallel_workers` | 8 | 클러스터 전체의 병렬 작업자 상한 |
| `max_worker_processes` | 8 | 백그라운드 프로세스 전체 상한(서버 시작 때만 변경) |
| `min_parallel_table_scan_size` | 8MB | 이보다 작은 테이블은 병렬 스캔을 고려하지 않음(테이블에 `parallel_workers`를 직접 지정하면 이 기준을 건너뜀) |
| `parallel_setup_cost` / `parallel_tuple_cost` | 1000 / 0.1 | 작업자 띄우기·행 전달의 추정 비용 |

**병렬 계획이 안 나오거나, 나와도 병렬로 안 도는 경우** (15.2)

```text
  계획 단계에서 제외                               실행 단계에서 혼자 실행 (작업자를 못 얻음)
  - 데이터를 쓰거나 행을 잠그는 쿼리                  - max_worker_processes 한도에 닿음
    (예외: CREATE TABLE AS, SELECT INTO,            - max_parallel_workers 한도에 닿음
     CREATE/REFRESH MATERIALIZED VIEW)             - 클라이언트가 0이 아닌 fetch count로
  - 커서(DECLARE CURSOR), PL/pgSQL FOR 루프            Execute 메시지를 보냄
  - PARALLEL UNSAFE 함수 사용
    (사용자 정의 함수는 기본이 UNSAFE)
  - 이미 병렬인 쿼리 안에서 부른 쿼리
```

MySQL 8.4 InnoDB:

- 문서에서 확인한 쿼리 내부 병렬은 *병렬 클러스터드 인덱스 읽기*다. `innodb_parallel_read_threads`(기본: 논리 프로세서 수 / 8, 최소 4)로 정한다. 문서는 `CHECK TABLE`의 두 번째 클러스터드 인덱스 읽기를 예로 들고, 보조 인덱스 스캔에는 적용되지 않는다고 적는다(17.14).
- 일반 `SELECT`의 조인·집계를 여러 스레드로 나누는 기능은 이번에 문서로 확인하지 못했다 [?].

### 6. 프로세스 모델 — 작업자는 무엇인가

- CMU L14는 DB의 작업자 모델을 *작업자마다 프로세스*와 *작업자마다 스레드*로 나누고, 셋째로 임베디드 방식을 든다.
- PostgreSQL은 병렬 작업자가 프로세스다(15.1 "background worker processes"). 연결마다 백엔드 프로세스를 두는 구조다.
- MySQL 8.4는 기본으로 연결 하나를 스레드 하나로 처리한다(`thread_handling` 기본 `one-thread-per-connection`). 스레드 풀 플러그인을 쓰면 `loaded-dynamically`로 바뀐다(7.1.8).
- OS 쪽 배경: [os/36-server-concurrency-architectures](../../os/36-server-concurrency-architectures/2-summary.md), [os/07-threads-and-context-switch](../../os/07-threads-and-context-switch/2-summary.md).

## 쓰이는 자료구조·알고리즘

- **반복자 트리** — 계획 트리의 노드마다 초기화·다음 행·종료 함수를 가진다. 트리를 재귀로 당겨 실행한다(`execProcnode.c`의 `ExecInitNode`·`ExecProcNode`·`ExecEndNode`). 행 대신 묶음을 넘기면 벡터화 모델이 된다.
- **교환 연산자** — 작업자가 만든 행을 리더에게 넘기는 통로다. Gather는 여러 입력을 하나로 합친다(CMU L14).
- **부분 집계 + 최종 집계** — `SUM`·`COUNT`처럼 쪼개 계산해 합칠 수 있는 집계를 조각별로 계산한 뒤 합친다. `AVG`는 (합, 개수)로 들고 다닌다(CMU L11).
- **k-way 병합** — `Gather Merge`는 정렬된 작업자 출력들을 순서를 지켜 합친다(41번의 병합과 같은 구조). [data-structure/07-heap](../../data-structure/07-heap/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 계획에서 실행 모델의 흔적을 읽는다

```sql
EXPLAIN (ANALYZE, VERBOSE, BUFFERS) SELECT count(*), sum(amount) FROM ev WHERE note LIKE '%ab%';
```

- `loops=3`, `Worker 0: actual …` → 병렬 작업자별 실적. `actual rows`는 loops 평균이다.
- `Workers Planned: 2` vs `Workers Launched: 0` → 계획은 병렬인데 혼자 돌았다. 작업자를 못 얻었거나, 클라이언트가 fetch count를 실은 `Execute`를 보냈다(장애 시나리오 4).
- `actual time=첫행..끝`의 첫 행 시간이 큰 노드 → 그 아래에 차단 연산자.
- `JIT:` 절 → JIT를 썼다. `Timing: … Total`이 실행 시간에서 차지하는 비율을 본다.

### 2. 병렬이 도는지 확인하고 조절한다

```sql
SHOW max_parallel_workers_per_gather;                   -- 2
SET max_parallel_workers_per_gather = 4;                -- 이 세션만
ALTER TABLE ev SET (parallel_workers = 4);              -- 테이블 단위 작업자 수
ALTER FUNCTION my_fn(int) PARALLEL SAFE;                -- 정말 안전할 때만
SELECT pid, leader_pid, backend_type, query
FROM pg_stat_activity WHERE backend_type = 'parallel worker';
```

- `PARALLEL SAFE`는 정말로 안전할 때만 붙인다. 문서는 실제로는 restricted·unsafe인 함수를 safe로 표시하면 병렬 쿼리에서 오류를 내거나 틀린 답을 낼 수 있다고 한다(15.4).
- OLTP 커넥션에는 병렬을 끄는 것도 방법이다. 짧은 쿼리는 작업자를 띄우는 비용이 더 클 수 있다.

### 3. JIT는 OLTP에서 끄거나 문턱을 올린다

```sql
SET jit = off;                                   -- 세션 단위
ALTER ROLE app_oltp SET jit = off;               -- 역할 단위
-- 분석 역할은 켜 두고 EXPLAIN ANALYZE의 JIT Timing으로 이득을 확인
```

### 4. 행 단위 CPU가 한계면 모델을 바꾼다

- 같은 DB 안에서: 병렬 실행, 미리 집계한 테이블, 필요한 컬럼만 읽기.
- 그래도 대량 스캔·집계가 주 업무면: 벡터화 실행 + 컬럼 저장 엔진으로 분석 부하를 옮긴다. database 37번(행 vs 컬럼 저장)과 45번.

## 장애 시나리오와 대처

### 1. 큰 집계가 코어 하나만 쓰며 느리다 (⚠ 행 단위 반복의 CPU 오버헤드)

- **현상**: 수억 행 집계가 수십 초. 디스크는 한가하고 CPU 코어 하나만 100%.
- **보이는 형태**: `top`에서 백엔드 프로세스 하나가 100%. `EXPLAIN (ANALYZE, BUFFERS)`에서 대부분 `shared hit`(캐시에서 읽음)인데 스캔·집계 노드 시간이 길다. 계획에 `Gather`가 없다.
- **원인**: 반복자 모델은 행마다 연산자 수만큼 호출·분기·식 해석을 한다. 데이터가 캐시에 있으면 이 CPU 비용이 전부다. 병렬이 꺼졌거나, 테이블이 `min_parallel_table_scan_size`보다 작다고 추정됐거나, 15.2의 조건으로 제외됐다.
- **대처**
  - 병렬이 안 나오는 이유를 15.2 목록으로 확인한다.
  - 분석 쿼리는 JIT 이득을 측정해 본다(항상 이득은 아니다, 시나리오 3).
  - 반복되는 대시보드 집계는 미리 집계한 테이블로 바꾼다. 부하가 계속 커지면 컬럼 저장·벡터화 엔진으로 분리한다.

### 2. 계획은 병렬인데 가끔만 빠르다 — `Workers Launched: 0`

- **현상**: 같은 쿼리가 한가할 때는 빠르고, 바쁠 때는 두세 배 느리다.
- **보이는 형태**: 느릴 때의 `EXPLAIN ANALYZE`에 `Workers Planned: 2`, `Workers Launched: 0`(또는 1).
- **원인**: 동시에 도는 병렬 쿼리들이 `max_parallel_workers`(8) 또는 `max_worker_processes`(8)를 다 썼다(바쁠 때만 느리다는 점이 이 원인을 가리킨다. 늘 0이면 시나리오 4를 의심). 작업자를 못 얻으면 리더 혼자 병렬용 계획을 돈다. 최적 계획은 작업자 수에 따라 다르므로 이때 성능이 나쁠 수 있다(15.1).
- **대처**: 문서 권고대로 두 상한을 올리거나, `max_parallel_workers_per_gather`를 낮춰 쿼리당 요구를 줄인다. 상한을 올리면 CPU·메모리 사용도 는다.

### 3. JIT 때문에 짧은 쿼리가 느려졌다

- **현상**: 수십 ms이던 쿼리가 두 배 이상으로 늘었다. 데이터가 늘어 비용 추정이 커진 뒤부터다.
- **보이는 형태**: `EXPLAIN ANALYZE` 끝의 `JIT: … Timing: … Total …` 시간이 실행 시간의 큰 부분을 차지한다(로컬 재현: 문턱을 낮추자 29.8 ms → 58.3 ms, JIT Total 14.7 ms).
- **원인**: JIT는 **추정 비용**(`jit_above_cost` 100000)으로 켜진다. 추정이 부풀었거나, 실행 자체가 짧아 컴파일 비용을 회수하지 못했다.
- **대처**: OLTP 역할은 `jit = off`. 분석 역할은 `jit_above_cost`·`jit_inline_above_cost`·`jit_optimize_above_cost`를 측정으로 맞춘다. 추정이 부푼 원인(12번)도 본다.

### 4. psql에서는 병렬인데 애플리케이션에서는 아니다

- **현상**: 같은 SQL이 psql에서는 `Gather`로 빠르고, 애플리케이션에서는 느리다.
- **보이는 형태**: `auto_explain` 로그의 계획에서 작업자가 0이다. 또는 병렬 계획 자체가 없다.
- **원인 후보** (15.2)
  - 클라이언트가 0이 아닌 fetch count로 `Execute` 메시지를 보냈다. 이때는 병렬로 실행할 수 없다. libpq는 이런 메시지를 보낼 방법이 없으므로 psql에서는 재현되지 않는다. pgJDBC 문서 기준으로 fetch size가 0보다 크고, 자동 커밋을 껐고, `TYPE_FORWARD_ONLY`이고, 한 문장 쿼리일 때(그리고 holdable ResultSet이 아닐 때) 커서 기반 ResultSet을 쓴다. 이때 `Execute`에 fetch size만큼의 행 수를 실어 보낸다(`setMaxRows()`가 더 작으면 그 값). 커서를 안 쓰는 확장 프로토콜 경로에서도 `setMaxRows()`를 걸면 `Execute`에 그 행 수가 실린다(단순 쿼리 프로토콜 모드면 `Execute` 자체가 없다)(pgJDBC 문서 "Getting results based on a cursor", 소스 `QueryExecutorImpl.calculateRowsToFetch`).
  - 커서(`DECLARE CURSOR`)로 읽는다.
  - 쿼리에 `PARALLEL UNSAFE`(사용자 정의 함수의 기본값) 함수가 들어 있다.
- **대처**: 문서는 이런 일이 잦으면 해당 세션에서 `max_parallel_workers_per_gather = 0`으로 두어, 병렬을 가정한 계획을 혼자 도는 일을 피하라고 권한다. 함수는 안전할 때만 `PARALLEL SAFE`로 표시한다.

### 5. `LIMIT 10`인데 느리다

- **현상**: 첫 페이지 10건 조회가 테이블이 커질수록 느려진다.
- **보이는 형태**: `Limit → Sort → Seq Scan`. Sort의 첫 행 시간이 거의 전체 시간과 같다. Seq Scan은 전체 행을 읽었다.
- **원인**: `ORDER BY`의 Sort는 파이프라인 차단 연산자다. LIMIT이 있어도 입력을 전부 받아야 첫 행을 낸다. LIMIT의 조기 종료는 파이프라인 안에서만 통한다.
- **대처**: `ORDER BY` 컬럼 순서의 인덱스를 만들어 `Limit → Index Scan`으로 바꾼다. 그러면 인덱스 순서대로 필요한 행만 읽고 멈춘다(09번, 41번).

## 핵심 문장

- 처리 모델은 연산자 사이의 제어 흐름(당김·밂)과 데이터 흐름(행 하나·전부·묶음)을 정한다.
- 반복자(Volcano) 모델은 `next()`로 한 행씩 당긴다. PostgreSQL 실행기도 이 방식이고, `LIMIT`이 스캔을 일찍 멈출 수 있다. 대신 행마다 호출·해석 비용이 든다.
- Sort·해시 build·해시 집계는 파이프라인 차단 연산자다. 그 위의 `LIMIT`은 입력 전체 읽기를 막지 못한다.
- 벡터화 모델은 행 묶음을 넘겨 호출 수를 줄이고 SIMD를 쓰기 쉽게 한다. 대량 스캔 OLAP에 맞다.
- PostgreSQL 병렬 실행은 주로 작업자 프로세스가 같은 연산자를 나눠 하고 `Gather`/`Gather Merge`가 모은다. 작업자를 못 얻으면 리더 혼자 돈다. 쓰기·커서·UNSAFE 함수·fetch count는 병렬을 막는다.
- JIT는 추정 비용 문턱으로 켜진다. 짧은 쿼리에서는 컴파일 비용이 이득보다 클 수 있다.

## 관련 주제·근거

- 선행
  - database `11-join-algorithms` — 조인 연산자(해시 build는 차단 연산자) → [../11-join-algorithms/2-summary.md](../11-join-algorithms/2-summary.md)
  - database `12-query-optimizer-and-explain` — 계획 트리가 만들어지는 과정 → [../12-query-optimizer-and-explain/2-summary.md](../12-query-optimizer-and-explain/2-summary.md)
- 연결
  - database `41-sorting-and-aggregation` — 차단 연산자 Sort·집계와 k-way 병합 → [../41-sorting-and-aggregation/2-summary.md](../41-sorting-and-aggregation/2-summary.md)
  - database `37-row-vs-column-storage` — 벡터화와 짝을 이루는 컬럼 저장 → [../37-row-vs-column-storage/2-summary.md](../37-row-vs-column-storage/2-summary.md)
  - [systems/clickhouse-mergetree](../../systems/clickhouse-mergetree/2-summary.md) — 컬럼 저장 분석 엔진
  - [os/36-server-concurrency-architectures](../../os/36-server-concurrency-architectures/2-summary.md) — 프로세스·스레드 작업자 모델
  - 문법 쪽: [sql/58 EXPLAIN 계획 트리](../../../languages/sql/syntax/58-explain-plan-tree/2-summary.md)
- 교재
  - CMU 15-445/645 Fall 2024 Lecture #13 "Query Processing I" — 파이프라인·차단 연산자, 반복자·구체화·벡터화 모델, pull vs push <https://15445.courses.cs.cmu.edu/fall2024/>
  - CMU 15-445/645 Fall 2024 Lecture #14 "Query Execution II" — 작업자 모델, 연산자 내부·사이·bushy 병렬, 교환 연산자(Gather·Distribute·Repartition)
  - G. Graefe, "Volcano — An Extensible and Parallel Query Evaluation System", 1994 (CMU L13의 "Volcano" 명칭 경유, 원문 미열람)
- PostgreSQL 17 문서·소스
  - 50.6 Executor("demand-pull pipeline") <https://www.postgresql.org/docs/17/executor.html>
  - 15.1 How Parallel Query Works · 15.2 When Can Parallel Query Be Used? · 15.3 Parallel Plans · 15.4 Parallel Safety <https://www.postgresql.org/docs/17/how-parallel-query-works.html>
  - 19.4 Resource Consumption(`max_worker_processes` 8, `max_parallel_workers` 8, `max_parallel_workers_per_gather` 2, `parallel_leader_participation` on) · 19.7 Query Planning(`parallel_setup_cost` 1000, `parallel_tuple_cost` 0.1, `min_parallel_table_scan_size` 8MB, `jit` on, `jit_above_cost` 100000)
  - 30.2 When to JIT? <https://www.postgresql.org/docs/17/jit-decision.html>
  - `src/backend/optimizer/path/allpaths.c` `compute_parallel_worker()`(테이블 `parallel_workers` 지정 시 `min_parallel_table_scan_size` 검사 생략) <https://github.com/postgres/postgres/blob/REL_17_STABLE/src/backend/optimizer/path/allpaths.c>
  - `src/backend/executor/execProcnode.c` 머리 주석 <https://github.com/postgres/postgres/blob/REL_17_STABLE/src/backend/executor/execProcnode.c>
- MySQL 8.4 Reference Manual
  - 15.8.2 EXPLAIN Statement(EXPLAIN ANALYZE는 반복자 기반, TREE 형식) <https://dev.mysql.com/doc/refman/8.4/en/explain.html>
  - 17.14 InnoDB System Variables(`innodb_parallel_read_threads`) <https://dev.mysql.com/doc/refman/8.4/en/innodb-parameters.html>
  - 7.1.8 Server System Variables(`thread_handling` 기본 `one-thread-per-connection`) <https://dev.mysql.com/doc/refman/8.4/en/server-system-variables.html>
- pgJDBC: 문서 "Issuing a Query and Processing the Result"(커서 기반 ResultSet 조건) <https://jdbc.postgresql.org/documentation/query/> · 소스 `pgjdbc/src/main/java/org/postgresql/core/v3/QueryExecutorImpl.java`(`calculateRowsToFetch`, `sendExecute`)·`jdbc/PgStatement.java`(`QUERY_FORWARD_CURSOR` 조건) <https://github.com/pgjdbc/pgjdbc>
- 로컬 재현(PostgreSQL 17.11, MySQL 8.4.10, 전용 DB `w12`): `LIMIT 3`에서 스캔 조기 종료(2,007행만 읽음, 두 제품), 병렬 집계 36.0 ms vs 병렬 끔 68.8 ms와 `Partial/Finalize Aggregate`·`loops=3`, `jit_above_cost=10`에서 29.8 → 58.3 ms
