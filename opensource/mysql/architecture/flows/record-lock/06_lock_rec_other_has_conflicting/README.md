# lock_rec_other_has_conflicting

상위: [레코드 잠금과 교착](../README.md)

**한 레코드의 큐를 앞에서부터 훑어, 내 요청이 기다려야 할 첫 번째 잠금을 찾는다.** 판정은 한 쌍씩 `rec_lock_check_conflict` 가 한다. 판정은 두 단계다. 먼저 모드(S/X) 호환 행렬을 보고, 모드가 충돌할 때만 gap, next-key, insert intention 의 규칙을 적용한다. 이 규칙들이 "gap 끼리는 서로 막지 않는다, gap 잠금은 insert intention 만 막는다"는 InnoDB 레코드 잠금의 성격을 만든다.

## 위치

`storage` / `innobase` / `lock` / `lock0lock.cc` L903-L925 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0lock.cc#L903-L925))

## 실제 코드

`storage` / `innobase` / `lock` / `lock0lock.cc` L903-L925 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0lock.cc#L903-L925))

```cpp
// lock0lock.cc L903-L925
static locksys::Conflicting lock_rec_other_has_conflicting(
    ulint mode, const buf_block_t *block, ulint heap_no, const trx_t *trx) {
  ut_ad(locksys::owns_page_shard(block->get_page_id()));
  ut_ad(!(mode & ~(ulint)(LOCK_MODE_MASK | LOCK_GAP | LOCK_REC_NOT_GAP |
                          LOCK_INSERT_INTENTION)));
  ut_ad(!(mode & LOCK_PREDICATE));
  ut_ad(!(mode & LOCK_PRDT_PAGE));
  bool bypassed{false};

  RecID rec_id{block, heap_no};
  const bool is_supremum = rec_id.is_supremum();
  locksys::Trx_locks_cache trx_locks_cache{};
  const lock_t *wait_for =
      lock_sys->rec_hash.find_on_record(rec_id, [&](const lock_t *lock) {
        const auto conflict = locksys::rec_lock_check_conflict(
            trx, mode, lock, is_supremum, trx_locks_cache);
        if (conflict == locksys::Conflict::CAN_BYPASS) {
          bypassed = true;
        }
        return conflict == locksys::Conflict::HAS_TO_WAIT;
      });
  return {wait_for, bypassed};
}
```

한 쌍의 판정이다. 위에서부터 걸리는 첫 `return` 이 답이다.

`storage` / `innobase` / `lock` / `lock0lock.cc` L554-L645 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0lock.cc#L554-L645))

```cpp
// lock0lock.cc L554-L645
static inline Conflict rec_lock_check_conflict(const trx_t *trx,
                                               ulint type_mode,
                                               const lock_t *lock2,
                                               bool lock_is_on_supremum,
                                               Trx_locks_cache &trx_locks_cache)

{
  // ... (L561-L562 생략: ut_ad)

  if (trx == lock2->trx ||
      lock_mode_compatible(static_cast<lock_mode>(LOCK_MODE_MASK & type_mode),
                           lock_get_mode(lock2))) {
    return Conflict::NO_CONFLICT;
  }

  const bool is_hp = trx_is_high_priority(trx);
  /* If our trx is High Priority and the existing lock is WAITING and not
      high priority, then we can ignore it. */
  if (is_hp && lock2->is_waiting() && !trx_is_high_priority(lock2->trx)) {
    return Conflict::NO_CONFLICT;
  }

  /* We have somewhat complex rules when gap type record locks
  cause waits */

  if ((lock_is_on_supremum || (type_mode & LOCK_GAP)) &&
      !(type_mode & LOCK_INSERT_INTENTION)) {
    /* Gap type locks without LOCK_INSERT_INTENTION flag
    do not need to wait for anything. This is because
    different users can have conflicting lock types
    on gaps. */

    return Conflict::NO_CONFLICT;
  }

  if (!(type_mode & LOCK_INSERT_INTENTION) && lock_rec_get_gap(lock2)) {
    /* Record lock (LOCK_ORDINARY or LOCK_REC_NOT_GAP
    does not need to wait for a gap type lock */

    return Conflict::NO_CONFLICT;
  }

  if ((type_mode & LOCK_GAP) && lock_rec_get_rec_not_gap(lock2)) {
    /* Lock on gap does not need to wait for
    a LOCK_REC_NOT_GAP type lock */

    return Conflict::NO_CONFLICT;
  }

  if (lock_rec_get_insert_intention(lock2)) {
    /* No lock request needs to wait for an insert
    intention lock to be removed. This is ok since our
    rules allow conflicting locks on gaps. This eliminates
    a spurious deadlock caused by a next-key lock waiting
    for an insert intention lock; when the insert
    intention lock was granted, the insert deadlocked on
    the waiting next-key lock.

    Also, insert intention locks do not disturb each
    other. */

    return Conflict::NO_CONFLICT;
  }

  /* This is very important that LOCK_INSERT_INTENTION should not overtake a
  WAITING Gap or Next-Key lock on the same heap_no, because the following
  insertion of the record would split the gap duplicating the waiting lock,
  violating the rule that a transaction can have at most one waiting lock. */
  if (!(type_mode & LOCK_INSERT_INTENTION) && lock2->is_waiting() &&
      lock2->mode() == LOCK_X && (type_mode & LOCK_MODE_MASK) == LOCK_X) {
    // We would've already returned false if it was a gap lock.
    ut_ad(!(type_mode & LOCK_GAP));
    // Similarly, since locks on supremum are either LOCK_INSERT_INTENTION or
    // gap locks, we would've already returned false if it's about supremum.
    ut_ad(!lock_is_on_supremum);
    // If lock2 was a gap lock (in particular: insert intention), it could
    // only block LOCK_INSERT_INTENTION, which we've ruled out.
    ut_ad(!lock_rec_get_gap(lock2));
    // So, both locks are REC_NOT_GAP or Next-Key locks
    ut_ad(lock2->is_record_not_gap() || lock2->is_next_key_lock());
    ut_ad((type_mode & LOCK_REC_NOT_GAP) ||
          lock_mode_is_next_key_lock(type_mode));
    /* In this case, we should ignore lock2, if trx already has a GRANTED lock
    blocking lock2 from being granted. */
    if (trx_locks_cache.has_granted_blocker(trx, lock2)) {
      return Conflict::CAN_BYPASS;
    }
  }

  return Conflict::HAS_TO_WAIT;
}
```

모드 호환 행렬은 다섯 모드(IS, IX, S, X, AUTO_INC)의 표다. 레코드 잠금에는 S 와 X 만 쓴다.

`storage` / `innobase` / `include` / `lock0priv.h` L593-L599 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/lock0priv.h#L593-L599))

```cpp
// lock0priv.h L593-L599
static const byte lock_compatibility_matrix[5][5] = {
    /**         IS     IX       S     X       AI */
    /* IS */ {true, true, true, false, true},
    /* IX */ {true, true, false, false, true},
    /* S  */ {true, false, true, false, false},
    /* X  */ {false, false, false, false, false},
    /* AI */ {true, true, false, false, false}};
```

## 동작 흐름

```text
 L912   rec_id = (page_id, heap_no)
 L913   supremum 인지 본다 (supremum 위의 요청은 gap 요청으로 친다)
 L916   rec_hash.find_on_record(rec_id, 람다)
          이 레코드의 비트가 켜진 lock_t 들을 큐 순서대로 (부여된 것 먼저, 기다리는 것 뒤)
 L917     rec_lock_check_conflict(trx, mode, lock, is_supremum, cache)
 L919     CAN_BYPASS 면 bypassed = true 로 적고 계속
 L922     HAS_TO_WAIT 면 멈춘다 -> wait_for = 그 잠금
 L924   {wait_for, bypassed} 를 돌려준다
```

판정의 순서를 그대로 세우면 아래와 같다. 줄 번호는 `rec_lock_check_conflict` 의 `return` 자리다.

```text
 rec_lock_check_conflict(내 요청 type_mode, 큐의 잠금 lock2)

 L564  lock2 가 내 것이거나 모드가 호환(S 와 S)                   -> NO_CONFLICT
 L573  내가 high priority 이고 lock2 는 기다리는 보통 트랜잭션     -> NO_CONFLICT
 ----- 여기부터는 모드가 충돌한다 (S-X, X-S, X-X) -----
 L580  내 요청이 gap(또는 supremum) 이고 insert intention 이 아니다 -> NO_CONFLICT
 L590  내 요청이 insert intention 이 아니고 lock2 가 gap           -> NO_CONFLICT
 L597  내 요청이 gap 이고 lock2 가 REC_NOT_GAP                     -> NO_CONFLICT
 L604  lock2 가 insert intention                                   -> NO_CONFLICT
 L623  내 요청이 X 레코드 잠금, lock2 가 기다리는 X 레코드 잠금
 L639    그리고 내가 lock2 를 막는 부여된 잠금을 이미 가졌다       -> CAN_BYPASS
 L644  그 밖                                                        -> HAS_TO_WAIT
```

모드가 충돌할 때 정밀 모드끼리의 관계를 표로 펼치면 다음과 같다. 행이 새 요청, 열이 큐에 이미 있는 잠금이다. W 는 기다린다, `.` 는 기다리지 않는다.

```text
 레코드 잠금 호환 행렬 (모드가 충돌할 때, rec_lock_check_conflict 기준)

 요청 \ 큐에 있는   GAP   REC_NOT_GAP   ORDINARY   INSERT_INTENTION
 GAP                .     .             .          .                 L580
 REC_NOT_GAP        .     W             W          .                 L590 (II 는 GAP 비트도 켠다, L5106)
 ORDINARY           .     W             W          .                 L590 (II 는 GAP 비트도 켠다, L5106)
 INSERT_INTENTION   W     .             W          .                 L597, L604

 모드 행렬 (lock0priv.h L593, 레코드에 쓰이는 부분)
          S     X
   S      ok    W
   X      W     W
 S 와 S 는 정밀 모드와 무관하게 늘 통과한다 (L564)
```

```text
 표를 읽는 법

 GAP 행이 모두 .
   gap 잠금은 "이 gap 에 아무도 넣지 마라"는 뜻일 뿐, 서로 배타적이지 않다
   두 트랜잭션이 같은 gap 에 X|GAP 을 동시에 가질 수 있다 (주석 L582-L585)
 GAP 열은 INSERT_INTENTION 행만 W
   gap 잠금이 막는 것은 삽입뿐이다
 INSERT_INTENTION 열이 모두 .
   삽입하려고 기다리는 표시는 아무도 막지 않는다
   next-key 가 insert intention 을 기다리다 생기는 가짜 교착을 없애려고 (주석 L605-L611)
 INSERT_INTENTION 행의 REC_NOT_GAP 은 .
   레코드만 잠긴 것은 그 앞 gap 에 넣는 것을 막지 않는다 (L597)
```

마지막 규칙은 공정성 규칙이다. 기다리는 X 잠금 뒤에 새 X 요청이 오면 기본은 줄을 서는 것이다. 단 새 요청자가 그 대기자를 이미 막고 있다면 줄을 서는 것이 오히려 교착이 된다.

```text
 CAN_BYPASS (L623-L641)

 큐:  T1  S REC_NOT_GAP  granted
      T2  X REC_NOT_GAP  waiting   (T1 을 기다림)
 T1 이 같은 레코드에 X REC_NOT_GAP 을 요청하면 (S -> X 올리기)
   [05] L1792  가진 S 는 X 를 덮지 못하므로 lock_rec_has_expl 은 nullptr
   L623  lock2 = T2 는 기다리는 X, 내 요청도 X 레코드 잠금
   L639  T1 의 S 가 T2 를 막고 있다 (has_granted_blocker) -> CAN_BYPASS
         줄을 섰다면 T1 은 T2 를, T2 는 T1 을 기다리는 순환이 된다
   큐의 T1 자신의 S 는 L564 에서 통과 -> 기다릴 것 없음
   [05] L1836  bypassed 이므로 X 잠금을 큐에 넣는다

 insert intention 은 건너뛸 수 없다 (L623 의 조건, lock_rec_insert_check_and_lock L5115 의 ut_a)
   삽입이 gap 을 둘로 쪼개면 기다리는 잠금이 둘로 복제되어
   "트랜잭션당 대기 잠금은 하나" 규칙이 깨지기 때문 (주석 L619-L622)
```

## 결과가 쓰이는 곳

```text
 wait_for
      --> [05] 가 nullptr 이 아니면 sel_mode 에 따라 SKIP/NOWAIT/대기로 가른다
      --> [07] 이 이 잠금의 trx 를 wait-for 간선의 끝(blocking_trx)으로 삼는다
 bypassed
      --> [05] 가 true 면 impl 이라도 명시 잠금을 만든다 (L1836)
 rec_lock_check_conflict
      --> 같은 규칙이 대기 잠금을 다시 볼 때도 쓰인다
          rec_lock_has_to_wait (L654) -> lock_rec_has_to_wait_in_queue (L1905)
          [11] 이 부여 여부를 정할 때의 lock_has_to_wait 도 이것을 거친다 (L673)
```

## 다루지 않는 것

`Trx_locks_cache::has_granted_blocker` 의 캐시 구조(L820), 테이블 잠금의 판정(`has_to_wait` 의 L676, 의도 잠금 IS/IX), 공간 인덱스의 `lock_prdt_has_to_wait`, high priority 트랜잭션 규칙은 이 흐름의 곁가지라 요약만 했다.
