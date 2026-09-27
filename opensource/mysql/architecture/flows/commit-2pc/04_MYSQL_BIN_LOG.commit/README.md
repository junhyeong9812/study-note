# MYSQL_BIN_LOG::commit

상위: [커밋과 binlog 2PC](../README.md)

**binlog 를 코디네이터로 쓸 때의 `tc_log->commit` 이다.** 세션의 binlog 캐시를 마감(finalize)해서 트랜잭션 끝 이벤트를 붙이고, 그룹 커밋 [05] `ordered_commit` 에 들어간다. 끝 이벤트의 종류가 2PC 여부를 말해 준다. 엔진이 둘 이상 쓰기에 참여했으면 `Xid_log_event` 가 붙고, 이 XID 가 크래시 복구 때 PREPARED 트랜잭션을 커밋할지 가르는 증거가 된다. 머리 주석이 세 부분 구조(캐시 마감 -> ordered_commit -> 오류 처리)를 적어 두었다.

## 위치

`sql` / `binlog.cc` L7107-L7377 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/binlog.cc#L7107-L7377))

## 실제 코드

XID 를 꺼내고 캐시 관리자를 얻는다. 캐시가 없으면 로그할 것이 없으니 엔진 커밋만 한다.

`sql` / `binlog.cc` L7107-L7150 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/binlog.cc#L7107-L7150))

```cpp
// binlog.cc L7107-L7150
TC_LOG::enum_result MYSQL_BIN_LOG::commit(THD *thd, bool all) {
  DBUG_TRACE;
  DBUG_PRINT("info",
             ("query='%s'", thd == current_thd ? thd->query().str : nullptr));
  Transaction_ctx *trn_ctx = thd->get_transaction();
  my_xid xid = trn_ctx->xid_state()->get_xid()->get_my_xid();
  bool stmt_stuff_logged = false;
  bool trx_stuff_logged = false;
  bool skip_commit = is_loggable_xa_prepare(thd);
  bool is_atomic_ddl = false;
  auto xs = thd->get_transaction()->xid_state();
  raii::Sentry<> reset_detached_guard{[&]() -> void {
    // XID_STATE may have been used to hold metadata for a detached transaction.
    // In that case, we need to reset it.
    if (xs->is_detached()) xs->reset();
  }};

  if (thd->lex->sql_command ==
      SQLCOM_XA_COMMIT) {  // XA commit must be written to the binary log prior
                           // to retrieving cache manager
    DBUG_EXECUTE_IF("simulate_xa_commit_log_abort", { return RESULT_ABORTED; });
    if (this->write_xa_to_cache(thd)) return RESULT_ABORTED;
  }

  binlog_cache_mngr *cache_mngr = thd_get_cache_mngr(thd);
  DBUG_PRINT("enter", ("thd: 0x%llx, all: %s, xid: %llu, cache_mngr: 0x%llx",
                       (ulonglong)thd, YESNO(all), (ulonglong)xid,
                       (ulonglong)cache_mngr));

  Scope_guard guard_applier_wait_enabled(
      [&thd]() { thd->disable_low_level_commit_ordering(); });

  if (is_current_stmt_binlog_enabled_and_caches_empty(thd)) {
    thd->enable_low_level_commit_ordering();
  }
  /*
    No cache manager means nothing to log, but we still have to commit
    the transaction.
   */
  if (cache_mngr == nullptr) {
    if (!skip_commit && trx_coordinator::commit_in_engines(thd, all))
      return RESULT_ABORTED;
    return RESULT_SUCCESS;
  }
```

문장 캐시(비트랜잭션 테이블 변경)를 먼저 마감한다.

`sql` / `binlog.cc` L7182-L7195 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/binlog.cc#L7182-L7195))

```cpp
// binlog.cc L7182-L7195
  if (!all && !trn_ctx->is_active(trx_scope) &&
      cache_mngr->stmt_cache.is_binlog_empty())
    return RESULT_SUCCESS;

  if (!cache_mngr->stmt_cache.is_binlog_empty()) {
    /*
      Commit parent identification of non-transactional query has
      been deferred until now, except for the mixed transaction case.
    */
    trn_ctx->store_commit_parent(
        m_dependency_tracker.get_max_committed_timestamp());
    if (cache_mngr->stmt_cache.finalize(thd)) return RESULT_ABORTED;
    stmt_stuff_logged = true;
  }
```

트랜잭션이 끝나는 커밋이면 트랜잭션 캐시에 끝 이벤트를 붙여 마감한다.

`sql` / `binlog.cc` L7199-L7208 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/binlog.cc#L7199-L7208))

```cpp
// binlog.cc L7199-L7208
  /*
    We commit the transaction if:
     - We are not in a transaction and committing a statement, or
     - We are in a transaction and a full transaction is committed.
    Otherwise, we accumulate the changes.
  */
  if (!cache_mngr->trx_cache.is_binlog_empty() && ending_trans(thd, all) &&
      !trx_stuff_logged) {
    const bool real_trans =
        (all || !trn_ctx->is_active(Transaction_ctx::SESSION));
```

`sql` / `binlog.cc` L7254-L7287 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/binlog.cc#L7254-L7287))

```cpp
// binlog.cc L7254-L7287
    */
    else if ((is_atomic_ddl = cache_mngr->trx_cache.has_xid())) {
      if (cache_mngr->trx_cache.finalize(thd, nullptr)) return RESULT_ABORTED;
    }
    /*
      We are committing a 2PC transaction if it is a "real" transaction
      and has an XID assigned (because some handlerton registered). A
      transaction is "real" if either 'all' is true or
      'trn_ctx->is_active(Transaction_ctx::SESSION)' is not true.

      Note: This is kind of strange since registering the binlog
      handlerton will then make the transaction 2PC, which is not really
      true. This occurs for example if a MyISAM statement is executed
      with row-based replication on.
    */
    else if (real_trans && xid && trn_ctx->rw_ha_count(trx_scope) > 1 &&
             !trn_ctx->no_2pc(trx_scope)) {
      Xid_log_event end_evt(thd, xid);
      if (cache_mngr->trx_cache.finalize(thd, &end_evt)) return RESULT_ABORTED;
    }
    /*
      No further action needed and no special case applies, log a final
      'COMMIT' statement and finalize the transaction cache.

      Empty transactions finalized with 'XA COMMIT ONE PHASE' will be covered
      by this branch.
     */
    else {
      Query_log_event end_evt(thd, STRING_WITH_LEN("COMMIT"), true, false, true,
                              0, true);
      if (cache_mngr->trx_cache.finalize(thd, &end_evt)) return RESULT_ABORTED;
    }
    trx_stuff_logged = true;
  }
```

캐시에 뭔가 썼으면 `before_commit` 훅(그룹 복제 등)을 거쳐 그룹 커밋에 들어간다.

`sql` / `binlog.cc` L7344-L7351 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/binlog.cc#L7344-L7351))

```cpp
// binlog.cc L7344-L7351

    if (DBUG_EVALUATE_IF("simulate_xa_commit_log_inconsistency", true, false) ||
        ordered_commit(thd, all, skip_commit)) {
      thd_get_cache_mngr(thd)->reset();
      if (thd->get_stmt_da()->is_ok())
        thd->get_stmt_da()->reset_diagnostics_area();
      return RESULT_INCONSISTENT;
    }
```

`sql` / `binlog.cc` L7371-L7377 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/binlog.cc#L7371-L7377))

```cpp
// binlog.cc L7371-L7377
  } else if (!skip_commit) {
    if (trx_coordinator::commit_in_engines(thd, all))
      return RESULT_INCONSISTENT;
  }

  return RESULT_SUCCESS;
}
```

## 동작 흐름

```text
 L7112  xid = xid_state 의 my_xid
 L7115  skip_commit = is_loggable_xa_prepare      XA PREPARE 면 엔진 커밋을 하지 않는다
 L7124  XA COMMIT 이면 XA 이벤트를 먼저 캐시에
 L7131  cache_mngr = thd_get_cache_mngr(thd)
 L7139  캐시가 비어 있으면 low level commit ordering 을 켠다
 L7146  cache_mngr 가 없으면 commit_in_engines 만 하고 끝

 L7182  문장 커밋이고 STMT 가 비활성이고 문장 캐시가 비었으면 return (할 일 없음)
 L7186  문장 캐시에 뭔가 있으면 L7193 stmt_cache.finalize, stmt_stuff_logged = true

 L7205  트랜잭션 캐시가 비어 있지 않고 ending_trans(thd, all) 이면
          끝 이벤트 고르기 (아래 표)
 L7286    trx_stuff_logged = true
 L7292  문장 커밋이면 trx_cache 의 savepoint 위치 초기화

 L7304  stmt_stuff_logged || trx_stuff_logged
 L7306    RUN_HOOK(transaction, before_commit)     실패면 엔진 롤백, RESULT_ABORTED
 L7329    플러그인이 롤백을 요청했으면 롤백, RESULT_ABORTED
 L7346    [05] ordered_commit(thd, all, skip_commit)
 L7350      실패면 RESULT_INCONSISTENT           binlog 에는 썼는데 엔진 커밋이 안 됐을 수 있다
 L7371  캐시에 아무것도 안 썼으면 commit_in_engines 만
 L7376  RESULT_SUCCESS
```

트랜잭션 캐시를 마감할 때 붙는 끝 이벤트는 네 가지 중 하나다. 이 선택이 binlog 안에서 "이 트랜잭션이 2PC 였다"는 기록이다.

```text
 끝 이벤트의 선택 (L7205-L7287)

 L 줄    끝 이벤트                    조건
 L7241   XA_prepare_log_event         XA PREPARE, 또는 아직 기록 안 된 XA COMMIT ONE PHASE
 L7255   (none, finalize(nullptr))    원자적 DDL (trx_cache.has_xid())
 L7271   Xid_log_event(thd, xid)      real_trans && xid && rw_ha_count > 1 && 2PC 가능
 L7282   Query_log_event("COMMIT")    그 밖 (비트랜잭션 엔진만, 빈 XA 등)

 트랜잭션 캐시의 모양 (InnoDB 트랜잭션, 마감 직후)

   | 문장마다 쌓인 이벤트들 ...                 | Xid_log_event(xid) |
   <-- 각 문장의 binlog 기록이 쌓아 둔 부분 -->   <-- L7272 에서 붙는다 -->
```

```text
 반환값 (TC_LOG::enum_result, 머리 주석 L7103-L7105)

 RESULT_SUCCESS       로그도 엔진 커밋도 성공
 RESULT_ABORTED       로그도 커밋도 안 됨 (캐시 마감 실패, before_commit 훅 거부)
 RESULT_INCONSISTENT  로그는 됐는데 엔진 커밋 실패 (L7350)
                      L7373 은 로그할 것이 없던 경우의 commit_in_engines 실패에도 이 값을 돌려준다
 [02] ha_commit_trans 는 0 이 아니면 모두 롤백을 시도하고 1 을 돌려준다
```

## 결과가 쓰이는 곳

```text
 마감된 trx_cache (끝 이벤트 포함)
      --> [06] flush_thread_caches 가 binlog 파일 버퍼로 옮긴다
      --> Xid_log_event 를 썼으면 wrote_xid 가 켜져 inc_prep_xids (binlog.cc L7407)
 ordered_commit 의 반환
      --> RESULT_INCONSISTENT 로 바뀌어 [02] 로
```

## 다루지 않는 것

XA 트랜잭션의 두 단계 로깅(`write_xa_to_cache`, `XA_prepare_log_event`), 원자적 DDL 의 XID, 비트랜잭션 테이블의 문장 캐시, commit parent 와 의존성 추적(`store_commit_parent`, 병렬 복제), `before_commit` 훅(그룹 복제의 인증), low level commit ordering 은 이 흐름의 곁가지라 줄만 적었다.
