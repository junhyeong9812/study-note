# 스레드 구성

상위: [MySQL 아키텍처 지도](../../README.md)

`mysqld` 프로세스 안에서 **누가 무엇을 기다리고, 누가 그것을 깨우는가**를 한 자리에 모은다. 스레드는 두 부류다. 연결 하나에 하나씩 붙는 **연결 스레드**가 SQL 을 실행하면서 InnoDB 코드도 직접 돈다. 그리고 InnoDB 가 시작할 때 만드는 **백그라운드 스레드**들이 redo 쓰기, 페이지 플러시, purge, 잠금 대기 감시를 나눠 맡는다. 둘이 만나는 방식은 대부분 같다. 연결 스레드가 일을 남기고 이벤트를 set 하고, 백그라운드 스레드는 그 이벤트(또는 타임아웃)에서 깨어나 일을 하고, 끝나면 연결 스레드가 기다리는 이벤트를 set 한다. 연결 스레드의 한 생애는 [연결과 스레드](../../flows/connection-thread/README.md) 흐름이 따라가고, 이 편은 스레드들의 **자리와 서로의 신호선**만 본다.

기준 태그: mysql-9.7.2 [`008e09c283`](https://github.com/mysql/mysql-server/tree/008e09c2834b98143a8c067d4d225c90953050cf). 모든 줄 번호는 이 태그 기준이다.

## 전체 그림

```text
 누가 누구를 깨우는가 (화살표 = os_event_set / cond_signal, 괄호 = 기다리는 이벤트)

 리스너 스레드
    | COND_thread_cache signal (per_thread.cc L396)
    v
 연결 스레드 (연결마다 하나, THD 하나)
    |  커밋: log_write_up_to
    |    +-- writer_event set (log0write.cc L849) ----------------> log_writer
    |    +-- flush_events[slot] 에서 잔다 (L934)  <---------------- log_flusher / log_flush_notifier
    |  잠금 충돌: lock_wait_suspend_thread
    |    +-- slot->event 에서 잔다 (lock0wait.cc L297) <----------- 잠금을 푼 연결 스레드
    |                                                               또는 lock_wait_timeout
    |  free 블록이 없다: buf_LRU_get_free_block
    |    +-- buf_flush_event set (buf0lru.cc L1405) --------------> page cleaner 코디네이터
    |  커밋으로 history 가 길어진다
    |    +-- srv_wake_purge_thread_if_not_active (trx0purge.cc L409) -> purge 코디네이터
    v
 InnoDB 백그라운드

 redo      log_writer --flusher_event--> log_flusher --flush_notifier_event--> log_flush_notifier
              |                             |                                    |
              +--write_notifier_event--> log_write_notifier                     +--> flush_events[*]
              |                             +--> write_events[*]
              +--checkpointer_event (공간 부족, L1925)--> log_checkpointer
                                             log_checkpointer --buf_flush_event (sync flush, log0chkp.cc L670)
                                                                       |
 플러시    page cleaner 코디네이터 (buf_flush_event 또는 1초)  <---------+
              +-- is_requested set (buf0flu.cc L2619) --> page cleaner 워커들
              <-- is_finished set (L2708) ------------- 마지막 슬롯을 끝낸 스레드

 purge     purge 코디네이터 (slot->event 또는 10ms)
              +-- srv_que_task_enqueue_low -> SRV_WORKER slot->event (srv0srv.cc L3159) --> purge 워커들

 master    1초마다 깬다 (sleep_for, srv0srv.cc L2599)
              +-- history 가 있으면 purge 코디네이터를 깨운다 (L2301-L2303)

 잠금 감시 lock_wait_timeout (timeout_event 또는 1초)
              +-- 대기가 너무 길거나 교착 희생자면 lock_cancel_waiting_and_release 로
                  그 연결 스레드의 slot->event set (set 자체는 lock0wait.cc L416 한 곳)
```

## 스레드 목록 - Srv_threads

InnoDB 백그라운드 스레드는 전부 전역 `srv_threads` 한 곳에 핸들(`IB_thread`)로 모인다. 종료할 때 이 핸들로 "다 끝났는가"를 확인한다(주석 L163-L164).

`storage` / `innobase` / `include` / `srv0srv.h` L163-L247 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/srv0srv.h#L163-L247))

```cpp
// srv0srv.h L163-L247
/** Structure which keeps shared future objects for InnoDB background
threads. One should use these objects to check if threads exited. */
struct Srv_threads {
  /** Monitor thread (prints info). */
  IB_thread m_monitor;

  /** Error monitor thread. */
  IB_thread m_error_monitor;

  /** Redo files governor thread. */
  IB_thread m_log_files_governor;

  /** Redo checkpointer thread. */
  IB_thread m_log_checkpointer;

  /** Redo writer thread. */
  IB_thread m_log_writer;

  /** Redo flusher thread. */
  IB_thread m_log_flusher;

  /** Redo write notifier thread. */
  IB_thread m_log_write_notifier;

  /** Redo flush notifier thread. */
  IB_thread m_log_flush_notifier;

  /** Redo log archiver (used by backup). */
  IB_thread m_backup_log_archiver;

  /** Buffer pool dump thread. */
  IB_thread m_buf_dump;

  /** Buffer pool resize thread. */
  IB_thread m_buf_resize;

  /** Dict stats background thread. */
  IB_thread m_dict_stats;

  /** Thread detecting lock wait timeouts. */
  IB_thread m_lock_wait_timeout;

  /** The master thread. */
  IB_thread m_master;

  /** The ts_alter_encrypt thread. */
  IB_thread m_ts_alter_encrypt;

  /** Thread doing rollbacks during recovery. */
  IB_thread m_trx_recovery_rollback;

  /** Thread writing recovered pages during recovery. */
  IB_thread m_recv_writer;

  /** Purge coordinator (also being a worker) */
  IB_thread m_purge_coordinator;

  /** Number of purge workers and size of array below. */
  size_t m_purge_workers_n;

  /** Purge workers. Note that the m_purge_workers[0] is the same shared
  state as m_purge_coordinator. */
  IB_thread *m_purge_workers;

  /** Page cleaner coordinator (also being a worker). */
  IB_thread m_page_cleaner_coordinator;

  /** Number of page cleaner workers and size of array below. */
  size_t m_page_cleaner_workers_n;

  /** Page cleaner workers. Note that m_page_cleaner_workers[0] is the
  same shared state as m_page_cleaner_coordinator. */
  IB_thread *m_page_cleaner_workers;

  /** Archiver's log archiver (used by Clone). */
  IB_thread m_log_archiver;

  /** Archiver's page archiver (used by Clone). */
  IB_thread m_page_archiver;

  /** Thread doing optimization for FTS index. */
  IB_thread m_fts_optimize;

  /** Thread for GTID persistence */
  IB_thread m_gtid_persister;
```

```text
 Srv_threads 의 칸과 만드는 곳

 무리         칸                              만드는 곳
 redo         m_log_writer, m_log_flusher      log_start_background_threads   log0log.cc L913
              m_log_write_notifier
              m_log_flush_notifier
              m_log_checkpointer
              m_log_files_governor
 플러시       m_page_cleaner_coordinator       buf_flush_page_cleaner_init    buf0flu.cc L2523
              m_page_cleaner_workers[n]        코디네이터가 시작하며 만든다     buf0flu.cc L2899
 purge        m_purge_coordinator              srv_start_purge_threads        srv0start.cc L2169
              m_purge_workers[n]
 잠금         m_lock_wait_timeout              srv_start                      srv0start.cc L1997
 감시         m_error_monitor, m_monitor       srv_start                      srv0start.cc L2003, L2010
 master       m_master                         srv_start_threads              srv0start.cc L2233
 기타         m_buf_resize, m_dict_stats       srv_start_threads              srv0start.cc L2221, L2248
              m_trx_recovery_rollback, m_buf_dump
                                               srv_start_threads_after_ddl_recovery  L2264, L2276
              m_fts_optimize, m_gtid_persister, 아카이버, m_ts_alter_encrypt, m_recv_writer

 워커 배열의 [0] 은 코디네이터 자신이다 (srv0srv.h 주석, buf0flu.cc L2545, srv0start.cc L2178)
```

```text
 시작 순서 (srv_start -> srv_start_threads -> srv_start_threads_after_ddl_recovery)

 srv_start (srv0start.cc L1330)
   L1581  page cleaner 코디네이터          redo 복구 중에도 페이지를 내려써야 한다
   L1657  redo 스레드 여섯 (새 DB 를 만들 때, create_new_db)
   L1830  redo 스레드 여섯 (기존 DB 의 복구를 마친 뒤, read-only 가 아니면)
   L1899  clone / MEB 로 복원한 DB 면 L1892 에서 멈췄다가 여기서 다시 띄운다
          read-only 모드에서는 띄우지 않는다 (log_start_background_threads 의 ut_a, log0log.cc L919)
   L1997  lock_wait_timeout, error_monitor, monitor
 srv_start_threads (L2197)
   L2221  buf_resize
   L2233  master
   L2248  dict_stats
 srv_start_threads_after_ddl_recovery (L2260)
   L2264  복구된 트랜잭션 롤백 (있을 때만)
   L2276  buf_dump
   L2302  purge 코디네이터와 워커  -- 메타데이터가 일관된 뒤에야 시작한다 (주석 L2300-L2301)
```

## redo 스레드 여섯

redo 를 파일에 쓰고(writer), fsync 하고(flusher), 기다리는 사용자에게 알리는(두 notifier) 일을 서로 다른 스레드가 한다. 쓰기와 fsync 를 떼어 놓았기 때문에 fsync 하는 동안에도 다음 쓰기가 진행된다. 실제 본체는 [mini-transaction과 redo 기록](../../flows/mtr-redo/README.md)의 [09] [10] 에 있다.

`storage` / `innobase` / `log` / `log0log.cc` L913-L951 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0log.cc#L913-L951))

```cpp
// log0log.cc L913-L951
void log_start_background_threads(log_t &log) {
  // ... (L914-L924 생략: 검증과 플래그 초기화)
  srv_threads.m_log_checkpointer =
      os_thread_create(log_checkpointer_thread_key, 0, log_checkpointer, &log);

  srv_threads.m_log_flush_notifier = os_thread_create(
      log_flush_notifier_thread_key, 0, log_flush_notifier, &log);

  srv_threads.m_log_flusher =
      os_thread_create(log_flusher_thread_key, 0, log_flusher, &log);

  srv_threads.m_log_write_notifier = os_thread_create(
      log_write_notifier_thread_key, 0, log_write_notifier, &log);

  srv_threads.m_log_writer =
      os_thread_create(log_writer_thread_key, 0, log_writer, &log);

  srv_threads.m_log_files_governor = os_thread_create(
      log_files_governor_thread_key, 0, log_files_governor, &log);

  log.m_no_more_dummy_records_requested.store(false);
  log.m_no_more_dummy_records_promised.store(false);

  srv_threads.m_log_checkpointer.start();
  srv_threads.m_log_flush_notifier.start();
  srv_threads.m_log_flusher.start();
  srv_threads.m_log_write_notifier.start();
  srv_threads.m_log_writer.start();
  srv_threads.m_log_files_governor.start();
```

writer 가 `write_lsn` 을 올리고 나서 누구를 깨우는지가 아래다. 깨울 슬롯이 하나뿐이면 notifier 를 거치지 않고 사용자 스레드를 직접 깨운다. `innodb_flush_log_at_trx_commit=1` 일 때만 flusher 를 재촉한다.

`storage` / `innobase` / `log` / `log0write.cc` L1558-L1606 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0write.cc#L1558-L1606))

```cpp
// log0write.cc L1558-L1606
static inline void notify_about_advanced_write_lsn(log_t &log,
                                                   lsn_t old_write_lsn,
                                                   lsn_t new_write_lsn) {
  if (!log.writer_threads_paused.load(std::memory_order_acquire)) {
    if (srv_flush_log_at_trx_commit == 1) {
      os_event_set(log.flusher_event);
    }
    /* For performance reasons, we rely on the help from notifier thread only if
    there is more than one event to set, and set it ourselves otherwise. The
    // ... (L1567-L1587 생략: 한 홉을 줄이는 근거 주석)
    const auto first_slot =
        log_compute_write_event_slot(log, old_write_lsn + 1);

    const auto last_slot = log_compute_write_event_slot(log, new_write_lsn);

    if (first_slot == last_slot &&
        (new_write_lsn - old_write_lsn) <= OS_FILE_LOG_BLOCK_SIZE) {
      log_sync_point("log_write_before_users_notify");
      os_event_set(log.write_events[first_slot]);
    } else {
      log_sync_point("log_write_before_notifier_notify");
      os_event_set(log.write_notifier_event);
    }
  }

  if (arch_log_sys && arch_log_sys->is_active()) {
    os_event_set(log_archiver_thread_event);
  }
}
```

flusher 쪽도 같은 모양이다. fsync 가 끝나면 `flushed_to_disk_lsn` 을 올리고 `flush_events` 의 슬롯 또는 flush_notifier 를 깨운다.

`storage` / `innobase` / `log` / `log0write.cc` L2465-L2487 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0write.cc#L2465-L2487))

```cpp
// log0write.cc L2465-L2487
  log.flushed_to_disk_lsn.store(flush_up_to_lsn);

  /* Notify other thread(s). */

  DBUG_PRINT("ib_log", ("Flushed to disk up to " LSN_PF, flush_up_to_lsn));

  if (!log.writer_threads_paused.load(std::memory_order_acquire)) {
    const auto first_slot =
        log_compute_flush_event_slot(log, last_flush_lsn + 1);

    const auto last_slot = log_compute_flush_event_slot(log, flush_up_to_lsn);

    if (first_slot == last_slot) {
      log_sync_point("log_flush_before_users_notify");
      os_event_set(log.flush_events[first_slot]);
    } else {
      log_sync_point("log_flush_before_notifier_notify");
      os_event_set(log.flush_notifier_event);
    }
  } else {
    log_sync_point("log_flush_before_users_notify");
    log_sync_point("log_flush_before_notifier_notify");
    os_event_set(log.old_flush_event);
```

```text
 redo 스레드가 기다리는 것과 깨우는 것

 스레드               기다리는 것                              깨우는 것
 log_writer           writer_event (L2240)                     flusher_event, write_notifier_event,
                      사용자의 log_wait_for_write 가 set (L849)  또는 write_events[slot] 직접
                                                               checkpointer_event (공간 부족, L1925)
 log_flusher          flusher_event                            flush_notifier_event
                      innodb_flush_log_at_timeout 간격 (L2600)  또는 flush_events[slot] 직접
 log_write_notifier   write_notifier_event                     write_events[slot] (L2727)
 log_flush_notifier   flush_notifier_event                     flush_events[slot] (L2849)
 log_checkpointer     checkpointer_event (log0chkp.cc L951)    buf_flush_event (sync flush 요청, L670)
                                                               next_checkpoint_event (L410)
 log_files_governor   m_files_governor_event                   (redo 파일 생성/삭제)

 slot = (lsn - 1) / OS_FILE_LOG_BLOCK_SIZE % S   (log0write.cc 주석 L325, L371)
 같은 512바이트 블록을 기다리는 사용자들이 한 이벤트를 같이 쓴다
```

## page cleaner 코디네이터와 워커

page cleaner 는 버퍼 풀 인스턴스마다 **슬롯 하나**를 만든다. 코디네이터가 모든 슬롯을 "요청됨"으로 바꾸고 `is_requested` 를 set 하면, 워커와 코디네이터 자신이 슬롯을 하나씩 집어 그 인스턴스를 플러시한다. 마지막 슬롯을 끝낸 스레드가 `is_finished` 를 set 한다. 본체는 [페이지 플러시, doublewrite, 체크포인트](../../flows/flush-checkpoint/README.md)의 [01] [02] 에 있다.

`storage` / `innobase` / `buf` / `buf0flu.cc` L2523-L2550 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0flu.cc#L2523-L2550))

```cpp
// buf0flu.cc L2523-L2550
void buf_flush_page_cleaner_init() {
  ut_ad(page_cleaner == nullptr);

  page_cleaner = ut::make_unique<page_cleaner_t>(UT_NEW_THIS_FILE_PSI_KEY);

  mutex_create(LATCH_ID_PAGE_CLEANER, &page_cleaner->mutex);

  page_cleaner->is_requested = os_event_create();
  page_cleaner->is_finished = os_event_create();

  page_cleaner->n_slots = static_cast<ulint>(srv_buf_pool_instances);

  page_cleaner->slots = ut::make_unique<page_cleaner_slot_t[]>(
      UT_NEW_THIS_FILE_PSI_KEY, page_cleaner->n_slots);

  ut_d(page_cleaner->n_disabled_debug = 0);

  page_cleaner->is_running = true;

  srv_threads.m_page_cleaner_coordinator = os_thread_create(
      page_flush_coordinator_thread_key, 0, buf_flush_page_coordinator_thread);

  srv_threads.m_page_cleaner_workers[0] =
      srv_threads.m_page_cleaner_coordinator;

  srv_threads.m_page_cleaner_coordinator.start();

  /* Make sure page cleaner is active. */
```

워커는 `is_requested` 하나만 기다린다.

`storage` / `innobase` / `buf` / `buf0flu.cc` L3298-L3319 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0flu.cc#L3298-L3319))

```cpp
// buf0flu.cc L3298-L3319
static void buf_flush_page_cleaner_thread() {
// ... (L3299-L3307 생략: Linux 스레드 우선순위)
  for (;;) {
    os_event_wait(page_cleaner->is_requested);

    ut_d(buf_flush_page_cleaner_disabled_loop());

    if (!page_cleaner->is_running) {
      break;
    }

    pc_flush_slot();
  }
}
```

```text
 한 바퀴 (buf_flush_page_coordinator_thread, buf0flu.cc L2875)

 코디네이터                                워커 1..n-1
 buf_flush_event 또는 최대 1초 대기
   (pc_sleep_if_needed L2509)
 pc_request(n, lsn_limit)   L3085
   slot[i].state = REQUESTED  (n_slots = 인스턴스 수, L2533)
   is_requested set   L2619  ----------->  os_event_wait(is_requested)  L3309
 pc_flush_slot() 반복  L3090                pc_flush_slot()             L3317
   (코디네이터도 일한다)                       슬롯 하나 = 인스턴스 하나의 LRU + flush_list
                                             마지막이면 is_finished set  L2708
 pc_wait_finished            <-----------
   os_event_wait(is_finished)  L2731
   buf_flush_tick_event set    L2759     -> sync flush 를 요청한 log_checkpointer 가 깬다

 buf_flush_event 를 set 하는 곳
   log_request_sync_flush      log0chkp.cc L670   체크포인트가 밀릴 때
   buf_LRU_get_free_block      buf0lru.cc L1405   LRU 를 다 뒤져도 free 블록이 없을 때
```

## purge 코디네이터와 워커

purge 는 코디네이터가 일감을 나눠 큐에 넣고 워커를 깨우는 구조다. 코디네이터도 마지막 일감을 직접 돈다. 흐름 본체는 [purge](../../flows/purge/README.md)에 있다.

`storage` / `innobase` / `srv` / `srv0start.cc` L2169-L2193 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/srv/srv0start.cc#L2169-L2193))

```cpp
// srv0start.cc L2169-L2193
void srv_start_purge_threads() {
  /* Start purge threads only if they are not started earlier. */
  if (srv_start_state_is_set(SRV_START_STATE_PURGE)) {
    return;
  }

  srv_threads.m_purge_coordinator =
      os_thread_create(srv_purge_thread_key, 0, srv_purge_coordinator_thread);

  srv_threads.m_purge_workers[0] = srv_threads.m_purge_coordinator;

  /* We've already created the purge coordinator thread above. */
  for (size_t i = 1; i < srv_threads.m_purge_workers_n; ++i) {
    srv_threads.m_purge_workers[i] =
        os_thread_create(srv_worker_thread_key, i, srv_worker_thread);
  }

  for (size_t i = 0; i < srv_threads.m_purge_workers_n; ++i) {
    srv_threads.m_purge_workers[i].start();
  }

  srv_start_wait_for_purge_to_start();

  srv_start_state_set(SRV_START_STATE_PURGE);
}
```

`storage` / `innobase` / `trx` / `trx0purge.cc` L2424-L2439 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0purge.cc#L2424-L2439))

```cpp
// trx0purge.cc L2424-L2439
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
```

`storage` / `innobase` / `srv` / `srv0srv.cc` L3150-L3160 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/srv/srv0srv.cc#L3150-L3160))

```cpp
// srv0srv.cc L3150-L3160
void srv_que_task_enqueue_low(que_thr_t *thr) /*!< in: query thread */
{
  ut_ad(!srv_read_only_mode);
  mutex_enter(&srv_sys->tasks_mutex);

  UT_LIST_ADD_LAST(srv_sys->tasks, thr);

  mutex_exit(&srv_sys->tasks_mutex);

  srv_release_threads(SRV_WORKER, 1);
}
```

워커는 자기 슬롯 이벤트에서 자다가, 깨면 큐에서 일감 하나를 꺼내 돈다.

`storage` / `innobase` / `srv` / `srv0srv.cc` L2813-L2827 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/srv/srv0srv.cc#L2813-L2827))

```cpp
// srv0srv.cc L2813-L2827
  do {
    srv_suspend_thread(slot);

    os_event_wait(slot->event);

    if (srv_task_execute()) {
      /* If there are tasks in the queue, wakeup
      the purge coordinator thread. */

      srv_wake_purge_thread_if_not_active();
    }

    /* Note: we are checking the state without holding the
    purge_sys->latch here. */
  } while (purge_sys->state != PURGE_STATE_EXIT);
```

```text
 purge 의 신호선

 코디네이터 (srv_purge_coordinator_thread, srv0srv.cc L3032)
   잘 때  srv_purge_coordinator_suspend L2923
          slot->event 에서 최대 10ms (SRV_PURGE_MAX_TIMEOUT L2935, 대기 L2956)
   깨우는 이
     커밋   trx_purge_add_update_undo_to_history  history 길이 > 스레드 수 x 배치 (trx0purge.cc L409)
     master srv_master_do_active_tasks           history 가 0 이 아니면 (srv0srv.cc L2301-L2303)
     워커   일을 끝내고 큐에 남은 게 있으면      (L2818-L2822)
   깨면   trx_purge -> 일감 n-1 개를 큐에 넣고 (L2429) 마지막은 직접 (que_run_threads)
          trx_purge_wait_for_workers_to_complete (L2439)

 워커 (srv_worker_thread, srv0srv.cc L2789)
   잘 때  slot->event (L2816)
   깨우는 이  srv_que_task_enqueue_low -> srv_release_threads(SRV_WORKER, 1) (L3159)
```

## master 스레드

8.0 이후 master 는 주기적 체크포인트를 하지 않는다. 그 일은 log_checkpointer 로 넘어갔다고 시작 코드 주석이 적어 두었다(srv0start.cc L2199-L2202). 지금의 master 는 1초마다 깨어 잡일을 하는 스레드다.

`storage` / `innobase` / `srv` / `srv0srv.cc` L2597-L2602 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/srv/srv0srv.cc#L2597-L2602))

```cpp
// srv0srv.cc L2597-L2602
static void srv_master_sleep(void) {
  srv_main_thread_op_info = "sleeping";
  std::this_thread::sleep_for(std::chrono::seconds(1));
  CONDITIONAL_SYNC_POINT("srv_master_sleep");
  srv_main_thread_op_info = "";
}
```

`storage` / `innobase` / `srv` / `srv0srv.cc` L2639-L2659 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/srv/srv0srv.cc#L2639-L2659))

```cpp
// srv0srv.cc L2639-L2659
    srv_master_sleep();

    MONITOR_INC(MONITOR_MASTER_THREAD_SLEEP);

    /* Just in case - if there is not much free space in redo,
    try to avoid asking for troubles because of extra work
    performed in such background thread. */
    srv_main_thread_op_info = "checking free log space";
    log_free_check();

    if (srv_check_activity(old_activity_count)) {
      old_activity_count = srv_get_activity_count();
      srv_master_do_active_tasks();
    } else {
      srv_master_do_idle_tasks();
    }

    /* Purge any deleted tablespace pages. */
    fil_purge();
  }
}
```

```text
 master 의 1초 (srv_master_main_loop, srv0srv.cc L2620)

 sleep_for(1s)                          L2599   이벤트를 기다리지 않는다
 log_free_check                         L2647   redo 여유가 없으면 여기서 멈춘다
 활동이 있었으면 srv_master_do_active_tasks (L2250)
   백그라운드 DROP TABLE              L2267
   change buffer 머지                 L2284
   log_buffer_sync_in_background      L2289
   history 가 있으면 purge 깨우기      L2301-L2303
   딕셔너리 캐시 축출 (주기)           L2305-L2314
 없었으면 srv_master_do_idle_tasks (L2324)
 fil_purge                              L2657
```

## 잠금 대기와 lock_wait_timeout

잠금 대기는 **연결 스레드가 직접 잔다.** 잠금이 충돌하면 `lock_wait_suspend_thread` 가 `lock_sys->waiting_threads` 배열에서 슬롯을 하나 얻어 그 이벤트에서 잔다. 깨우는 이는 둘이다. 잠금을 풀어 대기를 허가한 다른 연결 스레드, 그리고 시간 초과나 교착을 판정한 `lock_wait_timeout` 스레드다. 흐름은 [레코드 잠금과 교착](../../flows/record-lock/README.md)의 [09] [10] 에 있다.

`storage` / `innobase` / `lock` / `lock0wait.cc` L1432-L1459 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0wait.cc#L1432-L1459))

```cpp
// lock0wait.cc L1432-L1459
void lock_wait_timeout_thread() {
  int64_t sig_count = 0;
  os_event_t event = lock_sys->timeout_event;

  ut_ad(!srv_read_only_mode);

  /** The last time we've checked for timeouts. */
  auto last_checked_for_timeouts_at = std::chrono::steady_clock::now();
  do {
    auto current_time = std::chrono::steady_clock::now(); /* Calling this more
    often than once a second isn't needed, as lock timeouts are specified with
    one second resolution, so probably nobody cares if we wake up after T or
    T+0.99, when T itself can't be precise. */
    if (std::chrono::seconds(1) <=
        current_time - last_checked_for_timeouts_at) {
      last_checked_for_timeouts_at = current_time;
      lock_wait_check_slots_for_timeouts();
    }

    lock_wait_update_schedule_and_check_for_deadlocks();

    /* When someone is waiting for a lock, we wake up every second (at worst)
    and check if a timeout has passed for a lock wait */
    os_event_wait_time_low(event, std::chrono::seconds{1}, sig_count);
    sig_count = os_event_reset(event);

  } while (srv_shutdown_state.load() < SRV_SHUTDOWN_CLEANUP);
}
```

```text
 잠금 대기의 신호선

 연결 스레드 A (대기자)
   lock_wait_suspend_thread           lock0wait.cc L206
     슬롯 예약 -> 대기 간선이 생겼다고 알림
       lock_wait_request_check_for_cycles -> timeout_event set  (L188, L204)
       timeout_event 를 set 하는 함수는 lock_set_timeout_event 하나 (lock0lock.cc L5961)
       부르는 곳: 위 L204, 대기 간선 갱신 lock_update_wait_for_edge (lock0lock.cc L2054),
                  innodb_deadlock_detect 변경 (ha_innodb.cc L20872), 긴 세마포어 대기 진단
                  (sync0arr.cc L890), 종료 (srv0start.cc L1133)
     os_event_wait(slot->event)       L297

 lock_wait_timeout 스레드
   timeout_event 또는 1초               L1455
   1초마다 슬롯을 훑어 innodb_lock_wait_timeout 초과를 찾는다  L1448
   wait-for 그래프를 갱신하고 교착이면 희생자를 고른다         L1451
   -> 시간 초과 lock0wait.cc L497 / 교착 희생자 L701 에서 lock_cancel_waiting_and_release
      -> lock_reset_wait_and_release_thread_if_suspended (lock0lock.cc L5755)
      -> 아래 B 와 같은 L416 에서 희생자의 slot->event set

 연결 스레드 B (잠금을 푸는 쪽)
   커밋/롤백에서 잠금을 풀며 A 의 대기를 허가
   -> lock_wait_release_thread_if_suspended -> os_event_set(thr->slot->event)  L416
      이 함수가 slot->event 를 set 하는 유일한 자리다 (주석 L370-L371)
```

## 연결 스레드

연결 스레드는 SQL 계층 스레드지만, InnoDB 안에서는 위 그림의 "사용자 스레드"다. 연결이 끝나도 바로 죽지 않고 스레드 캐시에서 다음 연결을 기다린다. 대기와 깨움은 조건 변수 `COND_thread_cache` 하나다.

`sql` / `conn_handler` / `connection_handler_impl.h` L42-L72 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/conn_handler/connection_handler_impl.h#L42-L72))

```cpp
// connection_handler_impl.h L42-L72
class Per_thread_connection_handler : public Connection_handler {
  Per_thread_connection_handler(const Per_thread_connection_handler &);
  Per_thread_connection_handler &operator=(
      const Per_thread_connection_handler &);
  // ... (L46-L59 생략: check_idle_thread_and_enqueue_connection 과 대기 목록 주석)
  static std::list<Channel_info *> *waiting_channel_info_list;

  static mysql_mutex_t LOCK_thread_cache;
  static mysql_cond_t COND_thread_cache;
  static mysql_cond_t COND_flush_thread_cache;

 public:
  // Status variables related to Per_thread_connection_handler
  static ulong blocked_pthread_count;  // Protected by LOCK_thread_cache.
  static ulong slow_launch_threads;
  static bool shrink_cache;  // Protected by LOCK_thread_cache
  // System variable
  static ulong max_blocked_pthreads;
```

```text
 스레드 캐시의 신호선 (sql/conn_handler/connection_handler_per_thread.cc)

 리스너 스레드
   check_idle_thread_and_enqueue_connection   L387
     blocked_pthread_count > wake_pthread 이면
     waiting_channel_info_list 에 넣고 COND_thread_cache signal  L396
     아니면 새 스레드를 만든다 (handle_connection)

 연결을 끝낸 연결 스레드
   block_until_new_connection
     blocked_pthread_count++
     COND_thread_cache 에서 잔다  L162
     깨면 목록에서 Channel_info 를 꺼내 handle_connection 의 for(;;) 처음으로
```

## db-engine 에서는

db-engine 에는 **백그라운드 스레드가 없다.** 스레드는 `ConnectionPool` 의 고정 크기 실행기 하나뿐이고, MySQL 이 백그라운드로 떼어 낸 일은 호출한 스레드가 그 자리에서 한다.

```text
 같은 일, 누가 하는가 (위 MySQL / 아래 db-engine)

 요청 실행
   MySQL      연결 1개 = OS 스레드 1개. 끝나면 COND_thread_cache 에서 다음 연결을 기다린다
   db-engine  Executors.newFixedThreadPool(capacity). submit(sessionId) 로 일을 넘긴다
              세션과 스레드가 묶여 있지 않다

 커밋의 redo 내구성
   MySQL      연결 스레드는 writer_event 를 set 하고 flush_events[slot] 에서 잔다
              log_writer -> log_flusher -> log_flush_notifier 가 대신 쓰고 fsync 한다
   db-engine  Transaction.commit 이 호출 스레드에서 logManager.sync() 를 직접 부른다 (impl 08-01)

 dirty 페이지 내려쓰기
   MySQL      page cleaner 코디네이터 + 워커, 인스턴스마다 슬롯
   db-engine  evictOne 이 쫓아낼 때, 또는 flushAll 을 부를 때 (impl 02-02)

 체크포인트
   MySQL      log_checkpointer 가 주기적으로, 또는 redo 공간이 모자랄 때
   db-engine  checkpoint(activeTxs) 를 부를 때 (impl 08-02)

 잠금 대기
   MySQL      대기자가 slot->event 에서 자고 lock_wait_timeout 이 시간 초과와 교착을 본다
   db-engine  기다리지 않는다. LockConflict 즉시 실패 (impl 09-01)
```

db-engine 13-01 은 실행기 큐가 무제한(`LinkedBlockingQueue`)이라 세션이 몰리면 작업이 조용히 쌓인다고 적었다. MySQL 의 연결 스레드는 연결 수만큼 생기므로 큐는 없지만, 그 대신 `max_connections` 에서 연결 자체를 거절한다. 챕터: [13-01-connection-pool](../../../../../project/db-engine/13-01-connection-pool/), 비교에 쓴 다른 장은 [08-01-wal-recovery](../../../../../project/db-engine/08-01-wal-recovery/), [02-02-buffer-pool](../../../../../project/db-engine/02-02-buffer-pool/), [09-01-lock-manager](../../../../../project/db-engine/09-01-lock-manager/).

## 어디에서 쓰이는가

```text
 [연결과 스레드]                연결 스레드의 생애, 스레드 캐시
 [mini-transaction과 redo 기록] [09] log_writer, [10] log_flusher 의 본체
 [커밋과 binlog 2PC]            커밋이 log_write_up_to 로 flush_events 에서 기다리는 자리
 [페이지 플러시, doublewrite, 체크포인트]  [01] page cleaner 코디네이터, [08] log_checkpointer
 [purge]                        코디네이터와 워커의 본체
 [레코드 잠금과 교착]           [09] lock_wait_suspend_thread, [10] lock_wait_timeout_thread
 [크래시 복구]                  srv_start 가 복구 전에 page cleaner 를, 복구 뒤에 나머지를 띄운다
```

redo 스레드 본체는 [mtr-redo 의 log_writer](../../flows/mtr-redo/09_log_writer/README.md)와 [log_flusher](../../flows/mtr-redo/10_log_flusher/README.md), page cleaner 와 체크포인터는 [페이지 플러시, doublewrite, 체크포인트](../../flows/flush-checkpoint/README.md), 연결 스레드는 [handle_connection](../../flows/connection-thread/03_handle_connection/README.md)에 있다. 이 스레드들이 함께 만지는 객체는 [메모리 구조](../memory-structures/README.md)에 있다.

## 다루지 않는 것

I/O 핸들러 스레드(`os_aio_start_threads`, srv0start.cc L1577)와 Linux native AIO, `innodb_monitor` 와 error monitor 의 출력 내용, `dict_stats_thread` 의 통계 갱신 조건, `buf_dump_thread` 와 `buf_resize_thread`, 전문 검색 최적화 스레드, GTID persister, Clone 의 log/page 아카이버와 MEB redo 아카이버, 복구 중의 `m_recv_writer`, `innodb_thread_concurrency` 의 입장권(`n_tickets_to_enter_innodb`), thread pool 플러그인과 `thread_handling` 의 다른 값, 종료 순서(`srv_shutdown_state` 의 단계별로 어떤 스레드가 먼저 멈추는가)는 같은 뼈대의 곁가지라 요약만 했다.
