# mtr_t::start

상위: [mini-transaction과 redo 기록](../README.md)

**mini-transaction 하나의 출발점이다.** 하는 일은 두 버퍼(`m_log` 는 redo 레코드, `m_memo` 는 잡은 래치와 고정한 페이지)를 비우고 로그 모드를 `MTR_LOG_ALL` 로 두는 것뿐이다. 볼거리는 `check_nolog_and_mark` 한 줄이다. redo 가 전역으로 꺼져 있으면 이 mtr 은 시작부터 `MTR_LOG_NO_REDO` 가 되고, commit 이 그것을 보고 다른 길로 간다.

## 위치

`storage` / `innobase` / `mtr` / `mtr0mtr.cc` L565-L602 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/mtr/mtr0mtr.cc#L565-L602))

## 실제 코드

`storage` / `innobase` / `mtr` / `mtr0mtr.cc` L565-L602 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/mtr/mtr0mtr.cc#L565-L602))

```cpp
// mtr0mtr.cc L565-L602
void mtr_t::start(bool sync) {
  ut_ad(m_impl.m_state == MTR_STATE_INIT ||
        m_impl.m_state == MTR_STATE_COMMITTED);

  UNIV_MEM_INVALID(this, sizeof(*this));
  IF_DEBUG(UNIV_MEM_VALID(&m_restart_count, sizeof(m_restart_count)););

  UNIV_MEM_INVALID(&m_impl, sizeof(m_impl));

  m_sync = sync;

  m_commit_lsn = 0;

  new (&m_impl.m_log) mtr_buf_t();
  new (&m_impl.m_memo) mtr_buf_t();

  m_impl.m_mtr = this;
  m_impl.m_log_mode = MTR_LOG_ALL;
  m_impl.m_inside_ibuf = false;
  m_impl.m_modifications = false;
  m_impl.m_n_log_recs = 0;
  m_impl.m_state = MTR_STATE_ACTIVE;
  m_impl.m_flush_observer = nullptr;
  m_impl.m_marked_nolog = false;

#ifndef UNIV_HOTBACKUP
  check_nolog_and_mark();
#endif /* !UNIV_HOTBACKUP */
  ut_d(m_impl.m_magic_n = MTR_MAGIC_N);

#ifdef UNIV_DEBUG
  auto res = s_my_thread_active_mtrs.insert(this);
  /* Assert there are no collisions in thread local context - it would mean
  reusing MTR without committing or destructing it. */
  ut_a(res.second);
  m_restart_count++;
#endif /* UNIV_DEBUG */
}
```

시작과 끝이 짝을 이룬다. 시작에서 전역 상태에 표시하고, commit 끝에서 표시를 거둔다.

`storage` / `innobase` / `mtr` / `mtr0mtr.cc` L605-L634 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/mtr/mtr0mtr.cc#L605-L634))

```cpp
// mtr0mtr.cc L605-L634
void mtr_t::check_nolog_and_mark() {
  /* Safe check to make this call idempotent. */
  if (m_impl.m_marked_nolog) {
    return;
  }

  size_t shard_index = default_indexer_t<>::get_rnd_index();
  m_impl.m_marked_nolog = s_logging.mark_mtr(shard_index);

  /* Disable redo logging by this mtr if logging is globally off. */
  if (m_impl.m_marked_nolog) {
    ut_ad(m_impl.m_log_mode == MTR_LOG_ALL);
    m_impl.m_log_mode = MTR_LOG_NO_REDO;
    m_impl.m_shard_index = shard_index;
  }
}

void mtr_t::check_nolog_and_unmark() {
  if (m_impl.m_marked_nolog) {
    s_logging.unmark_mtr(m_impl.m_shard_index);

    m_impl.m_marked_nolog = false;
    m_impl.m_shard_index = 0;

    if (m_impl.m_log_mode == MTR_LOG_NO_REDO) {
      /* Reset back to default mode. */
      m_impl.m_log_mode = MTR_LOG_ALL;
    }
  }
}
```

로그 모드는 네 가지다.

`storage` / `innobase` / `include` / `mtr0types.h` L42-L57 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/mtr0types.h#L42-L57))

```cpp
// mtr0types.h L42-L57
enum mtr_log_t {
  /** Default mode: log all operations modifying disk-based data */
  MTR_LOG_ALL = 0,

  /** Log no operations and dirty pages are not added to the flush list */
  MTR_LOG_NONE = 1,

  /** Don't generate REDO log but add dirty pages to flush list */
  MTR_LOG_NO_REDO = 2,

  /** Inserts are logged in a shorter form */
  MTR_LOG_SHORT_INSERTS = 3,

  /** Last element */
  MTR_LOG_MODE_MAX = 4
};
```

## 동작 흐름

```text
 L566  상태가 INIT 이나 COMMITTED 여야 한다  (같은 mtr_t 를 다시 start 할 수 있다)
 L574  m_sync         이 mtr 이 동기 모드인지
 L576  m_commit_lsn = 0                    commit 이 end_lsn 으로 채운다
 L578  m_log  = 빈 mtr_buf_t               redo 레코드가 쌓일 곳
 L579  m_memo = 빈 mtr_buf_t               래치와 buf fix 가 쌓일 곳
 L582  m_log_mode      = MTR_LOG_ALL
 L584  m_modifications = false             페이지를 바꾸면 true 가 된다
 L585  m_n_log_recs    = 0                 레코드를 하나 쓸 때마다 +1
 L586  m_state         = MTR_STATE_ACTIVE
 L591  check_nolog_and_mark
         L612  s_logging.mark_mtr(shard)   전역 redo 가 꺼져 있으면 true
         L617    m_log_mode = MTR_LOG_NO_REDO
 L596  (debug) 스레드 지역 목록에 넣어 같은 mtr 을 commit 없이 다시 쓰는지 잡는다
```

mtr 은 redo 묶음이면서 래치를 쥐는 단위이기도 하다. start 와 commit 사이에 잡은 래치는 m_memo 에 기록되고 대부분 commit 에서 한꺼번에 풀린다. 중간에 푸는 `memo_release`, `release_page` 도 있지만 수정한 페이지의 X 래치는 중간에 풀 수 없다(mtr0mtr.cc L723-L725, L742-L744 주석).

```text
 mtr_t 의 수명 (한 스레드 안, 위에서 아래로)

 step      m_state            line   m_log, m_memo, 래치
 -------   ----------------   ----   ------------------------------------------
 start     ACTIVE             L586   둘 다 비어 있고 래치도 없다
 modify    ACTIVE             -      m_log 에 레코드, m_memo 에 X_FIX / S_FIX 가 쌓인다
 commit    COMMITTING         L666   m_log 를 log buffer 로 복사, 래치는 아직 쥐고 있다
 release   COMMITTED          L656   두 버퍼를 erase, 래치를 모두 푼다
```

```text
 로그 모드 네 가지와 commit 에서의 결과 (mtr0types.h L42-L57)

 mode                   prepare_write   redo 와 flush list
 MTR_LOG_ALL            m_log.size()    redo 를 쓰고 페이지를 flush list 에 붙인다
 MTR_LOG_NONE           0               둘 다 없다 (enum 주석 L46)
 MTR_LOG_NO_REDO        0               redo 없이 flush list 에만 붙인다 (lsn 0, 0)
 MTR_LOG_SHORT_INSERTS  0               debug 빌드에서는 ut_error
```

## 결과가 쓰이는 곳

```text
 m_log
      --> 레코드를 덧붙인 쪽이 mtr->added_rec() 로 m_n_log_recs 를 올린다 (mtr0log.ic L158, L182)
      --> [03] prepare_write 가 크기를 재고, [04] execute 가 log buffer 로 옮긴다

 m_memo
      --> buf_page_get_gen 과 래치 함수가 슬롯을 push 한다  [버퍼 풀 페이지 획득]
      --> [08] 이 X_FIX, SX_FIX 슬롯의 페이지를 flush list 에 붙인다
      --> commit 의 release_all 이 역순으로 푼다

 m_log_mode
      --> [02] commit 이 execute 로 갈지, 래치만 풀지 가른다
```

## 다루지 않는 것

`mtr_t::Logging`(전역 redo 비활성의 상태 기계와 `mark_mtr` 의 샤드 카운터), `mtr_buf_t` 의 블록 연결 구조, `m_inside_ibuf` 와 change buffer, `set_log_mode` 로 모드를 바꾸는 호출처(임시 테이블, bulk load)는 곁가지라 다루지 않는다.
