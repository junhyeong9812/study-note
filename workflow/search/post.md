# search — 검색과 자동완성

```
[검색]  브라우저 → front /search?q= (SSR) → backend GET /api/search?q=[&topic&doc_kind&size]
   backend:
   ├─ requestId 수용(front 발행) 
   ├─ llm /rewrite 호출 ──성공─▶ 키워드·확장어를 BM25 질의에 합침 (제안 필터는 미적용 — 과필터 실측)
   │                  └─실패(503/422/타임아웃)─▶ 생략 폴백 (rewrite_used=false)
   ├─ BM25(nori: title^3·heading^2·content) ─┐
   ├─ kNN(질의 임베딩→dense 코사인) ──────────┤ 임베딩 장애 → 빈 랭킹 (dense_used=false)
   └─ RRF 병합: 점수 버리고 등수만 — Σ 1/(60+등수), 키 = path#chunk_no
   불변식: 검색은 llm에도 임베딩에도 인질로 잡히지 않는다 — 폴백 상태를 응답 뱃지로 노출

[자동완성]  입력(200ms 디바운스) → front /api/suggest → backend GET /api/suggest?q=
   backend: ES 단독(저지연 — rewrite·kNN 없음)
   ├─ multi_match(title^3·heading^2·content) + doc_kind 필터(summary·answer·post)
   ├─ collapse(path): 문서당 최고 청크 1건
   └─ highlight: 일치 부분을 ⟦m⟧…⟦/m⟧ 마커로 (제목 전체 + 내용 90자 조각 1개)
   front: 텍스트를 이스케이프한 뒤 마커만 <mark>로 — HTML 주입 원천 차단
```

**절차 핵심**: 검색(정확도·폴백 다층)과 자동완성(지연 최소)은 요구가 달라 경로도 다르다 —
같은 ES를 쓰되 자동완성은 llm·임베딩을 부르지 않는다.
