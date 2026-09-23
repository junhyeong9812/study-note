# search-engine — 색인·쿼리·점수

전문 검색엔진(색인·분석기·쿼리·클러스터)에서 나오는 패턴이다.\
공통 원리: **쿼리는 원문이 아니라 색인에 저장된 표현과 매칭된다** — 표현이 어긋나면 에러 없이 0건·오답이 나오고, 비용과 점수는 입력 분포에 따라 조용히 폭발·왜곡된다.

## 공통 원리

```
  원문 ──▶ 분석기 체인 ──▶ 색인 표현 (매핑 = 생성 시 고정 스키마)
                               ▲
  쿼리 ──▶ 쿼리 분석 ──────────┘  표현 불일치 → 0건 (에러 없음)
                               │
                               ├─ 매칭 폭: 토큰 OR·fuzzy·ngram
                               ├─ 비용: 절 수·확장·힙 상한
                               └─ 점수: 상대값 → 고정 임계 금지
```

## 패턴 카드

- [cluster-ops-traps](cluster-ops-traps/) — 검색엔진 클러스터는 운영 조건(디스크 워터마크 read-only·단일 노드 replica·세그먼트 병합·alias 이름공간·라이선스 게이팅)에 따라 조용히 다른 모드로 들어간다.
- [document-model-quirks](document-model-quirks/) — ES 문서 모델(메타필드 `_id`·nested 숨은 문서·missing의 빈 문자열·스크립트의 값 부재·`_id` last-write-wins)은 일반 JSON 직관과 다르다.
- [mapping-is-schema](mapping-is-schema/) — 검색 인덱스 매핑은 생성 시점에 고정되는 스키마다 — 제자리 변경·소급 적용이 안 되므로 정의 단일화·명시 매핑·재색인+alias 스왑으로 관리한다.
- [multilingual-analysis-chain](multilingual-analysis-chain/) — 분석기 체인은 순서가 있는 파이프라인이고 문자체계마다 토큰화 전제가 다르다 — 필터 순서·비대상 스크립트 fallback·혼합 입력을 명시 처리한다.
- [query-and-index-cost-limits](query-and-index-cost-limits/) — 엔진 상한(절 수·max_expansions·circuit breaker·bulk 큐·힙)과 변형 폭증(cartesian)은 쿼리·색인 비용을 입력 분포에 따라 폭발시킨다 — 조합·요청 크기에 상한을 둔다.
- [query-index-representation-mismatch](query-index-representation-mismatch/) — 쿼리가 인덱스의 실제 표현(분석 여부·search_analyzer·normalizer·필드 존재·index:false·nested)과 어긋나면 ES는 에러 없이 0건·오매칭을 낸다 — 색인측과 질의측 변환을 대칭으로 맞추고 매핑과 대조한다.
- [query-matching-breadth](query-matching-breadth/) — full-text match의 토큰 OR·토큰별 fuzzy·ngram 부분문자열·위치 정보 없는 자질 합집합은 매칭을 과도하게 넓힌다 — 쿼리 종류와 토큰화 단위를 의도에 맞춘다.
- [score-semantics-and-composition](score-semantics-and-composition/) — 점수는 상대값이다 — should 합산·TF 누적·길이 정규화·근사(PQ) 점수에 고정 임계를 걸면 순위·재현율이 조용히 왜곡된다.

> 이 폴더의 메타 태그: `silent-failure`(1) · `resource-bounding`(1) — 태그별 전체 목록은 [cs/issue 태그 역인덱스](../../README.md#태그-역인덱스).
