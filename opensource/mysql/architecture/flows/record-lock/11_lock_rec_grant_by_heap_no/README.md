# lock_rec_grant_by_heap_no

상위: [레코드 잠금과 교착](../README.md)

**잠금이 풀린 레코드 하나의 큐에서, 풀린 트랜잭션 때문에 기다리던 잠금들을 골라 부여하고 그 스레드를 깨운다.** 이 흐름의 마지막 단계이고, 실행하는 것은 잠금을 푸는 쪽(커밋이나 롤백하는 트랜잭션, 또는 대기를 취소하는 [09] [10])의 스레드다. 부여 순서는 큐에 선 순서가 아니다. high priority 트랜잭션이 먼저이고, 그 다음은 [09] 가 매긴 `schedule_weight` 가 큰 순서다.

## 위치

`storage` / `innobase` / `lock` / `lock0lock.cc` L2115-L2231 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0lock.cc#L2115-L2231))

## 실제 코드

커밋이 잠금을 푸는 입구다. 이 트랜잭션이 아직 참조 중이면([02] 의 암묵 잠금 변환) 기다렸다가, 잠금 목록을 끝에서부터 하나씩 푼다.

`storage` / `innobase` / `lock` / `lock0lock.cc` L5815-L5845 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0lock.cc#L5815-L5845))

```cpp
// lock0lock.cc L5815-L5845
void lock_trx_release_locks(trx_t *trx) /*!< in/out: transaction */
{
  DEBUG_SYNC_C("before_lock_trx_release_locks");

  trx_mutex_enter(trx);

  check_trx_state(trx);
  ut_ad(trx_state_eq(trx, TRX_STATE_COMMITTED_IN_MEMORY));
  ut_ad(!trx->in_rw_trx_list);

  if (trx_is_referenced(trx)) {
    while (trx_is_referenced(trx)) {
      trx_mutex_exit(trx);

      DEBUG_SYNC_C("waiting_trx_is_not_referenced");

      /** Doing an implicit to explicit conversion
      should not be expensive. */
      ut_delay(ut::random_from_interval_fast(0, srv_spin_wait_delay));

      trx_mutex_enter(trx);
    }
  }

  ut_ad(!trx_is_referenced(trx));
  trx_mutex_exit(trx);

  while (!locksys::try_release_all_locks(trx)) {
    std::this_thread::yield();
  }

```

`storage` / `innobase` / `lock` / `lock0lock.cc` L4144-L4164 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0lock.cc#L4144-L4164))

```cpp
// lock0lock.cc L4144-L4164
  trx_mutex_enter(trx);

  ut_ad(trx->lock.wait_lock == nullptr);
  while ((lock = UT_LIST_GET_LAST(trx->lock.trx_locks)) != nullptr) {
    /* Following call temporarily releases trx->mutex */
    try_relatch_trx_and_shard_and_do(lock, [=]() {
      if (lock_get_type_low(lock) == LOCK_REC) {
        lock_rec_dequeue_from_page(lock);
      } else {
        lock_table_dequeue(lock);
      }
    });
    if (shared_latch_guard.is_x_blocked_by_us()) {
      trx_mutex_exit(trx);
      return false;
    }
  }

  trx_mutex_exit(trx);
  return true;
}
```

레코드 잠금 하나(`lock_t`, 비트맵 전체)를 큐에서 빼고, 켜져 있던 비트마다 부여를 검토한다.

`storage` / `innobase` / `lock` / `lock0lock.cc` L2311-L2314 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0lock.cc#L2311-L2314))

```cpp
// lock0lock.cc L2311-L2314
static void lock_rec_dequeue_from_page(lock_t *in_lock) {
  lock_rec_discard(in_lock);
  lock_rec_grant(in_lock);
}
```

`storage` / `innobase` / `lock` / `lock0lock.cc` L2274-L2301 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0lock.cc#L2274-L2301))

```cpp
// lock0lock.cc L2274-L2301
static void lock_rec_grant(lock_t *in_lock) {
  const auto page_id = in_lock->rec_lock.page_id;

  // ... (L2277-L2287 생략: 대기자가 하나도 없으면 비트를 훑지 않는 이유)

  if (in_lock->hash_table().find_on_page(
          page_id, [](lock_t *lock) { return lock->is_waiting(); })) {
    mon_type_t grant_attempts = 0;
    for (ulint heap_no = 0; heap_no < lock_rec_get_n_bits(in_lock); ++heap_no) {
      if (lock_rec_get_nth_bit(in_lock, heap_no)) {
        lock_rec_grant_by_heap_no(in_lock, heap_no);
        ++grant_attempts;
      }
    }
    MONITOR_INC_VALUE(MONITOR_RECLOCK_GRANT_ATTEMPTS, grant_attempts);
  }
  MONITOR_INC(MONITOR_RECLOCK_RELEASE_ATTEMPTS);
}
```

본체다. 큐를 네 묶음으로 나누고, 순서를 정해 하나씩 부여를 시도한다.

`storage` / `innobase` / `lock` / `lock0lock.cc` L2115-L2231 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0lock.cc#L2115-L2231))

```cpp
// lock0lock.cc L2115-L2231
static void lock_rec_grant_by_heap_no(lock_t *in_lock, ulint heap_no) {
  ut_ad(in_lock->is_record_lock());
  ut_ad(locksys::owns_page_shard(in_lock->rec_lock.page_id));

  using LockDescriptorEx = std::pair<trx_schedule_weight_t, lock_t *>;
  /* Preallocate for 4 lists with 32 locks. */
  Scoped_heap heap((sizeof(lock_t *) * 3 + sizeof(LockDescriptorEx)) * 32,
                   UT_LOCATION_HERE);

  RecID rec_id{in_lock, heap_no};
  Locks<lock_t *> low_priority_light{heap.get()};
  Locks<lock_t *> waiting{heap.get()};
  Locks<lock_t *> granted{heap.get()};
  Locks<LockDescriptorEx> low_priority_heavier{heap.get()};

  const auto in_trx = in_lock->trx;
#ifdef UNIV_DEBUG
  bool seen_waiting_lock = false;
#endif
  in_lock->hash_table().find_on_record(rec_id, [&](lock_t *lock) {
    /* Split the relevant locks in the queue into:
    - granted = granted locks
    - waiting = waiting locks of high priority transactions
    - low_priority_heavier = waiting locks of low priority, but heavy weight
    - low_priority_light = waiting locks of low priority and light weight
    */
    if (!lock->is_waiting()) {
      /* Granted locks should be before waiting locks. */
      ut_ad(!seen_waiting_lock);
      granted.push_back(lock);
      return false;
    }
    ut_d(seen_waiting_lock = true);
    const auto trx = lock->trx;
    if (trx->error_state == DB_DEADLOCK ||
        trx->lock.was_chosen_as_deadlock_victim) {
      return false;
    }
    // ... (L2153-L2156 생략: blocking_trx 를 relaxed 로 읽어도 되는 이유)
    const auto blocking_trx =
        trx->lock.blocking_trx.load(std::memory_order_relaxed);
    /* No one should be WAITING without good reason! */
    ut_ad(blocking_trx);
    /* We will only consider granting the `lock`, if we are the reason it
    was waiting. */
    if (blocking_trx != in_trx) {
      return false;
    }
    if (trx_is_high_priority(trx)) {
      waiting.push_back(lock);
      return false;
    }
    // ... (L2170-L2176 생략: schedule_weight 를 스냅샷하는 이유)
    const auto schedule_weight =
        trx->lock.schedule_weight.load(std::memory_order_relaxed);
    if (schedule_weight <= 1) {
      low_priority_light.push_back(lock);
      return false;
    }
    low_priority_heavier.push_back(LockDescriptorEx{schedule_weight, lock});

    return false;
  });

  if (waiting.empty() && low_priority_light.empty() &&
      low_priority_heavier.empty()) {
    /* Nothing to grant. */
    return;
  }
  /* We want high schedule weight to be in front, and break ties by position */
  std::stable_sort(low_priority_heavier.begin(), low_priority_heavier.end(),
                   [](const LockDescriptorEx &a, const LockDescriptorEx &b) {
                     return (a.first > b.first);
                   });
  for (const auto &descriptor : low_priority_heavier) {
    waiting.push_back(descriptor.second);
  }
  waiting.insert(waiting.end(), low_priority_light.begin(),
                 low_priority_light.end());

  /* New granted locks will be added from this index. */
  const auto new_granted_index = granted.size();

  granted.reserve(granted.size() + waiting.size());

  for (lock_t *wait_lock : waiting) {
    /* Check if the transactions in the waiting queue have
    to wait for locks granted above. If they don't have to
    wait then grant them the locks and add them to the granted
    queue. */

    /* We don't expect to be a waiting trx, and we can't grant to ourselves as
    that would require entering trx->mutex while holding in_trx->mutex. */
    ut_ad(wait_lock->trx != in_trx);

    const lock_t *blocking_lock =
        lock_rec_has_to_wait_for_granted(wait_lock, granted, new_granted_index);
    if (blocking_lock == nullptr) {
      lock_grant(wait_lock);

      lock_rec_move_granted_to_front(wait_lock, rec_id);

      granted.push_back(wait_lock);
    } else {
      lock_update_wait_for_edge(wait_lock, blocking_lock);
    }
  }
}
```

부여할 수 있는지는 "이미 부여된 잠금들과 충돌하는가"로만 본다. 새로 부여한 잠금도 판정 대상에 들어간다.

`storage` / `innobase` / `lock` / `lock0lock.cc` L2066-L2100 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0lock.cc#L2066-L2100))

```cpp
// lock0lock.cc L2066-L2100
static const lock_t *lock_rec_has_to_wait_for_granted(
    const typename Container::value_type &wait_lock, const Container &granted,
    const size_t new_granted_index)

{
  ut_ad(locksys::owns_page_shard(wait_lock->rec_lock.page_id));
  ut_ad(wait_lock->is_record_lock());

  ut_ad(new_granted_index <= granted.size());

  // ... (L2076-L2081 생략: 오래된 부여부터 보는 이유)
  for (size_t i = new_granted_index; i--;) {
    const auto granted_lock = granted[i];
    if (lock_has_to_wait(wait_lock, granted_lock)) {
      return (granted_lock);
    }
  }

  for (size_t i = new_granted_index; i < granted.size(); ++i) {
    const auto granted_lock = granted[i];
    ut_ad(granted_lock->trx->error_state != DB_DEADLOCK);
    ut_ad(!granted_lock->trx->lock.was_chosen_as_deadlock_victim);

    if (lock_has_to_wait(wait_lock, granted_lock)) {
      return (granted_lock);
    }
  }

  return (nullptr);
}
```

부여는 `LOCK_WAIT` 를 지우고 잠든 스레드를 깨우는 것이다.

`storage` / `innobase` / `lock` / `lock0lock.cc` L1930-L1957 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0lock.cc#L1930-L1957))

```cpp
// lock0lock.cc L1930-L1957
static void lock_grant(lock_t *lock) {
  ut_ad(locksys::owns_lock_shard(lock));
  ut_ad(!trx_mutex_own(lock->trx));

  trx_mutex_enter(lock->trx);

  // ... (L1936-L1948 생략: AUTO_INC 테이블 잠금 처리)

  DBUG_PRINT("ib_lock", ("wait for trx " TRX_ID_FMT " ends",
                         trx_get_id_for_print(lock->trx)));

  lock_reset_wait_and_release_thread_if_suspended(lock);
  ut_ad(trx_mutex_own(lock->trx));

  trx_mutex_exit(lock->trx);
}
```

## 동작 흐름

```text
 trx_release_impl_and_expl_locks (trx0trx.cc L1931)
   lock_trx_release_locks
     L5825  참조 카운트가 0 이 될 때까지 돈다 ([02] 의 암묵 -> 명시 변환이 끝나기를)
     L5842  try_release_all_locks
              L4147  trx_locks 의 끝에서부터
              L4151    lock_rec_dequeue_from_page(lock)
                         L2312  lock_rec_discard   rec_hash 와 trx_locks 에서 뺀다
                         L2313  lock_rec_grant
                                  L2289  이 페이지에 대기 잠금이 하나라도 있으면
                                  L2292  켜진 heap_no 마다
                                  L2294    lock_rec_grant_by_heap_no(in_lock, heap_no)
```

```text
 lock_rec_grant_by_heap_no(in_lock, heap_no)

 L2134  find_on_record 로 이 레코드의 큐를 훑으며 네 묶음으로 나눈다
          부여된 잠금                               -> granted
          희생자이거나 DB_DEADLOCK 인 대기          -> 건너뜀
          blocking_trx 가 in_lock->trx 가 아닌 대기 -> 건너뜀 (L2163, 내가 막던 것만 본다)
          high priority 대기                        -> waiting
          schedule_weight <= 1                      -> low_priority_light
          그 밖                                     -> low_priority_heavier
 L2188  셋 다 비었으면 끝
 L2194  heavier 를 weight 내림차순 stable_sort (동률은 큐 순서)
 L2198  waiting = high priority + heavier + light
 L2209  waiting 의 각 대기 잠금 W 에 대해
 L2220    lock_rec_has_to_wait_for_granted(W, granted, ...)
            granted 중 W 가 기다려야 할 잠금이 있나 ([06] 의 규칙, L2084 lock_has_to_wait)
 L2222    없으면 lock_grant(W)
            L1953  lock_reset_wait_and_release_thread_if_suspended -> 스레드를 깨운다
 L2224      W 를 큐 앞(부여된 쪽)으로 옮긴다
 L2226      granted 에 W 를 더한다 -> 뒤의 대기자는 W 와도 충돌을 본다
 L2228    있으면 lock_update_wait_for_edge(W, 막는 잠금)
            기다리는 이유가 바뀌었으면 blocking_trx 를 고치고 [09] 를 깨운다
```

아래는 레코드 R 하나에서 S 잠금 둘과 X 잠금 하나가 기다리다가, 쥐고 있던 X 가 커밋으로 풀리는 장면이다.

```text
 커밋이 R 의 큐를 바꾸는 과정

 전 (T1 이 X 를 쥐고, 셋이 T1 을 기다린다)
   T1  X REC_NOT_GAP  granted
   T2  S REC_NOT_GAP  WAIT   blocking_trx=T1  weight 1
   T3  X REC_NOT_GAP  WAIT   blocking_trx=T1  weight 5   (T3 이 쥔 다른 잠금을 넷이 기다린다)
   T4  S REC_NOT_GAP  WAIT   blocking_trx=T1  weight 1

 T1 COMMIT -> lock_rec_discard 로 T1 의 lock_t 가 빠진다
   granted = []
   waiting 순서 = heavier[T3] + light[T2, T4]

 L2209  T3  granted 와 충돌 없음        -> 부여, 깨움       granted=[T3]
 L2209  T2  T3 의 X 와 충돌             -> blocking_trx=T3 (간선 T2 -> T3)
 L2209  T4  T3 의 X 와 충돌             -> blocking_trx=T3

 후
   T3  X REC_NOT_GAP  granted
   T2  S REC_NOT_GAP  WAIT   blocking_trx=T3
   T4  S REC_NOT_GAP  WAIT   blocking_trx=T3

 큐 순서대로 부여했다면 T2 의 S 가 먼저 부여되고, T3 과 T3 을 기다리는 넷이 계속 기다렸다
```

## 결과가 쓰이는 곳

```text
 부여된 잠금
      --> 깨어난 스레드가 [08] 에서 돌아와 row_search_mvcc 가 같은 레코드를 다시 찾는다
          다시 잠그면 이번에는 [05] 의 lock_rec_has_expl 이 방금 부여된 잠금을 찾는다
 바뀐 blocking_trx
      --> [09] 가 다음 바퀴에 새 간선으로 그래프를 만든다
 lock_rec_dequeue_from_page
      --> 같은 함수가 대기 취소(lock_cancel_waiting_and_release L5748)에서도 불린다
          그래서 타임아웃이나 교착 희생자의 대기 잠금이 빠질 때도 뒤 대기자가 부여를 받는다
```

## 다루지 않는 것

`try_relatch_trx_and_shard_and_do` 의 래치 재획득 순서, 전역 배타 래치 요청이 있을 때 물러나는 `is_x_blocked_by_us`(L4156), READ COMMITTED 의 `lock_trx_release_read_locks`(prepare 때 gap 잠금을 먼저 푸는 경로), 테이블 잠금 해제(`lock_table_dequeue`), B-tree 재편성 때의 잠금 이동은 이 흐름의 곁가지라 요약만 했다.
