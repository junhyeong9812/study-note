# mtr_t::Command::add_dirty_blocks_to_flush_list

상위: [mini-transaction과 redo 기록](../README.md)

**mtr 이 X 또는 SX 래치로 잡은 페이지에 lsn 을 찍고, 처음 더럽혀진 페이지만 flush list 의 머리에 붙인다.** 페이지마다 `newest_modification = end_lsn` 은 매번 갱신하고, `oldest_modification = start_lsn` 은 처음 한 번만 정한다. flush list 에 붙는 순서가 lsn 순서와 어긋날 수 있는데, 그 어긋남의 상한을 `buf_flush_list_added` 가 `order_lag()` 로 묶는다. 이 함수 앞뒤의 `wait_to_add` 와 `report_added` 는 [04] execute 가 부른다.

## 위치

`storage` / `innobase` / `mtr` / `mtr0mtr.cc` L828-L836 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/mtr/mtr0mtr.cc#L828-L836))

## 실제 코드

`storage` / `innobase` / `mtr` / `mtr0mtr.cc` L828-L836 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/mtr/mtr0mtr.cc#L828-L836))

```cpp
// mtr0mtr.cc L828-L836
void mtr_t::Command::add_dirty_blocks_to_flush_list(lsn_t start_lsn,
                                                    lsn_t end_lsn) {
  Add_dirty_blocks_to_flush_list add_to_flush(start_lsn, end_lsn,
                                              m_impl->m_flush_observer);

  Iterate<Add_dirty_blocks_to_flush_list> iterator(add_to_flush);

  m_impl->m_memo.for_each_block_in_reverse(iterator);
}
```

m_memo 를 역순으로 돌며 슬롯마다 부르는 함수 객체다. 수정 가능한 래치(X_FIX, SX_FIX)이거나, 래치 없이 더럽힌 것으로 표시된 buf fix 만 대상이다.

`storage` / `innobase` / `mtr` / `mtr0mtr.cc` L319-L368 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/mtr/mtr0mtr.cc#L319-L368))

```cpp
// mtr0mtr.cc L319-L368
struct Add_dirty_blocks_to_flush_list {
  /** Constructor.
  @param[in]    start_lsn       LSN of the first entry that was
                                  added to REDO by the MTR
  @param[in]    end_lsn         LSN after the last entry was
                                  added to REDO by the MTR
  @param[in,out]        observer        flush observer */
  Add_dirty_blocks_to_flush_list(lsn_t start_lsn, lsn_t end_lsn,
                                 Flush_observer *observer);

  /** Add the modified page to the buffer flush list. */
  void add_dirty_page_to_flush_list(mtr_memo_slot_t *slot) const {
    ut_ad(m_end_lsn > m_start_lsn || (m_end_lsn == 0 && m_start_lsn == 0));

#ifndef UNIV_HOTBACKUP
    buf_block_t *block = reinterpret_cast<buf_block_t *>(slot->object);
    buf_flush_note_modification(block, m_start_lsn, m_end_lsn,
                                m_flush_observer);
#endif /* !UNIV_HOTBACKUP */
  }

  /** @return true always. */
  bool operator()(mtr_memo_slot_t *slot) const {
    if (slot->object != nullptr) {
      if (slot->type == MTR_MEMO_PAGE_X_FIX ||
          slot->type == MTR_MEMO_PAGE_SX_FIX) {
        add_dirty_page_to_flush_list(slot);

      } else if (slot->type == MTR_MEMO_BUF_FIX) {
        buf_block_t *block;
        block = reinterpret_cast<buf_block_t *>(slot->object);
        if (block->made_dirty_with_no_latch) {
          add_dirty_page_to_flush_list(slot);
          block->made_dirty_with_no_latch = false;
        }
      }
    }

    return true;
  }

  /** Mini-transaction REDO end LSN */
  const lsn_t m_end_lsn;

  /** Mini-transaction REDO start LSN */
  const lsn_t m_start_lsn;

  /** Flush observer */
  Flush_observer *const m_flush_observer;
};
```

페이지 하나에 lsn 을 찍는 곳이다. 끝의 주석이 `report_added` 를 여기서 부르지 않는 이유를 적어 두었다.

`storage` / `innobase` / `include` / `buf0flu.ic` L49-L110 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/buf0flu.ic#L49-L110))

```cpp
// buf0flu.ic L49-L110
static inline void buf_flush_note_modification(
    buf_block_t *block,       /*!< in: block which is modified */
    lsn_t start_lsn,          /*!< in: start lsn of the mtr that
                              modified this block */
    lsn_t end_lsn,            /*!< in: end lsn of the mtr that
                              modified this block */
    Flush_observer *observer) /*!< in: flush observer */
{
#ifdef UNIV_DEBUG
  {
    /* Allow write to proceed to shared temporary tablespace
    in read-only mode. */
    ut_ad(!srv_read_only_mode ||
          fsp_is_system_temporary(block->page.id.space()));
    ut_ad(buf_block_get_state(block) == BUF_BLOCK_FILE_PAGE);
    ut_ad(block->page.buf_fix_count > 0);

    buf_pool_t *buf_pool = buf_pool_from_block(block);

    ut_ad(!buf_flush_list_mutex_own(buf_pool));
  }
#endif /* UNIV_DEBUG */

  mutex_enter(&block->mutex);

  if (end_lsn != 0) {
    ut_ad(block->page.get_newest_lsn() <= end_lsn);
    block->page.set_newest_lsn(end_lsn);
  } else {
    /* Do nothing. This is the case with no-redo mtr and it
    possibly could re-modify some earlier dirtied page, in
    which case we don't want to change oldest/newest lsns.
    If that's not the case, we will set newest_modification
    within buf_flush_insert_into_flush_list call. That's
    because we can't read the value now, because we don't
    hold the flush list mutex yet. */
  }

  if (observer != nullptr) {
    block->page.set_flush_observer(observer);
  } else {
    block->page.reset_flush_observer();
  }

  if (!block->page.is_dirty()) {
    auto buf_pool = buf_pool_from_block(block);

    buf_flush_insert_into_flush_list(buf_pool, block, start_lsn);
  } else if (start_lsn != 0) {
    ut_ad(block->page.get_oldest_lsn() <= start_lsn);
  }

  buf_page_mutex_exit(block);

  srv_stats.buf_pool_write_requests.inc();
  /* Note: we can't add the arc to buf_flush_list_added here, because multiple
  pages from same mtr all share the same [start_lsn,end_lsn) range, and only
  after all of them are actually inserted into the flush list we can consider
  the range done. Therefore mtr commit has to call
  Buf_flush_list_added_lsns.report_added() manually once it adds all its
  dirty pages to flush lists. */
}
```

처음 더럽혀진 페이지만 flush list 에 들어간다. 머리(FIRST)에 붙이므로 flush list 의 꼬리가 가장 오래된 쪽이다.

`storage` / `innobase` / `buf` / `buf0flu.cc` L375-L434 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0flu.cc#L375-L434))

```cpp
// buf0flu.cc L375-L434
void buf_flush_insert_into_flush_list(
    buf_pool_t *buf_pool, /*!< buffer pool instance */
    buf_block_t *block,   /*!< in/out: block which is modified */
    lsn_t lsn)            /*!< in: oldest modification */
{
  ut_ad(mutex_own(buf_page_get_mutex(&block->page)));
  ut_ad(log_sys != nullptr);

  buf_flush_list_mutex_enter(buf_pool);

  ut_ad(buf_block_get_state(block) == BUF_BLOCK_FILE_PAGE);
  ut_ad(!block->page.in_flush_list);

  ut_d(block->page.in_flush_list = true);

  if (lsn == 0) {
    /* This is no-redo dirtied page. Borrow the lsn. */
    lsn = buf_flush_borrow_lsn(buf_pool);

    ut_ad(log_is_data_lsn(lsn));

    /* This page could already be no-redo dirtied before,
    and flushed since then. Also the page from which we
    borrowed lsn last time could be flushed by LRU and
    we would end up borrowing smaller LSN.

    Another risk is that this page was flushed earlier
    and freed. We should not re-flush it to disk with
    smaller FIL_PAGE_LSN.

    The best way to go is to use flushed_to_disk_lsn,
    unless we borrowed even higher value.

    This way we are sure that no page has ever been
    flushed with higher newest_modification - it would
    first need to wait until redo is flushed up to
    such point and it would ensure that by checking
    the log_sys->flushed_to_disk_lsn's value too.

    Because we keep the page latched, after we read
    flushed_to_disk_lsn this page cannot be flushed
    in background with higher lsn (hence we are safe
    even if the flushed_to_disk_lsn advanced after
    we read it). */

    block->page.set_newest_lsn(
        std::max(lsn, log_sys->flushed_to_disk_lsn.load()));
  }

  ut_ad(log_is_data_lsn(lsn));
  ut_ad(!block->page.is_dirty());
  ut_ad(block->page.get_newest_lsn() >= lsn);

  ut_ad(UT_LIST_GET_FIRST(buf_pool->flush_list) == nullptr ||
        buf_flush_list_order_validate(
            UT_LIST_GET_FIRST(buf_pool->flush_list)->get_oldest_lsn(), lsn));

  block->page.set_oldest_lsn(lsn);

  UT_LIST_ADD_FIRST(buf_pool->flush_list, &block->page);
```

앞뒤를 감싸는 두 호출의 실체다. 둘 다 `Link_buf` 하나(`m_buf_added_lsns`)를 쓴다. 이 클래스의 예전 이름은 recent_closed 였고(buf0flu.h L354 주석), 대기 모니터 이름 `MONITOR_LOG_ON_RECENT_CLOSED_WAIT_LOOPS` 에 그 흔적이 남아 있다.

`storage` / `innobase` / `buf` / `buf0flu.cc` L3610-L3641 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0flu.cc#L3610-L3641))

```cpp
// buf0flu.cc L3610-L3641
void Buf_flush_list_added_lsns::report_added(lsn_t oldest_modification,
                                             lsn_t newest_modification) {
  m_buf_added_lsns.add_link_advance_tail(oldest_modification,
                                         newest_modification);
}

uint64_t Buf_flush_list_added_lsns::order_lag() {
  ut_ad(srv_buf_flush_list_added_size == m_buf_added_lsns.capacity());
  return m_buf_added_lsns.capacity();
}

lsn_t Buf_flush_list_added_lsns::smallest_not_added_lsn() {
  m_buf_added_lsns.advance_tail();
  return m_buf_added_lsns.tail();
}

void Buf_flush_list_added_lsns::wait_to_add(lsn_t oldest_modification) {
  ut_a(log_is_data_lsn(oldest_modification));

  ut_ad(m_buf_added_lsns.tail() <= oldest_modification);

  uint64_t wait_loops = 0;

  while (!m_buf_added_lsns.has_space(oldest_modification)) {
    ++wait_loops;
    std::this_thread::sleep_for(std::chrono::microseconds(20));
  }

  if (unlikely(wait_loops != 0)) {
    MONITOR_INC_VALUE(MONITOR_LOG_ON_RECENT_CLOSED_WAIT_LOOPS, wait_loops);
  }
}
```

## 동작 흐름

```text
 mtr0mtr.cc
 L830  Add_dirty_blocks_to_flush_list(start_lsn, end_lsn, observer)
 L835  m_memo.for_each_block_in_reverse                   나중에 잡은 슬롯부터
         L343  X_FIX, SX_FIX                               --> add_dirty_page_to_flush_list
         L347  BUF_FIX 이고 made_dirty_with_no_latch        --> add, 표시를 지운다
         그 밖(S_FIX, 테이블스페이스 래치 등)은 건너뛴다

 buf0flu.ic buf_flush_note_modification
 L72   block->mutex
 L74   end_lsn != 0 이면 L76  newest_modification = end_lsn
 L93   아직 dirty 가 아니면 (oldest_lsn == 0, buf0buf.h L1366)
 L96     buf_flush_insert_into_flush_list(buf_pool, block, start_lsn)
           buf0flu.cc L383  flush_list_mutex
                      L390  lsn == 0 (NO_REDO mtr) 이면 L392 buf_flush_borrow_lsn 으로 빌린다
                      L432  oldest_modification = lsn
                      L434  UT_LIST_ADD_FIRST(flush_list)   머리에 붙인다
 L97   이미 dirty 면 oldest 는 그대로 (start_lsn 이상이어야 한다)
 L103  buf_pool_write_requests++
```

```text
 페이지 하나의 lsn 두 개가 어떻게 움직이는가 (mtr 세 개가 같은 페이지 P 를 바꿀 때)

 mtr     [start, end)    P.oldest     P.newest    flush list
 m1      [100, 180)      100          180         머리에 P 가 붙는다
 m2      [300, 340)      100          340         그대로 (이미 dirty)
 --- P 를 다 쓰면 buf_flush_remove 가 빼고 set_clean 으로 oldest = 0 (buf0buf.h L1377) ---
 m3      [500, 560)      500          560         다시 머리에 붙는다

 oldest  = "이 페이지에 아직 디스크에 없는 변경 중 가장 오래된 것의 시작"
           checkpoint 는 이보다 앞으로 갈 수 없다
 newest  = "이 페이지를 디스크에 쓰려면 redo 가 여기까지 먼저 나가 있어야 한다"
```

flush list 는 한 버퍼 풀 인스턴스에 하나다. 여러 스레드가 이 함수를 동시에 돌리므로 머리에 붙는 순서는 oldest 순서와 조금씩 어긋난다.

```text
 flush list 한 개 (buf_pool 인스턴스마다, 머리가 새것)

 FIRST                                                           LAST
  +------+   +------+   +------+   +------+   +------+   +------+
  | 520  |-->| 500  |-->| 510  |-->| 300  |-->| 180  |-->| 100  |
  +------+   +------+   +------+   +------+   +------+   +------+
  ^ UT_LIST_ADD_FIRST 로 들어온다              page cleaner 는 LAST 부터 flush 한다 ^
    (숫자는 oldest_modification)

 500 과 510 처럼 뒤집힐 수 있지만 그 차이는 order_lag() 를 넘지 않는다
   (debug 검사 buf_flush_list_order_validate, buf0flu.cc L317-L325)
 wait_to_add(start) 가 start < smallest_not_added_lsn + order_lag 일 때만 들여보내기 때문이다
 order_lag() = innodb_buf_flush_list_added_size, 기본 2MB (log0constants.h L503)
```

## 결과가 쓰이는 곳

```text
 flush list
      --> buf_do_flush_list_batch 가 LAST 부터 oldest < lsn_limit 인 페이지를 쓴다  [페이지 플러시...]
      --> buf_pool_get_oldest_modification_approx 가 LAST 쪽의 oldest 를 읽는다

 newest_modification
      --> buf_flush_write_block_low 가 쓰기 전에 log_write_up_to(newest) 한다
      --> FIL_PAGE_LSN 으로 페이지에 찍힌다

 report_added (execute L867)
      --> smallest_not_added_lsn 이 전진한다. checkpoint 의 상한이다
```

## 다루지 않는 것

`Flush_observer`(bulk load 와 DDL 이 자기 페이지의 flush 를 기다리는 장치), `made_dirty_with_no_latch` 가 켜지는 경로, `buf_flush_borrow_lsn` 이 빌린 lsn 을 `flushed_to_disk_lsn` 과 비교하는 이유(buf0flu.cc 주석 L396-L418), 압축 페이지(`BUF_BLOCK_ZIP_DIRTY`)의 flush list 이동(`buf_flush_relocate_on_flush_list`)은 요약만 했다.
