# mini-transaction과 redo 기록

상위: [MySQL 아키텍처 지도](../../README.md)

페이지를 바꾸는 쪽(B+Tree 삽입, undo 기록 등)이 `mtr_t::start` 로 mini-transaction 을 열고, 바꾼 내용을 redo 레코드로 모아 두었다가 **`mtr_t::commit` 한 번에 log buffer 로 옮기고, 바꾼 페이지를 flush list 에 붙이고, 래치를 푸는** 흐름이다. 그 뒤 log buffer 의 바이트를 파일에 쓰고 fsync 하는 일은 사용자 스레드가 하지 않는다. 이 흐름에는 **스레드 경계가 두 번** 있다. 사용자 스레드는 LSN 범위를 원자적으로 예약해 자기 몫을 복사하고 `recent_written` 에 링크를 거는 데서 끝나고, 그 링크를 따라가 파일에 쓰는 것은 `log_writer` 스레드, fsync 하는 것은 `log_flusher` 스레드다. 두 경계 모두 mutex 가 아니라 원자 변수와 링크 버퍼(`Link_buf`)로 이어진다. 흐름은 `flushed_to_disk_lsn` 이 전진하는 데서 끝나고, 그 값을 기다리는 커밋은 [커밋과 binlog 2PC](../commit-2pc/README.md), flush list 를 비우는 쪽은 [페이지 플러시, doublewrite, 체크포인트](../flush-checkpoint/README.md)로 이어진다.

기준 태그: mysql-9.7.2 [`008e09c283`](https://github.com/mysql/mysql-server/tree/008e09c2834b98143a8c067d4d225c90953050cf). 모든 줄 번호는 이 태그 기준이다.

## 전체 그림

```text
 사용자 스레드 (페이지를 바꾸는 쪽, 예: btr_cur_optimistic_insert)
 ------------------------------------------------------------------
 [01] mtr_t::start                                     mtr0mtr.cc L565
      +-- m_log, m_memo 두 버퍼를 새로 만든다          L578-L579
      +-- m_log_mode = MTR_LOG_ALL                     L582
      +-- check_nolog_and_mark                         L591  redo 가 전역으로 꺼져 있으면 NO_REDO
      ...  페이지 래치를 잡아 m_memo 에, redo 레코드를 m_log 에 쌓는다
 [02] mtr_t::commit                                    mtr0mtr.cc L662
      +-- 레코드가 있거나 NO_REDO 인데 수정이 있으면   L672-L673
      |   [04] Command::execute                        L676
      |     +-- [03] prepare_write                     L844  SINGLE_REC 플래그 또는 MULTI_REC_END
      |     +-- [05] log_buffer_reserve                L851  sn.fetch_add(len) 로 LSN 범위 예약
      |     +-- m_log.for_each_block(mtr_write_log_t)  L856  블록마다
      |     |     +-- [06] log_buffer_write            L516  log buffer 에 memcpy
      |     |     +-- [07] log_buffer_write_completed  L548  recent_written 에 링크
      |     +-- buf_flush_list_added->wait_to_add      L861
      |     +-- [08] add_dirty_blocks_to_flush_list    L865  oldest / newest LSN 을 찍고 flush list 에
      |     +-- buf_flush_list_added->report_added     L867  "이 범위의 페이지는 다 붙였다"
      |     +-- release_all, release_resources         L878-L879  래치를 여기서 푼다
      +-- 아니면 래치만 풀고 끝                        L678-L679
 ------------------------------------------------------------------
      스레드 경계 1  (log.recent_written 의 링크, writer_event)
 ------------------------------------------------------------------
 log_writer 스레드
 [09] log_writer                                       log0write.cc L2230
      +-- log_advance_ready_for_write_lsn              L2256  이어진 링크를 따라 ready_lsn 전진
      +-- log_writer_write_buffer(ready_lsn)           L2299
            +-- log_writer_wait_on_checkpoint          L2149  redo 파일에 자리가 없으면 기다림
            +-- log_write_buffer -> write_blocks       L2202  OS 버퍼로 write
            +-- write_lsn.store                        L1794
            +-- notify_about_advanced_write_lsn        L1796  flush_log_at_trx_commit=1 이면 flusher 를 깨운다
 ------------------------------------------------------------------
      스레드 경계 2  (log.write_lsn, flusher_event)
 ------------------------------------------------------------------
 log_flusher 스레드
 [10] log_flusher                                      log0write.cc L2495
      +-- flushed_to_disk_lsn < write_lsn 이면         L2538
            log_flush_low -> fsync                     L2449
            flushed_to_disk_lsn.store                  L2465  --> 커밋 대기자를 깨운다
```

한 mtr 이 LSN 축 위에 남기는 값은 넷이다. 사용자 스레드가 둘을, 백그라운드 스레드가 둘을 전진시킨다.

```text
 LSN 축 위의 네 경계 (작은 쪽이 왼쪽)

   flushed_to_disk_lsn <= write_lsn <= ready_for_write_lsn <= log.sn 이 가리키는 lsn
   |                      |            |                      |
   log_flusher 가 올림    log_writer   log_writer 가          사용자 스레드가 fetch_add 로 올림
   (fsync 끝)             (write 끝)   recent_written 링크를  (예약 끝, 복사는 아직일 수 있음)
                                       따라 올림

 ------------+--------------+----------------+-----------------------+------->  lsn
   디스크에   | OS 버퍼에만   | log buffer 에   | 예약됐지만 구멍이 있다
   영속       | 있다          | 구멍 없이 찼다  | (다른 스레드가 아직 복사 중)

 mtr 하나는 [start_lsn, end_lsn) 를 받는다. 이 범위는 log buffer 의 자리이자
 redo 파일의 자리다 (log0buf.cc L107-L109 주석)
```

## 어디에서 쓰이는가

```text
 [B+Tree 삽입과 분할]   btr_cur_optimistic_insert / pessimistic_insert 가 mtr 안에서 페이지를 바꾸고
                        row_ins_clust_index_entry_low 가 mtr.commit 한다
 [버퍼 풀 페이지 획득]  buf_page_get_gen 이 잡은 래치가 m_memo 에 쌓이고 commit 에서 풀린다
 [커밋과 binlog 2PC]    트랜잭션 커밋의 mtr 이 받은 LSN 으로 trx_flush_log_if_needed_low 가
                        log_write_up_to 를 부른다 (trx0trx.cc L1742) --> [10] 의 결과를 기다린다
 [페이지 플러시...]     [08] 이 채운 flush list 와 buf_flush_list_added 가 checkpoint LSN 의 재료다
 [크래시 복구]          여기서 쓴 redo 를 checkpoint 부터 다시 읽는다
```

다음 흐름은 [페이지 플러시, doublewrite, 체크포인트](../flush-checkpoint/README.md)다. redo 블록과 레코드의 바이트 모양은 [redo 로그 파일과 mlog 타입](../../structure/redo-log-files/README.md)에 둔다.

## db-engine 에서는

같은 문제(변경을 먼저 로그에 적고, 순번을 매기고, 커밋 때 디스크에 닿게 하기)를 db-engine 은 스레드 하나가 파일에 직접 append 하는 방식으로 풀었다.

```text
 같은 문제, 두 구현 (위 MySQL / 아래 db-engine)

 로그에 넣는 단위
   MySQL      mtr 하나 = redo 레코드 묶음 하나. 복구는 묶음 전체를 적용하거나 건너뛴다
   db-engine  LogRecord 하나 (BeginTx / InsertRow / CommitTx / AbortTx / Checkpoint)

 순번 (LSN)
   MySQL      바이트 위치. log.sn.fetch_add(len) 로 범위를 예약하고 블록 헤더를 더해 lsn 으로 바꾼다
   db-engine  레코드 개수. append 가 nextLsn 을 1 올린다. reopen 때 파일을 세서 복원

 동시 쓰기
   MySQL      여러 스레드가 서로 다른 범위를 동시에 memcpy, recent_written 이 구멍을 추적
   db-engine  append 가 file.seek(file.length()) 뒤 writeInt, write. 동시성 장치 없음

 디스크에 닿게 하기
   MySQL      log_writer 가 write, log_flusher 가 fsync. 커밋은 flushed_to_disk_lsn 을 기다린다
   db-engine  Transaction.commit 이 CommitTx 를 append 한 뒤 logManager.sync() (fd.sync)

 페이지와의 관계
   MySQL      페이지를 먼저 바꾸고 그 redo 를 적는다. 페이지는 dirty 로 flush list 에 남는다
   db-engine  deferred-apply. commit 에서 sync 한 뒤에야 heap 에 insert 한다 (undo 없음)
```

db-engine 은 heap 을 커밋 전에 건드리지 않으므로 "로그보다 페이지가 먼저 디스크에 가면 안 된다"는 WAL 규칙이 구조적으로 지켜진다. MySQL 은 페이지를 먼저 바꾸기 때문에 그 규칙을 페이지 쓰기 쪽이 따로 지킨다(`buf_flush_write_block_low` 의 `log_write_up_to`, 다음 흐름). 챕터: [08-01-wal-recovery](../../../../../project/db-engine/08-01-wal-recovery/), [08-02-lsn-checkpoint](../../../../../project/db-engine/08-02-lsn-checkpoint/).

## 단계

1. [mtr_t.start](01_mtr_t.start/README.md)가 두 버퍼를 비우고 로그 모드를 정한다.
2. [mtr_t.commit](02_mtr_t.commit/README.md)이 레코드가 있을 때만 `Command::execute` 로 넘긴다.
3. [mtr_t.Command.prepare_write](03_mtr_t.Command.prepare_write/README.md)가 쓸 바이트 수를 정하고 레코드 묶음의 끝을 표시한다.
4. [mtr_t.Command.execute](04_mtr_t.Command.execute/README.md)가 예약, 복사, flush list 추가, 래치 해제를 순서대로 부른다.
5. [log_buffer_reserve](05_log_buffer_reserve/README.md)가 `fetch_add` 한 번으로 LSN 범위를 예약한다.
6. [log_buffer_write](06_log_buffer_write/README.md)가 블록 헤더와 트레일러를 건너뛰며 log buffer 에 복사한다.
7. [log_buffer_write_completed](07_log_buffer_write_completed/README.md)가 `recent_written` 에 링크를 걸어 복사가 끝났음을 알린다.
8. [mtr_t.Command.add_dirty_blocks_to_flush_list](08_mtr_t.Command.add_dirty_blocks_to_flush_list/README.md)가 페이지에 LSN 을 찍고 flush list 에 붙인다.
9. [log_writer](09_log_writer/README.md)가 구멍 없는 구간을 파일에 쓰고 `write_lsn` 을 올린다.
10. [log_flusher](10_log_flusher/README.md)가 fsync 하고 `flushed_to_disk_lsn` 을 올린다.

## 결과가 쓰이는 곳

```text
 mtr->m_commit_lsn (= handle.end_lsn)
      --> 트랜잭션 커밋이 이 lsn 까지 log_write_up_to 로 기다린다  [커밋과 binlog 2PC]

 페이지의 oldest_modification / newest_modification
      --> oldest 는 flush list 의 순서와 checkpoint LSN 계산의 재료  [페이지 플러시...]
      --> newest 는 페이지를 쓰기 전에 redo 를 어디까지 맞출지 정한다
      --> newest 는 페이지 헤더 FIL_PAGE_LSN 에 찍히고, 복구가 레코드의 start_lsn 과 비교한다 (log0recv.cc L2632)

 buf_flush_list_added 의 smallest_not_added_lsn
      --> checkpoint 는 이 값보다 앞으로 갈 수 없다

 write_lsn, flushed_to_disk_lsn
      --> 커밋 대기자, 페이지 쓰기 전 WAL 검사, checkpoint 상한
```

## 다루지 않는 것

redo 레코드를 `m_log` 에 쓰는 쪽(`mlog_write_initial_log_record`, `mlog_open` 과 레코드 타입별 바이트 배치)은 [redo 로그 파일과 mlog 타입](../../structure/redo-log-files/README.md)에, `m_memo` 의 래치 종류와 `memo_push` 는 [메모리 구조](../../structure/memory-structures/README.md)에 둔다. log buffer 크기 변경(`log_buffer_x_lock_enter`, `log_buffer_resize`), write-ahead 와 불완전 블록 쓰기의 세부(`compute_how_much_to_write`, `copy_to_write_ahead_buffer`), `log_write_notifier` 와 `log_flush_notifier` 스레드의 이벤트 슬롯 배분, redo 파일을 만들고 지우는 `log_files_governor`, redo 아카이브와 clone 소비자, `ALTER INSTANCE DISABLE INNODB REDO_LOG` 의 `mtr_t::Logging` 은 요약만 했다.

## 하위 메서드

- [01 mtr_t.start](01_mtr_t.start/README.md)
- [02 mtr_t.commit](02_mtr_t.commit/README.md)
- [03 mtr_t.Command.prepare_write](03_mtr_t.Command.prepare_write/README.md)
- [04 mtr_t.Command.execute](04_mtr_t.Command.execute/README.md)
- [05 log_buffer_reserve](05_log_buffer_reserve/README.md)
- [06 log_buffer_write](06_log_buffer_write/README.md)
- [07 log_buffer_write_completed](07_log_buffer_write_completed/README.md)
- [08 mtr_t.Command.add_dirty_blocks_to_flush_list](08_mtr_t.Command.add_dirty_blocks_to_flush_list/README.md)
- [09 log_writer](09_log_writer/README.md)
- [10 log_flusher](10_log_flusher/README.md)
