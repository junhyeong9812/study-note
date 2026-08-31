# data-structure/06-binary-search-tree — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 계약 — SortedMap (`src/main/java/com/datastructure/bst/SortedMap.java`)

- `V put(K key, V value)`
- `V get(K key)`
- `boolean containsKey(K key)`
- `V remove(K key)`
- `int size()`
- `boolean isEmpty()`
- `void clear()`
- `K firstKey()`
- `K lastKey()`
- `K floorKey(K key)`
- `K ceilingKey(K key)`
- `Iterable<K> keys()`
- `Iterable<K> keysInRange(K from, K to)`
- 타입 파라미터: `SortedMap<K extends Comparable<K>, V>`

## 구현 — BinarySearchTree (`src/main/java/com/datastructure/bst/BinarySearchTree.java`)

<!-- 메서드마다 내 언어로. 복잡도는 "왜 그런지"까지. -->

### 구조

```
BinarySearchTree — 노드마다 "왼쪽 전부가 나보다 작고, 오른쪽 전부가 나보다 크다"만 지킨다
+---------------------------+
| root ---+                 |
| size = 7|                 |
+---------|-----------------+
          v
                          +--------+
                          | key 50 |
                          | value  |
                          +--------+
                     left /        \ right
                    +--------+    +--------+
                    | key 30 |    | key 70 |
                    +--------+    +--------+
                    /       \      /       \
              +------+  +------+ +------+ +------+
              |  20  |  |  40  | |  60  | |  80  |
              +------+  +------+ +------+ +------+

    불변식 (모든 노드에서 성립)
        왼쪽 서브트리의 모든 키  <  자기 키  <  오른쪽 서브트리의 모든 키
        "왼쪽 자식 하나가 작다"가 아니라 "왼쪽 전체가 작다"이다.
        50 의 왼쪽에는 20, 30, 40 이 전부 들어 있고 그 중 하나도 50 을 넘지 않는다

    Node 에 parent 필드가 없다 -> 위로 올라갈 길이 없다.
    그래서 모든 연산이 root 에서 아래로만 내려가고, 링크를 고쳐야 하면 parent 를 손에 들고 간다

    이 불변식이 주는 것
        비교 한 번에 남은 후보의 절반을 버린다 -> 균형 잡히면 O(log n)
        중위 순회(왼쪽 -> 자기 -> 오른쪽)가 그대로 정렬 순서다   20 30 40 50 60 70 80
    해시맵에는 없는 성질이 바로 이 두 번째다 — 순서, 범위, 이웃 키를 물을 수 있다
```

### 동작 — 탐색

```
findNode(key) : 루트에서 비교 결과대로 한쪽으로만 내려간다. 되돌아오지 않는다
    get(40)
                    [50]        40 < 50 -> 왼쪽
                    /
                 [30]           40 > 30 -> 오른쪽
                     \
                     [40]       같다 -> 찾음
    비용 = 뿌리에서 그 노드까지의 깊이

    firstKey() : 왼쪽 끝까지 내려간다 = 20      lastKey() : 오른쪽 끝까지 = 80
    height()   : 빈 트리 0, 노드 하나 1 (-1 규약이 아니다)

floorKey(45) : "45 이하 중 가장 큰 키". 후보(best)를 기억하면서 내려간다
                    [50]     45 < 50  -> 왼쪽. 50 은 45 보다 크니 답이 될 수 없다 (best 갱신 없음)
                    /
                 [30]        45 > 30  -> best = 30 으로 두고 오른쪽 (더 큰 후보가 있을 수 있다)
                     \
                     [40]    45 > 40  -> best = 40 으로 갱신하고 오른쪽
                         \
                         null         길이 끝났다 -> 답은 마지막 best = 40
    ceilingKey 는 완전 대칭 — 오른쪽으로 갈 때는 후보를 남기지 않고, 왼쪽으로 갈 때 남긴다

keysInRange(from, to) : 가지치기가 붙은 중위 순회. 양 끝 모두 포함
    node.key > from        이면 왼쪽 재귀    (아니면 왼쪽 전체가 from 미만 -> 통째로 버린다)
    from <= node.key <= to 이면 수집
    node.key < to          이면 오른쪽 재귀  (아니면 오른쪽 전체가 to 초과 -> 통째로 버린다)

    keysInRange(35, 65) 에서 잘려 나가는 가지
                        [50]
                       /    \
                    [30]    [70]        70 > 65 -> 70 의 오른쪽(80)은 보지도 않는다
                   /    \    /
                [20]  [40] [60]
                  ^ 20 < 35 -> 20 의 왼쪽 서브트리 전체를 버린다
    -> O(log n + 결과 개수). 전체를 훑어 거르는 것과 다르다
```

### 동작 — 추가

```
put(key, value) : 내려갈 자리가 없을 때까지 내려가서, 새 노드는 언제나 잎(leaf)으로 붙인다
    put(45)
                [50]        45 < 50 -> parent = 50, 왼쪽으로
                /
             [30]           45 > 30 -> parent = 30, 오른쪽으로
                 \
                 [40]       45 > 40 -> parent = 40, 오른쪽으로
                     \
                     null   빈 자리다 -> parent.right = new Node(45)

    after        [50]
                 /
              [30]
                  \
                  [40]
                      \
                      [45]      <- 새 노드. 기존 노드는 하나도 움직이지 않았다

    같은 키를 만나면 value 만 교체하고 옛 값을 돌려준다 (size 불변, 구조 불변)
    회전도 재균형도 없다 -> 넣는 순서가 트리 모양을 그대로 결정한다

편향(최악) — 이미 정렬된 순서로 넣으면
    put(10), put(20), put(30), put(40)
        [10]
            \
            [20]            내려갈 때마다 항상 오른쪽. 버려지는 후보가 없다
                \
                [30]        높이 = n. 사실상 연결 리스트다 -> 모든 연산이 O(n)
                    \
                    [40]
    "평균 O(log n)"은 입력이 뒤섞여 있을 때의 이야기다.
    이 편향을 회전으로 막는 것이 16 장 레드-블랙 트리다
```

### 동작 — 삭제

```
remove(key) : 자식 수에 따라 세 갈래다. parent 를 손에 들고 내려가야 링크를 고칠 수 있다

[1] 자식 0개 (잎) : 부모가 가리키던 자리를 null 로 바꾼다
    remove(20)
            [30]                    [30]
           /    \        ->            \
        [20]    [40]                   [40]

[2] 자식 1개 : 그 자식을 부모에 직접 이어 붙인다 (한 칸 끌어올리기)
    remove(20)
            [30]                    [30]
            /                       /
         [20]           ->       [25]
             \
             [25]
    child = (cur.left != null) ? cur.left : cur.right;
    parent == null ? root = child : (부모가 cur 을 가리키던 쪽) = child;
    자식이 하나면 그 자식을 통째로 올려도 불변식이 깨지지 않는다 — 부등호 방향이 그대로다

[3] 자식 2개 : 자리를 비울 수가 없다. 대신 "그 자리에 앉아도 되는 키"를 데려온다
    remove(30)
                [30]                후속자(successor) 찾는 길
               /    \               = 오른쪽 서브트리의 최소
            [20]    [40]              cur.right = 40 에서 왼쪽 끝까지
                    /   \                 [40]
                 [35]   [50]              /
                                       [35]   <- 왼쪽 자식이 없다. successor = 35

    (1) cur.key = successor.key;  cur.value = successor.value;   <- 값만 복사한다
                [35]                    노드 객체는 그대로 살아 있고 안의 내용만 바뀐다
               /    \
            [20]    [40]
                    /   \
                 [35]   [50]        <- 아직 남아 있는 중복. 이걸 지워야 끝난다

    (2) 삭제 대상을 successor 노드로 바꿔치고 [1] / [2] 로 처리한다
        후속자는 정의상 왼쪽 자식이 없다 -> 자식이 0개나 1개다 -> [3] 이 되풀이되지 않는다

    after       [35]
               /    \
            [20]    [40]
                        \
                        [50]

    왜 하필 "오른쪽 서브트리의 최소"인가
        그 키만이 왼쪽 전부보다 크면서 오른쪽 나머지 전부보다 작다.
        즉 불변식을 깨지 않고 그 자리에 앉을 수 있는 후보다 (대칭으로 왼쪽 서브트리의 최대도 가능)
```

### `필드`

- `static class Node<K, V> { K key; V value; Node<K, V> left; Node<K, V> right; }` — 역할:
- `Node<K, V> root` — 역할:
- `int size` — 역할:

### `int size()`

- 하는 일:
- 논리:
- 비용(왜):

### `boolean isEmpty()`

- 하는 일:
- 논리:
- 비용(왜):

### `boolean containsKey(K key)`

- 하는 일:
- 논리:
- 비용(왜):

### `V get(K key)`

- 하는 일:
- 논리:
- 비용(왜):

### `void clear()`

- 하는 일:
- 논리:
- 비용(왜):

### `int height()`

- 하는 일:
- 논리:
- 비용(왜):

### `String toString()`

- 하는 일:
- 논리:
- 비용(왜):

### `Node<K, V> findNode(K key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `V put(K key, V value)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `V remove(K key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `K firstKey()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `K lastKey()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `K floorKey(K key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `K ceilingKey(K key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `Iterable<K> keys()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `Iterable<K> keysInRange(K from, K to)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

## 문제 — BSTProblems (`src/main/java/com/datastructure/bst/BSTProblems.java`)

### 문제 1. 가장 가까운 키

> 문제 설명: `target` 과 차이가 가장 작은 키를 반환한다. 비었으면 `NoSuchElementException`.
> 양쪽 차이가 같으면 작은 쪽을 반환한다.
> `{1, 5, 9}, target=6` -> `5`
> `{1, 5, 9}, target=7` -> `5` (차이 2 대 2 이므로 작은 쪽)
> `{1, 5, 9}, target=0` -> `1`
> 함정 — 10만 개 × 10만 질의 시간 제한이 있다. 전부 훑어 최소 차이를 찾으면 O(n) 이다.
> 생각할 것 — 전부 훑어서 최소 차이를 찾으면 O(n) 이다. `floorKey` 와 `ceilingKey` 를 쓰면? /
> 둘 중 하나가 없는 경우를 잊지 마라.
> 시그니처: `static Integer closestKey(SortedMap<Integer, ?> map, int target)` — O(log n) 이어야 한다.

- 내 접근:
- 논리:
- 비용(왜):

### 문제 2. 구간 합

> 문제 설명: `from` 이상 `to` 이하인 키들의 값을 더한다. 값은 정수다.
> `{1=10, 5=50, 9=90}, from=1, to=5` -> `60`
> 생각할 것 — `keysInRange` 를 쓰면 볼 필요 없는 가지를 건너뛴다. / 답이 k 개면 전체 비용이 얼마인가?
> 시그니처: `static long rangeSum(SortedMap<Integer, Integer> map, int from, int to)`

- 내 접근:
- 논리:
- 비용(왜):

### 문제 3. k 번째로 작은 키 (1부터 센다)

> 문제 설명: `{1, 5, 9}, k=2` -> `5`
> k 가 범위를 벗어나면 `IndexOutOfBoundsException`.
> 생각할 것 — 정렬 순회를 하다가 k 번째에서 멈추면 된다. 전부 다 순회할 필요가 있는가? /
> (참고: 노드마다 "내 아래에 몇 개 있는지"를 들고 있으면 O(log n) 이 된다.
> 그건 17번 펜윅 트리에서 다시 만난다. 여기서는 순회로 충분하다.)
> 시그니처: `static Integer kthSmallest(SortedMap<Integer, ?> map, int k)`

- 내 접근:
- 논리:
- 비용(왜):

## 핵심 문장

<!-- 지도 수준의 문장들 — 세부가 아니라 "왜 이 구조인가"를 담은 문장 -->

-
-
-

## 관련 자료

<!-- 원본 문서·코드 경로. 기준 소스는 문서가 아니라 코드/원전이다. -->

- 원본 README: `/home/jun/project/myway/data-structure/06-binary-search-tree/README.md`
- 구현: `/home/jun/project/myway/data-structure/06-binary-search-tree/src/main/java/com/datastructure/bst/`
- 테스트: `/home/jun/project/myway/data-structure/06-binary-search-tree/src/test/java/com/datastructure/bst/`
- 참고 구현: `/home/jun/project/myway/data-structure/06-binary-search-tree/impl/`
