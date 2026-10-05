# data-structure/29-concurrent-data-structures — 동시 자료구조: 락 기반·lock-free 큐와 해시맵, ABA — 정리 (힌트)

## 해결하는 문제

여러 스레드가 한 자료구조를 같이 고친다. 한 줄짜리 `map.put`도 안에서는 여러 단계다.

```text
  HashMap.put(k, v) 안쪽 (단순화)
   1. 버킷 i 를 계산
   2. table[i] 를 읽는다 (비었다)
   3. 새 노드를 만들어 table[i] 에 쓴다

  스레드 A: 2(비었다) ─────────────── 3(A 노드 씀)
  스레드 B:      2(비었다) ── 3(B 노드 씀)            ← B 의 노드가 A 에게 덮였다. 예외 없음
```

- 동시 수정을 막지 않으면 결과는 "느려진다"가 아니라 **틀린다.** 원소가 조용히 사라지거나, 구조가 망가져 무한 루프를 돈다.
- 해법은 세 층이다.
  1. **큰 락 하나**로 감싼다(`Collections.synchronizedMap`). 맞지만 한 번에 한 스레드다.
  2. **잘게 쪼갠 락**(버킷마다, 머리·꼬리마다)으로 동시에 들어갈 수 있게 한다.
  3. **락 없이(lock-free)** CAS로 "내가 본 그대로면 바꾼다"를 반복한다.
- 3층으로 갈수록 빠를 수 있지만, 새 종류의 버그가 생긴다. 대표가 **ABA**다.

쉬운 예: 공용 화이트보드 할 일 목록.
- 큰 락 = 마커가 하나라서 한 명씩 쓴다.
- 쪼갠 락 = 칸마다 마커가 있다. 다른 칸은 동시에 쓴다.
- lock-free = 마커 없이 "내가 본 글자 그대로면 고친다". 그새 누가 지웠다가 **똑같은 글자를 다시 썼다면** 속는다(ABA).

똑같은 구조다.\
실무 예:
- 캐시용 `HashMap`을 여러 요청 스레드가 같이 쓰다가 항목이 사라지거나, CPU 하나가 100%로 멈춘다.
- `ConcurrentHashMap`으로 바꿨는데 카운터가 여전히 덜 센다(`get` 후 `put`).
- 순회 중 같은 리스트를 지우다 `ConcurrentModificationException`.

## 동작·원리

### 1. 진행 보장의 단어 — 출처마다 뜻이 다르다

```text
  블로킹(락)        한 스레드가 락을 쥔 채 멈추면(선점·페이지 폴트) 나머지도 못 나간다
  lock-free         누군가 멈춰도 "시스템 전체로는" 누군가의 연산이 유한 단계 안에 끝난다
                    (개별 스레드는 계속 CAS 에 져서 굶을 수 있다)
  wait-free         "스레드마다 각자" 상한이 정해진(bounded) 단계 안에 끝난다
```

- Michael–Scott 1996(PODC)의 용어
  - *non-blocking*: "if there are one or more active processes trying to perform operations ... some operation will complete within a finite number of time steps". 오늘날 교재가 lock-free라 부르는 것이 이것이다.
  - 이 논문에서 *lock-free*는 "락 메커니즘을 쓰지 않는다"는 뜻으로 쓰인다. 그래서 "lock-free but not non-blocking"(락은 없지만 느린 프로세스가 다른 프로세스를 무한정 막을 수 있는) 알고리즘이 있다고 적는다.
  - *wait-free*: "both non-blocking and starvation free" — "every active process will make progress within a bounded number of time steps"(각주 2).
    - 흔한 오해: "lock-free면 더 빠르다." 진행 **보장**에 대한 말이지 처리량에 대한 말이 아니다. 아래 처리량 실험에서도 이 환경에서는 락 기반 `ArrayBlockingQueue`가 가장 빨랐다.
- 이 노트는 오늘날 용법(lock-free = 시스템 진행 보장)을 따르고, 논문 인용에서는 논문 용어를 그대로 둔다.
- CAS 자체와 스핀락은 [os/16-locks-and-spinlocks](../../os/16-locks-and-spinlocks/2-summary.md)에서 다뤘다.
  - *CAS(compare-and-swap)*: "주소의 값이 기대값과 같으면 새 값으로 바꾸고 성공을, 다르면 실패를 알린다"를 원자적으로 하는 명령.

### 2. 락 기반 — 큰 락에서 쪼갠 락으로

```text
  (a) 큰 락 하나                 (b) 머리·꼬리 락 두 개 (Michael–Scott two-lock queue)
  ┌─lock─────────────────┐       headLock          tailLock
  │ head → [n1]→[n2]→[n3]│       head → [dummy]→[n1]→[n2] ← tail
  └──────────────────────┘        꺼내기는 headLock 만, 넣기는 tailLock 만
  넣기·꺼내기가 서로 막는다        dummy 노드 덕에 둘이 같은 노드를 안 건드린다
```

- OSTEP 29장: 동시 큐는 큰 락이 표준 방법이고, Michael–Scott 큐는 머리와 꼬리에 락을 하나씩 두어 enqueue와 dequeue가 동시에 진행되게 한다. dummy 노드가 머리·꼬리 연산을 분리한다.
- Java `LinkedBlockingQueue`가 이 모양이다. 소스 주석: "A variant of the 'two lock queue' algorithm", `putLock`·`takeLock`.
- 반대로 `ArrayBlockingQueue`는 락 하나(`ReentrantLock`) + 조건 변수 두 개다([25-ring-buffer](../25-ring-buffer/2-summary.md)).
- OSTEP 29.2: 노드마다 락을 잡고 넘어가는 *hand-over-hand locking*은 개념상 동시성이 높지만, 노드마다 락을 잡고 놓는 비용 때문에 큰 락 하나보다 빠르게 만들기 어렵다고 적는다. **잘게 쪼갠다고 빨라지지 않는다.** 재 봐야 한다.

### 3. `ConcurrentHashMap`(OpenJDK 21) — 빈 버킷은 CAS, 찬 버킷은 그 버킷만 잠근다

```text
  table:  [0]   [1]        [2]   [3]          [4] ...
          null  n1→n2      null  TreeBin       ForwardingNode(리사이즈 중)
           │     │                │                │
   put →  CAS   synchronized(n1)  synchronized     helpTransfer: 옮기는 일을 거든다
          (락 없음) 버킷 하나만 잠금  (트리 버킷)
  get  →  락 없이 읽는다 (volatile 읽기)
  size →  baseCount + CounterCell[] 합 (LongAdder 방식, 쓰기 경합을 칸으로 분산)
```

- 소스 주석(OpenJDK 21u `ConcurrentHashMap.java`)
  - 빈 버킷에 첫 노드 넣기는 "just CASing it to the bin". 대부분의 `put`이 이 경우다.
  - 그 외 갱신은 락이 필요하다. 버킷마다 락 객체를 두는 대신 **버킷의 첫 노드를 `synchronized` 모니터로** 쓴다.
  - 무작위 해시에서 서로 다른 원소에 접근하는 두 스레드의 락 경합 확률은 대략 "1 / (8 * #elements)".
  - 버킷 노드가 임계(`TREEIFY_THRESHOLD` 8, 표 크기 `MIN_TREEIFY_CAPACITY` 64 이상)를 넘으면 레드블랙 트리(`TreeBin`)로 바꾼다.
  - 옛 판(Java 7까지)의 `Segment` 구조는 직렬화 호환용으로만 남았다(주석: unused "Segment" class).
- 계약
  - 키·값에 `null`을 허용하지 않는다(Javadoc). `get`이 `null`이면 "없음" 하나로만 읽히게 하려는 것으로 해석한다(Javadoc에 이유는 적혀 있지 않다).
  - 조회는 락을 잡지 않고, 시작 시점에 **완료된** 갱신을 본다. 반복자는 *weakly consistent* — `ConcurrentModificationException`을 던지지 않고, 생성 이후 변경을 반영할 수도 안 할 수도 있다.
  - `compute*`·`merge`는 원자적이다. 대신 그동안 같은 버킷의 다른 갱신이 막히므로 함수는 "short and simple"이어야 하고, 계산 중 같은 맵을 고치면 안 된다. 어기면 `IllegalStateException: Recursive update`가 날 수 있다(소스).

#### 실험: 비동기화 `HashMap` 동시 `put`, `ConcurrentHashMap` 복합 연산 (`HashMapRace.java`)

스레드 4개가 서로 다른 정수 키 10만 개씩 넣었다(기대 크기 40만). 10초 안에 안 끝나면 그 스레드의 스택 맨 위 3줄을 찍는다.

핵심 코드:

```java
for (int t = 0; t < 4; t++) {
    int base = t * 100_000;
    threads[t] = new Thread(() -> { for (int i = 0; i < 100_000; i++) m.put(base + i, i); });
    threads[t].setDaemon(true);                 // 멈춰도 JVM 이 끝나게
}
// 시작 후 각 스레드 join(10_000); 살아 있으면 t.getStackTrace() 상단 3줄 출력
// 카운터: m.put("hits", m.get("hits") + 1)  vs  m.merge("hits", 1, Integer::sum)
```

(실험, eclipse-temurin:21-jdk = OpenJDK 21.0.12, docker `--cpus=2`, 2회 실행 × HashMap 8번, 2026-10-05)

```text
== 스레드 4개가 서로 다른 키 100000개씩 put (기대 size=400000)
HashMap           run1: size=187894
HashMap           run2: size=228614
HashMap           run3: size=343794
HashMap           run4: size=265971
HashMap           run5: size=161080
HashMap           run6: size=294180
HashMap           run7: size=282835
HashMap           run8: 10초 안에 안 끝남(멈춤), 그 스레드 스택 상단:
      at java.base/java.util.HashMap$TreeNode.root(HashMap.java:1983)
      at java.base/java.util.HashMap$TreeNode.putTreeVal(HashMap.java:2137)
      at java.base/java.util.HashMap.putVal(HashMap.java:644)
ConcurrentHashMap run1: size=400000
ConcurrentHashMap run2: size=400000
== ConcurrentHashMap 카운터: 스레드 4개 x 10만 번 +1 (기대 400000)
get+put 결과=147230
merge   결과=400000
```

- 이보다 앞선 예비 실행(같은 코드, HashMap 5번, 스택 출력 없음)에서도 1번 멈췄고 `get+put` 카운터는 144147이었다.
- 사실 점검 재실행(같은 코드·환경, HashMap 8번): 1번(run4)이 위와 같은 `TreeNode.root` ← `putTreeVal` ← `putVal` 스택에서 멈췄다. 나머지 7번은 크기 155373~306924. `ConcurrentHashMap`은 두 번 다 400000. `get+put` 카운터 179923, `merge` 400000.
- 두 번째 실행에서는 HashMap 8번 중 1번이 `HashMap$TreeNode.balanceInsertion` ← `treeify` ← `split`(리사이즈 중 트리 분할)에서 멈췄다. 나머지 7번은 크기 207228~334945. `get+put` 카운터는 167682.
- 관찰
  - 비동기화 `HashMap`은 예외 없이 `size()`가 기대보다 작았다(15만~34만, 기대 40만). `size`도 경합하는 `++size`라 이것만으로는 키 유실을 단정할 수 없어, 판정 단계에서 키마다 `containsKey`로 다시 셌다(8회, 같은 환경): 실제 조회되는 키 255379~394417개로 모두 40만보다 적었고, `size()`와도 어긋났다(예: `size()=191403`, 조회되는 키 394417). 키도 실제로 사라진다. 집필 16번 중 2번, 점검 8번 중 1번은 **끝나지 않았다.** 스택이 `TreeNode` 순회에 머물러 있다. 망가진 트리를 도는 무한 루프로 보인다(해석 — 루프 자체를 추적하지는 않았다).
    - 키가 서로 다른 정수라 정상이라면 트리화될 만큼 충돌하지 않는다. 경합으로 구조가 망가진 결과로 해석한다.
  - `ConcurrentHashMap`은 크기가 정확했다. 그러나 `m.put(k, m.get(k) + 1)`은 `get`과 `put` 사이에 다른 스레드가 끼어 14만~18만만 셌다(4회). `merge`는 40만.
  - JDK 7의 `HashMap` 리사이즈 중 연결 리스트 순환은 [02-linked-list](../02-linked-list/2-summary.md) 장애 2에서 다룬다. JDK 21에서도 형태만 바뀌어 멈출 수 있음을 이 실험이 보인다.

### 4. lock-free 큐·스택 — CAS 재시도

```text
  Treiber 스택의 pop (락 없음)
   loop:
     old  = top            ← 읽기
     next = old.next
     if CAS(top, old, next): return old     ← "top 이 아직 old 면 next 로"
     else: 다시 loop (누가 먼저 바꿨다)

  Michael–Scott 큐의 enqueue (개념)
   1. 새 노드 n
   2. t = tail, nx = t.next
   3. nx == null 이면 CAS(t.next, null, n) 시도 → 성공하면 CAS(tail, t, n)
      nx != null 이면 tail 이 뒤처진 것 → CAS(tail, t, nx) 로 "도와서" 밀고 다시
```

- 실패한 스레드는 다시 읽고 재시도한다. 누군가의 CAS는 성공했으므로 시스템은 진행한다(lock-free). 특정 스레드가 계속 질 수는 있다(wait-free 아님).
- Java `ConcurrentLinkedQueue`: Javadoc이 Michael–Scott 1996 논문 기반의 non-blocking 알고리즘이라고 밝힌다. `size()`는 "NOT a constant-time operation"이다(원소를 순회해 센다).
- 작업 훔치기 deque: `ForkJoinPool`의 작업 큐는 주인 스레드만 한쪽 끝에서 push·pop하고, 다른 스레드는 반대쪽에서 poll(훔치기)한다. 소스 주석은 설계가 Chase–Lev 2005 "Dynamic Circular Work-Stealing Deque"와 "roughly similar"하다고 적는다(주로 GC 요구 때문에 다르다고 덧붙인다).

### 5. ABA — 값은 같은데 세상은 바뀌었다

```text
  스택: top → A → B → C

  T1: old=A, next=B 를 읽음 ......(멈춤)....................... CAS(top, A, B) 성공!
  T2:            pop A, pop B(반납), push A(같은 노드 재사용)
                 이제 top → A → C,  B 는 반납됨

  T1 의 CAS 는 "top 이 A 인가?"만 본다 → 예 → top = B (이미 반납된 노드)
  결과: top → B,  C 는 사라짐
```

- Michael–Scott 1996: 읽은 값 A가 CAS 전에 "A에서 B로, 다시 A로" 바뀌면 CAS가 성공하지 말아야 할 때 성공한다.
- 흔한 해법: 포인터에 **수정 카운터(stamp)** 를 붙여 함께 비교한다. 논문은 이것이 ABA를 "extremely unlikely"하게 만들 뿐 보장하지는 않는다고 적는다(카운터가 한 바퀴 돌 수 있다). 2배 폭 CAS나, 포인터 대신 배열 인덱스 + 카운터를 한 워드에 담는 방법이 필요하다.
- **GC 언어에서는 노드 재사용이 없으면 ABA가 생기지 않는다.** T1이 A의 참조를 쥐고 있는 동안 A는 수거되지 않으므로, 새로 만든 노드가 같은 참조일 수 없다. `ConcurrentLinkedQueue` 소스 주석: "in garbage collected systems, there is no possibility of ABA problems due to recycled nodes, so there is no need to use 'counted pointers'".
- 그러므로 Java에서 ABA가 생기는 조건은 노드를 **직접 풀링해 재사용**하거나, 정수 값 자체를 CAS하는 경우다. C·C++에서는 `free` 뒤 `malloc`이 같은 주소를 돌려줄 수 있어 기본으로 위험하다.

#### 실험: ABA 재현 — 노드 재사용 vs 새 노드 vs stamp (`Aba.java`)

래치로 위 시간축을 그대로 만들었다. T1은 `old=A, next=B`를 읽고 기다리고, 그동안 메인 스레드(T2)가 A·B를 꺼내고 A를 다시 넣는다.

(실험, OpenJDK 21.0.12, docker `--cpus=2`, 2026-10-05)

```text
== 1. AtomicReference + 노드 재사용(풀)
  T2 뒤 스택: A->C   (B 는 이미 꺼내 반납한 노드)
  T1 CAS(top: A -> B) = true  (꺼낸 값 A)
  최종 스택: B   ← 반납된 B가 top, C가 사라졌다
== 2. AtomicReference + 매번 새 노드(GC가 재사용을 막는다)
  T2 뒤 스택: A'->C   (B 는 이미 꺼내 반납한 노드)
  T1 CAS(top: A -> B) = false
  최종 스택: A'->C
== 3. AtomicStampedReference + 노드 재사용
  T2 뒤 스택: A->C stamp=3
  T1 CAS(top: A@0 -> B) = false  현재 stamp=3
  T1 재시도 pop = A
  최종 스택: C
```

- 핵심 코드

```java
// T1: 읽고 멈춘다
Node old = top.get(); Node next = old.next;          // A, B
t1Read.countDown(); t2Done.await();
boolean ok = top.compareAndSet(old, next);           // "top == A ?" 만 본다

// stamp 판: 참조와 stamp 를 함께 비교
int[] st = new int[1]; Node old = top.get(st); int s0 = st[0];
Node next = old.next;                                // 멈추기 전에 읽어 둔 B
boolean ok = top.compareAndSet(old, next, s0, s0 + 1);
```

- 관찰
  - 1번: CAS가 성공해 이미 반납한 B가 top이 됐고 C가 사라졌다. 예외는 없다. "조용한 손상"이다.
  - 2번: 새 노드 A'는 다른 참조라 CAS가 실패했다. 실제 pop 루프라면 다시 읽고 재시도한다.
  - 3번: 같은 노드를 재사용했지만 stamp가 0 → 3으로 바뀌어 CAS가 실패했고, 재시도로 A를 꺼내 최종 `C`가 됐다.
  - `AtomicStampedReference`는 [참조, int] 쌍을 매번 내부 객체로 만들어 교체한다(Javadoc "Implementation note"). 갱신마다 할당이 생긴다.

#### 실험: C에서 주소 재사용 (`reuse.c`)

```c
struct node *seen = atomic_load(&top);            // 스레드 1이 읽어 둔 A 주소
free(a);                                           // 스레드 2: A를 pop 해서 free
struct node *a2 = malloc(sizeof *a2); a2->v = 99;  // 새 노드 → 같은 주소일 수 있다
atomic_store(&top, a2);
int ok = atomic_compare_exchange_strong(&top, &expected /* = seen */, NULL);
```

(실험, 호스트 gcc 13.3.0 `-std=c11 -O2`, glibc 2.39, 2026-10-05, 단일 스레드로 순서를 흉내 냄)

```text
old A=0x5f3d008f12a0  new node=0x5f3d008f12a0  same=1
CAS(top: old A -> NULL) = 1  (값은 v=99 인 다른 노드였다)
```

- glibc에서 같은 크기의 `free` 직후 `malloc`이 같은 주소를 돌려줬고, 옛 주소로 한 CAS가 성공했다. 주소 값은 실행마다 다르다.
- C 표준에서 `free`된 포인터 값을 쓰는 것(비교 포함) 자체가 정의되지 않은 동작이다. 이 실험은 그 위험이 실제 할당기에서 어떻게 보이는지만 관찰한 것이다. C의 lock-free 구조는 hazard pointer·epoch 기반 회수 같은 **안전한 메모리 회수**가 필요하다 [?] (이 노트에서 자세히 다루지 않음).

### 6. 순회 중 수정 — `ConcurrentModificationException`은 최선 노력이다

#### 실험: 리스트 순회 중 삭제 (`Cme.java`)

(실험, OpenJDK 21.0.12, 2026-10-05)

```text
b 삭제: java.util.ConcurrentModificationException
c(끝에서 두 번째) 삭제: 예외 없음 [a, b, d]  ← d 는 검사도 안 됐다
removeIf: [a, c, d]
```

- 단일 스레드에서도 난다. "Concurrent"는 스레드가 아니라 "순회와 수정이 겹쳤다"는 뜻이다.
- 끝에서 두 번째 원소를 지우면 크기가 줄어 `hasNext()`가 `false`가 되고, 검사 지점(`next()`)에 닿지 않는다. 예외 없이 마지막 원소를 건너뛴다.
- `ArrayList` Javadoc: fail-fast 동작은 "cannot be guaranteed", 예외는 "on a best-effort basis"로 던진다. 프로그램 정확성을 이 예외에 기대면 안 되고 버그 탐지용으로만 쓰라고 적는다.

### 7. 실험: 큐 처리량 — 락 vs lock-free (`QueueThroughput.java`)

생산자 2·소비자 2, 정수 400만 개. 비교한 네 가지는 `synchronized` 메서드 + `wait/notifyAll`로 감싼 무제한 `ArrayDeque`, `LinkedBlockingQueue`(무제한), `ArrayBlockingQueue(1024)`, `ConcurrentLinkedQueue`(`poll`이 `null`이면 `Thread.onSpinWait()` 후 재시도)다. 소비한 값의 합으로 유실이 없음을 확인했다.

(실험, OpenJDK 21.0.12, docker `--cpus=2`(스레드 4개 > CPU 2개), 3라운드 × 3회, 2026-10-05)

```text
producers=2 consumers=2 total=4000000 availableProcessors=2
round 1: synchronized ArrayDeque  7533 ms | LinkedBlockingQueue  6516 ms | ArrayBlockingQueue(1024)  1323 ms | ConcurrentLinkedQueue(스핀 poll)  3416 ms
round 2: synchronized ArrayDeque  6298 ms | LinkedBlockingQueue  6014 ms | ArrayBlockingQueue(1024)  1158 ms | ConcurrentLinkedQueue(스핀 poll)  3844 ms
round 3: synchronized ArrayDeque  6817 ms | LinkedBlockingQueue  6038 ms | ArrayBlockingQueue(1024)  1122 ms | ConcurrentLinkedQueue(스핀 poll)  3284 ms
```

- 3회(9라운드) 범위: `synchronized ArrayDeque`(+ `wait/notifyAll`) 5977~7848 ms, `LinkedBlockingQueue` 4979~6946 ms, `ArrayBlockingQueue(1024)` 1044~1327 ms, `ConcurrentLinkedQueue` 2806~3844 ms. 3회째에 각 라운드 GC 시간을 함께 쟀고 0~33 ms였다.
- 사실 점검 재실행(1회 × 3라운드): `synchronized ArrayDeque` 6727~7997 ms, `LinkedBlockingQueue` 5308~5599 ms, `ArrayBlockingQueue(1024)` 1091~1374 ms, `ConcurrentLinkedQueue` 3293~3697 ms, GC 0~30 ms. 순서는 같았다. 4회(12라운드)를 합친 범위는 `synchronized ArrayDeque` 5977~7997 ms, `ArrayBlockingQueue(1024)` 1044~1374 ms다.
- 관찰과 해석
  - 이 환경에서는 lock-free `ConcurrentLinkedQueue`가 락 기반 `ArrayBlockingQueue`보다 2~3배 느렸다. "lock-free = 빠르다"가 아니다.
  - `ArrayBlockingQueue`만 크기 제한(1024)이 있다. 생산자가 앞서 가면 막히므로 큐가 작게 유지된다. 무제한 큐 셋은 생산자가 앞서 가며 노드를 쌓는다. GC 시간은 작았으므로 GC 탓은 아니다. 정확한 원인(캐시 지역성·잠들기/깨우기 횟수 등)은 분석하지 않았다 [?].
  - CPU 2개에 스레드 4개라 스핀하는 소비자가 생산자의 CPU 시간을 뺏는다. 코어가 많은 환경에서는 순위가 바뀔 수 있다.

## 쓰이는 자료구조·알고리즘

- 이 주제가 쓰는 하위 구조
  - 해시맵([05-hashmap](../05-hashmap/2-summary.md)) — 버킷·리사이즈·트리화. `ConcurrentHashMap`은 그 위에 버킷 단위 동기화를 얹었다.
  - 연결 리스트([02-linked-list](../02-linked-list/2-summary.md)) — Michael–Scott 큐, Treiber 스택. 레드블랙 트리([16-red-black-tree](../16-red-black-tree/2-summary.md)) — `TreeBin`.
  - 링 버퍼([25-ring-buffer](../25-ring-buffer/2-summary.md)) — `ArrayBlockingQueue`, SPSC 링, 작업 훔치기 원형 deque.
  - 스킵 리스트([12-skip-list](../12-skip-list/2-summary.md)) — `ConcurrentSkipListMap`, 정렬된 동시 맵.
  - 원자 명령(CAS·fetch-and-add)과 락([os/16](../../os/16-locks-and-spinlocks/2-summary.md)), 조건 변수([os/17](../../os/17-condition-variables-and-monitors/2-summary.md)).
- 이 주제를 쓰는 곳(🔧)
  - `ConcurrentHashMap` — 공유 캐시, 세션 저장소, 카운터 맵(`computeIfAbsent(k, x -> new LongAdder()).increment()` — Javadoc 예).
  - 작업 훔치기 deque — `ForkJoinPool`, 병렬 스트림.
  - `ConcurrentLinkedQueue`·`LinkedBlockingQueue`·`ArrayBlockingQueue` — 스레드 풀 작업 큐, 이벤트 전달.
  - 타이머 큐([26-timer-structures](../26-timer-structures/2-summary.md)) — 여러 스레드가 등록·취소한다.
  - DB 인덱스 래치([database/53-index-concurrency-control](../../database/53-index-concurrency-control/2-summary.md)) — B-tree 래치 크래빙은 hand-over-hand와 같은 생각이다.

## 적용 — 풀어나가는 법

### 1. 고르는 순서

```text
  공유가 꼭 필요한가? ── 아니오 ──> 스레드마다 따로(ThreadLocal·지역 변수), 끝에 합친다
          │ 예
  JDK 동시 컬렉션으로 되나? ── 예 ──> ConcurrentHashMap / BlockingQueue / ConcurrentLinkedQueue
          │ 아니오(여러 구조를 한 번에 바꿔야 한다)
  락 하나로 감싼다 ──> 측정해서 병목이면 그때 쪼갠다
  직접 lock-free 구현은 마지막. 노드 재사용·메모리 회수·ABA 를 설명할 수 있을 때만
```

### 2. 복합 연산은 맵의 원자 메서드로

```java
ConcurrentHashMap<String, Integer> hits = new ConcurrentHashMap<>();

// 틀림: get 과 put 사이에 다른 스레드가 낀다 (실험: 40만 중 14만~18만)
hits.put(key, hits.getOrDefault(key, 0) + 1);

// 맞음: 버킷 락 안에서 한 번에
hits.merge(key, 1, Integer::sum);

// 경합이 심한 카운터: 쓰기를 칸으로 분산
ConcurrentHashMap<String, LongAdder> freq = new ConcurrentHashMap<>();
freq.computeIfAbsent(key, k -> new LongAdder()).increment();
```

- `compute*`·`merge` 안의 함수는 짧게. 그 안에서 같은 맵을 고치지 않는다(`Recursive update`).

### 3. 순회 중 삭제

```java
list.removeIf(x -> x.expired());          // 단일 스레드: 반복자 대신
for (var it = list.iterator(); it.hasNext(); ) if (it.next().expired()) it.remove();
```

- 여러 스레드가 순회·수정하면 `ConcurrentHashMap`·`CopyOnWriteArrayList`(읽기 많고 쓰기 적을 때) 같은 weakly consistent·스냅샷 반복자를 쓰는 컬렉션으로 바꾼다.

### 4. lock-free를 직접 쓸 때

- Java: 노드를 풀링하지 않는다. 풀링해야 하면 `AtomicStampedReference`(또는 버전 필드)로 ABA를 막는다. stamp(`int`)가 한 바퀴 돌면 다시 같아질 수 있으니 "사실상" 막는 것이다(5절 논문 인용).
- C·C++: `free` 직후 같은 주소가 돌아올 수 있다(5절 실험). 안전한 메모리 회수 방식이 정해지기 전에는 lock-free 구조를 쓰지 않는다.
- 테스트: 단위 테스트로는 경합을 거의 못 만든다. 래치로 인터리빙을 강제하는 재현 테스트(5절 `Aba.java` 방식)와, 여러 스레드로 개수·합을 대조하는 스트레스 테스트를 둔다. OpenJDK의 jcstress(github.com/openjdk/jcstress — "experimental harness and a suite of tests to aid the research in the correctness of concurrency support in the JVM") 같은 동시성 테스트 도구가 있다(이 노트에서 사용하지 않음).

### 5. 진단

- CPU 한 코어 100%, 처리 멈춤: `jstack <pid>`(또는 `jcmd <pid> Thread.print`)를 몇 초 간격으로 2~3번 떠서 `RUNNABLE`인 채 같은 위치에 있는 스레드를 찾는다. `HashMap$TreeNode`·`HashMap.putVal`·`getNode`에 머물면 비동기화 `HashMap` 공유를 의심한다(3절 실험 스택).
- 개수가 모자란다: 공유 컬렉션의 타입부터 본다. `ConcurrentHashMap`이면 `get` 후 `put` 패턴을 찾는다(`grep -n "put(.*get("` 같은 검색).
- `ConcurrentModificationException`: 스택의 `ArrayList$Itr.checkForComodification` 위쪽이 순회하는 코드다. 같은 반복 안에서 컬렉션을 직접 고치는지, 다른 스레드가 고치는지 본다.

## 장애 시나리오와 대처

### 1. 비동기화 `HashMap` 공유 — 유실과 멈춤

- **현상**: 캐시 항목이 가끔 사라진다. 드물게 서버 하나가 CPU 한 코어를 100% 쓰며 해당 기능이 응답하지 않는다.
- **보이는 형태**: 예외 로그 없음. 스레드 덤프에 `RUNNABLE` 스레드가 `HashMap$TreeNode.root`·`putTreeVal`·`balanceInsertion` 등에 계속 머문다(3절 실험).
- **원인**: `HashMap`은 "not synchronized"(Javadoc). 동시 `put`·리사이즈가 버킷 연결을 덮어써 원소를 잃거나, 리스트·트리 구조를 순환시켜 순회가 끝나지 않는다.
- **대처**: `ConcurrentHashMap`으로 바꾼다. 멈춘 프로세스는 재시작 외에 풀 방법이 없다. 공유 여부를 코드 리뷰 항목으로 두고, 필드로 둔 `HashMap`이 여러 스레드에서 접근되는지 찾는다.

### 2. 동시 컬렉션 위의 복합 연산 — 원자적이지 않다

- **현상**: `ConcurrentHashMap`을 썼는데 카운터·재고가 덜 줄거나 더 준다.
- **보이는 형태**: 예외 없음. 기대값과 차이(실험: 40만 중 14만~18만).
- **원인**: `get`·`put` 같은 단일 키 메서드는 각각 원자적이지만(`putAll`·`clear` 같은 묶음 연산은 Javadoc상 일부만 반영된 상태가 보일 수 있다) `get` → 계산 → `put` 사이에 다른 스레드가 끼어든다. "check-then-act".
- **대처**: 증가는 `merge`·`compute`나 `LongAdder.increment()`로 한 번에 한다. "없을 때만 넣기"는 `putIfAbsent`(이미 있으면 아무것도 안 바꾼다). 여러 키를 함께 바꿔야 하면 락으로 감싸거나 구조를 바꾼다.

### 3. `ConcurrentModificationException` — 또는 예외 없이 건너뛰기

- **현상**: 배치·순회 코드에서 간헐적 `java.util.ConcurrentModificationException`. 또는 예외는 없는데 마지막 원소가 처리되지 않았다.
- **보이는 형태**: 스택에 `ArrayList$Itr.checkForComodification`·`HashMap$HashIterator.nextNode`. 건너뛰기는 처리 건수 불일치로만 보인다(6절 실험: 끝에서 두 번째 삭제).
- **원인**: 순회 중 같은 컬렉션을 반복자 밖에서 고쳤다(단일 스레드에서도 생긴다). 다른 스레드가 고친 경우도 같다. 검사는 최선 노력이라 놓칠 수 있다.
- **대처**: `Iterator.remove`·`removeIf`. 여러 스레드면 동시 컬렉션이나 스냅샷 복사 후 순회. 예외에 기대지 말고 건수를 대조한다.

### 4. lock-free 구조의 ABA — 조용한 손상

- **현상**: 직접 만든 lock-free 스택·풀·프리 리스트에서 드물게 원소가 사라지거나, 이미 반납한 객체가 두 곳에서 쓰인다. C/C++에서는 해제된 메모리 접근으로 크래시.
- **보이는 형태**: 재현이 거의 안 된다. 부하가 높을 때만 개수가 어긋난다. C에서는 `SIGSEGV`나 AddressSanitizer의 `heap-use-after-free` 보고(사실 점검 실험: 호스트 gcc 13.3.0 `-fsanitize=address`로 해제 뒤 읽기를 하면 `ERROR: AddressSanitizer: heap-use-after-free`가 찍혔다). 단, 5절 `reuse.c`를 ASan으로 빌드하면 `same=0`·CAS 실패가 나왔다. ASan은 해제된 메모리를 격리 구역(quarantine)에 두어 바로 재사용하지 않기 때문이다(google/sanitizers wiki "AddressSanitizerAlgorithm"). 주소 재사용형 ABA는 ASan 빌드에서 오히려 재현되지 않을 수 있다.
- **원인**: CAS가 "값이 같다"만 확인한다. 그 사이 A → B → A로 바뀐 것(노드 재사용, 주소 재사용)을 못 본다(5절 실험 1번: 반납된 B가 top, C 소실).
- **대처**: Java는 노드를 재사용하지 않는다(GC가 막는다). 재사용해야 하면 stamp(`AtomicStampedReference`)·버전 카운터. C/C++은 안전한 메모리 회수 방식을 갖춘 검증된 라이브러리를 쓴다. 래치로 인터리빙을 강제하는 재현 테스트를 둔다.

## 핵심 문장

- 동시 수정을 막지 않은 자료구조는 느려지는 것이 아니라 틀린다. 비동기화 `HashMap`은 원소를 잃고, 드물게 끝나지 않는 순회에 빠진다.
- `ConcurrentHashMap`은 빈 버킷엔 CAS, 찬 버킷엔 그 첫 노드만 잠근다. `get`·`put` 같은 단일 키 메서드는 원자적이지만 `get` 후 `put`은 아니다 — `merge`·`compute`를 쓴다.
- lock-free는 "누군가는 진행한다"는 보장이지 "더 빠르다"가 아니다. 용어는 출처마다 다르다(Michael–Scott 1996은 그것을 non-blocking이라 부른다).
- CAS는 값이 같은지만 본다. 그 사이 A → B → A로 바뀌면 속는다(ABA). GC 언어에서 노드를 재사용하지 않으면 생기지 않고, 재사용하면 stamp로 막는다(stamp가 한 바퀴 돌 수 있어 사실상의 방어다).
- `ConcurrentModificationException`은 최선 노력 검사다. 예외 없이 원소를 건너뛸 수 있으니 정확성을 그 예외에 맡기지 않는다.

## 관련 주제·근거

- 선행
  - [05-hashmap](../05-hashmap/2-summary.md) — 버킷·리사이즈·트리화(커리큘럼 ds 07).
  - [os/16-locks-and-spinlocks](../../os/16-locks-and-spinlocks/2-summary.md) — CAS·스핀락·futex.
- 후속·연결
  - [os/15-race-conditions](../../os/15-race-conditions/2-summary.md), [os/17-condition-variables-and-monitors](../../os/17-condition-variables-and-monitors/2-summary.md), [os/20-concurrency-bugs](../../os/20-concurrency-bugs/2-summary.md)
  - [25-ring-buffer](../25-ring-buffer/2-summary.md) — SPSC 링, `ArrayBlockingQueue`. [26-timer-structures](../26-timer-structures/2-summary.md)
  - [02-linked-list](../02-linked-list/2-summary.md) — JDK 7 `HashMap` 리사이즈 순환. [12-skip-list](../12-skip-list/2-summary.md) — `ConcurrentSkipListMap`.
  - [database/53-index-concurrency-control](../../database/53-index-concurrency-control/2-summary.md) — 래치 크래빙.
  - 커리큘럼 전체: [../curriculum.md](../curriculum.md)
- 교재·논문
  - OSTEP 29장 "Lock-based Concurrent Data Structures" — 29.1 근사 카운터, 29.2 동시 연결 리스트·hand-over-hand, 29.3 Michael–Scott 두 락 큐·dummy 노드, 29.4 동시 해시 테이블 <https://pages.cs.wisc.edu/~remzi/OSTEP/threads-locks-usage.pdf>
  - Michael & Scott, "Simple, Fast, and Practical Non-Blocking and Blocking Concurrent Queue Algorithms", PODC 1996 — non-blocking·wait-free 정의, ABA와 수정 카운터, 두 락 큐 <https://www.cs.rochester.edu/~scott/papers/1996_PODC_queues.pdf>
  - Chase & Lev, "Dynamic Circular Work-Stealing Deque", SPAA 2005 — `ForkJoinPool` 소스 주석의 인용으로 확인(논문 본문은 열지 않음)
- 소스(OpenJDK 21u <https://github.com/openjdk/jdk21u>, `src/java.base/share/classes/java/util/`)
  - `concurrent/ConcurrentHashMap.java` — 빈 버킷 CAS·첫 노드 `synchronized`, 경합 확률 1/(8·#elements), `TREEIFY_THRESHOLD` 8·`MIN_TREEIFY_CAPACITY` 64, `Segment` 호환, `CounterCell`, null 금지, weakly consistent, "Recursive update"
  - `concurrent/ConcurrentLinkedQueue.java` — Michael–Scott 기반, GC 환경에서 재사용 노드 ABA 없음 주석, `size()` 비상수 시간
  - `concurrent/LinkedBlockingQueue.java` — "two lock queue" 변형(`putLock`·`takeLock`)
  - `concurrent/atomic/AtomicStampedReference.java` — [참조, int] 쌍을 내부 객체로
  - `HashMap.java`·`ArrayList.java` — "not synchronized", fail-fast "best-effort"
  - `concurrent/ForkJoinPool.java` — 작업 훔치기 큐 주석(Chase–Lev)
- 실험 목록(Java는 eclipse-temurin:21-jdk = OpenJDK 21.0.12, `docker run --rm --network none --cpus=2`, 2026-10-05)
  - `HashMapRace.java` — 스레드 4 × 10만 키 동시 `put`(HashMap 16번: size 부족 14번·멈춤 2번, 멈춘 스레드 스택), `ConcurrentHashMap` 크기, `get+put` vs `merge` 카운터
  - `HashMapKeys.java`(판정 단계 재실행) — 같은 동시 `put` 뒤 키마다 `containsKey`로 실제 남은 키를 셈(8회, 멈춤 없음)
  - 사실 점검 재실행(2026-10-05, 같은 환경): `HashMapRace`(8번 중 멈춤 1번)·`Aba`·`Cme`·`QueueThroughput`·`reuse.c`(+ ASan 빌드) — 결정값(`Aba`·`Cme` 출력, `merge` 400000, CHM 400000, `reuse.c` `same=1`) 일치
  - `Aba.java` — Treiber 스택 ABA: `AtomicReference` + 노드 재사용 / 새 노드 / `AtomicStampedReference`
  - `reuse.c` — 호스트 gcc 13.3.0·glibc 2.39, `free` 직후 `malloc` 같은 주소와 C11 `atomic_compare_exchange_strong`
  - `Cme.java` — `ArrayList` 순회 중 삭제(예외 / 끝에서 두 번째는 예외 없이 건너뜀), `removeIf`
  - `QueueThroughput.java` — 생산자 2·소비자 2, 400만 개: `synchronized ArrayDeque`·`LinkedBlockingQueue`·`ArrayBlockingQueue(1024)`·`ConcurrentLinkedQueue`, 3라운드 × 3회(3회째는 GC 시간 포함)
