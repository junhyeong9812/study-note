# os/15-race-conditions — 순서가 운에 달린 코드: 임계 구역·원자성·check-then-act — 정리 (힌트)

## 해결하는 문제

기초는 원고 [process-thread §10·§11](../../foundations/process-thread/README.md)이다.\
§10은 50개 스레드가 `g_count += 1`을 해 값이 모자라는 예를, §11은 `Lock`으로 막는 법을 보인다.\
이 노트는 **왜 그런 일이 생기는지를 기계어·스케줄러 수준에서** 보고, 실무에서 같은 모양으로 나타나는 경우(check-then-act)로 넓힌다.

여러 실행 흐름이 같은 자원을 고치면, 결과가 **누가 언제 실행됐는지**에 달라진다.

```text
  기대: 두 스레드가 각각 100만 번 counter++  → 200만
  실제: 102만, 109만, 103만 ... 매번 다름        (로컬 재현, 아래)
```

쉬운 예: 공유 가계부다.
- 두 사람이 동시에 잔액 50을 본다.
- 둘 다 "50 + 1 = 51"을 계산해 적는다.
- 두 번 입금했는데 잔액은 51이다. 한 번이 사라졌다.

똑같은 구조다.\
`counter++`는 "읽고 → 더하고 → 쓰는" 세 단계다. 두 스레드의 세 단계가 섞이면 한 번이 사라진다.

실무 예:
- 조회수·좋아요 카운터가 실제보다 적게 쌓인다.
- 재고가 1개인 상품이 동시 주문 5건에 모두 팔리고 재고가 음수가 된다.
- 테스트에서는 한 번도 안 나던 버그가 운영 부하에서만 가끔 난다.

## 동작·원리

### 1. `counter++`는 명령 세 개다

로컬 재현(예시, x86-64 · gcc 13.3 `-O0`): `counter++`의 기계어.

```text
  mov    0x2e0d(%rip),%rax     # ① 메모리 → 레지스터 (읽기)
  add    $0x1,%rax             # ② 레지스터 + 1
  mov    %rax,0x2e02(%rip)     # ③ 레지스터 → 메모리 (쓰기)
```

두 스레드가 섞이면(OSTEP 26 Figure 26.7과 같은 흐름):

```text
  시간 ↓        스레드 1 (rax)          스레드 2 (rax)          counter
               ① 읽기     50                                    50
               ② +1      51                                    50
  --- 타이머 인터럽트: 스레드 1 저장, 스레드 2 실행 ---
                                       ① 읽기     50            50
                                       ② +1      51            50
                                       ③ 쓰기     51            51
  --- 다시 스레드 1 ---
               ③ 쓰기     51                                    51   ← 52여야 한다
```

- 레지스터는 스레드마다 따로다. 컨텍스트 스위치 때 저장·복원된다(07번).
- 멀티코어에서는 인터럽트 없이도 두 코어가 **정말 동시에** ①을 실행해 같은 일이 생긴다.

용어(OSTEP 26):
  - *임계 구역(critical section)*: 공유 자원에 접근하는 코드 조각이다. 동시에 둘 이상이 실행하면 안 된다.
  - *경쟁 조건(race condition)*: 결과가 실행 타이밍에 달린 상태다. 운이 나쁘면 틀린 결과가 나온다.
  - *비결정적(indeterminate)*: 실행할 때마다 결과가 다를 수 있는 프로그램이다.
  - *상호 배제(mutual exclusion)*: 한 스레드가 임계 구역에 있으면 다른 스레드는 못 들어오게 하는 성질이다.
  - *원자적(atomic)*: "한 덩어리로" 실행된다는 뜻이다. 다른 흐름이 중간 상태를 볼 수 없다.

로컬 재현(예시, 리눅스 7.0 · 24코어 · gcc 13.3 `-O0`, 스레드 2개 × 100만 번):

```text
mode=0 result=1022091 (expected 2000000)    ← counter++ (보호 없음)
mode=0 result=1093191 (expected 2000000)
mode=0 result=1035561 (expected 2000000)
mode=1 result=2000000 (expected 2000000)    ← atomic_fetch_add → 기계어 "lock addq"
mode=2 result=2000000 (expected 2000000)    ← pthread_mutex로 감쌈
```

- `atomic_fetch_add`는 x86에서 `lock` 접두사가 붙은 **한 명령**이 된다. 반환값을 안 쓰면 `lock addq`, 쓰면 `lock xadd`다(gcc 13.3 로컬 확인). `lock` 접두사가 읽기-더하기-쓰기를 다른 코어가 끼어들 수 없게 묶는다.

### 2. 테스트에서는 안 나는 이유

```text
  반복 1000번 (작다)                       반복 100만 번 (크다)
  T1: [====]                              T1: [==================...]
  T2:         [====]   ← 거의 안 겹침       T2:    [==================...]  ← 오래 겹침
```

- 스레드 하나가 금방 끝나면 두 번째 스레드가 시작하기 전에 일이 끝난다. 겹치는 시간이 없으면 경쟁도 없다.
- 로컬 재현(예시): 반복 1000번으로 200회 돌리면 194회가 정확히 2000이었다. 반복 100만 번은 3회 모두 틀렸다.
- 그래서 경쟁 조건은 "부하·코어 수·타이밍"이 바뀌는 운영 환경에서 드러난다. 재현이 안 된다고 없는 게 아니다.

> 참고: 원고 §10의 파이썬 예(50스레드 × 10만 번 `g_count += 1`)는 작성 환경의 CPython 3.12.3에서 3번 모두 정확히 5,000,000이 나왔다(로컬 재현). 그래도 `g += 1`은 `LOAD_GLOBAL → LOAD_CONST → BINARY_OP(+=) → STORE_GLOBAL` 여러 바이트코드다(`dis`로 확인). 언어가 원자성을 보장하지 않으므로 잠금이 필요하다는 원고의 결론은 그대로다. 재현이 안 되는 이유는 CPython 3.12가 GIL 양보 요청(eval breaker)을 `RESUME`·`JUMP_BACKWARD`·`CALL` 계열 명령에서만 확인하기 때문이다(CPython 3.12 `Python/bytecodes.c`의 `CHECK_EVAL_BREAKER` 위치). 이 루프에서는 `STORE_GLOBAL` 뒤 `JUMP_BACKWARD`에서만 스레드가 바뀌어 네 명령이 우연히 끊기지 않는다. 구현 세부일 뿐 보장이 아니다.

### 3. data race와 race condition은 다르다

```text
                       data race                         race condition (넓은 뜻)
  무엇                 같은 메모리에 동시 접근,              결과가 실행 순서에 달림
                       하나 이상 쓰기, 순서 보장 없음
  C/C++                정의되지 않은 동작(UB)               논리 버그
  Java                 "data race"(JLS 17.4.5)             data race가 없어도 생긴다(JLS 17.4.3)
  예                   보호 없는 counter++                 원자 연산 두 개로 만든 check-then-act,
                                                           프로세스·서버·DB 사이 경쟁
```

- C에서 두 평가가 충돌(같은 위치, 하나 이상 쓰기)하면, 둘 다 원자 연산이거나 한쪽이 다른 쪽보다 happens-before인 경우가 아닌 한 data race다. data race가 있으면 동작이 정의되지 않는다(cppreference "Memory model", C11).
- JLS는 happens-before로 순서가 없는 충돌 접근을 data race라 부른다(17.4.5). 그리고 data race가 없어도 "한 덩어리로 보여야 할 연산 묶음"이 원자적이지 않으면 오류가 난다고 적는다(17.4.3).
- 그래서 **모든 변수를 atomic으로 바꿔도** check-then-act 경쟁은 남는다.
- 용어 주의: OSTEP 26은 이 예를 "race condition(더 구체적으로는 data race)"이라 부르고, 이 장과 다음 몇 장은 data race에 집중한다고 적는다(26.4, 참고문헌 [NM92] 주석). 이 노트는 언어 명세(C·JLS)의 구분을 따른다.

### 4. check-then-act — 가장 흔한 실무 모양

```text
  if (재고 > 0) {         ← check
      재고 = 재고 - 1;     ← act
  }

  주문 A: check(1 > 0 ✓) ─────────────── act(재고=0)
  주문 B:       check(1 > 0 ✓) ─────────────────── act(재고=0 또는 -1)
                ↑ A의 act 전에 B가 check → 둘 다 통과
```

- 검사와 행동 사이에 틈이 있으면, 그 틈에 다른 흐름이 상태를 바꿀 수 있다.
- 같은 모양
  - `if (!map.containsKey(k)) map.put(k, v);` — 두 스레드가 둘 다 put한다.
  - `if (access(path, W_OK) == 0) open(path, ...)` — 검사와 열기 사이에 파일이 바뀐다(TOCTOU). access(2)는 이것을 보안 구멍이라 적는다.
  - "없으면 INSERT" — 두 요청이 둘 다 "없음"을 보고 중복 행을 넣는다.
  - 싱글 스레드 Node.js에서도 `await` 사이에서 생긴다(아래 재현).

  - *TOCTOU(Time Of Check to Time Of Use)*: 검사한 시점과 쓰는 시점이 달라 생기는 경쟁이다.

로컬 재현(예시, Node.js v18.19.1): 재고 1개, 동시 주문 5건. 읽기와 쓰기가 각각 `await`다.

```js
async function order(id) {
  const s = await db.read();       // check
  if (s > 0) {
    await db.write(s - 1);         // act — 이 await 동안 다른 주문이 끼어든다
    return `order ${id}: OK`;
  }
  return `order ${id}: SOLD OUT`;
}
// 결과: order 1~5 모두 OK, stock = 0   ← 1개를 5번 팔았다
```

- 이벤트 루프는 한 번에 콜백 하나만 실행한다. 대신 `await`마다 다른 작업이 끼어든다. 두 `await` 사이가 곧 틈이다.

## 쓰이는 자료구조·알고리즘

- 이 주제의 핵심은 자료구조보다 **원자성 경계**를 어디에 긋는가다(커리큘럼 🔧 칸도 비어 있다).
- **원자적 read-modify-write** — `lock add`, compare-and-swap(CAS). 16번 락의 재료다.
- **상호 배제 락** — 임계 구역을 한 번에 하나만. 16번(뮤텍스·스핀락), 18번 세마포어([18-semaphores](../18-semaphores/2-summary.md)).
- **조건부 갱신(compare-and-set)** — "기대값이 맞을 때만 바꾼다". CAS, SQL `UPDATE ... WHERE qty > 0`, HTTP `If-Match`가 같은 발상이다.
- **동시성 안전 맵** — `ConcurrentHashMap.putIfAbsent`는 "없으면 넣기"를 원자적으로 한다(Java SE 문서).

## 적용 — 풀어나가는 법

### 1. 경계를 찾는다: "무엇이 한 덩어리여야 하나"

1. 공유 상태를 적는다(필드, 전역 변수, 파일, DB 행, 캐시 키).
2. 그 상태를 **읽고 판단해 쓰는** 코드 경로를 찾는다. 그것이 임계 구역 후보다.
3. 한 덩어리로 만든다. 방법은 아래 셋 중 하나다.

| 방법 | 언제 | 예 |
|---|---|---|
| 원자 연산 | 변수 하나를 고칠 때 | `AtomicLong.incrementAndGet()`, C `atomic_fetch_add` |
| 락으로 묶기 | 여러 변수·여러 단계를 함께 | `synchronized`, `ReentrantLock`, `pthread_mutex` |
| 저장소에 위임 | 상태가 DB·파일에 있을 때 | 조건부 UPDATE, 유니크 제약, `O_CREAT|O_EXCL` |

### 2. 코드로

```java
// 틀림: count++ 는 읽기-더하기-쓰기
private long count;
void hit() { count++; }

// 맞음 1: 원자 연산
private final AtomicLong count = new AtomicLong();
void hit() { count.incrementAndGet(); }

// 틀림: check-then-act (각 호출은 스레드 안전해도 묶음은 아님)
if (!map.containsKey(k)) map.put(k, create());

// 맞음 2: 원자적 "없으면 넣기"
map.putIfAbsent(k, v);                  // ConcurrentHashMap: 동작 전체가 원자적
map.computeIfAbsent(k, key -> create());
```

```sql
-- 틀림: 앱에서 읽고 판단한 뒤 쓴다
SELECT qty FROM stock WHERE id = 1;           -- 1
UPDATE stock SET qty = 0 WHERE id = 1;         -- 둘 다 이걸 실행

-- 맞음: 검사와 행동을 한 문장에. 영향받은 행 수로 성공 여부를 안다
UPDATE stock SET qty = qty - 1 WHERE id = 1 AND qty > 0;   -- 1 row → 성공, 0 row → 품절
```

- PostgreSQL READ COMMITTED에서 두 번째 UPDATE는 첫 번째의 커밋을 기다린 뒤, **갱신된 행으로 WHERE를 다시 평가**한다(PostgreSQL 문서 13.2.1). 그래서 `qty > 0`이 두 번째 요청을 막는다.

```c
/* 파일 "없으면 만들기"를 원자적으로 — 이미 있으면 EEXIST */
int fd = open("lockfile", O_WRONLY | O_CREAT | O_EXCL, 0600);
if (fd < 0 && errno == EEXIST) { /* 다른 프로세스가 먼저 만들었다 */ }
```

- `O_CREAT|O_EXCL`은 "이 호출이 파일을 만든다"를 보장한다. 이미 있으면 `EEXIST`로 실패한다(open(2)). `access` 뒤 `open`하는 대신 이렇게 한다.
- 예외: NFS에서는 NFSv3 이상·커널 2.6 이상에서만 `O_EXCL`이 지원된다. 지원이 없는 NFS에서 이 방식의 lockfile은 경쟁이 남는다. open(2)는 대안으로 고유한 임시 파일을 만들고 `link(2)`로 lockfile에 연결하는 방법을 적는다.

### 3. 도구로 찾는다

```bash
# ThreadSanitizer: 실행 중 data race를 잡는다 (C/C++)
gcc -O1 -g -fsanitize=thread -pthread counter.c -o counter_tsan && ./counter_tsan 0
```

로컬 재현(예시, gcc 13.3):

```text
WARNING: ThreadSanitizer: data race (pid=...)
  Read of size 8 at 0x... by thread T2:
    #0 worker counter.c:12
  Previous write of size 8 at 0x... by thread T1:
    #0 worker counter.c:12
  Location is global 'counter' of size 8 at ...
SUMMARY: ThreadSanitizer: data race counter.c:12 in worker
```

- TSan은 **data race**를 잡는다. 원자 연산으로 만든 check-then-act 같은 **논리적 경쟁**은 못 잡는다. 그것은 설계 리뷰와 동시성 테스트(반복·지연 주입)로 찾는다.
- 재현 요령: 반복 횟수와 스레드 수를 늘린다. check와 act 사이에 인위적 지연(`sleep`)을 넣으면 틈이 넓어져 거의 항상 재현된다.

## 장애 시나리오와 대처

### 1. `count++` 유실

- **현상**: 조회수·처리 건수 카운터가 실제(로그 건수)보다 적다. 차이가 부하에 비례해 커진다.
- **보이는 형태**: 에러·예외는 없다. 합계가 안 맞는 대사(reconciliation) 결과만 남는다.
- **원인**: 여러 스레드가 보호 없는 `count++`를 했다. 읽기-더하기-쓰기가 섞여 증가분이 사라졌다.
- **대처**
  - 원자 연산(`AtomicLong`, `LongAdder`)이나 락으로 바꾼다.
  - C/C++는 TSan으로 같은 종류의 data race를 전수 확인한다.
  - 여러 서버에 걸친 카운터면 저장소의 원자 연산(DB `SET c = c + 1`, Redis `INCR`)을 쓴다.

### 2. 재고 음수 / 초과 판매

- **현상**: 재고 1개에 주문이 여러 건 승인된다. 재고 값이 음수가 된다.
- **보이는 형태**: 주문 테이블 합계 > 입고량. 재고 컬럼에 `-1`, `-2`. 동시에 들어온 요청들의 타임스탬프가 수 ms 안에 몰려 있다.
- **원인**: 애플리케이션이 재고를 **읽고(check) 판단한 뒤 쓴다(act)**. 두 요청이 둘 다 "1개 남음"을 봤다. 여러 서버·여러 스레드·Node의 `await` 사이 어디서든 생긴다.
- **대처**
  - 검사와 차감을 한 문장으로: `UPDATE ... SET qty = qty - 1 WHERE id = ? AND qty > 0`, 영향 행 수로 성공 판정.
  - DB 제약으로 막는다: `CHECK (qty >= 0)`.
  - 행 잠금(`SELECT ... FOR UPDATE`)이나 버전 컬럼(낙관적 잠금)으로 묶는다(database/13).

### 3. 테스트에선 안 나고 부하에서만

- **현상**: 단위 테스트·스테이징은 늘 통과한다. 운영의 피크 시간에만 가끔 값이 틀리거나 중복 처리가 생긴다.
- **보이는 형태**: 재현 요청이 "가끔", "특정 시간대", "서버 증설 뒤"에 몰린다. 코어 수·인스턴스 수를 늘린 뒤 빈도가 오른다.
- **원인**: 테스트는 스레드가 거의 겹치지 않는다. 로컬 재현에서도 반복 1000번은 200번 중 194번 정답, 100만 번은 3번 모두 오답이었다. 겹침이 커야 틈이 드러난다.
- **대처**
  - 동시성 테스트를 따로 둔다: 많은 스레드, 많은 반복, `CountDownLatch`로 동시 출발, check와 act 사이 지연 주입(testing/10).
  - TSan·코드 리뷰로 "공유 상태를 읽고 판단해 쓰는 곳"을 목록으로 만든다.
  - 재현이 안 된다고 닫지 않는다. 경쟁은 확률 문제다.

### 4. 중복 생성 ("없으면 만들기")

- **현상**: 같은 사용자·같은 주문번호 행이 두 개 생긴다. 초기화 코드가 두 번 돈다.
- **보이는 형태**: 유니크해야 할 키의 중복 행, 싱글턴·캐시 항목이 두 번 생성된 로그.
- **원인**: "있나 확인 → 없으면 생성"이 두 흐름에서 동시에 "없음"을 봤다.
- **대처**: 유니크 제약 + 충돌 처리(`INSERT ... ON CONFLICT`), `putIfAbsent`/`computeIfAbsent`, 파일은 `O_CREAT|O_EXCL`(오래된 NFS 제외). 확인과 생성을 **한 원자 연산**으로 만든다.

## 핵심 문장

- `counter++`는 읽기·더하기·쓰기 세 명령이다. 그 사이에 다른 스레드가 끼어들면 증가가 사라진다.
- 임계 구역은 공유 자원을 다루는 코드이고, 상호 배제는 거기에 한 번에 하나만 들어가게 하는 성질이다.
- data race(보호 없는 동시 접근, C에서는 UB)와 race condition(결과가 순서에 달림)은 다르다. 모든 변수를 atomic으로 바꿔도 check-then-act 경쟁은 남는다.
- check-then-act는 검사와 행동 사이의 틈이 문제다. 조건부 UPDATE, `putIfAbsent`, `O_EXCL`처럼 검사와 행동을 한 원자 연산으로 합친다.
- 경쟁은 겹침이 클 때만 드러난다. 테스트 통과는 경쟁이 없다는 증거가 아니다.

## 관련 주제·근거

- 원고: [foundations/process-thread](../../foundations/process-thread/README.md) — §10 경쟁 조건, §11 상호 배제와 Lock, §12 GIL
- 선행: [07-threads-and-context-switch](../07-threads-and-context-switch/2-summary.md) — 스레드·레지스터 저장·컨텍스트 스위치
- 후속·연결
  - [16-locks-and-spinlocks](../16-locks-and-spinlocks/2-summary.md) — test-and-set·CAS·futex
  - [17-condition-variables-and-monitors](../17-condition-variables-and-monitors/2-summary.md) — 대기/통지
  - [18-semaphores](../18-semaphores/2-summary.md) — 카운팅 세마포어
  - [27-event-based-concurrency](../27-event-based-concurrency/2-summary.md) — 이벤트 루프(`await` 사이의 경쟁)
  - [19-deadlock](../19-deadlock/2-summary.md), [20-concurrency-bugs](../20-concurrency-bugs/2-summary.md)(원자성 위반·순서 위반)
  - [systems/semaphore](../../systems/semaphore/2-summary.md) — 기존 세마포어 초안
  - [database/13-transactions-acid](../../database/13-transactions-acid/2-summary.md)(원자성·격리)
  - [testing/10-testing-time-and-concurrency](../../testing/10-testing-time-and-concurrency/2-summary.md)
- 교재
  - OSTEP 26 "Concurrency: An Introduction" — 26.4 `counter` 기계어와 Figure 26.7, 임계 구역·경쟁 조건·비결정성·상호 배제 정의 <https://pages.cs.wisc.edu/~remzi/OSTEP/threads-intro.pdf>
- 언어 명세
  - cppreference, C "Memory model" — 충돌 평가, data race → 정의되지 않은 동작 <https://en.cppreference.com/w/c/language/memory_model>
  - JLS 21 17.4.3(데이터 경쟁 없음과 원자성 오류), 17.4.5(data race 정의) <https://docs.oracle.com/javase/specs/jls/se21/html/jls-17.html>
- man: access(2) — 검사 후 open은 보안 구멍, open(2) — `O_CREAT|O_EXCL`·`EEXIST`
- PostgreSQL 문서 13.2.1 Read Committed — 동시 UPDATE 뒤 WHERE 재평가 <https://www.postgresql.org/docs/current/transaction-iso.html>
- CPython 3.12 `Python/bytecodes.c` — `CHECK_EVAL_BREAKER()`가 `JUMP_BACKWARD`·`CALL` 계열에 있음 <https://github.com/python/cpython/blob/3.12/Python/bytecodes.c>
- Java SE 21 `ConcurrentHashMap` — `putIfAbsent` 등 "the action is performed atomically" <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/ConcurrentHashMap.html>
- 로컬 재현(리눅스 7.0 · gcc 13.3 · 24코어): C `counter++` 유실과 `lock addq`·mutex 정답, `objdump`로 mov/add/mov 확인, 반복 1000번 vs 100만 번 재현율, ThreadSanitizer 보고, CPython 3.12.3 원고 예 재실행과 `dis`, Node.js v18 `await` 사이 재고 초과 판매
