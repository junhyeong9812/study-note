# close_connection

상위: [연결과 스레드](../README.md)

**소켓을 실제로 끊는 자리다.** 인증에 실패한 연결도, 정상 종료한 연결도 [03] L308 에서 반드시 여기를 지난다. 연결 스레드가 자기 연결을 닫을 때와 서버 종료 스레드가 남의 연결을 닫을 때 같은 함수를 쓰는데, 인자로 역할을 가른다. 볼거리는 네 인자의 조합과 `THD::disconnect` 가 `killed` 를 세우는 방식이다.

## 위치

`sql` / `sql_connect.cc` L917-L933 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_connect.cc#L917-L933))

## 실제 코드

```cpp
// sql_connect.cc L917-L933
void close_connection(THD *thd, uint sql_errno, bool server_shutdown,
                      bool generate_event) {
  DBUG_TRACE;

  if (sql_errno) net_send_error(thd, sql_errno, ER_DEFAULT_NONCONST(sql_errno));
  thd->disconnect(server_shutdown);

  if (generate_event) {
    mysql_event_tracking_connection_notify(
        thd, AUDIT_EVENT(EVENT_TRACKING_CONNECTION_DISCONNECT), sql_errno);
#ifdef HAVE_PSI_THREAD_INTERFACE
    PSI_THREAD_CALL(notify_session_disconnect)(thd->get_psi());
#endif /* HAVE_PSI_THREAD_INTERFACE */
  }

  thd->security_context()->logout();
}
```

`thd->disconnect` 가 하는 일이다. `LOCK_thd_data` 안에서 사망 표시를 하고 Vio 를 닫는다.

`sql` / `sql_class.cc` L1730-L1772 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_class.cc#L1730-L1772))

```cpp
// sql_class.cc L1730-L1772
void THD::disconnect(bool server_shutdown) {
  Vio *vio = nullptr;

  mysql_mutex_lock(&LOCK_thd_data);

  /* Shutdown clone vio always, to wake up clone waiting for remote. */
  shutdown_clone_vio();

  /*
    If thread is in kill immune mode (i.e. operation on new DD tables
    is in progress) then just save state_to_set with THD::kill_immunizer
    object.

    While exiting kill immune mode, awake() is called again with the killed
    state saved in THD::kill_immunizer object.

    active_vio is already associated to the thread when it is in the kill
    immune mode. THD::awake() closes the active_vio.
   */
  if (kill_immunizer != nullptr)
    kill_immunizer->save_killed_state(THD::KILL_CONNECTION);
  else {
    killed = THD::KILL_CONNECTION;

    /*
      Since a active vio might might have not been set yet, in
      any case save a reference to avoid closing a inexistent
      one or closing the vio twice if there is a active one.
    */
    vio = active_vio;
    shutdown_active_vio();

    /* Disconnect even if a active vio is not associated. */
    if (is_classic_protocol() && get_protocol_classic()->get_vio() != vio &&
        get_protocol_classic()->connection_alive()) {
      DBUG_EXECUTE_IF("assert_only_current_thd_protocol_access",
                      { assert(current_thd == this); });
      m_protocol->shutdown(server_shutdown);
    }
  }

  mysql_mutex_unlock(&LOCK_thd_data);
}
```

서버 종료 때 다른 스레드가 이 함수를 부르는 자리다.

`sql` / `mysqld.cc` L2377-L2390 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/mysqld.cc#L2377-L2390))

```cpp
// mysqld.cc L2377-L2390
  void operator()(THD *closing_thd) override {
    if (closing_thd->get_protocol()->connection_alive()) {
      LEX_CSTRING main_sctx_user = closing_thd->m_main_security_ctx.user();
      LogErr(WARNING_LEVEL, ER_FORCE_CLOSE_THREAD, my_progname,
             (long)closing_thd->thread_id(),
             (main_sctx_user.length ? main_sctx_user.str : ""));
      /*
        Do not generate EVENT_TRACKING_CONNECTION_DISCONNECT event, when closing
        thread close sessions. Each session will generate DISCONNECT event by
        itself.
      */
      close_connection(closing_thd, 0, is_server_shutdown, false);
    }
  }
```

## 동작 흐름

```text
 L921  sql_errno 가 있으면 net_send_error        끊기 전에 마지막 오류를 보낸다
 L922  thd->disconnect(server_shutdown)
         sql_class.cc L1733  LOCK_thd_data
                      L1736  clone 용 Vio 도 깨운다
                      L1749  kill immune 모드면 KILL_CONNECTION 을 저장만 해 둔다
                      L1752  아니면 killed = KILL_CONNECTION
                      L1759  active_vio 를 기억하고
                      L1760  shutdown_active_vio
                      L1763  프로토콜의 Vio 가 active_vio 와 다르고 아직 살아 있으면
                      L1767    m_protocol->shutdown 으로 그것도 끊는다
 L924  generate_event 면 감사 DISCONNECT 이벤트와 PSI 알림
 L932  security_context()->logout()
```

같은 함수를 부르는 곳이 넷이고, 인자 조합이 부르는 쪽의 역할을 드러낸다.

```text
 호출처와 인자 (close_connection(thd, sql_errno, server_shutdown, generate_event))

 호출처                                   sql_errno            shutdown   event  부르는 스레드
 connection_handler_per_thread.cc L308       0                    false      false  자기 연결 스레드
 connection_handler_one_thread.cc L89        0                    false      false  자기 (no-threads 모드)
 mysqld.cc L2388  Call_close_conn            0                    true       false  종료 스레드 (남의 THD)
 bootstrap.cc L322                           ER_OUT_OF_RESOURCES  false(*)   true(*) 부트스트랩

 [03] 은 generate_event=false 로 부른다
   인증까지 마친 연결의 DISCONNECT 이벤트는 [07] end_connection 이 이미 냈다 (L735)
   인증에 실패한 연결은 CONNECT 이벤트(L653)만 남고 DISCONNECT 이벤트 없이 닫힌다
 Call_close_conn 이 false 로 부르는 까닭은 주석이 적어 두었다 (mysqld.cc L2383-L2387)
   각 세션이 스스로 DISCONNECT 이벤트를 낸다
```

(*) `bootstrap.cc` 는 뒤 두 인자를 생략한다. 기본값은 `server_shutdown = false`, `generate_event = true` 다(sql_connect.h L105-L106).

서버 종료 때는 종료 스레드가 남의 THD 를 닫는다. `close_connections`(mysqld.cc L2424)는 캐시에 잠든 스레드를 먼저 내보내고(L2434), 모든 THD 에 KILL 을 건 뒤(L2458-L2459), 그래도 남은 연결에 `Call_close_conn` 을 돌린다(L2495-L2496).

```text
 서버 종료 때 두 스레드가 한 THD 를 닫는 순서 (시간축)

 종료 스레드                                   연결 스레드 T (do_command 에서 읽기 대기 중)
 close_connections
 L2459  Set_kill_conn 으로 모든 THD 에 killed = KILL_CONNECTION
        (L2350, 표시와 cond broadcast 만 한다. 소켓은 닫지 않는다)
   (기다린 뒤에도 남아 있으면)
 L2496  Call_close_conn
          L2378  connection_alive 확인
          L2388  close_connection(T 의 thd, 0, true, false)
                   disconnect: LOCK_thd_data
                   killed = KILL_CONNECTION
                   shutdown_active_vio  -------->  읽고 있던 소켓이 닫힌다
                   logout                           do_command 가 돌아오면
                                                    [03] L303 thd_connection_alive -> false
                                                    [07] end_connection
                                                    [08] close_connection (T 가 직접, 두 번째)
                                                    L339 connection_events_loop_aborted 면
                                                         스레드도 끝낸다
```

연결 스레드가 깨어나는 근거는 두 곳이다. `vio_shutdown` 이 소켓에 `shutdown(SHUT_RDWR)` 를 건다(vio/viosocket.cc L492). `close_connections` 의 주석(mysqld.cc L2485-L2489)이 이 단계를 "클라이언트의 명령을 기다리며 blocking read 중인 스레드를 중단시키려고" 연결을 닫는다고 적어 두었다.

한 THD 에 `close_connection` 이 두 번 불릴 수 있고, 두 번째 `disconnect` 는 같은 표시를 다시 세울 뿐이다. `active_vio` 는 첫 번째에서 이미 nullptr 이 되었고, `m_protocol->shutdown` 이 부르는 `vio_shutdown` 은 이미 `inactive` 인 Vio 에서는 소켓을 건드리지 않는다(vio/viosocket.cc L487). 함수 주석(L913-L914)도 "종료를 수행하는 연결에서는 이 함수가 두 번 불린다"고 적어 두었다.

## 결과가 쓰이는 곳

```text
 thd->killed = KILL_CONNECTION
      --> 연결 스레드가 루프 안에 있었다면 thd_connection_alive 가 false 가 된다
      --> THD::cleanup 도 같은 표시를 세운다 (sql_class.cc L1331)

 닫힌 Vio
      --> [03] L311 release_resources 가 vio_delete 로 지운다 (sql_class.cc L1457-L1458)

 logout
      --> Security_context 의 로그인 상태를 끝낸다
```

## 다루지 않는 것

`THD::awake` 로 KILL 이 연결을 끊는 경로와 kill immune 모드(`kill_immunizer`), `shutdown_active_vio` 와 `Protocol::shutdown` 의 소켓 처리, `close_connections` 가 종료 시 THD 목록을 도는 순서, `Security_context::logout` 의 내용은 연결을 닫는 일의 곁가지라 요약만 했다.
