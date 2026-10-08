# btr_cur_ins_lock_and_undo

상위: [B+Tree 삽입과 분할](../README.md)

**삽입이 페이지에 닿기 직전에 지나는 두 관문이다.** 첫째는 잠금이다. 새 레코드가 들어갈 gap(커서 레코드와 다음 레코드 사이)을 다른 트랜잭션이 잠갔는지 보고, 그렇다면 insert intention 잠금을 대기열에 넣고 `DB_LOCK_WAIT` 로 돌아간다. 둘째는 undo 다. 클러스터드 인덱스일 때만 insert undo 레코드를 쓰고, 그 위치를 **DB_ROLL_PTR** 로 엔트리에 채운다. 이 두 갈래가 각각 [레코드 잠금과 교착](../../record-lock/README.md)과 [일관 읽기(MVCC)](../../mvcc-read/README.md)로 이어진다. [03] 과 [07] 이 모두 부른다.

## 위치

`storage` / `innobase` / `btr` / `btr0cur.cc` L2554-L2630 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/btr/btr0cur.cc#L2554-L2630))

## 실제 코드

`storage` / `innobase` / `btr` / `btr0cur.cc` L2554-L2630 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/btr/btr0cur.cc#L2554-L2630))

```cpp
// btr0cur.cc L2554-L2630
[[nodiscard]] static inline dberr_t btr_cur_ins_lock_and_undo(
    ulint flags,       /*!< in: undo logging and locking flags: if
                       not zero, the parameters index and thr
                       should be specified */
    btr_cur_t *cursor, /*!< in: cursor on page after which to insert */
    dtuple_t *entry,   /*!< in/out: entry to insert */
    que_thr_t *thr,    /*!< in: query thread or NULL */
    mtr_t *mtr,        /*!< in/out: mini-transaction */
    bool *inherit)     /*!< out: true if the inserted new record maybe
                        should inherit LOCK_GAP type locks from the
                        successor record */
{
  dict_index_t *index;
  dberr_t err = DB_SUCCESS;
  rec_t *rec;
  roll_ptr_t roll_ptr;

  /* Check if we have to wait for a lock: enqueue an explicit lock
  request if yes */

  rec = btr_cur_get_rec(cursor);
  index = cursor->index;

  ut_ad(!dict_index_is_online_ddl(index) || index->is_clustered() ||
        (flags & BTR_CREATE_FLAG));

  /* Check if there is predicate or GAP lock preventing the insertion */
  if (!(flags & BTR_NO_LOCKING_FLAG)) {
    if (dict_index_is_spatial(index)) {
      lock_prdt_t prdt;
      rtr_mbr_t mbr;

      rtr_get_mbr_from_tuple(entry, &mbr);

      /* Use on stack MBR variable to test if a lock is
      needed. If so, the predicate (MBR) will be allocated
      from lock heap in lock_prdt_insert_check_and_lock() */
      lock_init_prdt_from_mbr(&prdt, &mbr, 0, nullptr);

      err = lock_prdt_insert_check_and_lock(
          flags, rec, btr_cur_get_block(cursor), index, thr, mtr, &prdt);
      *inherit = false;
    } else {
      err = lock_rec_insert_check_and_lock(
          flags, rec, btr_cur_get_block(cursor), index, thr, mtr, inherit);
    }
  }

  if (err != DB_SUCCESS || !index->is_clustered() ||
      dict_index_is_ibuf(index)) {
    return (err);
  }

  err = trx_undo_report_row_operation(flags, TRX_UNDO_INSERT_OP, thr, index,
                                      entry, nullptr, 0, nullptr, nullptr,
                                      &roll_ptr);
  if (err != DB_SUCCESS) {
    return (err);
  }

  /* Now we can fill in the roll ptr field in entry
  (except if table is intrinsic) */

  if (!(flags & BTR_KEEP_SYS_FLAG) && !index->table->is_intrinsic()) {
    /* Roll_ptr is zero during copy alter table.
    So pretend to be freshly inserted row. */
    if (index->table->skip_alter_undo) {
      ut_ad(roll_ptr == 0);
      roll_ptr = trx_undo_build_roll_ptr(true, 0, 0, 0);
      ut_ad(roll_ptr == (1ULL << 55));
    }

    row_upd_index_entry_sys_field(entry, index, DATA_ROLL_PTR, roll_ptr);
  }

  return (DB_SUCCESS);
}
```

잠금 갈래다. 다음 레코드에 잠금이 하나도 없으면 바로 통과한다. 있으면 insert intention 과 충돌하는 잠금이 있는지 본다.

`storage` / `innobase` / `lock` / `lock0lock.cc` L5076-L5127 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0lock.cc#L5076-L5127))

```cpp
// lock0lock.cc L5076-L5127
  const rec_t *next_rec = page_rec_get_next_const(rec);
  ulint heap_no = page_rec_get_heap_no(next_rec);

  {
    locksys::Shard_latch_guard guard{UT_LOCATION_HERE, block->get_page_id()};

    // ... (L5082-L5090 생략: assert 와 주석)
    if (!lock_rec_has_any(lock_sys->rec_hash, block->get_page_id(), heap_no)) {
      *inherit = false;
    } else {
      *inherit = true;

      /* If another transaction has an explicit lock request which locks
      the gap, waiting or granted, on the successor, the insert has to wait.

      An exception is the case where the lock by the another transaction
      is a gap type lock which it placed to wait for its turn to insert. We
      do not consider that kind of a lock conflicting with our insert. This
      eliminates an unnecessary deadlock which resulted when 2 transactions
      had to wait for their insert. Both had waiting gap type lock requests
      on the successor, which produced an unnecessary deadlock. */

      const ulint type_mode = LOCK_X | LOCK_GAP | LOCK_INSERT_INTENTION;

      const auto conflicting =
          lock_rec_other_has_conflicting(type_mode, block, heap_no, trx);

      /* LOCK_INSERT_INTENTION locks can not be allowed to bypass waiting locks,
      because they allow insertion of a record which splits the gap which would
      lead to duplication of the waiting lock, violating the constraint that
      each transaction can wait for at most one lock at any given time */
      ut_a(!conflicting.bypassed);

      if (conflicting.wait_for != nullptr) {
        RecLock rec_lock(thr, index, block, heap_no, type_mode);

        trx_mutex_enter(trx);

        err = rec_lock.add_to_waitq(conflicting.wait_for);

        trx_mutex_exit(trx);
      }
    }
  } /* Shard_latch_guard */
```

undo 갈래다. 이 함수는 **자기 mtr** 을 따로 연다. 호출자의 mtr 과는 별개로 undo 페이지를 고치고 먼저 커밋한다.

`storage` / `innobase` / `trx` / `trx0rec.cc` L2153-L2215 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0rec.cc#L2153-L2215))

```cpp
// trx0rec.cc L2153-L2215
  if (flags & BTR_NO_UNDO_LOG_FLAG) {
    *roll_ptr = 0;

    return (DB_SUCCESS);
  }

  ut_ad(thr);
  ut_ad(!srv_read_only_mode);
  ut_ad((op_type != TRX_UNDO_INSERT_OP) || (clust_entry && !update && !rec));

  trx = thr_get_trx(thr);

  bool is_temp_table = index->table->is_temporary();

  /* Temporary tables do not go into INFORMATION_SCHEMA.TABLES,
  so do not bother adding it to the list of modified tables by
  the transaction - this list is only used for maintaining
  INFORMATION_SCHEMA.TABLES.UPDATE_TIME. */
  if (!is_temp_table) {
    trx->mod_tables.insert(index->table);
  }

  /* If trx is read-only then only temp-tables can be written. */
  ut_ad(!trx->read_only || is_temp_table);

  /* If this is a temp-table then we assign temporary rseg. */
  if (is_temp_table && trx->rsegs.m_noredo.rseg == nullptr) {
    trx_assign_rseg_temp(trx);
  }

  mtr_start(&mtr);

  if (is_temp_table) {
    /* If object is temporary, disable REDO logging that
    is done to track changes done to UNDO logs. This is
    feasible given that temporary tables and temporary
    undo logs are not restored on restart. */
    undo_ptr = &trx->rsegs.m_noredo;
    mtr.set_log_mode(MTR_LOG_NO_REDO);
  } else {
    undo_ptr = &trx->rsegs.m_redo;
  }

  mutex_enter(&trx->undo_mutex);

#ifdef UNIV_DEBUG
  if (srv_inject_too_many_concurrent_trxs) {
    err = DB_TOO_MANY_CONCURRENT_TRXS;
    goto err_exit;
  }
#endif /* UNIV_DEBUG */

  switch (op_type) {
    case TRX_UNDO_INSERT_OP:
      undo = undo_ptr->insert_undo;

      if (undo == nullptr) {
        err = trx_undo_assign_undo(trx, undo_ptr, TRX_UNDO_INSERT);
        undo = undo_ptr->insert_undo;

        if (undo == nullptr) {
          /* Did not succeed */
          ut_ad(err != DB_SUCCESS);
```

`storage` / `innobase` / `trx` / `trx0rec.cc` L2242-L2260 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0rec.cc#L2242-L2260))

```cpp
// trx0rec.cc L2242-L2260
  page_no = undo->last_page_no;
  undo_block = buf_page_get_gen(page_id_t(undo->space, page_no),
                                undo->page_size, RW_X_LATCH, undo->guess_block,
                                Page_fetch::NORMAL, UT_LOCATION_HERE, &mtr);

  buf_block_dbg_add_level(undo_block, SYNC_TRX_UNDO_PAGE);

  do {
    page_t *undo_page;
    ulint offset;

    undo_page = buf_block_get_frame(undo_block);
    ut_ad(page_no == undo_block->page.id.page_no());

    switch (op_type) {
      case TRX_UNDO_INSERT_OP:
        offset = trx_undo_page_report_insert(undo_page, trx, index, clust_entry,
                                             &mtr);
        break;
```

`storage` / `innobase` / `trx` / `trx0rec.cc` L2306-L2323 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0rec.cc#L2306-L2323))

```cpp
// trx0rec.cc L2306-L2323
      /* Success */
      undo->guess_block = undo_block;
      mtr_commit(&mtr);

      undo->empty = false;
      undo->top_page_no = page_no;
      undo->top_offset = offset;
      undo->top_undo_no = trx->undo_no;

      trx->undo_no++;
      trx->undo_rseg_space = undo_ptr->rseg->space_id;

      mutex_exit(&trx->undo_mutex);

      *roll_ptr =
          trx_undo_build_roll_ptr(op_type == TRX_UNDO_INSERT_OP,
                                  undo_ptr->rseg->space_id, page_no, offset);
      return (DB_SUCCESS);
```

roll pointer 는 undo 레코드의 주소를 64비트 하나에 담는다.

`storage` / `innobase` / `include` / `trx0undo.ic` L45-L54 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/trx0undo.ic#L45-L54))

```cpp
// trx0undo.ic L45-L54
inline roll_ptr_t trx_undo_build_roll_ptr(bool is_insert, space_id_t space_id,
                                          page_no_t page_no, ulint offset) {
  ut_ad(offset < 65536);

  ulint id = (fsp_is_undo_tablespace(space_id) ? undo::id2num(space_id) : 0);

  roll_ptr_t roll_ptr = (roll_ptr_t)is_insert << 55 | (roll_ptr_t)id << 48 |
                        (roll_ptr_t)page_no << 16 | offset;
  return (roll_ptr);
}
```

## 동작 흐름

```text
 L2574  rec = 커서 레코드 (새 레코드는 이 뒤에 들어간다)
 L2581  BTR_NO_LOCKING_FLAG 가 없으면
 L2582    공간 인덱스면 lock_prdt_insert_check_and_lock
 L2597    아니면 lock_rec_insert_check_and_lock(flags, rec, block, index, thr, mtr, inherit)
            lock0lock.cc
            L5076  next_rec = rec 의 다음 레코드, heap_no = 그 heap 번호
            L5080  이 페이지의 잠금 샤드 래치
            L5091  next_rec 에 어떤 잠금도 없으면 inherit = false, 통과
            L5094  있으면 inherit = true
            L5106    type_mode = LOCK_X | LOCK_GAP | LOCK_INSERT_INTENTION
            L5108    lock_rec_other_has_conflicting                --> [레코드 잠금과 교착]
            L5117    충돌하면 RecLock::add_to_waitq -> DB_LOCK_WAIT
            L5134  세컨더리이고 호출자가 넘긴 *inherit 가 true 였으면 (inherit_in, L5074)
                     page_update_max_trx_id. [03] 은 true (btr0cur.cc L2691), [07] 은 false (L2954) 로 넘기고
                     [07] 은 삽입 뒤 btr0cur.cc L3042 에서 따로 올린다

 L2602  잠금이 실패했거나, 세컨더리거나, change buffer 트리면 여기서 끝   (세컨더리는 undo 없음)
 L2607  trx_undo_report_row_operation(flags, TRX_UNDO_INSERT_OP, ...)   trx0rec.cc L2116
            L2153  BTR_NO_UNDO_LOG_FLAG 면 roll_ptr = 0, 끝
            L2172  trx->mod_tables 에 테이블 추가
            L2183  mtr_start(&mtr)                          호출자와 다른 mtr
            L2190  임시 테이블이면 m_noredo 롤백 세그먼트, 아니면 m_redo (L2193)
            L2196  trx->undo_mutex
            L2207  insert_undo 가 없으면 trx_undo_assign_undo(TRX_UNDO_INSERT)
            L2243  마지막 undo 페이지를 X 래치로 가져온다    --> [버퍼 풀 페이지 획득]
            L2258  trx_undo_page_report_insert             undo 레코드 쓰기
            L2268  페이지에 안 들어가면 trx_undo_add_page 로 한 페이지 늘려 다시 (L2343)
            L2308  mtr_commit                                undo 페이지 변경이 먼저 확정
            L2313  top_undo_no = trx->undo_no, L2315 undo_no++
            L2320  roll_ptr = build(insert, rseg space, page_no, offset)
 L2617  BTR_KEEP_SYS_FLAG 가 없으면
 L2626    row_upd_index_entry_sys_field(entry, DATA_ROLL_PTR, roll_ptr)   엔트리의 DB_ROLL_PTR 칸
```

잠금 검사는 **다음 레코드**를 본다. InnoDB 의 gap 잠금은 레코드 앞쪽의 틈에 걸리므로, 새 레코드가 끼어들 틈은 다음 레코드의 잠금 목록에 있다.

```text
 gap 과 insert intention (키 10, 30 사이에 20 을 넣을 때)

   ... [10] ~~~~~~~~ gap ~~~~~~~~ [30] ...
         ^ 커서 rec              ^ next_rec, heap_no 는 여기서 (L5077)
                   ^ 20 이 들어갈 자리

 T2 가 [30] 에 gap 을 막는 잠금을 갖고 있으면
   T1 의 LOCK_X | LOCK_GAP | LOCK_INSERT_INTENTION 이 충돌 -> 대기열 -> DB_LOCK_WAIT
 [30] 에 잠금이 하나도 없으면 L5091 에서 바로 통과, 잠금 구조체도 만들지 않는다

 주석 (L5096-L5104): 다른 트랜잭션이 같은 gap 에 걸어 둔 insert intention 대기끼리는
   충돌로 보지 않는다. 두 삽입이 서로를 기다리는 불필요한 교착을 없애기 위해서다
```

undo 는 두 mtr 사이의 순서가 있다. undo 페이지를 고친 mtr 이 먼저 커밋되고, 인덱스 페이지를 고치는 호출자의 mtr 은 그 뒤에 커밋된다.

```text
 한 번의 클러스터드 삽입에 쓰이는 두 mtr (시간 순서)

 [01] mtr A start (L2439)
      [02] 리프까지 래치
      [04] trx_undo_report_row_operation
             mtr B start (trx0rec.cc L2183)
             undo 페이지 X 래치, insert undo 레코드 쓰기
             mtr B commit (L2308)            --> undo 페이지의 redo 가 먼저 log buffer 로
      [04] entry.DB_ROLL_PTR = roll_ptr
      [05] [06] 리프에 레코드 쓰기 (mtr A 에 redo 기록)
 [01] mtr A commit (L2620)                   --> 인덱스 페이지의 redo
```

```text
 roll_ptr 64비트 (trx0undo.ic L51-L52)

 bit 55       48 47                         16 15             0
 +----+--------+-----------------------------+----------------+
 | I  | undo   |         page_no             |    offset      |
 +----+--------+-----------------------------+----------------+
   I = 1 이면 insert undo (trx0rec.cc L2321 의 op_type == TRX_UNDO_INSERT_OP)
   undo = undo 테이블스페이스 번호 (시스템 테이블스페이스면 0, L49)
   offset < 65536 (L47)

 복사식 ALTER 중간 테이블은 roll_ptr 을 1 << 55 로 만든다 (btr0cur.cc L2620-L2623)
   "새로 삽입된 행인 척" 하는 값이다
```

## 결과가 쓰이는 곳

```text
 DB_LOCK_WAIT
      --> [03] 은 fail_err, [07] 은 그대로 반환 -> [01] mtr.commit -> [행 쓰기] 06 이 잠든다
 inherit
      --> [03] [07] 의 lock_update_insert 가 새 레코드에 gap 잠금을 물려준다
 insert undo 레코드
      --> 롤백과 [행 쓰기] 06 의 savepoint 되돌리기가 이 레코드로 새 레코드를 지운다
 entry 의 DB_ROLL_PTR
      --> 레코드에 그대로 들어가 [일관 읽기(MVCC)] 의 trx_undo_prev_version_build 가 따라간다
 trx->undo_no
      --> 다음 undo 번호. savepoint (trx_savept_take) 가 이 값을 기억한다
```

## 다루지 않는 것

공간 인덱스의 predicate 잠금(`lock_prdt_insert_check_and_lock`), 잠금 충돌 판정과 대기열의 내부(`lock_rec_other_has_conflicting`, `RecLock::add_to_waitq`), undo 세그먼트 할당(`trx_undo_assign_undo`), insert undo 레코드의 바이트 형식(`trx_undo_page_report_insert`), undo 페이지 확장 실패와 `DB_UNDO_RECORD_TOO_BIG` 는 곁가지다. 잠금은 [레코드 잠금과 교착](../../record-lock/README.md), undo 의 자리는 [undo 테이블스페이스와 롤백 세그먼트](../../../structure/undo-segments/README.md)에서 다룬다.
