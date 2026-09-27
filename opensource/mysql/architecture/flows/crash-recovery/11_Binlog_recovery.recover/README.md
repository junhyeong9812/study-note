# Binlog_recovery::recover

상위: [크래시 복구](../README.md)

**InnoDB 가 PREPARED 로 남긴 트랜잭션의 운명을 binlog 로 정하는 서버 쪽 함수다.** 2PC 에서는 InnoDB prepare 가 binlog 쓰기보다 앞선다(`MYSQL_BIN_LOG::prepare` 다음에 `ordered_commit`). 그래서 크래시 뒤에는 "InnoDB 에서는 PREPARED 인데 binlog 에는 있는가"가 커밋 여부의 기준이 된다. 이 함수는 마지막 binlog 파일을 끝까지 읽어 **완결된 트랜잭션의 XID 집합**을 모으고, `ha_recover` 로 엔진마다 PREPARED 목록을 받아 집합에 든 것은 `commit_by_xid`, 없는 것은 `rollback_by_xid` 로 처리한다. 이어서 binlog 를 마지막 유효 위치에서 자른다.

## 위치

`sql` / `binlog` / `recovery.cc` L53-L63 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/binlog/recovery.cc#L53-L63))

## 실제 코드

본체는 두 줄이다. 로그를 훑고, 엔진 복구를 부른다.

`sql` / `binlog` / `recovery.cc` L53-L63 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/binlog/recovery.cc#L53-L63))

```cpp
// binlog/recovery.cc L53-L63
binlog::Binlog_recovery &binlog::Binlog_recovery::recover() {
  process_logs(m_reader);
  if (!this->is_log_malformed() && total_ha_2pc > 1) {
    Xa_state_list xa_list{this->m_external_xids};
    this->m_no_engine_recovery = ha_recover(&this->m_internal_xids, &xa_list);
    if (this->m_no_engine_recovery) {
      this->m_failure_message.assign("Recovery failed in storage engines");
    }
  }
  return (*this);
}
```

부르는 쪽은 binlog 를 여는 `open_binlog` 다. 마지막 파일의 IN_USE 플래그가 없으면(정상 종료) 이 함수를 부르지 않는다.

`sql` / `binlog.cc` L6940-L6993 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/binlog.cc#L6940-L6993))

```cpp
// binlog.cc L6940-L6993
  /*
    If the binary log was not properly closed it means that the server
    may have crashed. In that case, we need to call
    binlog::Binlog_recovery::recover()
    to:
      a) collect logged XIDs;
      b) complete the 2PC of the pending XIDs;
      c) collect the last valid position.

    Therefore, we do need to iterate over the binary log, even if
    total_ha_2pc == 1, to find the last valid group of events written.
    Later we will take this value and truncate the log if need be.
  */
  if (!read_binlog_in_use_flag(binlog_file_reader)) {
    /* should execute ha_recover */
    error = ha_recover();
    if (error) LogErr(ERROR_LEVEL, ER_BINLOG_CRASH_RECOVERY_ERROR_RETURNED_SE);
    return error;
  }

  LogErr(INFORMATION_LEVEL, ER_BINLOG_RECOVERING_AFTER_CRASH_USING, opt_name);

  binlog::Binlog_recovery bl_recovery{binlog_file_reader};
  bl_recovery.recover();

  my_off_t valid_pos = bl_recovery.get_valid_pos();
  my_off_t binlog_size = binlog_file_reader.ifile()->length();

  if (bl_recovery.is_binlog_malformed()) {
    LogErr(ERROR_LEVEL, ER_BINLOG_CRASH_RECOVERY_MALFORMED_LOG, log_name,
           valid_pos, binlog_file_reader.position(),
           bl_recovery.get_failure_message().data());
    return 1;
  }
  if (bl_recovery.has_engine_recovery_failed()) {
    /* truncate log file but do not clear LOG_EVENT_IN_USE_F flag */
    LogErr(ERROR_LEVEL, ER_BINLOG_CRASH_RECOVERY_ERROR_RETURNED_SE);
    if (!truncate_update_log_file(log_name, valid_pos, binlog_size, false)) {
      /* log error has been written */
    }
    return 1;
  }

  /* Trim the crashed binlog file to last valid transaction
     or event (non-transaction) base on valid_pos. */
  if (valid_pos > 0) {
    /* truncate log file and clear LOG_EVENT_IN_USE_F flag */
    if (!truncate_update_log_file(log_name, valid_pos, binlog_size, true)) {
      /* log error has been written */
      return 1;
    }
  }  // end if (valid_pos > 0)

  return 0;
```

XID 이벤트 하나가 트랜잭션 하나를 닫고, 그 XID 가 집합에 들어간다.

`sql` / `binlog` / `log_sanitizer.cc` L95-L112 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/binlog/log_sanitizer.cc#L95-L112))

```cpp
// log_sanitizer.cc L95-L112
void Log_sanitizer::process_xid_event(Xid_log_event const &ev) {
  if (!m_validation_started) {
    m_validation_started = true;
    m_in_transaction = true;
  }
  this->m_is_malformed = !this->m_in_transaction;
  if (this->m_is_malformed) {
    this->m_failure_message.assign(
        "Xid_log_event outside the boundary of a sequence of events "
        "representing an active transaction");
    return;
  }
  this->m_in_transaction = false;
  if (!this->m_internal_xids.insert(ev.xid).second) {
    this->m_is_malformed = true;
    this->m_failure_message.assign("Xid_log_event holds an invalid XID");
  }
}
```

엔진마다 PREPARED 목록을 받아 하나씩 처리한다.

`sql` / `xa` / `recovery.cc` L191-L239 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/xa/recovery.cc#L191-L239))

```cpp
// xa/recovery.cc L191-L239
bool xa::recovery::recover_one_ht(THD *, plugin_ref plugin, void *arg) {
  handlerton *ht = plugin_data<handlerton *>(plugin);
  xarecover_st *info = static_cast<struct xarecover_st *>(arg);
  int got;

  if (ht->state == SHOW_OPTION_YES && ht->recover) {
    ::recovery_statistics external_stats{{0, 0, 0}, {0, 0, 0}};
    ::recovery_statistics internal_stats{{0, 0, 0}, {0, 0, 0}};
    while (
        (got = ht->recover(
             ht, info->list, info->len,
             Recovered_xa_transactions::instance().get_allocated_memroot())) >
        0) {
      assert(got <= info->len);
      LogErr(INFORMATION_LEVEL, ER_XA_RECOVER_FOUND_TRX_IN_SE, got,
             ha_resolve_storage_engine_name(ht));

      for (int i = 0; i < got; ++i) {
        auto &xa_trx = info->list[i];
        my_xid xid = xa_trx.id.get_my_xid();

        if (!xid) {  // Externally coordinated transaction
          ::recover_one_external_trx(*info, *ht, xa_trx, external_stats);
          ++info->found_foreign_xids;
          continue;
        }

        if (info->dry_run) {  // No information provided w.r.t TC state so,
                              // nothing to do in regards to internally
                              // coordinated transactions
          ++info->found_my_xids;
          continue;
        }

        // Internally coordinated transaction
        ::recover_one_internal_trx(*info, *ht, xa_trx, xid, internal_stats);
      }
      if (got < info->len) break;
    }
    bool has_failures =
        ::has_failures(internal_stats) || ::has_failures(external_stats);
    LogErr(has_failures ? ERROR_LEVEL : INFORMATION_LEVEL,
           ER_BINLOG_CRASH_RECOVERY_ENGINE_RESULTS,
           ha_resolve_storage_engine_name(ht),
           ::print_stats(internal_stats, external_stats).data());
    DBUG_EXECUTE_IF("xa_recovery_error_reporting", return has_failures;);
  }
  return false;
}
```

내부 2PC 트랜잭션 하나의 판정이다.

`sql` / `xa` / `recovery.cc` L242-L275 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/xa/recovery.cc#L242-L275))

```cpp
// xa/recovery.cc L242-L275
void recover_one_internal_trx(xarecover_st const &info, handlerton &ht,
                              XA_recover_txn const &xa_trx, my_xid xid,
                              ::recovery_statistics &stats) {
  if (info.commit_list ? info.commit_list->count(xid) != 0
                       : tc_heuristic_recover == TC_HEURISTIC_RECOVER_COMMIT) {
    enum xa_status_code exec_status;
    if (DBUG_EVALUATE_IF("xa_recovery_error_reporting", true, false))
      exec_status = ::generate_xa_recovery_error();
    else
      exec_status = ht.commit_by_xid(&ht, const_cast<XID *>(&xa_trx.id));

    if (exec_status == XA_OK)
      ::add_to_stats<STATS_SUCCESS, STATS_COMMITTED>(stats);
    else {
      ::add_to_stats<STATS_FAILURE, STATS_COMMITTED>(stats);
      ::report_trx_recovery_error(ER_BINLOG_CRASH_RECOVERY_COMMIT_FAILED, xid,
                                  ht, exec_status);
    }
  } else {
    enum xa_status_code exec_status;
    if (DBUG_EVALUATE_IF("xa_recovery_error_reporting", true, false))
      exec_status = ::generate_xa_recovery_error();
    else
      exec_status = ht.rollback_by_xid(&ht, const_cast<XID *>(&xa_trx.id));

    if (exec_status == XA_OK)
      ::add_to_stats<STATS_SUCCESS, STATS_ROLLEDBACK>(stats);
    else {
      ::add_to_stats<STATS_FAILURE, STATS_ROLLEDBACK>(stats);
      ::report_trx_recovery_error(ER_BINLOG_CRASH_RECOVERY_ROLLBACK_FAILED, xid,
                                  ht, exec_status);
    }
  }
}
```

InnoDB 쪽의 받는 자리다. PREPARED 목록, 커밋, 롤백.

`storage` / `innobase` / `handler` / `ha_innodb.cc` L20358-L20438 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/ha_innodb.cc#L20358-L20438))

```cpp
// ha_innodb.cc L20358-L20438
/** This function is used to recover X/Open XA distributed transactions.
 @return number of prepared transactions stored in xid_list */
static int innobase_xa_recover(
    handlerton *hton,         /*!< in: InnoDB handlerton */
    XA_recover_txn *txn_list, /*!< in/out: prepared transactions */
    uint len,                 /*!< in: number of slots in xid_list */
    MEM_ROOT *mem_root)       /*!< in: memory for table names */
{
  assert(hton == innodb_hton_ptr);

  if (len == 0 || txn_list == nullptr) {
    return (0);
  }

  return (trx_recover_for_mysql(txn_list, len, mem_root));
}
// ... (L20374-L20381 생략: XA 외부 트랜잭션용 recover_prepared_in_tc)
/** This function is used to commit one X/Open XA distributed transaction
 which is in the prepared state
 @return 0 or error number */
static xa_status_code innobase_commit_by_xid(
    handlerton *hton, XID *xid) /*!< in: X/Open XA transaction identification */
{
  assert(hton == innodb_hton_ptr);

  trx_t *trx = trx_get_trx_by_xid(xid);

  if (trx != nullptr) {
    {
      TrxInInnoDB trx_in_innodb(trx);

      innobase_commit_low(trx);
    }
    ut_ad(trx->mysql_thd == nullptr);
    /* use cases are: disconnected xa, slave xa, recovery */
    trx_deregister_from_2pc(trx);
    ut_ad(!trx->will_lock); /* trx cache requirement */
    trx_free_for_background(trx);

    return (XA_OK);
  } else {
    return (XAER_NOTA);
  }
}

/** This function is used to rollback one X/Open XA distributed transaction
 which is in the prepared state
 @return 0 or error number */
static xa_status_code innobase_rollback_by_xid(
    handlerton *hton, /*!< in: InnoDB handlerton */
    XID *xid)         /*!< in: X/Open XA transaction
                      identification */
{
  assert(hton == innodb_hton_ptr);

  trx_t *trx = trx_get_trx_by_xid(xid);

  if (trx != nullptr) {
    int ret;
    {
      TrxInInnoDB trx_in_innodb(trx);

      ret = innobase_rollback_trx(trx);
    }

    trx_deregister_from_2pc(trx);
    ut_ad(!trx->will_lock);
    trx_free_for_background(trx);

    return (ret != 0 ? XAER_RMERR : XA_OK);
  } else {
    return (XAER_NOTA);
  }
}
```

## 동작 흐름

```text
 open_binlog (binlog.cc L6881)
 L6953  read_binlog_in_use_flag 가 거짓 (정상 종료)
          ha_recover() 만 부르고 끝 (commit_list 없음)
 L6962  Binlog_recovery bl_recovery{reader}
 L6963  bl_recovery.recover()
          recovery.cc L54  process_logs(m_reader)          이벤트를 끝까지 읽는다
            Xid_log_event -> m_internal_xids.insert(xid)   (log_sanitizer.cc L108)
            XA PREPARE / COMMIT / ROLLBACK -> m_external_xids
            트랜잭션 경계마다 m_valid_pos 갱신           (log_sanitizer_impl.hpp L153-L158)
          recovery.cc L55  로그가 정상이고 2PC 엔진이 binlog 말고도 있으면
          recovery.cc L57  ha_recover(&m_internal_xids, &xa_list)
 L6965  valid_pos = 마지막 완결 트랜잭션 뒤
 L6968  로그가 깨졌으면 에러
 L6974  엔진 복구가 실패했으면 자르되 IN_USE 는 남긴다
 L6985  valid_pos > 0 이면 truncate_update_log_file(..., true)
          잘린 꼬리를 버리고 IN_USE 플래그를 지운다

 ha_recover (xa.cc L270)
   recover_one_ht (xa/recovery.cc L191)  엔진마다
     L200  ht->recover(...)              InnoDB: trx_recover_for_mysql, PREPARED 만 (trx0trx.cc L3190)
     L212  XID 가 0 이면 외부 XA         recover_one_external_trx
     L226  내부 2PC                      recover_one_internal_trx
       L245  commit_list 에 xid 가 있다  ht.commit_by_xid   -> innobase_commit_low
       L265  없다                        ht.rollback_by_xid -> innobase_rollback_trx
```

```text
 크래시 시점별 결과 (내부 2PC, binlog 켬)

 prepare 전에 크래시
   InnoDB ACTIVE, binlog 에 XID 없음           -> [12] 가 롤백
 InnoDB prepare 뒤, binlog 에 XID 가 쓰이기 전
   InnoDB PREPARED, XID 없음                   -> 여기서 rollback_by_xid
 binlog 에 XID 이벤트까지 파일에 남은 뒤, InnoDB commit 전
   InnoDB PREPARED, XID 있음                   -> 여기서 commit_by_xid (L245 -> L251)
   "XID 있음" 은 마지막 binlog 파일을 읽는 process_logs 가 그 Xid_log_event 에
   도달해 m_internal_xids 에 넣었다는 뜻이다 (log_sanitizer.cc L108)
   읽기가 그 이벤트 앞에서 멈췄다면 집합에 없으므로 위 줄(rollback_by_xid)과 같다
   로그가 malformed 이거나 binlog 말고 2PC 엔진이 없으면 ha_recover 자체를
   부르지 않는다 (binlog/recovery.cc L55)
 InnoDB commit 뒤
   InnoDB COMMITTED (undo 정리 전일 수 있음)   -> [12] 가 정리만

 commit_list 가 있을 때 판정의 근거는 "그 XID 가 집합에 있는가" 하나다 (xa/recovery.cc L245)
 commit_list 가 없으면(정상 종료 경로의 ha_recover()) tc_heuristic_recover 를 본다 (L246)
   xa.cc L275  commit_list 도 heuristic 도 없으면 dry_run -> 내부 트랜잭션은 건너뜀 (L218)
   xa.cc L311  단, 2PC 엔진이 binlog 말고 하나뿐이면 ROLLBACK 으로 강제하고 dry_run 을 끈다
```

## 결과가 쓰이는 곳

```text
 커밋된 PREPARED 트랜잭션
      --> innobase_commit_low 로 커밋, trx_free_for_background
      --> undo 는 history list 로 가서 [purge] 대상이 된다
 롤백된 PREPARED 트랜잭션
      --> innobase_rollback_trx 로 undo 적용
 외부 XA 로 PREPARED 에 남긴 것
      --> Recovered_xa_transactions 에 올라 XA RECOVER 로 보인다 (mysqld.cc L8866-L8867)
 잘린 binlog
      --> 마지막 완결 트랜잭션 뒤(valid_pos)에서 파일이 끝나고 IN_USE 플래그가 지워진다 (binlog.cc L6985-L6991)
```

## 다루지 않는 것

`--tc-heuristic-recover` 로 강제 커밋, 롤백하는 경로, binlog 없이 쓰는 `TC_LOG_MMAP`, 외부 XA 의 상태별 처리(`recover_one_external_trx`, `PREPARED_IN_TC`), 레플리카 relay log 정리에 같은 `Log_sanitizer` 를 쓰는 경로, GTID 상태 복원은 이 함수의 곁가지라 요약만 했다. 정상 운영 중의 2PC 는 [커밋과 binlog 2PC](../../commit-2pc/README.md)에 있다.
