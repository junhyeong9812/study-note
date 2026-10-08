# row_purge_record_func

상위: [purge](../README.md)

**해석이 끝난 undo 레코드 하나를 종류에 따라 두 갈래로 보내고, 끝나면 연 것을 닫는 자리다.** delete-mark undo(`TRX_UNDO_DEL_MARK_REC`)는 [09] `row_purge_del_mark` 로 가서 행 전체를 인덱스에서 지운다. 키 열을 바꾼 갱신(`TRX_UNDO_UPD_EXIST_REC`)과 외부 저장 열을 바꾼 갱신은 `row_purge_upd_exist_or_extern` 으로 가서, 바뀐 키 열이 들어 있는 세컨더리 인덱스에서 **옛 키의 엔트리**만 지우고 옛 BLOB 을 해제한다. 클러스터드 레코드는 건드리지 않는다. 갱신이 만든 새 버전이 살아 있기 때문이다. 시작할 때 `node->index` 를 클러스터드 다음 인덱스(첫 세컨더리)로 맞춰 두는데, 두 갈래 모두 그 자리부터 세컨더리를 차례로 돈다.

## 위치

`storage` / `innobase` / `row` / `row0purge.cc` L1074-L1137 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0purge.cc#L1074-L1137))

## 실제 코드

함수 전체다. 반환값 false 는 delete-mark purge 가 공간 부족으로 끝나지 못했다는 뜻이고, `row_purge` 가 1초 뒤 다시 시도한다.

`storage` / `innobase` / `row` / `row0purge.cc` L1067-L1137 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0purge.cc#L1067-L1137))

```cpp
// row0purge.cc L1067-L1137
/** Purges the parsed record.
@param[in,out]  node            row purge node
@param[in]      undo_rec        undo record to purge
@param[in,out]  thr             query thread
@param[in]      updated_extern  whether external columns were updated
@param[in,out]  thd             current thread
@return true if purged, false if skipped */
[[nodiscard]] static bool row_purge_record_func(
    purge_node_t *node, trx_undo_rec_t *undo_rec,
    IF_DEBUG(const que_thr_t *thr, ) bool updated_extern, THD *thd) {
  dict_index_t *clust_index;
  bool purged = true;

  ut_ad(!node->found_clust);
  ut_ad(!node->table->skip_alter_undo);

  clust_index = node->table->first_index();

  node->index = clust_index->next();
  ut_ad(!trx_undo_roll_ptr_is_insert(node->roll_ptr));

  switch (node->rec_type) {
    case TRX_UNDO_DEL_MARK_REC:
      purged = row_purge_del_mark(node);
      if (!purged) {
        break;
      }
      MONITOR_INC(MONITOR_N_DEL_ROW_PURGE);
      break;
    default:
      if (!updated_extern) {
        break;
      }
      [[fallthrough]];
    case TRX_UNDO_UPD_EXIST_REC:
      DBUG_EXECUTE_IF("innodb_purge_sleep_12",
                      std::this_thread::sleep_for(std::chrono::seconds(5)););
      row_purge_upd_exist_or_extern_func(IF_DEBUG(thr, ) node, undo_rec);
      MONITOR_INC(MONITOR_N_UPD_EXIST_EXTERN);
      break;
  }

  if (node->update != nullptr) {
    node->update->reset();
  }

  if (node->found_clust) {
    node->pcur.close();
    node->found_clust = false;
  }

  if (node->table != nullptr) {
    if (node->mysql_table != nullptr) {
      close_thread_tables(thd);
      node->mysql_table = nullptr;
    }

    if (dict_table_is_sdi(node->table->id)) {
      dd_table_close(node->table, thd, &node->mdl, false);
      node->table = nullptr;
    } else {
      bool is_aux = node->table->is_fts_aux();
      dd_table_close(node->table, thd, &node->mdl, false);
      if (is_aux && node->parent) {
        dd_table_close(node->parent, thd, &node->parent_mdl, false);
      }
    }
  }

  return (purged);
}
```

갱신 갈래의 앞부분이다. 세컨더리 인덱스마다 이번 갱신이 그 인덱스의 키 열을 바꿨는지 보고, 바꿨으면 부분 행(`node->row`, 옛 값)으로 옛 엔트리를 만들어 지운다.

`storage` / `innobase` / `row` / `row0purge.cc` L698-L746 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0purge.cc#L698-L746))

```cpp
// row0purge.cc L698-L746
static void row_purge_upd_exist_or_extern_func(IF_DEBUG(const que_thr_t *thr, )
                                                   purge_node_t *node,
                                               trx_undo_rec_t *undo_rec) {
  mem_heap_t *heap;

  ut_ad(!node->table->skip_alter_undo);

  if (node->rec_type == TRX_UNDO_UPD_DEL_REC ||
      (node->cmpl_info & UPD_NODE_NO_ORD_CHANGE)) {
    goto skip_secondaries;
  }

  heap = mem_heap_create(1024, UT_LOCATION_HERE);

  while (node->index != nullptr) {
    bool non_mv_upd = false;

    dict_table_skip_corrupt_index(node->index);

    row_purge_skip_uncommitted_virtual_index(node->index);

    if (!node->index) {
      break;
    }

#ifndef UNIV_DEBUG
    que_thr_t *thr = nullptr;
#endif

    if (row_upd_changes_ord_field_binary(
            node->index, node->update, thr, nullptr, nullptr,
            (node->index->is_multi_value() ? &non_mv_upd : nullptr))) {
      if (node->index->is_multi_value()) {
        row_purge_remove_multi_sec_if_poss(node, heap, !non_mv_upd);
      } else {
        /* Build the older version of the index entry */
        dtuple_t *entry = row_build_index_entry_low(
            node->row, nullptr, node->index, heap, ROW_BUILD_FOR_PURGE);
        row_purge_remove_sec_if_poss(node, node->index, entry);
        mem_heap_empty(heap);
      }
    }

    node->index = node->index->next();
  }

  mem_heap_free(heap);

skip_secondaries:
```

## 동작 흐름

```text
 row_purge_record_func(node, undo_rec, thr, updated_extern, thd)

 L1083  clust_index = 첫 인덱스
 L1085  node->index = clust_index->next()          첫 세컨더리부터
 L1088  switch (rec_type)
 L1089    TRX_UNDO_DEL_MARK_REC
 L1090      purged = [09] row_purge_del_mark(node)
 L1096    default (UPD_DEL_REC 등)
 L1097      외부 저장 변경이 없으면 아무것도 안 한다
 L1101    TRX_UNDO_UPD_EXIST_REC (또는 위에서 외부 저장 변경이 있어 내려옴)
 L1104      row_purge_upd_exist_or_extern
 L1109  update 벡터 reset
 L1113  클러스터드 커서를 썼으면 close
 L1118  테이블을 닫는다 (MySQL TABLE, dd_table_close 로 MDL 해제)
 L1136  return purged
```

같은 행에 일어난 세 가지 일이 purge 에서 어떻게 다르게 치워지는지 보자. 테이블 `t(id PK, k, v)` 에 세컨더리 인덱스 `idx_k(k)` 가 있다.

```text
 사용자 문장                undo 종류        purge 가 지우는 것
 -------------------------  ---------------  -------------------------------------------------
 UPDATE t SET v=2 WHERE id=1  UPD_EXIST_REC    없음. 키 열(k)을 안 바꿨다 (cmpl_info 에
                              (키 변경 없음)     UPD_NODE_NO_ORD_CHANGE). [05] 에서 이미 건너뛴다
 UPDATE t SET k=9 WHERE id=1  UPD_EXIST_REC    idx_k 의 옛 엔트리 (k=5, id=1)
                              (키 변경)          클러스터드 (id=1) 는 그대로 (새 버전이 살아 있다)
 DELETE FROM t WHERE id=1     DEL_MARK_REC     idx_k 의 엔트리 (k=9, id=1) 와
                                                 클러스터드 레코드 (id=1) 를 B+Tree 에서 실제로 삭제

 UPDATE 가 키를 바꾸면 row_upd_sec_index_entry_low (row0upd.cc L2146) 가 옛 엔트리 (k=5) 를
 delete-mark 하고 (btr_cur_del_mark_set_sec_rec, L2340) 새 엔트리 (k=9) 를 넣는다 (L2377)
 delete-mark 로 남은 옛 엔트리를 지우는 것이 이 함수의 갱신 갈래다
```

```text
 갱신 갈래 (row_purge_upd_exist_or_extern_func, L698)

 L705  UPD_DEL_REC 이거나 키 변경 없음   -> 세컨더리는 건너뛰고 BLOB 만
 L712  세컨더리 인덱스마다
 L727    row_upd_changes_ord_field_binary   이 인덱스의 키 열이 바뀌었나
 L734      옛 엔트리 = row_build_index_entry_low(node->row, index)
 L736      row_purge_remove_sec_if_poss     ([09] 와 같은 삭제 함수)
 L746  skip_secondaries:  갱신 벡터에서 외부 저장 열을 찾아 옛 BLOB 을 해제
```

## 결과가 쓰이는 곳

```text
 purged
      --> row_purge 가 false 면 1초 뒤 해석부터 다시 ([07])
 지워진 세컨더리 엔트리, 클러스터드 레코드
      --> 페이지의 빈자리. 스캔이 건너뛸 delete-mark 레코드가 줄어든다
 MONITOR_N_DEL_ROW_PURGE, MONITOR_N_UPD_EXIST_EXTERN
      --> INFORMATION_SCHEMA.INNODB_METRICS 의 purge 계수
```

## 다루지 않는 것

옛 BLOB 해제의 세부(`lob::purge`, undo 의 roll_ptr 로 BLOB 소유를 확인하는 과정, L746 이후), 다중 값 인덱스(`row_purge_remove_multi_sec_if_poss`), 아직 커밋되지 않은 가상 열 인덱스 건너뛰기, 손상된 인덱스 건너뛰기는 이 흐름의 곁가지라 줄만 적었다. 세컨더리 엔트리를 실제로 지우는 `row_purge_remove_sec_if_poss` 는 [09](../09_row_purge_del_mark/README.md)에서 본다.
