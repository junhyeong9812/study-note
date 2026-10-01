# os/26-io-multiplexing-epoll — 한 스레드가 수만 개 fd를 기다리는 법: select·poll·epoll과 레벨/엣지 트리거 — 정리 (힌트)

## 해결하는 문제

25번에서 논블로킹 fd는 "지금 없으면 `EAGAIN`"을 돌려준다고 했다.\
그럼 1만 개 연결 중 **어느 것에 데이터가 왔는지**는 어떻게 아나.

```text
  나쁜 방법 1: fd마다 스레드 하나, 블로킹 read          -> 스레드 1만 개 (36번)
  나쁜 방법 2: 1만 개 fd를 돌며 read, EAGAIN이면 다음    -> CPU를 태운다 (25번 장애 1)
  원하는 것:   "준비된 fd만 알려 줘. 없으면 재워 줘"     -> I/O 다중화
```

  - *I/O 다중화(multiplexing)*: 여러 fd를 한 번의 대기로 감시하고, 준비된 것만 알려 받는 방식이다.

쉬운 예: 푸드코트의 진동벨이다.
- select·poll: 직원이 매번 **모든 테이블**을 돌며 "음식 나왔어요?"라고 묻는다. 테이블이 많아질수록 한 바퀴가 길다.
- epoll: 음식이 나오면 그 벨만 울린다. 직원은 **울린 벨 목록**만 본다.

똑같은 구조다.\
select·poll은 호출할 때마다 감시 목록 전체를 커널에 넘기고 전체를 검사한다.\
epoll은 감시 목록을 커널에 **한 번 등록**해 두고, 준비된 것만 모인 목록을 받아 간다.

실무 예:
- Nginx·Redis·Node(libuv)·Netty·Java NIO `Selector`가 리눅스에서 epoll로 돈다.
- 오래된 C 서버가 fd 1024번을 넘기는 순간 죽는다(select의 `FD_SETSIZE`).
- 엣지 트리거로 바꿨더니 가끔 요청이 응답 없이 멈춘다.

## 동작·원리

### select — 비트맵을 매번 주고받는다

```text
  앱                                         커널
  fd_set readfds = [0 0 0 1 0 1 1 0 ... ]  --복사-->  0..nfds-1 전부 검사 (O(n))
  (비트 i = fd i를 감시)                              준비 안 된 비트는 지움
  readfds = [0 0 0 0 0 1 0 0 ... ]         <--복사--  "fd 5만 준비됨"
  앱: 비트 0..nfds-1을 다시 훑어 준비된 fd 찾기 (O(n))
  다음 호출 전: 지워진 비트를 다시 세팅해야 함 (값-결과 인자)
```

- `fd_set`은 고정 크기 비트맵이다. glibc는 `FD_SETSIZE`를 1024로 정의한다. 커널에는 고정 한계가 없지만 glibc 타입이 1024비트다(select(2) BUGS).
- fd 번호가 1024 이상이면 `FD_SET`은 **정의되지 않은 동작**이다(select(2) NOTES). man 페이지 첫머리부터 "이 한계는 바뀌지 않는다. poll이나 epoll을 쓰라"고 경고한다.
- 반환 시 집합을 제자리에서 고친다. 그래서 루프에서 매번 다시 채워야 한다. man은 이것을 "설계 오류"라고 부른다(select(2) BUGS).
- 리눅스 `select()`는 `timeout`도 남은 시간으로 고친다. 반환 후 `timeout`은 정의되지 않은 값으로 본다(select(2)).
- 준비 알림은 **힌트**다. 리눅스 select는 체크섬이 틀린 패킷을 버리는 경우처럼, 준비됐다고 알린 소켓의 read가 막힐 수 있다고 적는다(select(2) BUGS). 그래서 다중화와 함께 쓰는 fd는 논블로킹으로 둔다(Kegel C10K도 같은 권고).

```text
  FD_SETSIZE 초과 재현 (예시, 리눅스 7.0, gcc 13.3, glibc)
  FD_SETSIZE=1024 sizeof(fd_set)=128 bytes
  last fd=1102
  -O2 (Ubuntu 기본 _FORTIFY_SOURCE=3):   *** bit out of range 0 - FD_SETSIZE on fd_set ***: terminated   (exit 134 = SIGABRT)
  -O0 -U_FORTIFY_SOURCE:                 FD_SET(1102) returned (no abort)  <- 스택의 다른 변수를 조용히 덮었을 수 있다
```

### poll — 배열로 바꿨지만 여전히 전체 검사

```c
struct pollfd fds[N];                 /* {fd, events, revents} */
int n = poll(fds, N, timeout_ms);     /* N개 전부 커널에 복사·검사, 전부 돌려받음 */
```

- 개수 한계가 비트맵 크기에서 풀렸다. 입력(`events`)과 출력(`revents`)이 분리돼 매번 다시 채울 필요도 없다.
- 하지만 호출마다 N개를 복사하고 N개를 검사한다. 준비된 것이 1개여도 비용은 N에 비례한다.

### epoll — 등록은 한 번, 준비된 것만 받아 간다

```text
  epoll_create1()  -> epfd (커널 안 eventpoll 객체, /proc에서 anon_inode:[eventpoll])

  +----------------------- eventpoll 객체 ------------------------+
  |  관심 목록 (interest list)          준비 목록 (ready list)       |
  |  레드블랙 트리, 키 = (fd, 파일)      이중 연결 리스트              |
  |     [fd 5]  [fd 9]  [fd 12] ...  ->   [fd 9] [fd 12]             |
  +----------------------------------------------------------------+
        ^ epoll_ctl(ADD/MOD/DEL)              | epoll_wait()가 여기서 꺼내 감
        |                                     |
  소켓 fd 9의 대기 큐에 콜백(ep_poll_callback)을 걸어 둠
  패킷 도착 -> 소켓이 대기 큐를 깨움 -> 콜백이 fd 9 항목을 준비 목록에 붙임
```

- `epoll_ctl(EPOLL_CTL_ADD)`는 관심 목록에 항목을 넣는다. 이때 감시 대상 파일의 대기 큐에 콜백을 건다(fs/eventpoll.c 개요 주석).
- 대상이 준비되면 콜백(`ep_poll_callback`)이 항목을 준비 목록에 붙인다.
- `epoll_wait()`는 준비 목록을 비워 가며 이벤트를 돌려준다. 비어 있으면 잠든다(epoll(7)).
- 그래서 `epoll_wait` 비용은 감시 fd 수가 아니라 **준비된 fd 수**에 비례한다.
  - 관심 목록 추가·삭제(`epoll_ctl`)는 트리 연산이라 O(log n)이다.
- epoll(7)은 관심 목록의 키를 "fd 번호 + open file description"의 조합이라고 적는다.

```text
  감시 fd 수에 따른 호출 1회 비용 — 준비된 fd는 1개 (예시, 리눅스 7.0, 부하 있는 24코어 머신)
       N    poll()          epoll_wait()
      10    1.4 us          0.6 us
     100    5.1 us          0.3 us
    1000   87   us          0.2 us
   10000  4456   us          0.3 us
```

### 레벨 트리거 vs 엣지 트리거

epoll(7)의 파이프 예를 그대로 재현한 것이다.

```text
  (1) 파이프 읽기 쪽 rfd를 epoll에 등록
  (2) 쓰는 쪽이 2KB 씀
  (3) epoll_wait -> rfd 준비됨
  (4) 1KB만 읽음                      (1KB 남음)
  (5) epoll_wait -> ?

                     (5)의 결과            이유
  레벨 트리거(기본)   rfd 준비됨 (즉시)      "읽을 게 남아 있다"는 상태를 매번 알린다
  엣지 트리거(EPOLLET) 알림 없음 (계속 대기)  "새로 준비됐다"는 변화만 알린다. (2)의 변화는 (3)에서 소비됨
```

```text
  재현 (예시, 리눅스 7.0 — 유닉스 소켓, 2048B 쓰고 1024B 읽음, 대기 100ms)
  LT: wait1=1 read=1024 wait2=1
  ET: wait1=1 read=1024 wait2=0 | 새 1B 도착: wait3=1 read_all=1025 then=-1(EAGAIN)
```

- 레벨 트리거(LT)는 "준비된 **상태**"를 알린다. 커널은 LT 항목을 이벤트로 돌려준 뒤 준비 목록에 **다시 넣는다**(fs/eventpoll.c: "re-queueing items in level-triggered mode"). 다음 `epoll_wait`에서 다시 검사한다.
- 엣지 트리거(ET)는 "준비되지 않음 → 준비됨" **변화**만 알린다. 남은 데이터는 새 데이터가 와서 또 변화가 생길 때까지 알림이 없다.
- 그래서 ET 사용법은 epoll(7)이 정해 둔다.
  - fd를 **논블로킹**으로 둔다.
  - `read`/`write`가 **`EAGAIN`을 돌려줄 때까지** 처리한 뒤에만 다시 기다린다.
- 스트림(소켓·파이프)이면 `read`가 요청보다 적게 돌려준 것으로도 "비었다"를 알 수 있다. 데이터그램·정규 모드 터미널이면 `EAGAIN`까지 읽는 방법뿐이다(epoll(7) Q&A).
- LT는 "더 빠른 poll"이다. poll과 의미가 같아 poll 자리에 그대로 쓸 수 있다(epoll(7)).

  - *레벨 트리거 / 엣지 트리거*: 하드웨어 인터럽트 용어에서 왔다. 전압이 "높은 상태"에 반응하면 레벨, "올라가는 순간"에 반응하면 엣지다.

### 알아 둘 플래그

| 플래그 | 뜻 | 근거 |
|---|---|---|
| `EPOLLET` | 엣지 트리거 | epoll(7) |
| `EPOLLONESHOT`(2.6.2+) | 한 번 알린 뒤 비활성. `EPOLL_CTL_MOD`로 다시 켜야 한다. 여러 스레드가 한 epfd를 기다릴 때 같은 fd를 두 스레드가 동시에 처리하지 않게 | epoll_ctl(2) |
| `EPOLLEXCLUSIVE`(4.5+) | 같은 대상 fd에 여러 epfd가 걸려 있을 때 하나 이상만 깨운다(기본은 전부). thundering herd 완화 | epoll_ctl(2) |
| `EPOLLRDHUP`(2.6.17+) | 상대가 연결을 닫거나 쓰기 쪽을 닫음. ET에서 상대 종료 감지에 유용 | epoll_ctl(2) |
| `EPOLLERR`·`EPOLLHUP` | 따로 요청하지 않아도 항상 보고된다 | epoll_ctl(2) |

  - *thundering herd*: 이벤트 하나에 기다리던 여러 스레드·프로세스가 한꺼번에 깨어나고, 하나만 일을 얻고 나머지는 헛걸음하는 현상이다.
- 같은 epfd를 여러 스레드가 기다리는 중에 ET 항목이 준비되면 그중 한 스레드만 깨어난다(epoll(7)).

### 닫기와 dup의 함정

```text
  fd 7 ─┐
        ├──> open file description X  <── 관심 목록의 키는 (fd 7, X)
  fd 9 ─┘    (dup, fork로 생긴 복사본)

  close(7)   -> X가 아직 fd 9로 살아 있다 -> 관심 목록에서 안 빠진다 -> fd 7 이름으로 이벤트가 계속 올 수 있다
```

- 관심 목록에서 빠지는 시점은 그 open file description을 가리키는 **모든** fd가 닫힌 뒤다(epoll(7) Q&A).
- 그래서 dup·fork 가능성이 있으면 `EPOLL_CTL_DEL`을 먼저 한다. epoll(7)은 "dup하기 전에" 빼라고 적는다. fd가 아직 그 open file description을 가리키는 동안(`close` 전)이면 DEL로 항목이 빠진다.

### 한도

- `/proc/sys/fs/epoll/max_user_watches`(2.6.28+): 실제 사용자 ID당 전체 epoll 인스턴스에 등록할 수 있는 fd 수의 상한이다. 기본값은 가용 low memory의 4%를 항목 비용(64비트 약 160바이트)으로 나눈 값이다(epoll(7)). 넘으면 `EPOLL_CTL_ADD`가 `ENOSPC`(epoll_ctl(2)). 작성 환경은 8,590,959였다(예시).
- 실제로는 프로세스 fd 한도(`ulimit -n`, `RLIMIT_NOFILE`)에 먼저 걸리는 일이 많다(`EMFILE`, network/23).

### 다른 OS

- FreeBSD는 kqueue, Solaris는 `/dev/poll`이다(epoll(7) VERSIONS). libuv는 macOS·BSD에서 kqueue, SunOS에서 event ports를 쓴다(libuv 설계 문서).
- Windows IOCP는 "준비됨"이 아니라 "**완료됨**"을 알린다. 모델이 다르다(34번·36번 프로액터).

## 쓰이는 자료구조·알고리즘

- **비트맵(select)** — fd 번호 = 비트 위치. 크기가 고정이라 1024에서 막힌다. [data-structure/18-bitset](../../data-structure/18-bitset/2-summary.md)
- **배열 선형 탐색(select·poll)** — 호출마다 O(n) 복사·검사.
- **레드블랙 트리(epoll 관심 목록)** — fs/eventpoll.c의 `struct rb_root_cached rbr`. 등록·삭제·중복 검사(`EEXIST`)를 O(log n)에. [data-structure/16-red-black-tree](../../data-structure/16-red-black-tree/2-summary.md)
- **이중 연결 리스트(준비 목록)** — `rdllist`. 준비된 항목만 꼬리에 붙이고 앞에서 꺼낸다. [data-structure/02-linked-list](../../data-structure/02-linked-list/2-summary.md)
- **대기 큐 + 콜백** — 소켓의 대기 큐에 "깨울 스레드" 대신 "준비 목록에 붙이는 함수"를 건다. 옵저버 패턴의 커널판이다.

## 적용 — 풀어나가는 법

### 1. C — 엣지 트리거 루프의 뼈대

```c
int ep = epoll_create1(EPOLL_CLOEXEC);
struct epoll_event ev = { .events = EPOLLIN, .data.fd = lfd };   /* 리슨 소켓(논블로킹) */
epoll_ctl(ep, EPOLL_CTL_ADD, lfd, &ev);

for (;;) {
    struct epoll_event evs[64];
    int n = epoll_wait(ep, evs, 64, -1);
    if (n < 0 && errno == EINTR) continue;                  /* 시그널에 끊김 */
    for (int i = 0; i < n; i++) {
        int fd = evs[i].data.fd;
        if (fd == lfd) {                                    /* 새 연결: EAGAIN까지 accept */
            int c;
            while ((c = accept4(lfd, NULL, NULL, SOCK_NONBLOCK | SOCK_CLOEXEC)) >= 0) {
                struct epoll_event ce = { .events = EPOLLIN | EPOLLET | EPOLLRDHUP, .data.fd = c };
                epoll_ctl(ep, EPOLL_CTL_ADD, c, &ce);
            }
            continue;                                       /* errno == EAGAIN이면 정상 */
        }
        for (;;) {                                          /* ET: EAGAIN까지 끝까지 읽는다 */
            char buf[4096];
            ssize_t r = read(fd, buf, sizeof buf);
            if (r > 0) { handle(fd, buf, r); continue; }
            if (r == 0 || (errno != EAGAIN && errno != EWOULDBLOCK)) {
                epoll_ctl(ep, EPOLL_CTL_DEL, fd, NULL);     /* close 전에 DEL (dup 함정) */
                close(fd);
            }
            break;                                          /* EAGAIN: 다 읽었다 */
        }
    }
}
```

- 한 연결이 데이터를 끝없이 보내면 "EAGAIN까지 읽기"가 다른 연결을 굶길 수 있다. epoll(7)은 앱 쪽에 준비 목록을 따로 두고 연결들을 돌아가며(round robin) 처리하라고 권한다.

### 2. Java — NIO Selector는 리눅스에서 epoll(레벨 트리거)

```java
Selector sel = Selector.open();                     // 리눅스 JDK: EPollSelectorProvider
ServerSocketChannel ss = ServerSocketChannel.open();
ss.bind(new InetSocketAddress(8080));
ss.configureBlocking(false);
ss.register(sel, SelectionKey.OP_ACCEPT);
while (true) {
    sel.select();                                   // epoll_wait
    Iterator<SelectionKey> it = sel.selectedKeys().iterator();
    while (it.hasNext()) {
        SelectionKey k = it.next(); it.remove();    // 직접 지워야 한다
        if (k.isAcceptable()) {
            SocketChannel c = ss.accept();
            if (c == null) continue;
            c.configureBlocking(false);
            c.register(sel, SelectionKey.OP_READ, ByteBuffer.allocate(4096));
        } else if (k.isReadable()) {
            SocketChannel c = (SocketChannel) k.channel();
            ByteBuffer b = (ByteBuffer) k.attachment();
            if (c.read(b) == -1) { k.cancel(); c.close(); }
            // 레벨 트리거라 덜 읽어도 다음 select에서 다시 알려 준다
        }
    }
}
```

- OpenJDK 리눅스 구현은 `EPollSelectorProvider`를 기본으로 쓰고(`DefaultSelectorProvider`), 관심 등록에 `EPOLLET`을 붙이지 않는다(`EPollSelectorImpl`). 즉 레벨 트리거다.
- Netty의 네이티브 epoll 전송은 기본이 엣지 트리거다(`AbstractEpollChannel`의 `flags = Native.EPOLLET`). `EpollMode.LEVEL_TRIGGERED`로 바꿀 수 있다.
- Node는 libuv가 리눅스에서 epoll을 쓴다(libuv 설계 문서).

### 3. 진단 명령

```bash
# 프로세스의 epoll 인스턴스 찾기
ls -l /proc/<pid>/fd | grep eventpoll          # -> anon_inode:[eventpoll]

# 그 epfd가 무엇을 감시하나 (tfd = 대상 fd, events = 관심 비트, 16진수)
cat /proc/<pid>/fdinfo/<epfd>
#   tfd:        3 events:       19 data: ...     (예시: 0x19 = EPOLLIN|EPOLLERR|EPOLLHUP)
#   tfd:        3 events: 80000019 data: ...     (0x80000000 = EPOLLET)

# 이벤트 루프가 무엇을 기다리고 몇 개씩 깨어나나
strace -f -tt -e trace=epoll_wait,epoll_pwait,epoll_ctl -p <pid>

# 한도
ulimit -n
cat /proc/sys/fs/epoll/max_user_watches
```

## 장애 시나리오와 대처

### 1. 엣지 트리거에서 끝까지 안 읽음 → 연결 hang

- **현상**: 대부분 정상인데 일부 요청이 응답 없이 멈춘다. 클라이언트는 결국 타임아웃. 큰 요청이나 파이프라이닝된 요청에서 잘 난다.
- **보이는 형태**
  - 서버 `ss -tn`에서 그 연결의 **Recv-Q가 0이 아닌 채** 머문다(커널 수신 버퍼에 데이터가 남아 있다).
  - `strace`에 그 fd의 `read`가 더 이상 나오지 않는다. 이벤트 루프는 다른 fd로는 정상 동작한다.
- **원인**: ET로 등록하고 한 번만 `read`했다. 남은 데이터에 대해서는 새 변화가 없으니 알림이 오지 않는다. 상대는 응답을 기다리고 있어 새 데이터도 보내지 않는다(epoll(7)의 "probably hang" 예).
- **대처**
  - ET면 `EAGAIN`까지 읽고 쓴다. 공정성이 필요하면 앱 준비 목록으로 돌아가며 처리한다.
  - 확신이 없으면 LT를 쓴다(Java NIO 기본).

### 2. select로 fd 1024 초과 → abort 또는 메모리 손상

- **현상**: 연결 수가 늘다 어느 순간 프로세스가 죽거나 이상하게 동작한다.
- **보이는 형태**
  - `_FORTIFY_SOURCE` 빌드: `*** bit out of range 0 - FD_SETSIZE on fd_set ***: terminated`, exit code 134(SIGABRT). 로컬 재현에서 그대로 났다.
  - 보호 없는 빌드: 에러 없이 스택의 인접 변수가 덮여 엉뚱한 곳에서 터진다.
- **원인**: glibc `fd_set`은 1024비트 고정이다. fd 번호가 1024 이상이면 `FD_SET`은 정의되지 않은 동작이다(select(2)). `ulimit -n`을 올려도 이 한계는 그대로다.
- **대처**: poll이나 epoll로 바꾼다. 당장은 fd를 1024 아래로 유지하는 것밖에 없다.

### 3. LT에서 EPOLLOUT을 상시 등록 → 이벤트 루프가 헛돈다

- **현상**: 보낼 것이 없는데 CPU가 높다.
- **보이는 형태**: `strace`에 `epoll_wait(...) = 1`이 쉼 없이 돌아온다. 로컬 재현(예시, 리눅스 7.0): 쓸 것 없이 `EPOLLIN|EPOLLOUT`을 LT로 등록하니 1초에 약 330만 번 깨어났다.
- **원인**: 소켓 송신 버퍼에 자리가 있으면 "쓰기 가능"은 **거의 늘 참인 상태**다. LT는 상태를 매번 알린다.
- **대처**: 보낼 데이터가 남았을 때만 `EPOLLOUT`을 켜고(`EPOLL_CTL_MOD`), 다 보내면 끈다. NIO도 같은 규칙이다(`OP_WRITE`는 쓰다 막혔을 때만).

### 4. dup·fork 후 close → 닫은 fd로 유령 이벤트

- **현상**: 이미 닫은 연결 번호로 이벤트가 오고, 그 번호를 재사용한 새 연결을 엉뚱하게 처리한다.
- **보이는 형태**: 간헐적 요청 뒤섞임, 처리 중 `EBADF`.
- **원인**: 관심 목록은 open file description이 살아 있는 한 항목을 유지한다. `fork()`한 자식이나 라이브러리의 `dup()`이 복사본을 쥐고 있으면 `close()`로는 빠지지 않는다(epoll(7) Q&A).
- **대처**: `close` 전에 `EPOLL_CTL_DEL`. fd를 만들 때 `O_CLOEXEC`/`SOCK_CLOEXEC`, epfd는 `EPOLL_CLOEXEC`로 exec 누수를 막는다.

### 5. 여러 워커가 같은 리슨 소켓을 기다림 → thundering herd

- **현상**: 연결 하나 들어올 때마다 모든 워커가 깨어나고 하나만 `accept`에 성공한다. 연결률이 낮을 때 CPU·컨텍스트 스위치가 쓸데없이 는다.
- **보이는 형태**: 나머지 워커의 `accept`가 `EAGAIN`. `pidstat -w`에서 자발적 컨텍스트 스위치 증가.
- **원인**: 각 워커의 epfd가 같은 리슨 소켓을 감시하면 기본 동작은 모든 epfd를 깨우는 것이다(epoll_ctl(2) `EPOLLEXCLUSIVE` 설명).
- **대처**
  - `EPOLLEXCLUSIVE`(4.5+)로 등록한다.
  - 워커마다 리슨 소켓을 따로 두고 `SO_REUSEPORT`(3.9+)로 커널이 나눠 주게 한다(socket(7)).
  - nginx 문서는 `EPOLLEXCLUSIVE`나 `reuseport`가 있으면 `accept_mutex`가 필요 없다고 적는다(nginx 1.11.3부터 기본 off).

## 핵심 문장

- select·poll은 호출마다 감시 목록 **전체**를 넘기고 검사한다(O(n)). epoll은 관심 목록을 커널에 **한 번 등록**하고, 준비된 것만 모인 목록을 받아 간다(O(준비된 수)).
- select의 `fd_set`은 glibc에서 1024비트 고정이다. fd 번호 1024 이상은 정의되지 않은 동작이라, 보호 빌드는 abort하고 아니면 메모리를 조용히 덮는다.
- epoll 관심 목록은 레드블랙 트리, 준비 목록은 연결 리스트다. 대상의 대기 큐에 건 콜백이 준비 목록을 채운다.
- 레벨 트리거는 "준비된 상태"를, 엣지 트리거는 "준비된 순간"을 알린다. ET는 논블로킹 fd로 `EAGAIN`까지 처리해야 하고, 안 그러면 남은 데이터가 영원히 묻힌다.
- 관심 목록의 키는 fd가 아니라 (fd, open file description)이다. dup·fork가 있으면 close 전에 `EPOLL_CTL_DEL`.

## 관련 주제·근거

- 선행: [25-io-models](../25-io-models/2-summary.md) — 논블로킹·`EAGAIN`, 준비 알림 vs 완료 알림
- 함께: [21-files-and-descriptors](../21-files-and-descriptors/2-summary.md) — fd와 open file description(관심 목록 키, dup·fork 함정의 바탕)
- 후속
  - [27-event-based-concurrency](../27-event-based-concurrency/2-summary.md) — epoll 위에 이벤트 루프 쌓기
  - [34-zero-copy-and-io-uring](../34-zero-copy-and-io-uring/2-summary.md) — 준비 알림이 아닌 완료 큐
  - [36-server-concurrency-architectures](../36-server-concurrency-architectures/2-summary.md) — 단일·멀티 리액터, `SO_REUSEPORT`
- 다른 영역
  - [network/23-socket-api](../../network/23-socket-api/2-summary.md) — `EMFILE`에서 LT 리슨 소켓 바쁜 루프, 부분 쓰기와 `EPOLLOUT`
  - [data-structure/16-red-black-tree](../../data-structure/16-red-black-tree/2-summary.md) — epoll 관심 목록
- man
  - epoll(7) — 관심/준비 목록, LT·ET 파이프 예, ET 사용법, thundering herd, Q&A(키·close·dup), `max_user_watches` <https://man7.org/linux/man-pages/man7/epoll.7.html>
  - epoll_ctl(2) — `EPOLLET`·`EPOLLONESHOT`(2.6.2)·`EPOLLEXCLUSIVE`(4.5)·`EPOLLRDHUP`(2.6.17), `ENOSPC`, 정규 파일 `EPERM` <https://man7.org/linux/man-pages/man2/epoll_ctl.2.html>
  - epoll_wait(2) — 타임아웃(-1 무한, 0 즉시), `EINTR` <https://man7.org/linux/man-pages/man2/epoll_wait.2.html>
  - select(2) — `FD_SETSIZE` 1024 경고, 값-결과 인자 "설계 오류", `timeout` 수정, 거짓 준비 가능성 <https://man7.org/linux/man-pages/man2/select.2.html>
  - poll(2) <https://man7.org/linux/man-pages/man2/poll.2.html>
  - socket(7) — `SO_REUSEPORT`(3.9) <https://man7.org/linux/man-pages/man7/socket.7.html>
  - (로컬 man-pages 6.7, 2023-10-31판으로 대조)
- 소스
  - fs/eventpoll.c — 개요 주석(ep_poll_callback, LT 재큐잉), `struct rb_root_cached rbr`, `rdllist` <https://github.com/torvalds/linux/blob/master/fs/eventpoll.c>
  - OpenJDK `sun/nio/ch/DefaultSelectorProvider.java`(linux) → `EPollSelectorProvider`, `EPollSelectorImpl.java`(EPOLLET 미사용) <https://github.com/openjdk/jdk/tree/master/src/java.base/linux/classes/sun/nio/ch>
  - Netty 4.1 `AbstractEpollChannel`(`flags = Native.EPOLLET`), `EpollMode` <https://github.com/netty/netty/tree/4.1/transport-classes-epoll>
- 문서
  - Dan Kegel, "The C10K problem" — I/O 전략 1(논블로킹 + 레벨 트리거 준비 알림), 2(준비 "변화" 알림 = 엣지 트리거), "준비 알림은 힌트일 뿐" <http://www.kegel.com/c10k.html>
  - nginx `ngx_core_module` — `accept_mutex`(1.11.3부터 기본 off, `EPOLLEXCLUSIVE`·`reuseport`면 불필요) <https://nginx.org/en/docs/ngx_core_module.html#accept_mutex>
  - libuv Design overview — 리눅스 epoll, macOS·BSD kqueue, SunOS event ports <https://docs.libuv.org/en/v1.x/design.html>
- 교재: OSTEP 33장 33.2~33.3 select()/poll(), CS:APP 3판 12.2 "Concurrent Programming with I/O Multiplexing"(3판 서문 PDF 목차로 확인 <http://csapp.cs.cmu.edu/3e/pieces/preface3e.pdf>)
- 로컬 재현(리눅스 7.0, gcc 13.3): LT/ET 차이(2048B 쓰고 1024B 읽기), `/proc/self/fdinfo`의 `EPOLLET` 비트, `FD_SET(1102)` fortify abort(exit 134) vs 무보호 무증상, poll vs epoll_wait N별 비용, LT `EPOLLOUT` 상시 등록 시 초당 깨어남 수
