# language/10-garbage-collection — 가비지 컬렉션: mark-sweep·복사·세대·동시 GC(G1·ZGC) — 정리 (힌트)

## 해결하는 문제

추적 GC는 "루트에서 닿지 않는 객체는 쓰레기"라는 규칙으로 해제를 자동화한다([09](../09-memory-management-models/2-summary.md)). 남는 문제는 **어떻게 빨리, 앱을 덜 멈추며** 그 판정을 하느냐다.

```text
  힙 512MB, 살아 있는 데이터 200MB, 초당 GB 단위 할당
   ├─ 매번 힙 전체를 훑으면 → 한 번에 수백 ms 멈춤
   ├─ 앱을 멈추지 않고 훑으면 → 훑는 동안 앱이 참조를 바꾼다 (놓치면 산 객체를 지운다)
   └─ 지운 뒤 빈칸이 흩어지면 → 큰 객체를 못 넣는다 (단편화)
```

- 이 노트는 세 질문에 대한 답을 차례로 본다: 무엇을 지우나(mark-sweep), 빈칸을 어떻게 모으나(복사·압축), 어떻게 덜 훑나(세대), 어떻게 덜 멈추나(동시 GC).
  - *STW(stop-the-world) 일시정지*: 수집기가 앱 스레드를 모두 세우고 일하는 구간. 이 동안 요청 처리가 멈춘다.

쉬운 예: 사무실 대청소다.
- 모두 일을 멈추게 하고 청소하면 빠르지만, 그동안 아무도 일을 못 한다.
- 일하는 중에 청소하면 업무는 계속되지만, 청소부가 "버려도 되는 서류"라고 표시한 뒤 누가 그 서류를 다시 집어 들 수 있다.
- 매번 창고까지 뒤지지 않고, 금방 버려지는 책상 위 메모지만 자주 치운다.

똑같은 구조다. 마지막이 세대 가설이다.\
실무 예:
- 배포 뒤 트래픽이 오르자 p99만 수백 ms로 튄다. GC 로그에 `Pause Full`이 찍혀 있다.
- 쿠버네티스 liveness 프로브가 짧은 타임아웃(예시: 1초)으로 실패해 파드가 재시작된다. 그 순간 긴 STW가 있었다.
- 힙 64MB 서비스가 `java.lang.OutOfMemoryError: GC overhead limit exceeded`로 죽는다(아래 실험 2).

## 동작·원리

### 1. mark-sweep — 칠하고 쓸어 낸다

```text
  삼색 마킹 (tricolour abstraction)
   흰색: 아직 못 봄 (끝까지 흰색이면 쓰레기)
   회색: 봤지만 그 객체의 참조 필드는 아직 안 따라감  ← 작업 목록(마크 스택)에 있음
   검은색: 봤고 참조도 다 따라감

  루트 ──> [A]──>[B]──>[C]        [D]<──>[E]
  1단계  A 회색                    D,E 흰색
  2단계  A 검정, B 회색
  3단계  A,B 검정, C 회색
  4단계  A,B,C 검정  → 회색 없음 → 마킹 끝.  D,E는 흰색 → sweep이 해제
```

- *mark*: 루트에서 그래프를 순회하며 산 객체에 표시. 회색 집합이 빌 때까지 반복한다.
- *sweep*: 힙을 훑으며 표시 안 된 칸을 빈칸 목록으로 돌린다.
- 비용: mark는 **살아 있는** 객체 수에, sweep은 **힙 전체** 크기에 비례한다.
- 약점: 객체를 옮기지 않으므로 빈칸이 흩어진다(단편화 — [os/11 §3](../../os/11-heap-allocation/2-summary.md)).

### 2. 복사·압축 — 산 것만 옮겨 빈칸을 한데 모은다

```text
  복사 (semispace)                         mark-compact
  from: [A][x][B][x][x][C][x]              [A][x][B][x][x][C][x]
          │      │        │                 ↓ 산 객체를 한쪽으로 민다
  to:   [A][B][C][          빈칸         ]   [A][B][C][   빈칸   ]
         ↑ 다음 할당은 여기서 포인터만 민다(bump pointer)
```

- *복사 수집*: 산 객체만 다른 공간으로 옮기고 원래 공간을 통째로 비운다. 비용은 **산 객체 양**에 비례하고, 공간은 두 배 든다.
- *압축(compaction)*: 같은 공간 안에서 산 객체를 한쪽으로 민다. 공간은 그대로, 대신 참조를 전부 고쳐야 한다.
- 옮긴 뒤 빈칸이 하나로 이어지므로 할당이 "포인터 하나 더하기"가 된다. JVM의 TLAB 할당이 이 모양이다([os/11 §2 자바](../../os/11-heap-allocation/2-summary.md), [12](../12-object-layout-and-allocation-reduction/2-summary.md)).
- 객체가 움직이므로 옛 주소를 가리키는 모든 참조를 새 주소로 고쳐야 한다. 앱을 멈추고 하면 쉽고, 동시에 하려면 장벽(barrier)이 필요하다(5절).

### 3. 세대 — 금방 죽는 것만 자주 치운다

```text
  JEP 439: "young objects tend to die young, while old objects tend to stick around"

  Young                                   Old
  [ Eden: 새 객체 ][ S0 ][ S1 ]   승격 →   [ 오래 산 객체 .................. ]
   Young GC: Eden+Survivor의 산 것만 복사 (짧음, 자주)
   Old 수집: 드물게, 크게 (Full GC 또는 G1의 mixed·동시 마킹)

  문제: Old → Young 참조는? Young GC 때 Old 전체를 훑으면 세대를 나눈 의미가 없다
   카드 테이블:  Old 영역을 512바이트 카드로 쪼개고, 참조 필드에 쓸 때 그 카드를 "더러움" 표시
   [0][0][1][0][0][1][0]   ← (Serial·Parallel) 1인 카드만 Young GC의 루트로 추가로 훑는다
```

- *세대 가설*(weak generational hypothesis): 대부분의 객체는 젊어서 죽는다. 그러면 젊은 영역만 자주 수집하면 적은 일로 많은 공간을 얻는다(JEP 439 Motivation).
- *승격(promotion)*: Young GC를 여러 번 살아남은 객체를 Old로 옮기는 것. HotSpot 기본 최대 나이 `MaxTenuringThreshold`=15(JDK 21 `-XX:+PrintFlagsFinal`로 확인).
- *카드 테이블·기억 집합(remembered set)*: 세대·영역 사이 참조를 따로 기록해 두는 구조. G1 문서: 힙을 기본 512바이트 카드로 나누고, 기억 집합 항목은 카드 인덱스다.
  - G1은 그림과 조금 다르다. 더러운 카드는 "쓰기가 일어난 후보 위치"일 뿐이라, 동시 정제(concurrent refinement) 스레드가 앱 실행 중에 그 카드를 훑어 영역별 기억 집합으로 옮겨 둔다. Young GC는 이 기억 집합(과 아직 정제 안 된 카드)을 합쳐 루트로 훑는다(JDK 21 G1 문서 "Remembered Set"·"Merge Heap Roots", G1 Tuning "concurrent refinement").
- *쓰기 장벽(write barrier)*: 참조 필드에 값을 쓸 때 JIT가 끼워 넣는 짧은 코드. 카드 표시가 여기서 일어난다. 그래서 GC 비용 일부는 앱 스레드의 매 참조 쓰기에 흩어져 있다.

### 4. 동시 GC — 앱이 도는 중에 칠하면 무엇이 깨지나

```text
  수집기 마킹 중 (A는 검정 = 다 봤음, B는 회색, C는 흰색)
     [A]검       [B]회 ──> [C]흰
  앱:   A.f = C        (검정 → 흰 간선 추가)
  앱:   B.g = null     (회색 → 흰 간선 제거)
  수집기: B를 따라가도 C가 없다 → C는 흰색으로 끝난다 → 산 객체 C를 지운다!
```

- 위 두 조건이 함께 일어나면 산 객체를 잃는다. 동시 수집기는 둘 중 하나를 장벽으로 막는다.
  - G1: *SATB*(snapshot-at-the-beginning). 마킹 시작 시점에 살아 있던 객체는 마킹 끝까지 산 것으로 본다(G1 문서). 그러려면 마킹 중 참조를 덮어쓸 때 옛 값을 수집기에 알려야 한다. OpenJDK jdk21u `g1BarrierSet.inline.hpp`의 `write_ref_field_pre`가 새 값을 쓰기 **전에** 필드의 옛 값을 SATB 큐에 넣는다(`g1BarrierSet.hpp` 주석: "objects that may have been disconnected from the pre-marking object graph"). "회색 → 흰 간선 제거"를 막는 쪽이다.
  - ZGC: *colored pointer*(참조 안에 상태 비트) + *load barrier*(참조를 읽을 때 끼워 넣는 코드). 세대형 ZGC는 store barrier도 쓴다(JEP 439 "Description").
- 대가: 장벽 코드가 앱 스레드 경로에 들어간다. 그리고 수집기 스레드가 앱과 CPU를 나눠 쓴다. CPU를 2개로 제한한 컨테이너에서는 이 경쟁이 앱 지연으로 보인다(실험 1의 ZGC).

### 5. HotSpot 수집기 지도 (JDK 21)

| 수집기 | 선택 옵션 | Young | Old | 앱 멈춤 |
|---|---|---|---|---|
| Serial | `-XX:+UseSerialGC` | 복사, STW, 스레드 1개 | mark-compact, STW | 길다 |
| Parallel | `-XX:+UseParallelGC` | 복사, STW, 병렬 | mark-compact, STW, 병렬 | 길다(처리량 우선) |
| G1 | `-XX:+UseG1GC`(서버급 기계 기본) | 영역 단위 복사, STW | 동시 마킹 + mixed 수집, 최후엔 Full GC | 목표 200ms(soft) |
| ZGC | `-XX:+UseZGC`(+`-XX:+ZGenerational`로 세대형) | 동시 | 동시 | `java` 문서 "max pause times of a few milliseconds" |

- 기본 수집기는 기계에 따라 다르다. CPU 2개 이상·메모리 1792MB 이상이면 G1, 아니면 Serial(Oracle GC 튜닝 가이드 2장, OpenJDK `os::is_server_class_machine`). 컨테이너에서 이 경계가 실제로 갈리는 모습은 [11](../11-gc-tuning-and-gc-logs/2-summary.md) 실험 1.
- JDK 21의 ZGC는 `-XX:+UseZGC`만 주면 비세대형이고, 세대형은 `-XX:+ZGenerational`을 더한다(JEP 439, Release 21). 이후 버전에서 기본값이 바뀌었다(JEP 474).
- G1 세부(영역·humongous·evacuation failure)와 튜닝은 [11](../11-gc-tuning-and-gc-logs/2-summary.md).

### 실험 1: 같은 부하, 네 수집기 (Java 21)

```java
// 오래 사는 데이터 200MB(1KB 배열 20만 개)를 유지하며, 짧게 사는 64~319바이트 배열을 8GB 할당.
// 오래 사는 쪽도 조금씩 교체. 별도 스레드가 sleep(1)을 반복하며 "깨어나기까지 초과 지연"을 잰다 = 앱이 본 멈춤.
byte[] tmp = new byte[64 + r.nextInt(256)]; sink = tmp;
if ((allocated & 0xFFFF) < 300) live[r.nextInt(live.length)] = new byte[1024];
```

`eclipse-temurin:21-jdk`(21.0.12), `--cpus=2 --memory=1g`, `-Xms512m -Xmx512m`, `-Xlog:gc`, 수집기마다 5회(집필 3회 + 사실 점검 재실행 2회, 범위). 재실행은 호스트에서 다른 실험이 함께 돌던 때(load average 약 10)라 시작이 느렸고 꼬리 값이 더 컸다:

| 수집기 | 총 시간 | 앱 지연 p99 | p99.9 | 최대 | 로그의 STW 합계 | STW 최대 | Full GC |
|---|---|---|---|---|---|---|---|
| Serial | 4.7~5.4s | 7.5~8.3ms | 12.6~87.4ms | 149~201ms | 925~1,077ms (63~66회) | 149~201ms | 1~2 |
| Parallel | 4.8~5.3s | 3.6~6.5ms | 83.9~119.7ms | 94~216ms | 847~918ms (76~97회) | 94~216ms | 2 |
| G1 | 5.4~6.4s | 3.4~7.5ms | 30.7~39.5ms | 72~122ms | 814~1,044ms (59~65회) | 69~111ms | 2~3 |
| ZGC(세대형) | 4.7~5.4s | 0.24~0.74ms | 3.2~13.9ms | 11.9~30.1ms | 7.2~9.1ms (256~307회, 별도 2회 `gc+phases`) | 0.063~0.145ms | 0 |

- 로그 한 줄 읽기: `GC(15) Pause Young (Normal) (G1 Evacuation Pause) 474M->231M(512M) 16.929ms` = 15번째 수집, 젊은 세대 STW, 힙 사용 474MB → 231MB(전체 512MB), 16.9ms 멈춤.
- STW 최대는 Serial·Parallel이 가장 길다. 시작 직후 200MB 살아 있는 데이터를 처음 옮기는 Young GC(Serial 128~157ms·Parallel 108~190ms)와 Full GC에서 나왔다. 같은 설정에서도 회차마다 최대값이 2배 가까이 갈렸다 — 꼬리 지연은 여러 번 돌려 범위로 본다.
- G1은 이 부하에서 `Evacuation Failure`(8~11회)와 `Pause Full (G1 Compaction Pause)`를 겪었다. 힙 512MB에 산 데이터 200MB + 큰 Young이 겹친 결과다. 원인과 처방은 [11](../11-gc-tuning-and-gc-logs/2-summary.md) 실험 2.
- ZGC의 STW는 모두 0.15ms 이하였다(`Pause Mark Start`·`Pause Mark End`·`Pause Relocate Start`, 2회 중 최대 0.063ms·0.145ms). 그런데 앱 지연 최대는 12~30ms였다. STW가 아니라 CPU 2개를 수집기 스레드와 나눠 쓴 결과일 가능성이 있다는 해석이다. 이 실험은 CPU 사용을 따로 재지 않았고, 재실행 때의 높은 호스트 부하로 인한 스케줄링 지연도 배제하지 못한다(로그에 `Allocation Stall`은 없었다).
- 총 시간은 수집기 사이 차이가 작았다(4.7~6.4s). 이 부하에서는 "어느 수집기가 빠르다"보다 "멈춤이 어떻게 분포하나"가 갈렸다. 다른 부하에서는 순위가 바뀔 수 있다.

## 쓰이는 자료구조·알고리즘

- **도달성 = 그래프 순회** — 마킹은 루트 집합에서 시작하는 BFS/DFS다. [algorithm/11-bfs](../../algorithm/11-bfs/2-summary.md)·[algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md), 그래프 표현은 [data-structure/08-graph](../../data-structure/08-graph/2-summary.md).
- **마크 스택(작업 목록)** — 회색 집합. 재귀 대신 명시적 스택을 써서 깊은 객체 그래프에서도 스택 오버플로를 피한다. [data-structure/03-stack](../../data-structure/03-stack/2-summary.md).
- **마크 비트맵** — 객체마다 1비트 "봤음" 표시. [data-structure/18-bitset](../../data-structure/18-bitset/2-summary.md).
- **삼색 마킹** — 흰·회·검 세 집합으로 진행 상태를 나눠, 동시 수집의 정확성 조건(검정 → 흰 간선 금지 등)을 말할 수 있게 한다.
- **카드 테이블(바이트 배열)·기억 집합** — 세대·영역 사이 참조 기록. 쓰기 장벽이 갱신한다.
- **bump pointer 할당** — 복사·압축 뒤 이어진 빈칸에서 포인터만 민다. [data-structure/35-allocator](../../data-structure/35-allocator/2-summary.md)의 bump 할당자와 같은 구조.
- **forwarding pointer** — 옮긴 객체의 옛 자리에 새 주소를 남겨, 다른 참조를 따라왔을 때 새 위치로 고친다.

## 적용 — 풀어나가는 법

### 1. 증상에서 GC를 의심하는 신호

```text
  p99·p99.9만 튀고 p50은 멀쩡하다              → STW 의심 (평균에는 안 보인다)
  튀는 시각이 주기적이다(수 초~수십 초 간격)       → Young GC 주기
  튀는 폭이 수백 ms~수 s, 드물다               → Full GC
  CPU 사용률이 높은데 처리량은 바닥이다           → GC가 시간을 다 쓴다 (실험 2)
```

### 2. 로그를 켜고 읽는다

```bash
# 시작 옵션 (JDK 9+ 통합 로깅)
java -Xlog:gc:file=/var/log/app/gc.log:time,uptime,level,tags -jar app.jar
# 실행 중인 JVM의 힙 요약, 1초마다 세대별 사용률·GC 횟수·누적 시간
jcmd <pid> GC.heap_info
jstat -gcutil <pid> 1000
```

- 먼저 볼 것: `Pause Full`의 개수와 원인 괄호(`Allocation Failure`·`Ergonomics`·`G1 Compaction Pause`·`System.gc()`), 그리고 Full GC 뒤 힙이 얼마나 내려가나(`511M->205M`이면 회수됨, `61M->61M`이면 못 회수 = 산 데이터가 꽉 참).
- 앱 지연 그래프와 GC 로그 시각을 나란히 놓는다. 스파이크 구간·길이가 STW 구간과 맞으면 GC가 유력하다(같은 구간에 다른 병목이 겹쳤을 수도 있다). 안 겹치면 다른 원인(락·I/O — [reliability/34-tail-latency-and-stragglers](../../reliability/34-tail-latency-and-stragglers/2-summary.md)).

### 3. 수집기를 고르는 첫 질문

| 요구 | 첫 후보 | 이유 |
|---|---|---|
| 배치·처리량, 멈춤 허용 | Parallel | 병렬 STW로 GC 총시간을 줄이는 것이 목표 |
| 일반 서비스, 수십~수백 ms 멈춤까지 허용 | G1 | 일시정지 목표(기본 200ms)를 두고 영역 단위로 나눠 수집 |
| 지연 민감, CPU 여유 있음 | ZGC(JDK 21은 `-XX:+ZGenerational`) | STW가 1ms 미만, 대신 동시 작업에 CPU를 더 쓴다 |
| 작은 컨테이너(1 CPU) | Serial이 기본으로 잡힘 | 의도한 선택인지 확인한다([11](../11-gc-tuning-and-gc-logs/2-summary.md)) |

- 선택 뒤의 조정(힙 크기·목표·IHOP)은 [11](../11-gc-tuning-and-gc-logs/2-summary.md), 할당 자체를 줄이는 법은 [12](../12-object-layout-and-allocation-reduction/2-summary.md).

## 장애 시나리오와 대처

### 1. ⚠ STW 일시정지 → p99 스파이크·헬스체크 실패

- **현상**: 평소 지연은 정상인데 몇 초~몇 분 간격으로 p99가 수백 ms로 튄다. 가끔 liveness 프로브가 실패해 파드가 재시작된다.
- **보이는 형태**: GC 로그의 `Pause Young`/`Pause Full` 시각이 지연 스파이크와 겹친다. 실험 1에서 같은 부하에 Serial의 앱 지연 최대 149~201ms, ZGC 12~30ms.
- **원인**: STW 동안 모든 요청 스레드가 멈춘다. 멈춤 길이는 옮겨야 할 산 데이터 양과 수집 방식에 달렸다.
- **대처**: 프로브 타임아웃을 관측된 최대 STW보다 넉넉히 잡는다. 수집기를 지연형(G1 → ZGC)으로 바꾸거나, 힙·Young 크기를 조정한다([11](../11-gc-tuning-and-gc-logs/2-summary.md)). 할당률을 줄이면 Young GC 횟수 자체가 준다([12](../12-object-layout-and-allocation-reduction/2-summary.md)).

### 2. ⚠ `OutOfMemoryError: GC overhead limit exceeded`

- **현상**: 서비스가 몇십 초 동안 거의 응답하지 않다가 OOM으로 죽는다.
- **보이는 형태**: 실험 2 — Parallel에서 `Pause Full (Ergonomics) 61M->61M(63M) 288ms`가 연달아 찍히고, 28초 중 27초가 STW였다.
- **원인**: 산 데이터가 힙을 거의 채워 매 수집이 거의 못 회수한다. Parallel은 GC 시간이 98%를 넘고 회수가 2% 미만이면 이 OOM을 던진다(`java` 문서 `-XX:+UseGCOverheadLimit`, 두 수치의 플래그 `GCTimeLimit`=98·`GCHeapFreeLimit`=2는 `gc_globals.hpp`·`PrintFlagsFinal`).
- **대처**: Oracle 문제 해결 가이드(JDK 21)는 이 에러의 전형적 원인을 "산 데이터가 힙에 겨우 들어가 여유가 없다"로 보고 힙 증설을 대처로 든다. 누수 없이 힙이 작아도 난다. 그래서 먼저 Full GC 뒤 바닥선이 시간이 지나며 오르는지(누수) 평평한지(힙 부족)를 가르고, 오르면 힙 덤프로 붙잡는 쪽을 찾는다([reliability/37](../../reliability/37-memory-leak-and-heap-analysis/2-summary.md)). `-XX:-UseGCOverheadLimit`로 끄면 죽는 시점만 늦어진다.

### 실험 2: static 컬렉션 누수 → 수집기마다 다른 OOM (Java 21)

```java
static Entry head;                                   // static 연결 리스트 — 지우지 않는다
for (;; i++) {
    head = new Entry(head, i);                       // 오래 사는 쪽: 계속 쌓인다 (항목당 32바이트 배열 포함)
    for (int k = 0; k < 20; k++) sink = new byte[64]; // 요청 중 짧게 사는 쓰레기
}
```

`-Xmx64m`, `--cpus=2`, 수집기마다 2회 + 사실 점검 재실행 1회:

```text
  Parallel  t=28167ms / 27698ms / 28161ms  entries≈758,000~792,2xx  OOM: GC overhead limit exceeded
            Pause Full 99회 / 99회 / 101회, STW 합계 27.3s / 27.0s / 27.6s
  G1        t=8616ms / 6644ms / 7732ms     entries≈772,000~798,000  OOM: Java heap space
            Pause Full 33회 / 22회 / 29회, 로그 마지막: "GC Overhead Limit exceeded too often (5)."
```

- 같은 누수인데 메시지가 갈렸다. Parallel은 문서대로 `GC overhead limit exceeded`를 던졌다.
- G1(21.0.12)도 같은 검사 코드가 있다(OpenJDK jdk21u `g1CollectedHeap.cpp` `update_gc_overhead_counter`). 로그에는 한도 초과가 찍혔지만 이 실행이 던진 메시지는 `Java heap space`였다. `java` 문서(21)는 이 정책을 parallel GC에 대해서만 설명한다.
- 어느 쪽이든 죽기 전 수 초~수십 초 동안 Full GC가 반복되며 거의 일을 못 했다. 알림은 OOM보다 "Full GC 빈도·GC 시간 비율"에 거는 것이 빠르다.

### 3. ⚠ static 컬렉션 누수 → Full GC 반복

- **현상**: 재시작 직후엔 괜찮다가 며칠에 걸쳐 Full GC 간격이 짧아진다.
- **보이는 형태**: Full GC 뒤 힙 바닥선(`→` 오른쪽 값)이 회차마다 오른다. 실험 2 G1(힙 64M)에서 Full GC 뒤 값이 `62M->54M` → `61M->58M` → 59M → 60M → 61M → 62M으로 회차마다 올라 힙 꼭대기에 닿았다(집필 2회 로그).
- **원인**: 지우지 않는 static 맵·리스너·ThreadLocal이 객체를 도달 가능하게 붙잡는다. GC는 이것을 쓰레기로 보지 않는다([09](../09-memory-management-models/2-summary.md) 장애 5).
- **대처**: 안정된 부하에서 바닥선이 계속 오르면 누수의 강한 징후로 보고(Oracle 문제 해결 가이드: "strong indication of a memory leak"), 힙 덤프의 지배자 트리로 붙잡는 필드를 찾아 확정한다([reliability/37](../../reliability/37-memory-leak-and-heap-analysis/2-summary.md)). 캐시는 크기 상한·만료를 둔다([data-structure/10-lru-cache](../../data-structure/10-lru-cache/2-summary.md)).

### 4. `System.gc()` 호출 → 원인 모를 Full GC

- **현상**: 부하와 무관하게 정해진 시각마다 긴 멈춤이 있다.
- **보이는 형태**: `Pause Full (System.gc())`.
- **원인**: 라이브러리·모니터링 도구·앱 코드가 `System.gc()`를 부른다.
- **대처**: G1 튜닝 가이드: 코드를 못 고치면 `-XX:+ExplicitGCInvokesConcurrent`(동시 사이클로 바꿈)나 `-XX:+DisableExplicitGC`(무시). 외부 도구가 요청하는 Full GC는 요청을 없애야 한다.

### 5. 지연형 수집기로 바꿨는데 CPU 제한에서 지연이 남는다

- **현상**: ZGC로 바꾼 뒤 로그의 STW는 1ms 미만인데, 앱의 최대 지연은 여전히 10ms대다.
- **원인(해석)**: 동시 수집기 스레드가 앱과 CPU를 나눈다. `--cpus=2` 같은 제한에서는 수집 중 앱 스레드가 CPU를 덜 받는다(실험 1).
- **대처**: CPU 한도에 여유를 두거나, 할당률을 줄여 동시 수집 빈도를 낮춘다. 수집이 할당을 못 따라가면 앱 스레드가 할당에서 기다리게 된다. ZGC는 이것을 `Allocation Stall` 단계로 기록한다(OpenJDK jdk21u `gc/z/zPageAllocator.cpp`). 실험 1의 로그에는 이 줄이 없었다.

## 핵심 문장

- 추적 GC의 핵심은 루트에서의 그래프 순회다. 삼색 마킹은 그 진행 상태를 흰·회·검 세 집합으로 나눈 것이다.
- mark-sweep은 산 것을 표시하고 나머지를 쓸어 내며, 복사·압축은 산 것만 옮겨 빈칸을 한데 모은다.
- 세대 가설 덕에 젊은 영역만 자주 수집해도 대부분의 공간을 되찾는다. 대가는 Old → Young 참조를 기록하는 카드 테이블과 쓰기 장벽이다.
- 동시 GC는 앱이 도는 중에 참조가 바뀌어 산 객체를 놓치지 않도록 장벽(SATB·load barrier)을 쓴다. 대신 앱 경로와 CPU에 비용이 흩어진다.
- 같은 부하에서도 수집기마다 멈춤의 분포가 다르다. 평균이 아니라 p99·최대와 GC 로그를 나란히 본다.
- `GC overhead limit exceeded`와 Full GC 반복은 "산 데이터가 힙을 거의 채웠다"는 신호다. 그것이 누수(계속 는다)인지 힙 부족(평평하다)인지는 Full GC 뒤 바닥선 추세로 가른다.

## 관련 주제·근거

- 선행
  - [09-memory-management-models](../09-memory-management-models/2-summary.md) — 추적 GC vs 참조 카운팅·소유권
  - [algorithm/11-bfs](../../algorithm/11-bfs/2-summary.md) — 그래프 순회
- 후속·연결
  - [11-gc-tuning-and-gc-logs](../11-gc-tuning-and-gc-logs/2-summary.md) — 수집기 선택·힙 크기·G1 evacuation failure·humongous
  - [12-object-layout-and-allocation-reduction](../12-object-layout-and-allocation-reduction/2-summary.md) — 할당률 줄이기·TLAB
  - [13-language-memory-model](../13-language-memory-model/2-summary.md) — 동시성의 순서 규칙
  - [os/11-heap-allocation](../../os/11-heap-allocation/2-summary.md) · [os/13-oom-and-memory-limits](../../os/13-oom-and-memory-limits/2-summary.md)
  - [reliability/37-memory-leak-and-heap-analysis](../../reliability/37-memory-leak-and-heap-analysis/2-summary.md) · [reliability/34-tail-latency-and-stragglers](../../reliability/34-tail-latency-and-stragglers/2-summary.md)
  - [languages/java/언어-특성 §7~8](../../../languages/java/언어-특성/README.md) — G1·ZGC를 고른 배경
- 교재
  - Jones·Hosking·Moss 『The Garbage Collection Handbook』 2판 — 2장 Mark-sweep(2.2 The tricolour abstraction, 2.4 Bitmap marking), 3장 Mark-compact, 4장 Copying, 9장 Generational(9.3 Generational hypotheses, 9.8 Inter-generational pointers), 11.8 Read and write barriers(Cards and card tables), 15장 Concurrent GC(The strong and weak tricolour invariants), 16.5 Garbage-First, 17장(ZGC 절). 장·절 번호는 공식 목차 <https://gchandbook.org/contents.html>에서 확인, 본문은 열지 못했다.
- 문서
  - Oracle "HotSpot Virtual Machine Garbage Collection Tuning Guide"(JDK 21) — 2장 Ergonomics(서버급 기계 = 프로세서 2개 이상·메모리 1792MB 이상, 기본 G1/Serial), 7장 G1(영역·카드 512바이트·기억 집합·SATB·evacuation failure·Full GC·humongous), 8장 G1 Tuning(Full GC 관찰, `ExplicitGCInvokesConcurrent`·`DisableExplicitGC`), 9장 ZGC <https://docs.oracle.com/en/java/javase/21/gctuning/>
  - Oracle "Troubleshooting Guide"(JDK 21) 메모리 누수 장 — `GC overhead limit exceeded`의 원인·대처, Full GC 뒤 live set 증가 = 누수의 강한 징후 <https://docs.oracle.com/en/java/javase/21/troubleshoot/troubleshooting-memory-leaks.html>
  - JEP 439 "Generational ZGC"(Release 21) — 세대 가설 인용, colored pointer·load/store barrier, `-XX:+ZGenerational` <https://openjdk.org/jeps/439>
  - `java` 도구 문서(JDK 21) — `-XX:+UseGCOverheadLimit`(98%·2%), `-XX:MaxGCPauseMillis`(G1 기본 200ms), `-XX:+UseZGC` <https://docs.oracle.com/en/java/javase/21/docs/specs/man/java.html>
  - OpenJDK jdk21u 소스 — `src/hotspot/share/gc/g1/g1CollectedHeap.cpp`(`update_gc_overhead_counter`, 로그 "GC Overhead Limit exceeded too often"), `src/hotspot/share/gc/shared/gc_globals.hpp`(`GCTimeLimit` 98, `GCHeapFreeLimit` 2, `GCOverheadLimitThreshold` 5), `src/hotspot/share/runtime/os.cpp`(`is_server_class_machine`), `src/hotspot/share/gc/shared/gcConfig.cpp`(`select_gc_ergonomically`)
  - JVMS SE21 §2.5.3 Heap <https://docs.oracle.com/javase/specs/jvms/se21/html/jvms-2.html>
- 실험(호스트 i7-13700HX, `eclipse-temurin:21-jdk` 21.0.12, `--cpus=2 --network none`)
  - 실험 1: 수집기 4종 같은 부하 — `--memory=1g`, `-Xms512m -Xmx512m`, 산 데이터 200MB + 할당 8GB, sleep(1) 지연 관찰 스레드, 각 3회 + 사실 점검 재실행 2회(호스트 부하 높음). ZGC STW는 `-Xlog:gc,gc+phases`로 별도 2회.
  - 실험 2: static 연결 리스트 누수 — `-Xmx64m`, Parallel·G1 각 2회 + 재실행 1회, OOM 메시지·Full GC 횟수·STW 합계
  - OpenJDK jdk21u `gc/g1/g1BarrierSet.hpp`·`g1BarrierSet.inline.hpp`(SATB 사전 쓰기 장벽), `gc/z/zPageAllocator.cpp`(`Allocation Stall`)
