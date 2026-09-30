# os/19-deadlock — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-30). 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 정답

### 1. 네 조건과 예방법 (OSTEP 32.3, Coffman 외 1971)

| 조건 | 뜻 | 깨는 법 |
|---|---|---|
| 상호 배제 | 자원을 한 번에 하나만 쓴다 | 락 없는 자료구조(CAS 재시도) |
| 점유 대기 | 쥔 채로 더 기다린다 | 필요한 락을 한꺼번에 잡는다(전역 락으로 감싸 획득) |
| 비선점 | 쥔 것을 빼앗을 수 없다 | `trylock` 실패 시 쥔 락을 모두 내려놓고 재시도 |
| 원형 대기 | 대기 사슬이 한 바퀴 돈다 | 락 획득 순서를 정한다(전순서·부분순서·주소 순서) |

- 하나라도 없으면 교착은 생기지 않는다. 실무의 기본은 원형 대기 깨기(락 순서)다.

### 2. 반대 순서 두 락

```text
  시간 ->
  스레드 1: lock(L1) 성공 ──────────── lock(L2) 대기...
  스레드 2:            lock(L2) 성공 ──────────── lock(L1) 대기...

  wait-for 그래프:  T1 ──(L2)──> T2 ──(L1)──> T1   사이클
```

- 두 스레드가 각자 첫 락을 잡고, 둘 다 두 번째 락을 잡기 전인 실행 순서에서만 멈춘다. 싱글 CPU에서는 스레드 1이 L1을 잡은 직후 스레드 2로 전환될 때, 멀티코어에서는 전환 없이 두 스레드가 동시에 실행될 때 그런 순서가 생긴다. 한 스레드가 두 락을 모두 잡고 나간 뒤 다른 스레드가 오면 멈추지 않는다.
- 그래서 **실행할 때마다 멈추지는 않는다**(OSTEP 32.3 "may occur"). 테스트에서는 잘 안 나고 부하에서 난다.

### 3. 은행원 알고리즘

- 현재: cash = 10 − (3 + 2 + 2) = 3, claim = need − loan = [5, 2, 4].

```text
  P1: claim 2 ≤ cash 3  → 끝났다고 치면 cash = 3 + 2 = 5
  P0: claim 5 ≤ 5       → cash = 5 + 3 = 8
  P2: claim 4 ≤ 8       → 끝
  안전 순서 P1, P0, P2가 있다 → 안전
```

- P0이 2개를 더 요청: 허락했다고 치면 loan = [5, 2, 2], cash = 1, claim = [3, 2, 4].
  - P1: 2 ≤ 1? 아니다. P0: 3 ≤ 1? 아니다. P2: 4 ≤ 1? 아니다.
  - 처음부터 끝낼 수 있는 프로세스가 없다 → **불안전** → 은행원은 요청을 **미룬다**.
- 지금 당장 교착은 아니다. "모두가 최대치를 요청하면 끝날 길이 없어지는 상태"로 가지 않게 막는 것이다(EWD 623).

### 4. 이체 교착 고치기

```java
void transfer(Account from, Account to, long amount) {
    Account first  = from.id() < to.id() ? from : to;   // 항상 id 작은 쪽 먼저
    Account second = from.id() < to.id() ? to   : from;
    synchronized (first) {
        synchronized (second) {
            from.withdraw(amount);
            to.deposit(amount);
        }
    }
}
```

- A→B든 B→A든 같은 순서로 잠그므로 사이클이 생길 수 없다. C라면 락 주소로 순서를 정한다(OSTEP 32.3 팁).
- 대안: `ReentrantLock.tryLock(timeout)`으로 두 번째 락을 시도하고, 실패하면 첫 번째를 풀고 재시도한다(비선점 조건 깨기).
- 함정
  - 두 스레드가 같은 박자로 "잡고-실패-놓고"를 반복하면 **라이브락**이다. 재시도 전에 무작위 지연을 둔다(OSTEP 32.3, 20번).
  - 첫 락을 잡은 뒤 한 일(메모리 할당 등)도 실패 시 되돌려야 한다.

### 5. 누가 탐지하고 누가 푸나

| 주체 | 탐지 | 해결 |
|---|---|---|
| pthread 기본 뮤텍스 | 안 한다. 같은 스레드의 재잠금은 POSIX상 DEFAULT 유형이면 정의되지 않은 동작, NORMAL 유형이면 "deadlock". glibc는 DEFAULT를 NORMAL로 둔다(`pthread.h`) | 없음 — glibc에서는 영원히 잔다 |
| JVM | `jstack`·`ThreadMXBean.findDeadlockedThreads()`로 monitor·ownable synchronizer 사이클을 찾는다 | 안 푼다. 사람이 재시작 |
| InnoDB | 기본 켜진 탐지기가 찾는다 | 작은 트랜잭션(바꾼 행 수 기준)을 롤백, `ERROR 1213` |
| PostgreSQL | `deadlock_timeout`(기본 1초) 동안 기다린 뒤 검사 | 검사를 시작한 쪽의 요청을 취소, `40P01` |

### 6. Java 교착 덤프 읽기

- 알 수 있는 것
  - 사이클에 든 스레드 이름(`worker-1`, `worker-2`).
  - 각자 **기다리는** 모니터와 그것을 **쥔** 스레드.
  - 아래 "Java stack information"에서 각 스레드가 어느 줄에서 무엇을 `locked`했고 무엇을 `waiting to lock`인지. 두 코드 경로의 락 순서가 반대라는 증거다.
- 긴급 조치: 재시작. JVM은 탐지만 하고 풀지 않는다. 재시작 전에 덤프를 남긴다.
- 근본 조치: 두 경로의 락 순서를 통일한다. 락을 쥔 채 다른 객체의 `synchronized` 메서드·콜백을 부르지 않는다.
- JVM이 못 찾는 것
  - 소유자가 없는 동기화 도구(`Semaphore`, `CountDownLatch`, 조건 대기)가 낀 사이클. 로컬 재현(JDK 21)에서 세마포어 교차 대기는 `null`이었다.
  - 가상 스레드가 낀 사이클(Java SE `ThreadMXBean` 문서).
  - 애플리케이션 락과 DB 락이 섞인 사이클.

### 7. MySQL 1213 vs 1205

| | 1213 `ER_LOCK_DEADLOCK` | 1205 `ER_LOCK_WAIT_TIMEOUT` |
|---|---|---|
| 메시지 | Deadlock found when trying to get lock; try restarting transaction | Lock wait timeout exceeded; try restarting transaction |
| SQLSTATE | 40001 | HY000 |
| 언제 | 탐지기가 사이클을 찾았을 때 | 행 락을 `innodb_lock_wait_timeout`(기본 50초) 넘게 기다렸을 때 |
| 롤백 | 희생자 트랜잭션 | 기본은 **현재 문장만**(`--innodb-rollback-on-timeout`이면 전체) |

- 1213 처리: 트랜잭션 전체를 처음부터 재시도한다(횟수 제한·백오프). 근본은 행 잠금 순서 통일.
- 1205 처리: 트랜잭션은 아직 열려 있다. 그대로 커밋하면 앞 문장만 반영된 반쪽 결과가 남을 수 있으니 **명시적으로 롤백**한 뒤 재시도한다. 탐지가 꺼졌거나(`innodb_deadlock_detect=OFF`) 탐지 밖의 락(`LOCK TABLES` 등)이 낀 교착도 1205로 드러난다.

### 8. PostgreSQL 교착의 시점과 희생자

- 시점: 한쪽이 락을 `deadlock_timeout`(기본 1초) 동안 기다린 뒤에야 검사가 돈다. 그래서 오류는 **약 1초 뒤**에 나온다.
- 희생자: 검사를 시작한 프로세스의 락 요청을 취소한다. 그 트랜잭션이 `ERROR: deadlock detected`를 받는다. 문서는 어느 쪽이 취소될지 예측하기 어렵고 그에 기대면 안 된다고 적는다(13.3.4).
- SQLSTATE: `40P01`(`deadlock_detected`).
- 단순 락 대기: 교착이 없으면 **무한정** 기다린다(13.3.4). 끝없이 기다리지 않으려면 `lock_timeout`(기본 0 = 꺼짐, 19.11)을 따로 건다.

### 9. lockdep·TSan의 "미리 보는" 탐지

- 둘 다 **실제 대기 그래프가 아니라 획득 순서의 이력**을 본다.
  - "L1을 쥔 채 L2를 잡았다"를 L1→L2 간선으로 기록한다.
  - 다른 곳에서 L2→L1이 한 번이라도 관측되면, 그 순간 둘이 겹치지 않았어도 사이클로 보고한다.
  - lockdep: "두 락이 역순으로 잡힐 수 없다", 위반 시 `WARNING: possible circular locking dependency detected`(docs.kernel.org lockdep-design, lockdep.c).
  - TSan: 로컬 재현(gcc 13.3)에서 두 스레드를 **차례로** 실행했는데도 `lock-order-inversion (potential deadlock)`, `Cycle in lock order graph: M0 => M1 => M0`.
- DB·JVM과의 차이: DB·JVM은 **지금 멈춘** 사이클을 찾는다(사후). lockdep·TSan은 멈출 **수 있는** 순서를 찾는다(사전). 대신 실행된 경로만 본다. 테스트가 지나가지 않은 경로의 역순은 모른다.

### 10. 멈춘 C++ 서비스 확정 순서

1. `ps -L -o pid,lwp,stat,pcpu,wchan:20 -p <pid>` — 작업 스레드가 모두 `S` + `futex_do_wait`이고 CPU 0%인지 본다. 로드 평균은 R·D만 세므로 S 상태 교착은 낮게 나온다(proc_loadavg(5)).
2. `gcore <pid>`로 코어를 남긴다(재시작 전 증거).
3. `gdb -p <pid>`(또는 코어) → `thread apply all bt` — 각 스레드가 어떤 뮤텍스(`futex_word=<L1>`)에서 `__lll_lock_wait`에 서 있는지 적는다.
4. 각 뮤텍스의 `__data.__owner`로 주인 TID를 찾는다.
5. "스레드 → 기다리는 락의 주인" 간선을 그려 사이클을 찾는다. 사이클이 있으면 교착 확정이다.
   - 로컬 재현(예시, 리눅스 7.0): `2006125 ─(L2)─> 2006126 ─(L1)─> 2006125`.
6. 사이클이 없고 모두 조건 대기·세마포어에 있다면 교착이 아니라 lost wakeup이나 permit 누수를 의심한다(17·18번).
- 재발 방지: 락 순서 규칙 + TSan을 CI에 넣는다.
