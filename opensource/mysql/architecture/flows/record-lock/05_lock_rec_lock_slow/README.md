# lock_rec_lock_slow

상위: [레코드 잠금과 교착](../README.md)

**레코드 하나의 큐를 직접 훑어 세 가지 중 하나로 결론 낸다.** 이미 충분히 센 잠금을 가졌으면 아무것도 하지 않고, 남의 잠금과 충돌하지 않으면 잠금을 큐에 넣고, 충돌하면 기다리는 잠금을 만들어 [07] 로 넘긴다. 이 함수에서 볼 것은 next-key 요청을 "레코드 잠금 + gap 잠금"으로 쪼개 보는 요령과, `SKIP LOCKED` / `NOWAIT` 가 대기 대신 돌아가는 자리다.

## 위치

`storage` / `innobase` / `lock` / `lock0lock.cc` L1749-L1844 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0lock.cc#L1749-L1844))

## 실제 코드

`storage` / `innobase` / `lock` / `lock0lock.cc` L1749-L1844 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0lock.cc#L1749-L1844))

```cpp
// lock0lock.cc L1749-L1844
static dberr_t lock_rec_lock_slow(bool impl, select_mode sel_mode, ulint mode,
                                  const buf_block_t *block, ulint heap_no,
                                  dict_index_t *index, que_thr_t *thr) {
  // ... (L1752-L1764 생략: ut_ad 로 입력 모드 검사, [03] 과 같은 조건)

  trx_t *trx = thr_get_trx(thr);

  ut_ad(sel_mode == SELECT_ORDINARY ||
        (sel_mode != SELECT_ORDINARY && !trx_is_high_priority(trx)));

  // ... (L1771-L1785 생략: next-key 를 레코드 잠금과 gap 잠금으로 나눠 보는 이유 (아래 그림에 정리))

  auto checked_mode =
      (heap_no != PAGE_HEAP_NO_SUPREMUM && lock_mode_is_next_key_lock(mode))
          ? mode | LOCK_REC_NOT_GAP
          : mode;

  const auto *held_lock = lock_rec_has_expl(checked_mode, block, heap_no, trx);

  if (held_lock != nullptr) {
    if (checked_mode == mode) {
      /* The trx already has a strong enough lock on rec: do nothing */
      return (DB_SUCCESS);
    }

    /* As check_mode != mode, the mode is Next Key Lock, which can not be
    emulated by implicit lock (which are LOCK_REC_NOT_GAP only). */
    ut_ad(!impl);

    lock_reuse_for_next_key_lock(held_lock, mode, block, heap_no, index, trx);
    return (DB_SUCCESS);
  }
  const auto conflicting =
      lock_rec_other_has_conflicting(mode, block, heap_no, trx);

  if (conflicting.wait_for != nullptr) {
    switch (sel_mode) {
      case SELECT_SKIP_LOCKED:
        return (DB_SKIP_LOCKED);
      case SELECT_NOWAIT:
        return (DB_LOCK_NOWAIT);
      case SELECT_ORDINARY:
        /* If another transaction has a non-gap conflicting request in the
        queue, as this transaction does not have a lock strong enough already
        granted on the record, we may have to wait. */

        RecLock rec_lock(thr, index, block, heap_no, mode);

        trx_mutex_enter(trx);

        dberr_t err = rec_lock.add_to_waitq(conflicting.wait_for);

        trx_mutex_exit(trx);

        ut_ad(err == DB_SUCCESS_LOCKED_REC || err == DB_LOCK_WAIT ||
              err == DB_DEADLOCK);
        return (err);
    }
  }
  /* In case we've used a heuristic to bypass a conflicting waiter, we prefer to
  create an explicit lock so it is easier to track the wait-for relation.*/
  if (!impl || conflicting.bypassed) {
    /* Set the requested lock on the record. */

    lock_rec_add_to_queue(LOCK_REC | mode, block, heap_no, index, trx);

    return (DB_SUCCESS_LOCKED_REC);
  }
  return (DB_SUCCESS);
}
```

"이미 가졌나"를 보는 `lock_rec_has_expl` 이다. 큐를 앞에서부터 보다가 **첫 번째 대기 잠금에서 멈춘다.** 부여된 잠금은 언제나 대기 잠금보다 앞에 있기 때문이다.

`storage` / `innobase` / `lock` / `lock0lock.cc` L783-L813 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0lock.cc#L783-L813))

```cpp
// lock0lock.cc L783-L813
static inline const lock_t *lock_rec_has_expl(ulint precise_mode,
                                              const page_id_t page_id,
                                              uint32_t heap_no,
                                              const trx_t *trx) {
  // ... (L787-L794 생략: ut_ad 로 모드 검사)
  const RecID rec_id{page_id, heap_no};
  const bool is_on_supremum = rec_id.is_supremum();
  const bool is_rec_not_gap = 0 != (precise_mode & LOCK_REC_NOT_GAP);
  const bool is_gap = 0 != (precise_mode & LOCK_GAP);
  const auto mode = static_cast<lock_mode>(precise_mode & LOCK_MODE_MASK);
  const auto p_implies_q = [](bool p, bool q) { return q || !p; };
  /* Stop iterating on first matching record or first WAITING lock */
  const auto first =
      lock_sys->rec_hash.find_on_record(rec_id, [&](const lock_t *lock) {
        return (lock->is_waiting() ||
                (lock->trx == trx && !lock->is_insert_intention() &&
                 lock_mode_stronger_or_eq(lock_get_mode(lock), mode) &&
                 (is_on_supremum ||
                  (p_implies_q(lock->is_record_not_gap(), is_rec_not_gap) &&
                   p_implies_q(lock->is_gap(), is_gap)))));
      });
  /* There are no GRANTED locks after the first WAITING lock in the queue. */
  return first == nullptr || first->is_waiting() ? nullptr : first;
}
```

next-key 를 원하는데 레코드 잠금만 가진 경우, 모자란 gap 잠금만 따로 얹는다.

`storage` / `innobase` / `lock` / `lock0lock.cc` L1708-L1731 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0lock.cc#L1708-L1731))

```cpp
// lock0lock.cc L1708-L1731
static void lock_reuse_for_next_key_lock(const lock_t *held_lock, ulint mode,
                                         const buf_block_t *block,
                                         ulint heap_no, dict_index_t *index,
                                         trx_t *trx) {
  ut_ad(mode == LOCK_S || mode == LOCK_X);
  ut_ad(lock_mode_is_next_key_lock(mode));

  if (!held_lock->is_record_not_gap()) {
    ut_ad(held_lock->is_next_key_lock());
    return;
  }

  /* We have a Record Lock granted, so we only need a GAP Lock. We assume
  that GAP Locks do not conflict with anything. Therefore a GAP Lock
  could be granted to us right now if we've requested: */
  mode |= LOCK_GAP;
  ut_ad(nullptr ==
        lock_rec_other_has_conflicting(mode, block, heap_no, trx).wait_for);

  /* It might be the case we already have one, so we first check that. */
  if (lock_rec_has_expl(mode, block, heap_no, trx) == nullptr) {
    lock_rec_add_to_queue(LOCK_REC | mode, block, heap_no, index, trx);
  }
}
```

## 동작 흐름

```text
 L1787  checked_mode 를 정한다
          supremum 이 아니고 요청이 next-key(ORDINARY) 면  mode | REC_NOT_GAP
          아니면                                          mode 그대로
 L1792  held_lock = lock_rec_has_expl(checked_mode, ...)
 L1794  가진 잠금이 있으면
 L1795    checked_mode == mode     -> DB_SUCCESS             이미 충분하다
 L1804    아니면 (next-key 를 원했는데 레코드 잠금을 가졌다)
          lock_reuse_for_next_key_lock
            L1715  가진 것이 이미 next-key 면 그대로 끝
            L1723  아니면 mode | GAP 을 요청한다. gap 잠금은 누구와도 충돌하지 않으므로
            L1729  같은 gap 잠금이 없을 때만 lock_rec_add_to_queue
          -> DB_SUCCESS

 L1807  conflicting = [06] lock_rec_other_has_conflicting(mode, ...)
 L1810  wait_for != nullptr (충돌)
 L1812    SELECT_SKIP_LOCKED  -> DB_SKIP_LOCKED       기다리지 않는다
 L1814    SELECT_NOWAIT       -> DB_LOCK_NOWAIT       기다리지 않는다
 L1816    SELECT_ORDINARY
 L1821      RecLock rec_lock(thr, index, block, heap_no, mode)
 L1823      trx_mutex_enter
 L1825      [07] rec_lock.add_to_waitq(wait_for)   -> DB_LOCK_WAIT (또는 DB_DEADLOCK)

 L1836  충돌 없음
          !impl 이거나 대기자를 앞질렀으면(bypassed)
 L1839      lock_rec_add_to_queue(LOCK_REC | mode, ...)  -> DB_SUCCESS_LOCKED_REC
          impl 이고 앞지르지 않았으면                    -> DB_SUCCESS (암묵 잠금으로 충분)
```

next-key 요청을 둘로 쪼개 보는 이유는 주석 L1771-L1785 에 있다. next-key 가 기다려야 한다면 그건 레코드 쪽 충돌 때문이다. gap 끼리는 충돌하지 않기 때문이다.

```text
 next-key 요청 = 레코드 잠금 + 그 앞 gap 잠금

         gap            레코드 R
   ... (prev) ======== [ R ] ...
        \______________/\___/
          GAP 부분     REC_NOT_GAP 부분
        \____________________/
              ORDINARY (next-key)

 T 가 이미 X|REC_NOT_GAP on R 을 가진 채 X ORDINARY on R 을 요청하면
   L1787  checked_mode = X|REC_NOT_GAP -> L1792 에서 찾는다
   L1804  모자란 것은 GAP 부분뿐 -> X|GAP on R 을 하나 더 얹는다 (L1729)
   남과 충돌할 일이 없으므로 [06] 도 [07] 도 지나지 않는다

 supremum 위의 잠금은 이 쪼개기를 하지 않는다 (L1788)
   supremum 의 잠금은 원래 gap 잠금처럼 다뤄지기 때문 (주석 L1781-L1785)
```

```text
 lock_rec_has_expl 이 "충분히 센" 잠금으로 인정하는 조건 (L804-L809)

 lock->trx == trx                       내 잠금
 !lock->is_insert_intention()           insert intention 은 아무것도 보호하지 않는다
 lock_mode_stronger_or_eq(가진, 원하는)  X 는 S 를 덮는다
 그리고 supremum 이 아니면 정밀 모드도 덮어야 한다
   가진 것이 REC_NOT_GAP 이면 원하는 것도 REC_NOT_GAP 이어야 한다
   가진 것이 GAP 이면 원하는 것도 GAP 이어야 한다
   가진 것이 ORDINARY 면 무엇이든 덮는다

 큐에서 첫 대기 잠금을 만나면 멈추고 nullptr (L804, L812)
```

```text
 bypassed 가 뜻하는 것 (L1834-L1835 주석)

 [06] 이 "기다리는 X 잠금 W 가 앞에 있지만, 나는 이미 W 를 막고 있는 부여된 잠금을 가졌다"
   고 보면 W 를 건너뛴다 (CAN_BYPASS)
 이때는 impl 이라도 명시 잠금을 만든다
   wait-for 관계를 추적하기 쉽게 하려고
```

## 결과가 쓰이는 곳

```text
 DB_SUCCESS / DB_SUCCESS_LOCKED_REC
      --> [03] 을 거쳐 호출자로. 잠금은 lock_rec_add_to_queue 가 같은 페이지의
          비슷한 lock_t 를 찾아 비트만 켜거나(L1558-L1593), 새 lock_t 를 만든다(L1598)
 DB_SKIP_LOCKED / DB_LOCK_NOWAIT
      --> row_search_mvcc 가 다음 레코드로 가거나(SKIP LOCKED) 오류로 끝낸다(NOWAIT)
 DB_LOCK_WAIT
      --> [07] 이 만든 대기 잠금을 남기고 [08] 에서 잠든다
```

## 다루지 않는 것

`lock_rec_add_to_queue` 의 B-tree 재편성 관련 분기(비어 있는 비트맵의 `lock_t` 를 큐 앞으로 옮기는 `lock_rec_move_granted_to_front`), high priority 트랜잭션에 대한 `sel_mode` 제약(L1768)은 이 흐름의 곁가지라 요약만 했다.
