# Buf_fetch::read_page

상위: [버퍼 풀 페이지 획득](../README.md)

**미적중 때 한 번 부르는 "읽어 오기" 함수다.** 요청한 페이지는 동기로 읽고(`buf_read_page`), 성공하면 그 주변 묶음에 대해 random read-ahead 를 비동기로 건다. 실패하면 호출자 루프가 다시 부르도록 재시도 횟수만 올리고, 100번을 넘기면 서버를 멈춘다. 읽은 블록을 돌려주지 않는 것이 요점이다. 블록은 page hash 에 올라가 있고, [04] 의 다음 lookup 이 그것을 찾는다.

## 위치

`storage` / `innobase` / `buf` / `buf0buf.cc` L4117-L4150 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0buf.cc#L4117-L4150))

## 실제 코드

`storage` / `innobase` / `buf` / `buf0buf.cc` L4116-L4150 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0buf.cc#L4116-L4150))

```cpp
// buf0buf.cc L4116-L4150
template <typename T>
void Buf_fetch<T>::read_page() {
  if (buf_read_page(m_page_id, m_page_size)) {
    /* Avoid doing read-ahead for parallel scans (well, at least currently this
    flag is used only during the parallel scans). This would cause unnecessary
    IO when the process is already being parallelized on higher level of
    abstraction. */
    if (m_mode != Page_fetch::SCAN) {
      buf_read_ahead_random(m_page_id, m_page_size, ibuf_inside(m_mtr));
    }
    m_retries = 0;
  } else if (m_retries < BUF_PAGE_READ_MAX_RETRIES) {
    ++m_retries;

    DBUG_EXECUTE_IF("innodb_page_corruption_retries",
                    m_retries = BUF_PAGE_READ_MAX_RETRIES;);
  } else {
    ib::fatal(UT_LOCATION_HERE, ER_IB_MSG_74)
        << "Unable to read page " << m_page_id << " into the buffer pool after "
        << BUF_PAGE_READ_MAX_RETRIES
        << " attempts. The most probable cause of this error may"
           " be that the table has been corrupted. Or, the table was"
           " compressed with with an algorithm that is not supported by "
           "this"
           " instance. If it is not a decompress failure, you can try to "
           "fix"
           " this problem by using innodb_force_recovery. Please "
           "see " REFMAN " for more details. Aborting...";
  }

#if defined UNIV_DEBUG || defined UNIV_BUF_DEBUG
  ut_ad(fsp_skip_sanity_check(m_page_id.space()) || ++buf_dbg_counter % 5771 ||
        buf_validate());
#endif /* UNIV_DEBUG || UNIV_BUF_DEBUG */
}
```

`buf_read_page` 는 `buf_read_page_low` 를 **동기(sync=true)** 로 부르는 얇은 래퍼다.

`storage` / `innobase` / `buf` / `buf0rea.cc` L288-L306 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0rea.cc#L288-L306))

```cpp
// buf0rea.cc L288-L306
bool buf_read_page(const page_id_t &page_id, const page_size_t &page_size) {
  ulint count;
  dberr_t err;

  count = buf_read_page_low(&err, true, 0, BUF_READ_ANY_PAGE, page_id,
                            page_size, false);

  srv_stats.buf_pool_reads.add(count);

  if (err == DB_TABLESPACE_DELETED) {
    ib::error(ER_IB_MSG_141) << "trying to read page " << page_id
                             << " in nonexisting or being-dropped tablespace";
  }

  /* Increment number of I/O operations used for LRU policy. */
  buf_LRU_stat_inc_io();

  return (count > 0);
}
```

재시도 상한은 파일 머리에 있다.

`storage` / `innobase` / `buf` / `buf0buf.cc` L297-L298 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0buf.cc#L297-L298))

```cpp
// buf0buf.cc L297-L298
/** Number of attempts made to read in a page in the buffer pool */
static const ulint BUF_PAGE_READ_MAX_RETRIES = 100;
```

## 동작 흐름

```text
 L4118  buf_read_page(m_page_id, m_page_size)
          buf0rea.cc L292  [06] buf_read_page_low(sync=true, BUF_READ_ANY_PAGE)
          buf0rea.cc L295  Innodb_buffer_pool_reads += count   (실제로 디스크를 읽은 수)
          buf0rea.cc L303  buf_LRU_stat_inc_io()               LRU 정책 통계
          true = 이 스레드가 한 장을 읽어 들였다

   true
 L4123    mode != SCAN 이면 buf_read_ahead_random    같은 read-ahead 영역의 이웃을 비동기로
 L4126    m_retries = 0
   false (이미 다른 스레드가 올렸거나, 공간이 없거나, 읽기 실패)
 L4127    m_retries < 100 이면 ++m_retries           돌아가서 다시 lookup
 L4133    아니면 ib::fatal ER_IB_MSG_74              "Unable to read page ... after 100 attempts"
```

false 가 곧 실패는 아니다. [07] 이 "이미 page hash 에 있음"을 발견하면 아무것도 읽지 않고 0을 돌려주는데, 이것은 다른 스레드가 먼저 올린 경우라 다음 lookup 이 적중한다. 그래서 재시도 횟수는 "연속으로 읽어 들이지 못한 횟수"를 센다.

```text
 Innodb_buffer_pool_read_requests 와 Innodb_buffer_pool_reads

 read_requests  [02] L4302  m_n_page_gets++           buf_page_get_gen 한 번마다
 reads          [05]        buf_pool_reads += count   디스크에서 읽은 페이지마다
             random read-ahead 로 읽은 페이지도 같은 카운터에 더한다 (buf0rea.cc L284)
             linear read-ahead 는 n_ra_pages_read 에만 더한다 (buf0rea.cc L584)

 적중률 = 1 - reads / read_requests 로 흔히 계산하는 두 값이 여기서 나온다
```

## 결과가 쓰이는 곳

```text
 page hash 에 올라간 블록 (IO_READ 는 동기 경로에서 이미 풀렸다)
      --> [04] 의 다음 바퀴 lookup 이 적중한다
 random read-ahead 로 올린 이웃 블록
      --> 비동기 I/O 핸들러 스레드가 buf_page_io_complete 로 마친다
      --> 나중에 누가 get 하면 적중. 한 번도 안 쓰이고 쫓겨나면 n_ra_pages_evicted
```

## 다루지 않는 것

`buf_read_ahead_random` 의 판정(영역 안 최근 접근 블록 수가 문턱을 넘는지), `innodb_random_read_ahead` 설정, `buf_LRU_stat_inc_io` 가 LRU 와 unzip_LRU 중 어느 쪽에서 교체할지 정하는 통계는 이 함수의 곁가지라 요약만 했다.
