# data-structure/25-ring-buffer — 링 버퍼: 고정 크기 원형 버퍼, 가득 참 판정과 넘침 정책 — 정리 (힌트)

## 해결하는 문제

만드는 쪽과 쓰는 쪽의 속도는 순간마다 다르다. 그 차이를 메울 **완충 공간**이 필요하다.

```text
  생산자 ──(초당 1000개, 가끔 3000개)──>  [ 완충 ]  ──(초당 1500개)──> 소비자

  완충이 무한이면?   몰릴 때 계속 쌓인다 → 메모리 고갈(OOM)
  완충이 없으면?     몰리는 순간 생산자가 멈추거나 버린다
  완충이 고정 크기면? 메모리는 예측 가능. 대신 "가득 찼을 때 무엇을 하나"를 정해야 한다
```

- 해법: 크기가 고정된 배열을 **원처럼** 돌려 쓴다. 끝에 닿으면 0번 칸으로 되감는다.
  - *링 버퍼(ring buffer, circular buffer)*: 고정 크기 배열 + 읽는 위치 + 쓰는 위치. 위치가 배열 끝을 넘으면 앞으로 되감는다. 새 메모리를 할당하지 않는다.
    - 흔한 오해: "원형 큐와 링 버퍼는 다른 자료구조다." 같은 배열 구조다. 링 버퍼라고 부를 때는 보통 **크기 고정 + 넘침 정책**까지 포함해 말한다([04-queue-deque](../04-queue-deque/2-summary.md)의 CircularQueue는 꽉 차면 배열을 키운다).
- 이 노트의 중심 질문은 두 개다.
  1. 빈 것과 가득 찬 것을 어떻게 구분하나.
  2. 가득 찼을 때 **새것을 버리나, 옛것을 덮나, 생산자를 세우나.**

쉬운 예: 회전 초밥 레일이다.
- 접시 자리가 정해져 있다. 주방(생산자)은 빈자리에 접시를 올리고, 손님(소비자)은 앞에 온 접시를 집는다.
- 자리가 다 차면 주방은 기다리거나(블로킹), 접시를 안 올리거나(거부), 오래된 접시를 치우고 올린다(덮어쓰기).

똑같은 구조다.\
실무 예:
- 네트워크 카드(NIC)의 수신 링이 차면 패킷이 버려진다. 애플리케이션은 예외를 보지 못한다. TCP라면 보통 재전송 지연으로 드러나고, 재전송이 계속 실패하면 연결 시간 초과·중단으로 드러난다(RFC 9293 §3.8.3, [network/25](../../network/25-kernel-network-stack/2-summary.md)).
- Logback `AsyncAppender`의 큐(기본 256칸)가 차면 기본 설정(`neverBlock=false`)에서는 **요청 스레드가 로그 한 줄 때문에 멈춘다**(Logback 매뉴얼). 기본값은 큐가 80% 차면 INFO 이하를 먼저 버리므로, 멈추는 것은 주로 WARN·ERROR를 넣을 때다(장애 2).
- io_uring은 앱과 커널이 공유하는 링 두 개로 요청과 완료를 주고받는다([os/34](../../os/34-zero-copy-and-io-uring/2-summary.md)).

## 동작·원리

### 1. 모양 — 두 위치가 같은 방향으로 돈다

```text
  용량 8, 읽는 위치 head=2, 쓰는 위치 tail=6

   index:  0    1    2    3    4    5    6    7
         [  ][  ][ C ][ D ][ E ][ F ][  ][  ]
                   ^head               ^tail
         poll() → C 를 읽고 head=3         offer(G) → 6번 칸에 쓰고 tail=7

  몇 번 더 넣으면 tail 이 7 → 0 으로 되감긴다
         [ I ][  ][ C ][ D ][ E ][ F ][ G ][ H ]
               ^tail  ^head
```

- *head*: 다음에 **읽을** 칸. *tail*: 다음에 **쓸** 칸.
  - 흔한 오해: "head는 읽는 쪽이라는 이름 규칙이 정해져 있다." 이름은 문서마다 반대다. 리눅스 커널 문서(`core-api/circular-buffers.rst`)는 생산자가 넣는 위치를 head, 소비자가 꺼내는 위치를 tail이라 부른다. Java `ArrayBlockingQueue`는 `putIndex`·`takeIndex`라는 이름을 쓴다. 코드를 읽을 때는 이름 말고 **누가 그 값을 올리나**를 본다.
- 되감기: `index = (index + 1) % capacity`. OpenJDK 21 `ArrayBlockingQueue`는 나머지 연산 대신 `if (++putIndex == items.length) putIndex = 0;`으로 되감는다(소스 `enqueue`).

### 2. 빈 것과 가득 찬 것이 같은 모양이다

```text
  빈 링                    가득 찬 링(칸 4개 다 씀)
  [  ][  ][  ][  ]         [ A ][ B ][ C ][ D ]
   ^head=tail=0             ^head=tail=0          ← 둘 다 head == tail
```

- `head == tail`만으로는 둘을 구분할 수 없다. 해결법은 세 가지다.

```text
  (1) 한 칸 비우기        (2) 개수 세기            (3) 단조 증가 시퀀스
  full: (tail+1)%N==head   full: size == N          full: tail - head == N
  empty: head == tail      empty: size == 0         empty: tail == head
  실제 용량 N-1            용량 N                   용량 N, 인덱스 = seq & (N-1)
  리눅스 circ_buf          ArrayBlockingQueue(count) LMAX Disruptor, io_uring
```

- (1) 리눅스 커널 문서: "the buffer is full when the head pointer is one less than the tail pointer" — 한 칸을 일부러 비운다.
- (2) `ArrayBlockingQueue`는 `count` 필드를 따로 둔다(OpenJDK 21 소스의 `items`·`takeIndex`·`putIndex`·`count`).
- (3) 위치를 되감지 않고 정수로 계속 올린다. 배열 칸은 `seq & (N-1)`로 고른다. 차이 `tail - head`가 곧 원소 수다.
  - Disruptor는 64비트 `long` 시퀀스를 쓴다. io_uring의 `struct io_uring`은 `u32 head`·`u32 tail`에 `sq_ring_mask`·`cq_ring_mask`를 쓴다(리눅스 `include/linux/io_uring_types.h`). 부호 없는 32비트는 넘쳐도 뺄셈이 맞으므로 되감을 필요가 없다(3절 실험의 `tail - head`와 같은 원리).

#### 실험: 세 판정과 순진한 판정 (`RingFull.java`)

순진한 판정 = 가득 참 검사 없이 `head == tail`만 빈 것으로 보는 링. 칸 4개에 1..6을 넣었다.

```java
// 순진한 링: 가득 참 검사가 없다
boolean offer(int v) { a[tail] = v; tail = (tail + 1) % a.length; return true; }
boolean isEmpty()    { return head == tail; }
```

(실험, eclipse-temurin:21-jdk = OpenJDK 21.0.12, docker `--cpus=2`, 2026-10-05)

```text
== (1) naive: N=4 칸에 4개 넣기
head=0 tail=0 isEmpty()=true poll()=null
6개 넣은 뒤 poll 전부=[5, 6]  (1..6 중 남아야 할 것은?)
== (2) one-slot: 배열 칸 N=4
offer 성공=3 꺼낸 것=[1, 2, 3]
== (3) count: 배열 칸 N=4
offer 성공=4 꺼낸 것=[1, 2, 3, 4]
== (4) seq+mask: 1000만 번 넣고 빼며 감기 (N=8)
head=10000000 tail=10000000 합 일치=true
```

- 관찰
  - 순진한 링은 4개를 넣자 **빈 링이 됐다.** 6개를 넣으면 5·6이 1·2를 덮는다. 3·4는 배열에 남아 있지만 `head=0, tail=2`라 읽히지 않고, 꺼내면 `[5, 6]`뿐이다. 예외는 하나도 없다.
  - 한 칸 비우기는 칸 4개 중 3개만 쓴다. 개수 세기는 4개를 다 쓴다.
  - 시퀀스 방식은 1000만 개를 넣고 빼는 동안(칸 8개라 배열을 125만 바퀴 돈 셈) 합이 맞았다.

### 3. 2의 거듭제곱 크기와 마스크

```text
  N = 8 (2^3), mask = 7 = 0b111
  seq = 13 = 0b1101  →  13 & 0b0111 = 0b0101 = 5  (= 13 % 8)

  N = 6, mask = 5 = 0b101   ← 2의 거듭제곱이 아니면 마스크가 나머지와 다르다
  seq & 5 는 0,1,4,5 만 나온다. 2·3번 칸은 쓰이지 않는다
```

- LMAX Disruptor 논문(2011): 나머지 연산 비용을 줄이려고 링 크기를 2의 거듭제곱으로 하고 "size minus one" 마스크를 쓴다고 적는다. 리눅스 `CIRC_SPACE`·`CIRC_CNT` 매크로도 2의 거듭제곱 크기 전용이다(커널 문서 "Measuring power-of-2 buffers").
- 마스크가 빠른지는 CPU·JIT에 달려 있다. 이 노트는 속도를 재지 않았고, **정확성 차이**만 실험으로 보였다.

#### 실험: 잘못된 마스크와 정수 넘침 (`RingFull.java`, `RingBugs.java`)

(실험, OpenJDK 21.0.12, docker `--cpus=2`, 2026-10-05)

```text
== 마스크를 2의 거듭제곱이 아닌 N=6 에 쓰면 (mask=5)
seq 0..59 의 (seq & 5) 칸별 횟수=[16, 16, 0, 0, 14, 14]  (seq % 6 이면 칸마다 10)
생성자 검사: N must be power of two: 6
== int 시퀀스가 넘칠 때
seq=2147483647  seq & 7 = 7   seq % 6 = 1
seq=-2147483648  seq & 7 = 0   seq % 6 = -2
seq=-2147483647  seq & 7 = 1   seq % 6 = -1
head=2147483646 tail=-2147483647  tail-head=3 (원소 수, 2의 보수 뺄셈은 넘쳐도 맞다)
arr[tail % 6] -> Index -1 out of bounds for length 6
```

- 관찰
  - N=6에 마스크를 쓰면 칸 두 개가 놀고, 나머지 칸끼리 겹쳐 쓴다.
  - `int` 시퀀스가 넘쳐도 `& 7`과 `tail - head`는 맞다. 2의 보수 덧셈·뺄셈이 2^32를 법으로 맞기 때문이다.
  - `%`는 음수에 음수 나머지를 돌려준다(Java `%`는 피제수의 부호를 따른다). 넘친 뒤 첫 접근에서 `ArrayIndexOutOfBoundsException`이 난다.
- 그래서 시퀀스 방식은 보통 `long`을 쓴다. 초당 10억 번 올려도 2^63에 닿으려면 약 292년이 걸린다(2^63 / 10^9초 계산).

### 4. 가득 찼을 때의 정책

```text
  용량 4, 1..10 을 차례로 넣는다

  거부 (drop-newest)     [1][2][3][4]   5..10 은 들어오지 못함   → 처음 것이 남는다
  덮어쓰기 (drop-oldest) [7][8][9][10]  1..6 은 밀려남           → 최근 것이 남는다
  블로킹                 생산자가 빈칸이 날 때까지 멈춘다          → 아무것도 안 버린다, 대신 생산자가 느려진다
  타임아웃               정한 시간만 기다리고 실패를 돌려준다
```

| 정책 | 무엇을 잃나 | 어울리는 곳 | 예 |
|---|---|---|---|
| 거부 | 새 데이터 | 넘침을 상위에서 재시도·백프레셔로 처리할 수 있을 때 | NIC 수신 링(패킷 드롭 → TCP 재전송), `ArrayBlockingQueue.offer` |
| 덮어쓰기 | 옛 데이터 | "최근 N개"만 의미 있을 때 | 최근 로그·지표 보관, 블랙박스 기록 |
| 블로킹 | 생산자 시간 | 잃으면 안 되고, 생산자가 기다려도 될 때 | `ArrayBlockingQueue.put`, Logback `AsyncAppender` 기본값(WARN·ERROR 이벤트) |
| 타임아웃 | 기다린 시간 + 실패 처리 | 기다릴 상한이 있는 요청 경로 | `offer(e, timeout, unit)` |

- 정책이 없다는 것은 대개 "구현이 우연히 고른 정책"이다. 2절의 순진한 링은 아무도 고르지 않은 덮어쓰기를 했다.

#### 실험: `ArrayBlockingQueue`의 네 가지 응답 (`AbqPolicy.java`)

용량 2의 큐를 채운 뒤 세 번째 원소를 네 가지 방법으로 넣었다.

(실험, OpenJDK 21.0.12, docker `--cpus=2`, 2026-10-05)

```text
remainingCapacity=0
add(3) -> java.lang.IllegalStateException: Queue full
offer(3) -> false
offer(3, 200ms) -> false (200 ms 기다림)
300ms 뒤 producer 상태=WAITING
    at java.base/jdk.internal.misc.Unsafe.park(Native Method)
    at java.base/java.util.concurrent.locks.LockSupport.park(LockSupport.java:371)
    at java.base/java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionNode.block(AbstractQueuedSynchronizer.java:519)
    at java.base/java.util.concurrent.ForkJoinPool.unmanagedBlock(ForkJoinPool.java:3780)
    at java.base/java.util.concurrent.ForkJoinPool.managedBlock(ForkJoinPool.java:3725)
    at java.base/java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionObject.await(AbstractQueuedSynchronizer.java:1746)
    at java.base/java.util.concurrent.ArrayBlockingQueue.put(ArrayBlockingQueue.java:370)
    at AbqPolicy.lambda$main$0(AbqPolicy.java:15)
    at java.base/java.lang.Thread.run(Thread.java:1583)
put(3) 끝남
소비자 take() -> 1
take 뒤 producer 상태=TERMINATED 큐=[2, 3]
```

- 관찰
  - 같은 "가득 참"에 API마다 예외·`false`·대기·멈춤으로 다르게 답한다. 호출하는 메서드가 곧 정책 선택이다.
  - `put`에 걸린 스레드는 `WAITING`이고 스택 맨 아래 쪽에 `ArrayBlockingQueue.put`이 보인다. 운영에서 `jstack`으로 보이는 모양이 이것이다.
  - "put(3) 끝남"이 "take() -> 1"보다 먼저 찍힌 것은 두 스레드의 출력 순서가 경합하기 때문이다. 큐 상태 `[2, 3]`이 실제 순서를 보여 준다.

### 5. 동시성 — 한 명씩이면 락이 없어도 된다

```text
  단일 생산자-단일 소비자(SPSC)

  생산자만 쓰는 값: tail          소비자만 쓰는 값: head
  ┌───────────────────────────────────────────────────────┐
  │ 1. buf[tail & mask] = v                                │  생산자
  │ 2. tail = tail + 1   (release: 1번 쓰기가 먼저 보이게) │
  └───────────────────────────────────────────────────────┘
  ┌───────────────────────────────────────────────────────┐
  │ 1. t = tail          (acquire: 이 뒤 읽기가 앞서지 않게)│  소비자
  │ 2. head != t 이면 buf[head & mask] 를 읽고 head + 1     │
  └───────────────────────────────────────────────────────┘
```

- 각 위치 변수를 **한 스레드만 쓴다.** 그래서 같은 변수를 두고 CAS로 다툴 일이 없다. 필요한 것은 메모리 순서(쓴 값이 위치 갱신보다 먼저 보이기)뿐이다.
  - *release / acquire*: release 쓰기 전의 메모리 쓰기는, 그 값을 acquire로 읽은 스레드에게 보인다. Java에서는 `AtomicLong.lazySet`(release 쓰기)·`get`(volatile 읽기)으로 표현했다.
- Michael–Scott 1996 논문은 Lamport의 대기 없는(wait-free) 큐를 "단일 enqueuer와 단일 dequeuer로 동시성을 제한한" 알고리즘으로 소개한다. SPSC 링이 이 계열이다. 정의(lock-free·wait-free)는 [29-concurrent-data-structures](../29-concurrent-data-structures/2-summary.md)에서 나눈다.
- 생산자나 소비자가 둘 이상이면 이 전제가 깨진다. 같은 칸을 둘이 쓰거나 위치를 둘이 올린다. CAS나 락이 필요하다(아래 실험).
- *거짓 공유(false sharing)*: 서로 다른 변수인데 같은 캐시 라인에 있어서, 한 코어의 쓰기가 다른 코어의 캐시 라인을 무효화하는 현상이다. Disruptor 논문은 "independent, but concurrently written, variables do not share the same cache-line"이 되게 하라고 적는다. 위 실험 코드는 패딩을 하지 않았다.

#### 실험: SPSC 락 없는 링 vs `ArrayBlockingQueue` (`SpscBench.java`)

핵심 코드(박싱 없는 판):

```java
final long[] buf; final int mask;
final AtomicLong head = new AtomicLong(), tail = new AtomicLong();
boolean offer(long v) {                       // 생산자 스레드만 호출
    long t = tail.get();
    if (t - head.get() == buf.length) return false;
    buf[(int) (t & mask)] = v;
    tail.lazySet(t + 1);                      // release: 값 쓰기 뒤에 tail 공개
    return true;
}
long poll() {                                 // 소비자 스레드만 호출, 비면 Long.MIN_VALUE(실험은 0 이상만 넣으므로 구별된다)
    long h = head.get();
    if (h == tail.get()) return Long.MIN_VALUE;
    long v = buf[(int) (h & mask)];
    head.lazySet(h + 1);
    return v;
}
```

생산자 1·소비자 1, 1000만 개, 용량 1024. `ArrayBlockingQueue`는 락 하나와 조건 변수 두 개(`notEmpty`·`notFull`)를 쓴다(OpenJDK 21 소스). 박싱 영향을 떼어 보려고 `Long` 객체를 담는 락 없는 링도 함께 쟀다.

(실험, OpenJDK 21.0.12, docker `--cpus=2`, 같은 JVM에서 4라운드 × 2회 실행, 2026-10-05)

```text
n=10000000 cap=1024 availableProcessors=2
round 1: spsc-ring(long) 570 ms, spsc-ring(Long 박싱) 2134 ms, ArrayBlockingQueue<Long> 7025 ms
round 2: spsc-ring(long) 828 ms, spsc-ring(Long 박싱) 1205 ms, ArrayBlockingQueue<Long> 7259 ms
round 3: spsc-ring(long) 698 ms, spsc-ring(Long 박싱) 1370 ms, ArrayBlockingQueue<Long> 7457 ms
round 4: spsc-ring(long) 586 ms, spsc-ring(Long 박싱) 2271 ms, ArrayBlockingQueue<Long> 7213 ms
n=10000000 cap=1024 availableProcessors=2
round 1: spsc-ring(long) 909 ms, spsc-ring(Long 박싱) 1739 ms, ArrayBlockingQueue<Long> 7627 ms
round 2: spsc-ring(long) 639 ms, spsc-ring(Long 박싱) 1685 ms, ArrayBlockingQueue<Long> 8191 ms
round 3: spsc-ring(long) 512 ms, spsc-ring(Long 박싱) 2088 ms, ArrayBlockingQueue<Long> 7627 ms
round 4: spsc-ring(long) 655 ms, spsc-ring(Long 박싱) 1909 ms, ArrayBlockingQueue<Long> 7045 ms
```

- 범위: `long` 링 512~909 ms, `Long` 링 1205~2271 ms, `ArrayBlockingQueue` 7025~8191 ms.
- 사실 점검 재실행(1회 × 4라운드): `long` 링 640~822 ms, `Long` 링 1442~1763 ms, `ArrayBlockingQueue` 7006~7574 ms — 위 범위 안이고 순서도 같았다.
- 해석
  - 이 환경에서는 `Long` 링 → `ArrayBlockingQueue<Long>` 사이의 시간 차가 `long` 링 → `Long` 링(박싱) 사이의 차보다 컸다. 박싱을 같게 맞춘 두 열도 3배 이상 벌어졌다. 그 차이에는 락·조건 변수 대기와 깨우기, 바쁜 대기 vs 잠들기 등이 섞여 있고, 원인별로 나눠 재지는 않았다.
  - 수치는 CPU 2개로 제한한 컨테이너·이 크기 한정이다. 1라운드는 JIT 워밍업이 섞였고, 라운드마다 수백 ms씩 흔들렸다. 논문 수치(Disruptor 논문 표 2: 1P-1C에서 ArrayBlockingQueue 약 534만 ops/s, Disruptor 약 2600만 ops/s, Nehalem)와 직접 비교하지 않는다.
  - 락 없는 링은 소비자가 바쁜 대기(`Thread.onSpinWait`)를 한다. 데이터가 없을 때도 CPU를 쓴다. 처리량 대신 CPU를 내준 것이다.

#### 실험: SPSC 링을 생산자 둘이 쓰면 (`RingBugs.java`)

같은 `SpscRing`에 생산자 2개가 100만 개씩 넣었다. 소비자는 생산이 끝난 뒤 1초 더 읽고 멈춘다.

(실험, OpenJDK 21.0.12, docker `--cpus=2`, 2026-10-05)

```text
run1 생산자 2개 x 1000000: 소비 개수=983494 (기대 2000000), 합 차이=-509498226594, 끝난 뒤 head=983494 tail=983494
run2 생산자 2개 x 1000000: 소비 개수=1139449 (기대 2000000), 합 차이=-416464974618, 끝난 뒤 head=1139449 tail=1139449
run3 생산자 2개 x 1000000: 소비 개수=1018530 (기대 2000000), 합 차이=-486659664542, 끝난 뒤 head=1018530 tail=1018530
```

- 사실 점검 재실행(같은 코드, 같은 환경, 3회): 소비 개수 968988·990139·975981. 끝난 뒤 `head == tail`도 같았다.
- 관찰: 절반 가까이(실행마다 다름, 6회 범위 43~52%)가 **예외 없이 사라졌다.** 두 생산자가 같은 `tail`을 읽고 같은 칸에 쓴 뒤 같은 값으로 `tail`을 올리면 한 개가 덮인다. 끝난 뒤 `head == tail`이라 링은 "정상적으로 비어 있는" 모습이다.

## 쓰이는 자료구조·알고리즘

- 이 주제가 쓰는 하위 구조
  - 배열 — 고정 크기 연속 메모리([01-dynamic-array](../01-dynamic-array/2-summary.md)와 달리 키우지 않는다).
  - 원형 큐의 되감기([04-queue-deque](../04-queue-deque/2-summary.md)) — 선행. 이 노트는 그 위에 "크기 고정 + 넘침 정책 + 동시성"을 얹는다.
  - 비트 마스크(2의 거듭제곱), 단조 증가 시퀀스, 메모리 순서(release/acquire), 조건 변수([os/17](../../os/17-condition-variables-and-monitors/2-summary.md)).
- 이 주제를 쓰는 곳(🔧)
  - **NIC DMA 링** — 드라이버가 디스크립터 칸을 원형으로 돌려 쓴다. 크기는 `ethtool -g`로 본다([network/25](../../network/25-kernel-network-stack/2-summary.md)).
  - **io_uring** — 제출 큐(SQ)·완료 큐(CQ) 두 링을 앱과 커널이 공유한다([os/34](../../os/34-zero-copy-and-io-uring/2-summary.md)).
  - **LMAX Disruptor** — 시퀀스 + 2의 거듭제곱 링 + 캐시 라인 패딩으로 스레드 간 교환을 한다(2011 논문).
  - **로그 버퍼** — Logback `AsyncAppender`는 BlockingQueue에 로그 이벤트를 모은다(매뉴얼). 넘침 정책이 설정값이다(장애 2).
  - **TCP 송수신 버퍼** — 커리큘럼 🔧 칸 항목. TCP는 바이트 번호(시퀀스)가 올라가는 창으로 버퍼를 관리한다는 점에서 3절의 "단조 증가 시퀀스" 모양과 닮았다. 리눅스 구현이 실제 원형 배열인지는 이 노트에서 확인하지 않았다 [?] ([network/17](../../network/17-tcp-flow-control/2-summary.md)).
  - Java `ArrayDeque`·`ArrayBlockingQueue`, `ForkJoinPool`의 작업 훔치기 큐(소스 주석: Chase–Lev 2005 "Dynamic Circular Work-Stealing Deque"와 "roughly similar"한 설계라고 적는다).
  - PostgreSQL 대량 스캔용 버퍼 링([database/07-buffer-pool](../../database/07-buffer-pool/2-summary.md)).
  - 타이머 휠 — 버킷을 원형으로 놓은 링이다([26-timer-structures](../26-timer-structures/2-summary.md)).
  - 배칭 flush — 크기·시간 트리거로 버퍼를 비운다([reliability/40](../../reliability/40-batching-and-round-trips/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 정책을 먼저 정한다

```text
  잃어도 되나? ── 아니오 ──> 생산자가 기다려도 되나? ── 예 ──> 블로킹(put) + 대기 시간 지표
       │                           └─ 아니오 ──> 타임아웃(offer(e,t,u)) + 실패를 호출자에게
       예
       └─ 무엇이 더 중요한가? ── 최근 것 ──> 덮어쓰기 + 덮어쓴 수 지표
                               └─ 먼저 온 것 ──> 거부(offer) + 거부 수 지표
```

- 어느 쪽이든 **버린 수·기다린 시간을 지표로 내보낸다.** 이 노트의 실험과 장애 1·4의 공통 모양이 "버려졌는데 아무도 몰랐다"이다.
- 크기: 평균 속도 차이가 아니라 **몰리는 구간의 길이**로 정한다. 소비가 평균적으로 생산보다 느리면 크기를 키워도 언젠가는 찬다. 그때는 백프레셔·부하 차단이 답이다([reliability/12](../../reliability/12-backpressure-and-load-shedding/2-summary.md)).

### 2. "최근 N개" 덮어쓰기 링 (Java 21)

```java
/** 최근 N개 이벤트만 보관. 단일 스레드 전용(동시 사용은 synchronized 로 감싼다). */
final class RecentEvents<T> {
    private final Object[] buf;
    private final int mask;
    private long head, tail;          // 단조 증가. 인덱스 = seq & mask
    private long overwritten;         // 지표로 내보낸다

    RecentEvents(int capacity) {
        if (capacity <= 0 || Integer.bitCount(capacity) != 1) throw new IllegalArgumentException("power of two: " + capacity);
        buf = new Object[capacity]; mask = capacity - 1;
    }
    void add(T e) {
        if (tail - head == buf.length) { head++; overwritten++; }   // 가득 참 → 가장 오래된 것 버림
        buf[(int) (tail & mask)] = e;
        tail++;
    }
    @SuppressWarnings("unchecked")
    java.util.List<T> snapshot() {
        var out = new java.util.ArrayList<T>((int) (tail - head));
        for (long s = head; s < tail; s++) out.add((T) buf[(int) (s & mask)]);
        return out;
    }
    long overwritten() { return overwritten; }
}
```

- 1절 실험의 `SeqRing.put`과 같은 방식이다. 용량 4에 1..10을 넣으면 `[7, 8, 9, 10]`, 덮어쓴 수 6(실험 출력).

### 3. 생산자-소비자 경계에는 기존 큐를 쓴다

- 직접 만든 락 없는 링은 SPSC 전제를 코드로 강제하기 어렵다(위 실험: 생산자를 하나 더 붙이면 조용히 반이 사라졌다).
- JDK 안에서는 `ArrayBlockingQueue`(고정 크기, 락 1개)부터 쓴다. 처리량이 실제로 병목인지 프로파일로 확인한 뒤에 Disruptor 같은 라이브러리를 검토한다.
- 넣는 쪽 코드에서 정책이 드러나게 쓴다.

```java
if (!queue.offer(event)) {          // 거부 정책: 이 줄이 곧 설계 결정
    droppedCounter.increment();     // 지표 없이 버리면 장애 1이 된다
}
```

### 4. 진단

- 자바 생산자가 멈췄다: `jstack <pid>` 또는 `jcmd <pid> Thread.print`에서 `WAITING` 상태이고 스택에 `ArrayBlockingQueue.put`·`ConditionObject.await`가 있는 스레드를 찾는다(4절 실험의 스택 모양). 같은 큐의 소비자 스레드가 무엇을 하는지 이어서 본다.
- NIC 링: `ip -s link`, `ethtool -S <dev>`의 드롭 계열 카운터, `ethtool -g <dev>`로 링 크기. 카운터 이름과 의미는 드라이버마다 다르다([network/25](../../network/25-kernel-network-stack/2-summary.md)의 `rx_dropped`·`rx_missed_errors` 구분 참고).
- 코테: "원형 큐 설계"(LeetCode 622 Design Circular Queue 등)는 2절의 개수 세기 방식이 가장 실수가 적다.

## 장애 시나리오와 대처

### 1. 조용한 드롭 — 버렸는데 아무도 모른다

- **현상**: 간헐적으로 지연이 튀거나 데이터 일부가 빈다. 애플리케이션 로그에는 오류가 없다.
- **보이는 형태**
  - 네트워크: `ip -s link`·`/proc/net/dev`의 drop 칸, `ethtool -S`의 드라이버 카운터가 오른다. 앱에서는 주로 TCP 재전송으로 인한 지연이 보이고, 드롭이 계속되면 연결 시간 초과까지 간다.
  - 앱 내부 링: 지표가 없으면 아무것도 안 보인다. 실험의 SPSC 오용처럼 끝난 뒤 `head == tail`인 정상 모습만 남는다.
- **원인**: 가득 찼을 때 거부·덮어쓰기 정책이 동작했다. 또는 정책을 정하지 않아 구현이 우연히 덮어썼다(2절 순진한 링).
- **대처**: 드롭·덮어쓰기 카운터를 지표로 내보내고 경보를 건다. NIC는 링 크기 조정(`ethtool -G`, 드라이버에 따라 인터페이스가 재시작될 수 있다 — network/25)과 수신 처리 분산(RSS·RPS)을 본다. 앱은 소비 속도·배치 크기·백프레셔를 본다.

### 2. 생산자 블로킹 전파 — 로그 한 줄이 요청을 멈춘다

- **현상**: 디스크·로그 수집기가 느려지자 API 지연이 함께 오른다. CPU는 낮다.
- **보이는 형태**: 스레드 덤프에 요청 스레드 다수가 `WAITING`, 스택에 `ArrayBlockingQueue.put` 계열이 있다. 4절 실험과 같은 모양이다.
- **원인**: 블로킹 정책의 링이 가득 찼다. Logback `AsyncAppender`는 기본 `neverBlock=false`라서 큐가 차면 "block on appending to a full queue rather than losing the message"(매뉴얼). 기본 `queueSize`는 256이고, 남은 칸이 20% 이하가 되면 TRACE·DEBUG·INFO를 버리고 WARN·ERROR만 넣는다(`discardingThreshold` 기본값).
- **대처**: 요청 경로에 있는 버퍼는 블로킹 대신 타임아웃·거부를 검토한다(`neverBlock=true` + 드롭 지표). 반대로 감사 로그처럼 잃으면 안 되는 것은 블로킹을 유지하고, 별도 경로로 분리한다.

### 3. 빈/가득 판정·인덱스 버그 — 링 전체가 사라진다

- **현상**: 테스트에서는 되는데 운영에서 버퍼 내용이 통째로 비거나, 오래 돌던 프로세스가 갑자기 `ArrayIndexOutOfBoundsException`을 낸다.
- **보이는 형태**: 2절 실험처럼 4개를 넣었는데 `isEmpty()=true`. 또는 `Index -1 out of bounds for length 6`.
- **원인**
  - 가득 참 검사 없이 `head == tail`만 빈 것으로 판정했다.
  - 2의 거듭제곱이 아닌 크기에 마스크를 썼다(칸 일부만 쓰이고 겹쳐 쓴다).
  - `int` 시퀀스에 `%`를 썼다가 2^31에서 음수가 됐다.
- **대처**: 세 판정 방식 중 하나를 고르고, 생성자에서 크기를 검사한다. 시퀀스는 `long`. 경계 테스트에 "정확히 가득 참", "되감기 직후", "시퀀스 넘침 직전 값에서 시작"을 넣는다.

### 4. head/tail 경합 — SPSC 링을 여럿이 쓴다

- **현상**: 처리량 수치는 정상인데 결과 개수가 모자라거나 같은 값이 두 번 나온다.
- **보이는 형태**: 예외 없음. 소비 개수 < 생산 개수(5절 실험: 200만 중 97만~114만, 6회).
- **원인**: SPSC 링은 "각 위치를 한 스레드만 쓴다"는 전제로 락을 뺐다. 생산자가 둘이면 같은 `tail`을 읽고 같은 칸에 쓴다. 또 성능 쪽으로는, 패딩 없이 head와 tail이 같은 캐시 라인에 있으면 거짓 공유로 느려진다(Disruptor 논문).
- **대처**: 다중 생산자면 MPMC 구현(락 기반 `ArrayBlockingQueue`, 또는 CAS로 칸을 예약하는 구현)을 쓴다. 생산자 수 전제를 클래스 이름·문서·assert(소유 스레드 검사)로 드러낸다. 직접 만든 링은 동시성 스트레스 테스트로 개수·합을 대조한다.

## 핵심 문장

- 링 버퍼는 고정 크기 배열을 원처럼 돌려 쓴다. 메모리는 예측 가능하지만, 가득 찼을 때 무엇을 할지(거부·덮어쓰기·블로킹·타임아웃)를 정해야 한다.
- `head == tail`만으로는 빈 것과 가득 찬 것을 못 가른다. 한 칸 비우기, 개수 세기, 단조 증가 시퀀스 중 하나를 쓴다.
- 마스크(`seq & (N-1)`)는 N이 2의 거듭제곱이고 seq가 0 이상일 때 나머지(`seq % N`)와 같다. 시퀀스는 `long`으로 두면 넘침을 사실상 걱정하지 않는다.
- 생산자·소비자가 각각 하나면 위치 변수마다 쓰는 스레드가 하나라서 락 없이 메모리 순서만으로 동작한다. 그 전제가 깨지면 데이터가 조용히 사라진다.
- 링 버퍼의 드롭·덮어쓰기는 예외 없이 일어날 수 있다. 버린 수와 기다린 시간을 지표로 내보내야 보인다.

## 관련 주제·근거

- 선행
  - [04-queue-deque](../04-queue-deque/2-summary.md) — 원형 큐(CircularQueue)·`ArrayDeque`의 되감기(커리큘럼 ds 06).
- 후속·연결
  - [26-timer-structures](../26-timer-structures/2-summary.md) — 타이머 휠은 버킷의 링이다.
  - [29-concurrent-data-structures](../29-concurrent-data-structures/2-summary.md) — lock-free·wait-free 정의, ABA, 다중 생산자 큐.
  - [network/25-kernel-network-stack](../../network/25-kernel-network-stack/2-summary.md) — NIC 링, 드롭 카운터. [network/17-tcp-flow-control](../../network/17-tcp-flow-control/2-summary.md)
  - [os/34-zero-copy-and-io-uring](../../os/34-zero-copy-and-io-uring/2-summary.md) — SQ·CQ 링. [os/17-condition-variables-and-monitors](../../os/17-condition-variables-and-monitors/2-summary.md) — 유한 버퍼 생산자/소비자.
  - [reliability/12-backpressure-and-load-shedding](../../reliability/12-backpressure-and-load-shedding/2-summary.md), [reliability/40-batching-and-round-trips](../../reliability/40-batching-and-round-trips/2-summary.md), [ops-patterns/05-backpressure](../../ops-patterns/05-backpressure/2-summary.md)
  - [database/07-buffer-pool](../../database/07-buffer-pool/2-summary.md) — clock sweep·버퍼 링.
  - 커리큘럼 전체: [../curriculum.md](../curriculum.md)
- 문서·논문·소스
  - Thompson 외, "LMAX Disruptor: High performance alternative to bounded queues for exchanging data between concurrent threads", 2011-05 — 2의 거듭제곱 크기와 마스크, false sharing, 단일 작성자 원칙, 큐의 head·tail·size 쓰기 경합, 표 2 처리량 <https://lmax-exchange.github.io/disruptor/disruptor.html>
  - Linux 커널 문서 "Circular Buffers"(`Documentation/core-api/circular-buffers.rst`) — head = 생산자 위치, 한 칸 비우기 판정, `CIRC_SPACE`·`CIRC_CNT`, 2의 거듭제곱 <https://www.kernel.org/doc/html/latest/core-api/circular-buffers.html>
  - Michael & Scott, "Simple, Fast, and Practical Non-Blocking and Blocking Concurrent Queue Algorithms", PODC 1996 — Lamport의 단일 enqueuer·dequeuer wait-free 큐 언급 <https://www.cs.rochester.edu/~scott/papers/1996_PODC_queues.pdf>
  - OpenJDK 21u 소스 `java/util/concurrent/ArrayBlockingQueue.java`(`items`·`takeIndex`·`putIndex`·`count`, `ReentrantLock` + `notEmpty`·`notFull`, `if (++putIndex == items.length) putIndex = 0`), `ForkJoinPool.java`(Chase–Lev 주석) <https://github.com/openjdk/jdk21u>
  - Logback 매뉴얼 "AsyncAppender" — `queueSize` 256, `discardingThreshold`(남은 20%에서 TRACE·DEBUG·INFO 드롭), `neverBlock` 기본 false <https://logback.qos.ch/manual/appenders-async-sift.html>
  - CLRS 3판 10.1(배열로 만든 큐의 되감기)
- 실험 목록(모두 eclipse-temurin:21-jdk = OpenJDK 21.0.12, `docker run --rm --network none --cpus=2`, 2026-10-05)
  - `RingFull.java` — 순진한 판정·한 칸 비우기·개수 세기·시퀀스 + 마스크, N=6 마스크 칸 분포, 거부 vs 덮어쓰기
  - `AbqPolicy.java` — `ArrayBlockingQueue`의 `add`·`offer`·`offer(timeout)`·`put`과 블로킹 스레드 스택
  - `SpscBench.java` — SPSC 링(`long`·`Long`) vs `ArrayBlockingQueue`, 1000만 개, 4라운드 × 2회
  - `RingBugs.java` — SPSC 링에 생산자 2개(유실 3회), `int` 시퀀스 넘침과 `%`·`&`
