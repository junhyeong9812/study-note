# BackendInitialize

상위: [연결과 backend 기동](../README.md)

자식 backend 가 **클라이언트와 처음 말을 주고받는** 구간이다. `Port` 를 만들고, `authentication_timeout` 시계를 건 채로 시작 패킷을 받고([06]), postmaster 가 넘겨 준 거절 판정(`cac`)이 있으면 **인증을 시작하기 전에** FATAL 로 끝낸다. 이 함수가 끝날 때까지 공유 메모리는 건드리지 않는다.

## 위치

`tcop` / `backend_startup.c` L141-L392 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/tcop/backend_startup.c#L141-L392))

## 실제 코드

`Port` 를 만들고, 시작 패킷 단계의 신호 처리를 바꿔 끼우는 앞부분이다.

`tcop` / `backend_startup.c` L141-L233 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/tcop/backend_startup.c#L141-L233))

```c
// tcop/backend_startup.c L141-L233
BackendInitialize(ClientSocket *client_sock, CAC_state cac)
{
	int			status;
	int			ret;
	Port	   *port;
	char		remote_host[NI_MAXHOST];
	char		remote_port[NI_MAXSERV];
	StringInfoData ps_data;
	MemoryContext oldcontext;

	/* Tell fd.c about the long-lived FD associated with the client_sock */
	ReserveExternalFD();

// ... (L154-L160 생략: PreAuthDelay 주석)
	if (PreAuthDelay > 0)
		pg_usleep(PreAuthDelay * 1000000L);

	/* This flag will remain set until InitPostgres finishes authentication */
	ClientAuthInProgress = true;	/* limit visibility of log messages */

	/*
	 * Initialize libpq and enable reporting of ereport errors to the client.
	 * Must do this now because authentication uses libpq to send messages.
	 *
	 * The Port structure and all data structures attached to it are allocated
	 * in TopMemoryContext, so that they survive into PostgresMain execution.
	 * We need not worry about leaking this storage on failure, since we
	 * aren't in the postmaster process anymore.
	 */
	oldcontext = MemoryContextSwitchTo(TopMemoryContext);
	port = MyProcPort = pq_init(client_sock);
	MemoryContextSwitchTo(oldcontext);

	whereToSendOutput = DestRemote; /* now safe to ereport to client */

	/* set these to empty in case they are needed before we set them up */
	port->remote_host = "";
	port->remote_port = "";

	/*
	 * We arrange to do _exit(1) if we receive SIGTERM or timeout while trying
	 * to collect the startup packet; while SIGQUIT results in _exit(2).
	 * Otherwise the postmaster cannot shutdown the database FAST or IMMED
	 * cleanly if a buggy client fails to send the packet promptly.
	 *
	 * Exiting with _exit(1) is only possible because we have not yet touched
	 * shared memory; therefore no outside-the-process state needs to get
	 * cleaned up.
	 */
	pqsignal(SIGTERM, process_startup_packet_die);
	/* SIGQUIT handler was already set up by InitPostmasterChild */
	InitializeTimeouts();		/* establishes SIGALRM handler */
	sigprocmask(SIG_SETMASK, &StartupBlockSig, NULL);

// ... (L201-L203 생략: 주석)
	remote_host[0] = '\0';
	remote_port[0] = '\0';
	if ((ret = pg_getnameinfo_all(&port->raddr.addr, port->raddr.salen,
								  remote_host, sizeof(remote_host),
								  remote_port, sizeof(remote_port),
								  (log_hostname ? 0 : NI_NUMERICHOST) | NI_NUMERICSERV)) != 0)
		ereport(WARNING,
				(errmsg_internal("pg_getnameinfo_all() failed: %s",
								 gai_strerror(ret))));

// ... (L214-L217 생략: 주석)
	port->remote_host = MemoryContextStrdup(TopMemoryContext, remote_host);
	port->remote_port = MemoryContextStrdup(TopMemoryContext, remote_port);

	/* And now we can log that the connection was received, if enabled */
	if (log_connections & LOG_CONNECTION_RECEIPT)
	{
		if (remote_port[0])
			ereport(LOG,
					(errmsg("connection received: host=%s port=%s",
							remote_host,
							remote_port)));
		else
			ereport(LOG,
					(errmsg("connection received: host=%s",
							remote_host)));
	}
```

시간 제한을 걸고 시작 패킷을 받은 뒤, postmaster 의 판정을 적용한다.

`tcop` / `backend_startup.c` L284-L348 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/tcop/backend_startup.c#L284-L348))

```c
// tcop/backend_startup.c L284-L348
	RegisterTimeout(STARTUP_PACKET_TIMEOUT, StartupPacketTimeoutHandler);
	enable_timeout_after(STARTUP_PACKET_TIMEOUT, AuthenticationTimeout * 1000);

	/* Handle direct SSL handshake */
	status = ProcessSSLStartup(port);

	/*
	 * Receive the startup packet (which might turn out to be a cancel request
	 * packet).
	 */
	if (status == STATUS_OK)
		status = ProcessStartupPacket(port, false, false);

	/*
	 * If we're going to reject the connection due to database state, say so
	 * now instead of wasting cycles on an authentication exchange. (This also
	 * allows a pg_ping utility to be written.)
	 */
	if (status == STATUS_OK)
	{
		switch (cac)
		{
			case CAC_STARTUP:
				ereport(FATAL,
						(errcode(ERRCODE_CANNOT_CONNECT_NOW),
						 errmsg("the database system is starting up")));
				break;
			case CAC_NOTHOTSTANDBY:
				if (!EnableHotStandby)
					ereport(FATAL,
							(errcode(ERRCODE_CANNOT_CONNECT_NOW),
							 errmsg("the database system is not accepting connections"),
							 errdetail("Hot standby mode is disabled.")));
				else if (reachedConsistency)
					ereport(FATAL,
							(errcode(ERRCODE_CANNOT_CONNECT_NOW),
							 errmsg("the database system is not yet accepting connections"),
							 errdetail("Recovery snapshot is not yet ready for hot standby."),
							 errhint("To enable hot standby, close write transactions with more than %d subtransactions on the primary server.",
									 PGPROC_MAX_CACHED_SUBXIDS)));
				else
					ereport(FATAL,
							(errcode(ERRCODE_CANNOT_CONNECT_NOW),
							 errmsg("the database system is not yet accepting connections"),
							 errdetail("Consistent recovery state has not been yet reached.")));
				break;
			case CAC_SHUTDOWN:
				ereport(FATAL,
						(errcode(ERRCODE_CANNOT_CONNECT_NOW),
						 errmsg("the database system is shutting down")));
				break;
			case CAC_RECOVERY:
				ereport(FATAL,
						(errcode(ERRCODE_CANNOT_CONNECT_NOW),
						 errmsg("the database system is in recovery mode")));
				break;
			case CAC_TOOMANY:
				ereport(FATAL,
						(errcode(ERRCODE_TOO_MANY_CONNECTIONS),
						 errmsg("sorry, too many clients already")));
				break;
			case CAC_OK:
				break;
		}
	}
```

시간 제한을 풀고, 실패나 취소 요청이면 조용히 끝내고, 아니면 프로세스 제목을 바꾼다.

`tcop` / `backend_startup.c` L350-L392 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/tcop/backend_startup.c#L350-L392))

```c
// tcop/backend_startup.c L350-L392
	/*
	 * Disable the timeout, and prevent SIGTERM again.
	 */
	disable_timeout(STARTUP_PACKET_TIMEOUT, false);
	sigprocmask(SIG_SETMASK, &BlockSig, NULL);

	/*
	 * As a safety check that nothing in startup has yet performed
	 * shared-memory modifications that would need to be undone if we had
	 * exited through SIGTERM or timeout above, check that no on_shmem_exit
	 * handlers have been registered yet.  (This isn't terribly bulletproof,
	 * since someone might misuse an on_proc_exit handler for shmem cleanup,
	 * but it's a cheap and helpful check.  We cannot disallow on_proc_exit
	 * handlers unfortunately, since pq_init() already registered one.)
	 */
	check_on_shmem_exit_lists_are_empty();

	/*
	 * Stop here if it was bad or a cancel packet.  ProcessStartupPacket
	 * already did any appropriate error reporting.
	 */
	if (status != STATUS_OK)
		proc_exit(0);

	/*
	 * Now that we have the user and database name, we can set the process
	 * title for ps.  It's good to do this as early as possible in startup.
	 */
	initStringInfo(&ps_data);
	if (am_walsender)
		appendStringInfo(&ps_data, "%s ", GetBackendTypeDesc(B_WAL_SENDER));
	appendStringInfo(&ps_data, "%s ", port->user_name);
	if (port->database_name[0] != '\0')
		appendStringInfo(&ps_data, "%s ", port->database_name);
	appendStringInfoString(&ps_data, port->remote_host);
	if (port->remote_port[0] != '\0')
		appendStringInfo(&ps_data, "(%s)", port->remote_port);

	init_ps_display(ps_data.data);
	pfree(ps_data.data);

	set_ps_display("initializing");
}
```

직접 TLS 연결인지 첫 바이트만 엿보는 쪽이다.

`tcop` / `backend_startup.c` L400-L423 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/tcop/backend_startup.c#L400-L423))

```c
// tcop/backend_startup.c L400-L423
static int
ProcessSSLStartup(Port *port)
{
	int			firstbyte;

	Assert(!port->ssl_in_use);

	pq_startmsgread();
	firstbyte = pq_peekbyte();
	pq_endmsgread();
	if (firstbyte == EOF)
	{
		/*
		 * Like in ProcessStartupPacket, if we get no data at all, don't
		 * clutter the log with a complaint.
		 */
		return STATUS_ERROR;
	}

	if (firstbyte != 0x16)
	{
		/* Not an SSL handshake message */
		return STATUS_OK;
	}
```

## 동작 흐름

```text
 L152  ReserveExternalFD                   클라이언트 소켓 fd 를 fd.c 에 알린다
 L161  PreAuthDelay 가 있으면 잠든다        디버거 붙이기용
 L165  ClientAuthInProgress = true         인증이 끝날 때까지 로그 노출을 제한

 L176-L178  TopMemoryContext 에서 pq_init(client_sock) -> port = MyProcPort
 L180  whereToSendOutput = DestRemote      이제부터 ereport 가 클라이언트로 간다

 L196  SIGTERM -> process_startup_packet_die   (_exit(1))
 L198  InitializeTimeouts                  SIGALRM 처리기
 L199  StartupBlockSig 로 신호 마스크 교체

 L206  pg_getnameinfo_all -> remote_host, remote_port   log_hostname 이면 역방향 DNS
 L222  log_connections 의 receipt 면 "connection received: host=... port=..."

 L284-L285  STARTUP_PACKET_TIMEOUT = AuthenticationTimeout * 1000 ms   (기본 60 초)
 L288  status = ProcessSSLStartup(port)
         첫 바이트를 엿보기만 한다. 0x16 (TLS 핸드셰이크) 이 아니면 STATUS_OK
         0x16 이면 바로 TLS 를 연다 (ALPN 필수)
 L295  status = [06] ProcessStartupPacket(port, false, false)

 L302  status 가 OK 면 cac 를 본다
         CAC_STARTUP / NOTHOTSTANDBY / SHUTDOWN / RECOVERY / TOOMANY  -> FATAL
         CAC_OK -> 통과

 L353  시간 제한 해제,  L354 BlockSig 로 되돌림
 L365  check_on_shmem_exit_lists_are_empty
 L371  status != OK (잘못된 패킷 또는 취소 요청) -> proc_exit(0)
 L378-L391  ps 제목: "[wal sender ]user database host(port)" 뒤 "initializing"
```

이 함수에서 연결이 끝나는 길은 다섯 가지다. 어느 길이든 공유 메모리는 아직 깨끗하다.

```text
 BackendInitialize 에서 끝나는 길

 어디서                          끝내는 방법        원인
 StartupPacketTimeoutHandler     _exit(1)           시작 패킷이 authentication_timeout 안에 안 옴
 process_startup_packet_die      _exit(1)           postmaster 가 SIGTERM (빠른 종료)
 L371                            proc_exit(0)       ProcessStartupPacket 이 STATUS_ERROR
                                                      (패킷이 깨짐, 취소 요청, 바이트 0)
 ProcessStartupPacket            FATAL              프로토콜 버전, user 없음 등. 클라이언트에 오류
 L304-L347                       FATAL              서버 상태로 거절 (cac). 클라이언트에 오류

 _exit(1) 이 허용되는 이유: 아직 공유 메모리를 건드리지 않아서
   프로세스 밖에 정리할 상태가 없다 (주석 L187-L195)
```

```text
 authentication_timeout 은 두 번 걸린다 (주석 L275-L278)

 BackendInitialize   STARTUP_PACKET_TIMEOUT   시작 패킷을 기다리는 동안   L285
 PerformAuthentication STATEMENT_TIMEOUT       인증 교환 동안             postinit.c L247

 그래서 악의적인 클라이언트는 거의 2 * 60 초 동안 backend 하나를 붙잡을 수 있다
```

## 결과가 쓰이는 곳

```text
 Port (MyProcPort)
      --> remote_host, remote_port  log_line_prefix 와 pg_stat_activity
      --> user_name, database_name  [04] BackendMain 이 PostgresMain 에 넘긴다
      --> ssl_in_use, gss          [09] 인증과 연결 로그

 whereToSendOutput = DestRemote
      --> 이후 모든 ereport 와 결과 전송이 클라이언트 소켓으로 간다

 ps 제목
      --> user=alice, database=shop, 10.0.0.5:51234 이면 "alice shop 10.0.0.5(51234)"
          를 init_ps_display 에 넘기고 상태를 "initializing" 으로 둔다 (값은 예시, 형식은 L379-L391)
```

## 다루지 않는 것

`pq_init` 이 만드는 송수신 버퍼, `secure_open_server` 의 TLS 핸드셰이크와 ALPN 협상, 역방향 DNS 와 `log_hostname`, 주입 지점(`INJECTION_POINT`) 테스트 경로, `init_ps_display` 의 플랫폼별 구현은 곁가지라 요약만 했다.
