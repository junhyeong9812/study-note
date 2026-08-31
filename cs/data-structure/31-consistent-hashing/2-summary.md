# data-structure/31-consistent-hashing — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 계약 — HashRing (`src/main/java/com/datastructure/conshash/HashRing.java`)

- `void addNode(String node)`
- `void removeNode(String node)`
- `String getNode(String key)`
- `int nodeCount()`
- `List<String> nodes()`
- `int slotCount()`
- `default Map<String, Integer> keyCounts(Iterable<String> keys)`

## 계약 — RingHash (`src/main/java/com/datastructure/conshash/RingHash.java`)

- `long position(String name)`

## 보조

- `Hashing` (`src/main/java/com/datastructure/conshash/Hashing.java`) — 역할:
- `RingMetrics` (`src/main/java/com/datastructure/conshash/RingMetrics.java`) — 역할:

## 구현 — ModuloSharding (`src/main/java/com/datastructure/conshash/ModuloSharding.java`)

### 구조

```
ModuloSharding
+------------------------------------------------------------+
| nodes : List<String> = ArrayList   (들고 있는 것은 이름 목록뿐) |
+------------------------------------------------------------+
      idx    0       1       2
          +-------+-------+-------+
  nodes   |   A   |   B   |   C   |    n = nodes.size() = 3
          +-------+-------+-------+
  slotCount() = nodeCount() = 3      <- 자리라는 것이 따로 없다. 메모리는 네 방식 중 제일 적다.

  getNode(key) = nodes.get( Hashing.bucketHash(key) % nodes.size() )
                            ^^^^^^^^^^^^^^^^^^^^^^^^^ 최상위 비트를 지운 값 -> 나머지가 음수가 안 된다
```

### 동작 — 노드 수 변화 (링과의 대비)

```
n 이 3 -> 4 로 바뀐다 = 나눗셈의 분모가 바뀐다 = 모든 몫이 바뀐다

  before  n = 3                       after  n = 4  (D 를 추가)
      +-------+-------+-------+           +-------+-------+-------+-------+
      |   A   |   B   |   C   |    ->     |   A   |   B   |   C   |   D   |
      +-------+-------+-------+           +-------+-------+-------+-------+

  key    h = bucketHash(key)   h%3    h%4     before -> after
  ----   ------------------    ---    ---     ---------------
  k1              27            0      3       A -> D    옮김
  k2              28            1      0       B -> A    옮김
  k3              29            2      1       C -> B    옮김
  k4              30            0      2       A -> C    옮김
  k5              31            1      3       B -> D    옮김
  k6              32            2      0       C -> A    옮김
  k7              33            0      1       A -> B    옮김
  ...                                          거의 전부가 움직인다
  (h 값은 이해용 예시)

  새 노드 D 와 아무 상관 없는 A <-> B <-> C 끼리도 서로 넘긴다.
  MovementTest 실측 : 노드 하나를 뺐을 때 자리가 바뀌는 키 89,905개
                      그중 죽은 노드가 맡던 것은 10,029개뿐 -> 나머지 8만 개는 순수한 낭비

왜 링과 대비하나
  이 식에는 N 이 들어 있다. N 이 바뀌면 모든 키의 계산이 바뀐다.
  링에는 배정 규칙에 N 이 없다. 자리들의 배치만 있다. 그 차이가 전부다.
  분포는 이쪽도 고르다(ModuloShardingTest 가 확인한다). 나쁜 것은 오직 이동량이다.
```

### 필드
- `nodes` — 역할:

### `void addNode(String node)`
- 하는 일:
- 논리:
- 비용(왜):

### `void removeNode(String node)`
- 하는 일:
- 논리:
- 비용(왜):

### `String getNode(String key)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `int nodeCount()` / `List<String> nodes()` / `int slotCount()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — ConsistentHashRing (`src/main/java/com/datastructure/conshash/ConsistentHashRing.java`)

### 구조

```
ConsistentHashRing
+---------------------------------------------------------------------+
| DEFAULT_VIRTUAL_NODES = 100  (노드 하나를 원 위 몇 곳에 올릴지의 기본값) |
| virtualNodes = 3             (이 그림에서만 3 으로 줄인다)             |
| hash : RingHash = Hashing.MIXED   (이름 -> 0 이상 2^32 미만의 자리)    |
| ring   : NavigableMap<Long,String> = TreeMap   자리 -> 그 자리의 노드  |
| placed : Map<String,Integer> = LinkedHashMap   노드 -> 실제로 찍은 자리 수 |
+---------------------------------------------------------------------+

원을 선으로 펼친 그림 (왼쪽 끝이 0, 오른쪽 끝이 2^32-1, 오른쪽 끝은 왼쪽 끝으로 되감김)

   0                                                              2^32-1
   |-----|--------|--------|--------|--------|--------|--------------|
        A#0      B#0      C#0      A#1      B#1      C#1        (되감김 -> A#0)
       (120)    (350)    (610)    (880)   (1240)   (1600)
        자리 = hash.position(virtualName(node, i)) = hash.position("A#0")
   |<------------------ 한 바퀴 = Hashing.RING_SIZE = 2^32 ------------->|

ring 안의 실제 모습 (TreeMap - 자리 오름차순 정렬 그 자체가 이 구조의 전부다)

     자리(long)    노드
    +----------+-------+
    |    120   |   A   |  <- ring.firstEntry() : 되감김이 도착하는 곳
    |    350   |   B   |
    |    610   |   C   |
    |    880   |   A   |
    |   1240   |   B   |
    |   1600   |   C   |  <- ring.lastEntry()
    +----------+-------+
    slotCount() = ring.size() = 6 = 노드 수 x virtualNodes
    placed = { A:3, B:3, C:3 }    nodeCount() = placed.size() = 3    slotsOf("A") = 3
    ringView() 는 이 맵을 그대로 읽기 전용으로 보여준다(구조 테스트가 배치를 직접 확인한다)

자리 값 120/350/... 은 이해를 위한 작은 예시다. 실제 자리는 0 .. 2^32-1 에 흩어진다.
```

### 동작 — 키 배정 (시계방향 첫 노드)

```
getNode(key) : ring.ceilingEntry(hash.position(key)) 가 있으면 그 값,
               null 이면 ring.firstEntry() 의 값  (한 바퀴 되감기)

[1] 보통 경우 - 키의 자리에서 오른쪽으로 처음 만나는 자리의 노드가 맡는다

    자리   120     350     610     880    1240    1600
          ( A )   ( B )   ( C )   ( A )   ( B )   ( C )
    ----|-------|-------|-------|-------|-------|-------|----
                        ^
                   key "k1" 의 자리 = 430
                        +------> 오른쪽 첫 자리 610 -> C 가 맡는다
    ceilingEntry(430) = { 610 -> C }

[2] 되감김 - 가장 큰 자리보다 뒤에 떨어진 키

    ----|-------|-------|-------|-------|-------|-------|- ... -|
       120     350     610     880    1240    1600          2^32-1
                                                    ^
                                            key "k2" 의 자리 = 1900
                                                    +--> 오른쪽에 자리가 없다
    ceilingEntry(1900) = null  ->  ring.firstEntry() = { 120 -> A }
    원이니까 "없는" 것이 아니라 한 바퀴 돌아 첫 자리로 간다.
    이 분기를 빠뜨리는 것이 이 문제에서 제일 흔한 실수다.
    그리고 잘 안 걸린다 - 자리가 1000개면 키 100,000개 중 18개뿐이다.

비용 : TreeMap 의 ceilingEntry = 정렬된 자리에 대한 이진 탐색 = O(log(자리 수))
       자리 수 = 노드 수 x virtualNodes 이므로 O(log(n * v))
       링이 비어 있으면 null. key 가 null 이면 IllegalArgumentException.
```

### 동작 — 노드 추가 / 제거

```
[1] addNode("D") -> addSlots("D", virtualNodes)
      i = 0 .. count-1 : ring.put(hash.position(virtualName("D", i)), "D")
      마지막에 placed.put("D", count)      <- virtualNodes 가 아니라 count 를 넣어야 한다
                                              (가중치 링에서 자리 300개 찍고 100개만 기억하게 된다)

    before   자리   120     350     610             880    1240    1600
                   ( A )   ( B )   ( C )           ( A )   ( B )   ( C )
            ------|-------|-------|---------------|-------|-------|------
            구간   |<--B-->|<--C-->|<------A------>|<--B-->|<--C-->|
                   121..350 351..610   611..880    881..1240 ...

    after    D 의 자리 하나가 700 에 들어왔다
                   120     350     610    700      880    1240    1600
                   ( A )   ( B )   ( C )  ( D )    ( A )   ( B )   ( C )
            ------|-------|-------|------|--------|-------|-------|------
            구간   |<--B-->|<--C-->|<-D-->|<--A--->|<--B-->|<--C-->|
                                    ^^^^^^
                                    611..700 만 A 에서 D 로 옮겨간다
                                    (D 와 그 반시계 이웃 610 사이의 구간)
            701..880 은 그대로 A. 그 밖의 구간은 손도 안 댄다.

[2] removeNode("D")
      count = placed.remove("D")                    없으면 IllegalArgumentException
      자리는 저장돼 있지 않다 -> 넣을 때와 같은 이름으로 다시 계산해서 찾는다
      i = 0 .. count-1 : position = hash.position(virtualName("D", i))
                         "D".equals(ring.get(position)) 일 때만 ring.remove(position)
                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ 남의 자리를 지우지 않기 위한 확인
      두 가상 이름이 같은 자리에 떨어지면 TreeMap 이 조용히 덮어쓴 상태다.
      확인 없이 지우면 남의 자리가 사라지고, 그 노드는 원에서 조금씩 없어진다.
      (실제 해시로는 거의 안 나서 키 100,000개로도 안 보인다. 구조 테스트가 겹치는 해시를 주입한다)

      D 를 빼면 611..700 이 다시 A 로 돌아간다. 그 밖은 아무것도 안 움직인다.

이동량 : 키 K 개, 노드 n 개에서 노드 하나를 넣거나 뺄 때 움직이는 키 = 대략 K/n
         새로 생기거나 사라진 자리 앞 구간만 바뀌고, 남은 자리들 사이 구간은 불변이기 때문이다.
         같은 상황에서 모듈로는 거의 K 전부가 움직인다(위 ModuloSharding 표).
비용   : addNode / removeNode 모두 자리 v 개마다 TreeMap 연산 -> O(v log(n*v))
```

### 동작 — 가상 노드

```
virtualName(node, i) = node + "#" + i        i 는 0 부터 count-1 까지
  이 규칙이 계약이다. removeNode 가 같은 이름을 다시 만들어 자리를 찾기 때문이다.
  addNode 는 count = virtualNodes 로 부른다 (기본 DEFAULT_VIRTUAL_NODES = 100)

[1] virtualNodes = 1 : 노드 하나가 자리 하나. 구간 길이가 들쭉날쭉하다.

   0                                                              2^32-1
   |--------|-------------------------------|------|----------------|
           A                                B      C          (되감김 -> A)
   |<--A--->|<-------------- B ------------>|<--C->|<------ A ----->|
   자리 몇 개를 무작위로 찍었을 때 그 사이가 고르게 나뉠 이유가 없다.
   실측으로 최대 구간이 최소 구간의 18배였다.

[2] virtualNodes = 3 : A#0 A#1 A#2 / B#0 B#1 B#2 / C#0 C#1 C#2 를 각각 해시해 흩는다

   0                                                              2^32-1
   |---|-----|--|------|----|--|-------|-----|--|--------|---|--------|
      A#0   B#1 C#2   A#2  B#0 C#0    A#1  B#2 C#1    (되감김 -> A#0)
   |<A>|<-B->|<C>|<-A->|<-B>|<C>|<--A-->|<-B->|<C>|<---A--->|<C>|<-A->|
   큰 조각과 작은 조각이 섞여 서로 상쇄된다 -> 노드별 몫의 합이 고르게 간다.
   자리가 많아질수록 더 고르다. 기본값 100 이 그래서 100 이다.

대가 : slotCount = 노드 수 x virtualNodes 만큼 TreeMap 항목이 늘어난다 (메모리)
       탐색도 O(log n) 이 아니라 O(log(n*v)) 가 된다
주의 : 해시가 나쁘면 소용없다. Hashing.WEAK 는 String.hashCode 라
       node-0 과 node-1 의 자리가 정확히 1 만큼 떨어진다 -> 노드 열 대가 원의 한 점에 뭉친다.
       그러면 가상 노드를 아무리 늘려도 분포가 안 펴진다. BalanceTest 가 그것을 잰다.
```

### 필드
- `DEFAULT_VIRTUAL_NODES` — 역할:
- `ring` — 역할:
- `placed` — 역할:
- `virtualNodes` — 역할:
- `hash` — 역할:

### `ConsistentHashRing()` / `ConsistentHashRing(int virtualNodes)` / `ConsistentHashRing(int virtualNodes, RingHash hash)`
- 하는 일:
- 논리:
- 비용(왜):

### `static String virtualName(String node, int index)`
- 하는 일:
- 논리:
- 비용(왜):

### `int virtualNodes()` (protected)
- 하는 일:
- 논리:
- 비용(왜):

### `void addNode(String node)`
- 하는 일:
- 논리:
- 비용(왜):

### `void addSlots(String node, int count)` (TODO, protected)
- 하는 일:
- 논리:
- 비용(왜):

### `void removeNode(String node)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `String getNode(String key)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `int nodeCount()` / `List<String> nodes()` / `int slotCount()`
- 하는 일:
- 논리:
- 비용(왜):

### `int slotsOf(String node)`
- 하는 일:
- 논리:
- 비용(왜):

### `SortedMap<Long, String> ringView()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — WeightedConsistentHashRing (`src/main/java/com/datastructure/conshash/WeightedConsistentHashRing.java`)

### 동작 — 가중치가 자리 수가 되는 곳 (부모와의 차이)

```
부모 ConsistentHashRing 과 다른 것은 addNode(node, weight) 한 줄뿐이다.
링 구조도(TreeMap), 배정 규칙도(시계방향 첫 노드) 그대로다.

  ConsistentHashRing.addNode(node)          -> addSlots(node, virtualNodes())
  Weighted...     .addNode(node, weight)    -> addSlots(node, virtualNodes() * weight)
                                                             ^^^^^^^^^^^^^^^^ 이 곱셈이 전부
  weight < 1 이면 IllegalArgumentException. weight = 1 이면 addNode(node) 와 같다.

virtualNodes = 3 일 때
  addNode("A", 1) -> 자리 3개    A#0 A#1 A#2
  addNode("B", 2) -> 자리 6개    B#0 B#1 B#2 B#3 B#4 B#5
  addNode("C", 3) -> 자리 9개    C#0 C#1 ... C#8

   0                                                              2^32-1
   |--|---|--|---|--|--|---|--|--|--|---|--|--|---|--|--|--|--|------|
     A   C   B   C   B  C   A  C   B  C   A  C   B   C  B  C  C   (되감김)
   |<-각 자리가 자기 앞 구간을 맡는다. 자리가 많을수록 구간 길이의 합이 커진다 ->|

  placed = { A:3, B:6, C:9 }    slotsOf("B") = 6    slotCount() = 18

  구간 합의 기댓값 = 링 전체 x (그 노드의 자리 수 / 전체 자리 수)
      노드    자리 수    몫의 기댓값        가중치
      ----    -------    -----------        ------
       A         3        3/18 = 1/6           1
       B         6        6/18 = 2/6           2
       C         9        9/18 = 3/6           3
      -> 가중치 1 : 2 : 3 이 그대로 몫의 비가 된다

이게 가능한 이유 : 배정 규칙에 노드 수 N 이 안 들어 있기 때문이다.
    모듈로에서 같은 것을 하려면 목록에 같은 이름을 두 번 넣어야 하고, 그러면 N 이 커져
    이동량 문제가 더 나빠진다.
정확히 비율대로는 안 나온다 : 자리를 무작위로 찍는 이상 오차가 남는다.
    BalanceTest 가 같은 가중치인 두 노드 사이에서도 6% 차이가 난다는 것까지 적어둔다.
```

### 필드
- 자체 필드 없음 — `ConsistentHashRing` 의 `ring` / `placed` / `virtualNodes` / `hash` 를 상속해 쓴다. 역할:

### `WeightedConsistentHashRing()` / `WeightedConsistentHashRing(int virtualNodes)` / `WeightedConsistentHashRing(int virtualNodes, RingHash hash)`
- 하는 일:
- 논리:
- 비용(왜):

### `void addNode(String node, int weight)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — JumpConsistentHash (`src/main/java/com/datastructure/conshash/JumpConsistentHash.java`)

### 동작 — 링 없이 점프로 버킷 찾기 (링과의 차이)

```
링도 자리도 가상 노드도 없다. 들고 있는 것은 nodes 목록 하나뿐이고 slotCount() 는 늘 0 이다.

  ConsistentHashRing : TreeMap 에 자리 (노드 수 x virtualNodes) 개  -> 메모리 O(n*v)
  JumpConsistentHash : 저장하는 자리 0 개                            -> 메모리 O(1)

  getNode(key) = nodes.get( jumpHash(Hashing.fnv64(key), nodes.size()) )
                                     ^^^^^^^^^^^^^^^^^^ 섞을 필요 없다. jumpHash 가 안에서 굴린다.
                 nodes 가 비어 있으면 null (안 막으면 jumpHash 가 -1 을 주고 get(-1) 이 터진다)

jumpHash(key, numBuckets) : 지역 변수 둘과 반복문 하나. 자료구조가 없다.

   b = -1     b : 마지막으로 "여기다" 하고 정한 버킷
   j =  0     j : 다음에 자리가 바뀌는 시점
   +-------------------------------------------------------------+
   |  j < numBuckets 인 동안 반복                                  |
   |     b = j                                                    |
   |     key = key * 2862933555777941757L + 1      (선형 합동 생성기) |
   |     j = (b + 1) * ( 2^31 / ((key >>> 33) + 1) )              |
   |                     ^^^^^^^^^^^^^^^^^^^^^^^ 나눗셈은 double     |
   |                             ^^^ 논리 시프트. >> 를 쓰면 음수가 되어 |
   |                                 j 가 뒤로 가고 무한 루프다        |
   +-------------------------------------------------------------+
   반복이 끝나면 b 가 답 (long 을 int 로 좁힌다. b < numBuckets 이라 안전)
   numBuckets 가 0 이면 반복이 한 번도 안 돌아 -1. 그 값이 계약이다.

   numBuckets = 8 인 키 하나의 자취 (j 값은 예시)

       버킷    0    1    2    3    4    5    6    7  |  8 이상 = 범위 밖
             +----+----+----+----+----+----+----+----+
    b = 0    [ *  ]                                       j = 2   (8 미만 -> 계속)
    b = 2              [ *  ]                             j = 3   (8 미만 -> 계속)
    b = 3                   [ *  ]                        j = 11  (8 이상 -> 멈춤)
             +----+----+----+----+----+----+----+----+
                             ^ 답 = b = 3

   버킷을 늘려도 답이 유지되는 이유 : 버킷이 N 개에서 N+1 개로 늘 때 각 키는 확률 1/(N+1) 로만
   새 버킷으로 옮겨가고, 기존 버킷끼리는 절대 주고받지 않는다.
   같은 key 를 같은 LCG 로 굴리면 늘 같은 난수열이 나오므로 아무것도 저장할 필요가 없다.

비용 : 점프 횟수의 기댓값 O(log numBuckets), 메모리 O(1)
       링은 O(log(n*v)) 탐색 + O(n*v) 메모리. 균형도 이쪽이 낫다
       (가상 노드 5000개짜리 링이 1.106 일 때 점프는 1.026)

무엇을 포기했나 : 버킷 번호가 0 부터 N-1 까지 빈틈없이 이어져야 한다

   nodes   [ A ][ B ][ C ][ D ]        removeNode("D") : 맨 뒤 -> OK
             0    1    2    3          removeNode("B") : UnsupportedOperationException
                       ^^^^^                             (메시지에 뺄 수 있는 것을 적는다.
                       여기만 뺄 수 있다                    거부할 때 목록은 안 바뀐다)

   밀어서 채우면 되지 않나 -> [ A ][ C ][ D ] 로 당기는 순간 C 와 D 의 번호가 전부 하나씩 바뀐다
             before  0:A  1:B  2:C  3:D
             after   0:A  1:C  2:D            <- C 와 D 를 가리키던 모든 키가 어긋난다
   MovementTest 실측 : 그때 이동량 28,682개. 1/N 인 10,000개가 아니다.
   아무 노드나 죽을 수 있는 곳에서는 링 방식이 여전히 필요하다.
```

### 필드
- `nodes` — 역할:

### `static int jumpHash(long key, int numBuckets)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `void addNode(String node)`
- 하는 일:
- 논리:
- 비용(왜):

### `void removeNode(String node)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `String getNode(String key)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `int nodeCount()` / `List<String> nodes()` / `int slotCount()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| ModuloSharding | | | |
| ConsistentHashRing | | | |
| WeightedConsistentHashRing | | | |
| JumpConsistentHash | | | |

## 핵심 문장

<!-- 지도 수준의 문장들 — 세부가 아니라 "왜 이 구조인가"를 담은 문장 -->

-
-
-

## 관련 자료

- 원본 README: `/home/jun/project/myway/data-structure/31-consistent-hashing/README.md`
- 구현 대상: `/home/jun/project/myway/data-structure/31-consistent-hashing/src/main/java/com/datastructure/conshash/`
- 테스트: `/home/jun/project/myway/data-structure/31-consistent-hashing/src/test/java/com/datastructure/conshash/`
- 정답 구현: `/home/jun/project/myway/data-structure/31-consistent-hashing/impl/`
