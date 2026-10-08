# RecLock::add_to_waitq

상위: [레코드 잠금과 교착](../README.md)

**충돌한 요청을 "기다리는 잠금"으로 큐 맨 뒤에 세우고, wait-for 그래프에 간선 하나를 긋는다.** 이 함수가 끝나면 세 가지가 바뀌어 있다. 큐에는 `LOCK_WAIT` 비트가 켜진 `lock_t` 가 생기고, 트랜잭션에는 `wait_lock` 과 `blocking_trx` 가 적히고, 질의 스레드는 멈춤 상태가 된다. 정작 잠드는 것은 여기가 아니라 호출 사슬을 거슬러 올라간 [08] 이다.

## 위치

`storage` / `innobase` / `lock` / `lock0lock.cc` L1445-L1478 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0lock.cc#L1445-L1478))

## 실제 코드

`storage` / `innobase` / `lock` / `lock0lock.cc` L1445-L1478 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0lock.cc#L1445-L1478))

```cpp
// lock0lock.cc L1445-L1478
dberr_t RecLock::add_to_waitq(const lock_t *wait_for, const lock_prdt_t *prdt) {
  ut_ad(locksys::owns_page_shard(m_rec_id.get_page_id()));
  ut_ad(m_trx == thr_get_trx(m_thr));

  /* It is not that the body of this function requires trx->mutex, but some of
  the functions it calls require it and it so happens that we always posses it
  so it makes reasoning about code easier if we simply assert this fact. */
  ut_ad(trx_mutex_own(m_trx));

  DEBUG_SYNC_C("rec_lock_add_to_waitq");

  if (m_trx->in_innodb & TRX_FORCE_ROLLBACK) {
    return (DB_DEADLOCK);
  }

  m_mode |= LOCK_WAIT;

  /* Do the preliminary checks, and set query thread state */

  prepare();

  /* Don't queue the lock to hash table, if high priority transaction. */
  lock_t *lock = create(m_trx, prdt);

  lock_create_wait_for_edge(lock, wait_for);

  ut_ad(lock_get_wait(lock));

  set_wait_state(lock);

  MONITOR_INC(MONITOR_LOCKREC_WAIT);

  return (DB_LOCK_WAIT);
}
```

`create` 가 `lock_t` 를 할당하고 `lock_add` 로 큐와 트랜잭션 목록 양쪽에 올린다.

`storage` / `innobase` / `lock` / `lock0lock.cc` L1287-L1327 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0lock.cc#L1287-L1327))

```cpp
// lock0lock.cc L1287-L1327
lock_t *RecLock::create(trx_t *trx, const lock_prdt_t *prdt) {
  ut_ad(locksys::owns_page_shard(m_rec_id.get_page_id()));

  /* Ensure that another transaction doesn't access the trx
  lock state and lock data structures while we are adding the
  lock and changing the transaction state to LOCK_WAIT.
  In particular it protects the lock_alloc which uses trx's private pool of
  lock structures.
  It might be the case that we already hold trx->mutex because we got here from:
    - lock_rec_convert_impl_to_expl_for_trx
    - add_to_waitq
  */
  ut_ad(trx_mutex_own(trx));

  /* Create the explicit lock instance and initialise it. */

  lock_t *lock = lock_alloc(trx, m_index, m_mode, m_rec_id, m_size);

// ... (L1305-L1318 생략: 디버그 빌드에서 DD 테이블에 gap 잠금이 없는지 검사)

  if (prdt != nullptr && (m_mode & LOCK_PREDICATE)) {
    lock_prdt_set_prdt(lock, prdt);
  }

  lock_add(lock);

  return (lock);
}
```

`storage` / `innobase` / `lock` / `lock0lock.cc` L1247-L1280 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0lock.cc#L1247-L1280))

```cpp
// lock0lock.cc L1247-L1280
void RecLock::lock_add(lock_t *lock) {
  ut_ad((lock->type_mode | LOCK_REC) == (m_mode | LOCK_REC));
  ut_ad(m_rec_id.matches(lock));
  ut_ad(locksys::owns_page_shard(m_rec_id.get_page_id()));
  ut_ad(locksys::owns_page_shard(lock->rec_lock.page_id));
  ut_ad(trx_mutex_own(lock->trx));

  bool wait = m_mode & LOCK_WAIT;

  auto &lock_hash = lock_hash_get(m_mode);

  lock->index->table->n_rec_locks.fetch_add(1, std::memory_order_relaxed);

  if (!wait) {
    lock_rec_insert_to_granted(lock_hash, lock, m_rec_id);
  } else {
    lock_rec_insert_to_waiting(lock_hash, lock, m_rec_id);
  }

// ... (L1266-L1273 생략: Performance Schema 용 스레드, 이벤트 id 기록)

  locksys::add_to_trx_locks(lock);

  if (wait) {
    lock_set_lock_and_trx_wait(lock);
  }
}
```

대기 잠금은 큐의 **뒤**에, 부여된 잠금은 **앞**에 넣는다. 큐가 "부여된 것들, 그 다음 기다리는 것들" 순서를 지키는 근거다.

`storage` / `innobase` / `lock` / `lock0lock.cc` L1194-L1214 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0lock.cc#L1194-L1214))

```cpp
// lock0lock.cc L1194-L1214
static void lock_rec_insert_to_waiting(Locks_hashtable &lock_hash, lock_t *lock,
                                       const RecID &rec_id) {
  ut_ad(lock->is_waiting());
  ut_ad(rec_id.matches(lock));
  ut_ad(locksys::owns_page_shard(lock->rec_lock.page_id));
  ut_ad(locksys::owns_page_shard(rec_id.get_page_id()));
  lock_hash.append(lock, rec_id.hash_value());
}

/** Insert lock record to the head of the queue where the GRANTED locks reside.
@param[in,out]  lock_hash       Hash table containing the locks
@param[in,out]  lock            Record lock instance to insert
@param[in]      rec_id          Record being locked */
static void lock_rec_insert_to_granted(Locks_hashtable &lock_hash, lock_t *lock,
                                       const RecID &rec_id) {
  ut_ad(rec_id.matches(lock));
  ut_ad(locksys::owns_page_shard(lock->rec_lock.page_id));
  ut_ad(locksys::owns_page_shard(rec_id.get_page_id()));
  ut_ad(!lock->is_waiting());
  lock_hash.prepend(lock, rec_id.hash_value());
}
```

wait-for 간선은 트랜잭션마다 하나뿐이다. `blocking_trx` 라는 원자 변수 하나가 곧 나가는 간선이다.

`storage` / `innobase` / `lock` / `lock0lock.cc` L1406-L1443 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0lock.cc#L1406-L1443))

```cpp
// lock0lock.cc L1406-L1443
static void lock_create_wait_for_edge(const lock_t *waiting_lock,
                                      const lock_t *blocking_lock) {
  trx_t *waiter = waiting_lock->trx;
  trx_t *blocker = blocking_lock->trx;
  ut_ad(trx_mutex_own(waiter));
  ut_ad(waiter->lock.wait_lock != nullptr);
  ut_ad(locksys::owns_lock_shard(waiter->lock.wait_lock));
  ut_ad(waiter->lock.blocking_trx.load() == nullptr);
  /* We don't call lock_wait_request_check_for_cycles() here as it
  would be slightly premature: the trx is not yet inserted into a slot of
  lock_sys->waiting_threads at this point, and thus it would be invisible to
  the thread which analyzes these slots. What we do instead is to let the
  lock_wait_table_reserve_slot() function be responsible for calling
  lock_wait_request_check_for_cycles() once it insert the trx to a
  slot.*/
  waiter->lock.blocking_trx.store(blocker);
  lock_report_wait_for_edge_to_server(waiting_lock, blocking_lock);
}

/**
Setup the requesting transaction state for lock grant
@param[in,out] lock             Lock for which to change state */
void RecLock::set_wait_state(lock_t *lock) {
  ut_ad(locksys::owns_page_shard(lock->rec_lock.page_id));
  ut_ad(m_trx == lock->trx);
  ut_ad(trx_mutex_own(m_trx));
  ut_ad(lock_get_wait(lock));

  m_trx->lock.wait_started =
      std::chrono::system_clock::from_time_t(time(nullptr));

  m_trx->lock.que_state = TRX_QUE_LOCK_WAIT;

  m_trx->lock.was_chosen_as_deadlock_victim = false;

  bool stopped = que_thr_stop(m_thr);
  ut_a(stopped);
}
```

## 동작 흐름

```text
 [05] L1821  RecLock rec_lock(thr, index, block, heap_no, mode)
 [05] L1823  trx_mutex_enter(trx)

 L1456  이미 강제 롤백 대상(TRX_FORCE_ROLLBACK)이면 -> DB_DEADLOCK
          high priority 트랜잭션이 이 트랜잭션을 희생자로 찍어 둔 경우
 L1460  m_mode |= LOCK_WAIT
 L1464  prepare()                  (L1106)
          que_thr_stop 이 이미 멈춰야 한다고 하면 ut_error
          DDL 트랜잭션이 레코드 잠금을 기다리면 오류 로그 (L1118-L1129)
 L1467  create(m_trx)
          L1303  lock_alloc            lock_t + 비트맵, heap_no 비트만 켠다 (L1181)
          L1324  lock_add
                   L1258  table->n_rec_locks++
                   L1263  wait 이므로 lock_rec_insert_to_waiting -> rec_hash 버킷 끝에 append
                   L1275  add_to_trx_locks   trx->lock.trx_locks 끝에
                   L1278  lock_set_lock_and_trx_wait
                            trx->lock.wait_lock = lock, wait_lock_type = LOCK_REC
 L1469  lock_create_wait_for_edge(lock, wait_for)
          L1421  waiter->lock.blocking_trx = wait_for->trx      간선 waiter -> blocker
          L1422  thd_report_lock_wait 로 서버 계층에 알린다
                 둘 다 복제 적용 워커일 때만 쓰인다 (sql_thd_api.cc L716-L718)
 L1473  set_wait_state(lock)
          L1434  wait_started = 지금
          L1437  que_state = TRX_QUE_LOCK_WAIT
          L1439  was_chosen_as_deadlock_victim = false
          L1441  que_thr_stop(m_thr)   질의 스레드를 멈춤 상태로
 L1477  DB_LOCK_WAIT
```

```text
 add_to_waitq 전후의 모양 (레코드 R 하나의 큐)

 전                                   후
 rec_hash[page_id(R)] 버킷            rec_hash[page_id(R)] 버킷
   T1  X ORDINARY  granted              T1  X ORDINARY  granted
                                        T2  X ORDINARY  WAIT      <- 맨 뒤에 append (L1200)

 T2 의 trx->lock                      T2 의 trx->lock
   wait_lock     = nullptr              wait_lock     = T2 의 새 lock_t
   blocking_trx  = nullptr              blocking_trx  = T1            <- 간선 T2 -> T1
   que_state     = RUNNING              que_state     = TRX_QUE_LOCK_WAIT
```

간선을 긋는 순간에는 교착 검사를 요청하지 않는다. 검사 스레드는 대기 슬롯만 보는데, T2 는 아직 슬롯에 없기 때문이다.

```text
 간선이 검사 스레드에 보이게 되는 순서

 [07] L1421  blocking_trx = T1          간선은 생겼지만 슬롯이 없어 그래프에 안 보인다
             (주석 L1414-L1420)
 [08]        lock_wait_table_reserve_slot
               L188  lock_wait_request_check_for_cycles -> timeout_event 를 set
 [09]        깨어난 검사 스레드가 슬롯을 훑어 T2 -> T1 간선을 읽는다
```

## 결과가 쓰이는 곳

```text
 큐 끝의 WAIT lock_t
      --> [11] 이 잠금이 풀릴 때 이것을 부여할지 판정한다
      --> [09] 가 타임아웃이나 희생자 처리 때 lock_cancel_waiting_and_release 로 걷어낸다
 trx->lock.blocking_trx
      --> [09] 가 그래프의 간선으로 읽는다
      --> 기다리는 이유가 바뀌면 lock_update_wait_for_edge 가 고쳐 쓴다 (L2049-L2055)
 DB_LOCK_WAIT
      --> [05] -> [03] -> [02] -> [01] -> row_search_mvcc -> [08] 로 올라간다
```

## 다루지 않는 것

`lock_alloc` 의 트랜잭션 전용 잠금 풀, high priority 트랜잭션이 대기 대신 상대를 죽이는 경로(`trx_kill_blocking`, `lock_make_trx_hit_list`), `thd_report_lock_wait` 를 받는 서버 쪽(`Commit_order_manager::check_and_report_deadlock`), 테이블 잠금의 대기 큐(`lock_table_enqueue_waiting`)는 이 흐름의 곁가지라 요약만 했다.
