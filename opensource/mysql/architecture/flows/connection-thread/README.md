# 연결과 스레드

상위: [MySQL 아키텍처 지도](../../README.md)

클라이언트 하나가 TCP 로 붙어서 **질의를 받을 준비가 될 때까지, 그리고 끊긴 뒤 스레드가 다음 연결을 기다리러 돌아갈 때까지**의 흐름이다. 기본 설정(`thread_handling=one-thread-per-connection`)에서는 연결 하나에 OS 스레드 하나가 붙는다. 이 흐름에는 **스레드 경계가 딱 한 번** 있다. 리스너 스레드는 연결 수를 세고 스레드를 고르거나 만드는 데까지만 하고, THD 생성부터 인증, 명령 루프, 정리는 전부 연결 스레드가 한다. 흐름은 [03] `handle_connection` 의 `while ... do_command` 루프에서 [명령 디스패치](../command-dispatch/README.md)로 넘어가고, 루프가 끝나면 다시 이 흐름으로 돌아와 연결을 닫는다.

기준 태그: mysql-9.7.2 [`008e09c283`](https://github.com/mysql/mysql-server/tree/008e09c2834b98143a8c067d4d225c90953050cf). 모든 줄 번호는 이 태그 기준이다.

## 전체 그림

```text
 리스너 스레드 (connection_event_loop, connection_acceptor.h L61)
 ------------------------------------------------------------------
 [01] Connection_handler_manager::process_new_connection       L256
      +-- check_and_incr_conn_count                            L259  connection_count++ (여기서 센다)
      |     넘치면 ER_CON_COUNT_ERROR 를 보내고 끝             L260
      +-- [02] Per_thread_connection_handler::add_connection   L265
            +-- check_idle_thread_and_enqueue_connection        L413  캐시에 쉬는 스레드가 있으면
            |     큐에 넣고 깨운다. 새 스레드를 만들지 않는다
            +-- 없으면 mysql_thread_create(handle_connection)   L420  여기서 스레드가 생긴다
 ------------------------------------------------------------------
                          스레드 경계 (Channel_info 하나가 넘어간다)
 ------------------------------------------------------------------
 연결 스레드
 [03] handle_connection                                        L246
      +-- init_new_thd -> Channel_info::create_thd              L264  THD 와 Vio 가 여기서 생긴다
      +-- thd_manager->add_thd                                  L298  이때부터 SHOW PROCESSLIST 에 보인다
      +-- [04] thd_prepare_connection                           L300
      |     +-- [05] login_connection                           L897
      |     |     +-- check_connection                          L709  호스트 확인, 핸드셰이크, 인증
      |     |           +-- acl_authenticate(thd, COM_CONNECT)  L651  (sql_authentication.cc L4050)
      |     +-- [06] prepare_new_connection_state               L901  압축, 세션 변수, init_connect
      |
      +-- while (thd_connection_alive) do_command               L303-L305  --> [명령 디스패치]
      |
      +-- [07] end_connection                                   L306  인증 성공한 연결만 지난다
      +-- [08] close_connection                                 L308  모든 연결이 지난다
      +-- release_resources / remove_thd / dec_connection_count L311, L317, L318
      +-- delete thd                                            L331
      +-- block_until_new_connection                            L341  캐시에 남을지, 스레드를 끝낼지
            다음 연결을 받으면 for(;;) 처음으로 (L263)

 [01] [02] 의 줄은 각자의 파일, [03] 아래는 connection_handler_per_thread.cc,
 [04] 아래는 sql_connect.cc 의 줄이다
```

연결 수는 리스너 스레드에서 올리고 연결 스레드에서 내린다. 올리는 곳은 하나인데 내리는 곳은 경로마다 다르다.

```text
 connection_count 의 짝 (파일은 모두 sql/conn_handler/ 아래)

 ++  manager.cc     L122  check_and_incr_conn_count        리스너 스레드
 --  manager.h      L198  dec_connection_count             이 핸들러에서는 아래 다섯 중 정확히 한 곳에서

     per_thread.cc  L433  리스너 스레드   add_connection 에서 스레드 생성 실패
     per_thread.cc  L257  연결 스레드     my_thread_init 실패
     per_thread.cc  L268  연결 스레드     init_new_thd 가 THD 를 못 만듦
     per_thread.cc  L318  연결 스레드     한 바퀴를 마침 (인증 실패도 여기)
     per_thread.cc  L349  연결 스레드     캐시에서 깨어났는데 서버가 종료 중

 0 이 되면 COND_connection_count 를 signal 한다 (manager.h L202)
 서버 종료의 close_connections 가 wait_till_no_connection 으로 이것을 기다린다 (mysqld.cc L2520)
```

```text
 max_connections 는 두 번 검사한다

 1차  리스너 스레드, 인증 전    check_and_incr_conn_count  manager.cc L118
        connection_count > max_connections 이고 admin 포트가 아니면 거절
        "올리기 전에" 보므로 max_connections + 1 번째까지 들어온다 (주석 L111-L117)

 2차  연결 스레드, 인증 후      check_restrictions_for_com_connect_command
                                sql_authentication.cc L3926-L3937
        SUPER / CONNECTION_ADMIN / SERVICE_CONNECTION_ADMIN 이 없으면
        valid_connection_count 로 다시 본다 -> 넘치면 ER_CON_COUNT_ERROR

 그래서 마지막 한 자리는 권한 있는 사용자 몫이 된다
   일반 사용자가 그 자리에 들어오면 인증까지 마친 뒤에 거절된다
```

## 어디에서 쓰이는가

```text
 [구조: 스레드 구성]  Per_thread_connection_handler 의 스레드 캐시가 여기서 돈다
 [명령 디스패치]      handle_connection 의 do_command 루프가 그 흐름의 입구다
 [커밋과 binlog 2PC]  연결이 끊기면 release_resources -> THD::cleanup 이
                      열린 트랜잭션을 trans_rollback 한다 (sql_class.cc L1345)
```

다음 흐름은 [명령 디스패치](../command-dispatch/README.md)다. 연결 스레드를 한 자리에서 보는 그림은 [스레드 구성](../../structure/threads/README.md)에 있다.

## db-engine 에서는

같은 세 가지 문제(연결 상한, 연결별 상태, 인증)를 db-engine 은 스레드 하나에 연결 하나를 묶지 않는 방식으로 풀었다.

```text
 같은 문제, 두 구현 (위 MySQL / 아래 db-engine)

 스레드
   MySQL      연결 1개 = OS 스레드 1개. 끝난 스레드는 캐시에 남아 다음 연결을 받는다
   db-engine  ConnectionPool(capacity) 이 Executors.newFixedThreadPool(capacity) 를 가진다
              세션과 스레드가 따로 논다. 일은 submit(sessionId) 으로 넘긴다

 상한
   MySQL      check_and_incr_conn_count 가 LOCK_connection_count 안에서 검사하고 올린다
              max_connections + 1 까지 받고, 마지막 자리는 인증 뒤 권한으로 가른다
   db-engine  openSession 의 require(sessions.size < capacity)
              검사와 put 이 원자적이지 않다 (impl 문서가 race 로 적어 둠)

 연결별 상태
   MySQL      THD. 연결 스레드가 만들고 끝까지 소유한다
   db-engine  Session(id, user, currentTxId, ...) 과 ProtocolHandler 의 sessionId 멤버

 인증
   MySQL      check_connection -> acl_authenticate
              호스트 확인, 플러그인 교체(RESTART), MFA, 프록시, SSL, 잠금, 만료
   db-engine  handleStartup -> AuthManager.authenticate
              사용자 맵 조회 + SHA-256 비교. 인증 전 Query 는 "not authenticated"

 종료
   MySQL      end_connection + close_connection, release_resources 에서 trans_rollback
   db-engine  handleTerminate -> pool.closeSession. 열린 트랜잭션 처리는 과제로 남김
```

db-engine 은 `ProtocolHandler` 가 응답을 직접 쓰지 않고 `ConnectionEvent` 를 돌려주게 해서 소켓 없이 테스트한다. MySQL 은 연결 스레드가 `NET` 에 직접 읽고 쓴다. db-engine 의 세션 종료는 `Terminate` 메시지에 기대고, impl 문서가 "종료 메시지 없이 끊기는 경우"를 과제로 남겼다. MySQL 에서는 그 경우도 `do_command` 가 읽기 실패로 루프를 빠져나와 같은 정리 경로를 탄다. 챕터: [13-01-connection-pool](../../../../../project/db-engine/13-01-connection-pool/), [14-01-protocol-handler](../../../../../project/db-engine/14-01-protocol-handler/), [15-01-auth](../../../../../project/db-engine/15-01-auth/).

## 단계

1. [Connection_handler_manager.process_new_connection](01_Connection_handler_manager.process_new_connection/README.md)이 연결 수를 세고 핸들러에 넘긴다.
2. [Per_thread_connection_handler.add_connection](02_Per_thread_connection_handler.add_connection/README.md)이 쉬는 스레드를 깨우거나 새 스레드를 만든다.
3. [handle_connection](03_handle_connection/README.md)이 연결 스레드의 본체로, 연결 하나의 수명 전체를 돈다.
4. [thd_prepare_connection](04_thd_prepare_connection/README.md)이 로그인과 세션 준비를 묶는다.
5. [login_connection](05_login_connection/README.md)이 타임아웃을 바꿔 끼우고 `check_connection` 으로 인증한다.
6. [prepare_new_connection_state](06_prepare_new_connection_state/README.md)가 압축과 세션 변수를 준비하고 `init_connect` 를 돌린다.
7. [end_connection](07_end_connection/README.md)이 인증된 연결의 끝을 기록하고 사용자 연결 수를 돌려준다.
8. [close_connection](08_close_connection/README.md)이 소켓을 끊고 로그아웃한다.

## 결과가 쓰이는 곳

```text
 THD
      --> 연결 스레드가 만들고 끝까지 소유한다
      --> do_command 루프의 모든 명령이 이 THD 를 들고 간다
      --> Global_THD_manager 목록에 올라 KILL 과 PROCESSLIST 의 대상이 된다

 Security_context (thd->m_main_security_ctx)
      --> acl_authenticate 가 채운 권한이 이후 모든 권한 검사의 근거다

 연결 스레드
      --> 연결이 끝나도 thread_cache_size 안이면 죽지 않고 다음 연결을 기다린다
      --> 기다리는 스레드 수는 blocked_pthread_count 로 센다

 연결 카운터 (괄호는 상태 변수, mysqld.cc 의 등록 줄)
      --> connection_count   현재 연결 수, max_connections 판정   (Threads_connected L12045)
      --> aborted_connects   연결 준비 단계의 실패                 (Aborted_connects  L11689)
      --> aborted_threads    준비를 마친 뒤 비정상 종료            (Aborted_clients   L11688)
```

## 다루지 않는 것

리스너 쪽(`Mysqld_socket_listener`, `listen_for_connection_event`, admin 포트 전용 스레드 `handle_admin_socket`), 연결 방식별 `Channel_info` 하위 클래스(TCP, Unix socket, named pipe, shared memory), `thread_handling=no-threads` 의 `One_thread_connection_handler` 와 thread pool 플러그인(`Plugin_connection_handler`), 인증 플러그인 내부(`caching_sha2_password` 의 교환 절차, 다단계 인증 `do_multi_factor_auth`), `COM_CHANGE_USER` 재인증, 호스트 캐시(`ip_to_hostname`, `inc_host_errors`), `KILL` 이 다른 스레드에서 연결을 끊는 경로(`THD::awake`), Performance Schema 계측은 이 흐름의 곁가지라 요약만 했다.

## 하위 메서드

- [01 Connection_handler_manager.process_new_connection](01_Connection_handler_manager.process_new_connection/README.md)
- [02 Per_thread_connection_handler.add_connection](02_Per_thread_connection_handler.add_connection/README.md)
- [03 handle_connection](03_handle_connection/README.md)
- [04 thd_prepare_connection](04_thd_prepare_connection/README.md)
- [05 login_connection](05_login_connection/README.md)
- [06 prepare_new_connection_state](06_prepare_new_connection_state/README.md)
- [07 end_connection](07_end_connection/README.md)
- [08 close_connection](08_close_connection/README.md)
