# StartTransaction

상위: [커밋](../README.md)

**최상위 트랜잭션 하나를 연다.** 이 시점에는 진짜 XID 를 받지 않는다. 대신 backend 번호와 지역 카운터로 만든 **가상 트랜잭션 ID(vxid)** 를 받아 `MyProc->vxid.lxid` 에 알리고, 격리 수준·읽기 전용 같은 트랜잭션 특성과 명령 카운터를 초기화한 뒤 상태를 `TRANS_INPROGRESS` 로 바꾼다. XID 는 첫 쓰기에서 [03] 이 붙인다.

## 위치

`access` / `transam` / `xact.c` L2063-L2219 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xact.c#L2063-L2219))

## 실제 코드

`access` / `transam` / `xact.c` L2063-L2219 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xact.c#L2063-L2219))

```c
// xact.c L2063-L2219
static void
StartTransaction(void)
{
	TransactionState s;
	VirtualTransactionId vxid;

	/*
	 * Let's just make sure the state stack is empty
	 */
	s = &TopTransactionStateData;
	CurrentTransactionState = s;

	Assert(!FullTransactionIdIsValid(XactTopFullTransactionId));

	/* check the current transaction state */
	Assert(s->state == TRANS_DEFAULT);

	/*
	 * Set the current transaction state information appropriately during
	 * start processing.  Note that once the transaction status is switched
	 * this process cannot fail until the user ID and the security context
	 * flags are fetched below.
	 */
	s->state = TRANS_START;
	s->fullTransactionId = InvalidFullTransactionId;	/* until assigned */

	// ... (L2089-L2113 생략: 로그 샘플링, nesting 초기화, 보안 문맥 저장)
	/*
	 * Make sure we've reset xact state variables
	 *
	 * If recovery is still in progress, mark this transaction as read-only.
	 * We have lower level defences in XLogInsert and elsewhere to stop us
	 * from modifying data during recovery, but this gives the normal
	 * indication to the user that the transaction is read-only.
	 */
	if (RecoveryInProgress())
	{
		s->startedInRecovery = true;
		XactReadOnly = true;
	}
	else
	{
		s->startedInRecovery = false;
		XactReadOnly = DefaultXactReadOnly;
	}
	XactDeferrable = DefaultXactDeferrable;
	XactIsoLevel = DefaultXactIsoLevel;
	forceSyncCommit = false;
	MyXactFlags = 0;

	/*
	 * reinitialize within-transaction counters
	 */
	s->subTransactionId = TopSubTransactionId;
	currentSubTransactionId = TopSubTransactionId;
	currentCommandId = FirstCommandId;
	currentCommandIdUsed = false;

	/*
	 * initialize reported xid accounting
	 */
	nUnreportedXids = 0;
	s->didLogXid = false;

	/*
	 * must initialize resource-management stuff first
	 */
	AtStart_Memory();
	AtStart_ResourceOwner();

	/*
	 * Assign a new LocalTransactionId, and combine it with the proc number to
	 * form a virtual transaction id.
	 */
	vxid.procNumber = MyProcNumber;
	vxid.localTransactionId = GetNextLocalTransactionId();

	/*
	 * Lock the virtual transaction id before we announce it in the proc array
	 */
	VirtualXactLockTableInsert(vxid);

	/*
	 * Advertise it in the proc array.  We assume assignment of
	 * localTransactionId is atomic, and the proc number should be set
	 * already.
	 */
	Assert(MyProc->vxid.procNumber == vxid.procNumber);
	MyProc->vxid.lxid = vxid.localTransactionId;

	TRACE_POSTGRESQL_TRANSACTION_START(vxid.localTransactionId);

	// ... (L2179-L2199 생략: transaction_timestamp() 설정)

	/*
	 * initialize other subsystems for new transaction
	 */
	AtStart_GUC();
	AtStart_Cache();
	AfterTriggerBeginXact();

	/*
	 * done with start processing, set current transaction state to "in
	 * progress"
	 */
	s->state = TRANS_INPROGRESS;

	/* Schedule transaction timeout */
	if (TransactionTimeout > 0)
		enable_timeout_after(TRANSACTION_TIMEOUT, TransactionTimeout);

	ShowTransactionState("StartTransaction");
}
```

## 동작 흐름

```text
 StartTransaction
 L2072  CurrentTransactionState = &TopTransactionStateData   (스택을 비운다)
 L2086  s->state = TRANS_START
 L2087  fullTransactionId = Invalid                            XID 는 아직 없다
 L2122  복구 중이면 XactReadOnly = true
 L2132  XactDeferrable, XactIsoLevel 을 기본값으로              (SET TRANSACTION 이 나중에 덮는다)
 L2134  forceSyncCommit = false, MyXactFlags = 0
 L2142  currentCommandId = FirstCommandId                      CommandCounterIncrement 가 올린다
 L2154  AtStart_Memory, AtStart_ResourceOwner                  TopTransactionContext, TopTransactionResourceOwner
 L2162  vxid.localTransactionId = GetNextLocalTransactionId()
 L2167  VirtualXactLockTableInsert(vxid)                        자기 vxid 에 잠금
 L2175  MyProc->vxid.lxid = 그 값                               ProcArray 에 알린다
 L2204  AtStart_GUC, AtStart_Cache, AfterTriggerBeginXact
 L2212  s->state = TRANS_INPROGRESS
 L2216  transaction_timeout 이 있으면 타이머
```

트랜잭션을 가리키는 번호는 두 가지이고, 이 함수는 그중 싼 쪽만 만든다.

```text
 id     assigned at                 shared state touched                          쓰임
 vxid   StartTransaction L2162      MyProc->vxid.lxid, MyProc->fpVXIDLock         모든 트랜잭션. 남이 이 트랜잭션의 끝을 기다릴 때 잠그는 대상
 XID    AssignTransactionId L706    XidGenLock, pg_xact extend, ProcGlobal->xids  쓰는 트랜잭션만. 행의 xmin/xmax, pg_xact 의 칸

 vxid 잠금은 공유 잠금 해시가 아니라 자기 PGPROC 에 표시만 한다 (lock.c L4590-L4603)
```

## 결과가 쓰이는 곳

```text
 s->state = TRANS_INPROGRESS
      --> [03] AssignTransactionId 의 Assert (L643)
      --> [05] CommitTransaction 이 TRANS_INPROGRESS 가 아니면 WARNING
 MyProc->vxid.lxid
      --> [10] ProcArrayEndTransaction 이 InvalidLocalTransactionId 로 지운다
 TopTransactionResourceOwner
      --> [05] 가 ResourceOwnerRelease 로 버퍼 핀, 잠금, 파일을 순서대로 놓는다
```

## 다루지 않는 것

병렬 worker 의 트랜잭션 시작(`StartParallelWorkerTransaction`)과 서브트랜잭션 시작(`StartSubTransaction`), GUC·relcache·트리거 초기화 함수의 내부는 다루지 않았다.
