# issue11 — /api/suggest: 자동완성은 왜 검색과 다른 길로 갔나

- 이슈 #22 · PR: #24 (front issue9와 쌍)

> ### 이 문서가 어떻게 바뀌었나 (2026-09-02 재작성)
> ```
> [기존 문서]                              [새 문서 — 지금 이것]
> "검색 파이프라인을 안 타고           ──▶   왜 안 타나(지연) → 무엇을 고민했나 →
>  ES 단독 경로" (요약)                       그래서 ES 단독 (문제→고민→선택)
> multi_match·collapse를 표로만        ──▶   실제 SuggestService.kt 쿼리 diff
> collapse 대안 비교를 두 줄로          ──▶   [size 키워 dedupe] ↔ [collapse] 나란히
> ⟦m⟧ 마커를 설명 없이 언급             ──▶   그 자리에서 마커·collapse·multi_match 풀이
> ```

---

## 1. 배경 — 자동완성의 제1요구는 "빠름"

자동완성(suggest)은 사용자가 검색창에 글자를 칠 때마다, 즉 **키 입력 한 번마다** 호출된다.
그래서 다른 무엇보다 **지연(latency)** 이 먼저다. 한 번 응답에 수백 밀리초가 걸리면
글자를 칠 때마다 화면이 버벅여 쓸 수 없다.

이 프로젝트의 본 검색(issue4)은 정확도를 위해 무거운 파이프라인을 탄다:

```
[본 검색 /api/search]
  질문 ──▶ llm rewrite(질의 재작성) ──▶ BM25 + kNN(벡터) 두 검색 ──▶ RRF로 순위 합침
           └ 느림(모델 호출)            └ 임베딩 필요            └ 후처리
```

> 용어 — BM25: 단어 빈도 기반 전통 검색 점수. kNN: 문장을 벡터로 바꿔 "의미가 가까운"
> 것을 찾는 검색(임베딩 필요). RRF: 두 검색의 순위를 합치는 방법. rewrite: 사용자 질문을
> 검색에 유리하게 모델이 고쳐 쓰는 단계. — 자세히는 issue4.

이 파이프라인을 키 입력마다 태우는 건 지연 요구와 정면으로 충돌한다. 그래서 고민은
"자동완성도 이 좋은 파이프라인을 재사용할까, 아니면 별도 길을 팔까"였다.

**결론: 별도 길.** 자동완성은 rewrite·kNN 없이 **Elasticsearch(ES) 단독**으로 간다.
자동완성은 "정확한 답"이 아니라 "지금 치는 글자로 시작될 만한 문서 후보"만 빠르게 주면
되므로, 모델 호출과 벡터 검색이라는 느린 단계를 뺀다.

---

## 2. 구현 — ES 쿼리 하나로 끝내기

새로 만든 `SuggestService`는 ES에 쿼리 하나를 던지고 결과를 다듬는다.

`src/main/kotlin/xyz/junproject/backend/search/usecase/SuggestService.kt` (신규)

```kotlin
fun suggest(requestId: String, query: String, size: Int = 8): List<SuggestItem> {
    val body = objectMapper.writeValueAsString(mapOf(
        "size" to size,
        "_source" to listOf("path", "title", "doc_kind"),
        "query" to mapOf("bool" to mapOf(
            "must" to listOf(mapOf("multi_match" to mapOf(
                "query" to query, "fields" to listOf("title^3", "heading^2", "content")))),
            "filter" to listOf(mapOf("terms" to mapOf(
                "doc_kind" to listOf("summary", "answer", "post")))),
        )),
        "collapse" to mapOf("field" to "path"),          // 문서(path)당 최고 청크 1건
        "highlight" to mapOf(
            "pre_tags" to listOf("⟦m⟧"), "post_tags" to listOf("⟦/m⟧"),
            "fields" to mapOf(
                "title" to mapOf("number_of_fragments" to 0),
                "content" to mapOf("fragment_size" to 90, "number_of_fragments" to 1),
            ),
        ),
    ))
    ...
}
```

이 쿼리의 세 부분을 풀어 쓰면:

**① `multi_match` (제목·헤딩·내용 동시 검색)**

```
multi_match(query, fields = [ title^3, heading^2, content ])
              │                  │        │        │
              │                  │        │        └ 내용도 검색 (가장 낮은 가중치)
              │                  │        └ 헤딩(소제목)은 2배 가중
              │                  └ 제목은 3배 가중 (^3 = boost 3)
              └ 한 단어로 세 필드를 한꺼번에 검색
```

> 용어 — `multi_match`: 하나의 검색어를 여러 필드에 동시에 매칭하는 ES 쿼리. `^3`은
> boost(가중치)로, 제목에서 맞으면 내용에서 맞은 것보다 3배 높은 점수를 준다. 그래서
> **제목이 일치하는 문서가 위로, 내용만 일치하는 문서가 아래로** 정렬된다.

**② `collapse` (문서당 1건만) — 여기가 대안 비교의 핵심**

문서 하나는 여러 청크(chunk, 잘게 쪼갠 조각)로 색인돼 있다. 검색어가 한 문서의 여러
청크에 맞으면, 그냥 두면 **같은 문서가 리스트를 도배**한다. 이걸 막는 방법이 두 가지였다:

```
[대안 A]  size를 크게 받아 backend에서 path별 dedupe(중복 제거)
   ES ── 20건 받음 ──▶ backend가 path로 묶고 최고 점수만 남김 ──▶ 8건
   문제: (1) 필요 없는 20건을 전송·수신 = 낭비
         (2) "문서당 최고 점수 청크"를 고르는 로직을 우리가 직접 짜야 함

[대안 B — 채택]  collapse(field=path)
   ES ── path별 최고 히트 1건만 골라 8건 ──▶ backend는 그대로 사용
   이점: ES가 그룹당 최고 1건을 골라주니 전송량도 로직도 최소
```

`collapse`는 지정한 keyword 필드(여기선 `path`) 기준으로 **그룹마다 점수 최고 히트
1건씩만** 돌려주는 ES 기능이다. 우리 색인의 문서 id는 `path#chunk_no` 구조지만, `path`
자체가 별도 keyword 필드로도 색인돼 있어 그대로 collapse 기준이 된다. 그래서 별도 설계
없이 "문서당 1건"이 성립한다. 대안 A의 낭비(불필요한 전송 + 직접 짜는 dedupe 로직)를
피하려고 B를 택했다.

**③ `highlight` (일치 부분 강조를 HTML이 아닌 마커로)**

일치한 글자를 강조해서 보여줘야 하는데, ES가 기본으로 주는 강조는 `<em>` 같은 HTML
태그다. 이걸 그대로 front가 화면에 그리면 XSS(악성 스크립트 주입) 위험이 있다. 그래서
강조 표시를 HTML 태그가 아니라 **`⟦m⟧ … ⟦/m⟧`라는 우리만의 마커 문자열**로 받는다.
front는 받은 텍스트를 통째로 이스케이프(HTML 무력화)한 뒤, 이 마커만 찾아 강조 렌더로
바꾼다. 강조 원천을 텍스트로 만들어 주입 가능성을 차단하는 것이다(상세는 front issue9).

- 제목은 `number_of_fragments = 0` → **제목 전체**를 마커 붙여 그대로.
- 내용은 `fragment_size = 90, number_of_fragments = 1` → 일치 주변 **90자 조각 1개**만.

---

## 3. 응답과 실패 처리

`src/main/kotlin/xyz/junproject/backend/search/api/SearchController.kt`

```kotlin
@GetMapping("/suggest")
fun suggest(@RequestParam q: String,
            @RequestHeader("X-Request-Id", required = false) incomingId: String?):
        ResponseEntity<Map<String, Any?>> {
    val requestId = requestLog.acceptOrIssue(incomingId)
    if (q.isBlank() || q.length > 100) {
        return ResponseEntity.status(HttpStatus.UNPROCESSABLE_ENTITY)
            .body(Envelope.fail("invalid_request", detail = "q 1~100자"))
    }
    return try {
        val items = suggestService.suggest(requestId, q).map {
            mapOf("path" to it.path, "title" to it.title,
                  "doc_kind" to it.docKind, "snippet" to it.snippet)
        }
        ResponseEntity.ok(Envelope.ok(mapOf("items" to items)))
    } catch (error: Exception) {
        requestLog.log(requestId, "suggest failed: ${error.message?.take(150)}", "error")
        ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE)
            .body(Envelope.fail("search_backend"))
    }
}
```

- 질의는 1~100자만 받는다(빈 문자열·과도한 길이는 422로 거절).
- ES가 죽어도 자동완성 하나 때문에 화면 전체가 깨지면 안 되니, 실패는 503으로 감싸고
  로그만 남긴다. 자동완성은 "있으면 좋은" 보조 기능이라 조용히 비는 게 낫다.

---

## 4. 결론

스모크(직접 실행 확인)에서 "정렬"을 입력하니, 제목이 일치하는 portfolio 글과 내용이
일치하는 lsm-tree 글(내용 스니펫과 함께)이 같은 리스트에 떴다 — **제목이든 내용이든 어느
쪽이 일치해도 잡힌다**는 요구가 충족됐다.

정리하면, 자동완성은 정확도가 아니라 지연이 제1요구라는 판단에서 검색 파이프라인을
재사용하지 않고 ES 단독 경로를 팠고, 문서 도배는 `collapse`로, 강조 주입은 마커로 막았다.
PR #24
