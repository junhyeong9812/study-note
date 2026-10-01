# os/05-fork-exec-wait — 나를 복제하고, 다른 프로그램으로 갈아입고, 끝을 거둔다 — 정리 (힌트)

## 해결하는 문제

셸에 `ls > out.txt`를 치면 새 프로세스가 `ls`를 실행하고, 출력은 파일로 간다. 셸은 끝나기를 기다렸다가 다음 프롬프트를 띄운다.\
이를 위해 세 가지가 필요하다.

```text
  필요한 것                               유닉스의 답
  새 프로세스를 만든다                      fork()   — 나를 복제한다
  그 프로세스가 다른 프로그램을 실행한다       exec()   — 복제본이 다른 프로그램으로 갈아입는다
  끝났는지, 어떻게 끝났는지 안다             wait()   — 자식의 종료 상태를 거둔다
```

왜 "만들기+실행"을 한 함수로 하지 않고 둘로 나눴나.\
fork와 exec **사이**에 자식이 자기 환경을 바꿀 수 있기 때문이다(OSTEP 5.4).
- 표준 출력을 파일로 바꾼다(`>`).
- 파이프를 연결한다(`|`).
- 작업 디렉터리·환경 변수·권한을 바꾼다.

쉬운 예: 복사기로 나를 복사한다.
- 복사본(자식)은 내 책상·메모(메모리·열린 파일)를 그대로 가지고 태어난다.
- 복사본은 옷을 갈아입고(exec) 전혀 다른 일을 한다. 이름표(PID)는 그대로다.
- 나는 복사본의 일이 끝나면 결과 보고서(종료 상태)를 받는다(wait).
- 복사본이 내 책상 열쇠(fd)를 가지고 나가면, 내가 문을 잠가도(close) 방은 열려 있다.

똑같은 구조다.\
자식은 부모의 열린 fd를 물려받는다. exec 뒤에도 기본적으로 유지된다.

실무 예:
- 컨테이너 PID 1인 앱이 자식을 회수하지 않아 `<defunct>`가 쌓인다.
- 서버가 띄운 헬퍼 프로세스가 listen 소켓을 물려받아, 서버를 재시작해도 포트가 안 풀린다.
- 메모리를 많이 쓰는 프로세스가 `fork`할 때 순간 지연이 생기고 메모리가 늘어난다.

## 동작·원리

### 세 호출의 시간표

```text
  부모 (PID 100)                         자식
  pid = fork()  ------------------------> 태어남 (PID 200), 부모의 복제본
    | fork가 200을 돌려줌                   | fork가 0을 돌려줌
    |                                      | (여기서 fd 정리·리다이렉트)
    |                                      | execvp("ls", ...)
    |                                      |   성공하면 돌아오지 않는다 — ls로 바뀜 (PID는 200 그대로)
    | waitpid(200, &st, 0)  ... 잠듦        |   실패하면 -1 → _exit(127)
    |                                      | ls 실행 ... exit(0)
    |                                      v
    |                                    좀비 (종료 상태 보관), 부모에게 SIGCHLD
    | <------ 깨어남, st에 종료 상태 --------
    v                                    사라짐
  WIFEXITED(st) && WEXITSTATUS(st) == 0
```

- `fork`는 **한 번 불려 두 번 돌아온다.** 부모에게는 자식 PID, 자식에게는 0이다. 실패면 부모에게 -1이다.
- `exec`는 성공하면 **돌아오지 않는다.** 그 다음 줄은 실패했을 때만 실행된다.
- `wait` 전까지 끝난 자식은 좀비다(04번). 단 `SIGCHLD`를 명시적으로 `SIG_IGN`으로 두거나 `SA_NOCLDWAIT`를 켰으면 좀비가 안 된다(아래 wait 절).

```c
pid_t pid = fork();
if (pid < 0) { perror("fork"); exit(1); }
if (pid == 0) {                                   /* 자식 */
    int fd = open("out.txt", O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (fd != STDOUT_FILENO) {                    /* stdout이 닫혀 있어 fd가 1이면 그대로 둔다 */
        dup2(fd, STDOUT_FILENO);                  /* 표준 출력을 파일로 */
        close(fd);
    }
    execlp("ls", "ls", "-l", (char *)NULL);
    _exit(127);                                   /* exec 실패. exit 아닌 _exit */
}
int st;
waitpid(pid, &st, 0);                             /* 부모 */
if (WIFEXITED(st))        printf("exit %d\n", WEXITSTATUS(st));
else if (WIFSIGNALED(st)) printf("signal %d\n", WTERMSIG(st));
```

- 자식이 exec 실패 뒤 `exit`가 아니라 `_exit`를 쓰는 이유: `exit`는 stdio 버퍼를 비우고 `atexit` 핸들러를 돈다. 부모에게서 복사된 버퍼가 **두 번** 출력될 수 있다.
  - 로컬 재현: `printf("hello ")`(줄바꿈 없음, 파이프로 출력) 뒤 `fork` → 출력이 `hello child` / `hello parent`로 "hello"가 두 번 나왔다.

### fork — 무엇을 복제하고 무엇을 나누나

```text
  부모                                   자식 (fork 직후)
  주소 공간 ---- 페이지 공유, 읽기 전용 표시 ---- 주소 공간      (copy-on-write)
  fd 표 [0][1][2][3]                      fd 표 [0][1][2][3]      (표는 복사)
          \  \  \  \                              /  /  /  /
           +--+--+--+-- 같은 "열린 파일 설명" -------+--+--+--+     (오프셋·플래그 공유)
  스레드: 여러 개                          스레드: fork를 부른 1개만
  대기 중인 시그널                         비어 있음
  시그널 처리 방식(핸들러)                  복사됨
```

- 자식은 부모의 **fd 표를 복사**한다. 두 fd는 같은 "열린 파일 설명(open file description)"을 가리켜 **파일 오프셋을 공유**한다(fork(2)).
  - *열린 파일 설명*: `open()` 한 번마다 커널이 만드는 객체다. 오프셋·상태 플래그를 담고, 여러 fd가 가리킬 수 있다(21번).
- 대기 중인 시그널, 메모리 락, 타이머(`alarm`·`setitimer`·`timer_create`), 프로세스에 딸린 레코드 락(전통적인 `fcntl` 락)은 물려받지 않는다(fork(2)).
  - 반대로 OFD 락·`flock` 락은 물려받는다. timerfd도 fd라서 같은 타이머를 공유한다(timerfd_create(2)).
- **자식에는 스레드가 하나만 있다.** 다른 스레드가 쥐고 있던 락은 fork가 따로 챙기지 않는 한 자식에서 영원히 안 풀린다. 그래서 멀티스레드 프로그램의 자식은 exec 전까지 async-signal-safe 함수만 써야 한다(fork(2)).
  - glibc `fork()`는 malloc·stdio 내부 락은 fork 전에 잡고 자식에서 되돌린다(posix/fork.c). 앱·다른 라이브러리의 락은 그렇지 않다(`pthread_atfork`로 직접 챙겨야 한다).
- glibc의 `fork()`는 `fork` 시스템 콜이 아니라 `clone`을 부른다. 로컬 strace: `clone(child_stack=NULL, flags=CLONE_CHILD_CLEARTID|CLONE_CHILD_SETTID|SIGCHLD, ...)`.

### copy-on-write — fork가 싼 이유

```text
  fork 직후                    자식이 페이지 P에 쓰기            결과
  부모 PTE ─┐                  쓰기 → 페이지 폴트(읽기 전용)       부모 PTE → P  (원본)
            ├─> 페이지 P        커널: P를 복사해 P'를 만들고        자식 PTE → P' (사본, 쓰기 가능)
  자식 PTE ─┘  (둘 다 읽기 전용)  자식 PTE를 P'로 바꿈
```

- fork는 private 매핑의 페이지 내용을 복사하지 않는다. **페이지 테이블**을 복사하고, 양쪽을 읽기 전용으로 표시한다.
  - 예외: `MAP_SHARED` 매핑은 COW가 아니라 계속 공유한다. 부모가 pin한(DMA 등으로 고정한) 익명 페이지는 fork 때 바로 복사한다(mm/memory.c `copy_present_ptes`).
- 아직 공유 중인 페이지에 누가 쓰는 순간 그 페이지 하나만 복사한다(minor fault, 03번). 상대가 이미 exec·종료해 혼자 남은 페이지는 복사 없이 쓰기 권한만 되돌린다(`do_wp_page`의 재사용).
- fork(2) NOTES: 비용은 "부모 페이지 테이블을 복제하는 시간·메모리 + 자식의 태스크 구조"뿐이다.

로컬 재현 — 256MB를 모두 건드린 프로세스를 fork했다(예시, 리눅스 7.0, THP 끔).

```text
  fork() 자체                           7–10 ms   (페이지 테이블 복사)
  자식이 256MB를 4KB마다 읽기             minor fault 3번
  자식이 256MB를 4KB마다 쓰기             minor fault 65555번, 189–230 ms  (256MB/4KB = 65536)
```

- 읽기만 하면 복사가 없다. 공유 중인 페이지에 **쓰는 만큼** 폴트와 메모리 복사가 생긴다.
- 그래서 "큰 프로세스 fork 뒤 부모·자식 둘 다 쓰기가 많으면" 메모리 사용이 최대 두 배까지 늘 수 있다.

### exec — 갈아입기

```text
  execve 뒤 유지되는 것                  execve 뒤 바뀌는 것
  PID, PPID                             코드·데이터·힙·스택 (새 프로그램으로 교체)
  열린 fd (FD_CLOEXEC 없는 것)            FD_CLOEXEC 표시된 fd는 닫힘
  무시(SIG_IGN)·기본 처리 시그널           잡던 시그널 핸들러 → 기본 동작으로
  실 UID·GID, 작업 디렉터리               다른 스레드 전부 소멸, 메모리 매핑 전부 해제
```

- 근거는 execve(2) "All process attributes are preserved during an execve(), except ..." 목록이다.
- **fd는 기본으로 살아남는다.** exec에서 닫히게 하려면 `O_CLOEXEC`·`SOCK_CLOEXEC`·`FD_CLOEXEC`로 표시한다.
- `execvp`·`execlp`는 `PATH`를 따라 파일을 찾는 **libc 기능**이다. 로컬 strace에서 `execve("/home/jun/.local/bin/sh") = -1 ENOENT` … `execve("/usr/bin/sh") = 0`처럼 PATH 순서대로 시도했다.

### wait — 종료 상태 읽기

```text
  status (int)
    WIFEXITED(st)   -> 정상 종료?    WEXITSTATUS(st) = exit 코드의 하위 8비트
    WIFSIGNALED(st) -> 시그널로 죽음? WTERMSIG(st)    = 시그널 번호
```

- 종료 코드는 **하위 8비트만** 부모에게 간다(exit(3) `status & 0xFF`). `exit(256)`은 0으로 보인다.
- bash는 시그널로 죽은 명령을 **128 + 시그널 번호**로 보여 준다(bash(1)). 커널의 wait 상태에는 "128+"가 없다. 셸의 관례다(셸마다 다르다: ksh93은 256 + 시그널 번호, ksh93 sh.1).
  - 로컬 재현: `sleep`에 SIGTERM → `WIFSIGNALED`, `WTERMSIG=15`, raw status 0xf.
- Java: `Process.waitFor()`는 시그널로 죽은 자식에 대해 **0x80 + 시그널 번호**를 돌려준다. "모든 유닉스 셸이 그렇게 하기 때문"이라고 주석에 적혀 있다(OpenJDK ProcessHandleImpl_unix.c `WTERMSIG_RETURN`). SIGTERM이면 143이다.
- Node: `'exit'` 이벤트가 `(code, signal)`을 준다. 로컬 재현(Node 18): 정상 종료 `code=3 signal=null`, kill → `code=null signal=SIGTERM`.
- `SIGCHLD`를 명시적으로 `SIG_IGN`으로 두면 자식이 좀비가 되지 않는다. 대신 `wait`로 종료 상태를 받을 수 없다(wait(2) NOTES).

### 다른 생성 방법 — vfork·posix_spawn

- `vfork`: 페이지 테이블도 복사하지 않고 부모 메모리를 **그대로 공유**한다. vfork를 부른 스레드는 자식이 exec하거나 끝날 때까지 멈춘다. 멀티스레드면 부모의 다른 스레드는 계속 돈다(vfork(2) CAVEATS). 바로 exec할 때 빠르지만, 자식이 메모리를 건드리면 부모가 깨진다.
- `posix_spawn`: "만들고 바로 실행"을 한 번에 요청한다. 로컬 glibc 2.39는 `clone3(CLONE_VM|CLONE_VFORK|CLONE_CLEAR_SIGHAND)`로 구현했다(strace).
- Java: 현재 OpenJDK(master) 리눅스의 기본 실행 방식은 `POSIX_SPAWN`이고, `VFORK` 옵션은 제거되어 `FORK`로 바뀐다(ProcessImpl.java `launchMechanism`). 자식 쪽에서는 exec 전에 표준 입출력(0·1·2)을 뺀 fd 3 이상 모두에 close-on-exec를 표시한다(childproc.c `markDescriptorsCloseOnExec`, `fd_from = STDERR_FILENO + 1`).
- fork를 비판하고 spawn류를 권하는 시각도 있다(Baumann 외, "A fork() in the road", HotOS 2019 — OSTEP 5장 곁글).

### PID 1과 고아 — 컨테이너

```text
  호스트 PID 네임스페이스                컨테이너 PID 네임스페이스
  ...                                  PID 1: 앱 (예: node server.js)
                                          |
                                          +-- PID 7: sh -c "..."  (앱이 띄움)
                                                  +-- PID 8: worker   (sh가 띄움)
  sh가 먼저 끝나면 → worker는 고아 → 네임스페이스의 PID 1(앱)에 입양
  worker가 끝나면 → 앱이 wait 안 하면 좀비로 남는다
```

- PID 네임스페이스에서 고아는 그 네임스페이스 안에 살아 있는 조상 subreaper가 없으면 **init(PID 1)** 이 입양한다(pid_namespaces(7), kernel/exit.c `find_new_reaper`).
- 일반 init은 입양한 자식을 회수한다. 하지만 앱이 PID 1이면 **앱이 그 일을 해야** 한다. 대부분의 앱은 모르는 자식을 `wait`하지 않는다.
- tini는 "자식 하나를 띄우고, 좀비를 회수하고, 시그널을 전달하는" 최소 init이다. Docker 1.13+는 `docker run --init`으로 내장한다(tini README).
- 로컬 재현(네임스페이스 대신 `PR_SET_CHILD_SUBREAPER`로 흉내): subreaper가 `wait`하지 않으면 입양된 손자까지 좀비 6개가 남았다. `SIGCHLD` 핸들러에서 `waitpid(-1, 0, WNOHANG)`을 돌리자 0개였다.

## 쓰이는 자료구조·알고리즘

- **copy-on-write 페이지 + 참조 수** — 여러 프로세스가 같은 물리 페이지를 가리키는 동안은 읽기 전용으로 두고, 쓰기 폴트 때 복사한다. 공유 여부는 페이지의 참조 수로 판단한다. 불변 자료구조의 구조 공유와 같은 발상이다. [data-structure/26-persistent](../../data-structure/26-persistent/2-summary.md)
- **fd 표(배열) + 열린 파일 설명(참조 수)** — fd 번호가 배열 인덱스다. 여러 fd(다른 프로세스의 것도)가 한 열린 파일 설명을 가리키고, 마지막 참조가 닫혀야 자원이 풀린다. 그래서 자식이 물려받은 소켓은 부모가 닫아도 살아 있다. [data-structure/01-dynamic-array](../../data-structure/01-dynamic-array/2-summary.md)
- **프로세스 트리** — fork가 부모-자식 간선을 만들고, 부모가 죽으면 간선을 subreaper·init으로 다시 잇는다(04번).
- **페이지 테이블 복사** — fork 비용은 매핑된 메모리 크기에 비례한다(다단계 페이지 테이블, 10번).

## 적용 — 풀어나가는 법

### 1. 자식을 만들 때 체크리스트 (C)

- fd는 처음부터 `O_CLOEXEC`/`SOCK_CLOEXEC`로 연다. 물려줄 fd만 명시적으로 `dup2`한다(`dup2`로 만든 새 fd는 CLOEXEC가 꺼진다. 단 원본과 대상 번호가 같으면 `dup2`는 아무것도 안 하니 CLOEXEC를 `fcntl`로 직접 끈다, dup(2)).
- 이미 연 fd를 한 번에 정리하려면 `close_range(3, ~0U, CLOSE_RANGE_CLOEXEC)`(리눅스 5.11+, close_range(2)).
- exec 실패 경로는 `_exit(127)`.
- 멀티스레드 프로그램이면 fork 대신 `posix_spawn`을 쓴다.
- 부모는 반드시 회수한다. 여러 자식이면 `SIGCHLD` 핸들러에서 루프로.

```c
static void on_sigchld(int sig) {
    int saved = errno;                       /* 핸들러가 errno를 망치지 않게 */
    while (waitpid(-1, NULL, WNOHANG) > 0) ; /* 끝난 자식을 모두 회수 */
    errno = saved;
}
/* struct sigaction sa = { .sa_handler = on_sigchld, .sa_flags = SA_RESTART | SA_NOCLDSTOP };
   sigaction(SIGCHLD, &sa, NULL); */
```

- `SIGCHLD`는 여러 자식이 동시에 끝나도 **한 번**만 올 수 있다(표준 시그널은 쌓이지 않는다, 06번). 그래서 `while` 루프다.

### 2. Java·Node

```java
Process p = new ProcessBuilder("sh", "-c", "exit 7")
        .redirectErrorStream(true)
        .start();
p.getInputStream().transferTo(OutputStream.nullOutputStream()); // 출력을 읽어 줘야 파이프가 안 막힌다(30번)
int code = p.waitFor();   // 7. 시그널로 죽었으면 128+시그널
```

```js
const { spawn } = require('node:child_process');
const c = spawn('sh', ['-c', 'exit 7'], { stdio: 'inherit' });
c.on('exit', (code, signal) => console.log(code, signal));   // 7 null
```

### 3. 진단 명령

```bash
# 프로세스 생성·exec·wait만 추적
strace -f -e trace=%process ./prog

# 누가 어떤 fd(소켓)를 잡고 있나
ls -l /proc/<pid>/fd
ss -ltnp 'sport = :8080'        # users:(("sleep",pid=...,fd=3)) 처럼 잡은 프로세스가 보인다

# 부모-자식 관계
pstree -p <pid>
```

## 장애 시나리오와 대처

### 1. 컨테이너 PID 1이 자식을 회수하지 않음 → 좀비 누적

- **현상**: 오래 돈 컨테이너에서 `ps`에 `<defunct>`가 늘어나고, 결국 프로세스·스레드 생성이 실패한다.
- **보이는 형태**
  - `ps -eo pid,ppid,stat,comm`에서 PPID 1인 `Z` 다수.
  - `fork: Resource temporarily unavailable`, `pids.max` 도달(04번).
- **원인**
  - 앱이 PID 1이다. 앱이 띄운 셸·헬퍼의 자손이 고아가 되면 PID 1(앱)에 입양된다.
  - 앱은 이 자식들을 모르니 `wait`하지 않는다. 끝난 자식이 좀비로 남는다.
- **대처**
  - PID 1에 최소 init을 둔다: `docker run --init`, 또는 `ENTRYPOINT ["/tini", "--", "app"]`.
  - 앱이 직접 자식을 띄운다면 회수까지 책임진다(`SIGCHLD` + `waitpid` 루프).
  - PID 1은 시그널 처리도 특별하다. 같은 네임스페이스(또는 조상 네임스페이스)에서 보낸 시그널 중 PID 1이 핸들러를 달지 않은 것은 전달되지 않는다. 조상에서 보낸 SIGKILL·SIGSTOP만 예외다(pid_namespaces(7)). SIGTERM 문제는 06번.

### 2. fork 후 fd 상속 → 소켓·파이프가 안 닫힘

- **현상**
  - 서버를 재시작하면 `Address already in use`로 bind가 실패한다.
  - 또는 클라이언트가 응답 끝(EOF)을 못 받고 멈춘다. 파이프를 읽는 쪽이 끝나지 않는다.
- **보이는 형태**
  - `ss -ltnp`에서 그 포트를 **엉뚱한 프로세스**(서버가 띄운 헬퍼)가 잡고 있다.
  - 로컬 재현: listen 소켓을 연 부모가 `sleep 4`를 fork+exec하고 소켓을 닫은 뒤 종료 → `ss`에 `users:(("sleep",pid=...,fd=3))`, 새 bind는 `Address already in use`. `SOCK_CLOEXEC`로 열면 새 bind가 성공했다.
- **원인**
  - fork는 fd 표를 복사하고, exec는 CLOEXEC 없는 fd를 유지한다.
  - 열린 파일 설명은 **모든** fd가 닫혀야 풀린다. 부모가 닫아도 자식의 fd가 소켓을 살려 둔다.
  - 파이프는 쓰기 쪽 fd가 **모두** 닫혀야 읽는 쪽이 EOF를 본다(pipe(7)). 자식이 쓰기 쪽 사본을 쥐고 있으면 EOF가 영원히 안 온다.
- **대처**
  - fd를 `O_CLOEXEC`·`SOCK_CLOEXEC`로 연다. 자식에서 필요 없는 fd를 닫는다(`close_range`).
  - 파이프는 부모·자식 각각 쓰지 않는 쪽 끝을 즉시 닫는다.
  - Java `ProcessBuilder`는 자식에서 fd 3 이상 모두에 close-on-exec를 표시한다(OpenJDK childproc.c). 문제는 주로 C·셸 스크립트·직접 쓴 네이티브 코드에서 생긴다.

### 3. 큰 프로세스의 fork → 지연과 메모리 급증

- **현상**: 수 GB 메모리를 쓰는 프로세스가 스냅숏·자식 실행을 위해 fork할 때 요청이 순간 멈추고, 이후 메모리가 크게 는다.
- **보이는 형태**: fork 순간 지연 스파이크, 이어서 `minflt/s` 급증과 RSS 증가. 심하면 `fork` 실패(`ENOMEM`) 또는 OOM(13번).
- **원인**
  - fork는 익명 메모리 영역의 페이지 테이블을 복사한다. 매핑이 클수록 오래 걸린다(로컬: 256MB에 7~10ms). 폴트로 다시 채울 수 있는 파일 공유 매핑 등은 복사를 건너뛴다(mm/memory.c `vma_needs_copy`).
  - fork 뒤 자식이 살아 있는 동안 부모가 계속 쓰면, 아직 공유 중인 페이지에 쓸 때마다 copy-on-write 복사가 생긴다(로컬: 256MB 쓰기에 65555번 폴트).
- **대처**
  - 바로 exec할 자식이면 `posix_spawn`·`vfork` 계열을 쓴다(페이지 테이블 복사 없음).
  - 스냅숏용 fork라면 fork 동안 쓰기량을 줄이고, 메모리 여유(최대 두 배)를 잡는다.
  - 큰 페이지(THP)는 페이지 테이블을 줄인다. COW 단위는 커지지 않는다: 리눅스 5.8부터 공유된 익명 THP에 쓰면 PMD를 쪼개 4KB 한 장만 복사한다(커밋 3917c80280c9 "thp: change CoW semantics for anon-THP", mm/huge_memory.c `do_huge_pmd_wp_page`). 대신 쪼갠 영역은 THP 이점을 잃는다.

### 4. 멀티스레드 프로세스에서 fork 후 자식이 멈춤

- **현상**: 스레드가 많은 프로그램이 fork한 자식이 exec 전에 멈춰 버린다. 가끔만 난다.
- **보이는 형태**: 자식이 `S`/futex 대기에서 영원히 멈춤, 부모의 `waitpid`도 안 끝남.
- **원인**: 자식에는 fork를 부른 스레드 하나만 있다. 다른 스레드가 fork 순간 쥐고 있던 락(예: 앱의 mutex, 로거·다른 라이브러리의 락)은 자식에서 풀어 줄 스레드가 없다. 자식이 그 락이 필요한 함수를 부르면 멈춘다. glibc는 malloc·stdio 내부 락은 fork 때 챙기지만(posix/fork.c), POSIX는 여전히 async-signal-safe 함수만 허용한다.
- **대처**: fork 후 exec 전에는 async-signal-safe 함수만 쓴다(fork(2)). 더 안전하게는 `posix_spawn`을 쓴다.

### 5. 종료 코드를 잘못 읽음

- **현상**: 실패한 작업이 "성공(0)"으로 보이거나, 143·137 같은 숫자의 뜻을 모른다.
- **보이는 형태**: CI·오케스트레이터 로그의 exit code.
- **원인**
  - 종료 코드는 하위 8비트만 전달된다. `exit(256)` → 0, `exit(-1)` → 255.
  - 시그널로 죽은 경우 커널 상태에는 "시그널 번호"가 들어 있고, bash·Java가 128+n으로 바꿔 보여 준다. 143 = SIGTERM, 137 = SIGKILL, 139 = SIGSEGV.
- **대처**: 종료 코드는 0~255 안에서 정의한다. 시그널 종료는 `WIFSIGNALED`·Node의 `signal` 인자로 따로 처리한다.

## 핵심 문장

- `fork`는 한 번 불려 두 번 돌아오고(부모: 자식 PID, 자식: 0), `exec`는 성공하면 돌아오지 않으며, `wait`는 자식의 종료 상태를 거두고 좀비를 없앤다.
- fork와 exec를 나눈 덕분에, 그 사이에서 자식이 리다이렉트·파이프·환경을 바꿀 수 있다.
- fork는 (private 매핑의) 페이지를 복사하지 않고 페이지 테이블을 복사한 뒤 copy-on-write로 공유 중에 쓴 페이지만 복사한다. 비용은 매핑 크기와 fork 뒤 쓰기량에 비례한다.
- fd는 fork로 복사되고 exec 뒤에도 기본으로 살아남는다. `O_CLOEXEC`가 없으면 자식이 소켓·파이프를 잡아 포트 재사용·EOF를 막는다.
- 컨테이너에서 앱이 PID 1이면 고아가 앱에 입양된다. 회수하지 않으면 좀비가 쌓이니 tini(`--init`) 같은 최소 init을 둔다.

## 관련 주제·근거

- 선행: [04-process-and-lifecycle](../04-process-and-lifecycle/2-summary.md) — 좀비·고아·입양
- 후속·연결
  - [06-signals](../06-signals/2-summary.md) — SIGCHLD, PID 1의 시그널, exit 137·143.
  - [21-files-and-descriptors](../21-files-and-descriptors/2-summary.md) — fd 표와 열린 파일 설명.
  - [28-containers-namespaces-cgroups](../28-containers-namespaces-cgroups/2-summary.md) — PID 네임스페이스·`pids.max`.
  - [30-ipc](../30-ipc/2-summary.md) — 파이프, 자식 출력을 안 읽어 생기는 교착.
  - [13-oom-and-memory-limits](../13-oom-and-memory-limits/2-summary.md) — fork·COW와 overcommit.
  - [02-system-calls](../02-system-calls/2-summary.md) — `fork()` 래퍼가 `clone`을 부르는 것
- 교재
  - OSTEP 5장 Interlude: Process API — 5.1 fork, 5.2 wait, 5.3 exec, 5.4 Why? Motivating The API, 곁글 [B+19] <https://pages.cs.wisc.edu/~remzi/OSTEP/cpu-api.pdf>
  - CS:APP 3판 8.4 Process Control
  - Baumann, Appavoo, Krieger, Roscoe, "A fork() in the road", HotOS 2019
- man
  - fork(2) — 복제·비상속 목록, 멀티스레드 주의, COW 비용(NOTES), glibc `clone` <https://man7.org/linux/man-pages/man2/fork.2.html>
  - execve(2) — 유지·초기화 목록, fd 기본 유지, `FD_CLOEXEC` <https://man7.org/linux/man-pages/man2/execve.2.html>
  - wait(2) — 상태 매크로, 좀비, `SIGCHLD` `SIG_IGN` · exit(3) — `status & 0xFF` · bash(1) — 128+n
  - vfork(2)(CAVEATS: 호출 스레드만 정지) · posix_spawn(3) · dup(2) · timerfd_create(2) · fcntl_locking(2)(OFD 락) · close_range(2)(5.9+, `CLOSE_RANGE_CLOEXEC` 5.11+) · pipe(7)(EOF 조건) · pid_namespaces(7)(namespace init) · prctl(2)(`PR_SET_CHILD_SUBREAPER`)
- tini README — 좀비 회수·시그널 전달, Docker 1.13+ `--init` <https://github.com/krallin/tini>
- OpenJDK(master)
  - src/java.base/unix/classes/java/lang/ProcessImpl.java — `launchMechanism` 기본 `POSIX_SPAWN`, `VFORK` 제거
  - src/java.base/unix/native/libjava/ProcessHandleImpl_unix.c — `WTERMSIG_RETURN` = 0x80 + 시그널
  - src/java.base/unix/native/libjava/childproc.c — `markDescriptorsCloseOnExec`(fd 3부터)
- glibc 2.39 posix/fork.c — malloc·stdio 락 처리 · Linux v7.0 mm/memory.c `copy_present_ptes`(pin된 익명 페이지 즉시 복사)·`do_wp_page`, kernel/exit.c `find_new_reaper` · ksh93 sh.1(256+n)
- 로컬 재현(리눅스 7.0.0, glibc 2.39, Node 18): fork→clone·posix_spawn→clone3 strace, execvp의 PATH 탐색, `exit 3`·SIGTERM 상태 해석, 256MB COW(fork 7~10ms, 읽기 3·쓰기 65555 폴트), `printf` 버퍼 이중 출력, listen 소켓 상속으로 bind 실패·`SOCK_CLOEXEC`로 해결, subreaper 미회수 좀비 6개·회수 0개, Node `'exit'`의 code·signal
