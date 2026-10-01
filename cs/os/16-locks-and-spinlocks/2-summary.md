# os/16-locks-and-spinlocks — 락은 어떻게 만들어지나: 원자 명령, 스핀, 그리고 futex로 잠들기 — 정리 (힌트)

## 해결하는 문제

15번에서 본 것처럼 `count++`는 읽기·더하기·쓰기 세 단계라 두 스레드가 끼어들면 값이 사라진다.\
해법은 "임계 구역에는 한 번에 한 스레드만"이다. 그 문지기가 **락**이다.
기초(경쟁 조건·`Lock` 사용법)는 원고 [process-thread §10~11](../../foundations/process-thread/README.md)에 있다. 이 노트는 그 `lock()`의 **안쪽**을 본다.

```text
  락이 답해야 할 세 가지 (OSTEP 28.4)
  1. 상호 배제   한 번에 한 스레드만 들어가는가
  2. 공정성      기다리는 스레드가 언젠가는 들어가는가 (기아가 없는가)
  3. 성능        경합이 없을 때 · 한 CPU에서 경합할 때 · 여러 CPU에서 경합할 때 비용은
```

쉬운 예: 화장실 열쇠가 하나다.
- 열쇠를 집는 동작이 "빈 걸 확인하고, 집는다" 두 단계면, 두 사람이 동시에 "비었네"를 보고 둘 다 들어간다.
- 그래서 "확인과 집기"가 **한 동작**이어야 한다. 이것이 하드웨어의 원자 명령이다.
- 열쇠가 없을 때 문 앞에서 계속 손잡이를 돌리면(스핀) 힘만 든다. 의자에 앉아 이름을 불러 줄 때까지 자면(sleep) 힘은 안 들지만 깨우는 데 시간이 걸린다.

똑같은 구조다.\
락 = **원자 명령**(확인+집기) + **기다리는 방법**(돌기 또는 자기)이다.

실무 예:
- 락을 잘못 고르면 CPU 사용률은 100%인데 처리량은 늘지 않는다(스핀락 과점유).
- 24코어 머신에서 스레드를 4개에서 24개로 늘렸더니 오히려 느려진다(락 경합에 의한 처리량 역전, 아래 장애 2의 예시).
- glibc의 `pthread_mutex_lock`은 경합이 있을 때 **futex**로 잠든다(아래 로컬 재현). Java 스레드가 락을 기다리는 프로그램도 strace에 futex 호출이 잔뜩 보였다(로컬 재현, JDK 21).

## 동작·원리

### 1. 왜 원자 명령이 필요한가

```text
  잘못된 락 (OSTEP 28.6 — load/store만 사용)

  스레드 A                       스레드 B
  while (flag == 1) ;  // 0 봄
                                 while (flag == 1) ;  // 0 봄
  flag = 1;                      flag = 1;
  [임계 구역]                     [임계 구역]   <- 둘 다 들어왔다
```

- "flag를 보고"와 "flag를 1로 쓰기" 사이에 다른 스레드가 끼어들 수 있다.
- 그래서 CPU는 읽기와 쓰기를 **한 번에** 하는 명령을 준다.

### 2. 하드웨어 원자 명령 세 가지

```text
  명령                의사 코드 (한 명령으로 원자 실행)                  대표 이름
  test-and-set        old = *p; *p = new; return old;                    x86 XCHG
  compare-and-swap    old = *p; if (old == expected) *p = new;           x86 CMPXCHG ("compare-and-exchange")
                      return old;
  fetch-and-add       old = *p; *p = old + 1; return old;                x86 LOCK XADD
```

  - *원자적(atomic)*: 다른 CPU·스레드가 중간 상태를 볼 수 없다는 뜻이다. 전부 일어났거나 전혀 안 일어났다.
  - *CAS(compare-and-swap)*: "값이 내가 본 그대로면 바꾼다. 누가 먼저 바꿨으면 실패를 알린다." 실패하면 다시 읽고 재시도한다.

- 원자 명령 하나로 스핀락을 만든다(OSTEP 28.7, 28.9).

```c
/* test-and-set 스핀락 — GCC 원자 내장 함수 */
static int flag = 0;
void lock(void)   { while (__atomic_exchange_n(&flag, 1, __ATOMIC_ACQUIRE)) ; /* spin */ }
void unlock(void) { __atomic_store_n(&flag, 0, __ATOMIC_RELEASE); }
```

- `ACQUIRE`·`RELEASE`는 메모리 순서 지시다. 임계 구역 안의 읽기·쓰기가 락 밖으로 새지 않게 한다(자세한 것은 선행 architecture/14).

### 3. 스핀락의 평가 — 옳지만 공정하지 않다

```text
  test-and-set 스핀락           결과
  상호 배제                     된다
  공정성                        보장 없음 — 운 나쁜 스레드는 계속 진다 (기아)
  성능, 한 CPU                  나쁘다 — 락 주인이 선점되면 나머지가 타임 슬라이스를 통째로 돈다
  성능, 여러 CPU (스레드≈CPU)    괜찮다 — 임계 구역이 짧으면 금방 풀린다
```

- 한 CPU에서 락 주인이 임계 구역 도중 선점되면, 스케줄러가 돌리는 N−1개 스레드가 각자 한 타임 슬라이스씩 헛돈다(OSTEP 28.8).
- 공정성은 **티켓 락**으로 얻는다.

```text
  티켓 락 (OSTEP 28.11, Mellor-Crummey & Scott)

  ticket: 다음에 뽑을 번호     turn: 지금 들어갈 번호
  lock():   myturn = fetch_and_add(&ticket);   while (turn != myturn) ;  // spin
  unlock(): turn = turn + 1;

   번호표   A=0  B=1  C=2
   turn=0 → A 입장 → A unlock → turn=1 → B 입장 → ...   (FIFO, 기아 없음)
```

- 번호를 뽑은 스레드는 앞사람들이 다 나가면 반드시 들어간다.
- 그래도 기다리는 동안은 여전히 돈다.

### 4. 돌지 말고 자기 — futex

```text
  "돌까, 잘까"의 비용

  스핀:  [CPU 사용] ─ 락 풀림 ─> 즉시 진입          (짧은 대기면 이득, 긴 대기면 CPU 낭비)
  sleep: [CPU 반납] ─ 락 풀림 ─> 깨움 syscall ─> 스케줄 ─> 진입   (긴 대기면 이득, 짧으면 전환 비용이 더 큼)
```

리눅스의 답은 **futex(fast user-space mutex)**다.

```text
  futex = 유저 공간의 32비트 정수(futex word) + 커널의 주소별 대기 큐

   유저 공간                                          커널
  +---------------------------+
  | futex word (int, 4바이트)  |  경합 없음: CAS로 0→1, 끝. syscall 0번
  +---------------------------+
          | 경합 있음
          v
  futex(uaddr, FUTEX_WAIT, val) ------------------->  *uaddr == val 인지 확인하고
                                                      "확인+잠들기"를 원자적으로 → 대기 큐에 넣고 재움
  futex(uaddr, FUTEX_WAKE, 1)  -------------------->  그 주소의 대기자 중 하나를 깨움
```

- 경합이 없으면 모든 일이 유저 공간의 원자 명령으로 끝난다. 커널은 경합일 때만 끼어든다(futex(7)).
- `FUTEX_WAIT`는 "futex word가 아직 `val`이면 잠든다"를 **원자적으로** 한다. 값이 이미 바뀌었으면 `EAGAIN`으로 바로 돌아온다(FUTEX_WAIT(2const)).
  - 이 비교가 없으면 "잠들기 직전에 락이 풀리고 깨우기가 먼저 지나가는" **lost wake-up**이 생긴다. man 페이지가 이 비교의 목적을 그렇게 적는다. 17번 조건 변수의 핵심 문제와 같다.
- `FUTEX_WAKE`는 누구를 깨울지 보장하지 않는다. 우선순위가 높은 대기자가 먼저 깨어난다는 보장도 없다(FUTEX_WAKE(2const)).

  - *futex word*: 모든 플랫폼에서 4바이트 정렬된 32비트 정수다. 64비트 시스템도 같다(futex(2)).
  - *FUTEX_PRIVATE_FLAG*: 한 프로세스 안 스레드끼리만 쓰는 futex라고 알려 커널이 최적화하게 한다(리눅스 2.6.22+). strace에 `FUTEX_WAIT_PRIVATE`로 보이는 이유다.

### 5. glibc 뮤텍스의 세 상태

```text
  glibc lowlevellock (sysdeps/nptl/lowlevellock.h)

   0 : 잠기지 않음
   1 : 잠김, 대기자 없음        ← 경합 없는 경우는 0 ↔ 1 만 오간다 (syscall 없음)
  >1 : 잠김, 대기자 있을 수 있음  ← 이때만 unlock이 FUTEX_WAKE를 부른다

  lock 느린 경로 (__lll_lock_wait):
     while (atomic_exchange(futex, 2) != 0)
         futex_wait(futex, 2);          // 값이 여전히 2면 잠든다
```

- OSTEP는 이런 락을 **2단계 락(two-phase lock)**의 한 형태로 본다(28.16).
  - 2단계 락: 먼저 잠깐 돌아 보고(1단계), 못 잡으면 잔다(2단계).
  - OSTEP의 리눅스 예는 1단계에서 **한 번만** 시도한다. 일정 시간 도는 것은 그 일반화다.
  - glibc 기본 뮤텍스도 원자 명령으로 한 번 시도한 뒤 느린 경로로 간다. 여러 번 도는 것은 `PTHREAD_MUTEX_ADAPTIVE_NP` 유형이다. 지수 백오프로 정해진 횟수만큼 돈 뒤 잠든다(glibc `nptl/pthread_mutex_lock.c`).
- 리눅스 **커널** mutex도 같은 발상이다(docs.kernel.org locking/mutex-design).
  - fastpath: `cmpxchg`로 주인 필드를 바꿔 본다.
  - midpath(낙관적 스핀): 락 주인이 **CPU에서 실행 중**이면 곧 풀 것이라 보고 돈다. 스피너들은 MCS 락으로 줄을 세운다.
  - slowpath: 대기 큐에 들어가 잔다.

### 6. 로컬 재현 — 경합이 있어야 futex가 불린다

`pthread_mutex`로 카운터를 올리며 `strace -f -c -e trace=futex`로 센 결과다(예시, 리눅스 7.0, glibc 2.39, 24 CPU).

```text
  스레드 수   lock/unlock 횟수    futex 호출    해석
  1          100,000            1           경합 없음 → 전부 유저 공간 (1회는 스레드 join으로 보인다)
  4          400,000            2,910       경합 → 이때만 커널에서 잠들고 깨움 (그중 1,021회는 실패 반환)
```

- 실패 반환: 잠들려는 순간 값이 이미 바뀌어 커널이 `EAGAIN`으로 바로 돌려보낸 경우다. 다시 돌린 실행에서 실패는 전부 `EAGAIN`이었다(850회). 위 4절의 원자적 비교가 실제로 일하는 모습이다.

## 쓰이는 자료구조·알고리즘

- **CAS 재시도 루프** — `do { old = *p; } while (!CAS(p, old, f(old)));`. 락 없는 카운터·스택의 기본형이다(OSTEP 32.3 "Mutual Exclusion" 절).
- **티켓 락 = 번호표 큐** — fetch-and-add 두 카운터로 FIFO 순서를 만든다. 대기자 목록을 저장하지 않는 "암묵적 큐"다. [data-structure/04-queue-deque](../../data-structure/04-queue-deque/2-summary.md)
- **MCS 락 = 연결 리스트 큐** — 대기자마다 자기 노드의 변수를 보며 돈다. 모두가 같은 캐시 라인을 두드리는 test-and-set의 "cacheline bouncing"을 피한다(docs.kernel.org mutex-design). 리눅스 커널의 qspinlock은 MCS를 4바이트에 맞게 압축한 구현이다(kernel/locking/qspinlock.c 주석). [data-structure/02-linked-list](../../data-structure/02-linked-list/2-summary.md)
- **커널 futex 대기 큐 = 해시 버킷** — futex word 주소로 만든 키(`futex_key`)를 해시해 버킷을 찾고, 그 버킷의 대기자 목록에 넣는다(kernel/futex/core.c `futex_hash`). [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- **비트 압축** — glibc 상태 0/1/2, OSTEP 그림 28.10은 "최상위 비트 = 잠김, 나머지 비트 = 대기자 수"로 정수 하나에 두 정보를 담는다.

## 적용 — 풀어나가는 법

### 1. 락 고르기 순서

```text
  질문                                          고를 것
  경합이 거의 없는 짧은 갱신 하나?                   원자 변수 (C11 atomic, Java AtomicLong/LongAdder)
  임계 구역이 여러 줄이고 대기 가능?                  기본 뮤텍스 (pthread_mutex, synchronized, ReentrantLock)
  기아가 문제?                                     공정 락 (ReentrantLock(true)) — 처리량을 대가로
  유저 공간 스핀락?                                 거의 안 쓴다 — 실시간 정책 + CPU 고정일 때만
```

- `pthread_spin_init(3)` NOTES는 유저 공간 스핀락을 **일반 해법이 아니라고** 적는다.
  - `SCHED_FIFO`(또는 `SCHED_RR`) 같은 실시간 정책과 함께 쓰라고 한다.
  - `SCHED_OTHER`에서 쓰면 "설계 실수일 가능성이 높다"고 적는다. 락을 쥔 채 선점되면 나머지가 헛돌기 때문이다.

### 2. Java — 락은 반드시 finally에서 푼다

```java
private final ReentrantLock lock = new ReentrantLock();   // 기본: 비공정
void transfer() {
    lock.lock();
    try {
        // 임계 구역
    } finally {
        lock.unlock();          // 예외 경로에서도 반드시 해제
    }
}
```

- `new ReentrantLock(true)`는 공정 락이다. 가장 오래 기다린 스레드에 우선권을 준다. 대신 처리량이 "종종 훨씬" 낮을 수 있다(Java SE `ReentrantLock` 문서).
- 시간 제한 없는 `tryLock()`은 공정 설정을 **무시**하고 비어 있으면 바로 잡는다(같은 문서).
- 직접 스핀해야 한다면 루프 안에서 `Thread.onSpinWait()`를 부른다. 런타임에 "바쁜 대기 중"이라고 알리는 힌트다(Java SE `Thread` 문서). HotSpot의 x86 C2 컴파일러는 이 호출을 `pause` 명령으로 바꾼다(OpenJDK `src/hotspot/cpu/x86/x86.ad` `onspinwait`).

### 3. 경합을 줄이는 법

- 임계 구역을 짧게 한다. 락 안에서 I/O·로그·원격 호출을 하지 않는다.
- 락을 쪼갠다. 해시 테이블은 버킷마다 락을 둘 수 있다(OSTEP 29.4).
- 카운터는 스레드별로 따로 세고 가끔 합친다. OSTEP 29.1의 approximate counter, Java `LongAdder`가 같은 발상이다.

### 4. 진단 명령

```bash
# 이 프로세스가 futex에서 얼마나 자고 깨는가 (경합의 간접 지표)
strace -f -c -e trace=futex -p <pid>        # Ctrl-C로 요약

# 스레드별 상태·대기 위치: 락 대기면 S 상태 + wchan=futex_do_wait (7.0 기준 이름)
ps -L -o pid,lwp,stat,pcpu,wchan:20,comm -p <pid>

# 자발적/비자발적 문맥 전환 누계 (락 대기로 잠들면 voluntary가 오른다)
grep ctxt /proc/<pid>/status
pidstat -w -t -p <pid> 1

# Java: 누가 어떤 락을 기다리나
jstack <pid> | grep -A3 'BLOCKED\|parking to wait'
```

- 스핀락 과점유는 반대로 보인다. `%CPU`는 높은데 voluntary 전환이 거의 없다.
- `perf`는 이 환경에서 막혀 있어(`perf_event_paranoid=4`) 재현하지 못했다. 권한이 있으면 `perf top`에서 락 함수 비중을 본다.

## 장애 시나리오와 대처

### 1. 스핀락 과점유 → CPU는 100%인데 진행이 없다

- **현상**: CPU 사용률이 치솟는데 처리량은 늘지 않는다. 한 CPU·과밀 환경에서 특히 심하다.
- **보이는 형태**
  - `top`에서 해당 프로세스 `%CPU`가 스레드 수 × 100%에 가깝다. `ps -L`의 STAT가 `R`이다.
  - `/proc/<pid>/status`의 `voluntary_ctxt_switches`는 거의 안 오르고 `nonvoluntary`만 오른다.
  - 로컬 재현(예시, 리눅스 7.0): 4스레드를 CPU 하나에 묶고(`taskset -c 0`) 임계 구역을 길게 했더니, test-and-set 스핀락 1.15초 대 pthread_mutex 0.48초였다.
- **원인**: 락 주인이 임계 구역 도중 선점된다. 나머지 스레드가 타임 슬라이스를 통째로 돈다(OSTEP 28.8, pthread_spin_init(3) NOTES).
- **대처**
  - 유저 공간 스핀락을 뮤텍스로 바꾼다. 뮤텍스는 못 잡으면 잠들어 CPU를 내준다(glibc 기본 뮤텍스는 원자 명령으로 한 번 시도한 뒤 futex로 잠든다, 5절).
  - 정말 스핀이 필요하면 CPU를 고정하고 실시간 정책을 쓰며, 스레드 수를 코어 수 이하로 둔다.

### 2. 락 경합 → 코어를 늘려도 처리량이 역전된다

- **현상**: 스레드·코어를 늘렸더니 초당 처리량이 오히려 줄었다.
- **보이는 형태** (로컬 재현, 공유 카운터 하나를 락으로 보호, 예시, 리눅스 7.0, 24 CPU)

```text
  스레드   test-and-set 스핀락        pthread_mutex
           처리량       CPU 시간       처리량       CPU 시간
  1       약 6,700만/s   0.004s      약 4,000만/s   0.006s
  4       약   700만/s   0.43s       약   960만/s   0.27s
  24      약   130만/s   67s         약   600만/s   14s
  (각 스레드 20만 회 증가. 처리량 = 총 증가 횟수 ÷ 벽시계 시간)
```

  - 스레드가 1→24로 늘자 스핀락 처리량은 약 50분의 1이 됐다. CPU 시간은 1만 배 이상 늘었다.
- **원인**
  - 임계 구역은 한 번에 하나만 실행된다. 스레드를 늘려도 **직렬 구간은 빨라지지 않는다**.
  - 대신 락 변수의 캐시 라인이 코어 사이를 오가는 비용이 커진다(cacheline bouncing, mutex-design 문서).
  - 스핀락은 여기에 헛도는 CPU까지 더해진다.
- **대처**
  - 공유 지점 자체를 없앤다. 스레드별 카운터 후 합산, `LongAdder`, 샤딩한다.
  - 임계 구역에서 불필요한 일을 뺀다.
  - 원자 변수 하나로 끝나는 갱신은 락 대신 원자 명령을 쓴다(같은 재현에서 4스레드 `fetch_add`는 0.08초, mutex는 0.44초였다, 스레드당 100만 회).

### 3. 비공정 락 → 특정 요청만 꼬리 지연이 길다

- **현상**: 평균 지연은 괜찮은데 p99가 튄다. 특정 스레드가 계속 락을 못 잡는다.
- **보이는 형태**: 스레드 덤프를 여러 번 떠도 같은 스레드가 `BLOCKED`·`parking to wait for`에 머문다.
- **원인**: 비공정 락은 방금 도착한 스레드가 줄 선 스레드를 앞지를 수 있다(barging). test-and-set 스핀락은 공정성 보장이 없다(OSTEP 28.8).
- **대처**
  - 공정 락(`new ReentrantLock(true)`, 티켓 락 계열)을 검토한다. 처리량이 줄어드는 대가를 잰다.
  - 근본은 경합 자체를 줄이는 것이다(시나리오 2).

### 4. 예외 경로에서 unlock 누락 → 다른 스레드의 호출이 멈춤

- **현상**: 어느 순간부터 해당 기능의 요청이 멈춘다. 에러 로그는 첫 번째 예외 하나뿐이다.
  - `ReentrantLock`은 재진입 락이다. unlock을 빠뜨린 스레드가 살아서 다시 `lock()`하면 보유 횟수(hold count)만 1 늘고 바로 통과한다(Java SE `ReentrantLock.lock()` 문서).
  - 그래서 **다른 스레드의** 호출만 영원히 기다린다. 스레드 풀이면 그 워커가 받은 요청은 성공해 "간헐적 멈춤"처럼 보일 수 있다.
- **보이는 형태**
  - Java 스레드 덤프에 같은 `ReentrantLock`을 기다리는 스레드가 줄줄이 `WAITING (parking)`이다. 주인 스레드는 이미 다른 일을 하거나 끝났다. 주인이 종료했으면 누구도 락을 얻지 못한다.
  - `jstack -l <pid>`의 "Locked ownable synchronizers"에서 락을 쥔 스레드를 찾는다. 코드에서는 `isHeldByCurrentThread()`·`getHoldCount()`로 확인한다.
  - C라면 `ps -L`에서 모두 `S` + `futex_do_wait`다.
- **원인**: `lock()` 뒤 예외가 나서 `unlock()`을 건너뛰었다. `synchronized`는 블록을 빠져나갈 때 자동으로 풀지만 `Lock`은 직접 풀어야 한다.
- **대처**: `lock(); try { … } finally { unlock(); }` 형식을 지킨다. 정적 분석 규칙으로 막는다.

## 핵심 문장

- 락은 하드웨어 원자 명령(test-and-set·CAS·fetch-and-add)으로 "확인+획득"을 한 동작으로 만든 것이다.
- 스핀락은 옳지만 공정하지 않다. 한 CPU나 과밀 환경에서는 락 주인이 선점되면 나머지가 타임 슬라이스를 헛돈다.
- 티켓 락은 fetch-and-add로 FIFO 공정성을 얻는다. MCS 락은 각자 자기 변수에서 돌아 캐시 라인 핑퐁을 줄인다.
- 리눅스 futex는 경합이 없으면 syscall 없이 유저 공간에서 끝나고, 경합일 때만 커널이 "값 비교+잠들기"를 원자적으로 한다.
- glibc·커널 mutex는 "먼저 유저/빠른 경로에서 시도하고, 안 되면 잔다"는 2단계 락 계열이다. glibc 기본 뮤텍스는 한 번만 시도하고, 여러 번 도는 것은 ADAPTIVE 유형·커널 mutex(주인이 실행 중일 때)다.
- 락 경합은 코어를 늘려도 풀리지 않는다. 공유 지점을 없애거나 쪼개야 처리량이 오른다.

## 관련 주제·근거

- 선행
  - [15-race-conditions](../15-race-conditions/2-summary.md) — 임계 구역·원자성. 기초는 원고 [process-thread §10~11](../../foundations/process-thread/README.md)
  - architecture `14-cache-coherence-and-memory-ordering` — MESI·배리어·CAS. 미작성, [architecture/README](../../architecture/README.md)
- 후속
  - [17-condition-variables-and-monitors](../17-condition-variables-and-monitors/2-summary.md) — 락 위에 "조건이 될 때까지 잠들기"를 얹는다
  - [19-deadlock](../19-deadlock/2-summary.md), [20-concurrency-bugs](../20-concurrency-bugs/2-summary.md)(우선순위 역전·PI futex)
- 교재
  - OSTEP 28장 "Locks" — 28.4 평가 기준, 28.6 load/store 실패, 28.7 test-and-set, 28.8 스핀락 평가, 28.9 CAS, 28.11 fetch-and-add·티켓 락, 28.13 yield, 28.14 큐와 park/unpark, 28.15 리눅스 futex(그림 28.10), 28.16 2단계 락 <https://pages.cs.wisc.edu/~remzi/OSTEP/threads-locks.pdf>
  - OSTEP 29장 "Lock-based Concurrent Data Structures" — 29.1 approximate counter, 29.4 버킷별 락 <https://pages.cs.wisc.edu/~remzi/OSTEP/threads-locks-usage.pdf>
- Linux
  - futex(7) — 경합 없는 경우는 유저 공간에서 끝남 <https://man7.org/linux/man-pages/man7/futex.7.html>
  - futex(2) — futex word 32비트·4바이트 정렬, 비교+블록의 원자성, `FUTEX_PRIVATE_FLAG`(2.6.22+) <https://man7.org/linux/man-pages/man2/futex.2.html>
  - FUTEX_WAIT(2const) — `EAGAIN`, lost wake-up 방지 목적 · FUTEX_WAKE(2const) — 깨울 대상 보장 없음 <https://man7.org/linux/man-pages/man2/FUTEX_WAIT.2const.html>
  - pthread_spin_init(3) NOTES — 유저 공간 스핀락의 제약 <https://man7.org/linux/man-pages/man3/pthread_spin_init.3.html>
  - docs.kernel.org locking/mutex-design — fastpath·midpath(낙관적 스핀, MCS)·slowpath <https://docs.kernel.org/locking/mutex-design.html>
  - kernel/locking/qspinlock.c — MCS 기반 queued spinlock <https://github.com/torvalds/linux/blob/master/kernel/locking/qspinlock.c>
  - glibc `sysdeps/nptl/lowlevellock.h`(상태 0/1/>1), `nptl/lowlevellock.c` `__lll_lock_wait`, `nptl/pthread_mutex_lock.c`(ADAPTIVE 스핀) <https://sourceware.org/git/?p=glibc.git;a=blob;f=nptl/lowlevellock.c>
- Java SE 21 API — `ReentrantLock`(공정성, `tryLock`의 barging), `Thread.onSpinWait` <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/locks/ReentrantLock.html>
- Intel SDM(felixcloutier 발췌) — `PAUSE`: spin-wait 루프 성능 힌트 <https://www.felixcloutier.com/x86/pause> · `XADD`: LOCK 접두사로 원자 실행 <https://www.felixcloutier.com/x86/xadd> · x86 `xchg`·compare-and-exchange 명칭은 OSTEP 28.7·28.9
- 로컬 재현(리눅스 7.0, glibc 2.39, gcc 13.3, 24 CPU): test-and-set·pthread_spin·pthread_mutex·원자 fetch_add 카운터 비교, 스레드 1~96 처리량, `strace -c`로 futex 호출 수, `taskset -c 0` 단일 CPU 비교
