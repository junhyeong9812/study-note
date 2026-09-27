# row_ins_index_entry_step

상위: [행 쓰기 (handler -> row0ins)](../README.md)

**인덱스 하나에 대한 한 걸음이다.** 행 틀(`node->row`)의 값을 이 인덱스의 엔트리 틀(`node->entry`)에 연결하고, 인덱스 종류에 따라 클러스터드, multi-value 세컨더리, 보통 세컨더리 중 하나로 보낸다. 볼거리는 값을 **복사하지 않고 포인터로 연결한다**는 점과, 접두 인덱스와 공간 인덱스가 여기서 값을 바꾼다는 점이다. 이 문서는 L3499 가 부르는 분기 함수 `row_ins_index_entry` 를 함께 본다.

## 위치

`storage` / `innobase` / `row` / `row0ins.cc` L3481-L3505 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0ins.cc#L3481-L3505))

## 실제 코드

`storage` / `innobase` / `row` / `row0ins.cc` L3481-L3505 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0ins.cc#L3481-L3505))

```cpp
// row0ins.cc L3481-L3505
[[nodiscard]] static dberr_t row_ins_index_entry_step(
    ins_node_t *node, /*!< in: row insert node */
    que_thr_t *thr)   /*!< in: query thread */
{
  dberr_t err;

  DBUG_TRACE;

  ut_ad(dtuple_check_typed(node->row));

  err = row_ins_index_entry_set_vals(node->index, node->entry, node->row);

  if (err != DB_SUCCESS) {
    return err;
  }

  ut_ad(dtuple_check_typed(node->entry));

  err = row_ins_index_entry(node->index, node->entry, node->ins_multi_val_pos,
                            thr);

  DEBUG_SYNC(thr_get_trx(thr)->mysql_thd, "after_row_ins_index_entry_step");

  return err;
}
```

엔트리 틀의 필드마다 행 틀에서 같은 열을 찾아 데이터 포인터를 넘긴다.

`storage` / `innobase` / `row` / `row0ins.cc` L3401-L3476 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0ins.cc#L3401-L3476))

```cpp
// row0ins.cc L3401-L3476
dberr_t row_ins_index_entry_set_vals(const dict_index_t *index, dtuple_t *entry,
                                     const dtuple_t *row) {
  ulint n_fields;
  ulint i;
  ulint num_v = dtuple_get_n_v_fields(entry);

  n_fields = dtuple_get_n_fields(entry);

  for (i = 0; i < n_fields + num_v; i++) {
    dict_field_t *ind_field = nullptr;
    dfield_t *field;
    const dfield_t *row_field;
    ulint len;
    dict_col_t *col;

    if (i >= n_fields) {
      /* This is virtual field */
      field = dtuple_get_nth_v_field(entry, i - n_fields);
      col = &dict_table_get_nth_v_col(index->table, i - n_fields)->m_col;
    } else {
      field = dtuple_get_nth_field(entry, i);
      ind_field = index->get_field(i);
      col = ind_field->col;
      ut_ad(!col->is_instant_dropped());
    }

    if (col->is_virtual()) {
      const dict_v_col_t *v_col = reinterpret_cast<const dict_v_col_t *>(col);
      ut_ad(dtuple_get_n_fields(row) == index->table->get_n_cols());
      row_field = dtuple_get_nth_v_field(row, v_col->v_pos);
    } else {
      ut_ad(ind_field != nullptr);
      row_field = dtuple_get_nth_field(row, ind_field->col->ind);
    }

    len = dfield_get_len(row_field);

    /* Check column prefix indexes */
    if (ind_field != nullptr && ind_field->prefix_len > 0 &&
        dfield_get_len(row_field) != UNIV_SQL_NULL) {
      const dict_col_t *col = ind_field->col;

      len = dtype_get_at_most_n_mbchars(
          col->prtype, col->mbminmaxlen, ind_field->prefix_len, len,
          static_cast<const char *>(dfield_get_data(row_field)));

      ut_ad(!dfield_is_ext(row_field));
    }

    // ... (L3450-L3466 생략: 공간 인덱스의 첫 필드를 MBR 로 바꾸는 분기)

    dfield_set_data(field, dfield_get_data(row_field), len);
    if (dfield_is_ext(row_field)) {
      ut_ad(index->is_clustered());
      dfield_set_ext(field);
    }
  }

  return (DB_SUCCESS);
}
```

L3499 가 부르는 분기다.

`storage` / `innobase` / `row` / `row0ins.cc` L3351-L3368 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0ins.cc#L3351-L3368))

```cpp
// row0ins.cc L3351-L3368
static dberr_t row_ins_index_entry(dict_index_t *index, dtuple_t *entry,
                                   uint32_t &multi_val_pos, que_thr_t *thr) {
  ut_ad(thr_get_trx(thr)->id != 0);

  DBUG_EXECUTE_IF("row_ins_index_entry_timeout", {
    DBUG_SET("-d,row_ins_index_entry_timeout");
    return (DB_LOCK_WAIT);
  });

  if (index->is_clustered()) {
    return (row_ins_clust_index_entry(index, entry, thr, false));
  } else if (index->is_multi_value()) {
    return (
        row_ins_sec_index_multi_value_entry(index, entry, multi_val_pos, thr));
  } else {
    return (row_ins_sec_index_entry(index, entry, thr, false));
  }
}
```

## 동작 흐름

```text
 L3491  row_ins_index_entry_set_vals(index, entry, row)
          L3409  엔트리 필드마다 (가상 열 포함)
          L3421    일반 필드: ind_field = index->get_field(i), col = ind_field->col
          L3433    row_field = row 의 col->ind 번째 필드       같은 열을 행 틀에서 찾는다
          L3439    접두 인덱스(prefix_len > 0)면 len 을 문자 수 기준으로 자른다
          L3452    공간 인덱스의 0 번 필드면 MBR 로 바꿔 쓴다
          L3468    dfield_set_data(field, row_field 의 데이터, len)   포인터 연결
          L3469    외부 저장(off-page) 열이면 엔트리에도 ext 표시 (클러스터드만)
 L3493  실패면 그대로 반환 (DB_CANT_CREATE_GEOMETRY_OBJECT 등)

 L3499  row_ins_index_entry(index, entry, ins_multi_val_pos, thr)
          L3360  클러스터드       -> [10] row_ins_clust_index_entry
          L3362  multi-value      -> row_ins_sec_index_multi_value_entry
                                     값마다 [11] 을 부르고, 실패하면 위치를 ins_multi_val_pos 에 기억
          L3366  그 밖 세컨더리    -> [11] row_ins_sec_index_entry
```

값을 연결만 하므로 행 틀과 엔트리 틀은 같은 바이트를 가리킨다. [07] 이 DB_TRX_ID 칸에 쓴 값도 이 연결로 클러스터드 엔트리에 그대로 보인다.

```text
 포인터 연결 (row 와 entry 가 같은 데이터를 본다)

 node->row      [id=7][a=3][b=9][DB_ROW_ID][DB_TRX_ID][DB_ROLL_PTR]
                  |     |    |                  |           |
 entry0 PRIMARY  [id]  ...                    [TRX_ID]   [ROLL_PTR]  ...
 entry1 idx_a   [a] [id]
                 |    |
                 +----+-- dfield_set_data 가 row 쪽 버퍼 주소를 넘긴 것

 예외 둘
   접두 인덱스   같은 주소, 길이만 짧게 (L3443 dtype_get_at_most_n_mbchars)
   공간 인덱스   엔트리 필드에 MBR 을 새로 써 넣는다 (L3458 row_ins_spatial_index_entry_set_mbr_field)
```

## 결과가 쓰이는 곳

```text
 node->entry (값이 채워진 인덱스 엔트리)
      --> [10] / [11] 을 거쳐 [B+Tree 삽입과 분할] 의 btr_cur_optimistic_insert 로 간다
      --> 클러스터드 엔트리의 DB_ROLL_PTR 칸에는 아직 이 행의 값이 없다.
          btr_cur_ins_lock_and_undo 가 undo 를 쓴 뒤 그 버퍼에 제자리로 써 넣는다 (btr0cur.cc L2626)

 ins_multi_val_pos
      --> multi-value 인덱스가 잠금 대기로 멈추면 다음 run_again 이 이 위치부터 넣는다
```

## 다루지 않는 것

가상 열(`dtuple_get_nth_v_field`), multi-value 인덱스의 값 풀기(`Multi_value_entry_builder_insert`), 공간 인덱스의 MBR 계산과 SRID 검사, 접두 길이의 문자셋별 계산은 곁가지라 줄만 적었다.
