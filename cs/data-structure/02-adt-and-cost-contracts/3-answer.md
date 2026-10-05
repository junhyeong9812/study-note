# data-structure/02-adt-and-cost-contracts — 정답

## 정답

### 1. 두 칸으로 읽는 이유

- 연산 계약: 이름·인자·반환·예외·불변식. `List.get(i)` = "i번째 원소, 범위 밖이면 `IndexOutOfBoundsException`".
- 비용 계약: 그 연산이 n에 따라 얼마나 드는지와 보장의 종류. `ArrayList.get`은 상수, `LinkedList.get`은 가까운 끝부터 순회.
- 컴파일러는 연산 계약(타입·시그니처)만 확인한다. 비용 계약은 문서·표시 인터페이스·측정으로만 확인된다. 그래서 같은 코드가 구현체에 따라 O(n)과 O(n²)로 갈린다.

### 2. get(i) 루프 vs for-each

- `ArrayList` get 루프: 두 배 → 약 2배(선형). `LinkedList` get 루프: 두 배 → 약 4배(제곱).
- 실험(OpenJDK 21.0.12, --cpus=2): `ArrayList` 0.28 → 0.50 → 1.06 ms, `LinkedList` 120.18 → 506.84 → 1861.54 ms(×4.2, ×3.7). 40,000개 3회 범위 `LinkedList` 1682~2098 ms vs `ArrayList` 0.71~1.26 ms.
- for-each는 반복자가 다음 노드로 한 칸씩만 가므로 둘 다 선형이다. 실험에서 n=40,000에도 둘 다 2 ms 미만이다(`ArrayList` 1.55 ms, `LinkedList` 0.85 ms — 이 크기는 노이즈가 커서 비율은 의미가 약하다).

### 3. `LinkedList.get(i)` 내부

- `checkElementIndex` 후 `node(index)`를 부른다. `index < size/2`면 `first`에서 `next`로, 아니면 `last`에서 `prev`로 따라간다(OpenJDK 21u `LinkedList.java` 577~591행).
- 그래도 한 번의 `get`이 최대 n/2번 이동한다. i = 0..n−1을 모두 부르면 이동 합 ≈ n²/4 → O(n²). 가까운 끝에서 출발하는 최적화는 상수(1/2)만 줄인다.

### 4. 중간 삽입 두 방식

- `add(size/2, x)` n번: 둘 다 O(n²). `ArrayList`는 뒤 절반을 `System.arraycopy`로 밀고, `LinkedList`는 중간 노드를 **찾는** 데 n/2번 이동한다. 실험(n=40,000, 5회): `ArrayList` 93.4~107.9 ms, `LinkedList` 1961~2247 ms → `ArrayList`가 약 20배 빠르다(이 환경 한정). 연속 메모리 복사가 노드 따라가기보다 상수가 작다.
- `ListIterator.add` n번: 반복자가 이미 자리를 쥐고 있으므로 `LinkedList`는 삽입마다 O(1) → 전체 선형(1.22~3.67 ms). `ArrayList`는 삽입마다 뒤를 밀어 O(n²)(180~238 ms). 이 경우 `LinkedList`가 이긴다.

### 5. `RandomAccess`

- 메서드 없는 표시 인터페이스. "fast (generally constant time) random access"를 지원한다는 표시다(Java 21 Javadoc). `ArrayList`는 구현하고 `LinkedList`는 안 한다. 수정 불가 리스트(`List.of`)도 구현한다.
- `Collections.binarySearch`: `list instanceof RandomAccess || list.size() < BINARYSEARCH_THRESHOLD`(5000)이면 `get(mid)`로 하는 인덱스 이진 탐색, 아니면 `ListIterator`로 이동하는 반복자 이진 탐색(OpenJDK 21u `Collections.java`). Javadoc: 후자는 O(n) 링크 이동 + O(log n) 비교.
- `shuffle`도 `RandomAccess`가 아니고 크면 배열로 옮겨 섞는다.

### 6. 보장의 종류

- `ArrayList.add` 분할상환 상수: n번 add의 합이 O(n). 한 번은 확장 복사로 O(n)일 수 있다.
- `TreeMap.get` log(n) 보장: 매 호출의 최악이 O(log n)(레드-블랙 트리).
- `HashMap.get` 상수: 해시가 버킷에 고르게 퍼진다는 **가정**이 붙은 보장. 충돌이 몰리면 깨진다. OpenJDK 8부터 큰 버킷을 트리로 바꿔 최악을 완화한다(JEP 180).

### 7. 덤프가 `LinkedList.node`를 가리킬 때

- 원인: `total()`이 `List`의 `get(i)`를 루프로 부르는데, 들어온 구현이 `LinkedList`라 `get`마다 순회한다 → O(n²). 582행은 `node()`에서 앞 절반을 `x = x.next`로 따라가는 `for` 루프 줄이다. 실험에서 10만 개에 14,340~15,720 ms(2회).
- 고치는 법
  - 루프를 for-each(반복자)로 바꾼다 → `LinkedList`·`ArrayList` 모두 선형. (`AbstractList`만 상속한 직접 구현은 기본 반복자가 `get(i)`를 부르므로 예외다.)
  - 인덱스가 꼭 필요하면 `list instanceof RandomAccess ? list : new ArrayList<>(list)`로 한 번 복사한다. 리스트를 만드는 쪽의 불필요한 `LinkedList`도 `ArrayList`로 바꾼다.

### 8. "likely to be faster"는 계약이 아니다

- 정상 상태 큐(길이 1000 유지, offer+poll 1천만 번, 캐시된 `Integer`라 박싱 할당 없음): 5회 모두 `ArrayDeque` 79~125 ms, `LinkedList` 158~193 ms → `ArrayDeque`가 빨랐다.
- 채운 뒤 비우기: 모든 실행에서 n=250,000·500,000은 `LinkedList`가 빨랐다(예: 68.5 ms vs 90.0 ms). n=1,000,000은 측정 회차에 따라 승자가 바뀌었다(집필 3회 `ArrayDeque`, 점검 2회 `LinkedList`).
- 해석: 점근 계약은 둘 다 양 끝 O(1)이다(`ArrayDeque`는 분할상환, `LinkedList`는 호출당). 상수는 박싱 할당·GC·작업 모양에 따라 바뀐다. Javadoc의 "likely"는 경향이다. 중요한 결정이면 자기 작업 모양으로 잰다.

### 9. `ConcurrentLinkedQueue.size()`

- Javadoc: `size`는 "NOT a constant-time operation" — 원소를 훑어서 세고, 순회 중 수정되면 부정확할 수 있다.
- 적체가 클수록 매초 훑는 길이가 길어져 CPU를 먹고, 값도 정확하지 않다.
- 대안: 넣을 때·뺄 때 `LongAdder`/`AtomicLong` 카운터를 갱신해 지표로 쓴다. 크기 상한이 필요하면 크기를 직접 관리하는 `ArrayBlockingQueue` 등을 검토한다.

### 10. `removeAll`의 비용

- `a`가 `ArrayList`면 `removeAll`은 `batchRemove`에서 `a`의 원소마다 `b.contains`를 부른다(OpenJDK 21u `ArrayList.java` 896행~). `b`가 `ArrayList`·`LinkedList`면 그 `contains`가 선형이다(`Collections.nCopies`처럼 `contains`가 O(1)인 특수 `List`도 있다) → 10만 × 10만 = 100억 비교 급 → O(n·m).
- 개선 1: `a.removeAll(new HashSet<>(b))` — 조회가 기대 O(1)이 되어 O(n + m)(해시 분포 가정).
- 개선 2: 두 목록이 정렬돼 있으면(또는 정렬해 두면) 투 포인터로 한 번에 훑어 O(n + m)(정렬 비용 O(n log n) 별도).
