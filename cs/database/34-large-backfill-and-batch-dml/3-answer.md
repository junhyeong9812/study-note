# database/34-large-backfill-and-batch-dml — 정답

## 정답

### 1. 한 문장 1억 행

| 측면 | 생기는 일 |
|---|---|
| 락 | 바꾼 행 전부를 커밋까지 쥔다. 같은 행을 쓰려는 요청이 대기하다 타임아웃(MySQL 1205) |
| 옛 버전 | InnoDB는 undo, PostgreSQL은 dead tuple이 한꺼번에 생긴다. 테이블·undo가 커진다 |
| 복제 | 레플리카가 거대한 변경을 한 번에 적용해야 한다. 지연이 급등한다(MySQL은 커밋 때 binlog에 몰아 써서 보낸다. PostgreSQL은 WAL을 생기는 대로 보내지만 커밋 재생 전엔 조회에 안 보인다) |
| 실패 | 중간에 죽으면 전부 롤백된다. 롤백도 바꾼 만큼 걸린다 |

- PostgreSQL 17 UPDATE 문서도 bloat·레플리카 지연·락 경합을 들며 작은 배치를 권한다.

### 2. OFFSET 청크

- 보고: `updated=5000`. 남은 `v2 IS NULL` **5,000행**. 에러는 없다(로컬 재현).
- 이유: 처리한 행이 대상에서 빠진다. 대상이 줄었는데 OFFSET은 계속 k×1000을 건너뛴다. 청크마다 앞쪽 1000개를 건너뛰고, k=5부터는 0행이다.
- 조건이 그대로인 UPDATE라면, 처리 도중 앞쪽에 행이 끼어들 때 OFFSET이 밀려 **같은 행을 두 번** 처리할 수 있다.

### 3. keyset 한 반복

```sql
SELECT max(id) INTO hi FROM (SELECT id FROM t WHERE id > :last ORDER BY id LIMIT 1000) c;
UPDATE t SET … WHERE id > :last AND id <= hi;
-- :last = hi 로 전진, 청크가 비면 끝
```

- 위치를 "몇 번째"가 아니라 **마지막 키**로 기억한다. 키가 유일·정렬 가능하면 범위 `(last, hi]`는 겹치지도 빠지지도 않는다. 대상 집합이 줄어도 상관없다(로컬 재현: 10청크, 남은 0). 단 커서가 지나간 구간에서 새로 대상이 된 행은 다시 보지 않는다(이중 쓰기·끝의 재검사 몫).
- 인덱스 범위 스캔이라 청크 비용이 뒤로 가도 일정하다.
- 새로 들어오는 행은 **이중 쓰기**(앱이 새 컬럼도 채움)가 맡는다. 백필은 과거 행만 책임진다.

### 4. 비멱등 재실행

- 앞 5,000행은 두 번 변환돼 ×4, 뒤 5,000행은 ×2다(로컬 재현: 2000원 5000행, 4000원 5000행).
- 필요한 두 가지
  - **멱등 변환**: 결과를 다른 컬럼에 쓴다(`won_v2 = won * 10`). 또는 "이미 목표 상태" 행을 제외한다(`IS DISTINCT FROM`).
  - **체크포인트**: 어디까지 했는지(`last_id`)를 남기고 거기서 이어 간다.
- 둘을 갖춘 잡은 체크포인트를 0으로 되돌려 다시 돌려도 바뀐 행이 0이었다(로컬 재현).

### 5. 체크포인트와 청크를 한 트랜잭션에

- 같이 커밋되거나 같이 롤백된다. 그래서 "청크를 바꿨다"와 "기록했다"가 항상 일치한다.
- 따로 커밋할 때의 어긋남
  - 청크 커밋 후 체크포인트 전에 죽음 → 재시작 시 그 청크를 다시 처리한다. 비멱등이면 이중 변환이다.
  - 체크포인트 먼저 커밋 후 청크 전에 죽음 → 그 청크를 건너뛴다. 조용한 누락이다.

### 6. 스로틀 기준

- gh-ost: `--max-lag-millis`를 넘는 복제 지연이면 복사를 멈춘다. 지연은 gh-ost가 changelog 테이블에 심은 **heartbeat**로 잰다. `SHOW SLAVE STATUS`가 필요 없다(gh-ost 문서).
  - 그 밖에 `--max-load`(멈춤)·`--critical-load`(기본은 중단, `--critical-load-hibernate-seconds`면 휴면 후 재개)·`--nice-ratio`(청크 시간 비례 휴식)·`--chunk-size`(기본 1000)가 있다.
- PostgreSQL: `pg_stat_replication.replay_lag`. 비동기 레플리카에서 최근 트랜잭션이 쿼리에 보이기까지의 지연을 근사한다.
- MySQL: `SHOW REPLICA STATUS`의 `Seconds_Behind_Source`.

### 7. DELETE 뒤 디스크 그대로

- DELETE는 dead tuple을 남긴다. 표준 VACUUM은 그 자리를 재사용 가능하게 표시할 뿐이다. 테이블 끝의 완전히 빈 페이지 외에는 OS에 돌려주지 않는다(PostgreSQL 17 24.1).
  - 로컬 재현: 전 행 UPDATE로 28 → 57 MB, 절반 DELETE + VACUUM 뒤에도 57 MB.
- 돌려받기: `VACUUM FULL`. 대가는 ACCESS EXCLUSIVE 락이다. 그동안 테이블을 읽지도 쓰지도 못한다.
- 피하는 설계: 시간 기준으로 지울 데이터는 범위 파티션으로 나눠 `DROP`한다. 청크 DELETE라면 청크 사이에 VACUUM을 돌려 공간을 재사용시킨다.

### 8. 1205 폭주

- 백필 트랜잭션이 많은 행의 락을 오래 쥐고 있다. 주문 API의 행 UPDATE가 그 락을 `innodb_lock_wait_timeout`(8.4 기본 50초) 동안 기다리다 실패한다(로컬 재현: 미커밋 20만 행 UPDATE에 막힌 한 행 UPDATE가 1205).
- 긴급: 백필 세션을 멈춘다(KILL). 롤백 시간을 감안한다.
- 근본: 청크를 작게 하고(청크당 < 1초 목표) 청크마다 커밋한다. 락 대기·지연을 보고 멈추게 한다.
- PostgreSQL 백필 세션에는 `SET lock_timeout = '2s'` 같은 짧은 값을 건다. 기본 0은 끔이다(19.11). 운영 요청과 부딪히면 백필 청크가 먼저 포기하고 나중에 다시 시도한다.

### 9. "에러 없이 완료"의 함정

- OFFSET 잡처럼 **에러 없이 절반만** 처리할 수 있다. 부분 실패를 건너뛰고 성공으로 끝낼 수도 있다.
- 증명
  - 대상 조건으로 다시 센 수가 0이다(`missing = 0`).
  - 변환이 맞다(`wrong = 0`, NULL까지 잡도록 `won_v2 IS DISTINCT FROM won * 10`으로 센다).
  - 전후 전체 행 수가 같다(지우기면 기대한 만큼 줄었다).
  - 잡이 보고한 처리 수와 대조한다. 샘플 몇 행은 원본과 손으로 비교한다.

### 10. History list length 증가

- 의심: 어딘가 **오래 열린 트랜잭션**(리포트·백업·잊힌 세션)이 옛 스냅샷을 쥐고 있다. 그 스냅샷이 필요로 하는 undo는 purge할 수 없다(MySQL 8.4 17.3).
- 찾기
  - `SELECT trx_id, trx_started, trx_mysql_thread_id, trx_query FROM information_schema.innodb_trx ORDER BY trx_started;`
  - `SHOW ENGINE INNODB STATUS`의 TRANSACTIONS 절
- 대처: 그 트랜잭션을 끝낸다. 백필의 멈춤 기준에 history list length를 넣는다.
