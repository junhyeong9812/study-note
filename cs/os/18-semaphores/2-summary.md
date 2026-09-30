# os/18-semaphores — 세마포어: 신호를 저장하는 카운터로 개수 제한과 순서 맞추기 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> ⚠️ 이 서머리는 Claude 초안(2026-09-30) — 근거는 아래 「관련 주제·근거」. 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 해결하는 문제

기초는 기존 초안 [systems/semaphore](../../systems/semaphore/2-summary.md)에 있다.\
요약: 세마포어는 "동시에 N개까지"를 세는 카운터다. 자리가 나면 들여보내며 −1, 나갈 때 +1이다. 포화 때는 줄 세우기와 즉시 거절 중 하나를 고른다.

> 참고: 기존 초안의 "카운터가 1이면 뮤텍스와 사실상 같다"는 **상호 배제** 면에서만 맞다. 세마포어에는 **소유자 개념이 없어서** 잡지 않은 스레드도 풀 수 있다(Java SE `Semaphore` 문서). 재진입도 없다 — 같은 스레드가 두 번 wait하면 permit을 두 개 쓴다. 아래 「동작·원리」 5절.

이 노트는 그 카운터의 **안쪽**과 **두 번째 용도**를 본다.

```text
  세마포어의 세 가지 용도 (초깃값이 용도를 정한다, OSTEP 31장)

  초깃값   용도                   예
  1        이진 세마포어 = 락         임계 구역 보호
  0        순서 맞추기(ordering)     "자식이 끝나면 부모가 진행"
  N        개수 제한(counting)       커넥션 N개, 동시 요청 N건, 버퍼 칸 N개
```

쉬운 예: 주차장 입구의 "빈자리 N" 전광판이다.
- 차가 들어가면 숫자가 줄고, 나가면 는다. 0이면 입구에서 기다린다.
- 전광판은 **숫자를 기억한다**. 아무도 기다리지 않을 때 차가 나가도, 다음 차는 그 빈자리를 바로 쓴다.

똑같은 구조다.\
17번의 조건 변수는 신호를 기억하지 않았다. 세마포어는 **신호를 숫자로 저장한다.** 그래서 "먼저 신호, 나중에 대기" 순서여도 잃어버리지 않는다.

실무 예:
- 외부 API 동시 호출 수 제한, DB 커넥션 풀, 스레드 스로틀링(OSTEP 31.7).
- 서비스 격리(bulkhead)가 호출 대상별 세마포어로 만들어진다([ops-patterns/03-bulkhead](../../ops-patterns/03-bulkhead/2-summary.md)).
- 생산자/소비자의 유한 버퍼.

## 동작·원리

### 1. 정의 — P와 V

```text
  sem_wait(s)   (Dijkstra의 P)                sem_post(s)   (Dijkstra의 V)
    값을 1 줄인다                                값을 1 늘린다
    값이 0 미만이면 잠든다                         기다리는 스레드가 있으면 하나 깨운다
```

- 위는 OSTEP 그림 31.2의 **Dijkstra식 정의**다. 여기서는 값이 음수가 될 수 있고, 음수일 때 절댓값이 대기자 수다(OSTEP 31.1).
- **리눅스 구현은 다르다.** 값은 0 밑으로 내려가지 않는다. 0이면 `sem_wait`가 값이 양수가 될 때까지 막힌다(sem_overview(7)).
  - `sem_getvalue(3)`: 대기자가 있을 때 POSIX는 "0" 또는 "대기자 수의 음수" 둘 다 허용한다. 리눅스는 **0**을 돌려준다.
  - OSTEP 31.8도 자기 구현(Zemaphore)이 음수를 유지하지 않으며 "현재 리눅스 구현과 맞다"고 적는다.

```text
  리눅스 식 상태 변화 (초깃값 2)

  동작          값    대기 큐
  A wait        1     -
  B wait        0     -
  C wait        0     [C]        ← 막힘 (값은 0에서 멈춤)
  A post        0     -          ← C를 깨우고, C가 그 1을 가져감
  B post        1     -
```

  - *P / V*: Dijkstra가 붙인 이름이다. 네덜란드어에서 왔고 어원 설명은 시기마다 달랐다(OSTEP 31.1 각주).
  - *이진 세마포어*: 값이 0과 1만 오가게 쓰는 세마포어다. 초깃값 1로 락처럼 쓴다.

### 2. 순서 맞추기 — 초깃값 0

```text
  부모                          자식
  sem_init(&s, 0, 0)
  create(child)
  sem_wait(&s)   ── 값 0 → 잠듦
                                printf("child")
                                sem_post(&s)  ── 값 1 → 부모 깨움
  "parent: end"
```

- 자식이 먼저 끝나도 된다. `sem_post`가 값을 1로 **저장**하고, 부모의 `sem_wait`는 그 1을 쓰고 바로 통과한다(OSTEP 31.3).
- 17번 조건 변수로 같은 일을 하려면 상태 변수 `done`과 락이 따로 필요했다. 세마포어는 그 "상태"를 값 안에 갖고 있다.

### 3. 유한 버퍼 — 세마포어 세 개

```text
  empty = MAX (빈 칸 수)    full = 0 (찬 칸 수)    mutex = 1 (버퍼 인덱스 보호)

  생산자                             소비자
  sem_wait(&empty)   빈 칸 하나 예약      sem_wait(&full)    찬 칸 하나 예약
  sem_wait(&mutex)                     sem_wait(&mutex)
  put(i)                               tmp = get()
  sem_post(&mutex)                     sem_post(&mutex)
  sem_post(&full)    찬 칸 +1           sem_post(&empty)   빈 칸 +1
```

- `empty`·`full`은 **개수**를 센다. `mutex`는 `fill`·`use` 인덱스를 두 생산자가 동시에 건드리지 않게 한다(OSTEP 31.4).
- **순서가 중요하다.** `mutex`를 먼저 잡고 `full`을 기다리면 교착이다.

```text
  잘못된 순서 (OSTEP 그림 31.11 — 생산자·소비자 모두 mutex를 먼저 잡는다)

  소비자: sem_wait(&mutex) 성공 → sem_wait(&full) → 값 0 → 잠듦  (mutex를 쥔 채!)
  생산자: sem_wait(&mutex) → 잠듦   (empty까지 가 보지도 못한다)
  → 소비자는 full을, 생산자는 mutex를 기다린다. 서로가 서로를 기다리는 사이클 = 교착 (19번)
```

- 생산자가 올바른 순서(`empty` 먼저)여도 소비자 한쪽만 틀리면 같은 교착이 난다. 생산자는 `empty`를 통과한 뒤 `mutex`에서 막힌다.

- 해법: 락의 범위를 줄인다. 개수 세마포어 대기는 락 **밖**에서, 락은 버퍼 조작만 감싼다(OSTEP 그림 31.12).

### 4. 세마포어로 만드는 것, 세마포어를 만드는 것

- 세마포어로 만드는 것 (OSTEP 31.5~31.7)
  - **읽기-쓰기 락**: 첫 독자가 쓰기 락을 잡고 마지막 독자가 푼다. 독자가 계속 오면 **작가가 굶는다**.
  - **식사하는 철학자**: 모두 왼쪽 포크부터 잡으면 교착이다. 한 명만 오른쪽부터 잡게 해 사이클을 끊는다(Dijkstra의 해법).
  - **스로틀링**: 메모리를 많이 쓰는 구간에 동시에 들어가는 스레드 수를 제한해 스래싱을 막는다. 입장 제어(admission control)의 한 형태다.
- 세마포어를 만드는 것 (OSTEP 31.8)
  - 락 하나 + 조건 변수 하나 + 정수 하나로 만든다. `wait`는 `while (value <= 0) cond_wait`, `post`는 `value++; cond_signal`이다. 17번의 도구로 18번을 만든 셈이다.
  - 리눅스 glibc의 `sem_t`는 futex로 잠든다. 로컬 재현(예시, 리눅스 7.0)에서 값 0인 `sem_wait`는 `futex(..., FUTEX_WAIT_BITSET_PRIVATE|FUTEX_CLOCK_REALTIME, 0, NULL, ...)`로 잠들었고, `sem_post`는 `FUTEX_WAKE_PRIVATE`를 불렀다.

### 5. 세마포어 vs 뮤텍스 — 소유자가 없다

```text
                    뮤텍스 (ReentrantLock, pthread_mutex)   세마포어
  소유자             있다 — 잡은 스레드만 푼다                  없다 — 아무 스레드나 post 가능
  재진입             ReentrantLock은 됨                       안 됨 (같은 스레드가 두 번 wait 하면 2 소모)
  상한 검사          —                                       post가 초깃값을 넘겨도 막지 않는다
  JVM 교착 탐지       synchronized·ReentrantLock은 탐지됨       탐지 안 됨 (소유자가 없어 사이클을 그릴 수 없다)
```

- Java 문서: 세마포어는 소유 개념이 없어 "소유자가 아닌 스레드가 풀 수 있다". release하는 스레드가 acquire했어야 한다는 요구도 없다. 올바른 사용은 **프로그래밍 관례**로 지킨다(Java SE `Semaphore`).
- 상한이 없다: 로컬 재현(JDK 21)에서 `new Semaphore(2)`에 `release()`를 두 번 더 하자 `availablePermits()`가 4가 됐다. POSIX `sem_post`도 `SEM_VALUE_MAX`(이 환경 2147483647)에 닿기 전까지는 막지 않는다(`EOVERFLOW`, sem_post(3)).
- 교착 탐지: 로컬 재현(JDK 21)에서 두 스레드가 세마포어 두 개를 엇갈려 기다리게 했더니 `ThreadMXBean.findDeadlockedThreads()`가 `null`이었다. 문서도 이 메서드는 "object monitor 또는 ownable synchronizer"의 사이클만 찾는다고 적는다.

## 쓰이는 자료구조·알고리즘

- **카운터 + 대기 큐** — 세마포어의 전부다. 카운터는 남은 permit, 대기 큐는 막힌 스레드다. [data-structure/04-queue-deque](../../data-structure/04-queue-deque/2-summary.md)
- **공정성 = 큐 규율** — Java `Semaphore(n, true)`는 FIFO로 permit을 준다. `false`(기본)는 새로 온 스레드가 대기자를 앞지르는 **barging**을 허용한다. 시간 제한 없는 `tryAcquire()`는 공정 설정을 무시한다(Java SE `Semaphore`).
  - Java 구현은 AQS(AbstractQueuedSynchronizer)의 공유 모드 대기 큐를 쓴다. 대기 중인 스레드 덤프에 `AbstractQueuedSynchronizer.acquireSharedInterruptibly`가 보인다(로컬 재현).
- **원형 버퍼** — 유한 버퍼의 `put`·`get`은 `(i + 1) % MAX`로 도는 배열이다(OSTEP 31.4).
- **futex** — 리눅스에서 대기 큐는 커널 futex 해시 버킷에 있다([16-locks-and-spinlocks](../16-locks-and-spinlocks/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 개수 제한 — Java

```java
private final Semaphore permits = new Semaphore(10, true);   // 동시 10건, 공정

Response call(Request r) throws Exception {
    if (!permits.tryAcquire(200, TimeUnit.MILLISECONDS)) {    // 무한 대기 대신 시간 제한 (200ms는 예시)
        throw new RejectedException("busy");                  // 포화 → 빠른 거절 (기존 초안의 503 선택)
    }
    try {
        return downstream.call(r);
    } finally {
        permits.release();                                     // 예외 경로에서도 반드시 반납
    }
}
```

- `acquire()`와 `try` 사이에 다른 코드를 두지 않는다. 그 사이에서 예외가 나면 반납이 빠진다.
- `release()`를 두 번 부르는 경로가 없는지 본다. 상한 검사가 없어 permit이 늘어난다(5절).
- 자원 접근 제어용 세마포어는 기아를 막으려 **공정**하게 만들라고 Java 문서가 권한다. 다른 용도의 동기화에는 비공정의 처리량 이득이 더 클 수 있다.

### 2. 유한 버퍼 — C

```c
sem_t empty, full, mutex;
sem_init(&empty, 0, MAX);   /* pshared=0: 한 프로세스의 스레드끼리 */
sem_init(&full,  0, 0);
sem_init(&mutex, 0, 1);

void produce(int v) {
    while (sem_wait(&empty) == -1 && errno == EINTR) ;   /* 시그널 핸들러에 끊기면 다시 */
    sem_wait(&mutex);  put(v);  sem_post(&mutex);        /* 락은 버퍼 조작만 감싼다 */
    sem_post(&full);
}
```

- `sem_wait`는 시그널 핸들러에 끊기면 `EINTR`로 실패한다. 재시도 루프를 둔다(sem_wait(3) 예제가 같은 형태). 시그널은 [06-signals](../06-signals/2-summary.md).
- `sem_post`는 async-signal-safe다. 시그널 핸들러에서 불러도 된다(POSIX `sem_post`). signal-safety(7)의 안전 함수 목록에 `sem_post`는 있고 `pthread_mutex_*`·`pthread_cond_*`는 없다.

### 3. 프로세스 사이 — 이름 있는 세마포어

- `sem_open("/name", O_CREAT, 0600, 1)`로 만든다. 리눅스에서는 `/dev/shm/sem.name` 파일로 보인다(sem_overview(7)).
- **커널 지속성**: `sem_unlink`하지 않으면 시스템이 꺼질 때까지 남는다. 프로세스가 죽어도 값이 그대로다(sem_overview(7)).
- 이름 없는 세마포어를 프로세스끼리 쓰려면 공유 메모리에 두고 `pshared=1`로 초기화한다([30-ipc](../30-ipc/2-summary.md)).

### 4. 진단 명령

```bash
# Java: permit을 기다리는 스레드
jstack <pid> | grep -B3 -A6 'Semaphore\$\(Nonfair\|Fair\)Sync'
#   "WAITING (parking)" + "parking to wait for <...> (a java.util.concurrent.Semaphore$NonfairSync)"

# 애플리케이션이 노출하는 값: availablePermits(), getQueueLength()를 지표로 내보낸다

# 이름 있는 POSIX 세마포어 목록
ls -l /dev/shm/sem.*

# C: sem_wait로 막힌 스레드
ps -L -o pid,lwp,stat,wchan:20,comm -p <pid>      # S + futex_do_wait
```

## 장애 시나리오와 대처

### 1. 예외 경로에서 release 누락 → permit이 영구 소진돼 멈춤

- **현상**: 하위 서비스가 몇 번 에러를 낸 뒤부터 해당 기능이 완전히 멈춘다. 하위 서비스는 이미 회복했다.
- **보이는 형태**
  - `availablePermits()`가 에러 횟수만큼 줄어 0에서 멈춘다.
  - 스레드 덤프에 `WAITING (parking)` + `parking to wait for <...> (a java.util.concurrent.Semaphore$NonfairSync)`인 스레드가 쌓인다. `jstack`의 교착 탐지에는 걸리지 않는다.
  - 로컬 재현(예시, JDK 21): `Semaphore(2)`에서 짝수 번째 호출이 `release()` 전에 예외를 던지게 했다. 에러 두 번 뒤 `availablePermits()`가 0이 됐고, 다음 `tryAcquire(1, SECONDS)`는 `false`였다. 시간 제한 없는 `acquire()`였다면 영원히 기다렸다.
- **원인**: `acquire()` 뒤 `release()`가 `finally`에 있지 않았다. 소유자가 없으니 누가 "잡고 안 놓았는지" 추적할 방법도 없다.
- **대처**
  - `acquire` 직후 `try { … } finally { release(); }` 형식을 강제한다.
  - 무한 대기 대신 `tryAcquire(timeout)`을 쓰고, 실패를 지표로 낸다.
  - `availablePermits()`를 지표로 내보내고, 유휴 시간에도 초깃값으로 돌아오지 않으면 경보를 건다.

### 2. release 두 번 → 상한이 조용히 늘어 하위 서비스 과부하

- **현상**: 동시 요청을 10건으로 막았는데 하위 서비스가 그보다 많은 동시 요청을 받는다.
- **보이는 형태**: `availablePermits()`가 초깃값보다 크다. 하위 서비스의 연결 수·지연이 오른다.
- **원인**: 재시도·콜백 경로에서 `release()`가 두 번 불렸다. Java `Semaphore`와 POSIX `sem_post`는 초깃값 상한을 검사하지 않는다(5절 로컬 재현: 2 → 4).
- **대처**: 반납을 한 곳(`finally`)으로 모은다. 한 번만 반납하도록 호출 단위 플래그를 두거나, 반납 여부를 검사하는 래퍼를 쓴다([ops-patterns/03-bulkhead](../../ops-patterns/03-bulkhead/2-summary.md)).

### 3. 락을 쥔 채 개수 세마포어를 기다림 → 교착

- **현상**: 생산자와 소비자가 모두 멈춘다. CPU는 0%다.
- **보이는 형태**: 소비자는 `full`에서, 생산자는 `mutex`에서 기다린다(C라면 둘 다 `S` + `futex_do_wait`). Java라면 스레드 덤프에 둘 다 `Semaphore$...Sync`에서 `WAITING (parking)`이고 교착 탐지 메시지는 없다.
- **원인**: `sem_wait(&mutex)` 뒤에 `sem_wait(&full)`을 불렀다. 소비자가 `mutex`를 쥔 채 잠들어 생산자가 `mutex`를 못 잡는다(OSTEP 그림 31.11).
- **대처**: 개수 대기는 락 밖에서 먼저 하고, 락은 버퍼 조작만 감싼다(OSTEP 그림 31.12). 세마포어 교착은 JVM이 탐지하지 않으므로 코드 리뷰와 시간 제한 대기로 막는다.

### 4. 이름 있는 세마포어가 크래시 뒤에도 남음 → 재시작해도 멈춤

- **현상**: 프로세스가 죽은 뒤 재시작했는데 첫 요청부터 막힌다.
- **보이는 형태**
  - `/dev/shm/sem.<name>` 파일이 남아 있다.
  - 로컬 재현(예시, 리눅스 7.0): 초깃값 1로 `sem_open` → `sem_trywait` 성공 → `sem_post` 없이 `_exit`. 다음 실행에서 값은 0이었고 `sem_trywait`는 `EAGAIN`("Resource temporarily unavailable")이었다. `sem_unlink` 뒤 파일이 사라졌다.
- **원인**: 이름 있는 세마포어는 커널 지속성을 가진다. 프로세스가 죽어도 잡은 permit은 반납되지 않는다(sem_overview(7)).
- **대처**
  - 시작 시 옛 세마포어를 `sem_unlink`하고 새로 만든다(단, 다른 프로세스가 쓰는 중이 아닐 때).
  - 프로세스 사이 상호 배제가 목적이면 소유자가 죽었을 때 알려 주는 robust 뮤텍스(`EOWNERDEAD`)나 파일 락(`flock`)을 검토한다. `flock` 락은 그 open file description을 가리키는 fd가 모두 닫히면 풀린다(flock(2)). 그래서 fork로 fd를 물려받은 다른 프로세스가 없다면 프로세스가 죽을 때 함께 풀린다.

### 5. 대기열에 상한이 없음 → 지연 폭증

- **현상**: 포화 때 요청이 실패하지 않고 한없이 느려진다. 결국 상위 타임아웃이 먼저 터진다.
- **보이는 형태**: `getQueueLength()`가 계속 오른다. 스레드 풀이 `acquire()` 대기로 가득 찬다.
- **원인**: 세마포어는 permit 수만 제한한다. 기다리는 쪽의 수는 제한하지 않는다(기존 초안의 "대기열 상한" 함정).
- **대처**: `tryAcquire(timeout)`으로 대기 시간을 제한하거나, 즉시 거절한다. 대기열 길이 자체에 상한을 둔다([ops-patterns/05-backpressure](../../ops-patterns/05-backpressure/2-summary.md)).

## 핵심 문장

- 세마포어는 카운터 + 대기 큐다. 초깃값이 용도를 정한다: 1이면 락, 0이면 순서 맞추기, N이면 개수 제한.
- 조건 변수와 달리 세마포어는 신호를 **값으로 저장**한다. 그래서 post가 wait보다 먼저 와도 잃지 않는다.
- 리눅스 세마포어 값은 0 밑으로 내려가지 않는다. 음수 = 대기자 수라는 Dijkstra 정의와 다르다.
- 세마포어에는 소유자가 없다. 아무나 post할 수 있고, 상한을 검사하지 않으며, JVM 교착 탐지에도 안 잡힌다. 반납은 `finally` 한 곳에서 한다.
- 개수 세마포어 대기를 락 안에서 하면 교착이다. 락은 버퍼 조작만 감싼다.

## 관련 주제·근거

- 기초(기존 초안): [systems/semaphore](../../systems/semaphore/2-summary.md) — 식당 비유, 포화 시 대기 vs 즉시 거절, 반납 누락·대기열 상한
- 선행: [17-condition-variables-and-monitors](../17-condition-variables-and-monitors/2-summary.md) — 신호를 저장하지 않는 대기, 세마포어를 만드는 재료
- 후속·연결
  - [19-deadlock](../19-deadlock/2-summary.md) — 식사하는 철학자·잘못된 락 순서
  - [16-locks-and-spinlocks](../16-locks-and-spinlocks/2-summary.md) — futex
  - [30-ipc](../30-ipc/2-summary.md) — 프로세스 공유 세마포어
  - [12-swapping-and-page-replacement](../12-swapping-and-page-replacement/2-summary.md) — 스로틀링이 막는 스래싱
  - [ops-patterns/03-bulkhead](../../ops-patterns/03-bulkhead/2-summary.md) · [ops-patterns/05-backpressure](../../ops-patterns/05-backpressure/2-summary.md)
- 교재
  - OSTEP 31장 "Semaphores" — 31.1 정의(P/V, 음수 = 대기자 수), 31.2 이진 세마포어, 31.3 순서, 31.4 유한 버퍼(그림 31.11 교착, 31.12 정답), 31.5 읽기-쓰기 락, 31.6 식사하는 철학자, 31.7 스로틀링, 31.8 구현(Zemaphore) <https://pages.cs.wisc.edu/~remzi/OSTEP/threads-sema.pdf>
- Linux·POSIX
  - sem_overview(7) — 값은 0 미만 불가, 이름 있는/없는 세마포어, 커널 지속성, `/dev/shm/sem.*` <https://man7.org/linux/man-pages/man7/sem_overview.7.html>
  - sem_wait(3) — `EINTR` 재시도 예제 · sem_post(3) — `EOVERFLOW`(`SEM_VALUE_MAX`) · sem_getvalue(3) — 대기자 있을 때 리눅스는 0 <https://man7.org/linux/man-pages/man3/sem_getvalue.3.html>
  - signal-safety(7) — async-signal-safe 함수 목록 · flock(2) — 모든 fd가 닫히면 해제 <https://man7.org/linux/man-pages/man7/signal-safety.7.html>
  - POSIX.1-2024 `sem_post` — async-signal-safe <https://pubs.opengroup.org/onlinepubs/9799919799/functions/sem_post.html>
- Java SE 21 API
  - `Semaphore` — 소유자 없음, 공정성·barging, `tryAcquire()`의 공정성 무시, release 관례 <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/Semaphore.html>
  - `ThreadMXBean.findDeadlockedThreads` — monitor·ownable synchronizer 사이클만 <https://docs.oracle.com/en/java/javase/21/docs/api/java.management/java/lang/management/ThreadMXBean.html>
- 로컬 재현(리눅스 7.0, glibc 2.39, JDK 21): release 누락 시 permit 소진(`Semaphore(2)` → 0 → `tryAcquire` false), 추가 release로 permit 2 → 4, 세마포어 교차 대기에서 `findDeadlockedThreads()` = null, 대기 스레드의 jstack 상태, `sem_wait`/`sem_post`의 futex 호출, 이름 있는 세마포어의 크래시 후 잔존(`/dev/shm/sem.os18demo`)
