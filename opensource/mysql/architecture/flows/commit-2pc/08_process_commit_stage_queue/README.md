# process_commit_stage_queue

상위: [커밋과 binlog 2PC](../README.md)

**COMMIT 스테이지 리더가 큐의 THD 를 순서대로 돌며 엔진 커밋을 대신 부르는 곳이다.** 리더 스레드가 `Thd_backup_and_restore` 로 팔로워의 THD 를 잠시 입고 `ha_commit_low` 를 부르므로, 팔로워의 InnoDB 커밋은 팔로워 스레드가 아니라 리더 스레드에서 일어난다. 큐 순서가 binlog 에 쓴 순서이므로 엔진 커밋 순서가 binlog 순서와 같아진다. 루프가 끝나면 GTID 를 그룹 단위로 `gtid_executed` 에 올리고 prepared XID 수를 내린다.

## 위치

`sql` / `binlog.cc` L7550-L7614 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/binlog.cc#L7550-L7614))

## 실제 코드

`sql` / `binlog.cc` L7550-L7614 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/binlog.cc#L7550-L7614))

```cpp
// binlog.cc L7550-L7614
void MYSQL_BIN_LOG::process_commit_stage_queue(THD *thd, THD *first) {
  mysql_mutex_assert_owner(&LOCK_commit);
#ifndef NDEBUG
  thd->get_transaction()->m_flags.ready_preempt =
      true;  // formality by the leader
#endif
  for (THD *head = first; head; head = head->next_to_commit) {
    DBUG_PRINT("debug", ("Thread ID: %u, commit_error: %d, commit_pending: %s",
                         head->thread_id(), head->commit_error,
                         YESNO(head->tx_commit_pending)));
    DBUG_EXECUTE_IF(
        "block_leader_after_delete",
        if (thd != head) { DBUG_SET("+d,after_delete_wait"); };);
    /*
      If flushing failed, set commit_error for the session, skip the
      transaction and proceed with the next transaction instead. This
      will mark all threads as failed, since the flush failed.

      If flush succeeded, attach to the session and commit it in the
      engines.
    */
#ifndef NDEBUG
    Commit_stage_manager::get_instance().clear_preempt_status(head);
#endif
    if (head->get_transaction()->sequence_number != SEQ_UNINIT) {
      mysql_mutex_lock(&LOCK_replica_trans_dep_tracker);
      m_dependency_tracker.update_max_committed(head);
      mysql_mutex_unlock(&LOCK_replica_trans_dep_tracker);
    }
    /*
      Flush/Sync error should be ignored and continue
      to commit phase. And thd->commit_error cannot be
      COMMIT_ERROR at this moment.
    */
    assert(head->commit_error != THD::CE_COMMIT_ERROR);
    Thd_backup_and_restore switch_thd(thd, head);
    bool all = head->get_transaction()->m_flags.real_commit;
    assert(!head->get_transaction()->m_flags.commit_low ||
           head->get_transaction()->m_flags.ready_preempt);
    ::finish_transaction_in_engines(head, all, false);
    DBUG_PRINT("debug", ("commit_error: %d, commit_pending: %s",
                         head->commit_error, YESNO(head->tx_commit_pending)));
  }

  /*
    Handle the GTID of the threads.
    gtid_executed table is kept updated even though transactions fail to be
    logged. That's required by slave auto positioning.
  */
  gtid_state->update_commit_group(first);

  for (THD *head = first; head; head = head->next_to_commit) {
    Thd_backup_and_restore switch_thd(thd, head);
    auto all = head->get_transaction()->m_flags.real_commit;
    // Mark transaction as prepared in TC, if applicable
    trx_coordinator::set_prepared_in_tc_in_engines(head, all);
    /*
      Decrement the prepared XID counter after storage engine commit.
      We also need decrement the prepared XID when encountering a
      flush error or session attach error for avoiding 3-way deadlock
      among user thread, rotate thread and dump thread.
    */
    if (head->get_transaction()->m_flags.xid_written) dec_prep_xids(head);
  }
}
```

`commit_low` 표시가 있으면 엔진 커밋을 한다. 이 표시는 [05] 의 `init_thd_variables` 가 켜 둔 것이다(XA PREPARE 가 아니면 켜진다, binlog.cc L7433).

`sql` / `binlog.cc` L10749-L10757 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/binlog.cc#L10749-L10757))

```cpp
// binlog.cc L10749-L10757
void finish_transaction_in_engines(THD *thd, bool all, bool run_after_commit) {
  if (thd->get_transaction()->m_flags.commit_low) {
    if (trx_coordinator::commit_in_engines(thd, all, run_after_commit))
      thd->commit_error = THD::CE_COMMIT_ERROR;
  } else if (is_xa_rollback(thd)) {
    if (trx_coordinator::rollback_in_engines(thd, all))
      thd->commit_error = THD::CE_COMMIT_ERROR;
  }
}
```

`sql` / `tc_log.cc` L137-L148 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/tc_log.cc#L137-L148))

```cpp
// tc_log.cc L137-L148
bool trx_coordinator::commit_in_engines(THD *thd, bool all,
                                        bool run_after_commit) {
  if (all) {
    CONDITIONAL_SYNC_POINT_FOR_TIMESTAMP("before_commit_in_engines");
  }
  if (thd->get_transaction()
          ->xid_state()
          ->is_detached())  // if processing a detached XA, commit by XID
    return trx_coordinator::commit_detached_by_xid(thd, run_after_commit);
  else  // if not, commit normally
    return ha_commit_low(thd, all, run_after_commit);
}
```

`ha_commit_low` 가 등록된 엔진마다 `commit` 콜백을 부른다. binlog 의 `commit` 은 할 일이 없고(binlog.cc L2606-L2612) InnoDB 는 [09] `innobase_commit` 이다.

`sql` / `handler.cc` L1959-L1964 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/handler.cc#L1959-L1964))

```cpp
// handler.cc L1959-L1964
int ha_commit_low(THD *thd, bool all, bool run_after_commit) {
  int error = 0;
  Transaction_ctx *trn_ctx = thd->get_transaction();
  const Transaction_ctx::enum_trx_scope trx_scope =
      all ? Transaction_ctx::SESSION : Transaction_ctx::STMT;
  auto ha_list = trn_ctx->ha_trx_info(trx_scope);
```

`sql` / `handler.cc` L1999-L2014 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/handler.cc#L1999-L2014))

```cpp
// handler.cc L1999-L2014
    for (auto &ha_info : ha_list) {
      int err;
      auto ht = ha_info.ht();
      if ((err = ht->commit(ht, thd, all))) {
        char errbuf[MYSQL_ERRMSG_SIZE];
        my_error(ER_ERROR_DURING_COMMIT, MYF(0), err,
                 my_strerror(errbuf, MYSQL_ERRMSG_SIZE, err));
        error = 1;
      }
      assert(!thd->status_var_aggregated);
      thd->status_var.ha_commit_count++;
      global_aggregated_stats.get_shard(thd->thread_id()).ha_commit_count++;
      ha_info.reset(); /* keep it conveniently zero-filled */
    }
    if (need_restore_backup_ha_data) thd->rpl_reattach_engine_ha_data();
    trn_ctx->reset_scope(trx_scope);
```

`sql` / `handler.cc` L2036-L2057 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/handler.cc#L2036-L2057))

```cpp
// handler.cc L2036-L2057
err:
  /* Free resources and perform other cleanup even for 'empty' transactions. */
  if (all) trn_ctx->cleanup();
  /*
    When the transaction has been committed, we clear the commit_low
    flag. This allow other parts of the system to check if commit_low
    was called.
  */
  trn_ctx->m_flags.commit_low = false;
  if (run_after_commit && thd->get_transaction()->m_flags.run_hooks) {
    /*
       If commit succeeded, we call the after_commit hook.

       TODO: Investigate if this can be refactored so that there is
             only one invocation of this hook in the code (in
             MYSQL_LOG_BIN::finish_commit).
    */
    if (!error) (void)RUN_HOOK(transaction, after_commit, (thd, all));
    trn_ctx->m_flags.run_hooks = false;
  }
  return error;
}
```

## 동작 흐름

```text
 L7551  LOCK_commit 를 쥐고 있어야 한다
 L7556  for (head = first; head; head = head->next_to_commit)
 L7574    sequence_number 가 있으면 의존성 추적기에 max committed 갱신  (병렬 복제용)
 L7584    commit_error 가 CE_COMMIT_ERROR 가 아님을 확인 (flush, sync 오류는 커밋 단계로 넘어온다)
 L7585    Thd_backup_and_restore switch_thd(thd, head)    리더가 head 의 THD 를 입는다
 L7586    all = real_commit                               [04] 가 받은 all
 L7589    finish_transaction_in_engines(head, all, false)
            binlog.cc L10750  commit_low 면
            tc_log.cc  L147   ha_commit_low(thd, all, run_after_commit=false)
              handler.cc L1999  for (ha_info : ha_list)
              handler.cc L2002    ht->commit(ht, thd, all)
                                    binlog    binlog_commit       할 일 없음
                                    InnoDB    [09] innobase_commit
              handler.cc L2014  reset_scope
              handler.cc L2038  all 이면 trn_ctx->cleanup()
 L7599  gtid_state->update_commit_group(first)          그룹의 GTID 를 한꺼번에
 L7601  다시 큐를 돌며
 L7605    set_prepared_in_tc_in_engines
 L7612    xid_written 이면 dec_prep_xids                 [06] 의 inc_prep_xids 와 짝
```

리더 스레드 하나가 여러 THD 를 입었다 벗으며 커밋하는 모양이다. 팔로워 스레드들은 이 동안 `enroll_for` 안에서 잠들어 있다.

```text
 COMMIT 스테이지의 스레드와 THD (그룹 [T1, T2, T3], 리더 T1)

 스레드  동작                                            설명
 T1      switch_thd(T1)  ha_commit_low -> innobase_commit
 T1      switch_thd(T2)  ha_commit_low -> innobase_commit  T2 의 trx_t 를 T1 스레드가 커밋
 T1      switch_thd(T3)  ha_commit_low -> innobase_commit
 T1      update_commit_group([T1, T2, T3])
 T1      signal_done                                      여기까지 T2, T3 는 잠들어 있다
 T2, T3  wake up -> finish_commit                         commit_low 가 이미 false 라 엔진 커밋 없음

 finish_commit 도 finish_transaction_in_engines 를 부르지만 (binlog.cc L7766)
 ha_commit_low 가 L2044 에서 commit_low = false 로 바꿔 두어 두 번 커밋하지 않는다
```

```text
 binlog_order_commits 에 따른 차이 ([05] L8083)

 ON (default)  이 함수가 리더 스레드에서 큐 순서대로 커밋한다. binlog 순서 = 엔진 커밋 순서
 OFF           COMMIT 스테이지를 건너뛰고 각 스레드가 finish_commit 에서 자기 트랜잭션을 커밋한다
               순서 보장 없음
```

## 결과가 쓰이는 곳

```text
 엔진 커밋 (innobase_commit)
      --> [09], [10]. 이 시점에 InnoDB 레코드 잠금이 풀린다
 gtid_executed
      --> update_commit_group 이 그룹 순서대로 올려 구멍 없는 구간을 유지한다 (주석 binlog.cc L8101-L8113)
 dec_prep_xids
      --> 새 binlog 파일로 넘어가는 new_file_impl 이 wait_for_prep_xids 로 이 수가 0 이 되기를 기다린다
          (binlog.cc L5711)
```

## 다루지 않는 것

의존성 추적기(`m_dependency_tracker`, 병렬 복제의 commit parent), `set_prepared_in_tc_in_engines`, 복제 적용 스레드의 `Commit_order_manager::wait`, XA ROLLBACK 경로(`is_xa_rollback`), detached XA 의 `commit_detached_by_xid`, `after_commit` 훅은 이 흐름의 곁가지라 줄만 적었다.
