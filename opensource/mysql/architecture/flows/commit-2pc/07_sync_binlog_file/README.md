# sync_binlog_file

상위: [커밋과 binlog 2PC](../README.md)

**`sync_binlog` 이 실제로 동작하는 자리다.** SYNC 스테이지 리더가 한 번 부르고, 카운터(`sync_counter`)가 `sync_binlog` 에 닿았을 때만 binlog 파일을 fsync 한다. 이 fsync 가 끝난 순간이 이 그룹 트랜잭션들의 커밋점이다. 그 뒤에 크래시가 나면 PREPARED 트랜잭션은 binlog 에 XID 가 있으니 커밋된다(크래시 창 D). 앞 단계 FLUSH 의 `flush_cache_to_file` 은 write 만 하고 fsync 하지 않는다.

## 위치

`sql` / `binlog.cc` L7700-L7721 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/binlog.cc#L7700-L7721))

## 실제 코드

`sql` / `binlog.cc` L7700-L7721 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/binlog.cc#L7700-L7721))

```cpp
// binlog.cc L7700-L7721
std::pair<bool, bool> MYSQL_BIN_LOG::sync_binlog_file(bool force) {
  bool synced = false;
  unsigned int sync_period = get_sync_period();
  if (force || (sync_period && ++sync_counter >= sync_period)) {
    sync_counter = 0;

    /*
      There is a chance that binlog file could be closed by 'RESET BINARY LOGS
      AND GTIDS' or or 'FLUSH LOGS' just after the leader releases LOCK_log and
      before it acquires LOCK_sync log. So it should check if m_binlog_file is
      opened.
    */
    if (DBUG_EVALUATE_IF("simulate_error_during_sync_binlog_file", 1,
                         m_binlog_file->is_open() && m_binlog_file->sync())) {
      THD *thd = current_thd;
      thd->commit_error = THD::CE_SYNC_ERROR;
      return std::make_pair(true, synced);
    }
    synced = true;
  }
  return std::make_pair(false, synced);
}
```

FLUSH 스테이지 끝에서 파일 버퍼를 write 하는 짝이다.

`sql` / `binlog.cc` L7687-L7695 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/binlog.cc#L7687-L7695))

```cpp
// binlog.cc L7687-L7695
int MYSQL_BIN_LOG::flush_cache_to_file(my_off_t *end_pos_var) {
  if (m_binlog_file->flush()) {
    THD *thd = current_thd;
    thd->commit_error = THD::CE_FLUSH_ERROR;
    return ER_ERROR_ON_WRITE;
  }
  *end_pos_var = m_binlog_file->position();
  return 0;
}
```

SYNC 스테이지에서의 호출이다. sync 할 차례면 `binlog_group_commit_sync_delay` 만큼 더 모은다.

`sql` / `binlog.cc` L8022-L8042 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/binlog.cc#L8022-L8042))

```cpp
// binlog.cc L8022-L8042
  /*
    Shall introduce a delay only if it is going to do sync
    in this ongoing SYNC stage. The "+1" used below in the
    if condition is to count the ongoing sync stage.
    When sync_binlog=0 (where we never do sync in BGC group),
    it is considered as a special case and delay will be executed
    for every group just like how it is done when sync_binlog= 1.
  */
  if (!flush_error && (sync_counter + 1 >= get_sync_period()))
    Commit_stage_manager::get_instance().wait_count_or_timeout(
        opt_binlog_group_commit_sync_no_delay_count,
        opt_binlog_group_commit_sync_delay, Commit_stage_manager::SYNC_STAGE);

  final_queue = Commit_stage_manager::get_instance().fetch_queue_acquire_lock(
      Commit_stage_manager::SYNC_STAGE);

  if (flush_error == 0 && total_bytes > 0) {
    DEBUG_SYNC(thd, "before_sync_binlog_file");
    std::pair<bool, bool> result = sync_binlog_file(false);
    sync_error = result.first;
  }
```

주기는 시스템 변수 `sync_binlog` 이고 기본값은 1 이다.

`sql` / `binlog.h` L218-L218 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/binlog.h#L218-L218))

```cpp
// binlog.h L218-L218
  inline uint get_sync_period() { return *sync_period_ptr; }
```

`sql` / `sys_vars.cc` L6276-L6282 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sys_vars.cc#L6276-L6282))

```cpp
// sys_vars.cc L6276-L6282
static Sys_var_uint Sys_sync_binlog_period(
    "sync_binlog",
    "Synchronously flush binary log to disk after"
    " every #th write to the file. Use 0 to disable synchronous"
    " flushing",
    GLOBAL_VAR(sync_binlog_period), CMD_LINE(REQUIRED_ARG),
    VALID_RANGE(0, UINT_MAX), DEFAULT(1), BLOCK_SIZE(1));
```

## 동작 흐름

```text
 L7701  synced = false
 L7702  sync_period = get_sync_period()          = sync_binlog
 L7703  force 이거나 (sync_period != 0 이고 ++sync_counter >= sync_period)
 L7704    sync_counter = 0
 L7712    binlog 가 열려 있으면 m_binlog_file->sync()   fsync
            실패면 commit_error = CE_SYNC_ERROR, return (true, false)
 L7718    synced = true
 L7720  return (false, synced)

 호출 쪽 (ordered_commit)
 L8030  이번 그룹이 sync 할 차례면 wait_count_or_timeout   (sync_binlog=0 도 매 그룹 지연, 주석 L8026-L8028)
 L8035  final_queue = SYNC 큐 전체                            지연 동안 들어온 스레드까지 포함
 L8038  flush 오류가 없고 쓴 바이트가 있으면
 L8040    sync_binlog_file(false)
```

`sync_binlog` 값에 따라 fsync 가 몇 그룹에 한 번 일어나는지, 그리고 그 사이 크래시가 무엇을 잃는지다.

```text
 sync_binlog 과 fsync (그룹 G1, G2, G3 ... 이 차례로 SYNC 를 지난다)

 sync_binlog  G1     G2     G3     G4     크래시 때 잃을 수 있는 것
 1            fsync  fsync  fsync  fsync  OK 를 받은 것은 없음 (창 C 의 그룹은 아직 OK 전)
 3            -      -      fsync  -      마지막 fsync 이후 그룹들 (OS 가 죽을 때)
 0            -      -      -      -      OS 가 아직 안 쓴 끝부분 전부 (OS 가 죽을 때)

 mysqld 만 죽고 OS 가 살아 있으면 write 한 부분(flush_cache_to_file)은 남는다
 binlog 를 잃은 트랜잭션은 InnoDB 에 무엇이 남았느냐로 갈린다
   PREPARED 로 남았으면  XID 가 없어 롤백된다. 이미 OK 를 받았다면 커밋 응답이 사라진 것이다
   커밋 redo 까지 디스크에 있었으면  InnoDB 에만 커밋되어 있고 binlog 에는 없다
```

```text
 binlog 의 세 위치 (FLUSH 에서 SYNC 까지)

 움직이는 곳                        도착하는 곳
 [06] flush_thread_caches           THD 캐시 -> binlog IO 캐시
 flush_cache_to_file L7688          IO 캐시 -> 파일 (OS 캐시), write(). flush_end_pos
 sync_binlog_file L7712             OS 캐시 -> 디스크, fsync
 update_binlog_end_pos              binlog end_pos. 덤프 스레드가 보낼 수 있는 끝
                                    sync_binlog=1 이면 fsync 뒤 (L8057), 아니면 write 뒤 (L7993)
```

## 결과가 쓰이는 곳

```text
 (error, synced)
      --> [05] 가 sync_error 로 받아 COMMIT 스테이지에 들어갈지, binlog_error_action 을 적용할지
 CE_SYNC_ERROR
      --> handle_binlog_flush_or_sync_error (binlog.cc L8146)
 fsync 된 binlog
      --> [크래시 복구] 의 Binlog_recovery 가 읽는 XID 목록의 원천
```

## 다루지 않는 것

`binlog_group_commit_sync_delay` 와 `binlog_group_commit_sync_no_delay_count` 의 대기 구현(`wait_count_or_timeout`), `force=true` 로 부르는 다른 경로(binlog.cc L6104), 로테이션 때의 sync, `binlog_error_action=ABORT_SERVER` 의 처리, relay log 의 `sync_relay_log` 는 이 흐름의 곁가지라 줄만 적었다.
