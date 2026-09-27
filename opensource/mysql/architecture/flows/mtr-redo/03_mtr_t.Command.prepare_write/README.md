# mtr_t::Command::prepare_write

상위: [mini-transaction과 redo 기록](../README.md)

**log buffer 에 몇 바이트를 예약할지 정하고, 레코드 묶음의 경계를 표시한다.** 레코드가 하나면 첫 바이트에 `MLOG_SINGLE_REC_FLAG` 비트를 켜고, 여럿이면 끝에 1바이트 `MLOG_MULTI_REC_END` 를 붙인다. 복구는 mtr 하나를 통째로 적용하거나 통째로 건너뛰어야 하는데(log0buf.cc L333 주석), 그 단위의 끝을 알려 주는 것이 이 표시다.

## 위치

`storage` / `innobase` / `mtr` / `mtr0mtr.cc` L760-L813 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/mtr/mtr0mtr.cc#L760-L813))

## 실제 코드

`storage` / `innobase` / `mtr` / `mtr0mtr.cc` L760-L813 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/mtr/mtr0mtr.cc#L760-L813))

```cpp
// mtr0mtr.cc L760-L813
ulint mtr_t::Command::prepare_write() {
  switch (m_impl->m_log_mode) {
    case MTR_LOG_SHORT_INSERTS:
      ut_d(ut_error);
      /* fall through (write no redo log) */
      [[fallthrough]];
    case MTR_LOG_NO_REDO:
    case MTR_LOG_NONE:
      ut_ad(m_impl->m_log.size() == 0);
      return 0;
    case MTR_LOG_ALL:
      break;
    default:
      ut_d(ut_error);
      ut_o(return 0);
  }

  /* No logs records can be produced during recovery. */
  ut_a(!recv_recovery_is_on());

  ulint len = m_impl->m_log.size();
  ut_ad(len > 0);

  const auto n_recs = m_impl->m_n_log_recs;
  ut_ad(n_recs > 0);

  ut_ad(log_sys != nullptr);

  /* This was not the first time of dirtying a
  tablespace since the latest checkpoint. */

  if (n_recs <= 1) {
    ut_ad(n_recs == 1);

    /* Flag the single log record as the
    only record in this mini-transaction. */

    *m_impl->m_log.front()->begin() |= MLOG_SINGLE_REC_FLAG;

  } else {
    /* Because this mini-transaction comprises
    multiple log records, append MLOG_MULTI_REC_END
    at the end. */

    mlog_catenate_ulint(&m_impl->m_log, MLOG_MULTI_REC_END, MLOG_1BYTE);
    ++len;
  }

  ut_ad(m_impl->m_log_mode == MTR_LOG_ALL);
  ut_ad(m_impl->m_log.size() == len);
  ut_ad(len > 0);

  return len;
}
```

## 동작 흐름

```text
 L761  switch (m_log_mode)
         SHORT_INSERTS  L763  debug 에서 ut_error, 아니면 아래로 떨어진다
         NO_REDO, NONE  L768  m_log 는 비어 있어야 한다  L769  return 0
         ALL            L771  break
 L778  복구 중에는 redo 를 만들 수 없다 (ut_a)
 L780  len    = m_log.size()
 L783  n_recs = m_n_log_recs
 L791  n_recs <= 1
         L797  첫 레코드의 첫 바이트(타입) |= MLOG_SINGLE_REC_FLAG     len 그대로
       else
         L804  mlog_catenate_ulint(MLOG_MULTI_REC_END, 1 byte)         L805 ++len
 L812  return len                    --> [04] 가 log_buffer_reserve(len) 에 넘긴다
```

두 표시 방법은 바이트 모양이 다르다. 레코드 하나일 때는 바이트를 늘리지 않고, 여럿일 때만 1바이트를 더 쓴다.

```text
 m_log 의 모양 (복구가 보는 경계)

 레코드 1개
   +--------------------+------------------+
   | type | 0x80        | 레코드 본문       |      MLOG_SINGLE_REC_FLAG = 128 (mtr0types.h L67)
   +--------------------+------------------+
   ^ 이 비트 하나로 "이 mtr 은 여기서 끝난다"

 레코드 여러 개
   +------+------+------+------+------+------+------------------+
   | type | 본문 | type | 본문 | type | 본문 | MLOG_MULTI_REC_END |   +1 byte
   +------+------+------+------+------+------+------------------+
   복구 쪽은 MLOG_MULTI_REC_END 를 경계로 읽는다 (log0recv.cc L3023, L3086)
```

복구가 이 경계를 어떻게 쓰는지는 [크래시 복구](../../crash-recovery/README.md)에서 다룬다. 이 함수가 보장하는 것은 `MTR_LOG_ALL` mtr 에 표시가 반드시 하나 붙는다는 것까지다.

## 결과가 쓰이는 곳

```text
 반환값 len
      --> 0  이면 [04] execute 가 예약 없이 add_dirty_blocks_to_flush_list(0, 0) 만 한다
      --> >0 이면 [05] log_buffer_reserve(len) 가 [start_lsn, end_lsn) 를 잡는다
               len 은 데이터 바이트 수(sn). 블록 헤더와 트레일러는 lsn 변환에서 더해진다

 m_log 의 SINGLE / MULTI 표시
      --> 그대로 log buffer 로 복사되어 redo 파일까지 간다
```

## 다루지 않는 것

레코드 타입 목록(`mlog_id_t`)과 각 타입의 본문 배치, `mlog_catenate_ulint` 의 버퍼 확장은 [redo 로그 파일과 mlog 타입](../../../structure/redo-log-files/README.md)에 둔다.
