# dispatch_sql_command

상위: [명령 디스패치](../README.md)

**SQL 문장 하나의 수명을 책임진다.** 문장별 THD 상태를 초기화하고, [04] 로 파싱하고, 로그에 남길 문장을 정하고(비밀번호 가리기), [05] `mysql_execute_command` 로 실행한 뒤 LEX 를 부순다. 파싱이 실패하면 실행 단계를 통째로 건너뛰고 정리만 한다. 볼거리는 파싱이 끝나야 비로소 문장 종류(`lex->sql_command`)를 알게 되고, 그 뒤에야 계측, 로그, 실행이 문장 종류별로 갈린다는 점이다.

## 위치

`sql` / `sql_parse.cc` L5307-L5494 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_parse.cc#L5307-L5494))

## 실제 코드

문장 상태를 초기화하고 파싱한다. 다중 문장이면 이번 문장의 길이만큼만 `thd->query()` 를 줄인다.

`sql` / `sql_parse.cc` L5307-L5350 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_parse.cc#L5307-L5350))

```cpp
// sql_parse.cc L5307-L5350
void dispatch_sql_command(THD *thd, Parser_state *parser_state, bool is_retry) {
  DBUG_TRACE;
  DBUG_PRINT("dispatch_sql_command", ("query: '%s'", thd->query().str));
  statement_id_to_session(thd);
  DBUG_EXECUTE_IF("parser_debug", turn_parser_debug_on(););

  mysql_reset_thd_for_next_command(thd);
  // It is possible that rewritten query may not be empty (in case of
  // multiqueries). So reset it.
  thd->reset_rewritten_query();
  lex_start(thd);

  thd->m_parser_state = parser_state;
  invoke_pre_parse_rewrite_plugins(thd);
  thd->m_parser_state = nullptr;

  // we produce digest if it's not explicitly turned off
  // by setting maximum digest length to zero
  if (get_max_digest_length() != 0)
    parser_state->m_input.m_compute_digest = true;

  LEX *lex = thd->lex;
  const char *found_semicolon = nullptr;

  bool err = thd->get_stmt_da()->is_error();
  size_t qlen = 0;

  if (!err) {
    err = parse_sql(thd, parser_state, nullptr);
    if (!err) err = invoke_post_parse_rewrite_plugins(thd, false);

    found_semicolon = parser_state->m_lip.found_semicolon;
    qlen = found_semicolon ? (found_semicolon - thd->query().str)
                           : thd->query().length;
    /*
      We set thd->query_length correctly to not log several queries, when we
      execute only first. We set it to not see the ';' otherwise it would get
      into binlog and Query_log_event::print() would give ';;' output.
    */

    if (!thd->is_error() && found_semicolon && (ulong)(qlen)) {
      thd->set_query(thd->query().str, qlen - 1);
    }
  }
```

파싱이 성공했으면 실행한다. 사용자별 시간당 질의 한도(`check_mqh`)와 비밀번호 만료를 먼저 본다.

`sql` / `sql_parse.cc` L5401-L5453 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_parse.cc#L5401-L5453))

```cpp
// sql_parse.cc L5401-L5453
  if (!err) {
    if (!is_retry) {
      thd->m_statement_psi = MYSQL_REFINE_STATEMENT(
          thd->m_statement_psi,
          sql_statement_info[thd->lex->sql_command].m_key);
    }

    if (mqh_used && thd->get_user_connect() &&
        check_mqh(thd, lex->sql_command)) {
      if (thd->is_classic_protocol())
        thd->get_protocol_classic()->get_net()->error = NET_ERROR_UNSET;
    } else {
      if (!thd->is_error()) {
        /* Actually execute the query */
        if (found_semicolon) {
          lex->safe_to_cache_query = false;
          thd->server_status |= SERVER_MORE_RESULTS_EXISTS;
        }
        lex->set_trg_event_type_for_tables();

        int error [[maybe_unused]];
        if (unlikely(
                (thd->security_context()->password_expired() ||
                 thd->security_context()->is_in_registration_sandbox_mode()) &&
                lex->sql_command != SQLCOM_SET_PASSWORD &&
                lex->sql_command != SQLCOM_ALTER_USER)) {
          if (thd->security_context()->is_in_registration_sandbox_mode())
            my_error(ER_PLUGIN_REQUIRES_REGISTRATION, MYF(0));
          else
            my_error(ER_MUST_CHANGE_PASSWORD, MYF(0));
          error = 1;
        } else {
          resourcegroups::Resource_group *src_res_grp = nullptr;
          resourcegroups::Resource_group *dest_res_grp = nullptr;
          MDL_ticket *ticket = nullptr;
          MDL_ticket *cur_ticket = nullptr;
          auto mgr_ptr = resourcegroups::Resource_group_mgr::instance();
          const bool switched = mgr_ptr->switch_resource_group_if_needed(
              thd, &src_res_grp, &dest_res_grp, &ticket, &cur_ticket);

          error = mysql_execute_command(thd, true);

          if (switched)
            mgr_ptr->restore_original_resource_group(thd, src_res_grp,
                                                     dest_res_grp);
          thd->resource_group_ctx()->m_switch_resource_group_str[0] = '\0';
          if (ticket != nullptr)
            mgr_ptr->release_shared_mdl_for_resource_group(thd, ticket);
          if (cur_ticket != nullptr)
            mgr_ptr->release_shared_mdl_for_resource_group(thd, cur_ticket);
        }
      }
    }
```

성공이든 실패든 문장이 쓴 것을 치운다.

`sql` / `sql_parse.cc` L5485-L5494 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_parse.cc#L5485-L5494))

```cpp
// sql_parse.cc L5485-L5494
  THD_STAGE_INFO(thd, stage_freeing_items);
  sp_cache_enforce_limit(thd->sp_proc_cache, stored_program_cache_size);
  sp_cache_enforce_limit(thd->sp_func_cache, stored_program_cache_size);
  thd->lex->destroy();
  thd->end_statement();
  thd->cleanup_after_query();
  assert(thd->change_list.is_empty());

  DEBUG_SYNC(thd, "query_rewritten");
}
```

L5313 의 문장별 초기화가 무엇을 지우는지가 뒤 흐름과 이어진다. 특히 `durability_property` 가 여기서 `HA_REGULAR_DURABILITY` 로 돌아온다.

`sql` / `sql_parse.cc` L5241-L5263 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_parse.cc#L5241-L5263))

```cpp
// sql_parse.cc L5241-L5263
  thd->clear_error();
  thd->get_stmt_da()->reset_diagnostics_area();
  thd->get_stmt_da()->reset_statement_cond_count();

  thd->rand_used = false;
  thd->m_sent_row_count = thd->m_examined_row_count = 0;

  thd->reset_current_stmt_binlog_format_row();
  thd->binlog_unsafe_warning_flags = 0;
  thd->binlog_need_explicit_defaults_ts = false;

  thd->commit_error = THD::CE_NONE;
  thd->durability_property = HA_REGULAR_DURABILITY;
  thd->set_trans_pos(nullptr, 0);
  thd->derived_tables_processing = false;
  thd->parsing_system_view = false;
  thd->parsing_json_duality_view = false;

  // Need explicit setting, else demand all privileges to a table.
  thd->want_privilege = ALL_ACCESS;

  thd->reset_skip_readonly_check();
  thd->tx_commit_pending = false;
```

## 동작 흐름

```text
 L5310  statement_id_to_session
 L5313  mysql_reset_thd_for_next_command -> THD::reset_for_next_command (L5198)
          clear_error, 진단 영역 초기화, 보낸 행 수와 검사한 행 수 0
          commit_error = CE_NONE (L5252), durability_property = HA_REGULAR_DURABILITY (L5253)
 L5316  reset_rewritten_query
 L5317  lex_start                                 LEX 를 새 문장용으로
 L5320  invoke_pre_parse_rewrite_plugins          문자열 단계의 rewrite 플러그인

 L5334  진단 영역에 이미 오류가 없으면
 L5335    [04] parse_sql(thd, parser_state, nullptr)
 L5336    invoke_post_parse_rewrite_plugins
 L5338    found_semicolon = 다음 문장의 시작 (없으면 nullptr)
 L5347    다중 문장이면 set_query(앞 문장만)      binlog 에 ;; 가 들어가지 않게 (주석 L5341-L5345)

 L5354  err == false 이면
 L5366    mysql_rewrite_query                     비밀번호 같은 것을 가린 문장
 L5384    general_log_write (rewrite 본이 있으면 그것)
 L5396  MYSQL_NOTIFY_STATEMENT_QUERY_ATTRIBUTES

 L5401  err == false 이면
 L5403    PSI 를 문장 종류로 세분 (statement/sql/insert 등)
 L5408    check_mqh 초과                          -> 실행하지 않는다
 L5415    found_semicolon 이면 SERVER_MORE_RESULTS_EXISTS
 L5422    비밀번호 만료 또는 등록 샌드박스이고 SET PASSWORD / ALTER USER 가 아니면 오류
 L5438    switch_resource_group_if_needed
 L5441    [05] mysql_execute_command(thd, true)
 L5443    리소스 그룹 복원, 리소스 그룹용 공유 MDL 해제
 L5454  err == true 이면  깨진 문장 그대로 PSI 에 남기고 statement/sql/error 로 계측

 L5485  THD_STAGE_INFO freeing_items
 L5488  lex->destroy()
 L5489  end_statement
 L5490  cleanup_after_query
```

문장 종류를 언제 알게 되는지를 기준으로 보면 이 함수는 두 반쪽이다.

```text
 문장 종류를 알기 전과 후

 대상            파싱 전 (L5307-L5334) -> 파싱 후 (L5354-L5453)
 thd->query()    패킷의 전체 문자열 -> 이번 문장만 (L5348)
 lex             빈 상태 -> sql_command, m_sql_cmd 가 채워짐
 PSI             statement/com/Query -> statement/sql/<종류> (L5403)
 general log     아직 안 씀 -> rewrite 본으로 기록 (L5384-L5391)
 check_mqh       없음 -> sql_command 로 갱신 여부를 가른다

 파싱이 실패하면 오른쪽 전체를 건너뛰고 L5485 의 정리로 간다
```

## 결과가 쓰이는 곳

```text
 lex (sql_command, m_sql_cmd, query_tables)
      --> [05] mysql_execute_command 의 switch 와 모든 하위 단계

 found_semicolon
      --> [02] dispatch_command 의 while 이 다음 문장의 위치로 쓴다

 durability_property = HA_REGULAR_DURABILITY
      --> [커밋과 binlog 2PC] 의 MYSQL_BIN_LOG::prepare 가 HA_IGNORE_DURABILITY 로 바꾸고
          다음 문장의 이 자리에서 다시 되돌아온다 (binlog.cc L7059-L7067 주석)
```

## 다루지 않는 것

query rewrite 플러그인(`invoke_pre_parse_rewrite_plugins`, `invoke_post_parse_rewrite_plugins`), `mysql_rewrite_query` 의 문장별 가리기 규칙, 리소스 그룹, `check_mqh` 의 사용자 자원 한도, 보조 엔진 재시도 인자(`is_retry`), 복제 스레드의 계측 차이, 저장 프로그램 캐시 크기 제한은 이 흐름의 곁가지라 줄만 적었다.
