# StartTransactionCommand

상위: [커밋](../README.md)

**문장 하나를 시작할 때마다 불린다.** 트랜잭션 블록 밖(`TBLOCK_DEFAULT`)이면 [02] `StartTransaction` 으로 새 트랜잭션을 열고 `TBLOCK_STARTED` 로 표시한다. 이미 블록 안이거나 실패한 블록 안이면 아무것도 하지 않는다. 그 밖의 상태에서 불리면 호출 순서가 깨진 것이므로 ERROR 다.

## 위치

`access` / `transam` / `xact.c` L3058-L3124 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xact.c#L3058-L3124))

## 실제 코드

backend 쪽 입구다. 같은 트랜잭션 안에서 이미 시작했으면(`xact_started`) 다시 부르지 않는다.

`tcop` / `postgres.c` L2786-L2823 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/tcop/postgres.c#L2786-L2823))

```c
// postgres.c L2786-L2823
static void
start_xact_command(void)
{
	if (!xact_started)
	{
		StartTransactionCommand();

		xact_started = true;
	}
	else if (MyXactFlags & XACT_FLAGS_PIPELINING)
	{
		/*
		 * When the first Execute message is completed, following commands
		 * will be done in an implicit transaction block created via
		 * pipelining. The transaction state needs to be updated to an
		 * implicit block if we're not already in a transaction block (like
		 * one started by an explicit BEGIN).
		 */
		BeginImplicitTransactionBlock();
	}

	// ... (L2807-L2822 생략: statement_timeout, 클라이언트 연결 검사 타이머)
}
```

`access` / `transam` / `xact.c` L3058-L3124 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xact.c#L3058-L3124))

```c
// xact.c L3058-L3124
void
StartTransactionCommand(void)
{
	TransactionState s = CurrentTransactionState;

	switch (s->blockState)
	{
			/*
			 * if we aren't in a transaction block, we just do our usual start
			 * transaction.
			 */
		case TBLOCK_DEFAULT:
			StartTransaction();
			s->blockState = TBLOCK_STARTED;
			break;

			/*
			 * We are somewhere in a transaction block or subtransaction and
			 * about to start a new command.  For now we do nothing, but
			 * someday we may do command-local resource initialization. (Note
			 * that any needed CommandCounterIncrement was done by the
			 * previous CommitTransactionCommand.)
			 */
		case TBLOCK_INPROGRESS:
		case TBLOCK_IMPLICIT_INPROGRESS:
		case TBLOCK_SUBINPROGRESS:
			break;

			/*
			 * Here we are in a failed transaction block (one of the commands
			 * caused an abort) so we do nothing but remain in the abort
			 * state.  Eventually we will get a ROLLBACK command which will
			 * get us out of this state.  (It is up to other code to ensure
			 * that no commands other than ROLLBACK will be processed in these
			 * states.)
			 */
		case TBLOCK_ABORT:
		case TBLOCK_SUBABORT:
			break;

			// ... (L3098-L3115 생략: 나머지 상태는 모두 잘못된 호출이라 ERROR)
	}

	/*
	 * We must switch to CurTransactionContext before returning. This is
	 * already done if we called StartTransaction, otherwise not.
	 */
	Assert(CurTransactionContext != NULL);
	MemoryContextSwitchTo(CurTransactionContext);
}
```

## 동작 흐름

```text
 start_xact_command (postgres.c L2787)
   xact_started == false  -> StartTransactionCommand, xact_started = true
   이미 true, 파이프라이닝 중 -> BeginImplicitTransactionBlock (L2804)

 StartTransactionCommand
   blockState
   TBLOCK_DEFAULT                     -> [02] StartTransaction, blockState = TBLOCK_STARTED  (L3069-L3071)
   TBLOCK_INPROGRESS
   TBLOCK_IMPLICIT_INPROGRESS
   TBLOCK_SUBINPROGRESS               -> 아무것도 안 한다  (L3081-L3084)
   TBLOCK_ABORT, TBLOCK_SUBABORT      -> 아무것도 안 한다, ROLLBACK 을 기다린다  (L3094-L3096)
   그 밖                              -> elog(ERROR)  (L3113)
   끝에 CurTransactionContext 로 메모리 문맥을 바꾼다  (L3123)
```

blockState 는 "트랜잭션 블록의 어디쯤인가"이고, 이 함수와 짝인 [04] 가 문장 끝에서 그 다음 칸으로 옮긴다. 아래는 `BEGIN; UPDATE ...; COMMIT;` 을 메시지 세 개로 보낼 때 blockState 가 지나는 길이다.

```text
 BEGIN
   StartTransactionCommand   DEFAULT -> StartTransaction -> STARTED    L3069-L3071
   BeginTransactionBlock     STARTED -> BEGIN                          L3934
   [04] at statement end     BEGIN -> INPROGRESS                       L3213
 UPDATE
   StartTransactionCommand   INPROGRESS, no-op                         L3081-L3084
   [04] at statement end     INPROGRESS, CommandCounterIncrement       L3224
 COMMIT
   StartTransactionCommand   INPROGRESS, no-op                         L3081-L3084
   EndTransactionBlock       INPROGRESS -> END                         L4056
   [04] at statement end     END -> CommitTransaction -> DEFAULT       L3232-L3233

 자동 커밋 문장 하나면 STARTED 에서 바로 [04] 의 TBLOCK_STARTED 갈래가 커밋한다
```

## 결과가 쓰이는 곳

```text
 blockState = TBLOCK_STARTED
      --> BEGIN 이면 BeginTransactionBlock 이 TBLOCK_BEGIN 으로 바꾼다
      --> 아니면 [04] 가 문장 끝에서 CommitTransaction 으로 간다
 CurTransactionContext
      --> 문장 실행의 메모리 할당이 이 문맥에 쌓이고 커밋 때 지워진다 (AtCommit_Memory)
```

## 다루지 않는 것

암묵적 트랜잭션 블록(`BeginImplicitTransactionBlock`, 여러 문장을 한 메시지로 보낼 때)과 서브트랜잭션 상태(`TBLOCK_SUB*`)는 분기 이름만 짚었다.
