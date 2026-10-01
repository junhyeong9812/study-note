# os/20-concurrency-bugs — 교착이 아닌 동시성 버그: 원자성 위반·순서 위반·기아·라이브락·우선순위 역전 — 정리 (힌트)

## 해결하는 문제

19번 교착은 "멈춤"이라 눈에 띈다.\
실제 동시성 버그는 **교착이 아닌 것**이 더 많다.

```text
  Lu 외, ASPLOS 2008 — MySQL·Apache·Mozilla·OpenOffice에서 고쳐진 동시성 버그 105개

  교착 아님   74개  ──  그중 97%가 두 패턴:  원자성 위반 · 순서 위반
  교착        31개  ──  그중 97%가 "스레드 2개가 자원 2개 이하를 두고 원형 대기"

  96%는 "스레드 2개 사이의 특정 순서"만 강제하면 반드시 재현된다
```

- 이 수치가 주는 교훈은 두 가지다.
  - 버그의 **모양은 몇 가지뿐**이다. 패턴을 알면 코드 리뷰에서 잡는다.
  - 재현 조건은 대부분 **두 스레드의 특정 끼어들기 순서** 하나다. 그 순서가 드물게 나와서 테스트에서는 안 보이고 부하에서만 보인다.

쉬운 예: 공유 문서를 두 사람이 고친다.
- "내가 확인한 뒤 고친다"가 원자적이지 않으면 남의 수정을 덮어쓴다(원자성 위반).
- "초안이 올라온 뒤 검토한다"를 약속만 하고 강제하지 않으면 빈 문서를 검토한다(순서 위반).
- 서로 "먼저 하세요"만 반복하면 둘 다 바쁜데 아무 일도 안 된다(라이브락).
- 급한 사람이 느긋한 사람의 펜을 기다리는데, 중간 급한 사람이 느긋한 사람을 계속 불러 세운다(우선순위 역전).

똑같은 구조다.\
공유 상태에 대한 **가정**(이 구간은 원자적이다, 이 일이 먼저 일어난다, 결국 내 차례가 온다)이 강제되지 않을 때 버그가 된다.

## 동작·원리

### 1. 원자성 위반 — 확인과 사용 사이에 끼어들기

```text
  MySQL 사례 (OSTEP 그림 32.2)

  스레드 1                                   스레드 2
  if (thd->proc_info) {        ← NULL 아님 확인
                                              thd->proc_info = NULL;
      fputs(thd->proc_info, ...);  ← NULL 역참조 → 크래시
  }
```

- Lu 외의 정의: "여러 메모리 접근 사이에 기대한 직렬성이 깨짐 — 원자적이어야 할 구역에 원자성이 강제되지 않음"(OSTEP 32.2 인용).
- 15번의 check-then-act(`if (재고 > 0) 재고--`)와 같은 모양이다.
- 고치기: 확인과 사용을 **같은 락**으로 감싼다. 그 필드를 건드리는 다른 모든 코드도 같은 락을 잡아야 한다(OSTEP 그림 32.3).

**싱글 스레드 런타임에서도 생긴다.** Node.js는 JS를 한 스레드에서 돌리지만, `await`마다 다른 작업이 끼어들 수 있다.

```ts
let stock = 1;
async function buy(name: string) {
  const s = await db.read();           // 확인  ─┐ 이 사이에 다른 buy()가 실행된다
  if (s > 0) await db.write(s - 1);    // 사용  ─┘
}
await Promise.all([buy("A"), buy("B")]);
// 로컬 재현(예시, Node 18): A, B 모두 "saw 1"로 성공 → 재고 1개로 두 건 판매
```

### 2. 순서 위반 — "A가 먼저"를 강제하지 않음

```text
  Mozilla 사례 (OSTEP 그림 32.4)

  스레드 1                                   스레드 2 (스레드 1이 만든 새 스레드)
  mThread = PR_CreateThread(mMain, ...);
      └─ 생성 즉시 스레드 2가 먼저 실행될 수 있다 ─>  mState = mThread->State;   ← mThread 아직 NULL
  (여기서야 mThread에 대입)
```

- Lu 외의 정의: "두 (묶음의) 메모리 접근 사이의 기대 순서가 뒤집힘 — A가 항상 B보다 먼저여야 하는데 강제되지 않음".
- 고치기: 순서를 **동기화로 강제**한다. 상태 변수 + 조건 변수(17번), 초깃값 0 세마포어(18번), Java `CountDownLatch`·`CompletableFuture`.
- Lu 외에서 교착 아닌 버그의 약 3분의 1(32%)이 순서 위반이었다.

### 3. 기아 — 진행은 되는데 나만 영원히 못 간다

```text
  비공정 락:     새로 온 스레드가 줄 선 스레드를 계속 앞지른다 (barging)
  읽기-쓰기 락:   독자가 끊이지 않으면 작가는 영원히 못 들어간다 (OSTEP 31.5)
  우선순위:      높은 우선순위 일이 계속 있으면 낮은 쪽은 CPU를 못 받는다
```

- 시스템 전체는 진행한다. 특정 스레드만 진행하지 못한다. 교착(전체 정지)과 다르다.
- 해법은 공정성이다. 티켓 락(16번), 공정 모드(`ReentrantLock(true)`, `Semaphore(n, true)`), 작가 우선 읽기-쓰기 락.

### 4. 라이브락 — 모두 바쁜데 아무도 못 간다

```text
  trylock으로 교착을 피하려는 코드 (OSTEP 32.3)

  스레드 1                       스레드 2
  lock(L1)                       lock(L2)
  trylock(L2) 실패                trylock(L1) 실패
  unlock(L1), 처음으로            unlock(L2), 처음으로
  lock(L1)                       lock(L2)
  trylock(L2) 실패 ...            trylock(L1) 실패 ...      ← 계속 반복
```

- 교착처럼 멈추지는 않는다. 둘 다 CPU를 쓰며 계속 실행 중이다. 그런데 **진행이 0에 가깝다**(OSTEP 32.3).
- 해법: 재시도 전에 **무작위 지연**을 둔다. 둘이 같은 박자로 부딪칠 확률이 떨어진다.
- 로컬 재현(예시, 리눅스 7.0): 두 스레드가 1초 동안 위 패턴을 돌렸다.

```text
  재시도 전 지연       성공(스레드1/스레드2)      재시도(스레드1/스레드2)
  없음                19,075 / 20,515           989,754 / 947,327     ← 시도의 98%가 헛수고
  무작위 0~49µs       321,492 / 334,862          6,267 / 6,422
```

  - 완전한 정지는 아니었다. 하지만 CPU는 쓰면서 성공은 무작위 지연 버전의 약 16분의 1이었다.
  - *라이브락(livelock)*: 스레드들이 상태를 계속 바꾸며 실행 중인데, 서로에게 반응하느라 아무도 앞으로 나아가지 못하는 상태다.

### 5. 우선순위 역전 — 낮은 놈이 높은 놈을 막는다

```text
  우선순위: H(높음) > M(중간) > L(낮음), 선점형 우선순위 스케줄러

  시간 ->
  L:  lock(R) ──[임계 구역]─┐                           (M이 있는 동안 실행 못 함)       ... unlock(R)
  H:                        └ 깨어남, lock(R) → 대기 ──────────────────────────────────────── 진행
  M:                              깨어남 → L을 선점하고 계속 실행 ──────────────────>
                                   └─ H는 M보다 높은데도 M이 끝날 때까지 못 간다 = "무한(unbounded)" 역전
```

- H가 L의 락을 기다리는 것 자체는 피할 수 없는 **유한한** 역전이다. 문제는 M이 L을 계속 선점해 역전 시간이 **정해지지 않는** 경우다(docs.kernel.org rt-mutex-design "Unbounded Priority Inversion").
- 스핀락이면 스레드 둘로도 생긴다. H가 L이 쥔 스핀락에서 돌기 시작하면, 스케줄러는 항상 H를 고르므로 L이 영원히 못 돌고 시스템이 멈춘다(OSTEP 28장 aside).
- 해법 (OSTEP 28장 aside)
  - **우선순위 상속(PI)**: H가 L의 락에서 막히면 L이 잠시 H의 우선순위를 물려받는다. M이 L을 선점하지 못한다. L이 락을 풀면 원래 우선순위로 돌아간다.
  - 스핀락을 쓰지 않는다(스핀으로 인한 경우).
  - 모든 스레드의 우선순위를 같게 한다.
- PI는 **전이적**이어야 한다. H가 L1을 기다리고, L1의 주인이 L2를 기다리면 사슬 전체가 H의 우선순위를 받는다(futex(2) PI 절, rt-mutex의 "PI chain").

#### Mars Pathfinder (1997)

```text
  bc_dist (높음, 버스 데이터 분배)      ─ select()용 뮤텍스를 기다림
  ASI/MET (낮음, 기상 데이터)           ─ 그 뮤텍스를 쥔 채 선점됨
  여러 중간 우선순위 작업                 ─ ASI/MET보다 높아 계속 실행
  bc_sched (다음 버스 주기 준비)         ─ "bc_dist가 제시간에 안 끝났다" → 치명 오류 → 컴퓨터 리셋
```

- 착륙 며칠 뒤부터 우주선이 전체 리셋을 반복했다(Mike Jones, "What really happened on Mars?", 1997).
- JPL의 Glenn Reeves 설명: 뮤텍스는 VxWorks `select()` 메커니즘이 파일 디스크립터 대기 목록을 보호하려 만든 것이었다. 리셋은 `bc_sched`가 `bc_dist`의 마감 초과를 감지해 일으켰다.
  - Mike Jones의 글은 이를 "워치독 타이머가 리셋"이라고 요약했다. 두 설명 모두 "마감을 감시하는 장치가 리셋을 걸었다"는 점은 같다.
- 원인 추적: 지상의 복제 기체에서 VxWorks 전체 트레이스를 켜고 재현해 역전을 찾았다.
- 수정: 그 뮤텍스의 **우선순위 상속 옵션**이 꺼져 있었다. 우주선에 올라가 있던 C 인터프리터로 전역 변수를 바꿔 켜자 리셋이 사라졌다.
- 교훈(Jones): 비행 전 시험에서도 재현되지 않는 리셋이 한두 번 있었지만 "하드웨어 결함일 것"으로 넘겼다.

#### 리눅스와 JVM에서는

- 리눅스는 **PI futex**를 제공한다(futex(2) "Priority-inheritance futexes"). pthread에서는 `pthread_mutexattr_setprotocol(&attr, PTHREAD_PRIO_INHERIT)`로 켠다(POSIX).
  - 로컬 재현(예시, 리눅스 7.0): PI 뮤텍스에서 경합이 나자 strace에 `FUTEX_LOCK_PI_PRIVATE`·`FUTEX_UNLOCK_PI_PRIVATE`가 보였다. 기본 뮤텍스는 `FUTEX_WAIT`/`FUTEX_WAKE`다.
- 무한 역전은 엄격한 우선순위 스케줄링(`SCHED_FIFO`·`SCHED_RR`)에서 두드러진다. 일반 정책 `SCHED_OTHER`에서도 nice 값 차이 1마다 약 1.25배 가중치가 붙어, nice +19 작업은 높은 부하가 있으면 CPU를 거의 받지 못한다(sched(7)). 그래서 긴 지연으로 나타날 수 있다.
  - 이 환경은 `RLIMIT_RTPRIO`가 0이라 일반 사용자가 실시간 정책을 쓸 수 없어(sched(7)) 역전 자체는 재현하지 않았다.
- HotSpot은 리눅스에서 기본(`ThreadPriorityPolicy=0`)일 때 `Thread.setPriority`를 OS 우선순위에 반영하지 않는다(OpenJDK `os_linux.cpp` `os::set_native_priority`). JVM 코드의 우선순위 설정만으로는 역전도, 그 해결도 기대하기 어렵다.

## 쓰이는 자료구조·알고리즘

- **우선순위 상속 사슬(PI chain)** — "락 → 주인 → 주인이 기다리는 락 → …"을 따라가며 우선순위를 올린다. 리눅스 rt-mutex는 락마다 대기자를 우선순위순 **레드블랙 트리**(waiters rbtree)로, 주인 태스크마다 최상위 대기자들을 `pi_waiters` 트리로 둔다(docs.kernel.org rt-mutex-design). [data-structure/16-red-black-tree](../../data-structure/16-red-black-tree/2-summary.md)
- **무작위 지수 백오프** — 라이브락을 깨는 기본 도구다. 네트워크 재전송·분산 재시도와 같은 발상이다. [ops-patterns/01-retry-backoff](../../ops-patterns/01-retry-backoff/2-summary.md)
- **CAS 재시도(조건부 갱신)** — 원자성 위반을 락 없이 고친다. DB에서는 `UPDATE … WHERE stock > 0`이 같은 역할을 한다.
- **happens-before 관계** — 순서 위반은 "A가 B보다 먼저"라는 관계를 동기화(락 해제→획득, signal→wait 복귀, latch countDown→await 복귀)로 만들어 줘야 고쳐진다. 동적 경쟁 탐지기 ThreadSanitizer도 두 접근 사이에 happens-before가 없으면(`HappensBefore` 검사) 경쟁으로 보고한다(google/sanitizers wiki "ThreadSanitizerAlgorithm").

## 적용 — 풀어나가는 법

### 1. 버그 패턴별 처방

| 패턴 | 코드에서 보이는 모양 | 처방 |
|---|---|---|
| 원자성 위반 | `if (x != null) use(x)`, `if (map.get(k) == null) map.put(k, v)`, read → await → write | 같은 락으로 묶기, 원자 연산(`computeIfAbsent`, `compareAndSet`), DB 조건부 UPDATE |
| 순서 위반 | 생성자·초기화가 끝나기 전에 다른 스레드가 쓴다 | 상태 변수 + 조건 변수, 세마포어(0), `CountDownLatch`, `CompletableFuture` |
| 기아 | 비공정 락, 읽기-쓰기 락, 우선순위 | 공정 모드, 작가 우선, 우선순위 평준화 |
| 라이브락 | trylock-실패-놓기-재시도, 서로 양보 | 무작위 백오프, 재시도 상한, 락 순서로 바꾸기 |
| 우선순위 역전 | 우선순위 다른 스레드가 같은 락을 공유 | PI 뮤텍스, 스핀락 금지, 우선순위 통일, 락 구간 최소화 |

### 2. 원자성 위반 고치기 — Java와 DB

```java
// 나쁜 예: 확인과 삽입 사이에 끼어들 수 있다
if (!cache.containsKey(k)) cache.put(k, load(k));
// 좋은 예: 확인+삽입을 한 연산으로 (ConcurrentHashMap)
cache.computeIfAbsent(k, this::load);

// 카운터: 읽고-더하고-쓰기를 CAS 한 번으로
AtomicInteger stock = new AtomicInteger(10);
boolean sold = false;
for (int s = stock.get(); s > 0; s = stock.get()) {
    if (stock.compareAndSet(s, s - 1)) { sold = true; break; }
}
```

```sql
-- 재고: 확인과 차감을 한 문장으로. 영향받은 행이 0이면 품절
UPDATE product SET stock = stock - 1 WHERE id = ? AND stock > 0;
```

- Node의 `await` 사이 원자성 위반도 같은 SQL로 고친다. 애플리케이션 메모리의 "확인"을 믿지 않고, 조건을 DB 문장 안에 넣는다.

### 3. 드물게 나는 버그를 드러내기

- Lu 외: 대부분의 버그는 두 스레드의 특정 순서만으로 재현된다. 그러니 **끼어들기 순서를 흔드는** 것이 핵심이다.
  - 확인과 사용 사이에 일부러 `sleep`·`Thread.yield()`를 넣어 본다(재현용, 커밋 금지).
  - 스레드 수를 코어 수보다 많이 두고, `taskset`으로 CPU 하나에 몰아 선점을 늘린다.
  - C/C++은 ThreadSanitizer(`-fsanitize=thread`)로 데이터 경쟁과 락 순서 위반을 본다(19번).

### 4. 진단 명령

```bash
# 라이브락·스핀: CPU는 높은데 처리량이 없다
top -H -p <pid>                              # 스레드별 CPU
pidstat -u -t -p <pid> 1
pidstat -w -t -p <pid> 1                     # 스레드별 cswch/s(자발)·nvcswch/s(비자발)
grep ctxt /proc/<pid>/task/<tid>/status      # 그 스레드의 전환 수. 자발적 전환이 거의 안 늘면 돌고 있다
                                             # (/proc/<pid>/status는 <pid> 태스크 하나(메인 스레드)의 값뿐)

# 기아: 특정 스레드만 오래 기다린다 → 덤프를 여러 번 떠서 같은 스레드가 계속 대기인지 본다
for i in 1 2 3; do jstack <pid> > dump.$i; sleep 5; done

# 우선순위 역전: 스케줄 정책·우선순위 확인
chrt -p <tid>                                 # 정책과 실시간 우선순위
ps -L -o pid,lwp,cls,rtprio,ni,stat,comm -p <pid>

# PI 뮤텍스를 쓰는지: 경합 시 FUTEX_LOCK_PI가 보인다
strace -f -e trace=futex -p <pid>
```

## 장애 시나리오와 대처

### 1. 원자성 위반 → `count++` 유실, 재고 음수, 간헐적 NPE

- **현상**: 부하 테스트에서만 합계가 틀리거나 재고가 음수가 된다. 드물게 NPE가 난다.
- **보이는 형태**
  - 합계가 기대보다 작다. 로컬 재현(16번 실험 프로그램의 락 없는 모드): 4스레드 × 100만 회 증가가 400만 대신 약 133만이었다(예시, 리눅스 7.0, `-O2`).
  - 재고가 1개인데 두 건 판매됐다. 로컬 재현(Node 18): 두 `buy()`가 모두 "saw 1"로 성공.
  - `NullPointerException` 스택이 "null 확인 직후" 줄을 가리킨다(MySQL `proc_info` 유형).
- **원인**: 확인(check)과 사용(act) 사이에 다른 스레드·다른 비동기 작업이 끼어들었다.
- **대처**: 확인과 사용을 한 락·한 원자 연산·한 SQL 문장으로 묶는다. 그 공유 변수를 건드리는 **모든** 경로를 같은 방식으로 바꾼다.

### 2. 순서 위반 → 시작 직후에만 가끔 NPE

- **현상**: 배포·재시작 직후 가끔 초기화 관련 NPE가 난다. 재현이 잘 안 된다.
- **보이는 형태**: 스택이 새 스레드의 시작 함수에서 "아직 대입되지 않은 필드"를 읽는 줄을 가리킨다.
- **원인**: "초기화가 먼저"라는 가정을 동기화로 강제하지 않았다. 새 스레드가 생성 즉시 먼저 실행됐다(Mozilla `mThread` 유형).
- **대처**: 초기화 완료를 상태 변수 + 조건 변수, `CountDownLatch`, `CompletableFuture`로 기다린다. 생성자 안에서 `this`를 다른 스레드에 넘기지 않는다.

### 3. 라이브락 → CPU는 바쁜데 진행 0

- **현상**: CPU 사용률은 높은데 처리량이 거의 없다. 교착 탐지에는 아무것도 안 걸린다.
- **보이는 형태**
  - `top -H`에서 해당 스레드들이 계속 `R`이다. 스레드 덤프를 여러 번 떠도 스택이 매번 재시도 루프 근처다.
  - 재시도·실패 카운터가 폭증한다. 로컬 재현: 백오프 없는 trylock 루프에서 시도의 약 98%가 실패했다.
- **원인**: 충돌하면 즉시, 같은 박자로 재시도한다. 서로의 재시도가 계속 부딪친다.
- **대처**
  - 재시도 전 **무작위 지연**(지수 백오프 + 지터)을 넣는다. 로컬 재현에서 성공이 약 16배로 늘었다.
  - 재시도 상한을 둔다.
  - 가능하면 trylock 대신 락 순서로 교착을 예방한다(19번).

### 4. 우선순위 역전 → 마감 초과, 워치독 리셋

- **현상**: 높은 우선순위 작업이 가끔 마감을 놓친다. 임베디드·실시간 시스템에서는 감시 장치가 리셋을 건다(Mars Pathfinder).
- **보이는 형태**
  - 마감 초과 로그, 워치독 리셋, 오디오 끊김 같은 지연 스파이크.
  - 트레이스에서: 높은 우선순위 스레드가 락 대기 → 그 락의 주인(낮은 우선순위)은 실행 대기 → 중간 우선순위 스레드가 CPU를 차지.
- **원인**: 우선순위가 다른 스레드들이 **상속 없는** 락을 공유했다.
- **대처**
  - 공유 락을 PI 뮤텍스로 만든다(`PTHREAD_PRIO_INHERIT`, 리눅스 PI futex).
  - 실시간 스레드에서 유저 공간 스핀락을 쓰지 않는다(pthread_spin_init(3)은 유저 스핀락이 우선순위 역전에 취약하다고 적는다).
  - 높은 우선순위 경로가 낮은 우선순위와 락을 공유하지 않게 설계한다. 락 구간을 짧게 한다.
  - 재현되지 않는 리셋을 "하드웨어 탓"으로 넘기지 않는다. 트레이스를 남길 수 있게 한다(Jones의 교훈).

### 5. 기아 → 평균은 괜찮은데 특정 요청만 오래 걸린다

- **현상**: p50은 정상인데 p99·p999가 튄다. 쓰기 요청만 유독 느리다.
- **보이는 형태**: 여러 번 뜬 덤프에서 같은 스레드가 계속 같은 락을 기다린다. 읽기-쓰기 락이면 쓰기 쪽이 계속 대기다.
- **원인**: 비공정 락에서 새 요청이 계속 앞지르거나, 독자가 끊이지 않아 작가가 들어가지 못한다(OSTEP 31.5).
- **대처**: 공정 모드를 쓰거나 작가 우선 정책을 고른다. 처리량 손실을 측정한 뒤 결정한다. 락 보유 시간을 줄여 경합 자체를 줄인다.

## 핵심 문장

- 실제 동시성 버그의 대부분은 교착이 아니다. Lu 외 연구에서 교착 아닌 버그의 97%가 원자성 위반 또는 순서 위반이었다.
- 원자성 위반은 확인과 사용 사이에 끼어들기다. 싱글 스레드 Node도 `await` 사이에서 같은 버그가 난다. 같은 락·원자 연산·조건부 SQL로 묶는다.
- 순서 위반은 "A가 먼저"를 동기화로 강제하지 않은 것이다. 조건 변수·세마포어·래치로 순서를 만든다.
- 라이브락은 모두 실행 중인데 진행이 없는 상태다. 무작위 백오프로 박자를 흩뜨린다.
- 우선순위 역전은 중간 우선순위가 락 주인을 선점해 높은 우선순위가 끝없이 기다리는 것이다. 우선순위 상속이 해법이고, Mars Pathfinder는 그 옵션 하나로 고쳐졌다.
- 대부분의 버그는 두 스레드의 특정 순서 하나로 재현된다. 끼어들기를 흔들어 드러낸다.

## 관련 주제·근거

- 선행: [19-deadlock](../19-deadlock/2-summary.md) — 교착 버그와 trylock 예방이 낳는 라이브락
- 연결
  - [15-race-conditions](../15-race-conditions/2-summary.md) — 임계 구역·check-then-act
  - [16-locks-and-spinlocks](../16-locks-and-spinlocks/2-summary.md) — 스핀락·공정성·futex
  - [17-condition-variables-and-monitors](../17-condition-variables-and-monitors/2-summary.md) · [18-semaphores](../18-semaphores/2-summary.md) — 순서 위반의 처방
  - [08-cpu-scheduling](../08-cpu-scheduling/2-summary.md) — 우선순위·nice·실시간 정책
  - [27-event-based-concurrency](../27-event-based-concurrency/2-summary.md) — 이벤트 루프에서의 원자성
  - [38-os-incidents](../38-os-incidents/2-summary.md) — Mars Pathfinder 등 실사건.
  - [api-design/03-stock-deduct](../../api-design/03-stock-deduct/2-summary.md) — 재고 차감의 조건부 갱신
  - [ops-patterns/01-retry-backoff](../../ops-patterns/01-retry-backoff/2-summary.md) — 지터 백오프
- 교재·논문
  - OSTEP 32장 "Common Concurrency Problems" — 32.1 Lu 외 연구 요약(그림 32.1), 32.2 원자성 위반(그림 32.2·32.3)·순서 위반(그림 32.4·32.5)·97%, 32.3 trylock과 라이브락 <https://pages.cs.wisc.edu/~remzi/OSTEP/threads-bugs.pdf>
  - OSTEP 28장 aside "More Reason To Avoid Spinning: Priority Inversion"(28.14 부근) <https://pages.cs.wisc.edu/~remzi/OSTEP/threads-locks.pdf> · 31.5 읽기-쓰기 락의 작가 기아 <https://pages.cs.wisc.edu/~remzi/OSTEP/threads-sema.pdf>
  - S. Lu, S. Park, E. Seo, Y. Zhou, "Learning from Mistakes — A Comprehensive Study on Real World Concurrency Bug Characteristics", ASPLOS 2008 — Findings (1)~(13): 97%·32%·96%·22%·66%·97% 등 <https://www.cs.columbia.edu/~junfeng/08fa-e6998/sched/readings/concurrency-bugs.pdf>
  - L. Sha, R. Rajkumar, J. Lehoczky, "Priority Inheritance Protocols", IEEE Trans. Computers, 1990 (Jones 글 경유, 원문 미열람)
- Mars Pathfinder
  - Mike Jones, "What really happened on Mars Rover Pathfinder" (1997-12-07) <https://www.cs.cornell.edu/courses/cs614/1999sp/papers/pathfinder.html>
  - Glenn Reeves(JPL), "What really happened on Mars? — Authoritative Account" (1997-12-15) <https://www.cs.unc.edu/~anderson/teach/comp790/papers/mars_pathfinder_long_version.html>
- Linux·POSIX
  - futex(2) "Priority-inheritance futexes" — 정의, 전이성 <https://man7.org/linux/man-pages/man2/futex.2.html>
  - docs.kernel.org locking/rt-mutex-design — unbounded priority inversion, PI chain, waiters rbtree <https://docs.kernel.org/locking/rt-mutex-design.html>
  - sched(7) — nice 1당 약 1.25배, `RLIMIT_RTPRIO` <https://man7.org/linux/man-pages/man7/sched.7.html>
  - `fs/proc/array.c` `task_context_switch_counts()` — `/proc/<pid>/status`의 ctxt 값은 그 태스크 하나의 `nvcsw`·`nivcsw` <https://github.com/torvalds/linux/blob/master/fs/proc/array.c>, pidstat(1) `-w`·`-t`
  - POSIX.1-2024 `pthread_mutexattr_setprotocol` — `PTHREAD_PRIO_INHERIT` <https://pubs.opengroup.org/onlinepubs/9799919799/functions/pthread_mutexattr_setprotocol.html>
- OpenJDK `src/hotspot/os/linux/os_linux.cpp` — `ThreadPriorityPolicy == 0`이면 우선순위 미반영
- google/sanitizers wiki "ThreadSanitizerAlgorithm" — happens-before 기반 판정 <https://github.com/google/sanitizers/wiki/ThreadSanitizerAlgorithm>
- 로컬 재현(리눅스 7.0, glibc 2.39, Node 18.19): trylock 라이브락(백오프 유무 비교), PI 뮤텍스의 `FUTEX_LOCK_PI`, Node `await` 사이 check-then-act 재고 초과 판매. 우선순위 역전은 `RLIMIT_RTPRIO=0`이라 재현하지 않음
