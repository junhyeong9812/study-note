# 크래시 복구

상위: [MySQL 아키텍처 지도](../../README.md)

서버가 비정상 종료된 뒤 다시 켜질 때, **데이터 파일을 마지막 커밋 상태로 되돌려 놓기까지**의 흐름이다. 세 층이 차례로 일한다. 먼저 InnoDB 가 마지막 체크포인트부터 redo 를 읽어 페이지별로 모으고, doublewrite 로 찢어진 페이지를 고친 뒤, 페이지마다 page LSN 보다 새로운 redo 만 적용한다. 다음으로 undo 에서 트랜잭션을 되살리고, 데이터 사전을 다시 열 때 그 가운데 **DDL 트랜잭션만** 먼저 되돌린다. 이어서 서버 쪽 `Binlog_recovery` 가 binlog 에 끝까지 적힌 XID 목록을 만들어, PREPARED 트랜잭션 각각을 커밋할지 롤백할지 InnoDB 에 알려 준다. 흐름은 백그라운드 롤백 스레드가 **PREPARED 가 아닌** 남은 ACTIVE 트랜잭션을 모두 되돌리는 데서 끝난다. 스레드 경계가 여럿 있다. redo 적용은 페이지 읽기의 완료 처리(`buf_page_io_complete`) 안에서 일어난다. [08] 이 거는 복구용 읽기는 비동기라(buf0rea.cc L697, sync=false) 그 완료는 **I/O 핸들러 스레드**가 하고, 동기로 읽힌 페이지는 읽은 스레드가 같은 함수를 직접 부르며 적용한다(buf0rea.cc L145). 이미 버퍼 풀에 있는 페이지는 [08] 의 `recv_apply_log_rec` 가 시작 스레드에서 `recv_recover_page(false, block)` 를 부르지만(log0recv.cc L1161), 소스 주석(L1143-L1154)은 그런 페이지도 읽힐 때 I/O 완료 쪽이 이미 적용했다고 보고, [09] 는 상태가 RECV_PROCESSED 면 곧바로 돌아간다(L2448-L2449). 또 복구 중 dirty 페이지는 **recv_writer** 스레드가 페이지 클리너에게 쓰기를 시키며, 사용자 트랜잭션 롤백은 **trx_recovery_rollback** 스레드가 한다.

기준 태그: mysql-9.7.2 [`008e09c283`](https://github.com/mysql/mysql-server/tree/008e09c2834b98143a8c067d4d225c90953050cf). 모든 줄 번호는 이 태그 기준이다.

## 전체 그림

```text
 시작 스레드 (mysqld -> InnoDB 플러그인 초기화 innobase_init_files, ha_innodb.cc L5733)
 ------------------------------------------------------------------
 [01] srv_start                                              srv0start.cc L1330
      +-- srv_sys_space.open_or_create                        L1595  첫 페이지의 flushed_lsn,
      |     doublewrite 파일을 메모리로 읽는다 (fsp0sysspace.cc L529)
      +-- [02] recv_recovery_from_checkpoint_start            L1764 -> log0recv.cc L3766
      |     +-- [03] recv_find_max_checkpoint                 L3783  모든 redo 파일의 헤더 두 개
      |     +-- checkpoint_lsn != flushed_lsn 이면
      |     |     [07] recv_init_crash_recovery               L3855  doublewrite 로 페이지 복원
      |     +-- [04] recv_recovery_begin                      L3859
      |     |     +-- while: recv_read_log_seg -> [05] recv_scan_log_recs    L3698-L3716
      |     |     |     +-- 블록 헤더, 체크섬, epoch 로 로그의 끝을 판정
      |     |     |     +-- [06] recv_parse_log_recs        L3501  mtr 단위로 잘라 해시에
      |     |     |     +-- 해시가 max_memory 를 넘으면 [08] 로 중간 적용  L3505
      |     |     +-- [08] recv_apply_hashed_log_recs       L3723
      |     |           +-- 페이지마다 읽기 요청 (recv_read_in_area, 비동기)
      |     |           |     I/O 핸들러 스레드: buf_page_io_complete
      |     |           |       -> [09] recv_recover_page_func  (buf0buf.cc L5960)
      |     |           +-- 전부 적용될 때까지 기다린 뒤 flush list 를 비우고 버퍼 풀 무효화
      |     +-- log_start                                     L3911  redo 쓰기 재개
      +-- [10] recv_recovery_from_checkpoint_finish           L1816
      +-- dict_boot                                           L1835
      +-- trx_sys_init_at_db_start                            L1930  undo 에서 트랜잭션 되살리기
 ------------------------------------------------------------------
 서버 초기화 (sql/mysqld.cc init_server_components)
 ------------------------------------------------------------------
 dd::init(DD_RESTART_OR_UPGRADE)                              mysqld.cc L8536
      +-- Dictionary_impl::init                               dd.cc L67
      +-- run_bootstrap_thread(restart_dictionary)            dictionary_impl.cc L155-L158
            부트스트랩 스레드를 만들고 끝날 때까지 join 한다  bootstrap.cc L441, L452
 [부트스트랩 스레드] restart_dictionary                       bootstrapper.cc L901
      +-- DDSE_dict_recover(thd, DICT_RECOVERY_RESTART_SERVER, ...)  bootstrapper.cc L943
            정의 L84. InnoDB handlerton 을 찾아                     L88
            ddse->dict_recover(mode, version) 로 부른다              L91
            +-- innobase_dict_recover                         ha_innodb.cc L4037
                  (handlerton 등록: innobase_hton->dict_recover = innobase_dict_recover, L5429)
                  +-- srv_dict_recover_on_restart             ha_innodb.cc L4103
                        +-- [12] trx_rollback_or_clean_recovered(false)
                                                              srv0start.cc L2119  DDL 트랜잭션만
 tc_log->open -> MYSQL_BIN_LOG::open_binlog                   mysqld.cc L8849
      +-- [11] Binlog_recovery::recover                       binlog.cc L6963
            +-- ha_recover -> innobase_commit_by_xid / innobase_rollback_by_xid
 ha_post_recover -> innobase_post_recover                     mysqld.cc L8857
      +-- srv_start_threads_after_ddl_recovery                ha_innodb.cc L4188
 ------------------------------------------------------------------
 백그라운드 스레드 trx_recovery_rollback                      srv0start.cc L2264
      +-- [12] trx_rollback_or_clean_recovered(true)          PREPARED 가 아닌 ACTIVE 전부
```

시간축으로 세우면 무엇이 어느 순서로 정리되는지가 보인다.

```text
 재시작 한 번의 시간축 (위에서 아래로, -> 뒤가 정리되는 것)

 open        시스템 테이블스페이스를 열고 dblwr 파일을 읽는다
 checkpoint  [03] 가장 큰 checkpoint_lsn -> redo 의 시작점
 dblwr       [07] 체크섬이 깨진 페이지를 dblwr 사본으로 -> 찢어진 페이지
 scan/parse  [05] [06] checkpoint 부터 로그 끝까지 -> 페이지별 redo 목록
 apply       [08] [09] 시작 LSN >= page LSN 인 레코드만 적용 -> 페이지가 크래시 직전 상태로
 finish      [10] recv_writer 종료, 복구 자료 해제
 resurrect   trx_sys_init_at_db_start -> ACTIVE / PREPARED / COMMITTED 로 되살림
 dd-undo     [12] all=false -> 미완 DDL 트랜잭션 롤백
 binlog      [11] binlog 에 XID 가 있으면 commit, 없으면 롤백 -> PREPARED (내부 2PC)
 bg-undo     [12] all=true, 백그라운드 스레드 -> 남은 ACTIVE 롤백

 bg-undo 는 연결을 받는 동안에도 계속될 수 있다
 (log0recv.cc L3918 주석 "transaction rollbacks can be run in background")
```

redo 적용의 판정은 페이지 하나 단위로 이루어진다. 한 페이지에 쌓인 레코드 목록을 앞에서부터 보며 **레코드의 시작 LSN 이 page LSN 이상인 것만** 적용한다. page LSN 은 그 페이지를 마지막으로 바꾼 mtr 의 끝 LSN 이므로, 결과적으로 mtr 단위로 통째로 건너뛰거나 통째로 적용된다.

```text
 페이지 하나의 적용 판정 ([09] recv_recover_page_func)

 page_lsn = FIL_PAGE_LSN (디스크 페이지에 적힌 마지막 수정 LSN)            L2560
 recv_addr->rec_list:  r1(start 100)  r2(start 180)  r3(start 260)  r4(start 330)
 page_lsn = 200 이면
   r1  start 100 < 200   건너뜀 (이미 디스크에 반영됨)
   r2  start 180 < 200   건너뜀
   r3  start 260 >= 200  적용                                               L2632
   r4  start 330 >= 200  적용
 적용한 것이 있으면 buf_flush_note_modification(start_lsn, end_lsn)       L2693
   페이지가 dirty 가 되어 flush list 에 붙는다 (redo 는 새로 쓰지 않는다: MTR_LOG_NONE)

 같은 redo 를 두 번 적용해도 결과가 같은 이유가 이 비교다
```

## 어디에서 쓰이는가

```text
 [mini-transaction과 redo 기록]   복구가 읽는 로그는 그 흐름이 log buffer 에 쓴 mtr 묶음이다
                                  MLOG_SINGLE_REC_FLAG 와 MLOG_MULTI_REC_END 가 mtr 경계다
 [페이지 플러시, doublewrite]     복구가 쓰는 dblwr 복사본과 checkpoint 헤더는 그 흐름이 남긴다
 [버퍼 풀 페이지 획득]            복구 중 페이지 읽기는 버퍼 풀을 그대로 쓰고,
                                  읽기 완료 buf_page_io_complete 가 redo 적용 자리다
 [커밋과 binlog 2PC]              prepare 까지 간 트랜잭션의 운명을 binlog 가 정한다
 [purge]                          롤백과 커밋 정리가 끝난 undo 가 purge 로 간다
```

연결 흐름: [mini-transaction과 redo 기록](../mtr-redo/README.md), [페이지 플러시, doublewrite, 체크포인트](../flush-checkpoint/README.md), [버퍼 풀 페이지 획득](../buffer-pool-fetch/README.md), [커밋과 binlog 2PC](../commit-2pc/README.md), [purge](../purge/README.md). 파일 형식은 [redo 로그 파일과 mlog 타입](../../structure/redo-log-files/README.md), [undo 테이블스페이스와 롤백 세그먼트](../../structure/undo-segments/README.md)에 있다.

## db-engine 에서는

db-engine 은 같은 문제(커밋된 것만 살리고 커밋 안 된 것은 버리기)를 **deferred-apply + redo-only** 로 단순화했다. 데이터에 쓰기 전에 커밋이 끝나므로 undo 가 필요 없다.

```text
 같은 문제, 두 구현 (위 MySQL / 아래 db-engine)

 시작점
   MySQL      redo 파일 헤더의 checkpoint_lsn. 그보다 앞의 로그는 읽지 않는다
   db-engine  08-01 Recovery 는 로그 처음부터 replay. Checkpoint 레코드는 무시한다 (08-02 가 다룬다)

 로그의 끝
   MySQL      블록 hdr_no 불일치, 블록 체크섬 실패, epoch 불일치, 짧은 블록 = 끝
   db-engine  잘린 마지막 레코드를 EOF 로 보고 멈춘다 (08-03 이 partial bytes 로 공격)

 무엇을 다시 하는가
   MySQL      물리 redo. 페이지마다 page_lsn <= start_lsn 인 레코드만 (멱등)
   db-engine  논리 redo. committed 집합에 든 txId 의 InsertRow 를 heap.insert 로 다시
              멱등이 아니라 두 번 돌리면 두 번 들어간다 (08-01 "다음 한계")

 커밋 안 된 트랜잭션
   MySQL      redo 로 페이지를 다 살린 뒤 undo 로 되돌린다 (ACTIVE -> 롤백)
              PREPARED 는 binlog 의 XID 로 commit / rollback 을 정한다
   db-engine  COMMIT 레코드가 없으면 적용하지 않는다. heap 에 쓴 적이 없어 되돌릴 것도 없다

 찢어진 페이지
   MySQL      doublewrite 복사본과 비교해 덮어쓴다
   db-engine  해당 없음 (페이지 단위 부분 쓰기를 가정하지 않는다)
```

db-engine 의 `Recovery.recover()` 는 `perTxInserts`, `committed`, `aborted` 세 컬렉션을 한 번의 replay 로 채운 뒤 committed 인 것만 다시 넣는다. MySQL 에서 이 "커밋 여부 판정"은 redo 가 아니라 undo 와 binlog 에 있고, redo 는 커밋 여부와 무관하게 페이지를 크래시 직전으로 돌려놓는 일만 한다. 08-03 처럼 복구 경로에 실패를 주입하는 MySQL 쪽 장치는 디버그 빌드의 `RECOVERY_CRASH(n)` 지점이다. `innodb_force_recovery_crash` 값과 같은 번호의 지점에서 `_exit(3)` 으로 복구 도중에 죽는다(srv0start.h L53-L62, 복구 경로의 지점은 srv0start.cc L1731, L1780, L1791, L1814, L1881). 챕터: [08-01-wal-recovery](../../../../../project/db-engine/08-01-wal-recovery/), [08-03-crash-simulation](../../../../../project/db-engine/08-03-crash-simulation/).

## 단계

1. [srv_start](01_srv_start/README.md)가 파일을 열고 redo 복구를 부른 뒤 트랜잭션 시스템을 되살린다.
2. [recv_recovery_from_checkpoint_start](02_recv_recovery_from_checkpoint_start/README.md)가 체크포인트를 찾고 복구가 필요한지 판정해 스캔과 적용을 부른다.
3. [recv_find_max_checkpoint](03_recv_find_max_checkpoint/README.md)가 redo 파일마다 헤더 두 개를 읽어 가장 큰 체크포인트를 고른다.
4. [recv_recovery_begin](04_recv_recovery_begin/README.md)이 해시 테이블 메모리 한도를 정하고 로그를 구간 단위로 읽는다.
5. [recv_scan_log_recs](05_recv_scan_log_recs/README.md)가 로그 블록을 검사해 로그의 끝을 찾고 파싱 버퍼에 옮긴다.
6. [recv_parse_log_recs](06_recv_parse_log_recs/README.md)가 mtr 단위로 레코드를 잘라 페이지별 해시에 넣는다.
7. [recv_init_crash_recovery](07_recv_init_crash_recovery/README.md)가 doublewrite 로 찢어진 페이지를 고치고 recv_writer 를 띄운다.
8. [recv_apply_hashed_log_recs](08_recv_apply_hashed_log_recs/README.md)가 페이지마다 읽기를 걸어 적용하고 결과를 디스크로 내린다.
9. [recv_recover_page_func](09_recv_recover_page_func/README.md)가 페이지 하나에 LSN 비교로 레코드를 적용한다.
10. [recv_recovery_from_checkpoint_finish](10_recv_recovery_from_checkpoint_finish/README.md)가 recv_writer 를 멈추고 복구 자료를 해제한다.
11. [Binlog_recovery.recover](11_Binlog_recovery.recover/README.md)가 binlog 의 XID 로 PREPARED 트랜잭션의 운명을 정한다.
12. [trx_rollback_or_clean_recovered](12_trx_rollback_or_clean_recovered/README.md)가 되살린 트랜잭션을 정리하거나 롤백한다.

## 결과가 쓰이는 곳

```text
 데이터 파일
      --> [08] 끝의 BUF_FLUSH_LIST 배치로 복구된 페이지가 디스크에 내려간다
      --> 이후 checkpoint 가 복구 이후 LSN 으로 전진할 수 있다

 log_sys (recovered_lsn, log_start)
      --> 새 redo 는 recovered_lsn 뒤에 이어 쓴다 ([mini-transaction과 redo 기록])

 trx_sys->rw_trx_list 의 되살린 트랜잭션
      --> PREPARED 는 [11] 에서 commit 또는 rollback, 외부 XA 는 XA RECOVER 에 남는다
      --> ACTIVE 는 [12] 가 롤백. 그 동안 잡은 잠금은 trx_resurrect_locks 로 되살아 있다

 binlog
      --> 마지막 파일을 마지막 유효 위치에서 자르고 IN_USE 플래그를 지운다 (binlog.cc L6985-L6991)
```

## 다루지 않는 것

`innodb_force_recovery` 단계별 동작(SRV_FORCE_NO_LOG_REDO 이상이면 redo 를 건너뛰는 L3767 등), 8.0.30 이전 redo 형식 업그레이드(`recv_verify_log_is_clean_pre_8_0_30`), 클론과 MEB 백업에서의 복구(`is_cloned_db`, `is_meb_db`), MLOG_FILE_* 레코드로 테이블스페이스를 찾는 과정(`fil_tablespace_lookup_for_recovery`), 동적 메타데이터(`MetadataRecover`), DDL 로그 복구(`log_ddl->recover`), 암호화된 redo 와 테이블스페이스 키, 외부 XA(`XA RECOVER`) 는 이 흐름의 곁가지라 요약만 했다.

## 하위 메서드

- [01 srv_start](01_srv_start/README.md)
- [02 recv_recovery_from_checkpoint_start](02_recv_recovery_from_checkpoint_start/README.md)
- [03 recv_find_max_checkpoint](03_recv_find_max_checkpoint/README.md)
- [04 recv_recovery_begin](04_recv_recovery_begin/README.md)
- [05 recv_scan_log_recs](05_recv_scan_log_recs/README.md)
- [06 recv_parse_log_recs](06_recv_parse_log_recs/README.md)
- [07 recv_init_crash_recovery](07_recv_init_crash_recovery/README.md)
- [08 recv_apply_hashed_log_recs](08_recv_apply_hashed_log_recs/README.md)
- [09 recv_recover_page_func](09_recv_recover_page_func/README.md)
- [10 recv_recovery_from_checkpoint_finish](10_recv_recovery_from_checkpoint_finish/README.md)
- [11 Binlog_recovery.recover](11_Binlog_recovery.recover/README.md)
- [12 trx_rollback_or_clean_recovered](12_trx_rollback_or_clean_recovered/README.md)
