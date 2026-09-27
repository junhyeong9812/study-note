# login_connection

상위: [연결과 스레드](../README.md)

**연결이 사용자가 되는 자리다.** 자신은 타임아웃을 `connect_timeout` 으로 바꿔 끼우고 결과 패킷을 보내는 일만 하고, 실제 일은 안에서 부르는 `check_connection` 이 한다. 그 안에서 호스트 확인, 핸드셰이크, 인증 플러그인 교체, 계정 검사가 차례로 일어나고, 어디서 떨어지든 결과는 오류 하나와 true 하나다.

## 위치

`sql` / `sql_connect.cc` L698-L723 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_connect.cc#L698-L723))

## 실제 코드

```cpp
// sql_connect.cc L698-L723
static bool login_connection(THD *thd) {
  int error;
  DBUG_TRACE;
  DBUG_PRINT("info",
             ("login_connection called by thread %u", thd->thread_id()));

  /* Use "connect_timeout" value during connection phase */
  Protocol_classic *protocol = thd->get_protocol_classic();
  protocol->set_read_timeout(connect_timeout, true);
  protocol->set_write_timeout(connect_timeout);

  error = check_connection(thd);
  thd->send_statement_status();

  if (error) {  // Wrong permissions
#ifdef _WIN32
    if (vio_type(protocol->get_vio()) == VIO_TYPE_NAMEDPIPE)
      my_sleep(1000); /* must wait after eof() */
#endif
    return true;
  }
  /* Connect completed, set read/write timeouts back to default */
  protocol->set_read_timeout(thd->variables.net_read_timeout);
  protocol->set_write_timeout(thd->variables.net_write_timeout);
  return false;
}
```

`check_connection` 의 앞부분은 TCP 연결의 호스트를 확인한다. 아래는 그 끝과 Unix socket 쪽 갈래다.

`sql` / `sql_connect.cc` L610-L627 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_connect.cc#L610-L627))

```cpp
// sql_connect.cc L610-L627
    if (acl_check_host(thd, thd->m_main_security_ctx.host().str,
                       main_sctx_ip.str)) {
      /* HOST_CACHE stats updated by acl_check_host(). */
      my_error(ER_HOST_NOT_PRIVILEGED, MYF(0),
               thd->m_main_security_ctx.host_or_ip().str);
      return 1;
    }
  } else /* Hostname given means that the connection was on a socket */
  {
    LEX_CSTRING main_sctx_host = thd->m_main_security_ctx.host();
    DBUG_PRINT("info", ("Host: %s", main_sctx_host.str));
    thd->m_main_security_ctx.set_host_or_ip_ptr(main_sctx_host.str,
                                                main_sctx_host.length);
    thd->m_main_security_ctx.set_ip_ptr(STRING_WITH_LEN(""));
    /* Reset sin_addr */
    memset(&net->vio->remote, 0, sizeof(net->vio->remote));
  }
  vio_keepalive(net->vio, true);
```

`check_connection` 의 뒷부분이다. 인증 앞뒤로 감사 이벤트를 하나씩 낸다.

`sql` / `sql_connect.cc` L646-L681 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_connect.cc#L646-L681))

```cpp
// sql_connect.cc L646-L681
  if (mysql_event_tracking_connection_notify(
          thd, AUDIT_EVENT(EVENT_TRACKING_CONNECTION_PRE_AUTHENTICATE))) {
    return 1;
  }

  auth_rc = acl_authenticate(thd, COM_CONNECT);

  if (mysql_event_tracking_connection_notify(
          thd, AUDIT_EVENT(EVENT_TRACKING_CONNECTION_CONNECT))) {
    return 1;
  }

#ifdef HAVE_PSI_THREAD_INTERFACE
  if (auth_rc == 0) {
    PSI_THREAD_CALL(notify_session_connect)(thd->get_psi());
  }
#endif /* HAVE_PSI_THREAD_INTERFACE */

  if (auth_rc == 0 && connect_errors != 0) {
    /*
      A client connection from this IP was successful,
      after some previous failures.
      Reset the connection error counter.
    */
    reset_host_connect_errors(thd->m_main_security_ctx.ip().str);
  }

  /*
    Now that acl_authenticate() is executed,
    the SSL info is available.
    Advertise it to THD, so SSL status variables
    can be inspected.
  */
  thd->set_ssl(net->vio);
  return auth_rc;
}
```

`acl_authenticate` 의 첫머리다. 기본 플러그인으로 한 번 시도하고, 사용자의 플러그인이 다르면 한 번 더 시도한다.

`sql` / `auth` / `sql_authentication.cc` L4098-L4138 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/auth/sql_authentication.cc#L4098-L4138))

```cpp
// sql_authentication.cc L4098-L4138
  } else {
    /* mark the thd as having no scramble yet */
    mpvio.scramble[SCRAMBLE_LENGTH] = 1;

    /*
     perform the first authentication attempt, with the default plugin.
     This sends the server handshake packet, reads the client reply
     with a user name, and performs the authentication if everyone has used
     the correct plugin.
    */

    res = do_auth_once(thd, auth_plugin_name, &mpvio);
  }

  /*
   retry the authentication, if - after receiving the user name -
   we found that we need to switch to a non-default plugin
  */
  if (mpvio.status == MPVIO_EXT::RESTART) {
    assert(mpvio.acl_user);
    assert(command == COM_CHANGE_USER ||
           my_strcasecmp(system_charset_info, auth_plugin_name.str,
                         mpvio.acl_user->plugin.str));
    auth_plugin_name = mpvio.acl_user->plugin;
    res = do_auth_once(thd, auth_plugin_name, &mpvio);
  }

  if (res == CR_OK_FORCE_PASSWORD_CHANGE) {
    password_change_directive_from_plugin = true;
    /*
      Set to CR_OK so that rest of the logic remains unchanged.
      When it is time to set the password expired flat in
      Security context, password_change_directive_from_plugin
      will be used.
    */
    res = CR_OK;
  }

  if (res == CR_OK) {
    res = do_multi_factor_auth(thd, &mpvio);
  }
```

`RESTART` 가 켜지는 자리다. 클라이언트의 응답 패킷을 파싱하다가 사용자의 플러그인이 서버 기본값과 다르면 파싱을 멈춘다.

`sql` / `auth` / `sql_authentication.cc` L3300-L3308 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/auth/sql_authentication.cc#L3300-L3308))

```cpp
// sql_authentication.cc L3300-L3308
  if (my_strcasecmp(system_charset_info, mpvio->acl_user_plugin.str,
                    plugin_name(mpvio->plugin)->str) != 0) {
    /* Server default plugin didn't match user plugin */
    mpvio->cached_client_reply.pkt = passwd;
    mpvio->cached_client_reply.pkt_len = passwd_len;
    mpvio->cached_client_reply.plugin = client_plugin;
    mpvio->status = MPVIO_EXT::RESTART;
    return packet_error;
  }
```

## 동작 흐름

```text
 login_connection

 L706-L707  읽기, 쓰기 타임아웃을 connect_timeout 으로
 L709       error = check_connection(thd)
 L710       send_statement_status          성공이면 OK 패킷, 실패면 오류 패킷이 여기서 나간다
 L712       error 면 true
 L720-L721  타임아웃을 세션의 net_read_timeout, net_write_timeout 으로 되돌린다
            (명령을 기다리는 동안은 do_command 가 wait_timeout 으로 다시 바꾼다)
```

`check_connection` 은 연결 방식에 따라 두 갈래로 시작해 인증에서 합친다.

```text
 check_connection (sql_connect.cc L440-L681)

 L450  set_active_vio                       KILL 이 이 Vio 를 끊을 수 있게 등록
 L452  security_ctx 에 host 가 비어 있으면 TCP/IP
 |       L459  vio_peer_addr                  상대 IP, 포트
 |             실패 -> ER_BAD_HOST_ERROR (L521)
 |       L524  IP 를 security_ctx 에
 |       L537  skip-name-resolve 가 아니면
 |               L556  ip_to_hostname           역방향 DNS + 호스트 캐시
 |               L592  너무 긴 이름 -> ER_HOSTNAME_TOO_LONG
 |               L597  차단된 호스트 -> ER_HOST_IS_BLOCKED
 |       L610  acl_check_host                   이 호스트에서 오는 계정이 하나라도 있나
 |             없으면 ER_HOST_NOT_PRIVILEGED (L613)
 +-- 아니면 Unix socket 등 (L617)
         host 를 그대로 쓰고 IP 는 빈 문자열
 L627  keepalive
 L629  출력 버퍼 할당 (net_buffer_length)
 L646  감사 이벤트 PRE_AUTHENTICATE          플러그인이 거부하면 여기서 끝
 L651  acl_authenticate(thd, COM_CONNECT)   <-- 아래 그림
 L653  감사 이벤트 CONNECT
 L664  성공인데 이 IP 에 이전 실패가 있었으면 호스트 캐시의 실패 수를 지운다
 L679  set_ssl
```

핸드셰이크는 서버가 먼저 말한다. 서버는 사용자를 모르는 채로 기본 플러그인(`caching_sha2_password`, sql_authentication.cc L1207)의 데이터를 첫 패킷에 싣는다.

```text
 인증 단계의 패킷 교환과 분기 (acl_authenticate, sql_authentication.cc L4050)

 서버 (연결 스레드)                                          클라이언트
 L4068  server_mpvio_initialize
 L4109  do_auth_once(기본 플러그인)
          플러그인이 첫 write_packet 을 부르면
          L3419-L3421  packets_written == 0
                       -> Initial Handshake 에 실어 보낸다 ---->
                                                   <---- (선택) SSL 요청
          L3061-L3076  CLIENT_SSL 이면 sslaccept           TLS 로 바뀐다
                                                   <---- Handshake Response
                                                         (사용자, 플러그인 이름, 인증 데이터, db)
          parse_client_handshake_packet (L2975)
            L3233  find_mpvio_user                     사용자 계정을 찾는다
            L3300  계정의 플러그인 != 서버 기본 플러그인 ?
            |        맞으면 응답을 cached_client_reply 에 보관
            |        L3306  status = RESTART, 파싱 중단
            +--      아니면 같은 플러그인이 이어서 검증

 L4116  status == RESTART 면
 L4121    auth_plugin_name = 계정의 플러그인
 L4122    do_auth_once 한 번 더
            이번 write_packet 은 L3422-L3430 에서
            Auth Switch Request 로 나간다 ------------------------>
                                                   <---- 새 플러그인의 응답
 L4125  CR_OK_FORCE_PASSWORD_CHANGE 는 CR_OK 로 바꾸고 표시만 남긴다
 L4136  CR_OK 면 do_multi_factor_auth              2, 3 번째 인증 수단
```

플러그인이 통과시킨 뒤에도 계정 단위 검사가 여러 겹 남아 있다. 하나라도 걸리면 `goto end` 로 빠지고 반환값은 1 이다.

```text
 인증 뒤 검사 (acl_authenticate, 위에서 아래로)

 L4192  플러그인 결과가 실패               실패 종류별 호스트 캐시 오류 수를 올린다 (L4195-L4217)
 L4229  --skip-grant-tables 가 아니면
          L4239  프록시 사용자 찾기          프록시면 대상 계정의 권한으로 바꾼다
          L4294  set_master_access         전역 권한을 security_ctx 에
          L4296  기본 역할 활성화
          L4328  offline_mode 인데 관리자 아님   -> 거절
          L4339  acl_check_ssl             계정의 REQUIRE SSL / X509 조건
          L4350  계정 잠김                  -> ER_ACCOUNT_HAS_BEEN_LOCKED
          L4374  require_secure_transport 인데 안전하지 않은 전송 -> 거절
          L4383  비밀번호 만료이고 클라이언트가 만료를 못 다룸 -> 거절
          L4407  사용자별 자원 제한이 있으면 get_or_create_user_conn
 L4436  사용자별 연결 수 제한                  check_for_max_user_connections
 L4452  COM_CONNECT 면 check_restrictions_for_com_connect_command
          admin 포트인데 SERVICE_CONNECTION_ADMIN 없음 -> 거절
          권한 없는 사용자인데 max_connections 초과    -> ER_CON_COUNT_ERROR
 L4466  접속 시 db 를 지정했으면 mysql_change_db
 L4485  my_ok                                 OK 패킷 준비 (보내는 것은 L710)
 L4496  ret = 0
```

```text
 실패가 어디에 남는가 (앞 셋은 sql_connect.cc, 뒤 셋은 sql_authentication.cc)

 line   error                       host cache       상황
 L521   ER_BAD_HOST_ERROR           -                상대 주소를 못 얻음
 L599   ER_HOST_IS_BLOCKED          ip_to_hostname   차단된 호스트
 L613   ER_HOST_NOT_PRIVILEGED      acl_check_host   이 호스트에서 오는 계정 없음
 L4217  (플러그인별)                     inc_host_errors  플러그인 인증 실패
 L4356  ER_ACCOUNT_HAS_BEEN_LOCKED  inc_host_errors  계정 잠김
 L3935  ER_CON_COUNT_ERROR          -                권한 없는 사용자의 max_connections 초과

 어느 경우든 check_connection 이 0 이 아닌 값을 돌려주고 [04] 가 true 를 받는다
 aborted_connects 는 여기서 올리지 않는다. true 를 받은 [03] L301 이 올린다
```

## 결과가 쓰이는 곳

```text
 thd->m_main_security_ctx
      --> 사용자, 호스트, 전역 권한, 활성 역할이 채워진다
      --> 이후 모든 권한 검사의 출발점이다

 thd->get_user_connect() (USER_CONN)
      --> [07] end_connection 의 release_user_connection 이 돌려준다

 OK 패킷 또는 오류 패킷
      --> L710 send_statement_status 로 클라이언트에 나간다

 타임아웃
      --> 성공이면 net_read_timeout, net_write_timeout 으로 돌아간다
```

## 다루지 않는 것

`caching_sha2_password` 의 fast/full 인증 교환과 RSA 키, `do_multi_factor_auth`(L3677)의 단계, `COM_CHANGE_USER` 로 같은 연결에서 재인증하는 갈래(L4082), `parse_client_handshake_packet` 의 패킷 필드 해석과 문자셋 협상, 호스트 캐시(`ip_to_hostname`, `inc_host_errors`)의 차단 규칙, 프록시 사용자와 역할 활성화의 세부, 네트워크 네임스페이스(`HAVE_SETNS`) 처리는 인증의 곁가지라 요약만 했다.
