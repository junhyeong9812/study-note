# data-structure/02-adt-and-cost-contracts — ADT = 연산 + 비용 계약: 같은 인터페이스, 다른 비용 — 정리 (힌트)

## 해결하는 문제

인터페이스는 **무엇을** 할 수 있는지만 알려 준다. **얼마나 드는지**는 구현에 따라 다르다.

```java
long total(List<Long> orders) {          // 호출부는 List만 안다
    long s = 0;
    for (int i = 0; i < orders.size(); i++) s += orders.get(i);
    return s;
}
```

```text
  orders = ArrayList  (원소 10만 개)  → get(i) 한 번 = 배열 칸 하나      → 전체 O(n)
  orders = LinkedList (원소 10만 개)  → get(i) 한 번 = 노드를 최대 n/2번 → 전체 O(n²)
  같은 코드, 같은 결과(4999950000) — 한쪽은 ms 단위, 다른 쪽은 15.7초 (아래 실험)
```

- 코드는 한 글자도 안 바뀌었다. 바뀐 것은 다른 팀이 넘긴 구현체뿐이다.
  - *ADT(Abstract Data Type, 추상 자료형)*: 연산의 이름·인자·결과만 정하고 내부 구현은 감춘 자료형. 원본 [foundations/data-structures-basics](../../foundations/data-structures-basics/README.md) §2는 "함수들의 사용 설명서"라고 부른다.
  - *비용 계약(cost contract)*: 각 연산이 n에 따라 얼마나 드는지에 대한 약속. 문서(Javadoc 등)에 적혀 있거나, 표시 인터페이스(`RandomAccess`)로 드러난다.

쉬운 예: 택배 "배송" 서비스다.
- "보내면 도착한다"(연산)는 같다. 그런데 익일 배송과 선박 화물은 걸리는 시간이 다르다.
- 무엇을 맡길지는 도착 여부가 아니라 **언제 도착하느냐**를 보고 정한다.

똑같은 구조다.\
`List`라는 같은 "배송 약관" 아래에 `ArrayList`(익일)와 `LinkedList`(위치 접근은 선박)가 있다. 인터페이스만 보고 고르면 약관의 소요 시간 항목을 안 읽은 셈이다.

실무 예:
- 공통 유틸 메서드가 `List`를 받아 `get(i)` 루프를 돈다. 어느 날 호출부가 `LinkedList`를 넘기자 배치가 몇 시간 늘어난다.
- `list.contains(x)`를 루프 안에서 부른다. `ArrayList`라 O(n)인데, `HashSet`이면 기대 O(1)이었다.
- ORM의 지연 로딩 컬렉션을 루프에서 건드린다. 같은 `List` 인터페이스인데 원소 접근이 쿼리를 낳는다([database/23-orm-and-n-plus-one](../../database/23-orm-and-n-plus-one/2-summary.md)) — "인터페이스 뒤의 비용"이 네트워크 왕복인 경우다.

## 동작·원리

### 1. ADT를 두 칸으로 나눠 읽는다

```text
  ┌──────────────── ADT ────────────────┐
  │ ① 연산 계약 (무엇)                     │   get(i) → i번째 원소, 범위 밖이면 예외
  │    이름·인자·반환·예외·불변식            │
  ├─────────────────────────────────────┤
  │ ② 비용 계약 (얼마나)                   │   ArrayList: 상수 시간
  │    n에 대한 시간·공간 + 어떤 종류의 보장    │   LinkedList: 가까운 끝부터 순회 (≈ O(n))
  └─────────────────────────────────────┘
```

- ①만 같으면 컴파일러는 통과시킨다. ②가 다르면 운영에서 드러난다.
- Sedgewick 4판 1.3은 API(연산 목록)를 먼저 정하고 구현을 붙인다(algs4 1.3 웹 페이지 "APIs" 절). 구현의 성능 목표("연산당 시간은 컬렉션 크기와 무관, 공간은 크기에 비례")를 책 본문이 명시한다는 세부는 웹 요약에서 확인하지 못했다 [?]. CLRS 3판 3부 서론은 동적 집합의 연산(SEARCH·INSERT·DELETE·MINIMUM·SUCCESSOR …)을 나열하고, 그 비용을 집합 크기로 잰다고 말한다.

### 2. 비용 계약은 어디에 적혀 있나 — Java 21 Javadoc 원문

| 구현 | Javadoc 문구(요지, 원문 인용은 따옴표) | 보장의 종류 |
|---|---|---|
| `ArrayList` | "The `size`, `isEmpty`, `get`, `set`, `iterator`, and `listIterator` operations run in constant time. The `add` operation runs in *amortized constant time*… All of the other operations run in linear time (roughly speaking)." | 최악 상수 / 분할상환 |
| `LinkedList` | "Operations that index into the list will traverse the list from the beginning or the end, whichever is closer to the specified index." | 인덱스 연산 ≈ O(n) |
| `ArrayDeque` | "Most `ArrayDeque` operations run in amortized constant time." 단 `remove(Object)`, `contains`, `iterator.remove()`, 대량 연산은 선형 | 분할상환 |
| `HashMap` | get·put "constant-time performance … assuming the hash function disperses the elements properly" | **해시가 고르게 퍼진다는 가정** 아래 상수 |
| `TreeMap` | "guaranteed log(n) time cost for the `containsKey`, `get`, `put` and `remove` operations" | 최악 보장 |
| `ConcurrentLinkedQueue` | "the `size` method is *NOT* a constant-time operation" — 원소를 훑어서 센다 | 선형, 동시 수정 중엔 부정확 |
| `CopyOnWriteArrayList` | 모든 변경 연산이 "making a fresh copy of the underlying array" | `add`·실제 교체하는 `set` 등 주요 쓰기 O(n), 읽기 싸다(OpenJDK 21u 구현상 `clear()`는 빈 배열로 바꿔 복사 없음) |

- 같은 "O(1)"도 보장의 종류가 다르다.
  - *최악(worst-case) 보장*: 매 호출이 그 안에 든다(`TreeMap`의 log n).
  - *분할상환(amortized) 보장*: 연산 n번의 합이 그 안에 든다. 한 번은 길 수 있다(`ArrayList.add`의 확장 복사).
  - *가정부 보장*: 입력·해시 분포가 좋다는 가정 아래에서만(`HashMap`). 충돌을 노린 입력이면 깨진다 — [algorithm/12-hash-functions](../../algorithm/12-hash-functions/2-summary.md).
    - 흔한 오해: "`HashMap.get`은 O(1)이다"를 무조건 보장으로 읽는 것. Javadoc 문장 자체가 가정을 달고 있다.
- 출처: Java SE 21 API 문서, OpenJDK 21u 소스의 클래스 주석(`src/java.base/share/classes/java/util/`).

### 3. `RandomAccess` — 비용 계약을 타입으로 표시한다

```text
              List (연산 계약)
             /                \
  ArrayList implements        LinkedList
  RandomAccess  ← "get(i)이 (대개) 상수 시간"   RandomAccess 없음
```

- Java 21 `RandomAccess` Javadoc: "Marker interface used by `List` implementations to indicate that they support fast (generally constant time) random access."
  - *표시 인터페이스(marker interface)*: 메서드가 하나도 없고, "이 성질이 있다"는 표시만 하는 인터페이스.
- 같은 문서의 경고: 임의 접근 리스트에 최적인 알고리즘이 순차 접근 리스트(`LinkedList`)에서는 "quadratic behavior"를 낼 수 있다. 그래서 범용 알고리즘은 `instanceof RandomAccess`로 갈라 가라고 권한다.
- JDK가 실제로 그렇게 한다(OpenJDK 21u `Collections.java`).

```java
// java.util.Collections (OpenJDK 21u)
private static final int BINARYSEARCH_THRESHOLD = 5000;

public static <T> int binarySearch(List<? extends Comparable<? super T>> list, T key) {
    if (list instanceof RandomAccess || list.size() < BINARYSEARCH_THRESHOLD)
        return Collections.indexedBinarySearch(list, key);   // get(mid)
    else
        return Collections.iteratorBinarySearch(list, key);  // ListIterator로 이동
}
```

- `Collections.binarySearch` Javadoc: 임의 접근 리스트면 log(n) 시간, 아니고 크면 "O(n) link traversals and O(log n) element comparisons".
- `shuffle`도 `RandomAccess`가 아니고 크면 배열로 옮겨 섞은 뒤 되돌린다(Javadoc: 순차 접근 리스트를 제자리에서 섞을 때의 제곱 동작을 피하려고).
- `List.of(...)` 같은 수정 불가 리스트도 `RandomAccess`를 구현한다(`List` Javadoc "Unmodifiable Lists" 절).

### 4. `LinkedList.get(i)`이 실제로 하는 일

```java
// java.util.LinkedList (OpenJDK 21u) 577~591행
Node<E> node(int index) {
    if (index < (size >> 1)) {           // 앞 절반이면 first부터
        Node<E> x = first;
        for (int i = 0; i < index; i++) x = x.next;
        return x;
    } else {                              // 뒤 절반이면 last부터
        Node<E> x = last;
        for (int i = size - 1; i > index; i--) x = x.prev;
        return x;
    }
}
```

```text
  size = 8, get(5)          first → [0]→[1]→[2]→[3]→[4]→[5]→[6]→[7] ← last
                                                         ▲─────────── 뒤에서 2칸
  get(i)를 i = 0..n-1로 부르면 이동 수 합 ≈ 2 × (0+1+…+n/2) ≈ n²/4  → O(n²)
```

- `ArrayList.get(i)`은 범위 검사 후 배열 칸 하나를 읽는다. `ArrayList.add(index, e)`는 `System.arraycopy`로 뒤를 한 칸 민다(`ArrayList.java` 509~521행).

### 실험: 같은 `List` 코드, 구현만 바꿔 크기 두 배씩

같은 메서드 네 개를 `ArrayList`와 `LinkedList`에 그대로 적용했다. 각 칸은 5번 중 최소, 앞에 작은 크기로 JIT 워밍업.

```java
static long sumByIndex(List<Integer> list) {        // for (i) list.get(i)
    long s = 0;
    for (int i = 0, n = list.size(); i < n; i++) s += list.get(i);
    return s;
}
static long sumByIterator(List<Integer> list) {     // for-each = Iterator
    long s = 0;
    for (int x : list) s += x;
    return s;
}
static void insertMiddle(List<Integer> list, int n) {   // add(size/2, x)를 n번
    for (int i = 0; i < n; i++) list.add(list.size() / 2, i);
}
static void insertAfterEach(List<Integer> list) {       // ListIterator로 원소마다 뒤에 하나씩
    ListIterator<Integer> it = list.listIterator();
    while (it.hasNext()) { it.next(); it.add(-1); }
}
```

(실험, OpenJDK 21.0.12 Temurin `eclipse-temurin:21-jdk` --cpus=2, 기본 GC, 2026-10-05 — 3회 실행 중 1회째 출력. 1 ms 미만 값은 노이즈가 크다)

```text
RandomAccess? ArrayList=true LinkedList=false
ArrayList get(i) 루프                n=10000      0.28ms       n=20000      0.50ms(x1.8) n=40000      1.06ms(x2.1)
ArrayList for-each 루프              n=10000      0.40ms       n=20000      0.76ms(x1.9) n=40000      1.55ms(x2.0)
ArrayList add(size/2) n번           n=10000      5.21ms       n=20000     18.32ms(x3.5) n=40000     93.64ms(x5.1)
ArrayList ListIterator.add n번      n=10000      9.28ms       n=20000     47.75ms(x5.1) n=40000    198.22ms(x4.2)
LinkedList get(i) 루프               n=10000    120.18ms       n=20000    506.84ms(x4.2) n=40000   1861.54ms(x3.7)
LinkedList for-each 루프             n=10000      0.46ms       n=20000      0.56ms(x1.2) n=40000      0.85ms(x1.5)
LinkedList add(size/2) n번          n=10000    131.13ms       n=20000    454.52ms(x3.5) n=40000   2100.73ms(x4.6)
LinkedList ListIterator.add n번     n=10000      0.33ms       n=20000      0.62ms(x1.9) n=40000      3.21ms(x5.2)
```

- 범위(n=40,000, 집필 3회 + 사실 점검 재실행 2회): `LinkedList get(i) 루프` 1682~2098 ms, `ArrayList get(i) 루프` 0.71~1.26 ms. `LinkedList add(size/2)` 1961~2247 ms, `ArrayList add(size/2)` 93.4~107.9 ms. `LinkedList ListIterator.add` 1.22~3.67 ms, `ArrayList ListIterator.add` 180~238 ms.
- 관찰과 해석
  - **get(i) 루프**: `ArrayList`는 두 배 → 약 2배(선형), `LinkedList`는 두 배 → 약 4배(제곱). 40,000개에서 1,000배 이상 차이(이 환경 한정).
  - **for-each**: 둘 다 n=40,000에서 2 ms 미만(`ArrayList` 1.55 ms, `LinkedList` 0.85 ms). 반복자는 다음 노드로 한 칸만 가므로 `LinkedList`도 선형이다. 같은 일을 하는 루프인데 쓰는 연산이 다르면 비용 계약이 달라진다.
  - **중간에 add(size/2)**: 둘 다 제곱(두 배 → 약 4배)이다. `LinkedList`도 중간 위치를 **찾는** 데 O(n)이 들기 때문이다. 같은 O(n²)이어도 상수는 `ArrayList`(연속 메모리 복사)가 20배쯤 작다.
  - **ListIterator.add**: 이것이 `LinkedList`가 이기는 경우다. 반복자가 이미 그 자리에 있으므로 끼우기가 O(1) → 전체 선형. `ArrayList`는 끼울 때마다 뒤를 밀어 제곱이다.
- 원본 §6의 "연결 리스트는 삽입·삭제가 빈번할 때"는 마지막 경우(자리를 쥔 삽입)에만 성립한다는 것이 측정으로 보인다.

### 실험: `Deque` 구현별 비용 — 계약은 같은 O(1), 상수는 작업 모양에 따라

(실험, OpenJDK 21.0.12 Temurin --cpus=2, `-Xmx1g`, 2026-10-05 — 5번 중 최소, 3회 실행 중 1회째 출력)

```text
정상 상태 큐(길이 1000) offer+poll m=5000000   ArrayDeque    60.5ms  LinkedList   123.4ms
정상 상태 큐(길이 1000) offer+poll m=10000000  ArrayDeque   118.1ms  LinkedList   193.2ms
큐 offer/poll 10회전 n=250000    ArrayDeque    90.0ms  LinkedList    68.5ms
큐 offer/poll 10회전 n=500000    ArrayDeque   175.2ms  LinkedList   140.8ms
큐 offer/poll 10회전 n=1000000   ArrayDeque   356.8ms  LinkedList   397.7ms
ArrayDeque.contains(없는 값) 1000번 n=10000    31.85ms
ArrayDeque.contains(없는 값) 1000번 n=20000    65.07ms
ArrayDeque.contains(없는 값) 1000번 n=40000   136.77ms
```

- 정상 상태(길이 1000 유지, 넣고 빼기 반복): 집필 3회·점검 2회 모두 `ArrayDeque`가 빨랐다(m=10,000,000에서 79~125 ms vs 158~193 ms). 이 측정은 넣는 값이 `i & 127`이라 캐시된 `Integer`를 써서 박싱 할당이 없다. `LinkedList`는 여전히 노드를 할당한다.
- 한꺼번에 n개를 채운 뒤 비우기: 모든 실행에서 n=250,000·500,000은 `LinkedList`가 빨랐다. n=1,000,000은 회차에 따라 승자가 바뀌었다. 집필 3회는 `ArrayDeque`가 빨랐고(`ArrayDeque` 336~375 ms, `LinkedList` 398~685 ms), 사실 점검 재실행 2회는 `LinkedList`가 빨랐다(`ArrayDeque` 391~478 ms, `LinkedList` 259~271 ms). 같은 코드의 앞선 시험 실행 3회에서도 `LinkedList`가 빨랐다. 이 측정은 값 `i`(최대 100만)를 박싱하므로 `Integer` 할당·GC가 시간을 크게 차지해 구조 차이를 덮는다(해석).
  - 해석: Javadoc의 "`ArrayDeque`는 큐로 쓸 때 `LinkedList`보다 빠를 가능성이 높다(likely)"는 **상수에 대한 경향**이지 계약이 아니다. 점근 계약은 둘 다 양 끝 O(1)이다(`ArrayDeque`는 배열 확장 때문에 분할상환, `LinkedList`는 노드 연결이라 호출당). 그 차이를 빼면 상수는 작업 모양·GC에 따라 달라진다. 결정이 중요하면 자기 작업 모양으로 잰다([reliability/38-microbenchmarking](../../reliability/38-microbenchmarking/2-summary.md)).
- `contains`: Javadoc대로 선형이다. 두 배 → 약 2배(n=10,000 → 40,000에서 약 3.4~4배, 집필·점검 실행).

## 쓰이는 자료구조·알고리즘

- 이 주제가 쓰는 하위 구조: 동적 배열 [01-dynamic-array](../01-dynamic-array/2-summary.md), 연결 리스트 [02-linked-list](../02-linked-list/2-summary.md), 원형 배열 덱 [04-queue-deque](../04-queue-deque/2-summary.md), 해시 맵 [05-hashmap](../05-hashmap/2-summary.md), 균형 트리 [16-red-black-tree](../16-red-black-tree/2-summary.md)(`TreeMap`)
- 비용 표기: 최악·분할상환·기대값의 구분은 [algorithm/02-asymptotic-analysis](../../algorithm/02-asymptotic-analysis/2-summary.md)
- 이 주제를 쓰는 곳(🔧 모든 컬렉션 선택)
  - 범용 알고리즘이 구현에 따라 경로를 고른다: `Collections.binarySearch`·`shuffle`·`rotate`의 `RandomAccess` 분기
  - 이진 탐색이 의미 있으려면 임의 접근이 O(1)이어야 한다 → [algorithm/06-binary-search](../../algorithm/06-binary-search/2-summary.md)
  - LRU 캐시는 "해시 맵이 노드를 직접 쥐어 연결 리스트의 O(1) 삭제 조건을 만족시킨" 조합이다 → [10-lru-cache](../10-lru-cache/2-summary.md)
  - DB 쪽 같은 문제: ORM 컬렉션의 지연 로딩([database/23-orm-and-n-plus-one](../../database/23-orm-and-n-plus-one/2-summary.md))

## 적용 — 풀어나가는 법

### 1. 메서드를 설계할 때 — 비용 계약을 시그니처나 코드로 드러낸다

```java
// (a) 인덱스가 필요 없으면 반복자로 — ArrayList·LinkedList 등 JDK List는 선형
//     (AbstractList 기본 반복자는 get(i)를 쓰므로, get이 느린 직접 구현은 예외)
static long total(Iterable<Long> orders) {
    long s = 0;
    for (long x : orders) s += x;
    return s;
}

// (b) 인덱스가 꼭 필요하면 RandomAccess를 확인하고, 아니면 복사
static <T> List<T> indexable(List<T> in) {
    return (in instanceof RandomAccess) ? in : new ArrayList<>(in);   // O(n) 복사 한 번
}

// (c) "포함 여부"를 반복해서 묻는다면 Set으로 바꿔 둔다
Set<String> banned = new HashSet<>(bannedList);      // contains 기대 O(1)
for (String u : users) if (banned.contains(u)) ...
```

- 공개 API의 Javadoc에도 비용을 적는다. "이 메서드는 `list.size()`에 대해 선형"처럼.
- 매개변수 타입을 `ArrayList`로 좁히는 것은 대개 지나치다. 인덱스를 안 쓰는 설계(a)가 먼저다.

### 2. 코드 리뷰 체크리스트

- `for (int i …) list.get(i)` — `list`가 어디서 오나? `LinkedList`·지연 로딩 컬렉션·`Collections.synchronizedList`(매 호출 락)일 수 있나?
- 루프 안의 `list.contains`·`list.indexOf`·`list.remove(Object)` — `ArrayList`·`LinkedList`에서는 선형. 바깥 루프와 곱해져 O(n·m)이 된다.
- `ArrayList.remove(0)`·`add(0, x)` — 앞쪽 변경은 선형. 큐면 `ArrayDeque`.
- `ConcurrentLinkedQueue.size()`를 지표 수집 루프에서 부르나 — 선형이고 동시 수정 중엔 부정확하다(Javadoc).
- `CopyOnWriteArrayList`에 쓰기가 잦나 — 추가·교체마다 배열 전체 복사.

### 3. 진단 — 스레드 덤프로 "어느 연산이 비싼가" 찾기

운영 JVM이 CPU를 쓰며 느릴 때, 스레드 덤프를 몇 초 간격으로 2~3번 떠서 같은 프레임이 반복되는지 본다.

```bash
jcmd <pid> Thread.print        # 또는 jstack <pid>
```

(실험, OpenJDK 21.0.12 Temurin --cpus=2, 2026-10-05 — 위 "해결하는 문제"의 `total()`에 원소 10만 개 `LinkedList`를 넘기고 약 6초 뒤 덤프)

```text
"main" #1 [7] prio=5 os_prio=0 cpu=5397.90ms elapsed=6.45s tid=0x00007776a802ad50 nid=7 runnable  [0x00007776ae343000]
   java.lang.Thread.State: RUNNABLE
	at java.util.LinkedList.node(java.base@21.0.12/LinkedList.java:582)
	at java.util.LinkedList.get(java.base@21.0.12/LinkedList.java:488)
	at SlowReport.total(SlowReport.java:6)
	at SlowReport.main(SlowReport.java:13)
```

- 읽는 법: 맨 위 프레임이 `LinkedList.node` 582행(앞 절반을 `x = x.next`로 따라가는 `for` 루프 줄)이고, 그 아래가 `get` → 우리 코드의 `total`. "인덱스 접근 루프 × 순차 접근 리스트"가 원인이다.
- 이 실행은 결과 `4999950000`을 15,720 ms 만에 냈다(사실 점검 재실행: 14,340 ms, 덤프 최상단 프레임 동일). 같은 크기 `ArrayList`면 앞 실험 비율로 ms 단위다.
- 덤프 한 장은 우연일 수 있다. 여러 장에서 같은 프레임이 나오면 그곳이 뜨거운 경로다. 상시 분석은 프로파일러([reliability/36-profiling](../../reliability/36-profiling/2-summary.md))로 한다.

### 4. 코딩 테스트에서

- 문제의 연산 빈도를 먼저 센다. "중간 삽입이 잦다"여도 위치를 인덱스로 받으면 `LinkedList`는 이득이 없다.
- 큐·BFS → `ArrayDeque`, 스택 → `ArrayDeque`(`Stack`은 동기화 오버헤드가 있는 옛 클래스이고 Javadoc이 `Deque`를 권한다), 포함 여부 → `HashSet`, 정렬 순서 + 범위 → `TreeMap`/`TreeSet`.

## 장애 시나리오와 대처

### 1. ⚠ `List.get(i)` 루프에 `LinkedList`가 들어옴 → O(n²) (인터페이스만 보고 비용 계약 무시)

- 현상: 배치·보고서 생성이 데이터 증가 비율보다 훨씬 빠르게 느려진다. 건수 두 배에 시간 네 배.
- 보이는 형태: CPU 100%(한 코어), 스레드 덤프 최상단 `java.util.LinkedList.node`(위 실례). GC는 조용하다.
- 원인: 호출부가 `List`만 보고 `get(i)`를 반복했다. `LinkedList`는 `RandomAccess`가 아니라 `get`마다 순회한다.
- 대처: 반복자(for-each)로 바꾼다. 인덱스가 필요하면 `RandomAccess` 검사 후 `new ArrayList<>(list)`로 복사한다. 리스트를 만드는 쪽도 이유 없는 `LinkedList`를 `ArrayList`로 바꾼다.

### 2. 루프 안의 `List.contains` / `removeAll` → O(n·m)

- 현상: 두 목록 대조(차집합·교집합) 작업이 10만 × 10만 건에서 끝나지 않는다.
- 보이는 형태: 덤프에 `ArrayList.indexOf`·`ArrayList.contains`가 반복된다.
- 원인: `ArrayList`·`LinkedList`의 `contains`는 선형이다. 바깥 루프와 곱해진다. `a.removeAll(b)`에서 `b`가 그런 `List`면 `a`의 원소마다 `b.contains`를 부른다.
- 대처: 조회 쪽을 `HashSet`으로 바꾼다(기대 O(1), 해시 분포 가정은 위 표). 정렬된 두 목록이면 투 포인터 병합으로 O(n + m)([algorithm/08-two-pointers](../../algorithm/08-two-pointers/2-summary.md)).

### 3. 동시성 컬렉션의 숨은 선형 연산 — `ConcurrentLinkedQueue.size()`

- 현상: 큐 길이 지표를 1초마다 수집하는데, 적체가 커질수록 수집 스레드와 큐 처리가 같이 느려진다.
- 보이는 형태: 덤프에서 지표 스레드가 `ConcurrentLinkedQueue.size`에 있다. 보고된 길이가 실제와 다르다.
- 원인: Javadoc대로 `size()`는 원소를 훑는 선형 연산이고, 동시 수정 중엔 부정확하다.
- 대처: 넣고 뺄 때 `AtomicLong`/`LongAdder` 카운터를 따로 둔다. 크기 상한이 필요하면 `ArrayBlockingQueue`처럼 크기를 직접 관리하는 구현을 쓴다(동시성 자료구조는 [29-concurrent-data-structures](../29-concurrent-data-structures/2-summary.md)).

### 4. 가정부 계약이 깨짐 — `HashMap`의 "상수 시간"

- 현상: 특정 입력(같은 해시로 모이는 키)이 들어오자 맵 조회가 느려진다.
- 보이는 형태: 응답 지연 증가, CPU 증가. 덤프에서 `HashMap.getNode`·`TreeNode.find`.
- 원인: 계약이 "해시가 고르게 퍼진다면"을 전제로 했다. 충돌이 몰리면 버킷 안 탐색이 길어진다. OpenJDK 8부터는 한 버킷이 커지면 트리로 바꿔 최악을 줄인다(JEP 180).
- 대처: 키의 `hashCode` 품질 점검, 신뢰할 수 없는 키 수 제한. 자세한 재현은 [05-hashmap](../05-hashmap/2-summary.md)과 [algorithm/12-hash-functions](../../algorithm/12-hash-functions/2-summary.md).

## 핵심 문장

- ADT는 연산 계약과 비용 계약 두 칸으로 읽는다. 컴파일러는 앞 칸만 확인한다.
- `List.get(i)`은 `ArrayList`에서 상수, `LinkedList`에서 가까운 끝부터 순회다. 같은 루프가 O(n)과 O(n²)로 갈린다.
- Java는 비용 차이를 `RandomAccess` 표시 인터페이스로 드러내고, JDK 범용 알고리즘이 이를 보고 경로를 고른다.
- "O(1)"에도 최악·분할상환·가정부(해시 분포) 보장이 있다. 문서의 단서를 함께 읽는다.
- 연결 리스트가 이기는 경우는 반복자가 이미 자리를 쥔 삽입·삭제다. 위치를 찾아야 하면 배열이 상수에서 이긴다.
- 의심되면 두 배 크기로 재 보고, 운영에서는 스레드 덤프 최상단 프레임으로 비싼 연산을 찾는다.

## 관련 주제·근거

- 선행: [01-data-structures-basics](../01-data-structures-basics/2-summary.md) · [algorithm/02-asymptotic-analysis](../../algorithm/02-asymptotic-analysis/2-summary.md) · 원본 [foundations/data-structures-basics](../../foundations/data-structures-basics/README.md) §2 ADT
- 후속·연결: [01-dynamic-array](../01-dynamic-array/2-summary.md) · [02-linked-list](../02-linked-list/2-summary.md) · [04-queue-deque](../04-queue-deque/2-summary.md) · [05-hashmap](../05-hashmap/2-summary.md) · [10-lru-cache](../10-lru-cache/2-summary.md) · [algorithm/06-binary-search](../../algorithm/06-binary-search/2-summary.md) · [algorithm/08-two-pointers](../../algorithm/08-two-pointers/2-summary.md)
- 다른 영역: [database/23-orm-and-n-plus-one](../../database/23-orm-and-n-plus-one/2-summary.md) · [reliability/36-profiling](../../reliability/36-profiling/2-summary.md) · [reliability/38-microbenchmarking](../../reliability/38-microbenchmarking/2-summary.md) · Java 문법 [languages/java/syntax/40-list-set-and-immutable-factories](../../../languages/java/syntax/40-list-set-and-immutable-factories/2-summary.md) · [43-iterator-and-fail-fast](../../../languages/java/syntax/43-iterator-and-fail-fast/2-summary.md)
- 교재
  - CLRS 3판 3부 서론(동적 집합과 그 연산), 10장 Elementary Data Structures
  - Sedgewick·Wayne 『Algorithms』 4판 1.3 Bags, Queues, and Stacks — API 우선 설계, 성능 요구, `java.util.Stack` 비판 <https://algs4.cs.princeton.edu/13stacks/>
- Java SE 21 API 문서
  - `ArrayList` <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/ArrayList.html> · `LinkedList` · `ArrayDeque` · `RandomAccess` <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/RandomAccess.html> · `Collections`(binarySearch·shuffle·rotate) <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Collections.html>
- OpenJDK 21u 소스(github.com/openjdk/jdk21u, `src/java.base/share/classes/java/util/`)
  - `LinkedList.java` `node(int)` 577~591행 · `ArrayList.java` `add(int,E)` 509~521행, `grow` · `Collections.java` `BINARYSEARCH_THRESHOLD = 5000`, `binarySearch` 분기 · `HashMap.java`·`TreeMap.java`·`concurrent/ConcurrentLinkedQueue.java`·`concurrent/CopyOnWriteArrayList.java`·`Stack.java` 클래스 주석 · `List.java`(수정 불가 리스트의 `RandomAccess`)
- JEP 180: Handle Frequent HashMap Collisions with Balanced Trees <https://openjdk.org/jeps/180>
- 실험 목록(2026-10-05, scratchpad `dsa/ds-01/`, OpenJDK 21.0.12 Temurin `eclipse-temurin:21-jdk`, --cpus=2)
  - `ListCost.java`: `ArrayList`/`LinkedList` × get(i) 루프·for-each·add(size/2)·ListIterator.add, n = 1만·2만·4만, 3회
  - `DequeCost.java`: `ArrayDeque`/`LinkedList` 정상 상태 큐·채우고 비우기, `ArrayDeque.contains`, 3회
  - `SlowReport.java`: `LinkedList` 10만 개 `get(i)` 루프 + `jcmd <pid> Thread.print`
