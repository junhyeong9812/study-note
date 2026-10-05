# os/19-deadlock — 교착 상태: 네 조건, 그리고 예방·회피·탐지 — 정리 (힌트)

## 해결하는 문제

락(16번)과 세마포어(18번)는 "한 번에 하나"를 지킨다.\
그런데 스레드가 락을 **두 개 이상** 잡기 시작하면 새로운 멈춤이 생긴다.

```text
  스레드 1                       스레드 2
  lock(L1)  성공                  lock(L2)  성공
  lock(L2)  ... L2는 스레드 2가 쥠  lock(L1)  ... L1은 스레드 1이 쥠
            잠듦                            잠듦
  → 둘 다 상대가 풀기를 기다린다. 아무도 풀지 않는다. 영원히.
```

이것이 **교착 상태(deadlock)**다(OSTEP 그림 32.6).\
이 코드가 **항상** 멈추지는 않는다. 두 스레드가 각자 첫 락을 잡고, 둘 다 두 번째 락을 잡기 전일 때만 멈춘다. 싱글 CPU에서는 스레드 1이 L1을 잡은 직후의 전환으로, 멀티코어에서는 전환 없이 동시 실행으로 이런 순서가 생긴다. 그래서 테스트에서는 안 나고 부하에서만 난다.

쉬운 예: 좁은 골목에서 마주 본 두 차다.
- 둘 다 이미 골목에 들어왔다(자원을 쥠).
- 둘 다 상대가 비키기를 기다린다(더 필요한 자원을 기다림).
- 아무도 상대 차를 치울 수 없다(빼앗을 수 없음).
- 서로가 서로의 길을 막는다(원형 대기).

똑같은 구조다.\
네 가지가 동시에 성립해야 교착이다. 그러니 **하나만 깨면 된다.**

실무 예:
- Java 스레드 덤프에 `Found one Java-level deadlock:`이 찍힌다.
- MySQL `ERROR 1213 (40001): Deadlock found when trying to get lock; try restarting transaction`.
- PostgreSQL `ERROR: deadlock detected` (SQLSTATE `40P01`).
- 계좌 이체 A→B와 B→A가 동시에 들어오면, 두 행을 반대 순서로 잠가 교착이 난다.

## 동작·원리

### 1. 네 조건 (Coffman 외 1971, OSTEP 32.3)

```text
  조건                 뜻                                        깨는 방법(예방)
  상호 배제            자원을 한 번에 하나만 쓴다                     락 없는 자료구조 (CAS)
  점유 대기            쥔 채로 더 기다린다                           필요한 락을 한꺼번에 잡는다
  비선점               쥔 것을 강제로 빼앗을 수 없다                   trylock 실패 시 쥔 것을 내려놓고 재시도
  원형 대기            대기의 사슬이 한 바퀴 돈다                     락 획득 순서를 정한다 (전순서·부분순서)
```

- 넷 중 하나라도 성립하지 않으면 교착은 생기지 않는다(OSTEP 32.3).
- 실무에서 가장 많이 쓰는 것은 **원형 대기 깨기**, 즉 락 순서다.

### 2. wait-for 그래프 — 교착 = 사이클

```text
  노드 = 스레드(트랜잭션), 간선 A → B = "A가 B가 쥔 락을 기다린다"

      T1 ──기다림──> T2           T1 ─> T2 ─> T3
      ^               |            ^           |
      └───기다림───────┘            └───────────┘
      사이클 = 교착               세 스레드짜리 사이클도 교착
```

- 락처럼 자원이 하나씩뿐이면 "wait-for 그래프에 사이클이 있다"와 "교착이다"가 같은 말이다. PostgreSQL 락 관리자 README도 자기 락에 대해 "교착은 WFG에 사이클이 있을 때, 그리고 그때만"이라고 적는다.
- 로컬 재현(예시, 리눅스 7.0, glibc 2.39): 위 C 코드를 gdb로 보면 두 스레드가 각각 상대 락의 `futex_wait(expected=2)`에 서 있다. 뮤텍스의 `__data.__owner` 필드가 주인 TID다.

```text
  (gdb) thread apply all bt
  Thread 3 (LWP 2006126): futex_wait (... futex_word=<L1>) ... in t2 () at dl.c:6
  Thread 2 (LWP 2006125): futex_wait (... futex_word=<L2>) ... in t1 () at dl.c:5
  (gdb) p L1.__data.__owner   → 2006125      (L1 주인 = Thread 2)
  (gdb) p L2.__data.__owner   → 2006126      (L2 주인 = Thread 3)

  wait-for:  2006125 ─(L2)─> 2006126 ─(L1)─> 2006125   사이클
```

### 3. 네 가지 대응 전략

```text
  전략        언제 무엇을 하나                                     누가 쓰나
  예방        코드 설계 단계에서 네 조건 중 하나를 없앤다              애플리케이션 락 설계 (락 순서)
  회피        요청마다 "허락해도 안전한가"를 계산해 위험하면 미룬다     은행원 알고리즘, 정적 스케줄링 (제한된 환경)
  탐지·복구    일단 기다리게 두고, 주기적으로 사이클을 찾아 하나를 죽인다  DB (InnoDB, PostgreSQL)
  무시        드물면 재시작한다                                     "1년에 한 번 멈추면 재부팅" (OSTEP 32.3)
```

- 회피는 모든 작업이 어떤 락을 쓸지 **미리 알아야** 한다. 그래서 작업을 다 아는 임베디드 같은 제한된 환경에서만 쓸모 있고, 동시성도 줄인다(OSTEP 32.3).
- 운영체제의 일반 락은 교착 탐지를 약속하지 않는다. POSIX는 `pthread_mutex_lock`이 `EDEADLK`로 실패하는 것을 "할 수 있다(may)"로만 둔다. glibc 기본 뮤텍스는 **탐지하지 않고** 교착 상태로 그냥 영원히 잔다.

### 4. 은행원 알고리즘 — 안전한 상태만 허락한다

Dijkstra의 설명(EWD 623)을 자원 한 종류로 줄인 것이다.

```text
  cap  = 전체 자원 수        loan[p] = p가 지금 빌린 수      need[p] = p가 최대로 필요한 수
  cash = cap − Σ loan        claim[p] = need[p] − loan[p]  (앞으로 더 빌릴 수 있는 최대)

  "안전" = 모든 프로세스를 어떤 순서로 줄 세웠을 때,
          각 프로세스의 claim ≤ cash + (앞 순서 프로세스들이 끝나며 돌려줄 loan 합)  이 성립한다

  은행원: 요청을 받으면 "허락했다고 치고" 안전한지 본다. 안전하면 허락, 아니면 미룬다.
```

```text
  예 1 (EWD 623의 위험 예): cap = 4, need = [3, 3], loan = [2, 2], cash = 0
        claim = [1, 1]. 누구의 claim도 cash(0)보다 크다 → 안전한 순서 없음 → 둘 다 한 개씩 더 요청하면 교착

  예 2 (예시): cap = 10, need = [8, 4, 6], loan = [3, 2, 2], cash = 3
        claim = [5, 2, 4]
        P1: 2 ≤ 3 → P1이 끝났다고 치면 cash = 3 + 2 = 5
        P0: 5 ≤ 5 → cash = 5 + 3 = 8
        P2: 4 ≤ 8 → 끝
        순서 P1, P0, P2가 있으므로 안전
```

- 핵심은 "지금 당장 교착인가"가 아니라 "**앞으로 교착을 피할 길이 남아 있는가**"를 본다는 점이다.
- Dijkstra 본인은 이것을 "교착 방지(deadlock prevention)"의 예로 들었다. OSTEP는 스케줄링에 의한 **회피(avoidance)**로 분류한다. 용어가 책마다 다르니 "요청마다 안전성을 계산한다"는 동작으로 기억한다.

### 5. 락 순서 — 가장 실용적인 예방

```c
/* 두 락을 받는 함수: 인자 순서와 무관하게 주소 순서로 잡는다 (OSTEP 32.3 팁) */
void lock_both(pthread_mutex_t *a, pthread_mutex_t *b) {
    if (a > b) { pthread_mutex_t *t = a; a = b; b = t; }   /* 주소 오름차순 */
    pthread_mutex_lock(a);
    pthread_mutex_lock(b);                                 /* a != b 가정 */
}
```

- **전순서**: 모든 락에 순서를 매기고 항상 그 순서로 잡는다. 사이클이 생길 수 없다.
- **부분순서**: 락이 많으면 그룹 단위로 순서를 정한다. OSTEP는 리눅스 메모리 매핑 코드의 머리 주석을 예로 든다(32.3). 현재 소스에서는 `mm/filemap.c`의 "Lock ordering:" 주석(`i_mmap_rwsem` → `private_lock` → `swap_lock` …)과 `mm/rmap.c`의 "Lock ordering in mm:" 주석이 그 역할을 한다.
- 순서는 **관례**일 뿐이다. 누군가 어기면 끝이다. 그래서 도구로 검사한다.
  - 리눅스 커널 **lockdep**: 락 클래스 사이의 획득 순서를 기록한다. 한 번이라도 L1→L2와 L2→L1이 모두 관측되면, 실제로 멈추지 않았어도 경고한다(docs.kernel.org lockdep-design). 메시지는 `WARNING: possible circular locking dependency detected`(kernel/locking/lockdep.c).
  - 유저 공간 **ThreadSanitizer**: 로컬 재현(예시, gcc 13.3)에서 두 스레드가 L1→L2, L2→L1을 **차례로**(겹치지 않게) 실행해 실제 교착이 없었는데도 `WARNING: ThreadSanitizer: lock-order-inversion (potential deadlock)`, `Cycle in lock order graph: M0 => M1 => M0`을 보고했다.

### 6. 탐지·복구 — 데이터베이스의 방식

```text
  InnoDB (MySQL)                                  PostgreSQL
  탐지기 기본 켜짐 (지연 설정은 문서에 없음)              deadlock_timeout(기본 1초)만큼 기다린 뒤 탐지
  작은 트랜잭션(바꾼 행 수 기준)을 골라 롤백              탐지를 시작한 쪽의 요청을 취소 → 그 트랜잭션 오류
  ERROR 1213, SQLSTATE 40001                       ERROR: deadlock detected, SQLSTATE 40P01
  wait-for 목록이 200개를 넘으면 교착으로 간주           "누가 취소될지 예측하기 어렵고 기대면 안 된다"
```

- InnoDB는 동시성이 아주 높으면 탐지 자체가 느려질 수 있다. 이때 `innodb_deadlock_detect`를 끄고 `innodb_lock_wait_timeout`(기본 50초)에 맡길 수 있다(MySQL 8.4 17.7.5.2).
- InnoDB는 `innodb_table_locks = 1`(기본)이고 `autocommit = 0`일 때만 테이블 락을 안다. 그렇지 않으면 `LOCK TABLES`가 건 테이블 락이나 다른 스토리지 엔진의 락이 낀 교착은 탐지하지 못한다. 이때는 lock wait timeout으로 풀린다(같은 절).
- PostgreSQL 탐지는 비싸서 매번 하지 않는다. 락을 `deadlock_timeout` 동안 기다린 뒤에야 검사한다(PostgreSQL 19.12). 그래서 교착 오류는 최소 그만큼 늦게 나온다.
- PostgreSQL은 wait-for 간선을 따라 재귀적으로 나가 **출발점으로 돌아오는지** 본다(`deadlock.c` `FindLockCycleRecurse`, 락 관리자 README).

## 쓰이는 자료구조·알고리즘

- **wait-for 그래프 + DFS 사이클 탐지** — 간선을 따라 깊이 우선으로 내려가다 "지금 경로 위의 노드"를 다시 만나면 사이클이다. InnoDB·PostgreSQL·JVM(`findDeadlockedThreads`)이 쓰는 방식이다. [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md)(CycleDetector), [data-structure/08-graph](../../data-structure/08-graph/2-summary.md)
- **락 전순서** — 락에 번호(주소, id)를 매기고 정렬된 순서로 잡는다. 여러 개를 잡을 때는 먼저 **정렬**한다(예: `ORDER BY id FOR UPDATE`).
- **락 순서 그래프** — lockdep·TSan은 "L1을 쥔 채 L2를 잡았다"를 간선으로 기록하고, 그 그래프의 사이클을 찾는다. 실제 대기가 아닌 **순서 이력**의 사이클이라 멈추기 전에 잡는다.
- **은행원 알고리즘** — 안전 순서를 찾는 탐욕 탐색이다. "지금 가진 cash로 끝낼 수 있는 프로세스"를 하나씩 골라 끝났다고 치고 cash를 늘린다(EWD 623).
- **강한 연결 요소** — 여러 사이클이 얽힌 큰 교착 덩어리를 한 번에 찾을 때 쓴다. [algorithm/18-scc](../../algorithm/18-scc/2-summary.md)

## 적용 — 풀어나가는 법

### 1. Java — 순서를 정해서 잡는다

```java
// 계좌 이체: from/to 순서가 요청마다 반대여도 id 순서로 잠근다
void transfer(Account from, Account to, long amount) {
    Account first  = from.id() < to.id() ? from : to;
    Account second = from.id() < to.id() ? to   : from;
    synchronized (first) {
        synchronized (second) {
            from.withdraw(amount);
            to.deposit(amount);
        }
    }
}
```

- 순서를 정할 수 없으면 `tryLock(timeout)`으로 비선점 조건을 깬다. 실패하면 쥔 락을 모두 풀고 **무작위 지연** 뒤 재시도한다. 지연이 없으면 라이브락이 된다(20번).

### 2. DB — 같은 순서로 잠그고, 재시도를 준비한다

```sql
-- 여러 행을 갱신할 때: 항상 같은 순서로 잠근다
SELECT id FROM account WHERE id IN (11111, 22222) ORDER BY id FOR UPDATE;
UPDATE account SET balance = balance - 100 WHERE id = 11111;
UPDATE account SET balance = balance + 100 WHERE id = 22222;
```

- PostgreSQL 문서: 모든 애플리케이션이 여러 객체의 락을 **같은 순서**로 잡는 것이 최선의 방어다. 한 객체에는 처음부터 필요한 가장 강한 모드로 잡는다(13.3.4).
- MySQL 문서: 애플리케이션이 옳아도 교착은 날 수 있으니 **트랜잭션을 다시 실행할 준비**를 하라고 적는다(17.7.5).
- Spring JDBC는 MySQL 1213, PostgreSQL 40P01을 `DeadlockLoserDataAccessException`으로 바꾼다(`sql-error-codes.xml`의 `deadlockLoserCodes`). 이 클래스는 6.0.3부터 deprecated이고, 부모인 `PessimisticLockingFailureException`으로 잡으라고 한다. 재시도는 **트랜잭션 전체**를 다시 한다.

### 3. 진단 명령

```bash
# Java: 교착 자동 탐지 (monitor · ReentrantLock 등 ownable synchronizer)
jstack <pid> | sed -n '/Found one Java-level deadlock/,/Found [0-9]* deadlock/p'
jcmd <pid> Thread.print          # 같은 출력

# C/C++: 탐지 도구가 없다 → 스택과 락 주인을 직접 본다
ps -L -o pid,lwp,stat,wchan:20,comm -p <pid>     # 전부 S + futex_do_wait, CPU 0%
gdb -p <pid> -batch -ex 'thread apply all bt'    # ptrace_scope=1이면 권한 필요
# 개발 중: 락 순서 위반을 미리 잡는다
gcc -fsanitize=thread -g ...                     # 이 환경은 setarch -R 로 실행해야 했다

# MySQL
SHOW ENGINE INNODB STATUS\G                      # LATEST DETECTED DEADLOCK 절
SET GLOBAL innodb_print_all_deadlocks = ON;      # 모든 교착을 에러 로그에

# PostgreSQL
SELECT * FROM pg_locks WHERE NOT granted;
SELECT pid, pg_blocking_pids(pid), query FROM pg_stat_activity WHERE wait_event_type = 'Lock';
```

- `pg_blocking_pids(pid)`는 그 프로세스의 락 획득을 막는 세션들의 PID 배열을 돌려준다(PostgreSQL 9.27 시스템 정보 함수).

## 장애 시나리오와 대처

### 1. Java 스레드 교착 → 요청이 멈추고 스레드 풀이 마른다

- **현상**: 특정 기능의 요청이 응답 없이 쌓인다. CPU는 낮다. 결국 스레드 풀이 고갈되어 다른 요청까지 멈춘다.
- **보이는 형태** (로컬 재현, JDK 21)

```text
  Found one Java-level deadlock:
  =============================
  "worker-1":
    waiting to lock monitor 0x... (object 0x...f70, a java.lang.Object),
    which is held by "worker-2"
  "worker-2":
    waiting to lock monitor 0x... (object 0x...f60, a java.lang.Object),
    which is held by "worker-1"
  ...
  Found 1 deadlock.
```

  - 같은 실행에서 `ThreadMXBean.findDeadlockedThreads()`는 스레드 2개를 돌려줬다.
- **원인**: 두 경로가 같은 두 락을 반대 순서로 잡았다. 흔히 `synchronized` 메서드가 다른 객체의 `synchronized` 메서드를 부르며 숨어 있다. OSTEP는 `v1.addAll(v2)`와 `v2.addAll(v1)`의 동시 호출 예를 든다(32.3).
- **대처**
  - 긴급: 재시작. JVM은 교착을 **탐지만** 하고 풀지 않는다.
  - 근본: 락 순서를 정한다. 락을 쥔 채 외부 코드(콜백·다른 객체 메서드)를 부르지 않는다.
  - 탐지 자동화: 헬스 체크에서 `findDeadlockedThreads()`가 `null`이 아니면 경보한다. 가상 스레드가 낀 사이클은 이 메서드가 찾지 못한다(Java SE `ThreadMXBean` 문서).

### 2. MySQL `ERROR 1213` → 트랜잭션 하나가 롤백된다

- **현상**: 동시 이체·재고 차감 중 일부 요청이 실패한다.
- **보이는 형태**
  - `ERROR 1213 (40001): Deadlock found when trying to get lock; try restarting transaction`.
  - Spring이면 `DeadlockLoserDataAccessException`(`PessimisticLockingFailureException`의 하위).
  - `SHOW ENGINE INNODB STATUS`의 `LATEST DETECTED DEADLOCK`에 두 트랜잭션의 쿼리와 잠근 레코드가 나온다.
- **원인**: 두 트랜잭션이 같은 행들을 반대 순서로 잠갔다. 인덱스 범위 잠금 때문에 쿼리만 봐서는 순서가 안 보일 때도 있다.
- **대처**
  - 행을 잠그는 순서를 통일한다(`ORDER BY id FOR UPDATE`).
  - 트랜잭션을 짧게 한다.
  - 1213은 **재시도**한다. InnoDB가 희생자 트랜잭션을 롤백했으므로 처음부터 다시 한다.
  - 1205(lock wait timeout)와 구분한다. 1205는 기본 설정에서 **현재 문장만** 롤백한다(`innodb_rollback_on_timeout`이 꺼져 있을 때). 트랜잭션을 이어 가면 반쯤 된 상태가 커밋될 수 있다.

### 3. PostgreSQL `40P01` → 교착 오류가 1초 뒤에야 나온다

- **현상**: 교착이 날 때마다 요청이 약 1초 멈췄다가 한쪽이 실패한다.
- **보이는 형태**: `ERROR: deadlock detected`, `DETAIL: Process <pid> waits for <lock> on <object>; blocked by process <pid>.` 형태(src/backend/storage/lmgr/deadlock.c). 서버 로그에 관련 쿼리가 남는다.
- **원인**
  - 교착 자체는 순서 문제다(시나리오 2와 같다).
  - 1초는 `deadlock_timeout` 기본값이다. 탐지가 비싸서 그만큼 기다린 뒤에 검사한다(PostgreSQL 19.12).
- **대처**
  - 락 순서를 통일하고 재시도한다.
  - `deadlock_timeout`은 보통 트랜잭션 시간보다 길게 두라고 문서가 권한다. 줄이면 탐지가 빨라지지만 검사 비용이 는다.
  - 교착이 없으면 락 대기는 **무한**이다. 사용자 입력을 기다리며 트랜잭션을 열어 두지 않는다(13.3.4).

### 4. C·C++ 서비스가 통째로 멈춤 → 아무 로그도 없다

- **현상**: 프로세스는 살아 있는데 응답이 없다. CPU 0%, 로그 없음.
- **보이는 형태**
  - `ps -L`에서 모든 작업 스레드가 `S` + `futex_do_wait`(로컬 재현, 리눅스 7.0). 로드 평균에도 잡히지 않는다. 로드 평균은 R·D 상태만 세는데(proc_loadavg(5)) 이 스레드들은 S다.
  - `gdb`의 `thread apply all bt`에서 스레드들이 `__lll_lock_wait` → `futex_wait`에 서 있다.
- **원인**: pthread 기본 뮤텍스는 교착을 탐지하지 않는다. 같은 스레드가 NORMAL 뮤텍스를 다시 잠그는 경우도 POSIX 표는 "deadlock"으로 정한다(POSIX `pthread_mutex_lock`의 Relock 열, glibc `pthread_mutex_lock.c` 주석도 같은 내용). DEFAULT 유형의 재잠금은 POSIX상 정의되지 않은 동작이지만, glibc는 DEFAULT를 NORMAL로 둔다(`pthread.h`).
- **대처**
  - 긴급: 코어 덤프(`gcore <pid>`)를 뜨고 재시작한다.
  - 분석: 스택마다 "기다리는 락"과 `__owner`를 적어 wait-for 그래프를 그린다.
  - 예방: 개발 단계에서 TSan으로 lock-order-inversion을 잡는다. 디버그 빌드에 `PTHREAD_MUTEX_ERRORCHECK`를 쓰면 같은 스레드의 재잠금이 `EDEADLK` 오류로 드러난다(POSIX `pthread_mutex_lock`). 두 스레드 사이의 교착은 이것으로 잡히지 않는다.

### 5. 탐지기가 못 보는 교착 → 영원히 기다린다

- **현상**: 교착처럼 멈췄는데 JVM도 DB도 아무 말이 없다.
- **보이는 형태**: 스레드 덤프에 `Semaphore`·`CountDownLatch`·조건 대기에서 `WAITING (parking)`인 스레드들이 서로를 기다린다. 또는 애플리케이션 락을 쥔 스레드가 DB 락을 기다리고, 그 DB 락을 쥔 트랜잭션의 스레드가 애플리케이션 락을 기다린다.
- **원인**
  - JVM 탐지는 monitor와 ownable synchronizer의 사이클만 본다. 소유자가 없는 세마포어·래치는 보지 못한다(18번 로컬 재현: `null`).
  - DB 탐지는 DB 안의 락만 본다. 애플리케이션 락과 DB 락이 섞인 사이클은 어느 쪽도 전체 그래프를 갖고 있지 않다.
- **대처**
  - 모든 대기에 시간 제한을 둔다(`tryAcquire(timeout)`, `lock_timeout`, `innodb_lock_wait_timeout`).
  - 애플리케이션 락을 쥔 채 DB 호출을 하지 않는다. 또는 둘을 하나의 순서 규칙에 넣는다.

## 핵심 문장

- 교착은 상호 배제·점유 대기·비선점·원형 대기가 **동시에** 성립할 때만 생긴다. 하나만 깨면 된다.
- 단일 인스턴스 락에서 교착 = wait-for 그래프의 사이클이다. 탐지는 DFS로 사이클을 찾는 일이다.
- 가장 실용적인 예방은 락 순서(전순서·주소 순서)다. 순서는 관례라서 lockdep·TSan 같은 도구로 순서 그래프의 사이클을 미리 잡는다.
- 은행원 알고리즘은 "허락해도 모두가 끝날 순서가 남는가"를 매 요청마다 계산한다. 필요한 자원을 미리 알아야 해서 쓰임이 좁다.
- DB는 탐지·복구를 한다. 희생자를 롤백하므로(MySQL 1213, PostgreSQL 40P01) 애플리케이션은 트랜잭션 재시도를 준비해야 한다.
- glibc 기본 pthread 뮤텍스는 탐지하지 않고, JVM은 탐지만 하고 풀지 않는다. 탐지기가 못 보는 대기에는 시간 제한이 마지막 방어선이다.

## 관련 주제·근거

- 선행: [16-locks-and-spinlocks](../16-locks-and-spinlocks/2-summary.md) — 락과 futex 대기
- 연결
  - [18-semaphores](../18-semaphores/2-summary.md) — 락 안에서 개수 세마포어를 기다리는 교착, 식사하는 철학자
  - [17-condition-variables-and-monitors](../17-condition-variables-and-monitors/2-summary.md) — 교착이 아닌 "깨워 줄 사람 없는 대기"(lost wakeup)
  - [20-concurrency-bugs](../20-concurrency-bugs/2-summary.md) — 라이브락·기아·우선순위 역전
  - [database/15-two-phase-locking-and-deadlock](../../database/15-two-phase-locking-and-deadlock/2-summary.md) — DB 락 모드와 교착 탐지.
  - [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md) · [algorithm/18-scc](../../algorithm/18-scc/2-summary.md) · [data-structure/08-graph](../../data-structure/08-graph/2-summary.md)
  - [api-design/03-stock-deduct](../../api-design/24-case-stock-deduct/2-summary.md) — 재고 차감의 행 잠금
- 교재·논문
  - OSTEP 32장 "Common Concurrency Problems" — 32.3 Deadlock Bugs(그림 32.6·32.7, 네 조건 [C+71], 예방 4종, 주소 순서 팁, 스케줄링 회피, Banker's, 탐지·복구) <https://pages.cs.wisc.edu/~remzi/OSTEP/threads-bugs.pdf>
  - E. W. Dijkstra, EWD 623 "The mathematics behind the Banker's Algorithm" (cap·loan·need·claim·cash, 안전 순서) <https://www.cs.utexas.edu/~EWD/transcriptions/EWD06xx/EWD623.html>
  - E. G. Coffman, M. Elphick, A. Shoshani, "System Deadlocks", ACM Computing Surveys, 1971 (OSTEP [C+71] 경유, 원문 미열람)
- Linux
  - docs.kernel.org locking/lockdep-design — 락 클래스 순서 추적, lock inversion 탐지 <https://docs.kernel.org/locking/lockdep-design.html>
  - kernel/locking/lockdep.c — "possible circular locking dependency detected"
  - glibc `nptl/pthread_mutex_lock.c` 주석 — 기본 뮤텍스의 재잠금은 교착 · 커널 `mm/filemap.c`·`mm/rmap.c` 락 순서 주석
  - POSIX.1-2024 `pthread_mutex_lock` — 유형별 Relock 동작(NORMAL = deadlock, ERRORCHECK = `EDEADLK`, DEFAULT = 정의되지 않은 동작) <https://pubs.opengroup.org/onlinepubs/9799919799/functions/pthread_mutex_lock.html>
- DB
  - MySQL 8.4 Reference Manual 17.7.5 Deadlocks in InnoDB, 17.7.5.2 Deadlock Detection(작은 트랜잭션 롤백, 200 한도, `innodb_deadlock_detect`), `innodb_lock_wait_timeout`(50초, 1205는 문장만 롤백) <https://dev.mysql.com/doc/refman/8.4/en/innodb-deadlock-detection.html>
  - MySQL Server Error Reference — `ER_LOCK_DEADLOCK` 1213 / SQLSTATE 40001, `ER_LOCK_WAIT_TIMEOUT` 1205 <https://dev.mysql.com/doc/mysql-errors/8.0/en/server-error-reference.html>
  - PostgreSQL 13.3.4 Deadlocks <https://www.postgresql.org/docs/current/explicit-locking.html> · 19.12 Lock Management(`deadlock_timeout` 1s) <https://www.postgresql.org/docs/current/runtime-config-locks.html> · 부록 A `40P01 deadlock_detected` · 9.27 `pg_blocking_pids` · 19.11 `lock_timeout`(기본 0 = 끔) <https://www.postgresql.org/docs/current/runtime-config-client.html>
  - PostgreSQL `src/backend/storage/lmgr/README`(WFG), `deadlock.c`(`FindLockCycleRecurse`, "deadlock detected") <https://github.com/postgres/postgres/blob/master/src/backend/storage/lmgr/deadlock.c>
- Java·Spring
  - Java SE 21 `ThreadMXBean.findDeadlockedThreads` <https://docs.oracle.com/en/java/javase/21/docs/api/java.management/java/lang/management/ThreadMXBean.html>
  - OpenJDK `src/hotspot/share/services/threadService.cpp` — "Found one Java-level deadlock:"
  - Spring Framework `sql-error-codes.xml`(`deadlockLoserCodes` MySQL 1213, PostgreSQL 40P01), `DeadlockLoserDataAccessException`(6.0.3 deprecated) <https://github.com/spring-projects/spring-framework/blob/main/spring-jdbc/src/main/resources/org/springframework/jdbc/support/sql-error-codes.xml>
- 로컬 재현(리눅스 7.0, glibc 2.39, gcc 13.3, JDK 21): C 두 락 교착의 `ps -L`·gdb 스택·`__owner`, Java `synchronized` 교착의 jstack 출력과 `findDeadlockedThreads`, TSan lock-order-inversion 보고(실제 교착 없이)
