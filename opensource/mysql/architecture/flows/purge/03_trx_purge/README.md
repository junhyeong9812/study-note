# trx_purge

상위: [purge](../README.md)

**purge 배치 하나를 처음부터 끝까지 지휘하는 함수다.** 순서는 다섯 걸음이다. DML 을 얼마나 늦출지 계산하고, [04] 로 "어디까지 치워도 되는가"를 새로 정하고, [05] 로 history 에서 undo 레코드를 모아 스레드 수만큼의 그룹으로 나누고, n-1 개 그룹은 워커 큐에 넣고 마지막 하나는 **코디네이터가 직접** 실행한 뒤, 워커가 다 끝나기를 기다린다. 요청이 있으면 마지막에 [10] 으로 history 를 잘라낸다. 반환값은 이번 배치가 다룬 undo 페이지 수이고, [02] 와 [01] 은 이 값이 0 인지로 쉴지 말지를 정한다.

## 위치

`storage` / `innobase` / `trx` / `trx0purge.cc` L2396-L2479 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0purge.cc#L2396-L2479))

## 실제 코드

함수 전체다. 워커에 넘긴 개수(`n_submitted`)와 워커가 끝낸 개수(`n_completed`)가 같아질 때까지 기다리는 것이 배치의 끝이다.

`storage` / `innobase` / `trx` / `trx0purge.cc` L2394-L2479 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0purge.cc#L2394-L2479))

```cpp
// trx0purge.cc L2394-L2479
/** This function runs a purge batch.
 @return number of undo log pages handled in the batch */
ulint trx_purge(ulint n_purge_threads, /*!< in: number of purge tasks
                                       to submit to the work queue */
                ulint batch_size,      /*!< in: the maximum number of records
                                       to purge in one batch */
                bool truncate)         /*!< in: truncate history if true */
{
  que_thr_t *thr = nullptr;
  ulint n_pages_handled;

  ut_a(n_purge_threads > 0);

  srv_dml_needed_delay = trx_purge_dml_delay();

  /* The number of tasks submitted should be completed. */
  ut_a(purge_sys->n_submitted == purge_sys->n_completed);

  trx_purge_update_oldest_needed();
  CONDITIONAL_SYNC_POINT("after_clone_oldest_view");
#ifdef UNIV_DEBUG
  if (srv_purge_view_update_only_debug) {
    return (0);
  }
#endif /* UNIV_DEBUG */

  /* Fetch the UNDO recs that need to be purged. */
  n_pages_handled = trx_purge_attach_undo_recs(n_purge_threads, batch_size);

  /* Submit the tasks to the work queue. */
  for (ulint i = 0; i < n_purge_threads - 1; ++i) {
    thr = que_fork_scheduler_round_robin(purge_sys->query, thr);

    ut_a(thr != nullptr);

    srv_que_task_enqueue_low(thr);
  }

  thr = que_fork_scheduler_round_robin(purge_sys->query, thr);
  ut_a(thr != nullptr);

  purge_sys->n_submitted += n_purge_threads - 1;

  que_run_threads(thr);

  trx_purge_wait_for_workers_to_complete();

  ut_a(purge_sys->n_submitted == purge_sys->n_completed);

// ... (L2443-L2451 생략: 디버그 빌드의 purge_sys->done 기록)

  /* The first page of LOBs are freed at the end of a purge batch because
  multiple purge threads will access the same LOB as part of the purge
  process.  Some purge threads will free only portion of the LOB related to
  the partial update of the LOB.  But 1 of the purge thread will free the LOB
  completely if it is not needed anymore (either because of full update or
  because of deletion).  If the LOB is freed, and a purge thread attempts to
  access the LOB, then it is a bug.  To avoid this, we delay the freeing of
  the first page of LOB till the end of a purge batch.  */
  for (thr = UT_LIST_GET_FIRST(purge_sys->query->thrs); thr != nullptr;
       thr = UT_LIST_GET_NEXT(thrs, thr)) {
    purge_node_t *node = static_cast<purge_node_t *>(thr->child);
    node->free_lob_pages();
  }

  /* During upgrade, to know whether purge is empty,
  we rely on purge history length. So truncate the
  undo logs during upgrade to update purge history
  length. */
  if (truncate) {
    trx_purge_truncate();
  }

  MONITOR_INC_VALUE(MONITOR_PURGE_INVOKED, 1);
  MONITOR_INC_VALUE(MONITOR_PURGE_N_PAGE_HANDLED, n_pages_handled);

  return (n_pages_handled);
}
```

purge 가 밀릴 때 DML 을 늦추는 계산이다. `innodb_max_purge_lag` 가 0 이면(기본 동작) 아무것도 늦추지 않는다.

`storage` / `innobase` / `trx` / `trx0purge.cc` L2319-L2351 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0purge.cc#L2319-L2351))

```cpp
// trx0purge.cc L2319-L2351
/** Calculate the DML delay required.
 @return delay in microseconds or ULINT_MAX */
static ulint trx_purge_dml_delay(void) {
  /* Determine how much data manipulation language (DML) statements
  need to be delayed in order to reduce the lagging of the purge
  thread. */
  ulint delay = 0; /* in microseconds; default: no delay */

  /* If purge lag is set (ie. > 0) then calculate the new DML delay.
  Note: we do a dirty read of the trx_sys_t data structure here,
  without holding trx_sys->mutex. */

  if (srv_max_purge_lag > 0 && trx_sys->rseg_history_len.load() >
                                   srv_n_purge_threads * srv_purge_batch_size) {
    float ratio;

    ratio = float(trx_sys->rseg_history_len.load()) / srv_max_purge_lag;

    if (ratio > 1.0) {
      /* If the history list length exceeds the srv_max_purge_lag, the data
      manipulation statements are delayed by at least 5 microseconds. */
      delay = (ulint)((ratio - 0.9995) * 10000);
    }

    if (delay > srv_max_purge_lag_delay) {
      delay = srv_max_purge_lag_delay;
    }

    MONITOR_SET(MONITOR_DML_PURGE_DELAY, delay);
  }

  return (delay);
}
```

그 지연을 실제로 쓰는 쪽이다. INSERT, UPDATE, DELETE 가 행 하나를 바꾸기 전에 잔다.

`storage` / `innobase` / `row` / `row0mysql.cc` L139-L145 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0mysql.cc#L139-L145))

```cpp
// row0mysql.cc L139-L145
/** Delays an INSERT, DELETE or UPDATE operation if the purge is lagging. */
static void row_mysql_delay_if_needed(void) {
  if (srv_dml_needed_delay) {
    std::this_thread::sleep_for(
        std::chrono::microseconds(srv_dml_needed_delay));
  }
}
```

워커를 기다리는 쪽이다. 열 번은 양보만 하고, 그래도 안 끝났으면 큐에 남은 작업이 있는지 보고 워커를 하나 더 깨운 뒤 20 마이크로초 잔다.

`storage` / `innobase` / `trx` / `trx0purge.cc` L2353-L2378 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0purge.cc#L2353-L2378))

```cpp
// trx0purge.cc L2353-L2378
/** Wait for pending purge jobs to complete. */
static void trx_purge_wait_for_workers_to_complete() {
  ulint i = 0;
  ulint n_submitted = purge_sys->n_submitted;

  /* Ensure that the work queue empties out. */
  while (purge_sys->n_completed.load() != n_submitted) {
    if (++i < 10) {
      std::this_thread::yield();
    } else {
      if (srv_get_task_queue_length() > 0) {
        srv_release_threads(SRV_WORKER, 1);
      }

      std::this_thread::sleep_for(std::chrono::microseconds(20));
      i = 0;
    }
  }

  /* None of the worker threads should be doing any work. */
  ut_a(purge_sys->n_submitted == purge_sys->n_completed);

  /* There should be no outstanding tasks as long
  as the worker threads are active. */
  ut_a(srv_get_task_queue_length() == 0);
}
```

이 배치가 먹는 재료가 history list 에 들어오는 자리다. 커밋하는 스레드가 update undo 로그 헤더를 롤백 세그먼트의 history 맨 앞에 붙이고, 그 로그에 커밋 번호(`trx->no`)를 적는다. 이 함수를 부르는 쪽은 [커밋과 binlog 2PC](../../commit-2pc/10_trx_commit_low/README.md)에 있다.

`storage` / `innobase` / `trx` / `trx0purge.cc` L401-L418 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0purge.cc#L401-L418))

```cpp
// trx0purge.cc L401-L418
  /* Add the log as the first in the history list */
  flst_add_first(rseg_header + TRX_RSEG_HISTORY,
                 undo_header + TRX_UNDO_HISTORY_NODE, mtr);

  if (update_rseg_history_len) {
    trx_sys->rseg_history_len.fetch_add(n_added_logs);
    if (trx_sys->rseg_history_len.load() >
        srv_n_purge_threads * srv_purge_batch_size) {
      srv_wake_purge_thread_if_not_active();
    }
  }

  /* Update maximum transaction number for this rollback segment. */
  mlog_write_ull(rseg_header + TRX_RSEG_MAX_TRX_NO, trx->no, mtr);

  /* Write the trx number to the undo log header */
  mlog_write_ull(undo_header + TRX_UNDO_TRX_NO, trx->no, mtr);

```

## 동작 흐름

```text
 trx_purge(n_purge_threads, batch_size, truncate)

 L2407  srv_dml_needed_delay = trx_purge_dml_delay()
 L2410  ut_a(n_submitted == n_completed)                 직전 배치가 완전히 끝났다
 L2412  [04] trx_purge_update_oldest_needed              purge_sys->view, m_lowest_needed_trx_no
 L2421  n_pages_handled = [05] trx_purge_attach_undo_recs(n, batch_size)
          스레드마다 purge_node_t->recs 에 undo 레코드 목록이 붙는다
 L2424  i = 0 .. n-2
          que_fork_scheduler_round_robin 으로 다음 query thread
 L2429    srv_que_task_enqueue_low(thr)                    srv_sys->tasks 에 넣고 워커 하나를 깨운다
 L2435  n_submitted += n - 1
 L2437  que_run_threads(thr)                              마지막 하나는 코디네이터가 직접  --> [07]
 L2439  trx_purge_wait_for_workers_to_complete           n_completed 가 따라올 때까지
 L2461  모든 node 의 free_lob_pages                       LOB 첫 페이지는 배치 끝에 한꺼번에 해제
 L2471  truncate 면 [10] trx_purge_truncate
 L2478  return n_pages_handled
```

배치 하나를 시간축에 놓으면 코디네이터와 워커가 같은 구간에 일한다. 그룹은 테이블 단위로 나뉜다. 다만 history 가 `innodb_max_purge_lag` 를 넘으면 그룹 크기를 고르게 맞추느라 한 테이블의 레코드가 여러 그룹으로 갈 수 있다([05]). LOB 첫 페이지 해제를 배치 끝으로 미루는 것도 여러 스레드가 같은 LOB 에 닿을 수 있기 때문이라고 주석(L2453-L2460)이 적었다.

```text
 n_use_threads = 3 인 배치 하나

 시간 ->
 코디네이터  [04][05 모으고 나누기][enqueue x2][ 그룹 C 실행 (row_purge_step) ][기다림][10?]
 워커 1                                   |[ 그룹 A 실행 ]-- n_completed++
 워커 2                                   |[ 그룹 B 실행 ...... ]-- n_completed++
                                          ^ srv_que_task_enqueue_low 가 깨운다

 n_submitted = 2, 끝날 때 n_completed = 2
 코디네이터 몫은 세지 않는다 (n_submitted 에 넣지 않았다)
```

```text
 DML 지연 계산 (trx_purge_dml_delay, L2321)

 조건  innodb_max_purge_lag > 0
       그리고 history 길이 > innodb_purge_threads x innodb_purge_batch_size
 ratio = history 길이 / innodb_max_purge_lag
 ratio > 1 이면  delay = (ratio - 0.9995) x 10000 마이크로초      (최소 약 5 마이크로초)
 상한  innodb_max_purge_lag_delay

 예) max_purge_lag = 100000, history = 150000
     ratio = 1.5 -> delay = 5005 마이크로초 = 행 하나 바꿀 때마다 약 5ms
 이 값은 다음 배치까지 유지된다 (배치마다 다시 계산)
```

## 결과가 쓰이는 곳

```text
 반환값 n_pages_handled    --> [02] 의 n_total_purged, 0 이면 쉬는 근거
 srv_dml_needed_delay      --> row_mysql_delay_if_needed (row0mysql.cc L140) 가 DML 마다 잔다
 purge_sys->iter, limit    --> [10] 이 어디까지 잘라낼지 정한다
```

## 다루지 않는 것

query graph 와 query thread(`que_fork_scheduler_round_robin`, `que_run_threads`, `trx_purge_graph_build`)의 일반 구조, LOB 첫 페이지 해제를 배치 끝으로 미루는 이유의 세부(L2453-L2460 주석), 디버그 빌드 전용 `srv_purge_view_update_only_debug` 는 이 흐름의 곁가지라 줄만 적었다.
