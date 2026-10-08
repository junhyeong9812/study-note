# CommitTransaction

상위: [커밋](../README.md)

**최상위 트랜잭션을 커밋한다.** 앞 절반은 사용자 코드(지연 트리거, 커서 닫기, 콜백)를 돌리는 pre-commit 이라 여기서 ERROR 가 나면 아직 abort 로 돌아갈 수 있다. `s->state = TRANS_COMMIT` 이후 [06] `RecordTransactionCommit` 이 WAL 과 pg_xact 에 커밋을 남기면 그때부터는 되돌릴 수 없고, 나머지는 [10] ProcArray 이탈 → 잠금 해제 → backend 지역 정리 순서의 뒷정리다. 순서는 주석이 정한다. ProcArray 이탈은 "RecordTransactionCommit 뒤, 잠금 해제 앞"이어야 하고(L2384-L2387), 정리는 "남에게 보이는 자원 → 잠금 → 지역 자원" 순이다(L2396-L2401).

## 위치

`access` / `transam` / `xact.c` L2227-L2506 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xact.c#L2227-L2506))

## 실제 코드

`access` / `transam` / `xact.c` L2227-L2506 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xact.c#L2227-L2506))

```c
// xact.c L2227-L2506
static void
CommitTransaction(void)
{
	TransactionState s = CurrentTransactionState;
	TransactionId latestXid;
	bool		is_parallel_worker;

	is_parallel_worker = (s->blockState == TBLOCK_PARALLEL_INPROGRESS);

	/* Enforce parallel mode restrictions during parallel worker commit. */
	if (is_parallel_worker)
		EnterParallelMode();

	ShowTransactionState("CommitTransaction");

	/*
	 * check the current transaction state
	 */
	if (s->state != TRANS_INPROGRESS)
		elog(WARNING, "CommitTransaction while in %s state",
			 TransStateAsString(s->state));
	Assert(s->parent == NULL);

	/*
	 * Do pre-commit processing that involves calling user-defined code, such
	 * as triggers.  SECURITY_RESTRICTED_OPERATION contexts must not queue an
	 * action that would run here, because that would bypass the sandbox.
	 * Since closing cursors could queue trigger actions, triggers could open
	 * cursors, etc, we have to keep looping until there's nothing left to do.
	 */
	for (;;)
	{
		/*
		 * Fire all currently pending deferred triggers.
		 */
		AfterTriggerFireDeferred();

		/*
		 * Close open portals (converting holdable ones into static portals).
		 * If there weren't any, we are done ... otherwise loop back to check
		 * if they queued deferred triggers.  Lather, rinse, repeat.
		 */
		if (!PreCommit_Portals(false))
			break;
	}

	/*
	 * The remaining actions cannot call any user-defined code, so it's safe
	 * to start shutting down within-transaction services.  But note that most
	 * of this stuff could still throw an error, which would switch us into
	 * the transaction-abort path.
	 */

	CallXactCallbacks(is_parallel_worker ? XACT_EVENT_PARALLEL_PRE_COMMIT
					  : XACT_EVENT_PRE_COMMIT);

	// ... (L2283-L2302 생략: 병렬 worker 정리와 parallelModeLevel 검사)

	/* Shut down the deferred-trigger manager */
	AfterTriggerEndXact(true);

	/*
	 * Let ON COMMIT management do its thing (must happen after closing
	 * cursors, to avoid dangling-reference problems)
	 */
	PreCommit_on_commit_actions();

	/*
	 * Synchronize files that are created and not WAL-logged during this
	 * transaction. This must happen before AtEOXact_RelationMap(), so that we
	 * don't see committed-but-broken files after a crash.
	 */
	smgrDoPendingSyncs(true, is_parallel_worker);

	/* close large objects before lower-level cleanup */
	AtEOXact_LargeObject(true);

	/*
	 * Insert notifications sent by NOTIFY commands into the queue.  This
	 * should be late in the pre-commit sequence to minimize time spent
	 * holding the notify-insertion lock.  However, this could result in
	 * creating a snapshot, so we must do it before serializable cleanup.
	 */
	PreCommit_Notify();

	/*
	 * Mark serializable transaction as complete for predicate locking
	 * purposes.  This should be done as late as we can put it and still allow
	 * errors to be raised for failure patterns found at commit.  This is not
	 * appropriate in a parallel worker however, because we aren't committing
	 * the leader's transaction and its serializable state will live on.
	 */
	if (!is_parallel_worker)
		PreCommit_CheckForSerializationFailure();

	/* Prevent cancel/die interrupt while cleaning up */
	HOLD_INTERRUPTS();

	/* Commit updates to the relation map --- do this as late as possible */
	AtEOXact_RelationMap(true, is_parallel_worker);

	/*
	 * set the current transaction state information appropriately during
	 * commit processing
	 */
	s->state = TRANS_COMMIT;
	s->parallelModeLevel = 0;
	s->parallelChildXact = false;	/* should be false already */

	/* Disable transaction timeout */
	if (TransactionTimeout > 0)
		disable_timeout(TRANSACTION_TIMEOUT, false);

	if (!is_parallel_worker)
	{
		/*
		 * We need to mark our XIDs as committed in pg_xact.  This is where we
		 * durably commit.
		 */
		latestXid = RecordTransactionCommit();
	}
	else
	{
		/*
		 * We must not mark our XID committed; the parallel leader is
		 * responsible for that.
		 */
		latestXid = InvalidTransactionId;

		/*
		 * Make sure the leader will know about any WAL we wrote before it
		 * commits.
		 */
		ParallelWorkerReportLastRecEnd(XactLastRecEnd);
	}

	TRACE_POSTGRESQL_TRANSACTION_COMMIT(MyProc->vxid.lxid);

	/*
	 * Let others know about no transaction in progress by me. Note that this
	 * must be done _before_ releasing locks we hold and _after_
	 * RecordTransactionCommit.
	 */
	ProcArrayEndTransaction(MyProc, latestXid);

	/*
	 * This is all post-commit cleanup.  Note that if an error is raised here,
	 * it's too late to abort the transaction.  This should be just
	 * noncritical resource releasing.
	 *
	 * The ordering of operations is not entirely random.  The idea is:
	 * release resources visible to other backends (eg, files, buffer pins);
	 * then release locks; then release backend-local resources. We want to
	 * release locks at the point where any backend waiting for us will see
	 * our transaction as being fully cleaned up.
	 *
	 * Resources that can be associated with individual queries are handled by
	 * the ResourceOwner mechanism.  The other calls here are for backend-wide
	 * state.
	 */

	CallXactCallbacks(is_parallel_worker ? XACT_EVENT_PARALLEL_COMMIT
					  : XACT_EVENT_COMMIT);

	CurrentResourceOwner = NULL;
	ResourceOwnerRelease(TopTransactionResourceOwner,
						 RESOURCE_RELEASE_BEFORE_LOCKS,
						 true, true);

	AtEOXact_Aio(true);

	/* Check we've released all buffer pins */
	AtEOXact_Buffers(true);

	/* Clean up the relation cache */
	AtEOXact_RelationCache(true);

	/* Clean up the type cache */
	AtEOXact_TypeCache();

	/*
	 * Make catalog changes visible to all backends.  This has to happen after
	 * relcache references are dropped (see comments for
	 * AtEOXact_RelationCache), but before locks are released (if anyone is
	 * waiting for lock on a relation we've modified, we want them to know
	 * about the catalog change before they start using the relation).
	 */
	AtEOXact_Inval(true);

	AtEOXact_MultiXact();

	ResourceOwnerRelease(TopTransactionResourceOwner,
						 RESOURCE_RELEASE_LOCKS,
						 true, true);
	ResourceOwnerRelease(TopTransactionResourceOwner,
						 RESOURCE_RELEASE_AFTER_LOCKS,
						 true, true);

	/*
	 * Likewise, dropping of files deleted during the transaction is best done
	 * after releasing relcache and buffer pins.  (This is not strictly
	 * necessary during commit, since such pins should have been released
	 * already, but this ordering is definitely critical during abort.)  Since
	 * this may take many seconds, also delay until after releasing locks.
	 * Other backends will observe the attendant catalog changes and not
	 * attempt to access affected files.
	 */
	smgrDoPendingDeletes(true);

	/*
	 * Send out notification signals to other backends (and do other
	 * post-commit NOTIFY cleanup).  This must not happen until after our
	 * transaction is fully done from the viewpoint of other backends.
	 */
	AtCommit_Notify();

	/*
	 * Everything after this should be purely internal-to-this-backend
	 * cleanup.
	 */
	// ... (L2466-L2497 생략: backend 지역 정리 (GUC, SPI, 스냅샷, 메모리 문맥, 상태 필드 초기화))

	/*
	 * done with commit processing, set current transaction state back to
	 * default
	 */
	s->state = TRANS_DEFAULT;

	RESUME_INTERRUPTS();
}
```

## 동작 흐름

pre-commit 과 commit 사이의 경계가 이 함수에서 가장 중요한 선이다. 그 위에서 난 ERROR 는 트랜잭션을 abort 시키고, 그 아래는 critical section 이거나 "이미 늦은" 정리다(L2392-L2394 주석).

```text
 CommitTransaction
 --------------------------------------------------- pre-commit (ERROR 면 abort 가능)
 L2257  for (;;)  AfterTriggerFireDeferred, PreCommit_Portals    트리거가 커서를, 커서가 트리거를 낳을 수 있어 반복
 L2280  CallXactCallbacks(PRE_COMMIT)                              확장(FDW 등)의 커밋 준비
 L2305  AfterTriggerEndXact
 L2311  PreCommit_on_commit_actions                                ON COMMIT DROP / DELETE ROWS
 L2318  smgrDoPendingSyncs                                         WAL 을 건너뛴 새 파일을 fsync
 L2329  PreCommit_Notify                                           NOTIFY 를 큐에 넣는다
 L2339  PreCommit_CheckForSerializationFailure                     SSI 직렬화 실패 검사
 L2342  HOLD_INTERRUPTS
 L2345  AtEOXact_RelationMap
 --------------------------------------------------- commit
 L2351  s->state = TRANS_COMMIT
 L2365  latestXid = [06] RecordTransactionCommit()                 WAL, flush, pg_xact, SyncRep
 L2389  [10] ProcArrayEndTransaction(MyProc, latestXid)            남의 새 스냅샷에서 커밋됨
 --------------------------------------------------- post-commit (ERROR 여도 이미 커밋)
 L2407  CallXactCallbacks(COMMIT)
 L2411  ResourceOwnerRelease(BEFORE_LOCKS)                         버퍼 핀, relcache 참조
 L2418  AtEOXact_Buffers                                           핀이 다 풀렸는지 검사
 L2433  AtEOXact_Inval                                             카탈로그 변경 무효화를 모두에게 보낸다
 L2437  ResourceOwnerRelease(LOCKS)                                -> ProcReleaseLocks -> LockReleaseAll
 L2440  ResourceOwnerRelease(AFTER_LOCKS)
 L2453  smgrDoPendingDeletes                                       DROP 한 파일을 지운다
 L2460  AtCommit_Notify                                            LISTEN 하는 backend 를 깨운다
 L2466-L2486  GUC, 스냅샷, 메모리 문맥 정리
 L2503  s->state = TRANS_DEFAULT
 L2505  RESUME_INTERRUPTS
```

ProcArray 이탈을 잠금 해제보다 먼저 하는 이유는 transam README 의 예(L231-L239)로 그릴 수 있다. B 가 커밋 중이고, A 는 B 가 고친 행을 고치려고 B 의 XID 잠금을 기다리고, C 가 그 사이에 스냅샷을 잡는다.

```text
 지금 순서 (ProcArray 이탈 -> 잠금 해제)
   B: L2389 ProcArray 에서 빠짐
   B: L2437 잠금 해제  ->  A 가 깨어나 행을 고치고 커밋
   C: 스냅샷  -> B 가 끝났으면 A 보다 먼저 끝났다. "B 진행 중, A 커밋"은 나올 수 없다

 순서를 뒤집으면 (잠금 해제 -> ProcArray 이탈)
   B: 잠금 해제  ->  A 가 깨어나 행을 고치고 커밋, A 는 ProcArray 에서 빠짐
   C: 스냅샷  -> B 는 아직 ProcArray 에 있다  ->  B 진행 중, A 커밋
      C 는 B 가 지운 옛 행 (B 미커밋으로 보임) 과 A 가 넣은 새 행을 둘 다 본다
   B: ProcArray 에서 빠짐
```

## 결과가 쓰이는 곳

```text
 latestXid
      --> [10] 이 latestCompletedXid 를 올리는 데 쓴다
 잠금 해제 (L2437)
      --> heavyweight lock 흐름의 [11] LockReleaseAll 이 대기자를 깨운다
          ([heavyweight lock 11](../../heavyweight-lock/11_LockReleaseAll/README.md))
 AtEOXact_Inval
      --> 다른 backend 의 relcache, catcache 가 다음 AcceptInvalidationMessages 에서 맞춰진다
 s->state = TRANS_DEFAULT, blockState 는 호출자가 TBLOCK_DEFAULT 로
      --> 다음 문장이 새 트랜잭션을 연다
```

## 다루지 않는 것

병렬 worker 의 커밋(`is_parallel_worker` 갈래, 리더가 대신 XID 를 기록), `PrepareTransaction`, 지연 트리거·포털·ON COMMIT 처리의 내부, 무효화 메시지 전달(`AtEOXact_Inval`)과 NOTIFY 큐의 내부는 다루지 않았다.
