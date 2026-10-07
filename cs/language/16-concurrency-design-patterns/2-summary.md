# language/16-concurrency-design-patterns — 스레드 풀·Future 합성·Active/Monitor Object·Scoped Locking·TSS·DCL·불변 스냅샷 — 정리 (힌트)

## 해결하는 문제

요청마다 스레드를 새로 만들고, 공유 객체를 각자 알아서 잠그면 세 가지가 무너진다.

```text
  요청 → new Thread() → 공유 객체를 직접 lock()/unlock()
         │                 │
         │                 └─ 예외 경로에서 unlock 누락 → 다음 요청이 영원히 대기
         └─ 몰리면 스레드 수만큼 스택·문맥 교환 → 메모리·CPU 고갈
  결과 → 비동기 작업의 예외가 어디로도 안 감 → 조용한 실패
```

- 동시성 설계 패턴은 이 반복 문제에 **이름 붙은 해법**을 준다.
  - *패턴(pattern)*: 자주 나오는 문제와 그 해법의 구조를 이름으로 묶은 것. 코드 조각이 아니라 역할 배치다.
- 이 노트가 다루는 패턴의 출처는 둘이다.
  - Schmidt·Stal·Rohnert·Buschmann, POSA2(Wiley, 2000): 17개 패턴. 이 중 동기화 패턴(Scoped Locking·Double-Checked Locking Optimization 등)과 동시성 패턴(Active Object·Monitor Object·Thread-Specific Storage 등)을 쓴다(저자 사이트 목차 4·5장).
  - Java 표준 라이브러리 `java.util.concurrent`: Executor·스레드 풀·`CompletableFuture`가 위 패턴의 실물 구현이다.

쉬운 예: 식당 주방이다.
- 주문서는 꽂이(큐)에 꽂힌다. 요리사(워커) 몇 명이 꽂이에서 하나씩 뽑아 요리한다.
- 꽂이가 꽉 차면 홀 직원이 "지금은 주문을 못 받습니다"라고 말한다(거부 정책).
- 요리가 끝나면 진동벨(Future)이 울린다.

똑같은 구조다.\
`ThreadPoolExecutor` = 꽂이(블로킹 큐) + 요리사(워커 스레드) + 홀 직원(거부 정책), `Future` = 진동벨이다.

실무 예:
- 외부 결제 API 호출을 `CompletableFuture.supplyAsync`로 돌렸더니, 그 API가 느려진 날 캐시 조회 같은 가벼운 비동기 작업까지 다 늦어졌다.
- 로그인 사용자 정보를 `ThreadLocal`에 넣는 필터가 있었는데, 익명 요청에 앞 사람의 사용자 ID가 찍혔다.
- 트래픽이 몰린 뒤 힙이 계속 차오르다 `OutOfMemoryError: Java heap space`로 죽었다. 힙 덤프의 최대 점유는 스레드 풀의 `LinkedBlockingQueue`였다.

## 동작·원리

### 1. 패턴 지도

```text
                 호출자(요청 스레드)
                     │ submit / supplyAsync
                     ▼
   ┌─────────── Executor (Active Object의 스케줄러 역할) ─────────────┐
   │  [블로킹 큐] ─take→ 워커1 ─┐                                      │
   │   ▲ 가득 차면 거부 정책    워커2 ─┼→ 공유 객체 (Monitor Object)   │
   │                            워커N ─┘   └ 잠금은 블록 수명 = Scoped Locking
   │  워커마다 따로 가진 칸 = Thread-Specific Storage (ThreadLocal)      │
   └────────────────────────────────────────────────────────────────────┘
                     │ 결과·예외
                     ▼
            Future / CompletableFuture  ── thenApply → thenCompose → whenComplete
                                            (완료 콜백 사슬)
   읽기가 많은 공유 설정 = 불변 스냅샷 + 참조 하나 원자 교체 (락 없이 읽기)
   지연 초기화 = Double-Checked Locking (volatile 없으면 깨짐)
```

- 패턴들은 따로 쓰이지 않는다. 한 요청 경로에 거의 다 들어 있다.
- 아래 절은 이 그림의 칸을 하나씩 연다.

### 2. Executor = 블로킹 큐 + 워커

`ThreadPoolExecutor.execute()`는 작업이 들어올 때 이렇게 판단한다(Java 21 API 문서 "Queuing").

```text
  execute(task)
     │
     ├─ 실행 중 스레드 < corePoolSize ?  ── 예 → 새 스레드를 만들어 바로 실행
     │
     ├─ 큐에 넣을 수 있나 (offer) ?      ── 예 → 큐에서 대기
     │
     ├─ 스레드 < maximumPoolSize ?      ── 예 → 새 스레드
     │
     └─ 아니오 → 거부 정책(RejectedExecutionHandler)
```

- *corePoolSize / maximumPoolSize*: 평소 유지할 스레드 수 / 최대 스레드 수.
  - 흔한 오해: "max를 키우면 바쁠 때 스레드가 늘어난다." 큐에 먼저 넣으므로, 큐가 무한이면 스레드는 core를 넘지 않는다. 문서도 무한 큐에서는 "corePoolSize보다 많은 스레드는 만들어지지 않고 maximumPoolSize는 아무 효과가 없다"고 적는다.
- 큐 전략 세 가지(같은 문서)

| 전략 | 예 | 장점 | 위험 |
|---|---|---|---|
| 직접 전달 | `SynchronousQueue` | 서로 기다리는 작업도 막히지 않음 | 스레드가 끝없이 늘 수 있음 |
| 무한 큐 | 용량 없는 `LinkedBlockingQueue` | 순간 몰림을 흡수 | **큐가 끝없이 자람** |
| 유한 큐 | `ArrayBlockingQueue` | 자원 고갈 방지 | 크기 조율이 어려움 |

- 거부 정책 네 가지(같은 문서)
  - `AbortPolicy`(기본): `RejectedExecutionException`을 던진다.
  - `CallerRunsPolicy`: 제출한 스레드가 직접 실행한다(풀이 종료되지 않은 경우 — 종료 뒤엔 그냥 버린다). 제출 속도가 저절로 느려지는 "간단한 피드백 제어"다.
  - `DiscardPolicy`: 조용히 버린다. 문서는 "완료에 의존하지 않는 드문 경우"에만 쓰라고 한다.
  - `DiscardOldestPolicy`: 큐 맨 앞을 버리고 다시 시도한다. 문서는 "거의 받아들일 수 없다"고 적는다.
- `Executors.newFixedThreadPool(n)`은 "공유 무한 큐" 위에서 도는 고정 크기 풀이다(Java 21 `Executors` 문서).

### 실험 1: 무한 큐 vs 유한 큐 + 거부 (`PoolQueue.java`)

작업 하나 = 16KB 요청 본문을 붙든 채 10ms 걸리는 작업. 워커 2개, 제출은 최대 속도.\
환경: `eclipse-temurin:21-jdk`, `--cpus=2`, `-Xmx64m`. 집필 4회(무한)·2회(유한) + 점검 재실행 3회·2회를 합친 범위다(호스트 부하에 따라 달라진다).

```text
  == newFixedThreadPool(2) — 무한 큐
  queue class = LinkedBlockingQueue, remainingCapacity = 2147483647
  submitted=1000 queue=990  heapUsed=28MB t=47ms
  submitted=2000 queue=1982 heapUsed=39MB t=105ms
  submitted=3000 queue=2978 heapUsed=57MB t=142ms                   (3,000건 시점 t=125~163ms)
  caught: java.lang.OutOfMemoryError: Java heap space queue=3816     (7회: 3,767~3,822)

  == ThreadPoolExecutor(2, 2, ArrayBlockingQueue(100)) — 2000건 제출
  abort:      rejected=1880~1886 completed=114~120  maxQueue=100 elapsed=589~629ms
  callerruns: rejected=0         completed=1369~1370 maxQueue=100 elapsed=6952~6963ms
```

- 무한 큐: 0.15초 남짓 만에 큐가 3,800개 안팎까지 자랐고 힙이 바닥났다. 그동안 **거부도 경고도 없었다.**
- `AbortPolicy`: 큐(100)가 차는 순간부터 거부했다. 2,000건 중 1,880~1,886건이 예외로 돌아왔다. 호출자가 "지금 바쁘다"를 즉시 안다.
- `CallerRunsPolicy`: 거부 0건. 풀이 약 1,370건, 나머지 약 630건은 제출 스레드가 직접 돌렸다. 제출 스레드가 일하는 동안 제출이 멈추므로 큐는 100을 넘지 않았다. 대신 총 시간이 약 7초로 늘었다(약 2,000건 × 10ms ÷ 3스레드).
- 해석: 무한 큐는 "과부하"를 "메모리 사용량"으로 바꿀 뿐이다. 과부하를 호출자에게 알리는 쪽(거부·역압)을 골라야 한다. 역압 일반론은 [reliability/12-backpressure-and-load-shedding](../../reliability/12-backpressure-and-load-shedding/2-summary.md).

### 3. 풀 크기 — CPU 시간과 대기 시간의 비

```text
  스레드 하나가 작업 하나에 쓰는 시간 = CPU(C) + 대기(W: I/O·락·원격 호출)
  CPU 코어 N개를 계속 바쁘게 하려면, 대기 중인 스레드 몫까지 더 둔다
     스레드 수 ≈ N × (1 + W/C)        ← JCIP 8장 "Applying Thread Pools"의 크기 공식으로 알려진 형태 (식 세부·절 번호 본문 미대조 [?])
```

### 실험 2: 풀 크기별 처리량 (`Sizing.java`)

작업 400개, 작업마다 CPU 바쁜 대기 2ms + `sleep` 18ms(대기 흉내). W/C = 9, 코어 2 → 공식으로 약 20.\
환경: `--cpus=2`(JVM `availableProcessors=2`), 집필 3회 + 점검 2회.

```text
  pool= 2  elapsed= 4039~4081ms  throughput=  98~99 tasks/s
  pool= 4  elapsed= 2014~2016ms  throughput= 198~199
  pool=10  elapsed=  807~809ms   throughput= 494~495
  pool=20  elapsed=  415~426ms   throughput= 939~964
  pool=40  elapsed=  377~413ms   throughput= 969~1061
  pool=80  elapsed=  393~458ms   throughput= 873~1018
```

- 20까지는 스레드에 비례해 늘었다(작업 하나 20ms → 스레드 하나가 초당 50개).
- 20 이후로는 거의 늘지 않았다. CPU 두 개가 상한이다(이론상 2코어 ÷ 2ms = 초당 1,000).
- 40·80은 실행마다 초당 870~1,060 사이를 오르내렸고, 둘 중 어느 쪽이 나은지도 실행마다 바뀌었다. 상한 근처에서는 스케줄링·문맥 교환이 결과를 흔든다(해석).
- 1,000을 약간 넘은 실행은 "CPU 2ms"를 벽시계 바쁜 대기로 흉내 냈기 때문이다. 경합 중에는 스레드가 실제 CPU를 덜 쓰고도 2ms가 지난다(해석).
- 교훈: 크기는 감이 아니라 **W/C를 재서** 정한다. 대기가 큰 작업과 CPU 작업은 **풀을 나눈다**(Bulkhead, [reliability/28-bulkhead](../../reliability/28-bulkhead/2-summary.md)).

### 4. Future/Promise 합성 — 완료 콜백 사슬

```text
  supplyAsync(조회) ──완료──> thenApply(변환) ──완료──> thenCompose(다음 비동기) ──> whenComplete(기록)
        │                          │
        └ 예외가 나면 정상 결과가 필요한 단계(thenApply·thenCompose)는 건너뛰고,
          "예외적 완료" 상태가 사슬을 따라 내려간다. whenComplete·exceptionally는 예외를 받아 실행된다
          끝에서 아무도 안 받으면 → 어디에도 안 찍힌다
```

- *Future*: 아직 안 끝난 계산의 결과를 나중에 받는 손잡이. *Promise*: 그 결과를 채우는 쪽. Java `CompletableFuture`는 둘을 겸한다.
- 구현: `CompletableFuture`는 뒤에 매달린 작업들을 Treiber 스택(CAS로 쌓는 연결 스택)으로 들고 있다가, 완료 순간에 꺼내 실행한다(OpenJDK 21 `CompletableFuture.java` 필드 `stack` 주석).
- **기본 실행기**: executor를 안 받는 `*Async` 메서드는 `ForkJoinPool.commonPool()`에서 돈다. `thenApply` 같은 비동기형이 아닌 단계는 앞 단계를 완료한 스레드나 완료 메서드를 부른 스레드에서 돌 수 있다. 단, 공용 풀 병렬도가 2 미만이면 **작업마다 새 스레드**를 만든다(Java 21 `CompletableFuture` 문서, 소스 `USE_COMMON_POOL = getCommonPoolParallelism() > 1`).
- 공용 풀 병렬도 기본값 = `availableProcessors() - 1`, 최소 1(OpenJDK 21 `ForkJoinPool.java`).

### 실험 3: 공용 풀에서 블로킹 (`CommonPoolBlock.java`)

500ms 블로킹 작업 8개를 `supplyAsync`로 띄우고, 바로 뒤에 가벼운 작업 하나를 띄운다.\
환경: `--cpus=2`, `-XX:ActiveProcessorCount`로 JVM이 보는 코어 수만 바꿈, 집필 각 2회 + 점검 각 2회(전용 풀 1회씩).

```text
  availableProcessors=2 commonPoolParallelism=1 executor=default
    light task waited 1~2ms     8 blocking tasks done in 506~508ms   threads=[Thread-N]
  availableProcessors=4 commonPoolParallelism=3 executor=default
    light task waited 1001~1002ms   8 blocking tasks done in 1506~1551ms threads=[ForkJoinPool.commonPool-worker-N]
  availableProcessors=4 executor=dedicated fixed(8)
    light task waited 2~3ms     8 blocking tasks done in 506ms       threads=[pool-1-thread-N]
```

- 코어 4개로 보이면 공용 풀 워커는 3개다. 블로킹 8개가 3개씩 차례로 돌아 약 1.5초가 걸렸다.
- 그 뒤에 들어온 가벼운 작업은 **1초를 기다렸다.** 같은 JVM의 다른 `supplyAsync`·병렬 스트림도 같은 풀을 쓴다.
- 코어 2개로 보이면 병렬도 1이라 작업마다 새 스레드(`Thread-N`)가 떴다. 그래서 0.5초에 끝났다. **개발 PC·작은 컨테이너에서는 안 보이던 정지가, 코어가 많은 서버에서 나타날 수 있다**는 뜻이다.
- 블로킹 작업용 전용 풀을 주면 다른 작업에 영향이 없었다.

### 실험 4: 예외가 사라지는 길 (`Silent.java`)

```text
  1) submit(): 결과 Future를 아무도 get() 하지 않음      → (출력 없음)
  2) execute(): 같은 작업
     Exception in thread "pool-1-thread-1" java.lang.IllegalStateException: ledger write failed
  3) CompletableFuture.runAsync(), 체인 끝에 처리 없음   → (출력 없음, thenRun도 안 돎)
  4) 같은 체인 + whenComplete로 실패를 기록
     logged: java.util.concurrent.CompletionException: java.lang.IllegalStateException: ledger write failed
  done                                                   → 프로세스 exit 0
```

- `submit`·`CompletableFuture`는 예외를 결과 객체 안에 담는다. 아무도 꺼내지 않으면 **흔적이 없다.**
- `execute`는 예외가 워커 스레드 밖으로 나가 기본 처리기가 stderr에 찍는다.
- 세부 API(`get`·`join`의 예외 타입 차이 등)는 [languages/java/syntax/54-executorservice-and-future](../../../languages/java/syntax/54-executorservice-and-future/2-summary.md).

### 5. Active Object — 메서드 호출을 메시지로 바꾼다

```text
  호출자 ── proxy.deposit(100) ──> [요청 큐] ──> 스케줄러 스레드 1개 ──> 실제 객체(servant)
     ▲                                                         │
     └──────────── Future<결과> ◀──────────────────────────────┘
  이 예제(기본형)에서 호출자는 큐에 넣고 바로 돌아간다. 실제 객체는 스레드 하나만 만지므로 내부에 락이 필요 없다.
  (Schmidt의 원 설명에는 결과를 동기로 기다리는 반환 정책, 유한 큐, servant 여럿을 스레드 여럿이 도는 thread pool 변형도 있다)
```

```java
final class Account {                                   // 실제 객체: 락 없음
    private long balance;
    long deposit(long amt) { return balance += amt; }
}
final class AccountProxy {                              // Active Object
    private final Account servant = new Account();
    private final ExecutorService scheduler = Executors.newSingleThreadExecutor();
    CompletableFuture<Long> deposit(long amt) {
        return CompletableFuture.supplyAsync(() -> servant.deposit(amt), scheduler);
    }
}
```

- 실무형: 액터 모델(메일박스 + 한 번에 한 메시지), 이벤트 루프의 단일 스레드 상태 소유. 동시성 모델 일반은 [14-concurrency-models](../14-concurrency-models/2-summary.md), 이벤트 루프는 [os/27-event-based-concurrency](../../os/27-event-based-concurrency/2-summary.md).
- 비용: 큐가 하나라 그 스레드가 병목이다. 큐가 무한이면 실험 1과 같은 문제가 생긴다.

### 6. Monitor Object — 메서드가 곧 임계 구역

```text
  객체 하나 = 락 하나 + 조건 대기열
  synchronized put()  ─ 꽉 찼으면 wait() ─┐
  synchronized take() ─ 비었으면 wait() ─┤ 깨면 조건을 다시 확인(while)
                                          └ 상태를 바꾼 쪽이 notifyAll()
```

- Java는 모든 객체에 모니터가 있다(`synchronized`·`wait`·`notify`). Active Object와 달리 **호출자 스레드가 직접** 들어와 일한다.
- `wait`를 `while`로 감싸는 이유(Mesa 의미론), lost wakeup, 조건 변수를 둘로 나누는 법은 [os/17-condition-variables-and-monitors](../../os/17-condition-variables-and-monitors/2-summary.md)에 있다.

### 7. Scoped Locking — 잠금 수명 = 블록 수명

- C++은 RAII(생성자에서 잠그고 소멸자에서 푼다), Java는 `synchronized` 블록과 `try`-`finally`/`try-with-resources`다.
  - *RAII(Resource Acquisition Is Initialization)*: 자원을 객체 수명에 묶는 C++ 관용구. 블록을 나가면 소멸자가 자원을 놓는다.

### 실험 5: 예외 경로의 unlock 누락 (`ScopedLock.java`)

```java
static void transferBad()  { LOCK.lock(); validate(); LOCK.unlock(); }          // 예외면 unlock 건너뜀
static void transferGood() { try (Held h = Held.lock(LOCK)) { validate(); } }    // 예외여도 close()
```

```text
  == manual
  request 1 failed: java.lang.IllegalArgumentException: amount < 0
  locked before request 2? true | request 2 got lock within 1s? false
  == scoped
  request 1 failed: java.lang.IllegalArgumentException: amount < 0
  locked before request 2? false | request 2 got lock within 1s? true
```

- 첫 요청이 실패한 뒤에도 락은 그 스레드 소유로 남았다. 다음 요청은 영영 못 들어간다(여기선 1초 `tryLock`이라 false로 끝남).
- `synchronized`는 블록을 나갈 때 JVM이 모니터를 풀어 준다. `ReentrantLock`은 사람이 풀어야 하므로 이 패턴이 필요하다.

### 8. Thread-Specific Storage — 스레드마다 따로 있는 칸

```text
  스레드 풀 워커 T1 ── ThreadLocal 칸: [user_001]   ← 요청 A가 넣음
     요청 A 끝 (remove 안 함)
     요청 B (익명) ── 같은 T1 재사용 ── get() → user_001   ← 누출
```

- *ThreadLocal*: 같은 변수 이름으로 스레드마다 다른 값을 갖게 하는 칸. 스레드가 살아 있는 동안 값도 산다(Java 21 `ThreadLocal` 문서).
- 풀의 스레드는 **요청보다 오래 산다.** 그래서 "요청 끝 = 칸 비우기"를 직접 해야 한다.

### 실험 6: ThreadLocal 누출 (`TlLeak.java`, 워커 1개 풀)

```text
  cleanup=false
  auth=user_001 -> handler sees user=user_001
  auth=null     -> handler sees user=user_001     ← 익명 요청이 앞 사람으로 처리됨
  cleanup=true (finally에서 remove)
  auth=null     -> handler sees user=null
```

- 가상 스레드는 작업마다 새로 만들고 재사용하지 않는다. JEP 444는 "가상 스레드는 절대 풀링하지 말라(should never be pooled)"고 적는다. 스레드 로컬로 비싼 자원을 나누던 풀 관용구는 옮길 때 경계하고 다른 캐시 방식으로 바꾸라고 한다.

### 9. Double-Checked Locking — 락 없이 한 번 더 보다가 반쯤 만든 객체를 본다

- 재정렬 그림·바이트코드·하드웨어 쪽 설명은 [architecture/14 §7](../../architecture/14-cache-coherence-and-memory-ordering/2-summary.md)에 있다. 여기서는 언어 규칙과 고치는 법만 정리한다.

```java
private static volatile Config instance;                 // volatile이 핵심 (JDK 5 이후)
static Config get() {
    Config c = instance;                                  // 락 밖에서 한 번만 읽는다
    if (c == null) {
        synchronized (Config.class) {
            c = instance;
            if (c == null) instance = c = new Config();
        }
    }
    return c;
}
// 더 단순한 대안: 홀더 클래스 — 클래스 초기화는 JVM이 한 번만, 안전하게 공개한다
static final class Holder { static final Config INSTANCE = new Config(); }
```

- "Double-Checked Locking is Broken" 선언문(Bacon·Bloch·Click·Lea 외 서명): JDK 5의 새 메모리 모델부터 `volatile`이면 동작한다. 정적 싱글턴이면 "별도 클래스의 static 필드"(홀더)가 단순한 해법이다.
- 언어 쪽 원리: `volatile` 쓰기와 그 값을 본 읽기 사이에 happens-before가 생긴다. 생성자 안의 쓰기가 그 앞에 있으므로 보인다. 세부는 [13-language-memory-model](../13-language-memory-model/2-summary.md), JLS §17.4.
- 모든 필드가 `final`인 불변 객체는 생성자가 끝나면 그 필드가 보이도록 보장된다. 단, 생성 중에 `this`를 다른 스레드에 흘리지 않았을 때다(JLS §17.5).

### 10. 불변 스냅샷 + 원자 참조 교체

```text
  가변 설정 (필드 둘을 따로 갱신)            불변 스냅샷 + 참조 교체
  writer: hi=1100 ...(틈)... lo=1000         writer: RANGE.set(new Range(1000,1100))
    (올릴 땐 hi 먼저, 내릴 땐 lo 먼저)
  reader: lo, hi를 따로 읽음                  reader: r = RANGE.get(); r.lo(), r.hi()
     → 틈에 걸리면 (0,1100) 관측                  → 옛 판이든 새 판이든 "온전한 한 판"
     → 두 읽기 사이에 갱신이 끼면 (1000,100)도
```

- 원리: 객체를 고치지 않고 **새로 만들어 참조 하나만 바꾼다.** 참조 쓰기는 원자적이고(`volatile`/`AtomicReference`), 불변 객체는 공개 후 바뀌지 않는다.
- 읽기 쪽은 락이 없다. 쓰기가 드물고 읽기가 많은 설정·라우팅 표·피처 플래그에 맞다.
- 읽고-고쳐-쓰기가 겹치면 `updateAndGet`(CAS 재시도)으로 바꾼다. 쓰기가 잦으면 매번 복사 비용이 커진다.

### 실험 7: 두 필드 갱신 vs 스냅샷 교체 (`Snapshot.java`)

writer는 [0,100] ↔ [1000,1100]을 2초 동안 번갈아 쓰고, reader는 계속 읽는다. 집필 3회 + 점검 4회(같은 `--cpus=2`, 호스트 부하 있음).

```text
  mutable : reads=5.4~15M  torn(h-l!=100)=38,996~3,374,760  inverted(lo>hi)=935~96,896
  snapshot: reads=5.9~7.0M torn=0  inverted=0
```

- 두 필드 모두 `volatile`이어도 "둘을 한 번에"는 보장되지 않는다. 쓰는 도중의 반쪽 상태(`h-l≠100`)를 실행마다 수만~수백만 번 봤다. 횟수는 두 스레드가 어떻게 스케줄되느냐에 따라 100배 가까이 흔들렸다.
- `lo>hi`는 writer가 한 번도 만든 적 없는 조합이다(실험 코드는 각 단계에서 lo≤hi를 지키는 순서로 쓴다). 두 읽기 사이에 writer가 끼어들어 생겼다(해석).
- 스냅샷 교체는 일곱 번 모두 0이었다. 읽기 횟수는 실행마다 크게 달라(가변 판이 더 적은 실행도 있었다) 두 방식의 속도 비교 근거로 쓰지 않는다.

## 쓰이는 자료구조·알고리즘

- **블로킹 큐 + 워커** — 생산자-소비자. OpenJDK 21 기준
  - `LinkedBlockingQueue`: 연결 리스트 + "two lock queue" 변형(넣기 락 `putLock`, 빼기 락 `takeLock`이 따로). 용량을 안 주면 `Integer.MAX_VALUE`.
  - `ArrayBlockingQueue`: 고정 배열을 원형으로 쓰는 링 버퍼 + 락 하나 + 조건 둘(`notEmpty`·`notFull`). [data-structure/25-ring-buffer](../../data-structure/25-ring-buffer/2-summary.md), [data-structure/04-queue-deque](../../data-structure/04-queue-deque/2-summary.md)
  - 세마포어 세 개로 만드는 유한 버퍼는 [os/18-semaphores](../../os/18-semaphores/2-summary.md) §3.
- **완료 콜백 사슬** — `CompletableFuture`의 의존 작업 = Treiber 스택(CAS로 머리를 바꾸는 lock-free 스택). [data-structure/29-concurrent-data-structures](../../data-structure/29-concurrent-data-structures/2-summary.md) §4
- **CAS 참조 교체** — `AtomicReference.compareAndSet`·`updateAndGet`. 하드웨어 쪽 `lock cmpxchg`는 [architecture/14](../../architecture/14-cache-coherence-and-memory-ordering/2-summary.md) §6.
- **작업 훔치기 덱** — `ForkJoinPool` 워커마다 덱을 두고, 놀면 남의 덱에서 훔친다(Java 21 `ForkJoinPool` 문서 "work-stealing", OpenJDK 21 `ForkJoinPool.java` 구현 주석: 워커 큐는 push·pop·poll(=steal)만 하는 덱, Chase–Lev 덱 기반).

## 적용 — 풀어나가는 법

1. **증상을 패턴으로 옮긴다.**

| 증상 | 의심할 칸 |
|---|---|
| 힙이 차오름, 덤프 최대 점유가 `LinkedBlockingQueue` | 무한 큐 풀(§2) |
| 다른 비동기 작업까지 같이 늦음, 스레드 덤프에 `commonPool-worker`가 전부 `TIMED_WAITING`/`WAITING` | 공용 풀 블로킹(§4) |
| 요청이 전부 멈춤, 덤프에 같은 락을 기다리는 스레드만 있고 주인은 안 보임 | Scoped Locking 누락(§7) |
| 가끔 남의 사용자·테넌트 값 | ThreadLocal 미정리(§8) |
| 기능이 가끔 "안 된 채" 성공 응답 | Future 예외 미처리(§4) |
| 싱글턴이 드물게 기본값(0·null) | DCL(§9) |

2. **진단 명령으로 확인한다.**

```bash
jcmd <pid> Thread.print | grep -A3 'commonPool-worker'        # 공용 풀 워커가 무엇에 막혀 있나
jcmd <pid> Thread.print | grep -B2 -A8 'waiting to lock\|parking to wait for'   # 락 주인 찾기
jcmd <pid> GC.class_histogram | head -20                      # 큐 노드·작업 객체가 상위인가
```

- 스레드 이름을 붙여 두면(`ThreadFactory`) 덤프에서 어느 풀인지 바로 보인다.

3. **운영용 풀은 이렇게 만든다.**

```java
ThreadPoolExecutor paymentPool = new ThreadPoolExecutor(
    20, 20, 0, TimeUnit.MILLISECONDS,
    new ArrayBlockingQueue<>(500),                                   // 유한 큐
    Thread.ofPlatform().name("payment-", 0).factory(),                // 덤프에서 보이는 이름
    (r, ex) -> { rejected.increment(); throw new RejectedExecutionException("payment pool full"); });
// 큐 길이·활성 스레드·거부 수를 지표로 내보낸다
gauge("payment.queue", () -> paymentPool.getQueue().size());
gauge("payment.active", paymentPool::getActiveCount);

CompletableFuture.supplyAsync(() -> pgClient.approve(req), paymentPool)   // 블로킹은 전용 풀에
    .orTimeout(2, TimeUnit.SECONDS)
    .whenComplete((r, ex) -> { if (ex != null) log.warn("approve failed", ex); });  // 사슬 끝에서 실패를 받는다
```

4. **요청 범위 상태는 `try`-`finally`로 비운다.** 필터 하나가 `set`과 `remove`를 같이 책임진다.

## 장애 시나리오와 대처

### 1. 무한 큐 스레드 풀 → 거부 없이 대기열 OOM

- **현상**: 하위 의존성이 느려진 뒤 응답이 점점 늦어지다가 인스턴스가 죽는다.
- **보이는 형태**: `java.lang.OutOfMemoryError: Java heap space`. 힙 덤프 상위에 `LinkedBlockingQueue$Node`와 작업 람다·요청 본문. 그 전까지 거부 예외나 경고 로그는 없다.
- **원인**: `Executors.newFixedThreadPool`의 큐 용량이 `Integer.MAX_VALUE`다. 처리 속도보다 들어오는 속도가 크면 큐가 끝없이 자란다(실험 1: 약 0.15초에 3,800건, 64MB 힙 소진).
- **대처**: 유한 큐 + 거부 정책을 명시한다. 거부는 429·503으로 호출자에게 돌려주거나 `CallerRunsPolicy`로 역압을 건다. 큐 길이를 지표로 본다.

### 2. 공용 풀(ForkJoin common pool)에서 블로킹 → 비동기 전체 정지

- **현상**: 외부 API 하나가 느려진 날, 그 API와 무관한 비동기 작업·병렬 스트림까지 느려진다.
- **보이는 형태**: 스레드 덤프에서 `ForkJoinPool.commonPool-worker-*`가 전부 소켓 읽기·`sleep`·`park`. 지연이 `blocking 시간 × (작업 수 ÷ 워커 수)` 꼴로 계단처럼 는다(실험 3: 가벼운 작업이 1초 대기).
- **원인**: executor 없는 `supplyAsync`·`runAsync`·병렬 스트림이 한 공용 풀(기본 `코어 수 - 1`)을 나눠 쓴다.
- **대처**: 블로킹 호출에는 전용 executor를 준다(또는 가상 스레드 executor). 코어가 적은 환경에선 증상이 안 보일 수 있으므로(병렬도 1이면 작업마다 새 스레드) 운영과 같은 코어 수로 시험한다.

### 3. `volatile` 없는 DCL → 반쯤 생성된 객체

- **현상**: 지연 초기화한 설정 객체가 드물게 0·`null` 필드를 내준다. 재현이 거의 안 된다.
- **보이는 형태**: 기본값으로 인한 `NullPointerException`·잘못된 포트·타임아웃 0. x86 개발 PC에서는 안 나고 ARM 서버에서 나올 수 있다(하드웨어 쪽은 [architecture/14](../../architecture/14-cache-coherence-and-memory-ordering/2-summary.md) §7).
- **원인**: 참조 공개와 생성자 안의 쓰기 사이에 happens-before가 없다. 컴파일러·CPU가 순서를 바꿀 수 있다.
- **대처**: 필드를 `volatile`로, 락 밖 읽기는 한 번만. 정적 싱글턴은 홀더 클래스나 `enum`. 객체를 불변(`final` 필드)으로.

### 4. 스레드 풀 ThreadLocal 미정리 → 사용자 A 컨텍스트가 B 요청에 누출

- **현상**: 익명 요청이 다른 사용자로 처리되거나, 감사 로그에 엉뚱한 사용자 ID가 찍힌다.
- **보이는 형태**: 예외 없음. 같은 워커 스레드 이름(`http-nio-8080-exec-7` 등)에서 연속된 요청 사이에만 생긴다(실험 6).
- **원인**: 풀 스레드는 요청보다 오래 산다. 값을 넣는 코드는 있는데 비우는 코드가 예외·분기 경로에서 빠졌다.
- **대처**: `set`한 곳이 `finally`에서 `remove`한다. 비동기 경계를 넘길 때는 값을 명시적으로 복사해 넘기고 끝에 지운다. 가상 스레드로 옮기면 스레드 재사용이 없어지지만, 스레드 로컬로 자원을 공유하던 관용구는 JEP 444가 경고하듯 다시 설계해야 한다.

### 5. `CompletableFuture` 예외 미처리 → 조용한 실패

- **현상**: "저장했습니다" 응답은 나갔는데 데이터가 없다. 로그에도 없다.
- **보이는 형태**: 아무것도 안 보인다. 프로세스는 exit 0(실험 4의 1·3번).
- **원인**: 예외가 `Future` 안에 담긴 채 아무도 `get`/`join`/`whenComplete`로 꺼내지 않았다.
- **대처**: 사슬마다 끝에 `whenComplete`/`exceptionally`로 기록·보상을 단다. 결과를 기다려야 하는 일이면 응답 전에 `join`한다. "발사 후 잊기" 작업은 실패 지표를 따로 센다.

## 핵심 문장

- 스레드 풀은 블로킹 큐 + 워커 + 거부 정책이고, 큐가 무한이면 과부하가 거부 대신 메모리 사용량으로 바뀌어 OOM으로 끝난다.
- 풀 크기는 코어 수 × (1 + 대기/CPU)로 시작해 재서 정하고, 블로킹 작업은 공용 풀이 아니라 전용 풀에 둔다.
- `Future`·`CompletableFuture`는 예외를 결과 안에 담으므로, 사슬 끝에서 꺼내지 않으면 실패가 사라진다.
- Active Object는 호출을 큐의 메시지로 바꿔 (기본형에서는) 스레드 하나가 상태를 독점하게 하고, Monitor Object는 호출자 스레드가 락을 쥐고 직접 들어온다.
- Scoped Locking은 잠금 수명을 블록 수명에 묶어 예외 경로의 unlock 누락을 없애고, Thread-Specific Storage는 풀에서 쓰면 요청 끝에 직접 비워야 한다.
- 여러 필드를 한 번에 바꿔야 하는 공유 상태는 불변 스냅샷을 새로 만들어 참조 하나를 원자 교체하고, 지연 초기화는 `volatile` DCL이나 홀더 클래스로 한다.

## 관련 주제·근거

- 선행
  - [14-concurrency-models](../14-concurrency-models/2-summary.md)(스레드·액터·async·가상 스레드), [13-language-memory-model](../13-language-memory-model/2-summary.md)(happens-before)
  - [os/18-semaphores](../../os/18-semaphores/2-summary.md) — 개수 제한·유한 버퍼
  - [os/17-condition-variables-and-monitors](../../os/17-condition-variables-and-monitors/2-summary.md) — Monitor Object의 바탕
- 후속·연결
  - [architecture/14-cache-coherence-and-memory-ordering](../../architecture/14-cache-coherence-and-memory-ordering/2-summary.md) — DCL 재정렬의 하드웨어 쪽, CAS
  - [data-structure/29-concurrent-data-structures](../../data-structure/29-concurrent-data-structures/2-summary.md) — 동시 컬렉션·lock-free·ABA
  - [os/16-locks-and-spinlocks](../../os/16-locks-and-spinlocks/2-summary.md) · [os/27-event-based-concurrency](../../os/27-event-based-concurrency/2-summary.md) · [os/36-server-concurrency-architectures](../../os/36-server-concurrency-architectures/2-summary.md)
  - [reliability/12-backpressure-and-load-shedding](../../reliability/12-backpressure-and-load-shedding/2-summary.md) · [reliability/28-bulkhead](../../reliability/28-bulkhead/2-summary.md)
  - [languages/java/syntax/54-executorservice-and-future](../../../languages/java/syntax/54-executorservice-and-future/2-summary.md) · [languages/java/syntax/33-synchronized-and-volatile](../../../languages/java/syntax/33-synchronized-and-volatile/2-summary.md) · [languages/java/syntax/56-virtual-threads](../../../languages/java/syntax/56-virtual-threads/2-summary.md)
- 문서·출처
  - Java SE 21 API — `ThreadPoolExecutor`(Queuing 세 전략, Rejected tasks 네 정책) <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/ThreadPoolExecutor.html> · `Executors.newFixedThreadPool`("shared unbounded queue") · `CompletableFuture`(병렬도 2 미만이면 작업마다 새 스레드) · `ForkJoinPool`(common pool, work-stealing) · `ThreadLocal`
  - OpenJDK jdk21u 소스 — `ForkJoinPool.java`(공용 풀 `availableProcessors() - 1`), `CompletableFuture.java`(`USE_COMMON_POOL`, Treiber 스택 `stack`), `LinkedBlockingQueue.java`(two lock queue), `ArrayBlockingQueue.java`(락 하나·조건 둘) <https://github.com/openjdk/jdk21u>
  - JLS SE21 §17.4(happens-before), §17.5(final 필드 의미) <https://docs.oracle.com/javase/specs/jls/se21/html/jls-17.html>
  - "The 'Double-Checked Locking is Broken' Declaration" — JDK 5 `volatile` 수정, 정적 싱글턴 홀더 <https://www.cs.umd.edu/~pugh/java/memoryModel/DoubleCheckedLocking.html>
  - JEP 444 Virtual Threads — 스레드 로컬 지원, "virtual threads should never be pooled" <https://openjdk.org/jeps/444>
  - Schmidt·Stal·Rohnert·Buschmann, *Pattern-Oriented Software Architecture Vol. 2: Patterns for Concurrent and Networked Objects*, Wiley 2000 — 17개 패턴, 4장 동기화 패턴·5장 동시성 패턴(저자 사이트 목차) <https://www.dre.vanderbilt.edu/~schmidt/POSA/POSA2/>
  - Goetz 외, *Java Concurrency in Practice* — 6장 Task Execution, 8장 Applying Thread Pools(jcip.net 공개 샘플 PDF가 "Chapter 6. Task Execution"이고 본문에 "thread pool configuration options in depth in Chapter 8"), 16장 The Java Memory Model(목차 순서로 센 번호 [?]) <https://jcip.net/contents.html> · <https://jcip.net/jcip-sample.pdf>
- 실험(로컬, `eclipse-temurin:21-jdk`, `--cpus=2`, `--network none`)
  - `PoolQueue.java` — 무한 큐 `-Xmx64m`에서 3,767~3,822건 대기 중 OOM(7회), 유한 큐 100 + Abort(거부 1,880~1,886/2,000) · CallerRuns(거부 0, 약 7초)
  - `Sizing.java` — 작업 CPU 2ms + 대기 18ms, 풀 2~80 처리량(5회)
  - `CommonPoolBlock.java` — `-XX:ActiveProcessorCount=2/4`, 공용 풀 병렬도 1/3, 블로킹 8건 506~508/1,506~1,551ms, 가벼운 작업 대기 1~2/1,001~1,002ms, 전용 풀 506ms
  - `Silent.java` — submit·runAsync 예외 무출력, execute는 stderr, whenComplete로 기록
  - `ScopedLock.java` — 수동 unlock 누락 시 다음 요청 `tryLock` 실패, try-with-resources는 성공
  - `TlLeak.java` — 워커 1개 풀에서 익명 요청이 `user_001`을 봄, `remove` 후 null
  - `Snapshot.java` — 두 `volatile` 필드 갱신의 반쪽 관측 38,996~3,374,760회·lo>hi 935~96,896회, 스냅샷 교체 0회(7회)
