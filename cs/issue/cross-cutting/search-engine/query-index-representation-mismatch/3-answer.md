# cs/issue/search-engine/query-index-representation-mismatch — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 출처 원문 대조. 복습 전 읽지 말 것.

태그: `silent-failure`

## 정답
<!-- 질문 1:1 대응 -->

1. **`term`은 검색어를 분석하지 않는다.**\
`match`는 검색어를 필드의 (search) 분석기에 태워 토큰으로 만든 뒤 비교하고, `term`은 입력에 analyzer를 적용하지 않고 역색인 **토큰**과 비교한다(keyword 필드에 normalizer가 있으면 그 normalizer는 term류에도 적용된다).\
색인 시 lowercase 분석기를 거쳐 `acme`로 저장된 토큰은 `term("ACME")`과 같지 않다 — 0건, 에러 없음.\
주의: text 필드에서 term이 맞는다는 건 "토큰 하나가 같다"는 뜻이지 원문 전체 일치가 아니다. 이 사례의 필드는 원문 전체를 한 토큰으로 만드는 분석기(공백·구분자 제거 + 소문자화)라서 토큰 일치 = 전체 일치였다.\
완전일치 의도를 지키는 가장 작은 변경은 `term`을 유지하고 **입력에 색인측과 같은 변환(`.lower()`)**을 적용하는 것이다(1줄).\
`match`는 검색어를 분석해 나온 토큰들을 (기본 OR로) 매칭하므로, 필드 분석기가 여러 토큰을 만든다면 일부 토큰 일치로도 걸린다 — 이 필드처럼 단일 토큰 분석기면 결과는 거의 같지만, 의도를 코드에 드러내려고 term + 변환 재현을 택했다.\
같은 원리로, 분석기가 문자를 정렬해 저장하는 서브필드에는 그 변환(공백 제거 → 문자 정렬)을 코드에서 **재현**해 term에 넘기고, 재현이 어려운 서브필드는 term 절을 빼고 match만 남겼다.
   > **term-level 쿼리** — `term`·`terms`·`prefix`·`wildcard`·`fuzzy`처럼 검색어에 analyzer를 적용하지 않고 저장된 토큰과 직접 비교하는 쿼리. 단, keyword 필드의 normalizer는 적용된다.

2. **`search_analyzer`가 없으면 검색어도 n-gram으로 쪼개진다.**\
접미 edge n-gram 분석기(reverse → edge n-gram(min_gram 1) → reverse — 일반 edge n-gram은 접두 토큰을 만들고, reverse로 감싸야 접미 토큰이 된다)를 색인 전용으로 설계했어도, `search_analyzer`를 지정하지 않으면 **같은 분석기가 검색어에도** 적용된다.\
5글자 검색어는 접미 토큰들(`마`, `라마`, `다라마`, ...)로 쪼개진다.\
"짧은 토큰 `마`가 희귀해서 IDF가 최대"라는 설명은 **틀리다** — 같은 필드에서 `라마`로 끝나는 문서는 모두 `마` 토큰도 가지므로 df(`마`) ≥ df(`라마`)이고, `마`의 IDF는 오히려 접미 토큰 중 가장 낮은 편이다.\
문제의 본질은 **매칭 범위**다: 검색어 토큰들이 (기본 OR로) 매칭되므로 `마`로 끝나기만 하면 무관한 문서도 후보에 들어오고, 짧은 필드의 길이 정규화 등이 겹치면 그런 문서가 상위에 오를 수 있다 — 실제로 의미가 무관한 "…마"로 끝나는 문서가 상위에 올라왔다. 어느 요인이 순위를 만들었는지는 `_explain`·`_termvectors`(토큰 통계)로 확인해야 한다.\
교정: 매핑에 `search_analyzer`를 지정하는 안도 있었다(`search_analyzer`는 기존 필드에도 매핑 업데이트로 바꿀 수 있고, 새 분석기를 정의해야 하면 인덱스를 닫고 settings를 바꿔야 한다 — 재색인까지는 필요 없다). 당시엔 매핑·설정 변경을 피하고 쿼리를 `terms`로 바꿔 분석기 파이프라인을 코드에서 재현해 **토큰을 직접 만들되 1글자 토큰을 제외**했다 — 너무 넓은 1글자 매칭이 사라지고, terms는 (ES 구현상) 상수 점수라 토큰 통계에 따른 점수 편차도 없어진다.\
같은 원인이 도메인 변환 분석기에서도 났다: 색인용 음차(transliteration) 분석기가 쿼리에도 걸려 이미 변환된 입력이 재변환 → 쓰레기 토큰. 원칙: **도메인 분석기 필드엔 `search_analyzer`를 명시**한다.
   > **IDF (inverse document frequency)** — 토큰이 적은 문서에만 있을수록 커지는 가중치. 희귀 토큰 하나의 매칭이 점수를 크게 올린다. 접미/접두 n-gram 필드에서는 짧은 토큰일수록 더 많은 문서에 나타나므로 IDF가 낮다.

3. **keyword는 정규형 합의가 전부다.**\
normalizer 없는 keyword의 term/terms/prefix는 바이트 비교라 `"9"`와 `"09"`는 다른 값이다 → 필터 0건.\
같은 유형: 쿼리 쪽이 구분자를 추가(`A-01` vs 저장 `A01`), 접두 문자를 붙임(`X123` vs `123`), 정수를 보냄(`9` vs 0 채움 저장값 `"09"` — keyword 필드는 숫자를 문자열 `"9"`로 바꿔 비교한다).\
쓰기 경로가 `"01"`과 `"001"`을 섞어 저장하면 **같은 값이 두 버킷으로 쪼개진다** — 값별 건수가 틀어질 뿐, 문서당 값이 하나라면 버킷 합 자체는 보존된다.\
버킷 합이 전체 문서 수와 어긋나는 원인은 따로 있다: 필드가 없는 문서(missing은 집계에서 빠짐), 다중값 필드(한 문서가 여러 버킷에 셈), terms 집계의 상위 N(`size`) 제한 — 한 사례에서 합이 크게 어긋났을 때도 빈 필드 문서의 제외와 포맷 중복 버킷이 겹쳐 있었는데, 합 불일치를 설명하는 쪽은 앞의 것이고 중복 버킷은 값별 건수를 틀리게 하는 별개 문제다.\
임시 해결은 읽기 쪽을 인덱스 형식에 맞추는 것(고정 자릿수 0 채움을 모든 입력 검증 경로에 동일 적용)이다. 저장 형식과 입력 자릿수가 다를 때 terms 대신 prefix를 쓰는 것은 정규화가 아니라 **검색 범위를 넓히는 의미 변경**이므로, 코드가 계층형(상위 코드가 하위 코드의 접두사)이라는 업무 계약이 있을 때만 택한다.\
**근본은 쓰기 경로(색인 파이프라인)에서 정규형으로 통일**하는 것이다.\
두 데이터 원천이 다른 표기를 쓰면 필터에 모든 변형을 보내야 하고, 필터를 합칠 땐 교집합/override 의미를 명시해야 한다 — 범주 유래 필터와 사용자 지정 필터를 합집합하면 사용자 필터가 **넓어지는** 의미 파괴가 생겼다.

4. **normalizer 없는 keyword는 대소문자를 보존한다.**\
keyword는 normalizer가 없으면 원문 대소문자 그대로 한 토큰으로 저장되고, wildcard·terms는 analyzer를 거치지 않는다(normalizer가 있으면 질의에도 적용되지만, 이 필드엔 없다).\
클라이언트가 `.lower()`한 값만 보내면 대문자 원본과 영원히 만나지 못한다.\
대칭 원칙: 색인측에 소문자화가 **없으면** 질의측에도 없어야 하고, 질의측에서 소문자화하고 싶으면 색인측에 lowercase normalizer를 둬야 한다.\
해결 선택지: `.lower()` 제거(여러 경로에서 안전망 역할이라 회귀 위험), 대/소/원본 3변형 전송(절 3배, 혼합 대소문자는 여전히 누락), normalizer 추가(가장 깨끗하지만 기존 필드에 추가할 수 없어 새 필드 + 재색인), **분석되는 base 필드를 대상에 추가**(standard가 lowercase 적용, 2줄 변경 — 단 base 필드는 토큰 단위 매칭이라 keyword 전체값 매칭과 의미가 다르다) — 영향 범위가 좁은 마지막 안을 택했고, 다른 경로들은 `.lower()` 제거로 맞췄다.

5. **없는 필드 — 검색 절은 0점·에러 없음, 정렬은 다르다.**\
엔진(ES 기준)은 매핑에 없는 필드에 대한 term/match/wildcard 같은 **검색 절을 오류가 아니라 "매칭 없음"**으로 처리한다. 반면 **정렬**은 기본적으로 매핑 없는 필드에 대해 오류를 내고, `unmapped_type`을 지정해야 조용히 무시된다(여러 인덱스 중 일부에만 필드가 있는 경우 등 조건에 따라 다름).\
이미 keyword인 필드에 `.keyword`를 붙이면 0건이 된다 — `.keyword`는 동적 매핑이 문자열에 기본으로 붙이는 multi-field 이름일 뿐 특별한 규칙이 아니므로, 존재 여부는 **실제 매핑**으로 판단해야 한다. 옛 필드명으로 정렬했는데 오류 없이 무동작이었다면 `unmapped_type` 등 조용해지는 조건이 있었는지 확인한다. `multi_match`의 fields에 없는 필드가 섞이면 조용히 skip된다.\
인덱스 버전마다 필드 적재 여부가 달라 같은 코드가 버전에 따라 0건이 되기도 했고, 설계한 커스텀 서브필드가 **실제 인덱스에는 하나도 없어**(필드가 `text → [keyword]`뿐) 기존 쿼리가 에러 없이 돌며 적중률만 낮았던 사례도 있다.\
쿼리 빌더만 보면 "절이 있다", 매핑만 보면 "필드가 있다/없다"만 보이므로, **둘을 대조**해야 dead 절이 드러난다 — 교훈: 코드 작성 전 `GET _mapping/field/<name>` 확인, 수정마다 카운트 질의로 실측(`term(field, v)` 다수 vs `term(field.keyword, v)` 0건), 인덱스 매핑 vs 코드 필드 매핑 전수 대조.\
"매핑이 없으면 검색 절은 0점"을 이용해 **쿼리를 매핑보다 먼저 배포**할 수도 있지만, 이는 검색 절에 한정된다 — 정렬(오류)·그 필드에 기대는 필터(0건으로 결과가 사라짐)가 섞여 있으면 안전하지 않으므로 절 종류별로 확인한다.

6. **`index: false`와 nested.**\
`index: false`는 역색인을 만들지 않는다 — 무엇이 남는지는 타입에 따라 다르다. text 필드는 검색 수단이 없어 질의하면 오류가 나고 `_source`로 표시만 된다. keyword·숫자·날짜 같은 타입은 doc values가 켜져 있으면 (최근 ES 버전에서) 느린 검색과 정렬·집계가 가능하다(일반론 — 버전·타입마다 지원 쿼리가 다르다).\
검색이 필요하면 해결은 매핑 변경 + 재색인, 또는 색인 파이프라인에서 검색용 필드에 따로 적재하는 것이다.\
nested 원소는 **별도 숨은 문서**로 색인되므로 루트 문서 레벨의 일반 쿼리·정렬로는 값이 보이지 않는다 — `nested` 쿼리(`path` 지정)로 감싸고, 정렬엔 `"nested": {"path": ...}`를 준다.\
검색용 최상위 플래그 필드가 따로 있으면 nested 대신 그것을 쓰는 편이 단순하다.

7. **dead 필드와 로컬 등가 복제.**\
질의측은 `"foo bar"`를 `foobar` 한 덩어리로 만들어 term 질의하는데, 인덱스는 standard로 `foo`·`bar`를 나눈 뒤 **단어별** n-gram만 저장했으므로 `foobar` 토큰은 존재하지 않는다 — **공백을 포함한 검색어 경로**에서 그 필드는 매칭되지 않고 저장 비용만 남는다(같은 정규화로 만든 `_norm` 필드의 n-gram만 매칭).\
필드 전체가 dead인 것은 아니다: 단일 단어 검색어(`"foo"`)는 max_gram 이하 길이라면 단어별 n-gram과 그대로 맞는다. 반대로 max_gram보다 긴 단일 단어 term은 어떤 n-gram과도 맞지 않으므로, max_gram을 줄이면 긴 검색어의 미매칭이 늘어난다 — 길이 경계를 반례로 검증해야 한다.\
게다가 `token_chars: [letter, digit]`의 letter에 한글이 포함돼 한글도 n-gram으로 잘려 짧은 검색어가 무관한 긴 단어에 걸리는 노이즈가 생겼다.\
교정은 "n-gram은 이미 정규화된 `_norm` 필드에만"이라는 단일 원칙으로 **매핑과 쿼리 필드 목록을 함께** 정리하는 것이었다(한쪽만 정리하면 조용히 품질 저하, 서브필드 제거는 재색인 때까지 반영 불가).\
로컬 등가 구현(다른 방안)은 토큰화 규칙(standard가 하이픈·슬래시·`&`는 나누고 `letter'letter`는 한 토큰으로 유지)과 **배열 원소 경계**(원소 사이에 `position_increment_gap`(text 기본 100)만큼 위치 간격이 들어가 slop이 작은 phrase는 원소를 넘지 못한다 — slop이 간격 이상이면 넘을 수 있다)까지 복제해야 한다.\
그래도 표본 대조로 말할 수 있는 건 전체 등가가 아니라 **계약(지원 분석기·slop 0·동의어 없음·위치 간격·키워드 최소 길이 등)으로 고정한 범위 안의 경험적 일치**다.

## 문제 구조 (추상화 코드)

### 변형 A — 비분석 쿼리 vs 분석된 필드
① 문제 코드
```python
name = raw.replace(" ", "").replace("-", "").replace("_", "")
q.should(term("name_exact", name))             # "ACME" vs 저장 "acme"
```
② 고친 코드
```python
name = raw.replace(" ", "").replace("-", "").replace("_", "").lower()   # 색인측 변환 재현
q.should(term("name_exact", name))
# 문자 정렬 서브필드: sorted_chars(name) 재현 후 term / 재현 어려운 서브필드는 term 절 제거
```
무엇이 깨졌나: term이 검색어를 분석하지 않는다는 걸 잊고 색인측 변환을 쿼리 쪽에서 재현하지 않았다.

### 변형 B — `search_analyzer` 미지정
① 문제 코드
```json
"name.suffix": { "type": "text", "analyzer": "suffix_edge" }  // search_analyzer 없음
```
```python
q.should(match("name.suffix", query))     # 검색어도 접미 n-gram → 1글자 토큰 → 매칭 범위 폭증
```
② 고친 코드
```python
tokens = back_ngrams(query, min_len=2)            # 분석기 파이프라인을 코드로 재현, 1글자 제외
q.should(terms("name.suffix", tokens))            # 분석기 우회 + 상수 점수
# 대안: 매핑에 "search_analyzer" 지정 (기존 필드도 매핑 업데이트로 가능)
```
무엇이 깨졌나: 색인용 분석기가 검색어에도 걸린다는 기본 동작을 놓쳤다 — 색인측과 "같은" 파이프라인이 아니라 "호환되는" 토큰 표현이 필요했다.\
같은 구조: 색인용 음차 분석기 필드(`"analyzer": "translit_x"`, search_analyzer 없음)에 이미 변환된 쿼리가 재통과 → 변환을 색인 전 ETL 단계로 옮겨 keyword 필드에 저장, 또는 변환기에 passthrough 가드.

### 변형 C — keyword 정규형 불일치
① 문제 코드
```python
codes = [str(int(c)) for c in raw_codes]                 # "09" → "9", 인덱스는 "09"
q.filter(terms("cat_codes", [9]))                        # 정수 전송, 인덱스는 0 채움 문자열
q.filter(terms("code_a", [add_dash(c)]))                 # "A-01", 인덱스는 구분자 없는 형식
```
② 고친 코드
```python
codes = [str(int(c)).zfill(WIDTH) for c in raw_codes]    # 저장 정규형(고정 폭 0 채움)을 모든 입력 검증 경로에 동일 적용
q.filter(terms("cat_codes", [str(int(c)).zfill(WIDTH) for c in raw]))
q.filter(term("code_a", strip_dash(c)))                  # 저장 형식(구분자 없음)에 맞춤
# prefix("code_a", ...) 는 정규화가 아니라 범위 확장 — 계층 코드 계약이 있을 때만
q.filter(term("id_no", to_stored_form(raw)))             # 저장 정규형으로 변환(접두 문자·선행 0 규칙은 계약으로)
# 근본: 색인 파이프라인에서 정규형으로 통일 (읽기 쪽 정규화는 임시)
```
무엇이 깨졌나: 쓰기 경로와 읽기 경로가 서로 다른 정규형을 적용했다.\
같은 구조: 한 필드의 값이 `"01"`/`"001"`로 섞여 저장 → 값별 버킷 분열 → 집계 후처리에서 정규형으로 바꿔 동일 값 합산·범위 밖 제거(버킷 합과 전체 문서 수의 차이는 missing·다중값·size 제한으로 따로 설명).\
같은 구조: 두 원천이 `"3"`/`"03"` 표기 → 필터에 두 형태 모두 전송, 사용자 지정 필터는 범주 유래 필터와 합집합하지 않고 override.

### 변형 D — keyword 대소문자 비대칭
① 문제 코드
```python
{"wildcard": {field: value.lower()}}              # keyword, normalizer 없음, 원본은 대문자
```
② 고친 코드
```python
{"wildcard": {field: value}}                      # 색인측에 소문자화가 없으면 질의측도 없음
# 또는 대상 필드에 분석되는 base 필드 추가 (standard → lowercase 토큰)
FIELDS = ["part_a.exact", "part_b.exact", "part_a", "part_b"]   # base 필드는 토큰 단위 매칭 (의미 차이 인지)
```
무엇이 깨졌나: 질의측에서만 정규화해 색인측과 대칭이 깨졌다.

### 변형 E — 존재하지 않는 필드 · index:false · nested
① 문제 코드
```python
q.should(term("codes.keyword", code))              # codes는 이미 keyword → .keyword 없음 → 0건
sort = {"name.keyword": "asc"}                     # 없는 서브필드 → 기본은 오류 (unmapped_type 지정 시 무동작)
q.should(match("name.cross_sub", v))               # 설계엔 있고 매핑엔 없음 → 0점
q.filter(range("children.date", gte=d))           # nested → 루트 레벨에서 안 닿음
q.should(match("holder.name", v))                  # text + index:false → 검색 불가 (질의 오류)
```
② 고친 코드
```python
q.should(term("codes", code))                      # GET _mapping/field/codes 로 확인 후
sort = {"name": "asc"}                             # name이 keyword(doc values)인 경우 — text 필드 정렬은 기본 불가
# dead 절 제거 (매핑 쪽 변경과 쿼리 쪽 정리를 짝지어)
q.filter(nested(path="children", query=range("children.date", gte=d)))
sort = {"children.name": {"order": "asc", "nested": {"path": "children"}}}
# index:false → 매핑 변경 + 재색인 또는 검색용 필드 별도 적재
```
무엇이 깨졌나: 코드의 필드명을 실제 인덱스 매핑과 대조하지 않았고, 엔진은 그 불일치를 알려주지 않았다.

### 변형 F — 질의 정규화 ≠ 색인 토큰화 (dead n-gram 필드)
① 문제 코드
```python
norm_q = "".join(c for c in q.lower() if c.isalnum())        # "foo bar" → "foobar"
q.should(term("name.ngram", norm_q))                         # 인덱스: ["fo","foo","ba","bar"] 단어별 → 공백 포함 질의는 항상 0 (단일 단어는 매칭)
```
```json
"ngram_tok": { "type": "ngram", "min_gram": 2, "max_gram": 30, "token_chars": ["letter", "digit"] }   // 한글도 letter
```
② 고친 코드
```python
q.should(term("name_norm.ngram", norm_q))                    # 같은 정규화로 만든 필드에만 n-gram
# 매핑: base text 필드의 n-gram 서브필드 제거 + 쿼리 필드 목록 동반 정리 (재색인 시 반영)
# max_gram 30 → 10 (max_ngram_diff 명시) — 10자 초과 단일 term은 더 이상 매칭 안 됨: 길이 경계 반례로 검증
```
무엇이 깨졌나: 질의측과 색인측이 서로 다른 표현을 만들어, 그 질의 경로에서는 필드가 저장 비용만 남았다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log

## 방안 비교

기본 방안(위 변형 A~F)은 "엔진 안에서 질의측과 색인측 변환을 대칭으로 맞추고 매핑과 대조한다"이다. 같은 원리(매칭은 양쪽 표현이 같을 때만 성립)에 다른 방안이 쓰인 사례:

### 방안 1 — 엔진 밖 로컬 등가 구현 (의미론까지 복제 + 엔진과 표본 대조)
```python
# 문제: 대량 문서 × 수만 키워드 전수 판정 → 엔진 절 한도·비용 때문에 불가
#      로컬 근사에서 배열을 이어 붙이면 원소 경계를 걸친 가짜 phrase,
#      부분문자열 매칭이면 "phone"이 "telephones"에 걸림
automaton = build_aho_corasick(" " + norm(kw) + " " for kw in keywords if len(kw) >= 3)   # 앞뒤 공백 = 단어 경계
def matches(doc):
    for element in doc.descs:                        # 원소 단위로 매칭 (position gap + slop 0 phrase 가정 모사)
        blob = " " + norm(element) + " "             # norm = 엔진 standard 토큰화 근사 (letter'letter 유지 차이만 남음 → 표본 대조로 규명)
        if any(True for _ in automaton.iter(blob)):
            return True                              # 원소 OR → 문서 판정
    return False
# 등가 검증: 실제 엔진 ids 필터 + bool.should 로 표본 대조, _analyze golden 케이스,
#           약점을 노린 표적 표본(아포스트로피 포함 문서) 추가
```

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 기본: 엔진 안에서 변환 대칭 + 매핑 대조 | 질의가 엔진 한도 안에 들어간다 | 쿼리·매핑 수정, 경우에 따라 재색인 | 한쪽만 고치면 조용히 0건·dead 필드 | 온라인 검색·필터 |
| 1. 로컬 등가 구현 | 토큰화·경계 의미론(분석기·slop·동의어·위치 간격)을 계약으로 고정하고 복제할 수 있다 | 복제 구현 + 엔진 대조 검증 | 의미론 차이가 희귀 케이스에서만 드러남(무작위 표본으로는 놓침) | 대량 일괄 판정(배치), 엔진 한도 밖 규모 |

**결론**: 온라인 질의라면 엔진 안에서 양쪽 변환을 대칭으로 맞추는 것이 기본이다 — 표현을 하나의 엔진이 결정하므로 등가성 문제가 없다.\
엔진 한도 밖 규모의 일괄 판정은 로컬 구현이 현실적이지만, 그때 "대칭"의 상대가 엔진의 **토큰화 규칙과 배열 경계 의미론 전체**로 넓어진다 — 표본 대조(불일치율 측정)와 약점 표적 표본이 있어도 주장할 수 있는 건 고정한 계약 범위 안의 경험적 일치이지 전체 등가는 아니다.\
엔진 쪽 정공법(퍼콜레이터 등)은 규모 때문에 보류된 대안이었다.
