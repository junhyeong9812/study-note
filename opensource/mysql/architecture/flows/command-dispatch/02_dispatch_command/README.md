# dispatch_command

상위: [명령 디스패치](../README.md)

**명령 하나의 앞뒤를 감싸는 틀이다.** 앞에서 query_id 와 시각을 새로 받고 실행 중 스레드 수를 올리고, 가운데 `switch (command)` 에서 명령 종류별로 가르고, 뒤의 `done:` 에서 결과 패킷을 보내고 상태를 `COM_SLEEP` 으로 되돌린다. SQL 문장은 `COM_QUERY` 한 갈래로만 들어가며, 한 패킷에 세미콜론으로 이은 문장이 여럿이면 여기서 한 문장씩 잘라 [03] 을 거듭 부른다.

## 위치

`sql` / `sql_parse.cc` L1752-L2539 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_parse.cc#L1752-L2539))

## 실제 코드

명령 시작이다. PROCESSLIST 의 Command 값을 바꾸고, 지난 문장의 `KILL QUERY` 를 지운다.

`sql` / `sql_parse.cc` L1778-L1795 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_parse.cc#L1778-L1795))

```cpp
// sql_parse.cc L1778-L1795
  thd->set_command(command);
  /*
    Commands which always take a long time are logged into
    the slow log only if opt_log_slow_admin_statements is set.
  */
  thd->enable_slow_log = true;
  thd->lex->sql_command = SQLCOM_END; /* to avoid confusing VIEW detectors */
  /*
    KILL QUERY may come after cleanup in mysql_execute_command(). Next query
    execution is interrupted due to this. So resetting THD::killed here.

    THD::killed value can not be KILL_TIMEOUT here as timer used for statement
    max execution time is disarmed in the cleanup stage of
    mysql_execute_command. KILL CONNECTION should terminate the connection.
    Hence resetting THD::killed only for KILL QUERY case here.
  */
  if (thd->killed == THD::KILL_QUERY) thd->killed = THD::NOT_KILLED;
  thd->set_time();
```

query_id 를 받고 실행 중 스레드 수와 Questions 를 올린다. 시각 검사(L1796-L1832)는 2038년 이후 시각에 대한 방어라 생략했다.

`sql` / `sql_parse.cc` L1833-L1846 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_parse.cc#L1833-L1846))

```cpp
// sql_parse.cc L1833-L1846
  thd->set_query_id(next_query_id());
  thd->reset_rewritten_query();
  thd_manager->inc_thread_running();

  if (!(server_command_flags[command] & CF_SKIP_QUESTIONS)) {
    thd->status_var.questions++;
    global_aggregated_stats.get_shard(thd->thread_id()).questions++;
  }

  /**
    Clear the set of flags that are expected to be cleared at the
    beginning of each command.
  */
  thd->server_status &= ~SERVER_STATUS_CLEAR_SET;
```

`COM_QUERY` 갈래다. 질의 문자열을 THD 메모리로 복사하고 파서 상태를 만든 뒤 첫 문장을 보낸다.

`sql` / `sql_parse.cc` L2095-L2158 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_parse.cc#L2095-L2158))

```cpp
// sql_parse.cc L2095-L2158
    case COM_QUERY: {
      /*
        IMPORTANT NOTE:

        Every execution path for COM_QUERY should call once
          MYSQL_NOTIFY_STATEMENT_QUERY_ATTRIBUTES()
      */
      assert(thd->m_digest == nullptr);
      thd->m_digest = &thd->m_digest_state;
      thd->m_digest->reset(thd->m_token_array, max_digest_length);

      if (alloc_query(thd, com_data->com_query.query,
                      com_data->com_query.length)) {
        MYSQL_NOTIFY_STATEMENT_QUERY_ATTRIBUTES(thd->m_statement_psi, false);
        break;  // fatal error is set
      }

      const char *packet_end = thd->query().str + thd->query().length;

      if (opt_general_log_raw)
        query_logger.general_log_write(thd, command, thd->query().str,
                                       thd->query().length);

      DBUG_PRINT("query", ("%-.4096s", thd->query().str));

#if defined(ENABLED_PROFILING)
      thd->profiling->set_query_source(thd->query().str, thd->query().length);
#endif

      const LEX_CSTRING orig_query = thd->query();

      Parser_state parser_state;
      if (parser_state.init(thd, thd->query().str, thd->query().length)) {
        MYSQL_NOTIFY_STATEMENT_QUERY_ATTRIBUTES(thd->m_statement_psi, false);
        break;
      }

      parser_state.m_input.m_has_digest = true;

      // we produce digest if it's not explicitly turned off
      // by setting maximum digest length to zero
      if (get_max_digest_length() != 0)
        parser_state.m_input.m_compute_digest = true;
      /*
        Initially, set up the statement for preparation and optimization
        in the primary storage engine. If an eligible secondary storage engine
        is found, the statement may be reprepared for the secondary storage
        engine later. In addition, open_secondary_engine_tables() will directly
        set up for the secondary storage engine if secondary engine is forced.
      */
      thd->set_secondary_engine_optimization(
          Secondary_engine_optimization::PRIMARY_TENTATIVELY);

      copy_bind_parameter_values(thd, com_data->com_query.parameters,
                                 com_data->com_query.parameter_count);

      /* This will call MYSQL_NOTIFY_STATEMENT_QUERY_ATTRIBUTES() */
      dispatch_sql_command(thd, &parser_state);

      // If statement failed, possibly restart it in another storage engine.
      if (thd->is_error()) {
        check_secondary_engine_statement(thd, &parser_state, orig_query.str,
                                         orig_query.length);
      }
```

같은 패킷에 다음 문장이 남아 있으면(`found_semicolon`) 앞 문장의 결과를 먼저 보내고 다음 문장을 같은 방식으로 실행한다.

`sql` / `sql_parse.cc` L2167-L2174 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_parse.cc#L2167-L2174))

```cpp
// sql_parse.cc L2167-L2174
      while (!thd->killed && (parser_state.m_lip.found_semicolon != nullptr) &&
             !thd->is_error()) {
        // Multiple queries exist, execute them individually
        const char *beginning_of_next_stmt = parser_state.m_lip.found_semicolon;

        /* Finalize server status flags after executing a statement. */
        thd->update_slow_query_status();
        thd->send_statement_status();
```

`sql` / `sql_parse.cc` L2222-L2255 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_parse.cc#L2222-L2255))

```cpp
// sql_parse.cc L2222-L2255
        THD_STAGE_INFO(thd, stage_starting);

        thd->set_query(beginning_of_next_stmt, length);
        thd->set_query_id(next_query_id());

        /*
          Count each statement from the client.
        */
        thd->status_var.questions++;
        global_aggregated_stats.get_shard(thd->thread_id()).questions++;
        thd->set_time(); /* Reset the query start time. */
        parser_state.reset(beginning_of_next_stmt, length);
        thd->set_secondary_engine_optimization(
            Secondary_engine_optimization::PRIMARY_TENTATIVELY);
        /* TODO: set thd->lex->sql_command to SQLCOM_END here */
        dispatch_sql_command(thd, &parser_state);

        if (thd->is_error()) {
          check_secondary_engine_statement(thd, &parser_state,
                                           beginning_of_next_stmt, length);
        }
      }

      thd->bind_parameter_values = nullptr;
      thd->bind_parameter_values_count = 0;
      thd->cleanup_after_statement_execution();

      /* Need to set error to true for graceful shutdown */
      if ((thd->lex->sql_command == SQLCOM_SHUTDOWN) &&
          (thd->get_stmt_da()->is_ok()))
        error = true;

      DBUG_PRINT("info", ("query ready"));
      break;
```

`COM_QUIT` 는 응답을 보내지 않고 `error = true` 로 끝난다. 이 값이 [01] 을 거쳐 연결 루프를 끝낸다.

`sql` / `sql_parse.cc` L2344-L2355 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_parse.cc#L2344-L2355))

```cpp
// sql_parse.cc L2344-L2355
    case COM_QUIT:
      /* Prevent results of the form, "n>0 rows sent, 0 bytes sent" */
      thd->set_sent_row_count(0);
      /* We don't calculate statistics for this command */
      query_logger.general_log_print(thd, command, NullS);
      // Don't give 'abort' message
      // TODO: access of protocol_classic should be removed
      if (thd->is_classic_protocol())
        thd->get_protocol_classic()->get_net()->error = NET_ERROR_UNSET;
      thd->get_stmt_da()->disable_status();  // Don't send anything back
      error = true;                          // End server
      break;
```

모든 명령이 지나는 뒷정리다. 응답 패킷이 여기서 나간다.

`sql` / `sql_parse.cc` L2456-L2464 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_parse.cc#L2456-L2464))

```cpp
// sql_parse.cc L2456-L2464
done:
  assert(thd->open_tables == nullptr ||
         (thd->locked_tables_mode == LTM_LOCK_TABLES));

  /* Finalize server status flags after executing a command. */
  thd->update_slow_query_status();
  if (thd->killed) thd->send_kill_message();
  thd->send_statement_status();

```

`sql` / `sql_parse.cc` L2494-L2512 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_parse.cc#L2494-L2512))

```cpp
// sql_parse.cc L2494-L2512
  log_slow_statement(thd);

  THD_STAGE_INFO(thd, stage_cleaning_up);

  thd->reset_query();
  thd->set_command(COM_SLEEP);
  thd->set_proc_info(nullptr);
  thd->lex->sql_command = SQLCOM_END;

  /* Performance Schema Interface instrumentation, end */
  MYSQL_END_STATEMENT(thd->m_statement_psi, thd->get_stmt_da());
  thd->m_statement_psi = nullptr;
  thd->m_digest = nullptr;
  thd->reset_query_for_display();

  /* Prevent rewritten query from getting "stuck" in SHOW PROCESSLIST. */
  thd->reset_rewritten_query();

  thd_manager->dec_thread_running();
```

## 동작 흐름

```text
 L1775  m_statement_psi 를 명령 종류로 세분 (statement/com/Query 등)
 L1778  thd->set_command(command)                PROCESSLIST 의 Command
 L1784  lex->sql_command = SQLCOM_END
 L1794  killed == KILL_QUERY 면 지운다           KILL CONNECTION 은 그대로 둔다 (주석 L1786-L1792)
 L1795  set_time                                 NOW() 의 기준 시각
 L1833  set_query_id(next_query_id())
 L1835  inc_thread_running                       Threads_running +1
 L1837  CF_SKIP_QUESTIONS 가 아니면 Questions +1
 L1846  server_status 의 명령별 플래그를 지운다

 L1848  플러그인 프로토콜이 허용하지 않는 명령     -> KILL_CONNECTION, done
 L1868  비밀번호 만료인데 허용 목록 밖의 명령      -> ER_MUST_CHANGE_PASSWORD, done
 L1878  감사 플러그인 COMMAND_START 가 거부         -> done

 L1893  switch (command)
          COM_QUERY          L2095  아래 그림
          COM_STMT_PREPARE   L2060  mysqld_stmt_prepare
          COM_STMT_EXECUTE   L2017  mysqld_stmt_execute
          COM_INIT_DB        L1894  mysql_change_db (USE db)
          COM_CHANGE_USER    L1964  cleanup_connection 후 acl_authenticate 다시
          COM_RESET_CONNECTION L1918  cleanup_connection
          COM_PING           L2408  my_ok
          COM_QUIT           L2344  error = true, 응답 없음
          COM_BINLOG_DUMP*   L2356  복제 덤프 스레드로 이 연결이 바뀐다
          나머지             L2446  ER_UNKNOWN_COM_ERROR

 L2456  done:
 L2462  killed 면 kill 메시지
 L2463  send_statement_status                    OK / ERR / EOF 패킷
 L2466  COM_CLONE 이면 응답 뒤 clone 프로토콜로 전환
 L2491  감사 COMMAND_END, L2494 log_slow_statement
 L2499  set_command(COM_SLEEP)
 L2512  dec_thread_running
 L2528  mem_root 가 40960 바이트 미만이면 ClearForReuse, 넘으면 Clear
 L2538  return error                              true 면 [01] 이 연결을 닫게 한다
```

`COM_QUERY` 한 패킷 안의 다중 문장은 이렇게 돈다. 문장마다 query_id, Questions, 시각을 새로 받는다는 점에서 패킷 여러 개와 같다.

```text
 COM_QUERY "INSERT ...; SELECT ...; COMMIT" (CLIENT_MULTI_STATEMENTS)

 L2106  alloc_query                     패킷의 질의를 thd->query() 로 복사
 L2127  parser_state.init(query 전체)
 L2152  [03] dispatch_sql_command        첫 문장. 파서가 ; 에서 멈추고 found_semicolon 에 위치를 남긴다
 L2155  오류면 보조 엔진으로 재시도 검토
 L2167  while (!killed && found_semicolon && !is_error())
          L2174  send_statement_status   앞 문장의 결과를 보낸다 (SERVER_MORE_RESULTS_EXISTS 와 함께)
          L2186  log_slow_statement
          L2224  set_query(다음 문장), L2225 set_query_id, L2230 Questions +1, L2232 set_time
          L2233  parser_state.reset(다음 문장)
          L2237  [03] dispatch_sql_command
 L2247  cleanup_after_statement_execution
 L2250  SHUTDOWN 문이 성공했으면 error = true

 한 문장이 실패하면 L2167 조건이 거짓이 되어 나머지 문장은 실행되지 않는다
 마지막 문장의 결과는 L2463 done: 에서 보낸다
```

## 결과가 쓰이는 곳

```text
 반환값 error
      --> [01] do_command 가 그대로 돌려주고 handle_connection 이 루프를 끝낼지 정한다

 send_statement_status 로 나간 패킷
      --> 클라이언트 라이브러리가 문장의 성공, 영향받은 행 수, 경고 수를 읽는다

 Threads_running (inc L1835 / dec L2512)
      --> 명령이 실행 중인 연결 수. 명령을 기다리는 연결은 세지 않는다
```

## 다루지 않는 것

prepared statement 명령들(`COM_STMT_*`)의 내부, `COM_CHANGE_USER` 의 재인증 절차, `COM_FIELD_LIST`, `COM_STATISTICS`, 복제용 `COM_BINLOG_DUMP` 와 `COM_REGISTER_SLAVE`, `COM_CLONE` 과 그룹 복제 스트림, 보조 엔진 재시도(`check_secondary_engine_statement`), 2038년 시각 검사, SHOW PROFILE 과 Performance Schema 계측은 이 흐름의 곁가지라 줄만 적었다.
