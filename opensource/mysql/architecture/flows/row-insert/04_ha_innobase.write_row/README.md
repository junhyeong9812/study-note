# ha_innobase::write_row

상위: [행 쓰기 (handler -> row0ins)](../README.md)

**handler 인터페이스를 InnoDB 가 구현한 자리다.** 여기서부터 InnoDB 의 트랜잭션 객체 `trx_t` 와 테이블별 캐시 `row_prebuilt_t`(`m_prebuilt`)가 주인공이 된다. 하는 일은 셋이다. AUTO_INCREMENT 값을 정하고, MySQL 형식과 InnoDB 형식을 잇는 템플릿을 준비하고, [05] `row_insert_for_mysql` 이 돌려준 `dberr_t` 를 MySQL 오류 코드로 바꾼다.

## 위치

`storage` / `innobase` / `handler` / `ha_innodb.cc` L9256-L9454 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/ha_innodb.cc#L9256-L9454))

## 실제 코드

들어오자마자 하는 검사다. 강제로 중단된 트랜잭션, 읽기 전용 서버, 핸들과 스레드의 트랜잭션 불일치를 거른다.

`storage` / `innobase` / `handler` / `ha_innodb.cc` L9256-L9300 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/ha_innodb.cc#L9256-L9300))

```cpp
// ha_innodb.cc L9256-L9300
int ha_innobase::write_row(uchar *record) /*!< in: a row in MySQL format */
{
  dberr_t error;
  int error_result = 0;
  bool auto_inc_used = false;

  DBUG_TRACE;

  /* Increase the write count of handler */
  ha_statistic_increment(&System_status_var::ha_write_count);

  if (m_prebuilt->table->is_intrinsic()) {
    return intrinsic_table_write_row(record);
  }

  trx_t *trx = thd_to_trx(m_user_thd);

  TrxInInnoDB trx_in_innodb(trx);

  if (!m_prebuilt->table->is_intrinsic() && trx_in_innodb.is_aborted()) {
    innobase_rollback(ht, m_user_thd, false);

    return convert_error_code_to_mysql(DB_FORCED_ABORT, 0, m_user_thd);
  }

  /* Validation checks before we commence write_row operation. */
  if (high_level_read_only) {
    ib_senderrf(ha_thd(), IB_LOG_LEVEL_WARN, ER_READ_ONLY_MODE);
    return HA_ERR_TABLE_READONLY;
  } else if (m_prebuilt->trx != trx) {
    // ... (L9286-L9297 생략: trx 불일치 시 메모리 덤프 후 ut_error)
  } else if (!trx_is_started(trx)) {
    ++trx->will_lock;
  }
```

AUTO_INCREMENT 처리와 삽입 호출이다.

`storage` / `innobase` / `handler` / `ha_innodb.cc` L9302-L9350 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/ha_innodb.cc#L9302-L9350))

```cpp
// ha_innodb.cc L9302-L9350
  /* Handling of Auto-Increment Columns. */
  if (table->next_number_field && record == table->record[0]) {
    /* Reset the error code before calling
    innobase_get_auto_increment(). */
    m_prebuilt->autoinc_error = DB_SUCCESS;

    error_result = update_auto_increment();
    // ... (L9309-L9326 생략: update_auto_increment 오류 분기)

    auto_inc_used = true;
  }

  /* Prepare INSERT graph that will be executed for actual INSERT
  (This is a one time operation) */
  if (m_prebuilt->mysql_template == nullptr ||
      m_prebuilt->template_type != ROW_MYSQL_WHOLE_ROW) {
    /* Build the template used in converting quickly between
    the two database formats */

    build_template(true);
  }

  error = innobase_srv_conc_enter_innodb(m_prebuilt);

  if (error != DB_SUCCESS) {
    goto report_error;
  }

  /* Execute insert graph that will result in actual insert. */
  error = row_insert_for_mysql((byte *)record, m_prebuilt);

  DEBUG_SYNC(m_user_thd, "ib_after_row_insert");
```

오류 코드를 바꿔 돌려주는 꼬리다.

`storage` / `innobase` / `handler` / `ha_innodb.cc` L9433-L9454 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/ha_innodb.cc#L9433-L9454))

```cpp
// ha_innodb.cc L9433-L9454
  innobase_srv_conc_exit_innodb(m_prebuilt);

report_error:
  /* Cleanup and exit. */
  if (error == DB_TABLESPACE_DELETED) {
    ib_senderrf(trx->mysql_thd, IB_LOG_LEVEL_ERROR, ER_TABLESPACE_DISCARDED,
                table->s->table_name.str);
  }

  error_result =
      convert_error_code_to_mysql(error, m_prebuilt->table->flags, m_user_thd);

  if (error_result == HA_FTS_INVALID_DOCID) {
    my_error(HA_FTS_INVALID_DOCID, MYF(0));
  }

func_exit:

  innobase_active_small();

  return error_result;
}
```

## 동작 흐름

```text
 L9265  ha_write_count++                     상태 변수 Handler_write (mysqld.cc L11821)
 L9267  내부 임시 테이블이면 intrinsic_table_write_row (L9011) 로 빠진다
 L9271  trx = thd_to_trx(m_user_thd)         이 연결의 InnoDB 트랜잭션
 L9273  TrxInInnoDB                           이 트랜잭션이 InnoDB 안에 있다는 표시 (범위 객체)
 L9275  강제 중단된 트랜잭션이면 innobase_rollback, DB_FORCED_ABORT
 L9282  high_level_read_only  -> HA_ERR_TABLE_READONLY
 L9285  m_prebuilt->trx != trx -> 메모리 덤프 후 ut_error
 L9298  트랜잭션이 아직 시작 전이면 ++trx->will_lock

 L9303  AUTO_INCREMENT 열이 있고 record[0] 에 쓰는 중이면
 L9308    update_auto_increment()             서버 계층 handler 가 값을 정하고
                                              InnoDB 의 get_auto_increment 에서 구간을 받는다
 L9328    auto_inc_used = true
 L9333  mysql_template 이 없거나 행 전체용이 아니면 build_template(true)
 L9341  innobase_srv_conc_enter_innodb       innodb_thread_concurrency 가 걸려 있으면 입장 대기
 L9348  row_insert_for_mysql(record, m_prebuilt)   --> [05]

 L9353  auto_inc_used 면 결과에 따라 테이블의 AUTO_INCREMENT 상한을 올린다
          DB_DUPLICATE_KEY  REPLACE, INSERT ... SELECT 류, LOAD DATA REPLACE 면 올린다
          DB_SUCCESS        넣은 값 >= autoinc_last_value 면 올린다
          L9420 innobase_set_max_autoinc(next)
 L9433  innobase_srv_conc_exit_innodb
 L9442  convert_error_code_to_mysql(error)    DB_* -> HA_ERR_*
 L9451  innobase_active_small
```

AUTO_INCREMENT 는 값을 넣기 전에 한 번, 결과를 본 뒤 한 번 다룬다. 사용자가 큰 값을 직접 넣으면 뒤쪽 처리에서 테이블의 다음 값이 그보다 커진다.

```text
 AUTO_INCREMENT 두 번 (auto_inc_used 일 때)

 앞  L9308  update_auto_increment           record 의 AUTO_INCREMENT 열이 비었으면 값을 채운다
 뒤  L9367  col_max_value = 열 타입의 최댓값
     L9370  auto_inc = 실제로 넣으려던 값
     L9407  auto_inc <= col_max_value 이면
     L9417    innobase_next_autoinc(auto_inc, 1, increment, offset, max)
     L9420    innobase_set_max_autoinc                테이블 카운터를 올린다
```

```text
 dberr_t 에서 MySQL 오류로 (convert_error_code_to_mysql 의 예, ha_innodb.cc)

 DB_SUCCESS          0
 DB_DUPLICATE_KEY    HA_ERR_FOUND_DUPP_KEY   (L2136-L2143)
 그 밖               오류마다 HA_ERR_* 하나. 모르는 값은 HA_ERR_GENERIC (L2132-L2134)
```

## 결과가 쓰이는 곳

```text
 m_prebuilt (row_prebuilt_t)
      --> [05] [06] 이 여기에 insert 그래프(ins_graph, ins_node)를 만들어 둔다
      --> mysql_template 이 [06] row_mysql_convert_row_to_innobase 의 변환표가 된다

 반환값 (HA_ERR_*)
      --> [03] handler::ha_write_row -> [02] write_record

 테이블 AUTO_INCREMENT 카운터
      --> 다음 행의 update_auto_increment 가 여기서 값을 받는다
```

## 다루지 않는 것

AUTO_INCREMENT 잠금 모드(`innodb_autoinc_lock_mode`)와 `get_auto_increment` 의 구간 예약, `build_template` 의 필드별 변환 규칙, `innodb_thread_concurrency` 대기열(`srv_conc_enter_innodb`), 내부 임시 테이블 경로(`intrinsic_table_write_row`), `TrxInInnoDB` 의 강제 롤백 처리는 곁가지라 줄만 적었다.
