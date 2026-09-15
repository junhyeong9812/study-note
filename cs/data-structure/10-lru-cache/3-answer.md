# data-structure/10-lru-cache — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 작성 방식: **2-summary를 닫고 기억만으로** 쓴다 → 실제 코드/원전으로 검증 → 틀린 부분만 수정.
> 기준 소스는 문서가 아니라 코드다.
> ⚠️ 이 정답은 Claude 초안(2026-09-15) — 본인 검토 후 이 줄 삭제

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### A. 문제 (LRUCacheProblems)

#### 1. LRU 적중률 시뮬레이션 — `hitRatio`

**질문**: 어떻게 푸는가. 왜 직접 세지 않고 `LRUCache` 의 `hits()` 에 맡기는가, 그리고 정수 나눗셈이 여기서 어떻게 답을 망치는가.

**impl 코드** (`impl/LRUCacheProblems.java`)

```java
public static double hitRatio(int capacity, int[] accesses) {
    if (accesses == null || accesses.length == 0) {
        return 0.0;
    }
    Cache<Integer, Boolean> cache = new LRUCache<>(capacity);
    for (int key : accesses) {
        if (cache.get(key) == null) {
            cache.put(key, Boolean.TRUE);
        }
    }
    return (double) cache.hits() / accesses.length;
}
```

- 논리: 접근 기록을 **순서대로 캐시에 흘려보내기만** 한다.
- 논리: 값이 필요 없으므로 `Boolean.TRUE` 를 표식으로 넣는다 — 이 캐시는 "봤다/안 봤다"만 기억한다.
- 논리: `get` 이 `null` 이면 캐시에 없다는 뜻이라 그때만 `put` 한다.\
  이미 있으면 `get` 이 이미 순서를 갱신했으므로 더 할 일이 없다.
- 논리: `put` 할 때 용량이 찼으면 캐시가 알아서 가장 오래된 것을 버린다 — 이 함수는 축출에 관여하지 않는다.

> **적중률(hit ratio)** — 전체 접근 중 캐시에 있었던 비율. `hits / 전체 접근 수`.\
> 예: 6번 접근해서 2번 있었으면 `2/6 ≈ 0.333` 이다.

**손으로 추적** — `hitRatio(2, {1, 2, 1, 3, 1, 2})` → `2/6` (테스트 `classic`)

```
용량 2. 줄은 [오래됨 ... 최근] 순서

 접근 1 : get(1) -> null (miss 1)      put(1)          줄 [1]
 접근 2 : get(2) -> null (miss 2)      put(2)          줄 [1, 2]
 접근 1 : get(1) -> TRUE (hit 1)       순서 갱신        줄 [2, 1]   <- 1 이 뒤로
 접근 3 : get(3) -> null (miss 3)      put(3): 꽉 참
                                        -> 맨 앞 2 를 버린다        줄 [1, 3]
 접근 1 : get(1) -> TRUE (hit 2)       순서 갱신        줄 [3, 1]
 접근 2 : get(2) -> null (miss 4)      put(2): 꽉 참
                                        -> 맨 앞 3 을 버린다        줄 [1, 2]

 hits = 2, 전체 = 6  ->  2/6 = 0.3333...
```

- 논리: 세 번째 접근에서 `1` 을 다시 쓴 덕에 `1` 이 살아남고 `2` 가 버려졌다.\
  **`get` 이 순서를 바꾸지 않았다면** 다른 결과가 나온다 — 그것이 3번 문제의 주제다.

**왜 직접 세지 않고 `hits()` 에 맡기는가**

```
 (A) 직접 세기

     int hits = 0;
     for (int key : accesses) {
         if (cache.containsKey(key)) hits++;     <- 판정 로직을 여기서 다시 쓴다
         ...
     }

     문제 1 : 판정 규칙이 두 곳에 생긴다
              캐시 안(get 이 hits++ 하는 곳)과 바깥(이 루프)
              두 규칙이 어긋나면 어느 쪽이 맞는지 알 수 없다
     문제 2 : containsKey 는 순서를 안 바꾼다 (계약에 그렇게 적혀 있다)
              그래서 판정용으로 containsKey 를 쓰면 시뮬레이션 자체가 달라진다
     문제 3 : 결국 get 을 또 불러야 하고, 그러면 통계가 두 배로 잡힌다

 (B) hits() 에 맡기기 (impl)

     적중 판정은 캐시의 일이다. 캐시가 자기 계약대로 센 값을 읽는다
     이 함수는 '접근을 흘려보내고 결과를 읽는' 역할만 한다

     => 단일 출처(single source of truth)
```

- 논리: `Cache` 계약이 `hits()`/`misses()`/`evictions()` 를 **처음부터 제공**하는 이유가 이것이다.\
  시뮬레이션을 하려면 통계가 자료구조 안에 있어야 한다.
- 논리: 08번에서 `edgeCount` 를 그래프가 세던 것과 같은 원리다 — **개수는 소유자가 센다**.
- 한계: 대신 `hits()` 가 틀리면 이 함수도 조용히 틀린다.\
  `CacheContractTest` 가 통계를 따로 검증하는 이유다.

**정수 나눗셈이 어떻게 답을 망치는가**

```java
return (double) cache.hits() / accesses.length;
//     ^^^^^^^^ 이 캐스팅이 없으면
```

```
 cache.hits()      -> long   (2)
 accesses.length   -> int    (6)

 (A) (double) hits / length
        double 2.0 / int 6
        -> 자바가 6 을 6.0 으로 승격 -> 0.3333...        OK

 (B) hits / length          (캐스팅 없음)
        long 2 / int 6
        -> long 나눗셈 -> 0 (소수점 버림)
        -> 반환 타입 double 로 승격 -> 0.0               틀림

 언제 0 이 아닌가?
    hits >= length 일 때만 -- 즉 적중률이 100% 일 때 1.0
    그 외에는 전부 0.0 이다

 컴파일 에러도 예외도 없다. 값만 조용히 0 이 된다
```

```java
@Test
@DisplayName("정수 나눗셈을 쓰면 여기서 걸린다")
void notIntegerDivision() {
    double r = LRUCacheProblems.hitRatio(2, new int[]{1, 2, 1, 3, 1, 2});
    assertTrue(r > 0.0 && r < 1.0, "적중률이 " + r + " 다. 0 이나 1 이면 정수로 나눈 것이다");
}
```

> **정수 나눗셈(integer division)** — 정수끼리 나누면 몫의 소수점 이하를 버리는 연산.\
> 예: `2 / 6` 은 0.333이 아니라 0이며, 결과를 `double` 에 담아도 이미 버려진 뒤라 0.0이 된다.

- 논리: 07번 `MedianFinder.median()` 의 `/ 2` vs `/ 2.0` 과 **같은 함정**이다.\
  반환 타입이 `double` 이라 타입 검사가 잡아 주지 않는다.
- 한계: 테스트가 `0 < r < 1` 을 요구하는 것이 영리하다 — 정확한 값 비교보다 **함정만 노린 검사**다.
- 한계: `allSame` 테스트(`{1,1,1,1}` → 3/4)는 정수 나눗셈이어도 0이 나오므로 걸린다.\
  그러나 적중률이 100%인 입력만 있으면 정수 나눗셈이 1.0을 주어 통과해 버린다.

**경계와 규모**

- 논리: `accesses` 가 `null` 이거나 비었으면 `0.0` 이다 — 0으로 나누는 것을 앞에서 막는다.
- 비용(왜): `get` 과 `put` 이 각각 O(1)이므로 전체 **O(접근 수)** 다.
- 비용(왜): `largeTrace` 테스트가 100만 접근을 20초 제한으로 돌린다.\
  키가 0~4999 중 무작위이고 용량이 1000이라 적중률이 0.1~0.4 사이로 나온다.\
  (대략 1000/5000 = 0.2 근처가 기대값이다 — 원본에 근거 없음, 내 추론)

**질문별 답**

- Q: 문제 1을 어떻게 푸는가?\
  A: 용량 `capacity` 짜리 `LRUCache` 를 만들고 접근 기록을 순서대로 `get` 해 본다.\
  `null` 이면(미적중) `put` 으로 넣고, 아니면 `get` 이 이미 순서를 갱신했으므로 넘어간다.\
  끝나면 `cache.hits() / 전체 접근 수` 를 실수로 나눈다.

- Q: 왜 직접 세지 않고 `hits()` 에 맡기는가?\
  A: 적중 판정은 **캐시의 일**이고, 밖에서 또 세면 규칙이 두 곳에 생겨 어긋날 수 있기 때문이다.\
  게다가 판정용으로 `containsKey` 를 쓰면 순서를 갱신하지 않아 시뮬레이션 자체가 달라지고, `get` 을 또 부르면 통계가 두 배로 잡힌다.\
  `Cache` 계약이 통계를 처음부터 제공하는 것이 그 때문이다.

- Q: 정수 나눗셈이 어떻게 답을 망치는가?\
  A: `hits()` 가 `long`, `length` 가 `int` 라 `(double)` 캐스팅이 없으면 **정수 나눗셈**이 되어 소수점이 버려진다.\
  적중률이 100%가 아닌 한 항상 `0.0` 이 나오는데, 반환 타입이 `double` 이라 컴파일 에러도 예외도 없다.\
  `notIntegerDivision` 테스트가 `0 < r < 1` 을 요구해 이 함정만 노린다.

---

#### 2. Belady 최적 — `optimalHitRatio`

**질문**: 어떻게 푸는가. "다음 등장 시점"을 O(1)로 얻으려면 무엇을 미리 만들어 두어야 하는가. 쓸 수도 없는 알고리즘을 구현하는 이유는 무엇인가.

**impl 코드**

```java
public static double optimalHitRatio(int capacity, int[] accesses) {
    if (accesses == null || accesses.length == 0) {
        return 0.0;
    }
    if (capacity < 1) {
        throw new IllegalArgumentException("용량은 1 이상이어야 한다: " + capacity);
    }
    Map<Integer, Deque<Integer>> nextUse = new HashMap<>();
    for (int i = accesses.length - 1; i >= 0; i--) {
        nextUse.computeIfAbsent(accesses[i], k -> new ArrayDeque<>()).addFirst(i);
    }

    Set<Integer> cache = new HashSet<>();
    int hits = 0;
    for (int key : accesses) {
        nextUse.get(key).pollFirst();
        if (cache.contains(key)) {
            hits++;
            continue;
        }
        if (cache.size() == capacity) {
            Integer victim = null;
            int farthest = -1;
            for (Integer c : cache) {
                Deque<Integer> q = nextUse.get(c);
                int next = q.isEmpty() ? Integer.MAX_VALUE : q.peekFirst();
                if (next > farthest) {
                    farthest = next;
                    victim = c;
                }
            }
            cache.remove(victim);
        }
        cache.add(key);
    }
    return (double) hits / accesses.length;
}
```

> **Belady 최적 알고리즘(OPT)** — "앞으로 가장 나중에 쓰일 것"을 버리는 축출 정책. 미래를 알아야 하므로 실제로는 쓸 수 없지만, 어떤 정책도 이보다 잘할 수 없다는 것이 증명되어 있다.\
> 예: 같은 접근 기록에서 LRU가 60%를 낸다면 OPT가 65%인지 95%인지를 보고 "정책을 바꿀 여지"를 판단한다.

**핵심 발상**

```
 축출 후보가 여럿일 때 누구를 버리는 것이 최선인가?

   "앞으로 가장 나중에 쓰일 것"을 버린다

 왜 최선인가 (직관)
   버린 것을 다시 쓰는 시점이 미스로 돌아온다
   그 시점이 멀수록 그 사이에 다른 이득을 볼 기회가 많다
   가장 나중에 쓰일 것을 버리면 미스가 가장 멀리 밀린다
   (다시 안 쓰일 것이 있으면 그것이 최우선 후보다 -- 미스가 영영 안 온다)

 LRU 와의 대비
   LRU  : "과거에 가장 오래 안 쓴 것" -- 과거를 보고 미래를 추측한다
   OPT  : "미래에 가장 나중에 쓸 것"  -- 미래를 직접 본다
   둘이 보는 방향이 정반대다
```

**"다음 등장 시점"을 O(1)로 얻는 장치 — 역방향으로 만든 인덱스 목록**

```java
Map<Integer, Deque<Integer>> nextUse = new HashMap<>();
for (int i = accesses.length - 1; i >= 0; i--) {
    nextUse.computeIfAbsent(accesses[i], k -> new ArrayDeque<>()).addFirst(i);
}
```

```
 accesses = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]
 인덱스      0  1  2  3  4  5  6  7  8  9 10 11

 뒤에서부터(i = 11 -> 0) 돌면서 각 키의 덱 '앞에' 인덱스를 꽂는다
 -> 결과적으로 각 덱이 '오름차순'이 된다

   nextUse[1] = [0, 4, 7]
   nextUse[2] = [1, 5, 8]
   nextUse[3] = [2, 9]
   nextUse[4] = [3, 10]
   nextUse[5] = [6, 11]

 왜 뒤에서부터 도는가:
   앞에서부터 돌면서 addLast 해도 같은 결과가 나온다
   (원본은 addFirst + 역방향을 택했을 뿐이다 -- 결과는 동치)

 본 루프의 첫 줄이 핵심이다

   nextUse.get(key).pollFirst();     <- '지금 이 접근'의 인덱스를 버린다

   그러면 덱의 맨 앞(peekFirst)이 항상 '다음 등장 시점'이 된다   -> O(1)
   덱이 비었으면 '다시 안 나온다' -> Integer.MAX_VALUE 로 취급
```

- 논리: `pollFirst()` 를 **판정 전에** 부르는 것이 중요하다.\
  현재 인덱스를 남겨 두면 "다음"이 아니라 "지금"을 보게 된다.
- 논리: 미리 만들어 두지 않으면 매번 `accesses` 의 뒤쪽을 스캔해야 한다 — 그러면 O(n^2) 이다.
- 비용(왜): 인덱스 만들기 O(n), 본 루프는 미스마다 캐시 전체를 훑으므로 O(n x capacity).\
  전체 **O(n x capacity)** 다.
- 한계: `hitRatio` 가 O(n)인 것과 달리 OPT는 용량에 비례하는 항이 붙는다.\
  그래서 문제 1에는 100만 건 테스트가 있지만 OPT에는 없다.

**손으로 추적** — `optimalHitRatio(2, {1, 2, 3, 1, 2, 3})` → `2/6` (테스트 `beatsLruOnScan`)

```
 nextUse : 1=[0,3]  2=[1,4]  3=[2,5]   용량 2

 i=0 key=1 : pollFirst -> 1=[3]
             캐시 {} 에 없다. 자리 있음 -> 넣는다          캐시 {1}
 i=1 key=2 : pollFirst -> 2=[4]
             없다. 자리 있음 -> 넣는다                     캐시 {1,2}
 i=2 key=3 : pollFirst -> 3=[5]
             없다. 꽉 참 -> 다음 등장 시점을 비교
                1 -> 3      2 -> 4        가장 먼 것은 2
             2 를 버리고 3 을 넣는다                       캐시 {1,3}
 i=3 key=1 : pollFirst -> 1=[]
             있다 -> hit (1)                               캐시 {1,3}
 i=4 key=2 : pollFirst -> 2=[]
             없다. 꽉 참 -> 다음 등장 시점
                1 -> 없음(MAX)   3 -> 5      가장 먼 것은 1
             1 을 버리고 2 를 넣는다                       캐시 {3,2}
 i=5 key=3 : pollFirst -> 3=[]
             있다 -> hit (2)

 hits = 2 -> 2/6

 같은 입력에서 LRU 는 0/6 이다 (i=2 에서 1 을 버리고, i=3 에서 2 를 버린다)
 -> LRU 는 '바로 다음에 쓸 것'을 계속 골라 버린다
```

- 논리: `i=4` 에서 `1` 을 버리는 것이 OPT의 성격을 잘 보여준다.\
  `1` 은 **방금 전에 썼는데도** 다시 안 나오므로 즉시 버려진다 — LRU라면 절대 안 버릴 것이다.

**쓸 수 없는 알고리즘을 구현하는 이유 — 상한선**

```
 "LRU 적중률이 60% 다" 만으로는 아무 판단도 못 한다

   최적이 95% 라면  -> 정책이 나쁘다. LFU·ARC·스캔 저항 같은 것을 검토할 여지가 크다
   최적이 65% 라면  -> 정책은 거의 최선이다.
                       고칠 것은 용량이거나 접근 패턴이지 교체 정책이 아니다

 => "얼마나 좋은가"는 무엇과 비교하느냐로 정해진다
    OPT 는 '이론적 상한'을 알려주는 자(ruler)다
```

```java
@Test
@DisplayName("최적은 LRU 보다 절대 나쁘지 않다")
void neverWorseThanLru() {
    Random rnd = new Random(99L);
    for (int trial = 0; trial < 200; trial++) {
        int cap = 1 + rnd.nextInt(5);
        int[] acc = new int[20 + rnd.nextInt(60)];
        for (int i = 0; i < acc.length; i++) {
            acc[i] = rnd.nextInt(8);
        }
        double lru = LRUCacheProblems.hitRatio(cap, acc);
        double opt = LRUCacheProblems.optimalHitRatio(cap, acc);
        assertTrue(opt >= lru - EPS,
                "최적 " + opt + " 이 LRU " + lru + " 보다 나쁘다. cap=" + cap);
    }
}
```

- 논리: 이 테스트가 **OPT가 상한임을 200개의 무작위 입력으로 확인**한다.\
  한 번이라도 OPT < LRU 가 나오면 OPT 구현이 틀린 것이다.
- 논리: 무작위 테스트가 잘 맞는 자리다 — 구체적 기대값을 손으로 계산하지 않아도 되는 **성질(property)** 이 있기 때문이다.

> **속성 기반 테스트(property-based test)** — 구체적 입출력 대신 "항상 성립해야 하는 성질"을 무작위 입력으로 검사하는 방식.\
> 예: "최적은 LRU보다 나쁠 수 없다"는 성질이라 입력을 무작위로 만들어도 검사할 수 있다.

- 논리: `capacityLargeEnough` 테스트는 **둘이 같아지는 경우**를 보여준다.\
  서로 다른 키가 3개인데 용량이 3이면 축출이 아예 없어 첫 접근 3번만 미스다 → 둘 다 6/9.
- 논리: `degenerate` 테스트도 마찬가지다 — 같은 키만 있으면 정책이 개입할 여지가 없다.
- 한계: OPT는 **전체 접근 기록을 미리 알아야** 한다.\
  실시간 캐시는 다음에 뭐가 올지 모르므로 절대 구현할 수 없다 — 사후 분석 도구다.
- 한계: `victim` 을 찾을 때 `HashSet` 을 순회하므로 동점(둘 다 `MAX_VALUE`)일 때 **어느 쪽이 버려질지는 비결정적**이다.\
  둘 다 다시 안 쓰이므로 적중률은 같다 — 답에 영향이 없다.

**질문별 답**

- Q: 문제 2를 어떻게 푸는가?\
  A: 각 키가 등장하는 인덱스 목록을 미리 만들어 두고, 접근을 순서대로 처리하면서 현재 인덱스를 목록에서 빼낸다.\
  캐시에 있으면 적중, 없고 꽉 찼으면 캐시 안의 키들 중 **다음 등장 시점이 가장 먼 것**(없으면 무한대)을 버린 뒤 넣는다.

- Q: "다음 등장 시점"을 O(1)로 얻으려면 무엇을 미리 만들어야 하는가?\
  A: **키 → 등장 인덱스 목록(오름차순 덱)** 이다.\
  본 루프에서 현재 접근의 인덱스를 `pollFirst` 로 버리면, 그 덱의 맨 앞이 항상 "다음 등장 시점"이라 `peekFirst` 한 번으로 읽힌다.\
  이것이 없으면 매번 뒤쪽을 스캔해 O(n²)이 된다.

- Q: 쓸 수도 없는 알고리즘을 구현하는 이유는?\
  A: **상한선(기준자)** 이기 때문이다.\
  "LRU가 60%"라는 숫자만으로는 좋은지 나쁜지 알 수 없다 — 최적이 95%면 정책을 바꿀 여지가 크고, 65%면 손볼 것은 정책이 아니라 용량이나 접근 패턴이다.\
  "얼마나 좋은가"는 무엇과 비교하느냐로 정해진다.

---

#### 3. 최근 capacity 개 기준 중복 제거 — `deduplicateStream`

**질문**: 어떻게 푸는가. 여기서 `containsKey` 가 아니라 `get` 을 써야 하는 이유는 무엇이고, 그 차이가 결과를 어떻게 바꾸는가.

**impl 코드**

```java
public static List<Integer> deduplicateStream(int capacity, int[] stream) {
    List<Integer> out = new ArrayList<>();
    if (stream == null || stream.length == 0) {
        return out;
    }
    Cache<Integer, Boolean> seen = new LRUCache<>(capacity);
    for (int x : stream) {
        if (seen.get(x) != null) {
            continue;
        }
        out.add(x);
        seen.put(x, Boolean.TRUE);
    }
    return out;
}
```

- 논리: "최근에 본 `capacity` 개"를 기억하는 **미끄러지는 창(sliding window)** 을 캐시로 만든 것이다.
- 논리: 창 안에 있으면 중복이라 버리고, 없으면 처음 보는 것이라 결과에 담고 창에 넣는다.
- 논리: 창이 넘치면 캐시가 알아서 가장 오래 안 본 것을 버린다.

> **미끄러지는 창(sliding window)** — 전체가 아니라 최근 일정 개수/기간만 기억하는 방식.\
> 예: 메모리가 유한한 스트림 처리에서 "최근 1000개 중 중복 제거"처럼 범위를 한정한다.

**손으로 추적** — `deduplicateStream(3, {1, 2, 3, 1, 4, 1, 2})` → `[1, 2, 3, 4, 2]`

```
 용량 3. 줄은 [오래됨 ... 최근]

 x=1 : get(1)=null  -> 처음  out=[1]           put(1)   줄 [1]
 x=2 : get(2)=null  -> 처음  out=[1,2]         put(2)   줄 [1,2]
 x=3 : get(3)=null  -> 처음  out=[1,2,3]       put(3)   줄 [1,2,3]
 x=1 : get(1)=TRUE  -> 중복  건너뜀                     줄 [2,3,1]  <- 1 이 최근으로
 x=4 : get(4)=null  -> 처음  out=[1,2,3,4]     put(4)
                                                꽉 참 -> 맨 앞 2 버림   줄 [3,1,4]
 x=1 : get(1)=TRUE  -> 중복  건너뜀                     줄 [3,4,1]
 x=2 : get(2)=null  -> 처음  out=[1,2,3,4,2]   put(2)
                                                꽉 참 -> 맨 앞 3 버림   줄 [4,1,2]

 결과 [1, 2, 3, 4, 2]
        마지막 2 가 다시 나온 이유 : 창(최근 3개)에서 이미 밀려났기 때문이다
```

**`containsKey` 를 쓰면 결과가 달라진다**

```
 계약 (Cache.java)
     get(key)         : 값을 꺼낸다. 꺼내는 순간 그 키가 '가장 최근'으로 올라간다
     containsKey(key) : 있는지만 본다. 순서를 바꾸지 않고 통계에도 안 잡힌다

 같은 입력 {1, 2, 3, 1, 4, 1, 2}, 용량 3 을 containsKey 로 돌리면

 x=1 : 없다   out=[1]              put(1)   줄 [1]
 x=2 : 없다   out=[1,2]            put(2)   줄 [1,2]
 x=3 : 없다   out=[1,2,3]          put(3)   줄 [1,2,3]
 x=1 : 있다   건너뜀                        줄 [1,2,3]   <- 순서가 그대로다!
 x=4 : 없다   out=[1,2,3,4]        put(4)
                                    꽉 참 -> 맨 앞 1 버림  줄 [2,3,4]
 x=1 : 없다!  out=[1,2,3,4,1]      put(1)
                                    꽉 참 -> 맨 앞 2 버림  줄 [3,4,1]
 x=2 : 없다   out=[1,2,3,4,1,2]    put(2)
                                    꽉 참 -> 맨 앞 3 버림  줄 [4,1,2]

 결과 [1, 2, 3, 4, 1, 2]      <- 1 이 한 번 더 나온다. 정답 [1,2,3,4,2] 와 다르다

 무엇이 갈렸나
     get 을 쓰면 창의 의미가 "최근에 '본' capacity 개"
     containsKey 를 쓰면 창의 의미가 "최근에 '넣은' capacity 개"

     중복으로 걸러진 것은 넣지 않으므로, containsKey 방식에서는
     계속 나타나는 키라도 창에서 밀려난다 -> 다시 '처음 보는 것'이 된다
```

- 논리: 즉 **`get` 이 하는 순서 갱신이 "봤다"를 갱신하는 유일한 수단**이다.\
  `containsKey` 는 통계에도 안 잡히고 순서도 안 바꾸므로 "본 것"으로 기록되지 않는다.
- 논리: 이것이 이 챕터의 핵심 문장을 문제로 바꾼 것이다 — **"`get` 은 읽기가 아니다."**
- 논리: `containsKey` 가 계약에 따로 있는 이유도 여기서 드러난다.\
  "순서를 건드리지 않고 확인만 하고 싶을 때"를 위한 것이지, `get` 의 대체품이 아니다.

**창 크기가 답을 바꾼다**

```java
@Test
@DisplayName("창이 좁으면 놓친다")
void narrowWindowMisses() {
    // 용량 1 이면 바로 앞의 것만 기억한다.
    assertEquals(List.of(1, 2, 1, 2),
            LRUCacheProblems.deduplicateStream(1, new int[]{1, 2, 1, 2}));
    // 창이 넉넉하면 전부 잡는다.
    assertEquals(List.of(1, 2),
            LRUCacheProblems.deduplicateStream(4, new int[]{1, 2, 1, 2}));
}
```

```java
@Test
@DisplayName("창이 딱 맞아도 순환하면 못 잡는다")
void exactlyAtCapacity() {
    // 용량 2, 서로 다른 키 3개 순환. 다시 볼 때마다 이미 밀려나 있다.
    assertEquals(List.of(1, 2, 3, 1, 2, 3),
            LRUCacheProblems.deduplicateStream(2, new int[]{1, 2, 3, 1, 2, 3}));
}
```

- 논리: **같은 입력인데 용량에 따라 답이 다르다** — 이것이 "완전한 중복 제거"가 아니라는 뜻이다.
- 논리: `exactlyAtCapacity` 는 10번 질문의 순차 스캔과 **정확히 같은 현상**이다.\
  서로 다른 키 수(3)가 용량(2)보다 크면 순환할 때마다 전부 밀려나 하나도 못 잡는다.
- 한계: 정확한 중복 제거를 원하면 `HashSet` 에 전부 담아야 하고, 그러면 메모리가 **서로 다른 키 수에 비례**해 무한정 자란다.
- 한계: 이 풀이는 **메모리를 상수(capacity)로 고정하는 대신 정확성을 포기**한 것이다.\
  09번 트라이가 전부 기억해서 정확한 답을 냈던 것과 정확히 반대 방향의 거래다.
- 비용(왜): 시간 O(스트림 길이), 공간 O(capacity) — 100만 건 테스트가 20초 제한으로 돈다.
- 비용(왜): `large` 테스트가 두 방향을 검사한다.\
  `out.size() < stream.length`("중복이 하나도 안 걸렸다")와 `out.size() > 1000`("너무 많이 걸렀다").\
  둘 다 **틀린 구현을 양쪽에서 조인다**.

**질문별 답**

- Q: 문제 3을 어떻게 푸는가?\
  A: 용량 `capacity` 짜리 LRU 캐시를 "최근에 본 것들의 창"으로 쓴다.\
  `get(x)` 이 `null` 이면 창에 없는 것이라 결과에 담고 `put` 으로 창에 넣고, `null` 이 아니면 중복이라 건너뛴다.\
  창이 넘치면 캐시가 가장 오래 안 본 것을 알아서 버린다.

- Q: 왜 `containsKey` 가 아니라 `get` 을 써야 하는가?\
  A: `containsKey` 는 계약상 **순서를 바꾸지 않기** 때문이다.\
  창의 의미가 "최근에 **본** capacity 개"여야 하는데, `containsKey` 를 쓰면 중복으로 걸러진 접근이 기록되지 않아 창의 의미가 "최근에 **넣은** capacity 개"로 바뀐다.

- Q: 그 차이가 결과를 어떻게 바꾸는가?\
  A: `{1,2,3,1,4,1,2}` 를 용량 3으로 돌리면 `get` 은 `[1,2,3,4,2]` 를, `containsKey` 는 `[1,2,3,4,1,2]` 를 낸다.\
  중간의 `1` 이 `get` 에서는 최근으로 올라가 살아남지만, `containsKey` 에서는 순서가 그대로라 다음 `put` 때 밀려나고, 그 뒤에 다시 만난 `1` 이 "처음 보는 것"으로 출력된다.

---

### B. 자료구조의 특성

#### 4. LRU 캐시가 왜 필요한가 — 두 구조의 약점이 정확히 맞물린다

**질문**: 05-hash-map만으로는 "가장 오래된 것"을 왜 O(n)에만 알 수 있고, 02-linked-list만으로는 "이 키가 어디 있나"를 왜 O(n)에만 알 수 있는가. 둘을 겹치면 왜 정확히 서로의 약점이 메워지는가.

**필요한 연산 두 가지**

```
 캐시가 매 접근마다 답해야 하는 것

   (1) "이 키가 캐시에 있나? 있으면 값은?"       -> 조회
   (2) "꽉 찼다. 누가 가장 오래 안 쓰인 것인가?"  -> 축출 대상 찾기

 (1)은 '내용으로 찾기'이고 (2)는 '순서로 찾기'다
 두 질문의 종류가 다르다는 것이 이 챕터의 출발점이다
```

**해시맵만으로는**

```
 HashMap<K, V>

   key -> 해시 -> 버킷 번호     내용으로 찾기가 O(1)

   그런데 버킷 안에서의 배치는 '해시값'이 정한다
   언제 넣었는지, 언제 마지막으로 썼는지는 어디에도 기록되지 않는다

   "가장 오래된 것"을 알려면
     -> 모든 엔트리에 타임스탬프를 붙이고
     -> 전부 훑어 최솟값을 찾아야 한다     O(n)

   05번에서 본 그대로다 : 해시맵은 O(1)을 얻는 대가로 '순서'를 잃었다
```

**이중 연결 리스트만으로는**

```
 DoublyLinkedList<K>

   [오래됨] A <-> B <-> C <-> D [최근]

   "가장 오래된 것"은 맨 앞이다              O(1)
   맨 뒤에 붙이고 맨 앞을 떼는 것도          O(1)

   그런데 "키 C 가 어디 있나"를 물으면
     -> 앞에서부터 하나씩 비교하며 찾아야 한다   O(n)

   02번에서 본 그대로다 : 연결 리스트는 '위치를 계산할 수 없다'
```

| | `get` | `put` | 가장 오래된 것 찾기 |
|---|---|---|---|
| 해시맵만 | O(1) | O(1) | **O(n)** — 전부 봐야 안다 |
| 이중 연결 리스트만 | **O(n)** | O(1) | O(1) |
| 둘 다 | O(1) | O(1) | O(1) |

**왜 겹치면 정확히 메워지는가**

```
 두 구조가 못 하는 것이 서로 '정반대'다

   해시맵     : 내용 -> 위치     (O(1))   /  순서 -> 위치  (없음)
   연결 리스트 : 순서 -> 위치     (O(1))   /  내용 -> 위치  (없음)

 겹치는 방법 : 맵의 '값'을 값(V)이 아니라 '리스트의 노드'로 둔다

    index: Map<K, Node>                      list: head <-> ... <-> tail

      "C" ---------------------------------->  [ C ]
                                                 ^
      키로 노드를 O(1)에 찾는다  --------------+
      노드를 손에 쥐면 앞뒤 이웃을 알므로
      그 자리에서 떼고 뒤에 붙이는 것도 O(1)

 => 조회는 맵이, 순서는 줄이 담당하고
    '노드'가 두 세계를 잇는 다리가 된다
```

```java
private final Map<K, Node<K, V>> index = new HashMap<>();
//                    ^^^^^^^^^ 값이 V 가 아니라 Node 다

final Node<K, V> head = new Node<>();
final Node<K, V> tail = new Node<>();
```

- 논리: 이것이 README가 말하는 **"맵의 값이 값(V)이 아니라 노드라는 점이 핵심"** 이다.
- 논리: 맵의 값을 `V` 로 두면 조회는 되지만 그 값이 **줄의 어디에 있는지**를 모른다.\
  결국 줄을 훑어야 해서 O(n)이 된다.
- 논리: 두 구조가 **같은 노드 객체를 가리킨다**는 것도 중요하다.\
  복사본이 아니라 같은 객체라 한쪽에서 값을 고치면 다른 쪽에도 보인다.
- 한계: 대신 **두 곳을 동기화해야 한다** — 넣을 때도 지울 때도 양쪽을 건드려야 한다(8번).\
  한쪽만 건드리면 조용히 어긋난다.
- 비용(왜): 메모리도 두 배 가까이 든다 — 맵 엔트리 + 노드 객체(`key`, `value`, `prev`, `next`).

> **합성(composition)** — 서로 다른 자료구조를 겹쳐 각자의 강점만 쓰는 설계.\
> 예: LRU 캐시는 새 자료구조가 아니라 해시맵과 이중 연결 리스트의 합성이다.

- 논리: 07번 `MedianFinder` 가 최대 힙 + 최소 힙을 겹쳤던 것과 같은 설계다.\
  **하나로 안 되면 둘을 겹쳐 각자 잘하는 것만 시킨다.**

**질문별 답**

- Q: 해시맵만으로는 "가장 오래된 것"을 왜 O(n)에만 알 수 있는가?\
  A: 해시맵의 배치는 **해시값**이 정하므로 시간 정보가 어디에도 기록되지 않기 때문이다.\
  타임스탬프를 붙여도 최솟값을 찾으려면 전부 훑어야 한다 — 05번에서 O(1)을 얻는 대가로 순서를 잃은 그 지점이다.

- Q: 연결 리스트만으로는 "이 키가 어디 있나"를 왜 O(n)에만 알 수 있는가?\
  A: 노드의 위치를 **계산할 수 없어** 앞에서부터 따라가며 비교하는 수밖에 없기 때문이다.\
  배열처럼 인덱스로 주소를 구할 수 없는 것이 02번에서 본 연결 리스트의 성질이다.

- Q: 둘을 겹치면 왜 정확히 서로의 약점이 메워지는가?\
  A: 해시맵은 **내용 → 위치**를 O(1)로, 연결 리스트는 **순서 → 위치**를 O(1)로 주는데, 각자 못 하는 것이 서로의 강점이기 때문이다.\
  맵의 값을 `V` 가 아니라 **노드**로 두면 키로 노드를 O(1)에 찾고, 노드를 쥐면 줄에서 떼고 붙이는 것도 O(1)이라 두 세계가 이어진다.\
  노드가 두 자료구조를 잇는 다리다.

---

#### 5. 언제 적합하고 언제 쓰면 안 되는가 — "가정이지 정리가 아니다"

**질문**: 어떤 접근 패턴에 LRU가 적합하고 언제 쓰면 안 되는가. LRU가 서 있는 시간 지역성은 "가정이지 정리가 아니다"라는 말이 무슨 뜻인가.

**LRU가 서 있는 가정**

```java
/**
 * LRU(Least Recently Used)는 "가장 오래 안 쓴 것을 버린다"를 고른다.
 * 최근에 쓴 것을 또 쓸 가능성이 높다는 가정(시간 지역성) 위에 서 있다.
 * 가정이지 정리가 아니다. 순차 스캔에서는 이 가정이 정확히 반대로 틀린다.
 */
```

> **시간 지역성(temporal locality)** — 최근에 접근한 데이터를 곧 다시 접근할 가능성이 높다는 경험적 성질.\
> 예: 웹 서비스에서 방금 조회된 상품이 몇 초 안에 또 조회되는 일이 흔하다.

**"가정이지 정리가 아니다"의 뜻**

```
 정리(theorem) : 전제가 참이면 반드시 참이다. 반례가 존재할 수 없다
                 예) "완전 이진 트리의 높이는 floor(log2 n) 이다"
                     -- 이것은 구조에서 증명된다

 가정(assumption) : 대개 그렇더라는 경험적 관찰이다. 반례가 존재한다
                    예) "최근에 쓴 것을 또 쓸 것이다"
                        -- 워크로드에 따라 참일 수도 거짓일 수도 있다

 무엇이 달라지는가
   정리 위에 세운 성질은 '항상' 성립한다 -> 최악의 경우를 걱정할 필요가 없다
   가정 위에 세운 성질은 '보통' 성립한다 -> 가정이 깨지는 워크로드를 따로 알아야 한다

 LRU 의 O(1) 은 정리다 (자료구조에서 나온다)
 LRU 의 '좋은 적중률' 은 가정이다 (워크로드에서 나온다)

 => "O(1) 이니까 좋다"와 "적중률이 좋다"는 완전히 다른 종류의 주장이다
```

- 논리: 이 구분이 실무에서 중요한 이유는 **테스트가 가정을 검증하지 않기** 때문이다.\
  단위 테스트는 O(1)과 정확성을 확인하지만, 적중률은 실제 워크로드로만 알 수 있다.
- 논리: 07번 힙의 "부모 ≤ 자식"은 정리였고(구조가 보장한다), 여기 "최근 것이 또 쓰인다"는 관찰이다.

**적합한 패턴**

- 논리: **소수의 인기 키에 접근이 몰리는** 경우(멱함수 분포·80:20).\
  상품 상세 조회, 인기 게시글, 자주 쓰는 설정값.
- 논리: 같은 키를 **짧은 시간 안에 반복**해서 쓰는 경우 — 세션 데이터, 렌더링 중 반복 조회.
- 논리: 뒤에 **비싼 저장소**가 있는 경우 — DB 쿼리, 네트워크 호출, 디스크 읽기.\
  캐시의 이득은 "미스 한 번의 비용 x 절약한 횟수"다.
- 논리: 작업 집합(working set)이 캐시 용량보다 **작은** 경우.

> **작업 집합(working set)** — 어떤 기간 동안 실제로 접근되는 서로 다른 키의 집합.\
> 예: 작업 집합이 캐시 용량보다 작으면 거의 다 적중하고, 크면 계속 밀려난다.

**쓰면 안 되는 패턴**

- 한계: **순차 스캔** — 전체를 한 번씩 훑는 배치 작업, 큰 테이블 full scan.\
  가정이 정확히 반대로 틀려 적중률 0%가 나올 수 있다(10번).
- 한계: **접근이 균등 분포**인 경우 — 어떤 키든 같은 확률이면 최근성이 아무 정보도 아니다.
- 한계: **접근 빈도**가 중요한데 최근성만 보는 경우.\
  하루에 1000번 쓰이는 키가, 방금 한 번 쓰인 키들에 밀려 나갈 수 있다 → LFU가 맞는 자리다.
- 한계: 한 번 쓰고 다시 안 쓰는 대량 데이터가 섞여 들어오는 경우(**캐시 오염**).\
  로그 처리 배치 하나가 캐시 전체를 쓸어낸다.

> **캐시 오염(cache pollution)** — 다시 쓰이지 않을 데이터가 캐시를 채워 정작 필요한 것을 밀어내는 현상.\
> 예: 야간 배치가 전체 테이블을 훑고 나면 아침의 캐시가 텅 비어 있다.

> **스캔 저항(scan resistance)** — 한 번만 읽히는 대량 데이터가 캐시를 밀어내지 못하게 막는 성질.\
> 예: 실무 캐시(ARC, 2Q, Caffeine의 W-TinyLFU)는 "두 번 이상 쓰인 것"만 주 영역에 올려 이 문제를 막는다.

**다른 정책들과의 비교**

| 정책 | 버리는 기준 | 강점 | 약점 |
|---|---|---|---|
| LRU | 가장 오래 안 쓴 것 | 시간 지역성이 있으면 좋다 · 구현이 단순 | 순차 스캔에 무너진다 |
| LFU | 가장 적게 쓴 것 | 인기 키를 지킨다 | 옛 인기 키가 눌러앉는다(노화 필요) |
| FIFO | 가장 먼저 들어온 것 | 가장 단순 | 재사용을 아예 무시한다 |
| Random | 무작위 | 최악이 없다 · 메타데이터 0 | 좋은 경우도 없다 |
| OPT | 가장 나중에 쓸 것 | 이론적 최적 | 미래를 알아야 해 구현 불가 |

- 논리: **어떤 정책도 모든 워크로드에서 최선일 수 없다**.\
  정책 선택은 워크로드에 대한 베팅이다.
- 논리: 그래서 실무 캐시는 정책을 섞거나 적응형으로 만든다(ARC는 LRU와 LFU 사이를 자동 조절한다).\
  (원본에 근거 없음 — 내 추론)

**질문별 답**

- Q: 어떤 접근 패턴에 적합한가?\
  A: 소수의 인기 키에 접근이 몰리고(멱함수 분포), 같은 키를 짧은 시간 안에 반복해서 쓰며, 작업 집합이 캐시 용량보다 작고, 뒤에 비싼 저장소(DB·네트워크·디스크)가 있는 경우다.

- Q: 언제 쓰면 안 되는가?\
  A: 순차 스캔(가정이 반대로 틀린다), 균등 분포(최근성이 아무 정보도 아니다), 최근성보다 **빈도**가 중요한 경우(LFU가 맞다), 한 번 쓰고 마는 대량 데이터가 섞여 캐시를 오염시키는 경우다.

- Q: "가정이지 정리가 아니다"가 무슨 뜻인가?\
  A: LRU의 `O(1)` 은 자료구조에서 **증명되는 정리**라 반례가 없지만, "좋은 적중률"은 워크로드에 대한 **경험적 가정**이라 반례가 존재한다는 뜻이다.\
  정리 위에 선 성질은 최악을 걱정할 필요가 없지만, 가정 위에 선 성질은 **가정이 깨지는 워크로드를 따로 알아야** 한다.\
  단위 테스트는 O(1)과 정확성은 검증하지만 적중률은 검증하지 않는다는 점도 여기서 나온다.

---

#### 6. 모든 연산이 O(1)인 구조적 이유 — 맵의 값이 노드여야 하는 이유

**질문**: `get`/`put`/축출이 모두 O(1)인 구조적 이유는 무엇인가. 맵의 값이 값(V)이 아니라 **노드**여야 하는 이유는, 그리고 그것이 02번의 "노드를 알면 O(1), 인덱스로 찾으면 O(n)"과 어떻게 같은 이야기인가.

**impl 코드**

```java
@Override
public V get(K key) {
    Node<K, V> node = index.get(key);
    if (node == null) {
        misses++;
        return null;
    }
    hits++;
    unlink(node);
    linkLast(node);
    return node.value;
}
```

```java
private void unlink(Node<K, V> node) {
    node.prev.next = node.next;
    node.next.prev = node.prev;
    node.prev = null;
    node.next = null;
}

private void linkLast(Node<K, V> node) {
    node.prev = tail.prev;
    node.next = tail;
    tail.prev.next = node;
    tail.prev = node;
}
```

**`get` 의 세 단계가 전부 O(1)**

```
 (1) index.get(key)      -> 해시 계산 + 버킷 접근        O(1) 평균
 (2) unlink(node)        -> 링크 4개 대입                O(1)
 (3) linkLast(node)      -> 링크 4개 대입                O(1)

 (2)의 그림

   전 : ... <-> P <-> [N] <-> Q <-> ...
                       ^ 떼어낼 노드

        node.prev.next = node.next     P.next = Q
        node.next.prev = node.prev     Q.prev = P
        node.prev = null               N 의 앞 끊기
        node.next = null               N 의 뒤 끊기

   후 : ... <-> P <-> Q <-> ...        그리고 N 은 혼자 떠 있다

   중요 : 훑지 않았다. node 를 '이미 손에 쥐고 있어서' 이웃을 바로 안다

 (3)의 그림

   전 : ... <-> Z <-> [tail]

        node.prev = tail.prev          N.prev = Z
        node.next = tail               N.next = tail
        tail.prev.next = node          Z.next = N
        tail.prev = node               tail.prev = N

   후 : ... <-> Z <-> N <-> [tail]
```

- 논리: `unlink` 가 O(1)인 유일한 근거는 **노드를 이미 갖고 있다**는 것이다.\
  "키가 어디 있는지 찾는" 단계가 이미 맵에서 끝났기 때문이다.
- 논리: `put` 도 같다 — 기존 키면 맵에서 노드를 찾아 `unlink`+`linkLast`, 새 키면 노드를 만들어 `linkLast`.
- 논리: 축출이 O(1)인 이유는 **버릴 대상의 위치가 고정**이기 때문이다.

```java
if (index.size() == capacity) {
    Node<K, V> oldest = head.next;     // 위치가 고정이다. 찾지 않는다
    index.remove(oldest.key);
    unlink(oldest);
    evictions++;
}
```

- 논리: `head.next` 가 항상 가장 오래된 것이다 — 07번 힙에서 `elements[0]` 이 항상 1등이던 것과 같은 구조다.\
  **찾을 필요가 없어서 O(1)** 이지 빨리 찾아서가 아니다.
- 논리: `oldest.key` 가 필요하기 때문에 노드가 `key` 필드를 들고 있다.\
  줄에서 뗄 때 **맵에서도 지워야 하는데**, 노드만 있고 키를 모르면 맵에서 못 지운다(8번).

**맵의 값이 `V` 가 아니라 `Node` 여야 하는 이유**

```
 (A) Map<K, V> 를 쓴다면

     get(key) -> 값은 O(1)에 나온다
     그런데 "그 키의 노드가 줄의 어디에 있나"를 모른다
     순서를 갱신하려면 줄을 앞에서부터 훑어 그 키를 찾아야 한다   O(n)

     => get 이 O(n) 이 된다. 캐시의 의미가 없다

 (B) Map<K, Node> 를 쓴다면 (impl)

     index.get(key) -> 노드가 O(1)에 나온다
     노드에는 value 도 있고 prev/next 도 있다
     -> 값도 얻고 줄 조작도 즉시 가능하다                        O(1)

 핵심 : 맵이 돌려주는 것이 '값'이 아니라 '줄 위의 자리' 여야 한다
        Node 는 값과 자리를 함께 들고 있는 물건이다
```

```java
static final class Node<K, V> {
    K key;      // 축출할 때 맵에서 지우려고 필요하다
    V value;    // 실제 값
    Node<K, V> prev;
    Node<K, V> next;
}
```

> **간접 참조(handle)** — 데이터 자체가 아니라 "그 데이터가 있는 자리"를 가리키는 값.\
> 예: `Map<K, Node>` 의 `Node` 가 핸들이고, 이것을 쥐고 있어야 줄 조작이 O(1)이 된다.

**02번의 "노드를 알면 O(1), 인덱스로 찾으면 O(n)"과 같은 이야기인 이유**

```
 02-linked-list 에서 배운 것

   list.remove(index)      -> index 번째 노드를 찾아가야 한다      O(n)
   list.remove(node)       -> 노드를 이미 알면 링크 4개면 끝       O(1)

   즉 연결 리스트의 O(1) 은 '조작'의 비용이지 '찾기'의 비용이 아니다
   찾는 단계가 O(n) 이라 밖에서 보면 전체가 O(n) 이 된다

 10-lru-cache 가 한 일

   '찾기' 단계를 연결 리스트에서 떼어내 해시맵에 맡긴다

       찾기 : index.get(key)  -> O(1)    (해시맵의 강점)
       조작 : unlink/linkLast -> O(1)    (연결 리스트의 강점)

   => 02번의 O(1) 이 처음으로 '진짜 O(1)' 이 되는 자리다
      02번에서 "노드를 알면"이라는 전제를 달았던 그 전제를 만들어 준 것이다

 07번 힙과의 대비도 같은 구조다
   힙은 임의의 키를 못 찾아서(O(n)) decrease-key 를 못 했다
   해법도 같았다 : 위치 맵을 따로 두는 것 (07번 3·10번)
```

- 논리: **"O(1) 연산"이라는 말에는 늘 전제가 붙는다** — 그 전제를 누가 만들어 주느냐가 설계다.
- 논리: 이 챕터가 02번과 05번을 동시에 다시 부르는 이유가 이것이다.\
  둘 다 혼자서는 전제를 못 만들고, 겹쳐야 만들어진다.
- 비용(왜): `HashMap` 의 O(1)은 **평균**이다 — 해시 충돌이 심하면 나빠질 수 있다.\
  자바 8 이후로는 버킷이 트리로 바뀌어 최악 O(log n)이다.\
  (원본에 근거 없음 — 내 추론)
- 한계: 노드 객체가 필드 4개(`key`, `value`, `prev`, `next`)를 들어 메모리가 더 든다.\
  `Map<K,V>` 라면 값 하나만 들면 됐다 — O(1)을 산 값이다.

**질문별 답**

- Q: `get`/`put`/축출이 모두 O(1)인 구조적 이유는?\
  A: 세 연산 모두 **"찾기"를 해시맵이 O(1)에 끝내 주고, 남은 "조작"이 링크 몇 개 대입이기 때문**이다.\
  축출은 대상 위치가 `head.next` 로 **고정**이라 찾는 단계조차 없다 — 07번 힙의 `elements[0]` 과 같은 구조다.

- Q: 맵의 값이 `V` 가 아니라 노드여야 하는 이유는?\
  A: 맵이 돌려줘야 하는 것이 값이 아니라 **줄 위의 자리**이기 때문이다.\
  `Map<K,V>` 면 값은 O(1)에 얻지만 그 키가 줄의 어디인지 몰라 순서 갱신에 O(n)이 들어 캐시의 의미가 없어진다.\
  `Node` 는 값(`value`)과 자리(`prev`/`next`)와 키(`key`, 축출 시 맵에서 지우려고)를 함께 들고 있는 물건이다.

- Q: 02번의 "노드를 알면 O(1), 인덱스로 찾으면 O(n)"과 어떻게 같은 이야기인가?\
  A: 02번에서 연결 리스트의 O(1)은 **조작의 비용**이었고, "노드를 알면"이라는 전제가 붙어 있었다 — 찾는 단계가 O(n)이라 밖에서 보면 전체가 O(n)이었다.\
  LRU 캐시는 그 **전제를 해시맵이 만들어 주게** 한 것이다.\
  찾기는 맵, 조작은 줄 — 02번의 O(1)이 처음으로 진짜 O(1)이 되는 자리다.

---

#### 7. 센티넬 두 개가 없애 주는 검사

**질문**: `head`/`tail` 센티넬 두 개는 어떤 검사를 없애 주는가. 02번에서는 안 썼던 장치가 왜 여기서 값을 하는가 — 센티넬이 없다면 `unlink`/`linkLast` 에 무엇이 더 붙는가.

**센티넬의 설치**

```java
final Node<K, V> head = new Node<>();
final Node<K, V> tail = new Node<>();

public LRUCache(int capacity) {
    if (capacity < 1) {
        throw new IllegalArgumentException("용량은 1 이상이어야 한다: " + capacity);
    }
    this.capacity = capacity;
    head.next = tail;
    tail.prev = head;
}
```

```
 빈 캐시                    [head] <-> [tail]          <- 둘이 서로를 가리킨다

 원소 하나                  [head] <-> A <-> [tail]

 원소 셋                    [head] <-> A <-> B <-> C <-> [tail]
                             ^^^^^^                      ^^^^^^
                             값이 없다. 자리만 지킨다

 핵심 성질 : 실제 원소는 '반드시' 앞뒤 이웃을 하나씩 갖는다
             A 의 앞은 head, C 의 뒤는 tail -- null 이 될 수 없다
```

> **센티넬(sentinel, 보초 노드)** — 값을 담지 않고 경계만 지키는 더미 노드.\
> 예: 리스트 양 끝에 하나씩 두면 모든 실제 노드가 앞뒤 이웃을 반드시 갖게 되어 `null` 검사가 사라진다.

**센티넬이 없애 주는 검사**

```
 센티넬이 없다면 (head/tail 이 '첫 노드/마지막 노드'를 직접 가리키는 방식)

 unlink(node) 에 붙어야 하는 것

   if (node.prev == null) {          // 이게 첫 노드인가?
       head = node.next;             // 그러면 head 를 갱신해야 한다
   } else {
       node.prev.next = node.next;
   }
   if (node.next == null) {          // 이게 마지막 노드인가?
       tail = node.prev;             // 그러면 tail 을 갱신해야 한다
   } else {
       node.next.prev = node.prev;
   }
   // 원소가 하나뿐이었다면 head 와 tail 이 둘 다 null 이 되어야 한다

   => 분기 4개 + 리스트가 비는 경우

 linkLast(node) 에 붙어야 하는 것

   if (tail == null) {               // 리스트가 비었나?
       head = tail = node;           // 첫 노드는 특별 취급
   } else {
       node.prev = tail;
       tail.next = node;
       tail = node;
   }

   => 분기 1개 + head/tail 갱신

 센티넬이 있으면 (impl)

   unlink   : 대입 4줄. 분기 0개
   linkLast : 대입 4줄. 분기 0개

   왜 : node.prev 와 node.next 가 절대 null 이 아니고
        head/tail 이 절대 바뀌지 않기 때문이다 (final 이다!)
```

- 논리: `head`/`tail` 이 `final` 로 선언된 것이 그 증거다 — **한 번 만들면 영영 안 바뀐다**.\
  센티넬이 없으면 첫/마지막 원소가 바뀔 때마다 갱신해야 해서 `final` 일 수 없다.
- 논리: 분기가 없다는 것은 **틀릴 자리가 없다**는 뜻이기도 하다.\
  경계 케이스(빈 리스트, 원소 하나)가 일반 케이스와 같은 코드로 처리된다.

**`clear()` 도 두 줄로 끝난다**

```java
@Override
public void clear() {
    index.clear();
    head.next = tail;
    tail.prev = head;
}
```

- 논리: 센티넬을 다시 이어 주기만 하면 줄이 빈 상태가 된다 — 노드들을 하나씩 끊을 필요가 없다.\
  참조가 끊긴 노드들은 GC가 가져간다.

**02번에서는 왜 안 썼고 여기서는 왜 값을 하는가**

```
 02-linked-list 의 연산       : add(index), remove(index), get(index) ...
   -> 인덱스로 접근한다. 매번 앞에서부터 훑어 간다
   -> 경계 검사(빈 리스트, 첫/마지막)가 '훑는 로직 안'에 어차피 섞인다
   -> 센티넬을 넣어도 없앨 수 있는 분기가 상대적으로 적다
   -> 그리고 학습 목적상 경계 처리를 직접 겪어보는 것이 요점이었다

 10-lru-cache 의 연산        : unlink(node), linkLast(node)
   -> '임의의 노드를 떼어 맨 뒤로 옮긴다'가 거의 모든 연산의 본체다
   -> get 마다, put 마다, 축출마다 불린다 (가장 뜨거운 경로)
   -> 그 노드가 첫 노드인지 마지막 노드인지가 매번 다르다
   -> 분기가 없으면 코드가 짧아질 뿐 아니라 '틀릴 자리'가 사라진다

 => 센티넬의 값은 '중간에서 임의 노드를 자주 떼고 붙이는' 워크로드에서 나온다
    그 워크로드가 이 챕터에서 처음 나온다
```

- 논리: 즉 센티넬은 **연산의 모양이 바뀌어서** 값을 하게 된 것이다.\
  같은 자료구조라도 어떤 연산을 자주 하느냐에 따라 필요한 장치가 달라진다.

**테스트가 센티넬을 직접 검사한다**

```java
@Test
@DisplayName("센티넬은 결과에 안 들어간다")
void sentinelsAreInvisible() {
    LRUCache<Integer, String> c = lru(3);
    assertEquals(List.of(), c.keysInOrder());
    assertNull(c.head.key, "head 는 값을 담지 않는다");
    assertNull(c.tail.key, "tail 은 값을 담지 않는다");
    c.put(1, "a");
    assertEquals(List.of(1), c.keysInOrder());
    assertSame(c.head.next, c.tail.prev, "원소가 하나면 같은 노드여야 한다");
}
```

```java
@Override
public List<K> keysInOrder() {
    List<K> out = new ArrayList<>(index.size());
    for (Node<K, V> cur = head.next; cur != tail; cur = cur.next) {
        out.add(cur.key);
    }
    return out;
}
```

- 논리: 순회 조건이 `cur != tail` 이라 센티넬이 자연스럽게 제외된다.\
  `head.next` 에서 시작하고 `tail` 전에서 멈춘다.
- 논리: `emptyLinksSentinels` 테스트는 **다 지운 뒤 처음 상태로 돌아오는지**를 본다.\
  `head.next == tail && tail.prev == head` — 센티넬 불변식이다.
- 한계: 센티넬 노드 2개만큼 메모리가 더 든다 — 무시할 만한 값이다.
- 한계: `head.key` 와 `tail.key` 가 `null` 이므로, 실수로 센티넬을 결과에 넣으면 `null` 키가 섞여 나온다.\
  테스트가 그것을 명시적으로 확인한다.

**질문별 답**

- Q: 센티넬 두 개는 어떤 검사를 없애 주는가?\
  A: **"이게 첫 노드인가"**, **"이게 마지막 노드인가"**, **"리스트가 비었나"** 세 가지다.\
  모든 실제 노드가 앞뒤 이웃을 반드시 갖게 되어 `node.prev`/`node.next` 가 절대 `null` 이 아니고, `head`/`tail` 이 절대 바뀌지 않아 `final` 로 둘 수 있다.

- Q: 센티넬이 없다면 `unlink`/`linkLast` 에 무엇이 더 붙는가?\
  A: `unlink` 에는 "첫 노드면 `head` 갱신 / 마지막 노드면 `tail` 갱신"이라는 분기 네 개와 원소가 하나뿐이던 경우의 처리가 붙는다.\
  `linkLast` 에는 "리스트가 비었으면 `head`/`tail` 을 둘 다 이 노드로" 라는 분기가 붙는다.\
  센티넬이 있으면 둘 다 **분기 0개, 대입 4줄**로 끝난다.

- Q: 02번에서는 안 썼던 장치가 왜 여기서 값을 하는가?\
  A: **연산의 모양이 다르기** 때문이다.\
  02번은 인덱스로 접근해 어차피 훑는 로직 안에 경계 처리가 섞였고, 학습상 그것을 직접 겪는 것이 목적이었다.\
  여기서는 "임의의 노드를 떼어 맨 뒤로 옮긴다"가 `get`·`put`·축출 전부의 본체이고 가장 뜨거운 경로라, 그 노드가 첫/마지막인지가 매번 달라진다.\
  분기가 사라지면 코드가 짧아질 뿐 아니라 **틀릴 자리가 사라진다**.

---

#### 8. 맵과 줄 양쪽에서 지워야 하는 이유 — 왜 이 버그는 조용한가

**질문**: 축출할 때 맵과 줄 양쪽에서 지워야 하는 이유는. 맵에만 남기면 무슨 일이 생기고, 줄에만 남기면 `keysInOrder` 와 `size` 가 어떻게 어긋나는가. 왜 이 버그는 조용한가.

**impl 코드 — 양쪽을 건드리는 자리**

```java
// 축출
if (index.size() == capacity) {
    Node<K, V> oldest = head.next;
    index.remove(oldest.key);      // (1) 맵에서
    unlink(oldest);                // (2) 줄에서
    evictions++;
}
```

```java
// remove
@Override
public V remove(K key) {
    Node<K, V> node = index.remove(key);   // (1) 맵에서
    if (node == null) {
        return null;
    }
    V old = node.value;
    unlink(node);                          // (2) 줄에서
    return old;
}
```

- 논리: 같은 데이터가 **두 자료구조에 동시에 존재**하므로, 지울 때도 두 곳을 지워야 한다.\
  이것이 4번의 "겹치기"가 치르는 대가다.
- 논리: `oldest.key` 를 쓰려고 노드가 `key` 필드를 드는 것도 여기서 필요해진다.\
  줄에서 찾은 노드를 맵에서 지우려면 키를 알아야 하기 때문이다.

**한쪽만 지우면**

```
 (A) 줄에서만 떼고 맵에 남기면

     index : {1 -> N1, 2 -> N2, 3 -> N3}        <- 3개
     줄    : [head] <-> N2 <-> N3 <-> [tail]    <- 2개 (N1 이 떨어져 나감)

     증상
       size()          = index.size() = 3       <- 맵 기준
       keysInOrder()   = [2, 3]                 <- 줄 기준, 길이 2
       -> size 와 keysInOrder().size() 가 어긋난다

       containsKey(1)  = true                   <- 있다고 한다
       get(1)          = N1 을 돌려준다
                         그리고 unlink(N1) 을 부른다!
                         N1.prev 와 N1.next 가 이미 null 이라 -> NullPointerException
                         (또는 이미 끊긴 노드를 엉뚱한 곳에 다시 이어 줄을 망가뜨린다)

       그리고 1 은 영원히 맵에 남는다 -- 축출로는 다시 못 골라진다
       (축출은 head.next 만 보는데 N1 은 줄에 없으므로)
       => 메모리 누수 + 영원히 낡은 값

 (B) 맵에서만 지우고 줄에 남기면

     index : {2 -> N2, 3 -> N3}                 <- 2개
     줄    : [head] <-> N1 <-> N2 <-> N3 <-> [tail]   <- 3개

     증상
       size()          = 2
       keysInOrder()   = [1, 2, 3]              <- size 보다 길다
       containsKey(1)  = false
       -> "줄에는 있는데 맵에는 없는 키"가 생긴다

       다음 축출 때 head.next = N1 을 고른다
         index.remove(1) -> 이미 없다. 아무 일도 안 일어난다
         unlink(N1)      -> 줄에서만 빠진다
         evictions++     -> 그런데 실제로 캐시에서 빠진 것은 없다
       => 축출이 '빈 방을 치우고' 끝나 진짜 축출이 안 일어난다
          그러면 size 가 capacity 를 넘어설 수 있다
```

- 논리: 두 경우 모두 **불변식**이 깨진 것이다 — "맵의 키 집합 = 줄의 키 집합".
- 논리: 이 불변식이 깨지면 `size`, `keysInOrder`, `containsKey`, 축출이 **서로 다른 진실을 말하기 시작한다**.

> **불변식(invariant)** — 자료구조가 연산 사이에 항상 참으로 유지해야 하는 조건.\
> 예: 이 캐시의 불변식은 "맵에 있는 키의 집합과 줄에 있는 키의 집합이 정확히 같다"이다.

**왜 이 버그는 조용한가**

```
 1. 예외가 안 난다 (대부분의 경우)
      맵도 줄도 각자 '자기 안에서는' 멀쩡하다
      맵을 읽는 연산은 맵의 답을, 줄을 읽는 연산은 줄의 답을 준다
      둘을 '대조하지 않으면' 아무 문제도 보이지 않는다

 2. 겉으로 드러나는 연산이 대체로 맞아 보인다
      get/put 은 맵만 보고 동작한다 -> 값은 계속 잘 나온다
      keysInOrder 는 줄만 보고 동작한다 -> 순서도 그럴듯하다

 3. 어긋남이 '누적'된다
      한 번 어긋나면 그 상태에서 계속 연산이 쌓인다
      한참 뒤에 메모리가 새거나, size 가 용량을 넘거나,
      줄이 끊겨 NullPointerException 이 나서야 발견된다
      -> 증상이 나타난 지점과 원인 지점이 멀다

 4. 소규모 테스트는 통과한다
      축출이 한 번도 안 일어나면 (넣은 개수 <= 용량)
      이 버그는 절대 안 드러난다
```

- 논리: 이것이 **조용한 실패(silent failure)** 의 전형이다 — 에러 없이 정상처럼 돌면서 상태만 틀어진다.
- 논리: 그래서 테스트가 **매 연산마다 둘을 대조한다**.

```java
@Test
@DisplayName("축출이 양쪽에서 일어난다")
void evictionTouchesBoth() {
    // 맵에서만 지우고 줄에 남겨두면 keysInOrder 가 size 보다 길어진다.
    // 줄에서만 떼고 맵에 남겨두면 그 키가 영원히 살아 있게 된다.
    LRUCache<Integer, String> c = lru(3);
    for (int i = 0; i < 100; i++) {
        c.put(i, "v" + i);
        assertEquals(c.size(), c.keysInOrder().size(),
                "맵 크기와 줄 길이가 어긋났다 (i=" + i + ")");
        assertSound(c);
    }
    assertEquals(3, c.size());
    assertEquals(List.of(97, 98, 99), c.keysInOrder());
}
```

- 논리: `put` 한 번마다 대조하므로 **어긋난 첫 순간**을 잡는다 — `i=` 를 메시지에 넣은 이유다.
- 논리: 100번 반복해 축출이 97번 일어나게 만든 것도 의도적이다.\
  용량 3에 100개를 넣으므로 축출 경로를 반드시 지난다.

**`assertSound` — 더 깊은 검사**

```java
private void assertSound(LRUCache<Integer, String> c) {
    List<Integer> forward = new ArrayList<>();
    for (LRUCache.Node<Integer, String> n = c.head.next; n != c.tail; n = n.next) {
        assertNotNull(n, "앞으로 훑다가 null 을 만났다. 줄이 끊겼다");
        forward.add(n.key);
        assertTrue(forward.size() <= c.size() + 1, "고리가 생겼다. 무한히 돈다");
    }
    List<Integer> backward = new ArrayList<>();
    for (LRUCache.Node<Integer, String> n = c.tail.prev; n != c.head; n = n.prev) {
        assertNotNull(n, "뒤로 훑다가 null 을 만났다. prev 링크가 안 이어져 있다");
        backward.add(n.key);
        assertTrue(backward.size() <= c.size() + 1, "뒤쪽에 고리가 생겼다");
    }
    List<Integer> reversed = new ArrayList<>(backward);
    java.util.Collections.reverse(reversed);
    assertEquals(forward, reversed, "앞으로 훑은 것과 뒤로 훑은 것이 서로의 역순이 아니다");
    assertEquals(c.size(), forward.size(), "맵의 크기와 줄의 길이가 다르다");
    assertEquals(forward, c.keysInOrder());
}
```

- 논리: **앞으로 훑은 결과와 뒤로 훑은 결과가 서로의 역순**이어야 한다.\
  이것을 안 보면 `prev` 링크를 제대로 안 고치는 구현도 대부분의 테스트를 통과한다(주석에 그렇게 적혀 있다).
- 논리: `forward.size() <= c.size() + 1` 이 **고리(cycle) 탐지**다.\
  링크를 잘못 이어 순환이 생기면 루프가 안 끝나므로, 개수 상한으로 무한 루프를 막는다.
- 논리: 02번 `DoublyLinkedList` 의 `assertSound` 와 같은 검사다 — 같은 종류의 버그를 같은 방법으로 잡는다.

**떼어낸 노드를 완전히 끊는 이유**

```java
private void unlink(Node<K, V> node) {
    node.prev.next = node.next;
    node.next.prev = node.prev;
    node.prev = null;      // 이 두 줄이 없어도 줄은 멀쩡하다
    node.next = null;      // 그런데 왜 있는가?
}
```

```java
@Test
@DisplayName("밀려난 노드는 줄을 붙들고 있지 않는다")
void evictedNodeIsCut() {
    LRUCache<Integer, String> c = lru(2);
    c.put(1, "a");
    LRUCache.Node<Integer, String> first = c.head.next;
    c.put(2, "b");
    c.put(3, "c");          // 1 이 밀려난다

    assertNull(first.prev, "떼어낸 노드가 앞을 붙들고 있으면 줄 전체가 GC 되지 않는다");
    assertNull(first.next);
    assertSound(c);
}
```

- 논리: 떼어낸 노드가 `prev`/`next` 를 붙들고 있으면, 바깥에서 그 노드 하나를 참조하는 것만으로 **줄 전체가 GC되지 않는다**.
- 논리: 노드 하나가 살아 있으면 그 이웃, 그 이웃의 이웃… 이 줄줄이 끌려온다.\
  01번의 "지운 자리의 참조를 null로"와 07번의 `elements[size] = null` 과 같은 규칙이다.

**질문별 답**

- Q: 왜 양쪽에서 지워야 하는가?\
  A: 같은 데이터가 **맵과 줄 두 곳에 동시에 존재**하고, "맵의 키 집합 = 줄의 키 집합"이 이 자료구조의 불변식이기 때문이다.\
  한쪽만 지우면 `size`·`keysInOrder`·`containsKey`·축출이 서로 다른 진실을 말하기 시작한다.

- Q: 맵에만 남기면 무슨 일이 생기는가?\
  A: 그 키가 **영원히 캐시에 살아 있게** 된다 — 축출은 `head.next` 만 보는데 그 노드는 줄에 없으므로 다시 골라질 수 없다.\
  `containsKey` 는 true를 주고, `get` 을 부르면 이미 끊긴 노드에 `unlink` 를 시도해 `NullPointerException` 이 나거나 줄을 망가뜨린다.\
  메모리 누수이면서 영원히 낡은 값이 남는다.

- Q: 줄에만 남기면 `keysInOrder` 와 `size` 가 어떻게 어긋나는가?\
  A: `size()` 는 맵 크기를 세고 `keysInOrder()` 는 줄을 훑으므로, **`keysInOrder().size()` 가 `size()` 보다 커진다**.\
  게다가 다음 축출이 그 유령 노드를 골라 "빈 방을 치우고" 끝나므로 실제 축출이 안 일어나 용량을 넘어설 수 있다.

- Q: 왜 이 버그는 조용한가?\
  A: 맵도 줄도 **각자 자기 안에서는 멀쩡해서** 둘을 대조하지 않으면 아무 문제도 안 보이기 때문이다.\
  `get`/`put` 은 맵만 보고 잘 동작하고 `keysInOrder` 는 줄만 보고 그럴듯한 답을 준다.\
  어긋남이 누적되다 한참 뒤에 메모리 누수나 `NullPointerException` 으로 터져 **증상 지점과 원인 지점이 멀고**, 축출이 한 번도 안 일어나는 작은 테스트는 그냥 통과한다.\
  그래서 테스트가 `put` 한 번마다 `size` 와 줄 길이를 대조하고 앞뒤 순회의 역순 일치까지 본다.

---

#### 9. "`get` 은 읽기가 아니다" — 이 챕터의 핵심

**질문**: 왜 핵심인가. `ThreadSafeLRUCache` 가 `ReadWriteLock` 의 읽기 잠금을 못 쓰는 이유, 그리고 그 손상이 왜 다음 순회에서야 무한 루프로 드러나는가. `try/finally` 를 빠뜨리면 왜 예외 한 번이 프로세스 전체를 세우는가.

**`get` 이 하는 일**

```java
@Override
public V get(K key) {
    Node<K, V> node = index.get(key);
    if (node == null) {
        misses++;              // 쓰기 1 : 통계
        return null;
    }
    hits++;                    // 쓰기 2 : 통계
    unlink(node);              // 쓰기 3 : 링크 4개
    linkLast(node);            // 쓰기 4 : 링크 4개
    return node.value;
}
```

```
 이름은 get 인데 실제로 바뀌는 것

   통계 카운터 (hits 또는 misses)
   떼어낸 자리의 앞뒤 노드 링크 : 2개
   떼어낸 노드 자신의 링크      : 2개
   붙인 자리의 앞뒤 링크        : 2개
   붙인 노드 자신의 링크        : 2개
   -> 링크만 8개 대입 (unlink 4 + linkLast 4)

 계약에도 그렇게 적혀 있다 (Cache.java)
   "이 메서드는 읽기가 아니다. 꺼내는 순간 그 키가 '가장 최근'으로 올라간다.
    상태를 바꾸므로 여러 스레드가 동시에 부르면 깨진다."
```

- 논리: LRU의 정의 자체가 "**최근에 쓴 것**을 남긴다"이므로, "썼다"를 기록하지 않으면 LRU가 아니다.\
  즉 `get` 이 쓰기인 것은 구현의 선택이 아니라 **정책의 요구**다.

**왜 `ReadWriteLock` 의 읽기 잠금을 못 쓰는가**

```java
private final ReentrantLock lock = new ReentrantLock();   // 읽기/쓰기 구분이 없다

@Override
public V get(K key) {
    lock.lock();
    try {
        return delegate.get(key);
    } finally {
        lock.unlock();
    }
}
```

```
 ReadWriteLock 의 전제
   읽기끼리는 서로 방해하지 않는다 -> 여러 스레드가 동시에 통과시켜도 안전하다
   그 전제는 '읽기가 상태를 안 바꾼다' 위에 서 있다

 그런데 get 은 상태를 바꾼다
 -> 읽기 잠금으로 두 스레드를 동시에 통과시키면?

 스레드 A 는 노드 X 를, 스레드 B 는 노드 Y 를 맨 뒤로 옮기려 한다
 둘 다 linkLast 를 실행한다

   linkLast(node) {
       node.prev = tail.prev;      // (1) 현재 마지막을 읽는다
       node.next = tail;           // (2)
       tail.prev.next = node;      // (3) 현재 마지막의 next 를 나로
       tail.prev = node;           // (4) tail 의 prev 를 나로
   }

 인터리빙 예 (줄이 ... <-> Z <-> [tail] 인 상태)

   A(1) X.prev = Z
   B(1) Y.prev = Z                 <- B 도 Z 를 마지막으로 본다
   A(2) X.next = tail
   B(2) Y.next = tail
   A(3) Z.next = X
   B(3) Z.next = Y                 <- A 가 쓴 것을 덮어쓴다. X 가 줄에서 사라진다
   A(4) tail.prev = X
   B(4) tail.prev = Y

 결과 : 앞으로 훑으면  ... Z -> Y -> tail        (X 가 없다)
        뒤로 훑으면   tail -> Y -> Z ...         (일관된 듯 보인다)
        그런데 X 는 맵에 남아 있다  -> 8번의 '줄에만/맵에만' 문제가 발생
        인터리빙이 다르면 고리가 생기기도 한다 (A.next = B, B.next = A)
```

- 논리: 링크 갱신이 **여러 줄에 걸친 비원자 연산**이라, 중간에 다른 스레드가 끼어들면 일관성이 깨진다.
- 논리: 그래서 `ReentrantLock` 하나로 **모든 연산을 직렬화**한다 — 읽기든 쓰기든 구분 없이.
- 논리: README가 대안도 적어 뒀다 — 진짜로 읽기를 동시에 통과시키려면 **순서 갱신을 미루는 설계**로 가야 한다.\
  Caffeine이 그렇게 한다: 접근 기록을 버퍼에 쌓아 두고 나중에 몰아서 반영한다.

> **읽기-쓰기 잠금(ReadWriteLock)** — 읽기끼리는 동시에 통과시키고 쓰기만 배타적으로 막는 잠금.\
> 예: 읽기가 상태를 바꾸지 않을 때만 쓸 수 있다 — LRU의 `get` 은 상태를 바꾸므로 해당되지 않는다.

> **원자적 연산(atomic operation)** — 중간 상태가 다른 스레드에게 보이지 않는, 쪼갤 수 없는 연산.\
> 예: `linkLast` 의 네 줄은 원자적이지 않아, 잠금 없이 두 스레드가 실행하면 서로의 중간 상태를 덮어쓴다.

**왜 손상이 다음 순회에서야 드러나는가**

```
 손상이 일어난 순간
   linkLast 가 끝난다. 예외도 안 난다. 반환값(node.value)도 정상이다
   -> get 을 부른 쪽은 아무것도 눈치채지 못한다

 손상은 '링크'에 남는다
   링크는 그 자체로 검사되는 것이 아니라 '따라갈 때' 비로소 문제가 된다

 언제 따라가는가
   keysInOrder()  : head.next 부터 tail 까지 훑는다
   축출           : head.next 를 본다
   -> 즉 '순회'하는 연산이 불릴 때다

 고리가 생겨 있다면
   for (cur = head.next; cur != tail; cur = cur.next)
   -> cur 이 영원히 tail 에 닿지 못한다  -> 무한 루프
   -> CPU 100%, 응답 없음, 힙이 out 될 때까지 리스트에 add

 그래서 증상은
   get 을 부른 스레드가 아니라 '한참 뒤에 keysInOrder 를 부른 스레드'에서 나타난다
   원인 코드와 증상 코드가 다른 곳에 있다 -> 디버깅이 매우 어렵다
```

```java
assertTrue(forward.size() <= c.size() + 1, "고리가 생겼다. 무한히 돈다");
```

- 논리: `assertSound` 가 개수 상한을 두는 이유가 정확히 이것이다 — **테스트가 무한 루프에 빠지지 않게** 하려고.
- 논리: 자바의 `HashMap` 도 같은 종류의 유명한 사고가 있었다.\
  동시 리사이즈 중 버킷 리스트에 고리가 생겨 `get` 이 무한 루프에 빠지는 문제다.\
  (원본에 근거 없음 — 내 추론)

**동시성 테스트가 확인하는 것**

```java
// 잠금이 제 일을 했다면 이 셋이 전부 성립한다.
List<Integer> order = cache.keysInOrder();
assertTrue(cache.size() <= capacity, "용량을 넘었다: " + cache.size());
assertEquals(cache.size(), order.size(), "맵 크기와 줄 길이가 어긋났다");
Set<Integer> unique = new HashSet<>(order);
assertEquals(order.size(), unique.size(), "같은 키가 줄에 두 번 들어 있다");
for (Integer k : order) {
    assertNotNull(cache.get(k), "줄에 있는데 맵에 없는 키가 있다: " + k);
}
```

- 논리: 8스레드 x 2만 연산 x 5회 반복으로 **경합을 억지로 만든다**.
- 논리: 검사 넷이 각각 다른 손상 모양을 잡는다 — 용량 초과, 맵-줄 불일치, 줄의 중복 노드, 줄에만 있는 키.
- 한계: 동시성 버그는 **재현되지 않을 수 있다** — 5회 반복하는 이유이기도 하다.\
  테스트가 통과했다고 잠금이 완전하다는 증명은 아니다.

**`try/finally` 를 빠뜨리면**

```java
@Override
public put(K key, V value) {
    lock.lock();
    delegate.put(key, value);     // 여기서 IllegalArgumentException 이 나면
    lock.unlock();                // 이 줄에 도달하지 못한다
}
```

```
 LRUCache.put 은 null 키/값에 IllegalArgumentException 을 던진다

   lock.lock()          -> 잠금 획득
   delegate.put(null,x) -> 예외 발생, 메서드를 즉시 빠져나간다
   lock.unlock()        -> 실행되지 않는다

 결과 : 잠금이 영원히 잠긴 채로 남는다

   그 뒤에 이 캐시의 어떤 메서드를 부르는 스레드든 lock.lock() 에서 멈춘다
   get 도, put 도, size 도 전부 멈춘다
   -> 캐시를 쓰는 모든 요청 스레드가 하나씩 쌓여 스레드 풀이 고갈된다
   -> 프로세스 전체가 멈춘다

 한 번의 잘못된 입력(null 키)이 서비스 전체를 세우는 종류의 버그다
```

```java
@Test
@Timeout(60)
@DisplayName("예외가 나도 잠금은 풀린다")
void lockIsReleasedOnException() throws Exception {
    Cache<Integer, String> c = create(2);
    for (int i = 0; i < 50; i++) {
        assertThrows(IllegalArgumentException.class, () -> c.put(null, "x"));
    }
    // try/finally 없이 잠갔다면 여기서 영원히 멈춘다.
    Thread other = new Thread(() -> c.put(1, "a"));
    other.start();
    other.join(5000);
    assertTrue(!other.isAlive(), "다른 스레드가 잠금을 못 얻었다. try/finally 가 빠졌다");
    assertEquals("a", c.get(1));
}
```

- 논리: 테스트가 **다른 스레드**로 확인하는 것이 핵심이다.\
  `ReentrantLock` 은 재진입 가능해서 같은 스레드가 다시 `lock()` 하면 통과해 버린다 — 버그를 못 잡는다.
- 논리: `join(5000)` + `isAlive()` 로 "영원히 멈췄는가"를 유한 시간에 판정한다.
- 논리: 50번 반복해 잠금 카운트를 50까지 올려 두는 것도 의도적이다.\
  `ReentrantLock` 은 획득 횟수만큼 해제해야 풀린다.
- 한계: `try/finally` 는 자바에서 **잠금의 표준 관용구**다.\
  `synchronized` 블록은 이것이 언어에 내장되어 있어 실수할 수 없지만, 명시적 `Lock` 은 직접 써야 한다.

**잠그지 않은 메서드**

```java
@Override
public int capacity() {
    return delegate.capacity();     // 잠그지 않는다
}
```

- 논리: `capacity` 는 계약상 **생성 후 바뀌지 않는다**(`Cache.java` 주석).\
  변하지 않는 값이라 경합이 없어 잠글 이유가 없다.
- 논리: 나머지는 통계 조회(`hits`/`misses`/`evictions`)까지 전부 잠근다 — `long` 읽기가 원자적이지 않을 수 있고, 어차피 `get` 이 그 값을 바꾸기 때문이다.

**질문별 답**

- Q: "`get` 은 읽기가 아니다"가 왜 이 챕터의 핵심인가?\
  A: LRU의 정의가 "최근에 **쓴** 것을 남긴다"라 "썼다"를 기록하지 않으면 LRU가 아니기 때문이다 — `get` 이 쓰기인 것은 구현의 선택이 아니라 정책의 요구다.\
  이름은 읽기인데 실제로는 통계 카운터 하나와 링크 8개를 바꾸며, 이 사실이 동시성 설계 전체를 규정한다.

- Q: `ReadWriteLock` 의 읽기 잠금을 못 쓰는 이유는?\
  A: 읽기 잠금은 "읽기가 상태를 안 바꾼다"는 전제 위에 서 있는데 `get` 이 그 전제를 어기기 때문이다.\
  두 스레드를 동시에 통과시키면 `linkLast` 의 네 줄이 서로 끼어들어 한쪽이 쓴 링크를 덮어쓰고, 노드가 줄에서 사라지거나 고리가 생긴다.\
  그래서 `ReentrantLock` 하나로 모든 연산을 직렬화한다 — 진짜로 읽기를 동시에 통과시키려면 순서 갱신을 버퍼에 미루는 설계(Caffeine)로 가야 한다.

- Q: 그 손상이 왜 다음 순회에서야 무한 루프로 드러나는가?\
  A: 손상은 **링크에만** 남고, 링크는 따라갈 때 비로소 문제가 되기 때문이다.\
  `get` 자체는 예외도 안 나고 값도 정상으로 돌려주므로 부른 쪽이 눈치채지 못한다.\
  한참 뒤 `keysInOrder` 나 축출이 줄을 훑을 때, 고리가 생겨 있으면 `cur` 이 영영 `tail` 에 닿지 못해 무한 루프가 된다 — **원인 코드와 증상 코드가 다른 곳에 있어** 디버깅이 어렵다.

- Q: `try/finally` 를 빠뜨리면 왜 예외 한 번이 프로세스 전체를 세우는가?\
  A: `delegate` 가 예외를 던지면 `unlock()` 줄에 도달하지 못해 **잠금이 영원히 잠긴 채로** 남기 때문이다.\
  그 뒤 이 캐시의 어떤 메서드를 부르는 스레드든 `lock()` 에서 멈추고, 요청 스레드가 하나씩 쌓여 스레드 풀이 고갈된다.\
  `null` 키 하나 같은 잘못된 입력 한 번이 서비스 전체를 세우는 종류의 버그다.\
  테스트가 **다른 스레드**로 확인하는 이유는 `ReentrantLock` 이 재진입 가능해서 같은 스레드로는 버그가 안 잡히기 때문이다.

---

#### 10. 최악의 사용 패턴 — 순차 스캔에서 적중률 0%

**질문**: 용량 3짜리 캐시에 0,1,2,3을 돌아가며 찍으면 적중률이 왜 정확히 0%인가. 같은 입력에서 최적(Belady)은 왜 66%를 내는가. 이것이 버그가 아니라 무엇인가.

**테스트**

```java
@Test
@DisplayName("한계: 순차 스캔에서는 적중률이 0 이다")
void sequentialScanDefeatsLru() {
    // 용량 3 짜리 캐시에 0,1,2,3 을 돌아가며 찍으면 **한 번도 안 맞는다.**
    // 다음에 쓸 것을 정확히 골라 버리기 때문이다.
    // 버그가 아니라 LRU 라는 가정(최근 쓴 것을 또 쓴다)이 반대로 틀린 경우다.
    int[] scan = new int[400];
    for (int i = 0; i < scan.length; i++) {
        scan[i] = i % 4;
    }
    assertEquals(0.0, LRUCacheProblems.hitRatio(3, scan), EPS,
            "LRU 는 여기서 완전히 진다");
    assertTrue(LRUCacheProblems.optimalHitRatio(3, scan) > 0.6,
            "최적은 같은 입력에서 60% 를 넘는다. 정책의 문제이지 용량의 문제가 아니다");
}
```

**왜 정확히 0%인가**

```
 용량 3, 접근 순서 0,1,2,3,0,1,2,3,0,1,2,3, ...

 줄은 [오래됨 ... 최근]

 i=0  key 0 : miss  줄 [0]
 i=1  key 1 : miss  줄 [0,1]
 i=2  key 2 : miss  줄 [0,1,2]
 i=3  key 3 : miss  꽉 참 -> 맨 앞 0 을 버린다     줄 [1,2,3]
                              ^^^^^^^^^^^^^^^^^
                              그런데 바로 다음에 쓸 것이 0 이다!
 i=4  key 0 : miss  꽉 참 -> 맨 앞 1 을 버린다     줄 [2,3,0]
                              다음에 쓸 것이 1 이다!
 i=5  key 1 : miss  꽉 참 -> 2 를 버린다           줄 [3,0,1]
                              다음에 쓸 것이 2 다!
 i=6  key 2 : miss  꽉 참 -> 3 을 버린다           줄 [0,1,2]
 i=7  key 3 : miss  ...

 영원히 반복된다. 적중률 정확히 0.0

 왜 '정확히' 0 인가
   서로 다른 키 4개가 순환하는데 용량이 3이다
   LRU 가 버리는 것은 '가장 오래 안 쓴 것'인데
   순환에서는 그것이 곧 '가장 먼저 다시 쓸 것'이다
   -> 매번 정확히 최악의 선택을 한다
   -> 우연히 맞는 경우조차 없다
```

```
 그림으로

   순환 순서 :  0 -> 1 -> 2 -> 3 -> 0 -> 1 -> ...

   지금 막 쓴 것          = 3
   가장 오래 안 쓴 것     = 0     <- LRU 가 버린다
   가장 먼저 다시 쓸 것   = 0     <- 바로 이것이다

   순환에서는 '가장 오래됨' 과 '가장 곧 필요함' 이 같은 것을 가리킨다
   LRU 의 가정(최근 쓴 것을 또 쓴다)이 정확히 180도 반대다
```

- 논리: **용량을 하나만 늘려 4로 만들면** 적중률이 극적으로 바뀐다.\
  서로 다른 키가 전부 들어가므로 첫 4번만 미스이고 나머지 396번이 전부 적중 → 99%다.\
  (원본에 근거 없음 — 내 추론: 테스트에는 이 케이스가 없다)
- 논리: 즉 **절벽(cliff)** 이 있다 — 용량 3에서 0%, 4에서 99%.\
  적중률이 용량에 매끄럽게 비례하지 않는다는 것이 LRU의 중요한 성질이다.

**최적(Belady)이 66%를 내는 이유**

```
 같은 입력에서 OPT 를 돌려보면

 i=0  key 0 : miss  {0}
 i=1  key 1 : miss  {0,1}
 i=2  key 2 : miss  {0,1,2}
 i=3  key 3 : miss  꽉 참 -> 다음 등장 시점 비교
                      0 -> 4,  1 -> 5,  2 -> 6      가장 먼 것은 2
                      2 를 버린다                   {0,1,3}
 i=4  key 0 : HIT                                   {0,1,3}
 i=5  key 1 : HIT                                   {0,1,3}
 i=6  key 2 : miss  -> 0 -> 8, 1 -> 9, 3 -> 7      가장 먼 것은 1
                      1 을 버린다                   {0,3,2}
 i=7  key 3 : HIT
 i=8  key 0 : HIT
 i=9  key 1 : miss  -> 0 -> 12, 3 -> 11, 2 -> 10   가장 먼 것은 0
                      0 을 버린다                   {3,2,1}
 i=10 key 2 : HIT
 i=11 key 3 : HIT
 i=12 key 0 : miss ...

 패턴 : 초기 3번 미스 뒤, 3번에 한 번씩만 미스가 난다

 400번 중 미스 = 처음 3번(i=0,1,2) + i=3,6,9,...,399 (133번) = 136번
 적중 = 400 - 136 = 264
 적중률 = 264 / 400 = 0.66      <- 정확히 66%

 왜 OPT 는 되는가
   "가장 나중에 쓸 것"을 버리므로 순환에서 '가장 멀리 있는 것'을 버린다
   -> 버린 것을 다시 만나기까지 시간이 벌린다
   -> 그 사이에 나머지 두 개가 계속 적중한다
```

- 논리: LRU와 OPT의 차이가 **같은 용량, 같은 입력에서 0% vs 66%** 로 벌어진다.\
  이만큼 벌어진다는 것은 "정책을 바꿀 여지가 크다"는 신호다(2번의 상한선 논리).
- 논리: 테스트 메시지가 그 결론을 명시한다 — **"정책의 문제이지 용량의 문제가 아니다."**

**버그가 아니라 무엇인가**

```
 버그란 : 명세와 구현이 다른 것
          이 코드는 "가장 오래 안 쓴 것을 버린다"를 정확히 하고 있다 -> 버그가 아니다

 이것은 : '가정이 반대로 틀린 워크로드' 다
          LRU 는 시간 지역성을 가정한다
          순차 스캔에는 시간 지역성이 없고, 오히려 반대 성질(막 쓴 것은 당분간 안 쓴다)이 있다

 5번에서 본 구분이 여기서 구체적 숫자로 나타난다
   O(1) 은 정리다 -> 순차 스캔에서도 여전히 O(1) 이다
   좋은 적중률은 가정이다 -> 순차 스캔에서 0% 로 무너진다

 실무의 대응
   스캔 저항(scan resistance)을 따로 넣는다
     2Q / ARC : '두 번 이상 쓰인 것'만 주 영역에 올린다
                -> 한 번만 읽히는 스캔 데이터가 캐시를 못 밀어낸다
     W-TinyLFU(Caffeine) : 빈도 추정기를 두고 '새로 들어올 것이 나갈 것보다 인기 있나'를 본다
   또는 스캔임을 아는 쪽에서 캐시를 우회한다 (DB의 대량 조회 힌트 등)
   (원본에 근거 없음 -- 내 추론: README 는 스캔 저항이라는 이름만 언급한다)
```

- 논리: `deduplicateStream` 의 `exactlyAtCapacity` 테스트가 **같은 현상의 다른 얼굴**이다.\
  용량 2에 서로 다른 키 3개 순환 → 중복을 하나도 못 잡는다.
- 논리: 이런 한계를 **테스트로 못 박는 것** 자체가 이 문제집의 방식이다.\
  `SortedListHeapTest.insertCostGrowsQuadratically`, `AdjacencyMatrixGraphTest.allocatesSquareRegardlessOfEdges` 와 같은 계열이다 — 버그를 잡는 테스트가 아니라 **대가를 숫자로 고정하는 테스트**다.

**질문별 답**

- Q: 용량 3에 0,1,2,3을 돌아가며 찍으면 왜 정확히 0%인가?\
  A: 순환에서는 **"가장 오래 안 쓴 것"과 "가장 먼저 다시 쓸 것"이 같은 키**이기 때문이다.\
  LRU는 매번 바로 다음에 필요한 것을 정확히 골라 버리므로 우연히 맞는 경우조차 없다.\
  서로 다른 키 4개가 용량 3에 들어가지 못하는 한, 이것이 영원히 반복된다.

- Q: 같은 입력에서 최적(Belady)은 왜 66%인가?\
  A: OPT는 "가장 **나중에** 쓸 것"을 버리므로 순환에서 가장 멀리 있는 것을 버려 **다시 만나기까지 시간을 번다**.\
  그 사이 나머지 두 개가 계속 적중해, 초기 3번 미스 뒤로는 3번에 한 번만 미스가 난다.\
  400번 중 미스 136번, 적중 264번 → 정확히 0.66이다.

- Q: 이것이 버그가 아니라 무엇인가?\
  A: **가정이 반대로 틀린 워크로드**다.\
  코드는 "가장 오래 안 쓴 것을 버린다"를 정확히 수행하고 있으므로 명세와 구현이 어긋난 버그가 아니다.\
  LRU가 기대는 시간 지역성이 순차 스캔에는 없고 오히려 반대 성질이 있을 뿐이다.\
  `O(1)` 은 정리라 여기서도 그대로지만 "좋은 적중률"은 가정이라 0%로 무너진다 — 실무 캐시가 스캔 저항(2Q·ARC·W-TinyLFU)을 따로 넣는 이유다.

---

#### 11. 세 구현의 트레이드오프

**질문**: 직접 엮은 `LRUCache` 40줄이 `LinkedHashMapLRU` 4줄이 되는데도 직접 만드는 이유는. `accessOrder=true` 와 `removeEldestEntry` 는 각각 무엇을 켜는가. `removeEldestEntry` 의 비교 부호를 `>=` 로 쓰면 왜 틀리는가.

**세 구현**

| | 무엇 | 왜 |
|---|---|---|
| `LRUCache` | 해시맵 + 이중 연결 리스트를 직접 엮는다 | 안에서 무슨 일이 벌어지는지 알기 위해 |
| `LinkedHashMapLRU` | 표준 라이브러리가 이미 해준다 | 40줄이 4줄이 된다 |
| `ThreadSafeLRUCache` | 위의 것을 감싸 잠근다 | `get` 이 쓰기라서 |

**`LinkedHashMapLRU` 의 핵심 4줄**

```java
this.map = new LinkedHashMap<>(16, 0.75f, true) {
    @Override
    protected boolean removeEldestEntry(Map.Entry<K, V> eldest) {
        return size() > LinkedHashMapLRU.this.capacity;
    }
};
```

```
 생성자 인자 세 개
   16     초기 버킷 수
   0.75f  적재율(load factor)
   true   accessOrder      <- 이 스위치가 첫 번째다

 그리고 removeEldestEntry 재정의   <- 두 번째 스위치
```

**`accessOrder = true` 가 켜는 것**

```
 LinkedHashMap 은 HashMap 에 이중 연결 리스트를 얹은 것이다 (구조가 LRUCache 와 같다)
 그 줄의 '순서 규칙'을 생성자 인자가 정한다

   accessOrder = false (기본값) : 삽입 순서 (insertion order)
       put 할 때만 줄 맨 뒤로 간다. get 은 순서를 안 바꾼다

   accessOrder = true           : 접근 순서 (access order)
       get 도 그 엔트리를 줄 맨 뒤로 옮긴다      <- 이것이 LRU 의 핵심 동작

 즉 accessOrder = true 는
 "get 을 읽기가 아니라 쓰기로 만든다"는 스위치다   (9번의 그 성질)
```

```java
@Test
@DisplayName("accessOrder 가 꺼져 있으면 get 이 순서를 안 바꾼다")
void accessOrderMatters() {
    // 이 테스트는 accessOrder=true 를 실제로 켰는지 본다.
    // 기본값(false)으로 만들면 삽입 순서가 유지되어 여기서 걸린다.
    Cache<Integer, String> c = create(3);
    c.put(1, "a");
    c.put(2, "b");
    c.put(3, "c");
    c.get(1);
    assertEquals(List.of(2, 3, 1), c.keysInOrder(),
            "삽입 순서 그대로면 accessOrder 를 안 켠 것이다");
}
```

- 논리: `get(1)` 뒤에 `[2, 3, 1]` 이 나와야 한다 — `1` 이 맨 뒤로 갔다는 뜻이다.\
  `accessOrder` 가 꺼져 있으면 `[1, 2, 3]` 이 그대로 나온다.

**`removeEldestEntry` 가 켜는 것**

```
 LinkedHashMap 은 put 이 끝난 뒤에 이 메서드를 부른다
   true 를 반환하면 -> 줄 맨 앞(가장 오래된 엔트리)을 지운다
   false 를 반환하면 -> 아무 일도 안 한다

 기본 구현은 항상 false 다 (= 용량 제한이 없는 평범한 맵)

 재정의해서 "용량을 넘었으면 true" 로 만들면 그것이 곧 축출 정책이다
```

- 논리: 즉 이 메서드는 **"언제 버릴 것인가"** 의 훅(hook)이다.\
  `accessOrder` 가 "무엇을 버릴 것인가"(가장 오래 안 쓴 것)를 정하고, 이것이 "언제"를 정한다.
- 논리: 두 스위치가 합쳐져야 LRU가 된다 — 하나만으로는 안 된다.

**`>` 와 `>=` 의 차이**

```
 호출 시점이 중요하다 : removeEldestEntry 는 put 이 '끝난 뒤' 불린다
 따라서 그 시점의 size() 는 방금 넣은 것까지 포함한 값이다

 용량 3 인 캐시에 세 번째 원소를 넣는 순간

   put(3, "c") 실행
   -> 맵에 3 이 들어간다. size() = 3
   -> removeEldestEntry(eldest) 호출

   (A) return size() > capacity   ->  3 > 3  -> false  -> 안 버린다
       결과 : {1, 2, 3} 세 개가 담긴다.  size = 3 = 용량   OK

   (B) return size() >= capacity  ->  3 >= 3 -> true   -> 버린다!
       결과 : 1 이 버려져 {2, 3} 두 개만 남는다.  size = 2
       -> 용량이 3 인데 실제로는 2 개밖에 못 담는다

 네 번째를 넣을 때는 둘 다 버린다 (4 > 3, 4 >= 3 둘 다 참)
 -> 차이가 드러나는 시점은 '딱 용량만큼 찼을 때' 한 번뿐이다
```

```java
@Test
@DisplayName("removeEldestEntry 의 부호 하나")
void thresholdOffByOne() {
    // size() >= capacity 로 쓰면 아직 자리가 있는데도 버린다.
    Cache<Integer, String> c = create(3);
    c.put(1, "a");
    c.put(2, "b");
    c.put(3, "c");
    assertEquals(3, c.size(), "용량만큼은 담겨야 한다");
    assertEquals(0, c.evictions());
    assertEquals(List.of(1, 2, 3), c.keysInOrder());
    c.put(4, "d");
    assertEquals(3, c.size());
    assertEquals(1, c.evictions());
    assertNull(c.get(1));
}
```

> **하나 차이 오류(off-by-one)** — 경계에서 1만큼 어긋나는 실수. 비교 연산자, 반복 범위, 인덱스에서 자주 난다.\
> 예: `>` 를 `>=` 로 쓰면 용량 3짜리 캐시가 2개만 담는다 — 동작은 하는데 용량이 하나 줄어든다.

- 논리: 이 버그는 **완전히 조용하다** — 캐시는 정상 동작하고 적중률만 조금 낮아진다.\
  "왜 캐시 효율이 기대보다 낮지?"로만 나타난다.
- 논리: 직접 만든 `LRUCache` 는 이 함정이 다른 모양이다.

```java
if (index.size() == capacity) {      // put '전에' 검사한다
    ...버린다...
}
```

- 논리: 직접 만든 쪽은 **넣기 전에** 검사하므로 `==` 가 맞다.\
  `LinkedHashMap` 은 **넣은 뒤에** 부르므로 `>` 가 맞다 — **검사 시점이 다르면 부호도 달라진다**.
- 논리: 이것이 "라이브러리를 쓰면 쉽다"의 이면이다.\
  라이브러리의 호출 시점을 모르면 부호를 못 정한다.

**직접 만드는 이유**

```
 1. 안을 알아야 밖을 쓸 수 있다
      removeEldestEntry 의 부호를 정하려면 '언제 불리는지'를 알아야 한다
      accessOrder 가 무엇을 하는지 알려면 '안에 줄이 있다'는 것을 알아야 한다
      직접 만들어 본 사람만 라이브러리의 스위치를 제대로 고를 수 있다

 2. 라이브러리가 항상 있는 것이 아니다
      다른 언어·환경에는 LinkedHashMap 이 없을 수 있다
      요구사항이 조금만 달라져도(TTL, 크기 기반 용량, 다단 캐시) 직접 짜야 한다

 3. 성능·동작을 조정할 수 없다
      LinkedHashMapLRU 의 put 은 evictions 를 세려고 containsKey + size 를 추가로 부른다
      -> 직접 엮은 쪽보다 연산이 몇 개 더 든다
      통계 하나를 얻으려고 우회하는 모양이 되는데, 안을 못 건드리기 때문이다

 4. 면접·설계 대화에서 '왜 그렇게 되는가'를 말할 수 있어야 한다
      (원본에 근거 없음 -- 내 추론)

 그리고 이 문제집이 확인시켜 주는 것
   두 구현이 '완전히 같게' 움직인다는 것 (identicalToHandWritten 테스트)
   -> 직접 만든 것이 표준 라이브러리와 동치임을 확인하고 나면
      라이브러리를 믿고 쓸 수 있게 된다
```

```java
@Test
@DisplayName("같은 연산을 주면 같은 순서가 나온다")
void identicalToHandWritten() {
    Cache<Integer, String> hand = new LRUCache<>(3);
    Cache<Integer, String> std = new LinkedHashMapLRU<>(3);
    // ... 같은 연산을 두 캐시에 동시에 흘려보내며 매번 대조 ...
    assertEquals(hand.hits(), std.hits());
    assertEquals(hand.misses(), std.misses());
    assertEquals(hand.evictions(), std.evictions());
}
```

- 논리: **차등 테스트(differential testing)** 다 — 두 독립 구현의 출력을 대조해 둘 다 검증한다.
- 논리: 순서·크기뿐 아니라 통계 셋까지 맞춰야 한다 — `evictions` 를 라이브러리 쪽에서 우회로 세는 이유다.

> **차등 테스트(differential testing)** — 같은 입력을 두 개 이상의 독립 구현에 주고 출력을 대조하는 검증 방식.\
> 예: 직접 만든 LRU와 `LinkedHashMap` 기반 LRU에 같은 연산 열을 흘려 순서·크기·통계가 전부 같은지 본다.

**`ThreadSafeLRUCache` 의 트레이드오프**

```java
public ThreadSafeLRUCache(Cache<K, V> delegate) {
    if (delegate == null) {
        throw new IllegalArgumentException("감쌀 캐시가 필요하다");
    }
    this.delegate = delegate;
}
```

- 논리: **어떤 `Cache` 든 감쌀 수 있다**(`wrapsAnyCache` 테스트가 `LinkedHashMapLRU` 를 감싼다).\
  데코레이터 패턴이라 정책(어떤 캐시냐)과 동시성(잠금)이 분리된다.
- 한계: 대가는 **모든 연산의 직렬화**다 — 8스레드가 있어도 캐시 접근은 한 번에 하나씩이다.\
  경합이 심하면 캐시가 병목이 된다.
- 한계: 그래서 실무 캐시는 잠금을 쪼개거나(세그먼트) 순서 갱신을 미루는 설계를 쓴다.

**질문별 답**

- Q: 40줄이 4줄이 되는데도 직접 만드는 이유는?\
  A: **안을 알아야 밖을 쓸 수 있기** 때문이다.\
  `removeEldestEntry` 의 부호를 정하려면 그것이 `put` 뒤에 불린다는 것을, `accessOrder` 를 이해하려면 안에 줄이 있다는 것을 알아야 한다.\
  덧붙여 라이브러리가 없는 환경도 있고, 요구가 조금만 달라져도(TTL·크기 기반 용량·다단 캐시) 직접 짜야 하며, 안을 못 건드려 통계 하나를 얻는 데도 우회해야 한다.\
  그리고 `identicalToHandWritten` 으로 둘이 동치임을 확인하고 나면 라이브러리를 믿고 쓸 수 있게 된다.

- Q: `accessOrder=true` 와 `removeEldestEntry` 는 각각 무엇을 켜는가?\
  A: `accessOrder=true` 는 `LinkedHashMap` 내부 줄의 순서 규칙을 **삽입 순서에서 접근 순서로** 바꾼다 — `get` 도 엔트리를 맨 뒤로 옮기게 만드는, 즉 "`get` 을 쓰기로 만드는" 스위치다.\
  `removeEldestEntry` 는 `put` 이 끝난 뒤 불리는 훅으로 **"언제 버릴 것인가"** 를 정한다 — `true` 를 반환하면 줄 맨 앞을 지운다.\
  전자가 "무엇을", 후자가 "언제"를 정하고, 둘이 합쳐져야 LRU가 된다.

- Q: `removeEldestEntry` 의 부호를 `>=` 로 쓰면 왜 틀리는가?\
  A: 이 메서드가 `put` 이 **끝난 뒤** 불려 그 시점의 `size()` 에 방금 넣은 것이 이미 포함되기 때문이다.\
  용량 3에 세 번째를 넣으면 `size()` 가 3인데 `3 >= 3` 이 참이라 하나를 버려, 용량 3짜리 캐시가 실제로는 2개만 담는다.\
  직접 만든 `LRUCache` 는 **넣기 전에** `index.size() == capacity` 로 검사하므로 `==` 가 맞다 — **검사 시점이 다르면 부호도 달라진다**.

---

#### 12. 11-bloom-filter 로의 연결 — 잊는 것에서 틀리는 것으로

**질문**: 여기서는 용량을 정해두고 **일부러 잊어서** 메모리를 한정했다. 거기서는 무엇을 포기해서 메모리를 수십 배 줄이는가. "일부러 잊는 것"과 "틀릴 수도 있는 것"은 어떻게 이어지는가.

**메모리를 줄이는 세 단계**

```
 09-trie 까지 : 전부 담는다
     "넣은 것은 전부, 정확하게 들어 있다"
     메모리 = 데이터 크기에 비례
     한계   : 데이터가 크면 그대로 터진다 (문제 3의 n(n+1)/2)

 10-lru-cache : 일부만 담는다  <- 용량을 포기
     "최근 capacity 개만 들어 있다. 나머지는 없다"
     메모리 = O(capacity), 데이터 크기와 무관하게 고정
     담긴 것에 대한 답은 여전히 '정확하다'
       - 있다고 하면 정말 있다
       - 없다고 하면 정말 캐시에 없다 (원본에는 있을 수 있지만 캐시에 없는 건 사실이다)
     대가   : 버린 것을 다시 물으면 미스다 (deduplicateStream 의 exactlyAtCapacity)

 11-bloom-filter : 부정확하게 담는다  <- 정확성을 포기
     "없다고 하면 확실히 없다. 있다고 하면 아마 있다"
     메모리 = 원소당 몇 비트 (100만 개에 1.2MB 수준)
     대가   : 오탐(false positive)이 확률적으로 발생한다
              그리고 담은 원소를 '꺼낼 수 없다' -- 키 자체를 저장하지 않으므로
```

> **오탐(false positive)** — 실제로는 없는데 "있다"고 답하는 것.\
> 예: 블룸 필터는 오탐을 허용하는 대신 메모리를 극단적으로 줄인다 — 누락(false negative)은 없다.

**"일부러 잊는 것"과 "틀릴 수도 있는 것"의 연결**

```
 공통점 : 둘 다 '완전함'을 포기해 메모리를 상수로 묶는다

   LRU   : 완전한 '보관'을 포기한다   -> 없는 것은 정말 없다 (거짓말은 안 한다)
   블룸  : 완전한 '정답'을 포기한다   -> 없는 것을 있다고 할 수 있다 (거짓말을 한다)

 차이점 : 무엇을 포기했느냐

   LRU 의 답은 항상 참이다. 다만 '아는 범위'가 좁다
       get(x) == null 은 "캐시에 없다"는 사실이다
       그래서 캐시 미스는 원본 저장소를 보면 해결된다

   블룸의 답은 한쪽 방향으로만 참이다
       mightContain(x) == false 는 "확실히 없다"는 사실이다
       mightContain(x) == true 는 "아마 있다" -- 확인이 필요하다

 둘 다 '뒤에 진짜 저장소가 있다'를 전제한다
   캐시    : 미스면 DB 를 본다
   블룸    : true 면 DB 를 본다 (false 면 DB 를 안 봐도 된다 -- 이게 이득이다)

 즉 블룸 필터는 '앞단 필터' 다
   비싼 조회를 '확실히 필요 없을 때' 건너뛰게 해 준다
```

```
 같은 문제(중복 제거)를 세 챕터가 어떻게 푸는가

   09 트라이/해시셋 : 본 것을 전부 저장 -> 정확하다.  메모리 O(서로 다른 키 수)
   10 LRU 캐시      : 최근 N 개만 저장  -> 오래된 중복을 놓친다. 메모리 O(N)
   11 블룸 필터     : 비트만 저장       -> 가끔 '봤다'고 잘못 말한다. 메모리 O(비트)

   10 은 '경계 밖'을 못 본다 (결정론적 한계)
   11 은 '경계'가 없는 대신 확률적으로 틀린다
```

- 논리: 흐름이 한 방향이다 — **정확하고 크다 → 부분적이고 작다 → 부정확하고 아주 작다.**
- 논리: 각 단계에서 **무엇을 포기했는지**가 명확하고, 그 대가로 무엇을 얻는지도 명확하다.\
  자료구조 선택이란 결국 이 거래를 고르는 일이다.
- 논리: 10번이 11번의 준비인 이유는 **"불완전해도 쓸모 있다"는 감각**을 먼저 겪게 하기 때문이다.\
  LRU에서 "버린 것을 다시 물으면 미스"가 정상 동작이라는 것을 받아들이고 나면, "가끔 틀린 답"도 받아들일 수 있다.

**11번에서 새로 나오는 것**

- 논리: **확률**이 설계 변수로 들어온다 — 오탐률 `p` 를 정하면 필요한 비트 수 `m` 과 해시 개수 `k` 가 공식으로 나온다.
- 논리: 그리고 **되돌릴 수 없음**이 새로 문제가 된다.\
  LRU는 용량이 부족하면 키워서 다시 쓰면 되지만, 블룸 필터는 담은 원소를 꺼낼 수 없어 **다시 만들 수조차 없다**.
- 논리: 삭제도 안 된다 — 한 비트를 여러 원소가 공유하기 때문이다.\
  그래서 `CountingBloomFilter`, `ScalableBloomFilter` 같은 변종이 나온다.

**질문별 답**

- Q: 거기서는 무엇을 포기해서 메모리를 수십 배 줄이는가?\
  A: **정확성**이다.\
  블룸 필터는 원소 자체를 저장하지 않고 비트만 켜므로, "없다"는 확실하지만 "있다"는 **아마 있다**가 된다(오탐).\
  덤으로 담은 원소를 꺼낼 수도 없고 지울 수도 없다 — 100만 개를 1.2MB 수준으로 담는 대가다.

- Q: "일부러 잊는 것"과 "틀릴 수도 있는 것"은 어떻게 이어지는가?\
  A: 둘 다 **완전함을 포기해 메모리를 상수로 묶는** 같은 계열의 거래이고, 포기한 대상만 다르다.\
  LRU는 완전한 **보관**을 포기했고(답은 항상 참이지만 아는 범위가 좁다), 블룸은 완전한 **정답**을 포기했다(한쪽 방향으로만 참이다).\
  둘 다 **뒤에 진짜 저장소가 있다**를 전제한다 — 캐시는 미스면 DB를 보고, 블룸은 true면 DB를 본다(false면 안 봐도 되는 것이 이득이다).\
  10번에서 "버린 것을 다시 물으면 미스"가 정상 동작임을 받아들이고 나면, 11번의 "가끔 틀린 답"도 같은 종류의 거래로 읽힌다.

**더 생각할 것**

- 이 챕터의 모든 주제가 **"`get` 은 읽기가 아니다"** 한 줄에서 파생된다.\
  문제 3에서 `containsKey` 대신 `get` 을 쓰는 이유, 동시성에서 `ReadWriteLock` 을 못 쓰는 이유, `accessOrder=true` 가 하는 일이 전부 같은 사실의 다른 얼굴이다.
- "테스트가 초록"과 "제대로 동작한다" 사이의 틈이 유난히 넓다.\
  `>` 대신 `>=` 를 써도 캐시는 동작하고, 맵·줄 한쪽만 지워도 값은 잘 나오고, `try/finally` 를 빠뜨려도 예외가 안 나는 동안은 멀쩡하다.\
  그래서 테스트가 **내부 불변식을 직접 대조한다**(`assertSound`, `evictionTouchesBoth`, 다른 스레드로 잠금 확인).
- 성능과 정책을 구분하는 훈련이 여기 있다.\
  `O(1)` 은 자료구조가 보장하는 **정리**이고 적중률은 워크로드에 대한 **가정**이다 — 순차 스캔 0%가 버그가 아닌 이유이고, Belady를 구현해 보는 이유이기도 하다.
