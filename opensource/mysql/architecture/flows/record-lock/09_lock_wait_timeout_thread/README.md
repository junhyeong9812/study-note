# lock_wait_timeout_thread

상위: [레코드 잠금과 교착](../README.md)

**잠든 트랜잭션들을 바깥에서 지켜보는 백그라운드 스레드 하나다.** 매 바퀴 두 가지를 한다. 1초에 한 번 모든 대기 슬롯을 훑어 `innodb_lock_wait_timeout` 을 넘긴 대기를 취소하고, 매 바퀴 대기 슬롯의 스냅샷으로 wait-for 그래프를 만들어 순환을 찾는다(순환 처리는 [10]). 대기는 사용자 스레드가, 탐지는 이 스레드가 맡는 구조라서, 잠금을 거는 경로([05], [07])에는 그래프 탐색 비용이 없다.

## 위치

`storage` / `innobase` / `lock` / `lock0wait.cc` L1432-L1459 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0wait.cc#L1432-L1459))

## 실제 코드

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

서버 시작 때 만들어진다.

`storage` / `innobase` / `srv` / `srv0start.cc` L1995-L1998 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/srv/srv0start.cc#L1995-L1998))

```cpp
// srv0start.cc L1995-L1998
    /* Create the thread which watches the timeouts
    for lock waits */
    srv_threads.m_lock_wait_timeout = os_thread_create(
        srv_lock_timeout_thread_key, 0, lock_wait_timeout_thread);
```

### 타임아웃

`storage` / `innobase` / `lock` / `lock0wait.cc` L541-L556 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0wait.cc#L541-L556))

```cpp
// lock0wait.cc L541-L556
static void lock_wait_check_slots_for_timeouts() {
  ut_ad(!lock_wait_mutex_own());
  lock_wait_mutex_enter();

  for (auto slot = lock_sys->waiting_threads; slot < lock_sys->last_slot;
       ++slot) {
    /* We are doing a read without latching the lock_sys or the trx mutex.
    This is OK, because a slot can't be freed or reserved without the lock wait
    mutex. */
    if (slot->in_use) {
      lock_wait_check_and_cancel(slot);
    }
  }

  lock_wait_mutex_exit();
}
```

`storage` / `innobase` / `lock` / `lock0wait.cc` L501-L517 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0wait.cc#L501-L517))

```cpp
// lock0wait.cc L501-L517
static void lock_wait_check_and_cancel(
    const srv_slot_t *slot) /*!< in: slot reserved by a user
                            thread when the wait started */
{
  const auto wait_time = std::chrono::steady_clock::now() - slot->suspend_time;
  /* Timeout exceeded or a wrap-around in system time counter */
  const auto timeout = slot->wait_timeout < std::chrono::seconds{100000000} &&
                       wait_time > slot->wait_timeout;
  trx_t *trx = thr_get_trx(slot->thr);

  if (!trx_is_interrupted(trx) && !timeout) {
    return;
  }
  /* We don't expect trx to commit (change version) as we hold lock_wait mutex
  preventing the trx from leaving the slot. */
  locksys::run_if_waiting({trx}, [&]() { lock_wait_try_cancel(trx, timeout); });
}
```

`storage` / `innobase` / `lock` / `lock0wait.cc` L463-L498 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0wait.cc#L463-L498))

```cpp
// lock0wait.cc L463-L498
static void lock_wait_try_cancel(trx_t *trx, bool timeout) {
  ut_a(trx->lock.wait_lock != nullptr);
  ut_ad(locksys::owns_lock_shard(trx->lock.wait_lock));
  ut_a(trx->lock.que_state == TRX_QUE_LOCK_WAIT);
  // ... (L467-L476 생략: high priority 트랜잭션은 상대가 high priority 일 때만 포기한다)
  ut_ad(trx_mutex_own(trx));
  if (timeout) {
    // ... (L479-L484 생략: DB_DEADLOCK 을 덮어쓰지 않는다는 설명)
    trx->error_state = DB_LOCK_WAIT_TIMEOUT;
    // ... (L486-L493 생략: 같은 이유의 ut_ad 설명)
  }
  /* Cancel the lock request queued by the transaction and release possible
  other transactions waiting behind. */
  lock_cancel_waiting_and_release(trx);
}
```

대기를 취소하는 공통 함수다. 기다리던 잠금을 큐에서 빼면서(그 뒤의 대기자에게 부여할 기회를 주고) 스레드를 깨운다.

`storage` / `innobase` / `lock` / `lock0lock.cc` L5742-L5756 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0lock.cc#L5742-L5756))

```cpp
// lock0lock.cc L5742-L5756
void lock_cancel_waiting_and_release(trx_t *trx) {
  ut_ad(trx_mutex_own(trx));
  const auto lock = trx->lock.wait_lock.load();
  ut_ad(locksys::owns_lock_shard(lock));

  if (lock_get_type_low(lock) == LOCK_REC) {
    lock_rec_dequeue_from_page(lock);
  } else {
    ut_ad(lock_get_type_low(lock) & LOCK_TABLE);

    lock_table_dequeue(lock);
  }

  lock_reset_wait_and_release_thread_if_suspended(lock);
}
```

### wait-for 그래프

`storage` / `innobase` / `lock` / `lock0wait.cc` L1377-L1427 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0wait.cc#L1377-L1427))

```cpp
// lock0wait.cc L1377-L1427
static void lock_wait_update_schedule_and_check_for_deadlocks() {
  // ... (L1378-L1411 생략: 지역 vector 를 쓰는 이유에 대한 실험 기록)
  ut::vector<waiting_trx_info_t> infos;
  ut::vector<int> outgoing;
  ut::vector<trx_schedule_weight_t> new_weights;

  auto table_reservations = lock_wait_snapshot_waiting_threads(infos);
  lock_wait_build_wait_for_graph(infos, outgoing);

  /* We don't update trx->lock.schedule_weight for trxs on cycles. */
  lock_wait_compute_and_publish_weights_except_cycles(infos, table_reservations,
                                                      outgoing, new_weights);

  if (innobase_deadlock_detect) {
    /* This will also update trx->lock.schedule_weight for trxs on cycles. */
    lock_wait_find_and_handle_deadlocks(infos, outgoing, new_weights);
  }
}
```

스냅샷은 슬롯마다 `(나, 내가 기다리는 trx, 슬롯, reservation_no)` 한 줄이다. 간선의 끝은 [07] 이 적어 둔 `blocking_trx` 다.

`storage` / `innobase` / `lock` / `lock0wait.cc` L562-L597 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0wait.cc#L562-L597))

```cpp
// lock0wait.cc L562-L597
static uint64_t lock_wait_snapshot_waiting_threads(
    ut::vector<waiting_trx_info_t> &infos) {
  ut_ad(!lock_wait_mutex_own());
  infos.clear();
  lock_wait_mutex_enter();
  // ... (L567-L583 생략: 스냅샷을 짧게 잡는 이유)
  const auto table_reservations = lock_wait_table_reservations;
  for (auto slot = lock_sys->waiting_threads; slot < lock_sys->last_slot;
       ++slot) {
    if (slot->in_use) {
      auto from = thr_get_trx(slot->thr);
      auto to = from->lock.blocking_trx.load();
      if (to != nullptr) {
        infos.push_back({from, to, slot, slot->reservation_no});
      }
    }
  }
  lock_wait_mutex_exit();
  return table_reservations;
}
```

`storage` / `innobase` / `lock` / `lock0wait.cc` L650-L688 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0wait.cc#L650-L688))

```cpp
// lock0wait.cc L650-L688
static void lock_wait_build_wait_for_graph(
    ut::vector<waiting_trx_info_t> &infos, ut::vector<int> &outgoing) {
  /** We are going to use int and uint to store positions within infos */
  ut_ad(infos.size() < std::numeric_limits<uint>::max());
  const auto n = static_cast<uint>(infos.size());
  ut_ad(n < static_cast<uint>(std::numeric_limits<int>::max()));
  outgoing.clear();
  outgoing.resize(n, -1);
  // ... (L658-L670 생략: 정렬 + 이분 탐색을 고른 이유)
  sort(infos.begin(), infos.end());
  waiting_trx_info_t needle{};
  for (uint from = 0; from < n; ++from) {
    /* Assert that the order used by sort and lower_bound depends only on the
    trx field, as this is the only one we will initialize in the needle. */
    ut_ad(from == 0 ||
          std::less<trx_t *>{}(infos[from - 1].trx, infos[from].trx));
    needle.trx = infos[from].waits_for;
    auto it = std::lower_bound(infos.begin(), infos.end(), needle);

    if (it == infos.end() || it->trx != needle.trx) {
      continue;
    }
    auto to = it - infos.begin();
    ut_ad(from != static_cast<uint>(to));
    outgoing[from] = static_cast<int>(to);
  }
}
```

## 동작 흐름

```text
 L1434  event = lock_sys->timeout_event
 L1440  do {
 L1445    지난 검사 뒤 1 초가 지났으면
 L1448      lock_wait_check_slots_for_timeouts
              L543  lock_wait_mutex_enter
              L545  쓰는 슬롯마다 lock_wait_check_and_cancel
                      L507  대기 시간 > wait_timeout 이면 timeout
                      L511  timeout 도 아니고 KILL 도 아니면 넘어간다
                      L516  run_if_waiting -> lock_wait_try_cancel
                              L485  error_state = DB_LOCK_WAIT_TIMEOUT
                              L497  lock_cancel_waiting_and_release
                                      lock0lock.cc L5748  대기 잠금을 큐에서 뺀다 + 뒤 대기자 부여 검토
                                      lock0lock.cc L5755  스레드를 깨운다 -> [08] L297
 L1451    lock_wait_update_schedule_and_check_for_deadlocks
            L1416  스냅샷 (lock_wait_mutex 아래, 짧게)
            L1417  그래프: outgoing[i] = 기다리는 상대의 index, 없으면 -1
            L1420  schedule_weight 계산과 공개 (순환 위의 trx 는 빼고)
            L1423  innodb_deadlock_detect 가 켜져 있으면
            L1425    [10] lock_wait_find_and_handle_deadlocks
 L1455    os_event_wait_time_low(event, 1 초)   누가 set 하거나 1 초가 지나면 깨어난다
 L1456    sig_count = os_event_reset(event)
 L1458  } while (종료 단계가 CLEANUP 전)
```

이 스레드를 깨우는 것은 `timeout_event` 하나다. 그래프가 바뀔 만한 일이 생기면 그 일을 한 스레드가 이 이벤트를 set 한다.

```text
 timeout_event 를 set 하는 자리 (lock_wait_request_check_for_cycles, L204)

 [08] lock_wait_table_reserve_slot L188     새 대기자가 슬롯에 들어왔다 (새 노드와 간선)
 lock_update_wait_for_edge  lock0lock.cc L2054  기다리는 이유(간선 끝)가 바뀌었다
 그 밖에는 1 초 시한으로 깨어난다 (L1455)
```

그래프는 "대기자마다 나가는 간선이 하나"인 모양이다. 트랜잭션은 한 번에 하나의 잠금만 기다리고, [07] 이 그 잠금을 막는 trx 하나만 `blocking_trx` 로 적기 때문이다.

```text
 스냅샷에서 그래프까지 (예: 대기자 셋)

 슬롯 스냅샷 infos (L591)              정렬 후 index   outgoing (L686)
   trx  waits_for  reservation_no
   T2   T1         7                   0: T1 -> T3      0 -> 2
   T3   T4         9                   1: T2 -> T1      1 -> 0
   T1   T3         12                  2: T3 -> T4      2 -> -1   T4 는 대기자가 아니다
 정렬은 trx 포인터 주소 순이다 (L671). 예에서는 T1 < T2 < T3 이라고 둔다

 그림
   T2 --> T1 --> T3 --> T4 (실행 중)
 순환이 없다. 초기 가중치가 모두 1 이면 (L636 의 boost 가 없다고 둔다) schedule_weight 는
   T2 = 1,  T1 = 1 + T2(1) = 2,  T3 = 1 + T1(2) = 3   (L849-L854 가 잎부터 위로 더한다)
   T4 가 푸는 레코드에 T3 말고 가벼운 대기자도 있다면 [11] 은 무게 3 인 T3 을 먼저 본다
```

```text
 schedule_weight (L1362, L607)

 초기 가중치 1. 오래 기다린 대기자는 WEIGHT_BOOST
   기준: 내가 슬롯에 든 뒤 새 예약이 2n 번 이상 있었다 (L634-L638)
 각 노드의 가중치 += 나를 기다리는 노드들의 가중치 (나무를 아래에서 위로 합산)
 결과는 trx->lock.schedule_weight 에 공개되고
   [11] lock_rec_grant_by_heap_no 가 큰 값부터 부여를 검토하는 순서로 쓴다
```

## 결과가 쓰이는 곳

```text
 DB_LOCK_WAIT_TIMEOUT
      --> [08] 에서 깨어난 스레드의 row_mysql_handle_errors 가 문장(또는 트랜잭션)을 롤백
          ER_LOCK_WAIT_TIMEOUT
 outgoing 그래프
      --> [10] 이 순환을 찾는다
 trx->lock.schedule_weight
      --> [11] 의 부여 순서 (CATS, lock0lock.h L130-L137: 많이 막고 있는 트랜잭션 먼저)
```

## 다루지 않는 것

`lock_wait_accumulate_weights` 와 `lock_wait_publish_new_weights` 의 합산 세부(L834, L886), `locksys::run_if_waiting` 의 래치 획득 순서, `lock_wait_table_print` 진단 출력, `innodb_lock_wait_timeout` 이 세션 변수로 읽히는 과정(`trx_lock_wait_timeout_get`)은 이 흐름의 곁가지라 요약만 했다.
