# data-structure/31-consistent-hashing — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.
> 2026-09-14: 쉽게 풀어쓴 확장(Claude 작성) — 한눈에 절·동작 그림·용어 풀이 추가.

## 한눈에 — 쉽게 말하면

**비유: 둥근 광장에 가게들이 띄엄띄엄 있고, 손님은 자기 자리에서 시계방향으로 걷다가 처음 만나는 가게로 간다.**

- 데이터(키)를 여러 서버(노드)에 나눠 담아야 한다. 제일 쉬운 방법은 "키 번호를 서버 수로 나눈 나머지"로 정하는 것.
- 그런데 이 방법은 서버가 한 대 늘거나 줄면 나눗셈의 분모가 바뀌어서, 거의 **모든** 데이터가 다른 서버로 이사해야 한다.
- 일관된 해싱(consistent hashing)은 서버들을 큰 원 위의 점으로 찍어두고, 키도 원 위의 한 점으로 찍는다. 키는 자기 점에서 시계방향으로 처음 만나는 서버가 맡는다.
- 이러면 서버 하나가 빠져도 **그 서버가 맡던 구간의 키만** 옆 서버로 옮기면 되고, 나머지는 전혀 안 움직인다.
- 점 하나만 찍으면 구간이 들쭉날쭉하니까, 서버 하나를 원 위 100곳에 찍는다(가상 노드) — 그러면 몫이 고르게 나뉜다.

```text
        [원(시계판)]                 키 k 의 자리에서 시계방향으로
             A                      처음 만나는 서버가 k 를 맡는다
          .--*--.
         /       \
      C *         * B               k --> ( 걷는다 ) --> B 가 맡음
         \   k   /
          '--o->'
```

이 "광장의 가게 찾기"와 **똑같은 구조**가 실무의 분산 캐시다 — Redis Cluster, CDN, 분산 데이터베이스가 "이 데이터는 어느 서버에 있나"를 정할 때 바로 이 원(링)을 쓴다. 가게 = 캐시 서버, 손님 = 키, 가게 폐업 = 서버 장애.

## 문제 — 이 챕터가 시키는 것

원본 README는 05번의 `hash(key) % N` 을 **서버 목록**에 그대로 쓰면 서버 한 대가 죽는 순간 거의 전부가 자리를 옮긴다는 데서 출발한다 — 키 10만·서버 10대에서 모듈로 **89,905개(89.9%)** 대 일관된 해싱 **12,044개(12.0%)** 다.\
차이는 **N 이 식 안에 있느냐**다 — 일관된 해싱은 노드와 키를 같은 원에 올리고 키가 시계 방향 첫 노드를 만나게 하므로 배정 규칙에 N 이 없고 **자리들의 배치만** 있다.\
"다음에 오는 자리를 찾는다"는 06번 BST 의 `ceilingKey` 그대로이고, **원이라는 것은 마지막에서 처음으로 돌아온다는 규칙 한 줄**뿐이다.\
과제는 네 구현(`ModuloSharding` · `ConsistentHashRing` · `WeightedConsistentHashRing` · `JumpConsistentHash`)을 만들어 **자리 메모리 / 한 대 죽을 때 이동량 / 가중치 / 가운데 제거 가능** 네 축으로 나란히 재는 것이고, 재는 것은 속도가 아니라 **이동량**이다.

과제 목록 — `src/main/java/com/datastructure/conshash/`의 TODO 8개:

- `ModuloSharding`(기준선) — TODO 1(`getNode` — `bucketHash(key) % nodes.size()`)
- `ConsistentHashRing`(본체) — TODO 2(`addSlots` — 가상 이름으로 count 곳에 올리기) · TODO 3(`removeNode` — 그 노드의 자리만 지우기) · TODO 4(`getNode` — `ceilingEntry` + 되감기 한 줄)
- `WeightedConsistentHashRing` — TODO 5(`addNode(node, weight)` — 자리를 weight 배로)
- `JumpConsistentHash` — TODO 6(`jumpHash` — 논문 의사코드) · TODO 7(`removeNode` — 맨 뒤만, 아니면 `UnsupportedOperationException`) · TODO 8(`getNode`)

순서: `HashRingContractTest.java`를 따라 친 뒤 `ModuloSharding` → `ConsistentHashRing` → `WeightedConsistentHashRing` → `JumpConsistentHash`.\
실행: `cd ~/project/myway/data-structure && ./run.sh 31` — README 기준 **84개 중 69개가 실패**한다.\
(참고: README 의 "TODO 2개/6개/2개/6개"는 `TODO` **문자열** 등장 수이고, 실제 과제 항목은 위 8개다 — 항목마다 주석 1회 + `throw` 1회로 두 번씩 나온다.)

아래 서머리는 이 문제(README)를 분석·정리한 것이다.

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

언제 보나: "나머지로 나누는 방식(모듈로)이 왜 안 되는가"를 확인할 때. 아래 그림은 노드가 3대에서 4대로 늘어난 전/후를 나란히 놓고, 키 7개가 전부 이사하는 것을 보여준다.

  - *모듈로(%)*: 나눗셈의 나머지. 키의 해시값을 노드 수로 나눈 나머지가 담당 노드 번호가 된다.
  - *해시(bucketHash)*: 문자열을 큰 숫자 하나로 바꾸는 함수. 같은 입력이면 늘 같은 숫자.

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

언제 쓰나: `getNode(key)` — "이 키는 어느 노드가 맡나"를 답할 때. 아래 그림 [1]은 보통 경우(오른쪽으로 걷다 처음 만나는 자리), [2]는 원의 끝을 지나 처음으로 되돌아오는 경우(되감김)다.

  - *TreeMap*: 자리(숫자)를 항상 정렬된 순서로 보관하는 자바의 맵. 링 그 자체다.
  - *ceilingEntry(x)*: 그 맵에서 "x 이상 중 가장 작은 항목"을 찾는 연산 = 시계방향으로 처음 만나는 자리.

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

언제 쓰나: 서버를 새로 들이거나(`addNode`) 뺄 때(`removeNode`). 아래 그림 [1]은 D가 들어오기 전/후를 비교한다 — D의 자리 바로 앞 구간(611..700)만 주인이 바뀌고 나머지는 그대로라는 것이 이 자료구조의 존재 이유다. [2]는 뺄 때 "남의 자리를 지우지 않기 위한 확인"이 왜 필요한지를 보여준다.

  - *구간*: 원 위에서 어떤 자리와 그 반시계(왼쪽) 이웃 자리 사이의 범위. 그 자리의 노드가 그 구간의 키를 전부 맡는다.

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

언제 쓰나: 노드마다 점을 하나만 찍으면 구간이 들쭉날쭉해서(실측 18배 차이) 몫이 불공평해진다. 그래서 노드 하나를 여러 이름(A#0, A#1, ...)으로 여러 곳에 찍는다. 아래 그림 [1]은 점 하나일 때의 불균형, [2]는 점 3개일 때 큰 조각·작은 조각이 섞여 상쇄되는 모습이다.

  - *가상 노드(virtual node)*: 진짜 서버는 하나인데 원 위에는 여러 점으로 존재하는 것. 이름 끝에 `#번호`를 붙여 만든다.

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

언제 쓰나: 서버들의 성능이 다를 때 — 좋은 서버에 2배, 3배의 몫을 주고 싶을 때. 방법은 "점을 그 배수만큼 더 찍는다"가 전부다. 아래 그림은 가중치 1:2:3인 세 노드의 점 개수(3:6:9)와, 그 비율이 그대로 몫의 비가 되는 계산이다.

  - *가중치(weight)*: 그 노드가 받을 몫의 배수. 가상 노드 수에 곱해져서 점 개수가 된다.

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

언제 쓰나: 링(TreeMap)의 메모리조차 아끼고 싶고, 노드가 "맨 뒤에서만" 늘고 줄어도 될 때. 저장하는 것 없이 계산만으로 키의 버킷을 정한다. 아래 그림은 키 하나가 버킷 0 → 2 → 3으로 점프하다가 범위를 벗어나는 순간 멈추고, 마지막 버킷 3이 답이 되는 과정이다.

  - *LCG(선형 합동 생성기)*: `key = key * 큰수 + 1`만으로 다음 난수를 만드는 생성기. 같은 키면 늘 같은 난수열 — 그래서 아무것도 저장할 필요가 없다.
  - *논리 시프트(`>>>`)*: 비트를 오른쪽으로 밀며 빈자리를 0으로 채우는 연산. `>>`를 쓰면 음수가 유지되어 무한 루프가 된다.

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

## 용어 풀이

- **해시(hash)**: 아무 문자열이나 넣으면 정해진 범위의 숫자 하나가 튀어나오는 함수. 같은 입력이면 늘 같은 숫자가 나온다.
- **키(key)**: 저장하거나 찾으려는 데이터의 이름표. 예: 사용자 아이디.
- **노드(node)**: 데이터를 나눠 맡는 서버(컴퓨터) 하나.
- **샤딩(sharding)**: 데이터를 여러 서버에 쪼개 나눠 담는 것.
- **모듈로(%, 나머지 연산)**: 나눗셈의 나머지. `h % 3`은 h를 3으로 나눈 나머지(0, 1, 2 중 하나).
- **버킷(bucket)**: 키가 배정되는 칸(번호 붙은 통). 여기서는 노드 번호와 같은 뜻으로 쓰인다.
- **링(ring)**: 0부터 2^32-1까지의 숫자 범위를 원처럼 이어붙인 것. 끝을 지나면 처음으로 되돌아온다.
- **되감김(wrap-around)**: 원의 가장 큰 자리보다 뒤에 떨어진 키가 한 바퀴 돌아 첫 자리로 가는 것.
- **가상 노드(virtual node)**: 서버 하나를 원 위 여러 곳(기본 100곳)에 찍은 점들. 구간을 고르게 만들기 위한 것.
- **가중치(weight)**: 성능 좋은 서버에 더 많은 몫을 주는 배수. 가상 노드 수를 그 배수만큼 늘려서 구현한다.
- **TreeMap / NavigableMap**: 키를 정렬된 순서로 보관하는 자바의 맵. "이 값 이상인 것 중 가장 작은 항목"(`ceilingEntry`) 같은 질문에 빠르게 답한다.
- **`ceilingEntry(x)`**: 정렬된 맵에서 x 이상인 것 중 가장 작은 항목을 찾는 연산. "시계방향으로 처음 만나는 자리"가 정확히 이것이다.
- **이진 탐색(binary search)**: 정렬된 것에서 절반씩 잘라가며 찾는 방법. n개 중에서 log n번 만에 찾는다.
- **O(log n), O(1), O(n)**: 데이터가 n개일 때 걸리는 시간의 대략적 규모. O(1)은 n과 무관하게 일정, O(log n)은 n이 두 배 되어도 한 걸음만 늘어남, O(n)은 n에 비례.
- **LCG(선형 합동 생성기)**: `key = key * 큰수 + 1`처럼 곱하고 더하기만으로 다음 난수를 만드는 아주 단순한 난수 생성기. 같은 시작값이면 늘 같은 수열이 나온다 — jumpHash가 "저장 없이" 동작하는 비밀.
- **논리 시프트(`>>>`)**: 비트를 오른쪽으로 밀면서 빈자리를 무조건 0으로 채우는 연산. `>>`는 음수일 때 1로 채워서 음수가 유지된다 — 그래서 jumpHash에서 `>>`를 쓰면 무한 루프가 된다.
- **FNV**: 문자열을 64비트 숫자로 바꾸는 간단하고 빠른 해시 함수의 이름.
- **계약(인터페이스)**: 구현들이 공통으로 지키기로 한 메서드 목록과 약속(HashRing이 그것).
- **`IllegalArgumentException` / `UnsupportedOperationException`**: 자바에서 "잘못된 값을 줬다" / "이 동작은 지원 안 한다"를 알리는 예외(에러 신호).
- **이동량(movement)**: 노드 수가 바뀔 때 배정이 달라져 이사해야 하는 키의 개수. 이 문제 전체의 평가 기준.

## 관련 자료

- 원본 README: `/home/jun/project/myway/data-structure/31-consistent-hashing/README.md`
- 구현 대상: `/home/jun/project/myway/data-structure/31-consistent-hashing/src/main/java/com/datastructure/conshash/`
- 테스트: `/home/jun/project/myway/data-structure/31-consistent-hashing/src/test/java/com/datastructure/conshash/`
- 정답 구현: `/home/jun/project/myway/data-structure/31-consistent-hashing/impl/`
