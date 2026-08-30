# data-structure/21-suffix-array — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 구현 — NaiveSuffixArray (`src/main/java/com/datastructure/suffix/NaiveSuffixArray.java`)

<!-- 메서드마다 내 언어로. 복잡도는 "왜 그런지"까지. -->

### `필드`

- `String text` 역할:
- `int[] sa` 역할:
- `long charComparisons` 역할(무엇을 재려고 있는가):

### `public NaiveSuffixArray(String text)`

- 하는 일:
- 논리:
- 비용(왜):

### `int compareSuffixes(int i, int j)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `public int[] toArray()` / `public int size()` / `public long charComparisons()` / `public static int[] of(String text)`

- 하는 일:
- 비용(왜):

## 구현 — SuffixArray (`src/main/java/com/datastructure/suffix/SuffixArray.java`)

### `필드`

- `String text` 역할:
- `int[] sa` 역할(접미사를 저장하지 않고 시작 위치만 남긴다는 것):
- `int sortRounds` 역할:
- `int searchProbes` 역할:

### `public SuffixArray(String text)` — 배가법 본체 (TODO)

- 하는 일:
- 논리(k 를 2배씩 늘리며 정렬 · 순위가 이미 k 글자를 요약한다는 것 · 종료 조건):
- 비용(왜):

### `static int[] initialRanks(String text)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `static int comparePair(int[] rank, int i, int j, int k)` (TODO)

- 하는 일:
- 논리(범위 밖을 -1 로 봐야 하는 이유 — `a` 가 `ab` 보다 앞인 이유):
- 비용(왜):

### `static int[] reRank(int[] sa, int[] rank, int k)` (TODO)

- 하는 일:
- 논리(같은 쌍끼리 같은 순위로 묶어야 하는 이유):
- 비용(왜):

### `int comparePrefix(int start, String pattern)`

- 하는 일:
- 논리:
- 비용(왜):

### `int lowerBound(String pattern)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `int upperBound(String pattern)` (TODO)

- 하는 일:
- 논리(lowerBound 와 딱 한 글자 다른 이유):
- 비용(왜):

### `public List<Integer> find(String pattern)` (TODO)

- 하는 일:
- 논리(찾은 위치를 그대로 주면 안 되는 이유 — 사전순이라 banana 의 `a` 는 5,3,1 순):
- 비용(왜):

### `public boolean contains(String pattern)` / `public int count(String pattern)`

- 하는 일:
- 비용(왜):

### `public int size()` / `public String text()` / `public int[] toArray()` / `public String suffixAt(int rank)`

- 하는 일:
- 비용(왜):

### `public int sortRounds()` / `public int lastSearchProbes()` / `public long memoryBytes()`

- 하는 일:
- 논리(측정용으로 열어둔 것들):
- 비용(왜):

## 구현 — LcpArray (`src/main/java/com/datastructure/suffix/LcpArray.java`)

### `필드`

- `String text` 역할:
- `int[] sa` 역할:
- `int[] lcp` 역할(이웃한 두 접미사가 앞에서 몇 글자까지 같은가):
- `long charComparisons` 역할:

### `public LcpArray(SuffixArray suffixArray)` / `public LcpArray(String text, int[] suffixArray)`

- 하는 일:
- 비용(왜):

### `public static int[] inverse(int[] suffixArray)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `private int[] kasai()` (TODO)

- 하는 일:
- 논리(순위 순서가 아니라 **원문 순서**로 훑는 이유 · h 를 0 으로 되돌리지 않는 이유):
- 비용(왜 O(n) 인가):

### `public static int[] build(String text, int[] suffixArray)`

- 하는 일:
- 비용(왜):

### `public int size()` / `public int get(int rank)` / `public int[] toArray()`

- 하는 일:
- 비용(왜):

### `public long sum()` / `public int max()` / `public int argMax()` / `public long charComparisons()`

- 하는 일:
- 논리(각각 어떤 문제의 답이 되는가):
- 비용(왜):

## 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| 09번 접미사 트라이 | | | |
| NaiveSuffixArray (비교 정렬) | | | |
| SuffixArray (배가법) | | | |
| 기수 정렬 / SA-IS | | | |

## 문제 — SuffixArrayProblems (`src/main/java/com/datastructure/suffix/SuffixArrayProblems.java`)

> 셋 다 접미사 배열 없이도 풀린다. 다만 길이 10만에서는 그 방법들이 안 돌아간다.
> 상수 `SEPARATOR = (char) 1` — 두 문자열을 이을 때 끼우는 구분자. 유일해야 하는 것이 절대 조건이다.

### 문제 1. 서로 다른 부분 문자열 개수 — `static long countDistinctSubstrings(String s)`

> 문제 설명: 문자열 s 의 서로 다른 부분 문자열 개수를 센다. (빈 문자열은 세지 않는다)
> 09번 문제 3번과 같은 문제다. 거기서는 모든 접미사를 트라이에 밀어 넣고 만들어진 노드를 셌다.
> 답은 맞지만 노드가 최대 n(n+1)/2 개라 길이 10만이면 50억 개가 필요해 아예 못 만든다.
> 여기서는 뺄셈 한 번이다.
>
> ```
>   전체 부분 문자열 개수(중복 포함) = n(n+1)/2
>   중복해서 센 것                  = sum(lcp)
> ```
>
> 왜 sum(lcp) 인지 보라. 접미사 하나가 부분 문자열 (길이)개를 만든다.
> 사전순으로 이웃한 접미사끼리는 앞 lcp 글자로 시작하는 것들이 겹친다.
> 정렬해 두면 겹치는 상대가 바로 앞 하나뿐이라 한 번씩만 빼면 된다.
> (s 가 null 이거나 비었으면 0)

- 내 접근:
- 논리:
- 비용(왜):

### 문제 2. 가장 긴 반복 부분 문자열 — `static String longestRepeatedSubstring(String s)`

> 문제 설명: 두 번 이상 나오는 가장 긴 부분 문자열. 없으면 빈 문자열.
> 겹쳐도 두 번으로 센다. `"aaa"` 에서 `"aa"` 는 위치 0 과 1 에 있다.
> 답이 여럿이면 사전순으로 앞선 것을 준다.
> (s 가 null 이거나 2글자 미만이면 빈 문자열)

- 내 접근:
- 논리:
- 비용(왜):

### 문제 3. 두 문자열의 가장 긴 공통 부분 문자열 — `static String longestCommonSubstring(String a, String b)`

> 문제 설명: a 와 b 에 둘 다 들어 있는 가장 긴 부분 문자열. 없으면 빈 문자열.
> 답이 여럿이면 사전순으로 앞선 것을 준다.
> a 나 b 가 null 이면 거부하고, 둘 중 하나가 비었으면 빈 문자열이다.
> 생각할 것: 그냥 `a + b` 로 이으면 경계가 사라진다. a = `"a"`, b = `"aa"` 를 이으면 `"aaa"` 가 되고
> 경계를 넘는 접미사 쌍이 `"aa"` 를 공통이라고 보고하는데 **a 에는 `"aa"` 가 없다.**
> 그래서 입력에 구분자가 들어 있으면 거부해야 한다 — 유일하지 않으면 보장이 깨진다.

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

- README: `/home/jun/project/myway/data-structure/21-suffix-array/README.md`
- 구현: `/home/jun/project/myway/data-structure/21-suffix-array/src/main/java/com/datastructure/suffix/`
- 테스트: `/home/jun/project/myway/data-structure/21-suffix-array/src/test/java/com/datastructure/suffix/`
- 정답 구현: `/home/jun/project/myway/data-structure/21-suffix-array/impl/`
