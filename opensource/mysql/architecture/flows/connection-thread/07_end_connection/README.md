# end_connection

상위: [연결과 스레드](../README.md)

**인증을 통과한 연결만 지나는 종료 기록**이다. 소켓을 닫지는 않는다. 감사 플러그인에 끊김을 알리고, 사용자별 연결 수를 돌려주고, 이 연결이 정상 종료였는지 판정해 `Aborted_clients` 를 올린다. 소켓을 닫는 것은 다음 단계 [08] 이다.

## 위치

`sql` / `sql_connect.cc` L732-L770 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_connect.cc#L732-L770))

## 실제 코드

```cpp
// sql_connect.cc L732-L770
void end_connection(THD *thd) {
  NET *net = thd->get_protocol_classic()->get_net();

  mysql_event_tracking_connection_notify(
      thd, AUDIT_EVENT(EVENT_TRACKING_CONNECTION_DISCONNECT), 0);

#ifdef HAVE_PSI_THREAD_INTERFACE
  PSI_THREAD_CALL(notify_session_disconnect)(thd->get_psi());
#endif /* HAVE_PSI_THREAD_INTERFACE */

  plugin_thdvar_cleanup(thd, thd->m_enable_plugins);

  thd->release_external_store();

  /*
    The thread may returned back to the pool and assigned to a user
    that doesn't have a limit. Ensure the user is not using resources
    of someone else.
  */
  release_user_connection(thd);

  if (thd->killed || (net->error && net->vio != nullptr)) {
    aborted_threads++;
  }

  if (net->error && net->vio != nullptr) {
    if (!thd->killed) {
      Security_context *sctx = thd->security_context();
      const LEX_CSTRING sctx_user = sctx->user();
      LogErr(
          INFORMATION_LEVEL, ER_ABORTING_USER_CONNECTION, thd->thread_id(),
          (thd->db().str ? thd->db().str : "unconnected"),
          sctx_user.str ? sctx_user.str : "unauthenticated",
          sctx->host_or_ip().str,
          (thd->get_stmt_da()->is_error() ? thd->get_stmt_da()->message_text()
                                          : ER_DEFAULT(ER_UNKNOWN_ERROR)));
    }
  }
}
```

L751 이 돌려주는 사용자별 연결 수다. 그 사용자의 마지막 연결이면 항목 자체를 지운다.

`sql` / `sql_connect.cc` L271-L286 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_connect.cc#L271-L286))

```cpp
// sql_connect.cc L271-L286
void release_user_connection(THD *thd) {
  const USER_CONN *uc = thd->get_user_connect();
  DBUG_TRACE;

  if (uc) {
    mysql_mutex_lock(&LOCK_user_conn);
    assert(uc->connections > 0);
    thd->decrement_user_connections_counter();
    if (!uc->connections && !mqh_used) {
      /* Last connection for user; Delete it */
      hash_user_connections->erase(std::string(uc->user, uc->len));
    }
    mysql_mutex_unlock(&LOCK_user_conn);
    thd->set_user_connect(nullptr);
  }
}
```

## 동작 흐름

```text
 L735  감사 이벤트 DISCONNECT (sql_errno 0)
 L739  PSI 에 세션 끊김 알림
 L742  plugin_thdvar_cleanup                플러그인 세션 변수 정리
 L744  release_external_store
 L751  release_user_connection
         L276  LOCK_user_conn
         L278  이 사용자의 connections -1
         L279  0 이 되고 시간당 제한(mqh)을 안 쓰면 해시에서 지운다
         L284  thd 에서 USER_CONN 을 뗀다
 L753  killed 이거나 (net->error 이고 vio 가 있으면)  aborted_threads++
 L757  net->error 이고 vio 가 있는데 killed 가 아니면
         L761  ER_ABORTING_USER_CONNECTION 을 INFORMATION 로그로
```

`Aborted_clients` 는 "명령 루프를 어떻게 빠져나왔는가"로 정해진다. 루프를 빠져나온 길과 이 함수의 판정을 맞대면 아래와 같다.

```text
 루프를 빠져나온 길과 판정 (L753, L757)

 killed       net->error  Aborted_clients  log  빠져나온 길
 NOT_KILLED   unset (*)   X                X    COM_QUIT
 NOT_KILLED   set         O                O    클라이언트가 말없이 끊음 (읽기 실패)
 NOT_KILLED   set         O                O    wait_timeout 초과 (읽기 타임아웃)
 KILL_CONN    -           O                X    KILL CONNECTION, 서버 종료
 KILL_CONN    -           O                X    [06] 에서 준비 실패

 (*) COM_QUIT 처리에서 net->error = NET_ERROR_UNSET 으로 되돌린다 (sql_parse.cc L2352)
 net->vio == nullptr 이면 net->error 쪽 조건은 둘 다 거짓이 된다
```

읽기 실패와 읽기 타임아웃이 같은 줄에 서는 것은 서버 빌드의 `net_read_raw_loop` 가 둘 다 `net->error = NET_ERROR_SOCKET_NOT_READABLE` 로 끝내기 때문이다(sql-common/net_serv.cc L1449). 명령의 첫 패킷을 기다리다 시간이 다 된 경우는 그 직전에 `ER_CLIENT_INTERACTION_TIMEOUT` 으로 오류 번호를 바꾼다(L1421-L1423). 조건은 `net->pkt_nr == 0` 인데, `do_command` 가 명령마다 `net_new_transaction`(`include/mysql_com.h` L1091, `pkt_nr = 0`)을 부르므로(sql_parse.cc L1379) 연결의 첫 패킷이 아니라 **매 명령을 기다리는 첫 패킷**이다.

```text
 USER_CONN 의 짝

 얻는 곳   acl_authenticate L4412  get_or_create_user_conn
             (사용자 자원 제한이나 max_user_connections 이 있을 때만)
 돌려주는 곳
   정상     end_connection L751 (여기)
   인증 중 실패
            sql_authentication.cc L4454  check_restrictions_for_com_connect_command 실패
            sql_authentication.cc L4469  mysql_change_db 실패

 L746-L750 주석이 이것을 여기서 하는 까닭을 적어 두었다
   스레드가 풀로 돌아가 제한 없는 다른 사용자에게 배정될 수 있으니
   이 사용자의 자원을 쓰고 있지 않게 한다
```

## 결과가 쓰이는 곳

```text
 aborted_threads
      --> 상태 변수 Aborted_clients (mysqld.cc L11688)

 사용자별 연결 수 (hash_user_connections)
      --> 다음 연결의 check_for_max_user_connections 가 이 값을 본다

 감사 DISCONNECT 이벤트
      --> 감사 로그 플러그인이 받는다
      --> [08] close_connection 은 generate_event=false 로 불려 다시 내지 않는다
```

## 다루지 않는 것

`plugin_thdvar_cleanup` 이 플러그인 참조를 푸는 방식, `release_external_store`, 감사 이벤트 플러그인 API(`mysql_event_tracking_connection_notify`), 시간당 질의 수 제한(`mqh_used`, `check_mqh`)은 종료 기록의 곁가지라 요약만 했다.
