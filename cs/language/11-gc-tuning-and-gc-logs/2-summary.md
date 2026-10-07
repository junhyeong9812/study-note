# language/11-gc-tuning-and-gc-logs — GC 튜닝과 GC 로그: 수집기 선택·힙 크기·일시정지 목표·컨테이너 — 정리 (힌트)

## 해결하는 문제

GC 알고리즘(10번)을 알아도, 운영에서 정할 것은 따로 있다: **어느 수집기를, 어떤 힙 크기와 목표로** 돌리나.

```text
  같은 이미지, 같은 코드
   파드 A: --memory=1g     → JVM이 Serial을 고르고 최대 힙 256MiB    (아래 실험 1)
   파드 B: --memory=4g     → G1, 최대 힙 1GiB
   파드 C: -Xmx를 limit 가까이 → 힙 밖 메모리까지 합쳐 OOMKilled (exit 137)
```

- 기본값은 "기계를 보고" 정해진다. 컨테이너에서는 그 기계가 cgroup 한도다. 모르고 두면 메모리를 낭비하거나, 의도치 않은 수집기로 돈다.
- 조정은 로그로 한다. GC 로그 한 줄에 멈춤 길이, 회수량, 원인이 다 들어 있다.

쉬운 예: 식당 설거지 담당을 정하는 일이다.
- 손님이 적은 가게(작은 컨테이너)에는 한 명이 몰아서 설거지한다(Serial).
- 바쁜 가게에는 여럿이 동시에 하되 "한 번에 3분 넘게 주방을 막지 않기" 같은 목표를 준다(G1의 일시정지 목표).
- 개수대(힙)를 너무 작게 두면 계속 설거지만 하고, 너무 크게 두면 가게(컨테이너)에 다른 물건 둘 자리가 없다.

똑같은 구조다.\
실무 예:
- 2 vCPU·1GiB 파드의 자바 서비스가 GC 로그 첫 줄에 `Using Serial`을 찍는다. 팀은 G1이라고 믿고 있었다.
- G1 로그에 `(Evacuation Failure)`가 몇 번 보인 뒤 `Pause Full (G1 Compaction Pause)`가 수십 ms~수백 ms 찍힌다(아래 실험 2).
- 큰 응답 버퍼를 요청마다 만들자 `G1 Humongous Allocation` 원인의 GC가 잦아진다(실험 3).

## 동작·원리

### 1. 기본값이 정해지는 길

```text
  cgroup memory.max·cpu 한도 (UseContainerSupport, 기본 true)
        │
        ▼
  "물리 메모리"·"CPU 수"로 본다
        │
        ├─ 서버급 기계? (CPU ≥ 2 그리고 메모리 ≥ 2GB − 256MB = 1792MB)
        │     예 → G1           아니오 → Serial
        │
        └─ 최대 힙 = 메모리 × MaxRAMPercentage(25%)
              단, 메모리가 작으면 × MinRAMPercentage(50%)
```

- Oracle GC 튜닝 가이드 2장: 서버급 기계에서는 G1, 아니면 Serial. 서버급 = "two or more processors and physical memory larger than or equal to 1792 MB". OpenJDK `os::is_server_class_machine`은 `2UL * G - 256UL * M`으로 계산한다.
- `MaxRAMPercentage`(기본 25%)·`MinRAMPercentage`(기본 50%)의 계산 규칙과 "작은 메모리" 경계는 [os/13 §5](../../os/13-oom-and-memory-limits/2-summary.md)에 소스와 함께 있다. 여기서는 JDK 21 컨테이너에서 실제로 나오는 값을 본다.

### 실험 1: 컨테이너 한도별 기본 수집기·최대 힙 (Java 21)

```bash
docker run --rm --cpus=<C> --memory=<M> eclipse-temurin:21-jdk \
  java -XX:+PrintFlagsFinal -Xlog:gc:stdout -version | grep -E "Using | MaxHeapSize | MaxRAMPercentage "
```

`eclipse-temurin:21-jdk`(21.0.12):

| 컨테이너 한도 | 고른 수집기 | MaxHeapSize | 비율 |
|---|---|---|---|
| 2 CPU, 200MiB | Serial | 100MiB | 50% (작은 메모리 규칙) |
| 2 CPU, 512MiB | Serial | 128MiB | 25% |
| 2 CPU, 1GiB | **Serial** | 256MiB | 25% |
| 2 CPU, 1791MiB | **Serial** | 448MiB | 25% |
| 2 CPU, 1792MiB | G1 | 448MiB | 25% |
| 2 CPU, 4GiB | G1 | 1GiB | 25% |
| 1 CPU, 4GiB | **Serial** | 1GiB | 25% |
| 2 CPU, 1GiB, `-XX:MaxRAMPercentage=75` | Serial | 768MiB | 75% |

- 1791MiB와 1792MiB 사이에서 수집기가 바뀌었다. 문서·소스의 경계와 정확히 일치한다.
- CPU 1개면 메모리가 커도 Serial이다.
- 1GiB 컨테이너는 기본으로 힙을 256MiB만 쓴다. 나머지 768MiB는 힙 밖(메타스페이스·스레드 스택·코드 캐시·direct buffer)과 여유다. 힙 밖 구성은 [os/13 §5](../../os/13-oom-and-memory-limits/2-summary.md).

### 2. 두 목표 — 처리량과 일시정지

```text
  처리량 목표   -XX:GCTimeRatio=n   GC 시간 : 앱 시간 = 1 : n     (예: 19 → GC 5%)
  일시정지 목표 -XX:MaxGCPauseMillis=t   "멈춤을 t ms 이하로" — 힌트(soft goal)
  둘 다 맞으면 → 힙을 줄여 본다(footprint)
```

- GC 튜닝 가이드 2장 "Behavior-Based Tuning": 수집기는 두 목표 중 하나를 우선한다. 일시정지 목표는 최근 멈춤에 가중치를 둔 평균 + 분산으로 판정하고, 이를 넘으면 목표 미달로 본다.
- `java` 문서: `MaxGCPauseMillis`는 soft goal이고 G1 기본값은 200ms다. G1 튜닝 가이드 표의 G1 `GCTimeRatio` 기본값은 12다.
- 같은 가이드 8장: G1은 기본 설정으로 쓰고, 필요하면 일시정지 목표와 `-Xmx`만 주라고 권한다. `-Xmn` 등으로 젊은 세대 크기를 고정하면 일시정지 목표를 맞추는 조정 수단을 막는다.

### 3. G1 힙 — 같은 크기 영역의 모음

```text
  힙 512MB, 영역 1MB × 512 (이 실험의 ergonomic 값: "Heap Region Size: 1M")
  [E][E][S][O][O][ ][H][H][O][E][ ][O] ...
   E = Eden  S = Survivor  O = Old  H = Humongous(영역 절반 이상 객체)  [ ] = 빈 영역
   Young GC:  E·S 영역 전부 + (mixed면) 회수 효율 높은 O 영역 몇 개 = collection set
   → 산 객체를 빈 영역으로 복사(evacuation) → 원래 영역은 통째로 빈 영역이 된다
```

- 영역은 할당·회수의 단위다(G1 문서 "Heap Layout"). 세대는 영역에 붙인 이름표일 뿐이라 젊은 세대 크기를 매 GC마다 바꿀 수 있다.
- 이름 "Garbage-First": 동시 마킹 뒤 Old 후보 영역을 **회수 효율 순**(빈 공간이 많고 수집 시간이 짧은 영역 먼저 — 문서: "More efficient regions that take less time to collect and that contain more free space")으로 정렬해 mixed 수집에서 먼저 가져간다(JDK 21 G1 문서 "Collection Set" 절: Cleanup 정지가 후보를 "sorting them according to efficiency"). 이름이 이 전략에서 왔다는 설명은 JDK 8 GC 튜닝 가이드 G1 장("This is why this method of garbage collection is called Garbage-First")에 있다. 정해진 시간 예산 안에서 효율 높은 것부터 고르는 탐욕 선택이다.
- 동시 마킹을 언제 시작하나: *IHOP*(Initiating Heap Occupancy Percent). 기본 `InitiatingHeapOccupancyPercent`=45이고, 기본으로 *적응형 IHOP*(`G1UseAdaptiveIHOP`=true)가 마킹 시간·할당 속도를 보고 값을 조정한다(G1 문서, JDK 21 `PrintFlagsFinal`).

### 4. 로그 한 덩어리 읽기 — `-Xlog:gc*`

```text
  [1.445s][info][gc,start    ] GC(15) Pause Young (Normal) (G1 Evacuation Pause)
  [1.445s][info][gc,task     ] GC(15) Using 2 workers of 2 for evacuation
  [1.462s][info][gc,phases   ] GC(15)   Evacuate Collection Set: 15.33ms      ← 대부분 산 객체 복사
  [1.462s][info][gc,heap     ] GC(15) Eden regions: 248->0(250)              ← Eden 248개 비움, 다음 목표 250개
  [1.462s][info][gc,heap     ] GC(15) Survivor regions: 21->21(34)
  [1.462s][info][gc,heap     ] GC(15) Old regions: 206->211                  ← Old 영역 5개 늘어남
  [1.462s][info][gc,heap     ] GC(15) Humongous regions: 1->1
  [1.462s][info][gc          ] GC(15) Pause Young (Normal) (G1 Evacuation Pause) 474M->231M(512M) 16.929ms
  [1.462s][info][gc,cpu      ] GC(15) User=0.02s Sys=0.01s Real=0.01s
```

- 위는 10번 실험 1과 같은 부하를 G1, `-Xms512m -Xmx512m`, `--cpus=2`로 돌린 실제 로그다.
- *할당률*: 직전 GC(14)가 끝난 1.318s에 226M, 이번 GC가 시작한 1.445s에 474M → 248MB / 0.127s ≈ **1.95GB/s**.
- *승격률*: Old 206 → 211, 한 번에 영역 5개(1MB 영역이라 대략 5MB 안팎). 로그 값은 영역 *개수*라 새 영역이 꽉 찼다는 보장이 없어 정확한 승격 바이트는 아니다. 할당 248MB 대비 대략 2% 수준이다. 세대 가설이 이 부하에서 잘 맞는다는 뜻이다.
- 승격률이 높아지면 Old가 빨리 차고, 동시 마킹이 늦으면 아래 evacuation failure로 이어진다.
- `Humongous regions: 1`은 산 데이터를 담은 `byte[][]` 배열(참조 20만 개 × 4바이트 ≈ 800KB)이다. 영역(1MB)의 절반 이상이라 humongous로 잡혔다.

### 실험 2: evacuation failure → Full GC, 그리고 힙 크기·목표 바꾸기 (Java 21)

같은 부하(산 데이터 200MB + 할당 8GB), G1, `--cpus=2 --memory=2g`, 설정마다 2회:

| 설정 | Young GC 횟수 | Young 평균 | Young 최대 | Evacuation Failure | Full GC | 앱 지연 최대 |
|---|---|---|---|---|---|---|
| `-Xmx512m`, 목표 200ms(기본) | 50 / 50 | 13.8 / 13.5ms | 35.1 / 33.3ms | 10 / 10 | 3 / 3 | 88 / 82ms |
| `-Xmx512m`, `MaxGCPauseMillis=20` | 101 / 62 | 9.8 / 11.6ms | 30.0 / 28.8ms | 12 / 8 | 0 / 2 | 30 / 79ms |
| `-Xmx1g`, 목표 200ms(기본) | 24 / 24 | 27.0 / 25.4ms | 65.2 / 59.3ms | 0 / 0 | 0 / 0 | 65 / 59ms |

```text
  -Xmx512m의 실제 순서 (10번 실험 1 로그에서)
  GC(22) Pause Young (Prepare Mixed) ...  483M->259M(512M)  9.665ms
  GC(23) Pause Young (Mixed) (G1 Evacuation Pause) (Evacuation Failure) 483M->484M(512M) 29.018ms
  GC(24) Pause Young (Mixed) (G1 Evacuation Pause) (Evacuation Failure) 507M->487M(512M) 11.127ms
  GC(25) Pause Young (Concurrent Start) (G1 Evacuation Pause) (Evacuation Failure) 511M->511M(512M) 2.829ms
  GC(26) Pause Full (G1 Compaction Pause) 511M->205M(512M) 81.525ms
```

- *evacuation failure*: 산 객체를 복사할 빈 영역이 모자란 상태. G1은 이미 옮긴 것은 두고, 못 옮긴 것은 제자리에 둔 채 GC를 끝낸다(G1 문서). 같은 부하를 `-Xlog:gc*`로 다시 돌린 실행에서 실패한 GC(23)는 `Old regions: 240->475`였다. 못 비운 영역이 Old로 넘어갔다는 해석이다.
  - 흔한 오해: "evacuation failure = 곧 OOM." G1 문서는 실패 GC도 "generally should be as fast as other young collections"라고 적는다. 위험은 그 뒤 공간이 회복되지 않을 때 오는 Full GC다.
  - JDK 17 G1 튜닝 가이드는 같은 상황을 "evacuation failure indicated by to-space exhausted tags"로 적는다. JDK 21 가이드와 21.0.12 로그의 문구는 `(Evacuation Failure)`다. 버전마다 검색할 문구가 다르다.
- G1 튜닝 가이드 8장 "Observing Full Garbage Collections": Full GC 앞에는 대개 `(Evacuation Failure)`가 있다. 원인은 회수가 할당을 못 따라가는 것이고, 흔히("Often") 동시 마킹이 공간 회수 단계를 제때 시작하지 못한 것이다. 위 로그처럼 `Prepare Mixed`·`Mixed`가 이미 시작된 뒤에도 실패할 수 있다 — 이때는 회수 속도가 모자란 것이다. 처방은 힙 늘리기, 동시 마킹 스레드 늘리기, 마킹을 더 일찍(`G1ReservePercent`↑ 또는 `-XX:-G1UseAdaptiveIHOP` + `InitiatingHeapOccupancyPercent`), humongous 줄이기다.
- 관찰
  - 힙을 1GiB로 늘리자 evacuation failure와 Full GC가 0이 됐다. 대신 Young 한 번이 더 길어졌다(평균 25~27ms). 젊은 세대가 커져 한 번에 더 많이 수집한다는 해석이다. 판정 재실행(`-Xlog:gc+heap`, 각 1회)에서 GC 직전 Eden 영역 수 중앙값이 512MB 228개 vs 1GiB 568개였다(복사한 산 객체 양은 재지 않았다).
  - 일시정지 목표 20ms는 Young 평균을 줄였지만 evacuation failure를 없애지 못했다. 한 번은 Full GC 0회, 다른 한 번은 2회로 갈렸다. 목표는 공간 부족을 고치지 못한다.

### 실험 3: humongous 할당 (Java 21)

```java
for (int i = 0; i < 4000; i++) sink = new byte[size];   // 요청마다 큰 버퍼
```

G1, `-Xms256m -Xmx256m -XX:G1HeapRegionSize=1m`, 각 2회 + 사실 점검 재실행 1회:

```text
  400KB × 4000   GC 14 / 14 / 16회   원인 "G1 Humongous Allocation" 0회          363 / 412 / 382ms
  600KB × 4000   GC 35 / 35 / 38회   원인 "G1 Humongous Allocation" 35 / 35 / 37회   512 / 518 / 504ms
                  집필 실행 첫 줄: GC(0) Pause Young (Concurrent Start) (G1 Humongous Allocation) 115M->2M(256M)
```

- 재실행은 `java Humongous.java`(소스 파일 실행)라 컴파일 중 할당으로 `G1 Evacuation Pause` 원인 GC가 1~2회 더 붙었다는 해석이다. 판정 재실행에서 `javac`로 미리 컴파일한 클래스(400KB, 2회)는 14회로 집필 실행과 같았고, 소스 파일 실행은 시작 1초 남짓에 `13M->4M` 같은 작은 GC가 먼저 찍혔다.

- 영역 1MB의 절반(512KB)을 넘는 600KB 배열은 humongous다. G1 문서: humongous는 Old에 연속 영역으로 바로 할당되고, 마지막 영역의 남은 칸은 그 객체가 회수될 때까지 못 쓴다. 600KB짜리가 1MB 영역 하나를 차지하니 40%가 버려진다.
- G1은 humongous 할당마다 IHOP를 검사해, 넘으면 바로 동시 마킹 시작 GC를 걸 수 있다(G1 문서 "may force an initial mark young collection immediately"). 그래서 GC 원인이 (컴파일 중 GC 1회를 빼면) 모두 `G1 Humongous Allocation`이 됐고 횟수가 약 2.4~2.5배였다.
- 처방(G1 튜닝 가이드 8장): `Humongous regions: X->Y`를 보고, 많으면 `-XX:G1HeapRegionSize`를 키우거나 큰 객체 할당을 줄인다(버퍼 재사용·스트리밍).

## 쓰이는 자료구조·알고리즘

- **세대 가설** — Young/Old 분리의 근거([10](../10-garbage-collection/2-summary.md)). 로그의 승격률이 가설이 맞는지 보여 준다.
- **탐욕 선택** — G1이 시간 예산 안에서 회수 효율이 높은 Old 영역부터 collection set에 넣는다. [algorithm/23-greedy](../../algorithm/23-greedy/2-summary.md).
- **가중 이동 평균 + 분산** — 일시정지 목표 판정(최근 멈춤에 가중치). 예측이 틀리면 목표를 넘는다.
- **고정 크기 영역(블록) 할당** — 힙을 같은 크기 영역으로 나누고 빈 영역 목록을 관리한다. humongous는 연속 영역이 필요해 단편화 문제가 다시 나온다([os/11 §3](../../os/11-heap-allocation/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 순서

```text
  1. 로그를 켠다           -Xlog:gc*:file=gc.log:time,uptime,level,tags  (상시 운영에서도 부담 작음 [?])
  2. 첫 줄들을 본다         "Using G1"? "Heap Region Size"? "Heap Max Capacity"? → 의도한 수집기·힙인가
  3. 산 데이터를 잰다       Full GC·mixed 뒤 바닥값 (예: 511M->205M → 산 데이터 ≈ 205M)
  4. 멈춤 분포를 본다       Pause Young 평균·최대, Pause Full 유무와 원인 괄호
  5. 할당률·승격률을 계산    위 4절처럼 GC 사이 증가량 / 시간
  6. 한 번에 하나만 바꾼다   힙 크기 → 목표 → IHOP 순, 같은 부하로 전후 비교
```

### 2. 컨테이너에서 힙을 정한다

```bash
# 힙을 한도의 비율로 (값은 예시 — 힙 밖 사용량을 재고 정한다, os/13 §3)
java -XX:MaxRAMPercentage=70 -XX:+UseG1GC -Xlog:gc*:file=/var/log/gc.log ...
# 실제로 적용된 값 확인
java -XX:MaxRAMPercentage=70 -XX:+PrintFlagsFinal -version | grep -E " MaxHeapSize | UseG1GC "
```

- 2 vCPU 미만 또는 1792MiB 미만 컨테이너에서 G1을 원하면 `-XX:+UseG1GC`를 명시한다(실험 1).
- `-Xms` = `-Xmx`로 두면 실행 중 힙 크기를 늘리고 줄이는 조정이 빠진다. 비교 실험의 변수를 줄이려고 이 노트의 실험(실험 1 제외)은 `-Xms` = `-Xmx`로 돌렸다.
- 힙을 limit 가까이 올리면 힙 밖 메모리 몫이 모자라 `OOMKilled`가 된다. 계산은 [os/13 §3·장애 2](../../os/13-oom-and-memory-limits/2-summary.md).

### 3. 증상별 첫 손잡이

| 증상 (로그) | 첫 손잡이 |
|---|---|
| `(Evacuation Failure)` 뒤 `Pause Full (G1 Compaction Pause)` | 힙↑, 마킹 일찍(`G1ReservePercent`↑ / IHOP 고정), 할당·승격 줄이기 |
| `G1 Humongous Allocation` 원인이 많음, `Humongous regions` 큼 | `G1HeapRegionSize`↑, 큰 배열 재사용 |
| `Pause Young` 평균이 목표보다 김 | 목표 확인, 산 데이터가 Young에 많은지(승격 직전 객체), 할당률 |
| `Pause Full (System.gc())` | [10 장애 4](../10-garbage-collection/2-summary.md) |
| `Using Serial`인데 의도와 다름 | `-XX:+UseG1GC` 명시 또는 CPU·메모리 한도 조정 |

## 장애 시나리오와 대처

### 1. ⚠ 컨테이너에서 기본 최대 힙(1/4)을 그대로 씀 → 메모리 낭비

- **현상**: 4GiB 파드의 자바 앱이 힙 1GiB에서 GC를 자주 돌린다. 컨테이너 메모리는 절반 이상 남는다.
- **보이는 형태**: 로그 첫 부분의 힙 최대 용량, `PrintFlagsFinal`의 `MaxHeapSize` = 한도의 25%(실험 1: 4GiB → 1GiB).
- **원인**: `MaxRAMPercentage` 기본 25%. 한 컨테이너에 JVM 하나뿐인 배치에서는 보수적인 값이다.
- **대처**: 힙 밖 사용량(NMT)을 잰 뒤 `MaxRAMPercentage`를 올린다(os/13의 예시 60~75). 바뀐 값을 `PrintFlagsFinal`로 확인한다.

### 2. ⚠ 힙을 limit 가까이 잡음 → `OOMKilled`(exit 137)

- **현상**: `-Xmx`를 한도의 90%로 올린 뒤 부하 때 파드가 로그 없이 재시작된다.
- **원인**: 힙 밖(메타스페이스·스레드 스택·코드 캐시·direct buffer)이 남은 10%를 넘었다. 커널이 cgroup 안 프로세스를 SIGKILL했다.
- **대처**: [os/13 장애 1·2](../../os/13-oom-and-memory-limits/2-summary.md). 힙은 비율로, 힙 밖은 상한(`MaxMetaspaceSize`·`MaxDirectMemorySize`)으로.

### 3. ⚠ G1 evacuation failure 뒤 Full GC

- **현상**: 평소 수십 ms 멈춤이던 서비스가 가끔 수십~수백 ms 멈춘다.
- **보이는 형태**: `(Evacuation Failure)` 태그가 붙은 Young/Mixed GC 몇 번 → `Pause Full (G1 Compaction Pause) 511M->205M`(실험 2).
- **원인**: 산 데이터(200MB)가 힙(512MB)에 비해 크고, 동시 마킹이 끝나 mixed 수집이 Old를 비우기 전에 공간이 바닥났다.
- **대처**: 실험 2에서 힙 1GiB로 Full GC 0. 힙을 못 늘리면 마킹을 일찍 시작하게 한다(`G1ReservePercent`, IHOP). 일시정지 목표만 낮추는 것은 이 실험에서 해결이 안 됐다.

### 4. ⚠ humongous 할당 반복

- **현상**: 큰 JSON 응답·파일 업로드를 처리할 때 GC가 잦아지고, 가끔 힙이 남아 있는데도 Full GC가 난다.
- **보이는 형태**: GC 원인 `G1 Humongous Allocation`, `Humongous regions: X->Y`의 Y가 Old 영역 수에 비해 크다(실험 3: 600KB 배열 → GC 35~37회가 이 원인).
- **원인**: 영역 절반 이상 객체는 연속 영역을 통째로 차지하고, 할당마다 마킹 시작 검사를 한다. 연속 영역을 못 찾으면 공간이 남아도 Full GC가 날 수 있다(G1 튜닝 가이드 "Humongous Object Fragmentation").
- **대처**: `-XX:G1HeapRegionSize`를 키워 humongous 문턱을 올린다. 큰 버퍼를 요청마다 새로 만들지 않고 재사용하거나 스트리밍한다([12](../12-object-layout-and-allocation-reduction/2-summary.md)).

### 5. 작은 컨테이너에서 Serial로 돌고 있었다

- **현상**: 1 vCPU 또는 1GiB대 파드로 줄인 뒤 p99가 크게 나빠졌다.
- **보이는 형태**: 로그 첫 줄 `Using Serial`(실험 1: 2 CPU·1791MiB까지 Serial).
- **원인**: 서버급 기계 판정(CPU ≥ 2, 메모리 ≥ 1792MB)에서 떨어져 기본 수집기가 바뀌었다. Serial은 Old 수집을 스레드 하나로 STW 처리한다([10](../10-garbage-collection/2-summary.md) 실험 1에서 최대 149~201ms).
- **대처**: 수집기를 명시한다(`-XX:+UseG1GC`). 정말 CPU 1개라면 동시 수집기가 쓸 CPU도 없다는 점을 함께 따진다.

## 핵심 문장

- JVM 기본값은 컨테이너 한도를 "기계"로 보고 정해진다: CPU 2개 이상·메모리 1792MB 이상이면 G1, 아니면 Serial, 최대 힙은 한도의 25%.
- `MaxGCPauseMillis`는 힌트다. 공간이 모자란 문제(evacuation failure·Full GC)는 목표를 낮춰서 고쳐지지 않는다.
- G1 로그 한 덩어리에서 멈춤 길이, 영역별 변화, 할당률(GC 사이 증가량/시간), 승격률(Old 증가)을 읽어 낸다.
- Full GC 앞의 `(Evacuation Failure)`는 회수가 할당을 못 따라간다는 신호다(흔한 원인은 동시 마킹이 늦게 끝나는 것). 힙을 늘리거나 마킹을 일찍 시작하게 한다.
- 영역 절반 이상 객체(humongous)는 영역을 통째로 쓰고, IHOP를 넘기면 마킹을 앞당길 수 있다. 영역 크기를 키우거나 큰 할당을 줄인다.
- 바꿀 때는 하나씩, 같은 부하로 전후 로그를 비교한다.

## 관련 주제·근거

- 선행
  - [10-garbage-collection](../10-garbage-collection/2-summary.md) — 수집 알고리즘·수집기 지도
  - [os/13-oom-and-memory-limits](../../os/13-oom-and-memory-limits/2-summary.md) — cgroup 한도, 힙 밖 메모리, `MaxRAMPercentage` 계산 규칙
- 후속·연결
  - [12-object-layout-and-allocation-reduction](../12-object-layout-and-allocation-reduction/2-summary.md) — 할당률 자체를 줄이기
  - [os/28-containers-namespaces-cgroups](../../os/28-containers-namespaces-cgroups/2-summary.md) · [algorithm/23-greedy](../../algorithm/23-greedy/2-summary.md)
  - [reliability/37-memory-leak-and-heap-analysis](../../reliability/37-memory-leak-and-heap-analysis/2-summary.md) · [reliability/34-tail-latency-and-stragglers](../../reliability/34-tail-latency-and-stragglers/2-summary.md)
- 문서
  - Oracle "HotSpot Virtual Machine Garbage Collection Tuning Guide"(JDK 21) <https://docs.oracle.com/en/java/javase/21/gctuning/>
    - 2장 Ergonomics — 기본 선택(G1/Serial, 서버급 1792MB, 최대 힙 1/4), Behavior-Based Tuning(일시정지 목표·처리량 목표 `GCTimeRatio`·footprint)
    - 7장 Garbage-First (G1) Garbage Collector — Heap Layout, Collection Set(회수 효율 순 정렬), IHOP·적응형 IHOP, SATB, Evacuation Failure, Humongous Objects
  - JDK 17 G1 튜닝 가이드 — "to-space exhausted" 표기 <https://docs.oracle.com/en/java/javase/17/gctuning/garbage-first-garbage-collector-tuning.html>, JDK 8 GC 튜닝 가이드 9장 G1 — 이름의 유래 <https://docs.oracle.com/javase/8/docs/technotes/guides/vm/gctuning/g1_gc.html>
    - 8장 Garbage-First Garbage Collector Tuning — Observing Full Garbage Collections, Humongous Object Fragmentation, Tunable Defaults 표(`GCTimeRatio`=12 등), `-Xmn` 고정 비권장
  - `java` 도구 문서(JDK 21) — `-XX:MaxGCPauseMillis`(soft goal, G1 기본 200ms), `-XX:MaxRAMPercentage`, `-XX:-UseContainerSupport` <https://docs.oracle.com/en/java/javase/21/docs/specs/man/java.html>
  - OpenJDK jdk21u 소스 — `src/hotspot/share/runtime/os.cpp` `is_server_class_machine`(2 CPU, `2UL*G - 256UL*M`), `src/hotspot/share/gc/shared/gcConfig.cpp` `select_gc_ergonomically`
- 실험(호스트 i7-13700HX, `eclipse-temurin:21-jdk` 21.0.12, `--network none`)
  - 실험 1: 컨테이너 한도 8가지 × `-XX:+PrintFlagsFinal -Xlog:gc:stdout -version` — 수집기·`MaxHeapSize`·`MaxRAMPercentage`(사실 점검 재실행 6가지 — 200MiB·1GiB·1791MiB·1792MiB·4GiB·1 CPU 4GiB — 모두 같은 값)
  - 4절 로그: 10번 실험 1 부하, G1 `-Xms512m -Xmx512m -Xlog:gc*`, `--cpus=2 --memory=2g`
  - 실험 2: 같은 부하, G1 설정 3가지 × 2회(`-Xmx512m` 기본 / `MaxGCPauseMillis=20` / `-Xmx1g`)
  - 실험 3: humongous — `-Xmx256m -XX:G1HeapRegionSize=1m`, 400KB vs 600KB 배열 4000개, 각 2회
  - 판정 재실행(2026-10-08): 실험 2 부하를 `-Xlog:gc,gc+heap=info`로 512MB·1GiB 각 1회(GC 직전 Eden 영역 수), 실험 3 400KB를 `javac` 선컴파일 클래스 2회 vs 소스 파일 실행 2회
  - JDK 21 G1 기본 플래그: `MaxGCPauseMillis` 200, `InitiatingHeapOccupancyPercent` 45, `G1UseAdaptiveIHOP` true, `G1ReservePercent` 10, `MaxTenuringThreshold` 15 (`-XX:+PrintFlagsFinal`, `--cpus=2 --memory=2g -Xmx512m`)
