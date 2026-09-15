# data-structure/09-trie — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.
> 2026-09-14: 쉽게 풀어쓴 확장(Claude 작성) — 한눈에 절·동작 그림·용어 풀이 추가.

## 한눈에 — 쉽게 말하면

**비유: 국어사전의 찾아가기.** "car"를 찾을 때 사전 전체를 뒤지지 않는다.\
ㄱㄴㄷ 순 색인처럼, c 섹션 → 그 안의 a → 그 안의 r로 **글자를 하나씩 따라 들어간다.**

**트라이가 바로 이 색인과 똑같은 구조다.** 갈림길마다 글자 하나로 갈라지는 나무다.

> **트라이(trie)** — 글자 하나가 갈림길 하나인 나무. 뿌리에서 어떤 노드까지의 경로가 곧 문자열이다.\
> 예: "cat"은 c → a → t 세 간선으로만 존재하고, 어디에도 "cat"이라는 글자 뭉치가 통째로 저장되지 않는다.

- 단어를 통째로 저장하지 않는다.\
  "cat"은 c → a → t 세 개의 길로만 존재한다.
- 그래서 cat, car, card는 "ca"까지의 길을 **셋이 나눠 쓴다** — 앞부분이 같으면 저장도 한 번만.

> **접두사(prefix)** — 단어의 앞부분.\
> 예: "ca"는 "cat", "car", "card" 셋 모두의 접두사이고, 트라이에서는 그 셋이 함께 지나는 길목이다.

- 찾는 비용은 단어 길이만큼(O(L)).\
  담긴 단어가 100만 개여도 상관없다.
- "ca로 시작하는 단어 전부/개수"를 바로 답한다 — 검색창 자동완성이 정확히 이 물건이다.

> **O(L)** — 비용이 단어 길이 L에만 비례한다는 뜻. 담긴 단어 수 n과 무관하다.\
> 예: "card"를 찾는 데 글자 4개만큼 내려가면 끝이라, 사전에 100만 단어가 있어도 걸음 수가 늘지 않는다.

```text
    (뿌리)
      +--c--+          "cat"과 "car"는
             +--a--+    c, a 길을 같이 쓰고
                    +--t   <- 여기서 "cat" 끝
                    +--r   <- 여기서 "car" 끝
```

## 문제 — 이 챕터가 시키는 것

원본 README는 이 박스를 "**05번 해시맵도 06번 BST도 못 하는 질문**을 다루는 박스"라고 소개한다.\
해시맵은 car와 card를 아예 다른 버킷에 넣어 "car로 시작하는 것 전부"가 불가능하고, BST는 범위로 흉내내지만 비교마다 문자열 전체를 훑는다.\
키를 통째로 저장하지 않고 **한 글자를 간선 하나로 삼아 경로가 곧 키가 되는** 구조를 직접 만들고, 같은 계약을 맵 자식(`MapTrie`)과 26칸 배열 자식(`ArrayTrie`) 두 가지로 구현해 메모리·순서의 거래를 숫자로 확인하는 것이 과제다.

과제 목록 — `src/main/java/com/datastructure/trie/`의 TODO:

- `MapTrie` — TODO 1(`insert`) · TODO 2(`remove` — 어디까지 끊어도 되는가) · TODO 3(`findNode`) · TODO 4(`collect` — 붙였다 떼기) · TODO 5(`countWithPrefix`)
- `ArrayTrie` — TODO 1(`indexOf` — 위아래 범위 밖 전부 -1) · TODO 2(`remove`) · TODO 3(`collect` — 자식 도는 방법만 다르다). 나머지는 이미 채워져 있다
- `WordDictionary` — TODO 1(`addWord`) · TODO 2(`search` — `.` 와일드카드, 되돌아오기)
- `TrieProblems` — TODO 1: 문제 1(`longestCommonPrefix`) · TODO 2: 문제 2(`autocomplete` — k개 차면 멈추기) · TODO 3: 문제 3(`countDistinctSubstrings`)

순서: `TrieContractTest.java`를 먼저 따라 친다(계약이 거기 있다) → `MapTrie` 5개 → `ArrayTrie` 3개 → `WordDictionary` 2개 → `TrieProblems` 3개.\
실행: `cd ~/project/myway/data-structure && ./run.sh 09` — README 기준 **130개 중 128개가 실패**한다(통과하는 2개는 미리 채워둔 null 검사 테스트).

아래 서머리는 이 문제(README)를 분석·정리한 것이다.

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

### 구조

```
MapTrie — 글자 하나가 간선이고, 뿌리에서 여기까지 온 "경로"가 곧 문자열이다
+---------------------------+
| root ---+                 |
+---------|-----------------+
          v
    (root)                    end=false   wordsBelow=4
      |
      +--'c'--> [c]           end=false   wordsBelow=3
      |           |
      |           +--'a'--> [ca]          end=false   wordsBelow=3
      |                       |
      |                       +--'t'--> [cat]    end=TRUE   wordsBelow=1
      |                       |
      |                       +--'r'--> [car]    end=TRUE   wordsBelow=2
      |                                    |
      |                                    +--'d'--> [card]  end=TRUE  wordsBelow=1
      |
      +--'d'--> [d]           end=false   wordsBelow=1
                  |
                  +--'o'--> [do]          end=false   wordsBelow=1
                              |
                              +--'g'--> [dog]   end=TRUE   wordsBelow=1

    담긴 단어 : cat, car, card, dog  (4개)

    Node 의 필드는 셋뿐이다
        children     TreeMap<Character, Node> — 글자별로 갈라지는 간선
        end          "여기서 끝나는 단어가 있다" 표시.
                     노드가 있다고 단어인 것은 아니다 — [ca] 는 노드는 있지만 end=false
        wordsBelow   이 노드를 지나는 단어 수 (= 이 경로를 접두사로 갖는 단어 수)
                     root 를 포함해 경로 위의 모든 노드에서 +1 된다

    노드 안에 키를 저장하지 않는다는 점이 해시맵/BST 와 결정적으로 다르다.
    "cat" 이라는 문자열은 어디에도 통째로 저장되어 있지 않고, c-a-t 세 간선으로만 존재한다.
    그래서 공통 접두사 "ca" 는 한 번만 만들어지고 cat, car, card 가 그 길을 나눠 쓴다

    size() 도 별도 필드가 아니라 root.wordsBelow 다
```

> **노드(node)** — 트리의 칸 하나. 트라이에서는 "뿌리에서 여기까지 온 글자들"을 대표한다.\
> 예: [ca] 노드는 "ca"라는 경로 자체이고, 그 아래 't' 간선을 타면 [cat] 노드가 된다.

> **루트/뿌리(root)** — 트리 맨 위의 출발 노드.\
> 예: 트라이의 루트는 아무 글자도 안 지난 상태, 즉 빈 문자열에 해당한다.

> **wordsBelow** — 그 노드를 지나는 단어 수(= 이 경로를 접두사로 갖는 단어 수).\
> 예: cat·car·card가 담겨 있으면 [ca].wordsBelow는 3이다.

### 동작 — 추가

**언제 쓰나** — 단어를 등록할 때(insert).\
"글자 따라 내려가며 없는 길만 새로 깐다".

```
insert(word) : 글자마다 내려가며 없으면 만들고, 지나는 노드마다 wordsBelow 를 올린다
    insert("card")  — cat, car 가 이미 있는 상태

    (0) contains("card") 면 아무것도 하지 않고 끝낸다
        (중복 삽입을 막지 않으면 같은 단어로 wordsBelow 가 두 번 올라 카운트가 망가진다)
    (1) root.wordsBelow++                         2 -> 3
    (2) 'c' : 있다 -> 내려가며 [c].wordsBelow++      2 -> 3
        'a' : 있다 -> 내려가며 [ca].wordsBelow++     2 -> 3
        'r' : 있다 -> 내려가며 [car].wordsBelow++    1 -> 2
        'd' : 없다 -> 새 노드를 만들고 [card].wordsBelow++   0 -> 1
    (3) [card].end = true

    before                              after
    (root)      wb=2                    (root)      wb=3
      'c' [c]   wb=2                      'c' [c]   wb=3
        'a' [ca]  wb=2                      'a' [ca]  wb=3
          't' [cat]  end wb=1                 't' [cat]  end wb=1
          'r' [car]  end wb=1                 'r' [car]  end wb=2
                                                'd' [card] end wb=1   <- 새 노드는 하나뿐

    비용은 O(L) — 단어 길이에만 비례한다. 이미 담긴 단어 수 n 과 무관하다.
    해시맵은 키 전체를 해싱해야 하고 BST 는 비교를 log n 번 해야 하지만,
    트라이는 글자를 하나씩 따라가기만 한다
```

**그림에서 일어난 일 (쉽게)**

1. "card"의 글자를 하나씩 따라 내려갔다.\
   c, a, r 길은 이미 있어서 그대로 지나가고, d 길만 새로 만들었다 — 새 노드는 딱 하나.
2. 지나간 모든 노드에서 wordsBelow(이 길을 지나는 단어 수)를 1씩 올렸다 — 나중에 "ca로 시작하는 단어 몇 개?"를 즉답하기 위한 장부다.
3. 마지막 노드에 end(여기서 끝나는 단어 있음) 도장을 찍었다.

> **end 표시** — "여기서 끝나는 단어가 있다"는 도장. 노드 존재 ≠ 단어 존재라서 필요하다.\
> 예: "ca"는 노드는 있지만 길목일 뿐이라 end=false 이고, "car"는 end=true 다.

4. 같은 단어를 두 번 넣으면 장부(wordsBelow)가 이중으로 올라가므로, 들어가기 전에 contains로 걸러낸다.

**비용** — 단어 길이 L만큼 = O(L).\
담긴 단어 수 n과 무관하다.

### 동작 — 탐색

**언제 쓰나** — "이 단어 있어?"(contains), "이걸로 시작하는 단어 있어/몇 개/전부?"(startsWith, countWithPrefix, keysWithPrefix).

```
findNode(s) : root 에서 글자마다 children 을 따라 내려간다. 중간에 길이 없으면 null

    contains("car")     -> 노드 도달 + end == true      -> 참
    contains("ca")      -> 노드 도달 + end == false     -> 거짓  (노드는 있지만 단어가 아니다)
    contains("cab")     -> 'b' 에서 길이 끊김 -> null   -> 거짓

    startsWith("ca")    -> 노드가 있고 wordsBelow > 0   -> 참
        노드 존재만으로 판정하지 않는 이유: 빈 트라이의 root 도 노드이기 때문이다

    countWithPrefix("ca") = findNode("ca").wordsBelow = 3        -> O(L)
        "ca" 로 시작하는 단어를 세면서 그 단어들을 한 번도 방문하지 않는다.
        삽입/삭제 때마다 미리 갱신해 둔 wordsBelow 를 그냥 읽는 것이다.
        (세어 보는 대신 세어 둔다 — 이 챕터의 핵심 아이디어)

    keysWithPrefix("ca") : findNode("ca") 부터 아래를 훑어 end 인 노드마다 경로를 담는다
        [ca] --'r'--> [car] end          =>  "car"
              |          |
              |          +--'d'--> [card] end   =>  "card"
              +--'t'--> [cat] end        =>  "cat"
        children 이 TreeMap 이라 순회 순서가 곧 사전순이다 -> 결과가 정렬되어 나온다
        경로 문자열은 StringBuilder 하나를 돌려 쓴다
            내려갈 때 append(글자),  돌아 나올 때 마지막 글자 삭제 (백트래킹)
        비용은 O(접두사 길이 + 결과 글자 수) — 전체를 훑고 거르는 것이 아니다
```

**그림에서 일어난 일 (쉽게)**

1. contains("car"): 글자 따라 내려가 도착한 노드에 end 도장이 있으면 단어다.\
   "ca"는 노드는 있지만 도장이 없어 거짓.
2. countWithPrefix("ca"): 도착한 노드의 장부(wordsBelow)를 **읽기만** 했다.\
   세어 보는 대신 넣을 때마다 세어 둔 것 — 이 챕터의 핵심 아이디어.
3. keysWithPrefix("ca"): 그 노드 아래만 훑어 end 도장이 찍힌 곳마다 지나온 글자들을 이어 단어로 만든다.\
   내려갈 때 글자를 붙이고 돌아 나올 때 떼는 것이 백트래킹이다.

> **백트래킹(backtracking)** — 갈림길을 깊이 들어가 보고, 되돌아 나올 때 가던 길 기록을 원래대로 되돌리는 것.\
> 예: 경로 문자열에 'r'을 붙여 [car]까지 갔다가, 돌아 나오면서 그 'r'을 다시 떼어 [ca] 상태로 만든다.

> **TreeMap** — 키를 정렬 순서로 관리하는 자바 맵.\
> 예: children이 TreeMap이라 자식을 순회하는 순서가 저절로 사전순이 되고, 결과 목록도 정렬되어 나온다.

**비용** — 접두사까지 O(L), 목록 만들기는 O(접두사 길이 + 결과 글자 수).\
트라이 전체 크기와 무관.

### 동작 — 삭제

**언제 쓰나** — 단어 하나를 지울 때(remove).\
남들과 같이 쓰는 길은 남기고, 나 혼자 쓰던 길만 끊는 게 요점이다.

```
remove(word) : 지나는 노드마다 wordsBelow 를 내리고, 0 이 되는 첫 노드에서 가지를 끊는다

[1] 나 혼자 쓰던 길이 있는 경우 — remove("card") (cat, car, card 가 있는 상태)
        root         wb 3 -> 2
        'c' [c]      wb 3 -> 2    0 아님 -> 계속
        'a' [ca]     wb 3 -> 2    0 아님 -> 계속
        'r' [car]    wb 2 -> 1    0 아님 -> 계속
        'd' [card]   wb 1 -> 0    0 이다 -> [car].children.remove('d') 하고 즉시 종료

    after   (root)      wb=2
              'c' [c]   wb=2
                'a' [ca]  wb=2
                  't' [cat] end wb=1
                  'r' [car] end wb=1        <- 'd' 로 가던 간선이 끊겼다
    참조 하나를 끊으면 그 아래 서브트리 전체가 한 번에 버려진다

[2] 남들과 나눠 쓰는 길만 지나는 경우 — remove("car") (cat, car, card 가 있는 상태)
        root         wb 3 -> 2
        'c' [c]      wb 3 -> 2    0 아님
        'a' [ca]     wb 3 -> 2    0 아님
        'r' [car]    wb 2 -> 1    0 아님 -> 루프가 끝까지 돈다
        루프를 다 돌았다 = 끊을 곳이 없었다 -> 마지막 노드의 end 만 끈다
        [car].end : true -> false        노드는 남는다 ("card" 가 이 길을 지나가야 하므로)

    정리 : 공유하는 단어가 사라지는 첫 지점에서 링크를 끊고, 그 위쪽은 카운트만 깎는다
```

**그림에서 일어난 일 (쉽게)**

1. 지나는 노드마다 장부(wordsBelow)를 1씩 깎으며 내려갔다.
2. 장부가 0이 된 첫 노드 = 이제 아무 단어도 안 지나는 길.\
   부모에서 그 연결 하나만 끊으면 그 아래 전체가 한꺼번에 버려진다(가비지 컬렉션이 회수).
3. 끝까지 내려가도 0이 안 나오면(남들이 아직 그 길을 쓰면) 아무것도 못 끊는다 — 마지막 노드의 end 도장만 지운다.\
   "car"를 지워도 "card"가 그 길로 다녀야 하니 노드는 남는다.

> **가지치기(pruning)** — 쓸모없어진 가지를 통째로 들어내는 것.\
> 예: [card]의 wordsBelow가 0이 되는 순간 [car]에서 'd' 링크 하나만 끊으면, 그 아래 서브트리가 전부 사라진다.

**비용** — 단어 길이만큼 한 번 내려가기 = O(L).

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

### 구조 — children 이 맵에서 배열로

```
ArrayTrie — Node 의 필드 이름도 규약(end, wordsBelow)도 MapTrie 와 같다.
            달라지는 것은 자식을 어디에 담느냐 하나다
    Node { Node[] children = new Node[ALPHABET];  boolean end;  int wordsBelow; }   ALPHABET = 26

    [ca] 노드 하나를 들여다보면 (자식은 'r' 과 't' 둘뿐)

        MapTrie                          ArrayTrie
        TreeMap<Character, Node>         idx   0    1   ...  17   ...  19   ...  25
        {  'r' -> [car],                     +----+----+     +----+    +----+    +----+
           't' -> [cat]  }                   |null|null| ... |  * | .. |  * | .. |null|
                                             +----+----+     +----+    +----+    +----+
        자식 2개만큼만 메모리                    a    b          r         t         z
                                             자식이 2개여도 26칸을 늘 잡는다

    글자에서 칸 번호로
        indexOf(c) = c - 'a'          'a' -> 0,  'b' -> 1,  ...  'z' -> 25
        범위를 벗어나면 -1 을 돌려준다 (양쪽 경계를 모두 검사한다)

    맞바꿈 표
                    MapTrie                          ArrayTrie
        자식 찾기   children.get(c)  트리 조회        children[i]  배열 인덱스 O(1)
        메모리      실제 자식 수만큼                  노드마다 26칸 고정
        사전순      TreeMap 순회가 곧 사전순          i = 0..25 로 도는 것이 곧 사전순
        자식 생성   computeIfAbsent                  if (children[i] == null) children[i] = new Node()
        가지치기    children.remove(c)               children[i] = null
                                                      (배열은 여전히 26칸 — 노드가 통째로
                                                       버려져야 그 26칸이 회수된다)
        범위 밖 문자
            insert / remove : 예외를 던진다 ("ArrayTrie 는 a~z 만 담는다")
            findNode 경유    : idx < 0 이면 null -> contains 는 false, countWithPrefix 는 0

    자식이 빽빽하면(영어 단어 뭉치처럼) 배열이 빠르고, 성기면 맵이 메모리를 아낀다.
    "26칸 중 대부분이 null" 이라는 낭비를 줄이는 것이 20 장 래딕스 트라이의 출발점이다
```

> **인덱스 변환(c - 'a')** — 글자를 배열 칸 번호로 바꾸는 산수.\
> 예: 'a'는 0번, 'r'은 17번, 'z'는 25번 칸이 된다. 범위를 벗어나면 -1을 돌려준다.

> **래딕스 트라이(radix trie)** — 자식이 하나뿐인 길목들을 한 칸으로 합쳐 메모리를 아끼는 트라이(20장).\
> 예: ArrayTrie에서 "26칸 중 25칸이 null" 인 낭비가 그 출발점이다.

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

### 동작 — 와일드카드 탐색

**언제 쓰나** — "ca."처럼 아무 글자나 되는 칸(.)이 섞인 패턴으로 단어를 찾을 때(search).

> **와일드카드(wildcard)** — 아무 글자와도 맞는 만능 문자.\
> 예: 여기서는 `.` 하나가 글자 하나를 대신해서, "ca." 는 car 와도 cat 과도 맞는다.

```
WordDictionary — 트라이를 새로 만들지 않는다. MapTrie 하나를 감싸고 search 만 더한다
    addWord(w) = trie.insert(w),   size() = trie.size()

search(pattern) : '.' 은 아무 글자 하나와 맞는다. 갈림길에서 전부 시도한다
    담긴 단어 : cat, car, card, dog

    search("ca.")
        (root) --'c'--> [c] --'a'--> [ca]      여기까지는 글자가 정해져 있어 길이 하나뿐
                                       |
                        '.' 이므로 children 의 값 전부를 시도한다
                                       |
                      +----------------+----------------+
                      |                                 |
                   'r' -> [car]                      't' -> [cat]
                   i == 길이 -> end 확인               i == 길이 -> end 확인
                   end = true -> 참 (여기서 끝)        (앞에서 이미 참이 나왔으면 오지 않는다)

    search("ca.e")
                      +----------------+----------------+
                      |                                 |
                   'r' -> [car]                      't' -> [cat]
                   다음 글자 'e' -> children.get('e') = null
                   -> 재귀가 null 을 받고 false        -> 마찬가지로 false
                                    => 전체 false

    재귀 세 줄이 전부다
        node == null            -> false          (막힌 길)
        i == pattern.length()   -> node.end       (자식이 있느냐가 아니라 end 냐를 본다)
        c == '.'                -> children.values() 를 전부 시도, 하나라도 참이면 참
        그 밖                   -> children.get(c) 로 한 갈래만 재귀

    되돌리기 코드가 따로 없다 — false 를 반환하고 호출자로 돌아가는 것이 곧 백트래킹이다
    '.' 하나마다 갈래가 자식 수만큼 늘어난다. 앞쪽에 '.' 이 많을수록 훑는 가지가 많아진다
```

**그림에서 일어난 일 (쉽게)**

1. 정해진 글자('c', 'a')까지는 길이 하나뿐이라 그냥 내려갔다.
2. '.'을 만나자 갈림길의 **모든 자식을 하나씩 다 시도**했다.\
   하나라도 성공하면 전체가 참.
3. 막힌 길은 false를 돌려주며 호출한 곳으로 되돌아간다 — 이 "돌아감" 자체가 백트래킹이라 되돌리기 코드가 따로 없다.

> **재귀(recursion)** — 함수가 자기 자신을 부르는 것.\
> 예: "서브트리도 똑같은 트라이"라서, search는 자식 노드에 대고 자기 자신을 다시 부르는 세 줄로 끝난다.

**비용** — '.'이 없으면 O(L).\
'.' 하나마다 그 자리의 자식 수만큼 갈래가 곱해진다.

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

> 문제 설명: `words` 가 비었으면 `""`. 공통 접두사가 없으면 `""`.\
> 흔한 풀이는 첫 단어를 기준으로 나머지와 한 글자씩 비교하는 것이고, 그게 더 짧다.\
> 여기서 트라이로 푸는 이유는 "공통 접두사"가 트라이에서 무엇인지 눈으로 보기 위해서다.\
> 생각할 것 — 전부 넣고 뿌리에서 내려간다. 언제 멈추는가. 두 조건이다.\
> 자식이 2개 이상이면 거기서 갈라진다. 공통이 아니다. /\
> 자식이 하나여도 지금 노드가 `end` 면 멈춘다. 그 단어 자체가 더 못 간다.\
> `["a", "ab"]` 의 답은 `"a"` 다. 이 조건을 빼면 `"ab"` 가 나온다.\
> 즉 공통 접두사는 **뿌리에서 첫 갈림길(또는 첫 단어 끝)까지의 경로**다.\
> 시그니처: `static String longestCommonPrefix(String[] words)`

- 내 접근:
- 논리:
- 비용(왜):

### 문제 2. 접두사로 시작하는 단어를 사전순 앞에서 k 개

> 문제 설명: k 개보다 적으면 있는 만큼. k 가 0 이하면 빈 리스트.\
> 여기 시간 제한이 있다. 접두사에 20만 개가 걸려 있는데 k 가 10 인 질의를 반복한다.\
> `trie.keysWithPrefix(prefix).subList(0, k)` 는 답은 맞지만 매번 20만 개를 다 모은다.\
> `MapTrie` 를 구체 타입으로 받는 이유가 이것이다. 중간에 멈추려면 노드를 봐야 한다.\
> 인터페이스가 주는 것만으로는 이 문제를 풀 수 없다. 그것도 정보다.\
> 생각할 것 — `collect` 를 하되 k 개가 차면 그만둔다. 개수를 확인할 자리가 셋이다.\
> 재귀 진입부, 단어를 담은 직후, 자식에서 돌아온 직후. 셋 중 하나만 있어도 답은 맞다.\
> 나머지는 헛걸음을 줄일 뿐이다. 진짜 요점은 **아예 확인하지 않고 전부 모은 뒤\
> 앞에서 k 개를 자르는 것**과의 차이다. 그것도 답은 맞다. 다만 접두사에 10만 개가 걸려 있으면\
> 질의마다 10만 걸음이다. 성능 테스트가 그 차이를 잡는다.\
> 시그니처: `static List<String> autocomplete(MapTrie trie, String prefix, int k)`

> **자동완성(autocomplete)** — 입력한 접두사로 시작하는 단어들을 제안하는 기능.\
> 예: 검색창에 "ca"를 치면 car·card·cat 을 사전순 앞에서 몇 개만 보여 준다.

- 내 접근:
- 논리:
- 비용(왜):

### 문제 3. 문자열 s 의 서로 다른 부분 문자열 개수

> 문제 설명: 빈 문자열은 세지 않는다.\
> `"abc"` 면 a, ab, abc, b, bc, c 로 6개. `"aaa"` 면 a, aa, aaa 로 3개. (같은 것은 한 번만)\
> 모든 접미사를 트라이에 넣으면 노드 하나가 부분 문자열 하나다.\
> 접미사 `"abc"`, `"bc"`, `"c"` 를 넣고 만들어진 노드를 세면 그게 답이다.\
> 중복 제거를 따로 할 필요가 없다. 같은 부분 문자열은 같은 경로라 노드를 다시 안 만든다.\
> 여기서는 `Trie` 대신 `MapTrie.Node` 를 직접 써도 된다.\
> `end` 도 `wordsBelow` 도 필요 없고 만들어진 노드 수만 세면 되기 때문이다.\
> 생각할 것 — i 를 0 부터 `s.length()-1` 까지 옮기며 `s[i..]` 를 뿌리부터 밀어 넣고,\
> **새 노드를 만들 때마다** 1 을 센다. s 가 null 이거나 비었으면 0.\
> 이 풀이의 한계도 같이 보라. 길이 n 이면 노드가 최대 n(n+1)/2 개다.\
> n 이 10만이면 50억 개라 아예 못 만든다. 접미사 배열과 접미사 오토마타가 존재하는 이유다.\
> 시그니처: `static int countDistinctSubstrings(String s)`

> **접미사(suffix)** — 단어의 뒷부분.\
> 예: "abc"의 접미사는 "abc", "bc", "c" 셋이고, 이 셋을 트라이에 넣으면 노드 하나가 서로 다른 부분 문자열 하나가 된다.

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

## 용어 풀이

- **트라이(trie)**: 글자 하나가 갈림길 하나인 나무. 뿌리에서 어떤 노드까지의 경로가 곧 문자열이다. 이름은 re**trie**val(검색)에서 왔다.
- **접두사(prefix)**: 단어의 앞부분. "ca"는 "cat", "car", "card"의 접두사다.
- **노드(node)**: 트리의 칸 하나. 트라이에서는 "여기까지 온 글자들"을 대표한다.
- **루트/뿌리(root)**: 트리 맨 위의 출발 노드. 빈 문자열에 해당한다.
- **end 표시**: "여기서 끝나는 단어가 있다"는 도장. 노드 존재 ≠ 단어 존재라서 필요하다.
- **wordsBelow**: 그 노드를 지나는 단어 수. 넣고 뺄 때마다 미리 갱신해 둬서 접두사 개수 질문에 즉답한다.
- **O(L)**: 비용이 단어 길이 L에만 비례한다는 뜻. 담긴 단어 수 n과 무관 — 트라이의 존재 이유.
- **TreeMap**: 키를 정렬 순서로 관리하는 자바 맵. children에 쓰면 자식 순회가 저절로 사전순이 된다.
- **백트래킹(backtracking)**: 갈림길들을 깊이 들어가 보고, 되돌아 나올 때 가던 길 기록(경로 문자열 등)을 원래대로 되돌리는 탐색 방식.
- **StringBuilder**: 문자열을 이어 붙였다 지웠다 할 수 있는 자바 도구. 경로 문자열 하나를 만들었다 지우며 돌려 쓴다.
- **재귀(recursion)**: 함수가 자기 자신을 부르는 것. "서브트리도 똑같은 트라이"라서 자연스럽다.
- **와일드카드(wildcard)**: 아무 글자와도 맞는 만능 문자. WordDictionary의 `.`.
- **인덱스 변환(c - 'a')**: 글자를 배열 칸 번호로 바꾸는 산수. 'a'→0, 'z'→25. ArrayTrie의 핵심.
- **가지치기(pruning)**: 답이 없는 가지를 들어가지 않는 것. 삭제에서 wordsBelow=0인 가지를 통째로 끊는 것도 같은 정신이다.
- **자동완성(autocomplete)**: 입력한 접두사로 시작하는 단어들을 제안하는 기능. keysWithPrefix가 그 엔진이다.
- **접미사(suffix)**: 단어의 뒷부분. 모든 접미사를 트라이에 넣으면 노드 하나 = 서로 다른 부분 문자열 하나가 된다(문제 3).
- **래딕스 트라이(radix trie)**: 자식이 하나뿐인 길목들을 한 칸으로 합쳐 메모리를 아끼는 트라이(20장).
