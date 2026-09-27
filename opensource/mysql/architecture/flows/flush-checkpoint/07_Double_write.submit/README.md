# Double_write::submit

상위: [페이지 플러시, doublewrite, 체크포인트](../README.md)

**비동기 배치 flush 가 doublewrite 를 거치는 입구다.** 본문은 버퍼 풀 인스턴스와 flush 종류에 맞는 `Double_write` 인스턴스를 골라 `enqueue` 하는 두 줄이다. 쌓인 페이지가 버퍼를 넘거나 배치가 끝나면(`force_flush`) 한 번에 내보내는데, 순서가 고정이다. doublewrite 파일의 배치 세그먼트에 전부 쓰고 fsync 한(O_DIRECT 계열이면 fsync 는 건너뛴다) **다음에** 페이지마다 데이터 파일 AIO 를 낸다. 세그먼트는 그 배치의 마지막 데이터 페이지 IO 가 끝나고 데이터 파일을 fsync 한 뒤에야 재사용된다.

## 위치

`storage` / `innobase` / `buf` / `buf0dblwr.cc` L669-L677 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0dblwr.cc#L669-L677))

## 실제 코드

`storage` / `innobase` / `buf` / `buf0dblwr.cc` L669-L677 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0dblwr.cc#L669-L677))

```cpp
// buf0dblwr.cc L669-L677
  static void submit(buf_flush_t flush_type, buf_page_t *bpage,
                     const file::Block *e_block) noexcept {
    if (s_instances == nullptr) {
      return;
    }

    auto dblwr = instance(flush_type, bpage);
    dblwr->enqueue(flush_type, bpage, e_block);
  }
```

버퍼에 넣다가 차면 내보내고 다시 넣는다.

`storage` / `innobase` / `buf` / `buf0dblwr.cc` L598-L635 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0dblwr.cc#L598-L635))

```cpp
// buf0dblwr.cc L598-L635
  void enqueue(buf_flush_t flush_type, buf_page_t *bpage,
               const file::Block *e_block) noexcept {
    ut_ad(buf_page_in_file(bpage));

    void *frame{};
    uint32_t len{};
    byte *e_frame =
        (e_block == nullptr) ? nullptr : os_block_get_frame(e_block);

    if (e_frame != nullptr) {
      frame = e_frame;
      len = e_block->m_size;
    } else {
      prepare(bpage, &frame, &len);
    }

    ut_a(len <= univ_page_size.physical());

    for (;;) {
      mutex_enter(&m_mutex);

      if (m_buffer.append(frame, len)) {
        break;
      }

      if (flush_to_disk(flush_type)) {
        auto success = m_buffer.append(frame, len);
        ut_a(success);
        break;
      }

      ut_ad(!mutex_own(&m_mutex));
    }

    m_buf_pages.push_back(bpage, e_block);

    mutex_exit(&m_mutex);
  }
```

내보내기 전에 앞선 배치가 끝나기를 기다린다. 한 인스턴스에서 배치는 한 번에 하나다.

`storage` / `innobase` / `buf` / `buf0dblwr.cc` L525-L591 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0dblwr.cc#L525-L591))

```cpp
// buf0dblwr.cc L525-L591
  /** Wait for any pending batch to complete.
  @return true if the thread had to wait for another batch. */
  bool wait_for_pending_batch() noexcept {
    ut_ad(mutex_own(&m_mutex));

    auto sig_count = os_event_reset(m_event);

    std::atomic_thread_fence(std::memory_order_acquire);

    if (m_batch_running.load(std::memory_order_acquire)) {
      mutex_exit(&m_mutex);

      MONITOR_INC(MONITOR_DBLWR_FLUSH_WAIT_EVENTS);
      os_event_wait_low(m_event, sig_count);
      sig_count = os_event_reset(m_event);
      return true;
    }

    return false;
  }

  /** Flush buffered pages to disk, clear the buffers.
  @param[in] flush_type           FLUSH LIST or LRU LIST flush.
  @return false if there was a write batch already in progress. */
  bool flush_to_disk(buf_flush_t flush_type) noexcept {
    ut_ad(mutex_own(&m_mutex));

    /* Wait for any batch writes that are in progress. */
    if (wait_for_pending_batch()) {
      ut_ad(!mutex_own(&m_mutex));
      return false;
    }

    MONITOR_INC(MONITOR_DBLWR_FLUSH_REQUESTS);

    /* Write the pages to disk and free up the buffer. */
    write_pages(flush_type);

    ut_a(m_buffer.empty());
    ut_a(m_buf_pages.empty());

    return true;
  }

  /** Process the requests in the flush queue, write the blocks to the
  double write file, sync the file if required and then write to the
  data files.
  @param[in] flush_type         LRU or FLUSH request. */
  void write_pages(buf_flush_t flush_type) noexcept;

  virtual uint16_t write_dblwr_pages(buf_flush_t flush_type) noexcept;

  void write_data_pages(buf_flush_t flush_type, uint16_t batch_id) noexcept;

  /** Force a flush of the page queue.
  @param[in] flush_type           FLUSH LIST or LRU LIST flush. */
  void force_flush(buf_flush_t flush_type) noexcept {
    for (;;) {
      mutex_enter(&m_mutex);
      if (!m_buf_pages.empty() && !flush_to_disk(flush_type)) {
        ut_ad(!mutex_own(&m_mutex));
        continue;
      }
      break;
    }
    mutex_exit(&m_mutex);
  }
```

내보내기의 두 단계다.

`storage` / `innobase` / `buf` / `buf0dblwr.cc` L2249-L2255 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0dblwr.cc#L2249-L2255))

```cpp
// buf0dblwr.cc L2249-L2255
void Double_write::write_pages(buf_flush_t flush_type) noexcept {
  ut_ad(mutex_own(&m_mutex));
  ut_a(!m_buffer.empty());

  const uint16_t batch_id = write_dblwr_pages(flush_type);
  write_data_pages(flush_type, batch_id);
}
```

1 단계, doublewrite 파일에 쓰고 fsync.

`storage` / `innobase` / `buf` / `buf0dblwr.cc` L2163-L2193 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0dblwr.cc#L2163-L2193))

```cpp
// buf0dblwr.cc L2163-L2193
uint16_t Double_write::write_dblwr_pages(buf_flush_t flush_type) noexcept {
  ut_ad(mutex_own(&m_mutex));
  ut_a(!m_buffer.empty());

  Batch_segment *batch_segment{};

  auto segments = flush_type == BUF_FLUSH_LRU ? s_LRU_batch_segments
                                              : s_flush_list_batch_segments;

  while (!segments->dequeue(batch_segment)) {
    std::this_thread::yield();
  }

  batch_segment->start(this);

  batch_segment->write(m_buffer);

  m_bytes_written += m_buffer.size();

  m_buffer.clear();

#ifndef _WIN32
  if (is_fsync_required()) {
    batch_segment->flush();
  }
#endif /* !_WIN32 */

  batch_segment->set_batch_size(m_buf_pages.size());

  return batch_segment->id();
}
```

2 단계, 데이터 파일에 페이지마다 비동기 쓰기.

`storage` / `innobase` / `buf` / `buf0dblwr.cc` L2195-L2210 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0dblwr.cc#L2195-L2210))

```cpp
// buf0dblwr.cc L2195-L2210
void Double_write::write_data_pages(buf_flush_t flush_type,
                                    uint16_t batch_id) noexcept {
  ut_ad(mutex_own(&m_mutex));

  for (uint32_t i = 0; i < m_buf_pages.size(); ++i) {
    const auto bpage = std::get<0>(m_buf_pages.m_pages[i]);

    ut_d(auto page_id = bpage->id);

    bpage->set_dblwr_batch_id(batch_id);

    ut_d(bpage->take_io_responsibility());
    auto err =
        write_to_datafile(bpage, false, std::get<1>(m_buf_pages.m_pages[i]));

    if (err == DB_PAGE_IS_STALE || err == DB_TABLESPACE_DELETED) {
```

IO 완료 쪽이다. 배치의 마지막 페이지가 끝나면 데이터 파일을 fsync 하고 세그먼트를 돌려준다.

`storage` / `innobase` / `buf` / `buf0dblwr.cc` L2563-L2612 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0dblwr.cc#L2563-L2612))

```cpp
// buf0dblwr.cc L2563-L2612
void Double_write::write_complete(buf_page_t *bpage,
                                  buf_flush_t flush_type) noexcept {
  if (s_instances == nullptr) {
    /* Not initialized yet. */
    return;
  }

  const auto batch_id = bpage->get_dblwr_batch_id();

  switch (flush_type) {
    case BUF_FLUSH_LRU:
    case BUF_FLUSH_LIST:
    case BUF_FLUSH_SINGLE_PAGE:
      if (batch_id != std::numeric_limits<uint16_t>::max()) {
        ut_ad(batch_id < s_segments.size());
        auto batch_segment = s_segments[batch_id];

        if (batch_segment->write_complete()) {
          batch_segment->completed();

          srv_stats.dblwr_pages_written.add(batch_segment->batch_size());

          batch_segment->reset();

          Batch_segments *segments{nullptr};

          if (is_reduced_batch_id(batch_id)) {
            segments = (flush_type == BUF_FLUSH_LRU)
                           ? Double_write::s_r_LRU_batch_segments
                           : Double_write::s_r_flush_list_batch_segments;
          } else {
            segments = (flush_type == BUF_FLUSH_LRU)
                           ? Double_write::s_LRU_batch_segments
                           : Double_write::s_flush_list_batch_segments;
          }

          fil_flush_file_spaces();

          while (!segments->enqueue(batch_segment)) {
            std::this_thread::yield();
          }
        }
      }
      bpage->set_dblwr_batch_id(std::numeric_limits<uint16_t>::max());
      break;

    case BUF_FLUSH_N_TYPES:
      ut_error;
  }
}
```

## 동작 흐름

```text
 submit
 L671  인스턴스가 없으면 무시
 L675  dblwr = instance(flush_type, bpage)          (flush 종류, 버퍼 풀 번호)로 고른다
 L676  dblwr->enqueue(flush_type, bpage, e_block)

 enqueue
 L616  for (;;), L617 m_mutex
 L619    m_buffer.append(frame, len) 성공 -> break
 L623    실패(가득) -> flush_to_disk
           L553  wait_for_pending_batch             앞선 배치가 끝날 때까지 (m_batch_running)
                   기다렸으면 false -> 처음부터 다시
           L561  write_pages
                   L2253  batch_id = write_dblwr_pages
                            L2172  빈 배치 세그먼트를 꺼낸다 (LRU 용, LIST 용 따로)
                            L2176  start -> batch_running = true
                            L2178  세그먼트에 m_buffer 전체를 쓴다
                            L2185  O_DIRECT 계열이 아니면 fsync
                            L2190  uncompleted = 페이지 수
                   L2254  write_data_pages(batch_id)
                            L2199  페이지마다
                            L2204    bpage->dblwr_batch_id = batch_id
                            L2208    write_to_datafile(sync = false)   데이터 파일 AIO
                            L2244  m_buf_pages.clear
 L632  m_buf_pages.push_back(bpage, e_block)

 IO 완료 (buf_flush_write_complete -> dblwr::write_complete)
 L2570  batch_id 를 읽는다
 L2580  segment.write_complete()                   uncompleted-- 가 0 이 되었나
 L2581    completed -> batch_completed             batch_running = false, m_event set
 L2599    fil_flush_file_spaces                    데이터 파일 fsync
 L2601    세그먼트를 빈 큐로 돌려준다
```

```text
 한 배치의 시간축 (페이지 A, B, C 가 같은 인스턴스로)

 page cleaner 스레드                             AIO 완료 스레드
 ---------------------------------------------   --------------------------------------
 enqueue A, B, C  (m_buffer 에 복사)
 buf_flush_end -> force_flush -> flush_to_disk
   세그먼트 S 를 꺼냄, batch_running = true
   S 에 A B C 를 write
   fsync(dblwr 파일)          <-- 이 시점부터 세 사본이 디스크에 있다
   데이터 파일 AIO: A, B, C
                                                 A 완료 -> flush list 에서 뺌, uncompleted 2
                                                 C 완료 -> uncompleted 1
 다음 배치 enqueue ... flush_to_disk
   wait_for_pending_batch 에서 잔다              B 완료 -> uncompleted 0
                                                   batch_completed (m_event)     L2581
   깨어날 수 있다 (m_event 가 먼저 선다)              fil_flush_file_spaces (데이터 fsync)  L2599
                                                   S 를 빈 큐로                  L2601
   다음 배치
```

`batch_completed` 가 이벤트를 먼저 세우고(L2581) 데이터 파일 fsync 는 그 뒤에 온다(L2599). 그래서 기다리던 page cleaner 는 fsync 가 끝나기 전에 깨어날 수 있다. 대신 세그먼트 S 는 fsync 뒤에야 빈 큐로 돌아가므로(L2601), fsync 되지 않은 데이터 페이지의 사본이 들어 있는 세그먼트를 다음 배치가 덮어쓰는 일은 없다.

```text
 doublewrite 의 두 파일 영역 (Batch_segment 와 Segment)

 s_LRU_batch_segments         LRU 배치용 세그먼트 큐
 s_flush_list_batch_segments  LIST 배치용 세그먼트 큐
 s_single_segments            단일 페이지 동기 쓰기용 (sync_page_flush, [06])

 세그먼트는 dequeue 로 빌리고, 데이터 파일 fsync 뒤 enqueue 로 돌려준다
 빌릴 세그먼트가 없으면 yield 하며 돈다 (L2172-L2174)
```

## 결과가 쓰이는 곳

```text
 doublewrite 파일의 배치 세그먼트
      --> 크래시 뒤 recv::Pages 가 읽어 찢어진 데이터 페이지를 덮는다   [크래시 복구]
      --> 세그먼트가 재사용되기 전에 데이터 파일이 fsync 되므로 필요 없어진 사본만 덮어쓴다

 write_complete 의 fil_flush_file_spaces
      --> dblwr 가 켜져 있으면 데이터 파일 fsync 가 여기서 배치 단위로 일어난다
```

## 다루지 않는 것

reduced 모드 인스턴스(`s_r_instances`, `Reduced_double_write::write_dblwr_pages`), 인스턴스 개수와 세그먼트 크기 계산(`create_batch_segments`), 암호화된 블록 해제, stale 페이지와 삭제된 테이블스페이스의 오류 경로(L2210-L2229)는 요약만 했다.
