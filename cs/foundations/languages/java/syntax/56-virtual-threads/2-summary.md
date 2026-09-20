# java/syntax/56 — 가상 스레드 (21): 쓰는 법과 막히는 자리 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **선행** — [`../54-executorservice-and-future/`](../54-executorservice-and-future/) (`ExecutorService`·`Future`·풀 크기 — **가상 스레드는 그 질문 자체를 없앤다**) · [`../33-synchronized-and-volatile/`](../33-synchronized-and-volatile/) (`synchronized` 의 문법 — **여기서 그 키워드가 버전에 따라 다르게 동작한다**).
> **기준 소스** — [`java.lang.Thread` API 문서 (Java SE 21)](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Thread.html) · [`Executors`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/Executors.html) · [JEP 444 — Virtual Threads](https://openjdk.org/jeps/444) · [JEP 491 — Synchronize Virtual Threads without Pinning](https://openjdk.org/jeps/491) · 이 머신의 `lib/src.zip` 에서 **직접 읽은** `java.base/java/lang/Thread.java`·`java/util/concurrent/Executors.java`·`StructuredTaskScope.java`.
> **실행 검증** — 이 문서의 모든 출력·에러·수치는 Temurin **21.0.5** 와 **25.0.1** 에서 실제로 돌려 얻은 것이다.\
> ★ **고정(pinning) 실험은 21 과 25 에서 각각 돌렸고 결과가 갈렸다** — 아래 (5).\
> 17 에서는 **컴파일부터 안 된다**(`cannot find symbol: method ofVirtual()`) — 그 에러도 실었다.
> ⚠️ **측정 조건**\
> 도구: **JMH 가 아니다.** 벽시계(`System.nanoTime`)이고 **워밍업 1~2회 + 측정 3~5회의 중앙값**이다(실험마다 본문에 적었다).\
> 머신: **CPU 24코어**(`availableProcessors` = 24), Linux x86-64, `ulimit -n` = 1,048,576.\
> 흔들림: 소켓 실험이 **183~326 ms** 로 1.8배 흔들렸다. 고정 실험은 흔들림이 거의 없었다(1601~1605 ms).\
> 고정 실험은 **캐리어를 1개로 묶어**(`-Djdk.virtualThreadScheduler.parallelism=1 -Djdk.virtualThreadScheduler.maxPoolSize=1`)\
> **"줄서면 1600ms, 안 줄서면 200ms"** 라는 **두 자리로 갈리게** 설계했다. 그래서 이 실험만은 흔들림이 결론을 안 흔든다.\
> 힙 사용량은 `System.gc()` 두 번 뒤 `totalMemory - freeMemory` 다 — **정확한 측정이 아니라 자릿수용**이다.
> **버전** — `Thread.ofVirtual()`·`Thread.startVirtualThread()`·`Thread.isVirtual()` 은 **`@since 21`**,\
> `Executors.newVirtualThreadPerTaskExecutor()` 도 **`@since 21`** 이다(`src.zip` 의 `@since` 를 직접 읽었다).\
> `ExecutorService.close()` 는 **`@since 19`** 라 가상 스레드보다 먼저 들어왔다([`../54-executorservice-and-future/`](../54-executorservice-and-future/)).\
> ★ **`StructuredTaskScope` 는 21 과 25 모두 `@PreviewFeature`** 다(`src.zip` 의 애너테이션을 직접 읽었다).\
> **`ScopedValue` 는 21 에서 `@PreviewFeature` + `@since 21`, 25 에서는 `@PreviewFeature` 가 없고 `@since 25`** 다 — 확정됐다.
> **범위** — OS 스레드·컨텍스트 스위칭·스케줄링은 [`../../../../process-thread/`](../../../../process-thread/) 가 정본이다.\
> 그쪽은 **스레드가 무엇이고 OS 가 무엇을 하나**까지, 여기는 **이 API 를 어떻게 쓰고 어디서 막히나**부터다.\
> **JIT·GC·런타임 내부**는 [`../../언어-특성/README.md`](../../언어-특성/README.md) 가 정본이다.\
> **가상 스레드가 왜 들어왔나(JEP 논쟁·설계 역사)**는 [`../../../../../../history/java/java-21.md`](../../../../../../history/java/java-21.md) 가 정본이다.\
> **공용 ForkJoinPool 경합**은 [`../49-parallel-streams/`](../49-parallel-streams/) 가 정본이다 — 가상 스레드 스케줄러는 **별도의 `ForkJoinPool`** 이다(실측 스레드 이름으로 확인).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 javadoc·`src.zip`·JEP 로, 출력은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**가상 스레드는 "직원을 늘리는 대신, 기다리는 동안 자리를 비켜 주게 만든 것"이다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 창구 직원 | **캐리어(carrier) 스레드** — 진짜 OS 스레드, 코어 수만큼 |
| 손님 | **가상 스레드** — 수백만 개 만들 수 있다 |
| 손님이 서류를 기다리는 동안 자리를 비켜 줌 | **마운트 해제(unmount)** — 블로킹하면 캐리어를 놓는다 |
| 서류가 오면 빈 창구에 다시 앉음 | **마운트(mount)** — 아무 캐리어에나 다시 올라간다 |
| **자리를 안 비켜 주고 버티는 손님** | **고정(pinning)** — 캐리어를 붙잡는다 |
| 손님을 재활용하려고 대기실을 만듦 | **가상 스레드 풀링 — 할 이유가 없다** |
| 손님마다 짐 보관함을 하나씩 | `ThreadLocal` — **손님이 100만이면 보관함도 100만** |

- 손님은 **싸다.** 실측에서 **100만 개를 604 ms 에** 만들었다.\
  같은 프로그램이 플랫폼 스레드 10만 개에 **47,973 ms** 를 썼다.
- 손님이 **기다릴 때만** 이득이다.\
  블로킹 작업 1만 개에서 고정 풀 16 대비 **6,317 ms → 22 ms**.\
  CPU 만 쓰는 작업 1만 개에서는 **97 ms → 88 ms** — **차이가 없다.**
- ★ **JDK 21 에서는 `synchronized` 블록 안에서 블로킹하면 자리를 안 비켜 준다.**\
  실측에서 같은 코드가 **21 에서 1,601 ms, 25 에서 200 ms** 였다.

```text
블로킹 I/O 가 많을 때                        CPU 만 쓸 때

  플랫폼 고정 풀 16   6,317 ms                플랫폼 고정 풀 24    97 ms
  플랫폼 고정 풀 200    521 ms                플랫폼 고정 풀 200  123 ms
  플랫폼 고정 풀 2000   269 ms                가상 스레드          88 ms
  가상 스레드            22 ms                      |
        |                                           v
        v                                    차이가 없다 — 코어 수가 상한이다
  287배. 여기가 가상 스레드의 자리다
```

**똑같은 구조로** 자바가 이렇게 동작한다: 창구 = 캐리어 `ForkJoinPool-1-worker-N`, 손님 = `VirtualThread[#31]`.\
실측한 `toString` 이 **`VirtualThread[#31]/runnable@ForkJoinPool-1-worker-1`** — **손님/창구**가 그대로 찍힌다.

실무에서 이게 헛도는 자리는 **"가상 스레드로 바꿨는데 안 빨라졌다"** 이다.\
CPU 바운드였거나, `synchronized` 로 고정됐거나(21), **병목이 내 쪽이 아니었던 것**이다.

> **캐리어 스레드(carrier thread)** — 가상 스레드를 실제로 실행하는 OS 스레드.\
> 예: 실측에서 CPU 만 쓰는 작업 2,000개가 **캐리어 24개**(= 코어 수)를 썼다.

> **마운트 해제(unmount)** — 가상 스레드가 블로킹할 때 캐리어에서 내려와 힙으로 스택을 옮기는 것.\
> 예: `Thread.sleep` 중인 가상 스레드는 캐리어를 점유하지 않는다.

> **고정(pinning)** — 마운트 해제가 안 되어 블로킹하는 동안에도 캐리어를 붙잡는 상태.\
> 예: JDK 21 에서 `synchronized` 블록 안의 `Thread.sleep` 이 그렇다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 네 질문을 둔다.

1. 가상 스레드를 **만드는 법 셋**과 플랫폼 스레드와 **다르게 동작하는 것**은 무엇인가.
2. **언제 값이 나나** — 그리고 언제 값이 **안 나나**.
3. **무엇이 캐리어를 붙잡나** — 그리고 그것이 **JDK 판에 따라 어떻게 달라졌나**.
4. 기존 습관(**풀링·`ThreadLocal`**) 중 무엇을 버려야 하나.

## 동작 방식

### (1) 만드는 법 셋과 기본 성질

**언제 쓰나** — 가상 스레드를 처음 쓸 때.

**실행 결과** (`Ex.java` — 56-a, JDK 21.0.5)

```text
--- 1. 만드는 법 셋
  Thread.ofVirtual().unstarted(..)  : isVirtual=true 상태=NEW 이름="직접-만든-것"
  Thread.startVirtualThread(..)     : isVirtual=true 이름="" (기본 이름은 빈 문자열)
  newVirtualThreadPerTaskExecutor   : true / VirtualThread[#31]/runnable@ForkJoinPool-1-worker-1
--- 2. 플랫폼 스레드와 무엇이 다른가
                     isVirtual isDaemon  priority   threadGroup
  가상 스레드             true      true      5          VirtualThreads
  플랫폼 스레드            false     false     5          main
  가상 스레드에 setDaemon(false) : java.lang.IllegalArgumentException: 'false' not legal for virtual threads
  가상 스레드에 setDaemon(true)  : 예외 없음(원래 데몬)
  setPriority(10) 뒤 priority   : 5   <- 무시된다
--- 3. 가상 스레드는 데몬이다 — main 이 끝나면 JVM 이 기다려 주지 않는다
  3초짜리 가상 스레드를 띄우고 main 을 끝낸다
--- 4. 캐리어(carrier) 스레드는 몇 개인가
  availableProcessors            : 24
  CPU 만 쓰는 작업 2000개가 쓴 캐리어 수 : 24
  캐리어 이름 예 : [ForkJoinPool-1-worker-1, ForkJoinPool-1-worker-10, ForkJoinPool-1-worker-11]
```

```text
가상 스레드의 toString 이 구조를 그대로 보여 준다

  VirtualThread[#31]/runnable@ForkJoinPool-1-worker-1
  ^^^^^^^^^^^^^^^^^^ ^^^^^^^^ ^^^^^^^^^^^^^^^^^^^^^^
     손님(가상)        상태       지금 앉아 있는 창구(캐리어)
```

그림 해설 (한 단계씩):

- **만드는 법 셋**\
  ① `Thread.ofVirtual().name(..).unstarted(r)` — 빌더. 시작을 나중에 한다.\
  ② `Thread.startVirtualThread(r)` — 만들고 바로 시작. **기본 이름이 빈 문자열**이다.\
  ③ `Executors.newVirtualThreadPerTaskExecutor()` — **`ExecutorService` 인터페이스 그대로** 쓴다.
- **가상 스레드는 항상 데몬이다.** `setDaemon(false)` 는 **`IllegalArgumentException: 'false' not legal for virtual threads`**.\
  그래서 **`main` 이 끝나면 JVM 이 기다려 주지 않는다** — 실측에서 3초짜리 가상 스레드의 출력이 안 찍혔다.
- **우선순위는 무시된다.** `setPriority(10)` 뒤에도 `5` 다. 예외는 안 난다.
- **캐리어는 코어 수만큼**이다 — CPU 만 쓰는 작업 2,000개가 캐리어 **24개**를 썼다.\
  캐리어 이름이 `ForkJoinPool-1-worker-N` 이다. ★ **공용 풀(`ForkJoinPool.commonPool-worker-N`)과 이름이 다르다** —\
  가상 스레드 스케줄러는 **별도의 `ForkJoinPool`** 이다([`../49-parallel-streams/`](../49-parallel-streams/) 의 공용 풀과 섞이지 않는다).

**17 에서는 컴파일이 안 된다**

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

비용 — **없다.** 만드는 것 자체는 (3) 에서 보듯 플랫폼 스레드의 22분의 1이다.

### (2) 몇 개나 만들 수 있나

**언제 쓰나** — "동시 요청 N건을 스레드 N개로 받아도 되나"를 판단할 때.

**실행 결과** (`Ex.java` — 56-b, `-Xmx2g`, 각 1회, JDK 21.0.5)

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

**프로세스 수 제한을 걸면 무엇이 터지나** (`ulimit -u 6000`)

```text
=== ulimit -u 6000 로 제한한 뒤
[0.344s][warning][os,thread] Failed to start thread "Unknown thread" - pthread_create failed (EAGAIN) for attributes: stacksize: 1024k, guardsize: 0k, detached.
[0.344s][warning][os,thread] Failed to start the native thread for java.lang.Thread "Thread-3749"
  platform 스레드 100,000개 만들다 3,749개에서 터졌다 (312 ms)
  java.lang.OutOfMemoryError: unable to create native thread: possibly out of memory or process/resource limits reached
--- 같은 제한에서 가상 스레드
  virtual 스레드 100,000개 생성 성공 — 115 ms
```

```text
플랫폼 스레드                               가상 스레드

  OS 스레드 하나 = 스택 1024k 예약            스택이 힙 위의 객체다
  프로세스 스레드 수 제한에 걸린다              OS 는 24개만 본다
        |                                          |
        v                                          v
  6000 제한에서 3,749개에 OOM                 같은 제한에서 100,000개 성공
  10만 개는 47,973 ms 걸렸다                  100만 개를 604 ms 에 만들었다
```

그림 해설 (한 단계씩):

- **가상 스레드 100만 개를 604 ms 에** 만들었고 **100만 개가 동시에 `sleep`** 중이었다.
- **플랫폼 스레드는 10만 개에 47,973 ms** 다 — 만들 수는 있지만 **80배 느리다.**
- **프로세스 스레드 제한을 걸면 플랫폼 스레드는 3,749개에서 죽는다.**\
  에러 메시지가 원인을 정확히 말한다 — `pthread_create failed (EAGAIN)`, `stacksize: 1024k`,\
  `OutOfMemoryError: unable to create native thread: possibly out of memory or process/resource limits reached`.
- **같은 제한에서 가상 스레드는 10만 개가 멀쩡하다.** OS 에게는 캐리어 24개만 보이기 때문이다.

비용 — 가상 스레드의 스택은 **힙 위**에 있다. 그래서 **힙을 쓴다**((6) 의 `ThreadLocal` 실측).

### (3) ★ 언제 값이 나나 — 블로킹일 때만

**언제 쓰나** — "가상 스레드로 바꿔 볼까"를 판단할 때. **이 주제의 핵심 판단이다.**

**실행 결과** (`Ex.java` — 56-c, 작업 1만 개, **워밍업 2 + 측정 5의 중앙값**, JMH 아님, 24코어, JDK 21.0.5)

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

```text
블로킹 (sleep 10ms x 10,000)               CPU 바운드 (40만 회 덧셈 x 10,000)

  고정 풀 16    6,317 ms                    고정 풀 24     97 ms
  고정 풀 200     521 ms                    고정 풀 200   123 ms
  고정 풀 2000    269 ms                    가상 스레드     88 ms
  가상 스레드       22 ms                          |
        |                                          v
        v                                   전부 같은 자릿수 — 이득이 없다
  하한(10ms)에 가장 가깝다                     코어 24개가 상한이기 때문
```

그림 해설 (한 단계씩):

- **블로킹에서 가상 스레드가 고정 풀 16의 287배** 빠르다. 하한 10 ms 에 가장 가깝다(22 ms).
- **풀을 2000까지 키우면 269 ms 까지 따라온다.** 그러나 그건 **OS 스레드 2000개**를 만든다는 뜻이고,\
  (2) 에서 봤듯 **프로세스 제한에 걸릴 수 있다.**
- **CPU 바운드에서는 이득이 없다** — 88 대 97 ms 는 **같은 자릿수**다.\
  계산은 **코어 24개** 위에서만 돌 수 있고, 스레드를 늘려도 코어가 안 늘어난다.\
  ★ 오히려 고정 풀 200 이 **123 ms 로 가장 느렸다** — 스레드를 코어보다 많이 만들면 손해다.

**진짜 소켓으로도 재 봤다**

**실행 결과** (`Ex.java` — 56-k, 로컬 TCP 소켓 3,000건, 서버가 50 ms 뒤 응답, 워밍업 1 + 측정 3의 중앙값)

```text
--- 진짜 소켓 I/O 3,000건 (서버가 50ms 뒤에 응답) / 워밍업 1 + 측정 3의 중앙값
  플랫폼 고정 풀 50        3회 [3046, 3044, 3044] → 중앙값 3044 ms
  플랫폼 고정 풀 500       3회 [366, 368, 363] → 중앙값 366 ms
  가상 스레드             3회 [183, 315, 326] → 중앙값 315 ms
  이상적 하한 = 50ms
```

- **풀 50 대비 9.7배**지만, **풀 500 과는 거의 차이가 없다**(366 대 315 ms).
- ★ **`sleep` 실험만큼 극적이지 않다.** 이 실험에서는 **연결 수립과 서버 쪽이 병목**이라\
  클라이언트 스레드 모델을 바꿔도 더 못 줄인다.\
  **흔들림도 크다** — 183~326 ms(1.8배).
- **결론** — 가상 스레드의 이득은 **"내 스레드가 병목일 때"**만 나온다.\
  병목이 DB·외부 API·대역폭이면 스레드를 바꿔도 그대로다.

비용 — 블로킹이 아니면 값이 없다. **바꾸기 전에 어디가 병목인지 먼저 본다.**

### (4) 풀링하면 안 되는 이유

**언제 쓰나** — 기존 코드의 `newFixedThreadPool` 을 바꿀 때.

**실행 결과** (`Ex.java` — 56-h, JDK 21.0.5)

```text
--- 3. 가상 스레드를 '풀링' 하면 무슨 일이 나나
  작업 10,000개가 쓴 서로 다른 가상 스레드 수 : 10000  (작업마다 새로 만든다)
--- 4. 만드는 비용 — 10만 번 (워밍업 2 + 측정 5의 중앙값)
  가상 스레드 start+join   : 중앙값 450 ms (최소 374, 최대 502)
  플랫폼 스레드 start+join : 중앙값 9939 ms (최소 9743, 최대 10114)
  고정 풀 1 에 submit+get  : 중앙값 745 ms (최소 606, 최대 877)
```

```text
플랫폼 스레드를 풀링하는 이유                가상 스레드에는 그 이유가 없다

  만드는 데 10만 번에 9,939 ms               만드는 데 10만 번에 450 ms
  -> 재활용해서 아끼는 게 이득               -> 풀에 넣는 비용(745 ms)이 더 크다
        |                                          |
        v                                          v
  풀이 동시성의 상한이 된다                    작업마다 하나씩 만든다
  (그래서 크기를 고민해야 한다)                (상한이라는 개념 자체가 없다)
```

그림 해설 (한 단계씩):

- **`newVirtualThreadPerTaskExecutor` 는 작업 1만 개에 가상 스레드 1만 개**를 만든다. 재활용이 없다.
- **만드는 비용이 플랫폼 스레드의 22분의 1**이다(450 대 9,939 ms).
- ★ **고정 풀 1에 `submit`+`get` 하는 것(745 ms)보다도 가상 스레드를 새로 만드는 게 싸다**(450 ms).\
  즉 **풀링이 이득이 아니다.**
- 그리고 풀링하면 **풀 크기가 동시성의 상한**이 되어 **가상 스레드를 쓰는 이유 자체가 사라진다.**

비용 — **가상 스레드는 풀에 넣지 않는다.** 동시성을 제한하고 싶으면 **`Semaphore`** 로 제한한다\
(풀은 "스레드 재활용"과 "동시성 제한" 둘을 겸하는데, 가상 스레드에는 **뒤의 것만** 필요하다).

### (5) ★★ 무엇이 캐리어를 붙잡나 — 21 과 25 가 갈린다

**언제 쓰나** — 가상 스레드로 바꿨는데 안 빨라질 때. **이 주제의 최대 함정이다.**

실험 설계 — **캐리어를 1개로 묶고**(`-Djdk.virtualThreadScheduler.parallelism=1 -Djdk.virtualThreadScheduler.maxPoolSize=1`)\
가상 스레드 8개가 **각자 다른 락**으로 200 ms 씩 잔다. **락 경합은 없다.**\
고정이 없으면 8개가 동시에 자므로 **200 ms**, 고정되면 하나씩 줄서므로 **1,600 ms** 다.

**실행 결과** (`Ex.java` — 56-e, 각 5회)

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

```text
JDK 21                                     JDK 25

  plain          200 ms                     plain          200 ms
  synchronized  1601 ms  <- 줄섰다           synchronized   200 ms  <- 안 줄섰다
  ReentrantLock  200 ms                     ReentrantLock  200 ms
        |                                          |
        v                                          v
  synchronized 가 캐리어를 붙잡는다            JEP 491 (JDK 24) 이후 안 붙잡는다
  -> 21 에서는 ReentrantLock 으로 바꾼다       -> 바꿀 필요가 없어졌다
```

그림 해설 (한 단계씩):

- **JDK 21 에서 `synchronized` 만 1,601 ms** 다. **8배** — 정확히 "하나씩 줄선" 값이다.
- **JDK 25 에서는 200 ms** 다. 같은 코드, 같은 설정인데 **고정이 사라졌다.**\
  [JEP 491](https://openjdk.org/jeps/491)(JDK 24) 이 모니터 고정을 없앴다.
- **`ReentrantLock` 은 21 에서도 200 ms** 다. **21 에서의 처방이 이것**이었다.
- **흔들림이 거의 없다**(1601~1605, 200~215). 이 실험만은 **결론이 흔들리지 않는다.**

**21 에서 더 넓게 재 봤다 — 무엇이 고정되나**

**실행 결과** (`Ex.java` — 56-f, 각 5회, 같은 캐리어 1개 설정)

```text
===== 21
  parallelism=1  (하한 200ms / 줄서면 1600ms)
  synchronized+sleep       5회 [1612, 1602, 1601, 1601, 1601] → 중앙값 1601 ms
  Object.wait              5회 [1602, 1602, 1602, 1602, 1602] → 중앙값 1602 ms
  동기화 블록 안에서 I/O           5회 [1621, 1602, 1601, 1601, 1602] → 중앙값 1602 ms
  native 프레임 아래 sleep      5회 [206, 201, 200, 200, 200] → 중앙값 200 ms
===== 25
  parallelism=1  (하한 200ms / 줄서면 1600ms)
  synchronized+sleep       5회 [213, 200, 200, 200, 200] → 중앙값 200 ms
  Object.wait              5회 [202, 200, 200, 200, 200] → 중앙값 200 ms
  동기화 블록 안에서 I/O           5회 [220, 201, 200, 200, 200] → 중앙값 200 ms
  native 프레임 아래 sleep      5회 [210, 201, 200, 200, 200] → 중앙값 200 ms
```

- **21 에서 `synchronized` 와 `Object.wait` 가 전부 고정**된다. 그 안의 I/O 도 마찬가지다.
- **25 에서는 넷 다 고정이 없다.**

**★ 그런데 25 에서도 고정되는 것이 남아 있다**

**실행 결과** (`Ex.java` — 56-g, 클래스 초기화 블록 안에서 `sleep`, 가상 스레드 4개, 캐리어 1개)

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

- **25 에서도 809 ms** 다 — **여전히 줄선다.** JEP 491 이 없앤 것은 **모니터**이지 **네이티브 프레임**이 아니다.
- 21 은 `-Djdk.tracePinnedThreads=short` 로 **`reason:NATIVE`** 를 찍어 준다.
- **25 는 콘솔에 아무것도 안 찍는다** — 아래 (5-1) 이 그 얘기다.

비용 — **21 에서는 `synchronized` 를 `ReentrantLock` 으로 바꾸는 것이 처방**이었다.\
**24 이상에서는 그 처방이 필요 없다.** 다만 **클래스 초기화·네이티브 호출은 여전히 고정한다.**

### (5-1) 고정을 어떻게 보나 — 도구가 판마다 다르다

**언제 쓰나** — "고정이 있나"를 확인할 때. **플래그 이름부터 판이 다르다.**

**실행 결과** (`Ex.java` — 56-e, JDK 21.0.5, `-Djdk.tracePinnedThreads=full`)

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

**JDK 25 에서 같은 플래그를 주면**

```text
===== 25: -Djdk.tracePinnedThreads=full
  synchronized   5회: [201, 201, 200, 200, 200] → 중앙값 200 ms
===== 25: jdk.traceVirtualThreadPinnedEvents
  synchronized   5회: [200, 200, 200, 200, 200] → 중앙값 200 ms
```

- **25 에서는 두 플래그 다 아무것도 안 찍는다.** (5) 에서 본 **클래스 초기화 고정이 실제로 있는데도** 안 찍는다.

**25 에서 고정을 보는 방법 — JFR 이벤트**

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

**21 의 같은 JFR 이벤트**

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

```text
JDK 21                                     JDK 25

  -Djdk.tracePinnedThreads=full/short        그 플래그는 아무것도 안 찍는다
    -> 콘솔에 reason:MONITOR / reason:NATIVE
  JFR jdk.VirtualThreadPinned 있음           JFR jdk.VirtualThreadPinned 있음
    필드: startTime, duration,                 필드가 늘었다:
          eventThread, stackTrace                blockingOperation, pinnedReason,
                                                 carrierThread 까지
```

그림 해설 (한 단계씩):

- **`-Djdk.tracePinnedThreads` 는 21 에서만 콘솔에 찍는다.** 25 에서는 고정이 있어도 침묵한다.
- **`jdk.traceVirtualThreadPinnedEvents` 도 25 에서 콘솔 출력이 없었다.**
- **양쪽 다 JFR 이벤트 `jdk.VirtualThreadPinned` 는 있다.** 25 쪽이 **필드가 훨씬 풍부**하다 —\
  `pinnedReason = "VM call to Ex$C0.<clinit> on stack"` 이 원인을 문장으로 말해 준다.
- ★ **그래서 "플래그가 있는지부터 확인"해야 한다.** 판마다 다르다.

비용 — **25 에서는 JFR 로 본다.** `-XX:StartFlightRecording=filename=x.jfr,settings=profile` 뒤 `jfr print --events jdk.VirtualThreadPinned x.jfr`.

### (6) `ThreadLocal` 의 비용이 바뀐다

**언제 쓰나** — 기존 코드에 `ThreadLocal` 이 있을 때.

**실행 결과** (`Ex.java` — 56-h, 8KB 버퍼를 `ThreadLocal` 에 두고 N개가 동시에 대기, `-Xmx8g`, JDK 21.0.5)

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

**플랫폼 고정 풀에서는 사본이 몇 개인가** (`Ex.java` — 56-i, 같은 8KB `ThreadLocal`, 작업 10만 개)

```text
--- 플랫폼 고정 풀에서 ThreadLocal 사본은 몇 개가 되나
  풀 크기   200 으로 작업 100,000개 처리 뒤 힙    3 MB  (8KB x 200 = 1 MB 어치가 살아 있다)
           풀을 닫은 뒤 힙    1 MB
  풀 크기 2,000 으로 작업 100,000개 처리 뒤 힙   18 MB  (8KB x 2,000 = 15 MB 어치가 살아 있다)
           풀을 닫은 뒤 힙    1 MB
```

```text
플랫폼 고정 풀 200 (작업 10만 개)           가상 스레드 10만 개 동시 대기

  사본 = 스레드 수 = 200                     사본 = 동시 작업 수 = 100,000
  힙 3 MB                                   힙 876 MB (없을 때 75 MB)
        |                                          |
        v                                          v
  작업이 10만이어도 사본은 200                 차이 801 MB
```

그림 해설 (한 단계씩):

- **`ThreadLocal` 은 가상 스레드에서도 그냥 동작한다.** 문법이 바뀌지 않는다.
- **바뀐 것은 "살아 있는 스레드 수"다.**\
  풀 200 이면 사본도 200개(힙 3 MB), 가상 스레드 10만 개면 **사본도 10만 개(힙 876 MB)** 다.
- **`InheritableThreadLocal` 은 기본으로 상속된다.** `inheritInheritableThreadLocals(false)` 로 끌 수 있다.
- **`Thread.Builder.OfVirtual` 에 `allowSetThreadLocals` 는 없다**(리플렉션으로 확인 — `false`).\
  21 의 공개 API 표면에는 그 스위치가 없다.
- 대안은 **`ScopedValue`** 다 — 21 에서는 프리뷰, **25 에서 확정**(`src.zip` 에서 `@PreviewFeature` 가 사라지고 `@since 25` 로 바뀐 것을 확인했다).

비용 — **캐싱 용도의 `ThreadLocal`(버퍼 재사용 등)은 가상 스레드에서 의미가 거꾸로 된다.**\
스레드가 한 작업만 하고 죽으므로 **재사용이 없고 사본만 늘어난다.**

### (7) 21 과 25 에서 다시 돌려 본 것 — 무엇이 같고 무엇이 달랐나

**언제 쓰나** — "버전을 올리면 무엇이 달라지나"를 판단할 때.

고정 실험((5))만 갈린 것이 아니라, **안 갈린 것도 확인**해야 결론이 선다.

**실행 결과** (`Ex.java` — 56-a, JDK 25.0.1 — 21 과 같은 프로그램)

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

- **21 의 출력과 다른 것은 스레드 id 하나뿐**이다(`#31` 대 `#38`). 나머지는 한 글자도 같았다.\
  id 는 JVM 이 그때까지 만든 스레드 수에 따라 달라지므로 **비교 대상이 아니다.**

**실행 결과** (`Ex.java` — 56-c, JDK 25.0.1, 워밍업 2 + 측정 5의 중앙값)

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

```text
블로킹 (21 -> 25)                           CPU 바운드 (21 -> 25)

  고정 풀 16    6,317 -> 6,318 ms            고정 풀 24     97 ->  85 ms
  고정 풀 200     521 ->   515 ms            고정 풀 200   123 ->  99 ms
  고정 풀 2000    269 ->   226 ms            가상 스레드     88 ->  99 ms
  가상 스레드       22 ->    21 ms                  |
        |                                           v
        v                                   ★ 21 에서는 가상이 이겼고(88<97)
  결론이 그대로다 — 두 자릿수 차이             25 에서는 졌다(99>85)
                                             둘 다 "차이가 없다"는 같은 결론이다
```

그림 해설 (한 단계씩):

- **블로킹 결론은 두 버전이 같다.** 가상 스레드가 **21 ms / 22 ms** 로 하한(10 ms)에 가장 가깝다.
- ★ **CPU 바운드에서는 부호가 뒤집혔다.** 21 에서는 가상이 **88 대 97** 로 근소하게 이겼고,\
  25 에서는 **99 대 85** 로 졌다.
- **그래서 "가상 스레드가 CPU 작업에서 몇 % 빠르다/느리다"는 말을 쓸 수 없다.**\
  두 버전에서 방향이 바뀌는 크기라면 그것은 **차이가 아니라 잡음**이다.\
  두 버전이 함께 말하는 것은 하나다 — **CPU 바운드에는 값이 없다.**

**실행 결과** (`Ex.java` — 56-b, JDK 25.0.1, `-Xmx2g`, 각 1회)

```text
===== 25 / virtual 1000000
  virtual 스레드 1,000,000개 생성 성공 — 989 ms
  동시에 sleep(2000) 중이던 개수 : 1,000,000
===== 25 / platform 10000
  platform 스레드 10,000개 생성 성공 — 987 ms
  동시에 sleep(2000) 중이던 개수 : 10,000
```

- 25 에서도 **가상 스레드 100만 개가 989 ms** 에 만들어졌다(21 은 604 ms).\
  **자릿수는 같다.** 플랫폼 스레드 1만 개는 21 에서 1,291 ms, 25 에서 987 ms 로 역시 같은 자릿수다.

비용 — **버전을 올려도 판단 기준은 안 바뀐다.** 바뀐 것은 **`synchronized` 를 먼저 걷어낼 필요가 있는가** 하나다((5)).

## 문법 — 형태와 규칙

### 만드는 법 셋

```java
// ① 빌더 — 이름·상속 옵션을 준다
Thread t = Thread.ofVirtual().name("worker-", 0).unstarted(() -> work());
t.start();
t.join();

// ② 만들고 바로 시작
Thread.startVirtualThread(() -> work());

// ③ ExecutorService 로 — 기존 코드와 같은 모양
try (ExecutorService es = Executors.newVirtualThreadPerTaskExecutor()) {
    for (var req : requests) es.submit(() -> handle(req));
}   // close() 가 전부 끝날 때까지 기다린다
```

- **③이 기본형이다.** `try`-with-resources 로 감싸면 **전부 끝날 때까지 기다린다**\
  ([`../54-executorservice-and-future/`](../54-executorservice-and-future/) 의 `close()` 규칙 그대로. **`@since 19`**).
- **①·②는 데몬이라** `join()` 하지 않으면 `main` 이 끝날 때 잘린다.

### 플랫폼 스레드와 다른 점

| | 플랫폼 스레드 | 가상 스레드 |
|---|---|---|
| `isDaemon()` | `false`(기본) | **항상 `true`** — `setDaemon(false)` 는 `IllegalArgumentException` |
| `getPriority()` | 1~10 | **항상 5** — `setPriority` 가 무시된다 |
| `getThreadGroup()` | `main` 등 | **`VirtualThreads`** |
| 기본 이름 | `Thread-0` | **빈 문자열** |
| `toString()` | `Thread[#21,Thread-0,5,main]` | `VirtualThread[#31]/runnable@ForkJoinPool-1-worker-1` |
| `ThreadLocal` | 된다 | 된다(사본 수가 다르다) |
| 풀링 | 이득 | **이득 없음** |

### 동시성을 제한하고 싶으면

```java
Semaphore db = new Semaphore(20);          // DB 커넥션이 20개뿐이라면
try (ExecutorService es = Executors.newVirtualThreadPerTaskExecutor()) {
    for (var req : requests) es.submit(() -> {
        db.acquire();
        try { query(req); } finally { db.release(); }
    });
}
```

- **풀 크기로 제한하지 않는다.** 제한이 필요한 자원마다 `Semaphore` 를 둔다.
- 풀은 "재활용"과 "제한"을 겸하는데, 가상 스레드에는 **제한만** 필요하다.

### 고정을 보는 명령

```text
JDK 21 : java -Djdk.tracePinnedThreads=full   ...   (콘솔에 reason:MONITOR / reason:NATIVE)
JDK 25 : java -XX:StartFlightRecording=filename=p.jfr,settings=profile ...
         jfr print --events jdk.VirtualThreadPinned p.jfr
```

- ★ **플래그가 있는지부터 확인한다.** 25 에서 `-Djdk.tracePinnedThreads` 는 조용히 아무 일도 안 한다.

## 어디서 틀리나

### 1. CPU 바운드 작업을 가상 스레드로 옮긴다

- (3) 의 실측 — **88 대 97 ms.** 같은 자릿수다.
- 계산은 코어 수가 상한이다. 병렬 스트림이나 코어 수만큼의 고정 풀이 맞다\
  ([`../49-parallel-streams/`](../49-parallel-streams/)).

### 2. 가상 스레드를 풀링한다

- (4) 의 실측 — 만드는 비용이 **고정 풀에 제출하는 것보다 싸다**(450 대 745 ms).
- 풀에 넣는 순간 **풀 크기가 동시성 상한**이 되어 이유가 사라진다.

### 3. `main` 에서 `join` 을 안 한다

- 가상 스레드는 **항상 데몬**이다. (1) 의 실측에서 3초짜리 작업의 출력이 안 찍혔다.
- `ExecutorService` 의 `close()` 를 쓰거나 `join()` 한다.

### 4. JDK 21 에서 `synchronized` 안에서 블로킹한다

- (5) 의 실측 — **200 → 1,601 ms.** 캐리어 수만큼으로 동시성이 줄어든다.
- 21 에서는 **`ReentrantLock` 으로 바꾼다.** 24 이상에서는 필요 없다.

### 5. "JDK 24에서 고쳤으니 고정은 없다"고 생각한다

- (5) 의 실측 — **클래스 초기화 안의 블로킹은 25 에서도 809 ms** 로 줄선다.
- JEP 491 이 없앤 것은 **모니터**다. **네이티브 프레임은 그대로다.**

### 6. `-Djdk.tracePinnedThreads` 로 25 에서 고정을 찾는다

- (5-1) 의 실측 — **고정이 실제로 있는데 아무것도 안 찍힌다.**
- **JFR `jdk.VirtualThreadPinned`** 를 쓴다.

### 7. `ThreadLocal` 을 캐시로 쓴다

- (6) 의 실측 — 10만 개 동시 대기에서 **801 MB 차이**.
- 가상 스레드는 **한 작업만 하고 죽으므로 재사용이 없다.** 사본만 늘어난다.

### 8. 스레드 수로 부하를 제한하던 코드를 그대로 둔다

- 풀 크기가 자연스러운 상한이었던 곳(DB 커넥션·외부 API 호출)이 **상한을 잃는다.**
- `Semaphore` 로 **자원마다** 제한한다.

### 9. 우선순위로 작업을 조절한다

- (1) 의 실측 — `setPriority(10)` 뒤에도 `5` 다. **예외도 안 난다.**

### 10. 17 로 내려서 빌드한다

- (1) 의 실측 — **`cannot find symbol: method ofVirtual()`**. 컴파일부터 안 된다.

### 11. "가상 스레드로 바꿨는데 안 빨라졌다"를 API 탓으로 본다

- (3) 의 소켓 실측 — 풀 500 과 **거의 차이가 없었다**(366 대 315 ms).
- **병목이 내 스레드가 아니면** 바꿔도 그대로다. 먼저 병목을 찾는다.

### 12. 가상 스레드 스케줄러를 공용 ForkJoinPool 과 같은 것으로 본다

- (1) 의 실측 — 캐리어 이름이 **`ForkJoinPool-1-worker-N`** 이다.\
  공용 풀은 **`ForkJoinPool.commonPool-worker-N`** 이다([`../49-parallel-streams/`](../49-parallel-streams/)). **다른 풀이다.**

## 구현 세부사항 대 언어 보장

| 관측한 것 | 누가 보장하나 | 버전에 갈리나 |
|---|---|---|
| `Thread.ofVirtual()`·`startVirtualThread`·`isVirtual` 의 존재 | **javadoc — `@since 21`** | ★ 17 에서 컴파일 에러 |
| 가상 스레드가 데몬인 것, 우선순위가 무시되는 것 | **javadoc 이 명시** | 21·25 동일 |
| `setDaemon(false)` 의 메시지 `'false' not legal for virtual threads` | **구현 세부** | 21 에서만 확인 |
| `toString` 이 `VirtualThread[#N]/상태@캐리어` 인 것 | **구현 세부** | 21 에서만 확인 |
| 캐리어 수가 `availableProcessors` 인 것 | **구현 세부.** 시스템 속성으로 바꿀 수 있다 | 21 에서 확인 |
| 캐리어 풀 이름이 `ForkJoinPool-1-worker-N` 인 것 | **구현 세부** | 21 에서 확인 |
| ★ **`synchronized` 가 캐리어를 고정하는 것** | **JEP 444 가 21의 한계로 명시, JEP 491(24)이 제거** | ★★ **갈린다 — 21 은 1,601 ms, 25 는 200 ms** |
| `Object.wait` 가 고정하는 것 | 위와 같다 | ★ **갈린다 — 21 은 1,602 ms, 25 는 200 ms** |
| **클래스 초기화 블록 안의 블로킹이 고정하는 것** | JEP 444 가 "native method or foreign function" 을 든다 | **21·25 모두 고정**(808·809 ms) |
| `-Djdk.tracePinnedThreads` 가 콘솔에 찍는 것 | **구현 세부·진단 플래그** | ★ **갈린다 — 25 에서는 아무것도 안 찍는다** |
| JFR `jdk.VirtualThreadPinned` 이벤트 | 이벤트는 양쪽 다 있다 | ★ **필드가 갈린다 — 25 에만 `pinnedReason`·`blockingOperation`·`carrierThread`** |
| `StructuredTaskScope` 가 프리뷰인 것 | `src.zip` 의 `@PreviewFeature` | **21·25 모두 프리뷰** |
| `ScopedValue` 의 상태 | `src.zip` 의 애너테이션·`@since` | ★ **갈린다 — 21 프리뷰, 25 확정(`@since 25`)** |
| 생성 비용·처리 시간 수치 | **아무도 보장 안 한다** | ★ **CPU 바운드의 부호가 뒤집혔다** — 21 은 88 대 97(가상 승), 25 는 99 대 85(가상 패) |
| 만드는 법·데몬·우선순위·캐리어 수의 출력 | 위 항목들과 같다 | **21·25 에서 스레드 id 말고 한 글자도 안 달랐다**(관찰이지 보장 아님) |

★ **이 주제는 "세 버전에서 같았다"가 성립하지 않는다.** 17 에서는 컴파일이 안 되고, 21 과 25 는 **실제로 갈렸다.**

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 요청마다 DB·외부 API 를 블로킹 호출 | **가상 스레드** | 실측 287배(sleep 기준). 여기가 자리다 |
| 동시 접속 수만 건을 스레드로 받는다 | **가상 스레드** | 100만 개를 604 ms 에 만들었다 |
| CPU 만 쓰는 계산 | **고정 풀(코어 수) 또는 병렬 스트림** | 88 대 97 ms — 이득이 없다 |
| 짧은 작업을 아주 많이 던진다 | 고정 풀도 괜찮다 | 생성 비용이 싸도 0은 아니다 |
| DB 커넥션이 20개뿐이다 | **가상 스레드 + `Semaphore(20)`** | 풀 크기로 제한하지 않는다 |
| `synchronized` 가 많은 레거시 (JDK 21) | **`ReentrantLock` 으로 바꾼 뒤** 가상 스레드 | 안 바꾸면 캐리어 수만큼으로 줄어든다 |
| `synchronized` 가 많은 레거시 (JDK 24+) | 그대로 가상 스레드 | JEP 491 이 고정을 없앴다 |
| `ThreadLocal` 캐시가 많은 코드 | 먼저 `ThreadLocal` 을 걷어낸다 | 10만 개 동시 대기에서 801 MB 차이 |
| JDK 17 을 써야 한다 | **못 쓴다** | 컴파일부터 안 된다 |
| 병목이 DB·네트워크 대역폭이다 | **바꿔도 그대로다** | 소켓 실측에서 풀 500 과 차이가 없었다 |

## 핵심 문장

- **가상 스레드는 블로킹할 때만 값이 있다.** CPU 바운드에서는 88 대 97 ms — 차이가 없다.
- **풀링하지 않는다.** 만드는 비용이 풀에 제출하는 비용보다 쌌다(450 대 745 ms).
- **★ JDK 21 에서 `synchronized` 는 캐리어를 붙잡는다.** 같은 코드가 21 에서 1,601 ms, 25 에서 200 ms.
- **24에서 고쳤어도 고정이 다 사라진 건 아니다.** 클래스 초기화는 25 에서도 809 ms 로 줄선다.
- **진단 플래그가 판마다 다르다.** 25 에서 `-Djdk.tracePinnedThreads` 는 침묵한다 — JFR 로 본다.
- **`ThreadLocal` 의 사본 수는 "동시에 살아 있는 스레드 수"다.** 10만 개면 10만 개다.

## 관련 자료

- [`../54-executorservice-and-future/`](../54-executorservice-and-future/) — `ExecutorService`·`Future`·풀 크기.\
  그쪽은 **풀을 어떻게 만들고 닫나**까지, 여기는 **그 풀 크기라는 질문을 없애는 법**부터.\
  `close()`(`@since 19`) 규칙은 그쪽이 정본이다.
- [`../33-synchronized-and-volatile/`](../33-synchronized-and-volatile/) — `synchronized` 의 문법과 잠금 대상.\
  그쪽은 **키워드가 무엇을 보장하나**까지, 여기는 **그 키워드가 가상 스레드에서 무엇을 막나**부터.\
  ★ **이 주제에서 그 키워드의 동작이 버전에 따라 갈린다.**
- [`../49-parallel-streams/`](../49-parallel-streams/) — 공용 ForkJoinPool 과 CPU 바운드 병렬화.\
  ★ 가상 스레드 스케줄러는 **별도의 `ForkJoinPool`** 이다(캐리어 이름으로 확인).\
  **CPU 바운드 작업은 그쪽이 정본**이고 여기는 **블로킹 작업**이 자리다.
- [`../55-atomics-and-concurrent-collections/`](../55-atomics-and-concurrent-collections/) — 스레드가 수만 개일 때의 자료구조 선택.
- [`../26-try-with-resources/`](../26-try-with-resources/) — `ExecutorService` 를 `try` 로 감싸는 형태의 근거.
- [`../../../../process-thread/`](../../../../process-thread/) — **OS 스레드와 스케줄링이 정본이다.**\
  그쪽은 **컨텍스트 스위칭이 무엇인가**까지, 여기는 **자바가 그 위에 무엇을 얹었나**부터.
- [`../../../../../../history/java/java-21.md`](../../../../../../history/java/java-21.md) — **가상 스레드가 왜 들어왔나가 정본이다.**\
  JEP 번호·설계 논쟁·Loom 의 역사는 그쪽. 여기는 **어떻게 쓰고 무엇을 못 하나**.
- [`../../언어-특성/README.md`](../../언어-특성/README.md) — JIT·GC·메모리 모델. 가상 스레드의 스택이 힙에 있다는 사실의 배경.

## 용어 풀이

- **가상 스레드(virtual thread)** — JVM 이 관리하는 가벼운 스레드. `@since 21`. OS 스레드가 아니다.
- **캐리어 스레드(carrier thread)** — 가상 스레드를 실제로 실행하는 OS 스레드. 기본은 코어 수만큼.
- **마운트(mount) / 마운트 해제(unmount)** — 가상 스레드가 캐리어에 올라가고 내려오는 것.
- **고정(pinning)** — 마운트 해제가 안 되어 블로킹 중에도 캐리어를 붙잡는 상태.
- **JEP 444** — 가상 스레드를 확정한 JDK 21 의 제안.
- **JEP 491** — `synchronized` 의 고정을 없앤 JDK 24 의 제안.
- **`jdk.VirtualThreadPinned`** — 고정을 기록하는 JFR 이벤트. 25 쪽 필드가 더 많다.
- **JFR(Java Flight Recorder)** — JVM 내장 기록 도구. `jfr print` 로 읽는다.
- **`Semaphore`** — 동시에 들어갈 수 있는 수를 세는 자물쇠. 가상 스레드에서 풀 크기를 대신한다.
- **`ScopedValue`** — `ThreadLocal` 의 대안. **21 프리뷰, 25 확정**.
- **`StructuredTaskScope`** — 부모-자식 동시 작업 묶음. **21·25 모두 프리뷰**.
- **`InheritableThreadLocal`** — 자식 스레드가 부모 값을 물려받는 `ThreadLocal`. 가상 스레드에서도 기본으로 상속된다.

## 더 들어가면

- **`jdk.virtualThreadScheduler.parallelism` / `maxPoolSize`** — 캐리어 수를 바꾸는 시스템 속성.\
  이 문서의 고정 실험이 이것을 1로 묶어 **"줄서면 8배"**가 보이게 만들었다. **운영에서 건드릴 것은 아니다.**
- **`ScopedValue`**(25 확정) — 값을 **범위**에 묶는다. 불변이고, 자식 작업에 자동으로 전달된다.\
  `ThreadLocal` 과 달리 **사본이 스레드마다 생기지 않는다.** 이 문서는 **측정하지 않았다.**
- **`StructuredTaskScope`**(21·25 프리뷰) — 자식 작업의 수명을 부모 범위에 묶는다.\
  하나가 실패하면 형제를 취소하는 패턴이 기본형이다. **확정 문법만 다루는 방침상 이름만 적는다.**
- **JEP 491 이 어떻게 고쳤나** — 모니터를 캐리어가 아니라 가상 스레드에 귀속시켰다.\
  **설계 논쟁은 [`../../../../../../history/java/java-21.md`](../../../../../../history/java/java-21.md) 와 JEP 본문이 정본이다.**
- **스레드 덤프** — `jcmd <pid> Thread.dump_to_file -format=json out.json` 이 가상 스레드까지 찍는다.\
  이 문서는 **그 출력을 확인하지 않았다.**
