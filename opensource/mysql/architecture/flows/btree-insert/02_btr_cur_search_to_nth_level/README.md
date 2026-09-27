# btr_cur_search_to_nth_level

상위: [B+Tree 삽입과 분할](../README.md)

**루트에서 원하는 층까지 내려가 커서를 세우는 B+Tree 탐색기다.** 1,080 줄짜리 함수지만 삽입에서 볼 뼈대는 셋이다. 첫째, 래치 모드(`BTR_MODIFY_LEAF` / `BTR_MODIFY_TREE`)에 따라 **index->lock 과 페이지 래치를 어떻게 잡고 언제 놓는지**가 정해진다. 둘째, `search_loop` 가 층마다 `buf_page_get_gen` 으로 페이지를 가져와 `page_cur_search_with_match` 로 이진 탐색하고 노드 포인터를 따라 한 층 내려간다. 셋째, 리프에서 `low_match` / `up_match` 를 커서에 남긴다. 이 문서는 [01] 이 L2461 에서 부르는 `btr_pcur_t::open` 을 함께 본다.

## 위치

`storage` / `innobase` / `btr` / `btr0cur.cc` L619-L1699 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/btr/btr0cur.cc#L619-L1699))

## 실제 코드

[01] 의 `pcur.open` 은 영구 커서를 초기화하고 이 함수를 부른다.

`storage` / `innobase` / `include` / `btr0pcur.h` L518-L550 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/btr0pcur.h#L518-L550))

```cpp
// btr0pcur.h L518-L550
inline void btr_pcur_t::open(dict_index_t *index, ulint level,
                             const dtuple_t *tuple, page_cur_mode_t mode,
                             ulint latch_mode, mtr_t *mtr,
                             ut::Location location) {
  init();

  m_search_mode = mode;
  m_latch_mode = BTR_LATCH_MODE_WITHOUT_FLAGS(latch_mode);

  /* Search with the tree cursor */

  auto cur = get_btr_cur();

  ut_ad(!dict_index_is_spatial(index));

  if (index->table->is_intrinsic()) {
    ut_ad((latch_mode & BTR_MODIFY_LEAF) || (latch_mode & BTR_SEARCH_LEAF) ||
          (latch_mode & BTR_MODIFY_TREE));

    btr_cur_search_to_nth_level_with_no_latch(
        index, level, tuple, mode, cur, location.filename, location.line, mtr,
        (((latch_mode & BTR_MODIFY_LEAF) || (latch_mode & BTR_MODIFY_TREE))
             ? true
             : false));
  } else {
    btr_cur_search_to_nth_level(index, level, tuple, mode, latch_mode, cur, 0,
                                location.filename, location.line, mtr);
  }

  m_pos_state = BTR_PCUR_IS_POSITIONED;

  m_trx_if_known = nullptr;
}
```

래치 모드에 따라 index->lock 을 잡고, 윗 층 페이지를 어떤 래치로 읽을지 정한다.

`storage` / `innobase` / `btr` / `btr0cur.cc` L813-L876 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/btr/btr0cur.cc#L813-L876))

```cpp
// btr0cur.cc L813-L876
  savepoint = mtr_set_savepoint(mtr);

  switch (latch_mode) {
    case BTR_MODIFY_TREE:
      // ... (L817-L830 생략: purge 와 공간 인덱스의 X 잠금 분기)
      } else {
        mtr_sx_lock(dict_index_get_lock(index), mtr, UT_LOCATION_HERE);
      }
      upper_rw_latch = RW_X_LATCH;
      break;
    case BTR_CONT_MODIFY_TREE:
    case BTR_CONT_SEARCH_TREE:
      /* Do nothing */
      ut_ad(srv_read_only_mode ||
            mtr_memo_contains_flagged(mtr, dict_index_get_lock(index),
                                      MTR_MEMO_X_LOCK | MTR_MEMO_SX_LOCK));
      if (dict_index_is_spatial(index) && latch_mode == BTR_CONT_MODIFY_TREE) {
        /* If we are about to locating parent page for split
        and/or merge operation for R-Tree index, X latch
        the parent */
        upper_rw_latch = RW_X_LATCH;
      } else {
        upper_rw_latch = RW_NO_LATCH;
      }
      break;
    default:
      if (!srv_read_only_mode) {
        if (s_latch_by_caller) {
          /* The BTR_ALREADY_S_LATCHED indicates that the index->lock has been
          taken either in RW_S_LATCH or RW_SX_LATCH mode. For parallel reads
          another thread can own the dict index lock. */
          ut_ad(rw_lock_own_flagged(dict_index_get_lock(index),
                                    RW_LOCK_FLAG_S | RW_LOCK_FLAG_SX));

        } else if (!modify_external) {
          /* BTR_SEARCH_TREE is intended to be used with
          BTR_ALREADY_S_LATCHED */
          ut_ad(latch_mode != BTR_SEARCH_TREE);

          mtr_s_lock(dict_index_get_lock(index), mtr, UT_LOCATION_HERE);
        } else {
          /* BTR_MODIFY_EXTERNAL needs to be excluded */
          mtr_sx_lock(dict_index_get_lock(index), mtr, UT_LOCATION_HERE);
        }
        upper_rw_latch = RW_S_LATCH;
      } else {
        upper_rw_latch = RW_NO_LATCH;
      }
  }
  root_leaf_rw_latch = btr_cur_latch_for_root_leaf(latch_mode);

```

`search_loop` 의 머리다. 이번 층의 페이지를 어떤 래치로, 어떤 방식으로 가져올지 정하고 가져온다.

`storage` / `innobase` / `btr` / `btr0cur.cc` L922-L961 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/btr/btr0cur.cc#L922-L961))

```cpp
// btr0cur.cc L922-L961
search_loop:
  fetch = cursor->m_fetch_mode;
  rw_latch = RW_NO_LATCH;
  rtree_parent_modified = false;

  if (height != 0) {
    /* We are about to fetch the root or a non-leaf page. */
    if ((latch_mode != BTR_MODIFY_TREE || height == level) &&
        !retrying_for_search_prev) {
      /* If doesn't have SX or X latch of index,
      each pages should be latched before reading. */
      if (modify_external && height == ULINT_UNDEFINED &&
          upper_rw_latch == RW_S_LATCH) {
        /* needs sx-latch of root page
        for fseg operation */
        rw_latch = RW_SX_LATCH;
      } else {
        rw_latch = upper_rw_latch;
      }
    }
  } else if (latch_mode <= BTR_MODIFY_LEAF) {
    rw_latch = latch_mode;

    if (btr_op != BTR_NO_OP &&
        ibuf_should_try(index, btr_op != BTR_INSERT_OP)) {
      /* Try to buffer the operation if the leaf
      page is not in the buffer pool. */

      fetch = btr_op == BTR_DELETE_OP ? Page_fetch::IF_IN_POOL_OR_WATCH
                                      : Page_fetch::IF_IN_POOL;
    }
  }

retry_page_get:
  ut_ad(n_blocks < BTR_MAX_LEVELS);
  tree_savepoints[n_blocks] = mtr_set_savepoint(mtr);
  block = buf_page_get_gen(
      page_id, page_size, rw_latch,
      (height == ULINT_UNDEFINED ? index->search_info->root_guess : nullptr),
      fetch, {file, line}, mtr);
```

리프에 닿으면 LEAF 모드는 트리 래치와 윗 층 페이지를 모두 놓는다. TREE 모드는 형제까지 X 로 잡고 아무것도 놓지 않는다.

`storage` / `innobase` / `btr` / `btr0cur.cc` L1133-L1177 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/btr/btr0cur.cc#L1133-L1177))

```cpp
// btr0cur.cc L1133-L1177
  if (height == 0) {
    if (rw_latch == RW_NO_LATCH) {
      latch_leaves = btr_cur_latch_leaves(block, page_id, page_size, latch_mode,
                                          cursor, mtr);
    }

    switch (latch_mode) {
      case BTR_MODIFY_TREE:
      case BTR_CONT_MODIFY_TREE:
      case BTR_CONT_SEARCH_TREE:
        break;
      default:
        if (!s_latch_by_caller && !srv_read_only_mode && !modify_external) {
          /* Release the tree s-latch */
          /* NOTE: BTR_MODIFY_EXTERNAL
          needs to keep tree sx-latch */
          mtr_release_s_latch_at_savepoint(mtr, savepoint,
                                           dict_index_get_lock(index));
        }

        /* release upper blocks */
        if (retrying_for_search_prev) {
          for (; prev_n_releases < prev_n_blocks; prev_n_releases++) {
            mtr_release_block_at_savepoint(
                mtr, prev_tree_savepoints[prev_n_releases],
                prev_tree_blocks[prev_n_releases]);
          }
        }

        for (; n_releases < n_blocks; n_releases++) {
          if (n_releases == 0 && modify_external) {
            /* keep latch of root page */
            ut_ad(mtr_memo_contains_flagged(
                mtr, tree_blocks[n_releases],
                MTR_MEMO_PAGE_SX_FIX | MTR_MEMO_PAGE_X_FIX));
            continue;
          }

          mtr_release_block_at_savepoint(mtr, tree_savepoints[n_releases],
                                         tree_blocks[n_releases]);
        }
    }

    page_mode = mode;
  }
```

층마다 이진 탐색을 한다.

`storage` / `innobase` / `btr` / `btr0cur.cc` L1245-L1260 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/btr/btr0cur.cc#L1245-L1260))

```cpp
// btr0cur.cc L1245-L1260
  } else if (height == 0 && btr_search_enabled &&
             !dict_index_is_spatial(index)) {
    /* The adaptive hash index is only used when searching
    for leaf pages (height==0), but not in r-trees.
    We only need the byte prefix comparison for the purpose
    of updating the adaptive hash index. */
    page_cur_search_with_match_bytes(block, index, tuple, page_mode, &up_match,
                                     &up_bytes, &low_match, &low_bytes,
                                     page_cursor);
  } else {
    /* Search for complete index fields. */
    up_bytes = low_bytes = 0;
    page_cur_search_with_match(block, index, tuple, page_mode, &up_match,
                               &low_match, page_cursor,
                               need_path ? cursor->rtr_info : nullptr);
  }
```

TREE 모드에서 내려가는 도중, 이 층이 바뀔 일이 없다고 판단되면 윗 층 래치를 미리 풀고, 목표 층에 닿으면 남은 페이지를 X 로 바꾼다.

`storage` / `innobase` / `btr` / `btr0cur.cc` L1441-L1477 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/btr/btr0cur.cc#L1441-L1477))

```cpp
// btr0cur.cc L1441-L1477
    /* If the page might cause modify_tree,
    we should not release the parent page's lock. */
    if (!detected_same_key_root && latch_mode == BTR_MODIFY_TREE &&
        !btr_cur_will_modify_tree(index, page, lock_intention, node_ptr,
                                  node_ptr_max_size, page_size, mtr) &&
        !rtree_parent_modified) {
      ut_ad(upper_rw_latch == RW_X_LATCH);
      ut_ad(n_releases <= n_blocks);

      /* we can release upper blocks */
      for (; n_releases < n_blocks; n_releases++) {
        if (n_releases == 0) {
          /* we should not release root page
          to pin to same block. */
          continue;
        }

        /* release unused blocks to unpin */
        mtr_release_block_at_savepoint(mtr, tree_savepoints[n_releases],
                                       tree_blocks[n_releases]);
      }
    }

    if (height == level && latch_mode == BTR_MODIFY_TREE) {
      ut_ad(upper_rw_latch == RW_X_LATCH);
      /* we should sx-latch root page, if released already.
      It contains seg_header. */
      if (n_releases > 0) {
        mtr_block_sx_latch_at_savepoint(mtr, tree_savepoints[0],
                                        tree_blocks[0]);
      }

      /* x-latch the branch blocks not released yet. */
      for (ulint i = n_releases; i <= n_blocks; i++) {
        mtr_block_x_latch_at_savepoint(mtr, tree_savepoints[i], tree_blocks[i]);
      }
    }
```

노드 포인터가 가리키는 자식으로 내려간다.

`storage` / `innobase` / `btr` / `btr0cur.cc` L1540-L1543 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/btr/btr0cur.cc#L1540-L1543))

```cpp
// btr0cur.cc L1540-L1543
    /* Go to the child node */
    page_id.reset(space, btr_node_ptr_get_child_page_no(node_ptr, offsets));

    n_blocks++;
```

리프에서 끝낼 때 커서에 match 값을 남긴다.

`storage` / `innobase` / `btr` / `btr0cur.cc` L1648-L1660 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/btr/btr0cur.cc#L1648-L1660))

```cpp
// btr0cur.cc L1648-L1660
  } else {
    cursor->low_match = low_match;
    cursor->low_bytes = low_bytes;
    cursor->up_match = up_match;
    cursor->up_bytes = up_bytes;

    /* We do a dirty read of btr_search_enabled here.  We
    will properly check btr_search_enabled again in
    btr_search_build_page_hash_index() before building a
    page hash index, while holding search latch. */
    if (btr_search_enabled && !index->disable_ahi) {
      btr_search_info_update(cursor);
    }
```

## 동작 흐름

```text
 L721   btr_op        latch_mode 의 BTR_INSERT / DELETE / DELETE_MARK 플래그 -> change buffer 연산
 L755   lock_intention BTR_LATCH_FOR_INSERT / DELETE 플래그 -> INSERT / DELETE / BOTH
                       클러스터드 삽입은 둘 다 없어 BTR_INTENTION_BOTH (L425)
 L775   LEAF 이하 모드이고 적응형 해시가 맞히면 (L786 btr_search_guess_on_hash)
          트리를 내려가지 않고 바로 return
 L813   savepoint = 트리 래치를 mtr 에 넣을 자리

 L815   switch (latch_mode)
          BTR_MODIFY_TREE   L832  mtr_sx_lock(index->lock)   upper_rw_latch = X
          BTR_CONT_*        L848  이미 잡혀 있다             upper_rw_latch = NO_LATCH
          그 밖 (LEAF 포함) L865  mtr_s_lock(index->lock)    upper_rw_latch = S
 L875   root_leaf_rw_latch  루트가 곧 리프일 때의 래치 (MODIFY_* 는 X)
 L883   page_id = 인덱스의 루트 페이지
 L900   윗 층 탐색 모드: GE -> L, G -> LE, 그 밖(LE)은 그대로

 L922   search_loop:
 L927     윗 층이면  rw_latch = upper_rw_latch
                     단 TREE 모드는 목표 층 전까지 NO_LATCH (L929). index->lock SX 가 지킨다
 L942     리프이고 LEAF 이하 모드면 rw_latch = latch_mode (X)
 L945       change buffer 대상이면 fetch = IF_IN_POOL
 L958     block = buf_page_get_gen(page_id, rw_latch, fetch)       --> [버퍼 풀 페이지 획득]
 L965     nullptr 이면 ibuf_insert 를 시도 (세컨더리 전용)
 L1071    루트가 리프인데 래치가 다르면 루트 래치를 바꿔 다시
 L1101    루트면 height = 페이지 level, tree_height = level + 1
 L1133    리프(height == 0)
 L1135      래치 없이 읽었으면 btr_cur_latch_leaves     TREE: 왼쪽, 자신, 오른쪽을 X
 L1139      TREE 가 아니면
 L1149        index->lock S 해제
 L1162        윗 층 페이지들 해제
 L1245    리프 + AHI 사용이면 page_cur_search_with_match_bytes
 L1257    아니면 page_cur_search_with_match              이진 탐색 (page directory)
 L1294    목표 층이 아니면
 L1298      height--
 L1300      node_ptr = 커서 레코드                        이 레코드가 가리키는 자식으로
 L1312      TREE 이고 반대 의도가 필요하면 모두 놓고 INTENTION_BOTH 로 처음부터
            (BOTH 의도에서는 btr_cur_need_opposite_intention 이 늘 false, L601-L602)
 L1443      TREE 이고 btr_cur_will_modify_tree 가 거짓이면 루트를 뺀 윗 층 해제
 L1464      TREE 이고 목표 층이면 남은 윗 층 페이지를 X 로 (루트는 SX)
 L1541      page_id = 자식 페이지 번호
 L1588      goto search_loop
 L1589    TREE 이고 의도가 BTR_INTENTION_INSERT 이고 커서가 페이지 마지막 레코드이고
          오른쪽 형제가 있으면 need_opposite_intention 으로 (btr_insert_into_right_sibling 대비)
          INSERT 의도(BTR_LATCH_FOR_INSERT)는 change buffer 만 쓴다 (ibuf0ibuf.cc L3392).
          [01] 과 행 쓰기의 세컨더리 삽입은 의도 플래그 없이 BOTH 라 이 두 갈래를 타지 않는다
 L1649    리프: cursor 에 low_match, up_match 기록
 L1659      AHI 통계 갱신 (btr_search_info_update)
```

LEAF 와 TREE 는 같은 경로를 내려가지만 쥐고 내려가는 것이 다르다. LEAF 는 한 번에 한두 페이지만 쥐고, TREE 는 바뀔 수 있는 경로 전체를 쥔다.

```text
 높이 3 트리를 내려갈 때 쥐고 있는 래치 (위에서 아래로 시간)

 BTR_MODIFY_LEAF
   index->lock  S -------------------------------------------+ L1149 에서 해제
   루트         S --------------------------------------------+ L1162 에서 해제
   중간               S --------------------------------------+ L1162
   리프                     X ----------------------------------------> mtr 끝까지
   (윗 층 래치는 리프에 닿은 순간 모두 놓는다)

 BTR_MODIFY_TREE
   index->lock  SX -------------------------------------------------------> mtr 끝까지
   루트         (NO_LATCH 로 buffer-fix 만) ... 목표 층 앞에서 L1469 SX 또는 L1475 X --> 끝까지
   중간               (NO_LATCH) ... 바뀔 일 없으면 L1459 에서 풀림
                                     아니면 L1475 에서 X --------------> 끝까지
   리프                     L1135 btr_cur_latch_leaves
                            왼쪽 형제 X, 리프 X, 오른쪽 형제 X ----------> 끝까지
```

```text
 층 하나에서 일어나는 일 (노드 페이지, PAGE_CUR_LE 로 키 25 를 찾을 때)

 노드 페이지 레코드 = (자식 첫 키, 자식 페이지 번호)
   infimum -> (min, P7) -> (10, P8) -> (50, P9) -> supremum

 page_cur_search_with_match(PAGE_CUR_LE)
   page directory 슬롯으로 이진 탐색 -> 슬롯 안에서 연결 리스트로 선형 탐색
   -> 25 이하인 마지막 레코드 (10, P8)
 L1541  btr_node_ptr_get_child_page_no(node_ptr) = P8 로 내려간다
```

## 결과가 쓰이는 곳

```text
 cursor->page_cur (블록, 레코드)
      --> [03] [07] 이 이 레코드 바로 뒤에 삽입한다
 cursor->low_match / up_match
      --> [01] 의 중복 검사(L2505)와 row_ins_must_modify_rec
 cursor->tree_height
      --> [07] 이 예약할 extent 수를 정한다 (tree_height / 16 + 3)
 mtr 의 memo (쥔 래치와 buffer-fix 목록)
      --> mtr.commit 이 한꺼번에 푼다. TREE 모드에서는 [08] 이 index->lock 을 먼저 풀 수 있다
```

## 다루지 않는 것

공간 인덱스(R-tree)의 경로 저장과 predicate 잠금, `BTR_SEARCH_PREV` / `BTR_MODIFY_PREV` 의 왼쪽 형제 재탐색(L1482-L1537), 적응형 해시 인덱스(`btr_search_guess_on_hash`, `btr_search_info_update`), change buffer 의 삭제 연산(`BTR_DELETE_OP`, purge 전용), `btr_cur_will_modify_tree` 와 `btr_cur_need_opposite_intention` 의 여유 공간 계산, 내부 임시 테이블의 무래치 탐색(`btr_cur_search_to_nth_level_with_no_latch`)은 곁가지라 줄만 적었다. 페이지를 가져오는 쪽은 [버퍼 풀 페이지 획득](../../buffer-pool-fetch/README.md)이다.
