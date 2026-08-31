# data-structure/20-radix-trie — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 계약 — PrefixMap (`src/main/java/com/datastructure/radix/PrefixMap.java`)

- `V put(String key, V value)`
- `V get(String key)`
- `boolean containsKey(String key)`
- `V remove(String key)`
- `int size()`
- `boolean isEmpty()`
- `void clear()`
- `List<String> keys()`
- `List<String> keysWithPrefix(String prefix)`
- `int countWithPrefix(String prefix)`
- `String longestPrefixOf(String s)`

## 구현 — RadixTrie (`src/main/java/com/datastructure/radix/RadixTrie.java`)

<!-- 메서드마다 내 언어로. 복잡도는 "왜 그런지"까지. -->

### 구조

```
Node<V> 한 개가 들고 있는 것
    edge      : 이 노드로 들어오는 간선에 적힌 "문자열 조각" (root 는 "")
    children  : Map<Character, Node<V>>  - 키는 자식 edge 의 "첫 글자" 한 개
    value     : null 이면 키가 아니라 그냥 지나가는 지점
    keysBelow : 이 노드 아래(자기 포함)에 있는 키 개수

같은 키 집합 { romane, romanus, romulus } 을 두 방식으로 그리면

[A] 일반 trie (09번) : 간선 하나 = 문자 하나
    root - r - o - m - a - n - e *          romane
                   |       |
                   |       +-- u - s *      romanus
                   |
                   +-- u - l - u - s *      romulus
    노드 12개 (root 제외).  * = 키의 끝 (09번은 boolean end)

[B] radix trie : 간선 하나 = 문자열 조각
    root -- "rom" -- "an" -- "e" *          romane
               |       |
               |       +---- "us" *         romanus
               |
               +---- "ulus" *               romulus
    노드 5개.  * = value != null
    자식이 하나뿐인 통과점(o, m, a, l, u ...)이 전부 간선 글자로 접혀 들어갔다

children 의 키가 "첫 글자" 하나인 이유
    한 노드의 자식 edge 들은 서로 첫 글자가 다르다
    (같으면 그만큼이 공통 접두사라서 이미 합쳐져 있었을 것이다)
    그래서 첫 글자 하나로 갈 자식이 유일하게 정해진다 -> 분기 O(1)
```

### 동작 — 삽입

```
put 은 key 를 pos 만큼 소비하며 내려가다가, 간선과 어긋나는 지점에서 네 갈래로 갈린다
commonPrefixLength(child.edge, key, pos) = 간선 조각과 남은 키가 몇 글자까지 같은가

[1] 첫 글자에 해당하는 자식이 아예 없다 -> 잎 하나를 새로 단다 (분할 없음)
    put("romane") on 빈 트리
        root         ->        root
                                 |
                              "romane" *
        children.put('r', new Node(key.substring(pos)))   남은 키를 통째로 간선에 적는다

[2] 간선 중간에서 갈라진다 -> 간선을 잘라 중간 노드가 하나 생긴다 (분할)
    put("romanus")
        root                        root
          |                           |
      "romane" *        ->         "roman"          <- 새로 생긴 중간 노드 (value 없음)
                                    /     \
                                 "e" *     "us" *
        common = 5 ("roman" 까지 같다).  기존 edge 를 "roman" + "e" 로 쪼개고
        중간 노드 아래에 옛 자식("e")과 새 잎("us")을 나란히 단다
        두 자식의 첫 글자가 'e' 와 'u' 로 다르다는 것이 분할이 성립하는 조건이다

[3] 기존 간선이 새 키의 접두사다 -> 분할 없이 그 간선을 통째로 지나 더 내려간다
    common == child.edge.length()
        "roman" -- "e" *      ->   "roman" -- "e" * -- "sque" *
    put("romanesque") : "roman" 도 "e" 도 전부 소비하고 그 아래에서 [1] 로 이어진다

[4] 새 키가 기존 간선의 중간에서 끝난다 -> 분할만 하고 잎은 안 만든다
    put("rom")
        root                        root
          |                           |
       "roman"          ->         "rom" *          <- 중간 노드가 값을 받는다
        /     \                       |
     "e" *     "us" *               "an"
                                    /    \
                                 "e" *    "us" *

새 키일 때만 지나가는 길의 keysBelow 를 1씩 올린다 (덮어쓰기는 개수가 안 변한다)
비용 : 내려가는 깊이가 아니라 키 길이에 묶인다. O(k), k = 키 길이. 노드 수와 무관
```

### 동작 — 조회

```
get("romanus") : 간선 조각을 "통째로" 맞대어 보며 내려간다
    pos  0        3        5        7
         r o m    a n      u s
    root --"rom"--> ( ) --"an"--> ( ) --"us"--> ( ) *
          |          |            |
          key.startsWith(child.edge, pos) 가 true 면 pos += edge.length()
    pos == key.length() 에서 멈추고 그 노드의 value 를 돌려준다 (null 이면 키가 아니다)

    조각이 한 글자라도 어긋나면 그 자리에서 null
        get("romans") : "an" 까지 왔지만 남은 "s" 로 시작하는 자식이 없다 -> null
    비교 횟수는 노드 수가 아니라 키 길이로 묶인다. O(k)

접두사 조회 : 접두사가 간선 "중간" 에서 끝날 수 있다는 것이 일반 trie 와 다른 점
    keysWithPrefix("roma")
        root --"rom"--> ( )    여기서 접두사에 남은 것은 "a" 한 글자뿐인데
                          |    자식 간선은 "an" 으로 더 길다
                          +--> "an" 이 "a" 로 시작하는가? yes -> 그 자식을 시작점으로 삼고
                               path 에는 "an" 전체를 붙인다 ("rom" + "an" = "roman")
        시작점 아래를 DFS 로 훑으며 value != null 인 노드의 path 를 모은다 (collect)

    countWithPrefix 는 훑지 않는다. 시작점의 keysBelow 를 그대로 읽는다
        -> 결과가 몇 만 개든 O(접두사 길이)
```

### 동작 — 삭제

```
remove("romanus") : 지나가는 길의 keysBelow 를 1씩 내리며 내려간다
    [1] 어떤 자식의 keysBelow 가 0 이 되면 그 가지를 통째로 떼어낸다 (아래에 키가 없다)
    [2] 키의 끝에 도착했으면 value = null (자식이 있으면 통과점으로 남는다)
    두 경우 모두 마지막에 compress(부모) 를 부른다

compress : 값이 없고 자식이 하나만 남은 노드는 그 자식을 흡수한다 (재압축)
    before                          after
      root                           root
        |                              |
     "roman"           ->          "romane" *
      /     \
   "e" *     "us" *          "us" 가지를 떼고 나니 "roman" 은 값 없이 자식 하나뿐
                             edge = "roman" + "e",  value = 자식의 value
                             자식의 children 을 그대로 물려받는다

안 합치면 "간선 하나 = 최대한 긴 조각" 이라는 불변식이 깨진다
    -> 키 집합이 같은데도 삽입/삭제 순서에 따라 모양과 노드 수가 달라진다
root 는 합치지 않는다 (edge 가 "" 인 고정점이고, 위에 부모가 없다)

비용 : O(k)
```

### `필드`

- `Node<V> root` 역할:
- `Node.edge` (간선 라벨) 역할:
- `Node.children` (`TreeMap<Character, Node<V>>`) 역할 — 왜 첫 글자를 키로 쓰고 왜 TreeMap 인가:
- `Node.value` 역할:
- `int size` 역할:
- 압축 불변식 — "뿌리가 아닌 노드는 키이거나 갈림길이다":

### `static int commonPrefixLength(String edge, String s, int from)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `public V put(String key, V value)` (TODO)

- 하는 일:
- 논리(경우 셋 · 간선 쪼개기 · 자른 자리에 값을 놓을지):
- 비용(왜):

### `Node<V> findNode(String key)` (TODO)

- 하는 일:
- 논리(한 걸음이 한 글자가 아니라는 것):
- 비용(왜):

### `Node<V> prefixRoot(String prefix, StringBuilder path)` (TODO)

- 하는 일:
- 논리(findNode 보다 한 경우가 더 있는 이유 — 접두사가 간선 중간에서 끝날 수 있다 · path 가 접두사보다 길 수 있다):
- 비용(왜):

### `static <V> void collect(Node<V> node, StringBuilder path, List<String> out)` (TODO)

- 하는 일:
- 논리(붙였다 떼는 단위가 09번과 다른 것):
- 비용(왜):

### `public V remove(String key)` (TODO)

- 하는 일:
- 논리(뒷정리가 하나 더 있는 이유):
- 비용(왜):

### `void compress(Node<V> node)` (TODO)

- 하는 일:
- 논리(합칠 수 있는 조건 셋 · 하나라도 어기면 자료가 사라진다):
- 비용(왜):

### `public String longestPrefixOf(String s)` (TODO)

- 하는 일:
- 논리(`containsKey` 와의 차이 — "정확히 이것" 대 "이것을 덮는 가장 구체적인 규칙"):
- 비용(왜):

### `public V get(String key)` / `public boolean containsKey(String key)`

- 하는 일:
- 비용(왜):

### `public List<String> keysWithPrefix(String prefix)` / `public int countWithPrefix(String prefix)`

- 하는 일:
- 비용(왜):

### `public List<String> keys()` / `public int size()` / `public boolean isEmpty()` / `public void clear()`

- 하는 일:
- 비용(왜):

### `int nodeCount()`

- 하는 일:
- 논리(09번식 노드 수와 나란히 놓으면 무엇이 보이는가):
- 비용(왜):

## 구현 — RoutingTable (`src/main/java/com/datastructure/radix/RoutingTable.java`)

### 구조

```
RoutingTable 은 자기 자료구조가 없다. RadixTrie<String> 하나를 그대로 쓴다
바꾸는 것은 "키의 표현" 뿐이다 : IP 를 32 글자짜리 '0'/'1' 문자열로 편다 (toBits)

    10.1.0.0   ->  00001010 00000001 00000000 00000000     옥텟마다 8 글자, 총 32 글자
                   |<-10->| |<-1 ->|

    add("10.1.0.0/16", B) 는 앞 16 글자만 잘라 키로 넣는다
        routes.put("0000101000000001", "B")

    add("10.0.0.0/8",  A)  ->  키 "00001010"          (8 글자)
    add("0.0.0.0/0",   D)  ->  키 ""                  (0 글자 = root 자신이 값을 갖는다)

이 표현을 쓰는 이유
    "대역이 대역을 포함한다" 가 "비트 문자열이 비트 문자열의 접두사다" 와 같은 말이 된다
    10.0.0.0/8 이 10.1.0.0/16 을 포함  <->  "00001010" 이 "0000101000000001" 의 접두사
    포함 관계가 트라이의 조상-자손 관계로 그대로 옮겨진다
```

### 동작 — 최장 접두사 일치

```
lookup("10.1.2.3") : longestPrefixOf 로 "값이 있는, 가장 깊이 도달한 노드" 를 찾는다

    s = 00001010 00000001 00000010 00000011      toBits("10.1.2.3"), 32 글자

    root  * = D  (0.0.0.0/0)      best = 0    root 에 값이 있으니 일단 후보
      |
      | "00001010"    s 의 pos 0 부터 조각이 맞는다 -> pos = 8
      v
     ( )  * = A  (10.0.0.0/8)     best = 8    더 깊고 값이 있다 -> 후보 갱신
      |
      | "00000001"    s 의 pos 8 부터 조각이 맞는다 -> pos = 16
      v
     ( )  * = B  (10.1.0.0/16)    best = 16   후보 갱신
      |
      x   s.charAt(16) 으로 시작하는 자식이 없다 -> 멈춘다

    답 = s.substring(0, best) = "0000101000000001" -> routes.get -> B

    "가장 깊이 도달한, 값이 있는 노드" = 가장 긴 일치 접두사 = longest prefix match
    더 깊은 노드일수록 더 긴 비트 접두사 = 더 좁은 대역이므로, 깊이가 곧 우선순위다

    lookup("10.9.0.1") 이면 s = 00001010 00001001 ...
        pos 8 에서 자식 간선 "00000001" 과 s[8..16) = "00001001" 이 어긋난다
        -> 더 못 내려가고 best = 8 에 머문다 -> A (덜 구체적인 대역으로 떨어진다)

    값 없는 통과점(분할로 생긴 중간 노드)은 후보가 되지 않는다
        경로가 갈라지는 자리일 뿐 등록된 대역이 아니다 -> value == null 이면 best 를 안 건드린다
    일치하는 대역이 하나도 없고 기본 경로도 없으면 best = -1 -> null

비용 : 키 길이가 32 로 고정 -> O(32), 등록된 경로 수와 무관
```

### `필드`

- `RadixTrie<String> routes` 역할:
- 주소를 32비트 이진 문자열로 눕히는 이유 (문자가 '0'/'1' 둘뿐 = 이진 트라이):

### `public void add(String cidr, String nextHop)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `public String lookup(String ip)` (TODO)

- 하는 일:
- 논리(왜 `longestPrefixOf` 한 번이면 끝인가 — 해시맵이면 33번 조회):
- 비용(왜):

### `static String toBits(String ip)` (TODO)

- 하는 일:
- 논리(옥텟을 8자리로 채워야 하는 이유 · 앞자리 0 을 거부하는 이유):
- 비용(왜):

### `public int size()`

- 하는 일:
- 비용(왜):

## 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| 09번 트라이 (한 글자 = 한 노드) | | | |
| RadixTrie (간선에 문자열 조각) | | | |
| HashMap (정확 일치만) | | | |
| RoutingTable (이진 트라이 응용) | | | |

## 문제 — RadixTrieProblems (`src/main/java/com/datastructure/radix/RadixTrieProblems.java`)

### 문제 1. 가장 긴 공통 접두사 — `static String longestCommonPrefix(String[] words)`

> 문제 설명: 주어진 단어들의 가장 긴 공통 접두사를 구한다.
> words 가 비었거나 null 이면 `""`. 공통 접두사가 없으면 `""`.
> 09번에서는 뿌리부터 한 글자씩 내려가며 갈림길을 찾아야 했다.
> 자식이 2개 이상이거나 그 노드가 단어이면 멈추는 식이었다.
> 여기서는 그 사슬이 이미 간선 하나로 눌려 있다.

- 내 접근:
- 논리:
- 비용(왜):

### 문제 2. 자동완성 — `static List<String> autocomplete(RadixTrie<String> trie, String prefix, int k)`

> 문제 설명: 접두사로 시작하는 키를 사전순 앞에서 k 개 돌려준다.
> k 개보다 적으면 있는 만큼. k 가 0 이하면 빈 리스트.
> 여기 시간 제한이 있다. 접두사에 10만 개가 걸려 있는데 k 가 10 인 질의를 반복한다.
> `trie.keysWithPrefix(prefix).subList(0, k)` 는 답은 맞지만 매번 10만 개를 다 모은다.
> `RadixTrie` 를 구체 타입으로 받는 이유가 09번과 같다 — 중간에 멈추려면 노드를 봐야 한다.
> 인터페이스가 주는 것만으로는 이 문제를 풀 수 없다. 그것도 정보다.
> 생각할 것: 시작 경로가 prefix 가 아닐 수 있다.

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

- README: `/home/jun/project/myway/data-structure/20-radix-trie/README.md`
- 구현: `/home/jun/project/myway/data-structure/20-radix-trie/src/main/java/com/datastructure/radix/`
- 테스트: `/home/jun/project/myway/data-structure/20-radix-trie/src/test/java/com/datastructure/radix/`
- 정답 구현: `/home/jun/project/myway/data-structure/20-radix-trie/impl/`
