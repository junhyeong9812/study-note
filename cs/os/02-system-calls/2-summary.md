# os/02-system-calls — 커널에 부탁하는 유일한 창구, 그리고 한 번 부를 때마다 드는 값 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> ⚠️ 이 서머리는 Claude 초안(2026-09-30) — 근거는 아래 「관련 주제·근거」. 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 해결하는 문제

유저 모드 프로그램은 파일·소켓·메모리·프로세스를 직접 만질 수 없다(01번).\
그런데 프로그램은 이런 일을 계속 해야 한다.

```text
  프로그램이 하고 싶은 일        누가 해 줘야 하나
  파일 읽기·쓰기                  커널 (디스크·페이지 캐시)
  소켓 열기·보내기                 커널 (네트워크 스택)
  메모리 더 받기                   커널 (페이지 테이블)
  새 프로세스 만들기               커널 (프로세스 목록)
```

그래서 "번호 + 인자"를 들고 커널에 들어가는 정해진 창구가 필요하다. 그것이 **시스템 콜**이다.
  - *시스템 콜(system call)*: 유저 프로그램이 커널 기능을 요청하는 진입점이다(intro(2)).

쉬운 예: 민원 창구다.
- 민원인은 서류 번호(시스템 콜 번호)와 내용(인자)을 적어 창구에 낸다.
- 창구 직원(커널)은 번호를 보고 담당 부서(핸들러)로 넘긴다.
- 처리 결과(반환값)를 돌려받는다. 실패면 사유 코드(errno)가 붙는다.
- 창구에 한 번 갈 때마다 줄 서고 신분 확인하는 **고정 비용**이 든다. 서류 한 장씩 100만 번 내면 하루가 간다.

똑같은 구조다.\
시스템 콜 한 번에는 모드 전환이라는 고정 비용이 있다. 작은 요청을 많이 보내면 그 비용이 주가 된다.

실무 예:
- 로그를 한 줄씩 버퍼 없이 쓰면 `sys` CPU가 치솟는다.
- 시그널을 받는 프로그램에서 `read()`가 가끔 `EINTR`로 실패한다.
- 운영 서버에 `strace`를 붙였더니 서비스가 느려졌다.

## 동작·원리

### `write()` 한 번의 여정

```text
  유저 모드                                   커널 모드
  ---------                                   ---------
  app:   write(fd, buf, n)
           |  (보통의 C 함수 호출)
           v
  glibc: write 래퍼
           rax <- 1        (시스템 콜 번호: write)
           rdi <- fd, rsi <- buf, rdx <- n
           syscall  ---------------------->  entry_SYSCALL_64
                                               rip->rcx, rflags->r11 (CPU가 저장)
                                               레지스터를 커널 스택(pt_regs)에 저장
                                             do_syscall_64(regs, nr)
                                               nr < NR_syscalls 인지 확인
                                               x64_sys_call(regs, nr)   번호로 분기
                                                 -> __x64_sys_write -> ... 실제 작업
                                               regs->ax <- 결과 (성공: 바이트 수, 실패: -errno)
           <-----------------------------  sysret (조건이 안 맞으면 iret)
  glibc: rax가 -4095..-1 이면
           errno <- -rax, return -1
         아니면 return rax
```

- 로컬 glibc 2.39의 `write`를 디스어셈블하면 `mov $0x1,%eax` → `syscall` → `cmp $0xfffffffffffff000,%rax`다(예시). 마지막 비교가 "에러 범위인가" 검사다.
- 커널 쪽 경로는 arch/x86/entry/entry_64.S `entry_SYSCALL_64` → arch/x86/entry/syscall_64.c `do_syscall_64`다(v6.19·v7.0 기준. 6.12 소스에서는 `do_syscall_64`가 arch/x86/entry/common.c에 있었다).
- 커널은 실패를 **음수 에러 번호**로 돌려준다. 대부분의 래퍼는 그것을 `errno`에 넣고 -1을 돌려준다(intro(2)).
  - 예외도 있다. `clock_nanosleep()`은 errno를 쓰지 않고 **양수 에러 번호를 그대로 반환**한다(clock_nanosleep(2) RETURN VALUE). pthread 함수들도 이 방식이다.
  - *errno*: 마지막 실패 원인을 담는 스레드별 변수다. 성공한 호출은 errno를 지우지 않으니, 반환값이 실패일 때만 본다.

### x86-64 리눅스의 약속(ABI)

```text
  번호: rax      인자: rdi  rsi  rdx  r10  r8  r9      반환: rax
  syscall 명령이 rcx(돌아갈 주소)·r11(rflags)을 덮어쓴다
```

- 네 번째 인자가 일반 C 함수(rcx)와 달리 **r10**이다. syscall 명령이 rcx를 쓰기 때문이다(syscall(2) 표, entry_64.S 주석).
- 인자는 최대 6개다.

### 래퍼 ≠ 시스템 콜

```text
  C 라이브러리 함수          실제로 부르는 시스템 콜 (로컬 strace, glibc 2.39)
  write()                    write
  fork()                     clone(flags=...|SIGCHLD)          (fork 시스템 콜 아님)
  posix_spawn()              clone3(CLONE_VM|CLONE_VFORK|...)
  printf()                   (버퍼가 차거나, 줄 버퍼면 줄바꿈, fflush·exit 때) write
  clock_gettime()            없음 — vDSO로 유저 모드에서 끝남
```

- 대부분의 래퍼는 얇다. 인자를 레지스터에 넣고 트랩하고 errno를 채운다(intro(2)).
- 일부는 이름과 다른 시스템 콜을 부른다. `fork()`는 glibc 2.3.3부터 `clone`을 부른다(fork(2) "C library/kernel differences").
- 래퍼가 없는 시스템 콜은 `syscall(SYS_xxx, ...)`로 직접 부른다(syscall(2)).

**vDSO** — 모드 전환 없이 끝나는 "시스템 콜".
- 커널이 모든 프로세스 주소 공간에 작은 공유 라이브러리를 넣어 둔다(`/proc/self/maps`의 `[vdso]`).
- `clock_gettime`·`gettimeofday`·`getcpu` 등이 여기 있다(vdso(7) x86-64 표). 시간 함수는 커널이 갱신하는 시간 데이터를 유저 모드에서 읽어 끝낸다. `getcpu`는 지금 도는 CPU·NUMA 노드 번호를 돌려준다(getcpu(2)).
- 로컬 재현: `clock_gettime()` 1000번 + `syscall(SYS_clock_gettime)` 1000번 → `strace -c`에는 **1000번만** 보였다(예시). vDSO 호출은 strace에 안 잡힌다.
  - *vDSO(virtual dynamic shared object)*: 커널이 프로세스마다 매핑해 주는 작은 공유 라이브러리다.

### 비용 — 로컬 측정

```text
  (예시, 리눅스 7.0, i7-13700HX, 200만 번 반복 평균)
  일반 함수 호출(noinline)              ~0.6–0.9 ns
  clock_gettime (vDSO, 전환 없음)        ~18 ns
  getppid 시스템 콜 (거의 일 없음)        ~109 ns
  write 1바이트 → /dev/null              ~150 ns
```

- 일 없는 시스템 콜 하나가 함수 호출의 약 100배다. 이것이 **모드 전환의 고정 비용**이다.
  - 레지스터 저장·복원, 커널 스택 전환, 보안 완화(투기 실행 방어) 코드가 여기 든다.
  - 보안 완화 비용은 CPU·커널 설정마다 다르다. 이 CPU는 `meltdown: Not affected`라 KPTI가 없다.
- OSTEP 6장은 1996년 리눅스 1.3.37·200MHz에서 시스템 콜이 약 4µs였고, 현대 시스템은 1µs 미만이라고 적는다.

**작은 `write` 반복 vs 버퍼링** — 같은 1,000,000바이트를 쓴다(예시, 로컬 재현).

```text
                          write 호출 수     real    user    sys
  write(1, "x", 1) × 1M   1,000,000         0.41s   0.06s   0.35s
  fputc('x') × 1M         245               0.00s   0.00s   0.00s
                          (stdio 버퍼 4096바이트씩)
```

- 데이터 양은 같다. 차이는 **호출 횟수**다. sys 시간이 호출 횟수를 따라간다.
- stdio는 버퍼를 채운 뒤 한 번에 `write`한다. 1,000,000 / 4096 ≈ 245번이다.

### 시그널이 끼어들면 — `EINTR`

```text
  read(pipe) 블록 중 ...
       |
       |  SIGALRM 도착, 핸들러 실행
       v
  핸들러를 SA_RESTART로 달았나?
       예  -> 커널이 read를 다시 시작 (앱은 모름)
       아니오 -> read가 -1, errno = EINTR
```

- signal(7)의 규칙이다. "느린 장치"(파이프·소켓·터미널)의 `read`·`write` 등은 `SA_RESTART`면 재시작, 아니면 `EINTR`이다.
  - 로컬 디스크 파일 I/O는 "느린 장치"가 아니라 시그널로 끊기지 않는다(signal(7)).
- **`SA_RESTART`와 상관없이 `EINTR`인 것**도 있다(signal(7)).
  - 드문 예외: seccomp 사용자 공간 알림(`SECCOMP_RET_USER_NOTIF`) 응답을 기다리다 끊긴 경우는 이 목록의 호출도 `SA_RESTART`로 재시작될 수 있다(seccomp_unotify(2) "Interaction with SA_RESTART signal handlers").
  - `poll`·`select`·`epoll_wait`, `nanosleep`·`clock_nanosleep`, 수신 타임아웃(`SO_RCVTIMEO`)을 건 `accept`·`recv`, 송신 타임아웃을 건 `connect`·`send` 등.
  - signal(7)은 송신 쪽 목록에도 `SO_RCVTIMEO`라고 적었지만, 커널 `inet_stream_connect`는 `sock_sndtimeo()`(= `SO_SNDTIMEO`)를 쓰고 `sock_intr_errno()`가 타임아웃이 있으면 `-EINTR`를 돌려준다(net/ipv4/af_inet.c, include/net/sock.h).
- 데이터를 일부 옮긴 뒤 끊기면 `EINTR`이 아니라 **옮긴 바이트 수**로 성공한다(signal(7), write(2)). 그래서 "짧은 쓰기"도 처리해야 한다.
- glibc의 `signal()` 함수는 기본으로 BSD 방식, 즉 `SA_RESTART`로 핸들러를 단다(signal(2)). 조건은 기능 테스트 매크로 `_DEFAULT_SOURCE`(glibc 2.19 이전은 `_BSD_SOURCE`)가 정의된 것이다. 기본으로 정의되지만, 없으면 System V 방식이다. `sigaction()`에 플래그를 안 주면 `SA_RESTART`가 없다.
- 로컬 재현: 파이프 `read` 중 1초 뒤 `SIGALRM`.
  - `SA_RESTART` 없음 → `read=-1 errno=Interrupted system call`.
  - `SA_RESTART` 있음 → 계속 기다렸다가 2초 뒤 데이터 2바이트를 받았다.
  - strace에는 `read(...) = ? ERESTARTSYS (To be restarted if SA_RESTART is set)`가 보였다. `ERESTARTSYS`는 커널 내부 값이고 앱에는 안 보인다.

### strace는 어떻게 보나

```text
  strace (tracer) --ptrace--> 대상 프로세스
       대상이 시스템 콜에 들어갈 때 멈춤 -> strace가 레지스터를 읽어 출력 -> 재개
       대상이 시스템 콜에서 나올 때 멈춤 -> 반환값 출력 -> 재개
```

- 시스템 콜마다 tracer와 문맥 전환이 여러 번 생긴다. 그래서 느리다.
- 로컬 재현: 1바이트 write 100만 번이 0.18s → `strace` 붙이면 19.8s(약 100배, 예시).
- Ubuntu 기본 Yama `ptrace_scope=1`에서는 일반 사용자가 기본적으로 **자기 자손**에만 attach할 수 있다(Yama.rst). 예외: 대상이 `prctl(PR_SET_PTRACER, ...)`로 디버거를 지정했으면 자손이 아니어도 된다. 그 밖의 프로세스에 `strace -p`하려면 권한(`CAP_SYS_PTRACE`)이 필요하다.

## 쓰이는 자료구조·알고리즘

- **시스템 콜 테이블 = 번호로 찾는 배열** — 번호가 인덱스다. 목록의 정본은 arch/x86/entry/syscalls/syscall_64.tbl이다(0 read, 1 write, 56 clone, 57 fork, 59 execve, 61 wait4, 435 clone3). [data-structure/01-dynamic-array](../../data-structure/01-dynamic-array/2-summary.md)
  - 오랫동안 x86-64는 `sys_call_table[nr]` 함수 포인터 배열로 **간접 호출**했다.
  - 2024-04 커밋 1e3ad78334a6("x86/syscall: Don't force use of indirect calls for system calls", 리눅스 6.9 개발 주기)부터 같은 표에서 **`switch` 문**(`x64_sys_call`)을 만들어 분기한다. 간접 분기를 노리는 투기 실행 공격(BHI)을 줄이려는 것이다. 배열은 추적용으로 남아 있다(syscall_64.c 주석).
  - 번호 검사 뒤 `array_index_nospec()`로 한 번 더 막는다. 투기 실행 중 범위 밖 인덱스를 쓰지 못하게 하는 것이다.
- **버퍼링 = 일괄 처리(batching)** — 작은 요청을 모아 고정 비용을 나눈다. stdio 버퍼, `writev`, 로그 appender 버퍼가 모두 이것이다.
- **링 버퍼로 호출 자체를 줄이기** — io_uring은 제출·완료 링을 공유 메모리에 둬 시스템 콜 횟수를 줄인다(34번).

## 적용 — 풀어나가는 법

### 1. 무엇을 얼마나 부르는지 본다 — strace

```bash
# 요약: 시스템 콜별 호출 수·에러 수·시간 (자식 포함 -f)
strace -c -f ./prog

# 파일·네트워크 관련만, 각 호출 소요 시간(-T)·시각(-tt)·fd 경로 해석(-y)
strace -f -tt -T -y -e trace=%file,%net -o trace.out ./prog

# 실패한 호출만
strace -f -Z ./prog

# 실행 중인 프로세스에 붙이기 (권한 필요할 수 있음) — 짧게 보고 뗀다
timeout 5 strace -c -f -p <pid>
```

- 운영 서버에서는 **짧게** 붙인다. 시스템 콜이 많은 프로세스는 수십~100배 느려질 수 있다(위 재현).
- `-c`의 시간 합계에는 추적 오버헤드가 섞인다. 호출 **수**를 먼저 믿는다.

### 2. 작은 호출을 묶는다

C — 한 번에 모아 쓴다.

```c
/* 나쁨: 줄마다 write */
for (int i = 0; i < n; i++) write(fd, lines[i], lens[i]);

/* 좋음: 여러 버퍼를 시스템 콜 한 번에 */
struct iovec iov[64];
/* ... iov[i].iov_base = lines[i]; iov[i].iov_len = lens[i]; */
writev(fd, iov, cnt);
```

Java — 바이트 단위 `write`가 곧 시스템 콜이 되는 스트림에는 버퍼를 끼운다.

```java
try (var out = new BufferedOutputStream(new FileOutputStream("out.log"))) {
    for (byte b : data) out.write(b);   // 버퍼에 쌓였다가 한 번에 write
}
```

- `FileOutputStream.write(int)`는 버퍼가 없다. 바이트마다 네이티브 쓰기를 한다.

### 3. `EINTR`와 짧은 쓰기를 처리한다 (C)

```c
ssize_t write_all(int fd, const char *p, size_t n) {
    while (n > 0) {
        ssize_t w = write(fd, p, n);
        if (w < 0) {
            if (errno == EINTR) continue;   /* 시그널: 다시 */
            return -1;                      /* 진짜 에러 */
        }
        p += w; n -= w;                     /* 짧은 쓰기: 나머지 */
    }
    return 0;
}
```

- `poll`·`epoll_wait`·`nanosleep`은 `SA_RESTART`여도 `EINTR`가 나니 루프가 필요하다.
- 런타임이 이 루프를 대신 하는 경우가 많다.
  - OpenJDK NIO 네이티브 코드는 `EINTR`를 예외로 던지지 않고 `IOS_INTERRUPTED`로 돌려준다(src/java.base/unix/native/libnio/ch/IOUtil.c `convertReturnVal`). Java 쪽은 `while (n == IOStatus.INTERRUPTED && isOpen())`로 다시 부른다(sun/nio/ch/FileChannelImpl.java).
  - libuv(Node)도 `while (r == -1 && errno == EINTR)` 루프를 쓴다(src/unix/core.c).
  - 그래서 Java·Node 앱 코드에서는 `EINTR`가 거의 드러나지 않는다. C·Go의 cgo·직접 작성한 네이티브 코드에서 주로 문제가 된다.

### 4. 시스템 콜 비용이 문제인지 판단한다

- `vmstat 1`의 `sy`, `pidstat -u`의 `%system`이 높은가(01번).
- `strace -c`의 호출 수가 초당 수십만 단위인가.
- 둘 다 그렇다면 버퍼링·배치·`sendfile`·io_uring 같은 "호출 줄이기"가 해법이다.

## 장애 시나리오와 대처

### 1. 작은 `write` 반복 → sys CPU 급등

- **현상**: 트래픽은 그대로인데 CPU가 치솟는다. 특히 로그를 많이 쓰는 경로다.
- **보이는 형태**
  - `vmstat`의 `sy`, `pidstat`의 `%system`이 `%usr`보다 크다.
  - `strace -c`에서 `write`가 수십만~수백만 번. 호출당 크기는 `-c`에 안 나오니 `strace -e trace=write`의 인자·반환값으로 본다(수 바이트씩).
- **원인**: 버퍼 없는 출력. 줄마다(또는 바이트마다) `write` 시스템 콜을 부른다. 모드 전환 고정 비용이 데이터 처리보다 커진다.
- **대처**
  - 버퍼링(stdio, `BufferedOutputStream`, 로그 프레임워크의 버퍼·비동기 appender).
  - 여러 조각은 `writev`로 한 번에.
  - 바로 디스크에 닿아야 하는 로그는 버퍼링과 `fsync` 정책을 따로 정한다(24번).

### 2. `EINTR` 미처리 → 간헐 실패

- **현상**: 평소엔 잘 되다가 가끔 I/O가 실패한다. 재현이 어렵다.
- **보이는 형태**: 로그 `read failed: Interrupted system call`, errno 4.
- **원인**
  - 프로세스가 시그널 핸들러를 갖고 있다(예: `SIGCHLD`로 자식 회수, 타이머 `SIGALRM`, 창 크기 `SIGWINCH`).
  - 블록 중인 호출이 그 시그널에 끊겼다. 핸들러가 `SA_RESTART` 없이 달렸거나, `poll`·`nanosleep`처럼 재시작 안 되는 호출이다.
  - 시그널이 오는 순간과 겹칠 때만 나서 "간헐적"이다.
- **대처**
  - 호출을 `EINTR` 재시도 루프로 감싼다.
  - 핸들러는 `SA_RESTART`로 단다. 단 재시작 안 되는 호출 목록(signal(7))은 여전히 루프가 필요하다.
  - 타임아웃이 걸린 대기(`poll`)면 남은 시간을 다시 계산해 부른다.

### 3. 짧은 쓰기를 성공으로 오인 → 데이터 잘림

- **현상**: 파이프·소켓으로 보낸 데이터 끝부분이 가끔 없다.
- **보이는 형태**: 에러 로그 없음. 받는 쪽에서 파싱 실패·잘린 메시지.
- **원인**: `write`가 요청보다 적은 바이트를 쓰고 성공했다. 시그널이 전송 중간에 왔거나 버퍼 공간이 부족했다(write(2)). 코드는 반환값을 확인하지 않았다.
- **대처**: 반환값만큼 진행하고 나머지를 다시 쓴다(`write_all`). 논블로킹 소켓이면 `EAGAIN`에서 멈추고 쓰기 가능 이벤트를 기다린다(25번).

### 4. 운영 중 `strace`로 서비스 지연

- **현상**: 원인 조사를 위해 `strace -p`를 붙였더니 응답 시간이 폭증했다.
- **보이는 형태**: 지연 지표 급등, strace를 떼면 회복.
- **원인**: ptrace는 시스템 콜마다 대상 프로세스를 멈추고 tracer로 문맥을 바꾼다. 시스템 콜이 많은 프로세스일수록 느려진다(로컬 재현 약 100배).
- **대처**
  - `-c`로 짧게(`timeout 5`) 보고 뗀다. `-e trace=`로 범위를 좁힌다.
  - 가능하면 한 인스턴스만 트래픽에서 빼고 붙인다.
  - 오버헤드가 작은 커널 추적(eBPF 도구, `perf trace`)은 권한이 필요하다. 이 환경은 `perf_event_paranoid=4`라 일반 사용자에게 막혀 있다.

## 핵심 문장

- 시스템 콜은 번호(rax)와 인자(rdi·rsi·rdx·r10·r8·r9)를 들고 `syscall` 명령으로 커널에 들어가, 번호로 핸들러를 찾아 실행하고 rax로 결과를 돌려받는 창구다.
- 커널은 실패를 음수로 돌려주고, 대부분의 libc 래퍼가 그것을 `errno`와 -1로 바꾼다. 래퍼 이름과 실제 시스템 콜은 다를 수 있다(`fork()` → `clone`).
- 시스템 콜 한 번에는 모드 전환 고정 비용이 있어서(로컬 약 100ns, 함수 호출의 약 100배), 작은 호출을 많이 하면 sys CPU가 치솟는다. 해법은 버퍼링·배치다.
- 시그널이 블록 중인 호출을 끊으면 `SA_RESTART`에 따라 재시작되거나 `EINTR`로 실패한다. `poll`·`nanosleep` 등은 핸들러에 끊기면 (seccomp 알림 대기 같은 드문 경우를 빼고) `SA_RESTART`와 상관없이 `EINTR`다.
- strace는 ptrace로 호출마다 멈춰 보므로 수십~100배 느려질 수 있다. 운영에서는 짧게 쓴다.

## 관련 주제·근거

- 선행: [01-kernel-and-user-mode](../01-kernel-and-user-mode/2-summary.md) — 유저/커널 모드와 세 개의 문
- 후속
  - [03-interrupts-traps-faults](../03-interrupts-traps-faults/2-summary.md) — 시스템 콜은 "트랩"의 한 종류
  - [05-fork-exec-wait](../05-fork-exec-wait/2-summary.md) — 프로세스를 만드는 시스템 콜들
  - [06-signals](../06-signals/2-summary.md) — `EINTR`의 원인인 시그널 핸들러.
  - [25-io-models](../25-io-models/2-summary.md) — 논블로킹 호출과 `EAGAIN`.
  - [31-os-observability-tools](../31-os-observability-tools/2-summary.md) — strace·perf·/proc.
  - [34-zero-copy-and-io-uring](../34-zero-copy-and-io-uring/2-summary.md) — 호출 횟수 자체를 줄이는 방법.
  - [network/23-socket-api](../../network/23-socket-api/2-summary.md) — 소켓 시스템 콜들
- 교재
  - OSTEP 6장 Limited Direct Execution — 6.2 시스템 콜·트랩, 측정 곁글(1996년 약 4µs) <https://pages.cs.wisc.edu/~remzi/OSTEP/cpu-mechanisms.pdf>
  - CS:APP 3판 8.1 Exceptions(트랩과 시스템 콜)
- man
  - intro(2) — 래퍼의 역할, 음수 에러 → errno <https://man7.org/linux/man-pages/man2/intro.2.html>
  - syscalls(2) — 시스템 콜 목록, syscall(2) — 아키텍처별 호출 규약 표 <https://man7.org/linux/man-pages/man2/syscall.2.html>
  - signal(7) — "Interruption of system calls and library functions by signal handlers" <https://man7.org/linux/man-pages/man7/signal.7.html>
  - signal(2) — glibc `signal()`의 BSD 방식(`SA_RESTART`) · write(2) — 짧은 쓰기 · vdso(7) · getcpu(2) · fork(2) · clock_nanosleep(2) · seccomp_unotify(2) · setbuf(3)
  - strace(1) — `-c`·`-f`·`-T`·`-y`·`-Z`·`-e trace=%file`
- Linux 소스(master)
  - arch/x86/entry/entry_64.S — `entry_SYSCALL_64` 주석(레지스터 규약, rcx·r11)
  - arch/x86/entry/syscall_64.c — `do_syscall_64`, `x64_sys_call`(switch), `array_index_nospec`, sysret/iret 선택(v6.19·v7.0에서 확인. v6.12는 common.c)
  - arch/x86/Makefile — `-fno-jump-tables`(IBT·retpoline 설정)
  - arch/x86/entry/syscalls/syscall_64.tbl — 번호 표
  - 커밋 1e3ad78334a6 (2024-04-08) "x86/syscall: Don't force use of indirect calls for system calls"
  - Documentation/admin-guide/LSM/Yama.rst — `ptrace_scope`
- OpenJDK src/java.base/unix/native/libnio/ch/IOUtil.c(`IOS_INTERRUPTED`) · sun/nio/ch/FileChannelImpl.java(재시도 루프) · libuv src/unix/core.c(EINTR 루프)
- 로컬 재현(리눅스 7.0.0, glibc 2.39, strace 6.8): glibc `write` 디스어셈블, 함수/vDSO/getppid/write 비용 측정, 1바이트 write vs stdio(user/sys, 호출 수), vDSO가 strace에 안 잡힘, SA_RESTART 유무별 EINTR, strace 오버헤드(약 100배), `fork()`→`clone`·`posix_spawn()`→`clone3`
