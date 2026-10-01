# data-structure/28-rope — 정리 (힌트)

## 해결하는 문제

문자열을 연속 배열 한 덩어리로 들고 있으면, 가운데에 한 글자를 넣을 때마다 그 뒤 전체를 옮겨야 한다.\
10MB 문서 한가운데에 타자 한 번 = `String`은 10MB 복사, `StringBuilder`는 뒤쪽 5MB 이동 — **키를 누를 때마다** 그렇다.

```text
연속 배열 (n 글자)                      로프 (조각 트리)
+---+---+---+---+---+---+---+            (뿌리)
| H | e | l | l | o | W | d |  <- 가운데 삽입      /    \
+---+---+---+---+---+---+---+          "Hel" "lo"   "Wd"   <- 잘린 잎 하나만 새로 쓴다
   뒤 절반을 전부 밀어 쓴다                나머지 조각은 손도 안 댄다
   옮긴 글자 = n                          옮긴 글자 <= leafMax (32)
```

로프는 연속을 포기하고 문자열을 짧은 조각(잎)으로 쪼개 트리로 묶는다. 편집이 "글자 옮기기"가 아니라 "조각 재연결"이 된다.\
쉬운 예: 두루마리 한 장 대신 쪽지 여러 장 + 목차. 한 줄 끼우면 쪽지 한 장만 자르고 목차만 고친다.\
똑같은 구조다: 이 노트의 `Rope`는 잎에만 글자를 두고, 내부 노드는 왼쪽 길이(weight)만 안다.\
실무 예: 텍스트 에디터의 문서 버퍼 — 수만 줄짜리 파일에서 키 한 번마다 전체를 복사할 수 없다. 편집 이력(undo)도 옛 버전을 그대로 두는 것으로 공짜가 된다.
  - *임의 접근(random access)*: i번째 글자를 바로 읽는 것. 배열은 O(1), 로프는 트리를 타고 내려가야 한다 — 이것이 로프가 내주는 대가다.

### 한눈에 — 쉽게 말하면

**비유: 두루마리 대 쪽지 묶음.** 글을 두루마리 한 장에 이어 쓰면, 중간에 한 줄 끼워 넣을 때 그 뒤 전체를 다시 써야 한다.
대신 글을 짧은 쪽지 여러 장에 나눠 쓰고 "몇 번째 쪽지 다음에 몇 번째"라는 목차로 묶어 두면,
중간에 끼워 넣을 때는 쪽지 한 장만 자르고 목차만 고치면 된다. 글자 대부분은 손도 안 댄다.

- 로프(rope) = 문서를 조각(잎)으로 나눠 트리(목차)로 묶은 문자열 자료구조.
- 편집(삽입·삭제·이어붙이기)이 "글자 옮기기"가 아니라 "조각 재연결"이 된다.
- 대가: i번째 글자를 읽으려면 목차를 타고 내려가야 한다(배열은 한 번에 읽는다).

```text
  배열: [Hello_World_of_the_Rope]          <- 한 덩어리. 중간 삽입 = 뒤 전체 다시 쓰기
  로프:         (목차)
               /      \
          (내부)      (내부)
          /    \      /     \
   "Hello_" "World_" "of_the_" "Rope"      <- 글자는 쪽지(잎)에만 있다
```

실제 텍스트 에디터가 **똑같은 구조다**: 수만 줄짜리 파일에서 키 한 번 누를 때마다 파일 전체를 복사할 수는 없으니, VS Code 같은 에디터는 문서를 조각 트리로 들고 조각만 재연결한다.

## 동작·원리

### 전체 흐름

```text
[1] 기준선 : 연속 배열 (StringBuilderStore)      [2] 조각 트리 (Rope)
    +---+---+---+---+---+---+                          (내부 w=6)
    | H | e | l | l | o | _ | ...                     /          \
    +---+---+---+---+---+---+                   "Hello_"      (내부 w=6)
    편집 = 새 버퍼에 n 글자 전부 옮김                          /        \
    charAt = O(1)                                       "World_"    "Rope"
              |                                     잎 = 글자, 내부 = weight(왼쪽 길이)
              v                                                |
[3] 세 연산이 전부다                                           v
    concat(a, b)  : 새 노드 하나가 둘을 자식 삼음   -> 옮긴 글자 0, O(1)
    split(index)  : 경로를 따라 내려가 한 잎만 자름  -> 옮긴 글자 <= leafMax, O(log n)
    charAt(i)     : i < weight ? 왼쪽 : (i -= weight, 오른쪽)  -> O(높이)
              |
              v
[4] insert = split 1 + concat 2      delete = split 2 + concat 1
    옛 로프는 그대로 산다 (불변) -> 새 로프는 경로 위 노드만 새로, 나머지는 공유
              |
              v
[5] 대가와 손잡이
    임의 접근 O(1) -> O(높이)  ·  앞에만 붙이면 기운다 -> rebalance()  ·  leafMax = 노드 수 vs 복사량
```

- [1] 비교 대상이 먼저다. 연속 배열은 읽기가 O(1)이지만 모든 편집이 새 버퍼에 n글자를 옮긴다. 이 노트는 시간이 아니라 **옮긴 글자 수**를 센다.
- [2] 로프는 글자를 잎에만 두고, 내부 노드는 "왼쪽 부분트리의 글자 수"(weight) 하나만 적어 둔다. i번째 글자가 왼쪽인지 오른쪽인지를 그 숫자로 판단한다.
  - *weight*: 내부 노드가 적어 둔 왼쪽 부분트리의 전체 길이. `index < weight`면 왼쪽, 아니면 `index -= weight` 하고 오른쪽.
- [3] 연산은 셋뿐이다. `concat`은 노드 하나를 새로 만들어 둘을 자식으로 삼는다(글자 이동 0). `split`은 경로를 따라 내려가 잎 하나만 자르고 올라오며 조각을 반대쪽과 다시 잇는다. `charAt`은 뿌리에서 잎까지 내려간다.
- [4] `insert`와 `delete`는 새 연산이 아니라 split과 concat의 조합이다. 로프가 불변이라 옛 로프의 부분트리를 그대로 자식으로 삼아도 안전하고, 그래서 새로 만드는 노드는 쪼개진 경로 위의 것뿐이다.
  - *불변(immutable)*: 한 번 만들면 안 고친다. 모든 편집이 새 로프를 돌려주고 옛 로프는 그대로 산다 — 실행 취소가 공짜인 이유.
- [5] 연속을 포기한 대가가 `charAt`의 O(높이)다. 앞에만 계속 붙이면 트리가 기울어 높이가 n에 가까워지므로 `rebalance()`로 잎을 순서대로 다시 세운다(글자 이동 0). 잎 크기 `leafMax`는 "노드 수"와 "복사량" 사이의 손잡이다.

### 계약 — CharSequenceStore (`src/main/java/com/datastructure/rope/CharSequenceStore.java`)

- `int length()`
- `char charAt(int index)`
- `String substring(int from, int to)`
- `CharSequenceStore concat(CharSequenceStore other)`
- `CharSequenceStore insert(int index, String s)`
- `CharSequenceStore delete(int from, int to)`
- `Split split(int index)`
- `String toString()`
- `long charsCopiedByLastOp()`
- `long charsCopiedTotal()`

### 보조 — (TODO 없는 값 객체 · 보조 타입)

- `Edit` (`Edit.java`) — 역할:
- `Edit.Insert(int index, String text)` — 역할:
- `Edit.Delete(int from, int to)` — 역할:
- `CharSequenceStore.Split(CharSequenceStore left, CharSequenceStore right)` — 역할:
- `RopeProblems.Lcp(int length, long comparedChars)` — 역할:

### 구현 — StringBuilderStore (`src/main/java/com/datastructure/rope/StringBuilderStore.java`)

#### 구조

로프가 얼마나 이득인지 재려면 비교 대상이 필요하다. 이 클래스가 그 기준선 — "문서 전체를 배열 한 덩어리로 드는" 가장 단순한 방법이다.
  - *StringBuilder / 버퍼(buffer)*: 글자들을 연속된 메모리 한 줄에 담아두는 자바의 글자 통. 여기서는 "연속 배열"의 대표로 쓴다.
  - *char*: 글자 하나를 담는 자바 타입.

```
StringBuilderStore - 기준선. 문서를 연속된 char 배열 하나(StringBuilder)에 통째로 담는다

  StringBuilderStore
  +-------------------------------------------------------+
  | buf            = "Hello_World"   만든 뒤 절대 안 고친다 |
  | copiedByLastOp = 0   이 객체를 만들어 낸 연산의 복사량   |
  | copiedTotal    = 0   계보를 따라 누적한 복사량           |
  +--------------------------+----------------------------+
                             |
                             v
   idx    0     1     2     3     4     5     6     7     8     9    10
       +-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
       |  H  |  e  |  l  |  l  |  o  |  _  |  W  |  o  |  r  |  l  |  d  |
       +-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
       |<------------------------ length() = 11 ------------------------>|

  charAt(i) / substring(from, to) = 자리 계산 한 번. O(1) / O(길이). 여기가 배열이 이기는 자리다
  모든 편집(concat, insert, delete, split)이 새 버퍼를 만들어 새 저장소를 돌려준다
    계약이 값(value)이라 편집 전 문서가 살아 있어야 하고, 배열 위에서 그것을 지키는 방법은
    매번 새 버퍼로 옮기는 것뿐이다. 제자리 편집을 허용해도 가운데 삽입이 O(n) 인 것은 안 바뀐다
  buf 를 아무도 안 고치므로 새 저장소에 그대로 넘겨 써도 안전하다
```

#### 동작 — 중간 삽입

**언제 쓰나**: 문서 가운데에 문자열을 끼워 넣을 때. 그림 먼저 — 위가 전 상태, 아래가 후 상태다. 배열이라 옛 버퍼의 글자 전부(n개)를 새 버퍼로 옮겨야 한다는 것이 요점이다.

```
insert(6, "Big_") : 앞 조각 + 넣을 문자열 + 뒤 조각을 순서대로 새 버퍼에 담는다

  before  buf  (n = 11)
       +---+---+---+---+---+---+---+---+---+---+---+
       | H | e | l | l | o | _ | W | o | r | l | d |
       +---+---+---+---+---+---+---+---+---+---+---+
       |<---- [0, 6) ---->|<------ [6, 11) ------->|
             그대로 옮김          4칸 밀려서 옮김
         \   \   \   \   \   \      \   \   \   \   \
          v    v    v    v    v    v      v    v    v    v    v
  after   새 버퍼 (n + 4 칸을 새로 잡는다)
       +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
       | H | e | l | l | o | _ | B | i | g | _ | W | o | r | l | d |
       +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
                               ^^^^^^^^^^^^^^^^^ 넣은 s (이건 안 센다)

  charsCopiedByLastOp = n = 11.  어디에 넣든 n 이다 - 맨 뒤여도 앞 n 글자를 새 버퍼로 옮긴다
    붙일 자리가 없어서다. 배열은 자기 크기만큼만 잡혀 있다
  넣는 s 를 안 세는 이유: 이미 있는 문자열을 자리에 놓는 것과 있던 문서를 통째로 다시 쓰는 것은
    다른 일이다. 로프도 s 를 안 센다. 두 구현이 같은 규칙으로 세야 비교가 성립한다
  01번 동적 배열의 add(index, E) 와 같은 결이다. 거기서는 뒤만 밀었고 여기서는 전부 옮긴다

  같은 규칙으로 잰 다른 연산
    concat(other) : n + m         왼쪽도 오른쪽도 새 버퍼로 옮긴다 (로프는 이 자리에서 0 이다)
    delete(f, t)  : n - (t - f)   살아남는 글자만 옮긴다 -> 많이 지울수록 싸진다
    split(index)  : n             어디서 쪼개든 양쪽을 다 새로 만들어야 한다
```

#### 필드
- `buf` — 역할:
- `copiedByLastOp` — 역할:
- `copiedTotal` — 역할:

#### `StringBuilderStore(String text)`
- 하는 일:
- 논리:
- 비용(왜):

#### `int length()` / `char charAt(int index)` / `String substring(int from, int to)`
- 하는 일:
- 논리:
- 비용(왜):

#### `StringBuilderStore concat(CharSequenceStore other)` (TODO 1)
- 하는 일:
- 논리:
- 비용(왜):

#### `StringBuilderStore insert(int index, String s)` (TODO 2)
- 하는 일:
- 논리:
- 비용(왜):

#### `StringBuilderStore delete(int from, int to)` (TODO 3)
- 하는 일:
- 논리:
- 비용(왜):

#### `Split split(int index)`
- 하는 일:
- 논리:
- 비용(왜):

#### `String toString()` / `long charsCopiedByLastOp()` / `long charsCopiedTotal()`
- 하는 일:
- 논리:
- 비용(왜):

### 구현 — Rope (`src/main/java/com/datastructure/rope/Rope.java`)

#### 구조

그림을 읽는 데 필요한 말 셋.
  - *weight*: 내부 노드가 적어 둔 "내 왼쪽 부분트리의 전체 글자 수". i번째 글자가 왼쪽에 있는지 오른쪽에 있는지를 이 숫자 하나로 판단한다.
  - *불변(immutable)*: 한 번 만들면 절대 안 고치는 것. 모든 편집이 새 로프를 돌려주고 옛 로프는 그대로 산다(26번 영속 자료구조와 같은 원리).
  - *캐시(cache)*: CPU 옆의 아주 빠른 임시 저장소. 연속된 메모리를 읽는 게 여기 잘 얹혀서, 잎을 어느 정도 크게 잡는 쪽이 빠르다.

```
Rope - 글자는 잎에만 있다. 내부 노드는 글자를 하나도 안 들고 weight 만 안다

                          +--------------------+
                   root : |  내부  weight = 12 |   weight = 왼쪽 부분트리의 전체 길이
                          |        length = 23 |   length = left.length + right.length
                          |        depth  = 2  |   depth  = 1 + max(왼쪽, 오른쪽)
                          +---------+----------+
                         /                      \
                        v                        v
          +--------------------+       +--------------------+
          |  내부  weight = 6  |       |  내부  weight = 7  |
          |        length = 12 |       |        length = 11 |
          +---------+----------+       +---------+----------+
              /            \               /             \
             v              v             v               v
      +------------+ +------------+ +-------------+ +------------+
      |  "Hello_"  | |  "World_"  | |  "of_the_"  | |   "Rope"   |  <- 잎: text 를 들고 있다
      | w=6  len=6 | | w=6  len=6 | | w=7   len=7 | | w=4  len=4 |     left = right = null
      +------------+ +------------+ +-------------+ +------------+     depth = 0

  문서 = 잎을 왼쪽부터 이은 것 = "Hello_World_of_the_Rope"     length() = root.length = 23
  자리    0                    6            12           19        23

  Node : text / left / right / weight / length / depth  (전부 final)
    잎이면 text 가 있고 left, right 가 null. 내부 노드면 반대다  (isLeaf() 는 text != null)
    length 와 depth 는 weight 로도 구할 수 있지만 매번 훑으면 O(n) 이라 만들 때 한 번 계산해 둔다
  EMPTY = 빈 잎 하나를 만들어 돌려 쓴다 (불변이라 공유해도 된다)
  DEFAULT_LEAF_MAX = 32  - 잎 하나에 담는 최대 글자 수. 이 상수가 절충이다
    1 로 두면 글자마다 노드다 (4096자 문서에 노드 8191개, 조회 한 번에 13노드를 지난다)
    문서 전체를 잎 하나에 담으면 노드는 1개인데 가운데 삽입마다 통째로 쪼갠다 (= 배열과 같은 값)
    실제 에디터는 훨씬 크게 잡는다 (수백~수천 바이트). 캐시 한 줄에 들어가는 것이 노드 하나를
    따라가는 것보다 훨씬 싸기 때문이다
  불변이다. 모든 연산이 새 Rope 를 돌려주고 옛 Rope 는 그대로 산다 (26번 영속 자료구조)
    그래서 남의 부분트리를 그대로 자식으로 삼아도 안전하고, concat 이 O(1) 이다
  계측 전용 필드 : charAtVisits (여기서만 final 이 아니다) / copiedByLastOp / copiedTotal
```

#### 동작 — charAt(index) 내려가기

**언제 쓰나**: i번째 글자 하나를 읽을 때. 그림 먼저 — 뿌리에서 잎까지 내려가는 세 걸음이고, 각 걸음의 판단은 "i 가 weight 보다 작은가" 하나뿐이다.
  - *재귀(recursion) / 스택 오버플로*: 함수가 자기 자신을 부르는 방식 / 그 호출이 너무 깊어져 메모리(호출 스택)가 터지는 것. 그래서 여기는 반복문으로 짠다.

```
charAt(15) : 뿌리에서 잎까지 내려가며 index 를 좁힌다. 답은 't' 다

  i = 15   뿌리에서 시작        +--------------------+
                               |  내부  weight = 12 |
                               +--------------------+
      i(15) < weight(12) ?  아니다  ->  i 에서 weight 를 뺀다 i = 15 - 12 = 3, 오른쪽으로
                                                         \
                                                          v
                                               +--------------------+
  i = 3                                        |  내부  weight = 7  |
                                               +--------------------+
      i(3) < weight(7) ?  그렇다  ->  i 는 그대로 3, 왼쪽으로
                                            /
                                           v
                                   +-------------+
  i = 3                            |  "of_the_"  |   잎에 닿았다
                                   +-------------+
                                     0 1 2 3
                                     o f _ t     ->  text.charAt(3) = 't'

  규칙은 두 줄이다
    index <  weight  ->  왼쪽으로. index 는 그대로 둔다
    index >= weight  ->  index -= weight 하고 오른쪽으로
  왜 빼는가 : 오른쪽 부분트리 안에서의 자리는 왼쪽 부분트리 길이만큼 당겨진 값이기 때문이다

  비용 = 지난 노드 수 = 트리 높이. 균형이면 O(log n), 기울면 O(높이)
    charAtVisits 가 그 걸음을 센다 (잎도 센다). 배열이면 언제나 1 이었을 값이다
  반복문으로 짠다. 재귀면 기운 트리에서 스택이 터진다 (앞에만 계속 붙인 로프는 깊이가 10만이 된다)
  함정: 빼는 것을 빠뜨려도 컴파일되고 예외도 안 나고 왼쪽 절반은 맞는 답이 나온다
        무작위 대조(RopeCrossCheckTest)가 그것을 잡는다
```

#### 동작 — concat

**언제 쓰나**: 두 문서를 이어 붙일 때. 그림 먼저 — 전 상태는 로프 두 개, 후 상태는 그 둘을 자식으로 삼은 새 노드 하나다. 글자는 한 글자도 안 옮긴다.

```
concat(other) / concatNodes(a, b) : 새 내부 노드 하나로 둘을 자식 삼는다. 글자는 안 옮긴다

  before   로프 A ("Hello_World_")           로프 B ("of_the_Rope")
              +--------+                        +--------+
              |   Na   |                        |   Nb   |
              +---+----+                        +---+----+
                 / \                              / \
          "Hello_"  "World_"               "of_the_"  "Rope"

  after    새로 생기는 것은 노드 하나뿐이다
                     +---------------------------+
                     |  weight = Na.length = 12  |   <- 왼쪽 길이를 적어 둔 것이 전부다
                     |  length = 12 + 11 = 23    |
                     +------+-------------+------+
                           /               \
                     +--------+          +--------+
                     |   Na   |          |   Nb   |   <- 둘 다 옛 노드 그대로. 새로 안 만든다
                     +---+----+          +---+----+
                        / \                 / \
                 "Hello_"  "World_"  "of_the_"  "Rope"    (같은 String 객체를 공유한다)

  charsCopiedByLastOp = 0.  O(1) 이다
  왜 안전한가 : 로프가 불변이라 아무도 노드를 안 고친다. 옛 로프 A 도 B 도 그대로 산다
    고칠 수 있는 자료구조였다면 한쪽을 복사해야 했다
  상대가 로프가 아니면(StringBuilderStore) 글자를 꺼내 와야 하므로 그때만 복사가 생긴다
  한쪽이 비었으면(Node.length == 0) 노드를 만들지 말고 반대쪽을 그대로 돌려준다
    빈 잎을 매달면 조회할 때마다 지나가야 하고 leafCount 가 부풀며 split 이 만든 빈 조각이 쌓인다
  대가 : 앞에만 계속 붙이면 트리가 기운다. depth 가 10만이 될 수 있고 charAt 이 O(n) 이 된다
    -> rebalance() 가 잎을 순서대로 모아 다시 세운다. O(잎 개수) 이고 글자는 한 개도 안 옮긴다
       (잎 객체를 그대로 다시 매달기 때문이다. 새로 만드는 것은 글자가 없는 내부 노드뿐)
       언제 부를지는 정책이라 이 클래스가 안 정한다. 부르는 쪽이 정한다
  대비 : StringBuilderStore.concat 은 n + m 글자를 새 버퍼로 전부 옮긴다. 여기가 28번의 출발점이다
```

#### 동작 — split(index)

**언제 쓰나**: 문서를 i번째 자리에서 앞뒤 두 문서로 가를 때. insert/delete 의 재료가 되는 연산이다. 그림 먼저 — 전 상태 트리, 내려가는 길(네 경우 중 하나씩 판단), 후 상태 두 트리 순서다. 글자 복사는 잘린 잎 한 장에서만 일어난다.

```
split(9) : 경로를 따라 내려가며 트리를 둘로 가르고, 갈라진 조각을 반대쪽과 다시 이어 붙인다

  before                           root (weight = 12)
                                 /                  \
                        Na (weight = 6)          Nb (weight = 7)
                          /        \               /        \
                   "Hello_"     "World_"    "of_the_"      "Rope"

  내려가는 길                                  splitNode 의 네 경우
    root     : 9 < weight(12)                   index == 0            {EMPTY, node}
               -> 왼쪽을 9 에서 쪼갠다          index == node.length  {node, EMPTY}
    Na       : 9 > weight(6)                    잎이다   text 를 자른다 여기서만 글자를 복사한다
               -> 오른쪽을 (9-6)=3 에서 쪼갠다  내부다   weight 와 비교해 한쪽으로 내려간다
    "World_" : 잎이다 -> "Wor" | "ld_"                    index < weight  왼쪽을 쪼갠다
               copied += 6                                index > weight  오른쪽을 index-weight 에서
                                                          index == weight {left, right} 그대로

  올라오며 재조립 (갈라진 조각을 반대쪽과 다시 concatNodes 로 잇는다)
    Na 자리 (index > weight)  : { concatNodes("Hello_", "Wor") ,  "ld_" }
    root 자리 (index < weight): { 위의 왼쪽 조각 ,  concatNodes("ld_", Nb) }

  after    left = "Hello_Wor"                right = "ld_of_the_Rope"
             +--------------+                    +--------------+
             | weight = 6   |                    | weight = 3   |
             | length = 9   |                    | length = 14  |
             +---+------+---+                    +---+------+---+
                /        \                          /        \
         "Hello_"        "Wor"                  "ld_"         Nb   <- 옛 객체 그대로 공유
                                                              / \
                                                      "of_the_"  "Rope"

  charsCopiedByLastOp = 잘린 잎 하나의 길이 = 6.  leafMax 이하로 묶인다
  새로 만드는 노드 = 쪼개진 경로 위의 것뿐이고 나머지는 옛 로프와 같은 객체를 공유한다 -> O(log n)
  index == weight 면 이미 경계다 -> {left, right} 를 그대로 돌려준다. 복사가 0 이다
    그래서 같은 자리를 계속 치는 편집은 두 번째부터 공짜다 (CopyCostTest 가 그 값을 잰다)
  함정: 조각을 반대쪽과 다시 붙이는 것을 빠뜨리면 글자가 조용히 사라진다. 길이만 줄고 예외는 없다
  대비 : StringBuilderStore.split 은 어디서 쪼개든 n 글자를 옮긴다
```

#### 동작 — insert/delete 비용 비교

**언제 쓰나**: 끼워 넣기(insert)와 지우기(delete). 둘 다 새 연산이 아니라 "split 으로 가르고 concat 으로 다시 잇는" 조합이라는 것이 요점이다. 그림과 표 먼저.
  - *GC(가비지 컬렉션)*: 아무도 안 가리키는 객체를 자바가 알아서 치우는 것. delete 로 버린 가운데 조각도, 옛 로프가 안 가리키게 되는 순간 치워진다.

```
insert = splitNode 한 번 + concatNodes 두 번.   delete = splitNode 두 번 + concatNodes 한 번

  insert(9, "XY")
      splitNode(root, 9)      ->  [ 앞 ]              [ 뒤 ]
      buildLeaves("XY", ...)  ->          [가운데]
      concatNodes(concatNodes(앞, 가운데), 뒤)

                   +-----------+              앞 과 뒤 의 부분트리는 옛 로프와 공유한다
                   | 새 노드    |              새로 생기는 노드 = 쪼개진 경로 위의 것뿐이다
                   +--+-----+--+              4096자 문서에서 노드 12개다
                     /       \                (RopeStructureTest 가 그것을 센다)
             +-----------+   [ 뒤 ]
             | 새 노드    |
             +--+-----+--+
               /       \
          [ 앞 ]       "XY"
      s 가 비었으면 트리를 그대로 쓰는 새 로프를 돌려준다 (복사 0). this 를 돌려주면 안 된다 -
      계기가 "이번 연산"을 가리켜야 하는데 옛 로프의 charsCopiedByLastOp 가 딸려 나온다

  delete(from, to)
      splitNode(root, from)         -> [ 앞 ][ 나머지 ]
      splitNode(나머지, to - from)  -> [ 지울것 ][ 뒤 ]   <- to 가 아니라 to - from 이다
      concatNodes(앞, 뒤)                                   나머지의 시작이 원래 from 이라 당긴다
      버린 가운데는 아무도 안 가리키면 GC 가 가져간다.
      다만 옛 로프는 여전히 그 조각을 가리키고 있다 - 그래서 실행 취소가 공짜다

  왜 중간 삽입이 배열과 다른가 (n = 문서 길이, 옮긴 글자 수로 잰다)
  +----------------------+---------------------------+------------------------------------+
  | 연산                 | StringBuilderStore        | Rope                               |
  +----------------------+---------------------------+------------------------------------+
  | insert(가운데, s)    | n  (문서 전체를 새 버퍼로)| 잘린 잎 하나 <= leafMax(32)        |
  |                      | O(n) 복사                 | + 경로 노드 O(log n) 개 새로 만듦  |
  | concat(other)        | n + m                     | 0   (노드 하나. O(1))              |
  | delete(from, to)     | n - (to - from)           | 잘린 잎 최대 2개 (<= 2 * leafMax)  |
  |                      | 많이 지울수록 싸진다      | 넓게 지울수록 잎을 두 번 쪼갠다    |
  | split(index)         | n                         | 0 ~ leafMax (경계면 0)             |
  | charAt(index)        | O(1)                      | O(높이)                            |
  +----------------------+---------------------------+------------------------------------+

  요점 : 배열은 "연속"을 지키느라 편집마다 전체를 옮긴다. 로프는 연속을 포기하고 조각을 재연결한다
         옮기는 것은 잘린 잎 하나뿐이고, 나머지는 포인터를 다시 거는 일이라 O(log n) 이다
         연속을 포기한 대가가 charAt 의 O(높이) 다. 공짜로 얻은 것이 아니다
  세는 규칙은 두 구현이 같다 - 실제로 메모리에서 메모리로 옮긴 글자만 센다. 넣는 s 는 안 센다
```

#### 필드
- `DEFAULT_LEAF_MAX` (public static final) — 역할:
- `root` — 역할:
- `leafMax` — 역할:
- `copiedByLastOp` / `copiedTotal` — 역할:
- `charAtVisits` — 역할:
- `EMPTY` — 역할:
- `Node.text` — 역할:
- `Node.left` / `Node.right` — 역할:
- `Node.weight` — 역할:
- `Node.length` — 역할:
- `Node.depth` — 역할:

#### `Rope(String text)` / `Rope(String text, int leafMax)`
- 하는 일:
- 논리:
- 비용(왜):

#### `int length()`
- 하는 일:
- 논리:
- 비용(왜):

#### `char charAt(int index)` (TODO 5)
- 하는 일:
- 논리:
- 비용(왜):

#### `String substring(int from, int to)`
- 하는 일:
- 논리:
- 비용(왜):

#### `void appendRange(Node node, int from, int to, StringBuilder out)` (TODO 9, private static)
- 하는 일:
- 논리:
- 비용(왜):

#### `Node concatNodes(Node a, Node b)` (TODO 4, static)
- 하는 일:
- 논리:
- 비용(왜):

#### `Rope concat(CharSequenceStore other)`
- 하는 일:
- 논리:
- 비용(왜):

#### `Split split(int index)`
- 하는 일:
- 논리:
- 비용(왜):

#### `Node[] splitNode(Node node, int index, long[] copied)` (TODO 6, static)
- 하는 일:
- 논리:
- 비용(왜):

#### `Rope insert(int index, String s)` (TODO 7)
- 하는 일:
- 논리:
- 비용(왜):

#### `Rope delete(int from, int to)` (TODO 8)
- 하는 일:
- 논리:
- 비용(왜):

#### `Rope rebalance()` (TODO 10)
- 하는 일:
- 논리:
- 비용(왜):

#### `String toString()`
- 하는 일:
- 논리:
- 비용(왜):

#### `long charsCopiedByLastOp()` / `long charsCopiedTotal()`
- 하는 일:
- 논리:
- 비용(왜):

#### `int leafMax()` / `int depth()` / `int leafCount()` / `int nodeCount()` / `List<String> leaves()`
- 하는 일:
- 논리:
- 비용(왜):

#### `long charAtVisits()` / `void resetCharAtVisits()`
- 하는 일:
- 논리:
- 비용(왜):

## 쓰이는 곳

- **텍스트 에디터의 문서 버퍼** — Xi 에디터·CodeMirror 6·Zed가 로프를 쓴다(원본 README). VS Code는 piece table의 조각들을 레드블랙 트리로 묶은 piece tree를 쓴다(VS Code 블로그 「Text Buffer Reimplementation」 2018) — 로프는 아니지만 "조각 + 트리 + 옮긴 글자 최소화"라는 발상은 같다.
- **협업 편집기·CRDT 문서** — 여러 사용자의 삽입·삭제가 문서 곳곳에 흩어져 들어온다. 편집마다 전체 복사는 불가능하므로 조각 트리 위에 얹는다. [ops-patterns/15-crdt](../../ops-patterns/15-crdt/2-summary.md)의 시퀀스 CRDT가 그 위층이다.
- **대용량 로그 뷰어** — 뒤에 계속 붙는 문서를 `concat` O(1)로 받는다. 대신 앞에만 붙이면 기울어 `rebalance` 정책이 필요하다.
- **Java `String` / `StringBuilder`** — 기준선. `String`은 불변이라 이어붙이기마다 전체 복사, `StringBuilder`는 뒤만 밀지만 가운데 삽입은 여전히 O(n). 이 노트의 `StringBuilderStore`가 그것을 감싼 것이다.
- **C++ SGI STL의 `rope`** — C++ 표준에는 없는 SGI STL의 확장 구현이고, GCC libstdc++에 `<ext/rope>`(`__gnu_cxx::rope`)로 남아 있다. 원전 Boehm 외 1995의 저자가 만들었다 [?].
- **영속 자료구조의 문자열 판** — 옛 버전이 그대로 살아 undo·버전 비교(문제 2의 공유 부분트리 건너뛰기)가 공짜다. [26-persistent](../26-persistent/2-summary.md)와 같은 원리다.
- **다른 챕터의 재료** — [01-dynamic-array](../01-dynamic-array/2-summary.md)의 "맨 앞 삽입 O(n)"이 출발점이고, 기운 트리를 다시 세우는 문제는 [06-binary-search-tree](../06-binary-search-tree/2-summary.md)·[23-splay-tree](../23-splay-tree/2-summary.md)와 같은 자리다.

## 적용 — 풀어나가는 법

로프 문제는 "편집이 많은가, 읽기가 많은가"를 먼저 묻는 데서 갈린다.\
순서: ① 워크로드를 센다 — 가운데 편집이 잦으면 로프, 읽기가 압도적이면 배열(정답 4번 참고) → ② 모든 편집을 `split`과 `concat`으로 분해한다(insert = split 1 + concat 2, delete = split 2 + concat 1) → ③ 비용은 시간이 아니라 **옮긴 글자 수**로 센다(`charsCopiedByLastOp`) → ④ 편집을 반복한 뒤 깊이를 보고 `rebalance` 시점을 정한다.\
아래 과제와 두 문제가 이 순서로 풀린다.

### 문제 — 이 챕터가 시키는 것

원본 README는 01번 동적 배열에서 **맨 앞에 넣는 것이 O(n)** 이었던 자리를, 자바 `String`·`StringBuilder` 까지 끌고 와 다시 묻는 상자라고 소개한다.\
10MB 문서 **가운데에 한 글자**를 넣으면 `String` 은 10MB 를, `StringBuilder` 는 뒤쪽 5MB 를 옮긴다 — **타자 한 번마다** 그렇다.\
로프는 문자열을 이진 트리의 **잎에 조각으로** 나눠 담고 내부 노드는 왼쪽 부분트리의 길이(weight)만 안다 — 이어붙이기 O(1), 가운데 삽입·삭제 O(log n) 을 사고 **임의 접근 O(1) 을 O(log n) 에 내주는 것**이 이 장의 거래다.\
그리고 이 상자도 시간이 아니라 **옮긴 글자 수**를 센다 — `charsCopiedByLastOp` / `charsCopiedTotal` 이 그 계기다.

과제 목록 — `src/main/java/com/datastructure/rope/`의 TODO 12개:

- `StringBuilderStore`(기준선) — TODO 1(`concat`) · TODO 2(`insert`) · TODO 3(`delete`) — "왜 한 글자에 문서 전체를 옮기는가"를 손으로 보는 자리
- `Rope` — TODO 4(`concatNodes`) · TODO 5(`charAt`) · **TODO 6(`splitNode` — 본체, 네 경우)** · TODO 7(`insert` = split 1 + concat 2) · TODO 8(`delete` = split 2) · TODO 9(`appendRange`) · TODO 10(`rebalance`)
- `RopeProblems` — TODO 11(`applyEdits`) · TODO 12(`longestCommonPrefix` — 공유한 부분트리는 참조 비교로 건너뛰기)

순서: `StringBuilderStore` 3개로 기준선을 먼저 만들고 → `Rope` 7개(`splitNode` 가 본체, 나머지는 그 위에 얹힌다) → `RopeProblems` 2개.\
실행: `cd ~/project/myway/data-structure && ./run.sh 28` — README 기준 **110개 중 82개가 실패**한다.

아래 서머리는 이 문제(README)를 분석·정리한 것이다.

### 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| StringBuilderStore (연속 배열) | | | |
| Rope (트리 + 조각) | | | |
| Rope, leafMax 작게 | | | |
| Rope, leafMax 크게 | | | |

### 문제 — RopeProblems (`src/main/java/com/datastructure/rope/RopeProblems.java`)

#### 문제 1. 편집 목록을 순서대로 적용한다 — `applyEdits(CharSequenceStore doc, List<Edit> edits)` (TODO 11)

> 문제 설명: 에디터가 하는 일이 이것이다. 키 입력 하나가 편집 하나이고, 문서는 그때마다 새로 만들어진다.
> 같은 목록을 `StringBuilderStore` 와 `Rope` 에 주고 `charsCopiedTotal` 을 비교하는 것이 이 박스의 한계 측정이다.
> 답은 반드시 같고 옮긴 글자 수만 다르다.
> `Edit` 은 sealed 이므로 두 경우(`Insert`, `Delete`)를 다 덮을 수 있다.
> 생각할 것: 이 계약에서 `doc` 은 안 바뀐다. 편집 목록이 비었으면 무엇을 돌려주는가.

- 내 접근:
- 논리:
- 비용(왜):

#### 문제 2. 두 문서의 공통 접두사 — `longestCommonPrefix(CharSequenceStore a, CharSequenceStore b)` (TODO 12: `sharedAwarePrefix`)

> 문제 설명: 두 문서의 공통 접두사 길이를 구한다. 비교한 글자 수(`Lcp.comparedChars`)도 같이 돌려준다.
> 로프 둘이면 구조를 이용하고, 아니면 나이브(`naiveLongestCommonPrefix`, 미리 채워져 있음)로 간다.
> `longestCommonPrefixLength` 는 길이만 필요할 때 쓰는 형태다.
> 생각할 것: 잎 크기가 다른 두 로프도 들어온다. 잎 경계가 어긋나도 답이 같아야 한다.
> 나이브는 두 문서가 실제로 같은 조각을 공유하고 있어도 알 길이 없다 — 왜인가.

- 내 접근:
- 논리:
- 비용(왜):

## 장애 시나리오와 대처

**1. 뒤에만 붙이는 로그 뷰어가 어느 순간 `StackOverflowError`로 죽는다**

- 현상: 줄이 들어올 때마다 `concat`으로 붙이기만 하던 문서가, 화면에 그리려고 `toString()`을 부르는 순간 죽는다.
- 보이는 형태: `java.lang.StackOverflowError` — 스택 트레이스에 `appendRange`(잎 모으기)가 수만 번 반복된다. 원본 README 실측으로 이 기계 기본 스택에서 깊이 19,628은 살고 19,726에서 터진다. `charAt`은 반복문이라 그 깊이에서도 산다.
- 원인: `concat`은 새 노드 하나로 둘을 자식 삼을 뿐 모양을 안 고친다. 한쪽에만 계속 붙이면 깊이가 붙인 횟수만큼 자라고(1000번이면 999), 재귀로 짠 `toString`·잎 모으기가 그 깊이를 그대로 호출 스택에 얹는다.
- 대처: `rebalance()`를 부르는 **정책**을 밖에서 정한다 — 예: `depth()`가 `2 * log2(leafCount)`를 넘으면, 또는 편집 N번마다. 옮기는 글자는 0이므로 자주 불러도 싸다(정답 6번 참고). 실무 구현이 자동 재균형을 거는 이유다.

**2. undo 이력을 무한정 붙잡아 메모리가 줄지 않는다**

- 현상: 편집을 계속하는데 힙이 단조 증가한다. 문서 크기는 그대로다.
- 보이는 형태: `OutOfMemoryError: Java heap space`. 힙 덤프에 `Rope$Node`가 수십만 개 — `delete`로 버린 가운데 조각이 여전히 살아 있다.
- 원인: 로프는 불변이라 옛 로프가 지운 조각을 계속 가리킨다. 옛 버전 목록(undo 스택)을 상한 없이 쌓으면 GC가 어떤 조각도 치우지 못한다 — 26번의 "옛 버전 참조 → 메모리 회수 불가"가 문자열에서 나온 모양이다.
- 대처: undo 스택에 길이 상한을 두고 오래된 버전의 참조를 끊는다. 스냅샷 간격을 두어(N번마다 한 버전만 보관) 공유되지 않는 노드만 살아남게 한다.

**3. 작은 편집이 누적돼 잎이 잘게 부서지고, `rebalance`로도 안 돌아온다**

- 현상: 오래 편집한 문서에서 `charAt`·`substring`이 점점 느려진다. `rebalance()`를 불러도 `leafCount()`가 줄지 않는다.
- 보이는 형태: `leafCount()`가 편집 횟수를 따라 늘기만 하고 잎 평균 길이(`length() / leafCount()`)가 `leafMax`보다 훨씬 작아진다. 조회 한 번의 방문 노드 수가 계속 커진다(원본 README 「측정」6의 표: 같은 4096자라도 잎이 작을수록 4096번 조회의 방문 노드가 는다).
- 원인: `split`은 잎을 자르기만 하고 합치지 않는다. `rebalance`는 모양(깊이)만 고치고 잎은 그대로 다시 매단다 — 복사 0을 지키기 때문이다. 작은 잎을 합치려면 글자를 옮겨야 하므로 이 노트의 `rebalance`는 하지 않는다(원본 README 한계 4).
- 대처: 실제 구현처럼 재균형 때 짧은 이웃 잎을 `leafMax`까지 합치는 단계를 둔다 — 복사 0은 깨지지만 그 값을 내고 조회를 되찾는다. 또는 편집이 뜸해진 시점에 `new Rope(toString(), leafMax)`로 통째로 다시 짓는다(O(n) 한 번).

## 핵심 문장

- 연속 배열은 "연속"을 지키느라 편집마다 전체를 옮긴다. 로프는 연속을 포기하고 글자를 잎에만 두며, 편집을 "잘린 잎 하나 + 경로 위 노드 재연결"로 바꾼다.
- 연산은 셋뿐이다 — `concat`은 노드 하나(글자 이동 0), `split`은 경로 따라 잎 하나 자르기(≤ leafMax), `charAt`은 weight로 좌우를 고르며 내려가기(O(높이)). insert와 delete는 이 셋의 조합이다.
- 로프가 불변이라 옛 부분트리를 그대로 자식 삼을 수 있고, 그래서 concat이 O(1)이며 옛 버전(undo)이 공짜로 산다 — 26번 영속 구조와 같은 원리다.
- 내준 것은 임의 접근이다: `charAt`이 O(1)에서 O(높이)가 되고, 한쪽에만 붙이면 높이가 n에 가까워져 `rebalance`가 필요하다. 어떤 방법으로도 O(1)로는 안 돌아온다.
- `leafMax`는 노드 수와 복사량 사이의 손잡이다 — 작으면 노드가 폭발하고 크면 배열처럼 복사가 폭발한다. 편집이 많을 때만 로프가 이긴다.

## 관련 주제·근거

- 선행 — [01-dynamic-array](../01-dynamic-array/2-summary.md): 맨 앞·가운데 삽입 O(n)의 출발점. 같은 데이터를 연속으로 놓아 조회를 산 쪽.
- 선행 — [26-persistent](../26-persistent/2-summary.md): 불변 + 구조 공유. 로프의 concat O(1)과 공짜 undo가 여기서 온다.
- 연결 — [06-binary-search-tree](../06-binary-search-tree/2-summary.md) · [23-splay-tree](../23-splay-tree/2-summary.md): 기운 트리와 재균형 — `rebalance()`가 서는 자리.
- 후속 — [ops-patterns/15-crdt](../../ops-patterns/15-crdt/2-summary.md): 협업 편집에서 조각 트리 위에 얹히는 병합 규칙.
- 영역 표 — [data-structure/curriculum.md](../curriculum.md) `41-rope` (선행 `09`, 원전 Boehm 외 1995).
- myway 원본 — `/home/jun/project/myway/data-structure/28-rope/` (README.md · impl/Rope.java · impl/StringBuilderStore.java · impl/RopeProblems.java).

### 관련 자료

- 원본 README: `/home/jun/project/myway/data-structure/28-rope/README.md`
- 구현 대상: `/home/jun/project/myway/data-structure/28-rope/src/main/java/com/datastructure/rope/`
- 테스트: `/home/jun/project/myway/data-structure/28-rope/src/test/java/com/datastructure/rope/`
- 정답 구현: `/home/jun/project/myway/data-structure/28-rope/impl/`

### 용어 풀이

- **로프(rope)**: 긴 문자열을 조각(잎)으로 나눠 트리로 묶은 자료구조. 편집이 "글자 옮기기" 대신 "조각 재연결"이 된다.
- **잎(leaf) / 내부 노드**: 실제 글자 조각을 든 트리 맨 아래 노드 / 글자 없이 왼쪽·오른쪽 연결과 weight 만 든 위층 노드.
- **weight**: 내부 노드가 적어 둔 "왼쪽 부분트리의 전체 글자 수". i번째 글자를 찾을 때 좌우 판단 기준.
- **버퍼(buffer) / StringBuilder**: 글자들을 연속된 메모리에 담는 통. 배열 기반 문자열의 대표.
- **char**: 글자 하나를 담는 자바 타입.
- **불변(immutable)**: 한 번 만들면 안 고치는 것. 모든 편집이 새 객체를 돌려주고 옛것은 그대로 산다.
- **영속 자료구조(persistent)**: 편집할 때마다 새 버전이 생기고 옛 버전도 계속 읽을 수 있는 구조(26번). 로프도 그렇다 — 실행 취소(undo)가 공짜인 이유.
- **구조 공유**: 새 버전이 옛 버전과 안 바뀐 부분(부분트리·String 객체)을 복사 없이 함께 가리키는 것.
- **split / concat**: 문서를 한 자리에서 두 개로 가르기 / 두 문서를 하나로 잇기. insert 와 delete 는 이 둘의 조합이다.
- **leafMax**: 잎 하나에 담는 최대 글자 수. 작으면 노드가 너무 많아지고, 크면 배열처럼 복사가 커지는 절충 손잡이.
- **캐시(cache) / 캐시 지역성**: CPU 옆의 아주 빠른 임시 저장소 / 연속된 메모리를 읽을 때 캐시가 잘 맞아 빨라지는 성질. 잎을 크게 잡는 이유.
- **재귀(recursion)**: 함수가 자기 자신을 부르는 방식.
- **스택 오버플로(stack overflow)**: 함수 호출이 너무 깊어져 호출 기록 메모리가 터지는 오류. 기운 트리 + 재귀 charAt 의 위험.
- **균형 / 기운 트리**: 좌우 크기가 비슷해 높이가 log n 인 트리 / 한쪽으로만 길어져 높이가 n 에 가까운 트리.
- **rebalance**: 잎을 순서대로 모아 트리를 다시 고르게 세우는 것. 글자는 안 옮기고 내부 노드만 새로 만든다.
- **O(1) / O(log n) / O(n) / O(높이)**: 일의 양이 항상 일정 / 트리 층수만큼 / 전체 글자 수에 비례 / 트리 높이만큼. n은 문서 길이.
- **GC(가비지 컬렉션)**: 아무도 안 가리키는 객체를 자바가 알아서 치우는 것.
- **sealed**: 자바에서 "이 타입의 종류는 여기 나열한 것뿐"이라고 못 박는 문법. Edit 이 Insert/Delete 둘뿐임을 보장한다.
- **접두사(prefix) / LCP**: 문자열의 앞부분 / 두 문자열이 앞에서부터 같은 가장 긴 길이(longest common prefix).
- **나이브(naive)**: 구조를 이용하지 않고 앞에서부터 하나씩 다 비교하는 가장 단순한 방법.
