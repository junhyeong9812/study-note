# data-structure/09-trie — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 계약 — Trie (`src/main/java/com/datastructure/trie/Trie.java`)

- `void insert(String word)`
- `boolean contains(String word)`
- `boolean startsWith(String prefix)`
- `boolean remove(String word)`
- `int size()`
- `boolean isEmpty()`
- `void clear()`
- `List<String> keysWithPrefix(String prefix)`
- `int countWithPrefix(String prefix)`

## 구현 — MapTrie (`src/main/java/com/datastructure/trie/MapTrie.java`)

<!-- 메서드마다 내 언어로. 복잡도는 "왜 그런지"까지. -->

### `필드`

- `static final class Node` — 역할:
- `Map<Character, Node> children` (Node, `new TreeMap<>()`) — 역할:
- `boolean end` (Node) — 역할:
- `int wordsBelow` (Node) — 역할:
- `Node root` — 역할:

### `void insert(String word)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `boolean remove(String word)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `Node findNode(String s)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `static void collect(Node node, StringBuilder path, List<String> out)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `int countWithPrefix(String prefix)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `List<String> keysWithPrefix(String prefix)`

- 하는 일:
- 논리:
- 비용(왜):

### `boolean contains(String word)`

- 하는 일:
- 논리:
- 비용(왜):

### `boolean startsWith(String prefix)`

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

## 구현 — ArrayTrie (`src/main/java/com/datastructure/trie/ArrayTrie.java`)

### `필드`

- `static final int ALPHABET = 26` — 역할:
- `static final class Node` — 역할:
- `Node[] children` (Node, `new Node[ALPHABET]`) — 역할:
- `boolean end` (Node) — 역할:
- `int wordsBelow` (Node) — 역할:
- `Node root` — 역할:

### `static int indexOf(char c)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `boolean remove(String word)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `static void collect(Node node, StringBuilder path, List<String> out)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `void insert(String word)`

- 하는 일:
- 논리:
- 비용(왜):

### `List<String> keysWithPrefix(String prefix)`

- 하는 일:
- 논리:
- 비용(왜):

### `boolean contains(String word)`

- 하는 일:
- 논리:
- 비용(왜):

### `boolean startsWith(String prefix)`

- 하는 일:
- 논리:
- 비용(왜):

### `int countWithPrefix(String prefix)`

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

## 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| MapTrie | | | |
| ArrayTrie | | | |

## 구현 — WordDictionary (`src/main/java/com/datastructure/trie/WordDictionary.java`)

### `필드`

- `private final MapTrie trie` — 역할:

### `void addWord(String word)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `int size()`

- 하는 일:
- 논리:
- 비용(왜):

### `boolean search(String pattern)`

- 하는 일:
- 논리:
- 비용(왜):

### `private static boolean search(MapTrie.Node node, String pattern, int i)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

## 문제 — TrieProblems (`src/main/java/com/datastructure/trie/TrieProblems.java`)

### 문제 1. 주어진 단어들의 가장 긴 공통 접두사

> 문제 설명: `words` 가 비었으면 `""`. 공통 접두사가 없으면 `""`.
> 흔한 풀이는 첫 단어를 기준으로 나머지와 한 글자씩 비교하는 것이고, 그게 더 짧다.
> 여기서 트라이로 푸는 이유는 "공통 접두사"가 트라이에서 무엇인지 눈으로 보기 위해서다.
> 생각할 것 — 전부 넣고 뿌리에서 내려간다. 언제 멈추는가. 두 조건이다.
> 자식이 2개 이상이면 거기서 갈라진다. 공통이 아니다. /
> 자식이 하나여도 지금 노드가 `end` 면 멈춘다. 그 단어 자체가 더 못 간다.
> `["a", "ab"]` 의 답은 `"a"` 다. 이 조건을 빼면 `"ab"` 가 나온다.
> 즉 공통 접두사는 **뿌리에서 첫 갈림길(또는 첫 단어 끝)까지의 경로**다.
> 시그니처: `static String longestCommonPrefix(String[] words)`

- 내 접근:
- 논리:
- 비용(왜):

### 문제 2. 접두사로 시작하는 단어를 사전순 앞에서 k 개

> 문제 설명: k 개보다 적으면 있는 만큼. k 가 0 이하면 빈 리스트.
> 여기 시간 제한이 있다. 접두사에 20만 개가 걸려 있는데 k 가 10 인 질의를 반복한다.
> `trie.keysWithPrefix(prefix).subList(0, k)` 는 답은 맞지만 매번 20만 개를 다 모은다.
> `MapTrie` 를 구체 타입으로 받는 이유가 이것이다. 중간에 멈추려면 노드를 봐야 한다.
> 인터페이스가 주는 것만으로는 이 문제를 풀 수 없다. 그것도 정보다.
> 생각할 것 — `collect` 를 하되 k 개가 차면 그만둔다. 개수를 확인할 자리가 셋이다.
> 재귀 진입부, 단어를 담은 직후, 자식에서 돌아온 직후. 셋 중 하나만 있어도 답은 맞다.
> 나머지는 헛걸음을 줄일 뿐이다. 진짜 요점은 **아예 확인하지 않고 전부 모은 뒤
> 앞에서 k 개를 자르는 것**과의 차이다. 그것도 답은 맞다. 다만 접두사에 10만 개가 걸려 있으면
> 질의마다 10만 걸음이다. 성능 테스트가 그 차이를 잡는다.
> 시그니처: `static List<String> autocomplete(MapTrie trie, String prefix, int k)`

- 내 접근:
- 논리:
- 비용(왜):

### 문제 3. 문자열 s 의 서로 다른 부분 문자열 개수

> 문제 설명: 빈 문자열은 세지 않는다.
> `"abc"` 면 a, ab, abc, b, bc, c 로 6개. `"aaa"` 면 a, aa, aaa 로 3개. (같은 것은 한 번만)
> 모든 접미사를 트라이에 넣으면 노드 하나가 부분 문자열 하나다.
> 접미사 `"abc"`, `"bc"`, `"c"` 를 넣고 만들어진 노드를 세면 그게 답이다.
> 중복 제거를 따로 할 필요가 없다. 같은 부분 문자열은 같은 경로라 노드를 다시 안 만든다.
> 여기서는 `Trie` 대신 `MapTrie.Node` 를 직접 써도 된다.
> `end` 도 `wordsBelow` 도 필요 없고 만들어진 노드 수만 세면 되기 때문이다.
> 생각할 것 — i 를 0 부터 `s.length()-1` 까지 옮기며 `s[i..]` 를 뿌리부터 밀어 넣고,
> **새 노드를 만들 때마다** 1 을 센다. s 가 null 이거나 비었으면 0.
> 이 풀이의 한계도 같이 보라. 길이 n 이면 노드가 최대 n(n+1)/2 개다.
> n 이 10만이면 50억 개라 아예 못 만든다. 접미사 배열과 접미사 오토마타가 존재하는 이유다.
> 시그니처: `static int countDistinctSubstrings(String s)`

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

- 원본 README: `/home/jun/project/myway/data-structure/09-trie/README.md`
- 구현: `/home/jun/project/myway/data-structure/09-trie/src/main/java/com/datastructure/trie/`
- 테스트: `/home/jun/project/myway/data-structure/09-trie/src/test/java/com/datastructure/trie/`
- 참고 구현: `/home/jun/project/myway/data-structure/09-trie/impl/`
