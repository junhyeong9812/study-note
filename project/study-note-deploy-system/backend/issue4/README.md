# issue4 — 검색 API: 두 검색기의 순위를 합치고, 뭐가 죽어도 응답한다

- 리포: https://github.com/junhyeong9812/study-note-deploy-system-backend
- 이슈 #7 · PR: https://github.com/junhyeong9812/study-note-deploy-system-backend/pull/8

## 1. 배경 (요구사항)

검색어 하나가 들어오면 ① llm에게 검색어를 다듬게 하고(선택) ② 키워드 검색(BM25)과
의미 검색(kNN)을 둘 다 돌려 ③ 하나의 순위로 합쳐 준다. 그리고 **불변식**: llm이 죽든
임베딩이 죽든 **검색은 응답한다**.

> 용어 — **BM25**: "이 단어가 이 문서에 얼마나 특징적으로 나오나"로 점수 매기는 고전
> 키워드 검색. **kNN**: 검색어를 벡터로 바꿔 "의미가 가까운" 청크를 찾는 것(단어가 달라도
> 잡힘). **RRF**(Reciprocal Rank Fusion): 점수 단위가 다른 두 순위를 "몇 등이었나"만으로
> 합치는 방법 — 점수 = Σ 1/(60+등수).

## 2. 검토한 방식들

### 선택 — BM25와 kNN을 따로 실행 후 수동 RRF

- 두 검색기의 점수는 스케일이 달라 더할 수 없다(BM25 18.5 vs 코사인 0.9). RRF는 등수만
  쓰니 스케일 문제가 없고, 한쪽이 비어도 그대로 합쳐진다 — 폴백과 궁합이 좋다.

### 대안 — ES 내장 hybrid(RRF retriever) (탈락)

- 라이선스·버전 제약이 있고, "한쪽 실패 시 다른 쪽만"을 우리가 제어하기 어렵다. 수동
  RRF는 30줄이다.

### 대안 — 임베딩만(kNN 단독) (탈락)

- 정확한 용어 매칭(예: 함수명·에러 문자열)에 약하다. 노트 검색은 둘 다 필요.

## 3. 구현 워크플로우

```
GET /api/search?q=낙관적 락 차이  [&topic=cs&doc_kind=summary&doc_kind=answer&size=10]
  ▼ requestId 발행 (backend가 발행 — 로그 규약)
  ▼ llm /rewrite ── 성공: 키워드·확장어를 BM25 검색어에 합침
                └── 503/422/타임아웃: rewrite 생략 (rewrite_used=false)     ← 폴백 1
  ▼ BM25(nori)  ──────────────────────────┐
  ▼ kNN(검색어 임베딩 → dense 유사도) ────┤ 임베딩 장애: 빈 순위 (dense_used=false) ← 폴백 2
  ▼ RRF 병합 (키 = path#chunk_no)  ◀──────┘
  ▼ {"success":true,"data":{"rewrite_used","dense_used","results":[{path,chunk_no,heading,snippet,score}]}}
```

기본 필터: `doc_kind ∈ summary·answer·post` — question(답 없는 질문 목록)과 index/readme는
검색 노이즈라 기본 제외, 파라미터로 켤 수 있다.

## 4. 코드 변경 (핵심)

```kotlin
// 폴백 2 — 임베딩이 죽어도 BM25만으로
val (knnRanking, denseUsed) = try {
    knn(query, ...) to true
} catch (error: Exception) {
    requestLog.log(requestId, "knn fallback: ${error.javaClass.simpleName}", "warning")
    emptyList<SearchHit>() to false
}
```

```kotlin
// RRF — 같은 청크(path#chunk_no)는 양쪽 등수 점수를 합산
val key = "${hit.path}#${hit.chunkNo}"
scores[key] = hit to (기존 + 1.0 / (60 + 등수))
```

## 5. 구현 중 마주친 문제

### 문제 — llm이 제안한 필터를 믿었더니 검색이 망가짐 (리뷰 반영 후 실측)
- **증상**: "세마포어가 뭐야"를 치면 결과가 전부 `1-question.md`(질문 목록). 정리·정답이
  하나도 안 나온다.
- **원인**: rewrite가 `filters.doc_kind = "question"`을 제안("질문이니까 question 문서겠지")
  → 이걸 하드 필터로 적용 → summary·answer가 전부 걸러짐. 의도와 정반대.
- **수정**: rewrite 제안(topic·doc_kind)은 **필터로 쓰지 않는다**. 검색어 확장에만 쓰고
  제안값은 로그로 남겨 나중에 판단 재료로 축적. 하드 필터는 사용자가 명시한 파라미터만.
- **배경**: 약한 모델의 "구조화" 출력은 참고 자료지 결정권자가 아니다. local-llm 때의
  교훈("약한 모델 + 좋은 검색")을 필터에서도 지켜야 했다. 리뷰어 둘이 "제안 필터를 안
  쓴다"고 지적했는데 막상 적용해보니 해롭다는 게 실측으로 드러난 사례 — **리뷰 지적도
  실측으로 검증**한다.

## 6. 결론

하이브리드 검색·rewrite 폴백(래퍼를 실제로 꺼보고 검색 정상 확인)·kNN 폴백·명시 필터
모두 동작. "정렬을 나중으로 미루는 구조" → lsm-tree, "kafka가 빠른 이유" → kafka-why-fast.
세마포어는 노트에 챕터가 없어 근접 문서만 — 코퍼스가 자라면 잡힌다. PR: #8
