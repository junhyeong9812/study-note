# reliability/47-server-design-antipatterns — 서버 설계·운영 안티패턴 카탈로그 — 정리 (힌트)

## 해결하는 문제

안티패턴 대부분은 **좋은 의도로 들인 결정**이다. 서비스를 나누고, 캐시를 넣고, 큐를 두고, 이중화를 한다. 그런데 어떤 조합은 이점은 없이 비용만 남긴다.\
카탈로그가 없으면 같은 실수를 팀마다, 해마다 다시 한다.

```text
 좋은 의도                    숨은 조건                       결과
 서비스를 나눴다      +  같은 DB를 직접 읽고 쓴다     →  분산 비용 + 결합 그대로
 큐를 넣었다          +  상한이 없다                  →  지표는 초록인 채로 OOM
 서버 3대로 늘렸다    +  스케줄러가 메모리 안에 있다  →  자정 정산 3번 실행
 백업을 받는다        +  복원해 본 적 없다            →  필요한 날 복원 실패
```

- *안티패턴(antipattern)*: 흔히 쓰이는데, 쓰면 문제를 키우는 것으로 알려진 해법. 증상과 처방이 함께 알려져 있다.
- 이 노트의 범위는 **구조·운영** 수준이다. 코드 수준 성능·안정성 안티패턴(Chatty I/O, N+1, 요청마다 클라이언트 생성 등)은 48이다.

쉬운 예: 집에 화재 경보기를 달았는데 배터리를 뺀 채로 둔다.
- 설치했다는 안도감 때문에 오히려 위험을 모른다.

똑같은 구조다.\
실무 예: 원본 [systems/server-design/11-antipatterns.md](../../systems/server-design/11-antipatterns.md)의 29개 항목(구조 4·확장 5·복원력 7·상태 5·운영 8). 이 노트는 항목을 길게 되풀이하지 않고, **왜 생기나(숨은 결합)**, **운영에서 어떻게 알아채나(탐지 신호)**, **실험으로 하나를 직접 확인**한다.

## 동작·원리

### 1. 공통 모양 — 국소 결정이 숨은 결합을 만든다

```text
             ┌──────────── 숨은 결합의 종류 ────────────┐
 국소 결정 ──▶│ 공유 상태  : 같은 DB·같은 메모리·같은 세션   │──▶ 한 곳의 문제가 전체로
             │ 시간 결합  : 동기 호출 체인, 타임아웃 없음   │──▶ 느림이 위로 번진다
             │ 용량 결합  : N대가 서로의 몫을 대신 진다     │──▶ 하나가 죽으면 같이 죽는다
             │ 검증 안 된 가정·운영 습관: 백업·페일오버·경보 │──▶ 필요한 날 안 된다
             └─────────────────────────────────────────┘
```

원본 29개를 이 네 결합으로 묶으면 이렇다(번호 = 원본 항목 번호).

| 숨은 결합 | 원본 항목 | 운영에서 보이는 신호 |
|---|---|---|
| 공유 상태 | 1 분산 모놀리스, 3 공유 DB, 17 인메모리 스케줄러, 18 로컬 락, 19 스티키 세션, 20 Redis를 진실의 원천으로, 21 분산 락을 정확성 보장으로 | 동시 배포 필요, 한 서비스 쿼리로 다른 서비스 지연, 같은 작업 실행 기록 N건, 인스턴스 재시작 때 세션 유실 |
| 시간 결합 | 4 동기 호출 체인, 10 타임아웃 없음, 11 무제한·중복 재시도, 12 4xx 재시도, 13 타임아웃×재시도 곱 | 하류 p99가 오르면 상류 스레드풀 포화, 장애 때 요청 수 급증(재시도), 클라이언트가 끊은 뒤에도 서버 작업 지속 |
| 용량 결합 | 5 측정 없이 증설, 8 무한 큐·캐시, 9 오토스케일로 덮기, 14 깊은 헬스체크, 15 이중화 + 용량 계획 없음, 16 폴백 없음 | 증설 뒤 DB 커넥션 급증, 큐 길이 단조 증가, 전 인스턴스 동시 unhealthy, 한 대 장애 뒤 나머지 연쇄 다운 |
| 검증 안 된 가정·운영 습관 | 6 캐시로 덮기, 7 조기 샤딩, 2 조기 마이크로서비스, 22 복원 안 해 본 백업, 23 복제를 백업으로, 24 실행 안 해 본 페일오버, 25 롤백 불가 마이그레이션, 26 LB 전파 대기 없는 종료, 27 원인 경보·경보 과다, 28 진단 먼저, 29 비난하는 사후 분석 | 캐시 미스 경로가 p99, 복원 리허설 기록 없음, 페일오버 첫 실행이 사고 날, 배포마다 502 몇 건, 경보 대부분이 무시됨 |

### 2. 숫자로 보는 세 가지

```text
 동기 체인(원본 4)        0.999^5 = 0.995    → 99.9% 서비스 5개 직렬 = 99.5%
 계층별 재시도(원본 11)   3 × 3 × 3 = 27      → 3계층이 각각 3회 시도하면 맨 아래는 최대 27배 요청
 이중화 용량(원본 15)     2대 × 70%           → 1대 장애 시 남은 1대에 140% → 같이 죽는다
                         N대면 평소 사용률 ≤ (N−1)/N  (3대면 약 67%, 4대면 75%)
```

- 체인 가용성의 곱은 독립 고장 가정이다. 같은 DB·같은 네트워크를 공유하면 고장이 함께 오므로 더 나쁠 수도 있다 → [01-fault-error-failure-availability](../01-fault-error-failure-availability/2-summary.md).

### 3. 실험: 인메모리 스케줄러 + 다중 인스턴스 (원본 17) — 그리고 "락이면 될까?"

원본은 "DB 락 / 리더 선출 → 락 잡은 1대만 실행, 나머지 스킵"이라고 그린다. 실험으로 확인했다.

- 인스턴스 3개 = 스레드 3개(각자 JDBC 커넥션). 같은 "자정 정산"을 각자 시계로 실행한다.
- 시각차: 인스턴스 i는 `(i−1) × skew` ms 늦게 자정을 맞는다(시계 어긋남·기동 시각 차이 흉내). 정산은 100ms.
- 세 방식
  - none: 조정 없음.
  - lock: 실행하는 **동안만** `pg_try_advisory_lock(42)`(세션 수준, 기다리지 않음 — PostgreSQL 17 문서). 못 잡으면 건너뛴다. 끝나면 푼다.
  - runkey: `(job, run_date)`를 기본 키로 한 실행 기록을 `INSERT … ON CONFLICT DO NOTHING`. 1행이 들어간 인스턴스만 실행. 기록과 지급은 한 트랜잭션.

```java
default -> {                                              // runkey
    c.setAutoCommit(false);
    try (PreparedStatement p = c.prepareStatement(
            "INSERT INTO job_run VALUES ('settle', DATE '2026-10-01', ?) ON CONFLICT DO NOTHING")) {
        p.setInt(1, me);
        if (p.executeUpdate() == 0) { c.rollback(); yield false; }   // 이번 회차는 이미 누가 했다
    }
    settle(c, me);
    c.commit();                                           // 실행권 기록과 지급이 한 트랜잭션
    yield true;
}
```

(실험, PostgreSQL 17.11 일회용 컨테이너 + JDK 21.0.12 temurin 컨테이너 `--cpus=2`, PostgreSQL JDBC 42.7.4, 2026-10-01 — 3회 중 1회)

```text
none   시각차   0ms → 지급 행 3개  [인스턴스1 실행, 인스턴스2 실행, 인스턴스3 실행]
none   시각차 150ms → 지급 행 3개  [인스턴스1 실행, 인스턴스2 실행, 인스턴스3 실행]
lock   시각차   0ms → 지급 행 1개  [인스턴스1 실행, 인스턴스2 건너뜀, 인스턴스3 건너뜀]
lock   시각차 150ms → 지급 행 3개  [인스턴스1 실행, 인스턴스2 실행, 인스턴스3 실행]
runkey 시각차   0ms → 지급 행 1개  [인스턴스1 건너뜀, 인스턴스2 실행, 인스턴스3 건너뜀]
runkey 시각차 150ms → 지급 행 1개  [인스턴스1 실행, 인스턴스2 건너뜀, 인스턴스3 건너뜀]
```

- 관찰 1 — none: 시각차와 무관하게 3번 지급. 원본 그림 그대로다.
- 관찰 2 — lock: 세 인스턴스가 **동시에** 깨면 1번. 그런데 150ms씩 어긋나면 3번이다. 앞 인스턴스가 100ms 만에 끝내고 락을 푼 뒤, 다음 인스턴스가 빈 락을 잡는다. 락은 "동시에 둘이 실행"만 막고 "이번 회차를 이미 했다"는 기억하지 않는다.
- 관찰 3 — runkey: 시각차와 무관하게 1번. 누가 실행했는지는 실행마다 다르다(3회 중 인스턴스1·2가 번갈아). 회차 단위의 유일 키가 "한 번만"을 만든다.
- 3회 실행의 행 수는 모두 같았다(none 3·3, lock 1·3, runkey 1·1). 점검 재실행 3회도 같았다.
- 참고: 원본 17의 "DB 락 → 락 잡은 1대만 실행"은 실행 시각이 겹칠 때만 성립한다. 시계가 어긋나거나 작업이 짧으면 락만으로는 중복 실행을 막지 못한다(위 실험). 회차 키(또는 리더 선출 + 회차 키)가 필요하다 → [30-scheduler-and-cron-ha](../30-scheduler-and-cron-ha/2-summary.md).

## 쓰이는 자료구조·알고리즘

- **유일 인덱스(B+Tree)** — 실험의 `PRIMARY KEY(job, run_date)`. 같은 키의 두 번째 삽입을 DB가 원자적으로 거절한다. 멱등의 바닥 → [database/08-btree-indexes](../../database/08-btree-indexes/2-summary.md), [13-idempotency](../13-idempotency/2-summary.md).
- **락 테이블(해시)** — advisory lock은 키(정수) → 소유 세션의 표다. 소유만 기록하고 이력은 없다. 그래서 "이미 했나"를 답하지 못한다.
- **의존 그래프** — 동기 호출 체인의 깊이 = 그래프의 최장 경로. 가용성은 경로 위 노드의 곱, 지연은 합.
- **유한 큐(링 버퍼)** — 무한 큐(원본 8)의 처방은 상한 있는 큐 + 거절 → [12-backpressure-and-load-shedding](../12-backpressure-and-load-shedding/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 설계 리뷰 질문 (결합 종류별)

```text
 공유 상태   이 데이터의 주인은 누구인가? 인스턴스가 2대가 되면 이 코드는 몇 번 도나?
 시간 결합   이 호출의 타임아웃은? 위·아래 계층 중 누가 재시도하나? 최악 시간 = 타임아웃 × 시도 수 + 재시도 대기(백오프) 합은 SLO 안인가?
 용량 결합   한 대(한 존)가 빠지면 남은 쪽 사용률은? 증설하면 하류(DB 커넥션)는 몇 배가 되나?
 검증 안 된 가정  마지막으로 복원·페일오버·롤백을 실제로 해 본 날은?
```

### 2. 운영에서 찾는 쿼리 (예)

```sql
-- 같은 회차가 두 번 이상 실행됐나 (실행 기록 테이블이 있을 때)
SELECT job, run_date, count(*) FROM job_history GROUP BY job, run_date HAVING count(*) > 1;
-- 앱 인스턴스 수 × 풀 크기가 DB 한도에 얼마나 가까운가 (PostgreSQL)
SELECT count(*) AS conns, current_setting('max_connections') AS max FROM pg_stat_activity
 WHERE backend_type = 'client backend';   -- autovacuum 등 서버 프로세스 제외. 앱별로는 application_name·usename으로 더 거른다
```

```promql
# 무한 큐의 신호: 최근 15분 큐 길이의 추세(선형 회귀 기울기)가 상승 — 단조 증가까지 보장하지는 않는다 (지표 이름은 예시)
deriv(queue_depth[15m]) > 0
# 한 대 빠지면 남은 쪽 사용률 — 평균 사용률(0~1) × N/(N-1)이 0.9를 넘으면 여유 없음 (지표 이름은 예시)
avg(instance_cpu_utilization_ratio{job="api"}) * count(up{job="api"} == 1) / (count(up{job="api"} == 1) - 1)
```

### 3. 처방 코드 — 설정 하나로 막는 것들 (Java)

```java
// 원본 10 타임아웃 없음 → 연결·요청 타임아웃을 명시 (JDK HttpClient)
HttpClient client = HttpClient.newBuilder().connectTimeout(Duration.ofMillis(300)).build();
HttpRequest req = HttpRequest.newBuilder(uri).timeout(Duration.ofSeconds(2)).build();

// 원본 8 무한 큐 → 상한 있는 큐 + 넘치면 호출자에게 실행시켜 속도를 늦춘다(역압 — 실행기가 종료(shutdown)된 뒤의 거절 작업은 실행되지 않고 버려진다)
ExecutorService pool = new ThreadPoolExecutor(8, 8, 0, TimeUnit.SECONDS,
        new ArrayBlockingQueue<>(200), new ThreadPoolExecutor.CallerRunsPolicy());
```

- `Executors.newFixedThreadPool(n)`은 내부 큐가 상한 없는 `LinkedBlockingQueue`다(JDK 문서: "operating off a shared unbounded queue"). 유입이 처리보다 많으면 큐가 무한히 자란다.

### 4. 항목을 고치는 순서

1. 데이터를 잃거나 두 번 쓰는 것(공유 상태 17·20·21, 23)부터.
2. 연쇄 장애를 부르는 것(시간·용량 결합 10·11·14·15).
3. 검증 안 된 가정을 리허설로 바꾼다(22·24·25 — 45의 게임 데이).
4. 구조 문제(1·2·3·7)는 비용이 크니 측정한 근거로 한다.

## 장애 시나리오와 대처

### 1. ⚠ 자정 정산이 인스턴스 수만큼 실행 — 3배 지급

- 현상: 서버를 3대로 늘린 다음 날 정산 금액이 3배다.
- 보이는 형태: 실행 기록에 같은 회차 3건(위 SQL), 인스턴스마다 "정산 완료" 로그.
- 원인: 인메모리 스케줄러(원본 17). 락을 넣었어도 실행이 짧고 시계가 어긋나면 순차로 다시 실행된다(실험: lock 150ms → 3행).
- 대처: 회차 유일 키(`job, run_date`)와 지급을 한 트랜잭션으로. 스케줄러를 하나로 모으거나 리더 선출을 쓰더라도 회차 키는 남긴다. 지급 자체에도 멱등 키(13).

### 2. ⚠ 깊은 헬스체크 → 부분 장애가 전체 장애로

- 현상: DB가 2초 느려졌을 뿐인데 로드 밸런서가 모든 인스턴스를 빼서 전면 503.
- 보이는 형태: 같은 시각에 전 인스턴스가 unhealthy, 헬스체크 엔드포인트 지연 = DB 지연.
- 원인: 헬스체크(특히 liveness)가 의존성을 확인한다(원본 14). 의존성 하나의 느림이 모든 인스턴스의 "죽음"이 된다.
- 대처: liveness는 프로세스 자신만 본다. readiness에서 의존성을 보더라도 전 인스턴스가 함께 빠지지 않게(의존성 문제는 오류·폴백으로 처리). 준비 해제·종료 순서는 [14-graceful-shutdown](../14-graceful-shutdown/2-summary.md).

### 3. ⚠ 이중화했는데 한 대 장애에 나머지도 쓰러진다

- 현상: 2대 중 1대가 죽자 몇 분 뒤 남은 1대도 응답 불능.
- 보이는 형태: 평소 각 70% → 장애 뒤 남은 쪽 100% 포화, 큐·지연 폭증, 헬스체크 실패.
- 원인: 용량 계획 없이 이중화(원본 15). 한 대의 몫을 다른 쪽이 받을 여유가 없다.
- 대처: 평소 사용률 ≤ (N−1)/N. 위 PromQL로 "한 대 빠지면" 사용률을 상시 본다. 로드 셰딩으로 넘치는 몫을 버린다(12).

### 4. ⚠ 증설(오토스케일)이 DB를 죽인다

- 현상: 트래픽이 늘어 앱이 10대 → 30대로 늘자 DB가 `too many connections`로 거절하기 시작했다.
- 보이는 형태: `FATAL: sorry, too many clients already`(PostgreSQL), 앱 쪽 커넥션 풀 획득 타임아웃, DB CPU 포화.
- 원인: 병목이 DB인데 앱을 늘렸다(원본 5·9). 인스턴스 수 × 풀 크기(`maximumPoolSize`) = 그 앱 풀들이 열 수 있는 DB 커넥션 상한(다른 클라이언트 연결은 별도).
- 대처: 증설 전에 병목을 잰다([21](../21-scaling-principles/2-summary.md)). 오토스케일 상한을 DB 커넥션 예산에서 역산한다. 커넥션 풀러(PgBouncer)·풀 크기 축소 → [database/21-connection-pooling](../../database/21-connection-pooling/2-summary.md).

### 5. ⚠ 백업은 있었는데 복원이 안 된다

- 현상: 실수로 테이블을 지웠다. 백업에서 복원하려니 파일이 깨졌거나, 복원에 예상보다 몇 배 오래 걸린다.
- 보이는 형태: 복원 리허설 기록이 없다. 복제본에도 `DELETE`가 그대로 반영됐다(원본 23).
- 원인: 복원해 본 적 없는 백업(원본 22), 복제를 백업으로 착각(원본 23).
- 대처: 정기 복원 리허설로 RTO를 실측한다. 논리 사고(삭제)는 시점 복구(PITR)로 → [database/20-backup-and-pitr](../../database/20-backup-and-pitr/2-summary.md), [46-disaster-recovery](../46-disaster-recovery/2-summary.md).

## 핵심 문장

- 서버 설계 안티패턴은 대개 좋은 의도의 국소 결정이 숨은 결합(공유 상태·시간·용량·검증 안 된 가정)을 만든 것이다.
- 탐지 신호가 있다: 같은 회차 실행 N건, 전 인스턴스 동시 unhealthy, 증설 뒤 DB 커넥션 급증, 큐 길이 단조 증가.
- 실험에서 인메모리 스케줄러 3대는 정산을 3번 했고, 실행하는 동안만 잡는 락은 시각이 150ms씩 어긋나자 역시 3번 했다. 회차 유일 키만 시각차와 무관하게 1번이었다.
- 락은 "동시에 둘"을 막고, 유일 키는 "이번 회차를 이미 했다"를 기억한다. 정확히 한 번이 필요하면 후자가 필요하다.
- 이중화는 용량 계획과 짝이다. N대면 평소 사용률 ≤ (N−1)/N.

## 관련 주제·근거

- 선행
  - [23-deployment-strategies](../23-deployment-strategies/2-summary.md)
  - 원본 [systems/server-design/11-antipatterns.md](../../systems/server-design/11-antipatterns.md) — 29개 항목 전체, 한 줄 요약 카드
- 후속·연결
  - [48-performance-and-stability-antipatterns-in-code](../48-performance-and-stability-antipatterns-in-code/2-summary.md) — 코드 수준 안티패턴
  - [30-scheduler-and-cron-ha](../30-scheduler-and-cron-ha/2-summary.md) — 스케줄러 이중화·중복 실행 방지
  - [13-idempotency](../13-idempotency/2-summary.md), [12-backpressure-and-load-shedding](../12-backpressure-and-load-shedding/2-summary.md), [05-timeouts-and-deadline-propagation](../05-timeouts-and-deadline-propagation/2-summary.md), [06-retry-backoff-jitter](../06-retry-backoff-jitter/2-summary.md)
  - [04-failure-modes-catalog](../04-failure-modes-catalog/2-summary.md) — 실패 카탈로그 F-01~25
  - [distributed/12-coordination-and-fencing](../../distributed/12-coordination-and-fencing/2-summary.md) — 분산 락이 정확성을 못 주는 이유(원본 21)
  - [database/21-connection-pooling](../../database/21-connection-pooling/2-summary.md), [database/20-backup-and-pitr](../../database/20-backup-and-pitr/2-summary.md)
  - [45-chaos-and-resilience-testing](../45-chaos-and-resilience-testing/2-summary.md) — 검증 안 된 가정을 실험으로
- 문서
  - PostgreSQL 17 문서 "System Administration Functions" — Advisory Lock Functions(`pg_try_advisory_lock`: 세션 수준, 기다리지 않음) <https://www.postgresql.org/docs/17/functions-admin.html>
  - JDK 21 `Executors.newFixedThreadPool` API 문서(공유 무제한 큐)
- 실험 목록
  - 인메모리 스케줄러 3대: `SchedulerDup.java`, 모드 none·lock(`pg_try_advisory_lock`)·runkey(`ON CONFLICT DO NOTHING`) × 시각차 0·150ms, 정산 100ms. PostgreSQL 17.11 일회용 컨테이너 + JDK 21.0.12 + JDBC 42.7.4, 3회 실행
