# java/syntax/56 — 가상 스레드 (21): 쓰는 법과 막히는 자리 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러·수치는 Temurin **21.0.5** 와 **25.0.1** 에서 실제로 돌려 얻은 것이다.\
> ★ **고정(pinning) 실험은 두 버전에서 각각 돌렸고 결과가 갈렸다** — 7·8·9번.
> ⚠️ **측정 조건** — **JMH 가 아니다.** 벽시계이고 **워밍업 1\~2 + 측정 3\~5회의 중앙값**이다(문항마다 적었다).\
> 머신 **24코어**(Linux x86-64), `ulimit -n` = 1,048,576.\
> 고정 실험은 캐리어를 **1개로 묶어**(`-Djdk.virtualThreadScheduler.parallelism=1 -Djdk.virtualThreadScheduler.maxPoolSize=1`)\
> **"줄서면 1600ms / 안 줄서면 200ms"** 로 **두 자리가 갈리게** 설계했다 — 그래서 이 실험만은 흔들림이 결론을 안 흔든다.\
> 다른 실험은 흔들린다 — 소켓 실험이 **183\~326 ms**(1.8배)였다. **자릿수만** 읽는다.\
> 힙 수치는 `System.gc()` 두 번 뒤 `totalMemory - freeMemory` — **자릿수용**이다.
> `@since` 와 프리뷰 상태는 `lib/src.zip` 의 애너테이션을 **직접 읽어** 확인했다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 만드는 법 셋과 그 차이

**출력** (`Ex.java` — 56-a, JDK 21.0.5)

```text
--- 1. 만드는 법 셋
  Thread.ofVirtual().unstarted(..)  : isVirtual=true 상태=NEW 이름="직접-만든-것"
  Thread.startVirtualThread(..)     : isVirtual=true 이름="" (기본 이름은 빈 문자열)
  newVirtualThreadPerTaskExecutor   : true / VirtualThread[#31]/runnable@ForkJoinPool-1-worker-1
```

**왜 그런가**

- **셋 다 `@since 21`** 이다. `src.zip` 에서 직접 읽었다.

```text
853-     * @since 21
855:    public static Builder.OfVirtual ofVirtual() {
1491-     * @since 21
1493:    public static Thread startVirtualThread(Runnable task) {
266-     * @since 21
268:    public static ExecutorService newVirtualThreadPerTaskExecutor() {
```

- **`startVirtualThread` 로 만든 스레드의 이름은 빈 문자열 `""`** 이다.\
  빌더로 `name(..)` 을 주면 그 이름이 붙는다(`"직접-만든-것"`).
- **`toString()` 이 구조를 그대로 보여 준다.**

```text
  VirtualThread[#31]/runnable@ForkJoinPool-1-worker-1
  ^^^^^^^^^^^^^^^^^^ ^^^^^^^^ ^^^^^^^^^^^^^^^^^^^^^^
     가상 스레드 + id    상태     지금 올라가 있는 캐리어
```

- **JDK 17 에서는 컴파일 에러**다.

```text
=== JDK 17 컴파일
a/Ex.java:7: error: cannot find symbol
        Thread t1 = Thread.ofVirtual().name("직접-만든-것").unstarted(() -> { });
                          ^
  symbol:   method ofVirtual()
  location: class Thread
a/Ex.java:8: error: cannot find symbol
        System.out.println("  Thread.ofVirtual().unstarted(..)  : isVirtual=" + t1.isVirtual() + " 상태=" + t1.getState() + " 이름=\"" + t1.getName() + "\"");
                                                                                  ^
  symbol:   method isVirtual()
  location: variable t1 of type Thread
```

### 2. 플랫폼 스레드와 무엇이 다른가

**출력** (`Ex.java` — 56-a, JDK 21.0.5)

```text
--- 2. 플랫폼 스레드와 무엇이 다른가
                     isVirtual isDaemon  priority   threadGroup
  가상 스레드             true      true      5          VirtualThreads
  플랫폼 스레드            false     false     5          main
  가상 스레드에 setDaemon(false) : java.lang.IllegalArgumentException: 'false' not legal for virtual threads
  가상 스레드에 setDaemon(true)  : 예외 없음(원래 데몬)
  setPriority(10) 뒤 priority   : 5   <- 무시된다
--- 3. 가상 스레드는 데몬이다 — main 이 끝나면 JVM 이 기다려 주지 않는다
  3초짜리 가상 스레드를 띄우고 main 을 끝낸다
```

**왜 그런가**

- **`isDaemon()` 의 기본값은 `true`** 다. 플랫폼 스레드는 `false` 다.
- **`setDaemon(false)` 는 예외다** — `IllegalArgumentException: 'false' not legal for virtual threads`.\
  `setDaemon(true)` 는 아무 일도 안 하고 통과한다.
- **`setPriority(10)` 은 조용히 무시된다.** 값은 `5` 그대로이고 **예외도 안 난다.**
- **`getThreadGroup().getName()` 은 `VirtualThreads`** 다.
- **`main` 이 끝나면 JVM 이 기다려 주지 않는다.** 실측에서 3초짜리 가상 스레드의 출력이 **안 찍혔다.**\
  `join()` 하거나 `ExecutorService.close()` 로 감싼다.

### 3. 캐리어 스레드는 몇 개인가

**출력** (`Ex.java` — 56-a, CPU 만 쓰는 작업 2,000개, JDK 21.0.5)

```text
--- 4. 캐리어(carrier) 스레드는 몇 개인가
  availableProcessors            : 24
  CPU 만 쓰는 작업 2000개가 쓴 캐리어 수 : 24
  캐리어 이름 예 : [ForkJoinPool-1-worker-1, ForkJoinPool-1-worker-10, ForkJoinPool-1-worker-11]
```

**왜 그런가**

- **캐리어는 24개** — `availableProcessors` 와 같다. 작업이 2,000개여도 캐리어는 코어 수만큼이다.
- 이름은 **`ForkJoinPool-1-worker-N`** 이다.
- ★ **공용 풀과 다르다.** 공용 ForkJoinPool 의 워커는 **`ForkJoinPool.commonPool-worker-N`** 이다\
  ([`../49-parallel-streams/`](../49-parallel-streams/) 의 실측 출력 참조). **이름이 다르므로 다른 풀이다.**
- 그래서 병렬 스트림이 공용 풀을 막아도 가상 스레드는 그 영향을 직접 받지 않는다\
  (물론 **CPU 는 나눠 쓴다**).

### 4. 몇 개까지 만들 수 있나

**출력** (`Ex.java` — 56-b, `-Xmx2g`, 각 1회, JDK 21.0.5)

```text
===== virtual 10000
  virtual 스레드 10,000개 생성 성공 — 37 ms
  동시에 sleep(2000) 중이던 개수 : 10,000
===== platform 10000
  platform 스레드 10,000개 생성 성공 — 1291 ms
  동시에 sleep(2000) 중이던 개수 : 10,000
===== virtual 1000000
  virtual 스레드 1,000,000개 생성 성공 — 604 ms
  동시에 sleep(2000) 중이던 개수 : 1,000,000
===== platform 100000
  platform 스레드 100,000개 생성 성공 — 47973 ms
  동시에 sleep(2000) 중이던 개수 : 100,000
```

**`ulimit -u 6000` 을 건 뒤**

```text
=== ulimit -u 6000 로 제한한 뒤
[0.344s][warning][os,thread] Failed to start thread "Unknown thread" - pthread_create failed (EAGAIN) for attributes: stacksize: 1024k, guardsize: 0k, detached.
[0.344s][warning][os,thread] Failed to start the native thread for java.lang.Thread "Thread-3749"
  platform 스레드 100,000개 만들다 3,749개에서 터졌다 (312 ms)
  java.lang.OutOfMemoryError: unable to create native thread: possibly out of memory or process/resource limits reached
--- 같은 제한에서 가상 스레드
  virtual 스레드 100,000개 생성 성공 — 115 ms
```

**왜 그런가**

- **가상 스레드 100만 개: 604 ms.** 자릿수로 **수백 ms**.
- **플랫폼 스레드 10만 개: 47,973 ms.** 자릿수로 **수만 ms** — **80배**다.
- **제한을 걸면 플랫폼 스레드는 3,749개에서 죽는다.**\
  `pthread_create failed (EAGAIN)` → `OutOfMemoryError: unable to create native thread: possibly out of memory or process/resource limits reached`.\
  경고 줄에 **`stacksize: 1024k`** 가 찍힌다 — 스레드 하나가 예약하는 스택 크기다.
- **같은 제한에서 가상 스레드 10만 개는 115 ms 에 성공**한다.\
  OS 에게는 **캐리어 24개만** 보이기 때문이다.

### 5. ★ 언제 값이 나나

**출력** (`Ex.java` — 56-c, 작업 1만 개, 워밍업 2 + 측정 5의 중앙값, JMH 아님, JDK 21.0.5)

```text
--- 블로킹 작업 10,000개 (각 sleep 10ms) / 워밍업 2 + 측정 5의 중앙값
  플랫폼 고정 풀 16                        중앙값   6317 ms  (최소 6308, 최대 6322)
  플랫폼 고정 풀 200                       중앙값    521 ms  (최소 519, 최대 527)
  플랫폼 고정 풀 2000                      중앙값    269 ms  (최소 237, 최대 273)
  가상 스레드 (작업당 하나)                    중앙값     22 ms  (최소 20, 최대 25)
  이상적 하한 = 10ms (전부 동시에 자면)
--- CPU 만 쓰는 작업 10,000개 / 워밍업 2 + 측정 5의 중앙값
  플랫폼 고정 풀 24(=코어 수)                 중앙값     97 ms  (최소 85, 최대 102)
  플랫폼 고정 풀 200                       중앙값    123 ms  (최소 116, 최대 131)
  가상 스레드 (작업당 하나)                    중앙값     88 ms  (최소 86, 최대 97)
```

**왜 그런가**

- **블로킹 순위** — 가상(22) < 풀 2000(269) < 풀 200(521) < 풀 16(6,317).\
  자릿수로 **10² / 10² / 10² / 10³** 이고, 가상만 **10¹** 이다.\
  하한이 10 ms 이므로 **가상 스레드가 하한에 가장 가깝다.**
- **CPU 작업에서는 가상 스레드가 안 이긴다** — 88 대 97 ms 는 **같은 자릿수**다.\
  오히려 풀 200 이 **123 ms 로 가장 느렸다**(코어보다 스레드가 많으면 손해).
- **차이가 안 나는 이유** — 계산은 **코어 24개** 위에서만 돌 수 있다.\
  블로킹은 "기다리는 시간"이라 스레드를 늘리면 겹칠 수 있지만, 계산은 겹칠 수 없다.
- **진짜 소켓으로 재면 덜 극적이다.**

```text
--- 진짜 소켓 I/O 3,000건 (서버가 50ms 뒤에 응답) / 워밍업 1 + 측정 3의 중앙값
  플랫폼 고정 풀 50        3회 [3046, 3044, 3044] → 중앙값 3044 ms
  플랫폼 고정 풀 500       3회 [366, 368, 363] → 중앙값 366 ms
  가상 스레드             3회 [183, 315, 326] → 중앙값 315 ms
  이상적 하한 = 50ms
```

- 풀 50 대비 **9.7배**지만 **풀 500 과는 거의 차이가 없다**(366 대 315 ms).\
  이 실험에서는 **연결 수립과 서버 쪽이 병목**이라 클라이언트 스레드 모델을 바꿔도 더 못 줄인다.\
  **흔들림도 크다**(183\~326 ms).
- ★ **결론** — 가상 스레드의 이득은 **"내 스레드가 병목일 때"** 나온다.

### 6. 가상 스레드를 풀링해도 되나

**출력** (`Ex.java` — 56-h, 워밍업 2 + 측정 5의 중앙값, JDK 21.0.5)

```text
--- 3. 가상 스레드를 '풀링' 하면 무슨 일이 나나
  작업 10,000개가 쓴 서로 다른 가상 스레드 수 : 10000  (작업마다 새로 만든다)
--- 4. 만드는 비용 — 10만 번 (워밍업 2 + 측정 5의 중앙값)
  가상 스레드 start+join   : 중앙값 450 ms (최소 374, 최대 502)
  플랫폼 스레드 start+join : 중앙값 9939 ms (최소 9743, 최대 10114)
  고정 풀 1 에 submit+get  : 중앙값 745 ms (최소 606, 최대 877)
```

**왜 그런가**

- **작업 1만 개에 가상 스레드 1만 개.** `newVirtualThreadPerTaskExecutor` 는 **재활용하지 않는다.**
- **가상 450 ms 대 플랫폼 9,939 ms — 22배**다.
- ★ **고정 풀 1에 `submit`+`get` 하는 것(745 ms)보다 가상 스레드를 새로 만드는 게 싸다**(450 ms).\
  즉 **풀링이 이득이 아니다.** 풀링의 존재 이유(생성 비용 절약)가 사라졌다.
- 게다가 풀에 넣으면 **풀 크기가 동시성 상한**이 되어 **가상 스레드를 쓰는 이유 자체가 사라진다.**
- **동시성 제한이 필요하면 `Semaphore`** 를 쓴다.

```java
Semaphore db = new Semaphore(20);
try (ExecutorService es = Executors.newVirtualThreadPerTaskExecutor()) {
    for (var req : requests) es.submit(() -> {
        db.acquire();
        try { query(req); } finally { db.release(); }
    });
}
```

- 풀은 "재활용"과 "제한"을 겸하는데, 가상 스레드에는 **제한만** 필요하다.

### 7. ★★ `synchronized` 안에서 블로킹하면

**출력** (`Ex.java` — 56-e, 각 5회, 캐리어 1개, 가상 스레드 8개가 각자 다른 락으로 200ms 씩 잔다)

```text
===== JDK 21.0.5
  캐리어 병렬도 설정 : parallelism=1 maxPoolSize=1
  가상 스레드 8개가 각자 200ms 잔다 (서로 다른 락 — 경합은 없다)
  이상적 하한 200ms, 하나씩 줄서면 1600ms
  plain          5회: [211, 200, 200, 200, 200] → 중앙값 200 ms
  synchronized   5회: [1602, 1601, 1601, 1601, 1601] → 중앙값 1601 ms
  ReentrantLock  5회: [200, 200, 200, 200, 200] → 중앙값 200 ms
===== JDK 25.0.1
  캐리어 병렬도 설정 : parallelism=1 maxPoolSize=1
  가상 스레드 8개가 각자 200ms 잔다 (서로 다른 락 — 경합은 없다)
  이상적 하한 200ms, 하나씩 줄서면 1600ms
  plain          5회: [215, 200, 200, 200, 200] → 중앙값 200 ms
  synchronized   5회: [200, 200, 200, 200, 200] → 중앙값 200 ms
  ReentrantLock  5회: [200, 200, 200, 200, 200] → 중앙값 200 ms
```

**왜 그런가**

| | JDK 21 | JDK 25 |
|---|---|---|
| (A) 그냥 `sleep` | **200 ms** | **200 ms** |
| (B) `synchronized` 안에서 `sleep` | **1,601 ms** | **200 ms** |
| (C) `ReentrantLock` 안에서 `sleep` | **200 ms** | **200 ms** |

- **하한은 200 ms**(전부 동시에 자면), **하나씩 줄서면 1,600 ms**(8 × 200).\
  21 의 `synchronized` 가 **정확히 1,601 ms** — **완전히 줄섰다.**
- **락 경합은 없다.** 8개가 **각자 다른 락**을 쓴다. 느려진 원인은 **고정(pinning)** 뿐이다.
- **21 과 25 를 가른 것은 [JEP 491](https://openjdk.org/jeps/491)**(JDK 24) 이다 —\
  모니터를 캐리어가 아니라 가상 스레드에 귀속시켜 **`synchronized` 고정을 없앴다.**
- **JDK 21 에서의 처방은 `ReentrantLock`** 이다. 21 에서도 200 ms 로 나온다.
- **흔들림이 거의 없다**(1601\~1605, 200\~215). 이 결론은 흔들리지 않는다.

```text
JDK 21                                     JDK 25

  plain          200 ms                     plain          200 ms
  synchronized  1601 ms  <- 8배, 줄섰다      synchronized   200 ms  <- 안 줄섰다
  ReentrantLock  200 ms                     ReentrantLock  200 ms
```

**21 에서 더 넓게 재 본 것** (`Ex.java` — 56-f, 각 5회)

```text
===== 21
  synchronized+sleep       5회 [1612, 1602, 1601, 1601, 1601] → 중앙값 1601 ms
  Object.wait              5회 [1602, 1602, 1602, 1602, 1602] → 중앙값 1602 ms
  동기화 블록 안에서 I/O           5회 [1621, 1602, 1601, 1601, 1602] → 중앙값 1602 ms
  native 프레임 아래 sleep      5회 [206, 201, 200, 200, 200] → 중앙값 200 ms
===== 25
  synchronized+sleep       5회 [213, 200, 200, 200, 200] → 중앙값 200 ms
  Object.wait              5회 [202, 200, 200, 200, 200] → 중앙값 200 ms
  동기화 블록 안에서 I/O           5회 [220, 201, 200, 200, 200] → 중앙값 200 ms
  native 프레임 아래 sleep      5회 [210, 201, 200, 200, 200] → 중앙값 200 ms
```

- **21 에서는 `synchronized`·`Object.wait`·그 안의 I/O 가 전부 고정**된다.
- **25 에서는 넷 다 200 ms** 다.

### 8. 25 에서도 고정되는 것이 있나

**출력** (`Ex.java` — 56-g, 클래스 초기화 블록 안에서 `sleep(200)`, 가상 스레드 4개, 캐리어 1개)

```text
=== 21
  parallelism=1  (하한 200ms / 줄서면 800ms)
VirtualThread[#28]/runnable@ForkJoinPool-1-worker-1 reason:NATIVE
    Ex$C0.<clinit>(Ex.java:7)
VirtualThread[#30]/runnable@ForkJoinPool-1-worker-1 reason:NATIVE
    Ex$C1.<clinit>(Ex.java:8)
VirtualThread[#31]/runnable@ForkJoinPool-1-worker-1 reason:NATIVE
    Ex$C2.<clinit>(Ex.java:9)
VirtualThread[#32]/runnable@ForkJoinPool-1-worker-1 reason:NATIVE
    Ex$C3.<clinit>(Ex.java:10)
  클래스 초기화 블록 안에서 sleep : 808 ms
=== 25
  parallelism=1  (하한 200ms / 줄서면 800ms)
  클래스 초기화 블록 안에서 sleep : 809 ms
```

**왜 그런가**

- **21 은 808 ms, 25 는 809 ms** — **둘 다 줄섰다**(하한 200 ms, 줄서면 800 ms).
- ★ **JEP 491 이 없앤 것은 "모니터"다.** 클래스 초기화(`<clinit>`)는 **VM 호출**이라 그대로 고정한다.\
  21 의 추적 출력이 그것을 `reason:NATIVE` 라고 부른다(모니터는 `reason:MONITOR`).
- **`Object.wait()` 는 21 에서 1,602 ms, 25 에서 200 ms** 다(7번). 모니터 계열이라 함께 고쳐졌다.
- **"24 에서 고쳤으니 고정은 없다"는 틀린 요약이다.**

### 9. 고정을 어떻게 보나

**출력** (`Ex.java` — 56-e, JDK 21.0.5, `-Djdk.tracePinnedThreads=full`)

```text
VirtualThread[#70]/runnable@ForkJoinPool-1-worker-1 reason:MONITOR
    java.base/java.lang.VirtualThread$VThreadContinuation.onPinned(VirtualThread.java:199)
    java.base/jdk.internal.vm.Continuation.onPinned0(Continuation.java:393)
    java.base/java.lang.VirtualThread.parkNanos(VirtualThread.java:635)
    java.base/java.lang.VirtualThread.sleepNanos(VirtualThread.java:807)
    java.base/java.lang.Thread.sleep(Thread.java:507)
    Ex.sleep(Ex.java:31)
    Ex.lambda$run$0(Ex.java:21) <== monitors:1
    java.base/java.lang.VirtualThread.run(VirtualThread.java:329)
  synchronized   5회: [1601, 1601, 1601, 1602, 1605] → 중앙값 1601 ms
```

**JDK 25 에서 같은 플래그를 주면** (고정이 실제로 있는 클래스 초기화 상황에서도)

```text
===== 25: -Djdk.tracePinnedThreads=full
  synchronized   5회: [201, 201, 200, 200, 200] → 중앙값 200 ms
===== 25: jdk.traceVirtualThreadPinnedEvents
  synchronized   5회: [200, 200, 200, 200, 200] → 중앙값 200 ms
=== 25 에서 -Djdk.tracePinnedThreads 가 아직 인식되나 (clinit 고정 상황)
  parallelism=1  (하한 200ms / 줄서면 800ms)
  클래스 초기화 블록 안에서 sleep : 809 ms
```

**JDK 25 에서 고정을 보는 방법 — JFR**

```text
=== jfr summary 중 VirtualThreadPinned
 jdk.VirtualThreadPinned                     4           272
=== jfr print
jdk.VirtualThreadPinned {
  startTime = 07:50:53.337 (2026-09-21)
  duration = 200 ms
  blockingOperation = "LockSupport.park"
  pinnedReason = "VM call to Ex$C0.<clinit> on stack"
  carrierThread = "ForkJoinPool-1-worker-1" (javaThreadId = 40)
  eventThread = "" (javaThreadId = 39, virtual)
  stackTrace = [
    java.lang.VirtualThread.parkOnCarrierThread(boolean, long) line: 826
    java.lang.VirtualThread.parkNanos(long) line: 794
    java.lang.VirtualThread.sleepNanos(long) line: 971
    java.lang.Thread.sleepNanos(long) line: 507
    java.lang.Thread.sleep(long) line: 540
  ]
}
```

**JDK 21 의 같은 이벤트**

```text
=== 21 jfr summary
 jdk.VirtualThreadPinned                     4            56
=== 21 jfr print
jdk.VirtualThreadPinned {
  startTime = 07:51:06.990 (2026-09-21)
  duration = 198 ms
  eventThread = "" (javaThreadId = 45, virtual)
  stackTrace = [
    java.lang.VirtualThread.parkOnCarrierThread(boolean, long) line: 689
    java.lang.VirtualThread.parkNanos(long) line: 648
    java.lang.VirtualThread.sleepNanos(long) line: 807
    java.lang.Thread.sleep(long) line: 507
    Ex.s() line: 11
    ...
  ]
}
```

**왜 그런가**

- **21 의 `-Djdk.tracePinnedThreads=full` 은 콘솔에 스택과 `reason:` 을 찍는다.**\
  `reason:` 값 두 가지를 실제로 봤다 — **`MONITOR`**(`synchronized`) 와 **`NATIVE`**(클래스 초기화).\
  `<== monitors:1` 이 **어느 프레임이 모니터를 쥐고 있는지** 짚어 준다.
- **25 에서는 같은 플래그가 아무것도 안 찍는다.** 고정이 실제로 있는 상황(클래스 초기화, 809 ms)에서도 침묵했다.\
  `jdk.traceVirtualThreadPinnedEvents` 도 콘솔 출력이 없었다.
- **25 에서 보는 방법은 JFR 이다.**

```text
java -XX:StartFlightRecording=filename=p.jfr,settings=profile ...
jfr print --events jdk.VirtualThreadPinned p.jfr
```

- **이벤트는 21 에도 있다.** 다만 **필드가 다르다.**

| 필드 | 21 | 25 |
|---|---|---|
| `startTime` · `duration` · `eventThread` · `stackTrace` | 있다 | 있다 |
| **`blockingOperation`** | 없다 | **있다** |
| **`pinnedReason`** | 없다 | **있다** (`"VM call to Ex$C0.<clinit> on stack"`) |
| **`carrierThread`** | 없다 | **있다** |

- ★ **그래서 "플래그가 있는지부터 확인"해야 한다.** 판마다 다르고, **조용히 아무 일도 안 한다.**

### 10. `ThreadLocal` 의 비용

**출력** (`Ex.java` — 56-h, 8KB 버퍼, `-Xmx8g`, JDK 21.0.5)

```text
--- 1. ThreadLocal 은 가상 스레드에서도 그냥 된다
      가상 스레드 안: 가상
  main 에서 본 값: null  (스레드마다 따로다)
--- 2. 8KB 짜리 ThreadLocal 을 '동시에 살아 있는 스레드 수' 만큼 곱하면
  가상 스레드   1,000개 동시 대기 : ThreadLocal 있음    11 MB / 없음     3 MB / 차이     8 MB
  가상 스레드  10,000개 동시 대기 : ThreadLocal 있음    98 MB / 없음    10 MB / 차이    88 MB
  가상 스레드 100,000개 동시 대기 : ThreadLocal 있음   876 MB / 없음    75 MB / 차이   801 MB
--- 5. 상속 — InheritableThreadLocal
      기본 가상 스레드            : 부모값
      inheritInheritable..(false)  : null
  Thread.Builder.OfVirtual 에 allowSetThreadLocals 가 있나 : false
```

**출력** (`Ex.java` — 56-i, 같은 8KB `ThreadLocal`, 플랫폼 고정 풀, 작업 10만 개)

```text
--- 플랫폼 고정 풀에서 ThreadLocal 사본은 몇 개가 되나
  풀 크기   200 으로 작업 100,000개 처리 뒤 힙    3 MB  (8KB x 200 = 1 MB 어치가 살아 있다)
           풀을 닫은 뒤 힙    1 MB
  풀 크기 2,000 으로 작업 100,000개 처리 뒤 힙   18 MB  (8KB x 2,000 = 15 MB 어치가 살아 있다)
           풀을 닫은 뒤 힙    1 MB
```

**왜 그런가**

- **10만 개 동시 대기에서 힙이 801 MB 늘어난다**(876 대 75 MB). 자릿수로 **수백 MB**.
- **플랫폼 고정 풀 200 이면 사본은 200개**다 — 작업이 10만 개여도. 힙은 **3 MB**.\
  `ThreadLocal` 의 사본 수는 **작업 수가 아니라 "동시에 살아 있는 스레드 수**"다.
- ★ **캐시로 쓰던 코드가 거꾸로 되는 이유** — 플랫폼 풀에서는 스레드가 **여러 작업을 돌며 버퍼를 재사용**한다.\
  가상 스레드는 **한 작업만 하고 죽는다.** **재사용이 0이고 사본만 늘어난다.**
- **`InheritableThreadLocal` 은 기본으로 상속된다**(`부모값`).\
  끄려면 **`Thread.ofVirtual().inheritInheritableThreadLocals(false)`** — 실측에서 `null` 이 나왔다.
- **`Thread.Builder.OfVirtual` 에 `allowSetThreadLocals` 는 없다**(리플렉션으로 확인, `false`).\
  21 의 공개 API 표면에는 그 스위치가 없다.
- 대안은 **`ScopedValue`**(11번).

### 11. 프리뷰 상태

**`src.zip` 에서 직접 읽은 것**

```text
=== 21.0.5-tem StructuredTaskScope
38:import jdk.internal.javac.PreviewFeature;
299: * @since 21
301:@PreviewFeature(feature = PreviewFeature.Feature.STRUCTURED_CONCURRENCY)
=== 25.0.1-tem StructuredTaskScope
32:import jdk.internal.javac.PreviewFeature;
349: * @since 21
351:@PreviewFeature(feature = PreviewFeature.Feature.STRUCTURED_CONCURRENCY)

=== 21.0.5-tem ScopedValue
38:import jdk.internal.javac.PreviewFeature;
237: * @since 21
239:@PreviewFeature(feature = PreviewFeature.Feature.SCOPED_VALUES)
=== 25.0.1-tem ScopedValue
239: * @since 25
311:     * @since 25
496:     * @since 25
```

**왜 그런가**

- **`StructuredTaskScope` 는 21 과 25 모두 프리뷰**다. 두 버전 다 `@PreviewFeature` 가 붙어 있다.
- **`ScopedValue` 는 21 에서 프리뷰**(`@PreviewFeature` + `@since 21`),\
  **25 에서 확정**(`@PreviewFeature` 가 **사라졌고** `@since` 가 **25** 로 바뀌었다).
- **확인 방법은 `src.zip` 의 애너테이션과 `@since` 를 직접 읽은 것**이다.\
  ★ **기억으로 쓰면 틀린다.** `StructuredTaskScope` 가 25에서 확정됐다고 잘못 알기 쉬운데,\
  이 머신의 25.0.1 소스에는 **여전히 `@PreviewFeature` 가 붙어 있다.**

### 12. 이 코드를 가상 스레드로 바꿔야 하나

**(A) 요청마다 DB 2회 + 외부 API 1회 (평균 120ms 대기)**

- **바꾼다.** 여기가 가상 스레드의 자리다.
- 근거: 5번 — 블로킹 1만 건에서 고정 풀 16 대비 **287배**(6,317 → 22 ms).

**(B) 이미지 1만 장 리사이즈 (CPU 만 씀)**

- **바꾸지 않는다.** 코어 수만큼의 고정 풀이나 병렬 스트림([`../49-parallel-streams/`](../49-parallel-streams/)).
- 근거: 5번 — CPU 작업에서 **88 대 97 ms**. 같은 자릿수다.

**(C) JDK 21 서비스인데 핵심 경로가 전부 `synchronized`**

- **`ReentrantLock` 으로 먼저 바꾼다.** 안 바꾸고 옮기면 동시성이 캐리어 수로 줄어든다.
- 근거: 7번 — 21 에서 **200 → 1,601 ms**(8배). `ReentrantLock` 은 21 에서도 200 ms.
- **JDK 24 이상으로 올릴 수 있다면 그게 더 싼 답이다**(JEP 491).

**(D) DB 커넥션 풀이 20개뿐이다**

- **가상 스레드 + `Semaphore(20)`.** 스레드 풀 크기로 제한하지 않는다.
- 근거: 6번 — 풀은 "재활용"과 "제한"을 겸하는데 가상 스레드에는 **제한만** 필요하다.

**(E) 요청마다 8KB 버퍼를 `ThreadLocal` 로 재사용**

- **`ThreadLocal` 을 먼저 걷어낸다.** 지역 변수로 만들거나 풀링 객체로 바꾼다.
- 근거: 10번 — 10만 개 동시 대기에서 **801 MB** 차이. 가상 스레드는 재사용이 0이다.

**(F) JDK 17 로 빌드한다**

- **못 쓴다.** `cannot find symbol: method ofVirtual()` — 컴파일부터 안 된다(1번).

**(G) 응답이 느린 원인이 외부 API 자체의 지연**

- **바꿔도 그대로다.** 병목이 내 스레드가 아니다.
- 근거: 5번의 소켓 실측 — 서버 쪽이 병목이라 풀 500 과 가상 스레드가 **366 대 315 ms** 로 거의 같았다.

### 13. 같은 실험을 25 에서 다시 돌리면

**출력** (`Ex.java` — 56-a, JDK 25.0.1)

```text
--- 1. 만드는 법 셋
  Thread.ofVirtual().unstarted(..)  : isVirtual=true 상태=NEW 이름="직접-만든-것"
  Thread.startVirtualThread(..)     : isVirtual=true 이름="" (기본 이름은 빈 문자열)
  newVirtualThreadPerTaskExecutor   : true / VirtualThread[#38]/runnable@ForkJoinPool-1-worker-1
--- 2. 플랫폼 스레드와 무엇이 다른가
                     isVirtual isDaemon  priority   threadGroup
  가상 스레드             true      true      5          VirtualThreads
  플랫폼 스레드            false     false     5          main
  가상 스레드에 setDaemon(false) : java.lang.IllegalArgumentException: 'false' not legal for virtual threads
  가상 스레드에 setDaemon(true)  : 예외 없음(원래 데몬)
  setPriority(10) 뒤 priority   : 5   <- 무시된다
--- 4. 캐리어(carrier) 스레드는 몇 개인가
  availableProcessors            : 24
  CPU 만 쓰는 작업 2000개가 쓴 캐리어 수 : 24
  캐리어 이름 예 : [ForkJoinPool-1-worker-1, ForkJoinPool-1-worker-10, ForkJoinPool-1-worker-11]
```

**출력** (`Ex.java` — 56-c, JDK 25.0.1, 워밍업 2 + 측정 5의 중앙값)

```text
--- 블로킹 작업 10,000개 (각 sleep 10ms) / 워밍업 2 + 측정 5의 중앙값
  플랫폼 고정 풀 16                        중앙값   6318 ms  (최소 6315, 최대 6322)
  플랫폼 고정 풀 200                       중앙값    515 ms  (최소 512, 최대 519)
  플랫폼 고정 풀 2000                      중앙값    226 ms  (최소 201, 최대 244)
  가상 스레드 (작업당 하나)                    중앙값     21 ms  (최소 19, 최대 35)
  이상적 하한 = 10ms (전부 동시에 자면)
--- CPU 만 쓰는 작업 10,000개 / 워밍업 2 + 측정 5의 중앙값
  플랫폼 고정 풀 24(=코어 수)                 중앙값     85 ms  (최소 81, 최대 99)
  플랫폼 고정 풀 200                       중앙값     99 ms  (최소 97, 최대 100)
  가상 스레드 (작업당 하나)                    중앙값     99 ms  (최소 94, 최대 106)
```

**출력** (`Ex.java` — 56-b, JDK 25.0.1, `-Xmx2g`)

```text
===== 25 / virtual 1000000
  virtual 스레드 1,000,000개 생성 성공 — 989 ms
  동시에 sleep(2000) 중이던 개수 : 1,000,000
===== 25 / platform 10000
  platform 스레드 10,000개 생성 성공 — 987 ms
  동시에 sleep(2000) 중이던 개수 : 10,000
```

**왜 그런가**

- **출력에서 달라진 것은 스레드 id 하나뿐**이다 — `VirtualThread[#31]`(21) 대 `VirtualThread[#38]`(25).\
  id 는 JVM 이 그때까지 만든 스레드 수에 따라 달라지므로 **비교 대상이 아니다.**\
  데몬·우선순위·스레드그룹·예외 메시지·캐리어 수·캐리어 이름은 **한 글자도 안 달랐다.**\
  ★ 그래도 **관찰이지 보장이 아니다.**
- **블로킹 결론은 유지된다.** 가상 스레드가 **21 ms**(21 에서는 22 ms)로 하한(10 ms)에 가장 가깝다.
- ★ **CPU 바운드의 승패는 뒤집혔다.**

| | JDK 21 | JDK 25 |
|---|---|---|
| 고정 풀 24(=코어 수) | 97 ms | **85 ms** |
| 가상 스레드 | **88 ms** | 99 ms |
| 승자 | **가상 스레드** | **고정 풀** |

- **뒤집혔다는 사실에서 끌어낼 결론** — ★ **그 차이는 차이가 아니라 잡음이다.**\
  "가상 스레드가 CPU 작업에서 몇 % 빠르다/느리다"는 말을 **쓸 수 없다.**\
  두 버전이 함께 말하는 것은 하나다 — **CPU 바운드에는 값이 없다.**\
  반대로 블로킹의 **287배**는 두 버전에서 모두 같은 방향이라 결론으로 쓸 수 있다.
- **100만 개 생성은 21 에서 604 ms, 25 에서 989 ms** — **자릿수가 같다**(수백 ms).\
  플랫폼 1만 개도 1,291 대 987 ms 로 같은 자릿수다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 반복 | 돌린 JDK |
|---|---|---|---|
| `Ex.java` (56-a) | 만드는 법 셋, 데몬·우선순위·스레드그룹, `setDaemon(false)` 예외, 캐리어 수와 이름 | 1회 | **21 · 25** (스레드 id 말고 동일) + **17 컴파일 에러** 확인 |
| `Ex.java` (56-b) | 가상 1만·100만 / 플랫폼 1만·10만 생성 시간, `ulimit -u 6000` 에서의 `OutOfMemoryError` | 각 1회 | **21 · 25**(가상 100만·플랫폼 1만만 재실행 — 자릿수 동일) |
| `Ex.java` (56-c) | 블로킹 1만 건·CPU 1만 건에서 풀 3종 대 가상 스레드 | **워밍업 2 + 측정 5의 중앙값** | **21 · 25** (블로킹 결론 동일, **CPU 승패는 뒤집힘**) |
| `Ex.java` (56-e) | ★ `plain`/`synchronized`/`ReentrantLock` 의 고정, `-Djdk.tracePinnedThreads` 출력 | **각 5회** | **21 · 25** (**갈렸다**) |
| `Ex.java` (56-f) | `synchronized`·`Object.wait`·블록 안 I/O·리플렉션 프레임의 고정 | **각 5회** | **21 · 25** (**갈렸다**) |
| `Ex.java` (56-g) | 클래스 초기화 블록 안 블로킹의 고정, `reason:NATIVE` 출력, JFR 이벤트 | 1회 | **21 · 25** (**둘 다 고정**) |
| `Ex.java` (56-h) | `ThreadLocal` 힙 사용(1천·1만·10만), 풀링 시 스레드 수, 생성 비용 3종, `InheritableThreadLocal` | 힙 각 1회 / 시간은 워밍업 2 + 5회의 중앙값 | 21 |
| `Ex.java` (56-i) | 플랫폼 고정 풀(200·2000)에서의 `ThreadLocal` 사본 힙 | 각 1회 | 21 |
| `Ex.java` (56-k) | 진짜 TCP 소켓 3,000건에서 풀 2종 대 가상 스레드 | 워밍업 1 + 측정 3의 중앙값 | 21 |
| `jfr` 도구 | `jdk.VirtualThreadPinned` 이벤트의 유무와 **필드 차이** | 1회 | **21 · 25** (**필드가 갈렸다**) |
| `src.zip` 열람 | `ofVirtual`·`startVirtualThread`·`isVirtual`·`newVirtualThreadPerTaskExecutor` 의 `@since 21`, `StructuredTaskScope`·`ScopedValue` 의 `@PreviewFeature` | — | **21 · 25** |

**측정 방법의 한계 (반드시 같이 읽을 것)**

- **JMH 가 아니다.** 워밍업이 1\~2회뿐이다.
- **머신 의존**이다 — 24코어. 코어가 적으면 CPU 실험의 차이가 더 작아지고, 고정 실험은 캐리어를 1로 묶었으므로 영향이 적다.
- **흔들린다** — 소켓 실험이 **183\~326 ms**(1.8배). **고정 실험만 흔들림이 거의 없다**(1601\~1605 / 200\~215).\
  그 실험은 "**줄서나 안 서나**"를 8배 차이로 설계했기 때문이다.
- **힙 수치는 정확한 측정이 아니다** — `System.gc()` 두 번 뒤의 `totalMemory - freeMemory` 다. **자릿수용.**
- **`sleep` 은 블로킹 I/O 의 대역이다.** 진짜 소켓으로도 재 봤고(56-k) **결과가 덜 극적이었다** — 그 사실을 본문에 적었다.
- **측정하지 않은 것** — ① `ScopedValue` 의 비용, ② `StructuredTaskScope` 의 동작,\
  ③ `jcmd Thread.dump_to_file` 의 가상 스레드 덤프, ④ FFM 다운콜에서의 고정.

**구현 의존 항목** (버전이 오르면 다시 돌려야 하는 것)

- ★ **`synchronized`·`Object.wait` 의 고정 — 21 과 25 가 실제로 갈렸다**(1,601 대 200 ms).
- ★ **`-Djdk.tracePinnedThreads` — 25 에서는 아무것도 안 찍는다.**
- ★ **JFR `jdk.VirtualThreadPinned` 의 필드 — 25 에만 `pinnedReason`·`blockingOperation`·`carrierThread`.**
- **클래스 초기화 고정은 21·25 모두 남아 있다** — 24 이후 판에서 또 바뀔 수 있다.
- 캐리어 수가 `availableProcessors` 인 것, 캐리어 풀 이름 — 구현 세부.
- `toString` 형식, `setDaemon(false)` 의 메시지 문구 — 구현 세부.
- `StructuredTaskScope` 의 프리뷰 여부 — **25.0.1 기준 아직 프리뷰다.** 다음 판에서 바뀔 수 있다.
- **생성 비용·처리 시간 수치 전부** — 아무도 보장하지 않는다.
- **JDK 17 에서는 컴파일 자체가 안 된다** — 이 주제에 "세 버전 공통"은 없다.
