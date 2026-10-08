# trx_undo_get_undo_rec

상위: [일관 읽기(MVCC)와 undo 체인](../README.md)

**undo 레코드를 읽기 직전에 "purge 가 이미 지웠을 수도 있는가"를 묻고, 아니면 undo 페이지에서 레코드를 복사해 오는 자리다.** 판정 재료는 purge 의 read view(`purge_sys->view`) 하나다. 현재 버전을 만든 트랜잭션(`rec_trx_id`)을 purge view 가 이미 본다면, purge 는 그 버전보다 오래된 버전을 아무도 찾지 않는다고 보고 그 undo 를 치울 수 있다. 그래서 그 경우에는 읽지 않고 true("기록 없음")를 돌려준다. 판정과 복사는 `purge_sys->latch` 의 S 래치 안에서 한 번에 한다. purge 는 자기 view 를 X 래치로만 바꾸므로, 복사하는 동안 판정의 근거가 움직이지 않는다.

## 위치

`storage` / `innobase` / `trx` / `trx0rec.cc` L2421-L2438 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0rec.cc#L2421-L2438))

## 실제 코드

판정하는 쪽이다. 이름과 달리 반환값은 "가져왔는가"가 아니라 **"기록이 없을 수 있는가"** 다.

`storage` / `innobase` / `trx` / `trx0rec.cc` L2408-L2438 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0rec.cc#L2408-L2438))

```cpp
// trx0rec.cc L2408-L2438
/** Copies an undo record to heap.
 @param[in]     roll_ptr        roll pointer to record
 @param[in]     trx_id          id of the trx that generated
                                 the roll pointer: it points to an
                                 undo log of this transaction
 @param[in]     heap            memory heap where copied
 @param[in]     is_temp         true if temporary, no-redo rseg.
 @param[in]     name            table name
 @param[out]    undo_rec        own: copy of the record
 @retval true if the undo log has been
 truncated and we cannot fetch the old version
 @retval false if the undo log record is available
 NOTE: the caller must have latches on the clustered index page. */
[[nodiscard]] static bool trx_undo_get_undo_rec(roll_ptr_t roll_ptr,
                                                trx_id_t trx_id,
                                                mem_heap_t *heap, bool is_temp,
                                                const table_name_t &name,
                                                trx_undo_rec_t **undo_rec) {
  bool missing_history;

  rw_lock_s_lock(&purge_sys->latch, UT_LOCATION_HERE);

  missing_history = purge_sys->view.changes_visible(trx_id, name);
  if (!missing_history) {
    *undo_rec = trx_undo_get_undo_rec_low(roll_ptr, heap, is_temp);
  }

  rw_lock_s_unlock(&purge_sys->latch);

  return (missing_history);
}
```

실제로 읽는 쪽이다. roll_ptr 을 풀어 undo 테이블스페이스, 페이지, 오프셋을 얻고, 그 페이지를 S 래치로 잡아 레코드를 힙에 복사한 뒤 바로 놓는다.

`storage` / `innobase` / `trx` / `trx0rec.cc` L2372-L2406 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0rec.cc#L2372-L2406))

```cpp
// trx0rec.cc L2372-L2406
/** Copies an undo record to heap. This function can be called if we know that
 the undo log record exists.
 @return own: copy of the record */
[[nodiscard]] static trx_undo_rec_t *trx_undo_get_undo_rec_low(
    roll_ptr_t roll_ptr, /*!< in: roll pointer to record */
    mem_heap_t *heap,    /*!< in: memory heap where copied */
    bool is_temp)        /*!< in: true if temp undo rec. */
{
  trx_undo_rec_t *undo_rec;
  ulint undo_num;
  space_id_t space_id;
  page_no_t page_no;
  ulint offset;
  const page_t *undo_page;
  bool is_insert;
  mtr_t mtr;

  trx_undo_decode_roll_ptr(roll_ptr, &is_insert, &undo_num, &page_no, &offset);
  space_id = trx_undo_num_to_space_id(undo_num, is_temp);

  bool found;
  const page_size_t &page_size = fil_space_get_page_size(space_id, &found);
  ut_ad(found);

  mtr_start(&mtr);

  undo_page = trx_undo_page_get_s_latched(page_id_t(space_id, page_no),
                                          page_size, &mtr);

  undo_rec = trx_undo_rec_copy(undo_page, static_cast<uint32_t>(offset), heap);

  mtr_commit(&mtr);

  return (undo_rec);
}
```

purge 가 자기 view 를 바꾸는 자리다. X 래치 안에서 가장 오래된 read view 를 복사한다.

`storage` / `innobase` / `trx` / `trx0purge.cc` L252-L255 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0purge.cc#L252-L255))

```cpp
// trx0purge.cc L252-L255
static void trx_purge_update_oldest_needed() {
  rw_lock_x_lock(&purge_sys->latch, UT_LOCATION_HERE);
  trx_sys->mvcc->clone_oldest_view(&purge_sys->view);
  const auto needed_by_purge_view = purge_sys->view.low_limit_no();
```

## 동작 흐름

```text
 trx_undo_get_undo_rec(roll_ptr, trx_id = rec_trx_id, heap, is_temp, name, &undo_rec)

 L2428  rw_lock_s_lock(&purge_sys->latch)
 L2430  missing_history = purge_sys->view.changes_visible(trx_id)      --> [06]
 L2431  아니면  trx_undo_get_undo_rec_low(roll_ptr, heap, is_temp)
          L2389  trx_undo_decode_roll_ptr -> is_insert, undo_num, page_no, offset
          L2390  space_id = trx_undo_num_to_space_id(undo_num, is_temp)
          L2396  mtr_start
          L2398  trx_undo_page_get_s_latched(page_id)        --> [버퍼 풀 페이지 획득]
          L2401  trx_undo_rec_copy(undo_page, offset, heap)  레코드 길이만큼 힙으로
          L2403  mtr_commit                                   undo 페이지 래치를 바로 푼다
 L2435  rw_lock_s_unlock(&purge_sys->latch)
 L2437  return missing_history
```

판정의 뜻을 시간축에 놓으면 이렇다. purge view 는 가장 오래된 활성 read view 를 복사한 것이다.

```text
 rec 의 DB_TRX_ID = T 일 때

 시간 ->   T 시작 ... T 커밋 ......... 가장 오래된 활성 view 생성 ......... 지금
                                       = purge_sys->view

 purge view 가 T 를 본다 (T 는 그 view 이전에 커밋)
   -> 지금 열린 어떤 view 도 T 이전 버전을 찾지 않는다고 purge 는 본다
   -> T 의 update undo (T 이전 버전을 만드는 재료) 는 이미 치워졌을 수 있다
   -> 읽지 않고 true. [09] 는 false 를 돌려주고 [08] 은 DB_MISSING_HISTORY

 purge view 가 T 를 못 본다
   -> 누군가 T 이전 버전이 필요할 수 있다. purge 가 아직 남겨 두었다
   -> 안전하게 읽는다
```

```text
 이 판정이 true 가 되는 경우 (trx0rec.cc L2498-L2499 주석)

 일관 읽기     자기 view 가 T 를 못 보는데 purge view 는 T 를 본다
               purge view 가 가장 오래된 view 의 복사본이라 보통은 생기지 않는다
 semi-consistent read  view 없이 "마지막 커밋 버전"을 찾는다. 이미 지워졌을 수 있다
 purge 자신    지우는 중인 레코드를 본다. 그래서 [09] 는 TRX_UNDO_PREV_IN_PURGE 면
               이 판정을 무시하고 _low 로 직접 읽는다 (L2494-L2496)
```

## 결과가 쓰이는 곳

```text
 undo_rec (힙 복사본)
      --> [09] 이 trx_undo_rec_get_pars 부터 읽어 갱신 벡터를 만든다
 true (기록 없음)
      --> [09] 이 false 를 돌려주고 [08] 이 DB_MISSING_HISTORY 로 끝낸다
 purge_sys->latch S 래치
      --> purge 코디네이터의 trx_purge_update_oldest_needed (X 래치) 와 서로를 막는다
```

## 다루지 않는 것

undo 테이블스페이스 번호와 space id 의 대응(`trx_undo_num_to_space_id`, `undo::spaces` 의 space_id_bank), undo 페이지에서 레코드 길이를 정하는 `trx_undo_rec_copy` 의 계산은 [undo 테이블스페이스와 롤백 세그먼트](../../../structure/undo-segments/README.md)에 둔다. purge 가 view 를 언제 어떻게 바꾸는지는 [purge](../../purge/04_trx_purge_update_oldest_needed/README.md)에 있다.
