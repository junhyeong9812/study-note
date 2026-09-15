# data-structure/20-radix-trie — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 작성 방식: **2-summary를 닫고 기억만으로** 쓴다 → 실제 코드/원전으로 검증 → 틀린 부분만 수정.
> 기준 소스는 문서가 아니라 코드다.
> ⚠️ 이 정답은 Claude 초안(2026-09-15) — 본인 검토 후 이 줄 삭제

## 정답

### A. 문제 (RadixTrieProblems)

#### 1. 가장 긴 공통 접두사 — `longestCommonPrefix`

**질문**: 어떻게 푸는가 — 왜 내려갈 필요 없이 **뿌리의 자식**만 보면 되는가(압축 불변식이 무엇을 보장하는가). 뿌리가 키인 경우는 왜 답이 `""` 인가. 09번과 비교해 비용이 정말 줄었는가, 아니면 읽는 자리만 바뀐 것인가.

**impl 코드**

`/home/jun/project/myway/data-structure/20-radix-trie/impl/RadixTrieProblems.java`

```java
public static String longestCommonPrefix(String[] words) {
    if (words == null || words.length == 0) {
        return "";
    }
    RadixTrie<Boolean> trie = new RadixTrie<>();
    for (String w : words) {
        trie.put(w, Boolean.TRUE);
    }
    if (trie.root.value != null || trie.root.children.size() != 1) {
        return "";
    }
    return trie.root.children.values().iterator().next().edge;
}
```

- 논리: 전부 트라이에 넣은 뒤 **뿌리의 자식이 하나인지만 본다**.\
  하나면 그 간선 라벨이 곧 답이고, 아니면 `""` 다.
- 논리: 09번에는 `while` 루프가 있었다 — 갈림길이 나올 때까지 한 글자씩 내려가며 `StringBuilder` 에 모았다.\
  여기에는 루프가 없다. **그 사슬이 이미 간선 하나로 눌려 있기 때문이다.**

> **간선 라벨(edge label)** — 압축 트라이에서 부모와 자식을 잇는 간선에 붙은 **문자열 조각**.\
> 예: 09번이 `r-o-m-a-n` 다섯 간선으로 표현한 것을 여기서는 라벨 `"roman"` 하나로 담는다.

> **압축 불변식(compression invariant)** — 뿌리가 아닌 모든 노드는 **키이거나 갈림길**이라는 규칙.\
> 예: 자식이 하나뿐이면서 값도 없는 노드는 존재할 수 없다 — 있으면 부모 간선에 흡수돼야 한다.

**압축 불변식이 보장하는 것**

```text
 뿌리의 자식이 정확히 하나라고 하자. 그 노드를 N, 간선 라벨을 E 라고 한다.

 (1) 모든 키가 E 로 시작한다
       뿌리에서 갈 길이 하나뿐이다. 다른 시작 글자를 가진 키가 있었다면
       뿌리에 자식이 둘 이상이었을 것이다.
       => E 는 '공통 접두사'다

 (2) E 보다 더 긴 공통 접두사는 없다
       압축 불변식에 의해 N 은 둘 중 하나다.
         N 이 키다        -> E 자체가 어떤 단어다. 그 단어는 E 보다 길지 않다.
                             => 공통 접두사는 E 를 넘어설 수 없다
         N 이 갈림길이다  -> N 아래에서 단어들이 서로 다른 글자로 갈라진다
                             => E 다음 글자가 단어마다 다르다
       => E 는 '가장 긴' 공통 접두사다

 (1) + (2) = E 가 곧 답이다. 내려갈 필요가 없다.
```

- 논리: 이 증명이 **압축 불변식에 전적으로 의존**한다.\
  자식 하나짜리 통과 노드가 남아 있는 트리(= 병합을 빼먹은 트리)에서는 (2)가 깨진다 — 답이 E 보다 짧게 잘린다.
- 논리: 09번에서 루프의 종료 조건이 둘(`children.size() == 1` 과 `!cur.end`)이었던 것이, 여기서는 **불변식이 그 둘을 미리 다 해치워 놓은 상태**로 바뀐 것이다.

**손으로 추적** — `["interspecies", "interstellar", "interstate"]` → `"inters"`

```text
 put("interspecies")
     root
       +-- "interspecies"*                        노드 1개

 put("interstellar")
     common = commonPrefixLength("interspecies", "interstellar", 0)
            = i n t e r s  까지 같고 7번째에서 p vs t  -> 6
     6 != 12 이므로 쪼갠다
     root
       +-- "inters"                               (자른 자리. 키가 아니다)
             +-- "pecies"*
             +-- "tellar"*

 put("interstate")
     'i' 로 내려가 edge "inters", common = 6 == 6  -> 통과
     pos = 6, 남은 것 "tate", 't' 자식이 edge "tellar"
     common = commonPrefixLength("tellar", "interstate", 6) = "t" 만 같다 -> 1
     1 != 6 이므로 또 쪼갠다
     root
       +-- "inters"
             +-- "pecies"*
             +-- "t"
                   +-- "ellar"*
                   +-- "ate"*

 답을 읽는다
     root.value == null          ("" 는 키가 아니다)
     root.children.size() == 1   (자식이 'i' 하나)
     -> 그 간선 라벨 "inters" 를 그대로 반환
```

`answerIsTheFirstEdge` 테스트가 이 등식을 그대로 못 박는다.

`/home/jun/project/myway/data-structure/20-radix-trie/src/test/java/com/datastructure/radix/RadixTrieProblemsTest.java`

```java
String[] words = {"interspecies", "interstellar", "interstate"};
RadixTrie<String> t = new RadixTrie<>();
for (String w : words) {
    t.put(w, w);
}
assertEquals(1, t.root.children.size());
assertEquals("inters", t.root.children.values().iterator().next().edge);
assertEquals(RadixTrieProblems.longestCommonPrefix(words),
        t.root.children.values().iterator().next().edge);
```

- 측정: 같은 입력을 impl 복제본으로 돌려 확인했다 — `뿌리 자식 수 = 1 / 간선 = inters / 답 = inters`.\
  (원본 문서에 없는 수치 — impl 을 복제해 직접 측정한 값이다)

**두 개의 조기 반환이 각각 막는 것**

```text
 if (trie.root.value != null || trie.root.children.size() != 1) return "";
        ^^^^^^^^^^^^^^^^^^^^^^^^    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        조건 A: 뿌리가 키다          조건 B: 자식이 0개 또는 2개 이상

 조건 A  words = ["", "abc"]
         put("") 은 pos == key.length() 가 즉시 참이라 root.value 에 값을 둔다
         "" 가 단어 중 하나이므로 공통 접두사는 "" 를 넘어설 수 없다
         -> 조건 A 가 없으면 "abc" 를 반환해버린다 (틀림)

 조건 B  자식 0개  : words = [""] 뿐이다  -> ""
         자식 2개+ : 첫 글자부터 갈린다   -> ""    예) ["dog","racecar","car"]

 두 조건 다 empties / noCommon 테스트가 직접 못 박는다
```

- 논리: 09번의 `!cur.end` 조건이 여기서는 **`root.value != null` 하나로 축소**됐다.\
  09번은 내려가는 모든 층에서 "여기서 끝나는 단어가 있나"를 물어야 했지만, 여기서는 그 상황이 뿌리에서만 발생한다.\
  뿌리가 아닌 노드가 키라면 그 노드는 이미 사슬의 끝이고, 그 아래로 더 눌릴 게 없기 때문이다.

**`["a", "ab"]` 는 왜 `"a"` 인가**

```text
 put("a")   root
              +-- "a"*

 put("ab")  'a' 자식의 edge = "a", common = 1 == edge.length()
            -> 쪼개지 않고 통과. pos = 1, cur = "a" 노드
            pos != key.length() 이므로 'b' 자식을 찾는다 -> 없다 -> 잎 "b" 를 단다

            root
              +-- "a"*          <- 키이면서 자식도 있다
                    +-- "b"*

 root.children.size() == 1, root.value == null
 -> 답은 간선 "a"

 왜 맞는가 : 노드 "a" 가 키이므로 압축 불변식의 (2)-앞가지에 걸린다.
             "a" 라는 단어가 있으니 공통 접두사는 "a" 를 넘을 수 없다.
             09번에서는 이것을 end 플래그로 따로 물어야 했는데,
             여기서는 간선이 거기서 끊겨 있다는 사실 자체가 같은 정보다.
```

**09번과 비교 — 비용은 줄었는가**

| | 09번 트라이 | 압축 트라이 |
|---|---|---|
| 트라이 만들기 | O(총 글자 수), `insert` 가 글자마다 노드 생성 | O(총 글자 수), `put` 이 간선마다 `substring` 할당 |
| 답 읽기 | 갈림길까지 하강 O(LCP 길이) | **필드 읽기 1회 O(1)** |
| 답 만들기 | `StringBuilder` 에 글자를 하나씩 append | **이미 있는 `String` 을 그대로 반환** |
| 총합 | O(총 글자 수) | O(총 글자 수) |

- 논리: **점근 비용은 똑같다.** 줄어든 것은 마지막 하강뿐이고 그건 원래도 O(L) 이라 지배항이 아니었다.
- 논리: LCP 글자들은 사라진 게 아니라 **삽입 시점의 `split` 으로 옮겨 갔다**.\
  `commonPrefixLength` 가 글자를 하나씩 비교하고, `child.edge.substring(common)` 이 새 문자열을 만든다.\
  README 가 말하는 "읽는 자리가 바뀐 것이지 공짜가 아니다"가 이 뜻이다.
- 논리: 실질적 차이는 **답을 만드는 비용**이다 — 09번은 LCP 길이만큼 `append` 하지만 여기서는 기존 `String` 참조를 넘긴다.\
  `manyWords` 테스트는 10만 단어에 `@Timeout(15)` 를 건다. 답 길이가 12(`"commonprefix"`)라 이 차이는 전체에서 미미하다.

**질문별 답**

- Q: 문제 1을 어떻게 푸는가?\
  A: 단어를 전부 압축 트라이에 넣고 **뿌리의 자식이 정확히 하나이고 뿌리가 키가 아닐 때만** 그 자식의 간선 라벨을 그대로 반환한다.\
  그 외에는 `""` 다. 하강 루프가 아예 없다.

- Q: 왜 내려갈 필요 없이 뿌리의 자식만 보면 되는가 — 압축 불변식이 무엇을 보장하는가?\
  A: "뿌리가 아닌 노드는 키이거나 갈림길이다"가 **외길 구간이 트리에 노드로 남아 있지 않다**는 것을 보장하기 때문이다.\
  뿌리의 자식이 하나면 모든 키가 그 간선을 지나므로 라벨은 공통 접두사이고, 그 자식 노드는 키이거나 갈림길이므로 라벨을 **더 늘릴 수 없다**.\
  09번이 루프를 돌며 찾던 "멈출 지점"이 여기서는 **자료구조 안에 이미 계산되어 있다**.

- Q: 뿌리가 키인 경우는 왜 답이 `""` 인가?\
  A: 뿌리가 키라는 것은 빈 문자열이 입력 단어 중 하나라는 뜻이고, `""` 는 어떤 문자열로도 시작하지 않으므로 공통 접두사의 **상한이 `""`** 이기 때문이다.\
  `["", "abc"]` 에서 이 검사를 빼면 자식이 하나(`"abc"`)라 `"abc"` 를 반환하는데, `""` 는 `"abc"` 로 시작하지 않으므로 틀린다.\
  09번의 `!cur.end` 종료 조건이 뿌리 한 곳으로 축소된 형태다.

- Q: 09번과 비교해 비용이 정말 줄었는가, 아니면 읽는 자리만 바뀐 것인가?\
  A: **읽는 자리만 바뀌었다.** 둘 다 O(총 글자 수)이고, 지배항은 트라이를 만드는 비용이다.\
  09번이 마지막에 하던 O(LCP 길이) 하강이 O(1) 필드 읽기로 바뀐 대신, 그 글자 비교는 삽입 때의 `commonPrefixLength` 와 `substring` 으로 **앞당겨졌다**.\
  게다가 압축 쪽은 `split` 마다 새 `String` 을 할당하므로 총 할당량은 오히려 더 많을 수 있다.

**더 생각할 것**

- 이 문제만 풀려면 트라이 자체가 과하다 — 세로 비교(단어들의 i번째 글자를 동시에 보기)가 O(총 글자 수) 시간에 **추가 공간 없이** 같은 답을 낸다.\
  여기서 트라이를 쓰는 이유는 답이 "구조에서 읽힌다"는 것을 보이기 위해서다.\
  (원본에 근거 없음 — 내 추론)
- `RadixTrie<Boolean>` 으로 선언한 이유가 있다 — `PrefixMap` 계약이 `null` 값을 금지하므로 존재 표시에 `Boolean.TRUE` 를 써야 한다.\
  05번 해시맵에서 "값이 null 인가, 키가 없는가"를 구별할 수 없게 되는 문제와 같은 결정이다.
- `trie.root` 는 `package-private` 필드다. 이 문제도 문제 2와 같은 이유로 **인터페이스만으로는 못 푼다**.

---

#### 2. 자동완성 상위 k개 — `autocomplete`

**질문**: 어떻게 푸는가 — `keysWithPrefix(prefix).subList(0, k)` 와의 차이는 무엇인가. 시작 경로가 prefix 가 아닐 수 있는 이유는. `RadixTrie` 를 구체 타입으로 받아야 하는 이유는(인터페이스가 못 주는 것). 비용은 왜 그런가.

**impl 코드**

`/home/jun/project/myway/data-structure/20-radix-trie/impl/RadixTrieProblems.java`

```java
public static List<String> autocomplete(RadixTrie<String> trie, String prefix, int k) {
    List<String> out = new ArrayList<>();
    if (k <= 0) {
        return out;
    }
    StringBuilder path = new StringBuilder();
    RadixTrie.Node<String> start = trie.prefixRoot(prefix, path);
    if (start != null) {
        collectUpTo(start, path, out, k);
    }
    return out;
}

private static void collectUpTo(RadixTrie.Node<String> node, StringBuilder path,
        List<String> out, int k) {
    if (out.size() >= k) {
        return;
    }
    if (node.value != null) {
        out.add(path.toString());
        if (out.size() >= k) {
            return;
        }
    }
    for (RadixTrie.Node<String> child : node.children.values()) {
        path.append(child.edge);
        collectUpTo(child, path, out, k);
        path.setLength(path.length() - child.edge.length());
        if (out.size() >= k) {
            return;
        }
    }
}
```

- 논리: `RadixTrie.collect` 와 **같은 재귀**인데 `out.size() >= k` 검사가 세 곳에 끼어 있다.
- 논리: 세 곳인 이유가 각각 다르다.\
  (1) 함수 진입 시 — 이미 찼으면 내려가지 않는다.\
  (2) 키를 담은 직후 — 방금 k번째를 담았으면 즉시 끝낸다.\
  (3) 자식에서 돌아온 직후 — 그 아래에서 채웠으면 형제 가지로 넘어가지 않는다.
- 논리: 붙였다 떼는 길이가 09번과 다르다 — 09번은 `deleteCharAt(length-1)` 로 **한 글자**를 떼지만 여기서는 `setLength(length - child.edge.length())` 로 **간선 라벨 길이만큼** 뗀다.\
  간선 하나에 글자가 여럿이기 때문이다.

> **사전순(lexicographic order)** — 앞 글자부터 비교해 정하는 문자열 순서.\
> 예: `"rubens" < "ruber" < "rubicon" < "rubicundus"` — 짧은 쪽이 접두사면 짧은 쪽이 앞이다.

> **조기 종료(early termination)** — 답이 다 찼으면 남은 탐색을 하지 않고 즉시 되돌아 나오는 것.\
> 예: 10만 개가 걸린 접두사에서 10개만 필요하면 10개를 담는 순간 부분 트리 순회를 끊는다.

**왜 재귀 순서가 사전순인가**

```text
 Node.children 이 TreeMap<Character, Node> 다

   `/home/jun/project/myway/data-structure/20-radix-trie/impl/RadixTrie.java`
   final Map<Character, Node<V>> children = new TreeMap<>();

 키가 '간선의 첫 글자' 이고 TreeMap 이 오름차순 순회이므로
   자식을 도는 순서 = 간선 첫 글자의 오름차순

 그리고 서로 다른 자식의 간선은 첫 글자가 반드시 다르다
   (같았다면 삽입 때 쪼개져서 하나로 합쳐졌을 것이다)
   => 첫 글자 순서가 곧 부분 트리 전체의 사전 순서를 결정한다

 노드 자신을 자식보다 먼저 담으므로
   "접두사 자신이 키이면 결과의 맨 앞" 이 자동으로 성립한다
   예) keysWithPrefix("test") 에서 "test" 가 "tester" 보다 앞
```

**ROMAN 7개에서 `autocomplete(t, "rub", 3)` 추적**

```text
 트리 모양 (RadixTrieStructureTest.romanShape 가 못 박은 것)

   root
    +-- "r"
         +-- "om"
         |    +-- "an"
         |    |    +-- "e"*        romane
         |    |    +-- "us"*       romanus
         |    +-- "ulus"*          romulus
         +-- "ub"
              +-- "e"
              |    +-- "ns"*       rubens
              |    +-- "r"*        ruber
              +-- "ic"
                   +-- "on"*       rubicon
                   +-- "undus"*    rubicundus

 prefixRoot("rub", path)
     pos=0  자식 'r' edge "r"   : 3-0=3 >= 1 이고 startsWith -> path="r",   pos=1
     pos=1  자식 'u' edge "ub"  : 3-1=2 >= 2 이고 startsWith -> path="rub", pos=3
     pos == prefix.length() -> 노드 "ub" 반환, path = "rub"

 collectUpTo(노드 "ub", path="rub", k=3)
     노드 "ub" 는 value == null  -> 안 담음
     자식 'e' : path="rube"
         노드 "e" value == null -> 안 담음
         자식 'n' : path="rubens" -> value != null -> out=[rubens]   (1개)
                    되돌림 path="rube"
         자식 'r' : path="ruber"  -> value != null -> out=[..,ruber] (2개)
                    되돌림 path="rube"
         되돌림 path="rub"
     자식 'i' : path="rubic"
         노드 "ic" value == null
         자식 'o' : path="rubicon" -> out 3개  -> 여기서 k 도달
                    (2)번 검사로 즉시 반환
         복귀 후 (3)번 검사로 'undus' 가지를 안 내려간다
     결과 [rubens, ruber, rubicon]

 topK 테스트의 기대값과 같다.
```

**`keysWithPrefix(prefix).subList(0, k)` 와의 차이**

| | `keysWithPrefix().subList(0,k)` | `autocomplete` |
|---|---|---|
| 답 | 같다 (`agreesWithKeysWithPrefix` 가 검증) | 같다 |
| 부분 트리 순회 | **전부** 훑는다 | k 개를 담는 순간 끊는다 |
| 만드는 문자열 수 | 매칭 수 m 개 | **최대 k 개** |
| 접두사에 10만 개, k=10 | 10만 걸음 + 10만 문자열 → 99,990개를 버림 | 10 걸음대 |
| 질의 10만 번 | 약 10^10 걸음 | 약 10^6 걸음 |

- 논리: 이것은 **틀린 풀이가 아니라 느린 풀이**다.\
  `agreesWithKeysWithPrefix` 테스트가 두 방식의 답이 모든 접두사·모든 k 에서 같음을 따로 못 박는다.
- 논리: 그래서 정확성 테스트로는 절대 안 걸린다. `stopsEarly` 라는 **성능 테스트 하나**가 유일한 방어선이다.\
  README 가 "변종으로 확인해보니 94개 중 성능 테스트 하나만 그 차이를 잡았다"고 적은 것이 이것이다.

`/home/jun/project/myway/data-structure/20-radix-trie/src/test/java/com/datastructure/radix/RadixTrieProblemsTest.java`

```java
@Test
@Timeout(20)
@DisplayName("10만 개가 걸린 접두사에서 10개만 뽑는다")
void stopsEarly() {
    // 전부 모으고 자르면 질의 하나가 10만 걸음이다. 그것을 10만 번 한다.
    RadixTrie<String> t = new RadixTrie<>();
    for (int i = 0; i < 100_000; i++) {
        t.put("a" + RadixTrieTest.encode(i), "v");
    }
    List<String> first = RadixTrieProblems.autocomplete(t, "a", 10);
    assertEquals(10, first.size());
    for (int q = 0; q < 100_000; q++) {
        assertEquals(first, RadixTrieProblems.autocomplete(t, "a", 10));
    }
}
```

**시작 경로가 prefix 가 아닐 수 있는 이유**

```text
 09번에서는 findNode(prefix) 가 돌려준 노드의 경로가 정확히 prefix 였다.
 한 글자에 노드 하나라 prefix 의 마지막 글자에 해당하는 노드가 항상 있었기 때문이다.
 그래서 09번은 collectUpTo(start, new StringBuilder(prefix), ...) 로 시작할 수 있었다.

 압축 트라이에서는 그 노드가 없을 수 있다.

   "romane" 하나만 넣은 트리

     root
       +-- "romane"*

   keysWithPrefix("rom") 을 물으면
       "rom" 에서 멈출 노드가 없다. 'r','o','m' 은 간선 중간이다.
       그래도 답은 ["romane"] 로 나와야 한다.

   그래서 prefixRoot 는 '간선을 넘어선' 노드를 돌려준다
       시작 노드 = "romane" 노드
       그 노드의 경로 = "romane"  <- prefix("rom") 보다 길다

 만약 path 를 new StringBuilder(prefix) 로 시작했다면
       "rom" + (자식 간선들) 이 되어 "rom" 이 그대로 답이 된다. 틀린다.
```

- 논리: 그래서 `prefixRoot` 의 시그니처에 `StringBuilder path` 가 **출력 인자**로 들어 있다.\
  "어디서 시작하는가"와 "거기까지의 실제 경로가 무엇인가"를 함께 돌려줘야 하기 때문이다.
- 논리: `autocomplete` 가 `new StringBuilder()` 를 **빈 채로** 넘기고 `prefixRoot` 가 채운다.\
  09번과 한 글자만 다른데 그 한 글자가 정확성의 전부다.

`/home/jun/project/myway/data-structure/20-radix-trie/impl/RadixTrie.java`

```java
Node<V> prefixRoot(String prefix, StringBuilder path) {
    Node<V> cur = root;
    int pos = 0;
    while (pos < prefix.length()) {
        Node<V> child = cur.children.get(prefix.charAt(pos));
        if (child == null) {
            return null;
        }
        if (prefix.length() - pos < child.edge.length()) {
            if (!child.edge.startsWith(prefix.substring(pos))) {
                return null;
            }
            path.append(child.edge);
            return child;
        }
        if (!prefix.startsWith(child.edge, pos)) {
            return null;
        }
        path.append(child.edge);
        pos += child.edge.length();
        cur = child;
    }
    return cur;
}
```

- 논리: 가운데 `if` 가 "남은 접두사가 간선보다 짧다" = **간선 중간에서 끝난다**는 경우다.\
  이때 방향이 뒤집힌다 — 평소에는 `prefix.startsWith(edge)` 를 보지만 여기서는 `edge.startsWith(남은 prefix)` 를 본다.
- 논리: `path.append(child.edge)` 를 **간선 전체**로 한다. prefix 까지만 붙이면 그 아래 키의 이름이 잘린다.

**`RadixTrie` 를 구체 타입으로 받아야 하는 이유**

```text
 PrefixMap 계약이 주는 것
     keysWithPrefix(prefix)  -> List<String> 을 완성해서 준다
     countWithPrefix(prefix) -> 개수만
     get / containsKey / longestPrefixOf / keys / size ...

 이 문제가 필요한 것
     prefixRoot(prefix, path)   <- 계약에 없다 (package-private)
     RadixTrie.Node             <- 계약에 없다 (package-private 내부 클래스)
     node.children, node.value  <- 계약에 없다

 중간에 멈추려면 부분 트리를 직접 걸어야 하고,
 직접 걸으려면 노드가 필요한데 인터페이스는 노드를 노출하지 않는다.
 keysWithPrefix 는 리스트를 다 만들어서 주므로
 반환값을 자르는 시점에는 이미 비용을 다 치른 뒤다.

 즉 "인터페이스가 주는 것만으로는 못 푸는 문제가 있다" 가 이 문제의 메시지다.
 09번 문제 2가 MapTrie 를 구체 타입으로 받은 것과 똑같은 이유다.
```

**비용**

| 단계 | 비용 | 왜 |
|---|---|---|
| `prefixRoot` | O(\|prefix\|) 글자 비교 + 갈림길 수만큼 `TreeMap` 조회 | 접두사 길이만큼만 훑는다 |
| `collectUpTo` | O(k · 평균 키 길이) | k 개를 담는 순간 세 곳에서 전부 끊는다 |
| `path.toString()` | 담는 키마다 문자열 1개 | **최대 k 개**만 만든다 |
| 총합 | **O(\|prefix\| + k·L)** — 매칭 수 m 과 무관 | m 이 10만이어도 k=10 이면 10개분만 일한다 |

- 논리: 정확히는 "k 개를 담기까지 지나친 노드 수"라서, 값 없는 갈림길 노드를 몇 개 지나칠 수 있다.\
  압축 불변식 덕에 그런 노드는 아래에 키가 최소 2개 있으므로, 지나친 갈림길 수는 담은 키 수를 넘지 않는다.\
  (원본에 근거 없음 — 내 추론)

**질문별 답**

- Q: 문제 2를 어떻게 푸는가?\
  A: `prefixRoot(prefix, path)` 로 시작 노드와 **그 노드까지의 실제 경로**를 함께 받고, 거기서부터 `collect` 와 같은 재귀를 돌되 `out.size() >= k` 가 되는 순간 모든 층에서 즉시 반환한다.\
  `TreeMap` 자식 순회가 간선 첫 글자의 오름차순이고 서로 다른 자식의 첫 글자는 반드시 다르므로, 나오는 순서가 그대로 사전순이다.

- Q: `keysWithPrefix(prefix).subList(0, k)` 와의 차이는 무엇인가?\
  A: 답은 같고 **비용이 다르다**. `subList` 방식은 비용이 출력 크기 k 가 아니라 **전체 매칭 수 m 에 비례**한다.\
  접두사에 10만 개가 걸려 있으면 질의 하나가 부분 트리 전체를 훑고 문자열 10만 개를 만든 뒤 99,990개를 버린다. 그것을 10만 번 하면 20초 제한을 넘는다.\
  `agreesWithKeysWithPrefix` 가 두 방식의 답이 같음을 따로 검증하므로, 이것은 틀린 풀이가 아니라 **느린 풀이**이고 성능 테스트 하나만이 그것을 잡는다.

- Q: 시작 경로가 prefix 가 아닐 수 있는 이유는?\
  A: 압축 트라이에서는 접두사가 **간선 중간에서 끝날 수 있어서** 그 자리에 노드가 아예 없기 때문이다.\
  `"romane"` 하나만 있을 때 `"rom"` 은 간선 `"romane"` 의 중간이라 멈출 노드가 없고, `prefixRoot` 는 그 간선을 넘어간 노드(`"romane"`)를 돌려준다 — 그 노드의 경로는 접두사보다 **길다**.\
  그래서 09번처럼 `new StringBuilder(prefix)` 로 시작하면 안 되고, `prefixRoot` 가 채워 준 `path` 를 그대로 써야 한다.

- Q: `RadixTrie` 를 구체 타입으로 받아야 하는 이유는(인터페이스가 못 주는 것)?\
  A: 중간에 멈추려면 부분 트리를 **직접 걸어야** 하고, 그러려면 `prefixRoot` 와 `Node`(그리고 `children`·`value`)가 필요한데 셋 다 `PrefixMap` 계약에 없는 내부 구조이기 때문이다.\
  계약이 주는 `keysWithPrefix` 는 리스트를 완성해서 돌려주므로 자르는 시점에는 이미 비용을 다 치른 뒤다.

- Q: 비용은 왜 그런가?\
  A: `prefixRoot` 가 O(|prefix|), `collectUpTo` 가 담은 키 수에 비례해 **O(k·L)** 이고, 전체 매칭 수 m 은 비용에 들어오지 않는다.\
  세 곳의 `out.size() >= k` 검사가 각각 "내려가기 전", "담은 직후", "형제로 넘어가기 전"을 막아 m 에 대한 의존을 끊기 때문이다.

**더 생각할 것**

- 실무 자동완성은 여기에 **점수**가 붙는다 — 사전순 앞 k 개가 아니라 인기순 앞 k 개다.\
  그러면 이 조기 종료가 통째로 무너진다(뒤쪽 가지에 더 높은 점수가 있을 수 있다). 노드마다 부분 트리 최대 점수를 들고 우선순위 큐로 내려가는 구조가 필요해진다 — 07번 힙과 만나는 지점이다.\
  (원본에 근거 없음 — 내 추론)
- `countWithPrefix` 가 `keysBelow` 로 O(|prefix|) 인 것과 같은 설계 사상이다 — **답을 세는 일과 답을 만드는 일을 분리한다.**
- `path` 를 `StringBuilder` 하나로 돌려쓰는 것이 핵심 최적화다. 노드마다 `path.toString()` 을 하면 문자열이 노드 수만큼 생긴다.

---

### B. 자료구조 특성

#### 3. 압축 트라이는 왜 필요한가 — 외길 노드가 말해주는 것은 이미 문자열에 있다

**질문**: 09번 트라이에서 `internationalization` 을 넣으면 노드가 20개인데 그중 갈림길이 하나도 없다는 것이 왜 낭비인가. "자식이 하나뿐인 노드가 말해주는 다음 글자는 문자열에 이미 있다"를 설명해 보라.

**낭비의 정체**

```text
 09번 트라이에 "internationalization" 하나만 넣으면

   root -i-> ( ) -n-> ( ) -t-> ( ) -e-> ( ) -r-> ( ) -n-> ( ) -a-> ( ) ...
   노드 20개, 그 중 자식이 2개 이상인 노드 = 0개

 각 노드가 들고 있는 것
   children : TreeMap 하나 (항목 1개)
   end      : boolean
   wordsBelow : int

 노드 하나가 대답할 수 있는 질문
   "여기서 어디로 갈 수 있나?"  ->  "'n' 으로만"

 그런데 그 답은 이미 알고 있다.
   우리는 "internationalization" 이라는 문자열을 손에 들고 찾는 중이다.
   i 다음이 n 이라는 것은 그 문자열의 1번 인덱스를 읽으면 나온다.
   노드는 우리가 이미 아는 것을 다시 말해주려고 40~50바이트를 쓰고 있다.

 정보가 있는 노드는 '선택지가 둘 이상인 곳' 뿐이다.
   거기서만 "어느 쪽으로 갈지"를 자료구조가 알려줄 수 있다.
```

> **갈림길 노드(branching node)** — 자식이 둘 이상인 노드. 여기서만 "어느 쪽으로 가야 하는가"라는 선택이 생긴다.\
> 예: ROMAN 7개에서 `"r"` 노드는 `"om"` 과 `"ub"` 두 자식을 가진 갈림길이다.

> **통과 노드(pass-through node)** — 자식이 하나뿐이고 키도 아닌 노드. 선택지를 주지 않는다.\
> 예: 09번에서 `internationalization` 의 중간 19개 노드가 전부 이것이다. 압축 트라이는 이런 노드를 만들지 않는다.

**같은 키 집합, 두 구조의 노드 수 — 손계산**

09번식 노드 수 = **서로 다른 접두사의 개수**(빈 문자열 제외)다. 압축 노드 수는 `nodeCount()` (뿌리 제외)다.

ROMAN 7개(`romane, romanus, romulus, rubens, ruber, rubicon, rubicundus`)를 하나씩 넣어가며 손으로 센다.

| 넣은 키 | 새로 생기는 09번 접두사 | 09번 누계 | 압축에서 일어나는 일 | 압축 누계 |
|---|---|---|---|---|
| `romane` | r, ro, rom, roma, roman, romane | 6 | 잎 `"romane"` 1개 | 1 |
| `romanus` | romanu, romanus | 8 | `"romane"` → `"roman"`+`"e"`, 잎 `"us"` (+2) | 3 |
| `romulus` | romu, romul, romulu, romulus | 12 | `"roman"` → `"rom"`+`"an"`, 잎 `"ulus"` (+2) | 5 |
| `rubens` | ru, rub, rube, ruben, rubens | 17 | `"rom"` → `"r"`+`"om"`, 잎 `"ubens"` (+2) | 7 |
| `ruber` | ruber | 18 | `"ubens"` → `"ube"`+`"ns"`, 잎 `"r"` (+2) | 9 |
| `rubicon` | rubi, rubic, rubico, rubicon | 22 | `"ube"` → `"ub"`+`"e"`, 잎 `"icon"` (+2) | 11 |
| `rubicundus` | rubicu, rubicun, rubicund, rubicundu, rubicundus | 27 | `"icon"` → `"ic"`+`"on"`, 잎 `"undus"` (+2) | 13 |

- 측정: impl 복제본으로 같은 누계를 확인했다 — 09번 `6, 8, 12, 17, 18, 22, 27` / 압축 `1, 3, 5, 7, 9, 11, 13`.\
  (원본 문서에 없는 수치 — impl 을 복제해 직접 측정한 값이다)
- 논리: **키 하나를 넣을 때마다 압축 노드가 정확히 2개씩 는다** — 쪼갠 자리 하나와 새 잎 하나.\
  이것이 `2n-1` 상한의 정체다(첫 키가 1개, 이후 n-1 개가 2개씩 → 1 + 2(n-1) = 2n-1).\
  ROMAN 은 모든 삽입이 쪼개기라 상한 13을 **정확히 달성**한다.

README 의 한계 표와 테스트가 같은 숫자를 못 박는다.

`/home/jun/project/myway/data-structure/20-radix-trie/src/test/java/com/datastructure/radix/RadixTrieStructureTest.java`

```java
@Test
@DisplayName("긴 단어에 공유 접두사가 없으면 20배 차이가 난다")
void longUnrelatedWords() {
    List<String> words = List.of(
            "internationalization", "counterrevolutionary", "electroencephalogram");
    assertEquals(60, charTrieNodes(words), "글자당 노드 하나면 20 글자 곱하기 3 이다");
    assertEquals(3, build(words).nodeCount(), "압축하면 단어당 노드 하나다");
}
```

| 키 집합 | 09번식 노드 | 압축 노드 | 배율 | 왜 |
|---|---|---|---|---|
| 긴 단어 3개, 공유 접두사 없음 | 60 | 3 | **20배** | 20글자 외길이 전부 간선 하나로 접힌다 |
| 로마 단어 7개 | 27 | 13 | 2.1배 | 갈림길이 여러 층 — 접힐 사슬이 짧다 |
| car, card, care, careful, cars, cat, dog | 13 | 8 | 1.6배 | 키가 짧고 접두사 공유가 많다 |
| a~z 한 글자 26개 | 26 | 26 | **1배** | 누를 사슬이 아예 없다 |

**질문별 답**

- Q: 노드 20개 중 갈림길이 하나도 없다는 것이 왜 낭비인가?\
  A: 노드는 **선택지를 표현하려고** 존재하는데 통과 노드에는 선택지가 없기 때문이다.\
  자식이 하나뿐인 노드는 "다음은 'n' 이다" 한 가지만 말할 수 있고, 그것 때문에 `TreeMap` 한 개와 필드 몇 개(노드당 수십 바이트)를 쓴다.\
  19개 노드가 전부 그러면 그 메모리 전부가 정보 없는 이정표다.

- Q: "자식이 하나뿐인 노드가 말해주는 다음 글자는 문자열에 이미 있다"를 설명해 보라.\
  A: 트라이를 타고 내려갈 때 우리는 찾으려는 문자열을 **손에 들고 있다**.\
  `internationalization` 을 찾는 중이라면 `i` 다음 글자가 `n` 이라는 사실은 그 문자열의 1번 인덱스를 읽으면 나오고, 자료구조에 물을 필요가 없다.\
  자료구조에 물어야 하는 것은 오직 **"내가 가진 글자로 갈 수 있는 길이 있는가, 아니면 다른 길로 갈라지는가"** 이고, 그 질문이 의미를 갖는 곳이 갈림길뿐이다.\
  그래서 외길 구간은 자료구조에서 **간선 라벨이라는 문자열 조각으로 그냥 옮겨 적으면** 되고, 확인은 `startsWith` 한 번으로 끝난다.

**더 생각할 것**

- IDE 가 `com/example/app/service` 처럼 자식이 하나뿐인 패키지 폴더를 한 줄로 접어 보여주는 것이 정확히 같은 조작이다.\
  보여주는 정보량이 같은데 줄 수가 준다.
- 15번 B-트리가 "노드 하나에 키를 여러 개 담아 높이를 낮췄다"면, 여기는 "간선 하나에 글자를 여러 개 담아 노드 수를 낮췄다"다.\
  둘 다 **디스크/메모리 접근 단위에 맞춰 뭉치기**라는 같은 사상이다.
- 그런데 이 뭉치기는 **최악의 경우 전혀 이득이 없다**(질문 7). 15번 B-트리의 이득이 입력과 무관한 것과 다른 점이다.

---

#### 4. 규칙 하나에서 split 과 merge 가 따라 나온다

**질문**: 이 구조 전부를 결정하는 규칙 하나("뿌리가 아닌 노드는 키이거나 갈림길이다")에서 삽입의 **간선 쪼개기**와 삭제의 **다시 합치기**가 어떻게 따라 나오는가. 합치지 않으면 무엇으로 조용히 퇴화하는가.

**규칙에서 두 연산이 나오는 논리**

```text
 규칙 : 뿌리가 아닌 노드 N 에 대해   (N 이 키) 또는 (N 의 자식 수 >= 2)

 삽입이 이 규칙을 깨는 방식
     새 키가 기존 간선의 중간에서 갈라진다고 하자.
     갈라지는 지점에 노드가 있어야 두 갈래를 담을 수 있는데, 지금은 없다.
     그 지점은 새로 만들면 자식이 2개(기존 쪽 + 새 쪽)가 되므로 규칙을 만족한다.
     => 간선을 그 지점에서 쪼개고 새 노드를 끼운다        [split]

     (새 키가 갈라지는 지점에서 끝나면, 그 노드는 '키' 라서 역시 규칙을 만족한다.
      그래서 impl 에 mid.value = value 갈래가 따로 있다.)

 삭제가 이 규칙을 깨는 방식
     갈림길 노드의 자식이 하나로 줄거나, 키였던 노드의 값이 지워진다.
     그러면 그 노드는 키도 아니고 갈림길도 아니게 된다 — 규칙 위반.
     그 노드가 말해주는 것은 "다음 조각은 이것" 하나뿐이고 그건 자식 간선에 이미 있다.
     => 자식 간선을 흡수해 다시 합친다                    [merge]

 즉 split 과 merge 는 서로 다른 두 연산이 아니라
    같은 규칙을 지키기 위한 양방향 보정이다.
```

> **간선 쪼개기(edge split)** — 기존 간선 라벨을 공통 부분과 나머지로 잘라 사이에 노드를 끼우는 삽입 조작.\
> 예: `"romane"` 간선에 `romanus` 를 넣으면 `"roman"` + `"e"` 로 잘리고 `"us"` 가 형제로 붙는다.

> **재병합(merge, `compress`)** — 규칙을 어기게 된 노드가 유일한 자식의 간선을 흡수해 없어지는 삭제 후 조작.\
> 예: `"rom"` → `"an"` 만 남으면 `"roman"` 하나로 합쳐진다.

**삽입의 세 갈래 — impl 코드**

`/home/jun/project/myway/data-structure/20-radix-trie/impl/RadixTrie.java`

```java
int common = commonPrefixLength(child.edge, key, pos);

if (common == child.edge.length()) {
    pos += common;
    cur = child;
    if (isNew) {
        cur.keysBelow++;
    }
    continue;
}

Node<V> mid = new Node<V>(child.edge.substring(0, common));
mid.keysBelow = child.keysBelow;
child.edge = child.edge.substring(common);
mid.children.put(child.edge.charAt(0), child);
cur.children.put(c, mid);
mid.keysBelow++;

if (pos + common == key.length()) {
    mid.value = value;
} else {
    Node<V> leaf = new Node<V>(key.substring(pos + common));
    leaf.value = value;
    leaf.keysBelow = 1;
    mid.children.put(leaf.edge.charAt(0), leaf);
}
return old;
```

```text
 경우가 셋이다 (README: "넣을 때 경우가 셋이고 그중 일부만 맞는 경우가 자르는 자리")

   (가) 자식이 아예 없다            -> 남은 글자 전부로 잎을 만든다. 안 쪼갠다.
   (나) common == edge.length()     -> 간선을 통째로 지나간다. 안 쪼갠다.  (continue)
   (다) 0 < common < edge.length()  -> 여기가 자르는 자리다.

 (다) 안에서 다시 둘로 갈린다 — README 가 "94개 중 18개가 갈린다"고 한 지점

   (다-1) pos + common == key.length()   자른 자리가 곧 새 키의 끝이다
                                         -> mid.value = value      (자른 자리에 값을 둔다)
   (다-2) 아직 남은 글자가 있다           -> 잎을 하나 더 단다
                                         -> mid 는 키가 아니다 (자식 2개로 규칙 만족)
```

**ASCII — `romane` 에 `romanus` 를 넣을 때 (다-2)**

```text
 [전]                                   put("romanus") 진입
   root
     +-- "romane"*                      cur=root, pos=0, c='r'
                                        child.edge = "romane"

 [계산]
   commonPrefixLength("romane", "romanus", 0)
        r o m a n e
        r o m a n u s
        ^ ^ ^ ^ ^ x
        0 1 2 3 4    -> i = 5 에서 'e' != 'u' 로 멈춤 -> common = 5
   common(5) != edge.length()(6)  -> 쪼갠다

 [쪼개는 중]
   mid = new Node("romane".substring(0,5))  = Node("roman")
   mid.keysBelow = child.keysBelow (= 1)
   child.edge = "romane".substring(5)       = "e"
   mid.children['e'] = child
   root.children['r'] = mid                 (덮어쓴다)
   mid.keysBelow++                          (= 2)

   pos + common = 0 + 5 = 5,  key.length() = 7   -> 같지 않다 -> (다-2)
   leaf = new Node("romanus".substring(5))  = Node("us"), value 설정, keysBelow=1
   mid.children['u'] = leaf

 [후]
   root
     +-- "roman"          <- 자른 자리. 키가 아니다 (별표 없음). 자식 2개라 규칙 만족
           +-- "e"*       <- 원래 노드. 간선만 짧아졌다. 값·자식은 그대로
           +-- "us"*      <- 새 잎

   partialMatchSplits 테스트가 못 박는 모양
     List.of("0:", "1:roman", "2:e*", "2:us*")
     주석: "자른 자리 자체는 키가 아니다. 별표가 붙으면 roman 이 키가 돼버린다"
```

**ASCII — `tester` 에 `test` 를 넣을 때 (다-1)**

```text
 [전]
   root
     +-- "tester"*

 [계산]
   commonPrefixLength("tester", "test", 0) = 4   ("test" 가 다 소진됨)
   4 != 6  -> 쪼갠다

 [후]
   mid = Node("test"),  child.edge = "er"
   pos + common = 0 + 4 = 4 == key.length()(4)  -> (다-1)
   mid.value = value                            <- 자른 자리에 값을 둔다

   root
     +-- "test"*        <- 키다. 자식이 하나여도 규칙 만족 (키니까)
           +-- "er"*

 newKeyIsPrefixOfExistingEdge 테스트
   assertEquals(List.of("0:", "1:test*", "2:er*"), shape(of("tester", "test")));
   assertEquals(shape(of("test", "tester")), shape(of("tester", "test")));
        ^ 넣는 순서가 반대여도 모양이 같아야 한다
```

- 논리: (다-1)에서 `mid.value` 를 안 두면 `test` 라는 키가 **조용히 사라진다**.\
  `get("test")` 가 `findNode` 로 `"test"` 노드까지 잘 도착하는데 `value` 가 `null` 이라 "없다"고 답한다. 예외는 안 난다.
- 논리: (다-2)에서 `mid.value` 를 **두면** 없던 키 `roman` 이 생긴다.\
  `keys()` 에 `"roman"` 이 끼고 `size()` 가 하나 커진다. `partialMatchSplits` 의 실패 메시지가 정확히 이것을 경고한다.

**삭제와 병합 — impl 코드**

```java
@Override
public V remove(String key) {
    requireKey(key);
    V old = get(key);
    if (old == null) {
        return null;
    }
    root.keysBelow--;

    Node<V> cur = root;
    int pos = 0;
    while (pos < key.length()) {
        char c = key.charAt(pos);
        Node<V> child = cur.children.get(c);
        child.keysBelow--;
        if (child.keysBelow == 0) {
            cur.children.remove(c);
            compress(cur);
            return old;
        }
        pos += child.edge.length();
        cur = child;
    }
    cur.value = null;
    compress(cur);
    return old;
}

void compress(Node<V> node) {
    if (node == root || node.value != null || node.children.size() != 1) {
        return;
    }
    Node<V> only = node.children.values().iterator().next();
    node.edge = node.edge + only.edge;
    node.value = only.value;
    node.children.clear();
    node.children.putAll(only.children);
}
```

- 논리: `compress` 의 **가드 세 개가 그대로 규칙의 부정**이다.\
  `node == root` — 뿌리는 라벨이 `""` 여야 한다는 별도 전제.\
  `node.value != null` — 키인 노드는 합치면 그 키가 사라진다.\
  `children.size() != 1` — 0개면 위에서 이미 제거됐고, 2개 이상이면 갈림길이라 남아야 한다.
- 논리: 합치는 방향이 **자식을 부모에 흡수**다(부모를 자식에 넣는 게 아니다).\
  부모의 간선에 자식 간선을 이어 붙이고, 자식의 값과 자식들을 부모가 넘겨받는다.
- 논리: `compress` 를 부르는 자리가 **정확히 둘**이다 — 자식을 떼어낸 직후(`cur`)와 값을 지운 직후(`cur`).\
  둘 다 "방금 규칙을 어기게 됐을 수 있는 노드"다.

**ASCII — `romane, romanus, romulus` 에서 `romulus` 를 지울 때**

```text
 [전]  nodeCount() = 5
   root
     +-- "rom"              keysBelow 3
           +-- "an"         keysBelow 2
           |     +-- "e"*   keysBelow 1
           |     +-- "us"*  keysBelow 1
           +-- "ulus"*      keysBelow 1

 [삭제 진행]
   old = get("romulus") -> 있다
   root.keysBelow-- (3 -> 2)
   pos=0, c='r' -> child "rom", keysBelow-- (3 -> 2), 0 아님
        pos += 3 -> 3, cur = "rom"
   pos=3, c=key.charAt(3)='u' -> child "ulus", keysBelow-- (1 -> 0)
        0 이다! -> cur.children.remove('u')
        compress(cur = "rom")

 [compress("rom")]
   node != root         OK
   node.value == null   OK (자른 자리라 키가 아니다)
   children.size() == 1 OK ("an" 하나 남음)
   -> 합친다
      node.edge     = "rom" + "an" = "roman"
      node.value    = "an".value   = null
      node.children = {e, us}

 [후]  nodeCount() = 3
   root
     +-- "roman"
           +-- "e"*
           +-- "us*"

   mergesWhenOneChildLeft 테스트
     assertEquals(List.of("0:", "1:roman", "2:e*", "2:us*"), shape(t),
             "합치지 않으면 rom -> an 이 그대로 남아 09번으로 퇴화한다");
     assertEquals(3, t.nodeCount());

   삽입 때 romulus 가 만든 쪼개기가 정확히 되돌려졌다.
```

**ASCII — `test, tester` 에서 `test` 를 지울 때 (값만 지우는 쪽)**

```text
 [전]
   root
     +-- "test"*          <- 키
           +-- "er"*

 [삭제 진행]
   pos=0, c='t' -> child "test", keysBelow 2 -> 1, 0 아님
        pos += 4 -> 4, cur = "test"
   pos == key.length() -> 루프 종료
   cur.value = null                  <- 값만 지운다
   compress(cur = "test")

 [compress]
   value == null 이 됐고 children.size() == 1  -> 합친다
   edge = "test" + "er" = "tester", value = "er".value, children = {}

 [후]
   root
     +-- "tester"*

   mergesAfterValueCleared 테스트
     assertEquals(List.of("0:", "1:tester*"), shape(t),
             "test 는 더 이상 키가 아니다. 간선을 끊어둘 이유가 없다");
```

**합치지 않으면 무엇으로 퇴화하는가**

```text
 impl 복제본에서 compress 의 본체만 비웠다.
 ROMAN 7개를 넣고 rubicundus 하나만 남기고 전부 지웠다.

   병합 있음 : [0:, 1:rubicundus*]            노드 1개
   병합 없음 : [0:, 1:r, 2:ub, 3:ic, 4:undus*] 노드 4개
   09번식    :                                 노드 10개 (r,ru,rub,rubi,...,rubicundus)

 test/tester 에서 test 만 지우면
   병합 있음 : [0:, 1:tester*]                노드 1개
   병합 없음 : [0:, 1:test, 2:er*]            노드 2개

 방향이 09번 쪽이다. 삭제를 반복할수록 노드가 09번 수치로 수렴한다.
 그런데 답은 하나도 안 틀린다 (질문 9).
```

> **조용한 퇴화(silent degradation)** — 답은 전부 맞는데 성능·공간 특성만 서서히 나빠지는 고장.\
> 예: 병합을 빼먹은 압축 트라이는 `get`·`keys` 가 계속 맞는 답을 내면서 노드 수만 09번 쪽으로 늘어난다.

- 측정: 6000 스텝 무작위 put/remove 후 노드 수 — **병합 있음 690개, 병합 없음 703개** (키 638개).\
  같은 시점 압축 불변식 위반 노드가 **13개**다.\
  (원본 문서에 없는 수치 — impl 을 복제해 직접 측정한 값이다)
- 논리: 이 워크로드에서 차이가 2% 밖에 안 난다는 것이 오히려 무섭다.\
  "성능이 눈에 띄게 나빠지면 알 수 있다"는 기대가 안 통한다 — 위반 노드는 꾸준히 쌓이는데 총량은 완만하게 는다.

**질문별 답**

- Q: 규칙 하나에서 간선 쪼개기가 어떻게 따라 나오는가?\
  A: 새 키가 기존 간선의 **중간**에서 갈라지면 갈라지는 지점에 노드가 필요한데, 압축 상태에서는 그 지점이 간선 안쪽이라 노드가 없기 때문이다.\
  그래서 간선을 `substring(0, common)` 과 `substring(common)` 으로 자르고 사이에 노드를 끼운다.\
  끼운 노드는 자식이 2개(기존 가지 + 새 가지)가 되거나, 새 키가 거기서 끝나면 값을 받아 키가 되므로 어느 쪽이든 규칙을 만족한다.

- Q: 삭제의 다시 합치기는 어떻게 따라 나오는가?\
  A: 삭제는 규칙을 반대 방향으로 깬다 — 갈림길의 자식이 하나로 줄거나, 키였던 노드의 값이 지워지면 그 노드는 **키도 갈림길도 아니게** 된다.\
  그런 노드가 주는 정보("다음 조각은 이것")는 자식 간선에 이미 있으므로, 자식 간선을 흡수해 없앤다.\
  `compress` 의 가드 셋(`root` 아님 · `value == null` · `children.size() == 1`)이 규칙 위반의 정의 그 자체다.

- Q: 합치지 않으면 무엇으로 조용히 퇴화하는가?\
  A: **09번 트라이로** 퇴화한다 — 삭제를 반복할수록 자식 하나짜리 통과 노드가 쌓여 노드 수가 "글자 수 비례" 쪽으로 돌아간다.\
  직접 확인하면 `rubicundus` 하나만 남긴 트리가 노드 1개가 아니라 4개(`r`→`ub`→`ic`→`undus`)로 남는다.\
  중요한 것은 이 퇴화가 **어떤 답도 틀리게 만들지 않는다**는 점이고, 그래서 "조용히"다(질문 9).

**더 생각할 것**

- `split` 과 `merge` 가 정확히 서로의 역연산이라는 것이 `roundTrip` 테스트로 검증된다 — 넣었다 지우면 모양이 원래대로 돌아와야 한다.\
  16번 레드블랙 트리의 회전·재색칠이 삽입/삭제에서 짝을 이루는 것과 같은 구조의 요구다.
- 삽입은 쪼개기를 **한 번만** 한다(쪼개면 바로 `return`). 삭제의 병합도 **한 번만** 한다.\
  연쇄로 위로 전파되지 않는 이유는, 한 번의 put/remove 가 규칙을 깨뜨리는 노드가 최대 하나이기 때문이다.
- `mid.keysBelow = child.keysBelow` 다음에 `mid.keysBelow++` 를 하는 순서가 미묘하다.\
  먼저 자식 것을 물려받고, 새로 들어오는 키 하나를 그 위에 더한다. 순서를 바꾸면 조용히 어긋난다.

---

#### 5. 줄어드는 것은 노드 개수이지 글자가 아니다

**질문**: 간선 라벨의 글자를 전부 더하면 09번의 노드 수와 같다는 것이 뜻하는 바는. 그럼 노드당 하는 일은 어떻게 되는가.

**등식과 그 증명**

```text
 주장 : (압축 트라이 간선 라벨 글자 수의 총합) == (09번 트라이의 노드 수, 뿌리 제외)

 09번 트라이의 노드 = 서로 다른 접두사 하나  (뿌리 = 빈 문자열)
     "romane" 를 넣으면 r, ro, rom, roma, roman, romane 여섯 개

 압축 트라이에서
     뿌리에서 어떤 노드까지의 경로 = 지나온 간선 라벨을 이어 붙인 문자열
     간선 라벨의 글자 하나 = 그 경로 위의 '한 걸음' = 서로 다른 접두사 하나

 두 구조는 같은 키 집합을 담으므로 '서로 다른 접두사의 집합'이 같다.
 09번은 그것을 노드 하나씩으로 표현하고
 압축은 그것을 간선 라벨의 글자 하나씩으로 표현한다.

 => 표현 단위만 다르고 개수는 같다.
```

`/home/jun/project/myway/data-structure/20-radix-trie/src/test/java/com/datastructure/radix/RadixTrieStructureTest.java`

```java
@Test
@DisplayName("노드는 줄지만 저장하는 글자 수는 그대로다")
void charactersAreNotSaved() {
    // 압축은 **노드 개수**를 줄이는 것이지 글자를 줄이는 것이 아니다.
    // 간선 라벨의 글자를 전부 더하면 09번의 노드 수와 같다.
    RadixTrie<String> t = build(RadixTrieTest.ROMAN);
    assertEquals(charTrieNodes(RadixTrieTest.ROMAN), totalEdgeChars(t.root));
}
```

**ROMAN 7개로 손계산**

```text
 romanShape 테스트가 못 박은 모양 (깊이:간선)

   0:            ""            0 글자   (뿌리)
   1:r           "r"           1
   2:om          "om"          2
   3:an          "an"          2
   4:e*          "e"           1
   4:us*         "us"          2
   3:ulus*       "ulus"        4
   2:ub          "ub"          2
   3:e           "e"           1
   4:ns*         "ns"          2
   4:r*          "r"           1
   3:ic          "ic"          2
   4:on*         "on"          2
   4:undus*      "undus"       5
                             ----
   간선 글자 총합                27
   노드 수 (뿌리 제외)           13

 09번식 서로 다른 접두사 (손으로 세기)
   romane      : r ro rom roma roman romane                             6
   romanus     : romanu romanus                                        +2  = 8
   romulus     : romu romul romulu romulus                             +4  = 12
   rubens      : ru rub rube ruben rubens                              +5  = 17
   ruber       : ruber                                                 +1  = 18
   rubicon     : rubi rubic rubico rubicon                             +4  = 22
   rubicundus  : rubicu rubicun rubicund rubicundu rubicundus          +5  = 27

   27 == 27   등식 확인
```

- 측정: impl 복제본으로 확인했다 — `간선 글자 총합 = 27 / 09번 노드 수 = 27 / 압축 노드 수 = 13`.\
  (원본 문서에 없는 수치 — impl 을 복제해 직접 측정한 값이다)

**그럼 무엇이 줄었나 — 글자는 그대로, 노드 껍데기가 줄었다**

| | 09번 트라이 | 압축 트라이 |
|---|---|---|
| 글자를 담는 곳 | 노드 27개의 `children` 키(Character) | 간선 라벨 13개, 글자 총합 27 |
| 노드 객체 | **27개** | **13개** |
| 노드 하나당 딸린 것 | `TreeMap` 1개 + `end` + `wordsBelow` | `String edge` + `TreeMap` 1개 + `value` + `keysBelow` |
| 절약되는 것 | — | **노드 껍데기 14개분** (`TreeMap` 인스턴스 14개 포함) |

- 논리: 절약의 정체는 글자가 아니라 **객체 헤더 + `TreeMap` 인스턴스 + 포인터**다.\
  자바에서 `TreeMap` 빈 인스턴스도 수십 바이트를 쓴다. 노드 수가 반으로 줄면 그만큼이 통째로 사라진다.
- 논리: 대신 `String` 객체가 13개 생긴다 — 09번은 `Character` 를 `TreeMap` 키로 박스했고, 여기는 `String` 을 따로 들고 있다.\
  글자 수가 많이 접힐수록(긴 외길) 이득이 커지고, 안 접히면 `String` 오버헤드만 늘 수도 있다.\
  (원본에 근거 없음 — 내 추론)

**노드당 하는 일**

```text
 09번에서 노드 하나를 지날 때
     children.get(c)      Character 하나로 TreeMap 조회
     비교 1회             (사실상 char 비교 몇 번)

 압축에서 노드 하나를 지날 때
     children.get(c)      Character 하나로 TreeMap 조회    <- 같다
     + s.startsWith(child.edge, pos)                      <- 추가
       = 간선 라벨 길이만큼 char 비교
     + (삽입이면) commonPrefixLength 로 또 한 번 글자 비교
     + (삽입이면) substring 으로 새 String 2~3개 할당

 즉 "노드당 문자 하나 비교" -> "노드당 문자열 조각 비교" 로 바뀌었다.
 총 비교 글자 수는 양쪽이 비슷한데 (둘 다 키 길이 이하)
 압축 쪽에는 메서드 호출과 할당이라는 상수가 붙는다.
```

PrefixMap 주석이 이것을 그대로 적고 있다.

`/home/jun/project/myway/data-structure/20-radix-trie/src/main/java/com/datastructure/radix/PrefixMap.java`

```java
 * | | 09번 트라이 | 압축 트라이 |
 * |---|---|---|
 * | 노드 수 | 서로 다른 접두사 개수 | 최대 2n-1 |
 * | 노드당 비교 | 문자 하나 | 문자열 조각 하나 |
 * | 깊이 | 키 길이 | 갈림길 수 |
 * | 삽입 | 없는 자식을 만든다 | 간선을 쪼갠다 |
 *
 * 공짜가 아니다. 노드는 줄지만 노드당 하는 일이 늘어난다.
```

**질문별 답**

- Q: 간선 라벨의 글자를 전부 더하면 09번의 노드 수와 같다는 것이 뜻하는 바는?\
  A: 압축이 줄인 것은 **정보가 아니라 그것을 담는 노드 껍데기**라는 뜻이다.\
  09번은 "서로 다른 접두사" 하나를 노드 하나로 표현했고, 압축은 같은 것을 간선 라벨의 글자 하나로 표현한다 — 개수는 정확히 같다(ROMAN 7개에서 둘 다 27).\
  그러니 "메모리를 줄인다"는 말은 글자를 줄인다는 뜻이 아니라, 객체 헤더·`TreeMap` 인스턴스·포인터를 줄인다는 뜻이다.\
  키 자체를 압축하는 구조(예: 앞자리 공유 인코딩)와는 성질이 다르다.

- Q: 그럼 노드당 하는 일은 어떻게 되는가?\
  A: **늘어난다.** "문자 하나 비교"가 "문자열 조각 비교"로 바뀐다.\
  조회는 노드마다 `s.startsWith(child.edge, pos)` 를 하고, 삽입은 여기에 `commonPrefixLength` 한 번과 `substring` 할당 2~3개가 더 붙는다.\
  비교하는 **글자 총량**은 양쪽이 비슷하지만(둘 다 키 길이 이하), 압축 쪽에는 메서드 호출·경계 검사·할당이라는 상수가 얹힌다.\
  그래서 "노드 수가 반이 됐으니 두 배 빠르다"는 결론이 나오지 않는다(질문 10).

**더 생각할 것**

- `totalEdgeChars` 를 재는 테스트가 **구조 테스트에만** 있다는 점이 의미심장하다 — 계약으로는 관찰할 수 없는 성질이다.
- 리눅스 `fib_trie` 는 여기서 한 걸음 더 간다 — 간선 라벨을 `String` 으로 들지 않고 "건너뛸 비트 수"만 정수로 들고, 실제 비트는 키에서 읽는다(path compression + level compression).\
  그러면 라벨 저장 비용조차 사라지지만, 그 대신 "건너뛴 구간이 실제로 맞는지"를 잎에서 한 번 더 확인해야 한다.\
  (원본에 근거 없음 — 내 추론)
- 이 등식은 **압축 불변식이 지켜질 때만** 성립한다. 병합을 빼먹으면 노드 수가 늘어나고 간선 라벨이 잘게 쪼개진 채 남는다(글자 총합은 그대로).

---

#### 6. `longestPrefixOf` — 정확히 이것이 아니라 이것을 덮는 가장 구체적인 규칙

**질문**: 09번에 없던 `longestPrefixOf(s)` 는 무엇을 묻는 연산인가 — `containsKey` 가 "정확히 이것"이라면 이것은 무엇인가. 10.1.2.3 이 `0.0.0.0/0` · `10.0.0.0/8` · `10.1.2.0/24` 에 다 걸릴 때 해시맵과 트라이의 조회 횟수가 왜 33 대 1 인가.

**두 질문의 차이**

```text
 containsKey("10.1.2.3")   "이 키가 맵에 정확히 있는가"       -> yes / no
 longestPrefixOf("10.1.2.3")
                           "이 문자열의 접두사 중에서
                            맵에 들어 있는 키가 있는가,
                            있다면 그 중 가장 긴 것은?"       -> 문자열 또는 null

 containsKey 는 '동등' 질의, longestPrefixOf 는 '포함' 질의다.
 전자는 해시맵이 O(1) 로 답하고, 후자는 해시맵이 못 답한다.
 해시맵은 "이 키가 있나"만 답할 수 있고 "이 키를 덮는 키가 있나"는 모른다.
```

> **최장 접두사 매칭(longest prefix match, LPM)** — 주어진 문자열을 덮는 여러 규칙 중 가장 긴(= 가장 구체적인) 것을 고르는 질의.\
> 예: 라우터가 `10.1.2.3` 에 대해 `/0`·`/8`·`/24` 중 `/24` 를 고르는 것.

> **CIDR** — `주소/길이` 형식으로 IP 대역을 적는 표기. 길이는 "앞에서 몇 비트가 이 대역을 정하는가"다.\
> 예: `10.1.2.0/24` 는 앞 24비트가 `000010100000000100000010` 인 모든 주소.

**impl 코드**

`/home/jun/project/myway/data-structure/20-radix-trie/impl/RadixTrie.java`

```java
@Override
public String longestPrefixOf(String s) {
    requireKey(s);
    int best = root.value != null ? 0 : -1;
    Node<V> cur = root;
    int pos = 0;
    while (pos < s.length()) {
        Node<V> child = cur.children.get(s.charAt(pos));
        if (child == null || !s.startsWith(child.edge, pos)) {
            break;
        }
        pos += child.edge.length();
        cur = child;
        if (cur.value != null) {
            best = pos;
        }
    }
    return best < 0 ? null : s.substring(0, best);
}
```

- 논리: **한 번 내려가면서 마지막으로 본 키의 위치를 `best` 에 갱신**한다. 되돌아가지 않는다.
- 논리: 초기값 `best = root.value != null ? 0 : -1` 가 기본 경로(`0.0.0.0/0` = 키 `""`)를 담당한다.\
  뿌리가 키면 무엇을 물어도 최소한 `""` 는 나온다.
- 논리: `!s.startsWith(child.edge, pos)` 로 끊는 것이 중요하다.\
  간선 라벨이 `s` 의 남은 부분과 **부분적으로만** 맞으면 그 아래 키는 전부 `s` 의 접두사가 아니므로 더 갈 이유가 없다.
- 논리: `s.substring(0, best)` 가 답 문자열을 새로 만든다 — 하강 자체는 할당이 없는데 **반환에서 한 번 할당**한다.

**`RoutingTable` 이 이 하나로 돌아간다**

`/home/jun/project/myway/data-structure/20-radix-trie/impl/RoutingTable.java`

```java
public void add(String cidr, String nextHop) {
    ...
    int len = prefixLength(cidr.substring(slash + 1));
    routes.put(toBits(cidr.substring(0, slash)).substring(0, len), nextHop);
}

public String lookup(String ip) {
    String key = routes.longestPrefixOf(toBits(ip));
    return key == null ? null : routes.get(key);
}

static String toBits(String ip) {
    ...
    StringBuilder bits = new StringBuilder(32);
    for (String part : parts) {
        int octet = octet(part, ip);
        for (int b = 7; b >= 0; b--) {
            bits.append((octet >>> b) & 1);
        }
    }
    return bits.toString();
}
```

- 논리: `add` 가 `.substring(0, len)` 으로 **prefix 길이 밖의 비트를 그냥 버린다**. 그것이 마스크를 씌우는 것과 같다.\
  `hostBitsAreMasked` 테스트가 `10.1.2.3/8` 과 `10.0.0.0/8` 이 같은 규칙임을 못 박는다.
- 논리: CIDR 의 "길이"가 곧 **트라이에서의 키 길이**가 된다. 그래서 "더 구체적" = "더 긴 키" = "더 깊은 노드"가 자동으로 성립한다.\
  최장 접두사 매칭이 자료구조의 형태와 정확히 겹친다는 것이 이 구조를 쓰는 이유다.

**10.1.2.3 을 찾는 과정 — 손으로**

```text
 toBits("10.1.2.3")
    10  = 00001010
     1  = 00000001
     2  = 00000010
     3  = 00000011
    -> "00001010000000010000001000000011"   (32 글자)

 등록된 키 (RoutingTableTest.ROUTES)
    0.0.0.0/0      -> ""                                      (길이 0)
    10.0.0.0/8     -> "00001010"                              (길이 8)
    10.1.0.0/16    -> "0000101000000001"                      (길이 16)
    10.1.2.0/24    -> "000010100000000100000010"              (길이 24)
    192.168.0.0/16 -> "1100000010101000"                      (길이 16)

 트라이 모양 (간선 라벨)
    root*                              <- "" 가 키다 (기본 경로)
      +-- "00001010"*                  <- /8   corp
      |     +-- "00000001"*            <- /16  branch
      |           +-- "00000010"*      <- /24  lab
      +-- "1100000010101000"*          <- /16  home

 longestPrefixOf("00001010...0011")
    best = 0                    (root.value != null)
    pos=0  자식 '0' edge "00001010"        startsWith OK -> pos=8,  value!=null -> best=8
    pos=8  자식 '0' edge "00000001"        startsWith OK -> pos=16, value!=null -> best=16
    pos=16 자식 '0' edge "00000010"        startsWith OK -> pos=24, value!=null -> best=24
    pos=24 자식 '0' -> 없다 -> break
    return s.substring(0, 24) = "000010100000000100000010"

    routes.get(그 키) -> "lab"      <- mostSpecific 테스트의 기대값
```

**33 대 1**

```text
 해시맵으로 최장 접두사 매칭을 하려면

   for (int len = 32; len >= 0; len--) {
       String key = bits.substring(0, len);     // 문자열 새로 만들기
       if (map.containsKey(key)) return map.get(key);
   }

   len = 32, 31, 30, ..., 1, 0  ->  33번 조회
   게다가 매 회차마다 substring 으로 문자열을 새로 만들고 해시를 계산한다.
   (문자열 길이 L 의 해시 계산이 O(L) 이라 총 O(32^2) 글자를 훑는다)

   왜 전부 훑어야 하나 : 해시맵은 "있나/없나"만 답한다.
     /24 가 없다고 해서 /16 이 없는 것도 아니고 있는 것도 아니다.
     한 번의 조회로는 다음에 어디를 봐야 할지 아무 정보도 못 얻는다.

 트라이는

   하강 1번 — 뿌리에서 더 갈 수 없을 때까지 내려가며 지나친 키를 기억한다.
   왜 한 번이면 되나 : 트라이의 깊이가 곧 접두사 길이다.
     내려가는 길 위에 있는 노드들이 곧 "이 주소를 덮는 규칙들" 전부이고,
     그것들이 짧은 것부터 긴 것까지 정렬된 채로 놓여 있다.
     마지막에 본 키가 곧 가장 긴 것이다.

 즉 33 대 1 은 '조회 시도 횟수'의 대비다.
 트라이 하강 내부에서도 비트는 최대 32개 비교한다.
 차이는 그 32개를 한 번 훑는가, 33번 겹쳐 훑는가 다.
```

| 방식 | 조회 횟수 | 훑는 글자 수 | 할당 | 왜 |
|---|---|---|---|---|
| 해시맵 + 길이 내림차순 | 33회 | 32+31+…+0 = **528** | `substring` 33개 | 조회 하나가 다음 조회에 정보를 안 준다 |
| 압축 트라이 하강 | **1회** | 최대 32 | 반환 `substring` 1개 | 깊이가 곧 접두사 길이라 길이순 정렬이 공짜 |

`longestPrefixIsCheap` 성능 테스트가 "키 수가 아니라 길이에만 의존한다"를 20초 제한으로 못 박는다(10만 키에 20만 질의).

**32자 문자열을 쓰는 대가**

```text
 실제 라우터/커널이 하는 것          이 구현이 하는 것
 --------------------------------  --------------------------------
 int (4바이트) 하나                 String 32글자
 addr & mask  (명령 1개)            s.startsWith(edge, pos) (루프)
 addr >>> (32-len)                  s.substring(0, len)     (새 객체)
 비교 = XOR + 시프트                char 비교 32회
 할당 0                             lookup 1회당 String 2개

 lookup("10.1.2.3") 한 번에 생기는 객체 (impl 기준)
   1. toBits 안의 StringBuilder(32)         <- 버려짐
   2. bits.toString() 의 String 32글자      <- 질의 키
   3. longestPrefixOf 의 s.substring(0,24)  <- 답 키
   (+ ip.split("\\.", -1) 이 String[] 과 String 4개)

 게다가 lookup 은 트라이를 두 번 내려간다
   routes.longestPrefixOf(bits)   <- 1차 하강, 키 문자열을 얻는다
   routes.get(key)                <- 2차 하강, 그 키로 값을 다시 찾는다
   longestPrefixOf 가 값을 같이 돌려줬다면 한 번이면 됐다.
```

- 논리: 그래도 32자 문자열을 쓰는 이유는 **`RadixTrie` 가 문자열 맵이기 때문**이다.\
  비트를 `'0'`/`'1'` 문자로 펴면 IP 라우팅이 문자열 트라이 문제로 그대로 환원된다 — 새 자료구조를 안 만들어도 된다.
- 논리: 대가는 상수다 — 비트 1개당 1바이트(문자), 마스크 연산 1개 대신 루프, 할당 0 대신 질의당 여러 개.\
  "학습용 구현"과 "커널 구현"이 갈리는 정확한 지점이다.
- 측정: `toBits("10.1.2.3")` = `00001010000000010000001000000011`, `/8` 키 = `00001010`, `/24` 키 = `000010100000000100000010`.\
  (원본 문서에 없는 수치 — impl 을 복제해 직접 측정한 값이다. `toBits` 기대값 자체는 `RoutingTableTest.octets` 에도 있다)

**질문별 답**

- Q: `longestPrefixOf(s)` 는 무엇을 묻는 연산인가 — `containsKey` 가 "정확히 이것"이라면 이것은 무엇인가?\
  A: **"이것을 덮는 가장 구체적인 규칙"** 을 묻는다.\
  `containsKey` 는 동등 질의라 답이 yes/no 이고, `longestPrefixOf` 는 포함 질의라 답이 "맵에 있는 키 중 `s` 의 접두사이면서 가장 긴 것"이라는 **문자열**이다.\
  해시맵은 이 질문에 구조적으로 못 답한다 — "이 키가 있나"는 알지만 "이 키를 덮는 키가 있나"는 모른다.

- Q: 10.1.2.3 이 셋에 다 걸릴 때 해시맵과 트라이의 조회 횟수가 왜 33 대 1 인가?\
  A: 해시맵은 길이 32부터 0까지 **가능한 접두사를 전부 만들어 물어봐야** 하기 때문이다(33개 길이).\
  조회 하나가 실패해도 다음에 어디를 봐야 할지 알려주지 않으므로 줄일 수가 없고, 매번 `substring` 과 해시 계산이 붙어 총 528글자를 훑는다.\
  트라이는 **깊이가 곧 접두사 길이**라서, 뿌리에서 한 번 내려가는 길 위에 `""`·`/8`·`/16`·`/24` 가 짧은 것부터 순서대로 놓여 있다.\
  내려가며 마지막으로 본 키를 기억하면 그게 답이라 하강 한 번(비트 최대 32회 비교)으로 끝난다.

- Q: `RoutingTable` 이 int·시프트 대신 32자 문자열을 쓰는 대가는?\
  A: 비트 하나가 1바이트 문자가 되어 키가 4바이트 대신 32바이트가 되고, 마스크 연산 한 개로 끝날 비교가 `startsWith` 루프가 된다.\
  `lookup` 한 번에 `StringBuilder`·`toString`·`split` 결과·답 `substring` 이 생기고, 게다가 `longestPrefixOf` 로 키를 찾은 뒤 `get` 으로 **한 번 더 내려간다**.\
  얻는 것은 "IP 라우팅이 문자열 트라이 문제로 그대로 환원된다"는 단순함이고, 그래서 이 구현은 학습용이다.

**더 생각할 것**

- `lookup` 이 트라이를 두 번 내려가는 것은 계약의 한계다 — `longestPrefixOf` 가 키만 돌려주기 때문이다.\
  실무 인터페이스라면 `Entry<String, V> longestPrefixEntry(String s)` 를 두었을 것이다.\
  (원본에 근거 없음 — 내 추론)
- 앞자리 0 거부(`010.0.0.1` 을 튕긴다)는 자료구조와 무관한 **파서 결정**이다.\
  `023` 을 8진수 19로 읽는 구현이 실제로 있어서 같은 문자열이 라이브러리마다 다른 주소가 된다 — "답이 갈리는 입력은 아예 안 받는다".
- URL 라우터(`/api/users/:id` 같은)도 같은 구조다. 다만 거기서는 와일드카드 세그먼트 때문에 "가장 긴 것"이 아니라 "가장 구체적인 것"의 정의가 복잡해진다.

---

#### 7. 최악의 입력과 최선의 입력 — 누를 사슬이 없으면 그냥 트라이다

**질문**: a부터 z까지 한 글자 26개를 넣으면 노드 수가 09번과 어떻게 되는가. "누를 사슬이 없으면 압축 트라이는 그냥 트라이"라는 한계에서, 이 구조가 이기는 조건은 무엇인가. 반대로 최선의 입력은.

**a~z 26개 — 손계산**

```text
 키 : "a", "b", "c", ..., "z"   (26개, 전부 길이 1)

 압축 트라이
     put("a") : root 에 'a' 자식이 없다 -> 잎 Node("a") 를 단다.
     put("b") : root 에 'b' 자식이 없다 -> 잎 Node("b") 를 단다.
     ...
     쪼갤 일이 한 번도 없다 (공통 접두사가 아예 없으니 common 계산에 갈 일이 없다)

     root
       +-- "a"*  +-- "b"*  +-- "c"*  ...  +-- "z"*

     전체 노드 = 뿌리 1 + 잎 26 = 27개
     nodeCount() = countNodes(root) - 1 = 27 - 1 = 26개   (뿌리를 뺀 값)

 09번식 (서로 다른 접두사 개수)
     "a" 의 접두사 : a
     "b" 의 접두사 : b
     ...
     서로 다른 접두사 = 26개                               = 26개

 26 == 26.  이득이 정확히 0 이다.
```

`/home/jun/project/myway/data-structure/20-radix-trie/src/test/java/com/datastructure/radix/RadixTrieStructureTest.java`

```java
@Test
@DisplayName("한 글자 키만 있으면 이득이 아예 없다")
void singleCharKeys() {
    List<String> words = new ArrayList<>();
    for (char c = 'a'; c <= 'z'; c++) {
        words.add(String.valueOf(c));
    }
    // 누를 사슬이 없다. 압축 트라이가 항상 이기는 것이 아니다.
    assertEquals(26, charTrieNodes(words));
    assertEquals(26, build(words).nodeCount());
}
```

- 논리: 이 경우 압축 트라이는 09번과 **모양이 완전히 같은데 코드만 복잡하다**.\
  게다가 노드마다 길이 1짜리 `String` 을 따로 들고 있어서 메모리는 오히려 더 쓴다.\
  (원본에 근거 없음 — 내 추론)
- 측정: impl 복제본에서 `a~z 한 글자 26개 -> 09번 26 / 압축 26`.\
  (원본 문서에 없는 수치 — impl 을 복제해 직접 측정한 값이다. README 한계 표와 `singleCharKeys` 테스트에도 같은 값이 있다)

**이기는 조건 — 비율로 보기**

```text
 09번 노드 수 P = 서로 다른 접두사 개수
 압축 노드 수 C <= 2n - 1        (n = 키 수)

 이득 = P / C

 P 는 '키 길이의 합' 쪽으로 커지고 (공유가 없으면 정확히 그것)
 C 는 '키 개수' 쪽에 갇힌다 (길이와 무관하게 2n-1 이 상한)

 => 이득 ~= (평균 키 길이) / 2    ... 공유가 거의 없을 때

 확인
   긴 단어 3개, 공유 없음 : P=60, C=3      평균 길이 20, 20/2 = 10 ... 실제 20배
                                          (전부 잎이라 C = n = 3, 2n-1 을 안 채운다)
   로마 단어 7개          : P=27, C=13     27/13 = 2.1
   car..dog 7개           : P=13, C=8      13/8 = 1.6
   한 글자 26개           : P=26, C=26     1.0

 이기는 조건 한 줄
     키가 길고, 갈림길이 드물다.
     = 평균 키 길이가 크고, 키 하나가 만드는 노드가 2개(쪼갠 자리 + 잎)에 머문다.
```

| | 최악 | 중간 | 최선 |
|---|---|---|---|
| 입력 | 짧은 키가 빽빽하게 갈라짐 (a~z 한 글자) | 로마 단어 7개 | 긴 키에 공통 사슬이 김 |
| 09번 노드 | 26 | 27 | 60 |
| 압축 노드 | 26 | 13 | 3 |
| 배율 | **1.0배** | 2.1배 | **20배** |
| 왜 | 누를 사슬이 0 | 갈림길이 여러 층 | 20글자 외길이 통째로 접힘 |

- 논리: `2n-1` 상한이 "키 하나당 노드 2개"라는 뜻이라 **키 길이가 비용에 안 들어온다**.\
  이것이 이 구조의 핵심 성질이고, 동시에 "키가 짧으면 이득이 없다"의 이유이기도 하다.
- 논리: 상한 `2n-1` 을 실제로 채우는 것은 **모든 삽입이 쪼개기인 경우**다(ROMAN 7개 → 정확히 13).\
  공유 접두사가 아예 없으면 모든 삽입이 (가)갈래라 노드가 n 개뿐이다(긴 단어 3개 → 3).
- 측정: 무작위 키 2000개(길이 0~7, 알파벳 {a,b,c})를 넣으면 노드 740개, 키 689개 → `2n-1 = 1377` 에 한참 못 미친다.\
  알파벳이 좁아 공유가 많으면 쪼개기보다 통과가 많아지기 때문이다.\
  (원본 문서에 없는 수치 — impl 을 복제해 직접 측정한 값이다)

**질문별 답**

- Q: a~z 한 글자 26개를 넣으면 노드 수가 09번과 어떻게 되는가?\
  A: **정확히 같다.** 뿌리 1개 + 잎 26개 = 27개이고, 뿌리를 빼는 `nodeCount()` 기준으로 26개다.\
  09번식 "서로 다른 접두사 개수"도 26개다.\
  공통 접두사가 하나도 없어서 쪼개기가 한 번도 일어나지 않고, 눌러 담을 외길 사슬도 없기 때문이다.

- Q: 이 구조가 이기는 조건은 무엇인가?\
  A: **키가 길고 갈림길이 드물 때**다.\
  09번 노드 수는 "서로 다른 접두사 개수"라 키 길이에 비례해 커지는데, 압축 노드 수는 `2n-1` 로 **키 개수에 갇혀 있다** — 길이가 비용에 안 들어온다.\
  그래서 이득은 대략 "평균 키 길이 / 2" 쪽으로 가고, 키가 짧아질수록 1배로 수렴한다.

- Q: 반대로 최선의 입력은?\
  A: **긴 키에 갈림길이 거의 없는 경우** — 극단이 "긴 단어 3개, 공유 접두사 없음"이다.\
  `internationalization`·`counterrevolutionary`·`electroencephalogram` 은 09번에서 60개 노드인데 압축에서는 **3개**다(단어당 잎 하나).\
  20글자 외길이 통째로 간선 하나로 접혀 20배 차이가 난다. URL 경로·파일 경로·IP 비트열이 실무에서 이 성질을 갖는 대표적 입력이다.

**더 생각할 것**

- IP 라우팅이 이 구조의 최선 사례인 이유가 여기 있다 — 키가 32비트(=32글자)로 **길고**, 실제 등록된 규칙 수에 비하면 갈림길이 드물다.
- 최악 사례를 피하려면 알파벳을 바꾸면 된다. 비트 단위 트라이(`0`/`1` 두 갈래)는 사슬이 길어져 압축 효과가 커진다.\
  대신 깊이가 8배가 되므로, 압축 없이는 못 쓴다 — 압축이 그 구조를 성립시키는 전제다.\
  (원본에 근거 없음 — 내 추론)
- 29번 open-addressing 이 "짧은 키를 빽빽하게"에 강하다. 최악 입력 영역이 서로 반대라서 실무에서는 둘을 섞어 쓴다.

---

#### 8. 접두사가 간선 중간에서 끝나는 경우 — 09번에 없던 함정

**질문**: 접두사가 **간선 중간에서** 끝나는 경우가 09번에는 없던 이유는. `romane` 만 있을 때 `keysWithPrefix("rom")` 이 멈출 노드가 없는데 답은 있는 상황을 어떻게 처리하는가 — 경로 관리의 함정은 무엇인가.

**09번에는 왜 없었나**

```text
 09번 : 간선 하나 = 글자 하나
        길이 k 접두사를 따라가면 정확히 k 번째 노드에 선다.
        그 노드는 항상 존재한다 (키가 그 접두사로 시작하기만 하면).
        => findNode(prefix) 가 항상 "경로가 정확히 prefix 인 노드"를 준다

 20번 : 간선 하나 = 문자열 조각
        접두사가 간선의 중간에서 끝날 수 있다.
        그 자리는 노드가 아니다. 압축 불변식이 거기에 노드를 두는 것을 금지한다
        (자식 하나짜리 통과 노드가 되니까).
        => "멈출 노드가 없는데 답은 있는" 상황이 생긴다
```

**`romane` 하나만 있을 때**

```text
   root
     +-- "romane"*

   keysWithPrefix("r")       -> ["romane"]    'r' 은 간선 중간
   keysWithPrefix("rom")     -> ["romane"]    'rom' 도 간선 중간
   keysWithPrefix("roman")   -> ["romane"]    여기도
   keysWithPrefix("romane")  -> ["romane"]    딱 맞는다
   keysWithPrefix("rome")    -> []            'rom' 까지 맞다가 'e' vs 'a' 로 갈림
   keysWithPrefix("romanes") -> []            간선보다 접두사가 길다

   prefixEndsInsideAnEdge 테스트가 이 여섯 줄을 그대로 못 박는다.
```

**`prefixRoot` 가 하는 세 가지 판정**

```java
Node<V> prefixRoot(String prefix, StringBuilder path) {
    Node<V> cur = root;
    int pos = 0;
    while (pos < prefix.length()) {
        Node<V> child = cur.children.get(prefix.charAt(pos));
        if (child == null) {
            return null;
        }
        if (prefix.length() - pos < child.edge.length()) {
            if (!child.edge.startsWith(prefix.substring(pos))) {
                return null;
            }
            path.append(child.edge);
            return child;
        }
        if (!prefix.startsWith(child.edge, pos)) {
            return null;
        }
        path.append(child.edge);
        pos += child.edge.length();
        cur = child;
    }
    return cur;
}
```

```text
 남은 접두사 길이 r = prefix.length() - pos,  간선 길이 e = child.edge.length()

  (1) 자식이 없다                 -> null            "그런 시작 글자로 가는 길이 없다"
  (2) r <  e   간선이 더 길다     -> 간선 중간에서 끝난다
                                     edge.startsWith(남은 접두사) 인지 본다
                                     맞으면 그 자식을 시작점으로, path 에 간선 전체를 append
                                     틀리면 null
  (3) r >= e   접두사가 더 길다   -> prefix.startsWith(edge, pos) 인지 본다
                                     맞으면 간선을 소진하고 계속 내려간다
                                     틀리면 null

 (2)에서 비교 방향이 뒤집힌다.
   평소   : prefix 안에 edge 가 들어 있나   (prefix.startsWith(edge, pos))
   (2)에서: edge 안에 prefix 나머지가 있나  (edge.startsWith(prefix.substring(pos)))
 이 뒤집힘이 09번에 없던 코드다.
```

> **경로 누적기(path accumulator)** — 재귀가 내려가며 지나온 간선 라벨을 이어 붙여 두는 `StringBuilder`.\
> 예: `collect` 가 `path.append(child.edge)` 로 붙이고 돌아올 때 `setLength` 로 정확히 그 길이만큼 되돌린다.

**경로 관리의 함정 — 세 가지**

```text
 함정 1 : path 를 prefix 로 시작하면 안 된다

   09번  collectUpTo(start, new StringBuilder(prefix), out, k)      <- 맞다
   20번  StringBuilder path = new StringBuilder();
         Node start = trie.prefixRoot(prefix, path);                <- 비워서 넘긴다

   "romane" 에서 prefix="rom" 일 때
     잘못  : path = "rom",  거기서 자식이 없으니 결과 = ["rom"]     <- 없는 키다!
     맞음  : path = "romane" (prefixRoot 가 간선 전체를 붙였다) -> ["romane"]

 함정 2 : (2)번 갈래에서 간선을 잘라서 붙이면 안 된다

     path.append(child.edge)                        <- 간선 전체
     path.append(prefix.substring(pos))             <- 이러면 "rom" 만 붙는다 (틀림)

   시작 노드의 실제 경로가 prefix 보다 길기 때문이다.

 함정 3 : 되돌릴 때 한 글자가 아니라 간선 길이만큼

     09번  path.deleteCharAt(path.length() - 1)
     20번  path.setLength(path.length() - child.edge.length())

   한 글자만 떼면 다음 형제 가지의 키 이름이 앞에 쓰레기를 달고 나온다.
   조용히 틀린다 — 예외가 안 난다.
```

**`countWithPrefix` 는 왜 같은 `prefixRoot` 로 O(|prefix|) 인가**

```java
@Override
public int countWithPrefix(String prefix) {
    requireKey(prefix);
    Node<V> start = prefixRoot(prefix, new StringBuilder());
    return start == null ? 0 : start.keysBelow;
}
```

> **`keysBelow`** — 그 노드를 뿌리로 하는 부분 트리에 들어 있는 키의 개수를 미리 세어 둔 값.\
> 예: ROMAN 7개에서 `"ub"` 노드의 `keysBelow` 는 4다(rubens, ruber, rubicon, rubicundus).

```text
 간선 중간에서 끝나는 접두사에서도 답이 맞는 이유

   "romane" 하나 있을 때 countWithPrefix("rom")
     prefixRoot 가 (2)번 갈래로 "romane" 노드를 준다
     그 노드의 keysBelow = 1
     -> 1

   왜 맞나 : 간선 중간에서 끝나는 접두사로 시작하는 키의 집합 =
             그 간선을 넘어간 노드 아래의 키 집합
             (간선 중간에서는 갈라질 수 없으므로 두 집합이 정확히 같다)

   ROMAN 에서 concreteValues 테스트의 값들
     countWithPrefix("")        = 7    뿌리
     countWithPrefix("r")       = 7    간선 "r" 을 딱 소진 -> "r" 노드
     countWithPrefix("rom")     = 3    "r" 다음 "om" 을 소진 -> "om" 노드
     countWithPrefix("roman")   = 2    "om" 다음 "an" 을 소진 -> "an" 노드
     countWithPrefix("rub")     = 4    "r" 다음 "ub" 를 소진 -> "ub" 노드
     countWithPrefix("rubic")   = 2    "ub" 다음 "ic" 를 소진 -> "ic" 노드
     countWithPrefix("z")       = 0    자식 없음 -> null
```

- 논리: `prefixRoot` 를 `keysWithPrefix`·`countWithPrefix`·`autocomplete` **셋이 공유**한다.\
  간선 중간 판정이라는 까다로운 로직이 한 곳에만 있어서, 틀려도 셋이 같이 틀린다(= 테스트가 잡기 쉽다).
- 논리: `midEdgePrefixCoversMany` 테스트가 "간선 중간의 접두사가 여럿을 덮기도 한다"를 따로 본다 — `keysWithPrefix("rube")` = `["rubens", "ruber"]`.\
  `"rube"` 는 `"ub"` 노드 아래 `"e"` 간선을 딱 소진하는 경우라 사실 (3)번 갈래다. 이름과 달리 중간이 아니다.

**질문별 답**

- Q: 접두사가 간선 중간에서 끝나는 경우가 09번에는 없던 이유는?\
  A: 09번은 **간선 하나가 글자 하나**라 길이 k 접두사를 따라가면 항상 k번째 노드에 정확히 설 수 있었기 때문이다.\
  압축 트라이는 간선 하나에 글자가 여럿이라 접두사가 간선 안쪽에서 끝날 수 있고, 그 자리에는 노드가 없다 — 압축 불변식이 거기에 통과 노드를 두는 것을 금지한다.

- Q: 멈출 노드가 없는데 답은 있는 상황을 어떻게 처리하는가?\
  A: `prefixRoot` 가 **간선을 넘어간 노드**를 시작점으로 돌려준다.\
  "남은 접두사 길이 < 간선 길이"이면 비교 방향을 뒤집어 `child.edge.startsWith(prefix.substring(pos))` 를 보고, 맞으면 그 자식을 반환한다.\
  간선 중간에서는 갈라질 수 없으므로 "그 접두사로 시작하는 키 집합"과 "그 노드 아래의 키 집합"이 정확히 같아서 답이 맞는다.

- Q: 경로 관리의 함정은 무엇인가?\
  A: 셋이다.\
  (1) `path` 를 `new StringBuilder(prefix)` 로 시작하면 안 된다 — 시작 노드의 실제 경로가 접두사보다 **길 수 있다**. 그래서 `prefixRoot` 가 `path` 를 출력 인자로 채워 준다.\
  (2) 간선 중간 갈래에서 `path` 에 **간선 전체**를 붙여야 한다. 접두사 부분만 붙이면 그 아래 키 이름이 잘린다.\
  (3) 되돌릴 때 한 글자가 아니라 `child.edge.length()` 만큼 `setLength` 해야 한다.\
  셋 다 예외를 안 내고 **답만 틀리는** 종류다.

**더 생각할 것**

- `findNode` 는 이 문제를 안 겪는다 — `get`/`containsKey` 는 "정확히 이 키"라 간선을 넘어 도착하면 그건 다른 키다.\
  그래서 `findNode` 에는 (2)번 갈래가 없고 `!key.startsWith(child.edge, pos)` 면 바로 `null` 이다.
- `longestPrefixOf` 도 (2)번 갈래가 없다 — 간선을 다 소진해야 그 노드가 키가 되므로, 중간에서 끊기면 그 아래는 볼 필요가 없다.\
  세 순회 함수가 각자 다른 이유로 다른 판정을 쓴다는 것이 이 챕터에서 제일 헷갈리는 지점이다.
- 28번 rope 가 같은 문제를 반대쪽에서 겪는다 — "i번째 글자"가 노드 경계와 안 맞는 것. 거기서도 "경계 안쪽 위치"를 다루는 코드가 본체다.

---

#### 9. 삭제 후 병합을 계약 테스트가 못 잡는다

**질문**: 병합을 빼면 `get` · `keys` · `keysWithPrefix` · `countWithPrefix` · `longestPrefixOf` 가 전부 맞는 답을 내고 TreeMap 대조 6000스텝도 통과한다. 그럼 무엇이 깨지고, 그것을 잡으려면 어떤 종류의 테스트가 필요한가.

**직접 확인 — `compress` 본체를 비운 변종**

impl 을 scratchpad 에 복제하고 `compress` 의 본체만 비웠다(호출은 그대로 둔 채).

```text
 변종 :   void compress(Node<V> node) { /* 병합을 일부러 뺐다 */ }

 RadixTrieTest.RandomCrossCheck.matchesTreeMap 과 같은 조건
 (seed 20260814L, 6000 스텝, 키 길이 0~6, 알파벳 {a,b,c}, 4분의 1 확률로 remove)

   put/remove 반환값·size·get 불일치 = 0
   keys() 가 TreeMap keySet 과 일치   = true
   keysWithPrefix/countWithPrefix 일치 = true   ("", a, ab, abc, b, cc, z)
   longestPrefixOf 2000 질의 전수 대조 = true

   -> 계약은 하나도 안 깨진다.

 같은 시점의 내부 상태
   압축 불변식 위반 노드 수 = 13
   노드 수 = 703 (병합 있음은 690), 키 수 = 638
```

- 측정: 위 여섯 줄 전부 impl 복제본으로 직접 얻은 값이다.\
  (원본 문서에 없는 수치 — impl 을 복제해 직접 측정한 값이다)
- 논리: 계약이 안 깨지는 이유는 **모든 순회가 "간선 라벨을 이어 붙인 경로"로 키 이름을 만들기 때문**이다.\
  `"roman"` 이 한 노드든 `"rom"` → `"an"` 두 노드든 이어 붙이면 똑같이 `"roman"` 이다.\
  값이 없는 통과 노드는 `collect` 가 건너뛰고(`node.value != null` 검사), `keysBelow` 도 정확히 유지된다.\
  즉 **키 집합과 값이 통과 노드의 존재에 전혀 의존하지 않는다.**

**무엇이 깨지는가 — 구조 테스트로 확인**

`RadixTrieStructureTest` 의 검사들을 같은 변종에 직접 돌렸다.

```text
 FAIL mergesWhenOneChildLeft(shape)
      기대 [0:, 1:roman, 2:e*, 2:us*]
      실제 [0:, 1:rom, 2:an, 3:e*, 3:us*]
 FAIL mergesWhenOneChildLeft(nodeCount)   기대 3   실제 4
 FAIL mergesAfterValueCleared(shape)
      기대 [0:, 1:tester*]
      실제 [0:, 1:test, 2:er*]
 FAIL keepsBranchingNode
      기대 [0:, 1:rom, 2:an, 3:e*, 3:us*, 2:ulus*]
      실제 [0:, 1:r, 2:om, 3:an, 4:e*, 4:us*, 3:ulus*]
 PASS keepsNodeThatIsStillAKey      (value != null 이라 원래도 안 합친다)
 PASS rootIsNeverMerged             (뿌리는 원래도 안 합친다)
 PASS roundTrip                     (이 시나리오는 값이 남는 노드라 병합이 안 일어난다)

 그리고 불변식 테스트
 FAIL heldThroughRandomOps          seed 777L, step 550 의 검사 지점에서 위반 1개
                                    3000 스텝 끝에서 위반 10개
 PASS nodeCountBound                삭제가 없어 위반이 안 생긴다 (노드 740 <= 2n-1 = 1377)
```

- 측정: 위 PASS/FAIL 판정과 step 550, 위반 10개·13개는 impl 복제본으로 직접 얻은 값이다.\
  (원본 문서에 없는 수치 — impl 을 복제해 직접 측정한 값이다)
- ⚠️ **원본 README 와 어긋나는 자리**: README 는 "깨진 것은 구조 테스트 3개뿐이었습니다(94개 중 91개 통과)"라고 적는다.\
  내가 복제해 돌린 결과로는 **4개**가 깨진다 — 병합 테스트 3개(`mergesWhenOneChildLeft`·`mergesAfterValueCleared`·`keepsBranchingNode`)와 불변식 테스트 `heldThroughRandomOps`.\
  `roundTrip` 은 README 가 짐작하기 쉬운 후보지만 실제로는 **통과**한다(`rubicundusx` 를 지울 때 부모가 키라 원래도 병합이 안 일어난다).\
  **코드 기준으로 4개**로 읽는다. 어느 쪽이든 결론("구조를 직접 봐야 잡힌다")은 같다.

**그것을 잡는 테스트의 종류**

> **계약 테스트(contract test)** — 공개 API 가 약속한 입출력만 검증하는 테스트. 내부를 안 본다.\
> 예: `assertEquals(List.of("romane","romanus"), t.keysWithPrefix("roman"))`.

> **구조 테스트(structure test)** — 자료구조의 내부 표현 자체를 직접 검증하는 테스트.\
> 예: 노드 수를 세거나, 트리 모양을 문자열로 펴서 비교하거나, 불변식을 재귀로 확인하는 것.

`RadixTrieStructureTest` 의 클래스 주석이 이 구분을 그대로 선언한다.

`/home/jun/project/myway/data-structure/20-radix-trie/src/test/java/com/datastructure/radix/RadixTrieStructureTest.java`

```java
/**
 * 내부 구조를 직접 본다.
 *
 * 계약만으로는 압축이 풀렸는지를 못 잡는다.
 * 간선을 안 쪼개고 한 글자씩 노드를 만들어도, 삭제 후 안 합쳐도 답은 전부 맞다.
 * 그래서 09번으로 조용히 퇴화한다. 여기서 그것을 잡는다.
 */
```

잡는 방식이 **세 종류**다.

```java
/** 트리를 "깊이:간선(키면 *)" 줄로 편다. 자식은 사전순, 뿌리 포함. */
static List<String> shape(RadixTrie<String> t) {
    List<String> out = new ArrayList<>();
    walk(t.root, 0, out);
    return out;
}

private static void walk(RadixTrie.Node<String> node, int depth, List<String> out) {
    out.add(depth + ":" + node.edge + (node.value != null ? "*" : ""));
    for (RadixTrie.Node<String> c : node.children.values()) {
        walk(c, depth + 1, out);
    }
}
```

```java
/**
 * 압축 불변식 셋.
 *   1. 뿌리가 아닌 노드의 간선은 비어 있지 않다
 *   2. 뿌리가 아닌 노드는 키이거나 갈림길이다 (자식 하나짜리 사슬이 없다)
 *   3. keysBelow 가 실제 아래 키 수와 같다
 */
static int verify(RadixTrie.Node<String> node, String path, boolean isRoot) {
    if (!isRoot) {
        assertFalse(node.edge.isEmpty(), "'" + path + "' 의 간선이 비었다");
        assertTrue(node.value != null || node.children.size() >= 2,
                "'" + path + "' 는 키도 아니고 갈림길도 아니다. 압축이 풀렸다");
    }
    int actual = node.value != null ? 1 : 0;
    for (RadixTrie.Node<String> c : node.children.values()) {
        actual += verify(c, path + c.edge, false);
    }
    assertEquals(actual, node.keysBelow, "'" + path + "' 의 keysBelow 가 실제와 다르다");
    if (!isRoot) {
        assertTrue(actual > 0, "'" + path + "' 아래에 키가 없는데 노드가 남아 있다");
    }
    return actual;
}
```

| 검사 종류 | 무엇을 보나 | 어디 있나 | 병합 누락을 잡나 |
|---|---|---|---|
| 모양 문자열 대조 | `깊이:간선(키면 *)` 줄 목록 전체 | `shape` + `Merging` 테스트 6개 | **예** (3개가 FAIL) |
| 노드 수 세기 | `nodeCount()` 의 정확한 값 | `mergesWhenOneChildLeft` 등 | **예** (3 대신 4) |
| 불변식 재귀 검증 | 자식 하나뿐인 비키 노드가 있나 + `keysBelow` | `Invariants.verify` | **예** (step 550 에서 FAIL) |
| 상한 검증 | `nodeCount() <= 2n-1` | `nodeCountBound` | 아니오 (삭제가 없다) |
| TreeMap 대조 6000스텝 | 키 집합·값·개수 | `RadixTrieTest.matchesTreeMap` | **아니오** |

- 논리: 세 검사 중 **불변식 재귀 검증이 가장 강하다**.\
  모양 대조는 시나리오를 사람이 손으로 고른 것이라 빠뜨린 경우가 생기지만(`roundTrip` 이 그 예다), `verify` 는 **아무 상태에서나 규칙을 직접 물어본다**.\
  무작위 3000 스텝 위에 얹으면 사람이 상상 못 한 삭제 순서까지 커버한다.
- 논리: 잡는 조건이 "규칙을 한 문장으로 적을 수 있는가"다.\
  "뿌리가 아닌 노드는 키이거나 갈림길이다"를 코드로 한 줄(`node.value != null || node.children.size() >= 2`)로 옮길 수 있으니 검사할 수 있다.
- 논리: 이 챕터가 주는 일반 교훈은 **"밖에서 안 보이는 성질은 안을 봐야 잡힌다"** 이고, 그 대가는 테스트가 내부 표현에 결합된다는 것이다.\
  `shape` 는 `Node.edge`·`Node.value`·`children` 에 직접 의존하므로 구현을 바꾸면 테스트도 바꿔야 한다.

**질문별 답**

- Q: 병합을 빼면 왜 계약이 전부 통과하는가?\
  A: 모든 순회가 키 이름을 **간선 라벨을 이어 붙여** 만들기 때문이다.\
  `"roman"` 이 노드 하나든 `"rom"`→`"an"` 두 개든 이어 붙이면 똑같이 `"roman"` 이고, 값 없는 통과 노드는 `collect` 가 `node.value != null` 로 건너뛴다.\
  `keysBelow` 도 정확히 유지되므로 `countWithPrefix` 도 맞고, `longestPrefixOf` 는 "값이 있는 노드"만 보므로 통과 노드가 몇 개든 답이 같다.\
  직접 돌려 보면 6000스텝 TreeMap 대조에서 불일치가 0이다.

- Q: 그럼 무엇이 깨지는가?\
  A: **압축 불변식** — "뿌리가 아닌 노드는 키이거나 갈림길이다"가 깨진다.\
  키도 갈림길도 아닌 통과 노드가 쌓여서 `"roman"` 이 `"rom"`→`"an"` 으로, `"rubicundus"` 가 `"r"`→`"ub"`→`"ic"`→`"undus"` 로 남는다.\
  결과는 09번 트라이로의 **조용한 퇴화**다 — 노드 수와 메모리·간접 참조가 늘지만 어떤 답도 안 틀린다.\
  6000스텝 뒤 위반 노드 13개, 노드 수 703 대 690이었다.

- Q: 그것을 잡으려면 어떤 종류의 테스트가 필요한가?\
  A: **내부 구조를 직접 보는 테스트**다. 세 방식이 있다.\
  (1) 트리를 `깊이:간선(키면 *)` 문자열 목록으로 펴서 통째로 대조하기(`shape`).\
  (2) `nodeCount()` 의 정확한 값을 못 박기(3 대신 4가 나오면 FAIL).\
  (3) 불변식을 재귀로 직접 검증하기 — `assertTrue(node.value != null || node.children.size() >= 2, "키도 아니고 갈림길도 아니다. 압축이 풀렸다")`.\
  이 중 (3)을 무작위 연산 위에 얹은 `heldThroughRandomOps` 가 가장 강하다. 사람이 고른 시나리오가 아니라 아무 상태에서나 규칙을 물어보기 때문이다.

**더 생각할 것**

- 같은 종류의 함정이 `remove` 자체에도 있다. `keysBelow` 만 줄이고 노드를 안 끊어도 `keys()` 는 맞는다(`collect` 가 값 없는 노드를 건너뛰니까).\
  그래서 `verify` 의 마지막 줄이 `assertTrue(actual > 0, "아래에 키가 없는데 노드가 남아 있다")` 로 그것까지 본다.
- 16번 레드블랙 트리도 같은 구조의 문제를 갖는다 — 색 규칙을 어겨도 `get`/`keys` 는 전부 맞고 높이만 나빠진다.\
  거기서도 "블랙 높이가 모든 경로에서 같은가"를 재귀로 직접 확인하는 테스트가 따로 있었다.
- README 한계 3 이 같은 계열의 또 다른 이야기다 — `common >= 1` 이 보장되므로 `common == 0` 처리를 넣어도 94개가 다 통과한다.\
  자식을 간선의 **첫 글자**로 찾았으니 공통 길이가 최소 1이라, 그 가지는 **도달할 수 없다**.\
  "테스트가 다 통과한다"가 "코드가 필요하다"의 증거가 아니라는 반대 방향의 예다.

---

#### 10. 걸음 수를 세지 시간을 재지 않는다

**질문**: 노드당 `substring` 할당과 문자열 비교가 붙어 짧은 키에서는 오히려 느릴 수 있는데, 이 문제집이 "걸음 수를 세지 시간을 재지 않는다"는 것이 무엇을 못 보게 하는가. `RoutingTable` 이 int·시프트 대신 32자 문자열을 쓰는 대가는.

**이 문제집의 성능 테스트가 하는 일**

```text
 RadixTrieTest.Performance / RadixTrieProblemsTest 의 성능 테스트 넷

   manyKeys                 @Timeout(20)  10만 개를 넣고 전부 찾는다
   countDoesNotWalkSubtree  @Timeout(20)  10만 질의 x countWithPrefix("a")
   longestPrefixIsCheap     @Timeout(20)  20만 질의 x longestPrefixOf
   stopsEarly               @Timeout(20)  10만 질의 x autocomplete(k=10)

 이것들이 판정하는 것
   "전체를 훑는 구현(O(m))인가, 안 훑는 구현(O(k) / O(|prefix|))인가"
   = 점근 차수가 하나 다른가

 이것들이 판정하지 못하는 것
   같은 차수 안에서의 상수 배 차이.
   10만 질의가 2초 걸리든 6초 걸리든 똑같이 PASS 다.
   3배가 조용히 통과한다.
```

- 논리: `@Timeout` 은 **측정이 아니라 관문**이다. 값을 남기지 않고 통과/실패만 남긴다.\
  그래서 "09번보다 빠른가"라는 질문에 이 문제집은 **답을 갖고 있지 않다**.

**못 보게 하는 것 — 네 가지**

```text
 (1) substring 할당

   put 한 번이 (다)갈래에 들어가면
       child.edge.substring(0, common)      새 String 1
       child.edge.substring(common)         새 String 2
       key.substring(pos + common)          새 String 3   (다-2 일 때)
   삽입 10만 번이면 문자열 수십만 개가 생겼다 사라진다.

   09번은? 노드를 만들지만 문자열은 안 만든다 (char 를 TreeMap 키로 박싱할 뿐).
   걸음 수로 세면 압축이 유리한데, 할당으로 세면 방향이 뒤집힐 수 있다.

   조회 경로에도 하나 있다 — prefixRoot 의 prefix.substring(pos)
   (간선 중간 갈래에서만. 매 질의마다는 아니다)
   longestPrefixOf 의 s.substring(0, best) 는 매 질의마다 하나 만든다.

 (2) 문자열 비교의 상수

   09번  children.get(c)                    Character 하나 비교
   20번  children.get(c) + s.startsWith(edge, pos)
                                            메서드 호출 + 경계 검사 + 루프
   비교하는 글자 총량은 비슷한데 (둘 다 키 길이 이하)
   호출/분기 오버헤드가 노드마다 한 번씩 더 붙는다.
   키가 짧으면 이 상수가 전부다.

 (3) 캐시 지역성

   노드 수가 반이 되면 포인터 추적(pointer chasing)이 반이 된다  <- 이득
   그런데 간선 라벨이 별도 String 객체라 노드를 읽고 또 한 번 뛰어야 한다  <- 손해
   순 효과가 어느 쪽인지는 재봐야 아는데, 이 문제집은 안 잰다.

 (4) TreeMap<Character, Node> 의 비용

   자식이 평균 2개인데 TreeMap 을 쓴다 (빨강-검정 트리 + Character 박싱).
   자식이 2개면 배열 2칸이 훨씬 싸다.
   사전순 순회를 공짜로 얻으려고 낸 값인데, 그 값이 얼마인지는 안 잰다.
```

> **캐시 지역성(cache locality)** — 연속으로 접근하는 데이터가 메모리에서 가까이 있어 캐시 한 줄에 같이 올라오는 성질.\
> 예: 배열 순회는 지역성이 좋고, 노드마다 포인터를 따라가는 트리 순회는 나쁘다.

> **도달할 수 없는 가지(unreachable branch)** — 실행 경로상 절대 참이 될 수 없는 조건 분기.\
> 예: 자식을 간선 첫 글자로 찾았으니 `common == 0` 은 일어날 수 없는데, 그 처리를 넣어도 테스트 94개가 전부 통과한다.

**`RoutingTable` 의 대가 — 다시 숫자로**

| | 실무(int + 시프트) | 이 구현(32자 문자열) |
|---|---|---|
| 키 크기 | 4바이트 int | `String` 32글자 (헤더 포함 약 56바이트) |
| 마스크 씌우기 | `addr & mask` 명령 1개 | `substring(0, len)` 새 객체 1개 |
| 접두사 비교 | `(a ^ b) >>> (32-len) == 0` | `startsWith(edge, pos)` 루프 |
| 하강 1회 비용 | 비트 연산 몇 개 | char 최대 32회 비교 |
| `lookup` 1회 할당 | 0 | `StringBuilder` + `toString` + `split` 배열 + 답 `substring` |
| `lookup` 하강 횟수 | 1 | **2** (`longestPrefixOf` 후 `get`) |

```text
 lookup("10.1.2.3") 한 번을 따라가며 세기

   toBits("10.1.2.3")
     ip.split("\\.", -1)        String[] 1개 + String 4개
     new StringBuilder(32)      1개
     루프 32회 append           (char 32개)
     bits.toString()            String 1개  (32글자)

   routes.longestPrefixOf(bits)
     하강 : 노드 4개 방문, startsWith 로 비트 24개 비교
     s.substring(0, 24)         String 1개

   routes.get(key)
     하강 : 노드 3개 재방문, startsWith 로 비트 24개 다시 비교     <- 중복 작업

   합계 : String 객체 약 7개, 비트 비교 48회, 하강 2회
   실무 구현이라면 : 할당 0, 비트 연산 십여 개, 하강 1회
```

- 논리: 그래도 이 선택이 **교육적으로는 옳다**.\
  "IP 라우팅 = 문자열 최장 접두사 매칭"이라는 환원을 보여주는 것이 목적이고, 그러려면 새 자료구조 없이 `RadixTrie` 를 그대로 써야 한다.
- 논리: 대가를 **말로 적어 두는 것**이 이 문제집의 방식이다 — README 한계 2가 "측정하지 않습니다"라고 명시한다.\
  안 재는 것을 안 잰다고 적는 것이, 안 재놓고 빠르다고 주장하는 것보다 낫다.

**질문별 답**

- Q: "걸음 수를 세지 시간을 재지 않는다"가 무엇을 못 보게 하는가?\
  A: **같은 점근 차수 안의 상수 배 차이**를 전부 못 보게 한다.\
  성능 테스트는 전부 `@Timeout(20)` 관문이라 "전체를 훑는 구현인가 아닌가"만 갈라내고, 2초든 6초든 똑같이 통과한다.\
  구체적으로 (1) `put` 이 쪼갤 때마다 만드는 `substring` 2~3개와 `longestPrefixOf` 가 질의마다 만드는 `substring` 1개, (2) `startsWith` 호출·경계 검사라는 노드당 상수, (3) 간선 라벨이 별도 `String` 객체라 노드 하나 읽는 데 포인터를 두 번 따라가는 캐시 특성, (4) 자식이 평균 2개인데 `TreeMap` + `Character` 박싱을 쓰는 비용 — 넷 다 안 보인다.\
  그래서 "짧은 키에서는 09번보다 느릴 수 있다"는 README 의 말은 **추정이지 측정이 아니다**.

- Q: `RoutingTable` 이 int·시프트 대신 32자 문자열을 쓰는 대가는?\
  A: 키가 4바이트에서 32글자 문자열(헤더 포함 수십 바이트)이 되고, 마스크 한 번이면 끝날 일이 `substring` 새 객체가 되고, 비트 비교 한 번이 `startsWith` 루프가 된다.\
  `lookup` 한 번에 `split` 배열 + `StringBuilder` + `toString` + 답 `substring` 으로 문자열이 예닐곱 개 생기고, 게다가 `longestPrefixOf` 로 키를 찾은 뒤 `get` 으로 **같은 길을 한 번 더 내려간다**(비트 24개를 두 번 비교한다).\
  얻는 것은 "새 자료구조 없이 `RadixTrie` 하나로 IP 라우팅이 된다"는 환원의 명료함이다.

**더 생각할 것**

- 제대로 재려면 JMH 같은 벤치마크 도구가 필요하고, 그러면 JIT 워밍업·GC·분기 예측을 통제해야 한다.\
  이 문제집이 그걸 안 하는 것은 **범위를 그은 것**이지 빠뜨린 것이 아니다.
- 그래도 싸게 얻을 수 있는 숫자는 있다 — `put` 이 만든 `String` 개수를 세는 것 정도는 걸음 수 세기와 같은 방식이다.\
  "할당 수"는 시간과 달리 결정적이라 테스트로 못 박을 수 있다.\
  (원본에 근거 없음 — 내 추론)
- 19번 확률적 카운팅도 같은 종류의 정직함을 요구했다 — "오차가 이 범위다"를 재지 않으면 아무것도 주장할 수 없다.\
  여기서는 반대로 "안 쟀으니 주장하지 않는다"를 택했다.

---

#### 11. 21-suffix-array 로의 연결 — 트리를 만들지 않고 배열 하나로

**질문**: 09번 문제 3이 남긴 숙제("모든 접미사를 트라이에 넣으면 노드가 n(n+1)/2 개라 n=10만이면 못 만든다")를 21번은 어떻게 푸는가. **트리를 만들지 않고 배열 하나로** 같은 질문에 답한다는 것이 무슨 뜻인가.

**20번이 그 숙제를 못 푸는 이유**

```text
 09번 문제 3 : 서로 다른 부분 문자열 수 = 접미사를 전부 트라이에 넣고 노드를 센다
     "abc" 의 접미사 : abc, bc, c
     노드 수 = 서로 다른 부분 문자열 수 = 6

 n = 100,000 이면
     노드 n(n+1)/2 = 50억 개. 노드 40바이트로 쳐도 200GB. 못 만든다.

 20번(압축)으로 줄면 되지 않나?
     압축 트라이의 노드 수 <= 2n - 1 = 199,999 개.  줄긴 준다.
     실제로 그것이 '접미사 트리(suffix tree)' 이고 O(n) 공간이다.

 그런데 이 챕터의 답은 "글자 수는 안 줄어든다" 였다 (질문 5).
     간선 라벨의 글자를 전부 더하면 09번 노드 수 = n(n+1)/2 = 50억 글자.
     -> 라벨을 String 으로 들고 있으면 압축을 해도 못 만든다.

 진짜 접미사 트리는 라벨을 (시작, 끝) 인덱스 쌍으로 들어 O(n) 으로 만든다.
 즉 압축 트라이의 아이디어를 끝까지 밀면 접미사 트리에 도달하는데,
 그러려면 '문자열을 복사하지 않고 원본의 구간으로 가리킨다' 는 한 걸음이 더 필요하다.
 (원본에 근거 없음 — 내 추론)
```

**21번이 택하는 길 — 트리를 아예 버린다**

`/home/jun/project/myway/data-structure/21-suffix-array/README.md`

```
접미사를 사전순으로 정렬하되 남기는 것은 **시작 위치 숫자뿐**입니다.
문자열은 하나도 새로 만들지 않습니다. O(n) 공간의 정체입니다.
```

> **접미사 배열(suffix array)** — 문자열의 모든 접미사를 사전순으로 정렬한 뒤 **시작 위치만** 담은 정수 배열.\
> 예: `banana` 의 접미사를 정렬하면 `a`(5), `ana`(3), `anana`(1), `banana`(0), `na`(4), `nana`(2) → 배열 `[5,3,1,0,4,2]`.

> **LCP 배열(longest common prefix array)** — 정렬된 이웃 두 접미사가 앞에서 몇 글자까지 같은지를 담은 배열.\
> 예: `banana` 면 `[0, 1, 3, 0, 0, 2]`.

```text
 저장 단위 비교 (README 표)

   길이 1000        09번 접미사 트라이        접미사 배열
   저장 단위        노드 500,500개            int 1,000개
   길이 10만        노드 5,000,050,000개      400,000 바이트

 "트리를 만들지 않고 배열 하나로" 가 뜻하는 것

   트리가 하던 일             배열이 대신하는 방법
   ------------------------  ----------------------------------------
   공통 접두사를 '경로 공유'  정렬해서 '이웃'으로 만든다
   로 표현                    (같은 접두사를 가진 접미사끼리 붙어 선다)

   갈림길 노드가 "여기까지     LCP 배열의 값이 "이웃 둘이 몇 글자까지
   같다"를 표현               같은가"를 숫자로 표현

   부분 문자열 찾기 = 하강     부분 문자열 찾기 = 이진 탐색
   O(m)                       O(m log n)

   노드를 세서 부분 문자열 수  뺄셈으로 구한다
                              n(n+1)/2 - sum(lcp)
```

**같은 질문, 두 가지 답 — `banana` 로 손계산**

```text
 "banana" (n = 6)

 [09번 트라이 방식]  접미사를 전부 넣고 노드를 센다
     banana, anana, nana, ana, na, a
     만들어지는 노드 = 서로 다른 부분 문자열 하나당 하나
     -> 답 15 (그리고 노드가 실제로 15개 생긴다)

 [21번 배열 방식]  정렬하고 이웃끼리 뺀다
     정렬된 접미사      시작 위치   이웃과의 LCP
       a                    5            0
       ana                  3            1     ("a" 가 같다)
       anana                1            3     ("ana" 가 같다)
       banana               0            0
       na                   4            0
       nana                 2            2     ("na" 가 같다)

     sa  = [5, 3, 1, 0, 4, 2]
     lcp = [0, 1, 3, 0, 0, 2]

     서로 다른 부분 문자열 수
       = n(n+1)/2 - sum(lcp)
       = 6*7/2 - (0+1+3+0+0+2)
       = 21 - 6
       = 15                               <- 같은 답

     만든 것 : int 배열 두 개(길이 6). 노드 0개. 새 문자열 0개.
```

- 논리: 이 뺄셈의 의미는 "전체 (접미사, 접두사 길이) 쌍에서 **중복으로 센 것**을 뺀다"다.\
  `n(n+1)/2` 는 모든 부분 문자열을 중복 포함해 센 값이고, `sum(lcp)` 는 이웃과 겹쳐서 이미 센 개수다.\
  정렬해 두면 "중복은 반드시 이웃 사이에서만 생긴다"가 성립해서 이웃만 보면 된다.
- 논리: 09번은 **중복 제거를 자료구조가** 해줬고(같은 경로는 같은 노드), 21번은 **정렬이** 해준다.\
  트리가 하던 일을 순서가 대신한다.
- 논리: 대가는 README 가 적은 그대로 **직관**이다 — "트라이는 그림이 그려지는데 접미사 배열은 안 그려진다".\
  그리고 조회가 O(m) 하강에서 O(m log n) 이진 탐색이 된다(길이 10만에서 33번 찔러본다).

**세 챕터를 한 줄로**

```text
 09  전부 담는다        노드 = 서로 다른 접두사 개수      n^2 에서 터진다
 20  껍데기를 줄인다    노드 <= 2n-1, 글자는 그대로       라벨을 String 으로 들면 여전히 n^2
 21  트리를 버린다      int 배열 2개, 새 문자열 0개       O(n) 공간, 대신 직관을 버린다

 "같은 질문에 답하는 표현을 바꾼다" 가 세 챕터를 관통한다.
   09 -> 20 : 표현 단위를 노드에서 간선 라벨로
   20 -> 21 : 표현 자체를 트리에서 정렬된 인덱스 배열로
```

**질문별 답**

- Q: 09번 문제 3이 남긴 숙제를 21번은 어떻게 푸는가?\
  A: **접미사를 저장하지 않는다.** 접미사를 사전순으로 정렬하되 남기는 것은 시작 위치 정수뿐이라 공간이 O(n) 이다.\
  길이 1000 이면 노드 500,500개 대신 int 1,000개이고, 길이 10만이면 노드 50억 개 대신 400,000바이트다.\
  거기에 LCP 배열(이웃한 두 접미사가 앞에서 몇 글자까지 같은가)을 얹으면 09번 문제 3의 답이 **뺄셈 한 줄**이 된다 — `n(n+1)/2 - sum(lcp)`.

- Q: "트리를 만들지 않고 배열 하나로" 같은 질문에 답한다는 것이 무슨 뜻인가?\
  A: 트리가 **경로 공유**로 표현하던 "공통 접두사"를, 배열이 **정렬된 이웃 관계**로 표현한다는 뜻이다.\
  트라이에서는 같은 접두사를 가진 키가 같은 경로를 지나가서 갈림길 노드가 "여기까지 같다"를 알려줬다면, 접미사 배열에서는 같은 접두사를 가진 접미사끼리 정렬 결과에서 **나란히 서고** LCP 값이 "몇 글자까지 같은가"를 숫자로 알려준다.\
  중복 제거를 자료구조 대신 **순서**가 해주는 것이다.\
  대가는 두 가지다 — 그림이 안 그려진다는 직관의 상실, 그리고 조회가 O(m) 하강에서 O(m log n) 이진 탐색이 된다는 것.

**더 생각할 것**

- 20번의 아이디어를 끝까지 밀면 **접미사 트리**(라벨을 문자열이 아니라 원본의 (시작, 끝) 인덱스로 드는 압축 트라이)가 되고 그것도 O(n) 공간이다.\
  21번이 배열을 택하는 이유는 공간이 아니라 **구현 난이도와 상수**다 — 접미사 트리는 만들기가 훨씬 어렵고 포인터가 많다.\
  (원본에 근거 없음 — 내 추론)
- "문자열을 복사하지 않고 원본 구간으로 가리킨다"는 아이디어는 28번 rope 에서도 나온다.\
  20번이 `substring` 으로 라벨을 **복사한** 것이 이 챕터의 학습용 단순화였다는 뜻이기도 하다.
- 21번의 `n(n+1)/2 - sum(lcp)` 는 길이 10만에서 답이 49억이라 **`int` 로는 담기지도 않는다**.\
  09번에서는 자료구조가 먼저 터졌는데, 21번에서는 자료구조가 버티고 **답의 크기**가 새 제약이 된다.

---

## 정리 — 이 챕터가 못 박는 것

| 질문 | 한 줄 답 |
|---|---|
| 1 | 압축 불변식 덕에 LCP 는 뿌리 자식의 간선 라벨 그 자체다 — 비용이 준 게 아니라 읽는 자리가 바뀌었다 |
| 2 | 조기 종료가 비용을 매칭 수 m 에서 출력 수 k 로 옮긴다 — 인터페이스로는 못 푼다 |
| 3 | 자식 하나짜리 노드는 우리가 이미 아는 것을 다시 말해준다 |
| 4 | "키이거나 갈림길" 규칙 하나가 split 과 merge 를 양방향 보정으로 만든다 |
| 5 | 간선 글자 총합 = 09번 노드 수(ROMAN 에서 27) — 줄어든 건 노드 껍데기다 |
| 6 | 깊이가 곧 접두사 길이라 최장 접두사 매칭이 하강 한 번이다 (해시맵은 33번) |
| 7 | 이득 ≈ 평균 키 길이 / 2 — 한 글자 키만 있으면 09번과 똑같다(26 대 26) |
| 8 | 접두사가 간선 중간에서 끝나면 노드가 없다 — `prefixRoot` 가 경로까지 같이 돌려준다 |
| 9 | 병합 누락은 계약을 하나도 안 깬다 — 불변식을 재귀로 직접 물어봐야 잡힌다 |
| 10 | `@Timeout` 은 관문이지 측정이 아니다 — 상수 배 차이는 전부 안 보인다 |
| 11 | 트리가 경로 공유로 하던 일을 배열은 정렬된 이웃 관계로 한다 |
