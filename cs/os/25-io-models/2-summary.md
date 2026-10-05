# os/25-io-models — 기다리는 방법 네 가지: 블로킹/논블로킹 × 동기/비동기 — 정리 (힌트)

## 해결하는 문제

`read(fd, buf, n)`를 불렀는데 읽을 데이터가 아직 없다.\
이때 커널은 둘 중 하나를 해야 한다.

```text
  read() 호출, 데이터 없음
     |
     +-- (a) 호출한 스레드를 재운다. 데이터가 오면 깨워서 돌려준다.   <- 블로킹
     |
     +-- (b) "지금은 없다"고 바로 돌려준다 (EAGAIN).                 <- 논블로킹
```

(a)는 쓰기 쉽다. 대신 **스레드 하나가 연결 하나에 묶인다.**\
연결이 1만 개면 잠든 스레드도 1만 개가 필요하다(36번).\
(b)는 스레드를 묶지 않는다. 대신 "그럼 언제 다시 물어보나"를 앱이 풀어야 한다.

그리고 두 번째 축이 있다. **데이터를 내 버퍼로 옮기는 일까지 누가 끝내 주나.**
- 내가 `read()`를 불러서 옮긴다 → 동기.
- 커널이 옮겨 놓고 "끝났다"고 알려 준다 → 비동기.

쉬운 예: 택배를 받는 방법이다.
- 문 앞에서 올 때까지 서 있는다 → 블로킹.
- 5분마다 문을 열어 본다 → 논블로킹(폴링).
- "도착하면 문자 주세요" 받고 내가 가지러 간다 → 준비 알림(다중화, 26번).
- "집 안 냉장고에 넣어 두고 문자 주세요" → 비동기(완료 알림, 34번 io_uring).

똑같은 구조다.\
앞의 셋은 결국 **내가 물건을 들고 들어오는** 단계가 남는다. 마지막만 그 단계까지 남이 끝낸다.

실무 예:
- 톰캣 기본 스레드 200개(`maxThreads`)가 느린 외부 API를 기다리며 전부 잠들면 새 요청을 못 받는다.
- 논블로킹 소켓에서 `EAGAIN`을 무시하고 바로 다시 `read()`하면 CPU 한 코어가 헛돈다.
- Node에서 `fs.readFileSync`를 요청 처리 중에 부르면 서버 전체가 그 파일을 기다린다.

## 동작·원리

### read 한 번은 두 단계다

```text
  시간 --->
  앱 스레드      read() 호출                                  반환
                   |                                          ^
  커널           [① 데이터 준비 대기] ---------> [② 커널 버퍼 -> 사용자 버퍼 복사]
                   소켓: 패킷 도착까지              memcpy (CPU)
                   파일: 디스크 읽기까지 (페이지 캐시에 없으면)
```

- ① **준비 대기**: 데이터가 커널 버퍼(소켓 수신 버퍼, 페이지 캐시)에 들어올 때까지다. 길고 예측할 수 없다.
- ② **복사**: 커널 버퍼에서 앱이 준 버퍼로 옮긴다. 짧지만 CPU가 한다.
- I/O 모델은 "①과 ② 동안 호출한 스레드가 무엇을 하나"로 나뉜다.

### 다섯 가지 모델 (Stevens의 분류)

```text
                      ① 준비 대기 동안             ② 복사 동안        완료를 아는 방법
  1 블로킹            read()에서 잠듦              read() 안에서 잠듦   read() 반환
  2 논블로킹          read()가 EAGAIN, 다시 호출    read() 안에서 대기   read() 반환
  3 I/O 다중화        select/poll/epoll에서 잠듦   read() 안에서 대기   준비 알림 -> read()
  4 시그널 구동       다른 일 (SIGIO 대기)         read() 안에서 대기   SIGIO -> read()
  5 비동기            다른 일                      다른 일              완료 알림 (CQE·시그널)
```

- 1~4는 모두 ②에서 스레드가 멈춘다. 그래서 POSIX 정의로는 **동기 I/O**다.
- 5만 ②까지 커널이 끝낸다. 이것이 **비동기 I/O**다.
- 이 다섯 분류는 Stevens 『UNIX Network Programming』 1권 6.2절로 알려져 있다 [?] (책 원문 미확인). 아래 POSIX 정의는 원문으로 확인했다.

POSIX 정의(XBD 3장):
- *동기 I/O 연산(3.371)*: I/O를 요청한 스레드를 그 I/O가 끝날 때까지 프로세서에서 막는 연산이다.
- *비동기 I/O 연산(3.31)*: 그 자체로는 요청한 스레드를 막지 않는 연산이다. 프로세스와 I/O가 동시에 진행될 수 있다.
- *블로킹(3.48)*: open file description의 속성이다. 요청한 동작이 이뤄질 때까지 기다렸다 반환한다.
- *논블로킹(3.226)*: 역시 open file description의 속성이다. "알 수 없는 지연" 없이는 못 끝내면 바로 반환한다. 정확한 의미는 파일 종류에 따라 다르다.
  - *open file description*: `open()`이 만든 커널 쪽 "열린 파일" 객체다. 파일 오프셋과 상태 플래그(`O_NONBLOCK` 등)를 가진다. fd는 이것을 가리키는 번호다(21번).

그래서 두 축은 다른 것을 묻는다.
- 블로킹/논블로킹: **fd의 속성**. "못 끝내면 기다리나, 바로 돌아오나."
- 동기/비동기: **연산의 성질**. "복사까지 끝나야 스레드가 풀리나."

### 4분면 표

```text
                    동기 (내가 read로 복사)              비동기 (커널이 복사까지 완료)
               +------------------------------------+------------------------------------+
  블로킹       | read() on 블로킹 fd                  | (드묾) 제출 후 완료를 블로킹 대기     |
               | Java InputStream.read                | io_uring_enter(..., GETEVENTS)로   |
               |                                      | 완료를 기다림                        |
               +------------------------------------+------------------------------------+
  논블로킹     | O_NONBLOCK + EAGAIN 재시도            | io_uring·POSIX AIO·Windows IOCP    |
               | + 준비 알림(select/epoll) = 26번     | 제출 즉시 반환, 완료 큐에서 결과    |
               +------------------------------------+------------------------------------+
```

- 이 표의 칸 이름은 자료마다 조금씩 다르다. "select는 블로킹-비동기"라고 부르는 자료도 있다. 이름보다 **①·② 동안 누가 멈추나**를 보면 헷갈리지 않는다.

### O_NONBLOCK과 EAGAIN

```c
int fl = fcntl(fd, F_GETFL);
fcntl(fd, F_SETFL, fl | O_NONBLOCK);     /* 이 open file description을 논블로킹으로 */

ssize_t n = read(fd, buf, sizeof buf);
if (n > 0)       { /* n바이트 받음 */ }
else if (n == 0) { /* EOF: 상대가 쓰기 쪽을 닫았다 */ }
else if (errno == EAGAIN || errno == EWOULDBLOCK) { /* 지금은 없음. 준비 알림을 기다린다 */ }
else if (errno == EINTR) { /* 시그널에 끊김. 다시 시도 */ }
else             { /* 진짜 에러 */ }
```

- 논블로킹 fd에서 기다려야 할 상황이면 `read()`는 `-1`과 `EAGAIN`을 돌려준다(read(2)).
- 소켓이면 `EAGAIN` 또는 `EWOULDBLOCK`이다. POSIX는 둘 중 아무거나 허용하고 같은 값일 필요도 없다. 그래서 둘 다 검사한다(read(2)). 리눅스 x86-64에서는 둘 다 11이었다(로컬 재현).
- 논블로킹 소켓의 `connect()`가 바로 끝나지 못하면 `-1`과 `EINPROGRESS`를 돌려준다(TCP 등, connect(2)·socket(7)). 바로 끝나면 `0`이다.
  - 완료는 쓰기 가능 알림 뒤 `getsockopt(SO_ERROR)`로 확인한다(connect(2)).
  - UNIX 도메인 소켓은 예외로 `EAGAIN`을 돌려준다(connect(2)).

```text
  논블로킹 소켓 재현 (예시, 리눅스 7.0)
  nonblocking read on empty socket: n=-1 errno=11 (Resource temporarily unavailable)
```

**정규 파일에는 논블로킹이 없다.**
- open(2): `O_NONBLOCK`은 정규 파일과 블록 장치에 효과가 없다. 장치 작업이 필요하면 (잠깐) 블록된다.
- poll(2)·select(2)·epoll은 "블로킹 모드로 해도 안 막힐까"를 알려 준다. 정규 파일은 항상 "준비됨"으로 나온다.
- epoll에는 정규 파일을 아예 못 넣는다(`EPERM`, epoll_ctl(2)).

```text
  정규 파일 + O_NONBLOCK 재현 (예시, 리눅스 7.0)
  poll ret=1 (POLLIN 켜짐), read n=40   <- "준비됨"이라 하고, 실제 디스크 대기는 read 안에서 일어난다
```

- 그래서 Node(libuv)는 파일 I/O를 스레드 풀에서 돌린다(libuv 설계 문서, 27번). libuv 1.45~1.48은 리눅스에서 일부 파일 작업을 io_uring으로도 처리했다. 1.49부터는 파일 작업용 io_uring(SQPOLL 링)이 기본 꺼짐이라 다시 스레드 풀이 기본이다(libuv ChangeLog 1.49.0 "disable SQPOLL io_uring by default", `src/unix/linux.c`, 34번).

### 리눅스의 비동기 I/O 선택지

```text
  POSIX AIO (aio_read)        glibc가 사용자 공간 스레드로 구현. 스레드 유지 비용이 크고 확장이 나쁘다 (aio(7))
  리눅스 native aio (io_submit) O_DIRECT(캐시 우회)에서만 제대로 비동기. 버퍼드 I/O는 동기처럼 동작 (Axboe 2019 기준)
  io_uring (5.1+)             공유 링 두 개(SQ·CQ)로 제출·완료. 버퍼드 파일·소켓 모두 (34번)
```

  - *O_DIRECT*: 페이지 캐시를 거치지 않고 장치와 직접 주고받는 모드다. 정렬·크기 제약이 있다.

### 잠든 스레드는 어디서 기다리나

```text
  스레드 T: read(sock) -> 데이터 없음
     |
     v
  sock의 대기 큐(wait queue)에 T를 매달고 T는 S 상태(잠듦)
     ...
  패킷 도착 -> 커널이 수신 버퍼에 넣고 대기 큐의 T를 깨움 -> T 실행 가능 -> read 반환
```

- 블로킹 read로 잠든 스레드는 `ps`에서 `S`(interruptible sleep)로 보인다. `wchan`이 어디서 기다리는지 알려 준다.

```text
  $ ps -o pid,stat,wchan:32,cmd -p <pid>        (예시, 리눅스 7.0 — 유닉스 소켓 recv 대기)
      PID STAT WCHAN                            CMD
  2050179 S    unix_stream_data_wait            python3 ...
```

- 디스크 I/O를 기다리는 스레드는 `D`(uninterruptible sleep)일 수 있다(proc_pid_stat(5) state 필드: "Waiting in uninterruptible disk sleep"). `D`는 보통의 시그널로 깨울 수 없다. 단 `TASK_KILLABLE` 대기도 `D`로 보이는데, 이것은 치명적 시그널(SIGKILL)로는 깨어난다(`include/linux/sched.h`: `TASK_KILLABLE = TASK_WAKEKILL | TASK_UNINTERRUPTIBLE`).

## 쓰이는 자료구조·알고리즘

- **대기 큐(wait queue)** — 소켓·파이프마다 "이 자원을 기다리는 태스크 목록"이 있다. 데이터가 오면 커널이 이 목록을 깨운다. 블로킹 I/O와 epoll 모두 이 대기 큐에 콜백을 건다(26번). [data-structure/04-queue-deque](../../data-structure/04-queue-deque/2-summary.md)
- **링 버퍼** — io_uring의 제출 큐·완료 큐는 커널과 앱이 공유하는 단일 생산자·단일 소비자 링이다(34번).
- **상태 기계** — 논블로킹 코드는 "어디까지 읽었나"를 스택이 아니라 연결 객체에 저장한다. 다음 준비 알림에서 거기서 이어 간다(27번).
- **폴링 vs 인터럽트** — 논블로킹 재시도는 폴링이다. 준비 알림·완료 알림은 인터럽트 방식이다. 장치 드라이버의 같은 선택이 앱 계층에 다시 나타난 것이다.

## 적용 — 풀어나가는 법

### 1. 먼저 "무엇을 기다리나"를 적는다

| 기다리는 것 | 논블로킹이 통하나 | 대기 도구 |
|---|---|---|
| 소켓·파이프·터미널 | 통한다(`EAGAIN`) | epoll·poll·select(26번) |
| 정규 파일·블록 장치 | 안 통한다 | 스레드 풀, io_uring(34번) |
| DNS 조회(`getaddrinfo`) | 블로킹 함수다 | 스레드 풀(libuv), 비동기 리졸버 |
| DB 드라이버(JDBC) | 블로킹 API다 | 전용 스레드 풀, 가상 스레드(36번) |

### 2. 블로킹 I/O는 타임아웃과 함께 쓴다

Java — 소켓 읽기에 타임아웃을 건다. 0은 무한이다(Java SE `Socket.setSoTimeout`).

```java
Socket s = new Socket();
s.connect(new InetSocketAddress(host, 8080), 3_000);  // 3초(예시)
s.setSoTimeout(5_000);                                  // read가 5초 넘게 막히면
try {
    int n = s.getInputStream().read(buf);               // -1이면 EOF
} catch (SocketTimeoutException e) {
    // 상대가 살아 있는지 모른다. 재시도·끊기 정책으로 넘긴다
}
```

### 3. 논블로킹 I/O는 "EAGAIN이면 멈추고 기다린다"

Java NIO — 논블로킹 채널의 `read`는 읽을 게 없으면 0을 돌려준다. EOF는 -1이다(`ReadableByteChannel` Javadoc).

```java
SocketChannel ch = SocketChannel.open(addr);
ch.configureBlocking(false);
int n = ch.read(buf);
if (n == 0)  { /* 지금은 없음 -> Selector에 OP_READ 등록하고 기다린다 (26번). 바로 재호출 금지 */ }
if (n == -1) { ch.close(); /* 상대가 닫았다 */ }
```

Node — 동기 API와 비동기 API가 이름으로 갈린다.

```js
const fs = require('node:fs');
// 요청 처리 경로에서 금지: 이벤트 루프 스레드가 디스크를 기다린다
const a = fs.readFileSync('/data/big.json');
// 권장: libuv 스레드 풀(또는 io_uring)이 읽고, 끝나면 콜백
fs.readFile('/data/big.json', (err, b) => { /* ... */ });
```

### 4. 진단 명령

```bash
# 스레드가 어디서 잠들어 있나: S/D 상태와 대기 지점
ps -L -o pid,tid,stat,wchan:32,comm -p <pid>
cat /proc/<pid>/task/<tid>/wchan; echo

# EAGAIN 폭주(헛도는 루프) 확인: 초당 수십만 번 같은 read가 EAGAIN이면 busy loop
strace -f -e trace=read,recvfrom -p <pid> 2>&1 | head
strace -c -f -p <pid>          # Ctrl-C 후 syscall별 호출 수·에러 수 요약

# CPU가 사용자(us)인지 커널(sy)인지: EAGAIN 루프는 sy 비중이 크다
pidstat -u -p <pid> 1
top -H -p <pid>                # 스레드별 CPU

# D 상태가 쌓였나 (디스크 대기)
ps -eo stat,pid,comm | awk '$1 ~ /^D/'
vmstat 1                       # b 열 = I/O 완료를 기다리는 수(procs_blocked). I/O가 아닌 D는 안 센다
```

## 장애 시나리오와 대처

### 1. EAGAIN 무시 → busy loop, CPU 100%

- **현상**: 트래픽이 거의 없는데 프로세스 CPU가 한 코어를 꽉 채운다.
- **보이는 형태**
  - `top`에서 해당 스레드 CPU 100% 가까이, `%sy`(커널 시간) 비중이 크다.
  - `strace`에 `read(7, ..., 4096) = -1 EAGAIN (Resource temporarily unavailable)`이 끝없이 찍힌다.
  - 로컬 재현(예시, 리눅스 7.0): 빈 논블로킹 소켓을 1초 동안 재시도하니 `read`가 약 20만~40만 번 불렸다. 같은 1초를 `poll()`로 기다리면 CPU 시간이 0.000초였다. (측정 당시 머신에 다른 부하가 있어 루프가 받은 CPU 시간은 0.3~0.5초였다. 한가한 머신이면 1초에 가깝다.)
- **원인**: 논블로킹 fd에서 `EAGAIN`을 "다시 시도하라"로만 읽고 바로 재호출했다. 준비 알림을 기다리는 단계가 없다.
- **대처**
  - `EAGAIN`이면 epoll·Selector에 관심을 등록하고 **잠든다**(26번).
  - 라이브러리(Netty·libuv)를 쓰면 이 루프를 직접 짜지 않는다.

### 2. EAGAIN을 에러로 처리 → 멀쩡한 연결을 끊는다

- **현상**: 부하가 조금 오르면 클라이언트가 `Connection reset`을 자주 본다.
- **보이는 형태**: 서버 로그에 `Resource temporarily unavailable` 뒤 연결 종료. 송신 쪽이면 큰 응답에서만 난다.
- **원인**: `write()`가 소켓 송신 버퍼가 차서 `EAGAIN`을 냈다. 코드가 `-1`이면 모두 에러로 보고 `close()`했다. 읽지 않은 데이터가 남은 채 닫으면 RST가 나갈 수 있다(network/19).
- **대처**: `EAGAIN`·`EWOULDBLOCK`·`EINTR`을 에러와 구분한다. 쓰기는 남은 바이트를 앱 버퍼에 두고 쓰기 가능 알림(`EPOLLOUT`, NIO `OP_WRITE`, Node `'drain'`)을 기다린다(network/23).

### 3. 블로킹 read에 타임아웃 없음 → 스레드가 영원히 잠든다

- **현상**: 스레드 풀이 서서히 줄어 결국 요청을 못 받는다. CPU는 한가하다.
- **보이는 형태**
  - 스레드 덤프(`jstack`)에서 여러 스레드가 `SocketInputStream.socketRead0`(JDK 버전에 따라 이름이 다르다)에 `RUNNABLE`로 멈춰 있다. Java 스레드 상태는 OS 상태가 아니라 JVM 상태라, 네이티브 블로킹 호출 중인 스레드도 `RUNNABLE`로 보인다(Java SE `Thread.State` Javadoc: RUNNABLE은 "may be waiting for other resources from the operating system").
  - `ps -L`에서 해당 스레드들이 `S` 상태, `wchan`이 소켓 대기 함수다.
- **원인**: 상대가 응답 없이 사라졌다(half-open, network/19·21). 블로킹 read에 타임아웃이 없으면 커널은 계속 기다린다.
- **대처**: 모든 블로킹 소켓에 읽기 타임아웃(`setSoTimeout`, `SO_RCVTIMEO`)을 건다. 연결 수준에서는 keepalive·`TCP_USER_TIMEOUT`을 쓴다(network/21).

### 4. 정규 파일도 논블로킹이라 믿음 → 이벤트 루프가 디스크를 기다린다

- **현상**: 평소엔 빠른데, 로그 디스크가 느려지거나 캐시에 없는 큰 파일을 읽을 때 서버 전체 응답이 함께 멈춘다.
- **보이는 형태**: 이벤트 루프 스레드가 `D` 상태로 보이는 순간이 있다. `vmstat`의 `b` 열이 오른다. 모든 요청의 지연이 같은 순간에 튄다.
- **원인**: `O_NONBLOCK`은 정규 파일에 효과가 없다(open(2)). poll·select도 "준비됨"이라 답한다. 결국 read가 디스크를 기다린다.
- **대처**: 파일 I/O는 스레드 풀(libuv 방식)이나 io_uring으로 뺀다(34번). 이벤트 루프 스레드에서 동기 파일 API를 부르지 않는다(27번).

### 5. read가 0을 돌려줬는데 무시 → 닫힌 연결에서 헛돈다

- **현상**: 클라이언트가 끊은 뒤 서버 CPU가 오른다.
- **보이는 형태**: `strace`에 `read(7, "", 4096) = 0`이 반복된다.
- **원인**: 0은 EOF다(상대가 쓰기 쪽을 닫았다). 레벨 트리거 알림은 EOF 상태를 계속 "읽기 가능"으로 알린다. 코드가 0을 "데이터 없음"으로 오해해 다시 기다린다.
- **대처**: 0이면 연결을 정리한다(`close`, 관심 목록에서 제거).

## 핵심 문장

- read 한 번은 **① 준비 대기 + ② 복사** 두 단계다. I/O 모델은 이 두 단계 동안 호출한 스레드가 무엇을 하는지로 나뉜다.
- 블로킹/논블로킹은 **fd의 속성**("못 끝내면 기다리나")이고, 동기/비동기는 **연산의 성질**("복사까지 끝나야 스레드가 풀리나")이다.
- select·epoll 기반 논블로킹 I/O도 POSIX 정의로는 동기 I/O다. ②를 내 `read()`가 하기 때문이다. 비동기는 io_uring·IOCP처럼 완료를 알려 주는 쪽이다.
- `EAGAIN`은 에러가 아니라 "지금은 없으니 **알림을 기다려라**"다. 바로 재시도하면 CPU를 태운다.
- 정규 파일에는 논블로킹이 없다. 파일은 스레드 풀이나 io_uring으로 비동기화한다.

## 관련 주제·근거

- 선행: [21-files-and-descriptors](../21-files-and-descriptors/2-summary.md) — fd·open file description(`O_NONBLOCK`이 붙는 곳)
- 후속
  - [26-io-multiplexing-epoll](../26-io-multiplexing-epoll/2-summary.md) — 준비 알림으로 여러 fd를 한 스레드가 기다리기
  - [27-event-based-concurrency](../27-event-based-concurrency/2-summary.md) — 이벤트 루프, "블로킹 호출 금지" 규칙
  - [34-zero-copy-and-io-uring](../34-zero-copy-and-io-uring/2-summary.md) — 진짜 비동기(완료 알림) io_uring
  - [36-server-concurrency-architectures](../36-server-concurrency-architectures/2-summary.md) — 연결당 스레드 vs 리액터 vs 프로액터
- 다른 영역
  - [network/23-socket-api](../../network/23-socket-api/2-summary.md) — send/recv의 블로킹·부분 쓰기
  - [network/21-tcp-keepalive-and-user-timeout](../../network/21-tcp-keepalive-and-user-timeout/2-summary.md) — 블로킹 read가 영원히 기다리는 half-open 대처
  - [network/19-tcp-termination-fin-rst-half-open](../../network/19-tcp-termination-fin-rst-half-open/2-summary.md) — EOF(0)와 RST
  - [reliability/39-async-io-gains-and-limits](../../reliability/39-async-io-gains-and-limits/2-summary.md)(비동기가 늘려 주는 것은 처리량)
- 표준·man
  - POSIX.1-2024 XBD 3장 정의 — 3.31 Asynchronous I/O Operation, 3.371 Synchronous I/O Operation, 3.48 Blocking, 3.226 Non-Blocking <https://pubs.opengroup.org/onlinepubs/9799919799/basedefs/V1_chap03.html>
  - read(2) — `EAGAIN`/`EWOULDBLOCK` <https://man7.org/linux/man-pages/man2/read.2.html>
  - open(2) — `O_NONBLOCK`은 정규 파일·블록 장치에 효과 없음, `O_ASYNC`(SIGIO) <https://man7.org/linux/man-pages/man2/open.2.html>
  - socket(7) — 논블로킹 소켓 `EAGAIN`, `connect`의 `EINPROGRESS` <https://man7.org/linux/man-pages/man7/socket.7.html>
  - connect(2) ERRORS — `EINPROGRESS` 조건, UNIX 도메인 소켓은 `EAGAIN` <https://man7.org/linux/man-pages/man2/connect.2.html>
  - epoll_ctl(2) — 정규 파일·디렉터리는 `EPERM` <https://man7.org/linux/man-pages/man2/epoll_ctl.2.html>
  - aio(7) — glibc 사용자 공간 구현의 한계 <https://man7.org/linux/man-pages/man7/aio.7.html>
  - proc_pid_stat(5) — `/proc/<pid>/stat` 상태 `S`·`D`, `wchan` <https://man7.org/linux/man-pages/man5/proc_pid_stat.5.html>
  - 커널 `include/linux/sched.h` — `TASK_KILLABLE` <https://github.com/torvalds/linux/blob/master/include/linux/sched.h>
- 문서
  - Jens Axboe, "Efficient IO with io_uring"(v0.4, 2019-10-15) §1.0 — native aio는 O_DIRECT에서만 비동기(2019년 기준) <https://kernel.dk/io_uring.pdf> (작성 시 원 URL 404, 보관본 <https://web.archive.org/web/2024id_/https://kernel.dk/io_uring.pdf>)
  - Kernel Newbies "Linux 5.1" — io_uring 도입 <https://kernelnewbies.org/Linux_5.1>
  - libuv Design overview — 파일 I/O는 스레드 풀 <https://docs.libuv.org/en/v1.x/design.html>
  - libuv ChangeLog — 1.45.0 "linux: introduce io_uring support", 1.49.0 "linux: disable SQPOLL io_uring by default" <https://github.com/libuv/libuv/blob/v1.x/ChangeLog>
  - Java SE `Socket.setSoTimeout`, `ReadableByteChannel.read`(0·-1) <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/nio/channels/ReadableByteChannel.html>
  - Java SE `Thread.State` — RUNNABLE은 JVM 상태, OS 자원 대기 포함 <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Thread.State.html>
  - Apache Tomcat HTTP Connector — `maxThreads` 기본 200 <https://tomcat.apache.org/tomcat-10.1-doc/config/http.html>
- 교재
  - W. R. Stevens 외, 『UNIX Network Programming Vol.1』 3판 6.2 "I/O Models" [?]
  - CS:APP 3판 12.2 "Concurrent Programming with I/O Multiplexing" (3판 서문 PDF의 목차로 확인 <http://csapp.cs.cmu.edu/3e/pieces/preface3e.pdf>)
  - OSTEP 33장 "Event-based Concurrency" — 33.5 블로킹 시스템 콜, 33.6 비동기 I/O
- 로컬 재현(리눅스 7.0, gcc 13.3): 빈 논블로킹 소켓 `EAGAIN`(=`EWOULDBLOCK`=11), 1초 재시도 루프 vs `poll` CPU 시간, 정규 파일 `O_NONBLOCK`에서 poll 즉시 준비, 블로킹 recv 중 `wchan`
