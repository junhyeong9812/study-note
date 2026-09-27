# Sql_cmd_dml::execute

상위: [명령 디스패치](../README.md)

**SELECT, INSERT, UPDATE, DELETE 가 공유하는 실행 순서의 틀이다.** 준비(테이블 열기와 이름 해석) -> 잠금 -> 실행 -> 정리의 순서가 여기 고정되어 있고, 문장마다 다른 부분만 가상 함수(`precheck`, `prepare_inner`, `execute_inner`)로 뺐다. 볼거리는 잠금이 준비 **뒤**, 최적화 **앞**에 온다는 점이다. 주석이 이유를 적어 두었다. 준비 단계에서 파티션 가지치기를 해 두면 쓰지 않는 파티션은 잠그지 않아도 된다.

## 위치

`sql` / `sql_select.cc` L685-L892 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_select.cc#L685-L892))

## 실제 코드

문장 타이머를 걸고, 데이터 변경 문장이면 IGNORE / strict 오류 핸들러를 건다. 처음 실행이면 `prepare` 로 간다.

`sql` / `sql_select.cc` L685-L728 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_select.cc#L685-L728))

```cpp
// sql_select.cc L685-L728
bool Sql_cmd_dml::execute(THD *thd) {
  DBUG_TRACE;

  lex = thd->lex;

  Query_expression *const unit = lex->unit;

  bool statement_timer_armed = false;
  bool error_handler_active = false;

  Ignore_error_handler ignore_handler;
  Strict_error_handler strict_handler;

  // If statement is preparable, it must be prepared
  assert(owner() == nullptr || is_prepared());
  // If statement is regular, it must be unprepared
  assert(!is_regular() || !is_prepared());
  // If statement is part of SP, it can be both prepared and unprepared.

  // If a timer is applicable to statement, then set it.
  if (is_timer_applicable_to_statement(thd))
    statement_timer_armed = set_statement_timer(thd);

  if (is_data_change_stmt()) {
    // Push ignore / strict error handler
    if (lex->is_ignore()) {
      thd->push_internal_handler(&ignore_handler);
      error_handler_active = true;
      /*
        UPDATE IGNORE can be unsafe. We therefore use row based
        logging if mixed or row based logging is available.
        TODO: Check if the order of the output of the select statement is
        deterministic. Waiting for BUG#42415
      */
      if (lex->sql_command == SQLCOM_UPDATE)
        lex->set_stmt_unsafe(LEX::BINLOG_STMT_UNSAFE_UPDATE_IGNORE);
    } else if (thd->is_strict_mode()) {
      thd->push_internal_handler(&strict_handler);
      error_handler_active = true;
    }
  }

  if (!is_prepared()) {
    if (prepare(thd)) goto err;
```

잠그고 실행한다. 잠금 위치에 대한 설명이 주석에 있다.

`sql` / `sql_select.cc` L766-L798 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_select.cc#L766-L798))

```cpp
// sql_select.cc L766-L798
  }

  if (validate_use_secondary_engine(lex)) goto err;

  lex->set_exec_started();
  lex->reset_crossed_memory_status_limit();

  DBUG_EXECUTE_IF("use_attachable_trx",
                  thd->begin_attachable_ro_transaction(););

  THD_STAGE_INFO(thd, stage_init);

  thd->clear_current_query_costs();

  // Replication may require extra check of data change statements
  if (is_data_change_stmt() && run_before_dml_hook(thd)) goto err;

  // Revertable changes are not supported during preparation
  assert(thd->change_list.is_empty());

  assert(!lex->is_query_tables_locked());
  /*
    Locking of tables is done after preparation but before optimization.
    This allows to do better partition pruning and avoid locking unused
    partitions. As a consequence, in such a case, prepare stage can rely only
    on metadata about tables used and not data from them.
  */
  if (!is_empty_query()) {
    if (lock_tables(thd, lex->query_tables, lex->table_count, 0)) goto err;
  }

  // Perform statement-specific execution
  if (execute_inner(thd)) goto err;
```

성공 경로의 정리다.

`sql` / `sql_select.cc` L823-L851 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_select.cc#L823-L851))

```cpp
// sql_select.cc L823-L851
  if (error_handler_active) thd->pop_internal_handler();

  THD_STAGE_INFO(thd, stage_end);

  // Do partial cleanup (preserve plans for EXPLAIN).
  lex->cleanup(false);
  lex->clear_values_map();
  lex->set_secondary_engine_execution_context(nullptr);

  // Perform statement-specific cleanup for Query_result
  if (result != nullptr) result->cleanup();

  thd->save_current_query_costs();

  thd->update_previous_found_rows();

  DBUG_EXECUTE_IF("use_attachable_trx", thd->end_attachable_transaction(););

  if (statement_timer_armed && thd->timer) reset_statement_timer(thd);

  /*
    This sync point is normally right before thd->query_plan is reset, so
    EXPLAIN FOR CONNECTION can catch the plan. It is copied here as
    after unprepare() EXPLAIN considers the query as "not ready".
    @todo remove in WL#6570 when unprepare() is gone.
  */
  DEBUG_SYNC(thd, "before_reset_query_plan");

  return false;
```

`prepare` 는 권한 검사, 테이블 열기, 문장별 준비를 한다. 테이블 열기가 MDL 을 잡는 자리다.

`sql` / `sql_select.cc` L544-L565 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_select.cc#L544-L565))

```cpp
// sql_select.cc L544-L565
  // Perform a coarse statement-specific privilege check.
  if (precheck(thd)) goto err;

  // Trigger out_of_memory condition inside open_tables_for_query()
  DBUG_EXECUTE_IF("sql_cmd_dml_prepare__out_of_memory",
                  DBUG_SET("+d,simulate_out_of_memory"););
  /*
    Open tables and expand views.
    During prepare of query (not as part of an execute), acquire only
    S metadata locks instead of SW locks to be compatible with concurrent
    LOCK TABLES WRITE and global read lock.
  */
  if (open_tables_for_query(
          thd, lex->query_tables,
          needs_explicit_preparation() ? MYSQL_OPEN_FORCE_SHARED_MDL : 0)) {
    if (thd->is_error())  // @todo - dictionary code should be fixed
      goto err;
    if (error_handler_active) thd->pop_internal_handler();
    lex->cleanup(false);
    return true;
  }
  DEBUG_SYNC(thd, "after_open_tables");
```

`sql` / `sql_select.cc` L580-L597 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_select.cc#L580-L597))

```cpp
// sql_select.cc L580-L597
  {
    const Prepare_error_tracker tracker(thd);
    const Prepared_stmt_arena_holder ps_arena_holder(thd);
    const Enable_derived_merge_guard derived_merge_guard(
        thd, is_show_cmd_using_system_view(thd));

    if (prepare_inner(thd)) goto err;
    if (needs_explicit_preparation() && result != nullptr) {
      result->cleanup();
    }
    if (!is_regular()) {
      if (save_cmd_properties(thd)) goto err;
    }
    if (needs_explicit_preparation()) {
      lex->set_secondary_engine_execution_context(nullptr);
    }
    set_prepared();
  }
```

## 동작 흐름

```text
 L705  is_timer_applicable_to_statement 이면 L706 set_statement_timer   max_execution_time
 L708  is_data_change_stmt()
         IGNORE 면 Ignore_error_handler, strict 모드면 Strict_error_handler
 L727  !is_prepared()                       일반 문장 (prepared statement 가 아닐 때)
 L728    prepare(thd)
           L545  precheck                    문장별 대략적 권한 검사
           L556  open_tables_for_query       테이블을 열고 MDL 을 잡는다, 뷰를 펼친다
           L586  prepare_inner               문장별 준비 (가상 함수)
           L596  set_prepared
 L729  else (prepared statement 재실행)
         L736  open_tables_for_query, L758 check_privileges

 L770  lex->set_exec_started
 L781  데이터 변경 문장이면 run_before_dml_hook      복제 플러그인 훅
 L793  빈 질의가 아니면
 L794    [07] lock_tables(thd, query_tables, table_count, 0)
 L798  [09] execute_inner(thd)                         가상 함수. INSERT 는 Sql_cmd_insert_values 쪽

 L825  THD_STAGE_INFO end
 L828  lex->cleanup(false)                             계획은 EXPLAIN 용으로 남긴다
 L833  result->cleanup
 L841  타이머 해제
 L851  return false

 L853  err:  result->abort_result_set, 핸들러 해제, 타이머 해제
 L891  return thd->is_error()
```

세 개의 가상 함수가 문장 종류별로 무엇이 되는지가 이 틀의 쓰임새다. 이 흐름이 뒤에서 [행 쓰기]와 [일관 읽기(MVCC)]로 갈리는 것도 여기서다.

```text
 틀과 구현 (Sql_cmd_dml 의 가상 함수)

 virtual       line      SELECT (Sql_cmd_select)       INSERT VALUES (Sql_cmd_insert_values)
 ------------  --------  ----------------------------  ---------------------------------------
 precheck      L545      Sql_cmd_select::precheck      Sql_cmd_insert_base::precheck
                         (sql_select.cc L1239)         (sql_insert.cc L432)
 prepare_inner L586      Sql_cmd_select::prepare_inner Sql_cmd_insert_base::prepare_inner
                         (sql_select.cc L635)          (sql_insert.cc L1048)
 lock_tables   L794      TL_READ* -> F_RDLCK           TL_WRITE* -> F_WRLCK
 execute_inner L798      Sql_cmd_dml::execute_inner    Sql_cmd_insert_values::execute_inner
                         (sql_select.cc L1123, [09])   (sql_insert.cc L482) --> [행 쓰기]
```

```text
 한 문장 안에서 테이블이 지나는 상태

 어디서                          상태와 잡은 것
 L556 open_tables_for_query       열림   TABLE 객체, handler 인스턴스, MDL
 L794 lock_tables                 잠김   thr_lock, InnoDB 문장 시작과 2PC 등록
 L798 execute_inner               실행   행 단위 handler 호출
 [05] L5002 close_thread_tables   닫힘   external_lock(F_UNLCK), thr_lock 해제
 [05] L5040 / L5044               MDL 해제  autocommit 이면 여기서, 아니면 트랜잭션 끝에서
```

## 결과가 쓰이는 곳

```text
 열린 TABLE 들 (lex->query_tables 의 table)
      --> [07] lock_tables 가 잠그고, [09] 의 반복자가 table->file 로 handler 를 부른다

 is_prepared / set_prepared
      --> prepared statement 는 두 번째 실행부터 prepare 를 건너뛰고 L729 갈래로 간다
```

## 다루지 않는 것

prepared statement 재실행 갈래(재준비 판정 `ask_to_reprepare`, `restore_cmd_properties`), 보조 엔진 판정(`validate_use_secondary_engine`), `open_tables_for_query` 의 내부(테이블 캐시, MDL 획득, 뷰 병합), 문장별 `prepare_inner` 의 이름 해석, 비용 계산(`save_current_query_costs`)은 이 흐름의 곁가지라 줄만 적었다.
