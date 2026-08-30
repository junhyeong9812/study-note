# data-structure/32-inverted-index — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

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

## 관련 자료

- 원본 README: `/home/jun/project/myway/data-structure/32-inverted-index/README.md`
- 구현 대상: `/home/jun/project/myway/data-structure/32-inverted-index/src/main/java/com/datastructure/searchindex/`
- 테스트: `/home/jun/project/myway/data-structure/32-inverted-index/src/test/java/com/datastructure/searchindex/`
- 정답 구현: `/home/jun/project/myway/data-structure/32-inverted-index/impl/`
