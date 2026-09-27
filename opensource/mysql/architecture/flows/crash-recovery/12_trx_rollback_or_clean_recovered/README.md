# trx_rollback_or_clean_recovered

상위: [크래시 복구](../README.md)

**undo 에서 되살린 트랜잭션을 상태별로 정리하는 함수다.** 같은 함수가 두 번 불린다. 첫 번째(`all=false`)는 데이터 사전을 열기 위해 기동 스레드가 부르며 **DDL 트랜잭션만** 롤백한다. 두 번째(`all=true`)는 binlog 복구가 끝난 뒤 백그라운드 스레드가 부르며 **PREPARED 가 아닌 ACTIVE 전부**를 롤백한다. COMMITTED 로 되살아난 것은 두 번 모두 정리만 한다. PREPARED 는 절대 건드리지 않는다. 그 운명은 [11] 이 binlog 로 정하거나, 외부 XA 면 사용자가 XA COMMIT/ROLLBACK 으로 정한다.

## 위치

`storage` / `innobase` / `trx` / `trx0roll.cc` L712-L777 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0roll.cc#L712-L777))

## 실제 코드

트랜잭션 목록을 돌며 하나씩 맡긴다. 하나를 처리하면 mutex 를 놓았으므로 처음부터 다시 돈다.

`storage` / `innobase` / `trx` / `trx0roll.cc` L708-L777 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0roll.cc#L708-L777))

```cpp
// trx0roll.cc L708-L777
/** Rollback or clean up any incomplete transactions which were
 encountered in crash recovery.  If the transaction already was
 committed, then we clean up a possible insert undo log. If the
 transaction was not yet committed, then we roll it back. */
void trx_rollback_or_clean_recovered(
    bool all) /*!< in: false=roll back dictionary transactions;
               true=roll back all non-PREPARED transactions */
{
  ut_ad(!srv_read_only_mode);

  ut_a(srv_force_recovery < SRV_FORCE_NO_TRX_UNDO);
  ut_ad(!all || trx_sys_need_rollback());

  if (all) {
    ib::info(ER_IB_MSG_1189) << "Starting in background the rollback"
                                " of uncommitted transactions";
  }

  /* Note: For XA recovered transactions, we rely on MySQL to
  do rollback. They will be in TRX_STATE_PREPARED state. If the server
  is shutdown and they are still lingering in trx_sys_t::trx_list
  then the shutdown will hang. */

  /* Loop over the transaction list as long as there are
  recovered transactions to clean up or recover. */

  trx_sys_mutex_enter();
  for (bool need_one_more_scan = true; need_one_more_scan;) {
    need_one_more_scan = false;
    for (auto trx : trx_sys->rw_trx_list) {
      assert_trx_in_rw_list(trx);

      /* In case of slow shutdown, we have to wait for the background
      thread (trx_recovery_rollback) which is doing the rollbacks of
      recovered transactions. Note that it can add undo to purge.
      In case of fast shutdown we do not care if we left transactions
      not rolled back. But still we want to stop the thread, so since
      certain point of shutdown we might be sure there are no changes
      to transactions / undo. */
      if (srv_shutdown_state.load() >= SRV_SHUTDOWN_RECOVERY_ROLLBACK &&
          srv_fast_shutdown != 0) {
        ut_a(srv_shutdown_state_matches([](auto state) {
          return state == SRV_SHUTDOWN_RECOVERY_ROLLBACK ||
                 state == SRV_SHUTDOWN_EXIT_THREADS;
        }));

        trx_sys_mutex_exit();

        if (all) {
          ib::info(ER_IB_MSG_TRX_RECOVERY_ROLLBACK_NOT_COMPLETED);
        }
        return;
      }

      /* If this function does a cleanup or rollback
      then it will release the trx_sys->mutex, therefore
      we need to reacquire it before retrying the loop. */
      if (trx_rollback_or_clean_resurrected(trx, all)) {
        trx_sys_mutex_enter();
        need_one_more_scan = true;
        break;
      }
    }
  }
  trx_sys_mutex_exit();

  if (all) {
    ib::info(ER_IB_MSG_TRX_RECOVERY_ROLLBACK_COMPLETED);
  }
}
```

트랜잭션 하나의 상태별 처리다.

`storage` / `innobase` / `trx` / `trx0roll.cc` L642-L706 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0roll.cc#L642-L706))

```cpp
// trx0roll.cc L642-L706
/** Rollback or clean up any resurrected incomplete transactions. It assumes
 that the caller holds the trx_sys_t::mutex and it will release the
 lock if it does a clean up or rollback.
 @return true if the transaction was cleaned up or rolled back
 and trx_sys->mutex was released. */
static bool trx_rollback_or_clean_resurrected(
    trx_t *trx, /*!< in: transaction to rollback or clean */
    bool all)   /*!< in: false=roll back dictionary transactions;
                 true=roll back all non-PREPARED transactions */
{
  ut_ad(trx_sys_mutex_own());
  ut_ad(trx->in_rw_trx_list);

  /* Generally, an HA transaction with is_recovered && state==TRX_STATE_PREPARED
  can be committed or rolled back by a client who knows its XID at any time.
  To prove that no such state transition is possible while our thread operates,
  observe that we hold trx_sys->mutex which is required by both commit and
  rollback to deregister the trx from trx_sys->rw_trx_list during
  trx_release_impl_and_expl_locks() and we see the trx is still in this list.
  Thus, if we see is_recovered==true, then the state can not change until we
  release the trx_sys->mutex. Moreover for TRX_STATE_PREPARED we do nothing, so
  we will not interfere with an HA COMMIT or ROLLBACK. So, if XA ROLLBACK or
  COMMIT latches trx_sys->mutex before us, then we will not see the trx in the
  rw_trx_list (so trx_rollback_or_clean_resurrected() would not be called for
  this transaction in the first place), and if we latch first, then we will
  leave the trx intact. */

  trx_mutex_enter(trx);
  const bool is_recovered = trx->is_recovered;
  const trx_state_t state = trx->state.load(std::memory_order_relaxed);
  trx_mutex_exit(trx);

  if (!is_recovered) {
    ut_ad(state != TRX_STATE_COMMITTED_IN_MEMORY);
    return false;
  }

  switch (state) {
    case TRX_STATE_COMMITTED_IN_MEMORY:
      trx_sys_mutex_exit();
      ib::info(ER_IB_MSG_1188)
          << "Cleaning up trx with id " << trx_get_id_for_print(trx);

      trx_cleanup_at_db_startup(trx);
      trx_free_resurrected(trx);
      ut_ad(!trx->is_recovered);
      return true;
    case TRX_STATE_ACTIVE:
      if (all || trx->ddl_operation) {
        trx_sys_mutex_exit();
        trx_rollback_active(trx);
        trx_free_for_background(trx);
        ut_ad(!trx->is_recovered);
        return true;
      }
      return false;
    case TRX_STATE_PREPARED:
      return false;
    case TRX_STATE_NOT_STARTED:
    case TRX_STATE_FORCED_ROLLBACK:
      break;
  }

  ut_error;
}
```

첫 번째 호출, 기동 중 데이터 사전 복구다.

`storage` / `innobase` / `srv` / `srv0start.cc` L2108-L2120 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/srv/srv0start.cc#L2108-L2120))

```cpp
// srv0start.cc L2108-L2120
/** On a restart, initialize the remaining InnoDB subsystems so that
any tables (including data dictionary tables) can be accessed. */
void srv_dict_recover_on_restart() {
  /* Resurrect locks for dictionary transactions */
  trx_resurrect_locks(false);

  /* Roll back any recovered data dictionary transactions, so
  that the data dictionary tables will be free of any locks.
  The data dictionary latch should guarantee that there is at
  most one data dictionary transaction active at a time. */
  if (srv_force_recovery < SRV_FORCE_NO_TRX_UNDO && trx_sys_need_rollback()) {
    trx_rollback_or_clean_recovered(false);
  }
```

두 번째 호출, DDL 복구 뒤 띄우는 백그라운드 스레드다.

`storage` / `innobase` / `srv` / `srv0start.cc` L2260-L2271 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/srv/srv0start.cc#L2260-L2271))

```cpp
// srv0start.cc L2260-L2271
void srv_start_threads_after_ddl_recovery() {
  if (srv_force_recovery < SRV_FORCE_NO_TRX_UNDO && trx_sys_need_rollback()) {
    /* Rollback all recovered transactions that are
    not in committed nor in XA PREPARE state. */
    srv_threads.m_trx_recovery_rollback = os_thread_create(
        trx_recovery_rollback_thread_key, 0, trx_recovery_rollback_thread);

    srv_threads.m_trx_recovery_rollback.start();
    /* Wait till shared MDL is taken by background thread for all tables,
    for which rollback is to be performed. */
    os_event_wait(recovery_lock_taken);
  }
```

`storage` / `innobase` / `trx` / `trx0roll.cc` L784-L857 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0roll.cc#L784-L857))

```cpp
// trx0roll.cc L784-L857
void trx_recovery_rollback(THD *thd) {
  std::vector<MDL_ticket *> shared_mdl_list;
  ut_ad(!srv_read_only_mode);

  // Take MDL locks
  /* During this stage the server is not open for external connections, and
   * there will not be any concurrent threads requesting MDL, hence we don't
   * have risk of hitting a deadlock.
   * TODO: We can improvize code by following some order while taking MDL locks.
   */
  for (const auto &element : to_rollback_trx_tables) {
    trx_id_t trx_id = element.first;
    table_id_t table_id = element.second;

    /* Passing false as we only intend to validate if the transaction is already
     * committed/rolled back during other stages of recovery. */
    auto trx = trx_rw_is_active(trx_id, false);

    /* Ignore transactions that has already finished. */
    if (trx == nullptr) {
      /* Currently these recovered transactions are not expected to finish
       * earlier. Assert in Debug mode. */
      ut_ad(false);
      continue;
    }
    auto table = dd_table_open_on_id(table_id, nullptr, nullptr, false, true);
    if (table == nullptr) {
      continue;
    }
    std::string table_name;
    std::string schema_name;
    table->get_table_name(schema_name, table_name);
    MDL_ticket *mdl_ticket;
    if (dd_mdl_acquire(thd, &mdl_ticket, schema_name.data(),
                       table_name.data())) {
      ut_error;
    }
    shared_mdl_list.push_back(mdl_ticket);
    lock_table_ix_resurrect(table, trx);
    ib::info(ER_IB_RESURRECT_ACQUIRE_TABLE_LOCK, ulong(table->id),
             table->name.m_name);
    dd_table_close(table, nullptr, nullptr, false);
  }

  /* Let the startup thread proceed now */
  os_event_set(recovery_lock_taken);

  while (DBUG_EVALUATE_IF("pause_rollback_on_recovery", true, false)) {
    if (srv_shutdown_state.load() >= SRV_SHUTDOWN_RECOVERY_ROLLBACK) {
      break;
    }
    std::this_thread::sleep_for(std::chrono::milliseconds(1));
  }

  trx_rollback_or_clean_recovered(true);

  // Release MDL locks
  for (auto mdl_ticket : shared_mdl_list) {
    dd_release_mdl(mdl_ticket);
  }
}

/** Rollback or clean up any incomplete transactions which were
encountered in crash recovery.  If the transaction already was
committed, then we clean up a possible insert undo log. If the
transaction was not yet committed, then we roll it back.
Note: this is done in a background thread. */
void trx_recovery_rollback_thread() {
  THD *thd = create_internal_thd();

  trx_recovery_rollback(thd);

  destroy_internal_thd(thd);
}
```

## 동작 흐름

```text
 trx_rollback_or_clean_recovered(all)  (L712)
 L734   trx_sys_mutex_enter
 L735   for (need_one_more_scan = true; ...)
 L737     for trx in trx_sys->rw_trx_list
 L747       종료 중이고 fast shutdown 이면 그만둔다 (주석 L740-L746)
 L765       trx_rollback_or_clean_resurrected(trx, all) 가 true 면
              mutex 를 다시 잡고 처음부터 (L766-L768)

 trx_rollback_or_clean_resurrected(trx, all)  (L647)
 L674   is_recovered 가 아니면 false          (복구로 되살린 트랜잭션이 아니다)
 L680   COMMITTED_IN_MEMORY                   trx_cleanup_at_db_startup, 해제
 L689   ACTIVE
 L690     all 이거나 ddl_operation 이면        trx_rollback_active (undo 를 거꾸로 적용)
          아니면 false                        첫 호출에서 일반 트랜잭션은 남긴다
 L698   PREPARED                              false, 건드리지 않는다
```

```text
 되살린 트랜잭션 상태별로 누가 정리하는가

 COMMITTED_IN_MEMORY  -> 첫 호출 (all=false) 에서 정리
 ACTIVE, DDL          -> 첫 호출에서 롤백 (srv_dict_recover_on_restart, srv0start.cc L2119)
 PREPARED, internal   -> [11] commit_by_xid 또는 rollback_by_xid
 PREPARED, XA         -> XA RECOVER 에 남아 사용자를 기다린다
 ACTIVE, other        -> 두 번째 호출 (all=true) 에서 롤백, 백그라운드 스레드
```

```text
 두 번 불리는 시간축 (S = 기동 스레드, B = DD 부트스트랩 스레드, R = trx_recovery_rollback 스레드)

 S  srv_start: trx_sys_init_at_db_start (L1930)
 S  dd::init (mysqld.cc L8536) -> run_bootstrap_thread 로 B 를 만들고 join (bootstrap.cc L441, L452)
 B  restart_dictionary -> DDSE_dict_recover (bootstrapper.cc L943, 정의 L84)
 B    ddse->dict_recover(...) (bootstrapper.cc L91) = innobase_dict_recover
        (등록: ha_innodb.cc L5429 innobase_hton->dict_recover = innobase_dict_recover)
 B    -> srv_dict_recover_on_restart (ha_innodb.cc L4103)
 B    L2112 trx_resurrect_locks(false)
 B    L2119 [12] all=false: DDL 트랜잭션 롤백
 B    L2155 trx_resurrect_locks(true): 나머지 잠금 되살리기
 S  tc_log->open -> [11] Binlog_recovery::recover
 S  ha_post_recover -> innobase_post_recover -> srv_start_threads_after_ddl_recovery
 S    L2264 R 스레드 생성
 S    L2270 recovery_lock_taken 대기
 R  trx_recovery_rollback (trx0roll.cc L784): 테이블마다 MDL, IX 잠금 (L822)
 R  L829 recovery_lock_taken set
 S  기동 계속, 연결 수락
 R  L838 [12] all=true: ACTIVE 를 하나씩 롤백
```

## 결과가 쓰이는 곳

```text
 롤백된 트랜잭션
      --> 변경이 undo 로 되돌아가고 잠금이 풀린다
      --> 그 사이 사용자 트랜잭션은 되살린 잠금 때문에 기다릴 수 있다
 정리된 COMMITTED 트랜잭션
      --> 남았을 수 있는 insert undo 를 치운다 (L708-L711 함수 주석)
 trx_sys->rw_trx_list 에 남은 PREPARED
      --> 외부 XA 트랜잭션. 남은 채로 서버를 끄면 종료가 멈출 수 있다고 주석이 적는다 (L726-L729)
```

## 다루지 않는 것

`trx_rollback_active` 가 롤백 그래프(`roll_node_t`, `que_run_threads`)로 undo 레코드를 거꾸로 적용하는 과정, `trx_resurrect_locks` 가 undo 에서 테이블 잠금을 되살리는 방식, `trx_sys_init_at_db_start` 가 undo 세그먼트를 훑어 트랜잭션을 만드는 과정([undo 테이블스페이스와 롤백 세그먼트](../../structure/undo-segments/README.md)), 종료 단계 `SRV_SHUTDOWN_RECOVERY_ROLLBACK` 과의 상호작용은 이 함수의 곁가지라 요약만 했다.
