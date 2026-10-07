# architecture/16-storage-media-workload — 디스크는 "어디를 읽느냐"로 느려진다: HDD 탐색·회전, SSD 병렬성, IOPS 유도 — 정리 (힌트)

## 해결하는 문제

같은 4KiB를 읽어도 **어디를, 어떤 순서로** 읽느냐에 따라 걸리는 시간이 수백 배 달라진다. 이것을 모르면 저장 매체를 용량으로 고르고, 운영에서 지연 폭증을 만난다.

- 기초 설명(HDD 구조, SSD 접근 특성, 최신 매체 동향, 데이터 종류별 선택 기준, 데이터시트 수치)은 원고 [systems/storage-media-workload](../../systems/storage-media-workload/2-summary.md) §1~§5에 있다. 이 노트는 그 위에 **식으로 IOPS를 유도하는 법, 실제로 재 본 SSD 수치, 큐 깊이, 엘리베이터 스케줄링, 장애**를 더한다.

쉬운 예: 도서관에서 책 100권을 가져온다.
- 같은 서가에 꽂힌 100권 → 한 번 걸어가서 쭉 뽑는다(순차).
- 100개 층·서가에 흩어진 100권 → 책마다 걸어가야 한다(랜덤). 걷는 시간이 전부다.
- 사서가 20명이고 각자 다른 서가로 동시에 간다면(SSD의 병렬 die), 흩어져 있어도 빨리 모인다. 단 한 번에 한 권씩만 부탁하면 사서 19명은 논다(큐 깊이 1).

똑같은 구조다.\
HDD는 암에 붙은 헤드가 걸어 다닌다(헤드는 기록면마다 하나씩이고, 한 암에 붙어 함께 움직인다 — OSTEP 37.2). SSD는 걷지 않지만, 동시에 여러 요청을 줘야 병렬성이 나온다.

실무 예:
- HDD에 올린 DB가 평소엔 괜찮다가 랜덤 조회가 조금 늘자 응답이 수십 배 느려진다.
- SSD로 바꿨는데 배치가 생각만큼 안 빨라진다. 스레드 하나가 한 번에 한 블록씩 읽고 있었다.
- 벤치마크에선 디스크가 아주 빨랐는데, 운영에선 느리다. 벤치마크 파일이 페이지 캐시에 있었다.

## 동작·원리

### 1. HDD 접근 시간 = 탐색 + 회전 + 전송

```text
            ┌──────── 플래터(회전) ────────┐
            │   ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○      │  ← 동심원 트랙, 트랙 위 섹터
            │       ↑                      │
   암 ──────┼───── 헤드: ① 트랙으로 이동(탐색)
            │       ② 원하는 섹터가 밑에 올 때까지 대기(회전 지연)
            │       ③ 지나가는 섹터를 읽음(전송)
            └──────────────────────────────┘

   T_I/O = T_seek + T_rotation + T_transfer        (OSTEP 37.4, 식 37.1)
```

- *탐색(seek)*: 헤드를 원하는 트랙으로 옮기는 시간. 가속·등속·감속·**정착(settling)**으로 나뉜다. 정착만 0.5~2ms가 될 수 있다(OSTEP 37.3).
- *회전 지연(rotational delay)*: 섹터가 헤드 밑으로 올 때까지 기다리는 시간. 평균은 반 바퀴다.
- 평균 탐색 거리는 전체 거리의 약 1/3이다(OSTEP 37.4의 Aside "Computing the Average Seek"). 책·논문이 흔히 "평균 탐색 시간 ≈ 최대 탐색 시간의 1/3"로 인용하는 값이 여기서 나온다. 단 OSTEP은 이것이 시간이 아니라 **거리**의 계산이라고 밝힌다. 탐색 시간은 정착 같은 고정비 때문에 거리에 비례하지 않는다.

### 2. IOPS를 손으로 유도한다

7,200rpm HDD, 랜덤 4KiB 읽기, 큐 깊이 1:

```text
  회전 한 바퀴 = 60,000 ms / 7,200 = 8.33 ms → 평균 반 바퀴 = 4.17 ms
  평균 탐색    = 8.0 ms                          (원고의 WD He10 데이터시트 값)
  전송         = 4 KiB / 250 MB/s ≈ 0.016 ms     (1%도 안 된다)
  ─────────────────────────────────────────────
  T_I/O ≈ 12.2 ms   →   IOPS ≈ 1 / 12.2 ms ≈ 82회/초
  처리량 ≈ 82 × 4 KiB ≈ 0.33 MB/s       ← 순차 대역폭(180~300MB/s)의 약 1/550~1/900
```

- OSTEP 37.4도 같은 계산을 한다. Cheetah 15K.5(평균 탐색 4ms·15,000rpm)는 랜덤 0.66MB/s 대 순차 125MB/s, Barracuda(9ms·7,200rpm)는 0.31MB/s 대 105MB/s다. 격차가 약 200배, 300배 넘게 난다(Figure 37.6).
- 회전 지연을 절반(15,000rpm)으로 줄여도 탐색이 남아 자릿수는 그대로(ms 단위)다.
- 데이터시트의 랜덤 IOPS(168~212)가 82보다 큰 이유의 하나는 큐 깊이 16~32에서 쟀기 때문으로 본다(해석). 큐가 깊으면 드라이브가 회전 위치를 보고 순서를 바꾼다(NCQ, 아래 4절). 단 82는 WD He10의 탐색 시간으로 셈한 값이고, 168은 Seagate Exos X24(QD16)·212는 WD HC580(QD32)의 값이다. 드라이브가 달라서 차이를 큐 깊이 하나로 돌릴 수는 없다. 확정하려면 같은 드라이브를 QD별로 재야 한다. 원고 §1·수치 출처.

### 3. SSD — 위치 대신 병렬성

```text
  호스트 ── NVMe 큐 여러 개 ──> 컨트롤러 ──┬── 채널 0: die die die die
                                          ├── 채널 1: die die die die
                                          └── ...
  작은 요청 하나는 die 하나(매핑에 따라 여럿)가 처리 (수십 µs).  요청 32개를 동시에 주면 die 여럿이 같이 일할 수 있다.
```

- 탐색·회전이 없다. 그래서 랜덤 읽기와 순차 읽기의 차이가 HDD보다 훨씬 작다.
- 대신 요청을 **동시에 여러 개** 줘야 내부 병렬성이 쓰인다. 큐 깊이가 IOPS를 정한다.
  - *큐 깊이(QD, queue depth)*: 장치에 동시에 걸려 있는 요청 수.
  - Little 법칙으로 이어진다: **IOPS ≈ 큐 깊이 / 평균 지연**([math/10](../../math/10-queueing-and-littles-law/2-summary.md)).
- 쓰기 쪽 비용(덮어쓰기 불가, GC, 쓰기 증폭)은 [systems/nand-flash](../../systems/nand-flash/2-summary.md)가 정본이다(커리큘럼 17번 자리).

#### 실험: 이 노트북 NVMe의 순차·랜덤·큐 깊이 (`seqrand.c`)

`O_DIRECT`로 페이지 캐시를 우회하고 `pread`를 반복한다. 큐 깊이는 스레드 수로 만든다(스레드마다 동기 읽기 1개).

```c
int fd = open(path, O_RDONLY | (direct ? O_DIRECT : 0));
...
if (rnd) { x ^= x << 13; x ^= x >> 7; x ^= x << 17; blk = x % nblk; }   // 랜덤 블록
else     { blk = pos++; }                                              // 다음 블록
ssize_t n = pread(fd, buf, bs, blk * bs);
```

환경: i7-13700HX, Linux 7.0.0-34, ext4, Samsung NVMe `MZVL2512HDJD`(PM9A1 계열 컨트롤러, PCIe), gcc 13.3 `-O2`, 512MiB 파일, 측정 2초 × 3회. 호스트에 다른 부하가 있었다(load average 약 9).

```text
                            IOPS               MB/s          평균 지연
  seq  4KiB  QD1      13,548~14,488      55.5~59.3      68.9~73.7 µs
  rand 4KiB  QD1       6,950~9,780       28.5~40.1     102.1~143.7 µs
  seq  128KiB QD1      3,660~4,237       479.8~555.4    235.8~272.9 µs
  rand 4KiB  QD4      42,618~43,714     174.6~179.1      91.3~93.6 µs
  rand 4KiB  QD16    145,626~159,262    596.5~652.3     100.2~109.6 µs
  rand 4KiB  QD32    213,818~223,337    875.8~914.8     143.0~149.3 µs
  (점검 재실행 1회, 같은 코드) seq QD1 15,658 · rand QD1 11,221(89.0 µs) · rand QD32 237,138(134.7 µs)
```

- 관찰 1: QD1에서 랜덤은 순차보다 약 1.4~2.1배 느렸다. HDD의 수백 배와 자릿수가 다르다.
  - 해석: 순차 4KiB가 더 빠른 것은 컨트롤러 안의 미리 읽기 같은 내부 최적화로 보인다. 장치 내부라 직접 확인하지 못했다 `[?]`.
- 관찰 2: 큐 깊이를 1 → 32로 늘리자 랜덤 IOPS가 약 23~31배 늘었다(점검 재실행은 QD1이 더 빨라 약 21배). 지연은 같은 회차 QD1 대비 약 1.0~1.4배만 늘었다.
- 검산(Little): QD32에서 220,844 × 144.6µs ≈ 31.9, QD16에서 146,893 × 108.7µs ≈ 16.0. 큐 깊이와 맞는다.
- 같은 SSD라도 **요청을 하나씩 기다리며 보내면** 이 장치 능력의 수 %만 쓴다(QD1 약 1만 vs QD32 약 22만).

### 4. 순서를 바꿔 이동을 줄인다 — 엘리베이터 스케줄링

```text
  요청 트랙:  98 183 37 122 14 124 65 67, 헤드 53       (예시)
  FCFS:  53→98→183→37→122→14→124→65→67    왔다 갔다
  SSTF:  53→65→67→37→14→98→122→124→183    가장 가까운 것부터 (먼 요청 굶을 수 있음)
  SCAN:  53→65→67→98→122→124→183 → 37→14  한 방향으로 쭉, 마지막 요청에서 돌아옴 (엘리베이터의 LOOK 변형)
```

- *SSTF(Shortest Seek Time First)*: 지금 헤드에서 가장 가까운 요청부터. 이동은 짧지만, 가까운 요청이 계속 오면 먼 요청이 굶는다(starvation, OSTEP 37.5).
- *SCAN(엘리베이터)*: 한 방향으로 쓸고 가며 요청을 처리하고, 끝에서 방향을 바꾼다. 먼 요청도 헤드가 그 트랙을 지나는 sweep에서 처리되므로 SSTF처럼 무한정 밀리지는 않는다. 단 sweep 도중 앞쪽에 새 요청이 계속 끼어들면 그만큼 sweep이 길어져 대기 시간에 고정 상한은 없다. F-SCAN은 sweep 동안 큐를 얼려 이것을 막는다(OSTEP 37.5). C-SCAN은 한 방향으로만 쓸고 처음으로 돌아간다(가운데 트랙 편애를 줄임).
- *SPTF(Shortest Positioning Time First)*: 탐색 + 회전을 함께 본다. 헤드 위치·트랙 배치를 아는 드라이브 내부가 잘한다. 그래서 요즘은 OS가 몇 개(예: 16)를 골라 한꺼번에 내리고 드라이브가 SPTF로 처리한다(OSTEP 37.5 "Other Scheduling Issues").
- OS 쪽 스케줄러는 인접 요청을 **합치는(merge)** 일도 한다. 33, 8, 34번 블록 요청이면 33·34를 하나로 묶는다(OSTEP 37.5).
- Linux blk-mq에서는 스케줄러를 고를 수 있다. 이 호스트의 NVMe는 `none`이다(`/sys/block/nvme0n1/queue/scheduler` → `[none] mq-deadline`). `none`은 재정렬 없이 넣는다(kernel docs `block/blk-mq`). 위치 비용이 없는 장치라 재정렬의 이득이 작기 때문으로 본다(해석 — 같은 문서의 배경 절이 SSD에는 랜덤 접근 페널티가 없다고 적는다).

#### 실험: 같은 요청 200개를 세 순서로 (`Elevator.java`)

트랙 0~9,999에 균등 랜덤 요청 200개, 헤드는 5,000에서 시작. 총 이동 거리(트랙 수)를 비교했다. SCAN은 디스크 끝 대신 가장 큰 요청까지만 갔다 돌아오는 LOOK 변형으로 셌다. JDK 21(`eclipse-temurin:21-jdk`, `--cpus=2`).

```text
  seed=1  FCFS=  702,498  SSTF= 14,738  SCAN= 14,803  (평균 1회 이동: FCFS 3,512 / SCAN 74 트랙)
  seed=2  FCFS=  714,641  SSTF= 14,857  SCAN= 14,792  (평균 1회 이동: FCFS 3,573 / SCAN 73 트랙)
  seed=3  FCFS=  601,826  SSTF= 14,858  SCAN= 14,884  (평균 1회 이동: FCFS 3,009 / SCAN 74 트랙)
```

- 관찰: 순서만 바꿔도 총 이동이 약 40~48배 줄었다. FCFS 1회 평균 이동(3,009~3,573)은 전체 폭 10,000의 약 1/3로, OSTEP의 "평균 탐색 거리 ≈ 1/3"과 맞는다.
- 한계: 이 모형은 거리만 센다. 실제 탐색 시간은 거리에 비례하지 않는다(짧은 이동은 정착 시간이 지배). 회전 지연도 빠졌다. 그래서 시간 이득은 거리 이득보다 작다. 그리고 재정렬은 요청이 **큐에 여러 개 쌓여 있을 때만** 할 수 있다.

### 5. 페이지 캐시와 미리 읽기 — 디스크에 안 가는 읽기

```text
  read() ──> 페이지 캐시에 있나? ── 있음 ──> 메모리 복사 (µs 이하~수 µs)
                    │
                    └ 없음 ──> 디스크 I/O (SSD 수십~수백 µs, HDD 수 ms)
                               순차로 읽히면 커널이 앞을 미리 읽어 둔다(readahead)
```

- 페이지 캐시 구조와 `free`의 buff/cache 해석은 [os/14-mmap-and-page-cache](../../os/14-mmap-and-page-cache/2-summary.md)에 있다.

#### 실험: 같은 파일을 차가운/따뜻한 캐시로 (`seqrand.c` 버퍼드 모드, `dropcache.c`, `incore.c`)

`posix_fadvise(POSIX_FADV_DONTNEED)`로 이 파일의 캐시만 비우고(root 불필요), `mincore`로 상주 비율을 쟀다. 4KiB, QD1, 3회.

```text
  캐시 비움 → rand 버퍼드 2초     11,023~11,212 IOPS   89.1~90.6 µs    → 상주 15.7~16.0%
  캐시 비움 → seq 버퍼드 한 바퀴  939.4~999.8 MB/s      4.0~4.3 µs      → 상주 100%
  (전부 캐시에 있음) rand 버퍼드  411,870~452,562 IOPS  2.1~2.3 µs
  (참고) seq O_DIRECT 4KiB        55.5~59.3 MB/s        68.9~73.7 µs
  read_ahead_kb = 128
```

- 관찰 1: 같은 4KiB 순차 읽기가 `O_DIRECT`로는 약 57MB/s, 버퍼드(차가운 캐시)로는 약 940~1,000MB/s였다. 미리 읽기가 작은 순차 읽기를 큰 읽기로 바꾼 것과 부합한다(해석 — 장치에 간 실제 요청 크기는 재지 않았다. 확인하려면 `iostat`의 `rareq-sz`를 보거나 `POSIX_FADV_RANDOM`으로 미리 읽기를 끄고 비교한다).
- 관찰 2: 랜덤 버퍼드 읽기 약 2.2만 번 뒤 상주 페이지는 약 2.1만 개였다. 랜덤에는 미리 읽기가 거의 붙지 않았다(무작위 중복을 빼면 읽은 만큼만 들어왔다).
- 관찰 3: 캐시에 다 있으면 랜덤도 약 2µs다. 디스크 벤치마크가 캐시를 재면 장치보다 수십 배 빠른 값이 나온다.

## 쓰이는 자료구조·알고리즘

- **엘리베이터(SCAN·C-SCAN)·SSTF·SPTF** — 대기 요청을 정렬해 헤드 이동을 줄인다. 정렬된 대기열은 [data-structure/16-red-black-tree](../../data-structure/16-red-black-tree/2-summary.md) 같은 정렬 구조로 둔다(Linux mq-deadline은 요청을 섹터 순 레드블랙 트리에 둔다 — 커널 소스 `block/mq-deadline.c`의 `struct rb_root sort_list[DD_DIR_COUNT]`, `block/elevator.c`의 `elv_rb_add`가 `blk_rq_pos`(시작 섹터)로 비교). SSTF의 "가장 가까운 것"은 정렬 구조에서 앞뒤 이웃을 보는 일이다.
- **요청 병합** — 인접 구간 합치기. [algorithm/30-sweeping](../../algorithm/30-sweeping/2-summary.md)의 구간 병합과 같은 모양이다.
- **큐와 Little 법칙** — IOPS = 큐 깊이 / 지연, 이용률이 1에 가까우면 대기 폭증. [math/10-queueing-and-littles-law](../../math/10-queueing-and-littles-law/2-summary.md)
- **외부 정렬·k-way 병합** — 랜덤 쓰기를 정렬해 순차로 바꾼다. [algorithm/11-external-sort-and-k-way-merge](../../algorithm/11-external-sort-and-k-way-merge/2-summary.md)
- **로그 구조(append-only)·LSM** — 쓰기를 순차로 바꾸는 저장 구조. [data-structure/24-lsm-tree](../../data-structure/24-lsm-tree/2-summary.md)
- **B-트리** — 한 노드 = 한 페이지로 랜덤 접근 횟수를 트리 높이로 줄인다. [data-structure/15-b-tree](../../data-structure/15-b-tree/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 증상 → 매체 원인 → 확인

| 증상 | 의심 | 확인 |
|---|---|---|
| 디스크 대기로 느림 | 이용률 포화 | `iostat -x 1`의 `r/s`·`w/s`(IOPS), `r_await`(평균 지연), `aqu-sz`(평균 큐 길이) |
| HDD인지 SSD인지 | 매체 | `lsblk -d -o NAME,ROTA,MODEL`(`ROTA=1`이면 회전 매체), `/sys/block/<dev>/queue/rotational` |
| 순차인데 느림 | 미리 읽기·요청 크기 | `/sys/block/<dev>/queue/read_ahead_kb`, `iostat`의 `rareq-sz` |
| SSD인데 IOPS가 안 나옴 | 큐 깊이 1 | `aqu-sz`가 1 근처인가, 앱이 동기 읽기 하나씩 기다리나 |
| 벤치마크와 운영 차이 | 페이지 캐시 | `free -h`, 측정 전 캐시 상태, `O_DIRECT` 여부 |

- `%util`은 NVMe·RAID처럼 병렬로 처리하는 장치에서 포화를 뜻하지 않을 수 있다([os/31](../../os/31-os-observability-tools/2-summary.md) 장애 3).
- Little로 검산한다: 읽기만 있는 구간이면 `r/s × r_await(초)` ≈ `aqu-sz`. `aqu-sz`는 장치의 요청 전체를 세므로, 쓰기·discard·flush가 섞이면 종류별 `처리율 × 평균 지연`(`w/s × w_await` 등)을 더해 비교한다. 그래도 크게 어긋나면 측정 구간이 정상 상태였는지 의심한다.

### 2. 용량을 정할 때 식으로 어림한다

```text
  필요 IOPS = 초당 요청 × 요청당 랜덤 읽기 수 (캐시 미스분만)
  HDD 한 대 QD1 ≈ 80 IOPS(7,200rpm), 데이터시트 QD16~32 ≈ 170~210
  이용률 ρ = 필요 IOPS / 장치 IOPS   → ρ가 0.7을 넘으면 대기가 빠르게 는다(M/M/1: 대기 ∝ ρ/(1-ρ))
```

- 예시: 초당 100요청 × 미스 3회 = 300 IOPS. 7,200rpm HDD 한 대(데이터시트 170~210)로는 넘친다. 2대로 나눠도 이용률이 약 0.7~0.9라 대기가 크다. SSD 한 대는 큐만 깊게 주면 여유다.

### 3. 코드에서 매체에 맞추기 (Java 21)

```java
// 랜덤 키 조회 N건: 하나씩 기다리면 QD1. 동시에 내면 SSD 병렬성을 쓴다.
try (var exec = Executors.newVirtualThreadPerTaskExecutor()) {
    List<Future<byte[]>> fs = keys.stream()
        .map(k -> exec.submit(() -> readBlock(channel, offsetOf(k))))   // FileChannel.read(buf, pos)
        .toList();
    for (var f : fs) consume(f.get());
}
```

- 동시 요청 수에 상한을 둔다(세마포어 등). 무한정 내면 장치 큐보다 앞에서 쌓여 지연만 는다.
- HDD에서는 동시성보다 **순서**가 중요하다. 키를 정렬해 오프셋 순으로 읽으면 엘리베이터와 같은 효과를 앱에서 낸다.
- 쓰기는 모아서 순차로(로그·배치 정렬). 내구성(`fsync`) 비용은 [os/24](../../os/24-fsync-and-durability/2-summary.md).

## 장애 시나리오와 대처

### 1. 랜덤 I/O 워크로드를 HDD에 → IOPS 한계로 지연 폭증 (⚠)

- **현상**: 평소 수십 ms이던 조회가 트래픽이 조금 늘자 수백 ms~초 단위로 튄다. CPU는 한가하다.
- **보이는 형태**: `iostat -x`에서 `r/s`가 디스크 한계(수백) 근처에 붙고 `r_await`가 수십~수백 ms, `aqu-sz`가 커진다. 프로세스가 `D` 상태로 쌓인다. load average가 CPU 사용률에 비해 높다([os/31](../../os/31-os-observability-tools/2-summary.md)).
- **원인**: 랜덤 4KiB 1회 ≈ 12ms라 HDD 한 대는 QD1 약 80, 큐가 깊어도 수백 IOPS가 상한이다. 이용률이 1에 다가가면 대기가 비선형으로 는다. 계산 예(M/M/1 가정, 모형): 서비스 12ms·ρ=0.875면 평균 대기 ≈ ρ/(1-ρ) × 12ms ≈ 84ms.
- **대처**: 핫 데이터를 SSD로(원고 §5의 계층 분리), 캐시로 미스 줄이기, 접근을 순차화(정렬·배치), 디스크 수를 늘려 나누기([os/32-raid](../../os/32-raid/2-summary.md)의 striping).

### 2. SSD로 바꿨는데 안 빨라짐 — 큐 깊이 1

- **현상**: NVMe로 옮겼는데 배치 시간이 몇 배밖에 안 줄었다.
- **보이는 형태**: `iostat`의 `aqu-sz` ≈ 1, `r_await`는 약 0.1ms인데 `r/s`가 1만 근처. 실험: QD1 랜덤 6,950~9,780 IOPS, QD32는 213,818~223,337.
- **원인**: 앱이 읽기 하나를 끝내야 다음을 낸다. SSD 내부 병렬성이 놀고 있다.
- **대처**: 동시 요청(스레드·가상 스레드·비동기 I/O·io_uring)을 상한과 함께 늘린다. 큰 블록 순차 읽기로 바꿀 수 있으면 그것이 먼저다.

### 3. 벤치마크는 빨랐는데 운영은 느림 — 페이지 캐시 착시

- **현상**: 테스트에서 디스크 랜덤 읽기가 µs 단위였는데, 운영 데이터가 커지자 수십~수백 배 느리다.
- **보이는 형태**: 테스트 파일이 RAM보다 작았다. 실험: 같은 랜덤 4KiB가 캐시에 있으면 2.1~2.3µs, 캐시를 비우면 89~91µs.
- **원인**: 테스트가 장치가 아니라 페이지 캐시를 쟀다. 운영에서는 hot set이 RAM을 넘어 미스마다 장치 지연이 드러난다.
- **대처**: `O_DIRECT`나 캐시 비우기(`posix_fadvise` DONTNEED, 시스템 전체는 root의 `drop_caches`) 후 측정하고, 데이터 크기를 운영과 맞춘다. 운영 hot set 크기 대비 RAM을 본다.

### 4. 순차 스트림이 여럿 섞여 랜덤이 된다 (HDD)

- **현상**: 파일 하나를 읽을 땐 200MB/s 나오던 HDD가 10개를 동시에 읽자 합쳐서 수십 MB/s로 떨어진다.
- **보이는 형태**: `rareq-sz`가 작아지고 `r_await`가 커진다.
- **원인**: 각자는 순차지만 헤드가 스트림 사이를 오가므로 장치 입장에선 랜덤이다.
- **대처**: 동시 스트림 수 제한, 요청 크기·미리 읽기 키우기(`read_ahead_kb`, root), 스트림을 다른 디스크로 나누기.

### 5. SSTF식 재정렬 → 먼 요청 굶김

- **현상**: 평균 지연은 좋은데 일부 요청만 아주 오래 기다린다(p99.9 튐).
- **보이는 형태**: 특정 영역(디스크 바깥쪽 트랙의 파일 등)을 읽는 요청만 타임아웃.
- **원인**: 가장 가까운 요청 우선은 먼 요청을 계속 뒤로 미룬다(OSTEP 37.5).
- **대처**: SCAN 계열이나 마감 시간을 두는 스케줄러(Linux `mq-deadline`)를 쓴다. 앱 수준 재정렬에도 대기 상한을 둔다.

## 핵심 문장

- HDD 랜덤 읽기 1회는 탐색 + 회전 ≈ 12ms(7,200rpm)라 QD1 약 80 IOPS다. 전송 시간은 1%도 안 된다.
- HDD의 순차 대 랜덤 격차는 수백 배(OSTEP 37.4: 약 200배·300배 넘게), 이 NVMe에서 잰 QD1 격차는 약 1.4~2.1배였다.
- SSD는 위치 대신 병렬성이다. IOPS ≈ 큐 깊이 / 지연이고, 이 NVMe는 QD1 약 1만에서 QD32 약 22만으로 늘었다.
- 요청이 쌓여 있으면 순서를 바꿔(엘리베이터) 이동을 줄인다. 같은 요청 200개의 총 이동이 FCFS 대비 약 1/40~1/48로 줄었다.
- 페이지 캐시와 미리 읽기가 장치를 가린다. 캐시를 재면 장치보다 수십 배 빠른 값이 나온다.

## 관련 주제·근거

- 원고
  - [systems/storage-media-workload](../../systems/storage-media-workload/2-summary.md) — HDD·SSD 구조, 최신 매체(SMR·HAMR·QLC·NVMe), 데이터 종류별 선택, 데이터시트 수치 출처
- 선행
  - architecture [15-io-devices-interrupts-dma](../15-io-devices-interrupts-dma/2-summary.md) — 완료 인터럽트, 블록 장치 큐
- 후속·연결
  - [systems/nand-flash](../../systems/nand-flash/2-summary.md) — 커리큘럼 17 nand-flash-ftl 자리: FTL·GC·쓰기 증폭
  - architecture [13-latency-numbers](../13-latency-numbers/2-summary.md) — 디스크 지연의 자릿수
  - os [14-mmap-and-page-cache](../../os/14-mmap-and-page-cache/2-summary.md) · [24-fsync-and-durability](../../os/24-fsync-and-durability/2-summary.md) · [31-os-observability-tools](../../os/31-os-observability-tools/2-summary.md) · [32-raid](../../os/32-raid/2-summary.md)
  - math [10-queueing-and-littles-law](../../math/10-queueing-and-littles-law/2-summary.md) — IOPS·큐 깊이·이용률
  - data-structure [15-b-tree](../../data-structure/15-b-tree/2-summary.md) · [24-lsm-tree](../../data-structure/24-lsm-tree/2-summary.md), algorithm [11-external-sort-and-k-way-merge](../../algorithm/11-external-sort-and-k-way-merge/2-summary.md)
- 교재·문서
  - OSTEP 37 "Hard Disk Drives" — 37.3 탐색 단계·정착 0.5~2ms, 37.4 식 37.1·Figure 37.5·37.6(Cheetah 15K.5 / Barracuda, 랜덤 0.66·0.31MB/s 대 순차 125·105MB/s), 평균 탐색 거리 1/3, 37.5 SSTF·SCAN·C-SCAN·SPTF·merge·anticipatory <https://pages.cs.wisc.edu/~remzi/OSTEP/file-disks.pdf>
  - OSTEP 44 "Flash-based SSDs" — SSD 내부 <https://pages.cs.wisc.edu/~remzi/OSTEP/file-ssd.pdf>
  - CS:APP 3판 6.1.2 Disk Storage, 6.1.3 Solid State Disks(3판 목차 <https://csapp.cs.cmu.edu/3e/pieces/preface3e.pdf>로 절 번호 확인, 본문은 이번에 열지 않음)
  - Linux `block/blk-mq` — NONE 스케줄러, 소프트웨어 큐 병합(plugging) <https://docs.kernel.org/block/blk-mq.html>
- 실험 목록(i7-13700HX, Linux 7.0.0-34, ext4 on Samsung NVMe `MZVL2512HDJD`, 2026-10-07, 호스트 load average 약 9)
  - `seqrand.c`(gcc 13.3 `-O2 -pthread`) — `O_DIRECT` seq/rand 4KiB·128KiB, 랜덤 QD 1·4·16·32, 각 2초 × 3회, 512MiB 파일(측정 뒤 삭제)
  - `seqrand.c` 버퍼드 + `dropcache.c`(`posix_fadvise` DONTNEED) + `incore.c`(`mincore`) — 차가운/따뜻한 캐시, 미리 읽기 효과, 3회
  - `Elevator.java` — FCFS·SSTF·SCAN 총 이동 거리, 시드 3개, Docker `eclipse-temurin:21-jdk` `--cpus=2 --network none`
