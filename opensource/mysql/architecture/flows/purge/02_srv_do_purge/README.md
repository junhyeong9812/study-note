# srv_do_purge

상위: [purge](../README.md)

**purge 배치를 연달아 돌리면서, history 길이를 보고 이번 배치에 쓸 스레드 수를 하나씩 올리거나 내리는 자리다.** 설정한 `innodb_purge_threads` 는 상한일 뿐이다. history 가 직전보다 길어졌거나 `innodb_max_purge_lag` 를 넘었으면 하나 늘리고, 길이가 그대로인데 서버에 다른 활동이 있었으면 하나 줄인다. 주석은 이것을 "purge 가 따라가지 못할 때만 추가 스레드를 쓴다"고 설명한다. 루프는 history 가 비거나, 배치가 0 페이지를 처리하거나(잘라낼 undo 테이블스페이스도 없으면), purge 가 멈추거나 종료할 때 끝난다. 몇 번째 배치마다 [10] truncate 를 할지도 여기서 정한다.

## 위치

`storage` / `innobase` / `srv` / `srv0srv.cc` L2845-L2920 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/srv/srv0srv.cc#L2845-L2920))

## 실제 코드

함수 전체다. `count`, `n_use_threads`, `rseg_history_len` 이 `static` 이라서 호출 사이에 값이 남는다.

`storage` / `innobase` / `srv` / `srv0srv.cc` L2842-L2920 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/srv/srv0srv.cc#L2842-L2920))

```cpp
// srv0srv.cc L2842-L2920
/** Do the actual purge operation.
@param[in,out]  n_total_purged  Total pages purged in this call
@return length of history list before the last purge batch. */
static ulint srv_do_purge(ulint *n_total_purged) {
  ulint n_pages_purged;

  static ulint count = 0;
  static ulint n_use_threads = 0;
  static uint64_t rseg_history_len = 0;
  ulint old_activity_count = srv_get_activity_count();
  bool need_explicit_truncate = false;

  const auto n_threads = srv_threads.m_purge_workers_n;

  ut_a(n_threads > 0);
  ut_ad(!srv_read_only_mode);

  /* Purge until there are no more records to purge and there is
  no change in configuration or server state. If the user has
  configured more than one purge thread then we treat that as a
  pool of threads and only use the extra threads if purge can't
  keep up with updates. */

  if (n_use_threads == 0) {
    n_use_threads = n_threads;
  }

  do {
    if (trx_sys->rseg_history_len.load() > rseg_history_len ||
        (srv_max_purge_lag > 0 && rseg_history_len > srv_max_purge_lag)) {
      /* History length is now longer than what it was
      when we took the last snapshot. Use more threads. */

      if (n_use_threads < n_threads) {
        ++n_use_threads;
      }

    } else if (srv_check_activity(old_activity_count) && n_use_threads > 1) {
      /* History length same or smaller since last snapshot,
      use fewer threads. */

      --n_use_threads;

      old_activity_count = srv_get_activity_count();
    }

    /* Ensure that the purge threads are less than what
    was configured. */

    ut_a(n_use_threads > 0);
    ut_a(n_use_threads <= n_threads);

    /* Take a snapshot of the history list before purge. */
    if ((rseg_history_len = trx_sys->rseg_history_len.load()) == 0) {
      break;
    }

    bool do_truncate = need_explicit_truncate ||
                       srv_shutdown_state.load() == SRV_SHUTDOWN_PURGE ||
                       (++count % srv_purge_rseg_truncate_frequency) == 0;

    n_pages_purged =
        trx_purge(n_use_threads, srv_purge_batch_size, do_truncate);

    *n_total_purged += n_pages_purged;

    need_explicit_truncate = (n_pages_purged == 0);
    if (need_explicit_truncate) {
      undo::spaces->s_lock();
      need_explicit_truncate =
          (undo::spaces->find_first_inactive_explicit(nullptr) != nullptr);
      undo::spaces->s_unlock();
    }
  } while (purge_sys->state == PURGE_STATE_RUN &&
           (n_pages_purged > 0 || need_explicit_truncate) &&
           !srv_purge_should_exit(n_pages_purged));

  return rseg_history_len;
}
```

## 동작 흐름

```text
 srv_do_purge(&n_total_purged)

 L2848  static count, n_use_threads, rseg_history_len   (호출 사이에 유지)
 L2854  n_threads = srv_threads.m_purge_workers_n         (= innodb_purge_threads, srv0srv.cc L1115)
 L2866  처음이면 n_use_threads = n_threads

 L2869  do
 L2870    history 가 직전 스냅샷보다 길다
            또는 max_purge_lag > 0 이고 직전 길이가 그것을 넘었다
            -> n_use_threads++ (상한 n_threads)
 L2879    아니면 서버 활동이 있었고 n_use_threads > 1   -> n_use_threads--
 L2895    rseg_history_len = 지금 길이.  0 이면 break
 L2899    do_truncate = 직전에 명시적 truncate 가 필요했거나
                        종료 단계(SRV_SHUTDOWN_PURGE)이거나
                        ++count % innodb_purge_rseg_truncate_frequency == 0
 L2904    n_pages_purged = [03] trx_purge(n_use_threads, srv_purge_batch_size, do_truncate)
 L2906    n_total_purged += n_pages_purged
 L2908    0 페이지였으면 SET INACTIVE 된 undo 테이블스페이스가 남았는지 본다
 L2915  while (state == RUN 이고 (처리한 페이지가 있거나 명시적 truncate 가 남았고)
               종료해야 하는 상황이 아니다)

 L2919  return rseg_history_len   (마지막 배치 직전의 길이)
```

스레드 수가 배치마다 어떻게 움직이는지 예로 보자. `innodb_purge_threads=4`, 서버는 계속 쓰기를 받는다.

```text
 배치   직전 길이   지금 길이   판단                     n_use_threads
 1      0           8000        늘었다                   4 (처음엔 n_threads 로 시작, 상한)
 2      8000        9500        늘었다                   4
 3      9500        6000        줄었다 + 활동 있음        3
 4      6000        2000        줄었다 + 활동 있음        2
 5      2000        2100        늘었다                   3
 6      2100        0           줄었다 + 활동 있음        2, 그다음 길이 0 이라 break (L2895)

 n_use_threads 는 [03] 이 레코드를 몇 그룹으로 나눌지, 몇 개를 워커 큐에 넣을지가 된다
 1 이면 코디네이터 혼자 처리한다 (워커 큐에 넣는 개수 = n - 1 = 0)
```

```text
 truncate 를 하는 배치 (L2899-L2901)

 count 는 static. innodb_purge_rseg_truncate_frequency 번째 배치마다 한 번
   + 종료 중이면 매번
   + 직전 배치가 0 페이지인데 ALTER UNDO TABLESPACE ... SET INACTIVE 된 공간이 남았으면
     (need_explicit_truncate, L2908-L2914) 페이지가 없어도 루프를 한 번 더 돈다
 truncate 한 번은 모든 undo 테이블스페이스의 모든 rseg 를 훑는다 ([10])
```

## 결과가 쓰이는 곳

```text
 반환값 (rseg_history_len)   --> [01] 이 다음 suspend 에서 "그새 늘었나" 비교
 n_total_purged              --> [01] 이 0 이면 잠든다
 n_use_threads (static)      --> 다음 호출의 시작 값
```

## 다루지 않는 것

서버 활동 계수(`srv_get_activity_count`, `srv_check_activity`)가 무엇을 세는지, 명시적으로 비활성화한 undo 테이블스페이스 찾기(`find_first_inactive_explicit`)의 세부는 이 흐름의 곁가지라 줄만 적었다.
