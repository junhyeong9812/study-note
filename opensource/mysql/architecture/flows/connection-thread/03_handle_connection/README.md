# handle_connection

상위: [연결과 스레드](../README.md)

**연결 스레드의 본체이자 이 흐름의 지휘자다.** `for (;;)` 한 바퀴가 연결 하나의 수명이고, 바퀴 끝에서 스레드는 죽지 않고 캐시에 들어가 다음 연결을 기다린다. THD 를 만들고, 인증을 맡기고, `do_command` 루프를 돌리고, 정리하는 순서가 전부 이 함수에 적혀 있다.

## 위치

`sql` / `conn_handler` / `connection_handler_per_thread.cc` L246-L357 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/conn_handler/connection_handler_per_thread.cc#L246-L357))

## 실제 코드

스레드 초기화가 실패하면 연결을 받지도 못하고 끝난다.

`sql` / `conn_handler` / `connection_handler_per_thread.cc` L246-L261 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/conn_handler/connection_handler_per_thread.cc#L246-L261))

```cpp
// connection_handler_per_thread.cc L246-L261
static void *handle_connection(void *arg) {
  Global_THD_manager *thd_manager = Global_THD_manager::get_instance();
  Connection_handler_manager *handler_manager =
      Connection_handler_manager::get_instance();
  Channel_info *channel_info = static_cast<Channel_info *>(arg);
  bool pthread_reused [[maybe_unused]] = false;

  if (my_thread_init()) {
    connection_errors_internal++;
    channel_info->send_error_and_close_channel(ER_OUT_OF_RESOURCES, 0, false);
    handler_manager->inc_aborted_connects();
    Connection_handler_manager::dec_connection_count();
    delete channel_info;
    my_thread_exit(nullptr);
    return nullptr;
  }
```

한 바퀴의 앞쪽이다. THD 를 만들고 목록에 올린 뒤 인증하고 명령 루프를 돈다.

`sql` / `conn_handler` / `connection_handler_per_thread.cc` L263-L308 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/conn_handler/connection_handler_per_thread.cc#L263-L308))

```cpp
// connection_handler_per_thread.cc L263-L308
  for (;;) {
    THD *thd = init_new_thd(channel_info);
    if (thd == nullptr) {
      connection_errors_internal++;
      handler_manager->inc_aborted_connects();
      Connection_handler_manager::dec_connection_count();
      break;  // We are out of resources, no sense in continuing.
    }

#ifdef HAVE_PSI_THREAD_INTERFACE
    if (pthread_reused) {
      /*
        Reusing existing pthread:
        Create new instrumentation for the new THD job,
        and attach it to this running pthread.
      */
      PSI_thread *psi = PSI_THREAD_CALL(new_thread)(key_thread_one_connection,
                                                    0 /* no sequence number */,
                                                    thd, thd->thread_id());
      PSI_THREAD_CALL(set_thread_os_id)(psi);
      PSI_THREAD_CALL(set_thread)(psi);
    }
#endif

#ifdef HAVE_PSI_THREAD_INTERFACE
    /* Find the instrumented thread */
    PSI_thread *psi = PSI_THREAD_CALL(get_thread)();
    /* Save it within THD, so it can be inspected */
    thd->set_psi(psi);
#endif /* HAVE_PSI_THREAD_INTERFACE */
    mysql_thread_set_psi_id(thd->thread_id());
    mysql_thread_set_psi_THD(thd);
    const MYSQL_SOCKET socket =
        thd->get_protocol_classic()->get_vio()->mysql_socket;
    mysql_socket_set_thread_owner(socket);
    thd_manager->add_thd(thd);

    if (thd_prepare_connection(thd))
      handler_manager->inc_aborted_connects();
    else {
      while (thd_connection_alive(thd)) {
        if (do_command(thd)) break;
      }
      end_connection(thd);
    }
    close_connection(thd, 0, false, false);
```

한 바퀴의 뒤쪽이다. THD 를 치우고, 스레드를 캐시에 넣을지 끝낼지 정한다.

`sql` / `conn_handler` / `connection_handler_per_thread.cc` L310-L357 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/conn_handler/connection_handler_per_thread.cc#L310-L357))

```cpp
// connection_handler_per_thread.cc L310-L357
    thd->get_stmt_da()->reset_diagnostics_area();
    thd->release_resources();

    // Clean up errors now, before possibly waiting for a new connection.
#if OPENSSL_VERSION_NUMBER < 0x10100000L
    ERR_remove_thread_state(nullptr);
#endif /* OPENSSL_VERSION_NUMBER < 0x10100000L */
    thd_manager->remove_thd(thd);
    Connection_handler_manager::dec_connection_count();

#ifdef HAVE_PSI_THREAD_INTERFACE
    /* Stop telemetry, while THD is still available. */
    if (psi != nullptr) {
      PSI_THREAD_CALL(abort_telemetry)(psi);
    }

    /* Decouple THD and the thread instrumentation. */
    thd->set_psi(nullptr);
    mysql_thread_set_psi_THD(nullptr);
#endif /* HAVE_PSI_THREAD_INTERFACE */

    delete thd;

#ifdef HAVE_PSI_THREAD_INTERFACE
    /* Delete the instrumentation for the job that just completed. */
    PSI_THREAD_CALL(delete_current_thread)();
#endif /* HAVE_PSI_THREAD_INTERFACE */

    // Server is shutting down so end the pthread.
    if (connection_events_loop_aborted()) break;

    channel_info = Per_thread_connection_handler::block_until_new_connection();
    if (channel_info == nullptr) break;
    pthread_reused = true;
    if (connection_events_loop_aborted()) {
      // Close the channel and exit as server is undergoing shutdown.
      channel_info->send_error_and_close_channel(ER_SERVER_SHUTDOWN, 0, false);
      delete channel_info;
      channel_info = nullptr;
      Connection_handler_manager::dec_connection_count();
      break;
    }
  }

  my_thread_end();
  my_thread_exit(nullptr);
  return nullptr;
}
```

THD 는 리스너 스레드가 아니라 여기, 연결 스레드에서 만든다.

`sql` / `conn_handler` / `connection_handler_per_thread.cc` L194-L229 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/conn_handler/connection_handler_per_thread.cc#L194-L229))

```cpp
// connection_handler_per_thread.cc L194-L229
static THD *init_new_thd(Channel_info *channel_info) {
  THD *thd = channel_info->create_thd();
  if (thd == nullptr) {
    channel_info->send_error_and_close_channel(ER_OUT_OF_RESOURCES, 0, false);
    delete channel_info;
    return nullptr;
  }

  thd->set_new_thread_id();

  if (channel_info->get_prior_thr_create_utime() != 0) {
    /*
      A pthread was created to handle this connection:
      increment slow_launch_threads counter if it took more than
      slow_launch_time seconds to create the pthread.
    */
    const ulonglong launch_time =
        thd->start_utime - channel_info->get_prior_thr_create_utime();
    if (launch_time >= slow_launch_time * 1000000ULL)
      Per_thread_connection_handler::slow_launch_threads++;
  }
  delete channel_info;

  /*
    handle_one_connection() is normally the only way a thread would
    start and would always be on the very high end of the stack ,
    therefore, the thread stack always starts at the address of the
    first local variable of handle_one_connection, which is thd. We
    need to know the start of the stack so that we could check for
    stack overruns.
  */
  thd_set_thread_stack(thd, (char *)&thd);
  thd->store_globals();

  return thd;
}
```

`do_command` 루프의 조건이다. 세 가지 중 하나만 틀려도 루프가 끝난다.

`sql` / `sql_connect.cc` L935-L941 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_connect.cc#L935-L941))

```cpp
// sql_connect.cc L935-L941
bool thd_connection_alive(THD *thd) {
  NET *net = thd->get_protocol_classic()->get_net();
  if (!net->error && net->vio != nullptr &&
      !(thd->killed == THD::KILL_CONNECTION))
    return true;
  return false;
}
```

## 동작 흐름

```text
 L253  my_thread_init 실패
         L255  ER_OUT_OF_RESOURCES. senderror=false 라 클라이언트에는 보내지 않고
               stderr 경고만 남긴다 (channel_info.cc L81-L89)
         L256  aborted_connects++   L257  dec_connection_count
         L259  스레드를 끝낸다

 L263  for (;;)                              한 바퀴 = 연결 하나
 L264    init_new_thd(channel_info)
           L195  create_thd  -> Vio 를 만들고 new THD, init_net (channel_info.cc L43-L52)
           L202  set_new_thread_id           이 연결의 thread_id 를 새로 받는다
           L204  새로 만든 스레드였으면 생성 소요를 잰다
           L215  delete channel_info         이제부터 연결은 THD 와 Vio 뿐이다
           L225  스택 시작 주소 기록, L226 store_globals (current_thd)
 L265    실패면 aborted_connects++, dec_connection_count, 스레드 종료

 L273    재사용 스레드면 PSI 스레드 계측을 새로 만든다
 L298    thd_manager->add_thd(thd)            이 순간부터 PROCESSLIST 와 KILL 대상

 L300    [04] thd_prepare_connection
           true   L301  aborted_connects++    (루프도 end_connection 도 건너뛴다)
           false  L303  while (thd_connection_alive(thd))
                  L304    if (do_command(thd)) break;       --> [명령 디스패치]
                  L306  [07] end_connection
 L308    [08] close_connection(thd, 0, false, false)       성공이든 실패든 지난다

 L310    진단 영역 초기화
 L311    thd->release_resources()              Vio 삭제, THD::cleanup (트랜잭션 롤백)
 L317    remove_thd                            PROCESSLIST 에서 빠진다
 L318    dec_connection_count                  Threads_connected -1
 L331    delete thd

 L339    서버 종료 중이면 break
 L341    block_until_new_connection            캐시에 들어가 잠든다
 L342      nullptr (캐시가 가득 찼거나 줄이는 중이거나 종료로 깨어남) -> break, 스레드 종료
 L343      pthread_reused = true
 L344      깨어 보니 종료 중이면 ER_SERVER_SHUTDOWN, dec_connection_count, break
           아니면 L263 으로 돌아가 다음 연결의 THD 를 만든다

 L354  my_thread_end, L355 my_thread_exit
```

아래 그림은 연결 하나가 이 함수 안에서 지나는 구간을 시간 순으로 세운 것이다. 오른쪽 막대는 각 자원이 살아 있는 구간이고, 가운데 `do_command` 구간이 다음 흐름이다.

```text
 연결 하나의 수명 (연결 스레드 T 의 시간축, 위에서 아래로)

 구간      줄          thr  cnt  THD  PL   하는 일
 --------- ----------  ---  ---  ---  ---  --------------------
 listener  [01] L122        +             connection_count++
           [02] L420   +    |             스레드 생성 (캐시 미스일 때)
 init      L264        |    |    +        THD, Vio 생성, thread_id
           L298        |    |    |    +   add_thd
 login     L300 [05]   |    |    |    |   connect_timeout 으로 핸드셰이크, 인증
 prepare   [06]        |    |    |    |   압축, 세션 변수, init_connect
 command   L303-L305   |    |    |    |   wait_timeout 으로 다음 명령을 기다리고 실행
                       |    |    |    |     (sql_parse.cc L1378)
 end       L306 [07]   |    |    |    |   감사 이벤트, 사용자 연결 수 반환
 close     L308 [08]   |    |    |    |   소켓 shutdown, 로그아웃
 free      L311        |    |    |    |   release_resources
           L317        |    |    |    -   remove_thd
           L318        |    -    |        dec_connection_count
           L331        |         -        delete thd
 cache     L341        |                  잠들어 다음 연결을 기다린다
           L342-L350   -                  캐시에 못 들어가거나 종료 중이면 스레드 종료

 thr = OS 스레드   cnt = connection_count   THD = THD 객체   PL = PROCESSLIST 에 보임
 + 는 시작, - 는 끝
 캐시 적중이면 [02] L420 대신 이전 연결의 L341 에서 잠들어 있던 스레드가 깨어난다
```

```text
 루프가 끝나는 세 가지 길 (thd_connection_alive, sql_connect.cc L937)

 조건                               누가 만드는가
 net->error                         읽기, 쓰기 실패. 클라이언트가 말없이 끊긴 경우도 여기로 온다
 net->vio == nullptr                Vio 가 떼어진 경우
 killed == KILL_CONNECTION          KILL, 서버 종료, [06] 의 init_connect 실패

 그리고 L304 의 do_command 가 true 를 돌려주는 경우
   COM_QUIT 이면 dispatch_command 가 error = true 로 끝난다 (sql_parse.cc L2354)
 어느 길로 나가든 L306 end_connection -> L308 close_connection 순서는 같다
```

```text
 성공과 실패에서 지나는 곳

 [04] 실패  [04] 성공  지나는 곳
 O (L301)   X          aborted_connects++
 X          O          do_command 루프
 X          O          [07] end_connection (Aborted_clients 판정, 사용자 연결 수 반환)
 O          O          [08] close_connection
 O          O          release_resources 이하

 인증 실패 연결은 end_connection 을 지나지 않는다
 사용자별 연결 수(USER_CONN) 반환은 인증 쪽이 실패 경로에서 따로 한다
   예: sql_authentication.cc L4454, L4469 의 release_user_connection
```

## 결과가 쓰이는 곳

```text
 THD
      --> do_command 에 들어가 [명령 디스패치] 의 모든 단계가 쓴다
      --> L298 이후 다른 스레드가 Global_THD_manager 로 찾아 KILL 할 수 있다

 release_resources
      --> THD::cleanup 이 열린 트랜잭션을 trans_rollback 한다 (sql_class.cc L1345)
      --> ha_close_connection 으로 스토리지 엔진에 연결 종료를 알린다 (sql_class.cc L1476)

 캐시로 돌아간 스레드
      --> 다음 [02] add_connection 이 check_idle_thread_and_enqueue_connection 으로 깨운다
```

## 다루지 않는 것

Performance Schema 스레드 계측(`PSI_THREAD_CALL` 들)의 의미, `THD` 생성자와 `store_globals` 가 잡는 스레드 지역 상태, `do_command` 의 내부(다음 흐름 [명령 디스패치](../../command-dispatch/README.md)), `THD::release_resources` 와 `THD::cleanup` 의 전체 정리 목록, `KILL` 이 다른 스레드에서 `THD::awake` 로 Vio 를 끊는 과정은 연결 수명의 곁가지라 요약만 했다.
