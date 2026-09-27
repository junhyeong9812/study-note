# 명령 디스패치

상위: [MySQL 아키텍처 지도](../../README.md)

연결 스레드가 **클라이언트 패킷 하나를 읽어서, SQL 이면 파싱하고, 테이블을 열고 잠그고, 실행한 뒤, 문장 트랜잭션을 끝내고 결과 상태를 보낼 때까지**의 흐름이다. 전부 [연결과 스레드](../connection-thread/README.md)가 만든 연결 스레드 하나 안에서 일어나고 스레드 경계는 없다. 대신 **서버 계층과 InnoDB 사이의 경계가 두 번** 나온다. 한 번은 [07] `lock_tables` 가 테이블마다 `handler::ha_external_lock` 을 부르는 자리로, 여기서 InnoDB 트랜잭션이 서버의 2PC 코디네이터에 등록된다([08]). 다른 한 번은 [09] `execute_inner` 가 실행기를 돌려 행 단위 handler 호출(`ha_write_row`, `ha_index_read_map` 등)을 내보내는 자리로, 여기서 흐름이 [행 쓰기](../row-insert/README.md)와 [일관 읽기(MVCC)](../mvcc-read/README.md)로 갈린다. 흐름은 [05] `mysql_execute_command` 의 `finish:` 에서 `trans_commit_stmt` 로 [커밋과 binlog 2PC](../commit-2pc/README.md)에 들어갔다가 돌아와 끝난다.

기준 태그: mysql-9.7.2 [`008e09c283`](https://github.com/mysql/mysql-server/tree/008e09c2834b98143a8c067d4d225c90953050cf). 모든 줄 번호는 이 태그 기준이다.

## 전체 그림

```text
 연결 스레드 (handle_connection 의 while ... do_command 루프, connection_handler_per_thread.cc L304)

 [01] do_command                                              L1347
      +-- my_net_set_read_timeout(net_wait_timeout)           L1378  명령을 기다리는 동안의 타임아웃
      +-- get_protocol()->get_command                         L1429  여기서 블록된다. 패킷 1개 = 명령 1개
      +-- my_net_set_read_timeout(net_read_timeout)           L1487
      +-- [02] dispatch_command                               L1491
            +-- set_query_id, inc_thread_running              L1833, L1835
            +-- switch (command)                              L1893
            |     COM_QUERY        -> [03] dispatch_sql_command     L2152
            |     COM_STMT_EXECUTE -> mysqld_stmt_execute           L2017
            |     COM_QUIT         -> error = true                  L2354
            |     COM_PING ...     -> my_ok
            +-- done: send_statement_status                   L2463  OK / ERR 패킷이 여기서 나간다
            +-- set_command(COM_SLEEP), dec_thread_running    L2499, L2512

 [03] dispatch_sql_command                                    L5307
      +-- lex_start                                           L5317
      +-- [04] parse_sql                                      L5335
      |     +-- THD::sql_parser -> my_sql_parser_parse        sql_class.cc L3194  (bison 문법)
      |     +-- lex->make_sql_cmd(root)                       sql_class.cc L3203  Sql_cmd 객체가 생긴다
      +-- mysql_rewrite_query, general_log_write              L5366, L5390
      +-- [05] mysql_execute_command(thd, true)               L5441
            +-- CF_IMPLICIT_COMMIT_BEGIN 이면 trans_commit_implicit  L3352-L3369
            +-- switch (lex->sql_command)                     L3486
            |     SQLCOM_INSERT / UPDATE / DELETE ...  -> m_sql_cmd->execute   L3803
            |     SQLCOM_SELECT ...                    -> m_sql_cmd->execute   L4766
            |     SQLCOM_COMMIT                        -> trans_commit         L4350
            |
            |     [06] Sql_cmd_dml::execute                   sql_select.cc L685
            |          +-- prepare -> open_tables_for_query   sql_select.cc L728 -> L556
            |          +-- [07] lock_tables                   sql_select.cc L794
            |          |     +-- mysql_lock_tables -> lock_external     lock.cc L339
            |          |           +-- ha_external_lock(F_RDLCK / F_WRLCK)  lock.cc L395
            |          |                 +-- [08] ha_innobase::external_lock
            |          |                       +-- innobase_register_trx     ha_innodb.cc L19027
            |          +-- [09] execute_inner                 sql_select.cc L798
            |                +-- optimize -> create_iterators -> unit->execute
            |                      --> [행 쓰기] / [일관 읽기(MVCC)] / [레코드 잠금]
            |
            +-- finish:
                  +-- trans_commit_stmt 또는 trans_rollback_stmt   L4973 / L4969  --> [커밋과 binlog 2PC]
                  +-- close_thread_tables                          L5002  (external_lock(F_UNLCK))
                  +-- MDL 해제 (autocommit 이면 트랜잭션 락까지)    L5029-L5044

 [01] [02] [03] [04] [05] 의 줄은 sql_parse.cc, [06] [09] 는 sql_select.cc,
 [07] 은 sql_base.cc, [08] 은 storage/innobase/handler/ha_innodb.cc 의 줄이다
```

명령 하나가 지나는 구간마다 THD 의 무엇이 바뀌는지를 세우면 아래와 같다. 이 흐름의 대부분은 "문장 하나"의 상태를 만들고 치우는 일이다.

```text
 명령 하나가 지나는 상태 (위에서 아래로 시간)

 줄            구간과 바뀌는 것
 ------------  ---------------------------------------------------------------
 [01] L1429    대기       thd->m_server_idle = true, 소켓 read 에서 잠든다
 [02] L1778    명령 시작  thd->command = COM_QUERY (PROCESSLIST 의 Command)
 [02] L1833               query_id 새로 받음. Threads_running +1 (L1835)
 [03] L5317    파싱       lex_start: LEX 를 새 문장용으로 초기화
 [04] L7282               LEX 가 채워지고 lex->m_sql_cmd 가 생긴다
 [05] L3314    실행       Com_xxx 상태 변수 +1
 [06] L556                테이블 열기, MDL 획득
 [07] L7382               thr_lock + InnoDB external_lock, 2PC 참여 등록
 [09]                     실행기가 행을 읽고 쓴다
 [05] L4973    문장 종료  trans_commit_stmt (autocommit=1 이면 여기서 진짜 커밋)
 [05] L5002               테이블 닫기, external_lock(F_UNLCK)
 [02] L2463    응답       OK 또는 ERR 패킷 전송
 [02] L2499    정리       thd->command = COM_SLEEP, Threads_running -1 (L2512)
```

## 어디에서 쓰이는가

```text
 [연결과 스레드]      handle_connection 이 루프에서 do_command 를 부른다 (connection_handler_per_thread.cc L304)
                      do_command 가 true 를 돌려주면 루프가 끝나고 연결이 닫힌다
 [행 쓰기]            SQLCOM_INSERT 의 m_sql_cmd 는 Sql_cmd_insert_values 이고
                      [09] execute_inner 가 가상 호출로 그쪽 execute_inner (sql_insert.cc L482) 로 간다
 [일관 읽기(MVCC)]    SELECT 의 unit->execute 가 반복자를 돌려 ha_index_read_map / ha_rnd_next 를 부른다
                      [08] 이 정한 m_prebuilt->select_lock_type (LOCK_NONE 이면 일관 읽기) 를 이어받는다
 [레코드 잠금]        select_lock_type 이 LOCK_S / LOCK_X 이면 읽기가 잠금 읽기가 된다
 [커밋과 binlog 2PC]  [05] finish: 의 trans_commit_stmt, SQLCOM_COMMIT 의 trans_commit
```

앞 흐름은 [연결과 스레드](../connection-thread/README.md), 뒤로는 [행 쓰기](../row-insert/README.md), [일관 읽기(MVCC)](../mvcc-read/README.md), [레코드 잠금](../record-lock/README.md), [커밋과 binlog 2PC](../commit-2pc/README.md)로 갈린다.

## db-engine 에서는

같은 일(문자열 -> AST -> 실행 계획 -> 실행)을 db-engine 은 `DbEngine.execute` 한 함수에 순서대로 적었다. MySQL 은 그 사이에 "테이블을 열고 잠근다"와 "문장 트랜잭션을 끝낸다"라는 두 단계를 더 끼운다.

```text
 같은 문제, 두 구현 (위 MySQL / 아래 db-engine)

 입구
   MySQL      do_command -> dispatch_command 가 COM_* 로 먼저 가르고 COM_QUERY 만 SQL 로 간다
   db-engine  DbEngine.execute(sql) 이 곧 입구. 명령 종류라는 층이 없다

 파싱
   MySQL      parse_sql -> THD::sql_parser -> my_sql_parser_parse (bison 생성 파서)
              결과는 LEX 와 Sql_cmd 객체 (make_sql_cmd)
   db-engine  Parser(Lexer(sql).tokenize()).parseStatement()  손으로 쓴 재귀 하강
              결과는 sealed class Statement (Select / Insert / CreateTable / DropTable)

 분기
   MySQL      switch (lex->sql_command) 에서 대부분 m_sql_cmd->execute(thd) 로 위임
   db-engine  when (stmt) { is Statement.Select -> executeSelect ... }

 계획
   MySQL      Sql_cmd_dml::prepare (이름 해석) -> execute_inner 의 optimize, create_iterators
   db-engine  Translator.toLogicalPlan -> SimpleOptimizer.optimize -> physical.root.iterator()

 테이블 열기와 잠금
   MySQL      open_tables_for_query (MDL) -> lock_tables -> ha_external_lock
              InnoDB 트랜잭션이 여기서 서버에 등록된다
   db-engine  heaps[name] 맵 조회. 잠금과 트랜잭션은 SQL 경로에 없다 (주석: programmatic)

 문장 끝
   MySQL      trans_commit_stmt / trans_rollback_stmt, close_thread_tables, MDL 해제
   db-engine  QueryResult 를 돌려주면 끝
```

db-engine 의 impl 문서는 존재하지 않는 컬럼이 실행 시점(`Project` 생성)에야 걸린다는 점을 짚고, 파서와 옵티마이저 사이의 의미 분석(binding) 층이 없어서라고 적었다. MySQL 은 [06] 의 `prepare` 가 테이블을 열고(sql_select.cc L556) 문장별 `prepare_inner`(L586)를 돌린 뒤에야 잠금과 최적화로 넘어간다. 챕터: [12-01-sql-parser](../../../../../project/db-engine/12-01-sql-parser/), [13-02-sql-translator](../../../../../project/db-engine/13-02-sql-translator/), [14-00-db-engine](../../../../../project/db-engine/14-00-db-engine/).

## 단계

1. [do_command](01_do_command/README.md)이 패킷 하나를 읽어 명령 번호와 인자를 꺼낸다.
2. [dispatch_command](02_dispatch_command/README.md)가 명령 번호로 가르고, 끝에서 응답을 보낸다.
3. [dispatch_sql_command](03_dispatch_sql_command/README.md)가 SQL 한 문장을 파싱하고 로그에 적고 실행기에 넘긴다.
4. [parse_sql](04_parse_sql/README.md)이 파서를 돌려 LEX 와 `Sql_cmd` 를 만든다.
5. [mysql_execute_command](05_mysql_execute_command/README.md)가 `sql_command` 로 가르고, 문장 트랜잭션을 끝낸다.
6. [Sql_cmd_dml.execute](06_Sql_cmd_dml.execute/README.md)가 DML 의 준비, 잠금, 실행 순서를 고정한다.
7. [lock_tables](07_lock_tables/README.md)이 열린 테이블 전부를 한 번에 잠근다.
8. [ha_innobase.external_lock](08_ha_innobase.external_lock/README.md)이 InnoDB 쪽 문장 시작과 2PC 등록을 한다.
9. [Sql_cmd_dml.execute_inner](09_Sql_cmd_dml.execute_inner/README.md)가 최적화하고 반복자를 만들어 실행한다.

## 결과가 쓰이는 곳

```text
 OK / ERR 패킷 (send_statement_status, [02] L2463)
      --> 클라이언트가 문장 하나의 결과로 받는다
      --> 다중 문장이면 문장마다 한 번씩 보낸다 ([02] L2174)

 Ha_trx_info 목록 (trans_register_ha 가 채움)
      --> [커밋과 binlog 2PC] 의 ha_commit_trans 가 이 목록의 엔진들을 prepare / commit 한다

 m_prebuilt->select_lock_type ([08])
      --> [일관 읽기(MVCC)] 와 [레코드 잠금] 이 읽기를 잠금 없이 할지 S / X 로 할지 이것으로 가른다

 query_id, Com_xxx, Questions, Threads_running
      --> SHOW STATUS 와 PROCESSLIST
```

## 다루지 않는 것

prepared statement 경로(`COM_STMT_PREPARE`, `COM_STMT_EXECUTE`, `Prepared_statement::execute`), 저장 프로시저와 트리거의 재귀 `mysql_execute_command(thd, false)`, 보조 엔진(secondary engine) 재시도(`check_secondary_engine_statement`), 복제 적용 스레드 전용 분기(`slave_thread` 필터, `launch_hook_trans_begin`), 리소스 그룹 전환, query rewrite 플러그인, Performance Schema 와 optimizer trace 계측, 옵티마이저 내부(`Query_expression::optimize`, hypergraph), 반복자 실행기(`unit->execute`)의 내부, DDL 명령들의 개별 처리는 이 흐름의 곁가지라 이름만 적었다.

## 하위 메서드

- [01 do_command](01_do_command/README.md)
- [02 dispatch_command](02_dispatch_command/README.md)
- [03 dispatch_sql_command](03_dispatch_sql_command/README.md)
- [04 parse_sql](04_parse_sql/README.md)
- [05 mysql_execute_command](05_mysql_execute_command/README.md)
- [06 Sql_cmd_dml.execute](06_Sql_cmd_dml.execute/README.md)
- [07 lock_tables](07_lock_tables/README.md)
- [08 ha_innobase.external_lock](08_ha_innobase.external_lock/README.md)
- [09 Sql_cmd_dml.execute_inner](09_Sql_cmd_dml.execute_inner/README.md)
