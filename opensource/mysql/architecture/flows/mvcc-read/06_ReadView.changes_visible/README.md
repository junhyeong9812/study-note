# ReadView::changes_visible

상위: [일관 읽기(MVCC)와 undo 체인](../README.md)

**MVCC 가시성 규칙 전체가 들어 있는 스무 줄이다.** trx id 하나를 받아 이 read view 가 그 트랜잭션의 변경을 보는지 답한다. 비교는 쉬운 것부터 한다. `m_up_limit_id` 보다 작거나 자기 자신이면 보이고, `m_low_limit_id` 이상이면 안 보이고, 그 사이면 `m_ids` 를 이진 탐색해 **없으면 보인다**. 뮤텍스도 원자 연산도 없다. read view 는 만들어진 뒤 바뀌지 않으므로 이 함수는 순수한 비교다. 같은 함수를 purge 도 쓴다. `purge_sys->view.changes_visible(id)` 가 true 면 "가장 오래된 view 도 그 변경을 본다", 곧 그 이전 버전은 아무에게도 필요 없다는 뜻이다.

## 위치

`storage` / `innobase` / `include` / `read0types.h` L163-L183 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/read0types.h#L163-L183))

## 실제 코드

판정 본체와, 바로 아래의 더 거친 판정 `sees` 다. `sees` 는 `m_up_limit_id` 하나만 본다.

`storage` / `innobase` / `include` / `read0types.h` L159-L188 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/read0types.h#L159-L188))

```cpp
// read0types.h L159-L188
  /** Check whether the changes by id are visible.
  @param[in]    id      transaction id to check against the view
  @param[in]    name    table name
  @return whether the view sees the modifications of id. */
  [[nodiscard]] bool changes_visible(trx_id_t id,
                                     const table_name_t &name) const {
    ut_ad(id > 0);

    if (id < m_up_limit_id || id == m_creator_trx_id) {
      return (true);
    }

    check_trx_id_sanity(id, name);

    if (id >= m_low_limit_id) {
      return (false);

    } else if (m_ids.empty()) {
      return (true);
    }

    const ids_t::value_type *p = m_ids.data();

    return (!std::binary_search(p, p + m_ids.size(), id));
  }

  /**
  @param id             transaction to check
  @return true if view sees transaction id */
  bool sees(trx_id_t id) const { return (id < m_up_limit_id); }
```

범위 밖의 id 를 만났을 때의 안전 장치다. 레코드에 찍힌 trx id 가 시스템이 아직 나눠 준 적 없는 번호면 경고를 남긴다(디버그 빌드는 멈춘다).

`storage` / `innobase` / `trx` / `trx0sys.cc` L113-L126 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0sys.cc#L113-L126))

```cpp
// trx0sys.cc L113-L126
void ReadView::check_trx_id_sanity(trx_id_t id, const table_name_t &name) {
  if (&name == &dict_sys->dynamic_metadata->name) {
    /* The table mysql.innodb_dynamic_metadata uses a
    constant DB_TRX_ID=~0. */
    ut_ad(id == (1ULL << 48) - 1);
    return;
  }

  if (id >= trx_sys_get_next_trx_id_or_no()) {
    ib::warn(ER_IB_MSG_1196)
        << "A transaction id"
        << " in a record of table " << name << " is newer than the"
        << " system-wide maximum.";
    ut_d(ut_error);
```

## 동작 흐름

```text
 changes_visible(id, name)

 L165  ut_ad(id > 0)
 L167  id < m_up_limit_id  또는  id == m_creator_trx_id   -> true
 L171  check_trx_id_sanity(id)        id >= next_trx_id_or_no 면 경고 (trx0sys.cc L121)
 L173  id >= m_low_limit_id                              -> false
 L176  m_ids 가 비었다                                    -> true
 L182  binary_search(m_ids, id)  있으면 false, 없으면 true
```

판정을 상자 하나로 그리면 이렇다. 위에서 아래로 먼저 맞는 칸에서 끝난다.

```text
 id 를 받았다
   |
   +-- id == m_creator_trx_id ? ----------- 예 --> 보인다 (자기 변경)
   +-- id < m_up_limit_id ? --------------- 예 --> 보인다 (view 이전에 끝났다)
   +-- id >= m_low_limit_id ? ------------- 예 --> 안 보인다 (view 이후에 시작했다)
   +-- m_ids 가 비었나 ? ------------------ 예 --> 보인다
   +-- m_ids 에 id 가 있나 ? -------------- 예 --> 안 보인다 (view 를 만들 때 활성)
                                           아니오 --> 보인다 (그 사이 커밋했다)

 비용: 앞의 세 칸은 비교 한 번. 마지막 칸만 O(log |m_ids|)
       동시 트랜잭션이 많을수록 m_up_limit_id 와 m_low_limit_id 사이가 넓어져 마지막 칸에 자주 간다
```

[02] 와 purge 가 같은 함수를 다른 뜻으로 쓴다. 독자가 들고 있는 view 와 purge 가 들고 있는 view 의 차이다.

```text
 changes_visible 을 부르는 쪽 (이 흐름 안과 밖)

 호출자                                    view                    true 의 뜻
 [05] lock_clust_rec_cons_read_sees         trx->read_view          이 버전을 읽어도 된다
 [08] row_vers_build_for_consistent_read    trx->read_view          이 옛 버전에서 멈춘다
 [10] trx_undo_get_undo_rec                 purge_sys->view         이 undo 는 purge 가 지웠을 수 있다
 [09] (BLOB 이 바뀐 delete-mark 버전)       purge_sys->view         외부 저장 열이 이미 지워졌을 수 있다
 row_vers_must_preserve_del_marked          purge_sys->view         false 면 delete-mark 된 옛 버전을
   (row0vers.cc L584)                                               지우지 말고 남겨야 한다

 purge_sys->view 는 가장 오래된 활성 view 를 복사한 것이다 ([purge] 04)
 purge 는 purge view 가 보는 trx 까지의 undo 를 지울 수 있으므로
 다른 쪽은 purge view 가 true 인 trx 의 undo 를 믿지 않는다 ([10])
```

## 결과가 쓰이는 곳

```text
 true / false
      --> [02] 에서는 "rec 를 그대로 쓸까, [07] 로 옛 버전을 만들까"
      --> [08] 에서는 "이 버전에서 멈출까, 한 칸 더 거슬러 갈까"
      --> [10] 에서는 "undo 를 읽어도 안전한가"
```

## 다루지 않는 것

`m_ids` 의 자료구조(`ids_t`, 정렬된 배열과 `insert`), `check_trx_id_sanity` 의 경고 문구와 `innodb_dynamic_metadata` 테이블의 고정 `DB_TRX_ID` 예외는 이 흐름의 곁가지라 줄만 적었다.
