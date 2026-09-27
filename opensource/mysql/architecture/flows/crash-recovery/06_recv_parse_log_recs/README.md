# recv_parse_log_recs

상위: [크래시 복구](../README.md)

**파싱 버퍼의 바이트를 mtr 단위로 잘라 페이지별 해시에 넣는 함수다.** 첫 바이트의 `MLOG_SINGLE_REC_FLAG` 로 mtr 이 레코드 하나짜리인지 여럿짜리인지 가르고, 여럿짜리는 `MLOG_MULTI_REC_END` 까지 **전부 버퍼에 들어와 있을 때만** 해시에 넣는다. mtr 이 원자 단위라는 성질이 여기서 지켜진다. 끝이 잘린 mtr 은 한 레코드도 해시에 들어가지 않는다. 해시에 넣는 일은 `recv_add_to_hash_table` 이 하며, 레코드 본문을 페이지별 목록 끝에 붙이고 그 mtr 의 시작, 끝 LSN 을 함께 적는다.

## 위치

`storage` / `innobase` / `log` / `log0recv.cc` L3135-L3169 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0recv.cc#L3135-L3169))

## 실제 코드

단일인지 다중인지 가른다.

`storage` / `innobase` / `log` / `log0recv.cc` L3133-L3169 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0recv.cc#L3133-L3169))

```cpp
// log0recv.cc L3133-L3169
/** Parse log records from a buffer and optionally store them to a
hash table to wait merging to file pages. */
static void recv_parse_log_recs() {
  ut_ad(recv_sys->parse_start_lsn != 0);

  for (;;) {
    const byte *ptr = recv_sys->buf + recv_sys->recovered_offset;

    const byte *end_ptr = recv_sys->buf + recv_sys->len;

    if (ptr == end_ptr) {
      return;
    }

    bool single_rec;

    switch (*ptr) {
#ifdef UNIV_LOG_LSN_DEBUG
      case MLOG_LSN:
#endif /* UNIV_LOG_LSN_DEBUG */
      case MLOG_DUMMY_RECORD:
        single_rec = true;
        break;
      default:
        single_rec = !!(*ptr & MLOG_SINGLE_REC_FLAG);
    }

    if (single_rec) {
      if (recv_single_rec(ptr, end_ptr)) {
        return;
      }

    } else if (recv_multi_rec(ptr, end_ptr)) {
      return;
    }
  }
}
```

레코드 하나짜리 mtr 이다.

`storage` / `innobase` / `log` / `log0recv.cc` L2871-L2969 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0recv.cc#L2871-L2969))

```cpp
// log0recv.cc L2871-L2969
static bool recv_single_rec(const byte *ptr, const byte *end_ptr) {
  /* The mtr did not modify multiple pages */

  lsn_t old_lsn = recv_sys->recovered_lsn;

  /* Try to parse a log record, fetching its type, space id,
  page no, and a pointer to the body of the log record */

  const byte *body;
  mlog_id_t type;
  page_no_t page_no;
  space_id_t space_id;

  ulint len =
      recv_parse_log_rec(&type, ptr, end_ptr, &space_id, &page_no, &body);

  if (recv_sys->found_corrupt_log) {
    recv_report_corrupt_log(ptr, type, space_id, page_no);

#ifdef UNIV_HOTBACKUP
    return true;
#endif /* UNIV_HOTBACKUP */

  } else if (len == 0 || recv_sys->found_corrupt_fs) {
    return true;
  }

  lsn_t new_recovered_lsn;

  new_recovered_lsn = recv_calc_lsn_on_data_add(old_lsn, len);

  if (new_recovered_lsn > recv_sys->scanned_lsn) {
    /* The log record filled a log block, and we
    require that also the next log block should
    have been scanned in */

    return true;
  }

  recv_previous_parsed_rec_type = type;
  recv_previous_parsed_rec_is_multi = 0;
  recv_previous_parsed_rec_offset = recv_sys->recovered_offset;

  recv_sys->recovered_offset += len;
  recv_sys->recovered_lsn = new_recovered_lsn;

  recv_track_changes_of_recovered_lsn();

  if (recv_update_bytes_to_ignore_before_checkpoint(len)) {
    return false;
  }

  switch (type) {
    case MLOG_DUMMY_RECORD:
      /* Do nothing */
      break;

#ifdef UNIV_LOG_LSN_DEBUG
    case MLOG_LSN:
      /* Do not add these records to the hash table.
      The page number and space id fields are misused
      for something else. */
      break;
#endif /* UNIV_LOG_LSN_DEBUG */

    default:

      if (recv_recovery_on
#ifndef UNIV_HOTBACKUP
          && (space_id == TRX_SYS_SPACE ||
              fil_tablespace_lookup_for_recovery(space_id))
#endif /* !UNIV_HOTBACKUP */
      ) {
        recv_add_to_hash_table(type, space_id, page_no, body, ptr + len,
                               old_lsn, recv_sys->recovered_lsn);
      }

      [[fallthrough]];

    case MLOG_INDEX_LOAD:
    case MLOG_FILE_DELETE:
    case MLOG_FILE_RENAME:
    case MLOG_FILE_CREATE:
    case MLOG_FILE_EXTEND:
    case MLOG_TABLE_DYNAMIC_META:

      /* These were already handled by
      recv_parse_log_rec() and
      recv_parse_or_apply_log_rec_body(). */

      DBUG_PRINT("ib_log",
                 ("scan " LSN_PF ": log rec %s"
                  " len " ULINTPF " " PAGE_ID_PF,
                  old_lsn, get_mlog_string(type), len, space_id, page_no));
      break;
  }

  return false;
}
```

여럿짜리 mtr 은 두 번 훑는다. 첫 바퀴는 끝 표시까지 모두 있는지 확인만 하고, 둘째 바퀴에서 해시에 넣는다.

`storage` / `innobase` / `log` / `log0recv.cc` L2975-L3131 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0recv.cc#L2975-L3131))

```cpp
// log0recv.cc L2975-L3131
static bool recv_multi_rec(const byte *ptr, const byte *end_ptr) {
  /* Check that all the records associated with the single mtr
  are included within the buffer */

  ulint n_recs = 0;
  ulint total_len = 0;

  for (;;) {
    mlog_id_t type = MLOG_BIGGEST_TYPE;
    const byte *body;
    page_no_t page_no = 0;
    space_id_t space_id = 0;

    ulint len =
        recv_parse_log_rec(&type, ptr, end_ptr, &space_id, &page_no, &body);

    if (recv_sys->found_corrupt_log) {
      recv_report_corrupt_log(ptr, type, space_id, page_no);

      return true;

    } else if (len == 0) {
      return true;

    } else if ((*ptr & MLOG_SINGLE_REC_FLAG)) {
      recv_sys->found_corrupt_log = true;

      recv_report_corrupt_log(ptr, type, space_id, page_no);

      return true;

    } else if (recv_sys->found_corrupt_fs) {
      return true;
    }

    recv_sys->save_rec(n_recs, space_id, page_no, type, body, len);

    recv_previous_parsed_rec_type = type;

    recv_previous_parsed_rec_offset = recv_sys->recovered_offset + total_len;

    recv_previous_parsed_rec_is_multi = 1;

    total_len += len;
    ++n_recs;

    ptr += len;

    if (type == MLOG_MULTI_REC_END) {
      DBUG_PRINT("ib_log", ("scan " LSN_PF ": multi-log end total_len " ULINTPF
                            " n=" ULINTPF,
                            recv_sys->recovered_lsn, total_len, n_recs));

      break;
    }

    DBUG_PRINT("ib_log",
               ("scan " LSN_PF ": multi-log rec %s len " ULINTPF " " PAGE_ID_PF,
                recv_sys->recovered_lsn, get_mlog_string(type), len, space_id,
                page_no));
  }

  lsn_t new_recovered_lsn =
      recv_calc_lsn_on_data_add(recv_sys->recovered_lsn, total_len);

  if (new_recovered_lsn > recv_sys->scanned_lsn) {
    /* The log record filled a log block, and we require
    that also the next log block should have been scanned in */

    return true;
  }

  /* Add all the records to the hash table */

  ptr = recv_sys->buf + recv_sys->recovered_offset;

  for (ulint i = 0; i < n_recs; i++) {
    lsn_t old_lsn = recv_sys->recovered_lsn;

    /* This will apply MLOG_FILE_ records. */
    space_id_t space_id = 0;
    page_no_t page_no = 0;

    mlog_id_t type = MLOG_BIGGEST_TYPE;

    const byte *body = nullptr;
    size_t len = 0;

    /* Avoid parsing if we have the record saved already. */
    if (!recv_sys->get_saved_rec(i, space_id, page_no, type, body, len)) {
      len = recv_parse_log_rec(&type, ptr, end_ptr, &space_id, &page_no, &body);
    }

    if (recv_sys->found_corrupt_log &&
        !recv_report_corrupt_log(ptr, type, space_id, page_no)) {
      return true;

    } else if (recv_sys->found_corrupt_fs) {
      return true;
    }

    ut_a(len != 0);
    ut_a(!(*ptr & MLOG_SINGLE_REC_FLAG));

    recv_sys->recovered_offset += len;

    recv_sys->recovered_lsn = recv_calc_lsn_on_data_add(old_lsn, len);

    const bool apply = !recv_update_bytes_to_ignore_before_checkpoint(len);

    switch (type) {
      case MLOG_MULTI_REC_END:
        recv_track_changes_of_recovered_lsn();
        /* Found the end mark for the records */
        return false;

#ifdef UNIV_LOG_LSN_DEBUG
      case MLOG_LSN:
        /* Do not add these records to the hash table.
        The page number and space id fields are misused
        for something else. */
        break;
#endif /* UNIV_LOG_LSN_DEBUG */

      case MLOG_FILE_DELETE:
      case MLOG_FILE_CREATE:
      case MLOG_FILE_RENAME:
      case MLOG_FILE_EXTEND:
      case MLOG_TABLE_DYNAMIC_META:
        /* case MLOG_TRUNCATE: Disabled for WL6378 */
        /* These were already handled by
        recv_parse_or_apply_log_rec_body(). */
        break;

      default:

        if (!apply) {
          break;
        }

        if (recv_recovery_on
#ifndef UNIV_HOTBACKUP
            && (space_id == TRX_SYS_SPACE ||
                fil_tablespace_lookup_for_recovery(space_id))
#endif /* !UNIV_HOTBACKUP */
        ) {

          recv_add_to_hash_table(type, space_id, page_no, body, ptr + len,
                                 old_lsn, new_recovered_lsn);
        }
    }

    ptr += len;
  }

  return false;
}
```

해시 테이블에 넣는다.

`storage` / `innobase` / `log` / `log0recv.cc` L2275-L2363 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0recv.cc#L2275-L2363))

```cpp
// log0recv.cc L2275-L2363
/** Adds a new log record to the hash table of log records.
@param[in]      type            log record type
@param[in]      space_id        Tablespace id
@param[in]      page_no         page number
@param[in]      body            log record body
@param[in]      rec_end         log record end
@param[in]      start_lsn       start lsn of the mtr
@param[in]      end_lsn         end lsn of the mtr */
static void recv_add_to_hash_table(mlog_id_t type, space_id_t space_id,
                                   page_no_t page_no, const byte *body,
                                   const byte *rec_end, lsn_t start_lsn,
                                   lsn_t end_lsn) {
  ut_ad(type != MLOG_FILE_DELETE);
  ut_ad(type != MLOG_FILE_CREATE);
  ut_ad(type != MLOG_FILE_RENAME);
  ut_ad(type != MLOG_FILE_EXTEND);
  ut_ad(type != MLOG_DUMMY_RECORD);
  ut_ad(type != MLOG_INDEX_LOAD);

  recv_sys_t::Space *space;

  space = recv_get_page_map(space_id, true);

  recv_t *recv;

  recv = static_cast<recv_t *>(mem_heap_alloc(space->m_heap, sizeof(*recv)));

  recv->type = type;
  recv->end_lsn = end_lsn;
  recv->len = rec_end - body;
  recv->start_lsn = start_lsn;

  auto it = space->m_pages.find(page_no);

  recv_addr_t *recv_addr;

  if (it != space->m_pages.end()) {
    recv_addr = it->second;

  } else {
    recv_addr = static_cast<recv_addr_t *>(
        mem_heap_alloc(space->m_heap, sizeof(*recv_addr)));

    recv_addr->space = space_id;
    recv_addr->page_no = page_no;
    recv_addr->state = RECV_NOT_PROCESSED;

    UT_LIST_INIT(recv_addr->rec_list);

    using Value = recv_sys_t::Pages::value_type;

    space->m_pages.insert(it, Value{page_no, recv_addr});

    recv_sys->n_pages_to_recover.increment();
  }

  UT_LIST_ADD_LAST(recv_addr->rec_list, recv);

  recv_data_t **prev_field;

  prev_field = &recv->data;

  /* Store the log record body in chunks of less than UNIV_PAGE_SIZE:
  the heap grows into the buffer pool, and bigger chunks could not
  be allocated */

  while (rec_end > body) {
    ulint len = rec_end - body;

    if (len > RECV_DATA_BLOCK_SIZE) {
      len = RECV_DATA_BLOCK_SIZE;
    }

    recv_data_t *recv_data;

    recv_data = static_cast<recv_data_t *>(
        mem_heap_alloc(space->m_heap, sizeof(*recv_data) + len));

    *prev_field = recv_data;

    memcpy(recv_data + 1, body, len);

    prev_field = &recv_data->next;

    body += len;
  }

  *prev_field = nullptr;
}
```

## 동작 흐름

```text
 recv_parse_log_recs (L3135)
 L3138  for (;;)
 L3139    ptr = buf + recovered_offset,  end_ptr = buf + len
 L3143    ptr == end_ptr 면 return               더 파싱할 것이 없다
 L3157    single_rec = 첫 바이트 & MLOG_SINGLE_REC_FLAG(128)
 L3161    단일 -> recv_single_rec, 다중 -> recv_multi_rec
          true 가 오면 return (데이터 부족 또는 손상)

 recv_single_rec (L2871)
 L2885  len = recv_parse_log_rec                  0 이면 레코드가 아직 다 안 왔다
 L2900  new_recovered_lsn 계산
 L2902  scanned_lsn 을 넘으면 return true        다음 블록을 기다린다
 L2914  recovered_offset += len, recovered_lsn = new
 L2919  체크포인트 앞 바이트면 건너뛴다
 L2944  recv_recovery_on 이고 공간이 알려져 있으면 recv_add_to_hash_table
          start_lsn = old_lsn, end_lsn = recovered_lsn

 recv_multi_rec (L2975)
 L2982  첫 바퀴: MLOG_MULTI_REC_END 까지 recv_parse_log_rec, save_rec 로 기억
          len == 0 이면 return true                mtr 이 아직 다 안 왔다
          중간에 SINGLE_REC_FLAG 가 보이면 손상
 L3037  mtr 전체의 new_recovered_lsn
 L3040  scanned_lsn 을 넘으면 return true
 L3051  둘째 바퀴: 레코드마다 recv_add_to_hash_table
          start_lsn = 레코드마다 old_lsn, end_lsn = mtr 전체의 끝 (new_recovered_lsn)
          MLOG_MULTI_REC_END 에서 return false
```

`recv_parse_log_rec` 는 레코드를 **적용하지 않고 파싱만** 한다. `recv_parse_or_apply_log_rec_body` 에 block 을 `nullptr` 로 넘기면 길이만 계산해 돌려준다(L2802-L2804). 적용은 같은 함수를 block 을 주고 다시 부르는 [09] 에서 한다.

```text
 해시 테이블의 모양 (log0recv.h L259-L402)

 recv_sys->spaces : unordered_map<space_id, Space>
   Space { m_heap, m_pages : unordered_map<page_no, recv_addr_t *> }
     recv_addr_t { state, space, page_no, rec_list }
       rec_list: recv_t -> recv_t -> recv_t      LSN 순 (파싱 순서대로 끝에 붙인다)
         recv_t { type, len, data, start_lsn, end_lsn }
           data: recv_data_t -> recv_data_t      본문을 RECV_DATA_BLOCK_SIZE 조각으로

 새 recv_addr_t 는 state = RECV_NOT_PROCESSED 로 만들고
 n_pages_to_recover 를 1 올린다 (L2320, L2328)
 [09] 가 한 페이지를 끝낼 때마다 1 내린다. [08] 은 이것이 0 이 되기를 기다린다
```

```text
 recv_addr_t 의 상태 (log0recv.h L286)

 RECV_NOT_PROCESSED  --(recv_read_in_area 가 읽기 요청)-->  RECV_BEING_READ
 RECV_BEING_READ     --([09] 시작)-->                       RECV_BEING_PROCESSED
 RECV_BEING_PROCESSED --([09] 끝)-->                        RECV_PROCESSED
 RECV_NOT_PROCESSED  --(테이블스페이스가 없음, [08])-->     RECV_DISCARDED
```

## 결과가 쓰이는 곳

```text
 recv_sys->spaces
      --> [08] 이 space 별, page 별로 돈다
      --> [09] 가 페이지의 rec_list 를 앞에서부터 적용한다
 recv_sys->recovered_lsn
      --> 완전한 mtr 까지만 전진한다. [02] 가 log.recovered_lsn 으로 쓴다
 recv_heap_used()
      --> [05] 가 max_memory 와 비교해 중간 적용을 끼운다
```

## 다루지 않는 것

`recv_parse_or_apply_log_rec_body` 의 mlog 타입별 분기(수백 줄), `mlog_parse_initial_log_record` 의 가변 길이 정수 인코딩, `MLOG_FILE_CREATE/RENAME/DELETE/EXTEND` 가 파싱 단계에서 곧바로 처리되는 방식, 손상 보고(`recv_report_corrupt_log`), `save_rec`/`get_saved_rec` 캐시는 이 함수의 곁가지라 요약만 했다. mlog 타입 목록은 [redo 로그 파일과 mlog 타입](../../structure/redo-log-files/README.md)에 있다.
