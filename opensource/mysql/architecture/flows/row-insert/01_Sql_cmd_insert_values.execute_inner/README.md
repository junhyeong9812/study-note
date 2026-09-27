# Sql_cmd_insert_values::execute_inner

상위: [행 쓰기 (handler -> row0ins)](../README.md)

**`INSERT ... VALUES` 와 `REPLACE ... VALUES` 의 실행 본체다.** 문장 단위 준비(핸들러 힌트, bulk insert 시작, 트리거 준비)를 한 번 하고, VALUES 목록을 한 행씩 `record[0]` 에 채워 [02] `write_record` 에 넘긴다. 볼거리는 한 행이 엔진에 가기 전에 서버 계층에서 거치는 검사 순서와, 오류가 나면 거기서 루프를 멈춘다는 점이다.

## 위치

`sql` / `sql_insert.cc` L482-L839 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_insert.cc#L482-L839))

## 실제 코드

문장 단위 준비다. 중복 처리 방식을 엔진에 `ha_extra` 로 알리고, 행 수를 넘겨 bulk insert 를 시작한다.

`sql` / `sql_insert.cc` L572-L605 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_insert.cc#L572-L605))

```cpp
// sql_insert.cc L572-L605
    insert_table->next_number_field = insert_table->found_next_number_field;

    THD_STAGE_INFO(thd, stage_update);
    if (duplicates == DUP_REPLACE &&
        (!insert_table->triggers ||
         !insert_table->triggers->has_delete_triggers()))
      insert_table->file->ha_extra(HA_EXTRA_WRITE_CAN_REPLACE);
    if (duplicates == DUP_UPDATE)
      insert_table->file->ha_extra(HA_EXTRA_INSERT_WITH_UPDATE);
    /*
      let's *try* to start bulk inserts. It won't necessary
      start them as insert_many_values.elements should be greater than
      some - handler dependent - threshold.
      We should not start bulk inserts if this statement uses
      functions or invokes triggers since they may access
      to the same table and therefore should not see its
      inconsistent state created by this optimization.
      So we call start_bulk_insert to perform nesessary checks on
      insert_many_values.elements, and - if nothing else - to initialize
      the code to make the call of end_bulk_insert() below safe.
    */
    if (duplicates != DUP_ERROR || lex->is_ignore())
      insert_table->file->ha_extra(HA_EXTRA_IGNORE_DUP_KEY);
    /*
       This is a simple check for the case when the table has a trigger
       that reads from it, or when the statement invokes a stored function
       that reads from the table being inserted to.
       Engines can't handle a bulk insert in parallel with a read form the
       same table in the same connection.
    */
    if (thd->locked_tables_mode <= LTM_LOCK_TABLES)
      insert_table->file->ha_start_bulk_insert(insert_many_values.size());

    prepare_triggers_for_insert_stmt(thd, insert_table);
```

행 루프다. 기본값 복원, 값 채우기, 제약 검사를 지나야 `write_record` 에 닿는다.

`sql` / `sql_insert.cc` L622-L690 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_insert.cc#L622-L690))

```cpp
// sql_insert.cc L622-L690
    for (const List_item *values : insert_many_values) {
      Autoinc_field_has_explicit_non_null_value_reset_guard after_each_row(
          insert_table);

      restore_record(insert_table, s->default_values);  // Get empty record
      /*
        Check whether default values of the insert_field_list not specified in
        column list are correct or not.
      */
      if (validate_default_values_of_unset_fields(thd, insert_table)) {
        has_error = true;
        break;
      }
      if (fill_record_n_invoke_before_triggers(
              thd, &info, insert_field_list, *values, insert_table,
              TRG_EVENT_INSERT, insert_table->s->fields, true, nullptr)) {
        assert(thd->is_error());
        /*
          TODO: Convert warnings to errors if values_list.elements == 1
          and check that all items return warning in case of problem with
          storing field.
        */
        has_error = true;
        break;
      }

      if (check_that_all_fields_are_given_values(thd, insert_table,
                                                 table_list)) {
        assert(thd->is_error());
        has_error = true;
        break;
      }

      const int check_result = table_list->view_check_option(thd);
      if (check_result == VIEW_CHECK_SKIP)
        continue;
      else if (check_result == VIEW_CHECK_ERROR) {
        has_error = true;
        break;
      }

      if (invoke_table_check_constraints(thd, insert_table)) {
        if (thd->is_error()) {
          has_error = true;
          break;
        }
        // continue when IGNORE clause is used.
        continue;
      }

      if (use_sql_fk_checks_for_table(thd, insert_table)) {
        if (check_all_parent_fk_ref(thd, insert_table,
                                    enum_fk_dml_type::FK_INSERT)) {
          if (thd->is_error()) {
            has_error = true;
            break;
          }
          // continue when IGNORE clause is used.
          continue;
        }
      }

      if (write_record(thd, insert_table, &info, &update)) {
        has_error = true;
        break;
      }
      thd->get_stmt_da()->inc_current_row_for_condition();
    }
  }  // Statement plan is available within these braces
```

모든 행이 끝난 뒤다. bulk insert 는 오류가 있어도 반드시 닫는다.

`sql` / `sql_insert.cc` L698-L706 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_insert.cc#L698-L706))

```cpp
// sql_insert.cc L698-L706
  {
    /* TODO: Only call this if insert_table->found_next_number_field.*/
    insert_table->file->ha_release_auto_increment();
    /*
      Make sure 'end_bulk_insert()' is called regardless of current error
    */
    int loc_error = 0;
    if (thd->locked_tables_mode <= LTM_LOCK_TABLES)
      loc_error = insert_table->file->ha_end_bulk_insert();
```

클라이언트에 돌려줄 LAST_INSERT_ID 를 정하는 규칙이다.

`sql` / `sql_insert.cc` L777-L791 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_insert.cc#L777-L791))

```cpp
// sql_insert.cc L777-L791
  const ulonglong id =
      (thd->first_successful_insert_id_in_cur_stmt > 0)
          ? thd->first_successful_insert_id_in_cur_stmt
          : (thd->arg_of_last_insert_id_function
                 ? thd->first_successful_insert_id_in_prev_stmt
                 : ((insert_table->next_number_field && info.stats.copied)
                        ? insert_table->next_number_field->val_int()
                        : 0));
  insert_table->next_number_field = nullptr;

  // Remember to restore warning handling before leaving
  thd->check_for_truncated_fields = CHECK_FIELD_IGNORE;

  assert(has_error == thd->get_stmt_da()->is_error());
  if (has_error) return true;
```

## 동작 흐름

```text
 L498  manage_defaults       열 목록이 있거나 VALUES () 이면 기본값을 관리한다
 L509  JSON duality view 면 jdv_insert 로 빠진다
 L523  REPLACE / ON DUPLICATE KEY UPDATE 면 prepare_for_positional_update
 L537  파티션 가지치기가 prepare 에서 안 끝났으면 여기서 한다

 L561  Modification_plan       EXPLAIN 이면 L566 에서 계획만 보여 주고 끝
 L572  next_number_field       AUTO_INCREMENT 열을 핸들러가 채우도록 연결
 L575  REPLACE, DELETE 트리거 없음 -> HA_EXTRA_WRITE_CAN_REPLACE
 L579  ON DUPLICATE KEY UPDATE      -> HA_EXTRA_INSERT_WITH_UPDATE
 L593  IGNORE 또는 중복 처리 있음   -> HA_EXTRA_IGNORE_DUP_KEY
 L602  LOCK TABLES 모드 이하면 ha_start_bulk_insert(행 수)
 L612  한 행짜리 INSERT(IGNORE 아님)는 NOT NULL 열의 NULL 을 오류로, 여러 행이면 경고로

 L622  for (values : insert_many_values)
 L626    restore_record(default_values)             빈 행 = 테이블 기본값
 L631    validate_default_values_of_unset_fields
 L635    fill_record_n_invoke_before_triggers       VALUES 값을 열에 넣고 BEFORE INSERT 트리거
 L648    check_that_all_fields_are_given_values     기본값 없는 NOT NULL 열 검사
 L655    view_check_option                          SKIP 이면 다음 행, ERROR 면 중단
 L663    invoke_table_check_constraints             IGNORE 면 이 행만 건너뜀
 L672    SQL 계층 FK 검사를 쓰는 테이블이면 check_all_parent_fk_ref
 L684    [02] write_record                          --> 엔진으로
 L688    inc_current_row_for_condition              경고 메시지의 "row N" 번호

 L700  ha_release_auto_increment    미리 잡아 둔 AUTO_INCREMENT 구간을 돌려준다
 L706  ha_end_bulk_insert
 L757  binlog_query                 binlog 가 열려 있으면
 L777  id                           LAST_INSERT_ID 결정
 L791  has_error 면 true, 아니면 L796 / L817 my_ok
```

행 하나가 `write_record` 에 닿기 전에 지나는 검사는 순서가 정해져 있다. 앞 단계에서 걸리면 뒤 단계와 엔진은 그 행을 보지 못한다.

```text
 한 행의 관문 (위에서 아래로)

 L631  기본값 유효성
         실패 -> has_error, 루프 중단
 L635  값 채우기 + BEFORE 트리거
         실패 -> has_error, 루프 중단
 L648  모든 열에 값이 있는가
         실패 -> has_error, 루프 중단
 L655  뷰 CHECK OPTION
         SKIP -> 그 행만 버림, ERROR -> 루프 중단
 L663  CHECK 제약
         오류 -> 루프 중단, IGNORE 경고 -> 그 행만 버림
 L673  SQL 계층 FK (부모 행 존재)
         오류 -> 루프 중단, IGNORE 경고 -> 그 행만 버림
 L684  write_record (엔진)
         실패 -> has_error, 루프 중단

 루프를 멈춰도 앞선 행들은 이 함수가 되돌리지 않는다
 되돌리는 코드는 이 함수 안에 없고, 문장 단위 롤백은 호출한 쪽의 몫이다
```

```text
 LAST_INSERT_ID 로 돌려주는 값 (L777-L784)

 앞에서부터 처음 맞는 것
 1  first_successful_insert_id_in_cur_stmt    이번 문장에서 자동 생성 값을 성공적으로 넣었다
 2  first_successful_insert_id_in_prev_stmt   LAST_INSERT_ID(X) 를 불렀다
 3  next_number_field->val_int()              AUTO_INCREMENT 열이 있고 복사된 행이 있다
 4  0                                         그 밖
```

## 결과가 쓰이는 곳

```text
 record[0] (한 행씩 채운 서버 형식의 행 버퍼)
      --> [02] write_record -> [03] ha_write_row(record[0]) -> [04] ha_innobase::write_row

 info.stats
      --> [02] 가 records, copied, deleted, updated 를 올리고 L796 / L817 my_ok 가 읽는다

 ha_start_bulk_insert / ha_end_bulk_insert
      --> 엔진이 여러 행을 한꺼번에 받을 준비를 한다 (구현은 엔진마다 다르다)
```

## 다루지 않는 것

JSON duality view(`jdv::jdv_insert`), 파티션 가지치기(`can_prune_insert`, `prune_partitions`), 트리거 본문(`fill_record_n_invoke_before_triggers` 안쪽), CHECK 제약과 SQL 계층 FK 검사의 내부, binlog 문장 기록(`THD::binlog_query`)의 형식 분기는 이 함수의 곁가지라 줄만 적었다. `INSERT ... SELECT` 는 이 함수가 아니라 `Query_result_insert` 경로를 탄다.
