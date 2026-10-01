# database/32-replication-leader-follower — 리더-팔로워 복제: 동기·비동기, 복제 지연, 읽기 보장 — 정리 (힌트)

## 해결하는 문제

DB 서버가 한 대면 두 가지가 막힌다.
- 그 서버가 죽으면 서비스도 죽는다(가용성).
- 읽기가 한 서버의 CPU·I/O를 넘으면 더 늘릴 곳이 없다(읽기 확장).

기초 구조(리더 1 + 복제본 N, 동기/비동기/준동기 표, read-your-writes 해법 표)는 원본 [server-design/03-data-layer.md](../../systems/server-design/03-data-layer.md) §1 "읽기 확장 — 복제"에 있다.\
이 노트는 그 아래를 판다. **무엇이 흘러가나(복제 로그), 커밋은 언제 성공으로 치나, 지연은 어디서 생기고 어떻게 재나, 페일오버 때 무엇을 잃나.**

쉬운 예: 강의 필기를 친구들이 베껴 간다.
- 선생님(리더)만 칠판에 쓴다. 친구들(팔로워)은 칠판을 보고 **같은 순서로** 베낀다.
- 베끼는 속도가 늦으면, 방금 칠판에 쓴 내용이 친구 노트에는 아직 없다(복제 지연).
- 선생님이 쓰러져 친구 노트로 수업을 이어 가면, 마지막 몇 줄은 사라질 수 있다(비동기 페일오버 유실).

똑같은 구조다. 쓰기는 리더 하나만 받고, 팔로워는 리더의 **변경 로그를 같은 순서로 재생**한다.

실무 예
- 글을 쓰고 목록으로 돌아왔는데 내 글이 없다. 새로고침하면 생긴다.
- 페일오버 뒤 "결제 완료" 응답을 받은 주문이 새 리더에 없다.
- 복제본에서 긴 리포트 쿼리가 `ERROR: canceling statement due to conflict with recovery`로 죽는다.

## 동작·원리

### 1. 무엇이 흘러가나 — 복제 로그

```text
  PostgreSQL 17 (물리 스트리밍 복제)            MySQL 8.4 (binlog 복제)
  리더: WAL 레코드 생성                         리더: binlog 이벤트 기록(커밋 시)
    │  walsender ──TCP──▶ walreceiver           │  dump 스레드 ──▶ 수신(I/O) 스레드 → relay log
    ▼                     ▼                     ▼                          ▼
  pg_wal/               팔로워 pg_wal/ → 재생     binlog.00000N             applier(SQL) 스레드가 적용
  "어느 페이지 몇 번 칸을 이렇게"                  "이 행이 이렇게 바뀌었다"(ROW 형식)
```

- *물리 복제*: 페이지 수준의 변경(WAL)을 그대로 보낸다. 팔로워는 리더와 **블록 단위로 같은 데이터**를 갖게 된다. 같은 메이저 버전이어야 한다.
  - 완전히 바이트까지 같지는 않다. WAL에 남지 않는 힌트 비트는 팔로워가 따로 다시 쓰고(26.4), `UNLOGGED` 테이블 내용은 복제되지 않는다(CREATE TABLE 문서).
- *논리(행) 복제*: "어떤 행이 어떻게 바뀌었나"를 보낸다. MySQL binlog의 ROW 형식이 이쪽이다(DML 기준. `CREATE`·`ALTER`·`DROP TABLE` 같은 DDL은 ROW 형식에서도 문장으로 기록된다 — MySQL 8.4 "Setting The Binary Log Format"). PostgreSQL도 논리 복제가 따로 있다(29장).

로컬 재현(예시, MySQL 8.4.10, `binlog_format = ROW`, `binlog_row_image = FULL`): INSERT·UPDATE·DELETE가 binlog에 이렇게 남았다(`SHOW BINLOG EVENTS`).

```text
  Anonymous_Gtid  SET @@SESSION.GTID_NEXT= 'ANONYMOUS'     ← gtid_mode=OFF라 익명
  Query           BEGIN
  Table_map       table_id: 353 (w20.orders)
  Update_rows     table_id: 353 flags: STMT_END_F           ← SQL 원문이 아니라 행 이미지
  Xid             COMMIT /* xid=2322 */
```

- 복제본은 이 이벤트를 **같은 순서**로 적용한다. 순서가 곧 일관성이다.

로컬 재현(예시, PostgreSQL 17.11): 복제 로그는 곧 WAL이다. `UPDATE` 한 번이 `Heap … HOT_UPDATE … blkref #0: rel 1663/26425/26786 blk 0`처럼 "어느 파일 어느 블록"으로 기록된다. 이 레코드들이 그대로 팔로워로 스트리밍된다.

### 2. 커밋은 언제 성공인가 — 동기 수준

```text
  클라이언트          리더                           팔로워
     │ COMMIT ──▶  WAL 로컬 flush ─────────────▶  수신(write) → flush → 재생(apply)
     │                  │                          ▲          ▲         ▲
     │                  │  off: 로컬 flush도 안 기다림│          │         │
     │                  │  local / (비동기 on): 여기 │          │         │
     │                  │                remote_write┘          │         │
     │                  │                     on(동기) ──────────┘         │
     │                  │                  remote_apply ───────────────────┘
     │ ◀── 성공 ─────────┘ (선택한 지점까지 기다린 뒤)
```

- PostgreSQL 17의 스트리밍 복제는 **기본이 비동기**다. 리더가 죽으면 커밋된 트랜잭션 일부가 팔로워에 없을 수 있고, 유실량은 페일오버 시점의 복제 지연에 비례한다(26.2.8).
- 동기로 하려면 `synchronous_standby_names`에 팔로워를 적는다. 그때 `synchronous_commit`(기본 `on`)이 기다릴 지점을 정한다(19.5.1).
  - `remote_write`: 팔로워가 받아서 OS에 **썼다**는 응답. 팔로워 OS가 죽으면 잃을 수 있다.
  - `on`: 팔로워가 **디스크에 flush**했다는 응답. 리더와 모든 동기 팔로워의 저장소가 함께 망가지지 않는 한 잃지 않는다.
  - `remote_apply`: 팔로워가 **재생까지** 해서 조회에 보인다는 응답. 지연이 가장 크다.
  - `synchronous_standby_names`가 비어 있으면 `remote_*`·`local`은 모두 `on`(로컬 flush)과 같다.
- 동기 팔로워가 죽으면 그 팔로워를 기다리는 커밋은 **영원히 끝나지 않을 수 있다**. 그래서 문서는 후보를 여럿 적으라고 권한다(26.2.8 Planning for High Availability).
- MySQL 8.4도 **기본은 비동기**다. 리더가 죽으면 커밋한 트랜잭션이 어떤 복제본에도 없을 수 있다(19.4.10).
  - *준동기(semisynchronous)*: 커밋이 최소 1개 복제본의 "받아서 relay log에 쓰고 flush했다"는 응답을 기다린다. 플러그인을 양쪽에 설치해야 한다. 이 컨테이너에는 설치돼 있지 않아 `rpl_semi_sync_source_enabled`를 조회하면 `ERROR 1193 Unknown system variable`이었다(로컬 확인).
  - 기다리는 지점 `rpl_semi_sync_source_wait_point`의 기본은 `AFTER_SYNC`다. binlog를 sync한 뒤 응답을 기다리고, 받은 **뒤에** 스토리지 엔진에 커밋한다. 그래서 모든 클라이언트가 같은 시점에 커밋을 본다.
  - `rpl_semi_sync_source_timeout`(기본 10000 ms) 안에 응답이 없으면 **비동기로 되돌아간다**. 이 구간의 커밋은 유실될 수 있다.

> 참고: 원본 §1 표의 "준동기 — 장애 시 유실 최소"는 응답이 제때 올 때만 맞다. 타임아웃으로 비동기로 떨어진 동안의 커밋은 비동기와 똑같이 잃을 수 있다(MySQL 8.4 19.4.10, `rpl_semi_sync_source_timeout`).

### 3. 복제 지연 — 어디서 생기고 어떻게 재나

```text
  리더 WAL flush ──▶ 팔로워 수신(write) ──▶ 디스크(flush) ──▶ 재생(조회에 보임)
  |<── write_lag ──────────>|
  |<── flush_lag ──────────────────────────────>|
  |<── replay_lag ─────────────────────────────────────────────>|
  (세 값 모두 리더 flush 시점부터의 누적 시간. PostgreSQL pg_stat_replication, 리더에서 조회)
```

- PostgreSQL 17 `pg_stat_replication`(리더에서): `write_lag`·`flush_lag`·`replay_lag`는 "리더가 WAL을 flush한 뒤 팔로워가 그 단계까지 했다는 알림을 받기까지 걸린 시간"이다(27.2).
- 팔로워에서: `pg_last_wal_receive_lsn()`·`pg_last_wal_replay_lsn()`으로 위치를 본다.
- MySQL 8.4: `SHOW REPLICA STATUS`의 `Seconds_Behind_Source`. applier가 리더 binlog 처리에서 몇 초 뒤처졌나. 문서는 0이 "대개" 따라잡았다는 뜻이지만 **항상은 아니라고** 적는다(예: 리더와의 네트워크 연결이 끊겼는데 수신(I/O) 스레드가 아직 알아채지 못했을 때, 19.1.7.1).
- 지연의 흔한 원인
  - 리더의 큰 트랜잭션·대량 DML(34번). 팔로워가 같은 양을 재생해야 한다.
  - 팔로워의 적용 병렬도. MySQL 8.4 `replica_parallel_workers` 기본값은 4다(19.1.6.3). 이 서버에서도 4, `replica_preserve_commit_order = 1`이었다(로컬 확인).
  - 팔로워의 긴 조회가 재생을 막는 경우(아래 §5).

### 4. 읽기 보장 — 세 가지 이상 현상

```text
  read-your-writes 위반              monotonic reads 위반               consistent prefix 위반
  나: 쓰기 → 리더                     읽기1 → 팔로워 A(최신)   "댓글 3개"    질문 → 파티션 1 (지연 큼)
  나: 읽기 → 팔로워(지연)               읽기2 → 팔로워 B(지연)   "댓글 2개"    답   → 파티션 2 (지연 작음)
  "내 글이 없다"                       "시간이 거꾸로 간다"                 "답이 질문보다 먼저 보인다"
```

- *read-your-writes*: 내가 쓴 것은 내가 곧바로 읽을 수 있어야 한다.
- *monotonic reads*: 한 번 본 것보다 **옛날 상태**를 다시 보지 않아야 한다.
- *consistent prefix reads*: 인과 순서가 있는 쓰기들을 그 순서대로 봐야 한다. 주로 여러 파티션이 따로 복제될 때 문제다(33번).
- 이 세 용어는 DDIA 5장 "Problems with Replication Lag"의 분류다.

### 5. 팔로워에서 읽기 — 재생과 조회의 충돌

```text
  팔로워 시간축
  조회 Q (옛 튜플 v1을 읽는 중) ──────────────────────────────▶
  WAL 재생: "v1을 vacuum으로 지움" ── 대기 ── max_standby_streaming_delay(기본 30s) 초과 ── Q 취소
```

- PostgreSQL 팔로워는 리더의 vacuum 기록까지 재생한다. 팔로워에서 아직 그 옛 버전을 보는 조회가 있으면 충돌이다(26.4).
- 재생은 `max_standby_streaming_delay`(기본 30초)까지만 기다리고, 넘으면 조회를 취소한다.
  - 이 값은 조회 하나에 주는 시간이 아니다. "받은 WAL의 적용을 미룰 수 있는 총 시간"이다. 앞선 충돌로 이미 밀렸다면 다음 조회는 훨씬 빨리 취소될 수 있다(19.6.3).
- 에러는 `canceling statement due to conflict with recovery`, SQLSTATE는 보통 `40001`(`ERRCODE_T_R_SERIALIZATION_FAILURE`, `postgres.c`)이다. 같은 메시지라도 복구와의 버퍼 교착이면 `40P01`이다(`standby.c`, DETAIL "User transaction caused buffer deadlock with recovery.").
- `hot_standby_feedback = on`(기본 off)이면 팔로워가 "이 버전은 아직 쓴다"고 리더에 알려 vacuum 정리 기록으로 생기는 이 충돌을 없앤다. 연결이 끊겨 피드백이 가지 않는 동안 만들어진 WAL, 그리고 락·DROP 같은 다른 종류의 충돌은 막지 못한다(26.4). 대신 리더 쪽 **테이블 팽창(bloat)**을 일으킬 수 있다(19.6.3).
- 즉 긴 조회를 팔로워에 두면 "재생이 늦어짐(지연)" 또는 "조회가 죽음" 또는 "리더가 부풂" 중 하나를 고르게 된다.

### 6. 페일오버 — 무엇을 잃나

```text
  비동기, 리더 L이 커밋 5까지 함          팔로워 F는 3까지만 받음
  L: 1 2 3 4 5  (클라이언트에 5까지 "성공")   F: 1 2 3
  L 사망 → F 승격 → 새 쓰기 4' 5' ...       4·5는 사라짐. 옛 L이 돌아오면 4·5와 4'·5'가 충돌
```

- 팔로워를 승격하면 PostgreSQL은 **새 타임라인**을 시작한다(20번 참고). 옛 리더에 새 리더가 받지 못한 WAL(아래 4·5)이 남아 있으면 그대로 팔로워로 붙일 수 없다. `pg_rewind`로 새 리더에 맞춰 되감은 뒤 팔로워로 붙인다(`pg_rewind` 문서).
- 옛 리더에만 있던 4·5는 **버려진다**. 이것이 "확인된 쓰기 유실"이다.
- 둘 다 자신이 리더라고 믿으면 *split brain*이다. 양쪽이 쓰기를 받아 데이터가 갈라진다(원본 [05-ha-topology.md](../../systems/server-design/05-ha-topology.md) §3).
- GitHub 2012-09-11 사고: 클러스터 관리 소프트웨어가 분할된 상태에서 **이미 뒤처진 것으로 알려진** MySQL 노드를 리더로 뽑았다. 7분 동안 그 노드가 쓰기를 받았다. MySQL이 만든 ID로 Redis를 조회하던 데이터가 어긋나, 일부 이벤트가 엉뚱한 사용자 대시보드에 보였고 비공개 저장소 16개가 7분간 외부에 노출됐다(GitHub 블로그 "GitHub availability this week").

## 쓰이는 자료구조·알고리즘

- **추가 전용 로그 + 위치(LSN·binlog 좌표·GTID)** — 복제는 "로그를 같은 순서로 재생"이다. 팔로워의 진행은 로그 위치 하나로 표현된다. 지연 = 위치의 차이.
  - *GTID*: MySQL 트랜잭션마다 붙는 전역 ID(`source_uuid:번호`). 파일·위치 대신 "어떤 트랜잭션들을 적용했나"의 집합으로 진행을 표현한다.
- **복제 슬롯** — 팔로워가 아직 안 받은 WAL을 리더가 지우지 못하게 붙잡는 표시. `restart_lsn`이 그 경계다.
- **상태 기계 복제** — 같은 초기 상태 + 같은 순서의 결정적 연산 = 같은 결과. ROW 형식이 SQL 문장 형식보다 안전한 이유는 `UUID()`·`RAND()`·`SYSDATE()`·`ORDER BY` 없는 `LIMIT` 같은 비결정 요소를 팔로워가 다시 계산하지 않기 때문이다. (MySQL 8.4 문서는 `NOW()`는 문장 기반으로도 올바르게 복제된다고 적는다 — 19.2.1.1.)
- **리더 선출·펜싱** — 누가 리더인지 정하고 옛 리더를 확실히 막는 문제([ops-patterns/12-leader-election](../../ops-patterns/12-leader-election/2-summary.md), [ops-patterns/11-distributed-lock](../../ops-patterns/11-distributed-lock/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 지연을 재고 경보한다

```sql
-- PostgreSQL 17, 리더에서
SELECT application_name, state, sync_state,
       write_lag, flush_lag, replay_lag,
       pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn)) AS replay_bytes_behind
FROM pg_stat_replication;

-- 팔로워에서
SELECT pg_last_wal_receive_lsn(), pg_last_wal_replay_lsn(), now() - pg_last_xact_replay_timestamp();
```

```sql
-- MySQL 8.4, 복제본에서
SHOW REPLICA STATUS\G     -- Seconds_Behind_Source, Replica_SQL_Running_State, Last_SQL_Error
```

- `pg_last_xact_replay_timestamp()`는 마지막으로 재생한 트랜잭션의 커밋(또는 abort) 레코드가 **리더에서 만들어진 시각**이다(9.28). 그래서 리더에 쓰기가 없으면 `now()`와의 차이가 지연이 없어도 계속 커진다.
- 임계치를 넘은 팔로워는 읽기 로드밸런서에서 뺀다(원본 §1 "필수 운영").

### 2. read-your-writes를 구현한다

```java
// (의사 코드) 쓰기 직후 위치를 받아 두고, 읽을 때 그 위치를 따라잡은 팔로워만 쓴다 — PostgreSQL 예
long commitLsn;
try (var tx = primary.begin()) {
    tx.update("UPDATE post SET body = ? WHERE id = ?", body, id);
    tx.commit();
    commitLsn = primary.queryLsn("SELECT pg_current_wal_lsn()");   // 커밋 뒤 위치(≥ 내 커밋)
}
session.put("minLsn", commitLsn);

// 읽기
DataSource ds = replicas.stream()
    .filter(r -> r.queryBool("SELECT pg_last_wal_replay_lsn() >= ?::pg_lsn", lsnText(session.get("minLsn"))))
    .findFirst().orElse(primary);                                 // 없으면 리더로
```

- MySQL(GTID 켠 경우): 리더에서 커밋 뒤 `@@GLOBAL.gtid_executed`를 받아 두고, 복제본에서 `SELECT WAIT_FOR_EXECUTED_GTID_SET('<gtid_set>', 1)`로 최대 1초 기다린다. 시간 안에 못 따라오면 리더에서 읽는다. 이 함수는 timeout을 주지 않으면(기본 0) 끝없이 기다린다.
- 더 단순한 방법(원본 §1 표): "쓴 사람은 N초 동안 리더에서 읽기", "내가 고칠 수 있는 데이터는 항상 리더". monotonic reads는 세션을 한 팔로워에 고정해서 얻는다.

### 3. 동기 복제를 설계한다

```ini
# PostgreSQL 17 (예시) — 리더 로컬 flush + s1·s2 중 아무 1대의 flush 응답(3대 중 2대에 기록)
synchronous_standby_names = 'ANY 1 (s1, s2)'
synchronous_commit = on
```

- 동기 팔로워가 1대뿐이면 그 1대의 장애가 **리더 쓰기 정지**로 번진다. 후보를 여럿 두고 quorum(`ANY k`)으로 받는다.
- 모든 트랜잭션이 같은 수준일 필요는 없다. `SET LOCAL synchronous_commit = off`로 로그성 쓰기는 가볍게, 결제는 `on`/`remote_apply`로 둘 수 있다.

### 4. 복제 슬롯의 WAL 보존을 관리한다

로컬 재현(예시, PostgreSQL 17.11): 물리 슬롯을 만들고(`immediately_reserve = true`) 연결 없이 두었다. 같은 서버의 다른 세션들이 쓰기를 하는 동안 잠깐 뒤 조회했다.

```text
  slot_name     | active | restart_lsn | wal_status | retained
  w20_demo_slot | f      | 0/CBC4BD30  | reserved   | 339 MB
```

- 팔로워가 죽어 있어도 슬롯은 WAL을 붙잡는다. 문서 경고: 슬롯이 `pg_wal`을 가득 채울 수 있다(26.2.6).
- `max_slot_wal_keep_size`(기본 -1 = 무제한)로 상한을 둔다. 넘으면 필요한 WAL이 지워져 그 팔로워가 복제를 이어 가지 못할 수 있다(19.6.1). WAL 아카이브에서도 그 구간을 받을 수 없으면 팔로워를 다시 만든다.
- 재현이 끝나고 슬롯은 바로 지웠다.

## 장애 시나리오와 대처

### 1. 복제 지연 → 방금 쓴 글이 안 보인다(read-your-writes 위반)

- **현상**: 글 작성 후 목록에 없다. 새로고침하면 생긴다. 쓰기가 몰리는 시간에만 난다.
- **보이는 형태**: `pg_stat_replication.replay_lag` 또는 `Seconds_Behind_Source`가 수 초 이상. 애플리케이션 에러는 없다. 사용자 문의만 온다.
- **원인**: 쓰기는 리더, 읽기는 비동기 팔로워로 보냈다. 팔로워가 아직 그 커밋을 재생하지 않았다.
- **대처**
  - 위 적용 2(LSN·GTID 기반 대기, 또는 쓴 사람은 리더에서 읽기).
  - 지연 임계치를 넘은 팔로워를 읽기 풀에서 뺀다.
  - 지연의 원인(대량 DML·긴 조회·적용 병렬도)을 줄인다.

### 2. 비동기 페일오버 → "성공" 응답을 받은 쓰기가 사라진다

- **현상**: 리더 장애 뒤 자동 승격. 몇몇 주문·결제가 새 리더에 없다. 사용자는 완료 화면을 봤다.
- **보이는 형태**: 승격 직전의 지연만큼 최근 트랜잭션이 없다. PostgreSQL에서는 옛 리더를 그대로 붙이려 하면 타임라인이 갈라져 거부된다. MySQL에서는 옛 리더의 binlog에 새 리더에 없는 트랜잭션이 남는다(GTID로 비교 가능).
- **원인**: 비동기 복제에서 커밋 응답은 "리더 로컬 flush"만 의미한다(PostgreSQL 26.2.8, MySQL 19.4.10). 로컬 내구성 설정이 기본일 때의 이야기다(PostgreSQL `synchronous_commit = on`, MySQL `sync_binlog = 1`·`innodb_flush_log_at_trx_commit = 1` — 로컬 확인). PostgreSQL `synchronous_commit = off`면 로컬 flush도 기다리지 않는다.
- **대처**
  - 잃으면 안 되는 쓰기는 동기(`synchronous_commit = on`, 후보 여럿) 또는 MySQL `AFTER_SYNC` 준동기로. 준동기 타임아웃으로 비동기로 떨어진 시간을 지표로 본다.
  - 승격 도구는 가장 앞선 팔로워를 고르고, 옛 리더를 확실히 막는다(펜싱). 옛 리더의 남은 트랜잭션은 따로 뽑아 사람이 판단한다.
  - ID가 다른 저장소의 키로 쓰이면 재사용 사고가 난다(GitHub 2012). 페일오버 뒤 시퀀스를 크게 건너뛰게 한다. GitLab 2017 복구도 ID 재사용을 막으려고 모든 시퀀스를 100,000 올렸다(GitLab 포스트모템, 20번 사고).

### 3. 팔로워의 긴 조회가 취소된다

- **현상**: 팔로워에서 돌던 리포트가 수십 초 뒤 실패한다. 재시도하면 될 때도 있다.
- **보이는 형태**: `ERROR: canceling statement due to conflict with recovery` + `DETAIL: User query might have needed to see row versions that must be removed.`(스냅숏 충돌일 때의 문구. 충돌 사유마다 DETAIL이 다르다 — `postgres.c`). SQLSTATE가 보통 `40001`이라(버퍼 교착이면 `40P01`) 드라이버·Spring은 직렬화 실패 계열로 분류할 수 있다.
- **원인**: 리더의 vacuum 기록을 재생해야 하는데 팔로워 조회가 그 옛 버전을 보고 있었다. 적용 지연이 `max_standby_streaming_delay`(30초)를 넘겨 조회를 취소했다.
- **대처**: 리포트 전용 팔로워는 `max_standby_streaming_delay`를 늘리거나(그만큼 지연 증가) `hot_standby_feedback = on`(리더 bloat 감수). 조회를 쪼개 짧게 한다. 아주 긴 분석은 논리 복제·별도 분석 DB로 보낸다.

### 4. 죽은 팔로워의 복제 슬롯 → 리더 디스크가 찬다

- **현상**: 팔로워를 내려 둔 사이 리더의 `pg_wal` 디렉터리가 계속 커진다. 결국 디스크 풀로 리더가 멈춘다.
- **보이는 형태**: `pg_replication_slots.active = f`, `restart_lsn`이 멈춰 있고 보존량이 계속 는다(위 재현 339 MB). 최악에는 `pg_wal/`이 든 파일 시스템이 차서 리더가 PANIC으로 내려간다(PostgreSQL 17 25.3.1: "If the file system containing pg_wal/ fills up, PostgreSQL will do a PANIC shutdown"). WAL 쓰기 실패의 로그는 `PANIC: could not write to log file "…" at offset …, length …: No space left on device`(소스 REL_17_STABLE `xlog.c` `XLogWrite`)이고, 새 세그먼트 생성 중이면 `could not write to file "pg_wal/xlogtemp.…": No space left on device`일 수도 있다([19번](../19-wal-and-logging/2-summary.md) 장애 2).
- **원인**: 슬롯은 팔로워가 돌아올 때를 위해 WAL을 무한정 붙잡는다(기본 `max_slot_wal_keep_size = -1`).
- **대처**: 안 쓰는 슬롯은 `pg_drop_replication_slot()`. `max_slot_wal_keep_size`로 상한. `pg_replication_slots`의 보존량을 경보 지표로.

### 5. 동기 팔로워 장애 → 리더 쓰기가 멈춘다

- **현상**: 팔로워 한 대를 점검하러 내렸더니 리더의 모든 커밋이 멈췄다.
- **보이는 형태**: 커밋하는 세션들이 `pg_stat_activity`에서 `wait_event = SyncRep`("동기 복제 중 원격 서버의 확인을 기다림" — 27.2 wait event 표)으로 멈춰 있다. 에러 없이 응답이 없다.
- **원인**: `synchronous_standby_names`에 그 한 대만 있었다. 문서: 동기 팔로워가 죽으면 그 커밋은 끝나지 않을 수 있다(26.2.8).
- **대처**: 후보를 여럿 두고 `ANY k`/`FIRST k`로. 점검 전 설정에서 빼고 reload. MySQL 준동기는 타임아웃 뒤 비동기로 떨어져 멈추지는 않지만, 그 대가로 유실 창이 열린다.

## 핵심 문장

- 복제는 리더의 변경 로그(PostgreSQL WAL, MySQL binlog)를 팔로워가 같은 순서로 재생하는 것이다. 진행은 로그 위치 하나로, 지연은 위치의 차이로 잰다.
- PostgreSQL·MySQL 모두 기본은 비동기다. 커밋 성공은 (기본 내구성 설정에서) "리더 로컬 flush"뿐이고, 비동기 페일오버는 그 차이만큼 확인된 쓰기를 잃는다.
- 동기 수준은 팔로워의 수신·flush·재생 중 어디까지 기다리나의 선택이다. 동기 팔로워가 하나뿐이면 그 장애가 리더 쓰기 정지로 번진다.
- 팔로워 읽기는 read-your-writes·monotonic reads를 깨뜨릴 수 있다. 커밋 위치(LSN·GTID)를 들고 다니거나 리더로 우회한다.
- 팔로워의 긴 조회는 재생 지연·조회 취소(40001)·리더 bloat 중 하나를 대가로 치른다.

## 관련 주제·근거

- 원본(기초): [systems/server-design/03-data-layer.md](../../systems/server-design/03-data-layer.md) §1 읽기 확장 — 복제 · [05-ha-topology.md](../../systems/server-design/05-ha-topology.md) §3 리더-팔로워 Failover
- 선행: [19-wal-and-logging](../19-wal-and-logging/2-summary.md)
- 연결
  - [20-backup-and-pitr](../20-backup-and-pitr/2-summary.md) — 복제는 백업이 아니다, 타임라인
  - [42-recovery-aries-checkpoints](../42-recovery-aries-checkpoints/2-summary.md) — 팔로워의 재생도 같은 redo
  - [33-partitioning-and-sharding](../33-partitioning-and-sharding/2-summary.md) — 파티션별 복제와 consistent prefix
  - [34-large-backfill-and-batch-dml](../34-large-backfill-and-batch-dml/2-summary.md) — 복제 지연 기준 스로틀
  - distributed `06-replication-strategies`·`07-consistency-models`·`10-leader-election` — [distributed/README](../../distributed/README.md) · [ops-patterns/12-leader-election](../../ops-patterns/12-leader-election/2-summary.md)
- 교재: DDIA 1판 5장 Replication — Leaders and Followers, Synchronous vs Asynchronous, Handling Node Outages(Failover), Problems with Replication Lag(read-your-writes·monotonic reads·consistent prefix reads)
- PostgreSQL 17
  - 26.2 Log-Shipping Standby Servers(26.2.6 슬롯 경고, 26.2.8 동기 복제·기본 비동기·HA 계획) <https://www.postgresql.org/docs/17/warm-standby.html>
  - 26.4 Hot Standby(조회 충돌, `max_standby_*_delay`) <https://www.postgresql.org/docs/17/hot-standby.html>
  - 19.5.1 `synchronous_commit` 5단계 · 19.6 Replication(`hot_standby_feedback` bloat 경고, `max_slot_wal_keep_size` -1) <https://www.postgresql.org/docs/17/runtime-config-replication.html>
  - 27.2 `pg_stat_replication`(`write_lag`·`flush_lag`·`replay_lag`) · `pg_rewind` <https://www.postgresql.org/docs/17/app-pgrewind.html>
  - `src/backend/tcop/postgres.c` — "canceling statement due to conflict with recovery", `ERRCODE_T_R_SERIALIZATION_FAILURE` · `src/backend/storage/ipc/standby.c` — 같은 메시지의 버퍼 교착 `ERRCODE_T_R_DEADLOCK_DETECTED`
  - CREATE TABLE `UNLOGGED`(standby로 복제되지 않음) <https://www.postgresql.org/docs/17/sql-createtable.html>
- MySQL 8.4 Reference Manual
  - 19.4.10 Semisynchronous Replication(기본 비동기, ack는 relay log flush 후, 타임아웃 시 비동기) <https://dev.mysql.com/doc/refman/8.4/en/replication-semisync.html>
  - 19.1.6.2 Source 옵션(`rpl_semi_sync_source_wait_point` 기본 AFTER_SYNC, `rpl_semi_sync_source_timeout` 10000 ms) <https://dev.mysql.com/doc/refman/8.4/en/replication-options-source.html>
  - 7.4.4.2 Setting The Binary Log Format(ROW에서도 DDL은 문장 형식) <https://dev.mysql.com/doc/refman/8.4/en/binary-log-setting.html>
  - 19.1.6.3 Replica 옵션(`replica_parallel_workers` 기본 4) · 19.1.7.1 복제 상태(`Seconds_Behind_Source`) · 14.18.2 GTID 함수(`WAIT_FOR_EXECUTED_GTID_SET`)
- 사고: GitHub "GitHub availability this week"(2012-09-14) <https://github.blog/news-insights/the-library/github-availability-this-week/>
- 로컬 재현(PostgreSQL 17.11, MySQL 8.4.10): binlog ROW 이벤트(`Table_map`·`Update_rows`·`Xid`), WAL의 `HOT_UPDATE` 블록 참조, 비활성 물리 슬롯의 WAL 보존(339 MB) 후 삭제, `wal_level = replica`에서 논리 슬롯 생성 거부, 준동기 플러그인 미설치 시 `ERROR 1193`, 복제 관련 기본값 조회
