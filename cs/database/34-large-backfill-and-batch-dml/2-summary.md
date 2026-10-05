# database/34-large-backfill-and-batch-dml — 대량 UPDATE·DELETE·백필: keyset 청크, 스로틀, 재시작, 검증 — 정리 (힌트)

## 해결하는 문제

운영 중인 큰 테이블의 행 수천만 개를 바꿔야 할 때가 있다.
- 새 컬럼 채우기(백필)
- 잘못 들어간 값 고치기
- 오래된 행 지우기

가장 쉬운 방법은 문장 하나다.

```sql
UPDATE orders SET amount_krw = amount * 1300;      -- 1억 행 (예시)
```

이 한 줄이 운영 DB를 흔든다.

```text
  하나의 거대한 트랜잭션
  ├─ 락: 바꾼 행 전부를 커밋까지 잡는다       → 같은 행을 바꾸려는 요청이 줄줄이 대기·타임아웃
  ├─ 되돌리기 정보: 행마다 옛 버전을 남긴다      → InnoDB undo 증가 / PostgreSQL 테이블 크기 증가(bloat)
  ├─ 복제: 레플리카가 거대한 변경을 한 번에 소화 → 복제 지연이 갑자기 수십 분으로 치솟는다 (예시)
  │        (MySQL은 커밋 때 binlog에 몰아 써서 보낸다. PostgreSQL은 WAL을 생기는 대로 보내지만
  │         레플리카 조회에는 커밋 레코드가 재생돼야 한꺼번에 보인다)
  └─ 실패: 중간에 죽으면 전부 롤백            → 몇 시간 작업이 0으로, 롤백도 오래 걸린다
```

쉬운 예: 이사할 때 짐 전부를 한 번에 옮기려고 트럭 하나에 싣는다. 트럭이 문을 막고, 중간에 고장 나면 처음부터 다시 한다.\
똑같은 구조다. 작은 상자(청크)로 나누고, 상자마다 끝냈다고 적어 두고(체크포인트), 길이 막히면 쉰다(스로틀).

실무 예:
- 무중단 마이그레이션의 백필 단계(expand → 이중 쓰기 → **백필** → 읽기 전환 → contract). 기초는 원고 [systems/server-design/08-deployment-ops.md](../../systems/server-design/08-deployment-ops.md) §2.
- Stripe는 구독 데이터를 새 테이블로 옮기며 이중 쓰기 → 읽기 경로 전환 → 쓰기 경로 전환 → 옛 데이터 제거의 4단계를 썼다. 백필은 1단계(이중 쓰기) 안에서 했고, 백필 대상 찾기는 운영 DB가 아닌 스냅샷(Hadoop·MapReduce)에서 했다(Stripe 2017).
- gh-ost는 MySQL 테이블을 청크(기본 1000행) 단위로 복사하며 복제 지연을 보고 스스로 멈춘다(gh-ost 문서).

## 동작·원리

### 1. 청크 = 짧은 트랜잭션 여러 개

```text
  한 문장 (1억 행)                         keyset 청크 (1000행 × 10만 번)
  BEGIN ──────────────────────── COMMIT    BEGIN─COMMIT  BEGIN─COMMIT  BEGIN─COMMIT …
  락·undo·복제 이벤트가 끝까지 쌓임          청크마다 락이 풀리고, 복제는 조금씩 흐른다
                                           청크 사이에 쉼·지연 확인이 들어갈 자리가 있다
```

- PostgreSQL 17 UPDATE 문서가 직접 말한다. 많은 행을 바꾸는 UPDATE는 **테이블 bloat, 레플리카 지연, 락 경합**을 부른다. 작은 배치로 나누고 배치 사이에 VACUUM을 돌리는 것이 맞을 수 있다.
- PostgreSQL의 UPDATE·DELETE에는 `LIMIT`이 없다. 문서는 CTE로 `ctid`를 골라 자기 조인하는 방법을 보여 준다. MySQL의 단일 테이블 UPDATE·DELETE에는 MySQL 고유의 `LIMIT row_count`가 있다(MySQL 8.4 DELETE 문서: 영향 행 수가 LIMIT보다 작아질 때까지 반복하라).
- 로컬 재현(예시, MySQL 8.4.10): 20만 행 `UPDATE big SET v = v + 1`을 커밋하지 않은 채 두자, 다른 세션의 한 행 UPDATE가 `ERROR 1205 (HY000): Lock wait timeout exceeded; try restarting transaction`으로 실패했다(세션 `innodb_lock_wait_timeout = 2`, 전역 기본값은 50초).

### 2. OFFSET 청크는 조용히 행을 건너뛴다

```text
  목표: v2 IS NULL 인 10,000행을 1000개씩
  청크 k: WHERE v2 IS NULL ORDER BY id LIMIT 1000 OFFSET k*1000

  k=0  남은 대상 [1 ……………………………… 10000]   앞 1000개(1~1000) 처리 → 대상에서 빠짐
  k=1  남은 대상 [1001 ………………………… 10000]  OFFSET 1000 → 2001~3000 처리 (1001~2000 건너뜀!)
  k=2  남은 대상 [1001~2000, 3001~10000]      OFFSET 2000 → 4001~5000 처리 (3001~4000 건너뜀!)
  …
  k=5  남은 대상 5000행                        OFFSET 5000 → 0행
  결과: "10번 돌았다", 처리 5,000행, 남은 대상 5,000행 — 에러 없음
```

- 로컬 재현(예시, PostgreSQL 17.11): 위 잡이 `updated=5000`을 보고하고 끝났다. `v2 IS NULL`은 5,000행 남았다.
- 원인: 처리할수록 대상 집합이 줄어드는데, OFFSET은 "줄어든 집합의 몇 번째"를 센다.
- 반대 경우도 있다. 대상 조건이 그대로이고 처리 중에 앞쪽에 행이 끼어들면 OFFSET이 밀려 **같은 행을 두 번** 처리한다.
- OFFSET은 앞의 행을 매번 읽고 버리므로 청크가 뒤로 갈수록 느려지기도 한다.

### 3. keyset 청크 — 마지막 키에서 이어 간다

```text
  last_id = 0
  loop:
    청크 = SELECT id … WHERE id > last_id ORDER BY id LIMIT 1000     ← 인덱스 범위 스캔
    UPDATE … WHERE id > last_id AND id <= max(청크)
    last_id = max(청크)                                             ← 체크포인트
  청크가 비면 끝
```

- *keyset(seek) 페이지네이션*: 위치를 "몇 번째"가 아니라 "마지막으로 본 키"로 기억하는 방식.
- 키가 유일하고 정렬 가능하면(보통 PK) 대상 집합이 줄거나 늘어도 **키 구간은 겹치지도 빠지지도 않는다.**
  - 다만 커서가 이미 지나간 구간에서 **새로 대상이 된 행**(뒤늦은 INSERT, 앱이 값을 바꾼 행)은 다시 보지 않는다. 그 몫은 이중 쓰기와 끝의 재검사(적용 5)가 맡는다.
- 로컬 재현(예시): 같은 10,000행을 keyset으로 돌리자 10청크, 10,000행, 남은 NULL 0이었다.
- 처리 중 새로 들어오는 행은 이중 쓰기(앱이 새 컬럼도 채움)가 맡는다. 백필은 "과거 행"만 책임진다.

### 4. 재시작 — 체크포인트와 멱등

```text
  잘못된 재시작                              안전한 재시작
  won = won * 2  (현재 값을 변환)            won_v2 = won * 10  (원본 컬럼 → 대상 컬럼)
  5청크 후 죽음 → 처음부터 다시               + WHERE won_v2 IS DISTINCT FROM won * 10
  앞 5000행은 ×4, 뒤 5000행은 ×2             + 체크포인트 테이블(last_id)을 청크와 같은 트랜잭션에서 갱신
  (로컬 재현: 2000원 5000행, 4000원 5000행)    처음부터 다시 돌려도 바뀐 행 0 (로컬 재현)
```

- *멱등*: 여러 번 실행해도 한 번과 같은 결과. 현재 값을 **자기 자신으로** 변환하는 UPDATE(`x = x * 2`, `x = x + 1`)는 멱등이 아니다.
- 멱등하게 만드는 법: 원본을 남기고 **다른 컬럼**에 쓰기, 또는 "이미 바뀐 행은 제외" 조건.
- 체크포인트를 청크 UPDATE와 **같은 트랜잭션**에 쓰면 "바꿨는데 기록 못 함"이나 "기록했는데 안 바꿈"이 생기지 않는다.

### 5. 스로틀 — 지표를 보고 쉰다

```text
  청크 실행 ──> 지연 측정 ──> 기준 넘음? ──예──> 멈춤(대기) ──┐
      ^                        │ 아니오                     │
      └──────── (선택) 청크 시간 × 비율만큼 쉼 <──────────────┘
```

- gh-ost 문서
  - `--chunk-size`: 한 번에 복사하는 행 수. 기본 1000, 허용 범위 10~100000.
  - `--max-lag-millis`: 복제 지연이 이 값을 넘으면 복사를 멈춘다. 지연은 gh-ost가 changelog 테이블에 심은 heartbeat로 잰다.
  - `--nice-ratio`: 청크마다 복사에 걸린 시간에 비례해 쉰다. 1이면 1ms 복사당 1ms 쉰다.
  - `--max-load`·`--critical-load`: 상태 지표 임계값. 앞의 것은 멈춤, 뒤의 것은 기본이 즉시 중단이다. `--critical-load-hibernate-seconds`를 주면 중단 대신 그 시간만큼 쉬었다 재개하고, `--critical-load-interval-millis`를 주면 한 번 더 확인한 뒤 중단한다.
- PostgreSQL에서는 `pg_stat_replication.replay_lag`가 비동기 레플리카에서 "최근 트랜잭션이 쿼리에 보이기까지의 지연"을 근사한다(27.2 The Cumulative Statistics System).
- MySQL에서는 `SHOW REPLICA STATUS`의 `Seconds_Behind_Source`를 본다.

### 6. 지우기의 뒤끝 — PostgreSQL bloat, InnoDB purge

```text
  PostgreSQL 17 (로컬 재현, 20만 행, 자동 VACUUM 끔)
  적재 직후        28 MB
  전 행 UPDATE     57 MB     ← 옛 버전 20만 개가 dead tuple로 남음
  VACUUM          57 MB     ← 자리만 재사용 가능 표시, 파일은 그대로
  절반 DELETE      57 MB
  VACUUM          57 MB
```

- PostgreSQL은 UPDATE·DELETE한 행의 옛 버전을 그 자리에 남긴다. 표준 VACUUM은 그 공간을 재사용 가능하게 할 뿐, 테이블 끝의 빈 페이지 외에는 OS에 돌려주지 않는다. VACUUM FULL은 공간을 돌려주지만 ACCESS EXCLUSIVE 락을 잡는다(24.1 Routine Vacuuming).
- InnoDB는 삭제·변경의 옛 버전을 undo 로그에 둔다. 그 undo는 **그것이 필요한 스냅샷이 모두 끝나야** 지울 수 있다. 문서는 읽기 전용 트랜잭션도 주기적으로 커밋하라고 권한다(MySQL 8.4 17.3 Multi-Versioning).
- 큰 DELETE는 "지웠다"가 끝이 아니다. 뒤따르는 VACUUM·purge의 I/O와 공간까지가 작업이다. 시간 단위로 지울 데이터면 처음부터 파티션을 나눠 DROP한다([44-timeseries-resolution-tiers](../44-timeseries-resolution-tiers/2-summary.md)).

## 쓰이는 자료구조·알고리즘

- **keyset 범위 스캔** — B+트리 인덱스에서 `id > last_id`의 첫 잎을 찾고 옆으로 1000개를 읽는다. 청크마다 O(log n + 청크). OFFSET은 건너뛸 행을 매번 읽는다. [data-structure/15-b-tree](../../data-structure/15-b-tree/2-summary.md)
- **체크포인트 커서** — `(job, last_id, done_rows)` 한 행. 커서 전진과 청크 변경을 한 트랜잭션에 묶는다. 배치 잡의 재시작 일반은 [reliability/31-batch-job-restart-and-checkpoint](../../reliability/31-batch-job-restart-and-checkpoint/2-summary.md).
- **멱등 변환** — "원본 → 다른 컬럼" 함수이거나, "이미 목표 상태인 행 제외" 조건. reliability `13-idempotency`(원고: [ops-patterns/06-idempotency-store](../../ops-patterns/06-idempotency-store/2-summary.md))의 키 기반 멱등과 같은 목표다.
- **피드백 스로틀** — 지연이 임계값을 넘으면 멈추고, 내려오면 재개하는 제어 루프. [ops-patterns/05-backpressure](../../ops-patterns/05-backpressure/2-summary.md)
- **MVCC 버전 체인** — 옛 버전이 남는 이유(PostgreSQL 힙 튜플, InnoDB undo). [16-mvcc](../16-mvcc/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 계획 — 시작 전에 적는다

```text
  대상 조건 · 예상 행 수 (SELECT count(*) …)
  변환이 멱등인가? 아니면 대상 컬럼·제외 조건으로 멱등하게
  청크 크기 · 청크당 목표 시간(예: < 1초) · 쉼 비율
  멈춤 기준: 복제 지연 · 락 대기 · CPU
  검증 쿼리: 전후 행 수, 남은 대상 0, 샘플 대조
  되돌리기: 원본 컬럼을 남기나? 백업·스냅샷은?
```

### 2. PostgreSQL 17 — 체크포인트 한 트랜잭션

```sql
CREATE TABLE backfill_ckpt (job text PRIMARY KEY, last_id bigint NOT NULL, done_rows bigint NOT NULL DEFAULT 0, updated_at timestamptz);

-- 청크 하나 (잡이 이 문장을 반복 호출한다. 한 번 = 한 트랜잭션)
SET lock_timeout = '2s';                                     -- 운영 요청과 부딪히면 이 청크만 포기
WITH ck AS (SELECT last_id FROM backfill_ckpt WHERE job = 'won_v2' FOR UPDATE),
     c  AS (SELECT id FROM price, ck WHERE id > ck.last_id ORDER BY id LIMIT 1000),
     u  AS (UPDATE price p SET won_v2 = p.won * 10 FROM c
             WHERE p.id = c.id AND p.won_v2 IS DISTINCT FROM p.won * 10 RETURNING p.id)
UPDATE backfill_ckpt
   SET last_id = COALESCE((SELECT max(id) FROM c), last_id),
       done_rows = done_rows + (SELECT count(*) FROM u), updated_at = now()
 WHERE job = 'won_v2'
RETURNING last_id, done_rows;
```

- 로컬 재현(예시): 10,000행이 10청크로 끝났다. 체크포인트를 0으로 되돌려 다시 돌리자 `done_rows = 0`(바뀐 행 없음), 잘못된 값 0이었다.
- `lock_timeout`의 기본값은 0(끔)이다(19.11). 청크 단위로 짧게 걸어 두면 잡이 운영 트래픽 뒤에 오래 줄 서지 않는다.

### 3. MySQL 8.4 — 같은 모양

```sql
-- 범위로 청크를 잡는다 (PK 순)
START TRANSACTION;                                             -- autocommit 기본 ON이라 명시해야 한 트랜잭션
SELECT MAX(id) INTO @hi FROM (SELECT id FROM price WHERE id > @lo ORDER BY id LIMIT 1000) c;
UPDATE price SET won_v2 = won * 10 WHERE id > @lo AND id <= @hi AND NOT (won_v2 <=> won * 10);  -- <=> = NULL 안전 비교
UPDATE backfill_ckpt SET last_id = @hi WHERE job = 'won_v2';
COMMIT;
-- 지우기는 DELETE … ORDER BY id LIMIT 1000 을 영향 행 수가 1000보다 작아질 때까지 반복
```

- 로컬 재현(예시, MySQL 8.4.10): `won`이 NULL이고 `won_v2 = 5`인 행은 `won_v2 <> won * 10`으로는 걸러지지 않는다(비교 결과가 NULL). `NOT (won_v2 <=> won * 10)`은 이 행을 NULL로 고쳤다.

### 4. 지켜보는 것

```sql
-- PostgreSQL: 레플리카 지연 · 락 대기 · bloat
SELECT application_name, replay_lag FROM pg_stat_replication;
SELECT pid, wait_event_type, wait_event, now() - xact_start AS xact_age, query
  FROM pg_stat_activity WHERE state <> 'idle' ORDER BY xact_age DESC;
SELECT relname, n_live_tup, n_dead_tup, last_autovacuum FROM pg_stat_user_tables WHERE relname = 'price';
-- MySQL
SHOW REPLICA STATUS\G                          -- Seconds_Behind_Source
SHOW ENGINE INNODB STATUS\G                    -- TRANSACTIONS 절의 History list length
SELECT * FROM performance_schema.data_lock_waits;
```

### 5. 끝났다고 말하기 전에 — 전후 검증

```sql
SELECT count(*) FILTER (WHERE won_v2 IS NULL)         AS missing,
       count(*) FILTER (WHERE won_v2 IS DISTINCT FROM won * 10) AS wrong,   -- <> 는 won이 NULL인 행을 놓친다
       count(*)                                        AS total
  FROM price;                                           -- 로컬 재현: 0 / 0 / 10000
```

- "잡이 에러 없이 끝났다"는 완료가 아니다. OFFSET 잡은 에러 없이 절반만 처리했다(동작·원리 2절).
- 잡이 보고한 처리 수와 **대상 조건으로 다시 센 수**를 대조한다. 샘플 몇 행은 원본과 손으로 비교한다.

## 장애 시나리오와 대처

### 1. 단일 UPDATE 1억 행 → 락·undo 폭증·복제 지연

- **현상**: 백필을 돌리자 주문 API의 쓰기가 줄줄이 실패한다. 조회는 레플리카에서 오래된 값을 돌려준다.
- **보이는 형태**
  - MySQL: `ERROR 1205 (HY000): Lock wait timeout exceeded; try restarting transaction`(로컬 재현). `Seconds_Behind_Source`가 커밋 직후 급등.
  - PostgreSQL: `pg_stat_activity`에 `wait_event_type = Lock`인 세션이 쌓인다. `replay_lag` 증가. 테이블 크기가 두 배 가까이 된다(로컬 재현 28 MB → 57 MB).
- **원인**
  - 한 트랜잭션이 바꾼 행 전부의 락을 커밋까지 쥔다.
  - 옛 버전(undo·dead tuple)이 한꺼번에 생긴다.
  - MySQL은 트랜잭션을 binlog 캐시에 모았다가 커밋할 때 binlog에 쓴다(`binlog_cache_size` 문서). 그래서 레플리카는 커밋 뒤에야 거대한 트랜잭션을 받아 적용한다.
- **대처**
  - 긴급: 잡을 멈춘다(KILL). 롤백도 바꾼 만큼 오래 걸린다는 점을 감안한다.
  - 근본: keyset 청크 + 청크당 짧은 트랜잭션 + 지연 기반 스로틀로 다시 짠다.

### 2. OFFSET 청크 → 행 누락이 에러 없이 끝남

- **현상**: 백필 잡은 "완료"인데 일부 사용자 화면에 새 컬럼 값이 비어 있다.
- **보이는 형태**: 잡 로그 `updated=5000` 정상 종료. 검증 쿼리 `missing = 5000`(로컬 재현).
- **원인**: 처리하면 대상에서 빠지는 조건(`v2 IS NULL`) 위에 OFFSET을 올렸다. 청크마다 앞쪽 대상을 건너뛴다. 조건이 그대로면 반대로 중복 처리가 생긴다.
- **대처**: keyset(`id > last_id`)으로 바꾼다. 남은 대상은 멱등 잡으로 다시 돌리면 채워진다. 잡 끝에 대상 조건 재계수를 넣어 0이 아니면 실패로 끝낸다.

### 3. 중단 후 재실행 → 이미 처리한 행을 다시 변환

- **현상**: 백필이 중간에 죽어 다시 돌렸더니 앞쪽 고객의 금액만 두 배로 올랐다.
- **보이는 형태**: 값 분포가 둘로 갈린다. 로컬 재현 2000원 5000행 / 4000원 5000행.
- **원인**: 변환이 비멱등이다(`won = won * 2`). 체크포인트 없이 처음부터 다시 돌렸다.
- **대처**
  - 복구: 원본(백업·변경 이력·원본 컬럼)에서 해당 범위를 다시 계산한다. 원본을 덮어썼다면 복구 근거부터 찾는다.
  - 예방: 결과를 다른 컬럼에 쓰거나 "이미 목표 상태" 행을 제외한다. 체크포인트를 청크와 같은 트랜잭션에 쓴다.

### 4. PostgreSQL 대량 DELETE → bloat, 디스크가 안 준다

- **현상**: 오래된 로그 행 절반을 지웠는데 디스크 사용량이 그대로다. 오히려 WAL과 백업이 커졌다.
- **보이는 형태**: `n_dead_tup` 급증, `pg_relation_size` 변화 없음(로컬 재현 57 MB 유지). autovacuum이 그 테이블에서 오래 돈다.
- **원인**: DELETE는 dead tuple을 남긴다. 표준 VACUUM은 공간을 OS에 돌려주지 않는다(24.1). 지우는 동안 열린 긴 트랜잭션이 있으면 VACUUM이 그 행을 치우지도 못한다.
- **대처**
  - 청크 사이에 VACUUM을 돌린다(UPDATE 문서의 권고).
  - 공간 회수가 꼭 필요하면 VACUUM FULL(ACCESS EXCLUSIVE 락) 대신 온라인 재구성 도구(확장 `pg_repack` — 처리 중에는 배타 락을 쥐지 않고 시작·끝에만 짧게 잡는다)를 검토한다.
  - 앞으로 시간 기준으로 지울 데이터는 파티션으로 나눠 DROP한다.

### 5. 긴 스냅샷이 purge를 막는다 (MySQL)

- **현상**: 청크로 잘 나눴는데도 InnoDB undo 공간이 계속 커지고 읽기가 느려진다.
- **보이는 형태**: `SHOW ENGINE INNODB STATUS`의 `History list length`가 계속 증가. `information_schema.innodb_trx`에 몇 시간 된 트랜잭션.
- **원인**: 어딘가 열린 채인 긴 트랜잭션(리포트·백업·잊힌 세션)이 옛 스냅샷을 쥐고 있다. 그 스냅샷이 필요로 하는 undo는 지울 수 없다(17.3).
- **대처**: 긴 트랜잭션을 찾아 끝낸다. 백필 중에는 history list length를 멈춤 기준 지표에 넣는다.

## 핵심 문장

- 큰 DML 한 문장은 락·옛 버전·복제 이벤트를 한 트랜잭션에 쌓는다. 짧은 트랜잭션 여러 개로 나눈다.
- 청크 위치는 OFFSET이 아니라 마지막 키(keyset)로 기억한다. OFFSET은 대상이 줄면 건너뛰고 늘면 중복하며, 에러 없이 끝난다.
- 재시작은 체크포인트(같은 트랜잭션에서 갱신)와 멱등 변환 둘 다 있어야 안전하다.
- 스로틀은 복제 지연·락 대기 같은 지표를 보고 멈추는 피드백 루프다(gh-ost `--max-lag-millis`).
- 끝났다는 증거는 잡 로그가 아니라 대상 조건으로 다시 센 0과 전후 행 수 대조다.
- 지운 뒤에도 PostgreSQL bloat·InnoDB purge가 남는다. 시간으로 지울 데이터는 파티션으로 설계한다.

## 관련 주제·근거

- 선행
  - [26-schema-migration](../26-schema-migration/2-summary.md) — expand/contract의 백필 단계. 원고: [systems/server-design/08-deployment-ops.md](../../systems/server-design/08-deployment-ops.md) §2
  - [32-replication-leader-follower](../32-replication-leader-follower/2-summary.md) — 복제 지연. 원고: [systems/server-design/03-data-layer.md](../../systems/server-design/03-data-layer.md) §1
  - [16-mvcc](../16-mvcc/2-summary.md) — 옛 버전·vacuum·purge
- 후속·연결
  - [35-bulk-file-import-export](../35-bulk-file-import-export/2-summary.md) — 파일에서 대량 적재
  - [44-timeseries-resolution-tiers](../44-timeseries-resolution-tiers/2-summary.md) — 파티션 DROP 보존, 멱등 롤업
  - [reliability/31-batch-job-restart-and-checkpoint](../../reliability/31-batch-job-restart-and-checkpoint/2-summary.md) — 배치 잡 재시작 일반.
  - data-engineering `08-idempotent-pipelines-and-backfill` — 파티션 덮어쓰기 백필. 미작성, [data-engineering/README](../../data-engineering/README.md)
- 문서·자료
  - PostgreSQL 17 UPDATE — 대량 UPDATE의 bloat·레플리카 지연·락 경합, 배치 권고, `LIMIT` 없음과 `ctid` CTE 예 <https://www.postgresql.org/docs/17/sql-update.html>
  - PostgreSQL 17 24.1 Routine Vacuuming · 27.2 `pg_stat_replication`(`replay_lag`) · 19.11 `lock_timeout` <https://www.postgresql.org/docs/17/routine-vacuuming.html>
  - MySQL 8.4 15.2.2 DELETE(`LIMIT row_count` 반복) · 15.2.17 UPDATE · 17.3 InnoDB Multi-Versioning(undo와 긴 트랜잭션) · 17.8.9 Purge Configuration(History list length) · `binlog_cache_size` · `innodb_lock_wait_timeout`(기본 50) <https://dev.mysql.com/doc/refman/8.4/en/delete.html>
  - Stripe, "Online migrations at scale"(2017) — 이중 쓰기(백필 포함)·읽기 경로 전환·쓰기 경로 전환·옛 데이터 제거 4단계, 스냅샷에서 대상 찾기 <https://stripe.com/blog/online-migrations>
  - pg_repack 문서 — VACUUM FULL과 달리 처리 중 배타 락 없이 bloat 제거 <https://github.com/reorg/pg_repack/blob/master/doc/pg_repack.rst>
  - gh-ost `doc/command-line-flags.md` — `chunk-size`(기본 1000), `max-lag-millis`(heartbeat), `nice-ratio`, `max-load`·`critical-load`(기본 중단, `critical-load-hibernate-seconds`·`critical-load-interval-millis`) <https://github.com/github/gh-ost>
- 로컬 재현(PostgreSQL 17.11 / MySQL 8.4.10, DB `w31`): OFFSET 청크 누락(보고 5000, 남은 5000), keyset 청크 완주, 비멱등 재실행(×2/×4 분포), 체크포인트+멱등 청크의 재실행 0건, 전 행 UPDATE·절반 DELETE 뒤 크기(28 → 57 MB, VACUUM 후 유지), MySQL 미커밋 대량 UPDATE에 막힌 한 행 UPDATE의 1205, MySQL 청크의 `START TRANSACTION`·`<=>` NULL 안전 비교(판정 단계, DB `fa24`), 전역 `innodb_lock_wait_timeout = 50`·`binlog_format = ROW`
