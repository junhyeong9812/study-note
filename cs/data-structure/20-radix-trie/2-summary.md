# data-structure/20-radix-trie — 정리 (힌트)

## 해결하는 문제

09번 트라이는 한 글자에 노드 하나다. `internationalization`을 넣으면 노드가 20개인데 그중 갈림길은 하나도 없다.
자식이 하나뿐인 노드가 알려주는 "다음 글자"는 문자열에 이미 적혀 있다 — 노드로 다시 들고 있을 이유가 없다.

```text
09번 트라이 (한 글자 = 노드 하나)          압축 트라이 (외길 = 간선 조각 하나)
root -r-( )-o-( )-m-( )-a-( )-n-( )-e-( )*   root --"roman"--( ) --"e"--( )*
                            \                            \
                             u-( )-s-( )*                 "us"--( )*
노드 8개, 갈림길은 'n' 뒤 하나뿐          노드 3개 — 갈림길과 키 끝만 남는다
```

압축 트라이는 자식이 하나뿐인 사슬을 간선 하나에 문자열 조각으로 눌러 담는다. 노드 수는 최대 2n-1(n = 키 수)로 묶이고, 걸음 수도 "갈림길 수"만큼으로 준다.
그 대가로 삽입은 간선을 쪼개고(split), 삭제는 다시 합쳐야(compress) 한다.

- 쉬운 예: 산길 팻말 — 한 걸음마다 세우지 않고 갈림길에만 세운다. 외길은 팻말 하나에 "이 길을 따라 300m"라고 적는다.
- 똑같은 구조다: 이 노트의 `RadixTrie`는 `Node.edge`에 조각을 적고, `children`은 자식 조각의 첫 글자 하나로만 갈라진다.
- 실무 예: 라우터가 목적지 IP를 덮는 가장 좁은 대역을 고르는 최장 접두사 일치 — `RoutingTable`이 IP를 32글자 비트 문자열로 펴서 같은 트라이에 얹는다.
  - *최장 접두사 일치(longest prefix match)*: 주소를 덮는 등록 대역 중 가장 긴(좁은) 것을 고르는 규칙. "정확히 이 키"가 아니라 "이 키를 덮는 가장 구체적인 규칙"을 묻는다.

### 한눈에 — 쉽게 말하면

**비유: 갈림길에만 세우는 이정표.** 산길에 팻말을 세운다고 하자. 한 글자짜리 팻말을 한 걸음마다 세우면(일반 트라이) 팻말이 너무 많다. 갈림길이 없는 외길 구간은 팻말 하나에 "romane 방면 3km"처럼 길게 적어 버리면, 팻말 수가 갈림길 수만큼으로 확 준다.

**radix trie가 똑같은 구조다.** 문자 하나짜리 간선이 줄줄이 이어진 외길을 문자열 조각 하나로 눌러 담는다. 실무에선 IDE가 폴더 안에 폴더 하나만 있을 때 `a/b/c`로 합쳐 보여주는 것, 그리고 인터넷 라우터의 IP 주소 찾기(최장 접두사 일치)가 이 구조다.

- 트라이(9장)는 "간선 하나 = 문자 하나". 공통 앞부분(접두사)을 공유해 접두사 검색이 빠르다.
  - *접두사(prefix)*: 문자열의 앞부분. "rom"은 "romane"의 접두사다.
- radix trie는 "간선 하나 = 문자열 조각". 자식이 하나뿐인 통과점들을 간선 글자로 접어 넣는다.
- 노드 수가 확 줄어 메모리가 절약되고, 걸음 수도 "갈림길 수"만큼으로 준다. 비용은 여전히 키 길이 O(k).
- 지울 때는 반대로, 갈림길이 아니게 된 노드를 다시 간선으로 합쳐(compress) 모양을 유지한다.

```text
  일반 트라이:  root -r-> ( ) -o-> ( ) -m-> ( ) -a-> ( ) -n-> ( )    노드 5개
  radix trie:   root --"roman"--> ( )                                노드 1개
                (갈림길 없는 외길이 팻말 하나로 접혔다)
```

## 동작·원리

### 전체 흐름

```text
[1] 09번 트라이의 낭비                    [2] 규칙 하나 — "뿌리가 아닌 노드는 키이거나 갈림길이다"
    r-o-m-a-n : 외길 노드 5개                  둘 다 아닌 노드는 부모에 흡수된다
    자식 하나뿐인 노드 = 정보가 없다            -> 간선 하나 = 문자열 조각 (edge)
              |                                          |
              v                                          v
[3] 삽입 = 간선 쪼개기 (split)            [4] 조회 = 조각을 통째로 맞대기
    commonPrefixLength(edge, key, pos)         get : startsWith(edge, pos) 로 pos 전진, O(k)
    자식 없음   -> 잎을 단다                    keysWithPrefix : 접두사가 간선 "중간"에서 끝나도
    중간에 어긋남 -> 간선을 자르고 중간 노드      그 자식을 시작점으로 잡고 DFS
    간선 = 키의 접두사 -> 통과해 더 내려감        countWithPrefix : keysBelow 만 읽는다
    키가 간선 중간에서 끝남 -> 자른 자리에 값     longestPrefixOf : 값 있는 가장 깊은 노드
              |                                          |
              v                                          v
[5] 삭제 = 끊고 다시 합치기 (compress)    [6] 대가
    keysBelow 가 0 인 가지를 떼고               노드 수는 준다, 글자 수는 같다
    값 없고 자식 하나인 노드는 자식을 흡수        노드당 일(문자열 비교·substring)은 는다
    안 합치면 09번으로 조용히 퇴화               짧은 키(a~z 26개)에는 이득이 0
```

- [1] 트라이의 외길 노드는 "다음 글자"만 알려주는데, 그 글자는 키에 이미 있다. 여기서 출발한다.
- [2] 규칙 하나가 구조 전부를 정한다 — 노드는 키의 끝이거나 갈림길이어야 하고, 둘 다 아니면 부모 간선에 눌러 담는다.
  - *불변식(invariant)*: 어떤 조작이 끝나도 항상 참이어야 하는 규칙. 삽입·삭제가 이 규칙을 지키는 것이 이 챕터의 본체다.
- [3] 삽입은 간선 조각과 남은 키가 "몇 글자까지 같은가"에 따라 네 갈래로 갈린다. 중간에서 어긋나면 간선을 두 토막으로 자르고 그 자리에 중간 노드를 만든다.
  - *분할(split)*: 간선 `"romane"`을 `"roman"` + `"e"`로 자르고, 새 잎 `"us"`를 옆에 다는 일. 09번에는 없던 연산이다.
- [4] 조회는 한 걸음이 한 글자가 아니라 조각 하나다. 비용은 노드 수가 아니라 키 길이 O(k)에 묶인다. 접두사가 간선 중간에서 끝날 수 있다는 것이 09번에 없던 함정이다.
- [5] 삭제는 지우기보다 뒷정리가 핵심이다 — 값 없이 자식 하나만 남은 노드를 자식과 합쳐 "간선 = 최대한 긴 조각"을 되살린다. 안 합쳐도 답은 다 맞아서 계약 테스트가 못 잡는다(정답 9번 참고).
- [6] 줄어드는 것은 노드 개수이지 글자가 아니다. 간선 라벨의 글자를 다 더하면 09번의 노드 수와 같다.

### 계약 — PrefixMap (`src/main/java/com/datastructure/radix/PrefixMap.java`)

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

### 구현 — RadixTrie (`src/main/java/com/datastructure/radix/RadixTrie.java`)

<!-- 메서드마다 내 언어로. 복잡도는 "왜 그런지"까지. -->

#### 구조

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

#### 동작 — 삽입

**언제 쓰나**: 키를 넣을 때. 간선의 글자 조각과 남은 키를 맞대 보며 내려가다가, "어디까지 같은가"에 따라 네 경우로 갈린다. 아래 그림 [1]~[4]가 각 경우의 전 상태 → put → 후 상태다.

- *분할(split)*: 간선 중간에서 갈라져야 할 때 간선을 두 토막으로 자르고 그 자리에 중간 노드를 만드는 일.

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

#### 동작 — 조회

**언제 쓰나**: 키 하나를 찾거나(get), 어떤 접두사로 시작하는 키를 전부 모을 때(keysWithPrefix). 한 걸음이 "한 글자"가 아니라 "간선 조각 하나"라는 점이 일반 트라이와 다르다.

- *DFS(깊이 우선 탐색)*: 갈림길에서 한 가지를 끝까지 파고든 뒤 되돌아와 다음 가지로 가는 훑기 순서.

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

#### 동작 — 삭제

**언제 쓰나**: 키를 지울 때. 지우기 자체보다 뒷정리(compress)가 핵심이다 — "간선 하나 = 최대한 긴 조각"이라는 불변식을 되살려야 한다.

- *불변식*: 어떤 조작이 끝나도 항상 참이어야 하는 규칙. 여기선 "뿌리가 아닌 노드는 키이거나 갈림길이다".

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

#### `필드`

- `Node<V> root` 역할:
- `Node.edge` (간선 라벨) 역할:
- `Node.children` (`TreeMap<Character, Node<V>>`) 역할 — 왜 첫 글자를 키로 쓰고 왜 TreeMap 인가:
- `Node.value` 역할:
- `int size` 역할:
- 압축 불변식 — "뿌리가 아닌 노드는 키이거나 갈림길이다":

#### `static int commonPrefixLength(String edge, String s, int from)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

#### `public V put(String key, V value)` (TODO)

- 하는 일:
- 논리(경우 셋 · 간선 쪼개기 · 자른 자리에 값을 놓을지):
- 비용(왜):

#### `Node<V> findNode(String key)` (TODO)

- 하는 일:
- 논리(한 걸음이 한 글자가 아니라는 것):
- 비용(왜):

#### `Node<V> prefixRoot(String prefix, StringBuilder path)` (TODO)

- 하는 일:
- 논리(findNode 보다 한 경우가 더 있는 이유 — 접두사가 간선 중간에서 끝날 수 있다 · path 가 접두사보다 길 수 있다):
- 비용(왜):

#### `static <V> void collect(Node<V> node, StringBuilder path, List<String> out)` (TODO)

- 하는 일:
- 논리(붙였다 떼는 단위가 09번과 다른 것):
- 비용(왜):

#### `public V remove(String key)` (TODO)

- 하는 일:
- 논리(뒷정리가 하나 더 있는 이유):
- 비용(왜):

#### `void compress(Node<V> node)` (TODO)

- 하는 일:
- 논리(합칠 수 있는 조건 셋 · 하나라도 어기면 자료가 사라진다):
- 비용(왜):

#### `public String longestPrefixOf(String s)` (TODO)

- 하는 일:
- 논리(`containsKey` 와의 차이 — "정확히 이것" 대 "이것을 덮는 가장 구체적인 규칙"):
- 비용(왜):

#### `public V get(String key)` / `public boolean containsKey(String key)`

- 하는 일:
- 비용(왜):

#### `public List<String> keysWithPrefix(String prefix)` / `public int countWithPrefix(String prefix)`

- 하는 일:
- 비용(왜):

#### `public List<String> keys()` / `public int size()` / `public boolean isEmpty()` / `public void clear()`

- 하는 일:
- 비용(왜):

#### `int nodeCount()`

- 하는 일:
- 논리(09번식 노드 수와 나란히 놓으면 무엇이 보이는가):
- 비용(왜):

### 구현 — RoutingTable (`src/main/java/com/datastructure/radix/RoutingTable.java`)

#### 구조

먼저 알아야 할 것 세 줄:

- *IP 주소*: 인터넷에서 컴퓨터의 주소. `10.1.2.3`처럼 0~255짜리 수(옥텟) 4개 = 32비트.
- *CIDR 표기 `10.1.0.0/16`*: "앞 16비트가 같은 주소 전부"라는 대역(범위) 표기. /8이 /16보다 넓은 대역이다.
- *라우팅*: 목적지 IP를 보고 "다음엔 어느 쪽으로 보낼까(nextHop)"를 정하는 일. 여러 대역이 겹치면 가장 좁은(긴) 대역이 이긴다.

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

#### 동작 — 최장 접두사 일치

**언제 쓰나**: 패킷의 목적지 IP로 "이 주소를 덮는 가장 구체적인(좁은) 대역"을 찾을 때. get의 "정확히 이 키"가 아니라 "이 문자열을 덮는 가장 긴 등록 접두사"를 찾는다는 점이 다르다. 아래 그림이 내려가며 후보(best)를 갱신하는 전 과정이다.

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

#### `필드`

- `RadixTrie<String> routes` 역할:
- 주소를 32비트 이진 문자열로 눕히는 이유 (문자가 '0'/'1' 둘뿐 = 이진 트라이):

#### `public void add(String cidr, String nextHop)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

#### `public String lookup(String ip)` (TODO)

- 하는 일:
- 논리(왜 `longestPrefixOf` 한 번이면 끝인가 — 해시맵이면 33번 조회):
- 비용(왜):

#### `static String toBits(String ip)` (TODO)

- 하는 일:
- 논리(옥텟을 8자리로 채워야 하는 이유 · 앞자리 0 을 거부하는 이유):
- 비용(왜):

#### `public int size()`

- 하는 일:
- 비용(왜):

## 쓰이는 자료구조·알고리즘

- **리눅스 커널 IPv4 라우팅 테이블(`net/ipv4/fib_trie.c`)** — 목적지 IP의 최장 접두사 일치를 LC-trie(경로 압축 + 레벨 압축 트라이, Nilsson–Karlsson)로 한다. 이 노트의 `RoutingTable`은 그중 경로 압축만 한 축소판이다.
- **HTTP 라우터** — `/users/:id/posts` 같은 경로 패턴을 radix tree에 넣고 요청 경로를 한 번 내려가며 매칭한다. Go의 httprouter(README: "compact prefix tree (or just Radix tree)")와 그 트리를 가져온 gin이 이 방식이다. 간선은 문자 단위 조각이고, `:id` 같은 파라미터 자리만 세그먼트 단위로 맞춘다.
- **etcd의 접두사 조회** — `etcdctl get --prefix`는 `keysWithPrefix`와 같은 질문이다. 다만 etcd는 트라이가 아니라 정렬된 인덱스(메모리 B-tree + bbolt B+tree)에서 `[prefix, prefix의 다음 키)` 범위를 스캔해 답한다 — 같은 질문을 다른 구조로 푸는 예다. Redis는 radix tree(`rax`)를 Streams 등 내부 구조에 쓴다.
- **IDE의 폴더 접기** — 폴더 안에 폴더 하나만 있을 때 `a/b/c`로 합쳐 보여주는 것은 "자식 하나뿐인 노드를 부모에 흡수"하는 compress와 같은 발상이다.
- **자동완성(autocomplete)** — 입력한 접두사 아래를 사전순으로 k개만 걷는다. 문제 2가 그 구조이고, 09번과 같은 함정(전부 모은 뒤 자르기)이 있다.
- **다른 챕터의 재료** — [09-trie](../09-trie/2-summary.md)의 압축판이고, [21-suffix-array](../21-suffix-array/2-summary.md)는 "모든 접미사를 트라이에 넣으면 노드가 n(n+1)/2개"라는 한계를 배열 하나로 푼다.

## 적용 — 풀어나가는 법

압축 트라이 문제는 "키를 어떤 문자열로 펼지"를 먼저 정하는 데서 갈린다.
순서: ① 포함 관계를 "비트/문자 접두사 관계"로 옮길 수 있는지 본다(`10.0.0.0/8` ⊃ `10.1.0.0/16` ↔ `"00001010"`이 `"0000101000000001"`의 접두사) → ② 묻는 것이 정확 일치인지(`get`), 덮는 규칙인지(`longestPrefixOf`), 아래 전부인지(`keysWithPrefix`) 고른다 → ③ 결과가 클 때는 훑지 않고 `keysBelow`를 읽거나 k개에서 멈춘다 → ④ 삭제가 있으면 compress를 구조 테스트로 못 박는다(계약 테스트는 못 잡는다).
아래 두 문제와 `RoutingTable`이 이 순서로 풀린다.

### 문제 — 이 챕터가 시키는 것

09번 트라이는 한 글자에 노드 하나라 `internationalization` 을 넣으면 노드가 20개인데 그중 갈림길이 하나도 없다.
자식이 하나뿐인 노드가 말해주는 다음 글자는 문자열에 이미 있으므로, 그 사슬을 간선 하나에 문자열 조각으로 눌러 담는 것이 압축 트라이다.
규칙 하나("뿌리가 아닌 노드는 키이거나 갈림길이다")가 구조 전부를 결정하고, 그 대가로 삽입이 간선을 쪼개고 삭제가 다시 합쳐야 한다.
`RadixTrieTest.java` 를 따라친 뒤 TODO 를 채운다(처음에는 94개 중 92개가 실패한다).

- `RadixTrie` 의 TODO 8개 — `commonPrefixLength` · `put`(제일 크다) · `findNode` · `prefixRoot` · `collect` · `remove` · `compress` · `longestPrefixOf`
- `RoutingTable` 의 TODO 3개 — `add` · `lookup` · `toBits`
- `RadixTrieProblems` 의 TODO 2개 — `longestCommonPrefix` · `autocomplete`
- 순서는 `RadixTrie` → `RoutingTable` → `RadixTrieProblems`. 통과하는 2개는 미리 채워둔 null 검사만 보는 테스트다.
- 응용으로 따져볼 것: 간선 쪼개기의 세 경우와 "자른 자리에 값을 둘지"(94개 중 18개가 갈린다) · 삭제 후 병합을 계약 테스트가 못 잡는다는 발견 · 접두사가 간선 중간에서 끝나는 경우의 경로 관리 · 문제 1이 09번과의 대비(읽는 자리가 바뀐 것이지 공짜가 아니다) · 문제 2의 전부 모으고 자르기 함정 · 앞자리 0 을 거부하는 이유

아래 서머리는 이 문제(README)를 분석·정리한 것이다.

### 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| 09번 트라이 (한 글자 = 한 노드) | | | |
| RadixTrie (간선에 문자열 조각) | | | |
| HashMap (정확 일치만) | | | |
| RoutingTable (이진 트라이 응용) | | | |

### 문제 — RadixTrieProblems (`src/main/java/com/datastructure/radix/RadixTrieProblems.java`)

#### 문제 1. 가장 긴 공통 접두사 — `static String longestCommonPrefix(String[] words)`

> 문제 설명: 주어진 단어들의 가장 긴 공통 접두사를 구한다.
> words 가 비었거나 null 이면 `""`. 공통 접두사가 없으면 `""`.
> 09번에서는 뿌리부터 한 글자씩 내려가며 갈림길을 찾아야 했다.
> 자식이 2개 이상이거나 그 노드가 단어이면 멈추는 식이었다.
> 여기서는 그 사슬이 이미 간선 하나로 눌려 있다.

- 내 접근:
- 논리:
- 비용(왜):

#### 문제 2. 자동완성 — `static List<String> autocomplete(RadixTrie<String> trie, String prefix, int k)`

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

## 장애 시나리오와 대처

**1. 호스트 비트가 남은 CIDR을 넣어 대역이 조용히 겹침**

- 현상: `add("10.1.2.3/16", "B")`처럼 주소 부분에 대역 밖 비트가 남은 CIDR을 등록해도 에러가 없다.
- 보이는 형태: 나중에 `add("10.1.0.0/16", "C")`를 하면 `B`가 말없이 `C`로 덮인다. `size()`는 1이고, 어느 쪽 nextHop이 살아 있는지는 등록 순서에 달린다.
- 원인: `add`는 `toBits(주소).substring(0, len)`으로 앞 `len`글자만 키로 쓴다. 뒤의 호스트 비트는 잘려 나가므로 `10.1.2.3/16`과 `10.1.0.0/16`은 같은 키 `"0000101000000001"`이다.
- 대처: 등록 전에 호스트 비트가 0인지(`주소 & ~마스크 == 0`) 검사해 거부하거나, 정규화한 CIDR을 로그에 남긴다. 예: Python `ipaddress.ip_network("10.1.2.3/16")`는 기본 strict 모드에서 `has host bits set`으로 거부한다. 라우터 설정 도구의 동작(거부 또는 자동 마스킹)은 제품마다 다르다 [?].

**2. 기본 경로 없이 운영하다 매칭 실패가 `null`로 새어 나감**

- 현상: 등록된 어느 대역에도 안 걸리는 주소를 `lookup`하면 `null`이 돌아온다.
- 보이는 형태: 호출자가 `null`을 그대로 다음 홉으로 쓰다가 `NullPointerException`, 또는 패킷이 조용히 버려진다(블랙홀).
- 원인: `longestPrefixOf`는 값 있는 가장 깊은 노드를 찾는데, 후보가 하나도 없으면 `best = -1`로 `null`이다. `0.0.0.0/0`(키 `""`, root 자신의 값)이 없으면 받아 줄 곳이 없다.
- 대처: 기본 경로 `0.0.0.0/0`을 반드시 먼저 등록하고, `lookup`의 `null`을 "드롭"으로 명시적으로 처리해 카운터를 올린다.

**3. 접두사가 간선 중간에서 끝나는 질의에 빈 결과가 나옴**

- 현상: `romane`만 있는데 `keysWithPrefix("rom")`이 빈 리스트를 준다. `get`·`containsKey`는 다 맞아서 눈치채기 어렵다.
- 보이는 형태: 자동완성 화면에 후보가 안 뜨는데 정확 검색은 된다. 계약 테스트에서 `keysWithPrefix`·`countWithPrefix` 쪽만 실패한다.
- 원인: 09번식으로 "접두사를 다 소비한 노드"를 찾으려 했다. 여기서는 접두사 남은 조각 `"rom"`보다 자식 간선 `"romane"`이 더 길어 멈출 노드가 없다 — `edge.startsWith(남은 접두사)`면 그 자식을 시작점으로 잡고 path에는 간선 전체를 붙여야 한다(정답 8번 참고).
- 대처: `prefixRoot`가 "간선이 남은 접두사로 시작하는가"를 별도 경우로 다루고, 테스트에 "접두사가 간선 중간에서 끝나는" 케이스를 명시적으로 둔다.

## 핵심 문장

- 자식이 하나뿐인 트라이 노드는 정보가 없다 — 다음 글자는 키에 이미 있다. 압축 트라이는 그 사슬을 간선 하나의 문자열 조각으로 눌러 담아 노드 수를 최대 2n-1로 묶는다.
- 규칙 하나가 전부다: 뿌리가 아닌 노드는 키이거나 갈림길이다. 삽입은 이 규칙을 지키려 간선을 쪼개고(split), 삭제는 다시 합친다(compress) — 안 합쳐도 답은 다 맞아서 밖에서는 안 보인다.
- 줄어드는 것은 노드 개수이지 글자가 아니다. 간선 라벨의 글자 합은 09번의 노드 수와 같고, 노드당 일은 오히려 는다 — 누를 사슬이 없는 짧은 키에는 이득이 0이다.
- `longestPrefixOf`는 "정확히 이 키"가 아니라 "이 키를 덮는 가장 구체적인 규칙"을 한 번의 하강으로 찾는다. IP를 32글자 비트 문자열로 펴면 대역의 포함 관계가 트라이의 조상-자손 관계가 되어 라우팅 테이블이 그대로 나온다.
- 접두사는 간선 중간에서 끝날 수 있다 — 09번에 없던 이 경우가 조회·수집의 함정이고, 걸음을 "글자"가 아니라 "조각"으로 세는 대가다.

## 관련 주제·근거

- 선행 — [09-trie](../09-trie/2-summary.md): 한 글자 = 노드 하나. 여기서 외길을 접은 것이 압축 트라이이고, 문제 1·2가 09번과 대비된다.
- 선행 — [05-hashmap](../05-hashmap/2-summary.md): 정확 일치만 되는 기준선. 최장 접두사 일치를 해시맵으로 하면 /32부터 /0까지 33번 조회다.
- 후속 — [21-suffix-array](../21-suffix-array/2-summary.md): 모든 접미사를 트라이에 넣을 수 없다는 09번의 숙제를 배열 하나로 푼다.
- 연결 — [31-consistent-hashing](../31-consistent-hashing/2-summary.md): "키를 덮는 가장 가까운 규칙"을 찾는 또 다른 구조(링 위의 시계 방향 첫 노드).
- 영역 표 — [data-structure/curriculum.md](../curriculum.md) `13-radix-trie` (선행 `12`, 원전 Morrison 1968 PATRICIA).
- myway 원본 — `/home/jun/project/myway/data-structure/20-radix-trie/` (README.md · impl/RadixTrie.java · impl/RoutingTable.java · impl/RadixTrieProblems.java).

### 관련 자료

<!-- 원본 문서·코드 경로. 기준 소스는 문서가 아니라 코드/원전이다. -->

- README: `/home/jun/project/myway/data-structure/20-radix-trie/README.md`
- 구현: `/home/jun/project/myway/data-structure/20-radix-trie/src/main/java/com/datastructure/radix/`
- 테스트: `/home/jun/project/myway/data-structure/20-radix-trie/src/test/java/com/datastructure/radix/`
- 정답 구현: `/home/jun/project/myway/data-structure/20-radix-trie/impl/`

### 용어 풀이

- **트라이(trie)**: 문자열을 한 글자씩 간선에 적어 내려가는 트리. 공통 앞부분을 공유해서 접두사 검색이 빠르다(9장).
- **radix trie(기수 트라이, 패트리샤 트라이)**: 자식이 하나뿐인 외길 구간을 문자열 조각 하나로 눌러 담은 압축 트라이.
- **접두사(prefix)**: 문자열의 앞부분. "rom"은 "romane"의 접두사.
- **간선(edge) / 간선 라벨**: 노드 사이 연결선 / 거기 적힌 문자열 조각. 이 구조에선 라벨이 여러 글자일 수 있다.
- **노드 / 잎 / 통과점**: 트리의 칸 / 자식 없는 끝 칸 / 값 없이 지나가기만 하는 칸(value == null).
- **분할(split)**: 간선 중간에서 갈라져야 할 때 간선을 두 토막으로 자르고 중간 노드를 만드는 일.
- **compress(재압축)**: 값이 없고 자식이 하나뿐인 노드를 그 자식과 합쳐 간선을 도로 길게 만드는 뒷정리. 삭제 후 불변식을 되살린다.
- **불변식**: 어떤 조작이 끝나도 항상 참이어야 하는 규칙. 여기선 "뿌리가 아닌 노드는 키이거나 갈림길이다".
- **keysBelow**: 각 노드가 "내 아래(나 포함)에 키가 몇 개인가"를 미리 세어 둔 수. 덕분에 개수 세기가 훑기 없이 O(접두사 길이).
- **DFS(깊이 우선 탐색)**: 한 가지를 끝까지 파고든 뒤 되돌아와 다음 가지로 가는 트리 훑기 순서.
- **TreeMap**: 키가 정렬된 순서로 유지되는 맵. 자식을 첫 글자 순으로 돌 수 있어 결과가 사전순이 된다.
- **O(k)**: 키 길이 k에 비례하는 시간. 트리에 키가 몇 개 있든 상관없다는 게 요점.
- **IP 주소 / 옥텟**: 인터넷 주소(32비트) / 그걸 8비트씩 끊은 0~255짜리 수 4개.
- **CIDR(`10.0.0.0/8`)**: "앞 8비트가 같은 주소 전부"라는 대역 표기. 숫자가 클수록 좁은 대역.
- **최장 접두사 일치(longest prefix match)**: 주소를 덮는 등록 대역 중 가장 긴(좁은) 것을 고르는 규칙. 라우터의 기본 동작.
- **nextHop**: 라우터가 패킷을 다음에 넘길 곳.
- **라우팅 테이블**: "이 대역이면 이쪽으로"의 목록. 여기선 radix trie 하나에 키 표현만 바꿔 얹었다.
- **자동완성(autocomplete)**: 입력한 접두사로 시작하는 후보를 몇 개 보여주는 기능. keysWithPrefix의 대표 쓰임.
- **인터페이스 / 구체 타입**: 약속(계약)만 보이는 껍데기 / 실제 구현 클래스. 탐색을 중간에 멈추려면 노드 내부가 보여야 해서 구체 타입을 받는다.
