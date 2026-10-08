# ProcessStartupPacket

상위: [연결과 backend 기동](../README.md)

클라이언트가 보내는 **첫 패킷을 읽어 무엇인지 가르는** 함수다. 같은 꼴(길이 4바이트 + 코드 4바이트)의 패킷이 **취소 요청, SSL 협상, GSS 협상, 진짜 시작 패킷** 넷 중 하나이고, 협상 패킷이면 한 바이트로 답한 뒤 `goto retry` 로 다음 패킷을 다시 읽는다. 진짜 시작 패킷이면 `이름\0값\0` 쌍을 훑어 `Port` 의 user, database, 옵션을 채운다.

## 위치

`tcop` / `backend_startup.c` L492-L891 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/tcop/backend_startup.c#L492-L891))

## 실제 코드

길이를 읽고, 몸통을 읽고, 첫 4바이트로 종류를 가른다.

`tcop` / `backend_startup.c` L492-L573 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/tcop/backend_startup.c#L492-L573))

```c
// tcop/backend_startup.c L492-L573
ProcessStartupPacket(Port *port, bool ssl_done, bool gss_done)
{
	int32		len;
	char	   *buf;
	ProtocolVersion proto;
	MemoryContext oldcontext;

retry:
	pq_startmsgread();

	/*
	 * Grab the first byte of the length word separately, so that we can tell
	 * whether we have no data at all or an incomplete packet.  (This might
	 * sound inefficient, but it's not really, because of buffering in
	 * pqcomm.c.)
	 */
	if (pq_getbytes(&len, 1) == EOF)
	{
// ... (L510-L519 생략: 주석)
		return STATUS_ERROR;
	}

	if (pq_getbytes(((char *) &len) + 1, 3) == EOF)
	{
		/* Got a partial length word, so bleat about that */
		if (!ssl_done && !gss_done)
			ereport(COMMERROR,
					(errcode(ERRCODE_PROTOCOL_VIOLATION),
					 errmsg("incomplete startup packet")));
		return STATUS_ERROR;
	}

	len = pg_ntoh32(len);
	len -= 4;

	if (len < (int32) sizeof(ProtocolVersion) ||
		len > MAX_STARTUP_PACKET_LENGTH)
	{
		ereport(COMMERROR,
				(errcode(ERRCODE_PROTOCOL_VIOLATION),
				 errmsg("invalid length of startup packet")));
		return STATUS_ERROR;
	}

	/*
	 * Allocate space to hold the startup packet, plus one extra byte that's
	 * initialized to be zero.  This ensures we will have null termination of
	 * all strings inside the packet.
	 */
	buf = palloc(len + 1);
	buf[len] = '\0';

	if (pq_getbytes(buf, len) == EOF)
	{
		ereport(COMMERROR,
				(errcode(ERRCODE_PROTOCOL_VIOLATION),
				 errmsg("incomplete startup packet")));
		return STATUS_ERROR;
	}
	pq_endmsgread();

	/*
	 * The first field is either a protocol version number or a special
	 * request code.
	 */
	port->proto = proto = pg_ntoh32(*((ProtocolVersion *) buf));

	if (proto == CANCEL_REQUEST_CODE)
	{
		ProcessCancelRequestPacket(port, buf, len);
		/* Not really an error, but we don't want to proceed further */
		return STATUS_ERROR;
	}
```

SSL 협상 요청이면 `'S'` 나 `'N'` 한 바이트로 답하고 처음으로 돌아간다. GSS 협상(L647-L714)도 같은 모양이다.

`tcop` / `backend_startup.c` L575-L646 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/tcop/backend_startup.c#L575-L646))

```c
// tcop/backend_startup.c L575-L646
	if (proto == NEGOTIATE_SSL_CODE && !ssl_done)
	{
		char		SSLok;

#ifdef USE_SSL

		/*
		 * No SSL when disabled or on Unix sockets.
		 *
		 * Also no SSL negotiation if we already have a direct SSL connection
		 */
		if (!LoadedSSL || port->laddr.addr.ss_family == AF_UNIX || port->ssl_in_use)
			SSLok = 'N';
		else
			SSLok = 'S';		/* Support for SSL */
#else
		SSLok = 'N';			/* No support for SSL */
#endif

// ... (L594-L602 생략: Trace connection negotiation 로그)

		while (secure_write(port, &SSLok, 1) != 1)
		{
			if (errno == EINTR)
				continue;		/* if interrupted, just retry */
			ereport(COMMERROR,
					(errcode_for_socket_access(),
					 errmsg("failed to send SSL negotiation response: %m")));
			return STATUS_ERROR;	/* close the connection */
		}

#ifdef USE_SSL
		if (SSLok == 'S' && secure_open_server(port) == -1)
			return STATUS_ERROR;
#endif

		/*
		 * At this point we should have no data already buffered.  If we do,
		 * it was received before we performed the SSL handshake, so it wasn't
		 * encrypted and indeed may have been injected by a man-in-the-middle.
		 * We report this case to the client.
		 */
		if (pq_buffer_remaining_data() > 0)
			ereport(FATAL,
					(errcode(ERRCODE_PROTOCOL_VIOLATION),
					 errmsg("received unencrypted data after SSL request"),
					 errdetail("This could be either a client-software bug or evidence of an attempted man-in-the-middle attack.")));

		/*
		 * regular startup packet, cancel, etc packet should follow, but not
		 * another SSL negotiation request, and a GSS request should only
		 * follow if SSL was rejected (client may negotiate in either order)
		 */
		ssl_done = true;
		if (SSLok == 'S')
		{
			/*
			 * We are done with SSL and negotiated correctly, so consider the
			 * same for GSS.
			 */
			gss_done = true;
		}
		goto retry;
	}
```

진짜 시작 패킷이다. 버전을 확인하고 이름-값 쌍을 `Port` 에 옮긴다.

`tcop` / `backend_startup.c` L716-L891 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/tcop/backend_startup.c#L716-L891))

```c
// tcop/backend_startup.c L716-L891
	/* Could add additional special packet types here */

	/*
	 * Set FrontendProtocol now so that ereport() knows what format to send if
	 * we fail during startup. We use the protocol version requested by the
	 * client unless it's higher than the latest version we support. It's
	 * possible that error message fields might look different in newer
	 * protocol versions, but that's something those new clients should be
	 * able to deal with.
	 */
	FrontendProtocol = Min(proto, PG_PROTOCOL_LATEST);

	/* Check that the major protocol version is in range. */
	if (PG_PROTOCOL_MAJOR(proto) < PG_PROTOCOL_MAJOR(PG_PROTOCOL_EARLIEST) ||
		PG_PROTOCOL_MAJOR(proto) > PG_PROTOCOL_MAJOR(PG_PROTOCOL_LATEST))
		ereport(FATAL,
				(errcode(ERRCODE_FEATURE_NOT_SUPPORTED),
				 errmsg("unsupported frontend protocol %u.%u: server supports %u.0 to %u.%u",
						PG_PROTOCOL_MAJOR(proto), PG_PROTOCOL_MINOR(proto),
						PG_PROTOCOL_MAJOR(PG_PROTOCOL_EARLIEST),
						PG_PROTOCOL_MAJOR(PG_PROTOCOL_LATEST),
						PG_PROTOCOL_MINOR(PG_PROTOCOL_LATEST))));

	/*
	 * Now fetch parameters out of startup packet and save them into the Port
	 * structure.
	 */
	oldcontext = MemoryContextSwitchTo(TopMemoryContext);

	/* Handle protocol version 3 startup packet */
	{
		int32		offset = sizeof(ProtocolVersion);
		List	   *unrecognized_protocol_options = NIL;

		/*
		 * Scan packet body for name/option pairs.  We can assume any string
		 * beginning within the packet body is null-terminated, thanks to
		 * zeroing extra byte above.
		 */
		port->guc_options = NIL;

		while (offset < len)
		{
			char	   *nameptr = buf + offset;
			int32		valoffset;
			char	   *valptr;

			if (*nameptr == '\0')
				break;			/* found packet terminator */
			valoffset = offset + strlen(nameptr) + 1;
			if (valoffset >= len)
				break;			/* missing value, will complain below */
			valptr = buf + valoffset;

			if (strcmp(nameptr, "database") == 0)
				port->database_name = pstrdup(valptr);
			else if (strcmp(nameptr, "user") == 0)
				port->user_name = pstrdup(valptr);
			else if (strcmp(nameptr, "options") == 0)
				port->cmdline_options = pstrdup(valptr);
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
			else if (strncmp(nameptr, "_pq_.", 5) == 0)
			{
// ... (L800-L804 생략: 주석)
				unrecognized_protocol_options =
					lappend(unrecognized_protocol_options, pstrdup(nameptr));
			}
			else
			{
				/* Assume it's a generic GUC option */
				port->guc_options = lappend(port->guc_options,
											pstrdup(nameptr));
				port->guc_options = lappend(port->guc_options,
											pstrdup(valptr));

				/*
				 * Copy application_name to port if we come across it.  This
				 * is done so we can log the application_name in the
				 * connection authorization message.  Note that the GUC would
				 * be used but we haven't gone through GUC setup yet.
				 */
				if (strcmp(nameptr, "application_name") == 0)
				{
					port->application_name = pg_clean_ascii(valptr, 0);
				}
			}
			offset = valoffset + strlen(valptr) + 1;
		}

		/*
		 * If we didn't find a packet terminator exactly at the end of the
		 * given packet length, complain.
		 */
		if (offset != len - 1)
			ereport(FATAL,
					(errcode(ERRCODE_PROTOCOL_VIOLATION),
					 errmsg("invalid startup packet layout: expected terminator as last byte")));

		/*
		 * If the client requested a newer protocol version or if the client
		 * requested any protocol options we didn't recognize, let them know
		 * the newest minor protocol version we do support and the names of
		 * any unrecognized options.
		 */
		if (PG_PROTOCOL_MINOR(proto) > PG_PROTOCOL_MINOR(PG_PROTOCOL_LATEST) ||
			unrecognized_protocol_options != NIL)
			SendNegotiateProtocolVersion(unrecognized_protocol_options);
	}

	/* Check a user name was given. */
	if (port->user_name == NULL || port->user_name[0] == '\0')
		ereport(FATAL,
				(errcode(ERRCODE_INVALID_AUTHORIZATION_SPECIFICATION),
				 errmsg("no PostgreSQL user name specified in startup packet")));

	/* The database defaults to the user name. */
	if (port->database_name == NULL || port->database_name[0] == '\0')
		port->database_name = pstrdup(port->user_name);

	/*
	 * Truncate given database and user names to length of a Postgres name.
	 * This avoids lookup failures when overlength names are given.
	 */
	if (strlen(port->database_name) >= NAMEDATALEN)
		port->database_name[NAMEDATALEN - 1] = '\0';
	if (strlen(port->user_name) >= NAMEDATALEN)
		port->user_name[NAMEDATALEN - 1] = '\0';

	if (am_walsender)
		MyBackendType = B_WAL_SENDER;
	else
		MyBackendType = B_BACKEND;

	/*
	 * Normal walsender backends, e.g. for streaming replication, are not
	 * connected to a particular database. But walsenders used for logical
	 * replication need to connect to a specific database. We allow streaming
	 * replication commands to be issued even if connected to a database as it
	 * can make sense to first make a basebackup and then stream changes
	 * starting from that.
	 */
	if (am_walsender && !am_db_walsender)
		port->database_name[0] = '\0';

	/*
	 * Done filling the Port structure
	 */
	MemoryContextSwitchTo(oldcontext);

	return STATUS_OK;
}
```

패킷 종류를 가르는 코드값과 길이 상한이다.

`src` / `include` / `libpq` / `pqcomm.h` L90-L173 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/libpq/pqcomm.h#L90-L173))

```c
// libpq/pqcomm.h L90-L97
#define PG_PROTOCOL(m,n)	(((m) << 16) | (n))

/*
 * The earliest and latest frontend/backend protocol version supported.
 */

#define PG_PROTOCOL_EARLIEST	PG_PROTOCOL(3,0)
#define PG_PROTOCOL_LATEST		PG_PROTOCOL(3,2)
```

```c
// libpq/pqcomm.h L118-L118
#define MAX_STARTUP_PACKET_LENGTH 10000
```

```c
// libpq/pqcomm.h L137-L137
#define CANCEL_REQUEST_CODE PG_PROTOCOL(1234,5678)
```

```c
// libpq/pqcomm.h L172-L173
#define NEGOTIATE_SSL_CODE PG_PROTOCOL(1234,5679)
#define NEGOTIATE_GSS_CODE PG_PROTOCOL(1234,5680)
```

## 동작 흐름

```text
 L499  retry:
 L508  길이의 첫 바이트를 따로 읽는다 -> EOF 면 조용히 STATUS_ERROR
         (모니터링 도구가 열었다 닫는 연결은 흔하다. 주석 L511-L518)
 L523  나머지 3 바이트 -> 모자라면 "incomplete startup packet"
 L533  len = ntoh(len) - 4                  길이 필드 자신을 뺀다
 L536  len < 4 또는 len > 10000 이면 "invalid length of startup packet"
 L550  buf = palloc(len + 1), buf[len] = '\0'   안의 문자열이 반드시 끝나게
 L553  몸통 len 바이트를 읽는다
 L566  proto = 첫 4 바이트

 L568  CANCEL_REQUEST_CODE   -> ProcessCancelRequestPacket, STATUS_ERROR (더 진행 안 함)
 L575  NEGOTIATE_SSL_CODE    -> 'S' 또는 'N' 1 바이트 응답, 'S' 면 TLS 시작
         L625  협상 전에 버퍼에 남은 평문이 있으면 FATAL (중간자 의심)
         L636  ssl_done = true (성공이면 gss_done 도), goto retry
 L647  NEGOTIATE_GSS_CODE    -> 'G' 또는 'N', 같은 방식으로 goto retry

 L726  FrontendProtocol = min(proto, 3.2)
 L729  주 버전이 3 이 아니면 FATAL "unsupported frontend protocol"
 L757  while (offset < len)  이름\0값\0 쌍 훑기
         database / user / options / replication / _pq_.* / 그 밖은 GUC
 L834  끝 바이트가 정확히 len - 1 이 아니면 FATAL
 L845  부 버전이 더 높거나 모르는 _pq_ 옵션이 있으면 NegotiateProtocolVersion 응답
 L851  user 가 없으면 FATAL
 L857  database 가 없으면 user 이름을 쓴다
 L864-L867  NAMEDATALEN(64) 이상이면 잘라낸다
 L869  am_walsender 면 MyBackendType = B_WAL_SENDER
 L882  물리 복제 walsender 면 database_name 을 비운다
```

같은 꼴의 패킷이 네 가지 뜻을 가진다. 구분은 두 번째 4바이트의 코드값이다.

```text
 첫 패킷의 모양 (모든 정수는 네트워크 바이트 순서)

 +--------+--------+---------------------------------------+
 | len    | code   | 몸통                                  |
 | 4 B    | 4 B    | len - 8 B                             |
 +--------+--------+---------------------------------------+

 code 값 (PG_PROTOCOL(m,n) = m << 16 | n, pqcomm.h L90)
   PG_PROTOCOL(3,0)        = 196608     시작 패킷, 프로토콜 3.0
   PG_PROTOCOL(3,2)        = 196610     시작 패킷, 프로토콜 3.2 (LATEST)
   PG_PROTOCOL(1234,5678)  = 80877102   CancelRequest
   PG_PROTOCOL(1234,5679)  = 80877103   SSLRequest
   PG_PROTOCOL(1234,5680)  = 80877104   GSSENCRequest

 주 버전이 1234 인 코드는 실제 프로토콜 버전과 겹치지 않는다
```

시작 패킷 몸통을 훑는 과정을 예시 값으로 따라가면 이렇다. 끝 검사(L834)가 왜 `len - 1` 인지 보인다.

```text
 user=alice, database=shop 인 3.0 시작 패킷

 byte     0-3      4-7       8-12    13-18    19-27       28-32   33
 content  len=34   196608    user\0  alice\0  database\0  shop\0  \0

 L533  len = 34 - 4 = 30       buf 는 바이트 4..33 을 담는다 (buf[0..29])
 L747  offset = 4              buf 안에서 이름 쌍이 시작하는 자리

 offset  name        valoffset              value    next offset
 4       "user"      4 + 4 + 1  = 9         "alice"  9 + 5 + 1  = 15
 15      "database"  15 + 8 + 1 = 24        "shop"   24 + 4 + 1 = 29
 29      buf[29] == '\0' -> break (L763-L764)

 L834  offset(29) == len - 1 (29) -> 통과
         끝의 '\0' 하나가 정확히 마지막 바이트여야 한다
```

```text
 SSL 을 먼저 협상하는 흔한 순서 (클라이언트 sslmode=prefer 등)

 client                             backend (이 함수)
 SSLRequest (80877103)   ------>    L575  ssl_done 아님
                         <------    L604  'S'
 TLS 핸드셰이크          <----->    L615  secure_open_server
                                    L625  평문 잔여 확인
                                    L636-L645  ssl_done = gss_done = true, goto retry
 StartupMessage (196608) ------>    L566  이번엔 시작 패킷
                                    L757-L828  user, database, 옵션
                                    STATUS_OK -> [05] 로 돌아가 cac 검사
```

## 결과가 쓰이는 곳

```text
 port->user_name, port->database_name
      --> [04] BackendMain -> [07] PostgresMain -> [08] InitPostgres 의 인자

 port->guc_options, port->cmdline_options
      --> InitPostgres 의 process_startup_options 가 세션 GUC 로 적용한다 (postinit.c L1197)
          superuser 인지 알아야 하므로 인증 뒤에야 적용된다 (postinit.c L1192-L1194 주석)

 am_walsender, am_db_walsender
      --> InitProcess 가 walsenderFreeProcs 에서 PGPROC 를 꺼내게 한다
      --> PostgresMain 의 'Q' 가 exec_replication_command 로 간다

 FrontendProtocol, port->proto
      --> 오류 메시지 형식, 취소 키 길이 (3.2 이상이면 긴 키, postgres.c L4273-L4274)
```

## 다루지 않는 것

취소 요청 처리(`ProcessCancelRequestPacket` 이 대상 backend 를 찾아 신호를 보내는 과정), TLS/GSSAPI 핸드셰이크 내부, `SendNegotiateProtocolVersion` 응답 형식, `options` 문자열의 명령행 스위치 파싱(`pg_split_opts`)은 곁가지라 요약만 했다.
