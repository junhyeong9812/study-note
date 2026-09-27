# do_command

상위: [명령 디스패치](../README.md)

**연결 스레드가 클라이언트의 다음 명령을 기다리는 유일한 자리다.** 소켓에서 패킷 하나를 읽어 첫 바이트를 명령 번호로 해석하고 [02] `dispatch_command` 에 넘긴다. 볼거리는 두 가지다. 기다리는 동안과 읽는 동안의 타임아웃이 다르다는 것, 그리고 읽기 실패의 종류에 따라 연결을 끊을지 이어 갈지 갈린다는 것이다.

## 위치

`sql` / `sql_parse.cc` L1347-L1500 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_parse.cc#L1347-L1500))

## 실제 코드

앞부분이다. 이전 명령의 오류를 지우고, 다음 명령을 기다리는 동안의 타임아웃을 건다.

`sql` / `sql_parse.cc` L1347-L1379 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_parse.cc#L1347-L1379))

```cpp
// sql_parse.cc L1347-L1379
bool do_command(THD *thd) {
  bool return_value;
  int rc;
  NET *net = nullptr;
  enum enum_server_command command = COM_SLEEP;
  COM_DATA com_data;
  DBUG_TRACE;
  assert(thd->is_classic_protocol());

  /*
    indicator of uninitialized lex => normal flow of errors handling
    (see my_message_sql)
  */
  thd->lex->set_current_query_block(nullptr);

  /*
    XXX: this code is here only to clear possible errors of init_connect.
    Consider moving to prepare_new_connection_state() instead.
    That requires making sure the DA is cleared before non-parsing statements
    such as COM_QUIT.
  */
  thd->clear_error();  // Clear error message
  thd->get_stmt_da()->reset_diagnostics_area();

  /*
    This thread will do a blocking read from the client which
    will be interrupted when the next command is received from
    the client, the connection is closed or "net_wait_timeout"
    number of seconds has passed.
  */
  net = thd->get_protocol_classic()->get_net();
  my_net_set_read_timeout(net, thd->variables.net_wait_timeout);
  net_new_transaction(net);
```

패킷을 읽는다. 여기서 스레드가 블록되고, 실패하면 오류 패킷을 보낸 뒤 돌아간다.

`sql` / `sql_parse.cc` L1413-L1465 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_parse.cc#L1413-L1465))

```cpp
// sql_parse.cc L1413-L1465
  rc = thd->m_mem_cnt.reset();
  if (rc)
    thd->m_mem_cnt.set_thd_error_status();
  else {
    /*
      Because of networking layer callbacks in place,
      this call will maintain the following instrumentation:
      - IDLE events
      - SOCKET events
      - STATEMENT events
      - STAGE events
      when reading a new network packet.
      In particular, a new instrumented statement is started.
      See init_net_server_extension()
    */
    thd->m_server_idle = true;
    rc = thd->get_protocol()->get_command(&com_data, &command);
    thd->m_server_idle = false;
  }

  if (rc) {
#ifndef NDEBUG
    char desc[VIO_DESCRIPTION_SIZE];
    vio_description(net->vio, desc);
    DBUG_PRINT("info", ("Got error %d reading command from socket %s",
                        net->error, desc));
#endif  // NDEBUG

    MYSQL_NOTIFY_STATEMENT_QUERY_ATTRIBUTES(thd->m_statement_psi, false);

    /* Instrument this broken statement as "statement/com/error" */
    thd->m_statement_psi = MYSQL_REFINE_STATEMENT(
        thd->m_statement_psi, com_statement_info[COM_END].m_key);

    /* Check if we can continue without closing the connection */

    /* The error must be set. */
    assert(thd->is_error());
    thd->send_statement_status();

    /* Mark the statement completed. */
    MYSQL_END_STATEMENT(thd->m_statement_psi, thd->get_stmt_da());
    thd->m_statement_psi = nullptr;
    thd->m_digest = nullptr;

    if (rc < 0) {
      return_value = true;  // We have to close it.
      goto out;
    }
    net->error = NET_ERROR_UNSET;
    return_value = false;
    goto out;
  }
```

읽기가 성공했으면 읽기 타임아웃을 원래대로 돌리고 디스패치한다.

`sql` / `sql_parse.cc` L1484-L1500 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_parse.cc#L1484-L1500))

```cpp
// sql_parse.cc L1484-L1500
  thd->get_protocol_classic()->get_output_packet()->shrink(
      thd->variables.net_buffer_length);
  /* Restore read timeout value */
  my_net_set_read_timeout(net, thd->variables.net_read_timeout);

  DEBUG_SYNC(thd, "before_command_dispatch");

  return_value = dispatch_command(thd, &com_data, command);
  thd->get_protocol_classic()->get_output_packet()->shrink(
      thd->variables.net_buffer_length);

out:
  /* The statement instrumentation must be closed in all cases. */
  assert(thd->m_digest == nullptr);
  assert(thd->m_statement_psi == nullptr);
  return return_value;
}
```

명령 번호는 패킷의 첫 바이트다. 인자 해석(`parse_packet`)까지 여기서 끝나 `COM_DATA` 에 담긴다.

`sql` / `protocol_classic.cc` L2890-L2922 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/protocol_classic.cc#L2890-L2922))

```cpp
// protocol_classic.cc L2890-L2922
int Protocol_classic::get_command(COM_DATA *com_data,
                                  enum_server_command *cmd) {
  // read packet from the network
  if (const int rc = read_packet()) return rc;

  /*
    'input_packet_length' contains length of data, as it was stored in packet
    header. In case of malformed header, my_net_read returns zero.
    If input_packet_length is not zero, my_net_read ensures that the returned
    number of bytes was actually read from network.
    There is also an extra safety measure in my_net_read:
    it sets packet[input_packet_length]= 0, but only for non-zero packets.
  */
  if (input_packet_length == 0) /* safety */
  {
    /* Initialize with COM_SLEEP packet */
    input_raw_packet[0] = (uchar)COM_SLEEP;
    input_packet_length = 1;
  }
  /* Do not rely on my_net_read, extra safety against programming errors. */
  input_raw_packet[input_packet_length] = '\0'; /* safety */

  *cmd = (enum enum_server_command)(uchar)input_raw_packet[0];

  if (*cmd >= COM_END) *cmd = COM_END;  // Wrong command

  assert(input_packet_length);
  // Skip 'command'
  input_packet_length--;
  input_raw_packet++;

  return parse_packet(com_data, *cmd);
}
```

`sql` / `protocol_classic.cc` L1411-L1422 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/protocol_classic.cc#L1411-L1422))

```cpp
// protocol_classic.cc L1411-L1422
int Protocol_classic::read_packet() {
  input_packet_length = my_net_read(&m_thd->net);
  if (input_packet_length != packet_error) {
    assert(!m_thd->net.error);
    bad_packet = false;
    input_raw_packet = m_thd->net.read_pos;
    return 0;
  }

  bad_packet = true;
  return m_thd->net.error == NET_ERROR_SOCKET_UNUSABLE ? 1 : -1;
}
```

## 동작 흐름

```text
 L1360  lex->set_current_query_block(nullptr)
 L1368  clear_error, reset_diagnostics_area       init_connect 의 오류를 지운다 (주석 L1362-L1367)
 L1377  net = NET
 L1378  my_net_set_read_timeout(net, net_wait_timeout)
 L1379  net_new_transaction(net)                  패킷 순번을 0 으로

 L1413  m_mem_cnt.reset()                         실패면 rc != 0 으로 아래 오류 경로
 L1428  m_server_idle = true
 L1429  get_protocol()->get_command(&com_data, &command)
          protocol_classic.cc L2893  read_packet -> my_net_read   여기서 잠든다
          L2912  *cmd = 첫 바이트, COM_END 이상이면 COM_END
          L2921  parse_packet(com_data, *cmd)     명령별 인자를 COM_DATA 에 푼다
 L1430  m_server_idle = false

 L1433  rc != 0
          L1451  send_statement_status              오류 패킷을 보낸다
          L1458  rc < 0  -> return true              연결을 닫는다
          L1462  아니면 net->error 를 지우고 return false   루프는 계속된다

 L1487  my_net_set_read_timeout(net, net_read_timeout)
 L1491  [02] dispatch_command(thd, &com_data, command)
 L1499  return return_value                          true 면 handle_connection 의 루프가 끝난다
```

같은 소켓 read 인데 언제 읽느냐에 따라 다른 시스템 변수가 걸린다. 명령과 명령 사이에는 `wait_timeout` 이, 명령이 실행되는 도중(LOAD DATA LOCAL 처럼 추가 패킷을 읽는 경우)에는 `net_read_timeout` 이 걸린다.

```text
 타임아웃의 교대 (한 연결의 시간축)

 ... 이전 명령 끝 | 대기                         | 실행 중                  | 대기 ...
                  L1378 net_wait_timeout          L1487 net_read_timeout     다음 do_command
                  |<-- wait_timeout 초 넘으면 -->|
                       read 실패 -> rc < 0 -> return true -> 연결 종료

 net_wait_timeout 은 기본이 wait_timeout 이고
   클라이언트가 CLIENT_INTERACTIVE 능력을 보냈으면 interactive_timeout 으로 바꿔 둔다 (sql_class.cc L1244-L1245)
```

```text
 get_command 의 결과 세 갈래

 rc     return              어디서, 그리고 그 뒤
 0      dispatch_command()  읽기와 parse_packet 성공
 < 0    true                read_packet 실패, NET_ERROR_SOCKET_UNUSABLE 아님 (protocol_classic.cc L1421)
                            -> 연결 종료
 > 0    false               NET_ERROR_SOCKET_UNUSABLE, parse_packet 실패
                            -> L1462 에서 net->error 를 지우고 다음 명령을 기다린다
 L1413 의 m_mem_cnt.reset 실패도 rc 에 담겨 같은 L1433 분기로 간다

 어느 쪽이든 오류가 있으면 L1451 에서 클라이언트에 먼저 알린다
```

## 결과가 쓰이는 곳

```text
 command, com_data
      --> [02] dispatch_command 의 switch (command) 와 각 case 의 인자

 반환값
      --> handle_connection 의 while 루프 (connection_handler_per_thread.cc L304)
          true 면 break -> end_connection -> close_connection
```

## 다루지 않는 것

`my_net_read` 의 압축 패킷과 16MB 초과 패킷 이어 붙이기, `parse_packet` 의 명령별 해석, X Protocol 같은 플러그인 프로토콜의 `get_command`, `opt_log_slow_extra` 용 상태 변수 복사, 디버그 동기점(`DEBUG_SYNC`)은 이 함수의 곁가지라 줄만 적었다. 연결이 끊긴 뒤의 정리는 [연결과 스레드](../../connection-thread/README.md)에 있다.
