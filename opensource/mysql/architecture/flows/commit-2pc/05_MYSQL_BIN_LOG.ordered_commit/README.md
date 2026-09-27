# MYSQL_BIN_LOG::ordered_commit

상위: [커밋과 binlog 2PC](../README.md)

**binlog 그룹 커밋(BGC)의 본체다.** 트랜잭션 하나는 FLUSH -> SYNC -> COMMIT 세 스테이지를 차례로 지나는데, 스테이지마다 큐가 있고 **빈 큐에 처음 들어간 스레드가 리더**가 된다. 리더는 스테이지의 뮤텍스를 잡고 그때까지 큐에 모인 스레드 전부의 일을 대신한 뒤, 모인 무리를 통째로 다음 스테이지 큐에 넣는다. 팔로워는 `tx_commit_pending` 이 false 가 될 때까지 잠들었다가 `finish_commit` 으로 나간다. 그래서 fsync 한 번이 여러 트랜잭션 몫이 되고, binlog 에 쓴 순서와 엔진 커밋 순서가 같아진다(`binlog_order_commits=ON` 일 때).

## 위치

`sql` / `binlog.cc` L7895-L8204 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/binlog.cc#L7895-L8204))

## 실제 코드

준비와 FLUSH 스테이지 입장이다. 팔로워면 여기서 잠들었다가 `finish_commit` 으로 돌아간다.

`sql` / `binlog.cc` L7895-L7911 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/binlog.cc#L7895-L7911))

```cpp
// binlog.cc L7895-L7911
int MYSQL_BIN_LOG::ordered_commit(THD *thd, bool all, bool skip_commit) {
  DBUG_TRACE;
  int flush_error = 0, sync_error = 0;
  my_off_t total_bytes = 0;

  CONDITIONAL_SYNC_POINT_FOR_TIMESTAMP("before_assign_session_to_bgc_ticket");
  thd->rpl_thd_ctx.binlog_group_commit_ctx().assign_ticket();

  DBUG_EXECUTE_IF("syncpoint_before_wait_on_ticket_3",
                  binlog::Bgc_ticket_manager::instance().push_new_ticket(););
  DBUG_EXECUTE_IF("begin_new_bgc_ticket",
                  binlog::Bgc_ticket_manager::instance().push_new_ticket(););

  DBUG_EXECUTE_IF("crash_commit_before_log", DBUG_SUICIDE(););
  init_thd_variables(thd, all, skip_commit);
  DBUG_PRINT("enter", ("commit_pending: %s, commit_error: %d, thread_id: %u",
                       YESNO(thd->tx_commit_pending), thd->commit_error,
```

`sql` / `binlog.cc` L7938-L7976 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/binlog.cc#L7938-L7976))

```cpp
// binlog.cc L7938-L7976
  /*
    Stage #1: flushing transactions to binary log

    While flushing, we allow new threads to enter and will process
    them in due time. Once the queue was empty, we cannot reap
    anything more since it is possible that a thread entered and
    appointed itself leader for the flush phase.
  */

  if (change_stage(thd, Commit_stage_manager::BINLOG_FLUSH_STAGE, thd, nullptr,
                   &LOCK_log)) {
    DBUG_PRINT("return", ("Thread ID: %u, commit_error: %d", thd->thread_id(),
                          thd->commit_error));
    return finish_commit(thd);
  }

  THD *wait_queue = nullptr, *final_queue = nullptr;
  mysql_mutex_t *leave_mutex_before_commit_stage = nullptr;
  my_off_t flush_end_pos = 0;
  bool update_binlog_end_pos_after_sync;
  if (unlikely(!is_open())) {
    final_queue = fetch_and_process_flush_stage_queue(true);
    leave_mutex_before_commit_stage = &LOCK_log;
    /*
      binary log is closed, flush stage and sync stage should be
      ignored. Binlog cache should be cleared, but instead of doing
      it here, do that work in 'finish_commit' function so that
      leader and followers thread caches will be cleared.
    */
    goto commit_stage;
  }
  DEBUG_SYNC(thd, "waiting_in_the_middle_of_flush_stage");
  flush_error = process_flush_stage_queue(&total_bytes, &wait_queue);

  if (flush_error == 0 && total_bytes > 0)
    flush_error = flush_cache_to_file(&flush_end_pos);
  DBUG_EXECUTE_IF("crash_after_flush_binlog", DBUG_SUICIDE(););

  update_binlog_end_pos_after_sync = (get_sync_period() == 1);
```

SYNC 스테이지다. FLUSH 에서 모인 무리(`wait_queue`)를 넘기며 들어간다.

`sql` / `binlog.cc` L8011-L8059 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/binlog.cc#L8011-L8059))

```cpp
// binlog.cc L8011-L8059
  /*
    Stage #2: Syncing binary log file to disk
  */

  if (change_stage(thd, Commit_stage_manager::SYNC_STAGE, wait_queue, &LOCK_log,
                   &LOCK_sync)) {
    DBUG_PRINT("return", ("Thread ID: %u, commit_error: %d", thd->thread_id(),
                          thd->commit_error));
    return finish_commit(thd);
  }

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

  if (update_binlog_end_pos_after_sync && flush_error == 0 && sync_error == 0) {
    THD *tmp_thd = final_queue;
    const char *binlog_file = nullptr;
    my_off_t pos = 0;

    while (tmp_thd != nullptr) {
      if (tmp_thd->commit_error == THD::CE_NONE) {
        tmp_thd->get_trans_fixed_pos(&binlog_file, &pos);
      }
      tmp_thd = tmp_thd->next_to_commit;
    }

    if (binlog_file != nullptr && pos > 0) {
      update_binlog_end_pos(binlog_file, pos);
    }
  }
```

COMMIT 스테이지와 AFTER_COMMIT 스테이지다.

`sql` / `binlog.cc` L8081-L8140 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/binlog.cc#L8081-L8140))

```cpp
// binlog.cc L8081-L8140
commit_stage:
  /* Clone needs binlog commit order. */
  if ((opt_binlog_order_commits || Clone_handler::need_commit_order()) &&
      (sync_error == 0 || binlog_error_action != ABORT_SERVER)) {
    if (change_stage(thd, Commit_stage_manager::COMMIT_STAGE, final_queue,
                     leave_mutex_before_commit_stage, &LOCK_commit)) {
      DBUG_PRINT("return", ("Thread ID: %u, commit_error: %d", thd->thread_id(),
                            thd->commit_error));
      return finish_commit(thd);
    }
    THD *commit_queue =
        Commit_stage_manager::get_instance().fetch_queue_acquire_lock(
            Commit_stage_manager::COMMIT_STAGE);
    DBUG_EXECUTE_IF("semi_sync_3-way_deadlock",
                    DEBUG_SYNC(thd, "before_process_commit_stage_queue"););

    if (flush_error == 0 && sync_error == 0)
      sync_error = call_after_sync_hook(commit_queue);

    /*
      process_commit_stage_queue will call update_on_commit or
      update_on_rollback for the GTID owned by each thd in the queue.

      This will be done this way to guarantee that GTIDs are added to
      gtid_executed in order, to avoid creating unnecessary temporary
      gaps and keep gtid_executed as a single interval at all times.

      If we allow each thread to call update_on_commit only when they
      are at finish_commit, the GTID order cannot be guaranteed and
      temporary gaps may appear in gtid_executed. When this happen,
      the server would have to add and remove intervals from the
      Gtid_set, and adding and removing intervals requires a mutex,
      which would reduce performance.
    */
    process_commit_stage_queue(thd, commit_queue);

    /**
     * After commit stage
     */
    if (change_stage(thd, Commit_stage_manager::AFTER_COMMIT_STAGE,
                     commit_queue, &LOCK_commit, &LOCK_after_commit)) {
      DBUG_PRINT("return", ("Thread ID: %u, commit_error: %d", thd->thread_id(),
                            thd->commit_error));
      return finish_commit(thd);
    }

    THD *after_commit_queue =
        Commit_stage_manager::get_instance().fetch_queue_acquire_lock(
            Commit_stage_manager::AFTER_COMMIT_STAGE);

    process_after_commit_stage_queue(thd, after_commit_queue);

    final_queue = after_commit_queue;
    mysql_mutex_unlock(&LOCK_after_commit);
  } else {
    if (leave_mutex_before_commit_stage)
      mysql_mutex_unlock(leave_mutex_before_commit_stage);
    if (flush_error == 0 && sync_error == 0)
      sync_error = call_after_sync_hook(final_queue);
  }
```

모두 끝나면 팔로워를 깨우고 리더 자신도 `finish_commit` 을 지난다.

`sql` / `binlog.cc` L8148-L8166 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/binlog.cc#L8148-L8166))

```cpp
// binlog.cc L8148-L8166
  /* Extract the rotate settings of all thread before signal done */
  const auto [check_rotate, force_rotate] =
      Binlog_group_commit_ctx::aggregate_rotate_settings(final_queue);

  DEBUG_SYNC(thd, "before_signal_done");
  /* Commit done so signal all waiting threads */
  Commit_stage_manager::get_instance().signal_done(final_queue);
  DBUG_EXECUTE_IF("block_leader_after_delete", {
    const char action[] = "now SIGNAL leader_proceed";
    assert(!debug_sync_set_action(thd, STRING_WITH_LEN(action)));
  };);

  /*
    Finish the commit before executing a rotate, or run the risk of a
    deadlock. We don't need the return value here since it is in
    thd->commit_error, which is returned below.
  */
  (void)finish_commit(thd);
  DEBUG_SYNC(thd, "bgc_after_commit_stage_before_rotation");
```

스테이지 입장(`change_stage` -> `enroll_for`)이 리더와 팔로워를 가른다. 큐가 비어 있었으면 리더다.

`sql` / `binlog.cc` L7651-L7677 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/binlog.cc#L7651-L7677))

```cpp
// binlog.cc L7651-L7677
bool MYSQL_BIN_LOG::change_stage(THD *thd [[maybe_unused]],
                                 Commit_stage_manager::StageID stage,
                                 THD *queue, mysql_mutex_t *leave_mutex,
                                 mysql_mutex_t *enter_mutex) {
  DBUG_TRACE;
  DBUG_PRINT("enter", ("thd: 0x%llx, stage: %s, queue: 0x%llx", (ulonglong)thd,
                       g_stage_name[stage], (ulonglong)queue));
  assert(0 <= stage && stage < Commit_stage_manager::STAGE_COUNTER);
  assert(enter_mutex);
  assert(queue);
  /*
    enroll_for will release the leave_mutex once the sessions are
    queued.
  */
  if (!Commit_stage_manager::get_instance().enroll_for(
          stage, queue, leave_mutex, enter_mutex)) {
    // enroll_for() returns false when this THD became a follower and was
    // signaled by the stage leader. Callers interpret this as "my transaction
    // was processed by the leader" and leave ordered_commit() through
    // finish_commit().
    assert(!thd->tx_commit_pending);
    assert(!thd_get_cache_mngr(thd)->dbug_any_finalized());
    return true;
  }

  return false;
}
```

`sql` / `rpl_commit_stage_manager.cc` L238-L249 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/rpl_commit_stage_manager.cc#L238-L249))

```cpp
// rpl_commit_stage_manager.cc L238-L249
bool Commit_stage_manager::enroll_for(StageID stage, THD *thd,
                                      mysql_mutex_t *stage_mutex,
                                      mysql_mutex_t *enter_mutex) {
  DBUG_TRACE;

  // If the queue was empty: we're the leader for this batch
  DBUG_PRINT("debug",
             ("Enqueue 0x%llx to queue for stage %d", (ulonglong)thd, stage));

  thd->rpl_thd_ctx.binlog_group_commit_ctx().assign_ticket();
  bool leader = this->append_to(stage, thd);

```

`sql` / `rpl_commit_stage_manager.cc` L309-L316 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/rpl_commit_stage_manager.cc#L309-L316))

```cpp
// rpl_commit_stage_manager.cc L309-L316
    Commit_order_manager::finish_one(thd);
  }

  /*
    The stage mutex can be nullptr if we are enrolling for the first
    stage.
  */
  if (stage_mutex) mysql_mutex_unlock(stage_mutex);
```

`sql` / `rpl_commit_stage_manager.cc` L354-L390 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/rpl_commit_stage_manager.cc#L354-L390))

```cpp
// rpl_commit_stage_manager.cc L354-L390
  /*
    If the queue was not empty, we're a follower and wait for the
    leader to process the queue. If we were holding a mutex, we have
    to release it before going to sleep.
  */
  if (!leader) {
    CONDITIONAL_SYNC_POINT_FOR_TIMESTAMP("before_follower_wait");
    mysql_mutex_lock(&m_lock_done);
#ifndef NDEBUG
    /*
      Leader can be awaiting all-clear to preempt follower's execution.
      With setting the status the follower ensures it won't execute anything
      including thread-specific code.
    */
    thd->get_transaction()->m_flags.ready_preempt = true;
    if (leader_await_preempt_status) mysql_cond_signal(&m_cond_preempt);
#endif
    while (thd->tx_commit_pending) {
      if (stage == COMMIT_ORDER_FLUSH_STAGE) {
        mysql_cond_wait(&m_stage_cond_commit_order, &m_lock_done);
      } else {
        mysql_cond_wait(&m_stage_cond_binlog, &m_lock_done);
      }
    }

    mysql_mutex_unlock(&m_lock_done);
    return false;
  }

#ifndef NDEBUG
  if (stage == Commit_stage_manager::SYNC_STAGE)
    DEBUG_SYNC(thd, "bgc_between_flush_and_sync");
#endif

  if (leader && enter_mutex != nullptr) {
    mysql_mutex_lock(enter_mutex);
  }
```

팔로워를 깨우는 쪽이다.

`sql` / `rpl_commit_stage_manager.cc` L500-L515 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/rpl_commit_stage_manager.cc#L500-L515))

```cpp
// rpl_commit_stage_manager.cc L500-L515
void Commit_stage_manager::signal_done(THD *queue, StageID stage) {
  mysql_mutex_lock(&m_lock_done);

  for (THD *thd = queue; thd; thd = thd->next_to_commit) {
    thd->tx_commit_pending = false;
    thd->rpl_thd_ctx.binlog_group_commit_ctx().reset();
  }

  /* if thread belong to commit order wake only commit order queue threads */
  if (stage == COMMIT_ORDER_FLUSH_STAGE)
    mysql_cond_broadcast(&m_stage_cond_commit_order);
  else
    mysql_cond_broadcast(&m_stage_cond_binlog);

  mysql_mutex_unlock(&m_lock_done);
}
```

## 동작 흐름

```text
 L7901  assign_ticket                            BGC 티켓 (그룹 경계)
 L7909  init_thd_variables                       tx_commit_pending = true, durability = HA_IGNORE_DURABILITY (L7430)
 L7930  복제 적용 스레드면 커밋 순서 차례를 기다린다

 FLUSH  (enter LOCK_log)
 L7947  change_stage(BINLOG_FLUSH_STAGE, thd, nullptr, &LOCK_log)
          팔로워면 L7951 return finish_commit(thd)     <-- 대부분의 스레드는 여기서 끝
 L7958  binlog 가 닫혀 있으면 flush, sync 를 건너뛰고 commit_stage 로
 L7970  [06] process_flush_stage_queue(&total_bytes, &wait_queue)
 L7973  flush_cache_to_file                       binlog 파일 버퍼를 write()
 L7976  update_binlog_end_pos_after_sync = (sync_binlog == 1)
 L7987  after_flush 훅
 L7993  sync_binlog != 1 이면 지금 end_pos 갱신   덤프 스레드가 여기까지 읽을 수 있다
 L8002  flush 오류면 binlog_error_action 처리

 SYNC   (leave LOCK_log, enter LOCK_sync)
 L8015  change_stage(SYNC_STAGE, wait_queue, &LOCK_log, &LOCK_sync)
 L8030  이번에 sync 할 차례면 binlog_group_commit_sync_delay 만큼 더 모은다
 L8035  final_queue = SYNC 큐 전체
 L8040  [07] sync_binlog_file(false)
 L8044  sync_binlog == 1 이면 sync 뒤에 end_pos 갱신  (L8057)

 COMMIT (leave LOCK_sync, enter LOCK_commit)
 L8081  commit_stage:
 L8083  binlog_order_commits 이면
 L8085    change_stage(COMMIT_STAGE, final_queue, ..., &LOCK_commit)
 L8098    after_sync 훅
 L8115    [08] process_commit_stage_queue(thd, commit_queue)
 L8120    AFTER_COMMIT 스테이지, L8131 after_commit 훅
 L8135  아니면 뮤텍스를 풀고 각 스레드가 finish_commit 에서 스스로 엔진 커밋

 L8146  sync 오류 처리 (모든 뮤텍스를 푼 뒤)
 L8154  signal_done(final_queue)                   팔로워 전원 tx_commit_pending = false, 깨움
 L8165  finish_commit(thd)                         리더 자신
 L8191  필요하면 rotate (binlog 파일 교체), purge
 L8203  return commit_error == CE_COMMIT_ERROR
```

세 스레드 T1, T2, T3 가 거의 동시에 커밋할 때의 시간축이다. T1 이 리더가 되고 T2, T3 는 한 번도 binlog 에 직접 쓰지 않는다.

```text
 그룹 커밋 시간축 (T1 리더, T2 T3 팔로워)

 스레드  동작                                   설명
 T1      enroll FLUSH                           큐가 비어 있어 리더
 T1      lock LOCK_log                          (enroll_for L388-L389)
 T2      enroll FLUSH                           큐에 T1 이 있어 팔로워, 잠든다
 T1      fetch FLUSH queue = [T1, T2]           큐가 비었다
 T3      enroll FLUSH                           빈 큐라 다음 그룹의 리더, LOCK_log 를 기다린다
 T1      ha_flush_logs                          redo 1 회
 T1      T1, T2 cache -> binlog write
 T1      enroll SYNC [T1, T2], unlock LOCK_log
 T3      lock LOCK_log                          자기 그룹의 FLUSH 시작
 T1      lock LOCK_sync, fsync                  binlog fsync 1 회
 T1      enroll COMMIT, unlock LOCK_sync, lock LOCK_commit
 T1      commit T1, commit T2                   엔진 커밋, 이 순서
 T1      signal_done([T1, T2])
 T2      wake up -> finish_commit               OK 패킷
 T1      finish_commit                          OK 패킷

 스테이지마다 뮤텍스가 달라서 T3 의 FLUSH 와 T1 의 SYNC 가 겹칠 수 있다
 큐를 fetch 하는 순간 (binlog.cc L7459-L7461) 이 그룹의 경계다. 비운 큐에 다음 리더가 선다 (주석 L7451-L7453)
```

```text
 스테이지와 뮤텍스, 큐 (Commit_stage_manager::StageID)

 StageID             mutex               lines         하는 일
 BINLOG_FLUSH_STAGE  LOCK_log            L7947-L8007   redo flush, 캐시 -> binlog write
 SYNC_STAGE          LOCK_sync           L8015-L8059   binlog fsync
 COMMIT_STAGE        LOCK_commit         L8085-L8115   엔진 커밋 (순서대로)
 AFTER_COMMIT_STAGE  LOCK_after_commit   L8120-L8134   after_commit 훅

 앞 스테이지의 뮤텍스는 다음 스테이지 큐에 줄을 선 뒤에 푼다 (enroll_for L316)
```

## 결과가 쓰이는 곳

```text
 thd->commit_error
      --> finish_commit 과 [04] 가 RESULT_INCONSISTENT 로 바꿀지 판단
 binlog end_pos (update_binlog_end_pos)
      --> 덤프 스레드가 복제본에 보낼 수 있는 끝. sync_binlog=1 이면 fsync 뒤에야 전진한다
 커밋 순서
      --> binlog 순서 = InnoDB 커밋 순서. InnoDB 는 이것을 서버가 보장한다고 가정한다 (ha_innodb.cc L6030-L6037 주석)
```

## 다루지 않는 것

복제 적용 스레드의 커밋 순서(`Commit_order_manager`, `COMMIT_ORDER_FLUSH_STAGE` 와 리더 교대), BGC 티켓(`Bgc_ticket_manager`), `binlog_group_commit_sync_delay` / `no_delay_count`, semi-sync 의 `after_sync`, binlog 오류 처리(`handle_binlog_flush_or_sync_error`, `binlog_error_action`), 로테이션과 자동 purge, 디버그 동기점은 이 흐름의 곁가지라 줄만 적었다.
