# reliability/40-batching-and-round-trips — 왕복 줄이기: 배칭·파이프라이닝·COPY·DataLoader — 정리 (힌트)

## 해결하는 문제

요청 하나를 보내고 응답을 기다리는 방식으로 일을 N개 하면, 일 자체가 아무리 빨라도 **왕복 시간 × N**이 바닥으로 깔린다.

```text
 한 건씩 (왕복 N번)                            모아서 (왕복 1번)
 앱 ──INSERT 1──>  DB                          앱 ──INSERT 1..1000──> DB
    <────OK─────                                  <──────OK×1000──────
 앱 ──INSERT 2──>                              
    <────OK─────                               
 ... × 5000                                    ... × 5
 RTT 3ms × 5000 = 15초 이상                     RTT 3ms × 5 + 처리 시간
```

- *왕복 시간(RTT, round-trip time)*: 요청이 상대에게 갔다가 응답이 돌아오기까지 걸리는 네트워크 시간. 같은 데이터센터 안에서도 수백 µs~수 ms다.
- *배칭(batching)*: 여러 요청을 한 번에 묶어 보내는 것.
- *파이프라이닝(pipelining)*: 응답을 기다리지 않고 요청을 연달아 보낸 뒤 응답을 한꺼번에 읽는 것.

쉬운 예: 마트에서 물건 50개를 살 때 하나 집을 때마다 계산대에 가서 계산하고 돌아오는 것과, 장바구니에 다 담아 한 번 계산하는 것의 차이다.

똑같은 구조다.\
실무 예: 1건씩 INSERT 10만 번, ORM의 N+1 쿼리, Redis 명령 수천 개를 하나씩, 마이크로서비스가 목록의 항목마다 다른 서비스 호출, Kafka 프로듀서의 레코드 묶음.\
N+1 쿼리 자체는 [database/23-orm-and-n-plus-one](../../database/23-orm-and-n-plus-one/2-summary.md), 대량 변경의 청크 설계는 [database/34-large-backfill-and-batch-dml](../../database/34-large-backfill-and-batch-dml/2-summary.md), 파일 적재는 [database/35-bulk-file-import-export](../../database/35-bulk-file-import-export/2-summary.md)에 있다. 이 노트는 **왕복과 배치 크기의 트레이드오프**에 집중한다.

## 동작·원리

### 1. 왕복 비용 모델

```text
 한 건 처리 시간 ≈ RTT + 서버 처리 + (커밋이면 로그 flush 대기)
 N건, 한 건씩      ≈ N × (RTT + 처리 + flush)
 N건, B개씩 묶음   ≈ (N/B) × (RTT + flush) + N × 처리'      (처리'은 묶음 덕에 더 작아지기도 함)
```

- Redis 문서 "Redis pipelining": RTT가 250ms인 느린 링크라면 서버가 초당 10만 요청을 처리할 수 있어도 클라이언트는 초당 최대 4요청밖에 못 한다. 루프백처럼 RTT가 짧아도 많이 쌓이면 크다.
- 같은 문서: 파이프라이닝의 이득은 RTT만이 아니다. 명령마다 `read()`·`write()` 시스템 콜을 하던 것을 여러 명령에 한 번씩으로 줄여 서버의 초당 처리량도 늘린다. 문서는 파이프라인 길이를 늘리면 처리량이 거의 선형으로 늘다가 파이프라인 없을 때의 약 10배에 이른다고 적는다(문서 그림의 환경 기준 — 아래 redis-benchmark 실험에서는 `-P 100`에서 14~19배였다).
- **커밋도 왕복처럼 비싸다**: 자동 커밋으로 한 건씩 넣으면 커밋마다 WAL을 디스크에 flush하고 기다린다. 아래 실험에서 이 비용(행당 약 3~4ms)이 RTT보다 컸다.
  - *WAL(Write-Ahead Log)*: 변경을 데이터 파일보다 먼저 기록하는 로그. 커밋의 내구성은 이 로그가 디스크에 닿았는지로 정해진다(→ [database/19-wal-and-logging](../../database/19-wal-and-logging/2-summary.md)).

### 2. 왕복을 줄이는 방법들

| 방법 | 하는 일 | 예 |
|---|---|---|
| 트랜잭션 묶기 | 커밋(flush 대기)을 N번 → 1번 | `BEGIN … COMMIT`, JDBC `setAutoCommit(false)` |
| 배치 실행 | 문장 N개를 한 번에 보냄 | JDBC `addBatch`/`executeBatch` |
| 다중 VALUES | 문장 하나에 행 N개 | `INSERT … VALUES (…),(…)`, pgjdbc `reWriteBatchedInserts=true` |
| 대량 적재 명령 | 전용 프로토콜로 스트리밍 | PostgreSQL `COPY`, MySQL `LOAD DATA` |
| 파이프라이닝 | 응답 대기 없이 연달아 | Redis 파이프라인, HTTP/2 다중화 |
| 모으기(coalescing) | 짧은 시간 동안 들어온 개별 요청을 하나로 | DataLoader, Kafka 프로듀서 `linger.ms` |

- PostgreSQL 17 문서 "Populating a Database"(14.4): 여러 INSERT는 자동 커밋을 끄고 끝에 한 번 커밋하라. 한 명령으로 모든 행을 넣는 `COPY`는 INSERT보다 오버헤드가 훨씬 작고, PREPARE를 쓰고 한 트랜잭션에 묶은 INSERT보다도 "거의 항상" 빠르다.
- pgjdbc 문서: `reWriteBatchedInserts`(기본 false)는 배치 INSERT를 `insert into foo (…) values (…), (…)` 한 문장으로 바꾼다. 문서는 2~3배 성능 향상을 적는다.
- DataLoader README: 한 실행 프레임(이벤트 루프의 한 틱) 안에서 일어난 개별 `load(key)`들을 모아 배치 함수 한 번으로 부른다. 배치 함수는 키 배열과 **같은 길이·같은 순서**의 값 배열을 돌려줘야 한다.
- Kafka 4.1 프로듀서 기본값(`ProducerConfig.java`): `batch.size` 16384바이트, `linger.ms` 5ms — 레코드를 최대 5ms 기다려 묶는다(→ [distributed/17-queues-logs-and-delivery-semantics](../../distributed/17-queues-logs-and-delivery-semantics/2-summary.md)).

### 실험 1: 같은 5000행을 다섯 방식으로 (PostgreSQL 17)

- 클라이언트 JDBC(pgjdbc 42.7.4) → PostgreSQL 17.11. 같은 Docker 네트워크 직결과, 한 방향 1ms 지연을 넣는 프록시 경유(RTT 약 +2ms) 두 경우.
- 모드: 자동 커밋 1행씩 / 한 트랜잭션 1행씩 / `executeBatch` 1000행씩 / 같은 배치 + `reWriteBatchedInserts=true` / `COPY`.

```java
case "batch1000" -> {
    c.setAutoCommit(false);
    try (PreparedStatement ps = c.prepareStatement("INSERT INTO t VALUES (?, ?)")) {
        for (int i = 0; i < n; i++) {
            ps.setInt(1, i); ps.setString(2, "v" + i); ps.addBatch();
            if ((i + 1) % 1000 == 0) ps.executeBatch();          // 1000행마다 한 번 보냄
        }
        ps.executeBatch();
    }
    c.commit();
}
case "copy" -> c.unwrap(PGConnection.class).getCopyAPI()
                .copyIn("COPY t FROM STDIN", new StringReader(tsv)); // 행 전체를 한 명령으로
```

(실험, Docker postgres:17(17.11) `--cpus=2` + eclipse-temurin:21-jdk `--cpus=2`, pgjdbc 42.7.4, 기본 설정(fsync·synchronous_commit on), 2026-10-01 — 2회 실행 중 두 번째)

```text
지연 프록시 한 방향 0ms, SELECT 1 왕복 중앙값 0.63ms, 행 5000개
autocommit-1row       16567ms  ( 3.313ms/행)  들어간 행 5000
tx-1row                 812ms  ( 0.162ms/행)  들어간 행 5000
batch1000               137ms  ( 0.027ms/행)  들어간 행 5000
batch1000-rewrite        67ms  ( 0.013ms/행)  들어간 행 5000
copy                     33ms  ( 0.007ms/행)  들어간 행 5000
지연 프록시 한 방향 1ms, SELECT 1 왕복 중앙값 3.66ms, 행 5000개
autocommit-1row       29378ms  ( 5.876ms/행)  들어간 행 5000
tx-1row               14461ms  ( 2.892ms/행)  들어간 행 5000
batch1000               197ms  ( 0.039ms/행)  들어간 행 5000
batch1000-rewrite        76ms  ( 0.015ms/행)  들어간 행 5000
copy                     36ms  ( 0.007ms/행)  들어간 행 5000
```

첫 번째 실행: 직결 20029 / 966 / 155 / 68 / 28ms, 지연 31871 / 14441 / 173 / 75 / 35ms.

- 관찰 1 — 직결에서도 자동 커밋 1행씩이 16~20초로 가장 느리다. 한 트랜잭션으로 묶기만 해도 0.8~1초다. 행마다 커밋 flush를 기다린 비용이다.
  - 확인 실험: 같은 자동 커밋 1행씩에 `SET synchronous_commit = off`만 주자 15872ms → 939ms(행당 0.188ms)로, 트랜잭션 묶기(918ms)와 거의 같아졌다(같은 날 별도 실행). 사실 점검 재실행에서는 0.8~1.5초 vs 0.8~1.1초로, 같은 자릿수(약 1초)지만 매번 똑같지는 않았다 — 16초에서 1초 안팎으로 떨어지는 것이 요점이다. 단, 이 설정은 DB가 죽으면 가장 최근 트랜잭션들을 잃을 수 있다(PostgreSQL 17 문서 28.4 "Asynchronous Commit": 평소 커밋은 WAL이 영구 저장소에 flush될 때까지 기다리며, 짧은 트랜잭션에서는 이 대기가 전체 시간의 큰 부분이다).
- 관찰 2 — RTT를 약 3ms로 늘리자 1행씩 방식(tx-1row)은 0.8초 → 14.5초로 18배 느려졌다(첫 실행 15배, 사실 점검 재실행 0.7 → 14.9초로 21배). 행당 2.9ms ≈ RTT다. **왕복이 바닥이 됐다.**
- 관찰 3 — 같은 RTT에서 batch1000은 137 → 197ms, COPY는 33 → 36ms로 거의 그대로다. 왕복이 5번(배치)·1번(COPY)뿐이기 때문이다.
- 관찰 4 — `reWriteBatchedInserts`는 batch1000보다 약 2배 빨랐다(137 → 67ms. 재실행: 직결 122 → 56ms, 지연 219 → 71ms로 2~3배). pgjdbc 문서의 "2~3배"와 같은 범위다.
- 커리큘럼 ⚠ "1건씩 INSERT 10만 번 → 수 분": 이 환경 기준 자동 커밋 행당 3~4ms면 10만 행에 5~7분이 된다(계산). COPY 행당 0.007ms면 1초 안팎이다(계산 — 10만 행으로 직접 재지는 않았다).

### 3. 배치 크기 ↔ 지연 트레이드오프

```text
 개별 요청 도착 ──> [ 버퍼 ] ──flush 조건──> 한 번에 전송
                     ├ 크기 트리거: maxSize개가 모이면
                     └ 시간 트리거: 첫 항목이 maxWait만큼 기다리면
 항목 하나가 버퍼에서 기다리는 시간 ≈ min(maxWait, maxSize / 도착률)
```

- 실제 상한은 maxWait보다 조금 크다: maxWait + 타이머 확인 주기 + 타이머 스레드가 늦게 깨는 스케줄링 지연(+ flush 처리 시간). 시간 트리거를 타이머가 주기적으로 확인하기 때문이다(실험 2: 주기 1ms, maxWait 20ms인데 max 20.4~23.3ms).
- maxSize / 도착률은 도착이 고르다는 가정의 근사다. 도착이 무작위로 몰렸다 끊기면 maxSize개가 차는 시간이 이보다 길 수 있다(그때는 maxWait가 막는다).

- 배치가 크면 왕복당 처리량은 늘지만, **모으는 대기 시간이 각 요청의 지연에 더해진다.** 도착이 드물면 시간 트리거까지 기다리게 된다.
- 배치가 너무 크면 다른 비용이 생긴다
  - 한 트랜잭션이 오래 걸려 락을 오래 쥔다(→ [database/34](../../database/34-large-backfill-and-batch-dml/2-summary.md) 「청크 = 짧은 트랜잭션 여러 개」).
  - 메시지 크기 한도에 걸린다: MySQL 8.4 문서 "Packet Too Large" — 서버 `max_allowed_packet` 기본 64MB(mysql 클라이언트 기본 16MB)를 넘는 패킷이면 `ER_NET_PACKET_TOO_LARGE`를 내고 연결을 닫는다. pgjdbc 문서는 확장 쿼리 프로토콜에서 한 문장의 바인드 파라미터가 65535개로 제한된다고 적는다.
  - Redis 문서: 파이프라인으로 보내는 동안 서버는 응답을 메모리에 쌓아야 하므로, 아주 많은 명령은 예컨대 1만 개씩 끊어 보내라고 권한다.

### 실험 2: 크기·시간 트리거 배처가 더하는 대기

- `maxSize=100`, `maxWait=20ms`. 도착률 고정(50·500·5000건/s) 3초씩. 항목이 들어온 뒤 flush될 때까지의 시간을 잰다.

```java
synchronized void add(long now) {
    if (buf.isEmpty()) firstAt = now;
    buf.add(now);
    if (buf.size() >= maxSize) { bySize++; flush(now); }          // 크기 트리거
}
synchronized void tick(long now) {                                // 1ms마다 타이머
    if (!buf.isEmpty() && now - firstAt >= maxWaitNs) flush(now); // 시간 트리거
}
```

(실험, Docker eclipse-temurin:21-jdk `--cpus=2`, 2회 실행 — 두 번째 실행도 ±0.4ms 안. 사실 점검 재실행 2회에서는 p99 19.7~21.1ms, max 최대 23.3ms로 1~2ms 더 흔들렸다 — 타이머가 1ms 간격이고 공유 호스트라 실행마다 다르다)

```text
도착    50건/s: 항목   150, flush   75번(크기 트리거 0), 평균 배치 2.0건, 대기 p50= 20.0ms p99= 20.4ms max= 20.4ms
도착   500건/s: 항목  1500, flush  137번(크기 트리거 0), 평균 배치 10.9건, 대기 p50= 10.5ms p99= 20.6ms max= 21.4ms
도착  5000건/s: 항목 15000, flush  150번(크기 트리거 150), 평균 배치 100.0건, 대기 p50= 10.0ms p99= 19.7ms max= 20.7ms
```

- 관찰 1 — 도착이 드물면(50건/s) 배치는 평균 2건뿐인데 대기는 20ms(= maxWait)다. 왕복은 거의 못 줄이고 지연만 20ms 늘었다.
- 관찰 2 — 5000건/s에서는 크기 트리거로 100건씩 찼지만, 100건이 차는 데 20ms(= 100 / 5000)가 걸려 p99 대기는 여전히 약 20ms다.
- 해석: 배처는 p99에 약 min(maxWait, maxSize / 도착률)을 더한다(max가 20ms를 조금 넘은 것은 1ms 타이머 확인 주기와 공유 호스트 스케줄링 때문이다). 커리큘럼 ⚠ "배치를 모으는 대기 시간이 p99에 더해진다"가 이것이다. maxWait는 지연 예산(→ [08-time-budget-allocation](../08-time-budget-allocation/2-summary.md))에서 떼어 줄 수 있는 만큼만 잡는다.

### 4. 배치의 부분 실패

```text
 배치 [r1 r2 r3 r4 r5 r6(실패) r7 r8 r9 r10]
 시스템마다 다르다
   전부 실패(원자적)   → 실패 하나 때문에 9건도 버려짐. 재시도는 실패 원인을 고쳐야 성공
   일부만 실패          → 응답 안의 항목별 결과를 보지 않으면 "성공"으로 착각
```

- 어느 쪽인지는 **제품·드라이버·설정**이 정한다. 확인하고 코드에 반영한다.
  - pgjdbc 42.7.4 + PostgreSQL 17(아래 실험): 자동 커밋이 켜져 있어도 배치 전체가 실패하고 남은 행이 0이었다.
  - Redis 파이프라인(아래 실험): 명령마다 따로 실행되고 응답도 따로 온다. 중간 하나가 에러여도 나머지는 반영된다.
  - Elasticsearch `_bulk`: 응답 최상위 `errors`와 항목별 `status`로 개별 실패를 알린다. 실패한 동작이 있어도 요청 전체는 계속 처리된다(Elastic Bulk API 문서).
  - DataLoader: 배치 함수가 키마다 값 또는 `Error` 인스턴스를 돌려줄 수 있다(README).

### 실험 3: 부분 실패는 어떻게 보이나

```java
int[] ids = {0, 1, 2, 3, 4, 3, 6, 7, 8, 9};       // 6번째 값이 중복 키
for (int id : ids) { ps.setInt(1, id); ps.addBatch(); }
try { ps.executeBatch(); }
catch (BatchUpdateException e) { print(Arrays.toString(e.getUpdateCounts())); }
```

(실험, pgjdbc 42.7.4 → PostgreSQL 17.11)

```text
autocommit=true: BatchUpdateException updateCounts=[-3, -3, -3, -3, -3, -3, -3, -3, -3, -3]
   원인: ERROR: duplicate key value violates unique constraint "t_pkey"
   테이블에 남은 행: 0 []
autocommit=false+commit: BatchUpdateException updateCounts=[-3, -3, -3, -3, -3, -3, -3, -3, -3, -3]
   원인: ERROR: duplicate key value violates unique constraint "t_pkey"
   테이블에 남은 행: 0 []
autocommit=true+rewrite: BatchUpdateException updateCounts=[-3, -3, -3, -3, -3, -3, -3, -3, -3, -3]
   원인: ERROR: duplicate key value violates unique constraint "t_pkey"
   테이블에 남은 행: 0 []
```

- `-3`은 JDBC `Statement.EXECUTE_FAILED`다. 세 경우 모두 10건 전부 실패로 보고되고, 테이블에도 하나도 남지 않았다.
- 해석: 이 조합에서는 "일부만 들어갔는데 모른다"는 일은 없었다. 대신 **중복 1건 때문에 나머지 9건도 버려졌다.** 재시도하려면 실패 행을 걸러야 한다. 다른 드라이버(예: MySQL Connector/J)는 설정에 따라 실패 뒤에도 계속 실행할 수 있다 [?] — 쓰는 드라이버로 같은 실험을 해 본다.

(실험, Redis 7.4.9, `nc`로 명령 4개를 한 번에 보냄)

```text
+OK
+OK
-ERR value is not an integer or out of range
+OK
---
a
hello
b
```

- 3번째 `INCR s`만 실패하고 앞뒤 `SET`은 반영됐다(`MGET k1 s k2` → `a hello b`). 응답 목록에서 에러 항목을 찾지 않으면 "파이프라인 성공"으로 착각한다.

## 쓰이는 자료구조·알고리즘

- **버퍼 + 크기·시간 트리거 flush**: 위 배처. 고정 크기라면 링 버퍼(→ [data-structure/25-ring-buffer](../../data-structure/25-ring-buffer/2-summary.md))로 구현해 할당을 줄인다. 시간 트리거는 타이머 하나(첫 항목 기준).
- **키 중복 제거·순서 맞추기**: DataLoader식 모으기는 키를 모아 중복을 없애고(`Set`/`Map`), 결과를 입력 키 순서로 다시 맞춘다(키 → 인덱스 맵).
- **청크 분할**: N개를 B개씩 자르기. 크기 한도(패킷·파라미터 수)를 넘지 않게 B를 정한다.
- **파이프라인 = 순서 있는 큐 두 개**: 보낸 요청 순서대로 응답이 온다(Redis·HTTP/1.1 파이프라이닝). 응답을 i번째 요청과 짝지을 때 FIFO 큐를 쓴다. HTTP/2는 스트림 ID로 짝지어 순서가 달라도 된다(→ [network/36-http2-multiplexing](../../network/36-http2-multiplexing/2-summary.md)).
- **Nagle 알고리즘과 같은 원리**: 작은 패킷을 모아 보내는 TCP 수준의 배칭이다. 지연 ACK와 겹치면 지연이 생긴다(→ [network/22-nagle-and-delayed-ack](../../network/22-nagle-and-delayed-ack/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 찾기 — 왕복이 많은 곳

```bash
# 요청 하나에 쿼리가 몇 번 나가나 — PostgreSQL 문장 통계(pg_stat_statements 확장 필요)
psql -c "SELECT calls, mean_exec_time, query FROM pg_stat_statements ORDER BY calls DESC LIMIT 10"
# Redis: 초당 명령 수와 클라이언트 수
redis-cli INFO stats | grep instantaneous_ops_per_sec
# 처리량 대비 파이프라인 효과 (redis-benchmark: -P 파이프라인 길이)
redis-benchmark -t set -n 100000 -c 1 -P 16 -q
```

- 트레이스에서 같은 하위 호출이 수십 번 반복되는 "빗살" 모양이 보이면 N+1·1건씩 호출이다(→ [17-distributed-tracing](../17-distributed-tracing/2-summary.md)).

(실험, `redis-benchmark` 7.4.9, 클라이언트 연결 1개, SET 10만 건, 같은 Docker 네트워크)

```text
# -P 1 (마지막 요약 줄)
SET: 11504.83 requests per second, p50=0.055 msec
# -P 16
SET: 98425.20 requests per second, p50=0.119 msec
# -P 100
SET: 222717.16 requests per second, p50=0.367 msec
```

- 파이프라인 길이 1 → 16 → 100에서 처리량은 약 8.6배 → 19배로 늘었다(사실 점검 재실행 — Redis 컨테이너 안 루프백: 15676 → 143062 → 218341 requests/s, 약 9.1배 → 13.9배, p50 0.039 → 0.079 → 0.375ms로 같은 경향). 그런데 p50 지연은 0.055 → 0.119 → 0.367ms로 **늘었다**. 묶음이 클수록 한 명령이 묶음과 함께 기다리기 때문이다. 처리량과 지연의 트레이드오프가 그대로 보인다.

### 2. 고치기 — Java

```java
// N+1 대신 한 번에: id 목록을 모아 IN 조회 1번 (크기 한도 때문에 청크로)
Map<Long, User> users = new HashMap<>();
for (List<Long> chunk : Lists.partition(new ArrayList<>(ids), 1000)) {   // Guava 예
    users.putAll(userRepo.findAllById(chunk).stream().collect(toMap(User::id, u -> u)));
}
return orders.stream().map(o -> new OrderView(o, users.get(o.userId()))).toList();
```

```java
// JDBC 배치: 트랜잭션 + addBatch + 실패 처리
try (Connection c = ds.getConnection()) {
    c.setAutoCommit(false);
    try (PreparedStatement ps = c.prepareStatement("INSERT INTO t(id, v) VALUES (?, ?)")) {
        for (Row r : rows) { ps.setLong(1, r.id()); ps.setString(2, r.v()); ps.addBatch(); }
        ps.executeBatch();
        c.commit();
    } catch (BatchUpdateException e) {
        c.rollback();
        int[] counts = e.getUpdateCounts();    // EXECUTE_FAILED(-3)·성공 수 확인 — 드라이버마다 의미가 다르다
        throw new PartialBatchFailure(counts, e.getNextException());
    }
}
```

### 3. 고치기 — TypeScript (DataLoader)

```typescript
import DataLoader from 'dataloader';

// 같은 틱 안의 load(id)들을 모아 배치 함수 한 번으로
const userLoader = new DataLoader<number, User>(async (ids) => {
  const rows = await db.query('SELECT * FROM users WHERE id = ANY($1)', [ids]);
  const byId = new Map(rows.map((r: User) => [r.id, r]));
  // 키 배열과 같은 길이·같은 순서. 없으면 Error 인스턴스
  return ids.map((id) => byId.get(id) ?? new Error(`user ${id} not found`));
}, { maxBatchSize: 500 });
```

- DataLoader 기본 `maxBatchSize`는 `Infinity`다(README 옵션 표). 크기 한도가 있는 저장소면 직접 제한한다.
- `batchScheduleFn`으로 모으는 시간을 늘릴 수 있다(README 예: `setTimeout(callback, 100)`). 늘린 만큼 지연에 더해진다.

### 4. 배치 크기 정하기

1. 한도부터: 패킷·메시지 크기, 파라미터 수, 트랜잭션 시간(락), 서버 메모리.
2. 지연 예산: 모으는 대기 `maxWait`는 요청 지연 예산에서 줄 수 있는 만큼.
3. 측정: 배치 크기를 바꿔 가며 처리량과 p99를 함께 잰다(위 redis-benchmark처럼 처리량만 보면 지연 증가를 놓친다).
4. 부분 실패: 그 시스템이 "전부 실패"인지 "항목별 결과"인지 실험으로 확인하고, 항목별이면 응답을 전부 검사한다.

## 장애 시나리오와 대처

### 1. 1건씩 INSERT 10만 번 → 수 분

- 현상: 야간 적재가 몇 분씩 걸린다. DB CPU는 한가하다.
- 보이는 형태: 문장 통계에서 같은 INSERT의 `calls`가 행 수만큼, 평균 실행 시간은 짧다. 트레이스에 짧은 DB 스팬이 빽빽하다.
- 원인: 행마다 왕복 + (자동 커밋이면) 커밋 flush 대기. 실험 1: 자동 커밋 1행씩 행당 3~6ms.
- 대처: 한 트랜잭션으로 묶고(실험: 16.6초 → 0.8초), 배치·다중 VALUES로 보내고(67~137ms), 대량이면 `COPY`(33ms). 단 거대 트랜잭션 하나가 되지 않게 청크로 커밋한다.

### 2. 배치가 너무 큼 → 락 장기 보유·패킷 한도

- 현상: 배치 적재 중 다른 요청이 그 테이블에서 멈춘다. 또는 `Packet for query is too large`.
- 보이는 형태: 긴 트랜잭션, 락 대기 증가, 복제 지연. MySQL `ER_NET_PACKET_TOO_LARGE` 뒤 연결 끊김. pgjdbc 바인드 파라미터 65535개 초과 오류.
- 원인: 배치 하나가 크기 한도와 트랜잭션 시간 한도를 넘었다.
- 대처: 청크 크기를 한도 아래로(행 수 × 컬럼 수 < 65535 등). 청크마다 커밋하고 진행 지점을 기록한다(→ database/34).

### 3. 배치를 모으는 대기가 p99에 더해짐

- 현상: 배처를 도입한 뒤 처리량은 늘었는데 한가한 시간대 p99가 오히려 20ms 늘었다.
- 보이는 형태: 실험 2의 50건/s처럼 배치 크기는 작은데 대기는 maxWait만큼.
- 원인: 시간 트리거까지 기다린다. 도착이 드물면 이득 없이 지연만 생긴다.
- 대처: maxWait를 지연 예산 안으로 줄인다. 대기 중인 항목이 하나뿐이고 연결이 한가하면 바로 보낸다(적응형). 지연에 민감한 요청은 배치 경로에서 뺀다.

### 4. 배치 일부만 실패했는데 전체 성공으로 처리

- 현상: 동기화 작업이 "완료"인데 몇몇 레코드가 대상 시스템에 없다.
- 보이는 형태: 응답 코드는 200·OK. 응답 본문의 항목별 결과(Elasticsearch `errors: true`, Redis 파이프라인의 `-ERR` 항목)를 읽지 않는다.
- 원인: 항목별 결과를 주는 배치 API를 전체 성공/실패로만 판단했다.
- 대처: 항목별 결과를 전부 검사하고, 실패 항목만 재시도하거나 격리 큐로 보낸다. 성공·실패 건수를 지표로 내고, 적재 후 건수를 대사한다. 재시도는 멱등해야 한다(→ [13-idempotency](../13-idempotency/2-summary.md), [distributed/18-consumer-failure-handling](../../distributed/18-consumer-failure-handling/2-summary.md)).

### 5. 원자적 배치에서 한 건 때문에 전체가 계속 실패

- 현상: 같은 배치가 재시도마다 실패한다. 진행이 멈췄다.
- 보이는 형태: 실험 3처럼 `updateCounts`가 전부 `-3`, 테이블 변화 없음, 같은 제약 위반 메시지 반복.
- 원인: 배치 안에 영구적으로 실패하는 행(중복 키·형식 오류)이 하나 있다.
- 대처: 실패 시 배치를 반으로 나눠 재시도해 문제 행을 찾거나(이분), 1건씩 재처리해 문제 행만 격리한다. `INSERT … ON CONFLICT DO NOTHING`처럼 중복을 허용하는 문장이 맞는지 업무 규칙으로 판단한다.

## 핵심 문장

- 1건씩 N번은 왕복(RTT)과 커밋 flush를 N번 낸다. 일 자체보다 기다림이 바닥이 된다.
- 실험: RTT가 약 3ms가 되자 1행씩 INSERT는 행당 2.9ms로 묶였고, 1000행 배치와 COPY는 거의 그대로였다.
- 트랜잭션 묶기 → 배치·다중 VALUES → COPY 순으로 왕복과 오버헤드가 준다(실험: 16.6초 → 0.8초 → 67ms → 33ms).
- 배치는 처리량을 얻는 대신 모으는 대기를 지연에 더한다. 대기는 약 min(maxWait, maxSize / 도착률)이고, 실제 상한은 maxWait + 타이머 확인 주기 + 스케줄링 지연이다.
- 배치의 부분 실패 의미는 제품마다 다르다. 원자적이면 한 건이 전체를 막고, 항목별이면 응답을 다 검사하지 않으면 실패를 놓친다.

## 관련 주제·근거

- 선행
  - [architecture/13-latency-numbers](../../architecture/13-latency-numbers/2-summary.md) — 지연 자릿수 감각
  - [database/23-orm-and-n-plus-one](../../database/23-orm-and-n-plus-one/2-summary.md) — N+1 쿼리
  - [network/22-nagle-and-delayed-ack](../../network/22-nagle-and-delayed-ack/2-summary.md) — TCP 수준의 모으기
  - [network/03-latency-bandwidth-bdp](../../network/03-latency-bandwidth-bdp/2-summary.md) — RTT와 대역폭
- 후속·연결
  - [database/34-large-backfill-and-batch-dml](../../database/34-large-backfill-and-batch-dml/2-summary.md) — 청크 커밋·재시작
  - [database/35-bulk-file-import-export](../../database/35-bulk-file-import-export/2-summary.md) — 파일 적재·한 행 실패 정책
  - [distributed/17-queues-logs-and-delivery-semantics](../../distributed/17-queues-logs-and-delivery-semantics/2-summary.md) — 프로듀서 배칭
  - [39-async-io-gains-and-limits](../39-async-io-gains-and-limits/2-summary.md) — 동시성 vs 지연
  - [48-performance-and-stability-antipatterns-in-code](../48-performance-and-stability-antipatterns-in-code/2-summary.md) — Chatty I/O
- 문서·소스
  - Redis 문서 "Redis pipelining"(RTT 250ms 예, 시스템 콜 감소, 1만 개씩 끊어 보내기) <https://redis.io/docs/latest/develop/using-commands/pipelining/>
  - PostgreSQL 17 문서 14.4 "Populating a Database"(자동 커밋 끄기, COPY) <https://www.postgresql.org/docs/17/populate.html>
  - pgjdbc 문서 "Connection parameters" — `reWriteBatchedInserts`(기본 false, 2~3배), 바인드 파라미터 65535개 <https://jdbc.postgresql.org/documentation/use/>
  - MySQL 8.4 Reference Manual B.3.2.8 "Packet Too Large" — `max_allowed_packet` 서버 기본 64MB, mysql 클라이언트 16MB, 최대 1GB <https://dev.mysql.com/doc/refman/8.4/en/packet-too-large.html>
  - graphql/dataloader README — 한 틱 안의 load 모으기, 배치 함수 규칙, `maxBatchSize`·`batchScheduleFn` <https://github.com/graphql/dataloader>
  - Apache Kafka 4.1 `clients/.../producer/ProducerConfig.java` — `batch.size` 16384, `linger.ms` 5
  - Elastic "Bulk API" 문서 — 응답 `errors`와 항목별 결과 <https://www.elastic.co/docs/api/doc/elasticsearch/operation/operation-bulk>
- 실험 목록
  - PgBatch.java — 5000행 × 5방식, 직결 vs 한 방향 1ms 지연 프록시, 2회 + `synchronous_commit=off` 확인 1회. 전용 컨테이너 `sn-rl-w19-pg`(postgres:17 17.11)·네트워크 `sn-rl-w19-net`, pgjdbc 42.7.4, Temurin 21.0.12
  - PgPartial.java — 10행 배치 중 중복 키 1건, 자동 커밋·명시 커밋·rewrite
  - Batcher.java — maxSize 100·maxWait 20ms, 50·500·5000건/s, 2회
  - Redis 7.4.9 전용 `sn-rl-w19-redis` — `redis-benchmark -P 1/16/100`, `nc` 파이프라인 부분 실패
