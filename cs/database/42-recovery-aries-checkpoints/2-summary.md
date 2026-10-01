# database/42-recovery-aries-checkpoints — 크래시 복구: ARIES의 분석·재실행·취소와 체크포인트 — 정리 (힌트)

## 해결하는 문제

WAL(19번)은 "데이터 페이지보다 로그를 먼저 디스크에" 쓰는 규칙이다.\
그 규칙 덕분에 크래시 직후 디스크에는 **로그는 다 있고, 페이지는 뒤죽박죽**인 상태가 남는다.

```text
  크래시 직후 디스크                           원하는 상태
  페이지 P1: 커밋된 T2의 변경이 아직 없음         커밋된 것은 전부 있다   (지속성)
  페이지 P3: 커밋 안 된 T1의 변경이 이미 있음      커밋 안 된 것은 하나도 없다 (원자성)
```

- *STEAL*: 커밋 안 된 트랜잭션이 바꾼 dirty 페이지도 디스크에 내보낼 수 있다. 버퍼 풀이 자유로워지지만, 복구 때 **되돌리기(undo)**가 필요해진다.
- *NO-FORCE*: 커밋할 때 그 트랜잭션의 페이지를 디스크에 강제로 쓰지 않는다. 커밋이 빨라지지만, 복구 때 **다시 하기(redo)**가 필요해진다.

쉬운 예: 가계부 앱이 "메모장(로그)"에 먼저 적고, 장부(페이지)는 나중에 몰아서 고친다.
- 앱이 죽으면 장부에는 반쯤 옮긴 내용이 있다.
- 메모장을 처음부터 보며 "옮겨야 했는데 안 옮긴 것"은 옮기고, "취소된 거래인데 옮겨진 것"은 지운다.
- 메모장이 길면 복구가 오래 걸린다. 그래서 가끔 "여기까지는 장부에 다 옮겼다"는 표시(체크포인트)를 한다.

똑같은 구조다. **ARIES**는 STEAL + NO-FORCE 버퍼 관리 아래에서 이 복구를 하는 알고리즘이다(IBM, Mohan 외 1992 — CMU 15-445 L21).

실무 예
- PostgreSQL 로그: `database system was not properly shut down; automatic recovery in progress` → `redo starts at …` → `redo done at …`.
- 재시작이 수십 분 걸린다. 원인은 흔히 "마지막 체크포인트 이후 WAL이 너무 많다"이다.

## 동작·원리

### 1. LSN과 네 가지 포인터

```text
  로그(디스크)   ... [LSN 20 T1 UPDATE P1] [LSN 30 T2 UPDATE P2] [LSN 40 CKPT-BEGIN] ...
                                                                     ▲
  MasterRecord ──────────────────────────────────────────────────────┘ (마지막 체크포인트 위치)

  페이지 P1 헤더: pageLSN = 20      ← 이 페이지를 마지막으로 바꾼 로그의 LSN
  메모리:        flushedLSN = 30   ← 로그가 디스크에 여기까지 내려갔다
  WAL 규칙:      P1을 디스크에 쓰려면 pageLSN(P1) ≤ flushedLSN 이어야 한다
```

- *LSN(Log Sequence Number)*: 로그 레코드마다 붙는, 단조 증가하는 번호. PostgreSQL에서는 WAL 안의 바이트 위치다(`0/9B698090` 같은 값).
- *pageLSN*: 페이지를 마지막으로 바꾼 로그 레코드의 LSN. 복구 때 "이 로그가 이미 페이지에 반영됐나"를 판정한다.
- *prevLSN*: 같은 트랜잭션의 **바로 앞** 로그 레코드. 트랜잭션별 연결 리스트를 만든다. 취소할 때 이 사슬을 거꾸로 따라간다.
- *recLSN*: dirty 페이지를 **처음** 더럽힌 로그의 LSN. 재실행을 어디서 시작할지 정한다.

### 2. 두 테이블 — ATT와 DPT

```text
  ATT (Active Transaction Table)          DPT (Dirty Page Table)
  txn  status   lastLSN                   page  recLSN
  T1   UNDO     80                        P1    20
  T2   COMMIT   70                        P2    30
                                          P3    60
```

- ATT는 아직 `TXN-END`가 없는 트랜잭션 목록이다. 커밋했지만 끝 처리가 안 된 것도 들어 있다.
- DPT는 버퍼 풀에서 dirty인 페이지 목록이다. 누가 더럽혔는지는 상관없다(CMU L21).

### 3. 퍼지 체크포인트 — 멈추지 않고 찍는다

```text
  ── T1·T2 계속 실행 ───────────────────────────────────────────>
       [CKPT-BEGIN]  (이 순간의 ATT·DPT를 떠 둔다)   ...   [CKPT-END: ATT, DPT]
            ▲
  MasterRecord에는 CKPT-BEGIN의 LSN을 적는다
```

- *비퍼지(블로킹) 체크포인트*: 새 트랜잭션을 막고, 실행 중인 것이 끝나길 기다리고, dirty 페이지를 다 쓴다. 복구는 쉽지만 서비스가 멈춘다.
- *퍼지 체크포인트*: 트랜잭션을 멈추지 않는다. 대신 그 순간의 ATT·DPT를 로그에 남겨 "무엇을 놓쳤을지"를 복구가 계산하게 한다. ARIES가 쓰는 방식이다(CMU L21).

로컬 재현(예시, PostgreSQL 17.11): `CHECKPOINT` 직후 WAL.

```text
  lsn: 0/CBC4BD30  desc: CHECKPOINT_REDO wal_level replica
  lsn: 0/CBC4BD50  desc: RUNNING_XACTS nextXid 1678 latestCompletedXid 1677 oldestRunningXid 1678
  lsn: 0/CBC4BD88  desc: CHECKPOINT_ONLINE redo 0/CBC4BD30; … online
```

- `CHECKPOINT_ONLINE` 레코드가 **자기보다 앞의** `redo 0/CBC4BD30`을 가리킨다. 체크포인트가 도는 동안에도 기록이 쌓였기 때문이다.
- 평소 부하 중에는 이 간격이 크다. 같은 서버의 `pg_controldata`에서 `Latest checkpoint location: 1/16C8D4E8`, `REDO location: 1/12B4E410`으로 약 65 MB 떨어져 있었다. `checkpoint_completion_target = 0.9`로 쓰기를 퍼뜨리기 때문이다.
- PostgreSQL 문서: 크래시 복구는 마지막 체크포인트 레코드를 보고 **redo 레코드**의 위치에서 REDO를 시작한다. 그 이전 변경은 디스크에 있음이 보장된다(28.5).

### 4. ARIES 세 단계 — 예제 하나로

```text
  LSN  레코드                               prevLSN
  10   T1 BEGIN
  20   T1 UPDATE P1                          10
  30   T2 UPDATE P2                          -
  40   CKPT-BEGIN
  50   CKPT-END  ATT={T1:20, T2:30}  DPT={P1:20, P2:30}
  60   T1 UPDATE P3                          20
  70   T2 COMMIT                             30
  80   T1 UPDATE P1                          60
  ──── 크래시 ────
```

```text
  ① 분석(Analysis): MasterRecord → LSN 40부터 앞으로 읽는다
     50: ATT={T1:20, T2:30}, DPT={P1:20, P2:30}로 시작
     60: T1.lastLSN=60, P3는 DPT에 없으니 추가(recLSN=60)
     70: T2 → COMMIT
     80: T1.lastLSN=80, P1은 이미 DPT에 있음(recLSN 20 유지)
     결과: 되돌릴 것 = {T1}, 다시 할 시작점 = min(recLSN) = 20

  ② 재실행(Redo): LSN 20부터 끝까지, 커밋 여부와 무관하게 "역사를 반복"
     각 레코드마다: 페이지가 DPT에 없거나 / LSN < recLSN 이거나 / 디스크의 pageLSN ≥ LSN 이면 건너뜀
     아니면 다시 적용하고 pageLSN = LSN
     끝에 커밋된 T2의 TXN-END를 쓰고 ATT에서 뺀다

  ③ 취소(Undo): ATT에 남은 T1을 lastLSN부터 prevLSN 사슬을 따라 거꾸로
     80 되돌림 → CLR 90 (undoNextLSN=60)
     60 되돌림 → CLR 100 (undoNextLSN=20)
     20 되돌림 → CLR 110 (undoNextLSN=10) → 10은 BEGIN이라 되돌릴 것 없음 → T1 TXN-END
```

- *CLR(Compensation Log Record)*: "되돌렸다"는 사실 자체를 적는 로그. `undoNextLSN`에 "다음에 되돌릴 레코드"를 적는다. CLR은 다시 되돌려지지 않는다(CMU L21).
- 왜 커밋 안 된 T1의 변경까지 **재실행**하나? 먼저 크래시 직전 상태를 그대로 복원해야, 그 위에서 취소가 페이지 상태를 틀리지 않고 되돌릴 수 있다. 이것이 "Repeating History During Redo"다.
- 취소 중에 또 죽으면? 재시작 때 CLR까지 재실행하고, 마지막 CLR의 `undoNextLSN`에서 취소를 이어 간다. 이미 되돌린 것을 두 번 되돌리지 않는다.

### 5. 실제 엔진은 ARIES를 어떻게 줄였나

```text
                     PostgreSQL 17                         MySQL 8.4 InnoDB
  재실행              redo 위치부터 WAL 재생                   체크포인트 LSN부터 redo 로그 재생
  취소 단계           없다 — 커밋 안 된 xid는 "중단"으로 판정      있다 — undo 로그로 롤백(백그라운드)
  ROLLBACK 기록       ABORT 레코드 하나(CLR 없음, XID가 있을 때)   undo 로그 적용
  이미 반영 판정       pageLSN ≥ 레코드 LSN이면 건너뜀            레코드 시작 LSN ≥ 페이지 LSN일 때만 적용
  찢긴 페이지 대비     체크포인트 후 첫 수정 때 전체 페이지(FPW)    doublewrite 버퍼(17.6.4)
```

- PostgreSQL은 MVCC(16번)라서 **옛 버전을 지우지 않고** 새 버전을 쓴다. 커밋 기록이 없는 트랜잭션의 튜플은 보이지 않을 뿐이다. 소스 README도 "크래시 뒤에는 어차피 그 트랜잭션이 중단된 것으로 간주한다"고 적는다(`src/backend/access/transam/README`, Asynchronous Commit 절). 그래서 abort 레코드는 flush를 기다리지 않는다.
- 예외: `PREPARE TRANSACTION`을 마친 2단계 커밋 트랜잭션은 상태가 디스크에 저장되어 크래시 뒤에도 준비 상태로 남는다. 나중에 `COMMIT PREPARED`·`ROLLBACK PREPARED`로 끝낸다(PostgreSQL 17 PREPARE TRANSACTION).
- XID를 받지 않은 트랜잭션(아무것도 쓰지 않은 것)의 `ROLLBACK`은 ABORT 레코드도 쓰지 않는다(`xact.c` `RecordTransactionAbort`).
- 로컬 재현(예시, PostgreSQL 17.11): `BEGIN; UPDATE …; UPDATE …; ROLLBACK;`의 WAL은 `HOT_UPDATE`·`LOCK`·`UPDATE` 뒤에 `ABORT` 하나였다. 되돌리는 레코드는 없었다.
- PostgreSQL WAL의 `prev`는 **WAL 전체에서 바로 앞 레코드**다. ARIES의 트랜잭션별 prevLSN이 아니다. 같은 재현에서 `ABORT`의 `prev 1/1902F120`은 그 트랜잭션의 앞 레코드(`1/1902CE58`)가 아니었다(사이에 다른 세션 기록).
- InnoDB 크래시 복구 순서(MySQL 8.4 17.18.2): 테이블스페이스 탐색 → redo 적용(연결 받기 전) → 미완료 트랜잭션 롤백 → change buffer 병합 → purge. 롤백은 백그라운드 스레드가 새 연결과 **병렬로** 한다. 그동안 새 연결이 복구 중인 트랜잭션과 락 충돌을 겪을 수 있다.
  - 예외: `XA PREPARE`까지 마친 XA 트랜잭션은 롤백하지 않고 준비 상태로 남아 명시적 `XA COMMIT`·`XA ROLLBACK`을 기다린다(MySQL 8.4 XA Restrictions, `XA RECOVER`로 확인).
  - 문서: 롤백 시간은 중단 전 트랜잭션이 돌던 시간의 **3~4배**가 걸릴 수 있고, 롤백 중인 트랜잭션은 취소할 수 없다.
- InnoDB의 *doublewrite 버퍼*: 버퍼 풀에서 내보내는 페이지를 제자리에 쓰기 **전에** 먼저 이 영역에 쓴다. 페이지를 쓰다 죽으면 복구 때 여기서 온전한 사본을 찾는다(MySQL 8.4 17.6.4). PostgreSQL의 FPW와 같은 문제(찢긴 페이지)를 다른 방법으로 푼다.

### 6. 체크포인트 간격의 저울

```text
  체크포인트 자주 ──────────────────────────────── 드물게
  재시작 복구 짧음                                 재시작 복구 김(재생할 WAL 많음)
  dirty 페이지 쓰기 잦음(I/O)                       쓰기 몰아서
  FPW 증가(체크포인트마다 첫 수정 = 페이지 통째)       FPW 적음
```

- PostgreSQL 17: `checkpoint_timeout`(기본 5분)마다, 또는 `max_wal_size`(기본 1 GB)를 넘기려 할 때 **먼저 오는 쪽**으로 체크포인트한다(28.5). 단 지난 체크포인트 뒤 WAL이 하나도 없으면 시간이 지나도 건너뛴다(28.5).
- `full_page_writes`(기본 on)면 체크포인트 뒤 **첫 수정**에서 페이지 전체를 WAL에 넣는다. 로컬 재현: 체크포인트 직후 첫 기록은 `len 8185 … FPW`, 같은 페이지의 다음 수정은 `len 71`이었다.
- WAL 양 때문에 불린 체크포인트가 직전 체크포인트와 `checkpoint_warning`(기본 30초)보다 가까우면 서버 로그에 경고가 나온다(시간 기반 체크포인트에는 안 나온다 — `checkpointer.c`). 로컬 관찰(부하 중인 같은 서버): `checkpoints are occurring too frequently (9 seconds apart)`, `HINT: Consider increasing the configuration parameter "max_wal_size".`
- InnoDB는 퍼지 체크포인트로 dirty 페이지를 **작은 묶음**으로 계속 내보낸다. 복구는 로그의 체크포인트 표시부터 앞으로 재생한다(MySQL 8.4 17.11.3).
  - redo 로그 크기 = `innodb_redo_log_capacity`. 이 서버의 값은 104857600(100 MiB)였다(로컬 확인, MySQL 8.4.10).
  - 체크포인트 나이 = `Log sequence number` − `Last checkpoint at`. 크래시 시 복구가 훑을 redo 양의 대략적인 지표다. `Log sequence number`에는 아직 flush 안 된 로그 버퍼 위치도 들어 있고, 훑은 기록이 모두 페이지에 다시 적용되는 것도 아니다.

## 쓰이는 자료구조·알고리즘

- **추가 전용 로그 + LSN** — 순서대로 쌓고, 위치로 가리킨다. 체크포인트는 "여기 이전은 볼 필요 없다"는 하한이다.
- **트랜잭션별 역방향 연결 리스트(prevLSN 사슬)** — 취소는 lastLSN에서 시작해 prevLSN으로 거꾸로 걷는다. 여러 트랜잭션을 되돌릴 때는 매번 **가장 큰 lastLSN**을 고른다(최대 힙이면 된다 — [data-structure/07-heap](../../data-structure/07-heap/2-summary.md)).
- **해시 테이블 두 개(ATT·DPT)** — 분석 단계에서 로그를 한 번 훑으며 채운다([data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)).
- **멱등 재적용(pageLSN 비교)** — "이미 반영됐으면 건너뜀" 판정 덕분에 재실행을 몇 번 반복해도 결과가 같다. 복구 중 크래시에도 안전한 이유다.
- **버퍼 풀과 dirty 추적** — DPT는 버퍼 풀([07-buffer-pool](../07-buffer-pool/2-summary.md))의 dirty 목록을 로그 관점에서 본 것이다.

## 적용 — 풀어나가는 법

### 1. 지금 체크포인트 상태를 본다

```sql
-- PostgreSQL 17
SELECT checkpoint_lsn, redo_lsn, checkpoint_time FROM pg_control_checkpoint();
SELECT pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), redo_lsn))  -- 지금 죽으면 재생할 양(대략)
  FROM pg_control_checkpoint();
SELECT num_timed, num_requested FROM pg_stat_checkpointer;   -- 17에서 새로 나뉜 뷰
```

- `num_requested`가 `num_timed`보다 훨씬 많으면 `max_wal_size`에 먼저 닿고 있을 가능성이 크다. 단 `num_requested`에는 수동 `CHECKPOINT` 같은 다른 요청도 들어간다. 원인은 `log_checkpoints` 로그의 `checkpoint starting: wal`(WAL 양)·`time`(시간)으로 확인한다(`xlog.c`). 로컬 관찰(부하 중 서버): `num_timed=2`, `num_requested=19`.
- 페이지의 pageLSN은 `pageinspect`로 볼 수 있다. 로컬 재현: `UPDATE` 직후 `SELECT lsn FROM page_header(get_raw_page('orders', 0))` → `0/CBC49F10`. 그 직후 `pg_current_wal_lsn()`은 `0/CBC4BD30`이었다.

```sql
-- MySQL 8.4
SHOW ENGINE INNODB STATUS\G   -- LOG 절
```

로컬 재현(예시, MySQL 8.4.10): 10만 행 삽입 직후 LOG 절.

```text
  Log sequence number          913016863
  Log flushed up to            913014959
  Pages flushed up to          865191733
  Last checkpoint at           865191733
  → 체크포인트 나이 = 913016863 − 865191733 = 47,825,130 B ≈ 45.6 MiB
```

### 2. 복구 시간을 설정으로 조절한다

```ini
# postgresql.conf (예시 — 값은 부하에 맞춰 측정 후 정한다)
checkpoint_timeout = 15min
max_wal_size = 8GB                # 체크포인트 사이 WAL이 커진다 = 복구 시간도 길어질 수 있다 (소프트 한계라 넘을 수도 있다)
checkpoint_completion_target = 0.9
log_checkpoints = on              # 17 기본 on: 쓰기량·거리(distance)·소요 시간 기록
```

- 목표 RTO에서 거꾸로 계산한다: "재생 속도(MB/s, 시험 측정) × 허용 복구 시간 ≥ 체크포인트 간 WAL 양".
- `recovery_prefetch`(기본 `try`)는 복구 중 필요한 블록을 미리 읽게 해 I/O 대기를 줄인다(19.5.4).
- `log_startup_progress_interval`(기본 10초)마다 긴 복구의 진행 상황이 로그에 찍힌다.

### 3. 로그를 읽는다 — 실제 크래시 복구 한 번

로컬 관찰(PostgreSQL 17.11, 같은 컨테이너에서 한 백엔드가 `SIGKILL`을 받았다 — 이 작업이 일으킨 것은 아니다):

```text
  22:07:27.635 LOG:  server process (PID 870) was terminated by signal 9: Killed
  22:07:27.638 LOG:  all server processes terminated; reinitializing
  22:07:27.667 LOG:  database system was interrupted; last known up at 2026-09-30 22:03:02 UTC
  22:07:29.328 LOG:  database system was not properly shut down; automatic recovery in progress
  22:07:29.338 LOG:  redo starts at 0/289D2C0            ← 22:03:02 체크포인트의 redo lsn
  22:07:32.048 LOG:  redo done at 0/207A5628 … elapsed: 2.71 s
  22:07:32.138 LOG:  checkpoint starting: end-of-recovery immediate wait
  22:07:38.211 LOG:  database system is ready to accept connections
```

- 한 백엔드만 죽어도 postmaster는 **모든** 백엔드를 끝내고 공유 메모리를 다시 만든 뒤 크래시 복구를 한다. 죽은 백엔드가 공유 메모리나 락을 망가뜨렸을 수 있어서, 공유 메모리를 초기화해 복구하는 설계다(`src/backend/postmaster/postmaster.c` 머리 주석).
- 재생량 = `0x207A5628 − 0x289D2C0` = 502,301,544 B ≈ 479 MiB. 체크포인트 뒤 약 4분 25초 동안 쌓인 WAL이다. 이 서버에서는 2.71초 만에 재생했다.
- 크래시 복구 중 접속하는 클라이언트는 `FATAL: the database system is in recovery mode`(SQLSTATE 57P03, DETAIL 없음)를 받는다. `DETAIL: Consistent recovery state has not been yet reached.`는 이것과 다른 메시지 `the database system is not yet accepting connections`(아카이브·대기 복구에서 아직 일관 상태 전)의 짝이다(`src/backend/tcop/backend_startup.c`, `postmaster.c` `canAcceptConnections`).
- 복구 끝에 **end-of-recovery 체크포인트**를 한다. 다음 크래시가 같은 WAL을 다시 재생하지 않게 하기 위해서다.

## 장애 시나리오와 대처

### 1. 체크포인트 간격 과대 → 재시작 복구 수십 분

- **현상**: DB가 죽었다 살아나는데 한참 동안 접속을 받지 않는다. 앱은 연결 실패를 반복한다.
- **보이는 형태**
  - 클라이언트: `FATAL: the database system is in recovery mode`(SQLSTATE 57P03 `cannot_connect_now` — `backend_startup.c`, `errcodes.txt`).
  - 서버 로그: `redo starts at X` 뒤 `redo done`이 한참 안 나온다. `log_startup_progress_interval`마다 진행 메시지가 찍힌다.
- **원인**: `max_wal_size`·`checkpoint_timeout`을 크게 잡아 체크포인트 사이 WAL이 수 GB~수십 GB 쌓였다. 재실행은 그 전부를 읽어야 한다.
- **대처**
  - 평소에 `pg_wal_lsn_diff(pg_current_wal_lsn(), redo_lsn)`의 최댓값을 지표로 둔다. 이것이 최악 재생량이다.
  - 시험 환경에서 재생 속도를 재고, RTO를 넘지 않게 두 파라미터를 줄인다.
  - 가용성이 중요하면 복구를 기다리지 않고 대기 복제본으로 넘긴다(32번).

### 2. 체크포인트 과소 → 쓰기 폭증과 경고

- **현상**: 부하가 오르면 디스크 쓰기량이 뛰고 쿼리 지연이 출렁인다.
- **보이는 형태**: `checkpoints are occurring too frequently (9 seconds apart)` + `HINT: Consider increasing … "max_wal_size"`(로컬 관찰). `pg_stat_checkpointer.num_requested`가 `num_timed`보다 훨씬 많다. WAL 양도 는다(FPW).
- **원인**: `max_wal_size`가 부하에 비해 작아 체크포인트가 시간 대신 WAL 양으로 계속 불린다. 체크포인트마다 첫 수정이 전체 페이지를 기록해 WAL이 더 빨리 찬다(되먹임).
- **대처**: `max_wal_size`를 키운다. 단, 시나리오 1의 복구 시간과 함께 저울질한다.

### 3. InnoDB redo 용량 부족 → 쓰기 스톨

- **현상**: MySQL 쓰기 처리량이 주기적으로 뚝 떨어진다.
- **보이는 형태**(로컬 관찰, MySQL 8.4.10, 여러 세션이 대량 쓰기 중):

```text
  [Warning] [MY-014084] [InnoDB] Threads are unable to reserve space in redo log which can't be
  reclaimed due to the 'log_checkpointer' consumer still lagging behind at LSN = 569167849.
  Consider increasing innodb_redo_log_capacity.
```

- **원인**: redo는 원형으로 재사용된다. 체크포인트가 따라오지 못하면 새 redo를 쓸 자리가 없다. 기본 100 MiB(이 서버 값)는 대량 쓰기에 작을 수 있다.
- **대처**: `innodb_redo_log_capacity`를 늘린다(8.4는 `SET GLOBAL`로 실행 중 변경 가능 — 17.6.5). 대신 체크포인트 나이 상한이 커져 크래시 복구가 길어질 수 있다.

### 4. 복구 뒤 긴 롤백 → 새 요청이 락에 막힌다

- **현상**: MySQL 재시작 직후 접속은 되는데 특정 테이블 갱신이 오래 멈춘다.
- **보이는 형태**: `SHOW ENGINE INNODB STATUS`에 복구된 트랜잭션이 롤백 중으로 보이고, 새 트랜잭션이 그 행의 락을 기다린다.
- **원인**: 크래시 직전 거대한 트랜잭션(예: 한 문장 대량 UPDATE)이 돌았다. InnoDB는 redo 뒤 미완료 트랜잭션을 백그라운드에서 롤백한다. 문서: 중단 전 실행 시간의 3~4배가 걸릴 수 있고 취소할 수 없다(17.18.2).
- **대처**
  - 대량 변경을 작은 트랜잭션으로 쪼갠다([34-large-backfill-and-batch-dml](../34-large-backfill-and-batch-dml/2-summary.md)).
  - 극단적인 경우 문서는 `innodb_force_recovery` 3 이상으로 롤백을 건너뛰는 방법을 적는다. 데이터 정합성 위험이 있으니 덤프 후 재구성 용도로만 쓴다(17.20.3).

### 5. 로그와 데이터 사이의 거짓 fsync → 복구가 틀린 상태를 만든다

- **현상**: 전원 장애 뒤 복구는 "성공"했는데 커밋된 데이터가 없거나 인덱스가 깨져 있다.
- **원인**: WAL 규칙은 "로그가 **정말** 디스크에 있다"는 가정 위에 있다. 쓰기 캐시가 fsync에 거짓으로 답하거나 `fsync = off`면 그 가정이 깨진다. PostgreSQL 28.1은 휘발성 쓰기 캐시를 가진 드라이브의 위험을 다룬다.
- **대처**: 배터리 보호 캐시가 아니면 드라이브 쓰기 캐시를 끄고, `fsync`는 켠다. 자세한 것은 [os/24-fsync-and-durability](../../os/24-fsync-and-durability/2-summary.md).

## 핵심 문장

- STEAL은 undo를, NO-FORCE는 redo를 필요하게 만든다. ARIES는 둘 다 허용하는 대가로 분석·재실행·취소 3단계 복구를 한다.
- 재실행은 커밋 여부와 무관하게 "역사를 반복"한다. 그 위에서 취소가 CLR을 남기며 되돌리므로, 복구 중 다시 죽어도 같은 일을 두 번 하지 않는다.
- pageLSN ≥ 레코드 LSN이면 건너뛰는 멱등 판정이 재실행을 안전하게 만든다.
- 퍼지 체크포인트는 서비스를 멈추지 않고 "재실행 시작점"을 앞당긴다. 간격은 복구 시간과 평소 I/O·FPW 비용의 저울이다.
- PostgreSQL은 MVCC 덕분에 취소 단계가 없다(커밋 기록 없음 = 중단, 준비된 2단계 커밋 트랜잭션은 예외). InnoDB는 undo 로그로 백그라운드 롤백을 한다.

## 관련 주제·근거

- 선행: [19-wal-and-logging](../19-wal-and-logging/2-summary.md) — WAL 규칙·no-force/steal
- 연결
  - [20-backup-and-pitr](../20-backup-and-pitr/2-summary.md) — 같은 WAL 재생을 목표 시점까지 하는 것
  - [07-buffer-pool](../07-buffer-pool/2-summary.md) · [16-mvcc](../16-mvcc/2-summary.md) · [34-large-backfill-and-batch-dml](../34-large-backfill-and-batch-dml/2-summary.md)
  - [os/23-crash-consistency-and-journaling](../../os/23-crash-consistency-and-journaling/2-summary.md) — 파일 시스템 저널링도 같은 redo 로그 발상 · [os/24-fsync-and-durability](../../os/24-fsync-and-durability/2-summary.md)
- 강의·논문
  - CMU 15-445 Fall 2024 Lecture #21 Database Crash Recovery(ARIES 3원칙, LSN 표, CLR·undoNextLSN, 퍼지 체크포인트, ATT·DPT, 분석·재실행·취소 규칙) <https://15445.courses.cs.cmu.edu/fall2024/notes/21-recovery.pdf>
  - C. Mohan 외, "ARIES: A Transaction Recovery Method Supporting Fine-Granularity Locking and Partial Rollbacks Using Write-Ahead Logging", ACM TODS 17(1), 1992 (CMU 노트 경유, 원문 미열람)
- PostgreSQL 17
  - 28.5 WAL Configuration(체크포인트 정의·redo 레코드·5분/1GB·FPW 비용·`checkpoint_warning`·`checkpoint_completion_target` 0.9) <https://www.postgresql.org/docs/17/wal-configuration.html>
  - 19.5 Write Ahead Log(`recovery_prefetch`) · 19.8 Error Reporting and Logging(`log_startup_progress_interval` 10초, `log_checkpoints`) · 27.2 `pg_stat_checkpointer`
  - `src/backend/access/transam/xlogutils.c` `XLogReadBufferForRedoExtended`(`lsn <= PageGetLSN(page)`면 `BLK_DONE`) · `src/backend/tcop/backend_startup.c`(57P03 메시지들)
  - `src/backend/access/transam/README` — pageLSN·WAL 규칙, 체크포인트 후 첫 수정의 전체 페이지, "크래시 뒤에는 중단으로 간주" <https://github.com/postgres/postgres/blob/REL_17_STABLE/src/backend/access/transam/README>
- MySQL 8.4 Reference Manual
  - 17.11.3 InnoDB Checkpoints(퍼지 체크포인트) <https://dev.mysql.com/doc/refman/8.4/en/innodb-checkpoints.html>
  - 17.18.2 InnoDB Recovery(복구 단계, 롤백 3~4배, 백그라운드 롤백) <https://dev.mysql.com/doc/refman/8.4/en/innodb-recovery.html>
  - 소스 `storage/innobase/log/log0recv.cc`(8.4) — `recv->start_lsn >= page_lsn`일 때만 redo 레코드를 페이지에 적용 <https://github.com/mysql/mysql-server/blob/8.4/storage/innobase/log/log0recv.cc>
  - 17.6.5 Redo Log(`innodb_redo_log_capacity`, `#innodb_redo`) <https://dev.mysql.com/doc/refman/8.4/en/innodb-redo-log.html> · 17.6.4 Doublewrite Buffer <https://dev.mysql.com/doc/refman/8.4/en/innodb-doublewrite-buffer.html> · 17.20.3 Forcing InnoDB Recovery
- 로컬 재현·관찰(PostgreSQL 17.11, MySQL 8.4.10): `CHECKPOINT` 뒤 `CHECKPOINT_REDO`/`CHECKPOINT_ONLINE redo …`, `pg_controldata`의 체크포인트·REDO 위치 차이, 체크포인트 후 첫 수정 FPW(8185 B) vs 다음 수정(71 B), `page_header`의 pageLSN, `ROLLBACK`의 WAL(`ABORT` 하나, CLR 없음), 같은 서버의 실제 크래시 복구 로그(479 MiB, 2.71 s), `checkpoints are occurring too frequently` 경고, InnoDB LOG 절의 체크포인트 나이와 redo 용량 경고
