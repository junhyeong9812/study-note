# PostgresMain

상위: [연결과 backend 기동](../README.md)

**backend 의 몸통이다.** 앞부분에서 신호 처리기를 바꿔 끼우고 [08] `InitPostgres` 로 세션을 세운 뒤, `for (;;)` 루프에서 **메시지 하나를 읽고, 첫 바이트로 갈라 처리하고, 쉬는 상태가 되면 `ReadyForQuery` 를 보내는** 일을 연결이 끝날 때까지 되풀이한다. 루프 바로 앞의 `sigsetjmp` 는 모든 `ERROR` 가 되돌아오는 자리라서, 쿼리가 실패해도 backend 는 죽지 않고 트랜잭션만 버린 뒤 루프로 돌아온다.

## 위치

`tcop` / `postgres.c` L4188-L5026 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/tcop/postgres.c#L4188-L5026))

## 실제 코드

신호 처리기를 정한 뒤, 취소 키를 만들고 세션을 초기화한다.

`tcop` / `postgres.c` L4258-L4348 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/tcop/postgres.c#L4258-L4348))

```c
// tcop/postgres.c L4258-L4348
	/* Early initialization */
	BaseInit();

	/* We need to allow SIGINT, etc during the initial transaction */
	sigprocmask(SIG_SETMASK, &UnBlockSig, NULL);

	/*
	 * Generate a random cancel key, if this is a backend serving a
	 * connection. InitPostgres() will advertise it in shared memory.
	 */
	Assert(MyCancelKeyLength == 0);
	if (whereToSendOutput == DestRemote)
	{
		int			len;

		len = (MyProcPort == NULL || MyProcPort->proto >= PG_PROTOCOL(3, 2))
			? MAX_CANCEL_KEY_LENGTH : 4;
		if (!pg_strong_random(&MyCancelKey, len))
		{
			ereport(ERROR,
					(errcode(ERRCODE_INTERNAL_ERROR),
					 errmsg("could not generate random cancel key")));
		}
		MyCancelKeyLength = len;
	}

// ... (L4284-L4292 생략: 주석)
	InitPostgres(dbname, InvalidOid,	/* database to connect to */
				 username, InvalidOid,	/* role to connect as */
				 (!am_walsender) ? INIT_PG_LOAD_SESSION_LIBS : 0,
				 NULL);			/* no out_dbname */

	/*
	 * If the PostmasterContext is still around, recycle the space; we don't
	 * need it anymore after InitPostgres completes.
	 */
	if (PostmasterContext)
	{
		MemoryContextDelete(PostmasterContext);
		PostmasterContext = NULL;
	}

	SetProcessingMode(NormalProcessing);

// ... (L4310-L4313 생략: 주석)
	BeginReportingGUCOptions();

// ... (L4316-L4319 생략: 주석)
	if (IsUnderPostmaster && Log_disconnections)
		on_proc_exit(log_disconnections, 0);

	pgstat_report_connect(MyDatabaseId);

	/* Perform initialization specific to a WAL sender process. */
	if (am_walsender)
		InitWalSender();

	/*
	 * Send this backend's cancellation info to the frontend.
	 */
	if (whereToSendOutput == DestRemote)
	{
		StringInfoData buf;

		Assert(MyCancelKeyLength > 0);
		pq_beginmessage(&buf, PqMsg_BackendKeyData);
		pq_sendint32(&buf, (int32) MyProcPid);

		pq_sendbytes(&buf, MyCancelKey, MyCancelKeyLength);
		pq_endmessage(&buf);
		/* Need not flush since ReadyForQuery will do it. */
	}

	/* Welcome banner for standalone case */
	if (whereToSendOutput == DestDebug)
		printf("\nPostgreSQL stand-alone backend %s\n", PG_VERSION);

```

`ERROR` 가 `siglongjmp` 로 돌아오는 자리다. 트랜잭션을 버리고 루프 꼭대기로 간다.

`tcop` / `postgres.c` L4397-L4514 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/tcop/postgres.c#L4397-L4514))

```c
// tcop/postgres.c L4397-L4514
	if (sigsetjmp(local_sigjmp_buf, 1) != 0)
	{
// ... (L4399-L4405 생략: 주석)

		/* Since not using PG_TRY, must reset error stack by hand */
		error_context_stack = NULL;

		/* Prevent interrupts while cleaning up */
		HOLD_INTERRUPTS();

// ... (L4413-L4423 생략: 주석)
		disable_all_timeouts(false);	/* do first to avoid race condition */
		QueryCancelPending = false;
		idle_in_transaction_timeout_enabled = false;
		idle_session_timeout_enabled = false;

		/* Not reading from the client anymore. */
		DoingCommandRead = false;

		/* Make sure libpq is in a good state */
		pq_comm_reset();

		/* Report the error to the client and/or server log */
		EmitErrorReport();

// ... (L4438-L4449 생략: valgrind 보고와 주석)
		/*
		 * Abort the current transaction in order to recover.
		 */
		AbortCurrentTransaction();

// ... (L4455-L4456 생략: walsender 정리)

		PortalErrorCleanup();

// ... (L4460-L4474 생략: 복제 슬롯 해제와 JIT 초기화)
		/*
		 * Now return to normal top-level context and clear ErrorContext for
		 * next time.
		 */
		MemoryContextSwitchTo(MessageContext);
		FlushErrorState();

// ... (L4482-L4486 생략: 주석)
		if (doing_extended_query_message)
			ignore_till_sync = true;

		/* We don't have a transaction command open anymore */
		xact_started = false;

// ... (L4493-L4500 생략: 주석)
		if (pq_is_reading_msg())
			ereport(FATAL,
					(errcode(ERRCODE_PROTOCOL_VIOLATION),
					 errmsg("terminating connection because protocol synchronization was lost")));

		/* Now we can allow interrupts again */
		RESUME_INTERRUPTS();
	}

	/* We can now handle ereport(ERROR) */
	PG_exception_stack = &local_sigjmp_buf;

	if (!ignore_till_sync)
		send_ready_for_query = true;	/* initially, or after error */
```

루프의 꼭대기다. 메시지 메모리를 비우고, 쉬는 상태면 `ReadyForQuery` 를 보낸다.

`tcop` / `postgres.c` L4520-L4689 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/tcop/postgres.c#L4520-L4689))

```c
// tcop/postgres.c L4520-L4689
	for (;;)
	{
		int			firstchar;
		StringInfoData input_message;

// ... (L4525-L4537 생략: 주석과 valgrind)
		/*
		 * Release storage left over from prior query cycle, and create a new
		 * query input buffer in the cleared MessageContext.
		 */
		MemoryContextSwitchTo(MessageContext);
		MemoryContextReset(MessageContext);

		initStringInfo(&input_message);

// ... (L4547-L4568 생략: 카탈로그 스냅샷 해제와 주석)
		if (send_ready_for_query)
		{
			if (IsAbortedTransactionBlockState())
			{
				set_ps_display("idle in transaction (aborted)");
				pgstat_report_activity(STATE_IDLEINTRANSACTION_ABORTED, NULL);

// ... (L4576-L4583 생략: idle-in-transaction 타이머)
			}
			else if (IsTransactionOrTransactionBlock())
			{
				set_ps_display("idle in transaction");
				pgstat_report_activity(STATE_IDLEINTRANSACTION, NULL);

// ... (L4590-L4597 생략: idle-in-transaction 타이머)
			}
			else
			{
// ... (L4601-L4639 생략: 알림 처리와 통계 보고)
				set_ps_display("idle");
				pgstat_report_activity(STATE_IDLE, NULL);

// ... (L4643-L4649 생략: idle session 타이머)
			}

// ... (L4652-L4686 생략: GUC 보고와 연결 시간 로그)
			ReadyForQuery(whereToSendOutput);
			send_ready_for_query = false;
		}
```

메시지를 읽고 첫 바이트로 가른다. `'Q'` 가 다음 흐름의 입구다.

`tcop` / `postgres.c` L4697-L4776 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/tcop/postgres.c#L4697-L4776))

```c
// tcop/postgres.c L4697-L4776
		DoingCommandRead = true;

		/*
		 * (3) read a command (loop blocks here)
		 */
		firstchar = ReadCommand(&input_message);

// ... (L4704-L4722 생략: idle 타이머 해제)
		/*
// ... (L4724-L4731 생략: 주석)
		CHECK_FOR_INTERRUPTS();
		DoingCommandRead = false;

		/*
		 * (6) check for any other interesting events that happened while we
		 * slept.
		 */
		if (ConfigReloadPending)
		{
			ConfigReloadPending = false;
			ProcessConfigFile(PGC_SIGHUP);
		}

// ... (L4745-L4748 생략: 주석)
		if (ignore_till_sync && firstchar != EOF)
			continue;

		switch (firstchar)
		{
			case PqMsg_Query:
				{
					const char *query_string;

					/* Set statement_timestamp() */
					SetCurrentStatementStartTimestamp();

					query_string = pq_getmsgstring(&input_message);
					pq_getmsgend(&input_message);

					if (am_walsender)
					{
						if (!exec_replication_command(query_string))
							exec_simple_query(query_string);
					}
					else
						exec_simple_query(query_string);

					valgrind_report_error_query(query_string);

					send_ready_for_query = true;
				}
				break;
```

연결을 끝내는 메시지와 모르는 메시지다.

`tcop` / `postgres.c` L4964-L5026 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/tcop/postgres.c#L4964-L5026))

```c
// tcop/postgres.c L4964-L5026
			case PqMsg_Sync:
				pq_getmsgend(&input_message);

				/*
				 * If pipelining was used, we may be in an implicit
				 * transaction block. Close it before calling
				 * finish_xact_command.
				 */
				EndImplicitTransactionBlock();
				finish_xact_command();
				valgrind_report_error_query("SYNC message");
				send_ready_for_query = true;
				break;

				/*
				 * PqMsg_Terminate means that the frontend is closing down the
				 * socket. EOF means unexpected loss of frontend connection.
				 * Either way, perform normal shutdown.
				 */
			case EOF:

				/* for the cumulative statistics system */
				pgStatSessionEndCause = DISCONNECT_CLIENT_EOF;

				/* FALLTHROUGH */

			case PqMsg_Terminate:

				/*
				 * Reset whereToSendOutput to prevent ereport from attempting
				 * to send any more messages to client.
				 */
				if (whereToSendOutput == DestRemote)
					whereToSendOutput = DestNone;

// ... (L4999-L5005 생략: 주석)
				proc_exit(0);

			case PqMsg_CopyData:
			case PqMsg_CopyDone:
			case PqMsg_CopyFail:

// ... (L5012-L5016 생략: 주석)
				break;

			default:
				ereport(FATAL,
						(errcode(ERRCODE_PROTOCOL_VIOLATION),
						 errmsg("invalid frontend message type %d",
								firstchar)));
		}
	}							/* end of input-reading loop */
}
```

`ReadyForQuery` 는 한 바이트로 트랜잭션 상태를 알린다.

`tcop` / `dest.c` L256-L272 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/tcop/dest.c#L256-L272))

```c
// tcop/dest.c L256-L272
ReadyForQuery(CommandDest dest)
{
	switch (dest)
	{
		case DestRemote:
		case DestRemoteExecute:
		case DestRemoteSimple:
			{
				StringInfoData buf;

				pq_beginmessage(&buf, PqMsg_ReadyForQuery);
				pq_sendbyte(&buf, TransactionBlockStatusCode());
				pq_endmessage(&buf);
			}
			/* Flush output at end of cycle in any case. */
			pq_flush();
			break;
```

## 동작 흐름

```text
 L4217-L4256  신호 처리기
                SIGHUP  설정 다시 읽기     SIGINT  현재 쿼리 취소
                SIGTERM die               SIGQUIT quickdie
 L4259  BaseInit
 L4262  UnBlockSig                         초기 트랜잭션 중에도 SIGINT 등을 받는다
 L4269  DestRemote 면 취소 키 생성
          프로토콜 3.2 이상이면 MAX_CANCEL_KEY_LENGTH 바이트, 아니면 4 바이트
 L4293  [08] InitPostgres(dbname, InvalidOid, username, InvalidOid, ...)
 L4302  PostmasterContext 삭제             HBA 데이터도 여기서 사라진다
 L4308  NormalProcessing
 L4314  BeginReportingGUCOptions           ParameterStatus 메시지들
 L4332  BackendKeyData ('K'): pid + 취소 키   flush 는 ReadyForQuery 가 한다
 L4355  MessageContext 생성                메시지 한 바퀴마다 리셋되는 메모리
 L4373  EventTriggerOnLogin

 L4397  if (sigsetjmp(local_sigjmp_buf, 1) != 0)    ERROR 로 돌아온 경우만 들어간다
          타이머 해제, pq_comm_reset, EmitErrorReport (ErrorResponse 'E')
 L4453    AbortCurrentTransaction
 L4458    PortalErrorCleanup
 L4479    MessageContext 로 전환, FlushErrorState
 L4487    확장 프로토콜 도중이었으면 ignore_till_sync = true
 L4491    xact_started = false
 L4501    메시지를 읽던 중이었으면 FATAL (프로토콜 동기화 상실)
 L4511  PG_exception_stack = &local_sigjmp_buf   이제부터 ERROR 는 여기로 온다
 L4514  send_ready_for_query = true

 L4520  for (;;)
 L4543    MemoryContextReset(MessageContext)    지난 메시지의 메모리를 통째로 버린다
 L4569    send_ready_for_query 면
            트랜잭션 상태로 ps 표시: "idle in transaction (aborted)" / "idle in transaction" / "idle"
            해당하는 idle 타이머를 켠다
 L4687      ReadyForQuery                       'Z' + 'I' / 'T' / 'E', 그리고 flush
 L4697    DoingCommandRead = true
 L4702    firstchar = ReadCommand(&input_message)    여기서 블록된다
 L4712-L4721  idle 타이머를 끈다
 L4732    CHECK_FOR_INTERRUPTS                  쉬는 동안 온 취소는 여기서 무시된다
 L4739    SIGHUP 이 왔으면 설정 파일을 다시 읽는다
 L4749    ignore_till_sync 면 Sync 가 올 때까지 버린다
 L4752    switch (firstchar)
```

루프 한 바퀴는 메시지 하나다. 단순 질의 프로토콜에서 클라이언트가 보는 대화는 이렇게 된다.

```text
 연결 직후와 SELECT 한 번 (단순 질의 프로토콜)

 client                           backend
                                  [08] 인증 중  R (AuthenticationOk 등)
                         <-----   S ParameterStatus ... (L4314)
                         <-----   K BackendKeyData      (L4332)
                         <-----   Z ReadyForQuery 'I'   (L4687)  첫 바퀴
 Q "SELECT 1"            ----->   L4702 ReadCommand -> L4754 'Q'
                                  L4770 exec_simple_query  --> [쿼리 실행 파이프라인]
                         <-----     T RowDescription, D DataRow, C CommandComplete
                                  L4774 send_ready_for_query = true
                         <-----   Z ReadyForQuery 'I'   다음 바퀴 꼭대기
 X Terminate             ----->   L4990 proc_exit(0)
```

```text
 firstchar 별 분기 (protocol.h 의 PqMsg_*)

 byte    message       line         Z   하는 일
 'Q'     Query         L4754        Y   exec_simple_query
 'P'     Parse         L4778        N   exec_parse_message
 'B'     Bind          L4808        N   exec_bind_message
 'E'     Execute       L4823        N   exec_execute_message
 'F'     FunctionCall  L4843        Y   start_xact_command -> HandleFunctionRequest -> finish_xact_command
 'C'     Close         L4878        N   준비문 또는 포털 삭제
 'D'     Describe      L4924        N   준비문 또는 포털 설명
 'H'     Flush         L4958        N   pq_flush
 'S'     Sync          L4964        Y   EndImplicitTransactionBlock, finish_xact_command
 EOF 'X' Terminate     L4983-L5006  -   proc_exit(0)
 'd' 'c' 'f'  Copy*    L5008-L5017  N   무시 (실패한 COPY 의 잔여 데이터)
 other                 L5019        -   FATAL "invalid frontend message type"

 Z 열: Y 면 send_ready_for_query = true 로 다음 바퀴에 ReadyForQuery 를 보낸다

 확장 질의 프로토콜은 Sync 를 받을 때까지 ReadyForQuery 를 미룬다
 오류가 나면 ignore_till_sync 로 Sync 까지 오는 메시지를 버린다 (L4487, L4749)
```

```text
 ReadyForQuery 의 상태 바이트 (xact.c TransactionBlockStatusCode)

 'I'  TBLOCK_DEFAULT, TBLOCK_STARTED          트랜잭션 밖
 'T'  TBLOCK_INPROGRESS, TBLOCK_BEGIN 등       BEGIN 블록 안
 'E'  TBLOCK_ABORT 등                         실패한 블록 안 (ROLLBACK 만 받는다)

 L4571 / L4585 의 ps 표시와 같은 구분이다
```

```text
 ERROR 하나가 지나는 길

 exec_simple_query 깊숙한 곳에서 ereport(ERROR)
   -> elog.c 가 PG_exception_stack 으로 siglongjmp
   -> L4397 sigsetjmp 가 0 이 아닌 값으로 돌아온다
   -> ErrorResponse 전송, AbortCurrentTransaction
        BEGIN 블록 밖이었으면 트랜잭션이 사라지고 다음 'Z' 는 'I'
        BEGIN 블록 안이었으면 TBLOCK_ABORT 가 되어 다음 'Z' 는 'E'
   -> L4520 루프 꼭대기, send_ready_for_query 가 true 라 'Z'
 프로세스는 살아 있다. FATAL 이나 PANIC 만 backend 를 끝낸다
```

## 결과가 쓰이는 곳

```text
 'Q' 분기
      --> [쿼리 실행 파이프라인] exec_simple_query 가 문자열 하나를 끝까지 처리한다

 MessageContext
      --> exec_simple_query 의 파스 트리, 질의 트리, 계획이 여기 놓이고
          다음 바퀴 L4543 에서 한꺼번에 사라진다

 sigsetjmp 복구 지점
      --> AbortCurrentTransaction 이 [커밋] 흐름의 반대편, 트랜잭션 버리기를 한다

 ReadyForQuery 의 상태 바이트
      --> 드라이버가 트랜잭션 상태를 아는 유일한 근거다
```

## 다루지 않는 것

확장 질의 프로토콜 각 메시지의 처리(`exec_parse_message`, `exec_bind_message`, `exec_execute_message`, `exec_describe_*`), fastpath 함수 호출(`HandleFunctionRequest`), `SocketBackend` 의 메시지 길이 상한과 읽기, `ProcessInterrupts` 와 신호 처리기 내부, `LISTEN/NOTIFY` 알림 전달, 통계 보고 타이머, walsender 의 `exec_replication_command` 는 곁가지라 요약만 했다.
