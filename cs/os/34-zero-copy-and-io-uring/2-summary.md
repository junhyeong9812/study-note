# os/34-zero-copy-and-io-uring — 복사를 줄이고 시스템 콜을 줄이기: sendfile·splice·mmap과 io_uring — 정리 (힌트)

## 해결하는 문제

정적 파일 서버가 하는 일은 단순하다. 파일을 읽어 소켓으로 보낸다.

```c
read(file, tmp_buf, len);
write(socket, tmp_buf, len);
```

Linux Journal의 "Zero Copy I"(2003)은 이 두 줄 뒤에서 데이터가 **최소 네 번 복사**되고, 사용자/커널 전환도 거의 그만큼 일어난다고 적는다.\
데이터는 앱이 한 번도 **보지도 고치지도 않는데** 사용자 공간을 왕복한다.

두 번째 비용은 시스템 콜 자체다.\
I/O 하나에 `read` 하나, 완료 확인에 또 하나. 요청이 초당 수십만 건이면 커널 진입·탈출 비용이 쌓인다.\
Axboe는 스펙터·멜트다운 완화 이후 이 비용이 더 커졌다고 적는다(2019).

쉬운 예: 창고 물건을 트럭에 싣는다.
- 지금 방식: 창고 → **사무실 책상**에 올림 → 다시 들고 나가 트럭에 싣는다. 책상에 올린 이유가 없다.
- zero-copy: 창고에서 트럭으로 바로 옮긴다. 목록(주소·길이)만 적어 넘긴다.
- io_uring: 물건 하나마다 창구에 줄 서지 않고, **공유 게시판**에 주문서를 붙여 두면 창고가 알아서 처리하고 결과 칸에 적어 둔다.

실무 예:
- nginx `sendfile on`, Kafka 컨슈머 전송, Java `FileChannel.transferTo`, Netty `DefaultFileRegion`이 zero-copy 경로다.
- "TLS를 켰더니 Kafka 브로커 CPU가 확 올랐다."
- "로컬에선 io_uring이 되는데 컨테이너에선 `EPERM`이다."

## 동작·원리

### 기준 — read + write의 네 번 복사

```text
  사용자 공간          [tmp_buf] ----------------------+
                         ^ ② CPU 복사                  | ③ CPU 복사
  ========================|============================|=================== 시스템 콜 경계
  커널                [페이지 캐시]                   [소켓 버퍼]
                         ^ ① DMA                       | ④ DMA
  장치                  디스크                          NIC

  모드 전환: read 진입·복귀, write 진입·복귀 = 4번
```

  - *DMA(Direct Memory Access)*: 장치가 CPU를 거치지 않고 메모리에 직접 읽고 쓰는 것이다. CPU 시간은 거의 안 든다.
  - *페이지 캐시*: 커널이 파일 내용을 메모리에 들고 있는 캐시다(14번).
- 아까운 것은 ②·③ **CPU 복사**다. CPU 시간과 메모리 대역폭을 쓰고, CPU 캐시를 쓸데없는 데이터로 채운다.

### mmap + write — 복사 하나를 줄인다

```text
  사용자 공간   [매핑된 영역] == 페이지 캐시와 같은 물리 페이지 (복사 없음)
  커널          [페이지 캐시] --③ CPU 복사--> [소켓 버퍼] --④ DMA--> NIC
                     ^ ① DMA
```

- `mmap`으로 파일을 매핑하면 페이지 캐시를 사용자 공간과 공유한다. ②가 사라진다(Linux Journal 2003).
- 하지만 `write`가 페이지 캐시에서 소켓 버퍼로 복사하는 ③은 남는다. 모드 전환 수도 그대로다.
- 함정: 매핑한 파일을 다른 프로세스가 잘라내면(truncate), 없어진 페이지를 건드리는 순간 문제가 난다.
  - 앱 코드가 매핑을 직접 읽으면 **SIGBUS**를 받는다. 기본 동작은 프로세스 종료다.
  - Linux Journal(2003)은 `write` 호출도 SIGBUS로 끊긴다고 적었다. 리눅스 7.0 로컬 재현에서는 `write`가 SIGBUS 없이 `-1 EFAULT`(Bad address)를 돌려줬다. 커널 안 복사 중의 폴트가 시그널이 아니라 에러로 돌아온 것이다. 에러를 무시하면 응답이 조용히 잘린다.

### sendfile — 커널 안에서 끝낸다

```text
  사용자 공간   (데이터가 올라오지 않는다)
  ======================================================= sendfile(sock, file, &off, len) 1번
  커널   [페이지 캐시] --③ CPU 복사--> [소켓 버퍼] --④ DMA--> NIC      (NIC이 gather 미지원)
         [페이지 캐시] --(주소·길이만)--> [소켓 버퍼] --DMA gather--> NIC   (gather 지원: CPU 복사 0)
               ^ ① DMA
```

- sendfile(2): "복사가 커널 안에서 일어나므로 `read`+`write`보다 효율적"이다. 사용자 공간과 주고받지 않는다.
- NIC가 **gather**(흩어진 메모리 조각을 모아 전송)를 지원하면 소켓 버퍼에 데이터 대신 위치·길이만 붙인다. CPU 복사가 0이 된다. 이것이 좁은 뜻의 "zero-copy"다(Linux Journal 2003, 리눅스 2.4의 소켓 버퍼 변경).
  - *scatter/gather*: 한 번의 DMA가 여러 떨어진 메모리 구역을 읽거나(gather) 쓰는(scatter) 기능이다.
- sendfile(2)의 규칙
  - `in_fd`는 mmap 비슷한 동작을 지원하는 파일이어야 한다. 소켓은 안 된다. (5.12부터 `out_fd`가 파이프면 내부적으로 splice가 된다.)
  - `out_fd`는 2.6.33 전에는 소켓만, 그 뒤로는 아무 파일이나 된다.
  - 한 번에 최대 `0x7ffff000`(2,147,479,552)바이트. 요청보다 **적게 보낼 수 있다**. 남은 만큼 다시 불러야 한다.
  - 소켓·파이프로 zero-copy 전송 중에는, 받는 쪽이 다 소비할 때까지 그 파일 구간을 고치면 안 된다(sendfile(2) NOTES). 페이지를 복사하지 않고 참조하기 때문이다.

```text
  128MB 파일을 루프백 TCP로 보내기 (예시, 리눅스 7.0, 페이지 캐시에 올라간 상태)
               시스템 콜 수         보내는 쪽 sys CPU
  read/write   read 2050 + write 2049   0.065~0.103 s   (64KB 버퍼)
  sendfile     sendfile 1              0.011~0.017 s
  splice       (파이프 경유)            0.016 s
```

### splice — 파이프를 통해 페이지를 옮긴다

```text
  file --splice--> [파이프 버퍼: 페이지 참조] --splice--> socket
```

- splice는 두 fd 중 **하나 이상이 파이프**여야 한다(sendfile(2)가 적는 splice의 조건). 파일→소켓이면 파이프를 가운데 두고 두 번 부른다.
- 파이프 버퍼가 데이터 대신 페이지 참조를 들고 다닌다. 프록시처럼 소켓→소켓 중계에도 쓴다.

### MSG_ZEROCOPY — 사용자 버퍼를 복사 없이 보낸다

- sendfile은 **파일**이 원본일 때다. 앱이 만든 버퍼를 복사 없이 보내려면 `MSG_ZEROCOPY`를 쓴다(TCP·UDP·VSOCK).
- 먼저 `setsockopt(SO_ZEROCOPY)`로 켜야 한다. 버퍼를 다시 써도 되는 시점은 소켓 **에러 큐**의 완료 알림으로 받는다.
- 커널 문서: 대략 **10KB 이상** 쓰기에서만 효과가 있다. 작으면 페이지 고정·알림 비용이 복사보다 크다.

### TLS가 끼면 zero-copy가 사라지는 이유

```text
  평문:      페이지 캐시 -> NIC          (바이트를 그대로 보내면 된다)
  TLS(앱):   페이지 캐시 -> 사용자 공간 [암호화] -> 소켓 버퍼 -> NIC   (다시 read/write 경로)
  kTLS:      페이지 캐시 -> 커널 [암호화] -> 소켓 버퍼 -> NIC        (사용자 공간 왕복 없음, 암호화 1패스)
  kTLS + NIC 오프로드 + TLS_TX_ZEROCOPY_RO:  페이지 캐시 -> NIC가 암호화    (진짜 zero-copy)
```

- TLS는 보내는 바이트를 **암호화한 결과**를 보내야 한다. 누군가는 데이터를 읽어 암호화해야 한다. OpenSSL 같은 사용자 공간 TLS면 데이터가 다시 사용자 공간으로 올라온다. sendfile을 쓸 수 없다.
- **kTLS**(커널 TLS): 핸드셰이크는 사용자 공간에서 하고, 키를 커널 소켓에 넘긴다. 그러면 `sendfile`이 파일 데이터를 최대 2^14바이트 TLS 레코드로 보낸다(커널 문서 networking/tls). 사용자 공간 왕복은 없어지지만, 암호화하는 CPU 패스는 남는다.
- **NIC 오프로드**면 `TLS_TX_ZEROCOPY_RO`로 커널 안 복사도 없앨 수 있다. 문서는 이것을 "진짜 zero-copy"라 부르고, 전송이 끝날 때까지 데이터가 바뀌면 원 전송과 재전송이 다른 내용이 될 수 있다고 경고한다.
- 사용하는 쪽
  - OpenSSL 3.0의 `SSL_sendfile()`은 kTLS가 켜져 있을 때만 쓸 수 있다(SSL_write(3)).
  - nginx 1.21.4부터 OpenSSL 3.0에서 `SSL_sendfile()`을 지원한다(nginx CHANGES).
  - Kafka 브로커의 TLS 비용은 [systems/kafka-why-fast](../../systems/kafka-why-fast/2-summary.md) B절에 있다.

### io_uring — 공유 링 두 개로 제출하고 완료를 받는다

```text
          앱 (사용자 공간)                          커널
  제출 큐 SQ:  앱이 tail을 올린다(생산) ---------> 커널이 head를 올린다(소비)
     [SQE][SQE][SQE][ ][ ][ ]                    SQE를 읽어 I/O 시작
  완료 큐 CQ:  앱이 head를 올린다(소비) <--------- 커널이 tail을 올린다(생산)
     [CQE][CQE][ ][ ][ ][ ]                      끝난 I/O 결과를 씀
  두 링과 SQE 배열은 mmap으로 공유한 메모리다. 앱과 커널 사이에 락이 없다.
```

- 설계 목표는 제출·완료에 **복사도 간접 참조도 없는 것**이었다. 앱과 커널이 락을 공유하려면 시스템 콜이 필요하므로, 락 대신 **단일 생산자·단일 소비자 링**과 메모리 배리어를 골랐다(Axboe 2019 §4.0).
- 제출은 앱이 생산자·커널이 소비자, 완료는 그 반대다. 그래서 링이 두 개다.
- *SQE(제출 큐 항목)*: opcode(`IORING_OP_READ` 등), fd, 오프셋, 버퍼 주소·길이, `user_data`. 64바이트다.
- *CQE(완료 큐 항목)*: `user_data`(제출 때 값 그대로), `res`(시스템 콜 반환값처럼. 실패면 `-EIO` 같은 음수 errno), `flags`.
- 링 인덱스는 자유롭게 증가하는 32비트 정수이고, `index = tail & mask`로 자리를 찾는다. 그래서 링 크기는 2의 거듭제곱이다.
- CQ는 기본적으로 SQ의 **두 배** 크기다(Axboe 2019 §4.2). 로컬 재현에서도 `sq_entries=8 cq_entries=16`이었다.
- 완료 순서는 제출 순서와 **무관하다**. 그래서 `user_data`로 짝을 맞춘다(io_uring(7)).
- 시스템 콜
  - `io_uring_setup(entries, params)`: 인스턴스 생성, 링 fd 반환. 링은 `mmap`으로 붙인다.
  - `io_uring_enter(fd, to_submit, min_complete, flags)`: 제출과 완료 대기를 **한 번에**. 여러 SQE를 한 번에 제출할 수 있다.
  - `IORING_SETUP_SQPOLL`: 커널 스레드가 SQ를 폴링한다. 앱은 SQ에 쓰기만 하면 되고 제출 시스템 콜이 필요 없다. 한가하면 `sq_thread_idle` 뒤 잠들고 `IORING_SQ_NEED_WAKEUP`을 세운다.
    - 권한: 5.11 전에는 특권이 필요했고, 5.11은 `CAP_SYS_NICE`, 5.13부터는 특별한 권한이 필요 없다(io_uring_setup(2)).
- 리눅스 5.1에서 들어왔다(Kernel Newbies). native aio와 달리 버퍼드 I/O·소켓까지 비동기로 다룬다(25번).

```text
  raw io_uring으로 /etc/hostname 읽기 (예시, 리눅스 7.0, liburing 없이 시스템 콜 직접)
  io_uring_setup ok: sq_entries=8 cq_entries=16
  io_uring_enter(3, 1, 1, IORING_ENTER_GETEVENTS, NULL, 0) = 1     <- 제출 1 + 완료 1 대기를 한 번에
  cqe: user_data=42 res=40                                          <- 40바이트 읽음
```

### io_uring과 보안 — 꺼져 있는 환경이 흔하다

- Google(2023-06): kCTF VRP 제출의 **60%가 io_uring**을 악용했고, 완화책을 우회한 제출은 모두 io_uring 취약점을 썼다.
  - 조치: ChromeOS에서 비활성, Android 앱은 seccomp로 접근 차단, **Google 운영 서버에서 비활성**. "신뢰된 구성 요소만" 쓰는 것이 안전하다고 봤다.
- Docker 25.0부터 기본 seccomp 프로필이 `io_uring_*` 시스템 콜을 막는다(moby PR #46762, containerd 기본 프로필과 맞춤). 기본 동작이 `SCMP_ACT_ERRNO`(errno 1)라 호출하면 `EPERM`이다.
- 리눅스 6.6부터 sysctl `kernel.io_uring_disabled`
  - 0: 모두 허용(기본값).
  - 1: `CAP_SYS_ADMIN`이 없거나 `kernel.io_uring_group`에 속하지 않은 프로세스는 `io_uring_setup()`이 `EPERM`.
  - 2: 모두 금지, 항상 `EPERM`.

```text
  seccomp로 io_uring_setup만 EPERM으로 막고 실행 (예시, 리눅스 7.0, Docker 기본 프로필 흉내)
  raw 프로그램:  io_uring_setup failed: errno=1 (Operation not permitted)
  Node 18 (libuv 1.48): io_uring_setup(...) = -1 EPERM  ... 그래도 "readFile ok, bytes 40"
                        -> 조용히 스레드 풀 경로로 돌아간다
```

## 쓰이는 자료구조·알고리즘

- **단일 생산자·단일 소비자 링 버퍼(io_uring SQ·CQ)** — head·tail 두 인덱스, 크기 2^k, `& mask`로 순환. 생산자만 tail을, 소비자만 head를 쓰니 락이 필요 없다. 대신 "데이터를 쓴 뒤 tail을 공개"하는 순서를 release/acquire 배리어로 지킨다. [data-structure/04-queue-deque](../../data-structure/04-queue-deque/2-summary.md)
- **간접 인덱스 배열(SQ array)** — SQ 링은 SQE를 직접 담지 않고 SQE 배열의 **인덱스**를 담는다. 앱이 SQE를 자기 자료구조 안에 두고도 여러 개를 한 번에 제출할 수 있게 한 설계다(Axboe 2019 §4.2).
- **scatter/gather 리스트** — 소켓 버퍼가 데이터 대신 (페이지, 오프셋, 길이) 목록을 든다. NIC가 이 목록대로 DMA한다.
- **참조 카운트 페이지** — splice·sendfile은 페이지를 복사하지 않고 참조를 늘려 넘긴다. 그래서 "전송이 끝날 때까지 원본을 바꾸지 말라"는 규칙이 생긴다.
- **완료 토큰(`user_data`)** — 비동기 요청과 완료를 잇는 값. POSA2의 Asynchronous Completion Token 패턴과 같은 발상이다(36번).

## 적용 — 풀어나가는 법

### 1. 파일을 소켓으로 보낼 때

C — 부분 전송을 반드시 처리한다.

```c
off_t off = 0;
while (off < size) {
    ssize_t n = sendfile(sock, fd, &off, size - off);   /* off는 커널이 전진시킨다 */
    if (n < 0) {
        if (errno == EAGAIN) { /* 논블로킹: EPOLLOUT 기다렸다 이어서 */ break; }
        if (errno == EINVAL || errno == ENOSYS) { /* read/write로 대체 (sendfile(2) 권고) */ }
        break;
    }
    if (n == 0) break;                                   /* 파일이 줄었다 */
}
```

Java — `transferTo`는 반환값이 요청보다 작을 수 있다.

```java
try (FileChannel fc = FileChannel.open(path, StandardOpenOption.READ)) {
    long pos = 0, size = fc.size();
    while (pos < size) {
        pos += fc.transferTo(pos, size - pos, socketChannel);   // 리눅스 JDK 21: copy_file_range 먼저, 소켓 대상이면 실패해 sendfile (JDK 17: sendfile만)
    }
}
```

- JDK 버전에 따라 다르다(OpenJDK 소스).
  - JDK 17은 `sendfile`만 부른다(jdk17u `src/java.base/unix/native/libnio/ch/FileChannelImpl.c`의 `transferTo0` → `sendfile64`).
  - JDK 21은 `copy_file_range`를 먼저 시도하고, `EINVAL`·`ENOSYS`·`EXDEV`·`EOPNOTSUPP`면 `sendfile`로 넘어간다(jdk21u `src/java.base/linux/native/libnio/ch/FileDispatcherImpl.c`). 이 경로는 jdk19u에는 없고 jdk20u에는 있다.
  - 그래서 JDK 17에서 strace를 보면 `copy_file_range` 실패 없이 바로 `sendfile`이 보인다.
- Netty는 `DefaultFileRegion`으로 같은 경로를 쓴다. nginx는 `sendfile on;`.
- TLS가 필요하면: kTLS 가능한 커널·OpenSSL 3.0·서버 설정을 확인한다. 안 되면 zero-copy는 없다고 보고 CPU를 산정한다.

### 2. io_uring을 쓰기 전에 확인할 것

```bash
cat /proc/sys/kernel/io_uring_disabled          # 6.6+: 0이면 허용
cat /proc/sys/kernel/io_uring_group             # 1일 때 허용 그룹 (-1 = CAP_SYS_ADMIN만)
grep Seccomp /proc/self/status                  # 2 = seccomp 필터 적용 중 (컨테이너 기본 프로필 등)
strace -f -e trace=io_uring_setup,io_uring_enter <cmd>   # 실제로 쓰나, EPERM인가
```

- 앱 코드에서는 `io_uring_setup` 실패를 **대체 경로(스레드 풀·epoll)** 로 받아야 한다. libuv처럼 조용히 돌아가면 성능 기대만 어긋나고, 대체 경로가 없으면 기동 실패다.
- 직접 링을 다루지 말고 liburing을 쓴다. 배리어·SQ 간접 배열 같은 세부를 대신 처리한다.
- CQ가 넘치지 않게 "진행 중 요청 수 ≤ CQ 크기"를 지킨다(Axboe 2019 §4.2).

### 3. 진단 명령

```bash
# 복사 경로 확인: read/write 수천 번인가, sendfile 몇 번인가
strace -c -f -p <pid>

# 보내는 쪽 CPU가 us(암호화·앱 복사)인가 sy(커널 복사)인가
pidstat -u -p <pid> 1

# kTLS가 실제로 쓰이나: TlsCurrTxSw(호스트 암호화)·TlsCurrTxDevice(NIC 오프로드) 세션 수
# (tls 모듈이 로드돼 있어야 파일이 있다. 작성 환경은 미로드라 없었다)
cat /proc/net/tls_stat

# mmap 매핑을 직접 읽다 SIGBUS로 죽었나: exit code 135 (128+7). write가 EFAULT인지도 strace로 본다
dmesg | tail
```

## 장애 시나리오와 대처

### 1. TLS를 켰더니 CPU가 급증 → zero-copy 경로가 사라졌다

- **현상**: 같은 트래픽인데 TLS 전환 후 브로커·파일 서버 CPU가 크게 오르고 처리량이 떨어진다.
- **보이는 형태**
  - `strace -c`에서 `sendfile`이 사라지고 `read`/`write`(또는 `sendmsg`)가 대량으로 보인다.
  - CPU가 사용자 시간(`%us`, 암호화)과 커널 복사로 나뉘어 오른다.
- **원인**: TLS는 암호화된 바이트를 보내야 한다. 사용자 공간 TLS면 데이터가 다시 사용자 공간을 왕복한다. sendfile·splice 경로를 쓸 수 없다.
- **대처**
  - kTLS(커널 TLS) + `SSL_sendfile`(OpenSSL 3.0) + 지원 서버(nginx 1.21.4+)로 사용자 공간 왕복을 없앤다. 암호화 CPU는 남는다.
  - NIC TLS 오프로드가 있으면 `TLS_TX_ZEROCOPY_RO`까지 고려한다(원본 불변 조건 확인).
  - 아니면 TLS 비용을 용량 계획에 넣는다(systems/kafka-why-fast B절).

### 2. 컨테이너·보안 정책에서 io_uring 비활성 → EPERM 또는 조용한 성능 저하

- **현상**: 개발 머신에선 되는 io_uring 기반 서버가 Docker·Kubernetes에서 기동에 실패한다. 또는 기동은 되는데 벤치마크만큼 빠르지 않다.
- **보이는 형태**
  - `strace`: `io_uring_setup(...) = -1 EPERM (Operation not permitted)`.
  - 앱 로그: "io_uring not available, falling back" 류, 또는 아무 로그 없음.
  - 로컬 재현: seccomp로 막자 raw 프로그램은 `errno=1`로 실패했고, Node(libuv 1.48)는 로그 없이 스레드 풀로 파일을 읽었다.
- **원인**
  - Docker 25.0+ 기본 seccomp 프로필이 `io_uring_*`를 막는다(errno 1 = `EPERM`).
  - 호스트가 `kernel.io_uring_disabled=1/2`(6.6+)다.
  - 조직 보안 정책으로 꺼 둔 환경(Google 운영 서버 사례).
- **대처**
  - io_uring을 **필수**로 두지 않는다. 대체 경로를 두고, 어느 경로로 도는지 기동 로그·지표로 드러낸다.
  - 꼭 필요하면 보안팀과 위험을 합의하고 그 워크로드에만 seccomp 프로필을 예외로 준다.

### 3. sendfile·transferTo의 부분 전송 무시 → 잘린 응답

- **현상**: 큰 파일 다운로드가 가끔 중간에 끊긴다. 파일 크기가 2GB를 넘으면 항상 잘린다.
- **보이는 형태**: 클라이언트 `Content-Length` 불일치 에러(예: curl `(18) transfer closed with N bytes remaining`), 서버는 성공 로그.
- **원인**: `sendfile`은 요청보다 적게 보낼 수 있고, 한 번에 최대 `0x7ffff000`바이트다(sendfile(2)). 논블로킹 소켓이면 버퍼가 찰 때 일부만 보낸다. `transferTo`도 반환값이 작을 수 있다. 코드가 한 번 호출로 끝났다고 가정했다.
- **대처**: 오프셋을 전진시키며 남은 바이트가 0이 될 때까지 반복한다. 논블로킹이면 `EAGAIN`에서 `EPOLLOUT`을 기다린다.

### 4. mmap 전송 중 파일 잘림 → SIGBUS 종료 또는 EFAULT

- **현상**: 로그 로테이션·파일 교체 직후 서버 프로세스가 갑자기 죽거나, 다운로드가 중간에 잘린다.
- **보이는 형태**
  - 앱이 매핑을 직접 읽었다면: 종료 코드 135(128 + SIGBUS 7), `Bus error (core dumped)`.
  - 매핑을 `write`에 넘겼다면: `strace`에 `write(...) = -1 EFAULT (Bad address)`. 에러를 무시하면 응답만 잘린다.
  - 로컬 재현(예시, 리눅스 7.0): 1MB 매핑 후 `ftruncate(fd, 0)` → 파일·소켓으로의 `write`는 둘 다 `EFAULT`, 매핑 직접 읽기는 `Bus error`(exit 135).
- **원인**: 매핑한 파일을 다른 프로세스가 잘라내면 없어진 영역에 뒷받침할 페이지가 없다. 사용자 코드 접근은 SIGBUS, 커널 안 복사(`write`)는 `EFAULT`가 된다. Linux Journal(2003)은 `write`도 SIGBUS라 적었으나 현재 커널 재현과 다르다.
- **대처**: 전송용으로는 mmap 대신 sendfile을 쓴다. 파일 교체는 잘라 쓰기(truncate) 대신 새 파일 + `rename`으로 한다(24번). 파일 리스(`F_SETLEASE`)로 변경 알림을 받는 방법도 있다(같은 글).

### 5. zero-copy 전송 중 원본 수정 → 받는 쪽이 바뀐 데이터를 받는다

- **현상**: 전송 직후 덮어쓴 파일·버퍼인데, 클라이언트가 **새 내용**이나 섞인 내용을 받는다. 재전송된 패킷만 내용이 다르기도 하다.
- **원인**: zero-copy는 페이지를 복사하지 않고 참조한다. sendfile(2)은 받는 쪽이 다 소비할 때까지 그 파일 구간을 고치지 말라고 적는다. kTLS `TLS_TX_ZEROCOPY_RO`도 원 전송과 재전송이 다른 데이터가 될 수 있다고 경고한다. `MSG_ZEROCOPY`는 완료 알림 전에는 버퍼를 다시 쓰면 안 된다.
- **대처**: 전송 중인 파일은 제자리에서 고치지 않는다(새 파일 + rename). `MSG_ZEROCOPY`는 에러 큐 완료 알림을 받은 뒤에 버퍼를 재사용한다.

## 핵심 문장

- `read`+`write`로 파일을 보내면 CPU 복사 2번을 포함해 최소 4번 복사된다. 앱이 보지도 않는 데이터가 사용자 공간을 왕복한다.
- sendfile은 커널 안에서 페이지 캐시를 소켓으로 보낸다. NIC가 gather를 지원하면 CPU 복사가 0이다. 부분 전송은 앱이 반복해 처리한다.
- TLS는 데이터를 암호화해야 하므로 사용자 공간 TLS에선 zero-copy가 사라진다. kTLS는 사용자 공간 왕복을, NIC 오프로드는 커널 복사까지 없앤다.
- io_uring은 앱과 커널이 공유하는 제출 링·완료 링(단일 생산자·단일 소비자)이다. 제출·완료를 배치로, SQPOLL이면 시스템 콜 없이 한다.
- io_uring은 보안 이유로 꺼진 환경이 많다(Docker 25+ 기본 seccomp, Google 운영 서버, `io_uring_disabled`). 항상 대체 경로를 둔다.

## 관련 주제·근거

- 선행
  - [26-io-multiplexing-epoll](../26-io-multiplexing-epoll/2-summary.md) — 준비 알림 모델(io_uring은 완료 알림 모델)
  - [14-mmap-and-page-cache](../14-mmap-and-page-cache/2-summary.md) — 페이지 캐시·mmap
- 함께: [25-io-models](../25-io-models/2-summary.md) — 동기/비동기, native aio의 한계
- 후속
  - [36-server-concurrency-architectures](../36-server-concurrency-architectures/2-summary.md) — 프로액터(IOCP·io_uring)
  - [24-fsync-and-durability](../24-fsync-and-durability/2-summary.md) — rename으로 파일 교체
- 다른 영역
  - [systems/kafka-why-fast](../../systems/kafka-why-fast/2-summary.md) — sendfile로 JVM을 데이터 경로에서 빼기, TLS와 zero-copy의 맞바꿈
  - [network/29-tls-handshake](../../network/29-tls-handshake/2-summary.md) — 핸드셰이크(사용자 공간)와 레코드 암호화(kTLS가 넘겨받는 부분)
  - [network/25-kernel-network-stack](../../network/25-kernel-network-stack/2-summary.md) — 소켓 버퍼·NIC 오프로드
- man·커널 문서
  - sendfile(2) — 커널 안 복사, `in_fd`·`out_fd` 조건(2.6.33, 5.12), 0x7ffff000 한도, 부분 전송, 전송 중 수정 금지 <https://man7.org/linux/man-pages/man2/sendfile.2.html>
  - splice(2) — 파이프 필요 <https://man7.org/linux/man-pages/man2/splice.2.html>
  - io_uring(7), io_uring_setup(2) — SQ·CQ, `user_data`, 완료 순서 무관, SQPOLL 권한 변화(5.11·5.13) <https://man7.org/linux/man-pages/man2/io_uring_setup.2.html>
  - Kernel docs "Kernel TLS" — sendfile로 TLS 레코드(2^14), `TLS_TX_ZEROCOPY_RO`와 원본 불변 경고, `/proc/net/tls_stat` 통계 <https://docs.kernel.org/networking/tls.html>
  - Kernel docs "MSG_ZEROCOPY" — `SO_ZEROCOPY`, 에러 큐 알림, 약 10KB 이상에서 효과 <https://docs.kernel.org/networking/msg_zerocopy.html>
  - Kernel docs sysctl/kernel — `io_uring_disabled`(0/1/2), `io_uring_group`(-1) <https://docs.kernel.org/admin-guide/sysctl/kernel.html>
  - Kernel Newbies "Linux 5.1"(io_uring 도입), "Linux 6.6"(io_uring 전역 비활성 sysctl) <https://kernelnewbies.org/Linux_6.6>
- 글·보안 보고
  - Jens Axboe, "Efficient IO with io_uring"(v0.4, 2019-10-15) — §1.0 aio 한계, §4.0 링 설계, §4.2 CQ = SQ의 2배, §8.3 SQPOLL <https://kernel.dk/io_uring.pdf> (작성 시 원 URL 404, 보관본 <https://web.archive.org/web/2024id_/https://kernel.dk/io_uring.pdf>)
  - Dragan Stancevic, "Zero Copy I: User-Mode Perspective", Linux Journal 2003 — 4번 복사, mmap의 SIGBUS(2003년 기준 `write`도 SIGBUS라 서술), 파일 리스, gather NIC <https://www.linuxjournal.com/article/6345>
  - Google Security Blog, "Learnings from kCTF VRP's 42 Linux kernel exploits submissions"(2023-06-14) <https://security.googleblog.com/2023/06/learnings-from-kctf-vrps-42-linux.html>
  - moby PR #46762 "seccomp: block io_uring_* syscalls in default profile"(Docker 25.0.0) <https://github.com/moby/moby/pull/46762>
  - OpenSSL 3.0 `SSL_sendfile`(SSL_write(3)) — kTLS 필요 <https://github.com/openssl/openssl/blob/openssl-3.0/doc/man3/SSL_write.pod>
  - nginx CHANGES 1.21.4 — "support for SSL_sendfile() when using OpenSSL 3.0" <https://nginx.org/en/CHANGES>
  - libuv ChangeLog — 1.45.0 io_uring 도입, 1.49.0 "disable SQPOLL io_uring by default" <https://github.com/libuv/libuv/blob/v1.x/ChangeLog>; `src/unix/linux.c` — 파일 작업용 SQPOLL 링은 루프 플래그·`UV_USE_IO_URING`이 있어야 생성 <https://github.com/libuv/libuv/blob/v1.x/src/unix/linux.c>
  - OpenJDK jdk21u `src/java.base/linux/native/libnio/ch/FileDispatcherImpl.c` — `transferTo0`: copy_file_range → sendfile <https://github.com/openjdk/jdk21u/blob/master/src/java.base/linux/native/libnio/ch/FileDispatcherImpl.c> · jdk17u `src/java.base/unix/native/libnio/ch/FileChannelImpl.c` — `transferTo0`: sendfile64만 <https://github.com/openjdk/jdk17u/blob/master/src/java.base/unix/native/libnio/ch/FileChannelImpl.c>
- 로컬 재현(리눅스 7.0, gcc 13.3, Node 18.19.1/libuv 1.48): 잘린 mmap 영역을 `write`에 넘기면 `EFAULT`, 직접 읽으면 SIGBUS(exit 135), 128MB 루프백 전송 read/write vs sendfile vs splice(시스템 콜 수·sys CPU), raw io_uring READ 1건(sq 8/cq 16), seccomp로 `io_uring_setup` EPERM 시 raw 실패·libuv 무음 대체
