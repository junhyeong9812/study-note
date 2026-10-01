# os/07-threads-and-context-switch — 한 주소 공간 안의 여러 실행 흐름, 그리고 갈아타는 비용 — 정리 (힌트)

## 해결하는 문제

기초는 원고 [foundations/process-thread](../../foundations/process-thread/README.md) §5(컨텍스트 스위칭과 PCB)·§7(스레드와 TCB)·§8(멀티 프로세스 vs 멀티 스레드)에 있다.\
요약하면 두 가지다.
- 스레드는 코드·데이터·힙을 공유하고 스택과 레지스터만 따로 가진 실행 흐름이다.
- CPU 하나에서 여러 흐름을 번갈아 돌리려면 레지스터 상태를 저장하고 복원해야 한다. 이것이 컨텍스트 스위칭이다.

이 노트는 그 위에서 세 가지를 채운다.

```text
  질문                                          이 노트의 답
  리눅스에서 스레드는 실제로 무엇인가?              task_struct 하나. 프로세스와 같은 구조체, 공유 범위만 다르다
  컨텍스트 스위칭은 커널 안에서 무엇을 하나?         레지스터 저장 -> (필요하면) 페이지 테이블 교체 -> 커널 스택 교체
  스레드를 많이 만들면 무엇이 깨지나?               스위치 폭증, 스레드 생성 실패(OOM: unable to create native thread)
```

쉬운 예: 요리사 한 명이 냄비 여러 개를 본다.
- 냄비를 옮길 때마다 "어디까지 했는지"를 메모지(PCB/TCB)에 적고, 다음 냄비의 메모지를 읽는다.
- 같은 부엌(주소 공간) 안에서 옮기면 메모만 바꾸면 된다.
- 다른 부엌(다른 프로세스)으로 옮기면 부엌 지도(페이지 테이블)까지 바꿔야 한다.
- 냄비가 너무 많으면 요리보다 메모 읽고 쓰기에 시간이 더 든다.

똑같은 구조다.\
스위칭 자체는 몇 마이크로초지만, 초당 수십만~수백만 번이면 CPU의 상당 부분이 스위칭에 쓰인다.

실무 예:
- 요청마다 스레드를 새로 만드는 서버가 피크 때 `vmstat`의 `cs`가 수십 배로 뛰고 `sy`(커널 시간)가 치솟는다.
- 컨테이너에서 JVM이 `java.lang.OutOfMemoryError: unable to create native thread`로 죽는다. 힙은 여유가 있다.

## 동작·원리

### 리눅스의 스레드 = 무엇을 공유하는 task

```text
  프로세스 (스레드 그룹, TGID = 100)
  +-------------------------------------------------------------+
  |  공유: mm_struct(주소 공간·페이지 테이블), fd 테이블,           |
  |        시그널 처리 방식, cwd/umask                            |
  |                                                             |
  |  task_struct TID=100      task_struct TID=101    TID=102    |
  |  +------------------+     +------------------+   +--------+ |
  |  | 레지스터(저장본)    |     | 레지스터(저장본)    |   | ...    | |
  |  | 커널 스택          |     | 커널 스택          |   |        | |
  |  | 유저 스택(8MB 예약) |     | 유저 스택          |   |        | |
  |  | 시그널 마스크, TLS  |     | 시그널 마스크, TLS  |   |        | |
  |  | 스케줄링 정보       |     | 스케줄링 정보       |   |        | |
  |  +------------------+     +------------------+   +--------+ |
  +-------------------------------------------------------------+
```

- 리눅스 커널에는 "스레드 전용 구조체"가 따로 없다. 스레드도 프로세스도 `task_struct` 하나다.
- 차이는 **무엇을 공유하느냐**다. glibc `pthread_create`는 `clone` 계열 시스템 콜에 다음 플래그를 준다(glibc 2.39 `nptl/pthread_create.c`). glibc 2.39는 `clone3`를 먼저 시도하고, 커널이 모르면(`ENOSYS`) `clone`으로 폴백한다(`sysdeps/unix/sysv/linux/clone-internal.c`). 로컬 `strace`에서도 `clone3(...CLONE_VM|...|CLONE_THREAD...)`가 보였다(예시, 리눅스 7.0).
  - `CLONE_VM` 주소 공간, `CLONE_FILES` fd 테이블, `CLONE_FS` cwd·umask, `CLONE_SIGHAND` 시그널 처리 방식을 공유한다.
  - `CLONE_THREAD`로 같은 스레드 그룹에 들어간다. `CLONE_SETTLS`로 스레드 지역 저장소를 설정한다.
- 그래서 원고의 PCB/TCB 구분은 리눅스에서 **같은 구조체의 공유 범위 차이**로 나타난다.

  - *TGID(thread group ID)*: `getpid()`가 돌려주는 값이다. 스레드 그룹의 첫 스레드 ID와 같다.
  - *TID*: 스레드마다 다른 ID다. `gettid()`가 돌려준다. `/proc/<pid>/task/<tid>/`에 스레드별 정보가 있다.

로컬에서 확인한 모습이다(예시, 리눅스 7.0).

```text
  tid=2071572 getpid=2071571 &local=0x75e5e13feea4
  tid=2071573 getpid=2071571 &local=0x75e5e0bfdea4     <- 두 스레드의 지역 변수 주소 차 = 0x801000
  /proc/2071571/task: 2071571 2071572 2071573          <- 메인 + 스레드 2개
  Threads: 3   VmRSS: 1764 kB
```

- 두 스레드 스택의 거리 0x801000은 8 MiB + 4 KiB다. 8 MiB 스택과 4 KiB 가드 페이지로 읽힌다.
- glibc(NPTL)의 새 스레드 기본 스택 크기는 프로그램 시작 때의 `RLIMIT_STACK`(`ulimit -s`, 이 환경 8192 KB)이다. 무제한이면 아키텍처 기본값(대부분 2 MB)을 쓴다(pthread_create(3)).
- 스택은 **가상 주소 예약**이다. 스레드 둘이 16 MB를 예약했지만 RSS는 1.7 MB였다. 실제로 건드린 페이지만 물리 메모리를 쓴다(10번 요구 페이징).
- JVM은 자체 기본값을 쓴다. 리눅스 x86-64 HotSpot의 `ThreadStackSize`(= `-Xss`) 기본은 1024 KB다(OpenJDK `globals_linux_x86.hpp`).

### 컨텍스트 스위칭 — 커널 안에서 일어나는 일

```text
  시간 --->
  스레드 A (유저)   | 트랩/인터럽트 |  커널: A의 커널 스택                 |  커널: B의 커널 스택  | 스레드 B (유저)
  ---------------->|------------>| (1) 유저 레지스터를 커널 스택에 저장     |                    |---------------->
                   |             | (2) schedule(): 다음 task로 B 선택     |                    |
                   |             | (3) switch_mm: 주소 공간이 다르면 CR3 교체 (같으면 생략)       |
                   |             | (4) switch_to: A의 callee-saved 레지스터 push,              |
                   |             |     A의 스택 포인터 저장, B의 스택 포인터 로드 ------------->|
                   |             |                                      | (5) B의 저장본 복원 → 유저로 복귀
```

- (1) 유저 모드에서 커널로 들어올 때 유저 레지스터를 커널 스택에 저장한다. 원고가 말한 "PCB에 저장"은 리눅스에서 커널 스택과 `task_struct->thread`에 나뉘어 있다.
- (2) 스케줄러가 다음에 돌릴 task를 고른다(08번).
- (3) `context_switch()`는 다음 task가 유저 task면 `switch_mm_irqs_off()`를 부른다(kernel/sched/core.c). x86은 이전·다음 주소 공간이 **같으면** 보통 페이지 테이블 교체를 생략한다(arch/x86/mm/tlb.c `if (prev == next)` "Not actually switching mm's"). 예외로 lazy TLB 상태에서 그사이 TLB가 낡았거나, 6.15+에서 그 `mm`이 전역 ASID로 옮겨 가는 중이면 다시 적재한다.
- (4) `switch_to()`가 커널 스택을 바꾼다. x86-64 `__switch_to_asm`은 callee-saved 레지스터를 push하고 `rsp`를 A의 `thread.sp`에 저장한 뒤 B의 값으로 바꾼다(arch/x86/entry/entry_64.S).
- (5) B는 자기가 멈췄던 커널 지점에서 이어 달리다가 유저 모드로 돌아간다.

**같은 프로세스의 스레드 간 스위칭 vs 다른 프로세스 간 스위칭**
- 레지스터 저장·복원은 같다(OSTEP 26 "the register state of T1 must be saved and the register state of T2 restored").
- 다른 점은 주소 공간이다. 스레드 간에는 페이지 테이블을 바꾸지 않는다(OSTEP 26). 주소 공간이 다른 프로세스 간에는 CR3를 바꾼다. (드물게 `clone(CLONE_VM)`만 주고 `CLONE_THREAD`는 뺀 두 프로세스는 `mm`을 공유하니 교체가 없다 — clone(2))
- x86 리눅스는 PCID(프로세스 문맥 ID)로 CPU마다 동적 ASID 슬롯 6개를 두고, 최근 주소 공간의 TLB 항목을 구분해 둔다(arch/x86/include/asm/tlbflush.h `TLB_NR_DYN_ASIDS 6`). 리눅스 6.15+에서 `INVLPGB`를 지원하는 CPU는 이와 별도로 전역 ASID도 쓴다(arch/x86/mm/tlb.c `allocate_global_asid()`). 그래서 CR3를 바꿔도 TLB를 매번 전부 비우지는 않는다(10번).

**자발적 vs 비자발적 스위치**

| 종류 | 언제 | 흔한 원인 |
|---|---|---|
| 자발적(voluntary) | 스레드가 잠들며(대기 상태로) CPU를 내놓음 | I/O 대기, 락 대기, `sleep`, 조건 변수 |
| 비자발적(involuntary) | 실행 가능 상태인 채로 CPU를 넘김 — 주로 선점 | 타임 슬라이스 소진, 더 급한 task 깨어남, `sched_yield()` |

- 분류 기준은 "스스로 했나"가 아니라 스위치 순간의 task 상태다. `sched_yield()`는 스스로 양보하지만 실행 가능 상태로 남으므로 비자발적으로 센다(kernel/sched/core.c `__schedule()`의 `nvcsw`/`nivcsw` 선택).
- `/proc/<pid>/status`의 `voluntary_ctxt_switches`·`nonvoluntary_ctxt_switches`가 누적값이다(리눅스 2.6.23+, proc_pid_status(5)). 이 값은 **그 스레드 하나**의 값이다. 스레드별로는 `/proc/<pid>/task/<tid>/status`를 본다.

### 비용 — 직접 비용과 간접 비용

```text
  직접 비용: 트랩 진입 + 레지스터 저장/복원 + 스케줄러 + (CR3 교체) + 복귀        -> 마이크로초 단위
  간접 비용: 새 스레드의 데이터가 L1/L2 캐시·TLB에 없음 -> 한동안 캐시 미스 연속   -> 작업 집합에 비례
```

로컬 측정(예시, 리눅스 7.0 · i7-13700HX). 파이프 두 개로 1바이트를 주고받는 핑퐁이다. 한 왕복 = 스위치 2번 + 시스템 콜 4번이다.

```text
  같은 CPU에 고정(taskset -c 2)     프로세스 3.9 µs/왕복   스레드 3.5~3.8 µs/왕복
  CPU 고정 없음                      프로세스 8.0 µs/왕복   스레드 8.4 µs/왕복
  빈 시스템 콜(getppid) 1회            0.12 µs
```

- 같은 CPU에서 한 번의 스위치(파이프 read/write 포함)는 약 2 µs였다. 이 측정에서는 프로세스와 스레드의 차이가 작았다. 작업 집합이 작고, PCID 덕에 TLB를 비우지 않기 때문으로 보인다.
- CPU를 고정하지 않으면 오히려 느렸다. 상대 CPU를 깨우는 비용(IPI, 유휴 상태 탈출)이 더해진다.
- OSTEP 6장은 1996년 측정(200 MHz)에서 컨텍스트 스위치 약 6 µs, 현대 시스템은 서브 마이크로초라고 적는다(lmbench 기준). 측정 방법마다 수치가 다르므로 **자릿수**로만 기억한다.
- 간접 비용은 작업 집합이 클수록 커진다. 이 측정은 간접 비용을 거의 담지 못한다.

### 1:1, M:N — 런타임이 스레드를 다루는 방식

```text
  1:1   Java 플랫폼 스레드, pthread     언어 스레드 1개 = 커널 task 1개. 스위칭은 커널이 한다
  M:N   Java 가상 스레드(JDK 21+)       가상 스레드 M개를 캐리어(플랫폼 스레드) N개에 올렸다 내렸다 한다
  1 + 풀 Node.js                      이벤트 루프 스레드 1개 + libuv 스레드 풀(기본 4개)
```

- Java 가상 스레드는 JEP 444(JDK 21)에서 정식이 됐다. JDK의 블로킹 연산 대부분은 가상 스레드를 캐리어에서 내리고, 캐리어는 다른 가상 스레드를 올린다. 이 전환은 커널 스위칭이 아니다(JEP 444 "The vast majority of blocking operations in the JDK will unmount the virtual thread").
  - 예외: 많은 파일 시스템 연산과 JDK 21~23의 `Object.wait()`는 캐리어를 붙잡는다(스케줄러가 캐리어를 임시로 늘려 보충). JDK 24부터 `Object.wait()`도 캐리어에서 내린다(JEP 491). JDK 21에서는 `synchronized` 안·네이티브 메서드에서 블로킹하면 캐리어에 고정(pinned)된다(JEP 444). `synchronized` 고정은 JEP 491(JDK 24)에서 풀렸다.
- libuv 스레드 풀 기본 크기는 4이고 `UV_THREADPOOL_SIZE`로 바꾼다. 파일 시스템 작업·`getaddrinfo`가 여기서 돈다(libuv 문서 "Thread pool work scheduling").

## 쓰이는 자료구조·알고리즘

- **실행 큐(run queue)** — CPU마다 하나씩 있는, 실행 가능한 task의 모음이다. 리눅스 일반 task는 가상 실행 시간·데드라인 기준 레드블랙 트리에 들어 있다(08번). [data-structure/16-red-black-tree](../../data-structure/16-red-black-tree/2-summary.md)
- **대기 큐(wait queue)** — 자원을 기다리는 task의 연결 리스트다. 잠든 task는 대기 원인에 따라 이런 대기 큐나 타이머(`nanosleep`의 hrtimer) 쪽에서 깨어나기를 기다린다. 리눅스 6.12+의 EEVDF는 잠든 task를 잠시 실행 큐에 남겨 두기도 하지만("deferred dequeue", sched-eevdf.rst) 실행 대상으로 고르지는 않는다. 자원이 준비되면 깨워 실행 큐로 되돌린다. [data-structure/02-linked-list](../../data-structure/02-linked-list/2-summary.md)
- **스택(콜 스택)** — 스레드마다 유저 스택과 커널 스택이 하나씩 있다. 스위칭은 결국 "스택 포인터 바꾸기"다. [systems/call-stack](../../systems/call-stack/README.md)
- **스레드 풀 = 작업 큐 + 재사용하는 워커** — 스레드 생성·스위칭 비용을 줄이려고 워커를 재사용하고 작업을 큐로 넘긴다. 워커 수는 고정(`newFixedThreadPool`)일 수도, 늘었다 줄었다(`newCachedThreadPool`) 할 수도 있다. [data-structure/04-queue-deque](../../data-structure/04-queue-deque/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 스레드 수를 정한다 — "많을수록 빠르다"가 아니다

- CPU 위주 작업: 스레드 수 ≈ 사용 가능한 코어 수. 더 늘리면 비자발적 스위치만 는다.
- I/O 위주 작업: 대기 시간 비율만큼 더 둘 수 있다. 그래도 상한을 둔다.
- 컨테이너에서는 "사용 가능한 코어"가 노드 코어가 아니라 CPU 제한이다. HotSpot은 `UseContainerSupport`(기본 켜짐)로 cgroup CPU quota를 읽어 사용 가능 CPU 수를 정한다(OpenJDK `globals_linux.hpp`, `cgroupSubsystem_linux.cpp`).

```java
// 상한 있는 풀 + 상한 있는 큐. 넘치면 호출자에게 되돌려(backpressure) 스레드 폭증을 막는다
ExecutorService pool = new ThreadPoolExecutor(
        16, 16, 0L, TimeUnit.MILLISECONDS,          // 16은 예시
        new ArrayBlockingQueue<>(1_000),            // 1000은 예시
        new ThreadPoolExecutor.CallerRunsPolicy());

// 블로킹 I/O가 대부분이면 가상 스레드 (JDK 21+)
try (var vexec = Executors.newVirtualThreadPerTaskExecutor()) {
    vexec.submit(() -> callRemote());
}
```

### 2. C — 스택 크기를 명시한다

```c
pthread_attr_t attr;
pthread_attr_init(&attr);
pthread_attr_setstacksize(&attr, 256 * 1024);   /* 256 KB (예시). 기본은 RLIMIT_STACK */
int r = pthread_create(&tid, &attr, worker, arg);
if (r != 0) { /* r == EAGAIN: 스레드 수 한도 또는 자원 부족 (pthread_create(3)) */ }
```

- `pthread_create`는 실패 시 `errno`를 세우지 않고 에러 번호를 **반환**한다(pthread_create(3)).

### 3. 진단 명령

```bash
# 시스템 전체: cs = 초당 컨텍스트 스위치, r = 실행 가능 task 수, sy = 커널 시간 비율
vmstat 1

# 프로세스의 스레드별 자발적(cswch/s)·비자발적(nvcswch/s) 스위치
pidstat -w -t -p <pid> 1

# 누적값 (메인 스레드 기준 / 스레드별)
grep ctxt /proc/<pid>/status
grep ctxt /proc/<pid>/task/*/status

# 스레드 수
ps -o pid,nlwp,cmd -p <pid>
ls /proc/<pid>/task | wc -l

# 스레드 생성 한도들
ulimit -u                                   # RLIMIT_NPROC: 실사용자 ID당 프로세스+스레드 수
cat /proc/sys/kernel/threads-max /proc/sys/kernel/pid_max
cat /sys/fs/cgroup/<그룹>/pids.max /sys/fs/cgroup/<그룹>/pids.current

# JVM 스레드 목록·상태
jstack <pid> | grep -c '^"'
```

로컬에서 400개 스레드가 락을 잡고 50 µs씩 자는 프로그램을 돌렸을 때의 `vmstat`이다(예시, 리눅스 7.0, 24 논리 CPU).

```text
   r  ...    in      cs  us sy id
   6  ...  35038   64226  12  4 84     <- 평소
 162  ... 250341 1559503  25 54 21     <- 400 스레드 시작
 269  ... 312798 1967742  26 71  3     <- 초당 약 200만 번 스위치, 커널 시간 71%
```

## 장애 시나리오와 대처

### 1. 스레드 과다 → 컨텍스트 스위치 폭증

- **현상**: 처리량은 늘지 않는데 CPU 사용률이 치솟고, 지연이 커진다.
- **보이는 형태**
  - `vmstat 1`의 `cs`가 평소의 수십 배, `sy`가 높고 `r`이 코어 수보다 훨씬 크다(위 예시).
  - `pidstat -w -t`에서 많은 스레드의 `cswch/s`(락·I/O 대기) 또는 `nvcswch/s`(선점)가 높다.
- **원인**
  - 요청당 스레드 생성, 상한 없는 풀, 풀마다 따로 만든 스레드가 합쳐져 코어 수의 수십 배가 됐다.
  - 스레드끼리 같은 락을 다투면 잠들고 깨는 자발적 스위치가 폭증한다.
- **대처**
  - 풀 크기에 상한을 두고 큐로 넘친 요청을 거절·지연한다.
  - 락 경합 지점을 줄인다(락 분할, 불변 객체, 16번).
  - 블로킹 I/O가 원인이면 가상 스레드나 논블로킹 I/O(25·26번)로 바꾼다.

### 2. `OutOfMemoryError: unable to create native thread`

- **현상**: JVM이 새 스레드를 만들다 실패한다. 힙(`-Xmx`)은 여유가 있다.
- **보이는 형태**
  - 현재 JDK: `java.lang.OutOfMemoryError: unable to create native thread: possibly out of memory or process/resource limits reached`(OpenJDK `os.hpp` `OS_NATIVE_THREAD_CREATION_FAILED_MSG`). JDK 8은 `unable to create new native thread`(jdk8u `jvm.cpp`).
  - 네이티브 코드라면 `pthread_create`가 `EAGAIN`(11, "Resource temporarily unavailable")을 돌려준다.
- **원인** — `pthread_create`의 `EAGAIN` 조건 중 하나다(pthread_create(3), cgroup-v2 문서).
  - `RLIMIT_NPROC`(`ulimit -u`) — **실사용자 ID 단위**라 같은 사용자의 다른 프로세스 스레드까지 합산된다.
  - 시스템 전체 `threads-max`, `pid_max`.
  - 컨테이너 `pids.max` — 초과하면 `fork`·`clone`이 `EAGAIN`을 돌려준다.
  - 스택 등 스레드 자원을 확보할 메모리 부족.
  - "OutOfMemoryError"라는 이름과 달리 힙 부족이 아니다.
- **대처**
  - 스레드 누수부터 찾는다: `jstack`으로 스레드 이름·상태를 세고, 시간에 따라 늘어나는 풀을 찾는다.
  - 한도를 확인한다: `ulimit -u`, `pids.max`, `threads-max`.
  - 스레드가 정말 많이 필요하면 `-Xss`를 줄이거나 가상 스레드로 옮긴다.
- 로컬 재현(예시, 리눅스 7.0): 같은 사용자의 현재 task 수 + 60으로 `ulimit -u`를 낮추고 C 프로그램이 스레드를 계속 만들게 했다. 61개를 만든 뒤 `pthread_create = 11 (Resource temporarily unavailable)`.

### 3. CPU 고정 없는 핑퐁 → 교차 CPU 깨우기 비용

- **현상**: 생산자·소비자 스레드가 작은 메시지를 주고받는 구조에서, 코어를 늘려도 지연이 줄지 않는다.
- **보이는 형태**: 메시지당 지연이 수 µs로 일정하게 높다. `in`(인터럽트)이 같이 오른다.
- **원인**: 매 메시지마다 잠든 상대 스레드를 다른 CPU에서 깨운다. 깨우기 인터럽트와 캐시 라인 이동이 더해진다. 로컬 측정에서 CPU를 고정하지 않은 핑퐁이 같은 CPU 고정보다 약 2배 느렸다(예시).
- **대처**: 메시지를 묶어 보낸다(배치). 필요하면 협력하는 스레드를 같은 코어·같은 캐시 도메인에 둔다(`taskset`, 08번 친화도).

### 4. 스레드 수만 보고 메모리를 오판

- **현상**: 스레드 2,000개인 JVM의 가상 메모리(VSZ)가 수 GB라 "메모리 누수"로 신고된다.
- **보이는 형태**: `ps -o vsz,rss`에서 VSZ는 크고 RSS는 작다. `/proc/<pid>/maps`에 스택 크기 구간이 반복된다.
- **원인**: 스레드 스택은 가상 예약이다. 실제로 쓴 페이지만 RSS에 잡힌다.
- **대처**: RSS·PSS(`/proc/<pid>/smaps_rollup`)로 판단한다. 다만 스레드 수 자체가 너무 많으면 위 1·2번 문제가 따라온다.

## 핵심 문장

- 리눅스에서 스레드는 주소 공간·fd·시그널 처리 방식을 공유하는 `task_struct`다. `pthread_create`는 `clone3`/`clone`에 `CLONE_VM|CLONE_FILES|CLONE_SIGHAND|CLONE_THREAD|…`를 주는 호출이다.
- 컨텍스트 스위칭은 레지스터를 커널 스택·`task_struct`에 저장하고, 주소 공간이 다를 때만 페이지 테이블을 바꾸고, 커널 스택 포인터를 바꾸는 일이다.
- 직접 비용은 마이크로초 단위다. 간접 비용(캐시·TLB 식음)은 작업 집합에 비례한다.
- 스레드가 많으면 `vmstat cs`와 `sy`가 치솟는다. 풀에 상한을 둔다.
- `unable to create native thread`는 힙이 아니라 스레드 수 한도(`ulimit -u`·`pids.max`·`threads-max`)나 네이티브 메모리 문제다.

## 관련 주제·근거

- 선행: [04-process-and-lifecycle](../04-process-and-lifecycle/2-summary.md). 원고 [foundations/process-thread](../../foundations/process-thread/README.md) §5·§7·§8.
- 후속·연결
  - [08-cpu-scheduling](../08-cpu-scheduling/2-summary.md) — 스위칭 뒤 "다음 누구"를 고르는 규칙.
  - [10-paging-and-tlb](../10-paging-and-tlb/2-summary.md) — CR3 교체와 TLB, PCID.
  - [06-signals](../06-signals/2-summary.md) — 스레드별 시그널 마스크.
  - [15-race-conditions](../15-race-conditions/2-summary.md)·[16-locks-and-spinlocks](../16-locks-and-spinlocks/2-summary.md) — 락 경합과 자발적 스위치.
  - [25-io-models](../25-io-models/2-summary.md)·[27-event-based-concurrency](../27-event-based-concurrency/2-summary.md) — 스레드 대신 이벤트.
  - [36-server-concurrency-architectures](../36-server-concurrency-architectures/2-summary.md) — 연결당 스레드 vs 리액터.
  - [language/README](../../language/README.md) — `14-concurrency-models`(가상 스레드·코루틴). 미작성.
- 소스
  - glibc 2.39 `sysdeps/unix/sysv/linux/clone-internal.c` `__clone_internal()` — `clone3` 우선, `ENOSYS`면 `clone` 폴백
  - glibc 2.39 `nptl/pthread_create.c` — `clone_flags = CLONE_VM | CLONE_FS | CLONE_FILES | CLONE_SYSVSEM | CLONE_SIGHAND | CLONE_THREAD | CLONE_SETTLS | CLONE_PARENT_SETTID | CLONE_CHILD_CLEARTID`
  - kernel/sched/core.c `context_switch()` — `switch_mm_irqs_off()`, `switch_to()` <https://github.com/torvalds/linux/blob/master/kernel/sched/core.c>
  - arch/x86/mm/tlb.c — `if (prev == next)` "Not actually switching mm's" · arch/x86/include/asm/tlbflush.h `TLB_NR_DYN_ASIDS 6`
  - arch/x86/entry/entry_64.S `__switch_to_asm` — callee-saved push, `TASK_threadsp`로 스택 교체
  - OpenJDK `src/hotspot/share/runtime/os.hpp` `OS_NATIVE_THREAD_CREATION_FAILED_MSG` · `share/prims/jvm.cpp` `JVM_StartThread` · jdk8u `jvm.cpp` "unable to create new native thread" · `os_cpu/linux_x86/globals_linux_x86.hpp` `ThreadStackSize 1024` · `os/linux/globals_linux.hpp` `UseContainerSupport`
- Linux man-pages 6.7(로컬): pthread_create(3) — 기본 스택 = RLIMIT_STACK(무제한이면 2 MB), `EAGAIN` 조건 · proc_pid_status(5) `voluntary_ctxt_switches` · proc_sys_kernel(5) `threads-max` · vmstat(8) `r`·`cs` · pidstat(1) `cswch/s`·`nvcswch/s`
- Kernel docs cgroup-v2 — `pids.max`, 초과 시 fork/clone `-EAGAIN` <https://docs.kernel.org/admin-guide/cgroup-v2.html>
- JEP 444 Virtual Threads <https://openjdk.org/jeps/444> · JEP 491 Synchronize Virtual Threads without Pinning(JDK 24, `Object.wait()` 언마운트 포함) <https://openjdk.org/jeps/491> · libuv "Thread pool work scheduling"(기본 4, `UV_THREADPOOL_SIZE`) <https://docs.libuv.org/en/v1.x/threadpool.html>
- 교재: OSTEP 26 "Concurrency: An Introduction"(TCB, 주소 공간 유지), 27 "Thread API", 6 "Limited Direct Execution"(컨텍스트 스위치 비용 aside) · CS:APP 3판 8.2.5 Context Switches, 12.3 Concurrent Programming with Threads
- 로컬 재현(리눅스 7.0 · glibc 2.39): TID/TGID와 스레드 스택 간격(8 MiB + 4 KiB), 파이프 핑퐁 스위치 비용, 400 스레드 `vmstat cs`, `ulimit -u` 아래 `pthread_create` → `EAGAIN`
