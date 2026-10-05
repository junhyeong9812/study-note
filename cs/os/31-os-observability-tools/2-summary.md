# os/31-os-observability-tools — "느리다"를 자원 이름으로 바꾸는 도구와 순서 — 정리 (힌트)

## 해결하는 문제

장애 보고는 늘 "느리다", "멈췄다"로 온다. 고치려면 이것을 **어느 자원이 얼마나 막혔는지**로 바꿔야 한다.

```text
  "API가 느리다"
      |
      v   ??? 어디부터 보나
  CPU가 모자란가?   메모리가 모자라 스왑하나?   디스크가 밀렸나?   네트워크?   락?
      |
      v
  "CPU 8개가 100% 바쁘고 실행 대기 줄(run queue)이 20이다"   <- 이 형태로 말할 수 있어야 한다
```

도구는 많다. 문제는 **순서 없이** 보는 것이다. 익숙한 도구만 보고(가로등 효과) 엉뚱한 곳을 튜닝한다.

쉬운 예: 병원 진료다.
- 체온·혈압·맥박(기본 지표)을 먼저 전부 잰다.
- 이상한 수치가 나온 장기만 정밀 검사(strace·perf)한다.
- 정밀 검사는 몸에 부담이 있다. 아무한테나 하지 않는다.

똑같은 구조다.\
**USE 방법론**이 "모든 자원마다 사용률·포화·에러를 잰다"는 체크리스트이고, `vmstat`·`iostat`·`pidstat`가 체온계, `strace`·`perf`가 정밀 검사다.

## 동작·원리

### 1. 거의 모든 도구는 `/proc`·`/sys`를 읽는다

```text
   사용자 공간 도구                  읽는 곳 (커널이 만들어 보여 주는 가상 파일)
   top, ps, pidstat          ->     /proc/<pid>/stat, /proc/<pid>/status, /proc/stat
   vmstat                    ->     /proc/vmstat, /proc/stat, /proc/meminfo
   iostat                    ->     /proc/stat, /sys/block/<dev>/stat (또는 /proc/diskstats)
   uptime, top 첫 줄          ->     /proc/loadavg
   free                      ->     /proc/meminfo
   ss                        ->     netlink (sock_diag)
   ----------------------------------------------------------------------
   strace                    ->     ptrace(2)로 대상 프로세스를 멈춰 가며 시스템 콜을 가로챈다
   perf                      ->     perf_event_open(2): 하드웨어·소프트웨어 이벤트 샘플을 링 버퍼로 받는다
```

- 작성 환경에서 `strace -e openat vmstat 1 1`을 돌리면 `/proc/vmstat`, `/proc/stat`, `/proc/meminfo`를 연다(로컬 재현). `iostat -x`는 `/proc/stat`과 `/sys/block/*/stat`을 연다.
- 대부분의 값은 **부팅 후 누적 카운터**다. 도구는 두 번 읽어 차이를 시간으로 나눈다(초당 값).
  - 그래서 `vmstat 1`의 **첫 줄은 부팅 이후 평균**이다(vmstat(8)). 지금 상태는 둘째 줄부터 본다. 단, procs(r·b)와 메모리 칸은 순간값이다.

### 2. load average — CPU 사용률이 아니다

```text
   리눅스 load = 지수 감쇠 평균( R 상태 수 + D 상태 수 )    5초마다 표본 (LOAD_FREQ = 5*HZ+1)
                              ^            ^
                    실행 중 + 실행 대기     중단 불가 대기 (디스크 I/O, 일부 락, NFS ...)

   예) CPU 8개 서버, load 20
       경우 A: R 20개  -> CPU가 모자라 12개가 줄 서 있다    (CPU 사용률 100%)
       경우 B: R 2, D 18 -> CPU는 한가하고 18개가 I/O·락에 묶였다 (CPU 사용률 25% 남짓)
```

- proc_loadavg(5): 앞 세 칸은 실행 큐(R) 또는 디스크 I/O 대기(D) 작업 수의 1·5·15분 평균이다.
- 커널 코드는 CPU별 `nr_running + nr_uninterruptible`을 모아 5초마다 지수 감쇠 평균을 낸다(kernel/sched/loadavg.c `calc_load_fold_active`, include/linux/sched/loadavg.h `LOAD_FREQ`·`EXP_1`·`EXP_5`·`EXP_15`).
- D 상태는 디스크만이 아니다. 중단 불가 대기면 무엇이든 들어간다. 1993년 Matthias Urlichs가 D를 넣은 패치 이후 리눅스 load는 "CPU 부하"가 아니라 **"시스템 부하"**다(Gregg, "Linux Load Averages: Solving the Mystery").
- 작성 환경 재현(로컬): `vfork` 부모 4개를 자식 exec 대기 상태로 두자 `ps`에 `D kernel_clone` 4개가 보였다. CPU를 전혀 안 쓰는 D 상태다.
  - 같은 때 `vmstat`의 `b` 칸은 0이었다. `b`는 `/proc/stat`의 `procs_blocked`인데, 커널은 이 값을 `nr_iowait()`로 낸다(fs/proc/stat.c). **I/O 대기 D만 세고, 다른 D는 안 센다.** 그래서 load에는 들어가도 `b`에는 안 보이는 D가 있다.

  - *R 상태*: 실행 중이거나 CPU를 기다리는 상태다.
  - *D 상태(TASK_UNINTERRUPTIBLE)*: 보통의 시그널로는 깨우지 않는 대기다. 디스크 I/O 완료 등을 기다린다. 단 `TASK_KILLABLE` 대기도 `D`로 보이는데, 이것은 치명적 시그널(SIGKILL)로는 깨어난다(`include/linux/sched.h`: `TASK_KILLABLE = TASK_WAKEKILL | TASK_UNINTERRUPTIBLE`). 위의 vfork 부모가 이 경우다(kernel/fork.c `wait_for_vfork_done`: `TASK_KILLABLE|TASK_FREEZABLE`).

### 3. USE 방법론 — 자원마다 세 가지

```text
   자원        Utilization(사용률)          Saturation(포화)                    Errors(에러)
   CPU        mpstat %usr+%sys, top       vmstat r > CPU 수, 스케줄 지연       (드묾)
   메모리       free / available            vmstat si·so, 익명 페이지 스왑        OOM kill (dmesg)
   디스크       iostat %util (주의 아래)     iostat aqu-sz, await 증가            dmesg I/O error
   네트워크     sar -n DEV (대역폭 대비)       ss 재전송, 드롭, 소켓 큐              sar -n EDEV
   (소프트웨어 자원도 같다: 스레드 풀, 커넥션 풀, 락, fd)
```

- 정의(Gregg, USE Method)
  - 사용률: 자원이 일을 처리하느라 바빴던 평균 시간.
  - 포화: 처리 못 한 일이 쌓인 정도. 대개 대기열이다.
  - 에러: 에러 이벤트 수.
- 요령: 사용률보다 **포화**가 더 직접적인 병목 신호다. 100% 바쁘다는 것만으로는 느리지 않을 수 있다. 줄이 생기면 지연이 붙는다.
- 한계: `iostat`의 `%util`은 요청을 **직렬로** 처리하는 장치에서만 포화를 뜻한다. RAID·최신 SSD처럼 병렬로 처리하는 장치에서는 100%여도 한계가 아니다(iostat(1)).

### 4. 60초 첫 점검 — 넓게 한 번 훑기

Netflix 글 "Linux Performance Analysis in 60,000 Milliseconds"(Gregg)의 순서다.

```text
  1 uptime              load 추세 (1분 > 15분이면 악화 중)
  2 dmesg | tail        OOM kill, I/O 에러, TCP 드롭 같은 커널 메시지
  3 vmstat 1            r(실행 대기), b, si/so(스왑), us/sy/id/wa/st
  4 mpstat -P ALL 1     CPU별 불균형 (한 코어만 100% = 단일 스레드 병목)
  5 pidstat 1           어느 프로세스가 CPU를 쓰나
  6 iostat -xz 1        장치별 r/s w/s, await, aqu-sz, %util
  7 free -m             available 메모리
  8 sar -n DEV 1        NIC 처리량
  9 sar -n TCP,ETCP 1   TCP 연결 수, 재전송
 10 top                 전체 요약 재확인
```

- 넓게 훑고, 이상 신호가 나온 자원만 파고든다. 여기서 원인이 좁혀지면 `strace`·`perf`로 간다.

### 5. 정밀 도구 — 비용이 있다

```text
   strace (ptrace)                                perf (샘플링)
   대상  --syscall-->  커널                          CPU 타이머/이벤트가 N번째마다 인터럽트
     |  멈춤                                          |
     v                                               v
   strace가 깨어나 인자 읽고 기록 -> 대상 재개          그 순간의 스택(IP)을 링 버퍼에 기록
   시스템 콜 하나마다 문맥 교환 여러 번                 대상은 멈추지 않는다. 비용 ≈ 샘플 빈도
```

- `strace`는 시스템 콜마다 대상을 멈춘다. 작성 환경에서 `dd bs=1 count=200000`이 0.07~0.08초에서 `strace` 아래 7.9~8.3초로 약 100배 느려졌다(예시, 시스템 콜이 극단적으로 많은 경우, 로컬 재현).
  - 필터(`-e trace=...`)와 `-c`(요약)는 **출력**만 줄인다. ptrace 정지는 추적 안 하는 시스템 콜에서도 그대로다.
  - 정지 자체를 줄이는 `--seccomp-bpf`는 `-f`와 함께, 새로 띄우는 프로세스에만 된다. `-p`로 붙인 프로세스에는 적용되지 않는다(strace(1)).
  - 그래서 운영 프로세스에 붙일 때는 아주 짧게 붙였다 떼고, 가능하면 eBPF 계열(`perf trace`·`bpftrace`, 권한 필요)로 대신한다.
- `perf`는 샘플링 프로파일러다. 일정 간격으로 "지금 어디서 돌고 있나"를 찍어 세면 오래 걸리는 함수가 많이 찍힌다.
  - 비특권 사용자의 사용 범위는 `kernel.perf_event_paranoid`로 정한다. 커널 문서의 기본값은 2이고 값이 클수록 제한이 많다. 작성 환경(Ubuntu)은 4였고 비특권 `perf stat`이 "No supported events found"로 거부됐다(로컬 재현). 2보다 큰 값의 뜻은 배포판 패치의 영역이다 [?].
- PSI(`/proc/pressure/{cpu,memory,io}`): "자원을 기다리느라 멈춘 시간 비율"을 `some`(일부 태스크가 멈춤)·`full`(비유휴 태스크가 모두 멈춤)로 보여 준다(커널 문서 psi). 포화를 직접 재는 지표다.
  - 단 시스템 수준 `/proc/pressure/cpu`는 `some`만 본다. 그 `full` 줄은 정의되지 않는 값이라 5.13부터 호환용으로 0으로 나온다(psi 문서, 작성 환경에서도 `full ... total=0`). cgroup의 `cpu.pressure` full은 의미가 있다.

## 쓰이는 자료구조·알고리즘

- **지수 가중 이동 평균(EWMA)** — load average: `avenrun = avenrun × e + n × (1 − e)`를 5초마다. 1·5·15분은 감쇠 상수 `EXP_1`·`EXP_5`·`EXP_15`만 다르다(kernel/sched/loadavg.c). 오래된 표본의 영향이 지수로 준다.
- **누적 카운터 + 차분** — `/proc` 값은 대부분 단조 증가 카운터다. 두 시점을 빼 기간으로 나눠 속도로 만든다. Prometheus의 `rate()`와 같은 방식이다.
- **샘플링 프로파일러 = 스택 표본의 빈도 집계** — 표본 스택을 경로별로 세어 트리(트라이)로 합치면 플레임 그래프가 된다 → [data-structure/09-trie](../../data-structure/09-trie/2-summary.md).
- **링 버퍼** — perf는 커널과 공유하는 mmap 링 버퍼로 샘플을 받는다(perf_event_open(2)) → [data-structure/04-queue-deque](../../data-structure/04-queue-deque/2-summary.md).
- **대기열 = 포화의 정체** — 실행 큐(r), 장치 큐(aqu-sz), 소켓 큐. 사용률이 1에 가까워질수록 대기 시간이 급증한다 → [math/README](../../math/README.md) `10-queueing-and-littles-law`(미작성).

## 적용 — 풀어나가는 법

### 1. "load가 높다" 알림을 받았다

```bash
uptime                                   # 1·5·15분 추세
nproc                                    # CPU 수와 비교
vmstat 1 5                               # 첫 줄 버리고, r vs CPU 수, b, wa, id
ps -eLo stat,pid,tid,wchan:25,comm | awk '$1 ~ /^D/'    # D 상태 스레드와 대기 지점
cat /proc/pressure/cpu /proc/pressure/io                # 포화를 직접
```

- `r`이 CPU 수보다 계속 크면 CPU 포화다 → `pidstat 1`, `mpstat -P ALL 1`로 누가 쓰는지 본다.
- `id`가 높은데 load가 높으면 D 상태를 본다 → `wchan`으로 무엇을 기다리는지(디스크, NFS, 락) 확인한다.

```text
(예시, 리눅스 7.0 — vfork 재현 중)
    PID STAT WCHAN                  CMD
1998980 D    kernel_clone           ./dstate
1998981 D    kernel_clone           ./dstate
```

### 2. 프로세스 하나를 파고든다

```bash
pidstat -u -r -d -w -p <pid> 1          # CPU, 메모리·페이지 폴트, 디스크 I/O, 문맥 교환
top -H -p <pid>                          # 스레드별 CPU
cat /proc/<pid>/status                   # State, VmRSS, Threads, voluntary_ctxt_switches ...
cat /proc/<pid>/wchan; echo              # 지금 자는 커널 함수
strace -f -tt -T -p <pid> -e trace=network,read,write -o /tmp/s.txt   # 짧게! 비용 큼
strace -c -f -p <pid>                    # 호출 수·시간 요약 (Ctrl-C로 끝)
```

- `/proc/<pid>/stack`(커널 스택)은 작성 환경에서 일반 사용자가 자기 프로세스 것도 읽지 못했다(`허가 거부`, 로컬 재현). 그럴 때는 `wchan`으로 대신한다.

### 3. JVM·Node와 OS 도구를 잇는다

- **JVM**: `top -H -p <pid>`에서 CPU를 많이 쓰는 스레드 ID(TID)를 찾는다. `jstack <pid>` 결과의 `nid=`와 맞추면 어느 Java 스레드인지 나온다.
  - `nid` 표기는 HotSpot 구현이고 판마다 다르다. JDK 17까지는 16진수(`nid=0x...`)라 `printf '%x\n' <tid>`로 바꿔 맞춘다. JDK 18부터는 10진수(`nid=12345`)라 TID를 그대로 맞춘다(JDK-8268425, osThread.cpp).
- **Node**: 이벤트 루프는 스레드 하나다. `mpstat`에서 한 코어만 100%이고 `pidstat -t`에서 메인 스레드가 바쁘면 이벤트 루프 막힘이다. `node --cpu-prof`로 V8 프로파일을 뜬다.
- **컨테이너 안**: `top`의 load·CPU 수는 호스트 기준일 수 있다. 컨테이너 한도는 cgroup 파일로 본다(28번).

### 4. 증상 → 도구 빠른 표

| 증상 | 먼저 볼 것 |
|---|---|
| load 높고 CPU 한가 | `ps ... D`, `wchan`, `iostat -x`, PSI io |
| CPU 100%, 누가? | `pidstat 1`, `top -H`, `perf top`(권한 필요) |
| sys CPU가 높다 | `strace -c`(짧게), `vmstat`의 `cs`·`in` |
| 메모리 부족 의심 | `free -m`의 available, `vmstat` si/so, `dmesg`의 OOM kill 메시지 |
| 디스크 느림 | `iostat -xz 1`의 await·aqu-sz(%util은 장치 종류 주의) |
| VM에서 원인 모를 지연 | `vmstat`·`top`의 `st`, `mpstat`의 `%steal`(35번) |

## 장애 시나리오와 대처

### 1. load average를 CPU 사용률로 오해 — "CPU 증설했는데 그대로"

- **현상**: 8코어 서버 load 30. CPU를 16코어로 늘렸는데 load도 지연도 그대로다.
- **보이는 형태**: `vmstat`의 `id`가 70%대, `r`은 작다. `ps`에 D 상태가 많다. `wa`가 높거나, NFS·디스크 대기면 `iostat` await가 크다.
- **원인**: 리눅스 load는 R + D다. D 상태(디스크 I/O, NFS, 중단 불가 락 대기)가 load를 올렸다. CPU 부족이 아니다.
- **대처**
  - load는 "무엇이든 기다리는 태스크 수"로 읽고, CPU 판단은 `r`·`mpstat`·PSI cpu로 한다.
  - D의 대기 지점(`wchan`)으로 진짜 자원(디스크·NFS 서버·파일시스템 락)을 찾는다.
  - `vmstat`의 `b`는 I/O 대기 D만 센다. `b`가 0이어도 D가 없다는 뜻이 아니다.

### 2. 운영에서 `strace`를 붙였더니 서비스가 더 느려졌다

- **현상**: 원인을 보려고 `strace -f -p`를 붙이자 응답 시간이 수 배로 늘고 타임아웃이 난다.
- **보이는 형태**: 대상 프로세스의 처리량 급감. 떼면 회복.
- **원인**: ptrace는 시스템 콜마다 대상을 멈추고 strace로 문맥 교환한다. 시스템 콜이 많은 프로세스일수록 느려진다(작성 환경 극단 예시 약 100배).
- **대처**: 짧게 붙였다 뗀다. `-e trace=`·`-c`는 출력만 줄일 뿐 정지 비용은 그대로다. 정지를 줄이는 `--seccomp-bpf`는 `-p` 부착에는 안 된다(strace(1)). 상시 관측은 `perf`·eBPF 계열(권한 필요)이나 앱 지표로 한다.

### 3. `%util` 100%인데 디스크는 멀쩡하다

- **현상**: NVMe 볼륨의 `iostat %util`이 100%라 "디스크 포화"로 판단했는데, 증설해도 나아지지 않는다.
- **보이는 형태**: `%util` 100%, 하지만 `await`는 낮고 안정적이다.
- **원인**: `%util`은 "요청이 하나라도 있던 시간 비율"이다. 병렬로 처리하는 장치에서는 한계를 뜻하지 않는다(iostat(1)).
- **대처**: `await`·`aqu-sz`(포화), 장치 사양의 IOPS·대역폭 대비 실제 값으로 판단한다.

### 4. `vmstat` 첫 줄만 보고 판단

- **현상**: "CPU wa 0%인데요?" 그런데 실제로는 I/O 대기가 심했다.
- **보이는 형태**: `vmstat 1 1`만 찍어 공유했다.
- **원인**: 첫 줄은 부팅 이후 평균이다(vmstat(8)). 지금 상태가 아니다.
- **대처**: `vmstat 1 5`처럼 여러 줄을 찍고 첫 줄은 버린다. `iostat`도 첫 보고는 부팅 이후 값이다(`-y`로 생략, iostat(1)).

### 5. 컨테이너 안 `top`이 거짓말을 한다

- **현상**: 컨테이너 안 `top`에서 CPU 여유, load도 낮아 보이는데 앱은 느리다.
- **보이는 형태**: 호스트 전체 CPU 수·load가 보인다. cgroup의 `cpu.stat`에는 `nr_throttled`가 쌓였다.
- **원인**: `/proc/stat`·`/proc/loadavg`는 namespace로 가상화되지 않는 전역 값이다. load 계산도 전역 변수(`calc_load_tasks`, `avenrun`)다(kernel/sched/loadavg.c). 컨테이너 한도는 따로 있다.
- **대처**: 컨테이너는 cgroup 파일(`cpu.stat`, `memory.events`, `/proc/pressure` 대신 cgroup의 `cpu.pressure` 등)로 본다(28번).

## 핵심 문장

- 관측 도구 대부분은 `/proc`·`/sys`의 누적 카운터를 두 번 읽어 차이를 낸다. 그래서 `vmstat`의 첫 줄은 부팅 이후 평균이다.
- 리눅스 load average는 **R + D**의 지수 감쇠 평균이다. CPU 사용률이 아니고, D 상태(I/O·중단 불가 락)가 load를 올릴 수 있다.
- USE: 모든 자원에 대해 **사용률·포화·에러**를 본다. 포화(대기열)가 병목의 직접 신호다.
- 넓게 훑고(60초 점검) 좁혀 들어간다. `strace`는 시스템 콜마다 멈추는 비싼 도구라 운영에서는 짧게 쓴다(필터는 출력만 줄인다).
- `%util`·컨테이너 안 `top`처럼 **숫자의 정의**를 모르면 반대로 읽는다.

## 관련 주제·근거

- 선행: [02-system-calls](../02-system-calls/2-summary.md) — strace가 보는 것
- 연결
  - [03-interrupts-traps-faults](../03-interrupts-traps-faults/2-summary.md) — `vmstat`의 `in`, 페이지 폴트
  - [08-cpu-scheduling](../08-cpu-scheduling/2-summary.md) — 실행 큐, 문맥 교환. 원고는 [foundations/process-thread](../../foundations/process-thread/README.md)
  - [12-swapping-and-page-replacement](../12-swapping-and-page-replacement/2-summary.md) — si/so, 스래싱
  - [28-containers-namespaces-cgroups](../28-containers-namespaces-cgroups/2-summary.md) — cgroup 지표, throttling
  - [35-virtualization-hypervisor](../35-virtualization-hypervisor/2-summary.md) — steal time
  - [37-os-symptom-index](../37-os-symptom-index/2-summary.md) — "load 높은데 CPU 낮음" 역색인.
  - [reliability/36-profiling](../../reliability/36-profiling/2-summary.md), [reliability/20-performance-method-and-amdahl](../../reliability/20-performance-method-and-amdahl/2-summary.md)
- 교재·글
  - Brendan Gregg, 『Systems Performance』 2판 — 2장 Methodologies(USE 등), 4장 Observability Tools, 6장 CPUs, 9장 Disks <https://www.brendangregg.com/systems-performance-2nd-edition-book.html>
  - Gregg, "The USE Method" <https://www.brendangregg.com/usemethod.html>
  - Gregg, "Linux Load Averages: Solving the Mystery"(2017) — 1993년 Urlichs 패치, 시스템 부하 <https://www.brendangregg.com/blog/2017-08-08/linux-load-averages.html>
  - Netflix Tech Blog / Gregg, "Linux Performance Analysis in 60,000 Milliseconds" — 10개 명령 <https://www.brendangregg.com/Articles/Netflix_Linux_Perf_Analysis_60s.pdf>
- Linux man-pages
  - proc_loadavg(5) · proc_stat(5)(`procs_blocked`, `steal`) · proc(5)
  - vmstat(8) — 첫 보고는 부팅 이후 평균, r·b 정의 · iostat(1) — `%util`의 한계 · mpstat(1) · pidstat(1) · top(1) · strace(1)(`--seccomp-bpf`는 `-f` 필요, `-p` 부착 불가) · perf_event_open(2)(링 버퍼)
- 커널
  - kernel/sched/loadavg.c — `calc_load_fold_active`(nr_running + nr_uninterruptible), 전역 `avenrun` <https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/kernel/sched/loadavg.c>
  - include/linux/sched/loadavg.h — `LOAD_FREQ (5*HZ+1)`, `EXP_1 1884`, `EXP_5 2014`, `EXP_15 2037`
  - fs/proc/stat.c — `procs_blocked` = `nr_iowait()`
  - kernel/fork.c `wait_for_vfork_done` — `TASK_KILLABLE|TASK_FREEZABLE` · include/linux/sched.h `TASK_KILLABLE`
- OpenJDK JDK-8268425 "Show decimal nid of OSThread instead of hex format one"(JDK 18) · src/hotspot/share/runtime/osThread.cpp(jdk17u `nid=0x%x`, jdk21u `nid=` 10진) <https://bugs.openjdk.org/browse/JDK-8268425>
  - 커널 문서 sysctl/kernel `perf_event_paranoid`(기본 2) <https://docs.kernel.org/admin-guide/sysctl/kernel.html> · PSI <https://docs.kernel.org/accounting/psi.html>
- 로컬 재현(리눅스 7.0, sysstat 12.6.1): `strace -e openat`으로 vmstat·iostat가 읽는 파일, vfork로 D 상태 만들기와 `vmstat b` 비교, `strace` 오버헤드(dd bs=1), `perf_event_paranoid=4`에서 perf 거부, `/proc/pressure` 조회, `ss`가 `NETLINK_SOCK_DIAG` 소켓을 여는 것, `/proc/self/stack` 권한 거부
