# ha_innobase::external_lock

상위: [명령 디스패치](../README.md)

**서버가 InnoDB 에게 "이 테이블로 문장을 시작한다 / 끝냈다"를 알리는 콜백이다.** 시작 쪽(`F_RDLCK`, `F_WRLCK`)에서 세 가지가 정해진다. InnoDB 트랜잭션이 서버의 2PC 코디네이터에 등록되고(`innobase_register_trx`), 이 테이블의 읽기가 일관 읽기일지 잠금 읽기일지(`select_lock_type`)가 정해지고, 트랜잭션이 쓰는 테이블 수가 올라간다. 끝 쪽(`F_UNLCK`)은 테이블 수를 내리고, 0 이 되면 문장이 끝난 것으로 본다. InnoDB 트랜잭션 자체(`trx_t`)는 여기서 시작되지 않는다. 첫 행을 건드릴 때 시작되고, 여기서는 `will_lock` 으로 예고만 한다.

## 위치

`storage` / `innobase` / `handler` / `ha_innodb.cc` L18903-L19180 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/ha_innodb.cc#L18903-L19180))

## 실제 코드

입구다. 내부 임시 테이블(intrinsic)은 문장 시작만 표시하고 나간다.

`storage` / `innobase` / `handler` / `ha_innodb.cc` L18903-L18925 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/ha_innodb.cc#L18903-L18925))

```cpp
// ha_innodb.cc L18903-L18925
int ha_innobase::external_lock(THD *thd, /*!< in: handle to the user thread */
                               int lock_type) /*!< in: lock type */
{
  DBUG_TRACE;
  DBUG_PRINT("enter", ("lock_type: %d", lock_type));

  update_thd(thd);

  trx_t *trx = m_prebuilt->trx;

  enum_sql_command sql_command = (enum_sql_command)thd_sql_command(thd);

  ut_ad(m_prebuilt->table);

  if (m_prebuilt->table->is_intrinsic()) {
    if (sql_command == SQLCOM_ALTER_TABLE) {
      return HA_ERR_WRONG_COMMAND;
    }

    TrxInInnoDB::begin_stmt(trx);

    return 0;
  }
```

쓰기 잠금이면 이 handler 의 읽기를 X 잠금으로 바꾼다.

`storage` / `innobase` / `handler` / `ha_innodb.cc` L19013-L19027 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/ha_innodb.cc#L19013-L19027))

```cpp
// ha_innodb.cc L19013-L19027
  if (lock_type == F_WRLCK) {
    /* If this is a SELECT, then it is in UPDATE TABLE ...
    or SELECT ... FOR UPDATE */
    m_prebuilt->select_lock_type = LOCK_X;
    m_stored_select_lock_type = LOCK_X;
  }

  ut_ad(!(lock_type == F_RDLCK && m_prebuilt->select_lock_type == LOCK_X));

  if (lock_type != F_UNLCK) {
    /* MySQL is setting a new table lock */

    *trx->detailed_error = 0;

    innobase_register_trx(ht, thd, trx);
```

읽기 잠금이면 격리 수준과 autocommit 에 따라 잠금 종류를 고른다. 이어서 테이블 수를 세고 문장을 시작한다.

`storage` / `innobase` / `handler` / `ha_innodb.cc` L19067-L19132 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/ha_innodb.cc#L19067-L19132))

```cpp
// ha_innodb.cc L19067-L19132
    if (lock_type == F_RDLCK) {
      /**
        To limit range of circumstances under which transaction's isolation
        level can be compromised, we allow disabling readlocks only for DD
        and ACL tables.
       */
      ut_ad(!m_prebuilt->no_read_locking || m_prebuilt->table->is_dd_table ||
            is_acl_table(table));

      if (m_prebuilt->table->is_dd_table || m_prebuilt->no_read_locking) {
        m_prebuilt->select_lock_type = LOCK_NONE;
        m_stored_select_lock_type = LOCK_NONE;
      } else if (trx->isolation_level == TRX_ISO_SERIALIZABLE &&
                 m_prebuilt->select_lock_type == LOCK_NONE &&
                 thd_test_options(thd, OPTION_NOT_AUTOCOMMIT | OPTION_BEGIN)) {
        m_prebuilt->select_lock_type = LOCK_S;
        m_stored_select_lock_type = LOCK_S;
      } else {
        // Retain value set earlier for example via store_lock()
        // which is LOCK_S or LOCK_NONE
        ut_ad(m_prebuilt->select_lock_type == LOCK_S ||
              m_prebuilt->select_lock_type == LOCK_NONE);
      }
    }

    /* Starting from 4.1.9, no InnoDB table lock is taken in LOCK
    TABLES if AUTOCOMMIT=1. It does not make much sense to acquire
    an InnoDB table lock if it is released immediately at the end
    of LOCK TABLES, and InnoDB's table locks in that case cause
    VERY easily deadlocks.

    We do not set InnoDB table locks if user has not explicitly
    requested a table lock. Note that thd_in_lock_tables(thd)
    can hold in some cases, e.g., at the start of a stored
    procedure call (SQLCOM_CALL). */

    if (m_prebuilt->select_lock_type != LOCK_NONE) {
      if (sql_command == SQLCOM_LOCK_TABLES && THDVAR(thd, table_locks) &&
          thd_test_options(thd, OPTION_NOT_AUTOCOMMIT) &&
          thd_in_lock_tables(thd)) {
        dberr_t error = row_lock_table(m_prebuilt);

        if (error != DB_SUCCESS) {
          return convert_error_code_to_mysql(error, 0, thd);
        }
      }

      trx->mysql_n_tables_locked++;
    }

    trx->n_mysql_tables_in_use++;
    m_mysql_has_locked = true;

    if (!trx_is_started(trx) && (m_prebuilt->select_lock_type != LOCK_NONE ||
                                 m_stored_select_lock_type != LOCK_NONE)) {
      ++trx->will_lock;
    }

    TrxInInnoDB::begin_stmt(trx);

#ifdef UNIV_DEBUG
    if (thd != nullptr && thd_tx_is_dd_trx(thd)) {
      trx->is_dd_trx = true;
    }
#endif /* UNIV_DEBUG */
    return 0;
```

`F_UNLCK` 쪽이다. 마지막 테이블이 풀리면 문장이 끝난다.

`storage` / `innobase` / `handler` / `ha_innodb.cc` L19133-L19180 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/ha_innodb.cc#L19133-L19180))

```cpp
// ha_innodb.cc L19133-L19180
  } else {
    TrxInInnoDB::end_stmt(trx);

    DEBUG_SYNC_C("ha_innobase_end_statement");
  }

  /* MySQL is releasing a table lock */

  trx->n_mysql_tables_in_use--;
  m_mysql_has_locked = false;

  innobase_srv_conc_force_exit_innodb(trx);

  /* If the MySQL lock count drops to zero we know that the current SQL
  statement has ended */

  if (trx->n_mysql_tables_in_use == 0) {
    trx->mysql_n_tables_locked = 0;
    m_prebuilt->used_in_HANDLER = false;

    if (!thd_test_options(thd, OPTION_NOT_AUTOCOMMIT | OPTION_BEGIN)) {
      if (trx_is_started(trx)) {
        innobase_commit(ht, thd, true);
      } else {
        /* Since the trx state is TRX_NOT_STARTED,
        trx_commit() will not be called. Reset
        trx->is_dd_trx here */
        ut_d(trx->is_dd_trx = false);
      }

    } else if (trx->isolation_level <= TRX_ISO_READ_COMMITTED &&
               MVCC::is_view_active(trx->read_view)) {
      mutex_enter(&trx_sys->mutex);

      trx_sys->mvcc->view_close(trx->read_view, true);

      mutex_exit(&trx_sys->mutex);
    }
  }

  if (!trx_is_started(trx) && lock_type != F_UNLCK &&
      (m_prebuilt->select_lock_type != LOCK_NONE ||
       m_stored_select_lock_type != LOCK_NONE)) {
    ++trx->will_lock;
  }

  return 0;
}
```

2PC 등록이다. 문장(`all=false`)에는 늘 등록하고, 트랜잭션(`all=true`)에는 autocommit 이 꺼져 있거나 `BEGIN` 안일 때만 등록한다.

`storage` / `innobase` / `handler` / `ha_innodb.cc` L3033-L3053 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/ha_innodb.cc#L3033-L3053))

```cpp
// ha_innodb.cc L3033-L3053
/** Registers an InnoDB transaction with the MySQL 2PC coordinator, so that
 the MySQL XA code knows to call the InnoDB prepare and commit, or rollback
 for the transaction. This MUST be called for every transaction for which
 the user may call commit or rollback. Calling this several times to register
 the same transaction is allowed, too. This function also registers the
 current SQL statement. */
void innobase_register_trx(handlerton *hton, /* in: Innobase handlerton */
                           THD *thd,   /* in: MySQL thd (connection) object */
                           trx_t *trx) /* in: transaction to register */
{
  const ulonglong trx_id = static_cast<ulonglong>(trx_get_id_for_print(trx));

  trans_register_ha(thd, false, hton, &trx_id);

  if (!trx_is_registered_for_2pc(trx) &&
      thd_test_options(thd, OPTION_NOT_AUTOCOMMIT | OPTION_BEGIN)) {
    trans_register_ha(thd, true, hton, &trx_id);
  }

  trx_register_for_2pc(trx);
}
```

서버 쪽 `trans_register_ha` 는 엔진을 `Transaction_ctx` 의 STMT 또는 SESSION 목록에 붙인다. 같은 엔진을 두 번 붙이지 않는다.

`sql` / `handler.cc` L1368-L1406 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/handler.cc#L1368-L1406))

```cpp
// handler.cc L1368-L1406
void trans_register_ha(THD *thd, bool all, handlerton *ht_arg,
                       const ulonglong *trxid [[maybe_unused]]) {
  Ha_trx_info *ha_info;
  Transaction_ctx *trn_ctx = thd->get_transaction();
  const Transaction_ctx::enum_trx_scope trx_scope =
      all ? Transaction_ctx::SESSION : Transaction_ctx::STMT;

  DBUG_TRACE;
  DBUG_PRINT("enter", ("%s", all ? "all" : "stmt"));

  if (all) {
    /*
      Ensure no active backup engine data exists, unless the current
      transaction is from replication and in active xa state.
    */
    assert(
        thd->get_ha_data(ht_arg->slot)->ha_ptr_backup == nullptr ||
        (thd->get_transaction()->xid_state()->has_state(XID_STATE::XA_ACTIVE)));
    assert(thd->get_ha_data(ht_arg->slot)->ha_ptr_backup == nullptr ||
           (thd->is_binlog_applier() || thd->slave_thread));

    thd->server_status |= SERVER_STATUS_IN_TRANS;
    if (thd->tx_read_only)
      thd->server_status |= SERVER_STATUS_IN_TRANS_READONLY;
    DBUG_PRINT("info", ("setting SERVER_STATUS_IN_TRANS"));
  }

  ha_info = thd->get_ha_data(ht_arg->slot)->ha_info + (all ? 1 : 0);

  if (ha_info->is_started()) {
    assert(trn_ctx->ha_trx_info(trx_scope));
    return; /* already registered, return */
  }

  trn_ctx->register_ha(trx_scope, ha_info, ht_arg);
  trn_ctx->set_ha_trx_info(trx_scope, ha_info);

  if (ht_arg->prepare == nullptr) trn_ctx->set_no_2pc(trx_scope, true);

```

## 동작 흐름

```text
 L18909  update_thd(thd)                       m_prebuilt->trx 를 이 THD 의 trx 로
 L18917  intrinsic 테이블이면 begin_stmt 만 하고 return
 L18934  F_WRLCK + STATEMENT binlog + table_flags 에 HA_BINLOG_STMT_CAPABLE 없음 -> HA_ERR_LOGGING_IMPOSSIBLE
         (InnoDB 는 격리 수준이 RC 이하면 그 플래그를 빼 둔다, L6592-L6596)
 L18953  innodb_read_only 인데 갱신 문장이면 오류
 L18969  sql_stat_start = true                  "이번 문장의 첫 호출" 표시
 L18974  quiesce 상태 처리                      FLUSH TABLES ... FOR EXPORT
 L19013  F_WRLCK 이면 select_lock_type = LOCK_X

 L19022  lock_type != F_UNLCK                   문장 시작
 L19027    innobase_register_trx(ht, thd, trx)
             L3045  trans_register_ha(thd, false, ...)       STMT 목록
             L3047  2PC 미등록이고 NOT_AUTOCOMMIT 또는 BEGIN 이면
             L3049    trans_register_ha(thd, true, ...)      SESSION 목록
             L3052  trx_register_for_2pc -> trx->is_registered = true (L2898)
 L19067    F_RDLCK 이면 잠금 종류 결정 (아래 표)
 L19104    LOCK TABLES + innodb_table_locks + autocommit=0 이면 row_lock_table (InnoDB 테이블 잠금)
 L19114    잠금 읽기면 mysql_n_tables_locked++
 L19117    n_mysql_tables_in_use++
 L19120    trx 가 아직 시작 전이고 잠금 읽기면 ++will_lock
 L19125    TrxInInnoDB::begin_stmt
 L19132    return 0

 L19133  else (F_UNLCK)                          문장 끝
 L19141    n_mysql_tables_in_use--
 L19149    0 이 되면
 L19153      autocommit 이고 trx 가 시작돼 있으면 L19155 innobase_commit(ht, thd, true)
 L19163      아니고 RC 이하면 read view 를 닫는다  (문장마다 새 스냅숏)
```

읽기 잠금 종류는 소스 주석(L19029-L19066)의 표가 정본이다. 요지만 옮기면 이렇다.

```text
 F_RDLCK 일 때 select_lock_type (L19067-L19090)

 select_lock_type  경우
 LOCK_NONE         DD 테이블이거나 no_read_locking
 LOCK_S            SERIALIZABLE 이고 LOCK_NONE 이었고 autocommit=0 또는 BEGIN 안
                   일반 SELECT 가 공유 잠금 읽기가 된다
 unchanged         그 밖. store_lock 이 정해 둔 값을 유지한다
                   일반 SELECT 는 LOCK_NONE (일관 읽기), FOR SHARE 는 LOCK_S
 LOCK_X            F_WRLCK 일 때 (L19013). UPDATE, DELETE, FOR UPDATE

 LOCK_NONE  --> [일관 읽기(MVCC)] 의 read view 경로
 LOCK_S / X --> [레코드 잠금] 의 lock_rec_lock 경로
```

서버와 InnoDB 가 각자 세는 것이 무엇인지 나란히 두면 이 함수의 역할이 보인다.

```text
 문장 하나 동안 두 계층의 표시 (INSERT INTO t ..., autocommit=1)

 lock_tables (external_lock F_WRLCK)
   서버    Transaction_ctx 의 STMT 목록에 innobase 추가, SESSION 목록은 비어 있음
   InnoDB  n_mysql_tables_in_use = 1, is_registered = true, state = NOT_STARTED, will_lock = 1

 첫 행 쓰기 ([행 쓰기])
   InnoDB  trx_start_if_not_started_xa -> ACTIVE
           (row_insert_for_mysql_using_ins_graph, row0mysql.cc L1557)

 [05] trans_commit_stmt
   서버    ha_commit_trans(all=false). SESSION 이 비어 있어 진짜 커밋
   InnoDB  innobase_commit -> 커밋

 close_thread_tables (external_lock F_UNLCK)
   InnoDB  n_mysql_tables_in_use = 0. 이미 커밋되어 L19155 은 건너뛴다
```

## 결과가 쓰이는 곳

```text
 Transaction_ctx 의 Ha_trx_info 목록 (trans_register_ha)
      --> [커밋과 binlog 2PC] 의 ha_commit_trans 가 rw_ha_count 를 세고 prepare / commit 할 엔진

 m_prebuilt->select_lock_type
      --> [일관 읽기(MVCC)] row_search_mvcc 가 LOCK_NONE 이면 read view 로 읽는다
      --> [레코드 잠금] LOCK_S / LOCK_X 면 레코드마다 잠근다

 trx->will_lock
      --> 트랜잭션이 시작될 때 읽기 전용으로 둘지 판단하는 재료
```

## 다루지 않는 것

`FLUSH TABLES ... FOR EXPORT` 의 quiesce, `LOCK TABLES` 의 InnoDB 테이블 잠금(`row_lock_table`), `innodb_read_only` 모드, STATEMENT binlog 형식 거부 조건, `TrxInInnoDB` 의 동시성 표시, `start_stmt`(LOCK TABLES 안의 문장 시작)는 이 흐름의 곁가지라 줄만 적었다. 트랜잭션이 실제로 시작되는 자리는 [행 쓰기](../../row-insert/README.md)에 있다.
