# data-structure/32-inverted-index — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.
> 2026-09-14: 쉽게 풀어쓴 확장(Claude 작성) — 한눈에 절·동작 그림·용어 풀이 추가.

## 한눈에 — 쉽게 말하면

**비유: 책 맨 뒤의 "찾아보기(색인)" 페이지.**

- "고양이"가 나오는 페이지를 찾고 싶을 때, 책을 첫 장부터 끝까지 넘기는 방법(전수 조사)도 있다. 느리다.
- 책 맨 뒤 찾아보기에는 "고양이 → 12, 87, 203쪽"처럼 **단어별로 나오는 페이지 목록**이 미리 적혀 있다. 거기만 보면 된다.
- 역색인(inverted index)이 정확히 이것이다. "문서 → 단어들"을 뒤집어 "단어 → 그 단어가 있는 문서들"로 미리 만들어 둔다.
- 두 단어를 다 가진 문서(AND 검색)는 두 페이지 목록의 겹치는 번호만 골라내면 된다 — 목록이 번호 순으로 정렬돼 있어서 한 번 훑기로 끝난다.
- 대가: 문서를 넣을 때마다 색인을 갱신하는 수고와 색인 메모리. 검색이 잦고 문서가 많을수록 이득이 커진다.

```text
  [전수 조사]  질문마다 책 전체를 넘긴다
     "cat"? -> [문서0][문서1][문서2][문서3] 전부 펼쳐 본다

  [역색인]    찾아보기 페이지만 본다
     "cat"? -> index["cat"] = [ 0, 1, 3 ]   <- 끝. 문서2는 열지도 않는다
```

이 "찾아보기 페이지"와 **똑같은 구조**가 실무의 검색 엔진이다 — 구글 검색, Elasticsearch, 데이터베이스의 전문(full-text) 검색이 전부 역색인 위에서 돈다. 단어 = 항(term), 페이지 목록 = 포스팅 리스트.

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 계약 — SearchEngine (`src/main/java/com/datastructure/searchindex/SearchEngine.java`)

- `void index(int docId, String text)`
- `int docCount()`
- `int termCount()`
- `List<SearchResult> search(String query, int k)`
- `List<Integer> searchPhrase(String phrase)`
- `static List<String> distinctTerms(List<String> analyzed)`

## 계약 — Analyzer (`src/main/java/com/datastructure/searchindex/Analyzer.java`)

- `List<String> analyze(String text)`

## 계약 — Tokenizer (`src/main/java/com/datastructure/searchindex/Tokenizer.java`)

- `List<String> tokenize(String text)`

## 계약 — Scorer (`src/main/java/com/datastructure/searchindex/Scorer.java`)

- `double score(int termFrequency, int documentFrequency, int documentCount)`

## 계약 — SearchStats (`src/main/java/com/datastructure/searchindex/SearchStats.java`)

- `long visitedDocs()`
- `long comparisons()`

## 보조 — TODO 없는 값·부품 클래스

- `MergeOrder` (`MergeOrder.java`) — 역할:
- `Posting` (`Posting.java`) — 역할:
- `TermFrequencyScorer` (`TermFrequencyScorer.java`) — 역할:

## 구현 — SimpleTokenizer (`src/main/java/com/datastructure/searchindex/SimpleTokenizer.java`)

### 동작 — 자르기 규칙

언제 쓰나: 문장을 단어(토큰) 단위로 자르는 첫 단계. 아래 그림은 "The cat, sat"이 글자 단위 판정(글자냐/경계냐)을 거쳐 세 토큰이 되는 과정과, 마지막 토큰 "sat"이 경계 없이 텍스트가 끝나 흘려보내기를 한 번 더 해야 하는 함정을 보여준다.

  - *토큰(token)*: 텍스트를 잘라 만든 조각(대개 단어 하나).
  - *buf(버퍼)*: 글자를 모아 두는 임시 그릇. 경계를 만나면 비우면서 토큰 하나를 내보낸다.

```
tokenize(text) : Character.isLetterOrDigit(c) 가 true 면 buf 에 쌓고, false 면 경계로 보고 끊는다
                 (자르기만 한다. 소문자화도 불용어 제거도 여기서는 안 한다)

  text = "The cat, sat"          ( _ 는 공백 )

    문자   T  h  e  _  c  a  t  ,  _  s  a  t   <- 여기서 텍스트가 끝난다
    판정   L  L  L  .  L  L  L  .  .  L  L  L
           +-----+     +-----+        +-----+     L = isLetterOrDigit true -> buf 에 쌓는다
            "The"       "cat"          "sat"      . = false -> 경계 -> buf 를 흘려보낸다
                              ^^^^
                              경계가 둘 연속( ',' 다음 ' ' )

  buf 의 흐름
    T -> Th -> The      ' ' 경계    -> out.add("The"),  buf.setLength(0)
    c -> ca -> cat      ',' 경계    -> out.add("cat"),  buf.setLength(0)
                        ' ' 경계    -> buf 가 비어 있으므로 아무것도 안 한다
                                       (경계가 연속돼도 빈 토큰이 안 생긴다)
    s -> sa -> sat      텍스트 끝   -> 경계를 못 만나고 끝난다
                                       ^ 루프 뒤에서 한 번 더 흘려보내지 않으면 조용히 사라진다

  out = [ "The" , "cat" , "sat" ]

비용 : 글자 하나를 한 번씩 본다 -> O(글자 수). 필드가 없어 상태도 없다.
한국어 : isLetterOrDigit 가 한글도 글자로 보므로 그대로 잘린다.
         "고양이2 좋다" -> [ "고양이2" , "좋다" ]
         그래서 "고양이가" 와 "고양이" 가 서로 다른 항이 된다. 형태소 분석은 이 박스 밖이다.
         영어 어간 추출(stemming)도 같은 이유로 없다.
```

### 필드
- (없음) — 역할:

### `List<String> tokenize(String text)` (TODO 1)
- 하는 일:
- 논리:
- 비용(왜):

### `String toString()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — StandardAnalyzer (`src/main/java/com/datastructure/searchindex/StandardAnalyzer.java`)

### 구조

```
StandardAnalyzer
+-------------------------------------------------------------------------+
| tokenizer : Tokenizer = SimpleTokenizer         (자르기를 위임)           |
| stopwords : Set<String> = Set.copyOf(...)       (걸러낼 말, 불변 복사본)   |
| DEFAULT_STOPWORDS =                                                      |
|   { a, an, and, or, the, of, is, to, in, it, 그리고, 그러나, 또는, 및, 등 } |
|     ^ 전부 소문자로 적어 둔다. 비교 직전에 소문자로 바꾸기 때문이다.        |
+-------------------------------------------------------------------------+
  분석기는 색인 쪽과 질의 쪽에 각각 주입된다. 둘을 다르게 주면 답이 어긋난다(AnalyzerMismatchTest).
```

### 동작 — 분석(analyze) 파이프라인

언제 쓰나: 색인할 때와 검색할 때 모두, 텍스트를 "색인에 넣을 최종 형태"로 다듬는 단계. 아래 그림은 한 문장이 자르기 → 소문자화 → 불용어 제거의 세 관문을 차례로 통과하는 흐름이다. 순서 자체가 약속(계약)이라는 것이 요점이다.

  - *불용어(stopword)*: "the", "그리고"처럼 너무 흔해서 검색에 도움이 안 되는 말. 색인에서 아예 뺀다.
  - *로케일(Locale)*: 나라·언어별 문자 규칙. `Locale.ROOT`는 어느 나라 규칙도 안 따르는 중립 설정이다.

```
세 단계의 순서가 계약이다 :  자르기 -> 소문자화 -> 불용어 제거

  text  "The Cat and The DOG"
    |
    v  [1] tokenizer.tokenize(text)
       +-------+-------+-------+-------+-------+
       | "The" | "Cat" | "and" | "The" | "DOG" |
       +-------+-------+-------+-------+-------+
    |
    v  [2] token.toLowerCase(Locale.ROOT)        <- 기본 로케일이 아니라 ROOT 고정
       +-------+-------+-------+-------+-------+    (터키어 환경에서 I 가 점 없는 i 로 바뀌면
       | "the" | "cat" | "and" | "the" | "dog" |     색인과 질의가 기계마다 다르게 어긋난다)
       +-------+-------+-------+-------+-------+
    |
    v  [3] stopwords.contains(lower) 면 버린다
         버림    남김    버림    버림    남김
       +---X---+-------+---X---+---X---+-------+
       |  the  | "cat" |  and  |  the  | "dog" |
       +-------+-------+-------+-------+-------+
    |
    v
       [ "cat" , "dog" ]
          0        1
          ^^^^^^^^^^^^  이 목록의 인덱스가 곧 Posting 의 위치(position)다.
                        불용어를 버린 뒤의 인덱스라는 뜻이고, 구문 검색이 이 번호를 그대로 믿는다.

순서를 뒤집으면 : 불용어를 먼저 보면 "The" 가 집합에 없어 안 걸리고 "the" 만 걸린다.
                 같은 말이 두 항이 되고 색인이 조용히 커진다.
비용 : 토큰마다 소문자화 1회 + 해시 집합 조회 1회 -> O(토큰 수)
```

### 필드
- `tokenizer` — 역할:
- `stopwords` — 역할:
- `DEFAULT_STOPWORDS` — 역할:

### `StandardAnalyzer()` / `StandardAnalyzer(Set<String> stopwords)` / `StandardAnalyzer(Tokenizer tokenizer, Set<String> stopwords)`
- 하는 일:
- 논리:
- 비용(왜):

### `List<String> analyze(String text)` (TODO 2)
- 하는 일:
- 논리:
- 비용(왜):

### `Set<String> stopwords()`
- 하는 일:
- 논리:
- 비용(왜):

### `String toString()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — TfIdfScorer (`src/main/java/com/datastructure/searchindex/TfIdfScorer.java`)

### 동작 — tf 와 idf 가 어디서 오나

언제 쓰나: 검색 결과의 순위를 매길 때 — "이 문서가 이 질의어와 얼마나 관련 있나"를 숫자 하나로 만든다. 아래 그림은 tf(문서 안을 본다)와 df(색인 전체를 본다)가 서로 다른 표에서 나와 한 식에서 만나는 흐름과, 드문 말일수록 점수가 커지는 표다.

  - *tf(term frequency)*: 이 문서에서 그 단어가 나온 횟수. 많이 나오면 그 문서가 그 주제를 많이 다룬다는 신호.
  - *df(document frequency)*: 그 단어를 가진 문서의 수. 작을수록 드문(= 문서를 잘 가려내는) 말이다.
  - *idf*: df의 역수에 로그(ln)를 씌운 것. "드문 말에 큰 가중치"를 수식으로 만든 것.
  - *ln(자연로그)*: 곱셈의 크기를 완만한 덧셈 크기로 눌러 주는 함수. ln(1) = 0이라 "모든 문서에 있는 말"은 0점이 된다.

```
score(termFrequency, documentFrequency, documentCount) = tf * ln(N / df)
    셋 중 하나라도 0 이하면 0.0 을 준다 (예외가 아니다)

세 값이 나오는 표가 서로 다르다

   tf = 이 문서에서 이 항이 나온 횟수           df = 이 항을 가진 문서 수
   +-----------------------------+             +-----------------------------+
   | Posting{docId, positions}   |             | index.get(term) 의 길이      |
   |   frequency()               |             |   = 포스팅 리스트의 원소 수   |
   |   = positions.size()        |             |                             |
   | 문서 "안"을 본다             |             | 색인 "전체"를 본다            |
   +-----------------------------+             +-----------------------------+
              |                                            |
              |   tf 가 크다 = 이 문서가 그 말을 많이 다룬다   |  df 가 작다 = 그 말이 드물다
              v                                            v
              +--------------->  tf * ln(N / df)  <--------+
                                       ^
                                       N = docCount() = 색인에 든 문서 수

희귀어 가중이 커지는 이유 (N = 100 으로 고정)

   항          df     N/df      ln(N/df)     tf = 3 일 때 점수
   ---------   ---    ------    --------     ----------------
   "the"       100      1.00      0.00            0.00     <- 모든 문서에 있다 = 문서를 못 가른다
   "cat"        60      1.67      0.51            1.53
   "quantum"     2     50.00      3.91           11.73
   "zebra"       1    100.00      4.61           13.82     <- 드물수록 ln 이 커진다

   ln 은 df 가 작아질수록 급히 커지고, df 가 N 에 가까워지면 0 으로 내려앉는다.
   "이 문서에 몇 번 나오나"(tf)에 "그 말이 얼마나 드문가"(idf)를 곱하는 것이 이 식의 전부다.

함정 : 나눗셈을 double 로 해야 한다.
       int 로 나누면 N=100, df=60 일 때 100/60 = 1 -> ln(1) = 0.
       흔한 항이 전부 0 점이 되어 그 사이의 순위 차이가 통째로 사라진다. 예외는 안 난다.
       df = N 이면(모든 문서에 있는 항) ln(1) = 0 이라 점수 0 - 버그가 아니라 이 식의 뜻이다.
       그래서 문서가 하나뿐인 색인에서는 모든 항이 0 점이고 순위가 문서 번호 순으로 무너진다.
비용 : 로그 한 번. O(1). 상태가 없어 스레드 안전하다.
```

### 필드
- (없음) — 역할:

### `double score(int termFrequency, int documentFrequency, int documentCount)` (TODO 3)
- 하는 일:
- 논리:
- 비용(왜):

### `String toString()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — SearchResult (`src/main/java/com/datastructure/searchindex/SearchResult.java`)

### 필드
- `docId` — 역할:
- `score` — 역할:

### `SearchResult(int docId, double score)`
- 하는 일:
- 논리:
- 비용(왜):

### `int docId()` / `double score()`
- 하는 일:
- 논리:
- 비용(왜):

### `int compareTo(SearchResult other)` (TODO 4)
- 하는 일:
- 논리:
- 비용(왜):

### `boolean equals(Object o)` / `int hashCode()` / `String toString()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — LinearScanEngine (`src/main/java/com/datastructure/searchindex/LinearScanEngine.java`)

### 구조

```
LinearScanEngine   (전수 조사 기준선 - 색인을 아예 안 만든다)
+---------------------------------------------------------------------+
| indexAnalyzer / queryAnalyzer : Analyzer  (따로 줄 수 있다 - 이 박스의 함정) |
| scorer    : Scorer                                                   |
| documents : Map<Integer,String> = TreeMap   원문 그대로, 문서번호 오름차순 |
| visitedDocs : long                          (측정용 계수기)            |
+---------------------------------------------------------------------+

   documents
   +-------+---------------------------+
   |   0   | "The cat sat"             |
   |   1   | "A dog and a cat"         |
   |   2   | "The dog barked"          |
   |   3   | "cat dog cat"             |
   +-------+---------------------------+
   index(docId, text) 가 하는 일은 put 하나뿐이다 -> O(1). 만들어 두는 것이 없다.
   termCount() 조차 전 문서를 다시 분석해야 답한다. 저장해 둔 것이 없기 때문이다.
   TreeMap 인 이유 : 훑는 순서가 정해져야 답(동점 순서 포함)이 하나로 정해진다.
```

### 동작 — 전수 조사 검색 (역색인과의 대비)

언제 보나: 역색인이 얼마나 이득인지 재는 기준선, 그리고 역색인의 조용한 누락을 잡는 대조 상대. 아래 그림은 질의 한 번에 모든 문서를 열어 다시 분석하는 흐름 — "답이 하나여도 전부 연다"가 이 방식의 비용이다.

  - *전수 조사(linear scan)*: 지름길 없이 처음부터 끝까지 다 보는 방식. 느리지만 틀리기 어렵다.

```
search("cat dog", k) : 질의마다 전 문서를 열어 다시 분석한다. 한 번만 훑는다.

   +-----+---------------------+  analyze ->            counts[cat,dog]   전부 있나
   |  0  | "The cat sat"       |  [cat, sat]                [1, 0]          X
   |  1  | "A dog and a cat"   |  [dog, cat]                [1, 1]          O  <- 답
   |  2  | "The dog barked"    |  [dog, barked]             [0, 1]          X
   |  3  | "cat dog cat"       |  [cat, dog, cat]           [2, 1]          O  <- 답
   +-----+---------------------+
      ^ 문서마다 visitedDocs++  -> 질의 한 번에 정확히 n 회
        두 번 훑으면 2n 이 되어 "질의마다 정확히 n" 이라는 자가 망가진다.
        그래서 df 도 같은 한 번의 훑기 안에서 함께 센다 : df[cat]=3, df[dog]=3, N=4

   matched -> 점수 합산 -> Collections.sort (점수 내림차순, 동점이면 docId 오름차순) -> 상위 k
   comparisons() 는 늘 0 이다. 병합이라는 것이 없기 때문이다.

비용 대비

   전수 조사   질의 1회마다   [문서0][문서1][문서2] ... [문서n-1]  을 전부 열고 다시 분석
                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                              O(문서 수 x 문서 길이)  - 답이 하나여도 전부 연다

   역색인      질의 1회마다   index["cat"] -> [ 0 , 1 , 3 ]
                              index["dog"] -> [ 1 , 2 , 3 ]
                                              ^^^^^^^^^^^^ 이 리스트만 훑는다
                              O(매칭 포스팅 수) - 나머지 문서는 열지도 않는다

이 클래스가 쉽다는 것이 요점이다.
역색인의 교집합 병합은 조건 하나만 틀려도 "봐야 할 문서를 안 본다"가 되는데,
예외도 안 나고 결과가 조용히 몇 개 빠진다.
그 조용한 누락을 잡는 자가 이 클래스다 - 두 엔진의 답이 같아야 한다.
```

### 필드
- `indexAnalyzer` — 역할:
- `queryAnalyzer` — 역할:
- `scorer` — 역할:
- `documents` — 역할:
- `visitedDocs` — 역할:

### `LinearScanEngine()` / `LinearScanEngine(Analyzer analyzer, Scorer scorer)` / `LinearScanEngine(Analyzer indexAnalyzer, Analyzer queryAnalyzer, Scorer scorer)`
- 하는 일:
- 논리:
- 비용(왜):

### `void index(int docId, String text)`
- 하는 일:
- 논리:
- 비용(왜):

### `int docCount()`
- 하는 일:
- 논리:
- 비용(왜):

### `int termCount()`
- 하는 일:
- 논리:
- 비용(왜):

### `List<SearchResult> search(String query, int k)` (TODO 5)
- 하는 일:
- 논리:
- 비용(왜):

### `List<Integer> searchPhrase(String phrase)` (TODO 6)
- 하는 일:
- 논리:
- 비용(왜):

### `long visitedDocs()` / `long comparisons()`
- 하는 일:
- 논리:
- 비용(왜):

### `String toString()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — InvertedIndexEngine (`src/main/java/com/datastructure/searchindex/InvertedIndexEngine.java`)

### 구조

```
정방향 색인   문서 -> 그 안의 항들        (문서를 보여줄 때 쓴다)
역색인        항  -> 그 항이 있는 문서들   (검색할 때 쓴다)     <- 방향을 뒤집은 것이 전부다

InvertedIndexEngine
+---------------------------------------------------------------------------+
| indexAnalyzer / queryAnalyzer : Analyzer     scorer : Scorer               |
| mergeOrder : MergeOrder = SHORTEST_FIRST (기본)                            |
| index         : Map<String,List<Posting>> = HashMap    항 -> 포스팅 리스트   |
| indexedDocIds : Set<Integer> = TreeSet    항이 0 개인 문서도 여기엔 들어간다  |
| visitedDocs / comparisons : long          (측정용 계수기)                   |
+---------------------------------------------------------------------------+

예시 문서 (오른쪽은 indexAnalyzer.analyze 결과. 인덱스가 곧 위치다)
   doc 0  "The cat sat"        -> cat(0)  sat(1)
   doc 1  "A dog and a cat"    -> dog(0)  cat(1)
   doc 2  "The dog barked"     -> dog(0)  barked(1)
   doc 3  "cat dog cat"        -> cat(0)  dog(1)  cat(2)

index (HashMap)         Posting = { docId , positions }   frequency() = positions.size()
  +----------+----------------------------------------------------+
  | "cat"    | [ {0,[0]} , {1,[1]} , {3,[0,2]} ]                   |
  | "sat"    | [ {0,[1]} ]                                        |
  | "dog"    | [ {1,[0]} , {2,[0]} , {3,[1]} ]                    |
  | "barked" | [ {2,[1]} ]                                        |
  +----------+----------------------------------------------------+
               ^^^^^^^^ 포스팅 하나 = (항, 문서) 한 쌍. 리스트는 늘 docId 오름차순이다.
               이 정렬이 이 구조의 값을 만든다 - 정렬돼 있어야 교집합을 한 번 훑기로 한다.

  postingCount()  = 3 + 1 + 3 + 1 = 8      (항, 문서) 쌍의 수. 색인 크기를 재는 첫 번째 자.
  positionCount() = 4 + 1 + 3 + 1 = 9      위치 정수의 수. 원문의 항 개수와 같아야 한다. 두 번째 자.
  indexedDocIds = { 0, 1, 2, 3 }   docCount() = 4   termCount() = index.size() = 4

  빈도를 따로 안 들고 positions.size() 로 센다. 두 값을 다 들면 어긋날 자리가 생기고,
  어긋나면 예외 없이 점수만 조용히 틀린다.
  위치를 안 담으면 구문 검색을 아예 못 한다. 대신 원문 토큰 하나마다 정수 하나가 색인에 들어간다.
```

### 동작 — 색인(indexing)

언제 쓰나: 문서가 새로 들어올 때 — 검색이 빨라지도록 "단어 → 문서 목록" 표를 미리 갱신해 둔다. 아래 그림은 문서 하나가 분석되고, 문서 안에서 항별로 모인 뒤, 전체 색인의 정렬된 자리에 꽂히는 3단계다.

  - *포스팅(Posting)*: "(이 단어가) 어느 문서의 어느 위치들에 있나"를 담은 기록 하나. 포스팅 리스트 = 그 단어의 기록 목록.
  - *computeIfAbsent*: 맵에 키가 없으면 새 값을 만들어 넣고, 있으면 그것을 돌려주는 자바 맵 연산.
  - *이분 탐색(binary search)*: 정렬된 목록에서 절반씩 잘라가며 자리를 찾는 방법.

```
index(docId, text)

  text "cat dog cat"  (docId = 3)
    |
    v  indexedDocIds.add(docId)      false 면 이미 색인된 번호 -> IllegalArgumentException
    |                                (항이 하나도 없는 문서도 여기 들어가 N 에 센다)
    v  indexAnalyzer.analyze(text)   자르기 -> 소문자화 -> 불용어 제거
       위치    0       1       2
            [ cat ][ dog ][ cat ]
    |
    v  문서 하나 안에서 항별로 모은다  (perDocument : LinkedHashMap<String,Posting>)
       computeIfAbsent(term, -> new Posting(docId)).addPosition(position)
       "cat" -> Posting{3, [0, 2]}      같은 항이 여러 번 나와도 포스팅은 하나다
       "dog" -> Posting{3, [1]}         앞에서 뒤로 훑으니 위치가 자연히 오름차순
                                        addPosition 은 오름차순이 아니면 던진다
    |
    v  항마다 index 의 포스팅 리스트에 "정렬된 자리"로 꽂는다  (insertSorted)

       index["cat"]  before  [ {0,[0]} , {1,[1]} ]
                                          |
                       이분 탐색으로 docId 3 이 들어갈 자리를 찾는다 (low = 2)
                                          v
                     after   [ {0,[0]} , {1,[1]} , {3,[0,2]} ]     docId 오름차순 유지

왜 append 가 아니라 insertSorted 인가
   문서를 번호 순서대로 넣으면 늘 맨 뒤가 정답이라 append 로도 테스트가 전부 통과한다.
   순서가 뒤섞여 들어오는 순간 리스트가 망가지고, 그러면 교집합 병합이 조용히 답을 빠뜨린다.
비용 : 분석 O(문서 길이) + 항마다 이분 탐색 O(log p) + 리스트 중간 삽입 O(p)
```

### 동작 — AND 검색 (posting 교집합)

언제 쓰나: "cat도 있고 dog도 있는 문서"처럼 질의어 전부를 가진 문서를 찾을 때. 아래 그림의 핵심은 [3] — 정렬된 두 목록에 손가락(포인터)을 하나씩 얹고, 작은 쪽 손가락만 앞으로 밀면서 같은 번호가 만나면 답에 담는 한 번 훑기다.

  - *교집합(intersection)*: 두 목록에 공통으로 들어 있는 것만 모은 것.
  - *두 포인터(two pointers)*: 두 목록에 각각 현재 위치 표시를 두고 동시에 전진시키는 기법. 정렬돼 있어야만 쓸 수 있다.

```
intersect(terms) : 질의어를 전부 가진 문서 번호를 오름차순으로

[1] 항마다 포스팅 리스트를 꺼낸다. 하나라도 없으면 즉시 공집합이다 (AND 니까)
[2] mergeOrder == SHORTEST_FIRST 면 길이 오름차순으로 정렬하고 짧은 것부터 병합한다
       중간 결과는 절대 커지지 않는다. 작게 시작하면 그 뒤의 모든 병합이 작은 쪽 길이에 묶인다.
       흔한 말부터 시작하면 첫 병합에서 긴 리스트를 통째로 훑고, 그 일은 되돌릴 수 없다.
       QUERY_ORDER 는 질의에 적힌 순서 그대로다. 답은 어느 쪽이든 같고 comparisons 만 달라진다.
       그래서 이 선택은 무작위 대조로는 안 잡히고 비교 횟수를 세는 측정으로만 드러난다.
[3] 두 포인터로 한 번 훑어 교집합을 만든다

    merged  ("cat" 의 docId 들)   [ 0 , 1 , 3 ]
                                    i
    other   ("dog" 의 포스팅)      [ 1 , 2 , 3 ]
                                    j

    단계   merged[i]   other[j]   판정      한 일
    ----   ---------   --------   -------   -----------------------------------
      1        0          1       0 < 1     i++                    (작은 쪽만 전진)
      2        1          1       같다      next.add(1) , i++ , j++
      3        3          2       3 > 2     j++                    (작은 쪽만 전진)
      4        3          3       같다      next.add(3) , i++ , j++
      5      i 가 끝       -       -         루프 종료

    next = [ 1 , 3 ]        <- docId 오름차순이 그대로 유지된다
    리스트가 셋 이상이면 merged = next 로 두고 다음 리스트와 또 접는다.
    merged 가 비면 즉시 멈춘다 (더 접어봐야 계속 공집합이다)

비용 : O(p1 + p2) - 두 리스트를 각각 한 번씩만 지나간다. 정렬돼 있어서 가능한 일이다.
       정렬이 안 돼 있으면 한쪽 원소마다 상대를 다 뒤져야 해서 O(p1 x p2) 가 된다.
계수 : 비교 1회마다 comparisons++ , 전진한 포인터마다 visitedDocs++
```

### 동작 — 점수(tf-idf) 흐름

언제 쓰나: 교집합으로 추린 후보 문서들에 순위를 매겨 상위 k개만 돌려줄 때. 아래 그림은 후보 두 문서가 질의어별 점수를 합산받고, 정렬을 거쳐 상위 k개로 잘리는 흐름이다. df를 "포스팅 리스트의 길이"로 그냥 읽는다는 것 — 전수 조사가 전 문서를 훑어 얻는 값을 여기서는 공짜로 얻는다는 것이 역색인의 두 번째 이득이다.

  - *부동소수점(floating point)*: 컴퓨터가 소수를 저장하는 방식. 더하는 순서가 바뀌면 마지막 자리 비트가 달라질 수 있다.

```
search(query, k) 의 채점 단계

  terms      = SearchEngine.distinctTerms(queryAnalyzer.analyze(query)) = [ "cat" , "dog" ]
               (중복 제거 + 처음 나온 순서 유지. 이 순서가 점수를 더하는 순서다)
  candidates = intersect(terms) = [ 1 , 3 ]

  df 는 그냥 읽는다 - 포스팅 리스트의 길이다
      df[cat] = index.get("cat").size() = 3        <- 전수 조사는 이 값 하나를 위해 전부 훑는다
      df[dog] = index.get("dog").size() = 3
      N       = docCount() = 4

  후보 문서마다 질의어 순서로 점수를 더한다 (병합 순서가 아니라 질의어 순서)

    문서 1                                    문서 3
      tf(cat,1) = 1   (positions [1])           tf(cat,3) = 2   (positions [0,2])
      tf(dog,1) = 1   (positions [0])           tf(dog,3) = 1   (positions [1])
    +--------------------------------+        +--------------------------------+
    | cat : 1 * ln(4/3) = 0.2877     |        | cat : 2 * ln(4/3) = 0.5754     |
    | dog : 1 * ln(4/3) = 0.2877     |        | dog : 1 * ln(4/3) = 0.2877     |
    |                sum = 0.5754    |        |                sum = 0.8631    |
    +--------------------------------+        +--------------------------------+
             |                                          |
             +------------------+-----------------------+
                                v
      results = [ (1, 0.5754) , (3, 0.8631) ]
                                v  Collections.sort  =  SearchResult.compareTo
                                   점수 내림차순, 동점이면 docId 오름차순
              [ (3, 0.8631) , (1, 0.5754) ]
                                v  subList(0, min(k, size))
      k = 1 이면  [ (3, 0.8631) ]

더하는 순서를 질의어 순서로 못 박는 이유 : 순서를 바꾸면 부동소수점 합의 마지막 비트가 달라지고,
    그러면 동점 판정이 흔들려 전수 조사와 역색인의 답을 비트까지 대조할 수 없다.
tf 는 Posting 안(문서 안)에서, df 는 포스팅 리스트 길이(색인 전체)에서 나온다. 표가 서로 다르다.
비용 : 후보 수 x 질의어 수 만큼 채점 + 정렬 O(m log m). 후보가 아닌 문서는 열지도 않는다.
```

### 필드
- `indexAnalyzer` — 역할:
- `queryAnalyzer` — 역할:
- `scorer` — 역할:
- `mergeOrder` — 역할:
- `index` (`Map<String, List<Posting>>`) — 역할:
- `indexedDocIds` (`Set<Integer>`) — 역할:
- `visitedDocs` — 역할:
- `comparisons` — 역할:

### `InvertedIndexEngine()` 외 생성자 4개 (analyzer / scorer / mergeOrder / 색인·질의 분석기 분리)
- 하는 일:
- 논리:
- 비용(왜):

### `void index(int docId, String text)` (TODO 7)
- 하는 일:
- 논리:
- 비용(왜):

### `static void insertSorted(List<Posting> postings, Posting posting)` (TODO 8, private)
- 하는 일:
- 논리:
- 비용(왜):

### `int docCount()` / `int termCount()`
- 하는 일:
- 논리:
- 비용(왜):

### `List<Posting> postings(String term)`
- 하는 일:
- 논리:
- 비용(왜):

### `long postingCount()` / `long positionCount()`
- 하는 일:
- 논리:
- 비용(왜):

### `List<Integer> intersect(List<String> terms)` (TODO 9, private)
- 하는 일:
- 논리:
- 비용(왜):

### `List<SearchResult> search(String query, int k)` (TODO 10)
- 하는 일:
- 논리:
- 비용(왜):

### `List<Integer> searchPhrase(String phrase)` (TODO 11)
- 하는 일:
- 논리:
- 비용(왜):

### `boolean containsPhrase(List<String> terms, int docId)` (TODO 12, private)
- 하는 일:
- 논리:
- 비용(왜):

### `long visitedDocs()` / `long comparisons()`
- 하는 일:
- 논리:
- 비용(왜):

### `String toString()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 전략 비교

엔진 (`SearchEngine` 두 구현)

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| LinearScanEngine | | | |
| InvertedIndexEngine | | | |

부품 (같은 계약의 변종 — 답이 갈리는 것과 비용만 갈리는 것)

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| TermFrequencyScorer | | | |
| TfIdfScorer | | | |
| MergeOrder.SHORTEST_FIRST | | | |
| MergeOrder.QUERY_ORDER | | | |

## 핵심 문장

<!-- 지도 수준의 문장들 — 세부가 아니라 "왜 이 구조인가"를 담은 문장 -->

-
-
-

## 용어 풀이

- **역색인(inverted index)**: "문서 → 단어들"을 뒤집어 "단어 → 그 단어가 있는 문서들"로 만든 표. 책 뒤의 찾아보기와 같다.
- **정방향 색인(forward index)**: "문서 → 그 안의 단어들" 방향의 표. 문서를 보여줄 때 쓴다.
- **항(term)**: 분석을 마치고 색인에 들어가는 최종 형태의 단어.
- **토큰(token)**: 텍스트를 잘라 만든 조각. 분석(소문자화·불용어 제거)을 거치면 항이 된다.
- **포스팅(posting)**: (항, 문서) 한 쌍의 기록 — 그 문서의 어느 위치들에 나오는지(positions)를 담는다.
- **포스팅 리스트(posting list)**: 한 항의 포스팅들을 docId 오름차순으로 모은 목록. 이 정렬이 한 번 훑기 교집합을 가능하게 한다.
- **불용어(stopword)**: 너무 흔해서 검색에 도움이 안 되는 말("the", "그리고"). 색인 전에 걸러낸다.
- **분석기(analyzer)**: 자르기 → 소문자화 → 불용어 제거를 순서대로 하는 파이프라인. 색인 쪽과 질의 쪽이 같아야 한다.
- **형태소 분석 / 어간 추출(stemming)**: "고양이가"에서 "고양이"를, "running"에서 "run"을 뽑는 언어 처리. 이 구현의 범위 밖.
- **tf(term frequency)**: 이 문서에서 그 항이 나온 횟수.
- **df(document frequency)**: 그 항을 가진 문서 수.
- **idf / tf-idf**: 드문 말에 큰 가중치를 주는 값(ln(N/df))과, 그것을 tf에 곱한 관련도 점수.
- **ln(자연로그)**: 큰 비율을 완만한 크기로 눌러 주는 함수. ln(1)=0.
- **교집합(intersection)**: 여러 목록에 공통으로 든 것만 모은 것. AND 검색의 본체.
- **두 포인터(two pointers)**: 정렬된 두 목록에 위치 표시를 하나씩 두고 작은 쪽만 전진시키며 한 번에 훑는 기법.
- **이분 탐색(binary search)**: 정렬된 목록에서 절반씩 잘라가며 찾는 방법. O(log n).
- **전수 조사(linear scan)**: 색인 없이 매 질의마다 모든 문서를 여는 기준선 방식.
- **구문 검색(phrase search)**: "cat sat"처럼 단어들이 그 순서로 붙어 나오는 문서만 찾는 검색. 위치(positions) 정보가 있어야 가능하다.
- **HashMap / TreeMap / TreeSet**: 자바의 맵·집합. Hash-는 순서 없이 빠르고, Tree-는 항상 정렬된 순서를 유지한다.
- **LinkedHashMap**: 넣은 순서를 기억하는 맵. "처음 나온 순서 유지"가 필요할 때 쓴다.
- **로케일(Locale) / Locale.ROOT**: 나라별 문자 규칙 / 어느 나라도 따르지 않는 중립 규칙. 소문자화 결과가 기계마다 달라지는 것을 막는다.
- **부동소수점(floating point)**: 컴퓨터의 소수 표현. 덧셈 순서에 따라 마지막 비트가 달라질 수 있어, 더하는 순서를 못 박아야 두 엔진의 답을 비트까지 맞출 수 있다.
- **O(1), O(log n), O(n)**: 걸리는 시간의 대략적 규모 표기. 각각 "일정", "n이 두 배여도 한 걸음", "n에 비례".
- **계약(인터페이스)**: 구현들이 공통으로 지키는 메서드 목록과 약속(SearchEngine, Analyzer 등).
- **주입(injection)**: 부품(분석기·채점기)을 밖에서 만들어 생성자로 넣어 주는 방식. 부품만 바꿔 끼울 수 있게 한다.

## 관련 자료

- 원본 README: `/home/jun/project/myway/data-structure/32-inverted-index/README.md`
- 구현 대상: `/home/jun/project/myway/data-structure/32-inverted-index/src/main/java/com/datastructure/searchindex/`
- 테스트: `/home/jun/project/myway/data-structure/32-inverted-index/src/test/java/com/datastructure/searchindex/`
- 정답 구현: `/home/jun/project/myway/data-structure/32-inverted-index/impl/`
