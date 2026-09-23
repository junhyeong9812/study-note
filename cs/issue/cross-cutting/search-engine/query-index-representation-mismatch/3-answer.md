# cs/issue/search-engine/query-index-representation-mismatch — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 출처 원문 대조. 복습 전 읽지 말 것.

태그: `silent-failure`

## 정답
<!-- 질문 1:1 대응 -->

1. **`term`은 검색어를 분석하지 않는다.**\
`match`는 검색어를 필드의 (search) 분석기에 태워 토큰으로 만든 뒤 비교하고, `term`은 입력을 **그대로** 역색인 토큰과 비교한다.\
색인 시 lowercase 분석기를 거쳐 `acme`로 저장된 토큰은 `term("ACME")`과 절대 같지 않다 — 0건, 에러 없음.\
완전일치 의도를 지키는 가장 작은 변경은 `term`을 유지하고 **입력에 색인측과 같은 변환(`.lower()`)**을 적용하는 것이다(1줄).\
`match`로 바꾸면 부분 매치가 되어 완전일치 의도가 훼손되므로 선택하지 않았다.\
같은 원리로, 분석기가 문자를 정렬해 저장하는 서브필드에는 그 변환(공백 제거 → 문자 정렬)을 코드에서 **재현**해 term에 넘기고, 재현이 어려운 서브필드는 term 절을 빼고 match만 남겼다.
   > **term-level 쿼리** — `term`·`terms`·`prefix`·`wildcard`·`fuzzy`처럼 검색어를 분석하지 않고 저장된 토큰과 직접 비교하는 쿼리.

2. **`search_analyzer`가 없으면 검색어도 n-gram으로 쪼개진다.**\
edge n-gram 분석기(뒤에서부터: reverse → edge n-gram → reverse)를 색인 전용으로 설계했어도, `search_analyzer`를 지정하지 않으면 **같은 분석기가 검색어에도** 적용된다.\
5글자 검색어는 뒤쪽 접미 토큰들(`마`, `라마`, `다라마`, ...)로 쪼개지고, 1글자 토큰 `마`는 그 필드에서 **희귀**하면(수백만 문서 중 수백 건) IDF가 최대치 근처라 BM25 점수를 지배한다 — 발음이 무관한 "…마"로 끝나는 문서가 상위 수십 위에 올라왔다.\
교정: 매핑에 `search_analyzer`를 추가하는 안은 인덱스 재생성이 필요해 운영 위험이 커서, 쿼리를 `terms`로 바꾸고 분석기 파이프라인을 코드에서 재현해 **토큰을 직접 만들되 1글자 토큰을 제외**했다 — terms는 분석기를 거치지 않고 필터처럼 상수 점수라 IDF 폭등이 원천 차단된다.\
같은 원인이 도메인 변환 분석기에서도 났다: 색인용 발음 변환 분석기가 쿼리에도 걸려 이미 변환된 입력이 재변환 → 쓰레기 토큰. 원칙: **도메인 분석기 필드엔 `search_analyzer`를 명시**한다.
   > **IDF (inverse document frequency)** — 토큰이 적은 문서에만 있을수록 커지는 가중치. 희귀 토큰 하나의 매칭이 점수를 크게 올린다.

3. **keyword는 정규형 합의가 전부다.**\
keyword의 term/terms/prefix는 바이트 비교라 `"9"`와 `"09"`는 다른 값이다 → 필터 0건.\
같은 유형: 쿼리 쪽이 구분자를 추가(`02.09.25` vs 저장 `020925`), 접두사를 붙임(`W0123` vs `123`), 정수를 보냄(`9` vs `"009"`).\
쓰기 경로가 `"01"`과 `"001"`을 섞어 저장하면 **같은 값이 두 버킷으로 쪼개져** 집계 합이 어긋난다(한 사례에서 전체 문서 수와 집계 합이 약 140만 건 어긋났는데, 필드가 빈 문서의 집계 제외와 포맷 중복 버킷이 겹친 결과였다).\
임시 해결은 읽기 쪽을 인덱스 형식에 맞추는 것(`str(int(c)).zfill(2)`를 모든 validator에 동일 적용, 점 제거 + 자릿수가 다른 코드는 terms 대신 prefix)이지만, **근본은 쓰기 경로(색인 파이프라인)에서 정규형으로 통일**하는 것이다.\
두 데이터 원천이 다른 표기를 쓰면 필터에 모든 변형을 보내야 하고, 필터를 합칠 땐 교집합/override 의미를 명시해야 한다 — 범주 유래 필터와 사용자 지정 필터를 합집합하면 사용자 필터가 **넓어지는** 의미 파괴가 생겼다.

4. **normalizer 없는 keyword는 대소문자를 보존한다.**\
keyword는 normalizer가 없으면 원문 대소문자 그대로 한 토큰으로 저장되고, wildcard·terms는 분석기·normalizer를 거치지 않는다.\
클라이언트가 `.lower()`한 값만 보내면 대문자 원본과 영원히 만나지 못한다.\
대칭 원칙: 색인측에 소문자화가 **없으면** 질의측에도 없어야 하고, 질의측에서 소문자화하고 싶으면 색인측에 lowercase normalizer를 둬야 한다.\
해결 선택지: `.lower()` 제거(여러 경로에서 안전망 역할이라 회귀 위험), 대/소/원본 3변형 전송(절 3배), normalizer 추가(가장 깨끗하지만 재색인), **분석되는 base 필드를 대상에 추가**(standard가 lowercase 적용, 2줄 변경) — 영향 범위가 좁은 마지막 안을 택했고, 다른 경로들은 `.lower()` 제거로 맞췄다.

5. **없는 필드 = 0점, 에러 없음.**\
엔진은 매핑에 없는 필드에 대한 term/match/wildcard/sort를 **오류가 아니라 "매칭 없음"**으로 처리한다.\
이미 keyword인 필드에 `.keyword`를 붙이면(`.keyword`는 text 필드의 multi-field로 정의됐을 때만 존재) 0건, 옛 필드명으로 정렬하면 무동작, `multi_match`의 fields에 없는 필드가 섞이면 조용히 skip된다.\
인덱스 버전마다 필드 적재 여부가 달라 같은 코드가 버전에 따라 0건이 되기도 했고, 설계한 커스텀 서브필드가 **실제 인덱스에는 하나도 없어**(필드가 `text → [keyword]`뿐) 기존 쿼리가 에러 없이 돌며 적중률만 낮았던 사례도 있다.\
쿼리 빌더만 보면 "절이 있다", 매핑만 보면 "필드가 있다/없다"만 보이므로, **둘을 대조**해야 dead 절이 드러난다 — 교훈: 코드 작성 전 `GET _mapping/field/<name>` 확인, 수정마다 카운트 질의로 실측(`term(field, v)` 수십만 건 vs `term(field.keyword, v)` 0건), 인덱스 매핑 vs 코드 필드 매핑 전수 대조.\
역으로 "매핑이 없으면 0점"을 이용해 **쿼리를 매핑보다 먼저 배포**하는 것이 안전하다고 판단한 경우도 있다.

6. **`index: false`와 nested.**\
`index: false`는 역색인을 만들지 않아 `_source`로 **저장·표시만** 되고 어떤 쿼리로도 검색할 수 없다 — 해결은 매핑 변경 + 재색인, 또는 색인 파이프라인에서 검색용 필드에 따로 적재(기록상 미해결로 남음).\
nested 원소는 **별도 숨은 문서**로 색인되므로 루트 문서 레벨의 일반 쿼리·정렬로는 값이 보이지 않는다 — `nested` 쿼리(`path` 지정)로 감싸고, 정렬엔 `"nested": {"path": ...}`를 준다.\
검색용 최상위 플래그 필드가 따로 있으면 nested 대신 그것을 쓰는 편이 단순하다.

7. **dead 필드와 로컬 등가 복제.**\
질의측은 `"foo bar"`를 `foobar` 한 덩어리로 만들어 term 질의하는데, 인덱스는 standard로 `foo`·`bar`를 나눈 뒤 **단어별** n-gram만 저장했으므로 `foobar` 토큰은 존재하지 않는다 — 그 필드는 **어떤 쿼리와도 매칭되지 않고 디스크만 차지하는 dead 필드**가 된다(같은 정규화로 만든 `_clean` 필드의 n-gram만 매칭).\
게다가 `token_chars: [letter, digit]`의 letter에 한글이 포함돼 한글도 2~10gram으로 잘려 짧은 검색어가 무관한 긴 단어에 걸리는 노이즈가 생겼다.\
교정은 "n-gram은 이미 정규화된 `_clean` 필드에만"이라는 단일 원칙으로 **매핑과 쿼리 필드 목록을 함께** 정리하는 것이었다(한쪽만 정리하면 조용히 품질 저하, 서브필드 제거는 재색인 때까지 반영 불가).\
로컬 등가 구현(다른 방안)은 토큰화 규칙(standard가 하이픈·슬래시·`&`는 나누고 `letter'letter`는 한 토큰으로 유지)과 **배열 원소 경계**(phrase는 원소 사이를 넘지 않음)까지 복제하고, 실제 엔진 결과와 표본 대조해야 "등가"라고 말할 수 있다.

## 문제 구조 (추상화 코드)

### 변형 A — 비분석 쿼리 vs 분석된 필드
① 문제 코드
```python
name = raw.replace(" ", "").replace("-", "").replace("_", "")
q.add_should(term("name_exact", name))         # "ACME" vs 저장 "acme"
```
② 고친 코드
```python
name = raw.replace(" ", "").replace("-", "").replace("_", "").lower()   # 색인측 변환 재현
q.add_should(term("name_exact", name))
# 문자 정렬 서브필드: sorted_chars(name) 재현 후 term / 재현 어려운 서브필드는 term 절 제거
```
무엇이 깨졌나: term이 검색어를 분석하지 않는다는 걸 잊고 색인측 변환을 쿼리 쪽에서 재현하지 않았다.

### 변형 B — `search_analyzer` 미지정
① 문제 코드
```json
"name.back": { "type": "text", "analyzer": "edge_back" }     // search_analyzer 없음
```
```python
q.add_should(match("name.back", query))   # 검색어도 edge n-gram → 1글자 토큰 → IDF 폭등
```
② 고친 코드
```python
tokens = back_ngrams(query, min_len=2)            # 분석기 파이프라인을 코드로 재현, 1글자 제외
q.add_should(terms("name.back", tokens))          # 분석기 우회 + 상수 점수
```
무엇이 깨졌나: 색인용 분석기가 검색어에도 걸린다는 기본 동작을 놓쳤다.\
같은 구조: 색인용 발음 변환 분석기 필드(`"analyzer": "pron_x"`, search_analyzer 없음)에 이미 변환된 쿼리가 재통과 → 변환을 색인 전 ETL 단계로 옮겨 keyword 필드에 저장, 또는 변환기에 passthrough 가드.

### 변형 C — keyword 정규형 불일치
① 문제 코드
```python
codes = [str(int(c)) for c in raw_codes]                 # "09" → "9", 인덱스는 "09"
q.filter(terms("class_codes", [9]))                      # 정수 전송, 인덱스는 "009"
q.filter(terms("figure_codes", [add_dots(c)]))           # "02.09.25", 인덱스는 점 없는 8자리 숫자
```
② 고친 코드
```python
codes = [str(int(c)).zfill(2) for c in raw_codes]        # 모든 validator에 동일 적용
q.filter(terms("class_codes", [str(int(c)).zfill(3) for c in raw]))
q.filter(prefix("figure_codes", strip_dots(c)))          # 6자리 입력 → 8자리 저장값 prefix
q.filter(term("reg_no", raw.lstrip("Ww").lstrip("0")))   # 접두사·선행 0 제거
# 근본: 색인 파이프라인에서 정규형으로 통일 (읽기 쪽 정규화는 임시)
```
무엇이 깨졌나: 쓰기 경로와 읽기 경로가 서로 다른 정규형을 적용했다.\
같은 구조: 한 필드의 값이 `"01"`/`"001"`로 섞여 저장 → 집계 버킷 분열 → 집계 normalizer에서 2자리 정규화·동일 값 합산·범위 밖 제거.\
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
FIELDS = ["part_a.exact", "part_b.exact", "part_a", "part_b"]
```
무엇이 깨졌나: 질의측에서만 정규화해 색인측과 대칭이 깨졌다.

### 변형 E — 존재하지 않는 필드 · index:false · nested
① 문제 코드
```python
q.add_should(term("codes.keyword", code))          # codes는 이미 keyword → .keyword 없음 → 0건
sort = {"owner_name.keyword": "asc"}               # 없는 서브필드 → 무동작
q.add_should(match("name.cross_sub", v))           # 설계엔 있고 매핑엔 없음 → 0점
q.filter(range("children.date", gte=d))           # nested → 루트 레벨에서 안 닿음
q.add_should(match("holder.name", v))              # index:false → 검색 불가
```
② 고친 코드
```python
q.add_should(term("codes", code))                  # GET _mapping/field/codes 로 확인 후
sort = {"owner_name": "asc"}
# dead 절 제거 (매핑 쪽 변경과 쿼리 쪽 정리를 짝지어)
q.filter(nested(path="children", query=range("children.date", gte=d)))
sort = {"children.name": {"order": "asc", "nested": {"path": "children"}}}
# index:false → 매핑 변경 + 재색인 또는 검색용 필드 별도 적재
```
무엇이 깨졌나: 코드의 필드명을 실제 인덱스 매핑과 대조하지 않았고, 엔진은 그 불일치를 알려주지 않았다.

### 변형 F — 질의 정규화 ≠ 색인 토큰화 (dead n-gram 필드)
① 문제 코드
```python
name_clean = "".join(c for c in q.lower() if c.isalnum())    # "foo bar" → "foobar"
q.add_should(term("name.ngram", name_clean))                 # 인덱스: ["fo","foo","ba","bar"] 단어별 → 영원히 0
```
```json
"ngram_tok": { "type": "ngram", "min_gram": 2, "max_gram": 30, "token_chars": ["letter", "digit"] }   // 한글도 letter
```
② 고친 코드
```python
q.add_should(term("name_clean.ngram", name_clean))           # 같은 정규화로 만든 필드에만 n-gram
# 매핑: base text 필드의 n-gram 서브필드 제거 + 쿼리 필드 목록 동반 정리 (재색인 시 반영)
# max_gram 30 → 10 (max_ngram_diff 명시)
```
무엇이 깨졌나: 질의측과 색인측이 서로 다른 표현을 만들어, 그 필드는 저장 비용만 남았다.

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
    for element in doc.descs:                        # 원소 단위로 매칭 (엔진의 position gap 모사)
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
| 1. 로컬 등가 구현 | 토큰화·경계 의미론을 정확히 복제할 수 있다 | 복제 구현 + 엔진 대조 검증 | 의미론 차이가 희귀 케이스에서만 드러남(무작위 표본으로는 놓침) | 대량 일괄 판정(배치), 엔진 한도 밖 규모 |

**결론**: 온라인 질의라면 엔진 안에서 양쪽 변환을 대칭으로 맞추는 것이 기본이다 — 표현을 하나의 엔진이 결정하므로 등가성 문제가 없다.\
엔진 한도 밖 규모의 일괄 판정은 로컬 구현이 현실적이지만, 그때 "대칭"의 상대가 엔진의 **토큰화 규칙과 배열 경계 의미론 전체**로 넓어진다 — 표본 대조(불일치율 측정)와 약점 표적 표본 없이는 등가라고 말할 수 없다.\
엔진 쪽 정공법(퍼콜레이터 등)은 규모 때문에 보류된 대안으로 기록돼 있다.
