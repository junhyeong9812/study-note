# architecture/15-io-devices-interrupts-dma — 장치와 CPU가 일을 주고받는 법: 폴링, 인터럽트, DMA — 정리 (힌트)

## 해결하는 문제

CPU는 나노초 단위로 일한다. 디스크·NIC 같은 장치는 마이크로초~밀리초 단위로 일한다. 둘 사이에는 두 가지 질문이 남는다.

```text
  질문 1: 장치가 일을 끝냈는지 CPU가 어떻게 아나?      → 폴링 / 인터럽트
  질문 2: 장치와 메모리 사이 데이터를 누가 옮기나?       → CPU가 한 단어씩(PIO) / 장치가 직접(DMA)
```

- 이것이 없으면 CPU는 장치를 기다리느라 다른 일을 못 하거나, 데이터를 한 단어씩 옮기느라 시간을 다 쓴다.

쉬운 예: 택배를 기다리는 방법.
- 1분마다 현관문을 열어 본다 → 폴링. 빨리 알지만 다른 일을 못 한다.
- 초인종이 울리면 나간다 → 인터럽트. 다른 일을 하다가 불려 나간다. 나가는 데 시간이 조금 든다.
- 경비실이 대신 받아 내 보관함에 넣고 문자를 준다 → DMA + 완료 인터럽트. 나는 옮기지 않는다.

똑같은 구조다.\
NIC는 패킷을 메모리의 링 버퍼에 직접 쓰고(DMA), 다 썼다고 인터럽트를 건다. NVMe SSD도 읽은 블록을 메모리에 직접 쓰고 완료를 인터럽트로 알린다.

실무 예:
- 트래픽이 몰리자 한 코어만 100%다. `top`의 `si`(softirq)가 그 코어에만 높다.
- 앱 로그에는 아무 오류가 없는데 NIC 통계의 드롭 카운터가 오른다.
- 지연을 줄이려고 바쁜 대기(busy polling)를 켰더니 CPU 사용률이 바닥에서 100%로 바뀌었다.

## 동작·원리

### 1. 장치의 겉모습 — 레지스터 세 개

```text
  +---------------------------------------------------+
  |  상태(STATUS)   명령(COMMAND)   데이터(DATA)       |  ← 인터페이스: OS가 읽고 쓰는 곳
  +---------------------------------------------------+
  |  마이크로컨트롤러(작은 CPU) · 메모리 · 전용 칩      |  ← 내부: 펌웨어가 돈다
  +---------------------------------------------------+
            OSTEP 36 Figure 36.3 "A Canonical Device"를 옮겨 그림
```

- OS는 이 레지스터를 읽고 써서 장치를 부린다(OSTEP 36.3).
  - *장치 레지스터*: 장치가 바깥에 내놓은 작은 저장 칸. 상태를 읽고, 명령을 쓰고, 데이터를 주고받는다.
- 레지스터에 닿는 길은 두 가지다(OSTEP 36.6).
  - *포트 I/O*: x86의 `in`·`out`처럼 장치 전용 명령을 쓴다. 보통 특권 명령이라 커널만 쓴다.
  - *메모리 맵 I/O(MMIO)*: 장치 레지스터를 메모리 주소처럼 보이게 한다. 보통의 load·store가 메모리 대신 장치로 간다.
    - 흔한 오해: "MMIO 주소는 RAM의 한 칸이다." — 하드웨어가 그 주소의 load·store를 장치로 보낸다. RAM에 저장되는 값이 아니다(OSTEP 36.6).
- 장치는 버스 계층에 붙는다. OSTEP Figure 36.2(Intel Z270 칩셋 예)에서 그래픽은 CPU에 PCIe로 바로 붙고, 나머지는 DMI로 CPU와 이어진 I/O 칩 아래에 붙는다. 그 안에서도 NIC·NVMe 같은 고성능 장치는 PCIe로, 디스크는 eSATA로, 키보드·마우스는 USB로 붙는다(OSTEP 36.1).
- 계층을 두는 이유는 물리와 비용이다. 빠른 버스일수록 짧아야 하고 만들기 비싸다(OSTEP 36.1, Figure 36.1).

### 2. 폴링 — 계속 물어본다

```text
  while (STATUS == BUSY) ;        // ① 장치가 놀 때까지 묻는다 (폴링)
  DATA    ← 보낼 데이터            // ② CPU가 한 단어씩 옮긴다 (PIO)
  COMMAND ← 명령                   // ③ 시작
  while (STATUS == BUSY) ;        // ④ 끝날 때까지 또 묻는다 (폴링)
            OSTEP 36.3의 "canonical protocol"
```

- *폴링(polling)*: 상태 레지스터를 반복해서 읽어 장치 상태를 확인하는 것.
- *PIO(Programmed I/O)*: CPU가 직접 데이터를 장치로 옮기는 방식.
- 단순하고 잘 돈다. 대신 느린 장치를 기다리는 동안 CPU가 헛돈다.

### 3. 인터럽트 — 끝나면 불러 달라

```text
  폴링:       CPU  1 1 1 1 1 p p p p p 1 1 1 1     (p = 묻기만 하며 헛돈다)
              Disk           1 1 1 1 1
  인터럽트:   CPU  1 1 1 1 1 2 2 2 2 2 1 1 1 1     (그동안 프로세스 2를 돌린다)
              Disk           1 1 1 1 1  ↑ 끝나면 인터럽트 → 프로세스 1을 깨운다
            OSTEP 36.4의 타임라인
```

- *인터럽트(interrupt)*: 장치가 CPU에 보내는 "일이 생겼다" 신호. CPU는 하던 명령을 마치고 커널의 처리기로 들어간다.
- 핸들러 안의 흐름(상반부·하반부, softirq, IPI)은 [os/03-interrupts-traps-faults](../../os/03-interrupts-traps-faults/2-summary.md)에 있다. 여기서는 "언제 폴링이 낫나"만 본다.
- OSTEP 36.4의 정리
  - 인터럽트는 계산과 I/O를 겹치게 해 준다. 느린 장치에 맞다.
  - 장치가 아주 빠르면 첫 폴링에 이미 끝나 있다. 이때 인터럽트는 문맥 전환·처리기 비용 때문에 오히려 느리다.
  - 빠를 때도 느릴 때도 있으면 **잠깐 폴링하다가 안 끝나면 인터럽트로** 바꾸는 2단계(hybrid)가 좋을 수 있다.
  - 패킷마다 인터럽트가 오면 OS가 인터럽트 처리만 하다 사용자 프로그램을 못 돌리는 **livelock**에 빠질 수 있다(Mogul·Ramakrishnan 1996, OSTEP이 [MR96]으로 인용).
    - *livelock*: 시스템이 계속 바쁘게 일하지만 실제로 진척되는 일이 없는 상태.
  - *인터럽트 병합(coalescing)*: 장치가 인터럽트를 조금 늦춰, 그동안 끝난 여러 요청을 인터럽트 하나로 알린다. 처리 비용이 줄고 요청 하나의 지연은 는다.

#### 실험: 바쁜 대기 vs 잠들고 깨우기 (`PollVsPark.java`)

같은 일을 두 방식으로 기다리게 했다. 생산자가 약 1ms마다 "일이 왔다"를 `volatile` 칸에 적는다. 소비자는
- poll: `Thread.onSpinWait()`로 그 칸을 계속 읽는다(폴링).
- park: `LockSupport.park()`로 잠든다. 생산자가 `unpark`로 깨운다(인터럽트에 해당).

```java
if (mode.equals("poll")) {
    while ((s = seq) == seen) Thread.onSpinWait();      // 계속 확인
} else {
    while ((s = seq) == seen) LockSupport.park();        // 잠든다, 깨워 주면 확인
}
lat[got[0]++] = System.nanoTime() - postedAt;           // 적힌 뒤 알아채기까지
got[1] += s - seen - 1;                                 // 칸이 하나라 합쳐져 놓친 사건 수
```

환경: i7-13700HX, Linux 7.0.0, Docker `eclipse-temurin:21-jdk`(JDK 21.0.12) `--cpus=2`, 사건 2,000개 × 모드당 2회 × JVM 3회. 각 JVM의 첫 두 줄에는 JIT 워밍업이 섞일 수 있다.

```text
  poll  wake p50=   2.0 us  p99=   22.6 us  consumer CPU= 2181 ms / wall  2217 ms ( 98%)  missed=8
  park  wake p50=  87.1 us  p99=  179.7 us  consumer CPU=   73 ms / wall  2229 ms (  3%)  missed=0
  poll  wake p50=   1.9 us  p99=   12.6 us  consumer CPU= 2188 ms / wall  2207 ms ( 99%)  missed=0
  park  wake p50=  78.9 us  p99=  146.0 us  consumer CPU=   65 ms / wall  2221 ms (  3%)  missed=0
  (JVM 3회 범위) poll p50 1.9~2.1us · CPU 98~100% · missed 0~10
                 park p50 37.3~87.1us · p99 137.4~179.7us · CPU 2~3% · missed 0~2
```

- 관찰 1: 폴링은 알아채는 데 약 2µs, 잠들고 깨우기는 수십 µs다. 대신 폴링은 기다리는 내내 코어 하나(98~100%)를 쓴다. 잠든 쪽은 2~3%다.
- 관찰 2: 상태 칸이 **하나**뿐이면, 소비자가 늦을 때 두 사건이 하나로 합쳐져 사라진다(missed). `--cpus=2` 쿼터로 소비자가 잠시 멈추면 폴링 쪽에서도 생겼다.
  - 해석: 장치가 "완료" 한 칸 대신 **완료 항목의 링(큐)**을 두는 이유와 같다. 칸이 여러 개면 늦게 와도 하나씩 꺼내 볼 수 있다.
- 이 수치는 이 호스트·이 컨테이너 제한에서의 값이다. 커널의 실제 인터럽트 경로와 같은 비용은 아니고, "확인 방식이 지연과 CPU를 맞바꾼다"는 모양만 보인다.

### 4. DMA — 장치가 메모리에 직접 쓴다

```text
  PIO:   CPU  1 1 1 1 1 c c c 2 2 2 2 2 1 1      (c = CPU가 한 단어씩 복사)
         Disk               1 1 1 1 1
  DMA:   CPU  1 1 1 1 1 2 2 2 2 2 2 2 2 1 1      (복사도 CPU가 안 한다)
         DMA            c c c
         Disk                 1 1 1 1 1  → 끝나면 DMA가 인터럽트
            OSTEP 36.5의 타임라인
```

- *DMA(Direct Memory Access)*: 장치(또는 DMA 엔진)가 CPU를 거치지 않고 메모리와 데이터를 주고받는 것.
- OS는 "데이터가 메모리 어디에 있고, 얼마나, 어느 장치로"만 알려 준다. 끝나면 인터럽트로 알림을 받는다(OSTEP 36.5).
- 현대 장치는 한 번에 요청 하나가 아니라 **디스크립터 링**을 쓴다.

```text
          메모리의 디스크립터 링 (칸 = 버퍼 주소 + 길이 + 상태)
          ┌────┬────┬────┬────┬────┬────┬────┬────┐
          │ 완 │ 완 │ 빈 │ 빈 │ 빈 │ 빈 │ 빈 │ 완 │
          └────┴────┴────┴────┴────┴────┴────┴────┘
                     ↑ 장치가 다음에 채울 칸   ↑ 드라이버가 다음에 꺼낼 칸
   장치: 빈 칸의 주소로 DMA → 칸을 "완료"로 표시 → (필요하면) 인터럽트
   드라이버: 완료 칸을 꺼내 처리 → 새 빈 버퍼를 달아 장치에 돌려준다
   링이 꽉 차면(빈 칸 0) 장치는 새 데이터를 둘 곳이 없다 → NIC에서는 드롭
```

- *디스크립터*: "이 주소에 이 길이만큼"을 적은 작은 기록. 장치가 읽어 DMA 대상을 안다.
- 링 자체의 원리(빈/가득 판정, 넘침 정책)는 [data-structure/25-ring-buffer](../../data-structure/25-ring-buffer/2-summary.md), NIC RX/TX 링과 NAPI는 [network/25-kernel-network-stack](../../network/25-kernel-network-stack/2-summary.md)에 있다.
- Linux 블록 계층(blk-mq)도 같은 모양이다. CPU별 소프트웨어 큐 → 하드웨어 디스패치 큐로 보내고, 하드웨어 큐는 "장치의 제출 큐(또는 장치 DMA 링 버퍼)"에 대응한다. 하드웨어 큐 수는 코어 수를 넘지 않는다(kernel docs `block/blk-mq`).

#### 실험: NVMe 읽기 1회 = 완료 인터럽트 1회, 그리고 그 CPU로 온다 (`nvmeirq.sh`)

`taskset`으로 CPU 하나에 고정해 `O_DIRECT` 4KiB 랜덤 읽기를 2초 돌리고, `/proc/interrupts`에서 그 CPU 칸의 `nvme0q*` 합이 얼마나 늘었는지 셌다.

```bash
snap() { awk -v c=$col '/nvme0q/{s+=$c} END{print s}' /proc/interrupts; }
a=$(snap); taskset -c $cpu ./seqrand data.bin rand 4096 1 1 2; b=$(snap)
```

환경: Samsung NVMe(`MZVL2512HDJD`, PM9A1 계열 컨트롤러), ext4, 커널 7.0.0, gcc 13.3. 파일 512MiB(`/dev/urandom`), 끝나고 지웠다.

```text
  cpu=2   avg_lat=  82.6 us   nvme IRQ on cpu2:  +24167   reads≈24168
  cpu=2   avg_lat=  77.2 us   nvme IRQ on cpu2:  +25869   reads≈25868
  cpu=20  avg_lat= 100.9 us   nvme IRQ on cpu20: +19787   reads≈19778
  cpu=20  avg_lat=  94.2 us   nvme IRQ on cpu20: +21216   reads≈21212
```

- 관찰: 큐 깊이 1에서는 읽기 1번에 완료 인터럽트가 거의 정확히 1번 늘었다. 몇 개 차이는 같은 CPU의 다른 I/O로 보인다.
- 관찰: 인터럽트는 요청을 낸 CPU 칸에 쌓였다. 이 호스트의 NVMe는 큐 24개(`nvme0q1`~`q24`)를 두고, 각 큐의 IRQ 친화도가 CPU 하나로 고정돼 있다(`/proc/irq/138/smp_affinity_list` = `6` 등). 제출한 CPU의 큐로 완료가 돌아오는 구조다.
- 관찰: E코어(CPU20)에서 낸 읽기의 평균 지연이 P코어(CPU2)보다 약 17~18µs(같은 회차끼리) 길었다. 점검 재실행(1회)에서는 88.4µs 대 96.4µs로 약 8µs 차이였다. 크기는 실행마다 흔들리지만 방향은 같았다. 이 실험은 읽기 전체 지연만 쟀다. 장치 처리·큐 대기·제출/완료 처리 시간을 나누지 않았으므로 차이가 어느 구간에서 생겼는지는 특정할 수 없다. 코어 종류(하이브리드 CPU, [20번](../20-multicore-and-numa/2-summary.md))에 따른 제출·완료 처리 시간 차이는 가능한 설명(해석)이다.
- 이 호스트는 블록 폴링이 꺼져 있다(`/sys/block/nvme0n1/queue/io_poll` = 0). 그래서 완료를 인터럽트로만 받는다.

### 5. 인터럽트가 어느 코어로 가나 — 이 호스트의 실제 분포

`/proc/interrupts`는 IRQ마다 CPU별 누적 횟수를 보여 준다(kernel docs `filesystems/proc`). 두 번 떠서 차이를 보면 초당 분포가 된다(`irqdelta.py`, 5초 × 3회).

```text
     per_s   irq topCPU share%  name
      5065   136     16  100.0  ...0-edge eno1          ← 유선 NIC: 한 CPU에 100%
      2131   179     14  100.0  ...0-edge i915          ← 내장 GPU
        21   149     15  100.0  ...12-edge nvme0q12     ← NVMe 큐: 큐마다 CPU 하나
     28837   LOC     16   13.5  Local timer interrupts  ← 코어별 타이머, 고르게 퍼짐
  (3회 범위) eno1 4,209~5,342/s, 매번 CPU16이 100%
```

- 유선 NIC(`eno1`, 드라이버 r8169)는 큐가 하나다(`/sys/class/net/eno1/queues` = `rx-0 tx-0`). IRQ 벡터도 하나다.
- 허용 CPU는 전부다(`smp_affinity_list` = `0-23`). 그런데 실제 전달 CPU는 하나다(`effective_affinity_list` = `16`). `irqbalance`는 돌지 않는다(`systemctl is-active` → `inactive`).
- 그 결과(부팅 후 약 6일 누적)

```text
  IRQ 136 eno1      : CPU16 = 935,920,001   나머지 23개 CPU = 0
  NET_RX softirq    : CPU16 = 1,328,499,134  나머지 = 약 24만~260만
  softnet_stat cpu16: time_squeeze = 0x740e (29,710)   ← 처리 한도에 걸려 일을 남긴 횟수
  eno1 통계         : rx_dropped = 245,440   rx_missed_errors = 30,278
  링 크기           : RX 256 (드라이버 최대 256)
```

- 해석: 큐 하나짜리 NIC는 하드웨어 IRQ와 그 뒤의 첫 수신 처리(NAPI 폴링)가 한 코어에 몰린다. RPS를 켜면 그 위 프로토콜 처리는 다른 CPU로 나눌 수 있다(kernel docs `networking/scaling`). 이 호스트는 RPS도 꺼져 있다(`/sys/class/net/eno1/queues/rx-0/rps_cpus` = `000000`). 그 코어가 E코어(CPU16)라 처리 여력이 P코어보다 작다.
- 위 값은 부팅 뒤 **처리 횟수**다. 횟수가 한 코어에 몰렸다는 것까지 보여 줄 뿐, 그 코어의 `%soft`가 100%였다는 측정은 아니다. 포화 여부는 같은 구간의 CPU 시간 지표(`mpstat -P ALL 1`의 `%soft`)로 확인한다. ⚠ "인터럽트 폭주 → 한 코어 softirq 100%"는 이 몰림이 부하를 만나 커진 모습이다.
- `time_squeeze`의 뜻은 [network/25](../../network/25-kernel-network-stack/2-summary.md)(softirq 한 주기의 budget·시간 한도). `rx_missed_errors`는 "호스트가 놓친 패킷"이다. 장치의 버퍼 부족으로 버린 패킷은 `rx_dropped`가 아니라 여기에 센다(kernel docs `networking/statistics`). 실제로 어느 경우에 올리는지는 드라이버 구현을 따른다.

## 쓰이는 자료구조·알고리즘

- **디스크립터 링(원형 큐)** — NIC RX/TX 링, 블록 장치의 제출·완료 큐. 생산자(장치)와 소비자(드라이버)가 각자 위치만 움직인다. [data-structure/25-ring-buffer](../../data-structure/25-ring-buffer/2-summary.md)
- **CPU별 큐** — blk-mq의 소프트웨어 큐·하드웨어 큐, NIC 다중 큐(RSS). 한 큐에 락 하나를 모두가 잡던 구조를 CPU마다 나눠 경합을 없앤다(kernel docs `block/blk-mq`). 동시성 구조 일반은 [data-structure/29-concurrent-data-structures](../../data-structure/29-concurrent-data-structures/2-summary.md)
- **비트마스크** — `smp_affinity`는 "이 IRQ를 받아도 되는 CPU" 비트 집합이다. [data-structure/18-bitset](../../data-structure/18-bitset/2-summary.md)
- **묶음 처리(batching)** — 인터럽트 병합, NAPI의 budget 단위 폴링. 건당 고정 비용을 여러 건에 나눠 낸다.
- **흐름 해시** — RSS가 4-튜플 해시로 수신 큐를 고른다. [algorithm/12-hash-functions](../../algorithm/12-hash-functions/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 증상 → 하드웨어 원인 → 확인 명령

| 증상 | 의심 | 확인 |
|---|---|---|
| 한 코어만 100%, `si`·`%soft` 높음 | IRQ·softirq가 한 CPU로 몰림 | `/proc/interrupts` 두 번 차이, `/proc/softirqs`의 `NET_RX` 열, `mpstat -P ALL 1` |
| 앱 오류 없이 수신 누락 | DMA 링 가득 | `ethtool -S <if>`, `/sys/class/net/<if>/statistics/rx_missed_errors`, `ethtool -g <if>` |
| softirq 처리 밀림 | budget·시간 한도 | `/proc/net/softnet_stat` 3번째 열(`time_squeeze`) |
| 큐가 몇 개인가 | 단일 큐 장치 | `ls /sys/class/net/<if>/queues`, `ethtool -l <if>`(드라이버가 지원할 때) |
| IRQ가 어디로 가나 | 친화도 | `/proc/irq/<n>/smp_affinity_list`, `/proc/irq/<n>/effective_affinity_list` |

```bash
# 5초 동안 IRQ별 초당 횟수와 가장 많이 받은 CPU (실험의 irqdelta.py와 같은 일)
python3 irqdelta.py 5
# softirq 누적 — 한 열만 큰가
grep -E "NET_RX|NET_TX|BLOCK" /proc/softirqs
```

- 읽기는 누구나 된다. 친화도 변경(`echo ... > /proc/irq/<n>/smp_affinity`), 링 크기 변경(`ethtool -G`), 큐 수 변경(`ethtool -L`)은 root가 필요하다. 링 크기를 바꾸면 많은 드라이버가 인터페이스를 내렸다 올린다([network/25](../../network/25-kernel-network-stack/2-summary.md)).

### 2. 코드에서 "폴링 vs 잠들기"를 고를 때

- 기본은 잠들기다. `BlockingQueue.take()`, `CompletableFuture`, NIO 셀렉터([os/26](../../os/26-io-multiplexing-epoll/2-summary.md))는 모두 기다리는 동안 CPU를 내놓는다.
- 바쁜 대기는 "코어를 하나 통째로 내줄 수 있고, 수 µs 지연이 돈이 되는" 경우만 쓴다. 예: 전용 코어를 둔 저지연 메시징.
  - 컨테이너 CPU 쿼터 아래서 바쁜 대기를 하면 쿼터를 그 루프가 다 먹는다. 실험에서 소비자 하나가 1코어를 98~100% 썼다.
- 섞어 쓰는 방법(OSTEP의 2단계)을 라이브러리가 이미 해 둔 경우가 많다. 예: 잠깐 스핀하다가 futex로 잠드는 락 구현(원리는 [os/16](../../os/16-locks-and-spinlocks/2-summary.md)).
- 상태 칸 하나로 신호를 주고받으면 사건이 합쳐진다(실험의 `missed`). 사건 수가 중요하면 큐나 카운터를 쓴다.

## 장애 시나리오와 대처

### 1. 인터럽트 폭주 → 한 코어 softirq 100% (⚠)

- **현상**: 트래픽이 늘자 처리량이 더 오르지 않는다. 다른 코어는 한가하다.
- **보이는 형태**: `mpstat -P ALL`에서 한 CPU의 `%soft`·`%irq`만 높다. `/proc/interrupts`의 NIC 줄이 한 CPU 열에서만 오른다. `/proc/softirqs`의 `NET_RX`가 한 열만 크다. 이 호스트에서는 `eno1` IRQ 935,920,001회가 전부 CPU16, `NET_RX`도 CPU16만 13억대였다.
- **원인**: NIC가 단일 큐이거나, 다중 큐라도 IRQ 친화도가 한 CPU로 모였다. 큰 단일 흐름은 RSS로도 한 큐로 간다([network/25](../../network/25-kernel-network-stack/2-summary.md)).
- **대처**: 큐 수 확인(`ethtool -l`) → 다중 큐면 친화도 분산(`irqbalance` 또는 수동). 단일 큐 NIC면 RPS로 프로토콜 처리를 다른 CPU에 나눈다(kernel docs `networking/scaling`). 그 코어에 앱 스레드를 고정하지 않는다. 하이브리드 CPU면 수신 IRQ를 P코어로 옮기는 것도 검토한다.

### 2. DMA 링 가득 → 패킷 드롭 (⚠)

- **현상**: 순간 폭주 때 재전송·타임아웃이 늘지만, 앱·커널 로그에는 오류가 없다.
- **보이는 형태**: `ethtool -S`·`/sys/class/net/<if>/statistics`의 `rx_missed_errors`(버퍼 부족 드롭)가 증가. `rx_fifo_errors`(수신 FIFO 오류)·`rx_dropped`도 함께 본다. 단 `rx_dropped`에는 지원하지 않는 프로토콜·L2 주소 필터로 버린 패킷도 들어갈 수 있다(kernel docs `networking/statistics`). `softnet_stat`의 `time_squeeze` 증가. 이 호스트: `rx_missed_errors` 30,278, `time_squeeze` 29,710(CPU16).
- **원인**: 장치는 빈 디스크립터가 있어야 DMA를 한다. 소비 쪽(softirq)이 늦으면 링이 차고, 장치는 새 프레임을 둘 곳이 없다. 카운터만으로 "링이 찼고 원인은 softirq 지연"이 확정되지는 않는다. 같은 시간대의 `time_squeeze`·`%soft`·드라이버별 통계를 함께 보고 판단한다(해석).
- **대처**: 소비를 빠르게(IRQ 분산, 그 코어의 다른 일 치우기) → 링 크기 키우기(`ethtool -G`, 드라이버 최대까지 — 이 NIC는 최대가 256이라 여지가 없다) → 그래도 모자라면 다중 큐 NIC. 링을 키우면 순간 폭주는 흡수하지만 지연이 늘 수 있다.

### 3. 수신 livelock — 바쁜데 일이 안 끝난다

- **현상**: 초당 패킷 수가 어느 선을 넘자 처리량이 오히려 떨어지고, 사용자 프로세스가 거의 못 돈다.
- **보이는 형태**: CPU는 `%irq`·`%soft`로 꽉 찼고 `%usr`는 작다. 응답 지연이 급등한다.
- **원인**: 패킷마다 인터럽트를 처리하느라 상위 처리·앱에 CPU가 안 간다(OSTEP 36.4, [MR96]).
- **대처**: Linux의 대표적인 답이 NAPI다. 첫 인터럽트 뒤 인터럽트를 가리고 budget 단위로 폴링한다([network/25](../../network/25-kernel-network-stack/2-summary.md)). 인터럽트 병합 설정(`ethtool -c`/`-C`)을 확인한다. 앞단에서 속도 제한을 건다.

### 4. 바쁜 대기 설정 → CPU 쿼터 소진·이웃 지연

- **현상**: 지연을 줄이려고 스핀 대기·busy polling을 켰더니 컨테이너가 쓰로틀되고 p99가 더 나빠졌다.
- **보이는 형태**: 한가할 때도 CPU 사용률이 코어 수만큼 꽉 차 있다. `cpu.stat`의 `nr_throttled` 증가([os/08](../../os/08-cpu-scheduling/2-summary.md)). 실험: 폴링 소비자 하나가 98~100% CPU, 잠드는 소비자는 2~3%.
- **원인**: 폴링은 지연과 CPU를 맞바꾼다. 쿼터·공유 코어 환경에서는 그 CPU가 다른 일의 몫이다.
- **대처**: 기본은 잠들기. 스핀은 짧게 하고 잠들기로 넘어가는 2단계로. 진짜로 필요하면 전용 코어를 따로 둔다.

### 5. 인터럽트 병합을 과하게 → 저부하에서 지연 증가

- **현상**: 처리량 튜닝 뒤 한가할 때 요청 하나의 응답이 느려졌다.
- **보이는 형태**: 부하가 낮을 때 p50이 오히려 높다. NIC 인터럽트 횟수는 크게 줄었다.
- **원인**: 병합은 인터럽트를 "조금 기다렸다가" 보낸다. 기다리는 시간이 그대로 지연에 더해진다(OSTEP 36.4).
- **대처**: `ethtool -c`로 현재 값(`rx-usecs` 등)을 보고, 지원되면 적응형(adaptive) 병합을 쓴다. 지연 목표와 CPU 목표를 같이 재며 바꾼다.

## 핵심 문장

- 장치가 끝났는지 아는 법은 폴링과 인터럽트다. 폴링은 빨리 알지만 CPU를 쓰고, 인터럽트는 CPU를 아끼지만 깨우는 비용이 든다.
- 빠른 장치에는 폴링, 느린 장치에는 인터럽트, 섞여 있으면 잠깐 폴링 후 인터럽트(2단계)가 낫다(OSTEP 36.4).
- DMA는 데이터 옮기기를 CPU에서 빼낸다. 현대 장치는 디스크립터 링에 DMA한다. 완료는 인터럽트로 알리거나, 드라이버가 폴링(NAPI·블록 폴링)으로 발견한다.
- 링이 차면 장치는 둘 곳이 없다. NIC에서는 앱 로그에 안 남는 조용한 드롭이 된다.
- 인터럽트는 특정 CPU로 간다. 단일 큐 장치나 몰린 친화도는 부하가 크면 한 코어 softirq 100%를 만들 수 있다.

## 관련 주제·근거

- 선행
  - architecture [11-memory-hierarchy-and-locality](../11-memory-hierarchy-and-locality/2-summary.md) — 장치는 메모리 계층의 가장 느린 끝
- 후속·연결
  - architecture [16-storage-media-workload](../16-storage-media-workload/2-summary.md) — 디스크·SSD의 접근 시간과 큐 깊이
  - architecture [20-multicore-and-numa](../20-multicore-and-numa/2-summary.md) — P/E 코어, IRQ를 받는 코어의 차이
  - os [03-interrupts-traps-faults](../../os/03-interrupts-traps-faults/2-summary.md) — 인터럽트 처리기, 상반부·하반부, IPI
  - os [25-io-models](../../os/25-io-models/2-summary.md) · [26-io-multiplexing-epoll](../../os/26-io-multiplexing-epoll/2-summary.md) — 앱이 I/O를 기다리는 방법
  - os [34-zero-copy-and-io-uring](../../os/34-zero-copy-and-io-uring/2-summary.md) — DMA gather, 공유 링(io_uring)
  - os [08-cpu-scheduling](../../os/08-cpu-scheduling/2-summary.md) · [16-locks-and-spinlocks](../../os/16-locks-and-spinlocks/2-summary.md) — CPU 쿼터, 스핀 후 잠들기
  - network [25-kernel-network-stack](../../network/25-kernel-network-stack/2-summary.md) — RX 링·NAPI·RSS·드롭 카운터 지도
  - data-structure [25-ring-buffer](../../data-structure/25-ring-buffer/2-summary.md) · [18-bitset](../../data-structure/18-bitset/2-summary.md) · [29-concurrent-data-structures](../../data-structure/29-concurrent-data-structures/2-summary.md)
- 교재·논문
  - OSTEP 36 "I/O Devices" — 36.1 System Architecture(Figure 36.2), 36.2–36.3 Canonical Device·Protocol(PIO·폴링), 36.4 인터럽트(hybrid, livelock, coalescing), 36.5 DMA, 36.6 I/O 명령 vs MMIO <https://pages.cs.wisc.edu/~remzi/OSTEP/file-devices.pdf>
  - Mogul, Ramakrishnan "Eliminating Receive Livelock in an Interrupt-driven Kernel" (USENIX 1996) — OSTEP 36 참고문헌 [MR96]
- Linux 문서
  - `filesystems/proc` — `/proc/interrupts`, `/proc/irq/<n>/smp_affinity` <https://docs.kernel.org/filesystems/proc.html>
  - `core-api/irq/irq-affinity` — `smp_affinity`·`smp_affinity_list` <https://docs.kernel.org/core-api/irq/irq-affinity.html>
  - `block/blk-mq` — 소프트웨어 큐·하드웨어 디스패치 큐, 하드웨어 큐 수 ≤ 코어 수 <https://docs.kernel.org/block/blk-mq.html>
  - `networking/napi`, `networking/scaling` — NAPI, RSS·RPS <https://docs.kernel.org/networking/napi.html> · <https://docs.kernel.org/networking/scaling.html>
- 실험 목록(모두 i7-13700HX 24 논리 CPU(P코어 8×2 + E코어 8), Linux 7.0.0-34, 2026-10-07)
  - `PollVsPark.java` — 바쁜 대기 vs park/unpark의 깨어남 지연·CPU 시간·합쳐진 사건 수. Docker `eclipse-temurin:21-jdk`(21.0.12) `--cpus=2 --network none`, JVM 3회
  - `nvmeirq.sh` + `seqrand.c`(gcc 13.3 `-O2`) — CPU 고정 `O_DIRECT` 4KiB 읽기 수와 그 CPU의 NVMe IRQ 증가 비교, P코어(CPU2)·E코어(CPU20) 각 2회
  - `irqdelta.py`(Python 3 표준 라이브러리) — `/proc/interrupts` 5초 차이 3회. 함께 읽은 것: `/proc/softirqs`, `/proc/net/softnet_stat`, `/proc/irq/*/{smp,effective}_affinity_list`, `/sys/class/net/eno1/{queues,statistics}`, `ethtool -i/-g/-c eno1`, `/sys/block/nvme0n1/queue/io_poll`
