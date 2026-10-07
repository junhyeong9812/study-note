# data-engineering/05-change-data-capture — 변경 데이터 캡처: DB 로그 구독, 스냅샷 + 스트림, 삭제와 DDL — 정리 (힌트)

## 해결하는 문제

운영 DB(원천)의 변경을 검색 인덱스·캐시·웨어하우스(파생)로 옮겨야 한다([01번](../01-system-of-record-and-derived-data/2-summary.md)). 가장 먼저 떠오르는 방법은 주기적으로 묻는 것이다.

```text
  폴링: 5분마다  SELECT * FROM customer WHERE updated_at > :last_seen
  ┌──────────────┐                ┌──────────────┐
  │ 운영 DB       │ ── 5분마다 ──> │ 파생 저장소    │
  └──────────────┘                └──────────────┘
  놓치는 것
   - DELETE된 행: 지워졌으니 WHERE에 걸리지 않는다 → 파생본에 남는다
   - 5분 안에 두 번 바뀐 행: 마지막 값만 보인다 → 중간 상태가 사라진다
   - updated_at을 갱신하지 않는 경로(배치 UPDATE, 수동 SQL)의 변경
```

- *CDC(Change Data Capture)*: 원천 DB의 행 변경(INSERT·UPDATE·DELETE)을 일어난 순서대로 뽑아 다른 시스템에 흘려보내는 기법.
- *로그 기반 CDC*: 테이블을 다시 읽는 대신, DB가 이미 쓰고 있는 변경 로그(PostgreSQL WAL, MySQL binlog)를 구독하는 방식.
  - Debezium 문서(Features)는 로그 기반 CDC가 폴링·이중 쓰기와 달리 "Ensures that all data changes are captured", 삭제를 잡고, "Last Updated" 같은 컬럼을 요구하지 않는다고 정리한다.

쉬운 예: 통장 잔액만 매일 확인하면, 하루에 무엇이 들어오고 나갔는지 모른다. 거래 내역을 순서대로 받아 적으면 잔액도, 그 사이에 오간 거래도 맞출 수 있다.

똑같은 구조다.\
DB의 WAL·binlog가 "거래 내역"이고, CDC 커넥터가 그것을 받아 적는 사람이다.

실무 예:
- 주문 DB의 변경을 Kafka로 흘려 검색 인덱스·캐시를 갱신한다.
- outbox 테이블을 폴링 대신 로그로 읽어 이벤트를 발행한다([distributed/16 §3](../../distributed/16-outbox-and-dual-write/2-summary.md)에서 슬롯·`test_decoding`의 기본 모습을 보였다 — 이 노트는 그 운영 측면을 이어 다룬다).
- 운영 DB를 웨어하우스로 복제해 분석한다([02번](../02-oltp-olap-and-warehouse/2-summary.md)).

## 동작·원리

### 1. 큰 그림 — 로그 → 슬롯(위치) → 커넥터 → 토픽 → 하류

```text
  PostgreSQL 17                                       Kafka                    하류
  ┌─────────────────────────────┐                 ┌────────────┐         ┌──────────────┐
  │ 트랜잭션 커밋                 │                 │ 토픽(테이블별)│         │ 검색 인덱스     │
  │   → WAL에 기록 (LSN 증가)     │                 │  key = PK   │ ──────> │ 웨어하우스      │
  │ 논리 디코딩 + 출력 플러그인      │ ── 커넥터 ──>   │  value =    │         │ 캐시           │
  │ 복제 슬롯: "어디까지 보냈나"     │  (Debezium 등) │  before/after│         └──────────────┘
  └─────────────────────────────┘                 └────────────┘
         ▲ 슬롯이 confirmed_flush_lsn·restart_lsn을 기억한다 (소비자가 꺼져 있어도)
```

- *WAL(Write-Ahead Log)*: 데이터 파일보다 먼저 쓰는 변경 기록. 원래 목적은 크래시 복구다([database/19](../../database/19-wal-and-logging/2-summary.md)).
- *LSN(Log Sequence Number)*: WAL 안의 바이트 위치. `0/1523600`처럼 쓰고 계속 커진다.
- *논리 디코딩(logical decoding)*: 저장 수준의 WAL 레코드를 "어느 테이블의 어느 행이 어떻게 바뀌었나"로 풀어내는 기능(PostgreSQL 17 문서 47.2.1).
- *출력 플러그인*: 풀어낸 변경을 어떤 형식으로 내보낼지 정하는 모듈. `test_decoding`(예제·시험용 텍스트, 문서 F.43), `pgoutput`(내장 논리 복제용)이 있다.
- *복제 슬롯(replication slot)*: 한 소비자를 위해 "변경을 어디까지 보냈나"를 서버가 기억하는 객체. 연결과 무관하게 남고 크래시에도 살아남는다(47.2.2).
  - 흔한 오해: 슬롯이 소비자 상태를 안다. 문서는 "A logical replication slot knows nothing about the state of the receiver(s)"라고 적는다. 소비자가 사라져도 슬롯은 WAL을 계속 붙잡는다.
- MySQL은 *binlog*(복제용 행 이벤트 로그)를 구독한다. Debezium MySQL 커넥터는 `binlog_format=ROW`, `binlog_row_image=FULL`을 요구한다(Debezium MySQL 문서). 슬롯 같은 서버 쪽 위치 객체는 없고, 커넥터가 binlog 위치(또는 GTID)를 자기 오프셋으로 저장한다.

#### 실험 A: `test_decoding`으로 본 변경 스트림

(실험, `postgres:17` = PostgreSQL 17.11 전용 컨테이너 `--network none`, `wal_level=logical`, 2026-10-07)

```sql
SELECT * FROM pg_create_logical_replication_slot('w05_slot','test_decoding');
INSERT INTO customer VALUES (3,'user_003','basic');
UPDATE customer SET tier='gold' WHERE id=1;
DELETE FROM customer WHERE id=2;
BEGIN; INSERT INTO customer VALUES (99,'user_099','basic'); ROLLBACK;
SELECT lsn, xid, data FROM pg_logical_slot_get_changes('w05_slot', NULL, NULL);
```

```text
    lsn    | xid | data
-----------+-----+---------------------------------------------------------------------------------------
 0/1523600 | 741 | BEGIN 741
 0/1523600 | 741 | table public.customer: INSERT: id[integer]:3 name[text]:'user_003' tier[text]:'basic'
 0/15236C0 | 741 | COMMIT 741
 0/15236C0 | 742 | BEGIN 742
 0/15236C0 | 742 | table public.customer: UPDATE: id[integer]:1 name[text]:'user_001' tier[text]:'gold'
 0/1523748 | 742 | COMMIT 742
 0/1523748 | 743 | BEGIN 743
 0/1523748 | 743 | table public.customer: DELETE: id[integer]:2
 0/15237B8 | 743 | COMMIT 743
-- 같은 슬롯에서 다시 get_changes → 0행 (읽으면 슬롯이 전진한다)
```

- 관찰
  - 커밋한 트랜잭션만, 커밋 순서대로, `BEGIN … COMMIT` 묶음으로 나왔다. 롤백한 `id=99`는 없다.
  - 기본 설정(`REPLICA IDENTITY DEFAULT`)에서 DELETE는 **기본 키만** 담았다(`id[integer]:2`). UPDATE에는 이전 값이 없다.
- 같은 테이블을 `ALTER TABLE customer REPLICA IDENTITY FULL`로 바꾸고 다시 했다.

```text
 table public.customer: UPDATE: old-key: id[integer]:3 name[text]:'user_003' tier[text]:'basic' new-tuple: id[integer]:3 name[text]:'user_003' tier[text]:'silver'
 table public.customer: DELETE: id[integer]:3 name[text]:'user_003' tier[text]:'silver'
 BEGIN 748
 COMMIT 748                      ← ALTER TABLE ... ADD COLUMN region (DDL) — 내용 없는 빈 트랜잭션
 table public.customer: INSERT: id[integer]:4 name[text]:'user_004' tier[text]:'basic' region[text]:'KR'
 table public.customer: TRUNCATE: (no-flags)
```

- *REPLICA IDENTITY*: UPDATE·DELETE 때 이전 행의 어떤 컬럼을 로그에 남길지 정하는 PostgreSQL 테이블 설정. `FULL`이면 이전 행 전체를 남긴다. 그만큼 WAL이 커진다.
- DDL(`ADD COLUMN`)은 변경 스트림에 나오지 않았다. 새 컬럼은 다음 INSERT에 **갑자기** 나타났다. Debezium PostgreSQL 문서도 "Logical decoding does not support DDL changes"라고 적는다(§5에서 다룬다).

### 2. 초기 스냅샷 + 스트리밍 — 경계가 문제다

WAL은 오래된 부분이 재활용된다. 그래서 커넥터는 처음에 현재 상태를 한 번 통째로 읽고(스냅샷), 그 뒤부터 로그를 따라간다. 문제는 "스냅샷 시점"과 "스트림 시작 위치"를 정확히 맞추는 것이다.

```text
  시간 ─────────────────────────────────────────────────────>
  B1  스냅샷 먼저, 슬롯 나중     SELECT(1~5) ── INSERT 6 ── 슬롯 생성 ── INSERT 7
                                                  └ 6은 스냅샷에도, 스트림에도 없다 → 누락
  B2  슬롯 먼저, 스냅샷 나중     슬롯 생성 ── INSERT 6 ── SELECT(1~6) ── INSERT 7
                                            └ 6이 스냅샷에도, 스트림에도 있다 → 중복
  B3  슬롯 생성이 내보낸 스냅샷   CREATE_REPLICATION_SLOT ... EXPORT_SNAPSHOT
                                 ├ 그 스냅샷으로 SELECT → 슬롯 시작점 "직전" 상태
                                 └ 스트림 → 슬롯 시작점 "이후" 변경   → 누락도 중복도 없다
```

#### 실험 B: 세 가지 순서

(실험, PostgreSQL 17.11, 테이블 `acct`에 1~5가 있는 상태에서 시작, 2026-10-07)

```text
== B1 스냅샷 먼저, 슬롯 나중
snapshot ids: 1,2,3,4,5
stream: table public.acct: INSERT: id[integer]:7 bal[integer]:100
== B2 슬롯 먼저, 스냅샷 나중
snapshot ids: 1,2,3,4,5,6
stream: table public.acct: INSERT: id[integer]:6 bal[integer]:100
stream: table public.acct: INSERT: id[integer]:7 bal[integer]:100
== B3 슬롯 생성 시 내보낸 스냅샷(EXPORT_SNAPSHOT)
replication conn: b3|0/152C3A8|00000071-00000002-1|test_decoding
snapshot ids: 1,2,3,4,5
stream: table public.acct: INSERT: id[integer]:6 bal[integer]:100
stream: table public.acct: INSERT: id[integer]:7 bal[integer]:100
```

- B1은 `id=6`을 잃었다. 에러는 없었다.
- B2는 `id=6`을 두 번 받았다. 하류가 덧붙이기만 하면 행이 하나 더 생긴다(아래 실험 C).
- B3은 복제 연결(`replication=database`)에서 슬롯을 만들며 받은 스냅샷 이름(`00000071-00000002-1`)을 `SET TRANSACTION SNAPSHOT`으로 썼다. PostgreSQL 17 문서 47.2.5: 이 스냅샷은 "exactly the state of the database after which all changes will be included in the change stream"을 보여 준다. 스냅샷 + 스트림이 빈틈도 겹침도 없이 이어진다는 뜻이다.
  - 단, 내보낸 스냅샷은 그 복제 연결이 다음 명령을 실행하거나 끊기 전까지만 쓸 수 있다. 실험에서는 FIFO로 연결을 열어 둔 채 읽었다.
- Debezium PostgreSQL 커넥터의 기본(`snapshot.mode=initial`) 흐름: 트랜잭션을 열고 → 현재 로그 위치를 읽고 → 테이블을 스캔해 `op=r`(read) 이벤트를 내고 → 커밋한 뒤, 읽어 둔 위치부터 스트리밍한다(Debezium PostgreSQL 문서 "Snapshots").
  - 스냅샷 도중 커넥터가 멈추면 재시작 때 스냅샷을 **처음부터** 다시 한다(같은 문서).

### 3. 증분 스냅샷 — 스트림을 멈추지 않고 나눠 읽기

초기 스냅샷은 크면 몇 시간이 걸린다. 그동안 스트리밍이 멈추고, 중간에 죽으면 처음부터다. 나중에 테이블을 하나 추가하려 해도 같은 문제가 생긴다(Debezium 블로그 2021-10-07 "Incremental Snapshots", Jiri Pechanec). 해법은 Netflix DBLog 논문의 워터마크 방식이다.

```text
  변경 로그 ──●──●──[ window-open ]──●(K4 삭제)──●(K5 삽입)──[ window-close ]──●──>
                         │                                          │
                         └─ 이 사이에 청크 쿼리: PK 순서로 K1,K2,K4,K5 를 읽어 버퍼에
  창 안에서 로그에 나타난 키(K4, K5)는 버퍼에서 지운다 → 로그 이벤트만 내보낸다
  window-close 때 버퍼에 남은 K1, K2를 read 이벤트로 내보낸다
```

- 블로그가 설명하는 Debezium 동작
  - 테이블의 최대 PK를 끝점으로 기록하고, PK 순서로 `incremental.snapshot.chunk.size`(기본 1,024)개씩 청크를 읽는다.
  - 청크마다 열기·닫기 신호를 로그에 남긴다. 창 안에서 로그에 나온 키는 스냅샷 버퍼에서 버린다. 순서를 확정할 수 없으니 로그 이벤트 쪽을 믿는다.
  - 오프셋에 "남은 테이블 목록, 최대 PK, 마지막으로 보낸 PK"를 넣어 두어, 재시작하면 마지막 청크 다음부터 잇는다.
- 소비자에게 바뀌는 의미(블로그 "Limitations")
  - PK가 있는 테이블만 된다.
  - read 이벤트는 "초기 상태"가 아니라 "임의 시점의 상태"다. read와 update가 거꾸로 올 수도 있다.
  - 본 적 없는 키의 delete가 올 수 있다. at-least-once는 그대로다.
- PostgreSQL 커넥터는 증분 스냅샷 진행 중 스키마 변경을 지원하지 않는다(Debezium PostgreSQL 문서).

### 4. 삭제 — delete 이벤트와 tombstone

```text
  원천: DELETE FROM customer WHERE id=2
  Debezium 기본 출력(같은 토픽, 같은 키)
    offset 41  key={id:2}  value={op:"d", before:{id:2}, after:null}       ← delete 이벤트
    (REPLICA IDENTITY DEFAULT면 before에 PK 컬럼만, FULL이면 이전 행 전체)
    offset 42  key={id:2}  value=null                                      ← tombstone
  compaction 토픽: 키 2의 이전 레코드들 → 결국 제거, tombstone도 delete.retention.ms 뒤 제거
```

- *tombstone*: 값이 `null`인 레코드. Kafka log compaction에게 "이 키의 이전 값을 지워도 된다"고 알리는 표식이다(Kafka 4.1 문서 Design "Log Compaction").
- *log compaction*: 토픽 파티션에서 키마다 "최소한 마지막 값"을 남기고 이전 값을 지우는 보존 방식(`cleanup.policy=compact`).
- Debezium PostgreSQL 문서
  - `tombstones.on.delete`(기본 true)면 delete 이벤트 뒤에 tombstone을 하나 더 보낸다.
  - 기본 키가 없는 테이블이 `REPLICA IDENTITY DEFAULT`면 delete 이벤트에 `before`가 없다. 그런 테이블은 `FULL`로 바꾸라고 권한다. 같은 문서의 Replica identity 절은 이 경우 UPDATE·DELETE 이벤트를 아예 내보내지 않는다고 적는다(문서 안 두 서술이 다르다).
  - PostgreSQL 17 문서 29.1 Publication: replica identity가 없는 테이블이 UPDATE·DELETE를 복제하는 publication에 들어 있으면, 원천에서 UPDATE·DELETE 자체가 오류가 난다. `FULL`은 이전 행을 남길 뿐 기본 키를 만들지는 않는다.
  - 기본 키 값이 바뀌면 "옛 키의 DELETE + tombstone, 새 키의 이벤트" 세 개가 나온다.
- Kafka 4.1 토픽 설정 `delete.retention.ms`(기본 86400000 = 1일): compaction 토픽에서 tombstone을 남겨 두는 시간. 오프셋 0부터 읽는 소비자는 이 시간 안에 끝까지 읽어야 삭제를 놓치지 않는다(토픽 설정 문서).

#### 실험 C: 하류에 반영하는 두 방식

실험 B2의 스냅샷(1~6)과 그 뒤 스트림(INSERT 6, INSERT 7, UPDATE 1→150, DELETE 2)을 Java 모형으로 하류 테이블에 반영했다.

(실험, `eclipse-temurin:21-jdk` = OpenJDK 21.0.12, `CdcApply.java`, 2026-10-07)

```text
원천(진실):   rows=6 sum=650  ids=[1, 3, 4, 5, 6, 7]
A append:     rows=9 sum=950 distinct ids=7
B upsert+del: rows=6 sum=650  ids=[1, 3, 4, 5, 6, 7]
```

- A(행을 덧붙이고 DELETE는 무시)는 행 9개·합계 950이 됐다. 경계 중복(id 6), UPDATE의 이전 행(id 1), 지운 행(id 2)이 모두 남았다.
- B(키로 upsert, DELETE는 키 삭제)는 원천과 같았다. 경계 중복도 같은 키로 덮이므로 흡수됐다.
- 이 모형은 이벤트 순서가 키마다 지켜진다고 가정한다. Kafka는 파티션 안에서만 순서를 지킨다. Debezium은 기본으로 PK를 메시지 키로 쓰므로, 토픽 파티션 수와 파티셔닝 방식이 그대로인 동안 같은 행의 변경이 같은 파티션에 들어간다. 파티션을 늘리면 `hash(key) % 파티션 수` 배정이 바뀔 수 있다(Kafka 4.1 문서 Operations "Modifying topics")([distributed/17 §5](../../distributed/17-queues-logs-and-delivery-semantics/2-summary.md)).

### 5. DDL 변경 — 스트림에 없는 스키마

- PostgreSQL 논리 디코딩은 DDL을 내보내지 않는다(실험 A, Debezium PostgreSQL 문서). 커넥터는 그 테이블의 다음 변경이 올 때 들어온 메시지의 스키마가 메모리 속 스키마와 다른 것을 보고 DB에서 스키마를 다시 읽는다(`schema.refresh.mode=columns_diff`). `pgoutput`은 DDL 뒤 첫 DML 메시지 **앞에** 바뀐 테이블 구조를 담은 Relation 메시지를 보낸다(PostgreSQL 17 문서 53.5.3 Message Flow). 어느 쪽이든 DDL만으로는 아무것도 오지 않는다.
  - Debezium 문서: 플러그인마다 스키마 갱신 시점이 다르다. `pgoutput`은 컬럼 기본값 변경에도 갱신하지만, 다른 플러그인은 다음 변경(예: 컬럼 추가)이 올 때까지 모를 수 있다.
- MySQL binlog에는 행 변경뿐 아니라 DDL 문도 들어 있다. Debezium MySQL 커넥터는 DDL을 파싱해 메모리 속 테이블 스키마를 고치고, DDL과 binlog 위치를 내부용 스키마 이력 토픽에 기록한다. 재시작하면 이 토픽을 읽어 그 시점의 테이블 구조를 다시 만든다(Debezium MySQL 문서 "Schema history topic"). 이 노트의 실험은 PostgreSQL만 다뤘다.
- 하류 쪽 위험: 컬럼 이름 변경은 "옛 컬럼 삭제 + 새 컬럼 추가"처럼 보일 수 있다. 하류가 옛 이름으로 매핑하면 값이 NULL로 들어온다. 생산자–소비자 사이 계약과 호환성 검사는 [09번](../09-data-contracts-and-schema-registry/2-summary.md)의 주제다.
- 원천 쪽 DDL 순서는 expand/contract로 맞춘다([database/26](../../database/26-schema-migration/2-summary.md)).

### 6. 슬롯은 WAL을 붙잡는다 — 디스크 vs 끊김의 선택

```text
  pg_wal 디렉터리                                     현재 LSN
  [seg][seg][seg][seg][seg][seg][seg][seg][seg][seg] ─┤
   ▲ restart_lsn (커넥터가 멈춘 곳)
   └── 이 뒤의 세그먼트는 체크포인트가 지우지 못한다 → 디스크가 계속 찬다

  max_slot_wal_keep_size = 32MB 로 상한을 두면
  [  지워짐  ][  지워짐  ][seg][seg] ─┤   restart_lsn이 상한 밖 → 슬롯 wal_status = lost
                                         그 슬롯으로는 더 이어 받을 수 없다 → 재스냅샷
```

#### 실험 D: 소비하지 않는 슬롯과 `pg_wal` 크기

(실험, PostgreSQL 17.11, `min_wal_size=32MB`·`max_wal_size=48MB`로 작게 시작, 200바이트 행을 15만 개씩 INSERT, 측정 전마다 `CHECKPOINT`, 2026-10-07)

```text
 단계                                        pg_wal   파일  슬롯 restart_lsn → confirmed_flush_lsn   retained  wal_status
 C1 슬롯 없음, 15만 행 뒤                      48 MB     3    (슬롯 없음)
 C2 비활성 슬롯 + 45만 행 뒤                   160 MB   10    0/4621FB8 → 0/4621FF0                   147 MB    extended
 C3 슬롯을 현재 위치까지 advance               144 MB    9    0/7722AA0 → 0/D91E148                   98 MB     extended
 C4 CHECKPOINT 뒤 한 번 더 advance             48 MB     3    0/D91E168 → 0/D91E2E8                   592 bytes reserved
```

- 관찰
  - 슬롯이 없을 때는 체크포인트가 WAL을 지워 `pg_wal`이 48 MB(=`max_wal_size`)에 머물렀다.
  - 연결된 소비자가 없는(`active=f`) 슬롯 하나가 147 MB를 붙잡았다. `wal_status`는 `extended`(=`max_wal_size`를 넘었지만 슬롯 때문에 보존 중, 문서 52.19)였다.
  - `pg_replication_slot_advance`로 소비를 끝낸 것처럼 해도 `restart_lsn`은 `confirmed_flush_lsn`보다 한참 뒤에 남았다(C3). 체크포인트 뒤 다시 advance하자 따라붙었고 `pg_wal`이 48 MB로 돌아왔다(C4).
- 해석: `restart_lsn`은 "디코딩을 다시 시작할 때 필요한 가장 오래된 WAL 위치"다. 진행 중이던 트랜잭션 정보를 다시 만들 수 있는 지점까지만 당겨진다. Debezium 문서도 "confirmed_flush_lsn은 오르는데 restart_lsn이 뒤처지는" 상태를 정상 동작의 한 형태로 설명한다. PostgreSQL 내부 동작을 소스로 확인하지는 않았다 [?].
- PostgreSQL 17 컬럼 `inactive_since`가 슬롯이 언제부터 놀았는지 알려 준다(17에서 추가, 52.19).

#### 실험 E: `max_slot_wal_keep_size`로 상한을 두면

(실험, 위 컨테이너에서 `ALTER SYSTEM SET max_slot_wal_keep_size='32MB'` + `pg_reload_conf()`, 새 슬롯 `cdc_capped`, 2026-10-07)

```text
-- D1 약 10MB WAL 뒤
 cdc_capped | 0/D91E3F0   | reserved   | 10040 kB | safe_wal_size 29 MB |
-- D2 약 50MB WAL 더 쓴 뒤 (CHECKPOINT)
 cdc_capped |             | lost       |          |                     | wal_removed
-- D3
ERROR:  can no longer get changes from replication slot "cdc_capped"
DETAIL:  This slot has been invalidated because it exceeded the maximum reserved size.
-- 서버 로그
LOG:  invalidating obsolete replication slot "cdc_capped"
DETAIL:  The slot's restart_lsn 0/D91E3F0 exceeds the limit by 7216144 bytes.
HINT:  You might need to increase "max_slot_wal_keep_size".
```

- 상한을 넘자 체크포인트가 WAL을 지우고 슬롯을 무효화했다(`invalidation_reason = wal_removed`, 17 컬럼). 디스크는 지켰지만 **CDC는 끊겼다**. 이 슬롯으로는 다시 이어 받을 수 없다.
- `safe_wal_size`: "이 슬롯이 lost가 되기 전까지 더 쓸 수 있는 WAL 바이트". 상한이 -1(기본)이면 NULL이다(52.19). 알람 지표로 쓴다.
- PostgreSQL 17 문서 19.6: `max_slot_wal_keep_size` 기본 -1은 무제한 보존이다. 값을 정하면 `restart_lsn`이 현재 LSN보다 그만큼 뒤처진 슬롯은 필요한 WAL이 지워져 복제를 이어 가지 못할 수 있다.

MySQL은 반대 방향으로 깨진다.

| | PostgreSQL 17 슬롯 | MySQL 8.4 binlog |
|---|---|---|
| 보존을 정하는 것 | 슬롯의 `restart_lsn`(소비자가 멈추면 무한정) | `binlog_expire_logs_seconds`(기본 2592000초 = 30일, 19.1.6.4) |
| 커넥터가 오래 멈추면 | WAL이 쌓여 **디스크가 찬다** | binlog가 만료돼 지워진다 → 커넥터 위치가 사라진다 |
| 결과 | 디스크 풀 → DB 정지 위험([database/19 장애 2](../../database/19-wal-and-logging/2-summary.md)) | Debezium MySQL 문서: 커넥터가 실패하며 새 스냅샷이 필요하다고 알린다. `snapshot.mode=when_needed`면 자동 재스냅샷 |
| 상한을 두면 | `max_slot_wal_keep_size` → 슬롯 `lost` → 재스냅샷 | (보존 기간 자체가 상한) |

### 7. 전달 보장 — 정상일 때와 장애 뒤

- PostgreSQL 17 문서 47.2.2: 슬롯은 정상 동작에서 변경을 한 번씩 내보낸다. 그러나 슬롯 위치는 체크포인트 때만 디스크에 남는다. 크래시 뒤에는 앞 LSN으로 돌아가 최근 변경을 **다시 보낼 수 있다**. 중복 처리는 클라이언트 책임이다.
- Debezium PostgreSQL 문서 "Behavior when things go wrong": 정상 운영에서는 정확히 한 번 전달하지만, 장애에서 복구하는 동안은 중복을 낼 수 있다(at-least-once).
- 그래서 하류는 키 기반 upsert나 이벤트 위치(LSN) 비교로 **멱등하게** 반영한다([reliability/13](../../reliability/13-idempotency/2-summary.md), 실험 C).

## 쓰이는 자료구조·알고리즘

- **append-only 로그 + 오프셋** — WAL·binlog·Kafka 토픽은 끝에만 붙는 로그다. 소비자는 "어디까지 읽었나"(LSN, binlog 위치, Kafka 오프셋)만 기억하면 된다. [distributed/17](../../distributed/17-queues-logs-and-delivery-semantics/2-summary.md) · [distributed/21](../../distributed/21-kafka-internals/2-summary.md)
- **체크포인트** — 슬롯은 `confirmed_flush_lsn`(소비자가 확인한 곳)과 `restart_lsn`(다시 시작에 필요한 곳) 두 위치를 둔다. 커넥터 오프셋 저장도 같은 생각이다. WAL 체크포인트 자체는 [database/19 §6](../../database/19-wal-and-logging/2-summary.md).
- **해시 맵으로 하는 중복 제거** — 증분 스냅샷의 창 버퍼는 "PK → 스냅샷 행" 맵이다. 창 안 로그 이벤트의 키로 버퍼를 지운다. [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- **키 순서 청크(keyset)** — 증분 스냅샷은 "마지막 PK보다 큰 다음 N행"으로 나눠 읽는다. 대량 작업의 keyset 청크와 같은 방식이다. [database/34 §3](../../database/34-large-backfill-and-batch-dml/2-summary.md)
- **키별 마지막 값만 남기기(compaction)** — LSM 트리의 compaction과 같은 발상이다. [data-structure/24-lsm-tree](../../data-structure/24-lsm-tree/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 도입 전 점검표

- PostgreSQL 17
  - `wal_level=logical`(재시작 필요).
  - 캡처할 테이블에 기본 키가 있나. 없으면 `REPLICA IDENTITY FULL`을 검토한다(WAL 증가 감수).
  - `max_slot_wal_keep_size`를 정한다. 기본 -1(무제한)은 "디스크 풀 위험", 값을 두면 "슬롯 lost → 재스냅샷 위험"이다. 둘 중 무엇을 감수할지 팀이 정한다.
  - 캡처 대상이 아닌 DB·테이블에 쓰기가 몰리면 슬롯이 전진하지 못할 수 있다. Debezium 문서는 `heartbeat.interval.ms`와 `heartbeat.action.query`로 주기적인 변경을 만들라고 권한다.
- MySQL 8.4
  - `binlog_format=ROW`, `binlog_row_image=FULL`(Debezium 요구사항).
  - `binlog_expire_logs_seconds` ≥ "커넥터가 멈춰 있을 수 있는 최대 시간 + 여유".

### 2. 진단 쿼리와 출력 읽기 (PostgreSQL 17)

```sql
SELECT slot_name, active, inactive_since, wal_status,
       pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS retained,
       pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), confirmed_flush_lsn)) AS unconfirmed,
       pg_size_pretty(safe_wal_size) AS safe_wal_size, invalidation_reason
FROM pg_replication_slots;

SELECT pg_size_pretty(sum(size)) AS pg_wal, count(*) AS files FROM pg_ls_waldir();  -- 슈퍼유저 또는 pg_monitor
```

- 읽는 법
  - `active=f`이고 `inactive_since`가 오래됐다 → 커넥터가 죽었거나 버려진 슬롯이다.
  - `retained`가 계속 오른다 + `wal_status=extended` → 디스크를 먹는 중이다.
  - `wal_status=unreserved` → 다음 체크포인트에 필요한 WAL이 지워질 수 있다. `lost` → 이미 끊겼다(52.19).
  - `safe_wal_size`가 0에 다가간다 → 곧 `lost`.
- 알람: `retained` 크기, `inactive_since` 경과 시간, `wal_status IN ('unreserved','lost')`.

### 3. 하류 반영 — 키 기반 upsert + 위치 비교

```sql
-- 하류 테이블에 마지막으로 반영한 원천 위치를 함께 둔다
CREATE TABLE customer_replica (
  id int PRIMARY KEY, name text, tier text,
  source_lsn pg_lsn NOT NULL, deleted boolean NOT NULL DEFAULT false
);
-- 변경 이벤트 하나 반영: 더 새로운 위치일 때만 덮어쓴다 (재전송·순서 뒤바뀜 흡수)
INSERT INTO customer_replica AS r (id, name, tier, source_lsn, deleted)
VALUES (:id, :name, :tier, :lsn::pg_lsn, :op = 'd')
ON CONFLICT (id) DO UPDATE
   SET name = EXCLUDED.name, tier = EXCLUDED.tier,
       source_lsn = EXCLUDED.source_lsn, deleted = EXCLUDED.deleted
 WHERE r.source_lsn < EXCLUDED.source_lsn;
```

- 삭제는 행을 바로 지우는 대신 `deleted=true`로 둘 수도 있다. 그러면 늦게 온 옛 INSERT가 지운 행을 되살리지 못한다. 실제 삭제는 나중에 일괄로 한다.
- 소비 코드는 모르는 `op` 값(예: `t` truncate, `m` message)을 **조용히 건너뛰지 않는다**. 실패시키거나 별도 큐로 보낸다(Debezium 문서의 `op` 값: c·u·d·r·t·m).

### 4. 숫자로 대조한다

- CDC는 에러 없이 행을 잃거나(B1) 늘릴 수(B2·A) 있다. 원천과 하류의 `count(*)`·합계를 주기적으로 비교한다.
- 대조 차이가 나면 재스냅샷(Debezium은 증분 스냅샷 신호)으로 그 테이블만 다시 맞춘다. 단 스냅샷은 지금 있는 행만 `read`로 내보낸다. 원천에서 이미 지운 키는 삭제 이벤트가 오지 않아 upsert 하류에 남으므로, 키 대조로 따로 지우거나 하류를 비우고 다시 적재한다. 대조·관측 지표는 [10번](../10-data-quality-and-data-observability/2-summary.md)의 주제다.

## 장애 시나리오와 대처

### 1. 커넥터가 멈춘 사이 슬롯이 WAL을 붙잡는다 → PG 디스크가 가득 찬다 (⚠)

- **현상**: 운영 DB 디스크 사용률이 며칠에 걸쳐 꾸준히 오른다. 결국 쓰기가 멈추고 DB가 내려갈 수 있다.
- **보이는 형태**: `pg_replication_slots`에 `active=f`인 슬롯, `inactive_since`가 며칠 전, `retained`가 수십~수백 GB, `wal_status=extended`. `pg_ls_waldir()` 합계가 `max_wal_size`보다 훨씬 크다(실험 D: 48 MB → 160 MB).
- **원인**: 커넥터가 죽었거나 내려간 뒤 슬롯을 지우지 않았다. 슬롯은 소비자 상태를 모른 채 `restart_lsn` 이후 WAL을 붙잡는다(47.2.2).
- **대처**
  - 커넥터를 살려 따라잡게 한다. 다시 쓸 일이 없으면 `pg_drop_replication_slot()`.
  - `max_slot_wal_keep_size` 상한 + `retained`·`safe_wal_size` 알람. 디스크가 이미 찼을 때의 처리는 [database/19 장애 2](../../database/19-wal-and-logging/2-summary.md)를 따른다.

### 2. binlog 보존 기간이 지났다 → 전체 재스냅샷이 필요하다 (⚠)

- **현상**: 주말 동안 내려 둔 MySQL 커넥터가 다시 뜨지 않는다.
- **보이는 형태**: 커넥터가 실패 상태로 멈추고 "새 스냅샷이 필요하다"는 오류를 남긴다(Debezium MySQL 문서). 하류 데이터는 마지막 반영 시점에 멈춰 있다.
- **원인**: 커넥터가 저장한 binlog 위치의 파일이 `binlog_expire_logs_seconds` 만료 뒤 자동 삭제됐다(MySQL 8.4: 만료된 파일은 서버 시작·binlog flush 때 지워질 수 있다. `binlog_expire_logs_auto_purge=OFF`면 자동 삭제하지 않는다). 그 사이 변경을 로그로는 복원할 수 없다.
- **대처**
  - 재스냅샷한다(`snapshot.mode=when_needed`면 새 초기 스냅샷을 자동으로 시작). 증분 스냅샷은 스트리밍과 함께 도는 기능이라, 위치를 잃은 커넥터에 바로 쓸 수 없다. 큰 테이블은 오프셋을 지우고 `snapshot.mode=no_data`로 현재 위치부터 스트리밍을 다시 세운 뒤 증분 스냅샷으로 나눠 읽을 수 있다(Debezium MySQL 문서의 "스키마 스냅샷 + 증분 스냅샷" 절차, 원래는 캡처 테이블을 추가할 때의 절차).
  - 스냅샷은 지금 있는 행만 내보낸다. 멈춘 사이 원천에서 지운 키는 하류에 남으므로 원천·하류 키를 대조해 따로 지운다(또는 하류를 비우고 다시 적재).
  - 예방: 보존 기간을 "최대 중단 시간 + 여유"보다 길게, 커넥터 지연 알람.

### 3. 스냅샷과 스트림 경계에서 중복·누락이 생긴다 (⚠)

- **현상**: 초기 적재 직후 하류의 행 수가 원천보다 조금 많거나 적다. 에러는 없다.
- **보이는 형태**: 같은 PK 행이 둘(덧붙이는 하류), 또는 적재 시각 근처에 만들어진 행 몇 개가 없다. 실험 B1(누락)·B2(중복).
- **원인**: 스냅샷 시점과 스트림 시작 위치가 어긋났다. 직접 만든 파이프라인(덤프 → 슬롯 생성)에서 흔하다. Debezium PostgreSQL 문서도 블로킹 스냅샷(신호로 띄우는 ad hoc 스냅샷의 한 종류)은 신호를 보낸 때와 스트리밍이 멈추고 스냅샷이 시작되는 때 사이 지연 때문에 스냅샷과 겹치는 이벤트를 낼 수 있다고 적는다("Possible duplicates"). 증분 스냅샷도 at-least-once다(블로그 2021-10-07).
- **대처**
  - 슬롯 생성이 내보낸 스냅샷(`EXPORT_SNAPSHOT`)으로 덤프한다(B3).
  - 하류는 PK로 upsert한다. 중복은 흡수되고(실험 C), 누락은 대조로 찾는다.

### 4. 삭제 이벤트를 처리하지 않는다 → 하류에 지운 행이 남는다 (⚠)

- **현상**: 원천에서 탈퇴·삭제한 상품이 검색 결과·웨어하우스 집계에 계속 나온다.
- **보이는 형태**: 하류 `count(*)`가 원천보다 꾸준히 많고 차이가 시간에 따라 커진다. 실험 C의 방식 A: 원천 6행·650 → 하류 9행·950.
- **원인**: 소비자가 `op=d`나 tombstone(`value=null`)을 무시하거나, null 값 역직렬화에서 실패한 레코드를 건너뛰었다. compaction 토픽을 처음부터 읽는 소비자가 `delete.retention.ms`(기본 1일)보다 오래 걸려 tombstone을 놓쳤을 수도 있다.
- **대처**
  - delete·tombstone 처리를 소비 코드의 필수 분기로 둔다. 개인정보 삭제 요청이 걸리면 삭제 전파 확인은 [12번](../12-data-retention-and-erasure/2-summary.md)의 주제다.
  - 기본 키 없는 테이블은 `REPLICA IDENTITY FULL` 또는 키 추가.

### 5. 상한을 걸었더니 CDC가 조용히 끊겼다

- **현상**: 디스크 풀은 막았는데, 며칠 뒤 하류 데이터가 어느 시점부터 갱신되지 않은 것을 발견한다.
- **보이는 형태**: `wal_status=lost`, `invalidation_reason=wal_removed`, 서버 로그 `invalidating obsolete replication slot`, 커넥터 쪽 `can no longer get changes from replication slot`(실험 E).
- **원인**: 커넥터 지연이 `max_slot_wal_keep_size`를 넘었다. 체크포인트가 필요한 WAL을 지우고 슬롯을 무효화했다.
- **대처**: 슬롯을 새로 만들고 재스냅샷한다. `safe_wal_size`가 줄어드는 단계에서 알람을 받아 미리 커넥터를 살린다.

## 핵심 문장

- CDC는 테이블을 다시 묻는 대신 DB가 이미 쓰는 변경 로그(WAL·binlog)를 구독해, 삭제와 중간 변경까지 커밋 순서대로 옮긴다.
- 초기 스냅샷과 스트림 시작 위치가 어긋나면 에러 없이 행이 빠지거나 겹친다. 슬롯이 내보낸 스냅샷으로 맞추고, 하류는 키로 upsert한다.
- PostgreSQL 슬롯은 소비자가 멈춰도 WAL을 붙잡아 디스크를 채운다. 상한(`max_slot_wal_keep_size`)을 두면 대신 슬롯이 `lost`가 되어 재스냅샷이 필요하다.
- MySQL binlog는 보존 기간이 지나면 자동 삭제될 수 있으므로, 커넥터가 그보다 오래 멈춰 저장한 위치의 파일이 지워지면 재스냅샷이다.
- 삭제는 delete 이벤트와 tombstone으로 오고, PostgreSQL 논리 디코딩은 DDL을 내보내지 않는다. 소비자가 둘 다 다뤄야 숫자가 맞는다.
- 로그 기반 CDC도 장애 뒤에는 at-least-once다.

## 관련 주제·근거

- 선행
  - [01-system-of-record-and-derived-data](../01-system-of-record-and-derived-data/2-summary.md) — 원천과 파생, 파생 = 원천 로그의 폴드
  - [database/19-wal-and-logging](../../database/19-wal-and-logging/2-summary.md) — WAL, 체크포인트, WAL 디스크 풀
  - [distributed/16-outbox-and-dual-write](../../distributed/16-outbox-and-dual-write/2-summary.md) — 이중 쓰기 문제, outbox, CDC 한 줄(이 노트가 이어 받음)
- 후속·연결
  - [06-event-data-modeling](../06-event-data-modeling/2-summary.md) — CDC 이벤트(상태 변경)와 도메인 이벤트의 차이, 봉투
  - [07-batch-stream-architectures](../07-batch-stream-architectures/2-summary.md) — 로그를 처음부터 다시 읽는 재처리
  - [09-data-contracts-and-schema-registry](../09-data-contracts-and-schema-registry/2-summary.md) — DDL·스키마 변경을 하류와 맞추기
  - [10-data-quality-and-data-observability](../10-data-quality-and-data-observability/2-summary.md)(대조·관측), [12-data-retention-and-erasure](../12-data-retention-and-erasure/2-summary.md)(삭제 전파)
  - [distributed/17](../../distributed/17-queues-logs-and-delivery-semantics/2-summary.md)(전달 보장), [distributed/21](../../distributed/21-kafka-internals/2-summary.md)(세그먼트·보존), [reliability/13](../../reliability/13-idempotency/2-summary.md)(멱등 반영), [database/26](../../database/26-schema-migration/2-summary.md)(DDL 순서), [database/34](../../database/34-large-backfill-and-batch-dml/2-summary.md)(keyset 청크)
- 문서
  - Debezium Features (stable = 3.7) <https://debezium.io/documentation/reference/stable/features.html>
  - Debezium PostgreSQL connector (stable) — Snapshots(`initial` 흐름, `snapshot.mode`), Replica identity, Tombstone events, `tombstones.on.delete`, `op` 값, WAL disk space consumption(`confirmed_flush_lsn`·`restart_lsn`, heartbeat), Behavior when things go wrong(at-least-once), "Logical decoding does not support DDL changes" <https://debezium.io/documentation/reference/stable/connectors/postgresql.html>
  - Debezium MySQL connector (stable) — `binlog_format=ROW`·`binlog_row_image=FULL`, 로그가 지워지면 새 스냅샷 필요·`when_needed` <https://debezium.io/documentation/reference/stable/connectors/mysql.html>
  - Debezium 블로그 2021-10-07 "Incremental Snapshots in Debezium"(Jiri Pechanec) — DBLog 워터마크, 청크 1,024, 창 버퍼, 재시작, 제약 <https://debezium.io/blog/2021/10/07/incremental-snapshots/>
  - PostgreSQL 17 문서 47.2 Logical Decoding Concepts(47.2.2 슬롯·크래시 뒤 재전송·Caution, 47.2.5 Exported Snapshots) <https://www.postgresql.org/docs/17/logicaldecoding-explanation.html> · F.43 test_decoding <https://www.postgresql.org/docs/17/test-decoding.html> · 19.6 Replication(`max_slot_wal_keep_size` 기본 -1) <https://www.postgresql.org/docs/17/runtime-config-replication.html> · 52.19 `pg_replication_slots`(`wal_status` 네 값, `safe_wal_size`, `inactive_since`, `invalidation_reason`) <https://www.postgresql.org/docs/17/view-pg-replication-slots.html>
  - MySQL 8.4 Reference Manual 19.1.6.4 Binary Logging Options and Variables — `binlog_expire_logs_seconds` 기본 2592000(30일). 원 페이지가 오류 화면이라 Internet Archive 2025 사본으로 확인 <https://dev.mysql.com/doc/refman/8.4/en/replication-options-binary-log.html>
  - Kafka 4.1 문서 — Topic Configs(`cleanup.policy`, `delete.retention.ms` 1일) <https://kafka.apache.org/41/configuration/topic-configs/> · Design "Log Compaction"(tombstone) <https://kafka.apache.org/41/design/design/>
  - PostgreSQL 17 문서 29.1 Publication(replica identity 없는 테이블의 UPDATE·DELETE 오류) <https://www.postgresql.org/docs/17/logical-replication-publication.html> · 53.5.3 Logical Replication Protocol Message Flow(Relation 메시지) <https://www.postgresql.org/docs/17/protocol-logical-replication.html> · Kafka 4.1 Operations "Modifying topics"(파티션 추가와 키 배정) <https://kafka.apache.org/41/operations/basic-kafka-operations/> · MySQL 8.4 `binlog_expire_logs_auto_purge`(같은 19.1.6.4 페이지)
  - DDIA 1판 11장 "Stream Processing" — 절 "Databases and Streams › Change Data Capture"(O'Reilly 목차, Internet Archive 2024 사본으로 확인)
- 실험 목록(scratchpad `de/05/exp05/`, 전용 컨테이너 `sn-de-w05-pg`, `--network none`, 2026-10-07)
  - A `a.sql` — PostgreSQL 17.11 `test_decoding`: 커밋 묶음, 롤백 제외, REPLICA IDENTITY DEFAULT vs FULL, DDL 미출력, TRUNCATE
  - B `b.sh` — 스냅샷/슬롯 순서 세 가지(누락·중복·`EXPORT_SNAPSHOT`)
  - C `CdcApply.java` — OpenJDK 21.0.12, append+삭제 무시 vs upsert+삭제
  - D `c.sh` — 비활성 슬롯이 붙잡은 `pg_wal`(48 MB → 160 MB → 48 MB), `restart_lsn`과 `confirmed_flush_lsn`의 차이
  - E `d.sh` — `max_slot_wal_keep_size=32MB`에서 슬롯 `lost`·`wal_removed`·get_changes 오류·서버 로그
