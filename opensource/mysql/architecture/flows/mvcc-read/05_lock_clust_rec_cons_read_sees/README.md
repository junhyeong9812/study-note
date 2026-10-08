# lock_clust_rec_cons_read_sees

상위: [일관 읽기(MVCC)와 undo 체인](../README.md)

**클러스터드 인덱스 레코드 하나가 지금 read view 에 그대로 보이는지 묻는 자리다.** 레코드의 숨은 열 `DB_TRX_ID` 6바이트를 읽어 [06] `changes_visible` 에 넘기는 것이 전부다. 이름에 `lock` 이 붙어 있고 `lock0lock.cc` 에 있지만 잠금은 하나도 잡지 않는다. 짝인 `lock_sec_rec_cons_read_sees` 는 세컨더리 인덱스용인데, 세컨더리 레코드에는 `DB_TRX_ID` 가 없어서 **페이지 전체의 최대 trx id** 로만 판정하고, 확실히 보일 때만 true 를 준다.

## 위치

`storage` / `innobase` / `lock` / `lock0lock.cc` L236-L262 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0lock.cc#L236-L262))

## 실제 코드

본체다. 읽기 전용 서버와 임시 테이블은 판정 없이 true 다. 임시 테이블은 연결 사이에 공유되지 않기 때문이라고 주석이 적었다.

`storage` / `innobase` / `lock` / `lock0lock.cc` L233-L262 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0lock.cc#L233-L262))

```cpp
// lock0lock.cc L233-L262
/** Checks that a record is seen in a consistent read.
 @return true if sees, or false if an earlier version of the record
 should be retrieved */
bool lock_clust_rec_cons_read_sees(
    const rec_t *rec,     /*!< in: user record which should be read or
                          passed over by a read cursor */
    dict_index_t *index,  /*!< in: clustered index */
    const ulint *offsets, /*!< in: rec_get_offsets(rec, index) */
    ReadView *view)       /*!< in: consistent read view */
{
  ut_ad(index->is_clustered());
  ut_ad(page_rec_is_user_rec(rec));
  ut_ad(rec_offs_validate(rec, index, offsets));

  /* Temp-tables are not shared across connections and multiple
  transactions from different connections cannot simultaneously
  operate on same temp-table and so read of temp-table is
  always consistent read. */
  if (srv_read_only_mode || index->table->is_temporary()) {
    ut_ad(view == nullptr || index->table->is_temporary());
    return (true);
  }

  /* NOTE that we call this function while holding the search
  system latch. */

  trx_id_t trx_id = row_get_rec_trx_id(rec, index, offsets);

  return (view->changes_visible(trx_id, index->table->name));
}
```

`DB_TRX_ID` 를 꺼내는 함수다. 인덱스가 열 위치를 미리 계산해 두었으면(`trx_id_offset`) 그 오프셋을 쓰고, 가변 길이 열이 앞에 있어 고정 오프셋이 없으면 레코드마다 계산한다.

`storage` / `innobase` / `include` / `row0row.ic` L59-L74 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/row0row.ic#L59-L74))

```cpp
// row0row.ic L59-L74
static inline trx_id_t row_get_rec_trx_id(const rec_t *rec,
                                          const dict_index_t *index,
                                          const ulint *offsets) {
  ulint offset;

  ut_ad(index->is_clustered());
  ut_ad(rec_offs_validate(rec, index, offsets));

  offset = index->trx_id_offset;

  if (!offset) {
    offset = row_get_trx_id_offset(index, offsets);
  }

  return (trx_read_trx_id(rec + offset));
}
```

`storage` / `innobase` / `include` / `trx0sys.ic` L137-L141 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/trx0sys.ic#L137-L141))

```cpp
// trx0sys.ic L137-L141
static inline trx_id_t trx_read_trx_id(
    const byte *ptr) /*!< in: pointer to memory from where to read */
{
  return (mach_read_from_6(ptr));
}
```

세컨더리 인덱스 쪽이다. 페이지 헤더의 `PAGE_MAX_TRX_ID` 가 view 의 `m_up_limit_id` 보다 작으면 이 페이지의 어떤 변경도 view 이전에 끝났으므로 세컨더리 레코드를 그대로 믿는다.

`storage` / `innobase` / `lock` / `lock0lock.cc` L264-L301 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0lock.cc#L264-L301))

```cpp
// lock0lock.cc L264-L301
/** Checks that a non-clustered index record is seen in a consistent read.

 NOTE that a non-clustered index page contains so little information on
 its modifications that also in the case false, the present version of
 rec may be the right, but we must check this from the clustered index
 record.

 @return true if certainly sees, or false if an earlier version of the
 clustered index record might be needed */
bool lock_sec_rec_cons_read_sees(
    const rec_t *rec,          /*!< in: user record which
                               should be read or passed over
                               by a read cursor */
    const dict_index_t *index, /*!< in: index */
    const ReadView *view)      /*!< in: consistent read view */
{
  ut_ad(page_rec_is_user_rec(rec));

  /* NOTE that we might call this function while holding the search
  system latch. */

  if (recv_recovery_is_on()) {
    return (false);

  } else if (index->table->is_temporary()) {
    /* Temp-tables are not shared across connections and multiple
    transactions from different connections cannot simultaneously
    operate on same temp-table and so read of temp-table is
    always consistent read. */

    return (true);
  }

  trx_id_t max_trx_id = page_get_max_trx_id(page_align(rec));

  ut_ad(max_trx_id > 0);

  return (view->sees(max_trx_id));
```

## 동작 흐름

```text
 클러스터드 레코드 (ROW_FORMAT=DYNAMIC 등, 사용자 열 부분)

 +----------+----------------+-----------------+-------------+
 | PK 열들  | DB_TRX_ID (6B) | DB_ROLL_PTR (7B)| 나머지 열들 |
 +----------+----------------+-----------------+-------------+
             ^ index->trx_id_offset (PK 가 고정 길이일 때 미리 계산)
             row_get_rec_trx_id -> trx_read_trx_id -> mach_read_from_6

 lock_clust_rec_cons_read_sees(rec, index, offsets, view)
   L251  srv_read_only_mode 또는 임시 테이블    -> true
   L259  trx_id = row_get_rec_trx_id(rec, index, offsets)
   L261  return view->changes_visible(trx_id, table name)   --> [06]
```

두 함수의 답은 무게가 다르다. 클러스터드 쪽 false 는 "이 버전은 확실히 안 보인다"이고, 세컨더리 쪽 false 는 "모르겠다"다.

```text
 클러스터드와 세컨더리의 판정

                 재료                         true 의 뜻             false 의 뜻
 클러스터드      레코드의 DB_TRX_ID           이 버전이 보인다       안 보인다 -> [07] 옛 버전
 세컨더리        페이지의 PAGE_MAX_TRX_ID     페이지 전체가 보인다   모른다 -> 클러스터드로 가서
                 view->sees(max) 하나만       (id < m_up_limit_id)   [05] 을 다시 한다

 세컨더리는 m_ids 도, m_creator_trx_id 도 보지 않는다
   그래서 자기 트랜잭션이 바꾼 페이지에서도 false 가 나올 수 있고 그러면 클러스터드까지 간다
 복구 중(recv_recovery_is_on)이면 세컨더리는 항상 false (L285)
```

```text
 PAGE_MAX_TRX_ID 가 세컨더리 판정에 쓸 만한 이유

 세컨더리 리프 페이지를 바꾸는 쪽은 그 페이지의 PAGE_MAX_TRX_ID 를 자기 trx id 로 올린다
   page_update_max_trx_id (page0page.ic L68) 는 더 클 때만 쓴다 (L88)
   부르는 곳 예: 세컨더리 삽입 lock_rec_insert_check_and_lock (lock0lock.cc L5139)
                 세컨더리 수정 lock_sec_rec_modify_check_and_lock (lock0lock.cc L5363)
 그래서 "max < m_up_limit_id" 이면 이 페이지를 마지막으로 건드린 trx 도
 view 를 만들기 전에 끝났다 -> 페이지의 모든 레코드가 커밋된 상태다
 바쁜 테이블에서는 이 조건이 자주 깨지고, 그만큼 클러스터드 조회가 늘어난다
```

## 결과가 쓰이는 곳

```text
 true   --> [02] 가 페이지 위의 rec 를 그대로 결과 후보로 쓴다
 false  --> [02] 가 [07] row_sel_build_prev_vers_for_mysql 를 부른다 (row0sel.cc L5341)
            세컨더리 인덱스 조회에서도 같다 (row0sel.cc L3312)
```

## 다루지 않는 것

`trx_id_offset` 을 정하는 `dict_index_add_col` 쪽 계산, 레코드 형식별 오프셋(`rec_get_offsets`)은 [레코드 포맷](../../../structure/record-format/README.md)에, `PAGE_MAX_TRX_ID` 를 올리는 `page_update_max_trx_id` 의 호출 지점은 페이지 쓰기 쪽이라 이름만 적었다.
