# architecture/20-multicore-and-numa — 코어가 여럿이면 생기는 일: 멀티코어·SMT·하이브리드 코어·NUMA — 정리 (힌트)

## 해결하는 문제

클록을 계속 올리기 어려워지자 CPU는 코어 수를 늘리는 쪽으로 갔다. 그런데 "코어 N개 = N배 빠름"은 아니다.

```text
  같은 코드인데 결과가 다르다
  ① 두 스레드를 같은 물리 코어(SMT 형제)에 놓으면 → 어떤 일은 각자 반 속도, 어떤 일은 그대로
  ② P코어에 놓으면 빠르고 E코어에 놓으면 느리다 (하이브리드 CPU)
  ③ 메모리가 다른 소켓에 붙어 있으면 → 같은 load가 더 오래 걸린다 (NUMA)
  ④ 코어보다 스레드가 많으면 → 처리량은 안 늘고 지연과 경합만 는다
```

- 이것을 모르면 스레드 수·배치·메모리 위치를 운에 맡기고, "같은 서버 같은 코드인데 어떤 인스턴스만 느리다"를 설명하지 못한다.

쉬운 예: 사무실.
- 한 책상에 두 사람(SMT): 서로 다른 일을 하면 책상을 나눠 써도 괜찮다. 둘 다 같은 계산기를 계속 쓰면 번갈아 써야 한다.
- 정규직 자리와 보조석(P/E 코어): 같은 일을 줘도 처리 속도가 다르다.
- 자료실이 층마다 있다(NUMA): 내 층 자료실은 가깝고, 다른 건물 자료실은 멀다. 내 자료를 다른 건물에 두면 매번 걸어가야 한다.
- 사람보다 일감 묶음을 더 많이 나눠 줘도(스레드 과다) 일하는 사람 수는 그대로다. 대신 서로 기다리는 시간만 는다.

똑같은 구조다.\
실무 예: 큰 DB 서버에서 같은 쿼리가 어떤 때는 빠르고 어떤 때는 느리다. 스레드가 다른 소켓으로 옮겨져 메모리가 원격이 된 경우다.

## 동작·원리

### 1. 토폴로지 — 소켓 → 코어 → 하드웨어 스레드

이 호스트(i7-13700HX)의 `lscpu -e` 출력을 그림으로 옮겼다.

```text
  소켓 0 ─ NUMA 노드 0 (메모리 전부 여기, 약 37GB)
  ├─ P코어 8개 (최대 4.8~5.0GHz) — 코어마다 하드웨어 스레드 2개 (SMT)
  │    코어0: CPU0 CPU1   코어1: CPU2 CPU3   ...   코어7: CPU14 CPU15
  │    코어마다 L1d 48KiB · L1i 32KiB · L2 1.25MiB  (형제 두 CPU가 공유)
  ├─ E코어 8개 (최대 3.7GHz) — SMT 없음
  │    CPU16 CPU17 CPU18 CPU19 | CPU20 CPU21 CPU22 CPU23
  │    코어마다 L1d 32KiB · L1i 64KiB,  L2 2MiB를 4코어가 공유 (16-19, 20-23)
  └─ L3 30MiB — CPU 0~23 전부 공유
```

- 근거: `lscpu -e=CPU,NODE,SOCKET,CORE,CACHE,MAXMHZ`, `/sys/devices/system/cpu/cpu*/cache/index*/{size,shared_cpu_list}`, `/sys/devices/cpu_core/cpus`(0-15)·`/sys/devices/cpu_atom/cpus`(16-23).
  - *논리 CPU*: OS가 스케줄하는 단위. `/proc/cpuinfo`·`nproc --all`이 세는 것. 이 호스트는 24개다. 옵션 없는 `nproc`는 현재 프로세스가 **쓸 수 있는** 수를 내므로 친화도·cgroup 제한 아래서는 더 작을 수 있다(GNU Coreutils `nproc`).
  - *SMT(Simultaneous Multithreading, Intel 명칭 Hyper-Threading)*: 물리 코어 하나가 명령 흐름 둘을 동시에 받는 것. 레지스터 상태는 따로, 실행 유닛·L1·L2는 같이 쓴다.
    - 흔한 오해: "논리 CPU 24개 = 코어 24개." — 이 호스트의 물리 코어는 16개다. SMT 형제 둘은 실행 유닛을 나눠 쓴다(Drepper 2007 §3.3.4).
  - *하이브리드 CPU*: 성능 코어(P)와 효율 코어(E)를 한 칩에 섞은 것. 같은 ISA를 실행하지만 속도·캐시가 다르다.
- 캐시 일관성(코어 사이 같은 주소의 값 맞추기)은 [14-cache-coherence-and-memory-ordering](../14-cache-coherence-and-memory-ordering/2-summary.md), false sharing은 [12-cache-organization](../12-cache-organization/2-summary.md)에 있다.

### 2. SMT 형제는 무엇을 나눠 쓰나

```text
  물리 코어 하나
  ┌─────────────────────────────────────────┐
  │ [스레드 A 레지스터]   [스레드 B 레지스터]  │  ← 따로
  │ ───────── 디코더 · 스케줄러 ─────────     │
  │  ALU  ALU  ALU  MUL  LOAD  LOAD  STORE   │  ← 같이 쓴다
  │  L1d · L2                                 │  ← 같이 쓴다
  └─────────────────────────────────────────┘
  A가 메모리를 기다리며 실행 유닛을 놀리면 → B가 그 빈칸을 쓴다 (이득)
  A와 B가 모두 실행 유닛을 꽉 채우면       → 나눠 써서 각자 느려진다 (이득 없음)
```

- Drepper 2007 §3.3.4: 하이퍼스레드의 이득은 한 스레드가 지연될 때(대개 메모리 접근) 다른 스레드가 ALU 같은 자원을 쓰는 데서 나온다. 대신 두 스레드가 같은 캐시를 써 각자의 실효 캐시 크기가 반으로 준다고 본다(작업 집합이 겹치지 않을 때의 모형 — 캐시를 반씩 고정 배분하는 것은 아니고, 한 스레드가 더 많이 차지할 수도 있다). 그래서 "제한된 상황에서만 쓸모 있다"고 정리한다.

#### 실험: 같은 코드를 P코어·SMT 형제·E코어에 고정 (`cores.c`)

스레드를 `sched_setaffinity`로 CPU 하나씩에 고정하고 1초 동안 일을 시켰다. 일은 세 종류다.

```c
// chain: 앞 결과가 다음 입력 — 곱셈 지연이 지배
for (...) { x = x * 6364136223846793005ULL + 1442695040888963407ULL; x ^= x >> 29; }
// wide: 서로 독립인 사슬 8개 — 실행 유닛 수가 지배
for (...) for (j = 0; j < 8; j++) { y[j] = y[j] * 6364136223846793005ULL + 1442695040888963407ULL; y[j] ^= y[j] >> 29; }
// chase: 64MiB 무작위 순환을 따라가기 (i = next[i]) — 메모리 지연이 지배 (L3 30MiB보다 큼)
```

환경: i7-13700HX, Linux 7.0.0-34, gcc 13.3 `-O2 -pthread`, 호스트에서 직접 실행, 3회. 호스트에 다른 부하가 있었다(CPU별 사용률 11~100%, 그래서 회차 사이 흔들림이 있다).

```text
                          chain (Mops/s/스레드)   wide (Mops/s/스레드)   chase (ns/load)
  P코어 1개   (CPU4)        138~149                 426~469                199~208
  다른 P코어 2 (CPU4,8)     142~151                 339~454                209~217
  SMT 형제 2  (CPU4,5)      134~150                 200~223                206~213
  E코어 1개   (CPU20)       104~113                 337~363                248~256
  E코어 2     (CPU20,21)    106~112                 350~361                241~252
```

- 관찰 1(wide): SMT 형제에 두면 스레드당 200~223으로, 혼자일 때(426~469)의 약 절반이다. 둘을 합쳐도(403~442) 코어 하나 몫이다. 이 일(wide)은 SMT로 처리량이 늘지 않았다. 실행 유닛을 꽉 채우는 일이라 그렇다고 해석한다(아래 perf 불가 참고).
- 관찰 2(chain·chase): SMT 형제에 둬도 스레드당 속도가 거의 그대로다. 합계는 약 2배다. 한 스레드가 곱셈 결과나 메모리를 기다리는 동안 다른 스레드가 빈 유닛을 쓴 것으로 해석한다.
- 관찰 3: E코어는 같은 일에서 P코어보다 chain 약 18~30%, wide 약 15~28% 느렸고, 메모리 한 번 따라가기가 약 40~57ns 길었다(범위 끝끼리 비교). 점검 재실행에서는 P 198~225ns · E 239~252ns로, 한 회차는 차이가 14ns까지 줄었다. 호스트 부하(load average 약 9)에 흔들리는 값이다.
- 관찰 4: "다른 P코어 2"의 wide에서 한 회차가 339/374로 낮았다. 그 회차에 다른 프로세스가 CPU8의 형제(CPU9)나 CPU8을 쓴 것으로 보인다(해석). 공유 호스트에서는 "같은 코어 다른 스레드"가 이웃의 부하에 흔들린다.
- 하드웨어 카운터(perf)는 이 환경에서 쓸 수 없었다(`perf_event_paranoid=4`). "실행 유닛 경합" "메모리 대기"는 작업 설계와 Drepper의 설명에 기댄 해석이다.

### 3. NUMA — 메모리에도 거리가 있다

```text
     노드 0                                   노드 1
  ┌──────────────┐    소켓 간 연결(QPI/UPI,   ┌──────────────┐
  │ 코어 0~15    │ ◄──── Infinity Fabric 등) ──►│ 코어 16~31   │
  │ 메모리 컨트롤러│                            │ 메모리 컨트롤러│
  └──────┬───────┘                            └──────┬───────┘
      로컬 DRAM                                    로컬 DRAM
   코어 3이 노드 0 메모리 읽기: 로컬(빠름)
   코어 3이 노드 1 메모리 읽기: 연결을 한 번 건넘(원격, 느림)       (2소켓 예시)
```

- *NUMA(Non-Uniform Memory Access)*: 메모리가 여러 노드에 나뉘어 붙어 있어, 어느 코어에서 어느 메모리를 읽느냐에 따라 접근 비용이 다른 구조.
  - *NUMA 노드*: 코어 묶음 + 그 코어에 가까운 메모리.
  - *NUMA factor*: 원격 접근이 로컬보다 얼마나 더 드는지(Drepper §5.1).
- 수치 예(Drepper §5.4, AMD가 문서화한 4소켓 기계 — 같은 절의 Opteron 시스템 맥락): 2-hop 읽기·쓰기는 0-hop 읽기보다 30%·49% 느렸다. 오래된 하드웨어의 수치이고, 요즘 서버의 값은 플랫폼마다 다르다 `[?]`.
- 이 호스트는 노드가 하나다. 그래서 원격 접근을 재현할 수 없다. 아래 출력을 읽는 법으로 대신한다.

```text
  $ numactl -H                                  (이 호스트)
  available: 1 nodes (0)
  node 0 cpus: 0 1 2 ... 23
  node 0 size: 37775 MB
  node distances:
  node   0
    0:  10

  $ numactl -H                                  (2소켓 서버의 모양 — 예시, 수치는 플랫폼마다 다름)
  available: 2 nodes (0-1)
  node 0 cpus: 0 1 2 ... 15 32 33 ... 47
  node 1 cpus: 16 17 ... 31 48 49 ... 63
  node distances:
  node   0   1
    0:  10  21
    1:  21  10
```

- *노드 거리(distance)*: 펌웨어(ACPI SLIT)가 알려 주는 상대 비용. 자기 자신을 10으로 둔다. 21이면 "로컬의 약 2.1배쯤"이라는 펌웨어의 주장일 뿐, 실측 지연비와 같다는 보장은 없다 `[?]`.

### 4. Linux는 메모리를 어디에 두나

- 기본 정책은 **로컬 할당**이다. 페이지를 할당하는(처음 건드리는) CPU가 속한 노드에서 먼저 준다(kernel docs `admin-guide/mm/numa_memory_policy`: 시스템이 뜬 뒤 기본 정책은 "local allocation", 부팅 중에는 인터리브).
  - 결과: **처음 쓴 스레드의 노드에 메모리가 놓이기 쉽다(first touch).** 그 노드에 빈 메모리가 모자라면 거리 순으로 다른 노드에서 준다(kernel docs `mm/numa`의 fallback). 메모리 정책·`numa_balancing`도 배치를 바꾼다. 초기화를 스레드 하나가 하고 일은 다른 노드 스레드들이 하면, 원격 접근이 많이 생길 수 있다.
- `numa_balancing`을 켜면 커널이 페이지를 주기적으로 언매핑해 누가 접근하는지 표본을 뜨고, 자주 접근하는 노드로 옮긴다(kernel docs `admin-guide/sysctl/kernel`). 이 호스트는 단일 노드라 0(꺼짐)이다.
- 스케줄러도 노드를 넘는 이주를 피하려 한다. 넘기면 캐시도 잃고 메모리도 원격이 되기 때문이다(Drepper §5.2).
- 관찰 도구
  - `numastat`: `numa_hit`·`numa_miss`·`other_node`. 이 값들은 **페이지 할당** 통계다(원하던 노드에서 받았나, 다른 노드 CPU가 이 노드 메모리를 받았나 — kernel docs `admin-guide/numastat`). 이미 할당된 페이지를 원격으로 읽는 횟수는 세지 않는다. 이 호스트: `numa_miss 0`, `other_node 0`(노드가 하나라 당연하다).
  - `/proc/<pid>/numa_maps`: 매핑마다 노드별 페이지 수(`N0=…`, `N1=…`). Drepper §5.4가 Figure 5.2로 같은 파일을 읽는다.

### 5. 코어보다 스레드가 많으면

```text
  CPU 2개, 스레드 8개
  CPU0: [T1][T3][T5][T7][T1][T3]...   ← 시간을 나눠 번갈아
  CPU1: [T2][T4][T6][T8][T2][T4]...
  처리량 = CPU 2개 몫 그대로.  일 하나가 끝나는 시간 = 차례를 기다린 만큼 길어짐
  락을 쥔 스레드가 차례를 뺏기면 → 그 락을 기다리는 나머지가 다 멈춤
```

#### 실험: CPU 2개에 스레드 1~32개 (`Oversub.java`)

```java
x = work(x, 2000);                         // 락 밖 계산
if (mode.equals("locked")) {
    lock.lock();
    try { shared = work(shared + x, 500); } // 락 안 계산 (락 밖의 1/4)
    finally { lock.unlock(); }
}
```

환경: Docker `eclipse-temurin:21-jdk`(21.0.12) `--cpuset-cpus=4,6`(P코어 2개, 서로 다른 물리 코어) `--network none`, 1.5초씩, JVM 3회. `Runtime.availableProcessors()` = 2.

```text
                  처리량 (ops/s)            작업 1건 최악 지연
  indep  1      65,949~70,790               0.30~4.04 ms
  indep  2     138,013~139,915              4.03~5.03 ms
  indep  4     138,984~140,253              9.03~12.02 ms
  indep  8     144,333~146,105             16.12~19.02 ms
  indep 32     141,430~144,804             65.03~97.03 ms
  locked 1      57,161~58,617               0.11~2.49 ms
  locked 2      96,535~105,211              5.03~11.93 ms
  locked 4      79,894~92,396              12.03~13.67 ms
  locked 8      64,138~79,457              19.02~42.04 ms
  locked 32     64,511~78,384              60.18~125.06 ms
```

- 관찰 1(독립 계산): 스레드 2개에서 처리량이 약 2배가 되고, 그 뒤로는 거의 늘지 않았다(8개가 2개보다 약 3~6% 높았다 — 2개 138,013~139,915 vs 8개 144,333~146,105. 원인은 재지 않았다). 최악 지연은 스레드 수에 비례해 커졌다(32개에서 65~97ms).
- 관찰 2(락 구간): 스레드 2개가 가장 좋았다. 4·8·32개로 늘리자 처리량이 같은 회차의 2개 대비 약 7~39% 떨어졌고 최악 지연은 60~125ms까지 갔다.
  - 해석(가능한 설명 — 락 보유 중 선점을 직접 재지는 않았다): 락을 쥔 스레드가 타임슬라이스를 뺏기면 그동안 아무도 락 구간에 못 들어간다. 스레드가 많을수록 이런 일이 잦을 수 있다. 기다리는 스레드의 깨어남·문맥 전환 비용도 든다([os/16](../../os/16-locks-and-spinlocks/2-summary.md) 장애 2).
- 최악 지연에는 JIT 컴파일·GC가 섞여 있을 수 있다. 처리량 비교가 주된 결론이다.

## 쓰이는 자료구조·알고리즘

- **CPU 집합 = 비트마스크** — `sched_setaffinity`의 `cpu_set_t`, `taskset` 마스크, cgroup `cpuset`. [data-structure/18-bitset](../../data-structure/18-bitset/2-summary.md)
- **스레드 배치(affinity)** — 같은 데이터를 쓰는 스레드는 같은 노드·같은 L2 묶음에, 실행 유닛을 다투는 스레드는 다른 물리 코어에.
- **작업 훔치기(work stealing)** — CPU별 큐 + 한가한 쪽이 가져오기. 스케줄러([os/08](../../os/08-cpu-scheduling/2-summary.md))와 `ForkJoinPool`이 쓴다. 덱 구조는 [data-structure/04-queue-deque](../../data-structure/04-queue-deque/2-summary.md)
- **샤딩·스트라이핑으로 경합 줄이기** — `LongAdder`처럼 카운터를 칸으로 나눴다가 합친다. [data-structure/29-concurrent-data-structures](../../data-structure/29-concurrent-data-structures/2-summary.md)
- **큐잉 모형** — 스레드 수를 일할 CPU 수 이상 늘려도 처리량은 서버(CPU) 몫이 상한이다. [math/10-queueing-and-littles-law](../../math/10-queueing-and-littles-law/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 먼저 토폴로지를 읽는다

```bash
lscpu                       # 소켓·코어·스레드 수, NUMA 노드와 그 CPU 목록, 캐시 크기
lscpu -e=CPU,NODE,SOCKET,CORE,CACHE,MAXMHZ   # CPU별: 같은 CORE 번호 = SMT 형제, MAXMHZ로 P/E 구분
numactl -H                  # 노드별 CPU·메모리 크기·빈 메모리, 노드 거리
cat /sys/devices/system/cpu/cpu0/topology/thread_siblings_list   # CPU0의 SMT 형제 (이 호스트: 0-1)
numastat                    # numa_miss·other_node가 늘고 있나 (할당 통계 — 원격 읽기 횟수는 아니다)
```

- 읽는 순서: 노드가 몇 개인가 → 각 노드의 CPU·메모리 → SMT 형제 짝 → 코어 종류(MAXMHZ, `cpu_core`/`cpu_atom`) → 캐시를 공유하는 묶음.

### 2. 스레드 수를 정한다

- CPU 계산 위주: 쓸 수 있는 코어 수 근처. SMT가 있으면 일의 성격에 따라 물리 코어 수 ~ 논리 CPU 수 사이에서 잰다(실험의 wide는 물리 코어, chain·chase는 논리 CPU까지 이득).
- I/O 대기 위주: 대기 비율만큼 더 둔다(Little). 다만 락·DB 커넥션 같은 공유 자원 앞에서는 그 자원 수가 상한이다.
- 컨테이너: JDK 21은 cgroup 제한을 읽어 `availableProcessors()`를 맞춘다(실험: `--cpuset-cpus=4,6`에서 2). 스레드 풀 기본값이 이 값을 따른다.

```java
int cpus = Runtime.getRuntime().availableProcessors();        // 컨테이너 제한 반영
var cpuPool = Executors.newFixedThreadPool(cpus);              // 계산 작업
var ioPool  = Executors.newVirtualThreadPerTaskExecutor();     // 대기 작업 (상한은 세마포어로)
```

### 3. NUMA가 있는 서버라면

- 프로세스를 한 노드에 묶는다: `numactl --cpunodebind=0 --membind=0 java ...`. 노드 하나의 메모리보다 큰 힙이면 쓰지 않는다(그 노드에서 메모리가 모자라면 할당 실패·스왑이 된다).
- 노드 전체에 고르게 퍼뜨린다: `numactl --interleave=all ...`. 페이지를 노드들에 돌아가며 놓는 배치 정책이다(kernel docs `numa_memory_policy`). 여러 노드 스레드가 고루 읽는 데이터면 접근이 평균화된다. 지연을 보장하지는 않는다. 한 노드에서 주로 쓰는 데이터면 원격 페이지가 늘어 오히려 느려질 수 있고, 최선(전부 로컬)도 포기한다.
- JVM: `-XX:+UseNUMA`(이 JDK 21의 기본값은 `false` — `-XX:+PrintFlagsFinal`로 확인). 켜면 Parallel GC 등에서 영 영역을 노드별로 나눠 할당한다(HotSpot 문서 `[?]`).
- 초기화하는 스레드와 쓰는 스레드를 같은 노드에 두거나, 쓰는 스레드가 각자 자기 몫을 초기화한다(first touch).

## 장애 시나리오와 대처

### 1. NUMA 원격 접근 → 같은 코드인데 지연 편차 (⚠)

- **현상**: 같은 서버·같은 요청인데 어떤 인스턴스·어떤 시간대만 p99가 높다. 재시작하면 좋아졌다 나빠졌다 한다.
- **보이는 형태**: `/proc/<pid>/numa_maps`·`numastat -p <pid>`에서 힙 매핑의 페이지가 실행 중인 노드가 아닌 `N1=`에 몰려 있다(스레드가 도는 노드는 `ps -eLo tid,psr`로 본다). 프로세스의 CPU 사용률은 같은데 처리량이 다르다. `numastat`의 `numa_miss`·`other_node`는 할당 통계라, 할당 뒤 스레드가 옮겨 가서 생긴 원격 접근에는 늘지 않을 수 있다.
- **원인**: 메모리를 처음 건드린 스레드의 노드에 페이지가 할당됐고(로컬 할당 기본), 스케줄러가 스레드를 다른 노드로 옮겼거나, 초기화와 처리가 다른 노드에서 일어났다. 원격 접근은 로컬보다 비싸다(Drepper §5.4 예: 30~49%).
- **대처**: `numactl`로 노드 고정, 인스턴스를 노드당 하나로 쪼개기, JVM `-XX:+UseNUMA` 검토, `numa_balancing` 상태 확인. 바꾼 뒤 같은 부하로 p99를 다시 잰다.

### 2. 코어 수 이상 스레드 → 경합으로 처리량 하락 (⚠)

- **현상**: 처리량을 올리려고 스레드 풀을 키웠는데 처리량은 그대로거나 줄고 지연이 늘었다.
- **보이는 형태**: 실험: CPU 2개에서 락 구간이 있는 일은 스레드 2개 96,535~105,211 ops/s → 32개 64,511~78,384 ops/s, 최악 지연 60~125ms. `vmstat`의 `cs`(문맥 전환)·`r`(실행 대기) 증가, 스레드 덤프에 같은 락 대기 다수.
- **원인**: 계산 위주 일의 처리량 상한은 일할 수 있는 CPU 몫이다(실험은 2개). 더 많은 스레드는 순서를 기다릴 뿐이다. 락 보유자가 선점되면 모두가 멈추는 것도 가능한 원인이다(실험은 이것을 직접 재지 않았다).
- **대처**: 계산 풀은 코어 수 근처로. 경합 지점을 줄인다(락 구간 축소, `LongAdder`·샤딩). 컨테이너면 쿼터·cpuset과 풀 크기를 맞춘다.

### 3. 무거운 두 스레드가 SMT 형제에 → 각자 반 속도

- **현상**: 코어가 남는데도 두 계산 작업이 기대의 절반 속도다.
- **보이는 형태**: `ps -eLo pid,tid,psr,pcpu,comm`의 `psr`이 같은 물리 코어의 형제(이 호스트 예: 4와 5)다. 실험(wide): 스레드당 426~469 → 200~223 Mops/s.
- **원인**: SMT 형제는 실행 유닛을 나눠 쓴다. 유닛을 꽉 채우는 일은 둘로 나눠도 합이 코어 하나 몫이다.
- **대처**: 무거운 계산 스레드는 서로 다른 물리 코어에 고정하거나(`taskset`), 그런 서버는 스레드 수를 물리 코어 수로 맞춘다. 메모리 대기가 많은 일이면 SMT가 오히려 이득이니 재 보고 정한다.

### 4. 하이브리드 CPU에서 일부 요청만 느림

- **현상**: 같은 요청인데 응답 시간이 두 무리로 갈린다.
- **보이는 형태**: 느린 요청을 처리한 스레드의 `psr`이 E코어(이 호스트 16~23)다. 실험: E코어에서 chain 약 18~30%, 메모리 따라가기 대개 약 40~57ns 느림(재실행 한 회차는 14ns). NVMe 읽기 평균 지연도 E코어에서 제출하면 약 8~18µs 길었다([15번](../15-io-devices-interrupts-dma/2-summary.md)).
- **원인**: P/E 코어는 클록·캐시가 다르다. 스케줄러가 어디에 놓느냐에 따라 같은 일의 속도가 달라진다.
- **대처**: 지연에 민감한 서비스는 P코어로 cpuset을 제한한다. 벤치마크는 코어 종류를 고정하고 잰다. 많은 서버 CPU는 한 종류 코어만 두지만 클라이언트·노트북 개발 환경 측정값을 운영에 옮길 때 조심한다.

## 핵심 문장

- 논리 CPU 수 ≠ 물리 코어 수다. SMT 형제는 실행 유닛과 L1·L2를 나눠 쓴다.
- 실행 유닛을 꽉 채우는 일은 SMT 형제에서 각자 반 속도가 되고, 지연을 기다리는 일은 거의 그대로다.
- NUMA에서는 메모리에도 거리가 있다. Linux 기본은 처음 건드린 CPU의 노드에서 먼저 할당하므로, 초기화하는 스레드의 위치가 이후 성능을 크게 좌우할 수 있다.
- 계산 위주 일의 처리량 상한은 일할 수 있는 CPU 몫이다(SMT 형제가 이득인 일이면 물리 코어 수보다 클 수 있다). 그보다 많은 스레드는 기다림·문맥 전환을 늘리고 락 보유자 선점 위험을 키운다.
- 배치를 바꾸기 전에 `lscpu -e`·`numactl -H`·`numa_maps`로 토폴로지와 메모리 배치를 먼저 읽는다.

## 관련 주제·근거

- 선행
  - architecture [14-cache-coherence-and-memory-ordering](../14-cache-coherence-and-memory-ordering/2-summary.md) — 코어 사이 일관성, CAS
  - architecture [12-cache-organization](../12-cache-organization/2-summary.md) — false sharing
- 후속·연결
  - architecture [21-simd-and-gpu](../21-simd-and-gpu/2-summary.md) — 코어 안의 데이터 병렬
  - architecture [11-memory-hierarchy-and-locality](../11-memory-hierarchy-and-locality/2-summary.md) · [13-latency-numbers](../13-latency-numbers/2-summary.md)
  - architecture [15-io-devices-interrupts-dma](../15-io-devices-interrupts-dma/2-summary.md) — IRQ를 어느 코어가 받나
  - os [08-cpu-scheduling](../../os/08-cpu-scheduling/2-summary.md) — CPU별 큐·이주·친화도·cgroup 쿼터
  - os [16-locks-and-spinlocks](../../os/16-locks-and-spinlocks/2-summary.md) — 락 경합으로 처리량 역전
  - os [02-system-calls](../../os/02-system-calls/2-summary.md) — `getcpu`(지금 CPU·노드 번호)
  - data-structure [29-concurrent-data-structures](../../data-structure/29-concurrent-data-structures/2-summary.md) · [18-bitset](../../data-structure/18-bitset/2-summary.md)
  - math [10-queueing-and-littles-law](../../math/10-queueing-and-littles-law/2-summary.md)
- 교재·문서
  - Drepper "What Every Programmer Should Know About Memory" (2007) — §3.3.4 Multi-Processor Support(하이퍼스레드), §5.1 NUMA Hardware(NUMA factor), §5.2 OS Support for NUMA(이주 회피), §5.3 Published Information(`/sys`), §5.4 Remote Access Costs(2-hop 30%·49%, Figure 5.2 `numa_maps`), §6.5 NUMA 메모리 정책 <https://people.freebsd.org/~lstewart/articles/cpumemory.pdf>
  - CS:APP 3판 12.6 "Using Threads for Parallelism", 1.9.2 "Concurrency and Parallelism"(3판 목차 <https://csapp.cs.cmu.edu/3e/pieces/preface3e.pdf>로 절 번호 확인, 본문은 이번에 열지 않음)
  - Linux `admin-guide/mm/numa_memory_policy` — 기본 local allocation, 부팅 중 인터리브 <https://docs.kernel.org/admin-guide/mm/numa_memory_policy.html>
  - Linux `admin-guide/sysctl/kernel` — `numa_balancing` <https://docs.kernel.org/admin-guide/sysctl/kernel.html>
  - `numactl(8)`, `numastat(8)`, `lscpu(1)` 매뉴얼
- 실험 목록(i7-13700HX, Linux 7.0.0-34, 2026-10-07)
  - 토폴로지 읽기: `lscpu`, `lscpu -e=CPU,NODE,SOCKET,CORE,CACHE,MAXMHZ`, `numactl -H`, `numactl --show`, `numastat`, `/sys/devices/system/cpu/cpu*/cache/index*`, `/sys/devices/cpu_{core,atom}/cpus`, `/proc/sys/kernel/numa_balancing`(0), JDK 21 `-XX:+PrintFlagsFinal`(`UseNUMA=false`)
  - `cores.c`(gcc 13.3 `-O2 -pthread`, 호스트) — chain·wide·chase × P1·P2·SMT 형제·E1·E2, 1초씩 3회
  - `Oversub.java` — Docker `eclipse-temurin:21-jdk` `--cpuset-cpus=4,6 --network none`, 스레드 1·2·4·8·32 × 독립/락, JVM 3회
