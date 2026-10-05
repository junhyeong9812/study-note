# data-structure/26-timer-structures — 타이머 힙 vs 해시·계층형 타이머 휠 — 정리 (힌트)

## 해결하는 문제

서버는 연결·요청마다 "N초 안에 안 끝나면 끊어라"를 건다. 그런 타이머가 동시에 수십만~수백만 개 살아 있을 수 있다.

```text
  연결 50만 개 × (읽기 타임아웃 + 유휴 타임아웃) = 타이머 100만 개 (예시)

  타이머의 일생 (대부분)          타이머의 일생 (가끔)
  등록 ──> 응답 도착 ──> 취소       등록 ──> ... ──> 만료 → 연결 끊기
```

- 리눅스 `kernel/time/timer.c` 주석: "The vast majority of timeout timers (networking, disk I/O ...) are canceled before expiry."
- 그래서 타이머 구조는 네 연산을 싸게 해야 한다(Varghese–Lauck 1987의 모델).
  - *START_TIMER*: 등록. *STOP_TIMER*: 취소. *PER_TICK_BOOKKEEPING*: 시계가 한 칸 갈 때마다 하는 일. *EXPIRY_PROCESSING*: 만료된 것 실행.
- 선택지는 둘이다.
  - **타이머 힙**: 만료 시각 순서를 정확히 지킨다. 연산마다 O(log n).
  - **타이머 휠**: 시간을 칸(틱)으로 나눈 배열의 링. 등록·취소가 O(1)이다. 대신 **틱보다 정밀하게 맞추지 못한다.**

쉬운 예: 알람 시계 100만 개.
- 힙 = 알람을 울릴 시각 순으로 줄 세워 맨 앞만 본다. 새 알람마다 줄 자리를 찾아 끼운다.
- 휠 = 시계판 칸마다 바구니를 두고, 알람을 그 시각 칸에 던져 넣는다. 바늘이 가리키는 바구니만 연다.

똑같은 구조다.\
실무 예:
- Java `ScheduledThreadPoolExecutor`·`DelayQueue`·`java.util.Timer`는 힙이다(OpenJDK 소스).
- Netty `HashedWheelTimer`(틱 100 ms, 512칸)는 해시 휠이다.
- Kafka의 요청 대기소(purgatory)는 `DelayQueue`에서 계층형 휠로 바꿨다(Confluent 블로그 2015).
- 리눅스 커널 `timer_list`는 4.8부터 계단식 이동(cascading)을 없앤 계층형 휠이다(kernelnewbies 4.8).

## 동작·원리

### 1. 타이머 힙 — 만료 시각을 키로 한 최소 힙

```text
  만료 시각(ms)으로 정렬된 최소 힙
                [ 105 ]               ← peek: 다음에 울릴 것, O(1)
              /         \
         [ 230 ]       [ 150 ]
          /   \         /
      [900] [400]   [170]

  등록(add)  : 맨 끝에 넣고 위로 올림        O(log n)
  만료(poll) : 루트를 빼고 끝 원소를 내림    O(log n)
  취소       : 위치를 알면 O(log n), 모르면 찾느라 O(n)
```

- 힙 자체는 [07-heap](../07-heap/2-summary.md)에서 다뤘다. 이 노트는 **취소**와 **개수**에 집중한다.
- 취소가 문제다. 힙은 "가장 작은 것"만 빨리 찾는다. 임의의 원소를 찾는 데는 O(n)이다.
  - `PriorityQueue` Javadoc: enqueue·dequeue는 O(log(n)), `remove(Object)`·`contains(Object)`는 "linear time".
  - `ScheduledThreadPoolExecutor`의 `DelayedWorkQueue`는 작업마다 힙 안 위치(`heapIndex`)를 기록한다. 소스 주석: 이것이 취소 시 제거를 "down from O(n) to O(log n)"으로 줄인다.
- 다른 길은 **지연 취소**다. 취소 표시만 하고 힙에 그대로 둔다. 루트까지 올라오면 그때 버린다.
  - 취소는 O(1)이 되지만, 힙 크기 = 살아 있는 것 + 취소된 쓰레기.
  - `ScheduledThreadPoolExecutor`의 기본이 이것이다. `setRemoveOnCancelPolicy` Javadoc: 취소 즉시 제거 여부는 "by default false".

#### 실험: 취소한 타이머는 어디에 남나 (`CancelLeak.java`)

1시간 뒤 실행할 작업 10만 개를 등록하자마자 취소했다(응답이 와서 타임아웃을 지우는 상황).

(실험, eclipse-temurin:21-jdk = OpenJDK 21.0.12, docker `--cpus=2`, 2026-10-05)

```text
removeOnCancel=false(기본 false): 취소 10만 개 뒤 getQueue().size()=100000
removeOnCancel=true(기본 false): 취소 10만 개 뒤 getQueue().size()=0
```

- 기본값에서는 취소한 10만 개가 1시간 동안 큐에 남는다. 요청률이 일정하면 남는 작업 수는 처음 타임아웃 길이 동안 오르다가 대략 `초당 취소 수 × 타임아웃 길이`에서 멈춘다. 그 규모가 가용 힙을 넘으면 `OutOfMemoryError`가 된다(장애 2).

### 2. 기본 타이밍 휠 — 칸 하나 = 틱 하나

```text
  틱 = 1 ms, 칸 8개, 현재 시각 바늘 = 2

   slot:  0     1     2     3     4     5     6     7
        [   ] [   ] [ ^ ] [ a ] [   ] [b,c] [   ] [   ]
                     now
  "3 ms 뒤" 등록 → (2 + 3) % 8 = 5번 칸 리스트 앞에 붙인다        O(1)
  취소        → 이중 연결 리스트에서 떼어 낸다                   O(1)
  매 틱       → 바늘을 한 칸 옮기고 그 칸 리스트만 실행           O(1) + 만료 수
```

- Varghese–Lauck의 **Scheme 4**다. 타이머가 전부 `MaxInterval`(칸 수 × 틱)보다 짧으면 세 연산이 모두 O(1)이다.
  - *틱(tick)*: 휠 바늘이 한 칸 움직이는 시간 단위. 해상도(정밀도)의 한계다.
- 문제: 1 ms 틱으로 1시간을 덮으려면 칸이 360만 개 필요하다(3600 × 1000). 더 긴 범위는 칸을 늘리는 대신 아래 두 방법으로 푼다.

### 3. 해시 휠 — 칸에 "몇 바퀴 남았나"를 함께 적는다

```text
  칸 8개, 틱 1 ms, now = 2.  "21 ms 뒤" 등록
  만료 틱 = 23 → 칸 = 23 % 8 = 7, 남은 바퀴 rounds = (21-1) / 8 = 2

   slot 7: [ d(rounds=2) ] ─ 바늘이 7에 올 때마다: rounds>0 이면 1 줄이고 지나감
                              rounds==0 이면 만료 실행

  바늘이 7번 칸을 지나는 시각: 7(rounds 2→1), 15(1→0), 23(만료)
```

- Varghese–Lauck의 **Scheme 6**(정렬 안 한 리스트를 담은 해시 테이블)이다.
  - 등록·취소는 O(1). 칸을 고르는 해시는 "2의 거듭제곱으로 나눈 나머지(AND 한 번)"를 권한다(논문 6.1).
  - 대신 매 틱마다 그 칸에 든 타이머를 **전부** 훑으며 rounds를 줄인다. 논문: "for n timers we do n/TableSize work on average per tick."
- Netty `HashedWheelTimer`가 이 모양이다(Netty 4.1 소스).
  - 기본 틱 100 ms, 칸 512개. 칸 수는 다음 2의 거듭제곱으로 올린다(`createWheel`).
  - 등록 시 `remainingRounds = (calculated - tick) / wheel.length`. 여기서 `tick`은 워커가 **다음에 처리할** 틱이다(같은 반복에서 곧바로 그 칸을 처리한다). 아래 실험 코드의 `now`는 마지막으로 처리한 틱이라 `tick = now + 1`에 해당하고, 그래서 식에 `- 1`이 붙는다.
  - Javadoc: "this timer does not execute the scheduled TimerTask on time" — 정밀도보다 비용을 고른 설계다.

#### 실험: 힙 vs 해시 휠(칸 수 둘) — 등록 후 전부 만료 (`TimerBench.java` A)

만료 시각을 1..100000 틱에 고르게 뿌린 타이머 N개를 등록하고, 가상 시각을 100000 틱까지 돌려 전부 만료시켰다. 힙은 `PriorityQueue`, 휠은 직접 구현(이중 연결 리스트 칸).

휠 핵심 코드:

```java
T add(long delayTicks) {                       // O(1)
    T t = new T(); t.deadline = now + Math.max(1, delayTicks);
    t.rounds = (t.deadline - now - 1) / heads.length;
    int s = (int) (t.deadline & mask); t.slot = s;
    t.next = heads[s]; if (t.next != null) t.next.prev = t; heads[s] = t;
    return t;
}
int tick() {                                   // 칸 하나만 훑는다
    now++; int fired = 0;
    for (T t = heads[(int) (now & mask)]; t != null; ) {
        T nx = t.next;
        if (t.rounds == 0) { cancel(t); fired++; } else t.rounds--;   // 아직이면 바퀴 수만 줄인다
        t = nx;
    }
    return fired;
}
```

(실험, OpenJDK 21.0.12, docker `--cpus=2`, 단일 스레드 가상 시간, 같은 프로그램 3회 실행, 2026-10-05)

```text
== A. 삽입 N + 전부 만료 (만료 시각 1..100000 틱 균등)
N=  250,000  heap(add+poll)   469 ms | wheel 512슬롯  3873 ms | wheel 131072슬롯    72 ms  fired=250000/250000/250000
N=  500,000  heap(add+poll)  1008 ms | wheel 512슬롯  6543 ms | wheel 131072슬롯   122 ms  fired=500000/500000/500000
N=1,000,000  heap(add+poll)  1904 ms | wheel 512슬롯 20862 ms | wheel 131072슬롯   293 ms  fired=1000000/1000000/1000000
```

- 3회 범위(N=100만): 힙 1862~1904 ms, 512칸 휠 3809~20862 ms, 131072칸 휠 214~293 ms.
- 사실 점검 재실행 1회(같은 코드·환경, N=100만): 힙 1740 ms, 512칸 휠 4150 ms, 131072칸 휠 200 ms. 512칸 휠은 이 회차에서 N=50만(5143 ms)이 N=100만보다 느렸다. 4회를 합친 범위는 힙 1740~1904 ms, 512칸 휠 3809~20862 ms, 131072칸 휠 200~293 ms다. 순서(131072칸 < 힙 < 512칸)는 4회 모두 같았다.
- 관찰
  - 칸이 만료 범위(100000틱)보다 많은 휠은 rounds가 늘 0이라 타이머마다 한 번만 만진다. N=100만에서 힙보다 6~9배(3회), N=25만에서 5~7배 빨랐다.
  - 512칸 휠은 **힙보다 느렸다.** 평균 만료가 약 5만 틱 뒤이므로 타이머 하나가 만료 전 약 100번(5만 / 512) 훑인다. 논문의 n/TableSize 비용이 그대로 드러났다.
  - 512칸 휠 수치가 3.8~20.9초로 크게 흔들렸다(N 크기 순서와도 어긋나는 회차가 있었다). 원인은 분석하지 않았다 [?] (연결 리스트를 반복해 훑는 메모리 접근과 GC가 후보).
  - 힙은 N이 두 배일 때 시간이 약 2배(1008 → 1904 ms)다. log n 인자는 이 범위에서 잘 안 보인다.
- 정리: 해시 휠의 O(1)은 **등록·취소**의 이야기다. 틱마다 훑는 비용은 평균적으로 "타이머 수 / 칸 수"에 비례하므로, 칸 수를 타임아웃 범위에 맞게 잡아야 한다. Netty Javadoc도 "You could specify a larger value if you are going to schedule a lot of timeouts"라고 적는다.

#### 실험: 취소 비용 — `PriorityQueue.remove(Object)` vs 휠 (`TimerBench.java` B)

(실험, OpenJDK 21.0.12, docker `--cpus=2`, 2회 실행, 2026-10-05. N=10000은 JIT 워밍업용)

```text
== B. 삽입 N + 전부 취소 (타임아웃 대부분은 만료 전에 취소된다)
N= 10,000  PriorityQueue.remove(Object) 전부    120 ms   wheel.cancel 전부    226 us  (남은 크기 0/0)
N= 20,000  PriorityQueue.remove(Object) 전부    108 ms   wheel.cancel 전부    446 us  (남은 크기 0/0)
N= 40,000  PriorityQueue.remove(Object) 전부    409 ms   wheel.cancel 전부    386 us  (남은 크기 0/0)
N= 80,000  PriorityQueue.remove(Object) 전부   1265 ms   wheel.cancel 전부    890 us  (남은 크기 0/0)
```

- 2회째: 104 → 397 → 1094 ms(힙), 365 → 549 → 1081 µs(휠).
- 사실 점검 재실행: 112 → 428 → 1066 ms(힙), 611 → 537 → 1063 µs(휠).
- 관찰: `remove(Object)`는 N이 두 배일 때 시간이 약 2.5~3.8배다(3회). 취소 하나가 O(n)이라 전체가 O(n²)에 가깝다. 휠은 µs 단위로, N에 대략 비례했다.
- 그래서 실전 힙 타이머는 위치 인덱스(`heapIndex`)나 지연 취소를 쓴다. 지연 취소는 1절 실험의 쓰레기 문제를 낳는다.

### 4. 계층형 휠 — 시·분·초 시계판

```text
  Varghese–Lauck Scheme 7 의 예: 100일까지
   일 [100칸]   시 [24칸]   분 [60칸]   초 [60칸]      = 244칸  (평평하게 하면 864만 칸)

  논문의 예: 지금 11일 10시 24분 30초, "50분 45초 뒤" 등록
    만료 시각 = 11일 11시 15분 15초
    → 시 바퀴의 1칸 앞(11시)에 둔다 (나머지 15분 15초를 함께 적음)
  시 바늘이 11에 오면 → 분 바퀴의 15칸 뒤로 옮긴다 (cascade, 계단식 이동)
  분 바늘이 그 칸에 오면 → 초 바퀴의 15칸 뒤로 옮긴다
  초 바늘이 오면 → 만료
```

- 등록은 O(m)(m = 단계 수), 취소 O(1). 정확한 시각을 지키려면 위 단계에서 아래 단계로 **옮겨 담는 비용**이 든다.
- Kafka purgatory(Confluent 블로그 2015)
  - 크기 n, 단위 u인 휠은 n × u 구간을 담는다. 넘치면 더 거친 "overflow wheel"로 보낸다. 등록 O(m), 삭제 O(1).
  - 바늘을 매 틱 돌리는 대신, **버킷**을 `DelayQueue`에 넣는다. 큐 원소 수가 버킷 수로 제한된다.
  - 옛 구현은 `DelayQueue`(O(log n))였고, 끝난 요청을 즉시 지우지 않아 "the server may exhaust JVM heap and cause OutOfMemoryError"였다.

### 5. 리눅스 4.8+ — 옮겨 담지 않는 계층형 휠

```text
  HZ=1000 (timer.c 주석 표, 레벨 9개 중 앞 4개)
  Level  Granularity   Range
   0       1 ms        0 ms -     63 ms
   1       8 ms       64 ms -    511 ms
   2      64 ms      512 ms -   4095 ms
   3     512 ms     4096 ms -  32767 ms
   ...
  레벨마다 칸 64개(LVL_BITS 6), 레벨이 오를 때마다 정밀도가 8배 거칠어진다(LVL_CLK_SHIFT 3)
```

- 먼 만료일수록 위 레벨(거친 칸)에 넣고, **아래로 옮기지 않는다.** 그 칸 그대로 만료된다.
- 그래서 오래 걸리는 타이머는 늦게 울릴 수 있다. 주석의 근거: 타임아웃 대부분은 만료 전에 취소되고, 만료됐다면 이미 정상이 아니므로 조금 늦어도 큰 문제가 아니다. 짧은 네트워킹 타이머는 1 ms 정밀도의 0레벨에 들어간다.
- 마지막 레벨 용량보다 긴 타이머는 그 최대값에서 강제로 만료된다(주석: 관측된 최대는 연결 추적의 5일).
- 정밀한 시각이 필요한 것은 별도의 고해상도 타이머(hrtimer)가 맡는다(커널 문서 hrtimers).
- 리눅스 TCP 재전송 타이머(`tcp_retransmit_timer`)는 `struct timer_list`다(메인라인 `include/net/sock.h`, 2026-10-05 조회).

### 6. 해상도 오차 — 틱보다 짧은 타임아웃

```text
  틱 100 ms 휠.  t=37 ms 에 "10 ms 뒤" 등록

   0        37  47      100       200
   |─────────●──○────────|─────────|
             등록 원하는 만료  ↑ 첫 틱 경계에서야 확인 → 실제 63 ms 뒤 실행

  실제 지연 = 요청 지연 + (다음 틱 경계까지 남은 시간)   →  요청 ≤ 실제 < 요청 + 틱 (+ 스케줄링 지연)
```

#### 실험: 틱 100 ms 휠 vs `ScheduledThreadPoolExecutor` 실제 지연 (`WheelLatency.java`)

전용 스레드가 100 ms마다 깨어나는 간단한 휠(Netty처럼 등록은 다음 틱에서 반영)과 STPE에 같은 타임아웃을 20개씩, 틱 사이 임의 시점에 걸었다.

(실험, OpenJDK 21.0.12, docker `--cpus=2`, 실시간 측정, 2026-10-05)

```text
요청  10 ms: wheel(tick 100ms) 실제 20..108 ms 평균 62 (n=20) | STPE 실제 10..16 ms 평균 10 (n=20)
요청 150 ms: wheel(tick 100ms) 실제 162..249 ms 평균 214 (n=20) | STPE 실제 150..150 ms 평균 150 (n=20)
```

- 사실 점검 재실행(같은 코드·환경): 휠 10 ms 요청 → 10..107 ms 평균 59, 150 ms 요청 → 160..250 ms 평균 199. STPE 10..15 ms, 150..150 ms.
- 관찰: 휠은 10 ms 요청을 10~108 ms 뒤에 실행했다(2회). 150 ms 요청은 160~250 ms. 실제 지연이 대략 "요청 + 0~1틱" 안에 있다(250 ms는 경계값으로, 스케줄링 지연이 더해질 수 있다). 힙 기반 STPE는 10~16 ms, 150 ms로 요청에 가까웠다.
- 휠의 수치는 이 실험의 틱(100 ms)과 등록 반영 방식에 달렸다. 실행마다 다르다(n=20씩 2회).

## 쓰이는 자료구조·알고리즘

- 이 주제가 쓰는 하위 구조
  - 이진 힙([07-heap](../07-heap/2-summary.md)) — 타이머 힙. 위치 인덱스로 O(log n) 취소.
  - 링 버퍼([25-ring-buffer](../25-ring-buffer/2-summary.md)) — 휠의 칸 배열이 링이다. 2의 거듭제곱 칸 수 + 마스크도 같다.
  - 이중 연결 리스트([02-linked-list](../02-linked-list/2-summary.md)) — 칸 안의 타이머 목록. 노드를 알면 O(1)로 뗀다.
  - 해시(나머지 = 칸 고르기, [05-hashmap](../05-hashmap/2-summary.md)), 기수 정렬과의 유비(논문: Scheme 7 ↔ radix sort, Scheme 5 ↔ bucket sort).
- 이 주제를 쓰는 곳(🔧)
  - 커널 타이머(`timer_list`, 계층형 휠), TCP 재전송·지연 ACK 타이머([network/16](../../network/16-tcp-reliability-retransmission/2-summary.md), [network/22](../../network/22-nagle-and-delayed-ack/2-summary.md)).
  - Netty `HashedWheelTimer` — I/O 타임아웃.
  - Kafka purgatory — `acks=all` 생산 요청·`min.bytes` fetch 요청이 조건을 기다리는 곳.
  - Java `ScheduledThreadPoolExecutor`·`DelayQueue`·`java.util.Timer` — 힙.
  - 레이어별 타임아웃([reliability/07-timeout-taxonomy-by-layer](../../reliability/07-timeout-taxonomy-by-layer/2-summary.md)), 스케줄러([ops-patterns/10-scheduler](../../ops-patterns/10-scheduler/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 어느 것을 고르나

```text
  타이머 수가 적다(수천 이하) 또는 정확한 시각이 중요 ──> 힙 (ScheduledThreadPoolExecutor)
  타이머 수가 많고, 대부분 취소되고, 수십~수백 ms 오차를 견딘다 ──> 해시/계층형 휠
  타임아웃 범위가 넓다(ms ~ 시간) ──> 계층형 휠, 또는 휠 칸 수 × 틱 ≥ 흔한 타임아웃
```

- `java.util.Timer` Javadoc: 이진 힙이라 등록이 O(log n)이고 "thousands should present no problem". 그보다 많으면 재 보고 고른다.

### 2. 힙을 쓸 때 — 취소 정책을 켠다

```java
var scheduler = new ScheduledThreadPoolExecutor(1);
scheduler.setRemoveOnCancelPolicy(true);   // 기본 false: 취소한 작업이 만료 시각까지 큐에 남는다

ScheduledFuture<?> timeout = scheduler.schedule(() -> conn.close(), 30, TimeUnit.SECONDS);
// ... 응답 도착
timeout.cancel(false);                      // removeOnCancel=true 면 heapIndex 로 O(log n) 제거
```

- 1절 실험: 기본값에서 취소 10만 개 뒤 `getQueue().size()=100000`, 켠 뒤 0.

### 3. 휠을 쓸 때 — 틱·칸 수를 타임아웃에 맞춘다

```java
// Netty 4.1 예: 틱 10 ms, 칸 1024 → 한 바퀴 10.24초. 흔한 타임아웃(수 초)이 한두 바퀴 안에 든다
HashedWheelTimer timer = new HashedWheelTimer(10, TimeUnit.MILLISECONDS, 1024);
Timeout t = timer.newTimeout(task -> onTimeout(), 3, TimeUnit.SECONDS);
// 응답 도착
t.cancel();
```

- 휠이 제때 도는 동안 해상도 오차는 대략 0~1틱이다(6절). 이것은 일반적인 상한이 아니다. 워커가 늦게 깨거나, 틱마다 대기 큐에서 칸으로 옮기는 수가 최대 10만 개라(Netty 4.1 소스 `transferTimeoutsToBuckets`) 등록이 몰리거나, 실행 중인 작업이 오래 걸리면 더 늦어질 수 있다. 틱을 줄이면 오차는 줄고, 빈 칸을 도는 틱 처리 횟수가 는다.
- 인스턴스는 하나를 공유한다. Netty Javadoc: 인스턴스마다 스레드를 만들며, 연결마다 만드는 것이 흔한 실수다. 많이 만들면 "You are creating too many HashedWheelTimer instances" 오류 로그를 남긴다(소스 `INSTANCE_COUNT_LIMIT` 64).
- 대기 타임아웃 수 상한(`maxPendingTimeouts`)을 넘으면 `RejectedExecutionException`이다(소스). 기본은 제한 없음(-1).

### 4. 진단

- 힙이 커진다: `jcmd <pid> GC.class_histogram`에서 `ScheduledThreadPoolExecutor$ScheduledFutureTask` 개수가 실제 진행 중 요청보다 훨씬 많다. 힙 덤프에서 `DelayedWorkQueue.queue` 배열 크기를 본다.
- 타임아웃이 늦게 울린다: 설정한 타임아웃과 실제 끊긴 시각의 차이를 로그로 비교한다. 차이가 틱 크기 안이면 휠 해상도, 그보다 크면 타이머 스레드가 막혔는지(`jstack`에서 휠 워커 스레드가 오래 걸리는 작업을 실행 중인지)를 본다.
- 코테: "가장 이른 만료부터 처리"는 최소 힙 문제다. 같은 틱에 몰리는 이벤트를 묶어 처리하면 휠(버킷) 문제로 바뀐다.

## 장애 시나리오와 대처

### 1. 타이머 수백만 개 — 힙 비용 누적

- **현상**: 연결 수가 늘자 CPU가 타이머 스레드·스케줄러 락에서 높아지고 지연이 오른다.
- **보이는 형태**: 프로파일에서 `PriorityQueue.siftUp/siftDown`·`DelayedWorkQueue` 메서드, 또는 `PriorityQueue.remove`(선형 탐색)가 상위에 보인다. 스케줄러 락(`DelayedWorkQueue`의 `ReentrantLock`)에서 대기하는 스레드.
- **원인**: 등록·만료가 O(log n)이고 한 락으로 직렬화된다. `remove(Object)`로 취소하면 O(n)이다(3절 실험: 8만 개 전부 취소에 약 1.1~1.3초).
- **대처**: 위치 인덱스가 있는 구조(STPE + `removeOnCancel`)를 쓰거나, 대량 타임아웃은 휠로 옮긴다. Kafka도 같은 이유로 `DelayQueue`에서 계층형 휠로 갔다(블로그 벤치마크: 높은 타임아웃 구간에서 옛 구현 약 2.5만 RPS, 새 구현 약 10.5만 RPS).

### 2. 취소한 타이머가 쌓여 OOM

- **현상**: 요청량은 일정한데 힙 사용량이 타임아웃 길이만큼의 시간 동안 계속 오른다. 쌓이는 규모(대략 `초당 취소 수 × 타임아웃 길이`)가 가용 힙을 넘으면 `java.lang.OutOfMemoryError: Java heap space`.
- **보이는 형태**: `getQueue().size()`가 진행 중 요청 수보다 몇 자릿수 크다. 클래스 히스토그램 상위에 `ScheduledFutureTask`. OpenJDK 21에서는 `cancel()`이 `FutureTask.finishCompletion()`에서 `callable = null`로 만들므로, 취소된 작업 객체는 남아도 람다가 잡은 요청 객체까지 보통 붙잡지는 않는다(`decorateTask`를 재정의했다면 따로 확인).
- **원인**: 지연 취소 — 취소 표시만 하고 만료 시각까지 큐에 둔다. STPE 기본 `removeOnCancel=false`. 긴 타임아웃(1시간)일수록 오래 남는다. Kafka 옛 purgatory도 끝난 요청을 즉시 지우지 않아 OOM을 경고했다.
- **대처**: `setRemoveOnCancelPolicy(true)`. 직접 만든 지연 취소 구조는 쓰레기 비율이 임계를 넘으면 정리(purge)한다. 1절 실험으로 정책별 큐 크기를 확인한다.

### 3. 틱보다 짧은 타임아웃이 늦게 울린다

- **현상**: 50 ms로 설정한 타임아웃이 100 ms 넘어서 발생한다. "타임아웃 설정이 안 먹는다"는 보고.
- **보이는 형태**: 실제 지연이 "설정값 + 0~1틱" 범위에 퍼진다(6절 실험: 10 ms 요청 → 10~108 ms).
- **원인**: 휠은 틱 경계에서만 만료를 확인한다. Netty 기본 틱 100 ms. 리눅스 계층형 휠은 먼 만료일수록 거친 칸에 둔다(HZ=1000에서 4~32초 구간은 512 ms 단위).
- **대처**: 정밀해야 하는 타임아웃은 틱을 줄인 별도 휠이나 힙 타이머로 분리한다. SLO 계산에는 타임아웃 + 틱을 정상 시 근사로 쓰고, 휠 워커 지연을 따로 지표로 본다([reliability/07](../../reliability/07-timeout-taxonomy-by-layer/2-summary.md)).

### 4. 칸 수가 모자란 해시 휠 — O(1)이라더니 느리다

- **현상**: 휠로 바꿨는데 타이머 스레드 CPU가 오히려 높다.
- **보이는 형태**: 프로파일에서 틱 처리(버킷 순회) 메서드가 상위. 타이머 수를 늘릴수록 틱 처리 시간이 비례해 는다.
- **원인**: 해시 휠은 매 틱 그 칸에 든 타이머를 전부 훑는다. 타이머 수 / 칸 수가 크면(긴 타임아웃 + 작은 휠) 같은 타이머를 여러 번 만진다(3절 실험: 512칸 휠이 힙보다 느렸다).
- **대처**: 칸 수 × 틱이 흔한 타임아웃 범위를 덮도록 키우거나, 계층형 휠을 쓴다. 휠 인스턴스를 연결마다 만들지 않는다(스레드가 인스턴스 수만큼 생긴다).

## 핵심 문장

- 타이머는 대부분 만료 전에 취소된다. 그래서 등록·취소가 싼 구조가 이긴다.
- 타이머 힙은 정확한 순서를 지키지만 연산마다 O(log n)이고, 위치를 모르면 취소가 O(n)이다. 지연 취소는 쓰레기를 남긴다(STPE 기본 `removeOnCancel=false`).
- 타이머 휠은 시간을 틱 칸으로 나눈 링이다. 등록·취소는 O(1)이고 대가로 정밀도가 틱 단위다.
- 해시 휠의 틱 비용은 평균적으로 "타이머 수 / 칸 수"에 비례한다(한 칸에 몰리면 그 틱 하나는 O(n)). 칸이 적으면 힙보다 느려질 수 있다.
- 계층형 휠은 시·분·초 시계판처럼 범위를 넓힌다. 리눅스 4.8+는 아래 단계로 옮기지 않는 대신 먼 타이머의 정밀도를 포기했다.

## 관련 주제·근거

- 선행
  - [07-heap](../07-heap/2-summary.md) — 최소 힙(커리큘럼 ds 10).
  - [25-ring-buffer](../25-ring-buffer/2-summary.md) — 링·2의 거듭제곱 마스크.
- 후속·연결
  - [29-concurrent-data-structures](../29-concurrent-data-structures/2-summary.md) — 타이머 큐를 여러 스레드가 등록·취소할 때.
  - [reliability/05-timeouts-and-deadline-propagation](../../reliability/05-timeouts-and-deadline-propagation/2-summary.md), [reliability/07-timeout-taxonomy-by-layer](../../reliability/07-timeout-taxonomy-by-layer/2-summary.md)
  - [network/16-tcp-reliability-retransmission](../../network/16-tcp-reliability-retransmission/2-summary.md) — RTO. [network/21-tcp-keepalive-and-user-timeout](../../network/21-tcp-keepalive-and-user-timeout/2-summary.md)
  - [ops-patterns/10-scheduler](../../ops-patterns/10-scheduler/2-summary.md)
  - 커리큘럼 전체: [../curriculum.md](../curriculum.md)
- 논문·문서·소스
  - Varghese & Lauck, "Hashed and Hierarchical Timing Wheels: Data Structures for the Efficient Implementation of a Timer Facility", SOSP 1987 — 4연산 모델, Scheme 4(기본 휠)·5·6(해시 휠, n/TableSize per tick)·7(계층, 244칸 예, radix sort 유비) <https://www.cs.columbia.edu/~nahum/w6998/papers/sosp87-timing-wheels.pdf>
  - Linux `kernel/time/timer.c` 머리 주석 — 레벨·정밀도 표, cascading 제거 근거, 대부분 만료 전 취소, 최대 5일 관측; `LVL_BITS` 6·`LVL_CLK_SHIFT` 3·`LVL_DEPTH` 9(HZ>100) <https://github.com/torvalds/linux/blob/master/kernel/time/timer.c>
  - kernelnewbies Linux 4.8 — "Rework of the timer wheel which addresses the shortcomings of the current wheel (cascading, slow search for next expiring timer, etc)" <https://kernelnewbies.org/Linux_4.8> · LWN "Reinventing the timer wheel" <https://lwn.net/Articles/646950/>
  - Netty 4.1 `HashedWheelTimer.java` — 기본 틱 100 ms·512칸, 2의 거듭제곱 정규화, `remainingRounds`, 인스턴스 한도 64, `maxPendingTimeouts` <https://github.com/netty/netty/blob/4.1/common/src/main/java/io/netty/util/HashedWheelTimer.java>
  - Yasuhiro Matsuda, "Apache Kafka, Purgatory, and Hierarchical Timing Wheels", Confluent 블로그 2015-10-28 — 옛 `DelayQueue` 구현의 O(log n)·OOM, overflow wheel, 버킷 단위 `DelayQueue`, 벤치마크 <https://www.confluent.io/blog/apache-kafka-purgatory-hierarchical-timing-wheels/>
  - OpenJDK 21u 소스 — `ScheduledThreadPoolExecutor.java`(`DelayedWorkQueue`의 `heapIndex` 주석, `setRemoveOnCancelPolicy` 기본 false), `PriorityQueue.java`(O(log(n)) enqueue/dequeue, `remove(Object)` linear), `Timer.java`(이진 힙, "thousands should present no problem") <https://github.com/openjdk/jdk21u>
  - Linux `include/net/sock.h` — `struct timer_list tcp_retransmit_timer`
  - CLRS 3판 6.5(우선순위 큐)
- 실험 목록(모두 eclipse-temurin:21-jdk = OpenJDK 21.0.12, `docker run --rm --network none --cpus=2`, 2026-10-05)
  - `TimerBench.java` A — `PriorityQueue` vs 해시 휠 512칸·131072칸, N=25만·50만·100만 등록 + 전부 만료(가상 시간), 3회
  - `TimerBench.java` B — `PriorityQueue.remove(Object)` vs 휠 취소, N=1만~8만, 2회
  - 사실 점검 재실행(2026-10-05, 같은 환경): `TimerBench` A·B 1회, `CancelLeak`, `WheelLatency` 1회 — 결정값(큐 크기 100000/0, fired 수) 일치, 시간 값은 위 범위 안 또는 본문에 넓힌 범위
  - `CancelLeak.java` — STPE `removeOnCancel` false/true에서 취소 10만 개 뒤 큐 크기
  - `WheelLatency.java` — 틱 100 ms 휠 vs STPE, 10·150 ms 타임아웃 실제 지연(실시간, 각 20개)
