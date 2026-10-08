# XLogFlush

상위: [행 쓰기와 WAL 기록](../README.md)

**주어진 LSN 까지의 WAL 이 디스크에 닿았음을 보장한다.** 이미 그만큼 flush 됐으면 바로 돌아오고, 아니면 그 구간을 복사 중인 삽입이 끝나기를 기다린 뒤 `WALWriteLock` 을 잡아 write 와 fsync 를 한다. 잠금을 바로 못 잡았으면 기다렸다가 "그사이 다른 백엔드가 내 몫까지 flush 했나"를 다시 본다. 잠금을 잡은 백엔드는 요청받은 위치가 아니라 지금까지 삽입이 끝난 위치까지 쓰므로, 동시에 커밋하는 여러 백엔드가 fsync 한 번을 나눠 쓴다(group commit). `heap_insert` 는 이 함수를 부르지 않는다. 커밋과 더러운 페이지 쓰기가 부른다.

## 위치

`access` / `transam` / `xlog.c` L2780-L2941 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlog.c#L2780-L2941))

## 실제 코드

`access` / `transam` / `xlog.c` L2773-L2941 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlog.c#L2773-L2941))

```c
// xlog.c L2773-L2941
/*
 * Ensure that all XLOG data through the given position is flushed to disk.
 *
 * NOTE: this differs from XLogWrite mainly in that the WALWriteLock is not
 * already held, and we try to avoid acquiring it if possible.
 */
void
XLogFlush(XLogRecPtr record)
{
	XLogRecPtr	WriteRqstPtr;
	XLogwrtRqst WriteRqst;
	TimeLineID	insertTLI = XLogCtl->InsertTimeLineID;

	/*
	 * During REDO, we are reading not writing WAL.  Therefore, instead of
	 * trying to flush the WAL, we should update minRecoveryPoint instead. We
	 * test XLogInsertAllowed(), not InRecovery, because we need checkpointer
	 * to act this way too, and because when it tries to write the
	 * end-of-recovery checkpoint, it should indeed flush.
	 */
	if (!XLogInsertAllowed())
	{
		UpdateMinRecoveryPoint(record, false);
		return;
	}

	/* Quick exit if already known flushed */
	if (record <= LogwrtResult.Flush)
		return;

// ... (L2803-L2809 생략: WAL_DEBUG 로그)

	START_CRIT_SECTION();

	/*
	 * Since fsync is usually a horribly expensive operation, we try to
	 * piggyback as much data as we can on each fsync: if we see any more data
	 * entered into the xlog buffer, we'll write and fsync that too, so that
	 * the final value of LogwrtResult.Flush is as large as possible. This
	 * gives us some chance of avoiding another fsync immediately after.
	 */

	/* initialize to given target; may increase below */
	WriteRqstPtr = record;

	/*
	 * Now wait until we get the write lock, or someone else does the flush
	 * for us.
	 */
	for (;;)
	{
		XLogRecPtr	insertpos;

		/* done already? */
		RefreshXLogWriteResult(LogwrtResult);
		if (record <= LogwrtResult.Flush)
			break;

		/*
		 * Before actually performing the write, wait for all in-flight
		 * insertions to the pages we're about to write to finish.
		 */
		SpinLockAcquire(&XLogCtl->info_lck);
		if (WriteRqstPtr < XLogCtl->LogwrtRqst.Write)
			WriteRqstPtr = XLogCtl->LogwrtRqst.Write;
		SpinLockRelease(&XLogCtl->info_lck);
		insertpos = WaitXLogInsertionsToFinish(WriteRqstPtr);

		/*
		 * Try to get the write lock. If we can't get it immediately, wait
		 * until it's released, and recheck if we still need to do the flush
		 * or if the backend that held the lock did it for us already. This
		 * helps to maintain a good rate of group committing when the system
		 * is bottlenecked by the speed of fsyncing.
		 */
		if (!LWLockAcquireOrWait(WALWriteLock, LW_EXCLUSIVE))
		{
			/*
			 * The lock is now free, but we didn't acquire it yet. Before we
			 * do, loop back to check if someone else flushed the record for
			 * us already.
			 */
			continue;
		}

		/* Got the lock; recheck whether request is satisfied */
		RefreshXLogWriteResult(LogwrtResult);
		if (record <= LogwrtResult.Flush)
		{
			LWLockRelease(WALWriteLock);
			break;
		}

		/*
		 * Sleep before flush! By adding a delay here, we may give further
		 * backends the opportunity to join the backlog of group commit
		 * followers; this can significantly improve transaction throughput,
		 * at the risk of increasing transaction latency.
		 *
		 * We do not sleep if enableFsync is not turned on, nor if there are
		 * fewer than CommitSiblings other backends with active transactions.
		 */
		if (CommitDelay > 0 && enableFsync &&
			MinimumActiveBackends(CommitSiblings))
		{
			pg_usleep(CommitDelay);

			/*
			 * Re-check how far we can now flush the WAL. It's generally not
			 * safe to call WaitXLogInsertionsToFinish while holding
			 * WALWriteLock, because an in-progress insertion might need to
			 * also grab WALWriteLock to make progress. But we know that all
			 * the insertions up to insertpos have already finished, because
			 * that's what the earlier WaitXLogInsertionsToFinish() returned.
			 * We're only calling it again to allow insertpos to be moved
			 * further forward, not to actually wait for anyone.
			 */
			insertpos = WaitXLogInsertionsToFinish(insertpos);
		}

		/* try to write/flush later additions to XLOG as well */
		WriteRqst.Write = insertpos;
		WriteRqst.Flush = insertpos;

		XLogWrite(WriteRqst, insertTLI, false);

		LWLockRelease(WALWriteLock);
		/* done */
		break;
	}

	END_CRIT_SECTION();

	/* wake up walsenders now that we've released heavily contended locks */
	WalSndWakeupProcessRequests(true, !RecoveryInProgress());

	// ... (L2915-L2935 생략: flush 가 요청 위치에 못 미친 경우에 대한 주석 (페이지 LSN 이 깨진 경우))
	if (LogwrtResult.Flush < record)
		elog(ERROR,
			 "xlog flush request %X/%X is not satisfied --- flushed only to %X/%X",
			 LSN_FORMAT_ARGS(record),
			 LSN_FORMAT_ARGS(LogwrtResult.Flush));
}
```

복사가 끝난 위치를 알아내는 함수다. 예약된 끝에서 시작해, 아직 복사 중인 삽입 잠금이 있으면 그 위치로 물러난다.

`access` / `transam` / `xlog.c` L1492-L1616 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlog.c#L1492-L1616))

```c
// xlog.c L1492-L1616
/*
 * Wait for any WAL insertions < upto to finish.
 *
 * Returns the location of the oldest insertion that is still in-progress.
 * Any WAL prior to that point has been fully copied into WAL buffers, and
 * can be flushed out to disk. Because this waits for any insertions older
 * than 'upto' to finish, the return value is always >= 'upto'.
 *
 * Note: When you are about to write out WAL, you must call this function
 * *before* acquiring WALWriteLock, to avoid deadlocks. This function might
 * need to wait for an insertion to finish (or at least advance to next
 * uninitialized page), and the inserter might need to evict an old WAL buffer
 * to make room for a new one, which in turn requires WALWriteLock.
 */
static XLogRecPtr
WaitXLogInsertionsToFinish(XLogRecPtr upto)
{
	uint64		bytepos;
	XLogRecPtr	inserted;
	XLogRecPtr	reservedUpto;
	XLogRecPtr	finishedUpto;
	XLogCtlInsert *Insert = &XLogCtl->Insert;
	int			i;

	if (MyProc == NULL)
		elog(PANIC, "cannot wait without a PGPROC structure");

	/*
	 * Check if there's any work to do.  Use a barrier to ensure we get the
	 * freshest value.
	 */
	inserted = pg_atomic_read_membarrier_u64(&XLogCtl->logInsertResult);
	if (upto <= inserted)
		return inserted;

	/* Read the current insert position */
	SpinLockAcquire(&Insert->insertpos_lck);
	bytepos = Insert->CurrBytePos;
	SpinLockRelease(&Insert->insertpos_lck);
	reservedUpto = XLogBytePosToEndRecPtr(bytepos);

	/*
	 * No-one should request to flush a piece of WAL that hasn't even been
	 * reserved yet. However, it can happen if there is a block with a bogus
	 * LSN on disk, for example. XLogFlush checks for that situation and
	 * complains, but only after the flush. Here we just assume that to mean
	 * that all WAL that has been reserved needs to be finished. In this
	 * corner-case, the return value can be smaller than 'upto' argument.
	 */
	if (upto > reservedUpto)
	{
		ereport(LOG,
				(errmsg("request to flush past end of generated WAL; request %X/%X, current position %X/%X",
						LSN_FORMAT_ARGS(upto), LSN_FORMAT_ARGS(reservedUpto))));
		upto = reservedUpto;
	}

	/*
	 * Loop through all the locks, sleeping on any in-progress insert older
	 * than 'upto'.
	 *
	 * finishedUpto is our return value, indicating the point upto which all
	 * the WAL insertions have been finished. Initialize it to the head of
	 * reserved WAL, and as we iterate through the insertion locks, back it
	 * out for any insertion that's still in progress.
	 */
	finishedUpto = reservedUpto;
	for (i = 0; i < NUM_XLOGINSERT_LOCKS; i++)
	{
		XLogRecPtr	insertingat = InvalidXLogRecPtr;

		do
		{
			// ... (L1565-L1587 생략: LWLockWaitForVar 의 의미와 메모리 장벽이 없어도 되는 이유 주석)
			if (LWLockWaitForVar(&WALInsertLocks[i].l.lock,
								 &WALInsertLocks[i].l.insertingAt,
								 insertingat, &insertingat))
			{
				/* the lock was free, so no insertion in progress */
				insertingat = InvalidXLogRecPtr;
				break;
			}

			/*
			 * This insertion is still in progress. Have to wait, unless the
			 * inserter has proceeded past 'upto'.
			 */
		} while (insertingat < upto);

		if (insertingat != InvalidXLogRecPtr && insertingat < finishedUpto)
			finishedUpto = insertingat;
	}

	/*
	 * Advance the limit we know to have been inserted and return the freshest
	 * value we know of, which might be beyond what we requested if somebody
	 * is concurrently doing this with an 'upto' pointer ahead of us.
	 */
	finishedUpto = pg_atomic_monotonic_advance_u64(&XLogCtl->logInsertResult,
												   finishedUpto);

	return finishedUpto;
}
```

## 동작 흐름

```text
 L2793 복구 중이면 UpdateMinRecoveryPoint 하고 끝      redo 중에는 쓰지 않는다
 L2800 record <= LogwrtResult.Flush 면 끝               지역 사본으로 빠른 확인
 L2811 START_CRIT_SECTION
 L2822 WriteRqstPtr = record
 L2828 for (;;)
 L2833   RefreshXLogWriteResult, 이미 됐으면 break
 L2842   공유 LogwrtRqst.Write 가 더 크면 그만큼 키운다    다른 백엔드의 요청도 같이
 L2845   insertpos = WaitXLogInsertionsToFinish(WriteRqstPtr)
           L1523  logInsertResult 가 이미 넘었으면 바로 반환
           L1529  reservedUpto = 예약된 끝 (CurrBytePos)
           L1559  삽입 잠금 8개마다
           L1588    LWLockWaitForVar: 잠금이 풀렸거나, insertingAt 이 upto 를 넘을 때까지 잔다
           L1603    아직 진행 중이면 finishedUpto = min(finishedUpto, insertingAt)
           L1612  logInsertResult 를 앞으로 민다
 L2854   LWLockAcquireOrWait(WALWriteLock)
           못 잡고 기다렸다 깨어나면 L2861 continue     남이 flush 했을 수 있다
 L2865   잡았으면 다시 확인, 됐으면 해제하고 break
 L2881   commit_delay > 0 이고 활성 트랜잭션이 commit_siblings 이상이면
 L2884     pg_usleep(CommitDelay)                     더 많은 커밋이 합류하게 기다린다
 L2896     insertpos 를 다시 앞으로
 L2900   WriteRqst.Write = WriteRqst.Flush = insertpos   요청보다 멀리
 L2903   XLogWrite(WriteRqst, insertTLI, false)
           WAL 버퍼 페이지를 pg_pwrite (L2434), issue_xlog_fsync (L2479, L2550)
 L2905   WALWriteLock 해제, break
 L2910 END_CRIT_SECTION
 L2913 WalSndWakeupProcessRequests                   walsender 를 깨운다 --> [스트리밍 복제]
 L2936 그래도 Flush < record 면 ERROR                 요청이 WAL 끝을 넘은 경우 (깨진 페이지 LSN 등)
```

`WALWriteLock` 을 기다린 백엔드가 깨어나자마자 쓰지 않고 다시 확인하는 것이 group commit 의 핵심이다. 앞 백엔드가 이미 더 먼 곳까지 써 두었으면 아무것도 하지 않고 나간다.

```text
 세 백엔드가 거의 동시에 커밋 (각자 commit 레코드를 넣은 뒤 XLogFlush)

 commit 레코드 끝   A = 0/6001040   B = 0/6001080   C = 0/60010C0
 시작 시 LogwrtResult.Flush = 0/6001000

 시각  A                                B                                C
 t1    Wait(0/6001040) -> 0/6001080     Wait(0/6001080) -> 0/6001080     commit 레코드 삽입 전
       (B 까지 예약, 복사가 끝나 있었다)
 t2    WALWriteLock acquire             AcquireOrWait -> sleep           예약, 복사
 t3    XLogWrite(0/6001080)                                              Wait(0/60010C0) -> 0/60010C0
       write + fsync                                                     AcquireOrWait -> sleep
 t4    release, Flush = 0/6001080       wake -> continue                 wake -> continue
 t5                                     Refresh: 0/6001080 >= record     Refresh: 아직 모자람
                                        -> break, no fsync               WALWriteLock 획득
 t6                                                                      XLogWrite(0/60010C0)

 Wait = WaitXLogInsertionsToFinish, AcquireOrWait = LWLockAcquireOrWait(WALWriteLock)
 C 가 t1 에 이미 위치를 예약하고 복사 중이었다면, A 의 Wait 는 C 의 삽입 잠금에서
 기다렸다가 0/60010C0 까지 돌려주고 (L1601 의 do-while), 한 번의 fsync 로 셋을 다 덮었을 것이다

 fsync 두 번으로 커밋 세 개. B 는 A 의 fsync 에 얹혀 갔다
 commit_delay 를 켜면 A 가 t2 와 t3 사이에 잠깐 잔다(L2884). 그사이 C 가 복사를 끝내고 자기 Wait 로
 logInsertResult 를 0/60010C0 까지 밀어 두었으면, A 의 L2896 재확인이 L1524 에서 그 값을 바로 받아 C 까지 한 번에 쓴다
 (L2896 은 기다리지 않고 이미 끝난 위치만 읽는다. L2886-L2894 주석)
```

이 함수를 부르는 두 자리가 WAL 규칙의 두 얼굴이다. 커밋은 "커밋했다고 답하기 전에 commit 레코드가 디스크에", 페이지 쓰기는 "데이터 페이지보다 그 페이지를 바꾼 WAL 이 먼저 디스크에"를 지킨다.

```text
 XLogFlush 를 부르는 자리

 호출자                                   위치                 지키는 것
 RecordTransactionCommit  xact.c L1502    XactLastRecEnd       커밋 응답 전에 commit 레코드가 디스크에 (내구성)
 FlushBuffer              bufmgr.c L4371  page LSN             페이지보다 WAL 이 먼저 (WAL-before-data)
 XLogInsertRecord         xlog.c L984     EndPos               XLOG_SWITCH 레코드 뒤 세그먼트 전환
```

## 결과가 쓰이는 곳

```text
 LogwrtResult.Flush / XLogCtl->logFlushResult
      --> 다음 XLogFlush 의 빠른 확인 (L2800)
      --> [커밋] 이 돌아와 클라이언트에 COMMIT 을 보낸다
      --> [버퍼 관리] FlushBuffer 가 smgrwrite 로 페이지를 쓴다
 WalSndWakeupProcessRequests
      --> [스트리밍 복제] walsender 가 새로 flush 된 WAL 을 보낸다
 logInsertResult
      --> 다음 WaitXLogInsertionsToFinish 가 잠금을 훑지 않고 끝낸다 (L1523)
```

## 다루지 않는 것

`XLogWrite` 의 내부(WAL 버퍼 순환, 세그먼트 파일 열기와 전환, 아카이브 알림), `wal_sync_method` 별 fsync 방식(`issue_xlog_fsync`), 비동기 커밋과 WAL writer(`XLogBackgroundFlush`), 복구 중의 `UpdateMinRecoveryPoint`, 동기 복제 대기(`SyncRepWaitForLSN`, 다음 흐름 [커밋](../../commit/README.md))는 flush 의 곁가지라 요약만 했다.
