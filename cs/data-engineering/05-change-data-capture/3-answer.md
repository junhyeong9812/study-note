# data-engineering/05-change-data-capture — 정답

## 정답

### 1. 폴링이 놓치는 것

- 놓치는 것
  - DELETE: 지운 행은 `WHERE updated_at > ...`에 걸리지 않는다. 파생본에 남는다.
  - 주기 안의 중간 변경: 5분 안에 두 번 바뀌면 마지막 값만 보인다.
  - `updated_at`을 갱신하지 않는 경로(배치 UPDATE, 수동 SQL)의 변경.
  - 그리고 매 주기 원천에 질의 부하를 준다.
- 로그 기반 CDC는 DB가 이미 쓰는 WAL·binlog를 읽는다. 커밋된 변경이 삭제까지 커밋 순서대로 나오고, 별도 컬럼이 필요 없다(Debezium Features, 실험 A).
- 남는 일: 초기 스냅샷 경계, 슬롯·binlog 보존, DDL, 장애 뒤 중복은 CDC가 새로 가져오는 문제다.

### 2. 흐름과 슬롯의 두 위치

```text
  커밋 → WAL(LSN 증가) → 논리 디코딩 + 출력 플러그인 → 복제 슬롯 → 커넥터 → 토픽(key=PK)
                                                         │
                     restart_lsn ──────────────── confirmed_flush_lsn ──── 현재 LSN
                     (다시 시작에 필요한 가장 오래된 WAL)  (소비자가 받았다고 확인한 곳)
```

- `confirmed_flush_lsn`: 소비자가 "여기까지 받았다"고 확인한 위치. 다음 전송은 이 뒤부터다.
- `restart_lsn`: 디코딩을 다시 시작할 때 필요한 가장 오래된 WAL 위치. 이 뒤의 WAL은 체크포인트가 지우지 못한다.
- 실험 D(C3): advance 직후 `confirmed_flush_lsn`은 `0/D91E148`인데 `restart_lsn`은 `0/7722AA0`에 남아 98 MB를 붙잡았다. 체크포인트 뒤 다시 advance하자 따라붙었다.

### 3. `test_decoding` 출력 예측

- DEFAULT(실험 A)
  - `UPDATE`: 새 행만 나온다(`UPDATE: id[integer]:1 name[text]:'user_001' tier[text]:'gold'`). 이전 값은 없다.
  - `DELETE`: 기본 키만 나온다(`DELETE: id[integer]:2`).
  - 롤백한 `INSERT`: 나오지 않는다. 커밋된 트랜잭션만 나온다.
  - `ADD COLUMN`: DDL 자체는 나오지 않는다. 빈 `BEGIN … COMMIT`만 보였고, 다음 INSERT에 `region[text]:'KR'`이 새로 나타났다.
- FULL
  - UPDATE가 `old-key: …(이전 행 전체) new-tuple: …`로 나온다.
  - DELETE가 지운 행 전체를 담는다.
  - 대가: UPDATE·DELETE마다 이전 행 전체를 WAL에 쓴다.

### 4. 스냅샷·슬롯 순서

- B1(스냅샷 먼저): 스냅샷 `1~5`, 스트림 `7`. `6`은 어디에도 없다 → **누락**.
- B2(슬롯 먼저): 스냅샷 `1~6`, 스트림 `6, 7`. `6`이 두 번 → **중복**.
- 실험 B의 출력이 그대로다.
- 둘 다 피하는 법
  - 복제 연결에서 `CREATE_REPLICATION_SLOT … LOGICAL test_decoding EXPORT_SNAPSHOT`으로 슬롯을 만들고, 받은 스냅샷 이름을 `SET TRANSACTION SNAPSHOT`으로 써서 덤프한다(B3: 스냅샷 `1~5`, 스트림 `6, 7`). PostgreSQL 17 문서 47.2.5.
  - 그래도 하류는 PK upsert로 만든다. 장애 뒤 재전송까지 흡수한다.

### 5. 증분 스냅샷의 창과 버퍼

- 청크를 읽는 쿼리와 동시에 다른 트랜잭션이 같은 행을 바꿀 수 있다. 쿼리 결과와 로그 이벤트의 순서를 정확히 알 수 없다.
- 그래서 청크 쿼리 앞뒤로 창 열기·닫기 신호를 로그에 남긴다. 창 안에서 로그에 나온 키는 스냅샷 버퍼에서 버리고 로그 이벤트만 내보낸다. 창이 닫히면 버퍼에 남은 행을 read 이벤트로 낸다. 옛 스냅샷 값이 새 변경을 덮어쓰는 것을 막는다(Debezium 블로그 2021-10-07).
- 소비자가 각오할 것(블로그 "Limitations")
  - read 이벤트는 "초기 상태"가 아니라 "임의 시점의 상태"다.
  - read와 update의 순서가 뒤바뀌어 올 수 있다. 본 적 없는 키의 delete가 올 수 있다.
  - PK가 있어야 하고, at-least-once는 그대로다.

### 6. 비활성 슬롯과 상한

- 상한 없음(실험 D): 슬롯이 없을 때 48 MB이던 `pg_wal`이 45만 행(약 147 MB WAL) 뒤 160 MB가 됐다. `wal_status=extended`, `retained` 147 MB.
- `max_slot_wal_keep_size=32MB`(실험 E): 약 10 MB 뒤에는 `reserved`, `safe_wal_size` 29 MB. 약 50 MB 더 쓰고 체크포인트하자 `wal_status=lost`, `invalidation_reason=wal_removed`. `pg_wal`은 48 MB에 머물렀다.
  - 이후 `pg_logical_slot_get_changes`는 `can no longer get changes from replication slot "cdc_capped"`로 실패했다.
- 정리: 상한이 없으면 디스크를, 상한이 있으면 슬롯을 잃는다.

### 7. PostgreSQL 슬롯 vs MySQL binlog

- PostgreSQL: 슬롯이 `restart_lsn` 이후 WAL을 붙잡는다. 커넥터가 오래 멈추면 **디스크가 찬다**. 상한을 두면 슬롯이 `lost`가 된다.
- MySQL 8.4: binlog는 `binlog_expire_logs_seconds`(기본 30일)가 지나면 서버 시작·binlog flush 때 자동 삭제될 수 있다(`binlog_expire_logs_auto_purge=OFF`면 자동 삭제 없음). 커넥터가 그보다 오래 멈춰 저장한 위치의 파일이 지워지면 **이어 받을 수 없다**(Debezium MySQL 문서).
- 공통 복구: **재스냅샷**. 증분 스냅샷은 스트리밍과 함께 도는 기능이므로, 먼저 현재 위치에서 스트리밍을 다시 세운 뒤(새 슬롯, Debezium MySQL은 오프셋을 지우고 `no_data`) 큰 테이블을 나눠 읽는다. 멈춘 사이 지워진 키는 스냅샷에 나오지 않으니 하류에서 키 대조로 따로 지운다. 예방은 커넥터 지연 알람과 보존·상한 설정이다.

### 8. 하류 행 수가 계속 많다

- 원인 후보
  - 삭제를 반영하지 않는다: 소비자가 `op=d`·tombstone을 무시하거나, null 값 역직렬화 실패를 건너뛴다. 차이가 탈퇴 수만큼 시간에 따라 커지는 모양과 맞는다.
  - 덧붙이기 적재: 하류가 PK upsert 대신 INSERT만 한다. 경계 중복·장애 뒤 재전송·UPDATE마다 행이 는다.
- 확인
  - 하류에서 `SELECT id, count(*) … GROUP BY id HAVING count(*) > 1` → 중복이 있으면 덧붙이기.
  - 원천에 없는 하류 키: 원천 키 목록과 anti-join → 있으면 삭제 미반영.
  - 실험 C: 원천 6행·650이 방식 A에서 9행·950이 됐다.
- 해석: 둘 다 에러 없이 진행되므로 대조 지표로만 보인다.

### 9. 디스크 경보 → 슬롯 점검

```sql
SELECT slot_name, active, inactive_since, wal_status,
       pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS retained,
       pg_size_pretty(safe_wal_size) AS safe_wal_size
FROM pg_replication_slots;
SELECT pg_size_pretty(sum(size)) FROM pg_ls_waldir();
```

- 버려진 슬롯의 모양: `active=f`, `inactive_since` 오래됨, `retained` 큼, `wal_status=extended`.
- 정리
  - 커넥터를 살릴 수 있으면 살려 따라잡게 한다.
  - 다시 쓰지 않으면 `SELECT pg_drop_replication_slot('이름')`. 그 슬롯을 쓰던 하류는 재스냅샷이 필요하다.
  - `pg_wal` 파일을 손으로 지우지 않는다([database/19 장애 2](../../database/19-wal-and-logging/2-summary.md)).
- 재발 방지: `max_slot_wal_keep_size` 상한(대가는 `lost`), `retained`·`safe_wal_size`·`inactive_since` 알람, 커넥터 해체 절차에 "슬롯 삭제" 포함.
