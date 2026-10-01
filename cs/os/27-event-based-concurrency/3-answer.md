# os/27-event-based-concurrency — 정답

## 정답

### 1. 이벤트 루프와 스케줄링

```text
  while (1) {
      events = getEvents();      // epoll_wait 등: 준비된 이벤트 받기
      for (e in events)
          processEvent(e);       // 핸들러 실행 (짧게)
  }
```

- 핸들러가 이벤트를 처리하는 동안 그 시스템에서는 **그 핸들러만** 돈다.
- 그래서 "다음에 어떤 이벤트를 처리할지"를 앱이 고르는 순간이 곧 스케줄링 결정이다. OS 스케줄러가 아니라 앱이 순서를 통제한다(OSTEP 33.1).

### 2. 락이 필요 없는 이유와 멀티코어

- 한 번에 이벤트 하나만 처리되고, 다른 스레드가 끼어들 수 없다. 그래서 스레드 프로그램의 동시성 버그가 기본 이벤트 방식에서는 나타나지 않는다(OSTEP 33.4).
- 코어를 다 쓰려고 루프를 여러 개 병렬로 돌리면 핸들러들이 동시에 실행된다. 공유 상태가 있으면 임계 구역·락이 다시 필요하다(OSTEP 33.8).
- 실무의 우회: 루프끼리 상태를 공유하지 않게 연결을 나눠 맡긴다(nginx 워커, Netty 채널-루프 고정, 36번).

### 3. 리액터

```text
  Initiation Dispatcher (루프, 핸들러 등록표 fd -> handler)
      | handle_events()
      v
  Synchronous Event Demultiplexer  ---- 리눅스: epoll_wait (또는 select/poll)
      | 준비된 fd들
      v
  Event Handler.handle_event()     ---- 연결별: 읽기·처리·쓰기, 짧게 반환
```

- 비선점 한계: 핸들러는 실행 도중 끊기지 않는다. 그래서 핸들러가 블로킹 I/O를 하면 프로세스 전체가 막히고 다른 핸들의 클라이언트 응답성이 떨어진다. 논문은 긴 작업을 Active Object(별도 스레드)로 넘기라고 한다(Schmidt, Reactor 11.2).

### 4. 500ms 동기 루프와 타이머

- 로컬 재현(예시, 리눅스 7.0, Node 18.19.1)

```text
  tick gap 101 ms
  tick gap 100 ms
  blocked 500ms (sync loop)
  tick gap 558 ms
  tick gap 101 ms
```

- 동기 루프가 도는 동안 이벤트 루프는 다음 단계로 못 넘어간다. 만기된 타이머도, epoll이 알려 줄 I/O도 처리되지 않는다.
- 그 사이 들어온 HTTP 요청은 커널 소켓 버퍼(연결이면 accept 큐, network/15)에 쌓여 있다가 루프가 풀린 뒤 처리된다. 응답 시간에 최대 약 500ms가 더해진다.
- 타이머는 "최소 지연"이라 정확한 시점을 보장하지 않는다(Node timers 문서).

### 5. 타이머 자료구조

- **libuv**: 최소 힙. `src/timer.c`가 `heap_insert`로 넣고 `heap_min`으로 가장 이른 만기를 본다. `uv__next_timeout`이 "힙 최솟값 − 현재 시각"을 계산해 I/O 대기(epoll) 타임아웃으로 쓴다. 타이머가 없으면 무한 대기다.
  - 비용: 최솟값 조회 O(1), 삽입·삭제 O(log n).
- **Redis ae.c**: 시간 이벤트를 정렬되지 않은 연결 리스트로 둔다. 다음 타이머를 찾는 데 O(N)이라고 소스 주석이 적는다. Redis는 시간 이벤트가 적다는 전제로 이 단순함을 택했다.

### 6. manual stack management와 continuation

- 스레드 코드에서는 `read(fd)` 뒤 `write(sd)`에 필요한 `sd`가 **스레드 스택**에 남아 있다.
- 이벤트 코드에서는 비동기 read를 걸고 핸들러를 반환해야 한다. 스택이 사라지므로 `sd` 같은 "이어서 할 일에 필요한 상태"를 앱이 직접 자료구조(예: fd → sd 해시 테이블)에 저장했다가 완료 이벤트 때 꺼내야 한다. 이것이 manual stack management다(OSTEP 33.7, Adya 외 2002).
- continuation은 "남은 계산"을 값으로 들고 다니는 방법이다. 콜백 함수 + 클로저가 대표적이다.
- `async/await`는 컴파일러가 함수를 상태 기계로 바꾸고 지역 변수를 그 상태 객체에 옮겨 준다. 즉 continuation을 언어가 자동으로 만든다.

### 7. 블로킹 호출 없이도 멈추는 경우

- **페이지 폴트**: 핸들러가 스왑 아웃된 페이지나 아직 안 읽힌 mmap 파일 페이지를 건드리면 폴트 처리 동안 스레드가 블록된다. 코드에 보이는 블로킹 호출이 없어 피하기 어렵다(OSTEP 33.8).
- 확인: `pidstat -r -p <pid> 1`의 `majflt/s`(주 페이지 폴트), `vmstat 1`의 `si`/`so`(스왑 입출력), `ps -L`에서 루프 스레드의 `D` 상태.

### 8. pbkdf2와 DNS·파일 지연

- 의심: **libuv 스레드 풀 고갈**. 기본 4개 스레드를 `fs.*`, 비동기 암호 함수(`pbkdf2` 등), `dns.lookup`이 나눠 쓴다. 해시 작업이 4개를 모두 차지하면 나머지는 큐에서 기다린다.
  - 호스트 이름으로 여는 HTTP 요청은 내부에서 `dns.lookup`을 부른다. Node 문서도 `dns.lookup`이 스레드 풀의 동기 `getaddrinfo`라 성능 문제가 생길 수 있다고 경고한다.
- 재현 근거(예시, 리눅스 7.0): `pbkdf2` 8개를 동시에 시작하면 풀 4에서는 두 물결(약 80ms, 약 150ms)로 끝났고, 풀 8에서는 한 물결로 끝났다.
- 고치기
  - `UV_THREADPOOL_SIZE`를 늘린다(시작 전에, 최대 1024).
  - `dns.resolve*`나 DNS 캐시를 쓴다.
  - 해시 같은 CPU 작업은 `worker_threads`로 옮긴다.

### 9. Netty 전체 지연 스파이크

- 스레드 덤프에서 `nioEventLoopGroup-*`/`epollEventLoopGroup-*` 스레드를 본다. JDBC 쿼리, 블로킹 HTTP 클라이언트, `Thread.sleep`, 큰 직렬화 같은 스택이 있으면 원인이다. 그 루프에 묶인 모든 채널이 같이 멈춘다.
- 고치기: 블로킹 핸들러를 별도 `EventExecutorGroup`에 붙인다.

```java
pipeline.addLast(new DefaultEventExecutorGroup(16), "handler", new MyBusinessLogicHandler());
```

- 남는 병목: Netty `ChannelPipeline` 문서는 `DefaultEventLoopGroup`으로 넘겨도 `ChannelHandlerContext`별로는 **순서대로** 처리된다고 경고한다(순서를 보장하는 그룹이면 같은 성질이다). 한 채널의 요청이 줄 서 있으면 여전히 병목이다. 순서가 필요 없으면 `UnorderedThreadPoolEventExecutor` 같은 대안을 고려한다(Javadoc 권고).
- 이벤트 루프에서 자기 결과를 블로킹으로 기다리면 `BlockingOperationException`이 난다. 교착 가능성 때문이다.

### 10. Redis KEYS

- Redis는 대부분 단일 스레드로 모든 클라이언트 요청을 **순서대로** 처리한다(Redis latency 문서). 이벤트 루프 하나다.
- `KEYS`는 키 공간 전체를 훑는 O(N) 명령이다. 그동안 루프가 다른 명령을 처리하지 못하니 모든 클라이언트가 기다린다. 문서는 이것을 운영 지연의 "매우 흔한 원인"으로 꼽고 디버깅 용도로만 쓰라고 한다.
- 대안: Redis 2.8부터 있는 `SCAN`(`SSCAN`·`HSCAN`·`ZSCAN`)으로 조금씩 나눠 순회한다. 이벤트 루프 원리로 말하면 "긴 핸들러를 짧은 조각으로 쪼개기"다.
