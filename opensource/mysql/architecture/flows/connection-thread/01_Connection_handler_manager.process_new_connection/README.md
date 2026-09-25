# Connection_handler_manager.process_new_connection

상위: [연결과 스레드](../README.md)

리스너 스레드가 `accept` 한 연결을 받아 **연결 수를 올리고 핸들러에 넘기는** 열네 줄짜리 입구다. 볼거리는 `max_connections` 1차 검사가 인증보다 먼저, 리스너 스레드에서 일어난다는 점과 실패했을 때 `Channel_info` 를 누가 지우는지다.

## 위치

`sql` / `conn_handler` / `connection_handler_manager.cc` L256-L269 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/conn_handler/connection_handler_manager.cc#L256-L269))

## 실제 코드

```cpp
// connection_handler_manager.cc L256-L269
void Connection_handler_manager::process_new_connection(
    Channel_info *channel_info) {
  if (connection_events_loop_aborted() ||
      !check_and_incr_conn_count(channel_info->is_admin_connection(), false)) {
    channel_info->send_error_and_close_channel(ER_CON_COUNT_ERROR, 0, true);
    delete channel_info;
    return;
  }

  if (m_connection_handler->add_connection(channel_info)) {
    inc_aborted_connects();
    delete channel_info;
  }
}
```

연결 수를 검사하고 올리는 쪽이다. 검사와 증가가 같은 뮤텍스 안에 있다.

`sql` / `conn_handler` / `connection_handler_manager.cc` L106-L131 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/conn_handler/connection_handler_manager.cc#L106-L131))

```cpp
// connection_handler_manager.cc L106-L131
bool Connection_handler_manager::check_and_incr_conn_count(
    bool is_admin_connection, bool internal_session) {
  bool connection_accepted = true;
  mysql_mutex_lock(&LOCK_connection_count);
  /*
    Here we allow max_connections + 1 clients to connect
    (by checking before we increment by 1).

    The last connection is reserved for SUPER users. This is
    checked later during authentication where valid_connection_count()
    is called for non-SUPER users only.
  */
  if (connection_count > max_connections && !is_admin_connection) {
    connection_accepted = false;
    m_connection_errors_max_connection++;
  } else {
    ++connection_count;
    if (!internal_session) ++incoming_connection_count;
    if (connection_count > max_used_connections) {
      max_used_connections = connection_count;
      max_used_connections_time = time(nullptr);
    }
  }
  mysql_mutex_unlock(&LOCK_connection_count);
  return connection_accepted;
}
```

이 함수를 부르는 리스너 루프다.

`sql` / `conn_handler` / `connection_acceptor.h` L61-L68 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/conn_handler/connection_acceptor.h#L61-L68))

```cpp
// connection_acceptor.h L61-L68
  void connection_event_loop() {
    Connection_handler_manager *mgr =
        Connection_handler_manager::get_instance();
    while (!connection_events_loop_aborted()) {
      Channel_info *channel_info = m_listener->listen_for_connection_event();
      if (channel_info != nullptr) mgr->process_new_connection(channel_info);
    }
  }
```

## 동작 흐름

```text
 리스너 스레드에서 도는 것

 connection_acceptor.h L64  while (!connection_events_loop_aborted())
                      L65    channel_info = listen_for_connection_event()
                                poll(또는 select)로 기다리다 accept 한 소켓을
                                Channel_info 로 감싼다 (socket_connection.cc L1349)
                      L66    process_new_connection(channel_info)

 L258  서버가 종료 중이거나
 L259  check_and_incr_conn_count 가 거절하면
         L260  ER_CON_COUNT_ERROR 를 소켓에 바로 쓰고 닫는다 (senderror=true)
         L261  channel_info 를 지운다
         L262  return. 스레드도 THD 도 만들지 않는다

 L265  m_connection_handler->add_connection(channel_info)
         false  넘겼다. 이제 channel_info 는 연결 스레드 소유다
         true   실패. L266 aborted_connects++, L267 channel_info 를 지운다
```

`add_connection` 이 true 를 돌려주는 경로는 스레드 생성 실패뿐인데, 그때 `add_connection` 안에서 이미 오류를 보내고 연결 수도 내렸다. 여기서는 카운터와 메모리만 정리한다.

```text
 check_and_incr_conn_count 의 판정표 (L118)

 connection_count     admin   결과
 <= max_connections   -       통과, ++connection_count
 >  max_connections   no      거절, m_connection_errors_max_connection++
 >  max_connections   yes     통과, ++connection_count  (상한 없음)

 admin 은 admin 포트로 들어온 연결이다 (Channel_info::is_admin_connection)
 "올리기 전에" 보므로 일반 연결도 max_connections + 1 번째까지 여기를 통과한다
 그 한 자리를 누가 쓸 수 있는지는 인증 뒤에 정해진다
   [05] login_connection -> acl_authenticate
     -> check_restrictions_for_com_connect_command (sql_authentication.cc L3926-L3937)
```

```text
 이 함수가 끝났을 때 channel_info 의 주인

 path          count   channel_info 의 행방
 L260          +0      여기서 delete (거절)
 L265 false    +1      캐시 스레드를 깨웠으면 waiting 큐 -> 깨어난 스레드
 L265 false    +1      새 스레드를 만들었으면 handle_connection 의 인자
 L265 true     +0      여기서 delete (스레드 생성 실패, count 는 add_connection 이 되돌림)
```

## 결과가 쓰이는 곳

```text
 connection_count
      --> 연결 스레드가 끝날 때 dec_connection_count 로 내린다 ([03] L318)
      --> 인증 뒤 valid_connection_count 가 같은 값을 다시 본다
      --> 종료 시 wait_till_no_connection 이 0 이 되기를 기다린다

 max_used_connections
      --> 상태 변수 Max_used_connections 로 보인다 (mysqld.cc L11854)

 m_connection_errors_max_connection
      --> L120 에서 거절할 때마다 오른다
          이 흐름에서 스레드도 THD 도 없이 끝난 연결이 남기는 유일한 흔적이다

 channel_info
      --> [02] add_connection 으로 넘어간다
```

## 다루지 않는 것

`listen_for_connection_event` 가 준비된 리스닝 소켓을 고르고 `Channel_info` 를 만드는 과정, admin 포트를 별도 스레드로 받는 `handle_admin_socket`(socket_connection.cc L1058, 같은 함수를 L1151 에서 부른다), `m_connection_handler` 가 스레드 풀 플러그인으로 바뀌는 `load_connection_handler`(L233)는 연결 핸들러를 고르는 곁가지라 요약만 했다.
