# lock_wait_suspend_thread

상위: [레코드 잠금과 교착](../README.md)

**사용자 스레드가 실제로 잠드는 곳이다.** `lock_sys->waiting_threads` 배열에서 빈 슬롯 하나를 잡고, 그 슬롯의 `os_event` 를 기다린다. 이 함수에서 볼 것은 두 가지다. 슬롯을 잡기 직전에 "그새 이미 풀렸나"를 다시 확인해 헛된 잠을 피하는 것, 그리고 깨어난 뒤 `trx->error_state` 를 보고 **누가 왜 깨웠는지**(부여, 교착 희생, 타임아웃) 구분하는 것이다. 깨우는 쪽은 언제나 다른 스레드다([09], [11]).

## 위치

`storage` / `innobase` / `lock` / `lock0wait.cc` L206-L353 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0wait.cc#L206-L353))

## 실제 코드

`row_search_mvcc` 가 `DB_LOCK_WAIT` 를 받으면 페이지 래치를 놓고([01] 의 L5927) 이 오류 처리 함수로 들어온다. 잠금 대기는 여기서 처리된다.

`storage` / `innobase` / `row` / `row0mysql.cc` L706-L729 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0mysql.cc#L706-L729))

```cpp
// row0mysql.cc L706-L729
    case DB_LOCK_WAIT:

      trx_kill_blocking(trx);
      DEBUG_SYNC_C("before_lock_wait_suspend");

      lock_wait_suspend_thread(thr);

      if (trx->error_state != DB_SUCCESS) {
        que_thr_stop_for_mysql(thr);

        goto handle_new_error;
      }

      *new_err = err;

      return (true);

    case DB_DEADLOCK:
    case DB_LOCK_TABLE_FULL:
      /* Roll back the whole transaction; this resolution was added
      to version 3.23.43 */

      trx_rollback_to_savepoint(trx, nullptr);
      break;
```

`storage` / `innobase` / `lock` / `lock0wait.cc` L206-L353 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0wait.cc#L206-L353))

```cpp
// lock0wait.cc L206-L353
void lock_wait_suspend_thread(que_thr_t *thr) {
  srv_slot_t *slot;
  trx_t *trx;

  trx = thr_get_trx(thr);

  // ... (L212-L214 생략: DEBUG_SYNC)

  /* InnoDB system transactions (such as the purge, and
  incomplete transactions that are being rolled back after crash
  recovery) will use the global value of
  innodb_lock_wait_timeout, because trx->mysql_thd == NULL. */
  const auto lock_wait_timeout = trx_lock_wait_timeout_get(trx);

  lock_wait_mutex_enter();

  trx_mutex_enter(trx);

  trx->error_state = DB_SUCCESS;

  if (thr->state == QUE_THR_RUNNING) {
    ut_ad(thr->is_active);

    /* The lock has already been released or this transaction
    was chosen as a deadlock victim: no need to suspend */

    if (trx->lock.was_chosen_as_deadlock_victim) {
      trx->error_state = DB_DEADLOCK;
      trx->lock.was_chosen_as_deadlock_victim = false;

      ut_d(trx->lock.in_rollback = true);
    }

    lock_wait_mutex_exit();
    trx_mutex_exit(trx);
    return;
  }

  ut_ad(!thr->is_active);

  slot = lock_wait_table_reserve_slot(thr, lock_wait_timeout);

  lock_wait_mutex_exit();

  /* We hold trx->mutex here, which is required to call
  lock_set_lock_and_trx_wait. This means that the value in
  trx->lock.wait_lock_type which we are about to read comes from the latest
  call to lock_set_lock_and_trx_wait before we obtained the trx->mutex, which is
  precisely what we want for our stats */
  auto lock_type = trx->lock.wait_lock_type;
  trx_mutex_exit(trx);

  // ... (L260-L277 생략: 사전 래치(dict_operation_lock)를 쥐고 있었으면 잠들기 전에 놓는다)

  /* Suspend this thread and wait for the event. */

  auto was_declared_inside_innodb = trx->declared_to_be_inside_innodb;

  if (was_declared_inside_innodb) {
    /* We must declare this OS thread to exit InnoDB, since a
    possible other thread holding a lock which this thread waits
    for must be allowed to enter, sooner or later */

    srv_conc_force_exit_innodb(trx);
  }

  ut_a(lock_type == LOCK_REC || lock_type == LOCK_TABLE);
  thd_wait_begin(trx->mysql_thd, lock_type == LOCK_REC ? THD_WAIT_ROW_LOCK
                                                       : THD_WAIT_TABLE_LOCK);

  DEBUG_SYNC_C("lock_wait_will_wait");

  os_event_wait(slot->event);

  DEBUG_SYNC_C("lock_wait_has_finished_waiting");

  thd_wait_end(trx->mysql_thd);

  /* After resuming, reacquire the data dictionary latch if
  necessary. */

  if (was_declared_inside_innodb) {
    /* Return back inside InnoDB */

    srv_conc_force_enter_innodb(trx);
  }

  if (had_dict_lock == RW_S_LATCH) {
    row_mysql_freeze_data_dictionary(trx, UT_LOCATION_HERE);
  } else if (had_dict_lock == RW_X_LATCH) {
    rw_lock_x_lock(dict_operation_lock, UT_LOCATION_HERE);
  }

  /* Release the slot for others to use */
  const auto start_time = slot->suspend_time;
  lock_wait_table_release_slot(slot);

  // ... (L322-L338 생략: 대기 시간 통계)

  /* The transaction is chosen as deadlock victim during sleep. */
  if (trx->error_state == DB_DEADLOCK) {
    ut_d(trx->lock.in_rollback = true);
    return;
  }

  if (trx->error_state == DB_LOCK_WAIT_TIMEOUT) {
    MONITOR_INC(MONITOR_TIMEOUT);
  }

  if (trx_is_interrupted(trx)) {
    trx->error_state = DB_INTERRUPTED;
  }
}
```

슬롯을 잡는 함수다. 슬롯을 잡은 직후 검사 스레드를 깨운다. 이 시점에야 이 트랜잭션의 wait-for 간선이 검사 스레드에 보이기 때문이다.

`storage` / `innobase` / `lock` / `lock0wait.cc` L138-L191 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0wait.cc#L138-L191))

```cpp
// lock0wait.cc L138-L191
static srv_slot_t *lock_wait_table_reserve_slot(
    que_thr_t *thr, /*!< in: query thread associated
                    with the user OS thread */
    std::chrono::steady_clock::duration
        wait_timeout) /*!< in: lock wait timeout value */
{
  srv_slot_t *slot;

  ut_ad(lock_wait_mutex_own());
  ut_ad(trx_mutex_own(thr_get_trx(thr)));

  slot = lock_sys->waiting_threads;

  for (uint32_t i = srv_max_n_threads; i--; ++slot) {
    if (!slot->in_use) {
      slot->reservation_no = lock_wait_table_reservations++;
      slot->in_use = true;
      slot->thr = thr;
      slot->thr->slot = slot;

      if (slot->event == nullptr) {
        slot->event = os_event_create();
        ut_a(slot->event);
      }

      os_event_reset(slot->event);
      slot->suspended = true;
      slot->suspend_time = std::chrono::steady_clock::now();
      slot->wait_timeout = wait_timeout;
      if (thr->lock_state == QUE_THR_LOCK_ROW) {
        srv_stats.n_lock_wait_count.inc();
        srv_stats.n_lock_wait_current_count.inc();
      }

      if (slot == lock_sys->last_slot) {
        ++lock_sys->last_slot;
      }

      ut_ad(lock_sys->last_slot <=
            lock_sys->waiting_threads + srv_max_n_threads);

      /* We call lock_wait_request_check_for_cycles() because the
      node representing the `thr` only now becomes visible to the thread which
      analyzes contents of lock_sys->waiting_threads. The edge itself was
      created by lock_create_wait_for_edge() during RecLock::add_to_waitq() or
      lock_table(), but at that moment the source of the edge was not yet in the
      lock_sys->waiting_threads, so the node and the outgoing edge were not yet
      visible.
      I hope this explains why we do waste time on calling
      lock_wait_request_check_for_cycles() from lock_create_wait_for_edge().*/
      lock_wait_request_check_for_cycles();
      return (slot);
    }
  }
```

## 동작 흐름

```text
 row_mysql_handle_errors (row0mysql.cc)
 L706   case DB_LOCK_WAIT
 L708     trx_kill_blocking(trx)          high priority 트랜잭션이면 막는 쪽을 죽인다
 L711     lock_wait_suspend_thread(thr)

 lock_wait_suspend_thread (lock0wait.cc)
 L220   lock_wait_timeout = trx_lock_wait_timeout_get(trx)   innodb_lock_wait_timeout
 L222   lock_wait_mutex_enter          슬롯 배열 보호
 L224   trx_mutex_enter
 L228   thr->state == QUE_THR_RUNNING 이면 잠들지 않는다
          [07] 과 이 줄 사이에 다른 스레드가 이미 부여하거나 희생자로 골랐다
 L234     희생자였으면 error_state = DB_DEADLOCK
 L243     return
 L248   lock_wait_table_reserve_slot
          L151  빈 슬롯을 찾는다
          L153  reservation_no = 전역 카운터++   (교착 검사의 ABA 판정에 쓴다)
          L163  os_event_reset(slot->event)
          L165  suspend_time = 지금, wait_timeout 기록
          L188  lock_wait_request_check_for_cycles -> [09] 를 깨운다
 L250   lock_wait_mutex_exit, L258 trx_mutex_exit
 L288   srv_conc_force_exit_innodb     innodb_thread_concurrency 자리를 내놓는다
 L292   thd_wait_begin(THD_WAIT_ROW_LOCK)
 L297   os_event_wait(slot->event)     <-- 여기서 잠든다
 ------------------------------------------------------------------
        다른 스레드가 os_event_set(slot->event) 를 부른다
          [11] lock_grant                부여
          [09] lock_wait_try_cancel      타임아웃
          [10] lock_wait_rollback_deadlock_victim  교착 희생자
 ------------------------------------------------------------------
 L301   thd_wait_end
 L309   srv_conc_force_enter_innodb
 L320   lock_wait_table_release_slot
 L341   error_state == DB_DEADLOCK         -> 그대로 돌아간다
 L346   error_state == DB_LOCK_WAIT_TIMEOUT -> 모니터 카운터
 L350   KILL 등으로 중단되었으면 DB_INTERRUPTED

 다시 row_mysql_handle_errors
 L713   error_state != DB_SUCCESS 면 L716 goto handle_new_error 로 그 오류를 처리
          DB_DEADLOCK           L728  트랜잭션 전체 롤백
          DB_LOCK_WAIT_TIMEOUT  L673  innodb_rollback_on_timeout 이면 전체 롤백, 아니면 문장만
 L721   아니면 true -> row_search_mvcc 가 커서를 복원해 같은 레코드부터 다시 찾는다
```

깨우는 길이 셋이어도 한 번 잠든 스레드는 정확히 한 번만 깨어난다. 깨우는 함수가 하나뿐이고, 깨우기 전에 반드시 `wait_lock` 을 `nullptr` 로 바꾸기 때문이다(주석 L361-L380).

```text
 깨우는 세 길이 모두 같은 문을 지난다 (lock0wait.cc)

 [11] lock_grant                          lock0lock.cc L1953  --+
 [09] lock_wait_try_cancel        L497 -> lock0lock.cc L5755  --+
 [10] lock_wait_rollback_deadlock_victim  L701 -> L5755       --+
                                                                v
      lock_reset_wait_and_release_thread_if_suspended           L420
        L442  blocking_trx = nullptr        간선을 지운다
        L452  que_thr_end_lock_wait         질의 스레드를 RUNNING 으로
        L457  lock_reset_lock_and_trx_wait  wait_lock = nullptr, LOCK_WAIT 비트 끔
        L460  lock_wait_release_thread_if_suspended
                L408  슬롯에 들어가 있으면
                L409    희생자 표시가 있으면 error_state = DB_DEADLOCK
                L416    os_event_set(slot->event)
                슬롯에 아직 없으면 아무것도 하지 않는다
                  -> 그 스레드는 L228 에서 RUNNING 을 보고 잠들지 않는다
```

```text
 잠드는 쪽과 깨우는 쪽의 경주 (trx->mutex 가 심판)

 잠드는 스레드 A                        깨우는 스레드 B
 [07] DB_LOCK_WAIT, trx_mutex_exit
 ... 래치를 놓고 오류 처리로 올라온다     lock_grant -> trx_mutex_enter(A)
                                         thr 를 RUNNING 으로, wait_lock = nullptr
                                         thr->slot 이 없다 -> set 하지 않는다
                                         trx_mutex_exit(A)
 L224 trx_mutex_enter(A)
 L228 RUNNING 이다 -> 잠들지 않고 돌아간다

 B 가 한 발 늦으면
 L248 슬롯을 잡고 L297 에서 잠든다
                                         lock_grant -> thr->slot 이 있다 -> os_event_set
 L297 깨어난다
```

## 결과가 쓰이는 곳

```text
 true (기다림이 끝나고 부여됨)
      --> row_search_mvcc 가 lock_state 를 NOLOCK 으로 돌리고 mtr 를 다시 시작해
          저장한 커서 위치로 복원한 뒤 같은 레코드에서 다시 잠근다 (row0sel.cc L5940-L5944)
 DB_DEADLOCK / DB_LOCK_WAIT_TIMEOUT / DB_INTERRUPTED
      --> row_mysql_handle_errors 가 롤백 범위를 정하고 SQL 오류로 바뀐다
          ER_LOCK_DEADLOCK, ER_LOCK_WAIT_TIMEOUT
 대기 시간
      --> srv_stats.n_lock_wait_time 이 Innodb_row_lock_time 이 된다 (srv0srv.cc L1665)
      --> thd_set_lock_wait_time 으로 THD 에도 넘긴다 (L334)
```

## 다루지 않는 것

`innodb_thread_concurrency` 의 입장 제어(`srv_conc_force_exit_innodb`), 슬롯 배열이 가득 찼을 때의 비상 종료(L193-L201), `trx_kill_blocking` 과 high priority 트랜잭션, 테이블 잠금 대기(`QUE_THR_LOCK_TABLE`)는 이 흐름의 곁가지라 요약만 했다.
