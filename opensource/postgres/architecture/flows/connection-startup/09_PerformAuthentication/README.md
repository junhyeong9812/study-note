# PerformAuthentication

상위: [연결과 backend 기동](../README.md)

인증 교환을 **시간 제한으로 감싸는** 얇은 함수다. 실제 판정은 `ClientAuthentication`(libpq/auth.c)이 한다. `pg_hba.conf` 에서 이 연결에 맞는 규칙 한 줄을 찾고, 그 줄의 방법(trust, scram-sha-256, peer, ...)대로 클라이언트와 주고받은 뒤, 성공이면 `AuthenticationOk` 를 보내고 실패면 **돌아오지 않고 FATAL 로 끝낸다.** 이 함수에서 돌아왔다는 것 자체가 인증 성공이다.

## 위치

`utils` / `init` / `postinit.c` L194-L316 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/utils/init/postinit.c#L194-L316))

## 실제 코드

`utils` / `init` / `postinit.c` L194-L316 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/utils/init/postinit.c#L194-L316))

```c
// init/postinit.c L194-L316
PerformAuthentication(Port *port)
{
	/* This should be set already, but let's make sure */
	ClientAuthInProgress = true;	/* limit visibility of log messages */

// ... (L199-L237 생략: EXEC BACKEND 에서 pg hba.conf 다시 읽기)

	/* Capture authentication start time for logging */
	conn_timing.auth_start = GetCurrentTimestamp();

	/*
	 * Set up a timeout in case a buggy or malicious client fails to respond
	 * during authentication.  Since we're inside a transaction and might do
	 * database access, we have to use the statement_timeout infrastructure.
	 */
	enable_timeout_after(STATEMENT_TIMEOUT, AuthenticationTimeout * 1000);

	/*
	 * Now perform authentication exchange.
	 */
	set_ps_display("authentication");
	ClientAuthentication(port); /* might not return, if failure */

	/*
	 * Done with authentication.  Disable the timeout, and log if needed.
	 */
	disable_timeout(STATEMENT_TIMEOUT, false);

	/* Capture authentication end time for logging */
	conn_timing.auth_end = GetCurrentTimestamp();

	if (log_connections & LOG_CONNECTION_AUTHORIZATION)
	{
// ... (L265-L310 생략: 연결 인가 로그 문자열 조립)
	}

	set_ps_display("startup");

	ClientAuthInProgress = false;	/* client_min_messages is active now */
}
```

판정하는 쪽이다. `pg_hba.conf` 의 규칙을 고르고, 방법별로 갈라, 결과를 보낸다.

`libpq` / `auth.c` L379-L670 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/libpq/auth.c#L379-L670))

```c
// libpq/auth.c L379-L422
ClientAuthentication(Port *port)
{
	int			status = STATUS_ERROR;
	const char *logdetail = NULL;

	/*
	 * Get the authentication method to use for this frontend/database
	 * combination.  Note: we do not parse the file at this point; this has
	 * already been done elsewhere.  hba.c dropped an error message into the
	 * server logfile if parsing the hba config file failed.
	 */
	hba_getauthmethod(port);

	CHECK_FOR_INTERRUPTS();

	/*
	 * This is the first point where we have access to the hba record for the
	 * current connection, so perform any verifications based on the hba
	 * options field that should be done *before* the authentication here.
	 */
	if (port->hba->clientcert != clientCertOff)
	{
		/* If we haven't loaded a root certificate store, fail */
		if (!secure_loaded_verify_locations())
			ereport(FATAL,
					(errcode(ERRCODE_CONFIG_FILE_ERROR),
					 errmsg("client certificates can only be checked if a root certificate store is available")));

		/*
		 * If we loaded a root certificate store, and if a certificate is
		 * present on the client, then it has been verified against our root
		 * certificate store, and the connection would have been aborted
		 * already if it didn't verify ok.
		 */
		if (!port->peer_cert_valid)
			ereport(FATAL,
					(errcode(ERRCODE_INVALID_AUTHORIZATION_SPECIFICATION),
					 errmsg("connection requires a valid client certificate")));
	}

	/*
	 * Now proceed to do the actual authentication check
	 */
	switch (port->hba->auth_method)
```

```c
// libpq/auth.c L587-L670
		case uaMD5:
		case uaSCRAM:
			status = CheckPWChallengeAuth(port, &logdetail);
			break;

		case uaPassword:
			status = CheckPasswordAuth(port, &logdetail);
			break;

// ... (L596-L621 생략: PAM, BSD, LDAP, RADIUS)
		case uaCert:
			/* uaCert will be treated as if clientcert=verify-full (uaTrust) */
		case uaTrust:
			status = STATUS_OK;
			break;
		case uaOAuth:
			status = CheckSASLAuth(&pg_be_oauth_mech, port, NULL, NULL);
			break;
	}

	if ((status == STATUS_OK && port->hba->clientcert == clientCertFull)
		|| port->hba->auth_method == uaCert)
	{
		/*
		 * Make sure we only check the certificate if we use the cert method
		 * or verify-full option.
		 */
#ifdef USE_SSL
		status = CheckCertAuth(port);
#else
		Assert(false);
#endif
	}

// ... (L646-L661 생략: 인증 로그)

	if (ClientAuthentication_hook)
		(*ClientAuthentication_hook) (port, status);

	if (status == STATUS_OK)
		sendAuthRequest(port, AUTH_REQ_OK, NULL, 0);
	else
		auth_failed(port, status, logdetail);
}
```

## 동작 흐름

```text
 PerformAuthentication (postinit.c)
 L197  ClientAuthInProgress = true
 L205-L237  EXEC_BACKEND 면 pg_hba.conf, pg_ident.conf 를 직접 읽는다
              (fork 빌드는 postmaster 가 읽어 둔 것을 물려받는다)
 L240  conn_timing.auth_start
 L247  STATEMENT_TIMEOUT = AuthenticationTimeout * 1000   트랜잭션 안이므로 statement_timeout 장치를 쓴다
 L252  ps 표시 "authentication"
 L253  ClientAuthentication(port)        실패면 돌아오지 않는다
 L258  타이머 해제,  L261 auth_end
 L263  log_connections 의 authorization 이면
         "connection authorized: user=... database=... application_name=... SSL ..."
 L313  ps 표시 "startup"
 L315  ClientAuthInProgress = false      이제 client_min_messages 가 적용된다

 ClientAuthentication (auth.c)
 L390  hba_getauthmethod(port)           port->hba = 맞는 규칙 한 줄
 L399  clientcert 옵션이면 인증서 저장소와 클라이언트 인증서를 먼저 확인
 L422  switch (port->hba->auth_method)
 L632  성공했고 clientcert=verify-full 이거나 cert 방법이면 CheckCertAuth
 L663  ClientAuthentication_hook        확장 모듈이 결과(status)를 본다
 L666  성공 -> sendAuthRequest(AUTH_REQ_OK)     'R' 메시지
 L669  실패 -> auth_failed                     FATAL, 연결 종료
```

인증 방법은 `pg_hba.conf` 의 한 줄이 정한다. 이 함수의 `switch` 에 보이는 방법과 처리 함수를 나란히 놓으면 이렇다.

```text
 auth_method 별 처리 (auth.c L422-L630)

 method          handler                            line        비고
 reject          FATAL                              L424        명시적 거부 줄
 implicitreject  FATAL                              L472        맞는 줄이 없을 때
 gss, sspi       pg_GSS_* / pg_SSPI_*               L541, L566  GSSAPI / SSPI 교환
 peer            auth_peer                          L579        getpeereid 로 상대 OS 사용자
 ident           ident_inet                         L583        클라이언트 쪽 ident 서버에 묻는다
 md5, scram      CheckPWChallengeAuth               L587        md5 규칙이고 저장 형식도 md5 면 CheckMD5Auth,
                                                                아니면 SCRAM (L859-L862)
 password        CheckPasswordAuth                  L592        평문 비밀번호
 pam bsd ldap    CheckPAMAuth / CheckBSDAuth /      L596-L618   빌드 옵션에 따라
                 CheckLDAPAuth
 radius          CheckRADIUSAuth                    L619
 cert, trust     status = STATUS_OK                 L622-L626   cert 는 L632 에서 CheckCertAuth 를 더 한다
 oauth           CheckSASLAuth(&pg_be_oauth_mech)   L627
```

인증은 클라이언트와 여러 번 주고받을 수 있지만, 그 왕복은 모두 이 함수 안에서 끝난다. 메시지 루프는 아직 돌지 않는다.

```text
 scram-sha-256 연결 하나의 인증 구간 (시간 순)

 client                            backend
                                   [08] InitPostgres L847  트랜잭션 시작
                                   L247 STATEMENT_TIMEOUT 60 초 시작 (기본값)
                                   L390 hba_getauthmethod -> scram-sha-256
                         <------   R  AUTH_REQ_SASL (10)      auth-sasl.c L68
 p  SASLInitialResponse  ------>
                         <------   R  AUTH_REQ_SASL_CONT (11) auth-sasl.c L181
 p  SASLResponse         ------>
                         <------   R  AUTH_REQ_SASL_FIN (12)  auth-sasl.c L179
                         <------   R  AuthenticationOk       L667
                                   L258 타이머 해제
                                   [08] 로 돌아가 InitializeSessionUserId ...

 60 초 안에 끝나지 않으면 statement_timeout 처럼 취소되어 연결이 끝난다
 'p' 는 SASL 응답과 비밀번호 메시지가 함께 쓰는 바이트다 (protocol.h L30-L33)
```

## 결과가 쓰이는 곳

```text
 port->hba (맞은 규칙)
      --> InitializeSystemUser 가 인증 방법 이름을 system_user 로 남긴다 (postinit.c L903-L905)

 MyClientConnectionInfo.authn_id
      --> 인증된 신원. system_user 와 로그의 근거

 AuthenticationOk 전송
      --> 클라이언트는 이후 ParameterStatus, BackendKeyData, ReadyForQuery 를 기다린다 ([07])

 conn_timing.auth_start / auth_end
      --> [07] 의 첫 ReadyForQuery 에서 "connection ready: ... authentication=... ms" 로그
```

## 다루지 않는 것

`pg_hba.conf` 의 파싱과 줄 고르기(`load_hba`, `hba_getauthmethod`, `check_hba`), SCRAM 교환 세부(`CheckSASLAuth`, `pg_be_scram_mech`), LDAP/PAM/RADIUS/OAuth 각 방법의 내부, 실패 메시지를 고르는 `auth_failed`, `pg_ident.conf` 사용자 매핑은 이 흐름의 곁가지라 요약만 했다.
