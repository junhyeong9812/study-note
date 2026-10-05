# data-structure/29-concurrent-data-structures — 정답

## 정답

### 1. 동시 `put`의 유실

```text
  스레드 A: table[i] 읽기(비었다) ────────────── table[i] = A노드
  스레드 B:      table[i] 읽기(비었다) ── table[i] = B노드
  결과: table[i] = A노드.  B 노드는 어디에도 연결되지 않았다
```

- `put`은 "읽기 → 판단 → 쓰기" 여러 단계다. 두 스레드가 같은 "비었다"를 보고 각자 쓰면 나중 쓰기가 앞의 것을 덮는다.
- 리사이즈 중이면 노드를 새 표로 옮기는 연결까지 덮여 구조가 망가질 수 있다.
- 락 대기는 없지만 그렇다고 성능이 지켜지는 것도 아니다(2번 실험: 일부 실행은 끝나지 않았다). 핵심은 상태가 틀린다는 것이다. `HashMap` Javadoc은 "not synchronized"라고 밝힌다.

### 2. 비동기화 `HashMap` 실험

- 실험(`HashMapRace.java`, OpenJDK 21.0.12, `--cpus=2`, HashMap 16번 + 사실 점검 8번): 끝난 21번의 `size()`는 155373~343794. 기대 400000보다 작다. 예외는 없었다.
- `size()`도 경합하는 카운터라 이것만으로 키 유실을 단정하지 않는다. 판정 단계 재실행(키마다 `containsKey`, 8회)에서 실제 조회되는 키는 255379~394417개로 모두 40만보다 적었고 `size()`와도 어긋났다.
- 24번 중 3번은 10초 안에 끝나지 않았다. 멈춘 스레드 스택
  - `HashMap$TreeNode.root` ← `putTreeVal` ← `HashMap.putVal`
  - `HashMap$TreeNode.balanceInsertion` ← `treeify` ← `split`(리사이즈 중 트리 분할)
- 서로 다른 정수 키라 정상이면 트리화될 만큼 충돌하지 않는다. 경합으로 망가진 구조를 도는 것으로 해석했다(루프 자체를 추적하지는 않았다).

### 3. 진행 보장

- blocking: 락을 쥔 스레드가 멈추면(선점·페이지 폴트) 다른 스레드도 못 나간다.
- lock-free(오늘날 용법): 누군가 멈춰도 시스템 전체로는 어떤 연산이 유한 단계 안에 끝난다. 개별 스레드는 계속 질 수 있다.
- wait-free: 스레드마다 각자 상한이 정해진(bounded) 단계 안에 끝난다. Michael–Scott 각주: "both non-blocking and starvation free", "within a bounded number of time steps".
- Michael–Scott 1996은 오늘날의 lock-free를 **non-blocking**이라 부르고, **lock-free**는 "락 메커니즘을 쓰지 않는다"는 뜻으로 쓴다. 그래서 "lock-free but not non-blocking"인 알고리즘(락은 없지만 느린 프로세스가 다른 프로세스를 무한정 막는)이 있다고 적는다.
- "더 빠르다"는 틀린 일반화다. 진행 보장은 처리량과 다른 축이다. 9번 실험에서 lock-free `ConcurrentLinkedQueue`는 `ArrayBlockingQueue`보다 느렸다.

### 4. `ConcurrentHashMap` 동기화

- 빈 버킷: 새 노드를 CAS로 버킷에 넣는다. 락이 없다(소스 주석: 대부분의 `put`이 이 경우).
- 찬 버킷: 버킷의 **첫 노드를 `synchronized` 모니터로** 잠그고, 잠근 뒤 그 노드가 여전히 첫 노드인지 확인한다. 다른 버킷은 동시에 갱신된다.
- 리사이즈 중인 버킷에는 `ForwardingNode`가 있고, 갱신하려던 스레드는 옮기는 일을 거든다(`helpTransfer`).
- `get`은 락을 잡지 않는다. 시작 시점에 완료된 갱신을 본다.
- `null` 키·값은 허용하지 않는다(Javadoc). `put(null, v)`는 `NullPointerException`이다.

### 5. 복합 연산

- 실험(`HashMapRace.java`, 집필 3회 + 사실 점검 1회): `get+put`은 144147·147230·167682·179923, `merge`는 400000.
- `get`과 `put`은 각각 원자적이지만 둘 사이에 다른 스레드의 `put`이 끼어든다. 같은 옛 값을 읽은 두 스레드가 같은 새 값을 쓰면 증가 하나가 사라진다.
- `merge`는 키의 버킷을 잠근 채 읽기·계산·쓰기를 한 번에 한다. 경합이 심하면 `computeIfAbsent(k, x -> new LongAdder()).increment()`가 쓰기 경합을 더 줄인다(Javadoc 예).

### 6. ABA

```text
  스택: top → A → B → C
  T1: old=A, next=B 읽음 .........(멈춤)......... CAS(top, A, B) 성공 → top = B
  T2:          pop A, pop B(반납), push A(재사용) → top → A → C
  결과: top → B(반납된 노드), C 소실
```

- 겪는 조건: 노드를 직접 **풀링해 재사용**할 때(또는 정수 값 자체를 CAS할 때). 실험 1번(`Aba.java`): CAS `true`, 최종 스택 `B`.
- 겪지 않는 조건: 노드를 매번 새로 만들 때. T1이 A의 참조를 쥐고 있으므로 GC가 A를 수거하지 않고, 새 노드는 다른 참조다. 실험 2번: CAS `false`, 최종 `A'->C`.
- 근거: `ConcurrentLinkedQueue` 소스 주석 — "in garbage collected systems, there is no possibility of ABA problems due to recycled nodes, so there is no need to use 'counted pointers'".
- C에서는 `free` 직후 `malloc`이 같은 주소를 돌려줄 수 있다(`reuse.c`: `same=1`, CAS 성공).

### 7. stamp

- 실험 3번: T2가 pop·pop·push로 stamp를 0 → 3으로 올렸다. T1의 `compareAndSet(A, B, 0, 1)`은 참조는 같아도 stamp가 달라 `false`. 재시도해서 A를 꺼냈고 최종 스택은 `C`.
- 완전하지 않은 이유: 카운터 폭이 유한해서 T1이 멈춘 사이 카운터가 한 바퀴 돌아 같은 값이 되면 다시 속는다. Michael–Scott: 이 방법은 ABA를 "extremely unlikely"하게 만들 뿐 보장하지 않는다. 또 포인터와 카운터를 함께 바꾸려면 2배 폭 CAS나 "배열 인덱스 + 카운터를 한 워드에" 같은 방법이 필요하다.
- Java `AtomicStampedReference`는 [참조, int] 쌍 객체를 갱신마다 새로 만들어 참조 하나를 CAS한다(Javadoc). 대가로 갱신마다 할당이 생긴다.

### 8. 순회 중 삭제

- 실험(`Cme.java`)
  - `"b"` 삭제 → `java.util.ConcurrentModificationException`.
  - `"c"`(끝에서 두 번째) 삭제 → 예외 없음, 결과 `[a, b, d]`. 크기가 3으로 줄어 `hasNext()`가 `false`가 되고 `d`는 검사되지 않는다.
- 단일 스레드에서도 일어난다. 이름의 "Concurrent"는 순회와 수정이 겹쳤다는 뜻이다.
- `ArrayList` Javadoc: fail-fast는 "cannot be guaranteed", 예외는 "best-effort". 6번처럼 예외 없이 원소를 건너뛸 수 있으므로 버그 탐지용일 뿐이다. 정확성은 `Iterator.remove`·`removeIf`나 동시 컬렉션으로 확보한다.

### 9. 큐 처리량

- 실험(`QueueThroughput.java`, `--cpus=2`, 12라운드 범위): `ArrayBlockingQueue(1024)` 1044~1374 ms < `ConcurrentLinkedQueue` 2806~3844 ms < `LinkedBlockingQueue` 4979~6946 ms < `synchronized ArrayDeque` 5977~7997 ms(대체로 이 순서, 두 락 큐는 범위가 겹친다).
- 일반화하면 안 되는 것
  - "lock-free가 느리다"도 "락이 빠르다"도 아니다. CPU 2개에 스레드 4개, 스핀하는 소비자, 크기 제한 유무가 섞인 이 환경의 결과다.
  - 크기 제한이 있는 것은 `ArrayBlockingQueue`뿐이라 큐 길이가 다르다. GC 시간은 0~33 ms로 작아 GC 탓은 아니었고, 정확한 원인은 분석하지 않았다.
  - 코어가 많거나 소비 작업이 무거우면 순위가 바뀔 수 있다. 실제 부하로 잰다.

### 10. 한 코어 100%, 응답 없음

- 순서
  1. `top -H -p <pid>`로 CPU를 쓰는 스레드 ID를 찾는다.
  2. `jstack <pid>`(또는 `jcmd <pid> Thread.print`)를 몇 초 간격으로 2~3번 뜬다. 스레드 ID를 16진수로 바꿔 `nid=0x...`와 맞춘다.
  3. 매번 `RUNNABLE`인 채 같은 메서드에 머무는지 본다.
- 의심
  - `HashMap$TreeNode.*`·`HashMap.putVal`·`getNode`·`resize`에 머문다 → 비동기화 `HashMap`을 여러 스레드가 공유해 구조가 망가진 무한 순회(2번 실험 스택).
  - 직접 만든 CAS 재시도 루프에 머문다 → 경합으로 계속 실패하는 루프나, ABA로 망가진 연결.
- 대처: 공유 맵을 `ConcurrentHashMap`으로 바꾼다. 멈춘 프로세스는 재시작 외에 되돌릴 방법이 없다. 재발 방지로 공유 필드의 컬렉션 타입을 리뷰 항목에 넣고, 동시 스트레스 테스트로 개수를 대조한다.
