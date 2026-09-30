# os/06-signals — 프로세스에 끼어드는 비동기 알림, 시그널 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> ⚠️ 이 서머리는 Claude 초안(2026-09-30) — 근거는 아래 「관련 주제·근거」. 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 해결하는 문제

프로세스는 자기 코드만 순서대로 실행한다.\
그런데 바깥에서 "지금 당장" 알려야 할 일이 생긴다.

```text
  알릴 일                               누가 알리나
  "그만 끝내라" (Ctrl+C, 배포 종료)        터미널 드라이버, kubelet, 사람(kill)
  "자식 프로세스가 끝났다"                  커널 (SIGCHLD)
  "없는 주소를 읽었다"                     CPU 예외 → 커널 (SIGSEGV)
  "읽는 쪽이 없는 파이프에 썼다"             커널 (SIGPIPE)
```

이 알림을 프로세스의 실행 흐름 한가운데에 끼워 넣는 장치가 **시그널**이다.

  - *시그널(signal)*: 커널이 프로세스(또는 스레드)에 보내는 작은 번호 하나로 종류를 가리키는 알림이다. 원인·보낸 PID 같은 부가 정보(`siginfo_t`)가 딸릴 수 있지만 데이터를 싣는 통로는 아니다(sigaction(2) "The siginfo_t argument").

쉬운 예: 수업 중 교실 방송이다.
- 방송이 나오면 선생님은 하던 말을 멈추고 방송을 듣는다(핸들러).
- 방송이 끝나면 멈췄던 문장부터 다시 이어 간다.
- 같은 방송이 여러 번 울려도, 듣기 전에 쌓인 것은 "방송 있음" 한 번으로 합쳐진다.

똑같은 구조다.\
시그널이 오면 커널은 프로세스를 잠깐 핸들러로 돌렸다가, 끝나면 원래 자리로 되돌린다.

실무 예:
- 쿠버네티스가 파드를 내릴 때 컨테이너에 SIGTERM을 보낸다. 앱이 무시하면 유예 시간 뒤 SIGKILL로 죽고 `exit 137`이 남는다.
- 셸 파이프라인 `producer | head -1`에서 `producer`가 로그도 없이 사라진다. SIGPIPE다.
- 시그널 핸들러에서 로그를 남기려고 `malloc`·`printf`를 불렀더니, 드물게 프로세스가 영원히 멈춘다.

프로세스 5상태·PCB 기초는 [04-process-and-lifecycle](../04-process-and-lifecycle/2-summary.md)(원고 [foundations/process-thread §2·§5](../../foundations/process-thread/README.md))에 있다.

## 동작·원리

### 시그널의 일생 — 생성 → 대기 → 전달

```text
  (1) 생성                     (2) 대기(pending)                 (3) 전달(delivery)
  kill(2), Ctrl+C,             커널이 대상의 pending 비트를 켠다     커널 → 유저 모드로 돌아가는 순간
  CPU 예외, 파이프 끊김  ---->   ... 막혀(blocked) 있으면 여기서 대기 ---> pending이고 막히지 않은 것을 골라
                                                                 기본 동작 / 무시 / 핸들러 실행
```

- (1) **생성**: 누군가 시그널을 만든다. `kill(2)`로 보내거나, 커널이 사건(자식 종료·잘못된 메모리 접근)을 보고 만든다.
- (2) **대기**: 생성과 전달 사이의 시그널은 "pending" 상태다. 막혀 있으면 풀릴 때까지 여기서 기다린다(signal(7)).
- (3) **전달**: 커널은 커널 모드에서 유저 모드로 돌아가는 순간마다 pending이면서 막히지 않은 시그널을 확인한다. 시스템 콜 복귀나 스케줄링 직후가 그 순간이다(signal(7) "Execution of signal handlers").

  - *블록(block)*: "지금은 받지 않겠다"는 표시다. 버리는 것이 아니라 미루는 것이다. 스레드마다 따로 가진 **시그널 마스크**로 정한다.
  - *무시(ignore)*: 받자마자 버린다. 블록과 다르다. 막혀 있지 않으면 리눅스는 생성 시점에 바로 버린다(`kernel/signal.c` `sig_ignored()`).
- 예외: SIGCONT의 "정지 해제"는 전달을 기다리지 않고 **생성 시점에** 일어난다. 막거나 무시해도 그렇다(`kernel/signal.c` `prepare_signal()`). 위 (3)은 핸들러·기본 동작이 실행되는 시점이다.

### 대기 비트마스크 — 표준 시그널은 쌓이지 않는다

```text
  커널의 sigset_t (x86-64에서 64비트 비트마스크, 비트 n-1 = 시그널 n)

  비트:   ... 14 13 12 11 10  9  8 ...  1  0
  시그널: ... 15 14 13 12 11 10  9 ...  2  1
                             ^
                     SIGUSR1(10) 세 번 보냄 -> 비트 하나만 켜짐 -> 핸들러 1번 실행
```

- 커널의 대기 목록은 `struct sigpending { struct list_head list; sigset_t signal; }`이다(include/linux/signal_types.h).
  - `signal` 비트마스크: 어떤 번호가 대기 중인지 표시한다.
  - `list`: 시그널마다 딸린 정보(`siginfo`)를 담는다.
- **표준 시그널(1~31)은 큐에 쌓이지 않는다.** 막혀 있는 동안 여러 번 와도 한 번만 pending으로 표시된다(signal(7)).
  - 자료구조가 못 세서가 아니다. 커널은 같은 표준 시그널이 이미 pending이면 새로 넣지 않는다(`kernel/signal.c` `legacy_queue()`). 첫 인스턴스의 `siginfo`는 리스트에 들어간다.
- **실시간 시그널(SIGRTMIN~SIGRTMAX)은 여러 개가 큐에 쌓인다.** `sigqueue(3)`로 값도 함께 보낼 수 있다(signal(7)).
  - 큐 한도(`RLIMIT_SIGPENDING`)에 걸리면 `sigqueue`는 `EAGAIN`으로 실패하고, `kill`은 성공하되 인스턴스 정보를 잃을 수 있다(`__send_signal_locked()`).
- 그래서 "SIGCHLD 한 번 = 자식 하나 종료"가 아니다. 핸들러에서 `waitpid(-1, …, WNOHANG)`를 반복해 전부 회수해야 한다.

로컬에서 확인한 모습이다(예시, 리눅스 7.0). SIGUSR1을 막아 둔 채 자기 자신에게 세 번 보냈다.

```text
  ShdPnd: 0000000000000200     <- 비트 9 = SIGUSR1(10), 프로세스 전체 대기
  SigBlk: 0000000000000200     <- 막아 둠
  SigCgt: 0000000000000200     <- 핸들러 설치됨
  (막기를 푼 뒤) handler ran 1 time(s)
```

- `/proc/<pid>/status`의 `SigPnd`는 스레드 대기, `ShdPnd`는 프로세스 전체 대기다. `SigBlk`·`SigIgn`·`SigCgt`는 막음·무시·잡음 마스크다(proc_pid_status(5)).

### 누구에게 가나 — 프로세스 방향 vs 스레드 방향

```text
  kill(pid, SIGTERM) --------> 프로세스 방향 -> 그 시그널을 막지 않은 스레드 중 아무나 하나
  잘못된 메모리 접근(SIGSEGV) --> 스레드 방향 -> 그 명령을 실행한 바로 그 스레드
  pthread_kill / tgkill -----> 스레드 방향 -> 지정한 스레드
```

- 처리 방식(disposition)은 **프로세스 단위**다. 모든 스레드가 같은 핸들러를 공유한다.
- 마스크는 **스레드 단위**다. 스레드마다 막는 시그널이 다를 수 있다(signal(7)).
- 프로세스 방향 시그널은 막지 않은 스레드 중 커널이 **임의로** 고른 하나에 전달된다.

### 전달될 때 일어나는 일 — 세 가지 처리 방식

```text
  전달 시점
     |
     +-- 기본 동작(SIG_DFL) ---> Term(종료) / Core(종료+코어) / Ign / Stop / Cont
     +-- 무시(SIG_IGN) -------> 버림
     +-- 핸들러 --------------> (a) 대기 비트 끔
                                (b) 현재 레지스터·PC·마스크를 유저 스택의 "시그널 프레임"에 저장
                                (c) PC를 핸들러 첫 명령으로 바꿔 유저 모드로 복귀
                                (d) 핸들러 return -> 트램펄린 -> sigreturn(2)
                                (e) 저장한 상태 복원 -> 끊겼던 명령부터 계속
```

- 핸들러가 도는 동안 **그 시그널 자신은 자동으로 막힌다**(`SA_NODEFER`를 주지 않으면). `sa_mask`에 넣은 시그널도 함께 막힌다(signal(7)).
- 커널은 "지금 핸들러 안이다"라는 상태를 따로 기록하지 않는다. 필요한 정보는 전부 유저 스택의 프레임에 있다(signal(7)).
- **SIGKILL(9)과 SIGSTOP(19)은 잡거나 막거나 무시할 수 없다**(signal(7)). 그래서 SIGKILL은 정리 코드를 돌릴 기회가 없다.

주요 시그널(번호는 x86·ARM 기준, signal(7)):

| 시그널 | 번호 | 기본 동작 | 흔한 원인 |
|---|---|---|---|
| SIGINT | 2 | Term | 터미널 Ctrl+C |
| SIGKILL | 9 | Term | `kill -9`, OOM killer, 유예 끝난 컨테이너 |
| SIGSEGV | 11 | Core | 잘못된 메모리 접근 |
| SIGPIPE | 13 | Term | 읽는 쪽 없는 파이프·소켓에 write |
| SIGTERM | 15 | Term | `kill` 기본값, 컨테이너 종료 요청 |
| SIGCHLD | 17 | Ign | 자식 종료·정지 |

### 종료 코드 128+N

```text
  시그널 N으로 죽은 자식  --->  bash·컨테이너 런타임이 보고하는 종료 코드 = 128 + N
  SIGKILL(9) -> 137    SIGSEGV(11) -> 139    SIGPIPE(13) -> 141    SIGTERM(15) -> 143
```

- bash는 치명적 시그널 N으로 끝난 명령의 상태를 128+N으로 적는다(bash(1) "EXIT STATUS"). POSIX는 "128보다 큰 값"만 요구하므로 셸마다 다를 수 있다(POSIX.1-2024 XCU §2.8.2).
- 숫자만으로 시그널 사망을 확정하지 못한다. 프로그램이 `exit(137)`을 불러도 137이다. 확정은 `wait` 상태의 `WIFSIGNALED`·`WTERMSIG`로 한다.
- 커널이 돌려주는 `wait` 상태에는 "시그널로 죽었음 + 번호"가 따로 들어 있다(`WIFSIGNALED`·`WTERMSIG`). 128+N은 셸 쪽 관례다.
- JDK는 기본 설정(`-Xrs` 없음)에서 SIGTERM·SIGINT·SIGHUP을 받으면 셧다운 훅을 돌리고 `128 + 시그널 번호`로 끝낸다. SIGTERM이면 143이다(OpenJDK `java/lang/Terminator.java`: `Shutdown.exit(sig.getNumber() + 0200)`).

### 시스템 콜 도중에 온 시그널 — `EINTR`

```text
  read(sock) 로 블록 중 ----> 시그널 도착, 핸들러 실행 ----> 핸들러 return 후
                                                       SA_RESTART 있음: read 자동 재시작
                                                       SA_RESTART 없음: read가 -1, errno=EINTR
```

- 파이프·소켓·터미널처럼 오래 막힐 수 있는 "느린" 장치의 호출이 대상이다. 로컬 디스크 I/O는 시그널로 끊기지 않는다(signal(7)).
- 이미 일부를 옮긴 뒤 끊기면 에러가 아니라 옮긴 바이트 수를 돌려준다(signal(7)).
- `SA_RESTART`를 줘도 항상 재시작되는 것은 아니다. 소켓에 타임아웃(`SO_RCVTIMEO`)을 건 경우 등은 `EINTR`로 끝난다(signal(7) 목록). 그래서 재시도해도 되는 블로킹 호출(`read`·`accept` 등)은 `EINTR`을 재시도하는 루프로 감싼다. 단 리눅스 `close()`는 `EINTR`이어도 fd가 이미 닫혔으니 재시도하지 않는다(close(2) NOTES).

### fork·exec 때 무엇이 남나

| 항목 | `fork` 후 자식 | `execve` 후 |
|---|---|---|
| 처리 방식 | 부모 것 복사 | **핸들러는 기본 동작으로 되돌림**, 무시(SIG_IGN)는 유지 |
| 마스크 | 복사 | 유지 |
| 대기 시그널 | **비움** | 유지 |

(signal(7))

- 함수 포인터는 새 프로그램에서 의미가 없으니 핸들러만 되돌린다.
- 무시는 유지된다. 그래서 SIGPIPE를 무시하던 부모가 실행한 프로그램도 SIGPIPE를 무시한 채 시작한다. Node.js는 시작할 때 이런 상속을 되돌리는 코드를 둔다(아래 SIGPIPE 절).

### 핸들러 안에서는 왜 조심해야 하나 — async-signal-safe

```text
  메인 흐름: malloc() 진입 -> 힙 락 잡음 -> [여기서 시그널!]
                                              |
  핸들러:                                       malloc() -> 같은 힙 락을 기다림
                                              -> 락 주인은 핸들러가 끝나기를 기다리는 메인 흐름 자신
                                              -> 영원히 대기 (데드락)
```

- 시그널은 메인 흐름의 **아무 명령 사이**에나 끼어든다. 그 순간 메인 흐름이 라이브러리 내부 자료구조를 반쯤 고친 상태일 수 있다.
- 핸들러가 같은 함수를 다시 부르면 망가진 자료를 쓰거나(printf 버퍼), 이미 잡힌 락을 기다린다(malloc).
- POSIX는 핸들러에서 불러도 되는 함수 목록을 정한다. 이것이 **async-signal-safe** 함수다(signal-safety(7)).
  - 들어 있는 것: `write`, `_exit`, `read`, `kill`, `sigaction`, `waitpid` 등.
  - 들어 있지 않은 것: `malloc`, `free`, `printf` 등 stdio 전부(signal-safety(7) "all of whose functions are not async-signal-safe").
- `errno`도 조심한다. 핸들러가 `errno`를 바꾸면 메인 흐름의 에러 판정이 틀어진다. 들어올 때 저장하고 나갈 때 되돌린다(signal-safety(7)).

  - *재진입(reentrant)*: 실행 도중 끼어들어 같은 함수를 또 불러도 안전한 성질이다.
  - *async-signal-safe*: 재진입 가능하거나, 시그널에 대해 원자적이어서 핸들러에서 불러도 되는 함수다.

로컬 재현(예시, 리눅스 7.0 · glibc 2.39): 50µs마다 SIGALRM을 받고 핸들러에서 `malloc`을 부르게 했다. 스레드가 둘 이상인 적이 있는 프로세스에서 즉시 멈췄다.

```text
  #0 futex_wait (futex_word=<main_arena>)          <- 힙 락을 기다림
  #2 __libc_malloc (bytes=5000)                    <- 핸들러 안의 malloc
  #3 h ()                                          <- 시그널 핸들러
  #4 <signal handler called>
  #5 _int_malloc (av=<main_arena>)                 <- 메인 흐름: 락을 잡은 채 끊김
  #7 main ()
```

- 같은 코드를 **단일 스레드 프로세스**로 돌리면 8초 동안 멈추지 않았다. glibc 2.39의 `malloc`은 단일 스레드일 때 힙 락 없이 `_int_malloc`을 바로 부른다(glibc `malloc/malloc.c` `__libc_malloc`의 `if (SINGLE_THREAD_P)` 분기).
  - 락이 없으니 데드락 대신 **반쯤 고친 힙 자료구조를 핸들러가 또 고치는** 위험이 남는다. 안전해진 것이 아니다.
- 교훈: "테스트에서 안 멈췄다"는 안전의 증거가 아니다. 규칙(signal-safety(7))을 따른다.

## 쓰이는 자료구조·알고리즘

- **비트마스크(sigset_t)** — 대기·막음·무시·잡음 집합을 비트 하나씩으로 표현한다. 합집합·교집합이 비트 연산 한 번이다. 표준 시그널은 "이미 켜진 비트면 또 넣지 않는다"는 규칙으로 쌓이지 않는다(`legacy_queue()`). [data-structure/18-bitset](../../data-structure/18-bitset/2-summary.md)
- **연결 리스트 큐(sigqueue)** — 실시간 시그널과 `siginfo`는 `struct sigpending`의 리스트에 순서대로 쌓인다. [data-structure/02-linked-list](../../data-structure/02-linked-list/2-summary.md)
- **자기 파이프(self-pipe) / signalfd** — 비동기 알림을 동기 이벤트 큐로 바꾸는 기법이다.
  - self-pipe: 핸들러는 파이프에 1바이트를 `write`만 한다. 이벤트 루프가 그 fd를 읽어 본 처리를 한다.
  - `signalfd(2)`: 핸들러가 없다. 대상 시그널을 막아 두고, fd에서 `signalfd_siginfo`를 `read`해 pending 시그널을 꺼낸다.
- **플래그 폴링** — 핸들러는 `volatile sig_atomic_t` 플래그만 세우고, 메인 루프가 플래그를 확인한다.

## 적용 — 풀어나가는 법

### 1. 핸들러는 "표시만" 한다 — C

```c
#include <signal.h>
#include <unistd.h>

static volatile sig_atomic_t stop;          /* 핸들러와 메인이 공유하는 유일한 값 */

static void on_term(int sig) { (void)sig; stop = 1; }   /* 안전: 대입 한 번 */

int main(void) {
    struct sigaction sa = {0};
    sa.sa_handler = on_term;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = SA_RESTART;               /* 느린 호출은 자동 재시작 */
    sigaction(SIGTERM, &sa, NULL);          /* signal(2)보다 sigaction(2)이 이식성 있다 */
    sigaction(SIGINT,  &sa, NULL);

    while (!stop) {
        /* 요청 처리 한 단위 */
    }
    /* 여기서 정리: 새 요청 거절 -> 진행 중 작업 마무리 -> 버퍼 flush -> 종료 */
    return 0;
}
```

- `signal(2)` 대신 `sigaction(2)`을 쓴다. `signal(2)`은 핸들러를 설치할 때 동작이 시스템마다 다르다(signal(7) "less portable").
- 멀티스레드 서버는 모든 스레드에서 시그널을 막고, 전용 스레드 하나가 `sigwait(3)`나 `signalfd(2)`로 받는 방식이 흔하다.

### 2. Java — 셧다운 훅

```java
Runtime.getRuntime().addShutdownHook(new Thread(() -> {
    server.stopAccepting();      // 새 요청 거절
    server.awaitInFlight(20, TimeUnit.SECONDS);   // 진행 중 요청 마무리 (값은 예시)
    log.flush();
}));
```

- JDK는 기본 설정(`-Xrs` 없음)에서 SIGTERM·SIGINT·SIGHUP에 자체 핸들러를 걸고, 받으면 셧다운 훅을 돌린 뒤 `128+N`으로 끝낸다(OpenJDK `Terminator.java`).
- SIGKILL에는 훅이 돌지 않는다. 잡을 수 없는 시그널이다.
- HotSpot은 SIGPIPE에 자체 핸들러를 걸고, 받으면 아무 일도 하지 않고 넘긴다(OpenJDK `signals_posix.cpp` `set_signal_handler(SIGPIPE)`, "Ignore SIGPIPE and SIGXFSZ"). `SIG_IGN`은 아니지만 효과는 무시와 같다. 그래서 끊긴 소켓에 쓰면 프로세스가 죽지 않고 `IOException: Broken pipe`가 난다.

### 3. Node.js — `process.on('SIGTERM')`

```js
const server = http.createServer(handler).listen(8080);
process.on('SIGTERM', () => {
  server.close(() => process.exit(0));      // 새 연결 거절, 기존 연결이 끝나면 종료
  setTimeout(() => process.exit(1), 20_000).unref();  // 안전장치 (값은 예시)
});
```

- Node는 시작할 때 SIGPIPE를 `SIG_IGN`으로 둔다(nodejs/node `src/node.cc`). 쓰기가 `EPIPE`로 실패하면 프로세스가 죽지 않고 에러 이벤트가 된다(`ECONNRESET`으로 보일 수도 있다).

### 4. 진단 명령

```bash
# 어떤 시그널을 막고/무시하고/잡는지 (16진 비트마스크, 비트 n-1 = 시그널 n)
grep -E 'Sig(Pnd|Blk|Ign|Cgt)|ShdPnd' /proc/<pid>/status

# 누가 어떤 시그널을 받았나 (strace는 시그널 도착을 --- SIGTERM {...} --- 로 보여 준다)
strace -f -e trace=none -e signal=all -p <pid>

# 시그널 보내기 / 번호 목록
kill -TERM <pid>
kill -l

# 컨테이너 종료 코드: 137 = SIGKILL, 143 = SIGTERM, 139 = SIGSEGV (128+N 관례. exit(137)도 137이다)
kubectl get pod <pod> -o jsonpath='{.status.containerStatuses[0].lastState.terminated}'
```

- 비트마스크 읽기: `SigCgt: 0000000000004002`면 비트 1(SIGINT=2)과 비트 14(SIGTERM=15)가 켜져 있다.

## 장애 시나리오와 대처

### 1. SIGTERM을 무시 → 유예 후 SIGKILL, `exit 137`

- **현상**: 배포·스케일 인 때마다 파드가 30초씩 걸려 내려가고, 진행 중 요청이 끊긴다.
- **보이는 형태**
  - `kubectl describe pod`의 종료 상태 `Exit Code: 137`(`128 + 9`).
  - 애플리케이션 종료 로그가 없다.
- **원인**
  - kubelet이 컨테이너 런타임을 시켜 각 컨테이너의 주 프로세스에 SIGTERM을 보낸다. 많은 런타임은 이미지에 `STOPSIGNAL`이 있으면 그것을 대신 보낸다. 유예 시간(`terminationGracePeriodSeconds`, 기본 30초)이 지나면 남은 프로세스에 SIGKILL을 보낸다(k8s Pod Lifecycle 문서 "Termination of Pods").
  - 앱이 SIGTERM을 잡지 않거나, 잡고도 종료하지 않았다.
  - 흔한 함정: 앱이 **컨테이너의 PID 1**이면 다른 프로세스가 보낸 시그널 중 핸들러를 설치하지 않은 것은 전달되지 않는다. 기본 동작(종료)도 일어나지 않는다(pid_namespaces(7) "Only signals for which the init process has established a signal handler can be sent"). 예외: 조상 네임스페이스에서 보낸 SIGKILL·SIGSTOP은 강제로 전달되고, 자기 잘못된 메모리 접근으로 난 SIGSEGV 같은 강제 시그널로도 죽는다(`force_sig_info_to_task()`).
  - 셸 형식 `CMD java -jar app.jar`처럼 `sh -c`가 PID 1이 되면 SIGTERM이 셸에서 멈추고 자식 앱에 전해지지 않을 수 있다.
- **대처**
  - 앱이 SIGTERM을 잡아 정리 후 스스로 끝내게 한다(위 적용 1~3).
  - PID 1 문제는 `exec` 형식 CMD로 앱을 직접 PID 1로 두거나, `tini` 같은 작은 init을 둔다(05번 fork·exec·wait).
  - 정리 시간이 30초를 넘으면 `terminationGracePeriodSeconds`를 늘린다.
  - graceful shutdown 절차 전체는 [ops-patterns/19-graceful-shutdown](../../ops-patterns/19-graceful-shutdown/2-summary.md).

### 2. SIGPIPE로 조용한 종료 (`exit 141`)

- **현상**: 배치 스크립트나 C로 된 도구가 로그 한 줄 없이 사라진다. 코어 덤프도 없다.
- **보이는 형태**
  - 종료 코드 141(`128 + 13`). `set -o pipefail`이면 파이프라인 전체가 141로 실패한다.
  - 로컬 재현: `yes | head -1`의 `PIPESTATUS`가 `141 0`이었다(예시, 리눅스 7.0).
- **원인**
  - 읽는 쪽 fd가 모두 닫힌 파이프에 `write`하면 커널이 SIGPIPE를 보낸다. 기본 동작은 종료다(pipe(7)).
  - 스트림 소켓도 쓰기가 `EPIPE` 조건(연결이 이미 끊겨 보낼 수 없음)에 걸리면 SIGPIPE가 난다(send(2) `EPIPE`). 상대가 막 닫은 직후의 첫 `write`는 성공할 수 있고, `ECONNRESET`이 먼저 날 수도 있다.
  - 종료는 기본 동작이라 핸들러도 로그도 없다.
- **대처**
  - 서버 프로그램은 SIGPIPE를 무시하고 `write`의 `EPIPE`를 에러로 처리한다. JVM(아무것도 안 하는 핸들러)·Node(`SIG_IGN`)는 이미 이렇게 한다.
  - 호출 단위로는 `send(fd, buf, len, MSG_NOSIGNAL)`을 쓴다. 프로세스 전체 설정을 건드리지 않는다(send(2)).
  - 셸에서 `| head`로 일부만 읽는 것이 의도라면 141을 정상으로 취급한다.

### 3. 핸들러 안의 `malloc`·`printf` → 드문 데드락

- **현상**: 평소엔 멀쩡한데, 가끔 프로세스가 CPU 0%로 영원히 멈춘다. 재시작하면 한동안 괜찮다.
- **보이는 형태**
  - `cat /proc/<pid>/wchan`이 `futex_do_wait` 같은 대기 함수를 보인다. `State: S (sleeping)`.
  - gdb 백트레이스에 `<signal handler called>` 아래위로 `malloc`이 두 번 보인다(위 재현).
- **원인**
  - 메인 흐름이 힙 락을 잡은 채 시그널로 끊겼다. 핸들러가 같은 락을 요청했다. 락 주인은 핸들러가 돌아오기를 기다리는 자기 자신이다.
  - `printf` 같은 stdio는 데드락 대신 버퍼를 망가뜨릴 수도 있다(signal-safety(7)).
- **대처**
  - 핸들러에서는 async-signal-safe 함수만 부른다. 보통은 플래그 대입이나 self-pipe `write` 하나로 끝낸다.
  - 로그는 메인 루프가 플래그를 본 뒤 남긴다.
  - 이미 이런 코드가 있다면 `signalfd(2)`나 `sigwait(3)` 전용 스레드로 옮긴다.

### 4. `EINTR`를 처리하지 않아 간헐 실패

- **현상**: 타이머·프로파일러·자식 종료 시그널이 있을 때만 `read`·`accept`·`sem_wait` 등이 가끔 실패한다.
- **보이는 형태**: 로그에 `Interrupted system call`(EINTR). 재현이 어렵다.
- **원인**
  - 핸들러를 `SA_RESTART` 없이 설치했다. 또는 `SA_RESTART`와 무관하게 `EINTR`을 내는 호출이다(signal(7) 목록).
  - 코드가 `-1`을 곧바로 치명적 에러로 취급한다.
- **대처**
  - 재시도해도 되는 블로킹 호출을 `while (r == -1 && errno == EINTR)` 재시도로 감싼다. 리눅스 `close()`는 예외다 — `EINTR`이어도 fd가 이미 닫혔으니 재시도하면 남의 fd를 닫을 수 있다(close(2) NOTES).
  - 핸들러에 `SA_RESTART`를 준다. 다만 모든 호출을 구하지 못한다는 점을 기억한다.

### 5. SIGCHLD를 한 번씩만 셈 → 좀비 누적

- **현상**: 자식을 많이 띄우는 서버에서 `<defunct>` 프로세스가 조금씩 늘어난다.
- **보이는 형태**: `ps -o pid,stat,cmd --ppid <부모>`에 `Z` 상태가 남는다.
- **원인**: 자식 여럿이 거의 동시에 끝나면 SIGCHLD는 한 번만 pending된다(표준 시그널은 쌓이지 않는다). 핸들러가 `waitpid`를 한 번만 부르면 나머지 자식은 회수되지 않는다.
- **대처**: 핸들러(또는 메인 루프)에서 `while (waitpid(-1, &st, WNOHANG) > 0) ;`로 끝난 자식을 전부 회수한다. 좀비·PID 고갈은 04·05번에서 이어진다.

## 핵심 문장

- 시그널은 생성 → 대기(pending) → 전달의 세 단계를 거친다. 전달은 커널이 유저 모드로 돌아가는 순간에 일어난다.
- 커널은 이미 pending인 표준 시그널을 또 넣지 않으므로 **표준 시그널은 쌓이지 않는다**. 실시간 시그널만 큐에 쌓인다.
- 처리 방식은 프로세스 단위, 마스크는 스레드 단위다. SIGKILL·SIGSTOP은 잡거나 막을 수 없다.
- 핸들러는 메인 흐름의 아무 명령 사이에 끼어든다. 그래서 async-signal-safe 함수만 부르고, 보통은 플래그만 세운다.
- 시그널로 죽은 프로세스의 종료 코드는 bash·런타임 관례로 128+N이다(`exit(137)`과는 wait 상태로 구분). 137 = SIGKILL, 143 = SIGTERM, 141 = SIGPIPE, 139 = SIGSEGV.
- 컨테이너 PID 1은 다른 프로세스가 보낸, 핸들러 없는 시그널을 받지 않는다(조상의 SIGKILL·SIGSTOP 제외). SIGTERM이 무시되면 유예 뒤 SIGKILL(137)로 끝난다.

## 관련 주제·근거

- 선행: [05-fork-exec-wait](../05-fork-exec-wait/2-summary.md) — fork·exec 때의 시그널 상속, 좀비 회수, 컨테이너 PID 1(tini).
- 후속·연결
  - [07-threads-and-context-switch](../07-threads-and-context-switch/2-summary.md) — 스레드별 마스크, 커널 ↔ 유저 전환.
  - [09-address-space](../09-address-space/2-summary.md) — SIGSEGV(exit 139)가 나는 주소.
  - [26-io-multiplexing-epoll](../26-io-multiplexing-epoll/2-summary.md) — 이벤트 루프와 `EINTR`·signalfd.
  - [28-containers-namespaces-cgroups](../28-containers-namespaces-cgroups/2-summary.md) — PID 네임스페이스와 PID 1.
  - [37-os-symptom-index](../37-os-symptom-index/2-summary.md)(errno·exit code 역색인).
  - [ops-patterns/19-graceful-shutdown](../../ops-patterns/19-graceful-shutdown/2-summary.md) — SIGTERM 이후의 드레이닝 절차.
  - [reliability/README](../../reliability/README.md) — `14-graceful-shutdown`, `09-cancellation-propagation`.
- Linux man-pages (로컬 `man`, man-pages 6.7 계열로 확인)
  - signal(7) — 처리 방식, 대기·마스크, 전달 절차(1)~(5), 표준 시그널 표·번호, 표준 시그널은 쌓이지 않음, EINTR·SA_RESTART 목록, fork/execve 상속 <https://man7.org/linux/man-pages/man7/signal.7.html>
  - signal-safety(7) — async-signal-safe 목록, stdio 불안전, errno 저장 <https://man7.org/linux/man-pages/man7/signal-safety.7.html>
  - pid_namespaces(7) — init(PID 1)에 대한 시그널 제한 <https://man7.org/linux/man-pages/man7/pid_namespaces.7.html>
  - signalfd(2) · close(2) NOTES(EINTR 후 재시도 금지)
  - pipe(7) SIGPIPE/EPIPE · send(2) `MSG_NOSIGNAL` · sigaction(2) · proc_pid_status(5) `SigPnd`·`ShdPnd`·`SigBlk`·`SigIgn`·`SigCgt` · bash(1) "128+N"
- 소스
  - kernel/signal.c (v6.16) — `sig_ignored()`(막히지 않은 무시 시그널은 생성 시 버림), `prepare_signal()`(SIGCONT 생성 시점 효과), `legacy_queue()`(pending 표준 시그널 재등록 생략), `__send_signal_locked()`(RT 큐 할당 실패 분기), `force_sig_info_to_task()` <https://github.com/torvalds/linux/blob/v6.16/kernel/signal.c>
  - include/linux/signal_types.h — `struct sigpending { list; sigset_t signal; }` <https://github.com/torvalds/linux/blob/master/include/linux/signal_types.h>
  - OpenJDK `src/java.base/unix/classes/java/lang/Terminator.java` — HUP·INT·TERM 핸들러, `Shutdown.exit(sig.getNumber() + 0200)`
  - OpenJDK `src/hotspot/os/posix/signals_posix.cpp` — `set_signal_handler(SIGPIPE)`, 핸들러 안 "Ignore SIGPIPE and SIGXFSZ"
  - glibc 2.39 `malloc/malloc.c` — `__libc_malloc`의 `SINGLE_THREAD_P` 분기(단일 스레드면 arena 락 생략)
  - nodejs/node `src/node.cc` — 시작 시 SIGPIPE·SIGXFSZ를 `SIG_IGN`으로 설정
- POSIX.1-2024 XCU §2.8.2 — 시그널 종료 상태는 128보다 큰 값 <https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html>
- Java `java` 명령 문서 `-Xrs` — HUP·INT·TERM·QUIT 핸들러를 설치하지 않음 <https://docs.oracle.com/en/java/javase/25/docs/specs/man/java.html>
- Kubernetes 문서 "Pod Lifecycle — Termination of Pods" — SIGTERM/STOPSIGNAL → 유예(기본 30초) → SIGKILL <https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/>
- 교재: CS:APP 3판 8.5 Signals(8.5.3 수신, 8.5.4 블록, 8.5.5 핸들러 작성, 8.5.6 동시성 버그)
- 로컬 재현(리눅스 7.0 · glibc 2.39): 대기 비트마스크와 비누적, 핸들러 안 `malloc` 데드락(gdb 백트레이스), `yes | head -1` → 141, `kill -TERM`/`-9`/`-SEGV` → 143/137/139
