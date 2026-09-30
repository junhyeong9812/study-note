# os/17-condition-variables-and-monitors — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-30). 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 정답

### 1. 락만으로 기다리기의 두 방법

- (1) 락을 쥔 채 잠든다: 큐를 채워 줄 생산자가 락을 잡지 못한다. 조건이 영원히 바뀌지 않는다.
- (2) 락을 풀었다 잡았다 하며 계속 확인한다: 조건이 바뀔 때까지 CPU를 태운다.
- `pthread_cond_wait(&c, &m)`이 원자적으로 하는 일: **뮤텍스 `m`을 풀고 `c`에서 잠드는 것**이다. 그 사이에 끼어든 signal이 사라지지 않도록, "다른 스레드가 `m`을 잡은 뒤 부른 signal은 이 스레드가 잠든 뒤에 부른 것처럼 동작해야 한다"(POSIX). 돌아올 때는 `m`을 다시 잡은 상태다.

### 2. join이 영원히 잠드는 두 순서

```text
  (a) 상태 변수 없음
  자식: lock; signal(c); unlock;     ← 대기자 없음 → 신호 사라짐
  부모: lock; wait(c, m);            ← 이미 지나간 신호를 기다림 → 영원히

  (b) 상태 변수는 있지만 락 없이 확인
  부모: if (done == 0)  → 0을 봄
  자식:                   done = 1; signal(c);   ← 아직 아무도 안 잠듦
  부모: wait(c)          → 영원히
```

- (a)의 해법: 사실을 공유 변수 `done`에 적는다. 부모는 `done`이 이미 1이면 기다리지 않는다.
- (b)의 해법: `done` 확인과 `wait`를 같은 락 안에서 한다. 자식도 그 락을 쥐고 `done = 1`과 signal을 한다. wait가 락을 원자적으로 풀며 잠들므로 틈이 없다(OSTEP 그림 30.3~30.5).
- 로컬 재현(예시, 리눅스 7.0): (a)를 2초 시간 제한 대기로 돌리면 `ETIMEDOUT`이었다.

### 3. 대기자 없는 signal

- **아무 효과가 없다.** POSIX: "cond에 막힌 스레드가 없으면 효과가 없어야 한다(shall have no effect)"(POSIX `pthread_cond_signal`).
- 세마포어의 `sem_post`는 값을 1 올린다. 나중에 오는 `sem_wait`가 그 값을 쓰고 바로 통과한다. 즉 **세마포어는 신호를 저장하고, 조건 변수는 저장하지 않는다.** 조건 변수를 쓸 때 상태 변수가 반드시 필요한 이유다.

### 4. if 대기로 빈 버퍼에서 꺼내기

```text
  Tc1: lock; count == 0 → wait (잠듦, 락 해제)
  P:   lock; put(); count = 1; signal → Tc1 깨움(준비 상태); unlock
  Tc2: lock (Tc1보다 먼저 잡음); count == 1 → get(); count = 0; unlock
  Tc1: 락 다시 잡고 wait에서 돌아옴 → if 는 이미 통과 → get() → 빈 버퍼!
```

- **Mesa 의미론**에서 생긴다. signal은 "상태가 바뀌었다"는 힌트일 뿐이고, 깨어난 스레드가 실행될 때까지 다른 스레드가 먼저 상태를 바꿀 수 있다.
- Hoare 의미론은 깨운 즉시 깨어난 스레드를 실행시키므로 이 틈이 없다. 하지만 만들기 어려워 거의 모든 시스템이 Mesa를 쓴다(OSTEP 30.2).
- 해법: `while (count == 0) wait;`. 로컬 재현(예시, 리눅스 7.0, 생산자 1·소비자 4·20만 개)에서 `if`는 1,920~3,224번 빈 큐에서 꺼냈고 `while`은 0번이었다.

### 5. spurious wakeup을 허용하는 이유

- 멀티프로세서에서 `pthread_cond_signal` 하나가 두 스레드를 깨우는 일을 막으려면 기본 연산 전체가 느려진다. POSIX RATIONALE은 드문 경우를 위해 모든 사용자가 효율을 잃는 것은 받아들일 수 없다고 적는다. 어차피 술어는 다시 확인해야 한다.
- 덤: 응용이 **술어 재확인 루프**를 반드시 쓰게 된다. 그러면 프로그램의 다른 곳에서 불필요한 signal·broadcast를 보내도 견딘다. 결과적으로 더 튼튼해진다(POSIX `pthread_cond_signal` RATIONALE "Multiple Awakenings by Condition Signal").

### 6. 조건 변수 하나 + signal → 모두 잠듦

```text
  Tc1, Tc2: 버퍼가 비어 cond에서 잠듦
  P:   put; signal(cond) → Tc1 깨움;  다시 put하려니 가득 참 → cond에서 잠듦
  Tc1: get; signal(cond) → 대기자는 Tc2(소비자)와 P(생산자). Tc2가 깨어남
  Tc2: 버퍼가 비었으니 while에 걸려 다시 잠듦
  Tc1: 다음 get 하려니 비었음 → 잠듦
  → P, Tc1, Tc2 모두 잠듦. 소비자가 생산자를 깨워야 했는데 소비자를 깨웠다.
```

- 해법 A: 조건 변수를 두 개로 나눈다. 생산자는 `empty`에서 기다리고 `fill`에 신호한다. 소비자는 반대다. 소비자가 소비자를 깨울 일이 구조적으로 없다(OSTEP 그림 30.12·30.14).
- 해법 B: `broadcast`로 모두 깨우고 각자 while로 다시 확인한다(covering condition, OSTEP 30.3). 코드는 단순하지만 필요 없는 스레드까지 깨워 비용이 든다.
- 대기자의 종류가 분명하면 A, 누가 진행할 수 있을지 미리 알 수 없으면(예: 크기가 다른 메모리 요청) B다.

### 7. Java 모니터

- 모니터 = **공유 상태를 보호하는 락 + 조건 대기(wait set)**를 객체 단위로 묶은 것이다. Java의 모든 객체는 모니터 하나와 wait set 하나를 가진다(JLS §17.1, §17.2). 모니터 락은 재진입된다.
- `synchronized` 밖에서 `wait()`·`notify()`를 부르면 `IllegalMonitorStateException`이다(Java SE `Object` 문서). 로컬 재현(JDK 21)에서 `notify`는 "current thread is not owner" 메시지와 함께 던졌다.
- 한계: 객체당 wait set이 하나뿐이다. 조건이 둘 이상이면 6번의 "잘못된 쪽을 깨움"이 생기고, `notifyAll()`로 덮어야 한다.
- `Condition`은 모니터 메서드를 별도 객체로 떼어 **락 하나에 wait set 여러 개**를 준다(Java SE `Condition` 문서).
- `ArrayBlockingQueue`: `ReentrantLock` 하나에 `notEmpty`·`notFull` 두 조건을 만든다. `put`은 `while (count == items.length) notFull.await();` 후 넣고 `notEmpty.signal()`, `take`는 `while (count == 0) notEmpty.await();` 후 꺼내고 `notFull.signal()`이다(OpenJDK 소스). 해법 A 그대로다.

### 8. 끝나지 않는 요청, CPU 0%, 교착 메시지 없음

- 의심: **lost wakeup**(또는 잘못된 쪽을 깨움). 교착이 아니라 "깨워 줄 사람이 없는 대기"다. `jstack`의 교착 탐지는 락 소유의 사이클만 찾으므로 이 경우는 잡지 못한다.
- 덤프에서 볼 줄
  - `java.lang.Thread.State: WAITING (on object monitor)` + `- waiting on <...>` — `Object.wait()`
  - `java.lang.Thread.State: WAITING (parking)` + `- parking to wait for <... AbstractQueuedSynchronizer$ConditionObject>` — `Condition.await()`
  - 그 조건을 바꿔 줄 스레드가 덤프에 없거나(이미 끝남) 전혀 다른 일을 하고 있다.
- 고치기
  - 기다리는 조건을 공유 변수로 적고, 확인·변경·signal을 같은 락 안에서 한다.
  - 대기는 while 루프로 한다.
  - 조건마다 `Condition`을 나누거나 `notifyAll()`을 쓴다.
  - 방어선으로 시간 제한 대기를 두고, 시간이 지나면 술어를 다시 보고 로그를 남긴다.

### 9. 시간 제한 대기의 절대 시각과 시계

- 절대 시각인 이유: while 루프에서 여러 번 깨어났다 다시 기다려도 **기한이 그대로** 유지된다. 상대 시간이면 깨어날 때마다 남은 시간을 다시 계산해야 한다.
- 기본 시계: 조건 변수 속성으로 정한 시계다. 설정하지 않으면 `CLOCK_REALTIME`이다(POSIX `pthread_cond_timedwait`).
- 문제: 벽시계가 움직이면(NTP 보정, 수동 변경) 기한도 같이 움직인다. 타임아웃이 너무 빨리 끝나거나 늦게 끝난다.
- 대처: `pthread_condattr_setclock(&attr, CLOCK_MONOTONIC)`으로 조건 변수를 만들거나, POSIX.1-2024의 `pthread_cond_clockwait(..., CLOCK_MONOTONIC, ...)`를 쓴다. (시계 변경 시나리오는 root가 필요해 로컬에서 재현하지 않았다.)
