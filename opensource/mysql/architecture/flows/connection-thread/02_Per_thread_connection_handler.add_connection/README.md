# Per_thread_connection_handler.add_connection

상위: [연결과 스레드](../README.md)

**연결 스레드가 언제 생기는지가 여기서 정해진다.** 스레드 캐시에 쉬고 있는 스레드가 있으면 연결을 큐에 넣고 깨우기만 하고, 없을 때만 `handle_connection` 을 시작 함수로 새 OS 스레드를 만든다. 아직 리스너 스레드 위다.

## 위치

`sql` / `conn_handler` / `connection_handler_per_thread.cc` L404-L440 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/conn_handler/connection_handler_per_thread.cc#L404-L440))

## 실제 코드

```cpp
// connection_handler_per_thread.cc L404-L440
bool Per_thread_connection_handler::add_connection(Channel_info *channel_info) {
  int error = 0;
  my_thread_handle id;

  DBUG_TRACE;

  // Simulate thread creation for test case before we check thread cache
  DBUG_EXECUTE_IF("fail_thread_create", error = 1; goto handle_error;);

  if (!check_idle_thread_and_enqueue_connection(channel_info)) return false;

  /*
    There are no idle threads available to take up the new
    connection. Create a new thread to handle the connection
  */
  channel_info->set_prior_thr_create_utime();
  error =
      mysql_thread_create(key_thread_one_connection, &id, &connection_attrib,
                          handle_connection, (void *)channel_info);
#ifndef NDEBUG
handle_error:
#endif  // !NDEBUG

  if (error) {
    connection_errors_internal++;
    if (!create_thd_err_log_throttle.log())
      LogErr(ERROR_LEVEL, ER_CONN_PER_THREAD_NO_THREAD, error);
    channel_info->send_error_and_close_channel(ER_CANT_CREATE_THREAD, error,
                                               true);
    Connection_handler_manager::dec_connection_count();
    return true;
  }

  Global_THD_manager::get_instance()->inc_thread_created();
  DBUG_PRINT("info", ("Thread created"));
  return false;
}
```

캐시에 쉬는 스레드가 있는지 보고, 있으면 연결을 큐에 넣는 쪽이다.

`sql` / `conn_handler` / `connection_handler_per_thread.cc` L387-L402 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/conn_handler/connection_handler_per_thread.cc#L387-L402))

```cpp
// connection_handler_per_thread.cc L387-L402
bool Per_thread_connection_handler::check_idle_thread_and_enqueue_connection(
    Channel_info *channel_info) {
  bool res = true;

  mysql_mutex_lock(&LOCK_thread_cache);
  if (Per_thread_connection_handler::blocked_pthread_count > wake_pthread) {
    DBUG_PRINT("info", ("waiting_channel_info_list->push %p", channel_info));
    waiting_channel_info_list->push_back(channel_info);
    wake_pthread++;
    mysql_cond_signal(&COND_thread_cache);
    res = false;
  }
  mysql_mutex_unlock(&LOCK_thread_cache);

  return res;
}
```

그 큐를 받아 가는 쪽이다. 이전 연결을 마친 연결 스레드가 [03] 의 끝에서 이 함수로 들어와 잠든다.

`sql` / `conn_handler` / `connection_handler_per_thread.cc` L144-L182 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/conn_handler/connection_handler_per_thread.cc#L144-L182))

```cpp
// connection_handler_per_thread.cc L144-L182
Channel_info *Per_thread_connection_handler::block_until_new_connection() {
  Channel_info *new_conn = nullptr;
  mysql_mutex_lock(&LOCK_thread_cache);
  if (blocked_pthread_count < max_blocked_pthreads && !shrink_cache) {
    /* Don't kill the pthread, just block it for reuse */
    DBUG_PRINT("info", ("Blocking pthread for reuse"));

    /*
      mysys_var is bound to the physical thread,
      so make sure mysys_var->dbug is reset to a clean state
      before picking another session in the thread cache.
    */
    DBUG_POP();
    assert(!_db_is_pushed_());

    // Block pthread
    blocked_pthread_count++;
    while (!connection_events_loop_aborted() && !wake_pthread && !shrink_cache)
      mysql_cond_wait(&COND_thread_cache, &LOCK_thread_cache);
    blocked_pthread_count--;

    if (shrink_cache && blocked_pthread_count <= max_blocked_pthreads) {
      mysql_cond_signal(&COND_flush_thread_cache);
    }

    if (wake_pthread) {
      wake_pthread--;
      if (!waiting_channel_info_list->empty()) {
        new_conn = waiting_channel_info_list->front();
        waiting_channel_info_list->pop_front();
        DBUG_PRINT("info", ("waiting_channel_info_list->pop %p", new_conn));
      } else {
        assert(0);  // We should not get here.
      }
    }
  }
  mysql_mutex_unlock(&LOCK_thread_cache);
  return new_conn;
}
```

## 동작 흐름

```text
 L411  (디버그) fail_thread_create 면 곧장 handle_error 로

 L413  check_idle_thread_and_enqueue_connection
         L392  blocked_pthread_count > wake_pthread ?
               잠든 스레드 수가 "이미 깨우기로 한 수"보다 많을 때만
                 L394  waiting_channel_info_list 에 push_back
                 L395  wake_pthread++
                 L396  COND_thread_cache 를 signal
                 L397  false -> add_connection 이 false 로 끝난다
               아니면 true

 L419  set_prior_thr_create_utime   스레드 생성 직전 시각을 적는다
 L420  mysql_thread_create(..., handle_connection, channel_info)
         성공  L437  Threads_created++, false
         실패  L428  connection_errors_internal++
               L429  로그 (스로틀)
               L431  ER_CANT_CREATE_THREAD 를 소켓에 쓴다
               L433  dec_connection_count  (01 에서 올린 것을 되돌린다)
               L434  true
```

같은 연결이 캐시 적중이면 스레드 생성 비용 없이, 적중하지 않으면 OS 스레드 생성 비용을 치르고 붙는다.

```text
 스레드가 생기는 시점 (시간축)

         리스너 스레드                       캐시에 잠든 연결 스레드 T1
 캐시 적중
   t0    accept -> [01] -> [02]
   t1    L392 blocked(1) > wake(0)
   t2    push_back, wake_pthread=1, signal ----> L162 cond_wait 에서 깬다
   t3    return false, 다음 accept 로               L163 blocked--
   t4                                              L170 wake_pthread--
   t5                                              L172 front, pop_front
   t6                                              [03] L263 for(;;) 처음으로
                                                   이 스레드의 THD 는 새로 만든다

         리스너 스레드                       새 연결 스레드 T2
 캐시 미스
   t0    accept -> [01] -> [02]
   t1    L392 blocked(0) > wake(0) 아님
   t2    L419 prior_thr_create_utime 기록
   t3    L420 mysql_thread_create ---------------> handle_connection(channel_info)
   t4    return false, 다음 accept 로               init_new_thd 가 생성 소요를 잰다
                                                   slow_launch_time 이상이면
                                                   Slow_launch_threads++ (L212-L213)
```

```text
 스레드 캐시 상태 (전부 LOCK_thread_cache 로 보호)

 blocked_pthread_count        L160 ++ / L163 --   지금 잠든 스레드 수
 wake_pthread                 L395 ++ / L170 --   깨우기로 했지만 아직 안 가져간 수
 waiting_channel_info_list    L394 push / L173 pop  넘겨줄 연결 큐 (FIFO)
 max_blocked_pthreads         = thread_cache_size   잠들 수 있는 스레드 상한
 shrink_cache                 modify_thread_cache_size 가 줄일 때 true

 불변식: 큐 길이 == wake_pthread
   push 할 때 같이 ++, pop 할 때 같이 --
   L176 assert(0) 이 "wake_pthread 는 있는데 큐가 비었다"를 막는다

 L392 가 blocked 가 아니라 blocked > wake 를 보므로
 잠든 스레드가 아직 깨어나기 전에 두 연결이 연달아 와도 하나만 큐로 간다
   blocked=1, wake=0  첫 연결  -> 큐에 넣음, wake=1
   blocked=1, wake=1  둘째 연결 -> 1 > 1 아님 -> 새 스레드 생성
```

```text
 thread_cache_size 기본값

 sys_vars.cc L4987-L4992  Sys_thread_cache_size
   GLOBAL_VAR(max_blocked_pthreads), DEFAULT(0), VALID_RANGE(0, 16384)

 mysqld.cc L6948-L6951   지정하지 않았으면
   8 + max_connections / 100, 최대 100 으로 맞춘다

 줄일 때 (SET GLOBAL)  modify_thread_cache_size  L360-L381
   shrink_cache = true 로 잠든 스레드를 깨워 초과분을 내보내고
   blocked_pthread_count 가 새 상한 이하가 될 때까지 기다린다
```

## 결과가 쓰이는 곳

```text
 false (넘김 성공)
      --> channel_info 는 이제 연결 스레드 소유다
      --> 새 스레드면 handle_connection 의 arg 로
      --> 캐시 스레드면 block_until_new_connection 의 반환값으로

 true (스레드 생성 실패)
      --> [01] 이 aborted_connects++ 하고 channel_info 를 지운다

 상태 변수 (mysqld.cc 의 등록 줄)
      --> Threads_created      inc_thread_created 가 올린다          L12047
      --> Threads_cached       blocked_pthread_count                 L12042
      --> Slow_launch_threads  init_new_thd 가 올린다                L11911
```

## 다루지 않는 것

`mysql_thread_create` 가 Performance Schema 계측을 붙여 `my_thread_create` 로 가는 과정, `connection_attrib`(스레드 스택 크기) 설정, `kill_blocked_pthreads`(L383)로 종료 때 캐시를 비우는 경로, `One_thread_connection_handler::add_connection` 은 스레드 생성의 곁가지라 요약만 했다.
