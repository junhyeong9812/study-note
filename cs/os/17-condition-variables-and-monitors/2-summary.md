# os/17-condition-variables-and-monitors — 조건이 될 때까지 잠들기: 조건 변수와 모니터 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> ⚠️ 이 서머리는 Claude 초안(2026-09-30) — 근거는 아래 「관련 주제·근거」. 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 해결하는 문제

락(16번)은 "한 번에 한 명만 들어가기"를 해결한다.\
그런데 스레드는 자주 **"어떤 조건이 될 때까지"** 기다려야 한다.

```text
  기다려야 하는 조건 예
  소비자:   큐가 비어 있지 않을 때까지
  생산자:   큐에 빈자리가 생길 때까지
  부모:     자식 스레드가 끝날 때까지 (join)
  워커:     설정 로딩이 끝날 때까지
```

락만으로 기다리면 두 가지 방법뿐이다. 둘 다 나쁘다.

```text
  (1) 락을 쥔 채 잠든다      → 조건을 바꿔 줄 생산자가 락을 못 잡는다 → 영원히 대기
  (2) 락을 풀고 계속 확인한다  → while (queue.isEmpty()) { unlock; lock; }  → CPU를 태운다
```

필요한 것은 **"락을 풀고 잠들기"를 한 동작으로** 하고, 조건이 바뀌면 누군가 **깨워 주는** 장치다. 그것이 **조건 변수(condition variable)**다.

쉬운 예: 식당 대기석이다.
- 손님은 "자리가 나면 불러 주세요"라고 이름을 적고 앉는다(wait).
- 직원은 자리가 나면 이름을 부른다(signal).
- 불린 손님은 가서 **자리가 정말 비었는지 다시 본다**. 그사이 다른 손님이 앉았을 수 있다.

똑같은 구조다.\
조건 변수 = 대기자 명단(대기 큐) + "깨우기" 연산이다. 조건 자체는 **공유 변수**에 있고, 조건 변수는 그 변수를 대신하지 않는다.

실무 예:
- Java의 `BlockingQueue`(`ArrayBlockingQueue`)의 `put`·`take`는 락 하나와 조건 변수 두 개로 만든다.
- 스레드 풀의 작업 큐, 커넥션 풀의 "빈 커넥션 대기"가 같은 구조다.

## 동작·원리

### 1. wait / signal / broadcast

```text
  pthread_cond_wait(&c, &m)     (m을 쥔 상태에서 불러야 한다)
    ① m을 풀고 c의 대기 큐에서 잠드는 것을 원자적으로 한다
    ② 깨어나면
    ③ m을 다시 잡은 뒤에야 돌아온다

  pthread_cond_signal(&c)       c에서 자는 스레드를 적어도 하나 깨운다 (없으면 아무 일도 없다)
  pthread_cond_broadcast(&c)    c에서 자는 스레드를 모두 깨운다
```

- ①의 원자성이 핵심이다. POSIX는 "다른 스레드가 이 뮤텍스를 잡을 수 있게 된 뒤 부른 signal은, 잠들려던 스레드가 **잠든 뒤에** 부른 것처럼 동작해야 한다(shall)"고 정한다(POSIX `pthread_cond_wait`).
- signal은 대기자가 없으면 **아무 효과가 없다**(POSIX `pthread_cond_signal`). 신호가 저장되지 않는다. 이 점이 세마포어(18번)와 다르다.
- `pthread_cond_signal`은 "**적어도** 하나"를 깨운다. 멀티프로세서에서는 둘 이상이 깨어날 수 있다(같은 문서 RATIONALE).

  - *조건 변수*: 조건이 참이 되기를 기다리는 스레드들의 대기 큐다. 조건 자체를 기억하지 않는다.
  - *술어(predicate)*: 기다리는 조건을 나타내는 불리언 식이다. 예: `count > 0`. POSIX는 모든 조건 대기에 이런 술어가 있다고 전제한다.

### 2. 상태 변수가 없으면 — lost wakeup

```text
  잘못된 join (OSTEP 그림 30.4 — 상태 변수 없음)

  부모                                 자식
                                       exit: lock; signal(c); unlock;   ← 대기자 없음 → 신호가 사라짐
  join: lock; wait(c, m); ...          ← 이미 지나간 신호를 기다린다 → 영원히 잠듦
```

- 신호는 저장되지 않는다. 그래서 "자식이 끝났다"는 사실을 **공유 변수**(`done = 1`)에 적어야 한다.
- 부모는 `done`을 보고 이미 1이면 기다리지 않는다.

```text
  락 없이 확인하면 — 두 번째 lost wakeup (OSTEP 그림 30.5)

  부모                                 자식
  if (done == 0)   ← 0을 봄
                                       done = 1; signal(c);   ← 아직 아무도 안 잠듦
  wait(c)          ← 영원히 잠듦
```

- 확인(`done == 0`)과 잠들기 사이에 틈이 있으면 신호가 그 틈으로 빠진다.
- 그래서 **확인과 wait를 같은 락 안에서** 하고, 상태 변경과 signal도 그 락을 쥐고 한다. wait가 락을 원자적으로 풀며 잠들기 때문에 틈이 사라진다.
- 16번 futex의 "값 비교 + 잠들기"가 원자적인 이유와 같은 문제다.

로컬 재현(예시, 리눅스 7.0): 상태 변수 없이 signal을 먼저 보내고 `pthread_cond_timedwait`로 2초 기다렸더니 `ETIMEDOUT`이었다. 시간 제한이 없었다면 영원히 잤다.

### 3. Mesa 의미론 — 깨어났다고 조건이 참은 아니다

```text
  생산자 1, 소비자 2 (Tc1, Tc2), 큐 크기 1 — if로 대기할 때 (OSTEP 30.2)

  Tc1: lock; count == 0 → wait (잠듦)
  P:   lock; put(); count = 1; signal → Tc1을 "준비" 상태로; unlock
  Tc2: lock; count == 1 → get(); count = 0; unlock      ← Tc1보다 먼저 락을 잡음
  Tc1: (깨어나 락을 다시 잡음) if 는 이미 지나감 → get() → 빈 큐에서 꺼냄!
```

- signal은 "상태가 바뀌었을 수 있다"는 **힌트**다. 깨어난 스레드가 실제로 실행될 때 상태가 그대로라는 보장이 없다. 이 해석을 **Mesa 의미론**이라 부른다(OSTEP 30.2, Lampson & Redell 1980).
- 반대인 **Hoare 의미론**은 깨운 즉시 깨어난 스레드가 실행된다고 보장한다. 만들기 어려워서 "사실상 모든 시스템"이 Mesa를 쓴다(OSTEP 30.2).
- 게다가 POSIX는 **spurious wakeup**(아무도 깨우지 않았는데 돌아옴)이 "일어날 수 있다(may occur)"고 명시한다. 돌아왔다는 사실은 술어에 대해 아무것도 뜻하지 않으니, 술어를 다시 평가해야 한다(POSIX `pthread_cond_wait`).
- 결론: **조건은 `if`가 아니라 `while`로 기다린다.**

```c
pthread_mutex_lock(&m);
while (count == 0)                 /* if 가 아니다 */
    pthread_cond_wait(&fill, &m);
int v = get();
pthread_cond_signal(&empty);
pthread_mutex_unlock(&m);
```

  - *spurious wakeup*: signal·broadcast·타임아웃 없이 wait가 돌아오는 것이다. POSIX RATIONALE은 멀티프로세서에서 signal 하나가 두 스레드를 깨울 수 있는 구현 예를 들고, 이를 막으면 효율이 떨어지므로 허용한다고 적는다.

### 4. 조건 변수 하나면 — 모두가 잠드는 교착

```text
  조건 변수 1개(cond)를 생산자·소비자가 같이 쓸 때 (OSTEP 30.2, 그림 30.11 요약)

  Tc1, Tc2: 큐가 비어 cond에서 잠듦
  P:        put → signal(cond) → Tc1 깨움;  다음 put 하려는데 가득 참 → cond에서 잠듦
  Tc1:      get → signal(cond) → 누구를 깨울까? 대기자는 Tc2와 P
            → Tc2(소비자)를 깨우면: Tc2는 큐가 비었으니 다시 잠듦
  Tc1:      다음 get 하려니 비었음 → cond에서 잠듦
  결과:     P, Tc1, Tc2 모두 잠듦 — 생산자를 깨워야 했는데 소비자를 깨웠다
```

- 해법은 조건 변수를 **조건마다 하나씩** 두는 것이다.
  - 생산자는 `empty`에서 기다리고 `fill`에 신호한다.
  - 소비자는 `fill`에서 기다리고 `empty`에 신호한다.
- 누구를 깨워야 할지 모를 때는 `broadcast`로 모두 깨우고, 각자 while로 다시 확인하게 한다. OSTEP는 이를 **covering condition**이라 부른다(30.3, 메모리 할당기 예). 대가는 불필요한 깨움이다.

### 5. 모니터 — 락과 조건 변수를 언어가 묶은 것

```text
  모니터 (Brinch Hansen 1973, Hoare 1974)

  +----------------------------- 객체 -------------------------------+
  |  공유 상태 (balance, items ...)                                   |
  |  락 1개 — 메서드에 들어가면 자동으로 잡고, 나가면 자동으로 푼다        |
  |  조건 대기열 — wait / notify                                      |
  +------------------------------------------------------------------+
         ^ 진입 대기 (락을 기다림)          ^ 조건 대기 (wait set)
```

- 모니터는 "공유 상태 + 락 + 조건 대기"를 한 단위로 묶는다. 메서드 경계에서 락을 자동으로 잡고 푼다(OSTEP 부록 D).
- Java가 대표적이다.
  - 모든 객체는 모니터 하나를 가진다. `synchronized`가 그 락을 잡는다. 같은 스레드가 여러 번 잡을 수 있다(재진입)(JLS §17.1).
  - 모든 객체는 **wait set**도 하나 가진다. `wait()`·`notify()`·`notifyAll()`이 그 집합을 다룬다(JLS §17.2).
  - 모니터를 쥐지 않고 `wait`·`notify`를 부르면 `IllegalMonitorStateException`이다(Java SE `Object` 문서).
  - `notify()`는 대기자 중 **임의의** 하나를 깨운다(같은 문서).
- 객체 하나에 wait set이 **하나**뿐이라는 것이 한계다. 4절의 "조건 변수 하나" 문제가 그대로 생긴다.
  - `java.util.concurrent.locks.Condition`은 모니터 메서드를 별도 객체로 떼어 **락 하나에 wait set 여러 개**를 준다(Java SE `Condition` 문서).
- Java도 spurious wakeup을 허용한다. `Object.wait` 문서는 while 루프 안에서 기다리기를 권장하고, `Condition` 문서는 "항상 루프 안에서 기다려야 한다(should always)"고 적는다.

### 6. 리눅스에서는 — 역시 futex

로컬 재현(예시, 리눅스 7.0, glibc 2.39): 조건 변수에서 기다리는 스레드를 strace로 보면 `FUTEX_WAIT_BITSET_PRIVATE`로 잠들고, signal 쪽은 `FUTEX_WAKE_PRIVATE`를 부른다.

```text
  [pid 2044709] futex(0x...00c8, FUTEX_WAIT_BITSET_PRIVATE|FUTEX_CLOCK_REALTIME, 0, NULL, ...)   ← cond_wait
  [pid 2044708] futex(0x...00c8, FUTEX_WAKE_PRIVATE, 1) = 1                                    ← cond_signal
```

## 쓰이는 자료구조·알고리즘

- **대기 큐(wait set)** — 조건마다 잠든 스레드의 목록이다. Java `Object`의 wait set은 이름대로 "집합"이라 깨우는 순서를 약속하지 않는다(`notify`는 임의 선택). [data-structure/04-queue-deque](../../data-structure/04-queue-deque/2-summary.md)
- **원형 버퍼(bounded buffer)** — 생산자/소비자의 공유 버퍼다. `fill_ptr = (fill_ptr + 1) % MAX`(OSTEP 그림 30.13), `ArrayBlockingQueue`의 `putIndex`·`takeIndex`가 끝에서 0으로 돌아간다(OpenJDK 소스).
- **술어 재검사 루프** — "깨어남 → 락 다시 잡음 → 술어 확인 → 거짓이면 다시 대기". 조건 변수 사용의 기본 알고리즘이다.
- **futex 해시 버킷** — glibc 조건 변수도 결국 futex word 주소로 커널 대기 큐를 찾는다(16번).

## 적용 — 풀어나가는 법

### 1. 조건 대기의 체크리스트

```text
  [ ] 조건을 공유 변수(술어)로 적었나           (신호는 저장되지 않는다)
  [ ] 술어를 읽고 쓰는 곳은 모두 같은 락 안인가
  [ ] wait 는 while 루프 안인가
  [ ] 조건마다 조건 변수를 따로 두었나 (또는 broadcast 로 덮었나)
  [ ] 상태를 바꾼 뒤 락을 쥔 채 signal 하나      (OSTEP 팁: 단순하고 안전)
  [ ] 무한 대기 대신 시간 제한이 필요한가
```

### 2. Java — 락 하나, 조건 두 개

`ArrayBlockingQueue`의 `put`·`take`가 정확히 이 모양이다(OpenJDK 소스).

```java
final ReentrantLock lock = new ReentrantLock();
final Condition notEmpty = lock.newCondition();
final Condition notFull  = lock.newCondition();

public void put(E e) throws InterruptedException {
    lock.lockInterruptibly();
    try {
        while (count == items.length) notFull.await();    // 가득 차면 빈자리를 기다림
        enqueue(e);                                        // 안에서 notEmpty.signal()
    } finally { lock.unlock(); }
}

public E take() throws InterruptedException {
    lock.lockInterruptibly();
    try {
        while (count == 0) notEmpty.await();              // 비었으면 원소를 기다림
        return dequeue();                                  // 안에서 notFull.signal()
    } finally { lock.unlock(); }
}
```

- 직접 만들기 전에 `BlockingQueue`·`CountDownLatch`·`CompletableFuture` 같은 기성 도구로 풀리는지 먼저 본다.
- `synchronized` + `wait`/`notify`를 쓴다면, 기다리는 조건이 둘 이상일 때 `notifyAll()`을 쓴다(4절의 covering condition).

### 3. C — 시간 제한 대기

```c
struct timespec ts;
clock_gettime(CLOCK_REALTIME, &ts);    /* 조건 변수의 기본 시계는 CLOCK_REALTIME */
ts.tv_sec += 2;
pthread_mutex_lock(&m);
int rc = 0;
while (!ready && rc != ETIMEDOUT)
    rc = pthread_cond_timedwait(&c, &m, &ts);   /* 절대 시각 — 루프를 돌아도 기한은 그대로 */
pthread_mutex_unlock(&m);
```

- `pthread_cond_timedwait`의 시계는 조건 변수 속성에서 오고, 설정하지 않으면 `CLOCK_REALTIME`이다(POSIX). 벽시계 조정에 흔들리지 않으려면 `pthread_condattr_setclock(CLOCK_MONOTONIC)`으로 만들거나 `pthread_cond_clockwait`를 쓴다(POSIX.1-2024).

### 4. 진단 명령

```bash
# Java: 조건 대기 중인 스레드 (아래 상태 문자열은 로컬 재현, JDK 21)
jstack <pid> | grep -B1 -A4 'WAITING (on object monitor)\|parking to wait for'
#   Object.wait()         -> "WAITING (on object monitor)"
#   Condition.await()     -> "WAITING (parking)" + "parking to wait for <...ConditionObject>"

# C: 스레드별 상태와 대기 위치 (조건 대기도 S + futex_do_wait)
ps -L -o pid,lwp,stat,wchan:20,comm -p <pid>

# 누가 누구를 깨우는가
strace -f -tt -e trace=futex -p <pid>
```

## 장애 시나리오와 대처

### 1. `if`로 대기 → 깨어났는데 큐가 비어 있다

- **현상**: 가끔, 부하가 높을 때만 소비자가 빈 큐에서 꺼내다 실패한다.
- **보이는 형태**
  - Java `NoSuchElementException`, `NullPointerException`(빈 큐의 `poll()`이 `null`), C라면 쓰레기 값·음수 카운터.
  - 로컬 재현(예시, 리눅스 7.0): 생산자 1, 소비자 4, 조건 변수 1개로 20만 개를 넘겼다. `if` 버전은 실행마다 1,920~3,224번 빈 큐에서 꺼냈다. `while` 버전은 0번이었다.
- **원인**
  - Mesa 의미론: 깨운 뒤 깨어난 스레드가 락을 다시 잡기 전에 다른 소비자가 먼저 가져갔다.
  - 또는 spurious wakeup이다. POSIX와 Java 모두 허용한다.
- **대처**: `while (술어 거짓) wait();`로 바꾼다. 테스트에서는 잘 안 나오므로 코드 리뷰 규칙으로 막는다.

### 2. lost wakeup → 영원히 대기

- **현상**: 드물게 요청 하나가 끝나지 않는다. CPU는 0%다.
- **보이는 형태**
  - Java 스레드 덤프에 `WAITING (on object monitor)`나 `WAITING (parking)`인 스레드가 있다. 그 조건을 바꿀 스레드는 이미 끝났다.
  - 교착이 아니므로 `jstack`의 "Found one Java-level deadlock"은 나오지 않는다.
- **원인**
  - 상태 변수 없이 신호만 주고받았다. 신호가 대기보다 먼저 오면 사라진다.
  - 또는 술어 확인과 wait 사이에 락이 없었다. 확인 직후·잠들기 직전에 온 신호가 사라진다.
- **대처**
  - 조건을 공유 변수로 기록하고, 확인·변경·signal을 모두 같은 락 안에서 한다.
  - 방어선으로 시간 제한 대기(`await(timeout)`, `pthread_cond_timedwait`)를 두고, 시간이 지나면 술어를 다시 확인하고 로그를 남긴다.

### 3. 잘못된 쪽을 깨움 → 모두 잠든 채 멈춤

- **현상**: 생산자와 소비자가 모두 멈췄다. 큐에는 원소가 있거나, 빈자리가 있다.
- **보이는 형태**: 스레드 덤프에서 생산자·소비자가 전부 같은 모니터(또는 같은 `Condition`)에서 `WAITING`이다.
- **원인**: 조건 변수(또는 wait set) 하나를 두 종류의 대기자가 같이 쓰면서 `signal`·`notify`로 하나만 깨웠다. 소비자가 소비자를 깨웠다(OSTEP 30.2).
- **대처**
  - 조건마다 `Condition`을 따로 둔다(`notFull`·`notEmpty`).
  - `synchronized`를 유지해야 하면 `notifyAll()`을 쓴다.

### 4. 락 없이 wait/notify → `IllegalMonitorStateException`

- **현상**: 배포 직후 해당 경로에서 바로 예외가 난다.
- **보이는 형태**: `java.lang.IllegalMonitorStateException` — 현재 스레드가 그 객체의 모니터를 쥐지 않았다(Java SE `Object` 문서). `Condition.await()`는 락을 쥐었다고 가정하며, 구현이 감지하면 `IllegalMonitorStateException` 같은 예외를 던질 수 있다(구현 의존, `Condition` 문서). 로컬 재현(JDK 21)에서는 둘 다 `IllegalMonitorStateException`이었다(`notify`는 메시지 "current thread is not owner").
- **원인**: `synchronized (lockA)` 안에서 `lockB.wait()`를 불렀거나, 락 블록 밖에서 불렀다.
- **대처**: wait·notify는 그 객체로 동기화한 블록 안에서만 부른다. C의 `pthread_cond_wait`에서는 락 없이 부르면 에러(ERRORCHECK·robust 뮤텍스)나 **정의되지 않은 동작**(그 밖의 뮤텍스)이다(POSIX). 예외가 없으니 더 위험하다.

### 5. 벽시계가 바뀌자 시간 제한 대기가 너무 길거나 짧다

- **현상**: NTP 보정이나 수동 시각 변경 직후 타임아웃이 예상과 다르게 동작한다.
- **보이는 형태**: 2초 타임아웃이 즉시 끝나거나 훨씬 늦게 끝난다.
- **원인**: `pthread_cond_timedwait`의 절대 시각을 기본 시계 `CLOCK_REALTIME`으로 쟀다(POSIX). 벽시계가 움직이면 기한도 같이 움직인다.
- **대처**: 조건 변수에 `CLOCK_MONOTONIC`을 지정하거나 `pthread_cond_clockwait(..., CLOCK_MONOTONIC, ...)`를 쓴다. 이 시나리오는 로컬에서 재현하지 않았다(시각 변경에 root 필요).

## 핵심 문장

- 조건 변수는 "락을 풀고 잠들기"를 원자적으로 해 주는 대기 큐다. 조건 자체는 기억하지 않는다. 대기자가 없을 때의 signal은 사라진다.
- 그래서 조건은 공유 변수(술어)에 적고, 확인·변경·signal을 같은 락 안에서 한다. 그렇지 않으면 lost wakeup으로 영원히 잔다.
- Mesa 의미론과 spurious wakeup 때문에 깨어났다고 조건이 참은 아니다. **항상 while로 기다린다.**
- 대기자의 종류가 다르면 조건 변수를 나눈다. 모를 때는 broadcast로 모두 깨우고 각자 다시 확인하게 한다.
- 모니터는 공유 상태·락·조건 대기를 언어가 묶은 것이다. Java 객체의 wait set은 하나뿐이라, 조건이 여럿이면 `Condition`을 쓴다.

## 관련 주제·근거

- 선행: [16-locks-and-spinlocks](../16-locks-and-spinlocks/2-summary.md) — 락과 futex의 원자적 "비교+잠들기"
- 후속·연결
  - [18-semaphores](../18-semaphores/2-summary.md) — 신호를 **저장하는** 카운터. 조건 변수와의 차이
  - [19-deadlock](../19-deadlock/2-summary.md), [20-concurrency-bugs](../20-concurrency-bugs/2-summary.md) — 순서 위반은 조건 변수로 고친다
  - [27-event-based-concurrency](../27-event-based-concurrency/2-summary.md) — 스레드 대신 이벤트 루프로 "기다리기"를 푸는 방식
  - [data-structure/04-queue-deque](../../data-structure/04-queue-deque/2-summary.md) — 원형 버퍼·큐
- 교재
  - OSTEP 30장 "Condition Variables" — 30.1 정의(그림 30.3~30.5 join), 30.2 생산자/소비자(Mesa vs Hoare, while, 조건 변수 두 개, 그림 30.10~30.14), 30.3 covering condition <https://pages.cs.wisc.edu/~remzi/OSTEP/threads-cv.pdf>
  - OSTEP 부록 D "Monitors (Deprecated)" <https://pages.cs.wisc.edu/~remzi/OSTEP/threads-monitors.pdf>
  - C.A.R. Hoare, "Monitors: An Operating System Structuring Concept", CACM 17(10), 1974 · B. Lampson, D. Redell, "Experience with Processes and Monitors in Mesa", CACM 1980 (OSTEP 참고문헌 경유, 원문 미열람)
- POSIX.1-2024
  - `pthread_cond_wait` — 원자적 해제, spurious wakeup "may occur", 기본 시계 `CLOCK_REALTIME`, 락 없이 호출 시 에러 또는 UB <https://pubs.opengroup.org/onlinepubs/9799919799/functions/pthread_cond_wait.html>
  - `pthread_cond_signal` — "적어도 하나", 대기자 없으면 효과 없음, RATIONALE "Multiple Awakenings" <https://pubs.opengroup.org/onlinepubs/9799919799/functions/pthread_cond_signal.html>
- Java
  - JLS §17.1 Synchronization, §17.2 Wait Sets and Notification <https://docs.oracle.com/javase/specs/jls/se21/html/jls-17.html>
  - Java SE 21 `Object.wait/notify`(spurious wakeup, `IllegalMonitorStateException`, 임의 선택), `Condition`(여러 wait set, spurious wakeup) <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/locks/Condition.html>
  - OpenJDK `java/util/concurrent/ArrayBlockingQueue.java` — `notEmpty`·`notFull`, while 대기, 원형 인덱스 <https://github.com/openjdk/jdk/blob/master/src/java.base/share/classes/java/util/concurrent/ArrayBlockingQueue.java>
- 로컬 재현(리눅스 7.0, glibc 2.39, JDK 21): 락 없는 `notify`·`await`의 예외, `Object.wait`·`Condition.await`의 jstack 상태, 상태 변수 없는 join의 lost wakeup(`pthread_cond_timedwait` → `ETIMEDOUT`), `if` vs `while` 빈 큐 꺼냄 횟수, 조건 변수 대기의 futex 호출(strace)
