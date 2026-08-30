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
