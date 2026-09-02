# issue4 — 검색 API: 두 검색기의 순위를 합치고, 뭐가 죽어도 응답한다

- 리포: https://github.com/junhyeong9812/study-note-deploy-system-backend
- 이슈 #7 · PR: https://github.com/junhyeong9812/study-note-deploy-system-backend/pull/8

> ### 이 문서가 어떻게 바뀌었나 (2026-09-02 재작성)
> ```
> [기존 문서]                          [새 문서 — 지금 이것]
> "BM25·kNN·RRF 채택" 결론만    ──▶   왜 두 개가 필요한가 → 왜 못 더하나
>                                       → 그래서 등수만 쓴다 (문제→고민→선택)
> 실제 코드 요약 스니펫          ──▶   실제 커밋 fbaee1c·f19cc50 diff 그대로
> "폴백이 있다"고만 서술         ──▶   [정상 흐름]↔[장애 흐름] ASCII 나란히
> ```
> 표현도 순화: "필터를 박았다" → "필터를 명시했다".

---

## 1. 배경 — 무엇을 만들어야 했나

검색어 하나가 들어오면 세 단계를 거쳐 결과를 돌려주는 API가 필요했다.

```
검색어 q
  ① (선택) llm에게 q를 다듬게 한다   — 오타 교정·동의어 확장·키워드 추출
  ② 키워드 검색(BM25)과 의미 검색(kNN)을 둘 다 돌린다
  ③ 두 결과의 순위를 하나로 합쳐 준다
```

그리고 절대 어기면 안 되는 **불변식**을 하나 기록해놨다: **llm이 죽든 임베딩 서버가
죽든, 검색은 어떻게든 응답한다.** 부가 기능(질의 재작성·의미 검색)의 장애가 본 기능
(검색)을 인질로 잡으면 안 된다.

> 용어 — BM25 / kNN / RRF: 아래 2·3·4장에서 각각 그 자리에서 풀이한다. 미리 한 줄로만
> 요약하면 BM25는 "이 단어가 이 문서에 얼마나 특징적인가"(키워드), kNN은 "뜻이 얼마나
> 가까운가"(의미), RRF는 "둘의 등수를 합치는 방법"이다.

---

## 2. BM25 — "이 단어가 이 문서에 얼마나 특징적인가"

BM25(Best Matching 25 — 정보검색에서 널리 쓰는 키워드 점수 공식)는 세 직관의 곱이다.

```
점수(단어, 청크) ≈  TF(빈도, 포화)  ×  IDF(희소성)  ×  길이 보정

TF   그 단어가 청크에 많이 나올수록 ↑. 단 포화된다 — 3번이나 30번이나 큰 차이 없음
     (같은 단어를 도배해도 점수를 무한히 올릴 수 없게).
IDF  전체 문서에서 흔한 단어일수록 ↓. "이", "하다"는 0에 수렴하고
     "낙관적"·"WAL" 같은 드문 단어가 점수를 지배한다.
길이  긴 청크는 아무 단어나 우연히 담기 쉬우므로 살짝 패널티.
```

여기서 **nori(한국어 형태소 분석기)가 선행 조건**이다 — "락을"과 "락이"를 같은 "락"으로
세지 못하면 TF·IDF가 전부 어긋난다. issue1에서 nori부터 실증한 이유가 여기서 갚아진다.

- **강점**: 정확한 용어(함수명·에러 문자열·고유명사). 결과가 "왜 나왔는지" 설명 가능.
- **약점**: 단어가 다르면 못 찾는다 — "정렬을 미룬다"라고 치면 LSM-Tree 문서를 못 잡는다.

---

## 3. kNN — "의미가 가까운가"

임베딩 모델(BGE-M3)이 글을 1024개의 숫자(벡터)로 바꾼다. 비슷한 뜻의 글은 비슷한 벡터가
되도록 학습된 모델이다.

```
검색어 q → 벡터 v
모든 청크의 저장된 벡터와 코사인 유사도(두 벡터 사이 각도가 좁을수록 1에 가까움) 비교
     → 가장 가까운 k개
실제론 전수 비교가 아니라 HNSW(근사 그래프 탐색)로 후보 num_candidates개만 본다
     — 빠르지만 "근사"라서 가끔 놓친다 (그래서 후보를 size*5로 넉넉히 잡는다)
```

> 용어 — kNN(k-Nearest Neighbors): "가장 가까운 k개 이웃"을 찾는 것. 여기선 검색어 벡터와
> 가장 가까운 청크 k개.

- **강점**: 표현이 달라도 잡는다 — "정렬을 나중으로 미루는 구조" → lsm-tree (실측).
- **약점**: 정확한 문자열에 둔감, 점수(0~1)의 근거를 설명하기 어려움, 임베딩 서버가 필요.

**왜 둘 다 쓰나 — 실패 모드가 정반대라서.** BM25가 놓치는 것(다른 표현)을 kNN이 잡고,
kNN이 흐리게 보는 것(정확한 용어)을 BM25가 꽂는다. 노트 검색은 두 유형의 질의가 다
들어온다("optimistic lock" 같은 정확한 용어 vs "락 거는 방식 차이" 같은 서술형).

---

## 4. RRF — 합치는 방법: 점수는 버리고 등수만 쓴다

두 점수는 단위가 다르다. BM25는 18.5 같은 무한대 스케일, 코사인은 0~1. 이걸 어떻게 합칠까?

- **그냥 더하면** BM25(18.5)가 코사인(0.9)을 완전히 지배한다 — kNN이 사실상 무시된다.
- **정규화(각자 최대값으로 나누기)는** 이상치 하나가 전체를 휘두른다 — 어쩌다 BM25 100점짜리가
  하나 나오면 나머지가 다 0.x로 눌린다.

RRF(Reciprocal Rank Fusion — 역순위 융합)의 답은 **원래 점수를 버리고 "몇 등이었나"만
쓰는 것**이다.

```
새 점수(청크) = Σ 각 랭킹  1 / (k + 등수)      (k=60)

예) 청크 A: BM25 1등, kNN 3등 → 1/61 + 1/63 = 0.0323
    청크 B: BM25 2등, kNN 없음 → 1/62        = 0.0161
    청크 C: BM25 없음, kNN 1등 → 1/61        = 0.0164
→ 양쪽 상위인 A가 확실히 위, 한쪽에만 있는 B·C는 등수대로.
```

k=60의 역할: 분모를 키워 **1등과 2등의 격차를 완만하게** 만든다. k가 작으면(예: 1)
1등이 독식하고(1/2 vs 1/3), k가 크면 등수 차이가 뭉개진다. 60은 원 논문의 관례값 —
일단 60으로 두고 실측 조정 항목([구현 검증] #2)에 올려놨다.

등수만 쓰는 것의 또 다른 이점: **한쪽 랭킹이 통째로 비어도 수식이 그대로 성립한다.**
그래서 "임베딩이 죽으면 BM25 단독" 폴백과 구조적으로 궁합이 좋다 — 아래 6장.

---

## 5. 검토한 방식들 — 왜 수동 RRF인가

**문제:** 두 검색기를 합치는 방법이 여럿 있는데 무엇을 고를까.

**대안 (1) — ES 내장 hybrid(RRF retriever).** ES가 알아서 RRF를 해주는 기능이 있다.
그런데 라이선스·버전 제약이 붙고, 무엇보다 "한쪽이 실패하면 다른 쪽만으로 응답"을 우리가
제어하기 어렵다. 불변식(뭐가 죽어도 응답)을 ES 내부 동작에 맡기는 셈이라 탈락.

**대안 (2) — 임베딩만(kNN 단독).** 코드는 가장 단순하지만 정확한 용어 매칭(함수명·에러
문자열)에 약하다. 노트 검색은 그런 질의가 실제로 많이 들어와서 탈락.

**선택 — BM25와 kNN을 따로 실행한 뒤 수동 RRF.** RRF는 등수만 쓰니 스케일 문제가 없고,
한쪽이 비어도 그대로 합쳐진다. 우리가 직접 짜면 폴백을 우리가 제어할 수 있고, 코드는
30줄 남짓이다.

---

## 6. 구현 워크플로우 — 정상 흐름과 장애 흐름

```
[정상 흐름]
GET /api/search?q=낙관적 락 차이  [&topic=cs&size=10]
  ▼ requestId 발행 (backend가 발행 — 로그 규약)
  ▼ llm /rewrite ── 키워드·확장어를 BM25 검색어에 합침 (rewrite_used=true)
  ▼ BM25(nori)  ──────────────────────────┐
  ▼ kNN(검색어 임베딩 → dense 유사도) ────┤
  ▼ RRF 병합 (키 = path#chunk_no)  ◀──────┘
  ▼ {"success":true,"data":{"rewrite_used":true,"dense_used":true,"results":[...]}}

[장애 흐름 — 불변식이 지켜지는 자리]
  ▼ llm /rewrite ── 503/422/타임아웃 ──▶ rewrite 생략 (rewrite_used=false)   ← 폴백 1
  ▼ BM25(nori)  ──────────────────────────┐
  ▼ kNN → 임베딩 서버 예외 ──▶ 빈 랭킹 (dense_used=false)                     ← 폴백 2
  ▼ RRF 병합 — 한쪽이 비어도 수식 그대로 성립  ◀──────┘
  ▼ {"success":true, ... "rewrite_used":false,"dense_used":false, ...}  (여전히 200)
```

기본 필터: `doc_kind ∈ summary·answer·post`. question(답 없는 질문 목록)과 index/readme는
검색 노이즈라 기본 제외하고, 파라미터로만 켤 수 있게 했다.

### 폴백 1 — llm 재작성은 실패를 전부 "생략"으로 흡수한다

`src/main/kotlin/xyz/junproject/backend/search/LlmClient.kt` (커밋 fbaee1c) — 성공/실패를
전부 `RewriteOutcome`으로 감싸고, 어떤 예외든 `fallback()`으로 흡수해 `used=false`를 준다:

```kotlin
    fun rewrite(requestId: String, query: String): RewriteOutcome = try {
        val response = client.post().uri("/rewrite")
            .header("Content-Type", "application/json")
            .body(mapOf("request_id" to requestId, "query" to query))
            .retrieve().body(Map::class.java)
        val data = response?.get("data") as? Map<String, Any?>
        if (response?.get("success") == true && data != null) {
            ...
            RewriteOutcome(used = true, keywords = ..., expanded = ..., ...)
        } else fallback(requestId, "success=false")
    } catch (error: Exception) {
        fallback(requestId, error.javaClass.simpleName)   // 어떤 장애든 여기로 수렴
    }

    private fun fallback(requestId: String, reason: String): RewriteOutcome {
        requestLog.log(requestId, "rewrite fallback: $reason", "warning")
        return RewriteOutcome(used = false)               // 검색은 원본 q로 계속 진행
    }
```

읽기 타임아웃은 `wrapper 총예산 5s + 여유`로 7초를 명시했다 — llm이 느려도 검색이
7초 넘게 매달리지 않게.

### 폴백 2 — 임베딩이 죽으면 BM25 단독 (issue5 리뷰에서 강화)

최초 fbaee1c의 kNN은 벡터가 비면 빈 리스트를 주는 정도였다. issue5 듀얼 리뷰에서 "임베딩
서버가 예외를 던지면 검색 전체가 503으로 죽는다"는 지적을 받아, kNN 호출 자체를 try/catch로
감쌌다.

`src/main/kotlin/xyz/junproject/backend/search/SearchService.kt` (커밋 8ea60a4):

```kotlin
        val (knnRanking, denseUsed) = try {
            knn(query, filterTopic, filterKinds, size * 2) to true
        } catch (error: Exception) {                    // 임베딩·kNN 장애 → BM25 단독 (B4)
            requestLog.log(requestId, "knn fallback: ${error.javaClass.simpleName}", "warning")
            emptyList<SearchHit>() to false
        }
```

응답에 `dense_used`를 실어 "이번 결과가 의미검색을 포함했는지"를 호출자가 알 수 있게 했다.

### RRF 병합 — 청크 정체성 키

`src/main/kotlin/xyz/junproject/backend/search/SearchService.kt` — 같은 청크가 BM25·kNN
양쪽 상위에 들면 두 등수 점수를 합산해야 한다. 그러려면 "같은 청크"를 식별하는 키가
필요한데, 최초 fbaee1c는 `path#heading`으로 잡았다. issue5 리뷰가 이 키의 결함을 잡아
`path#chunk_no`로 고쳤다(왜 결함이었는지는 issue5 문서에서 상세히):

```diff
- val key = "${hit.path}#${hit.heading}"
+ val key = "${hit.path}#${hit.chunkNo}"   // 청크 정체성은 path#chunk_no (es-index D1)
  val rrfScore = 1.0 / (k + index + 1)     // k=60, index는 0-based라 +1
  scores[key] = (existing?.first ?: hit) to ((existing?.second ?: 0.0) + rrfScore)
```

---

## 7. 구현 중 마주친 문제 — llm이 제안한 필터를 믿었더니 검색이 반대로 갔다

> 이 사건은 issue5(듀얼 리뷰)의 지적을 반영한 **직후** 재배포 스모크에서 터졌다. 커밋은
> f19cc50이며, 검색 필터에 관한 이야기라 이 문서에 함께 둔다.

**맥락:** 듀얼 리뷰가 "rewrite의 `filters.doc_kind`를 파싱만 하고 안 쓴다(사문(死文)
필드)"고 지적했다. 그래서 우선순위 `명시 파라미터 > rewrite 제안 > 기본값`으로 배선해
반영했다. 그리고 재배포 스모크에서:

**증상:**

```
$ curl --get .../api/search --data-urlencode "q=세마포어가 뭐야"
rewrite: True  dense: True
0.0318 cs/lsm-tree/1-question.md#1         | 질문
0.0315 cs/solid-principles/1-question.md#1 | 질문
0.0313 cs/striping/1-question.md#1         | 질문
0.0313 cs/straggler/1-question.md#1        | 질문
```

결과가 **전부 1-question.md** — 답이 없는 질문 목록만 나온다. 기본 필터는 분명 question을
제외하는데도.

**진단:** rewrite 로그를 보니 모델이 `filters.doc_kind = "question"`을 제안했다. "뭐야"로
끝나는 질문형 검색어니까 "question 문서를 찾는 거겠지"라고 추론한 것이다 — 사람 의도
(질문에 대한 **답**을 찾는다)와 정반대다. 방금 배선한 우선순위 때문에 이 제안이 기본값을
밀어내고 하드 필터로 적용돼 summary·answer·post가 전부 걸러졌다.

**무엇을 고민했나:** 리뷰어 둘 다 "제안을 쓰라"고 했는데, 실측해보니 제안을 쓰는 것 자체가
해로웠다. 여기서 두 겹의 교훈이 갈렸다. ① 약한 모델의 구조화 출력은 참고 자료지 결정권자가
아니다 — local-llm의 "약한 모델 + 좋은 검색" 원칙은 필터에도 적용된다. ② 리뷰 지적을 반영한
코드도 실측으로 재검증해야 한다 — 리뷰는 "설계와 코드의 불일치"는 잡지만 "설계 자체의
유해함"은 실측만 잡는다.

**그래서 이렇게 했다 (SearchService, 커밋 f19cc50):** 하드 필터는 명시 파라미터만 쓰고,
rewrite 제안은 **버리지 않되 로그로만 축적**한다 — 나중에 "제안이 얼마나 맞았나"를 실데이터로
판단할 재료([구현 검증] #7):

```diff
- val filterTopic = topic ?: rewrite.topic.takeIf { rewrite.used }
- // 필터 우선순위: 명시 파라미터 > rewrite 제안 > 기본값 (B2)
- val filterKinds = docKinds?.takeIf { it.isNotEmpty() }
-     ?: rewrite.docKind?.let { listOf(it) }
-     ?: defaultKinds
+ // 하드 필터는 명시 파라미터만. rewrite 제안(topic·doc_kind)은 필터로 쓰지 않는다 —
+ // 실측(2026-08-24): "세마포어가 뭐야"에 모델이 doc_kind=question을 제안해 정리·정답이 전멸.
+ // 제안은 로그로만 남겨 실측 데이터화 ([구현 검증] #7).
+ val filterTopic = topic
+ val filterKinds = docKinds?.takeIf { it.isNotEmpty() } ?: defaultKinds
+ if (rewrite.used && (rewrite.topic != null || rewrite.docKind != null)) {
+     requestLog.log(requestId,
+         "rewrite hint (미적용): topic=${rewrite.topic} doc_kind=${rewrite.docKind}")
+ }
```

---

## 8. 결론

하이브리드 검색·rewrite 폴백(래퍼를 실제로 꺼보고 검색 정상 확인)·kNN 폴백·명시 필터가
모두 동작한다. 실측 예: "정렬을 나중으로 미루는 구조" → lsm-tree, "kafka가 빠른 이유" →
kafka-why-fast. 세마포어는 노트에 챕터가 아직 없어 근접 문서만 잡히는데, 코퍼스가 자라면
채워질 자리다. 남긴 것: RRF k값 실측 조정·rewrite 제안 정확도 측정([구현 검증] 대장). PR #8
