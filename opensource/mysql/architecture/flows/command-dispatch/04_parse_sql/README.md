# parse_sql

상위: [명령 디스패치](../README.md)

**문자열을 LEX 와 `Sql_cmd` 객체로 바꾸는 입구다.** 실제 문법 처리는 bison 이 `sql_yacc.yy` 에서 만든 `my_sql_parser_parse` 가 하고, 이 함수는 그 앞뒤에 세 가지를 둘러친다. 파서 메모리 상한, 파싱 전용 진단 영역, 문장 digest 계산이다. 파싱 결과 트리(`Parse_tree_root`)는 곧바로 `LEX::make_sql_cmd` 로 `Sql_cmd` 객체가 되고, 이것이 [05] 이후 실행의 주인공이 된다.

## 위치

`sql` / `sql_parse.cc` L7208-L7373 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_parse.cc#L7208-L7373))

## 실제 코드

파서 상태를 THD 에 걸고, digest 를 계산할지 정한다.

`sql` / `sql_parse.cc` L7208-L7261 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_parse.cc#L7208-L7261))

```cpp
// sql_parse.cc L7208-L7261
bool parse_sql(THD *thd, Parser_state *parser_state,
               Object_creation_ctx *creation_ctx) {
  DBUG_TRACE;
  bool ret_value;
  assert(thd->m_parser_state == nullptr);
  // TODO fix to allow parsing gcol exprs after main query.
  //  assert(thd->lex->m_sql_cmd == NULL);

  /* Backup creation context. */

  Object_creation_ctx *backup_ctx = nullptr;

  if (creation_ctx) backup_ctx = creation_ctx->set_n_backup(thd);

  /* Set parser state. */

  thd->m_parser_state = parser_state;

  parser_state->m_digest_psi = nullptr;
  parser_state->m_lip.m_digest = nullptr;

  /*
    Partial parsers (GRAMMAR_SELECTOR_*) are not supposed to compute digests.
  */
  assert(!parser_state->m_lip.is_partial_parser() ||
         !parser_state->m_input.m_has_digest);

  /*
    Only consider statements that are supposed to have a digest,
    like top level queries.
  */
  if (parser_state->m_input.m_has_digest) {
    /*
      For these statements,
      see if the digest computation is required.
    */
    if (thd->m_digest != nullptr) {
      /* Start Digest */
      parser_state->m_digest_psi = MYSQL_DIGEST_START(thd->m_statement_psi);

      if (parser_state->m_input.m_compute_digest ||
          (parser_state->m_digest_psi != nullptr)) {
        /*
          If either:
          - the caller wants to compute a digest
          - the performance schema wants to compute a digest
          set the digest listener in the lexer.
        */
        parser_state->m_lip.m_digest = thd->m_digest;
        parser_state->m_lip.m_digest->m_digest_storage.m_charset_number =
            thd->charset()->number;
      }
    }
  }
```

파싱한다. 파서가 쓰는 메모리에 `parser_max_mem_size` 상한을 걸고, 오류는 별도 진단 영역(`parser_da`)에 모았다가 옮긴다.

`sql` / `sql_parse.cc` L7270-L7335 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_parse.cc#L7270-L7335))

```cpp
// sql_parse.cc L7270-L7335
  Diagnostics_area *parser_da = thd->get_parser_da();
  Diagnostics_area *da = thd->get_stmt_da();

  Parser_oom_handler poomh;
  // Note that we may be called recursively here, on INFORMATION_SCHEMA queries.

  thd->mem_root->set_max_capacity(thd->variables.parser_max_mem_size);
  thd->mem_root->set_error_for_capacity_exceeded(true);
  thd->push_internal_handler(&poomh);

  thd->push_diagnostics_area(parser_da, false);

  const bool mysql_parse_status = thd->sql_parser();

  thd->pop_internal_handler();
  thd->mem_root->set_max_capacity(0);
  thd->mem_root->set_error_for_capacity_exceeded(false);
  /*
    Unwind diagnostics area.

    If any issues occurred during parsing, they will become
    the sole conditions for the current statement.

    Otherwise, if we have a diagnostic statement on our hands,
    we'll preserve the previous diagnostics area here so we
    can answer questions about it.  This specifically means
    that repeatedly asking about a DA won't clear it.

    Otherwise, it's a regular command with no issues during
    parsing, so we'll just clear the DA in preparation for
    the processing of this command.
  */

  if (parser_da->current_statement_cond_count() != 0) {
    /*
      Error/warning during parsing: top DA should contain parse error(s)!  Any
      pre-existing conditions will be replaced. The exception is diagnostics
      statements, in which case we wish to keep the errors so they can be sent
      to the client.
    */
    if (thd->lex->sql_command != SQLCOM_SHOW_WARNS &&
        thd->lex->sql_command != SQLCOM_GET_DIAGNOSTICS)
      da->reset_condition_info(thd);

    /*
      We need to put any errors in the DA as well as the condition list.
    */
    if (parser_da->is_error() && !da->is_error()) {
      da->set_error_status(parser_da->mysql_errno(), parser_da->message_text(),
                           parser_da->returned_sqlstate());
    }

    da->copy_sql_conditions_from_da(thd, parser_da);

    parser_da->reset_diagnostics_area();
    parser_da->reset_condition_info(thd);

    /*
      Do not clear the condition list when starting execution as it
      now contains not the results of the previous executions, but
      a non-zero number of errors/warnings thrown during parsing!
    */
    thd->lex->keep_diagnostics = DA_KEEP_PARSE_ERROR;
  }

  thd->pop_diagnostics_area();
```

`sql` / `sql_parse.cc` L7351-L7373 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_parse.cc#L7351-L7373))

```cpp
// sql_parse.cc L7351-L7373
  /* Reset parser state. */

  thd->m_parser_state = nullptr;

  /* Restore creation context. */

  if (creation_ctx) creation_ctx->restore_env(thd, backup_ctx);

  /* That's it. */

  ret_value = mysql_parse_status;

  if ((ret_value == 0) && (parser_state->m_digest_psi != nullptr)) {
    /*
      On parsing success, record the digest in the performance schema.
    */
    assert(thd->m_digest != nullptr);
    MYSQL_DIGEST_END(parser_state->m_digest_psi,
                     &thd->m_digest->m_digest_storage);
  }

  return ret_value;
}
```

`THD::sql_parser` 가 bison 파서를 부르고 트리를 `Sql_cmd` 로 바꾼다.

`sql` / `sql_class.cc` L3179-L3207 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_class.cc#L3179-L3207))

```cpp
// sql_class.cc L3179-L3207
bool THD::sql_parser() {
  /*
    SQL parser function generated by YACC from sql_yacc.yy.

    In the case of success returns 0, and THD::is_error() is false.
    Otherwise returns 1, or THD::>is_error() is true.

    The second (output) parameter "root" returns the new parse tree.
    It is undefined (unchanged) on error. If "root" is NULL on success,
    then the parser has already called lex->make_sql_cmd() internally.
  */
  extern int my_sql_parser_parse(class THD * thd,
                                 class Parse_tree_root * *root);

  Parse_tree_root *root = nullptr;
  if (my_sql_parser_parse(this, &root) || is_error()) {
    /*
      Restore the original LEX if it was replaced when parsing
      a stored procedure. We must ensure that a parsing error
      does not leave any side effects in the THD.
    */
    cleanup_after_parse_error();
    return true;
  }
  if (root != nullptr && lex->make_sql_cmd(root)) {
    return true;
  }
  return false;
}
```

`sql` / `sql_lex.cc` L5175-L5184 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_lex.cc#L5175-L5184))

```cpp
// sql_lex.cc L5175-L5184
bool LEX::make_sql_cmd(Parse_tree_root *parse_tree) {
  if (!will_contextualize) return false;

  m_sql_cmd = parse_tree->make_cmd(thd);
  if (m_sql_cmd == nullptr) return true;

  assert(m_sql_cmd->sql_command_code() == sql_command);

  return false;
}
```

## 동작 흐름

```text
 L7212  assert(thd->m_parser_state == nullptr)   중첩 파싱이 끝나 있어야 한다
 L7220  creation_ctx 가 있으면 백업             (뷰, 저장 프로그램 본문 파싱 때)
 L7224  thd->m_parser_state = parser_state
 L7239  m_has_digest 이고 (L7244) thd->m_digest 가 있으면
 L7246    MYSQL_DIGEST_START
 L7248    계산이 필요하면 lexer 에 digest 리스너를 건다 (L7256)

 L7270  parser_da = get_parser_da(), da = get_stmt_da()
 L7276  mem_root->set_max_capacity(parser_max_mem_size)
 L7277  용량을 넘으면 오류로
 L7278  push_internal_handler(&poomh)              OOM 을 파서 오류로 바꾸는 핸들러
 L7280  push_diagnostics_area(parser_da)
 L7282  THD::sql_parser()
          sql_class.cc L3194  my_sql_parser_parse(this, &root)
            실패 -> L3200 cleanup_after_parse_error, return true
          L3203  root != nullptr 이면 lex->make_sql_cmd(root)
                   sql_lex.cc L5178  m_sql_cmd = parse_tree->make_cmd(thd)
 L7284  핸들러와 메모리 상한을 걷는다

 L7303  파싱 중 경고나 오류가 있었으면
 L7310    SHOW WARNINGS / GET DIAGNOSTICS 가 아니면 이전 조건을 지운다
 L7317    parser_da 의 오류를 da 로 옮긴다
 L7322    조건 목록 복사, L7324 parser_da 초기화
 L7332    keep_diagnostics = DA_KEEP_PARSE_ERROR
 L7335  pop_diagnostics_area

 L7353  m_parser_state = nullptr
 L7357  creation_ctx 복원
 L7363  성공이고 digest 계측 중이면 MYSQL_DIGEST_END
 L7372  return                                      true 가 실패
```

파싱이 끝나면 LEX 안에 실행에 필요한 것이 다 들어 있다. `INSERT INTO t VALUES (1)` 을 예로 든 모양이다.

```text
 파싱 결과 (INSERT INTO t VALUES (1) 의 경우)

 THD
  +-- lex (LEX)
       +-- sql_command   = SQLCOM_INSERT                  [05] 의 switch 가 본다
       +-- m_sql_cmd     -> Sql_cmd_insert_values          make_sql_cmd 가 만든다
       +-- query_tables  -> Table_ref(t) -> nullptr        [06] 이 열고 [07] 이 잠근다
       +-- query_block   -> Query_block                    SELECT 부분의 틀
       +-- unit          -> Query_expression
       +-- keep_diagnostics                                파싱 경고가 있으면 DA_KEEP_PARSE_ERROR
  +-- m_digest                                             정규화한 토큰 열 (performance_schema digest)

 sql_command 와 m_sql_cmd 의 종류는 반드시 맞아야 한다 (sql_lex.cc L5181 assert)
```

## 결과가 쓰이는 곳

```text
 lex->m_sql_cmd
      --> [05] 의 switch 에서 대부분의 문장이 m_sql_cmd->execute(thd) 로 간다
 lex->sql_command
      --> [03] 의 PSI 세분, check_mqh, [05] 의 switch 와 sql_command_flags 검사
 parser_da 에서 옮긴 오류
      --> [03] 이 err == true 로 실행을 건너뛰고, [02] done: 에서 ERR 패킷으로 나간다
```

## 다루지 않는 것

bison 문법(`sql_yacc.yy`)과 lexer(`Lex_input_stream`, `sql_lex.cc` 의 `MYSQLlex`), 파스 트리 노드(`PT_*`)의 contextualize 단계, `Parse_tree_root::make_cmd` 의 문장별 구현, digest 정규화 규칙, 부분 파서(`GRAMMAR_SELECTOR_*`), 저장 프로그램 파싱 때의 LEX 교체는 이 흐름의 곁가지라 이름만 적었다.
