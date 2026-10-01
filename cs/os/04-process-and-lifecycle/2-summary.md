# os/04-process-and-lifecycle — 프로세스라는 추상화, 그 상태와 기록부, 그리고 죽은 뒤의 좀비 — 정리 (힌트)

## 해결하는 문제

기초는 원고 [foundations/process-thread](../../foundations/process-thread/README.md) §1(프로그램과 프로세스)·§2(프로세스의 상태)·§5(컨텍스트 스위칭과 PCB)에 있다.\
요약하면: 프로그램은 디스크의 파일이고, 프로세스는 그것을 **실행 중인 인스턴스**다. OS는 프로세스마다 상태와 CPU 문맥을 PCB에 적어 둔다.

이 노트는 그 위에서 세 가지를 채운다.

```text
  질문                                          이 노트의 답
  리눅스에서 "프로세스 상태"는 실제로 무엇인가?      task_struct의 상태 값과 ps의 R·S·D·T·Z
  PCB는 실제로 어디에 무엇이 있나?                  task_struct, 커널 스택, 연결 리스트들
  프로세스가 끝나면 바로 사라지나?                  아니다 — 부모가 회수할 때까지 좀비로 남는다
```

쉬운 예: 식당 주문표다.
- 주문 하나(프로세스)마다 주문표(PCB)가 있다. "조리 중·대기 중·재료 기다림" 같은 상태가 적힌다.
- 요리가 끝나도 주문표는 바로 버리지 않는다. 계산(부모의 `wait`)이 끝나야 버린다.
- 계산 안 된 주문표가 쌓이면 주문표 꽂이(PID 표)가 꽉 차서 새 주문을 못 받는다.

똑같은 구조다.\
끝난 프로세스는 "종료 상태"를 부모에게 전할 때까지 좀비로 남아 PID를 차지한다.

실무 예:
- 컨테이너에서 `ps`를 치니 `<defunct>`가 수백 개다. 곧 `fork: Resource temporarily unavailable`이 난다.
- load average가 20인데 CPU는 놀고 있다. `D` 상태 프로세스가 쌓였다.
- 배포 스크립트가 끝났는데 옛 워커 프로세스가 PPID 1로 살아 있다.

## 동작·원리

### 상태 전이 — 교과서 모델

OSTEP 4.4의 세 상태에 생성·종료를 더한 것이다.

```text
                       스케줄됨
        생성 -----> Ready ---------> Running -----> 종료(좀비) --wait--> 사라짐
                     ^  <---------    |    exit()
                     |  선점(타이머)    |
                     |                | I/O 시작 (read, 디스크 대기 ...)
                     |  I/O 완료       v
                     +----------- Blocked
```

- Running → Ready: 타이머 인터럽트로 커널이 CPU를 빼앗았다(01번 타이머, 08번 스케줄링).
- Running → Blocked: 스스로 기다릴 일을 시작했다. 이때 CPU를 다른 프로세스에 준다.
- Blocked → Ready: 기다리던 일이 끝났다. **바로 Running이 아니라 Ready**로 간다(원고 §2도 같은 점을 강조한다).
- 종료 → 사라짐 사이에 **좀비** 단계가 있다. OSTEP 4.5도 "final state(좀비)"를 두고, 부모가 `wait()`로 종료 코드를 확인하게 한다고 적는다.

> 용어 주의: 원고 §2는 실행 가능 상태를 "Waiting"이라 부른다. OSTEP 4.4는 같은 상태를 **Ready**라 부른다. 이 노트는 Ready를 쓴다. "Waiting"은 I/O 대기(Blocked)와 헷갈리기 쉽다.
>
> 참고: 원고 §2의 "소멸(Terminated): 프로세스 실행이 완료되어 메인 메모리에서 사라진다"는 절반만 맞다. 리눅스에서 끝난 프로세스는 부모가 회수할 때까지 PID·종료 상태·자원 사용량을 남긴 **좀비**가 된다(wait(2) NOTES). 아래 로컬 재현 참고.

### 리눅스의 실제 상태 — `ps`의 한 글자

```text
  ps STAT   커널 값 (include/linux/sched.h)    교과서 모델      뜻
  R         TASK_RUNNING                        Running + Ready  CPU에서 실행 중이거나 실행 큐에서 대기
  S         TASK_INTERRUPTIBLE                  Blocked          사건 대기, 시그널로 깨울 수 있음
  D         TASK_UNINTERRUPTIBLE                Blocked          대기 중 시그널로 안 깸 (대개 I/O)
  T / t     __TASK_STOPPED / __TASK_TRACED       -               작업 제어로 멈춤 / 디버거가 멈춤
  Z         EXIT_ZOMBIE                         종료(좀비)       끝났지만 부모가 아직 회수 안 함
  X         EXIT_DEAD                           사라짐           회수 중 (거의 안 보임)
  I         TASK_IDLE                           -                놀고 있는 커널 스레드
```

- 문자는 fs/proc/array.c `task_state_array`와 ps(1) "PROCESS STATE CODES"가 정본이다.
- **리눅스는 Running과 Ready를 상태 값으로 구분하지 않는다.** 둘 다 `TASK_RUNNING`(R)이다. "지금 CPU 위인가"는 스케줄러가 따로 안다.
- `D`는 시그널로 깨지 않는다. 그래서 `kill -9`도 대기가 끝날 때까지 효과가 없을 수 있다.
  - 예외: `TASK_KILLABLE`(= `TASK_WAKEKILL | TASK_UNINTERRUPTIBLE`)로 잠든 경우는 치명적 시그널에는 깬다. ps에는 똑같이 `D`로 보인다(sched.h).
- **load average는 R과 D의 수**를 평균한 값이다(proc_loadavg(5)). CPU 사용률이 아니다.
  - 정확히는 R 수 + load에 산입되는 비인터럽트 대기 수다. `D`로 보여도 얼어 있는(`TASK_FROZEN`) 태스크 등은 load에 안 들어간다(kernel/sched/core.c `sched_contributes_to_load`, sched.h `__task_state_index`).

로컬에서 본 상태(예시, 리눅스 7.0):

```text
  sleep 3 &                  -> STAT S   (WCHAN hrtimer_nanosleep, 잠든 곳)
  kill -STOP <pid>           -> STAT T   (WCHAN do_signal_stop)
  kill -CONT <pid>           -> STAT S   (WCHAN do_sys_restart_syscall)
  자식이 _exit, 부모는 wait 안 함 -> STAT Z  (ps에 <defunct>)
```

### PCB = `task_struct`

```text
  task_struct (프로세스·스레드 하나마다 하나)          include/linux/sched.h
  +---------------------------------------------+
  | __state        R/S/D/T ... 상태 값            |
  | pid, tgid      스레드 ID, 프로세스(스레드 그룹) ID |
  | stack   -----> 커널 스택 -----------------------+----> 맨 위: pt_regs (유저 레지스터, 커널 진입 때 저장)
  | thread         CPU 문맥 일부 (커널 sp 등)        |      스위칭 때: callee-saved 레지스터 push
  | se             스케줄러용 엔티티 (08번)          |
  | mm      -----> 주소 공간 (09·10번)              |
  | files   -----> 열린 fd 표 (21번)                |
  | signal  -----> 시그널 공유 정보 (06번)           |
  | real_parent, parent  부모 포인터                |
  | children, sibling    자식 목록 연결             |
  | tasks          모든 프로세스(스레드 그룹 리더)를 잇는 연결 |
  | exit_state, exit_code  좀비일 때 남기는 것       |
  +---------------------------------------------+
```

- 원고 §5·§6은 "PCB에 PC·SP·레지스터를 저장한다"고 설명한다. 리눅스 x86-64에서 실제 위치는 나뉘어 있다.
  - 유저 모드 레지스터는 커널에 들어올 때 **커널 스택 맨 위(`pt_regs`)** 에 저장된다(02번).
  - 문맥 교환 때는 `__switch_to_asm`이 callee-saved 레지스터(rbp·rbx·r12~r15)를 커널 스택에 push하고, 스택 포인터를 `thread.sp`에 저장한다(arch/x86/entry/entry_64.S).
  - 개념상 모두 "그 프로세스의 PCB에 딸린 기록"이다.
- **리눅스 스레드도 `task_struct` 하나씩이다.** 한 프로세스의 스레드들은 `tgid`가 같다. 사용자에게 보이는 PID가 `tgid`다(wait(2) "Linux notes": 스레드는 `clone`으로 만든 프로세스). 07번에서 이어진다.
- `/proc/<pid>/status`에서 이 값 일부를 사람이 읽을 수 있게 보여 준다.

```text
  Name:  sleep
  State: S (sleeping)
  Tgid:  2042375
  Pid:   2042375
  PPid:  2042373
  Threads: 1
  voluntary_ctxt_switches:    1
  nonvoluntary_ctxt_switches: 0            (예시, 로컬)
```

### 생애 — 태어나서 회수될 때까지

```text
  부모: fork()/clone()
        |
        v
  [자식 생성] --> R --> (S/D/R 반복) --> exit(code) 또는 시그널로 죽음
                                            |
                                            v
                                  Z (좀비): 메모리·fd 등은 해제
                                           PID, 종료 상태, 자원 사용량만 남김
                                            |  부모에게 SIGCHLD
                                            v
                         부모가 wait()/waitpid() --> 종료 상태 전달 --> task 해제, PID 반납
```

- 좀비가 남기는 것: PID, 종료 상태, 자원 사용 정보(wait(2) NOTES).
- 예외: 부모가 `SIGCHLD`를 **명시적으로** `SIG_IGN`으로 두거나 `SA_NOCLDWAIT`를 켰으면, 자식은 좀비로 남지 않고 바로 치워진다(wait(2) NOTES). 기본 처분(무시)과는 다르다.
- 좀비는 이미 죽었다. **`kill -9`를 보내도 아무 변화가 없다.** 로컬 재현: `kill()`은 0(성공)을 돌려줬지만 STAT은 계속 Z였다. 부모가 `waitpid`한 뒤에야 사라졌고, 종료 코드 7도 그대로 받았다.
- 좀비가 회수되지 않는 동안 **커널 프로세스 표의 자리**를 하나 차지한다. 가득 차면 새 프로세스를 못 만든다(wait(2) NOTES).

**고아와 입양.**

```text
  할아버지(subreaper 또는 init)
      |
    부모 --X (먼저 종료)
      |
    자식 (살아 있음) ----> 부모가 사라지면 가장 가까운 subreaper, 없으면 init(PID 1)의 자식이 된다
```

- 부모가 먼저 끝나면 자식은 **고아**가 된다. 커널은 고아를 가장 가까운 **subreaper**에게, 없으면 **init**에게 붙인다(wait(2) NOTES, prctl(2) `PR_SET_CHILD_SUBREAPER`).
- init은 입양한 자식이 끝나면 자동으로 `wait`해 좀비를 치운다.
- 로컬 재현: 부모가 끝난 뒤 자식의 PPID가 4106이 됐다. 그 프로세스는 `/usr/lib/systemd/systemd --user`였다. 데스크톱 세션에서는 사용자 systemd가 subreaper 역할을 한다(예시).
  - *subreaper*: 자기 자손 중 고아가 된 프로세스를 대신 입양하겠다고 표시한 프로세스다.

## 쓰이는 자료구조·알고리즘

- **이중 원형 연결 리스트(프로세스 목록)** — 프로세스마다 스레드 그룹 리더의 `task_struct`가 `tasks` 필드로 이어진다(kernel/fork.c `copy_process`). `for_each_process(p)`는 `init_task`에서 출발해 한 바퀴 돈다. 스레드까지 모두 돌려면 `for_each_process_thread`를 쓴다(include/linux/sched/signal.h). 리눅스의 `list_head`는 구조체 안에 링크를 넣는 방식이다. [data-structure/02-linked-list](../../data-structure/02-linked-list/2-summary.md)
- **트리(부모-자식 관계)** — `children`·`sibling` 리스트로 프로세스 트리를 만든다. `pstree`가 보여 주는 모양이다.
- **상태 기계** — `__state` 값이 위의 전이만 허락한다. 좀비에서 R로 돌아가는 길은 없다.
- **ID 할당(IDR = 기수 트리 기반)** — 새 PID는 `idr_alloc_cyclic`으로 다음 빈 번호를 순환하며 고른다(kernel/pid.c). `pid_max`에 닿으면 `RESERVED_PIDS`(300)부터 다시 빈 번호를 찾는다(kernel/pid.c `alloc_pid`, include/linux/threads.h). [data-structure/20-radix-trie](../../data-structure/20-radix-trie/2-summary.md)
- **대기 큐** — S·D 상태의 태스크는 대개 기다리는 사건(I/O 완료, 락)의 대기 큐에 걸려 있다. 사건이 생기면 깨워 R로 만든다(17번). 대기 큐가 유일한 방법은 아니다. `nanosleep`은 타이머(`hrtimer_sleeper`)가 태스크를 직접 깨운다(kernel/time/hrtimer.c `do_nanosleep`).

## 적용 — 풀어나가는 법

### 1. 상태와 부모를 본다

```bash
# 상태·부모·잠든 커널 함수
ps -eo pid,ppid,stat,wchan:20,comm

# 스레드까지 (LWP = 스레드 ID)
ps -eLo pid,lwp,stat,comm | head

# 상태별 개수
ps -eo stat= | cut -c1 | sort | uniq -c

# 좀비와 그 부모
ps -eo pid,ppid,stat,comm | awk '$3 ~ /^Z/'

# 트리로
pstree -p <pid>

# 한 프로세스 자세히
grep -E '^(State|PPid|Threads|voluntary_ctxt|nonvoluntary_ctxt)' /proc/<pid>/status
```

- 로컬 예(리눅스 7.0 데스크톱): `S` 495개, `I` 171개, `R` 2개, `D` 1개(예시). 대부분의 프로세스는 대부분의 시간에 잠들어 있다.

### 2. 한도를 확인한다

```bash
cat /proc/sys/kernel/pid_max          # PID 최댓값+1 (6.13까지 시스템 전체, 6.14부터 PID 네임스페이스별)
cat /proc/sys/kernel/threads-max      # 태스크 수 한도 (시스템 전체)
ulimit -u                             # RLIMIT_NPROC: 이 사용자(실 UID)의 프로세스+스레드 수
cat /sys/fs/cgroup/<그룹>/pids.max     # cgroup(컨테이너)별 한도
```

- 로컬 값(예시): `pid_max` 4194304, `threads-max` 274945, `ulimit -u` 137472.
  - `pid_max` 커널 기본은 32768이다(proc_sys_kernel(5)). 단 소스는 CPU가 많으면 `1024 × CPU 수`까지 올린다(kernel/pid.c `PIDS_PER_CPU_DEFAULT`). 이 Ubuntu는 systemd의 `/usr/lib/sysctl.d/50-pid-max.conf`가 4194304로 올려 둔다.
- `fork`의 `EAGAIN`은 대개 이 네 가지 한도 중 하나에 닿았다는 뜻이다(fork(2) ERRORS). 다른 경우는 `SCHED_DEADLINE` 정책으로 돌면서 reset-on-fork 플래그가 없는 호출자 하나뿐이다.
  - `pid_max`는 리눅스 6.14부터 PID 네임스페이스마다 따로 있다(kernel/pid_namespace.c). 새 PID는 조상 네임스페이스에서도 번호를 받으니 조상 쪽 한도도 걸린다.
  - `RLIMIT_NPROC`은 root(초기 user 네임스페이스의 실 UID 0)나 `CAP_SYS_RESOURCE`·`CAP_SYS_ADMIN`이 있는 호출자에게는 적용되지 않는다(kernel/fork.c `copy_process`, getrlimit(2)).

### 3. 애플리케이션에서 자기 정보를 본다

```java
ProcessHandle me = ProcessHandle.current();
System.out.println(me.pid() + " parent=" + me.parent().map(ProcessHandle::pid).orElse(-1L));
```

```js
console.log(process.pid, process.ppid);   // Node
```

## 장애 시나리오와 대처

### 1. 좀비 누적 → PID 고갈 → `fork: Resource temporarily unavailable`

- **현상**: 처음엔 멀쩡하다가, 시간이 지나 새 프로세스·스레드를 못 만든다. 셸 명령조차 안 뜬다.
- **보이는 형태**
  - `ps`에 `Z`/`<defunct>`가 수백~수천 개, 모두 같은 PPID.
  - bash: `fork: retry: Resource temporarily unavailable`, C: `fork()` = -1, errno `EAGAIN`(11). Java: `OutOfMemoryError: unable to create native thread`·`IOException` 등 런타임마다 다른 모양.
  - 로컬 재현: `RLIMIT_NPROC`을 현재+5로 낮추고 자식을 만들자 7번째 `fork`가 `errno=11 Resource temporarily unavailable`이었다. bash도 `fork: retry: 자원이 일시적으로 사용 불가능함`을 냈다(예시).
- **원인**
  - 부모가 자식을 `wait`하지 않는다. 끝난 자식이 좀비로 남아 PID·태스크 자리를 차지한다.
  - 한도는 사용자별(`RLIMIT_NPROC`), 시스템(`pid_max`·`threads-max`), cgroup(`pids.max`) 중 먼저 닿는 것이다.
- **대처**
  - 좀비의 **부모**를 찾는다(`ps -o ppid`). 좀비 자체는 `kill -9`로 안 없어진다.
  - 부모 코드를 고친다: `SIGCHLD` 핸들러에서 `waitpid(-1, ..., WNOHANG)` 루프, 또는 자식마다 `waitpid`(05번).
  - 급하면 부모를 종료한다. 좀비는 init(또는 subreaper)에 입양되어 회수된다.
  - 컨테이너의 PID 1이 회수를 안 하는 경우는 05번(tini).

### 2. 고아 프로세스가 남는다

- **현상**: 서비스를 재시작했는데 옛 워커가 계속 돌며 포트·파일·메모리를 잡고 있다.
- **보이는 형태**: `ps -eo pid,ppid,comm`에서 PPID가 1(또는 사용자 systemd 같은 subreaper)인 옛 프로세스.
- **원인**
  - 부모만 죽이고 자식은 안 죽였다. 커널은 보통 고아를 죽이지 않고 입양만 한다(예외는 핵심 문장 아래 참고).
  - 셸 스크립트가 `&`로 띄운 자식을 기다리지 않고 끝났다.
- **대처**
  - 서비스 관리자에게 그룹 단위로 끄게 한다. systemd `KillMode=control-group`(기본)은 유닛의 cgroup에 남은 모든 프로세스를 끈다(systemd.kill(5)).
  - 자식이 부모와 함께 죽어야 하면 자식에서 `prctl(PR_SET_PDEATHSIG, SIGTERM)`. 단 "부모"는 자식을 만든 **스레드**다(prctl(2) 경고).
  - 부모는 종료 전에 자식에게 시그널을 보내고 `wait`한다.

### 3. `D` 상태 누적 → load average는 높은데 CPU는 한가

- **현상**: load average가 코어 수보다 훨씬 큰데 `top`의 CPU 사용률은 낮다.
- **보이는 형태**
  - `ps -eo stat,wchan:30,comm | awk '$1 ~ /^D/'`에 여러 프로세스.
  - `vmstat`의 `b` 열 증가.
- **원인**
  - load average는 R과 **D**를 센다(proc_loadavg(5)). D는 대개 디스크·NFS 같은 I/O 대기다.
  - 느린·멈춘 저장 장치, 끊긴 NFS 서버, major fault 폭주(03번)가 흔한 원인이다.
- **대처**
  - WCHAN(잠든 커널 함수)과 관련 마운트·장치를 본다. `/proc/<pid>/stack`은 root만 읽을 수 있다.
  - `kill -9`는 대기가 끝나야 효과가 있을 수 있다. 원인 I/O를 푸는 것이 먼저다.
  - load average만 보지 말고 `vmstat`의 `r`(실행 가능 수)과 `b`(I/O 대기로 막힌 수)를 나눠 본다. `b`는 `/proc/stat`의 `procs_blocked`(= `nr_iowait()`)라서 I/O 대기가 아닌 `D`는 안 센다(fs/proc/stat.c).

### 4. 컨테이너 안에서만 `fork` 실패

- **현상**: 호스트는 멀쩡한데 한 컨테이너에서만 스레드·프로세스 생성이 실패한다.
- **보이는 형태**: `EAGAIN`, JVM `unable to create native thread`.
- **원인**: 그 cgroup의 `pids.max`(프로세스+스레드 수 한도)에 닿았다(fork(2) ERRORS 4번째 항목). 좀비·스레드 누수가 흔한 원인이다.
- **대처**: `cat /sys/fs/cgroup/.../pids.current`·`pids.max`를 비교한다. 스레드 풀 크기·좀비 회수를 고치고, 필요하면 한도를 조정한다(28번).

## 핵심 문장

- 프로세스는 실행 중인 프로그램이고, 커널은 프로세스(와 스레드)마다 `task_struct` 하나에 상태·부모·주소 공간·fd·스케줄 정보를 적는다. 이것이 리눅스의 PCB다.
- 교과서의 Ready·Running은 리눅스에서 둘 다 `R`(TASK_RUNNING)이다. Blocked는 시그널로 깨는 `S`와 안 깨는 `D`로 나뉜다.
- 끝난 프로세스는 (부모가 `SIGCHLD`를 `SIG_IGN`으로 두지 않았다면) 부모가 `wait`할 때까지 PID·종료 상태를 남긴 좀비(`Z`)다. 좀비는 `kill -9`로 안 없어지고, 부모가 회수하거나 부모가 죽어 입양돼야 사라진다.
- 부모가 먼저 죽은 자식은 가장 가까운 subreaper나 init에 입양된다. 고아가 됐다는 이유만으로 보통 죽지는 않는다.
  - 예외: PID 네임스페이스의 init이 끝나면 그 네임스페이스의 나머지는 `SIGKILL`을 받는다(pid_namespaces(7)). 부모 종료로 새로 고아가 된 프로세스 그룹에 멈춘 작업이 있으면 `SIGHUP`·`SIGCONT`가 가서 기본 처분이면 죽는다(kernel/exit.c `kill_orphaned_pgrp`).
- 좀비·스레드가 쌓여 호출자에게 적용되는 한도(`RLIMIT_NPROC`·`pid_max`·`threads-max`·`pids.max`) 중 하나에 닿으면 `fork`가 `EAGAIN`("Resource temporarily unavailable")으로 실패한다.

## 관련 주제·근거

- 선행: [03-interrupts-traps-faults](../03-interrupts-traps-faults/2-summary.md) — 타이머 인터럽트·폴트가 상태를 바꾸는 계기
- 원고: [foundations/process-thread](../../foundations/process-thread/README.md) §1·§2·§5·§6
- 후속
  - [05-fork-exec-wait](../05-fork-exec-wait/2-summary.md) — 프로세스를 만들고 회수하는 API
  - [06-signals](../06-signals/2-summary.md) — SIGCHLD·SIGSTOP·SIGKILL.
  - [07-threads-and-context-switch](../07-threads-and-context-switch/2-summary.md) · [08-cpu-scheduling](../08-cpu-scheduling/2-summary.md) — 스레드도 task, 실행 큐.
  - [28-containers-namespaces-cgroups](../28-containers-namespaces-cgroups/2-summary.md) — `pids.max`, PID 네임스페이스.
- 교재
  - OSTEP 4장 The Abstraction: The Process — 4.4 Process States, 4.5 Data Structures(xv6 `proc`, 좀비) <https://pages.cs.wisc.edu/~remzi/OSTEP/cpu-intro.pdf>
  - CS:APP 3판 8.2 Processes
- man
  - ps(1) "PROCESS STATE CODES" · proc_pid_status(5) · proc_loadavg(5)(R+D) · proc_sys_kernel(5)(`pid_max` 기본 32768, `threads-max`)
  - wait(2) NOTES — 좀비가 남기는 것, 표가 차면 생성 불가, init/subreaper 입양 <https://man7.org/linux/man-pages/man2/wait.2.html>
  - fork(2) ERRORS — `EAGAIN`의 네 한도 <https://man7.org/linux/man-pages/man2/fork.2.html> · getrlimit(2) `RLIMIT_NPROC` · pid_namespaces(7)
  - prctl(2) — `PR_SET_CHILD_SUBREAPER`, `PR_SET_PDEATHSIG` · systemd.kill(5) — `KillMode=`
- Linux 소스(master)
  - include/linux/sched.h — `task_struct`(`__state`, `pid`, `tgid`, `real_parent`, `children`, `sibling`, `tasks`, `mm`, `files`, `signal`, `thread`, `exit_state`), 상태 상수, `TASK_KILLABLE`
  - fs/proc/array.c — `task_state_array`(R·S·D·T·t·X·Z·P·I)
  - include/linux/sched/signal.h — `for_each_process`, `for_each_process_thread`
  - v7.0에서 확인: kernel/fork.c `copy_process`(`tasks`는 리더만, `RLIMIT_NPROC` 면제), kernel/sched/core.c `sched_contributes_to_load`, kernel/time/hrtimer.c `do_nanosleep`, kernel/pid_namespace.c `pid_max`(6.14부터), kernel/exit.c `kill_orphaned_pgrp`
  - kernel/pid.c — `idr_alloc_cyclic`
  - arch/x86/entry/entry_64.S — `__switch_to_asm`
- 로컬 재현(리눅스 7.0.0): 좀비 3개 생성과 `wait` 후 소멸, 좀비에 `kill -9`(변화 없음, 종료 코드 7 유지), 고아의 PPID → `systemd --user`, `RLIMIT_NPROC`로 `fork` EAGAIN, bash `fork: retry`, S→T→S 상태 관찰, 상태별 개수
