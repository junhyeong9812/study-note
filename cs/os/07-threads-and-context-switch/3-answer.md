# os/07-threads-and-context-switch — 정답

## 정답

### 1. 스레드 셋의 그림

```text
  스레드 그룹 (TGID = 100)
  공유: 주소 공간(mm_struct·페이지 테이블), fd 테이블, 시그널 처리 방식, cwd/umask
  +----------------+  +----------------+  +----------------+
  | TID 100        |  | TID 101        |  | TID 102        |
  | 레지스터 저장본   |  | 레지스터 저장본   |  | 레지스터 저장본   |
  | 유저 스택        |  | 유저 스택        |  | 유저 스택        |
  | 커널 스택        |  | 커널 스택        |  | 커널 스택        |
  | 시그널 마스크·TLS |  | 시그널 마스크·TLS |  | 시그널 마스크·TLS |
  +----------------+  +----------------+  +----------------+
```

- `getpid()`는 TGID(스레드 그룹 ID)를 돌려준다. 모든 스레드에서 같다.
- `gettid()`는 스레드마다 다른 TID를 돌려준다. 첫 스레드의 TID = TGID다.
- 로컬 확인(예시): 두 스레드가 `getpid=2071571`로 같고 `tid`는 2071572, 2071573으로 달랐다.

### 2. `pthread_create`와 PCB/TCB

- glibc는 `clone` 계열 시스템 콜(2.39는 `clone3` 우선, 없으면 `clone`)을 부르며 `CLONE_VM | CLONE_FS | CLONE_FILES | CLONE_SYSVSEM | CLONE_SIGHAND | CLONE_THREAD | CLONE_SETTLS | …`를 준다(glibc 2.39 `nptl/pthread_create.c`).
- 커널에는 PCB와 TCB가 따로 없다. 스레드마다 `task_struct` 하나가 있다.
- 스레드 여럿이 `mm_struct`(주소 공간)·fd 테이블·시그널 처리 방식을 **포인터로 공유**한다. 원고의 PCB에 해당하는 정보가 이 공유 구조체들이고, TCB에 해당하는 것이 스레드마다의 `task_struct`·커널 스택이다.

### 3. A → B 스위칭 단계

1. A가 트랩(시스템 콜)·인터럽트로 커널에 들어온다. 유저 레지스터가 A의 **커널 스택**에 저장된다.
2. `schedule()`이 다음 task로 B를 고른다.
3. `context_switch()`: B의 주소 공간이 A와 다르면 `switch_mm_irqs_off()`로 페이지 테이블(CR3)을 바꾼다. 같으면 보통 생략한다(lazy TLB 중 낡은 경우, 6.15+ 전역 ASID로 옮기는 경우 제외).
4. `switch_to()`: A의 callee-saved 레지스터를 push하고, A의 스택 포인터를 `task_struct->thread.sp`에 저장한 뒤, B의 스택 포인터를 로드한다(x86-64 `__switch_to_asm`).
5. B는 예전에 멈췄던 커널 지점에서 이어 달리다가, 커널 스택의 유저 레지스터를 복원해 유저 모드로 돌아간다.

- 저장 위치: 유저 레지스터는 커널 스택, 커널 스택 포인터는 `task_struct->thread`.

### 4. 스레드 간 vs 프로세스 간

- 레지스터 저장·복원은 같다.
- 스레드 간: 주소 공간이 같아 페이지 테이블을 바꾸지 않는다(OSTEP 26, arch/x86/mm/tlb.c `prev == next`).
- 프로세스 간: 주소 공간이 다르면 CR3를 바꾼다(`CLONE_VM`으로 `mm`을 공유한 드문 경우는 예외).
- x86 리눅스는 **매번 TLB를 전부 비우지는 않는다**. PCID로 CPU마다 동적 ASID 슬롯 6개를 두고 최근 주소 공간의 TLB 항목을 구분해 둔다(`TLB_NR_DYN_ASIDS 6`, 6.15+ `INVLPGB` 지원 CPU는 전역 ASID도 별도). 다른 CPU에서의 변경 등으로 무효화가 필요하면 비운다.

### 5. 8 MB 스택과 2 MB 미만 RSS

- 모순이 아니다. 스레드 스택은 **가상 주소 예약**이고, 실제로 건드린 페이지만 물리 메모리(RSS)를 쓴다.
- 8 MB의 출처: glibc(NPTL)는 프로그램 시작 때의 `RLIMIT_STACK`(`ulimit -s`, 이 환경 8192 KB)을 새 스레드 기본 스택으로 쓴다. 무제한이면 아키텍처 기본(대부분 2 MB)이다(pthread_create(3)).
- 로컬 확인(예시): 두 스레드 지역 변수 주소 차가 0x801000 = 8 MiB + 4 KiB(가드 페이지)였고 RSS는 1764 KB였다.
- JVM: HotSpot 리눅스 x86-64의 `-Xss`(`ThreadStackSize`) 기본은 1024 KB다(OpenJDK `globals_linux_x86.hpp`).

### 6. 스위치 한 번의 비용

- 한 왕복 = 스위치 2번 + 시스템 콜 4번. 3.8 µs / 2 ≈ **약 2 µs**(파이프 read/write 포함).
- 빈 시스템 콜이 0.12 µs였으니 시스템 콜 몫은 작다. 대부분이 깨우기·스케줄링·전환 경로다(예시, 로컬 측정).
- 담지 못하는 비용: **간접 비용**. 새로 올라온 스레드의 데이터가 캐시·TLB에 없어 이어지는 미스들이다. 핑퐁은 작업 집합이 1바이트라 이것이 거의 없다.
- 교차 CPU 비용도 따로 있다. CPU 고정을 빼면 왕복이 약 8 µs로 늘었다(상대 CPU 깨우기).

### 7. `cs` 190만, `sy` 71%

- 의심: 스레드 과다, 락 경합(잠들고 깨기 반복), 짧은 sleep·타이머 폴링.
- 좁히기
  - `vmstat 1`의 `r`이 코어 수보다 훨씬 큰지 본다. 실행 가능한 task가 넘친다.
  - `pidstat -w -t 1`로 어느 프로세스·스레드의 `cswch/s`(자발적) 또는 `nvcswch/s`(비자발적)가 큰지 본다.
  - `ps -o nlwp`로 스레드 수를 확인한다.
  - 자발적이 크면 락·I/O 대기, 비자발적이 크면 보통 CPU 과다 경쟁(선점)이다. 단 `sched_yield()` 반복도 비자발적으로 잡히니 스핀·yield 루프가 있는지 함께 본다.
- 대처: 풀 상한, 락 경합 제거, 블로킹 구간을 가상 스레드·논블로킹 I/O로.

### 8. `unable to create native thread`

- `-Xmx`를 늘려도 **해결되지 않는다**. 힙 부족이 아니다. 오히려 네이티브 메모리를 줄여 악화할 수 있다.
- 확인할 한도
  1. `ulimit -u`(`RLIMIT_NPROC`) — 실사용자 ID 단위 합계.
  2. 컨테이너 `pids.max`(cgroup v2) — 초과하면 clone이 `EAGAIN`.
  3. `/proc/sys/kernel/threads-max`, `/proc/sys/kernel/pid_max` — 시스템 전체.
  4. 스택 등을 위한 네이티브 메모리(컨테이너 메모리 제한).
- 근거: pthread_create(3) `EAGAIN` 조건, cgroup-v2 문서. JDK 메시지는 `os.hpp` `OS_NATIVE_THREAD_CREATION_FAILED_MSG`.
- 순서: `jstack`으로 스레드 수·이름을 보고 누수 풀을 먼저 찾는다.

### 9. 자발적 vs 비자발적

- 자발적: 스레드가 I/O·락·sleep·조건 변수로 **잠들며** CPU를 내놓을 때.
- 비자발적: 타임 슬라이스를 다 썼거나 더 급한 task가 깨어나 스케줄러가 **빼앗을** 때. 실행 가능 상태로 넘기는 `sched_yield()`도 여기로 센다(kernel/sched/core.c `__schedule()`).
- `/proc/<pid>/status`의 값은 **그 스레드(메인 스레드) 하나**의 누적값이다. 다른 스레드의 스위치를 놓친다. 스레드별로는 `/proc/<pid>/task/<tid>/status`나 `pidstat -w -t`를 본다.
- 로컬 확인(예시): 400 스레드 프로그램의 메인 스레드는 `nonvoluntary_ctxt_switches: 68`뿐이었지만 시스템 `cs`는 초당 약 200만이었다.

### 10. 스레드 1만 개 — 플랫폼 vs 가상

- 플랫폼 스레드: 1만 개가 모두 커널 task다. 블로킹·깨어남마다 **커널 컨텍스트 스위치**가 일어난다. 스택 예약(기본 1 MB씩)과 스레드 수 한도(`pids.max` 등)에도 걸린다.
- 가상 스레드: JDK의 블로킹 연산 대부분은 가상 스레드를 캐리어(플랫폼 스레드)에서 **내리고**, 캐리어는 다른 가상 스레드를 올린다(JEP 444). 전환이 JVM 안에서 일어나 커널 스위칭 대상은 캐리어 수(기본은 대략 코어 수) 정도로 준다.
- 단서: 파일 시스템 연산(과 JDK 21~23의 `Object.wait()`) 등은 캐리어를 붙잡아 스케줄러가 캐리어를 임시로 늘린다. JDK 21에서는 `synchronized` 안 블로킹이 캐리어를 고정(pinned)한다(JEP 444, JDK 24의 JEP 491에서 해소).
- 남는 것: CPU 위주 작업은 가상 스레드로 빨라지지 않는다. 코어 수가 상한이다.
