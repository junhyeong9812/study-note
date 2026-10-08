# SyncRepReleaseWaiters

상위: [스트리밍 복제](../README.md)

**동기 standby 들의 보고를 모아 "모두가(또는 정족수가) 여기까지 왔다"는 write, flush, apply 세 위치를 구하고, 그 위치 이하를 기다리던 backend 를 큐에서 꺼내 깨우는 함수다.** 커밋하는 backend 쪽 짝은 `SyncRepWaitForLSN` 이다. 커밋 레코드 끝 LSN 을 `synchronous_commit` 이 고른 큐(write, flush, apply 중 하나)에 넣고 latch 에서 잔다. syncrep.c 머리 주석대로 대기와 해제의 판단은 전부 primary 에 있고, standby 는 자기 위치만 보고할 뿐 누가 기다리는지 모른다.

## 위치

`replication` / `syncrep.c` L474-L573 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/syncrep.c#L474-L573))

## 실제 코드

`synchronous_commit` 값이 기다릴 큐를 고른다. `local` 과 `off` 는 기다리지 않는다.

`replication` / `syncrep.c` L1124-L1141 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/syncrep.c#L1124-L1141))

```c
// replication/syncrep.c L1124-L1141
assign_synchronous_commit(int newval, void *extra)
{
	switch (newval)
	{
		case SYNCHRONOUS_COMMIT_REMOTE_WRITE:
			SyncRepWaitMode = SYNC_REP_WAIT_WRITE;
			break;
		case SYNCHRONOUS_COMMIT_REMOTE_FLUSH:
			SyncRepWaitMode = SYNC_REP_WAIT_FLUSH;
			break;
		case SYNCHRONOUS_COMMIT_REMOTE_APPLY:
			SyncRepWaitMode = SYNC_REP_WAIT_APPLY;
			break;
		default:
			SyncRepWaitMode = SYNC_REP_NO_WAIT;
			break;
	}
}
```

`src/include/replication` / `syncrep.h` L18-L25 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/replication/syncrep.h#L18-L25))

```c
// src/include/replication/syncrep.h L18-L25
#define SyncRepRequested() \
	(max_wal_senders > 0 && synchronous_commit > SYNCHRONOUS_COMMIT_LOCAL_FLUSH)

/* SyncRepWaitMode */
#define SYNC_REP_NO_WAIT		(-1)
#define SYNC_REP_WAIT_WRITE		0
#define SYNC_REP_WAIT_FLUSH		1
#define SYNC_REP_WAIT_APPLY		2
```

커밋 쪽이다. 먼저 이 서버의 디스크에 flush 하고, CLOG 에 커밋을 적은 뒤, 동기 복제를 기다린다.

`access/transam` / `xact.c` L1498-L1502 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xact.c#L1498-L1502))

```c
// access/transam/xact.c L1498-L1502
	if ((wrote_xlog && markXidCommitted &&
		 synchronous_commit > SYNCHRONOUS_COMMIT_OFF) ||
		forceSyncCommit || nrels > 0)
	{
		XLogFlush(XactLastRecEnd);
```

`access/transam` / `xact.c` L1556-L1557 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xact.c#L1556-L1557))

```c
// access/transam/xact.c L1556-L1557
	if (wrote_xlog && markXidCommitted)
		SyncRepWaitForLSN(XactLastRecEnd, true);
```

기다리는 쪽(`SyncRepWaitForLSN`)이다. 큐에 들어가고 latch 에서 잔다.

`replication` / `syncrep.c` L178-L345 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/syncrep.c#L178-L345))

```c
// replication/syncrep.c L178-L345
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

// ... (L195-L206 생략: 주석)
	if (WalSndCtl->sync_standbys_status & SYNC_STANDBY_INIT)
	{
		if ((WalSndCtl->sync_standbys_status & SYNC_STANDBY_DEFINED) == 0 ||
			lsn <= WalSndCtl->lsn[mode])
		{
			LWLockRelease(SyncRepLock);
			return;
		}
	}
// ... (L216-L244 생략: 동기 standby 정보가 아직 초기화 전일 때의 판단)

	/*
	 * Set our waitLSN so WALSender will know when to wake us, and add
	 * ourselves to the queue.
	 */
	MyProc->waitLSN = lsn;
	MyProc->syncRepState = SYNC_REP_WAITING;
	SyncRepQueueInsert(mode);
	Assert(SyncRepQueueIsOrderedByLSN(mode));
	LWLockRelease(SyncRepLock);

// ... (L256-L270 생략: ps 표시와 주석)
	for (;;)
	{
		int			rc;

// ... (L275-L284 생략: 주석)
		if (MyProc->syncRepState == SYNC_REP_WAIT_COMPLETE)
			break;
// ... (L287-L326 생략: 종료 요청이나 취소 요청이면 경고를 남기고 대기를 끝낸다)
		/*
		 * Wait on latch.  Any condition that should wake us up will set the
		 * latch, so no need for timeout.
		 */
		rc = WaitLatch(MyLatch, WL_LATCH_SET | WL_POSTMASTER_DEATH, -1,
					   WAIT_EVENT_SYNC_REP);

// ... (L334-L337 생략: 주석)
		if (rc & WL_POSTMASTER_DEATH)
		{
			ProcDiePending = true;
			whereToSendOutput = DestNone;
			SyncRepCancelWait();
			break;
		}
	}
```

깨우는 쪽이다. 이 walsender 가 동기 standby 를 맡고 있으면 세 위치를 구해 큐를 비운다.

`replication` / `syncrep.c` L474-L573 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/syncrep.c#L474-L573))

```c
// replication/syncrep.c L474-L573
SyncRepReleaseWaiters(void)
{
	volatile WalSndCtlData *walsndctl = WalSndCtl;
	XLogRecPtr	writePtr;
	XLogRecPtr	flushPtr;
	XLogRecPtr	applyPtr;
	bool		got_recptr;
	bool		am_sync;
	int			numwrite = 0;
	int			numflush = 0;
	int			numapply = 0;

// ... (L486-L492 생략: 주석)
	if (MyWalSnd->sync_standby_priority == 0 ||
		(MyWalSnd->state != WALSNDSTATE_STREAMING &&
		 MyWalSnd->state != WALSNDSTATE_STOPPING) ||
		XLogRecPtrIsInvalid(MyWalSnd->flush))
	{
		announce_next_takeover = true;
		return;
	}

	/*
	 * We're a potential sync standby. Release waiters if there are enough
	 * sync standbys and we are considered as sync.
	 */
	LWLockAcquire(SyncRepLock, LW_EXCLUSIVE);

// ... (L508-L515 생략: 주석)
	got_recptr = SyncRepGetSyncRecPtr(&writePtr, &flushPtr, &applyPtr, &am_sync);

// ... (L518-L534 생략: 처음 동기 standby 가 되었으면 LOG)

	/*
	 * If the number of sync standbys is less than requested or we aren't
	 * managing a sync standby then just leave.
	 */
	if (!got_recptr || !am_sync)
	{
		LWLockRelease(SyncRepLock);
		announce_next_takeover = !am_sync;
		return;
	}

// ... (L547-L550 생략: 주석)
	if (walsndctl->lsn[SYNC_REP_WAIT_WRITE] < writePtr)
	{
		walsndctl->lsn[SYNC_REP_WAIT_WRITE] = writePtr;
		numwrite = SyncRepWakeQueue(false, SYNC_REP_WAIT_WRITE);
	}
	if (walsndctl->lsn[SYNC_REP_WAIT_FLUSH] < flushPtr)
	{
		walsndctl->lsn[SYNC_REP_WAIT_FLUSH] = flushPtr;
		numflush = SyncRepWakeQueue(false, SYNC_REP_WAIT_FLUSH);
	}
	if (walsndctl->lsn[SYNC_REP_WAIT_APPLY] < applyPtr)
	{
		walsndctl->lsn[SYNC_REP_WAIT_APPLY] = applyPtr;
		numapply = SyncRepWakeQueue(false, SYNC_REP_WAIT_APPLY);
	}

	LWLockRelease(SyncRepLock);

// ... (L569-L572 생략: DEBUG3 로그)
}
```

큐는 LSN 순으로 정렬되어 있어서, 앞에서부터 꺼내다 기준 위치보다 큰 대기자를 만나면 멈춘다.

`replication` / `syncrep.c` L907-L954 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/syncrep.c#L907-L954))

```c
// replication/syncrep.c L907-L954
SyncRepWakeQueue(bool all, int mode)
{
	volatile WalSndCtlData *walsndctl = WalSndCtl;
	int			numprocs = 0;
	dlist_mutable_iter iter;

	Assert(mode >= 0 && mode < NUM_SYNC_REP_WAIT_MODE);
	Assert(LWLockHeldByMeInMode(SyncRepLock, LW_EXCLUSIVE));
	Assert(SyncRepQueueIsOrderedByLSN(mode));

	dlist_foreach_modify(iter, &WalSndCtl->SyncRepQueue[mode])
	{
		PGPROC	   *proc = dlist_container(PGPROC, syncRepLinks, iter.cur);

// ... (L921-L923 생략: 주석)
		if (!all && walsndctl->lsn[mode] < proc->waitLSN)
			return numprocs;

		/*
		 * Remove from queue.
		 */
		dlist_delete_thoroughly(&proc->syncRepLinks);

// ... (L932-L942 생략: 주석)
		proc->syncRepState = SYNC_REP_WAIT_COMPLETE;

		/*
		 * Wake only when we have set state and removed from queue.
		 */
		SetLatch(&(proc->procLatch));

		numprocs++;
	}

	return numprocs;
}
```

## 동작 흐름

```text
 synchronous_commit 단계별로 커밋이 무엇을 기다리는가 (기본값 on = remote_flush)

 value         SyncCommitLevel  local WAL           queue (SyncRepWaitMode)  기다리는 것
 off           OFF              XLogSetAsyncXactLSN NO_WAIT                   아무것도. WAL writer 가 나중에 flush
 local         LOCAL_FLUSH      XLogFlush           NO_WAIT                   이 서버의 fsync 만
 remote_write  REMOTE_WRITE     XLogFlush           SYNC_REP_WAIT_WRITE (0)   standby 가 pwrite 한 위치
 on            REMOTE_FLUSH     XLogFlush           SYNC_REP_WAIT_FLUSH (1)   standby 가 fsync 한 위치
 remote_apply  REMOTE_APPLY     XLogFlush           SYNC_REP_WAIT_APPLY (2)   standby 가 redo 한 위치

 local WAL 열: xact.c L1498 의 조건 (synchronous_commit > OFF 면 XLogFlush)
 queue 열: assign_synchronous_commit L1126-L1139
 synchronous_standby_names 가 비어 있으면 on 이어도 L178-L181 에서 바로 돌아간다
```

```text
 커밋 하나가 동기 복제를 기다리는 시간축 (synchronous_commit = on, 동기 standby 하나)

 primary backend               primary walsender             standby walreceiver
 RecordTransactionCommit
   L1502 XLogFlush(끝 = L)
     fsync, WalSndWakeup  ---->  [05] 깬다
   L1508 CLOG 에 커밋              [06] L 까지 'w'  --------->  [08] pwrite
   L1557 SyncRepWaitForLSN(L)                                  [10] 'r' write=L flush<L
     L250 waitLSN = L         <---------------------------------
     L252 FLUSH 큐에 삽입          [11] write 갱신
     L331 WaitLatch                [12] lsn[WRITE] = L
       (아직 잔다)                       WRITE 큐를 비운다. flush 가 올랐으면 FLUSH 큐도
                                         보지만 flush < L 이라 이 backend 는 남는다
                                                               [09] fsync
                                   <---------------------------- [10] 'r' flush=L
                                   [11] flush 갱신
                                   [12] L556 lsn[FLUSH] = L
                                        SyncRepWakeQueue(FLUSH)
                                          waitLSN L <= L
                                          syncRepState = COMPLETE
                                          SetLatch  ----+
     L285 COMPLETE -> break   <-------------------------+
   CommitTransaction L2389 ProcArrayEndTransaction   여기서야 다른 세션에 보인다
   클라이언트에 COMMIT 응답

 L1502, L1508, L1557, L2389 는 access/transam/xact.c, L250 L252 L285 L331 L556 은 replication/syncrep.c 의 줄이다
```

기다리는 동안 이 트랜잭션은 이미 로컬에서 커밋되었다. L1553-L1554 주석대로 CLOG 에는 커밋이 적혔지만 ProcArray 에는 아직 실행 중으로 남아 잠금도 쥐고 있다. 그래서 취소 요청이 와도 되돌릴 수 없고, 경고만 남기고 대기를 끝낸다(L300-L325).

```text
 동기 standby 가 여럿일 때 기준 위치 (SyncRepGetSyncRecPtr L586)

 보고된 flush   s1 0/5000000    s2 0/4800000    s3 0/4F00000

 synchronous_standby_names = 'FIRST 2 (s1, s2, s3)'
   동기 = 우선순위가 앞선 둘, s1 과 s2
   기준 = 둘 중 가장 오래된 값 = min(0/5000000, 0/4800000) = 0/4800000

 synchronous_standby_names = 'ANY 2 (s1, s2, s3)'
   후보 = 셋 다
   기준 = 내림차순 [0/5000000, 0/4F00000, 0/4800000] 의 2 번째 = 0/4F00000
          (둘이 이미 받은 가장 앞선 위치)

 FIRST 는 SyncRepGetOldestSyncRecPtr L660, ANY 는 SyncRepGetNthLatestSyncRecPtr L693
 이 계산은 동기 후보 walsender 가 'r' 을 받을 때마다 L516 에서 다시 한다
```

```text
 SyncRepReleaseWaiters 가 아무것도 안 하고 돌아가는 경우

 L493  이 walsender 의 sync_standby_priority 가 0     synchronous_standby_names 에 없다
 L494  STREAMING 도 STOPPING 도 아니다                 아직 CATCHUP (따라잡는 중)
 L496  flush 가 아직 없다
 L540  동기 standby 수가 num_sync 보다 적거나, 내가 동기가 아니다

 둘째 줄 때문에 새로 붙은 standby 는 다 따라잡기 전에는 대기자를 풀지 못한다
```

## 결과가 쓰이는 곳

```text
 WalSndCtl->lsn[mode]
      --> SyncRepWaitForLSN 이 큐에 들어가기 전에 이미 지났는지 본다 (L210, L216)
      --> SyncRepWakeQueue 의 기준

 proc->syncRepState = SYNC_REP_WAIT_COMPLETE, SetLatch
      --> [커밋] 흐름의 SyncRepWaitForLSN 이 L285 에서 루프를 나오고
          CommitTransaction 이 이어서 ProcArray 에서 빠지고 클라이언트에 응답한다
```

## 다루지 않는 것

`synchronous_standby_names` 파싱(`check_synchronous_standby_names`, `syncrep_gram.y`), 동기 후보 고르기(`SyncRepGetCandidateStandbys`, `SyncRepGetStandbyPriority`), 큐 삽입(`SyncRepQueueInsert`), checkpointer 가 관리하는 `sync_standbys_status` 깃발(`SyncRepUpdateSyncStandbysDefined`), 대기 취소(`SyncRepCancelWait`)는 요약만 했다. 커밋 전체 순서는 [커밋](../../commit/README.md) 흐름에 있다.
