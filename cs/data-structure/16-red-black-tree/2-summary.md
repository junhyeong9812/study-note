# data-structure/16-red-black-tree — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 계약 — SortedTree (`src/main/java/com/datastructure/redblack/SortedTree.java`)

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
- `K floorKey(K key)`
- `K ceilingKey(K key)`
- `int height()`

## 구현 — RedBlackTree (`src/main/java/com/datastructure/redblack/RedBlackTree.java`)

<!-- 메서드마다 내 언어로. 복잡도는 "왜 그런지"까지. -->

### 구조

```
이 구현은 좌편향 레드-블랙 트리(LLRB)다. CLRS 방식(NIL sentinel + 부모 포인터 + 삼촌 케이스)이 아니다
  - 부모 포인터 없음. NIL sentinel 없음 -- null 이 곧 블랙 (isRed(null) == false)
  - RED = true, BLACK = false. color 는 노드 필드지만 뜻은 "이 노드로 들어오는 부모 링크의 색"
  - 그래서 재귀는 늘 "고친 부분트리의 새 뿌리를 반환"해서 부모 슬롯에 재대입한다

표기 :  (7B) = 검은 링크로 매달린 노드,  (3R) = 붉은 링크로 매달린 노드
        /  \  검은 링크        //  \\  붉은 링크

A B C D E F G 를 순서대로 put 한 결과
                          (DB)
                        /      \
                    (BB)        (FB)
                    /  \        /  \
                (AB)  (CB)  (EB)  (GB)

G F E 순서로 넣던 중간 모습 -- 붉은 링크가 살아 있는 예
                          (FB)
                         //   \
                     (ER)      (GB)

실코드가 지키는 불변식 (put / remove 가 끝날 때마다 성립)
  [1] root 는 항상 블랙                    put() 끝에서 root.color = BLACK
  [2] null 은 블랙                          isRed(null) == false
  [3] 붉은 링크는 왼쪽으로만 (좌편향)      balance 케이스 [1] 이 오른쪽 레드를 눕힌다
  [4] 붉은 링크가 연달아 두 개일 수 없다   balance 케이스 [2]
  [5] 뿌리에서 어느 잎까지 가도 검은 링크 수가 같다 (완전 흑색 균형)   blackHeight()
  [3]+[4]+[5] -> 가장 긴 경로가 가장 짧은 경로의 2 배를 넘지 못한다 -> 높이 O(log n)
  ([3] 이 붉은 링크의 배치를 한 가지로 못박아서, 고쳐야 할 경우의 수가 아래 세 개로 줄어든다)

2-3 트리로 읽으면 :  붉은 링크로 묶인 두 노드를 한 덩어리로 보면 그대로 2-3 트리다
      (BB)                     -> 2-노드  [ B ]
      (FB) 와 그 왼쪽 (ER)     -> 3-노드  [ E F ]
  그래서 flipColors 는 15 장 B-트리의 split(가운데 키를 부모로 올리기)과 같은 일이다
```

### 동작 — 회전

```
rotateLeft(h) : 오른쪽으로 기운 붉은 링크를 왼쪽으로 눕힌다. 이 챕터에서 가장 중요한 조작이다

  before                       코드                          after
       (h:c)               Node x = h.right;                     (x:c)
       /   \\              h.right = x.left;                    //    \
    (A)     (x:R)          x.left  = h;                      (h:R)     (C)
            /   \          x.color = h.color;                /    \
         (B)     (C)       h.color = RED;                 (A)      (B)
                           return x;
  c = h 가 갖고 있던 색 (블랙일 수도 레드일 수도 있다)

  포인터가 옮겨지는 순서
    시작    h.left = A    h.right = x     x.left = B    x.right = C
    [1] x = h.right        오른쪽 자식을 붙잡아 둔다 (여기서 안 잡으면 [2] 에서 잃어버린다)
    [2] h.right = x.left   h 의 오른쪽 자리를 B 가 대신 채운다      h --> B
    [3] x.left  = h        x 가 h 를 왼쪽 자식으로 삼는다          x --> h
    [4] x.color = h.color  h 가 쓰던 "부모 링크 색"을 x 가 물려받는다 (위쪽에서 본 색은 그대로)
    [5] h.color = RED      h 로 들어가는 링크는 이제 붉은 왼쪽 링크가 된다
    끝      x.left = h     x.right = C     h.left = A    h.right = B
    A 와 C 는 손대지 않는다. 실제로 옮겨지는 것은 B 하나 + h 와 x 의 상하 관계뿐

  부모 링크는 어떻게 이어지나 -- 부모 포인터가 없으므로 "반환값 재대입"으로 잇는다
        h.left = put(h.left, key, value, old);   ...   return balance(h);
        h = rotateLeft(h);
    -> 재귀가 돌아 나오는 자리에서 부모의 left / right 슬롯이 새 뿌리 x 로 덮어써진다
       (부모가 root 면 put() 의 root = put(root, ...) 이 그 자리다)

  왜 순서가 안 깨지나 : A < h < B < x < C 라는 관계가 before / after 양쪽에서 그대로다
  왜 검은 높이가 안 변하나 : [4][5] 가 색을 맞바꿔서, 붉은 링크 하나를 오른쪽에서 왼쪽으로
       옮겼을 뿐 검은 링크의 개수는 어느 경로에서도 그대로이기 때문

rotateRight(h) 는 left / right 를 통째로 뒤집은 거울상이다
        x = h.left;  h.left = x.right;  x.right = h;  x.color = h.color;  h.color = RED;
비용 : 포인터 3 개 + 색 2 개 -> O(1)
```

### 동작 — 추가

```
put 은 평범한 BST 처럼 내려가 새 노드를 "붉게" 붙이고, 재귀가 돌아 나오며 노드마다 balance(h) 를 부른다
  새 노드를 붉게 붙이는 이유 : 검게 붙이면 그 경로만 검은 링크가 1 개 늘어 [5] 가 즉시 깨진다.
  붉게 붙이면 [5] 는 그대로고 [3][4] 만 깨진다 -- balance 는 그 둘만 고치면 된다

balance(h) 는 세 줄이 전부다. 순서도 그대로이고, 세 개가 연달아 실행될 수 있다

[1] 오른쪽만 붉다 -> rotateLeft(h)            ([3] 좌편향 위반 수리)
    isRed(h.right) && !isRed(h.left)
        (AB)                        (BB)
            \\           ->         //
             (BR)                (AR)
    (AB) 에 put("B") 한 직후. 새 노드가 오른쪽에 붙었으니 눕혀서 왼쪽으로 보낸다

[2] 왼쪽이 붉고 그 왼쪽도 붉다 -> rotateRight(h)      ([4] 연속 레드 위반 수리)
    isRed(h.left) && isRed(h.left.left)
          (GB)                      (FB)
          //                       //    \\
        (FR)          ->        (ER)      (GR)
        //
      (ER)
    한 줄로 서 있던 붉은 링크 두 개를, 가운데 F 를 축으로 세워 양옆에 하나씩 나눠 단다

[3] 양쪽이 다 붉다 -> flipColors(h)           (2-3 트리에서 4-노드를 쪼개는 자리)
    isRed(h.left) && isRed(h.right)
          (FB)                      (FR)   <- F 로 들어가는 링크가 붉어진다
         //   \\         ->         /   \      = 가운데 키가 부모로 올라간 것과 같은 뜻
      (ER)     (GR)              (EB)    (GB)
    h.color = !h.color;  h.left.color = !h.left.color;  h.right.color = !h.right.color;
    아래 두 링크가 같이 검어지고 위 링크 하나가 붉어지므로 모든 경로의 검은 링크 수가 함께 +1

한 번의 put 에서 [2] 와 [3] 이 연달아 걸리는 실제 예 -- (GB) 에 F, 그다음 E 를 넣는 경우
   put("E") 직후            balance(G) 의 [2]            이어서 [3]            put() 끝
      (GB)                      (FB)                      (FR)                  (FB)
      //                       //    \\          ->        /   \        ->       /   \
    (FR)          ->        (ER)      (GR)              (EB)   (GB)          (EB)   (GB)
    //                    rotateRight(G)              flipColors(F)      root.color = BLACK
  (ER)  <- 새 노드

[3] 이 h 를 붉게 만들면 그 위 부모에서 다시 [1][2][3] 이 걸릴 수 있다 -- 재귀가 돌아 나오는
길을 따라 위로 번져 올라간다. 뿌리까지 올라오면 put() 이 root.color = BLACK 으로 덮어 쓴다.
이때만 검은 높이가 1 늘어난다 = 트리가 위로 자라는 유일한 지점 (15 장 B-트리의 root split 과 같다)

비용 : 내려가기 O(log n) + 돌아 나오며 노드마다 O(1) 수리 -> O(log n)
```

### 동작 — 삭제

```
LLRB 의 삭제에는 double-black 이 없다. 대신 "내려가는 길에서 현재 노드를 계속 붉게 유지"한다.
붉은 노드는 잎에서 그냥 떼어내도 검은 링크 수가 안 변하기 때문이다 -- 사후 수리 대신 사전 준비다

remove(key)
  1) if (!isRed(root.left) && !isRed(root.right)) root.color = RED;   여분의 붉은색을 뿌리에 심는다
  2) root = delete(root, key)                                          아래로 내려가며 지운다
  3) if (root != null) root.color = BLACK                              [1] 복구

왼쪽으로 내려가기 직전의 검사
     if (!isRed(h.left) && !isRed(h.left.left)) h = moveRedLeft(h);
     뜻 : "왼쪽 자식이 2-노드라 빌려줄 여유가 없다 -> 내려가기 전에 붉은색을 만들어 주고 간다"

moveRedLeft(h) -- 15 장 B-트리의 merge / borrow 와 정확히 같은 두 갈래다

  공통 첫 줄 : flipColors(h)      h 가 쥐고 있던 붉은색을 두 자식에게 나눠 준다
        (hR)                        (hB)
        /   \           ->          //   \\
     (LB)   (RB)                 (LR)     (RR)

  [1] 오른쪽 형제도 빠듯하다 (isRed(h.right.left) == false) -> 여기서 끝 = merge
      셋이 한 덩어리가 된 셈이고, 왼쪽이 붉어졌으니 그대로 내려가서 지우면 된다
      실제 예 : A B C 세 개짜리 트리에서 최솟값 A 를 지울 때
          (BR)                       (BB)                      (CB)
          /   \        flip ->       //   \\      A 제거 ->     //
       (AB)   (CB)                (AR)     (CR)   + balance   (BR)
                                    ^ 붉으므로 떼어내도 검은 높이가 안 변한다

  [2] 오른쪽 형제가 빌려줄 게 있다 (h.right.left 가 붉다) -> 한 칸 끌어온다 = borrow
      h.right = rotateRight(h.right);   h = rotateLeft(h);   flipColors(h);
      실제 예 : 1..6 이 든 트리에서 deleteMin, h = 2 인 지점

      flipColors 직후        rotateRight(h.right)      rotateLeft(h)         flipColors(h)
          (2B)                    (2B)                    (3B)                  (3R)
         //   \\                 //   \\                 //   \\                /   \
      (1R)     (4R)           (1R)     (3R)           (2R)     (4R)         (2B)     (4B)
               //                          \\         //                    //
            (3R)                           (4R)    (1R)                  (1R)
                                                    형제 쪽 키 3 이 h 자리로 올라오고
                                                    1 은 붉은 채로 남아 안전하게 지워진다

  moveRedRight(h) 는 거울상이다 : flipColors 뒤 isRed(h.left.left) 면 rotateRight(h); flipColors(h);

지울 키가 내부 노드에 있으면 -- 잎 쪽 문제로 바꿔치기한다
     Node x = min(h.right);  h.key = x.key;  h.value = x.value;  h.right = deleteMin(h.right);
  후행자(오른쪽 부분트리의 최소 키)를 h 에 복사하고, 실제로 떼어내는 노드는 늘 잎 쪽이다
  (15 장 B-트리에서 선행자/후행자로 바꿔치기하던 것과 같은 수법)

돌아 나오면서 노드마다 balance(h) -- 내려가며 일부러 만들어 둔 붉은색을 [1][2][3] 으로 되정리한다
비용 : O(log n)
```

### `필드`

- `static final boolean RED / BLACK` 역할:
- `Node<K,V> root` 역할:
- `int size` 역할:
- `Node.key` / `Node.value` / `Node.left` / `Node.right` / `Node.color` 역할:
- 불변식 4개(뿌리는 검다 · 빨간 링크는 왼쪽에만 · 빨강 연속 금지 · 검은 높이가 같다):

### `static boolean isRed(Node<K,V> node)`

- 하는 일:
- 논리(null 을 검정으로 보는 이유):

### `private Node<K,V> rotateLeft(Node<K,V> h)` (TODO)

- 하는 일:
- 논리(링크만이 아니라 색도 옮기는 이유):
- 비용(왜):

### `private Node<K,V> rotateRight(Node<K,V> h)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `private void flipColors(Node<K,V> h)` (TODO)

- 하는 일:
- 논리(대입이 아니라 반전이어야 하는 이유 · 넣기/지우기에서 방향이 반대인 것):
- 비용(왜):

### `private Node<K,V> balance(Node<K,V> h)` (TODO)

- 하는 일:
- 논리(세 검사의 순서가 계약인 이유 · `else if` 가 아닌 이유):
- 비용(왜):

### `private Node<K,V> put(Node<K,V> h, K key, V value, Object[] old)` (TODO)

- 하는 일:
- 논리(새 노드를 빨강으로 넣는 이유 · 반환값을 부모에 다시 대입하는 방식):
- 비용(왜):

### `private Node<K,V> moveRedLeft(Node<K,V> h)` (TODO)

- 하는 일:
- 논리(내려가기 전에 미리 빨강을 확보 — 15번 B-트리의 "미리 채우기"와의 대응):
- 비용(왜):

### `private Node<K,V> deleteMin(Node<K,V> h)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `private Node<K,V> delete(Node<K,V> h, K key)` (TODO)

- 하는 일:
- 논리(key 비교를 두 번 하는 이유):
- 비용(왜):

### `public K floorKey(K key)` (TODO)

- 하는 일:
- 논리("찾으면 바로 반환"이 안 되는 이유):
- 비용(왜):

### `public V put(K key, V value)`

- 하는 일:
- 논리(마지막에 뿌리를 검게 강제하는 이유):
- 비용(왜):

### `public V get(K key)`

- 하는 일:
- 비용(왜):

### `public V remove(K key)`

- 하는 일:
- 논리(시작 전 뿌리를 빨갛게 만드는 줄의 뜻 — 지워도 테스트가 통과한다는 기록):
- 비용(왜):

### `public K ceilingKey(K key)`

- 하는 일:
- 비용(왜):

### `public List<K> keys()`

- 하는 일:
- 비용(왜):

### `public K firstKey()` / `public K lastKey()`

- 하는 일:
- 비용(왜):

### `public int height()`

- 하는 일:
- 비용(왜):

### `public int blackHeight()`

- 하는 일:
- 논리(왼쪽 한 줄만 세도 되는 이유):
- 비용(왜):

### `public boolean containsKey(K key)` / `public int size()` / `public boolean isEmpty()` / `public void clear()`

- 하는 일:
- 비용(왜):

## 구현 — RedBlackTreeMap (`src/main/java/com/datastructure/redblack/RedBlackTreeMap.java`)

TODO 없는 어댑터. 일은 전부 `RedBlackTree` 에 있고 여기는 `SortedTree` 계약으로 넘기기만 한다.

### `필드`

- `RedBlackTree<K,V> tree` 역할:

### `SortedTree 의 메서드 전부를 위임`

- 하는 일:
- 논리(같은 계약으로 여러 트리를 나란히 재기 위한 껍데기라는 것):

## 구현 — RedBlackTreeSet (`src/main/java/com/datastructure/redblack/RedBlackTreeSet.java`)

### `필드`

- `static final Object PRESENT` 역할:
- `RedBlackTreeMap<K, Object> map` 역할:

### `public boolean add(K key)` (TODO)

- 하는 일:
- 논리(별도 조회 없이 "새로 들어갔는지"를 아는 방법):
- 비용(왜):

### `public boolean remove(K key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `public boolean contains(K key)`

- 하는 일:
- 비용(왜):

### `public List<K> toList()` / `public K first()` / `public K last()` / `public K floor(K key)` / `public K ceiling(K key)`

- 하는 일:
- 비용(왜):

### `public int size()` / `public boolean isEmpty()` / `public void clear()`

- 하는 일:
- 비용(왜):

## 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| 12번 스킵 리스트 (확률) | | | |
| 15번 B-트리 (뚱뚱한 노드, 위로 자라기) | | | |
| 16번 좌편향 레드블랙 트리 (회전, 보장) | | | |
| 고전적 레드블랙 트리 (좌우 모두 허용 = 2-3-4) | | | |

## 핵심 문장

<!-- 지도 수준의 문장들 — 세부가 아니라 "왜 이 구조인가"를 담은 문장 -->

-
-
-

## 관련 자료

<!-- 원본 문서·코드 경로. 기준 소스는 문서가 아니라 코드/원전이다. -->

- README: `/home/jun/project/myway/data-structure/16-red-black-tree/README.md`
- 구현: `/home/jun/project/myway/data-structure/16-red-black-tree/src/main/java/com/datastructure/redblack/`
- 테스트: `/home/jun/project/myway/data-structure/16-red-black-tree/src/test/java/com/datastructure/redblack/`
- 정답 구현: `/home/jun/project/myway/data-structure/16-red-black-tree/impl/`
