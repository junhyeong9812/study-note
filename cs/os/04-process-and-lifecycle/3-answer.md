# os/04-process-and-lifecycle — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-30). 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 정답

### 1. 상태 전이도

```text
                  스케줄됨
  생성 ---> Ready ---------> Running ---exit---> 종료(좀비) --부모 wait--> 사라짐
              ^  <----------   |
              |  선점(타이머)    | I/O 시작
              |  I/O 완료       v
              +---------- Blocked
```

- 생성 → Ready: 만들어지면 먼저 실행 대기 줄에 선다.
- Ready → Running: 스케줄러가 골랐다. Running → Ready: 타이머 인터럽트로 선점됐다.
- Running → Blocked: I/O 등 기다릴 일을 시작했다. Blocked → Ready: 기다리던 일이 끝났다.
- I/O가 끝나도 **곧바로 Running이 아니라 Ready**다. CPU는 이미 다른 프로세스가 쓰고 있을 수 있다(OSTEP 4.4, 원고 §2).

### 2. 교과서 상태 ↔ ps 글자

- Ready·Running → 둘 다 **`R`**(`TASK_RUNNING`). ps(1)도 "running or runnable (on run queue)"라고 적는다.
- Blocked → **`S`**(시그널로 깨는 대기) 또는 **`D`**(시그널로 안 깨는 대기, 대개 I/O).
- 종료(좀비) → **`Z`**.
- "구분하지 않는다" = 태스크의 상태 값 자체는 둘 다 `TASK_RUNNING`이다. 지금 CPU 위에서 도는지는 상태 값이 아니라 스케줄러(실행 큐의 현재 태스크)가 안다.

### 3. `S` vs `D`

- `S`(`TASK_INTERRUPTIBLE`): 사건을 기다리지만 시그널이 오면 깨서 처리한다.
- `D`(`TASK_UNINTERRUPTIBLE`): 시그널이 와도 깨지 않는다. 기다리던 일이 끝나야 깬다. 대개 디스크·NFS I/O다.
- `D`에 `kill -9`: 시그널은 걸리지만 **대기가 끝날 때까지 효과가 없을 수 있다**.
- 예외: `TASK_KILLABLE`(= `TASK_WAKEKILL | TASK_UNINTERRUPTIBLE`)로 잠든 경우는 치명적 시그널(SIGKILL 등)에는 깬다. ps에는 똑같이 `D`로 보여서 겉으로는 구분이 안 된다.

### 4. `task_struct`와 레지스터 위치

- 들어 있는 것(include/linux/sched.h)
  - `__state`(상태), `pid`·`tgid`(스레드 ID·프로세스 ID)
  - `real_parent`·`parent`, `children`·`sibling`(프로세스 트리), `tasks`(전체 프로세스 목록 연결 — 스레드 그룹 리더만)
  - `mm`(주소 공간), `files`(fd 표), `signal`(시그널 정보)
  - `se`(스케줄러 엔티티), `stack`(커널 스택), `thread`(CPU 문맥 일부)
  - `exit_state`·`exit_code`(좀비일 때 남는 것)
- 레지스터 위치(x86-64)
  - 유저 모드 레지스터: 커널에 들어올 때(시스템 콜·인터럽트) **커널 스택 맨 위의 `pt_regs`** 에 저장된다.
  - 문맥 교환(`__switch_to_asm`): callee-saved 레지스터를 커널 스택에 push하고, 커널 스택 포인터를 `thread.sp`에 저장한 뒤 다음 태스크의 `thread.sp`로 바꾼다.
- 원고의 "PCB에 레지스터를 저장한다"는 개념상 맞다. 리눅스에서는 그 저장소가 task에 딸린 커널 스택과 `thread`로 나뉘어 있다.

### 5. 좀비

- `ps`에서 STAT **`Z`**, 명령 이름 옆에 **`<defunct>`**.
- `kill -9`: `kill()`은 성공(0)을 돌려주지만 **아무 변화 없다**. 이미 죽은 프로세스라 더 죽일 것이 없다. 로컬 재현에서도 계속 `Z`였다.
- 부모가 `waitpid`하면 좀비가 사라지고 종료 코드 **7**을 받는다(`WEXITSTATUS`). 로컬 재현으로 확인했다.
- 좀비가 남기는 것: PID, 종료 상태, 자원 사용 정보(wait(2) NOTES).

### 6. 고아

- 자식은 보통 죽지 않고 계속 돈다. **고아**가 된다.
  - 예외: 죽은 부모가 PID 네임스페이스의 init이면 나머지가 `SIGKILL`을 받는다(pid_namespaces(7)). 새로 고아가 된 프로세스 그룹에 멈춘 작업이 있으면 `SIGHUP`·`SIGCONT`를 받는다(kernel/exit.c).
- 커널이 고아를 가장 가까운 **subreaper**에게, 없으면 **init(PID 1)** 에게 입양시킨다. PPID가 그 프로세스로 바뀐다.
- 데스크톱에서는 사용자 세션의 systemd(`systemd --user`)가 subreaper라서 PPID가 1이 아닐 수 있다. 로컬 재현에서 PPID가 4106(`systemd --user`)이 됐다.
- init은 입양한 자식이 끝나면 자동으로 `wait`한다(wait(2) NOTES). subreaper는 스스로 `wait`해야 한다. 안 하면 입양된 자식이 좀비로 쌓인다(05번 재현).

### 7. load 20, CPU 10%

- load average는 **R(실행 중·대기)과 D(대개 I/O 대기)** 태스크 수의 평균이다(proc_loadavg(5)). CPU 사용률이 아니다. (정확히는 load에 산입되는 비인터럽트 대기만 센다. 얼어 있는 태스크처럼 `D`로 보여도 빠지는 경우가 있다 — kernel/sched/core.c.)
- D 상태 태스크가 많으면 CPU를 안 쓰는데도 load가 오른다. 예: 느린 디스크, 끊긴 NFS, major fault 폭주.
- 확인: `vmstat 1`의 `r`(실행 가능 수)와 `b`(I/O 대기로 막힌 수 — `D` 전체와 같지는 않다)를 나눠 보고, `ps -eo stat,wchan:30,comm`에서 `D`를 찾는다.

### 8. 컨테이너의 fork 실패와 좀비

- 원인
  - 어떤 부모가 자식을 `wait`하지 않아 좀비가 쌓였다. 좀비도 PID·태스크 자리를 차지한다.
  - 그 컨테이너의 `pids.max`(또는 `RLIMIT_NPROC`·`pid_max`·`threads-max`)에 닿아 `fork`가 `EAGAIN`을 돌려준다(fork(2) ERRORS).
- 확인 순서
  1. `ps -eo pid,ppid,stat,comm | awk '$3 ~ /^Z/'`로 좀비와 **공통 PPID**를 찾는다.
  2. `cat /sys/fs/cgroup/.../pids.current`와 `pids.max`를 비교한다.
  3. 그 부모가 무엇인지 본다. 컨테이너 PID 1인 앱이 자식을 회수하지 않는 경우가 흔하다(05번).
- 대처
  - 좀비를 직접 죽이는 것은 **소용없다**(이미 죽었다).
  - 부모가 회수하게 고친다(`SIGCHLD`에서 `waitpid(-1, &st, WNOHANG)` 루프).
  - PID 1 자리에 좀비를 회수하는 init(tini, `docker run --init`)을 둔다(05번).
  - 급하면 부모를 재시작한다. 좀비가 입양되어 회수된다.

### 9. 재시작 뒤 남은 옛 워커

- 이유: 부모(마스터)만 끝났고, 커널은 보통 자식을 죽이지 않고 **입양**만 한다. 고아가 된 워커는 PPID 1(또는 subreaper) 밑에서 계속 포트를 잡는다.
- 막는 법
  - 서비스 관리자에게 그룹 단위로 끄게 한다. systemd `KillMode=control-group`(기본)은 유닛 cgroup의 남은 프로세스를 모두 끈다. `process`·`none`은 이런 탈출을 허용해 권장되지 않는다(systemd.kill(5)).
  - 부모가 종료 전에 자식에게 SIGTERM을 보내고 `wait`한다.
  - 자식에서 `prctl(PR_SET_PDEATHSIG, SIGTERM)`. 단 "부모"는 자식을 만든 스레드라, 그 스레드만 끝나도 시그널이 온다(prctl(2)).
