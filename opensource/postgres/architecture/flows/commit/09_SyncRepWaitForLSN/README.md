# SyncRepWaitForLSN

상위: [커밋](../README.md)

**동기 복제일 때 standby 가 commit 레코드를 받았다고 알려올 때까지 잠든다.** 동기 복제를 쓰지 않으면 첫 검사에서 바로 돌아간다. 쓰면 `SyncRepLock` 아래에서 자기 PGPROC 를 LSN 순으로 정렬된 대기 큐에 넣고 latch 위에서 기다린다. 깨우는 쪽은 walsender 다. standby 의 응답을 받은 walsender 가 확인된 LSN 까지의 대기자를 큐에서 빼고 `SYNC_REP_WAIT_COMPLETE` 로 바꾼 뒤 latch 를 세운다. 이 동안 트랜잭션은 이미 로컬에서 커밋됐으므로(pg_xact COMMITTED) 취소 요청이 와도 abort 할 수 없고 WARNING 만 낸 채 대기를 끝낸다(L288-L299, L311-L316 주석). ProcArray 와 잠금은 그때까지 아직 쥐고 있다.

## 위치

`replication` / `syncrep.c` L147-L363 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/syncrep.c#L147-L363))

## 실제 코드

`replication` / `syncrep.c` L147-L363 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/syncrep.c#L147-L363))

```c
// syncrep.c L147-L363
void
SyncRepWaitForLSN(XLogRecPtr lsn, bool commit)
{
	int			mode;

	/*
	 * This should be called while holding interrupts during a transaction
	 * commit to prevent the follow-up shared memory queue cleanups to be
	 * influenced by external interruptions.
	 */
	Assert(InterruptHoldoffCount > 0);

	// ... (L159-L177 생략: 빠른 탈출 조건의 설명)
	if (!SyncRepRequested() ||
		((((volatile WalSndCtlData *) WalSndCtl)->sync_standbys_status) &
		 (SYNC_STANDBY_INIT | SYNC_STANDBY_DEFINED)) == SYNC_STANDBY_INIT)
		return;

	/* Cap the level for anything other than commit to remote flush only. */
	if (commit)
		mode = SyncRepWaitMode;
	else
		mode = Min(SyncRepWaitMode, SYNC_REP_WAIT_FLUSH);

	Assert(dlist_node_is_detached(&MyProc->syncRepLinks));
	Assert(WalSndCtl != NULL);

	LWLockAcquire(SyncRepLock, LW_EXCLUSIVE);
	Assert(MyProc->syncRepState == SYNC_REP_NOT_WAITING);

	// ... (L195-L206 생략: 대기 여부를 잠금 아래에서 다시 보는 이유)
	if (WalSndCtl->sync_standbys_status & SYNC_STANDBY_INIT)
	{
		if ((WalSndCtl->sync_standbys_status & SYNC_STANDBY_DEFINED) == 0 ||
			lsn <= WalSndCtl->lsn[mode])
		{
			LWLockRelease(SyncRepLock);
			return;
		}
	}
	// ... (L216-L244 생략: standby 상태가 아직 초기화 전일 때의 대체 검사)

	/*
	 * Set our waitLSN so WALSender will know when to wake us, and add
	 * ourselves to the queue.
	 */
	MyProc->waitLSN = lsn;
	MyProc->syncRepState = SYNC_REP_WAITING;
	SyncRepQueueInsert(mode);
	Assert(SyncRepQueueIsOrderedByLSN(mode));
	LWLockRelease(SyncRepLock);

	// ... (L256-L263 생략: ps 표시에 대기 LSN 을 붙인다)

	/*
	 * Wait for specified LSN to be confirmed.
	 *
	 * Each proc has its own wait latch, so we perform a normal latch
	 * check/wait loop here.
	 */
	for (;;)
	{
		int			rc;

		/* Must reset the latch before testing state. */
		ResetLatch(MyLatch);

		// ... (L278-L284 생략: 잠금 없이 상태를 읽어도 되는 이유)
		if (MyProc->syncRepState == SYNC_REP_WAIT_COMPLETE)
			break;

		// ... (L288-L299 생략: 대기 중 종료 요청을 WARNING 으로만 처리하는 이유)
		if (ProcDiePending)
		{
			ereport(WARNING,
					(errcode(ERRCODE_ADMIN_SHUTDOWN),
					 errmsg("canceling the wait for synchronous replication and terminating connection due to administrator command"),
					 errdetail("The transaction has already committed locally, but might not have been replicated to the standby.")));
			whereToSendOutput = DestNone;
			SyncRepCancelWait();
			break;
		}

		/*
		 * It's unclear what to do if a query cancel interrupt arrives.  We
		 * can't actually abort at this point, but ignoring the interrupt
		 * altogether is not helpful, so we just terminate the wait with a
		 * suitable warning.
		 */
		if (QueryCancelPending)
		{
			QueryCancelPending = false;
			ereport(WARNING,
					(errmsg("canceling wait for synchronous replication due to user request"),
					 errdetail("The transaction has already committed locally, but might not have been replicated to the standby.")));
			SyncRepCancelWait();
			break;
		}

		/*
		 * Wait on latch.  Any condition that should wake us up will set the
		 * latch, so no need for timeout.
		 */
		rc = WaitLatch(MyLatch, WL_LATCH_SET | WL_POSTMASTER_DEATH, -1,
					   WAIT_EVENT_SYNC_REP);

		/*
		 * If the postmaster dies, we'll probably never get an acknowledgment,
		 * because all the wal sender processes will exit. So just bail out.
		 */
		if (rc & WL_POSTMASTER_DEATH)
		{
			ProcDiePending = true;
			whereToSendOutput = DestNone;
			SyncRepCancelWait();
			break;
		}
	}

	/*
	 * WalSender has checked our LSN and has removed us from queue. Clean up
	 * state and leave.  It's OK to reset these shared memory fields without
	 * holding SyncRepLock, because any walsenders will ignore us anyway when
	 * we're not on the queue.  We need a read barrier to make sure we see the
	 * changes to the queue link (this might be unnecessary without
	 * assertions, but better safe than sorry).
	 */
	pg_read_barrier();
	Assert(dlist_node_is_detached(&MyProc->syncRepLinks));
	MyProc->syncRepState = SYNC_REP_NOT_WAITING;
	MyProc->waitLSN = 0;

	/* reset ps display to remove the suffix */
	if (update_process_title)
		set_ps_display_remove_suffix();
}
```

## 동작 흐름

```text
 SyncRepWaitForLSN(XactLastRecEnd, commit = true)
 L178  SyncRepRequested() 가 false 거나 sync standby 가 정의되지 않았으면 return
         SyncRepRequested = max_wal_senders > 0 && synchronous_commit > local   (syncrep.h L18-L19)
 L185  mode = SyncRepWaitMode                  WAIT_WRITE(0) / WAIT_FLUSH(1) / WAIT_APPLY(2)
 L192  LWLockAcquire(SyncRepLock)
 L209  standby 가 이미 lsn 이상을 확인했으면 (lsn <= WalSndCtl->lsn[mode]) return
 L250  MyProc->waitLSN = lsn
 L251  syncRepState = SYNC_REP_WAITING
 L252  SyncRepQueueInsert(mode)                 waitLSN 오름차순 자리
 L254  LWLockRelease(SyncRepLock)
 L271  for (;;)
         L276  ResetLatch
         L285  SYNC_REP_WAIT_COMPLETE 면 break
         L300  ProcDiePending  -> WARNING, 출력 끄고, 큐에서 빠지고 break
         L317  QueryCancelPending -> WARNING, 큐에서 빠지고 break
         L331  WaitLatch (타임아웃 없음)
 L357  syncRepState = SYNC_REP_NOT_WAITING, waitLSN = 0
```

대기 큐는 mode 마다 하나이고 LSN 순으로 정렬되어 있어서, walsender 는 앞에서부터 확인된 LSN 이하인 것만 빼면 된다(`SyncRepWakeQueue`, syncrep.c L907). 세 backend 가 거의 동시에 커밋하고 standby 가 중간 LSN 까지 flush 를 알려온 경우다.

```text
 SyncRepQueue[WAIT_FLUSH]  (waitLSN 오름차순)

 before   [B1 0/3000060] -> [B2 0/3000120] -> [B3 0/30001E0]
          WalSndCtl->lsn[WAIT_FLUSH] = 0/3000000

 standby reply: flush = 0/3000150
   walsender ProcessStandbyReplyMessage (walsender.c L2445)
     -> SyncRepReleaseWaiters (syncrep.c L474)
          lsn[WAIT_FLUSH] = 0/3000150
          SyncRepWakeQueue(false, WAIT_FLUSH)
            B1  0/3000060 <= 0/3000150  큐에서 빼고 WAIT_COMPLETE, SetLatch
            B2  0/3000120 <= 0/3000150  큐에서 빼고 WAIT_COMPLETE, SetLatch
            B3  0/30001E0 >  0/3000150  멈춘다 (뒤는 모두 더 크다)

 after    [B3 0/30001E0]
          B1, B2 는 L285 에서 break -> [10] ProcArrayEndTransaction -> 클라이언트에 COMMIT 응답
```

대기 중에 연결을 끊거나 취소하면 무엇이 남는지가 이 함수의 가장 미묘한 점이다(L288-L299 주석).

```text
 event during wait       action                                  결과
 QueryCancelPending      WARNING, SyncRepCancelWait, break       로컬 커밋은 유지. 클라이언트는 COMMIT 성공을 받는다
 ProcDiePending          WARNING, whereToSendOutput = DestNone   로컬 커밋은 유지. 응답 없이 연결이 끝난다
 postmaster death        ProcDiePending = true, DestNone         위와 같다

 어느 경우든 ERROR 는 내지 않는다 - 이미 커밋된 트랜잭션을 abort 로 보이게 할 수 없다
```

## 결과가 쓰이는 곳

```text
 return (대기 끝)
      --> [06] 이 XactLastCommitEnd 를 적고 돌아가 [05] 가 [10] ProcArrayEndTransaction 으로 간다
      --> 그 뒤에야 잠금이 풀리고 COMMIT 응답이 나간다
 MyProc->waitLSN, syncRepLinks
      --> walsender 의 SyncRepWakeQueue 가 읽는다
      --> pg_stat_activity 의 wait_event = SyncRep
```

## 다루지 않는 것

어느 standby 가 동기 standby 인지 고르는 규칙(`synchronous_standby_names` 의 FIRST/ANY, `SyncRepGetSyncRecPtr`), checkpointer 가 `sync_standbys_status` 를 갱신하는 과정, walsender 쪽 응답 처리 전체는 [스트리밍 복제](../../streaming-replication/README.md) 흐름의 몫이다(대기자를 깨우는 쪽은 [12 SyncRepReleaseWaiters](../../streaming-replication/12_SyncRepReleaseWaiters/README.md)).
