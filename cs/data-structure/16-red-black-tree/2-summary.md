# data-structure/16-red-black-tree — 정리 (힌트)

## 해결하는 문제

이진 탐색 트리는 넣는 순서가 나쁘면(정렬된 입력) 한쪽으로만 길게 자라 O(n)이 된다.\
12번은 동전(확률)으로, 15번은 뚱뚱한 노드(디스크)로 이것을 막았다. 그런데 **메모리 안에서, 최악까지 보장**으로 막는 답은 아직 없었다.

```text
정렬 입력을 BST에 넣으면              레드블랙 트리는 넣을 때마다 손질한다
 (A)                                       (B)
   \                                      /   \
    (B)         높이 n                 (A)     (C)     높이 <= 2 log2(n+1)
      \         찾기 O(n)                               찾기 O(log n) 보장
       (C)                      회전 + 색 뒤집기 = 포인터·색 몇 개만 바꾸는 O(1) 손질
```

레드블랙 트리는 링크에 빨강·검정을 칠하고 규칙 넷을 지키게 한다 — 규칙이 깨지면 그 자리에서 회전과 색 뒤집기로 바로 고친다.\
쉬운 예: 양팔 저울을 맞추는 사서 — 책을 꽂을 때마다 기울었는지 보고, 기울었으면 몇 권을 반대쪽으로 돌려 꽂는다.\
똑같은 구조다: 이 노트의 `RedBlackTree.put`은 내려갔다 올라오며 노드마다 `balance`를 부른다.\
실무 예: Java `TreeMap`·`TreeSet`, C++ `std::map` — "정렬된 맵"이 필요할 때 기본으로 고르는 구조이고, 메모리 안에서 O(log n)이 최악까지 보장된다.

  - *보장(guarantee)*: "평균적으로"가 아니라 어떤 입력·순서에서도 상한을 넘지 않는다는 뜻. 12번의 "기대값 O(log n)"과 갈리는 지점이다.

### 한눈에 — 쉽게 말하면

**비유: 양팔 저울을 계속 맞추는 도서관 사서.** 책이 들어올 때마다 책장이 한쪽으로만 길게 자라면 찾는 데 오래 걸린다. 그래서 사서는 책을 꽂을 때마다 "기울었나?"를 보고, 기울었으면 책 몇 권을 반대쪽으로 돌려 꽂아 균형을 맞춘다.

**레드-블랙 트리가 똑같은 구조다.** 데이터를 넣을 때마다 "규칙이 깨졌나?"를 검사하고, 깨졌으면 가지 몇 개를 반대쪽으로 돌려 다는(회전) 값싼 손질로 즉시 균형을 되찾는다.

- 레드-블랙 트리는 **이진 탐색 트리(BST)가 한쪽으로 길게 자라 느려지는 것을 막는 장치**다.
  - *이진 탐색 트리(BST)*: 왼쪽엔 작은 값, 오른쪽엔 큰 값만 두는 나무 모양 자료구조. 반씩 잘라 가며 찾는다.
- 링크(부모→자식 연결선)에 빨강/검정 색을 칠해 두고, 규칙 세 개를 지킨다: 빨간 링크는 왼쪽에만 · 빨강 연달아 두 개 금지 · 검은 링크 수는 어느 길로 가도 같게.
- 규칙이 깨지면 그 자리에서 **회전(가지 방향 바꾸기)과 색 뒤집기**로 바로 고친다. 둘 다 포인터·색 몇 개만 바꾸는 O(1) 조작이다.
  - *O(1)*: 데이터가 아무리 많아도 걸리는 시간이 일정하다는 뜻.
- 그 결과 트리 높이가 항상 log n 수준으로 눌려 있어서, 넣기·찾기·지우기가 전부 O(log n)으로 **보장**된다.
  - *O(log n)*: 데이터가 2배로 늘어도 일이 딱 한 걸음만 늘어난다는 뜻. 실무에서 Java의 `TreeMap`, 리눅스 커널 스케줄러가 이 구조를 쓴다.

```text
  균형이 깨진 트리 (느리다)          레드-블랙 트리 (항상 낮게 유지)
      (A)
        \                                (D)
         (B)                            /   \
           \              vs         (B)     (F)
            (C)                      / \     / \
              \                    (A) (C) (E) (G)
               (D)
  찾기 = 최대 4번 이동              찾기 = 최대 3번 이동 (n이 커질수록 차이 급증)
```

## 동작·원리

### 전체 흐름

```text
[1] 규칙 넷 (불변식)                          [2] 2-3 트리로 읽기
    1. 뿌리는 검다                                빨간 링크로 묶인 두 노드 = 2-3 트리의 키 2개 노드
    2. 빨간 링크는 왼쪽에만  (좌편향 LLRB)          검은 링크 = 2-3 트리의 진짜 간선
    3. 빨강 연달아 금지                            (B)          [A B]
    4. 뿌리->잎 검은 링크 수 모두 같음              //  \    =    / | \
    4번이 균형의 정체: 긴 길 <= 짧은 길 x 2     (A)   (C)      .  .  .
              |
              v
[3] 넣기 = 빨강으로 끼워 넣고 올라오며 balance     [4] 손질 도구 둘 (모두 O(1))
    새 노드는 빨강 (= 기존 2-3 노드에 키 하나 더)     rotateLeft / rotateRight : 링크 방향 + 색을 같이 옮긴다
    올라오며 세 검사를 연달아:                       flipColors : 나와 두 자식의 색을 반전 (= 2-3 노드 쪼개기)
      오른쪽 빨강        -> rotateLeft
      왼쪽 빨강 연속     -> rotateRight
      양쪽 빨강          -> flipColors (키가 위로 올라간다)
    반환값을 부모 슬롯에 재대입 -> 부모 포인터 불필요
              |
              v
[5] 지우기 = 내려가기 전에 빨강을 미리 확보 (moveRedLeft / moveRedRight)
    검은 노드를 그냥 지우면 4번이 깨진다 -> 15번 B-트리의 "미리 채우기"와 같은 발상
    후행자로 바꿔치기(deleteMin) -> 올라오며 balance -> 뿌리는 검게
```

- [1] 규칙 넷 중 4번(검은 높이 동일)이 균형의 정체다. 가장 긴 길이 가장 짧은 길의 두 배를 못 넘으니 높이가 `2*log2(n+1)` 이하로 보장된다.
- [2] 빨간 링크를 "한 노드 안의 두 번째 키"로 읽으면 그대로 2-3 트리다. 15번 B-트리를 이진 트리로 흉내낸 것이고, 좌편향 규칙이 모양의 가짓수를 줄여 고칠 경우가 셋으로 준다.
- [3] 새 노드는 빨강으로 넣는다 — 기존 2-3 노드에 키를 하나 더 끼우는 것이라 검은 높이가 안 변한다. 올라오며 세 검사를 **순서대로 연달아** 한다.
- [4] 회전은 링크 방향과 색을 같이 옮기고, `flipColors`는 반전이다 — 한 동작이 넣기와 지우기에서 방향이 반대인 채로 쓰인다.
- [5] 지우기는 넣기의 대칭이다. 검은 노드를 지우면 4번이 깨지므로 내려가기 전에 빨강을 미리 만들어 둔다.

### 계약 — SortedTree (`src/main/java/com/datastructure/redblack/SortedTree.java`)

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

### 구현 — RedBlackTree (`src/main/java/com/datastructure/redblack/RedBlackTree.java`)

<!-- 메서드마다 내 언어로. 복잡도는 "왜 그런지"까지. -->

#### 구조

먼저 알아야 할 것 세 줄:

- *LLRB(좌편향 레드-블랙 트리)*: 빨간 링크를 왼쪽에만 허용하는 단순화 버전. 고칠 경우의 수가 3개로 줄어든다.
- *CLRS 방식 / NIL sentinel*: 유명 교과서의 고전 구현 방식 / "자식 없음"을 null 대신 나타내는 가짜 검정 노드. 이 구현은 둘 다 안 쓴다.
- *불변식*: 어떤 조작이 끝나도 항상 참이어야 하는 규칙. 아래 그림의 [1]~[5]가 그것이다.

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

#### 동작 — 회전

**언제 쓰나**: 빨간 링크가 "왼쪽에만"이라는 규칙을 어기고 오른쪽에 생겼을 때, 그 링크를 왼쪽으로 눕힌다.

- *회전(rotate)*: 부모와 자식의 상하 관계를 한 번 비틀어 바꾸는 조작. 값의 크기 순서는 그대로 두고 모양만 바꾼다.

가장 단순한 형태 — 전 상태 → 조작 → 후 상태:

```text
  전: 오른쪽이 붉다        rotateLeft(A)        후: 왼쪽이 붉다
     (A)                                            (B)
       \\          ->    B를 위로 올리고    ->      //
        (B)              A를 그 왼쪽에 단다      (A)
  A < B 라는 순서는 양쪽 다 그대로다
```

아래 그림은 자식(A, B, C)까지 있는 일반형이다. 실제로 옮겨지는 것은 B 하나뿐임을 보라.

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

#### 동작 — 추가

**언제 쓰나**: 새 키를 넣을 때. 흐름은 "내려가서 붉게 붙이고 → 돌아 나오면서 노드마다 고친다" 두 박자다.

- *재귀*: 함수가 자기 자신을 다시 부르는 방식. 여기선 내려간 길을 그대로 되짚어 "돌아 나오는" 흐름을 만든다.

한 줄 요약 그림 — 전 상태 → 조작 → 후 상태:

```text
  전: 잎에 새 노드를 "붉게" 붙인 직후     balance 수리        후: 규칙이 다시 성립
     (B)                                                        (B)
     / \\           ->   [1]눕히기 [2]세우기 [3]색뒤집기   ->    / \
   (A) (C새R)            중 걸리는 것만 실행                  (A) (C)
  규칙 위반은 빨강 쪽에서만 생기고, 위반은 그 자리에서 O(1)에 고쳐진다
```

아래 그림이 그 세 가지 수리([1][2][3])의 실제 모습이다.

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

#### 동작 — 삭제

**언제 쓰나**: 키를 지울 때. 추가와 반대로 "내려가면서 미리 준비하고 → 돌아 나오면서 되정리"한다.

- *double-black*: 고전 방식 삭제에서 "검정이 하나 모자란 상태"를 임시 표시하는 개념. LLRB에는 없다 — 미리 빨강을 만들어 내려가기 때문이다.
- *후행자(successor)*: 어떤 키보다 큰 것 중 가장 작은 키. 내부 노드를 지울 때 이 값으로 바꿔치기한다.

한 줄 요약 그림 — 전 상태 → 조작 → 후 상태:

```text
  전: 지울 노드가 검다(그냥 떼면          내려가는 길에                후: 붉어진 노드는
      검은 높이 규칙이 깨진다)            미리 빨강을 심는다               안전하게 뗀다
     (BB)                                  (BB)                          (CB)
     /   \            ->                   //   \\           ->          //
  (A지울B) (CB)                         (AR)     (CR)                  (BR)
                                         ^ 이제 붉으니 떼도 규칙 유지
```

아래 그림이 이 "미리 빨강 심기"(moveRedLeft)의 두 갈래(merge / borrow)다.

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

#### `필드`

- `static final boolean RED / BLACK` 역할:
- `Node<K,V> root` 역할:
- `int size` 역할:
- `Node.key` / `Node.value` / `Node.left` / `Node.right` / `Node.color` 역할:
- 불변식 4개(뿌리는 검다 · 빨간 링크는 왼쪽에만 · 빨강 연속 금지 · 검은 높이가 같다):

#### `static boolean isRed(Node<K,V> node)`

- 하는 일:
- 논리(null 을 검정으로 보는 이유):

#### `private Node<K,V> rotateLeft(Node<K,V> h)` (TODO)

- 하는 일:
- 논리(링크만이 아니라 색도 옮기는 이유):
- 비용(왜):

#### `private Node<K,V> rotateRight(Node<K,V> h)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

#### `private void flipColors(Node<K,V> h)` (TODO)

- 하는 일:
- 논리(대입이 아니라 반전이어야 하는 이유 · 넣기/지우기에서 방향이 반대인 것):
- 비용(왜):

#### `private Node<K,V> balance(Node<K,V> h)` (TODO)

- 하는 일:
- 논리(세 검사의 순서가 계약인 이유 · `else if` 가 아닌 이유):
- 비용(왜):

#### `private Node<K,V> put(Node<K,V> h, K key, V value, Object[] old)` (TODO)

- 하는 일:
- 논리(새 노드를 빨강으로 넣는 이유 · 반환값을 부모에 다시 대입하는 방식):
- 비용(왜):

#### `private Node<K,V> moveRedLeft(Node<K,V> h)` (TODO)

- 하는 일:
- 논리(내려가기 전에 미리 빨강을 확보 — 15번 B-트리의 "미리 채우기"와의 대응):
- 비용(왜):

#### `private Node<K,V> deleteMin(Node<K,V> h)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

#### `private Node<K,V> delete(Node<K,V> h, K key)` (TODO)

- 하는 일:
- 논리(key 비교를 두 번 하는 이유):
- 비용(왜):

#### `public K floorKey(K key)` (TODO)

- 하는 일:
- 논리("찾으면 바로 반환"이 안 되는 이유):
- 비용(왜):

#### `public V put(K key, V value)`

- 하는 일:
- 논리(마지막에 뿌리를 검게 강제하는 이유):
- 비용(왜):

#### `public V get(K key)`

- 하는 일:
- 비용(왜):

#### `public V remove(K key)`

- 하는 일:
- 논리(시작 전 뿌리를 빨갛게 만드는 줄의 뜻 — 지워도 테스트가 통과한다는 기록):
- 비용(왜):

#### `public K ceilingKey(K key)`

- 하는 일:
- 비용(왜):

#### `public List<K> keys()`

- 하는 일:
- 비용(왜):

#### `public K firstKey()` / `public K lastKey()`

- 하는 일:
- 비용(왜):

#### `public int height()`

- 하는 일:
- 비용(왜):

#### `public int blackHeight()`

- 하는 일:
- 논리(왼쪽 한 줄만 세도 되는 이유):
- 비용(왜):

#### `public boolean containsKey(K key)` / `public int size()` / `public boolean isEmpty()` / `public void clear()`

- 하는 일:
- 비용(왜):

### 구현 — RedBlackTreeMap (`src/main/java/com/datastructure/redblack/RedBlackTreeMap.java`)

TODO 없는 어댑터. 일은 전부 `RedBlackTree` 에 있고 여기는 `SortedTree` 계약으로 넘기기만 한다.

#### `필드`

- `RedBlackTree<K,V> tree` 역할:

#### `SortedTree 의 메서드 전부를 위임`

- 하는 일:
- 논리(같은 계약으로 여러 트리를 나란히 재기 위한 껍데기라는 것):

### 구현 — RedBlackTreeSet (`src/main/java/com/datastructure/redblack/RedBlackTreeSet.java`)

#### `필드`

- `static final Object PRESENT` 역할:
- `RedBlackTreeMap<K, Object> map` 역할:

#### `public boolean add(K key)` (TODO)

- 하는 일:
- 논리(별도 조회 없이 "새로 들어갔는지"를 아는 방법):
- 비용(왜):

#### `public boolean remove(K key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

#### `public boolean contains(K key)`

- 하는 일:
- 비용(왜):

#### `public List<K> toList()` / `public K first()` / `public K last()` / `public K floor(K key)` / `public K ceiling(K key)`

- 하는 일:
- 비용(왜):

#### `public int size()` / `public boolean isEmpty()` / `public void clear()`

- 하는 일:
- 비용(왜):

## 쓰이는 곳

- **Java `TreeMap` · `TreeSet`** — 정렬된 맵·집합의 표준 구현이 레드블랙 트리다. `floorKey`·`ceilingKey`·`subMap` 같은 순서 연산이 O(log n)이다.
- **Java 8 `HashMap`의 트리화** — 한 버킷의 사슬이 8개를 넘고(`TREEIFY_THRESHOLD = 8`) 테이블이 64칸 이상이면(`MIN_TREEIFY_CAPACITY = 64`) 그 연결 리스트를 레드블랙 트리로 바꿔 충돌 공격(HashDoS) 때 O(n)이 O(log n)이 되게 한다. 테이블이 64칸 미만이면 트리화 대신 리사이즈한다(JDK 8+ `HashMap` 소스·JEP 180). [05-hashmap](../05-hashmap/2-summary.md)의 체이닝이 여기로 이어진다.
- **C++ `std::map` · `std::set`** — 표준이 구조를 못 박지는 않지만 주요 구현(libstdc++ `_Rb_tree`, libc++ `__tree`, MSVC STL)이 레드블랙 트리다.
- **Linux 커널 스케줄러(CFS, 6.6 이전)** — 실행 대기 태스크를 `vruntime` 순으로 레드블랙 트리에 두고, 가장 왼쪽(가장 적게 실행된) 태스크를 다음에 돌렸다. 6.6부터 기본 스케줄러가 EEVDF로 바뀌었고, EEVDF도 부분트리 정보를 얹은 레드블랙 트리(augmented rbtree)에 태스크를 둔다. 고르는 규칙은 "가장 왼쪽"에서 마감 시각 기준으로 바뀌었다.
- **Linux 커널의 `epoll` 관심 목록** — 커널 공용 `rbtree`로 감시 중인 파일 디스크립터를 관리한다. 프로세스 주소 공간(VMA)도 6.1 이전에는 `rbtree`였지만, 6.1부터 maple tree(B-트리 계열)로 바뀌었다.
- **[30-interval-tree](../30-interval-tree/2-summary.md)** — 레드블랙 트리에 부가 정보(부분트리 최대 끝점)를 얹은 구조. CLRS 14장의 "확장(augmenting)"이 이것이다.
- **[15-b-tree](../15-b-tree/2-summary.md)의 이진판** — 레드블랙 트리는 2-3(-4) 트리를 이진 노드로 흉내낸 것이다. 다만 "메모리면 레드블랙"은 아니다 — Rust `BTreeMap`·Abseil `btree_map`처럼 메모리 안에서도 캐시 지역성을 노려 B-트리를 쓰는 곳이 있다. 어느 쪽이 빠른지는 키 크기·갱신 비용·캐시 지역성에 따라 달라진다.

## 적용 — 풀어나가는 법

레드블랙 트리 문제는 "지금 어느 불변식이 깨졌고, 어느 O(1) 손질이 그것을 되돌리는가"로 푼다.\
순서: ① 정렬 순서와 `floorKey`류 연산이 필요하고 최악 보장이 필요한지 확인한다 — 순서가 필요 없으면 해시맵(05), 디스크면 B-트리(15)다 → ② 넣기·지우기를 2-3 트리 동작으로 먼저 그려 본다(키 끼우기·노드 쪼개기·빌리기·병합) → ③ 그 동작을 회전·`flipColors`·`moveRedLeft`로 옮긴다 → ④ 넣는 내내·지우는 내내 규칙 넷을 단언한다 — 계약 테스트는 색이 엉망이어도 통과한다.\
아래 과제 11개가 이 순서다 — 회전·색 뒤집기·`balance`·`put`이 한 덩어리이고 지우기는 그다음이다.

### 문제 — 이 챕터가 시키는 것

06번 이진 탐색 트리가 정렬 입력에서 무너지는 문제에, 12번(확률)·15번(뚱뚱한 노드)에 이은 네 번째 답을 직접 구현한다.
메모리 안에서 노드 크기를 키우지 않고, 회전과 색 뒤집기만으로 높이 `2*log2(n+1)` 이하를 **보장**하는 좌편향 레드블랙 트리(LLRB)를 만드는 과제다.
`RedBlackTreeMapTest.java` 를 따라친 뒤 TODO 를 채운다(처음에는 26개 중 25개가 실패한다).

- `RedBlackTree` 의 TODO 9개 — `rotateLeft` · `rotateRight` · `flipColors` · `balance` · `put(내부)` · `moveRedLeft` · `deleteMin` · `delete` · `floorKey`
- `RedBlackTreeSet` 의 TODO 2개 — `add` · `remove`
- TODO 1~5(회전·색뒤집기·balance·put)가 한 덩어리이고, 거기까지 하면 넣기가 전부 된다. 지우기는 그다음이다.
- 불변식 넷(뿌리는 검다 · 빨강은 왼쪽만 · 빨강 연속 금지 · 검은 높이 동일)을 `RedBlackTreeInvariantTest` 가 넣는 내내·지우는 내내 직접 검사한다.
- 응용으로 따져볼 것: 회전이 색까지 옮겨야 하는 이유 · `balance` 세 검사의 순서와 `else if` 금지 · `flipColors` 가 반전이어야 하는 이유 · `delete` 의 key 비교 두 번.

아래 서머리는 이 문제(README)를 분석·정리한 것이다.

### 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| 12번 스킵 리스트 (확률) | | | |
| 15번 B-트리 (뚱뚱한 노드, 위로 자라기) | | | |
| 16번 좌편향 레드블랙 트리 (회전, 보장) | | | |
| 고전적 레드블랙 트리 (좌우 모두 허용 = 2-3-4) | | | |

## 장애 시나리오와 대처

**1. 답은 맞는데 점점 느려진다 — 색이 깨진 채 굴러가는 트리**

- 현상: `put`·`get` 결과는 전부 맞는데, 데이터가 쌓일수록 조회가 O(log n)답지 않게 느려진다.
- 보이는 형태: `height()`가 `2*log2(n+1)`을 넘는다. 계약 테스트는 통과하고 `RedBlackTreeInvariantTest`(검은 높이 동일·빨강 연속 금지)만 실패한다. 정렬 입력 벤치마크에서 시간이 n에 비례해 늘어난다.
- 원인: 회전이 링크만 옮기고 색을 안 옮겼거나, `balance`의 세 검사 순서를 바꿨거나 `else if`로 끊었다. 탐색 순서(왼쪽 작음·오른쪽 큼)는 멀쩡해서 답이 맞고, 균형만 조용히 무너진다(정답 4·5번 참고).
- 대처: 불변식을 직접 검사하는 테스트를 계약 테스트와 별도로 두고, 넣는 내내·지우는 내내 돌린다. 크기가 작은 트리는 모든 삭제 순서를 전수로 돈다.

**2. 넣은 키가 사라진다 — 키를 바꿨거나 비교 순서가 `equals`와 다르다**

- 현상: `TreeMap`에 분명히 넣은 키를 `get`하면 `null`이고, `size()`는 그대로다. 같은 키를 두 번 넣었는데 둘 다 들어가기도 한다.
- 보이는 형태: `containsKey`가 `false`인데 `keys()`를 훑으면 그 키가 보인다. 또는 `equals`로는 같은 두 객체가 서로 다른 항목으로 들어가 있다.
- 원인: (a) 트리에 넣은 뒤 키 객체의 비교 필드를 바꿨다 — 노드는 옛 위치에 있고 탐색은 새 값으로 내려가니 못 만난다. (b) `compareTo`(또는 `Comparator`)가 `equals`와 다른 기준을 본다 — 트리는 오직 비교 결과로만 "같다"를 판정한다.
  - *총순서(total order)*: 어떤 두 키든 비교할 수 있고, 그 결과가 서로 모순되지 않는 순서. 비교 함수가 이것을 깨면 트리 구조 자체가 무의미해진다.
- 대처: 키는 불변 객체로 둔다. `compareTo`가 0일 때 `equals`도 참이 되게 맞춘다. 비교 함수가 `NaN`·`null`처럼 순서가 없는 값을 받으면 예외로 드러내지 조용히 0을 돌려주지 않는다.

**3. 동시 수정 — `ConcurrentModificationException` 또는 조용한 손상**

- 현상: 한 스레드가 `put`하는 동안 다른 스레드가 순회하면 순회가 예외로 죽거나, 예외 없이 트리가 망가진다.
- 보이는 형태: `TreeMap` 순회 중 `ConcurrentModificationException`(단, 이 검사는 최선 노력일 뿐 동시 수정을 막아 주지는 않는다). 이 노트의 `RedBlackTree`에는 그 검사가 없어 회전 도중 끼어든 스레드가 잘린 부분트리를 보거나 키를 놓칠 수 있다.
- 원인: 회전은 포인터 여러 개를 순서대로 바꾸는 조작이라 중간 상태가 있다. 그 순간 다른 스레드가 읽으면 불변식이 깨진 트리를 본다.
- 대처: 쓰기를 락으로 감싸거나 한 스레드로 제한한다. 동시 읽기·쓰기가 필요하면 `ConcurrentSkipListMap`을 쓴다 — 락 없이 CAS로 링크를 바꾸는 스킵 리스트다(12번 스킵 리스트가 동시성에 유리한 이유).

## 핵심 문장

- 레드블랙 트리는 BST 붕괴에 대한 네 번째 답이다 — 12번(확률)은 최악을 못 막고 15번(뚱뚱한 노드)은 디스크 I/O에 맞춘 구조라서, 이진 노드 그대로 최악까지 보장하는 답이 따로 필요했다(같은 칸의 다른 답으로 AVL 트리도 있다).
- 균형의 정체는 "모든 뿌리-잎 경로의 검은 링크 수가 같다"이다 — 가장 긴 길이 가장 짧은 길의 두 배를 못 넘으니 높이가 `2*log2(n+1)` 이하로 보장된다.
- 빨간 링크로 묶인 두 노드를 한 덩어리로 보면 그대로 2-3 트리다 — 회전과 `flipColors`는 15번 B-트리의 쪼개기·빌리기·병합을 이진 트리에서 흉내낸 것이다.
- 넣기는 빨강으로 끼우고 올라오며 세 검사를 순서대로 연달아 하고, 지우기는 내려가기 전에 빨강을 미리 확보한다 — 둘 다 검은 높이를 한순간도 깨뜨리지 않기 위해서다.
- 색이 엉망이어도 답은 맞을 수 있다 — 그래서 불변식은 계약 테스트가 아니라 별도 테스트가 넣는 내내·지우는 내내 직접 검사해야 한다.

## 관련 주제·근거

- 선행 — [06-binary-search-tree](../06-binary-search-tree/2-summary.md): 정렬 입력에서 무너지는 원인. [15-b-tree](../15-b-tree/2-summary.md): 2-3 트리 대응이 회전·색 뒤집기를 설명한다.
- 대조 — [12-skip-list](../12-skip-list/2-summary.md): 같은 문제를 확률로 푼 답. 보장 대 기대값, 그리고 동시성에서의 차이.
- 응용 — [05-hashmap](../05-hashmap/2-summary.md)(버킷 트리화) · [30-interval-tree](../30-interval-tree/2-summary.md)(레드블랙 트리 확장).
- 후속 — [17-fenwick-tree](../17-fenwick-tree/2-summary.md): 균형을 지키려고 코드를 늘린 뒤, 반대로 "구간 합만 남기고 포기하면" 코드가 열 줄로 준다.
- 영역 표 — [data-structure/curriculum.md](../curriculum.md) `17-red-black-tree` (선행 `09-binary-search-tree`).
- 교재 — CLRS 3판 13장 레드블랙 트리 · Sedgewick 『Algorithms』 4판 3.3(좌편향 레드블랙 트리) · Sedgewick 2008 "Left-leaning Red-Black Trees" 논문.
- myway 원본 — `/home/jun/project/myway/data-structure/16-red-black-tree/` (README.md · impl/RedBlackTree.java · impl/RedBlackTreeSet.java).

### 관련 자료

<!-- 원본 문서·코드 경로. 기준 소스는 문서가 아니라 코드/원전이다. -->

- README: `/home/jun/project/myway/data-structure/16-red-black-tree/README.md`
- 구현: `/home/jun/project/myway/data-structure/16-red-black-tree/src/main/java/com/datastructure/redblack/`
- 테스트: `/home/jun/project/myway/data-structure/16-red-black-tree/src/test/java/com/datastructure/redblack/`
- 정답 구현: `/home/jun/project/myway/data-structure/16-red-black-tree/impl/`

### 용어 풀이

- **이진 탐색 트리(BST)**: 각 칸(노드)의 왼쪽엔 작은 값, 오른쪽엔 큰 값만 두는 나무 모양 자료구조. 반씩 잘라 가며 찾을 수 있다.
- **노드**: 트리의 칸 하나. 키·값과 자식으로 가는 연결선을 갖고 있다.
- **링크**: 부모 노드에서 자식 노드로 가는 연결선. 이 구현에선 색(빨강/검정)이 노드가 아니라 "그 노드로 들어오는 링크"에 칠해져 있다고 읽는다.
- **레드-블랙 트리**: 링크에 색을 칠하고 색 규칙으로 균형을 유지하는 BST. 높이가 O(log n)으로 보장된다.
- **LLRB(좌편향 레드-블랙 트리)**: 빨간 링크를 왼쪽에만 허용하는 단순화 버전. 고칠 경우의 수가 3개로 줄어든다.
- **CLRS 방식**: 유명 교과서(저자 이름 첫 글자)의 고전적 레드-블랙 트리 구현. 부모 포인터와 NIL sentinel을 쓴다. 이 구현은 그 방식이 아니다.
- **NIL sentinel**: "자식 없음"을 null 대신 나타내는 가짜 검정 노드. 경계 검사를 줄이려고 쓴다.
- **포인터/참조**: 다른 노드가 어디 있는지 가리키는 값. "연결선"이라고 생각하면 된다.
- **불변식**: 어떤 조작이 끝나도 항상 참이어야 하는 규칙. 여기선 "뿌리는 검다, 빨강은 왼쪽만, 빨강 연속 금지, 검은 높이 동일" 네 가지.
- **회전(rotate)**: 부모-자식의 상하 관계를 한 번 비틀어 바꾸는 조작. 값의 크기 순서는 그대로 두고 모양만 바꾼다. 포인터 몇 개만 바꾸므로 O(1).
- **flipColors(색 뒤집기)**: 한 노드와 두 자식의 링크 색을 동시에 반전하는 조작. 2-3 트리에서 꽉 찬 노드를 쪼개는 것과 같은 뜻.
- **검은 높이(black height)**: 뿌리에서 잎까지 내려가며 만나는 검은 링크의 개수. 모든 경로에서 같아야 한다.
- **잎(leaf)**: 자식이 없는 맨 끝 노드.
- **재귀**: 함수가 자기 자신을 다시 부르는 방식. 여기선 "내려갔다가 돌아 나오면서 각 노드를 고치는" 흐름을 만든다.
- **2-3 트리 / B-트리**: 한 노드에 키를 여러 개 담고 위로 자라는 균형 트리. 빨간 링크로 묶인 두 노드를 한 덩어리로 보면 LLRB는 2-3 트리와 같은 구조다.
- **split / merge / borrow**: B-트리 용어. 꽉 찬 노드 쪼개기(split), 빈약한 노드 합치기(merge), 형제에게서 키 하나 빌려오기(borrow). LLRB의 flipColors·moveRedLeft가 각각 이에 대응한다.
- **double-black**: 고전적 레드-블랙 삭제에서 "검정이 하나 모자란 상태"를 임시로 표시하는 개념. LLRB는 미리 빨강을 만들어 내려가므로 이게 필요 없다.
- **후행자(successor)**: 어떤 키보다 큰 것 중 가장 작은 키. 내부 노드를 지울 때 이 값으로 바꿔치기한다.
- **O(1) / O(log n) / O(n)**: 데이터가 n개일 때 걸리는 시간의 눈금. O(1)=항상 일정, O(log n)=n이 2배 돼도 한 걸음만 늘어남, O(n)=n에 비례.
- **계약(인터페이스)**: "이 메서드들을 이렇게 제공하겠다"는 약속(여기선 `SortedTree`). 구현이 달라도 같은 계약이면 바꿔 끼울 수 있다.
- **어댑터/위임**: 실제 일은 다른 클래스에 넘기고 겉모양(계약)만 맞춰 주는 껍데기 패턴. `RedBlackTreeMap`이 그 예.
- **floorKey / ceilingKey**: 주어진 키 이하 중 가장 큰 키 / 이상 중 가장 작은 키를 찾는 연산.
- **스킵 리스트**: 여러 층의 연결 리스트로 균형을 "확률적으로" 잡는 다른 정렬 자료구조(12장). 보장이 아니라 기대값이 O(log n).
