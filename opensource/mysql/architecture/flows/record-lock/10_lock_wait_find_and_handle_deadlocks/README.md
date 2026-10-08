# lock_wait_find_and_handle_deadlocks

상위: [레코드 잠금과 교착](../README.md)

**[09] 가 만든 wait-for 그래프에서 순환을 찾아, 순환마다 희생자 하나를 골라 롤백시킨다.** 그래프는 노드마다 나가는 간선이 많아야 하나라서, 순환 찾기는 "색칠하며 간선을 따라가다 이번 색을 다시 만나면 순환"이라는 단순한 걸음이다. 어려운 쪽은 검증이다. 스냅샷을 찍은 뒤 래치를 모두 놓았기 때문에, 순환이 아직 진짜인지(그 트랜잭션들이 같은 슬롯에서 여전히 기다리는지) 확인한 다음에야 희생자를 고른다.

## 위치

`storage` / `innobase` / `lock` / `lock0wait.cc` L1265-L1316 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0wait.cc#L1265-L1316))

## 실제 코드

`storage` / `innobase` / `lock` / `lock0wait.cc` L1265-L1316 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0wait.cc#L1265-L1316))

```cpp
// lock0wait.cc L1265-L1316
static void lock_wait_find_and_handle_deadlocks(
    const ut::vector<waiting_trx_info_t> &infos,
    const ut::vector<int> &outgoing,
    ut::vector<trx_schedule_weight_t> &new_weights) {
  ut_ad(infos.size() == new_weights.size());
  ut_ad(infos.size() == outgoing.size());
  /** We are going to use int and uint to store positions within infos */
  ut_ad(infos.size() < std::numeric_limits<uint>::max());
  const auto n = static_cast<uint>(infos.size());
  ut_ad(n < static_cast<uint>(std::numeric_limits<int>::max()));
  ut::vector<uint> cycle_ids;
  cycle_ids.clear();
  ut::vector<uint> colors;
  colors.clear();
  colors.resize(n, 0);
  uint current_color = 0;
  for (uint start = 0; start < n; ++start) {
    if (colors[start] != 0) {
      /* This node was already fully processed*/
      continue;
    }
    ++current_color;
    for (int id = start; 0 <= id; id = outgoing[id]) {
      /* We don't expect transaction to deadlock with itself only
      and we do not handle cycles of length=1 correctly */
      ut_ad(id != outgoing[id]);
      if (colors[id] == 0) {
        /* This node was never visited yet */
        colors[id] = current_color;
        continue;
      }
      /* This node was already visited:
      - either it has current_color which means we've visited it during current
        DFS descend, which means we have found a cycle, which we need to verify,
      - or, it has a color used in a previous DFS which means that current DFS
        path merges into an already processed portion of wait-for graph, so we
        can stop now */
      if (colors[id] == current_color) {
        /* found a candidate cycle! */
        lock_wait_extract_cycle_ids(cycle_ids, id, outgoing);
        if (lock_wait_check_candidate_cycle(cycle_ids, infos, new_weights)) {
          MONITOR_INC(MONITOR_DEADLOCK);
        } else {
          MONITOR_INC(MONITOR_DEADLOCK_FALSE_POSITIVES);
        }
      }
      break;
    }
  }
  MONITOR_INC(MONITOR_DEADLOCK_ROUNDS);
  MONITOR_SET(MONITOR_LOCK_THREADS_WAITING, n);
}
```

순환 후보를 검증하고 처리한다. 두 단계로 확인한다.

`storage` / `innobase` / `lock` / `lock0wait.cc` L1164-L1231 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0wait.cc#L1164-L1231))

```cpp
// lock0wait.cc L1164-L1231
static bool lock_wait_check_candidate_cycle(
    ut::vector<uint> &cycle_ids, const ut::vector<waiting_trx_info_t> &infos,
    ut::vector<trx_schedule_weight_t> &new_weights) {
  ut_ad(!lock_wait_mutex_own());
  ut_ad(!locksys::owns_exclusive_global_latch());
  lock_wait_mutex_enter();
  // ... (L1170-L1183 생략: 포인터가 아직 같은 trx 를 가리키는지 reservation_no 로 확인하는 이유)
  if (!lock_wait_trxs_are_still_in_slots(cycle_ids, infos)) {
    lock_wait_mutex_exit();
    return false;
  }
  // ... (L1188-L1205 생략: 슬롯에 있어도 이미 깨우기로 결정된 trx 를 wait_lock 으로 거르는 이유)
  locksys::Global_exclusive_latch_guard gurad{UT_LOCATION_HERE};
  if (!lock_wait_trxs_are_still_waiting(cycle_ids, infos)) {
    lock_wait_mutex_exit();
    return false;
  }

  // ... (L1212-L1221 생략: lock_wait_mutex 를 먼저 놓아도 되는 이유)

  lock_wait_mutex_exit();

  trx_t *const chosen_victim = lock_wait_choose_victim(cycle_ids, infos);
  ut_a(chosen_victim);

  lock_wait_handle_deadlock(chosen_victim, cycle_ids, infos, new_weights);

  return true;
}
```

희생자 고르기다. 순환을 "가장 늦게 들어온 대기자"가 끝에 오도록 돌린 뒤, 앞에서부터 가벼운 쪽을 남긴다.

`storage` / `innobase` / `lock` / `lock0wait.cc` L917-L958 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0wait.cc#L917-L958))

```cpp
// lock0wait.cc L917-L958
static trx_t *lock_wait_choose_victim(
    const ut::vector<uint> &cycle_ids,
    const ut::vector<waiting_trx_info_t> &infos) {
  // ... (L920-L924 생략: 전역 배타 래치가 필요한 이유)
  ut_ad(locksys::owns_exclusive_global_latch());
  ut_ad(!cycle_ids.empty());
  trx_t *chosen_victim = nullptr;
  auto sorted_trxs = lock_wait_order_for_choosing_victim(cycle_ids, infos);

  for (auto *trx : sorted_trxs) {
    if (chosen_victim == nullptr) {
      chosen_victim = trx;
      continue;
    }

    if (trx_is_high_priority(chosen_victim) || trx_is_high_priority(trx)) {
      auto victim = trx_arbitrate(trx, chosen_victim);

      if (victim != nullptr) {
        if (victim == trx) {
          chosen_victim = trx;
        } else {
          ut_a(victim == chosen_victim);
        }
        continue;
      }
    }

    if (trx_weight_ge(chosen_victim, trx)) {
      /* The joining transaction is 'smaller',
      choose it as the victim and roll it back. */
      chosen_victim = trx;
    }
  }

  ut_a(chosen_victim);
  return chosen_victim;
}
```

"가볍다"의 정의는 고친 행 수(undo 수) + 가진 잠금 수다. 비트랜잭션 테이블을 고친 쪽은 무겁게 친다.

`storage` / `innobase` / `trx` / `trx0trx.cc` L2871-L2895 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0trx.cc#L2871-L2895))

```cpp
// trx0trx.cc L2871-L2895
bool trx_weight_ge(const trx_t *a, /*!< in: transaction to be compared */
                   const trx_t *b) /*!< in: transaction to be compared */
{
  /* To read TRX_WEIGHT we need a exclusive global lock_sys latch */
  ut_ad(locksys::owns_exclusive_global_latch());

  /* If mysql_thd is NULL for a transaction we assume that it has
  not edited non-transactional tables. */

  auto a_notrans_edit =
      a->mysql_thd != nullptr && thd_has_edited_nontrans_tables(a->mysql_thd);

  auto b_notrans_edit =
      b->mysql_thd != nullptr && thd_has_edited_nontrans_tables(b->mysql_thd);

  if (a_notrans_edit != b_notrans_edit) {
    return (a_notrans_edit);
  }

  /* Either both had edited non-transactional tables or both had
  not, we fall back to comparing the number of altered/locked
  rows. */

  return (TRX_WEIGHT(a) >= TRX_WEIGHT(b));
}
```

`storage` / `innobase` / `include` / `trx0trx.h` L1248-L1254 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/trx0trx.h#L1248-L1254))

```cpp
// trx0trx.h L1248-L1254
/** Calculates the "weight" of a transaction. The weight of one transaction
 is estimated as the number of altered rows + the number of locked rows.
 @param t transaction
 @return transaction weight */
static inline uint64_t TRX_WEIGHT(const trx_t *t) {
  return t->undo_no + UT_LIST_GET_LEN(t->lock.trx_locks);
}
```

희생자에게 표시를 하고 대기를 취소한다. 깨어난 희생자는 [08] 에서 `DB_DEADLOCK` 을 보고 트랜잭션 전체를 롤백한다.

`storage` / `innobase` / `lock` / `lock0wait.cc` L1132-L1147 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0wait.cc#L1132-L1147))

```cpp
// lock0wait.cc L1132-L1147
static void lock_wait_handle_deadlock(
    trx_t *chosen_victim, const ut::vector<uint> &cycle_ids,
    const ut::vector<waiting_trx_info_t> &infos,
    ut::vector<trx_schedule_weight_t> &new_weights) {
  // ... (L1136-L1139 생략: 가중치 갱신 이유)
  lock_wait_update_weights_on_cycle(chosen_victim, cycle_ids, infos,
                                    new_weights);

  lock_notify_about_deadlock(
      lock_wait_trxs_rotated_for_notification(cycle_ids, infos), chosen_victim);

  lock_wait_rollback_deadlock_victim(chosen_victim);
}
```

`storage` / `innobase` / `lock` / `lock0wait.cc` L692-L703 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0wait.cc#L692-L703))

```cpp
// lock0wait.cc L692-L703
static void lock_wait_rollback_deadlock_victim(trx_t *chosen_victim) {
  ut_ad(!trx_mutex_own(chosen_victim));
  /* We need to latch the shard containing wait_lock to read it and access
  the lock itself.*/
  ut_ad(locksys::owns_exclusive_global_latch());
  trx_mutex_enter(chosen_victim);
  chosen_victim->lock.was_chosen_as_deadlock_victim = true;
  ut_a(chosen_victim->lock.wait_lock != nullptr);
  ut_a(chosen_victim->lock.que_state == TRX_QUE_LOCK_WAIT);
  lock_cancel_waiting_and_release(chosen_victim);
  trx_mutex_exit(chosen_victim);
}
```

## 동작 흐름

```text
 L1279  colors[n] = 0                 0 = 아직 안 가 본 노드
 L1281  for start in 0..n-1
 L1282    이미 칠한 노드면 건너뛴다
 L1286    ++current_color             이번 걸음의 색
 L1287    for (id = start; id >= 0; id = outgoing[id])     간선을 따라간다
 L1291      처음 보는 노드 -> 이번 색으로 칠하고 계속
 L1302      이번 색을 다시 만났다 -> 순환 후보
 L1304        lock_wait_extract_cycle_ids        id 에서 출발해 다시 id 까지
 L1305        lock_wait_check_candidate_cycle
                진짜면 MONITOR_DEADLOCK, 아니면 MONITOR_DEADLOCK_FALSE_POSITIVES
 L1311      이전 색을 만났거나 순환을 처리했으면 이번 걸음 끝
```

노드마다 나가는 간선이 하나뿐이라 걸음은 갈래 없이 한 줄로 간다. 그래서 각 노드는 한 번만 칠해지고, 전체가 O(n) 이다.

```text
 색칠 예 (outgoing: 0->1, 1->2, 2->0, 3->1, 4->-1)

 start 0  색 1   0(칠) -> 1(칠) -> 2(칠) -> 0 은 색 1  => 순환 [0 1 2]
 start 1  이미 칠함, 건너뜀
 start 2  이미 칠함, 건너뜀
 start 3  색 2   3(칠) -> 1 은 색 1 (이전 걸음)        => 기존 부분에 합류, 끝
 start 4  색 3   4(칠) -> -1                           => 기다리지 않음, 끝

 그림
   T3 --> T1 --> T2
           ^      |
           |      v
           +----- T0          (T4 는 혼자)
```

```text
 lock_wait_check_candidate_cycle 의 두 단계 검증

 1단계  lock_wait_mutex 아래 (L1169)
 L1184    lock_wait_trxs_are_still_in_slots
            각 슬롯의 reservation_no 가 스냅샷 때와 같은가
            다르면 그 슬롯의 주인이 바뀌었다 (trx_t 는 재사용되므로 포인터만으론 모른다)
 2단계  전역 배타 래치 (L1206)
 L1207    lock_wait_trxs_are_still_waiting
            각 trx 의 wait_lock 이 아직 nullptr 이 아닌가
            슬롯에 있어도 이미 부여나 취소로 깨우기 직전일 수 있다
 L1223  lock_wait_mutex 를 놓는다 (배타 래치가 trx 를 붙잡아 둔다)
 L1225  lock_wait_choose_victim
 L1228  lock_wait_handle_deadlock
          L1140  순환 위 trx 들의 schedule_weight 갱신
          L1143  lock_notify_about_deadlock      SHOW ENGINE INNODB STATUS 의 LATEST DETECTED DEADLOCK
          L1146  lock_wait_rollback_deadlock_victim
                   L698  was_chosen_as_deadlock_victim = true
                   L701  lock_cancel_waiting_and_release -> 대기 잠금 제거, 스레드 깨움
```

```text
 희생자 고르기 (lock_wait_choose_victim)

 L928   lock_wait_order_for_choosing_victim (L776)
          reservation_no 가 가장 큰 trx(가장 늦게 기다리기 시작, 순환을 닫은 쪽) 를 찾아
          그 다음 자리부터 시작하도록 돌린다 -> 늦게 들어온 trx 가 맨 끝
 L930   앞에서부터 하나씩
 L936     어느 쪽이 high priority 면 trx_arbitrate 로 가른다
 L949     trx_weight_ge(지금 후보, trx) 면 trx 를 새 후보로
            같으면 뒤쪽으로 바뀐다 -> 동률이면 순환을 닫은 trx 가 희생된다

 예) 순환 T0 -> T1 -> T2 -> T0, reservation_no T0=5 T1=8 T2=11
     돌린 순서: T0, T1, T2       (T2 가 가장 늦다)
     TRX_WEIGHT  T0=40  T1=3  T2=3
       후보 T0 -> T1 (40 >= 3) -> T2 (3 >= 3) => 희생자 T2
```

```text
 희생자가 된 뒤 (시간 순)

 검사 스레드                               희생자 T2 의 스레드
 L698  was_chosen_as_deadlock_victim
 L701  lock_cancel_waiting_and_release
         T2 의 WAIT 잠금을 큐에서 뺀다
         뒤 대기자 부여 검토 (T1 은 여전히 T2 를 기다린다. 순환만 끊겼다)
         lock_wait_release_thread_if_suspended
           L410 error_state = DB_DEADLOCK
           L416 os_event_set  ---------------->  [08] L297 에서 깨어난다
                                                 L341 DB_DEADLOCK
                                                 row_mysql_handle_errors L728
                                                   trx_rollback_to_savepoint(trx, nullptr)
                                                   전체 롤백 -> T2 의 잠금이 모두 풀린다
                                                 -> ER_LOCK_DEADLOCK
```

## 결과가 쓰이는 곳

```text
 희생자의 DB_DEADLOCK
      --> 트랜잭션 전체 롤백. 그 롤백이 잠금을 풀면 [11] 이 순환의 나머지를 깨운다
 lock_notify_about_deadlock
      --> SHOW ENGINE INNODB STATUS, innodb_print_all_deadlocks 면 에러 로그에도 (lock0lock.cc L5989)
 MONITOR_DEADLOCK / MONITOR_DEADLOCK_FALSE_POSITIVES
      --> INNODB_METRICS 의 lock_deadlocks, lock_deadlock_false_positives (srv0mon.cc L126-L129)
```

## 다루지 않는 것

`innodb_deadlock_detect=OFF` 일 때(탐지 없이 타임아웃에만 기댄다, [09] L1423), `trx_arbitrate` 의 high priority 규칙, `lock_notify_about_deadlock` 의 출력 형식, 순환 위 가중치를 경로로 펴서 다시 계산하는 `lock_wait_update_weights_on_cycle`(L1078), 테이블 잠금이 낀 교착은 이 흐름의 곁가지라 요약만 했다.
