# trx_undo_prev_version_build

상위: [일관 읽기(MVCC)와 undo 체인](../README.md)

**레코드 한 버전과 그 `DB_ROLL_PTR` 이 가리키는 undo 레코드 하나로 바로 앞 버전을 만드는 자리다.** undo 레코드에는 "이 갱신 직전의 `DB_TRX_ID` 와 `DB_ROLL_PTR`", 그리고 "바뀐 열들의 옛 값"이 들어 있다. 이것을 갱신 벡터(`upd_t`)로 읽어 현재 버전의 복사본에 덮어쓰면 앞 버전이 나오고, 그 앞 버전의 `DB_ROLL_PTR` 이 다시 한 칸 앞 undo 를 가리킨다. 체인은 이렇게 undo 레코드 안에 숨어 있다. 반환값은 하나만 기억하면 된다. **false 는 "purge 가 이미 지웠을 수 있어 앞 버전을 만들 수 없다"** 이고, 나머지는 모두 true 다. 앞 버전이 없으면(insert 버전이면) true 와 함께 `old_vers = nullptr` 이다.

## 위치

`storage` / `innobase` / `trx` / `trx0rec.cc` L2446-L2657 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0rec.cc#L2446-L2657))

## 실제 코드

앞부분이다. `DB_ROLL_PTR` 의 insert 비트가 서 있으면 읽을 것도 없이 끝이고, 아니면 [10] 으로 undo 레코드를 복사해 온다.

`storage` / `innobase` / `trx` / `trx0rec.cc` L2446-L2515 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0rec.cc#L2446-L2515))

```cpp
// trx0rec.cc L2446-L2515
bool trx_undo_prev_version_build(
    const rec_t *index_rec ATTRIB_USED_ONLY_IN_DEBUG,
    mtr_t *index_mtr ATTRIB_USED_ONLY_IN_DEBUG, const rec_t *rec,
    const dict_index_t *const index, ulint *offsets, mem_heap_t *heap,
    rec_t **old_vers, mem_heap_t *v_heap, const dtuple_t **vrow, ulint v_status,
    lob::undo_vers_t *lob_undo) {
  DBUG_TRACE;

  // ... (L2454-L2467 생략: 지역 변수 선언)

  ut_ad(!rw_lock_own(&purge_sys->latch, RW_LOCK_S));
  ut_ad(mtr_memo_contains_page(index_mtr, index_rec, MTR_MEMO_PAGE_S_FIX) ||
        mtr_memo_contains_page(index_mtr, index_rec, MTR_MEMO_PAGE_X_FIX));
  ut_ad(rec_offs_validate(rec, index, offsets));
  ut_a(index->is_clustered());

  roll_ptr = row_get_rec_roll_ptr(rec, index, offsets);

  *old_vers = nullptr;

  if (trx_undo_roll_ptr_is_insert(roll_ptr)) {
    /* The record rec is the first inserted version */
    return true;
  }

  rec_trx_id = row_get_rec_trx_id(rec, index, offsets);

  /* REDO rollback segments are used only for non-temporary objects.
  For temporary objects NON-REDO rollback segments are used. */
  bool is_temp = index->table->is_temporary();

  ut_ad(!index->table->skip_alter_undo);

  if (trx_undo_get_undo_rec(roll_ptr, rec_trx_id, heap, is_temp,
                            index->table->name, &undo_rec)) {
    if (v_status & TRX_UNDO_PREV_IN_PURGE) {
      /* We are fetching the record being purged */
      undo_rec = trx_undo_get_undo_rec_low(roll_ptr, heap, is_temp);
    } else {
      /* The undo record may already have been purged,
      during purge or semi-consistent read. */
      return false;
    }
  }

  type_cmpl_t type_cmpl;
  ptr = trx_undo_rec_get_pars(undo_rec, &type, &cmpl_info, &dummy_extern,
                              &undo_no, &table_id, type_cmpl);

  if (table_id != index->table->id) {
    /* The table should have been rebuilt, but purge has
    not yet removed the undo log records for the
    now-dropped old table (table_id). */
    return true;
  }

  ptr = trx_undo_update_rec_get_sys_cols(ptr, &trx_id, &roll_ptr, &info_bits);
```

갱신 벡터를 읽고 앞 버전을 만든다. 열 크기가 바뀌지 않았으면 복사본에 제자리 갱신(`row_upd_rec_in_place`)을 하고, 바뀌었으면 튜플로 풀었다가 다시 레코드로 만든다.

`storage` / `innobase` / `trx` / `trx0rec.cc` L2539-L2606 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0rec.cc#L2539-L2606))

```cpp
// trx0rec.cc L2539-L2606
  ptr = trx_undo_rec_skip_row_ref(ptr, index);

  ptr = trx_undo_update_rec_get_update(ptr, index, type, trx_id, roll_ptr,
                                       info_bits, heap, &update, lob_undo,
                                       type_cmpl);
  ut_a(ptr);

  if (row_upd_changes_field_size_or_external(index, offsets, update)) {
    // ... (L2547-L2562 생략: 외부 저장 열과 purge 의 관계를 설명하는 주석)
    if ((update->info_bits & REC_INFO_DELETED_FLAG) &&
        row_upd_changes_disowned_external(update)) {
      bool missing_extern;

      rw_lock_s_lock(&purge_sys->latch, UT_LOCATION_HERE);

      missing_extern =
          purge_sys->view.changes_visible(trx_id, index->table->name);

      rw_lock_s_unlock(&purge_sys->latch);

      if (missing_extern) {
        /* treat as a fresh insert, not to
        cause assertion error at the caller. */
        if (update != nullptr) {
          update->reset();
        }
        return true;
      }
    }

    /* We have to set the appropriate extern storage bits in the
    old version of the record: the extern bits in rec for those
    fields that update does NOT update, as well as the bits for
    those fields that update updates to become externally stored
    fields. Store the info: */

    entry = row_rec_to_index_entry(rec, index, offsets, heap);
    /* The page containing the clustered index record
    corresponding to entry is latched in mtr.  Thus the
    following call is safe. */
    row_upd_index_replace_new_col_vals(entry, index, update, heap);

    buf = static_cast<byte *>(
        mem_heap_alloc(heap, rec_get_converted_size(index, entry)));

    *old_vers = rec_convert_dtuple_to_rec(buf, index, entry);
  } else {
    buf = static_cast<byte *>(mem_heap_alloc(heap, rec_offs_size(offsets)));

    *old_vers = rec_copy(buf, rec, offsets);
    rec_offs_make_valid(*old_vers, index, offsets);
    row_upd_rec_in_place(*old_vers, index, offsets, update, nullptr);
  }
```

갱신 벡터의 맨 끝 두 칸이 시스템 열이다. undo 에 적힌 옛 `DB_TRX_ID` 와 옛 `DB_ROLL_PTR` 을 거기 넣기 때문에, 앞 버전은 자기 시스템 열까지 옛 값으로 돌아간다.

`storage` / `innobase` / `trx` / `trx0rec.cc` L1748-L1773 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0rec.cc#L1748-L1773))

```cpp
// trx0rec.cc L1748-L1773
  update = upd_create(n_fields + 2, heap);

  update->table = index->table;

  update->info_bits = info_bits;

  /* Store first trx id and roll ptr to update vector */

  upd_field = upd_get_nth_field(update, n_fields);

  buf = static_cast<byte *>(mem_heap_alloc(heap, DATA_TRX_ID_LEN));

  trx_write_trx_id(buf, trx_id);

  auto const trx_id_col = index->table->get_sys_col(DATA_TRX_ID);
  upd_field_set_field_no(upd_field, dict_col_get_clust_pos(trx_id_col, index),
                         index);
  dfield_set_data(&(upd_field->new_val), buf, DATA_TRX_ID_LEN);
  trx_id_col->copy_type(dfield_get_type(&upd_field->new_val));

  upd_field = upd_get_nth_field(update, n_fields + 1);

  buf = static_cast<byte *>(mem_heap_alloc(heap, DATA_ROLL_PTR_LEN));

  trx_write_roll_ptr(buf, roll_ptr);

```

쓰는 쪽이다. UPDATE 나 DELETE 가 update undo 레코드를 쓸 때, 지금 레코드의 `DB_TRX_ID` 와 `DB_ROLL_PTR` 을 그대로 undo 에 적는다. 이것이 다음 고리다.

`storage` / `innobase` / `trx` / `trx0rec.cc` L1252-L1272 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0rec.cc#L1252-L1272))

```cpp
// trx0rec.cc L1252-L1272
  /* Store the values of the system columns */
  field = rec_get_nth_field(nullptr, rec, offsets,
                            index->get_sys_col_pos(DATA_TRX_ID), &flen);
  ut_ad(flen == DATA_TRX_ID_LEN);

  trx_id = trx_read_trx_id(field);

  /* If it is an update of a delete marked record, then we are
  allowed to ignore blob prefixes if the delete marking was done
  by some other trx as it must have committed by now for us to
  allow an over-write. */
  if (ignore_prefix) {
    ignore_prefix = (trx_id != trx->id);
  }
  ptr += mach_u64_write_compressed(ptr, trx_id);

  field = rec_get_nth_field(nullptr, rec, offsets,
                            index->get_sys_col_pos(DATA_ROLL_PTR), &flen);
  ut_ad(flen == DATA_ROLL_PTR_LEN);

  ptr += mach_u64_write_compressed(ptr, trx_read_roll_ptr(field));
```

`DB_ROLL_PTR` 7바이트 안의 배치다.

`storage` / `innobase` / `include` / `trx0undo.ic` L45-L82 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/trx0undo.ic#L45-L82))

```cpp
// trx0undo.ic L45-L82
inline roll_ptr_t trx_undo_build_roll_ptr(bool is_insert, space_id_t space_id,
                                          page_no_t page_no, ulint offset) {
  ut_ad(offset < 65536);

  ulint id = (fsp_is_undo_tablespace(space_id) ? undo::id2num(space_id) : 0);

  roll_ptr_t roll_ptr = (roll_ptr_t)is_insert << 55 | (roll_ptr_t)id << 48 |
                        (roll_ptr_t)page_no << 16 | offset;
  return (roll_ptr);
}

/** Decodes a roll pointer.
param[in]  roll_ptr   roll pointer
param[out] is_insert  true if insert undo log
param[out] undo_num   undo number
param[out] page_no    page number
param[out] offset     offset of the undo entry within page */
inline void trx_undo_decode_roll_ptr(roll_ptr_t roll_ptr, bool *is_insert,
                                     ulint *undo_num, page_no_t *page_no,
                                     ulint *offset) {
  ut_ad(roll_ptr < (1ULL << 56));
  *offset = (ulint)roll_ptr & 0xFFFF;
  roll_ptr >>= 16;
  *page_no = (ulint)roll_ptr & 0xFFFFFFFF;
  roll_ptr >>= 32;
  *undo_num = (ulint)roll_ptr & 0x7F;
  roll_ptr >>= 7;
  *is_insert = roll_ptr; /* true==1 */
}

/** Returns true if the roll pointer is of the insert type.
 @return true if insert undo log */
static inline bool trx_undo_roll_ptr_is_insert(
    roll_ptr_t roll_ptr) /*!< in: roll pointer */
{
  ut_ad(roll_ptr < (1ULL << 56));
  return roll_ptr >> 55;
}
```

## 동작 흐름

```text
 trx_undo_prev_version_build(index_rec, index_mtr, rec, index, offsets, heap, &old_vers, ...)

 L2475  roll_ptr = rec 의 DB_ROLL_PTR
 L2477  *old_vers = nullptr
 L2479  insert 비트(bit 55)가 1                     -> true  (처음 넣은 버전, 앞이 없다)
 L2484  rec_trx_id = rec 의 DB_TRX_ID
 L2492  [10] trx_undo_get_undo_rec(roll_ptr, rec_trx_id, ...)
          true (purge view 가 rec_trx_id 를 본다)
            purge 자신이 부른 것이면 그래도 읽는다      (L2494, TRX_UNDO_PREV_IN_PURGE)
            아니면                                   -> false  (기록이 없을 수 있다)
 L2505  type, cmpl_info, undo_no, table_id 를 읽는다
 L2508  table_id 가 다르다 (테이블 재구성 뒤 남은 undo) -> true, old_vers = nullptr
 L2515  옛 DB_TRX_ID, 옛 DB_ROLL_PTR, info_bits 를 읽는다
 L2539  행 식별 열(PK)을 건너뛴다
 L2541  나머지를 갱신 벡터로 (끝 두 칸 = 옛 DB_TRX_ID, 옛 DB_ROLL_PTR)
 L2546  열 크기가 바뀌거나 외부 저장이 바뀌면
          L2563  옛 버전이 delete-mark 이고 버려진 BLOB 이 있는데
                 purge view 가 그 trx 를 본다      -> true, old_vers = nullptr (BLOB 이 없을 수 있다)
          L2590  튜플로 풀고, 옛 값으로 바꾸고, 레코드로 다시 만든다
 L2600  아니면 rec_copy 후 row_upd_rec_in_place      (제자리 덮어쓰기)
 L2656  true
```

undo 레코드 하나가 레코드를 어떻게 한 칸 되돌리는지 바이트 단위로 보면 이렇다.

```text
 undo 레코드 R3 의 필드 순서 (trx_undo_page_report_modify 가 쓰는 순서, trx0rec.cc)

 크기     필드                               쓰는 줄    읽는 줄 (이 함수)
 2B       다음 레코드 위치 (자리만 잡는다)   L1214
 1B       type_cmpl (UPD_EXIST_REC 등)       L1235      L2505 trx_undo_rec_get_pars
 1B       플래그 (0x00)                      L1241      L2505
 압축     undo_no                            L1243      L2505
 압축     table_id                           L1245      L2505
 1B       info_bits                          L1250      L2515 trx_undo_update_rec_get_sys_cols
 압축     옛 DB_TRX_ID   (= 200)             L1266      L2515
 압축     옛 DB_ROLL_PTR (= R2)              L1272      L2515
 가변     PK 열 (길이, 값)                   L1278 부터 L2539 건너뛴다
 가변     바뀐 열 수, (열 번호, 옛 값) ...                L2541 trx_undo_update_rec_get_update

 갱신 벡터 upd_t (L1748 upd_create(n_fields + 2))
   [0]            v            <- 20
   [n_fields]     DB_TRX_ID    <- 200
   [n_fields + 1] DB_ROLL_PTR  <- R2

 현재 버전                                   앞 버전 (L2603 rec_copy + L2605 row_upd_rec_in_place)
 +------+---------+---------+-----+------+   +------+---------+---------+-----+------+
 | pk=1 | TRX=300 | ROLL=R3 | a=1 | v=30 |   | pk=1 | TRX=200 | ROLL=R2 | a=1 | v=20 |
 +------+---------+---------+-----+------+   +------+---------+---------+-----+------+
 a 는 undo 에 없으니 현재 값이 그대로 남는다
```

```text
 DB_ROLL_PTR 7바이트 (56비트, trx0undo.ic L45-L54)

 bit 55     54 ......... 48   47 .................... 16   15 ........... 0
 +--------+----------------+--------------------------+----------------+
 | insert |  undo 번호 (7) |  undo 페이지 번호 (32)    |  페이지 안 오프셋 (16) |
 +--------+----------------+--------------------------+----------------+
   1 이면 insert undo. 커밋 뒤 바로 지워지므로 [09] 는 따라가지 않는다
   undo 번호 -> trx_undo_num_to_space_id 로 undo 테이블스페이스를 찾는다 ([10])
```

## 결과가 쓰이는 곳

```text
 *old_vers   --> [08] 이 DB_TRX_ID 를 꺼내 [06] 에 묻는다
 반환 false  --> [08] 이 DB_MISSING_HISTORY 로 끝낸다
 같은 함수의 다른 호출자
             --> row0vers.cc 의 다른 함수들도 이 함수로 앞 버전을 만든다
                 row_vers_find_matching (L232), row_vers_old_has_index_entry (L974),
                 row_vers_build_for_semi_consistent_read (L1359) 등
                 row_vers_old_has_index_entry 는 purge 가 세컨더리 엔트리를 지울지 정할 때 쓴다 [purge] 09
```

## 다루지 않는 것

update undo 레코드를 쓰는 함수(`trx_undo_page_report_modify`)의 나머지 필드, `cmpl_info` 의 `UPD_NODE_NO_ORD_CHANGE` 비트, 가상 열의 옛 값(`trx_undo_read_v_cols`), LOB 부분 갱신, `row_upd_rec_in_place` 의 레코드 형식별 처리는 이 흐름의 곁가지라 줄만 적었다. undo 페이지와 undo 레코드의 전체 배치는 [undo 테이블스페이스와 롤백 세그먼트](../../../structure/undo-segments/README.md)에 둔다.
