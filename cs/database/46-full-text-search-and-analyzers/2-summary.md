# database/46-full-text-search-and-analyzers — 전문 검색: 분석기, 한국어 토큰화, BM25 — 정리 (힌트)

## 해결하는 문제

"냉장고"가 들어간 상품을 찾는 가장 쉬운 SQL은 이것이다.

```sql
SELECT * FROM product WHERE name LIKE '%냉장고%';
```

- 앞에 `%`가 붙으면 B-tree 구간 탐색을 쓸 수 없다. B-tree는 **앞에서부터** 정렬돼 있기 때문이다. 결국 행을 전부 훑는다.
- 찾아도 순서가 없다. "냉장고"가 제목에 있는 상품과 설명 끝에 한 번 나온 상품이 똑같이 취급된다.
- "냉장고들", "Refrigerator", "냉장고를"처럼 형태가 바뀌면 못 찾는다.

쉬운 예: 책 뒤의 **찾아보기**(색인)다. "교착 상태 → 212, 245쪽"처럼 단어에서 쪽 번호로 간다. 본문을 처음부터 넘기지 않는다. 그리고 "교착"을 찾는 사람도 "교착 상태" 항목으로 가도록, 색인을 만들 때 단어를 정리해 둔다.

똑같은 구조다.

- 찾아보기 = **역색인**(단어 → 문서 목록)
- 단어를 정리하는 규칙 = **분석기**(analyzer)
- 어느 쪽이 더 관련 있나 = **관련도 점수**(BM25)

실무 예: 쇼핑몰 상품 검색, 게시판 검색, 로그 검색. 한국어는 띄어쓰기 단위(어절)에 조사가 붙어 문제가 하나 더 생긴다. "삼성전자가"에서 "삼성"을 찾아야 한다.

## 동작·원리

### 1. 분석기 = 문자 필터 → 토크나이저 → 토큰 필터

```text
  원문: "<b>삼성전자</b>가 Running 냉장고를 출시"
     │ 문자 필터 (HTML 제거 등)
     ▼
  "삼성전자가 Running 냉장고를 출시"
     │ 토크나이저 (어디서 자를까)
     ▼
  [삼성전자가] [Running] [냉장고를] [출시]        ← 공백 기준이면
  [삼성][전자][가][Running][냉장고][를][출시]      ← 형태소 분석이면
     │ 토큰 필터 (소문자화·어간 추출·불용어·동의어·품사 제거)
     ▼
  [삼성][전자][run][냉장고][출시]                  ← 색인에 들어가는 용어(term)
```

- *토큰(token)*: 토크나이저가 잘라 낸 조각이다. 위치(position)와 오프셋을 함께 가진다.
- *용어(term)·어휘소(lexeme)*: 필터까지 거쳐 색인에 실제로 들어가는 정규화된 형태다. PostgreSQL 문서는 lexeme이라 부른다.
- *불용어(stop word)*: 너무 흔해 색인하지 않는 단어다(영어 "a", "the").
- *어간 추출(stemming)*: "running"과 "runs"를 "run"으로 모은다.

PostgreSQL 17로 본 두 설정의 차이(로컬 재현, 예시, PostgreSQL 17.11):

```text
  to_tsvector('english', 'The runners were running quickly')
  → 'quick':5 'run':4 'runner':2           불용어 제거 + 어간 추출

  to_tsvector('simple', '삼성전자 주가가 올랐다')
  → '삼성전자':1 '올랐다':3 '주가가':2      여기선 공백에서 잘렸다. 조사 "가"가 붙은 채 남는다
```

- PostgreSQL 17에는 한국어 텍스트 검색 설정이 기본 제공되지 않는다. `simple`은 소문자화만 한다.
  - 토큰 경계는 사전이 아니라 기본 파서가 정한다. 공백·구두점에서 자르고, 하이픈 단어는 전체와 부분을 함께 낸다(PostgreSQL 17 12.5 Parsers).
- 그래서 `'삼성'`으로 찾으면 `'삼성전자'`와 **다른 용어**라 맞지 않는다.

### 2. 역색인 — 용어 → 게시 목록(posting list)

```text
  문서 1: 삼성전자 주가 상승
  문서 2: 삼성 라이온즈 우승
  문서 3: 성전 건축 역사

  용어 사전 (정렬)        게시 목록 (문서 ID, 위치)
  ─────────────          ─────────────────────────
  라이온즈        ──>     (2, 2)
  삼성            ──>     (2, 1)
  삼성전자        ──>     (1, 1)
  성전            ──>     (3, 1)
  ...

  질의 "삼성 AND 우승" = 게시 목록 (2) ∩ (2) = {2}
```

- 기초 구조(게시 목록 교집합, 위치 색인, 압축)는 [data-structure/32-inverted-index](../../data-structure/32-inverted-index/2-summary.md)에 있다.
- PostgreSQL의 GIN 인덱스가 역색인이다. 문서는 "각 단어(lexeme)마다 항목 하나와 일치 위치의 압축 목록"이라고 설명한다.
- GIN은 weight 라벨을 저장하지 않는다. 그래서 가중치가 들어간 질의는 테이블 행을 다시 확인(recheck)한다.
- MySQL 8.4 InnoDB FULLTEXT도 역색인이다. 보조 인덱스 테이블 6개(`fts_..._index_1`~`_6`)로 나눠 저장한다.

### 3. 한국어 토큰화 — 세 가지 길

```text
  원문 "삼성전자"를 무엇으로 자르나

  (a) 공백 단위   [삼성전자]                    "삼성" 검색 → 누락
  (b) n-gram(2)   [삼성][성전][전자]             "삼성" 검색 → 찾음
                                                "성전" 검색 → "성전 건축"과 "삼성전자" 둘 다 (과다 매칭)
  (c) 형태소      [삼성][전자] (+원형 삼성전자)   "삼성" 검색 → 찾음. 사전에 달렸다
```

**(b) n-gram — MySQL 8.4 ngram 파서** (로컬 재현, 예시, MySQL 8.4.10, `ngram_token_size = 2`):

```text
  문서: 1 삼성전자 주가 상승 / 2 삼성 라이온즈 우승 / 3 성전 건축 역사 / 4 엘지전자 냉장고

  공백 파서(기본):  MATCH AGAINST('삼성')      → 0건
                   MATCH AGAINST('삼성전자')   → 1
  ngram 파서:      MATCH AGAINST('삼성')      → 1, 2
                   MATCH AGAINST('성전')      → 1, 3        ← 문서 1은 "성전"과 무관
                   '"삼성전자"' IN BOOLEAN MODE → 1          ← 구(phrase)로 묶으면 좁혀진다
                   MATCH AGAINST('삼성전자')   → 1(0.2719), 2·3·4(0.0906)
                                                ← 자연어 모드는 bigram 삼성·성전·전자의 OR
```

- 공백 파서의 "삼성" 0건에는 이유가 둘이다.
  - "삼성전자"는 한 토큰이다.
  - 문서 2의 "삼성"은 두 글자라 색인되지 않았다. InnoDB 기본 `innodb_ft_min_token_size`가 3이다(MySQL 8.4 기준, 로컬 확인).
- ngram 파서는 `innodb_ft_min_token_size`·`innodb_ft_max_token_size`를 무시한다. 대신 `ngram_token_size`(기본 2, 1~10)를 쓴다. 이 값은 읽기 전용이라 서버 시작 옵션으로만 바꾼다(MySQL 8.4 14.9.8).

**(b′) 트라이그램 — PostgreSQL pg_trgm**

- 단어 앞에 공백 둘, 뒤에 공백 하나를 붙여 세 글자씩 자른다. "cat" → `"  c"`, `" ca"`, `"cat"`, `"at "`(pg_trgm 문서).
- 한글 트라이그램은 3바이트를 넘는다. 그래서 CRC 해시 상위 3바이트로 줄여 저장한다(`contrib/pg_trgm/trgm_op.c` `compact_trigram`). `show_trgm('삼성전자')`가 `{0x8881f6,...}` 같은 16진 값 5개로 보이는 이유다.
- `LIKE '%냉장고%'`에 GIN(gin_trgm_ops)을 쓰면 풀스캔을 피한다. 다만 **추출할 트라이그램이 없는 패턴**은 인덱스 전체를 훑는 것으로 떨어진다(pg_trgm 문서). `'%삼성%'`처럼 두 글자 패턴이 그렇다.

```text
  (예시, PostgreSQL 17.11, 상품 20만 행)
  LIKE '%냉장고%'  인덱스 없음 → Parallel Seq Scan, Buffers: shared hit=1771
                   gin_trgm_ops → Bitmap Index Scan (인덱스 buffers 9) + Heap 1770
  LIKE '%삼성%'    gin_trgm_ops가 있어도 → Parallel Seq Scan (planner가 인덱스를 안 고름)
```

- 이 표본에서 "냉장고" 일치가 33335행(17%)이라 힙 블록은 거의 다 읽었다. 이득은 일치 행이 적을 때 커진다.

**(c) 형태소 분석 — Elasticsearch nori** (문서 기준)

- `nori` 분석기 = `nori_tokenizer` + `nori_part_of_speech`(품사로 조사·어미 제거) + `nori_readingform`(한자 → 한글 읽기) + `lowercase`.
- 기본 사전은 mecab-ko-dic이다. `user_dictionary`로 명사(NNG)를 추가한다. 복합명사는 분해 방식도 적는다(`세종시 세종 시`).
- `decompound_mode`
  - `none`: 분해하지 않는다. `가곡역`
  - `discard`(기본): 분해하고 원형을 버린다. `가곡역 → 가곡, 역`
  - `mixed`: 분해하고 원형도 남긴다. `가곡역 → 가곡역, 가곡, 역`
- "삼성전자"가 실제로 어떻게 잘리는지는 사전 내용에 달렸다. 배포 전에 `_analyze` API로 확인한다. 로컬 ES가 없어 실제 분해 결과는 확인하지 못했다 [?].

**형태소 분석의 알고리즘 — 격자 위 최단 경로**

```text
  입력: 삼 성 전 자
  위치  0  1  2  3  4
        ├삼성──┤├전자──┤         사전 단어 후보를 간선으로 놓는다
        ├삼성전자────────┤       간선 비용 = 단어 비용 + 품사 연결 비용
        ├삼┤├성전──┤├자┤
  비터비: 위치 0 → 4 의 최소 비용 경로를 동적 계획법으로 고른다
```

- Lucene `KoreanTokenizer`(nori의 구현) 주석: "rolling Viterbi search로 입력 문자열의 최소 비용 분할(경로)을 찾는다". 연결 비용 표(`ConnectionCosts`)를 쓴다.
- 사전에 없는 신조어·상품명도 미등록어 사전(`UnknownDictionary`)이 문자 종류로 후보를 만든다(Lucene nori `Viterbi.java`). 다만 원하는 분할이 뽑힌다는 보장이 없어 엉뚱하게 잘릴 수 있다. 그래서 사용자 사전을 관리한다.

### 4. 색인 분석기와 검색 분석기는 같은 규칙이어야 한다

```text
  색인:  "running" ──english──> 'run'     ┐
                                          ├─ 같은 용어여야 맞는다
  검색:  "running" ──english──> 'run'     ┘   → 일치

  검색:  "running" ──simple───> 'running'     → 'run'과 다른 용어 → 0건
```

로컬 재현(예시, PostgreSQL 17.11):

```text
  to_tsvector('english','running') @@ to_tsquery('english','running')  → t
  to_tsvector('english','running') @@ to_tsquery('simple','running')   → f
```

- Elasticsearch 문서: "보통 색인과 검색에 같은 분석기를 써야 한다. 그래야 질의의 용어가 역색인 용어와 같은 형태가 된다."
- 일부러 다르게 쓰는 경우가 있다(`search_analyzer`).
  - 자동완성의 edge n-gram(검색어는 자르지 않는다)
  - 검색 시점 동의어
- `analyzer` 설정은 기존 필드에서 바꿀 수 없다(ES 문서). `search_analyzer`는 update mapping API로 바꿀 수 있다. 색인 분석기를 바꾸려면 새 인덱스로 재색인한다([48-search-index-sync-and-reindexing](../48-search-index-sync-and-reindexing/2-summary.md)).

### 5. 사전을 바꾸면 이미 색인된 문서는 그대로다

로컬 재현(예시, PostgreSQL 17.11) — 설정 `my_cfg`(simple 복사)로 저장한 뒤 영어 단어 매핑을 `english_stem`으로 바꿨다.

```text
   id |                 tsv
  ----+-------------------------------------
    1 | 'quickly':3 'runners':1 'running':2      ← 변경 전에 저장한 행
    2 | 'quick':3 'run':2 'runner':1             ← 변경 후에 저장한 행

  WHERE tsv @@ to_tsquery('my_cfg','run')  → 2만 나온다
```

- 저장된 tsvector(또는 역색인 항목)는 **만들 때의 규칙**으로 굳어 있다. 질의는 **지금 규칙**으로 분석된다.
- PostgreSQL 문서(12.6.4 Thesaurus): "thesaurus는 색인 때 쓰이므로 매개변수를 바꾸면 재색인이 필요하다."
- Elasticsearch도 같다. 색인 시점 동의어·사용자 사전을 바꾸면 재색인해야 한다. 검색 분석기의 `synonym_graph`는 `updateable: true`로 두면 reload API로 다시 읽는다. 이 옵션은 검색 분석기에만 쓴다(ES 문서).

### 6. 관련도 — BM25

Lucene `BM25Similarity`(Elasticsearch 기본 similarity)의 식:

```text
  score(q, d) = Σ  idf(t) × tf(t, d)               (질의 용어 t마다 더한다)
               t∈q

  idf(t)   = ln( 1 + (N − n + 0.5) / (n + 0.5) )    N = 문서 수, n = t가 든 문서 수
  tf(t, d) = f / ( f + k1 × (1 − b + b × dl / avgdl) )
                                                     f = d 안의 t 횟수
                                                     dl = d 길이, avgdl = 평균 길이
  기본 k1 = 1.2, b = 0.75
```

- *idf*: 드문 단어일수록 크다. N = 1000일 때 n = 10이면 4.56, n = 500이면 0.69다(계산 예시).
- *tf 포화*: 같은 단어가 많이 나와도 점수가 1을 넘지 않는다. dl = avgdl이면 f = 1 → 0.45, 2 → 0.63, 10 → 0.89다(계산 예시). 키워드 도배가 잘 안 먹힌다.
- *길이 정규화*: 긴 문서는 단어가 우연히 들어갈 확률이 높다. f = 1일 때 dl/avgdl = 0.5면 0.57, 2면 0.32다(계산 예시).
- Lucene은 교과서 식의 분자 `(k1 + 1)`을 빼고 계산한다. 모든 문서에 같은 상수를 곱하는 것이라 순위는 같다.
- 분산 검색 엔진에서 통계(N, n, avgdl)를 샤드마다 따로 세면, 문서가 적은 샤드에서 점수가 튈 수 있다. Elasticsearch 기본 `search_type`인 `query_then_fetch`는 샤드 로컬 통계로 점수를 매긴다. `dfs_query_then_fetch`는 전 샤드의 전역 통계를 먼저 모은다(Search API 문서).

**PostgreSQL과 MySQL은 BM25가 아니다**

- PostgreSQL 17 `ts_rank`는 "일치하는 lexeme의 빈도"로 매긴다. `ts_rank_cd`는 근접도(cover density)를 더한다.
- 문서: 두 함수 모두 **전역 정보(문서 빈도 등)를 쓰지 않는다**. 그래서 idf가 없다.

```text
  (예시, PostgreSQL 17.11)
  ts_rank(to_tsvector('simple','a b c'),     to_tsquery('simple','a')) = 0.0608
  ts_rank(to_tsvector('simple','a a a b c'), to_tsquery('simple','a')) = 0.0827
```

- MySQL 8.4 InnoDB: "Sphinx를 본떴고, 알고리즘은 BM25와 TF-IDF 순위 알고리즘에 기반한다"(Boolean Full-Text Searches 절). 정확한 식은 문서에 없다 [?].

## 쓰이는 자료구조·알고리즘

- **역색인 + 게시 목록 교집합** — [data-structure/32-inverted-index](../../data-structure/32-inverted-index/2-summary.md). PostgreSQL GIN, InnoDB FULLTEXT 보조 테이블, Lucene 세그먼트.
- **용어 사전 = 정렬된 사전·FST** — Lucene은 용어 사전 색인에 FST를 쓴다. [data-structure/09-trie](../../data-structure/09-trie/2-summary.md)
- **n-gram·트라이그램** — 부분 문자열 검색을 역색인 조회로 바꾼다. pg_trgm은 멀티바이트 트라이그램을 CRC로 줄인다.
- **BM25** — idf × 포화 tf × 길이 정규화.
- **형태소 분석** — 사전 단어로 만든 격자 위에서 비터비(동적 계획법) 최소 비용 경로. [algorithm/21-dp-basics](../../algorithm/21-dp-basics/2-summary.md), [algorithm/14-dijkstra](../../algorithm/14-dijkstra/2-summary.md)(최단 경로의 DAG 특수형)
- **GiST 시그니처** — PostgreSQL tsvector GiST는 단어를 비트 하나로 해시해 OR한 고정 길이 시그니처다(기본 124바이트). 거짓 일치가 생겨 행을 다시 확인한다. [data-structure/11-bloom-filter](../../data-structure/11-bloom-filter/2-summary.md)와 같은 원리다.

## 적용 — 풀어나가는 법

### 1. 무엇을 쓸지 고르기

```text
  데이터가 DB에 있고, 검색이 부가 기능이다
    ├─ 영어·공백 언어 위주     → PostgreSQL tsvector + GIN
    ├─ 한국어 부분 문자열       → pg_trgm GIN (3글자 이상 질의) / MySQL ngram
    └─ 한국어 정확도·동의어·순위가 핵심 → 검색 엔진(ES/OpenSearch + nori)
                                       + 동기화 문제(48)를 떠안는다
```

### 2. PostgreSQL 17 전문 검색 기본형

```sql
-- 저장 열 + GIN
ALTER TABLE post ADD COLUMN tsv tsvector
  GENERATED ALWAYS AS (
    setweight(to_tsvector('simple', coalesce(title,'')), 'A') ||
    setweight(to_tsvector('simple', coalesce(body ,'')), 'D')) STORED;
CREATE INDEX post_tsv ON post USING gin (tsv);

-- 사용자 입력은 websearch_to_tsquery (문법 오류를 내지 않는다)
SELECT id, title, ts_rank(tsv, q) AS r
FROM post, websearch_to_tsquery('simple', '삼성 냉장고') q
WHERE tsv @@ q
ORDER BY r DESC LIMIT 20;
```

- `to_tsvector(NULL)`은 NULL이다. 문서는 `coalesce`를 권한다.
- 접두사 일치는 `to_tsquery('simple','삼성:*')`다. 로컬 재현에서 `'삼성'` 정확 일치는 0건, `'삼성:*'`는 40000건이었다(상품 20만 행 중 "삼성전자" 40000행).
- 단어 가운데("삼성전자"의 "전자")는 `:*`로도 못 찾는다(로컬 재현 `전자:*` → f).

### 3. 한국어 부분 문자열 — pg_trgm

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX product_name_trgm ON product USING gin (name gin_trgm_ops);
EXPLAIN (ANALYZE, BUFFERS) SELECT count(*) FROM product WHERE name LIKE '%냉장고%';
-- Bitmap Index Scan on product_name_trgm 이 보이면 인덱스를 탄다
```

- 앞뒤가 `%`인 두 글자 이하 질의(`'%삼성%'`)는 트라이그램이 안 나와 인덱스 이득이 없다. 앞이 고정된 `'삼성%'`는 앞 공백을 붙인 트라이그램이 나와 인덱스를 탄다(로컬 재현, 예시, PostgreSQL 17.11: 20만 행에서 `Bitmap Index Scan on p_trgm`, `'%삼성%'`는 `Parallel Seq Scan`). 앱에서 최소 길이를 두거나, 두 글자는 다른 경로(접두사 B-tree, 자동완성 사전)로 보낸다.

### 4. MySQL 8.4 — ngram 파서

```sql
CREATE TABLE doc_ng (
  id INT PRIMARY KEY,
  body VARCHAR(200),
  FULLTEXT (body) WITH PARSER ngram
) ENGINE=InnoDB;

SELECT id FROM doc_ng WHERE MATCH(body) AGAINST('"삼성전자"' IN BOOLEAN MODE);  -- 구로 좁힌다
```

- 자연어 모드에 긴 검색어를 넣으면 bigram OR가 돼 무관한 문서가 따라온다(재현: "엘지전자 냉장고"가 '삼성전자' 결과에 나옴). 구 검색이나 `+` 연산자로 좁힌다.
  - ngram 구 검색은 원문 문자열 일치가 아니라 토큰 구 일치다. 문서: 구 "abc"는 "ab bc"로 바뀌어 "abc"와 "ab bc"를 둘 다 찾는다(MySQL 8.4 14.9.8 ngram Parser Phrase Search). 정확한 문자열이 필요하면 `LIKE`·앱 쪽 조건을 덧붙인다.
- `innodb_ft_min_token_size`·`ngram_token_size`를 바꾸면 서버 재시작과 FULLTEXT 인덱스 재구축이 필요하다. InnoDB 불용어 설정(`innodb_ft_server_stopword_table` 등)은 재시작 없이 바꿀 수 있지만 재구축은 필요하다(MySQL 8.4 14.9.6 "Rebuilding InnoDB Full-Text Indexes").

### 5. Elasticsearch nori 매핑 예

```json
PUT products
{
  "settings": { "analysis": {
    "tokenizer": { "ko_tok": { "type": "nori_tokenizer", "decompound_mode": "mixed",
                               "user_dictionary": "userdict_ko.txt" } },
    "filter": { "ko_syn": { "type": "synonym_graph", "synonyms_path": "syn_ko.txt",
                            "updateable": true } },
    "analyzer": {
      "ko_index":  { "tokenizer": "ko_tok", "filter": ["nori_part_of_speech", "lowercase"] },
      "ko_search": { "tokenizer": "ko_tok", "filter": ["nori_part_of_speech", "lowercase", "ko_syn"] }
    } } },
  "mappings": { "properties": {
    "name": { "type": "text", "analyzer": "ko_index", "search_analyzer": "ko_search" } } }
}
```

- 동의어는 검색 분석기에 둔다. 사전을 고쳐도 재색인 없이 reload로 반영된다.
- 사용자 사전은 **색인 분석기**에도 쓰인다. 사용자 사전을 고치면 재색인해야 한다.

### 6. 앱 코드 — 사용자 입력은 파라미터로

```java
// JDBC: 검색어를 SQL 문자열에 붙이지 않는다
String sql = """
    SELECT id, title FROM post
    WHERE tsv @@ websearch_to_tsquery('simple', ?)
    ORDER BY ts_rank(tsv, websearch_to_tsquery('simple', ?)) DESC
    LIMIT 20""";
try (PreparedStatement ps = conn.prepareStatement(sql)) {
    ps.setString(1, userInput);
    ps.setString(2, userInput);
    ResultSet rs = ps.executeQuery();
}
```

- `to_tsquery`에 원문을 넘기면 `&`·`|`·괄호 문법 오류가 난다. 사용자 입력은 `websearch_to_tsquery`나 `plainto_tsquery`를 쓴다.
- `ts_headline` 출력은 XSS에 안전하지 않다(PostgreSQL 문서 경고). HTML로 낼 때는 이스케이프·새니타이저를 거친다.

## 장애 시나리오와 대처

### 1. "삼성"으로 검색했는데 "삼성전자" 상품이 안 나온다

- **현상**: 사용자가 브랜드명으로 찾는데 대표 상품이 빠진다.
- **보이는 형태**: 에러 없음. 결과 0건 또는 일부만. PostgreSQL `to_tsvector('simple', …)`에 `'삼성전자'` 한 덩어리만 있다.
- **원인**: 공백 토크나이저는 붙여 쓴 복합어를 자르지 않는다. MySQL 기본 파서는 추가로 3글자 미만 단어를 색인하지 않는다.
- **대처**: 분석기를 바꾼다(n-gram 또는 형태소 + `decompound_mode: mixed`). 급하면 접두사 질의(`:*`)로 일부를 메운다. 분석기를 바꾸면 재색인해야 한다.

### 2. n-gram 과다 매칭 — 무관한 결과가 섞인다

- **현상**: "성전"을 찾았는데 "삼성전자"가 나온다. 긴 검색어일수록 잡음이 많다.
- **보이는 형태**: 재현(MySQL ngram): '성전' → "삼성전자 주가 상승"·"성전 건축 역사". 자연어 모드 '삼성전자' → 4건 중 3건이 무관(점수 0.0906).
- **원인**: bigram은 단어 경계를 모른다. 자연어 모드는 bigram들을 OR로 찾는다.
- **대처**: 구 검색(`"…"` BOOLEAN MODE)이나 필수 연산자로 좁힌다. n-gram 필드와 형태소 필드를 함께 두고, 형태소 일치에 가중치를 더 준다.

### 3. 색인 분석기와 검색 분석기 불일치 → 0건

- **현상**: 배포 뒤 특정 필드 검색이 전부 0건이다.
- **보이는 형태**: 에러 없음. 재현: 'english'로 만든 tsvector에 'simple' tsquery → `f`. ES에서는 `_analyze`로 색인 쪽과 검색 쪽 토큰을 비교하면 다르게 나온다.
- **원인**: 질의 쪽 설정(PostgreSQL `default_text_search_config`, 쿼리에 박은 설정 이름, ES `search_analyzer`)이 색인 쪽과 다르다.
  - PostgreSQL 식 인덱스는 설정 이름을 명시한 식(`to_tsvector('simple', name)`)과 **똑같은 식**으로 질의해야 탄다.
- **대처**: 설정 이름을 코드와 인덱스 정의에 명시해 맞춘다. ES는 `_analyze` 비교를 배포 전 테스트에 넣는다.

### 4. 사전을 고쳤는데 옛 문서가 여전히 안 나온다

- **현상**: 사용자 사전에 "갤럭시탭"을 넣었다. 새 상품은 나오는데 기존 상품은 안 나온다.
- **보이는 형태**: 재현(PostgreSQL): 매핑 변경 전 행은 `'running'`, 후 행은 `'run'`. `'run'` 질의는 새 행만 찾는다.
- **원인**: 이미 저장된 용어는 옛 규칙의 결과다. 재색인 없이 새 규칙은 새로 쓰는 문서에만 적용된다.
- **대처**: 사전 변경 = 재색인 작업으로 묶는다. PostgreSQL은 저장 열을 다시 계산한다(`UPDATE … SET body = body`는 행을 전부 다시 쓴다. 청크로 나눠서 한다). ES는 새 인덱스로 재색인하고 별칭을 바꾼다. 검색 시점 동의어처럼 재색인 없이 되는 변경은 따로 분류한다.

### 5. `LIKE '%…%'` 풀스캔

- **현상**: 상품 수가 늘면서 검색 API p99가 선형으로 늘어난다. DB CPU가 오른다.
- **보이는 형태**: `EXPLAIN`에 `Seq Scan … Filter: (name ~~ '%냉장고%')`. `pg_stat_statements`에서 이 쿼리의 호출당 `shared_blks_hit + shared_blks_read`가 테이블 블록 수에 가깝다.
- **원인**: 앞 `%`가 있으면 B-tree를 쓸 수 없다.
- **대처**: pg_trgm GIN(3글자 이상) 또는 전문 검색 인덱스로 옮긴다. 앞뒤 `%`인 두 글자 질의는 인덱스를 못 타므로 입력 최소 길이를 둔다.

## 핵심 문장

- 전문 검색은 "분석기로 정규화한 용어 → 문서 목록"인 역색인을 만들어 두고, 질의도 같은 분석기로 정규화해 찾는다.
- 색인 쪽과 검색 쪽 분석이 다르면 만들어진 용어가 어긋나, 에러 없이 0건이나 누락이 생길 수 있다.
- 한국어는 공백 단위로는 조사·복합어 때문에 누락되고, n-gram은 경계를 몰라 과다 매칭하며, 형태소 분석은 사전 품질에 달렸다.
- 저장된 용어는 만들 때의 규칙으로 굳어 있으므로, 색인 쪽 사전·분석기를 바꾸면 재색인이 필요하다.
- BM25는 드문 단어에 가중치(idf)를 주고, 같은 단어 반복의 효과를 포화시키고, 긴 문서를 깎는다. PostgreSQL `ts_rank`는 전역 통계를 쓰지 않아 idf가 없다.

## 관련 주제·근거

버전 기준: PostgreSQL 17(로컬 17.11), MySQL 8.4(로컬 8.4.10), Elasticsearch 현행 문서(2026-10 확인), Apache Lucene `main` 소스. Elasticsearch 서버는 로컬에 없어 문서와 Lucene 소스로만 확인했다.

- 선행
  - [40-filters-and-specialized-indexes](../40-filters-and-specialized-indexes/2-summary.md)
  - [data-structure/32-inverted-index](../../data-structure/32-inverted-index/2-summary.md) — 역색인 기초
- 후속
  - [47-autocomplete-and-typeahead](../47-autocomplete-and-typeahead/2-summary.md) — 접두사 완성, edge n-gram, 한글 자모
  - [48-search-index-sync-and-reindexing](../48-search-index-sync-and-reindexing/2-summary.md) — DB → 검색 인덱스 동기화, 별칭 교체 재색인
  - [10-collation-and-text-comparison](../10-collation-and-text-comparison/2-summary.md)
- 후속(AI 엔지니어링): [ai-engineering/04-tokenization-and-token-cost](../../ai-engineering/04-tokenization-and-token-cost/2-summary.md) — LLM 토크나이저(BPE)와 검색 분석기 토큰화의 차이 · [ai-engineering/17-hybrid-search-and-reranking](../../ai-engineering/17-hybrid-search-and-reranking/2-summary.md) — BM25 + 벡터 검색의 RRF 합성·재순위
- PostgreSQL 17 문서
  - 12.3 Controlling Text Search — `to_tsvector`, `websearch_to_tsquery`, `ts_rank`·`ts_rank_cd`("do not use any global information"), `ts_headline` XSS 경고 <https://www.postgresql.org/docs/17/textsearch-controls.html>
  - 12.6 Dictionaries — 12.6.4 Thesaurus("changes … require reindexing") <https://www.postgresql.org/docs/17/textsearch-dictionaries.html>
  - 12.9 Preferred Index Types — GIN(lexeme별 압축 위치 목록, weight는 recheck), GiST(시그니처 기본 124바이트, lossy) <https://www.postgresql.org/docs/17/textsearch-indexes.html>
  - F.33 pg_trgm — 트라이그램 추출 규칙, 임계값 기본 0.3·0.6·0.5, "no extractable trigrams → full-index scan" <https://www.postgresql.org/docs/17/pgtrgm.html>
  - 소스 `contrib/pg_trgm/trgm_op.c` `compact_trigram`(REL_17_STABLE)
- MySQL 8.4 Reference Manual
  - 14.9.8 ngram Full-Text Parser(`ngram_token_size` 1~10, 최소·최대 길이 옵션 무시) <https://dev.mysql.com/doc/refman/8.4/en/fulltext-search-ngram.html>
  - 14.9.6 Fine-Tuning MySQL Full-Text Search(재시작·재구축 조건, `OPTIMIZE TABLE`) · 14.9.2 Boolean Full-Text Searches("based on BM25 and TF-IDF") · 17.6.2.4 InnoDB Full-Text Indexes(보조 테이블 6개)
- Elasticsearch 문서
  - Nori analysis plugin — `nori` analyzer, `nori_tokenizer`(`decompound_mode` 기본 discard, mecab-ko-dic, `user_dictionary`) <https://www.elastic.co/docs/reference/elasticsearch/plugins/analysis-nori-tokenizer>
  - `analyzer`(기존 필드에서 갱신 불가) · `search_analyzer`(기존 필드에서 갱신 가능) 매핑 파라미터 · Synonym graph token filter(`updateable`, "search analyzer only") · Similarity(BM25 기본 k1 1.2, b 0.75)
  - Search API `search_type` — "query_then_fetch: Documents are scored using local term and document frequencies for the shard" <https://www.elastic.co/docs/api/doc/elasticsearch/operation/operation-search>
- Apache Lucene `main`
  - `lucene/core/.../search/similarities/BM25Similarity.java` — idf·tf 식, 기본값
  - `lucene/analysis/nori/.../KoreanTokenizer.java` — "rolling Viterbi search … least cost segmentation"
- 교재·논문
  - Manning, Raghavan, Schütze 『Introduction to Information Retrieval』 2.2 토큰화(복합어·띄어쓰기 없는 언어의 분절), 6장 점수·tf-idf, 11.4.3 Okapi BM25 <https://nlp.stanford.edu/IR-book/>
  - Robertson, Zaragoza, "The Probabilistic Relevance Framework: BM25 and Beyond", 2009 (원문 미열람)
- 로컬 재현(PostgreSQL 17.11, MySQL 8.4.10): `simple`·`english` tsvector, 접두사·중간 일치, 트라이그램 해시·유사도, `LIKE '%…%'` 실행 계획(트라이그램 GIN 전후, 두 글자 패턴), 설정 변경 전후 tsvector, 분석기 불일치, `ts_rank` 비교, MySQL 공백 파서 vs ngram 파서 결과·점수
