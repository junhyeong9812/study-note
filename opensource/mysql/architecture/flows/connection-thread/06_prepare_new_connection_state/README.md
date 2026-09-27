# prepare_new_connection_state

상위: [연결과 스레드](../README.md)

인증을 통과한 연결이 **첫 명령을 받기 전에 세션을 꾸미는** 자리다. 압축을 켜고, 세션 시스템 변수를 전역값에서 복사하고, 관리자가 아니면 `init_connect` 를 실행한다. 반환값이 `void` 라서 여기서 실패하면 오류를 보내고 `thd->killed` 를 세우는 방식으로 연결을 끝낸다.

## 위치

`sql` / `sql_connect.cc` L776-L890 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_connect.cc#L776-L890))

## 실제 코드

압축을 켠다. 압축 컨텍스트를 둘 자리가 없으면 연결을 끝낸다.

`sql` / `sql_connect.cc` L776-L806 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_connect.cc#L776-L806))

```cpp
// sql_connect.cc L776-L806
static void prepare_new_connection_state(THD *thd) {
  NET *net = thd->get_protocol_classic()->get_net();
  Security_context *sctx = thd->security_context();

  Protocol *protocol = thd->get_protocol();
  if (protocol->has_client_capability(CLIENT_COMPRESS) ||
      protocol->has_client_capability(CLIENT_ZSTD_COMPRESSION_ALGORITHM)) {
    net->compress = true;  // Use compression
    const enum enum_compression_algorithm algorithm =
        get_compression_algorithm(protocol->get_compression_algorithm());
    NET_SERVER *server_extn = static_cast<NET_SERVER *>(net->extension);
    if (server_extn != nullptr)
      mysql_compress_context_init(&server_extn->compress_ctx, algorithm,
                                  protocol->get_compression_level());
    if (net->extension == nullptr) {
      const LEX_CSTRING sctx_user = sctx->user();
      Host_errors errors;
      my_error(ER_NEW_ABORTING_CONNECTION, MYF(0), thd->thread_id(),
               thd->db().str ? thd->db().str : "unconnected",
               sctx_user.str ? sctx_user.str : "unauthenticated",
               sctx->host_or_ip().str,
               "Unable to allocate memory for compression context: Aborting "
               "connection.");
      thd->server_status &= ~SERVER_STATUS_CLEAR_SET;
      thd->send_statement_status();
      thd->killed = THD::KILL_CONNECTION;
      errors.m_init_connect = 1;
      inc_host_errors(thd->m_main_security_ctx.ip().str, &errors);
      return;
    }
  }
```

세션 변수를 만들고, 관리자 연결인지 판정해 `init_connect` 를 돌릴지 정한다.

`sql` / `sql_connect.cc` L808-L837 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_connect.cc#L808-L837))

```cpp
// sql_connect.cc L808-L837
  // Initializing session system variables.
  alloc_and_copy_thd_dynamic_variables(thd, true);

  thd->set_proc_info(nullptr);
  thd->set_command(COM_SLEEP);
  thd->init_query_mem_roots();
  const bool is_admin_conn =
      (sctx->check_access(SUPER_ACL) ||
       sctx->has_global_grant(STRING_WITH_LEN("CONNECTION_ADMIN")).first);
  thd->m_mem_cnt.set_orig_mode(is_admin_conn ? MEM_CNT_UPDATE_GLOBAL_COUNTER
                                             : (MEM_CNT_UPDATE_GLOBAL_COUNTER |
                                                MEM_CNT_GENERATE_ERROR |
                                                MEM_CNT_GENERATE_LOG_ERROR));
  if (opt_init_connect.length && !is_admin_conn) {
    if (sctx->password_expired()) {
      LogErr(WARNING_LEVEL, ER_CONN_INIT_CONNECT_IGNORED, sctx->priv_user().str,
             sctx->priv_host().str);
      return;
    }
    if (sctx->is_in_registration_sandbox_mode()) {
      LogErr(WARNING_LEVEL, ER_CONN_INIT_CONNECT_IGNORED_MFA,
             sctx->priv_user().str, sctx->priv_host().str);
      return;
    }
    // Do not print OOM error to error log.
    thd->m_mem_cnt.set_curr_mode(
        (MEM_CNT_UPDATE_GLOBAL_COUNTER | MEM_CNT_GENERATE_ERROR));
    execute_init_command(thd, &opt_init_connect, &LOCK_sys_init_connect);
    thd->m_mem_cnt.set_curr_mode(MEM_CNT_DEFAULT);
    if (thd->is_error()) {
```

`init_connect` 가 실패했을 때의 뒷정리다. 오류를 보내기 전에 클라이언트의 첫 명령 패킷을 하나 읽어 버린다.

`sql` / `sql_connect.cc` L861-L890 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_connect.cc#L861-L890))

```cpp
// sql_connect.cc L861-L890
      thd->lex->set_current_query_block(nullptr);
      my_net_set_read_timeout(net, thd->variables.net_wait_timeout);
      thd->clear_error();
      net_new_transaction(net);
      packet_length = my_net_read(net);
      /*
        If my_net_read() failed, my_error() has been already called,
        and the main Diagnostics Area contains an error condition.
      */
      if (packet_length != packet_error)
        my_error(ER_NEW_ABORTING_CONNECTION, MYF(0), thd->thread_id(),
                 thd->db().str ? thd->db().str : "unconnected",
                 sctx_user.str ? sctx_user.str : "unauthenticated",
                 sctx->host_or_ip().str, "init_connect command failed");

      thd->server_status &= ~SERVER_STATUS_CLEAR_SET;
      thd->send_statement_status();
      thd->killed = THD::KILL_CONNECTION;
      errors.m_init_connect = 1;
      inc_host_errors(thd->m_main_security_ctx.ip().str, &errors);
      NET_SERVER *server_extn = static_cast<NET_SERVER *>(net->extension);
      if (server_extn != nullptr)
        mysql_compress_context_deinit(&server_extn->compress_ctx);
      return;
    }

    thd->set_proc_info(nullptr);
    thd->init_query_mem_roots();
  }
}
```

## 동작 흐름

```text
 L781  클라이언트가 CLIENT_COMPRESS 나 ZSTD 압축을 요청했으면
         L783  net->compress = true
         L787  서버 확장이 있으면 압축 컨텍스트 초기화
         L790  확장이 없으면
                 L793  ER_NEW_ABORTING_CONNECTION
                 L800  오류 패킷을 보낸다
                 L801  killed = KILL_CONNECTION
                 L803  호스트 캐시 m_init_connect 오류 수 +1
                 L804  return

 L809  alloc_and_copy_thd_dynamic_variables     세션 시스템 변수를 전역값에서 복사
 L812  set_command(COM_SLEEP)                  PROCESSLIST 의 Command 가 Sleep 이 된다
 L813  init_query_mem_roots
 L814  is_admin_conn = SUPER 또는 CONNECTION_ADMIN
 L817  메모리 집계 모드
         관리자     전역 카운터만 갱신
         그 외      전역 카운터 + 한도 초과 시 오류 + 오류 로그

 L821  init_connect 가 설정돼 있고 관리자가 아니면
         L822  비밀번호 만료 상태    -> 경고 로그만, 실행 안 함
         L827  MFA 등록 샌드박스     -> 경고 로그만, 실행 안 함
         L835  execute_init_command
         L837  실패하면 아래 그림
         L887  성공이면 proc_info, 메모리 루트 정리
```

```text
 init_connect 가 실패했을 때 (L837-L884)

 L845  경고 로그 ER_SERVER_NEW_ABORTING_CONNECTION (진단 메시지 포함)
 L862  읽기 타임아웃을 wait_timeout 으로
 L863  clear_error
 L865  my_net_read                    클라이언트가 보낸 첫 명령을 읽는다 (실행하지 않는다)
 L870  읽기에 성공했으면 ER_NEW_ABORTING_CONNECTION 을 세운다
       읽기가 실패했으면 my_net_read 가 세운 오류가 그대로 남는다
 L877  send_statement_status          클라이언트는 첫 명령의 응답으로 이 오류를 받는다
 L878  killed = KILL_CONNECTION
 L880  호스트 캐시 m_init_connect +1
 L883  압축 컨텍스트 해제
```

```text
 이 함수를 나간 뒤 [03] 에서 일어나는 일

 thd->killed        L303 loop   [07]  [08]  결과
 NOT_KILLED         runs        O     O     정상
 KILL_CONNECTION    0 times     O     O     압축 컨텍스트 실패 (L801)
 KILL_CONNECTION    0 times     O     O     init_connect 실패 (L878)
 NOT_KILLED         runs        O     O     비밀번호 만료, MFA 샌드박스라 init_connect 를 건너뜀

 실패해도 [04] 는 false 를 받는다. 루프를 한 번도 안 돌 뿐 정리 경로는 정상 종료와 같다
```

## 결과가 쓰이는 곳

```text
 thd->variables (세션 시스템 변수)
      --> SET SESSION 과 모든 명령이 이 복사본을 본다

 net->compress, compress_ctx
      --> 이후 모든 패킷 읽기, 쓰기가 압축을 거친다

 thd->killed = KILL_CONNECTION
      --> [03] L303 thd_connection_alive 가 false
      --> [07] end_connection 이 aborted_threads(Aborted_clients) 를 올린다 (L753-L754)

 COM_SLEEP
      --> 첫 명령이 오기 전까지 PROCESSLIST 에 Sleep 으로 보인다
```

## 다루지 않는 것

`alloc_and_copy_thd_dynamic_variables` 가 플러그인 변수를 다루는 방식, `execute_init_command` 가 문장을 파싱해 실행하는 경로(구조는 [명령 디스패치](../../command-dispatch/README.md)와 같다), 압축 알고리즘 협상과 `NET_SERVER` 확장, 메모리 집계 모드(`MEM_CNT_*`)의 세부, 비밀번호 만료 사용자에게 허용되는 명령의 범위는 세션 준비의 곁가지라 요약만 했다.
