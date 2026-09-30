# os/01-kernel-and-user-mode — 프로그램은 CPU를 "직접" 쓰되, 선을 넘으면 커널이 막는다 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> ⚠️ 이 서머리는 Claude 초안(2026-09-30) — 근거는 아래 「관련 주제·근거」. 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 해결하는 문제

한 컴퓨터에서 여러 프로그램이 CPU·메모리·디스크를 같이 쓴다.\
프로그램이 하드웨어를 마음대로 만질 수 있으면 이런 일이 생긴다.

```text
  프로그램이 할 수 있다면              결과
  다른 프로그램 메모리에 쓰기           남의 데이터가 깨진다
  디스크 컨트롤러에 직접 명령           파일 시스템이 깨진다
  인터럽트 끄기(cli)                    타이머가 안 울려 CPU를 영원히 독점
  페이지 테이블 주소(CR3) 바꾸기         아무 메모리나 다 보인다
```

OS가 할 일은 두 가지다.
- 프로그램을 **빠르게** 돌린다. 매 명령을 OS가 흉내 내면(인터프리트) 너무 느리다.
- 그러면서도 **통제권**을 쥔다. 위 표의 일은 막고, CPU는 언제든 되찾는다.

답은 **제한된 직접 실행(limited direct execution)** 이다(OSTEP 6장).
- 프로그램 명령은 CPU가 직접 실행한다(빠름).
- 대신 CPU에 "권한 모드"를 두어, 위험한 명령은 하드웨어가 거부한다(제한).
  - *제한된 직접 실행*: 평소엔 프로그램이 CPU 위에서 그대로 돌고, 위험한 일은 커널을 거쳐야만 하도록 하드웨어가 막는 방식이다.

쉬운 예: 은행이다.
- 손님(프로그램)은 로비에서 자유롭게 움직인다(직접 실행).
- 금고(하드웨어)에는 못 들어간다. 창구(시스템 콜)에 요청하면 직원(커널)이 대신 꺼내 준다.
- 손님이 너무 오래 창구를 붙잡으면 번호표 기계(타이머)가 다음 손님을 부른다.

똑같은 구조다.\
유저 모드 = 로비, 커널 모드 = 금고 안, 시스템 콜 = 창구, 타이머 인터럽트 = 번호표.

실무 예:
- Java·Node 서버도 유저 모드 프로세스다. 파일을 읽거나 소켓에 쓸 때마다 커널로 들어갔다 나온다.
- 컨테이너는 VM이 아니다. 모든 컨테이너가 **같은 커널** 위에서 유저 모드로 돈다.
- `root` 로 돌려도 유저 모드다. root는 커널이 확인하는 "권한 신원"이고, CPU 모드와는 다른 층이다.

## 동작·원리

### 두 모드와 세 개의 문

```text
  +---------------------------------------------------------+
  |  유저 모드 (x86: ring 3)                                  |
  |   앱 코드, JVM, Node, libc                                |
  |   - 자기 메모리만 접근                                     |
  |   - 특권 명령 실행 불가                                    |
  +------------+-----------------+-------------------+------+
               |                 |                   |
        (1) 시스템 콜        (2) 예외            (3) 인터럽트
        syscall 명령        0으로 나눔,          타이머, 디스크,
        "부탁합니다"         페이지 폴트,         NIC 패킷 도착
                            특권 명령 시도
               |                 |                   |
               v                 v                   v
  +---------------------------------------------------------+
  |  커널 모드 (x86: ring 0)                                  |
  |   - 모든 메모리·모든 명령                                  |
  |   - 부팅 때 등록한 핸들러로만 들어온다 (트랩 테이블)          |
  +---------------------------------------------------------+
               |
          return-from-trap (sysret / iret)
               v
          다시 유저 모드
```

- 유저 모드에서 커널 모드로 가는 길은 이 세 개뿐이다. 셋 다 **커널이 미리 정해 둔 입구**로만 들어간다.
- (1)은 프로그램이 원해서, (2)는 명령 실행의 결과로, (3)은 CPU 밖의 사건으로 들어간다. 자세한 차이는 03번.
  - *ring(보호 링)*: x86의 권한 등급이다. 0이 가장 강하고 3이 가장 약하다. 리눅스는 0(커널)과 3(유저)만 쓴다.
  - *CPL(Current Privilege Level)*: 지금 CPU가 몇 번 링에서 도는지다. x86-64에서는 CS 레지스터의 하위 2비트다.

로컬에서 확인한 값(예시, 리눅스 7.0, x86-64):

```text
  유저 프로그램에서 CS 읽기 → cs=0x33 → CPL = 0x33 & 3 = 3
```

- 리눅스 소스의 `__USER_CS` = 6×8 + 3 = 0x33이다. 끝의 +3이 ring 3이다. `__KERNEL_CS` = 2×8 = 0x10, ring 0이다(arch/x86/include/asm/segment.h).
- 참고로 ARM64는 링 대신 예외 레벨을 쓴다. 리눅스 arm64는 "유저 모드 = EL0"으로 판정하고(arch/arm64/include/asm/ptrace.h `user_mode()`), 커널은 보통 EL1에서 돈다(가상화 확장 VHE를 쓰면 EL2에서도 돈다).

### 제한된 직접 실행 — 시간 순서

OSTEP 6장의 프로토콜을 줄인 것이다.

```text
  시간 ↓     하드웨어                     커널 (커널 모드)                 프로그램 (유저 모드)
  부팅       .                            트랩 테이블 등록
                                          타이머 시작
  실행 시작  .                            프로세스 만들고 메모리 준비
                                          return-from-trap  ------->
             유저 모드로 전환, main()으로                                   main() 실행
  시스템 콜  .                                                   <------- syscall
             커널 모드로 전환,
             레지스터를 커널 스택에 저장,
             트랩 테이블의 핸들러로 점프
             (OSTEP의 일반화 — x86-64 실제는 아래 참고)
                                          요청 처리
                                          return-from-trap  ------->
             레지스터 복원, 유저 모드로                                     다음 명령 계속
  타이머     타이머 인터럽트 발생           스케줄러: 계속 돌릴까? 바꿀까?
```

- x86-64 `syscall` 명령의 실제 분담은 조금 다르다. CPU는 복귀 주소·플래그를 RCX·R11에 넣고, MSR(`IA32_LSTAR`)에 적힌 주소로 점프만 한다. 스택 전환과 레지스터 저장은 커널 진입 코드(`entry_SYSCALL_64`)가 한다(entry_64.S 주석 "SYSCALL does not save anything on the stack").
- **트랩 테이블**은 부팅 때 커널이 등록한다(리눅스 x86은 CPU마다 `lidt`로 적재한다). 등록 명령 자체가 특권 명령이다. 그래서 유저 프로그램이 자기 핸들러를 끼워 넣을 수 없다.
- **타이머 인터럽트**가 핵심이다. 프로그램이 시스템 콜을 한 번도 안 불러도(무한 루프) 커널이 CPU를 되찾는다.
  - 타이머가 없던 옛 방식은 *협력형(cooperative)* 이었다. 프로그램이 양보해 줘야만 OS가 돌았다. 무한 루프 하나면 재부팅뿐이었다(OSTEP 6.3).
- 이 로컬 커널은 `CONFIG_HZ=1000`이다(예시). 틱이 1ms 간격이라는 뜻이다. 단 `NO_HZ` 설정이면 한가한 CPU는 틱을 멈출 수 있다. `nohz_full=`로 지정한 CPU는 실행할 태스크가 하나뿐일 때 돌고 있는 중에도 틱을 거의 생략한다(docs.kernel.org timers/no_hz).

### 특권 명령을 유저 모드에서 실행하면

로컬 재현(예시, 리눅스 7.0, i7-13700HX). 각 명령을 유저 프로그램에서 인라인 어셈블리로 실행했다.

```text
  명령            무엇을 하나                 CPU 예외        커널이 보내는 시그널      셸 exit code
  hlt             CPU 정지                   #GP(13)         SIGSEGV (si_code=128)     139
  cli             인터럽트 끄기               #GP(13)         SIGSEGV                   139
  outb            I/O 포트 쓰기               #GP(13)         SIGSEGV                   139
  mov %cr3,..     페이지 테이블 주소 읽기       #GP(13)         SIGSEGV                   139
  ud2             "정의 안 된 명령"(일부러)     #UD(6)          SIGILL  (si_code=2)       132
  커널 주소 읽기   0xffffffff81000000 load     #PF(14)         SIGSEGV (si_code=1)       139
```

- 특권 명령 위반은 x86에서 대개 **#GP(일반 보호 예외)** 가 된다. 커널은 유저 모드에서 난 #GP에 `SIGSEGV`를 보낸다(arch/x86/kernel/traps.c `exc_general_protection` → `gp_user_force_sig_segv` → `force_sig(SIGSEGV)`).
  - 그래서 "특권 명령 = SIGILL"이 아니다. x86 리눅스에서는 대부분 **SIGSEGV** 다.
  - si_code=128은 `SI_KERNEL`이다. "커널이 직접 보냈다"는 뜻이다.
- CPU가 **모르는 명령**(#UD)이면 `SIGILL`이다(traps.c `handle_invalid_op` → `SIGILL, ILL_ILLOPN`). si_code=2가 `ILL_ILLOPN`이다.
- 커널 주소는 페이지 테이블에서 "커널 전용(supervisor)" 표시가 있다. 유저 모드 접근은 페이지 폴트가 되고 `SIGSEGV`로 끝난다.
- 셸의 exit code는 "128 + 시그널 번호"다(bash(1)). SIGSEGV=11 → 139, SIGILL=4 → 132.
- 커널 로그에는 `traps: priv[1234] general protection fault ip:... sp:... error:0 in priv[...]` 형태가 남는다(traps.c `show_signal`, `pr_fmt`). 단 `show_unhandled_signals`가 켜져 있고, 프로세스가 그 시그널을 처리하지 않을 때만 남는다. 이 환경은 `dmesg_restrict=1`이라 일반 사용자는 못 본다.

경계 사례: **모든 특권성 명령이 즉시 죽는 것은 아니다.**
- `sgdt`(GDT 주소 읽기)는 UMIP가 켜진 CPU(지원 CPU에서 커널이 `CR4.UMIP`를 설정, common.c `setup_umip`)에서 유저 모드 실행 시 #GP가 난다. 리눅스는 이를 **가로채 흉내 내고** 가짜 값을 돌려준다(traps.c `fixup_umip_exception`).
  - 로컬 재현: `sgdt` → 프로세스는 살고 base=0xfffffffffffe0000, limit=0을 받았다(예시).
  - *UMIP(User-Mode Instruction Prevention)*: 커널 구조 주소를 새게 하는 몇몇 명령을 유저 모드에서 막는 x86 기능이다.
- root가 `ioperm()`/`iopl()`로 I/O 포트 권한을 얻으면 `in`/`out`이 유저 모드에서도 된다(ioperm(2), `CAP_SYS_RAWIO` 필요). 이때도 CPU는 여전히 ring 3이다.

### root ≠ 커널 모드

```text
  층            무엇이 판단하나           예
  CPU 모드       하드웨어 (CPL)            hlt·cli는 ring 3이면 root여도 #GP
  권한 신원       커널 코드 (uid·capability) open("/etc/shadow")는 보통 root면 허용
                                            (SELinux 같은 LSM은 root도 막을 수 있다)
```

- 커널은 시스템 콜 안에서 uid·capability를 보고 허락할지 정한다. 이것은 **소프트웨어 검사**다.
- CPU 모드 검사는 **하드웨어 검사**다. 유저 모드에서 root가 `hlt`를 실행해도 CPU가 거부한다. (root로 실행하는 재현은 하지 않았다. 판단 근거는 CPL 검사가 uid를 모른다는 구조다.)

### 커널 안에서 보낸 시간 = sys

```text
  time ./prog
  real 0.41   벽시계 시간
  user 0.06   유저 모드에서 CPU를 쓴 시간
  sys  0.35   커널 모드에서 CPU를 쓴 시간 (이 프로세스를 위해)
```

- 위는 1바이트 `write()`를 100만 번 부른 프로그램이다(예시, 로컬 재현). 대부분의 시간이 커널 안이다. 이유는 02번.

## 쓰이는 자료구조·알고리즘

- **트랩 테이블 = 번호로 찾는 함수 포인터 배열** — 예외·인터럽트 번호(벡터)가 곧 인덱스다. x86의 IDT는 벡터 번호로 항목을 찾는다. 0 = 나눗셈 오류, 6 = 모르는 명령, 13 = 일반 보호, 14 = 페이지 폴트다(arch/x86/include/asm/trapnr.h). 배열 인덱싱이라 O(1)이다. [data-structure/01-dynamic-array](../../data-structure/01-dynamic-array/2-summary.md)
  - 최근 x86 CPU·커널에는 IDT 대신 FRED라는 새 진입 방식도 있다(`CONFIG_X86_FRED`). 이 로컬 CPU에는 해당 플래그가 없었다.
- **모드 비트 = 1비트짜리 상태 기계** — 유저 ↔ 커널 전환은 정해진 문(트랩·인터럽트·return-from-trap)으로만 일어난다. 임의 점프로는 바뀌지 않는다.
- **페이지 테이블의 U/S 비트** — 페이지마다 "유저 접근 가능?"을 1비트로 기록한다. 메모리 보호가 모드와 만나는 지점이다(10번에서 자세히).

## 적용 — 풀어나가는 법

### 1. 프로세스가 어느 모드에서 시간을 쓰는지 본다

```bash
# 한 번 실행하고 user/sys 비교
/usr/bin/time -f "real %e user %U sys %S" ./prog

# 실행 중인 프로세스: 초당 %usr·%system
pidstat -u -p <pid> 1

# 시스템 전체: us(유저) sy(커널) wa(I/O 대기)
vmstat 1

# 누적 값: /proc/<pid>/stat 의 14번째(utime)·15번째(stime) 필드, 단위는 clock tick
# 2번째 필드 (comm)에 공백·괄호가 들어갈 수 있어, 마지막 ") "까지 잘라 낸 뒤 센다(3번째가 $1)
sed 's/.*) //' /proc/<pid>/stat | awk '{print "utime="$12, "stime="$13}'
```

- `sy`가 `us`보다 크면 "커널에 너무 자주 들어간다"는 신호다. 흔한 원인은 작은 시스템 콜 반복(02번), 페이지 폴트(03번)다.

### 2. 크래시가 CPU 예외에서 왔는지 본다

- exit code 139(SIGSEGV)·132(SIGILL)·136(SIGFPE)·133(SIGTRAP)은 "CPU 예외 → 커널 → 시그널" 경로에서 자주 나온다.
- JVM이면 `hs_err_pid<pid>.log` 머리 부분(`# A fatal error has been detected ...` 다음 줄)에 `SIGSEGV (0xb)`·`SIGILL (0x4)` 같은 시그널이 적힌다.
- C 코드에서 원인 주소·종류를 보려면 `SA_SIGINFO` 핸들러로 `si_code`·`si_addr`를 찍는다.

```c
static void put_hex(unsigned long v) {        /* 숫자 → 16진 문자열, 안전한 연산만 */
    char b[16]; int i = sizeof b;
    do { b[--i] = "0123456789abcdef"[v & 15]; v >>= 4; } while (v);
    write(2, b + i, sizeof b - i);
}
static void h(int sig, siginfo_t *info, void *uc) {
    /* printf·snprintf는 async-signal-safe 목록에 없다 → write + 직접 변환 (06번, signal-safety(7)) */
    write(2, "sig=0x", 6);        put_hex(sig);
    write(2, " si_code=0x", 11);  put_hex((unsigned)info->si_code);
    write(2, " addr=0x", 8);      put_hex((unsigned long)info->si_addr);
    write(2, "\n", 1);
    _exit(128 + sig);
}
/* struct sigaction sa = { .sa_sigaction = h, .sa_flags = SA_SIGINFO }; sigaction(SIGSEGV, &sa, 0); */
```

### 3. "권한 문제"가 어느 층인지 가른다

- `EPERM`/`EACCES` errno가 났다 → 커널의 **소프트웨어 권한 검사**(uid·capability·seccomp)다. CPU 모드 문제가 아니다.
- `SIGSEGV`/`SIGILL`로 죽었다 → 대개 **CPU 예외**가 먼저다. root·privileged로 바꾸는 것만으로는 고쳐지지 않는다(예외: I/O 포트는 코드가 `ioperm()`으로 권한을 받으면 된다).
  - `kill`·`raise`로 보낸 시그널일 수도 있다. `si_code`가 `SI_USER`(0)·`SI_TKILL`(-6)이면 CPU 예외가 아니다(sigaction(2)).

## 장애 시나리오와 대처

### 1. 특권 명령·커널 주소 접근 → `SIGSEGV`(exit 139)

- **현상**: 네이티브 코드가 들어간 프로세스가 특정 경로에서 즉시 죽는다.
- **보이는 형태**
  - 셸 `Segmentation fault (core dumped)`, exit 139. 쿠버네티스 컨테이너면 종료 코드 139.
  - 커널 로그(권한 있으면) `traps: <comm>[pid] general protection fault ...`.
- **원인**
  - 유저 모드 코드가 특권 명령(`hlt`·`cli`·`in/out`·제어 레지스터 접근)을 실행했다.
  - 또는 커널 영역 주소를 역참조했다(잘못된 포인터).
  - x86 리눅스에서 특권 명령 위반은 #GP → `SIGSEGV`이지 `SIGILL`이 아니다.
- **대처**
  - 코어 덤프를 `gdb`로 열어 크래시 명령을 본다(`x/i $pc`).
  - 하드웨어를 직접 만지려는 코드라면 커널 드라이버나 시스템 콜 인터페이스로 바꾼다.

### 2. 다른 CPU에서 빌드한 바이너리 → `SIGILL`(exit 132)

- **현상**: 개발 머신에선 되는데, 특정 서버·노드로 옮기면 시작하자마자 죽는다.
- **보이는 형태**: `Illegal instruction (core dumped)`, exit 132.
- **원인**
  - `-march=native` 같은 옵션으로 새 CPU 명령(예: AVX-512)을 쓰게 빌드했다.
  - 옛 CPU는 그 명령을 모른다 → #UD → `SIGILL`.
  - 특권 문제가 아니라 "명령 집합이 다르다"는 문제다.
- **대처**
  - `grep -o -w avx512f /proc/cpuinfo`처럼 대상 CPU 플래그를 확인한다.
  - 배포 대상의 최소 CPU에 맞춰 빌드하거나, 실행 시점에 CPU 기능을 확인해 분기하는 라이브러리를 쓴다.

### 3. `sys` 시간이 비정상적으로 높다

- **현상**: CPU 사용률은 높은데 애플리케이션 프로파일러에는 뜨거운 함수가 안 보인다.
- **보이는 형태**: `vmstat`의 `sy`, `pidstat`의 `%system`이 `%usr`보다 크다.
- **원인**: 커널 모드에서 시간을 쓴다. 작은 시스템 콜 반복, 페이지 폴트 폭주, 락 경합의 futex 호출 등이다.
- **대처**: `strace -c`로 시스템 콜 분포를 보고(02번), `pidstat -r`로 폴트를 본다(03번).

### 4. "root로 돌리면 되겠지"

- **현상**: 하드웨어 접근 코드가 실패하자 컨테이너를 `privileged`·root로 바꿨는데도 여전히 죽는다.
- **보이는 형태**: 여전히 `SIGSEGV`.
- **원인**: root는 커널의 소프트웨어 권한이다. CPU 모드는 여전히 ring 3이라 특권 명령은 CPU가 거부한다.
- **대처**
  - 필요한 기능을 제공하는 시스템 콜·장치 파일을 쓴다.
  - I/O 포트라면 `ioperm(2)`(`CAP_SYS_RAWIO`)이 있지만, 권한을 넓히는 일이라 마지막 수단이다.

## 핵심 문장

- 제한된 직접 실행: 프로그램은 CPU에서 직접 돌고, 위험한 명령과 자원 접근은 하드웨어 모드 검사로 막는다.
- 유저 → 커널 전환은 시스템 콜·예외·인터럽트 세 문으로만 일어나고, 모두 부팅 때 커널이 등록한 입구(트랩 테이블 — x86-64에선 IDT와 `syscall`용 MSR)로 들어간다.
- 타이머 인터럽트가 있어서 협조하지 않는 프로그램에게서도 커널이 CPU를 되찾는다.
- x86 리눅스에서 유저 모드의 특권 명령은 #GP → `SIGSEGV`(139), 모르는 명령은 #UD → `SIGILL`(132)이다.
- root는 커널이 판단하는 권한이고, ring 3/ring 0은 CPU가 판단하는 모드다. 둘은 다른 층이다.

## 관련 주제·근거

- 선행: architecture/09-isa-and-machine-code — 원고 [foundations/hardware-basics](../../foundations/hardware-basics/README.md) §3 CPU 내부 구조·§9 인스트럭션 세트. 영역 표 [architecture/README](../../architecture/README.md)
- 후속
  - [02-system-calls](../02-system-calls/2-summary.md) — 첫 번째 문: 시스템 콜 경로와 비용
  - [03-interrupts-traps-faults](../03-interrupts-traps-faults/2-summary.md) — 세 문의 차이, 예외 벡터
  - [06-signals](../06-signals/2-summary.md) — 커널이 보낸 시그널을 프로세스가 받는 법.
  - [10-paging-and-tlb](../10-paging-and-tlb/2-summary.md) — U/S 비트가 있는 페이지 테이블.
  - [35-virtualization-hypervisor](../35-virtualization-hypervisor/2-summary.md) — 커널 아래 한 층 더(하이퍼바이저).
- 교재
  - OSTEP 2장 Introduction, 6장 Mechanism: Limited Direct Execution(6.1 기본 기법, 6.2 제한된 연산·트랩 테이블, 6.3 협력형 vs 타이머 인터럽트) <https://pages.cs.wisc.edu/~remzi/OSTEP/cpu-mechanisms.pdf>
  - CS:APP 3판 8.1 Exceptions (CMU 15-213 강의 자료 "Exceptional Control Flow")
- Linux 소스(master)
  - arch/x86/include/asm/segment.h — `__USER_CS`(×8+3), `__KERNEL_CS`
  - arch/x86/kernel/traps.c — `exc_general_protection`, `gp_user_force_sig_segv`, `handle_invalid_op`(SIGILL/ILL_ILLOPN), `fixup_umip_exception`, `show_signal`
  - arch/x86/include/asm/trapnr.h — 예외 벡터 번호
  - arch/arm64/include/asm/ptrace.h `user_mode()`(EL0) · Documentation/arch/arm64/booting.rst(EL0~EL3, 커널 진입 EL2/EL1)
  - <https://github.com/torvalds/linux/tree/master/arch/x86>
- man: bash(1)(128+n), ioperm(2), sigaction(2)(`si_code`), proc_pid_stat(5)(utime·stime), signal-safety(7), sched(7)(`sched_rt_runtime_us`)
- arch/x86/entry/entry_64.S `entry_SYSCALL_64` 주석(SYSCALL은 RCX·R11에 저장, 스택 안 씀), entry_64_fred.S(`ERETU`), arch/x86/kernel/cpu/common.c `setup_umip` — v6.19
- 커널 문서 <https://docs.kernel.org/timers/no_hz.html>(nohz_full)
- 로컬 재현(리눅스 7.0.0, gcc 13.3): CS=0x33 확인, hlt·cli·outb·mov cr3 → SIGSEGV 139, ud2 → SIGILL 132, 커널 주소 읽기 → SIGSEGV(SEGV_MAPERR), sgdt → UMIP 흉내로 생존, 1바이트 write 100만 번의 user/sys
