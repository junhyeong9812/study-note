# ha_innobase::index_read

상위: [일관 읽기(MVCC)와 undo 체인](../README.md)

**서버 계층의 "이 키로 인덱스를 찾아 첫 행을 달라"를 InnoDB 의 검색 호출로 옮기는 자리다.** MySQL 형식의 키 바이트를 InnoDB 의 검색 튜플(`dtuple_t`)로 바꾸고, `HA_READ_KEY_EXACT` 같은 서버 검색 플래그를 `PAGE_CUR_GE` 같은 커서 모드로 바꾼 뒤 [02] `row_search_mvcc` 를 부른다. 잠금 읽기인지 잠금 없는 읽기인지는 여기서 정하지 않는다. 그 값(`m_prebuilt->select_lock_type`)은 문장을 시작할 때 `store_lock` 과 `external_lock` 이 이미 정해 두었다.

## 위치

`storage` / `innobase` / `handler` / `ha_innodb.cc` L10430-L10616 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/ha_innodb.cc#L10430-L10616))

## 실제 코드

앞부분은 인덱스 상태 확인과 검색 템플릿 준비다. 디버그 빌드에서만 도는 템플릿 비교(L10481-L10496)는 뺐다. 템플릿은 "어느 열을 MySQL 행 버퍼의 어디에 복사할지"를 적은 표로, 문장의 첫 호출에서만 다시 만든다.

`storage` / `innobase` / `handler` / `ha_innodb.cc` L10430-L10480 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/ha_innodb.cc#L10430-L10480))

```cpp
// ha_innodb.cc L10430-L10480
int ha_innobase::index_read(
    // ... (L10431-L10442 생략: 매개변수 주석)
    enum ha_rkey_function find_flag) /*!< in: search flags from my_base.h */
{
  DBUG_TRACE;
  DEBUG_SYNC_C("ha_innobase_index_read_begin");

  ut_a(m_prebuilt->trx == thd_to_trx(m_user_thd));
  ut_ad(key_len != 0 || find_flag != HA_READ_KEY_EXACT);

  ha_statistic_increment(&System_status_var::ha_read_key_count);

  dict_index_t *index = m_prebuilt->index;

  if (index == nullptr || index->is_corrupted()) {
    m_prebuilt->index_usable = false;
    return HA_ERR_CRASHED;
  }

  if (!m_prebuilt->index_usable) {
    return index->is_corrupted() ? HA_ERR_INDEX_CORRUPT
                                 : HA_ERR_TABLE_DEF_CHANGED;
  }

  if (index->type & DICT_FTS) {
    return HA_ERR_KEY_NOT_FOUND;
  }

  /* For R-Tree index, we will always place the page lock to
  pages being searched */
  if (dict_index_is_spatial(index)) {
    ++m_prebuilt->trx->will_lock;
  }

  /* Note that if the index for which the search template is built is not
  necessarily m_prebuilt->index, but can also be the clustered index */

  if (m_prebuilt->sql_stat_start && !can_reuse_mysql_template()) {
    build_template(false);
  }
```

검색 키와 범위 끝 키를 InnoDB 튜플로 바꾸고, 서버의 검색 플래그를 커서 모드와 일치 모드로 옮긴다.

`storage` / `innobase` / `handler` / `ha_innodb.cc` L10497-L10535 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/ha_innodb.cc#L10497-L10535))

```cpp
// ha_innodb.cc L10497-L10535

  if (key_ptr != nullptr) {
    /* Convert the search key value to InnoDB format into
    m_prebuilt->search_tuple */

    row_sel_convert_mysql_key_to_innobase(
        m_prebuilt->search_tuple, m_prebuilt->srch_key_val1,
        m_prebuilt->srch_key_val_len, index, key_ptr, key_len);

    assert(m_prebuilt->search_tuple->n_fields > 0);
  } else {
    /* We position the cursor to the last or the first entry
    in the index */

    dtuple_set_n_fields(m_prebuilt->search_tuple, 0);
  }

  ut_ad(m_prebuilt->m_mysql_handler == this);
  m_prebuilt->m_stop_tuple_found = false;
  if (end_range != nullptr) {
    row_sel_convert_mysql_key_to_innobase(
        m_prebuilt->m_stop_tuple, m_prebuilt->srch_key_val2,
        m_prebuilt->srch_key_val_len, index, end_range->key, end_range->length);
  } else {
    dtuple_set_n_fields(m_prebuilt->m_stop_tuple, 0);
  }

  page_cur_mode_t mode = convert_search_mode_to_innobase(find_flag);

  ulint match_mode = 0;

  if (find_flag == HA_READ_KEY_EXACT) {
    match_mode = ROW_SEL_EXACT;

  } else if (find_flag == HA_READ_PREFIX_LAST) {
    match_mode = ROW_SEL_EXACT_PREFIX;
  }

  m_last_match_mode = (uint)match_mode;
```

InnoDB 로 들어가는 문턱이다. 동시성 제한(`innodb_thread_concurrency`)을 통과한 뒤, 내부 임시 테이블이 아니면 `row_search_mvcc` 로 간다.

`storage` / `innobase` / `handler` / `ha_innodb.cc` L10537-L10566 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/ha_innodb.cc#L10537-L10566))

```cpp
// ha_innodb.cc L10537-L10566
  dberr_t ret;

  if (mode != PAGE_CUR_UNSUPP) {
    ret = innobase_srv_conc_enter_innodb(m_prebuilt);

    if (ret != DB_SUCCESS) {
      return convert_error_code_to_mysql(ret, m_prebuilt->table->flags,
                                         m_user_thd);
    }

    if (!m_prebuilt->table->is_intrinsic()) {
      if (TrxInInnoDB::is_aborted(m_prebuilt->trx)) {
        innobase_rollback(ht, m_user_thd, false);

        return convert_error_code_to_mysql(DB_FORCED_ABORT, 0, m_user_thd);
      }

      m_prebuilt->ins_sel_stmt = thd_is_ins_sel_stmt(m_user_thd);

      ret = row_search_mvcc(buf, mode, m_prebuilt, match_mode, 0);

    } else {
      m_prebuilt->session = thd_to_innodb_session(m_user_thd);

      ret = row_search_no_mvcc(buf, mode, m_prebuilt, match_mode, 0);
    }

    innobase_srv_conc_exit_innodb(m_prebuilt);
  } else {
    ret = DB_UNSUPPORTED;
```

InnoDB 오류 코드를 서버의 handler 오류 코드로 바꾼다. 끝까지 찾았는데 없으면 `DB_RECORD_NOT_FOUND` 든 `DB_END_OF_INDEX` 든 똑같이 `HA_ERR_KEY_NOT_FOUND` 다.

`storage` / `innobase` / `handler` / `ha_innodb.cc` L10568-L10616 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/ha_innodb.cc#L10568-L10616))

```cpp
// ha_innodb.cc L10568-L10616

  DBUG_EXECUTE_IF("ib_select_query_failure", ret = DB_ERROR;);

  int error;

  switch (ret) {
    case DB_SUCCESS:
      error = 0;
      if (m_prebuilt->table->is_system_table) {
        srv_stats.n_system_rows_read.add(
            thd_get_thread_id(m_prebuilt->trx->mysql_thd), 1);
      } else {
        srv_stats.n_rows_read.add(thd_get_thread_id(m_prebuilt->trx->mysql_thd),
                                  1);
      }
      break;

    case DB_RECORD_NOT_FOUND:
      error = HA_ERR_KEY_NOT_FOUND;
      break;

    case DB_END_OF_INDEX:
      error = HA_ERR_KEY_NOT_FOUND;
      break;

    case DB_TABLESPACE_DELETED:
      ib_senderrf(m_prebuilt->trx->mysql_thd, IB_LOG_LEVEL_ERROR,
                  ER_TABLESPACE_DISCARDED, table->s->table_name.str);

      error = HA_ERR_NO_SUCH_TABLE;
      break;

    case DB_TABLESPACE_NOT_FOUND:

      ib_senderrf(m_prebuilt->trx->mysql_thd, IB_LOG_LEVEL_ERROR,
                  ER_TABLESPACE_MISSING, table->s->table_name.str);

      error = HA_ERR_TABLESPACE_MISSING;
      break;

    default:
      error = convert_error_code_to_mysql(ret, m_prebuilt->table->flags,
                                          m_user_thd);

      break;
  }

  return error;
}
```

## 동작 흐름

```text
 L10455  m_prebuilt->index 가 없거나 손상   -> HA_ERR_CRASHED
 L10460  index_usable 이 false             -> 손상이면 HA_ERR_INDEX_CORRUPT, 아니면 TABLE_DEF_CHANGED
 L10465  FULLTEXT 인덱스                   -> HA_ERR_KEY_NOT_FOUND (FTS 는 다른 경로)
 L10471  공간 인덱스면 will_lock++          (R-tree 는 페이지 잠금을 쓴다)
 L10478  문장의 첫 호출이고 템플릿을 재사용할 수 없으면 build_template(false)

 L10498  key_ptr 이 있으면  row_sel_convert_mysql_key_to_innobase -> search_tuple
         없으면              n_fields = 0 (인덱스의 처음이나 끝에 커서를 둔다)
 L10516  end_range 가 있으면 m_stop_tuple 도 만든다 (범위 끝 판정용)
 L10524  mode = convert_search_mode_to_innobase(find_flag)
 L10528  EXACT -> ROW_SEL_EXACT, PREFIX_LAST -> ROW_SEL_EXACT_PREFIX, 그 밖은 0

 L10539  mode 가 지원되면
 L10540    innobase_srv_conc_enter_innodb      동시성 슬롯
 L10547    일반 테이블
 L10548      강제 롤백 대상이 되었으면 DB_FORCED_ABORT
 L10554      ins_sel_stmt (INSERT ... SELECT 인지)
 L10556      [02] row_search_mvcc(buf, mode, m_prebuilt, match_mode, 0)
 L10561    내부 임시 테이블 -> row_search_no_mvcc
 L10564    innobase_srv_conc_exit_innodb
```

이 함수와 짝을 이루는 "다음 행" 호출들은 같은 `row_search_mvcc` 를 `direction` 만 바꿔 부른다. 처음 한 번만 0 이고, 그 뒤로는 커서를 복원해 한 칸씩 움직인다.

```text
 서버의 읽기 호출과 row_search_mvcc 의 direction

 handler 호출         InnoDB 함수 (ha_innodb.cc)              direction      커서
 ha_index_read_map    index_read L10430                       0              새로 연다
 ha_index_next        index_next L10864 -> general_fetch      ROW_SEL_NEXT   저장한 위치를 복원
 ha_index_prev        index_prev -> general_fetch             ROW_SEL_PREV   저장한 위치를 복원
 ha_rnd_next          rnd_next L11079                         처음은 index_first -> index_read (0)
                                                              그 뒤는 general_fetch (NEXT)

 general_fetch (L10780) 는 PAGE_CUR_UNSUPP 와 direction 을 넘긴다 (L10808)
 direction == 0 일 때만 PHASE 2 의 AHI 지름길을 시도한다 (row0sel.cc L4658)
```

```text
 결과 코드의 번역 (switch, L10573-L10613)

 InnoDB                        서버                     뜻
 DB_SUCCESS                    0                        buf 에 행이 들어 있다. n_rows_read++
 DB_RECORD_NOT_FOUND           HA_ERR_KEY_NOT_FOUND     조건에 맞는 행이 없다
 DB_END_OF_INDEX               HA_ERR_KEY_NOT_FOUND     인덱스 끝에 닿았다
 DB_TABLESPACE_DELETED         HA_ERR_NO_SUCH_TABLE     DISCARD 된 테이블
 DB_TABLESPACE_NOT_FOUND       HA_ERR_TABLESPACE_MISSING
 그 밖 (DB_LOCK_WAIT_TIMEOUT,   convert_error_code_to_mysql
       DB_DEADLOCK, DB_MISSING_HISTORY ...)
```

## 결과가 쓰이는 곳

```text
 buf
      --> 서버 반복자가 이 행으로 WHERE 와 조인을 평가한다
 m_prebuilt->pcur (row_search_mvcc 가 저장한 커서 위치)
      --> 다음 general_fetch 가 같은 위치에서 이어 읽는다
 m_last_match_mode
      --> index_next_same 같은 후속 호출이 같은 일치 모드를 쓴다
```

## 다루지 않는 것

`build_template` 이 만드는 `mysql_row_templ_t` 의 필드별 의미, 키 변환(`row_sel_convert_mysql_key_to_innobase`)의 열 형식별 처리, `general_fetch` 와 `rnd_next` 의 본문, 동시성 슬롯(`srv_conc_enter_innodb`), 내부 임시 테이블의 `row_search_no_mvcc` 는 이 흐름의 곁가지라 요약만 했다. 잠금 모드가 정해지는 `store_lock` 과 `external_lock` 은 [03](../03_trx_assign_read_view/README.md)에서 격리 수준과 함께 본다.
