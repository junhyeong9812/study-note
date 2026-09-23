# cs/issue/search-engine/query-and-index-cost-limits — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 사건 기록 대조·추상화. 복습 전 읽지 말 것.

태그: `resource-bounding`

## 정답
<!-- 질문 1:1 대응 -->

1. **절 한도는 사양 기반 휴리스틱으로 기동 시 고정.**\
이 엔진 버전(8.x)은 bool 쿼리의 절 수 한도를 **노드 힙 크기와 검색 스레드 풀 크기**로 기동 시 자동 산정한다.\
옛 설정 키 `indices.query.bool.max_clause_count`는 등록은 되지만 효력이 없어, 60,000으로 올리고 재시작해도 한도는 그대로였다(8GB 힙 로컬에서 14,169).\
즉 단일 bool 쿼리로는 **노드 사양이 허용하는 것 이상의 절을 보장할 수 없다** — 설정이 아니라 쿼리 모양을 바꿔야 한다.
   > **maxClauseCount** — 한 쿼리가 확장·조합될 때 만들 수 있는 Lucene 절의 최대 수. 메모리 폭주를 막는 엔진 상한.

2. **OR + filter 컨텍스트면 청크 합집합 = 단일 쿼리.**\
그 절들은 `should`(minimum_should_match=1) OR이고 **filter 컨텍스트**라 점수에 기여하지 않았다.\
합집합은 결합적이므로 `A∪B∪C = (A∪B)∪C`이고, 점수가 이 절들에 의존하지 않으므로 청크별 동일 쿼리(나머지 조건 + 키워드 일부)의 **매칭 문서 집합**의 합집합이 단일 쿼리의 매칭 집합과 같다.\
반환 결과까지 같으려면 조건이 더 있다: 각 청크는 상위 `size`개만 돌려주므로 **청크마다 최종적으로 필요한 from+size개 이상**을 가져와야 병합 후 상위 K가 단일 쿼리와 일치하고, `total` 건수·집계는 청크 간 중복 때문에 단순 합산할 수 없다(별도 계산 필요).\
`_msearch` 1회로 청크를 보내고 `_id`로 dedupe한 뒤, 각 청크의 정렬 키와 **같은 키**(점수 → 식별자 → 보조 키)로 재정렬해 결정론적으로 병합한다.\
청크 하나라도 실패하면 **전체를 예외로** 실패시킨다 — 부분 결과를 돌려주면 "일부 키워드의 매칭이 조용히 빠진 결과"가 정상 응답으로 나가 리콜 손실이 숨는다.\
청크 수 폭주에는 별도 안전핀(총 키워드 상한 초과 시 명시 거부)을 둔다.\
근본 해법은 색인 시점에 문서에 범주 ID를 태깅해 쿼리를 terms 1절로 만드는 것으로 후속 과제에 남겼다.

3. **cartesian은 지수적이다.**\
토큰당 후보 k개, 토큰 n개면 변형은 kⁿ개 — 4⁶ = 4,096개다(실제로 한 건이 4,096 변형이 된 사례가 있다).\
이것을 다중값 필드에 넣고 여러 n-gram 서브필드로 분석하면 문서당 term 수가 입력 길이에 지수적으로 커져, 인덱스가 수배(한 사례 약 3배, 다른 사례는 cap 적용 후 수 분의 1로 줄어듦)로 불고 워커 메모리가 수십 MB에서 GB 단위로 튄다.\
**결과 개수에만 cap을 걸면 부족하다** — 곱집합을 만드는 과정에서 이미 메모리를 쓰므로, **곱하기 전에** 토큰당 후보 수를 줄여야(per-token cap, 첫 토큰 기준 층화 quota, 동적 축소) 폭발을 막는다.\
색인 비용도 같다: 모든 변형에 무거운 분석기를 돌리면 색인이 변형 수에 비례해 느려지므로(문서당 수십 ms), 원 필드는 keyword로 두고 **상위 몇 개 변형에만** 분석기 서브필드를 걸어 19배 빨라졌다.

4. **circuit breaker는 힙을 지킨다.**\
엔진은 힙의 일정 비율을 요청 메모리 상한으로 두고, 추정 사용량이 이를 넘으면 요청을 (대개 처리 전, 경우에 따라 처리 도중) `429 circuit_breaking_exception: Data too large`로 거절한다 — 노드 OOM을 막는 방어선이다(추정치 기반이라 완벽하지는 않다).\
분석기 서브필드를 늘리자 같은 배치의 색인 메모리가 커져 breaker 상한을 넘었다.\
세 레버: **힙 증가**는 상한 자체를 올리고, **배치 크기 축소**는 요청 하나의 부피를, **워커 수 축소**는 동시에 떠 있는 요청의 총량을 줄인다(기록에는 세 대응이 나열돼 있고, 최종적으로 메모리 조정 후 전체 이관 실패 0건 완료가 남아 있다).\
breaker가 없거나 넉넉하면 대신 힙 자체가 넘쳐 노드가 죽고(샤드 일시 RED, bulk 대량 취소), 색인은 대량 부분 실패로 끝난다.

5. **클라이언트 동시성 ≤ 서버 쓰기 큐.**\
bulk는 샤드 단위 작업으로 쪼개져 서버의 쓰기 스레드 풀 큐에 들어가며, **동시 in-flight 작업**이 스레드 수 + 큐 용량을 넘으면 초과분은 429(`es_rejected_execution_exception`)로 거부된다 — 최근 버전은 큐와 별개로 진행 중 색인 바이트가 한도(indexing pressure)를 넘어도 429로 거부하므로, 동시성과 배치 부피를 함께 봐야 한다.\
워커 12 × 배치 500은 0.67%가 거부됐고 워커 8은 0건이었다 — 워커·배치 기본값을 서버 큐에 맞췄다(더 빠르게 하려면 큐 크기를 늘리되 힙을 고려).\
힙을 32GB 아래로 잡는 것은 JVM의 **compressed oops 임계 미만**을 유지하기 위해서다 — 넘으면 객체 포인터가 커져 같은 힙에서 쓸 수 있는 공간이 오히려 줄어든다. 실제 임계는 JVM·OS에 따라 32GB보다 조금 낮을 수 있어(대략 30GB 안팎) 기동 로그의 compressed oops 사용 여부로 확인하고, 파일시스템 캐시 몫을 위해 물리 메모리의 절반 이하로 두는 것이 일반 권고다.\
부수: 엔진 컨테이너를 재생성한 뒤 앱의 커넥션 풀이 죽은 연결을 재사용해 작업이 즉시 실패했다 — 재생성 순서를 "엔진 → green 확인 → 앱"으로 고정했다.
   > **compressed oops** — 64비트 JVM이 힙 32GB 미만일 때 객체 참조를 32비트로 압축해 메모리를 아끼는 최적화.

6. **정확도를 깎는 상한, 비용을 옮기는 구조.**\
fuzzy는 편집거리 안의 후보 term을 모은 뒤 **가까운(거리 작은) 순으로 `max_expansions`개만** 남기고(같은 거리면 term 순서로) 나머지를 버린다.\
편집거리 안에 드는 후보 term이 많은 필드(term 수가 많은 필드, 음절 하나가 한 문자라 짧은 단어끼리 거리가 가까운 한글 등)에서는 정답이 남는 목록에 들지 못할 수 있다 — 200에선 0건, 500에선 3건이 잡혔고, 기본값 50은 늘 모자랐다.\
대응: 필드의 term 수를 줄이고(토큰 중 최장 1개만 담는 필드), `fuzziness=2 · prefix_length=1 · max_expansions=500`을 명시했다 — 한글은 fuzzy 대신 색인 시점에 변형 풀을 만드는 편이 본질적이라는 결론.\
wildcard(특히 앞쪽 `*`)는 용어 사전을 순회해 사실상 전체 term 스캔이 되어 평균 지연이 수십 배로 늘었고, **색인 시점**에 앞·뒤 edge n-gram을 만들어 쿼리를 단순 term 조회로 바꿨다 — 비용을 **쿼리 시점에서 색인 시점(저장 공간)으로** 옮긴 것이다.\
단 앞·뒤 edge n-gram은 **접두·접미 일치**만 대신한다 — `*x*`의 "중간 포함" 의미까지 유지하려면 일반 n-gram(또는 부분 일치 전용 필드 타입)이 필요하고, 그만큼 저장 비용이 더 든다. 이 교정은 요구를 접두·접미 일치로 좁힌 것이기도 하다.
   > **max_expansions** — fuzzy·prefix 쿼리가 만들 수 있는 확장 term의 최대 개수.

7. **두 경로의 상한.**\
쿼리 경로: 입력(키워드 수)에 비례해 절이 느는 쿼리는 **대수 구조를 확인한 뒤 분할**하고, 분할 결과는 전부 성공해야 반환하며, 청크 수에도 명시 상한을 둔다. 확장형 쿼리(fuzzy·wildcard)는 확장 폭을 명시하거나 색인 구조로 대체한다.\
색인 경로: 조합 생성은 **곱하기 전 인자**에 cap을 두고, 요청 부피(배치 × 변형 × 서브필드)와 동시성을 **서버 한도(breaker·큐·힙·타임아웃)**에 맞추며, 무거운 작업을 동시에 돌리지 않는다.\
상한은 "없으면 입력 분포 하나가 시스템을 멈추는" 최후 방어선이다 — 대신 그 상한이 조용히 결과를 잘라내지 않는지(부분 결과·확장 절단) 함께 본다.

## 문제 구조 (추상화 코드)

### 변형 A — 절 수 한도 → 대수적 동치 청크 합집합
① 문제 코드
```java
BoolQuery.Builder or = new BoolQuery.Builder();
int n = 0;
for (String kw : keywords) {
    if (n < MAX_CLAUSES) { or.should(matchPhrase(field, kw)); n++; }   // 초과분 무음 절단 (또는 400)
}
```
② 고친 코드
```java
if (keywords.size() <= chunkSize) return searchSingle(keywords);
if (keywords.size() > MAX_TOTAL_KEYWORDS) throw new TooManyKeywords();     // 폭주 안전핀 (명시 거부)
List<List<String>> chunks = partition(keywords, chunkSize);
MsearchResponse r = client.msearch(chunks.stream().map(this::sameQueryWith).toList());   // 청크마다 size ≥ from+size
if (r.responses().stream().anyMatch(Item::isFailure)) throw new ChunkFailed();   // 부분 결과 금지
return merge(r, byScoreThenIdThenKey());                                      // _id dedupe + 청크와 같은 정렬 키
```
무엇이 깨졌나: 엔진 상한을 설정으로 올릴 수 있다고 믿었고, 그 전에는 상한 초과분을 조용히 잘랐다.

### 변형 B — cartesian 변형 폭증 → 곱하기 전 cap
① 문제 코드
```python
variants = ["".join(p) for p in itertools.product(*candidates_per_token)]   # k^n
doc["variants"] = variants               # 다중값 × n-gram 서브필드 여럿
```
② 고친 코드
```python
per_token_cap = 6 if is_long(name) else math.inf          # 곱하기 전에 인자 축소
capped = [c[:per_token_cap] for c in candidates_per_token]
quota = max(1, RESULT_CAP // len(capped[0]))               # 첫 토큰 기준 층화 quota
variants = stratified_product(capped, quota, cap=RESULT_CAP)
doc["variants"] = variants                                 # keyword만
doc["variants_top5"] = variants[:5]                        # 분석기 서브필드는 상위 5개에만
```
무엇이 깨졌나: 조합 수가 입력 길이에 지수적이라는 걸 무시했고, 결과 cap만으로 생성 비용을 막으려 했다.\
같은 구조: 한 변형 필드에 fuzzy까지 걸자 운영 클러스터에서 연결 타임아웃 → 상한 도입 후에도 효과 불분명해 해당 색인 기능 전체를 롤백(필드·분석기 제거 + 재색인 + alias 스왑).\
같은 구조: 알파벳 fallback 변형이 일반 단어에도 적용되고 두 변환기가 같은 숫자 토큰을 중복 처리 → 토큰 dedup + 층화 quota + 점진 cap.\
같은 구조: 언어별 변환 서브필드를 전 언어로 만들던 것을 문서의 원 언어 + 보조 언어로 제한.

### 변형 C — 요청 부피·동시성 vs 서버 한도
① 문제 코드
```python
with ThreadPool(12) as pool:                                    # 동시 워커 12 × 큰 배치
    pool.map(lambda b: es.bulk(b, request_timeout=30), batches(size=1000))
# → 429 circuit_breaking_exception / 429 rejected / Read timeout / 노드 OOM
```
② 고친 코드
```python
with ThreadPool(8) as pool:                                     # 동시성 ≤ 서버 쓰기 큐
    pool.map(lambda b: es.bulk(b, request_timeout=120), batches(size=500))
```
```yaml
environment:
  - ES_JAVA_OPTS=-Xms${HEAP} -Xmx${HEAP}   # HEAP < compressed oops 임계 (32GB보다 약간 낮을 수 있음 — 로그 확인)
# 재생성 순서: 엔진 → green → 앱 (앱 커넥션 풀의 죽은 연결 방지)
```
무엇이 깨졌나: 클라이언트가 서버의 메모리·큐·처리 시간 한도를 모른 채 부피와 동시성을 정했다.\
같은 구조: 대량 색인 중 힙 부족으로 대상의 과반이 실패 → 인덱스 삭제 후 힙 상향해 재실행.\
같은 구조: bulk가 클라이언트 기본 타임아웃(30초)을 넘음 → 힙 증설 + 타임아웃 120초(효과 검증은 후속으로 남음).

### 변형 D — 상한이 정확도를 깎음 · 쿼리 비용을 색인으로 이전
① 문제 코드
```python
q.match("name_tokens", name, fuzziness="AUTO")                    # 5자 입력 → 거리 1만, 후보 50개만 유지
q.wildcard("name.keyword", f"*{part}*")                           # term 사전 전체 순회
```
② 고친 코드
```python
q.match("name_longest_token", name, fuzziness="2", prefix_length=1,
        max_expansions=500, fuzzy_transpositions=False)            # term 수 줄인 필드 + 확장 폭 명시
q.term("name.front_ngram", part)                                  # 색인 시점 edge n-gram (앞)
q.term("name.back_ngram", part)                                   # reverse → edge n-gram → reverse (뒤)
# 의미: *x* (중간 포함) → x* 또는 *x (접두·접미) 로 좁혀짐 — 중간 포함이 필요하면 일반 n-gram
```
무엇이 깨졌나: 확장형 쿼리의 비용 상한이 결과 정확도의 상한이기도 하다는 걸 놓쳤고, 부분 매칭 비용을 매 요청에 지불했다.

## 검증 기록
- 2026-09-24: 사건 기록 대조·추상화(Claude 초안)
