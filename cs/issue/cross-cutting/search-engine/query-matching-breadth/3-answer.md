# cs/issue/search-engine/query-matching-breadth — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 출처 원문 대조. 복습 전 읽지 말 것.

태그: —

## 정답
<!-- 질문 1:1 대응 -->

1. **`match` = 분석된 토큰의 OR.**\
`match`는 검색어를 필드 분석기로 토큰화한 뒤 기본 연산자 **OR**로 결합한다.\
"○○ 서비스 센터"가 `○○`·`서비스`·`센터`로 쪼개지면, `서비스`나 `센터` 하나만 있어도 매칭되어 거의 전체 문서가 나왔다(짧은 두 단어 질의도 마찬가지).\
이 절이 `should` + `minimum_should_match: 1`로 keyword wildcard(0건)와 묶여 있었기 때문에, "wildcard가 못 찾은 걸 match가 찾아준다"처럼 보였고 **넓은 매칭이 그대로 결과**가 되어 문제가 가려졌다 — 결과가 "많다"는 것은 에러가 아니므로 아무도 경보를 받지 않는다.
   > **minimum_should_match** — should 절 중 최소 몇 개가 맞아야 문서가 매칭되는지. 1이면 하나만 맞아도 된다.

2. **`match_phrase` = 토큰 순서·인접 유지.**\
`match_phrase`는 모든 토큰이 **같은 순서로 붙어서** 나타나야 매칭한다 — 두 단어 질의의 결과가 거의 전체에서 수 자릿수 적은 규모로 줄었다.\
분석 후 토큰이 하나인 질의에서는 순서·인접 조건이 의미가 없어 `match`와 결과가 같다(실측으로 동일 건수 확인) — 그래서 다토큰 질의에서만 동작이 바뀌는 **안전한 변경**이다.\
단 "단일 단어 = 단일 토큰"은 분석기에 달렸다 — 형태소 분석기가 한 단어를 여러 형태소로 쪼개거나 n-gram 필드라면 한 단어 질의도 다토큰이 되어 phrase 조건이 걸리므로, 대상 필드의 `_analyze` 결과로 확인해야 한다.\
`operator: "and"`도 대안이지만(모든 토큰 포함, 순서 무관), 이름·구문처럼 순서가 의미인 경우는 phrase가 의도에 더 맞다.

3. **full-text 퍼지는 토큰마다, term-level 퍼지는 값 전체.**\
`match` + `fuzziness`는 검색어와 문서를 모두 토큰으로 쪼갠 뒤 **토큰마다** 편집거리 퍼지를 적용하고 OR로 합친다.\
그래서 문서의 긴 단어가 두 토큰으로 쪼개지면 그 **조각**에 오타 매칭이 걸리고, 공백으로 나뉜 다단어 배열에선 첫 음절 치환만으로 무관한 두 글자 단어들이 매칭되며, 복합어가 두 토큰으로 나뉘면 뒤쪽 흔한 토큰 하나(OR)로 수백 건 노이즈가 들어왔다.\
`fuzzy`는 term-level이라 분석기를 쓰지 않고 **값 전체**를 term 사전에서 편집거리로 찾는다 — 교정은 보조 쿼리를 `fuzzy`+`term`으로 바꿔 keyword/exact 서브필드에 걸고(다단어 후보는 길이 차이로 자동 차단), 형태소 match엔 `operator: "and"`를 준 것이다.\
반대로 **여러 토큰짜리 질의를 `fuzzy`에 통째로** 넣으면 질의 전체가 한 term이 되어 색인 토큰과 편집거리가 너무 멀어 매치 불가가 되고, 1음절 term 단독 fuzzy는 (fuzziness를 1 이상으로 명시하면 — `AUTO`는 2자 이하에 편집을 허용하지 않는다) 거리 1 안의 후보가 폭증해 광역(수천 건)이 된다 — 이 경우는 `match`(분석 후 토큰별 fuzzy)가 맞다.\
어느 쪽이든 "대체만 허용하는 fuzzy"는 엔진에 없어(`fuzzy_transpositions: false`로 전치만 끌 수 있고 삽입·삭제는 남는다), 본질적 해결은 색인 쪽 변형 보강이라는 결론이었다.

4. **letter ngram은 한글 음절도 자른다.**\
`token_chars: [letter, digit]`의 letter에는 한글 음절도 포함되어, 한글 단어가 2~10자 조각으로 분해된다 — 네 글자 단어 `가나다라`는 `가나`, `가나다`, `나다`, `나다라`, `다라`, ... 로 색인된다.\
음절 하나가 의미 단위에 가까운 문자체계에서는 두 글자 검색어가 **무관한 긴 단어의 부분문자열**과 대량으로 일치한다(외래어 표기 긴 단어 여럿이 같은 두 글자를 포함).\
교정: 해당 분기에서 ngram 호출을 빼고 **자모 시퀀스 1토큰 필드의 정확 match**(퍼지 없음)로 대체 → 문자 분해 시퀀스가 정확히 맞는 소수 후보만 남음; 이후 매핑도 "ngram은 정규화된 필드에만"으로 정리.

5. **위치 없는 자질 합집합 = 부분집합 조건이 거의 항상 참.**\
문서 배열이 여러 후보 변형의 자질을 합친 **집합**(토큰 후보 집합)이면, 위치마다 거의 모든 자질이 어딘가에 들어 있다.\
그래서 "검색어 자질이 모두 문서에 있다"(100% AND)는 조건이 거의 항상 참이 되어, 음절 수와 무관하게 **prefix 매칭처럼** 동작했다(짧은 질의에도 대량 매칭).\
자질이 "몇 번째 위치의 자질인지"라는 위치 정보를 잃었기 때문이다 — 자질 매칭이 의미를 가지려면 **단일 후보만** 색인하거나 **위치를 별도 차원**으로 분리해야 한다.\
실제 조치는 그 변경을 롤백하고 자질 필드를 제거한 뒤, 역할을 나눈 두 필드(다단어 정확매치용 곱집합 keyword / 단어 단위 합집합)를 새로 둔 것이다.

6. **phrase/slop은 단어 단위 position을 전제한다.**\
`match_phrase`의 `slop`은 "토큰 사이 position 차이가 N 이하"를 본다 — position이 **단어 순서**라는 전제다.\
n-gram 분석기는 한 단어를 겹치는 조각 다수로 쪼개 position이 단어 단위가 아니므로 "A와 B가 3단어 이내"라는 의미가 성립하지 않아 0건이 됐다(붙여 쓴 형태로는 수백 건).\
게다가 쿼리 빌더의 fallback 분기가 `span_near` 시도 **전에** 항상 먼저 실행돼 n-gram 필드로 떨어졌다.\
기록된 수정 방향은 단어 단위 분석 필드에 `span_near`를 쓰거나 fallback 판단을 span_near 가능 필드 우선으로 바꾸는 것이다(미적용).

7. **매칭 단위를 의도에 맞춘다.**\
음성 인코더는 짧은 입력일수록 **소수의 코드로 붕괴**해(예: 여러 토큰이 전부 `M` 하나로) 변별력을 잃고, 토큰 수가 많은 문서가 같은 코드의 TF 합으로 상위를 차지했다.

| 의도 | 넓어지는 선택 | 맞는 선택 |
|------|---------------|-----------|
| 다단어 이름·구문 | `match`(토큰 OR) | `match_phrase` / `operator: and` |
| 값 전체의 오타 허용 | `match` + fuzziness(토큰별) | `fuzzy` on keyword(값 단위) |
| 여러 토큰 질의의 토큰별 오타 | `fuzzy`에 통째로(매치 불가) | `match` + fuzziness |
| 짧은 한글 검색어의 과매칭 방지 | letter ngram(음절 조각 부분일치) | 자모 1토큰 정확 match(부분일치 포기) / ngram은 정규화 필드에만 |
| 위치가 의미인 자질 매칭 | 후보 자질 합집합 배열 | 단일 후보 or 위치 차원 분리 |
| 인접 검색 | n-gram 필드 phrase+slop | 단어 단위 필드 span_near |
| 발음 유사 | 거친 음성 인코더 단독 | fuzziness 명시 + 색인 시점 변형 생성 |

## 문제 구조 (추상화 코드)

### 변형 A — 토큰 OR이 넓은 절을 만들고 should가 그것을 숨김
① 문제 코드
```python
q = bool_(should=[
    match("name", "OO 서비스 센터"),                   # OO OR 서비스 OR 센터 → 거의 전체
    wildcard("name.keyword", "*OO 서비스 센터*"),       # 0건
], minimum_should_match=1)                             # 넓은 쪽이 그대로 결과
```
② 고친 코드
```python
q = bool_(should=[
    match_phrase("name", "OO 서비스 센터", boost=10.0),   # 순서·인접 유지 (단일어는 결과 동일)
    wildcard("name.keyword", "*OO 서비스 센터*"),
], minimum_should_match=1)
```
무엇이 깨졌나: full-text match의 기본 OR을 이름 검색에 그대로 썼고, 결과 과다는 에러가 아니라 보이지 않았다.

### 변형 B — 퍼지의 적용 단위가 의도와 다름
① 문제 코드
```python
q.should(match("name", user_query, fuzziness="AUTO"))       # 문서 긴 단어가 두 토큰 → 조각에 오타 매칭
q.should(match("name_local", local_query))                  # 복합어 두 토큰 → 흔한 뒤 토큰 OR 노이즈
q.should(fuzzy("name_tokens", "토큰1 토큰2 토큰3"))          # 다토큰을 한 term으로 → 매치 불가
```
② 고친 코드
```python
q.should(fuzzy("name.exact", user_query.lower(), fuzziness="AUTO", boost=1.5))   # 값 전체 단위
q.should(match("name_local", local_query, operator="and", boost=3.0))
q.should(match("name_tokens", multi_token_query, fuzziness="AUTO"))                # 토큰별 퍼지
```
무엇이 깨졌나: full-text와 term-level의 비교 단위 차이(토큰 vs 값 전체)를 의도와 반대로 골랐다.

### 변형 C — letter ngram이 음절 문자체계를 조각냄
① 문제 코드
```json
"tokenizer": { "ng": { "type": "ngram", "min_gram": 2, "max_gram": 10, "token_chars": ["letter", "digit"] } }   // 차이 8 → index.max_ngram_diff 상향 필요
// "가나다라" → ["가나","가나다","가나다라","나다","나다라","다라"] → 검색어 "다라"와 일치
```
② 고친 코드
```python
q.should(match("name.jamo", to_jamo_sequence(query)))    # 자모 시퀀스 1토큰 정확 매칭, 퍼지 없음
# 매핑: ngram은 정규화된 _norm 필드에만
```
무엇이 깨졌나: 공백 문자체계를 전제한 부분문자열 색인을 음절 문자체계에 그대로 적용했다.

### 변형 D — 위치 정보 없는 자질 합집합
① 문제 코드
```python
doc["features"] = sorted(set(f for cand in token_candidates for f in encode(cand)))   # 합집합
q.must(*[term("features", f) for f in encode_seq(query)])       # 검색어 자질 전부 AND
# → 부분집합 조건이 거의 항상 참 → prefix처럼 수천 건
```
② 고친 코드
```python
# 변경 롤백 + 자질 필드 제거, 역할 분리 필드
doc["variants_exact"] = cartesian_product(tokens)          # 다단어 정확매치용 keyword
doc["variants_flat"]  = merge_candidates(tokens)           # 토큰별 후보의 순서 보존 dedup 합집합 (곱 아닌 합)
```
무엇이 깨졌나: 집합으로 합치면서 "어느 위치의 자질인가"라는 정보를 버렸다.

### 변형 E — n-gram 필드 위의 phrase/slop
① 문제 코드
```python
fallback = get_fallback_field(field)                      # → ngram 분석 필드
if fallback:
    return match_phrase(fallback, "A B", slop=distance)    # position이 단어 단위 아님 → 0건
return span_near(...)                                     # 도달하지 못함
```
② 고친 코드 (기록된 방향, 미적용)
```python
if supports_span(field):                                  # 단어 단위 분석 필드 우선
    return span_near([span_term(field, "a"), span_term(field, "b")], slop=distance, in_order=False)
return match_phrase(fallback, "A B", slop=distance)
```
무엇이 깨졌나: 위치 기반 쿼리를 위치 의미가 다른 필드에 걸었고, 분기 순서가 올바른 경로를 가렸다.\
같은 구조: 음성 인코더가 짧은 입력을 소수 코드로 붕괴시켜 반복 토큰 문서가 상위 → 인코더 단독 의존 대신 fuzziness 명시(`2`, `max_expansions≥500`)와 색인 시점 변형 생성.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log
