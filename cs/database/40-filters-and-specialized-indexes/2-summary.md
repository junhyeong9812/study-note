# database/40-filters-and-specialized-indexes — 필터와 특수 인덱스: 블룸·역색인·공간·BRIN — 정리 (힌트)

## 해결하는 문제

B+Tree는 **값 전체의 정렬 순서**로 찾는다. 그래서 순서로 표현되지 않는 질문에는 약하다.

```text
  질문                                    B+Tree로 안 되는 이유                   쓰는 것
  "본문에 '삼성전자'가 들어간 글"             '%삼성전자%'는 정렬의 어느 구간도 아니다     역색인 (GIN, FULLTEXT)
  "이 점에서 가까운 가게 3곳"                 2차원 거리는 한 줄 정렬로 표현이 안 된다     공간 인덱스 (R-tree, GiST)
  "로그 30억 행 중 어제 1시간"               B+Tree도 되지만 인덱스가 수십 GB(예시)   BRIN (블록 범위 요약)
  "이 키가 이 파일에 있을까?"                 파일을 열어 보기 전에 "없음"을 알고 싶다     블룸 필터
```

쉬운 예: 도서관이다.
- 제목순 카드 목록(B+Tree)은 "제목이 '데'로 시작하는 책"을 잘 찾는다.
- "본문에 '트랜잭션'이 나오는 책"은 책 뒤의 **찾아보기**(단어 → 쪽 번호)가 있어야 한다. 역색인이다.
- "서가 3번은 2020~2021년 책만 있다"는 서가별 쪽지만 있어도 다른 서가를 건너뛸 수 있다. BRIN이다.
- "이 책이 이 분관에 있나?"를 전화로 물으면 "확실히 없다" 또는 "있을 수도 있다"로만 답해 주는 사서가 있다. 블룸 필터다.

똑같은 구조다.\
질문의 모양에 맞는 **다른 자료구조**를 인덱스로 쓴다.

실무 예:
- 상품 검색을 `WHERE name LIKE '%키보드%'`로 구현했다. 상품이 늘자 검색 한 번이 테이블 전체를 읽는다.
- 로그 테이블의 시간 컬럼 B+Tree 인덱스가 테이블 크기의 몇 분의 일을 차지한다.

## 동작·원리

### 1. 블룸 필터 — "없다"는 확실, "있다"는 아마도

```text
  비트 배열 m칸, 해시 함수 k개 (예시: m = 16, k = 3)

  insert("A"): h1=2, h2=7, h3=11 → 비트 2, 7, 11을 1로
  insert("B"): h1=7, h2=9, h3=14 → 비트 7, 9, 14를 1로

  비트: 0 0 1 0 0 0 0 1 0 1 0 1 0 0 1 0
            ^         ^   ^   ^     ^
  lookup("C"): h = 2, 9, 11 → 모두 1 → "있을 수도"  (실제로는 없음 = 거짓 양성)
  lookup("D"): h = 3, 7, 9  → 비트 3이 0 → "확실히 없음"
```

- 거짓 음성은 없고 거짓 양성은 있다(CMU 15-445 L9). "있다"면 실제 데이터를 확인해야 한다.
  - *거짓 양성(false positive)*: 없는데 "있을 수도"라고 답하는 것.
- 비트를 많이 쓸수록 거짓 양성이 준다. RocksDB 위키의 표: 키당 약 9.9비트면 1%, 15.5비트면 0.1%다.
- 기본 블룸 필터는 삭제를 못 한다. 비트를 끄면 다른 키의 비트까지 끌 수 있다. 삭제가 필요하면 카운팅 블룸 필터나 쿠쿠 필터를 쓴다(CMU L9).
- DB에서 쓰이는 자리
  - LSM 엔진(RocksDB 등)은 SST 파일마다 블룸 필터를 둔다. 키가 없는 파일은 열지 않는다(38번).
  - 해시 조인에서 빌드 쪽 키로 필터를 만들어 프로브 쪽 행을 미리 거른다(CMU L12, 11번).
  - PostgreSQL `bloom` 확장: 행마다 여러 컬럼을 한 서명(signature)에 담는다. 서명 길이 기본 80비트다. 손실이 있어 힙에서 다시 확인한다. 등호 조건만 된다(PostgreSQL 17 F.6).

```text
  bloom 인덱스 (a, b, c, d), 20만 행 (로컬 재현, 예시, PostgreSQL 17.11)
  크기: 테이블 10 MB, bloom 3152 kB, 같은 컬럼 B-tree 6176 kB
  WHERE c = 7 AND d = 42  (선행 컬럼 a, b 없음)
    → Bitmap Index Scan on tb_bloom  Buffers: 393 (인덱스 전체)   rows=3
    → Recheck 후 Rows Removed by Index Recheck: 3  → 결과 0행 (셋 다 거짓 양성)
```

- bloom 인덱스는 **인덱스 전체를 순차로 읽는다**. 대신 크기가 작고, 컬럼 조합에 상관없이 쓸 수 있다. 문서는 "임의 컬럼 조합을 검사하는 쿼리"에 맞고, 한 조합에는 B-tree가 더 빠르다고 적는다(F.6).

### 2. 역색인 — 단어 → 행 목록

```text
  문서                               역색인 (키 → 포스팅 리스트)
  1: "삼성전자 주가가 올랐다"          '삼성전자' → {1}
  2: "삼성 라이온즈 우승"              '삼성'     → {2}
  3: "전자 제품 할인"                 '전자'     → {3}
                                    '올랐다'   → {1}  ...
```

- *포스팅 리스트(posting list)*: 그 키가 들어 있는 행 ID 목록.
- PostgreSQL **GIN**(Generalized Inverted Index)은 (키, 포스팅 리스트) 쌍을 저장한다. 키는 한 번만 저장되고, 키 사전은 B+Tree다(PostgreSQL 17 64.4, CMU L9).
- 키를 무엇으로 뽑느냐가 **분석기**다. 같은 문서라도 키가 달라지면 찾을 수 있는 것이 달라진다.

```text
  (a) 공백 단위 단어 (PG to_tsvector('simple'), MySQL 기본 FULLTEXT 파서)
      '삼성전자 주가가 올랐다' → '삼성전자' '주가가' '올랐다'
      '삼성' 검색 → 없음        '삼성:*' 접두어 검색 → 있음         (로컬 재현, PG 17.11)

  (b) 트라이그램 (PG pg_trgm) — 연속 3글자
      LIKE '%삼성전자%' → 패턴의 트라이그램을 역색인에서 찾고 힙에서 재확인

  (c) n-gram (MySQL ngram 파서, 기본 2글자)
      '삼성전자' → '삼성' '성전' '전자'
```

- 한국어는 띄어쓰기 단위 어절에 조사가 붙는다(`주가가`). 공백 단위 분석기로는 `주가`를 못 찾는다. 형태소 분석이나 n-gram이 필요하다. 형태소 분석은 46번에서 다룬다.
- **pg_trgm**은 패턴에서 트라이그램을 뽑아 GIN/GiST 인덱스를 찾는다. B-tree와 달리 패턴이 앞에 고정될 필요가 없다. 뽑을 트라이그램이 없는 패턴은 인덱스 전체 스캔으로 떨어진다(PostgreSQL 17 F.33).
- **MySQL 8.4 InnoDB FULLTEXT**
  - 기본 파서는 공백·구두점으로 단어를 나눈다. `innodb_ft_min_token_size`(기본 3)보다 짧은 단어는 색인하지 않는다. 로컬 재현(MySQL 8.4.10)에서 두 글자 `삼성`은 기본 파서로 0건이었다.
  - `WITH PARSER ngram`은 `ngram_token_size`(기본 2) 글자씩 자른다. 최소 길이 설정은 적용되지 않는다(14.9.6, 14.9.8).
  - ngram 검색어 변환: **자연어 모드**는 n-gram들의 합집합(OR), **불리언 모드**는 n-gram 구(phrase) 검색이다(14.9.8).

```text
  ngram 인덱스, 문서: 1 '삼성전자 주가가 올랐다' 2 '삼성 라이온즈 우승' 3 '전자 제품 할인' 4 '성전 이야기'
  (로컬 재현, 예시, MySQL 8.4.10)
  AGAINST('삼성전자' IN BOOLEAN MODE)          → 1              ("삼성 성전 전자" 구)
  AGAINST('삼성전자' IN NATURAL LANGUAGE MODE) → 1, 2, 3, 4     (삼성 OR 성전 OR 전자)
```

- **쓰기 비용**: 행 하나가 키 여러 개를 만든다. 그래서 GIN 갱신은 느리다. PostgreSQL GIN은 새 항목을 **대기 목록(pending list)**에 모았다가 VACUUM·autoanalyze·`gin_clean_pending_list()` 또는 `gin_pending_list_limit`(기본 4MB) 초과 때 본 구조로 옮긴다(`fastupdate`, 기본 켜짐). 검색은 대기 목록도 훑어야 하고, 한도를 넘긴 한 번의 쓰기가 정리 비용을 떠안는다(64.4.4.1).

```text
  같은 10만 행 INSERT (로컬 재현, 예시, PostgreSQL 17.11)
  인덱스 없음                  75 ms
  pg_trgm GIN 인덱스 있음     2982 ms    (직후 pending_pages 315)
  테이블 9880 kB,  GIN 인덱스 14 MB   ← 인덱스가 테이블보다 크다
```

### 3. 공간 인덱스 — R-tree

```text
  노드마다 자식들을 감싸는 최소 경계 사각형(MBR)을 둔다

  루트:  [R1: (0,0)-(50,100)]   [R2: (50,0)-(100,100)]
            │                       │
     [a][b][c] (가게 점들)     [d][e][f]

  질의 "사각형 (10,10)-(11,11) 안의 가게" → MBR이 겹치는 가지만 내려간다
  질의 "(50,50)에서 가까운 3곳"          → 거리 하한이 작은 가지부터 (KNN)
```

- 1차원 정렬 대신 **경계 사각형의 포함 관계**로 트리를 만든다. 겹치지 않는 가지는 통째로 건너뛴다.
- PostgreSQL은 GiST로 R-tree와 같은 기능을 구현한다(PostgreSQL 17 64.2). `<->` 거리 연산자로 가까운 순 정렬도 인덱스로 한다.
- MySQL 8.4의 `SPATIAL INDEX`는 R-tree 인덱스를 만든다(13.4.10). 컬럼은 `NOT NULL`이어야 하고, 옵티마이저는 컬럼에 명시적 `SRID` 속성이 있을 때만 그 인덱스를 쓴다(10.3.3). 문서가 보여 주는 용도는 `WHERE MBRContains(…)` 같은 영역 검색이다(13.4.11).
- 로컬 재현(예시, PostgreSQL 17.11, 점 20만 개): 1×1 사각형 질의는 `Bitmap Index Scan on shop_gist`로 인덱스 페이지 5개만 읽었다. `ORDER BY loc <-> point '(50,50)' LIMIT 3`은 `Index Scan … Order By`로 0.27 ms였다.

### 4. BRIN — 블록 범위마다 요약값만 (기본 minmax는 최솟값·최댓값)

```text
  테이블 페이지:  [0 ~ 127] [128 ~ 255] [256 ~ 383] ...     pages_per_range = 128 (기본)
  BRIN 항목:      min~max    min~max     min~max

  시간순으로 쌓인 로그:  [01-01 00:00 ~ 01-01 04:30] [~ 09:00] [~ 13:30] ...  → 범위가 겹치지 않는다
    WHERE ts in [어제 1시간] → 겹치는 범위 1~2개만 읽는다

  무작위로 섞인 로그:    [01-01 ~ 01-04] [01-01 ~ 01-04] [01-01 ~ 01-04] ... → 모든 범위가 겹친다
    → 모든 범위를 읽는다 (인덱스가 쓸모없다)
```

- 블록 범위(연속한 페이지 묶음)마다 요약값(정렬 가능한 타입은 최솟값·최댓값)만 저장한다. 인덱스가 아주 작다(PostgreSQL 17 64.5).
  - 요약 방식은 연산자 클래스가 정한다. 기본 `minmax` 말고도 `minmax-multi`(최솟값·최댓값 여러 쌍), `inclusion`(값을 감싸는 값), `bloom`(범위별 블룸 필터, 등호용)이 있다(64.5.2). 이 노트의 그림·재현은 `minmax` 기준이다.
- 손실이 있다. 요약이 조건과 겹치는 범위의 **모든 행**을 돌려주고, 실행기가 다시 확인한다.
- 기본 `minmax` BRIN은 **컬럼 값이 물리적 위치와 상관이 있을 때만** 쓸모가 있다. 시간순 적재 로그, 증가하는 ID가 대표적이다.

```text
  로컬 재현 (예시, PostgreSQL 17.11, 30만 행, 17 MB)
  B-tree(ts) 6600 kB      BRIN(ts) 24 kB

  시간순 테이블   (pg_stats correlation = 1)
    1시간 질의 → Bitmap Heap Scan  Heap Blocks: lossy=256  Rows Removed by Index Recheck: 31216   3.2 ms
  섞인 테이블     (correlation = 0.004)
    1시간 질의 → 플래너가 Parallel Seq Scan 선택 (2240 블록)
    BRIN 강제   → Heap Blocks: lossy 합계가 테이블 전체 — 이득 없음
```

- 이미 요약된 범위(끝의 덜 찬 범위 포함)에 들어온 행은 요약에 바로 반영된다. 그러나 마지막 요약 범위를 벗어난 **새 범위**는 자동으로 요약되지 않는다. VACUUM(자동 포함)이나 `brin_summarize_new_values()`가 요약을 만든다. `autosummarize`는 기본 꺼짐이다(64.5.1.1). 요약되지 않은 범위는 조건과 상관없이 통째로 결과에 넣는다(`brin.c` `bringetbitmap`: "For page ranges with no indexed tuple, we must return the whole range"). 적재 직후 요약 전이면 BRIN이 덜 걸러 준다.

## 쓰이는 자료구조·알고리즘

- **블룸 필터** — 비트 배열 + 해시 k개. [data-structure/11-bloom-filter](../../data-structure/11-bloom-filter/2-summary.md)
- **역색인** — 키 사전(B+Tree·FST) + 포스팅 리스트(정렬된 행 ID, 압축). [data-structure/32-inverted-index](../../data-structure/32-inverted-index/2-summary.md)
- **R-tree** — 최소 경계 사각형으로 묶는 균형 트리. [data-structure/25-spatial-index](../../data-structure/25-spatial-index/2-summary.md)
- **GiST·SP-GiST** — PostgreSQL이 "키가 무엇이고 어떻게 겹치는가"만 정의하면 균형 트리(GiST) 또는 공간 분할 트리(SP-GiST, 쿼드트리·k-d 트리·기수 트리)를 만들어 주는 틀(64.2, 64.3).
- **존 맵(zone map)** — BRIN처럼 블록마다 최솟값·최댓값을 두어 건너뛰는 방식. 컬럼 저장 엔진의 파트·그래뉼 요약도 같은 발상이다(37·45번).
- **트라이그램·n-gram** — 문자열을 고정 길이 조각 집합으로 바꿔, 부분 문자열 검색을 "조각들의 교집합"으로 바꾼다.

## 적용 — 풀어나가는 법

### 1. 질문의 모양으로 고른다

```text
  질문                                      PostgreSQL 17                    MySQL 8.4
  부분 문자열 LIKE '%x%'                     GIN + pg_trgm                    FULLTEXT ngram (의미가 조금 다름)
  단어 검색·관련도                           tsvector + GIN                    FULLTEXT (기본·ngram 파서)
  배열·JSON 원소 포함(@>)                    GIN                              다중 값 인덱스(JSON 배열)
  좌표·영역·가까운 순                        GiST (PostGIS 포함)               SPATIAL INDEX (R-tree, 영역 검색. 가까운 순은 [?])
  시간순 적재 대형 테이블의 범위               BRIN                             (없음 — 파티셔닝으로 대신)
  많은 컬럼의 임의 등호 조합                   bloom 확장                        (없음)
  검색 품질이 중요(형태소·동의어·랭킹)          전용 검색 엔진 검토 (46~48번)
```

### 2. SQL

```sql
-- PostgreSQL 17: 부분 문자열 검색
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX product_name_trgm ON product USING gin (name gin_trgm_ops);
EXPLAIN (ANALYZE, BUFFERS) SELECT id FROM product WHERE name LIKE '%키보드%';

-- 시간순 로그
CREATE INDEX logs_ts_brin ON logs USING brin (ts) WITH (pages_per_range = 128);
SELECT correlation FROM pg_stats WHERE tablename = 'logs' AND attname = 'ts';  -- 1에 가까워야

-- 공간
CREATE INDEX shop_gist ON shop USING gist (loc);
SELECT id FROM shop ORDER BY loc <-> point '(50,50)' LIMIT 3;

-- GIN 대기 목록 확인·정리 (pgstattuple 확장)
SELECT * FROM pgstatginindex('product_name_trgm');
SELECT gin_clean_pending_list('product_name_trgm');
```

```sql
-- MySQL 8.4: 한국어 부분 검색
CREATE TABLE article (
  id BIGINT PRIMARY KEY, body TEXT,
  FULLTEXT KEY ft_body (body) WITH PARSER ngram
) ENGINE=InnoDB;
SELECT id FROM article WHERE MATCH(body) AGAINST('삼성전자' IN BOOLEAN MODE);
```

- 로컬 재현(예시, PostgreSQL 17.11, 20만 행): `LIKE '%abc12%'`는 인덱스 없이 `Parallel Seq Scan` 26 ms(3077 버퍼), pg_trgm GIN 뒤 `Bitmap Index Scan` 0.21 ms(24 버퍼).
- 참고: 접두어 검색 `LIKE 'abc%'`는 B-tree로 되지만, 데이터베이스 collation이 `C`가 아니면 `text_pattern_ops` 연산자 클래스가 필요하다(PostgreSQL 17 11.2, 11.10). 로컬 재현(`en_US.utf8`)에서 일반 B-tree로는 `Seq Scan`, `text_pattern_ops` 인덱스로는 `Index Scan`이었다.

## 장애 시나리오와 대처

### 1. 전문 검색을 `LIKE '%x%'`로 → 풀스캔

- **현상**: 검색 API가 데이터가 늘수록 느려지고, 검색이 몰리면 DB CPU가 치솟는다.
- **보이는 형태**: PostgreSQL `Seq Scan` + `Filter: (name ~~ '%키보드%'::text)` + 큰 `Rows Removed by Filter`. MySQL `Table scan` + `Filter: (… like '%…%')`(로컬 재현). 슬로 쿼리 로그의 `Rows_examined` = 테이블 행 수.
- **원인**: 앞이 `%`인 패턴은 B-tree 정렬의 어느 구간에도 대응하지 않는다.
- **대처**
  - PostgreSQL: pg_trgm GIN 인덱스. 패턴에서 뽑을 트라이그램이 없으면 인덱스 전체 스캔이 된다(F.33). 로컬 재현에서 두 글자 `'%ab%'`는 플래너가 `Seq Scan`을 골랐다.
  - MySQL: FULLTEXT ngram 인덱스 + `MATCH … AGAINST`. `LIKE`와 의미가 다르다(모드별 매칭 규칙). 결과 차이를 테스트한다.
  - 검색 품질(형태소, 랭킹)이 요구되면 검색 엔진으로 분리한다(46~48번).

### 2. 한국어 검색 누락·과다 매칭

- **현상**: "삼성"으로 검색하면 "삼성전자" 글이 안 나온다. 또는 "삼성전자" 검색에 무관한 글이 섞인다.
- **보이는 형태** (로컬 재현, 예시)
  - PostgreSQL `to_tsvector('simple', '삼성전자 주가가 올랐다')` → `'삼성전자' '주가가' '올랐다'`. `@@ to_tsquery('simple','삼성')` = false.
  - MySQL 기본 FULLTEXT 파서에서 `AGAINST('삼성')` → 0건(최소 토큰 길이 3).
  - MySQL ngram 자연어 모드 `AGAINST('삼성전자')` → '성전 이야기'까지 매칭.
- **원인**: 공백 단위 분석기는 어절 안을 못 본다. 최소 토큰 길이가 두 글자 단어를 버린다. n-gram 자연어 모드는 조각들의 OR다.
- **대처**: ngram 파서의 불리언 모드(구 검색)를 쓰거나, 형태소 분석기가 있는 검색 엔진을 쓴다. 색인 분석기와 검색 분석기를 같게 맞춘다(46번).

### 3. BRIN을 걸었는데 빨라지지 않음

- **현상**: 인덱스는 24 kB로 작은데 조회가 순차 스캔과 같다.
- **보이는 형태**: `Heap Blocks: lossy=`가 테이블 페이지 수에 가깝다. 또는 플래너가 아예 `Seq Scan`을 고른다. `pg_stats.correlation`이 0에 가깝다(로컬 재현 0.004).
- **원인**: 값이 물리 위치와 상관이 없다. 무작위 적재, 대량 UPDATE로 행이 다른 페이지로 옮겨졌거나, 과거 시각 데이터를 뒤늦게 넣었다.
- **대처**: 상관이 없는 컬럼이면 B-tree를 쓴다. 상관을 되살리려면 `CLUSTER`로 재정렬할 수 있지만 테이블 락이 걸린다. 시간 기준 파티셔닝이 더 안정적이다(33번).

### 4. GIN 인덱스 → 쓰기 급감·검색 지연 튐

- **현상**: 전문 검색 인덱스를 붙인 뒤 게시글 저장이 느려졌다. 가끔 저장 한 건이 유독 오래 걸리고, 검색도 들쭉날쭉하다.
- **보이는 형태**: 같은 10만 행 적재가 75 ms → 2982 ms(로컬 재현, 예시). `pgstatginindex`의 `pending_pages`가 크다.
- **원인**: 행 하나가 키 수십 개를 만든다. `fastupdate`의 대기 목록이 커지면 검색이 대기 목록까지 훑고, 한도를 넘긴 쓰기가 정리를 떠맡는다(64.4.4.1).
- **대처**: autovacuum이 테이블을 자주 처리하게 한다. 응답 시간 일관성이 더 중요하면 `fastupdate = off`로 끄거나, 백그라운드에서 `gin_clean_pending_list()`를 부른다. 대량 적재는 인덱스를 지우고 적재 후 다시 만든다(64.4.5 "Create vs. insert").

### 5. 블룸 필터의 거짓 양성 → 불필요한 I/O

- **현상**: 없는 키 조회인데 디스크 읽기가 생긴다(LSM 엔진). PostgreSQL bloom 인덱스 조회가 결과 0행인데 힙을 읽는다.
- **보이는 형태**: 로컬 재현에서 `Rows Removed by Index Recheck: 3`, 결과 0행. LSM에서는 블록 캐시 미스·읽기 증폭.
- **원인**: 비트 수가 적거나(키당 비트), 해시 함수 수가 맞지 않는다. 거짓 양성은 설계상 0이 될 수 없다.
- **대처**: 키당 비트를 늘린다(RocksDB 기준 약 10비트에 1%). 메모리와 맞바꾼다. PostgreSQL bloom은 `length`와 컬럼별 비트 수(`colN`)를 조정한다(F.6).

## 핵심 문장

- B+Tree는 값 전체의 정렬로 찾는다. 부분 문자열·단어·2차원·거대한 시간 범위에는 다른 자료구조가 필요하다.
- 블룸 필터는 "확실히 없음"과 "아마 있음"만 답한다. 없는 것을 건너뛰는 데 쓰고, "있음"은 반드시 재확인한다.
- 역색인은 키 → 행 목록이다. 무엇을 키로 뽑느냐(분석기)가 검색 결과를 정한다. 쓰기마다 키가 여럿 생겨 갱신이 비싸다.
- R-tree는 경계 사각형으로 묶어 겹치지 않는 가지를 건너뛴다. PostgreSQL은 GiST, MySQL은 SPATIAL INDEX로 쓴다.
- BRIN은 블록 범위마다 요약값만 둔다(기본 minmax는 최솟값·최댓값). 아주 작지만 minmax BRIN은 값과 물리 순서가 상관있을 때만 쓸모 있다.
- `LIKE '%x%'` 검색은 B+Tree로 해결되지 않는다. 트라이그램·n-gram 역색인이나 검색 엔진을 쓴다.

## 관련 주제·근거

- 선행: [08-btree-indexes](../08-btree-indexes/2-summary.md)
- 연결
  - [46-full-text-search-and-analyzers](../46-full-text-search-and-analyzers/2-summary.md) · [47-autocomplete-and-typeahead](../47-autocomplete-and-typeahead/2-summary.md) · [38-lsm-storage-engine](../38-lsm-storage-engine/2-summary.md)(SST 블룸 필터) · [37-row-vs-column-storage](../37-row-vs-column-storage/2-summary.md)(존 맵) · [33-partitioning-and-sharding](../33-partitioning-and-sharding/2-summary.md)
  - [09-index-design](../09-index-design/2-summary.md) — B+Tree 인덱스 설계
  - [39-hash-indexes](../39-hash-indexes/2-summary.md) — 등호 전용 인덱스
  - [11-join-algorithms](../11-join-algorithms/2-summary.md) — 해시 조인의 블룸 필터
  - [data-structure/11-bloom-filter](../../data-structure/11-bloom-filter/2-summary.md) · [data-structure/32-inverted-index](../../data-structure/32-inverted-index/2-summary.md) · [data-structure/25-spatial-index](../../data-structure/25-spatial-index/2-summary.md)
  - SQL 문법 노트: [sql/38 패턴 매칭](../../../languages/sql/syntax/38-pattern-matching-like-regex/2-summary.md)
- 강의·문서
  - CMU 15-445 Fall 2024 L9 "Indexes II"(블룸 필터·카운팅 블룸·쿠쿠 필터, 역색인, Lucene FST, PostgreSQL GIN) <https://15445.courses.cs.cmu.edu/fall2024/notes/09-indexes2.pdf>
  - PostgreSQL 17: 11.2 Index Types(접두어 `LIKE`) · 11.10 Operator Classes(`text_pattern_ops`) · 12.9 Preferred Index Types for Text Search · 64.2 GiST · 64.3 SP-GiST · 64.4 GIN(64.4.4.1 대기 목록·`fastupdate`, 64.4.5 `gin_pending_list_limit`·Create vs. insert) · 64.5 BRIN(`pages_per_range`, 요약, `autosummarize`) · F.6 bloom · F.33 pg_trgm · F.31 pgstattuple <https://www.postgresql.org/docs/17/gin.html> · <https://www.postgresql.org/docs/17/brin.html> · <https://www.postgresql.org/docs/17/bloom.html> · <https://www.postgresql.org/docs/17/pgtrgm.html>
  - MySQL 8.4: 14.9.6 Fine-Tuning MySQL Full-Text Search(`innodb_ft_min_token_size`) · 14.9.8 ngram Full-Text Parser(모드별 변환) · 17.6.2.4 InnoDB Full-Text Indexes · 13.4.10 Creating Spatial Indexes(R-tree) · 13.4.11 Using Spatial Indexes · 10.3.3 SPATIAL Index Optimization(SRID 조건) <https://dev.mysql.com/doc/refman/8.4/en/fulltext-search-ngram.html> · <https://dev.mysql.com/doc/refman/8.4/en/spatial-index-optimization.html>
  - RocksDB wiki "RocksDB Bloom Filter"(키당 비트 수와 거짓 양성률 표) <https://github.com/facebook/rocksdb/wiki/RocksDB-Bloom-Filter>
- 로컬 재현(PostgreSQL 17.11, MySQL 8.4.10): `LIKE '%x%'` 풀스캔 vs pg_trgm GIN, 한국어 `to_tsvector('simple')`·pg_trgm, GIN 적재 비용과 대기 목록, BRIN 시간순 vs 섞인 테이블, bloom 확장 크기·거짓 양성, GiST 사각형·KNN, MySQL FULLTEXT 기본 파서 vs ngram(불리언·자연어 모드)
