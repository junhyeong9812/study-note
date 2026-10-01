# database/47-autocomplete-and-typeahead — 자동완성: 접두사 색인, 인기도 순위, 한글 자모 — 정리 (힌트)

## 해결하는 문제

검색창에 "삼"을 치는 순간 "삼성전자", "삼겹살 맛집"이 떠야 한다.

```text
  사용자 입력    ㅅ → 사 → 삼 → 삼ㅅ → 삼서 → 삼성
  요청           1    2    3     4      5      6        ← 키 입력마다 요청
  기대 응답 시간  사람이 다음 글자를 치기 전 (수십~100ms 수준, 예시)
```

전문 검색([46](../46-full-text-search-and-analyzers/2-summary.md))과 다른 점이 셋이다.

1. 질의가 **단어의 앞부분**이다. "삼"은 완성된 용어가 아니다.
2. 요청이 **키 입력 수만큼** 온다. 한 사람이 검색어 하나에 요청 여러 개를 보낸다.
3. 결과는 관련도보다 **인기도 상위 k개**가 중요하다.

쉬운 예: 휴대폰 연락처 검색이다. "김"을 누르면 김씨 목록이 뜨고, 자주 연락한 사람이 위에 온다. 초성 "ㄱㅁㅅ"만 쳐도 "김민수"가 나온다.

똑같은 구조다. 접두사로 후보를 좁히고(트라이), 점수로 상위 k개를 고르고(힙), 한글은 자모로 풀어 비교한다.

실무 예: 쇼핑몰 검색창, 주소 입력, 태그 입력, 사내 사람 찾기.

## 동작·원리

### 1. 접두사 질의는 정렬된 사전의 구간이다

```text
  정렬된 용어      삼겹살 ... 삼성 ... 삼성가격 ... 삼성전자 ... 삼섲(여기부터 벗어남) ... 삼양
                             ├──────── '삼성%' 구간 ─────────┤
  B-tree 조건:  term >= '삼성'  AND  term < '삼섲'   (마지막 글자 +1)
```

로컬 재현(예시, PostgreSQL 17.11, 검색어 20만 행, 로케일 en_US.utf8):

```text
  CREATE INDEX suggest_prefix ON suggest (term text_pattern_ops);

  WHERE term LIKE '삼성%'  → Bitmap Index Scan on suggest_prefix
                             Index Cond: ((term ~>=~ '삼성') AND (term ~<~ '삼섲'))
                             (actual rows=20000) → Sort: top-N heapsort → 10행

  WHERE term LIKE '삼%'    → Parallel Seq Scan (actual rows=30000 loops=2, Rows Removed by Filter: 70000)
                             → 리더·워커 합쳐 60000행 통과 → top-N heapsort
```

- `text_pattern_ops`: 로케일 정렬 규칙 대신 **글자 단위**로 비교하는 B-tree 연산자 클래스다(PostgreSQL 17 11.10). C가 아닌 로케일에서 `LIKE '접두사%'`에 인덱스를 쓰려면 필요하다.
- 문제 1: 한 글자 접두사는 후보가 너무 많다("삼%" = 30%). planner가 순차 스캔을 고른다.
- 문제 2: 후보를 다 모은 뒤 인기도로 정렬한다. 후보가 2만 개면 2만 개를 읽고 10개를 고른다.
- 그래서 자동완성은 **"접두사별 상위 k개"를 미리 만들어 두는** 쪽으로 간다(아래 3·4).

### 2. edge n-gram — 색인 때 접두사를 전부 만든다

```text
  색인:  "삼성전자"  ──edge_ngram(min 1, max 10)──>  [삼] [삼성] [삼성전] [삼성전자]
  검색:  "삼성"      ──standard (자르지 않음)──────>  [삼성]              → 정확 일치로 찾는다
```

- *edge n-gram*: 단어 **앞에서부터** 길이 min~max의 조각을 만든다. 일반 n-gram은 모든 위치에서 자른다.
- 검색어는 자르지 않는다. 그래서 `search_analyzer`를 따로 둔다(ES 문서가 이 용도를 예로 든다).
- ES `edge_ngram` 기본값은 `min_gram` 1, `max_gram` 2다. 문서는 "기본 길이는 거의 쓸모없다"며 설정하고 쓰라고 한다.
- `max_gram`보다 긴 검색어는 맞지 않는다. `max_gram` = 3이면 "apple"은 색인된 "app"과 맞지 않는다. `truncate` 필터로 검색어를 자르면 "apply"까지 섞인다(ES 문서).
- 비용: 색인 용어 수가 단어 길이만큼 늘어난다.

### 3. search_as_you_type — ES가 묶어 둔 필드

```text
  my_field                 원래 분석기
  my_field._2gram          2단어 shingle   "quick brown", "brown fox"
  my_field._3gram          3단어 shingle
  my_field._index_prefix   _3gram에 edge n-gram을 씌운 것
```

- 한 필드를 선언하면 위 하위 필드를 자동으로 만든다. 접두사 완성과 중간 단어 완성(infix)을 모두 지원한다.
- 문서가 권하는 질의: `multi_match` + `type: bool_prefix`로 루트와 shingle 하위 필드를 함께 찾는다. 마지막 단어만 접두사로 본다.
- `max_shingle_size` 기본 3, 2~4.

### 4. completion suggester — 메모리의 가중 FST

```text
  입력(분석된 형태) → 출력(weight, 표시 문자열, 문서 ID)

        ┌─삼─┬─성─┬─전─자─ (w=90) 삼성전자
  (시작)┤    │    └─(끝)── (w=70) 삼성
        │    └─겹─살──── (w=40) 삼겹살
        └─서─울───────── (w=80) 서울

  "삼" 입력 → '삼' 노드로 내려가 그 아래 경로 중 weight 상위 k개를 찾는다(Top-N 탐색)
```

- *FST(finite state transducer)*: 접두사와 접미사를 함께 공유하는 트라이의 압축형이다. 경로마다 출력(여기서는 가중치 등)을 붙인다. Lucene `FST.java`는 "compact byte[] 형식의 유한 상태 기계"라고 적는다.
- Lucene `NRTSuggester` 주석: 가중 FST 위에서 Top N 검색을 한다. 입력은 분석된 용어, 출력은 (weight, 표시 형태, docID)다.
  - 삭제가 많거나 필터가 강하면 후보 경로를 지나치게 쳐내 검색이 "inadmissible"해질 수 있다고 경고한다.
- ES 문서: "빠른 조회용 자료구조를 쓰지만 만들기 비싸고 메모리에 둔다". near real-time이라 refresh 뒤 보이고, 삭제된 문서는 보이지 않는다.
- `weight`는 문서를 색인할 때 넣는 양의 정수다. 인기도를 바꾸려면 **문서를 다시 색인**해야 한다.
- `max_input_length` 기본 50(문서 표현 "50 UTF-16 code points"). 긴 입력은 색인 때 잘린다.

### 5. 한글 — 음절은 초성·중성·종성의 산술 조합이다

```text
  완성형 음절 U+AC00(가) ~ U+D7A3(힣) : 19 × 21 × 28 = 11172개

  SIndex = 코드포인트 − 0xAC00
  초성 = SIndex ÷ 588          (588 = 21 × 28)
  중성 = (SIndex mod 588) ÷ 28
  종성 = SIndex mod 28         (0이면 받침 없음)

  예) '삼' = U+C0BC = 49340 → SIndex 5308
      초성 5308 ÷ 588 = 9  → ㅅ   (ㄱㄲㄴㄷㄸㄹㅁㅂㅃ[ㅅ]...)
      중성 (5308 mod 588) ÷ 28 = 16 ÷ 28 = 0 → ㅏ
      종성 5308 mod 28 = 16 → ㅁ
```

- 근거: Unicode Standard 16.0 3.12 "Conjoining Jamo Behavior"(SBase = AC00, LCount 19, VCount 21, TCount 28, NCount 588, SCount 11172).
- 표준의 분해 결과는 **조합형 자모**(U+1100대)다. 키보드로 친 "ㅅ"은 **호환 자모**(U+3131대, 예: ㅅ = U+3145)다. 둘은 다른 코드포인트라 그대로 비교하면 맞지 않는다. 한쪽으로 맞춰 비교한다.

**입력 중인 글자의 문제**

```text
  사용자가 "삼성"을 치는 동안 IME가 보내는 값
     ㅅ → 사 → 삼 → 삼ㅅ → 삼서 → 삼성
                      └ 마지막 글자가 아직 음절이 아니다
  음절 단위 접두사 '삼ㅅ%' → 어떤 용어와도 맞지 않는다
  자모 단위 접두사 'ㅅㅏㅁㅅ%' → 'ㅅㅏㅁㅅㅓㅇ'(삼성)과 맞는다
```

로컬 재현(예시, PostgreSQL 17.11): 호환 자모로 푸는 SQL 함수 `jamo()`를 만들어 저장 열 + `text_pattern_ops` 인덱스를 걸었다.

```text
  jamo('삼성') = ㅅㅏㅁㅅㅓㅇ     jamo('삼ㅅ') = ㅅㅏㅁㅅ     jamo('과') = ㄱㅗㅏ     jamo('닭') = ㄷㅏㄹㄱ
  term LIKE '삼ㅅ%'           → 0행
  jm   LIKE 'ㅅㅏㅁㅅ%'        → 20000행 (삼성…), Index Cond: jm ~>=~ 'ㅅㅏㅁㅅ' AND jm ~<~ 'ㅅㅏㅁㅆ'
  chosung('삼성전자') = ㅅㅅㅈㅈ   cho LIKE 'ㅅㅅㅈ%' → 삼성전자 …
```

- 겹모음(ㅘ → ㅗㅏ)과 겹받침(ㄺ → ㄹㄱ)도 풀어야 한다. "고"까지 친 상태는 "과"의 앞부분이고, "달ㄱ"까지 친 상태는 "닭"의 앞부분이기 때문이다.
- 초성 검색은 짧으면 선택도가 나쁘다. 재현 표본에서는 모든 검색어가 ㅅ으로 시작해 `cho LIKE 'ㅅ%'`가 20만 행 전부였다.

### 6. 클라이언트 쪽 — 요청 수와 순서

```text
  키 입력:  삼 ─10ms─ 삼ㅅ ─10ms─ 삼서 ─10ms─ 삼성 ─── 300ms 멈춤
  디바운스 없이:  요청 4개
  디바운스 150ms: 마지막 입력 뒤 150ms 조용하면 요청 1개

  응답 순서 역전:
    요청 A("삼")  ─────────────────────────> 응답 A (느림, 200ms)
    요청 B("삼성") ──────> 응답 B (빠름, 50ms)
    화면: B를 그림 → 늦게 온 A가 B를 덮어씀 → "삼성"을 쳤는데 "삼" 결과가 보인다
```

- *디바운스(debounce)*: 입력이 멈춘 뒤 일정 시간이 지나야 요청을 보낸다.
- 응답 순서는 보장되지 않는다. 요청마다 경로·서버·캐시 적중이 다르다.
- 대처: 새 요청을 보낼 때 이전 요청을 취소하고(`AbortController`), 응답에 담긴 질의가 현재 입력과 같을 때만 그린다.

## 쓰이는 자료구조·알고리즘

- **트라이·FST** — 접두사 공유. FST는 접미사까지 공유하고 경로에 출력을 단다. [data-structure/09-trie](../../data-structure/09-trie/2-summary.md), [data-structure/20-radix-trie](../../data-structure/20-radix-trie/2-summary.md)
- **정렬된 B-tree의 구간 스캔** — `LIKE '접두사%'` → `[접두사, 접두사의 다음 값)`. [08-btree-indexes](../08-btree-indexes/2-summary.md)
- **top-k** — 크기 k 힙으로 후보를 한 번 훑는다. PostgreSQL 계획의 `top-N heapsort`가 이것이다. [data-structure/07-heap](../../data-structure/07-heap/2-summary.md)
- **Top-N 경로 탐색** — 가중 FST에서 최대 가중치 경로를 우선순위 큐로 뽑는다(Lucene `NRTSuggester`).
- **한글 음절 산술 분해** — 나눗셈·나머지 세 번으로 초·중·종성을 얻는다.
- **edge n-gram** — 접두사를 색인 시점에 펼쳐 정확 일치 조회로 바꾼다. 공간을 시간과 바꾼다.

## 적용 — 풀어나가는 법

### 1. 규모별 선택

```text
  검색어 수만~수십만, DB만 있다
    → 인기 검색어 테이블 + 접두사 B-tree(text_pattern_ops) + 자모 열
    → 한두 글자 접두사는 "접두사 → 상위 k" 사전 테이블(미리 계산)
  상품·문서 수백만, 검색 엔진이 있다
    → completion suggester(가장 빠름, weight 갱신 = 재색인)
    → 또는 search_as_you_type / edge n-gram(중간 단어 완성·필터 결합이 쉬움)
```

### 2. PostgreSQL — 접두사별 상위 k를 미리 만든다

```sql
-- 인기 검색어 원천
CREATE TABLE suggest (term text PRIMARY KEY, popularity int NOT NULL,
                      jm text GENERATED ALWAYS AS (jamo(term)) STORED);
CREATE INDEX suggest_jm ON suggest (jm text_pattern_ops);

-- 짧은 접두사(자모 1~4개)는 미리 계산 (배치로 주기 갱신)
CREATE TABLE suggest_top (prefix text, rank int, term text, PRIMARY KEY (prefix, rank));
INSERT INTO suggest_top
SELECT p, rn, term FROM (
  SELECT left(jm, n) AS p, term,
         row_number() OVER (PARTITION BY left(jm, n) ORDER BY popularity DESC) AS rn
  FROM suggest, generate_series(1, 4) AS n
  WHERE n <= length(jm)          -- 자모가 3개뿐인 '삼'이 n=3·4에서 두 번 들어가지 않게
) x WHERE rn <= 10;

-- 조회: 짧으면 사전, 길면 인덱스 구간 + top-N
SELECT term FROM suggest_top WHERE prefix = jamo($1) ORDER BY rank;         -- 자모 4개 이하
SELECT term FROM suggest WHERE jm LIKE jamo($1) || '%'
ORDER BY popularity DESC LIMIT 10;                                             -- 더 길 때
```

- `jamo()`는 로컬 재현에서 쓴 SQL 함수다(음절을 호환 자모로 펴고 겹모음·겹받침도 편다). `IMMUTABLE`로 선언해야 저장 열·인덱스에 쓸 수 있다.
- 사용자 입력 `$1`에 `%`·`_`가 있으면 LIKE 와일드카드가 된다. `\`·`%`·`_` 앞에 `\`를 붙여 이스케이프한 뒤 붙인다(PostgreSQL `LIKE`의 기본 이스케이프 문자는 `\`라 `\` 자체도 두 번 쓴다. 입력 끝의 `\`가 뒤의 `%`를 글자로 바꾸는 것을 막는다).
- 구간 스캔은 계획 시점에 패턴 앞부분을 알 때만 된다. 준비된 문장이 일반 계획(generic plan)으로 바뀌면 `$1`을 몰라 `Seq Scan`이 된다(로컬 재현, 예시, PostgreSQL 17.11: `plan_cache_mode = force_custom_plan`은 `Index Cond: (jm ~>=~ 'k123' AND jm ~<~ 'k124')`, `force_generic_plan`은 `Seq Scan`). `EXPLAIN EXECUTE`로 확인하고, 필요하면 `plan_cache_mode = force_custom_plan`을 쓰거나 앱이 구간 상·하한을 계산해 `jm >= $lo AND jm < $hi`로 보낸다.

### 3. Elasticsearch — completion 필드

```json
PUT products
{ "mappings": { "properties": {
    "suggest": { "type": "completion", "analyzer": "simple" } } } }

PUT products/_doc/1
{ "suggest": { "input": ["삼성전자 냉장고", "ㅅㅅㅈㅈ"], "weight": 90 } }

POST products/_search
{ "suggest": { "s": { "prefix": "삼성", "completion": { "field": "suggest", "size": 10 } } } }
```

- 초성·자모 입력을 받으려면 `input`에 변형을 함께 넣거나, 자모로 편 별도 필드를 둔다. 색인 쪽과 검색 쪽이 같은 변환을 거쳐야 한다([46](../46-full-text-search-and-analyzers/2-summary.md)의 분석기 일치 원칙).
- weight(인기도)를 매일 바꾸면 매일 그만큼 재색인한다. 변동이 큰 점수는 edge n-gram 필드 + `function_score`처럼 질의 시점에 섞는 편이 낫다 [?].

### 4. 브라우저 — 디바운스, 취소, 순서 확인

```ts
let timer: ReturnType<typeof setTimeout> | undefined;
let inflight: AbortController | undefined;

function onInput(q: string) {
  clearTimeout(timer);
  timer = setTimeout(() => void fetchSuggest(q), 150);    // 디바운스 (150ms는 예시)
}

async function fetchSuggest(q: string) {
  if (q.length === 0) return;
  inflight?.abort();                                       // 이전 요청 취소
  const ac = new AbortController();
  inflight = ac;
  try {
    const res = await fetch(`/suggest?q=${encodeURIComponent(q)}`, { signal: ac.signal });
    const body: { q: string; items: string[] } = await res.json();
    if (body.q !== currentInput()) return;                 // 늦게 온 옛 응답은 버린다
    render(body.items);
  } catch (e) {
    if ((e as Error).name !== "AbortError") throw e;       // 취소는 정상 흐름
  }
}
```

- 취소의 기본 효과는 브라우저가 응답을 기다리지 않는 것이다. 이미 서버에 도착한 요청은 서버에서 계속 처리될 수 있다.
  - 서버가 연결 종료를 감지해 작업을 멈추는 구성에서만 서버 부하도 준다(예: Elasticsearch는 클라이언트 HTTP 연결이 닫히면 검색을 자동 취소한다 — Elastic "The search API" 문서). 그래서 서버 부하는 디바운스·최소 길이·캐시로 먼저 줄인다.
- 조합 중(`compositionstart`~`compositionend`)에도 `input` 이벤트는 온다. 자모 분해로 서버가 "삼ㅅ"을 처리할 수 있으면 조합 중에도 요청해도 된다.

### 5. 캐시

- 접두사 응답은 사용자와 무관하면 공유 캐시에 둔다(`Cache-Control: public, max-age=60` 등, 값은 예시). 인기 접두사 몇 개가 요청 대부분을 차지하는 경우가 많아 적중률이 높다 [?].
- 개인화 추천을 섞으면 공유 캐시 키에 사용자 구분이 들어가야 한다. 빠뜨리면 남의 최근 검색어가 보인다.

## 장애 시나리오와 대처

### 1. 초성·입력 중 글자에 결과가 없다

- **현상**: "ㅅㅁ"이나 "삼ㅅ"을 치면 빈 목록이다. 한 글자를 더 쳐야 결과가 나온다.
- **보이는 형태**: 에러 없음. 재현: `term LIKE '삼ㅅ%'` → 0행.
- **원인**: 음절 단위로만 색인했다. 호환 자모 "ㅅ"은 어떤 음절의 접두사도 아니다.
- **대처**: 색인 쪽과 질의 쪽을 모두 자모로 편다(겹모음·겹받침 포함). 초성 열을 따로 둔다. 조합형(U+1100대)과 호환 자모(U+3131대)를 한쪽으로 맞춘다.

### 2. 키 입력마다 요청 → 검색 클러스터 QPS 폭증

- **현상**: 캠페인 시작 뒤 검색 클러스터 CPU가 치솟고 검색 결과 API까지 느려진다.
- **보이는 형태**: 자동완성 엔드포인트 요청 수가 검색 요청의 수 배. 접속 로그에 같은 세션이 한 글자씩 늘어나는 질의를 연달아 보낸다.
- **원인**: 디바운스·최소 길이·캐시가 없다. 한 글자 접두사가 후보 수만 개를 정렬한다.
- **대처**: 디바운스(예: 100~200ms), 최소 입력 길이, 접두사 응답 캐시, 짧은 접두사의 top-k 사전. 자동완성을 검색과 다른 인덱스·노드로 분리해 서로 번지지 않게 한다.

### 3. 늦게 온 이전 응답이 최신 결과를 덮는다

- **현상**: "삼성"까지 쳤는데 목록은 "삼" 결과다. 가끔만 난다.
- **보이는 형태**: 네트워크 탭에서 "삼" 요청이 "삼성" 요청보다 늦게 끝난다.
- **원인**: 응답 도착 순서는 요청 순서를 따르지 않는다. 클라이언트가 도착 순서대로 그린다.
- **대처**: 이전 요청 `abort()` + 응답의 질의 문자열(또는 요청 번호)이 현재 입력과 같을 때만 그린다.

### 4. `max_gram`보다 긴 검색어가 0건

- **현상**: 짧게 치면 나오는데 상품명을 끝까지 치면 사라진다.
- **보이는 형태**: ES `_analyze`로 보면 색인 토큰이 `max_gram` 길이에서 끊긴다.
- **원인**: edge n-gram 색인 분석기의 `max_gram`이 짧다. 검색어는 자르지 않으므로 더 긴 검색어와 맞는 색인 용어가 없다.
- **대처**: `max_gram`을 늘린다(색인 커짐). 또는 원문 필드에 대한 일반 match를 `should`로 함께 건다. `truncate`는 무관한 결과를 섞으니 시험 뒤 쓴다. 분석기 변경이므로 재색인한다.

### 5. 인기도가 반영되지 않는다

- **현상**: 급상승 검색어가 하루 지나도 자동완성에 안 뜬다.
- **원인**: completion의 `weight`는 색인 시점 값이다. 인기도 집계 배치만 돌고 재색인은 주 1회다.
- **대처**: 인기도 변화가 큰 목록은 질의 시점 점수로 섞는다. 또는 상위 변동분만 부분 재색인한다. 집계·재색인 지연을 지표로 둔다.

## 핵심 문장

- 접두사 질의는 정렬된 사전의 한 구간이다. B-tree(`text_pattern_ops`)·트라이·FST가 모두 이 성질을 쓴다.
- 짧은 접두사는 후보가 너무 많으므로, 접두사별 상위 k개를 미리 만들어 두는 것이 자동완성의 핵심 설계다.
- edge n-gram은 접두사를 색인 때 펼치는 방법이라 검색어는 자르지 않는 별도 `search_analyzer`가 필요하다.
- 한글 음절은 `0xAC00 + (초성×21 + 중성)×28 + 종성`이다. 입력 중인 "삼ㅅ"을 맞추려면 색인과 질의를 모두 자모로 풀어 비교한다.
- 키 입력마다 오는 요청은 디바운스·최소 길이·캐시로 줄이고, 순서 역전은 취소와 질의 일치 확인으로 막는다.

## 관련 주제·근거

버전 기준: PostgreSQL 17(로컬 17.11), Elasticsearch 현행 문서(2026-10 확인), Apache Lucene `main` 소스, The Unicode Standard 16.0 3.12절. Elasticsearch 서버는 로컬에 없다.

- 선행
  - [46-full-text-search-and-analyzers](../46-full-text-search-and-analyzers/2-summary.md) — 분석기, 색인·검색 분석기 일치
  - [data-structure/09-trie](../../data-structure/09-trie/2-summary.md) — 접두사 트리
- 연결
  - web-platform `05-fetch-from-browser`(fetch 중단) — 미작성, [web-platform/README](../../web-platform/README.md)
  - [data-structure/07-heap](../../data-structure/07-heap/2-summary.md) — top-k
  - [10-collation-and-text-comparison](../10-collation-and-text-comparison/2-summary.md) — 로케일 정렬과 패턴 연산자 클래스
- PostgreSQL 17 문서 11.10 Operator Classes and Operator Families(`text_pattern_ops`) <https://www.postgresql.org/docs/17/indexes-opclass.html>
- PostgreSQL 17 문서 9.7.1 `LIKE`(기본 이스케이프 문자 `\`) <https://www.postgresql.org/docs/17/functions-matching.html> · `PREPARE`(일반 계획·맞춤 계획, `plan_cache_mode`) <https://www.postgresql.org/docs/17/sql-prepare.html>
- Elasticsearch 문서
  - Edge n-gram tokenizer(기본 min 1·max 2, `max_gram` 한계) <https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-edgengram-tokenizer.html>
  - `search_analyzer`(edge n-gram 자동완성 예) · Search-as-you-type field type(`_2gram`·`_3gram`·`_index_prefix`, `bool_prefix`)
  - The search API — Search cancellation("automatically cancels a search request when your client's HTTP connection closes") <https://www.elastic.co/docs/solutions/search/the-search-api>
  - Completion field type(`max_input_length` 50) · Suggesters — completion suggester("costly to build and are stored in-memory", near real-time)
- Apache Lucene `main`
  - `lucene/core/src/java/org/apache/lucene/util/fst/FST.java`
  - `lucene/suggest/src/java/org/apache/lucene/search/suggest/document/NRTSuggester.java` — 가중 FST Top N, 출력 (weight, surface form, docID)
- The Unicode Standard, Version 16.0, 3.12 Conjoining Jamo Behavior — Hangul Syllable Decomposition(SBase·LCount·VCount·TCount·NCount·SCount) <https://www.unicode.org/versions/Unicode16.0.0/core-spec/chapter-3/>
- 로컬 재현(PostgreSQL 17.11): 검색어 20만 행의 접두사 LIKE 실행 계획(인덱스 전후, 한 글자 접두사), 초성 함수·자모 함수와 `삼ㅅ` 질의, 자모 열 인덱스 구간 조건, 준비된 문장의 맞춤/일반 계획별 접두사 LIKE 계획
