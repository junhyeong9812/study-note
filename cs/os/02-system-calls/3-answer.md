# os/02-system-calls — 정답

## 정답

### 1. `write()`의 경로

```text
  app: write(fd, buf, n)                       (보통 함수 호출)
    -> glibc 래퍼: rax=1, rdi=fd, rsi=buf, rdx=n, syscall
    -> [커널] entry_SYSCALL_64: 레지스터를 커널 스택(pt_regs)에 저장
    -> do_syscall_64: 번호 범위 확인 -> x64_sys_call(번호로 분기)
    -> __x64_sys_write -> 실제 쓰기
    -> 결과를 rax에 (성공: 바이트 수, 실패: -errno)
    -> sysret(조건 안 맞으면 iret)로 유저 모드 복귀
    -> glibc: rax가 -4095..-1이면 errno=-rax, return -1
```

- 번호: `rax`. 인자: `rdi, rsi, rdx, r10, r8, r9`. 반환: `rax`(syscall(2)).
- 4번째 인자가 `r10`인 이유: `syscall` 명령이 `rcx`에 돌아갈 주소를, `r11`에 rflags를 저장하기 때문이다(entry_64.S 주석).

### 2. 음수 반환과 errno

- 커널은 실패를 **음수 에러 번호**(예: -4 = -EINTR)로 돌려준다.
- 대부분의 libc 래퍼가 그 절댓값을 `errno`에 넣고 `-1`을 돌려준다(intro(2)). 그래서 사용자는 보통 -1과 errno를 본다.
  - 예외: `clock_nanosleep()`은 양수 에러 번호를 그대로 반환하고 errno를 쓰지 않는다(clock_nanosleep(2)).
- 성공한 호출은 errno를 0으로 지우지 않는다. 그래서 예전 실패의 값이 남아 있을 수 있다. errno는 **반환값이 실패를 가리킬 때만** 본다.

### 3. 함수 이름 ≠ 시스템 콜 이름

- `fork()`: glibc 2.3.3부터 `fork` 시스템 콜이 아니라 `clone`(flags에 SIGCHLD 등)을 부른다(fork(2)). 로컬 strace에서도 `clone(child_stack=NULL, flags=CLONE_CHILD_CLEARTID|CLONE_CHILD_SETTID|SIGCHLD, ...)`였다.
- `printf()`: 시스템 콜이 아니다. stdio 버퍼에 쌓고, 버퍼가 차거나 flush될 때(줄 버퍼면 줄바꿈, `fflush`, 정상 종료) `write`를 부른다(setbuf(3)).
- `clock_gettime()`: 대개 시스템 콜 없이 **vDSO**에서 끝난다. 모드 전환이 없고 strace에도 안 잡힌다(로컬: 1000번 호출이 strace에 0번).

### 4. 1바이트 write vs stdio

- (a) `write` **1,000,000번**. (b) 버퍼(로컬 4096바이트)가 찰 때마다 한 번 → 약 **245번**.
- (a)가 훨씬 느리고, 시간 대부분이 **sys**다. 로컬 재현: (a) real 0.41s·user 0.06s·sys 0.35s, (b) 거의 0(예시).
- 이유: 시스템 콜마다 모드 전환 고정 비용(로컬 약 100~150ns)이 든다. 데이터 양이 같아도 호출 수가 비용을 정한다.

### 5. `read` 중 SIGALRM

- `SA_RESTART` 없음: 핸들러가 끝나면 `read`가 **-1, errno=EINTR**로 돌아온다. 로컬: `read=-1 errno=Interrupted system call`.
- `SA_RESTART` 있음: 커널이 `read`를 **다시 시작**한다. 앱은 끊긴 것을 모른다. 로컬: 계속 기다렸다가 데이터를 받았다.
  - strace에는 그 순간 `ERESTARTSYS`가 보인다. 커널 내부 값이라 앱에는 안 보인다.
- `poll()`: `SA_RESTART`와 상관없이 **EINTR**다(signal(7) "never restarted" 목록). `epoll_wait`·`select`·`nanosleep`도 같다.
  - 드문 예외: seccomp 사용자 알림 응답을 기다리다 끊긴 경우는 재시작될 수 있다(seccomp_unotify(2)).

### 6. 전송 도중 시그널

- 이미 일부를 옮겼다면 **EINTR가 아니라 옮긴 바이트 수**로 성공을 돌려준다(signal(7), write(2)).
- 호출하는 쪽은 반환값이 요청보다 작으면 **나머지를 이어서** 다시 써야 한다(짧은 쓰기 루프). 안 하면 데이터 끝이 조용히 잘린다.

### 7. 번호로 핸들러 찾기

- 정본 목록은 `syscall_64.tbl`(번호 → 이름 → 함수)이다. 예: 0 read, 1 write, 59 execve.
- 예전 x86-64: `sys_call_table[nr](regs)` — 번호를 인덱스로 한 **함수 포인터 배열**의 간접 호출.
- 최신(2024-04 커밋 1e3ad78334a6, 6.9 개발 주기부터): 같은 표로 **`switch` 문**(`x64_sys_call`)을 만들어 분기한다. 간접 분기를 노리는 투기 실행 공격(BHI)을 줄이려는 변경이다. 배열은 추적용으로 남았다.
- 배열 방식은 번호를 인덱스로 바로 찾는다(상수 시간). `switch` 방식은 그 `switch`를 어떤 기계어(비교 분기열 등)로 만들지 컴파일러가 정한다. x86 커널은 `-fno-jump-tables`로 점프 테이블도 막으니, 상수 시간이 보장되지는 않는다(arch/x86/Makefile).
- 어느 쪽이든 범위 검사 뒤 `array_index_nospec()`도 거친다.

### 8. 로그 서비스의 sys CPU

- 확인
  - `pidstat -u -p <pid> 1`로 `%system`이 큰지 본다.
  - `timeout 5 strace -c -f -p <pid>`로 `write` 호출 수를 본다. 호출당 크기는 `-c`에 안 나오니 `timeout 5 strace -e trace=write -p <pid>`의 인자·반환값으로 본다. 초당 수십만 번, 호출당 수 바이트면 확정이다.
- 원인: 줄(또는 바이트)마다 버퍼 없이 `write`한다. 모드 전환 비용이 쌓인다.
- 대처: 버퍼링(stdio, `BufferedOutputStream`, 로거의 버퍼·비동기 appender), 여러 조각은 `writev`. 디스크 내구성이 필요한 로그는 flush·fsync 정책을 따로 정한다.

### 9. 간헐적 EINTR

- 원인
  - 프로세스에 시그널 핸들러가 있다(예: `SIGCHLD` 자식 회수, `SIGALRM` 타이머).
  - 블록 중인 `read`가 그 시그널에 끊겼다. 핸들러가 `SA_RESTART` 없이 달렸거나, 재시작 안 되는 호출이다.
  - 시그널 도착과 겹칠 때만 나서 하루 몇 번이다.
- 고치는 법
  - `EINTR`면 다시 부르는 루프로 감싼다. 타임아웃이 있는 대기는 남은 시간을 다시 계산한다.
  - 핸들러를 `SA_RESTART`로 단다. 단 `poll`·`nanosleep` 등은 여전히 루프가 필요하다.
- Java·Node에서 드문 이유: 런타임이 대신 재시도한다.
  - OpenJDK NIO는 `EINTR`를 `IOS_INTERRUPTED`로 바꾸고, Java 코드가 `while (n == IOStatus.INTERRUPTED && isOpen())`로 다시 부른다.
  - libuv는 `while (r == -1 && errno == EINTR)` 루프를 쓴다.

### 10. 운영 중 strace

- 조심할 것
  - ptrace는 시스템 콜마다 대상을 멈추고 strace로 문맥을 바꾼다. 시스템 콜이 많은 프로세스는 크게 느려진다(로컬 재현 약 100배).
  - Yama `ptrace_scope=1`이면 자기 자손이 아닌 프로세스에 붙이려면 권한(`CAP_SYS_PTRACE`)이 필요하다. 대상이 `PR_SET_PTRACER`로 허락한 경우는 예외다.
- 붙이는 법
  - 짧게: `timeout 5 strace -c -f -p <pid>` — 먼저 호출 **수** 분포만.
  - 범위를 좁힌다: `-e trace=%net` 또는 `-e trace=write`.
  - 가능하면 한 인스턴스를 트래픽에서 빼고 붙인다.
