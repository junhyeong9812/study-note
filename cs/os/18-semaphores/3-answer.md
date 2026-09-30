# os/18-semaphores — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-30). 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 정답

### 1. 초깃값과 용도

| 초깃값 | 용도 | 예 |
|---|---|---|
| 1 | 이진 세마포어 = 락(상호 배제) | 공유 버퍼 인덱스 보호 |
| 0 | 순서 맞추기 | 자식이 끝나면 부모 진행, 초기화가 끝나면 워커 시작 |
| N | 개수 제한 | 외부 API 동시 N건, 커넥션 N개, 메모리를 많이 쓰는 구간의 스로틀링 |

- 초깃값이 "처음부터 통과시킬 수"다. 0이면 누군가 post하기 전까지 아무도 못 지나간다(OSTEP 31.2~31.3, 31.7).

### 2. 리눅스 세마포어의 상태 변화

| 동작 | 값 | 대기자 |
|---|---|---|
| 처음 | 2 | — |
| A `sem_wait` | 1 | — |
| B `sem_wait` | 0 | — |
| C `sem_wait` | 0 | C (막힘) |
| A `sem_post` | 0 | — (C가 깨어나 그 1을 가져감) |
| B `sem_post` | 1 | — |

- C가 막혀 있을 때 `sem_getvalue`는 **0**을 돌려준다. POSIX는 0 또는 "대기자 수의 음수"를 허용하고, 리눅스는 0을 택했다(sem_getvalue(3)). 리눅스 값은 0 밑으로 내려가지 않는다(sem_overview(7)).
- OSTEP의 Dijkstra식 정의에서는 wait가 먼저 값을 줄이므로 C가 막힌 시점의 값은 **−1**이다. 음수의 절댓값이 대기자 수다(OSTEP 31.1).

### 3. post가 wait보다 먼저 오면

- `sem_post`가 값을 0 → 1로 올려 **저장**한다. 나중에 부모의 `sem_wait`가 그 1을 쓰고 바로 통과한다. 신호를 잃지 않는다(OSTEP 31.3).
- 조건 변수로 하려면 **상태 변수(`done`)와 그것을 보호하는 락**이 따로 필요했다. 조건 변수는 대기자 없는 signal을 버리기 때문이다(17번).
- 세마포어는 그 상태를 값 자체로 가진다. 값의 변경과 대기가 세마포어 연산 안에서 원자적으로 처리된다.

### 4. 유한 버퍼와 잘못된 순서

- 초깃값: `empty = MAX`(빈 칸 수), `full = 0`(찬 칸 수), `mutex = 1`.
- 교착 순서(소비자만 틀린 경우. OSTEP 그림 31.11은 생산자도 `mutex`를 먼저 잡아 `empty` 전에 막히지만 사이클은 같다)

```text
  소비자: sem_wait(&mutex) 성공 (mutex 0)
  소비자: sem_wait(&full)  → 버퍼가 비어 0 → 잠듦   ← mutex를 쥔 채
  생산자: sem_wait(&empty) 성공
  생산자: sem_wait(&mutex) → 0 → 잠듦
  → 소비자는 생산자의 post(full)을, 생산자는 소비자의 post(mutex)를 기다린다: 사이클
```

- 고치기: 개수 세마포어(`empty`·`full`) 대기를 락 **밖**에서 먼저 하고, `mutex`는 `put`·`get`만 감싼다(OSTEP 그림 31.12). 락의 범위를 줄이는 것이 해법이다.

### 5. 이진 세마포어 vs 뮤텍스

| | 뮤텍스(`ReentrantLock` 등) | 세마포어 |
|---|---|---|
| 소유자 | 있다. 잡은 스레드만 푼다 | 없다. 아무 스레드나 post·release 가능(Java SE `Semaphore`) |
| 재진입 | `ReentrantLock`·`synchronized`는 된다 | 안 된다. 같은 스레드가 두 번 wait하면 permit 2개를 쓴다 |
| 상한 검사 | 해당 없음 | 없다. release를 더 하면 초깃값을 넘는다 |
| JVM 교착 탐지 | `findDeadlockedThreads`가 찾는다 | 못 찾는다(로컬 재현: 세마포어 교차 대기에서 `null`) |

- 소유자가 없다는 점이 장점일 때도 있다. Java 문서는 교착 복구처럼 다른 스레드가 풀어야 하는 특수한 경우에 쓸모 있다고 적는다.

### 6. 에러 몇 번 뒤 기능 전체가 멈춤

- 보이는 것
  - 지표: `availablePermits()`가 에러 횟수만큼 줄어 0에 머문다. 유휴 시간에도 초깃값으로 돌아오지 않는다.
  - 스레드 덤프: `java.lang.Thread.State: WAITING (parking)` + `parking to wait for <...> (a java.util.concurrent.Semaphore$NonfairSync)`인 스레드가 쌓인다. 교착 메시지는 없다.
- 원인: `acquire()` 뒤 예외 경로에서 `release()`를 건너뛰었다. permit이 영구히 사라졌다.
  - 로컬 재현(예시, JDK 21): `Semaphore(2)`에서 에러 두 번 뒤 permit 0, 다음 `tryAcquire(1, SECONDS)`는 `false`.
- 대처
  - `acquire(); try { … } finally { release(); }`로 반납을 한 곳에 모은다.
  - 무한 `acquire()` 대신 `tryAcquire(timeout)`을 쓰고 실패를 지표로 낸다.
  - permit 수를 지표로 내보내고 "유휴 시 초깃값 복귀"를 경보로 건다.
  - 긴급 복구는 재시작이다. 소유자가 없어 "누가 안 놓았는지"를 런타임에 찾을 수 없다.

### 7. release 두 번 더

- `availablePermits()`는 **4**다. Java `Semaphore`는 release하는 스레드가 acquire했는지도, 초깃값을 넘는지도 검사하지 않는다(Java SE `Semaphore`, 로컬 재현 JDK 21).
- 문제: 동시 2건 제한이 조용히 4건 제한이 된다. 하위 서비스가 예상보다 많은 동시 요청을 받아 과부하가 된다. 에러는 나지 않는다.
- POSIX `sem_post`도 값이 `SEM_VALUE_MAX`를 넘을 때만 `EOVERFLOW`로 막는다(sem_post(3)). 이 환경에서 `getconf SEM_VALUE_MAX`는 2147483647이었다.

### 8. 이름 있는 세마포어와 크래시

- 원인: 이름 있는 POSIX 세마포어는 **커널 지속성**을 가진다. `sem_unlink`하지 않으면 시스템이 꺼질 때까지 남는다(sem_overview(7)). 크래시한 프로세스가 잡고 있던 permit은 반납되지 않는다.
- 확인
  - `ls -l /dev/shm/sem.<name>` — 리눅스에서 이름 있는 세마포어는 이 파일로 보인다.
  - `sem_getvalue`나 `sem_trywait`로 값을 본다. 로컬 재현(예시, 리눅스 7.0)에서 크래시 뒤 값은 0이었고 `sem_trywait`는 `EAGAIN`이었다.
- 대처
  - 모든 사용 프로세스가 내려간 상태에서 시작 스크립트가 `sem_unlink` 후 다시 만든다.
  - 목적이 상호 배제라면 소유자 사망을 알려 주는 robust 뮤텍스(`EOWNERDEAD`)나, 프로세스가 죽으면 풀리는 `flock` 락을 검토한다(flock(2): 같은 open file description을 가리키는 fd가 모두 닫히면 해제 — fork로 물려받은 fd가 남아 있으면 풀리지 않는다).

### 9. 결제 API 동시 10건 제한 설계

```java
private final Semaphore permits = new Semaphore(10, true);   // 공정

PaymentResult pay(PaymentRequest r) throws Exception {
    if (!permits.tryAcquire(300, TimeUnit.MILLISECONDS)) {    // 300ms는 예시
        throw new BusyException();                            // 빠른 거절 → 상위에서 재시도·안내
    }
    try {
        return client.pay(r);
    } finally {
        permits.release();
    }
}
```

- 공정/비공정: 자원 접근 제한용이므로 **공정**을 고른다. Java 문서는 자원 접근 제어용 세마포어를 공정하게 만들어 기아를 막으라고 권한다. 단, 시간 제한 없는 `tryAcquire()`는 공정 설정을 무시하므로 쓰지 않는다.
- 무한 대기 회피: `tryAcquire(timeout)`. 대기 시간은 상위 요청 타임아웃보다 짧게 잡는다.
- 반납 위치: `acquire` 성공 직후의 `try`에 대응하는 `finally` 한 곳. `acquire`와 `try` 사이에 코드를 두지 않는다. 재시도 루프 안에서 반납이 두 번 되지 않게 한다.
- 대기열 길이: 세마포어는 기다리는 스레드 수를 제한하지 않는다. `tryAcquire(timeout)`이 대기 시간을 제한하고, 필요하면 `getQueueLength()`가 상한을 넘을 때 즉시 거절한다. 스레드 풀의 스레드가 모두 대기에 묶이지 않게 한다.
