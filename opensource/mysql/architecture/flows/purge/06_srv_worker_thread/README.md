# srv_worker_thread

상위: [purge](../README.md)

**purge 워커 스레드의 본체다.** 하는 일은 "슬롯 이벤트에서 잠들었다가, 깨면 작업 큐(`srv_sys->tasks`)에서 query thread 하나를 꺼내 실행한다"의 반복이 전부다. 작업 하나는 [05] 가 만든 그룹 하나이고, 실행하면 [07] `row_purge_step` 이 그 그룹의 undo 레코드를 차례로 처리한다. 다 끝내면 `purge_sys->n_completed` 를 하나 올려 코디네이터에게 알린다. 워커는 `innodb_purge_threads - 1` 개다. 1 이면 워커가 없고 코디네이터 혼자 처리한다(`ut_a(srv_n_purge_threads > 1)`, L2801). 워커는 스스로 history 를 보지 않는다. 무엇을 할지는 전부 코디네이터가 정해서 큐에 넣는다.

## 위치

`storage` / `innobase` / `srv` / `srv0srv.cc` L2789-L2840 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/srv/srv0srv.cc#L2789-L2840))

## 실제 코드

함수 전체다. 주석이 종료 순서를 적었다. 워커는 코디네이터보다 늦게 끝나야 한다. 그렇지 않으면 코디네이터가 [03] 의 기다림에서 영원히 멈출 수 있다.

`storage` / `innobase` / `srv` / `srv0srv.cc` L2788-L2840 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/srv/srv0srv.cc#L2788-L2840))

```cpp
// srv0srv.cc L2788-L2840
/** Worker thread that reads tasks from the work queue and executes them. */
void srv_worker_thread() {
  srv_slot_t *slot;

  ut_ad(!srv_read_only_mode);
  ut_a(srv_force_recovery < SRV_FORCE_NO_BACKGROUND);

  THD *thd = create_internal_thd();

  purge_sys->is_this_a_purge_thread = true;

  slot = srv_reserve_slot(SRV_WORKER);

  ut_a(srv_n_purge_threads > 1);

  srv_sys_mutex_enter();

  ut_a(srv_sys->n_threads_active[SRV_WORKER] < srv_n_purge_threads);

  srv_sys_mutex_exit();

  /* We need to ensure that the worker threads exit after the
  purge coordinator thread. Otherwise the purge coordinaor can
  end up waiting forever in trx_purge_wait_for_workers_to_complete() */

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

  srv_free_slot(slot);

  rw_lock_x_lock(&purge_sys->latch, UT_LOCATION_HERE);

  ut_a(!purge_sys->running);
  ut_a(purge_sys->state == PURGE_STATE_EXIT);
  ut_a(srv_shutdown_state.load() >= SRV_SHUTDOWN_PURGE);

  rw_lock_x_unlock(&purge_sys->latch);

  destroy_internal_thd(thd);
}
```

큐에서 작업 하나를 꺼내 실행하는 쪽이다. 큐가 비어 있으면 뮤텍스도 잡지 않고 돌아간다.

`storage` / `innobase` / `srv` / `srv0srv.cc` L2755-L2786 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/srv/srv0srv.cc#L2755-L2786))

```cpp
// srv0srv.cc L2755-L2786
/** Fetch and execute a task from the work queue.
 @return true if a task was executed */
static bool srv_task_execute(void) {
  que_thr_t *thr = nullptr;

  ut_ad(!srv_read_only_mode);
  ut_a(srv_force_recovery < SRV_FORCE_NO_BACKGROUND);

  if (UT_LIST_GET_LEN(srv_sys->tasks) == 0) {
    return false;
  }

  mutex_enter(&srv_sys->tasks_mutex);

  if (UT_LIST_GET_LEN(srv_sys->tasks) > 0) {
    thr = UT_LIST_GET_FIRST(srv_sys->tasks);

    ut_a(que_node_get_type(thr->child) == QUE_NODE_PURGE);

    UT_LIST_REMOVE(srv_sys->tasks, thr);
  }

  mutex_exit(&srv_sys->tasks_mutex);

  if (thr != nullptr) {
    que_run_threads(thr);

    purge_sys->n_completed.fetch_add(1);
  }

  return (thr != nullptr);
}
```

큐에 넣는 쪽이다. 코디네이터가 [03] 에서 그룹마다 부른다. 넣고 나서 잠든 워커 하나를 깨운다.

`storage` / `innobase` / `srv` / `srv0srv.cc` L3147-L3158 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/srv/srv0srv.cc#L3147-L3158))

```cpp
// srv0srv.cc L3147-L3158

/** Enqueues a task to server task queue and releases a worker thread, if there
is a suspended one. */
void srv_que_task_enqueue_low(que_thr_t *thr) /*!< in: query thread */
{
  ut_ad(!srv_read_only_mode);
  mutex_enter(&srv_sys->tasks_mutex);

  UT_LIST_ADD_LAST(srv_sys->tasks, thr);

  mutex_exit(&srv_sys->tasks_mutex);

```

## 동작 흐름

```text
 srv_worker_thread   (워커 i, i = 1 .. innodb_purge_threads - 1, srv0start.cc L2181-L2184)

 L2795  create_internal_thd
 L2797  purge_sys->is_this_a_purge_thread = true
 L2799  slot = srv_reserve_slot(SRV_WORKER)
 L2813  do
 L2814    srv_suspend_thread(slot)
 L2816    os_event_wait(slot->event)                잠든다. srv_que_task_enqueue_low 가 깨운다
 L2818    if (srv_task_execute())
            L2763  큐가 비어 있으면 false
            L2767  tasks_mutex 안에서 맨 앞 thr 를 꺼낸다
            L2780  que_run_threads(thr)            --> [07] row_purge_step
            L2782  purge_sys->n_completed++         코디네이터의 wait 가 이것을 센다
 L2822      srv_wake_purge_thread_if_not_active   코디네이터가 자고 있으면 깨운다
 L2827  while (purge_sys->state != PURGE_STATE_EXIT)
 L2829  srv_free_slot, 상태 확인, destroy_internal_thd
```

코디네이터와 워커 사이에 오가는 것은 큐 하나와 계수기 둘이다.

```text
 코디네이터 ([03] trx_purge)                       워커 (이 함수)
 -----------------------------------------------   ------------------------------------
 que_fork_scheduler_round_robin 으로 thr 고르기
 srv_que_task_enqueue_low(thr)
   tasks_mutex { tasks.push_back(thr) }  ------->  srv_task_execute
   srv_release_threads(SRV_WORKER, 1)    ------->    os_event_wait 에서 깨어남
 n_submitted += n - 1                                tasks_mutex { thr = tasks.front; pop }
 que_run_threads(자기 몫)                            que_run_threads(thr)
 trx_purge_wait_for_workers_to_complete              n_completed.fetch_add(1)
   while (n_completed != n_submitted)    <-------
     yield x 10, 그래도 안 끝났고 큐가 남았으면
     srv_release_threads(SRV_WORKER, 1), 20us 잠
```

```text
 종료 순서 (주석 L2809-L2811 과 [01] 의 끝)

 코디네이터  state = PURGE_STATE_EXIT  ->  srv_release_threads(SRV_WORKER, n - 1)  ->  끝
 워커        깨어남 -> 큐는 비어 있다 -> while 조건에서 EXIT 를 보고 빠져나온다
 워커가 먼저 끝나면 코디네이터가 마지막 배치의 n_completed 를 영원히 기다릴 수 있다
```

## 결과가 쓰이는 곳

```text
 purge_sys->n_completed   --> [03] trx_purge_wait_for_workers_to_complete
 실행된 그룹              --> [07] 이 B+Tree 를 고친다 (delete-mark 레코드 삭제 등)
```

## 다루지 않는 것

슬롯 배열과 이벤트(`srv_reserve_slot`, `srv_suspend_thread`, `srv_release_threads`)의 일반 구조, query graph 실행기(`que_run_threads`)의 노드 순회는 이 흐름의 곁가지라 줄만 적었다. 워커를 띄우는 `srv_start_purge_threads` 는 [스레드 구성](../../../structure/threads/README.md)에 둔다.
