# CommitTransactionCommandInternal

상위: [커밋](../README.md)

**문장 하나가 끝날 때마다 불려 blockState 에 따라 할 일을 고른다.** 자동 커밋 문장(`TBLOCK_STARTED`)이나 COMMIT 문장(`TBLOCK_END`)이면 [05] `CommitTransaction` 으로 진짜 커밋을 하고 `TBLOCK_DEFAULT` 로 돌아간다. 블록 안의 보통 문장(`TBLOCK_INPROGRESS`)이면 커밋하지 않고 명령 카운터만 올려서, 다음 문장이 방금 쓴 행을 보게 만든다. 서브트랜잭션을 한 겹 정리할 때는 `false` 를 돌려주고, 바깥 래퍼 `CommitTransactionCommand` 가 다시 부른다.

## 위치

`access` / `transam` / `xact.c` L3174-L3443 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xact.c#L3174-L3443))

## 실제 코드

backend 쪽 출구다. 문장 하나를 처리한 뒤, 또는 트랜잭션 제어 문장 뒤에 불린다.

`tcop` / `postgres.c` L2825-L2848 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/tcop/postgres.c#L2825-L2848))

```c
// postgres.c L2825-L2848
static void
finish_xact_command(void)
{
	/* cancel active statement timeout after each command */
	disable_statement_timeout();

	if (xact_started)
	{
		CommitTransactionCommand();

// ... (L2835-L2844 생략: 메모리 검사 빌드 옵션)

		xact_started = false;
	}
}
```

재귀 대신 반복으로 서브트랜잭션 스택을 내려가는 래퍼다.

`access` / `transam` / `xact.c` L3156-L3166 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xact.c#L3156-L3166))

```c
// xact.c L3156-L3166
void
CommitTransactionCommand(void)
{
	/*
	 * Repeatedly call CommitTransactionCommandInternal() until all the work
	 * is done.
	 */
	while (!CommitTransactionCommandInternal())
	{
	}
}
```

`access` / `transam` / `xact.c` L3174-L3443 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xact.c#L3174-L3443))

```c
// xact.c L3174-L3443
static bool
CommitTransactionCommandInternal(void)
{
	TransactionState s = CurrentTransactionState;
	SavedTransactionCharacteristics savetc;

	/* Must save in case we need to restore below */
	SaveTransactionCharacteristics(&savetc);

	switch (s->blockState)
	{
			/*
			 * These shouldn't happen.  TBLOCK_DEFAULT means the previous
			 * StartTransactionCommand didn't set the STARTED state
			 * appropriately, while TBLOCK_PARALLEL_INPROGRESS should be ended
			 * by EndParallelWorkerTransaction(), not this function.
			 */
		case TBLOCK_DEFAULT:
		case TBLOCK_PARALLEL_INPROGRESS:
			elog(FATAL, "CommitTransactionCommand: unexpected state %s",
				 BlockStateAsString(s->blockState));
			break;

			/*
			 * If we aren't in a transaction block, just do our usual
			 * transaction commit, and return to the idle state.
			 */
		case TBLOCK_STARTED:
			CommitTransaction();
			s->blockState = TBLOCK_DEFAULT;
			break;

			/*
			 * We are completing a "BEGIN TRANSACTION" command, so we change
			 * to the "transaction block in progress" state and return.  (We
			 * assume the BEGIN did nothing to the database, so we need no
			 * CommandCounterIncrement.)
			 */
		case TBLOCK_BEGIN:
			s->blockState = TBLOCK_INPROGRESS;
			break;

			/*
			 * This is the case when we have finished executing a command
			 * someplace within a transaction block.  We increment the command
			 * counter and return.
			 */
		case TBLOCK_INPROGRESS:
		case TBLOCK_IMPLICIT_INPROGRESS:
		case TBLOCK_SUBINPROGRESS:
			CommandCounterIncrement();
			break;

			/*
			 * We are completing a "COMMIT" command.  Do it and return to the
			 * idle state.
			 */
		case TBLOCK_END:
			CommitTransaction();
			s->blockState = TBLOCK_DEFAULT;
			if (s->chain)
			{
				StartTransaction();
				s->blockState = TBLOCK_INPROGRESS;
				s->chain = false;
				RestoreTransactionCharacteristics(&savetc);
			}
			break;

			/*
			 * Here we are in the middle of a transaction block but one of the
			 * commands caused an abort so we do nothing but remain in the
			 * abort state.  Eventually we will get a ROLLBACK command.
			 */
		case TBLOCK_ABORT:
		case TBLOCK_SUBABORT:
			break;

			// ... (L3252-L3294 생략: ROLLBACK 처리 (ABORT_END, ABORT_PENDING) 와 PREPARE TRANSACTION)

			// ... (L3296-L3438 생략: SAVEPOINT, RELEASE, 서브트랜잭션 커밋과 롤백)
	}

	/* Done, no more iterations required */
	return true;
}
```

## 동작 흐름

```text
 finish_xact_command (postgres.c L2826)
   L2829  statement_timeout 해제
   L2833  CommitTransactionCommand   -> while (!Internal()) {}   (xact.c L3163)

 CommitTransactionCommandInternal
   L3181  SaveTransactionCharacteristics       COMMIT AND CHAIN 이면 같은 특성으로 새로 열려고
   blockState
   TBLOCK_STARTED     L3202  CommitTransaction, -> DEFAULT              자동 커밋 문장
   TBLOCK_BEGIN       L3213  -> INPROGRESS                              BEGIN 문장 끝
   TBLOCK_INPROGRESS  L3224  CommandCounterIncrement                    블록 안 보통 문장
   TBLOCK_END         L3232  CommitTransaction, -> DEFAULT              COMMIT 문장 끝
                      L3234  if chain: StartTransaction, -> INPROGRESS  COMMIT AND CHAIN
   TBLOCK_ABORT       L3250  no-op                                      실패한 블록, ROLLBACK 대기
   TBLOCK_ABORT_END   L3258  CleanupTransaction                         실패 뒤 ROLLBACK
   TBLOCK_SUBCOMMIT   L3335  CommitSubTransaction loop, L3342 CommitTransaction
   TBLOCK_SUBABORT_*  L3372, L3380  return false                        래퍼가 부모 상태로 다시 부른다
   L3442  return true
```

블록 안에서 커밋 대신 하는 일인 `CommandCounterIncrement` 가 무엇을 바꾸는지는 같은 트랜잭션의 두 문장으로 볼 수 있다.

```text
 BEGIN;
 INSERT INTO t VALUES (1);    cid 0 으로 쓴다 (행의 cmin = 0)
                              문장 끝  [04] TBLOCK_INPROGRESS -> CommandCounterIncrement, cid = 1
 SELECT * FROM t;             스냅샷 curcid = 1
                              HeapTupleSatisfiesMVCC: xmin 이 내 XID 이고 cmin 0 < curcid 1  -> 보인다
 COMMIT;                      [04] TBLOCK_END -> CommitTransaction
```

## 결과가 쓰이는 곳

```text
 blockState = TBLOCK_DEFAULT
      --> 다음 문장의 [01] StartTransactionCommand 가 새 트랜잭션을 연다
 CommandCounterIncrement
      --> 같은 트랜잭션의 다음 문장 스냅샷이 방금 쓴 행을 본다
      --> 무효화 메시지를 처리해 이 트랜잭션의 카탈로그 변경을 자기 relcache 에 반영한다
```

## 다루지 않는 것

ROLLBACK 과 실패한 블록의 정리(`AbortTransaction`, `CleanupTransaction`), SAVEPOINT 계열 상태(`TBLOCK_SUB*`), `PREPARE TRANSACTION` 은 분기 위치만 적었다.
