# row_log_online_op

상위: [온라인 DDL](../README.md)

**빌드 중인 보조 인덱스에 대한 다른 연결의 변경을 트리 대신 로그에 적는 함수다.** 이 함수는 ALTER 연결이 아니라 DML 을 하는 연결 스레드에서 돈다. 새 인덱스의 `online_status` 가 `ONLINE_INDEX_CREATION` 인 동안 INSERT 는 `ROW_OP_INSERT` 한 줄, DELETE 는 `ROW_OP_DELETE` 한 줄, UPDATE 는 둘 다를 `row_log_t` 의 꼬리 블록에 붙인다. 블록이 차면 임시 파일로 내보내고, 파일이 `innodb_online_alter_log_max_size` 를 넘으면 인덱스를 깨진 것으로 표시해 ALTER 를 실패시킨다.

## 위치

`storage` / `innobase` / `row` / `row0log.cc` L279-L406 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0log.cc#L279-L406))

## 실제 코드

`storage` / `innobase` / `row` / `row0log.cc` L279-L406 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0log.cc#L279-L406))

```cpp
// row0log.cc L279-L406
void row_log_online_op(
    dict_index_t *index,   /*!< in/out: index, S or X latched */
    const dtuple_t *tuple, /*!< in: index tuple */
    trx_id_t trx_id)       /*!< in: transaction ID for insert,
                           or 0 for delete */
{
  byte *b;
  ulint extra_size;
  ulint size;
  ulint mrec_size;
  ulint avail_size;
  row_log_t *log;

  ut_ad(dtuple_validate(tuple));
  ut_ad(dtuple_get_n_fields(tuple) == dict_index_get_n_fields(index));
  ut_ad(rw_lock_own(dict_index_get_lock(index), RW_LOCK_S) ||
        rw_lock_own(dict_index_get_lock(index), RW_LOCK_X));
  ut_ad(!index->is_clustered());

  if (index->is_corrupted()) {
    return;
  }

  ut_ad(dict_index_is_online_ddl(index));

  /* Compute the size of the record. This differs from ddl::buf_encode(),
  because here we do not encode extra_size+1 (and reserve 0 as the
  end-of-chunk marker). */

  /* Secondary index, version doesn't matter */
  size = rec_get_serialize_size(index, tuple->fields, tuple->n_fields, nullptr,
                                &extra_size, MAX_ROW_VERSION);
  ut_ad(size >= extra_size);
  ut_ad(size <= sizeof log->tail.buf);

  mrec_size = ROW_LOG_HEADER_SIZE + (extra_size >= 0x80) + size +
              (trx_id ? DATA_TRX_ID_LEN : 0);

  log = index->online_log;
  mutex_enter(&log->mutex);

  if (trx_id > log->max_trx) {
    log->max_trx = trx_id;
  }

  if (!row_log_block_allocate(log->tail)) {
    log->error = DB_OUT_OF_MEMORY;
    goto err_exit;
  }

  UNIV_MEM_INVALID(log->tail.buf, sizeof log->tail.buf);

  ut_ad(log->tail.bytes < srv_sort_buf_size);
  avail_size = srv_sort_buf_size - log->tail.bytes;

  if (mrec_size > avail_size) {
    b = log->tail.buf;
  } else {
    b = log->tail.block + log->tail.bytes;
  }

  if (trx_id != 0) {
    *b++ = ROW_OP_INSERT;
    trx_write_trx_id(b, trx_id);
    b += DATA_TRX_ID_LEN;
  } else {
    *b++ = ROW_OP_DELETE;
  }

  if (extra_size < 0x80) {
    *b++ = (byte)extra_size;
  } else {
    ut_ad(extra_size < 0x8000);
    *b++ = (byte)(0x80 | (extra_size >> 8));
    *b++ = (byte)extra_size;
  }

  rec_serialize_dtuple(b + extra_size, index, tuple->fields, tuple->n_fields,
                       nullptr, MAX_ROW_VERSION);
  b += size;

  if (mrec_size >= avail_size) {
    dberr_t err;
    IORequest request(IORequest::ROW_LOG | IORequest::WRITE);
    const os_offset_t byte_offset =
        (os_offset_t)log->tail.blocks * srv_sort_buf_size;

    if (byte_offset + srv_sort_buf_size >= srv_online_max_size) {
      goto write_failed;
    }

    if (mrec_size == avail_size) {
      ut_ad(b == &log->tail.block[srv_sort_buf_size]);
    } else {
      ut_ad(b == log->tail.buf + mrec_size);
      memcpy(log->tail.block + log->tail.bytes, log->tail.buf, avail_size);
    }

    UNIV_MEM_ASSERT_RW(log->tail.block, srv_sort_buf_size);

    if (!row_log_tmpfile(log)) {
      log->error = DB_OUT_OF_MEMORY;
      goto err_exit;
    }

    err = os_file_write_int_fd(request, "(modification log)", log->file.get(),
                               log->tail.block, byte_offset, srv_sort_buf_size);

    log->tail.blocks++;
    if (err != DB_SUCCESS) {
    write_failed:
      /* We set the flag directly instead of
      invoking dict_set_corrupted() here,
      because the index is not "public" yet. */
      index->type |= DICT_CORRUPT;
    }
    UNIV_MEM_INVALID(log->tail.block, srv_sort_buf_size);
    memcpy(log->tail.block, log->tail.buf + avail_size, mrec_size - avail_size);
    log->tail.bytes = mrec_size - avail_size;
  } else {
    log->tail.bytes += mrec_size;
    ut_ad(b == log->tail.block + log->tail.bytes);
  }

  UNIV_MEM_INVALID(log->tail.buf, sizeof log->tail.buf);
err_exit:
  mutex_exit(&log->mutex);
}
```

어디서 이 함수로 들어오는지가 핵심이다. 보조 인덱스에 쓰는 쪽은 먼저 인덱스 상태를 본다.

`storage` / `innobase` / `include` / `row0log.ic` L48-L74 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/row0log.ic#L48-L74))

```cpp
// row0log.ic L48-L74
static inline bool row_log_online_op_try(dict_index_t *index,
                                         const dtuple_t *tuple,
                                         trx_id_t trx_id) {
  ut_ad(rw_lock_own_flagged(dict_index_get_lock(index),
                            RW_LOCK_FLAG_S | RW_LOCK_FLAG_X | RW_LOCK_FLAG_SX));

  switch (dict_index_get_online_status(index)) {
    case ONLINE_INDEX_COMPLETE:
      /* This is a normal index. Do not log anything.
      The caller must perform the operation on the
      index tree directly. */
      return (false);
    case ONLINE_INDEX_CREATION:
      /* The index is being created online. Log the
      operation. */
      row_log_online_op(index, tuple, trx_id);
      break;
    case ONLINE_INDEX_ABORTED:
    case ONLINE_INDEX_ABORTED_DROPPED:
      /* The index was created online, but the operation was
      aborted. Do not log the operation and tell the caller
      to skip the operation. */
      break;
  }

  return (true);
}
```

INSERT 의 보조 인덱스 삽입이다. 인덱스가 아직 커밋되지 않았으면 `index->lock` 을 S(또는 SX)로 잡고 상태를 본다.

`storage` / `innobase` / `row` / `row0ins.cc` L2883-L2902 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0ins.cc#L2883-L2902))

```cpp
// row0ins.cc L2883-L2902
  bool check = !index->is_committed();

  DBUG_EXECUTE_IF("idx_mimic_not_committed", {
    check = true;
    mode = BTR_MODIFY_TREE;
  });

  if (check) {
    DEBUG_SYNC(thr_get_trx(thr)->mysql_thd, "row_ins_sec_index_enter");
    if (mode == BTR_MODIFY_LEAF) {
      search_mode |= BTR_ALREADY_S_LATCHED;
      mtr_s_lock(dict_index_get_lock(index), &mtr, UT_LOCATION_HERE);
    } else {
      mtr_sx_lock(dict_index_get_lock(index), &mtr, UT_LOCATION_HERE);
    }

    if (row_log_online_op_try(index, entry, thr_get_trx(thr)->id)) {
      goto func_exit;
    }
  }
```

UPDATE 는 옛 키의 DELETE 와 새 키의 INSERT 를 차례로 적는다.

`storage` / `innobase` / `row` / `row0upd.cc` L2221-L2249 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0upd.cc#L2221-L2249))

```cpp
// row0upd.cc L2221-L2249
  if (!index->is_committed()) {
    /* The index->online_status may change if the index is
    or was being created online, but not committed yet. It
    is protected by index->lock. */

    mtr_s_lock(dict_index_get_lock(index), &mtr, UT_LOCATION_HERE);

    switch (dict_index_get_online_status(index)) {
      case ONLINE_INDEX_COMPLETE:
        /* This is a normal index. Do not log anything.
        Perform the update on the index tree directly. */
        break;
      case ONLINE_INDEX_CREATION:
        /* Log a DELETE and optionally INSERT. */
        row_log_online_op(index, entry, 0);

        if (!node->is_delete) {
          mem_heap_empty(heap);
          entry =
              row_build_index_entry(node->upd_row, node->upd_ext, index, heap);
          ut_a(entry);
          row_log_online_op(index, entry, trx->id);
        }
        [[fallthrough]];
      case ONLINE_INDEX_ABORTED:
      case ONLINE_INDEX_ABORTED_DROPPED:
        mtr_commit(&mtr);
        goto func_exit;
    }
```

로그 한 줄이 들어가는 구조체다. 쓰는 쪽(`tail`)과 읽는 쪽(`head`)이 따로 있다.

`storage` / `innobase` / `row` / `row0log.cc` L185-L233 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0log.cc#L185-L233))

```cpp
// row0log.cc L185-L233
struct row_log_t {
  /** File descriptor */
  ddl::Unique_os_file_descriptor file;

  /** Mutex protecting error, max_trx and tail */
  ib_mutex_t mutex;

  /** Map of page numbers of off-page columns that have been freed during
  table-rebuilding ALTER TABLE (row_log_table_*); protected by index->lock
  X-latch only */
  page_no_map *blobs;

  /** Table that is being rebuilt, or NULL when this is a secondary index that
  is being created online */
  dict_table_t *table;

  /** Whether the definition of the PRIMARY KEY has remained the same */
  bool same_pk;

  /** Default values of added columns, or NULL */
  const dtuple_t *add_cols;

  /** Mapping of old column numbers to new ones, or NULL if !table */
  const ulint *col_map;

  /** Error that occurred during online table rebuild */
  dberr_t error;

  /** Biggest observed trx_id in row_log_online_op(); protected by mutex and
  index->lock S-latch, or by index->lock X-latch only */
  trx_id_t max_trx;

  /** writer context; protected by mutex and index->lock S-latch, or by
  index->lock X-latch only */
  row_log_buf_t tail;

  /** Reader context; protected by MDL only; modifiable by
  row_log_apply_ops() */
  row_log_buf_t head;

  /** number of non-virtual column in old table */
  size_t n_old_col;

  /** number of virtual column in old table */
  size_t n_old_vcol;

  /** Where to create temporary file during log operation */
  const char *path;
};
```

## 동작 흐름

```text
 DML 연결 (보조 인덱스 index 에 entry 를 넣거나 지우려 한다)

 row0ins.cc L2883  index 가 아직 커밋 전이면 (온라인 빌드 중이거나 중단됨)
 row0ins.cc L2894    mtr_s_lock(index->lock)   (BTR_MODIFY_TREE 면 SX)
 row0ins.cc L2899    row_log_online_op_try(index, entry, trx->id)
                       COMPLETE        false -> 트리에 직접 삽입 (보통 경로)
                       CREATION        [07] row_log_online_op -> true -> 트리는 건너뛴다
                       ABORTED(_DROPPED)                     true -> 아무것도 안 한다

 row_log_online_op
 L298  인덱스가 이미 깨졌으면 그냥 돌아간다
 L314  mrec_size = 헤더 + extra_size 길이 + 레코드 + (INSERT 면 trx_id 6 바이트)
 L318  log->mutex
 L320  max_trx 갱신                     나중에 인덱스의 trx_id 로 쓰인다 (ddl0ctx.cc L490-L494)
 L324  꼬리 블록이 없으면 srv_sort_buf_size 만큼 할당
 L334  남은 자리가 모자라면 tail.buf (임시) 에 먼저 쓴다
 L340  op 바이트: ROW_OP_INSERT + trx_id  또는  ROW_OP_DELETE
 L348  extra_size (1 또는 2 바이트)
 L356  rec_serialize_dtuple             레코드를 직렬화
 L360  블록이 찼으면
         L366  파일 크기가 srv_online_max_size 에 닿으면 write_failed -> DICT_CORRUPT
         L379  임시 파일을 처음이면 만든다
         L384  블록을 파일 끝 (tail.blocks * srv_sort_buf_size) 에 쓴다
         L396  넘친 나머지를 새 블록 앞으로
 L399  아니면 tail.bytes += mrec_size
 L405  mutex 해제
```

```text
 row log 한 줄 (row0log.cc L340-L358)

 +----------+--------------+---------------+------------------------------+
 | op 1B    | trx_id 6B    | extra_size    | 직렬화된 인덱스 레코드       |
 | INSERT   | (INSERT 만)  | 1B 또는 2B    | rec_serialize_dtuple         |
 +----------+--------------+---------------+------------------------------+
 | DELETE   | (없음)       |               |                              |
 +----------+--------------+---------------+------------------------------+

 UPDATE 한 번 = DELETE(옛 키) + INSERT(새 키, trx_id)   row0upd.cc L2235, L2242
```

```text
 row_log_t 의 두 커서 (row0log.cc L185-L233)

 임시 파일  [ 블록0 ][ 블록1 ][ 블록2 ]          메모리  [ tail.block (쓰는 중) ]
              ^ head.blocks                                ^ tail.bytes
              읽는 쪽 [08]                                  쓰는 쪽 [07]
              head.bytes 만큼 소비                          다 차면 파일 끝에 붙이고 tail.blocks++

 head.blocks == tail.blocks 이면 [08] 은 파일 대신 tail.block 을 바로 읽는다
 두 쪽이 다 따라잡으면 파일을 0 으로 자른다 (row0log.cc L3575-L3585)
 tail 은 mutex 와 index->lock S 로, head 는 MDL 로 보호된다 (L213-L223 주석)
```

## 결과가 쓰이는 곳

```text
 row log 블록과 임시 파일
      --> [08] row_log_apply 가 head 부터 읽어 새 인덱스 트리에 적용한다
 log->max_trx
      --> Context::note_max_trx_id 가 새 인덱스의 trx_id 를 이 값 이상으로 올린다
          (ddl0ctx.cc L479-L497)
 DICT_CORRUPT (로그가 너무 큼)
      --> [08] 이 DB_ONLINE_LOG_TOO_BIG 으로 바꾸고 ALTER 가 실패한다 (row0log.cc L3786-L3790)
```

## 다루지 않는 것

롤백(`row0uins.cc`, `row0umod.cc`)이 같은 함수를 부르는 경로, 재구성용 `row_log_table_insert` / `update` / `delete`, 레코드 직렬화 형식(`rec_serialize_dtuple`), 다중 값 인덱스의 여러 엔트리 처리는 이 흐름의 곁가지라 요약만 했다. 보조 인덱스 삽입의 나머지는 [행 쓰기](../../row-insert/README.md)와 [B+Tree 삽입과 분할](../../btree-insert/README.md)에 있다.
