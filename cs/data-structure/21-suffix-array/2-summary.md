# data-structure/21-suffix-array — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 구현 — NaiveSuffixArray (`src/main/java/com/datastructure/suffix/NaiveSuffixArray.java`)

<!-- 메서드마다 내 언어로. 복잡도는 "왜 그런지"까지. -->

### 구조

```
접미사 배열 = "모든 접미사를 사전순으로 세운 뒤, 시작 인덱스만 남긴 int 배열"

text = "banana"  (n = 6, 0-base)

[1] 접미사 6개를 늘어놓는다 (i = 시작 자리. 길이 n 짜리 문자열 n 개가 아니라 자리 n 개)
        i    접미사
        0    banana
        1    anana
        2    nana
        3    ana
        4    na
        5    a

[2] 사전순으로 정렬한다                    [3] 시작 인덱스만 남긴다
        r    접미사                              r     0  1  2  3  4  5
        0    a                                  sa   [ 5, 3, 1, 0, 4, 2 ]
        1    ana            ->
        2    anana                          sa[r] = "사전순 r 번째 접미사가 시작하는 자리"
        3    banana                                 (순위 -> 원문 위치)
        4    na
        5    nana

    문자열은 하나도 복사하지 않는다. 저장하는 것은 int[] 하나뿐 = 4n 바이트
    "접미사" 는 text 와 시작 인덱스만 있으면 언제든 다시 볼 수 있는 것이라, 굳이 담지 않는다
```

### 동작 — 정렬

```
compareSuffixes(i, j) : 두 접미사를 첫 글자부터 한 글자씩 맞대어 본다

    i = 1  "anana"    a  n  a  n  a
    j = 3  "ana"      a  n  a
                      =  =  =            3 글자까지 같고 짧은 쪽이 먼저 끝났다
                                         -> 글자로는 결판이 안 난다

    결판이 안 나면 남은 길이로 정한다 : Integer.compare(n - i, n - j) = compare(5, 3) > 0
        한쪽이 다른 쪽의 접두사면 짧은 쪽이 사전순 앞 ("ana" < "anana")

    i = 0  "banana"   b ...
    j = 1  "anana"    a ...
                      ^ 첫 글자에서 갈린다 -> 1 글자만 보고 끝

비용
    비교 1회가 최악 O(n) 글자 (두 접미사가 길게 겹칠수록 오래 본다)
    정렬이 비교를 O(n log n) 회 부른다
    -> 전체 O(n^2 log n).  charComparisons() 가 실제로 맞대어 본 글자 수를 센다
    "aaaa...a" 처럼 겹침이 심한 입력에서 최악이 그대로 나온다
```

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

### 구조

```
배가법(doubling) : 이미 매긴 순위를 재료로 써서 비교 길이를 라운드마다 2배로 늘린다

    rank[i] = "i 에서 시작하는 길이 k 조각" 의 순위 (같은 조각이면 같은 순위, 0 부터 촘촘히)

    길이 2k 조각의 순서는 길이 k 조각 순위 두 개만 보면 안다
        i 에서 시작하는 길이 2k 조각  =  [ i 부터 k 글자 ] + [ i+k 부터 k 글자 ]
                                          rank[i]            rank[i+k]
        -> (rank[i], rank[i+k]) 쌍으로 정렬한다.  i+k 가 문자열 밖이면 -1 (짧은 쪽이 앞)
        길이 n 짜리 비교가 아니라 정수 두 개 비교라서 한 번이 O(1)

text = "banana" (n = 6) 의 실제 라운드

초기 : rank[i] = text.charAt(i) 그 자체 (길이 1 조각의 순위. 글자 코드가 이미 사전순이다)
    i        0     1     2     3     4     5
    글자     b     a     n     a     n     a
    rank    98    97   110    97   110    97

k = 1  ->  길이 1 + 1 = 2 조각을 본다
    i        0        1        2        3        4        5
    조각    "ba"     "an"     "na"     "an"     "na"     "a"
    쌍    (98,97) (97,110) (110,97) (97,110) (110,97) (97,-1)
    쌍으로 정렬  ->  sa = [ 5, 1, 3, 0, 2, 4 ]
    reRank      ->  rank = [ 2, 1, 3, 1, 3, 0 ]
                    "an" 끼리(i=1,3), "na" 끼리(i=2,4) 아직 동점이다

k = 2  ->  길이 2 + 2 = 4 조각을 본다
    i        0        1        2        3        4        5
    조각   "bana"   "anan"   "nana"    "ana"    "na"     "a"
    쌍     (2,3)    (1,1)    (3,3)    (1,0)    (3,-1)   (0,-1)
    쌍으로 정렬  ->  sa = [ 5, 3, 1, 0, 4, 2 ]        <- naive 와 같은 답
    reRank      ->  rank = [ 3, 2, 5, 1, 4, 0 ]       동점이 하나도 없다

    종료 조건 : rank[sa[n-1]] == n - 1
        마지막 순위가 n-1 이면 0..n-1 이 한 번씩 다 쓰였다는 뜻 = 전부 유일 -> 더 늘릴 필요 없음
    sortRounds() = 2.  라운드 log n 회 x 한 라운드 정렬 O(n log n)  ->  O(n log^2 n)

reRank 가 하는 일 : 정렬된 sa 를 한 번 훑으며 "앞 이웃과 쌍이 다르면 +1"
    같은 조각에 같은 번호를 주고, 번호를 0..n-1 로 촘촘하게 다시 매긴다
    (촘촘해야 다음 라운드의 rank[i+k] 조회가 그대로 O(1) 정수 비교가 된다)
```

### 동작 — 검색

```
sa 가 사전순이므로 "pattern 으로 시작하는 접미사" 들은 반드시 연속 구간에 모여 있다
-> 그 구간의 양끝만 이진 탐색으로 잡으면 된다

find("ana") on "banana"
    r        0      1       2        3       4      5
    sa       5      3       1        0       4      2
    접미사   a     ana    anana   banana     na    nana
                   |<-- ana 로 시작 -->|
                   lo = 1           hi = 3          find 는 [lo, hi) 구간을 돌려준다

    lowerBound("ana")                          upperBound("ana")
      lo=0 hi=6 mid=3 "banana" > ana -> hi=3     lo=0 hi=6 mid=3 "banana" > ana -> hi=3
      lo=0 hi=3 mid=1 "ana"   == ana -> hi=1     lo=0 hi=3 mid=1 "ana"   == ana -> lo=2
      lo=0 hi=1 mid=0 "a"     <  ana -> lo=1     lo=2 hi=3 mid=2 "anana" == ana -> lo=3
      lo == hi == 1  (구간 시작)                  lo == hi == 3  (구간 끝)

    두 탐색의 유일한 차이는 "같다(0)" 를 어느 쪽으로 미느냐다
        lowerBound : 0 -> hi = mid      (더 왼쪽에도 같은 것이 있을 수 있다)
        upperBound : 0 -> lo = mid + 1  (더 오른쪽까지 같을 수 있다)

    comparePrefix(start, pattern) 는 pattern 길이 m 만큼만 본다
        m 글자가 다 맞으면 0 = "이 접미사는 pattern 으로 시작한다"
        접미사가 m 보다 짧아 중간에 끝나면 -1 (짧은 쪽이 앞)

    count = hi - lo,  contains = hi > lo      구간을 나열하지 않고 개수만 답한다
    find 는 [lo, hi) 의 sa 값을 꺼내 오름차순으로 정렬해 돌려준다 ("ana" -> [1, 3])
        sa 순서는 사전순이라 위치 순서가 아니다

비용 : 비교 1회 O(m) x 이진 탐색 O(log n)  ->  O(m log n).  원문 길이가 아니라 log 로 묶인다
```

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

### 구조

```
lcp[r] = sa 에서 이웃한 두 접미사가 공유하는 앞부분 길이 = LCP(sa[r-1], sa[r])
lcp[0] = 0 (왼쪽 이웃이 없다)

text = "banana",  sa = [5, 3, 1, 0, 4, 2]

    r         0      1       2        3       4      5
    sa[r]     5      3       1        0       4      2
    접미사    a     ana    anana   banana     na    nana
    lcp[r]    0      1       3        0       0      2
                     ^       ^        ^       ^      ^
                    "a"    "ana"      ""      ""    "na"     <- 바로 위 이웃과 겹치는 조각

    lcp[2] = 3 : "ana" 와 "anana" 가 앞 3 글자를 공유한다
    lcp[3] = 0 : "anana" 와 "banana" 는 첫 글자부터 다르다

이웃끼리만 재는 것으로 충분한 이유
    사전순으로 세워 두면 겹침이 많은 접미사끼리 붙어 있다
    떨어진 두 접미사 r < r' 의 공통 접두사 길이 = min(lcp[r+1 .. r']) 로 항상 되찾을 수 있다
    -> 인접 정보 n 개만 들고 있으면 모든 쌍의 겹침을 답할 수 있다
```

### 동작 — 구축 (Kasai)

```
sa 순서(r = 0, 1, 2 ...)가 아니라 원문 위치 순서(i = 0, 1, 2 ...)로 훑는 것이 요령이다
    rank = inverse(sa)   ->   rank[sa[r]] = r    (위치 -> 순위. sa 의 역함수)
    위치 i 의 왼쪽 이웃 j = sa[rank[i] - 1] 을 데려와, h 글자째부터 이어서 맞대어 본다

핵심 성질 : i 에서 i+1 로 갈 때 h 는 1 보다 많이 줄지 않는다
    위치 i 의 접미사와 그 이웃이 앞 h 글자를 공유한다면
        i 의 접미사    a n a n a          이웃    a n a
        i+1 의 접미사    n a n a          이웃      n a
                        |<- h-1 ->|
    i+1 의 접미사는 "그 둘에서 첫 글자를 뗀 것" 이므로 최소 h-1 글자는 그대로 겹친다
    (i+1 의 실제 왼쪽 이웃은 다른 접미사일 수 있지만, 사전순으로 더 가까우니 겹침이 더 길다)
    -> h 는 매 걸음 최대 1 줄고, 늘어난 총량은 n 을 못 넘는다 = 전체 글자 비교가 O(n)

"banana" 실제 진행   (sa = [5,3,1,0,4,2],  rank = [3,2,5,1,4,0])
    i   rank[i]  이웃 j       맞대어 본 것                h    기록          다음 h
    0     3      sa[2] = 1    b vs a 에서 불일치          0    lcp[3] = 0    0
    1     2      sa[1] = 3    a n a 3 글자 일치 후 끝     3    lcp[2] = 3    2
    2     5      sa[4] = 4    h=2 에서 시작, 바로 끝      2    lcp[5] = 2    1
    3     1      sa[0] = 5    h=1 에서 시작, 바로 끝      1    lcp[1] = 1    0
    4     4      sa[3] = 0    n vs b 에서 불일치          0    lcp[4] = 0    0
    5     0      순위 0 이라 왼쪽 이웃 없음 -> h = 0            lcp[0] = 0    0

    lcp = [0, 1, 3, 0, 0, 2]
    i = 2, 3 에서는 "이미 h 글자는 맞다고 보장" 되므로 그 앞부분을 다시 안 본다
    이 건너뛰기가 없으면 O(n^2), 있으면 O(n)
```

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
