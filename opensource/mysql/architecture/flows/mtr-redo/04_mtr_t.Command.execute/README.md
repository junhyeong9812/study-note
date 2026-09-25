# mtr_t::Command::execute

상위: [mini-transaction과 redo 기록](../README.md)

**commit 의 본체다. 순서가 곧 설계다.** 예약(`log_buffer_reserve`) -> 복사와 링크(`mtr_write_log_t`) -> flush list 창 대기(`wait_to_add`) -> 페이지를 flush list 에 붙임 -> 끝났다고 보고(`report_added`) -> 래치 해제. 페이지를 flush list 에 다 붙인 **뒤에** 보고하는 순서가 checkpoint 계산을 안전하게 만든다. 보고 전의 범위는 checkpoint 가 넘지 못하기 때문이다(log0buf.cc L430-L443 주석).

## 위치

`storage` / `innobase` / `mtr` / `mtr0mtr.cc` L840-L880 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/mtr/mtr0mtr.cc#L840-L880))

## 실제 코드

`storage` / `innobase` / `mtr` / `mtr0mtr.cc` L840-L880 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/mtr/mtr0mtr.cc#L840-L880))

```cpp
// mtr0mtr.cc L840-L880
void mtr_t::Command::execute() {
  ut_ad(m_impl->m_log_mode != MTR_LOG_NONE);

#ifndef UNIV_HOTBACKUP
  ulint len = prepare_write();

  if (len > 0) {
    mtr_write_log_t write_log;

    write_log.m_left_to_write = len;

    auto handle = log_buffer_reserve(*log_sys, len);

    write_log.m_handle = handle;
    write_log.m_lsn = handle.start_lsn;

    m_impl->m_log.for_each_block(write_log);

    ut_ad(write_log.m_left_to_write == 0);
    ut_ad(write_log.m_lsn == handle.end_lsn);

    buf_flush_list_added->wait_to_add(handle.start_lsn);

    DEBUG_SYNC_C("mtr_redo_before_add_dirty_blocks");

    add_dirty_blocks_to_flush_list(handle.start_lsn, handle.end_lsn);

    buf_flush_list_added->report_added(handle.start_lsn, handle.end_lsn);

    m_impl->m_mtr->m_commit_lsn = handle.end_lsn;

  } else {
    DEBUG_SYNC_C("mtr_noredo_before_add_dirty_blocks");

    add_dirty_blocks_to_flush_list(0, 0);
  }
#endif /* !UNIV_HOTBACKUP */

  release_all();
  release_resources();
}
```

복사는 `m_log` 의 블록마다 부르는 함수 객체가 한다. 블록 하나를 쓰고 곧바로 링크를 건다. 마지막 블록에서만 `is_last_block` 이 켜진다.

`storage` / `innobase` / `mtr` / `mtr0mtr.cc` L499-L558 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/mtr/mtr0mtr.cc#L499-L558))

```cpp
// mtr0mtr.cc L499-L558
struct mtr_write_log_t {
  /** Append a block to the redo log buffer.
  @return whether the appending should continue */
  bool operator()(const mtr_buf_t::block_t *block) {
    lsn_t start_lsn;
    lsn_t end_lsn;
    bool is_last_block = false;

    ut_ad(block != nullptr);

    if (block->used() == 0) {
      return true;
    }

    start_lsn = m_lsn;

    end_lsn =
        log_buffer_write(*log_sys, block->begin(), block->used(), start_lsn);

    ut_a(end_lsn % OS_FILE_LOG_BLOCK_SIZE <
         OS_FILE_LOG_BLOCK_SIZE - LOG_BLOCK_TRL_SIZE);

    m_left_to_write -= block->used();

    if (m_left_to_write == 0) {
      is_last_block = true;
      /* This write was up to the end of record group,
      the last record in group has been written.

      Therefore next group of records starts at m_lsn.
      We need to find out, if the next group is the first group,
      that starts in this log block.

      In such case we need to set first_rec_group.

      Now, we could have two cases:
      1. This group of log records has started in previous block
         to block containing m_lsn.
      2. This group of log records has started in the same block
         as block containing m_lsn.

      Only in case 1), the next group of records is the first group
      of log records in block containing m_lsn. */
      if (m_handle.start_lsn / OS_FILE_LOG_BLOCK_SIZE !=
          end_lsn / OS_FILE_LOG_BLOCK_SIZE) {
        log_buffer_set_first_record_group(*log_sys, end_lsn);
      }
    }

    log_buffer_write_completed(*log_sys, start_lsn, end_lsn, is_last_block);

    m_lsn = end_lsn;

    return true;
  }

  Log_handle m_handle;
  lsn_t m_lsn;
  ulint m_left_to_write;
};
```

## 동작 흐름

```text
 L844  len = [03] prepare_write()
 L846  len > 0 (MTR_LOG_ALL)
 L851    handle = [05] log_buffer_reserve(len)          [start_lsn, end_lsn) 확정, log buffer s-lock
 L853    write_log.m_handle = handle, m_lsn = start_lsn
 L856    m_log.for_each_block(write_log)                 블록마다 L502 operator()
           L509  빈 블록은 건너뛴다
           L515  end_lsn = [06] log_buffer_write(block, m_lsn)
           L521  m_left_to_write -= used
           L523  0 이 되면 마지막 블록
                   L542  시작 블록과 끝 블록이 다르면
                   L544    log_buffer_set_first_record_group(end_lsn)
           L548  [07] log_buffer_write_completed(start, end, is_last)   recent_written 링크
           L550  m_lsn = end_lsn
 L858    (debug) 다 썼고 m_lsn == end_lsn
 L861    buf_flush_list_added->wait_to_add(start_lsn)   flush list 순서 창이 start_lsn 까지 올 때까지
 L865    [08] add_dirty_blocks_to_flush_list(start, end)
 L867    buf_flush_list_added->report_added(start, end) [start, end) 는 다 붙였다
 L869    m_commit_lsn = end_lsn
 L871  len == 0 (NO_REDO)
 L874    [08] add_dirty_blocks_to_flush_list(0, 0)      lsn 없이 붙인다 (빌려 쓴다, [08] 참고)
 L878  release_all()                                   래치 해제
 L879  release_resources()                             버퍼 erase, COMMITTED
```

한 mtr 이 두 개의 링크 버퍼에 흔적을 남긴다. 하나는 log writer 를 위한 것, 하나는 checkpointer 를 위한 것이다.

```text
 한 mtr 이 [s, e) 를 받았을 때 두 링크 버퍼 (Link_buf, lsn 으로 직접 주소)

 log.recent_written          slot[s % S] = e     "s..e 는 log buffer 에 복사 끝"
   거는 곳  [07] L548 (블록마다 조각 링크)
   읽는 곳  log_writer 의 log_advance_ready_for_write_lsn  --> ready_for_write_lsn

 buf_flush_list_added        slot[s % L] = e     "s..e 가 더럽힌 페이지는 flush list 에 다 있다"
   거는 곳  L867 report_added
   읽는 곳  checkpointer 의 smallest_not_added_lsn()     --> checkpoint 상한

 둘 다 tail 은 "그보다 작은 lsn 은 모두 끝났다"는 뜻이다
 tail 은 끊긴 링크(아직 안 끝난 mtr)에서 멈춘다
```

```text
 두 mtr 이 겹칠 때 (시간축, 위에서 아래로)

 스레드 A: [100, 180)                        스레드 B: [180, 260)
 ---------------------------------------     ---------------------------------------
 reserve  sn.fetch_add -> 100
                                             reserve  sn.fetch_add -> 180
                                             write    memcpy 180..260
                                             recent_written[180] = 260
 write    memcpy 100..180
 recent_written[100] = 180
            --> 이제 log_writer 가 100 -> 180 -> 260 으로 링크를 따라간다
                (A 가 링크를 걸기 전에는 100 에서 멈춰 있었다)
                                             wait_to_add(180)   창 안이면 바로 통과
                                             flush list 에 B 의 페이지  (oldest = 180)
                                             report_added(180, 260)
 wait_to_add(100)
 flush list 에 A 의 페이지 (oldest = 100)    --> flush list 앞쪽에 B, 그 뒤에 A 가 올 수 있다
 report_added(100, 180)                          순서가 느슨하지만 차이는 order_lag() 이하
            --> smallest_not_added_lsn 이 100 -> 260 으로 뛴다
```

아래쪽 절반이 "느슨한 순서" 다. `wait_to_add` 는 `start_lsn` 이 `smallest_not_added_lsn + order_lag` 안에 들어올 때까지만 막는다(log0buf.cc L363-L371 주석). 그래서 flush list 의 순서가 oldest_modification 순서와 달라도 그 차이는 `order_lag()` 이하로 묶인다. checkpoint 쪽은 이 값을 빼서 보정한다([페이지 플러시...](../../flush-checkpoint/README.md) 의 `buf_pool_get_oldest_modification_lwm`).

## 결과가 쓰이는 곳

```text
 recent_written 의 링크
      --> [09] log_writer 가 따라가 ready_for_write_lsn 을 올리고 파일에 쓴다

 flush list 의 페이지와 buf_flush_list_added 의 링크
      --> page cleaner 가 tail 부터 flush 한다                 [페이지 플러시...]
      --> log_checkpointer 가 smallest_not_added_lsn 과 flush list 의 가장 오래된 페이지로
          checkpoint 를 정한다

 m_commit_lsn
      --> 트랜잭션 커밋의 log_write_up_to 대상                  [커밋과 binlog 2PC]
```

## 다루지 않는 것

`log_buffer_set_first_record_group`(블록 헤더의 first_rec_group 필드를 누가 채우는가, log0buf.cc L233-L236 주석)의 세부, `Link_buf` 의 구현(`add_link_advance_tail`, `advance_tail_until`, `has_space`), `DEBUG_SYNC_C` 지점은 요약만 했다.
