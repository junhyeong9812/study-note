# os/13-oom-and-memory-limits — "malloc은 성공했는데 죽었다": overcommit·OOM killer·cgroup 메모리 제한 — 정리 (힌트)

## 해결하는 문제

12번에서 본 회수(페이지 캐시 버리기, 스왑)로도 메모리를 못 만들면 커널은 선택해야 한다.\
**누군가의 요청을 거절하거나, 누군가를 죽이거나.**

이 선택이 생기는 이유는 리눅스가 메모리를 **약속만 먼저 해 주기** 때문이다.

```text
  malloc(1GB) 성공          → 커널: "가상 주소 1GB 예약. 물리 메모리는 아직 0"
  실제로 300MB만 건드림      → 물리 메모리 300MB만 쓰임
  모두가 약속을 한꺼번에 쓰면  → 물리 메모리 + 스왑 부족
                              → 이미 성공한 malloc을 되돌릴 수 없다
                              → OOM killer가 프로세스 하나를 SIGKILL
```

  - *overcommit*: 실제 가용 메모리보다 많은 양을 할당 약속하는 것이다. 대부분의 프로그램이 받은 메모리를 다 쓰지 않는다는 데 기대는 정책이다.
  - *OOM(Out Of Memory) killer*: 메모리를 되찾을 방법이 없을 때 커널이 프로세스를 골라 죽이는 장치다.

쉬운 예: 항공사의 초과 예약이다.
- 좌석 100개에 표를 110장 판다. 보통 10명쯤은 안 나타난다.
- 모두 나타나면 이미 판 표를 취소할 수 없다. 누군가를 내리게 해야 한다.
- 누구를 내리게 할지 기준이 있다. OOM killer의 `oom_score`다.

똑같은 구조다.\
컨테이너는 비행기 한 대를 더 작게 나눈 칸이다. 칸마다 정원(cgroup `memory.max`)이 있고, 칸 안에서 넘치면 그 칸 안의 승객을 내리게 한다.

실무 예:
- 쿠버네티스 파드가 `OOMKilled`, exit code 137로 재시작을 반복한다. 애플리케이션 로그에는 아무 에러도 없다.
- JVM 힙(`-Xmx`)은 limit보다 한참 작은데도 컨테이너가 죽는다.

## 동작·원리

### 1. 할당은 약속, 사용은 폴트

```text
  시점            가상(Committed_AS)   물리(RSS)
  malloc(1GB)     +1GB                 +0
  memset 300MB    그대로               +300MB  ← 첫 접근마다 페이지 폴트로 물리 페이지를 붙인다
  free            -1GB                 -300MB
```

- 약속된 총량은 `/proc/meminfo`의 `Committed_AS`, 모드 2의 한도는 `CommitLimit`이다(proc_meminfo(5)).
- 거절은 `malloc`·`mmap` 시점(`ENOMEM`)에만 가능하다. 사용 시점에 모자라면 거절할 방법이 없어 OOM killer로 간다.

### 2. overcommit 세 가지 모드 — `vm.overcommit_memory`

| 값 | 이름 | 동작 |
|---|---|---|
| 0 (기본) | 휴리스틱 | "뻔한" 초과만 거절한다. 현재 커널 코드에서는 한 번의 요청이 RAM + 스왑 총량보다 크면 거절한다(mm/util.c `__vm_enough_memory`) |
| 1 | 항상 허용 | 실제로 바닥날 때까지 있는 척한다 |
| 2 | 엄격 | 약속 총량이 `CommitLimit`을 넘으면 거절한다 |

- 모드 2의 한도: `CommitLimit = (RAM - 거대 페이지) × overcommit_ratio / 100 + 스왑`. `overcommit_ratio` 기본은 50이다(proc_sys_vm(5), kernel.org overcommit-accounting).
- 모드 2에서는 대부분 "쓰다가 죽는" 대신 "할당에서 에러를 받는다"(kernel.org overcommit-accounting). 대가는 실제로 안 쓸 약속도 한도에 잡혀 할당 실패가 더 잦다는 점이다.

로컬 재현(예시, 리눅스 7.0 — 작성 환경은 `overcommit_memory=1`로 바뀌어 있었다. 기본값 0이 아니다):

```text
$ grep -E 'MemTotal|CommitLimit|Committed_AS' /proc/meminfo
MemTotal:       38682560 kB
CommitLimit:    27729884 kB     ← 38.7GB × 50% + 스왑 8.4GB (모드 2일 때만 강제)
Committed_AS:   80781816 kB     ← 약속 총량이 한도의 약 3배. 모드 1이라 허용됨

$ ./big 1024                    # malloc(1TiB), 건드리지 않음
malloc(1024 GiB) = 0x7058bddff010      ← 성공 (모드 1). 모드 0이면 RAM+스왑보다 커서 거절된다

$ (ulimit -v 1048576; ./big 2)   # 가상 주소 한도 1GiB에서 2GiB 요청
malloc(2 GiB) = (nil)  errno=Cannot allocate memory   ← RLIMIT_AS는 할당 시점에 거절
```

### 3. OOM killer는 누구를 고르나

```text
  메모리 부족, 회수 실패
        |
        v
  후보 = (전체 시스템 OOM이면) 모든 프로세스 / (cgroup OOM이면) 그 cgroup 안
        |
        v
  점수(badness) = RSS + 스왑 사용 + 페이지 테이블   (페이지 수)
                + oom_score_adj × (허용 메모리 총량 / 1000)
        |
        v
  점수가 가장 큰 프로세스에 SIGKILL  → 커널 로그에 한 줄
```

- 기본 점수는 **메모리를 얼마나 쓰나**다. RSS·스왑 엔트리·페이지 테이블의 합이다(mm/oom_kill.c `oom_badness`).
- `oom_score_adj`(-1000 ~ +1000)를 "허용 메모리의 천분율" 단위로 더한다. +500은 대략 허용 메모리의 50%를 더 쓴 것처럼 친다(proc_pid_oom_score_adj(5)).
- **-1000이면 후보에서 빠진다**(같은 소스, `OOM_SCORE_ADJ_MIN`).
- 고른 프로세스에 `SIGKILL`을 보낸다(mm/oom_kill.c). 잡을 수 없는 시그널이라 애플리케이션은 로그를 남길 기회가 없다. 종료 코드는 128 + 9 = **137**이다.

> 참고: proc_pid_oom_score_adj(5)는 "root 프로세스는 3% 보너스"를 적지만, 현재 커널 소스의 `oom_badness`에는 그 계산이 없다(mm/oom_kill.c, master 기준). man 페이지가 뒤처진 부분이다.

`/proc/<pid>/oom_score`는 badness를 0~2000 범위로 바꿔 보여 준다.

```text
  oom_score = (1000 + badness × 1000 / (RAM + 스왑)) × 2 / 3      (fs/proc/base.c proc_oom_score)

  작성 환경의 셸 (예시, 리눅스 7.0): oom_score_adj = 100, 메모리 사용은 거의 0
  → (1000 + 100 + 0) × 2 / 3 ≈ 733   실제 값: 733
```

커널 로그 형식(mm/oom_kill.c `__oom_kill_process`):

```text
Out of memory: Killed process 1234 (java) total-vm:..kB, anon-rss:..kB, file-rss:..kB, shmem-rss:..kB, UID:.. pgtables:..kB oom_score_adj:..
Memory cgroup out of memory: Killed process 1234 (java) ...      ← cgroup limit 때문일 때
```

### 4. cgroup v2 메모리 — 컨테이너의 정원

```text
  메모리 사용량 (memory.current)
    ^
    |  memory.max  ======== 하드 한도: 회수로도 못 줄이면 cgroup 안에서 OOM killer
    |  memory.high -------- 넘으면 느려진다(스로틀 + 강한 회수). OOM killer는 부르지 않는다
    |  memory.low  -------- 이 밑은 되도록 회수하지 않는 보호선
    +--------------------------------------------> 시간
```

- `memory.max`에 닿고 회수로도 못 줄이면 **그 cgroup 안에서** OOM killer가 돈다(kernel.org cgroup-v2).
- `memory.high`를 넘으면 스로틀되고 회수 압력을 받는다. 문서는 high 초과가 OOM killer를 부르지 않는다(never invokes)고 적는다. 극단적인 경우 high를 넘을 수도 있다(같은 문서).
- `memory.current`에는 익명 메모리뿐 아니라 **페이지 캐시**(그 cgroup이 읽고 쓴 파일)도 들어간다. 캐시는 회수 가능하므로 max에 닿으면 먼저 캐시를 버린다.
- `memory.events`의 `oom`·`oom_kill` 카운터로 OOM이 났는지 확인한다. `memory.oom.group=1`이면 cgroup 전체를 함께 죽인다(같은 문서).
- `memory.swap.max`로 cgroup의 스왑 사용 한도를 둔다. 기본은 `max`다.

쿠버네티스 `resources.limits.memory`는 이 한도로 이어진다. 한도를 넘어 죽은 컨테이너는 `reason: OOMKilled`, `exitCode: 137`로 보인다(쿠버네티스 문서 "Assign Memory Resources to Containers").

### 5. JVM 힙 < limit인데 죽는 이유

```text
  컨테이너 memory.max = 2GiB (예시)
  +------------------------------------------------+
  | 자바 힙 (-Xmx 1.5GiB)                            |
  +------------------------------------------------+
  | 메타스페이스 (기본 상한 없음)                       |
  | 스레드 스택 × 스레드 수                            |
  | 코드 캐시 (JIT 결과)                               |
  | direct buffer (NIO, 기본 상한 = 최대 힙 크기)        |
  | GC 자료구조, JNI·native 라이브러리의 malloc        |
  | glibc arena 여유 공간 (11번)                      |
  +------------------------------------------------+
  | 페이지 캐시 (파일 읽기·쓰기 — 회수 가능)              |
  +------------------------------------------------+
  합계가 2GiB를 넘고 회수로도 못 줄이면 → OOMKilled
```

- `-Xmx`는 **자바 힙만** 제한한다. JVM 프로세스의 나머지는 native 메모리다.
- `-XX:MaxMetaspaceSize`는 기본으로 상한이 없다(Oracle `java` 문서).
- direct buffer는 기본 상한이 있다. `-XX:MaxDirectMemorySize`를 안 주면 상한 = `Runtime.getRuntime().maxMemory()`, 즉 최대 힙 크기다(OpenJDK `jdk/internal/misc/VM.java` `saveProperties`). 그래서 힙을 limit 가까이 잡으면 direct buffer도 같은 양까지 커질 수 있다.
- JVM은 컨테이너 한도를 인식해 기본 최대 힙을 한도의 **25%**(`MaxRAMPercentage` 기본값)로 잡는다(Oracle `java` 문서, `UseContainerSupport`). 한도가 작으면 다르다.
  - 한도 × `MinRAMPercentage`(기본 50%)가 기본 `MaxHeapSize`(64비트 약 125MiB)보다 작으면, 즉 한도가 약 250MiB 미만이면 50%를 쓴다(OpenJDK `arguments.cpp` `set_heap_size` "Small physical memory").
  - 그 위에서도 25%가 약 125MiB보다 작으면 125MiB 근처로 올려 잡는다.
  - 로컬 확인(예시, OpenJDK 8u504, `-XX:MaxRAM`으로 한도 흉내): 200m → 100MiB, 400m → 126MiB, 1g → 256MiB, 4g → 1024MiB. 힙을 수동으로 한도 가까이 올리면 native 몫이 모자란다.
- 힙이 차면 JVM이 `OutOfMemoryError: Java heap space`를 던진다. 이것은 **JVM 안의** 에러라 로그가 남는다. 커널 OOM kill은 로그 없이 SIGKILL이다. 둘은 다른 사건이다.

## 쓰이는 자료구조·알고리즘

- **점수 기반 선택(oom_badness)** — 후보 전체를 훑어 최댓값을 고른다. 우선순위 큐도 아니고 정렬도 아닌 O(n) 선형 탐색이다(mm/oom_kill.c `select_bad_process`가 후보를 순회한다).
- **계층형 카운터(cgroup)** — 사용량을 자식에서 부모로 합산하는 트리다. 한도 검사는 경로 위의 모든 조상에서 한다. `memory.events`도 계층 합이다(kernel.org cgroup-v2).
- **약속 회계(commit accounting)** — `Committed_AS`는 매핑 종류별 비용을 더한 누적 카운터다. 파일의 공유·읽기 전용 매핑과 익명 private 읽기 전용 매핑은 비용 0, private 쓰기 매핑과 익명 공유 매핑은 크기만큼 센다(kernel.org overcommit-accounting).

## 적용 — 풀어나가는 법

### 1. 죽었다 — OOM인지부터 확정한다

```bash
# 쿠버네티스: 마지막 종료 이유
kubectl get pod <pod> -o jsonpath='{.status.containerStatuses[*].lastState.terminated}'

# 커널 로그 (dmesg_restrict=1이면 root 필요)
dmesg -T | grep -E 'Killed process|out of memory'
journalctl -k | grep -i 'killed process'

# cgroup v2: 이 cgroup에서 OOM kill이 몇 번 났나
cat /sys/fs/cgroup/<경로>/memory.events     # oom, oom_kill
cat /sys/fs/cgroup/<경로>/memory.max /sys/fs/cgroup/<경로>/memory.peak
```

- exit 137만으로는 OOM이라고 단정할 수 없다. 137은 "SIGKILL로 죽었다"일 뿐이다. 쿠버네티스 유예 시간 초과 뒤의 SIGKILL, 사람의 `kill -9`도 137이다(06번 시그널). `memory.events`의 `oom_kill`이나 커널 로그로 확인한다.

### 2. 누가 메모리를 쓰나 — 힙과 native를 나눈다

```bash
# 프로세스 전체
grep -E 'VmRSS|RssAnon|RssFile|VmSwap' /proc/<pid>/status
cat /proc/<pid>/oom_score /proc/<pid>/oom_score_adj

# JVM 내부 구성 (JVM을 -XX:NativeMemoryTracking=summary 로 띄운 경우)
jcmd <pid> VM.native_memory summary
```

- NMT는 JVM이 아는 native 영역(힙, class/metaspace, thread, code, GC 등)을 나눠 보여 준다(Oracle `java`·`jcmd` 문서). JVM 밖 라이브러리의 `malloc`은 NMT에 안 잡힌다. RSS와 NMT 합계의 차이가 그 몫이다.

### 3. 한도를 설계한다

```text
  memory.max  ≥  힙(Xmx) + 메타스페이스 + 스레드 수 × 스택 + 코드 캐시 + direct buffer + 여유
```

- 힙은 한도의 일정 비율로 잡는다(예: `-XX:MaxRAMPercentage=60~75`, 값은 예시 — native 사용량을 측정해 정한다).
- native 영역에 상한을 건다: 기본 상한이 없는 메타스페이스는 `-XX:MaxMetaspaceSize`로. direct buffer는 기본 상한(= 최대 힙)이 너무 크면 `-XX:MaxDirectMemorySize`로 더 작게 잡는다.
- `memory.high`를 max보다 조금 낮게 두면 죽기 전에 느려지는 단계가 생겨, 경보를 받을 여유가 생긴다.
- 꼭 살아야 하는 프로세스(예: 노드의 에이전트)는 `oom_score_adj`를 낮춘다. 하한 `oom_score_adj_min`보다 낮추려면 `CAP_SYS_RESOURCE`가 필요하다. 이 하한은 `CAP_SYS_RESOURCE`를 가진 쪽이 값을 쓸 때 그 값으로 갱신된다. 올리는 것은 권한 없이 된다(fs/proc/base.c `__set_oom_adj`).

```c
/* 스스로를 먼저 죽을 후보로 만든다 (권한 불필요) — 캐시 워커 등 */
int fd = open("/proc/self/oom_score_adj", O_WRONLY);
write(fd, "500", 3);
close(fd);
```

## 장애 시나리오와 대처

### 1. 컨테이너 `OOMKilled`(exit 137)

- **현상**: 파드가 부하 때마다 재시작한다. 재시작 횟수가 오른다.
- **보이는 형태**
  - `kubectl describe pod`: `Last State: Terminated, Reason: OOMKilled, Exit Code: 137`.
  - 애플리케이션 로그는 중간에 끊긴다. 스택 트레이스·종료 로그가 없다.
  - 노드 커널 로그에 `Memory cgroup out of memory: Killed process ...`.
- **원인**: 컨테이너 cgroup의 사용량이 `memory.max`(= limit)에 닿았고, 페이지 캐시를 버려도 못 줄였다. 커널이 그 cgroup 안에서 가장 큰 프로세스를 SIGKILL했다.
- **대처**
  - `memory.peak`·메트릭으로 실제 최대 사용량을 확인하고 limit을 맞춘다.
  - 무엇이 컸는지 나눈다(힙 vs native, 아래 2번).
  - 누수라면 limit을 올려도 시점만 늦춘다. 사용량 추세가 계속 오르는지 본다(reliability/37).

### 2. JVM 힙 < limit인데 native·메타스페이스로 초과

- **현상**: `-Xmx`는 limit의 절반인데 OOMKilled. 힙 사용률 그래프는 여유롭다.
- **보이는 형태**
  - RSS가 힙 최대치보다 한참 크다.
  - NMT에서 Thread(스레드 수 × 스택), Class(메타스페이스), Internal·Other(direct buffer 등)가 크다. 또는 NMT 합계보다 RSS가 훨씬 크다.
- **원인**
  - 스레드가 많다(요청당 스레드, 큰 풀). 스레드마다 스택이 있다.
  - 동적 클래스 생성(프록시·스크립트 엔진)으로 메타스페이스가 계속 는다. 기본 상한이 없다.
  - Netty 등 direct buffer 사용, JNI 라이브러리, glibc arena 여유 공간(11번).
- **대처**
  - `MaxRAMPercentage`로 힙을 한도의 비율로 잡아 native 몫을 남긴다.
  - `MaxMetaspaceSize`로 상한을 건다. direct buffer는 기본 상한(= 최대 힙)을 `MaxDirectMemorySize`로 더 작게 잡는다. 상한이 limit 안에 들어오면, 넘칠 때 커널 SIGKILL 대신 JVM의 `OutOfMemoryError`로 바뀐다. 로그와 힙 덤프가 남는다.
  - 스레드 수를 줄이거나 스택 크기(`-Xss`)를 조정한다. glibc arena가 의심되면 `MALLOC_ARENA_MAX`를 비교한다.

### 3. 노드 전체 OOM → 엉뚱한 프로세스가 죽음

- **현상**: 메모리를 많이 쓴 배치가 아니라 DB나 핵심 데몬이 죽었다.
- **보이는 형태**: 커널 로그 `Out of memory: Killed process <pid> (<이름>) ... oom_score_adj:0`. cgroup 이름 없이 전체 OOM이다.
- **원인**: 점수는 "지금 가장 많이 쓰는 프로세스"다. 원인 제공자가 아니라 가장 큰 프로세스가 죽는다. 큰 캐시를 가진 DB가 흔한 희생자다.
- **대처**
  - 서비스마다 cgroup 한도를 둬 전체 OOM 대신 해당 cgroup의 OOM으로 가둔다.
  - 핵심 프로세스의 `oom_score_adj`를 낮추고, 버려도 되는 워커는 올린다.
  - 모드 2(엄격 overcommit)는 "죽는 대신 할당 실패"로 바꾼다. 대신 모든 프로그램이 `ENOMEM`을 처리해야 한다.

### 4. 할당 실패 `ENOMEM` — OOM kill과 다른 길

- **현상**: 프로세스가 죽지 않고 `Cannot allocate memory`를 낸다. `fork: Cannot allocate memory` 등. 자바 `OutOfMemoryError: unable to create native thread`(07번)도 같은 계열이지만, 이때 `pthread_create`는 스택을 못 받아도(`ENOMEM`) `EAGAIN`으로 바꿔 돌려준다(pthread_create(3), glibc `nptl/pthread_create.c`).
- **보이는 형태**: errno `ENOMEM`(스레드 생성은 `EAGAIN`). 커널 OOM 로그는 없다.
- **원인**: 할당 **시점**의 거절이다. `RLIMIT_AS`(`ulimit -v`), overcommit 모드 2의 `CommitLimit`, 또는 모드 0의 과도한 단일 요청.
- **대처**: `ulimit -a`, `/proc/meminfo`의 `CommitLimit`·`Committed_AS`, `vm.overcommit_memory`를 본다. 가상 주소를 크게 예약하는 프로그램(JVM, 일부 DB)은 가상 주소 한도와 궁합이 나쁘다.

## 핵심 문장

- 리눅스의 `malloc` 성공은 "가상 주소를 약속했다"는 뜻이다. 물리 메모리는 처음 건드릴 때 붙는다. 약속을 다 쓰려 할 때 모자라면 거절할 수 없어 OOM killer가 나선다.
- `overcommit_memory` 0은 뻔한 초과만 거절, 1은 항상 허용, 2는 `CommitLimit`까지만 약속한다. 2는 "죽음" 대신 "할당 실패"를 준다.
- OOM killer는 RSS + 스왑 + 페이지 테이블에 `oom_score_adj`를 더한 점수가 가장 큰 프로세스를 SIGKILL한다. -1000은 제외다. 종료 코드는 137이고 애플리케이션은 로그를 못 남긴다.
- 컨테이너 limit은 cgroup `memory.max`다. 넘으면 그 cgroup 안에서만 OOM kill이 일어나고 쿠버네티스는 `OOMKilled`(137)로 보여 준다.
- `-Xmx`는 힙만 막는다. 메타스페이스·스레드·direct buffer·native `malloc`까지 더한 값이 limit 안에 들어와야 한다.

## 관련 주제·근거

- 선행: [12-swapping-and-page-replacement](../12-swapping-and-page-replacement/2-summary.md) — 회수·스왑으로도 안 될 때 여기로 온다
- 후속·연결
  - [11-heap-allocation](../11-heap-allocation/2-summary.md) — native `malloc`, glibc arena
  - [14-mmap-and-page-cache](../14-mmap-and-page-cache/2-summary.md) — cgroup 사용량에 들어가는 페이지 캐시
  - [06-signals](../06-signals/2-summary.md) — SIGKILL·exit 137
  - [07-threads-and-context-switch](../07-threads-and-context-switch/2-summary.md) — `unable to create native thread`
  - [28-containers-namespaces-cgroups](../28-containers-namespaces-cgroups/2-summary.md) — cgroup 전반
  - [language/README](../../language/README.md) — `11-gc-tuning-and-gc-logs`(`MaxRAMPercentage`). 미작성
  - [reliability/README](../../reliability/README.md) — `37-memory-leak-and-heap-analysis`(힙 밖 누수·NMT). 미작성
- 커널 문서·소스
  - Overcommit Accounting — 모드 0/1/2, `CommitLimit`·`Committed_AS`, 매핑별 비용 <https://docs.kernel.org/mm/overcommit-accounting.html>
  - sysctl/vm — `overcommit_memory`(기본 0), `overcommit_ratio`(50) <https://docs.kernel.org/admin-guide/sysctl/vm.html>
  - Control Group v2 — `memory.current/high/max/peak/events/oom.group/swap.max` <https://docs.kernel.org/admin-guide/cgroup-v2.html>
  - `mm/oom_kill.c` — `oom_badness`, `select_bad_process`, `__oom_kill_process`(SIGKILL, 로그 형식) <https://github.com/torvalds/linux/blob/master/mm/oom_kill.c>
  - `mm/util.c` `__vm_enough_memory` — 모드 0에서 RAM + 스왑 초과 요청 거절
  - `fs/proc/base.c` `proc_oom_score` — 표시용 점수 환산 · `__set_oom_adj` — `oom_score_adj_min` 아래로 낮출 때 `CAP_SYS_RESOURCE`
- man
  - proc_pid_oom_score_adj(5), proc_pid_oom_score(5) <https://man7.org/linux/man-pages/man5/proc_pid_oom_score_adj.5.html>
  - proc_meminfo(5) `CommitLimit`·`Committed_AS`, proc_sys_vm(5) `CommitLimit` 식
  - malloc(3) NOTES — 낙관적 할당과 OOM killer · pthread_create(3) — `EAGAIN` "Insufficient resources"
- Oracle, `java` 명령 문서(JDK 21) — `MaxRAMPercentage`(기본 25), `NativeMemoryTracking`, `MaxMetaspaceSize`(기본 무제한), `MaxDirectMemorySize`, `MinRAMPercentage`(기본 50) <https://docs.oracle.com/en/java/javase/21/docs/specs/man/java.html>
- OpenJDK 21 소스 — `jdk/internal/misc/VM.java` `saveProperties`(`MaxDirectMemorySize` 미지정 시 `Runtime.getRuntime().maxMemory()`), `hotspot/share/runtime/arguments.cpp` `set_heap_size`(작은 메모리면 `MinRAMPercentage`), `gc/shared/gc_globals.hpp` `MaxHeapSize` 기본 `ScaleForWordSize(96*M)` <https://github.com/openjdk/jdk21u> · `jcmd` `VM.native_memory`
- Kubernetes, "Assign Memory Resources to Containers and Pods" — `reason: OOMKilled`, `exitCode: 137` <https://kubernetes.io/docs/tasks/configure-pod-container/assign-memory-resource/>
- 교재: OSTEP 22.11(OOM killer와 스래싱)
- 로컬 재현(리눅스 7.0): `/proc/meminfo` CommitLimit 계산 대조, overcommit 모드 1에서 `malloc(1TiB)` 성공, `ulimit -v`에서 `ENOMEM`, `oom_score` 환산식 대조(733), cgroup v2 `memory.*` 파일 읽기, `java -XX:+PrintFlagsFinal`로 `MaxRAMPercentage 25`·`UseContainerSupport` 확인(OpenJDK 8u504)
