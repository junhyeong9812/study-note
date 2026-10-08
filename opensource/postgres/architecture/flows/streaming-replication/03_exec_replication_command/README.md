# exec_replication_command

상위: [스트리밍 복제](../README.md)

**walsender 가 받은 질의 문자열을 복제 명령 문법으로 파싱해 갈래로 보내는 함수다.** walsender 는 따로 태어나는 프로세스가 아니다. 보통 backend 와 똑같이 fork 되고, 시작 패킷의 `replication=true` 하나 때문에 `am_walsender` 가 켜진 채 같은 `PostgresMain` 루프를 돈다. 그 루프의 `'Q'` 분기가 SQL 대신 이 함수를 먼저 부르는 것이 갈림길이다.

## 위치

`replication` / `walsender.c` L2012-L2261 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/walsender.c#L2012-L2261))

## 실제 코드

시작 패킷의 `replication` 값이 `am_walsender` 를 켠다. 물리 복제면 데이터베이스 이름을 지운다.

`tcop` / `backend_startup.c` L776-L797 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/tcop/backend_startup.c#L776-L797))

```c
// tcop/backend_startup.c L776-L797
			else if (strcmp(nameptr, "replication") == 0)
			{
// ... (L778-L784 생략: 주석)
				if (strcmp(valptr, "database") == 0)
				{
					am_walsender = true;
					am_db_walsender = true;
				}
				else if (!parse_bool(valptr, &am_walsender))
					ereport(FATAL,
							(errcode(ERRCODE_INVALID_PARAMETER_VALUE),
							 errmsg("invalid value for parameter \"%s\": \"%s\"",
									"replication",
									valptr),
							 errhint("Valid values are: \"false\", 0, \"true\", 1, \"database\".")));
			}
```

`tcop` / `backend_startup.c` L869-L883 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/tcop/backend_startup.c#L869-L883))

```c
// tcop/backend_startup.c L869-L883
	if (am_walsender)
		MyBackendType = B_WAL_SENDER;
	else
		MyBackendType = B_BACKEND;

// ... (L874-L881 생략: 주석)
	if (am_walsender && !am_db_walsender)
		port->database_name[0] = '\0';
```

인증 뒤 REPLICATION 속성을 검사하고, 물리 walsender 는 데이터베이스에 붙지 않고 초기화를 끝낸다.

`utils/init` / `postinit.c` L955-L977 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/utils/init/postinit.c#L955-L977))

```c
// utils/init/postinit.c L955-L977
	if (am_walsender)
	{
		Assert(!bootstrap);

		if (!has_rolreplication(GetUserId()))
			ereport(FATAL,
					(errcode(ERRCODE_INSUFFICIENT_PRIVILEGE),
					 errmsg("permission denied to start WAL sender"),
					 errdetail("Only roles with the %s attribute may start a WAL sender process.",
							   "REPLICATION")));
	}

// ... (L967-L972 생략: 주석)
	if (am_walsender && !am_db_walsender)
	{
		/* process any options passed in the startup packet */
		if (MyProcPort != NULL)
			process_startup_options(MyProcPort, am_superuser);
```

메시지 루프의 `'Q'` 가 갈라지는 자리다. 복제 명령이 아니면 `false` 를 돌려 SQL 로 처리하게 한다.

`tcop` / `postgres.c` L4764-L4770 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/tcop/postgres.c#L4764-L4770))

```c
// tcop/postgres.c L4764-L4770
					if (am_walsender)
					{
						if (!exec_replication_command(query_string))
							exec_simple_query(query_string);
					}
					else
						exec_simple_query(query_string);
```

복제 명령인지 먼저 확인하고, 맞으면 파싱한다.

`replication` / `walsender.c` L2012-L2107 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/walsender.c#L2012-L2107))

```c
// replication/walsender.c L2012-L2107
exec_replication_command(const char *cmd_string)
{
	yyscan_t	scanner;
	int			parse_rc;
	Node	   *cmd_node;
	const char *cmdtag;
	MemoryContext old_context = CurrentMemoryContext;

	/* We save and re-use the cmd_context across calls */
	static MemoryContext cmd_context = NULL;

// ... (L2023-L2026 생략: 주석)
	if (got_STOPPING)
		WalSndSetState(WALSNDSTATE_STOPPING);

// ... (L2030-L2034 생략: 주석)
	if (MyWalSnd->state == WALSNDSTATE_STOPPING)
		ereport(ERROR,
				(errcode(ERRCODE_OBJECT_NOT_IN_PREREQUISITE_STATE),
				 errmsg("cannot execute new commands while WAL sender is in stopping mode")));

// ... (L2040-L2046 생략: 논리 복제 스냅샷 정리와 인터럽트 확인)

// ... (L2048-L2065 생략: 주석)
	if (cmd_context == NULL)
		cmd_context = AllocSetContextCreate(TopMemoryContext,
											"Replication command context",
											ALLOCSET_DEFAULT_SIZES);
	else
		MemoryContextReset(cmd_context);

	MemoryContextSwitchTo(cmd_context);

	replication_scanner_init(cmd_string, &scanner);

	/*
	 * Is it a WalSender command?
	 */
	if (!replication_scanner_is_replication_command(scanner))
	{
		/* Nope; clean up and get out. */
		replication_scanner_finish(scanner);

		MemoryContextSwitchTo(old_context);
		MemoryContextReset(cmd_context);

		/* XXX this is a pretty random place to make this check */
		if (MyDatabaseId == InvalidOid)
			ereport(ERROR,
					(errcode(ERRCODE_FEATURE_NOT_SUPPORTED),
					 errmsg("cannot execute SQL commands in WAL sender for physical replication")));

		/* Tell the caller that this wasn't a WalSender command. */
		return false;
	}

	/*
	 * Looks like a WalSender command, so parse it.
	 */
	parse_rc = replication_yyparse(&cmd_node, scanner);
	if (parse_rc != 0)
		ereport(ERROR,
				(errcode(ERRCODE_SYNTAX_ERROR),
				 errmsg_internal("replication command parser returned %d",
								 parse_rc)));
	replication_scanner_finish(scanner);
```

명령 종류로 가른다. `START_REPLICATION` 이 물리 복제면 [04] 로 간다.

`replication` / `walsender.c` L2128-L2215 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/walsender.c#L2128-L2215))

```c
// replication/walsender.c L2128-L2215
	if (IsAbortedTransactionBlockState())
		ereport(ERROR,
				(errcode(ERRCODE_IN_FAILED_SQL_TRANSACTION),
				 errmsg("current transaction is aborted, "
						"commands ignored until end of transaction block")));

// ... (L2134-L2143 생략: 인터럽트 확인과 송수신 버퍼 할당)
	switch (cmd_node->type)
	{
		case T_IdentifySystemCmd:
			cmdtag = "IDENTIFY_SYSTEM";
			set_ps_display(cmdtag);
			IdentifySystem();
			EndReplicationCommand(cmdtag);
			break;

// ... (L2153-L2159 생략: READ_REPLICATION_SLOT)
		case T_BaseBackupCmd:
			cmdtag = "BASE_BACKUP";
			set_ps_display(cmdtag);
			PreventInTransactionBlock(true, cmdtag);
			SendBaseBackup((BaseBackupCmd *) cmd_node, uploaded_manifest);
			EndReplicationCommand(cmdtag);
			break;

		case T_CreateReplicationSlotCmd:
			cmdtag = "CREATE_REPLICATION_SLOT";
			set_ps_display(cmdtag);
			CreateReplicationSlot((CreateReplicationSlotCmd *) cmd_node);
			EndReplicationCommand(cmdtag);
			break;

// ... (L2175-L2188 생략: DROP, ALTER_REPLICATION_SLOT)
		case T_StartReplicationCmd:
			{
				StartReplicationCmd *cmd = (StartReplicationCmd *) cmd_node;

				cmdtag = "START_REPLICATION";
				set_ps_display(cmdtag);
				PreventInTransactionBlock(true, cmdtag);

				if (cmd->kind == REPLICATION_KIND_PHYSICAL)
					StartReplication(cmd);
				else
					StartLogicalReplication(cmd);

				/* dupe, but necessary per libpqrcv_endstreaming */
				EndReplicationCommand(cmdtag);

				Assert(xlogreader != NULL);
				break;
			}

		case T_TimeLineHistoryCmd:
			cmdtag = "TIMELINE_HISTORY";
			set_ps_display(cmdtag);
			PreventInTransactionBlock(true, cmdtag);
			SendTimeLineHistory((TimeLineHistoryCmd *) cmd_node);
			EndReplicationCommand(cmdtag);
			break;
```

## 동작 흐름

```text
 primary 쪽, 연결 하나가 walsender 가 되기까지 ([연결과 backend 기동] 과 같은 길)

 walreceiver 의 walrcv_connect  (시작 패킷: user, replication=true, application_name ...)
      |
      v
 postmaster ServerLoop -> BackendStartup -> fork         보통 연결과 똑같다
      |
      v
 ProcessStartupPacket                           backend_startup.c
   L776  "replication" 옵션
   L790    parse_bool -> am_walsender = true    ("database" 면 논리 복제용 am_db_walsender)
   L869  MyBackendType = B_WAL_SENDER
   L882  물리 walsender 면 database_name = ""
      |
      v
 PostgresMain                                   postgres.c
   L4217  am_walsender 면 WalSndSignals          신호 처리기가 다르다
   L4293  InitPostgres
            postinit.c L955  REPLICATION 속성이 없으면 FATAL
            postinit.c L973  물리 walsender 면 데이터베이스 없이 초기화 끝
   L4326  InitWalSender                         WalSnd 슬롯 확보, postmaster 에 walsender 라고 알림
   L4520  for (;;)
   L4754    'Q'
   L4764    am_walsender 면
              exec_replication_command(query)
                false -> exec_simple_query       SQL 이면 (데이터베이스가 없으면 L2089 에서 ERROR)
                true  -> 끝                      복제 명령이었다
```

walreceiver 가 보내는 명령은 차례가 정해져 있다. 둘 다 이 함수를 지나지만, `START_REPLICATION` 만은 돌아오지 않고 [05] 의 루프에 머문다.

```text
 walreceiver call                  command                                   branch               line
 walrcv_identify_system            IDENTIFY_SYSTEM                           IdentifySystem       L2146
 walrcv_readtimelinehistoryfile    TIMELINE_HISTORY n                        SendTimeLineHistory  L2209
 walrcv_create_slot                CREATE_REPLICATION_SLOT s TEMPORARY
                                     PHYSICAL (RESERVE_WAL)                  CreateReplicationSlot L2168
 walrcv_startstreaming             START_REPLICATION [SLOT s] X/X TIMELINE n
                                     kind == PHYSICAL                        [04] StartReplication  L2198
                                     otherwise                               StartLogicalReplication L2200
```

```text
 이 함수가 막는 것

 L2035  walsender 가 STOPPING 상태      새 명령 전부 ERROR (종료 체크포인트 중 WAL 생성 방지)
 L2089  복제 명령이 아닌데 데이터베이스가 없음   "cannot execute SQL commands in WAL sender for physical replication"
 L2128  실패한 트랜잭션 블록 안          ERROR
 L2195  트랜잭션 블록 안의 START_REPLICATION   PreventInTransactionBlock 이 ERROR
```

## 결과가 쓰이는 곳

```text
 output_message, reply_message, tmpbuf (L2140-L2142)
      --> [05] [06] [11] 이 송수신 버퍼로 그대로 쓴다

 T_StartReplicationCmd 의 startpoint, timeline, slotname
      --> [04] StartReplication 의 cmd 인자

 L2203 EndReplicationCommand
      --> 스트리밍이 끝나 [04] 가 돌아온 뒤 CommandComplete 를 보낸다
```

## 다루지 않는 것

복제 명령 문법(`repl_gram.y`, `repl_scanner.l`), `IDENTIFY_SYSTEM` 과 `TIMELINE_HISTORY` 의 결과 형식, 슬롯 생성과 삭제(`CreateReplicationSlot`, `DropReplicationSlot`), `BASE_BACKUP`, 논리 복제(`StartLogicalReplication`), `InitWalSender` 와 `WalSndSignals` 의 내부는 요약만 했다. 연결이 backend 가 되는 길 전체는 [연결과 backend 기동](../../connection-startup/README.md)에 있다.
