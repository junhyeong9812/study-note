# data-structure/12-skip-list — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 계약 — OrderedMap (`src/main/java/com/datastructure/skiplist/OrderedMap.java`)

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
- `List<K> keys()`
- `List<K> keysInRange(K from, K to)`

## 계약 — OrderedSet (`src/main/java/com/datastructure/skiplist/OrderedSet.java`)

- `boolean add(K key)`
- `boolean contains(K key)`
- `boolean remove(K key)`
- `int size()`
- `boolean isEmpty()`
- `void clear()`
- `K first()`
- `K last()`
- `K floor(K key)`
- `K ceiling(K key)`
- `List<K> toList()`
- `List<K> range(K from, K to)`

## 구현 — SkipList (`src/main/java/com/datastructure/skiplist/SkipList.java`)

<!-- 메서드마다 내 언어로. 복잡도는 "왜 그런지"까지. -->

### 구조

```
SkipList — 정렬된 연결 리스트를 여러 층으로 쌓아, 위층에서 멀리 건너뛴다
+---------------------------------------------------------------+
| MAX_LEVEL = 32,  P = 0.5                                      |
| head     더미(sentinel) 노드. key/value 가 없고 forward 는 32칸 |
| level = 4    지금 실제로 쓰는 층 수 (currentLevel())            |
| size = 9                                                      |
| random   randomLevel() 이 쓰는 난수원 (seed 생성자로 재현 가능)  |
+---------------------------------------------------------------+

    Node { final K key;  V value;  final Node<K,V>[] forward; }
        forward 배열의 길이가 곧 그 노드의 층수다 (별도 level 필드가 없다)
        forward[0] 이 최하위 층 — 여기가 모든 노드를 잇는 완전한 정렬 리스트다
        인덱스가 클수록 위층이고, 위층은 아래층의 부분집합이다

lv3   head------->[ 6]------------------------------------------> null
lv2   head------->[ 6]------------------------------>[21]------> null
lv1   head------->[ 6]------->[ 9]------->[17]------>[21]------> null
lv0   head->[ 3]->[ 6]->[ 7]->[ 9]->[12]->[17]->[19]->[21]->[25]-> null

    노드별 층수    3:1   6:4   7:1   9:2   12:1   17:2   19:1   21:3   25:1
    head 만 32칸을 갖고 있고, level(4) 이상의 칸은 전부 null 이다

    lv0 만 보면 그냥 정렬된 단일 연결 리스트다 — 탐색이 O(n).
    위층은 그 리스트 위에 놓인 "급행 노선"이고, 층이 올라갈수록 정차역이 줄어든다.
    BST 는 회전으로 모양을 균형 잡아 O(log n) 을 만든다.
    스킵 리스트는 균형을 잡지 않는다 — 층수를 동전 던지기로 정해 평균적으로 절반씩
    줄어드는 층을 만든다. 회전 코드가 한 줄도 없는 대신 확률에 기댄다
```

### 동작 — 탐색

```
get(19) : 위층에서 크게 건너뛰고, 넘칠 것 같으면 한 층 내려간다
    cur = head 에서 시작해 i = level-1 = 3 부터 0 까지 내려간다.
    각 층에서 "다음 노드의 키가 19 보다 작은 동안" 전진한다 (같거나 크면 내려간다)

    i=3   head 의 다음은 [ 6] — 6 < 19 이므로 전진      cur = [ 6]
          [ 6] 의 lv3 다음은 null                       -> 내려간다     update[3] = [ 6]
    i=2   [ 6] 의 lv2 다음은 [21] — 19 보다 크다        -> 전진 없이 내려간다  update[2] = [ 6]
    i=1   [ 6] -> [ 9] -> [17]     (9 < 19, 17 < 19)
          [17] 의 lv1 다음은 [21] — 크다                -> 내려간다     update[1] = [17]
    i=0   [17] 의 lv0 다음은 [19] — 작지 않다           -> 정지         update[0] = [17]

    답 확인 : update[0].forward[0] = [19] 이고 키가 같다 -> 찾았다

    지나온 자리     head, [ 6], [ 9], [17], [19]      노드 9개 중 5개만 봤다
    lv0 만 있었다면 head, 3, 6, 7, 9, 12, 17, 19 를 전부 지나야 했다

    핵심 두 가지
        (1) 층을 내려갈 때 cur 을 head 로 되돌리지 않는다. 그 자리에서 이어 내려간다 (계단식 하강)
        (2) 각 층에서 "바로 다음 것"만 본다. 되돌아가는 일이 없다 (prev 참조가 필요 없는 이유)
    평균적으로 층마다 두어 칸만 전진하고 층수가 log n 이라 평균 O(log n)

findPredecessors(key) : 하강하면서 각 층의 "key 보다 작은 마지막 노드"를 배열에 적어 둔다
    update[0] = [17]      lv0 에서 19 바로 앞
    update[1] = [17]
    update[2] = [ 6]
    update[3] = [ 6]
    update[4..31] = null      level(4) 위쪽 칸은 채우지 않는다 (배열 길이는 늘 32)

    삽입과 삭제는 이 배열만 있으면 각 층의 링크를 고칠 수 있다.
    이중 연결 리스트가 prev 참조로 하던 일을 여기서는 "내려오면서 기록"으로 해결한다.
    get 은 이 배열이 필요 없어서 32칸을 만들지 않고 따로 하강한다
```

### 동작 — 추가

```
put(20, v) : 동전 던지기로 층수를 정하고, 그 층수만큼만 끼워 넣는다

    (1) update = findPredecessors(20)
            update[0] = [19]   update[1] = [17]   update[2] = [ 6]   update[3] = [ 6]
    (2) update[0].forward[0] 이 같은 키면 -> 값만 교체하고 끝
            size 도 level 도 모양도 전부 그대로다

    (3) lvl = randomLevel()
            int lvl = 1;
            while (lvl < MAX_LEVEL && random.nextDouble() < P) lvl++;

            동전을 던져 앞면(< 0.5)이면 한 층 더. 그래서
                층수 1 : 1/2      2 : 1/4      3 : 1/8      4 : 1/16   ...
            층이 하나 올라갈 확률이 절반이라 위층 노드 수가 평균 절반씩 줄어든다.
            이 확률 분포 하나가 "균형 잡힌 모양"을 회전 없이 만들어 낸다.
            층수는 넣는 키의 값과 무관하다 — 어떤 순서로 넣어도 모양의 분포가 같다
            (BST 가 정렬 입력에 무너지던 것과 대비되는 지점)

    (4) lvl > level 이면 (지금까지 없던 층이 생긴 경우)
            새 층에는 앞 노드가 head 뿐이다 -> update[level .. lvl-1] = head
            level = lvl

    (5) node = new Node(20, v, lvl);   i = 0 .. lvl-1 각 층에서
            node.forward[i] = update[i].forward[i];    <- 새 노드가 먼저 뒤를 잡고
            update[i].forward[i] = node;               <- 그 다음 앞 노드를 갈아끼운다
        순서를 뒤집으면 뒤쪽으로 가는 길을 잃는다 (02 장 중간 삽입과 같은 함정)

    lvl = 2 가 나왔다면 lv0 과 lv1 두 층에만 끼어든다
    before   lv1   ... [17]--------------->[21] ...
             lv0   ... [17]->[19]--------->[21] ...
    after    lv1   ... [17]-------->[20]-->[21] ...
             lv0   ... [17]->[19]-->[20]-->[21] ...
                                     ^ 위층(lv2, lv3)은 손대지 않는다
```

### 동작 — 삭제

```
remove(21)
    (1) update = findPredecessors(21)
            update[0] = [19]   update[1] = [17]   update[2] = [ 6]   update[3] = [ 6]
    (2) target = update[0].forward[0] = [21].  키가 다르거나 null 이면 없는 것 -> null 반환
    (3) i = 0 부터 level-1 까지
            update[i].forward[i] != target 이면 break
                (그 층에 target 이 없다 = 더 위층에도 없다. 위를 볼 필요가 없다)
            아니면 update[i].forward[i] = target.forward[i]     <- 건너뛰게 만든다

            i=0   [19].forward[0] :  [21]  ->  [25]
            i=1   [17].forward[1] :  [21]  ->  null
            i=2   [ 6].forward[2] :  [21]  ->  null
            i=3   [ 6].forward[3] 은 null 이라 target 이 아니다  -> break

    before
    lv2   head------->[ 6]------------------------------>[21]------> null
    lv1   head------->[ 6]------->[ 9]------->[17]------>[21]------> null
    lv0   head->[ 3]->[ 6]->[ 7]->[ 9]->[12]->[17]->[19]->[21]->[25]-> null

    after
    lv2   head------->[ 6]------------------------------------> null
    lv1   head------->[ 6]------->[ 9]------->[17]------------> null
    lv0   head->[ 3]->[ 6]->[ 7]->[ 9]->[12]->[17]->[19]->[25]-> null

    (4) 빈 위층 걷어내기
            while (level > 1 && head.forward[level-1] == null) level--;
        맨 위층에 아무도 없으면 층수를 줄인다. 1 아래로는 내려가지 않는다.
        위 예에서는 lv3 에 [ 6] 이 남아 있어 level 은 4 그대로다.
        [ 6] 을 지웠다면 lv3 가 비어 level 이 3 으로 내려갔을 것이다
        (안 줄이면 빈 층을 훑느라 탐색이 쓸데없이 길어진다)
```

### 동작 — 이웃과 범위

```
floorKey / ceilingKey — get 과 같은 하강인데, 부등호 하나와 "답을 어디서 읽느냐"만 다르다

    get / ceilingKey :  while (다음.key <  key) 전진   -> 멈춘 자리의 "다음"이 key 이상
    floorKey         :  while (다음.key <= key) 전진   -> 멈춘 자리 자체가 key 이하 중 최대

    lv0   ... ->[17]->[19]->[21]->[25]-> ...
    floorKey(20)     19 까지 전진하고 멈춘다  -> 답은 멈춘 자리 [19]   (cur == head 면 null)
    ceilingKey(20)   19 에서 멈춘다           -> 답은 그 다음 [21]     (다음이 null 이면 null)

    BST 는 내려가면서 후보(best)를 따로 기억해야 했다.
    여기서는 lv0 이 완전한 정렬 리스트라 "멈춘 자리"와 "그 다음"이 곧 양쪽 이웃이다 —
    후보 변수가 아예 필요 없다

firstKey()  = head.forward[0]                             O(1)
lastKey()   = 각 층에서 갈 수 있는 데까지 오른쪽으로 간다   O(log n)   <- first 와 비대칭이다
              (뒤 방향 포인터가 없어서 끝을 바로 알 수 없다)
keys()      = head.forward[0] 부터 lv0 을 따라 끝까지 걷는다 -> 정렬 순서 그대로

keysInRange(from, to)
    lv3/lv2/lv1 로 from 자리까지 빠르게 하강한 다음, lv0 을 따라 to 이하인 동안 담는다
        head =====> ... =====> [from 직전]        위층으로 찾아가기      O(log n)
                                   |
        lv0                        +--> [ ] -> [ ] -> [ ] -> ... (to 를 넘으면 정지)   결과 개수
    -> O(log n + 결과 개수). 해시맵으로는 할 수 없는 질문이고, BST 의 범위 순회와 같은 성질이다
```

### `필드`

- `static final int MAX_LEVEL = 32` — 역할:
- `static final double P = 0.5` — 역할:
- `static final class Node<K, V> { final K key; V value; final Node<K, V>[] forward; }` — 역할:
- `final Node<K, V> head` — 역할:
- `private final Random random` — 역할:
- `int level` — 역할:
- `private int size` — 역할:

### `SkipList()`

- 하는 일:
- 논리:
- 비용(왜):

### `SkipList(long seed)`

- 하는 일:
- 논리:
- 비용(왜):

### `int randomLevel()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `Node<K, V>[] findPredecessors(K key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `V get(K key)` (TODO)

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

### `K floorKey(K key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `K ceilingKey(K key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `List<K> keys()`

- 하는 일:
- 논리:
- 비용(왜):

### `List<K> keysInRange(K from, K to)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `K firstKey()`

- 하는 일:
- 논리:
- 비용(왜):

### `K lastKey()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `boolean containsKey(K key)`

- 하는 일:
- 논리:
- 비용(왜):

### `int size()`

- 하는 일:
- 논리:
- 비용(왜):

### `boolean isEmpty()`

- 하는 일:
- 논리:
- 비용(왜):

### `int currentLevel()`

- 하는 일:
- 논리:
- 비용(왜):

### `void clear()`

- 하는 일:
- 논리:
- 비용(왜):

## 구현 — SkipListMap (`src/main/java/com/datastructure/skiplist/SkipListMap.java`)

### 구조 — 감싸기만 한다

```
SkipListMap — SkipList 하나를 감싸는 순수 위임이다. 자기 자료구조가 없다
    +--------------------------------+
    | list ----> SkipList<K, V>      |
    +--------------------------------+
    put / get / remove / firstKey / lastKey / floorKey / ceilingKey / keys / keysInRange ...
    전부 그대로 넘긴다

    유일하게 더하는 규칙 : put 의 value 가 null 이면 거부한다
        get 이 "없음"을 null 로 답하기 때문이다.
        null 값을 허용하면 "없다"와 "null 이 들어 있다"를 구분할 수 없고,
        containsKey 가 get(k) != null 로 구현되어 있어 곧장 틀린 답이 된다

    SkipList 는 OrderedMap 계약을 몰라도 되고, 계약을 맞추는 일은 이 클래스가 맡는다.
    seed 생성자를 그대로 뚫어 두어 테스트가 층수를 재현할 수 있게 한다
```

### `필드`

- `private final SkipList<K, V> list` — 역할:

### `SkipListMap()`

- 하는 일:
- 논리:
- 비용(왜):

### `SkipListMap(long seed)`

- 하는 일:
- 논리:
- 비용(왜):

### `V put(K key, V value)`

- 하는 일:
- 논리:
- 비용(왜):

### `V get(K key)`

- 하는 일:
- 논리:
- 비용(왜):

### `boolean containsKey(K key)`

- 하는 일:
- 논리:
- 비용(왜):

### `V remove(K key)`

- 하는 일:
- 논리:
- 비용(왜):

### `int size()`

- 하는 일:
- 논리:
- 비용(왜):

### `boolean isEmpty()`

- 하는 일:
- 논리:
- 비용(왜):

### `void clear()`

- 하는 일:
- 논리:
- 비용(왜):

### `K firstKey()`

- 하는 일:
- 논리:
- 비용(왜):

### `K lastKey()`

- 하는 일:
- 논리:
- 비용(왜):

### `K floorKey(K key)`

- 하는 일:
- 논리:
- 비용(왜):

### `K ceilingKey(K key)`

- 하는 일:
- 논리:
- 비용(왜):

### `List<K> keys()`

- 하는 일:
- 논리:
- 비용(왜):

### `List<K> keysInRange(K from, K to)`

- 하는 일:
- 논리:
- 비용(왜):

## 구현 — SkipListSet (`src/main/java/com/datastructure/skiplist/SkipListSet.java`)

### 구조 — 값 자리에 자리표시자 하나

```
SkipListSet — 상속이 아니라 포함이다. SkipListMap 의 값 자리에 자리표시자를 넣는다
    private static final Object PRESENT = new Object();
    +-----------------------------------+
    | map ----> SkipListMap<K, Object>  |
    +-----------------------------------+

    키    [ 3]      [ 6]      [ 7]      [ 9]      [12]  ...
           |         |         |         |         |
           +---------+---------+---------+---------+---> PRESENT (객체는 딱 하나뿐)

    값이 무엇인지는 아무 의미가 없다. 필요한 것은 "그 키가 있다"뿐이라서
    모든 항목이 같은 객체 하나를 가리킨다 (원소마다 객체를 만들지 않는다)

    add(k)     = map.put(k, PRESENT) == null      <- 옛 값이 없었으면 새로 넣은 것 -> true
    remove(k)  = map.remove(k) != null            <- 옛 값이 있었으면 지운 것      -> true
        둘 다 조회를 따로 하지 않고 반환값만으로 판정한다 (같은 길을 두 번 훑지 않는다)

    이름만 바꿔 넘긴다
        first / last / floor / ceiling / toList / range
          ->  firstKey / lastKey / floorKey / ceilingKey / keys / keysInRange
```

### `필드`

- `private static final Object PRESENT` — 역할:
- `private final SkipListMap<K, Object> map` — 역할:

### `SkipListSet()`

- 하는 일:
- 논리:
- 비용(왜):

### `SkipListSet(long seed)`

- 하는 일:
- 논리:
- 비용(왜):

### `boolean add(K key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `boolean contains(K key)`

- 하는 일:
- 논리:
- 비용(왜):

### `boolean remove(K key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `int size()`

- 하는 일:
- 논리:
- 비용(왜):

### `boolean isEmpty()`

- 하는 일:
- 논리:
- 비용(왜):

### `void clear()`

- 하는 일:
- 논리:
- 비용(왜):

### `K first()`

- 하는 일:
- 논리:
- 비용(왜):

### `K last()`

- 하는 일:
- 논리:
- 비용(왜):

### `K floor(K key)`

- 하는 일:
- 논리:
- 비용(왜):

### `K ceiling(K key)`

- 하는 일:
- 논리:
- 비용(왜):

### `List<K> toList()`

- 하는 일:
- 논리:
- 비용(왜):

### `List<K> range(K from, K to)`

- 하는 일:
- 논리:
- 비용(왜):

## 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| SkipList | | | |
| SkipListMap | | | |
| SkipListSet | | | |

## 핵심 문장

<!-- 지도 수준의 문장들 — 세부가 아니라 "왜 이 구조인가"를 담은 문장 -->

-
-
-

## 관련 자료

<!-- 원본 문서·코드 경로. 기준 소스는 문서가 아니라 코드/원전이다. -->

- 원본 README: `/home/jun/project/myway/data-structure/12-skip-list/README.md`
- 구현: `/home/jun/project/myway/data-structure/12-skip-list/src/main/java/com/datastructure/skiplist/`
- 테스트: `/home/jun/project/myway/data-structure/12-skip-list/src/test/java/com/datastructure/skiplist/`
- 참고 구현: `/home/jun/project/myway/data-structure/12-skip-list/impl/`
