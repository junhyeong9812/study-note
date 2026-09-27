# btr_root_raise_and_insert

상위: [B+Tree 삽입과 분할](../README.md)

**루트 페이지가 가득 찼을 때 트리를 한 층 높이는 함수다.** 루트를 둘로 나누는 대신 네 걸음을 밟는다. 새 페이지를 받아 루트의 레코드를 **전부 복사**하고, 루트를 한 층 높은 빈 노드 페이지로 **다시 만들고**, 그 루트에 새 페이지를 가리키는 노드 포인터 하나를 넣고, 마지막으로 새 페이지를 [08] 로 **분할**한다. 이렇게 하면 루트의 페이지 번호가 바뀌지 않는다.

## 위치

`storage` / `innobase` / `btr` / `btr0btr.cc` L1482-L1660 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/btr/btr0btr.cc#L1482-L1660))

## 실제 코드

새 페이지를 받아 루트와 같은 level 로 만들고 루트의 레코드를 복사한다.

`storage` / `innobase` / `btr` / `btr0btr.cc` L1532-L1591 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/btr/btr0btr.cc#L1532-L1591))

```cpp
// btr0btr.cc L1532-L1591
  /* Allocate a new page to the tree. Root splitting is done by first
  moving the root records to the new page, emptying the root, putting
  a node pointer to the new page, and then splitting the new page. */

  level = btr_page_get_level(root);

  new_block = btr_page_alloc(index, 0, FSP_NO_DIR, level, mtr, mtr);

  /* New page could not be allocated */
  if (!new_block) {
    return nullptr;
  }

  new_page = buf_block_get_frame(new_block);
  new_page_zip = buf_block_get_page_zip(new_block);
  ut_a(!new_page_zip == !root_page_zip);
  ut_a(!new_page_zip ||
       page_zip_get_size(new_page_zip) == page_zip_get_size(root_page_zip));

  btr_page_create(new_block, new_page_zip, index, level, mtr);

  /* Set the next node and previous node fields of new page */
  btr_page_set_next(new_page, new_page_zip, FIL_NULL, mtr);
  btr_page_set_prev(new_page, new_page_zip, FIL_NULL, mtr);

  /* Copy the records from root to the new page one by one. */

  if (false
#ifdef UNIV_ZIP_COPY
      || new_page_zip
#endif /* UNIV_ZIP_COPY */
      || !page_copy_rec_list_end(new_block, root_block,
                                 page_get_infimum_rec(root), index, mtr)) {
    // ... (L1565-L1581 생략: 압축 페이지에서 복사 실패 시 바이트 복사와 잠금, AHI 이동)
  }

  /* If this is a pessimistic insert which is actually done to
  perform a pessimistic update then we have stored the lock
  information of the record to be inserted on the infimum of the
  root page: we cannot discard the lock structs on the root page */

  if (!dict_table_is_locking_disabled(index->table)) {
    lock_update_root_raise(new_block, root_block);
  }
```

노드 포인터를 만들고 루트를 비운 뒤 그 포인터 하나만 넣는다. 그리고 새 페이지를 나눈다.

`storage` / `innobase` / `btr` / `btr0btr.cc` L1598-L1660 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/btr/btr0btr.cc#L1598-L1660))

```cpp
// btr0btr.cc L1598-L1660
  rec = page_rec_get_next(page_get_infimum_rec(new_page));
  new_page_no = new_block->page.id.page_no();

  /* Build the node pointer (= node key and page address) for the
  child */
  if (dict_index_is_spatial(index)) {
    // ... (L1604-L1608 생략: 공간 인덱스의 MBR 노드 포인터)
  } else {
    node_ptr = dict_index_build_node_ptr(index, rec, new_page_no, *heap, level);
  }
  /* The node pointer must be marked as the predefined minimum record,
  as there is no lower alphabetical limit to records in the leftmost
  node of a level: */
  dtuple_set_info_bits(node_ptr,
                       dtuple_get_info_bits(node_ptr) | REC_INFO_MIN_REC_FLAG);

  /* Rebuild the root page to get free space */
  btr_page_empty(root_block, root_page_zip, index, level + 1, mtr);

  /* Set the next node and previous node fields, although
  they should already have been set.  The previous node field
  must be FIL_NULL if root_page_zip != NULL, because the
  REC_INFO_MIN_REC_FLAG (of the first user record) will be
  set if and only if btr_page_get_prev() == FIL_NULL. */
  btr_page_set_next(root, root_page_zip, FIL_NULL, mtr);
  btr_page_set_prev(root, root_page_zip, FIL_NULL, mtr);

  page_cursor = btr_cur_get_page_cur(cursor);

  /* Insert node pointer to the root */

  page_cur_set_before_first(root_block, page_cursor);

  node_ptr_rec =
      page_cur_tuple_insert(page_cursor, node_ptr, index, offsets, heap, mtr);

  /* The root page should only contain the node pointer
  to new_page at this point.  Thus, the data should fit. */
  ut_a(node_ptr_rec);

  /* We play safe and reset the free bits for the new page */

  if (!index->is_clustered() && !index->table->is_temporary()) {
    ibuf_reset_free_bits(new_block);
  }

  /* Reposition the cursor to the child node */
  page_cur_search(new_block, index, tuple, page_cursor);

  /* Split the child and insert tuple */
  if (dict_index_is_spatial(index)) {
    /* Split rtree page and insert tuple */
    return (
        rtr_page_split_and_insert(flags, cursor, offsets, heap, tuple, mtr));
  } else {
    return (
        btr_page_split_and_insert(flags, cursor, offsets, heap, tuple, mtr));
  }
}
```

## 동작 흐름

```text
 L1536  level = 루트의 level
 L1538  btr_page_alloc(index, 0, FSP_NO_DIR, level)   새 페이지 N (방향 힌트 없음)
 L1541    못 받으면 nullptr -> [07] 이 DB_OUT_OF_FILE_SPACE
 L1551  btr_page_create(N, level)                      루트와 같은 level
 L1554  N.next = N.prev = FIL_NULL                      이 level 의 유일한 페이지
 L1563  page_copy_rec_list_end(N, root, infimum 부터)   루트의 모든 레코드를 N 으로 복사
 L1590  lock_update_root_raise(N, root)               루트 레코드의 잠금을 N 의 레코드로

 L1598  rec = N 의 첫 사용자 레코드
 L1610  node_ptr = dict_index_build_node_ptr(rec, N 의 번호, level)
 L1615  node_ptr 에 REC_INFO_MIN_REC_FLAG                이 level 의 가장 왼쪽 = 하한 없음
 L1619  btr_page_empty(root, level + 1)                 루트를 비우고 level 을 하나 올린다
 L1626  root.next = root.prev = FIL_NULL
 L1633  루트 커서를 infimum 에
 L1635  page_cur_tuple_insert(node_ptr)                 루트에 레코드 하나
 L1640  ut_a: 반드시 들어가야 한다 (빈 페이지에 포인터 하나)
 L1644  세컨더리면 N 의 change buffer 여유 비트 초기화
 L1649  page_cur_search(N, tuple)                       커서를 N 안의 삽입 자리로
 L1658  [08] btr_page_split_and_insert(cursor, tuple)   N 을 나누고 튜플을 넣는다
```

세 장면으로 보면 이렇다. 루트 페이지 번호 R 은 처음부터 끝까지 그대로다.

```text
 루트 승격 (R 은 루트 페이지 번호, 높이 1 -> 2)

 1. 복사 (L1563)
      R (level 0)  [a b c d e f]            N (level 0)  [a b c d e f]
                                             새 페이지, 형제 없음

 2. 루트 재구성 (L1619, L1635)
      R (level 1)  [ (min, N) ]             N (level 0)  [a b c d e f]
                        |                         ^
                        +-------------------------+
      min = REC_INFO_MIN_REC_FLAG. 이 포인터는 모든 키보다 작은 쪽까지 맡는다

 3. N 분할 ([08], L1658)
      R (level 1)  [ (min, N) (d, M) ]
                      /           \
      N (level 0) [a b c]  <->  M (level 0) [d e f + 새 튜플]      (자르는 자리는 예시)
      M 을 가리키는 (d, M) 은 [08] 의 btr_attach_half_pages 가 루트에 넣는다
```

루트 번호는 두 자리에서 쓰인다. 탐색은 언제나 `dict_index_get_page(index)` 에서 시작하고([02] L883), [07] 은 이 번호와 비교해 루트인지를 가린다(btr0cur.cc L3018). 이 함수는 그 번호를 건드리지 않는다.

```text
 db-engine 03-02 splitRootLeaf 와 나란히

 루트 내용 복사
   MySQL      page_copy_rec_list_end(N, root)
   db-engine  copyPageContent(root -> leftChild)
 루트 재정의
   MySQL      btr_page_empty(root, level + 1)
   db-engine  root 를 INTERNAL 로 다시 초기화
 루트의 포인터
   MySQL      (min, N) 하나를 넣고, 분할이 (d, M) 을 더한다
   db-engine  auxPage = leftChild, 엔트리 (separator, rightChild)
 분할
   MySQL      복사본 N 을 [08] 로 나눈다
   db-engine  moveHalfTo(leftChild, rightChild)
 루트 번호
   MySQL      dict_index_get_page 그대로
   db-engine  page 0 그대로
```

## 결과가 쓰이는 곳

```text
 루트의 새 level (level + 1)
      --> [02] 가 루트에서 height 를 읽어 tree_height 를 정한다 (btr0cur.cc L1104-L1106)
 REC_INFO_MIN_REC_FLAG 노드 포인터
      --> 이 level 가장 왼쪽 포인터. 가장 왼쪽 노드에는 하한이 없다는 표시다 (L1612-L1614 주석)
 N, M 페이지와 이동된 잠금
      --> 다음 탐색은 R -> N 또는 R -> M 으로 내려간다
```

## 다루지 않는 것

압축 페이지의 바이트 복사(`page_zip_copy_recs`), 공간 인덱스의 MBR 노드 포인터와 `rtr_page_split_and_insert`, 루트 페이지의 세그먼트 헤더(`PAGE_BTR_SEG_LEAF`, `PAGE_BTR_SEG_TOP`) 관리, `btr_page_empty` 의 초기화 세부는 곁가지다.
