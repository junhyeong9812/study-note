# database/54-query-execution-models — 정답

## 정답

### 1. 반복자 모델과 LIMIT

```text
  클라이언트 → Limit.next()
                 → Filter.next()
                     → SeqScan.next() → 행 1 (amount≠7) → Filter가 버리고 다시 next()
                     → SeqScan.next() → 행 2 ...
                     → ... amount=7인 행 → Filter가 위로 반환
                 ← 행 반환 (Limit 카운트 1)
  ... 3행을 받으면 Limit은 더 이상 next()를 부르지 않는다 → 스캔 종료
```

- 로컬 재현(PostgreSQL 17.11, 50만 행): 스캔은 **2,007행**만 읽고 멈췄다. `Seq Scan (actual rows=3)` + `Rows Removed by Filter: 2004` → 3 + 2,004 = 2,007.
- MySQL 8.4.10에서도 `Table scan on ev (actual … rows=2007)`로 같은 모양이 보였다.

### 2. 파이프라인 차단 연산자

- 정의: 자식이 모든 행을 내기 전에는 첫 출력 행을 낼 수 없는 연산자(CMU L13).
- 예: `Sort`(ORDER BY), 해시 조인의 build 쪽(`Hash`), 집계(해시 집계·전체 집계), 일부 서브쿼리.
- `ORDER BY note LIMIT 10`: Sort가 입력 전체를 받아야 "가장 작은 10개"를 알 수 있다. LIMIT은 Sort 위에 있으므로 Sort 아래 스캔을 멈추게 할 수 없다. 대신 Top-N 힙으로 메모리만 작다(41번).
- `note` 인덱스가 있으면 `Limit → Index Scan`이 되어 인덱스 순서대로 10행만 읽고 멈출 수 있다. 차단 연산자가 사라지기 때문이다.

### 3. 세 모델 비교

| | 반복자 | 구체화 | 벡터화 |
|---|---|---|---|
| 한 번에 넘기는 것 | 행 1개 | 행 전부 | 행 묶음 |
| 호출 수 | 행 수 × 연산자 수 | 연산자당 한 번 | 행 수 / 묶음 크기 |
| 맞는 부하 | 범용(거의 모든 행 기반 DB) | 조금 읽는 OLTP | 대량 스캔 OLAP |

- SIMD가 쉬운 이유: 묶음 안에서는 같은 연산을 같은 타입의 값 배열에 반복하는 촘촘한 루프가 된다. 명령 하나로 여러 값을 처리하는 SIMD에 그대로 맞는다. 행 하나씩이면 값마다 호출·분기가 끼어 이런 루프가 안 나온다.

### 4. 캐시에 있는데도 CPU 병목

- 반복자 모델은 행마다 연산자 수만큼 `next()` 호출, 분기, 식 해석을 한다. I/O가 없으면 이 행 단위 오버헤드가 시간 전부다.
- 같은 DB 안의 대응
  - 병렬 실행: 작업자를 늘려 코어 여러 개를 쓴다. 병렬이 안 나오는 이유(15.2)를 확인한다.
  - 표현식 JIT: 분석 쿼리에서 이득을 측정해 켠다.
  - 미리 집계한 테이블, 필요한 컬럼만 읽기.
- 모델 자체를 바꾸는 대응: 벡터화 실행 + 컬럼 저장 엔진으로 분석 부하를 옮긴다.

### 5. 병렬 계획 읽기

- `loops=3`: 작업자 2개 + **리더** 1개가 병렬 부분을 함께 실행했다(리더 참여는 기본 on).
- `actual rows=19144`는 loops 평균이다. 총 ≈ 19,144 × 3 ≈ 57,432행(병렬 끔 실행의 `rows=57432`와 같다).
- 두 단계인 이유: 작업자마다 자기 조각의 부분 결과(개수·합)를 `Partial Aggregate`로 만들고, 리더가 `Gather`로 모은 3개를 `Finalize Aggregate`에서 합친다. 행 57,432개를 리더로 보내는 대신 3행만 보낸다.
- 로컬 재현: 36.0 ms. 병렬을 끄면(`max_parallel_workers_per_gather = 0`) 68.8 ms.

### 6. 가끔만 빠른 병렬 쿼리

- 볼 것: `Workers Planned: 2` 대 `Workers Launched: 0`(또는 1).
- 원인: 다른 병렬 쿼리들이 작업자를 다 써서 못 얻었다(바쁠 때만 그렇다는 점이 근거. fetch count를 실은 `Execute`도 같은 수치를 내므로 늘 0이면 8번을 본다). 리더 혼자 병렬용 계획을 돌면 성능이 나쁠 수 있다(15.1).
- 설정(PostgreSQL 17 기본값)
  - `max_parallel_workers_per_gather` = 2
  - `max_parallel_workers` = 8
  - `max_worker_processes` = 8(서버 시작 때만 변경)
- 대처: 두 상한을 올리거나 쿼리당 요구(`max_parallel_workers_per_gather`)를 낮춘다. 작업자 하나가 세션 하나만큼 무겁다는 점을 감안한다.

### 7. JIT 문턱을 낮추면

- **빨라지지 않았다.** 로컬 재현: 기본(추정 9,307 < 100,000 → JIT 없음) 29.8 ms → `jit_above_cost = 10` 58.3 ms. JIT Timing Total 14.7 ms.
- 이유: 쿼리가 짧아서 LLVM 컴파일 비용을 회수하지 못했다. JIT는 실제 시간이 아니라 **추정 비용**으로 켜진다.
- OLTP 역할: `ALTER ROLE app_oltp SET jit = off`. 분석 역할만 켜고 `EXPLAIN ANALYZE`의 JIT Timing으로 이득을 확인한다.

### 8. psql에서만 병렬

- 원인 후보(15.2)
  1. 클라이언트가 **0이 아닌 fetch count**로 `Execute` 메시지를 보냈다. 이때는 실행 시점에 병렬로 돌 수 없다. libpq는 이런 메시지를 못 보내므로 psql로는 재현되지 않는다. pgJDBC는 fetch size > 0 + 자동 커밋 끔(트랜잭션 안) + `TYPE_FORWARD_ONLY` + 한 문장 쿼리(holdable 아님)이면 `Execute`에 fetch size만큼의 행 수(`setMaxRows()`가 더 작으면 그 값)를 실어 보낸다. 커서가 아니어도 확장 프로토콜에서 `setMaxRows()`를 걸면 그 행 수가 실린다(pgJDBC 문서·`QueryExecutorImpl.calculateRowsToFetch`).
  2. 커서(`DECLARE CURSOR`)로 읽는다 → 병렬 계획 자체를 만들지 않는다.
  3. `PARALLEL UNSAFE` 함수(사용자 정의 함수의 기본값)가 들어 있다 → 병렬 계획 제외.
- 대처: 문서 권고대로 fetch count를 쓰는 세션은 `max_parallel_workers_per_gather = 0`으로 두어 병렬을 가정한 계획을 혼자 도는 일을 피한다. 또는 대량 조회를 한 번에 받는다. 함수는 정말 안전할 때만 `PARALLEL SAFE`로 표시한다.

### 9. 병렬의 종류

- CMU L14 쿼리 안 병렬
  - 연산자 내부(수평): 같은 연산자를 데이터 조각마다 여러 작업자가 실행.
  - 연산자 사이(수직): 다른 연산자를 다른 작업자가 파이프라인으로 동시에.
  - bushy: 둘의 혼합.
- 교환 연산자: Gather(여럿→하나), Distribute(하나→여럿), Repartition(여럿→여럿).
- PostgreSQL 17: 주로 연산자 내부 병렬(예외: `Parallel Append`는 다른 자식 계획들을 작업자에 나눠 동시에 돌린다, 15.3.4). `Gather`·`Gather Merge`가 교환 연산자이고, 작업자는 백그라운드 프로세스다(15장).
- MySQL 8.4 InnoDB: 문서로 확인한 것은 `innodb_parallel_read_threads`의 병렬 클러스터드 인덱스 읽기다(`CHECK TABLE` 예, 보조 인덱스 스캔 비적용). 일반 조인·집계의 병렬 실행은 이번에 문서로 확인하지 못했다.
