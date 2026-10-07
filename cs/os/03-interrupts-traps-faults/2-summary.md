# os/03-interrupts-traps-faults — CPU의 흐름을 끊고 커널로 들어가는 네 가지 사건 — 정리 (힌트)

## 해결하는 문제

CPU는 보통 명령을 하나씩 순서대로 실행한다. 다음 명령이 바로 다음 주소에 있거나, 점프·호출로 정해진다.\
그런데 이 순서만으로는 처리할 수 없는 사건이 있다.

```text
  사건                                  순서대로만 실행하면
  디스크 읽기가 끝났다                   CPU가 끝났는지 계속 물어봐야 한다 (폴링)
  타이머가 울렸다                        무한 루프 프로그램을 멈출 수 없다
  명령이 0으로 나눴다                    결과가 없는데 다음 명령으로 갈 수 없다
  명령이 아직 메모리에 없는 페이지를 읽었다  읽을 데이터가 없다
  프로그램이 커널에 부탁하고 싶다          커널로 들어갈 방법이 없다
```

그래서 CPU는 "지금 흐름을 멈추고, 정해진 커널 코드로 갔다가, 필요하면 돌아오는" 장치를 갖는다.\
이것을 **예외적 제어 흐름(exceptional control flow)** 이라 부른다(CS:APP 8장).
  - *예외적 제어 흐름*: 명령 순서가 아니라 사건 때문에 실행 위치가 바뀌는 것이다.

쉬운 예: 요리 중인 사람이다.
- 초인종이 울린다(인터럽트). 하던 칼질을 마치고 문을 연 뒤, 다음 칼질부터 계속한다.
- 일부러 조수를 부른다(트랩). 부탁하고 나서 다음 단계로 간다.
- 재료가 냉장고에 없다(폴트). 가져온 뒤 **같은 단계를 다시** 한다.
- 가스가 샌다(어보트). 요리를 멈추고 나간다. 돌아오지 않는다.

똑같은 구조다.\
네 가지는 "무엇이 계기인가"와 "끝나고 어디로 돌아가나"가 다르다.

실무 예:
- 배포 직후 첫 요청들이 느리다. 코드·데이터 페이지가 아직 메모리에 없어 페이지 폴트가 쏟아진다.
- NIC 인터럽트가 한 코어에만 몰려 그 코어만 100%다.
- 0으로 나눈 정수 연산으로 프로세스가 exit 136으로 죽는다.

## 동작·원리

### 네 가지 분류

CS:APP 3판 8.1.2의 **예외(exception)** 분류다(CMU 15-213 "Exceptional Control Flow" 강의 자료). 예외적 제어 흐름 전체에는 이 밖에도 문맥 전환·시그널·`setjmp`/`longjmp`가 들어간다.

```text
  종류       계기                        동기/비동기   끝나면 어디로          예
  인터럽트   CPU 밖 장치의 신호            비동기        다음 명령              타이머, 디스크 완료, 패킷 도착
  트랩       명령이 일부러 요청            동기          다음 명령              syscall, int3(중단점)
  폴트       명령 실행 중 고칠 수도 있는 오류  동기        같은 명령 재실행 또는 종료  페이지 폴트, 0으로 나눔, 보호 위반
  어보트     고칠 수 없는 오류             동기          돌아가지 않음           머신 체크(하드웨어 오류)
```

  - *동기(synchronous)*: 지금 실행한 명령 때문에 생긴다. 같은 입력이면 같은 자리에서 다시 생긴다.
  - *비동기(asynchronous)*: 명령과 상관없이 밖에서 생긴다. 어느 명령 사이에 끼어들지 모른다.

돌아가는 위치를 그림으로 보면 이렇다.

```text
  인터럽트·트랩                      폴트 (고칠 수 있을 때)             어보트
  I1 실행 완료                       I1 실행 중 폴트                    I1 실행 중 어보트
     | 사건                             |                                  |
     v                                  v                                  v
  핸들러                             핸들러: 원인 해결                   핸들러: 프로그램 종료
     |                                  |  (예: 페이지를 메모리에 올림)
     v                                  v
  I2 (다음 명령)                     I1 (같은 명령 다시)
```

- 폴트가 "같은 명령을 다시" 하는 이유: 그 명령은 아직 끝나지 못했다. 원인을 고친 뒤 처음부터 다시 해야 한다.
- 고칠 수 없는 폴트(잘못된 주소, 0으로 나눔)라면 커널은 프로세스에 **시그널**을 보낸다. 대개 기본 동작이 종료다(06번).
- 분류는 문헌마다 조금 다르다. CMU 강의 자료는 "illegal instruction"을 어보트 예로 들지만, Intel SDM 3권 표 7-1은 `#UD`(모르는 명령)를 **Fault**로 분류한다. 리눅스는 어느 쪽이든 `SIGILL`을 보낸다.

### x86 예외 번호와 리눅스 시그널

벡터 번호는 arch/x86/include/asm/trapnr.h, 시그널은 arch/x86/kernel/traps.c 기준이다.

```text
  벡터  이름                 유저 모드에서 생기면           로컬 재현 exit code
  0     #DE 나눗셈 오류       SIGFPE (FPE_INTDIV)            136  (정수 10/0)
  3     #BP 중단점            SIGTRAP                        133  (int3)
  6     #UD 모르는 명령       SIGILL (ILL_ILLOPN)            132  (ud2)
  13    #GP 일반 보호          SIGSEGV                        139  (hlt, 01번)
  14    #PF 페이지 폴트        대개 조용히 해결 / 잘못된 주소면 SIGSEGV   139  (NULL 역참조)
  32~   외부 장치 인터럽트     시그널 없음 (커널이 처리)
```

- 0~31번은 CPU 예외용으로 예약된 자리다. 장치 인터럽트는 그 뒤 번호를 쓴다.
- 32비트 호환용 `int 0x80` 시스템 콜도 이 표의 0x80번 항목이다(idt.c `IA32_SYSCALL_VECTOR`).
- 64비트 시스템 콜은 이 표를 거치지 않는다. `syscall` 명령은 MSR에 등록된 진입점(`entry_SYSCALL_64`)으로 바로 간다(entry_64.S 주석). 그래도 분류로는 "트랩"이다.
- 위 두 줄은 FRED가 꺼진 기존 방식이다. FRED가 켜지면 `syscall`·`int 0x80` 모두 FRED 진입점으로 들어가 이벤트 종류로 나뉜다(arch/x86/entry/entry_fred.c `fred_other`·`fred_intx`).
- exit code는 셸의 "128 + 시그널 번호"다(bash(1)).

### 페이지 폴트 — 폴트의 대부분은 오류가 아니다

```text
  load/store 명령
      |
      v
  MMU: 페이지 테이블에 유효한 매핑이 있나?
      |-- 있다 ------------------------------> 그대로 진행 (폴트 없음)
      |-- 없다 -> #PF -> 커널 페이지 폴트 핸들러
                         |
                         |-- 이 주소가 프로세스 영역(VMA) 밖 / 권한 위반
                         |      -> SIGSEGV (진짜 오류)
                         |
                         |-- 영역 안, 필요한 페이지가 이미 메모리에 있거나 새로 만들면 됨
                         |      -> minor fault: 매핑만 채움 (디스크 I/O 없음)
                         |         예: 익명 메모리 첫 쓰기, 페이지 캐시에 있는 파일
                         |
                         |-- 영역 안, 내용을 디스크에서 읽어 와야 함
                                -> major fault: 보통 디스크 I/O 동안 스레드는 잠든다
                                   예: 캐시에 없는 mmap 파일, 스왑된 페이지
                         |
                         v
                  같은 명령 재실행
```

  - *minor fault*: 디스크를 읽지 않고 해결되는 페이지 폴트다.
  - *major fault*: 디스크에서 페이지를 읽어야 하는 폴트다(proc_pid_stat(5) `majflt` "required loading a memory page from disk").
    - 커널 집계는 이것과 딱 일대일은 아니다. 예: 스왑 캐시에 없던 페이지를 zswap(압축 메모리)에서 복원해도 major로 셀 수 있다(mm/memory.c `do_swap_page`의 `VM_FAULT_MAJOR`, mm/page_io.c `zswap_load`).

로컬 재현 — 64MB를 4KB 간격으로 한 바이트씩 건드렸다(예시, 리눅스 7.0, NVMe SSD, THP는 `madvise` 모드라 이 매핑에는 안 쓰임).

```text
  작업                                     minor     major    시간
  익명 메모리 mmap만 하고 안 건드림          0         0        0 ms
  익명 메모리 첫 쓰기 (16384 페이지)        16397     0        24–28 ms
  같은 곳 다시 쓰기                         0         0        0.3–0.4 ms
  파일 mmap 읽기, 캐시 비운 뒤(MADV_RANDOM) 0         16384    294–339 ms
  파일 mmap 읽기, 캐시에 있을 때             1024      0        3–4 ms
```

- `mmap`만 하면(`MAP_POPULATE` 없이) 데이터 페이지를 안 받는다. **처음 건드릴 때** 폴트로 한 장씩 받는다(요구 페이징). VMA 같은 관리용 메모리는 조금 쓴다.
- 매핑과 권한이 그대로인 동안에는 다시 폴트가 나지 않는다. `fork` 뒤 COW 쓰기, 스왑 아웃·회수로 매핑이 빠진 뒤의 접근은 다시 폴트가 난다.
- 캐시를 비운 행은 `MADV_RANDOM`으로 미리 읽기(readahead)를 끈 상태다. 미리 읽기가 켜져 있으면 한 번의 I/O로 여러 페이지가 들어와 major 수가 줄어든다.
- major fault는 minor보다 한 건당 약 10배 이상 느렸다(약 18~20µs vs 약 1.5µs, 이 SSD 기준 예시). HDD라면 차이가 훨씬 크다.
- 캐시에 있는 파일은 1024번이다. 커널이 한 번의 폴트에 주변 페이지 16장(64KB)을 함께 매핑하기 때문이다(mm/memory.c `fault_around_pages` 기본 65536 >> PAGE_SHIFT).
- `/usr/bin/time -v`로 같은 실행을 보면 major 16384번과 **자발적 문맥 전환 16386번**이 같이 찍혔다. 이 재현에서는 major fault마다 스레드가 디스크를 기다리며 잠들었다고 볼 수 있다(수가 맞는다는 정황이지, 일반 규칙은 아니다).

> 참고: 원고 [memory-management](../../foundations/memory-management/README.md) §11은 "페이지 폴트가 발생하면 해당 페이지를 하드에서 가져온다"고 적는다. 이것은 major fault의 설명이다. 익명 메모리 첫 쓰기처럼 디스크 I/O 없이 끝나는 minor fault가 더 흔하다(위 로컬 재현).

### 인터럽트 — 밖에서 오는 신호

```text
  장치 (NIC, 디스크, 타이머)
     | 신호
     v
  인터럽트 컨트롤러 (APIC) --> 한 CPU 코어를 골라 벡터 번호 전달
     v
  그 코어: 현재 명령을 마치고 -> 커널 모드로 -> 벡터의 핸들러
     |
     |  상반부(hard IRQ): 급한 것만 짧게 (장치 확인, 다음 처리 예약)
     |  하반부(softirq 등): 나머지 무거운 처리 (예: 네트워크 NAPI poll)
     v
  원래 프로그램의 다음 명령
```

- 핸들러가 도는 동안 같은 종류의 인터럽트는 막혀 있을 수 있다. 그래서 상반부는 짧게 두고 나머지를 뒤로 미룬다.
- 네트워크 수신의 IRQ → NAPI → softirq 흐름은 [network/25-kernel-network-stack](../../network/25-kernel-network-stack/2-summary.md)에 있다.
- CPU끼리도 인터럽트를 보낸다(IPI). `/proc/interrupts`의 아래 줄들로 볼 수 있다(arch/x86/kernel/irq.c). 단 `LOC`는 IPI가 아니다.
  - `LOC` Local timer interrupts — 코어별 로컬 APIC 타이머(IPI 아님).
  - `RES` Rescheduling interrupts — "다른 코어야, 스케줄러를 돌려라".
  - `CAL` Function call interrupts — 다른 코어에서 함수를 실행시킨다.
  - `TLB` TLB shootdowns — 다른 코어의 TLB 항목을 지우게 한다(10번).
  - *IPI(Inter-Processor Interrupt)*: 한 CPU 코어가 다른 코어에 보내는 인터럽트다.

## 쓰이는 자료구조·알고리즘

- **인터럽트 벡터 테이블 = 번호로 찾는 핸들러 배열** — x86의 IDT다. 사건 번호가 인덱스라 O(1)로 핸들러를 찾는다. [data-structure/01-dynamic-array](../../data-structure/01-dynamic-array/2-summary.md)
  - 최근 x86에는 IDT 대신 FRED라는 새 이벤트 전달 방식도 있다(`CONFIG_X86_FRED`, trapnr.h의 FRED 이벤트 종류). 이 로컬 CPU에는 해당 기능 플래그가 없었다.
- **예외 테이블 = 정렬 배열 + 이진 탐색** — 커널이 유저 메모리를 복사하다가 폴트가 나면, "이 명령 주소에서 난 폴트는 여기로 복구"라는 표를 찾는다. 부팅 때 정렬하고(`sort_extable`), 폴트 때 `bsearch`로 찾는다(kernel/extable.c, lib/extable.c).
- **VMA 탐색** — 페이지 폴트 핸들러는 폴트 주소가 어느 메모리 영역(VMA)에 속하는지 먼저 찾는다. 이 영역들은 maple tree(B-트리 계열)로 관리된다(include/linux/mm_types.h `mm_mt`, 09·10번).
- **상반부/하반부 = 작업 큐로 미루기** — 급한 일만 즉시, 나머지는 큐에 넣어 나중에. 이벤트 루프·워커 큐와 같은 발상이다.

## 적용 — 풀어나가는 법

### 1. 페이지 폴트를 센다

```bash
# 한 번 실행하는 프로그램
/usr/bin/time -v ./prog 2>&1 | grep -E "page faults|context switches"
#   Major (requiring I/O) page faults: 16384
#   Minor (reclaiming a frame) page faults: 17487         (예시)

# 실행 중인 프로세스: 초당 minflt/s, majflt/s
pidstat -r -p <pid> 1

# 누적 값 (프로세스)
ps -o pid,min_flt,maj_flt,comm -p <pid>

# 시스템 전체 누적 (차이를 본다)
grep -E "^(pgfault|pgmajfault) " /proc/vmstat
```

- `majflt/s`가 꾸준히 0보다 크면 디스크를 기다리는 폴트가 있다. 지연에 직접 영향을 준다.
- minor fault가 많아도 대개 괜찮다. 시작 직후·힙이 커질 때 몰린다.

### 2. 인터럽트 분포를 본다

```bash
# 코어별 인터럽트 누적 (두 번 떠서 차이)
cat /proc/interrupts

# 코어별 %irq(상반부), %soft(softirq)
mpstat -P ALL 1

# 시스템 전체 초당 인터럽트(in)·문맥 전환(cs)
vmstat 1
```

- 특정 코어만 `%soft`·`%irq`가 높으면 인터럽트 쏠림을 의심한다.

### 3. 폴트를 미리 치른다 — 워밍업

C — 지연에 민감한 구간 전에 메모리를 미리 건드리거나 요청한다.

```c
/* 익명 메모리: 미리 한 번씩 써서 minor fault를 시작 시점에 치른다 */
for (size_t i = 0; i < size; i += 4096) buf[i] = 0;

/* 파일 매핑: 곧 읽을 범위를 미리 읽어 달라고 힌트 */
madvise(addr, len, MADV_WILLNEED);

/* 스왑으로 밀려나면 안 되는 작은 영역 (권한·한도 필요, RLIMIT_MEMLOCK) */
mlock(addr, len);
```

Java — HotSpot `-XX:+AlwaysPreTouch`는 힙을 커밋할 때 모든 페이지를 미리 건드린다("Force all freshly committed pages to be pre-touched", gc_globals.hpp). 시작은 느려지고, 운영 중 첫 접근 폴트는 줄어든다.

## 장애 시나리오와 대처

### 1. major fault 폭주 → 디스크 대기로 지연 급등

- **현상**: 평소 p99 수 ms인 서비스가 배포 직후·메모리 압박 시 수백 ms로 뛴다. CPU는 한가하다.
- **보이는 형태**
  - `pidstat -r`의 `majflt/s` 급증, `/proc/vmstat`의 `pgmajfault` 증가.
  - `vmstat`의 `b`(I/O 대기로 막힌 수)와 `wa`, 스왑 쓰면 `si`가 오른다.
  - `ps`에서 스레드가 `D` 상태(디스크 대기)로 보인다(04번).
- **원인**
  - 필요한 페이지가 메모리에 없다. 캐시가 비었거나(재시작·다른 작업이 캐시를 밀어냄), 스왑으로 밀렸다.
  - 디스크를 읽는 major fault는 디스크 I/O만큼 걸리고, 그동안 스레드는 잠든다(로컬 SSD 약 18~20µs/건, HDD는 더 길다).
- **대처**
  - 메모리를 충분히 두고 스왑 사용을 확인한다(12번).
  - 배포 후 워밍업 트래픽을 흘린 뒤 실트래픽을 받는다.
  - 크게 매핑한 파일은 `MADV_WILLNEED`·순차 접근 힌트, 꼭 필요한 영역은 `mlock`.

### 2. 시작 직후 minor fault 몰림

- **현상**: JVM·큰 캐시를 쓰는 프로세스가 기동 직후나 힙이 커지는 순간 느리다.
- **보이는 형태**: `minflt/s`가 초당 수십만, `sys` 시간 증가.
- **원인**: `mmap`(`MAP_POPULATE` 없이)과 새로 커진 `malloc` 영역은 주소만 잡는다. 처음 건드릴 때 페이지마다 폴트가 난다(로컬: 64MB 첫 쓰기에 16397번). `malloc`이 이미 쓰던 메모리를 다시 주면 폴트가 없다.
- **대처**
  - 지연이 중요하면 미리 건드린다(JVM `-XX:+AlwaysPreTouch`, C는 시작 시 쓰기).
  - 큰 페이지(THP·huge page)로 폴트·TLB 부담을 줄일 수 있는지 검토한다(10번).

### 3. 인터럽트가 한 코어에 몰림

- **현상**: 전체 CPU는 여유인데 네트워크 처리량이 한계에 걸리고 지연이 튄다.
- **보이는 형태**
  - `mpstat -P ALL`에서 한 코어만 `%soft`·`%irq`가 높다.
  - `/proc/interrupts`에서 NIC 큐의 인터럽트가 한 CPU 칸에만 늘어난다.
- **원인**: 장치 인터럽트(와 이어지는 softirq)가 한 코어로만 간다. 그 코어가 병목이 된다.
- **대처**
  - NIC 다중 큐와 IRQ 분산(`irqbalance`, `/proc/irq/<n>/smp_affinity`)을 확인한다(설정 변경은 root).
  - 소프트웨어 분산(RPS)도 있다(network/25).

### 4. 복구할 수 없는 폴트 → 시그널로 종료

- **현상**: 프로세스가 특정 입력에서 죽는다.
- **보이는 형태**: exit 139(SIGSEGV), 136(SIGFPE), 132(SIGILL). 컨테이너 종료 코드도 같다.
- **원인**
  - 139: 매핑 없는 주소·권한 없는 주소 접근(NULL, 해제된 메모리, 스택 넘침).
  - 136: 정수 0으로 나눔(#DE). 부동소수 0 나눗셈은 기본 설정에서 시그널 없이 끝난다. `1.0/0.0`은 inf와 `FE_DIVBYZERO` 플래그, `0.0/0.0`은 NaN과 `FE_INVALID` 플래그다(fenv(3), 로컬 재현 `1.0/0.0` → inf, exit 0).
  - 132: CPU가 모르는 명령(01번).
- **대처**: 코어 덤프를 `gdb`로 열어 `bt`·`x/i $pc`로 폴트 명령과 주소를 본다. `SA_SIGINFO` 핸들러면 `si_addr`로 폴트 주소를 얻는다.

## 핵심 문장

- CS:APP는 예외를 네 가지로 나눈다. 인터럽트(밖, 비동기, 다음 명령으로), 트랩(일부러, 다음 명령으로), 폴트(오류지만 고칠 수 있으면 같은 명령 재실행), 어보트(복구 불가).
- 사건 번호가 인덱스인 벡터 테이블(IDT)로 핸들러를 O(1)에 찾는다. 0~31은 CPU 예외다.
- 페이지 폴트 대부분은 오류가 아니라 요구 페이징이다. minor는 디스크 없이, major는 디스크 I/O를 기다린다.
- 디스크를 읽는 major fault 한 건은 디스크 한 번 읽기만큼 걸리고 스레드가 잠든다. 그래서 major fault 폭주는 CPU가 한가한데 지연이 치솟는 모양으로 나타난다.
- 고칠 수 없는 폴트는 커널이 시그널(SIGSEGV·SIGFPE·SIGILL)로 바꿔 프로세스에 전달한다.

## 관련 주제·근거

- 선행: [02-system-calls](../02-system-calls/2-summary.md) — 트랩의 대표인 시스템 콜 · [01-kernel-and-user-mode](../01-kernel-and-user-mode/2-summary.md)
- 후속·연결
  - [04-process-and-lifecycle](../04-process-and-lifecycle/2-summary.md) — major fault 동안의 `D` 상태
  - [06-signals](../06-signals/2-summary.md) — 폴트가 바뀐 시그널을 받는 쪽.
  - [10-paging-and-tlb](../10-paging-and-tlb/2-summary.md) · [12-swapping-and-page-replacement](../12-swapping-and-page-replacement/2-summary.md) · [14-mmap-and-page-cache](../14-mmap-and-page-cache/2-summary.md) — 페이지 테이블·스왑·페이지 캐시.
  - [architecture/15-io-devices-interrupts-dma](../../architecture/15-io-devices-interrupts-dma/2-summary.md) — 폴링 vs 인터럽트, DMA
  - [network/25-kernel-network-stack](../../network/25-kernel-network-stack/2-summary.md) — IRQ → NAPI → softirq
  - 원고 [foundations/memory-management](../../foundations/memory-management/README.md) §10 요구 페이징·§11 페이지 폴트
- 교재
  - CS:APP 3판 8.1 Exceptions(8.1.2 예외의 종류) — CMU 15-213 강의 자료 "Exceptional Control Flow: Exceptions and Processes" <https://www.cs.cmu.edu/afs/cs/academic/class/15213-f15/www/lectures/14-ecf-procs.pdf>
  - OSTEP 6장(타이머 인터럽트) <https://pages.cs.wisc.edu/~remzi/OSTEP/cpu-mechanisms.pdf>
- Linux 소스(master)
  - arch/x86/include/asm/trapnr.h — 예외 벡터 번호, FRED 이벤트 종류
  - arch/x86/kernel/traps.c — `exc_divide_error`(SIGFPE/FPE_INTDIV), `handle_invalid_op`(SIGILL), `exc_general_protection`(SIGSEGV)
  - arch/x86/kernel/idt.c — `IA32_SYSCALL_VECTOR`(int 0x80)
  - arch/x86/kernel/irq.c — `/proc/interrupts`의 LOC·RES·CAL·TLB 이름
  - mm/memory.c — `fault_around_pages`(64KB)
  - kernel/extable.c, lib/extable.c — 예외 테이블 정렬·이진 탐색
- man: proc_pid_stat(5)(minflt·majflt), pidstat(1)(`-r`, majflt/s), vmstat(8), mpstat(1), madvise(2), mlock(2), mmap(2)(`MAP_POPULATE`, `SIGBUS`), fenv(3), bash(1)(128+n)
- v6.19/v7.0 소스 확인: arch/x86/entry/entry_fred.c(`fred_intx`의 `IA32_SYSCALL_VECTOR`), mm/page_io.c(`zswap_load`), mm/memory.c(`VM_FAULT_MAJOR`)
- HotSpot `AlwaysPreTouch` — src/hotspot/share/gc/shared/gc_globals.hpp
- 로컬 재현(리눅스 7.0.0): #DE→SIGFPE 136, int3→SIGTRAP 133, ud2→SIGILL 132, NULL→SIGSEGV 139, 익명/파일 매핑 minor·major fault 수와 시간, `/usr/bin/time -v`의 major fault = 자발적 문맥 전환, `/proc/interrupts`의 LOC·RES·CAL·TLB 줄
