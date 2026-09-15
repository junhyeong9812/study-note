# PR #36916 분석 — SimpleAsyncTaskExecutor throttle permit 불균형

> 기준: PR base = upstream `0c60266986`(수정 전) / PR head = `322ab59bb88`(수정 후).
> 프로덕션 파일 `SimpleAsyncTaskExecutor.java`·`ConcurrencyThrottleSupport.java`는 base와 현재 upstream/main이 바이트 동일하므로, 아래 "수정 전" 줄번호는 지금 main을 열어도 그대로 맞는다.
> 중복 회피: 무대 전경·스프링 전역 배치는 `structure.md` §1·§4, 테스트 해설은 `tests.md`, 서사형 설명은 `README.md`. 이 문서는 이름표 단위 사전(§2.5)과 단계별 값 추적(§3), 대안 기각 근거(§5)를 맡는다.

## 0. 결론

**결함**: permit을 **획득하는 조건**(`execute`의 분기 1)과 **반납하는 조건**(`TaskTrackingRunnable.run()`의 `finally`)이 서로 다른 메서드에 흩어져 있고 둘을 잇는 정보가 없어서, 획득 없이 반납되거나(카운트 음수 -> 한도 무력화) 획득 후 반납되지 않는(permit 영구 누수 -> 데드락) 두 방향의 불균형이 동시에 성립했다.

**수정**: `TaskTrackingRunnable`에 `boolean releaseThrottle`을 실어 "내 몫의 permit이 있는가"를 추측 대신 데이터로 전달하고, 동시에 `checkCancelled()`를 포함한 `run()` 본문 전체를 `try` 안으로 넣어 `finally`가 어떤 경로에서도 실행되게 만든다(프로덕션 2개소 + 래퍼 1개소, +76/-11).

**상태**: OPEN.\
2026-06-13 생성, base `main`, head `fix/simpleasync-immediate-throttle`, 라벨 `status: waiting-for-triage` 단 하나, 리뷰어 미배정.\
즉 아직 트리아지 대기이며 upstream 반영 여부는 미확정이다.

> **permit(퍼밋)** — "한 자리를 점유할 권리" 한 장.\
> 예: `beforeAccess()`가 `concurrencyCount`를 1 올려 한 장을 집어가고, `afterAccess()`가 1 내려 돌려놓는다.

> **트리아지(triage)** — 들어온 이슈·PR을 분류해 담당과 우선순위를 정하는 초기 단계.\
> 예: 라벨 `status: waiting-for-triage`는 아직 메인테이너가 이 PR을 분류하지 않았다는 표시다.

## 1. 무대

변경이 닿는 파일과 그 주변을 먼저 못 박아 둔다.

- 모듈: `spring-core`, 패키지 `org.springframework.core.task`
- 프로덕션 파일: `spring-core/src/main/java/org/springframework/core/task/SimpleAsyncTaskExecutor.java`
- 협력 파일: `spring-core/src/main/java/org/springframework/util/ConcurrencyThrottleSupport.java` (변경 없음 — 이 PR의 금지영역)
- 테스트 파일: `spring-core/src/test/java/org/springframework/core/task/SimpleAsyncTaskExecutorTests.java`

클래스는 넷이다.\
바깥 클래스 `SimpleAsyncTaskExecutor`(:66)와 그 안의 `private class ConcurrencyThrottleAdapter`(:437), `private class TaskTrackingRunnable`(:468), 그리고 어댑터의 상위 클래스인 범용 지원 클래스 `ConcurrencyThrottleSupport`(:50)다.

공개 진입 API는 넷인데 전부 한 메서드로 모인다.

| 공개 API | 파일:줄 | 넘기는 startTimeout | 이 결함에 닿는가 |
|---|---|---|---|
| `execute(Runnable)` | :296 | `TIMEOUT_INDEFINITE` | 결함 B만 |
| `submit(Runnable)` | :340 | `TIMEOUT_INDEFINITE` | 결함 B만 |
| `submit(Callable<T>)` | :348 | `TIMEOUT_INDEFINITE` | 결함 B만 |
| `execute(Runnable, long)` `@Deprecated(since="5.3.16")` | :311 | 호출자가 지정 | 결함 A(0을 줄 때) + 결함 B |

부르는 쪽은 이 executor를 기본값으로 꽂아 쓰는 프레임워크 코드(`@Async` 최종 폴백, `WebAsyncManager`, `JdkClientHttpRequestFactory`, JMS·websocket)와 상속해 쓰는 쪽(`SimpleAsyncTaskScheduler`, MVC의 `MvcSimpleAsyncTaskExecutor`)으로 갈린다.\
다만 전자는 대개 `setConcurrencyLimit`을 부르지 않아 `isThrottleActive()`가 거짓이고, 그러면 분기 1 자체가 성립하지 않는다.\
노출면은 "한도를 명시적으로 건 사용자"로 좁다(목록 전체는 `structure.md` §4).

## 2. 전체 메서드 그래프 — 진입점에서 결함 지점까지

아래 그래프는 제출 스레드가 permit을 얻는 지점부터 워커 스레드가 그것을 반납하는 지점까지를 한 장에 편 것이며, 스레드 경계가 그 둘을 가르는 자리를 표시했다.

```text
[제출 스레드]
 submit(Runnable) :340 / submit(Callable) :348 / execute(Runnable) :296
        |  전부 TIMEOUT_INDEFINITE 로 위임
        v
 execute(Runnable task, long startTimeout)                              :311
        |
        +-- Assert.notNull(task)                                        :312
        +-- !isActive() -> TaskRejectedException                        :313-315
        +-- taskToUse = taskDecorator != null ? decorate(task) : task    :317
        +-- future    = (task instanceof Future<?> f ? f : null)         :318
        |
        +-- [분기판정] isThrottleActive() && startTimeout > TIMEOUT_IMMEDIATE   :319
        |
        +--[1]-- concurrencyThrottle.beforeAccess()                      :320
        |          -> ConcurrencyThrottleSupport.beforeAccess()          CTS:119
        |               limit==NO_CONCURRENCY -> onAccessRejected        CTS:120-122
        |               count >= limit -> onLimitReached()               CTS:126-128
        |               count++                        (permit 획득)     CTS:132
        |        try { doExecute(new TaskTrackingRunnable(taskToUse, future)) }  :322
        |        catch (Throwable) { concurrencyThrottle.afterAccess(); throw }  :324-328
        |
        +--[2]-- activeThreads != null                                   :330
        |        doExecute(new TaskTrackingRunnable(taskToUse, future))  :331   <-- permit 없음
        |
        +--[3]-- doExecute(taskToUse)                                    :334   <-- 래퍼도 permit도 없음
                   |
                   v
              doExecute(Runnable) :361 -> newThread(task) :374 -> Thread.start()
                   |
=================== 스레드 경계 ===================
                   v
[워커 스레드]
 TaskTrackingRunnable.run()                                             :481
        |
        +-- threads = activeThreads ; thread = null                      :482-483
        +-- if (threads != null) { thread = currentThread()               :484-485
        |     synchronized (threads) {
        |         checkCancelled(this.future)         <-- try 바깥!       :487
        |              -> cancelled ? future.cancel(false) + throw CancellationException   :422-429
        |         threads.add(thread)                                     :488
        |     } }
        +-- try { this.task.run() }                                       :491-493
        +-- finally {                                                     :494
              threads.remove(thread) ; closed ? notify()                  :495-504
              concurrencyThrottle.afterAccess()   <-- 무조건              :505
                   -> CTS.afterAccess(): count-- ; signal()               CTS:191,:195
            }

[제3의 스레드]
 close() :390 -> cancelled = true (:396 또는 :411) -> threads.forEach(Thread::interrupt)
```

데이터 흐름으로 보면 결함은 한 문장이다.\
**`execute`가 아는 사실("나는 beforeAccess를 불렀다")이 `run()`으로 전달되지 않고, `run()`이 그것을 `activeThreads != null`이라는 무관한 조건으로 추측한다.**\
그리고 `checkCancelled`가 `try` 밖에 있어 `finally`가 그 추측을 실행할 기회조차 잃는 경로가 따로 존재한다.

그 "전달되지 않는 한 비트"를 수정 전/후로 나란히 놓으면 이렇다.

```text
수정 전 — 추측                        수정 후 — 기록
+----------------------------+        +----------------------------+
| execute: beforeAccess() 함 |        | execute: beforeAccess() 함 |
|   (이 사실은 여기서 소멸)  |        |   -> new TaskTracking      |
| new TaskTrackingRunnable   |        |      Runnable(.., true)    |
|      (task, future)        |        |      (task, future, true)  |
|          |                 |        |          |                 |
|          v                 |        |          v                 |
| run(): activeThreads !=null|        | run(): releaseThrottle 읽음|
|   -> 무조건 afterAccess()  |        |   -> true 일 때만 반납     |
+----------------------------+        +----------------------------+
  -> 분기 2 의 태스크도 반납한다        -> 획득한 태스크만 반납한다
```

## 2.5 핵심 이름표 사전

이 무대에서 헷갈리는 지점은 "스위치가 두 개인데 서로 독립"이라는 것이다.\
throttle 스위치(`concurrencyLimit`)와 추적 스위치(`activeThreads`)가 각각 켜지고, 래퍼는 추적 스위치로 씌워지는데 반납은 throttle 스위치의 일이다.\
아래 세 표는 그 두 스위치가 각각 어느 이름표에 살고 어디서 교차하는지를 나눠 적는다.

### 2.5.1 상태 필드

두 스위치가 각각 어느 필드에 사는지는 아래 표가 정리한다.

| 이름표 | 역할(무엇을 들고 있나) | 언제 정해지나 | 누가 읽나 | 이 결함과의 관계 |
|---|---|---|---|---|
| `concurrencyCount` (CTS:79) | 현재 점유 중인 permit 개수. `int` 하나이며 **소유권 정보가 없다** | `beforeAccess`에서 ++(CTS:132), `afterAccess`에서 --(CTS:191) | `beforeAccess`의 한도 판정(CTS:126), `onLimitReached`의 while(CTS:147) | 결함의 피해가 실제로 나타나는 값. A에서 음수로, B에서 내려가지 않은 채 고정 |
| `concurrencyLimit` (CTS:77) | 허용 동시 실행 수. 기본 `UNBOUNDED_CONCURRENCY`(-1) | `setConcurrencyLimit`(:246 -> CTS:92) | `isThrottleActive()`(CTS:108), `beforeAccess`, `afterAccess`(CTS:187) | -1(기본)이면 분기 1이 성립하지 않아 결함 A·B 모두 미발동. **노출 조건 1** |
| `concurrencyLock` / `concurrencyCondition` (CTS:73,:75) | 카운트를 보호하는 락과, 한도 대기자를 재우고 깨우는 조건변수 | 생성 시 고정 | `beforeAccess`·`afterAccess`·`onLimitReached` | 결함 B에서 `signal()`을 부를 주체가 사라져 `await()`가 영구화된다 |
| `activeThreads` (:93) | 실행 중 워커 스레드 집합. `null`이면 추적 안 함 | `trackActiveThreadsIfNecessary()`(:283-286) | `execute` 분기 2 판정(:330), `run()`(:482), `close()`(:392) | **래퍼를 씌울지 정하는 유일한 조건**. permit과 무관한데 반납 코드가 이 조건 아래 놓여 있었다. **노출 조건 2** |
| `taskTerminationTimeout` (:91) | 종료 시 워커를 기다릴 밀리초 | `setTaskTerminationTimeout`(:193) | `trackActiveThreadsIfNecessary`(:284), `close()`(:401,:405) | 0보다 크면 `activeThreads`가 생긴다 -> 노출 조건 2를 켜는 스위치 (a) |
| `cancelRemainingTasksOnClose` (:95) | 닫을 때 남은 태스크를 즉시 취소할지 | `setCancelRemainingTasksOnClose`(:214) | `trackActiveThreadsIfNecessary`(:284), `close()`(:394,:413) | 노출 조건 2를 켜는 스위치 (b). 동시에 `cancelled`를 조기에 세워 결함 B의 창을 넓힌다 |
| `cancelled` (:101) | "남은 태스크를 취소하라" 신호. volatile 아님, `activeThreads` 모니터로만 보호 | `close()` 안 두 곳(:396 조기, :411 타임아웃 후) | `checkCancelled`(:423) | true를 만나면 `run()`이 `try` 진입 전에 예외로 이탈 -> **결함 B의 방아쇠** |
| `closed` (:99) | `AtomicBoolean`. 더 이상 제출을 받지 않는다는 표시 | `close()`의 CAS(:391) | `isActive()`(:276), `run()`의 finally(:497) | 직접 관련은 없으나 `execute` 초입에서 제출을 막으므로, 결함 B의 창은 "제출은 통과했고 close가 그 뒤에 온" 구간에 한정된다 |
| `rejectTasksWhenLimitReached` (:97) | 한도 도달 시 대기 대신 거절할지 | `setRejectTasksWhenLimitReached`(:229) | `ConcurrencyThrottleAdapter.onLimitReached`(:446) | 결함 B의 **증상 형태**만 바꾼다. false면 무한 블로킹, true면 전건 `TaskRejectedException` |
| `TaskTrackingRunnable.task` / `.future` (:470,:472) | 감쌀 원본 Runnable / 대응 `Future`(있으면) | 생성자(:474-478) | `run()`(:487,:492) | `future`는 `checkCancelled`가 `cancel(false)`를 걸 대상. 결함 B에서 이 취소는 정상 수행되고 permit만 새어나간다 |
| `TaskTrackingRunnable.releaseThrottle` (수정 후 :474) | **"내가 만들어질 때 permit이 하나 획득되었다"**는 기록 | 생성자 인자(수정 후 :476-481). 분기 1은 `true`, 분기 2는 `false` | `run()`의 finally(수정 후 :510) | **이 PR이 신설한 이름표.** 추측을 데이터로 바꿔 결함 A를 막는다 |

### 2.5.2 메서드

메서드 쪽에서는 획득 조건과 반납 조건이 각각 어느 메서드에 사는지가 관심사다.

| 이름표 | 역할 | 입력 -> 출력 | 누가 언제 부르나 | 이 결함과의 관계 |
|---|---|---|---|---|
| `execute(Runnable, long)` :311 | 모든 제출 경로가 모이는 유일한 분기점 | (task, startTimeout) -> void | 공개 3 API가 위임, 사용자가 직접(deprecated) | 3분기 중 permit을 얻는 것은 분기 1뿐. **획득 조건이 사는 곳** |
| `isThrottleActive()` :263 | throttle이 켜져 있는가 | -> `limit >= 0` (CTS:108) | `execute` :319 | 분기 1의 앞 조건 |
| `beforeAccess()` (어댑터 :440 -> CTS:119) | permit 획득 | -> void, 한도 초과 시 블로킹 또는 예외 | `execute` :320 | 획득 지점. 제출 스레드에서만 실행된다 |
| `onLimitReached()` (어댑터 :444 -> CTS:145) | 한도 도달 시 정책 | -> void(블로킹) 또는 `TaskRejectedException` | `beforeAccess` CTS:127 | 결함 B의 피해가 드러나는 자리 — `await()`(CTS:157)에서 영구 대기 |
| `onAccessRejected(String)` (어댑터 :452) | 거절을 executor 예외로 치환 | msg -> `TaskRejectedException` 던짐 | `onLimitReached`, `beforeAccess` | 결함 B + reject 모드에서 전건 거절이 되는 경로 |
| `afterAccess()` (어댑터 :458 -> CTS:186) | permit 반납 + `signal()` | -> void | `execute`의 catch(:326), `run()`의 finally(:505) | **반납 지점이 둘**이고 서로 배타여야 한다. 그 배타성이 코드 배치로만 보장된다 |
| `doExecute(Runnable)` :361 | 실제 실행 방식(기본: 새 스레드) | task -> void | `execute` 세 분기 모두 | protected 확장점. 테스트가 이것을 오버라이드해 스레드 경계를 없애고 결함을 결정론적으로 관측한다 |
| `trackActiveThreadsIfNecessary()` :283 | 추적 스위치 계산 | -> `activeThreads` 대입 | 두 세터(:193,:214) | 래퍼를 씌우는 조건을 만든다. permit과는 무관 |
| `close()` :390 | 종료 대기 + 취소 + 인터럽트 | -> void | try-with-resources, 컨테이너 종료 | `cancelled`를 세워 결함 B를 발동시키는 쪽 |
| `checkCancelled(Future)` :422 | 취소 신호를 확인하고 태스크를 정식 취소 | future -> void 또는 `CancellationException` | `run()` :487 (호출자가 이미 `synchronized(threads)` 안이라는 전제, :423 주석) | **던지는 위치가 `try` 바깥**이라는 사실 하나가 결함 B의 전부 |
| `run()` :481 | 추적 등록 -> 태스크 실행 -> 정리 | -> void | 워커 스레드 | **반납 조건이 사는 곳**. 획득 조건을 모른 채 `activeThreads`만 보고 판단했다 |

### 2.5.3 지역 변수와 상수

마지막으로 두 분기를 실제로 가르는 값들, 즉 파라미터와 인터페이스 상수를 모은다.

| 이름표 | 역할 | 값이 정해지는 곳 | 이 결함과의 관계 |
|---|---|---|---|
| `startTimeout` (파라미터, :311) | "언제까지 시작되어야 하는가"의 힌트 | 호출자 | `> TIMEOUT_IMMEDIATE` 비교 하나로 분기 1/2가 갈린다 |
| `TIMEOUT_IMMEDIATE` (`AsyncTaskExecutor`) | 값 0. "즉시 실행, throttle 우회" | 인터페이스 상수 | 분기 1의 경계값. `0 > 0`이 거짓이므로 **경계값 자신이 분기 2로 떨어진다** — 결함 A의 유일한 입구 |
| `TIMEOUT_INDEFINITE` (`AsyncTaskExecutor`) | `Long.MAX_VALUE` | 인터페이스 상수 | 공개 3 API가 넘기는 값. 항상 분기 1로 간다 |
| `taskToUse` (:317) | 데코레이터 적용 후의 실제 Runnable | `execute` :317 | 결함과 무관(래퍼 안쪽에 그대로 실린다) |
| `future` (:318) | `task`가 `Future`면 그 자신 | `execute` :318 | `submit` 경로에서만 non-null. 결함 B에서 `cancel(false)`의 대상 |
| `threads` (run 지역, :482) | `activeThreads` 스냅샷 | `run()` 진입 시 1회 | `null` 검사를 `try` 안팎 어디서 하느냐가 수정의 형태를 정한다 |
| `thread` (run 지역, :483) | 현재 워커 스레드 | :485, **`synchronized` 블록 앞** | `try` 범위를 넓혀도 `finally`의 `threads.remove(thread)`가 NPE를 내지 않는 이유. 대입 순서가 반대였다면 `ConcurrentHashMap.newKeySet()`이 null을 거부해 터졌을 것 |
| `UNBOUNDED_CONCURRENCY` (CTS:58) | -1. throttle 끔 | 상수 | 기본값. 이 값이면 `afterAccess`가 CTS:187에서 통째로 no-op이라 결함 A가 표면화되지 않는다 |
| `NO_CONCURRENCY` (CTS:67) | 0. 진입 전면 금지 | 상수 | `beforeAccess` 첫 줄에서 즉시 거절(CTS:120-122). 이 경우 count는 오르지 않는데 예외로 나가므로 분기 1의 catch도 타지 않는다 — 결함과는 별개 경로 |

## 3. 결함 경로 단계 추적

### 3.1 결함 A — 획득 없는 반납

설정: `setConcurrencyLimit(2)` + `setTaskTerminationTimeout(10_000)`, 호출 `execute(task, TIMEOUT_IMMEDIATE)`.

"정상 케이스"는 같은 설정에서 `TIMEOUT_INDEFINITE`로 부른 경우다.\
두 줄기를 같은 단계에 놓고 값을 비교한다.

| 단계 | 정상 (`TIMEOUT_INDEFINITE`) | 결함 A (`TIMEOUT_IMMEDIATE`) |
|---|---|---|
| :319 분기 판정 | `true && (MAX > 0)` -> 분기 1 | `true && (0 > 0)` -> **거짓**, 분기 2로 |
| :320 `beforeAccess()` | 호출됨. count 0 -> 1 | **호출 안 됨.** count 0 유지 |
| :322 / :331 래퍼 생성 | `TaskTrackingRunnable` 생성 | `TaskTrackingRunnable` 생성 (동일) |
| :487 `checkCancelled` | 통과 | 통과 |
| :492 `task.run()` | 실행 | 실행 |
| :505 `afterAccess()` | 호출. count 1 -> 0 | **호출됨.** count 0 -> **-1** |
| 이후 제출자 3명 | count 0,1,2 -> 4번째가 대기. 동시 2개 | count -1,0,1 -> 4번째가 통과. **동시 3개** |

피해의 성격은 조용한 완화다.\
`getConcurrencyLimit()`은 여전히 2를 돌려주고, 예외도 로그도 없다.\
immediate 태스크를 던질 때마다 count가 더 내려가므로 설정값과 실제 동시성의 괴리가 누적된다.\
다만 입구가 deprecated 오버로드 + `TIMEOUT_IMMEDIATE`뿐이라 노출면은 좁다.

> **무음 실패(silent failure)** — 잘못된 동작이 예외·로그 없이 정상처럼 흘러가는 실패.\
> 예: 한도 2가 실제로 3을 통과시키는데도 `getConcurrencyLimit()`은 여전히 2를 돌려주므로, 관측 지표만 보면 아무 이상이 없다.

### 3.2 결함 B — 반납 없는 획득

설정: `setConcurrencyLimit(1)` + `setCancelRemainingTasksOnClose(true)`, 호출 `execute(task, TIMEOUT_INDEFINITE)` 후 워커가 `run()`에 닿기 전 `close()`.

| 단계 | 정상 (close가 늦게 옴) | 결함 B (close가 먼저 옴) |
|---|---|---|
| :320 `beforeAccess()` | count 0 -> 1 | count 0 -> 1 (동일) |
| :322 `doExecute` | 스레드 출발 | 스레드 출발 (동일) |
| `close()` :396 | 아직 안 옴 | `cancelled = true` |
| :487 `checkCancelled` | `cancelled == false` -> 통과 | `cancelled == true` -> `future.cancel(false)`(:425) 후 `CancellationException` 던짐(:427) |
| :491 `try` 진입 | 진입 | **미진입** |
| :494 `finally` | 실행 | **미실행** |
| :505 `afterAccess()` | count 1 -> 0 | **미호출.** count **1로 고정** |
| 다음 제출자 | `beforeAccess` 통과 | `count(1) >= limit(1)` -> `onLimitReached()`(CTS:145) -> `await()`(CTS:157)에서 **영구 대기** (reject 모드면 전건 `TaskRejectedException`) |

피해의 성격은 정지다.\
깨워 줄 `signal()`(CTS:195)을 호출할 주체가 사라졌으므로 한도가 1이면 executor가 사실상 죽는다.\
그리고 이 경로는 `submit`·`execute(Runnable)` 같은 통상 API로 도달한다 — 필요한 것은 throttle 활성 + 추적 활성 + 종료 시점 경합뿐이고, 마지막 항목은 애플리케이션 셧다운마다 벌어지는 상황이다.

> **경합 조건(race condition)** — 두 사건의 도착 순서에 따라 결과가 달라지는 상황.\
> 예: 워커가 `run()`에 닿는 시점과 `close()`가 `cancelled`를 세우는 시점 중 무엇이 먼저냐로 permit이 새는지가 갈린다.

### 3.3 이미 막혀 있던 세 번째 경로

같은 계열의 구멍 하나는 이 PR 이전에 이미 닫혀 있다.\
`doExecute`가 스레드 생성에 실패하면 워커가 없어 아무도 반납할 수 없으므로, 제출 스레드가 catch에서 직접 반납한다(:324-328).\
이 동작은 기존 테스트 `executeFailsToStartThreadReleasesConcurrencyPermit`이 지키고 있다.\
세 구멍 중 둘이 이 PR의 대상이다.

## 4. 계약과 위반

이 무대에서 지켜야 할 약속과, 이 결함이 그중 무엇을 어기는지를 나란히 놓는다.

| 계약 | 출처 | 이 결함이 어기는가 |
|---|---|---|
| "`afterAccess`는 보통 `finally` 블록에서 호출해야 한다" | `ConcurrencyThrottleSupport` 클래스 javadoc(CTS:32-35) | 형식상 지켰다(호출은 finally에 있다). 그러나 그 finally가 **획득하지 않은 경우에도** 돌고, **획득한 경우에도 안 돌 수 있다** — 계약의 의도를 어긴다 |
| `beforeAccess()` 1회당 `afterAccess()` 정확히 1회 | 명시 javadoc 없음. `concurrencyCount`가 `int` 하나(CTS:79)라는 구조가 강제하는 암묵 불변식 | 양방향으로 위반. A는 초과 반납, B는 미반납 |
| "Executes urgent tasks (with 'immediate' timeout) directly, bypassing the concurrency throttle (if active)." | `execute(Runnable, long)` javadoc(:303-305) | 결함 A는 이 계약의 **절반만** 지켰다. 획득은 우회했는데 반납은 우회하지 않았다 |
| `setConcurrencyLimit(n)`을 걸면 동시 실행이 n을 넘지 않는다 | `setConcurrencyLimit` javadoc(:239-245)과 `isThrottleActive` javadoc(:257-262) | 결함 A가 위반. 한도 2에서 3개가 동시 통과한다 |
| 취소된 태스크는 `future.cancel(false)` 후 `CancellationException`으로 끝난다 | `checkCancelled`(:422-429) | 위반하지 않는다. 결함 B에서도 취소 자체는 정상 수행된다 — **부작용만 남는다**는 점이 이 결함을 조용하게 만든다 |
| `ConcurrencyThrottleSupport`는 변경하지 않는다 | 이 작업의 명세 금지영역(`docs/plans/2026-06-13/spring-core-bug-hunt/B4-simpleasync-throttle/task.md` 4번 칸) | 수정안이 준수 — 변경은 executor 안에서만 |

## 5. 수정안

### 5.1 before / after

**(a) 획득 사실을 래퍼에 싣는다.**\
before는 base `0c60266986`의 :474-478, after는 head `322ab59bb88`의 :474-481이다.

```java
// before  SimpleAsyncTaskExecutor.java:474-478
		public TaskTrackingRunnable(Runnable task, @Nullable Future<?> future) {
			Assert.notNull(task, "Task must not be null");
			this.task = task;
			this.future = future;
		}
```

```java
// after  SimpleAsyncTaskExecutor.java:474-481
		private final boolean releaseThrottle;

		public TaskTrackingRunnable(Runnable task, @Nullable Future<?> future, boolean releaseThrottle) {
			Assert.notNull(task, "Task must not be null");
			this.task = task;
			this.future = future;
			this.releaseThrottle = releaseThrottle;
		}
```

호출부 두 곳이 서로 다른 값을 넘긴다 — 분기 1(:322)은 `true`, 분기 2(:331)는 `false`.

**(b) `try` 범위를 `run()` 본문 전체로 넓히고 반납을 플래그 아래로 옮긴다.**

```java
// before  SimpleAsyncTaskExecutor.java:481-507
		public void run() {
			Set<Thread> threads = activeThreads;
			Thread thread = null;
			if (threads != null) {
				thread = Thread.currentThread();
				synchronized (threads) {
					checkCancelled(this.future);
					threads.add(thread);
				}
			}
			try {
				this.task.run();
			}
			finally {
				if (threads != null) {
					threads.remove(thread);
					if (closed.get()) {
						synchronized (threads) {
							if (threads.isEmpty()) {
								threads.notify();
							}
						}
					}
				}
				concurrencyThrottle.afterAccess();
			}
		}
```

```java
// after  SimpleAsyncTaskExecutor.java:484-514
		public void run() {
			Set<Thread> threads = activeThreads;
			Thread thread = null;
			try {
				if (threads != null) {
					thread = Thread.currentThread();
					synchronized (threads) {
						checkCancelled(this.future);
						threads.add(thread);
					}
				}
				this.task.run();
			}
			finally {
				if (threads != null) {
					threads.remove(thread);
					if (closed.get()) {
						synchronized (threads) {
							if (threads.isEmpty()) {
								threads.notify();
							}
						}
					}
				}
				// Release the throttle permit only if one was acquired (see execute),
				// and always release it once acquired -- even if checkCancelled() above threw.
				if (this.releaseThrottle) {
					concurrencyThrottle.afterAccess();
				}
			}
		}
```

### 5.2 왜 그 위치인가

두 변경이 각각 하나의 결함에 대응하고, 서로를 대신할 수 없다.

- `releaseThrottle` 플래그는 **결함 A만** 막는다. 획득 여부를 아는 유일한 코드가 `execute`이므로 정보의 출처가 거기여야 하고, 그것을 소비하는 코드가 `run()`이므로 운반 수단은 스레드 경계를 넘는 유일한 객체인 래퍼여야 한다. 다른 자리(예: executor 필드)에 두면 태스크마다 다른 값을 가질 수 없다.
- `try` 범위 확장은 **결함 B만** 막는다. 워커 스레드 입장에서 permit은 `run()` 첫 줄부터 이미 들고 있는 리소스이므로, 정리 코드를 보증하려면 `try`가 첫 줄부터 시작해야 한다.

범위를 넓힐 때 걸리는 지점은 하나뿐이고 코드가 그것을 피해 간다.\
`finally`의 `threads.remove(thread)`가 `checkCancelled` 실패 시에도 실행되는데, `thread` 대입(:489)이 `synchronized` 블록보다 앞에 있으므로 그 시점에 `thread`는 이미 non-null이다.\
아직 집합에 넣지 않은 스레드를 지우는 것이라 무해한 no-op이다.

> **no-op** — 실행은 되지만 상태를 바꾸지 않는 동작.\
> 예: 집합에 들어간 적 없는 스레드에 대한 `threads.remove(thread)`는 아무것도 지우지 못하고 그냥 끝난다.

### 5.3 검토된 대안과 기각 이유

같은 결함을 다르게 막을 수 있었던 길이 다섯 있었고, 각각 다른 이유로 기각되었다.

| 대안 | 내용 | 기각 이유 |
|---|---|---|
| 분기 2에서도 `beforeAccess()`를 부른다 | 획득 조건을 반납 조건에 맞춘다 | `execute` javadoc(:303-305)이 "immediate 태스크는 throttle을 우회한다"를 명시한다. 계약을 바꾸는 수정이 된다 |
| `afterAccess()`가 count 0 이하에서 no-op | 지원 클래스에서 방어 | 명세 금지영역(`ConcurrencyThrottleSupport` 불변). 다른 사용처(`ConcurrencyThrottleInterceptor`, `SyncTaskExecutor`)의 계약까지 바꾼다. 게다가 결함 B(누수)는 전혀 막지 못한다 |
| `execute`의 catch를 넓혀 취소도 잡는다 | 반납을 제출 스레드로 일원화 | 취소는 워커 스레드에서 나므로 제출 스레드의 catch가 볼 수 없다. 물리적으로 불가능 |
| `try` 범위만 넓히고 플래그는 안 넣는다 | 변경 최소화 | 결함 A가 그대로 남는다. 오히려 `checkCancelled` 실패 경로에서도 `afterAccess`가 돌게 되어 A의 발동 폭이 늘어난다 |
| `checkCancelled`를 제출 시점(`execute`)으로 옮긴다 | 취소를 워커 밖에서 판정 | `cancelled`는 제출 이후 세워지므로 경합이 그대로 남고, `close()`가 세운 신호를 뒤늦게 출발한 워커가 못 본다 |

### 5.4 검증이 고정하는 값

테스트 두 건이 리플렉션으로 `concurrencyCount`를 직접 읽어 간접 증상이 아니라 숫자 자체를 단언한다 — `immediateTaskDoesNotReleaseThrottlePermit`은 fix 전 -1 / 기대 0, `cancelledThrottledTaskReleasesPermit`은 fix 전 1 / 기대 0(상세는 `tests.md`).\
두 red가 서로 반대 방향의 오수정을 막으므로 별도 가드 테스트가 없다.

## 6. 범위 밖과 인접 영향

**같은 지원 클래스를 쓰는 다른 두 곳은 이 결함 패턴이 없다.**\
grep으로 확인한 `beforeAccess`/`afterAccess` 호출처는 셋인데, 나머지 둘은 획득과 반납이 **같은 메서드의 같은 스코프**에 있다.

```java
// spring-aop/.../interceptor/ConcurrencyThrottleInterceptor.java:67-73
		beforeAccess();
		try {
			return methodInvocation.proceed();
		}
		finally {
			afterAccess();
		}
```

`SyncTaskExecutor.execute(Runnable)`(:78-85)와 `execute(TaskCallback)`(:108-116)도 같은 형태다.\
스레드 경계도 조건 불일치도 없으므로 언어가 짝을 강제한다.\
결함이 `SimpleAsyncTaskExecutor`에만 있는 이유가 여기서 드러난다 — **비동기 실행기만 획득과 반납이 서로 다른 스레드에 산다.**

같은 지원 클래스를 쓰는데 왜 한쪽만 깨지는지를 나란히 놓으면 이렇다.

```text
ConcurrencyThrottleInterceptor          SimpleAsyncTaskExecutor
+----------------------------+        +----------------------------+
| beforeAccess()             |        | execute:  beforeAccess()   |
| try {                      |        |   ==== 스레드 경계 ====    |
|   proceed()                |        | run(): checkCancelled()    |
| }                          |        |   try { task.run() }       |
| finally {                  |        |   finally {                |
|   afterAccess()            |        |     afterAccess()          |
| }                          |        |   }                        |
+----------------------------+        +----------------------------+
  -> 같은 스코프, 언어가 짝 강제         -> 스코프가 갈려 짝이 안 보장된다
```

**하위호환.**\
바뀐 생성자 `TaskTrackingRunnable(Runnable, Future, boolean)`는 `private` 내부 클래스의 것이라 공개 API 표면이 아니다.\
`execute`·`submit`·`doExecute`의 시그니처는 그대로다.\
동작 변화는 두 가지로 한정된다.\
(1) immediate 태스크가 더 이상 `concurrencyCount`를 내리지 않는다 — 이는 javadoc이 이미 약속한 "우회"의 완성이다.\
(2) 취소로 이탈한 throttled 태스크가 permit을 돌려준다 — 이전에는 누수였으므로 이 변화에 의존하던 정상 사용자는 존재할 수 없다.

**인접하지만 건드리지 않는 것.**\
`activeThreads`(:93)는 살아 있는 워커 집합을 실제로 들고 있지만 용도가 종료 대기와 인터럽트뿐이라 throttle 회계와 대조되지 않는다 — 정합성 검증 재료가 옆에 있는데도 쓰이지 않는다.\
`cancelled`의 비-volatile 모니터 규약(:101)도 그대로 둔다(결함 B는 가시성이 아니라 `try` 범위 문제였다).\
`execute(Runnable, long)`의 deprecation도 유지한다 — 결함 A의 입구가 deprecated API인데도 수정을 생략하지 않은 근거는, 같은 `run()` 코드가 결함 B에서 현행 API로 도달한다는 점이다.
