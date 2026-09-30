# os/37-os-symptom-index — 증상 사전: errno·종료 코드·프로세스 상태·지표 패턴·커널 로그 → 원인 leaf — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> ⚠️ 이 서머리는 Claude 초안(2026-09-30) — 근거는 아래 「관련 주제·근거」. 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 해결하는 문제

운영체제 영역의 다른 노트는 **원인에서 증상으로** 간다.\
"부모가 `wait`를 안 하면 → 좀비가 쌓이고 → `fork`가 `EAGAIN`으로 실패한다"처럼 쓴다.\
장애 현장에서는 반대 방향이 필요하다.\
대시보드에 "exit 137" 한 줄, 또는 "load 40인데 CPU 10%"라는 그래프 한 장만 있다. 이게 어느 노트의 이야기인지부터 찾아야 한다.

이 노트는 그 **역방향 색인**이다.

```text
  다른 노트 (정방향)                        이 노트 (역방향)
  원인 --> 메커니즘 --> 증상                 증상 --> 층 --> 흔한 원인 --> 첫 명령 --> leaf 노트
  "cgroup 한도에 닿으면 SIGKILL, 137"         "137이 떴다. 후보는 셋이다. memory.events부터"
```

쉬운 예: 자동차 계기판의 경고등 설명서다.\
엔진 경고등이 켜졌다고 엔진을 뜯지 않는다. 설명서가 "이 등이면 먼저 이것을 보라"고 알려 준다.\
설명서는 차를 고치지 않는다. **어디를 먼저 볼지**만 정한다.

똑같은 구조다.\
`exit 137` + "`memory.events`의 `oom_kill`이 늘었다" → OOM(13번)으로 간다.\
`exit 137` + "종료가 늘 유예 시간을 꽉 채웠다" → SIGTERM 처리(06·28번)로 간다.

실무 예:
- 같은 사건이 층마다 **다른 이름**으로 보인다. 커널의 SIGKILL은 셸에서 `Killed`와 137, 쿠버네티스에서 `OOMKilled`, Node에서 `signal: 'SIGKILL'`이다.
- 이름이 같아도 **호출**이 다르면 뜻이 다르다. `read`의 `EAGAIN`은 "지금 데이터 없음"이고, `fork`의 `EAGAIN`은 "프로세스·스레드 한도"다.
- 에러가 **없는** 증상도 있다. load만 높음, 카운터 합계가 틀림, 재부팅 뒤 0바이트 파일이 그렇다.

## 동작·원리

### 0. 증상이 올라오는 길 — 어느 층이 만든 말인가

```text
  +---------------------------------------------------------------------+
  | 애플리케이션 로그    "작업 실패" (원문을 버리면 여기서 끝)                 |
  +---------------------------------------------------------------------+
  | 런타임 번역          Java 예외·JVM 종료 코드 / Node err.code·(code,signal) |
  +---------------------------------------------------------------------+
  | 셸·오케스트레이터     종료 코드 0~255, 128+N, OOMKilled, "Killed"          |
  +---------------------------------------------------------------------+
  | libc / 시스템 콜     errno: EINTR EAGAIN EMFILE ENOSPC ENOMEM EIO ...    |
  +---------------------------------------------------------------------+
  | 커널                 시그널 전달, OOM killer, 스케줄러·load, 페이지 캐시,   |
  |                     writeback, 커널 로그(dmesg)                          |
  +---------------------------------------------------------------------+
  | 장치·하이퍼바이저     디스크 오류, RAID degraded, steal time               |
  +---------------------------------------------------------------------+
```

- 아래층 사건이 위층 이름으로 **번역**되어 올라온다. 번역하면서 정보가 줄어든다.
  - 예: 종료 코드 137은 "SIGKILL로 죽었다"까지만 말한다. **누가** 보냈는지(OOM killer, kubelet, 사람)는 빠진다.
- 그래서 색인을 쓰기 전에 두 가지를 확보한다.
  - **원문**: 예외 타입·메시지, errno 이름, 종료 코드와 시그널, 커널 로그 줄.
  - **모양**: 즉시 났나, 서서히 나빠졌나, 주기적인가. 한 코어인가, 전체인가.

  - *errno*: 시스템 콜이나 libc 함수가 실패했을 때 이유를 담는 정수다. 이름(`EMFILE`)과 문자열("Too many open files")이 붙는다(errno(3)).
  - *종료 상태(wait status)*: 부모가 `wait`로 받는 값이다. "정상 종료 + 코드"인지 "시그널로 죽음 + 시그널 번호"인지를 따로 담는다(05번).

### 1. 종료 코드 사전 — 128+N 규칙

```text
  커널이 부모에게 주는 것 (wait status)          셸·런타임이 보여 주는 숫자
  --------------------------------------      --------------------------------
  WIFEXITED,   WEXITSTATUS = 0~255     ---->   그 값 그대로 (exit(256) -> 0)
  WIFSIGNALED, WTERMSIG    = N         ---->   128 + N  (bash 관례)
```

- bash는 치명적 시그널 N으로 끝난 명령의 상태를 128+N으로 적는다(bash(1) "EXIT STATUS"). 커널의 wait 상태에는 "128+"가 없다(05·06번).
- 종료 코드는 하위 8비트만 전달된다. 이 노트 작성 환경(bash 5.2)에서 `exit 256`은 0, `exit -1`은 255였다(05번과 같은 결과).

| 코드 | 셸 메시지 (`LC_ALL=C`, bash 5.2) | 시그널 | 흔한 원인 | 첫 명령 | leaf |
|---|---|---|---|---|---|
| 126 | `Permission denied` | — | 실행 권한 없는 파일을 실행 | `ls -l`, `stat` | [29](../29-linking-and-loading/2-summary.md) |
| 127 | `No such file or directory` / `not found` | — | 명령 없음, 또는 ELF 로더(`PT_INTERP`)가 없음(alpine에 glibc 바이너리), `error while loading shared libraries` | `strace -f -e trace=execve`, `ldd`, `file` | [29](../29-linking-and-loading/2-summary.md) |
| 129 | `Hangup` | SIGHUP(1) | 터미널 세션 종료, 핸들러 없는 데몬에 재로드 신호 | 누가 보냈나: 부모·세션 | [06](../06-signals/2-summary.md) |
| 130 | (출력 없음, `^C`) | SIGINT(2) | 사용자가 Ctrl-C | — | [06](../06-signals/2-summary.md) |
| 132 | `Illegal instruction (core dumped)` | SIGILL(4) | 다른 CPU용으로 빌드한 바이너리(`-march=native`) | `grep -o -w avx512f /proc/cpuinfo`, 코어의 `x/i $pc` | [01](../01-kernel-and-user-mode/2-summary.md) · [03](../03-interrupts-traps-faults/2-summary.md) |
| 134 | `Aborted (core dumped)` | SIGABRT(6) | `abort()`: glibc가 double free 감지, `_FORTIFY_SOURCE` 검사 실패, JVM 치명 오류(`hs_err_pid*.log`) | stderr 마지막 줄, 코어 `bt` | [11](../11-heap-allocation/2-summary.md) · [26](../26-io-multiplexing-epoll/2-summary.md) · [09](../09-address-space/2-summary.md) |
| 135 | `Bus error (core dumped)` | SIGBUS(7) | `mmap`한 파일을 다른 프로세스가 `truncate`한 뒤 매핑을 직접 읽거나 씀. 같은 매핑을 `write`에 넘긴 경우는 SIGBUS가 아니라 `-1 EFAULT`다(34번, 리눅스 7.0 재현) | 로그 회전·파일 교체 시각과 대조, `/proc/<pid>/maps`, `strace`의 `EFAULT` | [14](../14-mmap-and-page-cache/2-summary.md) · [34](../34-zero-copy-and-io-uring/2-summary.md) |
| 136 | `Floating point exception (core dumped)` | SIGFPE(8) | **정수** 0 나눗셈(부동소수 0 나눗셈은 기본 설정에서 inf) | 코어 `bt` | [03](../03-interrupts-traps-faults/2-summary.md) |
| 137 | `Killed` | SIGKILL(9) | cgroup·전체 OOM kill, 유예 시간 뒤 강제 종료, 사람의 `kill -9` | `kubectl describe pod`의 Reason, `memory.events`의 `oom_kill`, `dmesg \| grep -i 'killed process'` | [13](../13-oom-and-memory-limits/2-summary.md) · [28](../28-containers-namespaces-cgroups/2-summary.md) · [06](../06-signals/2-summary.md) |
| 139 | `Segmentation fault (core dumped)` | SIGSEGV(11) | NULL·해제된 메모리·스택 넘침·읽기 전용 쓰기, x86에서 특권 명령(#GP) | 코어 `bt`·`x/i $pc`, `si_code`(`SEGV_MAPERR`/`SEGV_ACCERR`) | [09](../09-address-space/2-summary.md) · [11](../11-heap-allocation/2-summary.md) · [01](../01-kernel-and-user-mode/2-summary.md) · [03](../03-interrupts-traps-faults/2-summary.md) |
| 141 | (출력 없음) | SIGPIPE(13) | 읽는 쪽이 닫힌 파이프·소켓에 쓰기. `yes \| head -1`의 `yes`처럼 정상일 수도 있다 | `echo ${PIPESTATUS[@]}`, `strace -e trace=write,signal` | [06](../06-signals/2-summary.md) · [30](../30-ipc/2-summary.md) |
| 143 | `Terminated` | SIGTERM(15) | 정상 종료 요청(배포·스케일 인·`docker stop`) | 종료가 유예 시간 안에 끝났나 | [06](../06-signals/2-summary.md) · [28](../28-containers-namespaces-cgroups/2-summary.md) |

- 셸 메시지와 128+N 값은 이 노트 작성 환경(리눅스 7.0, bash 5.2.21)에서 `bash -c 'kill -<SIG> $$'`로 확인했다. 로케일이 한국어면 메시지도 번역된다(예: `죽었음`, `세그멘테이션 오류`).
- 126·127은 시그널과 무관한 bash 관례다. 이 환경에서 없는 파일 실행은 127, 실행 권한 없는 파일은 126이었다.

**런타임에서 보이는 모양**

| 런타임 | 시그널로 죽은 **자식**을 볼 때 | 자기 자신이 SIGTERM을 받을 때 |
|---|---|---|
| Java | `Process.waitFor()`가 `0x80 + 시그널`을 돌려준다(OpenJDK `ProcessHandleImpl_unix.c` `WTERMSIG_RETURN`, 05번). JDK 21에서 `destroyForcibly()` 뒤 137, `destroy()` 뒤 143이었다 | 셧다운 훅을 돌린 뒤 `128 + N`으로 **스스로 exit**한다(`Terminator.java`, 06번). bash는 이것을 `Exit 143`으로 적는다 |
| Node | `'exit'` 이벤트의 `(code, signal)`이 `(null, 'SIGKILL')`처럼 **따로** 온다. 숫자 137이 아니다 | 핸들러가 없으면 시그널로 죽는다. 셸에서 143(`Terminated`) |
| C | `WIFSIGNALED(st)`·`WTERMSIG(st)`로 직접 본다(05번) | 핸들러가 없으면 시그널로 죽는다. 셸에서 143 |

- Node·JDK 행은 이 노트 작성 환경(Node 18.19, OpenJDK 21.0.12)에서 재현했다.
- **143은 두 가지다.** JVM의 143은 "SIGTERM을 받고 정상 exit(143)"이다(`WIFEXITED`). C 프로그램의 143은 "SIGTERM으로 죽음"이다(`WIFSIGNALED`). 셸 숫자는 같다. 구분이 필요하면 부모 코드에서 `WIFSIGNALED`를 본다.
- **137은 누가 보냈는지 말하지 않는다.** OOM killer, kubelet·`docker stop`의 유예 후 SIGKILL, 사람의 `kill -9`가 모두 137이다. `Reason: OOMKilled`, `memory.events`의 `oom_kill`, 커널 로그 `Killed process`로 가른다(13·28번).

### 2. errno 사전 — 이름이 같아도 호출이 다르면 원인이 다르다

번호와 문자열은 이 노트 작성 환경(리눅스 x86-64, Python `errno`/`os.strerror`)에서 확인한 값이다. 번호는 아키텍처·OS마다 다를 수 있다.

```text
  errno 하나를 보면 먼저 묻는다: "어느 시스템 콜이 돌려줬나?"

      EAGAIN ---+-- read/write/accept (논블로킹 fd)  --> "지금은 없음, 나중에"   (25·26번)
                +-- fork / clone / pthread_create   --> "프로세스·스레드 한도"  (04·07번)
                +-- sem_trywait                     --> "permit 없음"          (18번)

      ENOSPC ---+-- write                           --> 블록 부족 / 예약 블록   (22번)
                +-- open(O_CREAT) / mkdir           --> inode 고갈 / htree 한도 (22번)
```

| errno (번호·문자열) | 흔한 호출 | 뜻·흔한 원인 | 첫 명령 | leaf |
|---|---|---|---|---|
| `EINTR` (4, Interrupted system call) | 블로킹 `read`·`accept`·`sem_wait`·`poll`·`epoll_wait`·`nanosleep` | 시그널 핸들러가 블록 중인 호출을 끊음. `SA_RESTART`가 없거나, 재시작되지 않는 호출(signal(7) 목록) | `strace -e trace=signal,<호출>`, `grep Sig /proc/<pid>/status` | [02](../02-system-calls/2-summary.md) · [06](../06-signals/2-summary.md) · [18](../18-semaphores/2-summary.md) · [26](../26-io-multiplexing-epoll/2-summary.md) |
| `EAGAIN` (11, Resource temporarily unavailable) — I/O | 논블로킹 `read`·`write`·`accept` | 지금 읽을 데이터·보낼 공간이 없음. **에러가 아니다**. 무시하고 재호출하면 busy loop, 에러로 닫으면 멀쩡한 연결을 끊는다 | `strace -c`의 `errors` 칸, `strace -e trace=read,write`에 `EAGAIN` 반복 | [25](../25-io-models/2-summary.md) · [26](../26-io-multiplexing-epoll/2-summary.md) |
| `EAGAIN` — 생성 | `fork`·`clone`·`pthread_create` | `RLIMIT_NPROC`, `threads-max`, `pid_max`, cgroup `pids.max`(fork(2), pthread_create(3)). `pthread_create`는 스레드 스택을 못 받은 `ENOMEM`도 `EAGAIN`으로 바꿔 돌려준다(glibc `nptl/pthread_create.c`, 13번). 좀비·스레드 누수가 흔한 뿌리 | `ps -eLf \| wc -l`, `ulimit -u`, `cat pids.current pids.max` | [04](../04-process-and-lifecycle/2-summary.md) · [05](../05-fork-exec-wait/2-summary.md) · [07](../07-threads-and-context-switch/2-summary.md) · [13](../13-oom-and-memory-limits/2-summary.md) · [28](../28-containers-namespaces-cgroups/2-summary.md) |
| `EMFILE` (24, Too many open files) | `open`·`socket`·`accept`·`pipe` | 프로세스 fd 한도(`RLIMIT_NOFILE`) 도달. 대개 fd 누수 | `ls /proc/<pid>/fd \| wc -l`, `grep 'open files' /proc/<pid>/limits`, `lsof -p` | [21](../21-files-and-descriptors/2-summary.md) |
| `ENFILE` (23, Too many open files in system) | 같음 | 시스템 전체 한도(`/proc/sys/fs/file-max`, errno(3)) | `cat /proc/sys/fs/file-nr` | [21](../21-files-and-descriptors/2-summary.md) |
| `ENOSPC` (28, No space left on device) | `write`·`open(O_CREAT)`·`mkdir` | 블록 고갈, **inode 고갈**(`df`는 여유), 일반 사용자만 예약 블록에 막힘, 지운 파일을 누가 열고 있음, ext4 `index full` | `df -h`, `df -i`, `lsof -nP +L1`, `dmesg \| grep -i 'index full'` | [22](../22-file-system-implementation/2-summary.md) · [21](../21-files-and-descriptors/2-summary.md) |
| `ENOMEM` (12, Cannot allocate memory) | `mmap`·`malloc`·`fork` | 할당 **시점**의 거절: `RLIMIT_AS`, overcommit 모드 2의 `CommitLimit`, 모드 0의 과도한 단일 요청, `fork`의 커널 구조 할당 실패. OOM kill과 다른 길이다 | `ulimit -a`, `grep -i commit /proc/meminfo`, `sysctl vm.overcommit_memory` | [13](../13-oom-and-memory-limits/2-summary.md) · [05](../05-fork-exec-wait/2-summary.md) |
| `EIO` (5, Input/output error) | `fsync`·`read`·`write` | 장치 오류가 보고됨. **fsync의 EIO 뒤 재시도 성공은 데이터가 안전하다는 뜻이 아니다** | `dmesg`의 블록 장치 오류, `smartctl`, `/proc/mdstat` | [24](../24-fsync-and-durability/2-summary.md) · [32](../32-raid/2-summary.md) · [33](../33-data-integrity-checksums/2-summary.md) |
| `EROFS` (30, Read-only file system) | 모든 쓰기 | ext4가 오류를 감지하고 `errors=remount-ro`로 읽기 전용 재마운트 | `dmesg \| grep -E 'EXT4-fs error\|Remounting'`, `findmnt` | [23](../23-crash-consistency-and-journaling/2-summary.md) |
| `EPIPE` (32, Broken pipe) | `write`·`send` | 읽는 쪽이 닫힌 파이프·소켓. SIGPIPE를 무시·차단하거나 핸들러로 잡은 프로세스, `send`에 `MSG_NOSIGNAL`을 준 경우에만 이 errno를 본다. 기본 동작이면 141로 죽는다(write(2), send(2)) | `strace -e trace=write,signal` | [06](../06-signals/2-summary.md) · [30](../30-ipc/2-summary.md) |
| `ENOENT` (2) — `execve` | `execve` | 파일은 있는데 ELF 로더(`PT_INTERP`)가 없음. 셸은 "not found"로 보여 준다 | `file ./app`, `readelf -l ./app \| grep interp` | [29](../29-linking-and-loading/2-summary.md) |
| `EPERM` (1, Operation not permitted) — `io_uring_setup` | `io_uring_setup` | Docker 25.0+ 기본 seccomp, `kernel.io_uring_disabled` | `strace -e trace=io_uring_setup` | [34](../34-zero-copy-and-io-uring/2-summary.md) |
| `EDEADLK` (35) | `pthread_mutex_lock` | `PTHREAD_MUTEX_ERRORCHECK` 뮤텍스를 같은 스레드가 다시 잠금 | 코어 `thread apply all bt` | [19](../19-deadlock/2-summary.md) |

- errno(3): `EMFILE`은 흔히 `RLIMIT_NOFILE` 초과, `ENFILE`은 리눅스에서 `file-max` 한도, `EAGAIN`은 `EWOULDBLOCK`과 같은 값일 수 있다.
- 이 노트 작성 환경에서 `RLIMIT_NOFILE`을 16으로 낮춰 `EMFILE`, 빈 논블로킹 파이프 `read`로 `EAGAIN`, `SA_RESTART` 없는 `SIGALRM` 핸들러로 블로킹 `read`의 `EINTR`을 재현했다.

**런타임에서 보이는 이름** (각 leaf가 확인한 것만)

| errno | Java | Node |
|---|---|---|
| `EMFILE` | 파일: `FileNotFoundException: ... (Too many open files)`(21번, JDK 21) | `Error: EMFILE: too many open files`(21번) |
| `ENOSPC` | 여는 단계 `FileNotFoundException: <경로> (No space left on device)`, 쓰는 단계 `IOException: No space left on device`(22번) | `ENOSPC: no space left on device`(22번) |
| `EAGAIN`(스레드 생성) | `OutOfMemoryError: unable to create native thread: possibly out of memory or process/resource limits reached`(현재 JDK), JDK 8은 `unable to create new native thread`(07번) | — |
| `EPIPE` | HotSpot은 SIGPIPE에 아무것도 안 하는 핸들러를 건다. 효과는 무시와 같아 `IOException: Broken pipe`로 받는다(06번) | 시작 때 SIGPIPE를 `SIG_IGN`으로 둔다. `EPIPE` 에러 이벤트(06번) |

- 괄호 속 문자열은 errno의 strerror 문자열이다. 그래서 Java 예외 **클래스**보다 **메시지 끝**이 원인을 더 잘 말한다.
- Node는 시스템 에러의 errno 이름을 `err.code`에 그대로 싣는다(network/52번).

### 3. 로그 한 줄 사전 — 커널·libc·런타임이 남기는 문자열

| 보이는 줄 | 어디서 | 뜻 | leaf |
|---|---|---|---|
| `Out of memory: Killed process <pid> (<이름>) ...` | 커널 로그(`mm/oom_kill.c`) | 노드 전체 OOM. 원인 제공자가 아니라 **badness 점수**(메모리 사용량 + `oom_score_adj` 보정)가 가장 높은 프로세스가 죽는다. `-1000`은 제외. `vm.oom_kill_allocating_task=1`이면 할당한 태스크가 죽는다(`Out of memory (oom_kill_allocating_task)`) | [13](../13-oom-and-memory-limits/2-summary.md) |
| `Memory cgroup out of memory: Killed process ...` | 커널 로그 | cgroup `memory.max` 도달. 쿠버네티스 `OOMKilled` | [13](../13-oom-and-memory-limits/2-summary.md) · [28](../28-containers-namespaces-cgroups/2-summary.md) |
| `Killed` | bash | 자식이 SIGKILL로 죽었다(누가 보냈는지는 모름) | [06](../06-signals/2-summary.md) · [13](../13-oom-and-memory-limits/2-summary.md) |
| `INFO: task <comm>:<pid> blocked for more than N seconds.` | 커널 hung task 감지(`kernel/hung_task.c`) | `D` 상태가 N초(기본 120, `DEFAULT_HUNG_TASK_TIMEOUT`) 넘게 스케줄되지 않음. 리눅스 7.1부터는 I/O 대기면 `blocked in I/O wait`로 찍힌다(7.0까지는 구분 없이 `blocked`) | [04](../04-process-and-lifecycle/2-summary.md) · [31](../31-os-observability-tools/2-summary.md) |
| `page allocation failure: order:N` | 커널 로그 | 빈 메모리는 있어도 2^N 연속 페이지가 없음(buddy 단편화) | [11](../11-heap-allocation/2-summary.md) |
| `EXT4-fs error ...` → `Aborting journal` → `Remounting filesystem read-only` | 커널 로그 | 디스크 I/O 오류·메타데이터 손상 감지 → 읽기 전용 | [23](../23-crash-consistency-and-journaling/2-summary.md) |
| `Directory (ino: N) index full, reach max htree level :2` | 커널 로그(ext4) | 한 디렉터리에 파일이 너무 많음(`large_dir` 없음). `df -i`는 여유인데 `ENOSPC` | [22](../22-file-system-implementation/2-summary.md) |
| `csum failed root ... mirror N` / `page verification failed, calculated checksum` | btrfs / PostgreSQL | 조용한 손상을 체크섬이 잡음. 첫 신호는 대개 디스크 열화 | [33](../33-data-integrity-checksums/2-summary.md) · [23](../23-crash-consistency-and-journaling/2-summary.md) |
| `free(): double free detected in tcache 2` / `malloc(): corrupted top size` | glibc | 힙 오용 감지 → `abort` → 134 | [11](../11-heap-allocation/2-summary.md) |
| `*** bit out of range 0 - FD_SETSIZE on fd_set ***: terminated` | glibc `_FORTIFY_SOURCE` | `select`에 1024 이상 fd → 134 | [26](../26-io-multiplexing-epoll/2-summary.md) |
| `hs_err_pid<pid>.log` 파일 생성 | HotSpot | JNI·네이티브 라이브러리의 메모리 오류 → 134 | [09](../09-address-space/2-summary.md) |
| `error while loading shared libraries: libfoo.so.1` / `version 'GLIBC_2.34' not found` | 동적 로더 | 라이브러리 탐색 실패 / 빌드한 glibc가 실행하는 glibc보다 새것 | [29](../29-linking-and-loading/2-summary.md) |
| `fork: retry: Resource temporarily unavailable` | bash | `fork`가 `EAGAIN`: 프로세스 한도(좀비·스레드 누수) | [04](../04-process-and-lifecycle/2-summary.md) · [05](../05-fork-exec-wait/2-summary.md) |
| `Found one Java-level deadlock:` | `jstack` | monitor·ownable synchronizer 사이클. 세마포어·래치 사이클은 여기 안 나온다 | [19](../19-deadlock/2-summary.md) · [18](../18-semaphores/2-summary.md) |
| `ERROR 1213 (40001): Deadlock found` / `ERROR: deadlock detected` | MySQL / PostgreSQL | DB가 교착을 탐지해 한쪽을 롤백 → 재시도 대상 | [19](../19-deadlock/2-summary.md) |
| `could not fsync file "...": Input/output error` (PANIC) | PostgreSQL | fsync `EIO`를 재시도로 덮지 않고 멈춤(fsyncgate 이후 동작) | [24](../24-fsync-and-durability/2-summary.md) · [38](../38-os-incidents/2-summary.md) |

### 4. 프로세스 상태 사전 — `ps`의 한 글자

```text
  ps STAT   뜻                                    load에 들어가나   흔한 증상                      leaf
  R         실행 중 또는 실행 큐 대기               예                CPU 포화, 스핀, 라이브락        08, 16, 20
  S         시그널로 깰 수 있는 대기                아니오            교착·lost wakeup(CPU 0%)       17, 19
  D         시그널로 안 깨는 대기 (대개 I/O)         예                load 높고 CPU 한가, kill -9 무효  04, 03, 31
  T / t     작업 제어로 멈춤 / 디버거가 멈춤          아니오            SIGSTOP·ptrace 붙은 채 방치      06
  Z         끝났지만 부모가 회수 안 함 (<defunct>)    아니오            PID 고갈 -> fork EAGAIN         04, 05, 06
  I         놀고 있는 커널 스레드 (TASK_IDLE)         아니오            정상                          04
```

- load average는 R과 D의 수를 1·5·15분 평균한 값이다(proc_loadavg(5)). **CPU 사용률이 아니다.**
- `vmstat`의 `b`는 `procs_blocked`(= `nr_iowait()`)라 I/O 대기 D만 센다. `b`가 0이어도 D가 없다는 뜻이 아니다(04·31번).
- `D`도 둘로 나뉜다. `TASK_KILLABLE`로 잠든 D는 치명적 시그널에 깬다(04번). hung task 감지기는 이 D와 `TASK_NOLOAD`를 건너뛴다(`kernel/hung_task.c` `task_is_hung`).
- **좀비 자체는 `kill -9`로 없어지지 않는다.** 이미 죽어 있다. 부모를 고치거나 부모를 끝내 init·subreaper가 회수하게 한다(04번).
- 이 노트 작성 환경에서 `_exit`한 자식을 회수하지 않은 부모 아래 `Z`, `waitpid` 뒤 사라짐을 확인했다.

### 5. 지표 패턴 사전 — 에러는 없는데 숫자가 이상하다

| 패턴 | 먼저 의심 | 첫 명령 | leaf |
|---|---|---|---|
| load ≫ 코어 수, CPU `id` 높음 | D 상태 누적(느린 디스크·끊긴 NFS·major fault 폭주) | `ps -eo stat,wchan:30,comm \| awk '$1 ~ /^D/'`, `iostat -x`, PSI io | [04](../04-process-and-lifecycle/2-summary.md) · [31](../31-os-observability-tools/2-summary.md) · [03](../03-interrupts-traps-faults/2-summary.md) |
| `sy` > `us`, 앱 프로파일에 뜨거운 함수 없음 | 작은 시스템 콜 반복, 폴트 폭주, futex 경합, `EAGAIN` busy loop | `strace -c`(짧게), `pidstat -r` | [01](../01-kernel-and-user-mode/2-summary.md) · [02](../02-system-calls/2-summary.md) · [25](../25-io-models/2-summary.md) |
| `cs` 폭증, `r` ≫ 코어 수 | 스레드 과다, 락 경합 | `pidstat -w -t` | [07](../07-threads-and-context-switch/2-summary.md) · [16](../16-locks-and-spinlocks/2-summary.md) · [36](../36-server-concurrency-architectures/2-summary.md) |
| CPU는 limit의 일부인데 p99가 100 ms 단위로 튐 | cgroup CPU quota throttling(`cpu.max`) | `cpu.stat`의 `nr_throttled`·`throttled_usec` | [08](../08-cpu-scheduling/2-summary.md) · [28](../28-containers-namespaces-cgroups/2-summary.md) |
| 평균 CPU 10%인데 처리량 한계 | 한 코어만 100%(이벤트 루프·단일 스레드·IRQ 한 코어) | `mpstat -P ALL 1`, `top -H` | [08](../08-cpu-scheduling/2-summary.md) · [27](../27-event-based-concurrency/2-summary.md) · [03](../03-interrupts-traps-faults/2-summary.md) |
| CPU 100%인데 진행 0 | 스핀락 선점, 라이브락, `EAGAIN`·`read`=0 무시 루프, LT의 상시 `EPOLLOUT` | `strace`에 같은 호출 반복, `ps -L`의 R | [16](../16-locks-and-spinlocks/2-summary.md) · [20](../20-concurrency-bugs/2-summary.md) · [25](../25-io-models/2-summary.md) · [26](../26-io-multiplexing-epoll/2-summary.md) |
| CPU 0%, 응답 없음, 프로세스는 살아 있음 | 교착, lost wakeup, 세마포어 permit 누수, 파이프 가득 교착 | 스레드 덤프, `ps -L -o stat,wchan`, `gdb thread apply all bt` | [19](../19-deadlock/2-summary.md) · [17](../17-condition-variables-and-monitors/2-summary.md) · [18](../18-semaphores/2-summary.md) · [30](../30-ipc/2-summary.md) |
| `si`·`so` 계속 높음, 모두 느림 | 스래싱(작업 집합 > RAM) | `vmstat 1`, `/proc/pressure/memory` | [12](../12-swapping-and-page-replacement/2-summary.md) |
| `majflt/s` 급증, D 상태 | 캐시가 비었거나 스왑 | `pidstat -r`, `/proc/vmstat`의 `pgmajfault` | [03](../03-interrupts-traps-faults/2-summary.md) · [12](../12-swapping-and-page-replacement/2-summary.md) |
| `write`가 가끔 수 초 멈춤, `Dirty`·`Writeback` 큼 | dirty가 한도 근처 → `balance_dirty_pages`가 쓰는 프로세스를 재워 속도를 맞춤(`(background + dirty_ratio)/2`부터, 14번) | `grep -E 'Dirty\|Writeback' /proc/meminfo` | [14](../14-mmap-and-page-cache/2-summary.md) |
| `free`의 free 작고 `buff/cache` 큼 | 정상(페이지 캐시). `available`을 본다 | `free -m`, `memory.stat`의 `anon`·`file` | [14](../14-mmap-and-page-cache/2-summary.md) |
| VSZ 수 GB, RSS 작음 | 스레드 스택 등 가상 예약. 누수 아님 | `/proc/<pid>/smaps_rollup` | [07](../07-threads-and-context-switch/2-summary.md) · [09](../09-address-space/2-summary.md) |
| RSS가 피크 뒤 안 줄어듦(계단식) | 힙 단편화·arena 여유(누수와 구분) | `pmap -x`, 추세가 멈추나 계속 오르나 | [11](../11-heap-allocation/2-summary.md) |
| `%steal` 상승 | 이웃 VM·vCPU 과할당·크레딧 소진 | `mpstat`, `vmstat`의 `st` | [35](../35-virtualization-hypervisor/2-summary.md) |
| `%util` 100%인데 `await` 낮음 | 병렬 장치(NVMe)에서 `%util`은 포화가 아님 | `iostat -x`의 `await`·`aqu-sz` | [31](../31-os-observability-tools/2-summary.md) |
| `df`는 줄지 않는데 `rm`은 했다 | 지운 파일을 누가 열고 있음 | `lsof -nP +L1` | [21](../21-files-and-descriptors/2-summary.md) |
| `mismatch_cnt` > 0 | RAID5/6면 하드웨어 신호, RAID1/10은 소프트웨어 동작으로도 | SMART, 커널 로그 | [32](../32-raid/2-summary.md) · [33](../33-data-integrity-checksums/2-summary.md) |

### 6. 조용한 실패 — 에러도 지표도 없는 증상

| 증상 | 흔한 원인 | 첫 확인 | leaf |
|---|---|---|---|
| 카운터 합계가 로그 건수보다 적음, 재고 음수 | 원자성 위반(`count++`, check-then-act) | 동시성 테스트, TSan | [15](../15-race-conditions/2-summary.md) · [20](../20-concurrency-bugs/2-summary.md) |
| 재부팅 뒤 설정 파일이 0바이트 | fsync 없는 교체 + 지연 할당 | 쓰기 패턴(`strace -e trace=openat,write,fsync,rename`) | [23](../23-crash-consistency-and-journaling/2-summary.md) · [24](../24-fsync-and-durability/2-summary.md) |
| 전원 차단 뒤 파일이 **예전 버전** | rename 뒤 디렉터리 fsync 누락 | 같은 strace | [24](../24-fsync-and-durability/2-summary.md) |
| 며칠 뒤 옛 값·빠진 데이터, 당시 fsync 실패 1회 | fsync `EIO` 뒤 재시도 성공을 믿음 | 당시 `dmesg` | [24](../24-fsync-and-durability/2-summary.md) |
| 받는 쪽 메시지 끝이 잘림 | 짧은 쓰기·`sendfile` 부분 전송 무시 | 반환값 처리 코드 | [02](../02-system-calls/2-summary.md) · [34](../34-zero-copy-and-io-uring/2-summary.md) |
| 해제 후 사용인데 안 죽음 | VMA가 남아 있으면 커널은 모름 | ASan | [09](../09-address-space/2-summary.md) · [11](../11-heap-allocation/2-summary.md) |
| 복제·백업까지 똑같이 깨짐 | 데이터 체크섬 없는 층의 비트 부패 | 앱·파일 시스템 체크섬, 스크럽 | [33](../33-data-integrity-checksums/2-summary.md) |
| 재구축은 성공, 파일은 깨짐 | RAID5 write hole | 체크섬 오류가 뒤늦게 | [32](../32-raid/2-summary.md) |
| 에러 로그 없는 워치독 리셋·마감 초과, 특정 부하 조합에서만 | 우선순위 역전(상속 없는 락, Mars Pathfinder) | 트레이스로 "높은 작업이 락 대기 → 락 주인은 실행 대기" 확인, 락이 PI 뮤텍스인가 | [20](../20-concurrency-bugs/2-summary.md) · [38](../38-os-incidents/2-summary.md) |

## 쓰이는 자료구조·알고리즘

- **역색인(inverted index)** — 이 노트 자체다. 정방향 "leaf → 증상 목록"을 뒤집어 "증상 → leaf 목록"으로 만든다. 검색 엔진이 "문서 → 단어"를 "단어 → 문서 목록"으로 뒤집는 것과 같다. [data-structure/32-inverted-index](../../data-structure/32-inverted-index/2-summary.md)
- **해시 맵** — 증상 이름(`EMFILE`, `137`)을 키로 후보 목록을 찾는다. 로그 수집기의 "에러 코드별 집계"도 같은 구조다. [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- **결정 트리** — 한 증상에 후보가 여럿이면 질문 몇 개로 가른다. "어느 시스템 콜이었나", "누가 시그널을 보냈나", "load의 몫이 R인가 D인가". 위 §2의 `EAGAIN`·`ENOSPC` 그림이 결정 트리다.
- **USE 체크리스트** — 자원마다 사용률·포화·에러를 본다. 증상이 없는 자원을 지워 나가는 소거법이다([31](../31-os-observability-tools/2-summary.md)).

```c
/* 종료 상태를 사람이 읽을 말로 — 셸의 128+N과 커널의 wait 상태를 구분한다 (05번) */
#include <signal.h>
#include <stdio.h>
#include <string.h>
#include <sys/wait.h>

void describe(int st) {
    if (WIFEXITED(st))
        printf("exit %d%s\n", WEXITSTATUS(st),
               WEXITSTATUS(st) > 128 ? " (JVM처럼 스스로 128+N으로 끝냈을 수 있음)" : "");
    else if (WIFSIGNALED(st))
        printf("signal %d (%s)%s -> 셸에서는 %d\n", WTERMSIG(st), strsignal(WTERMSIG(st)),
               WCOREDUMP(st) ? ", core" : "", 128 + WTERMSIG(st));
}
```

```java
// Java에서 자식 종료를 해석할 때 — waitFor()는 시그널 종료를 0x80 + N으로 준다 (OpenJDK 구현)
int code = process.waitFor();
String why = switch (code) {
    case 137 -> "SIGKILL: OOM kill? 유예 후 강제 종료? kill -9? (커널 로그·memory.events로 가른다)";
    case 143 -> "SIGTERM: 정상 종료 요청";
    case 139 -> "SIGSEGV: 네이티브 메모리 오류";
    case 134 -> "SIGABRT: abort() — glibc 검사 실패·JVM 치명 오류";
    default  -> code > 128 ? "signal " + (code - 128) : "exit " + code;
};
```

## 적용 — 풀어나가는 법

### 1. 원문을 잃지 않게 기록한다

- 종료는 **코드와 시그널을 따로** 남긴다. Node는 `(code, signal)`을 그대로, C는 `WIFSIGNALED`·`WTERMSIG`를 남긴다.
- 에러는 **errno 이름과 어느 호출이었나**를 남긴다. 메시지만 남기면 호출이 빠진다.
- 커널 로그는 권한이 있을 때 같이 모은다. 이 노트 작성 환경은 `dmesg_restrict=1`이라 일반 사용자는 `dmesg`를 못 읽었다(09번). 노드 로그 수집기가 필요한 이유다.

```js
// Node — 자식 종료와 시스템 에러를 원문 그대로
child.on('exit', (code, signal) => log.warn({ code, signal }, 'child exited'));   // (null, 'SIGKILL')
fs.open(path, 'r', (err) => { if (err) log.warn({ code: err.code, syscall: err.syscall, path }, 'open failed'); });
```

### 2. 모양으로 1차 분류한다

```text
  모양                             대개 뜻하는 것                                가 볼 곳
  ------------------------------   ------------------------------------------   ----------------
  시작 직후 즉시 종료                로더·라이브러리·CPU 명령·권한                   29, 01
  특정 입력에서 즉시 종료            메모리 오류 (139·134·135)                       09, 11, 14
  부하 때 재시작, 로그가 중간에 끊김   SIGKILL (137) — OOM 또는 유예 초과               13, 28, 06
  몇 시간·며칠 뒤 생성 실패           누수가 한도에 닿음 (fd, 좀비, 스레드)             21, 04, 07
  주기적 지연 스파이크                quota period, GC, dirty writeback, 타이머        08, 28, 14
  CPU 100% + 진행 0                  헛도는 루프                                    16, 20, 25, 26
  CPU 0% + 응답 없음                  모두 잠듦 (교착·lost wakeup·permit 누수)         19, 17, 18
  크래시 뒤에만 드러남                내구성 순서 (fsync·rename·디렉터리)             23, 24
```

### 3. 첫 명령 세트

```bash
# 종료 원인: 누가 SIGKILL을 보냈나
kubectl describe pod <pod> | grep -A3 'Last State'          # Reason, Exit Code
cat /sys/fs/cgroup/<그룹>/memory.events                        # oom_kill 카운트
journalctl -k | grep -iE 'killed process|out of memory'       # 권한 필요

# errno: 어느 호출이 무엇을 돌려줬나 (운영에서는 짧게, 02·31번)
timeout 5 strace -f -c -p <pid>
timeout 5 strace -f -e trace=openat,read,write,fsync -p <pid> 2>&1 | grep -E 'E[A-Z]+ '

# 상태: load의 몫이 R인가 D인가
vmstat 1 5                                                    # 첫 줄은 부팅 이후 평균이라 버린다
ps -eLo stat,pid,tid,wchan:32,comm | awk '$1 ~ /^[DZ]/'
cat /proc/pressure/{cpu,memory,io}

# 한도: fd·프로세스·메모리
ls /proc/<pid>/fd | wc -l; grep -E 'open files|processes' /proc/<pid>/limits
cat /sys/fs/cgroup/<그룹>/{pids.current,pids.max,cpu.stat}
df -h; df -i; lsof -nP +L1
```

- 명령별 상세와 도구 오버헤드는 [31-os-observability-tools](../31-os-observability-tools/2-summary.md)가 모은다.

### 4. leaf로 간다

- 위 §1~§6 표에서 후보 leaf를 고른다. 후보가 여럿이면 각 leaf의 「장애 시나리오」 "보이는 형태"와 내 관찰을 대조해 지운다.
- 후보가 하나도 맞지 않으면 USE로 자원을 하나씩 확인한다([31](../31-os-observability-tools/2-summary.md)).
- 네트워크 errno(`ECONNRESET`·`ETIMEDOUT` 등)는 [network/52-network-symptom-index](../../network/52-network-symptom-index/2-summary.md)로 간다.

## 장애 시나리오와 대처

### 1. load average를 CPU 포화로 읽는다 — 실제는 D 상태 누적

- **현상**: 8코어 서버의 load가 30이다. CPU를 16코어로 늘렸는데 load도 지연도 그대로다.
- **보이는 형태**
  - `vmstat`의 `id`가 70%대이고 `r`은 작다.
  - `ps`에 `D` 상태가 여럿이고, `wchan`이 파일 시스템·블록 I/O 대기 함수다.
  - 커널 로그에 `INFO: task ... blocked for more than 120 seconds.`가 찍히기도 한다.
- **원인**
  - 리눅스 load는 R과 **D**를 센다(proc_loadavg(5)). 느린 디스크·끊긴 NFS·major fault 폭주가 D를 쌓았다.
  - "load = CPU 사용률"로 읽어 CPU를 늘렸다. 기다리는 자원이 CPU가 아니었다.
- **대처**
  - load를 볼 때 `r`(실행 대기)과 D를 나눠 본다. CPU 판단은 `r`·`mpstat`·PSI cpu로 한다([31](../31-os-observability-tools/2-summary.md)).
  - D의 `wchan`과 관련 마운트·장치를 따라간다([04](../04-process-and-lifecycle/2-summary.md), [03](../03-interrupts-traps-faults/2-summary.md)).
  - 반대 방향 함정도 있다. 모든 스레드가 `S`인 교착은 load에 **잡히지 않는다**([19](../19-deadlock/2-summary.md)). "load가 낮으니 멀쩡하다"도 성립하지 않는다.

### 2. `free`의 "used"·낮은 "free"를 메모리 누수로 읽는다

- **현상**: 메모리 그래프가 며칠째 올라 90%에서 멈춘다. 누수로 보고 재시작했는데 또 오른다.
- **보이는 형태**: `free`의 `free`는 작고 `buff/cache`가 크다. `available`은 넉넉하다. 스왑·OOM이 없다.
- **원인**
  - 페이지 캐시가 빈 메모리를 채웠다. 커널은 필요하면 회수한다([14](../14-mmap-and-page-cache/2-summary.md)).
  - 비슷한 오판: 스레드 많은 JVM의 VSZ가 수 GB라 "누수"로 보는 경우([07](../07-threads-and-context-switch/2-summary.md)). 피크 뒤 RSS가 안 줄어 "누수"로 보는 경우는 단편화일 수 있다([11](../11-heap-allocation/2-summary.md)).
- **대처**
  - 판단 지표를 `MemAvailable`, 컨테이너면 `memory.stat`의 `anon`으로 바꾼다.
  - 누수와 단편화는 **추세**로 가른다. 단편화는 일정 수준에서 멈추고, 누수는 계속 오른다(11번).
  - `drop_caches`로 "치우는" 것은 진단 실험일 뿐 해결책이 아니다.

### 3. exit 137을 "앱이 크래시했다"로 읽는다

- **현상**: 파드가 재시작한다. 개발팀은 앱 로그에서 예외를 찾는데 아무것도 없다. 로그가 중간에 뚝 끊겨 있다.
- **보이는 형태**
  - `Exit Code: 137`. `Reason`이 `OOMKilled`일 수도, 아닐 수도 있다.
  - 셸에서 돌렸다면 `Killed` 한 줄.
- **원인**
  - 137은 128 + 9(SIGKILL)다. SIGKILL은 잡을 수 없어 앱은 로그를 남길 기회가 없다. **앱이 스스로 죽은 게 아니다.**
  - 보낸 쪽 후보가 셋이다.
    - cgroup OOM killer: `memory.events`의 `oom_kill` 증가, `Memory cgroup out of memory: Killed process`([13](../13-oom-and-memory-limits/2-summary.md), [28](../28-containers-namespaces-cgroups/2-summary.md)).
    - 유예 시간 초과: SIGTERM을 못 받거나 무시해 유예(쿠버네티스 기본 30초, Docker 기본 10초) 뒤 SIGKILL. 종료에 늘 그 시간이 걸린다([06](../06-signals/2-summary.md), [28](../28-containers-namespaces-cgroups/2-summary.md)).
    - 사람·스크립트의 `kill -9`.
- **대처**
  - 137을 보면 먼저 **누가 보냈나**를 가른다. Reason, `memory.events`, 커널 로그, 종료에 걸린 시간 순서로 본다.
  - OOM이면 힙만이 아니라 native·메타스페이스·스레드 스택까지 합쳐 한도를 잡는다(13번).
  - 유예 초과면 PID 1과 SIGTERM 핸들러를 고친다(06·28번).
  - 비슷한 오판: 139를 "JVM 버그"로, 141을 "원인 모를 사망"으로 읽는 것. 139는 네이티브 메모리 오류(09번), 141은 닫힌 파이프에 쓰기(06·30번)다.

### 4. `OutOfMemoryError: unable to create native thread`를 힙 부족으로 읽는다

- **현상**: 새 스레드를 만들다 실패한다. 담당자가 `-Xmx`를 늘렸는데 같은 에러가 계속 난다.
- **보이는 형태**
  - `java.lang.OutOfMemoryError: unable to create native thread: possibly out of memory or process/resource limits reached`.
  - 네이티브라면 `pthread_create` = `EAGAIN`, 셸이라면 `fork: retry: Resource temporarily unavailable`.
- **원인**
  - 이름과 달리 힙이 아니다. `pthread_create`의 `EAGAIN`이다(pthread_create(3)). `RLIMIT_NPROC`(실사용자 ID 단위 합산), `threads-max`, `pid_max`, cgroup `pids.max` 중 하나에 닿았다([07](../07-threads-and-context-switch/2-summary.md), [04](../04-process-and-lifecycle/2-summary.md)).
  - "OutOfMemoryError"라는 클래스 이름 때문에 힙 문제로 읽었다. 힙 크기는 이 개수 한도들과 무관하다. 07번은 스레드 스택 등을 확보할 메모리 부족도 원인으로 든다. 이때도 부족한 것은 힙이 아니라 native 메모리다. glibc는 이 경우의 `ENOMEM`도 `EAGAIN`으로 바꿔 돌려주므로 errno만으로는 둘을 가를 수 없다([13](../13-oom-and-memory-limits/2-summary.md)).
- **대처**
  - `jstack`으로 스레드 수·이름을 세어 누수 풀을 찾는다. 좀비가 PID를 쥐고 있지 않은지 본다(04·05번).
  - `ulimit -u`, `pids.current`/`pids.max`, `threads-max`를 비교한다.
  - 연결당 스레드 구조면 구조를 바꾼다([36](../36-server-concurrency-architectures/2-summary.md)).

### 5. `ENOSPC`인데 `df`는 여유 — "디스크 가득 오보"로 닫는다

- **현상**: 파일 생성이 `No space left on device`로 실패한다. 담당자가 `df -h`를 보고 "여유 40%, 오보"라고 닫는다. 실패는 계속된다.
- **보이는 형태**: 쓰기 실패 로그. `df -h`의 Use%는 여유. 기존 파일에 덧붙이기는 되기도 한다.
- **원인** — `ENOSPC`는 "블록이 없다"만 뜻하지 않는다.
  - inode 고갈: `df -i`가 100%([22](../22-file-system-implementation/2-summary.md)).
  - 한 디렉터리의 htree 한도: 커널 로그 `index full`(22번).
  - 디렉터리 크기 제한: `max_dir_size_kb` 마운트 옵션에 닿은 디렉터리는 `ENOSPC`를 낸다(22번, fs/ext4/namei.c `ext4_append`).
  - 헷갈리기 쉬운 것: 예약 블록에 막힌 경우는 이 모양이 아니다. 일반 사용자 기준 가용 공간이 0이라 `df`의 Use%도 100% 근처다(22번 시나리오 3).
  - 반대로 `df`가 가득인데 `du` 합이 작다면 지운 파일을 누가 열고 있다(`lsof +L1`, [21](../21-files-and-descriptors/2-summary.md)).
- **대처**
  - `ENOSPC`를 보면 `df -h`, `df -i`, `lsof -nP +L1`, 커널 로그를 한 세트로 본다.
  - 감시를 블록 사용률 하나에서 inode 사용률까지 넓힌다.

## 핵심 문장

- 이 노트는 **증상 → 층 → 흔한 원인 → 첫 명령 → leaf** 순서의 역색인이다. 고치지 않고 어느 노트로 갈지 정한다.
- 시그널로 죽은 프로세스는 셸에서 **128 + 시그널 번호**로 보인다. 137 = SIGKILL, 139 = SIGSEGV, 143 = SIGTERM, 134 = SIGABRT, 135 = SIGBUS, 141 = SIGPIPE.
- 137은 "누가 보냈나"를 말하지 않는다. OOM kill·유예 후 강제 종료·`kill -9`를 Reason·`memory.events`·커널 로그로 가른다.
- errno는 **어느 호출**이 돌려줬는지와 함께 읽는다. `read`의 `EAGAIN`은 정상 흐름이고 `fork`의 `EAGAIN`은 한도 도달이다.
- load average는 R + D의 수다. load가 높은데 CPU가 한가하면 D 상태(I/O 대기)를 본다. 모두 `S`인 교착은 load에 잡히지 않는다.
- 에러가 없는 증상(합계 불일치, 0바이트 파일, fsync 재시도 성공)이 가장 비싸다. 원자성·내구성 순서 leaf로 간다.

## 관련 주제·근거

- 선행: 운영체제 영역 전체. 특히
  - [04-process-and-lifecycle](../04-process-and-lifecycle/2-summary.md) — 프로세스 상태, 좀비, D와 load
  - [05-fork-exec-wait](../05-fork-exec-wait/2-summary.md) · [06-signals](../06-signals/2-summary.md) — wait 상태, 128+N, JDK·Node 동작
  - [31-os-observability-tools](../31-os-observability-tools/2-summary.md) — 첫 명령들의 상세, USE
- 이 노트가 가리키는 leaf: 위 §1~§6 표의 링크 전부. 영역 표는 [../README.md](../README.md).
- 후속·연결
  - [38-os-incidents](../38-os-incidents/2-summary.md) — 실사건에서 이 증상들이 어떻게 나타났나
  - [network/52-network-symptom-index](../../network/52-network-symptom-index/2-summary.md) — 네트워크 errno·예외·5xx 색인
- Linux man-pages
  - errno(3) — 이름·문자열, `EMFILE`(RLIMIT_NOFILE)·`ENFILE`(file-max)·`EAGAIN`/`EWOULDBLOCK` <https://man7.org/linux/man-pages/man3/errno.3.html>
  - fork(2) — `EAGAIN`(RLIMIT_NPROC·threads-max·pid_max·pids.max)·`ENOMEM` · pthread_create(3) — `EAGAIN` · write(2) — `EPIPE`는 SIGPIPE를 잡거나 막거나 무시할 때만 보임 · glibc `nptl/pthread_create.c` — `ENOMEM`을 `EAGAIN`으로 변환
  - signal(7) — 기본 동작, `SA_RESTART`와 재시작되지 않는 호출 · wait(2) — `WIFSIGNALED`·`WTERMSIG`
  - proc_loadavg(5) — load = R + D · ps(1) PROCESS STATE CODES
  - bash(1) "EXIT STATUS" — 128+N, 126, 127
- 커널 소스
  - `kernel/hung_task.c` — `task_is_hung`(TASK_KILLABLE·TASK_NOLOAD 제외), `"INFO: task %s:%d blocked%s for more than %ld seconds."` <https://github.com/torvalds/linux/blob/master/kernel/hung_task.c> · `in I/O wait` 표기는 커밋 "hung_task: explicitly report I/O wait state in log output"(2026-03), v7.1 태그부터 포함(v7.0에는 없음)
  - `lib/Kconfig.debug` — `DEFAULT_HUNG_TASK_TIMEOUT` 기본 120 (이 노트 작성 환경의 `/proc/sys/kernel/hung_task_timeout_secs`도 120)
  - `mm/oom_kill.c` — `Killed process`, `Memory cgroup out of memory`(13·28번)
- OpenJDK: `ProcessHandleImpl_unix.c` `WTERMSIG_RETURN`(0x80 + 시그널, 05번) · `java/lang/Terminator.java`(SIGTERM → 128+N exit, 06번)
- Node.js `child_process` — `'exit'` 이벤트 `(code, signal)` <https://nodejs.org/api/child_process.html#event-exit>
- 로컬 재현(2026-09-30, 리눅스 7.0.0, bash 5.2.21, Node 18.19, OpenJDK 21.0.12, gcc 13.3)
  - `bash -c 'kill -<SIG> $$'`로 129·132·134·135·136·137·139·141·143과 셸 메시지, `exit 256`→0·`exit -1`→255, 126·127
  - Node 자식 SIGKILL → `(null, 'SIGKILL')`, 핸들러 없는 Node의 SIGTERM → 143
  - Java `waitFor()` → 137·143, JVM 자신의 SIGTERM → bash `Exit 143`
  - C: `RLIMIT_NOFILE`=16에서 `EMFILE`, 빈 논블로킹 파이프 `EAGAIN`, `SA_RESTART` 없는 `SIGALRM`의 `EINTR`, 회수 안 한 자식의 `Z`
