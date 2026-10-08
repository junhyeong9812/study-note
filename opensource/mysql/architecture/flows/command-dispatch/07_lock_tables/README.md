# lock_tables

상위: [명령 디스패치](../README.md)

**문장이 쓰는 테이블 전부를 한 번에 잠그는 자리이고, 서버 계층이 스토리지 엔진에게 "문장이 시작된다"고 처음 알리는 자리다.** 잠금은 두 겹이다. 먼저 테이블마다 `handler::ha_external_lock` 을 불러 엔진에 알리고(InnoDB 는 여기서 트랜잭션을 등록한다, [08]), 그다음 서버의 테이블 잠금 `thr_multi_lock` 을 건다. 함수 머리 주석이 규칙을 적어 두었다. thr_lock 을 쥔 채 다시 부르면 안 되고, 필요한 잠금은 전부 한 번에 잡아야 한다.

## 위치

`sql` / `sql_base.cc` L7293-L7503 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_base.cc#L7293-L7503))

## 실제 코드

잠글 테이블이 없으면 표시만 하고 binlog 형식만 정한다.

`sql` / `sql_base.cc` L7293-L7319 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_base.cc#L7293-L7319))

```cpp
// sql_base.cc L7293-L7319
bool lock_tables(THD *thd, Table_ref *tables, uint count, uint flags) {
  Table_ref *table;

  DBUG_TRACE;
  /*
    We can't meet statement requiring prelocking if we already
    in prelocked mode.
  */
  assert(thd->locked_tables_mode <= LTM_LOCK_TABLES ||
         !thd->lex->requires_prelocking());

  /*
    lock_tables() should not be called if this statement has
    already locked its tables.
  */
  assert(thd->lex->lock_tables_state == Query_tables_list::LTS_NOT_LOCKED);

  if (!tables && !thd->lex->requires_prelocking()) {
    /*
      Even though we are not really locking any tables mark this
      statement as one that has locked its tables, so we won't
      call this function second time for the same execution of
      the same statement.
    */
    thd->lex->lock_tables_state = Query_tables_list::LTS_LOCKED;
    const int ret = thd->decide_logging_format(tables);
    return ret;
```

`LOCK TABLES` 모드가 아니면 잠글 `TABLE` 배열을 만들어 `mysql_lock_tables` 에 한 번에 넘긴다.

`sql` / `sql_base.cc` L7332-L7385 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_base.cc#L7332-L7385))

```cpp
// sql_base.cc L7332-L7385
  if (!thd->locked_tables_mode) {
    assert(thd->lock == nullptr);  // You must lock everything at once
    TABLE **start, **ptr;

    if (!(ptr = start = (TABLE **)thd->alloc(sizeof(TABLE *) * count)))
      return true;
    for (table = tables; table; table = table->next_global) {
      if (!table->is_placeholder() &&
          /*
            Do not call handler::store_lock()/external_lock() for temporary
            tables from prelocking list.

            Prelocking algorithm does not add element for a table to the
            prelocking list if it finds that the routine that uses the table can
            create it as a temporary during its execution. Note that such
            routine actually can use existing temporary table if its CREATE
            TEMPORARY TABLE has IF NOT EXISTS clause. For such tables we rely on
            calls to handler::start_stmt() done by routine's substatement when
            it accesses the table to inform storage engine about table
            participation in transaction and type of operation carried out,
            instead of calls to handler::store_lock()/external_lock() done at
            prelocking stage.

            In cases when statement uses two routines one of which can create
            temporary table and modifies it, while another only reads from this
            table, storage engine might be confused about real operation type
            performed by the whole statement. Calls to
            handler::store_lock()/external_lock() done at prelocking stage will
            inform SE only about read part, while information about modification
            will be delayed until handler::start_stmt() call during execution of
            the routine doing modification. InnoDB considers this breaking of
            promise about operation type and fails on assertion.

            To avoid this problem we try to handle both the cases when temporary
            table can be created by routine and the case when it is created
            outside of routine and only accessed by it, uniformly. We don't call
            handler::store_lock()/external_lock() for temporary tables used by
            routines at prelocking stage and rely on calls to
            handler::start_stmt(), which happen during substatement execution,
            to pass correct information about operation type instead.
          */
          !(table->prelocking_placeholder &&
            table->table->s->tmp_table != NO_TMP_TABLE)) {
        *(ptr++) = table->table;
      }
    }

    DEBUG_SYNC(thd, "before_lock_tables_takes_lock");

    if (!(thd->lock =
              mysql_lock_tables(thd, start, (uint)(ptr - start), flags)))
      return true;

    DEBUG_SYNC(thd, "after_lock_tables_takes_lock");
```

끝에서 잠금 상태를 표시하고 이 문장의 binlog 형식(STATEMENT / ROW)을 정한다.

`sql` / `sql_base.cc` L7494-L7503 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_base.cc#L7494-L7503))

```cpp
// sql_base.cc L7494-L7503
  /*
    Mark the statement as having tables locked. For purposes
    of Query_tables_list::lock_tables_state we treat any
    statement which passes through lock_tables() as such.
  */
  thd->lex->lock_tables_state = Query_tables_list::LTS_LOCKED;

  const int ret = thd->decide_logging_format(tables);
  return ret;
}
```

`mysql_lock_tables` 는 엔진 통지(`lock_external`)를 먼저, thr_lock 을 나중에 한다.

`sql` / `lock.cc` L317-L361 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/lock.cc#L317-L361))

```cpp
// lock.cc L317-L361
MYSQL_LOCK *mysql_lock_tables(THD *thd, TABLE **tables, size_t count,
                              uint flags) {
  int rc;
  MYSQL_LOCK *sql_lock;
  const ulong timeout = (flags & MYSQL_LOCK_IGNORE_TIMEOUT)
                            ? LONG_TIMEOUT
                            : thd->variables.lock_wait_timeout;

  DBUG_TRACE;

  if (lock_tables_check(thd, tables, count, flags)) return nullptr;

  if (!(sql_lock = get_lock_data(thd, tables, count, GET_LOCK_STORE_LOCKS)))
    return nullptr;

  if (!(thd->state_flags & Open_tables_state::SYSTEM_TABLES))
    THD_STAGE_INFO(thd, stage_system_lock);

  const ulonglong lock_start_usec = my_micro_time();

  DBUG_PRINT("info", ("thd->proc_info %s", thd->proc_info()));
  if (sql_lock->table_count &&
      lock_external(thd, sql_lock->table, sql_lock->table_count)) {
    /* Clear the lock type of all lock data to avoid reusage. */
    reset_lock_data_and_free(&sql_lock);
    goto end;
  }

  /* Copy the lock data array. thr_multi_lock() reorders its contents. */
  memcpy(sql_lock->locks + sql_lock->lock_count, sql_lock->locks,
         sql_lock->lock_count * sizeof(*sql_lock->locks));
  /* Lock on the copied half of the lock data array. */
  rc = thr_lock_errno_to_mysql[(int)thr_multi_lock(
      sql_lock->locks + sql_lock->lock_count, sql_lock->lock_count,
      &thd->lock_info, timeout)];

  DBUG_EXECUTE_IF("mysql_lock_tables_kill_query",
                  thd->killed = THD::KILL_QUERY;);

  if (rc) {
    if (sql_lock->table_count)
      (void)unlock_external(thd, sql_lock->table, sql_lock->table_count);
    reset_lock_data_and_free(&sql_lock);
    if (!thd->killed) my_error(rc, MYF(0));
  }
```

`lock_external` 이 테이블마다 읽기인지 쓰기인지를 정해 `ha_external_lock` 을 부른다. 하나라도 실패하면 앞에서 잠근 것을 거꾸로 푼다.

`sql` / `lock.cc` L381-L409 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/lock.cc#L381-L409))

```cpp
// lock.cc L381-L409
static int lock_external(THD *thd, TABLE **tables, uint count) {
  uint i;
  int lock_type, error;
  DBUG_TRACE;

  DBUG_PRINT("info", ("count %d", count));
  for (i = 1; i <= count; i++, tables++) {
    assert((*tables)->reginfo.lock_type >= TL_READ);
    lock_type = F_WRLCK; /* Lock exclusive */
    if ((*tables)->db_stat & HA_READ_ONLY ||
        ((*tables)->reginfo.lock_type >= TL_READ &&
         (*tables)->reginfo.lock_type <= TL_READ_NO_INSERT))
      lock_type = F_RDLCK;

    if ((error = (*tables)->file->ha_external_lock(thd, lock_type))) {
      print_lock_error(error, (*tables)->file->table_type());
      while (--i) {
        tables--;
        (*tables)->file->ha_external_lock(thd, F_UNLCK);
        (*tables)->current_lock = F_UNLCK;
      }
      return error;
    } else {
      (*tables)->db_stat &= ~HA_BLOCK_LOCK;
      (*tables)->current_lock = lock_type;
    }
  }
  return 0;
}
```

## 동작 흐름

```text
 L7301  assert: prelocking 모드 안에서 다시 prelocking 하지 않는다
 L7308  assert: 이 문장은 아직 잠그지 않았다
 L7310  tables == nullptr 이고 prelocking 도 없으면
 L7317    LTS_LOCKED 표시, L7318 decide_logging_format 만 하고 끝

 L7332  locked_tables_mode 가 아니면 (보통의 경우)
 L7336    TABLE* 배열을 count 만큼 할당
 L7338    table 목록을 돌며 L7375 *(ptr++) = table->table
            (자리표시자, 루틴이 만드는 임시 테이블은 뺀다. 이유는 주석 L7340-L7372)
 L7381    thd->lock = mysql_lock_tables(thd, start, n, flags)
            lock.cc L327  lock_tables_check
            lock.cc L329  get_lock_data(GET_LOCK_STORE_LOCKS)   thr_lock 에 넘길 잠금 목록
            lock.cc L339  lock_external           --> 테이블마다 ha_external_lock --> [08]
            lock.cc L349  thr_multi_lock(..., lock_wait_timeout)
            lock.cc L356  실패면 unlock_external 로 엔진 통지를 되돌린다
 L7387    prelocking 이 필요한 문장이면 LTM_PRELOCKED 로 (저장 함수, 트리거)
 L7420  LOCK TABLES 모드면 이미 잠겨 있으므로 check_lock_and_start_stmt 로 문장 시작만 알린다

 L7499  lock_tables_state = LTS_LOCKED
 L7501  decide_logging_format(tables)      이 문장을 STATEMENT 로 쓸지 ROW 로 쓸지
```

`lock_external` 이 고르는 잠금 종류는 파서가 테이블마다 정해 둔 `reginfo.lock_type` 에서 나온다. InnoDB 에게 넘어가는 것은 이 둘 중 하나다.

```text
 reginfo.lock_type -> ha_external_lock 의 인자 (lock.cc L389-L393)

 external_lock  reginfo.lock_type                 예
 F_RDLCK        TL_READ .. TL_READ_NO_INSERT      SELECT, SELECT ... FOR SHARE
 F_WRLCK        > TL_READ_NO_INSERT (TL_WRITE*)   INSERT, UPDATE, DELETE, SELECT ... FOR UPDATE
 F_RDLCK        db_stat & HA_READ_ONLY            읽기 전용으로 열린 테이블

 InnoDB 는 F_WRLCK 을 받으면 select_lock_type = LOCK_X 로 둔다 ([08] L19013)
```

위 표의 "예" 열은 파서가 문장 종류별로 적는 잠금 종류에서 나온다. 파서는 `TL_*_DEFAULT` 같은 파서 전용 값을 적고, `open_tables` 가 테이블을 연 뒤 실제 값으로 바꿔 `reginfo.lock_type` 에 넣는다(sql_base.cc L6353-L6363).

```text
 문장 종류 -> reginfo.lock_type 의 출처

 stmt          parser value                  after open_tables                 source
 SELECT        TL_READ_DEFAULT               TL_READ or TL_READ_NO_INSERT      sql_base.cc L6360, L4426
 FOR SHARE     TL_READ_WITH_SHARED_LOCKS     same                              parse_tree_nodes.h L792
 FOR UPDATE    TL_WRITE                      same                              parse_tree_nodes.h L789
 INSERT        TL_WRITE_CONCURRENT_DEFAULT   insert_lock_default               sql_yacc.yy L13725, parse_tree_nodes.cc L1403
 UPDATE        TL_WRITE_DEFAULT              update_lock_default               sql_yacc.yy L13995, parse_tree_nodes.cc L1320
 DELETE        TL_WRITE_DEFAULT              update_lock_default               parse_tree_nodes.cc L1213-L1215

 insert_lock_default 는 TL_WRITE_CONCURRENT_INSERT, update_lock_default 는 TL_WRITE 이다
   (low_priority_updates 면 둘 다 TL_WRITE_LOW_PRIORITY, sql_class.cc L1181-L1185)
 SELECT 의 테이블이 TL_READ_NO_INSERT 가 되는 것은 binlog 가 켜져 있고 형식이 ROW 가 아니며(STATEMENT, MIXED)
   갱신 문장 안의 읽기인 경우 등이다 (L4426 read_lock_type_for_table)
 파서 쪽 근거: 테이블의 기본값 TL_READ_DEFAULT 는 Yacc_state 초기화(sql_lex.h L4948), FOR SHARE / FOR UPDATE 는
   PT_query_block_locking_clause::set_lock_for_tables (parse_tree_nodes.cc L2713) 가 get_lock_descriptor 값으로,
   INSERT / UPDATE 는 Query_block::set_lock_for_tables (sql_parse.cc L6478) 가 문법의 lock 옵션 값으로 덮어쓴다
 다중 테이블 UPDATE 는 읽기만 하는 테이블의 잠금을 prepare_inner 에서 낮춘다 (parse_tree_nodes.cc L1315-L1319 주석)
```

```text
 두 겹의 잠금과 푸는 순서

 잡는 순서 (mysql_lock_tables)
   1. lock_external  -> ha_external_lock(F_*)     엔진이 문장 시작을 안다
   2. thr_multi_lock                               서버 테이블 잠금 (thr_lock)

 푸는 곳 (문장 끝, [05] L5002 close_thread_tables -> sql_base.cc L1731 mysql_unlock_tables)
   1. thr_multi_unlock                             lock.cc L414  서버 테이블 잠금을 먼저 푼다
   2. unlock_external -> ha_external_lock(F_UNLCK) lock.cc L416  그다음 엔진에 문장 끝을 알린다

 2 가 실패하면 lock.cc L358 unlock_external 이 1 을 되돌린다
 1 이 중간에 실패하면 lock.cc L397-L401 이 앞서 성공한 테이블을 F_UNLCK 으로 푼다
```

## 결과가 쓰이는 곳

```text
 thd->lock (MYSQL_LOCK)
      --> 문장 끝 close_thread_tables 에서 mysql_unlock_tables 가 푼다

 ha_external_lock 호출
      --> [08] ha_innobase::external_lock 이 InnoDB 트랜잭션을 서버 2PC 목록에 올린다

 decide_logging_format 의 결과
      --> [커밋과 binlog 2PC] 에서 binlog 캐시에 쌓인 이벤트의 형식
```

## 다루지 않는 것

`LOCK TABLES` 명시 잠금 모드와 prelocking(저장 함수, 트리거가 쓰는 테이블을 미리 잠그는 것), `thr_lock` 의 대기열과 우선순위, `get_lock_data` 와 `handler::store_lock` 의 잠금 종류 변환, `decide_logging_format` 의 binlog 형식 판정 규칙, 데이터 사전 테이블용 `lock_dictionary_tables` 는 이 흐름의 곁가지라 줄만 적었다.
