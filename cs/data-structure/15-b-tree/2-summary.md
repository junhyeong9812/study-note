# data-structure/15-b-tree — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 계약 — SearchTree (`src/main/java/com/datastructure/btree/SearchTree.java`)

- `V put(K key, V value)`
- `V get(K key)`
- `boolean containsKey(K key)`
- `V remove(K key)`
- `int size()`
- `boolean isEmpty()`
- `void clear()`
- `List<K> keys()`
- `K firstKey()`
- `K lastKey()`
- `int height()`

## 구현 — BTree (`src/main/java/com/datastructure/btree/BTree.java`)

<!-- 메서드마다 내 언어로. 복잡도는 "왜 그런지"까지. -->

### 구조

```
BTree(minDegree t) : 노드 키 개수 = t-1 개 이상 2t-1 개 이하, 자식 개수 = 키 개수 + 1
                     아래 그림은 전부 t = 2 (maxKeys = 2t-1 = 3, minKeys = t-1 = 1) = 2-3-4 트리

노드 하나 (Node) -- keys / values / children 세 리스트가 나란히 간다
+---------------------------------------------------------+
| keys     |   30   |   60   |   90   |   (오름차순)       |
| values   |   vA   |   vB   |   vC   |   (키와 같은 자리) |
| children | c0  |  c1  |  c2  |  c3  |   (키보다 1 개 많다)|
+------------|------|------|------|----------------------- +
             v      v      v      v
           30 미만  30~60  60~90  90 초과      각 자식이 맡는 키 구간
leaf() == children.isEmpty()  -- 잎은 자식 리스트가 비어 있다

전체 모습 (t=2, 10 20 30 ... 130 을 순서대로 put 한 결과)

                        +---------+
                        | 40   80 |            root : 키 2 개, 자식 3 개
                        +---------+
                 +----------+ |  +----------+
                 v            v             v
             +------+     +------+      +-------+
             |  20  |     |  60  |      |  100  |
             +------+     +------+      +-------+
              /    \       /    \        /     \
          +----+ +----+ +----+ +----+ +----+ +--------------+
          | 10 | | 30 | | 50 | | 70 | | 90 | | 110 120 130  |
          +----+ +----+ +----+ +----+ +----+ +--------------+

- 모든 잎의 깊이가 같다. 트리가 아래로 자라지 않고 "위로" 자라기 때문 (동작 - 추가 [3])
- values 가 내부 노드에도 있다. 키를 만난 그 자리에서 값을 돌려준다 (BPlusTree 와 다른 점)
```

### 동작 — 검색

```
get(key) : 노드 안에서 lowerBound(key) 로 자리 i 를 잡는다
           keys[i] == key 면 values[i] 반환 / 잎이면 null / 아니면 children[i] 로 내려간다

get(70)
                    +---------+
                    | 40   80 |   lowerBound(70) = 1   (40 < 70 <= 80)
                    +---------+   keys[1]=80 != 70  -> children[1]
                         |
                         v   40 초과 80 미만 구간
                    +------+
                    |  60  |      lowerBound(70) = 1   (60 < 70, 키 끝)
                    +------+      잎 아님        -> children[1]
                         \
                          v
                       +------+
                       |  70  |   lowerBound(70) = 0, keys[0] == 70 -> values[0]
                       +------+

키 i 개짜리 노드는 자식이 i+1 개라서 "키 사이 구간"이 빠짐없이 자식 하나에 대응한다
비용 : 높이 O(log_t n) 번 노드를 읽고, 노드 안은 이분탐색 O(log t) -> 전체 O(log n)
       t 를 키우면 높이가 낮아진다 = 디스크 블록 읽기 횟수가 준다 (B-트리를 쓰는 이유)
```

### 동작 — 추가

```
put 은 내려가면서 "꽉 찬 노드를 미리 쪼갠다"(preemptive split). 그래서 되돌아 올라오며
고칠 일이 없다. 쪼갤 때 가운데 키 keys[t-1] 하나가 부모로 올라간다.

[1] 잎에 자리가 있으면 그냥 끼워 넣는다. O(t) (리스트 밀기)
    +--------+            +-------------+
    | 30  50 |     ->     | 30  40  50  |    keys.add(i, key) / values.add(i, value)
    +--------+            +-------------+

[2] 내려갈 자식이 꽉 찼다(키 2t-1=3 개) -> splitChild(parent, i)
    put(60) : root=[20], children[1] = [30 40 50] 이 가득

    before                                after
       +------+                              +----------+
       |  20  |                              |  20   40 |   <- 가운데 40 이 부모로 승격
       +------+                              +----------+
        /    \                    ->          /    |    \
    +----+ +------------+               +----+  +----+  +----+
    | 10 | | 30  40  50 |               | 10 |  | 30 |  | 50 |
    +----+ +------------+               +----+  +----+  +----+
             ^^^^                                          |
             keys[t-1] = keys[1] = 40                       v  이어서 60 을 여기 삽입
    왼쪽은 keys[0..t-2] = [30] 을 남기고, 오른쪽 새 노드가 keys[t..] = [50] 을 가져간다
    부모에 키 1 개 + 자식 1 개가 늘어난다 -> 부모는 늘 여유가 있다(미리 쪼개 두었으므로)

[3] root 가 꽉 찬 채로 put 이 들어오면 -> 새 root 를 만들고 그 아래에서 쪼갠다. 높이 +1
    put(40) : root = [10 20 30] 이 가득

    before               새 root 를 씌우고                after
    +------------+       splitChild(newRoot, 0)      +------+
    | 10  20  30 |            ->                     |  20  |   높이 1 -> 2
    +------------+                                   +------+
                                                      /    \
                                                 +----+   +---------+
                                                 | 10 |   | 30  40  |
                                                 +----+   +---------+
    B-트리가 위로 자라는 유일한 지점. 그래서 모든 잎의 깊이가 항상 같다

[4] 내부 노드가 쪼개질 때는 자식 포인터도 같이 갈린다
    put(130) : root=[40], children[1] = [60 80 100] 이 가득 (자식 4 개)

    before                                    after
        +------+                                  +----------+
        |  40  |                                  |  40   80 |
        +------+                                  +----------+
         /    \                        ->          /    |    \
    +------+  +--------------+          +------+ +------+  +-------+
    |  20  |  | 60  80  100  |          |  20  | |  60  |  |  100  |
    +------+  +--------------+          +------+ +------+  +-------+
     /  \      /   |    |    \           /  \     /   \      /    \
    10  30    50  70   90  110 120      10  30   50   70    90  110 120
                                        keys[t..]=[100] 과 children[t..]=(90),(110 120)
                                        이 함께 오른쪽으로 넘어간다

비용 : 뿌리에서 잎까지 한 번 내려가며 필요할 때만 쪼갠다 -> O(log n)
```

### 동작 — 삭제

```
지우려는 키를 만나기 전에 "내려갈 자식의 키가 t-1 개뿐이면" 먼저 채워 놓는다(fill).
채우는 방법은 형제에게 빌리기(borrow) 또는 형제와 합치기(merge) 두 가지다. t = 2 이므로
키 1 개짜리 노드가 부족한(underfull) 노드다.

[1] borrow : 옆 형제가 t 개 이상 가졌으면 부모를 거쳐 한 칸 돌린다 (회전)
    remove(30) -- 내려갈 [30] 이 부족, 오른쪽 형제 [50 60] 은 여유 있음

    before                              after (borrowFromRight)
        +----------+                        +----------+
        | 20    40 |                        | 20    50 |   부모 키가 40 -> 50 으로 갱신
        +----------+            ->          +----------+
        /    |     \                        /    |     \
    +----+ +----+ +---------+          +----+ +-------+ +------+
    | 10 | | 30 | | 50   60 |          | 10 | | 30 40 | | 60   |
    +----+ +----+ +---------+          +----+ +-------+ +------+
             ^        |                         ^
             |        +-- 형제의 첫 키 50 이 부모로
             +----------- 부모 키 40 이 부족한 쪽으로 내려온다
    그 다음 [30 40] 안에서 30 을 지운다 -> [40].  키 순서는 그대로 유지된다

[2] merge : 양쪽 형제가 다 빠듯하면 부모 키 하나를 끌어내려 셋을 하나로 합친다
    remove(10) -- [10] 도 [30] 도 키 1 개뿐

    before                              after (mergeChildren)
        +----------+                        +------+
        | 20    40 |                        |  40  |   부모에서 키 20 이 빠져 내려간다
        +----------+            ->          +------+
        /    |     \                         /    \
    +----+ +----+ +---------+        +------------+ +---------+
    | 10 | | 30 | | 50   60 |        | 10  20  30 | | 50   60 |
    +----+ +----+ +---------+        +------------+ +---------+
      \     /                          그 다음 여기서 10 을 지운다 -> [20 30]
       \   /   합쳐진 노드는 (t-1) + 1 + (t-1) = 2t-1 개 = 정확히 꽉 찬 상태
    부모의 키가 줄어든다. 부모가 root 이고 키가 0 개가 되면 root = children[0] -> 높이 -1

[3] 지울 키가 내부 노드에 있으면 -- 잎의 키로 바꿔치기하고, 문제를 잎으로 미룬다
    remove(40) : 왼쪽 자식이 여유 있으면 그 부분트리의 최대 키(선행자 predecessor)를 올린다

    before                              after
        +------+                            +------+
        |  40  |                            |  30  |   <- 선행자 30 이 40 자리를 대신한다
        +------+              ->            +------+
        /     \                             /     \
    +----------+ +---------+          +--------+ +---------+
    | 10 20 30 | | 50   60 |          | 10  20 | | 50   60 |
    +----------+ +---------+          +--------+ +---------+
         ^^                             지운 것은 결국 잎의 30
    왼쪽이 빠듯하면 오른쪽 부분트리의 최소 키(후행자 successor)로, 양쪽 다 빠듯하면 [2] 로 합친 뒤
    합쳐진 노드에서 다시 지운다

비용 : 내려가는 길에서만 고친다 -> O(log n).  높이는 [2] 에서 root 가 비었을 때만 줄어든다
```

### `필드`

- `int minDegree` (t) 역할:
- `Node<K,V> root` 역할:
- `int size` 역할:
- `Node.keys` / `Node.values` / `Node.children` 역할:

### `public BTree(int minDegree)`

- 하는 일:
- 논리:
- 비용(왜):

### `private void splitChild(Node<K,V> parent, int i)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `private V insertNonFull(Node<K,V> node, K key, V value)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `private void removeFrom(Node<K,V> node, K key)` (TODO)

- 하는 일:
- 논리(네 경우):
- 비용(왜):

### `private int fill(Node<K,V> node, int i)` (TODO)

- 하는 일:
- 논리(우선순위와 반환값의 뜻):
- 비용(왜):

### `private void mergeChildren(Node<K,V> node, int i)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `public V put(K key, V value)`

- 하는 일:
- 논리(뿌리가 꽉 찼을 때):
- 비용(왜):

### `public V get(K key)`

- 하는 일:
- 논리:
- 비용(왜):

### `public V remove(K key)`

- 하는 일:
- 논리:
- 비용(왜):

### `public List<K> keys()`

- 하는 일:
- 비용(왜):

### `public K firstKey()` / `public K lastKey()`

- 하는 일:
- 비용(왜):

### `public int height()`

- 하는 일:
- 논리(왜 왼쪽 한 줄만 세면 되는가):
- 비용(왜):

### `public boolean containsKey(K key)` / `public int size()` / `public boolean isEmpty()` / `public void clear()`

- 하는 일:
- 비용(왜):

## 구현 — BPlusTree (`src/main/java/com/datastructure/btree/BPlusTree.java`)

### 구조

```
BPlusTree(order) : order = 노드 하나가 가질 수 있는 "자식의 최대 수". 키는 order-1 개까지
                   아래 그림은 전부 order = 4 (maxKeys = 3, minKeys = maxKeys/2 = 1)

BTree 와 다른 세 가지
  (1) values 는 잎에만 있다. 내부 노드에는 keys 만 있고 values 는 비어 있다
  (2) 내부 노드의 키는 "답"이 아니라 갈림길 표지판(구분키)일 뿐이다 -- 잎에 같은 키가 또 있다
  (3) 잎끼리 next 로 한 줄로 이어져 있다

10 20 30 ... 100 을 순서대로 put 한 결과 (order = 4)

                          +------+
                          |  70  |         내부 노드 : keys 만. values 는 빈 리스트
                          +------+         leaf == false
                          /      \
                +-----------+   +------+
                |  30    50 |   |  90  |
                +-----------+   +------+
                /     |     \    /     \
        +-------+ +-------+ +-------+ +-------+ +---------+
  잎 -> | 10 20 |>| 30 40 |>| 50 60 |>| 70 80 |>| 90 100  |-> null
        | vA vB | | vC vD | | vE vF | | vG vH | | vI  vJ  |
        +-------+ +-------+ +-------+ +-------+ +---------+
                ^ next     ^ next    ^ next    ^ next
                한 방향 연결 리스트 (splitLeaf 에서 right.next = node.next; node.next = right)

구분키 s 의 뜻 : 왼쪽 자식 < s <= 오른쪽 자식
  -- childIndex 가 keys[mid] <= key 일 때 오른쪽으로 가기 때문. 같은 키는 오른쪽 자식이 맡는다
  -- 그래서 구분키 70 은 내부 노드에도 있고 잎 [70 80] 에도 또 있다. 값은 잎 쪽에만 있다

BTree 와 나란히 놓으면
  BTree      : get(70) 이 내부 노드에서 70 을 만나면 거기서 끝 (깊이가 들쭉날쭉)
  BPlusTree  : get(70) 은 내부 노드에서 만나도 안 멈춘다. 늘 잎까지 내려간다 (깊이가 항상 같다)
```

### 동작 — 추가

```
BTree 와 달리 "미리 쪼개기"가 아니라, 잎에 먼저 넣고 넘치면 되돌아 올라오며 쪼갠다.
쪼개는 방식이 잎과 내부에서 다르다 -- 이게 이 자료구조의 핵심이다.

[1] splitLeaf : 가운데 키를 복사해서(copy up) 올린다. 키는 잎에도 그대로 남는다
    put(50) 으로 잎이 키 4 개(> maxKeys 3)가 된 순간

    before                              after
    +----------------+                  +---------+       +---------+
    | 30 40 50 60    |        ->        | 30  40  |-next->| 50  60  |
    | vC vD vE vF    |                  | vC  vD  |       | vE  vF  |
    +----------------+                  +---------+       +---------+
      mid = keys.size()/2 = 2                 \              /
      node 가 [0, mid) 을 남기고                 올라가는 키 = right.keys[0] = 50
      right 가 [mid, 끝) 을 가져간다             (50 은 오른쪽 잎에 그대로 남아 있다)
                                              +------+
                                     부모 ->  |  50  |   구분키로만 쓰인다
                                              +------+
    next 도 이어 붙인다 : right.next = node.next; node.next = right

[2] splitInternal : 가운데 키를 빼내서(push up) 올린다. 그 키는 이 노드에서 사라진다
    부모가 키 4 개가 된 순간

    before  (키 4 / 자식 5)
    +-------------------+
    | 30   50   70   90 |          mid = 4/2 = 2, up = keys[2] = 70
    +-------------------+
      c0   c1   c2   c3  c4

    after
                    +------+
                    |  70  |   <- 위로 "이동" (아래 어디에도 70 은 남지 않는다)
                    +------+
                    /      \
        +-----------+      +------+
        |  30   50  |      |  90  |
        +-----------+      +------+
         c0  c1  c2         c3  c4
    node 는 keys[0, mid) = [30 50] 과 children[0, mid] = c0 c1 c2 를 남기고
    right 가 keys[mid+1, 끝) = [90] 과 children[mid+1, 끝) = c3 c4 를 가져간다

[3] root 가 쪼개지면 새 root 를 만든다. 이때만 높이 +1 (모든 잎의 깊이가 같이 늘어난다)

왜 잎만 copy up 인가 : 잎이 모든 키를 하나도 빠짐없이 갖고 있어야 [범위 조회]가 잎 사슬만
걸어서 끝난다. 내부에서 키를 빼 가면 그 키가 사라지므로 잎에는 복사본을 남긴다
비용 : 잎까지 O(log n) 내려가고, 넘칠 때만 되돌아 올라오며 쪼갠다 -> O(log n)
```

### 동작 — 범위 조회

```
keysInRange(from, to) : from 이 있을 잎을 한 번만 찾고, 그 뒤로는 next 를 따라 걷는다

keysInRange(35, 85)

  1) findLeaf(35) -- 뿌리에서 잎까지 딱 한 번 내려간다  O(log n)
                          +------+
                          |  70  |   childIndex(35) : 70 <= 35 아님 -> 왼쪽
                          +------+
                          /
                +-----------+
                |  30    50 |         childIndex(35) : 30 <= 35 -> 오른쪽으로 한 칸
                +-----------+                          50 <= 35 아님 -> 여기서 멈춤
                      |
                      v
  2) lowerBound(35) = 1 부터 시작해 next 를 따라 to 를 넘을 때까지 줍는다  O(k)

        +-------+   +-------+   +-------+   +-------+   +---------+
        | 10 20 |   | 30 40 |-->| 50 60 |-->| 70 80 |-->| 90 100  |-> null
        +-------+   +-------+   +-------+   +-------+   +---------+
                        ^          |           |            |
                     시작 (40)   50 60       70 80       90 > 85 -> 즉시 종료

  결과 : [40, 50, 60, 70, 80]

비용 : O(log n + k). 내려가는 것은 처음 한 번뿐이고, 나머지는 잎 사슬 한 방향 걷기다
BTree 였다면 : 잎과 내부 노드를 오르내리며 중위 순회를 해야 한다(값이 내부에도 있으므로).
               잎 사슬이 없으므로 "다음 키"를 찾으려면 다시 위로 올라가야 한다
keys() 도 같은 원리다 -- firstLeaf() 하나 잡고 next 를 끝까지 따라가면 전체가 정렬 순서로 나온다
```

### `필드`

- `int order` 역할:
- `Node<K,V> root` 역할:
- `int size` 역할:
- `Node.leaf` / `Node.keys` / `Node.values` / `Node.children` / `Node.next` 역할:
- `record`성 보조 `Split<K,V>{ K key; Node right; }` 역할:

### `public BPlusTree(int order)`

- 하는 일:
- 논리:
- 비용(왜):

### `static int lowerBound(Node<K,V> node, K key)` (주어짐)

- 하는 일:
- 논리:
- 비용(왜):

### `static int childIndex(Node<K,V> node, K key)` (TODO)

- 하는 일:
- 논리(lowerBound 와 부등호가 왜 달라야 하는가):
- 비용(왜):

### `private Split<K,V> splitLeaf(Node<K,V> node)` (TODO)

- 하는 일:
- 논리(올려보낼 키를 잎에 남기는가):
- 비용(왜):

### `private Split<K,V> splitInternal(Node<K,V> node)` (TODO)

- 하는 일:
- 논리(가운데 키를 올려보내고 지우는 이유):
- 비용(왜):

### `public List<K> keysInRange(K from, K to)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `private void fix(Node<K,V> node, int i)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `private void merge(Node<K,V> node, int i)` (TODO)

- 하는 일:
- 논리(잎 병합과 내부 병합의 차이 · `next` 이어주기):
- 비용(왜):

### `public V put(K key, V value)`

- 하는 일:
- 논리:
- 비용(왜):

### `public V get(K key)`

- 하는 일:
- 논리(왜 늘 잎까지 내려가는가):
- 비용(왜):

### `public V remove(K key)`

- 하는 일:
- 논리:
- 비용(왜):

### `public List<K> keys()`

- 하는 일:
- 논리(사슬 걷기):
- 비용(왜):

### `public K firstKey()` / `public K lastKey()`

- 하는 일:
- 비용(왜):

### `public int height()`

- 하는 일:
- 비용(왜):

### `public boolean containsKey(K key)` / `public int size()` / `public boolean isEmpty()` / `public void clear()`

- 하는 일:
- 비용(왜):

## 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| BTree (값이 모든 노드에) | | | |
| BPlusTree (값은 잎에만 + 잎 사슬) | | | |

## 핵심 문장

<!-- 지도 수준의 문장들 — 세부가 아니라 "왜 이 구조인가"를 담은 문장 -->

-
-
-

## 관련 자료

<!-- 원본 문서·코드 경로. 기준 소스는 문서가 아니라 코드/원전이다. -->

- README: `/home/jun/project/myway/data-structure/15-b-tree/README.md`
- 구현: `/home/jun/project/myway/data-structure/15-b-tree/src/main/java/com/datastructure/btree/`
- 테스트: `/home/jun/project/myway/data-structure/15-b-tree/src/test/java/com/datastructure/btree/`
- 정답 구현: `/home/jun/project/myway/data-structure/15-b-tree/impl/`
