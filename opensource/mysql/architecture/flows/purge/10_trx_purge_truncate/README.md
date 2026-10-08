# trx_purge_truncate

상위: [purge](../README.md)

**purge 가 다 처리한 undo 로그를 history list 에서 떼어 내고, 커진 undo 테이블스페이스를 통째로 잘라내는 두 단계의 입구다.** 첫 단계 `trx_purge_truncate_history` 는 모든 롤백 세그먼트를 돌며 history 의 뒤(가장 오래된 커밋)부터 로그 헤더를 읽고, 커밋 번호가 잘라낼 경계보다 작으면 history 에서 뗀다. 그 로그가 세그먼트의 마지막 로그이고 세그먼트가 재사용 대상이 아니면(`TRX_UNDO_TO_PURGE`) 세그먼트를 통째로 해제한다. 경계는 [05] 가 실제로 처리한 위치(`purge_sys->limit` 또는 `iter`)이고, 그것도 [04] 의 `m_lowest_needed_trx_no` 를 넘지 못한다. 둘째 단계 `trx_purge_truncate_undo_spaces` 는 크기가 `innodb_max_undo_log_size` 를 넘은 undo 테이블스페이스 하나를 골라 비활성으로 표시하고(새 트랜잭션이 그 안의 롤백 세그먼트를 받지 않게), 안의 롤백 세그먼트가 모두 비면 파일을 새 space id 로 다시 만든다. [02] 가 `innodb_purge_rseg_truncate_frequency` 번째 배치마다, 그리고 종료 중일 때 이 단계를 켠다.

## 위치

`storage` / `innobase` / `trx` / `trx0purge.cc` L2381-L2392 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0purge.cc#L2381-L2392))

## 실제 코드

입구다. 배치에서 `limit` 이 정해지지 않았으면 `iter` 를 경계로 쓴다.

`storage` / `innobase` / `trx` / `trx0purge.cc` L2380-L2392 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0purge.cc#L2380-L2392))

```cpp
// trx0purge.cc L2380-L2392
/** Remove old historical changes from the rollback segments. */
static void trx_purge_truncate(void) {
  ut_ad(trx_purge_check_limit());

  if (purge_sys->limit.trx_no == 0) {
    trx_purge_truncate_history(&purge_sys->iter);
  } else {
    trx_purge_truncate_history(&purge_sys->limit);
  }

  /* Attempt to truncate an undo tablespace. */
  trx_purge_truncate_undo_spaces();
}
```

첫 단계다. 경계를 `m_lowest_needed_trx_no` 이하로 깎고, 모든 undo 테이블스페이스의 롤백 세그먼트와 임시 롤백 세그먼트를 돈다. 이미 비어서 잘라내기를 기다리는 공간은 건너뛴다.

`storage` / `innobase` / `trx` / `trx0purge.cc` L1612-L1669 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0purge.cc#L1612-L1669))

```cpp
// trx0purge.cc L1612-L1669
/** Removes unnecessary history data from rollback segments.
NOTE that when this function is called, the caller must not
have any latches on undo log pages!
@param[in]  limit  Truncate limit
*/
static void trx_purge_truncate_history(purge_iter_t *limit) {
  MONITOR_INC_VALUE(MONITOR_PURGE_TRUNCATE_HISTORY_COUNT, 1);

  auto counter_time_truncate_history = std::chrono::steady_clock::now();
  const auto lowest_needed_trx_no = purge_sys->m_lowest_needed_trx_no;
  /* We play safe and set the truncate limit at most to the purge view
  low_limit number, though this is not necessary */

  if (limit->trx_no >= lowest_needed_trx_no) {
    limit->trx_no = lowest_needed_trx_no;
    limit->undo_no = 0;
    limit->undo_rseg_space = SPACE_UNKNOWN;
  }

  ut_ad(limit->trx_no <= lowest_needed_trx_no);

  /* Purge rollback segments in all undo tablespaces.  This may take
  some time and we do not want an undo DDL to attempt an x_lock during
  this time.  If it did, all other transactions seeking a short s_lock()
  would line up behind it.  So get the ddl_mutex before this s_lock(). */
  mutex_enter(&undo::ddl_mutex);
  undo::spaces->s_lock();
  for (auto undo_space : undo::spaces->m_spaces) {
    /* Skip undo tablespace that is already empty and marked for truncation. */
    undo::Truncate &ut = purge_sys->undo_trunc;

    if (ut.is_equal(undo_space->id()) && ut.is_marked() &&
        ut.is_marked_space_empty()) {
      continue;
    }

    /* Purge rollback segments in this undo tablespace. */
    undo_space->rsegs()->s_lock();

    for (auto rseg : *undo_space->rsegs()) {
      trx_purge_truncate_rseg_history(rseg, limit);
    }
    undo_space->rsegs()->s_unlock();
  }

  undo::spaces->s_unlock();
  mutex_exit(&undo::ddl_mutex);

  /* Purge rollback segments in the temporary tablespace. */
  trx_sys->tmp_rsegs.s_lock();
  for (auto rseg : trx_sys->tmp_rsegs) {
    trx_purge_truncate_rseg_history(rseg, limit);
  }
  trx_sys->tmp_rsegs.s_unlock();

  MONITOR_INC_TIME(MONITOR_PURGE_TRUNCATE_HISTORY_MICROSECOND,
                   counter_time_truncate_history);
}
```

롤백 세그먼트 하나의 history 를 뒤에서부터 잘라내는 루프다.

`storage` / `innobase` / `trx` / `trx0purge.cc` L537-L635 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0purge.cc#L537-L635))

```cpp
// trx0purge.cc L537-L635
/** Removes unnecessary history data from a rollback segment. */
static void trx_purge_truncate_rseg_history(
    trx_rseg_t *rseg,          /*!< in: rollback segment */
    const purge_iter_t *limit) /*!< in: truncate offset */
{
  // ... (L542-L549 생략: 지역 변수 선언)
  const bool is_temp = fsp_is_system_temporary(rseg->space_id);

  mtr_start(&mtr);

  if (is_temp) {
    mtr.set_log_mode(MTR_LOG_NO_REDO);
  }

  rseg->latch();

  rseg_hdr =
      trx_rsegf_get(rseg->space_id, rseg->page_no, rseg->page_size, &mtr);

  hdr_addr = trx_purge_get_log_from_hist(
      flst_get_last(rseg_hdr + TRX_RSEG_HISTORY, &mtr));
loop:
  if (hdr_addr.page == FIL_NULL) {
    rseg->unlatch();
    mtr_commit(&mtr);

    return;
  }

  undo_page = trx_undo_page_get(page_id_t(rseg->space_id, hdr_addr.page),
                                rseg->page_size, &mtr);

  log_hdr = undo_page + hdr_addr.boffset;

  undo_trx_no = mach_read_from_8(log_hdr + TRX_UNDO_TRX_NO);

  if (undo_trx_no >= limit->trx_no) {
    /* limit space_id should match the rollback segment
    space id to avoid freeing if the page belongs to a
    different rollback segment for the same trx_no. */
    if (undo_trx_no == limit->trx_no &&
        rseg->space_id == limit->undo_rseg_space) {
      trx_undo_truncate_start(rseg, hdr_addr.page, hdr_addr.boffset,
                              limit->undo_no);
    }

    rseg->unlatch();
    mtr_commit(&mtr);

    return;
  }

  prev_hdr_addr = trx_purge_get_log_from_hist(
      flst_get_prev_addr(log_hdr + TRX_UNDO_HISTORY_NODE, &mtr));

  seg_hdr = undo_page + TRX_UNDO_SEG_HDR;

  if ((mach_read_from_2(seg_hdr + TRX_UNDO_STATE) == TRX_UNDO_TO_PURGE) &&
      (mach_read_from_2(log_hdr + TRX_UNDO_NEXT_LOG) == 0)) {
    /* We can free the whole log segment */

    rseg->unlatch();
    mtr_commit(&mtr);

    /* calls the trx_purge_remove_log_hdr()
    inside trx_purge_free_segment(). */
    trx_purge_free_segment(rseg, hdr_addr, is_temp);

  } else {
    /* Remove the log hdr from the rseg history. */

    trx_purge_remove_log_hdr(rseg_hdr, log_hdr, &mtr);

    rseg->unlatch();
    mtr_commit(&mtr);
  }

  mtr_start(&mtr);

  if (is_temp) {
    mtr.set_log_mode(MTR_LOG_NO_REDO);
  }

  rseg->latch();

  rseg_hdr =
      trx_rsegf_get(rseg->space_id, rseg->page_no, rseg->page_size, &mtr);

  hdr_addr = prev_hdr_addr;

  goto loop;
}
```

둘째 단계다. 표시, 비었는지 확인, 실제 잘라내기 셋 중 하나라도 지금 안 되면 다음 기회로 미룬다.

`storage` / `innobase` / `trx` / `trx0purge.cc` L1671-L1704 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0purge.cc#L1671-L1704))

```cpp
// trx0purge.cc L1671-L1704
/** Select an undo tablespace to truncate, make sure it is empty of undo logs,
then finally truncate it. */
static void trx_purge_truncate_undo_spaces() {
  auto &undo_trunc = purge_sys->undo_trunc;

  /* Truncate as many undo spaces as can be truncated.
  Break the loop and return whenever the process cannot be completed. */
  for (size_t i = 0; i < undo::spaces->size(); ++i) {
    /* Check current activity and if conditions allow, mark the undo space that
    needs to be truncated. */
    if (!trx_purge_mark_undo_for_truncate(i)) {
      break; /* No truncation is needed at this time. */
    }

    /* A space was marked but may not be yet empty. */
    ut_a(undo_trunc.is_marked());

    /* If any undo logs need to be purged from this marked space, try again
    later. */
    if (!trx_purge_check_if_marked_undo_is_empty()) {
      break;
    }

    /* A space has been marked and is now empty. */
    ut_a(undo_trunc.is_marked_space_empty());

    /* Truncate the marked space. */
    if (!trx_purge_truncate_marked_undo()) {
      /* If the marked and empty space did not get truncated due to a concurrent
      clone or something else, try again later. */
      break;
    }
  }
}
```

잘라낼 대상인지 정하는 기준이다. 이미 비활성이면 바로 대상이고, 아니면 파일 크기가 `innodb_max_undo_log_size` 와 처음 크기 중 큰 쪽을 넘을 때 대상이다.

`storage` / `innobase` / `trx` / `trx0purge.cc` L761-L799 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0purge.cc#L761-L799))

```cpp
// trx0purge.cc L761-L799
bool Tablespace::needs_truncation() {
  /* If it is already inactive, even implicitly, then proceed. */
  m_rsegs->s_lock();
  if (m_rsegs->is_inactive_implicit() || m_rsegs->is_inactive_explicit()) {
    m_rsegs->s_unlock();
    return (true);
  }

  /* If implicit undo truncation is turned off, or if the rsegs don't exist
  yet, don't bother checking the size. */
  if (!srv_undo_log_truncate || m_rsegs == nullptr || m_rsegs->is_empty() ||
      m_rsegs->is_init()) {
    m_rsegs->s_unlock();
    return (false);
  }
  ut_ad(m_rsegs->is_active());
  m_rsegs->s_unlock();

  /* Check if undo truncation is happening so often that too many pages
  from old space IDs are still in memory. Since undo spaces are deleted
  with BUF_REMOVE_NONE, the actual space is not deleted for that old
  space ID until all pages have been passively removed from the buffer
  pool. */
  auto count = fil_count_undo_deleted(undo::id2num(m_id));
  if (count > CONCURRENT_UNDO_TRUNCATE_LIMIT) {
    ib::warn(ER_IB_MSG_UNDO_TRUNCATE_TOO_OFTEN);
    return (false);
  }

  ut_ad(fil_space_get_undo_initial_size(m_id) != 0);

  page_no_t trunc_size = std::max(
      static_cast<page_no_t>(srv_max_undo_tablespace_size / srv_page_size),
      fil_space_get_undo_initial_size(m_id));

  if (fil_space_get_size(m_id) > trunc_size) {
    return (true);
  }

```

## 동작 흐름

```text
 trx_purge_truncate (L2381)
 L2384  limit.trx_no == 0 ?  trx_purge_truncate_history(&iter) : (&limit)
 L2391  trx_purge_truncate_undo_spaces()

 trx_purge_truncate_history(limit)  (L1617)
 L1625  limit.trx_no >= m_lowest_needed_trx_no 면 그 값으로 깎는다
 L1637  undo::ddl_mutex, undo::spaces s_lock           (undo 테이블스페이스 DDL 과 겹치지 않게)
 L1639  undo 테이블스페이스마다
 L1643    표시됐고 이미 비었으면 건너뛴다
 L1652    롤백 세그먼트마다 trx_purge_truncate_rseg_history(rseg, limit)
 L1661  임시 롤백 세그먼트도 같은 일 (redo 없이)

 trx_purge_truncate_rseg_history(rseg, limit)  (L538)
 L564   hdr_addr = history 의 last (가장 오래된 로그)
 L565 loop:
 L566   끝이면 return
 L578   undo_trx_no = 로그 헤더의 TRX_UNDO_TRX_NO
 L580   undo_trx_no >= limit.trx_no -> 여기서 멈춘다
          같은 번호이고 같은 공간이면 trx_undo_truncate_start 로 로그 앞부분만 잘라낸다
 L597   prev = 한 칸 앞 (더 최근 커밋)
 L601   세그먼트 상태 TO_PURGE 이고 이 로그가 세그먼트의 마지막 (NEXT_LOG == 0)
 L610     trx_purge_free_segment            세그먼트 통째로 해제 (history 에서도 뗀다)
        아니면
 L615     trx_purge_remove_log_hdr          history 에서만 뗀다 (rseg_history_len--)
 L632   hdr_addr = prev, goto loop
```

경계 앞뒤에서 history 가 어떻게 줄어드는지 그림으로 보자.

```text
 rseg 하나의 history (last 가 오른쪽)

 처리 전   first [900] [870] [760] [640] [600] [580] [520] [500] last
 limit.trx_no = 600   (purge 가 600 직전까지 처리했다. m_lowest_needed_trx_no 는 그 이상)

 루프      500 < 600  떼기      (세그먼트가 TO_PURGE 이고 마지막 로그면 세그먼트 해제)
           520 < 600  떼기
           580 < 600  떼기
           600 >= 600 멈춤      (같은 번호, 같은 공간이면 앞부분만 trx_undo_truncate_start)

 처리 후   first [900] [870] [760] [640] [600] last        rseg_history_len -= 3
```

undo 테이블스페이스 잘라내기는 여러 배치에 걸친 상태 기계다. 한 번에 끝나지 않으면 표시만 남기고 다음 배치에서 이어 간다.

```text
 undo 테이블스페이스 하나의 잘라내기 (trx_purge_truncate_undo_spaces, L1673)

 active
   |  needs_truncation: 파일 크기 > max(innodb_max_undo_log_size, 처음 크기)  (L792-L797)
   |  innodb_undo_log_truncate = OFF 면 대상이 아니다                          (L771)
   v
 trx_purge_mark_undo_for_truncate (L1236)
   undo::Truncate::mark -> set_inactive_implicit     새 트랜잭션은 이 공간의 rseg 를 받지 않는다
   v
 trx_purge_check_if_marked_undo_is_empty (L1356)
   rseg 마다 trx_ref_count == 0 이고 last_page_no == FIL_NULL (history 가 비었다) 인가
   아니면 break -> 다음 배치에서 다시 본다 (그 사이 purge 가 history 를 비운다)
   v
 trx_purge_truncate_marked_undo (L1533)
   MDL 획득, clone 확인, undo::ddl_mutex
   trx_purge_truncate_marked_undo_low
     undo::start_logging (L1439)          잘라내기 시작을 기록
     빠른 종료 중이면 여기서 멈춘다. 주석: 시작 시 fixup 이 마저 한다 (L1449)
     trx_undo_truncate_tablespace (L1475) 주석: marked space 의 space_id 가 바뀐다 (L1474)
     암묵 비활성이었으면 다시 active, SET INACTIVE 였으면 empty
   undo::done_logging, 데이터 사전에 새 space id 와 상태 기록
   v
 active (작아진 파일)
```

## 결과가 쓰이는 곳

```text
 history 에서 떼어 낸 로그
      --> rseg_history_len 이 준다 ([02] 의 스레드 수 조절, [03] 의 DML 지연)
 해제된 undo 세그먼트
      --> 롤백 세그먼트의 빈 슬롯이 되어 새 트랜잭션의 undo 가 쓴다
 잘라낸 undo 테이블스페이스
      --> 디스크 공간이 돌아온다. 옛 space id 의 페이지는 버퍼 풀에서 수동적으로 밀려날 때까지
          남는다. 그래서 잘라내기가 너무 잦으면 건너뛴다 (needs_truncation 의 주석 L779-L783)
```

## 다루지 않는 것

세그먼트 해제의 세부(`trx_purge_free_segment` 가 페이지를 몇 번에 나눠 돌려주는지), 로그 앞부분 잘라내기(`trx_undo_truncate_start`), 잘라내기 로그 파일(`undo::start_logging`, `undo::done_logging`)과 시작 시 복구, `ALTER UNDO TABLESPACE ... SET INACTIVE` 와 `DROP UNDO TABLESPACE` 의 DDL 쪽, clone 과의 조정(`Clone_notify`), 너무 잦은 잘라내기를 막는 `CONCURRENT_UNDO_TRUNCATE_LIMIT` 는 이 흐름의 곁가지라 줄만 적었다. undo 테이블스페이스와 롤백 세그먼트의 배치는 [undo 테이블스페이스와 롤백 세그먼트](../../../structure/undo-segments/README.md)에 둔다.
