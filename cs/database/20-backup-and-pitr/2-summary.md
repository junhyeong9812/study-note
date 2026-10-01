# database/20-backup-and-pitr — 백업과 시점 복구(PITR): 논리·물리 백업, WAL 아카이브, 복원 검증 — 정리 (힌트)

## 해결하는 문제

WAL(19번)은 **서버가 죽었을 때** 커밋된 것을 살린다.\
그런데 디스크가 통째로 사라지거나, 사람이 `DROP TABLE`을 치면 WAL 재생은 도움이 안 된다.\
WAL은 그 `DROP`까지 충실히 기록하고, 복제본(32번)은 그 `DROP`을 충실히 따라 한다.

```text
  사고 종류                     크래시 복구(19·42번)   복제본(32번)     백업 + PITR
  프로세스·OS 크래시              살린다                 -                -
  디스크·서버 소실                못 살린다              살린다(유실 가능)  살린다
  실수로 DROP / 잘못된 UPDATE     못 살린다              같이 망가진다      "사고 직전"으로 되돌린다
  랜섬웨어·버그로 오염된 데이터    못 살린다              같이 망가진다      오염 전 시점으로 되돌린다
```

- *RPO(Recovery Point Objective)*: 사고가 나면 **얼마만큼의 최근 데이터**를 잃어도 되나.
- *RTO(Recovery Time Objective)*: 사고가 나면 **얼마 안에** 다시 서비스해야 하나.

쉬운 예: 문서 편집기의 "버전 기록"이다.
- 파일을 매일 밤 통째로 복사해 둔다(전체 백업).
- 그 사이의 모든 입력을 따로 기록해 둔다(WAL 아카이브).
- 그러면 "어제 밤 복사본 + 오늘 오후 2시 59분까지의 입력"으로 **아무 시점**이나 되살릴 수 있다.

똑같은 구조다. **베이스 백업 + 연속된 로그**가 PITR(point-in-time recovery, 시점 복구)이다.

실무 예: GitLab.com 2017-01-31 사고.
- 엔지니어가 복제 재구성 중 **프라이머리**의 데이터 디렉터리를 지웠다. 약 300 GB가 지워진 뒤 멈췄다.
- 매일 돌던 `pg_dump` 백업은 **오류로 끝나고 있었고, S3 버킷은 비어 있었다.** 9.6 서버에 9.2 `pg_dump`를 써서 오류로 끝났고, 실패 알림 메일은 수신 측에서 거절되어 아무도 몰랐다.
- 결국 6시간 전 수동 LVM 스냅숏으로 복구했다. 17:20 UTC 이후의 DB 변경을 잃었다. 잃은 구간은 포스트모템 서두에 "17:20~00:00 UTC", 「Data loss impact」 절에 "17:20~23:30 UTC"로 다르게 적혀 있다(57번).
- 교훈: **복원해 본 적 없는 백업은 백업이 아니다.**

## 동작·원리

### 1. 세 가지 백업 방식

```text
  논리 백업                     물리 백업                      연속 아카이브(PITR)
  pg_dump / mysqldump           pg_basebackup / 파일 복사        베이스 백업 + WAL(binlog) 연속본
  ┌──────────────┐              ┌──────────────┐               ┌──────────────┐  ┌──┬──┬──┬──┐
  │ CREATE TABLE │              │ base/…/1663  │               │ 베이스 백업   │ +│W1│W2│W3│…│
  │ COPY … 데이터 │              │ pg_wal/ …    │               │ (T0 시점)     │  └──┴──┴──┴──┘
  └──────────────┘              └──────────────┘               └──────────────┘
  SQL 문장으로 다시 만든다          바이트 그대로 복사                T0 이후 아무 시점으로 재생
  버전·플랫폼 이식 쉬움             빠르다, 같은 메이저 버전·플랫폼     RPO를 분 단위 이하로
  복원 = 재적재(느림), 인덱스 재생성   복원 = 파일 제자리 + WAL 재생       복원 = 베이스 + 목표 시점까지 재생
  "백업 시점" 하나로만 복원          "백업 시점" 하나로만 복원            목표 시점을 고른다
```

- *논리 백업*: 데이터를 SQL(또는 그에 준하는 형식)로 뽑는다. 다른 버전·다른 머신으로 옮기기 쉽다.
- *물리 백업*: 데이터 파일을 그대로 복사한다. MySQL 8.4 문서는 물리 백업이 논리 백업보다 빠르고 출력이 작다고 적는다(9.1 Backup and Recovery Types).
- *베이스 백업(base backup)*: 연속 아카이브의 출발점이 되는 물리 백업. PostgreSQL은 `pg_basebackup`으로 뜬다.

### 2. 논리 백업은 어떻게 "한 시점"을 찍나

```text
  시간 ─────────────────────────────────────────────>
  pg_dump   BEGIN(스냅숏 S) ── 테이블 A 읽기 ── 테이블 B 읽기 ── 끝
  다른 세션         UPDATE A  COMMIT      INSERT B  COMMIT
                    └ S 이후 커밋이라 dump에 안 보인다(MVCC 16번)
```

- PostgreSQL 17 `pg_dump`는 동시 사용 중에도 일관된 백업을 만들고, 다른 사용자(읽기·쓰기)를 막지 않는다(`pg_dump` 문서).
  - 대신 덤프할 테이블마다 `ACCESS SHARE` 락을 잡는다. 이 락은 `ALTER TABLE`·`DROP TABLE` 같은 `ACCESS EXCLUSIVE`와 충돌한다.
- MySQL 8.4 `mysqldump --single-transaction`은 격리 수준을 REPEATABLE READ로 두고 `START TRANSACTION`을 보낸 뒤 덤프한다(`mysqldump` 문서).
  - InnoDB 테이블만 일관되게 덤프된다. MyISAM·MEMORY 테이블은 덤프 중에도 바뀔 수 있다.
  - 덤프 중 다른 연결이 `ALTER`·`CREATE`·`DROP`·`RENAME`·`TRUNCATE TABLE`을 쓰면 덤프 내용이 틀리거나 실패할 수 있다.
  - 이 옵션 없이 기본값(`--opt` 안의 `--lock-tables`)으로 돌리면 덤프 동안 테이블 읽기 락(`READ LOCAL`)을 잡는다. MyISAM은 이 락 아래서도 동시 INSERT가 될 수 있지만 그 밖의 쓰기는 막힌다.
  - `--source-data`를 함께 쓰면 시작할 때 binlog 좌표를 읽느라 `FLUSH TABLES WITH READ LOCK`(전역 읽기 락)을 **짧게** 잡는다. 그 뒤 덤프는 락 없이 간다. 이때 긴 갱신 문장이 돌고 있으면 그것이 끝날 때까지 서버가 멈춘 듯 보일 수 있다(`mysqldump` 문서).
- `pg_dump`는 **한 DB만** 뜬다. 역할(role)·테이블스페이스 같은 클러스터 전역 객체는 빠진다. 클러스터 전체를 받으려면 `pg_dumpall` 하나로 뜨거나, DB마다 `pg_dump`를 뜨고 전역 객체만 `pg_dumpall --globals-only`로 따로 뜬다(PostgreSQL 25.1).

### 3. 백업 중 락 — 누가 누구를 막나

로컬 재현(예시, PostgreSQL 17.11): 긴 읽기 트랜잭션(덤프와 같은 `ACCESS SHARE`)이 도는 중에 `ALTER TABLE`이 들어오고, 그 뒤에 평범한 `SELECT`가 왔다.

```text
   pid  | blocked_by | wait_event_type | query
  ------+------------+-----------------+---------------------------------------
   5129 | {}         | Timeout         | begin isolation level repeatable read; select …   ← 덤프 역할
   5136 | {5129}     | Lock            | alter table orders add column note text          ← ACCESS EXCLUSIVE 대기
   5150 | {5136}     | Lock            | select count(*) from orders                      ← ALTER 뒤에 줄 섬

  pg_locks:  5129 AccessShareLock granted=t
             5136 AccessExclusiveLock granted=f
             5150 AccessShareLock granted=f
```

- 덤프 자체는 `SELECT`를 막지 않는다.
- 그러나 **덤프 + DDL 하나**가 겹치면, DDL의 대기열 뒤로 모든 읽기가 줄을 선다. 서비스가 멈춘 것처럼 보인다.
- 반대 방향도 있다. 이미 `ACCESS EXCLUSIVE`가 잡혀 있으면 덤프가 기다린다. `pg_dump --lock-wait-timeout=1s`로 돌리면(로컬 재현) 다음처럼 실패하고 **exit code 1**을 낸다.

```text
  pg_dump: error: query failed: ERROR:  canceling statement due to statement timeout
  pg_dump: detail: Query was: LOCK TABLE public.orders IN ACCESS SHARE MODE
  exit=1
```

### 4. 연속 아카이브와 PITR — 그림 한 장

```text
  T0            T1           T2          T3(사고: DROP TABLE)      지금
  │ 베이스 백업  │             │            │                        │
  ▼             ▼             ▼            ▼                        ▼
  [base]──WAL 000…9A──WAL 000…9B─────────X─────────────────────────
                                          ↑
                   복원: base를 풀고 WAL을 X "직전"까지 재생 → 새 타임라인 2에서 운영 재개

  WAL 파일 이름:  00000001 00000000 0000009B
                 └ 타임라인 ┘└─ 세그먼트 번호 ─┘
```

- PostgreSQL 17에서 아카이브를 켜려면 `wal_level`을 `replica` 이상, `archive_mode = on`, 그리고 `archive_command` 또는 `archive_library`를 둔다(25.3.1).
  - *archive_command*: WAL 세그먼트가 찰 때마다 서버가 부르는 셸 명령. `%p`는 파일 경로, `%f`는 파일 이름으로 바뀐다.
- **exit code가 계약이다.** 명령은 성공했을 때만 0을 돌려줘야 한다. 0을 받으면 서버는 그 세그먼트를 지우거나 재활용한다. 0이 아니면 성공할 때까지 주기적으로 다시 시도한다(25.3.1).
  - 그래서 "복사는 실패했는데 0을 돌려주는" 스크립트는 WAL을 조용히 잃는다.
  - 문서는 아카이브 명령이 **이미 있는 파일을 덮어쓰지 않게** 만들라고 권한다. 예로 GNU `cp -i`는 대상이 있어도 0을 돌려주니 믿지 말라고 적는다.
- 아카이브가 계속 실패하면 `pg_wal/`에 세그먼트가 쌓인다. 결국 디스크가 찬다(25.3.1).
- 복원할 때(25.3.5)
  1. 베이스 백업 파일을 제자리에 푼다(소유자는 DB 사용자).
  2. `restore_command`를 설정한다. 아카이브에서 WAL을 꺼내 오는 명령이다. 없는 파일을 요청받으면 0이 아닌 값을 돌려줘야 한다. 이것은 정상 동작이다.
  3. 목표 시점을 정한다. `recovery_target`(=`immediate`)·`recovery_target_time`·`recovery_target_xid`·`recovery_target_lsn`·`recovery_target_name` 중 **하나만** 쓸 수 있다(19.5.6).
  4. 데이터 디렉터리에 `recovery.signal` 파일을 만들고 서버를 시작한다.
- `recovery_target_inclusive`(기본 `on`)는 목표 트랜잭션을 **포함할지** 정한다. 실수한 트랜잭션을 목표로 잡았다면 `off`로 둬야 그 직전에 멈춘다.
- `recovery_target_action`의 기본값은 `pause`다. 목표에 닿으면 재생을 멈추고 조회를 받는다(`hot_standby`가 켜져 있을 때. 꺼져 있으면 `pause`는 `shutdown`처럼 동작한다). 맞는 시점이면 `pg_wal_replay_resume()`으로 끝낸다. 더 나중 시점이 필요하면 서버를 내리고 목표를 **더 나중**으로 바꿔 재시작해 이어 간다. 더 이른 시점이 필요하면 베이스 백업 복원부터 다시 한다(이미 재생한 것은 되돌릴 수 없다, 19.5.6).
- 복구가 끝나면 **새 타임라인**이 생긴다. 타임라인 ID가 WAL 파일 이름 앞 8자리에 들어가므로 새 기록이 옛 기록을 덮어쓰지 않는다(25.3.6).

### 5. 사고 지점 찾기 — WAL과 binlog를 직접 읽는다

PITR의 실제 어려움은 "몇 시 몇 분"이 아니라 **정확히 어느 트랜잭션**인가다.

로컬 재현(예시, PostgreSQL 17.11): `w20` DB에서 `orders`를 만들고 `DROP TABLE orders`를 쳤다. `pg_waldump`로 그 구간을 봤다(다른 DB의 기록이 섞여 있다).

```text
  rmgr: Transaction … tx: 1521, lsn: 0/9B697988, … desc: COMMIT 2026-09-30 22:17:58.682794 UTC
  rmgr: Standby     … tx: 1525, lsn: 0/9B697BB8, … desc: LOCK xid 1525 db 26425 rel 26626
  rmgr: Transaction … tx: 1525, lsn: 0/9B698090, … desc: COMMIT 2026-09-30 22:17:58.783747 UTC;
                                                    rels: base/26425/26626 base/26425/26629; …
                        └ db 26425 = w20, 26626 = orders 파일. 이 커밋이 DROP이다.
```

- 목표: `recovery_target_xid = '1525'` + `recovery_target_inclusive = off` → 1525 직전까지 재생.
- 시간으로 잡으면 같은 밀리초에 다른 세션의 커밋이 끼어 있을 수 있다. xid·LSN이 더 정확하다.

로컬 재현(예시, MySQL 8.4.10): `mysqldump --single-transaction --source-data=2`로 덤프를 뜨면 덤프 파일 머리에 binlog 좌표가 주석으로 남는다.

```text
  -- CHANGE REPLICATION SOURCE TO SOURCE_LOG_FILE='binlog.000002', SOURCE_LOG_POS=94422530;
```

그 뒤 INSERT·UPDATE·(실수)DELETE를 하고 `SHOW BINLOG EVENTS`로 봤다.

```text
  Pos       Event_type   End_log_pos  Info
  94422530  Anonymous_Gtid 94422609
  …         Write_rows     94422779   table_id: 353 (w20.orders)      ← INSERT
  …         Xid            94422810   COMMIT
  94422810  …              …          Update_rows                     ← UPDATE
  …         Xid            94423109   COMMIT
  94423109  Anonymous_Gtid 94423188                                    ← 여기서 멈춘다
  …         Delete_rows    94423385   ← 실수한 DELETE
```

- 복원 = 덤프 재적재 → `mysqlbinlog --start-position=94422530 --stop-position=94423109 binlog.000002 | mysql`(MySQL 9.5.2 Point-in-Time Recovery Using Event Positions 방식).
- 이 컨테이너에는 `mysqlbinlog`가 없어 재생 단계는 돌리지 못했다. 덤프 재적재는 별도 DB에서 돌려 3행·합계 60을 확인했다.
- `binlog_format`은 이 서버에서 `ROW`다. 행 이벤트라서 SQL 원문이 안 보인다. `mysqlbinlog -v`(`--verbose`)로 행 값을 주석 형태의 "의사 SQL"로 풀어 본다(`mysqlbinlog` Row Event Display 문서, 이 환경에서는 미실행).

### 6. 증분 백업(PostgreSQL 17 신규)

```text
  full(월)          incr(화)            incr(수)
  [전체 파일] ──▶ [주로 바뀐 블록] ──▶ [주로 바뀐 블록]
        └──────── pg_combinebackup ────────┘ → 합성된 전체 백업 → 여기에 WAL 재생
```

- `pg_basebackup --incremental=<이전 백업의 manifest>`로 뜬다. 서버 17 이상에서만 된다(`pg_basebackup` 문서).
- "주로"인 이유: 관계(테이블·인덱스)가 아닌 파일은 통째로 담고, 관계 파일도 **일부만** 바뀐 블록짜리 증분 파일로 바뀐다(25.3.3).
- 서버에 `summarize_wal = on`(기본 `off`)이 필요하다. 요약 파일이 없으면 증분 백업은 실패한다(19.5.7, 25.3.3).
- 복원에는 **앞선 모든 백업**이 필요하다. PostgreSQL은 어떤 백업이 아직 필요한지 추적하지 않는다. 사슬 중간을 지우면 뒤 증분들이 전부 쓸모없어진다(25.3.3).

## 쓰이는 자료구조·알고리즘

- **추가 전용 로그(WAL·binlog)** — 변경을 순서대로 쌓는다. 재생은 "시작점에서 목표 지점까지 순서대로 다시 적용"이다. 로그가 한 칸이라도 빠지면 그 뒤는 재생할 수 없다.
- **LSN·binlog 좌표** — 로그 안의 위치(바이트 오프셋). 목표 시점을 시간 대신 위치로 정확히 찍는다.
- **MVCC 스냅숏** — 논리 덤프가 락 없이 한 시점을 보는 방법([16-mvcc](../16-mvcc/2-summary.md)).
- **manifest + 체크섬** — `pg_basebackup`이 남기는 `backup_manifest`에는 기본으로 파일별 CRC32C 체크섬이 있다(`--manifest-checksums=NONE`이면 없다). `pg_verifybackup`이 이것으로 파일 누락·손상을 찾고(의도적 변조까지 막으려면 SHA 계열 체크섬을 고른다, `pg_basebackup` 문서), 필요한 WAL이 읽히는지 `pg_waldump`로 파싱해 본다([os/33-data-integrity-checksums](../../os/33-data-integrity-checksums/2-summary.md)).
- **블록 단위 변경 요약(WAL summary)** — 증분 백업이 "어느 블록이 바뀌었나"를 WAL에서 미리 요약해 둔 것.

## 적용 — 풀어나가는 법

### 1. 먼저 숫자를 정한다

```text
  RPO 24시간  → 매일 논리 덤프로 충분할 수 있다
  RPO 수 분   → 베이스 백업 + WAL 아카이브(PITR) 필요
  RPO 0       → 백업만으로는 불가. 동기 복제(32번) + 백업을 함께
  RTO 짧음    → 논리 덤프 재적재는 느리다(인덱스 재생성). 물리 백업·대기 복제본을 쓴다
```

- `archive_timeout`: WAL이 적게 쌓이는 서버는 세그먼트가 오래 안 차서 아카이브가 늦는다. 이 값으로 세그먼트 전환 주기의 상한을 둔다(PostgreSQL 28.5 — 체크포인트 파라미터가 아니라 이것을 조정하라고 적는다).

### 2. PostgreSQL — 최소 구성

```ini
# postgresql.conf (예시)
wal_level = replica
archive_mode = on
archive_command = 'test ! -f /mnt/archive/%f && cp %p /mnt/archive/%f'   # 문서 예시
```

```bash
# 베이스 백업 (manifest 포함, WAL 스트리밍 기본)
pg_basebackup -D /backup/base_2026-10-01 -X stream -c fast
pg_verifybackup /backup/base_2026-10-01           # 파일·체크섬·WAL 파싱 확인

# 논리 덤프 (소규모·이관용)
pg_dump -Fc -d app -f app.dump && echo ok          # exit code를 반드시 본다
pg_dumpall --globals-only > globals.sql            # 역할·테이블스페이스
pg_restore --list app.dump                         # 목록이 읽히는지
```

```ini
# 복원 서버의 postgresql.conf (예시)
restore_command = 'cp /mnt/archive/%f %p'
recovery_target_xid = '1525'
recovery_target_inclusive = off
recovery_target_action = pause        # 기본값. 확인 후 pg_wal_replay_resume()
```

### 3. MySQL — 덤프 + binlog

```bash
mysqldump --single-transaction --source-data=2 --routines --triggers app > app.sql
# 사고 후
mysql app < app.sql
mysqlbinlog --start-position=<덤프의 SOURCE_LOG_POS> --stop-position=<사고 직전> binlog.00000N | mysql app
```

- binlog 보존 기간이 백업 주기보다 짧으면 PITR 사슬이 끊긴다. 이 서버의 `binlog_expire_logs_seconds`는 2592000(30일)이었다(로컬 확인, MySQL 8.4.10).
- MySQL 8.4의 물리 백업 도구로는 MySQL Enterprise Backup(상용)이 문서에 나온다(9.1 Backup and Recovery Types). 오픈소스 대안은 이 노트 범위 밖이다.

### 4. 복원 검증을 일로 만든다

```text
  [매일] 백업 → [매일/매주] 격리된 서버에 자동 복원 → 검사 → 결과를 지표로
                                                     ├ exit code 0?
                                                     ├ 행 수·합계가 원본(같은 시점)과 같나
                                                     ├ 앱 스모크 쿼리가 도나
                                                     └ 걸린 시간 = 실제 RTO
```

- `pg_verifybackup` 문서 스스로 "이 도구를 써도 **시험 복원**을 하고 데이터가 맞는지 확인하라"고 적는다.
- 로컬 재현(예시, PostgreSQL 17.11): `pg_dump -Fc` → 새 DB에 `pg_restore` → `count(*)=1000`, `sum(amount)=5005000`으로 원본과 대조했다.
- 백업 작업의 **실패를 알리는 경로**도 시험한다. GitLab은 실패 메일이 DMARC로 거절되어 아무도 몰랐다.

## 장애 시나리오와 대처

### 1. 복원 테스트를 안 한 백업 → 사고 때 전부 무용

- **현상**: 사고가 나서 백업을 찾았는데 비어 있거나, 복원이 안 된다.
- **보이는 형태**
  - 백업 저장소가 비어 있다(GitLab: S3 버킷이 비어 있었다).
  - 백업 로그에 `pg_dump: error: …`. cron은 exit code 1로 끝났지만 알림이 닿지 않았다.
  - `pg_dump`의 메이저 버전이 서버보다 낮으면 덤프를 거부한다. 문서: `pg_dump`는 자기보다 **새 메이저 버전** 서버는 덤프하지 않는다.
- **원인**: 백업 "작업"만 돌리고 "결과"를 확인하지 않았다. 도구 버전·경로가 운영 서버와 달랐다.
- **대처**
  - 주기적 자동 복원 + 데이터 대조를 파이프라인으로 만든다(위 적용 4).
  - 백업 성공 여부를 exit code가 아니라 "복원된 결과"로 판정하고, 마지막 성공 시각을 지표로 경보한다.
  - 백업 수단을 여러 개 두되, **각각** 복원해 본다. GitLab 포스트모템이 적은 절차는 넷(`pg_dump`, 24시간 LVM 스냅숏, Azure 디스크 스냅숏, 복제)이었다. 그런데 Azure 스냅숏은 DB 서버에는 켜져 있지 않았고, 실제로 쓴 것은 작업 전에 수동으로 뜬 6시간 전 LVM 스냅숏이었다.

### 2. 아카이브 명령이 거짓 성공 → PITR 사슬에 구멍

- **현상**: 복원 중 WAL 재생이 중간에 멈추고, 목표 시점까지 못 간다.
- **보이는 형태**: 아카이브(와 `pg_wal/`)에 다음 세그먼트가 없어 재생이 거기서 멈춘다. 복구 목표를 지정했는데 목표 전에 WAL이 끝나면 `FATAL: recovery ended before configured recovery target was reached`로 서버가 내려간다(19.5.6, `xlogrecovery.c`). 아카이브 디렉터리에 WAL 파일 번호가 비어 있다.
- **원인**: `archive_command` 스크립트가 복사 실패에도 0을 돌려줬다. 서버는 그 세그먼트를 지웠다.
- **대처**
  - 스크립트는 `set -e`로 쓰고 마지막 명령의 exit code를 그대로 넘긴다. 문서 예시처럼 "있으면 거부(`test ! -f`)"를 넣는다.
  - `pg_stat_archiver`의 `failed_count`·`last_failed_wal`·`last_failed_time`을 감시한다(PostgreSQL 27.2). 문서는 WAL이 항상 순서대로 아카이브된다고 가정하지 말라고 적는다. `last_archived_wal`보다 오래된 파일이 모두 성공했다고 볼 수 없다.
  - 아카이브에서 세그먼트 번호가 연속인지 정기적으로 검사한다.

### 3. 백업 중 락 → 서비스가 멈춘 듯 보인다

- **현상**: 백업이 도는 밤마다 특정 테이블 요청이 줄줄이 타임아웃난다.
- **보이는 형태**: `pg_stat_activity`에 `wait_event_type = Lock`인 세션이 여럿이고, `pg_blocking_pids`를 따라가면 `ALTER TABLE` → 덤프 세션으로 이어진다(위 §3 재현). MySQL에서 `--single-transaction` 없이 덤프하면 `LOCK TABLES ... READ LOCAL` 때문에 쓰기가 멈춘다(MyISAM의 동시 INSERT만 예외).
- **원인**: 덤프의 `ACCESS SHARE` 락과 배포·마이그레이션의 DDL(`ACCESS EXCLUSIVE`)이 겹쳤다. DDL 뒤로 모든 읽기가 줄을 섰다.
- **대처**
  - 백업 시간과 DDL 배포 시간을 분리한다.
  - DDL에는 `SET lock_timeout = '3s'`를 걸어 오래 기다리지 않고 실패하게 한다([22-database-side-timeouts](../22-database-side-timeouts/2-summary.md)).
  - 덤프에는 `--lock-wait-timeout`을 걸어 락을 못 잡으면 바로 실패하게 한다.
  - MySQL InnoDB는 `--single-transaction`을 쓴다.

### 4. 증분 사슬의 중간 백업 삭제 → 뒤 백업 전부 무용

- **현상**: 수요일 증분으로 복원하려는데 `pg_combinebackup`이 실패한다.
- **보이는 형태**: 결합 단계에서 참조 백업을 찾지 못한다는 오류가 난다 [?] — 정확한 메시지는 확인하지 못했다.
- **원인**: 보존 정책 스크립트가 날짜만 보고 월요일 전체 백업을 지웠다. PostgreSQL은 백업 사이의 의존을 추적하지 않는다(25.3.3).
- **대처**: 보존 정책을 "사슬 단위"로 짠다. 가장 오래된 증분이 기대는 전체 백업이 사라지지 않게 한다.

### 5. 복제본을 백업으로 착각 → 실수가 복제본에도 그대로

- **현상**: `DELETE`를 잘못 쳤다. 복제본으로 페일오버했는데 거기도 지워져 있다.
- **원인**: 복제는 **변경을 전파**하는 장치다. 실수도 전파한다. GitLab 포스트모템도 복제는 페일오버용이지 재해 복구용이 아니었다고 적는다.
- **대처**: 복제와 별개로 PITR 가능한 백업을 둔다. 원본 §6 "백업 — 복제와 다르다"([05-ha-topology.md](../../systems/server-design/05-ha-topology.md))와 같은 결론이다.

## 핵심 문장

- 크래시 복구와 복제는 사람의 실수를 되돌리지 못한다. 실수 직전으로 가려면 베이스 백업 + 끊김 없는 WAL(binlog)이 있어야 한다.
- 논리 백업은 이식성, 물리 백업은 속도, 연속 아카이브는 "아무 시점" 복원을 산다. RPO·RTO를 먼저 정하고 고른다.
- `archive_command`·`restore_command`·백업 스크립트는 exit code가 계약이다. 거짓 0 하나가 사슬 전체를 끊는다.
- 사고 지점은 시각보다 xid·LSN·binlog 위치로 찍는 것이 정확하다. `recovery_target_inclusive = off`로 실수한 트랜잭션 직전에 멈춘다.
- 백업의 성공은 "작업이 돌았다"가 아니라 "복원해서 데이터를 대조했다"로 판정한다.

## 관련 주제·근거

- 선행: [19-wal-and-logging](../19-wal-and-logging/2-summary.md) — WAL 규칙
- 연결
  - database `42-recovery-aries-checkpoints` — 크래시 복구와 체크포인트 → [../42-recovery-aries-checkpoints/2-summary.md](../42-recovery-aries-checkpoints/2-summary.md)
  - database `32-replication-leader-follower` — 복제는 백업이 아니다 → [../32-replication-leader-follower/2-summary.md](../32-replication-leader-follower/2-summary.md)
  - [16-mvcc](../16-mvcc/2-summary.md) · [22-database-side-timeouts](../22-database-side-timeouts/2-summary.md)
  - database [57-db-incidents](../57-db-incidents/2-summary.md)(GitLab 2017 등 실사건)
  - [os/24-fsync-and-durability](../../os/24-fsync-and-durability/2-summary.md) · [os/33-data-integrity-checksums](../../os/33-data-integrity-checksums/2-summary.md)
  - [systems/server-design/05-ha-topology.md](../../systems/server-design/05-ha-topology.md) §1 RTO/RPO, §6 백업 — 복제와 다르다
- PostgreSQL 17 문서
  - 25.1 SQL Dump(`pg_dumpall --globals-only`) <https://www.postgresql.org/docs/17/backup-dump.html>
  - 25.3 Continuous Archiving and PITR(아카이브 exit code 계약·덮어쓰기 금지·`restore_command`·`recovery.signal`·타임라인·증분 백업) <https://www.postgresql.org/docs/17/continuous-archiving.html>
  - 19.5 WAL 설정(`recovery_target_*`, `recovery_target_inclusive` 기본 on, `recovery_target_action` 기본 pause·목표는 더 나중으로만 바꿔 이어 감·목표 전에 끝나면 FATAL, `summarize_wal` 기본 off) · 소스 `src/backend/access/transam/xlogrecovery.c`("recovery ended before configured recovery target was reached") <https://www.postgresql.org/docs/17/runtime-config-wal.html>
  - `pg_dump`(일관성·비차단·`--lock-wait-timeout`·새 메이저 서버 거부) <https://www.postgresql.org/docs/17/app-pgdump.html> · `pg_basebackup`(`--incremental`은 17 이상, `--manifest-checksums` 기본 CRC32C) <https://www.postgresql.org/docs/17/app-pgbasebackup.html> · `pg_verifybackup`(4단계 검증, 시험 복원 권고) <https://www.postgresql.org/docs/17/app-pgverifybackup.html> · `pg_waldump` <https://www.postgresql.org/docs/17/pgwaldump.html>
- MySQL 8.4 Reference Manual
  - `mysqldump`(`--single-transaction`, `--opt`·`--lock-tables`(`READ LOCAL`), `--source-data`(시작 시 `FLUSH TABLES WITH READ LOCK`)) <https://dev.mysql.com/doc/refman/8.4/en/mysqldump.html>
  - 9.5 Point-in-Time Recovery(binlog, 이벤트 위치) <https://dev.mysql.com/doc/refman/8.4/en/point-in-time-recovery-positions.html> · 9.1 Backup and Recovery Types <https://dev.mysql.com/doc/refman/8.4/en/backup-types.html>
- 사고: GitLab "Postmortem of database outage of January 31"(2017-02-10) <https://about.gitlab.com/blog/postmortem-of-database-outage-of-january-31/>
- 로컬 재현(PostgreSQL 17.11, MySQL 8.4.10): `pg_waldump`로 DROP 커밋의 xid·LSN 찾기, 덤프 유사 트랜잭션 + DDL 락 대기열(`pg_blocking_pids`), `pg_dump --lock-wait-timeout` 실패와 exit 1, `pg_dump -Fc`→`pg_restore` 대조, `mysqldump --source-data=2` 좌표와 `SHOW BINLOG EVENTS`로 DELETE 직전 위치 찾기, 덤프 재적재 대조
